from typing import List, Dict
from enum import Enum

from setup_db import connect_to_db
import psycopg2
from psycopg2.extras import RealDictCursor

import datetime
import copy
import requests
import os
import re
import math
import threading
import time

from difflib import SequenceMatcher

# Enum, liste des stations qui correspondent aux gares utilisés dans le cas de test
class STATIONS_DICT(Enum):

    LYON_STATIONS = ["gare de lyon-gorge-de-loup", "gare de lyon-part-dieu", "gare de lyon-perrache", 
                 "gare de lyon-st-paul", "gare de lyon-vaise", "gare de lyon-jean-macé", 
                 "lyon-part-dieu-gare-routière", "lyon-perrache-gare-routière", "lyon-st-paul-la-feuilée",
                 "lyon-st-paul-quai-bondy", "lyon-vaise-gare-routière"]
    
    PARIS_STATIONS = ["gare de paris-austerlitz", "gare de paris-bercy", "gare de paris-est",
                    "gare de paris-gare-de-lyon", "gare de paris gare du nord", "gare de paris-montparnasse 3 vaugirard",
                    "gare de paris-montparnasse 1-2", "gare de paris-st-lazare"]
    
    LILLE_STATIONS = ["gare de lille europe", "gare de lille flandres"]
    
    MARSEILLE_STATIONS = ["gare de marseille-blancarde", "gare de marseille-st-charles","gare de saint-antoine",
                        "gare de picon-busserine."]
    
    AIX_PROVENCE_STATIONS = ["gare de aix-en-provence","aix-gare-routière"]

    LIMOGES_STATIONS = ["gare de limoges-bénédictins", "gare de limoges-montjovis"]

    STRASBOURG_STATIONS = ["gare de strasbourg", "gare de strasbourg-roethig"]

    NANTES_STATIONS = ["gare de nantes", "nantes-pirmil"]

    RENNES_STATIONS = ["gare de rennes", "rennes beaulieu tournebride"]

    GRENOBLE_STATIONS = ["gare de grenoble", "gare de grenoble universités gières", "grenoble-champollion",
                        "grenoble-eugène-chavant", "grenoble-gare-routière", "grenoble-victor-hugo"]
    METZ_STATIONS = ["gare de metz-nord", "gare de metz-ville"]

    METZERVISSE_STATIONS = ["metzervisse (centre)", "metzervisse (eglise)"]

    NICE_STATIONS = ["gare de nice-pont-michel", "gare de nice-riquier", "gare de nice-st-augustin",
                    "gare de nice-ville"]
    
    ROUEN_STATIONS = ["gare de rouen-rive-droite","rouen-gare-routière", "rouen saint-sever"]

    DIJON_STATIONS = ["gare de dijon-porte-neuve", "gare de dijon-ville"]

    ALL_STATIONS = (LYON_STATIONS + PARIS_STATIONS + LILLE_STATIONS + MARSEILLE_STATIONS + AIX_PROVENCE_STATIONS + LIMOGES_STATIONS + 
                    STRASBOURG_STATIONS + NANTES_STATIONS + RENNES_STATIONS + GRENOBLE_STATIONS + METZ_STATIONS + METZERVISSE_STATIONS + 
                    NICE_STATIONS + ROUEN_STATIONS + DIJON_STATIONS)


class TrainStation:
    # Forme obligatoire de la class elle est immuable
    __slots__ = ("is_valid", "stops_id", "name", "longitude", "latitude", "trips", "is_loaded", "id", "has_special_travel", "special_walking_loaded")

    def __init__(self, name:str, long: float, lat: float, stops_id: List[str]):
        
        if name: self.name = name.lower()
        else: self.name = "unknown"
        self.longitude = long
        self.latitude = lat
        self.stops_id = stops_id

        self.trips: Dict[str, Trip] = {}
        self.is_loaded = False
        self.id = id(self)
        self.has_special_travel = False

        if self.name in STATIONS_DICT.ALL_STATIONS.value:
            self.has_special_travel = True
            self.special_walking_loaded = False


        print("Station {} created.".format(self.name))
    
    def __repr__(self) -> str:
        return "<TrainStation name={} stop_id={} long={} lat={} is_loaded={}>".format(self.name, self.stops_id, self.longitude, self.latitude, self.is_loaded)

class Trip():
    __slots__ = ("trip_id", "coming_from", "going_to", "duration", "time", "opening_days", "starting_time", "service_id", "start_date", "end_date", 
                 "is_special_trip", "special_trip_path", "travel_type")
    def __init__(self, 
                 coming_from: TrainStation, 
                 going_to: TrainStation, 
                 trip_id: str, 
                 duration: int, 
                 service_id: int,
                 start_date: int,
                 end_date: int,
                 opening_days: List[int],
                 travel_type: str,
                 starting_time: str = None,
                 is_special_trip: bool = False,
                 special_trip_path: List = None
                 ) -> None:

        # Define gare de départ et d'entrée
        self.coming_from: TrainStation = coming_from
        self.going_to: TrainStation = going_to
        self.travel_type: str = travel_type

        #Vient check s'il y a une heure de départ fixer ou non ( dépend du trajet, 
        # en sorte pas de temps définit dans un trajet un pied )
        if not starting_time: 
            self.starting_time = None
        else:
            hours, minutes, secondes = starting_time.split(":")
            if int(hours) > 23: hours = int(hours) - 23
            self.starting_time: datetime.time = datetime.time(hour=int(hours), minute=int(minutes), second=int(secondes))

        self.service_id: str = service_id
        self.start_date: int = start_date
        self.end_date: int = end_date
        self.opening_days: List[int] = opening_days
        self.trip_id: str = trip_id
        self.duration: int = duration
        self.is_special_trip = is_special_trip

        if is_special_trip:
            self.special_trip_path = special_trip_path

    # Permet d'avoir ce custom string en réponse de class (btw : dès lors que l'on print la class)
    def __repr__(self) -> str:
        return "<Trip id={} starting_time={} duration={} from={} to={} opening_days={}>".format(
            self.trip_id ,self.starting_time ,self.duration, self.coming_from.name, self.going_to.name, self.opening_days)

# Singletton : INIT une seul fois, utilisé qu'une seul fois dans le projet, une sorte de répliqua du main 
# (class utilisé au coeur du run)
class Map():
    # station_manager: "dict stop_id (idGare + nom gare DEPART), pemet de taper sur un ID et pas une clé "
    # stop_list : Array avec tt les noms de stations dans la db : VIent check si station que l'on donne existe
    __slots__ = "station_manager", "stop_list"


    def __init__(self) -> None:
        self.station_manager: Dict[str, TrainStation] = {}
        self.stop_list: List[str] = []
        # Select stop name from stop, vient chercher tout les noms de stations (toute les gares -> Uniquement les noms)
        self.load_stop_list()

    def load_path(self, travel_data, wanted_date):

        steps_holder: List[TrainStation] = []
        steps = self.sanitize_station_input(travel_data)
        if not steps: return False
        for step in steps:
            if step["departure"] == None or step["destination"] == None:
                return False
        
        for step in steps:
            new_step = {"sentenceID": step["sentenceID"]}

            departure_station = self.load_station(name=step["departure"])
            if not departure_station:
                print("Station: {} not found.".format(step["departure"]))
                return False
            
            destination_station = self.load_station(name=step["destination"])
            if not destination_station:
                print("Station: {} not found.".format(step["destination"]))
                return False
            
            self.load_trips(departure_station)
            self.load_trips(destination_station)
            
            new_step["departure"] = departure_station
            new_step["destination"] = destination_station

            steps_holder.append(new_step)

        return self.a_star(steps_holder, wanted_date)

    def load_station(self, name=None, stop_id=None):
        if not name and not stop_id: return None
        if stop_id and stop_id in self.station_manager: return self.station_manager[stop_id]

        if name:
            conn = connect_to_db()
            query = """
                SELECT *
                FROM stops
                WHERE LOWER(stop_name) LIKE %s
            """
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query, (name,))
                stations_data = cursor.fetchall()
            except Exception as e:
                stations_data = False
                print(e)
            finally:
                cursor.close()
                conn.close()
        
        elif stop_id:
            conn = connect_to_db()
            query = """
                SELECT stop_id, LOWER(stop_name) as stop_name, stop_lat, stop_lon
                FROM stops
                WHERE stop_id = ANY(
                SELECT stop_id
                FROM stops
                WHERE parent_station = ANY(
                    SELECT parent_station
                    FROM stops
                    WHERE stop_id = %s
                )
                OR stop_id = ANY(
                    SELECT parent_station
                    FROM stops
                    WHERE stop_id = %s
                )
)
            """
            try:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query, (stop_id, stop_id))
                stations_data = cursor.fetchall()
            except Exception as e:
                stations_data = False
                print(e)
            finally:
                cursor.close()
                conn.close()
        
        if stations_data:
            if stations_data[0]["stop_id"] in self.station_manager:
                return self.station_manager[stations_data[0]["stop_id"]]
            
            stations_id = [station["stop_id"] for station in stations_data] 
            station = stations_data[0]
            new_station = TrainStation(name=station["stop_name"], long=station["stop_lon"], lat=station["stop_lat"],stops_id=stations_id)

            for station_id in stations_id:
                if not station_id in self.station_manager :
                    self.station_manager[station_id] = new_station
            
            return new_station
        
        return None

    def load_trips(self, initial_station: TrainStation):
        if not initial_station or initial_station.is_loaded: return

        trips: Dict[str, List] = {}

        very_first_station = initial_station

        conn = connect_to_db()
        query = """
                SELECT trip_id, arrival_time ,departure_time, stop_id
                FROM stop_times as st
                WHERE st.trip_id = ANY(
                    SELECT s.trip_id
                    FROM stop_times as s
                    WHERE s.stop_id = ANY(%s)
                )
                ORDER BY st.trip_id, st.stop_sequence
            """
        query_vars = (initial_station.stops_id,)
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, query_vars)
            
            destinations = cursor.fetchall()
        except Exception as e:
            print(e)
            destinations = []
        finally:
            cursor.close()
    
        for item in destinations:
            if item["trip_id"] not in trips: trips[item["trip_id"]] = [item]
            else: trips[item["trip_id"]].append(item)

        for trip_id in trips:
            service_id, start_time, end_time, opening_days, closed = self.load_trip_data(trip_id)
            
            if closed: continue
            previous_station = initial_station
            for index, stop in enumerate(trips[trip_id]):
                if stop["stop_id"] not in self.station_manager:
                    self.load_station(stop_id=stop["stop_id"])

                if not stop["stop_id"] in self.station_manager:
                    self.load_station(stop_id=stop["stop_id"])
                
                if index == 0:
                    previous_hours, previous_min = stop["departure_time"].split(":")[0:2]
                    previous_station = self.station_manager[stop["stop_id"]]
                    continue
                

                current_hours, current_min = stop["arrival_time"].split(":")[0:2]
                duration = (int(current_hours) * 60 + int(current_min)) - (int(previous_hours) * 60 + int(previous_min))

                if "Car" in stop["trip_id"]:
                    travel_type = "BUS"
                else:
                    travel_type = "TRAIN"

                if previous_station is self.station_manager[stop["stop_id"]]:
                    continue

                created_trip = Trip(previous_station, 
                                    self.station_manager[stop["stop_id"]], 
                                    stop["trip_id"], 
                                    duration, 
                                    service_id, 
                                    start_time, 
                                    end_time, 
                                    opening_days, 
                                    starting_time=stop["departure_time"],
                                    travel_type=travel_type)
                
                self.add_trip_to_stations(previous_station, created_trip)

                previous_station = self.station_manager[stop["stop_id"]]
                previous_hours, previous_min = stop["departure_time"].split(":")[0:2]    

        if very_first_station.has_special_travel and not very_first_station.special_walking_loaded:
            selected_city = None
            for city in STATIONS_DICT:
                if city is STATIONS_DICT.ALL_STATIONS: continue
                if very_first_station.name in city.value:
                    selected_city = city.value

            for station in selected_city:
                if station == very_first_station.name: continue
                station = self.load_station(name=station)
                self.load_google_api_walking_trip(very_first_station, station)
            very_first_station.special_walking_loaded = True


        very_first_station.is_loaded = True
        print("Station {} is fully loaded. ({} trips existing).".format(very_first_station.name, len(very_first_station.trips)))
    
    def add_trip_to_stations(self, station: TrainStation, trip: Trip)-> bool:
        if not trip.trip_id in station.trips: 
            station.trips[trip.trip_id] = trip
            return True
        else: return False

    def load_trip_data(self, trip_id: int):
        
        conn = connect_to_db()
        query = """
            SELECT c.monday,c.tuesday,c.wednesday,c.thursday,c.friday,c.saturday,c.sunday,c.start_date,c.end_date,t.service_id
            FROM trips AS t
            JOIN calendar AS c ON t.service_id = c.service_id
            AND t.trip_id = %s;
        """
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, (trip_id,))
            trip_data = cursor.fetchone()
        except Exception as e:
            trip_data = None
            print(e)
        finally:
            cursor.close()
            conn.close()

        if trip_data:
            service_id = trip_data["service_id"]
            start_date = trip_data["start_date"]
            end_date = trip_data["end_date"]
            opening_days = [trip_data["monday"],trip_data["tuesday"],trip_data["wednesday"],trip_data["thursday"],trip_data["friday"],trip_data["saturday"],trip_data["sunday"]]
            if not any(opening_days): closed = True
            else: closed = False

            return service_id, start_date, end_date, opening_days, closed
        
        return None, None, None, [0, 0, 0, 0, 0, 0, 0], True
        
    def duration_before_trip_available(self, trip: Trip, current_time: datetime.datetime) -> int:
        current_week_day = current_time.weekday()

        if trip.opening_days[current_week_day] and current_time.time() < trip.starting_time:
            time_diff = (datetime.datetime.combine(current_time, trip.starting_time) - current_time).total_seconds() / 60
            return int(time_diff)
        
        else:
            if current_week_day == 6: current_week_day = 0
            else: current_week_day += 1

            next_day = current_time + datetime.timedelta(days=1)
            next_day = datetime.datetime(next_day.year, next_day.month, next_day.day, 0, 0, 0)
            time_diff = (next_day - current_time).total_seconds()/60
            current_time = next_day

            while not trip.opening_days[current_week_day]:
                if current_week_day == 6: current_week_day = 0
                else: current_week_day += 1

                time_diff += 1440
            
            time_diff += (datetime.datetime.combine(current_time, trip.starting_time) - current_time).total_seconds() / 60
            return int(time_diff)
            
    def load_google_api_walking_trip(self, starting_station: TrainStation, finishing_station: TrainStation):

        if not starting_station or not finishing_station: return 

        if not starting_station.has_special_travel or not finishing_station.has_special_travel: return
        if abs(starting_station.latitude - finishing_station.latitude) + abs(starting_station.longitude - finishing_station.longitude) > 1.5: return
        if starting_station.special_walking_loaded: return

        walking_query = "https://maps.googleapis.com/maps/api/directions/json?origin={}&destination={}&mode=walking&language=fr&key={}".format(
            starting_station.name, finishing_station.name, os.environ["GOOGLE_MAP_API_KEY"]).replace(" ", "%20")
        
        print(walking_query)
        try:
            walking_response = requests.get(walking_query)
            walking_response = walking_response.json()

            if "routes" in walking_response and "legs" in walking_response["routes"][0]:

                total_time = int(walking_response["routes"][0]["legs"][0]["duration"]["value"] / 60)
                steps = []

                for step in walking_response["routes"][0]["legs"][0]["steps"]:
                    steps.append({"distance": step["distance"]["value"], 
                                "duration": math.ceil(step["duration"]["value"] / 60), 
                                "instructions": re.sub(r"<.*?>", "", step["html_instructions"]),
                                "type": step["travel_mode"]})

                walking_trip = Trip(starting_station, 
                                    finishing_station, 
                                    str(starting_station.id) + str(finishing_station.id) + "_walking", 
                                    total_time,
                                    starting_station.name + finishing_station.name,
                                    0, 0 ,[1, 1, 1, 1, 1, 1, 1],
                                    is_special_trip=True,
                                    travel_type="WALKING",
                                    special_trip_path=steps)
                
                self.add_trip_to_stations(starting_station, walking_trip)

        except Exception as e:
            walking_trip = None
        
        return walking_trip
    
    def load_google_api_transit_trip(self, starting_station: TrainStation, finishing_station: TrainStation, departure_time: datetime.datetime):

        if not starting_station or not finishing_station: return 

        if not starting_station.has_special_travel or not finishing_station.has_special_travel: return
        if abs(starting_station.latitude - finishing_station.latitude) + abs(starting_station.longitude - finishing_station.longitude) > 1.5: return

        transit_query = """https://maps.googleapis.com/maps/api/directions/json?origin={}&destination={}&departure_time={}&mode=transit&language=fr&key={}""".format(
            starting_station.name, finishing_station.name, int(departure_time.timestamp()), os.environ["GOOGLE_MAP_API_KEY"]).replace(" ", "%20")
        
        print(transit_query)
        
        try:
            transit_response = requests.get(transit_query)
            transit_response = transit_response.json()

            steps = []

            if "routes" in transit_response and "legs" in transit_response["routes"][0]:

                if "departure_time" in transit_response["routes"][0]["legs"][0]:
                    starting_time = transit_response["routes"][0]["legs"][0]["departure_time"]["text"] + ":00"
                else: starting_time = None

                for step in transit_response["routes"][0]["legs"][0]["steps"]:
                    formated_step = {"main_instruction":  re.sub(r"<.*?>", "", step["html_instructions"]),
                                    "travel_mode": step["travel_mode"]}

                    if "steps" in step:
                        intermediary_stops = []

                        for intermediate_step in step["steps"]:
                            intermediary_data = {"travel_mode": intermediate_step["travel_mode"],
                                                "duration": math.ceil(intermediate_step["duration"]["value"]/60)}
                            
                            if "html_instructions" in intermediate_step:
                                intermediary_data["instructions"] = re.sub(r"<.*?>", "", intermediate_step["html_instructions"])
                            
                            intermediary_stops.append(intermediary_data)
                    
                    if "transit_details" in step:
                        formated_step["duration"] = math.ceil(step["duration"]["value"]/60)
                        formated_step["transit_name"] =  step["transit_details"]["line"]["name"]
                        
                        formated_step["short_name"] = step["transit_details"]["line"]["short_name"] if "short_name" in step["transit_details"]["line"] else None
                        formated_step["stops_num"] = step["transit_details"]["num_stops"]
                        formated_step["arrival_time"] = step["transit_details"]["arrival_time"]["text"]
                        formated_step["arrival_name"] = step["transit_details"]["arrival_stop"]["name"]
                        formated_step["departure_time"] = step["transit_details"]["departure_time"]["text"]
                        formated_step["departure_name"] = step["transit_details"]["departure_stop"]["name"]

                    formated_step["intermediary_stops"] = intermediary_stops
                    steps.append(formated_step)


            transit_trip = Trip(starting_station, 
                                finishing_station, 
                                str(starting_station.id) + str(finishing_station.id) + "_transit", 
                                math.ceil(transit_response["routes"][0]["legs"][0]["duration"]["value"])/60,
                                starting_station.name + finishing_station.name,
                                0, 0 ,[1, 1, 1, 1, 1, 1, 1],
                                starting_time= starting_time,
                                is_special_trip=True,
                                travel_type="TRANSIT",
                                special_trip_path=steps)
            
            self.add_trip_to_stations(starting_station, transit_trip)

        except Exception as e:
            transit_trip = None

        return transit_trip

    def back_tracking(self, last_node):
        path = []
        
        while last_node:
            if not last_node.ancestor:
                path.append({"starting_in": last_node.station.name})
                break

            if last_node.trip.is_special_trip:
                path.append({
                    "travel_type": last_node.trip.travel_type,
                    "coming_from": last_node.trip.coming_from.name,
                    "going_to": last_node.trip.going_to.name,
                    "duration": last_node.trip.duration,
                    "waiting_time": last_node.waiting_time,
                    "intermediate_steps": last_node.trip.special_trip_path,
                    "is_special_trip": True
                })
            else: 
                path.append({
                    "travel_type": last_node.trip.travel_type,
                    "coming_from": last_node.trip.coming_from,
                    "going_to": last_node.trip.going_to,
                    "duration": last_node.trip.duration,
                    "waiting_time": last_node.waiting_time,
                    "trip_id": last_node.trip.trip_id,
                    "starting_time": last_node.trip.starting_time.strftime("%H:%M") if last_node.trip.starting_time else None,
                    "is_special_trip": False
                })

            last_node = last_node.ancestor
        
        path.reverse()

        return path

    def a_star(self, steps_holder, wanted_date: datetime.datetime):

        # Convertit train stations en Node -> Sert à relié les points entre eux, principes basiques des Nodes dans A star
        # Utilise un dictionnaire avec les Nodes dedans, + simple pour les trouver que dans une Array
        node_dict: Dict[str, Node] = {}
        for step in steps_holder:
            step["departure"]: Node = Node(step["departure"])
            for stop_id in step["departure"].station.stops_id:
                node_dict[stop_id] = step["departure"]
            
            step["destination"]: Node = Node(step["destination"])
            for stop_id in step["destination"].station.stops_id:
                node_dict[stop_id] = step["destination"]
        
        paths = []

        for step in steps_holder:
            goal_node: Node = step["destination"]
            current_node: Node = step["departure"]

            current_node.set_distance_from_end(get_abs_distance(current_node.station, goal_node.station))
            # Distance heuristic
            current_node.set_heuristic_distance(current_node.distance_from_end + current_node.distance_from_start)
            # Augmente generation de 1 à chaque itération, permet de trouver le nombre d'étape avant de trouver le chemin
            current_node.generation = 0

            # set List avec un seul exemplaire par objet : l'idée -> 1 Node ^par liste pas de doublon
            visited = set()
            explored_next = set([current_node])

            # Liste des Nodes pas encore exploré
            while explored_next:

                # Prend Node avec cout moins élevé pour le custom
                current_node = get_lower_heuristic_node(explored_next)
                # On prend la node actuel, celle prise comme étant la plus courte actu
                # Dans la suite on va continuer dans cette idée de prendre comme prochaine Node, celle avec le coût le plus bas
                visited.add(current_node)

                print("Current node: {}".format(current_node))

                if current_node.station.name == goal_node.station.name: 
                    print("Trouvé")
                    break
            
                # Si la station est pas load (pas de trajet dedans, on vient la chargé pour avoir ces trajets possibles)
                # Prévient l'eventuelle miss de load
                if not current_node.station.is_loaded: 
                    self.load_trips(current_node.station)

                # SI on peut passé par metro ou route à pied, vient crée un trip et l'ajouter à la liste de trip dispo depuis cette node
                if current_node.station.has_special_travel: 
                    selected_city = None
                    for city in STATIONS_DICT:
                        if city is STATIONS_DICT.ALL_STATIONS: continue
                        if current_node.station.name in city.value:
                            selected_city = city.value

                    # Passe par l'API google
                    for station in selected_city:
                        if station == current_node.station.name: continue
                        
                        station = self.load_station(name=station)
                        self.load_trips(station)
                        self.load_google_api_transit_trip(current_node.station, station, departure_time = wanted_date + datetime.timedelta(minutes=current_node.distance_from_start))

                # Regarde tout les trajets possibles pour aller de Lille à quelques parts Et vient prendre le plus petit
                for possible_trip in current_node.station.trips:

                    # Vient se combiner à notre heure de départ
                    copied_date = copy.deepcopy(wanted_date)
                    copied_date = copied_date + datetime.timedelta(minutes=current_node.distance_from_start)
                    trip_object = current_node.station.trips[possible_trip]

                    # Pour éviter de revenir sur une Node antérieur
                    if current_node.ancestor and trip_object.going_to is current_node.ancestor.station: continue

                    # Prend la station et la traduit en Node pour faire des futurs calculs dessus
                    if not trip_object.going_to.stops_id[0] in node_dict:
                        future_node = Node(trip_object.going_to)
                        future_node.generation = current_node.generation + 1 
                        for stop_id in trip_object.going_to.stops_id: 
                            node_dict[stop_id] = future_node
                    else: 
                        future_node = node_dict[trip_object.going_to.stops_id[0]]
                    
                    # Vient faire les liens entre les nodes antérieurs et postérieurs
                    if future_node.generation != 0 and not future_node.ancestor: 
                        future_node.ancestor = current_node
                    
                    # Si pas de chemin attitré on prend celui là alors
                    if not future_node.trip:
                        future_node.trip = trip_object
                    
                    # Si la node à pas encore été calculé, on la calcul on la retourne
                    if future_node.distance_from_end == 9999999999:
                        distance_from_end = get_abs_distance(future_node.station, goal_node.station)
                        future_node.set_distance_from_end(distance_from_end)
                    
                    # Si jamais attente pour train, si pied pas d'attente. Sinon vient chercher le temps 
                    # qu'il y a entre l'heure et celle ou le bus démarre
                    if trip_object.is_special_trip and trip_object.travel_type == "WALKING":
                        extra_duration = 0
                    else:
                        # Vient s'ajouter ou coup total de l'objet ( prend en compte les jours)
                        if trip_object.starting_time:
                            extra_duration = self.duration_before_trip_available(trip_object, copied_date)
                        else: extra_duration = 0

                    # Calcul temps total pour le trajet + temps total pour plus tard
                    duration = current_node.distance_from_start + extra_duration + trip_object.duration

                    if future_node.generation != 0 and future_node.set_distance_from_start(duration):

                        future_node.ancestor = current_node
                        future_node.trip = trip_object
                        future_node.generation = current_node.generation + 1
                        future_node.waiting_time = extra_duration
                    
                        future_node.set_heuristic_distance(future_node.distance_from_start + future_node.distance_from_end)
                    
                    if future_node not in visited and future_node not in explored_next:
                        explored_next.add(future_node)

            if not explored_next:
                print("No stations to explore anymore.")

            path = {"path": self.back_tracking(current_node), "total_duration": current_node.distance_from_start, "sentenceID": step["sentenceID"]}
            paths.append(path)
            
            # Vient le trip le plus court sinon on le reset
            for item in node_dict:
                node_dict[item].reset_node()  
                  
        return paths

    def sanitize_station_input(self, travel_data):

        def first_verification(travel_data):
            first_step_verification = []

            for step in travel_data:
                first_step_verification.append(
                    {
                        "destination": check_station_name(step["destination"]),
                        "departure": check_station_name(step["departure"]),
                        "sentenceID": step["sentenceID"]
                    }
                )

            return first_step_verification
        
        def check_station_name(station: str):
            if station.lower() in self.stop_list:
                return station.lower()

            if station.lower() in ["paris", "capitale", "la capitale", "le théatre de l'histoire du comte de monte-cristo"]:
                return "paris"

            if station.lower() in ["lyon", "lion","la ville des céréales au caramel et chocolat"]:
                return "lyon"

            if station.lower() in ["lille", "l'école des epicopains", "le lieu de l'arnaque"]:
                return "lille"

            if station.lower() in ["marseille", "le lieu de naissance du comte de monte-cristo", "bouillabaisse-land"]:
                return "marseille"

            if station.lower() in ["aix-en-provence", "aix en provence", "aix", "là d'où vienne les herbes"]:
                "aix-en-provence"

            if station.lower() in ["limoges"]:
                return "limoges"
                    
            if station.lower() in ["strasbourg", "la ville des saucisses"]:
                return "strasbourg"
                    
            if station.lower() in ["nantes"]:
                return "nantes"
                    
            if station.lower() in ["rennes", "lieu de logements des esclaves du père noel", "les parents de chopper"]:
                return "rennes"
                    
            if station.lower() in ["grenoble"]:
                return "grenoble"
                    
            if station.lower() in ["metz"]:
                return "metz"
                    
            if station.lower() in ["metzervisse"]:
                return "metzervisse"

            if station.lower() in ["nice", "là où sont les gens sympas askip"]:
                return "nice"

            if station.lower() in ["rouen"]:
                return "rouen"

            if station.lower() in ["dijon", "ville de la moutarde"]:
                return "dijon"
            
            matched_station_ration = 0
            current_closest = None

            for possible_station in self.stop_list:
                if not possible_station: continue
                if station.lower() in possible_station:
                    ratio =  SequenceMatcher(None, station.lower(), possible_station).ratio()
                    if ratio > matched_station_ration and ratio > 0.5:
                        current_closest = possible_station
                        matched_station_ration = ratio
                    if ratio == 1.0: break
            if not current_closest:
                print("Station {} does not exist".format(station))
                
            return current_closest
        
        for step in travel_data:
            if not isinstance(step["departure"], str):
                print("{} is not a string.".format(step["departure"]))
                return None

            if not isinstance(step["destination"], str):
                print("{} is not a string.".format(step["destination"]))
                return None

        first_verification_stations = first_verification(travel_data)         
        
        for index, step in enumerate(first_verification_stations):
            if step["departure"] == None:
                print("Invalid departure for step {}".format(index))
                return False
            if step["destination"] == None:
                print("Invalid destination for step {}".format(index))
                return False
        
        # Enum des stations de metro
        special_stations = ["paris", "lille", "lyon", "marseille", "aix-en-provence", "limoges", 
                            "strasbourg", "nantes", "rennes", "grenoble", "metz", "metzervisse", 
                            "nice", "rouen", "dijon"]
        
        sanitized_steps = []
        
        for step in first_verification_stations:

            sanitized_step = {}
            sanitized_step["sentenceID"] = step["sentenceID"]

            if step["departure"] not in special_stations and step["destination"] not in special_stations:
                sanitized_step["departure"] = step["departure"]
                sanitized_step["destination"] = step["destination"]
                sanitized_steps.append(sanitized_step)
                continue

            if step["departure"] in special_stations and step["destination"] in special_stations:
                coming_from = self.get_special_stations(step["departure"])
                going_to = self.get_special_stations(step["destination"])

                coming_from_data = self.get_multiple_stations(coming_from)
                going_to_data = self.get_multiple_stations(going_to)

                current_min_distance = 999999
                coming_from_closest = None
                going_to_closest = None

                for item in coming_from_data:
                    first_sum = item[1] + item[2]
                    for second_item in going_to_data:
                        if item == second_item: continue

                        second_sum = second_item[1] + second_item[2]
                        if abs(first_sum - second_sum) < current_min_distance:
                            current_min_distance = abs(item[1] - second_item[1])
                            coming_from_closest = item[0]
                            going_to_closest = second_item[0]
                
                sanitized_step["departure"] = coming_from_closest.lower()
                sanitized_step["destination"] = going_to_closest.lower()
                sanitized_steps.append(sanitized_step)
                continue

            if step["departure"] not in special_stations and step["destination"] in special_stations:
                departure = self.get_multiple_stations([step["departure"]])[0]
                departure_sum = departure[1] + departure[2]

                multiple_stations = self.get_special_stations(step["destination"])
                multiple_stations = self.get_multiple_stations(multiple_stations)

                current_min_distance = 999999
                closest = None

                for item in multiple_stations:
                    second_sum = item[1] + item[2]

                    if abs(departure_sum - second_sum) < current_min_distance:
                        current_min_distance = abs(departure_sum - second_sum)
                        closest = item[0]
                
                sanitized_step["departure"] = step["departure"]
                sanitized_step["destination"] = closest.lower()
                sanitized_steps.append(sanitized_step)
                continue

            if step["destination"] not in special_stations and step["departure"] in special_stations:
                destination = self.get_multiple_stations([step["destination"]])[0]
                destination_sum = destination[1] + destination[2]

                multiple_stations = self.get_special_stations(step["departure"])
                multiple_stations = self.get_multiple_stations(multiple_stations)

                current_min_distance = 999999
                closest = None

                for item in multiple_stations:
                    second_sum = item[1] + item[2]

                    if abs(destination_sum - second_sum) < current_min_distance:
                        current_min_distance = abs(destination_sum - second_sum)
                        closest = item[0]
                
                sanitized_step["departure"] = closest.lower()
                sanitized_step["destination"] = step["destination"]
                sanitized_steps.append(sanitized_step)
                continue
                
        return sanitized_steps

    def load_stop_list(self):
        conn = connect_to_db()
        query = "SELECT LOWER(stop_name) FROM stops;"
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            stops = cursor.fetchall()
        except Exception as e:
            stops = None
            print(e)
        finally:
            cursor.close()
            conn.close()
        
        self.stop_list = [stop[0] for stop in stops]
    
    def search_lowest_distance_station(self, first_station: str, list_station: List[str]):

        conn = connect_to_db()
        query = """
            SELECT SUM(CAST(stop_lat AS numeric) + CAST(stop_lon AS numeric)) AS sum_first_station
            FROM stops
            WHERE LOWER(stop_name) = %s;"""
        try:
            cursor = conn.cursor()
            cursor.execute(query, (first_station,))
            first_station_long_lat = cursor.fetchone()
        except Exception as e:
            first_station_long_lat = None
            print(e)
        finally:
            cursor.close()
            conn.close()
        
        conn = connect_to_db()
        query = """
            SELECT LOWER(stop_name), stop_lat, stop_lon, ABS(%s - (stop_lat + stop_lon)) AS distance_difference
            FROM stops
            WHERE LOWER(stop_name) = ANY(%s)
            ORDER BY distance_difference
            LIMIT 1;"""
        try:
            cursor = conn.cursor()
            cursor.execute(query, (first_station_long_lat, [station.lower() for station in list_station], ))
            stop = cursor.fetchone()
        except Exception as e:
            stop = None
            print(e)
        finally:
            cursor.close()
            conn.close()
        
        return stop[0]

    def get_special_stations(self, name) -> List[str]:
        if name == "paris": return STATIONS_DICT.PARIS_STATIONS.value
        if name == "lyon": return STATIONS_DICT.LYON_STATIONS.value
        if name == "lille": return STATIONS_DICT.LILLE_STATIONS.value
        if name == "marseille": return STATIONS_DICT.MARSEILLE_STATIONS.value
        if name == "aix-en-provence": return STATIONS_DICT.AIX_PROVENCE_STATIONS.value
        if name == "limoges": return STATIONS_DICT.LIMOGES_STATIONS.value
        if name == "strasbourg": return STATIONS_DICT.STRASBOURG_STATIONS.value
        if name == "nantes": return STATIONS_DICT.NANTES_STATIONS.value
        if name == "rennes": return STATIONS_DICT.RENNES_STATIONS.value
        if name == "grenoble": return STATIONS_DICT.GRENOBLE_STATIONS.value
        if name == "metz": return STATIONS_DICT.METZ_STATIONS.value
        if name == "metzervisse": return STATIONS_DICT.METZERVISSE_STATIONS.value
        if name == "nice": return STATIONS_DICT.NICE_STATIONS.value
        if name == "rouen": return STATIONS_DICT.ROUEN_STATIONS.value
        if name == "dijon": return STATIONS_DICT.DIJON_STATIONS.value

    def get_multiple_stations(self, station_list: List[str]):
        conn = connect_to_db()
        query = """
            SELECT stop_name, stop_lat, stop_lon
            FROM stops
            WHERE LOWER(stop_name) = ANY(%s);"""
        try:
            cursor = conn.cursor()
            cursor.execute(query, ([station.lower() for station in station_list],))
            stations = cursor.fetchall()
        except Exception as e:
            stations = None
            print(e)
        finally:
            cursor.close()
            conn.close()
        
        return stations

    def load_all_stations_and_trip(self):

        start_time = time.time()
        
        conn = connect_to_db()
        query = """
                SELECT *
                FROM stops
            """
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query)
            stations = cursor.fetchall()
        except Exception as e:
            stations = None
            print(e)
        finally:
            cursor.close()
            conn.close()
        
        created_stations = {}


        for station in stations:
            if station["stop_name"] in created_stations:
                created_stations[station["stop_name"]].stops_id.append(station["stop_id"])
                self.station_manager[station["stop_id"]] = created_stations[station["stop_name"]]
            else:
                created_stations[station["stop_name"]] = {}
                new_station = TrainStation(name=station["stop_name"], long=station["stop_lon"], lat=station["stop_lat"],stops_id=[station["stop_id"]])
                created_stations[station["stop_name"]] = new_station
                self.station_manager[station["stop_id"]] = new_station
        
        chunked_lists = [stations[x:x+35] for x in range(0, len(stations), 35)]

    
        for index, chunk in enumerate(chunked_lists):
            print("Total stations {} loaded".format(str(index*35)))
            threads = []
            for station in chunk:
                t = threading.Thread(target=self.load_trips, args=[self.station_manager[station["stop_id"]]])
                t.start()
                threads.append(t)

            for thread in threads:
                thread.join()
        
        trip_count = 0
        for station in self.station_manager:
            trip_count += len(self.station_manager[station].trips)

        end_time = time.time()

        print("Finished loading stations in {}, station_count: {}, trip_count = {}.".format(str(end_time - start_time),str(len(self.station_manager)), str(trip_count)))


class Node:
    __slots__ = "station", "distance_from_start", "distance_from_end", "heuristic_distance", "ancestor", "trip", "generation", "waiting_time"

    def __init__(self, station: TrainStation) -> None:
        self.station: TrainStation = station
        self.trip: Trip = None
        self.distance_from_start: int = 0
        self.distance_from_end: int = 9999999999
        self.heuristic_distance: int = None
        self.ancestor: Node = None
        self.generation = None
        self.waiting_time = 0
    
    def set_distance_from_start(self, distance)-> bool:
        if self.distance_from_start == 0:
            self.distance_from_start = distance
            return True
        
        if self.distance_from_start > distance: 
            self.distance_from_start = distance
            return True
        
        return False
    
    def set_ancestor(self, ancestor):
        self.ancestor = ancestor

    def set_heuristic_distance(self, heuristic_distance):
        self.heuristic_distance = heuristic_distance
    
    def set_distance_from_end(self, distance):
        self.distance_from_end = distance

    def reset_node(self):
        self.distance_from_start: int = 0
        self.distance_from_end: int = 9999999999
        self.heuristic_distance: int = None
        self.ancestor: Node = None
        self.generation = None

    def __repr__(self) -> str:
        return "<Node station={} generation={} distance_from_start={} distance_from_end={} heuristic_distance={} ancestor={} >".format(
            self.station.name, 
            self.generation, 
            self.distance_from_start, 
            self.distance_from_end, 
            self.heuristic_distance, 
            self.ancestor.station.name if self.ancestor else None
        )

    def __hash__(self) -> int:
        return hash(str(self.station.name))
    
    def __lt__(self, other):
        return self.heuristic_distance < other.heuristic_distance


# Prise d'un temps moyen pour estimer le temps d'un point A à un point B
def get_abs_distance(first_station: TrainStation, second_station: TrainStation) -> int:
    # 0.01587212933 pour 1 minute
    # 0.2380819399999976 pour 15 min
    # 0.95232776 pour 60 min
    lat_diff = abs(first_station.latitude - second_station.latitude)
    long_diff = abs(first_station.longitude - second_station.longitude)
    diff = (lat_diff + long_diff)/(0.2380819399999976 / 15)
    return int(diff)

def get_lower_heuristic_node(node_list: List[Node]):
    lowest: Node = next(iter(node_list))
    
    for node in node_list:
        if lowest.heuristic_distance > node.heuristic_distance:
            lowest = node
    
    node_list.remove(lowest)
    return lowest

    



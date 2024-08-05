import argparse
from setup_db import setup_db
from map_class import Map
import datetime
from map_class import TrainStation
import time

def display_special_trip_data(trip):
    print("Temps total: ", trip["duration"])
    for index, step in enumerate(trip["intermediate_steps"]):
        print("------------------------------------------------")
        print("Etape {}".format(index + 1))
        print("Instruction principale: ", step["instructions"])
        print("Mode de transport: ", step["type"])
        if  step["type"] != "WALKING":

            print("Durée de transport en commun: ", step["duration"])
            print("Nom de ligne: ",step["transit_name"])
            print("Numéro de ligne: ",step["short_name"])
            print("Nombre d'arret avant arrivée: ", step["stops_num"])
            print("Nom de l'arret de départ: ", step["departure_name"])
            print("Heure de départ: ", step["departure_time"])
            print("Nom de l'arret d'arrivée: ", step["arrival_name"])
            print("Heure d'arrivée: ", step["arrival_time"])

        if "intermediary_stops" in step:
            for index_intermediary, intermediary_step in enumerate(step["intermediary_stops"]):
                print("-----------------")
                print("Etape intermédiaire {}".format(index_intermediary + 1))
                print("Durée :", intermediary_step["duration"])
                print("Mode de transport: ", intermediary_step["travel_mode"])
                if "instructions" in intermediary_step:
                    print("Instructions secondaires: ", intermediary_step["instructions"])

def detailled_travel(paths):
    travels = []

    for path in paths:
        travel = {"total_duration": path["total_duration"]}
        steps = []

        for step in path["path"]:
            
            if not "departure" in travel:
                travel["departure"] = step["starting_in"]
                continue

            if isinstance(step["going_to"], TrainStation): going_to = step["going_to"].name
            else: going_to = step["going_to"]

            step_infos = {
                "duration": step["duration"],
                "waiting_time": step["waiting_time"],
                "travel_type": step["travel_type"],
                "going_to": going_to
            }

            if "is_special_trip" in step and step["is_special_trip"]:
                intermediate_steps = []
                for intermediate_step in step["intermediate_steps"]:
                    intermediate_step_infos = {
                        "main_instruction": intermediate_step["instructions"],
                        "travel_type": intermediate_step["type"]}
                    
                    if intermediate_step["type"] != "WALKING":
                        intermediate_step_infos["duration"] = intermediate_step["duration"]
                        intermediate_step_infos["transit_name"] = intermediate_step["transit_name"]
                        intermediate_step_infos["short_name"] = intermediate_step["short_name"]
                        intermediate_step_infos["stops_count"] = intermediate_step["stops_num"]
                        intermediate_step_infos["departure_name"] = intermediate_step["departure_name"]
                        intermediate_step_infos["departure_time"] = intermediate_step["departure_time"]
                        intermediate_step_infos["arrival_name"] = intermediate_step["arrival_name"]
                        intermediate_step_infos["arrival_time"] = intermediate_step["arrival_time"]
                    
                    if "intermediary_stops" in intermediate_step:
                        second_intermediary_steps = []
                        for intermediary_stop in intermediate_step["intermediary_stops"]:
                            data = {"duration": intermediary_stop["duration"],
                                    "travel_type": intermediary_stop["travel_mode"]}
                            if "instructions" in intermediary_stop:
                                data["secondary_instructions"] = intermediary_stop["instructions"]
                            
                            second_intermediary_steps.append(data)
                        intermediate_step_infos["intermediary_stops"] = second_intermediary_steps

                    intermediate_steps.append(intermediate_step_infos)

                step_infos["intermediary_steps"] = intermediate_steps
            steps.append(step_infos)
            travel["steps"] = steps
            
            if step == path["path"][-1]:
                if isinstance(step["going_to"], TrainStation): travel["destination"] = step["going_to"].name
                else: travel["destination"] = step["going_to"]
        
        travels.append(travel)
    return travels

def short_travel(paths):
    travels = []

    for path in paths:
        travel = {}
        steps = []

        for step in path["path"]:
            if not "departure" in travel: 
                if "starting_in" in step: travel["departure"] = step["starting_in"]
                else: travel["departure"] = step["coming_from"]
                continue

            if step == path["path"][-1]:
                if isinstance(step["going_to"], TrainStation): travel["destination"] = step["going_to"].name
                else: travel["destination"] = step["going_to"]
                break
            
            if isinstance(step["going_to"], TrainStation): going_to = step["going_to"].name
            else: going_to = step["going_to"]

            steps.append(going_to)
        
        travel["steps"] = steps
        travels.append(travel)
    
    return travels

def keynote_format(paths):
    path_strings = []
    
    for path in paths:
        path_string = "{}, ".format(path["sentenceID"])
        for index, station in enumerate(path["path"]):
            if index == 0:
                path_string += station["starting_in"] + ", "
            else:
                if isinstance(station["going_to"], TrainStation):
                    path_string += station["going_to"].name + ", "
                else:
                    path_string += station["going_to"] + ", "
        path_string = path_string[:-2]
        path_strings.append(path_string)
    
    return path_strings


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check for docker flag.")
    parser.add_argument("-d", action="store_true")
    options = parser.parse_args()
    if not options.d:
        from dotenv import load_dotenv
        load_dotenv()
        data_path = "../project/data_sncf/"
    else:
        data_path = "./data/"
    
    setup_db(data_path)

    wanted_date = datetime.datetime(2023, 9, 21, 9, 27, 0)
    #wanted_date = datetime.datetime.now()

    map = Map()
    map.load_all_stations_and_trip()

    starting_time = time.time()
    travel_data = [
        {
        "departure": "Lille", 
        "destination": "Libercourt",
        "sentenceID": "1"
        }
    ]
    paths = map.load_path(travel_data, wanted_date)

    travel_data = [
        {
        "departure": "Lille", 
        "destination": "Calais Ville",
        "sentenceID": "1"
        },
        {
        "departure": "Paris", 
        "destination": "fjceghcoegvhifphi",
        "sentenceID": "2"
        }
    ]
    #paths = map.load_path(travel_data, datetime.datetime(2023, 9, 21, 9, 27, 0))
    ending_time = time.time()
    
    #starting_time_second = time.time()
    #paths = map.load_path(["Gare de Lille Europe", "Gare de Calais Ville", "Gare de Lille Flandres", "Gare de Lille Europe"], wanted_date)
    #ending_time_second = time.time()

    print("FIRST VERSION = {}".format(ending_time - starting_time))
    #print("SECOND VERSION = {}".format(ending_time_second - starting_time_second))

    if not paths: print("ERROR MON COCHON")
    else:
        formated_keynote = keynote_format(paths)

        print("------------\nFormat de la keynote:\n")
        for path in formated_keynote:
            print(path)

        short_path_format = short_travel(paths)

        print("--------------\nFormat minimal:\n")
        for point in short_path_format:
            print("Point départ: ",point["departure"])
            for step in point["steps"]: print(step)
            print("Point d'arrivée: ", point["destination"])

        detailled_path_format = detailled_travel(paths)

        print("--------------\nFormat détaillé:\n")
        for point in detailled_path_format:
            print("Point de départ: ",point["departure"])

            for step in point["steps"]:
                print("-----------")
                print("Durée de l'étape: ",step["duration"])
                print("Attente pour cette étape: ",step["waiting_time"])
                print("Type de transport: ",step["travel_type"])
                print("Destination intermédiaire: ", step["going_to"])
            
                if "intermediary_steps" in step:
                    for first_degree_step in step["intermediary_steps"]:
                        print("------")
                        print("Instruction principale: ", first_degree_step["main_instruction"])
                        print("Mode de transport de l'étape intermédiaire: ", first_degree_step["travel_type"])
                        if step["travel_type"] != "WALKING":
                            print("Durée de l'étape intermédiaire: ", first_degree_step["duration"])
                            print("Nom du transport: ", first_degree_step["transit_name"])
                            print("Nom de la ligne: ", first_degree_step["short_name"])
                            print("Nombre d'arrets: ", first_degree_step["stops_count"])
                            print("Arret de départ: ", first_degree_step["departure_name"])
                            print("Heure de départ: ", first_degree_step["departure_time"])
                            print("Arret de fin: ", first_degree_step["arrival_name"])
                            print("Heure de fin: ", first_degree_step["arrival_time"])

                        if "intermediary_stops" in first_degree_step:
                            for second_degree_step in first_degree_step["intermediary_stops"]:
                                print("---")
                                print("Durée de l'étape secondaire: ", second_degree_step["duration"])
                                print("Type de transport pour l'étape secondaire:", second_degree_step["travel_type"])
                                if "secondary_instructions" in second_degree_step:
                                    print("Instructions secondaires: ", second_degree_step["secondary_instructions"])
        
            print("Point d'arrivée: ", point["destination"])



import spacy
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv
import pandas as pd

nlp = spacy.load("fr_core_news_sm")

def connect_to_db():
    """Open a connexion to the database using the .env informations
    """
    connexion = psycopg2.connect(
        host=os.environ["DB_HOST"],
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        port=os.environ["DB_PORT"])

    return connexion

def create_table(query: str):
    """Take a query string to create a table and execute it
    """

    conn = connect_to_db()

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        cursor.close()
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        conn.close()

def extract_trip_info(sentence):
    doc = nlp(sentence)

    departure = None
    destination = None

    names = []
    check_name = []

    for ent in doc.ents:
        if ent.label_ in ("LOC", "GPE"):
            names.append(ent.text)   

    if len(names) < 2: return None, None
    if len(names) == 2: return names[0], names[1]

    count_found = 0
    for name in names:
        found = search_name_in_db(name)
        check_name.append(found)
        if found: count_found += 1
    
    if count_found == len(names):
        return names[0], names[1]

    for index, name in enumerate(names):
        if check_name[index]:
            if not departure: 
                departure = name
                continue
            if not destination:
                destination = name
    
    if departure and destination and departure != destination: return departure, destination
    else: return None, None

def filter_french_city(dataset):
    french_cities = []
    for line in dataset:
        if line[4] == "France":
            french_cities.append((line[0].lower(), line[1].lower(), line[9]))
    
    return french_cities

def save_in_db(query, data):
    conn = connect_to_db()
    conn.autocommit = True

    try:
        cursor = conn.cursor()
        psycopg2.extras.execute_values(cursor, query, data, page_size=500)
        cursor.close()
        conn.commit()

    except Exception as e:
        print(e)
    finally:
        conn.close()

def search_name_in_db(city_name):

    conn = connect_to_db()
    query = "SELECT * FROM french_cities WHERE city_name LIKE %s OR city_name_ascii LIKE %s;"

    

    try:
        cursor = conn.cursor()
        cursor.execute(query, (city_name.lower(), city_name.lower(),))
        data = cursor.fetchone()

        cursor.close()
    except Exception as e:
        print(e)
    finally:
        conn.close()

    if data: return True
    else: return False


load_dotenv()

query = "CREATE TABLE french_cities (id SERIAL PRIMARY KEY, city_name VARCHAR(255) NOT NULL, city_name_ascii VARCHAR(255), population INT)"
create_table(query)

query = "INSERT INTO french_cities (city_name, city_name_ascii, population) VALUES %s;"

dataset = pd.read_csv("./machine_learning/worldcities.csv")
dataset = list(dataset.itertuples(index=False, name=None))
dataset = filter_french_city(dataset)

save_in_db(query, dataset)

phrases = [
    "Je prévois de partir de Paris pour me rendre à Nice en vacances.",
    "Paris Lyon stp et fissa",
    "Wallah je suis pas fr",
    "Pourrais-je avoir un trajet allant de Marseille à Armentières je vous pries?",
    "Oh hi Mark !",
    "Je prévois de partir de Paris pour me rendre à Nice en vacances.",
    "Mon ami cherche à voyager de Bordeaux à Strasbourg en train.",
    "J'ai l'intention de faire un road trip de Marseille à Lyon avec ma famille.",
    "Elle rêve de prendre l'avion de Toulouse à Montpellier pour une escapade ensoleillée.",
    "Mon collègue envisage de prendre le bus de Lille à Nantes pour une réunion.",
    "Je vais partir de Paris pour me rendre à Bordeaux en train.",
    "Mon ami envisage de voyager de Marseille à Lyon en voiture.",
    "Nous prévoyons un vol de Nice à Toulouse pour nos vacances.",
    "Elle souhaite prendre le bus de Lille à Nantes pour visiter des amis.",
    "Mon collègue cherche à organiser un trajet de Strasbourg à Montpellier en avion.",
    "Nous préparons un voyage en train de Grenoble à Rennes en passant par Paris.",
]

for index, test_phrase in enumerate(phrases):
    print("----------------")
    print(index)
    print(test_phrase)
    departure, destination = extract_trip_info(test_phrase)
    print(departure, destination)

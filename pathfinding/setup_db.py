import os
import psycopg2
import psycopg2.extras
import ast
import pandas as pd

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

def check_table_exists(table_name: str) -> bool:
    """Return a boolean depending if the tables already exists or not
    True for existing, False if not
    """

    conn = connect_to_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = '{}');".format(table_name))
        result = cursor.fetchone()[0]
        cursor.close()
    except Exception as e:
        print(e)
    finally:
        conn.close()

    return result

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

def is_valid_list_string(string):
    try:
        parsed_list = ast.literal_eval(string)
        return isinstance(parsed_list, list)
    except (ValueError, SyntaxError):
        return False

def search_data_type_in_dict(dict):
    if not dict["data_array"]: return
    data_types = []

    for index, column in enumerate(dict["data_array"][0]):
        current_type = None

        for line in dict["data_array"]:
            if current_type == "string": break
            if pd.isna(line[index]): continue
            if is_valid_list_string(line[index]):current_type = "array"
            elif type(line[index]) == float: current_type = "float"
            elif type(line[index]) == int: current_type = "integer"
            else: current_type = "string"

        if current_type is not None:
            data_types.append({"name":dict["columns"][index],
                               "type":current_type, 
                               "index": index})
    
    return data_types
    
def get_distinct_cities():
    query = """
        SELECT DISTINCT trip_start
        FROM timetables
        UNION
        SELECT DISTINCT trip_end
        FROM timetables
    """

    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(query)
    cities_list = cursor.fetchall()
    cursor.close()
    conn.close()

    return cities_list

def create_train_station_list():
    query = """CREATE TABLE valid_train_stations (id SERIAL PRIMARY KEY, name VARCHAR(255));"""
    create_table(query)

    cities = get_distinct_cities()

    query = """INSERT INTO valid_train_stations (name) VALUES %s;"""
    save_in_db(query, cities)

def query_preper(query_type, table_name, table_params):
    if query_type == "table_creation":
        query = "CREATE TABLE {} (id SERIAL PRIMARY KEY".format(table_name)
        for index, param in enumerate(table_params):
            param_to_add = ", {}".format(param["name"])
            if param["type"] == "string": param_to_add += " VARCHAR(255)"
            if param["type"] == "integer": param_to_add += " INT"
            if param["type"] == "float": param_to_add += " FLOAT"
            if index + 1 == len(table_params): param_to_add += ");"
            query += param_to_add
        
        return query
    
    if query_type == "insert_data":
        query = "INSERT INTO {} (".format(table_name)

        for index, param in enumerate(table_params):
            if index == 0: 
                query += "{}, ".format(param["name"])
                continue
            if index + 1 == len(table_params): 
                query += param["name"]
                break

            query += "{}, ".format(param["name"])
        query += ") VALUES %s;"

        return query

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

def setup_db(data_path: str):

    data_dict = {}

    #Le path c'est /project/data_sncf si PC
    #/data si c'est du docker

    for file in os.listdir(data_path):
        data_dict[file] = {}
        if file == "timetables.csv":
            data = pd.read_csv("{}{}".format(data_path,file), delimiter="\t")
            data_dict[file]["columns"] = ["trip_id", "trip_start", "trip_end", "duration"]
            data_dict[file]["data_array"] = list(data.itertuples(index=False, name=None))

            data_types = [
                {"name": "trip_id","type": "string","index": 0},
                {"name": "trip_start","type": "string","index": 1},
                {"name": "trip_end","type": "string","index": 2},
                {"name": "duration","type": "integer","index": 3}
            ]

            query = query_preper(table_name= file.split(".")[0], table_params=data_types, query_type="table_creation")
            create_table(query)

            query = query_preper(table_name= file.split(".")[0], table_params=data_types, query_type="insert_data")

            values_to_save = []
            for line in data_dict[file]["data_array"]:
                new_data = line[1].split(" - ")
                if len(new_data) == 2:
                    start, end  = new_data[0], new_data[1]
                else:
                    start, end  = new_data[0] + " - " + new_data[1], new_data[2]
                values_to_save.append((line[0], start, end, int(line[2])))
            
            save_in_db(query, values_to_save)
            continue

        data = pd.read_csv("{}{}".format(data_path,file))
        data_dict[file]["columns"] = [col for col in data.columns]
        data_dict[file]["data_array"] = list(data.itertuples(index=False, name=None))

        data_types = search_data_type_in_dict(data_dict[file])
        if not data_types: continue

        query = query_preper(table_name= file.split(".")[0], table_params=data_types, query_type="table_creation")
        create_table(query)

        query = query_preper(table_name= file.split(".")[0], table_params=data_types, query_type="insert_data")
        
        values_to_save = []
        for line in data_dict[file]["data_array"]:
            values = []
            for column in data_types:     
                if line[column["index"]] == 0 or line[column["index"]] == "0": 
                    values.append(0)
                    continue
                if not line[column["index"]] or pd.isna(line[column["index"]]): 
                    values.append(None)
                    continue
                if column["type"] == "string": values.append(str(line[column["index"]]))
                if column["type"] == "integer": values.append(int(line[column["index"]]))
                if column["type"] == "float": values.append(float(line[column["index"]]))
            values_to_save.append(tuple(values))

        save_in_db(query, values_to_save)
    
    create_train_station_list()

    print("Setup finito")

        
    
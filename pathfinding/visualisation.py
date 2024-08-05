import streamlit as st
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
import argparse
from spacy import *
import spacy
import time
import datetime
import streamlit as st

from map_class import Map
from main import *
# from language_detection.language_detection import detect_language
# from store_sentence.store_sentence import storeSentence
# from store_sentence.get_id import getID
# from voice_recognization.reco_vocale import reco_vocale


############################ Language Detection ############################

from langdetect import detect

def detect_language(text):
    try:
        language = detect(text)
        return language
    except:
        return None


########################### Store sentences ################################
    

def storeSentence(id, sentence, code):
    text = str(sentence).replace('\n', ' ')
    with open('./store.txt', 'a', encoding='utf-8') as file:
        # Write content to the file
        file.write(f'{id}, {text}, {code}.\n')


################################## Get ID ##################################
    
def getID():
    with open('./store.txt', 'r') as file:
        lines = file.readlines()

    if lines:
        last_line = lines[-1].strip()

        elements = last_line.split(',')

        # Vérifier s'il y a au moins un élément après la division
        if elements:
            # Récupérer le premier élément avant la virgule
            premier_element = elements[0].strip()

            return premier_element
        else:
            return 0
    else:
        return 0



########################### Reconnaissance Vocale ################################

from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

def reco_vocale():
    recording_started = False

    stt_button = Button(label="Speak", width=100)

    stt_button.js_on_event("button_click", CustomJS(code="""
        mainScript();

        function mainScript() {
            const SpeechRecognition =
                window.SpeechRecognition || window.webkitSpeechRecognition;
            const SpeechGrammarList =
                window.SpeechGrammarList || window.webkitSpeechGrammarList;
            const SpeechRecognitionEvent =
                window.SpeechRecognitionEvent || window.webkitSpeechRecognitionEvent;

            const recordTime = 5000;
            const recognition = new SpeechRecognition();
            const speechRecognitionList = new SpeechGrammarList();
            let resInProgress = '';
            let res = '';

            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = "fr-FR";

            document.dispatchEvent(new CustomEvent("START_RECORDING", {detail: recordTime}));

            recognition.onresult = (event) => {
                resInProgress = event.results[0][0].transcript;
            };

            recognition.onspeechend = () => {
                res += ' ' + resInProgress;

                if (isEmptyOrSpaces(res)) {
                    res = 'Pas de phrase reconnue :/'
                }

                document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: res}));
            };

            sleep(recordTime).then(() => { recognition.stop(); });

            recognition.start();
        }    

        function isEmptyOrSpaces(str) {
            return str === null || str.match(/^ *$/) !== null;
        }

        function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }
        """))

    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT,START_RECORDING",
        key="listen",
        refresh_on_update=False,
        override_height=75,
        debounce_time=0)

    text_result = ''

    if result:
        if "GET_TEXT" in result:
            recording_started = True

            text_result = result.get("GET_TEXT")
            # st.write(text_result)
        if "START_RECORDING" in result and not recording_started:
            progress_text = "Recording in progress"
            my_bar = st.progress(0, text=progress_text)

            recording_started = True

            record_time = result.get("START_RECORDING") / 1000

            for percent_complete in range(100):
                time.sleep(record_time / 100)
                my_bar.progress(percent_complete + 1, text=progress_text)
            time.sleep(1)
            my_bar.empty()

    return text_result


##############################################################################


parser = argparse.ArgumentParser(description="Check for docker flag.")
parser.add_argument("-d", action="store_true")
options = parser.parse_args()
if not options.d:
    from dotenv import load_dotenv
    load_dotenv()
    data_path = "../project/data_sncf/"
else:
    data_path = "./data/"

map = Map()
# map.load_station("Gare de Paris Gare du Nord")
map.load_all_stations_and_trip()

def get_coordinates(station_name):
    geolocator = Nominatim(user_agent="streamlit_app")
    location = geolocator.geocode(f"{station_name}, France")
    return (location.latitude, location.longitude) if location else None

def plot_path_on_map(path):
    m = folium.Map(location=get_coordinates(path[0]), zoom_start=6)
 
    for i, station in enumerate(path):
        coords = get_coordinates(station)
        if coords:
            folium.Marker(coords, tooltip=station).add_to(m)
            if i < len(path) - 1:
                next_station = path[i + 1]
                next_coords = get_coordinates(next_station)
                if next_coords:
                    folium.PolyLine([coords, next_coords], color="blue").add_to(m)
 
    return m


##############################################################################


##############################################################################


def main():
    index = getID()

    code = ""

    if index is None:
        index = 1

    st.title("Travel Order Resolver!")

    nlp = spacy.load("../model_2")

    # Text input
    text_input = st.text_area("Enter your phrase here :")

    text_vocal = reco_vocale()

    if text_input:
        phrase = text_input
    elif text_vocal:
        phrase = text_vocal
    else:
        phrase = ""
    
    if 'clicked' not in st.session_state:
        st.session_state.clicked = False

    def click_button():
        st.session_state.clicked = True
    

    st.button('Validé', on_click=click_button)

    st.write("-----------")

    st.write("ID:", int(index)+1)
    st.write("Phrase:", phrase)

    if st.session_state.clicked:
        # st.slider('Select a value')
    
        detect_ville = []

        # Check if the user has entered a name
        if phrase:

            langue_detectee = detect_language(phrase)
            if langue_detectee == 'fr':
                nl = spacy.load("fr_core_news_sm")

                txt = phrase
                test_text = txt.lower().replace("la gare de ", "").replace("gare de ", "").replace("la gare ", "").replace("gare ", "").replace("rendre", "")
                
                
                doc = nl(txt)
                localisation = []

                for ent in doc.ents:
                    if ent.label_ == "LOC":  # Filtrez les entités qui sont des lieux
                        localisation.append(ent.text.lower())

                ville = []

                for i in range(0, len(localisation)):
                    ville.append(localisation[i].replace("la gare de ", "").replace("gare de ", "").replace("la gare ", "").replace("gare ", ""))
                
                doc = nlp(test_text.lower())

                if len(list(doc.ents)) == 2:
                    for ent in doc.ents:
                        for v in ville:
                            if str(ent) in v:
                                detect_ville.append([ent.label_, ent.text])
                                st.write("=>", ent.label_.lower(), ":", ent.text.upper())
                else:
                    test_text = txt.lower().replace("la gare de ", "").replace("gare de ", "").replace("la gare ", "").replace("gare ", "").replace("rendre", "")
                    doc = nlp(test_text.lower())

                    for ent in doc.ents:
                        for v in ville:
                            if str(ent) in v:
                                detect_ville.append([ent.label_, ent.text])
                                st.write("=>", ent.label_.lower(), ":", ent.text.upper())
                
        
                wanted_date = datetime.datetime(2023, 9, 21, 9, 27, 0)


                if len(detect_ville) == 2:
                    code = "OK"
                    storeSentence(int(index)+1, phrase, "OK")
                    st.write("Code:", code)
                    
                    if str(detect_ville[0][0]) == 'DEPART':
                        travel_data = [
                            {
                            "departure": str(detect_ville[0][1]),
                            "destination": str(detect_ville[1][1]),
                            "sentenceID": str(int(index)+1)
                            }
                        ]
                    else:
                        travel_data = [
                            {
                            "departure": str(detect_ville[1][1]),
                            "destination": str(detect_ville[0][1]),
                            "sentenceID": str(int(index)+1)
                            }
                        ]
                    paths = map.load_path(travel_data, wanted_date)

                    if not paths:
                        st.error("Erreur, Veuillez réessayer à saisir une nouvelle phrase en ajoutant la gare devant la ville ou mettre la première lettre de la ville en MAJUSCULE.")
                        return
                    else:
                        formated_keynote = keynote_format(paths)

                        st.write("------------\nFormat de la keynote:\n")
                        for path in formated_keynote:
                            st.write(path)

                        liste_separee = formated_keynote[0].split(', ')
                        liste_separee = liste_separee[1:]

                        detailled_path_format = detailled_travel(paths)

                        st.write("--------------\nFormat détaillé:\n")
                        for point in detailled_path_format:

                            for step in point["steps"]:
                                st.write("-----------")
                                st.write("Destination intermédiaire: ", step["going_to"])
                                st.write("Durée de l'étape: ",step["duration"])
                                st.write("Attente pour cette étape: ",step["waiting_time"])

                                if "intermediary_steps" in step:
                                    for first_degree_step in step["intermediary_steps"]:
                                        st.write("------")
                                        st.write("Instruction principale: ", first_degree_step["main_instruction"])
                                        st.write("Mode de transport de l'étape intermédiaire: ", first_degree_step["travel_type"])
                                        if step["travel_type"] != "WALKING":
                                            st.write("Durée de l'étape intermédiaire: ", first_degree_step["duration"])
                                            st.write("Nom du transport: ", first_degree_step["transit_name"])
                                            st.write("Nom de la ligne: ", first_degree_step["short_name"])
                                            st.write("Nombre d'arrets: ", first_degree_step["stops_count"])
                                            st.write("Arret de départ: ", first_degree_step["departure_name"])
                                            st.write("Heure de départ: ", first_degree_step["departure_time"])
                                            st.write("Arret de fin: ", first_degree_step["arrival_name"])
                                            st.write("Heure de fin: ", first_degree_step["arrival_time"])

                                        if "intermediary_stops" in first_degree_step:
                                            for second_degree_step in first_degree_step["intermediary_stops"]:
                                                st.write("---")
                                                st.write("Durée de l'étape secondaire: ", second_degree_step["duration"])
                                                st.write("Type de transport pour l'étape secondaire:", second_degree_step["travel_type"])
                                                if "secondary_instructions" in second_degree_step:
                                                    st.write("Instructions secondaires: ", second_degree_step["secondary_instructions"])

                    st.write("-----------")
                    
                    # Plot map
                    liste_sans_gare = [gare.replace('gare de ', '', 1) if gare.startswith('gare de ') else gare for gare in liste_separee]

                    map_fig = plot_path_on_map(liste_sans_gare)
                    folium_static(map_fig)
                elif len(detect_ville) == 1:
                    st.error("Il y a qu'une ville qui a été détecté.\nVeuillez réessayer à saisir une nouvelle phrase en ajoutant la gare devant la ville ou mettre la première lettre de la ville en MAJUSCULE.")
                else:
                    code = "NOT TRIP"
                    storeSentence(int(index)+1, phrase, "NOT TRIP")
                    st.error("Le résultat n'est pas correct, il y'a 0 ou plus de 2 villes")
            else:
                code = "NOT_FRENCH"
                storeSentence(int(index)+1, phrase, "NOT_FRENCH")
                st.error("La phrase n'est pas en français. Merci de rentrer une phrase en langue française")
                st.write("Code:", code)
        else:
            code = "NOT_TRIP’"
            storeSentence(int(index)+1, phrase, "NOT_TRIP’")
            st.error("Veuillez renseigner une phrase et valider")
            st.write("Code:", code)
    


if __name__ == "__main__":
    main()

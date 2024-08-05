from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import streamlit as st
import time

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

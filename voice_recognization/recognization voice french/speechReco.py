import speech_recognition
import pyttsx3
import sounddevice
import warnings
 
 
warnings.filterwarnings("ignore")
 
recognizer = speech_recognition.Recognizer()
recognizer.dynamic_energy_threshold = True
 
 
while True:
    try:
        with speech_recognition.Microphone() as mic:
            recognizer.adjust_for_ambient_noise(mic, duration=0.5)
            
            audio = recognizer.listen(mic)
 
            text = recognizer.recognize_google(audio, language="fr-FR", show_all=True)

            # text = recognizer.recognize_whisper(audio, language="french")
 
            # text = recognizer.recognize_sphinx(audio)
 
            # text = text.lower()
            # del audio, mic
            
            print(f"          {text}")
            # print("on repasse la boucle!!!!!")
            
            # la reduction du bruit est le principale problème de performance remarqué
    
    except speech_recognition.UnknownValueError:
        recognizer = speech_recognition.Recognizer()
        continue
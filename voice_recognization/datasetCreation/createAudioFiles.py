import pandas as pd
import time
import os
import sounddevice as sd
from scipy.io.wavfile import write
import keyboard

# Charger le fichier CSV
df = pd.read_csv("texte.csv")

# Créer un dossier pour stocker les fichiers audio s'il n'existe pas déjà
output_folder = "audio_files"
os.makedirs(output_folder, exist_ok=True)

# Configuration de l'enregistrement audio
sample_rate = 44100  # fréquence d'échantillonnage en Hz
duration = 10  # durée de l'enregistrement en secondes

# Fonction pour afficher le texte avec un compte à rebours et créer le fichier audio
def process_line(row):
    print(f"Normalized Transcription: {row['normalized_transcription']}")
    
    for i in range(3, 0, -1):
        print(f"Reading in {i} seconds...")
        time.sleep(1)

    # Enregistrement audio
    print("Start speaking now...")
    audio_data = sd.rec(int(sample_rate * duration), samplerate=sample_rate, channels=2, dtype='int16')
    sd.wait()

    # Exporter le fichier audio dans le dossier spécifié
    file_path = os.path.join(output_folder, f"{row['file_name']}.wav")
    write(file_path, sample_rate, audio_data)
    print(f"Audio file exported to: {file_path}")

# Parcourir les lignes du DataFrame
for index, row in df.iterrows():
    process_line(row)
    
    # Attente de l'utilisateur pour passer à la ligne suivante
    print("Press any key to continue...")
    keyboard.read_event(suppress=True)

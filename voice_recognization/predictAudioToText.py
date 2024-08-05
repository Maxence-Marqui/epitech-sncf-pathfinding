import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from pydub import AudioSegment
import matplotlib.pyplot as plt


def CTCLoss(y_true, y_pred):
    # Compute the training-time loss value
    batch_len = tf.cast(tf.shape(y_true)[0], dtype="int64")
    input_length = tf.cast(tf.shape(y_pred)[1], dtype="int64")
    label_length = tf.cast(tf.shape(y_true)[1], dtype="int64")

    input_length = input_length * tf.ones(shape=(batch_len, 1), dtype="int64")
    label_length = label_length * tf.ones(shape=(batch_len, 1), dtype="int64")

    loss = keras.backend.ctc_batch_cost(y_true, y_pred, input_length, label_length)
    return loss

# Load your pre-trained model
model = keras.models.load_model('model.h5', custom_objects={'CTCLoss': CTCLoss})

# The set of characters accepted in the transcription.
characters = [x for x in "abcdefghijklmnopqrstuvwxyz'?! "]
# Mapping characters to integers
char_to_num = keras.layers.StringLookup(vocabulary=characters, oov_token="")
# Mapping integers back to original characters
num_to_char = keras.layers.StringLookup(
    vocabulary=char_to_num.get_vocabulary(), oov_token="", invert=True
)

print(
    f"The vocabulary is: {char_to_num.get_vocabulary()} "
    f"(size ={char_to_num.vocabulary_size()})"
)

# Uniformisation du son
def uniformize_audio(audio_file1, audio_file2):
    sound1 = AudioSegment.from_file(audio_file1)
    sound2 = AudioSegment.from_file(audio_file2)

    # Récupérer les données audio en tant que tableaux NumPy
    data1 = np.array(sound1.get_array_of_samples())
    data2 = np.array(sound2.get_array_of_samples())

    # Calculer le facteur d'ajustement d'amplitude
    gain_factor = np.max(data1) / np.max(data2)

    # Ajuster l'amplitude du deuxième son en fonction du facteur de gain
    adjusted_sound2 = sound2 - 20 * np.log10(gain_factor)

    # Sauvegarder le deuxième son uniformisé
    adjusted_sound2.export(audio_file2, format="wav")

    # Save the chunk to a new file
    adjusted_sound2.export(f"test.wav", format="wav")


# An integer scalar Tensor. The window length in samples.
frame_length = 256
# An integer scalar Tensor. The number of samples to step.
frame_step = 160
# An integer scalar Tensor. The size of the FFT to apply.
# If not provided, uses the smallest power of 2 enclosing frame_length.
fft_length = 384
def encode_single_sample(wav_file):
    ###########################################
    ##  Process the Audio
    ##########################################
    # 1. Read wav file
    file = tf.io.read_file(wav_file)
    # 2. Decode the wav file
    audio, _ = tf.audio.decode_wav(file)
    audio = tf.squeeze(audio, axis=-1)
    # 3. Change type to float
    audio = tf.cast(audio, tf.float32)
    # 4. Get the spectrogram
    spectrogram = tf.signal.stft(
        audio, frame_length=frame_length, frame_step=frame_step, fft_length=fft_length
    )
    # 5. We only need the magnitude, which can be derived by applying tf.abs
    spectrogram = tf.abs(spectrogram)
    spectrogram = tf.math.pow(spectrogram, 0.5)
    # 6. normalisation
    means = tf.math.reduce_mean(spectrogram, 1, keepdims=True)
    stddevs = tf.math.reduce_std(spectrogram, 1, keepdims=True)
    spectrogram = (spectrogram - means) / (stddevs + 1e-10)

    return spectrogram

def decode_batch_predictions(pred):
    input_len = np.ones(pred.shape[0]) * pred.shape[1]
    # Use greedy search. For complex tasks, you can use beam search
    results = keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0]
    # Iterate over the results and get back the text
    output_text = []
    for result in results:
        result = tf.strings.reduce_join(num_to_char(result)).numpy().decode("utf-8")
        output_text.append(result)
    return output_text

# Chemin des fichiers audio à uniformiser
audio_file1 = "audio_1.wav"  # Remplacez par le chemin du premier fichier audio
audio_file2 = "audio_1.wav"  # Remplacez par le chemin du deuxième fichier audio

# Uniformiser le son
# uniformize_audio(audio_file1, audio_file2)

# Predict the transcription using the pre-trained model
audio = encode_single_sample(audio_file2)
predictions = model.predict(np.expand_dims(audio, axis=0))
predicted_text = decode_batch_predictions(predictions)[0]

# Print the predicted text
print("Predicted Text:", predicted_text)


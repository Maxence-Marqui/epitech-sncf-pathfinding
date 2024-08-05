from pydub import AudioSegment

# Input audio file
input_file = "audio.wav"

# Length of each chunk in milliseconds (10 seconds = 10,000 milliseconds)
chunk_length_ms = 10000

# Load the audio file
audio = AudioSegment.from_wav(input_file)

# Calculate the total duration of the audio
total_duration = len(audio)

# Initialize the start and end points for the first chunk
start_time = 0
end_time = chunk_length_ms

# Counter to keep track of the chunk number
chunk_number = 1

# Loop through the audio and create chunks
while start_time < total_duration:
    # Ensure the end_time does not exceed the total_duration
    if end_time > total_duration:
        end_time = total_duration

    # Extract the chunk
    chunk = audio[start_time:end_time]

    # Save the chunk to a new file
    chunk.export(f"chunk_{chunk_number}.wav", format="wav")

    # Move to the next chunk
    start_time = end_time
    end_time += chunk_length_ms
    chunk_number += 1

print("Audio has been split into 10-second chunks.")

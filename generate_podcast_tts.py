from TTS.api import TTS
import os

def split_text(text, max_length=1000):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        if len(' '.join(current_chunk)) + len(word) < max_length:
            current_chunk.append(word)
        else:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

# Initialize TTS
#tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

# Read text from file
input_file = "hn_transcript_09242024.txt"
with open(input_file, 'r') as file:
    text = file.read()

# Split text into chunks
chunks = split_text(text)

# Generate speech for each chunk
output_file = "output.mp3"
for i, chunk in enumerate(chunks):
    temp_file = f"temp_{i}.mp3"
    tts.tts_to_file(text=chunk, file_path=temp_file, speaker_wav="samples_en_sample.wav", language="en")

# Combine temporary files (requires pydub)
from pydub import AudioSegment

combined = AudioSegment.empty()
for i in range(len(chunks)):
    temp_file = f"temp_{i}.mp3"
    audio = AudioSegment.from_mp3(temp_file)
    combined += audio
    os.remove(temp_file)

combined.export(output_file, format="mp3")

print(f"Audio saved to {os.path.abspath(output_file)}")
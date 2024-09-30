import time
import nltk
import os
import sys
from pathlib import Path
from nltk.tokenize import sent_tokenize
from unrealspeech import UnrealSpeechAPI, save
from pydub import AudioSegment
from dotenv import load_dotenv
from datetime import datetime

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
# Load environment variables from the .env file
load_dotenv()

# OpenAI API key
UNREAL_API_KEY = os.getenv('UNREAL_API_KEY')

# Initialize UnrealSpeechAPI client
speech_api = UnrealSpeechAPI(UNREAL_API_KEY)

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def chunk_text(text, max_chars=950):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += sentence + " "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def process_chunks(chunks, temp_dir):
    audio_files = []
    
    for i, chunk in enumerate(chunks):
        try:
            audio_data = speech_api.stream(
                text=chunk,
                voice_id="Liv",  # or Zoe 
                bitrate="192k"
            )
            file_name = temp_dir / f"audio_chunk_{i+1}.mp3"
            save(audio_data, file_name)
            audio_files.append(file_name)
            print(f"Processed and saved chunk {i+1}: {chunk[:30]}...")
        except Exception as e:
            print(f"Error processing chunk {i+1}: {str(e)}")
        time.sleep(1)  # Respect rate limit
    return audio_files

def concatenate_audio_files(audio_files, output_file):
    combined = AudioSegment.empty()
    for file in audio_files:
        sound = AudioSegment.from_mp3(file)
        combined += sound
    combined.export(output_file, format="mp3")
    print(f"All audio files concatenated into {output_file}")



# Main execution
if __name__ == "__main__":

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = f'output/hn_transcript_{datetime.now().strftime("%m%d%Y")}.txt'

    output_file = input_file.replace('.txt', '.mp3')
    # Create a temporary directory for audio chunks
    temp_dir = Path("temp_audio_chunks")
    temp_dir.mkdir(exist_ok=True)

    # Read and process the text
    text = read_file(input_file)
    chunks = chunk_text(text)
    audio_files = process_chunks(chunks, temp_dir)

    print(f"Generated {len(audio_files)} audio files.")

    # Concatenate all audio files
    concatenate_audio_files(audio_files, output_file)

    # Clean up temporary files
    for file in temp_dir.glob("*.mp3"):
        file.unlink()
    temp_dir.rmdir()

    print(f"Podcast saved to {output_file}")
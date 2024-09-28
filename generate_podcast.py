import sys
import datetime
from pathlib import Path
from dotenv import load_dotenv
import os
import re
from openai import OpenAI
from pydub import AudioSegment
from datetime import datetime

# Load environment variables from the .env file
load_dotenv()

# OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
client = OpenAI()


def split_into_sentences(text):
    # Simple sentence splitting - you might want to use a more sophisticated method
    return re.findall(r'[^.!?\s][^.!?]*(?:[.!?](?![\'\"]?\s|$)[^.!?]*)*[.!?]?[\'\"]?(?=\s|$)', text)


def chunk_sentences(sentences, target_chunk_size=1000):
    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        sentence_size = len(sentence)
        if current_size + sentence_size > target_chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_size = 0
        current_chunk.append(sentence)
        current_size += sentence_size

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def generate_tts_chunks(input_file, target_chunk_size=1000):
    # Read the input text file
    with open(input_file, "r") as file:
        text = file.read()

    print(f"Estimated cost: {round(len(text)*15.0/1000000.0, 2)} USD")
    # Split the text into sentences and then into chunks
    sentences = split_into_sentences(text)
    chunks = chunk_sentences(sentences, target_chunk_size)

    # Create a temporary directory for audio chunks
    temp_dir = Path("temp_audio_chunks")
    temp_dir.mkdir(exist_ok=True)

    # select voice based on day of the week
    # 0 = Monday, 1 = Tuesday, ..., 6 = Sunday
    voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "echo"]
    dayofweek = datetime.today().weekday()
    voice = voices[dayofweek]

    # Process each chunk
    for i, chunk in enumerate(chunks):
        speech_file_path = temp_dir / f"speech_chunk_{i:03d}.mp3"
        #print(f"Generating audio for chunk {i+1}/{len(chunks)}")

        with client.audio.speech.with_streaming_response.create(
            model="tts-1",
            voice=voice,
            input=chunk
        ) as response:
            # Stream the response content to a file
            with open(speech_file_path, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
    
        #response.stream_to_file(speech_file_path)

    #print(f"Generated {len(chunks)} audio files.")
    return temp_dir

def concatenate_audio_chunks(chunk_directory, output_file):
    # Get all MP3 files in the directory
    audio_chunks = [f for f in os.listdir(chunk_directory) if f.endswith('.mp3')]
    
    # Sort the chunks
    audio_chunks.sort()

    # Create an empty AudioSegment
    combined = AudioSegment.empty()

    # Iterate through the audio chunks and append them to the combined audio
    for chunk_file in audio_chunks:
        chunk_path = os.path.join(chunk_directory, chunk_file)
        audio_chunk = AudioSegment.from_mp3(chunk_path)
        combined += audio_chunk

    # Export the combined audio as a single MP3 file
    combined.export(output_file, format="mp3")
    #print(f"Concatenated {len(audio_chunks)} chunks into {output_file}")

# Main execution
if __name__ == "__main__":

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = f'output/hn_transcript_{datetime.now().strftime("%m%d%Y")}.txt'

    output_file = input_file.replace('.txt', '.mp3')
    target_chunk_size = 1000  # Target characters per chunk

    # Generate TTS chunks
    temp_dir = generate_tts_chunks(input_file, target_chunk_size)

    # Concatenate chunks
    concatenate_audio_chunks(temp_dir, output_file)

    # Clean up temporary files
    for file in temp_dir.glob("*.mp3"):
        file.unlink()
    temp_dir.rmdir()

    print(f"Podcast saved to {output_file}")

    
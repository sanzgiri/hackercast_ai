import requests
from pydub import AudioSegment
from pydub.playback import play
from dotenv import load_dotenv
import os
import sys

# Load environment variables from the .env file
load_dotenv()

# ElevenLabs API key
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

# Function to generate speech from text using ElevenLabs
def text_to_speech(text, voice_id):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        'xi-api-key': ELEVENLABS_API_KEY,
        'Content-Type': 'application/json'
    }

    data = {
        "text": text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to generate speech: {response.status_code}, {response.text}")

# Function to generate the podcast
def generate_podcast(summaries, male_voice_id, female_voice_id):
    podcast_segments = []

    for i, summary in enumerate(summaries):
        voice_id = male_voice_id if i % 2 == 0 else female_voice_id
        audio_data = text_to_speech(summary, voice_id)

        # Save the audio file
        audio_file_path = f'summary_{i}.mp3'
        with open(audio_file_path, 'wb') as audio_file:
            audio_file.write(audio_data)

        # Load the audio segment and append it to the podcast segments
        segment = AudioSegment.from_mp3(audio_file_path)
        podcast_segments.append(segment)

    # Concatenate all segments into a single podcast
    podcast = sum(podcast_segments)

    # Save the final podcast
    podcast.export("podcast.mp3", format="mp3")

    # Optionally, play the podcast
    # play(podcast)


def main():

    # add cmd line args from user on source bb or hn
    src = sys.argv[1]
    summary_file = f'{src}_summaries_latest.txt'

    # Replace these with actual voice IDs from ElevenLabs
    male_voice_id = 'onwK4e9ZLuTAKqWW03F9' # Daniel
    female_voice_id = 'XrExE9yKIg1WjnnlVkGX' # Matilda

    # read summaries from file into a list
    with open(summary_file, 'r') as f:
        summaries = f.readlines()

    generate_podcast(summaries, male_voice_id, female_voice_id)



if __name__ == "__main__":
    main()

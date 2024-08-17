import requests
from pydub import AudioSegment
from pydub.playback import play
from dotenv import load_dotenv
import os
import sys
import json

# Load environment variables from the .env file
load_dotenv()

# ElevenLabs API key
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

# Function to generate speech from text using ElevenLabs
def generate_speech_from_text(text: str, voice_id: str) -> bytes:
    """
    Generate speech from text using ElevenLabs API.

    Args:
        text (str): The text to convert to speech.
        voice_id (str): The voice ID to use for the speech.

    Returns:
        bytes: The audio data in bytes.
    """
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
def create_podcast(summary_list: list[str], male_voice: str, female_voice: str) -> None:
    """
    Generate a podcast from a list of summaries using male and female voices.

    Args:
        summary_list (list[str]): List of summaries to include in the podcast.
        male_voice (str): Voice ID for the male voice.
        female_voice (str): Voice ID for the female voice.

    Returns:
        None
    """
    podcast_segments = []

    for i, summary in enumerate(summary_list):
        voice_id = male_voice if i % 2 == 0 else female_voice
        audio_data = generate_speech_from_text(summary, voice_id)

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


def main() -> None:
    """
    Main function to generate a podcast from summaries based on user input.

    Args:
        None

    Returns:
        None
    """

    # add cmd line args from user on source bb or hn
    src = sys.argv[1]
    interval = sys.argv[2]

    with open('config.json', 'r') as f:
        config = json.load(f)

    if interval not in config:
        raise ValueError("Unsupported interval. Use 'daily', 'weekly', or 'monthly'.")

    if src not in config[interval]:
        raise ValueError(f"Source '{src}' not configured for interval '{interval}'.")

    summary_file = f'{src}_summaries_latest.txt'

    # Replace these with actual voice IDs from ElevenLabs
    male_voice = 'onwK4e9ZLuTAKqWW03F9' # Daniel
    female_voice = 'XrExE9yKIg1WjnnlVkGX' # Matilda

    # read summaries from file into a list
    with open(summary_file, 'r') as f:
        summary_list = f.readlines()

    create_podcast(summary_list, male_voice, female_voice)



if __name__ == "__main__":
    main()

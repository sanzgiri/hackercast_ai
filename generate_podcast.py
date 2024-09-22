from dotenv import load_dotenv
import os
import sys
from openai import OpenAI
from pydub import AudioSegment
from pydub.playback import play
import datetime

# Load environment variables from the .env file
load_dotenv()

# OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


# Function to generate the podcast
def create_podcast(summary_file: str, voice: str) -> None:
    """
    Generate a podcast from a list of summaries using male and female voices.

    Args:
        summary: text to include in the podcast.
        voice (str): Voice ID for the voice.

    Returns:
        None
    """

    client = OpenAI()
    audio_file_path = summary_file.replace('.txt', '.mp3')
    print("Generating podcast...")

    # read summary from file
    with open(summary_file, 'r') as f:
        summary= f.read()

    # split summary into 4096 character chunks
    summary = [summary[i:i+4096] for i in range(0, len(summary), 4096)]

    # generate speech from text using OpenAI API
    for i, s in enumerate(summary):
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=s
        )
        response.stream_to_file(f"temp_{i}.mp3")

    # combine audio files
    combined = AudioSegment.empty()
    for i in range(len(summary)):
        combined += AudioSegment.from_mp3(f"temp_{i}.mp3")
        os.remove(f"temp_{i}.mp3")

    combined.export(audio_file_path, format="mp3")
    print("Podcast generated successfully!")
    print(f"Podcast saved to {audio_file_path}")

    # Calculate tokens and estimate cost
    tokens_used = len(summary)
    cost_per_1M_tokens = 15
    estimated_cost = (tokens_used / 1000000) * cost_per_1M_tokens
    print(f"Estimated cost: ${estimated_cost:.4f}"))

    # Optionally, play the podcast
    # play(audio_file_path)


def main() -> None:
    """
    Main function to generate a podcast from summaries based on user input.

    Args:
        None

    Returns:
        None
    """
    summary_file = sys.argv[1]
    # select voice based on day of the week
    # 0 = Monday, 1 = Tuesday, ..., 6 = Sunday
    voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "echo"]

    dayofweek = datetime.datetime.today().weekday()
    voice = voices[dayofweek]
    create_podcast(summary_file, voice)


if __name__ == "__main__":
    summary_file = sys.argv[1]
    main()

import sys
import datetime
from podcast_creator import create_podcast


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

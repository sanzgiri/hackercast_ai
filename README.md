# Project Overview

This project is designed to generate podcasts from summarized content. It fetches top stories from various sources, summarizes them, and then uses text-to-speech to create audio files.

## File Descriptions

- **generate_podcast.py**: Contains functions to create a podcast from a summary file using a specified voice.
  - **Run**: `python generate_podcast.py <summary_file>`
- **generate_podcast_elevenlabs.py**: Similar to `generate_podcast.py`, but uses ElevenLabs for text-to-speech conversion.
  - **Run**: `python generate_podcast_elevenlabs.py <summary_file> <voice_id>`
- **generate_summaries.py**: Fetches top stories from different sources and summarizes them.
  - **Run**: `python generate_summaries.py <source> <interval> <num_stories>`
- **get_bb_summaries.py**: Script to get summaries specifically from the BBC.
  - **Run**: `python get_bb_summaries.py <num_stories> <interval>`
- **get_hn_summaries.py**: Script to get summaries specifically from Hacker News.
  - **Run**: `python get_hn_summaries.py <num_stories> <interval>`
- **get_voices.py**: Utility to fetch available voices for text-to-speech conversion.
  - **Run**: `python get_voices.py`
- **config.json**: Configuration file containing settings and parameters for the project.
- **Todo.md**: A markdown file listing tasks and features to be implemented or improved.
- **.gitignore**: Specifies files and directories to be ignored by git.

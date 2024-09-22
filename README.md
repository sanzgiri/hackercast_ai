# Project Overview

This project is designed to generate podcasts from summarized content. It fetches top stories from various sources, summarizes them, and then uses text-to-speech to create audio files.

## File Descriptions

- **generate_summaries.py**: Fetches top stories from different sources and summarizes them.
  - **Run**: `python generate_summaries.py <source> <interval> <num_stories>`

- **generate_podcast.py**: Contains functions to create a podcast from a summary file using a specified voice.
  - **Run**: `python generate_podcast.py <summary_file>`


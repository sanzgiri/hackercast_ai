# HackerCast AI - Automated Daily Podcast Generation

This project automatically generates daily podcasts from Hacker News top stories using AI summarization and text-to-speech.

## Architecture Overview

The system has a **3-step pipeline** that runs daily:

1. **📝 generate_summaries_hn.py** - Fetches and summarizes top Hacker News stories
2. **🎵 generate_podcast_unreal.py** - Converts summaries to high-quality MP3 audio  
3. **📡 publish_podcast.py** - Publishes to GitHub with Apple Podcasts-compatible RSS feed

## File Descriptions

- **generate_summaries_hn.py**: Fetches top stories from Hacker News via GitHub API and creates AI summaries
  - **Run**: `python generate_summaries_hn.py daily 10`
  - **Features**: File existence check to avoid regenerating content and wasting API tokens

- **generate_podcast_unreal.py**: Converts text summaries to MP3 using UnrealSpeech API
  - **Run**: `python generate_podcast_unreal.py`
  - **Features**: Chunk processing, audio concatenation, file existence check

- **publish_podcast.py**: Uploads MP3 to GitHub and generates RSS feed for podcast platforms
  - **Run**: `python publish_podcast.py --date MMDDYYYY`
  - **Features**: Smart file routing (GitHub <25MB, Google Drive fallback), Apple Podcasts compliance

## Quick Setup

```bash
git clone https://github.com/sanzgiri/hackercast_ai.git
cd hackercast_ai

# Setup environment
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Create output directories
mkdir output logs

# Create .env file with API keys
cp env.template .env
# Add your API keys: OPENAI_API_KEY, GITHUB_API_KEY, UNREAL_API_KEY

# Test the pipeline manually
python generate_summaries_hn.py daily 10
python generate_podcast_unreal.py  
python publish_podcast.py
```

## Daily Automation with launchd

The system runs automatically every day at 9 AM using macOS launchd:

```bash
# Install the daily automation
cp com.sanzgiri.podcastgeneration.plist ~/Library/LaunchAgents
chmod 644 ~/Library/LaunchAgents/com.sanzgiri.podcastgeneration.plist
launchctl load ~/Library/LaunchAgents/com.sanzgiri.podcastgeneration.plist

# Check if it's loaded
launchctl list | grep com.sanzgiri.podcastgeneration

# View logs
tail -f logs/podcast_generation.log

# Stop automation (if needed)
launchctl unload ~/Library/LaunchAgents/com.sanzgiri.podcastgeneration.plist
```

## Key Features

### 🧠 Smart Token Conservation
- **File existence checks** prevent regenerating existing content
- Saves OpenAI and UnrealSpeech API costs by skipping completed steps
- Safe to run multiple times - only processes missing files

### 🎯 Apple Podcasts Compliance  
- **GitHub-hosted MP3s** with proper `.mp3` URL extensions
- **Complete RSS feed** with iTunes namespace elements
- **1400x1400 cover art** meeting platform requirements
- **Automatic file size routing** (GitHub <25MB, Google Drive fallback)

### 📊 Storage Analysis
- **Small episodes (<5MB)**: GitHub free tier perfect
- **Medium episodes (5-25MB)**: GitHub works, monitor usage  
- **Large episodes (>25MB)**: Automatic Google Drive fallback with cost recommendations

### 🔧 Production Ready
- **Comprehensive logging** with timestamps
- **Error handling** and graceful failures  
- **Automated cleanup** of temporary files
- **Environment isolation** with proper PATH handling

## Outputs

All files are stored in the `output/` directory:
- `hn_transcript_MMDDYYYY.txt` - Summarized stories
- `hn_transcript_MMDDYYYY.mp3` - Generated podcast audio
- `hn_td_MMDDYYYY.txt` - Episode metadata
- `rss` - RSS feed file (uploaded to GitHub)

## Live RSS Feed

**🎯 Podcast RSS URL**: `https://raw.githubusercontent.com/sanzgiri/podcast-feed/main/rss`

Use this URL to subscribe in:
- Apple Podcasts
- Spotify for Podcasters  
- Google Podcasts
- Any podcast directory

## Manual Commands

```bash
# Generate summaries only
python generate_summaries_hn.py daily 10

# Generate audio only (requires existing summary)
python generate_podcast_unreal.py

# Publish only (requires existing MP3)
python publish_podcast.py --date 10142025

# Run complete pipeline manually
bash run_podcast_generation.sh
```
```
cp com.sanzgiri.podcastgeneration.plist ~/Library/LaunchAgents
chmod 644 ~/Library/LaunchAgents/com.sanzgiri.podcastgeneration.plist
launchctl load ~/Library/LaunchAgents/com.sanzgiri.podcastgeneration.plist
```
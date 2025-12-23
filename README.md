# HackerCast AI - Automated Daily Podcast from Hacker News

Automatically generates daily podcasts from Hacker News top stories using AI summarization and text-to-speech, hosted on AWS S3 with Apple Podcasts-compliant RSS feed.

## 🎙️ What It Does

Every day at 9 AM, this system:
1. � Fetches top stories from Hacker News
2. 🤖 Generates concise AI summaries using OpenAI GPT-4
3. 🎵 Converts to professional podcast audio with UnrealSpeech
4. ☁️ Uploads MP3 to AWS S3 for reliable hosting
5. 📡 Updates RSS feed on GitHub for podcast platforms

**Live RSS Feed**: `https://raw.githubusercontent.com/sanzgiri/hackercast_ai/refs/heads/main/podcast.xml`

---

## 🏗️ Architecture

### 3-Step Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Generate Summaries                                 │
│  → generate_summaries_hn.py                                 │
│  → Fetches Hacker News top stories                          │
│  → Creates AI summaries with OpenAI GPT-4o-mini             │
│  → Output: hn_transcript_MMDDYYYY.txt                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Generate Audio                                     │
│  → generate_podcast_unreal.py                               │
│  → Converts text to speech with UnrealSpeech               │
│  → Processes in chunks and concatenates                     │
│  → Output: hn_transcript_MMDDYYYY.mp3                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Publish                                            │
│  → publish_podcast_s3.py                                    │
│  → Uploads MP3 to AWS S3 (correct MIME type)                │
│  → Updates RSS feed (lastBuildDate for Apple Podcasts)      │
│  → Publishes RSS to GitHub                                  │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Content Source** | Hacker News API | Top tech stories |
| **Summarization** | OpenAI GPT-4o-mini | AI summaries |
| **Text-to-Speech** | UnrealSpeech API | High-quality audio |
| **Audio Processing** | pydub + nltk | Chunking & concatenation |
| **MP3 Hosting** | AWS S3 | Reliable, correct MIME type |
| **RSS Hosting** | GitHub | Free, version-controlled |
| **Automation** | macOS launchd | Daily scheduling |
| **Environment** | uv + venv | Fast package management |

---

## 🚀 Quick Setup

### Prerequisites
- Python 3.10+
- macOS (for launchd automation)
- API Keys: OpenAI, UnrealSpeech, GitHub
- AWS Account (free tier is fine)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/sanzgiri/hackercast_ai.git
cd hackercast_ai

# 2. Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Create virtual environment
uv venv
source .venv/bin/activate

# 4. Install dependencies
uv pip install -r requirements.txt

# 5. Create directories
mkdir -p output logs

# 6. Configure environment variables
nano .env
# Add:
# OPENAI_API_KEY=your_openai_key
# UNREAL_SPEECH_API_KEY=your_unrealspeech_key
# GITHUB_API_KEY=your_github_token

# 7. Configure AWS
aws configure
# Enter: Access Key ID, Secret Access Key, us-east-1, json

# 8. Setup S3 bucket
./setup_s3.sh

# 9. Install automation (optional)
./setup_automation.sh
```

---

## 📝 Core Scripts

### generate_summaries_hn.py
Fetches and summarizes Hacker News stories.

```bash
python generate_summaries_hn.py daily 10
```

**Features:**
- ✅ Fetches top 10 Hacker News stories
- ✅ Generates concise summaries with OpenAI
- ✅ File existence check (skips if already generated)
- ✅ Rate limit handling with exponential backoff

**Output:** `output/hn_transcript_MMDDYYYY.txt`

---

### generate_podcast_unreal.py
Converts text summaries to podcast audio.

```bash
python generate_podcast_unreal.py
```

**Features:**
- ✅ Text-to-speech via UnrealSpeech API
- ✅ Intelligent text chunking (500 char max)
- ✅ Audio concatenation with pydub
- ✅ Automatic cleanup of temp files
- ✅ File existence check (skips if MP3 exists)

**Output:** `output/hn_transcript_MMDDYYYY.mp3`

---

### publish_podcast_s3.py
Publishes podcast to S3 and GitHub.

```bash
python publish_podcast_s3.py --date 10172025
```

**Features:**
- ✅ Uploads MP3 to AWS S3 with `audio/mpeg` MIME type
- ✅ Updates RSS feed with S3 URLs
- ✅ Sets `lastBuildDate` to trigger Apple Podcasts refresh
- ✅ Publishes RSS to GitHub
- ✅ Full Apple Podcasts compliance

**Outputs:**
- S3: `https://hackercast-ai-podcast.s3.us-east-1.amazonaws.com/episodes/*.mp3`
- RSS: `https://raw.githubusercontent.com/sanzgiri/hackercast_ai/refs/heads/main/podcast.xml`

---

## 🤖 Automation

### Install Daily Automation

```bash
./setup_automation.sh
```

This sets up a launchd job that runs daily at 9:00 AM.

### Manage Automation

```bash
# Check status
launchctl list | grep podcastgeneration

# View logs
tail -f logs/podcast_generation.log
tail -f logs/podcast_generation_error.log

# Stop automation
launchctl unload ~/Library/LaunchAgents/com.sanzgiri.podcastgeneration.plist

# Restart automation
launchctl load ~/Library/LaunchAgents/com.sanzgiri.podcastgeneration.plist
```

---

## 🎯 Key Features

### 💰 Smart Token Conservation
- **File existence checks** before API calls
- **Skips completed steps** automatically
- **Safe to run multiple times** - no wasted tokens
- Saves on OpenAI and UnrealSpeech costs

### � Apple Podcasts Compatible
- ✅ **Correct MIME type** (`audio/mpeg` from S3)
- ✅ **RSS compliance** with iTunes namespace
- ✅ **lastBuildDate updates** trigger feed refresh
- ✅ **1400x1400 cover art** meeting requirements
- ✅ **Direct MP3 URLs** with `.mp3` extension

### 📊 Cost Efficient
- **AWS S3**: ~$1-2/year for podcast hosting
- **GitHub**: Free RSS feed hosting
- **OpenAI**: ~$0.10/day for summaries
- **UnrealSpeech**: ~$0.03/day for TTS
- **Total**: ~$5-10/month for daily podcast

### 🔧 Production Ready
- ✅ Comprehensive error handling
- ✅ Detailed logging with timestamps
- ✅ Automatic temp file cleanup
- ✅ Environment isolation
- ✅ Graceful failure recovery

---

## 📁 Project Structure

```
hackercast_ai/
├── .venv/                          # Virtual environment (uv)
├── .env                            # API keys (not in git)
├── output/                         # Generated files
│   ├── hn_transcript_*.txt         # Daily transcripts
│   ├── hn_transcript_*.mp3         # Audio files
│   └── podcast.xml                 # RSS feed (local copy)
├── logs/                           # Automation logs
│   ├── podcast_generation.log      # Main log
│   └── podcast_generation_error.log # Error log
├── archive/                        # Old/unused code
├── requirements.txt                # Python dependencies
├── .env.template                   # Environment template
├── run_podcast_generation.sh       # Main pipeline script
├── setup_automation.sh             # Install launchd job
├── setup_s3.sh                     # Setup AWS S3 bucket
├── generate_summaries_hn.py        # Step 1: Summaries
├── generate_podcast_unreal.py      # Step 2: Audio
├── publish_podcast_s3.py           # Step 3: Publish
└── com.sanzgiri.podcastgeneration.plist  # launchd config
```

---

## 📱 Subscribe to Podcast

**RSS Feed URL:**
```
https://raw.githubusercontent.com/sanzgiri/hackercast_ai/refs/heads/main/podcast.xml
```

### Add to Podcast Apps:
- **Apple Podcasts**: Podcasts → Library → Add by URL
- **Spotify**: Settings → Show → Add podcast by URL
- **Google Podcasts**: Explore → Add by RSS feed
- **Any podcast app**: Use the RSS URL above

---

## 🛠️ Manual Usage

```bash
# Activate environment
source .venv/bin/activate

# Run complete pipeline
./run_podcast_generation.sh

# Or run steps individually:
python generate_summaries_hn.py daily 10
python generate_podcast_unreal.py
python publish_podcast_s3.py --date $(date +%m%d%Y)
```

---

## 🔧 Troubleshooting

### "Module not found" errors
```bash
source .venv/bin/activate
uv pip install -r requirements.txt
```

### AWS credentials not found
```bash
aws configure
# Enter your Access Key ID and Secret Access Key
```

### Apple Podcasts not refreshing
```bash
# Force refresh at https://podcastsconnect.apple.com/
# Or wait 1-4 hours for automatic refresh
```

### Check logs
```bash
tail -f logs/podcast_generation.log
tail -f logs/podcast_generation_error.log
```

---

## 📚 Documentation

- **`ENVIRONMENT_SETUP.md`** - Complete setup guide
- **`S3_QUICK_START.md`** - AWS S3 quick reference
- **`APPLE_PODCASTS_REFRESH.md`** - Podcast refresh guide
- **`HOSTING_OPTIONS.md`** - Hosting comparison

---

## 🎉 Features Highlights

✅ **Fully Automated** - Set it and forget it  
✅ **Cost Effective** - ~$5-10/month total  
✅ **Apple Podcasts Ready** - Proper MIME types & RSS  
✅ **Smart Caching** - Avoids regenerating content  
✅ **Production Logging** - Track everything  
✅ **Easy Maintenance** - Update, monitor, debug easily  

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Issues and pull requests welcome! This is a personal project but happy to help others set it up.

---

**Built with ❤️ using OpenAI, UnrealSpeech, AWS S3, and macOS automation**
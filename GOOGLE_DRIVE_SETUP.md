# Podcast Publishing Setup

## Prerequisites

1. Install the required packages:
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib requests
```

## Setup Steps

### 1. GitHub Repository Setup

1. Make sure your GitHub repository `https://github.com/sanzgiri/podcast-feed` exists
2. Ensure your `GITHUB_API_KEY` is set in your `.env` file
3. The RSS feed will be published to: `https://raw.githubusercontent.com/sanzgiri/podcast-feed/main/podcast.xml`

### 2. Google Drive API Setup (for MP3 hosting)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Drive API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

### 3. Create Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Choose "Desktop application"
4. Name it "HackerCast Podcast Publisher"
5. Download the JSON file
6. Rename it to `credentials.json`
7. Place it in your `/Users/sanzgiri/hackercast_ai/` folder

### 4. First Run Authorization

When you first run the script, it will:
1. Open a browser window
2. Ask you to sign in to Google
3. Request permission to access your Google Drive
4. Save the authorization token for future use

## Usage

### Publish today's episode:
```bash
python publish_podcast.py
```

### Publish specific date episode:
```bash
python publish_podcast.py 10142025
```

## What the script does:

1. ✅ Downloads current RSS from GitHub repository
2. ✅ Copies MP3 to local Google Drive folder
3. ✅ Uploads MP3 to Google Drive cloud storage
4. ✅ Makes MP3 publicly shareable
5. ✅ Updates RSS feed with new episode (removes duplicates)
6. ✅ Copies RSS to local Google Drive folder
7. ✅ Uploads updated RSS to GitHub repository
8. ✅ Provides permanent RSS URL for podcast platforms

## RSS Feed URL

**Permanent RSS URL:** `https://raw.githubusercontent.com/sanzgiri/podcast-feed/main/podcast.xml`

✅ This URL never changes - perfect for Spotify, Apple Podcasts, etc.

## File Structure Expected:

```
/Users/sanzgiri/hackercast_ai/
├── credentials.json          # Google API credentials (you create this)
├── token.json               # Auto-generated after first auth
├── publish_podcast.py       # The main script
├── output/
│   ├── hn_transcript_MMDDYYYY.mp3  # Daily podcast audio
│   ├── hn_td_MMDDYYYY.txt  # Episode metadata
│   └── podcast.xml         # RSS feed (synced with GitHub)
└── Google Drive/My Drive/hackercast_ai/  # Local Google Drive sync folder
```

## Advantages of GitHub RSS Hosting:

- 🔒 **Permanent URL** - Never changes
- 🚀 **Fast CDN** - GitHub's global content delivery
- 🔄 **Version Control** - Track all RSS changes
- 💰 **Free** - No hosting costs
- 📊 **Reliable** - 99.9% uptime

## Troubleshooting

- **"credentials.json not found"**: Download OAuth credentials from Google Cloud Console
- **"GitHub API error"**: Check your GitHub token has repository write permissions
- **"Repository not found"**: Ensure `https://github.com/sanzgiri/podcast-feed` exists and is accessible
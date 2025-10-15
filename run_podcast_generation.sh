#!/bin/bash

# HackerCast AI - Daily Podcast Generation Pipeline
# Runs: Summaries → Audio Generation → Publishing

set -e  # Exit on any error

# Configuration
DATE_STR=$(date +"%m%d%Y")
LOG_FILE="podcast_generation_${DATE_STR}.log"

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check if a step should be skipped
check_file_exists() {
    if [ -f "$1" ]; then
        log "✅ File exists: $1 ($(ls -lh "$1" | awk '{print $5}')"
        return 0
    else
        return 1
    fi
}

log "🚀 Starting daily podcast generation pipeline for $DATE_STR"

# Ensure output directory exists
mkdir -p output

# Step 1: Generate summaries
log "📝 Step 1: Generating Hacker News summaries..."
if check_file_exists "output/hn_transcript_${DATE_STR}.txt"; then
    log "🚫 Summaries already exist, skipping to save API tokens"
else
    log "🔄 Running: python generate_summaries_hn.py daily 10"
    if python generate_summaries_hn.py daily 10; then
        log "✅ Summaries generated successfully"
    else
        log "❌ Failed to generate summaries"
        exit 1
    fi
fi

# Step 2: Generate podcast audio
log "🎵 Step 2: Generating podcast audio..."
if check_file_exists "output/hn_transcript_${DATE_STR}.mp3"; then
    log "🚫 MP3 already exists, skipping to save API tokens"
else
    log "🔄 Running: python generate_podcast_unreal.py"
    if python generate_podcast_unreal.py; then
        log "✅ Podcast audio generated successfully"
    else
        log "❌ Failed to generate podcast audio"
        exit 1
    fi
fi

# Step 3: Publish podcast
log "📡 Step 3: Publishing podcast..."
log "🔄 Running: python publish_podcast.py --date $DATE_STR"
if python publish_podcast.py --date "$DATE_STR"; then
    log "✅ Podcast published successfully"
else
    log "❌ Failed to publish podcast"
    exit 1
fi

# Summary
log "🎉 Daily podcast generation completed successfully!"
log "📊 Generated files:"
for file in "output/hn_transcript_${DATE_STR}.txt" "output/hn_transcript_${DATE_STR}.mp3" "output/hn_td_${DATE_STR}.txt"; do
    if [ -f "$file" ]; then
        log "   - $(basename "$file"): $(ls -lh "$file" | awk '{print $5}')"
    fi
done

log "📱 Check your RSS feed: https://raw.githubusercontent.com/sanzgiri/podcast-feed/main/rss"
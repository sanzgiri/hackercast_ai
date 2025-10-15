#!/bin/bash

# HackerCast AI - Setup Script
# Installs daily automation using launchd

set -e

echo "🎙️ HackerCast AI - Daily Automation Setup"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "com.sanzgiri.podcastgeneration.plist" ]; then
    echo "❌ Error: com.sanzgiri.podcastgeneration.plist not found"
    echo "Please run this script from the hackercast_ai directory"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p output logs
echo "✅ Created output/ and logs/ directories"

# Install launchd job
echo "🤖 Installing daily automation..."
cp com.sanzgiri.podcastgeneration.plist ~/Library/LaunchAgents/
chmod 644 ~/Library/LaunchAgents/com.sanzgiri.podcastgeneration.plist
echo "✅ Copied plist to LaunchAgents"

# Load the job
echo "🔄 Loading launchd job..."
launchctl load ~/Library/LaunchAgents/com.sanzgiri.podcastgeneration.plist
echo "✅ Loaded automation job"

# Verify installation
echo "🔍 Verifying installation..."
if launchctl list | grep -q "com.sanzgiri.podcastgeneration"; then
    echo "✅ Automation job is loaded and ready"
else
    echo "⚠️  Warning: Job may not be loaded properly"
fi

echo ""
echo "🎉 Setup completed!"
echo ""
echo "📋 Daily Automation Details:"
echo "   • Runs every day at 9:00 AM"
echo "   • Logs: logs/podcast_generation.log"
echo "   • Errors: logs/podcast_generation_error.log"
echo ""
echo "🛠️  Management Commands:"
echo "   • View logs: tail -f logs/podcast_generation.log"
echo "   • Test manually: ./run_podcast_generation.sh"
echo "   • Stop automation: launchctl unload ~/Library/LaunchAgents/com.sanzgiri.podcastgeneration.plist"
echo "   • Check status: launchctl list | grep com.sanzgiri.podcastgeneration"
echo ""
echo "📡 RSS Feed URL: https://raw.githubusercontent.com/sanzgiri/podcast-feed/main/rss"
echo ""
echo "⚠️  Don't forget to:"
echo "   1. Add API keys to .env file"
echo "   2. Test the pipeline: ./run_podcast_generation.sh"
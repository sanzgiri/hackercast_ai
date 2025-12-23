#!/bin/bash

# HackerCast AI - Setup Script
# Installs daily automation using launchd (macOS)

set -e

echo "🎙️ HackerCast AI - Daily Automation Setup"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "com.sanzgiri.podcastgeneration.plist" ]; then
    echo "❌ Error: com.sanzgiri.podcastgeneration.plist not found"
    echo "Please run this script from the hackercast_ai directory"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "⚠️  Warning: uv not found. Install with:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "⚠️  Warning: .venv not found. Creating it now..."
    if command -v uv &> /dev/null; then
        uv venv
        source .venv/bin/activate
        echo "📦 Installing dependencies..."
        uv pip install -r requirements.txt
        echo "✅ Virtual environment created and dependencies installed"
    else
        echo "❌ Cannot create venv without uv. Please install uv first."
        exit 1
    fi
else
    echo "✅ Virtual environment (.venv) exists"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p output logs
echo "✅ Created output/ and logs/ directories"

# Make run script executable
chmod +x run_podcast_generation.sh
echo "✅ Made run_podcast_generation.sh executable"

# Unload existing job if it exists (ignore errors)
launchctl unload ~/Library/LaunchAgents/com.sanzgiri.podcastgeneration.plist 2>/dev/null || true

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
echo "   • Environment: uv + venv (.venv/)"
echo "   • Runs every day at 9:00 AM"
echo "   • Logs: logs/podcast_generation.log"
echo "   • Errors: logs/podcast_generation_error.log"
echo ""
echo "🛠️  Management Commands:"
echo "   • View logs: tail -f logs/podcast_generation.log"
echo "   • Test manually: source .venv/bin/activate && ./run_podcast_generation.sh"
echo "   • Stop automation: launchctl unload ~/Library/LaunchAgents/com.sanzgiri.podcastgeneration.plist"
echo "   • Restart automation: launchctl unload ~/Library/LaunchAgents/com.sanzgiri.podcastgeneration.plist && launchctl load ~/Library/LaunchAgents/com.sanzgiri.podcastgeneration.plist"
echo "   • Check status: launchctl list | grep com.sanzgiri.podcastgeneration"
echo ""
echo "📡 RSS Feed URL: https://raw.githubusercontent.com/sanzgiri/hackercast_ai/refs/heads/main/podcast.xml"
echo ""
echo "⚠️  Don't forget to:"
echo "   1. Add API keys to .env file (OPENAI_API_KEY, UNREAL_SPEECH_API_KEY, GITHUB_API_KEY)"
echo "   2. Configure AWS: aws configure"
echo "   3. Setup S3 bucket: ./setup_s3.sh"
echo "   4. Test the pipeline: source .venv/bin/activate && ./run_podcast_generation.sh"
echo ""
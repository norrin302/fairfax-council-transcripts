#!/bin/bash
# Fairfax City Council Transcription - Quick Start
# Run this script to transcribe a meeting video

set -e

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY environment variable not set"
    echo ""
    echo "Set it with:"
    echo "  export OPENAI_API_KEY='your-key-here'"
    echo ""
    echo "Or create a .env file in this directory with:"
    echo "  OPENAI_API_KEY=your-key-here"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install openai yt-dlp -q 2>/dev/null || pip3 install openai yt-dlp -q

# Run transcription
echo ""
echo "Starting transcription..."
python3 scripts/transcribe_demo.py

echo ""
echo "Done! Check the transcripts/ directory for output."

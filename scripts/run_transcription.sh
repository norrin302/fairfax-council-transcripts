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
echo "Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies into .venv..."
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -q

# Run transcription
echo ""
echo "Starting transcription..."
python scripts/transcribe_demo.py

echo ""
echo "Done! Check the transcripts/ directory for output."

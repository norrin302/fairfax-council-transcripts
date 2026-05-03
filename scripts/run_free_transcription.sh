#!/bin/bash
# Fairfax City Council Transcription - Free Version
# Uses local Whisper model (no API key required)

set -e

echo "=============================================="
echo "FAIRFAX CITY COUNCIL TRANSCRIPTION (FREE)"
echo "=============================================="
echo ""
echo "This uses local Whisper - no API key needed!"
echo "First run will download the model (~150MB)"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found"
    exit 1
fi

# Check if video exists
if [ ! -f "videos/fairfax_demo_5min.mp4" ]; then
    echo "Downloading 5-minute demo video..."
    mkdir -p videos
    yt-dlp -f hls-3701 --download-sections "*0:00-5:00" \
        -o "videos/fairfax_demo_5min.%(ext)s" \
        "https://fairfax.granicus.com/player/clip/4421?meta_id=128481"
fi

echo ""
echo "Starting transcription (this may take a few minutes)..."
echo ""

# Run transcription
python3 scripts/transcribe_free.py

echo ""
echo "Done!"

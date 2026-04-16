# Quick Start Guide

## Transcribe a Meeting

### Option 1: Use OpenAI Whisper API (Recommended)

```bash
# Set your API key
export OPENAI_API_KEY='sk-your-key-here'

# Run transcription
./scripts/run_transcription.sh
```

### Option 2: Manual Transcription

```bash
# Install dependencies
pip install openai yt-dlp

# Download a meeting video (or use the existing demo)
python3 scripts/transcribe.py "https://fairfax.granicus.com/player/clip/4421" --output .

# For a shorter demo
yt-dlp -f hls-3701 --download-sections "*0:00-5:00" -o "demo.mp4" "https://fairfax.granicus.com/player/clip/4421"
```

### Option 3: Use Local Whisper (No API)

```bash
# Install whisper
pip install openai-whisper

# Run transcription
python3 scripts/transcribe.py "<video_url>" --output . --no-api
```

## Deploy to GitHub Pages

```bash
# Initialize git (if not already)
cd fairfax-council-transcripts
git init
git add .
git commit -m "Initial commit"

# Create GitHub repo and push
gh repo create fairfax-council-transcripts --public --source=. --push

# Enable GitHub Pages
gh api repos/{owner}/fairfax-council-transcripts/pages -X PUT -f source='{"branch":"main","path":"/site"}'

# Your site will be live at:
# https://{username}.github.io/fairfax-council-transcripts
```

## File Structure

```
fairfax-council-transcripts/
├── site/                    # GitHub Pages site
│   ├── index.html          # Main page
│   ├── css/style.css      # Styling
│   └── transcripts/       # Generated transcripts
├── scripts/
│   ├── transcribe.py      # Main transcription script
│   └── transcribe_demo.py # Quick demo script
├── videos/                 # Downloaded video files
├── transcripts/            # Text transcripts
├── archive/                # JSON/WebVTT archives
└── README.md
```

## Customize

### Add Council Members

Edit `scripts/transcribe.py` and update the `COUNCIL_MEMBERS` dictionary:

```python
COUNCIL_MEMBERS = {
    "Stacy Hall": {"role": "City Council Member", "title": "Councilwoman"},
    # Add more members...
}
```

### Site Styling

Edit `site/css/style.css` to match your branding.

## Costs

- OpenAI Whisper API: ~$0.006 per minute of audio
- Typical 2-hour meeting: ~$0.72
- 5-minute demo: ~$0.03

## Troubleshooting

**Video won't download:**
- Check if the URL is correct
- Try a different format: `yt-dlp -F <url>`

**No API key error:**
- Make sure OPENAI_API_KEY is set
- Check the key is valid at platform.openai.com

**Transcript is empty:**
- Check if audio is present in the video
- Try a different video URL

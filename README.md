# Fairfax City Council Transcripts

AI-powered transcription of Fairfax City Council meetings for transparency and accessibility.

## Live Site

**https://norrin302.github.io/fairfax-council-transcripts/**

## About

This project provides searchable, timestamped transcripts of Fairfax City Council meetings. Transcripts are generated using OpenAI Whisper and include:

- 📋 Full-text search across published meetings
- 🎙️ Best-effort automated speaker labels (may contain errors)
- ⏱️ Clickable timestamps (video deep links + shareable transcript deep links)
- 📋 Copy citation feature (quote + timestamp + links)
- 🔗 Links to official city video archives

## Current Transcripts

| Date | Meeting | Link |
|------|---------|------|
| April 14, 2026 | City Council Regular Meeting | [View](https://norrin302.github.io/fairfax-council-transcripts/transcripts/apr-14-2026.html) |

## How Transcripts Are Generated

1. **Download** - Meeting video downloaded from Granicus (Fairfax's official archive)
2. **Extract Audio** - Convert to MP3 (Whisper has 25MB limit)
3. **Transcribe** - OpenAI Whisper API processes the audio
4. **Format** - Convert to HTML with timestamps, best-effort speaker labels, and section shortcuts
5. **Index** - Build a client-side search index for cross-meeting search
6. **Deploy** - Push to GitHub Pages

## Project Structure

```
fairfax-council-transcripts/
├── docs/                    # GitHub Pages site
│   ├── index.html          # Homepage with global search
│   ├── transcripts/        # Individual meeting transcripts
│   ├── css/                # Stylesheets
│   └── js/                 # Search & interaction scripts
├── scripts/                 # Transcription pipeline
│   └── transcribe.py       # Whisper API integration
├── videos/                  # Source audio files
├── templates/               # Data schemas
│   └── meeting.schema.json # Canonical meeting model
└── README.md
```

## Adding a New Meeting

0. (One-time) set up Python deps:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
1. Find the meeting on [Fairfax Granicus](https://fairfax.granicus.com/)
2. Run transcription (downloads + transcribes from Granicus):
   ```bash
   python3 scripts/transcribe.py "https://fairfax.granicus.com/player/clip/4519" --meeting-id <meeting_id> --output .
   ```
3. Publish the meeting to the static site:
    - Create `meetings/<meeting_id>.json` (meeting metadata + sections + official links)
    - Generate the transcript page + turns JS from Whisper JSON:
      ```bash
      python3 scripts/publish_meeting.py <meeting_id> --input transcripts/<meeting_id>_complete.json
      ```
    - Add a meeting card to `docs/index.html` (until the homepage list is auto-generated)
   
   (Automation is planned, but today this step is partially manual.)
4. Commit and push

## Architecture

- **Frontend**: Static HTML/CSS/JS on GitHub Pages
- **Search**: Client-side JavaScript with pre-built search index
- **Index build**: `scripts/build_search_index.py` reads `meetings/*.json` + transcript turn data
- **Transcription**: OpenAI Whisper API
- **Hosting**: GitHub Pages (free, reliable)
- **Video Links**: Direct to Granicus (city's official archive)

## Official Resources

- [Fairfax City Meetings Portal](https://www.fairfaxva.gov/Government/Public-Meetings/City-Meetings)
- [Granicus Video Archive](https://fairfax.granicus.com/)

## Disclaimer

Transcripts are AI-generated and may contain minor errors. For the official record, always refer to the [city's official video archive](https://fairfax.granicus.com/).

---

Built for transparency in local government. A project for Councilwoman Stacy Hall.

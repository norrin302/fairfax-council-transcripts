# Fairfax City Council Transcripts

AI-powered transcription of Fairfax City Council meetings for transparency and accessibility.

## Live Site

**https://norrin302.github.io/fairfax-council-transcripts/**

## About

This project provides searchable, timestamped transcripts of Fairfax City Council meetings. Transcripts are generated using OpenAI Whisper and include:

- 📋 Full-text search across all meetings
- 🎙️ Speaker identification
- ⏱️ Clickable timestamps with deep linking
- 📋 Copy citation feature
- 🔗 Links to official city video archives

## Current Transcripts

| Date | Meeting | Link |
|------|---------|------|
| April 14, 2026 | City Council Regular Meeting | [View](https://norrin302.github.io/fairfax-council-transcripts/transcripts/apr-14-2026.html) |

## How Transcripts Are Generated

1. **Download** - Meeting video downloaded from Granicus (Fairfax's official archive)
2. **Extract Audio** - Convert to MP3 (Whisper has 25MB limit)
3. **Transcribe** - OpenAI Whisper API processes the audio
4. **Format** - Convert to HTML with timestamps, speakers, and agenda navigation
5. **Index** - Add to search index for cross-meeting search
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

1. Find the meeting on [Fairfax Granicus](https://fairfax.granicus.com/)
2. Download the video or extract audio
3. Convert to MP3 under 25MB: `ffmpeg -i video.mp4 -vn -acodec mp3 audio.mp3`
4. Run transcription:
   ```bash
   python scripts/transcribe.py audio.mp3 > transcript.json
   ```
5. Create HTML page in `docs/transcripts/`
6. Update `docs/js/search-index.js` with new segments
7. Add meeting card to `docs/index.html`
8. Commit and push

## Architecture

- **Frontend**: Static HTML/CSS/JS on GitHub Pages
- **Search**: Client-side JavaScript with pre-built search index
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
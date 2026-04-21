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
- 🧭 Agenda index navigation (when available via Granicus)
- 🔗 Links to official city video archives

## Current Transcripts

| Date | Meeting | Link |
|------|---------|------|
| April 14, 2026 | City Council Regular Meeting | [View](https://norrin302.github.io/fairfax-council-transcripts/transcripts/apr-14-2026.html) |

## How Transcripts Are Generated

Phase 1 pipeline:

1. **Ingest** - Download meeting media from Granicus using a repeatable meeting-id based script
2. **Normalize** - Convert source media on Juggernaut to canonical mono 16 kHz WAV
3. **Transcribe** - Run local WhisperX-first transcription on Juggernaut
4. **Diarize** - Run local diarization and keep raw intermediates for audit/debug
5. **Structure** - Build `transcripts_structured/<meeting_id>.json` as the source of truth
6. **Publish** - Generate static HTML, transcript JS, and search index from structured data
7. **Deploy** - Push committed site artifacts to GitHub Pages

## Project Structure

```
fairfax-council-transcripts/
├── docs/                    # GitHub Pages site
│   ├── index.html          # Homepage with global search
│   ├── transcripts/        # Individual meeting transcripts
│   ├── css/                # Stylesheets
│   └── js/                 # Search & interaction scripts
├── scripts/                 # Phase 1 ingest, local pipeline, publish, and fallback helpers
│   ├── run_phase1_local_pipeline.py
│   ├── build_structured_transcript.py
│   └── transcribe.py       # Legacy/fallback Whisper API path
├── videos/                  # Source audio files
├── templates/               # Data schemas
│   └── meeting.schema.json # Canonical meeting model
└── README.md
```

## Adding a New Meeting

0. One-time setup:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
1. Add or verify `meetings/<meeting_id>.json`
2. Ingest from Granicus to Juggernaut local storage:
   ```bash
   python3 scripts/phase1_ingest.py "<granicus_clip_url>" --meeting-id <meeting_id> --work-root /mnt/disk1/fairfax-phase1/work --format audio
   ```
3. Run the Phase 1 local pipeline on Juggernaut:
   ```bash
   python3 scripts/run_phase1_local_pipeline.py <meeting_id> --work-root /mnt/disk1/fairfax-phase1/work --hf-token-file ~/secrets/hf_token.txt
   ```
4. Review unresolved speakers if needed via `approvals/<meeting_id>.json`
5. Re-run publish if approvals changed:
   ```bash
   python3 scripts/publish_structured_meeting.py <meeting_id> --structured transcripts_structured/<meeting_id>.json
   ```
6. Commit and push published/code artifacts only

## Architecture

- **Frontend**: Static HTML/CSS/JS on GitHub Pages
- **Search**: Client-side JavaScript with pre-built search index
- **Index build**: `scripts/build_search_index.py` reads `meetings/*.json` + published turn data
- **Phase 1 transcription**: Local WhisperX-first on Juggernaut
- **Structured source of truth**: `transcripts_structured/<meeting_id>.json`
- **Publish step**: `scripts/publish_structured_meeting.py` generates public site output from structured data
- **Fallback path**: older OpenAI Whisper flow is retained only as fallback/legacy tooling
- **Hosting**: GitHub Pages
- **Video Links**: Direct to Granicus (city's official archive)

## Official Resources

- [Fairfax City Meetings Portal](https://www.fairfaxva.gov/Government/Public-Meetings/City-Meetings)
- [Granicus Video Archive](https://fairfax.granicus.com/)

## Disclaimer

Transcripts are AI-generated and may contain minor errors. For the official record, always refer to the [city's official video archive](https://fairfax.granicus.com/).

---

Built for transparency in local government. A project for Councilwoman Stacy Hall.

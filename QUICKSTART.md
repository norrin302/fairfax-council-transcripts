# Quick Start Guide

This repo is a **static GitHub Pages site**. The published site lives under `docs/`.

- Local development: serve the `docs/` folder
- GitHub Pages: branch `main`, folder `/docs`

## 0) One-time setup (for transcription scripts)

The website itself needs no build step, but the transcription scripts require Python deps.

```bash
# From repo root
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If `python3 -m venv` fails, install venv support (Ubuntu/Debian):

```bash
sudo apt-get install python3-venv
```

## 1) Transcribe a Meeting

### Option A: Whisper API (recommended)

```bash
export OPENAI_API_KEY='sk-...'

# Example (Granicus clip URL)
python scripts/transcribe.py "https://fairfax.granicus.com/player/clip/4519" --meeting-id apr-14-2026 --output .
```

### Option B: Run the 5-minute demo (Whisper API)

```bash
export OPENAI_API_KEY='sk-...'
./scripts/run_transcription.sh
```

### Option C: Local Whisper (no API key)

This is optional and heavier (torch + whisper models). Use a dedicated environment.

## 2) Publish to GitHub Pages

This repo is already structured for GitHub Pages.

### Using the GitHub UI

1. Repo Settings → Pages
2. Source: `Deploy from a branch`
3. Branch: `main`
4. Folder: `/docs`

### Using the GitHub CLI

```bash
# Enable GitHub Pages from /docs
gh api repos/{owner}/fairfax-council-transcripts/pages \
  -X PUT \
  -f source='{"branch":"main","path":"/docs"}'
```

Your site will be live at:
`https://{username}.github.io/fairfax-council-transcripts/`

## 3) Local preview

```bash
cd docs
python3 -m http.server 8000
# open http://127.0.0.1:8000/
```

## 4) Rebuild the global search index

The homepage search uses a prebuilt client-side index at `docs/js/search-index.js`, generated from:

- `meetings/*.json` (meeting metadata)
- `docs/transcripts/<meeting_id>-data.js` (TRANSCRIPT_TURNS)

```bash
python3 scripts/build_search_index.py
```

## File structure (current)

```
fairfax-council-transcripts/
├── docs/                     # GitHub Pages publish root
│   ├── index.html
│   ├── js/
│   └── transcripts/
├── scripts/                  # Transcription + index build helpers
├── transcripts/              # Raw transcript JSON outputs (source data)
├── videos/                   # Downloaded media (optional)
├── templates/
├── README.md
├── QUICKSTART.md
└── requirements.txt
```

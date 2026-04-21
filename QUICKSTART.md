# Quick Start Guide

Phase 1 canonical path:
- local WhisperX-first transcription on Juggernaut
- structured transcript JSON is the source of truth
- public site output is generated from structured data
- older Whisper API scripts are fallback only

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

## 1) Phase 1 acceptance path, local pipeline on Juggernaut

Phase 1 uses a static GitHub Pages site, but the ingest, normalization, ASR, and diarization run locally on Juggernaut.

### Ingest from Granicus

```bash
python3 scripts/phase1_ingest.py \
  "https://fairfax.granicus.com/player/clip/4519?view_id=13&redirect=true" \
  --meeting-id apr-14-2026 \
  --work-root /mnt/disk1/fairfax-phase1/work \
  --format audio
```

### Run normalize + local WhisperX + local diarization + structured publish

```bash
python3 scripts/run_phase1_local_pipeline.py apr-14-2026 \
  --work-root /mnt/disk1/fairfax-phase1/work \
  --hf-token-file ~/secrets/hf_token.txt
```

### Rebuild site from structured data only

```bash
python3 scripts/publish_structured_meeting.py apr-14-2026 \
  --structured transcripts_structured/apr-14-2026.json
```

### Optional agenda import

```bash
python3 scripts/import_granicus_agenda_index.py apr-14-2026
```

### Manual review workflow

Generate the review queue:

```bash
python3 scripts/build_review_queue.py apr-14-2026 \
  --structured transcripts_structured/apr-14-2026.json \
  --out reviews/apr-14-2026-review-queue.json
```

Export and edit reviewer decisions:

```bash
python3 scripts/export_review_template.py apr-14-2026 \
  --queue reviews/apr-14-2026-review-queue.json \
  --out reviews/apr-14-2026-review-decisions.json
```

Apply decisions and rebuild:

```bash
python3 scripts/apply_review_decisions.py apr-14-2026 \
  --structured transcripts_structured/apr-14-2026.json \
  --decisions reviews/apr-14-2026-review-decisions.json

python3 scripts/publish_structured_meeting.py apr-14-2026 \
  --structured transcripts_structured/apr-14-2026.json

python3 scripts/validate_site.py
```

If approvals or review decisions are incomplete, unresolved speakers stay conservative on the public site.

### Legacy Whisper API path

The older OpenAI Whisper API flow still exists for earlier repo history, but the documented Phase 1 acceptance path is the local Juggernaut pipeline above.

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

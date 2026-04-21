# RUNBOOK

## Phase 1 pipeline overview

Phase 1 stays on the static GitHub Pages architecture.
Canonical Phase 1 transcript path is local WhisperX-first processing on Juggernaut.
Older Whisper API scripts remain fallback only and are not the primary documented workflow.

Source of truth flow:

1. `meetings/<meeting_id>.json` for meeting metadata
2. Juggernaut work root for large local artifacts
3. `transcripts_structured/<meeting_id>.json` for durable structured transcript data
4. `docs/transcripts/<meeting_id>.html` and `docs/transcripts/<meeting_id>-data.js` generated from structured data
5. `docs/js/search-index.js` generated from published turn data

Public speaker policy:
- publish approved names only
- unresolved or mixed identities render as `Unknown Speaker`
- do not hand-edit transcript HTML as the main workflow

## One-time setup

### Repo

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Juggernaut

Required host tools:
- `yt-dlp`
- `ffmpeg`
- `docker`
- NVIDIA runtime support for Docker

Required local Docker images:

```bash
cd pipeline

docker build -t fairfax-whisperx:latest -f docker/whisperx/Dockerfile .
docker build -t fairfax-diarize-pyannote:latest -f docker/diarize-pyannote/Dockerfile .
```

Required secret:
- Hugging Face token file for pyannote diarization, for example: `~/secrets/hf_token.txt`

Recommended local-only work root:
- `/mnt/disk1/fairfax-phase1/work`

## Ingest a meeting

```bash
python3 scripts/phase1_ingest.py \
  "https://fairfax.granicus.com/player/clip/4519?view_id=13&redirect=true" \
  --meeting-id apr-14-2026 \
  --work-root /mnt/disk1/fairfax-phase1/work \
  --format audio
```

Outputs on Juggernaut:
- `/mnt/disk1/fairfax-phase1/work/apr-14-2026/ingest.json`
- `/mnt/disk1/fairfax-phase1/work/apr-14-2026/media/<downloaded-file>`

Notes:
- default ingest preference is `--format audio` for Phase 1 because audio is the canonical working input
- use `--format video` only when source video is specifically needed
- idempotent unless `--force` is used
- large downloaded media stays off Git

## Normalize audio

```bash
python3 scripts/phase1_normalize_audio.py \
  --meeting-id apr-14-2026 \
  --work-root /mnt/disk1/fairfax-phase1/work
```

Output on Juggernaut:
- `/mnt/disk1/fairfax-phase1/work/apr-14-2026/audio/audio_16k_mono.wav`

Canonical Phase 1 working format:
- WAV
- mono
- 16 kHz

## Run the Phase 1 local pipeline

```bash
python3 scripts/run_phase1_local_pipeline.py apr-14-2026 \
  --work-root /mnt/disk1/fairfax-phase1/work \
  --hf-token-file ~/secrets/hf_token.txt
```

What this does:
- normalizes audio if needed
- runs local WhisperX-first ASR on Juggernaut
- runs local pyannote diarization on Juggernaut
- builds `transcripts_structured/apr-14-2026.json`
- publishes static site files from structured data
- rebuilds search index
- validates the site

Local-only artifacts kept on Juggernaut:
- `media/`
- `audio/`
- `asr/whisperx.json`
- `diarization/pyannote_segments.json`
- any other debug intermediates

## Review unresolved speaker labels

Default approval input:
- `approvals/<meeting_id>.json`

Canonical review artifacts:
- `reviews/<meeting_id>-review-queue.json`
- `reviews/<meeting_id>-review-decisions.json`

Generate the queue:

```bash
python3 scripts/build_review_queue.py <meeting_id> \
  --structured transcripts_structured/<meeting_id>.json \
  --out reviews/<meeting_id>-review-queue.json
```

Export a reviewer decisions template:

```bash
python3 scripts/export_review_template.py <meeting_id> \
  --queue reviews/<meeting_id>-review-queue.json \
  --out reviews/<meeting_id>-review-decisions.json
```

Apply reviewer decisions:

```bash
python3 scripts/apply_review_decisions.py <meeting_id> \
  --structured transcripts_structured/<meeting_id>.json \
  --decisions reviews/<meeting_id>-review-decisions.json
```

Then regenerate public output:

```bash
python3 scripts/publish_structured_meeting.py <meeting_id> \
  --structured transcripts_structured/<meeting_id>.json

python3 scripts/validate_site.py
```

Policy:
- only `status: approved` with a real `name` may publish a person name
- likely public commenters without verified identity may publish as `Public Comment Speaker`
- `rejected_*`, `mixed`, missing approvals, and unknown diarization stay conservative
- reviewer text changes must not invent wording

If approvals are not ready yet, the pipeline still succeeds, but unresolved speakers stay conservative on the public site.

## Regenerate the site from structured artifacts

```bash
python3 scripts/publish_structured_meeting.py apr-14-2026 \
  --structured transcripts_structured/apr-14-2026.json

python3 scripts/validate_site.py
```

Outputs committed to Git:
- `transcripts_structured/<meeting_id>.json`
- `docs/transcripts/<meeting_id>.html`
- `docs/transcripts/<meeting_id>-data.js`
- `docs/js/search-index.js`

## Publish output

```bash
git checkout -b feat/phase1-pipeline-apr14-acceptance
git add scripts/ pipeline/ templates/ transcripts_structured/ docs/ meetings/ approvals/ RUNBOOK.md WORKLOG.md QUICKSTART.md README.md
git commit -m "Implement Phase 1 local pipeline for structured transcript publishing"
git push -u origin feat/phase1-pipeline-apr14-acceptance
gh pr create --base main --head feat/phase1-pipeline-apr14-acceptance --title "Implement Phase 1 pipeline for apr-14-2026 acceptance" --body-file scripts/phase1_acceptance_apr14.md
```

Do not commit:
- raw media
- normalized audio
- WhisperX raw outputs stored on Juggernaut
- diarization raw outputs stored on Juggernaut
- secret token files

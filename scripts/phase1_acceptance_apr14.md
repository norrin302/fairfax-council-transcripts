# Phase 1 Acceptance Test: apr-14-2026

This file documents the Phase 1 acceptance-test run for the meeting `apr-14-2026`.

## Canonical goals

- ingest Granicus source
- normalize audio on Juggernaut
- run local transcription + diarization on Juggernaut
- build structured transcript JSON (source of truth)
- publish static site artifacts from the structured transcript

## Juggernaut work root

Recommended work root (not in Git):
- `/mnt/disk1/fairfax-phase1/work`

## Commands

### 1) Ingest

```bash
python3 scripts/phase1_ingest.py \
  "https://fairfax.granicus.com/player/clip/4519?view_id=13&redirect=true" \
  --meeting-id apr-14-2026 \
  --work-root /mnt/disk1/fairfax-phase1/work
```

### 2) Normalize audio

```bash
python3 scripts/phase1_normalize_audio.py \
  --meeting-id apr-14-2026 \
  --work-root /mnt/disk1/fairfax-phase1/work
```

### 3) Local transcription + diarization + structured publish

Run the orchestrated local pipeline on Juggernaut:

```bash
python3 scripts/run_phase1_local_pipeline.py apr-14-2026 \
  --work-root /mnt/disk1/fairfax-phase1/work \
  --hf-token-file ~/secrets/hf_token.txt
```

Outputs expected under Juggernaut work root:
- `/mnt/disk1/fairfax-phase1/work/apr-14-2026/asr/whisperx.json`
- `/mnt/disk1/fairfax-phase1/work/apr-14-2026/diarization/pyannote_segments.json`
- `/mnt/disk1/fairfax-phase1/work/apr-14-2026/audio/audio_16k_mono.wav`

Outputs expected in Git repo:
- `transcripts_structured/apr-14-2026.json`
- `docs/transcripts/apr-14-2026.html`
- `docs/transcripts/apr-14-2026-data.js`
- `docs/js/search-index.js`

### 4) Manual review input

Optional but recommended before public naming:
- `approvals/apr-14-2026.json`

Only approved or strongly supported identities publish as real names. Everything else remains `Unknown Speaker`.

### Name-conflict precedence rule

When speaker-name evidence conflicts, resolve labels in this order:
1. speaker self-identification
2. official roster or agenda evidence tied directly to that speaker block
3. internally consistent contiguous speech block
4. chair or mayor call-up line
5. captions or subtitles as advisory only

Operational rule:
- preserve a conflicting call-up line in transcript text where it was spoken
- do not let a weaker call-up override a stronger self-identification for the public speaker label
- store both `called_as_name` and `supported_public_name` when they differ
- use `display_name` for public output
- prefer `Unknown Speaker` over speculative identity merging when evidence is weak

### 5) Validation

```bash
python3 scripts/validate_site.py
```

## What is committed vs local-only

Committed:
- `meetings/apr-14-2026.json`
- `transcripts_structured/apr-14-2026.json`
- `docs/transcripts/apr-14-2026.html`
- `docs/transcripts/apr-14-2026-data.js`
- `docs/js/search-index.js`
- scripts under `scripts/`

Local-only (Juggernaut):
- raw downloaded media
- normalized audio
- diarization outputs
- whisperx outputs
- reference clips and embeddings

## Manual review required

Speaker identity approvals are an explicit input. If approvals are absent or incomplete, the structured transcript will label unresolved speakers as `Unknown Speaker`.

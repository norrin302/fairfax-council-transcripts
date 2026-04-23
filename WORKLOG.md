# WORKLOG

## 2026-04-21

### Phase 1 implementation, apr-14-2026 acceptance target

Implemented Phase 1 repository-side pipeline pieces for the acceptance meeting `apr-14-2026`:

- `scripts/phase1_ingest.py`
  - repeatable Granicus ingest
  - deterministic meeting-local download naming
  - idempotent marker file at `ingest.json`
- `scripts/phase1_normalize_audio.py`
  - canonical Phase 1 audio normalization to mono 16 kHz WAV
- `scripts/run_phase1_local_pipeline.py`
  - orchestrates normalize → local WhisperX → local diarization → structured transcript build → static publish
- `scripts/build_structured_transcript.py`
  - builds durable structured transcript JSON from ASR words + diarization
  - applies conservative public speaker policy
- `scripts/publish_structured_meeting.py`
  - regenerates transcript JS/HTML and search index from structured transcript source of truth
- `templates/structured-transcript.schema.json`
  - schema for committed transcript structure
- `approvals/apr-14-2026.json`
  - manual approval input for speaker names allowed on the public site

### Phase 1 artifact split

Committed to Git:
- code
- docs
- meeting metadata
- approvals config
- structured transcript JSON
- published site artifacts

Kept local on Juggernaut:
- raw downloaded media
- normalized audio
- WhisperX intermediates
- diarization intermediates
- debug and audit artifacts

### Acceptance workflow

Canonical acceptance commands are documented in:
- `RUNBOOK.md`
- `scripts/phase1_acceptance_apr14.md`

The end-to-end acceptance run must execute on Juggernaut because that is where normalization and local GPU pipeline artifacts live.

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

### Phase 1 quality tuning, apr-14-2026

Follow-up tuning focused on transcript quality and review ergonomics without changing architecture or loosening speaker policy.

Changes:
- increased turn-builder merge tolerance for same-speaker adjacent units
- added cleanup for repeated filler phrases and obvious caption noise
- reduced micro-turn fragmentation with a post-pass merge step
- added `scripts/build_review_queue.py` to generate explicit review worklists with local context

Observed improvement on `apr-14-2026`:
- total turns reduced from 673 to 591
- very short turns of 2 words or fewer reduced from 66 to 18
- generated review queue to focus manual review on unresolved or mixed items with context

### Manual review workflow, apr-14-2026

Implemented a repeatable human-in-the-loop review flow:
- `scripts/build_review_queue.py` creates canonical review queue artifacts
- `scripts/export_review_template.py` exports a reviewer decision template
- `scripts/apply_review_decisions.py` applies reviewer outcomes back onto the structured transcript
- `reviews/apr-14-2026-review-decisions.json` stores auditable reviewer actions in Git

Review outcomes currently supported:
- keep as `Unknown Speaker`
- mark as `Public Comment Speaker`
- approve a named official
- correct transcript text conservatively
- suppress obviously broken junk turns
- hold back questionable text for later review

Reviewed-enough standard for public publishing:
- approved names only for explicitly approved officials
- unresolved and mixed blocks remain conservative
- questionable text is either left conservative, corrected with human review, or suppressed
- regenerated site must pass `scripts/validate_site.py`

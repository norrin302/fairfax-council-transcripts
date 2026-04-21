# ARCHITECTURE

## Overview

The project should remain a static GitHub Pages site at the presentation layer while the processing pipeline becomes more structured, auditable, and review-driven.

The architecture splits into:
1. ingest
2. local processing on Juggernaut
3. human review / approval
4. static artifact generation
5. Git-based publication

## 1. Ingest from Granicus

### Inputs
- Fairfax Granicus clip URL
- meeting metadata and official links
- optional Granicus agenda index markers

### Current repo pieces
- `scripts/transcribe.py`
- `scripts/import_granicus_agenda_index.py`
- `scripts/import_viewpublisher_2026_city_council.py`
- `meetings/*.json`

### Desired role
- Establish the meeting ID and canonical metadata record
- Download or reference source media for local processing
- Preserve official URLs in meeting metadata for public linking

## 2. Local diarization on Juggernaut GPU

### Purpose
Run the heavier audio processing locally on Juggernaut rather than pushing everything through paid API calls.

### Current repo pieces
- `pipeline/src/prep_audio.py`
- `pipeline/src/transcribe_faster_whisper.py`
- `pipeline/src/diarize_pyannote.py`
- `pipeline/docker/*`

### Expected flow
1. Pull meeting media or extract audio
2. Normalize audio into a consistent working format
3. Run transcription locally where appropriate
4. Run diarization locally on GPU
5. Save intermediate artifacts as files, not hidden state

### Constraints
- container outputs must remain writable by the normal operator account
- diarization output must be reviewable and versionable as an artifact
- over-segmentation should be treated as a known failure mode

## 3. Transcription path

### Phase 1 expectation
Preserve the current static site and prioritize auditable output over a full rewrite.

### Likely near-term path
- use the current repo/site structure as the publish target
- use the best available local or API transcription path per meeting
- keep transcript timing aligned with the public video
- treat speaker naming as a separate review problem from raw text generation

### Decision principle
Text quality, timestamps, and speaker attribution should be separable concerns. A transcript should not inherit speculative speaker names just because the text exists.

## 4. Speaker registry and reference clips

### Purpose
Create durable, reusable voice references for recurring speakers.

### Current repo pieces
- `speaker_registry/speakers.json`
- `pipeline/src/extract_embedding.py`
- `pipeline/src/speaker_registry.py`
- `scripts/export_reference_clips.py`
- `scripts/build_reference_review_sheet.py`
- `scripts/preseed_reference_candidates.py`
- `scripts/extract_embeddings_from_manifest.py`
- `scripts/match_reference_embeddings.py`

### Required artifacts
- manual speaker approvals
- reference clips
- embedding files
- central reference voice registry

### Key rule
Only human-approved identities should enter the reusable voice registry.

## 5. Review workflow for low-confidence speaker assignments

### Principle
Low-confidence assignments must never flow straight to the public site.

### Review stages
1. Export long candidate clips per diarized speaker
2. Build review sheets with transcript excerpts and timestamps
3. Allow manual approval / rejection / mixed-audio marking
4. Build or update reference embeddings from approved samples
5. Match unresolved speakers against the registry conservatively
6. Publish only accepted identities

### Output states
- approved
- rejected / mixed
- unresolved / generic placeholder

### Public behavior
If confidence is low, the public site should show a generic or unknown label rather than a guessed real name.

## 6. Artifact generation for static site publishing

### Current repo pieces
- `scripts/publish_meeting.py`
- `scripts/build_verified_transcript_from_diarization.py`
- `docs/transcripts/*`
- `scripts/build_search_index.py`

### Publish artifacts
- `docs/transcripts/<meeting_id>.html`
- `docs/transcripts/<meeting_id>-data.js`
- `docs/js/search-index.js`
- meeting metadata in `meetings/<meeting_id>.json`

### Phase 1 direction
Keep the static Pages site, but improve how those artifacts are generated and reviewed.

## 7. Search/index strategy

### Current strategy
Client-side search with a prebuilt JSON-style JS index generated from meeting metadata and transcript turns.

### Phase 1 strategy
Keep this approach.

Reasons:
- cheap to host
- easy to audit
- works well with GitHub Pages
- avoids adding backend complexity too early

### Future strategy
Revisit only if static search becomes too slow, too large, or too limited for the project’s needs.

## 8. Deployment strategy

### Current strategy
- repo on GitHub
- `main` branch
- static Pages publish from `docs/`

### Phase 1 recommendation
Retain this strategy.

Reasons:
- simplest possible public hosting
- already working
- low cost
- easy rollback via Git
- transparent history of public artifacts

### Operational note
Heavy processing can continue to live on Juggernaut as long as the publish output remains deterministic and Git is treated as the public release record.

## Architecture decision summary

For Phase 1, keep the public architecture static and Git-driven.

Invest effort in:
- documentation
- artifact discipline
- reproducible local processing
- review gates for speaker identity
- reference voice registry growth

Do not replace the public site architecture unless the static approach becomes a demonstrated blocker.

# ARCHITECTURE

## Architectural stance

For Phase 1, the project keeps the **current static GitHub Pages site** as the public presentation layer.

Heavy processing happens on **Juggernaut**, while the Git repo remains the canonical home for:
- project docs
- meeting metadata
- reviewed publish artifacts
- compact approval / registry state

The project should not add a richer backend until the static model is a demonstrated blocker.

## Canonical Phase 1 pipeline

1. **Ingest** meeting metadata from Granicus into `meetings/<meeting_id>.json`
2. **Prepare audio** on Juggernaut
3. **Transcribe locally** with the WhisperX-first path
4. **Run local diarization** on Juggernaut
5. **Export review artifacts** for speaker validation
6. **Apply manual speaker approvals** and registry-backed decisions
7. **Generate static publish artifacts** in `docs/`
8. **Rebuild search index**
9. **Commit and push reviewed publish outputs**
10. **Publish via GitHub Pages**

This is the official near-term path.

---

## 1. Ingest from Granicus

### Source of truth
- Granicus clip URL
- official city meeting links
- official agenda/minutes/packet references
- optional Granicus agenda index markers

### Repo artifacts
- `meetings/*.json`
- `scripts/import_granicus_agenda_index.py`
- ingest/transcription helpers under `scripts/`

### Output
A canonical meeting metadata record that survives retries and supports publishing regardless of which transcript engine was used.

---

## 2. Local processing on Juggernaut GPU

### Why Juggernaut
- lower recurring costs than full API-first operation
- better support for local diarization and embedding workflows
- richer intermediate artifacts for review

### Current code areas
- `pipeline/src/prep_audio.py`
- `pipeline/src/transcribe_faster_whisper.py`
- `pipeline/src/diarize_pyannote.py`
- `pipeline/docker/*`

### Processing outputs
- normalized audio
- transcript JSON / aligned words
- diarization segments
- review clip candidates
- embedding files

These outputs are primarily operational and should remain on Juggernaut unless a compact reviewed subset is promoted into Git.

---

## 3. Transcription path

## Decision
Use the **WhisperX-first local flow** as the Phase 1 transcript engine, paired with local diarization and existing static-site publishing.

### Why this path
- better fit for word-level alignment and later speaker review
- better cost profile than using the older OpenAI Whisper path as the default
- integrates naturally with local diarization and reference-clip workflows
- does not require replacing the static site architecture

### Non-decision
The older OpenAI Whisper/static publish flow is not deleted, but it is not the official Phase 1 default.

---

## 4. Speaker registry and reference clips

### Goal
Maintain a reusable voice registry for recurring officials and other manually approved speakers.

### Current code areas
- `speaker_registry/speakers.json`
- `pipeline/src/extract_embedding.py`
- `pipeline/src/speaker_registry.py`
- `scripts/export_reference_clips.py`
- `scripts/build_reference_review_sheet.py`
- `scripts/preseed_reference_candidates.py`
- `scripts/extract_embeddings_from_manifest.py`
- `scripts/match_reference_embeddings.py`

### Required artifacts
- manual approval records
- reference clips
- embedding JSON files
- central reusable voice registry metadata

### Rule
No identity should enter the reusable voice registry without explicit human approval.

---

## 5. Review workflow for low-confidence speaker assignments

### Public label policy
- approved known speaker -> real name
- likely public commenter but unverified -> `Public Comment Speaker`
- unresolved / mixed / low-confidence -> `Unknown Speaker`

### Review stages
1. export diarized reference clips
2. generate review sheet with timestamps and transcript excerpts
3. mark each candidate as approved, rejected/mixed, or unresolved
4. update reference registry from approved samples
5. run conservative matching for future meetings or unresolved buckets
6. publish only approved names

### Why this matters
Transcript text quality and speaker identity quality are separate problems. The architecture must not assume that one being “mostly right” makes the other safe for publication.

---

## 6. Artifact generation for static site publishing

### Current code areas
- `scripts/publish_meeting.py`
- `scripts/build_verified_transcript_from_diarization.py`
- `scripts/build_search_index.py`
- `docs/transcripts/*`

### Publish artifacts
- `docs/transcripts/<meeting_id>.html`
- `docs/transcripts/<meeting_id>-data.js`
- `docs/js/search-index.js`

### Phase 1 rule
Keep the current static Pages artifact model. Improve generation quality and review gates, not the public hosting architecture.

---

## 7. Search/index strategy

### Current strategy
Client-side search driven by a generated JS index.

### Phase 1 decision
Keep the current prebuilt client-side search index.

### Why
- zero backend requirement
- easy to review in Git
- consistent with static Pages hosting
- good enough for current project size

### Future trigger for change
Only reconsider if corpus size, latency, or search quality clearly exceed what the static index can support.

---

## 8. Deployment strategy

### Current deployment
- GitHub repo as release record
- `main` branch
- GitHub Pages serving `docs/`

### Phase 1 decision
Do not replace this deployment model.

### Why
- simplest rollback story
- lowest hosting complexity
- public outputs are transparent and versioned
- aligns with the project’s auditability requirement

---

## 9. Acceptance-test meeting

### Decision
Use **April 14, 2026 (`apr-14-2026`)** as the first end-to-end acceptance-test meeting.

### Why
- already exercises the current workflow deeply
- includes proclamation, public comment, council discussion, and staff sections
- already surfaced the main failure modes that Phase 1 must solve

---

## Architecture summary

The architecture is deliberately conservative:
- **static site stays**
- **local processing improves**
- **speaker review becomes explicit**
- **Git stores the reviewed public truth**
- **Juggernaut stores the heavy operational working set**

# RUNBOOK

## Purpose

This runbook describes the **official Phase 1 path** for processing Fairfax City Council meetings.

The goal is a workflow that is:
- accurate
- reviewable
- resumable
- cheap enough to run repeatedly
- compatible with the existing static GitHub Pages site

## Phase 1 canonical path

The canonical Phase 1 path is:
1. ingest Granicus meeting metadata
2. prepare audio on Juggernaut
3. transcribe locally with WhisperX-first flow
4. run local diarization on Juggernaut
5. export review artifacts
6. apply manual speaker approvals and registry-backed matches
7. build static publish artifacts in the repo
8. rebuild search index
9. validate
10. commit and push

The older OpenAI Whisper/static publish path remains a fallback only.

---

## 1. How to ingest a new meeting

### Inputs needed
- Granicus clip URL
- canonical meeting ID
- official agenda/minutes/packet links
- meeting title/date/type

### Steps
1. Create or update `meetings/<meeting_id>.json`
2. Preserve:
   - `source_video_url`
   - official city links
   - sections / agenda markers where available
3. If useful, import official agenda markers:
   ```bash
   python3 scripts/import_granicus_agenda_index.py <meeting_id>
   ```

### Output
- durable meeting metadata in Git

---

## 2. How to register a speaker

### Goal
Create reusable, approved voice references without guessing.

### Steps
1. Export candidate clips:
   ```bash
   python3 scripts/export_reference_clips.py <audio> <diarization.json> --out-dir <dir>
   ```
2. Build a review sheet:
   ```bash
   python3 scripts/build_reference_review_sheet.py <manifest.json> <asr.json> --out-csv <csv> --out-json <json>
   ```
3. Review clips manually
4. Record approval / rejection / mixed-audio status
5. Extract embeddings from approved clips
6. Update the central reference voice registry

### Rule
Do not register speakers from heuristic text cues alone.

---

## 3. How to process a meeting end to end

### Canonical Phase 1 steps
1. Ingest meeting metadata into `meetings/<meeting_id>.json`
2. Acquire and normalize audio on Juggernaut
3. Run local WhisperX-first transcription
4. Run local diarization
5. Export speaker review clips and review sheets
6. Apply manual approvals and cautious registry matches
7. Generate transcript artifacts with the public speaker-label policy:
   - approved speaker -> real name
   - likely public commenter but unverified -> `Public Comment Speaker`
   - unresolved / mixed -> `Unknown Speaker`
8. Write:
   - `docs/transcripts/<meeting_id>.html`
   - `docs/transcripts/<meeting_id>-data.js`
9. Rebuild search:
   ```bash
   python3 scripts/build_search_index.py
   ```
10. Validate:
   ```bash
   python3 scripts/validate_site.py
   ```
11. Commit and push
12. Recheck GitHub Pages propagation

### Acceptance-test meeting
Use `apr-14-2026` as the first end-to-end validation meeting.

---

## 4. How to publish to the site

### Current deployment model
GitHub Pages publishes from `main:/docs`.

### Publish steps
1. Ensure meeting metadata is correct
2. Ensure transcript assets are regenerated
3. Rebuild search index
4. Run validation
5. Commit only intended changes
6. Push to GitHub
7. Recheck live page after propagation

### Important
Do not restructure the public site in Phase 1 unless there is a documented blocker.

---

## 5. How to recover from interrupted work

### Recovery checklist
1. Read:
   - `PROJECT_OUTLINE.md`
   - `ARCHITECTURE.md`
   - `RUNBOOK.md`
   - `ROADMAP.md`
   - `WORKLOG.md`
2. Identify the current meeting and its artifact set
3. Determine which artifacts exist on Juggernaut and which are already committed
4. Check Git state:
   ```bash
   git status
   git log --oneline -10
   ```
5. Resume from the earliest missing durable artifact, not from memory

### Rule
If a decision or result is not written down or saved as an artifact, it is not complete enough.

---

## 6. Artifact ownership summary

### Git
- planning docs
- meeting metadata
- final transcript HTML / data JS
- search index
- compact reviewed approval / registry metadata

### Juggernaut
- raw media
- normalized audio
- diarization outputs
- reference clips
- embeddings
- temp logs / caches / queue files

---

## 7. Operational guardrails

- prefer correct partial attribution over confident false attribution
- prefer review artifacts over hidden state
- prefer local heavy processing over recurring API spend when practical
- prefer a documented fallback over undocumented improvisation

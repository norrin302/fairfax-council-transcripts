# RUNBOOK

## Purpose

This runbook describes how to process Fairfax City Council meetings using the current repo and the emerging Juggernaut-based review workflow.

The goal is not maximum automation. The goal is resumable, auditable execution.

---

## 1. How to ingest a new meeting

### Inputs needed
- Granicus clip URL
- canonical meeting ID (for example `apr-14-2026`)
- meeting title, date, official URLs

### Steps
1. Add or update `meetings/<meeting_id>.json`
2. Preserve:
   - `source_video_url`
   - official agenda / minutes / packet URLs
   - agenda section markers if available
3. If useful, import agenda index markers:
   ```bash
   python3 scripts/import_granicus_agenda_index.py <meeting_id>
   ```

### Output
- durable meeting metadata file

---

## 2. How to register a speaker

### Goal
Add a reusable, human-approved voice identity for future matching.

### Steps
1. Export candidate reference clips from a processed meeting:
   ```bash
   python3 scripts/export_reference_clips.py <audio> <diarization.json> --out-dir <dir>
   ```
2. Build a review sheet:
   ```bash
   python3 scripts/build_reference_review_sheet.py <manifest.json> <asr.json> --out-csv <csv> --out-json <json>
   ```
3. Review clips manually and record approvals / rejections
4. Extract embeddings from approved clips
5. Update the central reference voice registry
6. Keep the approval record as an artifact

### Rule
Never register a speaker identity from weak inference alone.

---

## 3. How to process a meeting end to end

### Phase 1 canonical flow
1. Ingest metadata and official links
2. Acquire / normalize source audio
3. Generate transcript text with timing
4. Run diarization locally on Juggernaut
5. Export review clips for relevant speaker buckets
6. Record manual approvals for speaker identities where confidence is high
7. Build transcript turns using:
   - approved real names where available
   - generic placeholders where identity is unresolved
8. Generate publish artifacts under `docs/`
9. Rebuild `docs/js/search-index.js`
10. Validate site structure
11. Commit and push to Git
12. Wait for GitHub Pages propagation

### Notes
- speaker attribution and transcript text should be treated as related but separate outputs
- low-confidence names should not be published

---

## 4. How to publish to the site

### Current publishing model
GitHub Pages publishes the static site from `main:/docs`.

### Steps
1. Ensure the transcript assets are updated:
   - `docs/transcripts/<meeting_id>.html`
   - `docs/transcripts/<meeting_id>-data.js`
2. Rebuild the search index:
   ```bash
   python3 scripts/build_search_index.py
   ```
3. Validate:
   ```bash
   python3 scripts/validate_site.py
   ```
4. Commit only the intended changes
5. Push to GitHub
6. Recheck the live Pages URL after propagation

### Important
Do not change the public site structure casually. Prefer targeted updates over layout churn.

---

## 5. How to recover from interrupted work

### Recovery checklist
1. Read the repo root planning docs:
   - `PROJECT_OUTLINE.md`
   - `ARCHITECTURE.md`
   - `RUNBOOK.md`
   - `ROADMAP.md`
   - `WORKLOG.md`
2. Identify the current meeting and locate its artifacts:
   - meeting metadata
   - raw transcript / ASR outputs
   - diarization outputs
   - review sheets
   - manual approvals
   - embeddings / registry files
3. Check Git state:
   ```bash
   git status
   git log --oneline -10
   ```
4. Check whether the last intended public push actually propagated to GitHub Pages
5. Resume from the earliest missing durable artifact, not from memory

### Recovery principle
If a step was not written down or saved as an artifact, it is not complete enough.

---

## 6. Operational guardrails

- prefer documented files over ad hoc chat memory
- prefer reversible Git changes over hidden state
- prefer generic labels over guessed names
- prefer a correct partial transcript over a fully labeled incorrect one
- keep the public site simple unless complexity is clearly justified

# PROJECT_OUTLINE

## Project purpose

Build and maintain a low-cost, auditable transcript publishing workflow for Fairfax City Council meetings.

The project should produce searchable, speaker-attributed meeting transcripts that are useful to the public while remaining explicit about uncertainty and preserving the official Granicus video archive as the source of record.

## Current repo/site state

- Public site is a static GitHub Pages site published from `docs/`.
- Repo already contains meeting metadata in `meetings/*.json`, transcript assets in `docs/transcripts/`, and a client-side search index in `docs/js/search-index.js`.
- Current scripts support several paths:
  - Granicus ingest and transcription helpers in `scripts/`
  - Static publishing via `scripts/publish_meeting.py`
  - Search index generation via `scripts/build_search_index.py`
  - Local diarization / embedding / merge experiments in `pipeline/src/`
  - New review-oriented utilities for reference clips, embedding extraction, and matching in `scripts/`
- The site structure itself is already viable and should be preserved for near-term work.
- Recent testing showed that naive speaker attribution is not accurate enough for public publishing without a stronger review workflow.

## Requirements

1. Preserve a simple static public site for Phase 1 unless there is a compelling reason to change it.
2. Improve speaker attribution accuracy without introducing opaque or hard-to-audit automation.
3. Keep infrastructure and inference costs low.
4. Support work pausing and resuming cleanly.
5. Store durable artifacts for review:
   - meeting metadata
   - transcript assets
   - speaker review sheets
   - reference clips
   - reference voice registry
   - approval records
6. Make it possible to process new meetings repeatedly with predictable outputs.

## Constraints

- Accuracy is more important than speed.
- The public site should remain simple.
- GitHub Pages should remain the default deployment target in the near term.
- Granicus remains the source video system.
- Some work currently happens on Juggernaut GPU infrastructure outside the Git repo.
- Speaker identification must prefer false negatives over false positives.
- Public labels must come from strong evidence, not heuristic name guessing.

## Target end state

A reproducible, documented pipeline that:
- ingests Fairfax City Council meetings from Granicus
- prepares local audio on Juggernaut
- generates transcripts with strong timing
- performs diarization locally
- supports human-reviewed speaker identification using reference clips and voice embeddings
- produces static publish artifacts for GitHub Pages
- records approvals and decisions in durable, reviewable files
- can be resumed by a new operator without relying on hidden session context

## Phased plan

### Phase 0
Document the current system, artifacts, assumptions, and recovery procedures.

### Phase 1
Stabilize the static pipeline, preserve the existing Pages architecture, and make outputs reproducible and reviewable.

### Phase 2
Add a high-accuracy speaker identification workflow driven by human-approved reference clips, conservative embedding matching, and low-confidence review gates.

### Phase 3
Improve review tooling, search/index quality, and publishing ergonomics without abandoning the static site.

### Phase 4
Optionally add richer backend features such as semantic search or more advanced review surfaces if the static approach becomes the limiting factor.

## Risks

- Incorrect speaker attribution being published as fact
- Over-fragmented diarization clusters leading to mislabeled turns
- Transcription errors cascading into bad speaker review decisions
- Drift between repo state and off-repo working artifacts on Juggernaut
- Root-owned container artifacts blocking later updates
- Hidden operator knowledge becoming required to resume work
- Costs rising if cloud inference becomes the default path instead of the fallback

## Open questions

1. What should be considered the canonical transcription path for Phase 1: existing static publish flow, WhisperX-first flow, or a hybrid?
2. Which model stack should be the default for local transcription on Juggernaut?
3. How should council/staff/public commenters be represented in the reference voice registry?
4. What confidence thresholds are acceptable for automatic assignment versus mandatory review?
5. Should unresolved speakers appear publicly as `Unknown Speaker`, generic `Speaker XX`, or context-aware labels like `Public Comment Speaker`?
6. Which artifacts should be committed to Git versus kept as operational data on Juggernaut?

## Immediate next tasks

1. Finish and review the repo-level documentation set.
2. Decide the Phase 1 canonical processing path and freeze it in writing.
3. Decide which operational artifacts live in Git and which stay on Juggernaut.
4. Build a documented, repeatable command path for:
   - ingest
   - transcript generation
   - diarization
   - review
   - publish
5. Add a first-class speaker registry / approval workflow that future meetings can reuse.
6. Rebuild Apr 14 internally using the documented reviewed workflow before making further architectural changes.

# PROJECT_OUTLINE

## Project purpose

Build and maintain an accurate, low-cost, auditable transcript pipeline for Fairfax City Council meetings.

The public output should remain a simple static site that gives residents searchable, timestamped meeting transcripts while clearly separating verified speaker identity from unresolved or low-confidence attribution.

## Current repo/site state

- The public site is a static GitHub Pages site published from `docs/`.
- The repo already has durable meeting metadata in `meetings/*.json` and public transcript/search artifacts under `docs/`.
- The repo also now contains newer workflow utilities for:
  - local diarization on Juggernaut
  - reference clip export
  - review sheet generation
  - embedding extraction and matching
  - verified transcript rebuilds
- The main gap is not site hosting. The main gap is a sufficiently accurate, reviewable speaker-attribution workflow.
- The existing static site should be treated as the Phase 1 publish target, not replaced casually.

## Requirements

1. Preserve the current static GitHub Pages approach for Phase 1 unless there is a strong documented reason to change it.
2. Favor accuracy over automation.
3. Favor auditable artifacts over hidden state.
4. Keep costs down by preferring local processing where practical.
5. Ensure work can pause and resume without relying on chat memory.
6. Prevent false speaker identification on the public site.
7. Make one real meeting the acceptance-test path for the workflow.

## Constraints

- Granicus remains the source video/archive system.
- Juggernaut is the local GPU processing host.
- The public site must stay simple in Phase 1.
- Large binary artifacts should not bloat the Git repo.
- Speaker identity must be review-driven, not heuristically guessed into publication.

## Target end state

A documented pipeline that:
- ingests a Fairfax meeting from Granicus
- processes audio on Juggernaut
- generates transcript text with timing
- performs local diarization
- supports human-reviewed speaker identification using reference clips and registry data
- publishes static GitHub Pages artifacts from the repo
- keeps enough written context and durable files that a new operator can resume safely

## Decision log

### Decision 1: Canonical Phase 1 transcription pipeline

**Decision:** Use a **hybrid local pipeline** as the official near-term path:
1. ingest Granicus meeting metadata
2. normalize audio on Juggernaut
3. generate transcript text locally with the WhisperX-first path
4. run local diarization on Juggernaut
5. perform human review / approval for speaker identities
6. generate static transcript artifacts in the existing repo/site structure
7. publish via GitHub Pages

**Reasoning:**
- keeps recurring processing costs down
- produces richer local artifacts for review
- fits the newer speaker-review workflow better than the older API-only path
- preserves the current static site instead of forcing a backend rewrite

**Fallback:** the older OpenAI Whisper/static publish path remains a fallback, not the Phase 1 default.

### Decision 2: Public speaker-label policy

**Decision:** Public speaker labels follow this rule:
- **approved known speaker** -> real name
- **likely public commenter but unverified** -> `Public Comment Speaker`
- **otherwise unresolved / mixed / low-confidence** -> `Unknown Speaker`

**Reasoning:**
- avoids false certainty
- keeps public output readable
- preserves trust by preferring false negatives over false positives

### Decision 3: GitHub vs Juggernaut artifact ownership

**Decision:**
- **GitHub repo** stores canonical small text artifacts, documentation, approvals, and public publish outputs
- **Juggernaut** stores large media, heavy intermediate processing outputs, embeddings, and temporary working files

**Reasoning:**
- Git stays auditable and review-friendly
- Juggernaut handles large and compute-heavy artifacts without bloating the repo

### Decision 4: Acceptance-test meeting

**Decision:** Use **April 14, 2026** (`apr-14-2026`) as the Phase 0-2 acceptance-test meeting.

**Reasoning:**
- it already has the deepest investigation and review context
- it exercises both public comment and council/staff sections
- it is the best current testbed for transcript accuracy, diarization, review, and publishing

## Git vs Juggernaut artifact matrix

| Artifact | Canonical location | Commit to Git? | Notes |
|---|---|---:|---|
| Repo planning docs | GitHub repo root | Yes | Durable operator context |
| Meeting metadata (`meetings/*.json`) | GitHub repo | Yes | Canonical meeting config |
| Generated HTML (`docs/transcripts/*.html`) | GitHub repo | Yes | Public publish artifact |
| Transcript turns JS (`docs/transcripts/*-data.js`) | GitHub repo | Yes | Public publish artifact |
| Search index (`docs/js/search-index.js`) | GitHub repo | Yes | Generated but committed publish artifact |
| Manual approval summaries / small review decisions | GitHub repo or mirrored canonical text artifact | Yes | Must remain auditable |
| Raw downloaded audio/video | Juggernaut | No | Large source media |
| Normalized audio | Juggernaut | No | Large processing input |
| Diarization outputs | Juggernaut | No (Phase 1) | Keep local unless a compact canonical form is later needed in Git |
| Reference speaker clips | Juggernaut | No | Large binary review artifacts |
| Voice embeddings | Juggernaut | No | Operational and potentially numerous |
| Central reference voice registry metadata | GitHub repo + Juggernaut working copy | Yes for compact metadata, no for raw clip binaries | Keep the registry durable without committing large media |
| Review sheets / review queue | GitHub repo for compact canonical records, Juggernaut for working copies | Yes for final reviewed state | Working CSV/JSON may begin local but should end in durable reviewed form |
| Logs / caches / temp files | Juggernaut | No | Local operational state only |

## Phased plan

### Phase 0
Document the current system, decisions, and recovery path.

### Phase 1
Stabilize the hybrid local processing + static publish workflow and make it reproducible.

### Phase 2
Add accurate speaker identification through reviewed reference clips and conservative registry matching.

### Phase 3
Improve review/search/publishing UX while keeping the public site simple.

### Phase 4
Only if justified, add richer backend or semantic search capabilities.

## Risks

- publishing incorrect speaker names
- over-fragmented diarization boundaries causing turn errors
- transcript errors propagating into bad review decisions
- drift between repo state and Juggernaut working state
- hidden operator knowledge becoming required to resume work
- cost growth if local processing is not the default path

## Open questions

1. What compact reviewed artifacts should be mirrored into Git as the canonical record of speaker approvals?
2. What acceptance thresholds should move a registry match from `review` to `approved` across meetings?
3. How should recurring non-official speakers be treated when their identity is manually confirmed only once?
4. When should `Public Comment Speaker` be preferred over `Unknown Speaker` in the public output?

## Immediate next tasks

1. Freeze the Phase 1 command path in code and runbook form.
2. Mirror the compact approval / registry metadata into the repo in a durable format.
3. Rebuild the April 14, 2026 meeting strictly through the documented Phase 1 path.
4. Validate that the public output uses the decided speaker-label policy.
5. Use Apr 14 as the first end-to-end acceptance test before scaling to more meetings.

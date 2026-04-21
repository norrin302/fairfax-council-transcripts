# WORKLOG

## 2026-04-21

### Initial project documentation pass

What I found:
- The repo already has a workable static GitHub Pages structure centered on `docs/`, `meetings/`, and publish/search scripts.
- There are now two overlapping realities that need to be reconciled in writing:
  1. the original static publish flow
  2. newer Juggernaut-based local processing for diarization, reference clips, embeddings, and reviewed speaker attribution
- Speaker attribution accuracy is the primary risk area. The biggest recent lesson is that naive speaker naming can look plausible while still being wrong.
- The static site itself is not the current blocker. The reliability of the processing and review workflow is the blocker.

What I planned next:
- freeze the current architecture and runbook in repo-level docs
- define the Phase 1 canonical path without rebuilding the public site architecture
- keep speaker identity review explicit and artifact-driven
- push the documentation set on a dedicated branch for review before additional architectural churn

---

## 2026-04-21

### Planning docs tightened for review branch

What changed:
- Added hard decisions to `PROJECT_OUTLINE.md`, including the canonical Phase 1 pipeline, public speaker-label policy, Git vs Juggernaut artifact ownership, and the acceptance-test meeting.
- Tightened `ARCHITECTURE.md` so the Phase 1 transcription path is no longer left open-ended.
- Updated `RUNBOOK.md` to make the canonical processing path explicit.
- Updated `ROADMAP.md` with concrete exit criteria tied to April 14, 2026.

Files touched:
- `PROJECT_OUTLINE.md`
- `ARCHITECTURE.md`
- `RUNBOOK.md`
- `ROADMAP.md`
- `WORKLOG.md`

Current branch:
- `feat/project-outline-and-architecture`

Next blocking decision:
- How much compact reviewed speaker-approval / registry metadata should be mirrored into Git as the canonical audit record versus kept only as Juggernaut operational state.

Next implementation step:
- Freeze the Phase 1 command path into one documented entrypoint and run April 14, 2026 through it as the acceptance-test meeting.

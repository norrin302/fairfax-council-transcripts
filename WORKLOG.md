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

What I plan next:
- freeze the current architecture and runbook in repo-level docs
- define the Phase 1 canonical path without rebuilding the public site architecture
- keep speaker identity review explicit and artifact-driven
- push the documentation set on a dedicated branch for review before additional architectural churn

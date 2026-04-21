# ROADMAP

## Phase 0: document current system

### Goal
Capture the current repo, static site, Juggernaut processing reality, and operating assumptions in durable docs.

### Exit criteria
Using **April 14, 2026 (`apr-14-2026`)** as the acceptance-test meeting context:
- repo root planning docs exist and are reviewed
- the canonical Phase 1 path is explicitly chosen in writing
- public speaker-label policy is explicitly chosen in writing
- Git vs Juggernaut artifact ownership is explicitly documented
- a reviewer can understand where to resume work without chat history

---

## Phase 1: stabilize static pipeline

### Goal
Preserve the existing static GitHub Pages architecture while making the processing path deterministic and reviewable.

### Scope
- canonical local transcription + diarization path
- reviewed speaker policy
- reproducible publish artifacts
- stable search index generation
- explicit publish / rollback path

### Exit criteria
Using **April 14, 2026** as the acceptance test:
- the meeting can be processed end to end through the documented canonical path
- transcript HTML, turns JS, and search index are generated reproducibly
- no speculative speaker names are published
- unresolved identities follow the documented public label policy
- the public site remains static GitHub Pages based

---

## Phase 2: add accurate speaker identification workflow

### Goal
Add a high-accuracy, human-reviewed speaker identification workflow that can be reused across meetings.

### Scope
- reference clip export
- review sheet generation
- manual approvals
- reusable voice registry
- conservative embedding matching

### Exit criteria
Using **April 14, 2026** as the first validation meeting and at least one later meeting as a reuse check:
- recurring known officials can be matched from the registry with documented thresholds
- low-confidence matches stay out of the public site
- approved registry state is stored durably
- unresolved speakers are reduced without introducing false identities

---

## Phase 3: improve review/search/publishing UX

### Goal
Improve operator workflow and public usability without replacing the static architecture prematurely.

### Scope
- better review summaries
- safer batch publish flow
- clearer preview workflow before public push
- improved client-side search quality and ergonomics

### Exit criteria
Using the acceptance-test meeting plus at least one new meeting:
- review workload is materially lower than the current manual process
- publishing requires fewer ad hoc corrections
- search remains stable and understandable for end users

---

## Phase 4: optional semantic search / richer backend

### Goal
Only if clearly justified, add richer capabilities that the static model cannot support well enough.

### Candidate directions
- semantic transcript search
- richer review UI
- backend service for registry or queue management
- cross-meeting speaker analytics

### Exit criteria
- a documented limitation of the static model exists
- the added complexity is justified by clear accuracy or workflow gains
- operating costs remain acceptable

---

## Roadmap summary

The project should mature in this order:
1. document
2. stabilize
3. identify accurately
4. improve UX
5. only then consider richer backend features

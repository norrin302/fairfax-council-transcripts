# ROADMAP

## Phase 0: document current system

Goal:
- capture the repo structure, current scripts, operational assumptions, and off-repo processing realities so work can pause and resume safely

Deliverables:
- `PROJECT_OUTLINE.md`
- `ARCHITECTURE.md`
- `RUNBOOK.md`
- `ROADMAP.md`
- `WORKLOG.md`

Success criteria:
- a new operator can understand the project without relying on chat history

---

## Phase 1: stabilize static pipeline

Goal:
- preserve the current static GitHub Pages architecture while making processing reproducible and reviewable

Focus:
- canonical meeting metadata flow
- deterministic transcript artifact generation
- explicit review gates for speaker identity
- documented publish / rollback path
- avoid structural changes to the public site unless necessary

Success criteria:
- new meetings can be processed with a repeatable documented command path
- public output avoids speculative names
- Git remains the public release record

---

## Phase 2: add accurate speaker identification workflow

Goal:
- support high-accuracy speaker attribution using approved reference clips and conservative voice matching

Focus:
- reference clip export
- review sheet generation
- manual approvals
- reusable voice registry
- conservative matching thresholds
- unresolved / mixed speaker handling

Success criteria:
- recurring council and staff voices can be matched with strong evidence
- low-confidence assignments stay out of the public site

---

## Phase 3: improve review/search/publishing UX

Goal:
- make the review and publishing experience smoother without abandoning the static model too early

Focus:
- clearer reviewer artifacts
- improved search/index quality
- safer batch publish flows
- better interrupted-work recovery paths
- possible preview workflows before public push

Success criteria:
- lower operator friction
- faster review cycles
- fewer accidental regressions

---

## Phase 4: optional semantic search / richer backend

Goal:
- only if justified, add richer capabilities that the static model cannot support well enough

Possible directions:
- semantic search over transcript corpus
- richer transcript review interfaces
- service-backed registry / workflow storage
- better cross-meeting speaker analytics

Guardrail:
- do not leave the static site model behind without a clear architectural reason and cost justification

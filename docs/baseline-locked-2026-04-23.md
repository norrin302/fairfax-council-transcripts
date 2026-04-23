# Baseline Locked — Production Pipeline State as of 2026-04-23

**Date:** 2026-04-23  
**Status:** FROZEN — this is the current production baseline  
**Author:** Neo

---

## Production Stack (Locked)

| Stage | Component | Version |
|-------|-----------|---------|
| ASR | faster-whisper medium | GPU, float16 |
| Diarization | pyannote.audio | 3.1 |
| Merge | microblock cleanup | dominance threshold 0.60 |
| Speaker mapping | registry v2.1 | speakers.json |
| Review workflow | review-mode UI + apply pipeline | v2.2 |
| Publish | publish_structured_meeting.py | static HTML/JS |

**What this stack does well:**
- Word-level timestamps from faster-whisper enable precise merge
- 1721 pyannote segments merged to ~572 turns
- Named officials (Mayor, councilmembers) correctly mapped via registry
- Public commenter blocks are flagged for conservative handling

**What this stack doesn't solve:**
- ~20 wrong attributions on 49-turn gold set (ex_003 dominant)
- ~12 unknown-when-named in gold set evaluation
- ~1/236 review burden (on gold set segments; full meeting review burden is larger)

---

## Rejected Experiments

Both clustering experiments were benchmarked and rejected.

### Rejected: Centroid-Level Embedding Clustering

**Date tested:** 2026-04-22  
**File:** `docs/embedding-clustering-benchmark-2026-04-22.md`

**What it does:** Average per-segment embeddings per pyannote speaker ID → 34 centroids → agglomerative cosine similarity clustering at threshold 0.75.

**Result:** ZERO improvement
- Wrong attributions: 38 → 38 (baseline on full meeting evaluation)
- Match rate: 38.7% → 38.7%
- Merges performed: 0 at threshold 0.75

**Why it failed:**
- Centroid averaging mixes acoustic profiles when pyannote reassigns the same person to different IDs
- SPEAKER_06 (Tom Peterson) vs SPEAKER_07 (JC Martinez): similarity = 0.7737 — highest cross-person similarity. No safe threshold: 0.75 merges nothing, 0.60 would wrongly merge different people
- The 38 wrong attributions are NOT clustering failures — they are diarization accuracy failures that centroid clustering can't fix

**Verdict:** Wrong architecture for this problem. Not adopted.

### Rejected: Per-Segment Embedding Clustering

**Date tested:** 2026-04-23  
**File:** `docs/per-segment-clustering/architecture.md`

**What it does:** Extract 256-dim wespeaker-voxceleb embedding per diarization segment (1721 individually) → sparse similarity graph (temporal non-overlap + cosine sim ≥ threshold) → BFS connected components → vote-dominant pyannote ID → registry mapping.

**Result:** Real but not material
- Wrong attributions: 20 → 18 (gold set, 49 turns)
- Match rate: 31.9% → 36.2%
- Threshold sweep (0.70/0.75/0.80): identical results — robust, not fragile
- ex_004: 13 wrong → 11 wrong (council appointments section)
- ex_003: 7 wrong → 7 wrong (unchanged — SPEAKER_24 assigned to Mayor when it should be SPEAKER_21)

**Why it didn't advance:**
- 2-error reduction not material against acceptance bar
- ex_003 bottleneck is a diarization accuracy problem (wrong VAD/diarization assignment), not a clustering problem
- The 2-error gain is real and correctly achieved, but too small to justify production complexity

**Architecture notes:**
- Per-segment approach is architecturally sound
- Temporal non-overlap constraint is the correct safeguard
- Threshold-invariant results are a good sign of robustness
- The pipeline (`benchmark_per_segment.py`, `per_segment_clustering.py`) is available for future experimentation

**Verdict:** NOT READY. Not adopted. See `docs/per-segment-clustering/architecture.md` for full benchmark data.

---

## Current Baseline Definition

The current baseline is:

```
faster-whisper medium (GPU)
    ↓
pyannote 3.1 diarization
    ↓
microblock cleanup (min_duration=1.5s, dominance_threshold=0.60)
    ↓
registry v2.1 speaker mapping
    ↓
structured transcript JSON
    ↓
review/apply/publish workflow
```

**Do not add clustering stages to this pipeline without re-benchmarking against this baseline.**

**Do not modify the baseline components without a written architecture note.**

---

## Known Failure Modes

These are document-known failure modes that require targeted rescue, not global architectural changes:

### ex_003 Pattern (Known-Bad Window)
**Window:** ~1650-1850s  
**Failure:** pyannote assigns SPEAKER_24 when it should assign SPEAKER_21 (Mayor Catherine Read)  
**Symptom:** 7 wrong attributions in this window  
**Root cause:** Diarization accuracy — wrong speaker ID assigned during continuous Mayor speech  
**Clustering fixable:** NO — post-hoc clustering cannot reverse a wrong diarization assignment

### SPEAKER_06/SPEAKER_07 Confusion
**Failure:** pyannote assigns different IDs to Tom Peterson vs JC Martinez  
**Symptom:** Appears in council appointment sections  
**Per-segment clustering:** Fixed 2 errors here (ex_004) — correct behavior  
**Registry-level fix:** Would require registry update for these IDs

### Short Micro-Blocks at Transitions
**Failure:** pyannote over-segments at speaker transitions → consecutive micro-blocks <1.5s  
**Symptom:** UNKNOWN speaker assignments for 1-3 word utterances  
**Current handling:** microblock cleanup pass collapses with dominance threshold  
**Residual:** Some still pass through → flagged for review

---

## What Comes Next

See `docs/next-priorities-2026-04-23.md` for the current priority list.

Short version:
1. **Lock this baseline** ← you are here
2. **Review prioritization** — focus on high-risk segments first
3. **Targeted bad-window rescue** — bounded experiments on known-bad windows only
4. **Multi-meeting gold set** — broader evidence before more architecture experiments

---

## Files

| File | Purpose |
|---|---|
| `docs/baseline-locked-2026-04-23.md` | This document |
| `docs/embedding-clustering-benchmark-2026-04-22.md` | Centroid clustering rejection data |
| `docs/per-segment-clustering/architecture.md` | Per-segment clustering rejection data |
| `docs/next-priorities-2026-04-23.md` | Current priorities |

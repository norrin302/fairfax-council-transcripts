# apr-14-2026 Pipeline Benchmark Report

**Date:** 2026-04-22
**Audio:** 10,021s (2h 47m), 24,612 ASR words
**ASR:** faster-whisper medium, GPU, word-level timestamps
**Diarization:** pyannote 3.1 (AgglomerativeClustering, min_cluster_size=25, threshold=0.78, min_duration_off=2.0s)
**GPU:** NVIDIA GTX 1650 SUPER (4GB) on Juggernaut

---

## Three-Stage Benchmark Results

Three runs on the same audio, evaluated against gold-set (5 excerpts, 49 turns):

| Metric | Stage 1: Raw | Stage 2: +Cleanup | Stage 3: +Registry v2 |
|--------|-------------|-------------------|------------------------|
| **Match rate** | **0.0%** | **0.0%** | **32.6%** |
| **Wrong attributions** | 36 | 36 | **22** |
| Unknown-when-named | 2 | 2 | 3 |
| **Review burden** | 483 (37.4%) | 577 (45.4%) | 860 (67.6%) |
| Total segments | 1,290 | 1,272 | 1,272 |

**Key insight:** Cleanup (Stage 2) reorganizes blocks but does NOT fix speaker names. The registry mapping (Stage 3) is what reduces wrong attributions — from 36 → 22 (-39%).

---

## Three-Stage Per-Excerpt Breakdown

| Excerpt | Duration | Gold turns (named/unk) | Stage 1 wrong | Stage 2 wrong | Stage 3 match | Stage 3 wrong |
|---------|----------|----------------------|--------------|--------------|--------------|--------------|
| ex_001 (open) | 72-180s | 3/0 | 3 | 3 | **100%** | 0 |
| ex_002 (roll call) | 300-420s | 2/3 | 2 | 2 | **40%** | 0 |
| ex_003 (agenda) | 1651-1850s | 9/4 | 9 | 9 | 7.7% | 8 |
| ex_004 (appointments) | 3700-3900s | 20/1 | 20 | 20 | 33.3% | 13 |
| ex_005 (hearings) | 5000-5200s | 2/5 | 2 | 2 | 42.9% | 1 |
| **Total** | — | **36/13** | **36** | **36** | **32.6%** | **22** |

---

## Speaker Registry v2.1 — Confirmed Mappings

### Officials / Recurring Speakers

| Canonical name | pyannote IDs | Strongest ID (segs) | Notes |
|---------------|-------------|---------------------|-------|
| Mayor Catherine Read | SPEAKER_21, **SPEAKER_22**, SPEAKER_20, SPEAKER_15 | SPEAKER_22 (66 segs) | pyannote uses 4 IDs for the mayor at different meeting portions |
| Councilmember Tom Peterson | **SPEAKER_06**, SPEAKER_30 | SPEAKER_06 (57 segs) | Consistent across appointment discussions |
| Councilmember Stacy Hardy-Chandler | **SPEAKER_17** | SPEAKER_17 (22 segs) | Active in motions and votes |
| Councilmember Rachel McQuillen | **SPEAKER_26** | SPEAKER_26 (27 segs) | pyannote sometimes assigns SPEAKER_27 (Stacy Hall) to her |
| Councilmember Stacy Hall | **SPEAKER_27** | SPEAKER_27 (36 segs) | pyannote cross-assigns with Rachel McQuillen |
| Councilmember Anthony Amos | **SPEAKER_28** | SPEAKER_28 (11 segs) | SPEAKER_25 and SPEAKER_22 sometimes assigned to him — not in registry |
| JC Martinez | **SPEAKER_07**, SPEAKER_14 | SPEAKER_07 (28 segs) | City staff presenter; confirmed via video frame |
| Daniel Alexander | **SPEAKER_05** | SPEAKER_05 (10 segs) | Budget Director; confirmed via video frame |
| William Pitchford | **SPEAKER_24** | SPEAKER_24 (8 segs) | City staff presenter |

### Public Commenters

| Name | pyannote ID | Segments |
|------|------------|---------|
| Elijah Tibbs | SPEAKER_00 | 3 |
| Kevin Anderson | SPEAKER_01 | 9 |
| Janice Miller | SPEAKER_02 | 5 |
| Douglas Stewart | SPEAKER_03 | 7 |
| Alan Glenn | SPEAKER_04 | 4 |
| Fasa Alam | SPEAKER_08 | 3 |
| Toby Sorenson | SPEAKER_11 | 6 |
| Becky Rager | SPEAKER_16 | 5 |
| Janet Jaworski | SPEAKER_23 | 6 |
| Anita Light | SPEAKER_31 | 7 |
| Dale Lucena | SPEAKER_29 | 6 |

---

## Root Cause: pyannote ID Reassignment

**Problem:** pyannote's clustering reassigns speaker IDs within a single meeting. One pyannote ID (e.g., SPEAKER_22) maps to Mayor Catherine Read for most of the meeting, but occasionally assigns that same ID to a different speaker (e.g., Councilmember Anthony Amos) in a specific time portion.

**Impact:** When the registry maps SPEAKER_22 → Mayor Catherine Read, it correctly identifies the mayor in 66 segments but **wrongly assigns 1 segment** where pyannote actually assigned SPEAKER_22 to Councilmember Anthony Amos. This creates 1 "wrong" per reassignment event.

**Severity:** ex_003 (1651-1850s) and ex_004 (3700-3900s) are most affected because they contain complex council discussions with rapid speaker transitions where pyannote frequently reassigns IDs.

**Fix:** Embedding-based speaker clustering — track actual voice characteristics rather than relying on stable pyannote IDs across meeting portions.

---

## Quality Issues Found

### 1. Text ordering in overlapping speech
During Pledge of Allegiance and applause, multiple speakers overlap. Diarization assigns word-level segments to different speakers. Merging these micro-blocks produces fluent text but word order may reflect the overlapping structure. All `merged_into` blocks are flagged `needs_review: true`.

### 2. Pyannote reassignment corrupts registry mapping
The registry correctly maps most recurring speakers, but reassignment events create wrong attributions. These are concentrated in complex discussion portions (ex_003, ex_004).

### 3. Review burden increase from registry
Stage 3 flags 860/1272 (67.6%) blocks for review — higher than Stage 1 (37.4%). This is because:
- Unknown blocks after cleanup: 161
- Registry-unmapped pyannote IDs: ~230 (these are not named officials)
- `needs_review` from cleanup (merged_into, kept_review): ~470

The high review burden is expected with conservative labeling.

---

## Before/After Summary

| Metric | Baseline (pre-pipeline) | After pipeline v2.1 | Change |
|--------|----------------------|---------------------|--------|
| Unknown blocks | 483 (37.5%) | 161 (12.7%) | **-322 blocks, -24.8pp** |
| Wrong attributions (gold set) | 36 | 22 | **-14 (-39%)** |
| Unknown-when-named | 2 | 3 | +1 |
| Named match rate (gold set) | 0.0% | 32.6% | **+32.6pp** |
| Review burden | 0 | 860 (67.6%) | +860 |

---

## Files Changed (this pass)

| File | Change |
|------|--------|
| `speaker_registry/speakers.json` | v2.1: 20 confirmed pyannote ID mappings added |
| `pipeline/src/benchmark_stages.py` | NEW: three-stage benchmark script |
| `docs/pipeline-benchmark-2026-04-22.md` | Updated with three-stage measured results |

---

## What Still Sucks

1. **Pyannote ID reassignment**: 22 wrong attributions remain, concentrated in complex council discussion portions. Fixable with embedding-based clustering.
2. **Review burden**: 860 blocks (67.6%) flagged for review. High but expected with conservative labeling approach.
3. **No embedding-based clustering**: The current heuristic can't track speakers across ID reassignments. Needs per-segment voice embedding extraction.
4. **Gold set coverage**: 5 excerpts, 49 turns — needs more coverage especially for council discussion phases.

---

## Recommendation: Ready for Apply/Publish?

**Conditional yes — with caveats.**

The pipeline is ready to generate structured output for human review, but:

1. **Do NOT auto-publish without review** — 22 wrong attributions would appear in public output
2. **Use the 860-review-burden output** as the input to review mode, not the raw structured JSON
3. **Ex_001 and ex_002 are near-production quality** (100% and 40% match, 0 wrong in ex_001) — these meeting-opening portions can be reviewed quickly
4. **ex_003 and ex_004 need careful review** — 21 wrong attributions in these two excerpts alone

**Next step before full publish:**
- Run review-mode on the Stage 3 output
- Apply review decisions for high-confidence corrections only
- Then publish

**Non-negotiable before full publish:** No named official should appear as a wrong attribution in public output.

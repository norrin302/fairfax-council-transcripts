# Multi-Meeting Gold Set — Proposal
**Date:** 2026-04-23  
**Purpose:** Gather broader evidence before any more architecture experiments

---

## Why a Broader Gold Set

The current benchmark is anchored to apr-14-2026 (49 gold turns across 5 excerpts). Both clustering experiments were evaluated against this single meeting, which creates two problems:

1. **Overfitting to one meeting's quirks.** The ex_003 window is a specific diarization failure mode that may not generalize. If we optimize for apr-14-2026's error profile, we may build the wrong thing for future meetings.

2. **Noise floor.** 49 turns is small. A 2-error improvement (20→18 on apr-14-2026) could be noise — 4% of the gold set. We don't know if it's consistent across meetings.

A broader gold set would tell us:
- What error rate is typical across meetings
- Which error patterns are consistent (appear in multiple meetings) vs. one-off failures
- Whether the 2-error improvement from per-segment clustering is repeatable or noise
- Whether the ex_003 pattern (dais transition errors) is the dominant failure mode in all meetings

---

## Goal

Build a 200-300 turn gold set across 3-5 additional meetings to establish:
1. A baseline error rate per meeting (wrong attributions / named turns)
2. A signal on whether current baseline errors are consistent or meeting-specific
3. Enough evidence to know whether any future experiment is actually improving things or noise

---

## Scope

### Meetings to Target

Priority order based on availability:

| Meeting | Why | Expected Value |
|---------|-----|----------------|
| apr-07-2026 | Same council, available | Same-day baseline comparison |
| may-05-2026 (upcoming) | Budget adoption — high-stakes | Complex dais debate, new failure modes |
| ??? | Additional council meeting | Expand evidence base |

### Turns Per Meeting

Target 40-60 gold turns per meeting (enough to detect a 3-5 turn difference at 90% confidence).

### Gold Turn Criteria

For a turn to be in the gold set:
1. Speaker must be identifiable from video/nameplate/known-voice evidence
2. Text must be audible and intelligible
3. Turn duration ≥ 5 seconds (skip microblocks)
4. Mix of: named officials, procedural, public comment

### Gold Turn Format

Same schema as `pipeline/gold-set/apr-14-2026.json` (`fairfax.gold_set.v1`).

---

## Implementation

### Phase 1: Collect Gold Turns (Apr-07-2026)

1. Run full baseline pipeline on apr-07-2026 (ASR → diarization → merge → cleanup → registry → structured)
2. Generate review queue
3. Russ reviews 40-60 turns manually, assigns ground-truth speaker names
4. Export as `pipeline/gold-set/apr-07-2026.json`

**Effort estimate:** 2-3 hours of manual review for Russ

### Phase 2: Baseline Benchmark on Apr-07-2026

Run `gold_set_eval.py` on apr-07-2026 to get baseline error counts:

```bash
python3 pipeline/src/gold_set_eval.py \
  --structured transcripts_structured/apr-07-2026.json \
  --gold-set pipeline/gold-set/apr-07-2026.json \
  --out /tmp/apr-07-2026_baseline.json
```

Compare to apr-14-2026 baseline.

### Phase 3: Cross-Meeting Analysis

After 2+ meetings in the gold set, run cross-meeting analysis:
- Per-meeting error rates
- Error pattern frequency (how often does ex_003 pattern appear?)
- Which speaker transitions are most error-prone across all meetings

### Phase 4: Future Experiments Against Multi-Meeting Gold Set

Any future clustering or rescue experiment must show improvement across ≥2 meetings before advancing.

---

## Files

| File | Purpose |
|---|---|
| `pipeline/gold-set/apr-14-2026.json` | Existing gold set (49 turns, 5 excerpts) |
| `pipeline/gold-set/apr-07-2026.json` | Next target |
| `pipeline/gold-set/may-05-2026.json` | Budget adoption (TBD) |
| `docs/multi-meeting-gold-set-2026-04-23.md` | This document |

---

## Decision Points for Russ

1. **Approve apr-07-2026 gold set collection** — approve the 2-3 hours of manual review
2. **Decide how many meetings** to build gold sets for before next architecture experiment
3. **Decide if the review burden for gold set collection is worth it** vs. automated sampling

---

## Constraints

- No automated gold set generation yet — requires manual review
- Each meeting's gold set must be committed to Git
- Gold set schema must remain stable (`fairfax.gold_set.v1`)

---

## Kill Criteria

If apr-07-2026 baseline error rate is within 5 percentage points of apr-14-2026:
- We have a consistent baseline — proceed with confidence that improvements generalize

If apr-07-2026 baseline error rate is dramatically different (>15pp):
- Something about apr-14-2026 is unusual — investigate before more experiments
- Consider whether the gold set sampling method needs adjustment

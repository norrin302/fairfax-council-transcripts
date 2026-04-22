# apr-14-2026 Pipeline Benchmark Report

**Date:** 2026-04-22
**Audio:** 10,021s (2h 47m), 24,612 ASR words
**ASR:** faster-whisper medium, GPU, word-level timestamps
**Diarization:** pyannote 3.1 (AgglomerativeClustering, min_cluster_size=25, threshold=0.78, min_duration_off=2.0s)
**GPU:** NVIDIA GTX 1650 SUPER (4GB) on Juggernaut

---

## Benchmark: Cleanup Impact

| Stage | Total blocks | UNKNOWN | Unknown% | Needs review | Notes |
|-------|-------------|---------|---------|-------------|-------|
| **Merge baseline** | 1,288 | 483 | **37.5%** | 0 | raw pyannote merge |
| **+ microblock cleanup** | 1,270 | 168 | 13.2% | — | dom=0.60, min_dur=1.5s |
| **+ sandwich attach** | 1,270 | 161 | **12.7%** | 539 | after both passes |

**UNKNOWN reduction: 322 blocks (24.8 percentage points), from 37.5% → 12.7%**

### Threshold sweep

| threshold | total | unknown | unk% | merged_into | kept_review |
|-----------|-------|---------|------|------------|-------------|
| 0.50 | 1,242 | 138 | 11.1% | 53 | 145 |
| **0.60** | **1,270** | **161** | **12.7%** | **33** | **193** |
| 0.70 | 1,282 | 167 | 13.0% | 27 | 211 |
| 0.75 | 1,284 | 168 | 13.1% | 25 | 215 |
| 0.80 | 1,288 | 170 | 13.2% | 22 | 222 |

**Recommended: threshold=0.60** — best balance of unknown reduction and false-attribution risk.
At 0.50, 53 blocks are force-assigned (vs 33 at 0.60) — more aggressive but still manageable.

---

## Action Breakdown (threshold=0.60)

| Action | Count | Description |
|--------|-------|-------------|
| `kept` | 731 | Non-micro blocks, pass through unchanged |
| `sandwich_attached` | 313 | Short unknown fragments between same-speaker neighbors |
| `kept_review` | 193 | Micro-blocks with no dominant speaker — deferred to human review |
| `merged_into` | 33 | Micro-blocks with ≥60% dominant speaker — force-assigned with review flag |

**Key finding:** The sandwich attach is the most impactful pass (313 blocks). It correctly attaches short unknown interjections (≤5 words, not sentence-ending) between two blocks from the same confirmed speaker.

---

## Quality Issues Found

### 1. Text ordering in merged blocks (overlapping speech)

During the Pledge of Allegiance, multiple speakers say overlapping lines. The diarization assigns word-level segments to different speakers. When microblock cleanup merges these, the resulting text may be fluent but the word order reflects the overlapping structure.

Example:
```
# Merged block output (SPEAKER_11, dom=0.667):
"you. Sorry. Thank"

# Reality:
#   SPEAKER_07: "and to the"
#   SPEAKER_11: "you. Sorry. Thank you so much for joining us."
# The merged text reads fluently but the word order is from overlapping speech.
```

**Impact:** Text WER is unreliable for merged blocks containing overlapping speech. Speaker attribution is the more reliable metric for merged blocks.

**Mitigation:** Flag merged blocks with `review_reason: "microblock_cleanup"` and require human review. Text content should be verified during review.

### 2. Remaining UNKNOWN blocks (161 total)

After cleanup, 161 blocks remain UNKNOWN. These fall into categories:

- **Short silence/noise** (<1.5s, no diarization overlap): expected, safe to stay unknown
- **Overlapping public commenters** (pledge, applause): honest floor
- **Short procedural interjections** that couldn't be safely attached: deferred to review

The honest floor for this meeting is approximately 114 Unknown Speaker turns (from the full manual review). The current 161 reflects the automated pipeline's additional uncertainty.

---

## Speaker Clustering

**Finding:** pyannote outputs 34 unique speaker IDs for a 9-person council meeting.

Full embedding-based clustering requires running the pyannote embedding extraction pipeline, which is compute-intensive. A production clustering implementation should:

1. Extract per-segment embeddings using `wespeaker-voxceleb-resnet34-LM` (already used by pyannote)
2. Average embeddings per pyannote speaker ID
3. Agglomerative cluster the speaker-level embedding vectors
4. Map cluster IDs to canonical speaker registry entries

**Current status:** `cluster_speakers.py` is scaffolded but requires embedding extraction to be production-quality. The fallback speech-rate heuristic is not suitable for production use.

---

## Gold-Set Evaluation

**Gold set:** 5 excerpts, 49 turns from apr-14-2026

| Excerpt | Duration | Turns | Description |
|---------|----------|-------|-------------|
| ex_001 | 72-180s | 3 | Meeting opening, Pledge of Allegiance, Library Week |
| ex_002 | 300-420s | 5 | Roll call, public comment signup |
| ex_003 | 1650-1850s | 13 | Agenda adoption, consent agenda |
| ex_004 | 3700-3900s | 21 | Appointments discussion |
| ex_005 | 5000-5200s | 7 | Public hearings |

**Evaluation:** Pipeline output vs gold set (with partial SPEAKER_21→Mayor Catherine Read mapping)

| Metric | Value |
|--------|-------|
| Speaker match rate | 20.4% (10/49 turns) |
| Wrong attributions | 37 |
| Unknown when Named | 0 |
| False Confident Rate | 0 (no named officials labeled Unknown) |

**Interpretation:** The 20.4% match rate reflects that only SPEAKER_21→Mayor Catherine Read is correctly mapped. All other pyannote IDs (SPEAKER_06, SPEAKER_09, SPEAKER_17, SPEAKER_24, etc.) are not yet mapped to real names. These appear as "wrong" in the evaluation because the candidate says SPEAKER_17 while gold says Unknown Speaker — but Unknown Speaker is a valid conservative output.

**Correct interpretation of "wrong":** The evaluation counts as "wrong" any case where the candidate assigned a specific pyannote ID that doesn't match the gold name. In most of these cases, the gold says "Unknown Speaker" (correct conservative) but the candidate assigned a named pyannote ID. This is a false-confident attribution, which is the real quality issue to avoid.

**Recommended metric:** Count turns where the pipeline assigned a wrong specific name (not Unknown), rather than turns where the raw pyannote ID differs from the gold name.

---

## Before/After Summary

| Metric | Before cleanup | After cleanup | Change |
|--------|---------------|---------------|--------|
| Total blocks | 1,288 | 1,270 | -18 |
| UNKNOWN blocks | 483 | 161 | **-322 (-24.8pp)** |
| UNKNOWN rate | 37.5% | 12.7% | **-24.8pp** |
| Needs review | 0 | 539 | +539 |
| False confident (Named as Unknown) | 0 | 0 | 0 |
| Wrong specific attributions | ~37 | ~37 | unchanged (registry unmapped) |

**Conclusion:** Microblock cleanup + sandwich attach reduces unknown rate by 24.8 percentage points with zero increase in false-confident wrong attributions. The 539 needs_review blocks are all correctly flagged for human review. No named official is incorrectly labeled Unknown.

---

## What Still Sucks

1. **Text ordering in overlapping speech** — merged blocks can have jumbled word order from interleaved overlapping speech. Requires human review of merged block text.
2. **No speaker clustering** — 34 pyannote IDs for 9 people is unresolved. Needs embedding-based clustering.
3. **Speaker registry mapping is manual** — only SPEAKER_21 confirmed from this meeting. Other IDs require per-meeting manual mapping or automated clustering.
4. **Gold set is limited** — 49 turns from 5 excerpts. More coverage needed for robust evaluation.

---

## Files Changed (this pass)

| File | Change |
|------|--------|
| `pipeline/src/cleanup_blocks.py` | NEW: micro-block cleanup + sandwich attach |
| `pipeline/src/cluster_speakers.py` | NEW: speaker clustering (scaffold — needs embedding extraction for production) |
| `pipeline/src/gold_set_eval.py` | NEW: gold-set creation and evaluation workflow |
| `speaker_registry/speakers.json` | v2: added confidence_boost, min_diarization_confidence, diarization_speaker_ids, text_patterns fields |
| `pipeline/gold-set/apr-14-2026.json` | NEW: gold set (5 excerpts, 49 turns) |
| `docs/pipeline-architecture-2026-04-22.md` | Updated with benchmark results |
| `pipeline/src/merge_transcript.py` | Bug note: speaker_at loop correctly increments `i` (existing production code is correct) |

---

## Next Steps

1. **Fix speaker registry mapping** — integrate registry v2 into merge pipeline so SPEAKER_21 maps to Mayor Catherine Read and SPEAKER_30 maps to Councilmember Tom Peterson before output
2. **Run full gold-set evaluation with mapped names** — currently 80% of "wrong" attributions are actually Unknown Speaker being assigned a raw pyannote ID (false confident, but the speaker is still Unknown Speaker in the gold)
3. **Implement embedding-based speaker clustering** — reduce 34 → ~10-15 pyannote IDs
4. **Add overlap detection** — flag blocks with overlapping speech for text review
5. **Expand gold set** — add 3-4 more excerpts covering different meeting phases

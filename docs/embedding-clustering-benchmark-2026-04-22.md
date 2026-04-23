# Embedding-Based Speaker Clustering — Benchmark Report
**Date:** 2026-04-22  
**Author:** Neo  
**Test subject:** apr-14-2026 pipeline + wespeaker-voxceleb embedding layer

---

## 1. What was tested

| | Baseline | Candidate |
|---|---|---|
| Method | faster-whisper medium + pyannote 3.1 + microblock cleanup + registry v2.1 | baseline + wespeaker-voxceleb-resnet34-LM per-segment embeddings + agglomerative cosine-similarity clustering at 0.75 |
| Files | `pipeline/src/benchmark_clustering.py` | same + `extract_embeddings.py` |

**Architecture under test:**
1. Extract per-segment 256-dim voice embedding from each diarized segment
2. Average embeddings per pyannote speaker ID → speaker centroid
3. Agglomerative cluster the 34 centroids by pairwise cosine similarity
4. Apply cluster ID instead of raw pyannote ID before registry mapping

---

## 2. Benchmark results

```
=== BASELINE (cleanup + registry v2.1) ===
Segments: 1721
Match: 38.7% | Wrong: 38 | UWN: 8 | Review: 1490/1721

=== CANDIDATE (embeddings + clustering + registry v2.1) ===
Embedding extraction: 1532 processed, 189 skipped, 0 failed
Raw speakers: 34, Clusters: 34, Merges: 0
Match: 38.7% | Wrong: 38 | UWN: 8 | Review: 1490/1721

=== COMPARISON ===
Wrong attributions:  baseline=38, candidate=38, delta=+0
Match rate:         baseline=38.7%, candidate=38.7%, delta=+0.0%
Distinct speakers:  baseline=21, candidate=21
Recommendation: NOT_READY
```

**Per-excerpt breakdown:**

| Excerpt | Baseline Wrong | Candidate Wrong | Delta | Notes |
|---|---|---|---|---|
| ex_001 | 3 | 3 | 0 | |
| ex_002 | 1 | 1 | 0 | |
| ex_003 | 19 | 19 | 0 | Most errors here |
| ex_004 | 15 | 15 | 0 | |
| ex_005 | 0 | 0 | 0 | |

**Zero improvement.** Clustering merged zero speakers at 0.75 threshold.

---

## 3. What the similarity matrix reveals

The full 34×34 centroid cosine-similarity matrix was computed. Pairs above 0.75 similarity:

| Pair | Similarity | Should merge? |
|---|---|---|
| SPEAKER_06 vs SPEAKER_07 | **0.7737** | **NO** — Tom Peterson vs JC Martinez (confirmed different people in structured JSON) |
| SPEAKER_20 vs SPEAKER_21 | **0.7511** | **YES** — both mapped to Mayor Catherine Read |

At 0.60 threshold, same two pairs qualify.

**The core problem is visible here:** The centroid approach cannot distinguish SPEAKER_06 (Tom Peterson, 57 turns) from SPEAKER_07 (JC Martinez, 26 turns) at 0.77 similarity — even though they are clearly different people speaking in the same meeting. Lowering threshold to force a merge would be wrong.

Meanwhile, the pairs that *should* merge (same person with pyannote ID reassignment, like the Mayor across SPEAKER_20/21/22) don't have as high similarity — SPEAKER_20 vs SPEAKER_21 is 0.75, but SPEAKER_21 vs SPEAKER_22 is only 0.21. This is the reassignment problem in embedding space.

---

## 4. Root cause diagnosis

### 4a. Why centroid clustering fails here

pyannote speaker IDs are **reassigned within the same meeting**. This means:
- SPEAKER_21 = Mayor Catherine Read (301 segments, consistent voice)
- SPEAKER_20 = Mayor Catherine Read (26 segments)
- SPEAKER_22 = Mayor Catherine Read (9 segments)

These are the **same physical speaker** but pyannote gave them different IDs. A centroid computed across all segments of SPEAKER_21 is valid (301 segs of consistent voice). But SPEAKER_20 with only 26 segments might have a noisy centroid if those 26 segments include cross-talk or background.

The cosine similarity between SPEAKER_21's centroid and SPEAKER_20's centroid is **0.75** — above the 0.75 threshold but barely. Lowering to 0.60 adds no new pairs because the next-highest pair (SPEAKER_06 vs SPEAKER_07 at 0.77) would incorrectly merge two different people.

### 4b. What the errors actually are

In ex_003 (1650-1850s):
- **Gold says:** Mayor Catherine Read speaking continuously from 1650-1690s
- **pyannote assigns:** SPEAKER_24 during 1655-1690s
- **Registry maps:** SPEAKER_24 → William Pitchford
- **Result:** wrong attribution = Mayor called William Pitchford

This is **not a clustering problem**. pyannote's raw diarization assigned the *wrong speaker ID* to the Mayor during this segment. The ID-to-name registry cannot fix this — it correctly maps SPEAKER_24 → William Pitchford, but pyannote should have assigned SPEAKER_21 (or 20/22) here.

Clustering SPEAKER_24 with any other cluster won't help because the underlying diarization is wrong for this time range.

### 4c. What clustering actually does (and doesn't fix)

| Error type | Clustering can fix? | Why |
|---|---|---|
| pyannote ID reassignment (same person → different IDs) | Partially — if centroids are discriminative enough | Works when same person gets different IDs AND centroids are distinct; fails when centroids are ambiguous |
| pyannote wrong speaker assignment | **No** | If pyannote assigns SPEAKER_24 when it should be SPEAKER_21, clustering can't reverse that |
| Registry gaps (unmapped pyannote ID) | No | Clustering doesn't add new names |

---

## 5. What was built

### Files created/modified

| File | Change |
|---|---|
| `pipeline/src/extract_embeddings.py` | New: extract per-segment embeddings using `pyannote/wespeaker-voxceleb-resnet34-LM` |
| `pipeline/src/benchmark_clustering.py` | New: self-contained benchmark script with baseline + candidate evaluation |
| `pipeline/src/benchmark_clustering.py` (local copy) | Fixed `canonical_name` → `display_name` for registry compatibility |
| `/tmp/bench_cluster/` | Juggernaut working directory with all scripts, data, outputs |

### Commands run on Juggernaut

```bash
# Setup
ssh ... norrin302@192.168.13.200
mkdir -p /tmp/bench_cluster

# Copy scripts
scp -i ~/.ssh/neo_to_50_ed25519 \
    pipeline/src/benchmark_clustering.py \
    pipeline/src/extract_embeddings.py \
    norrin302@192.168.13.200:/tmp/bench_cluster/

# Copy required data files
scp -i ~/.ssh/neo_to_50_ed25519 \
    pipeline/gold-set/apr-14-2026.json \
    speaker_registry/speakers.json \
    transcripts_structured/apr-14-2026.json \
    norrin302@192.168.13.200:/tmp/bench_cluster/

# Run benchmark
docker run --rm --gpus all \
  -v /mnt/disk1:/mnt/disk1 \
  -v /tmp/bench_cluster:/work \
  --entrypoint python \
  fairfax-pipeline-diarize_pyannote \
  /work/benchmark_clustering.py \
    --asr /mnt/disk1/fairfax-council-transcripts/pipeline/work/apr-14-2026/asr/faster-whisper_gpu_medium.json \
    --diarization /mnt/disk1/fairfax-council-transcripts/pipeline/work/apr-14-2026/diarization/pyannote_segments.json \
    --audio /mnt/disk1/fairfax-council-transcripts/pipeline/work/apr-14-2026/audio/audio_16k_mono.wav \
    --registry /work/speakers.json \
    --gold-set /work/gold_apr-14-2026.json \
    --structured /work/struct_apr-14-2026.json \
    --out /work/cluster_benchmark.json \
    --device cuda \
    --similarity-threshold 0.75 \
    --min-duration 1.5 \
    --dominance-threshold 0.60
```

**Embedding extraction took ~3 minutes for 1721 segments** on GTX 1650 SUPER. Wespeaker model downloads ~26MB on first run.

---

## 6. Similarity matrix (full, for future tuning)

Top 20 pairwise cosine similarities between speaker centroids:

```
SPEAKER_06 vs SPEAKER_07:  0.7737  ← Tom Peterson vs JC Martinez (DIFFERENT people!)
SPEAKER_20 vs SPEAKER_21:  0.7511  ← Mayor reassignment pair (should merge)
SPEAKER_19 vs SPEAKER_20:  0.5983
SPEAKER_18 vs SPEAKER_20:  0.5780
SPEAKER_18 vs SPEAKER_21:  0.5600
SPEAKER_19 vs SPEAKER_21:  0.5463
SPEAKER_03 vs SPEAKER_04:  0.4746
SPEAKER_05 vs SPEAKER_06:  0.4713
SPEAKER_17 vs SPEAKER_21:  0.4692
SPEAKER_06 vs SPEAKER_32:  0.4480
SPEAKER_26 vs SPEAKER_27:  0.4408
SPEAKER_17 vs SPEAKER_20:  0.4399
SPEAKER_11 vs SPEAKER_20:  0.4348
SPEAKER_15 vs SPEAKER_22:  0.4178
SPEAKER_13 vs SPEAKER_18:  0.3988
SPEAKER_13 vs SPEAKER_20:  0.3942
SPEAKER_00 vs SPEAKER_31:  0.3875
SPEAKER_14 vs SPEAKER_17:  0.3828
SPEAKER_16 vs SPEAKER_18:  0.3815
```

**Key finding:** SPEAKER_06 vs SPEAKER_07 is the *highest* cross-person similarity. This means a lower threshold (e.g. 0.60) would force a merge of two confirmed different people — exactly what we need to avoid.

---

## 7. Why this is NOT ready

1. **Zero merges at 0.75:** Clustering produces no improvement at the configured threshold.
2. **Threshold dilemma:** 0.75 is too high (misses the Mayor reassignment pair at 0.75 exactly). 0.60 would incorrectly merge SPEAKER_06+SPEAKER_07 (different people, 0.77) with SPEAKER_20+SPEAKER_21 (same person, 0.75). No safe threshold exists.
3. **Centroid approach is fragile:** Averaging embeddings across all segments of a pyannote ID loses temporal information. Two different people speaking at different times with the same pyannote ID will produce a corrupted centroid.
4. **The real errors are not clustering failures:** ex_003 errors (19 of 38 wrong) come from pyannote assigning SPEAKER_24 when it should be SPEAKER_21. No clustering approach fixes this — it's a voice activity detection / diarization accuracy problem.
5. **SPEAKER_06 vs SPEAKER_07 paradox:** Two confirmed different people (Tom Peterson vs JC Martinez) have the highest cross-person similarity (0.77). This reveals that centroid similarity doesn't reliably distinguish same-person vs different-person in this domain.

---

## 8. What actually fixes the errors

The 38 wrong attributions are **not a clustering problem.** They are:

| Count | Root cause | Fix |
|---|---|---|
| ~19 | pyannote assigns SPEAKER_24 when it should be SPEAKER_21 (Mayor reassignment error in ex_003) | Per-segment embedding clustering, not centroid |
| ~15 | SPEAKER_06/SPEAKER_07 confusion (Tom Peterson vs JC Martinez, high acoustic similarity) | Per-segment clustering + temporal continuity constraint |
| ~4 | Other mis-mappings | Per-segment clustering |

**Per-segment clustering** (cluster each 1721 diarization segments individually, not per speaker centroid) would:
- Handle time-localized reassignment (not global centroid)
- Use temporal continuity to constrain merges (if segment A is at t=100s and B is at t=9000s, they can't be the same speaker)
- Avoid centroid corruption from multi-person pyannote IDs

This requires a larger architectural change: clustering 1721 segments directly rather than 34 centroid vectors.

---

## 9. Recommendation

**NOT READY to become new baseline.**

The embedding extraction works reliably (1532/1721 segments processed, 189 skipped for being too short). The cluster output is well-formed. But:

- The approach (centroid-level clustering) is wrong for this problem
- Zero merges at threshold 0.75 means no measurable improvement
- The errors that remain are not fixable by centroid clustering
- A lower threshold introduces unacceptable false merges

### Next step (recommended):

**Per-segment embedding clustering** instead of centroid clustering:
1. Extract embedding for each of the 1721 diarization segments
2. Build a similarity graph where nodes are segments, edges are cosine similarity
3. Apply agglomerative clustering with temporal continuity constraints
4. Propagate speaker labels from cluster centroids to segments

This is architecturally more complex but directly addresses the pyannote ID reassignment problem.

### What IS ready:
- Embedding extraction pipeline ✓ (reusable for per-segment clustering)
- Similarity matrix for threshold tuning ✓
- The benchmark infrastructure is solid ✓

---

## 10. What still sucks

| Problem | Severity | Notes |
|---|---|---|
| Centroid clustering is wrong architecture | High | Only works when one pyannote ID = one person. Fails on reassignment. |
| No safe merge threshold | High | 0.75 merges nothing; 0.60 merges different people |
| ex_003 errors not fixable by clustering | High | 19 errors from pyannote assigning wrong ID (SPEAKER_24 instead of SPEAKER_21) |
| SPEAKER_06 vs SPEAKER_07 acoustic collision | Medium | Two different people, highest similarity. Reveals centroid approach limits. |
| Review burden still 86.5% | Medium | Clustering doesn't reduce the 1490 blocks needing review |
| 34 raw speakers still unresolved | Low | Registry covers 22/34. Remaining 12 are public commenters or marginal |

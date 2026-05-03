# Fairfax Council Transcript Pipeline — Architecture Note
## Production-Ready Low-Cost Pipeline Design

**Date:** 2026-04-22
**Status:** Reviewed and approved for implementation
**Juggernaut:** GTX 1650 SUPER (4GB VRAM), 16 CPU cores, Ubuntu 24.04

---

## Executive Summary

The existing pipeline is sound but the automated speaker diarization quality is the main bottleneck. The core problem: **pyannote over-segments at speaker transitions**, creating many short micro-blocks that cannot be confidently attributed and inflating the UNKNOWN rate to ~37% in automated output vs. ~20% after full manual review.

The fix is not a different ASR engine — it is better merge logic and a micro-block post-processor.

---

## 1. What Was Tested

| Stack | ASR | Diarization | Artifacts |
|-------|-----|-------------|-----------|
| faster-whisper + pyannote | medium/GPU (24612 words) | pyannote 3.1 (1721 segs, 34 speakers) | ✅ existing |
| WhisperX + pyannote | medium/GPU | gated HF model, needs token | ⚠️ blocked |
| faster-whisper only | medium/GPU | none | baseline reference |

---

## 2. Benchmark Results — apr-14-2026 (10021s audio)

### ASR Quality (faster-whisper medium)

| Metric | Value |
|--------|-------|
| Words | 24,612 |
| Language | English (auto-detected) |
| Duration | 10,021s (2h 47m) |
| Word timestamps | ✅ Present |
| Model | `medium` (GPU, float16) |

### Diarization Quality (pyannote 3.1 default params)

| Metric | Value |
|--------|-------|
| Segments | 1,721 |
| Unique speakers | 34 |
| Avg segment duration | 5.0s |
| Min/Max | 0.02s / 181.7s |

**Key finding:** 34 diarization speakers for a 9-person council meeting is significant over-segmentation. pyannote splits at transitions, overlaps, and brief pauses.

### Merge Output (faster-whisper words → pyannote segments)

Default params: `max_gap=1.2s`, `max_duration=35s`

| Metric | Value |
|--------|-------|
| Total blocks | 1,288 |
| Unique speakers in blocks | 35 |
| UNKNOWN blocks | 483 (37.5%) |
| Known blocks | 805 (62.5%) |

### Parameter Sweep (impact on block count and UNKNOWN rate)

```
gap\dur     20s      30s      40s      50s
max_gap=0.3s  2171u=485  2152u=485  2146u=485  2143u=485
max_gap=0.5s  1817u=485  1772u=485  1760u=485  1751u=485
max_gap=0.8s  1532u=484  1466u=484  1440u=484  1429u=484
max_gap=1.0s  1445u=483  1361u=483  1330u=483  1314u=483
max_gap=1.2s  1403u=483  1311u=483  1277u=483  1256u=483
max_gap=1.5s  1370u=482  1273u=482  1235u=482  1211u=482
max_gap=2.0s  1352u=482  1251u=482  1211u=482  1186u=482
```

**Key finding:** UNKNOWN count is stable across all parameters (~482-485). Only total block count changes with gap/duration tuning. The UNKNOWN problem is not a merge parameter issue — it is a diarization quality issue.

### Root Cause Analysis — UNKNOWN blocks

Sample UNKNOWN blocks from the automated merge:
```
[00:01:29 dur=0.2s] UNKNOWN: I
[00:01:42 dur=0.5s] UNKNOWN: I
[00:01:52 dur=1.0s] UNKNOWN: National
[00:02:12 dur=0.4s] UNKNOWN: All
[00:02:14 dur=1.2s] UNKNOWN: libraries
```

These are micro-blocks (0.2-1.2s) at speaker transitions during the Pledge of Allegiance. pyannote produces a burst of overlapping short segments at these transitions, and none has strong enough speaker embedding confidence. The merge assigns UNKNOWN.

**Conclusion:** The problem is pyannote over-segmentation at transitions, not a fundamental ASR or merge logic error. The fix is a micro-block post-processor.

---

## 3. Speaker Identification Quality

Top identified speakers in automated merge:

| Diarization Speaker | Blocks | Confirmed Identity |
|---------------------|---------|-------------------|
| SPEAKER_21 | 145 (11%) | Mayor Catherine Read |
| SPEAKER_30 | 96 (7.5%) | Councilmember Tom Peterson |
| SPEAKER_06 | 92 (7.1%) | Unknown (not Peterson, not Read) |
| SPEAKER_09 | 56 (4.3%) | Unknown |
| SPEAKER_29 | 46 (3.6%) | Unknown |
| SPEAKER_24 | 30 (2.3%) | Unknown |

SPEAKER_21 (Mayor Read) and SPEAKER_30 (Peterson) are identified correctly. The remaining speakers are not yet mapped to real identities.

---

## 4. Pipeline Architecture

### Stage Flow

```
Video/Audio Source
       │
       ▼
┌──────────────────┐
│  1. PREP         │  ffmpeg normalization, audio extraction
│  (prep container) │  Output: 16kHz mono WAV
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  2. ASR          │  faster-whisper medium GPU
│  (asr container) │  Output: JSON with word-level timestamps
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  3. DIARIZATION  │  pyannote speaker diarization
│  (diarize cont.) │  Output: segments with speaker IDs
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  4. MERGE        │  Merge ASR words + diarization segments
│  (merge cont.)   │  Apply speaker registry mapping
│                  │  Apply corrections
│                  │  Output: structured JSON (pre-review)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  5. REVIEW       │  Human review via review-mode UI (?review=1)
│  (browser)       │  Export staged decisions as JSON
│                  │  Apply to structured JSON via apply_review_decisions.py
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  6. PUBLISH      │  publish_structured_meeting.py
│  (local script)  │  Output: HTML + JS + search index
└──────────────────┘
```

### Existing Docker Images (on Juggernaut)

| Image | Purpose | Size |
|-------|---------|------|
| `fairfax-pipeline-prep` | ffmpeg normalization | slim |
| `fairfax-pipeline-asr_faster_whisper` | faster-whisper GPU | 2.76GB |
| `fairfax-pipeline-diarize_pyannote` | pyannote diarization | 8.12GB |
| `fairfax-pipeline-whisperx` | WhisperX alignment (not yet production) | 20.1GB |
| `fairfax-pipeline-merge` | merge + corrections | slim |

### Files to Change

The existing `pipeline/` directory structure needs these additions:

```
pipeline/
  docker/
    merge/
      Dockerfile          ← no change needed
    microblocks/          ← NEW: micro-block post-processor
      Dockerfile
  compose.yml             ← add microblocks + update if needed
  src/
    merge_transcript.py   ← update: micro-block cleanup pass
    cleanup_blocks.py     ← NEW: post-merge cleanup
```

---

## 5. Recommended Improvements

### Priority 1: Micro-Block Post-Processor

**Problem:** pyannote produces micro-segments (<1.5s) at speaker transitions that become UNKNOWN because no single speaker has dominant overlap.

**Fix:** A post-merge cleanup pass that:
1. Identifies consecutive micro-blocks (<1.5s) from different speakers
2. Merges them with adjacent blocks if the dominant speaker covers >60% of the merged duration
3. Flags the result with `review_reason: "microblock_cleanup"` for audit

```python
def cleanup_microblocks(blocks, min_duration=1.5, merge_threshold=0.6):
    """Collapse consecutive micro-blocks into coherent speaker segments."""
    cleaned = []
    i = 0
    while i < len(blocks):
        b = blocks[i]
        dur = b['end'] - b['start']
        
        # If not a micro-block, keep as-is
        if dur >= min_duration:
            cleaned.append(b)
            i += 1
            continue
        
        # Collect consecutive micro-blocks
        cluster = [b]
        j = i + 1
        while j < len(blocks) and (blocks[j]['end'] - blocks[j]['start']) < min_duration:
            cluster.append(blocks[j])
            j += 1
        
        # Find dominant speaker in cluster
        speaker_dur = {}
        for cb in cluster:
            sp = cb['speaker_id']
            d = cb['end'] - cb['start']
            speaker_dur[sp] = speaker_dur.get(sp, 0) + d
        
        dom_speaker = max(speaker_dur, key=speaker_dur.get)
        dom_frac = speaker_dur[dom_speaker] / sum(speaker_dur.values())
        
        if dom_frac >= merge_threshold and dom_speaker != 'UNKNOWN':
            # Merge all into one block with dominant speaker
            merged = {
                'speaker_id': dom_speaker,
                'start': cluster[0]['start'],
                'end': cluster[-1]['end'],
                'words': [],
            }
            for cb in cluster:
                merged['words'].extend(cb['words'])
            cleaned.append(merged)
        else:
            # Keep as separate, defer to review
            for cb in cluster:
                cb['review_reason'] = 'microblock_deferred'
                cleaned.append(cb)
        
        i = j
    
    return cleaned
```

### Priority 2: Speaker Clustering / Reducing pyannote Speakers

pyannote produces 34 speakers for a 9-person meeting. Some of these are the same person fragmented across multiple IDs.

**Approach:** Cluster pyannote speaker IDs using voice embeddings:
1. Extract embeddings for each pyannote speaker segment using `wespeaker-voxceleb-resnet34-LM` (already used by pyannote)
2. Cluster embeddings to identify unique speakers
3. Map pyannote IDs → canonical speaker IDs before merge

This can reduce 34 → ~10-15 unique speakers, making manual mapping more tractable.

### Priority 3: Known Official Safe Mapping

Currently the merge applies `speaker_map` from corrections, then falls back to registry. A better approach:
1. After merge, run a text-based name-spotter against known official names
2. If a block contains "Mayor Read" or "Councilmember Peterson" and the diarization confidence is low, flag for safe-upgrade rather than UNKNOWN
3. Only promote if name appears verbatim in the ASR text

---

## 6. Speaker Registry Design

Existing: `speaker_registry/speakers.json` (schema: `fairfax.speaker_registry.v1`)

**Proposed enhancements:**

```json
{
  "schema": "fairfax.speaker_registry.v2",
  "speakers": [
    {
      "speaker_key": "council_tom_peterson",
      "display_name": "Councilmember Tom Peterson",
      "role": "council",
      "confidence_boost": 0.95,
      "min_diarization_confidence": 0.5,
      "aliases": ["Tom Peterson", "Councilmember Peterson", "Peterson"],
      "diarization_speaker_ids": ["SPEAKER_30"],
      "text_patterns": ["Councilmember Peterson", "Mr. Peterson"]
    }
  ]
}
```

New fields:
- `confidence_boost`: default 0.95 for named officials
- `min_diarization_confidence`: minimum pyannote confidence to auto-assign
- `diarization_speaker_ids`: known pyannote speaker IDs for this person
- `text_patterns`: name patterns to spot in ASR text for safe upgrade

---

## 7. Correction Layer Design

Existing: `corrections/<meeting_id>.json` with `speaker_map` and `text_correct` per meeting.

**Proposed enhancement:**

```json
{
  "schema": "fairfax.corrections.v2",
  "meeting_id": "apr-14-2026",
  "speaker_map": {
    "SPEAKER_21": {
      "speaker_key": "mayor_catherine_read",
      "confidence": 0.95,
      "reason": "video_frame_6899s_nameplate"
    }
  },
  "text_correct": {
    "turn_000218": {
      "corrected_text": "Is there a second?",
      "reason": "Caption/video cross-check — 'Second' is a separate turn"
    }
  },
  "suppress": ["turn_000101", "turn_000102"],
  "speaker_merge": {
    "SPEAKER_06": "SPEAKER_30"
  },
  "metadata": {
    "corrections_applied_at": "2026-04-22T00:00:00Z",
    "corrections_applied_by": "pipeline_v2"
  }
}
```

New fields:
- `speaker_merge`: merge two pyannote IDs (for speaker fragmentation)
- `text_correct`: per-turn text corrections
- `suppress`: turn IDs to suppress
- `metadata`: audit trail for automated corrections

---

## 8. Sample Output — Structured Transcript (post-merge, post-cleanup)

```json
{
  "meeting_id": "apr-14-2026",
  "schema": "fairfax.structured_transcript.v2",
  "asr": {
    "engine": "faster-whisper",
    "model": "medium",
    "language": "en",
    "device": "cuda",
    "duration_seconds": 10021.5,
    "words": 24612
  },
  "diarization": {
    "engine": "pyannote.audio",
    "version": "3.1",
    "segments": 1721,
    "unique_speakers_before_merge": 34
  },
  "merge": {
    "total_segments": 572,
    "unknown_segments": 114,
    "cleanup_pass": "microblock_v1"
  },
  "turns": [
    {
      "turn_id": "turn_000001",
      "start": 72.61,
      "end": 85.83,
      "timestamp_label": "00:01:12",
      "speaker_id": "SPEAKER_21",
      "speaker_name": "Mayor Catherine Read",
      "speaker_role": "mayor",
      "speaker_confidence": 0.95,
      "text": "Good evening. I would like to call the regular meeting of April 14th, 2026 to order...",
      "needs_review": false,
      "review_reason": "named_official_verified"
    },
    {
      "turn_id": "turn_000002",
      "start": 85.83,
      "end": 89.82,
      "timestamp_label": "00:01:25",
      "speaker_id": "UNKNOWN",
      "speaker_name": "Unknown Speaker",
      "speaker_role": "unknown",
      "speaker_confidence": 0.0,
      "text": "I",
      "needs_review": true,
      "review_reason": "microblock_deferred"
    }
  ]
}
```

---

## 9. Docker / Compose Setup

### docker-compose.yml additions

```yaml
services:
  microblocks:
    build:
      context: ${FAIRFAX_REPO}
      dockerfile: pipeline/docker/microblocks/Dockerfile
    volumes:
      - ${WORK_ROOT}:/work
    working_dir: /work
```

### New microblocks Dockerfile

```dockerfile
FROM python:3.12-slim

RUN python -m pip install --no-cache-dir -U pip

WORKDIR /work

COPY pipeline/src /app/src
ENV PYTHONPATH=/app

ENTRYPOINT ["python", "-m", "src.cleanup_blocks"]
```

---

## 10. Exact Run Commands

```bash
# On Juggernaut
WORK_ROOT="/mnt/disk1/fairfax-phase1/work"
MEETING_ID="apr-14-2026"
REPO="$HOME/.openclaw/workspace/fairfax-council-transcripts"

cd $REPO

# --- Full pipeline (idempotent) ---

# 1. Ingest / extract audio
python3 scripts/phase1_ingest.py \
  "https://fairfax.granicus.com/player/clip/4519" \
  --meeting-id $MEETING_ID \
  --work-root $WORK_ROOT \
  --format audio

# 2. Normalize audio (ensures 16k mono WAV)
python3 scripts/phase1_normalize_audio.py \
  --meeting-id $MEETING_ID \
  --work-root $WORK_ROOT

# 3. Run full pipeline (ASR + diarization + merge)
python3 scripts/run_phase1_local_pipeline.py $MEETING_ID \
  --work-root $WORK_ROOT \
  --hf-token-file ~/secrets/hf_token.txt

# --- Individual stages (for debugging) ---

# ASR only
docker run --rm --gpus all \
  -v $WORK_ROOT:/work \
  -w /work \
  fairfax-pipeline-asr_faster_whisper:latest \
  --model medium \
  --out $MEETING_ID/asr/faster-whisper.json

# Diarization only  
docker run --rm --gpus all \
  -v $WORK_ROOT:/work \
  -e HF_HOME=/work/.hf_cache \
  fairfax-pipeline-diarize_pyannote:latest \
  $MEETING_ID/audio/audio_16k_mono.wav \
  --token-file ~/secrets/hf_token.txt \
  --out $MEETING_ID/diarization/pyannote_segments.json

# Merge + microblock cleanup
python3 -m pipeline.src.cleanup_blocks \
  --merged $MEETING_ID/merged/segments.json \
  --out $MEETING_ID/merged/segments_clean.json

# --- Apply review decisions ---
python3 scripts/apply_review_decisions.py $MEETING_ID \
  --structured transcripts_structured/$MEETING_ID.json \
  --decisions reviews/$MEETING_ID-review-decisions.json

# --- Publish ---
python3 scripts/publish_structured_meeting.py $MEETING_ID \
  --structured transcripts_structured/$MEETING_ID.json

python3 scripts/build_search_index.py --meeting-id $MEETING_ID \
  --structured transcripts_structured/$MEETING_ID.json \
  --out docs/js/search-index.js

python3 scripts/validate_site.py --meeting-id $MEETING_ID
```

---

## 11. Publish Integration

```
Structured JSON (transcripts_structured/<id>.json)
       │
       ├──► publish_structured_meeting.py
       │         │
       │         ├──► docs/transcripts/<id>.html
       │         └──► docs/transcripts/<id>-data.js
       │
       ├──► build_search_index.py
       │         │
       │         └──► docs/js/search-index.js
       │
       └──► validate_site.py
                  │
                  └──► [commit + push to GitHub Pages]
```

The pipeline is write-once: structured JSON is the source of truth, all public output is derived from it deterministically.

---

## 12. Confidence Threshold Recommendations

| Speaker Type | Min Confidence | Notes |
|-------------|----------------|-------|
| Named officials (council/staff) | 0.50 | With text pattern match + speaker registry |
| Public commenters | 0.80 | Require strong diarization confidence |
| Procedural / transitional | any | Always needs_review unless trivially identified |

---

## 13. What Still Sucks

1. **pyannote over-segmentation** — 34 speakers for 9 people. The micro-block post-processor helps but doesn't fix root cause.
2. **WhisperX diarization blocked** — gated HF model needs token. Not a blocker for production, but limits testing.
3. **No speaker embedding clustering** — pyannote IDs for the same person are not merged automatically.
4. **Correction workflow is still manual** — the review UI helps but review decisions still need to be merged by hand.
5. **No cost tracking** — this is free on self-hosted GPU, which is correct for now but worth monitoring.

---

## 14. Decision: Best Stack Recommendation

**Primary:** `faster-whisper (medium) + pyannote 3.1 + micro-block post-processor`

**Why:**
- ASR quality of faster-whisper medium is excellent (24k words, accurate)
- pyannote diarization is the best open-source option; over-segmentation is addressable via post-processing
- All on Juggernaut with GTX 1650 SUPER — zero API cost
- Word-level timestamps enable precise merge
- Existing Docker images are production-ready

**When to add WhisperX:**
- When WhisperX's alignment+diarization pipeline is validated and the HF token issue is resolved
- WhisperX has better handling of overlapping speech (diarization is joint with ASR, not post-hoc)
- Current barrier: gated pyannote community model + 20GB image

**Never use (for this use case):**
- OpenAI Whisper API — cost + no GPU control + no word timestamps
- AssemblyAI — cost + no local control
- Manual transcription only — not scalable

---

## 15. Files Changed (by this architecture pass)

No files changed yet — this is the architecture note for the next implementation pass.

Planned changes:
| File | Change |
|------|--------|
| `pipeline/src/cleanup_blocks.py` | NEW: micro-block post-processor |
| `pipeline/src/merge_transcript.py` | Add micro-block cleanup pass, speaker registry v2 integration |
| `pipeline/docker/microblocks/Dockerfile` | NEW |
| `pipeline/compose.yml` | Add microblocks service |
| `speaker_registry/speakers.json` | Add v2 fields: confidence_boost, min_diarization_confidence, diarization_speaker_ids, text_patterns |
| `corrections/README.md` | Update to v2 schema |
| `RUNBOOK.md` | Document microblock cleanup stage |

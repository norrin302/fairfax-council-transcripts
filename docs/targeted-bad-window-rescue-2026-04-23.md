# Targeted Bad-Window Rescue Design
**Date:** 2026-04-23  
**Scope:** Bounded rescue experiments for specific known-bad windows, not global pipeline changes

---

## Principle

Do not attempt another global architecture change. The 38→38 (centroid) and 20→18 (per-segment) experiments confirm that the remaining errors are not clustering problems.

The dominant failure is a **diarization accuracy problem**: pyannote assigns the wrong speaker ID in specific time windows, and no post-hoc clustering can fix a wrong diarization assignment.

The rescue strategy is therefore **not** "fix clustering" — it is "fix diarization for the specific windows where it fails."

---

## Identified Bad Windows

### apr-14-2026: ex_003 Window (1650-1850s)

**Problem:** pyannote assigns SPEAKER_24 when it should be SPEAKER_21 (Mayor Catherine Read)

**Affected turns:** ~7 gold set wrong attributions (all in this window)

**Root cause:** Diarization assigns SPEAKER_24 during a continuous Mayor speech stretch. SPEAKER_24 should be mapped to Mayor Read in this window only, or the diarization itself needs to be corrected for this window.

**Why clustering can't help:** Per-segment embeddings for SPEAKER_24 segments reflect whoever pyannote thought was speaking. The embedding of a SPEAKER_24 segment at t=1655s will look like Mayor Read's voice if pyannote made a mistake — not like a different person's voice. Clustering can't distinguish "pyannote made a mistake" from "pyannote was correct."

### Pattern for Future Meetings

The ex_003 pattern is:
1. Mayor or a councilmember gives a long continuous statement (>30s)
2. pyannote fragments their speech across 3+ different speaker IDs
3. One of those IDs is wrong (SPEAKER_24 in ex_003)
4. Registry correctly maps the wrong ID to the wrong person

This pattern appears in:
- Agenda adoption sections
- Proclamation readings
- Vote-call roll calls
- Any extended official statement

---

## Rescue Approaches (Bounded)

### Approach A: Window-Isolated Diarization Re-Run

**Concept:** For a known-bad window, extract just that audio segment, re-run pyannote with tighter parameters, compare.

**Steps:**
1. Isolate the bad window audio (e.g., 1650-1850s from the 10min clip)
2. Re-run diarization with `max_speakers=2` or stricter overlap handling
3. Compare the re-run output to the original diarization
4. If the re-run correctly assigns SPEAKER_21 instead of SPEAKER_24, update the meeting's diarization file for just those segments

**Pros:** Addresses the root cause  
**Cons:** Requires audio extraction + re-run for each bad window; must be validated manually

**Implementation:**
```bash
# Extract window audio
ffmpeg -i audio_16k_mono.wav -ss 1650 -to 1850 -c copy window_1650_1850.wav

# Re-run diarization on window
docker run --rm --gpus all \
  -v /work:/work \
  fairfax-pipeline-diarize_pyannote \
  /work/window_1650_1850.wav \
  --max-speakers 2 \
  --out /work/window_diar.json
```

### Approach B: Registry Override for Specific Time Windows

**Concept:** Add a time-window-specific override to the meeting's corrections file.

**Steps:**
1. Identify the bad window time range
2. Add a `window_speaker_override` to the corrections file
3. Apply corrections during merge, before registry lookup

**Schema:**
```json
{
  "meeting_id": "apr-14-2026",
  "window_speaker_override": [
    {
      "start": 1650,
      "end": 1850,
      "source_speaker": "SPEAKER_24",
      "target_speaker": "SPEAKER_21",
      "reason": "Mayor continuous speech — pyannote misassigned SPEAKER_24",
      "validation": "manual_audio_review"
    }
  ]
}
```

**Pros:** No re-run needed, deterministic  
**Cons:** Manual identification required, not generalizable

### Approach C: Short-Audio Diarization Quality Check

**Concept:** Run a short-audio diarization accuracy check as a diagnostic after each meeting's main run. Report which windows have high speaker-ID churn (many different IDs in a short window, suggesting fragmentation).

**Implementation:**
```python
def detect_bad_windows(diar_segments, window_size=60, churn_threshold=5):
    """Detect windows with abnormal speaker ID churn."""
    from collections import Counter
    bad_windows = []
    for start in range(0, int(max(d["end"] for d in diar_segments)), window_size):
        window_segs = [d for d in diar_segments if d["start"] < start+window_size and d["end"] > start]
        speakers = set(d["speaker"] for d in window_segs)
        if len(speakers) >= churn_threshold:
            bad_windows.append({"start": start, "end": start+window_size, "n_speakers": len(speakers)})
    return bad_windows
```

Output: list of bad windows for human review, passed to `build_review_queue.py` for priority tiering.

---

## Recommended Approach

**Phase 1: Approach B (Registry Override)** is the most practical for apr-14-2026.

**Phase 2: Approach C (Bad Window Detection)** should be built into the pipeline to identify future bad windows automatically.

**Phase 3: Approach A (Window Re-Run)** is the fallback for meetings where manual window overrides aren't sufficient.

---

## Scope Constraints

- **No global architecture changes**
- **No new clustering experiments**
- **No WhisperX integration in this phase**
- **No new Docker images** unless Approach A shows consistent value
- Each bad window rescue must be: isolated, validated, and documented before adoption

---

## Deliverables

1. `corrections/apr-14-2026.json` — add window overrides for ex_003
2. `pipeline/src/detect_bad_windows.py` — new diagnostic script (Approach C)
3. `docs/rescue-results-2026-04-23.md` — results of any rescue experiments run

---

## Kill Criteria

If Approach A (re-run) doesn't produce materially better diarization for the ex_003 window, the rescue path is abandoned for this meeting.

If Approach B (window override) produces a correct result for ex_003, it becomes the standard pattern for similar windows in future meetings.

If Approach C (detection) finds >3 bad windows in apr-14-2026 or >5 in any future meeting, escalate to Russ for a decision about whether the baseline pyannote parameters need adjustment.

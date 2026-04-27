# Fairfax Council Transcripts — Speaker Verification Pipeline

## Overview

This document describes the post-pipeline verification workflow that improves speaker accuracy from ~91-95% (hybrid pipeline output) to ~97-99% through targeted video verification.

**Status:** Verified on apr-14-2026. Ready for apr-07-2026 and future meetings.

---

## The Problem

The hybrid pipeline (AssemblyAI + Granicus VTT + text heuristics) achieves 91-95% speaker accuracy but makes systematic errors in specific scenarios:

1. **Council members speaking from seats** — during proclamations, Peterson/Levy etc. may speak from the dais while someone else is at the podium. ASR captures both; Granicus labels only the podium speaker.

2. **Mayor announcing public commenters** — the mayor's introduction ("Our next speaker is Kevin Anderson") gets merged into the public commenter's turn. The pipeline labels it as a council member based on text content heuristics.

3. **ASR fragmentation at turn boundaries** — short (< 5 char) fragments at the start/end of turns get assigned to the wrong speaker.

4. **Roll-call vote fragments** — single-word utterances ("Aye", "Yes", "Motion passed") during roll calls are genuinely ambiguous.

---

## The Verification Workflow

### Step 1: Generate the Hybrid Transcript

```bash
# On Juggernaut
cd /mnt/disk1/fairfax-council-transcripts/pipeline
python3 run_hybrid_v2.py --date YYYY-MM-DD
```

Output: `docs/transcripts/YYYY-MM-DD-data.js`

### Step 2: Run Automated Checks

Before touching the video, run pattern-based scans to catch obvious errors:

```python
# Pattern 1: Self-identification statements
for each turn:
    if "my name is" in text_lower:
        → Flag for speaker correction
        → The named person IS the speaker, not the labeled council member

# Pattern 2: Mayor introducing next speaker
for each turn:
    if "our next speaker is" in text_lower OR "next speaker is" in text_lower:
        → This turn may contain the mayor's announcement
        → The ACTUAL speaker starts their turn AFTER this one

# Pattern 3: Specific role statements
for each turn where speaker is council member:
    if any(role_pattern in text_lower for role_pattern in [
        'i live at', 'i reside', 'i have lived',
        'i am here tonight', 'i am speaking as a',
        'i serve on the', 'i want to thank',
    ]):
        → Flag as likely public commenter, not council member

# Pattern 4: Very short turns at boundaries
for each turn:
    if len(text.strip()) < 5 AND start is near known event boundary:
        → Check if this is a fragment of adjacent speech
```

### Step 3: Video Verification (Tandem Browser)

For each flagged turn, use Tandem Browser to watch the Granicus player at the relevant timestamp.

**Tandem setup:**
```bash
API="http://127.0.0.1:8765"
TOKEN="$(cat ~/.tandem/api-token)"
AUTH_HEADER="Authorization: Bearer $TOKEN"
```

**Open video at specific timestamp:**
```bash
curl -sS -X POST "$API/tabs/open" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://fairfax.granicus.com/player/clip/CLIP_ID?entrytime=SECONDS","focus":true,"source":"wingman"}'
```

**Navigate to timestamp:**
```bash
curl -sS -X POST "$API/execute-js" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"code":"var v = document.querySelector(\"video\"); if(v){v.currentTime=SECONDS;}}'
```

**Take screenshot:**
```bash
curl -sS "$API/screenshot" -H "$AUTH_HEADER" -o /tmp/vid_TIMESTAMP.png
```

**Watch the video for 10-20 seconds around the timestamp** — pay attention to:
- Who is physically at the podium/microphone
- Whether council members are speaking from their seats
- Whether the mayor is making announcements vs someone else speaking

### Step 4: Cross-reference with Granicus VTT

Download the Granicus VTT to see the original speaker labels:
```python
url = f"https://fairfax.granicus.com/vienna_download.php?video_id={clip_id}&content_id=1&download=1"
# Parse VTT: speaker label is embedded in text field as ">> speaker_name."
```

VTT timestamps are in **milliseconds** and may have ~15-20 second offset from video playback — use text content, not speaker labels, for mapping.

### Step 5: Apply Corrections

Corrections are applied directly to `docs/transcripts/YYYY-MM-DD-data.js`:
```python
d[turn_index]['speaker'] = 'Correct Speaker Name'
```

Then commit and push:
```bash
git add docs/transcripts/YYYY-MM-DD-data.js
git commit -m "fix: N speaker corrections from video verification"
git push
```

---

## apr-14-2026 Corrections Applied

| Turn | Timestamp | Was | Fixed to | Verification |
|------|-----------|-----|----------|-------------|
| 1 | 94s | Tom Peterson | Mayor Catherine Read | Video: podium empty, everyone standing (Pledge) |
| 3 | 264s | Tom Peterson | Suzanne Levy | Video: woman at podium (Levy), Peterson at dais |
| 60 | 1687s | Anthony Amos | Anita Light | VTT: "My name is Anita Light" |
| 64 | 1888s | Anthony Amos | Kevin Anderson | VTT: mayor announces Kevin Anderson |
| 65 | 2115s | Stacy Hall | Douglas Stewart | VTT: self-introduction confirms |
| 66 | 2260s | Tom Peterson | Janet Jaworski | VTT: mayor announces Jan Jaworski |
| 70 | 2462s | Tom Peterson | Janice Miller | VTT: "My name is Janice Miller" |
| 75 | 2840s | Stacy Hall | Becky Rager | VTT: "My name is Becky Rager" |
| 81 | 3206s | Anthony Amos | William Pitchford | VTT: "My name is William Pitchford" |
| 82 | 3435s | Tom Peterson | Toby Sorenson | VTT: mayor announces; self-intro confirms |
| 175 | 4799s | Billy Bates | Douglas Stewart | VTT: self-introduction confirms |
| 177 | 4952s | Stacy Hall | Jennifer Rose | VTT: "Jennifer Rose, Executive Director" |

---

## Key Learnings

### ASR captures all voices, Granicus labels only podium speaker
During proclamations, council members often speak from the dais while visitors stand at the podium. ASR picks up both. Granicus VTT only labels who's at the microphone. The pipeline mapped text→council member but missed that the actual podium speaker was someone else.

**Fix:** When text content mentions board roles / self-identifies as council, check if someone else is at the podium in the video.

### Mayor announcements get merged into public commenter turns
The mayor introducing a speaker ("Our next speaker is Kevin Anderson") happens right before the commenter starts speaking. ASR sometimes merges them into one turn. The pipeline saw council-member-sounding text and assigned the label accordingly.

**Fix:** "Our next speaker is [Name]" at the start of a turn → the NEXT turn belongs to Name, not the current one. Self-introduction ("My name is X") confirms the speaker.

### Short fragments at turn boundaries
Turns < 5 characters at event boundaries (pledge, roll call, proclamation handoff) are usually ASR splitting artifacts.

**Fix:** Check if adjacent turns form a complete sentence when merged. The shorter turn probably has the wrong label.

### Video verification is definitive
For any disputed turn, 20-30 seconds of video observation resolves it definitively. Tandem Browser makes this systematic.

---

## Granicus Clip IDs (Reference)

| Meeting | Clip ID | Date |
|---------|---------|------|
| jan-06-2026 | 4432 | 2026-01-06 |
| jan-13-2026 | 4436 | 2026-01-13 |
| feb-03-2026 | 4456 | 2026-02-03 |
| feb-10-2026 | 4463 | 2026-02-10 |
| feb-17-2026 | 4468 | 2026-02-17 |
| feb-24-2026 | 4474 | 2026-02-24 |
| mar-03-2026 | 4489 | 2026-03-03 |
| mar-10-2026 | 4494 | 2026-03-10 |
| mar-24-2026 | 4504 | 2026-03-24 |
| apr-07-2026 | 4513 | 2026-04-07 |
| apr-14-2026 | 4519 | 2026-04-14 |

Video URL pattern: `https://fairfax.granicus.com/player/clip/CLIP_ID?entrytime=SECONDS`

---

## Files Modified During Verification

| File | Purpose |
|------|---------|
| `docs/transcripts/YYYY-MM-DD-data.js` | Speaker corrections |
| `docs/js/transcript-page.js` | Timestamp display fix (ms→sec) |
| `docs/js/review-ui.js` | Timestamp display fix (ms→sec) |
| `docs/js/search-index.js` | Duration field fix |

---

## Future Meetings Checklist

- [ ] Run `run_hybrid_v2.py` pipeline
- [ ] Run automated self-identification scan (`"my name is"` pattern)
- [ ] Run automated mayor-announcement scan (`"our next speaker"` pattern)
- [ ] Run automated public-comment-phrase scan
- [ ] For each flagged turn: open video in Tandem at `entrytime=SECONDS`
- [ ] Watch 10-20s of video around the timestamp
- [ ] Cross-reference with Granicus VTT speaker labels
- [ ] Apply corrections to data file
- [ ] Commit and push
- [ ] Verify site updated: https://norrin302.github.io/fairfax-council-transcripts/

# Review Prioritization Plan
**Date:** 2026-04-23  
**Purpose:** Focus manual review on highest-risk segments first, rather than broad linear passes.

---

## The Problem with Unstructured Review

Current review queue (`build_review_queue.py`) generates all unresolved/mixed/short-unknown blocks in document order. For a 2h 47m meeting this creates hundreds of review items, most of which are low-risk (procedural noise, public comment blocks that should stay unknown, micro-block fragments).

Reviewers end up spending most of their time on low-risk items before reaching the high-risk sections that actually affect transcript quality.

---

## Prioritization Tiers

### Tier 1 — High Risk (Review First)

Segments that are:
- In **known-bad meeting windows** (ex_003 pattern, ~1650-1850s, or similar dais-transition windows in future meetings)
- Involve **named officials/staff** where attribution matters — councilmembers, Mayor, staff presenting agenda items
- Have **rapid speaker changes** — 3+ different speakers within 30 seconds (dais debate, vote calls)
- Have `review_reason` flags: `diarization_conflict`, `speaker_reassigned`, `overlap_segment`
- Have **procedural vote-call patterns** — roll calls, motion seconds, procedural acknowledgments

**Why:** These are the segments most likely to be wrong attributions that affect the public record. ex_003 errors are all in this category.

### Tier 2 — Medium Risk

Segments that are:
- Public commenters with usable text content (not just 1-3 word fragments)
- Mixed speaker segments marked `needs_review`
- Any segment with `speaker_status: mixed`

**Why:** These affect completeness and readability. Wrong name assignment here is embarrassing but fixable.

### Tier 3 — Low Risk (Review Last or Skip)

Segments that are:
- Very short (< 3 words) unknown blocks in procedural sections (Pledge, welcome, sign-offs)
- Single-word microblocks from speaker transitions
- Blocks that are `speaker_status: unknown` with no useful text

**Why:** These are noise from diarization artifacts. Conservative handling (keep unknown or suppress) is the correct choice, and spending review time on them is low ROI.

---

## Implementation

### Enhanced `build_review_queue.py` with Priority Tiers

```python
def classify_priority(turn, context_windows=None):
    """Assign review priority tier to a turn."""
    status = turn.get("speaker_status", "")
    reason = turn.get("review_reason", "")
    text = turn.get("text", "")
    words = text.split()
    start = turn.get("start", 0)
    speaker = turn.get("speaker_raw", "")

    # Tier 1 signals
    if reason in ("diarization_conflict", "speaker_reassigned", "overlap_segment"):
        return 1
    if status == "mixed":
        return 1
    if context_windows:
        for win in context_windows:
            if win["start"] <= start <= win["end"]:
                return 1
    # Named officials in rapid-change windows
    if speaker in KNOWN_OFFICIAL_IDS and _has_rapid_speaker_changes(turn, context_window=30):
        return 1
    # Vote-call procedural patterns
    if any(kw in text.lower() for kw in ["motion", "second", "roll call", "councilmember", "aye", "nay"]):
        if len(words) > 3:
            return 1

    # Tier 2 signals
    if status in ("unknown", "unresolved"):
        if len(words) >= 3:
            return 2
    if status == "public_comment_unverified":
        return 2

    # Tier 3 — everything else
    return 3
```

### Known-Bad Window Registry

```python
# For apr-14-2026
KNOWN_BAD_WINDOWS = [
    {"start": 1650, "end": 1850, "label": "ex_003_agenda_adoption"},
    # Add future known-bad windows here as they're identified
]
```

### Output Format

Updated review queue JSON with `review_priority` field:

```json
{
  "items": [
    {
      "turn_id": "...",
      "review_priority": 1,
      "priority_reason": "known_bad_window_ex003",
      ...
    }
  ]
}
```

Review UI (`review-ui.js`) sorts/colors by priority tier.

---

## Review UI Enhancement

Add priority tier badges to the review cockpit:

| Tier | Badge | Color | Label |
|------|-------|-------|-------|
| 1 | 🔴 | Red | High Risk — Review First |
| 2 | 🟡 | Yellow | Medium Risk |
| 3 | 🟢 | Green | Low Risk — Review Last |

Sort default view by `review_priority` ascending (tier 1 first).

---

## Adoption Path

1. Add `review_priority` field to `build_review_queue.py` (small change)
2. Add KNOWN_BAD_WINDOWS config to the script
3. Sort review queue output by priority tier
4. Update REVIEW_WORKFLOW.md to document prioritization
5. No changes to apply pipeline

No changes to structured transcript JSON schema — priority is a review-queue concern only.

---

## Metrics

Track priority tier distribution to calibrate future tuning:

```
python3 scripts/build_review_queue.py apr-14-2026 --structured transcripts_structured/apr-14-2026.json --out reviews/apr-14-2026-review-queue.json
# → log: "Tier 1: N, Tier 2: M, Tier 3: K"
```

Target: ≥60% of review time should be spent on Tier 1 segments after prioritization is adopted.

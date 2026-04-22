# Review Mode — Speaker Labeling

## Overview

Review mode adds a **Label speaker** button to each unlabeled speaker block on the transcript page. Authorized reviewers can use it to submit a speaker label that is written to the review decisions artifact and applied through the existing pipeline.

**Key constraints:**
- Review mode is NOT public editing — it requires `?review=1` in the URL
- Decisions write to localStorage (staging) first, then to `reviews/<meeting>-review-decisions.json` via the existing apply pipeline
- Public output is always generated from structured data, never directly edited

---

## Enabling Review Mode

Add `?review=1` to any transcript page URL:

```
https://norrin302.github.io/fairfax-council-transcripts/transcripts/apr-14-2026.html?review=1
```

A purple banner appears at the top confirming review mode is active:

> **Review mode active — unlabeled turns can be labeled** | Exit review mode

Unlabeled turns (marked with `unlabeled` badge) receive a **Label speaker** button in their header row.

---

## Labeling a Turn

### Step 1 — Open the form

Click **Label speaker** on any unlabeled block. A modal appears.

### Step 2 — Fill in the form

| Field | Description |
|-------|-------------|
| **Speaker name** | Free text. Use quick-pick buttons for known council/staff names. |
| **Speaker type** | `Council / Mayor` → `approve_named_official`; `Staff` → `approve_named_official`; `Public Comment` → `mark_public_comment`; `Keep unknown` → `keep_unknown` |
| **Apply to** | Currently: **This turn only** (other scopes require manual JSON editing) |
| **Evidence / notes** | **Required** for any named label. Describe the evidence — video timestamp, adjacent speaker context, etc. |

### Step 3 — Save

Click **Save decision**. The decision JSON is:
1. Written to localStorage (`reviewdecisions:pending:<meeting_id>`)
2. Displayed in the modal for copy/paste
3. Applied instructions shown in the modal

A "X pending decision(s)" badge appears in the review banner.

---

## Applying Saved Decisions

Decisions are staged in localStorage. To apply them:

### Option A — Copy individual decisions into the JSON artifact

1. Click **Copy JSON** in the modal for each decision
2. Open `reviews/apr-14-2026-review-decisions.json`
3. Find the `decisions` array
4. Paste the decision object(s) into the array
5. Deduplicate by `turn_id` (earlier decision for same turn_id wins)

### Option B — Bulk apply from localStorage (developer)

Run the apply script:

```bash
cd fairfax-council-transcripts

# Show pending decisions
python3 - << 'PY'
import json, localStorage
# (manual step - paste into apply script)
PY

# Apply to structured transcript
python3 scripts/apply_review_decisions.py apr-14-2026

# Republish meeting
python3 scripts/publish_structured_meeting.py apr-14-2026

# Rebuild search index
python3 scripts/build_search_index.py --meeting-id apr-14-2026 \
  --structured transcripts_structured/apr-14-2026.json \
  --out docs/js/search-index.js

# Validate
cd docs && python3 ../scripts/validate_site.py --meeting-id apr-14-2026
```

### Option C — One-click path (demo on apr-14-2026)

See the **Demo** section below.

---

## Supported Reviewer Actions

| Action | speaker_type | reviewer_action |
|--------|-------------|----------------|
| Label council/mayor | `council` | `approve_named_official` |
| Label staff | `staff` | `approve_named_official` |
| Label public commenter | `public_comment` | `mark_public_comment` |
| Keep unknown | `unknown` | `keep_unknown` |

Text corrections, suppression, and hold-back are currently via manual JSON edit.

---

## Scope Limitations

- Default scope is **this turn only**
- Contiguous block and same-raw-speaker cluster application require manual JSON editing of the decisions array
- No segmentation changes from this UI

---

## Data Flow

```
[Label Speaker UI]
    ↓ (Save)
[localStorage: reviewdecisions:pending:<meeting_id>]
    ↓ (copy JSON manually)
[reviews/<meeting>-review-decisions.json — decisions[]]
    ↓ (apply_review_decisions.py)
[transcripts_structured/<meeting>.json — updated speakers]
    ↓ (publish_structured_meeting.py)
[docs/transcripts/<meeting>-data.js — public output]
[docs/transcripts/<meeting>.html — re-rendered]
```

---

## Demo — apr-14-2026

**URL:** `https://norrin302.github.io/fairfax-council-transcripts/transcripts/apr-14-2026.html?review=1`

1. Open the URL above
2. Find an `unlabeled` speaker block (look for the purple "unlabeled" badge)
3. Click **Label speaker**
4. Select a quick-pick name (e.g., `Councilmember Tom Peterson`)
5. Choose type `Council / Mayor`
6. Enter evidence: e.g., `Video frame at 6899s shows CM PETERSON nameplate`
7. Click **Save decision**
8. Copy the displayed JSON
9. Paste into `reviews/apr-14-2026-review-decisions.json` → `decisions` array
10. Run the apply and publish commands above

---

## Files Changed

| File | Change |
|------|--------|
| `docs/js/review-ui.js` | New — review mode UI, modal, pending storage |
| `docs/css/transcript-page.css` | Review banner, label button, modal styles |
| `docs/transcripts/apr-14-2026.html` | Loads `review-ui.js` |
| `docs/REVIEW_WORKFLOW.md` | This documentation |

---

## Security Notes

- Review mode is gated by a URL parameter, not auth — do not share reviewer URLs publicly
- Decisions must go through the artifact pipeline — never written directly to public output
- Evidence notes required for named labels to support future audit trail
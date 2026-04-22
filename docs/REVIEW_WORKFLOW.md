# Review Mode — Speaker Labeling (v2)

## Overview

Review mode is a reviewer cockpit for labeling unlabeled speaker blocks in the transcript. Decisions are staged locally and exported as JSON for insertion into the canonical review artifact, then applied through the existing pipeline.

**Architecture constraints:**
- Review mode is NOT public editing — gated by URL parameter + passphrase
- Decisions write to localStorage first, then to `reviews/<meeting>-review-decisions.json` via the existing apply pipeline
- Public output is always generated from structured data, never directly edited

---

## Enabling Review Mode

**Step 1 — URL parameter:**

Add `?review=1` to any transcript page URL:

```
https://norrin302.github.io/fairfax-council-transcripts/transcripts/apr-14-2026.html?review=1
```

**Step 2 — Passphrase confirmation (v2):**

On first use in a browser session, a small passphrase prompt appears. Enter `review` to confirm. The confirmation is stored in `sessionStorage` for the duration of the browser tab — you won't be prompted again until you close the tab.

---

## The Reviewer Cockpit (v2)

Once review mode is active, the page shows:

1. **Purple review banner** — top of page, confirms review mode is active with meeting ID and staged decision count
2. **Staged Decisions sidebar** — below the banner, lists all decisions staged in the current session
3. **Label speaker buttons** — appear on every unlabeled speaker block

---

## Staging a Label

1. Click **Label speaker** on any unlabeled block (or **Edit label** if already staged)
2. Fill in the modal:
   - **Speaker name** — free text, or use quick-pick buttons for known council/staff names
   - **Speaker type** — Council / Mayor, Staff, Public comment, or Keep unknown
   - **Evidence / notes** — required for any named label; describe the supporting evidence
3. Click **Save decision**
4. The decision appears in the Staged Decisions sidebar

### Quick Actions

Three one-click shortcuts at the top of the modal:
- **Keep unknown** — marks the turn for `keep_unknown`
- **Public comment** — marks as public commenter
- **Suppress turn** — marks for `suppress_turn` with a default note

---

## Staged Decisions Sidebar

Each staged item shows:
- **Turn ID** and **timestamp**
- **Speaker name** applied
- **Action** (Named official / Public comment / Keep unknown / Suppress)
- **Type badge** (Council / Staff / Public / Unknown)
- **Evidence note** (truncated if long)
- **Edit** and **Remove** buttons

Clicking **Edit** reopens the modal pre-populated with the existing decision. Clicking **Remove** deletes the staged decision.

---

## Exporting Staged Decisions

Two export options in the review banner:

- **Copy JSON** — copies the staged decisions JSON to your clipboard, formatted for direct paste into `reviews/<meeting>-review-decisions.json`
- **Export JSON** — downloads a `.json` file named `<meeting>-staged-decisions.json`

The exported JSON is an array of decision objects matching the `decisions[]` schema in the review decisions artifact.

**To merge into the review artifact:**

1. Open `reviews/apr-14-2026-review-decisions.json`
2. Find the `decisions` array
3. Paste the exported JSON into the array (or merge — later entries for the same `turn_id` replace earlier ones)
4. Deduplicate by `turn_id`

---

## Applying and Publishing

```bash
cd fairfax-council-transcripts

# 1. Apply decisions to structured transcript
python3 scripts/apply_review_decisions.py apr-14-2026 \
  --structured transcripts_structured/apr-14-2026.json \
  --decisions reviews/apr-14-2026-review-decisions.json

# 2. Republish meeting (generates public HTML + data.js)
python3 scripts/publish_structured_meeting.py apr-14-2026

# 3. Rebuild search index
python3 scripts/build_search_index.py --meeting-id apr-14-2026 \
  --structured transcripts_structured/apr-14-2026.json \
  --out docs/js/search-index.js

# 4. Validate
cd docs && python3 ../scripts/validate_site.py --meeting-id apr-14-2026
```

---

## Clearing Staged Decisions

Click **Clear all** in the review banner. A confirmation dialog appears before clearing. This removes all staged decisions from localStorage.

---

## Safety Model

- **Gated by URL param + passphrase** — not just a naked `?review=1`
- **No public writeback** — decisions never go directly to public output
- **No GitHub API writeback** — reviewer manually merges into the artifact
- **Evidence notes required** for named labels — no speculative labeling
- **Scope is per-turn only** — no segmentation changes from this UI
- Decisions are in localStorage — they persist across page refreshes but are browser-local

---

## Files Changed (v2)

| File | Change |
|------|--------|
| `docs/js/review-ui.js` | Complete rewrite — staged decisions panel, sidebar, export, passphrase gate, quick actions |
| `docs/css/transcript-page.css` | Banner, sidebar, modal, badge, and quick-action styles |
| `docs/REVIEW_WORKFLOW.md` | Updated to reflect v2 workflow |

---

## Demo

**URL:** `https://norrin302.github.io/fairfax-council-transcripts/transcripts/apr-14-2026.html?review=1`

1. Open the URL above — passphrase prompt appears, enter `review`
2. Purple review banner + Staged Decisions sidebar appear
3. Find an unlabeled block (purple "unlabeled" badge) — click **Label speaker**
4. Quick-pick a name, select type, add evidence note, save
5. Decision appears in sidebar — click **Export JSON** or **Copy JSON**
6. Merge into `reviews/apr-14-2026-review-decisions.json` → run apply/publish commands above
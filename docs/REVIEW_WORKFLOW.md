# Review Mode — Speaker Labeling (v2.1)

## Overview

Review mode is a reviewer cockpit for labeling unlabeled speaker blocks in the transcript. Decisions are staged locally and exported as JSON for insertion into the canonical review artifact, then applied through the existing pipeline.

**Architecture constraints:**
- Review mode is NOT public editing — gated by URL parameter + passphrase
- Decisions write to localStorage first, then to `reviews/<meeting>-review-decisions.json` via the existing apply pipeline
- Public output is always generated from structured data, never directly edited

---

## Security Model (Important — Read This)

**`?review=1` + passphrase is convenience gating, NOT authentication.**

This system is designed to prevent casual or accidental access by people who happen to be using the same browser. It does NOT:
- Authenticate a real user identity
- Protect sensitive data from a determined attacker
- Provide any security boundary against someone who knows the passphrase

If you need real access control, this system must be upgraded with proper auth. For now, treat the passphrase as a soft door latch, not a locked gate.

---

## Enabling Review Mode

**Step 1 — URL parameter:**

```
https://norrin302.github.io/fairfax-council-transcripts/transcripts/apr-14-2026.html?review=1
```

**Step 2 — Passphrase confirmation (v2+):**

On first use in a browser tab, enter `review` when prompted. Confirmation is stored in `sessionStorage` for the tab — you won't be prompted again until you close the tab.

---

## The Reviewer Cockpit (v2.1)

Once active, the page shows:
1. **Purple review banner** — meeting ID, staged decision count, dirty-state indicator, export/copy/clear buttons
2. **Staged Decisions sidebar** — all staged decisions with edit/remove per item, export-status icons
3. **Label speaker buttons** — on every unlabeled block

---

## Staging a Label

1. Click **Label speaker** (or **Edit label** if already staged) on any unlabeled block
2. Fill in the modal:
   - **Speaker name** — free text or quick-pick for known council/staff names
   - **Speaker type** — Council / Mayor, Staff, Public comment, or Keep unknown
   - **Evidence / notes** — required for named labels; full text preserved in export
   - **Reviewer name** — your name or alias for audit traceability; default is `manual-review`
3. Click **Save decision**

### Quick Actions

- **Keep unknown** — sets note to "Reviewer action: keep unknown" if empty, saves immediately
- **Public comment** — checks public type, does NOT auto-save (lets you add evidence first)
- **Suppress turn** — requires note OR a confirm dialog; prevents accidental suppression

### Guardrails on Suppress / Keep Unknown

Both actions now require either:
- A non-empty evidence note, OR
- An explicit confirm dialog if no note is provided

This makes it harder to click through sloppily and damage the audit record.

---

## Staged Decisions Sidebar

Each staged item shows:
- **Turn ID** + timestamp
- **Speaker name** + export-status icon (✓ exported / ○ pending)
- **Action** label + type badge
- **Evidence note** (truncated to 60 chars in sidebar; full text preserved in export)
- **Edit** and **Remove** buttons

Export-status icons let you see at a glance which decisions have already been exported vs. which are still unexported.

---

## Dirty State Indicator

When staged decisions exist but none have been exported yet, the review banner shows:

> ⚠️ unexported

Clicking **Export JSON** or **Copy JSON** clears the dirty state. If you stage new decisions after exporting, the dirty indicator reappears.

**beforeunload warning:** If you have unexported decisions and try to close or navigate away from the tab, the browser will warn you. Export or copy your decisions before leaving.

---

## Exporting Staged Decisions

Two options in the review banner:

- **Copy JSON** — copies the full audit-enriched decision JSON to clipboard
- **Export JSON** — downloads a `.json` file named `<meeting>-staged-decisions.json`

Both include the full audit metadata for each decision. Export format:

```json
{
  "meeting_id": "apr-14-2026",
  "turn_id": "turn_000123",
  "timestamp": 1743201000000,
  "reviewed_at": "2026-04-22T20:30:00.000Z",
  "reviewer": "manual-review",
  "reviewer_action": "approve_named_official",
  "speaker_name": "Councilmember Tom Peterson",
  "speaker_type": "council",
  "evidence_note": "Video frame at 6899s shows CM PETERSON nameplate at dais",
  "speaker_public_override": "Councilmember Tom Peterson",
  "speaker_status_override": "approved",
  "suppress": false,
  "ui_version": "2.1"
}
```

### Merging into the Review Artifact

1. Open `reviews/apr-14-2026-review-decisions.json`
2. Find the `decisions` array
3. Paste the exported decisions into the array (later entry for same `turn_id` replaces earlier)
4. Deduplicate by `turn_id`

---

## Applying and Publishing

```bash
cd fairfax-council-transcripts

# 1. Apply decisions
python3 scripts/apply_review_decisions.py apr-14-2026 \
  --structured transcripts_structured/apr-14-2026.json \
  --decisions reviews/apr-14-2026-review-decisions.json

# 2. Republish meeting
python3 scripts/publish_structured_meeting.py apr-14-2026

# 3. Rebuild search index
python3 scripts/build_search_index.py --meeting-id apr-14-2026 \
  --structured transcripts_structured/apr-14-2026.json \
  --out docs/js/search-index.js

# 4. Validate
cd docs && python3 ../scripts/validate_site.py --meeting-id apr-14-2026
```

---

## Files Changed (v2.1)

| File | Change |
|------|--------|
| `docs/js/review-ui.js` | Audit metadata, reviewer field, export enricher, guardrails, dirty state, beforeunload |
| `docs/css/transcript-page.css` | Export-status icons (✓/○), dirty indicator |
| `docs/REVIEW_WORKFLOW.md` | Updated — security model clarification, guardrails docs, full audit schema |

---

## Export Schema (v2.1)

Every exported decision includes:

| Field | Description |
|-------|-------------|
| `meeting_id` | Meeting ID for context |
| `turn_id` | Turn being labeled |
| `timestamp` | Unix ms when decision was created |
| `reviewed_at` | ISO 8601 timestamp of review |
| `reviewer` | Reviewer name/alias; defaults to `manual-review` |
| `reviewer_action` | Action taken |
| `speaker_name` | Label applied |
| `speaker_type` | `council`, `staff`, `public_comment`, `unknown` |
| `evidence_note` | Full evidence text (not truncated) |
| `speaker_public_override` | Named official override |
| `speaker_status_override` | Status override |
| `suppress` | Boolean |
| `ui_version` | `2.1` |

---

## Demo

**URL:** `https://norrin302.github.io/fairfax-council-transcripts/transcripts/apr-14-2026.html?review=1`
**Passphrase:** `review`
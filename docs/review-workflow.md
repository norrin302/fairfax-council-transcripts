# Speaker Review Workflow

This document describes the end-to-end workflow for reviewing and labeling anonymous or uncertain speaker attributions in a structured transcript, then publishing those decisions.

---

## Overview

The review UI (running at `/review/<meeting_id>`) lets you stage speaker-label decisions without touching the public-facing output. Once you're satisfied with your staged decisions, you export them as a JSON file and apply them to the structured transcript with `apply_review_decisions.py`.

---

## Step 1 — Open the Review UI

Navigate to the review page for the meeting you want to label:

```
http://<your-host>/review/apr-14-2026
```

The page loads the full transcript and highlights turns that need review (those with `speaker_status: "unknown"` or `needs_review: true`).

---

## Step 2 — Label Speakers

For each unlabeled or uncertain turn:

1. Click the turn block to open the speaker-label form.
2. Choose a **reviewer action**:
   - `approve_named` — You've confirmed this speaker's name/role and want to use the exact name you provide.
   - `approve_role` — You've confirmed the speaker's role (e.g., "Councilmember") but not their specific name.
   - `keep_unknown` — You can't confidently identify the speaker; leave them as "Unknown Speaker".
3. Fill in the **speaker name** (for `approve_named` or `approve_role`).
4. Optionally add an **evidence note** explaining why you made this decision (e.g., "Video frame at 6:42 shows nameplate CM PETERSON").
5. Click **Save**. The decision is staged in `localStorage` — it is **not** yet written to any public file.

Repeat for all turns you want to label.

> **Dirty state warning**: If you navigate away from the page with unexported staged decisions, the browser will warn you. Export first, or your staged decisions will be lost.

---

## Step 3 — Export Decisions as JSON

When you've finished labeling for this session:

1. Click the **Export** button in the review sidebar.
2. The browser downloads a file named `<meeting_id>-staged-decisions.json`, e.g.:

```json
[
  {
    "turn_id": "turn_000101",
    "reviewer_action": "approve_named",
    "speaker_name": "Councilmember Tom Peterson",
    "speaker_type": "council",
    "speaker_public_override": "Councilmember Tom Peterson",
    "speaker_status_override": "approved",
    "suppress": false,
    "evidence_note": "Video frame at 6:42 shows nameplate CM PETERSON"
  },
  {
    "turn_id": "turn_000150",
    "reviewer_action": "keep_unknown",
    "speaker_name": "",
    "speaker_type": "unknown",
    "speaker_public_override": "",
    "speaker_status_override": "unknown",
    "suppress": false,
    "evidence_note": "Turn does not self-identify"
  }
]
```

Each export is tagged with a unique `export_batch_id` and `exported_at` timestamp for auditability.

---

## Step 4 — Apply Decisions to the Structured Transcript

On the server (or wherever the repository is checked out):

```bash
cd ~/.openclaw/workspace/fairfax-council-transcripts

python3 scripts/apply_review_decisions.py apr-14-2026 \
  --decisions ~/Downloads/apr-14-2026-staged-decisions.json
```

### Dry Run

To see what would change without writing anything:

```bash
python3 scripts/apply_review_decisions.py apr-14-2026 \
  --decisions ~/Downloads/apr-14-2026-staged-decisions.json \
  --dry-run
```

### What the script does

1. **Reads** `transcripts_structured/<meeting_id>.json`
2. **Matches** each decision by `turn_id`
3. **Updates** the matching turn's `speaker_public`, `speaker_status`, and `review_reason` fields
4. **Writes** the updated structured transcript back to the same file
5. **Republishes** the meeting docs:
   - `docs/transcripts/<meeting_id>-data.js`
   - `docs/transcripts/<meeting_id>.html`
   - `docs/js/search-index.js` (global, rebuilt via `build_search_index.py`)
6. **Prints** a summary: `Applied N decisions: X approved, Y kept unknown, Z suppressed`

### Warnings

- If a `turn_id` in the decisions file doesn't exist in the structured JSON, the script logs a warning and skips it.
- Applying the same decisions file twice is idempotent — it simply overwrites with the same values.

---

## Step 5 — Review and Commit

Inspect the republished output to confirm it looks correct, then commit and push:

```bash
cd ~/.openclaw/workspace/fairfax-council-transcripts

git checkout -b feat/apply-review-decisions
git add transcripts_structured/apr-14-2026.json \
        docs/transcripts/apr-14-2026-data.js \
        docs/transcripts/apr-14-2026.html \
        docs/js/search-index.js
git commit -m "Apply review decisions for apr-14-2026

Reviewed speaker labels via review UI and applied staged decisions.

$(python3 scripts/apply_review_decisions.py apr-14-2026 --decisions ~/Downloads/apr-14-2026-staged-decisions.json --dry-run 2>&1 | tail -1)"

git push origin feat/apply-review-decisions
```

---

## Decision Format Reference

Each entry in the exported JSON has these fields:

| Field | Description |
|-------|-------------|
| `turn_id` | Matches the turn in `transcripts_structured/<meeting_id>.json` |
| `reviewer_action` | One of: `approve_named`, `approve_role`, `keep_unknown` |
| `speaker_name` | Free-text name entered by reviewer |
| `speaker_type` | Speaker category: `council`, `staff`, `public`, `unknown` |
| `speaker_public_override` | Value to write to `speaker_public` field |
| `speaker_status_override` | Value to write to `speaker_status` field (`approved` or `unknown`) |
| `suppress` | `true` to redact the turn entirely (speaker shown as REDACTED) |
| `evidence_note` | Reviewer's justification or notes |

---

## Tips

- **Work in batches**: Stage decisions across multiple sessions; each time you click Export, all pending decisions are included. You don't have to label everything in one sitting.
- **Audit trail**: The `export_batch_id` and `exported_at` fields in each JSON let you trace which export session a decision came from.
- **Review reason format**: The applied `review_reason` field uses the format `reviewed:<reviewer_action> | <evidence_note>`.

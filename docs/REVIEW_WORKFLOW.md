# Review Mode — Speaker Labeling (v2.2)

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

## The Reviewer Cockpit (v2.2)

Once active, the page shows:
1. **Purple review banner** — meeting ID, staged decision count, dirty-state indicator, export/copy/clear buttons
2. **Staged Decisions sidebar** — all staged decisions with edit/remove per item, export-status icons, decision IDs
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

Both actions require either:
- A non-empty evidence note, OR
- An explicit confirm dialog if no note is provided

---

## Staged Decisions Sidebar

Each staged item shows:
- **Turn ID** + timestamp
- **Speaker name** + export-status icon (✓ exported / ○ pending)
- **Action** label + type badge
- **Decision ID** — stable unique ID for this decision, shown in monospace
- **Evidence note** (truncated to 60 chars in sidebar; full text preserved in export)
- **Edit** and **Remove** buttons

---

## Dirty State Indicator

When staged decisions exist but none have been exported yet, the review banner shows:

> ⚠️ **unexported**

Clicking **Export JSON** or **Copy JSON** clears the dirty state. If you stage new decisions after exporting, the dirty indicator reappears.

**beforeunload warning:** If you have unexported decisions and try to close or navigate away from the tab, the browser will warn you. Export or copy your decisions before leaving.

---

## Exporting Staged Decisions

Two options in the review banner:

- **Copy JSON** — copies the full provenance-enriched decision JSON to clipboard
- **Export JSON** — downloads a `.json` file named `<meeting>-staged-decisions.json`

### Export Schema (v2.2)

Every exported decision includes:

| Field | Description |
|-------|-------------|
| `meeting_id` | Meeting ID for context |
| `decision_id` | Stable unique ID for this decision; the same decision exported twice in different batches will have the same `decision_id` |
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
| `ui_version` | `2.2` |
| `exported_at` | ISO 8601 timestamp set at the moment of export |
| `export_batch_id` | Groups all decisions from one export event; changes each time you click Export or Copy JSON |

### How provenance fields work

- **`decision_id`**: Assigned once when you first save a staged decision. Re-editing the same decision does NOT change its `decision_id`. This means the same logical decision can be exported multiple times across different batches and always carries the same ID — useful for deduplication and audit trails.

- **`export_batch_id`**: Changes every time you click Export JSON or Copy JSON. All decisions in one export share the same batch ID. This lets you distinguish between "the same decisions exported twice" (same batch ID) vs. "different review sessions" (different batch IDs).

- **`exported_at`**: The exact moment of export. Allows ordering of exports chronologically even if batch IDs are not globally unique.

### Merging into the Review Artifact

1. Open `reviews/apr-14-2026-review-decisions.json`
2. Find the `decisions` array
3. Paste the exported decisions into the array (later entry for same `turn_id` replaces earlier)
4. Deduplicate by `turn_id`

---

## Apply-Time Provenance (v2.2)

When you run `apply_review_decisions.py`, provenance is recorded automatically:

### 1. In the structured JSON metadata

Each apply run appends one entry to `_review_apply_provenance`:

```json
{
  "_review_apply_provenance": [
    {
      "applied_at": "2026-04-22T21:16:11.913527+00:00",
      "applied_from_decisions_file": "/path/to/apr-14-2026-review-decisions.json",
      "applied_decision_count": 322,
      "applied_decision_ids": ["m1x7f2-9k3pqr", "n2y8g3-lp2stu", ...],
      "applied_export_batch_ids": ["p3z9h4-qr5vwx"],
      "apply_script_version": "2.2"
    }
  ]
}
```

### 2. Sidecar apply report

A dated report is also written to:

```
transcripts_structured/.apply-reports/<meeting_id>-<ISO timestamp>.json
```

Example path:
```
transcripts_structured/.apply-reports/apr-14-2026-20260422T211611Z.json
```

Report contents:
```json
{
  "meeting_id": "apr-14-2026",
  "structured_output": "/path/to/transcripts_structured/apr-14-2026.json",
  "provenance": { ... },
  "decisions_applied": [
    {
      "decision_id": "m1x7f2-9k3pqr",
      "export_batch_id": "p3z9h4-qr5vwx",
      "turn_id": "turn_000342",
      "reviewer_action": "approve_named_official",
      "speaker_name": "JC Martinez"
    },
    ...
  ]
}
```

### Inspecting provenance after the fact

**To see all apply events for a meeting:**
```bash
python3 -c "
import json
d = json.load(open('transcripts_structured/apr-14-2026.json'))
for e in d.get('_review_apply_provenance', []):
    print(e['applied_at'], '-', e['applied_decision_count'], 'decisions from', e['applied_from_decisions_file'].split('/')[-1])
"
```

**To inspect a specific apply report:**
```bash
cat transcripts_structured/.apply-reports/apr-14-2026-20260422T211611Z.json
```

---

## Applying and Publishing

```bash
cd fairfax-council-transcripts

# 1. Apply decisions (v2.2 also writes provenance)
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

## Files Changed (v2.2)

| File | Change |
|------|--------|
| `docs/js/review-ui.js` | `decision_id` (stable, assigned on save), `exported_at` + `export_batch_id` (set at export), sidebar shows decision ID, UI_VERSION → `2.2` |
| `docs/css/transcript-page.css` | `.review-staged-decision-id` style (muted monospace) |
| `scripts/apply_review_decisions.py` | Provenance entry appended to `_review_apply_provenance` in structured JSON; sidecar apply report written to `.apply-reports/` |
| `docs/REVIEW_WORKFLOW.md` | Full provenance docs, schema, how to inspect, sample records |

---

## Backward Compatibility

- v2.1 staged decisions (without `decision_id` / `export_batch_id`) apply correctly — those fields simply won't be present
- The `_review_apply_provenance` array is appended to, never overwritten
- Existing structured JSON files are not modified until the next apply run

---

## Limitations Still Remaining

1. **No GitHub API writeback** — decisions flow through manual JSON editing → apply → republish. Correct for current architecture.

2. **Export deduplication is still manual** — if the reviewer exports twice without clearing, the review decisions file will contain duplicate `turn_id` entries. The docs tell users to deduplicate.

3. **`decision_id` depends on localStorage stability** — if localStorage is cleared between sessions, a re-created decision will get a new `decision_id` even for the same logical decision. For audit use within a single ongoing review session this is fine; for long-term archival, treat `decision_id` as a session-level identifier.

4. **`export_batch_id` is not globally unique** — it's a UUID-style string but not a ULID or timestamp-sortable ID. It identifies batch membership, not global ordering. Use `exported_at` for chronological ordering.

5. **Reviewer field is self-reported** — defaults to `manual-review`. Good enough for a v2.2 audit trail.

---

## Demo

**URL:** `https://norrin302.github.io/fairfax-council-transcripts/transcripts/apr-14-2026.html?review=1`
**Passphrase:** `review`
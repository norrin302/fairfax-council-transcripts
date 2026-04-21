# Review Workflow

Phase 1 keeps the public speaker policy conservative and reviewable.

Use the review artifacts to inspect:
- unresolved speaker turns
- mixed/rejected speaker turns
- questionable ASR wording
- segments that should remain conservative on the public site

## Canonical review artifacts

- `reviews/<meeting_id>-review-queue.json`
- `reviews/<meeting_id>-review-decisions.json`

The queue is generated from the structured transcript.
The decisions file is the human-edited record of reviewer outcomes.

## Generate review queue

```bash
python3 scripts/build_review_queue.py apr-14-2026 \
  --structured transcripts_structured/apr-14-2026.json \
  --out reviews/apr-14-2026-review-queue.json
```

## Export review template

```bash
python3 scripts/export_review_template.py apr-14-2026 \
  --queue reviews/apr-14-2026-review-queue.json \
  --out reviews/apr-14-2026-review-decisions.json
```

## Apply reviewer decisions

```bash
python3 scripts/apply_review_decisions.py apr-14-2026 \
  --structured transcripts_structured/apr-14-2026.json \
  --decisions reviews/apr-14-2026-review-decisions.json

python3 scripts/publish_structured_meeting.py apr-14-2026 \
  --structured transcripts_structured/apr-14-2026.json

python3 scripts/validate_site.py
```

## Allowed reviewer actions

- `keep_unknown`
- `mark_public_comment`
- `approve_named_official`
- `correct_text`
- `suppress_turn`
- `hold_back_text`

## Policy reminder

Do not promote unresolved speakers to real names without explicit approval evidence.
Do not invent transcript text.
Unknown remains better than wrong.

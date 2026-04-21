# Review Queue

Phase 1 quality tuning keeps the public speaker policy conservative.

Use the generated review queue to focus manual review on:
- unresolved speaker turns
- mixed/rejected speaker turns
- short ambiguous fragments that still need human judgment

## Generate

```bash
python3 scripts/build_review_queue.py apr-14-2026 \
  --structured transcripts_structured/apr-14-2026.json \
  --out reviews/apr-14-2026-review-queue.json
```

## Output

- `reviews/apr-14-2026-review-queue.json`

Each item includes:
- target turn metadata
- review reason
- speaker status
- neighboring turn context

## Policy reminder

Do not promote unresolved speakers to real names without explicit approval evidence.
Unknown remains better than wrong.

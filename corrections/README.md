# Corrections

This folder contains deterministic, user-authored corrections that can be applied during rebuild.

Rules:

- Never edit generated HTML/JS by hand.
- Corrections live here and are applied by the merge/publish steps.
- Prefer mapping *speaker_id → speaker_key* over per-segment hacks.

## Format (v1)

Create `corrections/<meeting_id>.json`:

```json
{
  "schema": "fairfax.corrections.v1",
  "speaker_map": {
    "SPEAKER_22": {
      "speaker_key": "mayor_catherine_read",
      "confidence": 1.0,
      "reason": "manual"
    }
  }
}
```

If you need per-segment overrides later, we will extend the schema.


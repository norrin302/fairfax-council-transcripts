#!/usr/bin/env python3
"""Export a canonical review-decisions template from a review queue.

The output is meant for human editing in Git. It captures reviewer actions,
overrides, and notes while keeping the original structured transcript canonical
until decisions are explicitly applied.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Export review decisions template from review queue")
    ap.add_argument("meeting_id")
    ap.add_argument("--queue", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    queue = json.loads(Path(args.queue).read_text(encoding="utf-8"))
    items = queue.get("items") or []

    decisions = []
    for item in items:
        decisions.append(
            {
                "turn_id": item.get("turn_id"),
                "reviewer_action": "pending",
                "speaker_public_override": "",
                "speaker_status_override": "",
                "text_override": "",
                "suppress": False,
                "notes": "",
            }
        )

    out = {
        "schema": "fairfax.review_decisions.v1",
        "meeting_id": args.meeting_id,
        "status": "draft",
        "source_queue": args.queue,
        "allowed_actions": [
            "pending",
            "keep_unknown",
            "mark_public_comment",
            "approve_named_official",
            "correct_text",
            "suppress_turn",
            "hold_back_text",
        ],
        "decisions": decisions,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"decisions={len(decisions)}")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

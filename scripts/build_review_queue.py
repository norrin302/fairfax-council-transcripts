#!/usr/bin/env python3
"""Build a lightweight review queue from a structured transcript.

Focuses manual review on unresolved and mixed turns, plus very short unknown turns.
Outputs JSON so the review surface stays static-file friendly and Git-friendly.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Build Phase 1 review queue from structured transcript")
    ap.add_argument("meeting_id")
    ap.add_argument("--structured", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--context", type=int, default=1, help="Neighbor turns before/after each review item")
    args = ap.parse_args()

    data = json.loads(Path(args.structured).read_text(encoding="utf-8"))
    turns = data.get("turns") or []
    items = []

    for idx, turn in enumerate(turns):
        text = str(turn.get("text") or "").strip()
        status = str(turn.get("speaker_status") or "")
        reason = str(turn.get("review_reason") or "")
        is_short_unknown = status in {"unknown", "unresolved", "mixed", "public_comment_unverified"} and len(text.split()) <= 3
        suspicious_text = len(text.split()) <= 3 or any(bad in text.lower() for bad in ["even more oh", "has the name", ". i"])
        if not (bool(turn.get("needs_review")) or is_short_unknown or suspicious_text):
            continue

        start = max(0, idx - args.context)
        end = min(len(turns), idx + args.context + 1)
        context = []
        for j in range(start, end):
            t = turns[j]
            context.append(
                {
                    "turn_id": t.get("turn_id"),
                    "speaker_public": t.get("speaker_public"),
                    "speaker_raw": t.get("speaker_raw"),
                    "speaker_status": t.get("speaker_status"),
                    "start": t.get("start"),
                    "end": t.get("end"),
                    "text": t.get("text"),
                    "is_target": j == idx,
                }
            )

        items.append(
            {
                "turn_id": turn.get("turn_id"),
                "speaker_raw": turn.get("speaker_raw"),
                "speaker_public": turn.get("speaker_public"),
                "speaker_status": status,
                "review_reason": reason,
                "start": turn.get("start"),
                "end": turn.get("end"),
                "text": text,
                "word_count": len(text.split()),
                "final_reviewer_action": "pending",
                "final_reviewer_notes": "",
                "context": context,
            }
        )

    out = {
        "schema": "fairfax.review_queue.v1",
        "meeting_id": args.meeting_id,
        "structured_source": args.structured,
        "allowed_reviewer_actions": [
            "pending",
            "keep_unknown",
            "mark_public_comment",
            "approve_named_official",
            "correct_text",
            "suppress_turn",
            "hold_back_text",
        ],
        "items": items,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"items={len(items)}")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Apply human review decisions to a structured transcript.

This keeps the structured transcript as the canonical editable artifact.
The site is regenerated only after explicit review decisions are applied.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ALLOWED_ACTIONS = {
    "pending",
    "keep_unknown",
    "mark_public_comment",
    "approve_named_official",
    "correct_text",
    "suppress_turn",
    "hold_back_text",
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply review decisions to structured transcript")
    ap.add_argument("meeting_id")
    ap.add_argument("--structured", required=True)
    ap.add_argument("--decisions", required=True)
    ap.add_argument("--out", default="", help="Optional output path; defaults to overwriting --structured")
    args = ap.parse_args()

    structured_path = Path(args.structured)
    decisions_path = Path(args.decisions)

    structured = json.loads(structured_path.read_text(encoding="utf-8"))
    decisions_doc = json.loads(decisions_path.read_text(encoding="utf-8"))
    turns = structured.get("turns") or []
    turn_map = {str(t.get("turn_id")): t for t in turns}

    for decision in decisions_doc.get("decisions") or []:
        turn_id = str(decision.get("turn_id") or "")
        action = str(decision.get("reviewer_action") or "pending")
        if not turn_id or action not in ALLOWED_ACTIONS:
            continue
        turn = turn_map.get(turn_id)
        if not turn or action == "pending":
            continue

        speaker_public_override = str(decision.get("speaker_public_override") or "").strip()
        speaker_status_override = str(decision.get("speaker_status_override") or "").strip()
        text_override = str(decision.get("text_override") or "").strip()
        suppress = bool(decision.get("suppress"))
        notes = str(decision.get("notes") or "").strip()

        if action == "keep_unknown":
            turn["speaker_public"] = "Unknown Speaker"
            turn["speaker_status"] = speaker_status_override or "unknown"
        elif action == "mark_public_comment":
            turn["speaker_public"] = speaker_public_override or "Public Comment Speaker"
            turn["speaker_status"] = speaker_status_override or "public_comment_unverified"
        elif action == "approve_named_official":
            if speaker_public_override:
                turn["speaker_public"] = speaker_public_override
            if speaker_status_override:
                turn["speaker_status"] = speaker_status_override
            else:
                turn["speaker_status"] = "approved"
        elif action == "correct_text":
            if text_override:
                turn["text"] = text_override
        elif action == "hold_back_text":
            turn["speaker_public"] = speaker_public_override or turn.get("speaker_public") or "Unknown Speaker"
            turn["speaker_status"] = speaker_status_override or str(turn.get("speaker_status") or "unknown")
            turn["needs_review"] = True
            turn["review_reason"] = "hold_back_text"
        elif action == "suppress_turn" or suppress:
            turn["text"] = ""
            turn["needs_review"] = False
            turn["review_reason"] = "suppressed_by_reviewer"

        if notes:
            turn["reviewer_notes"] = notes
        turn["reviewed"] = True
        if action != "hold_back_text" and turn.get("text"):
            turn["needs_review"] = False
            turn["review_reason"] = f"reviewed:{action}"

    structured["turns"] = [t for t in turns if str(t.get("text") or "").strip()]

    out_path = Path(args.out) if args.out else structured_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(structured, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

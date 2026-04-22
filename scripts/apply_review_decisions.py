#!/usr/bin/env python3
"""Apply human review decisions to a structured transcript.

This keeps the structured transcript as the canonical editable artifact.
The site is regenerated only after explicit review decisions are applied.

Provenance tracking (v2.2+):
  Each apply run records a provenance entry in:
    - structured_json["_review_apply_provenance"]: append-only log of apply events
    - <structured_dir>/.apply-reports/<meeting_id>-<ts>.json: one report per apply run
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
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
    ap.add_argument(
        "--out",
        default="",
        help="Optional output path; defaults to overwriting --structured",
    )
    args = ap.parse_args()

    structured_path = Path(args.structured)
    decisions_path = Path(args.decisions)
    out_path = Path(args.out) if args.out else structured_path

    structured = json.loads(structured_path.read_text(encoding="utf-8"))
    decisions_doc = json.loads(decisions_path.read_text(encoding="utf-8"))

    # ---- Collect provenance from decisions ----
    decisions_list = decisions_doc.get("decisions") or []
    decision_ids = [str(d.get("decision_id", "")) for d in decisions_list if d.get("decision_id")]
    batch_ids = list(
        dict.fromkeys(
            str(d.get("export_batch_id", "")) for d in decisions_list if d.get("export_batch_id")
        )
    )
    # Deduplicate while preserving order
    batch_ids = list(dict.fromkeys(batch_ids))

    applied_at = datetime.now(timezone.utc).isoformat()

    # ---- Apply each decision ----
    turns = structured.get("turns") or []
    turn_map = {str(t.get("turn_id")): t for t in turns}
    applied_count = 0

    for decision in decisions_list:
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

        applied_count += 1

    # Prune suppressed/empty turns
    structured["turns"] = [
        t for t in turns if str(t.get("text") or "").strip()
    ]

    # ---- Build provenance entry ----
    provenance_entry = {
        "applied_at": applied_at,
        "applied_from_decisions_file": str(decisions_path.resolve()),
        "applied_decision_count": applied_count,
        "applied_decision_ids": decision_ids,
        "applied_export_batch_ids": batch_ids,
        "apply_script_version": "2.2",
    }

    # ---- Append to structured JSON metadata ----
    if "_review_apply_provenance" not in structured:
        structured["_review_apply_provenance"] = []
    structured["_review_apply_provenance"].append(provenance_entry)

    # ---- Write structured JSON ----
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(structured, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # ---- Write sidecar apply report ----
    report_dir = out_path.parent / ".apply-reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    ts_suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = report_dir / f"{args.meeting_id}-{ts_suffix}.json"
    report = {
        "meeting_id": args.meeting_id,
        "structured_output": str(out_path.resolve()),
        "provenance": provenance_entry,
        "decisions_applied": [
            {
                "decision_id": str(d.get("decision_id", "")),
                "export_batch_id": str(d.get("export_batch_id", "")),
                "turn_id": str(d.get("turn_id", "")),
                "reviewer_action": str(d.get("reviewer_action", "")),
                "speaker_name": str(d.get("speaker_name", "")),
            }
            for d in decisions_list
            if str(d.get("turn_id", "")) in turn_map
            and str(d.get("reviewer_action", "")) in ALLOWED_ACTIONS
        ],
    }
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Applied {applied_count} decisions")
    print(f"Structured JSON: {out_path}")
    print(f"Apply report:    {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

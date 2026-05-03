#!/usr/bin/env python3
"""Apply review decisions from a staged-decisions JSON export to a structured transcript.

Reads decisions exported from docs/js/review-ui.js (the review cockpit), updates the
matching turns in transcripts_structured/<meeting_id>.json, then republishes the
meeting docs.

Usage:
    python3 scripts/apply_review_decisions.py apr-14-2026 --decisions ~/Downloads/apr-14-2026-staged-decisions.json
    python3 scripts/apply_review_decisions.py apr-14-2026 --decisions decisions.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
STRUCTURED_DIR = REPO_ROOT / "transcripts_structured"


def load_structured(meeting_id: str) -> dict[str, Any]:
    path = STRUCTURED_DIR / f"{meeting_id}.json"
    if not path.exists():
        raise SystemExit(f"Structured transcript not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_decisions(decisions_path: str) -> list[dict[str, Any]]:
    p = Path(decisions_path)
    if not p.exists():
        raise SystemExit(f"Decisions file not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Decisions file must contain a JSON array.")
    return data


def build_review_reason(decision: dict[str, Any]) -> str:
    """Construct a review_reason string from the decision."""
    action = decision.get("reviewer_action", "keep_unknown")
    evidence = decision.get("evidence_note", "")
    reason = f"reviewed:{action}"
    if evidence:
        reason += f" | {evidence}"
    return reason


def apply_decisions(
    data: dict[str, Any],
    decisions: list[dict[str, Any]],
    dry_run: bool = False,
) -> tuple[int, int, int]:
    """Apply decisions to turns in data. Returns (approved, unknown, suppressed) counts."""
    turns_by_id: dict[str, dict[str, Any]] = {t["turn_id"]: t for t in data.get("turns", [])}

    approved = 0
    unknown = 0
    suppressed = 0

    for decision in decisions:
        turn_id = decision.get("turn_id")
        if not turn_id:
            print("  [WARN] Decision missing turn_id, skipping", file=sys.stderr)
            continue

        turn = turns_by_id.get(turn_id)
        if turn is None:
            print(f"  [WARN] turn_id '{turn_id}' not found in structured transcript, skipping", file=sys.stderr)
            continue

        suppress = bool(decision.get("suppress", False))

        if suppress:
            # Redact the speaker — turn stays in transcript but is marked suppressed
            turn["speaker_public"] = "REDACTED"
            turn["speaker_status"] = "suppressed"
            turn["review_reason"] = build_review_reason(decision)
            suppressed += 1
        else:
            speaker_public = decision.get("speaker_public_override") or turn.get("speaker_public", "Unknown Speaker")
            speaker_status = decision.get("speaker_status_override") or turn.get("speaker_status", "unknown")

            turn["speaker_public"] = speaker_public
            turn["speaker_status"] = speaker_status
            turn["review_reason"] = build_review_reason(decision)
            turn["reviewer_notes"] = decision.get("evidence_note", "")

            if speaker_status == "approved":
                approved += 1
            else:
                unknown += 1

        # Idempotent: always overwrite — re-running same decisions just confirms them

    return approved, unknown, suppressed


def republish_meeting(meeting_id: str) -> None:
    """Rebuild docs/transcripts/<meeting_id>-data.js and <meeting_id>.html."""
    structured_path = STRUCTURED_DIR / f"{meeting_id}.json"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "publish_structured_meeting.py"),
            meeting_id,
            "--structured",
            str(structured_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  [ERROR] publish_structured_meeting.py failed:\n{result.stderr}", file=sys.stderr)
        raise SystemExit(f"Republish failed with code {result.returncode}")
    print(f"  Republished: docs/transcripts/{meeting_id}-data.js and {meeting_id}.html")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Apply review decisions from review-ui export to a structured transcript."
    )
    ap.add_argument("meeting_id", help="Meeting ID (e.g. apr-14-2026)")
    ap.add_argument(
        "--decisions",
        required=True,
        dest="decisions_path",
        help="Path to the staged-decisions JSON file exported from the review UI",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing any files",
    )
    args = ap.parse_args()

    print(f"Loading structured transcript: {args.meeting_id}")
    data = load_structured(args.meeting_id)

    print(f"Loading decisions from: {args.decisions_path}")
    decisions = load_decisions(args.decisions_path)
    print(f"  {len(decisions)} decision(s) to apply")

    approved, unknown, suppressed = apply_decisions(data, decisions, dry_run=args.dry_run)

    if args.dry_run:
        print("\n[DRY RUN] No files written. Would apply:")
    else:
        # Write updated structured transcript
        out_path = STRUCTURED_DIR / f"{args.meeting_id}.json"
        tmp_path = out_path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp_path.rename(out_path)
        print(f"\nWrote: {out_path}")
        republish_meeting(args.meeting_id)
        print("\nApplied:")

    print(f"  Applied {len(decisions)} decisions: {approved} approved, {unknown} kept unknown, {suppressed} suppressed")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

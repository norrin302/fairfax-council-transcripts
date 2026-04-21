#!/usr/bin/env python3
"""Publish a meeting from a structured transcript JSON (Phase 1).

Source of truth: structured transcript JSON with turns[]
Outputs:
- docs/transcripts/<meeting_id>-data.js
- docs/transcripts/<meeting_id>.html
- docs/js/search-index.js

This avoids hand-editing HTML and decouples publish from raw ASR formats.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.publish_meeting import load_meeting, write_turns_js, write_transcript_html  # type: ignore
from scripts.build_search_index import build  # type: ignore


def main() -> int:
    ap = argparse.ArgumentParser(description="Publish meeting from structured transcript JSON")
    ap.add_argument("meeting_id")
    ap.add_argument("--structured", required=True, help="Structured transcript JSON (fairfax.structured_transcript.v1)")
    args = ap.parse_args()

    meeting = load_meeting(args.meeting_id)
    data = json.loads(Path(args.structured).read_text(encoding="utf-8"))
    turns = data.get("turns")
    if not isinstance(turns, list) or not turns:
        raise SystemExit("Structured transcript missing turns[]")

    labeled_turns: list[dict[str, Any]] = []
    for t in turns:
        text = str(t.get("text") or "").strip()
        if not text:
            continue
        labeled_turns.append(
            {
                "speaker": str(t.get("speaker_public") or "Unknown Speaker"),
                "speaker_source": str(t.get("speaker_status") or "unknown"),
                "speaker_source_detail": str(t.get("review_reason") or ""),
                "start": float(t.get("start", 0) or 0),
                "end": float(t.get("end", 0) or 0),
                "text": text,
            }
        )

    turns_out = REPO_ROOT / "docs" / "transcripts" / f"{args.meeting_id}-data.js"
    html_out = REPO_ROOT / "docs" / "transcripts" / f"{args.meeting_id}.html"

    write_turns_js(args.meeting_id, labeled_turns, turns_out)
    write_transcript_html(meeting, html_out)

    build()

    print(turns_out)
    print(html_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

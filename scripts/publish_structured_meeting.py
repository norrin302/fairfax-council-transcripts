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
import subprocess
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
    for idx, t in enumerate(turns):
        # Worker writes to speaker/speaker_source; speaker_public/speaker_status is the pre-review baseline.
        # When review decisions are applied, speaker is set directly. Use it if present.
        effective_speaker = t.get("speaker") or t.get("speaker_public") or "Unknown Speaker"
        effective_source = t.get("speaker_source") or t.get("speaker_status") or "unknown"
        labeled_turns.append(
            {
                "turn_id": str(t.get("turn_id") or f"turn_{idx+1:06d}"),
                "speaker": str(effective_speaker),
                "speaker_source": str(effective_source),
                "speaker_source_detail": str(t.get("speaker_source_detail") or t.get("review_reason") or ""),
                "start": float(t.get("start", 0) or 0),
                "end": float(t.get("end", 0) or 0),
                "text": str(t.get("text") or "").strip(),
            }
        )
    turns_out = REPO_ROOT / "docs" / "transcripts" / f"{args.meeting_id}-data.js"
    html_out = REPO_ROOT / "docs" / "transcripts" / f"{args.meeting_id}.html"

    write_turns_js(args.meeting_id, labeled_turns, turns_out)
    write_transcript_html(meeting, html_out)

    build()

    print(turns_out)
    print(html_out)

    # Run voice clustering so clusters file is available for review UI
    cluster_script = REPO_ROOT / "scripts" / "cluster_for_review.py"
    try:
        result = subprocess.run(
            [sys.executable, str(cluster_script), args.meeting_id],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print(result.stdout.strip())
        else:
            print("cluster_for_review warning:", result.stderr.strip(), file=sys.stderr)
    except Exception as exc:
        print(f"cluster_for_review skipped ({exc})", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

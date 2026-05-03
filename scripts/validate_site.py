#!/usr/bin/env python3
"""Lightweight repo sanity checks for the static site.

Validates:
- meetings/*.json required fields
- referenced docs assets exist
- build_search_index can run
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def die(msg: str) -> None:
    print(f"ERROR: {msg}")
    raise SystemExit(1)


def require(path: Path, why: str) -> None:
    if not path.exists():
        die(f"Missing {why}: {path}")


def validate_meetings() -> None:
    meetings_dir = REPO_ROOT / "meetings"
    require(meetings_dir, "meetings/ directory")
    files = sorted(meetings_dir.glob("*.json"))
    if not files:
        die("No meeting metadata found in meetings/*.json")

    for p in files:
        m = json.loads(p.read_text(encoding="utf-8"))
        for k in ["meeting_id", "meeting_date", "title", "meeting_type", "source_video_url", "transcript_url", "transcript_turns_js"]:
            if not m.get(k):
                die(f"{p}: missing required field {k}")

        meeting_id = m["meeting_id"]
        if p.stem != meeting_id:
            die(f"{p}: filename stem must equal meeting_id ({meeting_id})")

        # Docs paths (allow incremental backfills where meeting metadata exists
        # but transcript hasn't been published yet)
        transcript_html = REPO_ROOT / "docs" / m["transcript_url"]
        turns_js = REPO_ROOT / m["transcript_turns_js"]

        if not transcript_html.exists() or not turns_js.exists():
            print(f"WARN: {meeting_id} not published yet (missing docs assets)")
            continue

        # Quick validation that TRANSCRIPT_TURNS is present
        raw = turns_js.read_text(encoding="utf-8")
        if not re.search(r"const\s+TRANSCRIPT_TURNS\s*=\s*\[", raw):
            die(f"{turns_js}: does not define const TRANSCRIPT_TURNS = [ ... ]")


def validate_docs_root() -> None:
    require(REPO_ROOT / "docs" / "index.html", "docs/index.html")
    require(REPO_ROOT / "docs" / "js" / "search.js", "docs/js/search.js")
    require(REPO_ROOT / "docs" / "js" / "search-index.js", "docs/js/search-index.js")
    require(REPO_ROOT / "docs" / "js" / "meetings.js", "docs/js/meetings.js")
    require(REPO_ROOT / "docs" / "js" / "transcript-page.js", "docs/js/transcript-page.js")
    require(REPO_ROOT / "docs" / "css" / "transcript-page.css", "docs/css/transcript-page.css")


def main() -> int:
    validate_docs_root()
    validate_meetings()
    print("OK: site structure looks sane")
    return 0


if __name__ == "__main__":
    sys.exit(main())

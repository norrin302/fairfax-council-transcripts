#!/usr/bin/env python3
"""Republish all meetings using official Granicus captions.vtt.

This is fast (no transcription) and keeps transcript text/timestamps aligned with the player.

Usage:
  python3 scripts/republish_all_captions.py
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    meetings_dir = REPO_ROOT / "meetings"
    meeting_ids = sorted(p.stem for p in meetings_dir.glob("*.json"))
    if not meeting_ids:
        print(f"No meetings found in {meetings_dir}")
        return 1

    for mid in meeting_ids:
        print(f"=== {mid} ===")
        subprocess.run(
            ["python3", "scripts/publish_meeting.py", mid, "--captions"],
            cwd=str(REPO_ROOT),
            check=True,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


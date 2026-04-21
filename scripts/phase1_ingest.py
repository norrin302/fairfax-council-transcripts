#!/usr/bin/env python3
"""Phase 1 ingest: download a Granicus clip to a Juggernaut work root.

Idempotent by default: if the target file exists and looks non-empty, it will not re-download unless --force.

This script intentionally does NOT write large binaries into Git.

Dependencies (Juggernaut):
- yt-dlp
- ffmpeg (optional for downstream steps)
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def _require_bin(name: str) -> None:
    if subprocess.run(["bash", "-lc", f"command -v {name}"], capture_output=True).returncode != 0:
        raise SystemExit(f"Missing required binary: {name}. Install it on Juggernaut (e.g. apt-get install {name}).")


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest a Granicus clip URL (Phase 1)")
    ap.add_argument("url", help="Granicus clip URL")
    ap.add_argument("--meeting-id", required=True)
    ap.add_argument("--work-root", required=True, help="Work root on Juggernaut (not in Git)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    _require_bin("yt-dlp")

    work_root = Path(args.work_root)
    meeting_dir = work_root / args.meeting_id
    media_dir = meeting_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    marker = meeting_dir / "ingest.json"
    if marker.exists() and not args.force:
        try:
            prev = json.loads(marker.read_text(encoding="utf-8"))
            fp = prev.get("filepath")
            if fp and Path(fp).exists() and Path(fp).stat().st_size > 1024 * 1024:
                print(f"Already ingested: {fp}")
                print(marker)
                return 0
        except Exception:
            pass

    # Download best available media to the meeting media dir.
    # NOTE: We keep filenames deterministic by embedding meeting id.
    outtmpl = str(media_dir / f"{args.meeting_id}.%(ext)s")
    cmd = [
        "yt-dlp",
        "--no-warnings",
        "--no-playlist",
        "-f",
        "bestaudio/best",
        "-o",
        outtmpl,
        args.url,
    ]
    subprocess.run(cmd, check=True)

    # Find the downloaded file (the template may select different extensions).
    candidates = sorted(media_dir.glob(f"{args.meeting_id}.*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise SystemExit(f"Ingest failed: no downloaded file found in {media_dir}")

    filepath = str(candidates[0])
    info = {
        "meeting_id": args.meeting_id,
        "url": args.url,
        "filepath": filepath,
        "work_root": str(work_root),
    }
    marker.write_text(json.dumps(info, indent=2), encoding="utf-8")

    print(filepath)
    print(marker)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

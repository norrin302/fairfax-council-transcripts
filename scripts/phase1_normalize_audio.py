#!/usr/bin/env python3
"""Phase 1 audio normalization.

Convert source media to canonical working audio format:
- mono
- 16 kHz
- WAV

All outputs are written under Juggernaut work root, not committed to Git.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Normalize audio to 16k mono wav (Phase 1)")
    ap.add_argument("--meeting-id", required=True)
    ap.add_argument("--work-root", required=True)
    ap.add_argument("--source", default="", help="Optional explicit source media path (otherwise uses ingest.json)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    work_root = Path(args.work_root)
    meeting_dir = work_root / args.meeting_id
    audio_dir = meeting_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    out_wav = audio_dir / "audio_16k_mono.wav"
    if out_wav.exists() and out_wav.stat().st_size > 1024 * 1024 and not args.force:
        print(out_wav)
        return 0

    source = args.source
    if not source:
        ingest_path = meeting_dir / "ingest.json"
        obj = json.loads(ingest_path.read_text(encoding="utf-8"))
        source = obj.get("filepath")
    if not source:
        raise SystemExit("Missing source media. Provide --source or run phase1_ingest.py first.")

    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-ac",
            "1",
            "-ar",
            "16000",
            str(out_wav),
        ],
        check=True,
    )

    print(out_wav)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

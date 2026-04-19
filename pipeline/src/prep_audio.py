from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
import json


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Download + normalize meeting audio")
    ap.add_argument("meeting_id")
    ap.add_argument("--meetings-dir", default="/repo/meetings")
    ap.add_argument("--work-dir", default="/work")
    ap.add_argument("--format", default="bestaudio/best")
    args = ap.parse_args()

    meetings_dir = Path(args.meetings_dir)
    meeting_path = meetings_dir / f"{args.meeting_id}.json"
    if not meeting_path.exists():
        raise SystemExit(f"Missing meeting file: {meeting_path}")

    meeting = json.loads(meeting_path.read_text(encoding="utf-8"))
    url = str(meeting.get("source_video_url") or meeting.get("source_url") or "").strip()
    if not url:
        raise SystemExit("Meeting metadata missing source_video_url")

    out_root = Path(args.work_dir) / args.meeting_id
    audio_dir = out_root / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    downloaded = audio_dir / "source.%(ext)s"
    normalized = audio_dir / "audio_16k_mono.wav"

    # Download bestaudio.
    run([
        "yt-dlp",
        "-f",
        args.format,
        "-o",
        str(downloaded),
        url,
    ])

    # Find the downloaded file (yt-dlp expands extension).
    # yt-dlp may leave sidecar files (e.g. .ytdl) or partial downloads (.part).
    # Select the largest plausible media file.
    candidates = []
    for p in audio_dir.iterdir():
        if not (p.name.startswith("source.") and p.is_file()):
            continue
        suf = set(p.suffixes)
        if ".part" in suf or ".ytdl" in suf:
            continue
        try:
            sz = p.stat().st_size
        except Exception:
            continue
        if sz < 1024 * 1024:
            continue
        candidates.append((sz, p))

    src = max(candidates, key=lambda x: x[0])[1] if candidates else None
    if not src:
        raise SystemExit("Download finished but could not find source.*")

    # Normalize.
    run([
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(normalized),
    ])

    print(str(normalized))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Chunked OpenAI Whisper transcription for long meetings.

Why:
- OpenAI's audio transcription endpoint has a per-file size limit.
- Granicus MP4 downloads are often huge.

This script:
1) Downloads the clip's official MP3 (or any audio URL) once.
2) Re-encodes + segments into small MP3 chunks.
3) Transcribes each chunk with OpenAI (verbose_json).
4) Merges into a single *_complete.json with global timestamps.

Outputs (repo-relative):
- transcripts/<meeting_id>_segNNN.json  (raw per-chunk responses)
- transcripts/<meeting_id>_complete.json (merged segments, global timeline)

Safe to re-run, it resumes from existing seg files.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


def sh(cmd: list[str]) -> str:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout.strip()


def ffprobe_duration_seconds(path: Path) -> float:
    out = sh([
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ])
    try:
        return float(out)
    except Exception as e:
        raise RuntimeError(f"Could not parse duration from ffprobe output for {path}: {out}") from e


def download(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and out_path.stat().st_size > 0:
        return
    # curl with resume
    sh([
        "curl",
        "-L",
        "--fail",
        "--retry",
        "3",
        "--retry-delay",
        "2",
        "-C",
        "-",
        "-o",
        str(out_path),
        url,
    ])


def segment_audio(
    src_audio: Path,
    chunks_dir: Path,
    segment_seconds: int,
    bitrate: str,
    sample_rate: int,
    channels: int,
) -> list[Path]:
    chunks_dir.mkdir(parents=True, exist_ok=True)

    # If chunks already exist, reuse.
    existing = sorted(chunks_dir.glob("chunk*.mp3"))
    if existing:
        return existing

    out_pattern = str(chunks_dir / "chunk%03d.mp3")
    sh([
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src_audio),
        "-vn",
        "-ac",
        str(channels),
        "-ar",
        str(sample_rate),
        "-b:a",
        str(bitrate),
        "-f",
        "segment",
        "-segment_time",
        str(segment_seconds),
        "-reset_timestamps",
        "1",
        out_pattern,
    ])

    chunks = sorted(chunks_dir.glob("chunk*.mp3"))
    if not chunks:
        raise RuntimeError(f"No chunks produced in {chunks_dir}")
    return chunks


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def openai_client():
    try:
        import openai  # type: ignore
    except ImportError as e:
        raise RuntimeError("Missing dependency 'openai'. Install requirements.txt in a venv.") from e

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        secrets_path = Path("~/.openclaw/secrets.env").expanduser()
        if secrets_path.exists():
            for line in secrets_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("OPENAI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"\'')
                    break

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    return openai.OpenAI(api_key=api_key)


def transcribe_chunk(client: Any, chunk_path: Path, model: str) -> dict[str, Any]:
    with chunk_path.open("rb") as f:
        tr = client.audio.transcriptions.create(
            model=model,
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    # openai objects are pydantic-ish; to dict via json
    raw = json.loads(tr.model_dump_json()) if hasattr(tr, "model_dump_json") else json.loads(tr.json())
    return raw


@dataclass
class MergeResult:
    language: str
    duration: float
    text: str
    segments: list[dict[str, Any]]


def merge_segments(seg_files: list[Path], meeting_date: str | None = None) -> dict[str, Any]:
    merged: list[dict[str, Any]] = []
    full_text_parts: list[str] = []
    offset = 0.0
    global_id = 0
    language = "en"

    for sf in seg_files:
        data = load_json(sf)
        language = data.get("language") or language
        full_text_parts.append(str(data.get("text", "") or "").strip())

        segs = data.get("segments") or []
        for seg in segs:
            s = float(seg.get("start", 0) or 0) + offset
            e = float(seg.get("end", s) or s) + offset
            out = dict(seg)
            out["start"] = s
            out["end"] = e
            out["id"] = global_id
            global_id += 1
            merged.append(out)

        # Advance offset by actual chunk duration when available, else by last segment end
        dur = data.get("duration")
        try:
            offset += float(dur)
        except Exception:
            if segs:
                offset = float(merged[-1].get("end", offset))

    out = {
        "meeting_date": meeting_date or "",
        "duration": offset,
        "language": language,
        "text": "\n".join([t for t in full_text_parts if t]),
        "segments": merged,
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Chunked OpenAI Whisper transcription")
    ap.add_argument("--meeting-id", required=True, help="Meeting id slug, e.g. apr-07-2026")
    ap.add_argument("--audio-url", required=True, help="Direct audio URL (mp3 preferred)")
    ap.add_argument("--meeting-date", default="", help="Human label for meeting date (e.g. April 7, 2026)")
    ap.add_argument("--segment-seconds", type=int, default=600, help="Chunk size in seconds")
    ap.add_argument("--bitrate", default="48k", help="Audio bitrate for chunk encoding")
    ap.add_argument("--sample-rate", type=int, default=16000, help="Sample rate for chunk encoding")
    ap.add_argument("--channels", type=int, default=1, help="Audio channels for chunk encoding")
    ap.add_argument("--model", default="whisper-1", help="OpenAI transcription model")
    ap.add_argument("--max-chunks", type=int, default=0, help="If >0, only transcribe first N chunks (debug)")
    ap.add_argument("--prepare-only", action="store_true", help="Only download + segment audio, do not call OpenAI")
    args = ap.parse_args()

    meeting_id = args.meeting_id
    audio_url = args.audio_url

    audio_path = REPO_ROOT / "videos" / f"{meeting_id}.mp3"
    download(audio_url, audio_path)

    chunks_dir = REPO_ROOT / "videos" / f"{meeting_id}-chunks"
    chunks = segment_audio(
        audio_path,
        chunks_dir,
        segment_seconds=args.segment_seconds,
        bitrate=args.bitrate,
        sample_rate=args.sample_rate,
        channels=args.channels,
    )

    if args.max_chunks and args.max_chunks > 0:
        chunks = chunks[: args.max_chunks]

    if args.prepare_only:
        total = sum(ffprobe_duration_seconds(c) for c in chunks)
        print(f"Prepared {len(chunks)} chunks in {chunks_dir} (total_duration_seconds≈{total:.1f})")
        return 0

    transcripts_dir = REPO_ROOT / "transcripts"
    seg_files: list[Path] = []

    client = openai_client()

    for i, chunk in enumerate(chunks):
        seg_out = transcripts_dir / f"{meeting_id}_seg{i:03d}.json"
        seg_files.append(seg_out)
        if seg_out.exists() and seg_out.stat().st_size > 0:
            continue
        raw = transcribe_chunk(client, chunk, model=args.model)
        save_json(seg_out, raw)
        print(f"Wrote {seg_out}")

    complete = merge_segments(seg_files, meeting_date=args.meeting_date)
    complete_out = transcripts_dir / f"{meeting_id}_complete.json"
    save_json(complete_out, complete)
    print(f"Wrote {complete_out} (segments={len(complete.get('segments', []))})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

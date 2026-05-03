#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class Segment:
    speaker: str
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


def load_segments(path: Path) -> list[Segment]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    raw = obj.get("segments") if isinstance(obj, dict) else None
    if not isinstance(raw, list):
        raise SystemExit(f"Diarization JSON missing segments[]: {path}")

    out: list[Segment] = []
    for seg in raw:
        try:
            speaker = str(seg.get("speaker") or "").strip()
            start = float(seg.get("start"))
            end = float(seg.get("end"))
        except Exception:
            continue
        if not speaker or end <= start:
            continue
        out.append(Segment(speaker=speaker, start=start, end=end))
    out.sort(key=lambda s: (s.start, s.end, s.speaker))
    return out


def merge_adjacent(segments: Iterable[Segment], max_gap: float) -> list[Segment]:
    merged: list[Segment] = []
    current: Segment | None = None
    for seg in segments:
        if current is None:
            current = Segment(seg.speaker, seg.start, seg.end)
            continue
        if seg.speaker == current.speaker and (seg.start - current.end) <= max_gap:
            current.end = max(current.end, seg.end)
        else:
            merged.append(current)
            current = Segment(seg.speaker, seg.start, seg.end)
    if current is not None:
        merged.append(current)
    return merged


def export_clip(audio: Path, start: float, end: float, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{(end - start):.3f}",
            "-i",
            str(audio),
            "-ac",
            "1",
            "-ar",
            "16000",
            str(out_path),
        ],
        check=True,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Export long diarized clips for reference-voice review")
    ap.add_argument("audio", help="Source audio file")
    ap.add_argument("diarization", help="Diarization JSON with segments[]")
    ap.add_argument("--out-dir", required=True, help="Directory for exported clips + manifest")
    ap.add_argument("--meeting-id", default="", help="Optional meeting id for manifest")
    ap.add_argument("--max-gap", type=float, default=0.35, help="Merge adjacent same-speaker segments up to this gap")
    ap.add_argument("--min-duration", type=float, default=6.0, help="Only export clips at least this long")
    ap.add_argument("--max-clips-per-speaker", type=int, default=4, help="Maximum exported clips per speaker")
    ap.add_argument("--top-speakers", type=int, default=12, help="Only export the most talkative speakers (0 = all)")
    ap.add_argument("--speaker", action="append", default=[], help="Export only this speaker ID (repeatable)")
    args = ap.parse_args()

    audio = Path(args.audio)
    diar = Path(args.diarization)
    out_dir = Path(args.out_dir)
    if not audio.exists():
        raise SystemExit(f"Missing audio file: {audio}")
    if not diar.exists():
        raise SystemExit(f"Missing diarization file: {diar}")

    segments = merge_adjacent(load_segments(diar), args.max_gap)

    by_speaker: dict[str, list[Segment]] = {}
    total_seconds: dict[str, float] = {}
    for seg in segments:
        total_seconds[seg.speaker] = total_seconds.get(seg.speaker, 0.0) + seg.duration
        if seg.duration < args.min_duration:
            continue
        by_speaker.setdefault(seg.speaker, []).append(seg)

    ranked_speakers = sorted(total_seconds.items(), key=lambda kv: kv[1], reverse=True)
    requested = {s.strip() for s in args.speaker if s.strip()}
    if requested:
        allowed = requested
    elif args.top_speakers > 0:
        allowed = {speaker for speaker, _ in ranked_speakers[: args.top_speakers]}
    else:
        allowed = {speaker for speaker, _ in ranked_speakers}

    manifest: dict[str, object] = {
        "meeting_id": args.meeting_id,
        "audio": str(audio),
        "diarization": str(diar),
        "selection": {
            "max_gap": args.max_gap,
            "min_duration": args.min_duration,
            "max_clips_per_speaker": args.max_clips_per_speaker,
            "top_speakers": args.top_speakers,
            "requested_speakers": sorted(requested),
        },
        "speakers": [],
    }

    exported = 0
    for speaker, total in ranked_speakers:
        if speaker not in allowed:
            continue
        candidates = sorted(by_speaker.get(speaker, []), key=lambda s: s.duration, reverse=True)
        selected = candidates[: args.max_clips_per_speaker]
        if not selected:
            continue

        speaker_entry = {
            "speaker_id": speaker,
            "total_speech_seconds": round(total, 3),
            "clips": [],
        }
        for idx, seg in enumerate(selected, start=1):
            clip_name = f"clip_{idx:02d}_{seg.start:09.3f}_{seg.end:09.3f}.wav"
            clip_path = out_dir / speaker / clip_name
            export_clip(audio, seg.start, seg.end, clip_path)
            speaker_entry["clips"].append(
                {
                    "path": str(clip_path),
                    "start": round(seg.start, 3),
                    "end": round(seg.end, 3),
                    "duration": round(seg.duration, 3),
                }
            )
            exported += 1
        manifest["speakers"].append(speaker_entry)

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Exported {exported} clips for {len(manifest['speakers'])} speakers")
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

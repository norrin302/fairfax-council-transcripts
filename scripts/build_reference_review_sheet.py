#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def load_words(asr_path: Path) -> list[dict]:
    obj = json.loads(asr_path.read_text(encoding="utf-8"))
    words = obj.get("word_segments") or obj.get("words") or []
    if not isinstance(words, list):
        raise SystemExit(f"ASR JSON missing word_segments[]/words[]: {asr_path}")
    out = []
    for w in words:
        try:
            start = float(w.get("start"))
            end = float(w.get("end"))
            word = str(w.get("word") or "").strip()
        except Exception:
            continue
        if not word:
            continue
        out.append({"start": start, "end": end, "word": word})
    return out


def join_words(parts: list[str]) -> str:
    out = ""
    for word in parts:
        if not word:
            continue
        if not out:
            out = word
        elif word.startswith("'"):
            out += word
        elif word in {".", ",", "!", "?", ":", ";"} or word.startswith(".") or word.startswith(","):
            out += word
        else:
            out += " " + word
    return " ".join(out.split())


def excerpt_for_range(words: list[dict], start: float, end: float, pad: float) -> str:
    lo = start - pad
    hi = end + pad
    selected = []
    for word in words:
        if word["end"] < lo:
            continue
        if word["start"] > hi:
            break
        selected.append(word["word"])
    return join_words(selected)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a review sheet for reference voice clips")
    ap.add_argument("manifest", help="Manifest JSON from export_reference_clips.py")
    ap.add_argument("asr", help="ASR JSON with word_segments[] or words[]")
    ap.add_argument("--out-csv", required=True, help="Output CSV path")
    ap.add_argument("--out-json", default="", help="Optional output JSON path")
    ap.add_argument("--excerpt-pad", type=float, default=1.0, help="Extra seconds of context around each clip")
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    asr_path = Path(args.asr)
    out_csv = Path(args.out_csv)
    out_json = Path(args.out_json) if args.out_json else None

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    speakers = manifest.get("speakers") or []
    words = load_words(asr_path)

    rows = []
    for speaker in speakers:
        speaker_id = str(speaker.get("speaker_id") or "").strip()
        total_speech = speaker.get("total_speech_seconds")
        for clip in speaker.get("clips") or []:
            start = float(clip["start"])
            end = float(clip["end"])
            rows.append(
                {
                    "meeting_id": manifest.get("meeting_id") or "",
                    "speaker_id": speaker_id,
                    "total_speech_seconds": total_speech,
                    "clip_path": clip["path"],
                    "start": start,
                    "end": end,
                    "duration": float(clip["duration"]),
                    "transcript_excerpt": excerpt_for_range(words, start, end, args.excerpt_pad),
                    "approval_status": "pending",
                    "approved_identity": "",
                    "approved_speaker_key": "",
                    "approved_by": "",
                    "notes": "",
                }
            )

    rows.sort(key=lambda r: (r["speaker_id"], -r["duration"], r["start"]))

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "meeting_id",
                "speaker_id",
                "total_speech_seconds",
                "clip_path",
                "start",
                "end",
                "duration",
                "transcript_excerpt",
                "approval_status",
                "approved_identity",
                "approved_speaker_key",
                "approved_by",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    if out_json:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    print(f"Wrote {len(rows)} rows to {out_csv}")
    if out_json:
        print(out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

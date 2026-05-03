#!/usr/bin/env python3
"""Convert merge output (segments_with_speaker_names.json) to structured transcript format."""
import argparse, json
from pathlib import Path

MEETINGS_DIR = Path(__file__).resolve().parents[1] / "meetings"

def load_meeting_meta(meeting_id):
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"meeting_id": meeting_id, "title": meeting_id, "meeting_date": "", "meeting_type": ""}

def convert(meeting_id, merge_path, out_path):
    merge = json.loads(Path(merge_path).read_text())
    meta = load_meeting_meta(meeting_id)

    turns = []
    for i, seg in enumerate(merge.get("segments", [])):
        turns.append({
            "turn_id": seg.get("segment_id", f"turn_{i+1:06d}"),
            "start": seg.get("start_seconds", 0),
            "end": seg.get("end_seconds", 0),
            "text": seg.get("text", ""),
            "speaker": seg.get("speaker_name", "Unknown Speaker"),
            "speaker_raw": seg.get("speaker_id", "UNKNOWN"),
            "speaker_public": seg.get("speaker_name", "Unknown Speaker"),
            "speaker_status": "unresolved" if seg.get("needs_review") else "resolved",
            "needs_review": seg.get("needs_review", True),
            "review_reason": seg.get("review_reason", ""),
            "confidence": seg.get("speaker_confidence", 0.0),
        })

    out = {
        "schema": "fairfax.structured_transcript.v1",
        "meeting": meta,
        "turns": turns,
    }
    Path(out_path).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {len(turns)} turns to {out_path}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("meeting_id")
    ap.add_argument("--merge")
    ap.add_argument("--out")
    args = ap.parse_args()
    if not args.merge:
        args.merge = f"pipeline/work/{args.meeting_id}/merged/segments_with_speaker_names.json"
    if not args.out:
        args.out = f"transcripts_structured/{args.meeting_id}.json"
    convert(args.meeting_id, args.merge, args.out)

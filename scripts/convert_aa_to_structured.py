#!/usr/bin/env python3
"""Convert AssemblyAI structured output to pipeline structured transcript format."""
import argparse, json
from pathlib import Path

MEETINGS_DIR = Path(__file__).resolve().parents[1] / "meetings"

def load_meeting_meta(meeting_id):
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"meeting_id": meeting_id, "title": meeting_id, "meeting_date": "", "meeting_type": ""}

def convert(meeting_id, aa_structured_path, out_path):
    aa = json.loads(Path(aa_structured_path).read_text())
    meta = load_meeting_meta(meeting_id)

    turns = []
    for i, utt in enumerate(aa.get("utterances", [])):
        speaker = utt.get("speaker", "Unknown Speaker")
        is_unknown = speaker.startswith("Unknown")
        turns.append({
            "turn_id": f"turn_{i+1:06d}",
            "start": utt.get("start", 0),
            "end": utt.get("end", 0),
            "text": utt.get("text", ""),
            "speaker": speaker,
            "speaker_raw": utt.get("speaker_label", "?"),
            "speaker_public": speaker,
            "speaker_status": "unresolved" if is_unknown else "resolved",
            "needs_review": is_unknown,
            "review_reason": "" if not is_unknown else "AssemblyAI could not identify speaker",
            "confidence": 1.0 if not is_unknown else 0.0,
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
    ap.add_argument("--aa-structured")
    ap.add_argument("--out")
    args = ap.parse_args()
    if not args.aa_structured:
        args.aa_structured = f"pipeline/work/{args.meeting_id}/assemblyai_structured.json"
    if not args.out:
        args.out = f"transcripts_structured/{args.meeting_id}.json"
    convert(args.meeting_id, args.aa_structured, args.out)
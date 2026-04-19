from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .utils import hhmmss, norm_ws, read_json, write_json


@dataclass
class DiarSeg:
    start: float
    end: float
    speaker: str


def _load_diar(path: Path) -> list[DiarSeg]:
    obj = read_json(path)
    segs = obj.get("segments") or []
    out: list[DiarSeg] = []
    for s in segs:
        try:
            start = float(s["start"])
            end = float(s["end"])
            sp = str(s["speaker"]).strip()
            if not sp or end <= start:
                continue
            out.append(DiarSeg(start=start, end=end, speaker=sp))
        except Exception:
            continue
    out.sort(key=lambda x: (x.start, x.end))
    return out


def _speaker_at(t: float, segs: list[DiarSeg], state: dict[str, Any]) -> str:
    """Return a best-effort active speaker at time t.

    We keep a small rolling active set to handle overlaps without scanning the full list.
    """
    i = int(state.get("i", 0))
    active: list[DiarSeg] = state.get("active", [])

    # Drop ended segments.
    active = [s for s in active if s.end > t]

    # Add segments that start before/at t.
    while i < len(segs) and segs[i].start <= t:
        if segs[i].end > t:
            active.append(segs[i])
        i += 1

    state["i"] = i
    state["active"] = active

    if not active:
        return "UNKNOWN"
    # Choose the segment with the longest duration as a heuristic.
    best = max(active, key=lambda s: (s.end - s.start))
    return best.speaker


def _join_words(words: list[str]) -> str:
    out = ""
    for w in words:
        w = str(w)
        if not w:
            continue
        if not out:
            out = w
            continue
        if w.startswith("'"):
            out += w
        elif w in {".", ",", "!", "?", ":", ";"}:
            out += w
        elif w.startswith(".") or w.startswith(","):
            out += w
        else:
            out += " " + w
    return norm_ws(out)


def _load_registry(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    obj = read_json(path)
    speakers = obj.get("speakers") if isinstance(obj, dict) else None
    if not isinstance(speakers, list):
        return {}
    by_key: dict[str, dict[str, Any]] = {}
    for s in speakers:
        try:
            key = str(s.get("speaker_key") or "").strip()
            if not key:
                continue
            by_key[key] = dict(s)
        except Exception:
            continue
    return by_key


def _load_corrections(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = read_json(path)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Merge ASR + diarization into structured JSON")
    ap.add_argument("--meeting-id", required=True)
    ap.add_argument("--asr", required=True, help="ASR JSON (expects words[])")
    ap.add_argument("--diarization", required=True, help="Diarization JSON (segments[])")
    ap.add_argument("--out", default="merged/segments.json")
    ap.add_argument("--registry", default="/repo/speaker_registry/speakers.json")
    ap.add_argument("--corrections", default="")
    ap.add_argument("--max-seconds", type=float, default=35.0)
    ap.add_argument("--max-gap", type=float, default=1.2)
    args = ap.parse_args()

    asr_path = Path(args.asr)
    diar_path = Path(args.diarization)

    asr = read_json(asr_path)
    diar = _load_diar(diar_path)

    words = asr.get("words") or []
    if not isinstance(words, list) or not words:
        raise SystemExit("ASR JSON missing words[] (run faster-whisper with word_timestamps)")

    registry = _load_registry(Path(args.registry))

    corr_path = Path(args.corrections) if args.corrections else Path(f"/repo/corrections/{args.meeting_id}.json")
    corrections = _load_corrections(corr_path)
    speaker_map = corrections.get("speaker_map") or {}
    if not isinstance(speaker_map, dict):
        speaker_map = {}

    # Build speaker-separated blocks.
    blocks: list[dict[str, Any]] = []
    state: dict[str, Any] = {"i": 0, "active": []}

    cur = None
    for w in words:
        try:
            ws = float(w.get("start"))
            we = float(w.get("end"))
            word = str(w.get("word") or "").strip()
        except Exception:
            continue
        if not word:
            continue
        mid = (ws + we) / 2.0 if we > ws else ws
        sp = _speaker_at(mid, diar, state)

        if cur is None:
            cur = {"speaker_id": sp, "start": ws, "end": we, "words": [word]}
            continue

        gap = ws - float(cur["end"])
        dur = float(cur["end"]) - float(cur["start"])

        # split on speaker change, long gaps, or max duration.
        if sp != cur["speaker_id"] or gap > args.max_gap or dur >= args.max_seconds:
            blocks.append(cur)
            cur = {"speaker_id": sp, "start": ws, "end": we, "words": [word]}
        else:
            cur["end"] = we
            cur["words"].append(word)

    if cur is not None:
        blocks.append(cur)

    # Apply identification (corrections first, then registry).
    segments_out: list[dict[str, Any]] = []
    for idx, b in enumerate(blocks):
        speaker_id = str(b["speaker_id"])
        speaker_key = ""
        speaker_conf = 0.0
        review_reason = ""

        if speaker_id in speaker_map:
            m = speaker_map.get(speaker_id) or {}
            speaker_key = str(m.get("speaker_key") or "").strip()
            speaker_conf = float(m.get("confidence") or 1.0)
            review_reason = str(m.get("reason") or "manual_mapping").strip()

        reg = registry.get(speaker_key) if speaker_key else None
        if reg:
            speaker_name = str(reg.get("display_name") or reg.get("name") or "Unknown Speaker")
            speaker_role = str(reg.get("role") or "unknown")
        else:
            speaker_name = "Unknown Speaker"
            speaker_role = "unknown"
            if speaker_id != "UNKNOWN":
                review_reason = review_reason or "unmapped_known_speaker_id"
            else:
                review_reason = review_reason or "no_diarization"

        text = _join_words(b["words"]).strip()
        needs_review = (speaker_name == "Unknown Speaker") or (speaker_conf < 0.85)

        segments_out.append(
            {
                "segment_id": f"seg_{idx+1:06d}",
                "start_seconds": float(b["start"]),
                "end_seconds": float(b["end"]),
                "timestamp_label": hhmmss(float(b["start"])),
                "speaker_id": speaker_id,
                "speaker_name": speaker_name,
                "speaker_role": speaker_role,
                "speaker_confidence": float(round(speaker_conf, 3)),
                "text": text,
                "needs_review": bool(needs_review),
                "review_reason": review_reason or ("low_confidence" if speaker_conf < 0.85 else ""),
            }
        )

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = Path.cwd() / out_path

    write_json(
        out_path,
        {
            "meeting_id": args.meeting_id,
            "asr_path": str(asr_path),
            "diarization_path": str(diar_path),
            "corrections_path": str(corr_path) if corr_path.exists() else "",
            "segments": segments_out,
        },
    )

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.publish_meeting import write_turns_js, write_transcript_html  # type: ignore
from scripts.build_search_index import build  # type: ignore
from scripts.publish_meeting import load_meeting  # type: ignore


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
    return re.sub(r"\s+", " ", out).strip()


def load_words(asr_path: Path) -> list[dict[str, Any]]:
    obj = json.loads(asr_path.read_text(encoding="utf-8"))
    words = obj.get("word_segments") or obj.get("words") or []
    out: list[dict[str, Any]] = []
    for word in words:
        try:
            start = float(word.get("start"))
            end = float(word.get("end"))
            token = str(word.get("word") or "").strip()
        except Exception:
            continue
        if not token:
            continue
        out.append({"start": start, "end": end, "word": token})
    return out


def load_diarization(path: Path) -> list[dict[str, Any]]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    segs = obj.get("segments") or []
    out = []
    for seg in segs:
        try:
            start = float(seg.get("start"))
            end = float(seg.get("end"))
            speaker = str(seg.get("speaker") or "").strip()
        except Exception:
            continue
        if not speaker or end <= start:
            continue
        out.append({"start": start, "end": end, "speaker": speaker})
    out.sort(key=lambda s: (s["start"], s["end"], s["speaker"]))
    return out


def load_approvals(path: Path) -> dict[str, dict[str, Any]]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj if isinstance(obj, dict) else {}


def speaker_at(t: float, segs: list[dict[str, Any]], state: dict[str, Any]) -> str:
    idx = state.get("idx", 0)
    active = state.get("active", [])
    active = [seg for seg in active if seg["end"] > t]
    while idx < len(segs) and segs[idx]["start"] <= t:
        if segs[idx]["end"] > t:
            active.append(segs[idx])
        idx += 1
    state["idx"] = idx
    state["active"] = active
    if not active:
        return "UNKNOWN"
    best = max(active, key=lambda seg: (seg["end"] - seg["start"]))
    return str(best["speaker"])


def main() -> int:
    ap = argparse.ArgumentParser(description="Build transcript page from WhisperX + diarization + manual approvals")
    ap.add_argument("meeting_id")
    ap.add_argument("--asr", required=True)
    ap.add_argument("--diarization", required=True)
    ap.add_argument("--approvals", required=True)
    ap.add_argument("--out-data", required=True)
    ap.add_argument("--out-html", required=True)
    ap.add_argument("--max-gap", type=float, default=1.2)
    ap.add_argument("--max-seconds", type=float, default=35.0)
    ap.add_argument("--max-chars", type=int, default=650)
    args = ap.parse_args()

    meeting = load_meeting(args.meeting_id)
    words = load_words(Path(args.asr))
    diar = load_diarization(Path(args.diarization))
    approvals = load_approvals(Path(args.approvals))

    state: dict[str, Any] = {"idx": 0, "active": []}
    tagged_words = []
    for word in words:
        mid = (word["start"] + word["end"]) / 2.0 if word["end"] > word["start"] else word["start"]
        tagged_words.append(word | {"speaker_id": speaker_at(mid, diar, state)})

    segments = []
    cur = None
    for word in tagged_words:
        if cur is None:
            cur = {
                "speaker_id": word["speaker_id"],
                "start": word["start"],
                "end": word["end"],
                "words": [word["word"]],
            }
            continue

        gap = word["start"] - cur["end"]
        duration = cur["end"] - cur["start"]
        prospective = join_words(cur["words"] + [word["word"]])
        if (
            word["speaker_id"] != cur["speaker_id"]
            or gap > args.max_gap
            or duration >= args.max_seconds
            or (len(prospective) >= args.max_chars and prospective.endswith((".", "!", "?")))
        ):
            segments.append(cur)
            cur = {
                "speaker_id": word["speaker_id"],
                "start": word["start"],
                "end": word["end"],
                "words": [word["word"]],
            }
        else:
            cur["end"] = word["end"]
            cur["words"].append(word["word"])
    if cur is not None:
        segments.append(cur)

    generic_labels: dict[str, str] = {}
    next_generic = 1
    turns = []
    for seg in segments:
        speaker_id = seg["speaker_id"]
        approval = approvals.get(speaker_id, {})
        status = str(approval.get("status") or "").strip()
        approved_name = str(approval.get("name") or "").strip()

        if status == "approved" and approved_name:
            speaker = approved_name
            speaker_source = "manual_review"
            speaker_source_detail = "Human verified speaker ID"
        elif status.startswith("rejected") or speaker_id == "UNKNOWN":
            speaker = "Unknown Speaker"
            speaker_source = "unknown"
            speaker_source_detail = ""
        else:
            if speaker_id not in generic_labels:
                generic_labels[speaker_id] = f"Speaker {next_generic:02d}"
                next_generic += 1
            speaker = generic_labels[speaker_id]
            speaker_source = "diarization"
            speaker_source_detail = f"Verified turn boundary, unresolved identity ({speaker_id})"

        text = join_words(seg["words"])
        turns.append(
            {
                "speaker": speaker,
                "speaker_source": speaker_source,
                "speaker_source_detail": speaker_source_detail,
                "start": round(float(seg["start"]), 3),
                "end": round(float(seg["end"]), 3),
                "text": text[:1].upper() + text[1:] if text else text,
            }
        )

    out_data = Path(args.out_data)
    out_html = Path(args.out_html)
    write_turns_js(args.meeting_id, turns, out_data)
    write_transcript_html(meeting, out_html)
    build()

    print(f"turns={len(turns)}")
    print(out_data)
    print(out_html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

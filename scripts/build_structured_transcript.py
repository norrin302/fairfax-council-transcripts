#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.publish_meeting import load_meeting  # type: ignore


@dataclass
class DiarSeg:
    start: float
    end: float
    speaker: str


_FILLER_TURNS = {
    "oh",
    "uh",
    "um",
    "hmm",
    "mm",
    "mhm",
    "yeah",
    "yes",
    "no",
    "okay",
    "ok",
    "aye",
    "second",
    "all right",
    "thank you",
    "i",
    "i i",
    "♪♪",
}


def _load_diar(path: Path) -> list[DiarSeg]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    segs = obj.get("segments") if isinstance(obj, dict) else None
    if not isinstance(segs, list):
        raise SystemExit(f"Diarization JSON missing segments[]: {path}")
    out: list[DiarSeg] = []
    for seg in segs:
        try:
            start = float(seg.get("start"))
            end = float(seg.get("end"))
            speaker = str(seg.get("speaker") or "").strip()
        except Exception:
            continue
        if not speaker or end <= start:
            continue
        out.append(DiarSeg(start=start, end=end, speaker=speaker))
    out.sort(key=lambda s: (s.start, s.end, s.speaker))
    return out


def _speaker_at(t: float, segs: list[DiarSeg], state: dict[str, Any]) -> str:
    idx = int(state.get("idx", 0))
    active: list[DiarSeg] = state.get("active", [])
    active = [s for s in active if s.end > t]
    while idx < len(segs) and segs[idx].start <= t:
        if segs[idx].end > t:
            active.append(segs[idx])
        idx += 1
    state["idx"] = idx
    state["active"] = active
    if not active:
        return "UNKNOWN"
    best = max(active, key=lambda s: (s.end - s.start))
    return best.speaker


def _load_asr_units(asr_path: Path) -> list[dict[str, Any]]:
    obj = json.loads(asr_path.read_text(encoding="utf-8"))

    words = obj.get("word_segments") or obj.get("words") or []
    if isinstance(words, list) and words:
        out: list[dict[str, Any]] = []
        for w in words:
            try:
                start = float(w.get("start"))
                end = float(w.get("end"))
                word = str(w.get("word") or "").strip()
            except Exception:
                continue
            if not word:
                continue
            out.append({"start": start, "end": end, "text": word, "unit": "word"})
        if out:
            return out

    segments = obj.get("segments") or []
    if isinstance(segments, list) and segments:
        out = []
        for seg in segments:
            try:
                start = float(seg.get("start"))
                end = float(seg.get("end"))
                text = str(seg.get("text") or "").strip()
            except Exception:
                continue
            if not text or end <= start:
                continue
            out.append({"start": start, "end": end, "text": text, "unit": "segment"})
        if out:
            return out

    raise SystemExit(f"ASR JSON missing word_segments[]/words[]/segments[]: {asr_path}")


def _join_tokens(parts: list[str]) -> str:
    out = ""
    for w in parts:
        if not w:
            continue
        if not out:
            out = w
        elif w.startswith("'"):
            out += w
        elif w in {".", ",", "!", "?", ":", ";"} or w.startswith(".") or w.startswith(","):
            out += w
        else:
            out += " " + w
    return re.sub(r"\s+", " ", out).strip()


def _cleanup_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return ""

    text = re.sub(r"\b([A-Za-z]+)(?:\s+\1\b){2,}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(all right)(?:,?\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(thank you)(?:,?\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(come)(?:\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(play)\s+a\s+little\s+bit\s+of\s+the\s+pledge\s+of\s+allegiance\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bit's a little bit of the pledge of allegiance\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:i[\.,!?]?\s+)+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bi\s+(?=will\b|am\b|move\b|think\b|want\b|would\b)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,.;:!?]){2,}", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip(" ,")

    if re.fullmatch(r"[♪\s]+", text):
        return ""

    if text:
        text = text[:1].upper() + text[1:]
    return text


def _load_approvals(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        return {}
    if isinstance(obj.get("approvals"), dict):
        return obj["approvals"]
    return obj


def _public_label_policy(speaker_raw: str, approvals: dict[str, dict[str, Any]]) -> tuple[str, str, bool, str]:
    a = approvals.get(speaker_raw) or {}
    status = str(a.get("status") or "").strip()
    name = str(a.get("name") or "").strip()

    if status == "approved" and name:
        return name, "approved", False, ""

    if status.startswith("rejected") or status == "mixed":
        return "Unknown Speaker", "mixed", True, "mixed_or_rejected_audio"

    if speaker_raw == "UNKNOWN":
        return "Unknown Speaker", "unknown", True, "no_diarization"

    return "Unknown Speaker", "unresolved", True, "unresolved_identity"


def _is_micro_turn(turn: dict[str, Any]) -> bool:
    text = str(turn.get("text") or "").strip()
    if not text:
        return True
    words = text.split()
    if len(words) <= 2:
        normalized = re.sub(r"[^a-z]+", " ", text.lower()).strip()
        if normalized in _FILLER_TURNS or len(normalized.split()) <= 2:
            return True
    return False


def _merge_micro_turns(turns: list[dict[str, Any]], max_gap: float) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    i = 0
    while i < len(turns):
        cur = dict(turns[i])
        if _is_micro_turn(cur):
            prev = merged[-1] if merged else None
            nxt = turns[i + 1] if i + 1 < len(turns) else None
            prev_gap = float(cur["start"]) - float(prev["end"]) if prev else 9999.0
            next_gap = float(nxt["start"]) - float(cur["end"]) if nxt else 9999.0

            if prev and prev.get("speaker_raw") == cur.get("speaker_raw") and prev_gap <= max_gap:
                prev["end"] = cur["end"]
                prev["text"] = _cleanup_text(f"{prev['text']} {cur['text']}")
                i += 1
                continue

            if nxt and nxt.get("speaker_raw") == cur.get("speaker_raw") and next_gap <= max_gap:
                nxt = dict(nxt)
                nxt["start"] = cur["start"]
                nxt["text"] = _cleanup_text(f"{cur['text']} {nxt['text']}")
                turns[i + 1] = nxt
                i += 1
                continue

            if prev and prev_gap <= max_gap and cur.get("speaker_status") != "approved":
                prev["end"] = cur["end"]
                prev["text"] = _cleanup_text(f"{prev['text']} {cur['text']}")
                prev["needs_review"] = True
                prev["review_reason"] = prev.get("review_reason") or "merged_micro_turn"
                i += 1
                continue

            if not prev and nxt and next_gap <= max_gap and cur.get("speaker_status") != "approved":
                nxt = dict(nxt)
                nxt["start"] = cur["start"]
                nxt["text"] = _cleanup_text(f"{cur['text']} {nxt['text']}")
                nxt["needs_review"] = True
                nxt["review_reason"] = nxt.get("review_reason") or "merged_leading_micro_turn"
                turns[i + 1] = nxt
                i += 1
                continue

        cur["text"] = _cleanup_text(str(cur.get("text") or ""))
        if cur["text"]:
            merged.append(cur)
        i += 1
    return [t for t in merged if str(t.get("text") or "").strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description="Build structured transcript turns (Phase 1) from ASR + diarization")
    ap.add_argument("meeting_id")
    ap.add_argument("--asr", required=True, help="ASR JSON with word_segments[]/words[] or segments[]")
    ap.add_argument("--diarization", required=True, help="Diarization JSON with segments[]")
    ap.add_argument("--approvals", default="", help="Optional manual approvals JSON mapping diar speaker_id to public names")
    ap.add_argument("--out", required=True, help="Output structured transcript JSON")
    ap.add_argument("--max-gap", type=float, default=2.4)
    ap.add_argument("--max-seconds", type=float, default=42.0)
    ap.add_argument("--max-chars", type=int, default=720)
    args = ap.parse_args()

    meeting = load_meeting(args.meeting_id)
    asr_units = _load_asr_units(Path(args.asr))
    diar = _load_diar(Path(args.diarization))
    approvals = _load_approvals(Path(args.approvals)) if args.approvals else {}

    state: dict[str, Any] = {"idx": 0, "active": []}
    tagged = []
    for u in asr_units:
        mid = (u["start"] + u["end"]) / 2.0 if u["end"] > u["start"] else u["start"]
        tagged.append(u | {"speaker_raw": _speaker_at(mid, diar, state)})

    turns: list[dict[str, Any]] = []
    cur = None
    for u in tagged:
        token = str(u["text"])
        if cur is None:
            cur = {"speaker_raw": u["speaker_raw"], "start": u["start"], "end": u["end"], "parts": [token], "unit": u["unit"]}
            continue

        gap = u["start"] - float(cur["end"])
        dur = float(cur["end"]) - float(cur["start"])
        prospective = _join_tokens(cur["parts"] + [token])
        same_speaker = u["speaker_raw"] == cur["speaker_raw"]
        same_mode = u["unit"] == cur["unit"]

        should_split = (
            not same_speaker
            or not same_mode
            or gap > args.max_gap
            or dur >= args.max_seconds
            or (len(prospective) >= args.max_chars and prospective.endswith((".", "!", "?")))
        )

        if should_split:
            turns.append(cur)
            cur = {"speaker_raw": u["speaker_raw"], "start": u["start"], "end": u["end"], "parts": [token], "unit": u["unit"]}
        else:
            cur["end"] = u["end"]
            cur["parts"].append(token)

    if cur is not None:
        turns.append(cur)

    structured_turns: list[dict[str, Any]] = []
    for i, t in enumerate(turns):
        speaker_public, speaker_status, needs_review, reason = _public_label_policy(str(t["speaker_raw"]), approvals)
        text = _cleanup_text(_join_tokens(t["parts"]))
        structured_turns.append(
            {
                "turn_id": f"turn_{i+1:06d}",
                "start": round(float(t["start"]), 3),
                "end": round(float(t["end"]), 3),
                "text": text,
                "speaker_raw": str(t["speaker_raw"]),
                "speaker_public": speaker_public,
                "speaker_status": speaker_status,
                "needs_review": bool(needs_review),
                "review_reason": reason,
                "confidence": None,
            }
        )

    structured_turns = _merge_micro_turns(structured_turns, max_gap=max(args.max_gap, 3.0))

    for i, t in enumerate(structured_turns):
        t["turn_id"] = f"turn_{i+1:06d}"

    out = {
        "schema": "fairfax.structured_transcript.v1",
        "meeting": {
            "meeting_id": meeting.get("meeting_id"),
            "meeting_date": meeting.get("meeting_date"),
            "title": meeting.get("title"),
            "source_url": meeting.get("source_video_url") or meeting.get("source_url"),
        },
        "turns": structured_turns,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"turns={len(structured_turns)}")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

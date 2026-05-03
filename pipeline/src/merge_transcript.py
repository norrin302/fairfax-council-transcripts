from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cleanup_blocks import (
    _seg_start as _s_start,
    _seg_end as _s_end,
    _id as _s_id,
    _spk as _s_spk,
    _txt as _s_txt,
    _name as _s_name,
    _role as _s_role,
    _conf as _s_conf,
    _needs_review as _s_nr,
)
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


def _build_speaker_id_to_key_map(
    registry: dict[str, dict[str, Any]],
    corrections_speaker_map: dict[str, Any],
) -> dict[str, tuple[str, float, str]]:
    """Build mapping from raw diarization speaker ID (e.g. SPEAKER_21)
    to (speaker_key, confidence, reason).

    Registry v2 fields used:
      - diarization_speaker_ids: known pyannote IDs for this person
      - confidence_boost: default confidence for named officials
      - text_patterns: name patterns to spot in ASR text

    Corrections take priority over registry.
    """
    speaker_id_to_key: dict[str, tuple[str, float, str]] = {}

    # First: corrections (manual overrides)
    for raw_id, m in corrections_speaker_map.items():
        key = str(m.get("speaker_key", "")).strip()
        conf = float(m.get("confidence", 1.0))
        reason = str(m.get("reason", "manual_mapping")).strip()
        if key:
            speaker_id_to_key[str(raw_id)] = (key, conf, reason)

    # Second: registry diarization_speaker_ids (if not already mapped)
    for key, reg in registry.items():
        diar_ids = reg.get("diarization_speaker_ids") or []
        boost = float(reg.get("confidence_boost", 0.0))
        for raw_id in diar_ids:
            raw_id = str(raw_id).strip()
            if raw_id and raw_id not in speaker_id_to_key:
                speaker_id_to_key[raw_id] = (key, boost, "diarization_speaker_id_match")

    return speaker_id_to_key


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
    ap.add_argument(
        "--min-duration",
        type=float,
        default=1.5,
        help="Minimum duration (s) to avoid microblock cleanup (default: 1.5)",
    )
    ap.add_argument(
        "--dominance-threshold",
        type=float,
        default=0.60,
        help="Fraction of cluster duration required for dominant speaker (default: 0.60)",
    )
    ap.add_argument(
        "--skip-sandwich",
        action="store_true",
        help="Skip the sandwich-attachment pass in cleanup",
    )
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

    # Build raw blocks.
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

    # ---- Stage 1: Microblock cleanup ----
    from .cleanup_blocks import cleanup_segments as _cleanup_segments, attach_to_neighbors as _attach_to_neighbors

    # Convert raw blocks to Segment dataclass-compatible dicts for cleanup
    segs_for_cleanup = [
        {
            "segment_id": f"seg_{i+1:06d}",
            "start": float(b["start"]),
            "end": float(b["end"]),
            "speaker_id": str(b["speaker_id"]),
            "text": " ".join(b["words"]),
            "speaker_name": "Unknown Speaker",
            "speaker_role": "unknown",
            "speaker_confidence": 0.0,
            "needs_review": False,
            "review_reason": "",
        }
        for i, b in enumerate(blocks)
    ]

    min_dur = float(getattr(args, "min_duration", 1.5) or 1.5)
    dom_thresh = float(getattr(args, "dominance_threshold", 0.60) or 0.60)

    cleaned_segs = _cleanup_segments(
        segs_for_cleanup,
        min_duration=min_dur,
        dominance_threshold=dom_thresh,
    )
    if not getattr(args, "skip_sandwich", False):
        cleaned_segs = _attach_to_neighbors(cleaned_segs)

    # ---- Stage 2: Build speaker ID -> speaker_key map ----
    speaker_id_to_key = _build_speaker_id_to_key_map(registry, corrections.get("speaker_map", {}))

    # ---- Stage 3: Apply identification to cleaned segments ----
    segments_out: list[dict[str, Any]] = []
    for idx, seg in enumerate(cleaned_segs):
        raw_id = str(seg.get("speaker_id", ""))
        cleanup_action = str(seg.get("cleanup_action", "kept"))

        # Lookup via corrections + registry
        speaker_key = ""
        speaker_conf = 0.0
        review_reason = str(seg.get("review_reason") or "")

        if raw_id in speaker_id_to_key:
            speaker_key, speaker_conf, map_reason = speaker_id_to_key[raw_id]
            if not review_reason:
                review_reason = map_reason

        reg = registry.get(speaker_key) if speaker_key else None
        if reg:
            speaker_name = str(reg.get("display_name") or "Unknown Speaker")
            speaker_role = str(reg.get("role") or "unknown")
        else:
            speaker_name = "Unknown Speaker"
            speaker_role = "unknown"
            if raw_id != "UNKNOWN" and not review_reason:
                review_reason = review_reason or "unmapped_diarization_id"

        text = str(seg.get("text", "")).strip()
        needs_review = (
            bool(seg.get("needs_review", False))
            or speaker_name == "Unknown Speaker"
            or speaker_conf < 0.85
        )

        segments_out.append(
            {
                "segment_id": _s_id(seg) or str(f"seg_{idx+1:06d}"),
                "start_seconds": _s_start(seg),
                "end_seconds": _s_end(seg),
                "timestamp_label": hhmmss(_s_start(seg)),
                "speaker_id": raw_id,
                "speaker_name": speaker_name,
                "speaker_role": speaker_role,
                "speaker_confidence": float(round(speaker_conf, 3)),
                "text": _s_txt(seg).strip(),
                "needs_review": needs_review,
                "review_reason": review_reason,
                # Audit fields from cleanup
                "cleanup_action": cleanup_action,
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


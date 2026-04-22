#!/usr/bin/env python3
"""Three-stage benchmark for apr-14-2026 pipeline.

Stage 1: Baseline merge (no cleanup, no registry) — raw pyannote IDs as speaker_name
Stage 2: Cleanup only (no registry) — same raw IDs, cleanup applied
Stage 3: Cleanup + registry v2 mapping — canonical names

Evaluation: per gold-set excerpt + overall.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cleanup_blocks import cleanup_segments, attach_to_neighbors

# ---------------------------------------------------------------------------
# Minimal helpers (duplicated from merge_transcript/utils to keep benchmark self-contained)
# ----------------------------------------------------------------------------

def hhmmss(seconds: float) -> str:
    s = max(0, int(math.floor(float(seconds or 0))))
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"


def norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


@dataclass
class DiarSeg:
    start: float
    end: float
    speaker: str


def _load_diar(path: Path) -> list[DiarSeg]:
    obj = read_json(path)
    segs = obj.get("segments", []) if isinstance(obj, dict) else obj
    out = []
    for s in segs:
        try:
            out.append(DiarSeg(
                start=float(s["start"]),
                end=float(s["end"]),
                speaker=str(s.get("speaker", "UNKNOWN") or "UNKNOWN"),
            ))
        except Exception:
            continue
    out.sort(key=lambda x: x.start)
    return out


def _speaker_at(t: float, diar: list[DiarSeg], state: dict[str, Any]) -> str:
    active = state.get("active", [])
    i = state.get("i", 0)
    # advance pointer
    while i < len(diar):
        seg = diar[i]
        if seg.end <= t:
            i += 1
        else:
            break
    state["i"] = i
    state["active"] = [s for s in active if s.end > t]
    if i < len(diar) and diar[i].start <= t < diar[i].end:
        state["active"].append(diar[i])
    if not state["active"]:
        return "UNKNOWN"
    # return the speaker with the longest overlap so far
    best = max(state["active"], key=lambda s: min(s.end, t) - max(s.start, t))
    return best.speaker


# ---------------------------------------------------------------------------
# Registry helpers (duplicated from merge_transcript to keep benchmark self-contained)
# ----------------------------------------------------------------------------

def _load_registry(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    obj = json.loads(path.read_text(encoding="utf-8"))
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
    speaker_id_to_key: dict[str, tuple[str, float, str]] = {}
    for raw_id, m in corrections_speaker_map.items():
        key = str(m.get("speaker_key", "")).strip()
        conf = float(m.get("confidence", 1.0))
        reason = str(m.get("reason", "manual_mapping")).strip()
        if key:
            speaker_id_to_key[str(raw_id)] = (key, conf, reason)
    for key, reg in registry.items():
        diar_ids = reg.get("diarization_speaker_ids") or []
        boost = float(reg.get("confidence_boost", 0.0))
        for raw_id in diar_ids:
            raw_id = str(raw_id).strip()
            if raw_id and raw_id not in speaker_id_to_key:
                speaker_id_to_key[raw_id] = (key, boost, "diarization_speaker_id_match")
    return speaker_id_to_key


# ---------------------------------------------------------------------------
# Gold set loader
# ---------------------------------------------------------------------------
def load_gold_set(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    excerpts = {}
    for ex in obj.get("excerpts", []):
        excerpts[ex["excerpt_id"]] = ex
    return {
        "excerpts": excerpts,
        "total_turns": sum(len(ex.get("turns", [])) for ex in obj.get("excerpts", [])),
    }


# ---------------------------------------------------------------------------
# Merge (raw, no cleanup, no registry)
# ---------------------------------------------------------------------------
def merge_raw(
    words: list[dict],
    diar: list[dict],
    max_gap: float = 1.2,
    max_seconds: float = 35.0,
) -> list[dict[str, Any]]:
    """Standard merge without cleanup or registry."""
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

        if sp != cur["speaker_id"] or gap > max_gap or dur >= max_seconds:
            blocks.append(cur)
            cur = {"speaker_id": sp, "start": ws, "end": we, "words": [word]}
        else:
            cur["end"] = we
            cur["words"].append(word)

    if cur is not None:
        blocks.append(cur)

    # Convert to output format (no registry, no cleanup)
    out = []
    for idx, b in enumerate(blocks):
        ws = float(b["start"])
        we = float(b["end"])
        sp = str(b["speaker_id"])
        text = " ".join(b["words"]).strip()
        needs_review = (sp == "UNKNOWN")

        out.append({
            "segment_id": f"seg_{idx+1:06d}",
            "start_seconds": ws,
            "end_seconds": we,
            "speaker_id": sp,
            "speaker_name": "Unknown Speaker" if sp == "UNKNOWN" else sp,
            "speaker_role": "unknown",
            "speaker_confidence": 0.0,
            "text": text,
            "needs_review": needs_review,
            "review_reason": "no_diarization" if sp == "UNKNOWN" else "",
            "cleanup_action": "kept",
        })
    return out


# ---------------------------------------------------------------------------
# Merge with cleanup, no registry
# ---------------------------------------------------------------------------
def merge_with_cleanup(
    words: list[dict],
    diar: list[dict],
    max_gap: float = 1.2,
    max_seconds: float = 35.0,
    min_duration: float = 1.5,
    dominance_threshold: float = 0.60,
) -> list[dict[str, Any]]:
    """Merge with cleanup applied, but no registry mapping."""
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

        if sp != cur["speaker_id"] or gap > max_gap or dur >= max_seconds:
            blocks.append(cur)
            cur = {"speaker_id": sp, "start": ws, "end": we, "words": [word]}
        else:
            cur["end"] = we
            cur["words"].append(word)

    if cur is not None:
        blocks.append(cur)

    # Build Segment-compatible dicts for cleanup
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

    cleaned = cleanup_segments(segs_for_cleanup, min_duration, dominance_threshold)
    cleaned = attach_to_neighbors(cleaned)

    # Convert to output (no registry mapping, keep raw IDs)
    out = []
    for seg in cleaned:
        ws = seg.get("start_seconds", seg.get("start", 0))
        we = seg.get("end_seconds", seg.get("end", 0))
        sp = str(seg.get("speaker_id", "UNKNOWN"))
        text = str(seg.get("text", "")).strip()
        needs_review = seg.get("needs_review", False) or sp == "UNKNOWN"

        out.append({
            "segment_id": seg.get("segment_id", "?"),
            "start_seconds": float(ws),
            "end_seconds": float(we),
            "speaker_id": sp,
            "speaker_name": "Unknown Speaker" if sp == "UNKNOWN" else sp,
            "speaker_role": "unknown",
            "speaker_confidence": float(seg.get("speaker_confidence", 0.0)),
            "text": text,
            "needs_review": needs_review,
            "review_reason": seg.get("review_reason", ""),
            "cleanup_action": seg.get("cleanup_action", "kept"),
        })
    return out


# ---------------------------------------------------------------------------
# Merge with cleanup + registry
# ---------------------------------------------------------------------------
def merge_with_cleanup_and_registry(
    words: list[dict],
    diar: list[dict],
    registry_path: Path,
    max_gap: float = 1.2,
    max_seconds: float = 35.0,
    min_duration: float = 1.5,
    dominance_threshold: float = 0.60,
) -> list[dict[str, Any]]:
    """Full pipeline: merge + cleanup + registry mapping."""
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

        if sp != cur["speaker_id"] or gap > max_gap or dur >= max_seconds:
            blocks.append(cur)
            cur = {"speaker_id": sp, "start": ws, "end": we, "words": [word]}
        else:
            cur["end"] = we
            cur["words"].append(word)

    if cur is not None:
        blocks.append(cur)

    # Cleanup
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

    cleaned = cleanup_segments(segs_for_cleanup, min_duration, dominance_threshold)
    cleaned = attach_to_neighbors(cleaned)

    # Registry
    registry = _load_registry(registry_path)
    corrections_speaker_map = {}
    speaker_id_to_key = _build_speaker_id_to_key_map(registry, corrections_speaker_map)

    # Apply identification
    out = []
    for seg in cleaned:
        ws = seg.get("start_seconds", seg.get("start", 0))
        we = seg.get("end_seconds", seg.get("end", 0))
        raw_id = str(seg.get("speaker_id", ""))
        cleanup_action = str(seg.get("cleanup_action", "kept"))
        review_reason = str(seg.get("review_reason") or "")

        speaker_key = ""
        speaker_conf = 0.0

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

        out.append({
            "segment_id": seg.get("segment_id", "?"),
            "start_seconds": float(ws),
            "end_seconds": float(we),
            "speaker_id": raw_id,
            "speaker_name": speaker_name,
            "speaker_role": speaker_role,
            "speaker_confidence": float(round(speaker_conf, 3)),
            "text": text,
            "needs_review": needs_review,
            "review_reason": review_reason,
            "cleanup_action": cleanup_action,
        })
    return out


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def evaluate_stage(
    stage_name: str,
    candidate_segments: list[dict],
    gold: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate candidate segments against gold set.

    For each gold turn, find the candidate segment that overlaps
    the most with the gold turn's time range, then compare names.
    """
    # Build lookup: for each second, find segment at that time
    # Use interval tree: for each gold turn, find best overlapping candidate
    excerpt_metrics = []
    total_wrong = 0
    total_unknown_when_named = 0
    total_match = 0
    total_gold_named = 0
    total_gold_unknown = 0
    total_turns = 0

    for ex_id, excerpt in gold["excerpts"].items():
        gold_turns = excerpt.get("turns", [])
        ex_wrong = 0
        ex_unknown_when_named = 0
        ex_match = 0
        ex_gold_named = 0
        ex_gold_unknown = 0

        for gt in gold_turns:
            g_start = float(gt["start"])
            g_end = float(gt["end"])
            g_name = gt.get("speaker_name", "Unknown Speaker")

            if g_name not in ("Unknown Speaker", "Unknown"):
                gold_is_named = True
                ex_gold_named += 1
            else:
                gold_is_named = False
                ex_gold_unknown += 1

            # Find best overlapping candidate segment
            best_seg = None
            best_overlap = 0.0
            for seg in candidate_segments:
                s_start = float(seg["start_seconds"])
                s_end = float(seg["end_seconds"])
                overlap_start = max(g_start, s_start)
                overlap_end = min(g_end, s_end)
                overlap = max(0.0, overlap_end - overlap_start)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_seg = seg

            c_name = best_seg["speaker_name"] if best_seg else "Unknown Speaker"
            total_turns += 1

            if c_name == g_name:
                ex_match += 1
            elif gold_is_named and c_name == "Unknown Speaker":
                ex_unknown_when_named += 1
                ex_wrong += 1
            elif gold_is_named and c_name != "Unknown Speaker" and c_name != g_name:
                # Wrong specific name
                ex_wrong += 1
            # else: gold is Unknown, pipeline is Unknown = correct conservative (don't count as wrong)

        total_match += ex_match
        total_wrong += ex_wrong
        total_unknown_when_named += ex_unknown_when_named
        total_gold_named += ex_gold_named
        total_gold_unknown += ex_gold_unknown

        ex_total = len(gold_turns)
        excerpt_metrics.append({
            "excerpt_id": ex_id,
            "match_rate": round(ex_match / ex_total, 4) if ex_total else 0,
            "wrong": ex_wrong,
            "unknown_when_named": ex_unknown_when_named,
            "total": ex_total,
            "gold_named": ex_gold_named,
            "gold_unknown": ex_gold_unknown,
        })

    n = total_turns
    return {
        "stage": stage_name,
        "total_turns": n,
        "match_rate": round(total_match / n, 4) if n else 0,
        "wrong_count": total_wrong,
        "unknown_when_named_count": total_unknown_when_named,
        "gold_named_total": total_gold_named,
        "gold_unknown_total": total_gold_unknown,
        "per_excerpt": excerpt_metrics,
    }


# ---------------------------------------------------------------------------
# Review burden
# ---------------------------------------------------------------------------
def compute_review_burden(segments: list[dict]) -> dict[str, Any]:
    total = len(segments)
    needs_review = sum(1 for s in segments if s.get("needs_review"))
    actions = defaultdict(int)
    for s in segments:
        actions[s.get("cleanup_action", "kept")] += 1
    return {
        "total": total,
        "needs_review": needs_review,
        "review_rate": round(needs_review / total, 4) if total else 0,
        "actions": dict(actions),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="Three-stage pipeline benchmark")
    ap.add_argument("--asr", required=True, help="ASR JSON path")
    ap.add_argument("--diarization", required=True, help="Diarization JSON path")
    ap.add_argument("--registry", required=True, help="Speaker registry JSON path")
    ap.add_argument("--gold-set", required=True, help="Gold set JSON path")
    ap.add_argument("--structured", required=True, help="Structured transcript JSON (for truth reference)")
    ap.add_argument("--out", required=True, help="Output report JSON path")
    ap.add_argument("--max-gap", type=float, default=1.2)
    ap.add_argument("--max-seconds", type=float, default=35.0)
    ap.add_argument("--min-duration", type=float, default=1.5)
    ap.add_argument("--dominance-threshold", type=float, default=0.60)
    args = ap.parse_args()

    asr = read_json(Path(args.asr))
    diar = _load_diar(Path(args.diarization))
    words = asr.get("words", [])

    gold = load_gold_set(Path(args.gold_set))
    registry_path = Path(args.registry)

    print("=== Stage 1: Baseline merge (raw pyannote IDs) ===")
    stage1 = merge_raw(words, diar, args.max_gap, args.max_seconds)
    print(f"  {len(stage1)} segments")
    eval1 = evaluate_stage("stage1_raw", stage1, gold)
    burden1 = compute_review_burden(stage1)
    print(f"  Match rate: {eval1['match_rate']:.1%} | Wrong: {eval1['wrong_count']} | Unknown-when-named: {eval1['unknown_when_named_count']}")
    print(f"  Review burden: {burden1['needs_review']}/{burden1['total']} ({burden1['review_rate']:.1%})")

    print("\n=== Stage 2: Cleanup only (no registry) ===")
    stage2 = merge_with_cleanup(words, diar, args.max_gap, args.max_seconds, args.min_duration, args.dominance_threshold)
    print(f"  {len(stage2)} segments")
    eval2 = evaluate_stage("stage2_cleanup", stage2, gold)
    burden2 = compute_review_burden(stage2)
    print(f"  Match rate: {eval2['match_rate']:.1%} | Wrong: {eval2['wrong_count']} | Unknown-when-named: {eval2['unknown_when_named_count']}")
    print(f"  Review burden: {burden2['needs_review']}/{burden2['total']} ({burden2['review_rate']:.1%})")

    print("\n=== Stage 3: Cleanup + Registry v2 mapping ===")
    stage3 = merge_with_cleanup_and_registry(
        words, diar, registry_path,
        args.max_gap, args.max_seconds,
        args.min_duration, args.dominance_threshold,
    )
    print(f"  {len(stage3)} segments")
    eval3 = evaluate_stage("stage3_full", stage3, gold)
    burden3 = compute_review_burden(stage3)
    print(f"  Match rate: {eval3['match_rate']:.1%} | Wrong: {eval3['wrong_count']} | Unknown-when-named: {eval3['unknown_when_named_count']}")
    print(f"  Review burden: {burden3['needs_review']}/{burden3['total']} ({burden3['review_rate']:.1%})")

    # Print per-excerpt breakdown for stage 3
    print("\nStage 3 per-excerpt:")
    for em in eval3["per_excerpt"]:
        print(f"  {em['excerpt_id']}: match={em['match_rate']:.1%} wrong={em['wrong']} unk_when_named={em['unknown_when_named']}")

    # Summary comparison
    print("\n=== Summary ===")
    print(f"{'Metric':<30} {'Stage 1 (raw)':>15} {'Stage 2 (+cleanup)':>18} {'Stage 3 (+registry)':>18}")
    print("-" * 85)
    print(f"{'Match rate':<30} {eval1['match_rate']:>14.1%} {eval2['match_rate']:>17.1%} {eval3['match_rate']:>17.1%}")
    print(f"{'Wrong attributions':<30} {eval1['wrong_count']:>15} {eval2['wrong_count']:>18} {eval3['wrong_count']:>18}")
    print(f"{'Unknown-when-named':<30} {eval1['unknown_when_named_count']:>15} {eval2['unknown_when_named_count']:>18} {eval3['unknown_when_named_count']:>18}")
    print(f"{'Review burden (needs_review)':<30} {burden1['needs_review']:>15} {burden2['needs_review']:>18} {burden3['needs_review']:>18}")
    print(f"{'Total segments':<30} {len(stage1):>15} {len(stage2):>18} {len(stage3):>18}")

    # Named speaker counts in stage 3
    name_counts = defaultdict(int)
    for s in stage3:
        name_counts[s["speaker_name"]] += 1
    print(f"\nStage 3 named speakers:")
    for name, count in sorted(name_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {name}: {count}")

    report = {
        "stage1_raw": {**eval1, **burden1},
        "stage2_cleanup": {**eval2, **burden2},
        "stage3_full": {**eval3, **burden3},
    }

    write_json(Path(args.out), report)
    print(f"\nReport written: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

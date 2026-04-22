#!/usr/bin/env python3
"""Micro-block cleanup for merged transcript segments.

Problem: pyannote diarization produces many short segments (<1.5s) at speaker
transitions and overlapping speech. When these micro-blocks have no dominant
speaker in the diarization output, they are assigned UNKNOWN.

Solution: a post-merge cleanup pass that:
  1. Identifies consecutive micro-blocks (< min_duration)
  2. Merges them into a single block if one speaker dominates (> threshold)
  3. Otherwise leaves them flagged for human review
  4. Preserves original block IDs for audit traceability

Usage:
  python -m pipeline.src.cleanup_blocks \\
    --merged <input-merged.json> \\
    --out  <output-clean.json> \\
    [--min-duration 1.5] \\
    [--dominance-threshold 0.6]
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------
DEFAULT_MIN_DURATION = 1.5   # seconds; blocks shorter than this are micro-blocks
DEFAULT_DOMINANCE_THRESHOLD = 0.60  # fraction of cluster duration for dominant speaker


# -------------------------------------------------------------------
# Data classes
# -------------------------------------------------------------------
@dataclass
class Segment:
    segment_id: str
    start: float
    end: float
    speaker_id: str
    text: str
    speaker_name: str
    speaker_role: str = "unknown"
    speaker_confidence: float = 0.0
    needs_review: bool = False
    review_reason: str = ""
    # Audit fields (set during cleanup)
    cleanup_action: str = "kept"  # "kept" | "merged_into" | "kept_review" | "sandwich_attached"
    original_ids: list[str] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


# -------------------------------------------------------------------
# Duck-typed field accessors (works with Segment or plain dict)
# -------------------------------------------------------------------
def _dur(seg) -> float:
    if hasattr(seg, "duration"):
        return seg.duration
    return max(0.0, float(seg.get("end", 0)) - float(seg.get("start", 0)))


def _id(seg) -> str:
    if hasattr(seg, "segment_id"):
        return seg.segment_id
    return str(seg.get("segment_id", ""))


def _spk(seg) -> str:
    if hasattr(seg, "speaker_id"):
        return seg.speaker_id
    return str(seg.get("speaker_id", "UNKNOWN"))


def _txt(seg) -> str:
    if hasattr(seg, "text"):
        return seg.text
    return str(seg.get("text", ""))


def _name(seg) -> str:
    if hasattr(seg, "speaker_name"):
        return seg.speaker_name
    return str(seg.get("speaker_name", "Unknown Speaker"))


def _role(seg) -> str:
    if hasattr(seg, "speaker_role"):
        return seg.speaker_role
    return str(seg.get("speaker_role", "unknown"))


def _conf(seg) -> float:
    if hasattr(seg, "speaker_confidence"):
        return seg.speaker_confidence
    return float(seg.get("speaker_confidence", 0.0))


def _needs_review(seg) -> bool:
    if hasattr(seg, "needs_review"):
        return seg.needs_review
    return bool(seg.get("needs_review", False))


# -------------------------------------------------------------------
# Accessors for start/end (used by merge_transcript for output fields)
# -------------------------------------------------------------------
def _seg_start(seg) -> float:
    """Get segment start time, works with Segment or dict."""
    if hasattr(seg, "start"):
        return float(seg.start)
    return float(seg.get("start_seconds", seg.get("start", 0)))


def _seg_end(seg) -> float:
    """Get segment end time, works with Segment or dict."""
    if hasattr(seg, "end"):
        return float(seg.end)
    return float(seg.get("end_seconds", seg.get("end", 0)))


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _load_merged(path: Path) -> list[dict[str, Any]]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj.get("segments", [])


def _to_segments(blocks: list[dict[str, Any]]) -> list[Segment]:
    out: list[Segment] = []
    for b in blocks:
        try:
            # Accept both raw merge format (start/end) and cleaned format (start_seconds/end_seconds)
            seg = Segment(
                segment_id=str(b.get("segment_id", f"seg_{len(out)+1:06d}")),
                start=float(b.get("start_seconds", b.get("start", 0))),
                end=float(b.get("end_seconds", b.get("end", 0))),
                speaker_id=str(b.get("speaker_id", "UNKNOWN")),
                text=str(b.get("text", "")),
                speaker_name=str(b.get("speaker_name", "Unknown Speaker")),
                speaker_role=str(b.get("speaker_role", "unknown")),
                speaker_confidence=float(b.get("speaker_confidence", 0.0)),
                needs_review=bool(b.get("needs_review", False)),
                review_reason=str(b.get("review_reason", "")),
            )
            out.append(seg)
        except Exception:
            continue
    return out


def _to_dicts(segments: list[Segment]) -> list[dict[str, Any]]:
    return [
        {
            "segment_id": s.segment_id,
            "start_seconds": s.start,
            "end_seconds": s.end,
            "speaker_id": s.speaker_id,
            "speaker_name": s.speaker_name,
            "speaker_role": s.speaker_role,
            "speaker_confidence": round(s.speaker_confidence, 4),
            "text": s.text,
            "needs_review": s.needs_review,
            "review_reason": s.review_reason,
            # Audit
            "cleanup_action": s.cleanup_action,
            "original_segment_ids": s.original_ids,
        }
        for s in segments
    ]


def _join_words(words: list[str]) -> str:
    """Join ASR word tokens into clean text."""
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
    return re.sub(r"\s+", " ", out).strip()


def _merge_text(texts: list[str]) -> str:
    """Merge multiple text fragments with natural spacing."""
    merged = ""
    for t in texts:
        t = t.strip()
        if not t:
            continue
        if not merged:
            merged = t
            continue
        if merged.endswith(" ") or t.startswith(" "):
            merged += t
        else:
            merged += " " + t
    return re.sub(r"\s+", " ", merged).strip()


# -------------------------------------------------------------------
# Core cleanup logic (duck-typed: works with Segment or dict)
# -------------------------------------------------------------------
def cleanup_segments(
    segments: list,
    min_duration: float = DEFAULT_MIN_DURATION,
    dominance_threshold: float = DEFAULT_DOMINANCE_THRESHOLD,
) -> list:
    """Main cleanup pass.

    Works with both list[Segment] and list[dict].
    Returns same type as input (duck-typed throughout).
    """
    input_was_dicts = isinstance(segments, list) and segments and isinstance(segments[0], dict)
    if input_was_dicts:
        segments = _to_segments(segments)

    result: list[Segment] = []
    i = 0

    while i < len(segments):
        seg = segments[i]
        dur = _dur(seg)

        if dur >= min_duration:
            seg.cleanup_action = "kept"
            seg.original_ids = [_id(seg)]
            result.append(seg)
            i += 1
            continue

        # Collect consecutive micro-blocks
        cluster = [seg]
        j = i + 1
        while j < len(segments) and _dur(segments[j]) < min_duration:
            cluster.append(segments[j])
            j += 1

        # Compute per-speaker duration
        speaker_dur: dict[str, float] = {}
        for cseg in cluster:
            sp = _spk(cseg)
            if sp == "UNKNOWN":
                continue
            speaker_dur[sp] = speaker_dur.get(sp, 0.0) + _dur(cseg)

        total_dur = sum(_dur(c) for c in cluster)
        if not speaker_dur or total_dur == 0:
            for cseg in cluster:
                cseg.needs_review = True
                cseg.review_reason = "microblock_deferred"
                cseg.cleanup_action = "kept_review"
                cseg.original_ids = [_id(cseg)]
                result.append(cseg)
            i = j
            continue

        dom_speaker = max(speaker_dur, key=speaker_dur.get)
        dom_dur = speaker_dur[dom_speaker]
        dom_frac = dom_dur / total_dur

        if dom_frac >= dominance_threshold:
            merged = Segment(
                segment_id=_id(cluster[0]),
                start=cluster[0].start,
                end=cluster[-1].end,
                speaker_id=dom_speaker,
                text=_merge_text([_txt(c) for c in cluster]),
                speaker_name=_name(cluster[0]),
                speaker_role=_role(cluster[0]),
                speaker_confidence=dom_frac,
                needs_review=True,
                review_reason="microblock_cleanup",
                cleanup_action="merged_into",
                original_ids=[_id(c) for c in cluster],
            )
            result.append(merged)
        else:
            for cseg in cluster:
                cseg.needs_review = True
                cseg.review_reason = "microblock_deferred"
                cseg.cleanup_action = "kept_review"
                cseg.original_ids = [_id(cseg)]
                result.append(cseg)

        i = j

    if input_was_dicts:
        return _to_dicts(result)
    return result


def attach_to_neighbors(segments: list, max_attach_duration: float = 2.0) -> list:
    """Attach short unknown fragments to same-speaker neighbors (sandwich rule).

    Works with both list[Segment] and list[dict]. Returns same type as input.
    """
    input_was_dicts = isinstance(segments, list) and segments and isinstance(segments[0], dict)
    if input_was_dicts:
        segments = _to_segments(segments)

    result: list[Segment] = []
    i = 0

    while i < len(segments):
        seg = segments[i]
        dur = _dur(seg)

        # Only process micro-blocks still UNKNOWN after cleanup
        if dur >= 1.5 or _spk(seg) != "UNKNOWN":
            result.append(seg)
            i += 1
            continue

        if i > 0 and i < len(segments) - 1:
            prev_seg = segments[i - 1]
            next_seg = segments[i + 1]

            if (
                _spk(prev_seg) == _spk(next_seg)
                and _spk(prev_seg) != "UNKNOWN"
                and _dur(prev_seg) >= 1.5
                and _dur(next_seg) >= 1.5
            ):
                text = _txt(seg).strip()
                is_short = len(text.split()) <= 5
                ends_sentence = text.endswith((".", "!", "?", ":", ",", '"'))

                if is_short and not ends_sentence:
                    seg.speaker_id = _spk(prev_seg)
                    seg.speaker_name = _name(prev_seg)
                    seg.speaker_role = _role(prev_seg)
                    seg.speaker_confidence = 0.5
                    seg.review_reason = "sandwich_attached"
                    seg.cleanup_action = "sandwich_attached"
                    seg.original_ids = [_id(seg)]
                    result.append(seg)
                    i += 1
                    continue

        result.append(seg)
        i += 1

    if input_was_dicts:
        return _to_dicts(result)
    return result


# -------------------------------------------------------------------
# Metrics reporting (duck-typed)
# -------------------------------------------------------------------
def compute_metrics(segments: list) -> dict[str, Any]:
    total = len(segments)
    unknown = sum(1 for s in segments if _spk(s) == "UNKNOWN")
    needs_review = sum(1 for s in segments if _needs_review(s))
    actions: dict[str, int] = {
        "kept": 0,
        "merged_into": 0,
        "kept_review": 0,
        "sandwich_attached": 0,
    }
    for s in segments:
        act = s.cleanup_action if hasattr(s, "cleanup_action") else str(s.get("cleanup_action", "kept"))
        actions[act] = actions.get(act, 0) + 1

    speakers = {_spk(s) for s in segments if _spk(s) != "UNKNOWN"}

    return {
        "total_segments": total,
        "unknown_segments": unknown,
        "unknown_rate": round(unknown / total, 4) if total else 0,
        "needs_review_segments": needs_review,
        "distinct_known_speakers": len(speakers),
        "actions": actions,
    }


# -------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="Micro-block cleanup for merged transcript segments")
    ap.add_argument("--merged", required=True, help="Input merged segments JSON")
    ap.add_argument("--out", required=True, help="Output cleaned segments JSON")
    ap.add_argument(
        "--min-duration",
        type=float,
        default=DEFAULT_MIN_DURATION,
        help=f"Minimum duration (s) to avoid micro-block cleanup (default: {DEFAULT_MIN_DURATION})",
    )
    ap.add_argument(
        "--dominance-threshold",
        type=float,
        default=DEFAULT_DOMINANCE_THRESHOLD,
        help=f"Fraction of cluster duration required for dominant speaker (default: {DEFAULT_DOMINANCE_THRESHOLD})",
    )
    ap.add_argument(
        "--skip-sandwich",
        action="store_true",
        help="Skip the secondary sandwich-attachment pass",
    )
    args = ap.parse_args()

    merged_path = Path(args.merged)
    out_path = Path(args.out)

    if not merged_path.exists():
        raise SystemExit(f"Input file not found: {merged_path}")

    blocks = _load_merged(merged_path)
    segments = _to_segments(blocks)

    before_metrics = compute_metrics(segments)

    cleaned = cleanup_segments(
        segments,
        min_duration=args.min_duration,
        dominance_threshold=args.dominance_threshold,
    )

    if not args.skip_sandwich:
        cleaned = attach_to_neighbors(cleaned)

    after_metrics = compute_metrics(cleaned)

    print(f"Before: {before_metrics['total_segments']} segs, "
          f"{before_metrics['unknown_segments']} unknown ({before_metrics['unknown_rate']:.1%}), "
          f"{before_metrics['needs_review_segments']} needs_review")

    print(f"After:  {after_metrics['total_segments']} segs, "
          f"{after_metrics['unknown_segments']} unknown ({after_metrics['unknown_rate']:.1%}), "
          f"{after_metrics['needs_review_segments']} needs_review")

    delta_unknown = before_metrics['unknown_segments'] - after_metrics['unknown_segments']
    print(f"Unknown reduction: {delta_unknown:+d} segments "
          f"({before_metrics['unknown_rate']:.1%} → {after_metrics['unknown_rate']:.1%})")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    output_doc = {
        "schema": "fairfax.cleaned_segments.v1",
        "cleanup_config": {
            "min_duration": args.min_duration,
            "dominance_threshold": args.dominance_threshold,
            "sandwich_pass": not args.skip_sandwich,
        },
        "before_metrics": before_metrics,
        "after_metrics": after_metrics,
        "segments": _to_dicts(cleaned) if isinstance(cleaned[0], Segment) else cleaned,
    }
    out_path.write_text(
        json.dumps(output_doc, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Output: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

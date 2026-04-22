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
    cleanup_action: str = "kept"  # "kept" | "merged_into" | "kept_review"
    original_ids: list[str] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


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
            seg = Segment(
                segment_id=str(b.get("segment_id", f"seg_{len(out)+1:06d}")),
                start=float(b.get("start_seconds", 0)),
                end=float(b.get("end_seconds", 0)),
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


# -------------------------------------------------------------------
# Core cleanup logic
# -------------------------------------------------------------------
def cleanup_segments(
    segments: list[Segment],
    min_duration: float = DEFAULT_MIN_DURATION,
    dominance_threshold: float = DEFAULT_DOMINANCE_THRESHOLD,
) -> list[Segment]:
    """Main cleanup pass.

    Algorithm:
      1. Scan for consecutive micro-blocks (each < min_duration)
      2. For each micro-block cluster:
         a. Compute per-speaker total duration
         b. Find dominant speaker and dominance fraction
         c. If dominant speaker != UNKNOWN and dominance >= threshold:
              merge all into one block with dominant speaker
              tag with review_reason="microblock_cleanup"
            else:
              tag each micro-block as needs_review=True, review_reason="microblock_deferred"
      3. Non-micro-blocks pass through unchanged
    """
    result: list[Segment] = []
    i = 0

    while i < len(segments):
        seg = segments[i]
        dur = seg.duration

        # Not a micro-block — pass through unchanged
        if dur >= min_duration:
            seg.cleanup_action = "kept"
            seg.original_ids = [seg.segment_id]
            result.append(seg)
            i += 1
            continue

        # Collect consecutive micro-blocks
        cluster: list[Segment] = [seg]
        j = i + 1
        while j < len(segments) and segments[j].duration < min_duration:
            cluster.append(segments[j])
            j += 1

        # Analyze cluster
        speaker_dur: dict[str, float] = {}
        for cseg in cluster:
            sp = cseg.speaker_id
            if sp == "UNKNOWN":
                # UNKNOWN gets 0 weight in dominance calc
                continue
            speaker_dur[sp] = speaker_dur.get(sp, 0.0) + cseg.duration

        total_dur = sum(c.duration for c in cluster)
        if not speaker_dur or total_dur == 0:
            # All UNKNOWN or empty — defer each to review
            for cseg in cluster:
                cseg.needs_review = True
                cseg.review_reason = "microblock_deferred"
                cseg.cleanup_action = "kept_review"
                cseg.original_ids = [cseg.segment_id]
                result.append(cseg)
            i = j
            continue

        dom_speaker = max(speaker_dur, key=speaker_dur.get)
        dom_dur = speaker_dur[dom_speaker]
        dom_frac = dom_dur / total_dur

        if dom_frac >= dominance_threshold:
            # Merge all into one block with dominant speaker
            merged = Segment(
                segment_id=cluster[0].segment_id,  # keep first block's ID
                start=cluster[0].start,
                end=cluster[-1].end,
                speaker_id=dom_speaker,
                text=_merge_text([c.text for c in cluster]),
                speaker_name=cluster[0].speaker_name,  # keep first block's name (may be updated by registry)
                speaker_role=cluster[0].speaker_role,
                speaker_confidence=dom_frac,  # reflect actual dominance as confidence proxy
                needs_review=True,  # still flagged for review since we force-assigned
                review_reason="microblock_cleanup",
                cleanup_action="merged_into",
                original_ids=[c.segment_id for c in cluster],
            )
            result.append(merged)
        else:
            # No dominant speaker — defer each to review
            for cseg in cluster:
                cseg.needs_review = True
                cseg.review_reason = "microblock_deferred"
                cseg.cleanup_action = "kept_review"
                cseg.original_ids = [cseg.segment_id]
                result.append(cseg)

        i = j

    return result


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
        # Avoid double spaces when joining
        if merged.endswith(" ") or t.startswith(" "):
            merged += t
        else:
            merged += " " + t
    return re.sub(r"\s+", " ", merged).strip()


# -------------------------------------------------------------------
# Optional: secondary merge for post-cleanup remaining micro-blocks
# -------------------------------------------------------------------
def attach_to_neighbors(segments: list[Segment], max_attach_duration: float = 2.0) -> list[Segment]:
    """For remaining micro-blocks after cleanup, try to attach to adjacent non-micro blocks.

    Only attaches if:
      - the micro-block is between two blocks with the SAME speaker
      - both adjacent blocks are not micro-blocks
      - the micro-block text naturally continues (short fragment, not a sentence end)

    This handles cases like:
      [SPEAKER_21: "Good evening."] [UNKNOWN: "I"] [SPEAKER_21: "would like..."]
    where UNKNOWN is a 0.3s interjection that should stay unknown.
    """
    result: list[Segment] = []
    i = 0

    while i < len(segments):
        seg = segments[i]
        dur = seg.duration

        # Only process micro-blocks that are still UNKNOWN after cleanup
        if dur >= 1.5 or seg.speaker_id != "UNKNOWN":
            result.append(seg)
            i += 1
            continue

        # Check if sandwiched between two same-speaker non-micro blocks
        if i > 0 and i < len(segments) - 1:
            prev_seg = segments[i - 1]
            next_seg = segments[i + 1]

            if (
                prev_seg.speaker_id == next_seg.speaker_id
                and prev_seg.speaker_id != "UNKNOWN"
                and prev_seg.duration >= 1.5
                and next_seg.duration >= 1.5
            ):
                # Check if text is a short continuation (not a sentence end)
                text = seg.text.strip()
                is_short = len(text.split()) <= 5
                ends_sentence = text.endswith((".", "!", "?", ":", ",", '"'))

                if is_short and not ends_sentence:
                    # Attach to previous block
                    seg.speaker_id = prev_seg.speaker_id
                    seg.speaker_name = prev_seg.speaker_name
                    seg.speaker_role = prev_seg.speaker_role
                    seg.speaker_confidence = 0.5  # lowered, still needs review
                    seg.review_reason = "sandwich_attached"
                    seg.cleanup_action = "sandwich_attached"
                    seg.original_ids = [seg.segment_id]
                    result.append(seg)
                    i += 1
                    continue

        result.append(seg)
        i += 1

    return result


# -------------------------------------------------------------------
# Metrics reporting
# -------------------------------------------------------------------
def compute_metrics(segments: list[Segment]) -> dict[str, Any]:
    total = len(segments)
    unknown = sum(1 for s in segments if s.speaker_id == "UNKNOWN")
    needs_review = sum(1 for s in segments if s.needs_review)
    actions = {
        "kept": 0,
        "merged_into": 0,
        "kept_review": 0,
        "sandwich_attached": 0,
    }
    for s in segments:
        actions[s.cleanup_action] = actions.get(s.cleanup_action, 0) + 1

    speakers = set(s.speaker_id for s in segments if s.speaker_id != "UNKNOWN")

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

    # Cleanup
    cleaned = cleanup_segments(
        segments,
        min_duration=args.min_duration,
        dominance_threshold=args.dominance_threshold,
    )

    # Secondary pass: attach short unknown fragments to same-speaker neighbors
    if not args.skip_sandwich:
        cleaned = attach_to_neighbors(cleaned)

    # Report metrics
    before_metrics = compute_metrics(_to_segments(blocks))
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

    # Write output
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
        "segments": _to_dicts(cleaned),
    }
    out_path.write_text(
        json.dumps(output_doc, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Output: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

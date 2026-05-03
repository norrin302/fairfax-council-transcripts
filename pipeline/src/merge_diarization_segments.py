#!/usr/bin/env python3
"""Post-process diarization to merge consecutive same-speaker segments with small gaps."""

import json
import argparse
from pathlib import Path


def merge_segments(segments, max_gap_seconds=2.0):
    """Merge consecutive segments from the same speaker if gap is small."""
    if not segments:
        return segments
    
    merged = []
    current = segments[0].copy()
    
    for seg in segments[1:]:
        gap = seg["start"] - current["end"]
        same_speaker = seg["speaker"] == current["speaker"]
        
        if same_speaker and gap <= max_gap_seconds:
            # Merge: extend current segment
            current["end"] = seg["end"]
        else:
            # Save current and start new
            merged.append(current)
            current = seg.copy()
    
    merged.append(current)
    return merged


def main():
    ap = argparse.ArgumentParser(description="Merge consecutive same-speaker segments")
    ap.add_argument("input_json")
    ap.add_argument("--max-gap", type=float, default=2.0, help="Max gap in seconds to merge")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    
    data = json.loads(Path(args.input_json).read_text())
    original_count = len(data["segments"])
    
    merged = merge_segments(data["segments"], args.max_gap)
    
    result = {"audio": data.get("audio"), "segments": merged}
    Path(args.out).write_text(json.dumps(result, indent=2))
    
    print(f"Merged {original_count} -> {len(merged)} segments (max_gap={args.max_gap}s)")


if __name__ == "__main__":
    main()

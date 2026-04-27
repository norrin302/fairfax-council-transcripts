#!/usr/bin/env python3
"""Identify speakers in a meeting by comparing embeddings to the speaker registry."""
from __future__ import annotations
import argparse
import json
import math
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parents[1] / "pipeline"
REGISTRY_PATH = PIPELINE_DIR / "speaker_registry.json"
EXTRACT_EMB = PIPELINE_DIR / "src" / "extract_embedding.py"
sys.path.insert(0, str(PIPELINE_DIR / "src"))


def cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def load_registry_embeddings():
    reg = json.loads(REGISTRY_PATH.read_text())
    speakers = {}
    for name, info in reg.get("speakers", {}).items():
        samples = info.get("samples", [])
        if not samples:
            continue
        emb_path = REGISTRY_PATH.parent / "embeddings" / samples[0]["file"]
        if not emb_path.exists():
            continue
        emb_data = json.loads(emb_path.read_text())
        emb = emb_data["embedding"]
        speakers[name] = {"role": info.get("role"), "embedding": emb}
    for spk_id, info in reg.get("pending_identification", {}).items():
        emb_path = REGISTRY_PATH.parent / "embeddings" / info["file"]
        if emb_path.exists():
            emb_data = json.loads(emb_path.read_text())
            emb = emb_data["embedding"]
            speakers[spk_id] = {"role": "unknown", "embedding": emb}
    return speakers


def extract_embedding(audio_path: str, start: float, end: float, work_dir: Path) -> list[float] | None:
    """Extract embedding for an audio segment using extract_embedding.py"""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, dir=work_dir) as f:
        out_path = Path(f.name)
    try:
        token_file = PIPELINE_DIR / "token.txt"
        token_arg = ["--token-file", str(token_file)] if token_file.exists() else []
        result = subprocess.run(
            ["python3", str(EXTRACT_EMB), audio_path,
             "--start", str(start), "--end", str(end),
             "--out", str(out_path)] + token_arg,
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0 or not out_path.exists():
            print(f"  Embedding extraction failed: {result.stderr[:200]}")
            return None
        data = json.loads(out_path.read_text())
        return data["embedding"]
    except Exception as e:
        print(f"  Error: {e}")
        return None
    finally:
        out_path.unlink(missing_ok=True)


def identify_speakers_in_merge(merge_path: Path, audio_path: Path, work_dir: Path, threshold: float = 0.5):
    """Identify speakers in merge output using registry embeddings."""
    merge = json.loads(merge_path.read_text())
    registry = load_registry_embeddings()
    print(f"Loaded {len(registry)} registry speakers")

    # Group segments by speaker_id
    by_speaker: dict[str, list] = defaultdict(list)
    for seg in merge.get("segments", []):
        sid = seg.get("speaker_id", "UNKNOWN")
        by_speaker[sid].append(seg)

    # For each non-UNKNOWN speaker, extract embedding and identify
    speaker_map = {}  # speaker_id -> identified name
    for sid in sorted(by_speaker.keys()):
        if sid == "UNKNOWN":
            continue
        segs = by_speaker[sid]
        # Use the longest segment for embedding
        best = max(segs, key=lambda s: s.get("end_seconds", 0) - s.get("start_seconds", 0))
        start = best.get("start_seconds", 0)
        end = best.get("end_seconds", 0)
        duration = end - start
        # Use center 1 second
        center = (start + end) / 2
        emb_start = max(0, center - 0.5)
        emb_end = center + 0.5

        print(f"  Extracting embedding for {sid} ({len(segs)} segs, best seg {duration:.1f}s)...")
        emb = extract_embedding(str(audio_path), emb_start, emb_end, work_dir)
        if emb is None:
            print(f"    -> Failed, keeping Unknown Speaker")
            speaker_map[sid] = ("Unknown Speaker", 0.0)
            continue

        # Compare with registry
        best_name = "Unknown Speaker"
        best_score = 0.0
        for name, info in registry.items():
            score = cosine_sim(emb, info["embedding"])
            if score > best_score:
                best_score = score
                best_name = name
        if best_score >= threshold:
            print(f"    -> {best_name} (score={best_score:.3f})")
            speaker_map[sid] = (best_name, best_score)
        else:
            print(f"    -> Unknown Speaker (best score={best_score:.3f} < {threshold})")
            speaker_map[sid] = ("Unknown Speaker", best_score)

    # Update merge with identified names
    identified = 0
    for seg in merge.get("segments", []):
        sid = seg.get("speaker_id", "UNKNOWN")
        if sid in speaker_map:
            name, score = speaker_map[sid]
            seg["speaker_name"] = name
            seg["speaker_confidence"] = score
            seg["needs_review"] = name == "Unknown Speaker"
            if name != "Unknown Speaker":
                identified += 1

    print(f"Identified {identified}/{len(merge['segments'])} segments")
    return merge, speaker_map


def main():
    import sys
    ap = argparse.ArgumentParser(description="Identify speakers using embedding similarity")
    ap.add_argument("meeting_id")
    ap.add_argument("--merge")
    ap.add_argument("--audio")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--out")
    args = ap.parse_args()

    meeting_id = args.meeting_id
    work_dir = Path(f"pipeline/work/{meeting_id}")
    merge_path = Path(args.merge or f"pipeline/work/{meeting_id}/merged/segments_with_speaker_names.json")
    audio_path = Path(args.audio or f"pipeline/work/{meeting_id}/audio/audio_16k_mono.wav")
    out_path = Path(args.out or f"pipeline/work/{meeting_id}/merged/segments_identified.json")

    if not merge_path.exists():
        print(f"Merge file not found: {merge_path}")
        sys.exit(1)
    if not audio_path.exists():
        print(f"Audio file not found: {audio_path}")
        sys.exit(1)

    result, speaker_map = identify_speakers_in_merge(merge_path, audio_path, work_dir, args.threshold)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out_path}")
    print("\nSpeaker mapping:")
    for sid, (name, score) in sorted(speaker_map.items()):
        print(f"  {sid} -> {name} ({score:.3f})")


if __name__ == "__main__":
    import sys
    raise SystemExit(main())

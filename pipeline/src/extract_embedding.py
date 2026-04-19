#!/usr/bin/env python3
"""
Extract speaker embedding from audio segment.
Uses pyannote's embedding model.
"""

import argparse
import json
import tempfile
from pathlib import Path

from huggingface_hub import hf_hub_download as _hf_hub_download
import pyannote.audio.core.pipeline as _pipeline_mod


def _hf_hub_download_compat(*args, **kwargs):
    if "use_auth_token" in kwargs and "token" not in kwargs:
        kwargs["token"] = kwargs.pop("use_auth_token")
    else:
        kwargs.pop("use_auth_token", None)
    return _hf_hub_download(*args, **kwargs)


_pipeline_mod.hf_hub_download = _hf_hub_download_compat

from pyannote.audio import Model


def main():
    ap = argparse.ArgumentParser(description="Extract speaker embedding from audio")
    ap.add_argument("audio", help="Audio file")
    ap.add_argument("--start", type=float, default=0, help="Start time in seconds")
    ap.add_argument("--end", type=float, help="End time in seconds")
    ap.add_argument("--out", required=True, help="Output JSON file")
    ap.add_argument("--token-file", default="")
    args = ap.parse_args()
    
    # Load HF token
    token_file = Path(args.token_file) if args.token_file else None
    token = None
    if token_file and token_file.exists():
        token = token_file.read_text().strip()
    
    # Load embedding model
    model = Model.from_pretrained(
        "pyannote/wespeaker-voxceleb-resnet34-LM",
        use_auth_token=token
    )
    
    # Extract embedding
    audio_path = Path(args.audio)
    if args.end:
        # Extract segment
        import subprocess
        segment_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        segment_path = segment_file.name
        segment_file.close()
        
        duration = args.end - args.start
        subprocess.run([
            "ffmpeg", "-y", "-i", str(audio_path),
            "-ss", str(args.start), "-t", str(duration),
            "-c", "copy", segment_path
        ], check=True, capture_output=True)
        audio_path = Path(segment_path)
    
    # Get embedding
    embedding = model(audio_path)
    
    # Convert to list for JSON serialization
    import numpy as np
    embedding_list = embedding.squeeze().tolist()
    
    result = {
        "audio": str(args.audio),
        "start": args.start,
        "end": args.end if args.end else "full",
        "embedding": embedding_list,
        "embedding_dim": len(embedding_list)
    }
    
    # Cleanup temp file if created
    if args.end:
        Path(segment_path).unlink(missing_ok=True)
    
    Path(args.out).write_text(json.dumps(result, indent=2))
    print(f"Wrote embedding ({len(embedding_list)} dims) to {args.out}")


if __name__ == "__main__":
    main()

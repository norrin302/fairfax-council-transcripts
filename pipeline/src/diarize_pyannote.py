from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

# Compatibility shim for older pyannote.audio expecting huggingface_hub.hf_hub_download(use_auth_token=...)
from huggingface_hub import hf_hub_download as _hf_hub_download
import pyannote.audio.core.pipeline as _pipeline_mod


def _hf_hub_download_compat(*args, **kwargs):
    if "use_auth_token" in kwargs and "token" not in kwargs:
        kwargs["token"] = kwargs.pop("use_auth_token")
    else:
        kwargs.pop("use_auth_token", None)
    return _hf_hub_download(*args, **kwargs)


_pipeline_mod.hf_hub_download = _hf_hub_download_compat

from pyannote.audio import Pipeline


# Very aggressive config to minimize over-segmentation
# - min_duration_off: 2.0s (require 2s gap before splitting)
# - threshold: 0.78 (very strict speaker clustering)
# - min_cluster_size: 25 (larger minimum speaker segments)
DEFAULT_YAML = """version: 3.1.0

pipeline:
  name: pyannote.audio.pipelines.SpeakerDiarization
  params:
    clustering: AgglomerativeClustering
    embedding: pyannote/wespeaker-voxceleb-resnet34-LM
    embedding_batch_size: 8
    embedding_exclude_overlap: true
    segmentation: pyannote/segmentation-3.0
    segmentation_batch_size: 8
params:
  clustering:
    method: centroid
    min_cluster_size: 25
    threshold: 0.78
  segmentation:
    min_duration_off: 2.0
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Run pyannote speaker diarization")
    ap.add_argument("audio")
    ap.add_argument("--out", default="diarization/pyannote_segments.json")
    ap.add_argument("--token-file", default=os.environ.get("HF_TOKEN_FILE", ""))
    args = ap.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        raise SystemExit(f"Missing audio: {audio_path}")

    token_file = Path(args.token_file) if args.token_file else None
    if not token_file or not token_file.exists():
        raise SystemExit("Missing HF token file. Provide --token-file or HF_TOKEN_FILE env.")

    token = token_file.read_text(encoding="utf-8").strip()
    if not token:
        raise SystemExit("HF token file is empty")

    yaml_text = os.environ.get("PIPELINE_YAML", "").strip() or DEFAULT_YAML
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(yaml_text)
        cfg_path = f.name

    pipeline = Pipeline.from_pretrained(cfg_path, use_auth_token=token)

    try:
        import torch
        if torch.cuda.is_available():
            pipeline.to(torch.device("cuda"))
    except Exception:
        pass

    diar = pipeline(str(audio_path))

    segs = []
    for turn, _, speaker in diar.itertracks(yield_label=True):
        segs.append({
            "start": float(turn.start),
            "end": float(turn.end),
            "speaker": str(speaker),
        })

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = Path.cwd() / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)

    out_path.write_text(
        json.dumps({"audio": str(audio_path), "segments": segs}, indent=2),
        encoding="utf-8",
    )
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

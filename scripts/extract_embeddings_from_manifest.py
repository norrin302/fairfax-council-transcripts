#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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
from pyannote.audio import Inference


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract speaker embeddings for every clip in a manifest")
    ap.add_argument("manifest", help="Manifest JSON from export_reference_clips.py")
    ap.add_argument("--out-dir", required=True, help="Output directory for embedding JSON files")
    ap.add_argument("--token-file", required=True, help="HF token file")
    ap.add_argument("--host-prefix", default="", help="Optional host path prefix to rewrite")
    ap.add_argument("--container-prefix", default="", help="Optional replacement for host prefix")
    ap.add_argument("--identity-map", default="", help="Optional JSON file mapping speaker_id to approved name")
    args = ap.parse_args()

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    token = Path(args.token_file).read_text(encoding="utf-8").strip()
    inference = Inference("pyannote/wespeaker-voxceleb-resnet34-LM", use_auth_token=token)

    identity_map = {}
    if args.identity_map:
        identity_map = json.loads(Path(args.identity_map).read_text(encoding="utf-8"))

    def map_path(raw: str) -> str:
        if args.host_prefix and args.container_prefix and raw.startswith(args.host_prefix):
            return raw.replace(args.host_prefix, args.container_prefix, 1)
        return raw

    registry = []
    count = 0
    for speaker in manifest.get("speakers") or []:
        speaker_id = str(speaker.get("speaker_id") or "").strip()
        if not speaker_id:
            continue
        approved_identity = str((identity_map.get(speaker_id) or {}).get("name") or "")
        speaker_dir = out_dir / speaker_id
        speaker_dir.mkdir(parents=True, exist_ok=True)
        for clip in speaker.get("clips") or []:
            clip_path = str(clip.get("path") or "")
            if not clip_path:
                continue
            emb = inference(map_path(clip_path))
            if hasattr(emb, "data"):
                emb_data = emb.data.mean(axis=0).tolist()
            else:
                emb_data = emb.squeeze().tolist()
            out_path = speaker_dir / (Path(clip_path).stem + ".json")
            payload = {
                "speaker_id": speaker_id,
                "approved_identity": approved_identity,
                "clip_path": clip_path,
                "start": clip.get("start"),
                "end": clip.get("end"),
                "duration": clip.get("duration"),
                "embedding": emb_data,
                "embedding_dim": len(emb_data),
            }
            out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            registry.append(payload | {"embedding_path": str(out_path)})
            count += 1

    registry_path = out_dir / "embeddings_registry.json"
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(f"Wrote {count} embeddings")
    print(registry_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

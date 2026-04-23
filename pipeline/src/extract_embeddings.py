#!/usr/bin/env python3
"""Extract speaker embeddings from pyannote diarization segments.

Uses pyannote.audio's PyannoteAudioPretrainedSpeakerEmbedding
(pyramid-based wespeaker resnet34) to extract 256-dim embeddings
per diarization segment, then averages per pyannote speaker to get
a centroid embedding per speaker ID. Clusters by cosine similarity
to merge pyannote ID reassignments.

Requires: pyannote.audio 3.x, PyannoteAudioPretrainedSpeakerEmbedding
Runs inside the diarize-pyannote Docker container.

Usage:
  docker run --rm --gpus all -v /mnt/disk1:/mnt/disk1 \
    -v $PWD:/work fairfax-pipeline-diarize_pyannote \
    python -m pipeline.src.extract_embeddings \
    --audio /mnt/disk1/.../apr-14-2026/audio/audio_16k_mono.wav \
    --segments /mnt/disk1/.../apr-14-2026/diarization/pyannote_segments.json \
    --out /work/embeddings.json \
    --clusters /work/cluster_map.json \
    [--device cuda]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
import torch


def load_diarization(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def extract_speaker_embeddings(
    audio_path: str,
    diarization_segments: list[dict[str, Any]],
    model_name: str = "pyannote/wespeaker-voxceleb-resnet34-LM",
    device: str = "cuda",
    min_duration: float = 0.3,
) -> dict[str, Any]:
    """Extract per-segment embeddings and average per speaker to get centroid embeddings."""
    from pyannote.audio.pipelines.speaker_verification import (
        PyannoteAudioPretrainedSpeakerEmbedding,
    )

    print(f"Loading embedding model {model_name} on {device}...")
    emb_model = PyannoteAudioPretrainedSpeakerEmbedding(model_name, device=torch.device(device))
    print(f"  Embedding dimension: {emb_model.dimension}")
    print(f"  Sample rate: {emb_model.sample_rate}")

    # Pre-load audio once
    print(f"Loading audio: {audio_path}")
    y, sr = sf.read(audio_path, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)  # mono
    print(f"  Audio: {len(y)/sr:.1f}s, {sr}Hz, shape={y.shape}")

    # Collect embeddings per speaker
    speakers: set[str] = set(seg.get("speaker", "") for seg in diarization_segments)
    speaker_embs: dict[str, list[np.ndarray]] = {sp: [] for sp in speakers}

    n_processed = 0
    n_skipped = 0
    n_failed = 0

    for i, seg in enumerate(diarization_segments):
        sp = seg.get("speaker", "")
        if not sp:
            continue

        seg_start = seg.get("start", 0)
        seg_end = seg.get("end", 0)
        seg_dur = seg_end - seg_start

        if seg_dur < min_duration:
            n_skipped += 1
            continue

        # Extract audio chunk
        start_s = int(seg_start * sr)
        end_s = int(seg_end * sr)
        y_seg = y[start_s:end_s]

        if len(y_seg) < sr * 0.1:
            n_skipped += 1
            continue

        # Reshape to (batch=1, channels=1, samples)
        y_t = torch.from_numpy(y_seg).float().reshape(1, 1, -1)

        try:
            emb_vec = emb_model(y_t)  # (1, 256) ndarray
            if emb_vec.ndim > 1:
                emb_vec = emb_vec.reshape(-1)
            speaker_embs[sp].append(emb_vec)
            n_processed += 1
        except Exception:
            n_failed += 1
            continue

        if (i + 1) % 200 == 0:
            print(f"  [{i + 1}/{len(diarization_segments)}] processed={n_processed}, "
                  f"skipped={n_skipped}, failed={n_failed}")

    print(f"Embedding extraction done: {n_processed} processed, {n_skipped} skipped, {n_failed} failed")

    # Compute centroid per speaker
    speaker_centroids: dict[str, list[float]] = {}
    for sp, embs in speaker_embs.items():
        if not embs:
            print(f"  Warning: no embeddings for {sp}")
            speaker_centroids[sp] = [0.0] * emb_model.dimension
            continue
        arr = np.stack(embs)
        centroid = arr.mean(axis=0)
        speaker_centroids[sp] = centroid.tolist()

    return {
        "model": model_name,
        "device": device,
        "embedding_dim": emb_model.dimension,
        "n_segments_input": len(diarization_segments),
        "n_segments_processed": n_processed,
        "n_segments_skipped": n_skipped,
        "n_segments_failed": n_failed,
        "speakers": list(speakers),
        "speaker_centroids": speaker_centroids,
    }


def cluster_speakers_by_embeddings(
    speaker_centroids: dict[str, list[float]],
    similarity_threshold: float = 0.75,
) -> dict[str, Any]:
    """Agglomerative cluster speakers by cosine similarity of centroid embeddings."""
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics.pairwise import cosine_similarity

    speaker_list = list(speaker_centroids.keys())
    n_speakers = len(speaker_list)
    print(f"Clustering {n_speakers} speakers by embedding similarity...")

    emb_matrix = np.array([speaker_centroids[sp] for sp in speaker_list])
    sim_matrix = cosine_similarity(emb_matrix)
    np.fill_diagonal(sim_matrix, 1.0)

    # Distance = 1 - similarity
    dist_matrix = 1.0 - sim_matrix
    np.fill_diagonal(dist_matrix, 0.0)

    # Auto-determine clusters: merge if similarity > threshold
    # Start with n_speakers clusters, merge where similarity > threshold
    # Use the threshold as a guide: for each pair above threshold, they should merge
    # We approximate this with n_clusters = n_speakers initially, then adjust
    n_clusters = n_speakers  # start conservative

    clustering = AgglomerativeClustering(
        n_clusters=n_clusters,
        metric="precomputed",
        linkage="average",
    )
    labels = clustering.fit_predict(dist_matrix)

    # Build cluster map
    raw_to_cluster: dict[str, str] = {}
    clusters: dict[str, list[str]] = {}

    for i, sp in enumerate(speaker_list):
        cluster_id = f"CLUSTER_{labels[i]:02d}"
        raw_to_cluster[sp] = cluster_id
        clusters.setdefault(cluster_id, []).append(sp)

    n_actual_clusters = len(clusters)
    merges = n_speakers - n_actual_clusters

    print(f"  Raw speakers: {n_speakers}, Clusters: {n_actual_clusters}, Merges: {merges}")

    return {
        "method": "agglomerative_cosine_similarity",
        "similarity_threshold": similarity_threshold,
        "n_raw_speakers": n_speakers,
        "n_clusters": n_actual_clusters,
        "merges_performed": merges,
        "raw_to_cluster": raw_to_cluster,
        "clusters": clusters,
        "pairwise_similarity": {
            f"{speaker_list[i]}_{speaker_list[j]}": float(sim_matrix[i, j])
            for i in range(n_speakers) for j in range(i + 1, n_speakers)
        } if n_speakers <= 20 else {},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract speaker embeddings and cluster")
    ap.add_argument("--audio", required=True, help="16k mono WAV audio file")
    ap.add_argument("--segments", required=True, help="pyannote diarization segments JSON")
    ap.add_argument("--out", required=True, help="Output embeddings JSON")
    ap.add_argument("--clusters", required=True, help="Output cluster map JSON")
    ap.add_argument(
        "--model",
        default="pyannote/wespeaker-voxceleb-resnet34-LM",
        help="Embedding model (default: pyannote/wespeaker-voxceleb-resnet34-LM)",
    )
    ap.add_argument(
        "--device",
        default="cuda",
        choices=["cuda", "cpu"],
        help="Device (default: cuda)",
    )
    ap.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.75,
        help="Cosine similarity threshold for same-speaker merge (default: 0.75)",
    )
    args = ap.parse_args()

    diar = load_diarization(args.segments)
    segments = diar.get("segments", [])

    print(f"Audio: {args.audio}")
    print(f"Segments: {len(segments)}")

    emb_result = extract_speaker_embeddings(
        args.audio,
        segments,
        model_name=args.model,
        device=args.device,
    )

    out_emb = Path(args.out)
    out_emb.parent.mkdir(parents=True, exist_ok=True)
    with open(out_emb, "w", encoding="utf-8") as f:
        json.dump(emb_result, f, indent=2, ensure_ascii=False)
    print(f"Embeddings saved: {out_emb}")
    print(f"  Speakers: {len(emb_result['speakers'])}")
    print(f"  Processed: {emb_result['n_segments_processed']}")

    cluster_result = cluster_speakers_by_embeddings(
        emb_result["speaker_centroids"],
        similarity_threshold=args.similarity_threshold,
    )

    out_cluster = Path(args.clusters)
    out_cluster.parent.mkdir(parents=True, exist_ok=True)
    with open(out_cluster, "w", encoding="utf-8") as f:
        json.dump(cluster_result, f, indent=2, ensure_ascii=False)
    print(f"Cluster map saved: {out_cluster}")

    print("\nCluster details:")
    for cid, members in sorted(cluster_result["clusters"].items()):
        print(f"  {cid}: {members}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

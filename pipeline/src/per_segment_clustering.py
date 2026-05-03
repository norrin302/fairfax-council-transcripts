#!/usr/bin/env python3
"""
per_segment_clustering.py — Conservative per-segment embedding clustering

Architecture:
1. Extract per-segment embeddings for each diarization segment
2. Build a sparse similarity graph connecting segments that:
   a) Have different pyannote speaker IDs
   b) Are temporally non-overlapping (can be the same physical speaker)
   c) Have cosine similarity above the conservative threshold
3. Find connected components = clusters
4. Each segment gets: raw pyannote ID + cluster ID (for audit)
5. Cluster centroid → cluster representative embedding → registry mapping

This handles pyannote ID REASSIGNMENT (same person gets different IDs)
without incorrectly merging DIFFERENT people who happen to sound similar.

Key safeguard: similarity threshold of 0.85+ means only very confident
same-person links. Different people with moderate similarity (0.77 for
Tom Peterson vs JC Martinez) will NOT be merged because they overlap
in time with each other.
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

# =============================================================================
# Helpers
# =============================================================================

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def cosim(a, b):
    """Cosine similarity between two vectors."""
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def segments_overlap(a_start, a_end, b_start, b_end, gap_tol=0.5):
    """Return True if segments are temporally non-overlapping (with small gap tolerance)."""
    # Non-overlapping means: a ends before b starts, or b ends before a starts
    # gap_tol allows small gaps (e.g., 0.5s between segments)
    return not (a_end > b_start - gap_tol and b_end > a_start - gap_tol)

# =============================================================================
# Per-segment embedding extraction
# =============================================================================

def extract_segment_embeddings(diarization_path, audio_path, device="cuda",
                                 min_duration=0.5, model_name="pyannote/wespeaker-voxceleb-resnet34-LM"):
    """Extract embedding for each diarization segment individually."""
    import torch
    from pyannote.audio import Model
    from pyannote.audio.pipeline.pyannote_audio_pretrained import PyannoteAudioPretrainedSpeakerEmbedding

    print(f"  Loading embedding model {model_name} on {device}...")
    emb_model = PyannoteAudioPretrainedSpeakerEmbedding(model_name, device=device)

    diar = load_json(diarization_path)
    diar_segments = diar["segments"]

    print(f"  Loading audio: {audio_path}")
    import soundfile as sf
    waveform, sample_rate = sf.read(audio_path)
    if waveform.ndim > 1:
        waveform = waveform.mean(axis=1)
    print(f"  Audio: {waveform.shape[0]/sample_rate:.1f}s at {sample_rate}Hz")

    embeddings = {}
    n_proc = 0
    n_skip = 0
    n_fail = 0

    for i, seg in enumerate(diar_segments):
        start = seg["start"]
        end = seg["end"]
        duration = end - start

        if duration < min_duration:
            n_skip += 1
            continue

        # Convert to samples
        start_s = int(start * sample_rate)
        end_s = int(end * sample_rate)
        segment_wav = waveform[start_s:end_s]

        if len(segment_wav) < sample_rate * 0.1:  # less than 100ms
            n_skip += 1
            continue

        try:
            emb = emb_model({"waveform": segment_wav, "sample_rate": sample_rate})
            if emb is None or (hasattr(emb, 'shape') and emb.shape[0] == 0):
                n_skip += 1
                continue
            if hasattr(emb, 'numpy'):
                emb = emb.numpy()
            if emb.ndim > 1:
                emb = emb.squeeze()
            embeddings[seg["speaker"]] = embeddings.get(seg["speaker"], [])
            embeddings[seg["speaker"]].append({
                "seg_idx": i,
                "start": start,
                "end": end,
                "embedding": emb.tolist()
            })
            n_proc += 1
        except Exception as e:
            n_fail += 1
            continue

        if (i + 1) % 200 == 0:
            print(f"  [{i+1}/{len(diar_segments)}] proc={n_proc}, skip={n_skip}, fail={n_fail}")

    return embeddings, n_proc, n_skip, n_fail

# =============================================================================
# Segment-level similarity + clustering
# =============================================================================

def build_similarity_graph(segment_embeddings, similarity_threshold=0.85, gap_tol=0.5):
    """
    Build adjacency graph: connect segments with different pyannote IDs,
    non-overlapping times, and similarity >= threshold.

    Returns dict: seg_idx -> set of connected seg_idx
    """
    # First, collect all segment info
    all_segs = []
    for speaker, segs in segment_embeddings.items():
        for seg in segs:
            all_segs.append({
                "idx": seg["seg_idx"],
                "speaker": speaker,
                "start": seg["start"],
                "end": seg["end"],
                "embedding": seg["embedding"]
            })

    n_segs = len(all_segs)
    print(f"  Building similarity graph for {n_segs} segments...")

    # Create speaker -> [seg_idx] index
    speaker_to_seg = defaultdict(list)
    for s in all_segs:
        speaker_to_seg[s["speaker"]].append(s["idx"])

    # For each pair of speakers, check if they could be the same person
    # (temporally non-overlapping)
    speakers = list(speaker_to_seg.keys())
    n_speakers = len(speakers)

    # For each speaker pair, find temporally non-overlapping segment pairs
    # Only connect segments if they have DIFFERENT pyannote IDs
    graph = defaultdict(set)  # seg_idx -> connected seg_idx

    edges_found = 0
    pairs_checked = 0

    for i, sp1 in enumerate(speakers):
        for sp2 in speakers[i+1:]:
            segs1 = speaker_to_seg[sp1]
            segs2 = speaker_to_seg[sp2]

            for idx1 in segs1:
                for idx2 in segs2:
                    # Find segment data
                    s1 = next(s for s in all_segs if s["idx"] == idx1)
                    s2 = next(s for s in all_segs if s["idx"] == idx2)

                    pairs_checked += 1

                    # Check temporal non-overlap
                    if not segments_overlap(s1["start"], s1["end"], s2["start"], s2["end"], gap_tol):
                        continue  # Overlapping in time — skip

                    # Check similarity
                    sim = cosim(s1["embedding"], s2["embedding"])
                    if sim >= similarity_threshold:
                        graph[idx1].add(idx2)
                        graph[idx2].add(idx1)
                        edges_found += 1

    print(f"  Speakers: {n_speakers}, Pairs checked: {pairs_checked}, Edges found: {edges_found}")
    return dict(graph)

def find_connected_components(graph, n_total):
    """Find connected components via BFS."""
    visited = [False] * n_total
    components = []

    def bfs(start):
        comp = []
        queue = [start]
        while queue:
            node = queue.pop(0)
            if visited[node]:
                continue
            visited[node] = True
            comp.append(node)
            for neighbor in graph.get(node, []):
                if not visited[neighbor]:
                    queue.append(neighbor)
        return comp

    for i in range(n_total):
        if not visited[i] and (i in graph or any(i in g for g in graph.values())):
            # Only start component if node has ANY connection
            if i in graph or any(i in g for g in graph.values()):
                comp = bfs(i)
                if comp:
                    components.append(comp)

    return components

# =============================================================================
# Cluster assignment
# =============================================================================

def assign_clusters(segment_embeddings, components):
    """
    Assign cluster IDs to each segment.
    Segments in the same component get the same cluster ID.
    Segments not in any component keep their original pyannote ID as cluster.
    """
    # Build seg_idx -> component_id mapping
    seg_to_cluster = {}
    for cid, comp in enumerate(components):
        for seg_idx in comp:
            seg_to_cluster[seg_idx] = f"CLUSTER_{cid:03d}"

    # Assign clusters to all segments
    all_segs_with_cluster = []
    for speaker, segs in segment_embeddings.items():
        for seg in segs:
            seg_idx = seg["seg_idx"]
            cluster_id = seg_to_cluster.get(seg_idx, f"SINGLE_{speaker}")
            all_segs_with_cluster.append({
                "seg_idx": seg_idx,
                "speaker": speaker,
                "cluster": cluster_id,
                "start": seg["start"],
                "end": seg["end"],
                "embedding": seg["embedding"]
            })

    # Sort by segment index
    all_segs_with_cluster.sort(key=lambda x: x["seg_idx"])
    return all_segs_with_cluster

# =============================================================================
# Cluster-level resolution
# =============================================================================

def resolve_clusters_to_registry(segment_clusters, pyannote_to_name):
    """
    For each cluster, decide the resolved speaker name.
    Strategy: use majority vote among pyannote IDs in the cluster,
    then map through registry.
    If cluster contains segments from multiple pyannote IDs that are
    all mappable to the same canonical name, confidence is high.
    If cluster contains segments from different people, mark as ambiguous.
    """
    # Group segments by cluster
    cluster_segments = defaultdict(list)
    for seg in segment_clusters:
        cluster_segments[seg["cluster"]].append(seg)

    resolved = {}
    for cid, segs in cluster_segments.items():
        speaker_counts = defaultdict(int)
        for seg in segs:
            speaker_counts[seg["speaker"]] += 1

        # Dominant pyannote ID in this cluster
        dominant_speaker = max(speaker_counts, key=speaker_counts.get)
        count = speaker_counts[dominant_speaker]
        total = len(segs)

        # Map dominant through registry
        resolved_name = pyannote_to_name.get(dominant_speaker, None)
        if resolved_name:
            confidence = count / total
            resolved[cid] = {
                "speaker": resolved_name,
                "dominant_pyannote": dominant_speaker,
                "confidence": confidence,
                "n_segments": total,
                "is_single": cid.startswith("SINGLE")
            }
        else:
            resolved[cid] = {
                "speaker": "Unknown Speaker",
                "dominant_pyannote": dominant_speaker,
                "confidence": count / total,
                "n_segments": total,
                "is_single": cid.startswith("SINGLE")
            }

    return resolved

# =============================================================================
# Main
# =============================================================================

def main():
    ap = argparse.ArgumentParser(description="Per-segment embedding clustering benchmark")
    ap.add_argument("--asr", required=True)
    ap.add_argument("--diarization", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--gold-set", required=True)
    ap.add_argument("--structured", required=True)
    ap.add_argument("--embeddings", default=None)  # optional: reuse embeddings
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--similarity-threshold", type=float, default=0.85)
    ap.add_argument("--min-duration", type=float, default=1.5)
    ap.add_argument("--gap-tol", type=float, default=0.5)
    ap.add_argument("--dominance-threshold", type=float, default=0.60)
    ap.add_argument("--min-cluster-size", type=int, default=2)
    args = ap.parse_args()

    # Load registry
    registry = load_json(args.registry)
    pyannote_to_name = {}
    for sp in registry.get("speakers", []):
        for pid in sp.get("diarization_speaker_ids", []):
            pyannote_to_name[pid] = sp.get("display_name", sp["speaker_key"])

    print(f"Registry: {len(pyannote_to_name)} pyannote ID mappings")
    print(f"Similarity threshold: {args.similarity_threshold}")
    print(f"Min duration: {args.min_duration}s")
    print(f"Gap tolerance: {args.gap_tol}s")

    # Load embeddings (extract if not provided)
    if args.embeddings and os.path.exists(args.embeddings):
        print(f"Loading saved embeddings from {args.embeddings}")
        emb_data = load_json(args.embeddings)
        segment_embeddings = emb_data["segment_embeddings"]
    else:
        print("Extracting per-segment embeddings...")
        segment_embeddings, n_proc, n_skip, n_fail = extract_segment_embeddings(
            args.diarization, args.audio, args.device, args.min_duration
        )
        print(f"  Processed: {n_proc}, Skipped: {n_skip}, Failed: {n_fail}")

    # Build similarity graph
    graph = build_similarity_graph(segment_embeddings, args.similarity_threshold, args.gap_tol)

    # Build all_segs list for component finding
    all_segs = []
    for speaker, segs in segment_embeddings.items():
        for seg in segs:
            all_segs.append({
                "idx": seg["seg_idx"],
                "speaker": speaker,
                "start": seg["start"],
                "end": seg["end"],
                "embedding": seg["embedding"]
            })
    n_total = len(all_segs)

    # Find connected components
    print("  Finding connected components...")
    components = find_connected_components(graph, n_total)

    # Filter components by min size
    large_components = [c for c in components if len(c) >= args.min_cluster_size]
    print(f"  Total components: {len(components)}, Large (size>={args.min_cluster_size}): {len(large_components)}")

    # Assign clusters
    segment_clusters = assign_clusters(segment_embeddings, large_components)
    print(f"  Segments with cluster IDs: {len(segment_clusters)}")

    # Build cluster summary
    from collections import Counter
    cluster_counts = Counter(seg["cluster"] for seg in segment_clusters)
    merged_clusters = [c for c in cluster_counts if c.startswith("CLUSTER_")]
    print(f"  Merged clusters: {len(merged_clusters)}")
    print(f"  Single-segment (unchanged): {len([c for c in cluster_counts if c.startswith('SINGLE')])}")

    # Save embeddings and cluster map
    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    emb_out = args.out.replace(".json", "_embeddings.json")
    save_json({
        "segment_embeddings": segment_embeddings,
        "n_segments": len(all_segs)
    }, emb_out)

    # Build cluster map
    cluster_map = {
        "method": "per_segment_similarity_graph",
        "similarity_threshold": args.similarity_threshold,
        "gap_tol": args.gap_tol,
        "n_total_segments": n_total,
        "n_components": len(components),
        "n_large_components": len(large_components),
        "components": {f"CLUSTER_{i:03d}": c for i, c in enumerate(large_components)}
    }
    map_out = args.out.replace(".json", "_cluster_map.json")
    save_json(cluster_map, map_out)

    print(f"\nEmbeddings: {emb_out}")
    print(f"Cluster map: {map_out}")
    print(f"Full output: {args.out}")

    return {
        "n_segments": n_total,
        "n_components": len(large_components),
        "similarity_threshold": args.similarity_threshold
    }

if __name__ == "__main__":
    sys.exit(main())

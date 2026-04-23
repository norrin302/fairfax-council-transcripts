#!/usr/bin/env python3
"""Benchmark: compare Stage 3 baseline vs. baseline + embedding/clustering.

Inline implementation — no module imports required.
Handles the full pipeline: ASR → merge → embeddings → cluster → evaluate.

Usage (on Juggernaut):
  docker run --rm --gpus all \
    -v /mnt/disk1:/mnt/disk1 \
    -v /tmp:/work \
    --entrypoint python \
    fairfax-pipeline-diarize_pyannote \
    /work/bench_cluster/benchmark_clustering.py \
    --asr /mnt/disk1/.../faster-whisper_gpu_medium.json \
    --diarization /mnt/disk1/.../pyannote_segments.json \
    --audio /mnt/disk1/.../audio_16k_mono.wav \
    --registry .../speakers.json \
    --gold-set .../gold-set/apr-14-2026.json \
    --structured .../transcripts_structured/apr-14-2026.json \
    --out /work/bench_cluster/cluster_benchmark.json \
    --device cuda
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
import torch


# =============================================================================
# Inline helpers (duplicated from pipeline/src for self-contained execution)
# =============================================================================

def _seg_start(seg) -> float:
    return seg.get("start_seconds", seg.get("start", 0.0))


def _seg_end(seg) -> float:
    return seg.get("end_seconds", seg.get("end", 0.0))


def _to_segments(blocks: list[dict[str, Any]]) -> list:
    """Convert raw blocks to minimal Segment-like dicts."""
    from dataclasses import dataclass

    @dataclass
    class Segment:
        segment_id: str
        start: float
        end: float
        speaker_id: str
        text: str
        speaker_name: str = ""
        speaker_role: str = "unknown"
        speaker_confidence: float = 0.0
        merged_from: list = None
        needs_review: bool = False

    segs = []
    for b in blocks:
        s = Segment(
            segment_id=b.get("segment_id", ""),
            start=_seg_start(b),
            end=_seg_end(b),
            speaker_id=b.get("speaker_id", "UNKNOWN"),
            text=b.get("text", ""),
            speaker_name=b.get("speaker_name", ""),
            speaker_role=b.get("speaker_role", "unknown"),
            speaker_confidence=b.get("speaker_confidence", 0.0),
            merged_from=b.get("merged_from", []),
            needs_review=b.get("needs_review", False),
        )
        segs.append(s)
    return segs


def _to_dicts(segments: list) -> list[dict[str, Any]]:
    return [
        {
            "segment_id": s.segment_id,
            "start": s.start,
            "end": s.end,
            "speaker_id": s.speaker_id,
            "text": s.text,
            "speaker_name": s.speaker_name,
            "speaker_role": s.speaker_role,
            "speaker_confidence": s.speaker_confidence,
            "merged_from": s.merged_from,
            "needs_review": s.needs_review,
        }
        for s in segments
    ]


def merge_transcript_segments(
    asr_segments: list[dict],
    diar_segments: list[dict],
    min_duration: float = 1.5,
    dominance_threshold: float = 0.60,
) -> list[dict]:
    """Merge ASR + diarization by time overlap, then apply microblock cleanup."""
    merged = []
    for diar_seg in diar_segments:
        d_start = diar_seg.get("start", 0.0)
        d_end = diar_seg.get("end", 0.0)
        d_spk = diar_seg.get("speaker", "UNKNOWN")

        # Collect overlapping ASR words
        words_in = []
        for w in asr_segments:
            w_start = w.get("start", 0.0)
            w_end = w.get("end", 0.0)
            if w_start < d_end and w_end > d_start:
                words_in.append(w)

        if not words_in:
            text = ""
            start_s = d_start
            end_s = d_end
        else:
            starts = [w.get("start", 0.0) for w in words_in]
            ends = [w.get("end", 0.0) for w in words_in]
            text = " ".join(w.get("text", "") for w in words_in)
            start_s = min(starts)
            end_s = max(ends)

        merged.append({
            "segment_id": f"ms_{len(merged):05d}",
            "start_seconds": start_s,
            "end_seconds": end_s,
            "speaker_id": d_spk,
            "text": text,
            "merged_from": [w.get("segment_id", "") for w in words_in],
            "needs_review": d_spk == "UNKNOWN",
        })

    # Microblock cleanup: merge consecutive micro-blocks dominated by one speaker
    cleaned = []
    i = 0
    while i < len(merged):
        seg = merged[i]
        dur = _seg_end(seg) - _seg_start(seg)

        if dur >= min_duration or seg.get("speaker_id") != "UNKNOWN":
            cleaned.append(seg)
            i += 1
            continue

        # Cluster short UNKNOWN blocks
        cluster_start = i
        cluster_spk = {}
        cluster_dur = {}
        total_dur = 0.0

        while i < len(merged):
            cur = merged[i]
            cur_spk = cur.get("speaker_id", "UNKNOWN")
            cur_dur = _seg_end(cur) - _seg_start(cur)
            if cur_dur < min_duration and cur_spk == "UNKNOWN":
                cluster_spk[cur_spk] = cluster_spk.get(cur_spk, 0.0) + cur_dur
                cluster_dur[cur_spk] = cluster_dur.get(cur_spk, 0.0) + cur_dur
                total_dur += cur_dur
                i += 1
            else:
                break

        if total_dur < min_duration:
            # All short — check neighbors for dominant speaker
            if cleaned and i < len(merged):
                prev_spk = cleaned[-1].get("speaker_id", "UNKNOWN")
                next_spk = merged[i].get("speaker_id", "UNKNOWN") if i < len(merged) else "UNKNOWN"
                if prev_spk == next_spk and prev_spk != "UNKNOWN":
                    dominant_spk = prev_spk
                elif cluster_spk:
                    dominant_spk = max(cluster_spk, key=cluster_spk.get)
                else:
                    dominant_spk = "UNKNOWN"
            else:
                dominant_spk = max(cluster_spk, key=cluster_spk.get) if cluster_spk else "UNKNOWN"

            # Merge all in cluster
            merged_texts = [merged[j].get("text", "") for j in range(cluster_start, i)]
            merged_ids = [merged[j].get("segment_id", "") for j in range(cluster_start, i)]
            first_start = _seg_start(merged[cluster_start])
            last_end = _seg_end(merged[i - 1])

            cleaned.append({
                "segment_id": f"ms_{len(cleaned):05d}",
                "start_seconds": first_start,
                "end_seconds": last_end,
                "speaker_id": dominant_spk,
                "text": " ".join(merged_texts),
                "merged_from": merged_ids,
                "needs_review": dominant_spk == "UNKNOWN",
            })
        else:
            # Total duration is long enough — find dominant speaker
            if cluster_spk:
                dominant_spk = max(cluster_spk, key=cluster_spk.get)
                dom_frac = cluster_spk[dominant_spk] / total_dur if total_dur > 0 else 0
            else:
                dominant_spk = "UNKNOWN"
                dom_frac = 0.0

            if dom_frac >= dominance_threshold:
                merged_texts = [merged[j].get("text", "") for j in range(cluster_start, i)]
                merged_ids = [merged[j].get("segment_id", "") for j in range(cluster_start, i)]
                first_start = _seg_start(merged[cluster_start])
                last_end = _seg_end(merged[i - 1])
                cleaned.append({
                    "segment_id": f"ms_{len(cleaned):05d}",
                    "start_seconds": first_start,
                    "end_seconds": last_end,
                    "speaker_id": dominant_spk,
                    "text": " ".join(merged_texts),
                    "merged_from": merged_ids,
                    "needs_review": dominant_spk == "UNKNOWN",
                })
            else:
                # Not dominated — add individually, mark for review
                for j in range(cluster_start, i):
                    cur = merged[j]
                    cleaned.append({
                        "segment_id": cur.get("segment_id", f"orphan_{j}"),
                        "start_seconds": _seg_start(cur),
                        "end_seconds": _seg_end(cur),
                        "speaker_id": cur.get("speaker_id", "UNKNOWN"),
                        "text": cur.get("text", ""),
                        "merged_from": [cur.get("segment_id", "")],
                        "needs_review": True,
                    })

    return cleaned


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_registry(path: str):
    data = load_json(path)
    speaker_list = data.get("speakers", [])
    pyannote_to_name = {}
    for sp in speaker_list:
        for pid in sp.get("diarization_speaker_ids", []):
            pyannote_to_name[pid] = sp.get("display_name", sp["speaker_key"])
    return data, pyannote_to_name


def baseline_merge(asr, diar, pyannote_to_name, min_dur=1.5, dom_thresh=0.60):
    merged = merge_transcript_segments(asr, diar, min_dur, dom_thresh)
    for seg in merged:
        pid = seg.get("speaker_id", "")
        seg["speaker_name"] = pyannote_to_name.get(pid, "Unknown Speaker")
        if pid not in pyannote_to_name and pid != "UNKNOWN":
            seg["needs_review"] = True
    return merged


def cluster_aware_merge(asr, diar, cluster_map, pyannote_to_name, min_dur=1.5, dom_thresh=0.60):
    merged = merge_transcript_segments(asr, diar, min_dur, dom_thresh)
    for seg in merged:
        raw_pid = seg.get("speaker_id", "")
        cluster_id = cluster_map.get(raw_pid, raw_pid)
        # Prefer cluster ID, fall back to raw ID
        seg["speaker_name"] = pyannote_to_name.get(cluster_id, pyannote_to_name.get(raw_pid, "Unknown Speaker"))
        seg["raw_speaker_id"] = raw_pid
        seg["cluster_id"] = cluster_id
        if cluster_id not in pyannote_to_name and raw_pid not in pyannote_to_name:
            seg["needs_review"] = True
    return merged


def evaluate_vs_gold(segments, gold_turns):
    def find_overlap(s_start, s_end, turns):
        best_t, best_ov = None, 0.0
        for t in turns:
            t_start = t.get("start", 0)
            t_end = t.get("end", 0)
            ov = max(0, min(s_end, t_end) - max(s_start, t_start))
            if ov > best_ov:
                best_t, best_ov = t, ov
        return best_t, best_ov

    named = wrong = uwn = correct_unknown = 0
    errors = []

    for seg in segments:
        s_start = seg.get("start_seconds", 0)
        s_end = seg.get("end_seconds", 0)
        c_name = seg.get("speaker_name", "Unknown Speaker")

        gt, overlap = find_overlap(s_start, s_end, gold_turns)
        if not gt or overlap < 0.5:
            continue

        g_name = gt.get("speaker_name", "Unknown Speaker")

        if g_name not in ("Unknown Speaker", "Unknown"):
            named += 1
            if c_name == g_name:
                pass
            elif c_name == "Unknown Speaker":
                uwn += 1
                errors.append({"type": "unk_when_named", "gold": g_name, "cand": c_name})
            else:
                wrong += 1
                errors.append({"type": "wrong", "gold": g_name, "cand": c_name})
        else:
            if c_name == "Unknown Speaker":
                correct_unknown += 1

    return {
        "named_in_gold": named,
        "wrong": wrong,
        "unknown_when_named": uwn,
        "correct_unknown": correct_unknown,
        "match_rate": (named - wrong - uwn) / named if named else 0.0,
        "review_burden": sum(1 for s in segments if s.get("needs_review")),
        "total_segments": len(segments),
        "errors": errors,
    }


# =============================================================================
# Embedding extraction (uses pyannote.wespeaker via pyannote.audio)
# =============================================================================

def extract_speaker_embeddings(audio_path, diar_segments, device="cuda", min_dur=0.3):
    from pyannote.audio.pipelines.speaker_verification import PyannoteAudioPretrainedSpeakerEmbedding

    print(f"Loading embedding model pyannote/wespeaker-voxceleb-resnet34-LM on {device}...")
    emb_model = PyannoteAudioPretrainedSpeakerEmbedding(
        "pyannote/wespeaker-voxceleb-resnet34-LM",
        device=torch.device(device),
    )
    print(f"  Embedding dimension: {emb_model.dimension}")

    print(f"Loading audio: {audio_path}")
    y, sr = sf.read(audio_path, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    print(f"  Audio: {len(y)/sr:.1f}s at {sr}Hz")

    speakers = sorted(set(seg.get("speaker", "") for seg in diar_segments if seg.get("speaker")))
    speaker_embs = {sp: [] for sp in speakers}

    n_proc = n_skip = n_fail = 0

    for i, seg in enumerate(diar_segments):
        sp = seg.get("speaker", "")
        if not sp:
            continue

        seg_start = seg.get("start", 0)
        seg_end = seg.get("end", 0)
        seg_dur = seg_end - seg_start

        if seg_dur < min_dur:
            n_skip += 1
            continue

        start_s = int(seg_start * sr)
        end_s = int(seg_end * sr)
        y_seg = y[start_s:end_s]

        if len(y_seg) < sr * 0.1:
            n_skip += 1
            continue

        y_t = torch.from_numpy(y_seg).float().reshape(1, 1, -1)

        try:
            emb_vec = emb_model(y_t)  # (1, 256) ndarray
            if emb_vec.ndim > 1:
                emb_vec = emb_vec.reshape(-1)
            speaker_embs[sp].append(emb_vec)
            n_proc += 1
        except Exception:
            n_fail += 1
            continue

        if (i + 1) % 200 == 0:
            print(f"  [{i+1}/{len(diar_segments)}] proc={n_proc}, skip={n_skip}, fail={n_fail}")

    print(f"Embedding extraction: {n_proc} processed, {n_skip} skipped, {n_fail} failed")

    speaker_centroids = {}
    for sp, embs in speaker_embs.items():
        if not embs:
            print(f"  Warning: no embeddings for {sp}")
            speaker_centroids[sp] = [0.0] * emb_model.dimension
            continue
        arr = np.stack(embs)
        speaker_centroids[sp] = arr.mean(axis=0).tolist()

    return {
        "model": "pyannote/wespeaker-voxceleb-resnet34-LM",
        "device": device,
        "embedding_dim": emb_model.dimension,
        "n_segments_input": len(diar_segments),
        "n_segments_processed": n_proc,
        "n_segments_skipped": n_skip,
        "n_segments_failed": n_fail,
        "speakers": speakers,
        "speaker_centroids": speaker_centroids,
    }


def cluster_speakers(speaker_centroids, sim_thresh=0.75):
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics.pairwise import cosine_similarity

    speaker_list = list(speaker_centroids.keys())
    n_speakers = len(speaker_list)
    print(f"Clustering {n_speakers} speakers by embedding similarity...")

    emb_matrix = np.array([speaker_centroids[sp] for sp in speaker_list])
    sim_matrix = cosine_similarity(emb_matrix)
    np.fill_diagonal(sim_matrix, 1.0)

    n_clusters = n_speakers
    clustering = AgglomerativeClustering(
        n_clusters=n_clusters,
        metric="precomputed",
        linkage="average",
    )
    dist_matrix = 1.0 - sim_matrix
    np.fill_diagonal(dist_matrix, 0.0)
    labels = clustering.fit_predict(dist_matrix)

    raw_to_cluster = {}
    clusters = {}
    for i, sp in enumerate(speaker_list):
        cluster_id = f"CLUSTER_{labels[i]:02d}"
        raw_to_cluster[sp] = cluster_id
        clusters.setdefault(cluster_id, []).append(sp)

    print(f"  Raw speakers: {n_speakers}, Clusters: {len(clusters)}, Merges: {n_speakers - len(clusters)}")

    return {
        "method": "agglomerative_cosine_similarity",
        "similarity_threshold": sim_thresh,
        "n_raw_speakers": n_speakers,
        "n_clusters": len(clusters),
        "merges_performed": n_speakers - len(clusters),
        "raw_to_cluster": raw_to_cluster,
        "clusters": clusters,
    }


# =============================================================================
# Main benchmark
# =============================================================================

def main() -> int:
    ap = argparse.ArgumentParser(description="Benchmark clustering layer vs. baseline")
    ap.add_argument("--asr", required=True)
    ap.add_argument("--diarization", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--gold-set", required=True)
    ap.add_argument("--structured", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--similarity-threshold", type=float, default=0.75)
    ap.add_argument("--min-duration", type=float, default=1.5)
    ap.add_argument("--dominance-threshold", type=float, default=0.60)
    args = ap.parse_args()

    asr = load_json(args.asr)
    diar = load_json(args.diarization)
    registry_data, pyannote_to_name = load_registry(args.registry)
    gold = load_json(args.gold_set)

    asr_segs = asr.get("segments", [])
    diar_segs = diar.get("segments", [])
    gold_excerpts = gold.get("excerpts", [])

    print(f"\nASR: {len(asr_segs)} segments")
    print(f"Diarization: {len(diar_segs)} segments")
    print(f"Gold excerpts: {len(gold_excerpts)}")

    # =====================================================================
    # BASELINE
    # =====================================================================
    print("\n=== BASELINE (cleanup + registry v2.1) ===")
    baseline_segs = baseline_merge(
        asr_segs, diar_segs, pyannote_to_name,
        min_dur=args.min_duration,
        dom_thresh=args.dominance_threshold,
    )
    print(f"Segments: {len(baseline_segs)}")

    b_results = []
    for ex in gold_excerpts:
        r = evaluate_vs_gold(baseline_segs, ex.get("turns", []))
        r["excerpt_id"] = ex["excerpt_id"]
        b_results.append(r)

    b_wrong = sum(r["wrong"] for r in b_results)
    b_uwn = sum(r["unknown_when_named"] for r in b_results)
    b_named = sum(r["named_in_gold"] for r in b_results)
    b_match = (b_named - b_wrong - b_uwn) / b_named if b_named else 0.0
    b_review = sum(r["review_burden"] for r in b_results)
    b_distinct = len(set(s.get("speaker_name", "") for s in baseline_segs))

    print(f"Match: {b_match:.1%} | Wrong: {b_wrong} | UWN: {b_uwn} | Review: {b_review}/{len(baseline_segs)}")

    # =====================================================================
    # CANDIDATE
    # =====================================================================
    print("\n=== CANDIDATE (embeddings + clustering + registry v2.1) ===")
    print("Extracting speaker embeddings (this takes several minutes for full audio)...")

    emb_result = extract_speaker_embeddings(
        args.audio, diar_segs, device=args.device, min_dur=0.3
    )

    emb_out = Path(args.out).parent / "embeddings.json"
    with open(emb_out, "w") as f:
        json.dump(emb_result, f, indent=2)
    print(f"Embeddings: {emb_out}")

    cluster_result = cluster_speakers(
        emb_result["speaker_centroids"],
        sim_thresh=args.similarity_threshold,
    )

    cluster_out = Path(args.out).parent / "cluster_map.json"
    with open(cluster_out, "w") as f:
        json.dump(cluster_result, f, indent=2)
    print(f"Clusters: {cluster_out}")

    print("\nCluster details:")
    for cid, members in sorted(cluster_result["clusters"].items()):
        print(f"  {cid}: {members}")

    candidate_segs = cluster_aware_merge(
        asr_segs, diar_segs,
        cluster_result["raw_to_cluster"],
        pyannote_to_name,
        min_dur=args.min_duration,
        dom_thresh=args.dominance_threshold,
    )
    print(f"\nSegments: {len(candidate_segs)}")

    c_results = []
    for ex in gold_excerpts:
        r = evaluate_vs_gold(candidate_segs, ex.get("turns", []))
        r["excerpt_id"] = ex["excerpt_id"]
        c_results.append(r)

    c_wrong = sum(r["wrong"] for r in c_results)
    c_uwn = sum(r["unknown_when_named"] for r in c_results)
    c_named = sum(r["named_in_gold"] for r in c_results)
    c_match = (c_named - c_wrong - c_uwn) / c_named if c_named else 0.0
    c_review = sum(r["review_burden"] for r in c_results)
    c_distinct = len(set(s.get("speaker_name", "") for s in candidate_segs))

    print(f"Match: {c_match:.1%} | Wrong: {c_wrong} | UWN: {c_uwn} | Review: {c_review}/{len(candidate_segs)}")

    # =====================================================================
    # REPORT
    # =====================================================================
    improvement_wrong = b_wrong - c_wrong

    result = {
        "baseline": {
            "method": "cleanup + registry v2.1",
            "segments": len(baseline_segs),
            "named_in_gold": b_named,
            "wrong": b_wrong,
            "unknown_when_named": b_uwn,
            "correct_unknown": sum(r["correct_unknown"] for r in b_results),
            "match_rate": b_match,
            "review_burden": b_review,
            "distinct_speakers": b_distinct,
            "per_excerpt": {r["excerpt_id"]: {"wrong": r["wrong"], "uwn": r["unknown_when_named"], "match_rate": r["match_rate"]} for r in b_results},
        },
        "candidate": {
            "method": "embeddings + clustering + registry v2.1",
            "segments": len(candidate_segs),
            "named_in_gold": c_named,
            "wrong": c_wrong,
            "unknown_when_named": c_uwn,
            "correct_unknown": sum(r["correct_unknown"] for r in c_results),
            "match_rate": c_match,
            "review_burden": c_review,
            "distinct_speakers": c_distinct,
            "per_excerpt": {r["excerpt_id"]: {"wrong": r["wrong"], "uwn": r["unknown_when_named"], "match_rate": r["match_rate"]} for r in c_results},
            "clustering": {
                "n_raw_speakers": cluster_result["n_raw_speakers"],
                "n_clusters": cluster_result["n_clusters"],
                "merges_performed": cluster_result["merges_performed"],
            },
        },
        "improvement": {
            "wrong_attributions_reduced": improvement_wrong,
            "unknown_when_named_reduced": b_uwn - c_uwn,
            "match_rate_delta": c_match - b_match,
        },
        "recommendation": "READY" if improvement_wrong > 0 and c_match >= b_match else "NOT_READY",
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nReport: {out_path}")

    print("\n=== COMPARISON ===")
    print(f"Wrong attributions:  baseline={b_wrong}, candidate={c_wrong}, delta={improvement_wrong:+d}")
    print(f"Match rate:         baseline={b_match:.1%}, candidate={c_match:.1%}, delta={c_match-b_match:+.1%}")
    print(f"Distinct speakers:  baseline={b_distinct}, candidate={c_distinct}")
    print(f"Recommendation: {result['recommendation']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

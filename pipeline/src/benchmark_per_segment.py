#!/usr/bin/env python3
"""
benchmark_per_segment.py — Self-contained per-segment clustering benchmark

Compares:
  BASELINE: cleanup + registry v2.1 (current shipped pipeline)
  CANDIDATE: per-segment embeddings + similarity graph clustering + registry v2.1

Uses gold set evaluation with exact same logic for fair comparison.
"""

import argparse
import json
import os
import sys
from collections import defaultdict, Counter
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

# =============================================================================
# JSON helpers
# =============================================================================

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =============================================================================
# Cosine similarity
# =============================================================================

def cosim(a, b):
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# =============================================================================
# Registry loader
# =============================================================================

def load_registry(path):
    data = load_json(path)
    pyannote_to_name = {}
    for sp in data.get("speakers", []):
        for pid in sp.get("diarization_speaker_ids", []):
            pyannote_to_name[pid] = sp.get("display_name", sp["speaker_key"])
    return data, pyannote_to_name

# =============================================================================
# Cleanup blocks (from cleanup_blocks.py — inline for self-contained benchmark)
# =============================================================================

def _seg_start(seg):
    return seg.get("start_seconds", seg.get("start", 0.0))

def _seg_end(seg):
    return seg.get("end_seconds", seg.get("end", 0.0))

def _dur(seg):
    return max(0.0, _seg_end(seg) - _seg_start(seg))

def apply_microblock_cleanup(asr_segments, diarization_segments,
                           min_duration=1.5,
                           dominance_threshold=0.60,
                           skip_sandwich=False):
    blocks = []
    i = 0
    n_asr = len(asr_segments)

    while i < n_asr:
        seg = asr_segments[i]
        s_start = _seg_start(seg)
        s_end = _seg_end(seg)
        s_dur = _dur(seg)

        dia_in_seg = [d for d in diarization_segments
                      if _seg_start(d) < s_end and _seg_end(d) > s_start]
        if not dia_in_seg:
            blocks.append({
                "start": s_start, "end": s_end,
                "start_seconds": s_start, "end_seconds": s_end,
                "text": seg.get("text", ""),
                "speaker": None,
                "diarization_segments": [],
                "is_merged": False
            })
            i += 1
            continue

        speaker_dur = defaultdict(float)
        for d in dia_in_seg:
            ovl_start = max(_seg_start(d), s_start)
            ovl_end = min(_seg_end(d), s_end)
            speaker_dur[d["speaker"]] += max(0.0, ovl_end - ovl_start)

        total_dur = sum(speaker_dur.values()) or 1.0
        dominant = max(speaker_dur, key=lambda sp: speaker_dur[sp] / total_dur)
        dominance = speaker_dur[dominant] / total_dur

        text = seg.get("text", "")
        combined = [{"start": s_start, "end": s_end, "speaker": dominant,
                     "text": text, "dominance": dominance,
                     "diarization": dia_in_seg}]

        j = i + 1
        while j < n_asr and dominance >= dominance_threshold:
            next_seg = asr_segments[j]
            ns_start = _seg_start(next_seg)
            ns_end = _seg_end(next_seg)

            next_dia = [d for d in diarization_segments
                        if _seg_start(d) < ns_end and _seg_end(d) > ns_start]
            if not next_dia:
                break

            next_speaker_dur = defaultdict(float)
            for d in next_dia:
                ovl_start = max(_seg_start(d), ns_start)
                ovl_end = min(_seg_end(d), ns_end)
                next_speaker_dur[d["speaker"]] += max(0.0, ovl_end - ovl_start)

            next_total = sum(next_speaker_dur.values()) or 1.0
            next_dominant = max(next_speaker_dur, key=lambda sp: next_speaker_dur[sp] / next_total)
            next_dominance = next_speaker_dur[next_dominant] / next_total

            if next_dominant != dominant:
                break

            combined.append({
                "start": ns_start, "end": ns_end,
                "speaker": next_dominant,
                "text": next_seg.get("text", ""),
                "dominance": next_dominance,
                "diarization": next_dia
            })
            s_end = ns_end
            dominance = (speaker_dur[dominant] / total_dur)
            j += 1

        block_text = " ".join(c["text"] for c in combined)
        merged_start = combined[0]["start"]
        merged_end = combined[-1]["end"]

        if not skip_sandwich and len(combined) >= 3:
            first_sp = combined[0]["speaker"]
            last_sp = combined[-1]["speaker"]
            if first_sp == last_sp:
                middle_texts = [c["text"] for c in combined[1:-1]]
                block_text = combined[0]["text"] + " " + " ".join(middle_texts) + " " + combined[-1]["text"]

        blocks.append({
            "start": merged_start, "end": merged_end,
            "start_seconds": merged_start, "end_seconds": merged_end,
            "text": block_text,
            "speaker": dominant,
            "dominance": dominance,
            "diarization_segments": dia_in_seg,
            "is_merged": len(combined) > 1
        })
        i = j if j > i else i + 1

    return blocks

# =============================================================================
# Per-segment embedding extraction (uses working benchmark_clustering.py approach)
# =============================================================================

def extract_segment_embeddings(diarization_path, audio_path, device="cuda",
                                min_duration=1.5):
    """Extract embedding for each diarization segment individually."""
    from pyannote.audio.pipelines.speaker_verification import PyannoteAudioPretrainedSpeakerEmbedding

    print(f"  Loading embedding model pyannote/wespeaker-voxceleb-resnet34-LM on {device}...")
    emb_model = PyannoteAudioPretrainedSpeakerEmbedding(
        "pyannote/wespeaker-voxceleb-resnet34-LM",
        device=torch.device(device),
    )
    print(f"  Embedding dimension: {emb_model.dimension}")

    diar = load_json(diarization_path)
    diar_segments = diar["segments"]

    print(f"  Loading audio: {audio_path}")
    waveform, sample_rate = sf.read(audio_path, dtype="float32")
    if waveform.ndim > 1:
        waveform = waveform.mean(axis=1)
    print(f"  Audio: {waveform.shape[0]/sample_rate:.1f}s at {sample_rate}Hz")

    segment_embeddings = {}
    n_proc = 0
    n_skip = 0
    n_fail = 0

    for i, seg in enumerate(diar_segments):
        start = seg["start"]
        end = seg["end"]
        duration = end - start
        speaker = seg["speaker"]

        if duration < min_duration:
            n_skip += 1
            continue

        start_s = int(start * sample_rate)
        end_s = int(end * sample_rate)
        segment_wav = waveform[start_s:end_s]

        if len(segment_wav) < sample_rate * 0.1:
            n_skip += 1
            continue

        try:
            y_t = torch.from_numpy(segment_wav).float().reshape(1, 1, -1)
            emb = emb_model(y_t)
            if emb is None:
                n_skip += 1
                continue
            if hasattr(emb, 'numpy'):
                emb = emb.numpy()
            if emb.ndim > 1:
                emb = emb.squeeze()
            key = f"{speaker}_{i}"
            segment_embeddings[key] = {
                "embedding": emb.tolist(),
                "start": start,
                "end": end,
                "speaker": speaker,
                "seg_idx": i
            }
            n_proc += 1
        except Exception as e:
            n_fail += 1
            continue

        if (i + 1) % 200 == 0:
            print(f"  [{i+1}/{len(diar_segments)}] proc={n_proc}, skip={n_skip}, fail={n_fail}")

    print(f"  Embedding extraction: {n_proc} processed, {n_skip} skipped, {n_fail} failed")
    return segment_embeddings, n_proc, n_skip, n_fail

# =============================================================================
# Per-segment similarity graph + clustering
# =============================================================================

def build_similarity_graph(segment_embeddings, similarity_threshold=0.85, gap_tol=0.5):
    """
    Connect segments with different pyannote IDs, non-overlapping times,
    and cosine similarity >= threshold.
    """
    all_segs = []
    for key, seg in segment_embeddings.items():
        all_segs.append({
            "key": key,
            "speaker": seg["speaker"],
            "start": seg["start"],
            "end": seg["end"],
            "embedding": seg["embedding"],
            "seg_idx": seg["seg_idx"]
        })

    all_segs.sort(key=lambda x: x["seg_idx"])
    n_segs = len(all_segs)
    print(f"  Building similarity graph for {n_segs} segments...")

    speaker_segs = defaultdict(list)
    for s in all_segs:
        speaker_segs[s["speaker"]].append(s)

    speakers = list(speaker_segs.keys())
    graph = defaultdict(set)
    edges_found = 0

    for i, sp1 in enumerate(speakers):
        for sp2 in speakers[i+1:]:
            for seg1 in speaker_segs[sp1]:
                for seg2 in speaker_segs[sp2]:
                    # Temporal non-overlap: seg1 ends before seg2 starts (with gap_tol)
                    if not (seg1["end"] <= seg2["start"] - gap_tol or
                           seg2["end"] <= seg1["start"] - gap_tol):
                        continue

                    sim = cosim(seg1["embedding"], seg2["embedding"])
                    if sim >= similarity_threshold:
                        graph[seg1["key"]].add(seg2["key"])
                        graph[seg2["key"]].add(seg1["key"])
                        edges_found += 1

    print(f"  Speakers: {len(speakers)}, Edges found: {edges_found}")
    return graph, all_segs

def find_components(graph, all_segs):
    """Find connected components via BFS."""
    seg_to_comp = {}
    visited = set()

    for seg in all_segs:
        key = seg["key"]
        if key in visited:
            continue
        comp = []
        queue = [key]
        while queue:
            k = queue.pop(0)
            if k in visited:
                continue
            visited.add(k)
            comp.append(k)
            for nb in graph.get(k, []):
                if nb not in visited:
                    queue.append(nb)
        if comp:
            comp_id = f"CLUSTER_{len([c for c in seg_to_comp.values() if c]):03d}"
            for k in comp:
                seg_to_comp[k] = comp_id

    return seg_to_comp

# =============================================================================
# Registry mapping
# =============================================================================

def map_segments_to_names(blocks, pyannote_to_name, cluster_info=None):
    """
    Map each block to a speaker name using dominant diarization speaker.
    If cluster_info is provided, use cluster-aware resolution:
    - For segments in a cluster, use the cluster's dominant pyannote ID
    - This lets us re-attribute SPEAKER_07 segments to SPEAKER_06 cluster
    """
    result = []
    for block in blocks:
        start = block["start"]
        end = block["end"]
        dia_segs = block.get("diarization_segments", [])
        raw_speaker = block.get("speaker")

        if not dia_segs:
            result.append({
                "start": start, "end": end,
                "speaker_raw": None,
                "speaker_public": "Unknown Speaker",
                "speaker_status": "unresolved",
                "needs_review": True,
                "review_reason": "no_diarization"
            })
            continue

        speaker_dur = defaultdict(float)
        for d in dia_segs:
            ovl_start = max(d["start"], start)
            ovl_end = min(d["end"], end)
            speaker_dur[d["speaker"]] += max(0.0, ovl_end - ovl_start)


        total_dur = sum(speaker_dur.values()) or 1.0
        dominant = max(speaker_dur, key=lambda sp: speaker_dur[sp] / total_dur)
        dominance = speaker_dur[dominant] / total_dur

        # Cluster-aware: if the dominant speaker is part of a multi-speaker cluster,
        # use the cluster's dominant pyannote ID (same-person reassignment case)
        if cluster_info and raw_speaker in cluster_info.get("speaker_cluster", {}):
            cid = cluster_info["speaker_cluster"][raw_speaker]
            cluster_data = cluster_info["clusters"].get(cid, {})
            if not cluster_data.get("is_single"):
                # Use cluster's dominant speaker instead
                dominant = cluster_data.get("dominant_pyannote", dominant)

        mapped_name = pyannote_to_name.get(dominant, None)
        if mapped_name:
            status = "approved"
            needs_review = False
            reason = ""
        else:
            mapped_name = "Unknown Speaker"
            status = "unresolved"
            needs_review = True
            reason = f"unmapped_speaker:{dominant}"

        result.append({
            "start": start, "end": end,
            "speaker_raw": dominant,
            "speaker_public": mapped_name,
            "speaker_status": status,
            "needs_review": needs_review,
            "review_reason": reason,
            "confidence": dominance,
            "text": block.get("text", "")[:100]
        })

    return result

# =============================================================================
# Gold set evaluation
# =============================================================================

def evaluate_gold(mapped_segments, gold):
    correct = 0
    wrong = 0
    unknown_when_named = 0
    correct_unknown = 0

    per_excerpt = {}

    for ex in gold.get("excerpts", []):
        ex_id = ex["excerpt_id"]
        ex_wrong = 0
        ex_uwn = 0
        ex_correct = 0
        ex_total = len(ex["turns"])

        for gt in ex["turns"]:
            gs = gt["start"]
            ge = gt["end"]
            gold_name = gt["speaker_name"]
            gold_name_is_unknown = gold_name in ("Unknown Speaker", "Unknown")

            overlapping = [s for s in mapped_segments
                          if s["start"] < ge and s["end"] > gs]

            if not overlapping:
                continue

            overlaps = [(s, min(s["end"], ge) - max(s["start"], gs))
                        for s in overlapping]
            dominant_seg = max(overlaps, key=lambda x: x[1])[0]
            mapped_name = dominant_seg["speaker_public"]
            mapped_status = dominant_seg["speaker_status"]

            if gold_name_is_unknown:
                if mapped_status in ("unresolved", "unknown") or mapped_name == "Unknown Speaker":
                    correct_unknown += 1
                    ex_correct += 1
                else:
                    unknown_when_named += 1
                    ex_uwn += 1
            else:
                if mapped_name == gold_name:
                    correct += 1
                    ex_correct += 1
                elif mapped_name == "Unknown Speaker":
                    unknown_when_named += 1
                    ex_uwn += 1
                else:
                    wrong += 1
                    ex_wrong += 1

        match_rate = ex_correct / ex_total if ex_total > 0 else 0.0
        per_excerpt[ex_id] = {
            "correct": ex_correct,
            "wrong": ex_wrong,
            "unknown_when_named": ex_uwn,
            "match_rate": round(match_rate, 4)
        }

    total = correct + wrong + unknown_when_named
    match_rate = correct / total if total > 0 else 0.0
    named_in_gold = correct + wrong + unknown_when_named

    return {
        "named_in_gold": named_in_gold,
        "correct": correct,
        "wrong": wrong,
        "unknown_when_named": unknown_when_named,
        "correct_unknown": correct_unknown,
        "match_rate": round(match_rate, 4),
        "per_excerpt": per_excerpt
    }

# =============================================================================
# Main
# =============================================================================

def main():
    ap = argparse.ArgumentParser(description="Per-segment clustering benchmark")
    ap.add_argument("--asr", required=True)
    ap.add_argument("--diarization", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--gold-set", required=True)
    ap.add_argument("--structured", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--similarity-threshold", type=float, default=0.85)
    ap.add_argument("--min-duration", type=float, default=1.5)
    ap.add_argument("--dominance-threshold", type=float, default=0.60)
    ap.add_argument("--gap-tol", type=float, default=0.5)
    ap.add_argument("--min-cluster-size", type=int, default=2)
    args = ap.parse_args()

    # Load data
    asr = load_json(args.asr)
    diar = load_json(args.diarization)
    gold = load_json(args.gold_set)
    registry_data, pyannote_to_name = load_registry(args.registry)

    asr_segs = asr["segments"]
    diar_segs = diar["segments"]

    print(f"\nASR: {len(asr_segs)} segments")
    print(f"Diarization: {len(diar_segs)} segments")
    print(f"Gold excerpts: {gold['total_excerpts']}")

    # -------------------------------------------------------------------------
    # BASELINE: cleanup + registry v2.1
    # -------------------------------------------------------------------------
    print("\n=== BASELINE (cleanup + registry v2.1) ===")
    blocks = apply_microblock_cleanup(
        asr_segs, diar_segs,
        min_duration=args.min_duration,
        dominance_threshold=args.dominance_threshold
    )
    mapped_baseline = map_segments_to_names(blocks, pyannote_to_name)
    eval_baseline = evaluate_gold(mapped_baseline, gold)
    review_blocks = sum(1 for b in blocks if b.get("speaker") is None)
    print(f"Segments: {len(blocks)}")
    print(f"Match: {eval_baseline['match_rate']*100:.1f}% | Wrong: {eval_baseline['wrong']} | "
          f"UWN: {eval_baseline['unknown_when_named']} | Review: {review_blocks}/{len(blocks)}")

    # -------------------------------------------------------------------------
    # CANDIDATE: per-segment embeddings + clustering + registry v2.1
    # -------------------------------------------------------------------------
    print("\n=== CANDIDATE (per-segment embeddings + clustering + registry v2.1) ===")
    emb_cache = args.out.replace(".json", "_emb_cache.json")
    if os.path.exists(emb_cache):
        print(f"Loading cached embeddings from {emb_cache}")
        emb_data = load_json(emb_cache)
        seg_emb = emb_data["segment_embeddings"]
    else:
        print("Extracting per-segment embeddings...")
        seg_emb, n_proc, n_skip, n_fail = extract_segment_embeddings(
            args.diarization, args.audio, args.device, args.min_duration
        )
        save_json({"segment_embeddings": seg_emb, "n_segments": len(seg_emb)}, emb_cache)
        print(f"  Saved to {emb_cache}")

    graph, all_segs = build_similarity_graph(seg_emb, args.similarity_threshold, args.gap_tol)
    seg_to_cluster = find_components(graph, all_segs)
    n_distinct = len(set(seg_to_cluster.values()))
    n_large = len([c for c in set(seg_to_cluster.values())
                   if sum(1 for v in seg_to_cluster.values() if v == c) >= args.min_cluster_size])

    # Build cluster info for cluster-aware mapping
    # For each cluster with multiple pyannote IDs, find the dominant ID
    from collections import defaultdict as dd2
    cluster_pyannote_votes = dd2(lambda: dd2(int))
    for seg_key, cid in seg_to_cluster.items():
        # Find the original segment
        seg_data = seg_emb.get(seg_key)
        if seg_data:
            cluster_pyannote_votes[cid][seg_data["speaker"]] += 1

    clusters = {}
    speaker_cluster = {}  # pyannote_id -> cluster_id
    for cid, votes in cluster_pyannote_votes.items():
        dominant = max(votes, key=lambda sp: votes[sp])
        total = sum(votes.values())
        clusters[cid] = {
            "dominant_pyannote": dominant,
            "pyannote_votes": dict(votes),
            "is_single": len(votes) == 1,
            "n_segments": total
        }
        for sp in votes:
            speaker_cluster[sp] = cid

    cluster_info = {"clusters": clusters, "speaker_cluster": speaker_cluster}

    # Report merge opportunities
    merged = [c for c in clusters if not clusters[c]["is_single"]]
    print(f"  Segments in clusters: {len(seg_to_cluster)}")
    print(f"  Distinct clusters: {n_distinct}, Large (size>={args.min_cluster_size}): {n_large}")
    print(f"  Merge opportunities (multi-pyannote clusters): {len(merged)}")
    if merged:
        for cid in merged[:5]:
            c = clusters[cid]
            print(f"    {cid}: {c['dominant_pyannote']} ({c['pyannote_votes']})")

    mapped_candidate = map_segments_to_names(blocks, pyannote_to_name, cluster_info=cluster_info)
    eval_candidate = evaluate_gold(mapped_candidate, gold)

    print(f"Segments: {len(blocks)}")
    print(f"Match: {eval_candidate['match_rate']*100:.1f}% | Wrong: {eval_candidate['wrong']} | "
          f"UWN: {eval_candidate['unknown_when_named']} | Review: {review_blocks}/{len(blocks)}")
    print(f"Clusters: {n_distinct}, Large (size>={args.min_cluster_size}): {n_large}")

    # -------------------------------------------------------------------------
    # COMPARISON
    # -------------------------------------------------------------------------
    print("\n=== COMPARISON ===")
    delta_wrong = eval_candidate['wrong'] - eval_baseline['wrong']
    delta_match = (eval_candidate['match_rate'] - eval_baseline['match_rate']) * 100

    print(f"Wrong attributions:  baseline={eval_baseline['wrong']}, "
          f"candidate={eval_candidate['wrong']}, delta={delta_wrong:+d}")
    print(f"Match rate:         baseline={eval_baseline['match_rate']*100:.1f}%, "
          f"candidate={eval_candidate['match_rate']*100:.1f}%, delta={delta_match:+.1f}%")
    print(f"UWN:                 baseline={eval_baseline['unknown_when_named']}, "
          f"candidate={eval_candidate['unknown_when_named']}")

    improve = eval_candidate['wrong'] < eval_baseline['wrong']
    material = delta_wrong <= -3
    rec = "READY" if (improve and material) else "NOT_READY"
    print(f"\nRecommendation: {rec}")

    # Save report
    report = {
        "baseline": {
            "method": "cleanup + registry v2.1",
            "segments": len(blocks),
            **eval_baseline,
            "distinct_speakers": len(set(b.get("speaker") for b in blocks if b.get("speaker")))
        },
        "candidate": {
            "method": "per_segment_embeddings + similarity_graph + registry v2.1",
            "segments": len(blocks),
            **eval_candidate,
            "similarity_threshold": args.similarity_threshold,
            "gap_tol": args.gap_tol,
            "n_clusters": n_distinct,
            "n_large_clusters": n_large,
            "distinct_speakers": n_distinct
        },
        "improvement": {
            "wrong_attributions_reduced": eval_baseline['wrong'] - eval_candidate['wrong'],
            "unknown_when_named_reduced": eval_baseline['unknown_when_named'] - eval_candidate['unknown_when_named'],
            "match_rate_delta_pct": round(delta_match, 2)
        },
        "recommendation": rec
    }

    save_json(report, args.out)
    print(f"\nReport: {args.out}")
    return 0 if rec == "READY" else 1

if __name__ == "__main__":
    sys.exit(main())

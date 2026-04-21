#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def load_embeddings(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"Expected list JSON: {path}")
    base = path.parent
    rows = []
    for row in data:
        if isinstance(row, dict) and (not isinstance(row.get("embedding"), list) or not row.get("embedding")) and row.get("embedding_path"):
            emb_path = Path(str(row["embedding_path"]))
            if not emb_path.is_absolute():
                emb_path = base / emb_path
            if not emb_path.exists() and str(emb_path).startswith("/work/"):
                host_path = Path(str(emb_path).replace("/work/", "/mnt/disk1/fairfax-council-transcripts/", 1))
                if host_path.exists():
                    emb_path = host_path
            if emb_path.exists():
                payload = json.loads(emb_path.read_text(encoding="utf-8"))
                merged = dict(row)
                if isinstance(payload, dict) and isinstance(payload.get("embedding"), list):
                    merged["embedding"] = payload["embedding"]
                rows.append(merged)
                continue
        rows.append(row)
    return rows


def mean_embedding(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []
    dims = len(vectors[0])
    out = [0.0] * dims
    for vec in vectors:
        for i, value in enumerate(vec):
            out[i] += value
    return [value / len(vectors) for value in out]


def main() -> int:
    ap = argparse.ArgumentParser(description="Match candidate speaker embeddings against approved reference embeddings")
    ap.add_argument("references", help="JSON list of approved embedding records")
    ap.add_argument("candidates", help="JSON list of candidate embedding records")
    ap.add_argument("--out", required=True, help="Output JSON path")
    ap.add_argument("--accept-threshold", type=float, default=0.72)
    ap.add_argument("--margin-threshold", type=float, default=0.03)
    args = ap.parse_args()

    reference_rows = load_embeddings(Path(args.references))
    candidate_rows = load_embeddings(Path(args.candidates))

    ref_vectors: dict[str, list[list[float]]] = defaultdict(list)
    for row in reference_rows:
        name = str(row.get("approved_identity") or row.get("name") or "").strip()
        emb = row.get("embedding")
        if name and isinstance(emb, list) and emb:
            ref_vectors[name].append(emb)

    ref_means = {name: mean_embedding(vectors) for name, vectors in ref_vectors.items()}

    by_candidate: dict[str, list[dict]] = defaultdict(list)
    for row in candidate_rows:
        speaker_id = str(row.get("speaker_id") or "").strip()
        emb = row.get("embedding")
        if speaker_id and isinstance(emb, list) and emb:
            by_candidate[speaker_id].append(row)

    results = []
    for speaker_id, rows in by_candidate.items():
        clip_scores: list[dict] = []
        aggregate_scores: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            emb = row["embedding"]
            scores = {name: cosine_similarity(emb, ref_mean) for name, ref_mean in ref_means.items()}
            ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
            best_name, best_score = ranked[0] if ranked else ("", 0.0)
            second_score = ranked[1][1] if len(ranked) > 1 else 0.0
            clip_scores.append(
                {
                    "clip_path": row.get("clip_path") or row.get("path") or "",
                    "best_match": best_name,
                    "best_score": round(best_score, 4),
                    "second_score": round(second_score, 4),
                    "all_scores": {k: round(v, 4) for k, v in ranked},
                }
            )
            for name, score in scores.items():
                aggregate_scores[name].append(score)

        averaged = {name: sum(vals) / len(vals) for name, vals in aggregate_scores.items() if vals}
        ranked = sorted(averaged.items(), key=lambda kv: kv[1], reverse=True)
        best_name, best_score = ranked[0] if ranked else ("", 0.0)
        second_score = ranked[1][1] if len(ranked) > 1 else 0.0
        support = sum(1 for clip in clip_scores if clip["best_match"] == best_name)

        if best_score >= args.accept_threshold and (best_score - second_score) >= args.margin_threshold and support >= 2:
            status = "accepted"
        elif best_name:
            status = "review"
        else:
            status = "unknown"

        results.append(
            {
                "speaker_id": speaker_id,
                "status": status,
                "best_match": best_name,
                "best_score": round(best_score, 4),
                "second_score": round(second_score, 4),
                "margin": round(best_score - second_score, 4),
                "supporting_clips": support,
                "clip_scores": clip_scores,
            }
        )

    results.sort(key=lambda row: (row["status"] != "accepted", -row["best_score"], row["speaker_id"]))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Group unknown speaker turns into voice clusters for bulk labeling.

Uses text-based TF-IDF cosine similarity when per-segment embeddings are
unavailable.  Loads confirmed speaker turns as reference centroids, scores
each unknown turn against them, groups consecutive unknowns that share the
same best-match speaker, and writes reviews/<meeting_id>-voice-clusters.json.

Usage:
    python3 scripts/cluster_for_review.py apr-14-2026
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# TF-IDF from stdlib (no sklearn/numpy required)
# ---------------------------------------------------------------------------

STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you",
    "your", "yours", "yourself", "yourselves", "he", "him", "his",
    "himself", "she", "her", "hers", "herself", "it", "its", "itself",
    "they", "them", "their", "theirs", "themselves", "what", "which",
    "who", "whom", "this", "that", "these", "those", "am", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "having",
    "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if",
    "or", "because", "as", "until", "while", "of", "at", "by", "for",
    "with", "about", "against", "between", "into", "through", "during",
    "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how",
    "all", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too",
    "very", "s", "t", "can", "will", "just", "don", "should", "now",
    "d", "ll", "m", "o", "re", "ve", "y", "ain", "aren", "couldn",
    "didn", "doesn", "hadn", "hasn", "haven", "isn", "ma", "mightn",
    "mustn", "needn", "shan", "shouldn", "wasn", "weren", "won", "wouldn",
}


def tokenize(text: str) -> list[str]:
    """Lowercase, extract word tokens, drop stop words."""
    return [
        w for w in re.sub(r"[^a-z0-9\s]", " ", text.lower()).split()
        if w not in STOP_WORDS and len(w) > 2
    ]


def build_vocabulary(texts: list[str], min_df: int = 1) -> dict[str, int]:
    """Map each term to a zero-based index."""
    doc_freq: Counter[str] = Counter()
    for text in texts:
        doc_freq.update(set(tokenize(text)))
    return {term: idx for idx, term in enumerate(t for t, c in doc_freq.items() if c >= min_df)}


def tfidf_vectors(texts: list[str], vocab: dict[str, int]) -> list[dict[str, float]]:
    """Return a list of sparse TF-IDF dicts, one per text."""
    n = len(texts)
    idf: dict[str, float] = {}
    tf_list: list[dict[str, int]] = []

    # Pass 1: token counts
    for text in texts:
        tokens = tokenize(text)
        counts: Counter[str] = Counter(tokens)
        tf_list.append(dict(counts))

    # IDF per term
    for term, idx in vocab.items():
        df = sum(1 for tf in tf_list if term in tf)
        idf[term] = math.log((n + 1) / (df + 1)) + 1  # smooth

    # Sparse TF-IDF vectors
    vectors: list[dict[str, float]] = []
    for tf in tf_list:
        vec = {term: (count / max(1, len(tf))) * idf.get(term, 0) for term, count in tf.items() if term in vocab}
        vectors.append(vec)
    return vectors


def cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity between two sparse TF-IDF vectors."""
    dot = sum(a.get(t, 0) * b.get(t, 0) for t in set(a) & set(b))
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

CONFIDENCE_THRESHOLD = 0.25   # minimum cosine sim to claim a match
MIN_CLUSTER_SIZE = 1          # singletons with no confident match go to list


def load_structured(meeting_id: str) -> dict:
    path = REPO_ROOT / "transcripts_structured" / f"{meeting_id}.json"
    if not path.exists():
        raise SystemExit(f"Structured transcript not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def speaker_key(name: str) -> str:
    return name.lower().replace(" ", "").replace("-", "").replace("'", "")


def compute_clusters(structured: dict, confidence_threshold: float = 0.25) -> dict:
    """Return the clusters + singletons structure."""
    turns = structured.get("turns", [])

    # Separate confirmed vs unknown
    confirmed: list[dict] = []   # turns with a known speaker
    unknowns: list[dict] = []    # turns that are unknown

    for t in turns:
        status = t.get("speaker_status", "")
        public = t.get("speaker_public", "") or ""
        raw = t.get("speaker_raw", "") or ""
        # 'unknown' speaker_status = unlabeled; also any 'UNKNOWN' raw
        if status == "unknown" or raw.upper() == "UNKNOWN":
            unknowns.append(t)
        elif status in ("approved", "mixed") and public:
            confirmed.append(t)

    if not unknowns:
        return {"meeting_id": structured["meeting"]["meeting_id"], "clusters": [], "singletons": []}

    if not confirmed:
        # No reference — can't cluster
        return {
            "meeting_id": structured["meeting"]["meeting_id"],
            "clusters": [],
            "singletons": [t["turn_id"] for t in unknowns],
        }

    # Group confirmed turns by unique speaker_public name
    by_speaker: dict[str, list[dict]] = defaultdict(list)
    for t in confirmed:
        by_speaker[t["speaker_public"]].append(t)

    # Build a reference TF-IDF centroid per speaker from all their turns
    speaker_texts: dict[str, list[str]] = {sp: [t["text"] for t in turns] for sp, turns in by_speaker.items()}
    all_texts = [t["text"] for t in confirmed]
    vocab = build_vocabulary(all_texts)

    centroids: dict[str, dict[str, float]] = {}
    for sp, texts in speaker_texts.items():
        vecs = tfidf_vectors(texts, vocab)
        # Centroid = mean vector
        centroid: defaultdict[str, float] = defaultdict(float)
        for vec in vecs:
            for term, val in vec.items():
                centroid[term] += val / len(vecs)
        centroids[sp] = dict(centroid)

    speaker_keys = list(centroids.keys())

    # Score each unknown turn
    turn_assignments: list[tuple[str, str, float]] = []  # (turn_id, speaker, score)
    for t in unknowns:
        text = t.get("text", "")
        if not text.strip():
            turn_assignments.append((t["turn_id"], "", 0.0))
            continue

        vec = tfidf_vectors([text], vocab)[0]
        best_sp = ""
        best_score = 0.0
        for sp in speaker_keys:
            score = cosine_similarity(vec, centroids[sp])
            if score > best_score:
                best_score = score
                best_sp = sp
        turn_assignments.append((t["turn_id"], best_sp, best_score))

    # Build clusters: consecutive unknowns with same best speaker
    clusters_out: list[dict] = []
    singletons: list[str] = []

    i = 0
    while i < len(unknowns):
        t = unknowns[i]
        turn_id, best_sp, best_score = turn_assignments[i]

        if best_score < confidence_threshold or not best_sp:
            singletons.append(turn_id)
            i += 1
            continue

        # Collect consecutive unknowns matching the same speaker
        cluster_turns = [t]
        j = i + 1
        while j < len(unknowns):
            nid, nsp, nscore = turn_assignments[j]
            if nsp == best_sp and nscore >= confidence_threshold:
                cluster_turns.append(unknowns[j])
                j += 1
            else:
                break

        confidence = sum(
            score for tid, sp, score in turn_assignments[i:j]
            if sp == best_sp
        ) / (j - i)

        clusters_out.append({
            "cluster_id": f"cluster_{len(clusters_out) + 1:03d}",
            "likely_speaker": best_sp,
            "likely_speaker_key": speaker_key(best_sp),
            "confidence": round(confidence, 3),
            "turn_ids": [ct["turn_id"] for ct in cluster_turns],
            "texts": [ct["text"] for ct in cluster_turns],
        })
        i = j

    return {
        "meeting_id": structured["meeting"]["meeting_id"],
        "clusters": clusters_out,
        "singletons": singletons,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Cluster unknown speaker turns for review")
    ap.add_argument("meeting_id", help="e.g. apr-14-2026")
    ap.add_argument(
        "--threshold", type=float, default=0.25,
        help="Minimum cosine similarity to assign a speaker (default: 0.25)",
    )
    args = ap.parse_args()

    structured = load_structured(args.meeting_id)
    result = compute_clusters(structured, confidence_threshold=args.threshold)

    out_path = REPO_ROOT / "reviews" / f"{args.meeting_id}-voice-clusters.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"Clusters: {len(result['clusters'])}")
    print(f"Singletons: {len(result['singletons'])}")
    print(f"Output: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

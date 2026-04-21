#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def extract_candidates(text: str) -> list[tuple[str, str, int]]:
    candidates: list[tuple[str, str, int]] = []
    s = " ".join((text or "").split())

    patterns = [
        (r"\bmy name is ([A-Z][a-z]+(?: [A-Z][a-z]+){1,3})\b", "self_intro", 5),
        (r"\bthis is ([A-Z][a-z]+(?: [A-Z][a-z]+){1,3})\b", "self_intro", 4),
        (r"\bGood evening, ([A-Z][a-z]+(?: [A-Z][a-z]+){1,3})(?:,|\b)", "opening_intro", 3),
    ]

    for pattern, reason, weight in patterns:
        for match in re.finditer(pattern, s):
            name = match.group(1).strip()
            if len(name.split()) < 2:
                continue
            candidates.append((name, reason, weight))

    # Address / residency cues strengthen opening introductions.
    if re.search(r"\b\d{3,5}\s+[A-Z][a-zA-Z]+", s) or re.search(r"\bI (?:live|have lived|am here)\b", s, re.I):
        enriched = []
        for name, reason, weight in candidates:
            if reason == "opening_intro":
                enriched.append((name, "opening_intro_with_context", weight + 1))
            else:
                enriched.append((name, reason, weight))
        candidates = enriched

    return candidates


def load_rows(path: Path) -> list[dict]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise SystemExit(f"Expected list in JSON review sheet: {path}")
        return data

    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description="Pre-seed obvious reference voice review candidates")
    ap.add_argument("review_sheet", help="review_sheet.json or review_sheet.csv")
    ap.add_argument("--out-json", required=True, help="Output JSON path")
    ap.add_argument("--out-csv", default="", help="Optional output CSV path")
    args = ap.parse_args()

    rows = load_rows(Path(args.review_sheet))

    evidence_by_speaker: dict[str, list[tuple[str, str, int, str]]] = defaultdict(list)
    for row in rows:
        speaker_id = str(row.get("speaker_id") or "").strip()
        excerpt = str(row.get("transcript_excerpt") or "")
        for name, reason, weight in extract_candidates(excerpt):
            evidence_by_speaker[speaker_id].append((name, reason, weight, excerpt))

    suggestions: dict[str, dict] = {}
    for speaker_id, items in evidence_by_speaker.items():
        scores = Counter()
        reasons = defaultdict(list)
        for name, reason, weight, excerpt in items:
            scores[name] += weight
            reasons[name].append({"reason": reason, "weight": weight, "excerpt": excerpt})
        if not scores:
            continue
        best_name, best_score = scores.most_common(1)[0]
        second_score = scores.most_common(2)[1][1] if len(scores) > 1 else 0
        support = len(reasons[best_name])

        strong_evidence = any(e[1] in {"self_intro", "opening_intro_with_context"} for e in items if e[0] == best_name)
        if best_score >= 8 and best_score >= second_score + 3 and support >= 2:
            level = "strong_candidate"
        elif best_score >= 5 and best_score >= second_score + 2:
            level = "candidate"
        elif strong_evidence and best_score >= 4 and best_score >= second_score + 2:
            level = "candidate"
        else:
            level = "weak"

        suggestions[speaker_id] = {
            "suggested_identity": best_name,
            "suggested_confidence": level,
            "suggested_score": best_score,
            "supporting_clips": support,
            "evidence": reasons[best_name],
        }

    seeded_rows = []
    for row in rows:
        speaker_id = str(row.get("speaker_id") or "").strip()
        suggestion = suggestions.get(speaker_id, {})
        new_row = dict(row)
        new_row["suggested_identity"] = suggestion.get("suggested_identity", "")
        new_row["suggested_confidence"] = suggestion.get("suggested_confidence", "")
        new_row["suggested_score"] = suggestion.get("suggested_score", "")
        new_row["supporting_clips"] = suggestion.get("supporting_clips", "")
        evidence = suggestion.get("evidence") or []
        new_row["suggested_evidence"] = " | ".join(f"{e['reason']}" for e in evidence[:3])
        seeded_rows.append(new_row)

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(seeded_rows, indent=2), encoding="utf-8")
    if args.out_csv:
        write_csv(Path(args.out_csv), seeded_rows)

    summary = {speaker_id: v for speaker_id, v in suggestions.items() if v.get("suggested_confidence") in {"strong_candidate", "candidate"}}
    print(json.dumps(summary, indent=2))
    print(f"Seeded {len(seeded_rows)} review rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

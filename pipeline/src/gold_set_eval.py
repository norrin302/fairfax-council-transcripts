#!/usr/bin/env python3
"""Gold-set evaluation for the transcript pipeline.

Creates a small manually-reviewed benchmark set from meeting excerpts,
then evaluates any pipeline variant against it.

Usage:
  # Create gold set from an existing reviewed transcript
  python -m pipeline.src.gold_set_eval \
    --mode create \
    --meeting-id apr-14-2026 \
    --structured transcripts_structured/apr-14-2026.json \
    --out pipeline/gold-set/apr-14-2026.json

  # Evaluate a pipeline run against the gold set
  python -m pipeline.src.gold_set_eval \
    --mode evaluate \
    --gold-set pipeline/gold-set/apr-14-2026.json \
    --candidate <candidate-segments.json> \
    --report-out pipeline/gold-set/apr-14-2026-eval.json

Gold-set schema:
{
  "meeting_id": "apr-14-2026",
  "created_at": "2026-04-22T...",
  "total_duration_s": 300,
  "excerpts": [
    {
      "excerpt_id": "ex_001",
      "start": 72.0,
      "end": 180.0,
      "description": "Meeting opening, Pledge of Allegiance",
      "turns": [
        {
          "turn_id": "gold_001",
          "start": 72.61,
          "end": 85.83,
          "speaker_name": "Mayor Catherine Read",
          "speaker_role": "mayor",
          "text": "Good evening...",
          "is_final": true,
          "notes": "Confirmed via video frame at 5849s"
        },
        ...
      ]
    }
  ]
}

Evaluation metrics per excerpt:
  - total_turns
  - speaker_match_rate (fraction where speaker_name matches gold)
  - unknown_vs_wrong (did pipeline guess wrong instead of Unknown?)
  - text_word_error_rate (WER on matched turns)
  - attribution_errors (list of turn_ids where speaker was wrong)

Overall:
  - coverage: fraction of meeting duration covered by gold set
  - speaker_match_rate: overall attribution accuracy
  - false_confident: turns wrongly attributed (not Unknown when they should be)
  - miss_rate: turns left Unknown when they should have been identified
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# -------------------------------------------------------------------
# Schema version
# -------------------------------------------------------------------
SCHEMA = "fairfax.gold_set.v1"


# -------------------------------------------------------------------
# Gold-set creation
# -------------------------------------------------------------------
def create_gold_set(
    meeting_id: str,
    structured_path: Path,
    excerpt_specs: list[dict[str, Any]] | None = None,
    out_path: Path | None = None,
) -> dict[str, Any]:
    """Create a gold-set from an existing reviewed structured transcript.

    excerpt_specs: list of {"start": float, "end": float, "description": str}
    If None, uses default hardcoded excerpts.
    """
    structured = json.loads(structured_path.read_text(encoding="utf-8"))
    turns = structured.get("turns", [])

    # Default excerpts for apr-14-2026 (5 representative sections)
    if excerpt_specs is None:
        excerpt_specs = [
            {
                "excerpt_id": "ex_001",
                "start": 72.0,
                "end": 180.0,
                "description": "Meeting opening, Pledge of Allegiance, Library Week proclamation — mixed voices, ceremonial speech",
            },
            {
                "excerpt_id": "ex_002",
                "start": 300.0,
                "end": 420.0,
                "description": "Roll call, public comment signup — sparse council speech, procedural",
            },
            {
                "excerpt_id": "ex_003",
                "start": 1650.0,
                "end": 1850.0,
                "description": "Agenda adoption, consent agenda — council debate, dais discussion",
            },
            {
                "excerpt_id": "ex_004",
                "start": 3700.0,
                "end": 3900.0,
                "description": "Appointments discussion — council back-and-forth, named official identification",
            },
            {
                "excerpt_id": "ex_005",
                "start": 5000.0,
                "end": 5200.0,
                "description": "Public hearings — public commenters at podium, staff response",
            },
        ]

    def in_excerpt(turn_start: float, excerpt: dict) -> bool:
        return excerpt["start"] <= turn_start < excerpt["end"]

    excerpts_out = []
    for spec in excerpt_specs:
        ex_turns = []
        for t in turns:
            t_start = float(t.get("start", 0))
            if in_excerpt(t_start, spec):
                ex_turns.append({
                    "turn_id": f"gold_{spec['excerpt_id']}_{len(ex_turns)+1:03d}",
                    "start": t_start,
                    "end": float(t.get("end", 0)),
                    "speaker_name": str(t.get("speaker_public", "Unknown Speaker")),
                    "speaker_role": str(t.get("speaker_role", "unknown")),
                    "text": str(t.get("text", "")),
                    "is_final": True,  # gold set turns are reviewed/approved
                    "notes": "Derived from reviewed structured transcript",
                })

        if ex_turns:
            total_dur = max(t["end"] for t in ex_turns) - min(t["start"] for t in ex_turns)
            excerpts_out.append({
                "excerpt_id": spec["excerpt_id"],
                "start": spec["start"],
                "end": spec["end"],
                "description": spec["description"],
                "duration_s": round(total_dur, 1),
                "n_turns": len(ex_turns),
                "turns": ex_turns,
            })

    gold_set = {
        "schema": SCHEMA,
        "meeting_id": meeting_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_excerpts": len(excerpts_out),
        "total_duration_s": sum(e["duration_s"] for e in excerpts_out),
        "excerpts": excerpts_out,
    }

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(gold_set, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Gold set written: {out_path}")
        print(f"  {len(excerpts_out)} excerpts, {sum(len(e['turns']) for e in excerpts_out)} total turns")

    return gold_set


# -------------------------------------------------------------------
# Gold-set evaluation
# -------------------------------------------------------------------
@dataclass
class TurnRef:
    start: float
    end: float
    speaker_name: str
    speaker_role: str
    text: str


@dataclass
class CandidateTurn:
    start: float
    end: float
    speaker_id: str
    speaker_name: str
    speaker_role: str
    text: str
    needs_review: bool
    review_reason: str


@dataclass
class EvalResult:
    excerpt_id: str
    n_gold: int
    n_candidate: int
    speaker_match: int
    speaker_wrong: int
    speaker_unknown_when_named: int
    speaker_named_when_unknown: int
    attribution_errors: list[dict] = field(default_factory=list)
    text_wer: float = 0.0


def word_error_rate(ref: str, hyp: str) -> float:
    """Compute Word Error Rate between reference and hypothesis."""
    ref_words = ref.lower().split()
    hyp_words = hyp.lower().split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    # Simple Levenshtein-style edit distance
    m, n = len(ref_words), len(hyp_words)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[m][n] / m


def evaluate_candidate(
    gold_set: dict[str, Any],
    candidate_path: Path,
) -> dict[str, Any]:
    """Evaluate candidate pipeline output against gold set."""
    candidate_data = json.loads(candidate_path.read_text(encoding="utf-8"))

    # Handle both raw merged output and structured transcript formats
    if "segments" in candidate_data:
        cand_turns = candidate_data["segments"]
    elif "turns" in candidate_data:
        cand_turns = candidate_data["turns"]
    else:
        raise SystemExit("Candidate file must have 'segments' or 'turns' key")

    results: list[EvalResult] = []
    total_gold = 0
    total_match = 0
    total_wrong = 0
    total_unknown_when_named = 0
    total_named_when_unknown = 0
    all_errors: list[dict] = []

    for excerpt in gold_set.get("excerpts", []):
        ex_id = excerpt["excerpt_id"]
        gold_turns = excerpt.get("turns", [])

        # Find candidate turns that overlap with this excerpt
        cand_in_excerpt = []
        for t in cand_turns:
            t_start = float(t.get("start_seconds", t.get("start", 0)))
            t_end = float(t.get("end_seconds", t.get("end", 0)))
            if excerpt["start"] <= t_start < excerpt["end"]:
                cand_in_excerpt.append({
                    "start": t_start,
                    "end": t_end,
                    "speaker_name": str(t.get("speaker_name", "Unknown Speaker")),
                    "speaker_role": str(t.get("speaker_role", "unknown")),
                    "text": str(t.get("text", "")),
                    "needs_review": bool(t.get("needs_review", False)),
                    "review_reason": str(t.get("review_reason", "")),
                })

        # Match gold turns to candidate turns by time overlap
        n_gold = len(gold_turns)
        n_cand = len(cand_in_excerpt)
        speaker_match = 0
        speaker_wrong = 0
        unknown_when_named = 0
        named_when_unknown = 0
        errors: list[dict] = []

        for g in gold_turns:
            g_start = float(g.get("start", 0))
            g_end = float(g.get("end", 0))
            g_speaker = str(g.get("speaker_name", ""))
            g_role = str(g.get("speaker_role", ""))
            g_text = str(g.get("text", ""))

            # Find overlapping candidate turn
            overlap = None
            for c in cand_in_excerpt:
                c_start = c["start"]
                c_end = c["end"]
                # Check for overlap
                if c_start < g_end and c_end > g_start:
                    overlap = c
                    break

            if overlap is None:
                # No candidate turn found - counts as Unknown when Named
                if g_role in ("council", "mayor", "staff"):
                    unknown_when_named += 1
                    errors.append({
                        "excerpt_id": ex_id,
                        "turn_id": g.get("turn_id"),
                        "start": g_start,
                        "gold_speaker": g_speaker,
                        "candidate_speaker": "MISSING",
                        "error_type": "missing_candidate",
                    })
                continue

            c_speaker = overlap["speaker_name"]

            # Compare speakers
            if g_speaker == c_speaker:
                speaker_match += 1
            elif c_speaker == "Unknown Speaker":
                # Candidate correctly flagged as unknown
                if g_role in ("council", "mayor", "staff"):
                    unknown_when_named += 1
                    errors.append({
                        "excerpt_id": ex_id,
                        "turn_id": g.get("turn_id"),
                        "start": g_start,
                        "gold_speaker": g_speaker,
                        "candidate_speaker": c_speaker,
                        "error_type": "wrongly_unknown",
                    })
            else:
                # Wrong attribution
                speaker_wrong += 1
                errors.append({
                    "excerpt_id": ex_id,
                    "turn_id": g.get("turn_id"),
                    "start": g_start,
                    "gold_speaker": g_speaker,
                    "candidate_speaker": c_speaker,
                    "error_type": "wrong_attribution",
                })

        # Compute text WER for matched turns
        total_wer = 0
        wer_count = 0
        for g, c in zip(gold_turns, cand_in_excerpt):
            if g.get("speaker_name") == c.get("speaker_name"):
                wer = word_error_rate(g.get("text", ""), c.get("text", ""))
                total_wer += wer
                wer_count += 1
        avg_wer = total_wer / wer_count if wer_count else 0.0

        result = EvalResult(
            excerpt_id=ex_id,
            n_gold=n_gold,
            n_candidate=n_cand,
            speaker_match=speaker_match,
            speaker_wrong=speaker_wrong,
            speaker_unknown_when_named=unknown_when_named,
            speaker_named_when_unknown=named_when_unknown,
            attribution_errors=errors,
            text_wer=round(avg_wer, 4),
        )
        results.append(result)

        total_gold += n_gold
        total_match += speaker_match
        total_wrong += speaker_wrong
        total_unknown_when_named += unknown_when_named
        total_named_when_unknown += named_when_unknown
        all_errors.extend(errors)

    # Compute overall metrics
    overall_match_rate = total_match / total_gold if total_gold else 0
    overall_accuracy = (total_match + total_unknown_when_named) / total_gold if total_gold else 0

    return {
        "gold_set": {
            "meeting_id": gold_set.get("meeting_id"),
            "total_excerpts": gold_set.get("total_excerpts"),
            "total_gold_turns": total_gold,
            "total_duration_s": gold_set.get("total_duration_s"),
        },
        "overall": {
            "speaker_match_rate": round(overall_match_rate, 4),
            "speaker_accuracy": round(overall_accuracy, 4),
            "total_speaker_wrong": total_wrong,
            "total_unknown_when_named": total_unknown_when_named,
            "total_named_when_unknown": total_named_when_unknown,
        },
        "per_excerpt": [
            {
                "excerpt_id": r.excerpt_id,
                "n_gold": r.n_gold,
                "n_candidate": r.n_candidate,
                "speaker_match": r.speaker_match,
                "speaker_wrong": r.speaker_wrong,
                "speaker_match_rate": round(r.speaker_match / r.n_gold if r.n_gold else 0, 4),
                "text_wer": r.text_wer,
                "unknown_when_named": r.speaker_unknown_when_named,
            }
            for r in results
        ],
        "attribution_errors": all_errors[:20],  # cap for readability
    }


# -------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="Gold-set evaluation for transcript pipeline")
    ap.add_argument("--mode", required=True, choices=["create", "evaluate"],
                   help="create: build gold set from reviewed transcript; evaluate: compare candidate to gold set")
    ap.add_argument("--meeting-id", help="Meeting ID (for create mode)")
    ap.add_argument("--structured", type=Path, help="Path to structured transcript JSON (for create mode)")
    ap.add_argument("--out", type=Path, help="Output path for gold set JSON")
    ap.add_argument("--gold-set", type=Path, help="Path to gold set JSON (for evaluate mode)")
    ap.add_argument("--candidate", type=Path, help="Path to candidate pipeline output JSON (for evaluate mode)")
    ap.add_argument("--report-out", type=Path, help="Output path for evaluation report")
    args = ap.parse_args()

    if args.mode == "create":
        if not args.structured or not args.out:
            raise SystemExit("--structured and --out required for create mode")
        gold_set = create_gold_set(
            meeting_id=args.meeting_id or "unknown",
            structured_path=args.structured,
            out_path=args.out,
        )
        print(f"Created gold set: {len(gold_set['excerpts'])} excerpts, "
              f"{sum(e['n_turns'] for e in gold_set['excerpts'])} turns")
        return 0

    elif args.mode == "evaluate":
        if not args.gold_set or not args.candidate:
            raise SystemExit("--gold-set and --candidate required for evaluate mode")
        gold_set = json.loads(args.gold_set.read_text(encoding="utf-8"))
        report = evaluate_candidate(gold_set, args.candidate)
        print(f"\n=== Gold-Set Evaluation Results ===")
        print(f"Gold set: {gold_set['meeting_id']} ({gold_set['total_excerpts']} excerpts, "
              f"{gold_set['total_gold_turns']} turns)")
        print(f"\nOverall:")
        print(f"  Speaker match rate: {report['overall']['speaker_match_rate']:.1%}")
        print(f"  Speaker accuracy:  {report['overall']['speaker_accuracy']:.1%}")
        print(f"  Wrong attributions:  {report['overall']['total_speaker_wrong']}")
        print(f"  Unknown when Named: {report['overall']['total_unknown_when_named']}")
        print(f"\nPer excerpt:")
        for ex in report["per_excerpt"]:
            print(f"  {ex['excerpt_id']}: match={ex['speaker_match_rate']:.1%} "
                  f"wrong={ex['speaker_wrong']} "
                  f"unk_named={ex['unknown_when_named']} "
                  f"wer={ex['text_wer']:.2f}")
        if report["attribution_errors"]:
            print(f"\nSample attribution errors (first 5):")
            for err in report["attribution_errors"][:5]:
                print(f"  [{err['excerpt_id']}] t={err['start']:.0f}s "
                      f"gold={err['gold_speaker']} cand={err['candidate_speaker']} "
                      f"type={err['error_type']}")
        if args.report_out:
            args.report_out.parent.mkdir(parents=True, exist_ok=True)
            args.report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
            print(f"\nReport: {args.report_out}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Post-process a structured transcript JSON to fix common ASR artifacts.

Fixes applied:
  1. Fix broken sentence continuations: "I Am " → "I am " (etc.) when the
     "I Am" appears mid-sentence — a single-word ASR segment that became its own
     turn, then got sentence-capitalized by the pipeline's normalizer.
  2. Absorb orphan single-word "I" / "Oh" / "Um" fragments at the start of a
     meeting into the first labeled turn.
  3. Absorb single-word "I" fragments between consecutive same-speaker turns
     into the next turn (ASR splits "I" from the following verb).

Pipeline integration (add after build_structured_transcript.py):
    python scripts/build_structured_transcript.py ...
    python scripts/fix_transcript.py transcripts_structured/<meeting>.json
    python scripts/publish_structured_meeting.py ...

Usage:
    python3 scripts/fix_transcript.py transcripts_structured/apr-14-2026.json
"""
import json
import sys
from pathlib import Path


TERMINALS = frozenset(".!?")


def _is_continuation(text: str) -> bool:
    """Return True if text looks like a mid-sentence fragment (not a new sentence)."""
    if not text:
        return False
    # Starts with a lowercase word — strong continuation signal
    words = text.split()
    if words and words[0][0].islower():
        return True
    # Starts with "And" / "But" / "So" / "Or" — classic conjunction continuation
    if words and words[0].lower() in frozenset(["and", "but", "so", "or", "nor"]):
        return True
    return False


def fix_transcript(path: str | Path) -> int:
    path = Path(path)
    d = json.load(open(path))
    fixes = 0

    # Pattern 1: Fix "I Am" / "I Think" etc. mid-sentence
    # These appear when ASR splits "I" into its own segment, creating a turn that
    # starts with "I" (capital I) followed by a capitalized word — pipeline then
    # sentence-capitalizes the whole turn, producing "I Am now going..." when
    # the intended text is "I am now going..."
    CAPITALS = ["Am", "Think", "Want", "Know", "See", "Hope", "Believe",
               "Feel", "Guess", "Assume", "Remember", "Understand", "Recalled"]
    for t in d["turns"]:
        for cap in CAPITALS:
            needle = f"I {cap} "
            if needle in t["text"]:
                before = t["text"].split(needle)[0].strip()
                # If there's nothing before the "I {Cap}" or the before text
                # doesn't end with terminal punctuation, this is mid-sentence
                if not before or (before[-1] not in TERMINALS and not before.endswith('"')):
                    t["text"] = t["text"].replace(needle, f"I {cap.lower()} ", 1)
                    fixes += 1
                    print(f"  [{t['start']:.2f}s] 'I {cap}' → 'I {cap.lower()}': {t['text'][:70]!r}")

    # Pattern 2 & 3: Absorb single-word fragments
    i = 0
    while i < len(d["turns"]) - 1:
        t = d["turns"][i]
        next_t = d["turns"][i + 1]
        gap = next_t["start"] - t["end"]
        fragment_words = frozenset(["I", "Oh", "Um", "Uh", "Ah", "Er"])
        is_short_fragment = len(t["text"].strip()) <= 3 and t["text"].strip() in fragment_words

        if not is_short_fragment:
            i += 1
            continue

        # Same speaker continuation: absorb "I" fragments into next turn
        if (t["text"].strip() == "I"
                and t["speaker_public"] == next_t["speaker_public"]
                and gap < 10
                and len(next_t["text"]) > 5):
            next_t["text"] = "I " + next_t["text"]
            next_t["start"] = t["start"]
            t["text"] = ""
            fixes += 1
            print(f"  [{t['start']:.2f}s] Absorbed 'I' into {next_t['speaker_public']} at {next_t['start']:.2f}s")
            i += 1
            continue

        # Orphan fragment at meeting start (first 2 turns, unknown speaker,
        # adjacent to first labeled speaker) → absorb into next labeled turn
        if (is_short_fragment
                and i < 2
                and t["speaker_public"] == "Unknown Speaker"
                and next_t["speaker_public"] != "Unknown Speaker"
                and gap < 15):
            next_t["text"] = t["text"].strip() + " " + next_t["text"]
            next_t["start"] = t["start"]
            t["text"] = ""
            fixes += 1
            print(f"  [{t['start']:.2f}s] Absorbed orphan {t['text'].strip()!r} into {next_t['speaker_public']} at {next_t['start']:.2f}s")

        i += 1

    # Remove now-empty turns
    d["turns"] = [t for t in d["turns"] if t["text"] != ""]

    # Pattern 4: Merge clear sentence-fragment splits (same speaker, small gap,
    # prev ends mid-sentence, next looks like continuation) — supplemental to the
    # pipeline's built-in sentence fragment repair
    i = 0
    while i < len(d["turns"]) - 1:
        curr = d["turns"][i]
        nxt = d["turns"][i + 1]
        gap = float(nxt["start"]) - float(curr["end"])
        if (i == 0
                or curr["speaker_public"] != nxt["speaker_public"]
                or gap >= 3.0
                or curr["text"].strip()[-1:] in TERMINALS):
            i += 1
            continue
        if _is_continuation(nxt["text"]) and len(nxt["text"]) < 120:
            curr["text"] = (curr["text"].strip() + " " + nxt["text"].strip())
            curr["end"] = nxt["end"]
            nxt["text"] = ""
            fixes += 1
            print(f"  [{curr['start']:.2f}s] Merged sentence fragment: {curr['text'][:60]!r} + {nxt['text'][:40]!r}")
            i += 1
            continue
        i += 1

    # Remove empty turns again after fragment merge
    d["turns"] = [t for t in d["turns"] if t["text"] != ""]

    json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)
    print(f"\nTotal fixes applied: {fixes}")
    return fixes


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 fix_transcript.py transcripts_structured/<meeting>.json")
        sys.exit(1)
    fix_transcript(sys.argv[1])

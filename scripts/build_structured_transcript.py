#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.publish_meeting import load_meeting  # type: ignore


@dataclass
class DiarSeg:
    start: float
    end: float
    speaker: str


def _load_diar(path: Path) -> list[DiarSeg]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    segs = obj.get("segments") if isinstance(obj, dict) else None
    if not isinstance(segs, list):
        raise SystemExit(f"Diarization JSON missing segments[]: {path}")
    out: list[DiarSeg] = []
    for seg in segs:
        try:
            start = float(seg.get("start"))
            end = float(seg.get("end"))
            speaker = str(seg.get("speaker") or "").strip()
        except Exception:
            continue
        if not speaker or end <= start:
            continue
        out.append(DiarSeg(start=start, end=end, speaker=speaker))
    out.sort(key=lambda s: (s.start, s.end, s.speaker))
    return out


def _speaker_at(t: float, segs: list[DiarSeg], state: dict[str, Any]) -> str:
    idx = int(state.get("idx", 0))
    active: list[DiarSeg] = state.get("active", [])
    active = [s for s in active if s.end > t]
    while idx < len(segs) and segs[idx].start <= t:
        if segs[idx].end > t:
            active.append(segs[idx])
        idx += 1
    state["idx"] = idx
    state["active"] = active
    if not active:
        return "UNKNOWN"
    best = max(active, key=lambda s: (s.end - s.start))
    return best.speaker


def _load_asr_units(asr_path: Path) -> list[dict[str, Any]]:
    obj = json.loads(asr_path.read_text(encoding="utf-8"))

    words = obj.get("word_segments") or obj.get("words") or []
    if isinstance(words, list) and words:
        out: list[dict[str, Any]] = []
        for w in words:
            try:
                start = float(w.get("start"))
                end = float(w.get("end"))
                word = str(w.get("word") or "").strip()
            except Exception:
                continue
            if not word:
                continue
            out.append({"start": start, "end": end, "text": word, "unit": "word"})
        if out:
            return out

    segments = obj.get("segments") or []
    if isinstance(segments, list) and segments:
        out = []
        for seg in segments:
            try:
                start = float(seg.get("start"))
                end = float(seg.get("end"))
                text = str(seg.get("text") or "").strip()
            except Exception:
                continue
            if not text or end <= start:
                continue
            out.append({"start": start, "end": end, "text": text, "unit": "segment"})
        if out:
            return out

    raise SystemExit(f"ASR JSON missing word_segments[]/words[]/segments[]: {asr_path}")


def _join_tokens(parts: list[str]) -> str:
    out = ""
    for w in parts:
        if not w:
            continue
        if not out:
            out = w
        elif w.startswith("'"):
            out += w
        elif w in {".", ",", "!", "?", ":", ";"} or w.startswith(".") or w.startswith(","):
            out += w
        else:
            out += " " + w
    return re.sub(r"\s+", " ", out).strip()


def _normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if text:
        return text[:1].upper() + text[1:]
    return text


def _load_approvals(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        return {}
    if isinstance(obj.get("approvals"), dict):
        return obj["approvals"]
    return obj


# ---------------------------------------------------------------------------
# Granicus caption parsing — speaker hints from WebVTT captions
# ---------------------------------------------------------------------------

def _parse_vtt_timestamp(ts: str) -> float:
    """Parse WebVTT timestamp HH:MM:SS.mmm → seconds."""
    h, m, rest = ts.split(":")
    s, ms = rest.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def _fetch_granicus_captions_vtt(source_video_url: str) -> str:
    """Fetch Granicus WebVTT captions from public endpoint (no API key needed)."""
    m = re.search(r"/clip/(\d+)", source_video_url or "")
    if not m:
        raise RuntimeError(f"Could not extract clip id from source_video_url: {source_video_url}")
    clip_id = m.group(1)
    url = f"https://fairfax.granicus.com/videos/{clip_id}/captions.vtt"
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _load_caption_hints(vtt_text: str) -> list[dict[str, Any]]:
    """Parse WebVTT into caption segments with speaker_hint and strength.

    Returns list of {start, end, speaker_hint, speaker_hint_strength, text}.
    Uses the same parsing logic as publish_meeting.py segments_from_webvtt().
    """
    lines = [ln.rstrip("\n") for ln in (vtt_text or "").splitlines()]
    segs: list[dict[str, Any]] = []
    i = 0

    def normalize_ws(s: str) -> str:
        return re.sub(r"\s+", " ", s or "").strip()

    def titleize_name(raw: str) -> str:
        parts = re.split(r"([\-'])", raw.strip())
        out = []
        for p in parts:
            if p in {"-", "'"}:
                out.append(p)
            else:
                out.append(p[:1].upper() + p[1:].lower() if p else "")
        return "".join(out)

    def norm_for_hint(s: str) -> str:
        s = (s or "").strip().lower()
        s = re.sub(r"[^a-z\-\'\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    roster_last_to_full = {
        "amos": "Anthony Amos",
        "bates": "Billy Bates",
        "hall": "Stacy Hall",
        "hardy-chandler": "Stacy Hardy-Chandler",
        "mcquillen": "Rachel McQuillen",
        "peterson": "Tom Peterson",
    }
    roster_keys = list(roster_last_to_full.keys())

    def canon_last(raw_last: str) -> str:
        raw_last = (raw_last or "").strip().lower()
        raw_last = re.sub(r"[^a-z\-']", "", raw_last)
        if not raw_last:
            return ""
        if raw_last in roster_last_to_full:
            return raw_last
        import difflib
        best = None
        best_ratio = 0.0
        second_ratio = 0.0
        for k in roster_keys:
            r = difflib.SequenceMatcher(a=raw_last, b=k).ratio()
            if r > best_ratio:
                second_ratio = best_ratio
                best_ratio = r
                best = k
            elif r > second_ratio:
                second_ratio = r
        if best and (best_ratio >= 0.66 or (best_ratio >= 0.58 and (best_ratio - second_ratio) >= 0.12)):
            return best
        first = raw_last[:1]
        if first:
            candidates = [k for k in roster_keys if k.startswith(first)]
            if len(candidates) == 1:
                return candidates[0]
        return ""

    def parse_speaker_hint(line: str) -> str:
        low = norm_for_hint(line)
        m = re.match(r"^(council\s*member|councilmember|councilman|councilwoman)\s+([a-z][a-z\-']+)", low)
        if m:
            last = canon_last(m.group(2))
            if not last:
                return ""
            full = roster_last_to_full.get(last)
            if full:
                return f"Councilmember {full}"
            return f"Councilmember {titleize_name(last)}"
        m = re.match(r"^(mayor)\s+([a-z][a-z\-']+)", low)
        if m:
            token = re.sub(r"[^a-z\-']", "", m.group(2) or "").strip().lower()
            import difflib
            if difflib.SequenceMatcher(a=token, b="read").ratio() >= 0.7:
                return "Mayor Catherine Read"
            return ""
        m = re.match(r"^(city\s+manager)\s+([a-z][a-z\-']+)", low)
        if m:
            token = re.sub(r"[^a-z\-']", "", m.group(2) or "").strip().lower()
            import difflib
            if difflib.SequenceMatcher(a=token, b="coll").ratio() >= 0.7:
                return "City Manager David Coll"
            return ""
        return ""

    def split_inline_speaker_header(line: str) -> tuple[str, str, str]:
        """Detect inline speaker header at start of cue. Returns (hint, remainder, strength)."""
        l = (line or "").strip()
        low = norm_for_hint(l)
        m = re.match(r"^(council\s*member|councilmember|councilman|councilwoman)\s+([a-z][a-z\-']+)\.\s*(.*)", low)
        if m:
            last = canon_last(m.group(2))
            if last:
                full = roster_last_to_full.get(last)
                hint = f"Councilmember {full}" if full else f"Councilmember {titleize_name(last)}"
                rem = m.group(3).strip()
                return hint, rem, "inline"
        m = re.match(r"^(mayor)\s+([a-z][a-z\-']+)\.\s*(.*)", low)
        if m:
            token = re.sub(r"[^a-z\-']", "", m.group(2) or "").strip().lower()
            import difflib
            if difflib.SequenceMatcher(a=token, b="read").ratio() >= 0.7:
                hint = "Mayor Catherine Read"
                rem = m.group(3).strip()
                return hint, rem, "inline"
        return "", "", ""

    def looks_like_label_only(line: str) -> bool:
        """Heuristic: single short line that looks like a name/title, not speech."""
        line = (line or "").strip()
        if not line:
            return False
        words = line.split()
        if len(words) > 4:
            return False
        if re.match(r"^(council\s*member|councilmember|councilman|councilwoman|mayor|city\s*manager)\s+[a-z]", line, re.I):
            return True
        if re.match(r"^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$", line):
            return True
        return False

    while i < len(lines):
        line = lines[i].lstrip("\ufeff").strip()
        if not line:
            i += 1
            continue
        if line.upper().startswith("WEBVTT"):
            i += 1
            continue
        if (i + 1) < len(lines) and ("-->" in lines[i + 1]):
            i += 1
            line = lines[i].strip()
        if "-->" not in line:
            i += 1
            continue
        m_ts = re.match(r"(\d\d:\d\d:\d\d\.\d\d\d)\s*-->\s*(\d\d:\d\d:\d\d\.\d\d\d)", line)
        if not m_ts:
            i += 1
            continue
        start = _parse_vtt_timestamp(m_ts.group(1))
        end = _parse_vtt_timestamp(m_ts.group(2))
        i += 1
        buf_lines: list[str] = []
        new_speaker = False
        speaker_hint = ""
        speaker_hint_strength = ""
        while i < len(lines) and lines[i].strip() != "":
            ln = lines[i].strip()
            if ln.startswith(">>"):
                new_speaker = True
                ln = ln[2:].lstrip()
                if not speaker_hint:
                    speaker_hint = parse_speaker_hint(ln)
                    if speaker_hint:
                        speaker_hint_strength = "explicit"
            if not speaker_hint and not buf_lines:
                ihint, remainder, istrength = split_inline_speaker_header(ln)
                if ihint:
                    if not remainder:
                        j = i + 1
                        nxt = ""
                        while j < len(lines) and lines[j].strip() != "":
                            nxt = lines[j].strip()
                            if nxt:
                                break
                            j += 1
                        if nxt and looks_like_label_only(nxt):
                            ihint = ""
                    if ihint:
                        speaker_hint = ihint
                        speaker_hint_strength = istrength or "inline"
                        new_speaker = True
                        ln = remainder
            buf_lines.append(ln)
            i += 1
        if not speaker_hint and buf_lines:
            first = str(buf_lines[0] or "").strip()
            mh = re.match(r"^(council\s*member|mayor|city\s*manager)\s+([a-z][a-z\-\']+)\.?$", norm_for_hint(first))
            if mh:
                speaker_hint = parse_speaker_hint(first)
                if speaker_hint:
                    buf_lines = buf_lines[1:]
                    speaker_hint_strength = "marker"
                    new_speaker = True
        text = normalize_ws(" ".join(buf_lines))
        if re.search(r"aberdeen\s+captioning|www\.|\b\d{3}-\d{3}-\d{4}\b", text, flags=re.I):
            i += 1
            continue
        if speaker_hint and speaker_hint_strength in {"explicit", "inline", "marker"}:
            segs.append({
                "start": start, "end": end,
                "speaker_hint": speaker_hint,
                "speaker_hint_strength": speaker_hint_strength,
                "text": text,
            })
        i += 1

    return segs


def _caption_speaker_at(t: float, caption_segs: list[dict[str, Any]]) -> tuple[str, str]:
    """Return (speaker_hint, strength) for time t using caption hints.

    Uses the most recent caption speaker hint that is active at time t.
    Captions are continuous within a speaker's turn, so if a hint is set at time T0
    and t > T0 with no intervening NEW speaker marker, the hint carries forward.
    """
    if not caption_segs:
        return "", ""

    # Build ordered list of caption segments with hints
    # For each segment, determine if it STARTS a new speaker (has explicit hint)
    hint_segs: list[tuple[float, float, str, str]] = []  # (start, end, hint, strength)
    current_hint = ""
    current_strength = ""
    for seg in caption_segs:
        hint = str(seg.get("speaker_hint") or "").strip()
        strength = str(seg.get("speaker_hint_strength") or "").strip()
        s = float(seg["start"])
        e = float(seg["end"])
        if hint and strength in {"explicit", "inline", "marker"}:
            current_hint = hint
            current_strength = strength
        if current_hint:
            hint_segs.append((s, e, current_hint, current_strength))

    if not hint_segs:
        return "", ""

    # Find the active hint at time t: the last segment where start <= t
    # The speaker at t is the hint from the most recent segment STARTING at or before t
    # that hasn't been overridden by a new speaker.
    best: tuple[str, str] = ("", "")
    for s, e, hint, strength in hint_segs:
        if s <= t:
            best = (hint, strength)
        else:
            # Segments are ordered by start time, first miss means no more applicable segs
            break
    return best


# ---------------------------------------------------------------------------
# Text-based heuristic speaker identification (from transcribe.py)
# ---------------------------------------------------------------------------

COUNCIL_MEMBERS = {
    "Stacy Hall": {"role": "City Council Member", "title": "Councilwoman"},
    "Catherine Read": {"role": "Mayor", "title": "Mayor"},
    "Anthony Amos": {"role": "City Council Member", "title": "Councilman"},
    "Billy Bates": {"role": "City Council Member", "title": "Councilman"},
    "Stacy Hardy-Chandler": {"role": "City Council Member", "title": "Councilwoman"},
    "Rachel McQuillen": {"role": "City Council Member", "title": "Councilwoman"},
    "Tom Peterson": {"role": "City Council Member", "title": "Councilman"},
    "David Coll": {"role": "City Manager", "title": "City Manager"},
}


def _labeled_name(base_name: str) -> str:
    """Return full labeled name with title prefix (e.g. 'Mayor Catherine Read')."""
    info = COUNCIL_MEMBERS.get(base_name, {})
    title = info.get("title", "")
    if title in ("Mayor", "City Manager"):
        return f"{title} {base_name}"
    return base_name


def _identify_speaker_from_text(text: str, prev_speaker: str | None = None) -> str | None:
    """Attempt to identify speaker from transcript text content using heuristics.

    Returns the identified name or None if no confident identification possible.
    Used as a fallback when pyannote speaker labels are not in the approvals registry.
    """
    text_lower = text.lower()

    # Check for explicit speaker identification (name mentioned in speech)
    for name, info in COUNCIL_MEMBERS.items():
        if name.lower() in text_lower:
            title = info.get("title", "")
            if title == "Mayor":
                return f"Mayor {name}"
            if title == "City Manager":
                return f"City Manager {name}"
            return name

    # Role-based patterns
    if any(term in text_lower for term in ["as mayor", "this is your mayor", "i'm the mayor", "i am mayor"]):
        return "Mayor Catherine Read"
    if "city manager" in text_lower and "david coll" in text_lower:
        return "City Manager David Coll"

    # Pattern: councilmember [Name] (council members saying their own names during roll call)
    cm_match = re.search(r"council\s*(?:member|woman|man)\s+([a-z][a-z\-']+)", text_lower)
    if cm_match:
        first_name = cm_match.group(1).capitalize()
        for name in COUNCIL_MEMBERS:
            if name.startswith(first_name):
                return name

    # Pattern: "Thank you, [FirstName]" often indicates the next speaker
    thanks_match = re.search(r"thank you[,\s]+([A-Z][a-z]+)", text)
    if thanks_match:
        first_name = thanks_match.group(1).capitalize()
        for name in COUNCIL_MEMBERS:
            if name.startswith(first_name):
                return name

    # Library board representative heuristic: "your representative to the Fairfax County
    # Public Library Board [of Trustees]" — Suzanne Levy is the chair/rep for the library proclamation.
    if "your representative to the fairfax county public library board" in text_lower:
        return "Suzanne Levy"

    # MAYOR OPENING PATTERN: detect meeting opening without needing prior context
    # The mayor typically opens with "call the meeting to order", "pledge", "ask [staff] to..."
    mayor_opening_phrases = [
        "call the", "regular meeting", "to order", "pledge of allegiance",
        "ask suzanne levy", "ask eric carlson", "ask alana",
        "i pledge", "will now ask", "please rise",
    ]
    if any(phrase in text_lower for phrase in mayor_opening_phrases):
        # High confidence mayor indicator
        return "Mayor Catherine Read"

    # Carry over previous speaker for continuation phrases.
    # prev_speaker may be the full labeled name ("Mayor Catherine Read") or base name.
    # Normalize to base name for COUNCIL_MEMBERS lookup.
    def _base_name(labeled: str) -> str:
        for key in COUNCIL_MEMBERS:
            if labeled == key or labeled == _labeled_name(key):
                return key
        return labeled

    base = _base_name(prev_speaker or "")
    if base in COUNCIL_MEMBERS:
        if base == "Catherine Read":
            short_text = text_lower[:100]
            continuation_phrases = [
                "i ", "we ", "the ", "this ", "our ", "to the",
                "pledge", "allegiance", "ask ", "please ", "will now",
            ]
            if any(phrase in short_text for phrase in continuation_phrases):
                return _labeled_name(base)

    return None


# ---------------------------------------------------------------------------
# Label policy
# ---------------------------------------------------------------------------

def _public_label_policy(
    speaker_raw: str,
    approvals: dict[str, dict[str, Any]],
    caption_segs: list[dict[str, Any]] | None = None,
    turn_mid: float = 0.0,
    text_hint: str = "",
    prev_speaker: str | None = None,
) -> tuple[str, str, bool, str]:
    """Resolve public speaker label from diarization speaker + approvals + caption hints + text heuristics.

    Priority:
    1. Approved named official from approvals registry
    2. Granicus caption hint (for segments with caption speaker markers)
    3. Text-based heuristic identification (for explicit name/role mentions)
    4. "Unknown Speaker" with appropriate reason
    """
    a = approvals.get(speaker_raw) or {}
    status = str(a.get("status") or "").strip()
    name = str(a.get("name") or "").strip()

    if status == "approved" and name:
        return name, "approved", False, ""

    if status.startswith("rejected") or status == "mixed":
        return "Unknown Speaker", "mixed", True, "mixed_or_rejected_audio"

    # Try Granicus caption hint as fallback
    if caption_segs:
        hint, strength = _caption_speaker_at(turn_mid, caption_segs)
        if hint and strength in {"explicit", "inline", "marker"}:
            src = "caption" if speaker_raw == "UNKNOWN" else "caption_override"
            return hint, src, False, f"caption:{strength}"

    # Try text-based heuristic identification (for UNKNOWN, unresolved, or any case without approved name)
    if text_hint:
        identified = _identify_speaker_from_text(text_hint, prev_speaker)
        if identified:
            return identified, "heuristic", False, "text_heuristic"

    if speaker_raw == "UNKNOWN":
        return "Unknown Speaker", "unknown", True, "no_diarization"

    return "Unknown Speaker", "unresolved", True, "unresolved_identity"


# ---------------------------------------------------------------------------
# Name-call handoff heuristic
# ---------------------------------------------------------------------------
# When a speaker explicitly names the next speaker ("turn it over to [Name]"),
# and the immediately following turn thanks that person (e.g. "thank you, Jen"),
# override the next turn's label to the named speaker. This corrects pyannote
# mis-attributions when the next speaker actually self-identifies in their response.

_HANDOVER_PAT = re.compile(
    r"(?:turn\s+it\s+over\s+to\s+(?:(?:miss|mr|mrs|ms|dr)\s+)?|hand\s+(?:it\s+)?over\s+to\s+(?:(?:miss|mr|mrs|ms|dr)\s+)?|pass\s+(?:it\s+)?to\s+(?:(?:miss|mr|mrs|ms|dr)\s+)?|=>>\s*)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    re.IGNORECASE,
)
_THANKYOU_PAT = re.compile(
    r"(?:thank\s+you[.,!?\s]*|thanks[.,!?\s]*)([A-Z][a-z]+)",
    re.IGNORECASE,
)


def _apply_name_call_handoffs(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Override speaker labels for name-call handoff turns.

    Scans for patterns like:
      "... turn it over to Stephanie"  +  "Thank you, Jen"  =>  next turn = Stephanie

    The named person is used verbatim as the label (no title prefix needed;
    _labeled_name() is a separate pass in publish_meeting.py for approved officials).
    """
    CHASING_MAX_GAP = 5.0  # seconds; handoff must be within this window
    result = [t.copy() for t in turns]
    overrides = 0

    for i, t in enumerate(result):
        m = _HANDOVER_PAT.search(t.get("text", "") or "")
        if not m:
            continue
        named = m.group(1).strip()  # e.g. "Stephanie"
        # Skip role titles (e.g. "our Assistant City Manager", "the City Manager")
        role_prefixes = ("our ", "the ", "your ", "this ", "my ", "city ", "assistant ", "assistant city ",
                         "city manager", "mayor ", "councilmember ", "council member", "mr. ", "ms. ",
                         "mrs. ", "dr. ", "hon. ")
        if named.lower().startswith(role_prefixes):
            continue
        # Look at the very next turn
        if i + 1 >= len(result):
            continue
        nxt = result[i + 1]
        gap = float(nxt["start"]) - float(t["end"])
        if gap > CHASING_MAX_GAP:
            continue
        # Does the next turn thank the handing-off speaker?
        # Walk backwards through prev turns to find who just spoke
        prev_texts: list[str] = []
        for j in range(i - 1, max(i - 3, -1), -1):
            sp = result[j].get("speaker_public", "")
            if sp and sp != "Unknown Speaker":
                prev_texts.append(sp)
                break
        prev_name = prev_texts[0] if prev_texts else ""
        # Check if next turn thanks prev_name (using first name or known nickname)
        nicknames = {
            "janet": "jen",
            "mary": "mary",
            "fasa": "fasa",
            "fasal": "fasal",
            "stacy": "stacy",
            "tom": "tom",
            "pete": "pete",
            "rachel": "rachel",
            "anthony": "anthony",
            "douglas": "doug",
            "doug": "doug",
            "alexander": "alex",
            "alex": "alex",
            "kevin": "kevin",
            "jc": "jc",
        }
        prev_parts = prev_name.lower().split()
        prev_last = prev_parts[-1] if prev_parts else ""
        expected_nick = nicknames.get(prev_last, prev_last)
        thank_you_m = _THANKYOU_PAT.search(nxt.get("text", "") or "")
        if thank_you_m:
            thanked = thank_you_m.group(1).lower()
            if thanked == expected_nick or thanked == prev_last:
                # Confident: next speaker is the named person
                result[i + 1] = nxt.copy()
                result[i + 1]["speaker_public"] = named
                result[i + 1]["speaker_status"] = "heuristic"
                result[i + 1]["review_reason"] = "name_call_handoff"
                result[i + 1]["handoff_applied"] = True  # store as actual bool for merge logic
                overrides += 1
                continue

        # Fallback: if no thank-you match but we have strong named handoff + response from next turn,
        # treat it as a handoff regardless of response length. A named person responding to being
        # called on will speak at length — that's not an ASR artifact. The explicit "turn it over to [Name]"
        # + immediate response (gap<3s) + different speaker is sufficient signal.
        if gap < 3.0:
            result[i + 1] = nxt.copy()
            result[i + 1]["speaker_public"] = named
            result[i + 1]["speaker_status"] = "heuristic"
            result[i + 1]["review_reason"] = "name_call_handoff"
            result[i + 1]["handoff_applied"] = True
            overrides += 1

    if overrides:
        print(f"Name-call handoffs applied: {overrides}")
    return result


# ---------------------------------------------------------------------------
# Self-introduction heuristic
# ---------------------------------------------------------------------------
_AUXILIARY_AFTER_I = frozenset({
    "going", "to", "be", "get", "have", "do", "will", "would", "could",
    "should", "need", "want", "know", "think", "see", "say", "tell",
    "ask", "help", "make", "let", "just", "also", "really", "not",
    "never", "always", "ever", "still", "yet", "now", "here",
    "trying", "planning", "glad", "sorry",
})


def _extract_self_intro_name(text: str) -> str | None:
    """Extract a self-introduction name from text using simple string matching.

    Handles three reliable patterns:
      "My name is [Name]"
      "I am [Name]"   (but NOT "I am going" / "I am here" etc.)
      "This is [Name]" (but NOT "This is the" / "This is a" etc.)
    """
    t = text.strip()

    def _collect_name(words: list[str]) -> str | None:
        name_words = []
        for w in words[:3]:
            w_clean = w.strip(".,!?;:'")
            # Skip single-letter words (likely pronouns like "I" or "A")
            if w_clean and len(w_clean) >= 2 and w_clean[0].isupper() and w_clean.isalpha():
                name_words.append(w_clean)
            else:
                break
        return " ".join(name_words) if name_words else None

    # "My name is [Name]"
    for p in ("my name is ", "My name is ", "MY NAME IS "):
        idx = t.lower().find(p.lower())
        if idx >= 0:
            after = t[idx + len(p):].strip()
            result = _collect_name(after.split())
            if result:
                return result

    # "I am [Name]" — skip if the word after "am" is a known auxiliary
    for p, plen in (("i am ", 5), ("I am ", 5), ("i'm ", 4), ("I'm ", 4)):
        idx = t.lower().find(p.lower())
        if idx >= 0:
            after = t[idx + plen:].strip()
            words = after.split()
            if words and words[0].lower() not in _AUXILIARY_AFTER_I:
                result = _collect_name(words)
                if result:
                    return result

    # "This is [Name]" — skip common non-name patterns
    for p, plen in (("this is ", 8), ("This is ", 8)):
        idx = t.lower().find(p.lower())
        if idx >= 0:
            after = t[idx + plen:].strip()
            words = after.split()
            if words and words[0].lower() not in frozenset({"the", "a", "an", "this", "that", "it", "what", "such"}):
                result = _collect_name(words)
                if result:
                    return result

    return None
def _apply_self_introductions(
    turns: list[dict[str, Any]],
    approvals: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Override labels when a turn contains an explicit self-introduction that conflicts.

    If the speaker says "My name is Anita Light" but our approved label says "Rachel McQuillen",
    we use the self-introduced name. The person knows their own name better than pyannote.
    """
    result = [t.copy() for t in turns]
    overrides = 0

    for i, t in enumerate(result):
        intro_name = _extract_self_intro_name(t.get("text", "") or "")
        if not intro_name:
            continue

        current_label = t.get("speaker_public", "")
        if current_label == intro_name:
            continue  # already correct

        # Check if the intro name is a known approved person under a different label
        # If so, override with the self-introduced name
        result[i] = t.copy()
        result[i]["speaker_public"] = intro_name
        result[i]["speaker_status"] = "heuristic"
        result[i]["review_reason"] = "self_introduction"
        result[i]["self_intro_applied"] = True
        overrides += 1

    if overrides:
        print(f"Self-introduction overrides applied: {overrides}")
    return result


# ---------------------------------------------------------------------------
# Sentence-fragment repair heuristic
# ---------------------------------------------------------------------------
# When a labeled speaker's turn ends mid-sentence (no terminal punctuation)
# and the very next turn starts with a lowercase/continuation word AND the gap
# is small, it's likely an ASR artifact or a false speaker boundary.
# Merge them back together.

_CONTINUATION_STARTS = frozenset({
    "and", "but", "so", "or", "the", "a", "an",
    "it", "they", "we", "you", "i", "this", "that",
    "to", "of", "in", "for", "on", "with", "at",
    "is", "are", "was", "were", "have", "has", "had",
    "be", "been", "being", "do", "does", "did",
    "will", "would", "could", "should", "can",
    "my", "your", "our", "their", "his", "her",
})
_TERMINAL_END = frozenset(".!?\"")
_FRAGMENT_MAX_GAP = 3.0  # seconds
_FRAGMENT_MAX_CHARS = 600  # only repair reasonably-sized turns


def _apply_sentence_fragment_repair(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge turns that appear to be a single sentence split by a false speaker boundary.

    Detects:
      - prev turn ends mid-sentence (no terminal punctuation)
      - next turn starts with a common continuation word (lowercase article/pronoun/conjunction)
      - gap between them is small (< 3s)
      - prev turn is reasonably sized (not an artifact)
    """
    result = [t.copy() for t in turns]
    repairs = 0
    i = 0
    while i < len(result) - 1:
        curr = result[i]
        nxt = result[i + 1]

        speaker = curr.get("speaker_public", "")
        next_speaker = nxt.get("speaker_public", "")
        if not speaker or speaker == "Unknown Speaker":
            i += 1
            continue

        gap = float(nxt["start"]) - float(curr["end"])
        if gap > _FRAGMENT_MAX_GAP:
            i += 1
            continue

        curr_text = (curr.get("text") or "").strip()
        next_text = (nxt.get("text") or "").strip()

        # Only repair if prev turn is reasonably sized (not a fragment itself)
        if len(curr_text) > _FRAGMENT_MAX_CHARS or len(curr_text) < 5:
            i += 1
            continue

        # Check if prev ends mid-sentence (no terminal punctuation)
        ends_terminal = curr_text[-1:] in _TERMINAL_END

        # Check if next starts with a continuation pattern.
        # Only match if the word is genuinely lowercase (not capitalized at sentence start).
        # "Will" (capital-W) at the beginning of a sentence is NOT a continuation signal.
        next_words = next_text.split()
        first_word = next_words[0] if next_words else ""
        starts_continuation = (
            next_words
            and first_word.islower()
            and first_word in _CONTINUATION_STARTS
        )

        # Also merge if next is very short and starts capitalized (another fragment)
        next_capital_word = next_words[0] if next_words else ""
        is_short_capital = (
            len(next_text) < 80
            and next_capital_word
            and next_capital_word[0].isupper()
            and next_capital_word.lower() not in {"i", "i'm", "i'll", "i've", "a", "an", "the"}
        )

        if (not ends_terminal and starts_continuation) or (not ends_terminal and is_short_capital):
            # Merge: extend prev turn to include next turn
            result[i] = curr.copy()
            result[i]["end"] = nxt["end"]
            result[i]["text"] = curr_text + " " + next_text
            del result[i + 1]  # remove the next turn
            repairs += 1
            # Don't advance i — check the new i against its next neighbor
            continue

        i += 1

    if repairs:
        print(f"Sentence-fragment repairs applied: {repairs}")
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build structured transcript turns (Phase 1) from ASR + diarization. "
                    "Optionally uses Granicus caption speaker hints as fallback for undiarized segments."
    )
    ap.add_argument("meeting_id")
    ap.add_argument("--asr", required=True, help="ASR JSON with word_segments[]/words[] or segments[]")
    ap.add_argument("--diarization", required=True, help="Diarization JSON with segments[]")
    ap.add_argument("--approvals", default="", help="Optional manual approvals JSON")
    ap.add_argument("--captions-vtt", default="",
                    help="Path or URL to WebVTT captions. If a Granicus source_video_url is available "
                         "in meeting metadata and this starts with 'fetch:', the captions will be "
                         "retrieved from Granicus automatically.")
    ap.add_argument("--out", required=True, help="Output structured transcript JSON")
    ap.add_argument("--max-gap", type=float, default=1.2)
    ap.add_argument("--max-seconds", type=float, default=35.0)
    ap.add_argument("--max-chars", type=int, default=650)
    args = ap.parse_args()

    meeting = load_meeting(args.meeting_id)
    asr_units = _load_asr_units(Path(args.asr))
    diar = _load_diar(Path(args.diarization))
    approvals = _load_approvals(Path(args.approvals)) if args.approvals else {}

    # Load caption hints
    caption_segs: list[dict[str, Any]] = []
    captions_vtt = (args.captions_vtt or "").strip()
    if captions_vtt:
        if captions_vtt.startswith("fetch:"):
            # Auto-fetch from Granicus using meeting source_video_url
            source_url = str(meeting.get("source_video_url") or meeting.get("source_url") or "")
            if not source_url:
                print("WARNING: --captions-vtt=fetch: but no source_video_url in meeting metadata; skipping captions")
            else:
                print(f"Fetching Granicus captions from: {source_url}")
                vtt_text = _fetch_granicus_captions_vtt(source_url)
                caption_segs = _load_caption_hints(vtt_text)
                print(f"  Caption segments with speaker hints: {len(caption_segs)}")
        elif captions_vtt.startswith("http://") or captions_vtt.startswith("https://"):
            # Fetch from URL
            with urllib.request.urlopen(captions_vtt, timeout=60) as resp:
                vtt_text = resp.read().decode("utf-8", errors="ignore")
            caption_segs = _load_caption_hints(vtt_text)
            print(f"Loaded {len(caption_segs)} caption segments from URL")
        else:
            # Local file
            vtt_path = Path(captions_vtt)
            if vtt_path.exists():
                vtt_text = vtt_path.read_text(encoding="utf-8")
                caption_segs = _load_caption_hints(vtt_text)
                print(f"Loaded {len(caption_segs)} caption segments from {vtt_path}")
            else:
                print(f"WARNING: captions-vtt file not found: {vtt_path}")

    state: dict[str, Any] = {"idx": 0, "active": []}
    tagged = []
    for u in asr_units:
        mid = (u["start"] + u["end"]) / 2.0 if u["end"] > u["start"] else u["start"]
        tagged.append(u | {"speaker_raw": _speaker_at(mid, diar, state)})

    turns: list[dict[str, Any]] = []
    cur = None
    for u in tagged:
        token = str(u["text"])
        if cur is None:
            cur = {"speaker_raw": u["speaker_raw"], "start": u["start"], "end": u["end"], "parts": [token], "unit": u["unit"]}
            continue

        gap = u["start"] - float(cur["end"])
        dur = float(cur["end"]) - float(cur["start"])
        prospective = _join_tokens(cur["parts"] + [token])
        same_speaker = u["speaker_raw"] == cur["speaker_raw"]
        same_mode = u["unit"] == cur["unit"]

        should_split = (
            not same_speaker
            or not same_mode
            or gap > args.max_gap
            or dur >= args.max_seconds
            or (len(prospective) >= args.max_chars and prospective.endswith((".", "!", "?")))
        )

        if should_split:
            turns.append(cur)
            cur = {"speaker_raw": u["speaker_raw"], "start": u["start"], "end": u["end"], "parts": [token], "unit": u["unit"]}
        else:
            cur["end"] = u["end"]
            cur["parts"].append(token)

    if cur is not None:
        turns.append(cur)

    structured_turns: list[dict[str, Any]] = []
    prev_speaker: str | None = None  # Track previously identified real speaker
    prev_raw: str | None = None       # Track previous pyannote speaker label
    for i, t in enumerate(turns):
        turn_mid = (float(t["start"]) + float(t["end"])) / 2.0
        text_raw = _normalize_text(_join_tokens(t["parts"]))
        speaker_public, speaker_status, needs_review, reason = _public_label_policy(
            str(t["speaker_raw"]), approvals,
            caption_segs if caption_segs else None,
            turn_mid,
            text_hint=text_raw,
            prev_speaker=prev_speaker,
        )
        # Update prev_speaker for continuation detection
        raw = str(t["speaker_raw"])
        if speaker_public and speaker_public != "Unknown Speaker":
            prev_speaker = speaker_public
            prev_raw = raw
        elif raw != "UNKNOWN" and raw == prev_raw:
            # Same pyannote speaker continuing across turns — track raw ID too
            prev_speaker = speaker_public if speaker_public != "Unknown Speaker" else prev_speaker
        # For UNKNOWN segments, carry forward last known raw speaker if same diar segment
        if raw == "UNKNOWN" and prev_raw and prev_raw != "UNKNOWN":
            prev_speaker = prev_speaker  # keep last known

        structured_turns.append(
            {
                "turn_id": f"turn_{i+1:06d}",
                "start": round(float(t["start"]), 3),
                "end": round(float(t["end"]), 3),
                "text": text_raw,
                "speaker_raw": raw,
                "speaker_public": speaker_public,
                "speaker_status": speaker_status,
                "needs_review": bool(needs_review),
                "review_reason": reason,
                "confidence": None,
            }
        )

    # -----------------------------------------------------------------------
    # Pre-merge: consolidate consecutive turns by shared speaker_raw
    # When pyannote oscillates between SPEAKER_XX and UNKNOWN for the same speaker
    # (common with filler words like "the", "and", "so" getting labeled UNKNOWN while
    # content words get SPEAKER_XX), we merge identical speaker_raw blocks FIRST so the
    # oscillation is resolved before text heuristics run. Without this, Case A/B can't
    # merge across different speaker_raw values even when it's clearly the same person.
    # -----------------------------------------------------------------------
    _raw_sessions: dict[int, list[dict]] = {}
    for t in structured_turns:
        sid = id(t)
        _raw_sessions[sid] = [t]
    raw_merged: list[dict[str, Any]] = []
    i = 0
    while i < len(structured_turns):
        t = structured_turns[i]
        raw = str(t.get("speaker_raw") or "")
        # Strip pyannote suffix (_sp, _spk, etc.) for comparison
        base_raw = re.sub(r'_spk?$', '', raw)
        # Collect consecutive turns with same base speaker_raw
        group = [t]
        j = i + 1
        while j < len(structured_turns):
            next_raw = str(structured_turns[j].get("speaker_raw") or "")
            next_base = re.sub(r'_spk?$', '', next_raw)
            if next_base == base_raw:
                group.append(structured_turns[j])
                j += 1
            else:
                break
        # Merge the group into one turn
        if len(group) == 1:
            raw_merged.append(t.copy())
        else:
            merged_t = group[0].copy()
            merged_t["end"] = group[-1]["end"]
            merged_t["text"] = " ".join(g["text"] for g in group)
            raw_merged.append(merged_t)
        i = j
    print(f"Pre-merged {len(structured_turns)} turns into {len(raw_merged)} by speaker_raw (raw consolidation)")
    structured_turns = raw_merged

    # -----------------------------------------------------------------------
    # Pre-merge heuristics: identify speakers before merging so Case A/B can
    # use heuristic flags to make better merge decisions.
    # -----------------------------------------------------------------------
    structured_turns = _apply_name_call_handoffs(structured_turns)
    structured_turns = _apply_self_introductions(structured_turns, approvals)

    # -----------------------------------------------------------------------
    # Post-processing: merge consecutive turns using speaker-chain logic
    # -----------------------------------------------------------------------
    # Russ's rule: small unknown gaps between labeled speech = same person still
    # talking. We merge labeled blocks with tiny unknown gaps into the same chain.
    # Two rules:
    #   1. Same labeled speaker + small gap → merge
    #   2. Labeled speaker + small-gap Unknown next to it → Unknown absorbed into speaker
    # No merging across labeled→labeled boundaries (different people speaking).

    MERGE_MAX_GAP = 4.0   # seconds; labeled+labeled merge threshold
    ABSORB_MAX_GAP = 4.0  # seconds; Unknown blocks absorbed into adjacent labeled
    ABSORB_MIN_CHARS = 30  # minimum text length to absorb; tiny fragments are likely ASR noise
    MAX_CONSECUTIVE_ABSORB = 12  # max Unknown segments Case B will absorb in a row into one chain

    def _is_labeled(speaker: str) -> bool:
        return speaker not in ("Unknown Speaker", "")

    merged: list[dict[str, Any]] = []
    unknown_absorbed_count = 0  # consecutive Case B absorptions into current chain
    for i, t in enumerate(structured_turns):
        speaker = t.get("speaker_public", "")

        if not merged:
            merged.append(t.copy())
            continue

        prev = merged[-1]
        prev_speaker = prev.get("speaker_public", "")
        gap = float(t["start"]) - float(prev["end"])

        # Case A: both labeled, same speaker, small gap → merge
        # Block if the PREVIOUS turn was relabeled by a heuristic (handoff/self-intro) —
        # such turns represent complete speech acts that should not absorb following turns.
        # Exception: don't block labeled→heuristic merges (so labeled turns can absorb
        # heuristic-labeled turns that were upgraded from unknown via handoff or self-intro).
        _do_merge = (
            # Case A: both labeled, same speaker, small gap → merge
            (_is_labeled(speaker) and _is_labeled(prev_speaker)
             and prev_speaker == speaker and gap < MERGE_MAX_GAP
             and ((prev.get("handoff_applied") is not True and prev.get("self_intro_applied") is not True)
                  or (t.get("speaker_status") == "approved" and prev.get("speaker_status") == "heuristic" and prev.get("handoff_applied") is True)
                  or (prev.get("self_intro_applied") is True)
                  or (prev.get("speaker_status") == "approved" and t.get("speaker_status") == "approved")))
            # Pre-merge groups consecutive same speaker_raw blocks, but Case A can't merge them
            # when speaker_public resolves to "Unknown Speaker" for both (pyannote fragmentation).
            # Merge if speaker_raw matches — pre-merge guarantees they're consecutive.
            or (prev.get("speaker_raw") == t.get("speaker_raw") and gap < MERGE_MAX_GAP)
        )
        if _do_merge:
            prev["end"] = t["end"]
            prev["text"] = prev["text"] + " " + t["text"]

            # Take better status if needed
            status_priority = {"approved": 5, "heuristic": 4, "caption": 3, "caption_override": 3, "unresolved": 2, "unknown": 1}
            if status_priority.get(t.get("speaker_status", ""), 0) > status_priority.get(prev.get("speaker_status", ""), 0):
                prev["speaker_status"] = t["speaker_status"]
                prev["review_reason"] = t.get("review_reason")
            unknown_absorbed_count = 0
            continue

        # Case B: absorb small Unknown gaps into adjacent labeled speakers
        # A 0-gap Unknown turn abutting a labeled prev speaker is a pyannote fragmentation
        # artifact — absorb it (it's part of the prev labeled speaker's speech act).
        # A 0-gap Unknown turn abutting an Unknown prev speaker is a real speaker change
        # (or more fragments of the Unknown) — do NOT absorb (Case A would have merged if
        # prev was labeled and same speaker).
        # Case B: absorb small Unknown-labeled gaps (speaker_raw=UNKNOWN) into adjacent labeled speakers.
        # We check speaker_raw directly — a pyannote speaker ID like SPEAKER_29 may resolve to
        # "Unknown Speaker" publicly but is still a labeled pyannote speaker that should NOT be
        # absorbed here. Only true UNKNOWN pyannote segments are Case B absorption targets.
        prev_raw = prev.get("speaker_raw", "")
        curr_raw = t.get("speaker_raw", "")
        if prev_raw != "UNKNOWN" and curr_raw == "UNKNOWN" and gap < ABSORB_MAX_GAP and unknown_absorbed_count < MAX_CONSECUTIVE_ABSORB:
            prev["end"] = t["end"]
            prev["text"] = prev["text"] + " " + t["text"]
            unknown_absorbed_count += 1
            continue

        # Case C removed — do NOT absorb labeled turns into an Unknown-prev block.
        # Unknown→labeled transitions are real speaker changes; keep them separate.
        # Case B already handles labeled→Unknown (the more common ASR fragmentation).

        # Otherwise: keep separate
        merged.append(t)
        unknown_absorbed_count = 0

    before = len(structured_turns)
    structured_turns = merged
    print(f"Merged {before} turns into {len(structured_turns)} (merged {before - len(structured_turns)} fragments)")

    # Sentence-fragment repair runs after merge to fix cross-speaker splits
    structured_turns = _apply_sentence_fragment_repair(structured_turns)

    # Summary of label sources
    caption_labeled = sum(1 for t in structured_turns if t.get("speaker_status") == "caption")
    heuristic_labeled = sum(1 for t in structured_turns if t.get("speaker_status") == "heuristic")
    unknown = sum(1 for t in structured_turns if t.get("speaker_status") == "unknown")
    approved = sum(1 for t in structured_turns if t.get("speaker_status") == "approved")
    unresolved = sum(1 for t in structured_turns if t.get("speaker_status") == "unresolved")
    print(f"Labels: {approved} approved, {heuristic_labeled} heuristic, {caption_labeled} from captions, {unresolved} unresolved, {unknown} unknown")

    out = {
        "schema": "fairfax.structured_transcript.v1",
        "meeting": {
            "meeting_id": meeting.get("meeting_id"),
            "meeting_date": meeting.get("meeting_date"),
            "title": meeting.get("title"),
            "source_url": meeting.get("source_video_url") or meeting.get("source_url"),
        },
        "turns": structured_turns,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"turns={len(structured_turns)}")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

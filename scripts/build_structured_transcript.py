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

    def _is_labeled(speaker: str) -> bool:
        return speaker not in ("Unknown Speaker", "")

    merged: list[dict[str, Any]] = []
    for t in structured_turns:
        speaker = t.get("speaker_public", "")

        if not merged:
            merged.append(t)
            continue

        prev = merged[-1]
        prev_speaker = prev.get("speaker_public", "")
        gap = float(t["start"]) - float(prev["end"])

        # Case A: both labeled, same speaker, small gap → merge
        if _is_labeled(speaker) and _is_labeled(prev_speaker) and prev_speaker == speaker and gap < MERGE_MAX_GAP:
            prev["end"] = t["end"]
            prev["text"] = prev["text"] + " " + t["text"]
            # Take better status if needed
            status_priority = {"approved": 5, "heuristic": 4, "caption": 3, "caption_override": 3, "unresolved": 2, "unknown": 1}
            if status_priority.get(t.get("speaker_status", ""), 0) > status_priority.get(prev.get("speaker_status", ""), 0):
                prev["speaker_status"] = t["speaker_status"]
                prev["review_reason"] = t.get("review_reason")
            continue

        # Case B: prev is labeled, current is Unknown, tiny gap → absorb Unknown into prev speaker
        if _is_labeled(prev_speaker) and not _is_labeled(speaker) and gap < ABSORB_MAX_GAP:
            prev["end"] = t["end"]
            prev["text"] = prev["text"] + " " + t["text"]
            continue

        # Case C: current is labeled, prev is Unknown, tiny gap → absorb into current speaker
        if not _is_labeled(prev_speaker) and _is_labeled(speaker) and gap < ABSORB_MAX_GAP:
            # Extend the previous turn with this labeled turn's speaker and text
            # The prev turn keeps its speaker (Unknown) but extends its text and end time
            prev["end"] = t["end"]
            prev["text"] = prev["text"] + " " + t["text"]
            continue

        # Otherwise: keep separate
        merged.append(t)

    before = len(structured_turns)
    structured_turns = merged
    print(f"Merged {before} turns into {len(structured_turns)} (merged {before - len(structured_turns)} fragments)")

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

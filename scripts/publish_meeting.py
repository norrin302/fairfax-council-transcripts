#!/usr/bin/env python3
"""Publish a meeting to the static site.

Inputs:
- meetings/<meeting_id>.json (metadata)
- A Whisper verbose_json transcript file with `segments[]` (e.g. transcripts/*_complete.json)

Outputs:
- docs/transcripts/<meeting_id>-data.js (TRANSCRIPT_TURNS)
- docs/transcripts/<meeting_id>.html (page that renders with docs/js/transcript-page.js)
- docs/js/search-index.js (rebuilt)

This keeps the public site static and reproducible.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import urllib.request
import difflib
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]

# Allow `import scripts.transcribe` when running as a script.
sys.path.insert(0, str(REPO_ROOT))


def load_meeting(meeting_id: str) -> dict[str, Any]:
    p = REPO_ROOT / "meetings" / f"{meeting_id}.json"
    if not p.exists():
        raise SystemExit(f"Missing meeting metadata: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def chunk_segments(segments: list[dict[str, Any]], target_seconds: int = 30, max_chars: int = 650) -> list[dict[str, Any]]:
    """Combine small segments into larger turns for readability/search.

    If segments contain `new_speaker: true` (as provided by captions parsing), we flush the
    current buffer before starting the new segment. This preserves speaker-change boundaries
    even when we do not know speaker names.
    """
    turns: list[dict[str, Any]] = []
    buf: list[str] = []
    start = None
    end = None
    buf_hint = ""
    buf_hint_strength = ""
    active_hint = ""
    active_hint_strength = ""

    def flush():
        nonlocal buf, start, end, buf_hint, buf_hint_strength
        if start is None or end is None:
            return
        text = normalize_ws(" ".join(buf))
        if text:
            out = {"start": float(start), "end": float(end), "text": text}
            if buf_hint:
                out["speaker_hint"] = str(buf_hint)
            if buf_hint_strength:
                out["speaker_hint_strength"] = str(buf_hint_strength)
            turns.append(out)
        buf = []
        start = None
        end = None
        buf_hint = ""
        buf_hint_strength = ""

    for seg in segments:
        # Preserve explicit speaker-change boundaries (from captions parsing).
        if bool(seg.get("new_speaker")):
            if buf:
                flush()
            # New speaker started. If a hint is provided, use it; otherwise clear.
            active_hint = str(seg.get("speaker_hint") or "").strip()
            active_hint_strength = str(seg.get("speaker_hint_strength") or "").strip()
            if not active_hint:
                active_hint = ""
                active_hint_strength = ""

        seg_hint = str(seg.get("speaker_hint") or "").strip()
        seg_hint_strength = str(seg.get("speaker_hint_strength") or "").strip()

        # For highly reliable hints, we carry the hint forward across segments until the
        # next new_speaker boundary.
        if seg_hint and seg_hint_strength in {"explicit", "marker"}:
            if seg_hint != active_hint:
                if buf:
                    flush()
                active_hint = seg_hint
                active_hint_strength = seg_hint_strength

        # Compute the effective hint for this segment.
        # - If the segment itself has a hint, use it.
        # - Otherwise, only inherit the active hint when it was explicit.
        effective_hint = seg_hint or (active_hint if active_hint_strength in {"explicit", "marker"} else "")
        effective_strength = seg_hint_strength or (active_hint_strength if effective_hint else "")

        s = float(seg.get("start", 0) or 0)
        e = float(seg.get("end", s) or s)
        t = str(seg.get("text", "") or "")
        t = normalize_ws(t)
        if not t:
            continue

        # If the hint context changes (or falls back to unknown), split the turn to avoid
        # misattributing unlabeled text to a previously inferred speaker.
        if start is not None and (buf_hint or "") != (effective_hint or ""):
            flush()

        if start is None:
            start = s
            end = e
            buf = [t]
            buf_hint = effective_hint
            buf_hint_strength = effective_strength
        else:
            end = e
            buf.append(t)

        dur = (end - start) if (start is not None and end is not None) else 0
        joined = " ".join(buf)
        # Heuristic boundaries
        if dur >= target_seconds:
            flush()
        elif len(joined) >= max_chars and re.search(r"[.!?]\s*$", joined):
            flush()

    flush()
    return turns


def _parse_vtt_timestamp(ts: str) -> float:
    # Format: HH:MM:SS.mmm
    h, m, rest = ts.split(":")
    s, ms = rest.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def segments_from_webvtt(vtt_text: str) -> list[dict[str, Any]]:
    """Parse WebVTT text into a Whisper-like segments[] list.

    Granicus captions are generally accurate and timestamp-aligned with the player.
    We treat each cue as a segment.
    """
    lines = [ln.rstrip("\n") for ln in (vtt_text or "").splitlines()]
    segs: list[dict[str, Any]] = []
    i = 0
    sid = 0

    def normalize_caption(text: str) -> str:
        return normalize_ws(text)

    def titleize_name(raw: str) -> str:
        # Handles hyphenated/compound names like hardy-chandler
        parts = re.split(r"([\-'])", raw.strip())
        out = []
        for p in parts:
            if p in {"-", "'"}:
                out.append(p)
            else:
                out.append(p[:1].upper() + p[1:].lower() if p else "")
        return "".join(out)

    def _norm_for_hint(s: str) -> str:
        """Normalize for hint parsing (drop punctuation)."""
        s = (s or "").strip().lower()
        s = re.sub(r"[^a-z\-\'\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def _norm_for_header(s: str) -> str:
        """Normalize for header parsing (keep simple punctuation like ,:.)."""
        s = (s or "").strip().lower()
        # Keep comma/colon/period for boundary detection.
        s = re.sub(r"[^a-z0-9\-\'\s,\.:]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def parse_speaker_hint(line: str) -> str:
        """Parse a speaker hint from a caption line after stripping leading '>>'.

        Only returns hints for explicit, trustworthy patterns.
        """
        l = (line or "").strip()
        low = _norm_for_hint(l)

        # Known 2026 Fairfax, VA council roster (last token in captions is often last name).
        # We canonicalize common caption misspellings via fuzzy matching.
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

            # Try fuzzy match against roster keys.
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

            # Accept if reasonably close, or clearly better than the runner-up.
            if best and (best_ratio >= 0.66 or (best_ratio >= 0.58 and (best_ratio - second_ratio) >= 0.12)):
                return best

            # As a last resort, map by unique first-letter (works for pern->peterson, aye->amos, etc.).
            first = raw_last[:1]
            if first:
                candidates = [k for k in roster_keys if k.startswith(first)]
                if len(candidates) == 1:
                    return candidates[0]

            # Unknown/unreliable token.
            return ""

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
            # Only trust mayor name if it's clearly Read (Fairfax, VA).
            token = re.sub(r"[^a-z\-']", "", m.group(2) or "").strip().lower()
            ratio = difflib.SequenceMatcher(a=token, b="read").ratio() if token else 0.0
            if ratio >= 0.7:
                return "Mayor Catherine Read"
            return ""

        m = re.match(r"^(city\s+manager)\s+([a-z][a-z\-']+)", low)
        if m:
            # City manager labels are rarely present in captions. Avoid guessing.
            token = re.sub(r"[^a-z\-']", "", m.group(2) or "").strip().lower()
            if difflib.SequenceMatcher(a=token, b="coll").ratio() >= 0.7:
                return "City Manager David Coll"
            return ""
        return ""

    def split_inline_speaker_header(line: str) -> tuple[str, str, str]:
        """Detect and strip an inline speaker header at the start of a cue line.

        Examples:
          - "Councilmember Hall. Thank you..."
          - "Council member Hardy Chandler: I move..."
          - "Mayor Read, members of council, ..." (comma is common in these captions)

        Returns (speaker_hint, remainder_text, strength).
        strength is one of: "inline", "inline_loose", or "".
        """
        orig = (line or "").strip()
        cleaned = _norm_for_header(orig)

        # Council member header, require a punctuation boundary '.' or ':' (more trustworthy).
        m = re.match(
            r"^(council\s*member|councilmember|councilman|councilwoman)\s+([a-z\-']+)(?:\s+([a-z\-']+))?\s*[:\.]\s*(.*)$",
            cleaned,
        )
        if m:
            title = m.group(1)
            p1 = (m.group(2) or "").strip()
            p2 = (m.group(3) or "").strip()
            remainder = (m.group(4) or "").strip()
            # If the remainder immediately looks like another label list, skip (roll call, etc.).
            if remainder.startswith("council") or remainder.startswith("mayor"):
                return "", orig, ""
            name_raw = " ".join([x for x in [p1, p2] if x]).strip()
            parts = [p for p in name_raw.split(" ") if p]
            last = "-".join(parts) if len(parts) >= 2 else (parts[0] if parts else "")
            hint = parse_speaker_hint(f"{title} {last}")
            if hint and remainder:
                # Best-effort remainder reconstruction using original line (keep case/punct).
                # Find the first occurrence of punctuation after the title+name span.
                mm = re.match(
                    r"^(?:Council\s*member|Councilmember|Councilman|Councilwoman)\s+[A-Za-z\-']+(?:\s+[A-Za-z\-']+)?\s*[:\.]\s*(.*)$",
                    orig,
                )
                if mm:
                    return hint, (mm.group(1) or "").strip(), "inline"
                return hint, remainder, "inline"
            return (hint, remainder, "inline") if hint else ("", orig, "")

        # Lenient council member header: no punctuation after name.
        # Example: "Council member Peterson Thank you all..."
        # This pattern is common in some Fairfax clips, and is still relatively safe because:
        # - it must be the first line of the cue (enforced by caller)
        # - it requires a plausible utterance starter word
        # - it rejects the addressing form "Councilmember X, ..."
        starters = {
            "thank",
            "thanks",
            "uh",
            "um",
            "i",
            "yes",
            "no",
            "hi",
            "good",
            "okay",
            "so",
            "well",
        }
        if re.match(r"^(?:Council\s*member|Councilmember|Councilman|Councilwoman)\s+[A-Za-z\-']+(?:\s+[A-Za-z\-']+)?\s*,", orig):
            # Ambiguous addressing form.
            pass
        else:
            t = _norm_for_hint(orig)
            m2 = re.match(
                r"^(council\s*member|councilmember|councilman|councilwoman)\s+([a-z\-']+)(?:\s+([a-z\-']+))?\s+([a-z]+)\b(.*)$",
                t,
            )
            if m2:
                starter = (m2.group(4) or "").strip().lower()
                if starter in starters:
                    title = m2.group(1)
                    p1 = (m2.group(2) or "").strip()
                    p2 = (m2.group(3) or "").strip()
                    name_raw = " ".join([x for x in [p1, p2] if x]).strip()
                    parts = [p for p in name_raw.split(" ") if p]
                    last = "-".join(parts) if len(parts) >= 2 else (parts[0] if parts else "")
                    hint = parse_speaker_hint(f"{title} {last}")
                    if hint:
                        # Reconstruct remainder from original text (keep case) by dropping
                        # the title + name tokens.
                        mm = re.match(
                            r"^(?:Council\s*member|Councilmember|Councilman|Councilwoman)\s+[A-Za-z\-']+(?:\s+[A-Za-z\-']+)?\s+(.*)$",
                            orig,
                        )
                        if mm:
                            remainder = (mm.group(1) or "").strip()
                            # Avoid obvious non-speech lead-ins.
                            if not remainder.lower().startswith("members of council"):
                                return hint, remainder, "inline_loose"

        # Mayor header, allow comma as well (common: "Mayor Read, members of council").
        m = re.match(r"^(mayor)\s+([a-z\-']+)\s*[,\.:]\s*(.*)$", cleaned)
        if m:
            remainder = (m.group(3) or "").strip()
            if remainder.startswith("council") or remainder.startswith("mayor"):
                return "", orig, ""
            hint = parse_speaker_hint(f"mayor {m.group(2)}")
            if hint:
                mm = re.match(r"^(?:Mayor)\s+[A-Za-z\-']+\s*[,\.:]\s*(.*)$", orig)
                if mm:
                    return hint, (mm.group(1) or "").strip(), "inline"
                return hint, remainder, "inline"
        return "", orig, ""

    def looks_like_label_only(line: str) -> bool:
        t = _norm_for_hint(line)
        return bool(re.match(r"^(council\s*member|councilmember|councilman|councilwoman|mayor)\b", t))

    def parse_marker_only(line: str) -> str:
        """Return a speaker hint if the *entire* line is just a speaker marker.

        Examples:
          - "Councilmember Bates."
          - "Mayor Read"

        This is used to interpret standalone marker cues as reliable speaker boundaries.
        """
        t = _norm_for_hint(line)
        m = re.match(
            r"^(council\s*member|councilmember|councilman|councilwoman)\s+([a-z][a-z\-']+)$",
            t,
        )
        if m:
            return parse_speaker_hint(f"{m.group(1)} {m.group(2)}")
        m = re.match(r"^(mayor)\s+([a-z][a-z\-']+)$", t)
        if m:
            return parse_speaker_hint(f"{m.group(1)} {m.group(2)}")
        return ""

    while i < len(lines):
        line = lines[i].lstrip("\ufeff").strip()

        # Skip header and blank lines
        if not line:
            i += 1
            continue
        if line.upper().startswith("WEBVTT"):
            i += 1
            continue

        # Optional cue identifier line: if the next line is a timing line, skip id.
        if (i + 1) < len(lines) and ("-->" in lines[i + 1]):
            i += 1
            line = lines[i].strip()

        if "-->" not in line:
            i += 1
            continue

        m = re.match(r"(\d\d:\d\d:\d\d\.\d\d\d)\s*-->\s*(\d\d:\d\d:\d\d\.\d\d\d)", line)
        if not m:
            i += 1
            continue

        start = _parse_vtt_timestamp(m.group(1))
        end = _parse_vtt_timestamp(m.group(2))

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

            # Inline headers (without the '>>' marker) are only trusted at the very start
            # of a cue to avoid false positives from wrapped lines like:
            #   "... seconded by" / "Council member Amos. ..."
            if not speaker_hint and not buf_lines:
                ihint, remainder, istrength = split_inline_speaker_header(ln)
                if ihint:
                    # If the header line is *only* a name/title (no remainder), it is often
                    # a roll-call artifact. Only accept it if the next line looks like
                    # actual speech, not another label.
                    if not remainder:
                        j = i + 1
                        nxt = ""
                        while j < len(lines) and lines[j].strip() != "":
                            nxt = lines[j].strip()
                            if nxt:
                                break
                            j += 1
                        if nxt and looks_like_label_only(nxt):
                            ihint = ""  # ignore ambiguous roll-call label

                    if ihint:
                        speaker_hint = ihint
                        speaker_hint_strength = istrength or "inline"
                        new_speaker = True
                        ln = remainder
            buf_lines.append(ln)
            i += 1

        # Handle standalone marker cues like:
        #   "Councilmember Bates."
        #   "Mayor Read"
        # These appear in some Fairfax clips as a separate cue before the speech.
        if not speaker_hint and buf_lines:
            first = str(buf_lines[0] or "").strip()
            mhint = parse_marker_only(first)
            if mhint:
                # Drop the marker line from the caption text.
                buf_lines = buf_lines[1:]
                speaker_hint = mhint
                speaker_hint_strength = "marker"
                new_speaker = True

        text = normalize_caption(" ".join(buf_lines))

        # Drop vendor watermarks/noise
        if re.search(r"aberdeen\s+captioning|www\.|\b\d{3}-\d{3}-\d{4}\b", text, flags=re.I):
            continue

        # We emit empty-text segments when they are pure speaker markers so chunking can
        # still carry forward the speaker context.
        if text or (speaker_hint and new_speaker and not text):
            segs.append(
                {
                    "id": sid,
                    "start": float(start),
                    "end": float(end),
                    "text": text,
                    "new_speaker": bool(new_speaker),
                    "speaker_hint": speaker_hint,
                    "speaker_hint_strength": speaker_hint_strength,
                }
            )
            sid += 1

        i += 1

    return segs


def fetch_granicus_captions_vtt(source_video_url: str) -> str:
    """Fetch Granicus captions.vtt for a clip URL like https://fairfax.granicus.com/player/clip/4519"""
    m = re.search(r"/clip/(\d+)", source_video_url or "")
    if not m:
        raise RuntimeError(f"Could not extract clip id from source_video_url: {source_video_url}")
    clip_id = m.group(1)
    url = f"https://fairfax.granicus.com/videos/{clip_id}/captions.vtt"
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def load_elevenlabs_words(path: Path) -> list[dict[str, Any]]:
    """Load ElevenLabs speech-to-text JSON and return words[] entries."""
    data = json.loads(path.read_text(encoding="utf-8"))
    words = data.get("words") or []
    if not isinstance(words, list):
        return []
    # Only keep word tokens with timestamps and speaker ids
    out: list[dict[str, Any]] = []
    for w in words:
        try:
            if str(w.get("type")) != "word":
                continue
            s = float(w.get("start"))
            e = float(w.get("end"))
            sid = str(w.get("speaker_id") or "").strip()
            if not sid:
                continue
            out.append({"start": s, "end": e, "speaker_id": sid})
        except Exception:
            continue
    return out


def dominant_speaker_id(words: list[dict[str, Any]], start: float, end: float) -> str:
    """Return the dominant speaker_id in a time range using word counts."""
    if not words:
        return ""
    s = float(start)
    e = float(end)
    if e <= s:
        return ""
    counts: dict[str, int] = {}
    for w in words:
        ws = float(w.get("start", -1) or -1)
        if ws < s or ws > e:
            continue
        sid = str(w.get("speaker_id") or "")
        if not sid:
            continue
        counts[sid] = counts.get(sid, 0) + 1
    if not counts:
        return ""
    # Max by count
    return max(counts.items(), key=lambda kv: kv[1])[0]


def label_speakers(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Best-effort speaker labeling using heuristics from scripts/transcribe.py."""
    # Import without triggering yt-dlp requirements
    from scripts.transcribe import COUNCIL_MEMBERS, identify_speaker  # type: ignore

    prev = None
    out: list[dict[str, Any]] = []
    for t in turns:
        text = str(t.get("text", "") or "")
        name = identify_speaker(text, prev)
        prev = name

        speaker = "Unknown Speaker"
        if name and name != "Unknown":
            if name in COUNCIL_MEMBERS:
                title = COUNCIL_MEMBERS[name].get("title")
                if title and not str(name).lower().startswith(str(title).lower()):
                    speaker = f"{title} {name}"
                else:
                    speaker = name
            else:
                speaker = name

        out.append({
            "speaker": speaker,
            "speaker_source": "heuristic",
            "speaker_source_detail": "Heuristic (text-based speaker guess)",
            "start": float(t["start"]),
            "end": float(t["end"]),
            "text": text,
        })
    return out


def write_turns_js(meeting_id: str, turns: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    js = (
        f"// Transcript turns for {meeting_id}\n"
        "// AUTO-GENERATED by scripts/publish_meeting.py (do not hand-edit)\n"
        "const TRANSCRIPT_TURNS = "
        + json.dumps(turns, indent=2, ensure_ascii=False)
        + ";\n\n"
        + "if (typeof module !== 'undefined' && module.exports) {\n"
        + "  module.exports = TRANSCRIPT_TURNS;\n"
        + "}\n"
    )
    out_path.write_text(js, encoding="utf-8")


def write_transcript_html(meeting: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    meeting_id = meeting["meeting_id"]
    display_date = meeting.get("display_date") or meeting.get("meeting_date") or ""
    title = meeting.get("title") or "Meeting"
    source_url = meeting.get("source_video_url") or ""
    portal_url = meeting.get("official_meetings_portal_url") or ""
    agenda_url = meeting.get("official_agenda_url") or ""
    minutes_url = meeting.get("official_minutes_url") or ""

    # Minimal page shell. Transcript body is rendered by docs/js/transcript-page.js
    html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>{title} - {display_date}</title>
  <link rel=\"stylesheet\" href=\"../css/style.css\">
  <link rel=\"stylesheet\" href=\"../css/transcript-page.css\">
  <link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css\">
</head>
<body>
  <div class=\"container\">
    <header class=\"meeting-header\">
      <h1><i class=\"fas fa-landmark\"></i> Fairfax City Council Meeting</h1>
      <div class=\"meta\">
        <span><i class=\"fas fa-calendar\"></i> {display_date}</span> &bull;
        <span><i class=\"fas fa-file-alt\"></i> Full Transcript</span>
      </div>
    </header>

    <div class=\"ai-notice\">
      <h4><i class=\"fas fa-robot\"></i> AI-Generated Transcript</h4>
      <p>
        This transcript was generated using AI speech recognition and best-effort speaker labeling.
        It may contain errors.
        For the official record, refer to the
        <a href=\"{source_url}\" target=\"_blank\" rel=\"noopener\">city's video archive</a>.
      </p>
    </div>

    <div class=\"official-links\" id=\"official-resources\"></div>

    <div class=\"official-links\">
      <h3><i class=\"fas fa-list\"></i> Jump to section</h3>
      <div id=\"section-links\" style=\"display:flex; gap:12px; flex-wrap:wrap;\"></div>
    </div>

    <div class=\"search-container\">
      <input type=\"text\" id=\"search-input\" placeholder=\"Search within this meeting... (type to filter)\">
      <div id=\"search-count\"></div>
    </div>

    <div id=\"transcript\">
      <p style=\"color: #718096; text-align: center;\">Loading transcript…</p>
    </div>

    <button id=\"back-to-top\"><i class=\"fas fa-arrow-up\"></i> Top</button>
  </div>

  <script>
    const MEETING = {json.dumps({
        'meeting_id': meeting_id,
        'meeting_date': meeting.get('meeting_date'),
        'display_date': display_date,
        'title': title,
        'source_url': source_url,
        'official_meetings_portal_url': portal_url,
        'official_agenda_url': meeting.get('official_agenda_url'),
        'official_minutes_url': meeting.get('official_minutes_url'),
        'official_packet_url': meeting.get('official_packet_url'),
        'sections': meeting.get('sections') or [],
    }, ensure_ascii=False)};
  </script>
  <script src=\"./{meeting_id}-data.js\"></script>
  <script src=\"../js/transcript-page.js\"></script>
</body>
</html>
"""

    out_path.write_text(html, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Publish a meeting to docs/")
    ap.add_argument("meeting_id", help="Meeting id (must match meetings/<meeting_id>.json)")
    ap.add_argument("--input", "-i", help="Whisper verbose_json transcript (with segments[])")
    ap.add_argument(
        "--captions",
        action="store_true",
        help="Use official Granicus captions.vtt (derived from meeting.source_video_url) instead of --input",
    )
    ap.add_argument(
        "--diarization",
        default="",
        help="Optional ElevenLabs STT JSON with words[] + speaker_id to propagate council/mayor labels",
    )
    ap.add_argument("--chunk-seconds", type=int, default=30, help="Target chunk size in seconds")
    ap.add_argument("--max-chars", type=int, default=650, help="Max chars per chunk before forcing a boundary")
    ap.add_argument(
        "--label-speakers",
        action="store_true",
        help="Enable heuristic speaker labeling (can be inaccurate). Default is disabled for safety.",
    )
    args = ap.parse_args()

    meeting = load_meeting(args.meeting_id)

    diar_words: list[dict[str, Any]] = []
    if args.diarization:
        dp = (REPO_ROOT / args.diarization).resolve() if not Path(args.diarization).is_absolute() else Path(args.diarization)
        if dp.exists():
            diar_words = load_elevenlabs_words(dp)
    if args.captions:
        vtt = fetch_granicus_captions_vtt(str(meeting.get("source_video_url") or ""))
        segments = segments_from_webvtt(vtt)
        if not segments:
            raise SystemExit("No segments parsed from captions.vtt")
    else:
        if not args.input:
            raise SystemExit("Missing --input (or pass --captions)")
        input_path = (REPO_ROOT / args.input).resolve() if not Path(args.input).is_absolute() else Path(args.input)
        data = json.loads(input_path.read_text(encoding="utf-8"))
        segments = data.get("segments")
        if not isinstance(segments, list) or not segments:
            raise SystemExit("Input JSON missing segments[]")

    # If we have diarization, map speaker_id -> known speaker_hint using explicit caption tags.
    speaker_id_to_hint: dict[str, str] = {}
    if diar_words:
        scores: dict[str, dict[str, int]] = {}
        for seg in segments:
            hint = str(seg.get("speaker_hint") or "").strip()
            if not hint:
                continue
            sid = dominant_speaker_id(diar_words, float(seg.get("start", 0) or 0), float(seg.get("end", 0) or 0))
            if not sid:
                continue
            scores.setdefault(sid, {})
            scores[sid][hint] = scores[sid].get(hint, 0) + 1

        for sid, hcounts in scores.items():
            best_hint, best = max(hcounts.items(), key=lambda kv: kv[1])
            # Require a little evidence to avoid mapping on tiny cues.
            if best >= 2:
                speaker_id_to_hint[sid] = best_hint

    raw_turns = chunk_segments(segments, target_seconds=args.chunk_seconds, max_chars=args.max_chars)

    # Propagate diarization-derived speaker hints onto turns when possible.
    if diar_words and speaker_id_to_hint:
        for t in raw_turns:
            if str(t.get("speaker_hint") or "").strip():
                continue
            sid = dominant_speaker_id(diar_words, float(t.get("start", 0) or 0), float(t.get("end", 0) or 0))
            if sid and sid in speaker_id_to_hint:
                t["speaker_hint"] = speaker_id_to_hint[sid]
                t["speaker_hint_strength"] = "diarization"
    if args.label_speakers:
        labeled_turns = label_speakers(raw_turns)
    else:
        labeled_turns = [
            {
                "speaker": str(t.get("speaker_hint") or "").strip() or "Unknown Speaker",
                "speaker_source": (
                    "captions" if str(t.get("speaker_hint") or "").strip() and str(t.get("speaker_hint_strength") or "").strip() in {"explicit", "inline", "inline_loose"}
                    else "diarization" if str(t.get("speaker_hint") or "").strip() and str(t.get("speaker_hint_strength") or "").strip() == "diarization"
                    else "unknown"
                ),
                "speaker_source_detail": (
                    "Captions (explicit speaker tag)" if str(t.get("speaker_hint_strength") or "").strip() == "explicit"
                    else "Captions (standalone marker cue)" if str(t.get("speaker_hint_strength") or "").strip() == "marker"
                    else "Captions (inline header)" if str(t.get("speaker_hint_strength") or "").strip() == "inline"
                    else "Captions (inline header, loose)" if str(t.get("speaker_hint_strength") or "").strip() == "inline_loose"
                    else "Diarization (mapped from caption tags)" if str(t.get("speaker_hint_strength") or "").strip() == "diarization"
                    else ""
                ),
                "start": float(t["start"]),
                "end": float(t["end"]),
                "text": str(t.get("text", "") or ""),
            }
            for t in raw_turns
        ]

    turns_out = REPO_ROOT / "docs" / "transcripts" / f"{args.meeting_id}-data.js"
    html_out = REPO_ROOT / "docs" / "transcripts" / f"{args.meeting_id}.html"

    write_turns_js(args.meeting_id, labeled_turns, turns_out)
    write_transcript_html(meeting, html_out)

    # Rebuild global index
    from scripts.build_search_index import build  # type: ignore

    build()

    print(f"Published {args.meeting_id} -> {html_out} + {turns_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

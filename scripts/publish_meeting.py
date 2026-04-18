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
    active_hint = ""

    def flush():
        nonlocal buf, start, end, buf_hint
        if start is None or end is None:
            return
        text = normalize_ws(" ".join(buf))
        if text:
            out = {"start": float(start), "end": float(end), "text": text}
            if buf_hint:
                out["speaker_hint"] = str(buf_hint)
            turns.append(out)
        buf = []
        start = None
        end = None
        buf_hint = ""

    for seg in segments:
        # Preserve explicit speaker-change boundaries (from captions parsing).
        if bool(seg.get("new_speaker")):
            if buf:
                flush()
            # New speaker started. If a hint is provided, use it; otherwise clear.
            active_hint = str(seg.get("speaker_hint") or "").strip()
            if not active_hint:
                active_hint = ""

        # If we see a new hint mid-stream, treat it as a boundary.
        seg_hint = str(seg.get("speaker_hint") or "").strip()
        if seg_hint and seg_hint != active_hint:
            if buf:
                flush()
            active_hint = seg_hint

        s = float(seg.get("start", 0) or 0)
        e = float(seg.get("end", s) or s)
        t = str(seg.get("text", "") or "")
        t = normalize_ws(t)
        if not t:
            continue

        if start is None:
            start = s
            end = e
            buf = [t]
            buf_hint = active_hint
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

    def parse_speaker_hint(line: str) -> str:
        """Parse a speaker hint from a caption line after stripping leading '>>'.

        Only returns hints for explicit, trustworthy patterns.
        """
        l = (line or "").strip()
        low = l.lower()

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

        m = re.match(r"^(councilmember)\s+([a-z][a-z\-']+)", low)
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
        while i < len(lines) and lines[i].strip() != "":
            ln = lines[i].strip()
            if ln.startswith(">>"):
                new_speaker = True
                ln = ln[2:].lstrip()
                if not speaker_hint:
                    speaker_hint = parse_speaker_hint(ln)
            buf_lines.append(ln)
            i += 1

        text = normalize_caption(" ".join(buf_lines))

        # Drop vendor watermarks/noise
        if re.search(r"aberdeen\s+captioning|www\.|\b\d{3}-\d{3}-\d{4}\b", text, flags=re.I):
            continue

        if text:
            segs.append({
                "id": sid,
                "start": float(start),
                "end": float(end),
                "text": text,
                "new_speaker": bool(new_speaker),
                "speaker_hint": speaker_hint,
            })
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
    ap.add_argument("--chunk-seconds", type=int, default=30, help="Target chunk size in seconds")
    ap.add_argument("--max-chars", type=int, default=650, help="Max chars per chunk before forcing a boundary")
    ap.add_argument(
        "--label-speakers",
        action="store_true",
        help="Enable heuristic speaker labeling (can be inaccurate). Default is disabled for safety.",
    )
    args = ap.parse_args()

    meeting = load_meeting(args.meeting_id)
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

    raw_turns = chunk_segments(segments, target_seconds=args.chunk_seconds, max_chars=args.max_chars)
    if args.label_speakers:
        labeled_turns = label_speakers(raw_turns)
    else:
        labeled_turns = [
            {
                "speaker": str(t.get("speaker_hint") or "").strip() or "Unknown Speaker",
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

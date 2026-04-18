#!/usr/bin/env python3
"""Build docs/js/search-index.js from per-meeting metadata + transcript turn data.

Source of truth:
- Meeting metadata: meetings/*.json
- Transcript turns (published): docs/transcripts/<meeting_id>-data.js (TRANSCRIPT_TURNS)

Output:
- docs/js/search-index.js (SEARCH_INDEX)
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_meetings(repo_root: Path) -> list[dict[str, Any]]:
    meetings_dir = repo_root / "meetings"
    if not meetings_dir.exists():
        raise RuntimeError(f"Missing meetings directory: {meetings_dir}")

    meetings: list[dict[str, Any]] = []
    for p in sorted(meetings_dir.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        data["_path"] = str(p)
        meetings.append(data)

    # Stable ordering: newest first (helps deterministic output)
    meetings.sort(key=lambda m: (m.get("meeting_date", ""), m.get("meeting_id", "")), reverse=True)
    return meetings


def _format_timestamp(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _make_snippet(text: str, max_len: int = 220) -> str:
    t = re.sub(r"\s+", " ", text).strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


def _extract_turns_from_js(js_path: Path) -> list[dict[str, Any]]:
    raw = js_path.read_text(encoding="utf-8")
    m = re.search(r"const\s+TRANSCRIPT_TURNS\s*=\s*(\[.*?\n\];)\s*$", raw, re.S)
    if not m:
        raise RuntimeError(f"Could not find TRANSCRIPT_TURNS array in {js_path}")
    arr = m.group(1).strip()
    if arr.endswith(";"):
        arr = arr[:-1]
    turns = json.loads(arr)
    if not isinstance(turns, list):
        raise RuntimeError("TRANSCRIPT_TURNS did not parse to a list")
    return turns


def _section_for(seconds: int, sections: list[dict[str, Any]] | None) -> str:
    if not sections:
        return ""

    # Expect list like: [{start_seconds: int, label: str}, ...] in ascending start_seconds
    label = str(sections[0].get("label", "") or "")
    for sec in sections:
        start = int(sec.get("start_seconds", 0) or 0)
        name = str(sec.get("label", "") or "")
        if seconds >= start:
            label = name
        else:
            break
    return label


def build() -> None:
    meetings_out: list[dict[str, Any]] = []
    segments_out: list[dict[str, Any]] = []

    meetings = load_meetings(REPO_ROOT)

    for meeting in meetings:
        meeting_id = str(meeting.get("meeting_id") or "").strip()
        meeting_date = str(meeting.get("meeting_date") or "").strip()
        title = str(meeting.get("title") or "").strip()
        meeting_type = str(meeting.get("meeting_type") or "").strip()
        source_url = str(meeting.get("source_video_url") or meeting.get("source_url") or "").strip()
        transcript_url = str(meeting.get("transcript_url") or "").strip()
        transcript_turns_js = str(meeting.get("transcript_turns_js") or meeting.get("transcript_data_js") or "").strip()
        sections = meeting.get("sections")
        duration_hint = meeting.get("duration_seconds")

        if not meeting_id or not meeting_date or not title or not transcript_url or not transcript_turns_js:
            raise RuntimeError(f"Invalid meeting config in {meeting.get('_path')}: missing required fields")

        data_path = (REPO_ROOT / transcript_turns_js).resolve()
        turns = _extract_turns_from_js(data_path)

        # Meeting duration best-effort
        duration = 0
        if turns:
            last_end = turns[-1].get("end")
            if isinstance(last_end, (int, float)):
                duration = int(math.ceil(float(last_end)))
        if isinstance(duration_hint, (int, float)):
            duration = max(duration, int(duration_hint))

        meetings_out.append(
            {
                "meeting_id": meeting_id,
                "meeting_date": meeting_date,
                "title": title,
                "meeting_type": meeting_type,
                "source_url": source_url,
                "duration_seconds": duration,
                "transcript_url": transcript_url,
                "sections": [str(s.get("label", "") or "") for s in (sections or [])],
            }
        )

        for idx, turn in enumerate(turns):
            start = int(math.floor(float(turn.get("start", 0) or 0)))
            text = str(turn.get("text", "") or "").strip()
            speaker = str(turn.get("speaker", "Unknown") or "Unknown").strip()

            segments_out.append(
                {
                    "meeting_id": meeting_id,
                    "meeting_date": meeting_date,
                    "speaker": speaker,
                    "section": _section_for(start, sections),
                    "turn_index": idx,
                    "start_seconds": start,
                    "timestamp_label": _format_timestamp(start),
                    "transcript_text": text,
                    "snippet": _make_snippet(text),
                }
            )

    # Deterministic speaker list
    speakers = sorted({s["speaker"] for s in segments_out if s.get("speaker")})

    search_index = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "meetings": meetings_out,
        "segments": segments_out,
        "speakers": speakers,
    }

    out_path = REPO_ROOT / "docs/js/search-index.js"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Keep it as a JS file for GitHub Pages, but data is JSON-friendly.
    js = (
        "// Search index for Fairfax City Council transcripts\n"
        "// AUTO-GENERATED by scripts/build_search_index.py (do not hand-edit)\n\n"
        + "const SEARCH_INDEX = "
        + json.dumps(search_index, indent=2, ensure_ascii=False)
        + ";\n\n"
        + "if (typeof module !== 'undefined' && module.exports) {\n"
        + "  module.exports = SEARCH_INDEX;\n"
        + "}\n"
    )
    out_path.write_text(js, encoding="utf-8")
    print(f"Wrote {out_path} (meetings={len(meetings_out)}, segments={len(segments_out)})")


if __name__ == "__main__":
    build()

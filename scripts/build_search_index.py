#!/usr/bin/env python3
"""Build docs/js/search-index.js from canonical transcript turn data.

Current state:
- Source of truth for the published Apr 14, 2026 meeting transcript is:
  docs/transcripts/transcript-data.js (TRANSCRIPT_TURNS)

This script turns those turns into a client-side SEARCH_INDEX that powers
cross-meeting search on the homepage.

As we add more meetings, extend MEETINGS below.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class MeetingConfig:
    meeting_id: str
    meeting_date: str  # YYYY-MM-DD
    title: str
    meeting_type: str
    source_url: str
    transcript_url: str
    transcript_data_js: str
    full_duration_seconds: int | None = None
    # Topic/section shortcuts (best-effort, not official agenda)
    sections: list[tuple[int, str]] | None = None  # [(start_seconds, label)]


MEETINGS: list[MeetingConfig] = [
    MeetingConfig(
        meeting_id="apr-14-2026",
        meeting_date="2026-04-14",
        title="City Council Regular Meeting",
        meeting_type="regular",
        source_url="https://fairfax.granicus.com/player/clip/4519",
        transcript_url="transcripts/apr-14-2026.html",
        transcript_data_js="docs/transcripts/apr-14-2026-data.js",
        full_duration_seconds=10020,
        sections=[
            (0, "Meeting"),
            (104, "Library Week Proclamation"),
            (439, "Earth Day and Arbor Day"),
            (695, "Monarch Pledge"),
            (1017, "Women's Club 70th Anniversary"),
            (1249, "Telecommunicators Week"),
            (1679, "Public Comment (Willard Sherwood Center)"),
        ],
    )
]


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


def _section_for(seconds: int, sections: list[tuple[int, str]] | None) -> str:
    if not sections:
        return ""
    label = sections[0][1]
    for start, name in sections:
        if seconds >= start:
            label = name
        else:
            break
    return label


def build() -> None:
    meetings_out: list[dict[str, Any]] = []
    segments_out: list[dict[str, Any]] = []

    for meeting in MEETINGS:
        data_path = (REPO_ROOT / meeting.transcript_data_js).resolve()
        turns = _extract_turns_from_js(data_path)

        # Meeting duration best-effort
        duration = 0
        if turns:
            last_end = turns[-1].get("end")
            if isinstance(last_end, (int, float)):
                duration = int(math.ceil(float(last_end)))
        if meeting.full_duration_seconds:
            duration = max(duration, int(meeting.full_duration_seconds))

        meetings_out.append(
            {
                "meeting_id": meeting.meeting_id,
                "meeting_date": meeting.meeting_date,
                "title": meeting.title,
                "meeting_type": meeting.meeting_type,
                "source_url": meeting.source_url,
                "duration_seconds": duration,
                "transcript_url": meeting.transcript_url,
                "sections": [name for _, name in (meeting.sections or [])],
            }
        )

        for idx, turn in enumerate(turns):
            start = int(math.floor(float(turn.get("start", 0) or 0)))
            text = str(turn.get("text", "") or "").strip()
            speaker = str(turn.get("speaker", "Unknown") or "Unknown").strip()

            segments_out.append(
                {
                    "meeting_id": meeting.meeting_id,
                    "meeting_date": meeting.meeting_date,
                    "speaker": speaker,
                    "section": _section_for(start, meeting.sections),
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

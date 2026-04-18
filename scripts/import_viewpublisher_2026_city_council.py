#!/usr/bin/env python3
"""Import 2026 City Council meetings list from Granicus ViewPublisher (view_id=13).

Produces a JSON list with clip_id, date, duration, agenda/minutes links, and MP3/MP4 URLs.

Usage:
  python3 scripts/import_viewpublisher_2026_city_council.py --out scripts/city_council_2026.json
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Any
from urllib.request import urlopen, Request


REPO_ROOT = Path(__file__).resolve().parents[1]
VIEWPUBLISHER_URL = "https://fairfax.granicus.com/ViewPublisher.php?view_id=13"


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    with urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "ignore")


def duration_to_seconds(s: str) -> int:
    """Convert strings like '02h 47m' / '03h 37m' / '00h 45m' to seconds."""
    t = unescape(s or "")
    t = re.sub(r"\s+", " ", t.replace("\xa0", " ")).strip()
    mh = re.search(r"(\d{1,2})\s*h", t)
    mm = re.search(r"(\d{1,2})\s*m", t)
    h = int(mh.group(1)) if mh else 0
    m = int(mm.group(1)) if mm else 0
    return h * 3600 + m * 60


def parse_date(s: str) -> str:
    """Return ISO date YYYY-MM-DD from strings like 'Apr  7, 2026'."""
    t = re.sub(r"\s+", " ", (s or "").strip())
    dt = datetime.strptime(t, "%b %d, %Y")
    return dt.date().isoformat()


def month_slug(dt: datetime) -> str:
    return dt.strftime("%b").lower()


def meeting_id_from_date(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{month_slug(dt)}-{dt.strftime('%d')}-{dt.strftime('%Y')}"


def extract_2026_city_council_section(html: str) -> str:
    start = html.find("<!-- 2026 City Council Meeting -->")
    if start < 0:
        raise RuntimeError("Could not find 2026 City Council Meeting section")
    end = html.find("<!-- End 2026 City Council Meeting -->", start)
    if end < 0:
        raise RuntimeError("Could not find end marker for 2026 City Council Meeting section")
    return html[start:end]


TAG_RE = re.compile(r"<[^>]+>")


def strip_tags(s: str) -> str:
    t = TAG_RE.sub("", s or "")
    t = unescape(t)
    t = t.replace("\xa0", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def parse_rows(section_html: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    # Iterate table rows that contain a clip_id
    for tr in re.findall(r"<tr\b[\s\S]*?</tr>", section_html, flags=re.I):
        mclip = re.search(r"clip_id=(\d+)", tr)
        if not mclip:
            continue
        clip_id = int(mclip.group(1))

        # Name
        mname = re.search(r"&nbsp;([^<\r\n]+)", tr)
        name = strip_tags(mname.group(1)) if mname else "City Council Meeting"

        # Date
        mdate = re.search(r"<td[^>]*nowrap[^>]*>\s*([^<]+)\s*</td>", tr, flags=re.I)
        date_label = strip_tags(mdate.group(1)) if mdate else ""
        date_iso = parse_date(date_label) if date_label else ""

        # Duration
        mdur = re.search(r"<td[^>]*headers=\"Duration[\s\S]*?\">([\s\S]*?)</td>", tr, flags=re.I)
        duration_label = strip_tags(mdur.group(1)) if mdur else ""
        duration_seconds = duration_to_seconds(duration_label)

        # Links
        agenda = None
        minutes = None
        mp3 = None
        mp4 = None

        magenda = re.search(r"href=\"(//fairfax\.granicus\.com/AgendaViewer\.php[^\"]+)\"", tr)
        if magenda:
            agenda = "https:" + magenda.group(1)

        mminutes = re.search(r"href=\"(//fairfax\.granicus\.com/MinutesViewer\.php[^\"]+)\"", tr)
        if mminutes:
            minutes = "https:" + mminutes.group(1)

        mmp3 = re.search(r"href=\"(https://archive-video\.granicus\.com/[^\"]+\.mp3)\"", tr)
        if mmp3:
            mp3 = mmp3.group(1)

        mmp4 = re.search(r"href=\"(https://archive-video\.granicus\.com/[^\"]+\.mp4)\"", tr)
        if mmp4:
            mp4 = mmp4.group(1)

        rows.append(
            {
                "clip_id": clip_id,
                "name": name,
                "date_label": date_label,
                "date": date_iso,
                "duration_label": duration_label,
                "duration_seconds": duration_seconds,
                "agenda_url": agenda,
                "minutes_url": minutes,
                "mp3_url": mp3,
                "mp4_url": mp4,
                "player_url": f"https://fairfax.granicus.com/player/clip/{clip_id}",
                "media_player_url": f"https://fairfax.granicus.com/MediaPlayer.php?view_id=13&clip_id={clip_id}",
                "meeting_id_suggested": meeting_id_from_date(date_iso) if date_iso else None,
            }
        )

    # Stable order newest->oldest
    rows.sort(key=lambda r: (r.get("date") or "", r.get("clip_id") or 0), reverse=True)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="scripts/city_council_2026.json")
    ap.add_argument("--url", default=VIEWPUBLISHER_URL)
    args = ap.parse_args()

    html = fetch(args.url)
    section = extract_2026_city_council_section(html)
    rows = parse_rows(section)

    out_path = (REPO_ROOT / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"generated_at": datetime.utcnow().isoformat() + "Z", "meetings": rows}, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} (meetings={len(rows)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


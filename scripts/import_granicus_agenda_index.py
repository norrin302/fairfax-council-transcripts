#!/usr/bin/env python3
"""Import agenda index points (time + label) from a Granicus clip page.

For Fairfax Granicus clips, the player page includes an "Index" panel with
div.index-point elements that contain the official agenda headings and a start
time in seconds.

This script fetches the clip HTML, extracts those points, and writes them into
meetings/<meeting_id>.json as `sections`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


class IndexPointParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_index_point = False
        self.current_time: int | None = None
        self.buf: list[str] = []
        self.points: list[dict[str, Any]] = []

    def handle_starttag(self, tag, attrs):
        if tag != "div":
            return
        attrs_d = dict(attrs)
        cls = attrs_d.get("class", "")
        if "index-point" not in cls:
            return
        t = attrs_d.get("time")
        if not t or not re.match(r"^\d+$", t):
            return
        self.in_index_point = True
        self.current_time = int(t)
        self.buf = []

    def handle_endtag(self, tag):
        if tag != "div":
            return
        if not self.in_index_point:
            return
        label = re.sub(r"\s+", " ", " ".join(self.buf)).strip()
        if label and self.current_time is not None:
            self.points.append({"start_seconds": self.current_time, "label": label})
        self.in_index_point = False
        self.current_time = None
        self.buf = []

    def handle_data(self, data):
        if self.in_index_point:
            self.buf.append(data)


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def load_meeting(meeting_id: str) -> tuple[Path, dict[str, Any]]:
    p = REPO_ROOT / "meetings" / f"{meeting_id}.json"
    if not p.exists():
        raise SystemExit(f"Missing meeting metadata: {p}")
    return p, json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Import Granicus agenda index points into meetings/<id>.json")
    ap.add_argument("meeting_id")
    ap.add_argument("--keep", choices=["all", "top"], default="top", help="Keep all points or only top-level numeric items")
    args = ap.parse_args()

    path, meeting = load_meeting(args.meeting_id)
    clip_url = meeting.get("source_video_url") or meeting.get("source_url")
    if not clip_url:
        raise SystemExit("Meeting JSON missing source_video_url")

    html = fetch(str(clip_url))
    parser = IndexPointParser()
    parser.feed(html)

    points = sorted(parser.points, key=lambda p: int(p["start_seconds"]))

    if args.keep == "top":
        # Keep only top-level numeric agenda headings like "1. ...", "2. ...", "14. ..."
        points = [p for p in points if re.match(r"^\s*\d+\.", p.get("label", ""))]

    if not points:
        raise SystemExit("No index points found (page layout may have changed)")

    meeting["sections"] = points
    path.write_text(json.dumps(meeting, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated {path} with {len(points)} sections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


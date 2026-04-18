#!/usr/bin/env python3
"""Batch publish all available 2026 City Council meetings from ViewPublisher export.

Pipeline per meeting:
1) Ensure meetings/<meeting_id>.json exists (metadata).
2) Import Granicus Index -> sections.
3) Prefer official Granicus closed captions (captions.vtt) for transcript text/timestamps.
   Fallback: chunked OpenAI transcription if captions are unavailable.
4) Publish to docs/ + rebuild search index.

This script is resumable: it skips meetings that already have docs/transcripts/<meeting_id>.html.

Usage:
  python3 scripts/batch_publish_2026_city_council.py --max 2
  python3 scripts/batch_publish_2026_city_council.py
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_URL = "https://www.fairfaxva.gov/Government/Public-Meetings/City-Meetings"


def granicus_has_captions(clip_id: int) -> bool:
    url = f"https://fairfax.granicus.com/videos/{int(clip_id)}/captions.vtt"
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=20) as resp:
            return int(getattr(resp, "status", 0) or 0) == 200
    except Exception:
        return False


def sh(cmd: list[str], *, cwd: Path) -> None:
    p = subprocess.run(cmd, cwd=str(cwd))
    if p.returncode != 0:
        raise SystemExit(p.returncode)


def meeting_type_from_name(name: str) -> str:
    n = (name or "").lower()
    if "work session" in n:
        return "work_session"
    if "special" in n:
        return "special"
    if "public hearing" in n:
        return "public_hearing"
    if "retreat" in n:
        return "other"
    return "regular"


def meeting_id_from_date(date_iso: str) -> str:
    dt = datetime.strptime(date_iso, "%Y-%m-%d")
    return f"{dt.strftime('%b').lower()}-{dt.strftime('%d')}-{dt.strftime('%Y')}"


def ensure_unique_meeting_id(base_id: str, clip_id: int) -> str:
    p = REPO_ROOT / "meetings" / f"{base_id}.json"
    if not p.exists():
        return base_id
    try:
        existing = json.loads(p.read_text(encoding="utf-8"))
        if int(existing.get("granicus_clip_id") or 0) == int(clip_id):
            return base_id
        src = str(existing.get("source_video_url") or "")
        if f"/clip/{int(clip_id)}" in src or f"clip_id={int(clip_id)}" in src:
            return base_id
    except Exception:
        pass
    return f"{base_id}-{clip_id}"


def write_meeting_metadata(meeting_id: str, m: dict) -> Path:
    meetings_dir = REPO_ROOT / "meetings"
    meetings_dir.mkdir(parents=True, exist_ok=True)
    out_path = meetings_dir / f"{meeting_id}.json"
    if out_path.exists():
        return out_path

    date_iso = m.get("date")
    display = m.get("date_label") or date_iso
    title = m.get("name") or "City Council Meeting"
    meeting_type = meeting_type_from_name(title)
    clip_id = int(m.get("clip_id"))

    data = {
        "meeting_id": meeting_id,
        "meeting_date": date_iso,
        "display_date": display,
        "title": title,
        "meeting_type": meeting_type,
        "city": "Fairfax, VA",

        "granicus_clip_id": clip_id,
        "source_video_url": m.get("player_url"),
        "official_meetings_portal_url": PORTAL_URL,

        "official_agenda_url": m.get("agenda_url"),
        "official_minutes_url": m.get("minutes_url"),
        "official_packet_url": None,

        "transcript_url": f"transcripts/{meeting_id}.html",
        "transcript_turns_js": f"docs/transcripts/{meeting_id}-data.js",

        "duration_seconds": int(m.get("duration_seconds") or 0),
        "sections": [],
    }
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", default="scripts/city_council_2026.json", help="Input JSON from import_viewpublisher_2026_city_council.py")
    ap.add_argument("--max", type=int, default=0, help="If >0, process at most N meetings")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lst = json.loads((REPO_ROOT / args.list).read_text(encoding="utf-8"))
    meetings: list[dict] = lst.get("meetings") or []

    done = 0
    for m in meetings:
        name = str(m.get("name") or "")
        if "cancel" in name.lower():
            continue
        if not m.get("mp3_url"):
            continue

        date_iso = str(m.get("date") or "").strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_iso):
            continue

        clip_id = int(m.get("clip_id"))
        base_id = meeting_id_from_date(date_iso)
        meeting_id = ensure_unique_meeting_id(base_id, clip_id)

        html_out = REPO_ROOT / "docs" / "transcripts" / f"{meeting_id}.html"
        if html_out.exists():
            continue

        print(f"=== {meeting_id} :: {name} (clip_id={clip_id}) ===")

        if args.dry_run:
            continue

        write_meeting_metadata(meeting_id, m)

        # Sections from official clip index
        sh(["python3", "scripts/import_granicus_agenda_index.py", meeting_id, "--keep", "all"], cwd=REPO_ROOT)

        # Publish page + index
        if granicus_has_captions(clip_id):
            sh(["python3", "scripts/publish_meeting.py", meeting_id, "--captions"], cwd=REPO_ROOT)
        else:
            # Fallback: transcribe (chunked) then publish from the merged Whisper JSON
            sh([
                str(REPO_ROOT / ".venv" / "bin" / "python"),
                "scripts/transcribe_openai_chunked.py",
                "--meeting-id",
                meeting_id,
                "--audio-url",
                str(m.get("mp3_url")),
                "--meeting-date",
                str(m.get("date_label") or date_iso),
                "--segment-seconds",
                "600",
            ], cwd=REPO_ROOT)

            sh(["python3", "scripts/publish_meeting.py", meeting_id, "-i", f"transcripts/{meeting_id}_complete.json"], cwd=REPO_ROOT)

        # Commit + push per meeting (keeps deployments incremental)
        sh(["git", "add", "-A"], cwd=REPO_ROOT)
        sh(["git", "commit", "-m", f"Publish {meeting_id} transcript"], cwd=REPO_ROOT)
        sh(["git", "push", "origin", "main"], cwd=REPO_ROOT)

        done += 1
        if args.max and done >= args.max:
            break

    print(f"Done. Published {done} meeting(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

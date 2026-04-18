#!/usr/bin/env python3
"""Run ElevenLabs Scribe v2 speech-to-text with diarization.

Purpose in this repo:
- We already use official Granicus captions.vtt for accurate text + timing.
- This tool is to get *speaker diarization* (speaker_id per word) so we can
  attribute captions/turns to consistent speakers.

Output:
- Writes raw JSON response to the path you specify.

Notes:
- Speaker IDs returned by diarization are per-file (not guaranteed stable across meetings).
- Map those IDs to real names via a separate workflow (voiceprints or manual mapping).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests


API_URL = "https://api.elevenlabs.io/v1/speech-to-text"


def _load_key_from_env_files() -> str:
    """Best-effort load ELEVENLABS_API_KEY from common .env locations.

    We avoid printing the key. This is only to reduce friction when Russ stores
    the key outside process env.
    """

    candidates = [
        # Repo-local
        Path.cwd() / ".env",
        # OpenClaw common locations
        Path("~/.openclaw/.env").expanduser(),
        Path("~/.openclaw/secrets.env").expanduser(),
        # Fallback
        Path("~/.env").expanduser(),
    ]

    for p in candidates:
        try:
            if not p.exists():
                continue
            for line in p.read_text(encoding="utf-8").splitlines():
                if not line or line.lstrip().startswith("#"):
                    continue
                if line.startswith("ELEVENLABS_API_KEY="):
                    v = line.split("=", 1)[1].strip().strip('"\'')
                    if v:
                        return v
        except Exception:
            continue
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", help="Path to an audio file (mp3/wav/etc)")
    ap.add_argument("--out", required=True, help="Write raw response JSON to this path")
    ap.add_argument("--model-id", default="scribe_v2")
    ap.add_argument("--diarize", action="store_true", default=True)
    ap.add_argument("--timestamps", default="word", choices=["word", "segment", "none"])
    ap.add_argument("--language", default="", help="Optional language code hint (e.g. eng)")
    args = ap.parse_args()

    key = os.environ.get("ELEVENLABS_API_KEY") or _load_key_from_env_files()
    if not key:
        print("ERROR: ELEVENLABS_API_KEY is not set", file=sys.stderr)
        return 2

    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"ERROR: missing file: {audio_path}", file=sys.stderr)
        return 2

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "model_id": args.model_id,
        "diarize": "true" if args.diarize else "false",
    }
    if args.timestamps != "none":
        data["timestamps_granularity"] = args.timestamps
    if args.language:
        data["language_code"] = args.language

    with audio_path.open("rb") as f:
        resp = requests.post(
            API_URL,
            headers={"xi-api-key": key},
            files={"file": (audio_path.name, f)},
            data=data,
            timeout=600,
        )

    # Always persist response for debugging
    try:
        payload = resp.json()
    except Exception:
        payload = {"raw": resp.text}

    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if resp.status_code >= 400:
        print(f"ERROR: HTTP {resp.status_code}: {payload}", file=sys.stderr)
        return 1

    # Minimal summary
    words = payload.get("words") or []
    speakers = sorted({w.get("speaker_id") for w in words if w.get("speaker_id")})
    print(f"OK: wrote {out_path} (words={len(words)}, speakers={len(speakers)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

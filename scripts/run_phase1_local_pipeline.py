#!/usr/bin/env python3
"""Run the documented Phase 1 local pipeline on Juggernaut.

This is the end-to-end local runner for one meeting:
1. normalize audio (assumes ingest already completed)
2. local WhisperX-first transcription in Docker
3. local diarization in Docker
4. build structured transcript JSON in repo
5. publish static site artifacts from structured transcript

Large artifacts stay under --work-root on Juggernaut.
Published/code artifacts stay in Git.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(str(x) for x in cmd), flush=True)
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def require_bin(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"Missing required binary: {name}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Phase 1 local pipeline for a meeting")
    ap.add_argument("meeting_id")
    ap.add_argument("--work-root", required=True, help="Juggernaut work root, outside Git")
    ap.add_argument("--hf-token-file", required=True, help="Path to Hugging Face token file for pyannote")
    ap.add_argument("--approvals", default="", help="Optional repo-relative or absolute approvals JSON")
    ap.add_argument("--whisperx-model", default="medium")
    ap.add_argument("--whisperx-language", default="en")
    ap.add_argument("--skip-normalize", action="store_true")
    ap.add_argument("--skip-publish", action="store_true")
    args = ap.parse_args()

    require_bin("docker")
    require_bin("python3")

    work_root = Path(args.work_root).resolve()
    meeting_dir = work_root / args.meeting_id
    audio_path = meeting_dir / "audio" / "audio_16k_mono.wav"
    asr_dir = meeting_dir / "asr"
    diar_dir = meeting_dir / "diarization"
    asr_dir.mkdir(parents=True, exist_ok=True)
    diar_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_normalize:
        run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "phase1_normalize_audio.py"),
                "--meeting-id",
                args.meeting_id,
                "--work-root",
                str(work_root),
            ],
            cwd=REPO_ROOT,
        )

    if not audio_path.exists():
        raise SystemExit(f"Missing normalized audio: {audio_path}")

    whisperx_json = asr_dir / "whisperx.json"
    run(
        [
            "docker",
            "run",
            "--rm",
            "--gpus",
            "all",
            "-v",
            f"{meeting_dir}:/work",
            "fairfax-whisperx:latest",
            str(audio_path),
            "--model",
            args.whisperx_model,
            "--language",
            args.whisperx_language,
            "--output_format",
            "json",
            "--output_dir",
            "/work/asr",
        ]
    )

    if not whisperx_json.exists():
        json_candidates = sorted(asr_dir.glob("*.json"))
        if not json_candidates:
            raise SystemExit(f"WhisperX did not produce JSON in {asr_dir}")
        produced = json_candidates[0]
        if produced != whisperx_json:
            produced.rename(whisperx_json)

    pyannote_json = diar_dir / "pyannote_segments.json"
    run(
        [
            "docker",
            "run",
            "--rm",
            "--gpus",
            "all",
            "-v",
            f"{meeting_dir}:/work",
            "-v",
            f"{Path(args.hf_token_file).resolve()}:/run/secrets/hf_token:ro",
            "-e",
            "HF_TOKEN_FILE=/run/secrets/hf_token",
            "fairfax-diarize-pyannote:latest",
            str(audio_path),
            "--out",
            "/work/diarization/pyannote_segments.json",
            "--token-file",
            "/run/secrets/hf_token",
        ]
    )

    approvals = args.approvals.strip()
    if approvals:
        approvals_path = Path(approvals)
        if not approvals_path.is_absolute():
            approvals_path = (REPO_ROOT / approvals_path).resolve()
    else:
        default_approvals = REPO_ROOT / "approvals" / f"{args.meeting_id}.json"
        approvals_path = default_approvals if default_approvals.exists() else None

    structured_dir = REPO_ROOT / "transcripts_structured"
    structured_dir.mkdir(parents=True, exist_ok=True)
    structured_json = structured_dir / f"{args.meeting_id}.json"

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "build_structured_transcript.py"),
        args.meeting_id,
        "--asr",
        str(whisperx_json),
        "--diarization",
        str(pyannote_json),
        "--out",
        str(structured_json),
    ]
    if approvals_path is not None and approvals_path.exists():
        cmd.extend(["--approvals", str(approvals_path)])
    run(cmd, cwd=REPO_ROOT)

    if not args.skip_publish:
        run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "publish_structured_meeting.py"),
                args.meeting_id,
                "--structured",
                str(structured_json),
            ],
            cwd=REPO_ROOT,
        )
        run([sys.executable, str(REPO_ROOT / "scripts" / "validate_site.py")], cwd=REPO_ROOT)

    print(f"structured={structured_json}")
    print(f"asr={whisperx_json}")
    print(f"diarization={pyannote_json}")
    print(f"audio={audio_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

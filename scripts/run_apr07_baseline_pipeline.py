#!/usr/bin/env python3
"""Run the locked baseline pipeline on apr-07-2026.

Orchestrates:
1. Download Granicus media
2. Normalize to 16k mono WAV
3. faster-whisper medium ASR
4. pyannote 3.1 diarization
5. Build structured transcript
6. Priority-tiered review queue (Tier 1 + Tier 2 only)

Usage:
  python3 scripts/run_apr07_pipeline.py \
    --work-root /mnt/disk1/fairfax-council-transcripts/pipeline/work \
    --token-file /mnt/disk1/fairfax-council-transcripts/pipeline/secrets/hf_token.txt
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SYSROOT = Path("/home/norrin302/.openclaw/workspace/fairfax-council-transcripts")
WORK_ROOT = Path("/mnt/disk1/fairfax-council-transcripts/pipeline/work")
TOKEN_FILE = "/mnt/disk1/fairfax-council-transcripts/pipeline/secrets/hf_token.txt"
MEETING_ID = "apr-07-2026"

def run(cmd, cwd=None, timeout=None, check=True):
    print(f"\n+ {' '.join(str(x) for x in cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, timeout=timeout, check=check,
                           capture_output=False)
    return result

def require_bin(name):
    r = subprocess.run(["bash", "-lc", f"command -v {name}"], capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"Missing required binary: {name}")

def stage(name):
    print(f"\n{'='*60}")
    print(f"STAGE: {name}")
    print(f"{'='*60}")

def main() -> int:
    ap = argparse.ArgumentParser(description=f"Run baseline pipeline on {MEETING_ID}")
    ap.add_argument("--work-root", default=str(WORK_ROOT))
    ap.add_argument("--token-file", default=TOKEN_FILE)
    ap.add_argument("--skip-normalize", action="store_true")
    ap.add_argument("--skip-asr", action="store_true")
    ap.add_argument("--skip-diarization", action="store_true")
    args = ap.parse_args()

    work_root = Path(args.work_root)
    meeting_dir = work_root / MEETING_ID
    audio_dir = meeting_dir / "audio"
    asr_dir = meeting_dir / "asr"
    diar_dir = meeting_dir / "diarization"
    merged_dir = meeting_dir / "merged"

    require_bin("yt-dlp")
    require_bin("ffmpeg")
    require_bin("docker")

    token_path = Path(args.token_file)
    if not token_path.exists():
        raise SystemExit(f"Token file not found: {token_path}")

    # ================================================================= ====
    # STAGE 1: Ingest
    # ================================================================= ====
    stage("1/5 — Ingest")
    t0 = time.time()
    media_dir = meeting_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    # Check if already ingested
    marker = meeting_dir / "ingest.json"
    if marker.exists():
        try:
            prev = json.loads(marker.read_text(encoding="utf-8"))
            fp = prev.get("filepath")
            if fp and Path(fp).exists() and Path(fp).stat().st_size > 1024 * 1024:
                print(f"Already ingested: {fp}")
        except Exception:
            pass
    else:
        cmd = [
            "python3", str(REPO_ROOT / "scripts" / "phase1_ingest.py"),
            "https://fairfax.granicus.com/player/clip/4513",
            "--meeting-id", MEETING_ID,
            "--work-root", str(work_root),
            "--format", "audio",
        ]
        run(cmd)

    print(f"  Ingest done in {time.time()-t0:.0f}s")

    # ================================================================= ====
    # STAGE 2: Normalize audio
    # ================================================================= ====
    stage("2/5 — Normalize audio")
    t0 = time.time()
    audio_dir.mkdir(parents=True, exist_ok=True)
    out_wav = audio_dir / "audio_16k_mono.wav"

    if args.skip_normalize and out_wav.exists() and out_wav.stat().st_size > 1024 * 1024:
        print(f"Skipping normalize (using existing {out_wav})")
    else:
        cmd = [
            "python3", str(REPO_ROOT / "scripts" / "phase1_normalize_audio.py"),
            "--meeting-id", MEETING_ID,
            "--work-root", str(work_root),
        ]
        run(cmd)
    print(f"  Audio: {out_wav} ({out_wav.stat().st_size // 1024 // 1024}MB)")
    print(f"  Normalize done in {time.time()-t0:.0f}s")

    # ================================================================= ====
    # STAGE 3: ASR (faster-whisper medium)
    # ================================================================= ====
    stage("3/5 — ASR (faster-whisper medium GPU)")
    t0 = time.time()
    asr_dir.mkdir(parents=True, exist_ok=True)
    asr_out = asr_dir / "faster-whisper_gpu_medium.json"

    if args.skip_asr and asr_out.exists():
        print(f"Skipping ASR (using existing {asr_out})")
    else:
        cmd = [
            "docker", "run", "--rm", "--gpus", "all",
            "-v", f"{work_root}:/work",
            "-w", f"/work/{MEETING_ID}",
            "--entrypoint", "python",
            "fairfax-pipeline-asr_faster_whisper",
            "-m", "src.transcribe_faster_whisper",
            "--audio", f"/work/{MEETING_ID}/audio/audio_16k_mono.wav",
            "--out", f"/work/{MEETING_ID}/asr/faster-whisper_gpu_medium.json",
            "--model", "medium",
            "--language", "en",
        ]
        run(cmd)
    print(f"  ASR done in {time.time()-t0:.0f}s")

    # ================================================================= ====
    # STAGE 4: Diarization (pyannote 3.1)
    # ================================================================= ====
    stage("4/5 — Diarization (pyannote 3.1)")
    t0 = time.time()
    diar_dir.mkdir(parents=True, exist_ok=True)
    diar_out = diar_dir / "pyannote_segments.json"

    if args.skip_diarization and diar_out.exists():
        print(f"Skipping diarization (using existing {diar_out})")
    else:
        cmd = [
            "docker", "run", "--rm", "--gpus", "all",
            "-v", f"{work_root}:/work",
            "-v", f"{token_path.parent}:/secrets:ro",
            "-e", "HF_HOME=/mnt/disk1/fairfax-council-transcripts/pipeline/cache/huggingface",
            "-e", f"HF_TOKEN_FILE=/secrets/{token_path.name}",
            "--entrypoint", "python",
            "fairfax-pipeline-diarize_pyannote",
            "-m", "src.diarize_pyannote",
            f"/work/{MEETING_ID}/audio/audio_16k_mono.wav",
            "--out", f"/work/{MEETING_ID}/diarization/pyannote_segments.json",
            "--token-file", f"/secrets/{token_path.name}",
        ]
        run(cmd)
    print(f"  Diarization done in {time.time()-t0:.0f}s")

    # ================================================================= ====
    # STAGE 5: Build structured transcript
    # ================================================================= ====
    stage("5/5 — Build structured transcript")
    t0 = time.time()
    struct_out = REPO_ROOT / "transcripts_structured" / f"{MEETING_ID}.json"
    struct_out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python3", str(REPO_ROOT / "scripts" / "build_structured_transcript.py"),
        MEETING_ID,
        "--asr", str(asr_dir / "faster-whisper_gpu_medium.json"),
        "--diarization", str(diar_dir / "pyannote_segments.json"),
        "--registry", str(REPO_ROOT / "speaker_registry" / "speakers.json"),
        "--out", str(struct_out),
    ]
    run(cmd)
    print(f"  Structured transcript: {struct_out}")
    print(f"  Build done in {time.time()-t0:.0f}s")

    # ================================================================= ====
    # STAGE 6: Build priority-tiered review queue (Tier 1 + Tier 2)
    # ================================================================= ====
    stage("6/6 — Build priority-tiered review queue")
    t0 = time.time()
    rq_out = REPO_ROOT / "reviews" / f"{MEETING_ID}-review-queue.json"

    cmd = [
        "python3", str(REPO_ROOT / "scripts" / "build_review_queue.py"),
        MEETING_ID,
        "--structured", str(struct_out),
        "--out", str(rq_out),
        "--context", "2",
    ]
    run(cmd)
    print(f"  Review queue: {rq_out}")

    # Parse tier summary
    rq = json.loads(rq_out.read_text(encoding="utf-8"))
    tier_sum = rq.get("tier_summary", {})
    print(f"\n  TIER SUMMARY:")
    print(f"    Tier 1 (high risk): {tier_sum.get('tier_1_high_risk', '?')}")
    print(f"    Tier 2 (medium):    {tier_sum.get('tier_2_medium_risk', '?')}")
    print(f"    Tier 3 (low):       {tier_sum.get('tier_3_low_risk', '?')}")
    print(f"  Review queue done in {time.time()-t0:.0f}s")

    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE: {MEETING_ID}")
    print(f"{'='*60}")
    print(f"  Structured transcript: {struct_out}")
    print(f"  Review queue: {rq_out}")
    print(f"  Diarization: {diar_out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

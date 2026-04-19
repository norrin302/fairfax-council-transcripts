from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .utils import write_json, norm_ws


def main() -> int:
    ap = argparse.ArgumentParser(description="Transcribe using faster-whisper")
    ap.add_argument("audio", help="Path to 16k mono wav")
    ap.add_argument("--out", default="asr/faster-whisper.json")
    ap.add_argument("--model", default="medium")
    ap.add_argument("--language", default="en")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--compute-type", default="float16")
    ap.add_argument("--beam-size", type=int, default=5)
    args = ap.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        raise SystemExit(f"Missing audio: {audio_path}")

    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception as e:
        raise SystemExit(
            "Missing faster-whisper in this image. "
            "If you are building locally, ensure the base image provides faster-whisper. "
            f"Import error: {e}"
        )

    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)

    segments_iter, info = model.transcribe(
        str(audio_path),
        language=None if args.language == "auto" else args.language,
        beam_size=args.beam_size,
        word_timestamps=True,
        vad_filter=True,
    )

    segments: list[dict[str, Any]] = []
    words: list[dict[str, Any]] = []
    for seg in segments_iter:
        s = {
            "start": float(seg.start),
            "end": float(seg.end),
            "text": norm_ws(seg.text),
        }
        if getattr(seg, "words", None):
            s_words = []
            for w in seg.words:
                if w is None:
                    continue
                s_words.append({"start": float(w.start), "end": float(w.end), "word": str(w.word)})
                words.append({"start": float(w.start), "end": float(w.end), "word": str(w.word)})
            s["words"] = s_words
        segments.append(s)

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = Path.cwd() / out_path

    write_json(
        out_path,
        {
            "audio": str(audio_path),
            "model": args.model,
            "language": getattr(info, "language", None),
            "duration": getattr(info, "duration", None),
            "segments": segments,
            "words": words,
        },
    )

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


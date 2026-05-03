# Fairfax transcripts pipeline (Docker, low-cost)

This directory will hold the reproducible, Docker-based pipeline for:

- audio prep (download + normalize)
- transcription (faster-whisper baseline, WhisperX optional)
- diarization (pyannote)
- merge (transcript + diarization)
- safe identification (speaker registry + conservative confidence thresholds)
- correction workflow (deterministic rebuild without editing generated HTML)

Notes:
- GPU transcription requires NVIDIA Container Toolkit on the host. The ASR image installs CUDA BLAS (libcublas) at build-time to avoid runtime failures.

Status: under active development.

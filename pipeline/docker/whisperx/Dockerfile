FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir -U pip \
    && python -m pip install --no-cache-dir whisperx

WORKDIR /work

ENTRYPOINT ["python", "-m", "whisperx"]

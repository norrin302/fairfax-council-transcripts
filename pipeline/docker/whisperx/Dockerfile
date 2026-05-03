FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir -U pip \
    && python -m pip install --no-cache-dir whisperx

WORKDIR /work

ENTRYPOINT ["python", "-m", "whisperx"]

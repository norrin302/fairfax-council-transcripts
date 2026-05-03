FROM python:3.12-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir -U pip \
  && python -m pip install --no-cache-dir yt-dlp

COPY src /app/src

ENV PYTHONPATH=/app

ENTRYPOINT ["python", "-m", "src.prep_audio"]

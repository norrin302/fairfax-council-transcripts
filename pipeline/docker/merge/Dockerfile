FROM python:3.12-slim

RUN python -m pip install --no-cache-dir -U pip

WORKDIR /work

COPY src /app/src

ENV PYTHONPATH=/app

ENTRYPOINT ["python", "-m", "src.merge_transcript"]

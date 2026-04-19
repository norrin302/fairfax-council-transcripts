ARG BASE_IMAGE=lscr.io/linuxserver/faster-whisper:gpu
FROM ${BASE_IMAGE}

# LinuxServer images are not guaranteed to have pip tooling exposed as in standard python images.
# We keep our runtime minimal and rely on the base image's faster-whisper install.

WORKDIR /work

COPY src /app/src

ENV PYTHONPATH=/app

ENTRYPOINT ["python3", "-m", "src.transcribe_faster_whisper"]

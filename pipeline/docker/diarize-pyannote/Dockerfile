FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN python -m pip install --no-cache-dir -U pip \
  && python -m pip install --no-cache-dir "pyannote.audio>=3.1,<4" soundfile \
  && python -m pip install --no-cache-dir "huggingface_hub==0.20.3"

WORKDIR /work

COPY src /app/src

ENV PYTHONPATH=/app

ENTRYPOINT ["python", "-m", "src.diarize_pyannote"]

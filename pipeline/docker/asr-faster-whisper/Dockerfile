ARG BASE_IMAGE=lscr.io/linuxserver/faster-whisper:gpu
FROM ${BASE_IMAGE}

# LinuxServer images ship faster-whisper, but some variants do not include CUDA BLAS
# libraries (e.g. libcublas.so.12). Without these, `--device cuda` will fail at
# runtime. We install the CUDA BLAS runtime via NVIDIA's pip wheels and register
# its lib directory with the dynamic linker.

RUN python3 -m pip install --no-cache-dir -U pip \
  && python3 -m pip install --no-cache-dir nvidia-cublas-cu12 \
  && CUBLAS_LIB="$(python3 -c 'import pathlib, nvidia.cublas; print((pathlib.Path(nvidia.cublas.__file__).resolve().parent / "lib"))')" \
  && echo "$CUBLAS_LIB" > /etc/ld.so.conf.d/nvidia-cublas.conf \
  && ldconfig

WORKDIR /work

COPY src /app/src

ENV PYTHONPATH=/app

ENTRYPOINT ["python3", "-m", "src.transcribe_faster_whisper"]

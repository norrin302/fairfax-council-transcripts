#!/usr/bin/env python3
"""Test what pyannote.audio exposes for embedding extraction.

Run inside the diarize-pyannote container:
  docker run --rm -it --gpus all \
    -v /mnt/disk1/fairfax-council-transcripts:/data \
    -v $HF_TOKEN_FILE:/run/secrets/hf_token:ro \
    fairfax-pipeline-diarize_pyannote \
    python /app/src/test_pyannote_embeddings.py
"""

from __future__ import annotations

import sys
import json

print("=== pyannote.audio version ===")
import pyannote.audio
print(f"Version: {pyannote.audio.__version__}")

print("\n=== Model.from_pretrained ===")
from pyannote.audio import Model
try:
    model = Model.from_pretrained("pyannote/segmentation-3.0")
    print(f"Model loaded: {type(model).__name__}")
    print(f"  device: {next(model.parameters()).device}")
except Exception as e:
    print(f"Failed: {e}")
    sys.exit(1)

print("\n=== Checking for embedding/pipeline attributes ===")
attrs = [a for a in dir(model) if 'embed' in a.lower() or 'voice' in a.lower()]
print(f"  Embedding-related attrs: {attrs}")

print("\n=== Checking Pipeline ===")
from pyannote.audio import Pipeline
print(f"  Pipeline class: {Pipeline}")

print("\n=== Checking VoicePrintDetection ===")
try:
    from pyannote.audio.pipelines.speaker_verification import VoicePrintDetection
    print(f"  VoicePrintDetection available: True")
except ImportError as e:
    print(f"  VoicePrintDetection NOT available: {e}")

print("\n=== Test embedding extraction for a short audio clip ===")
try:
    from pyannote.audio.pipelines.speaker_verification import (
        VoicePrintDetection, RESTRICTED_SEGMENT_DURATION
    )
    import torch
    
    pipeline_vpd = VoicePrintDetection(segmentation=model)
    print(f"  VoicePrintDetection pipeline created")
    print(f"  RESTRICTED_SEGMENT_DURATION: {RESTRICTED_SEGMENT_DURATION}")
    
    # Test on a small audio file
    test_audio = "/data/pipeline/work/apr-14-2026/audio/prepared/apr-14-2026_mono.wav"
    import os
    if os.path.exists(test_audio):
        from pyannote.core import Segment
        import soundfile as sf
        
        # Get first 10 seconds
        y, sr = sf.read(test_audio, dtype="float32")
        y_10s = y[:sr * 10]
        
        seg = Segment(start=0.0, end=10.0)
        
        # Run voice print detection
        result = pipeline_vpd({"audio": (y_10s, sr), "duration": 10.0})
        print(f"  VoicePrintDetection result keys: {result.keys() if hasattr(result, 'keys') else type(result)}")
        print(f"  Result: {result}")
    else:
        print(f"  Test audio not found: {test_audio}")
        
except Exception as e:
    print(f"  Embedding extraction test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test: can we get per-segment embeddings from pyannote Pipeline output? ===")
print("NOTE: The standard pyannote Pipeline diarization output does NOT include embeddings.")
print("We need to run a separate embedding extraction pass.")
print("Strategy: extract per-segment embeddings after diarization using the embedding model.")

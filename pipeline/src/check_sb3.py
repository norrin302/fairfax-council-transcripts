#!/usr/bin/env python3
"""Test SpeechBrainPretrainedSpeakerEmbedding extraction using HF_TOKEN env var."""
import sys
sys.path.insert(0, '/app')

import os
import soundfile as sf
import numpy as np

# Get HF token from env
hf_token = os.environ.get("HF_TOKEN", "")
hf_token_file = os.environ.get("HF_TOKEN_FILE", "")

print("HF_TOKEN env var set:", bool(hf_token))
print("HF_TOKEN_FILE env var set:", bool(hf_token_file))

from pyannote.audio.pipelines.speaker_verification import (
    SpeechBrainPretrainedSpeakerEmbedding
)

print("\n=== Load embedding model (no use_auth_token) ===")
try:
    emb = SpeechBrainPretrainedSpeakerEmbedding("speechbrain/spkrec-ecapa-voxceleb")
    print("Loaded OK")
    print("  dimension: " + str(emb.dimension))
except Exception as e:
    print("Failed to load: " + str(e))

print("\n=== Test embedding on real audio ===")
audio_path = "/mnt/disk1/fairfax-council-transcripts/pipeline/work/apr-14-2026/audio/audio_16k_mono.wav"
if os.path.exists(audio_path):
    y, sr = sf.read(audio_path, dtype="float32", start=0, stop=30*sr)
    print("Audio: {:.1f}s at {}Hz".format(len(y)/sr, sr))
    y_3d = y.reshape(1, -1)  # (batch=1, samples)
    try:
        result = emb(y_3d)
        print("Result shape: " + str(result.shape))
    except Exception as e:
        print("Embedding failed: " + str(e))
else:
    print("Audio not found: " + audio_path)

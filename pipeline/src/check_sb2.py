#!/usr/bin/env python3
"""Test SpeechBrainPretrainedSpeakerEmbedding without use_auth_token."""
import sys
sys.path.insert(0, '/app')

from pyannote.audio.pipelines.speaker_verification import (
    SpeechBrainPretrainedSpeakerEmbedding
)
import numpy as np
import soundfile as sf
import torch

print("=== Load embedding model ===")
try:
    emb = SpeechBrainPretrainedSpeakerEmbedding("speechbrain/spkrec-ecapa-voxceleb")
    print("Loaded: " + type(emb).__name__)
    print("  dimension: " + str(emb.dimension))
    print("  sample_rate: " + str(emb.sample_rate))
    print("  min_samples: " + str(emb.min_num_samples))
except Exception as e:
    print("Failed to load: " + str(e))

print("\n=== Test embedding extraction on synthetic audio ===")
try:
    # Generate a short synthetic sine wave (not real speech, but tests the interface)
    sr = 16000
    t = np.linspace(0, 1.0, sr)
    # 440 Hz sine wave
    audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    audio = audio.reshape(1, -1)  # (batch, samples)

    result = emb(audio)
    print("Embedding result type: " + type(result).__name__)
    print("Embedding shape: " + str(result.shape))
    print("Embedding dim: " + str(result.shape[-1]))
except Exception as e:
    print("Embedding test failed: " + str(e))
    import traceback
    traceback.print_exc()

print("\n=== Test on real audio ===")
try:
    # Real audio path from the apr-14-2026 meeting
    audio_path = "/mnt/disk1/fairfax-council-transcripts/pipeline/work/apr-14-2026/audio/audio_16k_mono.wav"
    import os
    if os.path.exists(audio_path):
        y, sr = sf.read(audio_path, dtype="float32", start=0, stop=30*sr)
        print("Audio loaded: {:.1f}s".format(len(y)/sr))
        # Reshape for batch processing
        y_batch = y.reshape(1, -1)
        result = emb(y_batch)
        print("Embedding shape: " + str(result.shape))
    else:
        print("Real audio not found at: " + audio_path)
except Exception as e:
    print("Real audio test failed: " + str(e))
    import traceback
    traceback.print_exc()

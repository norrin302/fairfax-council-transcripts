#!/usr/bin/env python3
"""Test SpeechBrainPretrainedSpeakerEmbedding with correct API."""
import sys
sys.path.insert(0, '/app')

from pyannote.audio.pipelines.speaker_verification import (
    SpeechBrainPretrainedSpeakerEmbedding
)
import torch
import inspect

print("=== Test SpeechBrainPretrainedSpeakerEmbedding ===")
try:
    emb = SpeechBrainPretrainedSpeakerEmbedding("speechbrain/spkrec-ecapa-voxceleb")
    print("Loaded: " + type(emb).__name__)
    print("  dimension: " + str(emb.dimension))
    print("  sample_rate: " + str(emb.sample_rate))
    print("  min_samples: " + str(emb.min_num_samples))
except Exception as e:
    print("Failed: " + str(e))

print("\n=== Signature ===")
try:
    sig = inspect.signature(SpeechBrainPretrainedSpeakerEmbedding.__init__)
    print("Signature: " + str(sig))
except Exception as e:
    print("Could not get signature: " + str(e))

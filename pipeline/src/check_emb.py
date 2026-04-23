#!/usr/bin/env python3
"""Inspect SpeakerEmbedding interface for embedding extraction."""
import sys
sys.path.insert(0, '/app')

from pyannote.audio.pipelines.speaker_verification import (
    SpeakerEmbedding, SpeechBrainPretrainedSpeakerEmbedding
)

print("=== SpeakerEmbedding ===")
print(type(SpeakerEmbedding))
print(dir(SpeakerEmbedding))

print("\n=== SpeechBrainPretrainedSpeakerEmbedding ===")
print(type(SpeechBrainPretrainedSpeakerEmbedding))
print(dir(SpeechBrainPretrainedSpeakerEmbedding))

# Try to instantiate and check available models
print("\n=== Check available models ===")
try:
    emb = SpeechBrainPretrainedSpeakerEmbedding(
        source="speechbrain/spkrec-ecapa-voxceleb",
        device="cpu"
    )
    print(f"SpeechBrainPretrainedSpeakerEmbedding created")
    print(f"  Input: {emb.hours}")
except Exception as e:
    print(f"SpeechBrainPretrainedSpeakerEmbedding failed: {e}")

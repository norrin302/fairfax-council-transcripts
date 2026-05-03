#!/usr/bin/env python3
"""Test SpeakerEmbedding.from_pretrained for ECAPA-TDNN model."""
import sys
sys.path.insert(0, '/app')

from pyannote.audio.pipelines.speaker_verification import (
    SpeakerEmbedding, SpeechBrainPretrainedSpeakerEmbedding
)
import torch

print("=== Test SpeakerEmbedding.from_pretrained ===")
try:
    emb = SpeakerEmbedding.from_pretrained(
        "speechbrain/spkrec-ecapa-voxceleb",
        device="cpu"
    )
    print(f"SpeakerEmbedding loaded: {type(emb).__name__}")
    print(f"  dimension: {emb.dimension}")
    print(f"  sample_rate: {emb.sample_rate}")
    print(f"  min_samples: {emb.min_num_samples}")
except Exception as e:
    print(f"SpeakerEmbedding.from_pretrained failed: {e}")

print("\n=== Test PyannoteAudioPretrainedSpeakerEmbedding ===")
try:
    from pyannote.audio.pipelines.speaker_verification import (
        PyannoteAudioPretrainedSpeakerEmbedding
    )
    emb2 = PyannoteAudioPretrainedSpeakerEmbedding(
        "pyannote/segmentation-3.0",
        device="cpu"
    )
    print(f"PyannoteAudioPretrainedSpeakerEmbedding loaded: {type(emb2).__name__}")
    print(f"  dimension: {emb2.dimension}")
except Exception as e:
    print(f"PyannoteAudioPretrainedSpeakerEmbedding failed: {e}")

print("\n=== GPU check ===")
try:
    import torch
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
except Exception as e:
    print(f"GPU check failed: {e}")

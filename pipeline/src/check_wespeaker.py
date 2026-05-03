#!/usr/bin/env python3
"""Test pyannote.wespeaker embedding extraction on real audio."""
import sys
sys.path.insert(0, '/app')

import os
import soundfile as sf
import numpy as np

print("=== Test PyannoteAudioPretrainedSpeakerEmbedding ===")
try:
    from pyannote.audio.pipelines.speaker_verification import (
        PyannoteAudioPretrainedSpeakerEmbedding
    )
    emb = PyannoteAudioPretrainedSpeakerEmbedding(
        "pyannote/wespeaker-voxceleb-resnet34-LM"
    )
    print("Loaded OK")
    print("  dimension: " + str(emb.dimension))
    print("  sample_rate: " + str(emb.sample_rate))
except Exception as e:
    print("Failed to load PyannoteAudio: " + str(e))

print("\n=== Test embedding on real audio ===")
audio_path = "/mnt/disk1/fairfax-council-transcripts/pipeline/work/apr-14-2026/audio/audio_16k_mono.wav"
if os.path.exists(audio_path):
    y, sr = sf.read(audio_path, dtype="float32", start=0, stop=30 * sr)
    print("Audio: {:.1f}s at {}Hz".format(len(y)/float(sr), sr))
    y_3d = y.reshape(1, -1)
    try:
        result = emb(y_3d)
        print("Result shape: " + str(result.shape))
        print("Result type: " + str(type(result).__name__))
    except Exception as e:
        print("Embedding failed: " + str(e))
        import traceback
        traceback.print_exc()
else:
    print("Audio not found: " + audio_path)

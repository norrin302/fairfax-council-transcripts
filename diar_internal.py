#!/usr/bin/env python3
"""Bypass broken pyannote.io AudioDecoder by calling internal methods directly with waveforms."""
import warnings, os, torch, json
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from huggingface_hub import login
login('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')

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel
from pyannote.audio import Model, Pipeline
import pyannote.audio.core.io as audio_io

print("=== Step 1: Load models ===")
device = torch.device('cpu')

# Segmentation model for VAD + speaker embedding
seg_model = Model.from_pretrained('pyannote/segmentation-3.0')
seg_model.to(device)
seg_model.eval()
print(f"Segmentation model loaded")

# Diarization pipeline (we'll call its internal methods, not apply())
p = Pipeline.from_pretrained('pyannote/speaker-diarization-3.1')
p.to(device)
print(f"Diarization pipeline loaded")

whisper_model = WhisperModel('small', device='cpu', compute_type='int8')
print(f"Whisper model loaded")

# Patch AudioDecoder in the module so nothing breaks if some code path still references it
class _FakeDecoder:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Should not be called")
audio_io.AudioDecoder = _FakeDecoder

print("\n=== Step 2: Patch internal pipeline methods ===")

# The pipeline's _segmentation and get_embeddings work with waveform dicts.
# The key issue is that Pipeline.apply() -> get_segmentations() -> _segmentation() -> 
# model.audio(file) which calls Audio.__call__ which tries AudioDecoder.
# 
# Instead, we'll call _segmentation and get_embeddings directly with waveform dict.
# These are the only methods we actually need.

# Verify _segmentation accepts waveform dict
print("Testing _segmentation with waveform dict...")
data, sr = sf.read('/tmp/test_clip.wav')
waveform = torch.from_numpy(data.astype(np.float32)/32768.0).unsqueeze(0)
waveform_dict = {'waveform': waveform, 'sample_rate': sr}

try:
    segs = p._segmentation(waveform_dict)
    print(f"  _segmentation OK: {type(segs)}")
except Exception as e:
    print(f"  _segmentation FAILED: {e}")

# The pipeline's get_embeddings needs binary_segmentations. Let's look at what to_diarization needs.
# to_diarization(segmentations, embeddings) -> Annotation
# We need: segmentations (from _segmentation) + embeddings (from get_embeddings)

# Try get_embeddings with a dummy segmentation
print("Testing get_embeddings with waveform dict...")
try:
    embs = p.get_embeddings(waveform_dict)
    print(f"  get_embeddings OK: {embs.shape}")
except Exception as e:
    print(f"  get_embeddings FAILED: {e}")

# Try to_diarization
print("Testing to_diarization...")
try:
    dia = p.to_diarization(segs, embs)
    print(f"  to_diarization OK: {len(dia)} tracks")
    for turn, _, speaker in dia.itertracks(yield_label=True):
        print(f"    {turn.start:.2f}-{turn.end:.2f}s: {speaker}")
except Exception as e:
    print(f"  to_diarization FAILED: {e}")
    import traceback; traceback.print_exc()
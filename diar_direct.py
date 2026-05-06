#!/usr/bin/env python3
"""Bypass broken pyannote.io AudioDecoder by calling models directly with waveform."""
import warnings, os, torch, json
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from huggingface_hub import login
login('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')

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel
from pyannote.audio import Model, Pipeline
from pyannote.core import Segment, Annotation

print("=== Step 1: Load models ===")
device = torch.device('cpu')

# Segmentation model
seg_model = Model.from_pretrained('pyannote/segmentation-3.0')
seg_model.to(device)
seg_model.eval()
print(f"Segmentation model loaded")

whisper_model = WhisperModel('small', device='cpu', compute_type='int8')
print(f"Whisper model loaded")

# Load test clip
data, sr = sf.read('/tmp/test_clip.wav')
waveform = torch.from_numpy(data.astype(np.float32)/32768.0).unsqueeze(0).unsqueeze(0)  # (1,1,samples)
print(f"Audio: {data.shape}, sr={sr}, dur={data.shape[0]/sr:.1f}s")

# Run segmentation
print("\n=== Step 2: Segmentation ===")
with torch.no_grad():
    seg_out = seg_model(waveform)  # (1, frames, 7) - raw logits
probs = torch.sigmoid(seg_out).squeeze(0).numpy()  # (frames, 7)
print(f"Seg output: {seg_out.shape}, probs: {probs.shape}")
print(f"Mean prob/speaker: {probs.mean(axis=0).round(4)}")

# Check sliding window params
# Each frame covers ~10ms (from segmentation_3.0 default)
# With 16000 sr and small model, step is probably 10ms = 160 samples
step = 0.01  # 10ms
# Total frames = samples/sr/step = 960000/16000/0.01 = 6000 frames
num_frames = probs.shape[0]
print(f"Frames: {num_frames}, step: {step}s, duration: {num_frames * step:.1f}s")

# For each frame, find which speakers are active (prob > threshold)
THRESH = 0.5
active = probs > THRESH  # (frames, 7)
print(f"\nActive frames per speaker: {active.sum(axis=0)}")

# Convert frames to time segments
# Build segments: (start_frame, end_frame, speaker_id)
speaker_segments = []
for spk in range(7):
    spk_active = active[:, spk]
    if spk_active.sum() == 0:
        continue
    # Find contiguous regions
    in_seg = False
    start_frame = None
    for f in range(len(spk_active)):
        if spk_active[f] and not in_seg:
            start_frame = f
            in_seg = True
        elif not spk_active[f] and in_seg:
            seg = Segment(start=start_frame * step, end=f * step)
            speaker_segments.append((seg, spk))
            in_seg = False
    if in_seg:
        seg = Segment(start=start_frame * step, end=len(spk_active) * step)
        speaker_segments.append((seg, spk))

print(f"\nRaw segments: {len(speaker_segments)}")
for seg, spk in speaker_segments[:5]:
    print(f"  {seg.start:.2f}-{seg.end:.2f}s: SPEAKER_{spk}")
print("  ...")

# Build Annotation
dia = Annotation()
for seg, spk in speaker_segments:
    dia[seg] = f'SPEAKER_{spk}'

print(f"\n=== Diarization result: {len(dia)} tracks ===")
for turn, _, speaker in dia.itertracks(yield_label=True):
    print(f"  {turn.start:.2f}-{turn.end:.2f}s: {speaker}")
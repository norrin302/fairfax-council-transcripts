#!/usr/bin/env python3
"""
Full diarization + transcription pipeline for apr-14-2026 Fairfax city council meeting.
Patches pyannote.audio.core.io to use soundfile instead of the broken torchcodec AudioDecoder.
"""
import warnings, os, sys, json, subprocess
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from huggingface_hub import login
login('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')

import torch
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline

print("=== Step 1: Patch pyannote audio IO ===")
# Fix pyannote.audio.core.io to use soundfile instead of broken torchcodec AudioDecoder
import pyannote.audio.core.io as audio_io

# We need to create a fake AudioDecoder class that wraps soundfile
class _SoundfileMetadata:
    def __init__(self, info):
        self.sample_rate = info.samplerate
        self.num_channels = info.channels
        self.num_samples = int(info.duration * info.samplerate)
        self.duration = info.duration

class _SoundfileDecoder:
    def __init__(self, file_path):
        self.path = str(file_path)
        self._info = None
    
    @property
    def metadata(self):
        if self._info is None:
            self._info = _SoundfileMetadata(sf.info(self.path))
        return self._info
    
    def get_all_samples(self):
        X, sr = sf.read(self.path, dtype='float32')
        if X.ndim > 1:
            X = X.mean(axis=1)
        import torch
        return _SoundfileAudioSamples(torch.from_numpy(X).unsqueeze(0), sr)

class _SoundfileAudioSamples:
    def __init__(self, data, sample_rate):
        self.data = data  # (1, samples)
        self.sample_rate = sample_rate

# Monkey-patch the module-level AudioDecoder reference
audio_io.AudioDecoder = _SoundfileDecoder

# Also patch get_audio_metadata to handle string paths directly
_original_get_audio_metadata = audio_io.get_audio_metadata
def _patched_get_audio_metadata(file):
    if isinstance(file, str) or hasattr(file, '__fspath__'):
        info = sf.info(file)
        return _SoundfileMetadata(info)
    elif isinstance(file, dict) and 'audio' in file:
        info = sf.info(file['audio'])
        return _SoundfileMetadata(info)
    elif isinstance(file, dict) and 'waveform' in file:
        from pyannote.audio.core.io import Audio
        sr = file['sample_rate']
        num = file['waveform'].shape[-1]
        class _FakeMeta:
            sample_rate = sr
            num_channels = file['waveform'].shape[0]
            num_samples = num
            duration = num / sr
        return _FakeMeta()
    return _original_get_audio_metadata(file)

audio_io.get_audio_metadata = _patched_get_audio_metadata

print("  Patched io.py to use soundfile")

print("\n=== Step 2: Load models ===")
device = torch.device('cpu')

p = Pipeline.from_pretrained('pyannote/speaker-diarization-3.1')
p.to(device)
print(f"  Diarization pipeline loaded")

whisper_model = WhisperModel('small', device='cpu', compute_type='int8')
print(f"  Whisper model loaded")

print("\n=== Step 3: Process audio in chunks ===")
AUDIO_FILE = '/home/norrin302/.openclaw/workspace/apr14_meeting.mp3'
CHUNK_DURATION = 300  # 5 minutes per chunk

FFMPEG = '/tmp/ffmpeg-7.0.2-amd64-static/ffmpeg'

# Get total duration using ffmpeg
result = subprocess.run([FFMPEG, '-i', AUDIO_FILE], capture_output=True, text=True)
import re
dur_match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', result.stderr)
total_duration = int(dur_match.group(1))*3600 + int(dur_match.group(2))*60 + float(dur_match.group(3))
print(f"  Total duration: {total_duration:.0f}s ({total_duration/3600:.1f}h)")

# Process each 5-minute chunk
chunk_results = []
chunk_idx = 0

for chunk_start in range(0, int(total_duration), CHUNK_DURATION):
    chunk_end = min(chunk_start + CHUNK_DURATION, total_duration)
    chunk_dur = chunk_end - chunk_start
    
    print(f"\n--- Chunk {chunk_idx+1}: {chunk_start:.0f}s - {chunk_end:.0f}s ({chunk_dur:.0f}s) ---")
    
    chunk_path = f'/tmp/meeting_chunk_{chunk_idx:03d}.wav'
    
    # Extract chunk using ffmpeg (largest disk I/O step)
    if not os.path.exists(chunk_path):
        cmd = [
            FFMPEG, '-y', '-i', AUDIO_FILE,
            '-ss', str(chunk_start), '-t', str(chunk_dur),
            '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le',
            chunk_path
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  FFmpeg error: {r.stderr[-300:]}")
            continue
        print(f"  Extracted chunk ({os.path.getsize(chunk_path)//1024//1024}MB)")
    else:
        print(f"  Using cached chunk")
    
    # Transcribe with Whisper
    print(f"  Transcribing...")
    segments, info = whisper_model.transcribe(chunk_path, language='en', vad_filter=True)
    whisper_segments = []
    for seg in segments:
        ws = seg.start + chunk_start
        we = seg.end + chunk_start
        text = seg.text.strip()
        if text:
            whisper_segments.append({'start': ws, 'end': we, 'text': text})
    print(f"  Whisper: {len(whisper_segments)} speech segments")
    
    # Diarize with pyannote
    print(f"  Diarizing...")
    try:
        diar_result = p(chunk_path, max_speakers=10)
        dia = diar_result.speaker_diarization
    except Exception as e:
        print(f"  Diarization error: {e}")
        dia = None
    
    if dia:
        print(f"  Diarization: {len(dia)} tracks")
        for turn, _, speaker in dia.itertracks(yield_label=True):
            ds = turn.start + chunk_start
            de = turn.end + chunk_start
            chunk_results.append({
                'start': ds, 'end': de, 'speaker': speaker,
                'whisper_segments': [w for w in whisper_segments 
                                    if w['start'] < de and w['end'] > ds]
            })
    else:
        # No diarization - just use whisper segments without speaker info
        for wseg in whisper_segments:
            chunk_results.append({
                'start': wseg['start'], 'end': wseg['end'],
                'speaker': 'UNKNOWN',
                'whisper_segments': [wseg]
            })
    
    chunk_idx += 1

print(f"\n=== Step 4: Save results ===")
output = {
    'total_duration': total_duration,
    'num_chunks': chunk_idx,
    'segments': chunk_results
}
with open('/home/norrin302/.openclaw/workspace/diar_results.json', 'w') as f:
    json.dump(output, f, indent=2)
print(f"Saved {len(chunk_results)} segments to diar_results.json")
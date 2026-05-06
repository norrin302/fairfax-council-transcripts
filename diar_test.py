#!/usr/bin/env python3
"""Full diarization pipeline for apr-14-2026 meeting using pyannote + whisper.
Bypasses the AudioDecoder issue by calling internal methods with waveform dict.
"""
import warnings, os, torch, json
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from huggingface_hub import login
login('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')

from pyannote.audio import Model, Pipeline
import torch
import numpy as np
import soundfile as sf
from scipy.io import wavfile
from faster_whisper import WhisperModel
from pyannote.core import Segment, Annotation

print("=== Step 1: Load models ===")
device = torch.device('cpu')

# Load the segmentation model separately
seg_model = Model.from_pretrained('pyannote/segmentation-3.0')
seg_model.to(device)
seg_model.eval()
print(f"Segmentation model loaded")

# Load the full diarization pipeline (won't use its apply method)
p = Pipeline.from_pretrained('pyannote/speaker-diarization-3.1')
p.to(device)
print(f"Diarization pipeline loaded")

whisper_model = WhisperModel('small', device='cpu', compute_type='int8')
print(f"Whisper model loaded")

print("\n=== Step 2: Test with waveform dict ===")
data, sr = sf.read('/tmp/test_clip.wav')
waveform = torch.from_numpy(data.astype(np.float32) / 32768.0).unsqueeze(0)  # (1, samples)
waveform_dict = {'waveform': waveform, 'sample_rate': sr}

# Check if get_segmentations works with waveform dict
try:
    segs = p.get_segmentations(waveform_dict)
    print(f"get_segmentations: OK, {segs.nb_features} features, dimension={segs.dimension}")
except Exception as e:
    print(f"get_segmentations FAILED: {e}")
    print("Trying alternative approach...")

# Try calling _segmentation directly 
try:
    segs = p._segmentation(waveform_dict)
    print(f"_segmentation: OK, type={type(segs)}")
except Exception as e:
    print(f"_segmentation FAILED: {e}")

# Let's try the apply method - intercept AudioDecoder
print("\n=== Step 3: Patch AudioDecoder ===")
# Patch AudioDecoder in the io module
import pyannote.audio.core.io as audio_io

original_audiodecoder = None

def patched_audiodecoder_init(self, file):
    # Just set a dummy metadata
    from pyannote.audio.core.io import AudioStreamMetadata
    if isinstance(file, dict) and 'waveform' in file:
        raise NotImplementedError("Should not reach here")
    # For file paths
    info = sf.info(file)
    from pyannote.audio.core.io import AudioStreamMetadata
    self.metadata = AudioStreamMetadata(
        sample_rate=info.samplerate,
        num_channels=info.channels,
        num_samples=int(info.duration * info.samplerate),
        duration=info.duration,
    )

# Actually let's just patch the io module's AudioDecoder
try:
    from torchcodec.decoders import AudioDecoder, AudioStreamMetadata
    print("torchcodec AudioDecoder available")
except ImportError:
    print("torchcodec AudioDecoder NOT available")

# Check what AudioDecoder is in the io module
print(f"AudioDecoder in io: {audio_io.AudioDecoder if hasattr(audio_io, 'AudioDecoder') else 'NOT FOUND'}")

# Let's just try the direct pipeline approach with wav files
print("\n=== Step 4: Run pipeline on wav file with patched Audio ===")
from pyannote.audio.core.io import Audio

# Save waveform dict to wav
sf.write('/tmp/test_waveform.wav', data, sr)

# Patch Audio to handle string paths using soundfile
original_get_duration = Audio.get_duration
original_get_audio_metadata = audio_io.get_audio_metadata

def patched_get_duration(self, file):
    if isinstance(file, dict) and 'waveform' in file:
        return file['waveform'].shape[-1] / file['sample_rate']
    elif isinstance(file, (str, os.PathLike)):
        info = sf.info(file)
        return info.duration
    elif isinstance(file, dict) and 'audio' in file:
        info = sf.info(file['audio'])
        return info.duration
    return original_get_duration(self, file)

def patched_get_audio_metadata(file):
    if isinstance(file, dict) and 'waveform' in file:
        from pyannote.audio.core.io import AudioStreamMetadata
        sr = file['sample_rate']
        num = file['waveform'].shape[-1]
        return AudioStreamMetadata(sample_rate=sr, num_channels=file['waveform'].shape[0],
                                  num_samples=num, duration=num/sr)
    elif isinstance(file, (str, os.PathLike)):
        info = sf.info(file)
        from pyannote.audio.core.io import AudioStreamMetadata
        return AudioStreamMetadata(sample_rate=info.samplerate, num_channels=info.channels,
                                  num_samples=int(info.duration*info.samplerate), duration=info.duration)
    elif isinstance(file, dict) and 'audio' in file:
        info = sf.info(file['audio'])
        from pyannote.audio.core.io import AudioStreamMetadata
        return AudioStreamMetadata(sample_rate=info.samplerate, num_channels=info.channels,
                                  num_samples=int(info.duration*info.samplerate), duration=info.duration)
    raise NotImplementedError(f"Unsupported: {type(file)}")

Audio.get_duration = patched_get_duration
audio_io.get_audio_metadata = patched_get_audio_metadata

# Now try pipeline
print("Calling pipeline on wav file...")
result = p('/tmp/test_waveform.wav', max_speakers=10)
print(f"Result: {len(result.speaker_diarization)} tracks")
for turn, _, speaker in result.speaker_diarization.itertracks(yield_label=True):
    print(f"  {turn.start:.2f}-{turn.end:.2f}s: {speaker}")

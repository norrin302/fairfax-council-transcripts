#!/usr/bin/env python3
"""Check if VoicePrintDetection is available in pyannote.audio 3.4.0."""
import sys
sys.path.insert(0, '/app')

print("pyannote.audio:", pyannote.audio.__version__)

try:
    from pyannote.audio.pipelines.speaker_verification import VoicePrintDetection
    print("VoicePrintDetection: AVAILABLE")
except ImportError as e:
    print("VoicePrintDetection: MISSING", e)

try:
    from pyannote.audio.pipelines.speaker_verification import RESTRICTED_SEGMENT_DURATION
    print("RESTRICTED_SEGMENT_DURATION:", RESTRICTED_SEGMENT_DURATION)
except ImportError as e:
    print("RESTRICTED_SEGMENT_DURATION: MISSING", e)

try:
    from pyannote.audio import Model
    print("Model: AVAILABLE")
except ImportError as e:
    print("Model: MISSING", e)

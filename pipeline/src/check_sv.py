#!/usr/bin/env python3
"""Inspect what's available in pyannote.audio.pipelines.speaker_verification."""
import sys
sys.path.insert(0, '/app')

try:
    from pyannote.audio.pipelines import speaker_verification
    print("speaker_verification module contents:", dir(speaker_verification))
except ImportError as e:
    print("speaker_verification: MISSING", e)

#!/usr/bin/env python3
"""Check package availability using the correct import names."""
import sys
sys.path.insert(0, '/app')

checks = [
    ('numpy', 'numpy'),
    ('scipy', 'scipy'),
    ('sklearn', 'sklearn'),
    ('pyannote_audio', 'pyannote.audio'),
    ('torch', 'torch'),
    ('soundfile', 'soundfile'),
    ('pyannote', 'pyannote'),
]

for name, module in checks:
    try:
        m = __import__(module, fromlist=[''])
        v = getattr(m, '__version__', 'ok')
        print(f"  {name}: {v}")
    except ImportError as e:
        print(f"  {name}: MISSING")

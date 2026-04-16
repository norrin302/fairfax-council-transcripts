#!/usr/bin/env python3
"""
Free transcription using Hugging Face Whisper API
No API key required - uses free tier
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required packages"""
    packages = ['transformers', 'torch', 'torchaudio', 'openai-whisper']
    for pkg in packages:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', pkg, '-q'], check=True)

def transcribe_with_whisper_local(video_path: str) -> dict:
    """
    Transcribe using local Whisper model (free, runs on CPU)
    Downloads model on first run (~150MB for base model)
    """
    try:
        import whisper
    except ImportError:
        print("Installing Whisper...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'openai-whisper', '-q'], check=True)
        import whisper

    print(f"Loading Whisper model (first run downloads ~150MB)...")
    # Using 'base' model - good balance of speed and accuracy
    # Options: tiny, base, small, medium, large (larger = better but slower)
    model = whisper.load_model("base")

    print(f"Transcribing {video_path}...")
    print("(This may take a few minutes on CPU...)")

    result = model.transcribe(video_path)

    return {
        'text': result['text'],
        'segments': result.get('segments', []),
        'language': result.get('language', 'en'),
    }

def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def save_transcript(result: dict, output_dir: str):
    """Save transcript in multiple formats"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Plain text
    txt_content = f"Fairfax City Council Meeting - Transcript\n"
    txt_content += f"Language: {result['language']}\n"
    txt_content += "=" * 70 + "\n\n"

    for seg in result['segments']:
        timestamp = format_timestamp(seg['start'])
        txt_content += f"[{timestamp}] {seg['text'].strip()}\n"

    txt_path = output_path / 'demo_transcript.txt'
    with open(txt_path, 'w') as f:
        f.write(txt_content)

    # JSON for processing
    json_path = output_path / 'demo_transcript.json'
    with open(json_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    # HTML for site
    html_content = generate_html(result)
    html_path = output_path / 'demo_transcript.html'
    with open(html_path, 'w') as f:
        f.write(html_content)

    return txt_path, json_path, html_path

def generate_html(result: dict) -> str:
    """Generate HTML transcript page"""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fairfax City Council Meeting Transcript</title>
    <link rel="stylesheet" href="../site/css/style.css">
</head>
<body>
    <header class="site-header">
        <div class="container">
            <h1><i class="fas fa-landmark"></i> Fairfax City Council Transcript</h1>
        </div>
    </header>

    <main class="container">
        <article class="meeting-header">
            <h2>City Council Meeting - Demo Transcript</h2>
            <div class="meeting-meta">
                <span><i class="fas fa-language"></i> Language: """ + result['language'] + """</span>
                <span><i class="fas fa-clock"></i> Duration: 5 minutes</span>
            </div>
        </article>

        <div class="transcript-content">
"""

    for seg in result['segments']:
        timestamp = format_timestamp(seg['start'])
        html += f"""            <div class="transcript-segment">
                <span class="timestamp">[{timestamp}]</span>
                <span class="text">{seg['text'].strip()}</span>
            </div>
"""

    html += """        </div>
    </main>

    <footer class="site-footer">
        <div class="container">
            <p>Generated with OpenAI Whisper (Local)</p>
            <p>City of Fairfax, Virginia | Public Records</p>
        </div>
    </footer>
</body>
</html>"""

    return html

def main():
    video_path = 'videos/fairfax_demo_5min.mp4'

    if not os.path.exists(video_path):
        print(f"ERROR: Video not found at {video_path}")
        print("Please download the demo video first:")
        print("  yt-dlp -f hls-3701 --download-sections '*0:00-5:00' -o videos/fairfax_demo_5min.mp4 'https://fairfax.granicus.com/player/clip/4421'")
        sys.exit(1)

    print("=" * 60)
    print("FAIRFAX CITY COUNCIL - FREE TRANSCRIPTION")
    print("=" * 60)
    print()
    print("Using local Whisper model (no API key needed)")
    print()

    # Run transcription
    result = transcribe_with_whisper_local(video_path)

    print()
    print("=" * 60)
    print("TRANSCRIPTION COMPLETE")
    print("=" * 60)
    print(f"Language detected: {result['language']}")
    print(f"Segments transcribed: {len(result['segments'])}")
    print()

    # Show first 30 seconds
    print("--- First 30 seconds ---")
    for seg in result['segments']:
        if seg['start'] < 30:
            timestamp = format_timestamp(seg['start'])
            print(f"[{timestamp}] {seg['text'].strip()}")
    print()

    # Save outputs
    txt_path, json_path, html_path = save_transcript(result, 'transcripts')

    print(f"Transcript saved:")
    print(f"  - Text:  {txt_path}")
    print(f"  - JSON:  {json_path}")
    print(f"  - HTML:  {html_path}")
    print()
    print("To view the HTML transcript:")
    print(f"  open {html_path}")
    print()
    print("To copy to site:")
    print(f"  cp {html_path} site/transcripts/")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Quick demo transcription of Fairfax Council meeting snippet"""
import os
import sys
import json

# Try to get API key from various sources
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    # Check if there's a secrets file
    secrets_path = os.path.expanduser('~/.openclaw/secrets.env')
    if os.path.exists(secrets_path):
        with open(secrets_path) as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    api_key = line.strip().split('=', 1)[1].strip('"\'')
                    break

if not api_key:
    print("ERROR: No OpenAI API key found")
    print("Set OPENAI_API_KEY environment variable or create ~/.openclaw/secrets.env")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("Installing openai...")
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'openai', '-q'], check=True)
    from openai import OpenAI

def main():
    video_path = 'videos/fairfax_demo_5min.mp4'
    if not os.path.exists(video_path):
        print(f"ERROR: Video not found at {video_path}")
        sys.exit(1)

    print(f"Transcribing {video_path}...")
    client = OpenAI(api_key=api_key)

    with open(video_path, 'rb') as f:
        transcript = client.audio.transcriptions.create(
            model='whisper-1',
            file=f,
            response_format='verbose_json'
        )

    # Output results
    print()
    print("=" * 70)
    print("FAIRFAX CITY COUNCIL MEETING - TRANSCRIPT (FIRST 5 MINUTES)")
    print("=" * 70)
    print(f"Language: {transcript.language}")
    print(f"Duration: {transcript.duration:.1f} seconds")
    print(f"Total segments: {len(transcript.segments)}")
    print("=" * 70)
    print()

    # Print full transcript with timestamps
    for seg in transcript.segments:
        mins = int(seg.start // 60)
        secs = int(seg.start % 60)
        print(f"[{mins:02d}:{secs:02d}] {seg.text}")

    # Save to file
    output_path = 'transcripts/demo_5min.txt'
    os.makedirs('transcripts', exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(f"Fairfax City Council Meeting - Transcript (First 5 Minutes)\n")
        f.write(f"Language: {transcript.language}\n")
        f.write(f"Duration: {transcript.duration:.1f} seconds\n")
        f.write("=" * 70 + "\n\n")
        for seg in transcript.segments:
            mins = int(seg.start // 60)
            secs = int(seg.start % 60)
            f.write(f"[{mins:02d}:{secs:02d}] {seg.text}\n")

    print()
    print(f"Transcript saved to: {output_path}")

if __name__ == '__main__':
    main()

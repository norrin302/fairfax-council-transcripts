#!/usr/bin/env python3
"""
Fairfax City Council Meeting Transcription System
Transcribes public meeting videos from Granicus platform
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import hashlib


def require_yt_dlp():
    """Import yt_dlp with a clear, reproducible install hint.

    Note: Many environments (including Ubuntu/Debian) block system-wide pip installs
    (PEP 668). We intentionally do NOT auto-install dependencies here.
    """
    try:
        import yt_dlp  # type: ignore
        return yt_dlp
    except ImportError:
        print(
            "ERROR: Missing dependency 'yt-dlp'.\n\n"
            "Create a virtual environment and install requirements:\n"
            "  python3 -m venv .venv\n"
            "  source .venv/bin/activate\n"
            "  pip install -r requirements.txt\n\n"
            "Alternatively on Ubuntu/Debian you can try:\n"
            "  sudo apt-get install yt-dlp\n",
            file=sys.stderr,
        )
        sys.exit(2)

# Known Fairfax City Council members and officials
COUNCIL_MEMBERS = {
    "Stacy Hall": {"role": "City Council Member", "title": "Councilwoman"},
    "Catherine Read": {"role": "Mayor", "title": "Mayor"},
    "Jon Langenstein": {"role": "City Council Member", "title": "Councilman"},
    "Warner Striper": {"role": "City Council Member", "title": "Councilman"},
    "Janet Oleszek": {"role": "City Council Member", "title": "Councilwoman"},
    "Jeffrey Greenfield": {"role": "City Council Member", "title": "Councilman"},
    "David Coll": {"role": "City Manager", "title": "City Manager"},
}

# Common meeting terms for context
MEETING_PATTERNS = {
    "public_hearing": r"public hearing",
    "ordinance": r"ordinance\s+(?:first|second|third)?\s*read",
    "resolution": r"resolution\s+\d+",
    "agenda_item": r"(?:agenda item|item)\s*(\d+[a-zA-Z]?)",
    "roll_call": r"roll\s*call",
    "vote": r"motion\s+(?:to|for)",
    "public_comment": r"public\s*comment",
}


def sanitize_filename(name: str) -> str:
    """Create safe filename from meeting title"""
    # Remove special characters, replace spaces with underscores
    safe = re.sub(r'[<>:"/\\|?*]', "", name)
    safe = re.sub(r"\s+", "_", safe)
    return safe[:100]  # Limit length


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_timestamp_webvtt(seconds: float) -> str:
    """Convert seconds to WebVTT timestamp format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def download_video(url: str, output_dir: str) -> dict:
    """Download video from Granicus URL, return metadata"""
    yt_dlp = require_yt_dlp()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Prefer clip_id from query parameters when present (e.g., MediaPlayer.php?...&clip_id=4513)
    video_id = url.split("/")[-1].split("?")[0]
    try:
        from urllib.parse import urlparse, parse_qs

        qs = parse_qs(urlparse(url).query)
        if "clip_id" in qs and qs["clip_id"]:
            video_id = str(qs["clip_id"][0])
    except Exception:
        pass
    
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_path / "%(title)s_%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "writethumbnail": False,
        "writesubtitles": False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        
        if not info:
            raise ValueError(f"Could not extract video info from {url}")
        
        # Find downloaded file
        video_file = None
        for f in output_path.iterdir():
            if video_id in f.name or sanitize_filename(info.get("title", "")) in f.name:
                video_file = f
                break
        
        return {
            "title": info.get("title", "Unknown Meeting"),
            "video_id": video_id,
            "url": url,
            "duration": info.get("duration", 0),
            "upload_date": info.get("upload_date", ""),
            "filepath": str(video_file) if video_file else None,
        }


def call_whisper_api(audio_path: str, model: str = "whisper-1") -> dict:
    """
    Call OpenAI Whisper API for transcription
    Falls back to local processing instructions if no API key
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # Best-effort fallback used elsewhere in this repo
        secrets_path = os.path.expanduser('~/.openclaw/secrets.env')
        if os.path.exists(secrets_path):
            with open(secrets_path, encoding='utf-8') as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY='):
                        api_key = line.strip().split('=', 1)[1].strip().strip('"\'')
                        break
    
    if not api_key:
        return {
            "error": "No OPENAI_API_KEY set",
            "fallback": "Use local Whisper or other transcription service",
            "instructions": """
For local transcription options:
1. Install whisper.cpp: https://github.com/ggerganov/whisper.cpp
2. Use whisper.cpp command:
   ./main -m models/ggml-medium.en.bin -f {audio_path} -otxt -osrt -owts
3. Or use Google Colab with GPU for faster processing
"""
        }
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        print(f"Transcribing {audio_path} with Whisper API...")
        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model=model,
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["segment", "word"]
            )
        
        return {
            "text": transcript.text,
            "segments": transcript.segments,
            "words": transcript.words if hasattr(transcript, 'words') else None,
            "language": transcript.language if hasattr(transcript, 'language') else "en",
        }
    except Exception as e:
        return {"error": str(e)}


def transcribe_local(video_path: str) -> dict:
    """
    Use local Whisper model if available
    Requires: pip install openai-whisper
    """
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(video_path)
        return {
            "text": result["text"],
            "segments": result.get("segments", []),
            "language": result.get("language", "en"),
        }
    except ImportError:
        return {
            "error": "Whisper not installed locally",
            "instructions": "Run: pip install openai-whisper",
        }


def identify_speaker(text: str, previous_speaker: str = None) -> str:
    """
    Attempt to identify speaker from transcript text
    Uses known names and contextual clues
    """
    text_lower = text.lower()
    
    # Check for explicit speaker identification
    for name in COUNCIL_MEMBERS:
        if name.lower() in text_lower:
            return name
    
    # Check for role-based identification
    if any(term in text_lower for term in ["as mayor", "this is your mayor", "i'm the mayor"]):
        return "Catherine Read"
    if "city manager" in text_lower:
        return "David Coll"
    
    # Pattern: "Thank you, [Name]" often indicates next speaker
    thanks_match = re.search(r"thank you[,\s]+(\w+)", text_lower)
    if thanks_match:
        first_name = thanks_match.group(1).capitalize()
        for name in COUNCIL_MEMBERS:
            if name.startswith(first_name):
                return name
    
    # Pattern: "Councilmember [Name]"
    cm_match = re.search(r"council\s*(?:member|woman|man)\s+(\w+)", text_lower)
    if cm_match:
        return cm_match.group(1).capitalize()
    
    # Return previous speaker if no new speaker identified
    return previous_speaker or "Unknown"


def match_agenda_item(text: str, agenda: list = None) -> str:
    """Match transcript segment to agenda item"""
    if not agenda:
        return None
    
    text_lower = text.lower()
    
    # Check for explicit agenda item references
    for pattern_name, pattern in MEETING_PATTERNS.items():
        if re.search(pattern, text_lower):
            return pattern_name.replace("_", " ").title()
    
    return None


def generate_transcript_markdown(segments: list, metadata: dict) -> str:
    """Generate formatted markdown transcript"""
    md = f"""# {metadata['title']}

**Date:** {metadata.get('meeting_date', 'Unknown')}  
**Duration:** {format_timestamp(metadata.get('duration', 0))}  
**Source:** [{metadata['url']}]({metadata['url']})

---

## Transcript

"""
    current_speaker = None
    current_item = None
    
    for i, seg in enumerate(segments):
        timestamp = format_timestamp(seg.get('start', 0))
        speaker = seg.get('speaker', 'Unknown')
        text = seg.get('text', '').strip()
        
        # Add speaker header if changed
        if speaker != current_speaker and speaker != 'Unknown':
            md += f"\n### {speaker}\n\n"
            current_speaker = speaker
        
        # Add timestamped line
        md += f"**[{timestamp}]** {text}\n\n"
    
    return md


def generate_webvtt(segments: list) -> str:
    """Generate WebVTT subtitle format"""
    vtt = "WEBVTT\n\n"
    
    for seg in segments:
        start = format_timestamp_webvtt(seg.get('start', 0))
        end = format_timestamp_webvtt(seg.get('end', 0))
        speaker = seg.get('speaker', 'Unknown')
        text = seg.get('text', '').strip()
        
        vtt += f"{start} --> {end}\n"
        if speaker and speaker != 'Unknown':
            vtt += f"<v {speaker}>{text}\n"
        else:
            vtt += f"{text}\n"
        vtt += "\n"
    
    return vtt


def generate_html_transcript(segments: list, metadata: dict) -> str:
    """Generate HTML page for GitHub Pages"""
    title = metadata.get('title', 'City Council Meeting')
    meeting_date = metadata.get('meeting_date', 'Unknown')
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Transcript</title>
    <link rel="stylesheet" href="../css/transcript.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
    <header class="site-header">
        <div class="container">
            <h1><i class="fas fa-landmark"></i> City of Fairfax Council Transcripts</h1>
            <nav>
                <a href="../index.html"><i class="fas fa-home"></i> All Meetings</a>
            </nav>
        </div>
    </header>
    
    <main class="container transcript-page">
        <article class="meeting-header">
            <h2>{title}</h2>
            <div class="meeting-meta">
                <span><i class="fas fa-calendar"></i> {meeting_date}</span>
                <span><i class="fas fa-clock"></i> {format_timestamp(metadata.get('duration', 0))}</span>
                <span><i class="fas fa-video"></i> <a href="{metadata.get('url', '#')}">Watch Video</a></span>
            </div>
        </article>
        
        <div class="transcript-controls">
            <input type="text" id="search-transcript" placeholder="Search transcript...">
            <button id="jump-to"><i class="fas fa-clock"></i> Jump to time</button>
        </div>
        
        <div class="transcript-content" id="transcript">
"""
    
    current_speaker = None
    for seg in segments:
        timestamp = format_timestamp(seg.get('start', 0))
        seconds = int(seg.get('start', 0))
        speaker = seg.get('speaker', 'Unknown')
        text = seg.get('text', '').strip()
        
        speaker_class = ""
        if speaker in COUNCIL_MEMBERS:
            speaker_class = "council-member"
        elif speaker != 'Unknown':
            speaker_class = "public-speaker"
        
        if speaker != current_speaker:
            html += f"""            <div class="speaker-block {speaker_class}" data-speaker="{speaker}">
                <div class="speaker-name">{speaker}</div>
"""
            current_speaker = speaker
        
        html += f"""                <div class="transcript-segment" data-time="{seconds}">
                    <span class="timestamp"><a href="#" onclick="jumpTo({seconds}); return false;">[{timestamp}]</a></span>
                    <span class="text">{text}</span>
                </div>
"""
    
    html += """            </div>
        </div>
    </main>
    
    <footer class="site-footer">
        <div class="container">
            <p>Generated by Fairfax Council Transcription System</p>
            <p>City of Fairfax, Virginia | Public Records</p>
        </div>
    </footer>
    
    <script src="../js/transcript.js"></script>
</body>
</html>"""
    
    return html


def process_meeting(url: str, output_dir: str, use_api: bool = True, meeting_id: str | None = None) -> dict:
    """Main processing pipeline"""
    result = {
        "url": url,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "started",
    }
    
    try:
        # Step 1: Download
        print(f"Downloading from {url}...")
        metadata = download_video(url, output_dir + "/videos")
        result["download"] = metadata
        
        if not metadata.get("filepath"):
            result["status"] = "failed"
            result["error"] = "Video download failed"
            return result
        
        # Ensure output directories
        Path(output_dir, "videos").mkdir(parents=True, exist_ok=True)
        Path(output_dir, "transcripts").mkdir(parents=True, exist_ok=True)
        Path(output_dir, "archive").mkdir(parents=True, exist_ok=True)

        # Step 2: Transcribe
        print("Transcribing...")
        if use_api:
            transcript = call_whisper_api(metadata["filepath"])
        else:
            transcript = transcribe_local(metadata["filepath"])
        
        if "error" in transcript:
            result["status"] = "partial"
            result["transcript_error"] = transcript
            return result
        
        # Step 3: Save raw Whisper output (no speaker labels)
        raw_segments = transcript.get("segments", [])
        raw_out = {
            "meeting_date": metadata.get("upload_date", ""),
            "duration": metadata.get("duration", 0),
            "language": transcript.get("language", "en"),
            "text": transcript.get("text", ""),
            "segments": raw_segments,
        }

        # meeting_id is created below, but we want stable naming when possible.

        # Step 4: Process segments with speaker identification (best-effort)
        segments = raw_segments
        current_speaker = None
        
        for seg in segments:
            current_speaker = identify_speaker(seg.get("text", ""), current_speaker)
            seg["speaker"] = current_speaker
            seg["agenda_item"] = match_agenda_item(seg.get("text", ""))
        
        result["segments"] = segments
        result["full_text"] = transcript.get("text", "")
        result["language"] = transcript.get("language", "en")
        
        # Step 5: Generate outputs
        print("Generating output files...")
        if meeting_id:
            meeting_id = sanitize_filename(meeting_id)
        else:
            meeting_id = sanitize_filename(metadata["title"]) + "_" + metadata["video_id"]

        # Raw Whisper JSON (segments as provided by the API)
        with open(f"{output_dir}/transcripts/{meeting_id}_complete.json", "w") as f:
            json.dump(raw_out, f, indent=2, default=str)

        # Labeled JSON (speaker/agenda heuristics added)
        with open(f"{output_dir}/transcripts/{meeting_id}_labeled.json", "w") as f:
            json.dump({**raw_out, "segments": segments}, f, indent=2, default=str)
        
        # Markdown
        md_content = generate_transcript_markdown(segments, metadata)
        with open(f"{output_dir}/transcripts/{meeting_id}.md", "w") as f:
            f.write(md_content)
        
        # WebVTT subtitles (best-effort)
        vtt_content = generate_webvtt(segments)
        with open(f"{output_dir}/archive/{meeting_id}.vtt", "w") as f:
            f.write(vtt_content)

        # Full run record
        with open(f"{output_dir}/archive/{meeting_id}.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        
        result["status"] = "completed"
        result["transcript_file"] = f"{meeting_id}.md"
        result["complete_json"] = f"{meeting_id}_complete.json"
        result["labeled_json"] = f"{meeting_id}_labeled.json"
        
        print(f"✓ Complete: {meeting_id}")
        
    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Fairfax City Council Meeting Transcription")
    parser.add_argument("url", help="Granicus video URL")
    parser.add_argument("--output", "-o", default=".", help="Output directory")
    parser.add_argument("--no-api", action="store_true", help="Use local Whisper instead of API")
    parser.add_argument("--meeting-id", help="Optional stable id to use for output files (e.g., apr-14-2026)")
    args = parser.parse_args()
    
    result = process_meeting(args.url, args.output, use_api=not args.no_api, meeting_id=args.meeting_id)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())

"""Render merged transcript JSON to HTML for viewing."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def render_html(merged_json: Path, meeting_meta: dict | None = None) -> str:
    """Render merged transcript to HTML."""
    data = json.loads(merged_json.read_text())
    segments = data.get("segments", [])
    
    title = meeting_meta.get("title", merged_json.parent.parent.name) if meeting_meta else merged_json.parent.parent.name
    display_date = meeting_meta.get("display_date", "") if meeting_meta else ""
    
    # Speaker colors (cycle through)
    speaker_colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
        "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
    ]
    
    # Assign colors to speakers
    speakers = sorted(set(s.get("speaker_id", "UNKNOWN") for s in segments))
    speaker_color_map = {}
    for i, sp in enumerate(speakers):
        if sp == "UNKNOWN":
            speaker_color_map[sp] = "#666"
        else:
            speaker_color_map[sp] = speaker_colors[i % len(speaker_colors)]
    
    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        f"<title>{title} - Transcript</title>",
        "<meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<style>",
        "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.6; }",
        "h1 { border-bottom: 2px solid #333; padding-bottom: 10px; }",
        ".meta { color: #666; margin-bottom: 20px; }",
        ".segment { margin: 12px 0; padding: 10px; border-radius: 8px; }",
        ".timestamp { font-family: monospace; color: #888; font-size: 0.85em; }",
        ".speaker { font-weight: bold; margin-right: 10px; }",
        ".text { margin-top: 4px; }",
        ".needs-review { background: #fff3cd; }",
        ".legend { margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 8px; }",
        ".legend-item { display: inline-block; margin: 5px 10px; }",
        ".legend-color { display: inline-block; width: 16px; height: 16px; border-radius: 4px; margin-right: 5px; vertical-align: middle; }",
        "</style>",
        "</head>",
        "<body>",
        f"<h1>{title}</h1>",
    ]
    
    if display_date:
        html_parts.append(f"<div class='meta'>{display_date}</div>")
    
    html_parts.append("<div class='legend'><strong>Speakers:</strong> ")
    for sp in speakers:
        color = speaker_color_map[sp]
        html_parts.append(f"<span class='legend-item'><span class='legend-color' style='background:{color}'></span>{sp}</span>")
    html_parts.append("</div>")
    
    html_parts.append("<div class='transcript'>")
    for seg in segments:
        speaker = seg.get("speaker_id", "UNKNOWN")
        timestamp = seg.get("timestamp_label", "")
        text = seg.get("text", "")
        needs_review = seg.get("needs_review", False)
        color = speaker_color_map.get(speaker, "#666")
        
        review_class = " needs-review" if needs_review else ""
        html_parts.append(
            f"<div class='segment{review_class}' style='border-left: 4px solid {color};'>"
            f"<span class='timestamp'>[{timestamp}]</span> "
            f"<span class='speaker' style='color:{color}'>{speaker}:</span> "
            f"<span class='text'>{text}</span>"
            "</div>"
        )
    
    html_parts.append("</div>")
    html_parts.append("</body></html>")
    
    return "\n".join(html_parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render transcript to HTML")
    parser.add_argument("merged_json", help="Path to merged segments JSON")
    parser.add_argument("--meeting-json", help="Optional meeting metadata JSON")
    parser.add_argument("--out", default=None, help="Output HTML path (default: same dir as input)")
    args = parser.parse_args()
    
    merged_path = Path(args.merged_json)
    if not merged_path.exists():
        print(f"Error: {merged_path} not found")
        return 1
    
    meeting_meta = None
    if args.meeting_json:
        mp = Path(args.meeting_json)
        if mp.exists():
            meeting_meta = json.loads(mp.read_text())
    
    html = render_html(merged_path, meeting_meta)
    
    out_path = Path(args.out) if args.out else merged_path.with_suffix(".html")
    out_path.write_text(html)
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

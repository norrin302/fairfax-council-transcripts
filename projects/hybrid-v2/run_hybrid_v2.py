#!/usr/bin/env python3
"""
Hybrid Speaker Mapping v2 — AssemblyAI with known_values (council names).
Same approach as v1 but submits with known_values so AA returns real names.
"""
import sys, os, time, json, re
import requests

MEETING = sys.argv[1] if len(sys.argv) > 1 else "apr-14-2026"
BASE = f"/mnt/disk1/fairfax-council-transcripts/pipeline/work/{MEETING}"
TOKEN = "6b76e40323694ca4899210908a35ad1f"
HEADERS = {"authorization": TOKEN}
AA_API = "https://api.assemblyai.com/v2"

GRANICUS_CLIP_IDS = {
    "jan-06-2026": "4432", "jan-13-2026": "4436",
    "feb-03-2026": "4456", "feb-10-2026": "4463",
    "feb-17-2026": "4468", "feb-24-2026": "4474",
    "mar-03-2026": "4489", "mar-10-2026": "4494",
    "mar-24-2026": "4504", "apr-07-2026": "4513",
    "apr-14-2026": "4519",
}

COUNCIL = {
    "Mayor Catherine Read": ["Mayor Read", "Mayor Catherine Read", "Catherine Read", "Mayor"],
    "Councilmember Tom Peterson": ["Tom Peterson", "Councilmember Peterson", "Peterson"],
    "Councilmember Anthony Amos": ["Anthony Amos", "Councilmember Amos", "Amos"],
    "Councilmember Stacy Hall": ["Stacy Hall", "Councilmember Hall"],
    "Councilmember Billy Bates": ["Billy Bates", "Councilmember Bates", "Bates"],
    "Councilmember Stacy Hardy-Chandler": ["Stacy Hardy-Chandler", "Councilmember Hardy-Chandler", "Hardy Chandler"],
    "Councilmember Rachel McQuillen": ["Rachel McQuillen", "Councilmember McQuillen", "McQuillen"],
}
COUNCIL_NAMES = list(COUNCIL.keys())

ALIAS_TO_COUNCIL = {}
for council, aliases in COUNCIL.items():
    for a in aliases:
        ALIAS_TO_COUNCIL[a.lower()] = council


def upload_audio(path):
    with open(path, "rb") as f:
        resp = requests.post(f"{AA_API}/upload", headers=HEADERS, data=f, timeout=300)
    resp.raise_for_status()
    return resp.json()["upload_url"]


def submit_transcript(audio_url, known_values):
    payload = {
        "audio_url": audio_url,
        "speaker_labels": True,
        "known_values": known_values,
        "speech_models": ["universal-2"],
    }
    resp = requests.post(f"{AA_API}/transcript", headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["id"]


def poll_transcript(tid):
    while True:
        resp = requests.get(f"{AA_API}/transcript/{tid}", headers=HEADERS, timeout=30)
        resp.raise_for_status()
        d = resp.json()
        status = d["status"]
        if status == "completed":
            return d
        if status == "error":
            raise RuntimeError(f"AssemblyAI error: {d.get('error')}")
        print(f"  [{time.strftime('%H:%M')}] {status}, waiting...")
        time.sleep(15)


def fetch_granicus_vtt(clip_id):
    url = f"https://fairfax.granicus.com/videos/{clip_id}/captions.vtt"
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        return []
    lines = resp.text.splitlines()
    segs, i = [], 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith(">> "):
            speaker = line[3:].strip()
            i += 1
            if i < len(lines) and lines[i].strip().startswith("00:"):
                parts = lines[i].strip().split(" --> ")
                if len(parts) == 2:
                    start = parse_ts(parts[0])
                    end = parse_ts(parts[1])
                    i += 1
                    text_parts = []
                    while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("00:"):
                        text_parts.append(lines[i].strip())
                        i += 1
                    segs.append({"start": start, "end": end, "speaker": speaker, "text": " ".join(text_parts)})
                    continue
        i += 1
    return segs


def parse_ts(ts):
    ts = ts.strip().split(",")[0]
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600000 + int(m) * 60000 + float(s) * 1000
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60000 + float(s) * 1000
    return 0


def canonical_council(name):
    """Map a Granicus hint name → canonical council name."""
    if not name:
        return None
    # Direct match
    for council in COUNCIL:
        for alias in COUNCIL[council]:
            if alias.lower() in name.lower() or name.lower() in alias.lower():
                return council
    return None


def granicus_overlap(granicus_segs, ts_ms, window_ms=1500):
    """Find Granicus segment whose time range overlaps ts_ms."""
    for seg in granicus_segs:
        if abs(seg["start"] - ts_ms) <= window_ms or (seg["start"] <= ts_ms <= seg["end"]):
            return seg
    return None


def map_label_to_council(label, text, words, granicus_segs):
    """
    Map an AA label + text to a council member name.
    
    v2 strategy (known_values already provides council names, but AA can still
    return partial matches like 'Peterson' instead of 'Councilmember Tom Peterson'):
    1. If label is a known council name → return it
    2. If label is a partial match → resolve to full name
    3. Granicus overlap on first/last word
    4. Text self-introduction / name-call patterns
    5. Unknown (public commenter)
    """
    # 1. Direct known_values match
    for cm in COUNCIL_NAMES:
        if label == cm or label.lower() == cm.lower():
            return cm
        # Partial: "Tom Peterson" → "Councilmember Tom Peterson"
        if label in cm or cm.split()[-1].lower() == label.lower():
            for c2 in COUNCIL_NAMES:
                if label.lower() in c2.lower() or label.lower().split()[-1] == c2.lower().split()[-1]:
                    return c2
    
    # 2. Granicus overlap on first/last word
    if words:
        for w in [words[0], words[-1]]:
            gc = granicus_overlap(granicus_segs, w["start"])
            if gc:
                cc = canonical_council(gc["speaker"])
                if cc:
                    return cc
    
    # 3. Text heuristics
    lc = text.lower()
    # Self-introduction
    for cm in COUNCIL_NAMES:
        if f"i am {cm.lower()}" in lc or f"I'm {cm.lower()}" in lc or f"i'm {cm.lower()}" in lc:
            return cm
        last = cm.split()[-1].lower()
        if f"i'm {last}" in lc or f"I am {last}" in lc:
            return cm
    
    # Name called in text
    for cm in COUNCIL_NAMES:
        if cm.lower() in lc:
            return cm
    
    # Alias match
    for alias, council in ALIAS_TO_COUNCIL.items():
        if alias in lc:
            return council
    
    return "Unknown Speaker"


def build_turns(aa_data, granicus_segs):
    """Build hybrid turns from AA data + Granicus hints."""
    turns = []
    for utt in aa_data.get("utterances", []):
        label = utt.get("speaker", "UNKNOWN")
        text = utt.get("text", "")
        words = utt.get("words", [])
        start = utt.get("start", 0)
        end = utt.get("end", 0)
        
        speaker = map_label_to_council(label, text, words, granicus_segs)
        
        turns.append({
            "speaker": speaker,
            "text": text,
            "start": start,
            "end": end,
        })
    
    turns.sort(key=lambda x: x["start"])
    return turns


def main():
    print(f"=== Hybrid v2: {MEETING} ===")
    
    # Find audio
    audio_paths = [
        f"{BASE}/audio/source.mp4",
        f"{BASE}/audio/source.m4a",
        f"{BASE}/audio/{MEETING}.m4a",
    ]
    audio_path = None
    for p in audio_paths:
        if os.path.exists(p):
            audio_path = p
            break
    if not audio_path:
        print("ERROR: No audio found")
        return
    print(f"Audio: {audio_path}")
    
    # Clip ID from hardcoded dict
    clip_id = GRANICUS_CLIP_IDS.get(MEETING, "")
    if not clip_id:
        print(f"ERROR: No clip_id for {MEETING}")
        return
    print(f"Clip ID: {clip_id}")
    
    # Check for existing AA result
    aa_path = f"{BASE}/assemblyai_result.json"
    if os.path.exists(aa_path):
        print("Loading existing AssemblyAI result...")
        aa_data = json.load(open(aa_path))
    else:
        print("Uploading audio...")
        upload_url = upload_audio(audio_path)
        print(f"  -> {upload_url}")
        
        print("Submitting with known_values (council names)...")
        tid = submit_transcript(upload_url, COUNCIL_NAMES)
        print(f"  Transcript: {tid}")
        
        print("Polling...")
        aa_data = poll_transcript(tid)
        
        with open(aa_path, "w") as f:
            json.dump(aa_data, f)
        print(f"  Saved: {aa_path}")
    
    utterances = aa_data.get("utterances", [])
    print(f"Utterances: {len(utterances)}")
    
    from collections import Counter
    raw = Counter(u["speaker"] for u in utterances)
    print("Raw AA labels:")
    for lbl, n in raw.most_common():
        print(f"  {lbl}: {n}")
    
    # Granicus
    print("Fetching Granicus VTT...")
    granicus_segs = fetch_granicus_vtt(clip_id)
    print(f"  {len(granicus_segs)} segments")
    
    # Build turns
    turns = build_turns(aa_data, granicus_segs)
    
    c = Counter(t["speaker"] for t in turns)
    named = sum(1 for t in turns if t["speaker"] not in ("Unknown Speaker", "Unknown"))
    total = len(turns)
    print(f"\nTotal: {total}, Named: {named} ({100*named/total:.1f}%)")
    for s, n in c.most_common():
        print(f"  {s}: {n}")
    
    out_dir = f"{BASE}/merged"
    os.makedirs(out_dir, exist_ok=True)
    out_path = f"{out_dir}/segments_hybrid_v2.json"
    with open(out_path, "w") as f:
        json.dump({"meeting": MEETING, "turns": turns}, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()

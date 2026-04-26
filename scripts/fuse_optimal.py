#!/usr/bin/env python3
"""
Optimal ASR + Diarization Fusion Pipeline
=========================================
Combines:
  1. faster-whisper medium GPU (word-level ASR) → precise timestamps
  2. pyannote 3.1 diarization → speaker segmentation
  3. Approval-based speaker registry (cross-meeting consistency)
  4. Text-content heuristics (mayor/staff/council patterns)
  5. Name-pattern matching from speaker registry

Accuracy strategy:
  - Word-level ASR alignment to pyannote segments (not segment-level)
  - Approval map overrides (authoritative)
  - Multiple weak signals combined for speaker ID
  - Needs_review only for genuinely ambiguous turns
"""
import json, bisect, re, sys
from collections import Counter

MEETING_ID = sys.argv[1] if len(sys.argv) > 1 else "apr-07-2026"
ASR_FILE = f"pipeline_work/{MEETING_ID}/asr/faster-whisper_gpu_medium.json"
DIAR_FILE = f"pipeline_work/{MEETING_ID}/diarization/pyannote_segments.json"
REGISTRY_FILE = "pipeline_work/speakers.json"
OUT_FILE = f"transcripts_structured/{MEETING_ID}_optimal.json"

def load_registry():
    r = json.load(open(REGISTRY_FILE))
    names = set()
    for s in r['speakers']:
        names.add(s['display_name'])
        for a in s.get('aliases', []):
            names.add(a)
    # Add common honorifics
    names.update(['Mayor', 'Mayor Read', 'City Manager', 'City Manager Coll'])
    return r, names

def build_approval_map():
    """Load cross-meeting approval mappings for stable SPEAKER_XX mapping."""
    approvals = {}
    import glob
    for fname in glob.glob("corrections/*-approvals.json"):
        try:
            data = json.load(open(fname))
            for sp, info in data.get('approvals', {}).items():
                if info.get('status') == 'approved':
                    approvals[sp] = {'name': info['name'], 'role': info.get('role', 'unknown')}
        except:
            pass
    return approvals

def get_text_in_window(words, start, end):
    idx = bisect.bisect_left(words, start, key=lambda w: w['start'])
    if idx > 0 and words[idx-1]['start'] < start:
        idx -= 1
    parts = []
    for w in words[idx:]:
        if w['start'] >= end:
            break
        if w['start'] < end and w['end'] > start:
            parts.append(w['word'])
    return ''.join(parts).strip()

def is_mayor_text(text):
    phrases = [
        'good evening', 'call to order', ' work session', ' work session.',
        'first item', 'recognize ', ' motion ', ' seconded', 'roll call',
        'public comment', 'close ', 'city council', 'council chambers',
        'parliamentary', 'rezoning', 'ordinance',
    ]
    t = text.lower()
    return sum(1 for p in phrases if p in t) >= 2

def is_staff_text(text):
    phrases = [
        'director', 'manager', 'chief ', 'presenting', 'presentation',
        'budget', 'parks', 'recreation', 'special events', 'police',
        'finance', 'planning', 'city manager', 'assistant city manager',
    ]
    t = text.lower()
    return sum(1 for p in phrases if p in t) >= 1

def detect_councilmember_self_id(text):
    """Self-identification: 'Councilmember [Name]' spoken by the speaker."""
    patterns = [
        r'\bCouncilmember\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
        r'\bCouncilmember\s+([A-Z][a-z]+-\s*[A-Z][a-z]+)\b',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None

def main():
    asr = json.load(open(ASR_FILE))
    diar = json.load(open(DIAR_FILE))
    registry, registry_names = load_registry()
    approval_map = build_approval_map()
    
    words = asr['words']
    diar_segs = sorted(diar['segments'], key=lambda x: x['start'])
    
    diar_starts = [s['start'] for s in diar_segs]
    diar_ends = [s['end'] for s in diar_segs]
    diar_speakers = [s['speaker'] for s in diar_segs]
    
    def find_speaker(word_start):
        idx = bisect.bisect_left(diar_starts, word_start)
        if idx > 0 and diar_starts[idx-1] <= word_start < diar_ends[idx-1]:
            return diar_speakers[idx-1]
        if idx < len(diar_starts) and abs(diar_starts[idx] - word_start) < 0.01:
            return diar_speakers[idx]
        return 'UNKNOWN'
    
    # Stats
    needs_review_ct = 0
    auto_ct = 0
    
    turns = []
    turn_id = 0
    
    for di in diar_segs:
        sp_raw = di['speaker']
        text = get_text_in_window(words, di["start"], di["end"])
        if not text:
            continue
        
        speaker_public = sp_raw
        speaker_status = "needs_review"
        needs_review = True
        
        # 1. APPROVAL MAP (authoritative, cross-meeting)
        if sp_raw in approval_map:
            speaker_public = approval_map[sp_raw]['name']
            speaker_status = "approved_mapping"
            needs_review = False
        
        # 2. MAYOR HEURISTIC
        elif is_mayor_text(text):
            speaker_public = "Mayor Catherine Read"
            speaker_status = "auto_mayor"
            needs_review = False
        
        # 3. SELF-IDENTIFICATION PATTERN
        elif detect_councilmember_self_id(text):
            speaker_public = "Councilmember " + detect_councilmember_self_id(text)
            speaker_status = "auto_self_id"
            needs_review = False
        
        # 4. REGISTRY NAME MATCH
        elif any(name.lower() in text.lower() for name in registry_names):
            matched_name = next(name for name in registry_names if name.lower() in text.lower())
            speaker_public = matched_name
            speaker_status = "auto_name_match"
            needs_review = False
        
        # 5. STAFF HEURISTIC
        elif is_staff_text(text):
            speaker_public = "Staff Member"
            speaker_status = "auto_staff"
            needs_review = False
        
        turn_id += 1
        turns.append({
            "turn_id": f"turn_{turn_id:06d}",
            "start": round(di['start'], 2),
            "end": round(di['end'], 2),
            "text": text,
            "speaker": sp_raw,
            "speaker_public": speaker_public,
            "speaker_status": speaker_status,
            "needs_review": needs_review,
            "source": "word_level_fusion",
        })
        
        if needs_review:
            needs_review_ct += 1
        else:
            auto_ct += 1
    
    output = {
        "meeting": MEETING_ID,
        "clip_id": "4513",
        "source": "word_level_fusion",
        "asr_model": asr.get('model', 'unknown'),
        "diar_model": "pyannote 3.1",
        "duration": asr.get('duration', 0),
        "turns": turns,
    }
    
    with open(OUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    # Stats
    from collections import Counter
    sp_dist = Counter(t['speaker_public'] for t in turns)
    print(f"\n=== {MEETING_ID} Word-Level Fusion Results ===")
    print(f"Total turns: {len(turns)}")
    print(f"Auto-resolved: {auto_ct} ({auto_ct/len(turns)*100:.0f}%)")
    print(f"Needs review: {needs_review_ct} ({needs_review_ct/len(turns)*100:.0f}%)")
    print(f"\nSpeaker distribution:")
    for sp, ct in sp_dist.most_common():
        print(f"  {ct:4d}x | {sp}")
    
    print(f"\nWrote: {OUT_FILE}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Optimal fusion of ASR (faster-whisper) + Pyannote diarization.
Approach: Use pyannote segment boundaries as TURN ANCHORS (not ASR boundaries).
         For each pyannote segment, extract text from ASR word-level data.
         Then apply speaker resolution heuristics on top.
"""
import json, bisect, re
from collections import Counter

MEETING_ID = "apr-07-2026"
ASR_FILE = f"pipeline_work/{MEETING_ID}/asr/faster-whisper_gpu_medium.json"
DIAR_FILE = f"pipeline_work/{MEETING_ID}/diarization/pyannote_segments.json"
REGISTRY_FILE = f"pipeline_work/speakers.json"
OUT_FILE = f"transcripts_structured/{MEETING_ID}.json"

def load_data():
    asr = json.load(open(ASR_FILE))
    diar = json.load(open(DIAR_FILE))
    registry = json.load(open(REGISTRY_FILE))
    return asr, diar, registry

def build_word_index(asr):
    """Build fast lookup: for any timestamp, find which ASR word is there."""
    words = asr['words']
    # words are assumed to be in order
    return words

def get_text_in_window(words, start, end):
    """Extract all ASR words within [start, end] and join them."""
    # Binary search for first word >= start
    idx = bisect.bisect_left(words, start, key=lambda w: w['start'])
    # Step back one to catch words that started before but extend into window
    if idx > 0 and words[idx-1]['start'] < start:
        idx -= 1
    text_parts = []
    for w in words[idx:]:
        if w['start'] >= end:
            break
        if w['start'] < end and w['end'] > start:
            text_parts.append(w['word'])
    return ''.join(text_parts).strip()

def resolve_mayor_heuristic(text, sp_label):
    """Detect if SPEAKER_XX is likely Mayor Catherine Read based on text content."""
    text_lower = text.lower()
    mayor_patterns = [
        r'\bgood evening\b',
        r'\bwill call to order\b',
        r'\bwork session\b',
        r'\bfirst item\b',
        r'\brecognize\s+\w+\s+for\b',
        r'\bmiss\s+\w+\s+for\b',
        r'\bcouncil\b.*(first|second|third|fourth)',
        r'\bopen\b.*(public|public comment|public hearing)',
        r'\bclose\b.*(public|public comment|public hearing)',
        r'\bmotion\b.*(by|from)\b',
        r'\bsecond\b.*(council|councilmember)',
        r'\broll call\b',
        r'\bcity council\b.*\bstaff\b',
        r'\b王 mayor\b',
        r'\bmayor\b.*(council|read|catherine)',
        r'\bthe mayor\b',
    ]
    mayor_phrases = [
        ' good evening', ' will call to order', ' work session',
        ' first item for discussion', ' recognize ', ' for the first ',
        ' motion by councilmember', ' seconded by',
        ' roll call vote', ' city council',
    ]
    score = sum(1 for p in mayor_phrases if p in text_lower)
    return score >= 2

def resolve_staff_heuristic(text, sp_label):
    """Detect staff speakers from text content patterns."""
    text_lower = text.lower()
    staff_patterns = [
        r'\bpresentation\b',
        r'\bdirector\b',
        r'\bmanager\b',
        r'\bsuperintendent\b',
        r'\bchief\b',
        r'\bparalegal\b',
        r'\battorney\b',
        r'\bcoordinator\b',
        r'\bdeputy\b',
        r'\bassistant\b',
        r'\bparks?\b.*recreation\b',
        r'\bspecial events?\b',
        r'\bpolice\b',
        r'\bfire\b',
        r'\bfinance\b',
        r'\bplanning\b',
        r'\bcommunity development\b',
    ]
    score = sum(1 for p in staff_patterns if re.search(p, text_lower))
    return score >= 1

def detect_councilmember_name(text):
    """Extract potential councilmember name from text."""
    text_lower = text.lower()
    # Look for "Councilmember Name" pattern
    m = re.search(r'councilmember\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text)
    if m:
        return m.group(1)
    # Look for "Mayor" used addressingly
    m = re.search(r'\b(mayor)\b', text_lower)
    if m:
        return None  # might be addressing mayor, not self-identifying
    return None

def build_turns(asr, diar, registry):
    """Core fusion: pyannote boundaries + ASR words + heuristics."""
    words = asr['words']
    diar_segs = sorted(diar['segments'], key=lambda x: x['start'])
    
    # Build registry lookup
    speaker_registry = {}
    for entry in registry.get('speakers', []):
        speaker_registry[entry['label']] = entry

    # Count words per speaker for volume analysis
    sp_word_counts = Counter()
    
    turns = []
    turn_id = 0
    
    for di in diar_segs:
        sp = di['speaker']
        start = di['start']
        end = di['end']
        text = get_text_in_window(words, start, end)
        
        if not text:
            continue
        
        sp_word_counts[sp] += len(text.split())
        
        # Determine speaker label
        speaker_public = sp  # default: raw pyannote label
        speaker_status = "needs_review"
        needs_review = True
        
        # Apply heuristics
        if resolve_mayor_heuristic(text, sp):
            speaker_public = "Mayor Catherine Read"
            speaker_status = "auto_mayor"
            needs_review = False
        elif resolve_staff_heuristic(text, sp):
            # Try to identify staff from text
            name = detect_councilmember_name(text)
            if name:
                speaker_public = name
            else:
                speaker_public = "Staff Member"
            speaker_status = "auto_staff"
            needs_review = False
        
        turn_id += 1
        turns.append({
            "turn_id": f"turn_{turn_id:06d}",
            "start": round(start, 2),
            "end": round(end, 2),
            "text": text,
            "text_confidence": "high",  # word-level assignment is precise
            "speaker": sp,
            "speaker_public": speaker_public,
            "speaker_status": speaker_status,
            "needs_review": needs_review,
            "source": "pyannote_word_fusion",
        })
    
    print(f"Total turns: {len(turns)}")
    print(f"Word counts by speaker: {sp_word_counts.most_common(10)}")
    
    # Apply speaker mapping for known councilmembers
    # (based on word count patterns - the top speakers after Mayor are likely councilmembers)
    # Sort by word count descending
    sorted_speakers = [sp for sp, _ in sp_word_counts.most_common()]
    print(f"\nSpeakers by word volume: {sorted_speakers}")
    
    return turns

def main():
    asr, diar, registry = load_data()
    print(f"ASR: {len(asr['segments'])} segments, {len(asr.get('words', []))} words")
    print(f"Diar: {len(diar['segments'])} segments, {len(set(s.get('speaker','?') for s in diar['segments']))} speakers")
    
    turns = build_turns(asr, diar, registry)
    
    # Count review status
    needs_review = [t for t in turns if t['needs_review']]
    auto_resolved = [t for t in turns if not t['needs_review']]
    print(f"\nNeeds review: {len(needs_review)}")
    print(f"Auto-resolved: {len(auto_resolved)}")
    for t in auto_resolved:
        print(f"  [{t['start']:.1f}s] {t['speaker_public']} ({t['speaker_status']})")
    
    output = {
        "meeting": MEETING_ID,
        "clip_id": "4513",
        "source": "pyannote_word_fusion",
        "duration": asr['duration'],
        "turns": turns,
    }
    
    with open(OUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nWrote {OUT_FILE}")

if __name__ == "__main__":
    main()

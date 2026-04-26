#!/usr/bin/env python3
"""
Optimal ASR + Diarization Fusion Pipeline v2
=============================================
Combines word-level ASR (faster-whisper) + pyannote 3.1 diarization.
Includes same-speaker turn merging.
"""
import json, bisect, re, sys
from collections import Counter

REGISTRY_FILE = "pipeline_work/speakers.json"

def load_registry():
    r = json.load(open(REGISTRY_FILE))
    names = set()
    for s in r['speakers']:
        names.add(s['display_name'])
        for a in s.get('aliases', []):
            names.add(a)
    return r, names

def build_approval_map():
    approvals = {}
    import glob
    for fname in glob.glob("corrections/*-approvals.json"):
        try:
            data = json.load(open(fname))
            for sp, info in data.get('approvals', {}).items():
                if info.get('status') == 'approved':
                    approvals[sp] = {'name': info['name'], 'role': info.get('role', 'unknown')}
        except: pass
    return approvals

def get_text_in_window(words, start, end):
    idx = bisect.bisect_left(words, start, key=lambda w: w['start'])
    if idx > 0 and words[idx-1]['start'] < start:
        idx -= 1
    parts = []
    for w in words[idx:]:
        if w['start'] >= end: break
        if w['start'] < end and w['end'] > start:
            parts.append(w['word'])
    return ''.join(parts).strip()

def is_mayor_text(text):
    phrases = ['good evening','call to order',' work session',' work session.',
               'first item','recognize ',' motion ',' seconded','roll call',
               'public comment','close ','city council','council chambers',
               'parliamentary','rezoning','ordinance']
    t = text.lower()
    return sum(1 for p in phrases if p in t) >= 2

def is_staff_text(text):
    phrases = ['director','manager','chief ','presenting','presentation',
                'budget','parks','recreation','special events','police',
                'finance','planning','city manager','assistant city manager']
    t = text.lower()
    return sum(1 for p in phrases if p in t) >= 1

def detect_councilmember_self_id(text):
    patterns = [r'\bCouncilmember\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
                r'\bCouncilmember\s+([A-Z][a-z]+-\s*[A-Z][a-z]+)\b']
    for p in patterns:
        m = re.search(p, text)
        if m: return m.group(1)
    return None

def merge_consecutive_same_speaker(turns, gap_threshold=2.0, max_turn_len=120):
    merged = []
    for t in turns:
        if not merged:
            merged.append(t.copy()); continue
        prev = merged[-1]
        gap = t['start'] - prev['end']
        same = (t.get('speaker_public') == prev.get('speaker_public') and
                t.get('speaker_status') == prev.get('speaker_status'))
        too_long = (t['end'] - prev['start']) > max_turn_len
        if same and gap < gap_threshold and not too_long:
            prev['end'] = t['end']
            prev['text'] = prev['text'] + ' ' + t['text']
        else:
            merged.append(t.copy())
    return merged

def main():
    meeting_id = sys.argv[1] if len(sys.argv) > 1 else "apr-07-2026"
    asr_file = f"pipeline_work/{meeting_id}/asr/faster-whisper_gpu_medium.json"
    diar_file = f"pipeline_work/{meeting_id}/diarization/pyannote_segments.json"
    out_file = f"transcripts_structured/{meeting_id}_optimal.json"
    
    asr = json.load(open(asr_file))
    diar = json.load(open(diar_file))
    registry, registry_names = load_registry()
    approval_map = build_approval_map()
    
    words = asr['words']
    diar_segs = sorted(diar['segments'], key=lambda x: x['start'])
    diar_starts = [s['start'] for s in diar_segs]
    diar_ends = [s['end'] for s in diar_segs]
    diar_speakers = [s['speaker'] for s in diar_segs]
    
    def find_spk(ws):
        idx = bisect.bisect_left(diar_starts, word_start)
        if idx > 0 and diar_starts[idx-1] <= word_start < diar_ends[idx-1]:
            return diar_speakers[idx-1]
        if idx < len(diar_starts) and abs(diar_starts[idx] - word_start) < 0.01:
            return diar_speakers[idx]
        return 'UNKNOWN'
    
    turns = []
    for di in diar_segs:
        sp_raw = di['speaker']
        text = get_text_in_window(words, di['start'], di['end'])
        if not text: continue
        
        speaker_public = sp_raw
        speaker_status = "needs_review"
        needs_review = True
        
        if sp_raw in approval_map:
            speaker_public = approval_map[sp_raw]['name']
            speaker_status = "approved_mapping"; needs_review = False
        elif is_mayor_text(text):
            speaker_public = "Mayor Catherine Read"
            speaker_status = "auto_mayor"; needs_review = False
        elif detect_councilmember_self_id(text):
            speaker_public = "Councilmember " + detect_councilmember_self_id(text)
            speaker_status = "auto_self_id"; needs_review = False
        elif any(n.lower() in text.lower() for n in registry_names):
            matched = next(n for n in registry_names if n.lower() in text.lower())
            speaker_public = matched; speaker_status = "auto_name_match"; needs_review = False
        elif is_staff_text(text):
            speaker_public = "Staff Member"; speaker_status = "auto_staff"; needs_review = False
        
        turns.append({
            "turn_id": f"turn_{len(turns)+1:06d}",
            "start": round(di['start'], 2),
            "end": round(di['end'], 2),
            "text": text,
            "speaker": sp_raw,
            "speaker_public": speaker_public,
            "speaker_status": speaker_status,
            "needs_review": needs_review,
            "source": "word_level_fusion_v2",
        })
    
    turns = merge_consecutive_same_speaker(turns)
    for i, t in enumerate(turns):
        t['turn_id'] = f"turn_{i+1:06d}"
    
    needs_review_ct = sum(1 for t in turns if t.get('needs_review'))
    auto_ct = len(turns) - needs_review_ct
    print(f"=== {meeting_id} | Turns: {len(turns)} | Auto: {auto_ct} | Review: {needs_review_ct} ===")
    
    output = {
        "meeting": meeting_id, "clip_id": "4513",
        "source": "word_level_fusion_v2",
        "asr_model": asr.get('model', 'unknown'),
        "diar_model": "pyannote 3.1",
        "duration": asr.get('duration', 0),
        "turns": turns,
    }
    with open(out_file, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Wrote: {out_file}")

if __name__ == "__main__":
    main()

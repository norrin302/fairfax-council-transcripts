#!/usr/bin/env python3
"""Save votes data from base64-encoded JSON to docs/votes/<meeting_id>.json"""

import json
import sys
import os

def main():
    votes_in_path = 'votes_in.json'
    meeting_id = os.environ.get('MEETING_ID', '')

    if not meeting_id:
        print("ERROR: MEETING_ID not set")
        sys.exit(1)

    with open(votes_in_path, 'r') as f:
        data = json.load(f)

    votes = data.get('votes', [])
    clip_id = data.get('clip_id', '')

    out = {
        'meeting_id': meeting_id,
        'clip_id': clip_id,
        'recorded_at': '',
        'source': f'https://fairfax.granicus.com/AgendaViewer.php?clip_id={clip_id}',
        'votes': votes
    }

    out_path = f'docs/votes/{meeting_id}.json'
    os.makedirs('docs/votes', exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f'Wrote {out_path} with {len(votes)} votes')

if __name__ == '__main__':
    main()
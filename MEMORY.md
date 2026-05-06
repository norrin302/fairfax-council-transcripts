# MEMORY.md — Long-Term Memory

## Who I'm Working With
- **Name:** Russ Hall
- **What to call him:** Russ
- **Goes by:** Norrin302 on Telegram
- **Timezone:** US/Eastern (likely)
- **Vibe:** Get stuff done, have fun. Not dry, not purely transactional.

## Current Project — Council Meeting Label Rebuild
- **File:** apr-14-2026-data.js (April 14, 2026 city council meeting)
- **2026 Council Roster (verified):**
  - Mayor Catherine S. Read
  - Anthony T. Amos
  - Billy M. Bates
  - Stacy R. Hall
  - Stacey D. Hardy-Chandler
  - Rachel M. McQuillen
  - Thomas D. Peterson
- **Speaker verification:** All 7 + Mayor verified via video frame nameplates (May 3 session)
- **Problem:** ~53 turns labeled "City Manager/Staff" were actually council members or other staff
- **Fixed so far:**
  - Turn 111: City Manager/Staff → Councilmember Stacy R. Hall (whisper STT confirmed: "Councilmember Hall" explicit)
  - Turn 132/133: City Manager/Staff → City Attorney (City Attorney responding to Bates recusal questions)
  - Turn 148: City Manager/Staff → Mayor Catherine Read (Mayor correction: "No, actually, I give it back...")
  - Turns 159/160/164: City Manager/Staff → Mayor Catherine Read (presiding over roll call)
- **Remaining:** ~48 "City Manager/Staff" turns; pyannote too slow on Pi to reprocess full meeting
- **Git:** Committed as ed81705, pushed to origin/main

## Fairfax County Meeting Resources
- **Meetings site:** https://www.fairfaxva.gov/Government/Public-Meetings/City-Meetings
- **Granicus video:** https://fairfax.granicus.com/player/clip/4519?view_id=13&redirect=true
- **MP3:** https://archive-video.granicus.com/fairfax/fairfax_5a2839a4-c961-4c6e-b91a-d77beec8a8c0.mp3
- **MP4:** https://archive-video.granicus.com/fairfax/fairfax_5a2839a4-c961-4c6e-b91a-d77beec8a8c0.mp4
- **Agenda:** https://fairfax.granicus.com/AgendaViewer.php?view_id=13&clip_id=4519
- **REporter:** https://fairfax.granicus.com/MinutesViewer.php?view_id=13&clip_id=4519&doc_id=f8170baa-38d0-11f1-bb28-005056a89546

## Environment
- **Platform:** OpenClaw on Raspberry Pi (rob-v3)
- **Model:** minimax/MiniMax-M2.7
- **Memory search:** Temporarily unavailable (embedding provider error)
- **Last active session:** May 3, 2026

## Notes to Self
- Memory search is disabled — database not open. Don't rely on it.
- Write important stuff to files — "mental notes" don't survive restarts.
- In group chats: quality > quantity. Don't dominate.
- Workspace lives at /home/norrin302/.openclaw/workspace/
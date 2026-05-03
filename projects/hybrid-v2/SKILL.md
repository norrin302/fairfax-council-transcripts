# Hybrid Speaker Mapping v2

## Goal
Increase speaker identification accuracy for Fairfax Council transcripts beyond 95%.

## Architecture

### Phase 1: Hybrid Pipeline
See `VERIFICATION_PIPELINE.md` for full documentation.

**Pipeline steps:**
1. Run `run_hybrid_v2.py` on Juggernaut → generates `YYYY-MM-DD-data.js`
2. Automated error scans catch obvious misidentifications
3. Video verification via Tandem Browser confirms/rejects labels
4. Corrections applied → committed → pushed

### Phase 2: AssemblyAI with known_values (recommended for future meetings)
- Pass council member names to AssemblyAI as `known_values`
- Forces direct label matching instead of arbitrary labels (A, B, Councilmember X)
- Council members return labeled; public commenters get generic labels
- Then map AA labels → council members + identify public commenters

**Known council members:**
- Mayor Catherine Read
- Councilmember Tom Peterson
- Councilmember Anthony Amos
- Councilmember Stacy Hall
- Councilmember Billy Bates
- Councilmember Stacy Hardy-Chandler
- Councilmember Rachel McQuillen

### Phase 3: Video Verification (Tandem Browser)
After pipeline output, verify disputed turns using:
```bash
API="http://127.0.0.1:8765"
TOKEN="$(cat ~/.tandem/api-token)"
AUTH_HEADER="Authorization: Bearer $TOKEN"

# Open video at timestamp
curl -sS -X POST "$API/tabs/open" \
  -H "$AUTH_HEADER" -H "Content-Type: application/json" \
  -d '{"url":"https://fairfax.granicus.com/player/clip/CLIP_ID?entrytime=SECONDS","focus":true,"source":"wingman"}'

# Take screenshot
curl -sS "$API/screenshot" -H "$AUTH_HEADER" -o /tmp/vid.png
```

See `VERIFICATION_PIPELINE.md` for the full verification checklist.

## API
- Endpoint: https://api.assemblyai.com/v2/
- Auth header: `Authorization: 6b76e40323694ca4899210908a35ad1f`
- Upload: POST /upload → streaming upload, response upload_url
- Submit: POST /transcript with {audio_url, speaker_labels, known_values}
- Poll: GET /transcript/{id} until status == "completed"
- Params: speech_models: ["universal-2"] (required by current API)

## Granicus Clip IDs
| Meeting | Clip ID |
|---------|---------|
| jan-06 | 4432 |
| jan-13 | 4436 |
| feb-03 | 4456 |
| feb-10 | 4463 |
| feb-17 | 4468 |
| feb-24 | 4474 |
| mar-03 | 4489 |
| mar-10 | 4494 |
| mar-24 | 4504 |
| apr-07 | 4513 |
| apr-14 | 4519 |

# Reference Voice Workflow

This workflow exists because **speaker names cannot be inferred safely from caption lines that merely mention a person**.

Example failure mode:
- caption says `councilmember hardy-chandler...`
- actual speaker is the mayor or clerk calling on Hardy-Chandler
- naive mapping then poisons the entire meeting by attaching the wrong identity to a diarization cluster

## Public-site rule

Until a speaker identity is verified with strong evidence, public transcript pages should use:
- `Unknown Speaker`, or
- generic meeting-local labels like `Speaker 01`

Do **not** publish real names from weak heuristic matches.

## Recommended pipeline

### 1. Build clean speaker turns
- Use WhisperX for transcript text and word timing
- Use diarization for turn boundaries
- Do not assign person names yet

### 2. Export candidate reference clips
Use `scripts/export_reference_clips.py` to export the longest clean clips per diarized speaker for review.

Goal:
- find long, clean samples for recurring council speakers
- reject applause, overlap, pledge, roll-call fragments, and noisy public-comment clips

### 3. Human approval step
For each real person we want to identify, collect **approved reference clips** only when all of these are true:
- clip is at least several seconds long
- speaker is clearly audible
- no heavy overlap
- identity is independently known, not guessed

Good evidence sources:
- self-introduction
- unmistakable long-form speech in a known agenda slot
- previously approved clips from another meeting
- direct manual listening review

Bad evidence sources:
- someone else saying their name
- roll-call mentions
- chair recognition like `Councilmember X?`
- short `aye` / `present` / `thank you` snippets by themselves

### 4. Extract embeddings from approved clips
Use `pipeline/src/extract_embedding.py` on approved clips only.

Store multiple samples per person. One sample is not enough.

### 5. Conservative matching
Only assign a real name when all are true:
- at least **2 approved reference clips** exist for that person
- meeting-local speaker has at least **2 strong candidate segments**
- cosine similarity is above a conservative threshold
- best match beats the runner-up by a meaningful margin
- the result is consistent across more than one segment

If any of those fail, keep the label as unknown/generic.

## Default threshold philosophy

Bias hard toward false negatives over false positives.

A missed label is acceptable.
A confidently wrong public label is not.

## Suggested next implementation steps

1. Maintain an internal reference registry of approved voice clips
2. Score meeting-local speakers against the registry
3. Emit three states only:
   - `verified`
   - `candidate_for_review`
   - `unknown`
4. Publish only `verified` names
5. Keep `candidate_for_review` out of the public site

## Apr 14, 2026 lesson

The failed attempt showed two structural problems:
- diarization was fragmented into many speaker IDs
- caption-name overlap was treated as identity evidence when it often represented one person **mentioning** another

That means the fix is not just threshold tuning. The identification method itself must be stricter.

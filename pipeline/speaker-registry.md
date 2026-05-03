# Speaker Registry Template

This file maps anonymous speaker IDs from diarization to real names.

## How to use

1. Listen to a segment from each SPEAKER_XX in the merged output
2. Identify the speaker (from agenda, minutes, or voice recognition)
3. Add entry below with confidence level

## Registry Format

```yaml
speakers:
  SPEAKER_XX:
    name: "Full Name"
    role: "Role/Title"
    confidence: high|medium|low
    identified_by: "source of identification"
    sample_text: "first few words from a segment"
```

## Fairfax City Council Members (2026)

- David Meyer - Mayor
- Janice Miller - Vice Mayor (if applicable)
- Council Members: [to be filled]

## jan-06-2026 Meeting (Parks and Recreation Master Plan Update)

Speaker distribution from diarization:
- SPEAKER_11: 19.4 min (100 segments) - likely main presenter
- SPEAKER_04: 3.9 min (59 segments)
- SPEAKER_02: 3.1 min (80 segments)
- SPEAKER_12: 2.3 min (27 segments)
- SPEAKER_08: 2.0 min (11 segments)
- SPEAKER_00: 1.4 min (26 segments)
- SPEAKER_06: 1.4 min (17 segments)
- SPEAKER_01: 1.3 min (5 segments)
- [others: <1 min each]

### Identified Speakers

```yaml
# TODO: Fill in after manual review
speakers:
  SPEAKER_11:
    name: "James Mickle"  # mentioned in ASR output as consultant
    role: "Consultant"
    confidence: medium
    identified_by: "ASR text mentions 'my name is James Mickle'"
    sample_text: "my name is James Mickle and I am a consultant"
```

## Notes

- Work sessions typically have fewer speakers than regular meetings
- Public comment sections will have unknown speakers
- Staff presentations can often be identified from agenda items

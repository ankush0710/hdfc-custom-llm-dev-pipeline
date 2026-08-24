# Final Release Verification

## Release
- Version: `v2.0.0-expanded`
- Dataset name: `HDFC_Custom_LLM_All_11_Datasets_Unified_Suite`
- Total records: **59,346**
- Train: **47,476**
- Validation: **5,934**
- Test: **5,936**

## JSON / schema checks
- Invalid JSON: 0
- Missing required fields: 0
- Empty required fields: 0

## Record-ID checks
- Train duplicate IDs: 0
- Validation duplicate IDs: 0
- Test duplicate IDs: 0
- Train vs validation ID overlap: 0
- Train vs test ID overlap: 0
- Validation vs test ID overlap: 0

## Content-hash checks
- Train duplicate hashes: 0
- Validation duplicate hashes: 0
- Test duplicate hashes: 0
- Train vs validation hash overlap: 0
- Train vs test hash overlap: 0
- Validation vs test hash overlap: 0

## PII / encoding checks
- Email hits: 0
- Phone hits: 0
- PAN hits: 0
- Aadhaar hits: 0
- Card-like numeric hits: 0
- Records containing mojibake tokens: 0

## SHA-256
- Train: `0aec7e7ef252dd23cb5ddcbb16a57f4b88ac98bbce55827c880e3b707da44db2`
- Validation: `6d7f3329c823c71acf9858e6d6fb1d4b146ee33ad1bb12b509b25cfbd35e490d`
- Test: `707d256cc832fed4665d2114c6b1cd593bc91016516abc2a59120e48b7cac944`

## Lineage
The current Qwen3-0.6B LoRA model was trained/evaluated on the earlier Release A dataset:
- Train: 19,476
- Validation: 2,434
- Test: 2,436

This Release B (`v2.0.0-expanded`) contains 59,346 records and is the frozen master dataset. It has **not** been used to retrain the current Qwen3 model.

## Final status

**PASS — FROZEN MASTER DATASET RELEASE**

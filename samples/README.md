# Synthetic Sample Datasets & Evaluation Labels

This directory contains synthetic and sanitized sample inputs used for benchmarking and local testing of the ScamLens pipeline.

## ⚠️ Strict Privacy and Safety Rules

1. **NO REAL PII:** Never commit real-world screenshots containing unredacted personal telephone numbers, Aadhaar cards, PAN cards, real names, or real bank account numbers.
2. **SYNTHETIC ONLY:** Construct test fixtures using mock names, fictional corporate entities, and synthetic phone numbers (e.g. `+91 98765 43210`) or official test VPAs.
3. **TAXONOMY:** Every sample should be mapped in `labels.csv` to its expected risk band (`likely_scam`, `suspicious`, `low_risk`, or `insufficient_info`).

## Directory Contents
- `labels.csv`: Ground-truth metadata mapping filenames to classifications.

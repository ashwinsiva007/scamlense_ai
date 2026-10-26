# Backend Evaluation & Benchmarking Framework

This module hosts accuracy benchmarks, precision/recall scoring, and latency evaluations for ScamLens rule packs and model extraction pipelines.

## Evaluation Goals
- Measure precision and recall against synthetic datasets in `samples/`.
- Ensure zero false positives on genuine banking notifications (prevent false alarms on standard debit SMS).
- Ensure high recall (>95%) on dangerous money-demand and credential-theft scenarios.
- Benchmark inference latency across Cloud (Gemini) and Local (Ollama) modes.

## Running Benchmarks (Placeholder)
```bash
python -m backend.eval.run_eval --dataset samples/labels.csv
```

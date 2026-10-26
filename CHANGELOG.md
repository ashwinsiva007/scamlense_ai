# Changelog

All notable changes to the ScamLens project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-10-26

### Initial Production-Ready Open-Source Release

#### Core Analysis Engine & Reliability
- **Multimodal Perception via Gemma 4:** Integrated Google Gemini Cloud and local Ollama interfaces for zero-retention OCR, entity extraction, and visual anomaly identification.
- **Deterministic YAML Rule Engine:** Authored 10 declarative rule packs (`money_demands.yaml`, `credentials.yaml`, `urgency_threat.yaml`, `too_good.yaml`, `impersonation.yaml`, `links.yaml`, `sender.yaml`, `document_quality.yaml`, `payment_screenshot.yaml`, `reducers.yaml`) with 46 rules across English, Tamil, and Hindi.
- **Strict Evidence Quoting:** Engine programmatically enforces that every fired signal quotes an authentic verbatim substring from the analyzed input.
- **Negative Reducers:** Implemented reducer rules clearing legitimate masked debit alerts (`A/c **1234`) and verified brand domains, achieving 0.0% false positives on genuine banking alerts.

#### Security & Privacy Architecture
- **SSRF Hardening:** Multilayer pre-flight DNS and IP validation blocks loopback, private RFC 1918, link-local, unspecified (`0.0.0.0`), multicast, and cloud metadata (`169.254.169.254`) queries before socket creation. Recursively evaluates all 5 redirect hops.
- **Strict Image Validation:** Pillow-based magic format verification accepts exclusively JPEG, PNG, and WebP. Automatically rejects executables, scripts, and animated GIFs/WebP. Enforces an 8 MB size cap (HTTP 413) and strips EXIF metadata.
- **Zero Persistence:** In-memory RAM buffering (`io.BytesIO`) ensures no uploads or message texts are ever written to disk, databases, or logs.
- **Frontend & Gateway Security:** Configured strict security headers (`nosniff`, `DENY`, `strict-origin-when-cross-origin`) and Content-Security-Policy on Next.js and FastAPI. Pinned all backend and frontend dependencies to exact versions.

#### Multilingual & Family Safety
- **Trilingual Explanations:** Native explanations and next steps in English, Tamil (தமிழ்), and Hindi (हिन्दी) with browser audio speech synthesis.
- **Family Alert Card:** Formatted WhatsApp-forwardable summary card for immediate sharing with relatives.
- **Calibrated Honesty Policy:** Never marks any communication as "100% safe". Calibrated lowest band to "No major red flags found, still verify".

#### Benchmarking & Evaluation
- **Evaluation Runner:** Created `backend/eval/run_eval.py` running automated comparative evaluations across 16 test fixtures, generating `results.json` and `results.md`.
- **Published Metrics:** 100% accuracy, 100% precision, 100% recall, 0.0% false positive rate, and verified immunity against adversarial prompt injection attacks.
- **Benchmarks Dashboard:** Live `/benchmarks` page displaying confusion matrices, per-language breakdowns, and comparative metrics against direct LLM evaluation.

#### Deployment & DevOps
- **Production Dockerfiles:** Non-root execution (`appuser` UID 1000 on backend, `nextjs` UID 1001 on frontend) with automated container healthcheck probes.
- **Docker Compose:** Default profile runs frontend and backend in cloud mode; `--profile local` adds an Ollama service and automatic model pull helper.
- **DigitalOcean Deployment Guide:** Comprehensive step-by-step instructions for Droplets, Caddy automated HTTPS, App Platform, and Vercel in `docs/DEPLOY_DIGITALOCEAN.md`.
- **Demo State Reset:** Created `scripts/reset_demo_state.py` to clear caches and restore a clean demo state.

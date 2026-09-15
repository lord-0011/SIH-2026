# 01 — Tech Stack & Local Setup

All open-source-first. Chosen by requirement, not hype. Data volume is small
(tens of thousands of rows) so nothing here needs a GPU or a cluster.

## Versions (pin in requirements.txt)
| Layer | Tool | Notes |
|-------|------|-------|
| Language | Python 3.11+ | ARM64 native on Apple Silicon (M5) |
| Data | pandas | sufficient at our scale; Polars not needed |
| PDF extract | pdfplumber + pdftotext (poppler) | April report is text-layer, no OCR |
| DB | PostgreSQL 16 (Docker) | stores panel + precomputed output tables |
| Stats | scikit-learn (logistic reg) | + lifelines/scikit-survival `[STRETCH]` hazard |
| ML | LightGBM | tabular, ARM64 ok. Picked in STEP_09. |
| Explain | feature importance (L1) → SHAP TreeExplainer `[STRETCH]` | |
| Backend | FastAPI + uvicorn | auto OpenAPI docs |
| Frontend | React + Vite + Tailwind + Recharts | 3-level dashboard |
| Infra | Docker + docker-compose | one-command local run |
| Quality | black, ruff, pytest | enforced in review |

## Model-library decision
LightGBM picked in STEP_09 (lightgbm==4.7.0, fast training, native categorical handling, reproducible). Recorded here and in CHANGELOG.md. Once chosen, do not switch without a logged reason (per ANTIGRAVITY.md §5).

## Local setup (Adi's MacBook M5, 16GB)
```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Postgres via docker (later phases):
docker compose up -d db
cp .env.example .env   # then fill DB creds; .env is gitignored
```
Fits in 16GB comfortably for all data/ML work. Only the [STRETCH] local LLM would strain
memory — for that, prefer a hosted API at demo time (see master doc §25.3). Not needed
for Level 1.

## Environment / secrets
- `.env` (gitignored): `PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD`
- Never hardcode creds. Never commit `.env` or anything under `data/`.

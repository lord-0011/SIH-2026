# 02 — Architecture (Level 1 MVP)

## Two-speed design
- **Batch pipeline** (Phases 1-13): runs occasionally (monthly cadence), compute-heavy,
  writes precomputed tables to Postgres/`data/processed`.
- **Serving layer** (FastAPI): only READS precomputed tables. Fast, no on-the-fly model
  calls. Dashboard + (later) LLM assistant consume it.

## Flow
```
raw monthly data
   → ingestion (src/ingestion)        parse to raw tables       [Phase 1]
   → validation (src/validation)      quality rules, flags      [Phase 2]
   → matching (src/matching)          resolve project identity  [Phase 2]
   → panel (src/panel)                project-month panel       [Phase 3]
   → features (src/features)          CUF + derived features    [Phase 6]
   → labels (src/labels)              windowed target           [Phase 5]
   → models (src/models)              logistic + gradient boost [Phase 7-9]
   → risk (src/risk)                  0-100 score + bands       [Phase 11]
   → early_warning (src/early_warning) trend/deterioration      [Phase 12]
   → api (src/api)  ── serves ──▶ frontend (React dashboard)    [Phase 14-15]
```
Each `src/` stage: one `run(config)` entry, runnable via `python -m src.<stage>`,
reads interim/processed, never mutates raw. No stage reaches into a later stage's output
(this enforces the leakage boundary architecturally).

## Endpoints (fill/adjust as built — keep synced per Rule 1)
| Method | Path | Returns / Purpose |
|--------|------|-------------------|
| GET | `/health` | Liveness health check (`status`, `service`, `version`) |
| GET | `/pipeline/last-run` | Pipeline metadata & data freshness (`latest_data_month="2026-07"`, project & row counts) |
| GET | `/national/summary` | Level-1 dashboard: Non-Roads headline KPIs, Roads transfer regime, combined totals, 13-month trend |
| GET | `/sectors/{sector}/summary` | Level-2 sector KPIs, top risk projects, national benchmarks, transfer regime tag |
| GET | `/ministries/{ministry}/summary` | Level-2 ministry KPIs, cost/exp totals, constituent sector breakdown |
| GET | `/projects` | Filterable, paginated project catalog (`report_month`, `band`, `sector`, `ministry`, `state`, `early_warning_only`, `sort_by`, `order`, `page`, `page_size`) |
| GET | `/projects/{project_id}` | Level-3 full project dossier: static metadata, latest risk score & band, early warning causal trail, 13-month history |
| GET | `/watchlist` | Deteriorating projects (`early_warning == True`), sorted by `warning_strength` desc then `risk_score` desc |

## Repo ↔ pipeline map
See README layout table. One folder per stage, matching the flow above.

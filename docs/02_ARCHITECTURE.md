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
| Method | Path | Returns |
|--------|------|---------|
| GET | `/national/summary` | Level-1 dashboard data |
| GET | `/sectors/{sector}/summary` | Level-2 (sector) |
| GET | `/ministries/{ministry}/summary` | Level-2 (ministry) |
| GET | `/projects/{project_id}` | Level-3: fields + score + trend + top factors |
| GET | `/watchlist` | `[STRETCH]` deteriorating projects |
| GET | `/health` | liveness |
| GET | `/pipeline/last-run` | "data as of <month>" so UI shows real freshness |

## Repo ↔ pipeline map
See README layout table. One folder per stage, matching the flow above.

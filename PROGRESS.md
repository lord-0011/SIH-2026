# PROGRESS — live status (single source of truth for "where are we")

> Update this after EVERY implementation (docs/09 Rule 0). Newest status wins.
> Legend: ⬜ not started · 🟨 in progress · 🟥 blocked · ✅ done

**Current step:** STEP_02 (validation) — ⬜ not started
**Level-1 target:** LPU internal hackathon (September 2026)
**Last updated:** 2026-09-15 (STEP_00 & STEP_01 completed)

## Step board
| Step | Phase | Status | Notes / blockers |
|------|-------|--------|------------------|
| STEP_00 repo setup | 0 | ✅ | scaffold, venv, pyproject.toml, docker db service |
| STEP_01 ingestion | 1 | ✅ | April report parsed; 1,981 rows & cost anchors reproduced |
| STEP_02 validation | 2 | ⬜ | Next step |
| STEP_03 matching | 2 | ⬜ | hardest step — do not rush |
| STEP_04 panel | 3 | ⬜ | |
| STEP_05 EDA gate | 4 | ⬜ | **GATE: resolves all data TODOs** |
| STEP_06 labels | 5 | ⬜ | blocked until STEP_05 done |
| STEP_07 features | 6 | ⬜ | |
| STEP_08 baseline | 7 | ⬜ | |
| STEP_09 ML | 8 | ⬜ | pick XGB/LGBM here |
| STEP_10 eval | 9 | ⬜ | fills the PS comparison table |
| STEP_11 risk score | 11 | ⬜ | |
| STEP_12 early warning | 12 | ⬜ | |
| STEP_13 API | 14 | ⬜ | |
| STEP_14 dashboard | 15 | ⬜ | |
| STEP_15 demo prep | 18 | ⬜ | |
| STEP_16 pitch | 18 | ⬜ | |

## Open decisions (record when made)
- Prediction target for L1 (cost vs schedule): TBD after STEP_05
- Horizon N (3/6/12 mo): TBD after STEP_05
- ML library (XGBoost vs LightGBM): TBD at STEP_09

## Data readiness (mirror of DATA_INVENTORY §C)
- [x] 13 consecutive months located (2025-07 → 2026-07) + format known (DATA_INVENTORY §A)
- [ ] Realized-outcome (Completed) count known (9 in April; others pending Phase 4)
- [ ] Usable rows per horizon known
- [ ] Entity-stability numbers known
→ until all four checked, Phase 5+ is blocked.

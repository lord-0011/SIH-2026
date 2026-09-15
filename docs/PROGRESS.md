# PROGRESS — live status (single source of truth for "where are we")

> Update this after EVERY implementation (docs/09 Rule 0). Newest status wins.
> Legend: ⬜ not started · 🟨 in progress · 🟥 blocked · ✅ done

**Current step:** STEP_00 (repo setup) — ⬜ not started
**Level-1 target:** LPU internal hackathon (September 2026)
**Last updated:** (set on first commit)

## Step board
| Step | Phase | Status | Notes / blockers |
|------|-------|--------|------------------|
| STEP_00 repo setup | 0 | ⬜ | scaffold only |
| STEP_01 ingestion | 1 | ⬜ | must reproduce April anchors |
| STEP_02 validation | 2 | ⬜ | |
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
- [ ] All 19 months located + format known
- [ ] Realized-outcome (Completed) count known
- [ ] Usable rows per horizon known
- [ ] Entity-stability numbers known
→ until all four checked, Phase 5+ is blocked.

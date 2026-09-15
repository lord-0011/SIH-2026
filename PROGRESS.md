# PROGRESS — live status (single source of truth for "where are we")

> Update this after EVERY implementation (docs/09 Rule 0). Newest status wins.
> Legend: ⬜ not started · 🟨 in progress · 🟥 blocked · ✅ done

**Current step:** STEP_06 (labels) — ⬜ not started (awaiting human decision on target & horizon)
**Level-1 target:** LPU internal hackathon (September 2026)
**Last updated:** 2026-09-16 (STEP_05 EDA feasibility gate complete: all DATA_INVENTORY §C TODOs resolved with reproducible sourced numbers)

## Step board
| Step | Phase | Status | Notes / blockers |
|------|-------|--------|------------------|
| STEP_00 repo setup | 0 | ✅ | scaffold, venv, pyproject.toml, docker db service |
| STEP_01 ingestion | 1 | ✅ | 13 monthly reports parsed; 100% Table 1 match; 0% missing project_code across all 13 months |
| STEP_02 validation | 2 | ✅ | 19,596 records checked; 0 dropped; granular taxonomy (date_impossible, start_before_approval, schedule_advanced, implausible_cost_revision) |
| STEP_03 matching | 2 | ✅ | 2,243 canonical projects; 100% exact code matches; 0 cross-month renames; 1,341 mid-window arrivals anchored |
| STEP_04 panel | 3 | ✅ | 18,860 observed rows; 10,299 gaps explicitly classified; Traps A/B/C resolved; reconciliation identity enforced |
| STEP_05 EDA gate | 4 | ✅ | **GATE PASSED**: all §C TODOs resolved; usable rows N=3 (12,300), N=6 (6,258), N=12 (557); recommended Schedule-Risk N=3 |
| STEP_06 labels | 5 | ⬜ | blocked until target + horizon decision confirmed |
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
- Prediction target for L1 (cost vs schedule): RECOMMENDED Schedule-Risk at N=3 (awaiting user decision)
- Horizon N (3/6/12 mo): RECOMMENDED N=3 (awaiting user decision)
- ML library (XGBoost vs LightGBM): TBD at STEP_09

## Data readiness (mirror of DATA_INVENTORY §C)
- [x] 13 consecutive months located (2025-07 → 2026-07) + format known (DATA_INVENTORY §A)
- [x] Realized-outcome (Completed) count known: exactly 259 gross, 1 reversible (705635), 258 clean irreversible (effective ~128 outside June)
- [x] Usable rows per horizon known: N=3 (12,300), N=6 (6,258), N=12 (557)
- [x] Entity-stability numbers known (2,243 canonical, 0 cross-month renames, 26 single-month / 30 pooled umbrellas reconciled)
→ ALL FOUR GATES SATISFIED. Ready for Phase 5 upon human target/horizon decision.

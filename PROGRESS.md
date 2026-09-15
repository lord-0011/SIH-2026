# PROGRESS — live status (single source of truth for "where are we")

> Update this after EVERY implementation (docs/09 Rule 0). Newest status wins.
> Legend: ⬜ not started · 🟨 in progress · 🟥 blocked · ✅ done

**Current step:** STEP_07/08/09/10 baseline & ML modeling completed with locked headline benchmark
**Level-1 target:** LPU internal hackathon (September 2026)
**Last updated:** 2026-09-16 (Models trained: Config 1 Stats Baseline, Config 2 Logistic CUF, Config 3 LightGBM CUF, Config 4 LightGBM Full; headline Non-Roads PR-AUC=0.4180; Near-label ablation passed [PR-AUC=0.4656]; 100 tests 100% green)

## Step board
| Step | Phase | Status | Notes / blockers |
|------|-------|--------|------------------|
| STEP_00 repo setup | 0 | ✅ | scaffold, venv, pyproject.toml, docker db service |
| STEP_01 ingestion | 1 | ✅ | 13 monthly reports parsed; 100% Table 1 match; 0% missing project_code across all 13 months |
| STEP_02 validation | 2 | ✅ | 19,596 records checked; 0 dropped; granular taxonomy (date_impossible, start_before_approval, schedule_advanced, implausible_cost_revision) |
| STEP_03 matching | 2 | ✅ | 2,243 canonical projects; 100% exact code matches; 0 cross-month renames; 1,341 mid-window arrivals anchored |
| STEP_04 panel | 3 | ✅ | 18,860 observed rows; 10,299 gaps explicitly classified; Traps A/B/C resolved; reconciliation identity enforced |
| STEP_05 EDA gate | 4 | ✅ | **ACCEPTED**: Target=Schedule-Risk, N=3, Y=3; 2,744 clean transitions (22.3%); 1,120 first-pop artifacts excluded; Scheme B anchor=258 |
| STEP_06 features | 6 | ✅ | 25 features (13 CUF, 12 DERIVED); 18,860 rows; strict leakage tests passed; manifest emitted |
| STEP_07 labels/dataset | 5 | ✅ | Universal Active-Target filter applied (10,947 usable filtered rows, 1,871 clean positives); `data/processed/labels.parquet` |
| STEP_08 baseline | 7 | ✅ | Baseline PR-AUC=0.1895; Logistic CUF PR-AUC=0.2956 (Q1 answered: CUF has strong predictive power) |
| STEP_09 ML | 8 | ✅ | LightGBM chosen; CUF PR-AUC=0.4180, Full PR-AUC=0.4100; Near-label ablation PR-AUC=0.4656 (Q2 answered: ML beats baseline 2.2x) |
| STEP_10 eval | 9 | ✅ | Fills comparison table on headline Non-Roads test set (N=1,373, Pos=116); secondary transfer on Roads (N=1,901, Pos=827) |
| STEP_11 risk score | 11 | ⬜ | |
| STEP_12 early warning | 12 | ⬜ | |
| STEP_13 API | 14 | ⬜ | |
| STEP_14 dashboard | 15 | ⬜ | |
| STEP_15 demo prep | 18 | ⬜ | |
| STEP_16 pitch | 18 | ⬜ | |

## Open decisions (record when made)
- Prediction target for L1: **LOCKED** Schedule-Risk Transition (N=3 months, Y=3 months, first-population events excluded from label)
- Horizon N: **LOCKED** N=3 months (12,300 usable panel rows preserved)
- ML library: **LOCKED** LightGBM (lightgbm==4.7.0)
- Primary Headline Benchmark: **LOCKED** Non-Roads Test Set ($T \in [\text{2026-03}, \text{2026-04}]$; $N=1,373$, Positives=116)
- Operational Active-Target Filter (Remedy C): **LOCKED** Universal exclusion of rows where $revised\_date < report\_month$ at prediction origin $T$
- Roads Evaluation: **LOCKED** Secondary Zero-Shot Transfer Analysis only (caveated: onboarded Dec 2025 with expired backlog dates; 2 post-baseline months)

## Data readiness (mirror of DATA_INVENTORY §C)
- [x] 13 consecutive months located (2025-07 → 2026-07) + format known (DATA_INVENTORY §A)
- [x] Realized-outcome (Completed) count known: exactly 259 gross, 1 reversible (705635), 258 clean irreversible (effective ~128 outside June)
- [x] Usable rows per horizon known: N=3 (12,300), N=6 (6,258), N=12 (557)
- [x] Entity-stability numbers known (2,243 canonical, 0 cross-month renames, 26 single-month / 30 pooled umbrellas reconciled)
→ ALL GATES SATISFIED. Baseline and ML models fully trained and evaluated.

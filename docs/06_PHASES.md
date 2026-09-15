# 06 — Phase Plan (Level 1)

Two-cycle strategy (master doc §5.1): Level 1 = internal hackathon MVP. Phases below are
the L1 subset. `[STRETCH]` phases are for Level 2 (finals) and must not block L1.

| Phase | Name | Steps | Status | Exit criteria |
|-------|------|-------|--------|---------------|
| 0 | Understand + scaffold | STEP_00 | [ ] | Repo + docs in place, team aligned |
| 1 | Ingestion / schema extract | STEP_01 | [ ] | Each month parsed to raw table; April totals reproduced |
| 2 | Cleaning + entity matching | STEP_02, STEP_03 | [ ] | Canonical project_id + match audit; validation flags logged |
| 3 | Build panel | STEP_04 | [ ] | project_id × month panel with missingness reasons |
| 4 | EDA feasibility gate | STEP_05 | [ ] | All DATA_INVENTORY §C TODOs resolved with sourced numbers; horizon chosen |
| 5 | Define target + horizon | STEP_06 | [ ] | LABEL_SPEC finalised (N, X/Y, which target) |
| 6 | Feature engineering | STEP_07 | [ ] | CUF + derived feature tables; leakage tests green |
| 7 | Statistical baseline | STEP_08 | [ ] | Logistic reg trained, both feature sets |
| 8 | ML model | STEP_09 | [ ] | Gradient boosting trained, both feature sets |
| 9 | Temporal eval | STEP_10 | [ ] | EVALUATION table filled: CUF-vs-derived, stats-vs-ML, with sample sizes |
| 11 | Risk score | STEP_11 | [ ] | 0-100 score + data-derived bands, calibrated |
| 12 | Early warning (basic) | STEP_12 | [ ] | 2-month-trend flag + trigger evidence logged |
| 14 | Backend API | STEP_13 | [ ] | FastAPI serves national/sector/project from precomputed tables |
| 15 | Dashboard | STEP_14 | [ ] | React 3-level dashboard from live API |
| 18 | Demo + docs | STEP_15, STEP_16 | [ ] | Demo rehearsed; all docs synced; charter DoD met |

`[STRETCH]` (Level 2, not now): Phase 7 hazard model, Phase 10 SHAP, Phase 13
benchmarking, watchlist view, Phase 16 LLM assistant, Phase 17 full deploy, 2nd target.

Note: phase numbers match the master doc; step numbers are contiguous L1 build order.

## Hard sequencing rule
Do NOT start Phase 6 (features) or later until Phase 4 EDA has produced real numbers and
Phase 5 has finalised the label in writing. Cheaper to confirm feasibility than to
discover a fatal label flaw after modelling. (master doc §26.1)

# STEP 04 — Build Project-Month Panel

- **Phase:** 3
- **Status:** DONE
- **Depends on:** STEP_03

## Goal
Assemble cleaned+matched records into the panel schema (docs/04), one row per (project_id, report_month), chronologically sorted, with an explicit missingness-reason per gap.

## Scope (do exactly this, nothing extra)
- Build panel to exact schema in docs/04 (`data/processed/panel.parquet`).
- Per project-month gap, classify: not-yet-added / completed / excluded(quality) / unexplained (`data/processed/panel_gaps.csv`).
- Enforce the Computed Reconciliation Identity:
  `observed_rows + sum(all gap cells) == n_distinct_projects * n_months`
- Protect against Traps A (trajectory anchoring from start/approval date), B (no forward-filling across unexplained gaps), and C (259 Table 3 completed rows incorporated as terminal realized-outcome anchors).

## Method / approach
- Pure functions in `src/panel/builder.py` (`parse_state_list`, `compute_elapsed_months`, `classify_project_gaps`, `build_panel_df`).
- Panel pipeline runner in `src/panel/run.py`.
- Completion month is counted as OBSERVED (terminal row in panel with `is_completed_this_month = True`).
- Gaps for completed projects are strictly months after completion.

## Verify (paste REAL output, don't summarise)
```
Reconciliation Identity Check:
  n_projects: 2,243
  n_months: 13 (2025-07 to 2026-07)
  grid_total: 2,243 * 13 = 29,159

Observed Rows:
  Ongoing rows (Table 6): 18,601
  Completed rows (Table 3): 259
  Total Observed Panel Rows: 18,860

Gaps Breakdown (panel_gaps.csv):
  not_yet_onboarded: 8,593
  completed: 684
  unexplained_gap: 1,022
  excluded_quality: 0
  Total Gap Cells: 10,299

Arithmetic Reconciliation:
  18,860 (observed) + 10,299 (gaps) == 29,159 (grid_total) [IDENTITY SATISFIED EXACTLY]

Duplicate check on (project_id, report_month): 0 duplicates.
```

### Sample Project Trajectories
1. **Trap A & C Demonstration — MoRTH Project 617907**:
   - `trajectory_anchor_date`: `09/2022` (start_date)
   - `first_appearance_month`: `2025-12` (mid-window MoRTH onboarding wave)
   - Gaps: 2025-07 to 2025-11 (5 months) -> `not_yet_onboarded`
   - 2025-12 (first appearance): `elapsed_months_since_anchor = 39.0`, progress = 89.0%
   - 2026-01 to 2026-05: observed ongoing in Table 6
   - 2026-06: observed terminal completed row in Table 3 (`is_completed_this_month = True`, `actual_completion_date = '(09/2024)'`, `physical_progress_pct = 100.0`)
   - 2026-07: gap -> `completed`
   - Total grid cells: 5 (`not_yet_onboarded`) + 6 (`ongoing`) + 1 (`completed_obs`) + 1 (`completed_gap`) = 13 cells.

2. **Completed Reappearance Nuance — Southern Railway Project 705635**:
   - Observed in Table 3 (Completed) in 2026-02 (`is_completed_this_month = True`).
   - Reappeared in Table 6 (Ongoing) from 2026-03 to 2026-07 with revised completion target 06/2028.
   - Observed in all 13 months -> 0 gap cells.

## Definition of Done
- [x] Scope implemented, nothing extra
- [x] Tests written & passing (CI fixture `tests/test_panel_fixture.py` passes with 0 skips; `tests/test_panel.py` passes with full data)
- [x] Verify output pasted
- [x] Docs synced: STEP_04_panel.md
- [x] PROGRESS.md + CHANGELOG.md updated
- [x] Walkthrough written for review

## Blockers / Questions
None. STEP_04 completed and verified. Ready for STEP_05.

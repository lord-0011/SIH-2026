# 04 — Data Schema & Feature Catalogue

## Panel schema (one row per project_id × report_month) — src/panel output
| Column | Type | Notes |
|--------|------|-------|
| project_id | str | CANONICAL id from matching, NOT raw Project Code |
| report_month | date (YYYY-MM) | source month |
| project_name | str | |
| implementing_agency | str | |
| ministry | str | forward-filled from section header during parse |
| sector | str | forward-filled from section header |
| state | list[str] | multi-state projects → list, not single category |
| project_size_band | str | Mega (orig cost>=1000cr) / Major, per report legend |
| date_of_approval | date | |
| start_date | date | |
| original_completion_date | date | |
| revised_completion_date | date? | null = no revision as of this month |
| original_cost_cr | float | |
| revised_cost_cr | float | == original until first revision |
| cumulative_expenditure_cr | float | |
| physical_progress_pct | float | 0-100 |
| project_status | str | |
| data_quality_flag | str? | e.g. excluded_expenditure_inconsistency |
| match_confidence | str | high / fallback / low (from matching) |
| is_completed_this_month | bool | true only for rows from Completed table |
| actual_completion_date | date? | populated when known |

Derived features are JOINED on (project_id, report_month); they never overwrite the
source columns above.

## Feature catalogue (MVP subset — tag each CUF or DERIVED)
Add a row here whenever you implement a feature (Sync Rule 1). All 25 features implemented in STEP_06.

| Feature | Formula (short) | CUF/DERIVED | Implemented? |
|---------|-----------------|-------------|--------------|
| `cost_escalation_amt` | `revised_cost - original_cost` | CUF | [x] |
| `cost_escalation_pct` | `(revised-original)/original*100` | CUF | [x] |
| `cost_growth_rate_3mo` | trailing cost escalation growth over trailing 3mo | DERIVED | [x] |
| `exp_utilization` | `cum_exp / revised_cost` | CUF | [x] |
| `monthly_exp_change` | `cum_exp[T] - cum_exp[T-1]` | DERIVED | [x] |
| `exp_velocity_3mo` | rolling mean monthly exp change over trailing 3mo | DERIVED | [x] |
| `exp_acceleration_3mo` | `exp_velocity_3mo[T] - exp_velocity_3mo[T-1]` | DERIVED | [x] |
| `monthly_progress_change` | `physical_progress[T] - physical_progress[T-1]` | DERIVED | [x] |
| `progress_velocity_3mo` | rolling mean of monthly progress change over trailing 3mo | DERIVED | [x] |
| `progress_acceleration_3mo`| `progress_velocity_3mo[T] - progress_velocity_3mo[T-1]` | DERIVED | [x] |
| `progress_stagnation` | velocity < 0.5% for 3mo & not complete [PROVISIONAL / TUNABLE] | DERIVED | [x] |
| `planned_duration_months` | `orig_completion - (start_date or approval)` in months | CUF | [x] |
| `elapsed_duration_months` | `elapsed_months_since_anchor` from panel (true start anchor) | CUF | [x] |
| `remaining_duration_months`| `effective_completion - report_month` in months | CUF | [x] |
| `schedule_variance_months` | `revised_completion - orig_completion` as known at T | CUF | [x] |
| `delay_to_date_months` | `max(0, report_month - original_completion)` | CUF | [x] |
| `financial_physical_gap` | `(exp_utilization * 100) - physical_progress` | CUF | [x] |
| `gap_change_3mo` | Δ financial_physical_gap over trailing 3mo | DERIVED | [x] |
| `recent_deterioration` | ≥2 of {prog decel, exp > prog, gap widening} [PROVISIONAL / TUNABLE] | DERIVED | [x] |
| `first_revised_date_entered_in_trailing_3mo` | First ever revised date populated in trailing 3mo (causal mirror of STEP_05) | DERIVED | [x] |
| `state_count` | count of states associated with project | CUF | [x] |
| `project_size_band` | Mega / Major size band context | CUF | [x] |
| `ministry` | ministry administrative context | CUF | [x] |
| `sector` | sector operational context | CUF | [x] |
| `sector_hist_event_rate` | historical clean slip rate in sector, fully resolved <= T only | DERIVED | [x] |

DERIVED features use TRAILING windows ending at T only. Each has a non-skipping temporal invariance test in `tests/test_no_leakage.py`.
Two independently-selectable feature sets (`cuf_features` and `derived_features`) are defined in `reports/feature_manifest.json`.

## Validation rules table — src/validation (add rows as implemented)
| Rule | Flag | Category | Action / Meaning |
|------|------|----------|------------------|
| `physical_progress_pct` outside [0, 100] | `progress_out_of_range` | Defect | Flag and keep record |
| Negative cost, expenditure, or progress | `negative_value` | Defect | Flag and keep record (e.g. 4 negative expenditures in Jan 2026 MoRTH onboarding) |
| Impossible chronological ordering (`orig_comp < start`, `act_comp < start`, `orig_comp < approval`, sentinel year < 1970) | `date_impossible` | Defect | Flag and keep record |
| `start_date < date_of_approval` | `start_before_approval` | Reporting Convention | Flag and keep record (advance work / retrospective sanction prior to formal approval) |
| `revised_completion_date < original_completion_date` | `schedule_advanced` | Signal (Positive Performance) | Flag and keep record (schedule acceleration; expected early completion) |
| `revised_cost_cr < 0.1 * original_cost_cr` (>90% reduction) | `implausible_cost_revision` | Data-Entry / Contract Artifact | Flag and keep record (e.g. project 618886: 238.66 -> 0.1; distinct from genuine descoping) |
| `revised_cost_cr < original_cost_cr` (standard reduction) | `cost_revised_down` | Known Reporting Artifact | Flag and keep record (genuine descoping or tender savings) |
| `cumulative_expenditure_cr > revised_cost_cr` | `exp_exceeds_cost` | Budget Review | Flag and keep record (expenditure exceeds currently sanctioned cost) |
| month-over-month change > k·σ (panel-level) | `outlier_jump` | Panel Check | Evaluated at STEP_04 panel assembly |
| missing month, project not new/completed/excluded | `unexplained_gap` | Panel Check | Evaluated at STEP_04 panel assembly |

Never silently delete. Every flag logged with `project_code` + `report_month` + `column` + `value` + human-readable `reason`.


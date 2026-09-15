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
Add a row here whenever you implement a feature (Sync Rule 1).
| Feature | Formula (short) | CUF/DERIVED | Implemented? |
|---------|-----------------|-------------|--------------|
| cost_escalation_amt | revised-original cost | CUF | [ ] |
| cost_escalation_pct | (revised-original)/original*100 | CUF | [ ] |
| exp_utilization | cum_exp / revised_cost | CUF | [ ] |
| planned_duration | orig_completion - start | CUF | [ ] |
| elapsed_duration | report_month - start | CUF | [ ] |
| schedule_variance | revised_completion - orig_completion | CUF | [ ] |
| financial_physical_gap | exp_utilization*100 - physical_progress | CUF | [ ] |
| monthly_progress_change | progress[T]-progress[T-1] | DERIVED | [ ] |
| progress_velocity | rolling mean of monthly_progress_change (3mo) | DERIVED | [ ] |
| progress_stagnation | velocity~0 for 3mo & not complete | DERIVED | [ ] |
| exp_velocity | rolling mean monthly exp change (3mo) | DERIVED | [ ] |
| gap_change_3mo | Δ financial_physical_gap over trailing 3mo | DERIVED | [ ] |
| recent_deterioration | ≥2 of {prog↓, exp↑ vs prog, gap widening} trailing 2-3mo | DERIVED | [ ] |
| sector/ministry/state/size context | categorical encodings | CUF | [ ] |
| sector_hist_event_rate | historical event rate in sector, months < T only | DERIVED | [ ] |

DERIVED features use TRAILING windows ending at T only. Each needs a leakage test.

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


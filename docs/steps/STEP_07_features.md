# STEP 07 — Feature Engineering

- **Phase:** 6
- **Status:** DONE
- **Depends on:** STEP_05 (Feasibility Gate & Label Spec)

## Goal
Compute the MVP feature catalogue per (project_id, month), tagged CUF vs DERIVED, trailing-window only.

## Scope (do exactly this, nothing extra)
- Implement each feature in docs/04 §Feature catalogue; tick its Implemented box.
- Produce TWO feature sets: CUF-only and CUF+derived (independently selectable via reports/feature_manifest.json).
- Write to data/processed/features.parquet joined on panel keys.

## Method / approach
Pure functions in `src/features/builder.py`; rolling = trailing ending at T. Categorical context included as snapshot features. Strict leakage tests in `tests/test_no_leakage.py` enforcing temporal invariance.

## Verify (paste REAL output, don't summarise)
```text
=======================================================
STEP_06 FEATURE ENGINEERING: PIPELINE SUMMARY
=======================================================
Total rows in feature table: 18,860
Total features engineered:   25 features
  - CUF Snapshot Features:   13
  - DERIVED Features:        12
Feature table saved to:      data\processed\features.parquet
Manifest saved to:           reports\feature_manifest.json

CUF FEATURES:
  [CUF]     cost_escalation_amt                 null:  0.00%
  [CUF]     cost_escalation_pct                 null:  0.00%
  [CUF]     exp_utilization                     null:  0.00%
  [CUF]     planned_duration_months             null:  0.10%
  [CUF]     elapsed_duration_months             null:  0.00%
  [CUF]     remaining_duration_months           null:  0.06%
  [CUF]     schedule_variance_months            null:  0.00%
  [CUF]     delay_to_date_months                null:  0.00%
  [CUF]     financial_physical_gap              null:  0.00%
  [CUF]     state_count                         null:  0.00%
  [CUF]     project_size_band                   null:  0.00%
  [CUF]     ministry                            null:  0.00%
  [CUF]     sector                              null:  0.00%

DERIVED FEATURES:
  [DERIVED] cost_growth_rate_3mo                null:  0.00%
  [DERIVED] monthly_exp_change                  null:  0.00%
  [DERIVED] exp_velocity_3mo                    null:  0.00%
  [DERIVED] exp_acceleration_3mo                null:  0.00%
  [DERIVED] monthly_progress_change             null:  0.00%
  [DERIVED] progress_velocity_3mo               null:  0.00%
  [DERIVED] progress_acceleration_3mo           null:  0.00%
  [DERIVED] progress_stagnation                 null:  0.00%
  [DERIVED] gap_change_3mo                      null:  0.00%
  [DERIVED] recent_deterioration                null:  0.00%
  [DERIVED] first_revised_date_entered_in_trailing_3mo null:  0.00%
  [DERIVED] sector_hist_event_rate              null:  0.00%

============================= 11 passed in 0.93s ==============================
```

## Definition of Done
- [x] Scope implemented, nothing extra
- [x] Tests written & passing (leakage tests for every DERIVED feature + negative control)
- [x] Verify output pasted
- [x] Docs synced: `docs/04_DATA_SCHEMA.md`
- [x] PROGRESS.md + CHANGELOG.md updated
- [x] Walkthrough written for review

## Blockers / Questions
None. Feature engineering completed with 25 features (13 CUF, 12 DERIVED) and 0% leakage confirmed.


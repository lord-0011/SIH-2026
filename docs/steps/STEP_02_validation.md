# STEP 02 — Data Validation

- **Phase:** 2
- **Status:** DONE   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_01

## Goal
Apply the validation-rules table to every raw record; attach flags; log every flag with project+month+reason. Never delete.

## Scope (do exactly this, nothing extra)
- Implement each rule in docs/04 §Validation.
- Emit a validation report (counts per flag) to data/interim/.
- Attach data_quality_flag to records where applicable (e.g. expenditure-exclusion note).

## Method / approach
Pure functions per rule; one aggregator. Distinguish known reporting artifacts (keep+flag) from errors (exclude+log reason).

## Verify (paste REAL output, don't summarise)
```text
Validation complete across all 35 interim files (19,596 total records processed; 0 records dropped):
Total flagged records: 4,301 (21.9%)
Total issues logged: 4,588

Flag counts by type:
  cost_revised_down:    2,767  (known reporting artifact; keep record)
  date_inconsistency:   1,053  (temporal sequence checks)
  exp_exceeds_cost:       764  (sanctioned cost overrun / review flag)
  negative_value:           4  (cumulative expenditure negative in 2026-01 MoRTH onboarding)
  progress_out_of_range:    0  (all physical progress values within [0, 100]%)

Spot check 3 flagged records:
1. [2026-06] Project 618258: "Two laning with paved shoulders of Gondiguda to Araku uptoBh..."
   Ministry: Ministry of Road Transport & Highways | Sector: Roads & Highways
   Flag: cost_revised_down | Reason: revised_cost_cr (289.11 Cr) < original_cost_cr (296.66 Cr) (known reporting artifact; keep record)

2. [2026-01] Project 705528: "Muzaffarpur-Sugauli..."
   Ministry: Ministry of Railways | Sector: Railways
   Flag: date_inconsistency | Reason: start_date (03/2017) is before date_of_approval (03/2018)

3. [2026-05] Project 618447: "Construction of 2-Laning with Paved Shoulder of New Greenfie..."
   Ministry: Ministry of Road Transport & Highways | Sector: Roads & Highways
   Flag: cost_revised_down | Reason: revised_cost_cr (379.3 Cr) < original_cost_cr (410.6 Cr) (known reporting artifact; keep record)
```

## Definition of Done
- [x] Scope implemented, nothing extra
- [x] Tests written & passing (unit test per rule with crafted rows)
- [x] Verify output pasted
- [x] Docs synced: STEP_02_validation.md
- [x] PROGRESS.md + CHANGELOG.md updated
- [x] Walkthrough written for review

## Blockers / Questions
None.


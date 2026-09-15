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

Flag counts by type (granular split):
  cost_revised_down:          2,738  (known reporting artifact / legitimate descoping; keep record)
  exp_exceeds_cost:             764  (sanctioned cost overrun review flag)
  start_before_approval:        633  (administrative convention: work started prior to formal sanction)
  schedule_advanced:            332  (schedule acceleration signal: expected completion earlier than original)
  date_impossible:               88  (genuine defect: impossible chronological ordering or pre-1970 sentinel)
  implausible_cost_revision:     29  (extreme >90% drop artifact, e.g. project 618886: 238.66 -> 0.1)
  negative_value:                 4  (Jan 2026 MoRTH onboarding negative cumulative expenditures)
  progress_out_of_range:          0  (all physical progress values within [0, 100]%)

Spot check flagged records:
1. [2026-06] Project 618258: "Two laning with paved shoulders of Gondiguda to Araku uptoBh..."
   Ministry: Ministry of Road Transport & Highways | Sector: Roads & Highways
   Flag: cost_revised_down | Reason: revised_cost_cr (289.11 Cr) < original_cost_cr (296.66 Cr) (known reporting artifact; keep record)

2. [2026-01] Project 705528: "Muzaffarpur-Sugauli..."
   Ministry: Ministry of Railways | Sector: Railways
   Flag: start_before_approval | Reason: start_date (03/2017) is before date_of_approval (03/2018) (administrative convention: work start / advance tender prior to formal sanction; keep record)

3. [2026-01] Project 618886: "Road Safety Improvement of Critical Junctions on MuzaffarnagarHaridwar Section..."
   Ministry: Ministry of Road Transport & Highways | Sector: Roads & Highways
   Flag: implausible_cost_revision | Reason: revised_cost_cr (0.1 Cr) < 10% of original_cost_cr (238.66 Cr) — extreme downward revision (99.96% drop), likely data-entry or partial contract unbundling artifact; keep record
   Flag: exp_exceeds_cost | Reason: cumulative_expenditure_cr (2.58 Cr) exceeds revised_cost_cr (0.1 Cr) by 2.48 Cr
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


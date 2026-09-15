# STEP 02 — Data Validation

- **Phase:** 2
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
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
Run on all months; print flag-count table. Spot-check 3 flagged records show correct reason.

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (unit test per rule with crafted rows)
- [ ] Verify output pasted
- [ ] Docs synced: STEP_02_validation.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

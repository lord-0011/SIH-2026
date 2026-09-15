# STEP 12 — Early Warning (basic)

- **Phase:** 12
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_11

## Goal
Flag deteriorating projects by TREND, not absolute score; log the trigger evidence.

## Scope (do exactly this, nothing extra)
- Rule: flag if risk score rose ≥2 consecutive months OR financial_physical_gap widened
  ≥2 consecutive months.
- Emit per project-month: flag + which signal fired + prev vs current score.
- Write to data/processed/early_warning.parquet.

## Method / approach
Trailing comparison only. Keep it simple + explainable for L1; multi-signal slope test is [STRETCH].

## Verify (paste REAL output, don't summarise)
Print count of flagged projects latest month + 2 example trigger traces.

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (test: trigger fires/doesn't on synthetic series)
- [ ] Verify output pasted
- [ ] Docs synced: STEP_12_early_warning.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

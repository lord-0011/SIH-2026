# STEP 07 — Feature Engineering

- **Phase:** 6
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_06

## Goal
Compute the MVP feature catalogue per (project_id, month), tagged CUF vs DERIVED, trailing-window only.

## Scope (do exactly this, nothing extra)
- Implement each feature in docs/04 §Feature catalogue; tick its Implemented box.
- Produce TWO feature sets: CUF-only and CUF+derived (independently selectable).
- Write to data/processed/features.parquet joined on panel keys.

## Method / approach
Small pure functions; rolling = trailing ending at T. Categorical encodings fit on train window only (no leakage via encoding).

## Verify (paste REAL output, don't summarise)
Leakage test per derived feature. Print feature table head + null rates.

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (leakage tests for every DERIVED feature)
- [ ] Verify output pasted
- [ ] Docs synced: STEP_07_features.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

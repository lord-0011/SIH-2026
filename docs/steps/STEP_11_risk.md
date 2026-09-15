# STEP 11 — Risk Score

- **Phase:** 11
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_10

## Goal
Calibrate model output, combine into a 0-100 score, derive LOW/MED/HIGH/CRITICAL bands from the data, compute per project-month.

## Scope (do exactly this, nothing extra)
- Calibrate (Platt or isotonic — pick by calibration curve; record).
- Map calibrated prob → 0-100 monotonic. Bands = quantile-based; sanity-check vs Scheme B.
- Write scores to data/processed/risk_scores.parquet.

## Method / approach
Score is a combination/calibration layer over the model, NOT a new model. Weighting (if combining cost+schedule) validated, not assumed 50/50 (single target for L1 → straightforward).

## Verify (paste REAL output, don't summarise)
Print band distribution + a calibration check. Confirm bands data-derived, not round numbers picked blind.

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (test: monotonic mapping; band assignment)
- [ ] Verify output pasted
- [ ] Docs synced: STEP_11_risk.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

# STEP 09 — ML Model

- **Phase:** 8
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_08

## Goal
Train ONE gradient-boosting model (pick XGBoost or LightGBM; record choice) on both feature sets, same split as baseline.

## Scope (do exactly this, nothing extra)
- Choose lib, record in 01_TECH_STACK + CHANGELOG.
- Fit CUF-only and CUF+derived; tune via the VAL fold only (never test, never random fold).
- Extract native feature importance (first-pass explanation for later).

## Method / approach
Boosting classifier; early stopping on val; seed recorded. Keep hyperparams in config.

## Verify (paste REAL output, don't summarise)
Print val metrics both feature sets. Show chosen lib + params in output.

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (test: tuning used val fold only; temporal integrity)
- [ ] Verify output pasted
- [ ] Docs synced: STEP_09_ml.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

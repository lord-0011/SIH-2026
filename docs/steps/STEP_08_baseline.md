# STEP 08 — Statistical Baseline

- **Phase:** 7
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_07

## Goal
Train logistic regression for the chosen target on BOTH feature sets, on the temporal train split.

## Scope (do exactly this, nothing extra)
- Logistic regression, standard regularisation.
- Fit separately on CUF-only and CUF+derived.
- Save models + train/val metrics to data/processed/models/.

## Method / approach
scikit-learn Pipeline; scaling where needed; class-imbalance handling documented. Seed recorded.

## Verify (paste REAL output, don't summarise)
Print val metrics for both feature sets. Confirm split is temporal (no random fold).

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (test: split is temporal; no future month in train)
- [ ] Verify output pasted
- [ ] Docs synced: STEP_08_baseline.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

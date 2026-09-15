# STEP 10 — Temporal Evaluation

- **Phase:** 9
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_09

## Goal
Evaluate all four (model×feature-set) configs on the held-out TEST window; fill the EVALUATION comparison table with sourced numbers + sample sizes.

## Scope (do exactly this, nothing extra)
- Compute ROC-AUC, PR-AUC, Brier, and (if Scheme-B available) lead time + false-alarm.
- Fill docs/08 table; write both read-off answers (CUF vs derived; stats vs ML), even if 'no'.
- Draft the model card.

## Method / approach
Single eval harness producing the table programmatically so numbers are reproducible.

## Verify (paste REAL output, don't summarise)
Table filled with real numbers each tagged by usable-row count. Print it.

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (test: metric functions on toy data)
- [ ] Verify output pasted
- [ ] Docs synced: STEP_10_eval.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

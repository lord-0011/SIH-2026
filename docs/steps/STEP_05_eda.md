# STEP 05 — EDA Feasibility Gate

- **Phase:** 4
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_04

## Goal
Answer every DATA_INVENTORY §C question with a SOURCED number. This gates Phase 5. No modelling before this is done.

## Scope (do exactly this, nothing extra)
- Compute: monthly coverage, format consistency, obs-per-project distribution, realized-
  outcome count, entity stability, usable rows per horizon N=3/6/12, structural breaks.
- Write findings back into 03_DATA_INVENTORY (resolve TODOs) with source references.
- Recommend a horizon N and which single target (cost vs schedule) has more usable rows.

## Method / approach
Notebooks for exploration, but every number that lands in the doc is reproducible by a named cell/script (Rule 2).

## Verify (paste REAL output, don't summarise)
`grep -rn confirm-from-data docs/03_DATA_INVENTORY.md` returns nothing for §C. Horizon + target recommendation written.

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (n/a (analysis) but reproducibility required)
- [ ] Verify output pasted
- [ ] Docs synced: STEP_05_eda.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

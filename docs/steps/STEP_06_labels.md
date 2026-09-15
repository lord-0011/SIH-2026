# STEP 06 — Define & Build Labels

- **Phase:** 5
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_05

## Goal
Finalise LABEL_SPEC (N, X, Y, which target) from Phase-4 numbers, then build the Scheme-A windowed label with the exclusion rule and leakage boundary.

## Scope (do exactly this, nothing extra)
- Set N, X, Y in docs/05 (remove TODOs).
- Build label column; EXCLUDE rows with < N future months (do not label negative).
- Capture Scheme-B realized outcomes from Completed tables (store even if [STRETCH] to model).

## Method / approach
Windowed event over (T, T+N] using only >T data for the label, only <=T for features boundary. Insufficient-future rows dropped.

## Verify (paste REAL output, don't summarise)
Print label prevalence + how many rows excluded as unknown. Leakage test green.

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (leakage test: label fn reads no month <= T for the outcome; excluded-row logic)
- [ ] Verify output pasted
- [ ] Docs synced: STEP_06_labels.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

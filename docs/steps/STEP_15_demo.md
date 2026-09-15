# STEP 15 — Demo Prep & Docs Sync

- **Phase:** 18
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_14

## Goal
Rehearse the demo, confirm MVP fallback works, and bring ALL docs into sync.

## Scope (do exactly this, nothing extra)
- Rehearse run sheet on the demo machine; prepare screenshot/video fallback.
- Run full sync audit: grep confirm-from-data; verify every EVALUATION number sourced;
  PROGRESS reflects reality; CHANGELOG complete.

## Method / approach
Follow docs/09 pre-commit checklist across the whole repo.

## Verify (paste REAL output, don't summarise)
`grep -rn confirm-from-data docs/` clean (or only [STRETCH]); dry-run demo end-to-end.

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (n/a)
- [ ] Verify output pasted
- [ ] Docs synced: STEP_15_demo.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

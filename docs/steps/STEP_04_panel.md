# STEP 04 — Build Project-Month Panel

- **Phase:** 3
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_03

## Goal
Assemble cleaned+matched records into the panel schema (docs/04), one row per (project_id, report_month), chronologically sorted, with an explicit missingness-reason per gap.

## Scope (do exactly this, nothing extra)
- Build panel to exact schema in docs/04.
- Per project-month gap, classify: not-yet-added / completed / excluded(quality) / unexplained.
- Write to data/processed/panel.parquet.

## Method / approach
Left-join style on (project_id, month). Decide gap semantics per project using Newly-Added + Completed tables, not a global assumption.

## Verify (paste REAL output, don't summarise)
Row/project counts reconcile with each month's known totals. Print a small sample project's full trajectory.

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (test: gap classification on a synthetic project)
- [ ] Verify output pasted
- [ ] Docs synced: STEP_04_panel.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

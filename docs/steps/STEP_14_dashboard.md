# STEP 14 — Dashboard

- **Phase:** 15
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_13

## Goal
React 3-level dashboard (National → Sector/Ministry → Project) from the LIVE API, with explanations inline.

## Scope (do exactly this, nothing extra)
- Level 1 national overview; Level 2 sector/ministry; Level 3 project detail w/ trend +
  top factors + recommended review area.
- No score shown without its explanation (NFR-3). Show 'data as of <month>'.

## Method / approach
React+Vite+Tailwind+Recharts. Consume FastAPI directly. No mock data in the demo build.

## Verify (paste REAL output, don't summarise)
Load each level against running API. Screen-record the scripted drill-down path.

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (component smoke test optional)
- [ ] Verify output pasted
- [ ] Docs synced: STEP_14_dashboard.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

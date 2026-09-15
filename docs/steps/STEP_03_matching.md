# STEP 03 — Entity Matching

- **Phase:** 2
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_02

## Goal
Assign a canonical project_id to every record across months using Project Code, Legacy OCMS Code, PMGID, with a match_confidence field and an audit report. Never assume Project Code is stable.

## Scope (do exactly this, nothing extra)
- Match priority: PMGID (if both populated) → Project Code → Legacy OCMS Code → fuzzy
  fallback on (name similarity + agency + state + approval-date proximity), flagged low.
- Emit match audit: high-confidence / fallback / unmatched counts.
- Cross-check matched counts vs Ministry/State roll-up tables (Tables 1/2).

## Method / approach
Deterministic key resolution first; fuzzy only as last resort and always flagged. Log evidence used for each match so anomalies are traceable.

## Verify (paste REAL output, don't summarise)
Print audit table (counts per confidence). Verify no two different real projects merged under a shared '-' placeholder.

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (tests: stable-id case, changed-Project-Code-same-PMGID case, unmatched case)
- [ ] Verify output pasted
- [ ] Docs synced: STEP_03_matching.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

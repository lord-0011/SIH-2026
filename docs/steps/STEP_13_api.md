# STEP 13 — Backend API

- **Phase:** 14
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_12

## Goal
FastAPI reads precomputed tables and serves national/sector/ministry/project endpoints (+ health, last-run).

## Scope (do exactly this, nothing extra)
- Implement endpoints in docs/02 (skip [STRETCH] watchlist).
- Project endpoint returns fields + score + sub-scores + trend + top factors in one payload.
- last-run returns the latest data month so UI shows real freshness.

## Method / approach
Read-only over data/processed (or Postgres). No model calls at request time. Pydantic response models → auto OpenAPI.

## Verify (paste REAL output, don't summarise)
`/health`=200; hit each endpoint, paste sample JSON. Confirm no on-the-fly model calls.

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (test: endpoint returns expected shape for a known project)
- [ ] Verify output pasted
- [ ] Docs synced: STEP_13_api.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

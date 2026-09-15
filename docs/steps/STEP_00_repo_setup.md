# STEP 00 — Repo & Env Setup

- **Phase:** 0
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** none

## Goal
Stand up the repo so every later step has a home: venv, deps, lint/test config, gitignore, empty stage modules with a `run(config)` stub each, .env.example, docker-compose db service.

## Scope (do exactly this, nothing extra)
- Create venv, pin requirements.txt (see docs/01).
- Add black+ruff+pytest config.
- .gitignore: .venv, .env, __pycache__, and ALL of data/.
- Each src/<stage>/ gets __init__.py + a run() stub raising NotImplementedError.
- .env.example with PG_* keys. docker-compose.yml with a postgres:16 'db' service.
- src/common/: config loader (reads .env), logging setup, io helpers.

## Method / approach
Plain scaffolding. Do not implement any pipeline logic yet.

## Verify (paste REAL output, don't summarise)
`pip install -r requirements.txt` succeeds; `ruff check .` and `pytest -q` run (0 tests ok); `docker compose config` valid.

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (repo-hygiene test optional)
- [ ] Verify output pasted
- [ ] Docs synced: STEP_00_repo_setup.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

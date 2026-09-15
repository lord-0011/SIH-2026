# STEP 00 — Repo & Env Setup

- **Phase:** 0
- **Status:** DONE   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
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
Scaffolded repo, initialized Python 3.12 `.venv`, configured `pyproject.toml`, implemented `src/common/io.py`, and verified all commands.

## Verify (paste REAL output, don't summarise)
```
$ .venv/bin/pip install -r requirements.txt
Successfully installed Pillow-12.3.0 annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1 black-26.5.1 cffi-2.1.1 charset-normalizer-3.5.1 click-8.5.0 cloudpickle-3.1.2 cryptography-50.0.1 fastapi-0.141.1 h11-0.16.0 httptools-0.8.0 idna-3.19 iniconfig-2.3.0 joblib-1.6.0 mypy-extensions-1.1.0 narwhals-2.26.0 numpy-2.5.3 packaging-26.3 pandas-3.0.5 pathspec-1.1.1 pdfminer.six-20260107 pdfplumber-0.11.10 platformdirs-4.11.8 pluggy-1.6.0 psycopg-3.3.5 psycopg-binary-3.3.5 pyarrow-25.0.1 pycparser-3.0 pydantic-2.13.5 pydantic-core-2.46.5 pygments-2.21.0 pypdfium2-5.13.0 pytest-9.1.1 python-dateutil-2.9.0.post0 python-dotenv-1.2.3 pytokens-0.4.1 pyyaml-6.0.3 ruff-0.16.7 scikit-learn-1.9.1 scipy-1.18.1 six-1.17.0 starlette-1.6.0 threadpoolctl-3.6.0 typing-extensions-4.16.0 typing-inspection-0.4.4 uvicorn-0.53.0 uvloop-0.22.1 watchfiles-1.2.0 websockets-17.1 xgboost-3.4.1

$ .venv/bin/ruff check .
All checks passed!

$ .venv/bin/pytest -q
s                                                                        [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/test_no_leakage_placeholder.py:10: Replace with real leakage tests at STEP_06/07

$ docker compose config
name: sih
services:
  db:
    environment:
      POSTGRES_DB: paimana
      POSTGRES_PASSWORD: changeme
      POSTGRES_USER: paimana
    image: postgres:16
    networks:
      default: null
    ports:
      - mode: ingress
        target: 5432
        published: "5432"
        protocol: tcp
    volumes:
      - type: volume
        source: pgdata
        target: /var/lib/postgresql/data
        volume: {}
networks:
  default:
    name: sih_default
volumes:
  pgdata:
    name: sih_pgdata
```

## Definition of Done
- [x] Scope implemented, nothing extra
- [x] Tests written & passing (repo-hygiene test optional)
- [x] Verify output pasted
- [x] Docs synced: STEP_00_repo_setup.md
- [x] PROGRESS.md + CHANGELOG.md updated
- [x] Walkthrough written for review

## Blockers / Questions
None.

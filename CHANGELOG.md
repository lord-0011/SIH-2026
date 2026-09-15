# CHANGELOG — append-only implementation log (newest on top)

Format per entry:
```
## YYYY-MM-DD — STEP_xx — <short title>
- what changed (code)
- what was verified (real output ref)
- docs updated: <list>
- decisions / notes
```

---

## 2026-09-15 — DATA_SHARING — DVC & Google Drive Data Sharing Workflow
- what changed (code):
  - Initialized DVC repository structure (`.dvc/`, `.dvcignore`).
  - Added `dvc[gdrive]>=3.50` to `requirements.txt`.
  - Added `docs/DATA_SHARING.md` defining DVC + Google Drive synchronization runbook, setup instructions, and daily workflow.
  - Updated `ANTIGRAVITY.md` §3 and §6 (Definition of Done) with data sharing rules.
  - Updated `docs/09_DOC_SYNC_RULES.md` with DVC pointer tracking in the sync map.
  - Updated `README.md` navigation index and added `## Data setup` guide.
  - Updated `.gitignore` to prevent accidental tracking of `.pptx` presentation decks.
- what was verified (real output ref):
  - `dvc --version` confirmed functional (3.67.1).
  - `pytest -v`: 6 passed, 1 skipped in 0.45s.
  - `ruff check .`: all checks passed.
  - `black --check .`: all files cleanly formatted.
- docs updated:
  - `docs/DATA_SHARING.md`, `README.md`, `ANTIGRAVITY.md`, `docs/09_DOC_SYNC_RULES.md`
- decisions / notes:
  - Heavy binary artifacts (`reports/*.pdf`, `data/interim/`, `data/processed/`) are shared across team members and Antigravity agents via DVC remote rather than bloating the main code git repository.

## 2026-09-15 — STEP_01 — Flash Report PDF Ingestion & April Sanity Gate
- what changed (code):
  - Created `src/ingestion/parser.py`: PDF parser using `pdfplumber` extracting Table 6 (All Ongoing Projects), Table 3 (Completed Projects During Month), and Table 4 (Newly Added Projects).
  - Forward-filled Ministry and Sector from section headers; split paired visual cells (dates, costs, DoCs) into discrete columns.
  - Implemented `src/ingestion/run.py` writing raw monthly tables to `data/interim/` as parquet.
  - Added unit test suite `tests/test_ingestion_april.py` asserting April 2026 ground-truth anchors.
- what was verified (real output ref):
  - `python -m src.ingestion.run`: parsed 1,981 ongoing rows, 9 completed rows, 55 newly added rows.
  - `pytest -v tests/test_ingestion_april.py`: 6 passed in 0.23s. Hard verification gate passed:
    - 1,981 ongoing projects (exact)
    - 17 ministries, 22 sectors (exact)
    - Original Cost: Rs 3,712,662.01 Cr (exact)
    - Revised Cost: Rs 4,278,402.37 Cr (~42.78 lakh Cr)
    - Cumulative Expenditure: Rs 2,036,107.49 Cr (~20.36 lakh Cr)
- docs updated:
  - `docs/03_DATA_INVENTORY.md` (filled Section A file manifest with 13 held months + confirmed Section E anchors)
  - `docs/steps/STEP_01_ingestion.md` (marked DONE with verify output)
  - `PROGRESS.md` (ticked STEP_01, moved current step to STEP_02)
- decisions / notes:
  - Relocated all Flash Report PDFs into `reports/` folder.
  - Discovered structural evolution: 2025-07 to 2025-11 use Table 4 for Ongoing (MoRTH excluded), transitioning in late 2025 to Table 6 structure (150-168 pp).

## 2026-09-15 — STEP_00 — Repo & Environment Setup
- what changed (code):
  - Relocated all 14 Flash Report PDFs to `reports/`.
  - Created Python 3.12 `.venv` and pinned dependencies in `requirements.txt`.
  - Configured `pyproject.toml` for `black` (line length 100), `ruff` (linter rules E, W, F, I, UP), and `pytest`.
  - Updated `.gitignore` to protect government data, parquet/csv/xlsx, and docs.
  - Added `src/common/io.py` for parquet/csv DataFrame operations with auto-directory creation.
  - Added `REPORTS` directory to `src/common/config.py`.
- what was verified (real output ref):
  - `pip install -r requirements.txt` succeeded.
  - `ruff check .` passed cleanly.
  - `black --check .` passed cleanly.
  - `pytest -q` ran with 0 failures (1 skipped placeholder).
  - `docker compose config` validated successfully for `postgres:16` service.
- docs updated:
  - `docs/steps/STEP_00_repo_setup.md` (marked DONE with verify output)
  - `PROGRESS.md` (ticked STEP_00)
- decisions / notes:
  - Used Python 3.12 via Apple Silicon native runtime.

## 2026-09-15 — STEP_-- — Project scaffolding & docs created
- Created repo structure, ANTIGRAVITY.md, full docs/ set, 17 step files, PROGRESS,
  this changelog, code stage stubs, requirements, docker-compose, gitignore.
- No pipeline logic yet.
- docs updated: all (initial creation)
- decisions: two-cycle plan (L1 MVP now, L2 finals later); single target for L1 TBD.

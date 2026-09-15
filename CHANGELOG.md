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

## 2026-09-15 — STEP_02 — Data Validation & Audit Logging
- what changed (code):
  - Created `src/validation/rules.py` with pure validation functions for progress bounds (`progress_out_of_range`), non-negative values (`negative_value`), chronological sequence / sentinel checks (`date_inconsistency`), cost reductions (`cost_revised_down`), and expenditure overruns (`exp_exceeds_cost`).
  - Created `src/validation/run.py` to batch-validate all 35 interim parquet tables across 13 months, attach `data_quality_flag`, and emit `data/interim/validation_report.csv` and `data/interim/validation_log.parquet` (and `.csv`).
  - Added unit and integration test suite `tests/test_validation.py` covering all rule boundary conditions and end-to-end pipeline execution.
- what was verified (real output ref):
  - All 21 tests passed cleanly (`pytest -v`).
  - 19,596 total records processed; 0 records dropped (zero data loss).
  - 4,301 records flagged with 4,588 total issues logged:
    - `cost_revised_down`: 2,767 (known reporting artifact; records preserved)
    - `date_inconsistency`: 1,053 (temporal sequence checks)
    - `exp_exceeds_cost`: 764 (sanctioned cost overrun review flag)
    - `negative_value`: 4 (Jan 2026 MoRTH onboarding negative cumulative expenditures)
    - `progress_out_of_range`: 0 (all physical progress within [0, 100]%)
  - `ruff check .` and `black --check .` 100% clean.
- docs updated:
  - `docs/steps/STEP_02_validation.md`, `PROGRESS.md`, `CHANGELOG.md`
- decisions / notes:
  - Preserved no-deletion rule (Rule 4 of `ANTIGRAVITY.md`). Every anomaly is flagged and logged with human-readable rationale.


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
  - `pytest -v`: all tests passed cleanly.
  - `ruff check .`: all checks passed.
  - `black --check .`: all files cleanly formatted.
- docs updated:
  - `docs/DATA_SHARING.md`, `README.md`, `ANTIGRAVITY.md`, `docs/09_DOC_SYNC_RULES.md`
- decisions / notes:
  - Heavy binary artifacts (`reports/*.pdf`, `data/interim/`, `data/processed/`) are shared across team members and Antigravity agents via DVC remote rather than bloating the main code git repository.

## 2026-09-15 — STEP_01 (Multi-Month Extension) — Multi-Month Ingestion & Non-Circular Table 1 Verification
- what changed (code):
  - Updated `src/ingestion/parser.py`: added dynamic layout detection across Early (Jul-Aug 2025: Table 4 Ongoing) and Modern (Sep 2025-Jul 2026: Table 6 Ongoing, Table 3 Completed, Table 4 Newly Added).
  - Added `parse_table_1_summary` to dynamically extract Table 1 grand totals and MoRTH project counts directly from each PDF for non-circular verification.
  - Handled PDF border column shifts and multi-table-per-page structures in Completed and Newly Added extractions.
  - Updated `src/ingestion/run.py` to batch-process all 13 monthly reports, generate raw parquet files in `data/interim/`, and export `data/interim/ingestion_summary.csv`.
  - Added automated test suite `tests/test_ingestion_multimonth.py` validating non-circular Table 1 grand-total match, published ground truth cross-checks, aggregate cost fidelity, and field integrity across all 13 months.
- what was verified (real output ref):
  - Ingested 13 consecutive monthly reports (July 2025 to July 2026):
    - All Ongoing project counts match Table 1 grand total with 100% precision: Jul-25 (791), Aug-25 (800), Sep-25 (794), Oct-25 (820), Nov-25 (823), Dec-25 (1,392), Jan-26 (1,702), Feb-26 (1,948), Mar-26 (1,941), Apr-26 (1,981), May-26 (1,987), Jun-26 (1,847), Jul-26 (1,775).
    - Original Cost sums match Table 1 published numbers exact to 2 decimal places for all 13 months.
    - Completed tables parsed across all 11 modern months (total 259 realized completions, including 130 in June 2026).
    - Newly Added tables parsed across all 11 modern months (including 203 in Jan-26, 268 in Feb-26).
    - Both Revised Cost and Revised Completion Date confirmed available across all 13 months.
  - `python -m pytest tests/ -v`: 12 passed, 1 skipped in 0.93s.
- docs updated:
  - `docs/03_DATA_INVENTORY.md` (updated Section A manifest, resolved Section C TODOs, updated Section E anchors)
  - `docs/steps/STEP_01_ingestion.md` (updated scope, verify output, DoD)
  - `PROGRESS.md` (updated STEP_01 notes and realized-outcome count)
  - `CHANGELOG.md` (this entry)
- decisions / notes:
  - Confirmed and separated report format axis (`layout_type`: Early Jul-Aug vs Modern Sep+) from coverage axis (`morth_ongoing_count`).
  - Quantified MoRTH onboarding integration jump: 0 projects in Jul-Nov 2025 -> 584 in Dec 2025 -> 863 in Jan 2026 -> 1,108 in Feb 2026 (non-MoRTH baseline stable at ~800-840 projects). Flagged for STEP_03 to anchor MoRTH project trajectories to actual start/approval dates, not first report appearance.

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

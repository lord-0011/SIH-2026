# STEP 01 — Ingestion / Schema Extraction

- **Phase:** 1
- **Status:** DONE   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_00

## Goal
Parse each held monthly source into a normalised raw table (one per month), preserving source month. Split the PDF's paired visual cells (orig/revised cost, approval/start date, orig/revised DoC) into separate columns.

## Scope (do exactly this, nothing extra)
- Multi-month layout-aware parser for all 13 Flash Reports (July 2025 – July 2026).
- Supports Early format (Jul-Aug 2025: Table 4 Ongoing) and Modern format (Sep 2025-Jul 2026: Table 6 Ongoing, Table 3 Completed, Table 4 Newly Added).
- Forward-fill Ministry/Sector from section headers onto each row.
- Output raw parquet tables to `data/interim/`, tagged with source month + source doc.
- Generate `data/interim/ingestion_summary.csv` tracking layout type, MoRTH coverage, project counts, cost aggregates, and month-over-month drop notes.
- Verify against Table 1 grand totals non-circularly.

## Method / approach
Implemented layout-aware parsing in `src/ingestion/parser.py` using `pdfplumber` to extract Ongoing Projects (Table 4 or Table 6 dynamically by title), Table 3 (Completed), and Table 4 (Newly Added). Forward-fills Ministry and Sector from section headers, parses bottom-up multi-line project cells, handles leading/trailing border column shifts, and extracts Table 1 Ministry-wise grand totals directly from each PDF for non-circular verification. Outputs parquet tables and summary CSV to `data/interim/`.

## Verify (paste REAL output, don't summarise)
```
$ python -m pytest tests/ -v
============================= test session starts =============================
platform win32 -- Python 3.12.4, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\krpri\OneDrive\Desktop\SIH2026
configfile: pyproject.toml
plugins: anyio-4.8.0
collected 13 items

tests\test_ingestion_april.py::test_table6_project_counts PASSED         [  7%]
tests\test_ingestion_april.py::test_table6_ministries_and_sectors PASSED [ 15%]
tests\test_ingestion_april.py::test_table6_cost_and_expenditure_aggregates PASSED [ 23%]
tests\test_ingestion_april.py::test_table6_field_integrity PASSED        [ 30%]
tests\test_ingestion_april.py::test_table3_completed_projects PASSED     [ 38%]
tests\test_ingestion_april.py::test_table4_newly_added_projects PASSED   [ 46%]
tests\test_ingestion_multimonth.py::test_all_13_months_present PASSED    [ 53%]
tests\test_ingestion_multimonth.py::test_non_circular_table1_match PASSED [ 61%]
tests\test_ingestion_multimonth.py::test_independent_ground_truth_crosscheck PASSED [ 69%]
tests\test_ingestion_multimonth.py::test_cost_aggregates_match_table1 PASSED [ 76%]
tests\test_ingestion_multimonth.py::test_revised_fields_available_all_months PASSED [ 84%]
tests\test_ingestion_multimonth.py::test_parquet_file_integrity PASSED   [ 92%]
tests\test_no_leakage_placeholder.py::test_no_leakage_placeholder SKIPPED [100%]

======================== 12 passed, 1 skipped in 0.93s ========================
```

## Definition of Done
- [x] Scope implemented across all 13 monthly Flash Reports
- [x] Non-circular Table 1 verification passed 13/13 months
- [x] Parquets generated in `data/interim/` (raw_ongoing, raw_completed, raw_newly_added)
- [x] `data/interim/ingestion_summary.csv` generated with format vs MoRTH coverage axes
- [x] Real verify output pasted
- [x] Docs synced: DATA_INVENTORY.md, STEP_01_ingestion.md, PROGRESS.md, CHANGELOG.md

## Blockers / Questions
None. All 13 months reproduced Table 1 project counts and cost totals with 100% precision. Revised cost and revised completion dates confirmed available across all 13 months. MoRTH integration effect fully surfaced and quantified.

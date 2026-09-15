# STEP 01 — Ingestion / Schema Extraction

- **Phase:** 1
- **Status:** DONE   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_00

## Goal
Parse each held monthly source into a normalised raw table (one per month), preserving source month. Split the PDF's paired visual cells (orig/revised cost, approval/start date, orig/revised DoC) into separate columns.

## Scope (do exactly this, nothing extra)
- Parser for the April PDF's Table 6, Table 3 (Completed), Table 4 (Newly Added).
- Forward-fill Ministry/Sector from section headers onto each row.
- If other months are non-PDF, add a loader per format instead of assuming PDF.
- Output raw tables to data/interim/, tagged with source month + source doc.
- Do NOT clean/validate/match here.

## Method / approach
Implemented `src/ingestion/parser.py` using `pdfplumber` to extract Table 6, Table 3, and Table 4 from Flash Report PDFs. Forward-fills Ministry and Sector from section headers, parses bottom-up multi-line project cells into (project_name, implementing_agency, project_code, legacy_ocms_code, pmgid), and splits paired visual cells (approval/start date, orig/revised DoC, orig/revised cost). Outputs parquet tables to `data/interim/`.

## Verify (paste REAL output, don't summarise)
```
$ .venv/bin/python -m src.ingestion.run
2026-09-15 10:28:59,662 INFO ingestion :: Starting ingestion for FlashReport_April2026.pdf (month: 2026-04)
2026-09-15 10:28:59,662 INFO ingestion.parser :: Opening FlashReport_April2026.pdf for month 2026-04
2026-09-15 10:29:12,064 INFO ingestion.parser :: Parsed Table 6: 1981 rows from FlashReport_April2026.pdf
2026-09-15 10:29:12,079 INFO ingestion.parser :: Parsed Table 3: 9 rows from FlashReport_April2026.pdf
2026-09-15 10:29:14,766 INFO ingestion.parser :: Parsed Table 4: 55 rows from FlashReport_April2026.pdf
2026-09-15 10:29:16,707 INFO ingestion :: Saved ongoing (1981 rows) to /Users/adii/Development/SIH/data/interim/raw_ongoing_2026_04.parquet
2026-09-15 10:29:16,708 INFO ingestion :: Saved completed (9 rows) to /Users/adii/Development/SIH/data/interim/raw_completed_2026_04.parquet
2026-09-15 10:29:16,710 INFO ingestion :: Saved newly_added (55 rows) to /Users/adii/Development/SIH/data/interim/raw_newly_added_2026_04.parquet
2026-09-15 10:29:16,710 INFO ingestion :: Ingestion complete for 2026-04.

$ .venv/bin/pytest -v tests/test_ingestion_april.py
tests/test_ingestion_april.py::test_table6_project_counts PASSED         [ 16%]
tests/test_ingestion_april.py::test_table6_ministries_and_sectors PASSED [ 33%]
tests/test_ingestion_april.py::test_table6_cost_and_expenditure_aggregates PASSED [ 50%]
tests/test_ingestion_april.py::test_table6_field_integrity PASSED        [ 66%]
tests/test_ingestion_april.py::test_table3_completed_projects PASSED     [ 83%]
tests/test_ingestion_april.py::test_table4_newly_added_projects PASSED   [100%]
============================== 6 passed in 0.23s ===============================
```

## Definition of Done
- [x] Scope implemented, nothing extra
- [x] Tests written & passing (parse test that reproduces April anchors (DATA_INVENTORY §E))
- [x] Verify output pasted
- [x] Docs synced: STEP_01_ingestion.md
- [x] PROGRESS.md + CHANGELOG.md updated
- [x] Walkthrough written for review

## Blockers / Questions
None. April 2026 anchors reproduced with 100% precision.

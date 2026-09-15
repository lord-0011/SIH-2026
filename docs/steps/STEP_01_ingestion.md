# STEP 01 — Ingestion / Schema Extraction

- **Phase:** 1
- **Status:** NOT STARTED   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
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
pdfplumber/pdftotext -layout; position/regex parser tuned to observed layout. Multi-line project names handled. Keep raw strings + parsed values so parse bugs are debuggable.

## Verify (paste REAL output, don't summarise)
Parse April → assert exactly 1,981 ongoing rows and aggregate cost totals match DATA_INVENTORY §E within rounding. Print the assertion result.

## Definition of Done
- [ ] Scope implemented, nothing extra
- [ ] Tests written & passing (parse test that reproduces April anchors (DATA_INVENTORY §E))
- [ ] Verify output pasted
- [ ] Docs synced: STEP_01_ingestion.md0
- [ ] PROGRESS.md + CHANGELOG.md updated
- [ ] Walkthrough written for review

## Blockers / Questions
(record here; stop and ask rather than improvising a design decision)

# CHANGELOG — append-only implementation log (newest on top)

Format per entry:
```
## YYYY-MM-DD — STEP_xx — <short title>
- what changed (code)
- what was verified (real output ref)
- docs updated: <list>
- decisions / notes
```

## 2026-09-16 — STEP_06 — Feature Engineering (CUF vs. DERIVED Split & Leakage Invariance)
- what changed (code):
  - `src/features/builder.py`: Feature builder computing 25 engineered features per `(project_id, report_month)`: 13 snapshot CUF features and 12 strictly causal DERIVED features. Implements elapsed duration anchored to `elapsed_months_since_anchor` (preventing mid-window MoRTH clock corruption), trailing expenditure and progress velocity/acceleration, provisional progress stagnation (<0.5%) and recent deterioration (>=2 adverse indicators), first revised date trailing population (mirror of STEP_05 exclusion logic), and cross-project historical sector event rate resolved strictly <= T (M <= T - 3).
  - `src/features/run.py`: Pipeline runner writing `data/processed/features.parquet` (18,860 rows, 27 columns) and `reports/feature_manifest.json` defining independent `cuf_features` and `derived_features` subsets.
  - `tests/test_no_leakage.py`: Replaced placeholder with non-skipping CI suite (5 tests) asserting mathematical invariance of all derived features to future data (> T), negative control demonstrating test failure under intentional leak, strict cross-project sector rate leakage invariance, schedule variance at T isolation, and first-revised date mirror assertion.
  - `tests/test_features_fixture.py`: Non-skipping fixture tests (3 tests) validating CUF formulas, mid-window MoRTH anchor clock preservation, and manifest integrity in CI (<1s).
  - `tests/test_features.py`: Real-data integration tests (3 tests) verifying alignment with panel.parquet, column completeness, and zero infinite values.
  - `tests/test_no_leakage_placeholder.py`: Removed placeholder test file.
- what was verified (real output ref):
  - Total rows in feature table: 18,860 (100% matched with panel keys).
  - Total features engineered: 25 features (13 CUF, 12 DERIVED).
  - Null rates: 23 of 25 features have strictly 0.00% null rate. Planned duration has 18 nulls (0.10%), remaining duration has 11 nulls (0.06%) due to unpopulated raw dates.
  - Leakage invariance: `tests/test_no_leakage.py` passed with 0.0 difference between truncated (<= T) and full (> T) panels.
  - All 91 repository tests passing (`pytest -v`): 91 passed, 0 skipped, 0 failed in 7.03s.
  - Black and Ruff: 100% clean across all 49 repository files.
- docs updated:
  - `docs/04_DATA_SCHEMA.md`, `docs/steps/STEP_07_features.md`, `PROGRESS.md`, `CHANGELOG.md`, `walkthrough.md`.
- decisions / notes:
  - Tagging machine-readable in `reports/feature_manifest.json` with helper functions `get_cuf_feature_names()` and `get_derived_feature_names()`.
  - `progress_stagnation` and `recent_deterioration` flagged as PROVISIONAL / TUNABLE in the manifest.
  - Ready for STEP_07 / STEP_08 (modeling dataset assembly and baseline training).

## 2026-09-16 — STEP_05 — EDA Feasibility Gate & Label Specification Finalization
- what changed (code):
  - `src/eda/eda_gate.py`: Pure EDA analysis engine computing observation depth distributions across baseline vs mid-window cohorts, usable row counts under Scheme A exclusion rule for candidate horizons N in (3, 6, 12), positive event class balances, empirical percentiles for cost escalation and schedule delays, clean Scheme B completed project breakdown, monthly structural breaks, and `compute_schedule_contamination_analysis` decomposing schedule slips into clean transitions vs. administrative first-population artifacts.
  - `src/eda/run.py`: Pipeline runner emitting reproducible empirical findings to `reports/eda_gate_summary.json`.
  - `tests/test_eda_fixture.py`: Dedicated non-skipping CI fixture test suite (4 tests) validating date parsing, observation depth, usable rows, and Scheme B breakdowns on synthetic panel grids.
  - `tests/test_eda.py`: Real-data integration test suite (5 tests) asserting exact sourced facts from `docs/03_DATA_INVENTORY.md` §C and pinning the contamination decomposition (1,120 first-pop artifacts, 2,744 clean transitions).
  - `docs/05_LABEL_SPEC.md`: Finalized specification completely: locked Schedule-Risk at N=3, Y=3; explicit first-population exclusion rule; causal trailing feature candidate note for STEP_06; Scheme B model card honesty caveats (~60 independent realized slips outside June road packages). All TODOs eliminated.
  - `docs/03_DATA_INVENTORY.md`: Resolved all remaining §C TODOs (questions 3 and 6) with sourced reproducible numbers (`grep -rn "confirm-from-data"` returns 0 hits in §C).
- what was verified (real output ref):
  - Schedule contamination decomposition:
    - Out of 3,933 gross forward slips (N=3, Y>=3), 1,120 (28.48%) are first-population artifacts (812 of which occurred in March 2026 alone).
    - 2,744 clean transition positives (69.77% of gross slips, 22.31% positive rate across all 12,300 rows; 33.27% among established projects).
  - Observation depth (2,243 projects): >=3 months: 2,138 (95.32%); >=6 months: 1,948 (86.85%); >=9 months: 768 (34.24%); >=12 months: 639 (28.49%); 13 months: 557 (24.83%). Mid-window arrivals (1,341) have median 7 months and 0 >=9 months by construction.
  - Usable rows & positives under Scheme A:
    - N=3 months: 12,300 usable rows. Cost-risk positives (>0%): 237 (1.93%). Schedule-risk clean positives (>=3 mo): 2,744 (22.31%).
    - N=6 months: 6,258 usable rows. Cost-risk positives: 272 (4.35%).
    - N=12 months: 557 usable rows (drops all 1,341 mid-window arrivals). Non-viable for training.
  - Empirical event base rates:
    - Cost escalation delta: p50 to p98 are all 0.00% (p99 is 15.75%). 98% of 3-month project windows experience zero cost escalation.
    - Schedule delay delta: p50=0.0 mo, p75=4.0 mo, p90=13.0 mo, p95=21.0 mo, p98=36.0 mo, p99=55.0 mo.
  - Scheme B clean anchor (N = 258, effective independent ~ 128):
    - Cost overrun (>0 Cr): 97 (37.60%). Schedule slip (>0 mo): 92 (35.66%). Both: 31 (12.02%). Neither: 100 (38.76%).
  - Structural breaks: In March 2026, revised completion date population jumped from 50.56% to 82.12% (+31.56 percentage points) as MoSPI systematically backfilled revised dates for 616 projects.
  - All 81 repository tests passing (`pytest -v`): 80 passed, 1 skipped in 4.08s.
  - Black and Ruff: 100% clean across all 46 repository files.
- docs updated:
  - `docs/03_DATA_INVENTORY.md`, `docs/05_LABEL_SPEC.md`, `docs/steps/STEP_05_eda.md`, `PROGRESS.md`, `CHANGELOG.md`, `walkthrough.md`.
- decisions / notes:
  - STEP_05 accepted by user. Primary target LOCKED as Schedule-Risk Transition at N=3 months, Y=3 months.
  - First-population events strictly EXCLUDED from the label and reserved as a causal trailing feature for STEP_06.
  - Cost-risk demoted to feature and secondary indicator.
  - Ready to merge STEP_05 and branch STEP_06 from main.

---

## 2026-09-16 — STEP_04 — Build Project-Month Panel & Enforce Reconciliation Identity
- what changed (code):
  - `src/panel/builder.py`: Pure functions module for panel assembly (`parse_state_list`, `compute_elapsed_months`, `classify_project_gaps`, `build_panel_df`). Standardizes ongoing and completed rows, computes elapsed months against `trajectory_anchor_date` (Trap A), leaves missing months empty without forward-filling (Trap B), incorporates all Table 3 completed rows as terminal observed records (Trap C), and enforces the computed reconciliation identity `observed_rows + sum(gaps) == n_projects * n_months`.
  - `src/panel/run.py`: Panel pipeline runner. Assembles `data/processed/panel.parquet` (18,860 rows across 2,243 projects and 13 months) and `data/processed/panel_gaps.csv` (10,299 explicitly classified absent cells). Asserts 0 duplicates on `(project_id, report_month)` and validates anchoring and gap distributions.
  - `tests/test_panel_fixture.py`: Dedicated non-skipping CI fixture test suite (3 tests). Validates Trap A (anchor vs report month), Trap B (missing month semantics with no forward fill), Trap C (completed row presence), state list parsing, and computed reconciliation identity on synthetic multi-month project grids.
  - `tests/test_panel.py`: Real-data integration test suite (6 tests) that skips cleanly in clean CI runners. Asserts computed reconciliation identity, exact totals (18,860 observed + 10,299 gaps == 29,159 grid total), 0 duplicates, project 617907 39-month anchor verification, and completed row schemas.
- what was verified (real output ref):
  - Computed Reconciliation Identity verified exact:
    - 2,243 distinct canonical projects x 13 months = 29,159 grid cells
    - 18,860 observed rows (18,601 ongoing + 259 completed) + 10,299 gap cells == 29,159 [DIFFERENCE = 0].
  - Gap breakdown: 8,593 `not_yet_onboarded`, 684 `completed`, 1,022 `unexplained_gap`, 0 `excluded_quality`.
  - Trap A verified: MoRTH project 617907 anchored to `09/2022` start date computes `elapsed_months_since_anchor = 39.0` in `2025-12` (at 89% progress), not 0.
  - Trap B verified: project 400019 (missing in 2026-07) has 0 rows fabricated in panel, logged as `unexplained_gap`.
  - Trap C verified: all 259 completed records present with `is_completed_this_month = True`, `actual_completion_date` populated, and `physical_progress_pct = 100.0`.
  - All 70 repository tests passing (`pytest -v`): 69 passed, 1 skipped placeholder in 3.48s.
  - Clean runner simulation: `test_panel_fixture.py` passed 100% in 0.56s.
  - Black and Ruff: 100% clean across all 41 repository files.
- docs updated:
  - `docs/steps/STEP_04_panel.md`, `PROGRESS.md`, `CHANGELOG.md`, `walkthrough.md`.
- decisions / notes:
  - The completion month is an OBSERVED row in `panel.parquet` (`is_completed_this_month = True`), so it is NOT a gap. Gaps for a completed project are strictly the months after completion.
  - The single project that reappeared in ongoing after a completed table appearance (Southern Railway 705635 in Feb 2026, then Mar-Jul 2026 ongoing) was observed in all 13 months, contributing 0 post-completion gap cells and explaining the 684 vs 689 gap delta.

---

## 2026-09-16 — STEP_03 — Entity Matching & Canonical Identity Resolution
- what changed (code):
  - `src/matching/matcher.py`: Pure entity matching engine. Implements direct join on `project_code` (`canonical_project_id = project_code`, `match_confidence = "exact_code"`), and fallback cascade exception handler for records lacking `project_code`. Enforces that distinct `project_code`s are never merged into one canonical ID.
  - `src/matching/run.py`: Pipeline runner. Loads 13 months of validated ongoing records (18,601 rows), resolves canonical project IDs, computes `first_appearance_month`, flags `is_mid_window_arrival` (all 1,341 Dec+ arrivals) and `is_morth_onboarded_mid_window` (1,187 MoRTH), extracts non-null `trajectory_anchor_date` for 100% of mid-window arrivals, asserts concurrency and no-merge invariants across all 13 months, and outputs `matched_ongoing_*.parquet`, `canonical_projects.parquet`, and `matching_audit.csv`.
  - `tests/test_matching_fixture.py`: Dedicated non-skipping CI fixture suite (6 tests). Includes adversarial Bokaro vs Bhilai legacy-swap anomaly test (two projects in different months sharing legacy code `N12000133`), umbrella corridor split test, fallback exception handler test, and concurrency invariant test.
  - `tests/test_matching.py`: Full 13-month real data verification suite (7 tests). Asserts 100% exact code matches across 18,601 rows, 2,243 distinct canonical projects, 0 duplicates per month, 0 cross-month renames, 26 single-month vs 30 corpus-wide umbrella legacy codes reconciled (identifying the 4 swap codes `N12000133`, `N12000134`, `N12000135`, `N22000602`), and valid anchor dates for all 1,341 mid-window arrivals.
- what was verified (real output ref):
  - 100% exact code match rate across all 18,601 ongoing records (0 null canonical IDs).
  - Exactly 2,243 distinct canonical projects across the 13-month corpus.
  - Zero cross-month renames: `(legacy_ocms_code, project_name)` maps to multiple `project_code`s: exactly 0.
  - Reconciled umbrella legacy codes: 26 within any single month; 30 across pooled 13 months.
  - Mid-window arrivals: exactly 1,341 (1,187 MoRTH + 154 other ministries), 100% populated with `trajectory_anchor_date`.
  - All 60 unit/integration tests passed locally in 3.99s.
  - In clean runner simulation: `test_matching_fixture.py` passed 100%; data-dependent suite skipped cleanly.
  - Black and Ruff: 100% clean across all 38 repository files.
- docs updated:
  - `docs/steps/STEP_03_matching.md`, `docs/03_DATA_INVENTORY.md` §C#5, `PROGRESS.md`, `CHANGELOG.md`, `walkthrough.md`.
- decisions / notes:
  - Matching is a direct join on `project_code`, not a fuzzy cascade. Legacy code is one-to-many and occasionally reassigned across plants by MoSPI, so it must never be used to collapse project identities.
  - All 1,341 mid-window arrivals (MoRTH and non-MoRTH alike) are anchored to their actual approval/start dates to prevent misrepresenting legacy projects as new in STEP_04.

---

## 2026-09-15 — CI_ARCHITECTURE — Decouple CI from DVC/Cache & Add Committed PDF Fixtures
- what changed (code):
  - `.github/workflows/ci.yml`: Removed stale `Cache interim data` and conditional `Run Multi-Month Ingestion` steps. CI now runs clean and deterministically on every runner without stale cache pollution.
  - Added committed 1-page sample PDF fixture `tests/fixtures/sample_table6_page.pdf` (extracted from actual February 2026 report with 20 real ongoing projects including legacy codes and dash placeholders).
  - Created `tests/test_ingestion_fixture.py` (9 tests) testing end-to-end table extraction on `sample_table6_page.pdf` and parsing rules across all historical layout patterns (Patterns A, B, C, dashes).
  - Added clean skip guards in `tests/test_ingestion_multimonth.py` (`summary_df` fixture) and `tests/test_validation.py` (`test_pipeline_integration_real_data`) when full DVC-tracked datasets / 13 PDFs are absent.
- what was verified (real output ref):
  - GitHub Actions Run [#35000903149](https://github.com/lord-0011/SIH-2026/actions/runs/35000903149) completed **SUCCESS** (Job 104488750135: all steps green).
  - In CI: 25 tests PASSED (all fixture and pure rule tests), 14 tests SKIPPED cleanly (April and multimonth data suites).
  - Locally: all 38 tests PASSED, 1 skipped placeholder (`pytest -v`).
  - `ruff check .` and `black --check .`: 100% clean across all 34 files.
- docs updated:
  - `CHANGELOG.md`, `PROGRESS.md`, `walkthrough.md`
- decisions / notes:
  - CI must never assert against cached real data it cannot deterministically reproduce. Code-coupled coverage belongs to committed fixtures; heavy 13-month data tests belong to the local pre-merge gate.



## 2026-09-15 — STEP_01 & STEP_02 — Parser Project Code Resolution & Granular Validation Refactor
- what changed (code):
  - Fixed `src/ingestion/parser.py` (`parse_table6_project_cell`): properly handles single-parenthesized legacy code lines at cell bottom (introduced by MoSPI in Feb/Mar 2026 before PMGID was added in Apr 2026). Swallowed project codes restored across all tables.
  - Added regression test `test_project_code_completeness_all_months` in `tests/test_ingestion_multimonth.py` asserting strict 0.0% missing-rate on `project_code` across all 13 months.
  - Refactored `src/validation/rules.py` with granular flag taxonomy:
    - Split `date_inconsistency` into:
      - `date_impossible`: chronological impossibilities (`orig < start`, `act < start`, `orig < approval`) and sentinel years (<1970).
      - `start_before_approval`: administrative reporting convention (work start prior to formal cabinet sanction; kept).
      - `schedule_advanced`: schedule acceleration signal (revised completion earlier than original; kept as positive signal for STEP_05).
    - Split downward cost revisions into:
      - `implausible_cost_revision`: extreme reductions >90% (`revised < 0.1 * original`, e.g. project 618886: 238.66 -> 0.1), flagging potential data-entry/contract unbundling artifact.
      - `cost_revised_down`: legitimate descoping / tender savings.
  - Added dedicated fixture test suite `tests/test_validation_fixtures.py` exercising all split rules and boundary conditions.
- what was verified (real output ref):
  - All 29 tests passing (`pytest -v`):
    - `test_ingestion_april.py`: 6 passed
    - `test_ingestion_multimonth.py`: 7 passed (including 0% project_code missing assertion)
    - `test_validation.py`: 9 passed
    - `test_validation_fixtures.py`: 7 passed
  - Identifier completeness across all 13 months:
    - `project_code` missing-rate = 0.0% across all 13 months (0 missing rows in Feb/Mar, down from 758 and 752).
    - Legacy OCMS codes extracted: 1,190 in Feb 2026, 1,189 in Mar 2026, 1,184 in Apr 2026, 1,170 in May 2026.
    - Zero rows missing all 3 identifiers across entire corpus.
  - Real validation metrics across 19,596 records (0 dropped):
    - `cost_revised_down`: 2,738
    - `exp_exceeds_cost`: 764
    - `start_before_approval`: 633
    - `schedule_advanced`: 332
    - `date_impossible`: 88
    - `implausible_cost_revision`: 29 (affecting 4 distinct projects including 618886)
    - `negative_value`: 4
    - `progress_out_of_range`: 0
  - `ruff check .` and `black --check .`: 100% clean.
- docs updated:
  - `docs/04_DATA_SCHEMA.md`, `docs/steps/STEP_02_validation.md`, `PROGRESS.md`, `CHANGELOG.md`
- decisions / notes:
  - Preserved no-deletion rule (Rule 4 of `ANTIGRAVITY.md`). Schedule acceleration (`schedule_advanced`) is recognized as a signal, not a defect. Implausible downward cost crashes (>90%) are separated from standard descoping.


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

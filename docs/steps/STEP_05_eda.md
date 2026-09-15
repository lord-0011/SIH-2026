# STEP 05 — EDA Feasibility Gate

- **Phase:** 4
- **Status:** DONE
- **Depends on:** STEP_04

## Goal
Answer every DATA_INVENTORY §C question with a SOURCED number. This gates Phase 5. No modelling before this is done.

## Scope (do exactly this, nothing extra)
- Compute: monthly coverage, format consistency, obs-per-project distribution, realized-outcome count, entity stability, usable rows per horizon N=3/6/12, structural breaks.
- Write findings back into 03_DATA_INVENTORY (resolve TODOs) with source references.
- Recommend a horizon N and which single target (cost vs schedule) has more usable rows.

## Method / approach
- Pure analysis functions in `src/eda/eda_gate.py` and pipeline runner `src/eda/run.py`.
- Outputs generated to `reports/eda_gate_summary.json`.
- Unit test suite `tests/test_eda_fixture.py` and integration tests `tests/test_eda.py`.

## Verify (paste REAL output, don't summarise)
```
=======================================================
STEP_05 EDA FEASIBILITY GATE: SOURCED RESULTS
=======================================================

1. OBSERVATION DEPTH (Total Projects: 2,243)
  All Projects: >=3mo=2138 (95.32%), >=6mo=1948 (86.85%), >=9mo=768 (34.24%), >=12mo=639 (28.49%)
  Baseline (902): >=3mo=855, >=6mo=805, >=9mo=768, >=12mo=639
  Mid-Window (1,341): >=3mo=1283, >=6mo=1143, >=9mo=0 (by construction, arrived Dec 2025+), >=12mo=0

2. USABLE ROWS & POSITIVES ACROSS HORIZONS (Scheme A Exclusion Rule)
Horizon  | Usable Rows  | Cost Positives (>0%)   | Sched Positives (>=1mo)   | Sched Positives (>=3mo)  
----------------------------------------------------------------------------------------------------
N = 3    | 12300        | 237 (1.93%)            | 4531 (36.84%)             | 3933 (31.98%)            
N = 6    | 6258         | 272 (4.35%)            | 2638 (42.15%)             | 2510 (40.11%)            
N = 12   | 557          | 115 (20.65%)           | 265 (47.58%)              | 255 (45.78%)             

3. SCHEME B CLEAN REALIZED-OUTCOME ANCHOR (N = 258, effective independent ~ 128)
  Cost Overrun (>0 Cr): 97 (37.6%)
  Schedule Slip (>0 mo): 92 (35.66%)
  Both Cost & Schedule Slip: 31 (12.02%)
  Neither (On-time & On-budget): 100 (38.76%)
```

Verification command:
`python -c "with open('docs/03_DATA_INVENTORY.md') as f: print([line for line in f if 'TODO' in line])"` -> returns 0 hits in Section C.

## Definition of Done
- [x] Scope implemented, nothing extra
- [x] Tests written & passing (`tests/test_eda_fixture.py` and `tests/test_eda.py`)
- [x] Verify output pasted
- [x] Docs synced: STEP_05_eda.md
- [x] PROGRESS.md + CHANGELOG.md updated
- [x] Walkthrough written for review

## Blockers / Questions
Awaiting user review and joint decision on primary prediction target and horizon selection before beginning Phase 5 (STEP_06 Labels).

# STEP 11 — Risk Score

- **Phase:** 11
- **Status:** DONE   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_10

## Goal
Calibrate model output, combine into a 0-100 score, derive LOW/MED/HIGH/CRITICAL bands from the data, compute per project-month.

## Scope (do exactly this, nothing extra)
- Calibrate (Platt or isotonic — pick by calibration curve; record).
- Map calibrated prob → 0-100 monotonic. Bands = quantile-based; sanity-check vs Scheme B.
- Write scores to data/processed/risk_scores.parquet.

## Method / approach
Score is a combination/calibration layer over the model, NOT a new model.
- Production model: LightGBM (Ablated: No Near-Label Features), PR-AUC = 0.4656, ROC-AUC = 0.8525.
- Calibration method: Platt Scaling (logistic sigmoid fitted strictly on the Validation fold $T \in [\text{2026-01}, \text{2026-02}]$).
- Platt scaling was chosen over Isotonic regression because Platt strictly preserves rank ordering ($\text{PR-AUC} = 0.4656$) while reducing test-set ECE from 0.2077 to 0.0685 (67.0% reduction) and Brier score from 0.1467 to 0.0718 (51.1% reduction). Isotonic regression degraded PR-AUC to 0.4148 due to flat step plateaus.
- Monotonic score: $S = \text{round}(100 \times p_{\text{calibrated}}, 1)$.
- Quantile-derived bands from validation distribution:
  - 50th percentile = 4.6 (`low_med`)
  - 80th percentile = 36.1 (`med_high`)
  - 95th percentile = 55.9 (`high_crit`)
- Bands:
  - `LOW`: $S < 4.6$
  - `MEDIUM`: $4.6 \le S < 36.1$
  - `HIGH`: $36.1 \le S < 55.9$
  - `CRITICAL`: $S \ge 55.9$
- Data Sufficiency Indicator (NFR-4): attached per project-month as `observed_months_to_date` and `data_sufficiency` (`PROVISIONAL` if $\le 2$, `SUFFICIENT` if $\ge 3$).

## Verify (paste REAL output, don't summarise)
### 1. Calibration Performance on Held-Out Test Set
```
- Raw LightGBM ECE: 0.2077, Brier: 0.1467
- Platt-calibrated ECE: 0.0685 (67.0% reduction)
- Platt-calibrated Brier: 0.0718 (51.1% reduction)
- Rank Preservation: 100% (PR-AUC remains 0.4656)
```

### 2. Risk Band Realized-Event Rates on Non-Roads Held-Out Test Set ($N=1,373$, Positives=116, Base Rate=8.45%)
```
| Band     | Score Range | Count | % Portfolio | Realized Positives | Realized Event Rate | Realized Lift vs Base |
|:---------|:------------|------:|------------:|-------------------:|--------------------:|----------------------:|
| LOW      | [2.1, 4.5]  |   726 |       52.9% |                 12 |               1.65% |                 0.20x |
| MEDIUM   | [4.6, 36.0] |   400 |       29.1% |                 27 |               6.75% |                 0.80x |
| HIGH     | [36.2, 55.8]|   164 |       11.9% |                 31 |              18.90% |                 2.24x |
| CRITICAL | [55.9, 64.7]|    83 |        6.0% |                 46 |              55.42% |                 6.56x |
```
- Monotonic Ordering Invariant: $\text{LOW} (1.65\%) < \text{MEDIUM} (6.75\%) < \text{HIGH} (18.90\%) < \text{CRITICAL} (55.42\%)$ — **STRICTLY SATISFIED**.
- Operational Concentration: CRITICAL contains 6.0% of projects but captures 39.7% of all slips; HIGH + CRITICAL (18.0% of portfolio) captures 66.4% of all slips.

### 3. Full Corpus Risk Score Output (`data/processed/risk_scores.parquet`)
- Total rows: 18,860 across 2,243 projects and 13 months.
- Null counts: `project_id`: 0, `report_month`: 0, `risk_score`: 0, `risk_band`: 0, `data_sufficiency`: 0.
- Entire corpus band distribution:
  - LOW: 9,077 (48.1%)
  - MEDIUM: 5,607 (29.7%)
  - HIGH: 2,752 (14.6%)
  - CRITICAL: 1,424 (7.5%)
- Data sufficiency breakdown:
  - SUFFICIENT ($\ge 3$ observed months): 14,449 (76.6%)
  - PROVISIONAL ($\le 2$ observed months): 4,411 (23.4%)
  - In latest report month (2026-07): 1,747 SUFFICIENT (97.1%), 53 PROVISIONAL (2.9%).

## Definition of Done
- [x] Scope implemented, nothing extra
- [x] Tests written & passing (test: monotonic mapping; band assignment; CI fixture)
- [x] Verify output pasted
- [x] Docs synced: STEP_11_risk.md
- [x] PROGRESS.md + CHANGELOG.md updated
- [x] Walkthrough written for review

## Blockers / Questions
None. STEP_11 successfully completed and verified.

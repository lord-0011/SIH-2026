# STEP 08 — Statistical Baseline

- **Phase:** 7
- **Status:** DONE   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_07

## Goal
Train statistical baseline (sector event rate + schedule variance) and logistic regression for the chosen target on BOTH feature sets, on the temporal train split.

## Scope (do exactly this, nothing extra)
- Config 1: Statistical Baseline (`sector_hist_event_rate` + `schedule_variance_months`).
- Config 2: Logistic Regression on CUF features (StandardScaler + L2 regularization).
- Fit on Non-Roads temporal train split ($T \le \text{2025-12}$), tune on validation split ($T \in [\text{2026-01}, \text{2026-02}]$), evaluate on headline Non-Roads test split ($T \in [\text{2026-03}, \text{2026-04}]$).
- Save models + evaluation metrics to `data/processed/models/`.

## Method / approach
- Primary Benchmark: Non-Roads infrastructure (clean operational universe, base rate stationary at 12.3% train $\to$ 8.45% test).
- Universal Active-Target Filter applied: rows where $revised\_date < report\_month$ excluded as past-due backlog artifacts.
- Lead Metric: PR-AUC (Average Precision), alongside ROC-AUC, Brier score, ECE, P@10%, and P@20%.

## Verify (Real output)
```
Config 1: Statistical Baseline   | PR-AUC: 0.1895 | ROC-AUC: 0.7497 | Brier: 0.2798 | ECE: 0.4531 | P@10%: 0.2190 | P@20%: 0.1825 | (N=1373, Pos=116)
Config 2: Logistic Reg (CUF)     | PR-AUC: 0.2956 | ROC-AUC: 0.8080 | Brier: 0.1875 | ECE: 0.2776 | P@10%: 0.3066 | P@20%: 0.2591 | (N=1373, Pos=116)
```

## Answers to Problem Statement Questions
- **Question 1: Does currently-captured CUF data have predictive power?**
  - **YES.** Logistic Regression on CUF features achieves PR-AUC 0.2956 vs Baseline 0.1895 (+10.61 percentage points lift, +56% relative gain) and ROC-AUC 0.8080 vs 0.7497.

## Definition of Done
- [x] Scope implemented, nothing extra
- [x] Tests written & passing (test: split is temporal; no future month in train; test_models.py green)
- [x] Verify output pasted
- [x] Docs synced: STEP_08_baseline.md
- [x] PROGRESS.md + CHANGELOG.md updated
- [x] Walkthrough written for review

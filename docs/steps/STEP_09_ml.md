# STEP 09 — ML Model

- **Phase:** 8
- **Status:** DONE   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_08

## Goal
Train gradient-boosting model (LightGBM) on both feature sets (CUF-only and Full features), same temporal split as baseline.

## Scope (do exactly this, nothing extra)
- Lib: LightGBM (lightgbm==4.7.0).
- Fit Config 3: LightGBM (CUF-only) and Config 4: LightGBM (CUF + Derived).
- Tune hyperparameters via VAL fold only (`num_leaves`, `max_depth`, `learning_rate`).
- Near-Label Ablation: evaluate best model WITH vs WITHOUT `schedule_variance_months` and `delay_to_date_months`.
- Secondary Transfer: evaluate Non-Roads-trained model on Roads test set.

## Method / approach
- Gradient Boosting Classifier with balanced class weights.
- Early stopping / validation tuning on Val block ($T \in [\text{2026-01}, \text{2026-02}]$).
- Evaluated on headline Non-Roads test set ($T \in [\text{2026-03}, \text{2026-04}]$; $N=1,373$, Positives=116).

## Verify (Real output)
```
Config 3: LightGBM (CUF)         | PR-AUC: 0.4180 | ROC-AUC: 0.8408 | Brier: 0.1386 | ECE: 0.1924 | P@10%: 0.4234 | P@20%: 0.2810 | (N=1373, Pos=116)
Config 4: LightGBM (Full)        | PR-AUC: 0.4100 | ROC-AUC: 0.8433 | Brier: 0.1443 | ECE: 0.2004 | P@10%: 0.4161 | P@20%: 0.2737 | (N=1373, Pos=116)

=== NEAR-LABEL ABLATION: NON-ROADS TEST SET ===
WITH Near-Label Features    | PR-AUC: 0.4100 | ROC-AUC: 0.8433 | P@10%: 0.4161 | P@20%: 0.2737
WITHOUT Near-Label Features | PR-AUC: 0.4656 | ROC-AUC: 0.8525 | P@10%: 0.4453 | P@20%: 0.2883
PR-AUC Delta: +0.0556 — Model does NOT collapse without near-label features; it genuinely predicts upcoming slippage from trajectory dynamics.

=== SECONDARY TRANSFER TO ROADS TEST SET ===
Caveat: Roads onboarded Dec 2025 with mostly expired backlog dates; only 2 clean post-baseline months exist, so Roads is reported as a transfer test of the Non-Roads-trained model, NOT an independently trained/validated result.
Config 3: LightGBM (CUF) on Roads Transfer  | PR-AUC: 0.6694 | ROC-AUC: 0.7850 | Brier: 0.1974 | ECE: 0.1123 | P@10%: 0.6947 | P@20%: 0.6816 | (N=1901, Pos=827)
Config 4: LightGBM (Full) on Roads Transfer | PR-AUC: 0.6736 | ROC-AUC: 0.7835 | Brier: 0.2023 | ECE: 0.1251 | P@10%: 0.7158 | P@20%: 0.6842 | (N=1901, Pos=827)
```

## Answers to Problem Statement Questions
- **Question 2: Does Machine Learning beat the statistical baseline?**
  - **YES, decisively.** LightGBM achieves PR-AUC 0.4180 vs Baseline 0.1895 (more than 2x lift) and Logistic Regression 0.2956. At top 10% risk tier, Precision@10% reaches 42.34% (a 5x lift over the 8.45% base rate).

## Definition of Done
- [x] Scope implemented, nothing extra
- [x] Tests written & passing (tests/test_models.py 100% green)
- [x] Verify output pasted
- [x] Docs synced: STEP_09_ml.md
- [x] PROGRESS.md + CHANGELOG.md updated
- [x] Walkthrough written for review

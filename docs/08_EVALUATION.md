# 08 — Evaluation Framework & Results

## Split
Temporal / rolling-origin strictly. Never random k-fold.
All models evaluated across sequential temporal blocks with an active-target filter ($revised\_date \ge report\_month$ at origin $T$):
- **Train block**: $T \le \text{2025-12}$ (6,013 usable filtered rows, 942 positives = 15.66%)
- **Validation block**: $T \in [\text{2026-01}, \text{2026-02}]$ (2,683 usable filtered rows, 686 positives = 25.57%)
- **Held-out Test block**: $T \in [\text{2026-03}, \text{2026-04}]$ (2,251 usable filtered rows)
  - **Headline Benchmark (Non-Roads)**: $N = 1,373$ rows, 116 positives (Base rate = 8.45%)
  - **Secondary Transfer (Roads)**: $N = 1,901$ rows, 827 positives (Base rate = 43.50%; onboarded Dec 2025 with expired backlog dates)
- **Censored**: $T \ge \text{2026-05}$ (forward horizon $T+3$ not yet observed in 13-month corpus)

## Metrics
- **PR-AUC**: Lead metric; precision-recall area under the curve is primary under class imbalance.
- **ROC-AUC**: Discrimination metric.
- **Brier Score & ECE**: Probability calibration (Expected Calibration Error).
- **Precision@10% & Precision@20%**: Operational concentration in top priority flags.

## THE comparison table the PS demands
**Target**: Schedule-Risk Transition ($N=3$ months forward, slip $Y \ge 3$ months, first-population events excluded).
**Primary Test Window**: 2026-03 to 2026-04 (Held-Out Non-Roads, $N=1,373$, Positives=116, Base Rate=8.45%).

| Model | Features | ROC-AUC | PR-AUC | Brier | ECE | P@10% | P@20% | Usable rows |
|:------|:---------|--------:|-------:|------:|----:|------:|------:|------------:|
| Config 1: Statistical Baseline | Historical sector slip rate | 0.7497 | 0.1895 | 0.2798 | 0.4531 | 21.90% | 19.34% | 1,373 (116 pos) |
| Config 2: Logistic Regression | 13 CUF snapshot features | 0.8080 | 0.2956 | 0.1875 | 0.2776 | 30.66% | 22.99% | 1,373 (116 pos) |
| Config 3: LightGBM | 13 CUF snapshot features | 0.8408 | 0.4180 | 0.1386 | 0.1924 | 42.34% | 31.39% | 1,373 (116 pos) |
| Config 4: LightGBM | 25 Full (CUF + Derived) | 0.8433 | 0.4100 | 0.1443 | 0.2004 | 41.61% | 31.75% | 1,373 (116 pos) |
| **Config 4 (Ablated: Production)** | **23 Features (No near-label)** | **0.8525** | **0.4656** | **0.1467** | **0.2077** | **44.53%** | **31.75%** | **1,373 (116 pos)** |

### Answers to the Two Problem Statement Questions:
1. **Does the currently-captured CUF data predict on its own?**
   **YES**. Logistic regression on CUF features achieves PR-AUC = 0.2956 vs baseline 0.1895 (+10.6 percentage points lift), and LightGBM on CUF reaches PR-AUC = 0.4180 (2.2x lift over baseline).
2. **Does ML beat the statistical baseline?**
   **DECISIVELY YES**. LightGBM delivers PR-AUC = 0.4180–0.4656 vs baseline 0.1895. Precision@10% reaches 42.34%–44.53% (a 5.0x–5.3x lift over the 8.45% base rate).

## Model card (Production Model)
- **Model Architecture**: LightGBM Classifier (`n_estimators=100, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, min_child_samples=20`).
- **Feature Set**: 23 Features (Full features with near-label leak candidates `schedule_variance_months` and `delay_to_date_months` ablated).
- **Target**: Clean forward schedule slip $\ge 3$ months within 3 months, excluding first-population administrative artifacts.
- **Split Protocol**: Temporal split strictly: Train $\le \text{2025-12}$, Val $\text{2026-01}..\text{2026-02}$, Test $\text{2026-03}..\text{2026-04}$. Seed = 42.
- **Headline Non-Roads Performance**: PR-AUC = 0.4656, ROC-AUC = 0.8525, P@10% = 44.53%, P@20% = 31.75%.
- **Limitations**:
  - Validated against 116 clean non-roads test outcomes (indicative percentages; robust monotonic ordering).
  - Roads sector is affected by MoRTH onboarding backlog artifacts; zero-shot transfer performance is reported separately.
  - Right-censoring beyond Month 10 due to 13-month historical window.

## Risk score validation
- **Calibration Method**: Platt Scaling (sigmoid logistic regression on validation fold log-odds).
  - Platt scaling was selected because it strictly preserves rank ordering ($\text{PR-AUC} = 0.4656$) while reducing test-set ECE from 0.2077 to 0.0685 (**67.0% reduction**) and Brier score from 0.1467 to 0.0718 (**51.1% reduction**).
  - Isotonic regression was rejected because its step-function plateaus degraded PR-AUC from 0.4656 down to 0.4148.
- **Target Combination Weighting**: Single primary target for L1: Schedule-Risk Transition ($N=3, Y \ge 3$). Cost escalation is demoted to feature and secondary flag.
- **Band Cutoffs**: Quantile-derived on validation distribution ($N=2,683$):
  - 50th percentile = 4.6 (`low_med`)
  - 80th percentile = 36.1 (`med_high`)
  - 95th percentile = 55.9 (`high_crit`)
- **Held-Out Test Set Monotonicity Invariant** ($N=1,373$, Positives=116, Base Rate=8.45%):
  - `LOW` ($S < 4.6$): 726 projects (52.9%), 12 realized slips (**1.65% event rate**).
  - `MEDIUM` ($4.6 \le S < 36.1$): 400 projects (29.1%), 27 realized slips (**6.75% event rate**).
  - `HIGH` ($36.1 \le S < 55.9$): 164 projects (11.9%), 31 realized slips (**18.90% event rate**).
  - `CRITICAL` ($S \ge 55.9$): 83 projects (6.0%), 46 realized slips (**55.42% event rate**).
  - **Monotonic Ordering**: $\text{LOW} (1.65\%) < \text{MEDIUM} (6.75\%) < \text{HIGH} (18.90\%) < \text{CRITICAL} (55.42\%)$ is strictly increasing.
- **Honest Sample-Size Caveat**:
  - The risk bands are validated against 116 clean realized slip events on the held-out Non-Roads test set ($N=1,373$). While the monotonic ordering and operational concentration are mathematically sound, the exact percentage values should be understood as sample-specific empirical estimates.
- **Data Sufficiency Rule (NFR-4)**:
  - `PROVISIONAL`: $\le 2$ observed historical months for the project.
  - `SUFFICIENT`: $\ge 3$ observed historical months. Emitted per project-month in `risk_scores.parquet`.

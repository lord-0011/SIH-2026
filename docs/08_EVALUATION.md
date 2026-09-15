# 08 — Evaluation Framework & Results

## Split
Temporal / rolling-origin only. Record exact month boundaries + row counts per block.
Never random k-fold. `TODO(confirm-from-data)`: fill block boundaries after Phase 4.
- Train: months __ to __ (__ rows)
- Val (hyperparams): months __ to __ (__ rows)
- Test (held out): months __ to __ (__ rows)

## Metrics (report ALL, with sample size beside each)
- ROC-AUC — discrimination (don't rely on alone; imbalance-optimistic)
- PR-AUC — main metric; positives are the rare cases that matter
- Calibration (Brier / curve) — "80%" must mean ~80%; matters because score is shown as prob
- Early-warning lead time — months before actual event the flag first fires (Scheme B)
- False-alarm rate — fraction of high-risk flags that don't materialise; high → users ignore it

## THE comparison table the PS demands (fill after Phase 9)
Target: __________ (cost-risk / schedule-risk). Test window: ______. 

| Model | Features | ROC-AUC | PR-AUC | Brier | Lead time | False-alarm | Usable rows |
|-------|----------|---------|--------|-------|-----------|-------------|-------------|
| Logistic reg | CUF-only | | | | | | |
| Logistic reg | CUF+derived | | | | | | |
| Gradient boost | CUF-only | | | | | | |
| Gradient boost | CUF+derived | | | | | | |

Read two answers off this table (report even if "no"):
1. Does CUF+derived beat CUF-only? (does feature engineering help)
2. Does ML beat the statistical baseline? (does model flexibility help)

## Model card (fill for the chosen production model)
- Target, horizon N, thresholds X/Y (from LABEL_SPEC)
- Training window, test window, seed
- Metrics above + honest sample size
- Limitations: censoring, ~19mo data, our data ≠ full OCMS (master doc §23)

## Risk score validation
- Calibration method used: Platt / isotonic (record which + why)
- Cost/schedule combination weighting + how validated (against Scheme B if available)
- Band cutoffs (LOW/MED/HIGH/CRITICAL): values + how derived (quantile) + sanity check

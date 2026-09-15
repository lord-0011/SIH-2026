"""Evaluation metrics for the PAIMANA Predictive Risk Platform.

Computes:
  - PR-AUC (Average Precision) — Lead Metric
  - ROC-AUC
  - Brier Score
  - Expected Calibration Error (ECE)
  - Precision@10%
  - Precision@20%
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error across n_bins equal-width probability bins."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_indices = np.digitize(y_prob, bins) - 1
    ece = 0.0
    n = len(y_true)
    if n == 0:
        return 0.0

    for b in range(n_bins):
        mask = bin_indices == b
        bin_count = np.sum(mask)
        if bin_count > 0:
            bin_acc = np.mean(y_true[mask])
            bin_conf = np.mean(y_prob[mask])
            ece += (bin_count / n) * np.abs(bin_acc - bin_conf)

    return float(ece)


def precision_at_k(y_true: np.ndarray, y_prob: np.ndarray, k_pct: float) -> float:
    """Compute precision among the top k_pct percent of predicted probabilities."""
    n = len(y_true)
    if n == 0:
        return 0.0
    k = max(1, int(n * k_pct / 100.0))
    top_indices = np.argsort(y_prob)[::-1][:k]
    return float(np.mean(y_true[top_indices]))


def evaluate_predictions(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    model_name: str = "",
    block_name: str = "",
) -> dict[str, Any]:
    """Compute comprehensive performance and calibration metrics for binary risk predictions."""
    n_total = len(y_true)
    n_pos = int(np.sum(y_true))
    base_rate = float(np.mean(y_true)) if n_total > 0 else 0.0

    if n_total == 0 or n_pos == 0:
        return {
            "model_name": model_name,
            "block_name": block_name,
            "total_samples": n_total,
            "positive_count": n_pos,
            "base_rate": base_rate,
            "pr_auc": None,
            "roc_auc": None,
            "brier_score": None,
            "ece": None,
            "precision_at_10pct": None,
            "precision_at_20pct": None,
        }

    pr_auc = float(average_precision_score(y_true, y_prob))
    roc_auc = float(roc_auc_score(y_true, y_prob))
    brier = float(brier_score_loss(y_true, y_prob))
    ece = compute_ece(y_true, y_prob)
    p10 = precision_at_k(y_true, y_prob, 10.0)
    p20 = precision_at_k(y_true, y_prob, 20.0)

    return {
        "model_name": model_name,
        "block_name": block_name,
        "total_samples": n_total,
        "positive_count": n_pos,
        "base_rate": round(base_rate, 4),
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc_auc, 4),
        "brier_score": round(brier, 4),
        "ece": round(ece, 4),
        "precision_at_10pct": round(p10, 4),
        "precision_at_20pct": round(p20, 4),
    }

"""Stage: models — trains, tunes, and evaluates risk prediction models.

Primary Benchmark: Non-Roads Test Set (Headline).
Secondary Analysis: Zero-Shot Transfer to Roads Test Set.
Ablation: Near-label features removed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

from src.common.io import load_dataframe
from src.common.logging_setup import get_logger
from src.models.trainer import train_and_evaluate_all

log = get_logger("models.run")


def run(config: dict[str, Any] | None = None) -> Path:
    """Run full modeling stage."""
    log.info("Starting models stage...")

    features_path = Path("data/processed/features.parquet")
    labels_path = Path("data/processed/labels.parquet")

    if not features_path.exists():
        raise FileNotFoundError(f"Features file not found at {features_path}")
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels file not found at {labels_path}")

    features_df = load_dataframe(features_path)
    labels_df = load_dataframe(labels_path)

    output = train_and_evaluate_all(features_df, labels_df)
    results = output["results"]
    models = output["models"]

    # Save artifacts
    models_dir = Path("data/processed/models")
    models_dir.mkdir(parents=True, exist_ok=True)

    results_path = models_dir / "evaluation_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    log.info("Saved evaluation results to %s", results_path)

    for m_name, m_obj in models.items():
        joblib.dump(m_obj, models_dir / f"{m_name}.joblib")
    log.info("Saved model checkpoints to %s", models_dir)

    # Print Headline Table
    log.info("=== HEADLINE RESULTS: NON-ROADS TEST SET (Clean Operational Benchmark) ===")
    headline = results["headline_nonroads_test"]
    for row in headline:
        log.info(
            "%-32s | PR-AUC: %.4f | ROC-AUC: %.4f | Brier: %.4f | ECE: %.4f | P@10%%: %.4f | P@20%%: %.4f | (N=%d, Pos=%d)",
            row["model_name"],
            row["pr_auc"],
            row["roc_auc"],
            row["brier_score"],
            row["ece"],
            row["precision_at_10pct"],
            row["precision_at_20pct"],
            row["total_samples"],
            row["positive_count"],
        )

    # Print Ablation Table
    log.info("=== NEAR-LABEL ABLATION: NON-ROADS TEST SET ===")
    abl = results["near_label_ablation"]
    w_row = abl["with_near_label"]
    wo_row = abl["without_near_label"]
    log.info(
        "WITH Near-Label Features    | PR-AUC: %.4f | ROC-AUC: %.4f | P@10%%: %.4f | P@20%%: %.4f",
        w_row["pr_auc"],
        w_row["roc_auc"],
        w_row["precision_at_10pct"],
        w_row["precision_at_20pct"],
    )
    log.info(
        "WITHOUT Near-Label Features | PR-AUC: %.4f | ROC-AUC: %.4f | P@10%%: %.4f | P@20%%: %.4f",
        wo_row["pr_auc"],
        wo_row["roc_auc"],
        wo_row["precision_at_10pct"],
        wo_row["precision_at_20pct"],
    )
    log.info("PR-AUC Delta: %+.4f — %s", abl["pr_auc_delta"], abl["conclusion"])

    # Print Secondary Transfer Table
    log.info("=== SECONDARY TRANSFER TO ROADS TEST SET ===")
    log.info("Caveat: %s", results["roads_transfer_analysis"]["caveat"])
    for row in results["roads_transfer_analysis"]["test_metrics"]:
        log.info(
            "%-32s | PR-AUC: %.4f | ROC-AUC: %.4f | Brier: %.4f | ECE: %.4f | P@10%%: %.4f | P@20%%: %.4f | (N=%d, Pos=%d)",
            row["model_name"],
            row["pr_auc"],
            row["roc_auc"],
            row["brier_score"],
            row["ece"],
            row["precision_at_10pct"],
            row["precision_at_20pct"],
            row["total_samples"],
            row["positive_count"],
        )

    return results_path


if __name__ == "__main__":
    run()

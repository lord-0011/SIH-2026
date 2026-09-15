"""Stage: risk — computes calibrated 0-100 risk scores, bands, and data sufficiency flags."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

from src.common.io import load_dataframe, save_dataframe
from src.common.logging_setup import get_logger
from src.risk.scorer import generate_risk_scores

log = get_logger("risk.run")


def run(config: dict[str, Any] | None = None) -> Path:
    """Run full risk scoring and calibration stage."""
    log.info("Starting risk scoring stage...")

    features_path = Path("data/processed/features.parquet")
    labels_path = Path("data/processed/labels.parquet")
    panel_path = Path("data/processed/panel.parquet")
    model_path = Path("data/processed/models/model_lightgbm_ablation.joblib")

    for p in [features_path, labels_path, panel_path, model_path]:
        if not p.exists():
            raise FileNotFoundError(f"Required artifact not found: {p}")

    features_df = load_dataframe(features_path)
    labels_df = load_dataframe(labels_path)
    panel_df = load_dataframe(panel_path)
    model = joblib.load(model_path)

    risk_df, summary = generate_risk_scores(
        features_df=features_df,
        labels_df=labels_df,
        panel_df=panel_df,
        model=model,
    )

    # Save outputs
    out_parquet = Path("data/processed/risk_scores.parquet")
    save_dataframe(risk_df, out_parquet)
    log.info("Saved risk scores to %s (%d rows)", out_parquet, len(risk_df))

    # Save calibration summary
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    models_dir = Path("data/processed/models")
    models_dir.mkdir(parents=True, exist_ok=True)

    json_path = reports_dir / "risk_score_calibration.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Also mirror into data/processed/models/
    with open(models_dir / "risk_score_calibration.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    log.info("Saved calibration diagnostics to %s", json_path)

    # Print summary tables
    log.info("=== CALIBRATION DIAGNOSTICS ===")
    cal = summary["calibration_metrics"]
    log.info(
        "ECE Before: %.4f | ECE After: %.4f (Reduction: %.1f%%)",
        cal["test_ece_before"],
        cal["test_ece_after"],
        cal["ece_reduction_pct"],
    )

    log.info(
        "=== RISK BAND VALIDATION ON NON-ROADS TEST SET (N=%d, Pos=%d) ===",
        summary["nonroads_test_band_validation"]["sample_size"],
        summary["nonroads_test_band_validation"]["clean_positives"],
    )
    bands = summary["nonroads_test_band_validation"]["bands"]
    for b_name in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        b = bands[b_name]
        log.info(
            "%-10s | Score Range: [%4.1f, %4.1f] | Count: %4d | Realized Pos: %2d | Realized Rate: %5.2f%%",
            b_name,
            b["min_score"],
            b["max_score"],
            b["count"],
            b["realized_positives"],
            b["realized_event_rate_pct"],
        )

    log.info(
        "Monotonic Ordering Invariant Satisfied: %s",
        summary["nonroads_test_band_validation"]["is_strictly_monotonic_increasing"],
    )

    return out_parquet


if __name__ == "__main__":
    run()

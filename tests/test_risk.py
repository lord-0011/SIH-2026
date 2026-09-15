"""Real-data integration tests for risk scoring and calibration (STEP_11).

Guarded with pytest.skip on clean CI runners lacking DVC assets.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.common.io import load_dataframe

RISK_SCORES_PATH = Path("data/processed/risk_scores.parquet")
CALIBRATION_JSON_PATH = Path("reports/risk_score_calibration.json")


@pytest.fixture(scope="module")
def risk_scores_df() -> pd.DataFrame:
    if not RISK_SCORES_PATH.exists():
        pytest.skip(f"Risk scores not found at {RISK_SCORES_PATH} (DVC-tracked)")
    return load_dataframe(RISK_SCORES_PATH)


@pytest.fixture(scope="module")
def calibration_summary() -> dict:
    if not CALIBRATION_JSON_PATH.exists():
        pytest.skip(f"Calibration summary not found at {CALIBRATION_JSON_PATH} (DVC-tracked)")
    with open(CALIBRATION_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_risk_scores_parquet_completeness(risk_scores_df: pd.DataFrame):
    """Parquet table must have exact 18,860 panel rows and zero nulls in critical score columns."""
    assert len(risk_scores_df) == 18860

    critical_cols = [
        "project_id",
        "report_month",
        "sector",
        "raw_probability",
        "calibrated_probability",
        "risk_score",
        "risk_band",
        "observed_months_to_date",
        "data_sufficiency",
    ]
    for col in critical_cols:
        assert col in risk_scores_df.columns
        assert risk_scores_df[col].isnull().sum() == 0, f"Column {col} has nulls"


def test_calibration_reduces_ece(calibration_summary: dict):
    """Platt calibration must achieve significant ECE reduction on held-out test block."""
    metrics = calibration_summary["calibration_metrics"]
    assert metrics["test_ece_after"] < metrics["test_ece_before"]
    assert metrics["ece_reduction_pct"] >= 50.0  # Expect ~67% reduction


def test_per_band_realized_rate_strict_monotonicity(calibration_summary: dict):
    """INVARIANT: Higher risk bands must have strictly higher realized slip rates on held-out test set."""
    val_data = calibration_summary["nonroads_test_band_validation"]
    assert val_data["is_strictly_monotonic_increasing"] is True

    bands = val_data["bands"]
    rate_low = bands["LOW"]["realized_event_rate_pct"]
    rate_med = bands["MEDIUM"]["realized_event_rate_pct"]
    rate_high = bands["HIGH"]["realized_event_rate_pct"]
    rate_crit = bands["CRITICAL"]["realized_event_rate_pct"]

    assert (
        rate_low < rate_med < rate_high < rate_crit
    ), f"Monotonicity broken: LOW={rate_low}% < MED={rate_med}% < HIGH={rate_high}% < CRIT={rate_crit}%"

    # CRITICAL band must exhibit marked lift over base rate (base ~8.45%)
    assert rate_crit >= 45.0


def test_data_sufficiency_partitioning(risk_scores_df: pd.DataFrame):
    """Data sufficiency must be correctly partitioned between PROVISIONAL and SUFFICIENT."""
    prov = risk_scores_df[risk_scores_df["data_sufficiency"] == "PROVISIONAL"]
    suff = risk_scores_df[risk_scores_df["data_sufficiency"] == "SUFFICIENT"]

    assert (prov["observed_months_to_date"] <= 2).all()
    assert (suff["observed_months_to_date"] >= 3).all()
    assert len(prov) + len(suff) == len(risk_scores_df)

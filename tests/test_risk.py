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


def test_per_band_realized_rate_strict_monotonicity(risk_scores_df: pd.DataFrame):
    """INVARIANT (must hold forever): Higher risk bands have strictly higher realized slip rates.

    Recomputes realized rates directly from raw parquet columns on held-out Non-Roads test set.
    Guards the core operational guarantee without relying on static summary JSONs:
    - Every band non-empty
    - Strictly monotonic ordering: LOW < MEDIUM < HIGH < CRITICAL
    - CRITICAL tier achieves marked lift (>= 3x) over the dynamically computed base rate
    """
    test_nonroads = risk_scores_df[
        (risk_scores_df["split"] == "test")
        & (risk_scores_df["is_usable_filtered"])
        & (~risk_scores_df["sector"].str.lower().str.contains("road"))
    ]
    assert len(test_nonroads) > 0, "Non-roads test subset must not be empty"

    base_rate = float(test_nonroads["target_slip_3m_ge3m"].mean() * 100.0)

    rates = {}
    for band in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        sub = test_nonroads[test_nonroads["risk_band"] == band]
        assert len(sub) > 0, f"Risk band {band} must have non-zero project count"
        rate = float((sub["target_slip_3m_ge3m"].sum() / len(sub)) * 100.0)
        rates[band] = rate

    # Invariant 1: Strict monotonic ordering
    assert (
        rates["LOW"] < rates["MEDIUM"] < rates["HIGH"] < rates["CRITICAL"]
    ), f"Monotonicity invariant broken: {rates}"

    # Invariant 2: CRITICAL band must achieve at least 3x lift over dynamically computed base rate
    assert (
        rates["CRITICAL"] >= 3.0 * base_rate
    ), f"CRITICAL rate ({rates['CRITICAL']:.2f}%) did not achieve 3x lift over base ({base_rate:.2f}%)"


def test_per_band_snapshot_regression(risk_scores_df: pd.DataFrame):
    """SNAPSHOT of current dataset; update deliberately when the model/data legitimately changes.

    This is a tripwire, not an invariant. Pinned to the 2026-09-16 baseline release:
    - 1,373 non-roads test rows, 116 clean positives (8.45% base rate)
    - LOW ~1.65%, MEDIUM ~6.75%, HIGH ~18.90%, CRITICAL ~55.42%
    """
    test_nonroads = risk_scores_df[
        (risk_scores_df["split"] == "test")
        & (risk_scores_df["is_usable_filtered"])
        & (~risk_scores_df["sector"].str.lower().str.contains("road"))
    ]

    # Sample size snapshot
    assert len(test_nonroads) == 1373
    assert int(test_nonroads["target_slip_3m_ge3m"].sum()) == 116

    counts = test_nonroads["risk_band"].value_counts().to_dict()
    assert counts["LOW"] == 726
    assert counts["MEDIUM"] == 400
    assert counts["HIGH"] == 164
    assert counts["CRITICAL"] == 83

    # Per-band realized rate snapshot
    def get_rate(band: str) -> float:
        sub = test_nonroads[test_nonroads["risk_band"] == band]
        return round(float((sub["target_slip_3m_ge3m"].sum() / len(sub)) * 100.0), 2)

    assert get_rate("LOW") == 1.65
    assert get_rate("MEDIUM") == 6.75
    assert get_rate("HIGH") == 18.90
    assert get_rate("CRITICAL") == 55.42


def test_data_sufficiency_partitioning(risk_scores_df: pd.DataFrame):
    """Data sufficiency must be correctly partitioned between PROVISIONAL and SUFFICIENT."""
    prov = risk_scores_df[risk_scores_df["data_sufficiency"] == "PROVISIONAL"]
    suff = risk_scores_df[risk_scores_df["data_sufficiency"] == "SUFFICIENT"]

    assert (prov["observed_months_to_date"] <= 2).all()
    assert (suff["observed_months_to_date"] >= 3).all()
    assert len(prov) + len(suff) == len(risk_scores_df)

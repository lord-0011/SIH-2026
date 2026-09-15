"""CI fixture tests for risk scoring and calibration (non-skipping, runs on synthetic data).

Validates Platt calibration, monotonic score mapping in [0, 100], band assignment,
data sufficiency flags, and monotonicity invariants without DVC assets.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.risk.scorer import (
    assign_risk_band,
    calibrate_probabilities,
    compute_data_sufficiency,
    compute_risk_score,
    fit_platt_calibrator,
)


def test_monotonic_score_mapping():
    """Risk score must be strictly monotonic in calibrated probability and bounded in [0, 100]."""
    probs = np.linspace(0.0, 1.0, 101)
    scores = compute_risk_score(probs)

    # Bounded
    assert np.all(scores >= 0.0)
    assert np.all(scores <= 100.0)

    # Monotonic non-decreasing
    assert np.all(np.diff(scores) >= 0.0)

    # Exact endpoints
    assert scores[0] == 0.0
    assert scores[-1] == 100.0


def test_band_assignment_boundaries():
    """Bands must strictly follow defined cutoff thresholds."""
    cutoffs = {"low_med": 10.0, "med_high": 40.0, "high_crit": 70.0}

    assert assign_risk_band(0.0, cutoffs) == "LOW"
    assert assign_risk_band(9.9, cutoffs) == "LOW"
    assert assign_risk_band(10.0, cutoffs) == "MEDIUM"
    assert assign_risk_band(39.9, cutoffs) == "MEDIUM"
    assert assign_risk_band(40.0, cutoffs) == "HIGH"
    assert assign_risk_band(69.9, cutoffs) == "HIGH"
    assert assign_risk_band(70.0, cutoffs) == "CRITICAL"
    assert assign_risk_band(100.0, cutoffs) == "CRITICAL"


def test_data_sufficiency_computation():
    """Data sufficiency must assign PROVISIONAL to <= 2 months and SUFFICIENT to >= 3 months."""
    panel_rows = [
        {"project_id": "P1", "report_month": "2025-07"},
        {"project_id": "P1", "report_month": "2025-08"},
        {"project_id": "P1", "report_month": "2025-09"},
        {"project_id": "P1", "report_month": "2025-10"},
        {"project_id": "P2", "report_month": "2025-12"},
        {"project_id": "P2", "report_month": "2026-01"},
    ]
    df_panel = pd.DataFrame(panel_rows)
    suff_df = compute_data_sufficiency(df_panel)

    p1_suff = suff_df[suff_df["project_id"] == "P1"].sort_values("report_month")
    assert p1_suff["observed_months_to_date"].tolist() == [1, 2, 3, 4]
    assert p1_suff["data_sufficiency"].tolist() == [
        "PROVISIONAL",
        "PROVISIONAL",
        "SUFFICIENT",
        "SUFFICIENT",
    ]

    p2_suff = suff_df[suff_df["project_id"] == "P2"].sort_values("report_month")
    assert p2_suff["observed_months_to_date"].tolist() == [1, 2]
    assert p2_suff["data_sufficiency"].tolist() == ["PROVISIONAL", "PROVISIONAL"]


def test_platt_calibration_fit_and_predict():
    """Platt scaling must preserve rank ordering of raw model probabilities."""
    np.random.seed(42)
    # Synthetic raw probabilities
    raw_p_val = np.linspace(0.05, 0.95, 200)
    # Generate labels positively correlated with probability
    y_val = (raw_p_val + np.random.normal(0, 0.1, 200) > 0.5).astype(int)

    calibrator = fit_platt_calibrator(raw_p_val, y_val)

    test_raw = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
    test_cal = calibrate_probabilities(calibrator, test_raw)

    # Probabilities must be in [0, 1]
    assert np.all(test_cal >= 0.0)
    assert np.all(test_cal <= 1.0)

    # Monotonicity: higher raw probability must yield higher calibrated probability
    assert np.all(np.diff(test_cal) > 0.0)

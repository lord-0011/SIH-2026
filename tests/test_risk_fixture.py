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


def test_synthetic_per_band_monotonicity_invariant():
    """INVARIANT: Higher risk bands must have strictly higher realized event rates.

    Validates that the per-band recomputation logic dynamically asserts:
    - Every band non-empty
    - Strictly monotonic ordering: LOW < MEDIUM < HIGH < CRITICAL
    - CRITICAL lift over computed base rate (>= 2x)
    without hardcoding any specific percentage values.
    """
    scores = np.array([5.0] * 100 + [25.0] * 100 + [45.0] * 100 + [75.0] * 100)
    cutoffs = {"low_med": 10.0, "med_high": 40.0, "high_crit": 60.0}
    bands = [assign_risk_band(s, cutoffs) for s in scores]

    # Synthetic labels with clear progression: 2% in LOW, 10% in MED, 25% in HIGH, 60% in CRIT
    labels = np.array(
        [1] * 2 + [0] * 98 + [1] * 10 + [0] * 90 + [1] * 25 + [0] * 75 + [1] * 60 + [0] * 40
    )

    df_synth = pd.DataFrame({"risk_band": bands, "label": labels})
    base_rate = float(df_synth["label"].mean() * 100.0)

    rates = {}
    for b in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        sub = df_synth[df_synth["risk_band"] == b]
        assert len(sub) > 0, f"Band {b} must not be empty"
        rates[b] = float((sub["label"].sum() / len(sub)) * 100.0)

    # Monotonicity invariant
    assert rates["LOW"] < rates["MEDIUM"] < rates["HIGH"] < rates["CRITICAL"]
    # Lift invariant
    assert rates["CRITICAL"] >= 2.0 * base_rate


def test_synthetic_per_band_snapshot_regression():
    """SNAPSHOT of synthetic fixture dataset; update deliberately when fixture data changes.

    This is a tripwire, not an invariant. Pinned to fixture baseline:
    - 400 rows, 97 positives (24.25% base rate)
    - LOW 2.0%, MEDIUM 10.0%, HIGH 25.0%, CRITICAL 60.0%
    """
    scores = np.array([5.0] * 100 + [25.0] * 100 + [45.0] * 100 + [75.0] * 100)
    cutoffs = {"low_med": 10.0, "med_high": 40.0, "high_crit": 60.0}
    bands = [assign_risk_band(s, cutoffs) for s in scores]
    labels = np.array(
        [1] * 2 + [0] * 98 + [1] * 10 + [0] * 90 + [1] * 25 + [0] * 75 + [1] * 60 + [0] * 40
    )

    df_synth = pd.DataFrame({"risk_band": bands, "label": labels})
    assert len(df_synth) == 400
    assert df_synth["label"].sum() == 97

    sub_low = df_synth[df_synth["risk_band"] == "LOW"]
    sub_med = df_synth[df_synth["risk_band"] == "MEDIUM"]
    sub_high = df_synth[df_synth["risk_band"] == "HIGH"]
    sub_crit = df_synth[df_synth["risk_band"] == "CRITICAL"]

    assert (sub_low["label"].sum() / len(sub_low)) * 100.0 == 2.0
    assert (sub_med["label"].sum() / len(sub_med)) * 100.0 == 10.0
    assert (sub_high["label"].sum() / len(sub_high)) * 100.0 == 25.0
    assert (sub_crit["label"].sum() / len(sub_crit)) * 100.0 == 60.0

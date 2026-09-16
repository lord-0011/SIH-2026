"""CI fixture tests for early warning trend detection (non-skipping, runs on synthetic data).

Validates:
- Consecutive-month score trend trigger
- Steady-HIGH negative control (does not fire)
- Gap handling: short gaps (span <= 4 mo) tolerated; wide gaps (> 4 mo) rejected as STALE_HISTORY
- PROVISIONAL data sufficiency guard (INSUFFICIENT_HISTORY)
- Driver trend and velocity divergence triggers
- Multi-trigger combination & warning strength (0..3)
- Causal temporal leakage invariance (warning at T invariant to future data > T)
"""

from __future__ import annotations

import pandas as pd

from src.early_warning.detector import compute_early_warnings


def _create_synthetic_inputs(rows: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Helper to create matching risk_scores and features synthetic DataFrames."""
    risk_cols = [
        "project_id",
        "report_month",
        "sector",
        "risk_score",
        "risk_band",
        "data_sufficiency",
    ]
    feat_cols = [
        "project_id",
        "report_month",
        "financial_physical_gap",
        "progress_velocity_3mo",
        "exp_velocity_3mo",
    ]
    df = pd.DataFrame(rows)
    risk_df = df[risk_cols].copy()
    feat_df = df[feat_cols].copy()
    return risk_df, feat_df


def test_trend_trigger_fires_on_consecutive_increases():
    """Score rising across last 3 observed rows (10 -> 20 -> 30) must fire score_rising_2m."""
    rows = [
        {
            "project_id": "P1",
            "report_month": "2025-07",
            "sector": "Power",
            "risk_score": 10.0,
            "risk_band": "MEDIUM",
            "data_sufficiency": "SUFFICIENT",
            "financial_physical_gap": -10.0,
            "progress_velocity_3mo": 2.0,
            "exp_velocity_3mo": 5.0,
        },
        {
            "project_id": "P1",
            "report_month": "2025-08",
            "sector": "Power",
            "risk_score": 20.0,
            "risk_band": "MEDIUM",
            "data_sufficiency": "SUFFICIENT",
            "financial_physical_gap": -10.0,
            "progress_velocity_3mo": 2.0,
            "exp_velocity_3mo": 5.0,
        },
        {
            "project_id": "P1",
            "report_month": "2025-09",
            "sector": "Power",
            "risk_score": 30.0,
            "risk_band": "MEDIUM",
            "data_sufficiency": "SUFFICIENT",
            "financial_physical_gap": -10.0,
            "progress_velocity_3mo": 2.0,
            "exp_velocity_3mo": 5.0,
        },
    ]
    risk_df, feat_df = _create_synthetic_inputs(rows)
    out = compute_early_warnings(risk_df, feat_df)

    p1_m3 = out[out["report_month"] == "2025-09"].iloc[0]
    assert p1_m3["score_rising_fired"]
    assert p1_m3["early_warning"]
    assert p1_m3["warning_status"] == "ACTIVE_WARNING"
    assert "score_rising_2m" in p1_m3["triggers_fired"]
    assert p1_m3["risk_score_delta_1m"] == 10.0
    assert p1_m3["risk_score_delta_2m"] == 20.0


def test_steady_high_negative_control_does_not_fire():
    """NEGATIVE CONTROL: Project steady or declining at HIGH/CRITICAL must NOT fire score trend."""
    rows = [
        {
            "project_id": "P_HIGH",
            "report_month": "2025-07",
            "sector": "Railways",
            "risk_score": 60.0,
            "risk_band": "CRITICAL",
            "data_sufficiency": "SUFFICIENT",
            "financial_physical_gap": -5.0,
            "progress_velocity_3mo": 1.0,
            "exp_velocity_3mo": 2.0,
        },
        {
            "project_id": "P_HIGH",
            "report_month": "2025-08",
            "sector": "Railways",
            "risk_score": 60.0,
            "risk_band": "CRITICAL",
            "data_sufficiency": "SUFFICIENT",
            "financial_physical_gap": -5.0,
            "progress_velocity_3mo": 1.0,
            "exp_velocity_3mo": 2.0,
        },
        {
            "project_id": "P_HIGH",
            "report_month": "2025-09",
            "sector": "Railways",
            "risk_score": 58.0,
            "risk_band": "CRITICAL",
            "data_sufficiency": "SUFFICIENT",
            "financial_physical_gap": -5.0,
            "progress_velocity_3mo": 1.0,
            "exp_velocity_3mo": 2.0,
        },
    ]
    risk_df, feat_df = _create_synthetic_inputs(rows)
    out = compute_early_warnings(risk_df, feat_df)

    p_m3 = out[out["report_month"] == "2025-09"].iloc[0]
    assert not p_m3["score_rising_fired"]
    assert not p_m3["early_warning"]
    assert p_m3["warning_status"] == "STABLE_OR_IMPROVING"


def test_one_month_gap_tolerated_within_span():
    """A 1-month reporting gap (span = 3 months <= 4) must still fire when score is rising."""
    rows = [
        {
            "project_id": "P_GAP",
            "report_month": "2025-07",
            "sector": "Coal",
            "risk_score": 15.0,
            "risk_band": "MEDIUM",
            "data_sufficiency": "SUFFICIENT",
            "financial_physical_gap": 0.0,
            "progress_velocity_3mo": 1.0,
            "exp_velocity_3mo": 2.0,
        },
        {
            "project_id": "P_GAP",
            "report_month": "2025-08",
            "sector": "Coal",
            "risk_score": 25.0,
            "risk_band": "MEDIUM",
            "data_sufficiency": "SUFFICIENT",
            "financial_physical_gap": 0.0,
            "progress_velocity_3mo": 1.0,
            "exp_velocity_3mo": 2.0,
        },
        # 2025-09 skipped (reporting gap)
        {
            "project_id": "P_GAP",
            "report_month": "2025-10",
            "sector": "Coal",
            "risk_score": 40.0,
            "risk_band": "HIGH",
            "data_sufficiency": "SUFFICIENT",
            "financial_physical_gap": 0.0,
            "progress_velocity_3mo": 1.0,
            "exp_velocity_3mo": 2.0,
        },
    ]
    risk_df, feat_df = _create_synthetic_inputs(rows)
    out = compute_early_warnings(risk_df, feat_df)

    p_m3 = out[out["report_month"] == "2025-10"].iloc[0]
    assert p_m3["observation_span_months"] == 3  # 2025-10 minus 2025-07 is 3 months <= 4
    assert p_m3["score_rising_fired"]
    assert p_m3["early_warning"]
    assert p_m3["warning_status"] == "ACTIVE_WARNING"


def test_large_gap_rejected_as_stale_history():
    """A wide gap (span > 4 calendar months) must be rejected as STALE_HISTORY and not fire."""
    rows = [
        {
            "project_id": "P_STALE",
            "report_month": "2025-07",
            "sector": "Coal",
            "risk_score": 10.0,
            "risk_band": "MEDIUM",
            "data_sufficiency": "SUFFICIENT",
            "financial_physical_gap": 0.0,
            "progress_velocity_3mo": 1.0,
            "exp_velocity_3mo": 2.0,
        },
        {
            "project_id": "P_STALE",
            "report_month": "2025-08",
            "sector": "Coal",
            "risk_score": 20.0,
            "risk_band": "MEDIUM",
            "data_sufficiency": "SUFFICIENT",
            "financial_physical_gap": 0.0,
            "progress_velocity_3mo": 1.0,
            "exp_velocity_3mo": 2.0,
        },
        # 5-month reporting gap to 2026-01 (total span = 6 months > 4)
        {
            "project_id": "P_STALE",
            "report_month": "2026-01",
            "sector": "Coal",
            "risk_score": 40.0,
            "risk_band": "HIGH",
            "data_sufficiency": "SUFFICIENT",
            "financial_physical_gap": 0.0,
            "progress_velocity_3mo": 1.0,
            "exp_velocity_3mo": 2.0,
        },
    ]
    risk_df, feat_df = _create_synthetic_inputs(rows)
    out = compute_early_warnings(risk_df, feat_df)

    p_m3 = out[out["report_month"] == "2026-01"].iloc[0]
    assert p_m3["observation_span_months"] == 6  # 6 > 4
    assert not p_m3["score_rising_fired"]
    assert not p_m3["early_warning"]
    assert p_m3["warning_status"] == "STALE_HISTORY"


def test_provisional_insufficient_history():
    """PROVISIONAL projects (<= 2 observed months) must flag INSUFFICIENT_HISTORY and not fire."""
    rows = [
        {
            "project_id": "P_PROV",
            "report_month": "2025-07",
            "sector": "Power",
            "risk_score": 10.0,
            "risk_band": "LOW",
            "data_sufficiency": "PROVISIONAL",
            "financial_physical_gap": 0.0,
            "progress_velocity_3mo": 1.0,
            "exp_velocity_3mo": 2.0,
        },
        {
            "project_id": "P_PROV",
            "report_month": "2025-08",
            "sector": "Power",
            "risk_score": 30.0,
            "risk_band": "MEDIUM",
            "data_sufficiency": "PROVISIONAL",
            "financial_physical_gap": 0.0,
            "progress_velocity_3mo": 1.0,
            "exp_velocity_3mo": 2.0,
        },
    ]
    risk_df, feat_df = _create_synthetic_inputs(rows)
    out = compute_early_warnings(risk_df, feat_df)

    p_m2 = out[out["report_month"] == "2025-08"].iloc[0]
    assert not p_m2["early_warning"]
    assert p_m2["warning_status"] == "INSUFFICIENT_HISTORY"


def test_driver_trend_and_velocity_divergence_triggers():
    """Driver trend (gap widening) and velocity divergence must fire and combine in warning_strength."""
    rows = [
        {
            "project_id": "P_DRIVER",
            "report_month": "2025-07",
            "sector": "Petroleum",
            "risk_score": 25.0,
            "risk_band": "MEDIUM",
            "data_sufficiency": "SUFFICIENT",
            "financial_physical_gap": -15.0,
            "progress_velocity_3mo": 0.0,
            "exp_velocity_3mo": 10.0,
        },
        {
            "project_id": "P_DRIVER",
            "report_month": "2025-08",
            "sector": "Petroleum",
            "risk_score": 25.0,  # Score is flat
            "risk_band": "MEDIUM",
            "data_sufficiency": "SUFFICIENT",
            "financial_physical_gap": -10.0,  # Gap widened (-15 -> -10)
            "progress_velocity_3mo": -0.2,  # Velocity divergence (prog <= 0, exp > 0)
            "exp_velocity_3mo": 12.0,
        },
        {
            "project_id": "P_DRIVER",
            "report_month": "2025-09",
            "sector": "Petroleum",
            "risk_score": 25.0,  # Score still flat (Trigger 1 does NOT fire)
            "risk_band": "MEDIUM",
            "data_sufficiency": "SUFFICIENT",
            "financial_physical_gap": -4.0,  # Gap widened again (-10 -> -4)
            "progress_velocity_3mo": -0.5,  # Velocity divergence continues
            "exp_velocity_3mo": 15.0,
        },
    ]
    risk_df, feat_df = _create_synthetic_inputs(rows)
    out = compute_early_warnings(risk_df, feat_df)

    p_m3 = out[out["report_month"] == "2025-09"].iloc[0]
    assert not p_m3["score_rising_fired"]
    assert p_m3["gap_widening_fired"]
    assert p_m3["velocity_divergence_fired"]
    assert p_m3["warning_strength"] == 2
    assert p_m3["early_warning"]
    assert p_m3["warning_status"] == "ACTIVE_WARNING"
    assert "gap_widening_2m" in p_m3["triggers_fired"]
    assert "velocity_divergence_2m" in p_m3["triggers_fired"]


def test_causal_leakage_invariance_synthetic():
    """INVARIANT: Warning indicator and evidence at month T must be invariant to data at months > T."""
    # Multi-month project trajectory up to 2025-10
    months = ["2025-07", "2025-08", "2025-09", "2025-10"]
    scores = [10.0, 20.0, 30.0, 45.0]
    gaps = [-20.0, -15.0, -10.0, -5.0]

    rows = []
    for m, s, g in zip(months, scores, gaps):
        rows.append(
            {
                "project_id": "P_LEAK",
                "report_month": m,
                "sector": "Aviation",
                "risk_score": s,
                "risk_band": "MEDIUM",
                "data_sufficiency": "SUFFICIENT",
                "financial_physical_gap": g,
                "progress_velocity_3mo": 1.0,
                "exp_velocity_3mo": 5.0,
            }
        )

    risk_full, feat_full = _create_synthetic_inputs(rows)
    out_full = compute_early_warnings(risk_full, feat_full)

    # Truncated run (only data <= 2025-09)
    risk_trunc, feat_trunc = _create_synthetic_inputs(rows[:3])
    out_trunc = compute_early_warnings(risk_trunc, feat_trunc)

    row_full_t = out_full[out_full["report_month"] == "2025-09"].iloc[0]
    row_trunc_t = out_trunc[out_trunc["report_month"] == "2025-09"].iloc[0]

    # Must be 100% identical
    evidence_fields = [
        "early_warning",
        "warning_status",
        "warning_strength",
        "triggers_fired",
        "score_rising_fired",
        "gap_widening_fired",
        "velocity_divergence_fired",
        "risk_score_delta_1m",
        "risk_score_delta_2m",
        "gap_delta_1m",
        "gap_delta_2m",
    ]
    for field in evidence_fields:
        assert (
            row_full_t[field] == row_trunc_t[field]
        ), f"Leakage detected on {field}: full={row_full_t[field]} vs trunc={row_trunc_t[field]}"

"""CI fixture tests for feature engineering (non-skipping, runs on synthetic data).

Validates CUF and DERIVED feature formulas, manifest integrity, mid-window arrival elapsed
clocks, and edge cases.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.features.builder import (
    compute_cuf_features,
    compute_feature_table,
    get_cuf_feature_names,
    get_derived_feature_names,
)


@pytest.fixture
def synthetic_features_panel() -> pd.DataFrame:
    """Create a minimal 2-project synthetic panel for formula and edge-case validation."""
    rows = [
        # Project 1: Baseline project with complete dates
        {
            "project_id": "P_BASE",
            "project_code": 101,
            "report_month": "2025-07",
            "project_name": "Metro Rail Phase 1",
            "implementing_agency": "DMRC",
            "ministry": "Housing and Urban Affairs",
            "sector": "Urban Development",
            "state": "Delhi",
            "project_size_band": "Mega",
            "date_of_approval": "2022-01",
            "start_date": "2022-06",
            "original_completion_date": "2026-06",
            "revised_completion_date": "2026-12",
            "original_cost_cr": 2000.0,
            "revised_cost_cr": 2500.0,
            "cumulative_expenditure_cr": 1000.0,
            "physical_progress_pct": 40.0,
            "project_status": "Ongoing",
            "data_quality_flag": None,
            "match_confidence": "high",
            "is_completed_this_month": False,
            "actual_completion_date": None,
            "elapsed_months_since_anchor": 37.0,  # from 2022-06 to 2025-07
        },
        {
            "project_id": "P_BASE",
            "project_code": 101,
            "report_month": "2025-08",
            "project_name": "Metro Rail Phase 1",
            "implementing_agency": "DMRC",
            "ministry": "Housing and Urban Affairs",
            "sector": "Urban Development",
            "state": "Delhi",
            "project_size_band": "Mega",
            "date_of_approval": "2022-01",
            "start_date": "2022-06",
            "original_completion_date": "2026-06",
            "revised_completion_date": "2026-12",
            "original_cost_cr": 2000.0,
            "revised_cost_cr": 2500.0,
            "cumulative_expenditure_cr": 1050.0,
            "physical_progress_pct": 42.0,
            "project_status": "Ongoing",
            "data_quality_flag": None,
            "match_confidence": "high",
            "is_completed_this_month": False,
            "actual_completion_date": None,
            "elapsed_months_since_anchor": 38.0,
        },
        # Project 2: Mid-window arrival (arrived 2025-12, but start date is 2021-01)
        {
            "project_id": "P_MORTH_MID",
            "project_code": 202,
            "report_month": "2025-12",
            "project_name": "Highway Bypass Four-Laning",
            "implementing_agency": "NHAI",
            "ministry": "Road Transport and Highways",
            "sector": "Roads and Highways",
            "state": "['Rajasthan', 'Gujarat']",  # multi-state list representation
            "project_size_band": "Major",
            "date_of_approval": "2020-08",
            "start_date": "2021-01",
            "original_completion_date": "2024-01",
            "revised_completion_date": "2026-03",
            "original_cost_cr": 800.0,
            "revised_cost_cr": 800.0,
            "cumulative_expenditure_cr": 400.0,
            "physical_progress_pct": 60.0,
            "project_status": "Ongoing",
            "data_quality_flag": None,
            "match_confidence": "high",
            "is_completed_this_month": False,
            "actual_completion_date": None,
            "elapsed_months_since_anchor": 59.0,  # 59 months since true start!
        },
    ]
    return pd.DataFrame(rows)


def test_cuf_feature_formulas(synthetic_features_panel):
    """Verify CUF snapshot features match mathematical definitions."""
    cuf_df = compute_cuf_features(synthetic_features_panel)

    p_base = cuf_df[
        (cuf_df["project_id"] == "P_BASE") & (cuf_df["report_month"] == "2025-07")
    ].iloc[0]

    # Cost escalation: 2500 - 2000 = 500 Cr; pct = 500 / 2000 * 100 = 25.0%
    assert p_base["cost_escalation_amt"] == 500.0
    assert p_base["cost_escalation_pct"] == 25.0

    # Expenditure utilization: 1000 / 2500 = 0.40
    assert p_base["exp_utilization"] == 0.40

    # Planned duration: 2026-06 minus 2022-06 = 48 months
    assert p_base["planned_duration_months"] == 48.0

    # Elapsed duration: uses elapsed_months_since_anchor = 37.0
    assert p_base["elapsed_duration_months"] == 37.0

    # Remaining duration: effective 2026-12 minus 2025-07 = 17 months
    assert p_base["remaining_duration_months"] == 17.0

    # Schedule variance: 2026-12 minus 2026-06 = 6 months
    assert p_base["schedule_variance_months"] == 6.0

    # Delay to date: report 2025-07 is BEFORE orig comp 2026-06 -> 0.0
    assert p_base["delay_to_date_months"] == 0.0

    # Financial-Physical Gap: (0.40 * 100) - 40.0 = 0.0%
    assert p_base["financial_physical_gap"] == 0.0


def test_mid_window_morth_elapsed_clock_preservation(synthetic_features_panel):
    """CRITICAL TRAP CHECK: Mid-window arrivals must use the anchor clock, NOT 0 months."""
    cuf_df = compute_cuf_features(synthetic_features_panel)

    p_morth = cuf_df[cuf_df["project_id"] == "P_MORTH_MID"].iloc[0]

    # Even though P_MORTH_MID first appeared in 2025-12, its elapsed duration is 59 months!
    assert p_morth["elapsed_duration_months"] == 59.0

    # Multi-state parsing
    assert p_morth["state_count"] == 2


def test_feature_manifest_integrity(synthetic_features_panel):
    """Assert machine-readable manifest separates CUF and DERIVED and flags provisional thresholds."""
    feat_df, manifest = compute_feature_table(synthetic_features_panel)

    cuf_names = get_cuf_feature_names()
    derived_names = get_derived_feature_names()

    assert manifest["cuf_features"]["count"] == len(cuf_names)
    assert manifest["derived_features"]["count"] == len(derived_names)
    assert manifest["all_features"]["total_count"] == len(cuf_names) + len(derived_names)

    # Check that provisional tunable thresholds are documented
    prov = manifest["derived_features"]["provisional_tunable_thresholds"]
    assert "progress_stagnation" in prov
    assert "recent_deterioration" in prov
    assert prov["progress_stagnation"]["status"] == "PROVISIONAL / TUNABLE"

    # All columns present in output DataFrame
    for col in cuf_names + derived_names:
        assert col in feat_df.columns

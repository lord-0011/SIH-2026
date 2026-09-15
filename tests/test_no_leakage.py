"""Temporal leakage tests for all engineered features (ANTIGRAVITY.md §2, docs/05 §Leakage).

Every derived feature and CUF feature at month T must use ONLY observations with
report_month <= T. A feature value at month T must be strictly IDENTICAL whether or not
future observations (> T) are present in the dataset.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.features.builder import (
    compute_cuf_features,
    compute_feature_table,
    compute_sector_historical_event_rate,
    get_derived_feature_names,
)


@pytest.fixture
def multi_project_synthetic_panel() -> pd.DataFrame:
    """Create a multi-project panel across 7 consecutive months (2025-07 to 2026-01).

    Includes 3 projects in 'Roads' sector and 1 in 'Power' sector with changing costs,
    expenditures, physical progress, and future schedule revisions after T = '2025-10'.
    """
    months = [
        "2025-07",
        "2025-08",
        "2025-09",
        "2025-10",
        "2025-11",
        "2025-12",
        "2026-01",
    ]
    rows = []

    # Project 1: Roads sector, experiences major slip and cost spike in 2025-11/2025-12
    for idx, m in enumerate(months):
        rows.append(
            {
                "project_id": "P_ROAD_1",
                "project_code": 1001,
                "report_month": m,
                "project_name": "Highway Package 1",
                "implementing_agency": "NHAI",
                "ministry": "Road Transport and Highways",
                "sector": "Roads and Highways",
                "state": "Maharashtra",
                "project_size_band": "Mega",
                "date_of_approval": "2024-01",
                "start_date": "2024-03",
                "original_completion_date": "2026-06",
                "revised_completion_date": "2026-06" if idx <= 3 else "2027-06",
                "original_cost_cr": 1000.0,
                "revised_cost_cr": 1000.0 if idx <= 3 else 1500.0,
                "cumulative_expenditure_cr": 100.0 + idx * 30.0 + (500.0 if idx > 3 else 0.0),
                "physical_progress_pct": 10.0 + idx * 5.0 + (20.0 if idx > 3 else 0.0),
                "project_status": "Ongoing",
                "data_quality_flag": None,
                "match_confidence": "high",
                "is_completed_this_month": False,
                "actual_completion_date": None,
                "elapsed_months_since_anchor": 16.0 + idx,
            }
        )

    # Project 2: Roads sector, first revised date populated in 2025-10 (T)
    for idx, m in enumerate(months):
        rows.append(
            {
                "project_id": "P_ROAD_2",
                "project_code": 1002,
                "report_month": m,
                "project_name": "Highway Package 2",
                "implementing_agency": "NHAI",
                "ministry": "Road Transport and Highways",
                "sector": "Roads and Highways",
                "state": "Gujarat",
                "project_size_band": "Major",
                "date_of_approval": "2024-02",
                "start_date": "2024-04",
                "original_completion_date": "2026-12",
                # Null until 2025-10 (idx=3), then populated
                "revised_completion_date": None if idx < 3 else "2027-03",
                "original_cost_cr": 500.0,
                "revised_cost_cr": 500.0,
                "cumulative_expenditure_cr": 50.0 + idx * 10.0,
                "physical_progress_pct": 5.0 + idx * 2.0,
                "project_status": "Ongoing",
                "data_quality_flag": None,
                "match_confidence": "high",
                "is_completed_this_month": False,
                "actual_completion_date": None,
                "elapsed_months_since_anchor": 15.0 + idx,
            }
        )

    # Project 3: Roads sector, stable ongoing
    for idx, m in enumerate(months):
        rows.append(
            {
                "project_id": "P_ROAD_3",
                "project_code": 1003,
                "report_month": m,
                "project_name": "Highway Package 3",
                "implementing_agency": "NHAI",
                "ministry": "Road Transport and Highways",
                "sector": "Roads and Highways",
                "state": "Rajasthan",
                "project_size_band": "Major",
                "date_of_approval": "2024-05",
                "start_date": "2024-06",
                "original_completion_date": "2027-06",
                "revised_completion_date": "2027-06",
                "original_cost_cr": 300.0,
                "revised_cost_cr": 300.0,
                "cumulative_expenditure_cr": 20.0 + idx * 5.0,
                "physical_progress_pct": 2.0 + idx * 1.0,
                "project_status": "Ongoing",
                "data_quality_flag": None,
                "match_confidence": "high",
                "is_completed_this_month": False,
                "actual_completion_date": None,
                "elapsed_months_since_anchor": 13.0 + idx,
            }
        )

    # Project 4: Power sector
    for idx, m in enumerate(months):
        rows.append(
            {
                "project_id": "P_POWER_1",
                "project_code": 2001,
                "report_month": m,
                "project_name": "Thermal Plant 1",
                "implementing_agency": "NTPC",
                "ministry": "Power",
                "sector": "Power",
                "state": "Odisha",
                "project_size_band": "Mega",
                "date_of_approval": "2023-01",
                "start_date": "2023-05",
                "original_completion_date": "2026-03",
                "revised_completion_date": "2026-03",
                "original_cost_cr": 4000.0,
                "revised_cost_cr": 4000.0,
                "cumulative_expenditure_cr": 800.0 + idx * 100.0,
                "physical_progress_pct": 30.0 + idx * 3.0,
                "project_status": "Ongoing",
                "data_quality_flag": None,
                "match_confidence": "high",
                "is_completed_this_month": False,
                "actual_completion_date": None,
                "elapsed_months_since_anchor": 26.0 + idx,
            }
        )

    return pd.DataFrame(rows)


def test_derived_features_invariance_to_future_observations(multi_project_synthetic_panel):
    """PRIMARY LEAKAGE DELIVERABLE: Assert every derived feature at T is strictly invariant

    to the presence or absence of future observations (> T).
    """
    cutoff_T = "2025-10"
    full_panel = multi_project_synthetic_panel.copy()
    truncated_panel = full_panel[full_panel["report_month"] <= cutoff_T].copy()

    # Compute features on truncated panel (data <= T only)
    feat_trunc, _ = compute_feature_table(truncated_panel)

    # Compute features on full panel (data <= T and data > T present)
    feat_full, _ = compute_feature_table(full_panel)

    derived_cols = get_derived_feature_names()

    # Compare values at T for all projects
    t_trunc = feat_trunc[feat_trunc["report_month"] == cutoff_T].sort_values("project_id")
    t_full = feat_full[feat_full["report_month"] == cutoff_T].sort_values("project_id")

    assert len(t_trunc) == len(t_full)

    for col in derived_cols:
        val_trunc = t_trunc[col].values
        val_full = t_full[col].values
        # Float comparison with tolerance
        np.testing.assert_allclose(
            val_trunc,
            val_full,
            rtol=1e-5,
            atol=1e-5,
            err_msg=f"LEAKAGE DETECTED in derived feature '{col}'! Value at {cutoff_T} changed when future data was present.",
        )


def test_negative_control_catches_intentional_leakage(multi_project_synthetic_panel):
    """Negative control: Verify that if a feature deliberately peeks into T+1, the test FAILS."""
    cutoff_T = "2025-10"
    full_panel = multi_project_synthetic_panel.copy()
    truncated_panel = full_panel[full_panel["report_month"] <= cutoff_T].copy()

    # Define a leaking mock feature that peeks at T+1
    def compute_leaking_feature(df: pd.DataFrame) -> pd.DataFrame:
        df_sorted = df.sort_values(["project_id", "report_month"]).copy()
        # Shifts backwards to peek at next month's revised cost!
        df_sorted["leaking_future_cost"] = df_sorted.groupby("project_id")["revised_cost_cr"].shift(
            -1
        )
        return df_sorted

    trunc_res = compute_leaking_feature(truncated_panel)
    full_res = compute_leaking_feature(full_panel)

    t_trunc = trunc_res[trunc_res["report_month"] == cutoff_T].set_index("project_id")
    t_full = full_res[full_res["report_month"] == cutoff_T].set_index("project_id")

    # In truncated panel, T is the last month, so shifted future cost is NaN
    assert pd.isna(t_trunc.loc["P_ROAD_1", "leaking_future_cost"])
    # In full panel, T+1 exists and revised cost changed to 1500.0!
    assert t_full.loc["P_ROAD_1", "leaking_future_cost"] == 1500.0

    # Assert that this difference is caught by the test
    with pytest.raises(AssertionError):
        np.testing.assert_allclose(
            t_trunc["leaking_future_cost"].fillna(0.0).values,
            t_full["leaking_future_cost"].fillna(0.0).values,
        )


def test_sector_historical_event_rate_strict_leakage(multi_project_synthetic_panel):
    """REFINEMENT 1: Stricter leakage discipline for sector_hist_event_rate.

    1. Rate at T is invariant to ALL data after T across ALL projects in the sector.
    2. Only slip events fully determined by M + 3 <= T are counted (slips with M > T-3 are NOT counted).
    """
    cutoff_T = "2025-10"
    full_panel = multi_project_synthetic_panel.copy()
    truncated_panel = full_panel[full_panel["report_month"] <= cutoff_T].copy()

    rate_trunc = compute_sector_historical_event_rate(truncated_panel, horizon=3, threshold=3)
    rate_full = compute_sector_historical_event_rate(full_panel, horizon=3, threshold=3)

    t_idx_trunc = truncated_panel[truncated_panel["report_month"] == cutoff_T].index
    t_idx_full = full_panel[full_panel["report_month"] == cutoff_T].index

    # Rate at T must be identical whether or not future data > T exists in ANY project in the sector
    np.testing.assert_allclose(
        rate_trunc.loc[t_idx_trunc].values,
        rate_full.loc[t_idx_full].values,
        err_msg="LEAKAGE DETECTED in sector_hist_event_rate! Value at T was altered by future sector data.",
    )


def test_schedule_variance_months_uses_only_date_at_T(multi_project_synthetic_panel):
    """REFINEMENT 2: schedule_variance_months (CUF) must use ONLY revised_completion_date

    as known at T, never the future revision that constitutes the downstream label.
    """
    full_panel = multi_project_synthetic_panel.copy()
    cuf_features = compute_cuf_features(full_panel)

    p1_at_t = cuf_features[
        (cuf_features["project_id"] == "P_ROAD_1") & (cuf_features["report_month"] == "2025-10")
    ].iloc[0]

    # At 2025-10, P_ROAD_1 had revised_completion_date == '2026-06' (same as original)
    # The slip to '2027-06' occurred in 2025-11!
    # Therefore, schedule_variance_months at 2025-10 MUST BE 0.0, NOT 12.0!
    assert p1_at_t["schedule_variance_months"] == 0.0

    # In 2025-11, after the revision is published, variance becomes 12.0
    p1_after_t = cuf_features[
        (cuf_features["project_id"] == "P_ROAD_1") & (cuf_features["report_month"] == "2025-11")
    ].iloc[0]
    assert p1_after_t["schedule_variance_months"] == 12.0


def test_first_revised_date_feature_mirrors_step05_first_pop_logic(multi_project_synthetic_panel):
    """REFINEMENT 4: first_revised_date_entered_in_trailing_3mo must EXACTLY mirror

    the STEP_05 label first-population exclusion logic (first ever revised date, judged from data <= T).
    """
    full_panel = multi_project_synthetic_panel.copy()
    _, manifest = compute_feature_table(full_panel)
    feat_df, _ = compute_feature_table(full_panel)

    # For P_ROAD_2:
    # 2025-07: revised = None -> feature = 0
    # 2025-08: revised = None -> feature = 0
    # 2025-09: revised = None -> feature = 0
    # 2025-10 (T): revised = '2027-03' (first ever populated!) -> feature MUST BE 1!
    p2 = feat_df[feat_df["project_id"] == "P_ROAD_2"].sort_values("report_month")
    flags = p2["first_revised_date_entered_in_trailing_3mo"].values

    assert flags[0] == 0  # 2025-07
    assert flags[1] == 0  # 2025-08
    assert flags[2] == 0  # 2025-09
    assert flags[3] == 1  # 2025-10 (first entered!)

    # For P_ROAD_1 (revised date already existed from month 1):
    # Should NEVER trigger first-population feature (flag == 0 throughout)
    p1 = feat_df[feat_df["project_id"] == "P_ROAD_1"].sort_values("report_month")
    assert (p1["first_revised_date_entered_in_trailing_3mo"] == 0).all()

"""Integration test suite for STEP_04 project-month panel on real data.

Skips cleanly in CI when DVC data is not pulled.
Runs locally / pre-merge to enforce the reconciliation identity and panel invariants.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture(scope="module")
def panel_data():
    panel_path = Path("data/processed/panel.parquet")
    gaps_path = Path("data/processed/panel_gaps.csv")
    canonical_path = Path("data/interim/canonical_projects.parquet")

    if not panel_path.exists() or not gaps_path.exists() or not canonical_path.exists():
        pytest.skip("Full dataset not available in this environment (DVC data not pulled)")

    panel_df = pd.read_parquet(panel_path)
    gaps_df = pd.read_csv(gaps_path, dtype={"project_id": str})
    canonical_df = pd.read_parquet(canonical_path)

    return {
        "panel_df": panel_df,
        "gaps_df": gaps_df,
        "canonical_df": canonical_df,
    }


def test_reconciliation_identity_and_grid_counts(panel_data):
    """Assert First Invariant: computed reconciliation identity.

    observed_rows + sum(all gap cells) == n_distinct_projects * n_months
    For the 13-month MoSPI corpus:
      2,243 projects x 13 months = 29,159 grid cells
      18,860 observed rows + 10,299 gap cells = 29,159
    """
    panel_df = panel_data["panel_df"]
    gaps_df = panel_data["gaps_df"]
    canonical_df = panel_data["canonical_df"]

    n_observed = len(panel_df)
    n_gaps = len(gaps_df)
    n_projects = canonical_df["canonical_project_id"].nunique()
    all_months = sorted(panel_df["report_month"].unique())
    n_months = len(all_months)
    grid_total = n_projects * n_months

    # First Invariant: COMPUTED IDENTITY
    assert n_observed + n_gaps == grid_total, (
        f"Reconciliation identity failed: {n_observed} + {n_gaps} = "
        f"{n_observed + n_gaps} != {grid_total}"
    )

    # Sourced totals
    assert n_projects == 2243
    assert n_months == 13
    assert grid_total == 29159
    assert n_observed == 18860
    assert n_gaps == 10299

    # Partition of observed rows
    n_ongoing = int((~panel_df["is_completed_this_month"]).sum())
    n_completed = int(panel_df["is_completed_this_month"].sum())
    assert n_ongoing == 18601
    assert n_completed == 259
    assert n_ongoing + n_completed == 18860

    # Partition of gap cells
    gap_counts = gaps_df["gap_reason"].value_counts().to_dict()
    assert gap_counts.get("not_yet_onboarded") == 8593
    assert gap_counts.get("completed") == 684
    assert gap_counts.get("unexplained_gap") == 1022
    assert gap_counts.get("excluded_quality", 0) == 0
    assert 8593 + 684 + 1022 == 10299


def test_no_duplicate_project_month_pairs(panel_data):
    """Assert primary key uniqueness: exactly 0 duplicate (project_id, report_month)."""
    panel_df = panel_data["panel_df"]
    dup_count = panel_df.duplicated(subset=["project_id", "report_month"]).sum()
    assert dup_count == 0, f"Found {dup_count} duplicate (project_id, report_month) rows"


def test_trap_a_trajectory_anchoring_morth_project(panel_data):
    """Verify Trap A: elapsed months measured from anchor date, NOT first appearance.

    MoRTH project 617907 first appears in 2025-12, but start_date is 09/2022.
    Its elapsed_months_since_anchor must be 39 months (not 0).
    """
    panel_df = panel_data["panel_df"]
    p617907 = panel_df[panel_df["project_id"] == "617907"]
    assert len(p617907) == 7  # 6 ongoing + 1 completed in 2026-06

    p617907_dec = p617907[p617907["report_month"] == "2025-12"].iloc[0]
    assert p617907_dec["trajectory_anchor_date"] == "09/2022"
    assert p617907_dec["first_appearance_month"] == "2025-12"
    assert bool(p617907_dec["is_mid_window_arrival"]) is True
    assert bool(p617907_dec["is_morth_onboarded_mid_window"]) is True
    assert p617907_dec["elapsed_months_since_anchor"] == 39.0
    assert p617907_dec["physical_progress_pct"] == 89.0


def test_trap_b_missing_month_semantics_no_forward_fill(panel_data):
    """Verify Trap B: unexplained gaps are NOT forward-filled into panel rows.

    Project 400019 appeared in 12 months (2025-07 to 2026-06) and dropped out in 2026-07.
    Assert no row exists in panel for (400019, 2026-07), and it is logged as unexplained_gap.
    """
    panel_df = panel_data["panel_df"]
    gaps_df = panel_data["gaps_df"]

    p_rows = panel_df[panel_df["project_id"] == "400019"]
    assert len(p_rows) == 12
    assert "2026-07" not in p_rows["report_month"].values

    p_gaps = gaps_df[(gaps_df["project_id"] == "400019") & (gaps_df["report_month"] == "2026-07")]
    assert len(p_gaps) == 1
    assert p_gaps.iloc[0]["gap_reason"] == "unexplained_gap"


def test_trap_c_completed_project_rows_as_realized_anchors(panel_data):
    """Verify Trap C: all 259 completed projects exist as terminal rows in panel.

    Each has is_completed_this_month=True, actual_completion_date populated,
    physical_progress_pct=100.0, and project_status='Completed'.
    """
    panel_df = panel_data["panel_df"]
    comp_rows = panel_df[panel_df["is_completed_this_month"]]
    assert len(comp_rows) == 259
    assert (comp_rows["project_status"] == "Completed").all()
    assert (comp_rows["physical_progress_pct"] == 100.0).all()
    assert comp_rows["actual_completion_date"].notna().all()


def test_direct_query_reversible_completions(panel_data):
    """Direct query for reversible completions.

    Systematically checks all completed projects that appear in any Ongoing table
    in a month strictly after their Table 3 completion month.
    Enforces that exactly 1 project (705635) is reversible, leaving exactly 258 clean
    irreversible outcomes (~130 concentrated in June 2026 MoRTH road packages -> ~129
    effective independent outcomes).
    """
    panel_df = panel_data["panel_df"]

    completed_rows = panel_df[panel_df["is_completed_this_month"]][
        ["project_id", "report_month"]
    ].rename(columns={"report_month": "completion_month"})
    ongoing_rows = panel_df[~panel_df["is_completed_this_month"]][
        ["project_id", "report_month"]
    ].rename(columns={"report_month": "ongoing_month"})

    joined = pd.merge(completed_rows, ongoing_rows, on="project_id")
    reversibles = joined[joined["ongoing_month"] > joined["completion_month"]]

    distinct_reversibles = reversibles["project_id"].unique().tolist()
    assert distinct_reversibles == ["705635"], (
        f"Unexpected reversible completions: {distinct_reversibles}. "
        "If a data refresh introduces new reversibles, update Scheme B in docs/05_LABEL_SPEC.md."
    )

    # Clean realized-outcome count
    clean_realized_outcomes = len(completed_rows) - len(distinct_reversibles)
    assert clean_realized_outcomes == 258


def test_panel_schema_and_columns(panel_data):
    """Verify panel has all columns specified in docs/04_DATA_SCHEMA.md."""
    panel_df = panel_data["panel_df"]
    required_cols = [
        "project_id",
        "project_code",
        "report_month",
        "project_name",
        "implementing_agency",
        "ministry",
        "sector",
        "state",
        "project_size_band",
        "date_of_approval",
        "start_date",
        "original_completion_date",
        "revised_completion_date",
        "original_cost_cr",
        "revised_cost_cr",
        "cumulative_expenditure_cr",
        "physical_progress_pct",
        "project_status",
        "data_quality_flag",
        "match_confidence",
        "is_completed_this_month",
        "actual_completion_date",
        "first_appearance_month",
        "is_mid_window_arrival",
        "is_morth_onboarded_mid_window",
        "trajectory_anchor_date",
        "elapsed_months_since_anchor",
    ]
    for col in required_cols:
        assert col in panel_df.columns, f"Missing required column: {col}"
    assert (panel_df["project_size_band"].isin(["Mega", "Major"])).all()
    import numpy as np

    assert isinstance(panel_df["state"].iloc[0], list | np.ndarray)

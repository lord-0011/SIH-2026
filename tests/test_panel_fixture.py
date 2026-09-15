"""CI Fixture Test for STEP_04 Panel Assembly.

Tests panel construction against synthetic in-memory fixtures.
NEVER skips in CI. Validates Trap A, Trap B, Trap C, and the Reconciliation Identity.
"""

from __future__ import annotations

import pandas as pd

from src.panel.builder import (
    build_panel_df,
    compute_elapsed_months,
    parse_state_list,
)


def test_parse_state_list():
    """Verify single-state, multi-state with parentheses, and empty/dash states."""
    assert parse_state_list("Maharashtra") == ["Maharashtra"]
    assert parse_state_list("Multi-States (Goa,\nKarnataka,\nMaharashtra)") == [
        "Goa",
        "Karnataka",
        "Maharashtra",
    ]
    assert parse_state_list("-") == []
    assert parse_state_list(None) == []


def test_compute_elapsed_months_trap_a():
    """Verify Trap A: elapsed months calculated from own anchor, not appearance."""
    # MoRTH project: anchor 09/2022, report_month 2025-12 -> 39 months
    assert compute_elapsed_months("09/2022", "2025-12") == 39.0
    # Anchor 01/2025, report_month 2025-07 -> 6 months
    assert compute_elapsed_months("01/2025", "2025-07") == 6.0
    # Future anchor (retrospective sanction): anchor 12/2026, report 2025-07 -> -17 months
    assert compute_elapsed_months("12/2026", "2025-07") == -17.0
    # Invalid inputs return None
    assert compute_elapsed_months(None, "2025-12") is None
    assert compute_elapsed_months("invalid", "2025-12") is None


def test_synthetic_panel_assembly_and_reconciliation_identity():
    """Verify panel assembly, Traps A/B/C, and the computed reconciliation identity.

    Grid: 3 projects x 4 months = 12 total project-month cells.
    Project 1 (P100): Onboarded at m1, drops at m2 (Trap B: unexplained gap), reappears at m3, completes at m4 (Trap C).
      - Observed: m1, m3 (ongoing), m4 (completed) = 3 rows.
      - Gaps: m2 (unexplained_gap) = 1 cell.
    Project 2 (P200): Mid-window arrival at m3 (Trap A: anchor at 2020-01), observed m3, m4.
      - Observed: m3, m4 = 2 rows.
      - Gaps: m1, m2 (not_yet_onboarded) = 2 cells.
    Project 3 (P300): Onboarded at m1, completes at m2, absent m3, m4.
      - Observed: m1 (ongoing), m2 (completed) = 2 rows.
      - Gaps: m3, m4 (completed) = 2 cells.

    Summary:
      - Total observed: 3 + 2 + 2 = 7 rows.
      - Total gaps: 1 + 2 + 2 = 5 cells.
      - Grid: 3 x 4 = 12 cells.
      - Reconciliation Identity: 7 + 5 == 12!
    """
    corpus_months = ["2025-07", "2025-08", "2025-09", "2025-10"]

    canonical_df = pd.DataFrame(
        [
            {
                "canonical_project_id": "P100",
                "project_code": "100",
                "project_name": "Project Alpha",
                "implementing_agency": "Agency A",
                "ministry": "Ministry of Transport",
                "sector": "Roads",
                "state": "Delhi",
                "date_of_approval": "01/2024",
                "start_date": "03/2024",
                "first_appearance_month": "2025-07",
                "is_mid_window_arrival": False,
                "is_morth_onboarded_mid_window": False,
                "trajectory_anchor_date": "03/2024",
                "total_months_observed": 3,
            },
            {
                "canonical_project_id": "P200",
                "project_code": "200",
                "project_name": "Project Beta (Mid-Window Arrival)",
                "implementing_agency": "NHAI",
                "ministry": "Ministry of Road Transport and Highways",
                "sector": "Roads",
                "state": "Multi-States (Haryana, Punjab)",
                "date_of_approval": "01/2020",
                "start_date": "01/2020",
                "first_appearance_month": "2025-09",
                "is_mid_window_arrival": True,
                "is_morth_onboarded_mid_window": True,
                "trajectory_anchor_date": "01/2020",
                "total_months_observed": 2,
            },
            {
                "canonical_project_id": "P300",
                "project_code": "300",
                "project_name": "Project Gamma",
                "implementing_agency": "Agency C",
                "ministry": "Ministry of Railways",
                "sector": "Railways",
                "state": "Gujarat",
                "date_of_approval": "05/2023",
                "start_date": "06/2023",
                "first_appearance_month": "2025-07",
                "is_mid_window_arrival": False,
                "is_morth_onboarded_mid_window": False,
                "trajectory_anchor_date": "06/2023",
                "total_months_observed": 2,
            },
        ]
    )

    ongoing_df = pd.DataFrame(
        [
            # P100 at m1 and m3 (missing m2!)
            {
                "canonical_project_id": "P100",
                "project_code": "100",
                "report_month": "2025-07",
                "project_name": "Project Alpha",
                "original_cost_cr": 500.0,
                "revised_cost_cr": 550.0,
                "cumulative_expenditure_cr": 100.0,
                "physical_progress_pct": 20.0,
                "data_quality_flag": None,
                "match_confidence": "high",
            },
            {
                "canonical_project_id": "P100",
                "project_code": "100",
                "report_month": "2025-09",
                "project_name": "Project Alpha",
                "original_cost_cr": 500.0,
                "revised_cost_cr": 550.0,
                "cumulative_expenditure_cr": 300.0,
                "physical_progress_pct": 60.0,
                "data_quality_flag": None,
                "match_confidence": "high",
            },
            # P200 arrives mid-window at m3 and m4
            {
                "canonical_project_id": "P200",
                "project_code": "200",
                "report_month": "2025-09",
                "project_name": "Project Beta (Mid-Window Arrival)",
                "original_cost_cr": 1200.0,  # Mega
                "revised_cost_cr": 1200.0,
                "cumulative_expenditure_cr": 800.0,
                "physical_progress_pct": 75.0,
                "data_quality_flag": None,
                "match_confidence": "high",
            },
            {
                "canonical_project_id": "P200",
                "project_code": "200",
                "report_month": "2025-10",
                "project_name": "Project Beta (Mid-Window Arrival)",
                "original_cost_cr": 1200.0,
                "revised_cost_cr": 1200.0,
                "cumulative_expenditure_cr": 900.0,
                "physical_progress_pct": 85.0,
                "data_quality_flag": None,
                "match_confidence": "high",
            },
            # P300 at m1
            {
                "canonical_project_id": "P300",
                "project_code": "300",
                "report_month": "2025-07",
                "project_name": "Project Gamma",
                "original_cost_cr": 800.0,
                "revised_cost_cr": 800.0,
                "cumulative_expenditure_cr": 400.0,
                "physical_progress_pct": 90.0,
                "data_quality_flag": None,
                "match_confidence": "high",
            },
        ]
    )

    completed_df = pd.DataFrame(
        [
            # P100 completes at m4
            {
                "project_code": "100",
                "report_month": "2025-10",
                "project_name": "Project Alpha",
                "original_cost_cr": 500.0,
                "revised_cost_cr": 550.0,
                "cumulative_expenditure_cr": 540.0,
                "actual_completion_date": "10/2025",
                "data_quality_flag": None,
            },
            # P300 completes at m2
            {
                "project_code": "300",
                "report_month": "2025-08",
                "project_name": "Project Gamma",
                "original_cost_cr": 800.0,
                "revised_cost_cr": 800.0,
                "cumulative_expenditure_cr": 790.0,
                "actual_completion_date": "08/2025",
                "data_quality_flag": None,
            },
        ]
    )

    panel_df, gaps_df = build_panel_df(
        ongoing_df=ongoing_df,
        completed_df=completed_df,
        canonical_df=canonical_df,
        all_corpus_months=corpus_months,
    )

    # 1. Computed Reconciliation Identity
    n_observed = len(panel_df)
    n_gaps = len(gaps_df)
    n_projects = len(canonical_df)
    n_months = len(corpus_months)
    grid_total = n_projects * n_months

    assert n_observed == 7
    assert n_gaps == 5
    assert n_observed + n_gaps == grid_total == 12

    # 2. Trap A: Mid-Window arrival elapsed time
    # P200 anchor is 01/2020. At m3 (2025-09), elapsed months must be (2025-2020)*12 + (9-1) = 68 months!
    p200_m3 = panel_df[
        (panel_df["project_id"] == "P200") & (panel_df["report_month"] == "2025-09")
    ].iloc[0]
    assert p200_m3["elapsed_months_since_anchor"] == 68.0
    assert bool(p200_m3["is_mid_window_arrival"]) is True
    assert p200_m3["project_size_band"] == "Mega"

    # 3. Trap B: Missing-Month Semantics (No forward fill)
    # P100 was missing at 2025-08. Assert NO row exists in panel for (P100, 2025-08)
    p100_m2 = panel_df[(panel_df["project_id"] == "P100") & (panel_df["report_month"] == "2025-08")]
    assert len(p100_m2) == 0

    # Assert 2025-08 is in gaps_df as 'unexplained_gap'
    p100_gap = gaps_df[(gaps_df["project_id"] == "P100") & (gaps_df["report_month"] == "2025-08")]
    assert len(p100_gap) == 1
    assert p100_gap.iloc[0]["gap_reason"] == "unexplained_gap"

    # 4. Trap C: Completed-Project Rows as Terminal Observed Anchors
    # P300 completed at 2025-08. Assert it IS an observed row with is_completed_this_month=True
    p300_comp = panel_df[
        (panel_df["project_id"] == "P300") & (panel_df["report_month"] == "2025-08")
    ].iloc[0]
    assert bool(p300_comp["is_completed_this_month"]) is True
    assert p300_comp["project_status"] == "Completed"
    assert p300_comp["physical_progress_pct"] == 100.0
    assert p300_comp["actual_completion_date"] == "08/2025"

    # Gaps for P300 are strictly months after completion (2025-09 and 2025-10)
    p300_gaps = gaps_df[gaps_df["project_id"] == "P300"]
    assert len(p300_gaps) == 2
    assert set(p300_gaps["report_month"]) == {"2025-09", "2025-10"}
    assert (p300_gaps["gap_reason"] == "completed").all()

    # Gap breakdown check
    gap_breakdown = gaps_df["gap_reason"].value_counts().to_dict()
    assert gap_breakdown["not_yet_onboarded"] == 2  # P200 at m1, m2
    assert gap_breakdown["completed"] == 2  # P300 at m3, m4
    assert gap_breakdown["unexplained_gap"] == 1  # P100 at m2

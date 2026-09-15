"""CI Fixture Test for STEP_05 EDA Feasibility Gate.

Tests observation depth, usable row calculation, positive class rates, and Scheme B
breakdowns against synthetic in-memory panel data.
NEVER skips in clean CI runner.
"""

from __future__ import annotations

import pandas as pd

from src.eda.eda_gate import (
    compute_observation_depth,
    compute_scheme_b_breakdown,
    compute_usable_rows_and_positives,
    parse_date_to_months,
)


def test_parse_date_to_months():
    """Verify parsing MM/YYYY and YYYY-MM into calendar months."""
    assert parse_date_to_months("03/2026") == 2026 * 12 + 3
    assert parse_date_to_months("2026-03") == 2026 * 12 + 3
    assert parse_date_to_months("(09/2024)") == 2024 * 12 + 9
    assert parse_date_to_months("-") is None
    assert parse_date_to_months(None) is None


def test_synthetic_observation_depth():
    """Verify observation depth calculation across baseline and mid-window projects."""
    canonical_df = pd.DataFrame(
        [
            {
                "canonical_project_id": "P1",
                "is_mid_window_arrival": False,
                "is_morth_onboarded_mid_window": False,
            },
            {
                "canonical_project_id": "P2",
                "is_mid_window_arrival": True,
                "is_morth_onboarded_mid_window": True,
            },
        ]
    )

    # P1 observed in 6 months, P2 observed in 3 months
    panel_df = pd.DataFrame(
        [{"project_id": "P1", "report_month": f"2025-{m:02d}"} for m in range(7, 13)]
        + [{"project_id": "P2", "report_month": f"2026-{m:02d}"} for m in range(1, 4)]
    )

    obs = compute_observation_depth(panel_df, canonical_df)
    assert obs["all_projects"]["total_projects"] == 2
    assert obs["all_projects"]["thresholds"]["ge_3_months"]["count"] == 2
    assert obs["all_projects"]["thresholds"]["ge_6_months"]["count"] == 1
    assert obs["baseline_projects"]["thresholds"]["ge_6_months"]["count"] == 1
    assert obs["mid_window_arrivals"]["thresholds"]["ge_6_months"]["count"] == 0


def test_synthetic_usable_rows_and_positives():
    """Verify Scheme A exclusion rule and positive event detection.

    Project A has 4 observations (m1, m2, m3, m4).
    At N=2:
      - m1 has 3 future months (>=2) -> USABLE
      - m2 has 2 future months (>=2) -> USABLE
      - m3 has 1 future month (<2) -> EXCLUDED
      - m4 has 0 future months (<2) -> EXCLUDED
    Total usable rows for Project A at N=2: 2 rows.
    """
    panel_df = pd.DataFrame(
        [
            {
                "project_id": "PA",
                "report_month": "2025-07",
                "revised_cost_cr": 100.0,
                "original_cost_cr": 100.0,
                "original_completion_date": "12/2026",
                "revised_completion_date": "12/2026",
            },
            {
                "project_id": "PA",
                "report_month": "2025-08",
                "revised_cost_cr": 100.0,
                "original_cost_cr": 100.0,
                "original_completion_date": "12/2026",
                "revised_completion_date": "12/2026",
            },
            {
                "project_id": "PA",
                "report_month": "2025-09",
                "revised_cost_cr": 110.0,  # 10% cost increase
                "original_cost_cr": 100.0,
                "original_completion_date": "12/2026",
                "revised_completion_date": "03/2027",  # 3 months schedule delay
            },
            {
                "project_id": "PA",
                "report_month": "2025-10",
                "revised_cost_cr": 110.0,
                "original_cost_cr": 100.0,
                "original_completion_date": "12/2026",
                "revised_completion_date": "03/2027",
            },
        ]
    )

    res = compute_usable_rows_and_positives(panel_df, candidate_horizons=(2,))
    assert res[2]["usable_rows"] == 2
    # At m1 (2025-07), window [m2, m3] sees cost 110 (+10%) and date 03/2027 (+3mo) -> POSITIVE
    # At m2 (2025-08), window [m3, m4] sees cost 110 (+10%) and date 03/2027 (+3mo) -> POSITIVE
    assert res[2]["cost_risk"]["ge_5pct"]["positives"] == 2
    assert res[2]["schedule_risk"]["ge_3mo"]["positives"] == 2


def test_synthetic_scheme_b_breakdown():
    """Verify clean Scheme B calculation and concentration check."""
    panel_df = pd.DataFrame(
        [
            # Clean completed with cost overrun & schedule slip
            {
                "project_id": "C1",
                "report_month": "2025-09",
                "is_completed_this_month": True,
                "original_cost_cr": 100.0,
                "revised_cost_cr": 120.0,
                "original_completion_date": "01/2025",
                "actual_completion_date": "06/2025",
                "sector": "Railways",
            },
            # Clean completed on time and budget
            {
                "project_id": "C2",
                "report_month": "2026-06",
                "is_completed_this_month": True,
                "original_cost_cr": 200.0,
                "revised_cost_cr": 200.0,
                "original_completion_date": "06/2026",
                "actual_completion_date": "06/2026",
                "sector": "Roads & Highways",
            },
            # Reversible project (705635)
            {
                "project_id": "705635",
                "report_month": "2026-02",
                "is_completed_this_month": True,
                "original_cost_cr": 500.0,
                "revised_cost_cr": 600.0,
                "original_completion_date": "01/2025",
                "actual_completion_date": "02/2026",
                "sector": "Railways",
            },
        ]
    )

    sb = compute_scheme_b_breakdown(panel_df)
    assert sb["gross_completed"] == 3
    assert sb["reversible_completed"] == 1
    assert sb["clean_completed"] == 2
    assert sb["cost_overrun_outcomes"]["count"] == 1
    assert sb["schedule_slip_outcomes"]["count"] == 1
    assert sb["neither_on_time_and_budget"]["count"] == 1
    assert sb["effective_independent_outcomes"] == 1  # 2 clean - 1 June = 1

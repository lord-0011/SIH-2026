"""Integration test suite for STEP_05 EDA Feasibility Gate on real data.

Skips cleanly in clean CI runners when DVC data is not pulled.
Runs locally / pre-merge to verify all DATA_INVENTORY §C sourced facts.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.eda.eda_gate import (
    compute_observation_depth,
    compute_scheme_b_breakdown,
    compute_structural_breaks,
    compute_usable_rows_and_positives,
)


@pytest.fixture(scope="module")
def eda_data():
    panel_path = Path("data/processed/panel.parquet")
    canonical_path = Path("data/interim/canonical_projects.parquet")

    if not panel_path.exists() or not canonical_path.exists():
        pytest.skip("Full dataset not available in this environment (DVC data not pulled)")

    panel_df = pd.read_parquet(panel_path)
    canonical_df = pd.read_parquet(canonical_path)

    return {"panel_df": panel_df, "canonical_df": canonical_df}


def test_observation_depth_real_data(eda_data):
    """Verify exact observations-per-project counts matching DATA_INVENTORY §C#3."""
    panel_df = eda_data["panel_df"]
    canonical_df = eda_data["canonical_df"]

    obs = compute_observation_depth(panel_df, canonical_df)

    assert obs["all_projects"]["total_projects"] == 2243
    assert obs["all_projects"]["thresholds"]["ge_3_months"]["count"] == 2138
    assert obs["all_projects"]["thresholds"]["ge_6_months"]["count"] == 1948
    assert obs["all_projects"]["thresholds"]["ge_9_months"]["count"] == 768
    assert obs["all_projects"]["thresholds"]["ge_12_months"]["count"] == 639

    # Baseline (902)
    assert obs["baseline_projects"]["total_projects"] == 902
    assert obs["baseline_projects"]["thresholds"]["ge_6_months"]["count"] == 805
    assert obs["baseline_projects"]["thresholds"]["ge_12_months"]["count"] == 639

    # Mid-window arrivals (1,341)
    assert obs["mid_window_arrivals"]["total_projects"] == 1341
    assert obs["mid_window_arrivals"]["thresholds"]["ge_3_months"]["count"] == 1283
    assert obs["mid_window_arrivals"]["thresholds"]["ge_6_months"]["count"] == 1143
    assert (
        obs["mid_window_arrivals"]["thresholds"]["ge_9_months"]["count"] == 0
    )  # Arrived Dec 2025+


def test_usable_rows_and_positives_real_data(eda_data):
    """Verify exact usable rows and positive rates per horizon matching DATA_INVENTORY §C#6."""
    panel_df = eda_data["panel_df"]

    usable = compute_usable_rows_and_positives(panel_df, candidate_horizons=(3, 6, 12))

    # Horizon N=3
    assert usable[3]["usable_rows"] == 12300
    assert usable[3]["cost_risk"]["gt_0pct"]["positives"] == 237
    assert usable[3]["cost_risk"]["ge_5pct"]["positives"] == 188
    assert usable[3]["schedule_risk"]["ge_1mo"]["positives"] == 4531
    assert usable[3]["schedule_risk"]["ge_3mo"]["positives"] == 3933

    # Horizon N=6
    assert usable[6]["usable_rows"] == 6258
    assert usable[6]["cost_risk"]["gt_0pct"]["positives"] == 272
    assert usable[6]["schedule_risk"]["ge_1mo"]["positives"] == 2638
    assert usable[6]["schedule_risk"]["ge_3mo"]["positives"] == 2510

    # Horizon N=12
    assert usable[12]["usable_rows"] == 557
    assert usable[12]["cost_risk"]["gt_0pct"]["positives"] == 115
    assert usable[12]["schedule_risk"]["ge_1mo"]["positives"] == 265


def test_scheme_b_breakdown_real_data(eda_data):
    """Verify clean Scheme B completed project breakdown matching DATA_INVENTORY §C#4."""
    panel_df = eda_data["panel_df"]

    sb = compute_scheme_b_breakdown(panel_df)

    assert sb["gross_completed"] == 259
    assert sb["reversible_completed"] == 1
    assert sb["clean_completed"] == 258
    assert sb["effective_independent_outcomes"] == 128  # 258 - 130 June completions

    assert sb["cost_overrun_outcomes"]["count"] == 97
    assert sb["schedule_slip_outcomes"]["count"] == 92
    assert sb["both_cost_and_schedule_slip"]["count"] == 31
    assert sb["neither_on_time_and_budget"]["count"] == 100


def test_structural_breaks_real_data(eda_data):
    """Verify structural breaks capture the March 2026 revised completion date reporting surge."""
    panel_df = eda_data["panel_df"]

    breaks = compute_structural_breaks(panel_df)
    b_map = {b["report_month"]: b for b in breaks}

    # Feb 2026 vs Mar 2026 revised completion date jump
    feb_pct = b_map["2026-02"]["pct_has_revised_completion_date"]
    mar_pct = b_map["2026-03"]["pct_has_revised_completion_date"]

    assert feb_pct < 55.0  # 50.56%
    assert mar_pct > 80.0  # 82.12%
    assert mar_pct - feb_pct > 30.0  # +31.56 percentage point reporting jump

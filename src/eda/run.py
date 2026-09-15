"""Stage: EDA Feasibility Gate — see docs/steps/STEP_05_eda.md.

Entry point: run(config). Reads data/processed/panel.parquet, computes
empirical observation depths, usable rows, positive class balances across horizons,
Scheme B breakdown, and structural breaks. Emits reports/eda_gate_summary.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.common.logging_setup import get_logger
from src.eda.eda_gate import (
    compute_event_rate_distributions,
    compute_observation_depth,
    compute_scheme_b_breakdown,
    compute_structural_breaks,
    compute_usable_rows_and_positives,
)

log = get_logger("eda")


def run(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute STEP_05 EDA Feasibility Gate."""
    config = config or {}
    processed_dir = Path(config.get("processed_dir", "data/processed"))
    interim_dir = Path(config.get("interim_dir", "data/interim"))
    reports_dir = Path(config.get("reports_dir", "reports"))
    reports_dir.mkdir(parents=True, exist_ok=True)

    log.info("Starting STEP_05 EDA Feasibility Gate...")

    panel_path = processed_dir / "panel.parquet"
    if not panel_path.exists():
        raise FileNotFoundError(f"Missing panel file: {panel_path}")
    panel_df = pd.read_parquet(panel_path)
    log.info(
        f"Loaded panel: {len(panel_df)} rows across {panel_df['project_id'].nunique()} projects."
    )

    canonical_path = interim_dir / "canonical_projects.parquet"
    if not canonical_path.exists():
        raise FileNotFoundError(f"Missing canonical projects file: {canonical_path}")
    canonical_df = pd.read_parquet(canonical_path)

    # 1. Observation depth
    log.info("Computing observation depth...")
    obs_depth = compute_observation_depth(panel_df, canonical_df)

    # 2. Usable rows and positive class balances per horizon
    log.info("Computing usable rows and positive rates across horizons N=3, 6, 12...")
    usable_rows = compute_usable_rows_and_positives(panel_df, candidate_horizons=(3, 6, 12))

    # 3. Event-base-rate reality check (empirical distributions)
    log.info("Computing empirical distribution percentiles for N=3...")
    event_distributions_n3 = compute_event_rate_distributions(panel_df, horizon=3)
    event_distributions_n6 = compute_event_rate_distributions(panel_df, horizon=6)

    # 4. Clean Scheme B breakdown
    log.info("Computing clean Scheme B completed project breakdown...")
    scheme_b = compute_scheme_b_breakdown(panel_df)

    # 5. Structural breaks
    log.info("Computing structural breaks across 13 months...")
    structural_breaks = compute_structural_breaks(panel_df)

    summary = {
        "observation_depth": obs_depth,
        "usable_rows_by_horizon": usable_rows,
        "event_distributions": {
            "horizon_3": event_distributions_n3,
            "horizon_6": event_distributions_n6,
        },
        "scheme_b_breakdown": scheme_b,
        "structural_breaks": structural_breaks,
    }

    out_file = reports_dir / "eda_gate_summary.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    log.info(f"Wrote EDA Gate summary to {out_file}")

    return summary


if __name__ == "__main__":
    summary = run()
    print("\n=======================================================")
    print("STEP_05 EDA FEASIBILITY GATE: SOURCED RESULTS")
    print("=======================================================")

    # 1. Observation depth
    obs = summary["observation_depth"]
    print("\n1. OBSERVATION DEPTH (Total Projects: 2,243)")
    print(
        f"  All Projects: >=3mo={obs['all_projects']['thresholds']['ge_3_months']['count']} ({obs['all_projects']['thresholds']['ge_3_months']['pct']}%), "
        f">=6mo={obs['all_projects']['thresholds']['ge_6_months']['count']} ({obs['all_projects']['thresholds']['ge_6_months']['pct']}%), "
        f">=9mo={obs['all_projects']['thresholds']['ge_9_months']['count']} ({obs['all_projects']['thresholds']['ge_9_months']['pct']}%), "
        f">=12mo={obs['all_projects']['thresholds']['ge_12_months']['count']} ({obs['all_projects']['thresholds']['ge_12_months']['pct']}%)"
    )
    print(
        f"  Baseline (902): >=3mo={obs['baseline_projects']['thresholds']['ge_3_months']['count']}, "
        f">=6mo={obs['baseline_projects']['thresholds']['ge_6_months']['count']}, "
        f">=9mo={obs['baseline_projects']['thresholds']['ge_9_months']['count']}, "
        f">=12mo={obs['baseline_projects']['thresholds']['ge_12_months']['count']}"
    )
    print(
        f"  Mid-Window (1,341): >=3mo={obs['mid_window_arrivals']['thresholds']['ge_3_months']['count']}, "
        f">=6mo={obs['mid_window_arrivals']['thresholds']['ge_6_months']['count']}, "
        f">=9mo=0 (by construction, arrived Dec 2025+), >=12mo=0"
    )

    # 2. Usable rows
    print("\n2. USABLE ROWS & POSITIVES ACROSS HORIZONS (Scheme A Exclusion Rule)")
    print(
        f"{'Horizon':<8} | {'Usable Rows':<12} | {'Cost Positives (>0%)':<22} | {'Sched Positives (>=1mo)':<25} | {'Sched Positives (>=3mo)':<25}"
    )
    print("-" * 100)
    for N, data in summary["usable_rows_by_horizon"].items():
        cost_p = (
            f"{data['cost_risk']['gt_0pct']['positives']} ({data['cost_risk']['gt_0pct']['pct']}%)"
        )
        sched_p1 = f"{data['schedule_risk']['ge_1mo']['positives']} ({data['schedule_risk']['ge_1mo']['pct']}%)"
        sched_p3 = f"{data['schedule_risk']['ge_3mo']['positives']} ({data['schedule_risk']['ge_3mo']['pct']}%)"
        print(
            f"N = {N:<4} | {data['usable_rows']:<12} | {cost_p:<22} | {sched_p1:<25} | {sched_p3:<25}"
        )

    # 3. Scheme B
    sb = summary["scheme_b_breakdown"]
    print(
        f"\n3. SCHEME B CLEAN REALIZED-OUTCOME ANCHOR (N = {sb['clean_completed']}, effective independent ~ {sb['effective_independent_outcomes']})"
    )
    print(
        f"  Cost Overrun (>0 Cr): {sb['cost_overrun_outcomes']['count']} ({sb['cost_overrun_outcomes']['pct']}%)"
    )
    print(
        f"  Schedule Slip (>0 mo): {sb['schedule_slip_outcomes']['count']} ({sb['schedule_slip_outcomes']['pct']}%)"
    )
    print(
        f"  Both Cost & Schedule Slip: {sb['both_cost_and_schedule_slip']['count']} ({sb['both_cost_and_schedule_slip']['pct']}%)"
    )
    print(
        f"  Neither (On-time & On-budget): {sb['neither_on_time_and_budget']['count']} ({sb['neither_on_time_and_budget']['pct']}%)"
    )

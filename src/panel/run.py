"""Stage: panel — see docs/steps/STEP_04_panel.md.

Entry point: run(config). Reads data/interim, writes data/processed/panel.parquet
and data/processed/panel_gaps.csv.
"""

from __future__ import annotations

import glob
from pathlib import Path
from typing import Any

import pandas as pd

from src.common.logging_setup import get_logger
from src.panel.builder import build_panel_df

log = get_logger("panel")


def run(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute STEP_04 Panel Assembly pipeline."""
    config = config or {}
    interim_dir = Path(config.get("interim_dir", "data/interim"))
    processed_dir = Path(config.get("processed_dir", "data/processed"))
    processed_dir.mkdir(parents=True, exist_ok=True)

    log.info("Starting STEP_04 panel assembly...")

    # 1. Load canonical projects
    canonical_path = interim_dir / "canonical_projects.parquet"
    if not canonical_path.exists():
        raise FileNotFoundError(f"Missing canonical projects file: {canonical_path}")
    canonical_df = pd.read_parquet(canonical_path)
    log.info(f"Loaded {len(canonical_df)} canonical projects.")

    # 2. Load matched ongoing parquets
    ongoing_pattern = str(interim_dir / "matched_ongoing_*.parquet")
    ongoing_files = sorted(glob.glob(ongoing_pattern))
    if not ongoing_files:
        raise FileNotFoundError(f"No matched ongoing files found at {ongoing_pattern}")
    log.info(f"Found {len(ongoing_files)} matched ongoing monthly files.")
    ongoing_dfs = [pd.read_parquet(f) for f in ongoing_files]
    ongoing_df = pd.concat(ongoing_dfs, ignore_index=True)
    log.info(f"Loaded {len(ongoing_df)} total ongoing records.")

    # 3. Load completed parquets
    completed_pattern = str(interim_dir / "raw_completed_*.parquet")
    completed_files = sorted(glob.glob(completed_pattern))
    log.info(f"Found {len(completed_files)} raw completed monthly files.")
    completed_dfs = [pd.read_parquet(f) for f in completed_files]
    completed_df = pd.concat(completed_dfs, ignore_index=True) if completed_dfs else pd.DataFrame()
    log.info(f"Loaded {len(completed_df)} total completed records.")

    # 4. Determine corpus months in order
    all_months_set = set(ongoing_df["report_month"].unique())
    if not completed_df.empty and "report_month" in completed_df.columns:
        all_months_set.update(completed_df["report_month"].unique())
    all_corpus_months = sorted(list(all_months_set))
    log.info(
        f"Corpus span: {len(all_corpus_months)} months ({all_corpus_months[0]} to {all_corpus_months[-1]})"
    )

    # 5. Build panel and gap dataframes
    panel_df, gaps_df = build_panel_df(
        ongoing_df=ongoing_df,
        completed_df=completed_df,
        canonical_df=canonical_df,
        all_corpus_months=all_corpus_months,
    )

    # 6. Verify hard invariants
    n_observed = len(panel_df)
    n_gaps = len(gaps_df)
    n_projects = len(canonical_df["canonical_project_id"].unique())
    n_months = len(all_corpus_months)
    grid_total = n_projects * n_months

    # First invariant: Computed Reconciliation Identity
    assert (
        n_observed + n_gaps == grid_total
    ), f"Reconciliation Identity failed: {n_observed} + {n_gaps} != {grid_total}"

    # Invariants for full 13-month corpus
    if n_months == 13 and n_projects == 2243:
        assert n_observed == 18860, f"Expected 18,860 observed rows, got {n_observed}"
        assert n_gaps == 10299, f"Expected 10,299 gaps, got {n_gaps}"
        assert panel_df["project_id"].nunique() == 2243
        gap_counts = gaps_df["gap_reason"].value_counts().to_dict()
        assert (
            gap_counts.get("not_yet_onboarded") == 8593
        ), f"Unexpected not_yet_onboarded: {gap_counts}"
        assert gap_counts.get("completed") == 684, f"Unexpected completed gaps: {gap_counts}"
        assert (
            gap_counts.get("unexplained_gap") == 1022
        ), f"Unexpected unexplained gaps: {gap_counts}"
        assert gap_counts.get("excluded_quality", 0) == 0

        # Trap A check: project 617907
        p617907 = panel_df[panel_df["project_id"] == "617907"]
        assert len(p617907) == 7  # 6 ongoing + 1 completed in 2026-06
        p617907_dec = p617907[p617907["report_month"] == "2025-12"].iloc[0]
        assert p617907_dec["elapsed_months_since_anchor"] == 39.0

    # 7. Write outputs
    panel_out = processed_dir / "panel.parquet"
    gaps_out = processed_dir / "panel_gaps.csv"

    panel_df.to_parquet(panel_out, index=False)
    gaps_df.to_csv(gaps_out, index=False)
    log.info(f"Wrote panel to {panel_out} ({len(panel_df)} rows, {len(panel_df.columns)} columns)")
    log.info(f"Wrote gaps to {gaps_out} ({len(gaps_df)} rows)")

    summary = {
        "n_projects": n_projects,
        "n_months": n_months,
        "grid_total": grid_total,
        "n_observed_rows": n_observed,
        "n_ongoing_rows": int((~panel_df["is_completed_this_month"]).sum()),
        "n_completed_rows": int(panel_df["is_completed_this_month"].sum()),
        "n_gap_cells": n_gaps,
        "gap_breakdown": gaps_df["gap_reason"].value_counts().to_dict(),
        "panel_path": str(panel_out),
        "gaps_path": str(gaps_out),
    }
    return summary


if __name__ == "__main__":
    summary = run()
    print("STEP_04 Panel Assembly Completed Successfully:")
    for k, v in summary.items():
        print(f"  {k}: {v}")

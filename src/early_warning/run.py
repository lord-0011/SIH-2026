"""Pipeline runner for Early Warning Trend Detection (STEP_12).

Loads risk_scores.parquet and features.parquet, evaluates consecutive observed
deterioration triggers, and saves early_warning.parquet and early_warning_summary.json.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.common.io import load_dataframe, save_dataframe
from src.early_warning.detector import compute_early_warnings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

RISK_SCORES_PATH = Path("data/processed/risk_scores.parquet")
FEATURES_PATH = Path("data/processed/features.parquet")
OUTPUT_PARQUET_PATH = Path("data/processed/early_warning.parquet")
OUTPUT_SUMMARY_PATH = Path("reports/early_warning_summary.json")


def run_early_warning_pipeline() -> pd.DataFrame:
    """Execute end-to-end early warning detection pipeline."""
    log.info("Loading risk scores from %s and features from %s...", RISK_SCORES_PATH, FEATURES_PATH)
    risk_scores_df = load_dataframe(RISK_SCORES_PATH)
    features_df = load_dataframe(FEATURES_PATH)

    log.info("Computing early warnings across %d project-month records...", len(risk_scores_df))
    ew_df = compute_early_warnings(risk_scores_df, features_df)

    # Invariant assertions
    assert len(ew_df) == len(
        risk_scores_df
    ), f"Row count mismatch: {len(ew_df)} vs {len(risk_scores_df)}"

    critical_cols = [
        "project_id",
        "report_month",
        "sector",
        "is_road",
        "data_sufficiency",
        "risk_score",
        "risk_band",
        "early_warning",
        "warning_status",
        "warning_strength",
        "triggers_fired",
    ]
    for c in critical_cols:
        null_cnt = ew_df[c].isnull().sum()
        assert null_cnt == 0, f"Critical column {c} has {null_cnt} nulls"

    log.info("Saving early warnings to %s...", OUTPUT_PARQUET_PATH)
    save_dataframe(ew_df, OUTPUT_PARQUET_PATH)

    # Compute diagnostics & summary
    latest_month = "2026-07"
    latest_df = ew_df[ew_df["report_month"] == latest_month]

    nr_latest = latest_df[~latest_df["is_road"]]
    roads_latest = latest_df[latest_df["is_road"]]

    # Example trigger traces (projects firing multiple triggers in latest month)
    multi_triggered = latest_df[latest_df["warning_strength"] >= 2]
    example_traces = []
    for pid in multi_triggered["project_id"].unique()[:3]:
        p_hist = ew_df[ew_df["project_id"] == pid].sort_values("report_month")
        recent = p_hist.tail(4)
        example_traces.append(
            {
                "project_id": str(pid),
                "sector": str(recent["sector"].iloc[-1]),
                "is_road": bool(recent["is_road"].iloc[-1]),
                "latest_month": latest_month,
                "warning_status": str(recent["warning_status"].iloc[-1]),
                "warning_strength": int(recent["warning_strength"].iloc[-1]),
                "triggers_fired": str(recent["triggers_fired"].iloc[-1]),
                "trajectory": [
                    {
                        "report_month": str(row["report_month"]),
                        "risk_score": float(row["risk_score"]),
                        "risk_band": str(row["risk_band"]),
                        "financial_physical_gap": float(np.round(row["financial_physical_gap"], 2)),
                        "progress_velocity_3mo": float(np.round(row["progress_velocity_3mo"], 2)),
                        "exp_velocity_3mo": float(np.round(row["exp_velocity_3mo"], 2)),
                        "early_warning": bool(row["early_warning"]),
                    }
                    for _, row in recent.iterrows()
                ],
            }
        )

    # Concrete steady-HIGH non-firing check (Project 400145)
    p400145 = ew_df[ew_df["project_id"] == "400145"]
    p400145_summary = {}
    if len(p400145) > 0:
        p400145_summary = {
            "project_id": "400145",
            "band": str(p400145["risk_band"].iloc[0]),
            "score_rising_fired_any_month": bool(p400145["score_rising_fired"].any()),
            "months_evaluated": len(p400145),
        }

    summary = {
        "step": "STEP_12_early_warning",
        "total_panel_rows": len(ew_df),
        "total_active_warnings": int(ew_df["early_warning"].sum()),
        "warning_status_distribution": ew_df["warning_status"].value_counts().to_dict(),
        "warning_strength_distribution": ew_df["warning_strength"].value_counts().to_dict(),
        "latest_month_metrics": {
            "month": latest_month,
            "total_projects": len(latest_df),
            "total_active_warnings": int(latest_df["early_warning"].sum()),
            "active_warning_rate_pct": round(float(latest_df["early_warning"].mean() * 100.0), 2),
            "non_roads": {
                "total_projects": len(nr_latest),
                "active_warnings": int(nr_latest["early_warning"].sum()),
                "warning_rate_pct": round(float(nr_latest["early_warning"].mean() * 100.0), 2),
                "strength_1": int((nr_latest["warning_strength"] == 1).sum()),
                "strength_2": int((nr_latest["warning_strength"] == 2).sum()),
                "strength_3": int((nr_latest["warning_strength"] == 3).sum()),
            },
            "roads_caveated_transfer": {
                "total_projects": len(roads_latest),
                "active_warnings": int(roads_latest["early_warning"].sum()),
                "warning_rate_pct": round(float(roads_latest["early_warning"].mean() * 100.0), 2),
                "strength_1": int((roads_latest["warning_strength"] == 1).sum()),
                "strength_2": int((roads_latest["warning_strength"] == 2).sum()),
                "strength_3": int((roads_latest["warning_strength"] == 3).sum()),
            },
            "triggers_breakdown_latest_month": {
                "score_rising_2m": int(latest_df["score_rising_fired"].sum()),
                "gap_widening_2m": int(latest_df["gap_widening_fired"].sum()),
                "velocity_divergence_2m": int(latest_df["velocity_divergence_fired"].sum()),
            },
        },
        "steady_high_negative_control": p400145_summary,
        "example_traces": example_traces,
    }

    OUTPUT_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    log.info("Saved summary diagnostics to %s", OUTPUT_SUMMARY_PATH)

    log.info(
        "STEP_12 Pipeline complete. Active warnings in latest month (%s): %d / %d (Non-Roads: %d, Roads: %d)",
        latest_month,
        latest_df["early_warning"].sum(),
        len(latest_df),
        nr_latest["early_warning"].sum(),
        roads_latest["early_warning"].sum(),
    )

    return ew_df


if __name__ == "__main__":
    run_early_warning_pipeline()

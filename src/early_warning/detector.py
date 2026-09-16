"""Early warning trend detector module (STEP_12).

Detects deteriorating projects based on trajectory worsening across consecutive
observed project reports (trend, not snapshot level).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# Default maximum calendar span across 3 observed rows (e.g., at most 1 missed reporting month)
MAX_OBSERVATION_SPAN_MONTHS = 4


def _to_month_int(m: str) -> int:
    """Convert YYYY-MM string to absolute month integer."""
    parts = str(m).strip().split("-")
    return int(parts[0]) * 12 + int(parts[1])


def compute_early_warnings(
    risk_scores_df: pd.DataFrame,
    features_df: pd.DataFrame,
    max_observation_span_months: int = MAX_OBSERVATION_SPAN_MONTHS,
) -> pd.DataFrame:
    """Compute trend-based early warning flags and evidence trails per project-month.

    Parameters
    ----------
    risk_scores_df : pd.DataFrame
        Scored project-months from STEP_11 with risk_score, risk_band, and data_sufficiency.
    features_df : pd.DataFrame
        Engineered feature table with financial_physical_gap, progress_velocity_3mo,
        and exp_velocity_3mo.
    max_observation_span_months : int, optional
        Maximum calendar month span between T and T_prev2. Defaults to 4 months.

    Returns
    -------
    pd.DataFrame
        DataFrame with early warning indicators, trigger flags, and full causal evidence.
    """
    feature_cols = [
        "project_id",
        "report_month",
        "financial_physical_gap",
        "progress_velocity_3mo",
        "exp_velocity_3mo",
    ]
    merged = risk_scores_df.merge(
        features_df[feature_cols],
        on=["project_id", "report_month"],
        how="inner",
    )

    merged["month_int"] = merged["report_month"].apply(_to_month_int)
    # Sort strictly chronologically per project
    merged = merged.sort_values(["project_id", "month_int"]).reset_index(drop=True)

    # Shifted values over project's observed rows
    grp = merged.groupby("project_id")

    # Prior month (T_prev1)
    merged["month_int_prev1"] = grp["month_int"].shift(1)
    merged["score_prev1"] = grp["risk_score"].shift(1)
    merged["gap_prev1"] = grp["financial_physical_gap"].shift(1)
    merged["prog_vel_prev1"] = grp["progress_velocity_3mo"].shift(1)
    merged["exp_vel_prev1"] = grp["exp_velocity_3mo"].shift(1)

    # Pre-prior month (T_prev2)
    merged["month_int_prev2"] = grp["month_int"].shift(2)
    merged["score_prev2"] = grp["risk_score"].shift(2)
    merged["gap_prev2"] = grp["financial_physical_gap"].shift(2)

    # Calendar spans
    merged["span_1m"] = merged["month_int"] - merged["month_int_prev1"]
    merged["total_span"] = merged["month_int"] - merged["month_int_prev2"]

    # Deltas
    merged["score_delta_1m"] = np.round(merged["risk_score"] - merged["score_prev1"], 2)
    merged["score_delta_2m"] = np.round(merged["risk_score"] - merged["score_prev2"], 2)

    merged["gap_delta_1m"] = np.round(merged["financial_physical_gap"] - merged["gap_prev1"], 2)
    merged["gap_delta_2m"] = np.round(merged["financial_physical_gap"] - merged["gap_prev2"], 2)

    # Pre-allocate output arrays
    n = len(merged)
    score_rising_fired = np.zeros(n, dtype=bool)
    gap_widening_fired = np.zeros(n, dtype=bool)
    vel_divergence_fired = np.zeros(n, dtype=bool)
    warning_strength = np.zeros(n, dtype=int)
    early_warning = np.zeros(n, dtype=bool)
    warning_status = ["INSUFFICIENT_HISTORY"] * n
    triggers_fired = ["none"] * n

    # Extract vectors for fast row-wise iteration
    scores = merged["risk_score"].values
    s_prev1 = merged["score_prev1"].values
    s_prev2 = merged["score_prev2"].values

    gaps = merged["financial_physical_gap"].values
    g_prev1 = merged["gap_prev1"].values
    g_prev2 = merged["gap_prev2"].values

    p_vel = merged["progress_velocity_3mo"].values
    p_vel_prev1 = merged["prog_vel_prev1"].values
    e_vel = merged["exp_velocity_3mo"].values
    e_vel_prev1 = merged["exp_vel_prev1"].values

    total_spans = merged["total_span"].values
    data_suff = merged["data_sufficiency"].values

    for i in range(n):
        # 1. Data sufficiency check: PROVISIONAL projects (<= 2 observed months) cannot trend
        if data_suff[i] == "PROVISIONAL" or pd.isna(s_prev2[i]):
            warning_status[i] = "INSUFFICIENT_HISTORY"
            continue

        # 2. Freshness check: total calendar span across 3 observed rows must be <= limit
        if total_spans[i] > max_observation_span_months:
            warning_status[i] = "STALE_HISTORY"
            continue

        # 3. Evaluate Trigger 1: Score trend rising across last 3 observed rows
        t1 = (scores[i] > s_prev1[i]) and (s_prev1[i] > s_prev2[i])

        # 4. Evaluate Trigger 2: Gap widening across last 3 observed rows
        t2 = (gaps[i] > g_prev1[i]) and (g_prev1[i] > g_prev2[i])

        # 5. Evaluate Trigger 3: Velocity divergence across last 2 observed rows
        # (Progress stagnant/negative while expenditure velocity is positive)
        t3 = (
            (p_vel[i] <= 0.0)
            and (e_vel[i] > 0.0)
            and (p_vel_prev1[i] <= 0.0)
            and (e_vel_prev1[i] > 0.0)
        )

        score_rising_fired[i] = t1
        gap_widening_fired[i] = t2
        vel_divergence_fired[i] = t3

        fired = []
        if t1:
            fired.append("score_rising_2m")
        if t2:
            fired.append("gap_widening_2m")
        if t3:
            fired.append("velocity_divergence_2m")

        cnt = len(fired)
        warning_strength[i] = cnt

        if cnt > 0:
            early_warning[i] = True
            warning_status[i] = "ACTIVE_WARNING"
            triggers_fired[i] = ",".join(fired)
        else:
            early_warning[i] = False
            warning_status[i] = "STABLE_OR_IMPROVING"
            triggers_fired[i] = "none"

    is_road = merged["sector"].astype(str).str.lower().str.contains("road")

    out_df = pd.DataFrame(
        {
            "project_id": merged["project_id"].values,
            "report_month": merged["report_month"].values,
            "sector": merged["sector"].values,
            "is_road": is_road.values,
            "data_sufficiency": data_suff,
            "risk_score": scores,
            "risk_band": merged["risk_band"].values,
            "risk_score_prev": s_prev1,
            "risk_score_delta_1m": merged["score_delta_1m"].values,
            "risk_score_delta_2m": merged["score_delta_2m"].values,
            "financial_physical_gap": gaps,
            "gap_delta_1m": merged["gap_delta_1m"].values,
            "gap_delta_2m": merged["gap_delta_2m"].values,
            "progress_velocity_3mo": p_vel,
            "exp_velocity_3mo": e_vel,
            "observation_span_months": total_spans,
            "score_rising_fired": score_rising_fired,
            "gap_widening_fired": gap_widening_fired,
            "velocity_divergence_fired": vel_divergence_fired,
            "triggers_fired": triggers_fired,
            "warning_strength": warning_strength,
            "early_warning": early_warning,
            "warning_status": warning_status,
        }
    )

    return out_df

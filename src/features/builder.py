"""Feature engineering builder for the PAIMANA Predictive Risk Platform.

Computes snapshot CUF features and trajectory DERIVED features per (project_id, report_month).
Strictly adheres to temporal causality: every feature at month T uses ONLY observations
with report_month <= T.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.common.logging_setup import get_logger

log = get_logger("features.builder")


def _to_month_int(val: Any) -> int | None:
    """Convert YYYY-MM, MM/YYYY, date, or Timestamp to integer month count (year * 12 + month)."""
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, pd.Timestamp | pd.Period):
        return val.year * 12 + val.month
    s = str(val).strip()
    if not s or s.lower() in ("none", "nan", "nat", "-"):
        return None
    try:
        if "/" in s:
            parts = s.split("/")
            return int(parts[1]) * 12 + int(parts[0])
        elif "-" in s:
            parts = s.split("-")
            return int(parts[0]) * 12 + int(parts[1])
    except Exception:
        return None
    return None


def compute_cuf_features(panel_df: pd.DataFrame) -> pd.DataFrame:
    """Compute snapshot features derivable strictly from a single month's raw CUF record.

    Every calculation operates strictly on the fields of that row at month T.
    """
    df = panel_df.copy()

    # 1. Cost CUF features
    orig_cost = pd.to_numeric(df["original_cost_cr"], errors="coerce").fillna(0.0)
    rev_cost = pd.to_numeric(df["revised_cost_cr"], errors="coerce").fillna(orig_cost)
    cum_exp = pd.to_numeric(df["cumulative_expenditure_cr"], errors="coerce").fillna(0.0)
    phys_prog = pd.to_numeric(df["physical_progress_pct"], errors="coerce").fillna(0.0)

    cost_esc_amt = rev_cost - orig_cost
    # Safe percentage escalation: only when original_cost > 0
    cost_esc_pct = np.where(orig_cost > 0, (cost_esc_amt / orig_cost) * 100.0, 0.0)

    # 2. Expenditure CUF features
    # exp_utilization = cum_exp / rev_cost
    safe_rev_cost = np.where(rev_cost > 0, rev_cost, np.where(orig_cost > 0, orig_cost, 1.0))
    exp_util = np.clip(cum_exp / safe_rev_cost, 0.0, 10.0)

    # 3. Schedule CUF features
    report_m_ints = df["report_month"].apply(_to_month_int)
    orig_comp_ints = df["original_completion_date"].apply(_to_month_int)
    rev_comp_ints = df["revised_completion_date"].apply(_to_month_int)
    start_ints = df["start_date"].apply(_to_month_int)
    appr_ints = df["date_of_approval"].apply(_to_month_int)

    # Planned duration (months): orig_completion - (start_date or date_of_approval)
    base_start_ints = start_ints.fillna(appr_ints)
    planned_dur = orig_comp_ints - base_start_ints

    # Elapsed duration (months): Uses elapsed_months_since_anchor from STEP_04 panel
    # This prevents the mid-window MoRTH arrival trap (anchoring to true start, not report appearance)
    elapsed_dur = pd.to_numeric(df["elapsed_months_since_anchor"], errors="coerce").fillna(0.0)

    # Effective completion date at T (revised if present, else original)
    eff_comp_ints = rev_comp_ints.fillna(orig_comp_ints)
    remaining_dur = eff_comp_ints - report_m_ints

    # Schedule variance at T: revised - original (0.0 if revised is null)
    sched_variance = np.where(
        rev_comp_ints.notna() & orig_comp_ints.notna(), rev_comp_ints - orig_comp_ints, 0.0
    )

    # Delay to date: max(0, report_month - original_completion_date)
    delay_to_date = np.maximum(0.0, report_m_ints - orig_comp_ints).fillna(0.0)

    # 4. Financial-Physical Gap: exp_utilization * 100 - physical_progress
    fin_phys_gap = (exp_util * 100.0) - phys_prog

    # 5. Context features
    def _calc_state_count(st: Any) -> int:
        if isinstance(st, list):
            return len(st)
        if isinstance(st, np.ndarray):
            return len(st)
        if pd.isna(st) or st is None:
            return 1
        s = str(st).strip()
        if s.startswith("[") and s.endswith("]"):
            return max(1, len(s.split(",")))
        return 1

    state_cnt = df["state"].apply(_calc_state_count)

    cuf_df = pd.DataFrame(
        {
            "project_id": df["project_id"],
            "report_month": df["report_month"],
            "cost_escalation_amt": cost_esc_amt.round(2),
            "cost_escalation_pct": cost_esc_pct.round(2),
            "exp_utilization": exp_util.round(4),
            "planned_duration_months": planned_dur.round(1),
            "elapsed_duration_months": elapsed_dur.round(1),
            "remaining_duration_months": remaining_dur.round(1),
            "schedule_variance_months": sched_variance.round(1),
            "delay_to_date_months": delay_to_date.round(1),
            "financial_physical_gap": fin_phys_gap.round(2),
            "state_count": state_cnt,
            "project_size_band": df["project_size_band"].fillna("Major"),
            "ministry": df["ministry"].fillna("Unknown"),
            "sector": df["sector"].fillna("Unknown"),
        }
    )
    return cuf_df


def _compute_project_trajectory_features(proj_df: pd.DataFrame) -> pd.DataFrame:
    """Compute strictly causal trailing trajectory features for a single project slice.

    Must receive rows sorted by report_month. Evaluates trailing features ending at each T.
    """
    p_df = proj_df.sort_values("report_month").copy()
    n_rows = len(p_df)

    m_ints = p_df["report_month"].apply(_to_month_int).values
    rev_costs = pd.to_numeric(p_df["revised_cost_cr"], errors="coerce").values
    cum_exps = pd.to_numeric(p_df["cumulative_expenditure_cr"], errors="coerce").values
    phys_progs = pd.to_numeric(p_df["physical_progress_pct"], errors="coerce").values
    fin_gaps = p_df["financial_physical_gap"].values
    rev_comp_ints = p_df["revised_completion_date"].apply(_to_month_int).values
    is_completed = (
        p_df["is_completed_this_month"].values
        if "is_completed_this_month" in p_df.columns
        else np.zeros(n_rows, dtype=bool)
    )

    cost_growth_3mo = np.zeros(n_rows, dtype=float)
    monthly_exp_chg = np.zeros(n_rows, dtype=float)
    exp_vel_3mo = np.zeros(n_rows, dtype=float)
    exp_acc_3mo = np.zeros(n_rows, dtype=float)
    monthly_prog_chg = np.zeros(n_rows, dtype=float)
    prog_vel_3mo = np.zeros(n_rows, dtype=float)
    prog_acc_3mo = np.zeros(n_rows, dtype=float)
    prog_stagnation = np.zeros(n_rows, dtype=int)
    gap_chg_3mo = np.zeros(n_rows, dtype=float)
    recent_deterioration = np.zeros(n_rows, dtype=int)
    first_rev_trailing_3mo = np.zeros(n_rows, dtype=int)

    for i in range(n_rows):
        T_m = m_ints[i]

        # 1. Cost growth rate over trailing up to 3 months (strictly <= T)
        trail_indices = [k for k in range(i + 1) if (T_m - m_ints[k]) <= 3]
        earliest_idx = trail_indices[0]
        if earliest_idx < i and rev_costs[earliest_idx] > 0:
            cost_growth_3mo[i] = (
                (rev_costs[i] - rev_costs[earliest_idx]) / rev_costs[earliest_idx]
            ) * 100.0

        # 2. Monthly expenditure change & velocity/acceleration
        if i > 0:
            monthly_exp_chg[i] = cum_exps[i] - cum_exps[i - 1]
            monthly_prog_chg[i] = phys_progs[i] - phys_progs[i - 1]
        else:
            monthly_exp_chg[i] = 0.0
            monthly_prog_chg[i] = 0.0

        # Rolling velocity: average monthly change over trailing observations in [T_m - 3, T_m]
        if len(trail_indices) > 1:
            chg_exp_slice = [monthly_exp_chg[k] for k in trail_indices[1:]]
            chg_prog_slice = [monthly_prog_chg[k] for k in trail_indices[1:]]
            exp_vel_3mo[i] = float(np.mean(chg_exp_slice))
            prog_vel_3mo[i] = float(np.mean(chg_prog_slice))
        else:
            exp_vel_3mo[i] = monthly_exp_chg[i]
            prog_vel_3mo[i] = monthly_prog_chg[i]

        # Acceleration: change in velocity from prior month
        if i > 0:
            exp_acc_3mo[i] = exp_vel_3mo[i] - exp_vel_3mo[i - 1]
            prog_acc_3mo[i] = prog_vel_3mo[i] - prog_vel_3mo[i - 1]
        else:
            exp_acc_3mo[i] = 0.0
            prog_acc_3mo[i] = 0.0

        # 3. Progress stagnation (PROVISIONAL threshold: progress velocity < 0.5% over trailing window)
        if len(trail_indices) >= 2 and phys_progs[i] < 95.0 and not is_completed[i]:
            if prog_vel_3mo[i] < 0.5:
                prog_stagnation[i] = 1

        # 4. Financial-Physical Gap change over trailing 3mo
        gap_chg_3mo[i] = fin_gaps[i] - fin_gaps[earliest_idx]

        # 5. Recent deterioration flag (PROVISIONAL tunable definition: >= 2 adverse conditions)
        cond1 = prog_vel_3mo[i] <= 0.2 or prog_acc_3mo[i] < 0
        cond2 = exp_vel_3mo[i] > 0 and prog_vel_3mo[i] <= 0
        cond3 = gap_chg_3mo[i] > 2.0
        adverse_count = int(cond1) + int(cond2) + int(cond3)
        if len(trail_indices) >= 2 and adverse_count >= 2:
            recent_deterioration[i] = 1

        # 6. First revised date entered in trailing 3 months (Mirror of STEP_05 exclusion logic)
        has_rev_now = pd.notna(rev_comp_ints[i])
        prior_to_window = [rev_comp_ints[k] for k in range(earliest_idx)]
        window_revs = [rev_comp_ints[k] for k in trail_indices]
        had_no_rev_before_window = all(pd.isna(r) for r in prior_to_window)
        entered_in_window = any(pd.notna(r) for r in window_revs)
        had_prior_null_obs = any(pd.isna(rev_comp_ints[k]) for k in range(i))

        if has_rev_now and had_no_rev_before_window and entered_in_window and had_prior_null_obs:
            first_rev_trailing_3mo[i] = 1

    p_df["cost_growth_rate_3mo"] = np.round(cost_growth_3mo, 2)
    p_df["monthly_exp_change"] = np.round(monthly_exp_chg, 2)
    p_df["exp_velocity_3mo"] = np.round(exp_vel_3mo, 2)
    p_df["exp_acceleration_3mo"] = np.round(exp_acc_3mo, 2)
    p_df["monthly_progress_change"] = np.round(monthly_prog_chg, 2)
    p_df["progress_velocity_3mo"] = np.round(prog_vel_3mo, 2)
    p_df["progress_acceleration_3mo"] = np.round(prog_acc_3mo, 2)
    p_df["progress_stagnation"] = prog_stagnation
    p_df["gap_change_3mo"] = np.round(gap_chg_3mo, 2)
    p_df["recent_deterioration"] = recent_deterioration
    p_df["first_revised_date_entered_in_trailing_3mo"] = first_rev_trailing_3mo

    return p_df


def compute_sector_historical_event_rate(
    panel_df: pd.DataFrame, horizon: int = 3, threshold: int = 3
) -> pd.Series:
    """Compute historical sector schedule-slip event rate strictly using fully-resolved events <= T.

    LEAKAGE DISCIPLINE (Refinement 1):
    A schedule slip labeled at month M requires observing project data through M + horizon.
    Therefore, at month T, an event at month M is ONLY fully determined and observable without
    future leakage if M + horizon <= T (i.e. M <= T - horizon).
    Any observation at month M > T - horizon is NOT yet fully resolved at month T and must NOT be counted.
    """
    df = panel_df.copy()
    m_ints = df["report_month"].apply(_to_month_int)
    df["_month_int"] = m_ints

    slip_events: list[dict[str, Any]] = []

    for pid, g in df.groupby("project_id"):
        g_sorted = g.sort_values("report_month")
        g_m_ints = g_sorted["_month_int"].values
        g_rev_ints = [_to_month_int(x) for x in g_sorted["revised_completion_date"]]
        g_orig_ints = [_to_month_int(x) for x in g_sorted["original_completion_date"]]
        g_eff_ints = [
            (g_rev_ints[k] if pd.notna(g_rev_ints[k]) else g_orig_ints[k])
            for k in range(len(g_sorted))
        ]
        g_sec = g_sorted["sector"].values

        n_g = len(g_sorted)
        for idx in range(n_g):
            m_M = g_m_ints[idx]
            rev_M = g_rev_ints[idx]
            eff_M = g_eff_ints[idx]
            sec_M = g_sec[idx]

            # Forward window (M, M + horizon]
            fwd_indices = [k for k in range(idx + 1, n_g) if 0 < (g_m_ints[k] - m_M) <= horizon]
            # Resolved only if forward horizon exists in observations
            if len(fwd_indices) == horizon:
                fwd_revs = [g_rev_ints[k] for k in fwd_indices]
                fwd_effs = [g_eff_ints[k] for k in fwd_indices if pd.notna(g_eff_ints[k])]

                # Clean transition condition (STEP_05 definition)
                is_clean_slip = 0
                if pd.notna(rev_M) and fwd_effs:
                    valid_fwd_rev = [r for r in fwd_revs if pd.notna(r)]
                    slip_amt = max(fwd_effs) - eff_M if pd.notna(eff_M) else 0
                    if slip_amt >= threshold and valid_fwd_rev and max(valid_fwd_rev) > rev_M:
                        is_clean_slip = 1

                slip_events.append(
                    {
                        "project_id": pid,
                        "month_int": m_M,
                        "resolved_month_int": m_M + horizon,
                        "sector": sec_M,
                        "is_clean_slip": is_clean_slip,
                    }
                )

    slips_df = pd.DataFrame(slip_events)

    sector_rates = np.zeros(len(df), dtype=float)

    if not slips_df.empty:
        unique_T_ints = sorted(df["_month_int"].dropna().unique())

        cache: dict[tuple[str, int], tuple[int, int]] = {}
        global_cache: dict[int, tuple[int, int]] = {}
        proj_cache: dict[tuple[Any, str, int], tuple[int, int]] = {}

        for T_int in unique_T_ints:
            sub = slips_df[slips_df["resolved_month_int"] <= T_int]
            if sub.empty:
                continue
            global_cache[T_int] = (int(sub["is_clean_slip"].sum()), len(sub))

            for sec, g in sub.groupby("sector"):
                cache[(sec, T_int)] = (int(g["is_clean_slip"].sum()), len(g))

            for (pid, sec), g in sub.groupby(["project_id", "sector"]):
                proj_cache[(pid, sec, T_int)] = (int(g["is_clean_slip"].sum()), len(g))

        for i, (pid, sec, T_int) in enumerate(
            zip(df["project_id"], df["sector"], df["_month_int"])
        ):
            if (sec, T_int) in cache:
                tot_slips, tot_count = cache[(sec, T_int)]
                if (pid, sec, T_int) in proj_cache:
                    p_slips, p_count = proj_cache[(pid, sec, T_int)]
                    tot_slips -= p_slips
                    tot_count -= p_count
                if tot_count >= 5:
                    sector_rates[i] = round(tot_slips / tot_count, 4)
                    continue

            if T_int in global_cache:
                g_slips, g_count = global_cache[T_int]
                if (pid, sec, T_int) in proj_cache:
                    p_slips, p_count = proj_cache[(pid, sec, T_int)]
                    g_slips -= p_slips
                    g_count -= p_count
                if g_count >= 5:
                    sector_rates[i] = round(g_slips / g_count, 4)

    return pd.Series(sector_rates, index=df.index, name="sector_hist_event_rate")


def compute_feature_table(panel_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Compute the complete feature table and machine-readable CUF vs DERIVED manifest.

    Returns:
        (feature_df, manifest_dict)
    """
    log.info("Computing CUF features (snapshot-level)...")
    cuf_df = compute_cuf_features(panel_df)

    work_df = panel_df.copy()
    work_df["financial_physical_gap"] = cuf_df["financial_physical_gap"]

    log.info("Computing project-level DERIVED trajectory features (strictly trailing <= T)...")
    proj_results = []
    for _, proj_group in work_df.groupby("project_id", sort=False):
        proj_results.append(_compute_project_trajectory_features(proj_group))
    derived_proj_df = pd.concat(proj_results, ignore_index=True)

    log.info("Computing cross-project historical sector event rate (strictly resolved <= T)...")
    sector_rate_series = compute_sector_historical_event_rate(panel_df, horizon=3, threshold=3)

    cuf_cols = get_cuf_feature_names()
    derived_cols = get_derived_feature_names()
    proj_trajectory_cols = [c for c in derived_cols if c != "sector_hist_event_rate"]

    feature_df = pd.DataFrame(
        {
            "project_id": cuf_df["project_id"].values,
            "report_month": cuf_df["report_month"].values,
        }
    )

    for c in cuf_cols:
        feature_df[c] = cuf_df[c].values

    feature_df["sector_hist_event_rate"] = sector_rate_series.values

    merged = pd.merge(
        feature_df,
        derived_proj_df[["project_id", "report_month"] + proj_trajectory_cols],
        on=["project_id", "report_month"],
        how="left",
    )

    manifest = {
        "cuf_features": {
            "count": len(cuf_cols),
            "columns": cuf_cols,
            "description": "Snapshot features computable strictly from a single month's raw CUF record.",
        },
        "derived_features": {
            "count": len(derived_cols),
            "columns": derived_cols,
            "description": "Trajectory, rolling velocity/acceleration, or cross-project historical features computed strictly from data <= T.",
            "provisional_tunable_thresholds": {
                "progress_stagnation": {
                    "threshold": "< 0.5% trailing progress velocity",
                    "status": "PROVISIONAL / TUNABLE",
                    "note": "Provisional heuristic; subject to hyperparameter tuning in modeling stages.",
                },
                "recent_deterioration": {
                    "threshold": ">= 2 adverse signals (progress deceleration, exp outpacing progress, gap widening > 2%)",
                    "status": "PROVISIONAL / TUNABLE",
                    "note": "Provisional composite heuristic; subject to feature selection.",
                },
            },
        },
        "all_features": {
            "total_count": len(cuf_cols) + len(derived_cols),
            "keys": ["project_id", "report_month"],
        },
    }

    return merged, manifest


def get_cuf_feature_names() -> list[str]:
    """Return the list of CUF feature column names."""
    return [
        "cost_escalation_amt",
        "cost_escalation_pct",
        "exp_utilization",
        "planned_duration_months",
        "elapsed_duration_months",
        "remaining_duration_months",
        "schedule_variance_months",
        "delay_to_date_months",
        "financial_physical_gap",
        "state_count",
        "project_size_band",
        "ministry",
        "sector",
    ]


def get_derived_feature_names() -> list[str]:
    """Return the list of DERIVED feature column names."""
    return [
        "cost_growth_rate_3mo",
        "monthly_exp_change",
        "exp_velocity_3mo",
        "exp_acceleration_3mo",
        "monthly_progress_change",
        "progress_velocity_3mo",
        "progress_acceleration_3mo",
        "progress_stagnation",
        "gap_change_3mo",
        "recent_deterioration",
        "first_revised_date_entered_in_trailing_3mo",
        "sector_hist_event_rate",
    ]

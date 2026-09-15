"""EDA Feasibility Gate analysis engine for STEP_05.

Provides pure functions to analyze observation depth, usable rows, positive class
balances across horizons, event distribution percentiles, Scheme B realized outcomes,
and structural breaks across the 13-month panel.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.common.logging_setup import get_logger

log = get_logger("eda.eda_gate")


def parse_date_to_months(d_str: Any) -> int | None:
    """Parse MM/YYYY or YYYY-MM into total calendar months (year * 12 + month)."""
    if d_str is None or pd.isna(d_str):
        return None
    s = str(d_str).strip("() ")
    if not s or s == "-":
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


def compute_observation_depth(panel_df: pd.DataFrame, canonical_df: pd.DataFrame) -> dict[str, Any]:
    """Compute observed-months-per-project distribution, split by baseline vs mid-window."""
    obs_by_proj = panel_df.groupby("project_id")["report_month"].nunique()

    meta = canonical_df.set_index("canonical_project_id")[
        ["is_mid_window_arrival", "is_morth_onboarded_mid_window"]
    ]
    df = pd.DataFrame({"obs_months": obs_by_proj}).join(meta)

    def _get_counts(sub_df: pd.DataFrame) -> dict[str, Any]:
        total = len(sub_df)
        counts = {}
        for k in [3, 6, 9, 12, 13]:
            c = int((sub_df["obs_months"] >= k).sum())
            pct = round(c / total * 100, 2) if total > 0 else 0.0
            counts[f"ge_{k}_months"] = {"count": c, "pct": pct}
        percentiles = {
            f"p{p}": float(np.percentile(sub_df["obs_months"], p)) for p in [10, 25, 50, 75, 90]
        }
        return {"total_projects": total, "thresholds": counts, "percentiles": percentiles}

    return {
        "all_projects": _get_counts(df),
        "baseline_projects": _get_counts(df[~df["is_mid_window_arrival"]]),
        "mid_window_arrivals": _get_counts(df[df["is_mid_window_arrival"]]),
    }


def compute_usable_rows_and_positives(
    panel_df: pd.DataFrame, candidate_horizons: tuple[int, ...] = (3, 6, 12)
) -> dict[int, dict[str, Any]]:
    """Compute usable labeled row counts and positive event rates under Scheme A.

    Scheme A exclusion rule: A row at month T is usable if and only if the project
    has >= N future observed months in the panel after T.
    """
    panel = panel_df.copy()
    target_date_str = panel["revised_completion_date"].fillna(panel["original_completion_date"])
    panel["completion_month_num"] = target_date_str.apply(parse_date_to_months)
    panel["cost_escalation_pct"] = (
        (panel["revised_cost_cr"] - panel["original_cost_cr"])
        / panel["original_cost_cr"].replace(0, np.nan)
        * 100.0
    ).fillna(0.0)

    # Build per-project trajectories
    trajectories = {}
    for pid, group in panel.groupby("project_id"):
        sorted_group = group.sort_values("report_month")
        trajectories[pid] = {
            "months": sorted_group["report_month"].tolist(),
            "costs": sorted_group["revised_cost_cr"].tolist(),
            "cost_escs": sorted_group["cost_escalation_pct"].tolist(),
            "dates": sorted_group["completion_month_num"].tolist(),
        }

    horizon_results = {}

    for N in candidate_horizons:
        rows = []
        for pid, traj in trajectories.items():
            t_months = traj["months"]
            n_obs = len(t_months)

            for i, m_T in enumerate(t_months):
                # Scheme A exclusion rule
                if (n_obs - 1 - i) < N:
                    continue

                cost_esc_T = traj["cost_escs"][i]
                date_T = traj["dates"][i]

                future_cost_escs = traj["cost_escs"][i + 1 : i + N + 1]
                future_dates = traj["dates"][i + 1 : i + N + 1]

                # Max cost escalation change in window
                delta_cost_esc = max(future_cost_escs) - cost_esc_T

                # Max schedule delay in window
                valid_future_dates = [d for d in future_dates if d is not None]
                if date_T is not None and valid_future_dates:
                    delta_sched = max(valid_future_dates) - date_T
                else:
                    delta_sched = None

                rows.append(
                    {
                        "project_id": pid,
                        "report_month": m_T,
                        "delta_cost_esc": delta_cost_esc,
                        "delta_sched_months": delta_sched,
                    }
                )

        rdf = pd.DataFrame(rows)
        n_usable = len(rdf)

        # Cost-risk positive checks (excluding zero/negative changes)
        cost_pos_any = int((rdf["delta_cost_esc"] > 0).sum())
        cost_pos_1 = int((rdf["delta_cost_esc"] >= 1.0).sum())
        cost_pos_5 = int((rdf["delta_cost_esc"] >= 5.0).sum())
        cost_pos_10 = int((rdf["delta_cost_esc"] >= 10.0).sum())

        # Schedule-risk positive checks (excluding schedule_advanced, delay only > 0)
        valid_sched = rdf["delta_sched_months"].dropna()
        sched_pos_1 = int((valid_sched >= 1).sum())
        sched_pos_2 = int((valid_sched >= 2).sum())
        sched_pos_3 = int((valid_sched >= 3).sum())
        sched_pos_6 = int((valid_sched >= 6).sum())
        sched_pos_12 = int((valid_sched >= 12).sum())

        horizon_results[N] = {
            "usable_rows": n_usable,
            "cost_risk": {
                "gt_0pct": {
                    "positives": cost_pos_any,
                    "pct": round(cost_pos_any / n_usable * 100, 2),
                },
                "ge_1pct": {"positives": cost_pos_1, "pct": round(cost_pos_1 / n_usable * 100, 2)},
                "ge_5pct": {"positives": cost_pos_5, "pct": round(cost_pos_5 / n_usable * 100, 2)},
                "ge_10pct": {
                    "positives": cost_pos_10,
                    "pct": round(cost_pos_10 / n_usable * 100, 2),
                },
            },
            "schedule_risk": {
                "ge_1mo": {"positives": sched_pos_1, "pct": round(sched_pos_1 / n_usable * 100, 2)},
                "ge_2mo": {"positives": sched_pos_2, "pct": round(sched_pos_2 / n_usable * 100, 2)},
                "ge_3mo": {"positives": sched_pos_3, "pct": round(sched_pos_3 / n_usable * 100, 2)},
                "ge_6mo": {"positives": sched_pos_6, "pct": round(sched_pos_6 / n_usable * 100, 2)},
                "ge_12mo": {
                    "positives": sched_pos_12,
                    "pct": round(sched_pos_12 / n_usable * 100, 2),
                },
            },
        }

    return horizon_results


def compute_schedule_contamination_analysis(
    panel_df: pd.DataFrame, horizon: int = 3
) -> dict[str, Any]:
    """Decompose schedule-risk positives to detect and isolate data-entry bulk population artifacts.

    Distinguishes between:
      1. existing_rev_moved_out: Project already had an active revised_completion_date at T,
         which was extended further into the future during (T, T+N] (strict transition).
      2. first_population_artifact: Project had NO revised_completion_date at T (revised was null),
         and a revised date was bulk-entered for the first time in (T, T+N] (data event).
    """
    panel = panel_df.copy()
    trajectories = {}
    for pid, group in panel.groupby("project_id"):
        sorted_group = group.sort_values("report_month")
        trajectories[pid] = {
            "months": sorted_group["report_month"].tolist(),
            "orig_dates": [
                parse_date_to_months(x) for x in sorted_group["original_completion_date"]
            ],
            "rev_dates": [parse_date_to_months(x) for x in sorted_group["revised_completion_date"]],
        }

    rows = []
    for pid, traj in trajectories.items():
        t_months = traj["months"]
        n_obs = len(t_months)
        orig_dates = traj["orig_dates"]
        rev_dates = traj["rev_dates"]

        for i, m_T in enumerate(t_months):
            if (n_obs - 1 - i) < horizon:
                continue

            has_rev_T = rev_dates[i] is not None
            rev_T = rev_dates[i]
            orig_T = orig_dates[i]
            eff_date_T = rev_T if has_rev_T else orig_T

            future_rev = rev_dates[i + 1 : i + horizon + 1]
            future_orig = orig_dates[i + 1 : i + horizon + 1]
            future_months = t_months[i + 1 : i + horizon + 1]

            future_eff = [
                future_rev[k] if future_rev[k] is not None else future_orig[k]
                for k in range(horizon)
            ]

            valid_future_eff = [d for d in future_eff if d is not None]
            slip_amount = (
                (max(valid_future_eff) - eff_date_T)
                if (eff_date_T is not None and valid_future_eff)
                else 0
            )

            # Detect first slip month
            slip_event_month = None
            for k in range(horizon):
                if (
                    future_eff[k] is not None
                    and eff_date_T is not None
                    and (future_eff[k] - eff_date_T) >= 3
                ):
                    slip_event_month = future_months[k]
                    break

            is_first_pop = (not has_rev_T) and any(r is not None for r in future_rev)
            is_exist_move = False
            if has_rev_T:
                valid_f_rev = [r for r in future_rev if r is not None]
                if valid_f_rev and max(valid_f_rev) > rev_T:
                    is_exist_move = True

            rows.append(
                {
                    "project_id": pid,
                    "origin_month": m_T,
                    "has_rev_T": has_rev_T,
                    "slip_amount": slip_amount,
                    "is_slip_ge_3": slip_amount >= 3,
                    "is_slip_ge_1": slip_amount >= 1,
                    "is_first_pop": is_first_pop,
                    "is_exist_move": is_exist_move,
                    "slip_event_month": slip_event_month,
                }
            )

    df = pd.DataFrame(rows)
    n_usable = len(df)
    n_has_rev_T = int(df["has_rev_T"].sum())

    # Decompose Y >= 3
    sub3 = df[df["is_slip_ge_3"]]
    exist_move_3 = int(((df["is_slip_ge_3"]) & (df["is_exist_move"])).sum())
    first_pop_3 = int(((df["is_slip_ge_3"]) & (df["is_first_pop"])).sum())
    other_3 = len(sub3) - exist_move_3 - first_pop_3

    # Decompose Y >= 1
    sub1 = df[df["is_slip_ge_1"]]
    exist_move_1 = int(((df["is_slip_ge_1"]) & (df["is_exist_move"])).sum())
    first_pop_1 = int(((df["is_slip_ge_1"]) & (df["is_first_pop"])).sum())
    other_1 = len(sub1) - exist_move_1 - first_pop_1

    # Monthly breakdown of origin T
    by_origin = {}
    for m, g in df.groupby("origin_month"):
        tot = len(g)
        gross_pos = int(g["is_slip_ge_3"].sum())
        clean_pos = int(((g["is_slip_ge_3"]) & (g["is_exist_move"])).sum())
        fpop_pos = int(((g["is_slip_ge_3"]) & (g["is_first_pop"])).sum())
        by_origin[m] = {
            "total_usable": tot,
            "gross_positives_ge3": gross_pos,
            "clean_positives_ge3": clean_pos,
            "first_pop_positives_ge3": fpop_pos,
            "clean_positive_pct": round(clean_pos / tot * 100, 2),
        }

    # Monthly breakdown of when slip event was recorded
    ge3_events = df[df["is_slip_ge_3"] & df["slip_event_month"].notna()]
    by_event_month = {}
    for em, g in ge3_events.groupby("slip_event_month"):
        clean_c = int(g["is_exist_move"].sum())
        fpop_c = int(g["is_first_pop"].sum())
        by_event_month[em] = {
            "clean_existing_rev_moved": clean_c,
            "first_population_artifact": fpop_c,
            "total": clean_c + fpop_c,
        }

    return {
        "horizon": horizon,
        "total_usable_rows": n_usable,
        "rows_with_existing_rev_at_T": {
            "count": n_has_rev_T,
            "pct": round(n_has_rev_T / n_usable * 100, 2),
        },
        "rows_with_null_rev_at_T": {
            "count": n_usable - n_has_rev_T,
            "pct": round((n_usable - n_has_rev_T) / n_usable * 100, 2),
        },
        "threshold_ge_3_months": {
            "gross_positives": len(sub3),
            "gross_positive_pct": round(len(sub3) / n_usable * 100, 2),
            "clean_existing_rev_moved_out": exist_move_3,
            "clean_positive_pct_all_rows": round(exist_move_3 / n_usable * 100, 2),
            "clean_positive_pct_rev_only": round(exist_move_3 / n_has_rev_T * 100, 2),
            "first_population_artifacts": first_pop_3,
            "first_population_share_of_positives": round(first_pop_3 / len(sub3) * 100, 2),
            "other_slips": other_3,
        },
        "threshold_ge_1_month": {
            "gross_positives": len(sub1),
            "gross_positive_pct": round(len(sub1) / n_usable * 100, 2),
            "clean_existing_rev_moved_out": exist_move_1,
            "clean_positive_pct_all_rows": round(exist_move_1 / n_usable * 100, 2),
            "first_population_artifacts": first_pop_1,
            "first_population_share_of_positives": round(first_pop_1 / len(sub1) * 100, 2),
            "other_slips": other_1,
        },
        "by_origin_month": by_origin,
        "by_event_recording_month": by_event_month,
    }


def compute_event_rate_distributions(panel_df: pd.DataFrame, horizon: int = 3) -> dict[str, Any]:
    """Compute empirical distribution percentiles for changes in cost escalation and schedule variance."""
    panel = panel_df.copy()
    target_date_str = panel["revised_completion_date"].fillna(panel["original_completion_date"])
    panel["completion_month_num"] = target_date_str.apply(parse_date_to_months)
    panel["cost_escalation_pct"] = (
        (panel["revised_cost_cr"] - panel["original_cost_cr"])
        / panel["original_cost_cr"].replace(0, np.nan)
        * 100.0
    ).fillna(0.0)

    trajectories = {}
    for pid, group in panel.groupby("project_id"):
        sorted_group = group.sort_values("report_month")
        trajectories[pid] = {
            "months": sorted_group["report_month"].tolist(),
            "cost_escs": sorted_group["cost_escalation_pct"].tolist(),
            "dates": sorted_group["completion_month_num"].tolist(),
        }

    delta_costs = []
    delta_scheds = []

    for pid, traj in trajectories.items():
        n_obs = len(traj["months"])
        for i in range(n_obs):
            if (n_obs - 1 - i) < horizon:
                continue
            cost_T = traj["cost_escs"][i]
            date_T = traj["dates"][i]

            future_cost_escs = traj["cost_escs"][i + 1 : i + horizon + 1]
            future_dates = traj["dates"][i + 1 : i + horizon + 1]

            delta_costs.append(max(future_cost_escs) - cost_T)

            valid_dates = [d for d in future_dates if d is not None]
            if date_T is not None and valid_dates:
                delta_scheds.append(max(valid_dates) - date_T)

    d_cost = np.array(delta_costs)
    d_sched = np.array(delta_scheds)

    percentiles = [50, 75, 80, 85, 90, 95, 98, 99]
    return {
        "horizon": horizon,
        "n_samples": len(delta_costs),
        "cost_escalation_pct_delta_percentiles": {
            f"p{p}": round(float(np.percentile(d_cost, p)), 2) for p in percentiles
        },
        "schedule_delay_months_delta_percentiles": {
            f"p{p}": round(float(np.percentile(d_sched, p)), 2) for p in percentiles
        },
    }


def compute_scheme_b_breakdown(panel_df: pd.DataFrame) -> dict[str, Any]:
    """Breakdown the 258 clean completed projects by cost overrun and schedule slip outcomes."""
    completed = panel_df[panel_df["is_completed_this_month"]].copy()

    # Direct exclusion of reversible completion (705635)
    clean_completed = completed[completed["project_id"] != "705635"].copy()
    n_clean = len(clean_completed)

    clean_completed["orig_date_num"] = clean_completed["original_completion_date"].apply(
        parse_date_to_months
    )
    clean_completed["act_date_num"] = clean_completed["actual_completion_date"].apply(
        parse_date_to_months
    )

    clean_completed["cost_overrun_cr"] = (
        clean_completed["revised_cost_cr"] - clean_completed["original_cost_cr"]
    )
    clean_completed["has_cost_overrun"] = clean_completed["cost_overrun_cr"] > 0

    clean_completed["sched_slip_months"] = (
        clean_completed["act_date_num"] - clean_completed["orig_date_num"]
    )
    clean_completed["has_schedule_slip"] = clean_completed["sched_slip_months"] > 0

    n_cost = int(clean_completed["has_cost_overrun"].sum())
    n_sched = int(clean_completed["has_schedule_slip"].sum())
    n_both = int((clean_completed["has_cost_overrun"] & clean_completed["has_schedule_slip"]).sum())
    n_neither = int(
        (~clean_completed["has_cost_overrun"] & ~clean_completed["has_schedule_slip"]).sum()
    )
    n_missing_date = int(clean_completed["sched_slip_months"].isna().sum())

    # Concentration check
    june_completions = int((clean_completed["report_month"] == "2026-06").sum())
    june_roads = int(
        (
            (clean_completed["report_month"] == "2026-06")
            & (clean_completed["sector"] == "Roads & Highways")
        ).sum()
    )
    effective_independent = n_clean - june_completions

    return {
        "gross_completed": len(completed),
        "reversible_completed": len(completed) - n_clean,
        "clean_completed": n_clean,
        "effective_independent_outcomes": effective_independent,
        "cost_overrun_outcomes": {
            "count": n_cost,
            "pct": round(n_cost / n_clean * 100, 2),
        },
        "schedule_slip_outcomes": {
            "count": n_sched,
            "pct": round(n_sched / n_clean * 100, 2),
            "missing_date_count": n_missing_date,
        },
        "both_cost_and_schedule_slip": {
            "count": n_both,
            "pct": round(n_both / n_clean * 100, 2),
        },
        "neither_on_time_and_budget": {
            "count": n_neither,
            "pct": round(n_neither / n_clean * 100, 2),
        },
        "june_2026_concentration": {
            "total_june": june_completions,
            "june_roads": june_roads,
        },
    }


def compute_structural_breaks(panel_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Compute monthly aggregates of cost, revised completion date, and expenditure across 13 months."""
    months = sorted(panel_df["report_month"].unique())
    ongoing = panel_df[~panel_df["is_completed_this_month"]]

    break_records = []
    for m in months:
        sub = ongoing[ongoing["report_month"] == m]
        c = len(sub)
        pct_cost_esc = float((sub["revised_cost_cr"] > sub["original_cost_cr"]).mean() * 100)
        pct_cost_down = float((sub["revised_cost_cr"] < sub["original_cost_cr"]).mean() * 100)
        pct_has_rev_date = float(sub["revised_completion_date"].notna().mean() * 100)
        exp_ratio = float(
            (sub["cumulative_expenditure_cr"] / sub["revised_cost_cr"].replace(0, np.nan)).median()
            * 100
        )

        break_records.append(
            {
                "report_month": m,
                "ongoing_project_count": c,
                "pct_cost_escalated": round(pct_cost_esc, 2),
                "pct_cost_revised_down": round(pct_cost_down, 2),
                "pct_has_revised_completion_date": round(pct_has_rev_date, 2),
                "median_expenditure_utilization_pct": round(exp_ratio, 2),
            }
        )

    return break_records

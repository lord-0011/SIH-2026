"""Labels generator for the PAIMANA Predictive Risk Platform.

Computes 3-month forward clean-transition schedule slip labels with universal
active-target filtering and temporal train/val/test split tagging.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.common.logging_setup import get_logger
from src.eda.eda_gate import parse_date_to_months

log = get_logger("labels.generator")


def generate_labels(
    panel_df: pd.DataFrame, horizon: int = 3, slip_threshold: int = 3
) -> pd.DataFrame:
    """Generate clean-transition schedule slip labels across the project panel.

    Rules applied:
      1. Scheme A Horizon Exclusion: Row at month T is usable only if >= horizon future
         observed months exist in the panel for that project.
      2. Clean Transition: Existing revised completion date at T must move further out
         in the forward window (T, T + horizon] by >= slip_threshold months.
         First-population artifacts (null -> populated) are excluded from the positive label.
      3. Universal Active-Target Filter (Remedy C): A project cannot have a forward
         operational slip from a target date that has already expired prior to T
         (revised_date < report_month at T). These are historical backlog dates, not
         active project targets.
      4. Temporal Split Tagging:
         - Train: report_month <= 2025-12
         - Val:   2026-01 <= report_month <= 2026-02
         - Test:  2026-03 <= report_month <= 2026-04
         - Censored: report_month >= 2026-05 (less than horizon future months)
    """
    log.info("Generating labels with horizon=%d, slip_threshold=%d", horizon, slip_threshold)

    trajectories = {}
    for pid, group in panel_df.groupby("project_id"):
        sorted_group = group.sort_values("report_month")
        trajectories[pid] = {
            "months": sorted_group["report_month"].tolist(),
            "orig_dates": [
                parse_date_to_months(x) for x in sorted_group["original_completion_date"]
            ],
            "rev_dates": [parse_date_to_months(x) for x in sorted_group["revised_completion_date"]],
            "rep_dates": [parse_date_to_months(x) for x in sorted_group["report_month"]],
            "sectors": sorted_group["sector"].tolist(),
            "is_morth": (
                sorted_group["is_morth_onboarded_mid_window"].iloc[0]
                if "is_morth_onboarded_mid_window" in sorted_group.columns
                else False
            ),
        }

    rows = []
    for pid, traj in trajectories.items():
        t_months = traj["months"]
        n_obs = len(t_months)
        orig_dates = traj["orig_dates"]
        rev_dates = traj["rev_dates"]
        rep_dates = traj["rep_dates"]
        sectors = traj["sectors"]

        for i, m_T in enumerate(t_months):
            has_future = (n_obs - 1 - i) >= horizon
            has_rev_T = rev_dates[i] is not None
            rev_T = rev_dates[i]
            orig_T = orig_dates[i]
            eff_date_T = rev_T if has_rev_T else orig_T
            rep_T = rep_dates[i]

            # Active-target check: did the project have an already-expired revised date?
            is_target_expired = bool(
                has_rev_T and rev_T is not None and rep_T is not None and rev_T < rep_T
            )

            if not has_future:
                rows.append(
                    {
                        "project_id": pid,
                        "report_month": m_T,
                        "sector": sectors[i],
                        "is_road": "road" in str(sectors[i]).lower(),
                        "target_slip_3m_ge3m": np.nan,
                        "is_clean_pos_raw": False,
                        "is_first_pop": False,
                        "is_target_expired": is_target_expired,
                        "is_usable_unfiltered": False,
                        "is_usable_filtered": False,
                        "slip_amount_months": 0,
                        "split": "censored",
                    }
                )
                continue

            future_rev = rev_dates[i + 1 : i + horizon + 1]
            future_orig = orig_dates[i + 1 : i + horizon + 1]
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

            is_first_pop = (not has_rev_T) and any(r is not None for r in future_rev)
            is_exist_move = False
            if has_rev_T:
                valid_f_rev = [r for r in future_rev if r is not None]
                if valid_f_rev and max(valid_f_rev) > rev_T:
                    is_exist_move = True

            is_clean_pos_raw = bool(slip_amount >= slip_threshold and is_exist_move)

            # Temporal split assignment
            if m_T <= "2025-12":
                split_label = "train"
            elif m_T <= "2026-02":
                split_label = "val"
            elif m_T <= "2026-04":
                split_label = "test"
            else:
                split_label = "censored"

            # Universal active-target filter: row is usable if target date not expired at T
            is_usable_filtered = not is_target_expired

            rows.append(
                {
                    "project_id": pid,
                    "report_month": m_T,
                    "sector": sectors[i],
                    "is_road": "road" in str(sectors[i]).lower(),
                    "target_slip_3m_ge3m": 1 if is_clean_pos_raw else 0,
                    "is_clean_pos_raw": is_clean_pos_raw,
                    "is_first_pop": is_first_pop,
                    "is_target_expired": is_target_expired,
                    "is_usable_unfiltered": True,
                    "is_usable_filtered": is_usable_filtered,
                    "slip_amount_months": slip_amount,
                    "split": split_label,
                }
            )

    labels_df = pd.DataFrame(rows)
    log.info(
        "Labels generated: %d total rows, %d usable unfiltered (%d raw pos), %d usable filtered (%d filtered pos)",
        len(labels_df),
        labels_df["is_usable_unfiltered"].sum(),
        labels_df["is_clean_pos_raw"].sum(),
        labels_df["is_usable_filtered"].sum(),
        int((labels_df["is_usable_filtered"] & (labels_df["target_slip_3m_ge3m"] == 1)).sum()),
    )
    return labels_df

"""Panel construction module for STEP_04.

Provides pure functions to assemble ongoing and completed project records into a
standardized project-month time-series panel, classify unobserved grid cells,
and enforce the reconciliation identity.
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from src.common.logging_setup import get_logger

log = get_logger("panel.builder")


def parse_state_list(state_val: Any) -> list[str]:
    """Parse raw state string or representation into a clean list of state names."""
    if state_val is None or pd.isna(state_val):
        return []
    if isinstance(state_val, list | tuple):
        return [str(s).strip() for s in state_val if str(s).strip()]

    s = str(state_val).strip()
    if not s or s == "-":
        return []

    if "Multi-States" in s or "(" in s:
        m = re.search(r"\((.*?)\)", s, re.DOTALL)
        content = m.group(1) if m else s.replace("Multi-States", "")
        parts = [
            re.sub(r"\s+", " ", p).strip()
            for p in content.split(",")
            if re.sub(r"\s+", " ", p).strip()
        ]
        return parts

    cleaned = re.sub(r"\s+", " ", s).strip()
    return [cleaned] if cleaned else []


def compute_elapsed_months(anchor_str: str | None, report_month_str: str | None) -> float | None:
    """Compute elapsed calendar months between anchor date and report month.

    Handles 'MM/YYYY' and 'YYYY-MM' format strings.
    Anchor is typically start_date or date_of_approval.
    """
    if not anchor_str or not report_month_str or pd.isna(anchor_str) or pd.isna(report_month_str):
        return None

    try:
        anchor_clean = str(anchor_str).strip()
        report_clean = str(report_month_str).strip()

        if "/" in anchor_clean:
            a_parts = anchor_clean.split("/")
            a_m, a_y = int(a_parts[0]), int(a_parts[1])
        elif "-" in anchor_clean:
            a_parts = anchor_clean.split("-")
            a_y, a_m = int(a_parts[0]), int(a_parts[1])
        else:
            return None

        r_parts = report_clean.split("-")
        r_y, r_m = int(r_parts[0]), int(r_parts[1])

        return float((r_y - a_y) * 12 + (r_m - a_m))
    except Exception:
        return None


def classify_project_gaps(
    canonical_project_id: str,
    observed_months: set[str],
    completion_month: str | None,
    all_corpus_months: list[str],
) -> list[dict[str, Any]]:
    """Classify absent project-month cells for a single canonical project.

    The completion month itself is an OBSERVED row in panel.parquet.
    Gaps for a completed project are strictly months after completion.
    Categories:
      - not_yet_onboarded: months strictly before the first observed month
      - completed: months strictly after appearance in Table 3 Completed
      - unexplained_gap: months where project dropped out between appearances
      - excluded_quality: reserved for data quality exclusions
    """
    gaps: list[dict[str, Any]] = []
    if not observed_months:
        return gaps

    first_m = min(observed_months)

    for m in all_corpus_months:
        if m in observed_months:
            continue  # Observed row, not a gap

        if m < first_m:
            reason = "not_yet_onboarded"
        elif completion_month is not None and m > completion_month:
            reason = "completed"
        else:
            reason = "unexplained_gap"

        gaps.append(
            {
                "project_id": str(canonical_project_id),
                "report_month": m,
                "gap_reason": reason,
            }
        )

    return gaps


def build_panel_df(
    ongoing_df: pd.DataFrame,
    completed_df: pd.DataFrame,
    canonical_df: pd.DataFrame,
    all_corpus_months: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Assemble panel dataframe and gap dataframe, verifying the reconciliation identity."""
    if all_corpus_months is None:
        all_months_set = set(ongoing_df["report_month"].unique())
        if not completed_df.empty and "report_month" in completed_df.columns:
            all_months_set.update(completed_df["report_month"].unique())
        all_corpus_months = sorted(list(all_months_set))

    # Map project_code to canonical metadata
    canon_map = canonical_df.set_index("project_code").to_dict(orient="index")

    # Standardize ongoing rows
    ongoing_rows: list[dict[str, Any]] = []
    for _, row in ongoing_df.iterrows():
        pcode = str(row.get("project_code", "")).strip()
        canon_meta = canon_map.get(pcode, {})
        pid = str(
            row.get("canonical_project_id") or canon_meta.get("canonical_project_id") or pcode
        )

        orig_cost = float(row["original_cost_cr"]) if pd.notna(row.get("original_cost_cr")) else 0.0
        size_band = "Mega" if orig_cost >= 1000.0 else "Major"

        anchor = (
            row.get("trajectory_anchor_date")
            or canon_meta.get("trajectory_anchor_date")
            or row.get("start_date")
            or row.get("date_of_approval")
        )
        rm = str(row["report_month"])
        elapsed = compute_elapsed_months(anchor, rm)

        ongoing_rows.append(
            {
                "project_id": pid,
                "project_code": pcode,
                "report_month": rm,
                "project_name": row.get("project_name", canon_meta.get("project_name", "")),
                "implementing_agency": row.get(
                    "implementing_agency", canon_meta.get("implementing_agency", "")
                ),
                "ministry": row.get("ministry", canon_meta.get("ministry", "")),
                "sector": row.get("sector", canon_meta.get("sector", "")),
                "state": parse_state_list(row.get("state", canon_meta.get("state", ""))),
                "project_size_band": size_band,
                "date_of_approval": row.get("date_of_approval", canon_meta.get("date_of_approval")),
                "start_date": row.get("start_date", canon_meta.get("start_date")),
                "original_completion_date": row.get("original_completion_date"),
                "revised_completion_date": row.get("revised_completion_date"),
                "original_cost_cr": orig_cost,
                "revised_cost_cr": (
                    float(row["revised_cost_cr"])
                    if pd.notna(row.get("revised_cost_cr"))
                    else orig_cost
                ),
                "cumulative_expenditure_cr": (
                    float(row["cumulative_expenditure_cr"])
                    if pd.notna(row.get("cumulative_expenditure_cr"))
                    else 0.0
                ),
                "physical_progress_pct": (
                    float(row["physical_progress_pct"])
                    if pd.notna(row.get("physical_progress_pct"))
                    else 0.0
                ),
                "project_status": "Ongoing",
                "data_quality_flag": row.get("data_quality_flag"),
                "match_confidence": row.get("match_confidence", "high"),
                "is_completed_this_month": False,
                "actual_completion_date": None,
                "first_appearance_month": canon_meta.get("first_appearance_month", rm),
                "is_mid_window_arrival": canon_meta.get("is_mid_window_arrival", False),
                "is_morth_onboarded_mid_window": canon_meta.get(
                    "is_morth_onboarded_mid_window", False
                ),
                "trajectory_anchor_date": anchor,
                "elapsed_months_since_anchor": elapsed,
            }
        )

    # Standardize completed rows
    completed_rows: list[dict[str, Any]] = []
    for _, row in completed_df.iterrows():
        pcode = str(row.get("project_code", "")).strip()
        canon_meta = canon_map.get(pcode, {})
        pid = str(
            row.get("canonical_project_id") or canon_meta.get("canonical_project_id") or pcode
        )

        orig_cost = float(row["original_cost_cr"]) if pd.notna(row.get("original_cost_cr")) else 0.0
        size_band = "Mega" if orig_cost >= 1000.0 else "Major"

        anchor = (
            canon_meta.get("trajectory_anchor_date")
            or row.get("start_date")
            or row.get("date_of_approval")
        )
        rm = str(row["report_month"])
        elapsed = compute_elapsed_months(anchor, rm)

        completed_rows.append(
            {
                "project_id": pid,
                "project_code": pcode,
                "report_month": rm,
                "project_name": row.get("project_name", canon_meta.get("project_name", "")),
                "implementing_agency": row.get(
                    "implementing_agency", canon_meta.get("implementing_agency", "")
                ),
                "ministry": row.get("ministry", canon_meta.get("ministry", "")),
                "sector": row.get("sector", canon_meta.get("sector", "")),
                "state": parse_state_list(row.get("state", canon_meta.get("state", ""))),
                "project_size_band": size_band,
                "date_of_approval": row.get("date_of_approval", canon_meta.get("date_of_approval")),
                "start_date": row.get("start_date", canon_meta.get("start_date")),
                "original_completion_date": row.get("original_completion_date"),
                "revised_completion_date": row.get("revised_completion_date"),
                "original_cost_cr": orig_cost,
                "revised_cost_cr": (
                    float(row["revised_cost_cr"])
                    if pd.notna(row.get("revised_cost_cr"))
                    else orig_cost
                ),
                "cumulative_expenditure_cr": (
                    float(row["cumulative_expenditure_cr"])
                    if pd.notna(row.get("cumulative_expenditure_cr"))
                    else 0.0
                ),
                "physical_progress_pct": 100.0,
                "project_status": "Completed",
                "data_quality_flag": row.get("data_quality_flag"),
                "match_confidence": "high",
                "is_completed_this_month": True,
                "actual_completion_date": row.get("actual_completion_date"),
                "first_appearance_month": canon_meta.get("first_appearance_month", rm),
                "is_mid_window_arrival": canon_meta.get("is_mid_window_arrival", False),
                "is_morth_onboarded_mid_window": canon_meta.get(
                    "is_morth_onboarded_mid_window", False
                ),
                "trajectory_anchor_date": anchor,
                "elapsed_months_since_anchor": elapsed,
            }
        )

    # Combine into panel dataframe
    all_rows = ongoing_rows + completed_rows
    panel_df = pd.DataFrame(all_rows)

    # Sort panel chronologically by project_id and report_month
    panel_df = panel_df.sort_values(by=["project_id", "report_month"]).reset_index(drop=True)

    # Assert 0 duplicate (project_id, report_month) pairs
    dup_mask = panel_df.duplicated(subset=["project_id", "report_month"], keep=False)
    if dup_mask.any():
        dup_rows = panel_df[dup_mask][["project_id", "report_month", "project_status"]]
        raise ValueError(
            f"Panel contains {dup_mask.sum()} duplicate (project_id, report_month) rows:\n{dup_rows}"
        )

    # Build gaps dataframe
    # Map observed months and completion month per canonical project
    project_obs: dict[str, set[str]] = {
        str(pid): set() for pid in canonical_df["canonical_project_id"].unique()
    }
    project_comp_month: dict[str, str] = {}

    for r in ongoing_rows:
        project_obs[r["project_id"]].add(r["report_month"])

    for r in completed_rows:
        project_obs[r["project_id"]].add(r["report_month"])
        project_comp_month[r["project_id"]] = r["report_month"]

    all_gap_records: list[dict[str, Any]] = []
    for pid in canonical_df["canonical_project_id"].unique():
        pid_str = str(pid)
        gaps = classify_project_gaps(
            canonical_project_id=pid_str,
            observed_months=project_obs.get(pid_str, set()),
            completion_month=project_comp_month.get(pid_str),
            all_corpus_months=all_corpus_months,
        )
        all_gap_records.extend(gaps)

    gaps_df = pd.DataFrame(all_gap_records)
    if not gaps_df.empty:
        gaps_df = gaps_df.sort_values(by=["project_id", "report_month"]).reset_index(drop=True)

    # RECONCILIATION IDENTITY (FIRST PANEL INVARIANT)
    n_observed = len(panel_df)
    n_gaps = len(gaps_df)
    n_projects = len(canonical_df["canonical_project_id"].unique())
    n_months = len(all_corpus_months)
    grid_total = n_projects * n_months

    log.info(
        f"Reconciliation Identity Check: observed={n_observed} + gaps={n_gaps} == "
        f"grid_total={grid_total} ({n_projects} projects x {n_months} months)"
    )

    if n_observed + n_gaps != grid_total:
        raise ValueError(
            f"Reconciliation Identity VIOLATED: observed ({n_observed}) + gaps ({n_gaps}) = "
            f"{n_observed + n_gaps} != grid_total ({grid_total}). "
            f"Difference = {(n_observed + n_gaps) - grid_total}"
        )

    return panel_df, gaps_df

"""Stage: matching — assigns canonical_project_id across all monthly project records.

Governed by docs/steps/STEP_03_matching.md, docs/04_DATA_SCHEMA.md, and ANTIGRAVITY.md.
Resolves identities using project_code as the primary stable key, provides fallback
cascade exception handling for missing codes, enforces no-merge and concurrency invariants,
and surfaces mid-window arrivals with trajectory anchor dates for STEP_04.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from src.common.config import DATA_INTERIM
from src.common.io import load_dataframe, save_dataframe
from src.common.logging_setup import get_logger
from src.matching.matcher import assign_canonical_id

log = get_logger("matching")


def run(config: dict | None = None) -> dict[str, Any]:
    """Execute entity matching across all raw interim ongoing project records."""
    cfg = config or {}
    interim_dir = Path(cfg.get("interim_dir", DATA_INTERIM))

    if not interim_dir.exists():
        raise FileNotFoundError(f"Interim data directory not found: {interim_dir}")

    ongoing_files = sorted(interim_dir.glob("raw_ongoing_*.parquet"))
    if not ongoing_files:
        raise FileNotFoundError(f"No raw ongoing parquet files found in {interim_dir}")

    log.info(
        "Starting entity matching across %d monthly files in %s", len(ongoing_files), interim_dir
    )

    # 1. Load all monthly datasets
    month_dfs: dict[str, pd.DataFrame] = {}
    for f in ongoing_files:
        df = load_dataframe(f)
        month = (
            df["report_month"].iloc[0]
            if "report_month" in df.columns and len(df) > 0
            else f.stem.split("_")[-2] + "-" + f.stem.split("_")[-1]
        )
        month_dfs[str(month)] = df

    all_records = pd.concat(list(month_dfs.values()), ignore_index=True)

    # 2. Identify Umbrella Legacy Codes (both single-month concurrency and corpus-wide)
    single_month_umbrellas = set()
    for m, group in all_records.groupby("report_month"):
        valid = group[group["legacy_ocms_code"].notna() & (group["legacy_ocms_code"] != "")]
        counts = valid.groupby("legacy_ocms_code")["project_code"].nunique()
        single_month_umbrellas.update(counts[counts > 1].index)

    valid_all = all_records[
        all_records["legacy_ocms_code"].notna() & (all_records["legacy_ocms_code"] != "")
    ]
    corpus_counts = valid_all.groupby("legacy_ocms_code")["project_code"].nunique()
    corpus_umbrellas = set(corpus_counts[corpus_counts > 1].index)

    log.info(
        "Umbrella legacy codes identified: %d single-month concurrent, %d corpus-wide",
        len(single_month_umbrellas),
        len(corpus_umbrellas),
    )

    # 3. Build Fallback Lookup Registry from records with project_code
    fallback_registry: dict[str, str] = {}
    for _, row in all_records.iterrows():
        pcode = row.get("project_code")
        if pcode and str(pcode).strip() not in ("nan", "None", ""):
            cid = str(pcode).strip()
            legacy = row.get("legacy_ocms_code")
            if (
                legacy
                and str(legacy).strip() not in ("-", "--", "", "nan", "None")
                and str(legacy).strip() not in corpus_umbrellas
            ):
                fallback_registry[f"legacy:{str(legacy).strip()}"] = cid
            pmgid = row.get("pmgid")
            if pmgid and str(pmgid).strip() not in ("-", "--", "", "nan", "None"):
                fallback_registry[f"pmgid:{str(pmgid).strip()}"] = cid

    # 4. First Appearance Month & Trajectory Anchor Date Determination
    first_seen = all_records.groupby("project_code")["report_month"].min().to_dict()

    # Anchor date per canonical project: earliest valid start_date or date_of_approval
    def extract_anchor_date(group: pd.DataFrame) -> str | None:
        starts = group["start_date"].dropna().unique()
        valid_starts = [s for s in starts if s not in ("-", "--", "")]
        if valid_starts:
            return valid_starts[0]
        approvals = group["date_of_approval"].dropna().unique()
        valid_approvals = [a for a in approvals if a not in ("-", "--", "")]
        if valid_approvals:
            return valid_approvals[0]
        return None

    anchor_dates = (
        all_records.groupby("project_code")[["start_date", "date_of_approval"]]
        .apply(extract_anchor_date)
        .to_dict()
    )

    # 5. Process each month: assign canonical IDs and trajectory metadata
    audit_rows = []
    matched_month_dfs = {}

    for month_str, df in month_dfs.items():
        canonical_ids = []
        confidences = []
        rules = []
        evidences = []
        is_mid_window_list = []
        is_morth_mid_window_list = []
        anchor_date_list = []

        for _, row in df.iterrows():
            cid, conf, rule, evid = assign_canonical_id(
                row,
                registry=fallback_registry,
                umbrella_legacy_codes=corpus_umbrellas,
            )
            canonical_ids.append(cid)
            confidences.append(conf)
            rules.append(rule)
            evidences.append(evid)

            f_month = first_seen.get(cid, month_str)
            is_mid = bool(f_month >= "2025-12")
            is_morth = bool(
                is_mid
                and str(row.get("ministry", "")).strip() == "Ministry of Road Transport & Highways"
            )

            is_mid_window_list.append(is_mid)
            is_morth_mid_window_list.append(is_morth)
            anchor_date_list.append(
                anchor_dates.get(cid, row.get("start_date") or row.get("date_of_approval"))
            )

        matched_df = df.copy()
        matched_df["canonical_project_id"] = canonical_ids
        matched_df["match_confidence"] = confidences
        matched_df["match_rule"] = rules
        matched_df["match_evidence"] = evidences
        matched_df["first_appearance_month"] = [
            first_seen.get(cid, month_str) for cid in canonical_ids
        ]
        matched_df["is_mid_window_arrival"] = is_mid_window_list
        matched_df["is_morth_onboarded_mid_window"] = is_morth_mid_window_list
        matched_df["trajectory_anchor_date"] = anchor_date_list

        # INVARIANT 1: Concurrency (no duplicate canonical_project_ids in same month)
        if matched_df["canonical_project_id"].duplicated().any():
            dups = matched_df[matched_df["canonical_project_id"].duplicated(keep=False)][
                "canonical_project_id"
            ].tolist()
            raise ValueError(
                f"Concurrency invariant violated in month {month_str}: duplicate canonical_project_ids found: {dups[:5]}"
            )

        matched_month_dfs[month_str] = matched_df

        # Save matched parquet alongside raw
        clean_month = month_str.replace("-", "_")
        save_dataframe(matched_df, interim_dir / f"matched_ongoing_{clean_month}.parquet")

        # Record monthly audit counts
        conf_counts = matched_df["match_confidence"].value_counts().to_dict()
        mid_count = sum(is_mid_window_list)
        morth_mid_count = sum(is_morth_mid_window_list)
        non_morth_mid_count = mid_count - morth_mid_count

        audit_rows.append(
            {
                "report_month": month_str,
                "total_records": len(matched_df),
                "exact_code_matches": conf_counts.get("exact_code", 0),
                "fallback_matches": conf_counts.get("fallback", 0),
                "unmatched_records": conf_counts.get("unmatched", 0),
                "distinct_projects_this_month": matched_df["canonical_project_id"].nunique(),
                "mid_window_arrivals_active": mid_count,
                "morth_mid_window_active": morth_mid_count,
                "non_morth_mid_window_active": non_morth_mid_count,
            }
        )

    # 6. Global Corpus-Wide INVARIANT 2: No merge of distinct project codes
    all_matched = pd.concat(list(matched_month_dfs.values()), ignore_index=True)
    distinct_pcodes = all_matched["project_code"].nunique()
    distinct_cids = all_matched["canonical_project_id"].nunique()
    if distinct_pcodes != distinct_cids:
        raise ValueError(
            f"No-merge invariant violated: {distinct_pcodes} distinct project_codes mapped to {distinct_cids} canonical IDs!"
        )

    # 7. Build and Save Canonical Projects Registry
    canonical_projects = (
        all_matched.groupby("canonical_project_id")
        .agg(
            project_code=("project_code", "first"),
            project_name=("project_name", "first"),
            implementing_agency=("implementing_agency", "first"),
            ministry=("ministry", "first"),
            sector=("sector", "first"),
            state=("state", "first"),
            date_of_approval=("date_of_approval", "first"),
            start_date=("start_date", "first"),
            first_appearance_month=("first_appearance_month", "first"),
            is_mid_window_arrival=("is_mid_window_arrival", "first"),
            is_morth_onboarded_mid_window=("is_morth_onboarded_mid_window", "first"),
            trajectory_anchor_date=("trajectory_anchor_date", "first"),
            total_months_observed=("report_month", "nunique"),
        )
        .reset_index()
    )
    save_dataframe(canonical_projects, interim_dir / "canonical_projects.parquet")

    # 8. Save Matching Audit Log
    audit_df = pd.DataFrame(audit_rows)
    audit_df.to_csv(interim_dir / "matching_audit.csv", index=False)

    total_canonical = len(canonical_projects)
    total_mid_window = canonical_projects["is_mid_window_arrival"].sum()
    total_morth_mid = canonical_projects["is_morth_onboarded_mid_window"].sum()
    total_non_morth_mid = total_mid_window - total_morth_mid

    log.info(
        "Matching completed: %d total records across 13 months, %d distinct canonical projects",
        len(all_matched),
        total_canonical,
    )
    log.info(
        "Arrival breakdown: %d baseline (<=2025-11), %d mid-window arrivals (>=2025-12: %d MoRTH + %d non-MoRTH)",
        total_canonical - total_mid_window,
        total_mid_window,
        total_morth_mid,
        total_non_morth_mid,
    )

    return {
        "total_records": len(all_matched),
        "total_canonical_projects": total_canonical,
        "baseline_projects": total_canonical - total_mid_window,
        "mid_window_arrivals": int(total_mid_window),
        "morth_mid_window_arrivals": int(total_morth_mid),
        "non_morth_mid_window_arrivals": int(total_non_morth_mid),
        "single_month_umbrella_legacy_codes": len(single_month_umbrellas),
        "corpus_umbrella_legacy_codes": len(corpus_umbrellas),
    }


if __name__ == "__main__":
    run()

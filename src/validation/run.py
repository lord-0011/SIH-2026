"""Stage: validation — applies validation rules to raw ingested records.

Governed by docs/steps/STEP_02_validation.md, docs/04_DATA_SCHEMA.md, and ANTIGRAVITY.md.
Never deletes records. Attaches data_quality_flag to records and produces
a full audit log with project, month, flag, and human-readable reason.
"""

from pathlib import Path
from typing import Any

import pandas as pd

from src.common.io import load_dataframe, save_dataframe
from src.common.logging_setup import get_logger
from src.validation.rules import validate_record

log = get_logger("validation")


def validate_dataframe(
    df: pd.DataFrame, table_type: str, report_month: str
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Apply validation rules to all records in a dataframe.

    Returns:
        (validated_df, audit_records)
        where validated_df has the 'data_quality_flag' column populated,
        and audit_records contains one entry per triggered issue.
    """
    audit_records: list[dict[str, Any]] = []
    flags_col: list[str | None] = []

    for _, row in df.iterrows():
        issues = validate_record(row)
        if issues:
            unique_flags = sorted({issue.flag for issue in issues})
            flags_col.append(";".join(unique_flags))
            for issue in issues:
                audit_records.append(
                    {
                        "report_month": report_month,
                        "table_type": table_type,
                        "project_code": row.get("project_code", ""),
                        "project_name": row.get("project_name", ""),
                        "implementing_agency": row.get("implementing_agency", ""),
                        "ministry": row.get("ministry", ""),
                        "sector": row.get("sector", ""),
                        "flag": issue.flag,
                        "reason": issue.reason,
                        "column": issue.column or "",
                        "value": str(issue.value) if issue.value is not None else "",
                    }
                )
        else:
            flags_col.append(None)

    validated_df = df.copy()
    validated_df["data_quality_flag"] = flags_col
    return validated_df, audit_records


def run(config: dict | None = None) -> dict[str, Any]:
    """Run data validation across all raw interim parquet files."""
    cfg = config or {}
    interim_dir = Path(cfg.get("interim_dir", "data/interim"))

    if not interim_dir.exists():
        raise FileNotFoundError(f"Interim data directory not found: {interim_dir}")

    parquet_files = sorted(interim_dir.glob("raw_*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No raw parquet files found in {interim_dir}")

    all_audit_records: list[dict[str, Any]] = []
    total_records = 0
    total_flagged_records = 0
    files_processed = 0

    log.info("Starting validation across %d files in %s", len(parquet_files), interim_dir)

    for pfile in parquet_files:
        name = pfile.name
        # Determine table_type from filename: raw_ongoing_YYYY_MM, raw_completed_YYYY_MM, raw_newly_added_YYYY_MM
        if "ongoing" in name:
            table_type = "ongoing"
        elif "completed" in name:
            table_type = "completed"
        elif "newly_added" in name:
            table_type = "newly_added"
        else:
            table_type = "unknown"

        df = load_dataframe(pfile)
        month = (
            df["report_month"].iloc[0]
            if "report_month" in df.columns and len(df) > 0
            else "unknown"
        )

        validated_df, audits = validate_dataframe(
            df, table_type=table_type, report_month=str(month)
        )
        save_dataframe(validated_df, pfile)

        flagged_count = validated_df["data_quality_flag"].notna().sum()
        total_records += len(df)
        total_flagged_records += int(flagged_count)
        files_processed += 1
        all_audit_records.extend(audits)

        log.info(
            "Validated %s: %d records, %d flagged (%d total issues)",
            name,
            len(df),
            flagged_count,
            len(audits),
        )

    # Save audit log
    audit_df = pd.DataFrame(all_audit_records)
    audit_csv_path = interim_dir / "validation_log.csv"
    audit_parquet_path = interim_dir / "validation_log.parquet"
    save_dataframe(audit_df, audit_csv_path)
    save_dataframe(audit_df, audit_parquet_path)

    # Save validation report summary (counts per flag per month)
    if not audit_df.empty:
        summary_df = (
            audit_df.groupby(["report_month", "table_type", "flag"])
            .size()
            .reset_index(name="issue_count")
        )
        flag_totals = audit_df["flag"].value_counts().to_dict()
    else:
        summary_df = pd.DataFrame(columns=["report_month", "table_type", "flag", "issue_count"])
        flag_totals = {}

    summary_csv_path = interim_dir / "validation_report.csv"
    save_dataframe(summary_df, summary_csv_path)

    log.info(
        "Validation complete. Processed %d records across %d files. %d records flagged. %d issues logged.",
        total_records,
        files_processed,
        total_flagged_records,
        len(all_audit_records),
    )
    log.info("Issue breakdown across corpus: %s", flag_totals)

    return {
        "files_processed": files_processed,
        "total_records": total_records,
        "total_flagged_records": total_flagged_records,
        "total_issues_logged": len(all_audit_records),
        "flag_breakdown": flag_totals,
        "audit_log_path": str(audit_csv_path),
        "report_path": str(summary_csv_path),
    }


if __name__ == "__main__":
    run()

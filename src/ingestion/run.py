"""Stage: ingestion — parse Flash Report PDFs into raw tables in data/interim/.

Preserves source month and source document name.
Splits paired visual cells into distinct columns.
Does NOT clean or validate; preserves raw strings and parsed values.
Generates data/interim/ingestion_summary.csv for all processed months.
"""

import concurrent.futures
import os
from pathlib import Path
from typing import Any

import pandas as pd
import pdfplumber

from src.common.config import DATA_INTERIM, REPORTS
from src.common.io import save_dataframe
from src.common.logging_setup import get_logger
from src.ingestion.parser import parse_flash_report

log = get_logger("ingestion")

MONTHLY_REPORTS = [
    ("2025-07", "FlashReport_July_2025.pdf"),
    ("2025-08", "FlashReport_August_2025.pdf"),
    ("2025-09", "FlashReport_September_2025.pdf"),
    ("2025-10", "FlashReport_October_2025.pdf"),
    ("2025-11", "FlashReport_November_2025.pdf"),
    ("2025-12", "FlashReport_December_2025.pdf"),
    ("2026-01", "FlashReport_January_2026 (1).pdf"),
    ("2026-02", "FlashReport_February_2026.pdf"),
    ("2026-03", "FlashReport_March_2026.pdf"),
    ("2026-04", "FlashReport_April2026.pdf"),
    ("2026-05", "FlashReport_May2026.pdf"),
    ("2026-06", "FlashReport_June_2026.pdf"),
    ("2026-07", "FlashReport_July_2026.pdf"),
]


def ingest_single_report(pdf_path: Path, source_month: str) -> dict[str, Any]:
    """Ingest a single Flash Report PDF and save parquets."""
    log.info("Starting ingestion for %s (month: %s)", pdf_path.name, source_month)
    results = parse_flash_report(pdf_path, source_month=source_month)

    clean_month = source_month.replace("-", "_")
    output_paths = {}

    for table_name in ("ongoing", "completed", "newly_added"):
        df = results.get(table_name)
        if not isinstance(df, pd.DataFrame) or df.empty:
            log.info("Table %s is empty or not present for %s", table_name, source_month)
            continue
        out_file = DATA_INTERIM / f"raw_{table_name}_{clean_month}.parquet"
        save_dataframe(df, out_file)
        output_paths[table_name] = out_file
        log.info("Saved %s (%d rows) to %s", table_name, len(df), out_file)

    results["output_paths"] = output_paths
    return results


def process_report_task(source_month: str, pdf_path: Path) -> dict[str, Any]:
    """Process a single monthly report PDF and return metadata and summary dict."""
    if not pdf_path.exists():
        log.warning("Report file not found: %s", pdf_path)
        return {}

    with pdfplumber.open(pdf_path) as doc:
        page_count = len(doc.pages)

    res = ingest_single_report(pdf_path, source_month=source_month)

    df_ongoing = res["ongoing"]
    df_completed = res["completed"]
    df_newly_added = res["newly_added"]
    t1 = res.get("table1_summary", {})

    ongoing_count = len(df_ongoing)
    completed_count = len(df_completed) if isinstance(df_completed, pd.DataFrame) else 0
    newly_added_count = len(df_newly_added) if isinstance(df_newly_added, pd.DataFrame) else 0

    layout_type = "Early" if source_month in ("2025-07", "2025-08") else "Modern"
    ongoing_table_title = (
        "Table 4: All Ongoing Projects"
        if layout_type == "Early"
        else "Table 6: All Ongoing Projects"
    )

    has_revised_cost = bool(
        "revised_cost_cr" in df_ongoing.columns and df_ongoing["revised_cost_cr"].notna().any()
    )
    has_revised_doc = bool(
        "revised_completion_date" in df_ongoing.columns
        and df_ongoing["revised_completion_date"].notna().any()
    )
    has_completed_table = completed_count > 0
    has_newly_added_table = newly_added_count > 0

    ongoing_orig_cost = (
        round(float(df_ongoing["original_cost_cr"].sum()), 2) if not df_ongoing.empty else 0.0
    )
    ongoing_cum_exp = (
        round(float(df_ongoing["cumulative_expenditure_cr"].sum()), 2)
        if not df_ongoing.empty
        else 0.0
    )

    t1_count = t1.get("table1_project_count")
    t1_orig_cost = t1.get("table1_orig_cost_cr")
    t1_cum_exp = t1.get("table1_cum_exp_cr")
    morth_count = t1.get("morth_ongoing_count", 0)

    summary_dict = {
        "report_month": source_month,
        "source_doc": pdf_path.name,
        "layout_type": layout_type,
        "ongoing_table_title": ongoing_table_title,
        "page_count": page_count,
        "morth_ongoing_count": morth_count,
        "table1_project_count": t1_count,
        "ongoing_row_count": ongoing_count,
        "count_match": (t1_count == ongoing_count) if t1_count is not None else False,
        "table1_orig_cost_cr": t1_orig_cost,
        "ongoing_orig_cost_cr": ongoing_orig_cost,
        "table1_cum_exp_cr": t1_cum_exp,
        "ongoing_cum_exp_cr": ongoing_cum_exp,
        "has_revised_cost": has_revised_cost,
        "has_revised_doc": has_revised_doc,
        "has_completed_table": has_completed_table,
        "completed_row_count": completed_count,
        "has_newly_added_table": has_newly_added_table,
        "newly_added_row_count": newly_added_count,
        "columns_found": ";".join(df_ongoing.columns.tolist()),
        "drop_note": "N/A",
    }

    return {
        "source_month": source_month,
        "output_paths": res["output_paths"],
        "summary_dict": summary_dict,
    }


def run(config: dict | None = None) -> dict[str, Any]:
    """Execute ingestion pipeline stage.

    Config options:
      - all_months (bool): if True, process all 13 reports. Default True if no pdf_path is specified.
      - pdf_path (Path | str): specific report to process (backwards compatibility).
      - source_month (str): specific month string (e.g. '2026-04').
    """
    config = config or {}
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    summary_path = DATA_INTERIM / "ingestion_summary.csv"

    # Single-file mode
    if "pdf_path" in config:
        source_month = config.get("source_month", "2026-04")
        pdf_path = Path(config["pdf_path"])
        task_res = process_report_task(source_month, pdf_path)
        new_row = task_res.get("summary_dict", {})
        if new_row:
            if summary_path.exists():
                existing_df = pd.read_csv(summary_path)
                if source_month in existing_df["report_month"].astype(str).values:
                    # Update row in place
                    for col, val in new_row.items():
                        if col in existing_df.columns:
                            existing_df.loc[
                                existing_df["report_month"].astype(str) == source_month, col
                            ] = val
                    summary_df = existing_df
                else:
                    summary_df = pd.concat(
                        [existing_df, pd.DataFrame([new_row])], ignore_index=True
                    )
            else:
                summary_df = pd.DataFrame([new_row])
            summary_df.to_csv(summary_path, index=False)
            log.info(
                "Updated ingestion summary at %s (single month: %s)", summary_path, source_month
            )
        return task_res.get("output_paths", {})

    # All 13 months mode
    reports_to_process = [(m, REPORTS / fname) for m, fname in MONTHLY_REPORTS]
    max_workers = min(len(reports_to_process), max(1, (os.cpu_count() or 2)))
    task_results = {}

    log.info(
        "Processing %d monthly reports using %d worker processes",
        len(reports_to_process),
        max_workers,
    )
    if max_workers > 1:
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_month = {
                executor.submit(process_report_task, m, p): m for m, p in reports_to_process
            }
            for future in concurrent.futures.as_completed(future_to_month):
                m = future_to_month[future]
                try:
                    res = future.result()
                    if res and "source_month" in res:
                        task_results[res["source_month"]] = res
                except Exception as e:
                    log.error("Failed processing month %s: %s", m, e)
    else:
        for m, p in reports_to_process:
            res = process_report_task(m, p)
            if res and "source_month" in res:
                task_results[res["source_month"]] = res

    # Build summary rows in canonical chronological order
    summary_rows = []
    all_output_paths = {}
    prev_ongoing_count = None

    for source_month, _ in reports_to_process:
        if source_month not in task_results:
            continue
        res = task_results[source_month]
        all_output_paths[source_month] = res["output_paths"]
        row = res["summary_dict"]

        ongoing_count = row["ongoing_row_count"]
        completed_count = row["completed_row_count"]
        newly_added_count = row["newly_added_row_count"]

        # Compute drop notes
        drop_note = "N/A"
        if prev_ongoing_count is not None and ongoing_count < prev_ongoing_count:
            drop_diff = prev_ongoing_count - ongoing_count
            if source_month == "2025-09":
                drop_note = f"Drop of {drop_diff} projects; exactly {completed_count} projects completed (Table 3)."
            elif source_month == "2026-03":
                drop_note = f"Drop of {drop_diff} projects; {completed_count} completed vs {newly_added_count} newly added."
            elif source_month == "2026-06":
                drop_note = f"Drop of {drop_diff} projects; massive {completed_count} projects completed (Table 3, incl 127 MoRTH) vs {newly_added_count} newly added."
            elif source_month == "2026-07":
                drop_note = f"Drop of {drop_diff} projects; {completed_count} completed vs {newly_added_count} newly added alongside reconciliation."
            else:
                drop_note = f"Drop of {drop_diff} projects; {completed_count} completed vs {newly_added_count} newly added."

        row["drop_note"] = drop_note
        prev_ongoing_count = ongoing_count
        summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(summary_path, index=False)
    log.info("Saved ingestion summary to %s (%d months)", summary_path, len(summary_df))

    return {
        "summary_csv": summary_path,
        "outputs": all_output_paths,
    }


if __name__ == "__main__":
    run()

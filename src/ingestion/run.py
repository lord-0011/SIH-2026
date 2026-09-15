"""Stage: ingestion — parse Flash Report PDFs into raw tables in data/interim/.

Preserves source month and source document name.
Splits paired visual cells into distinct columns.
Does NOT clean or validate; preserves raw strings and parsed values.
"""

from pathlib import Path

from src.common.config import DATA_INTERIM, REPORTS
from src.common.io import save_dataframe
from src.common.logging_setup import get_logger
from src.ingestion.parser import parse_flash_report

log = get_logger("ingestion")


def run(config: dict | None = None) -> dict[str, Path]:
    """Execute ingestion pipeline stage.

    Parses the configured or default Flash Report(s) and writes raw tables to data/interim/.
    """
    config = config or {}
    pdf_path = Path(config.get("pdf_path", REPORTS / "FlashReport_April2026.pdf"))
    source_month = config.get("source_month", "2026-04")

    log.info("Starting ingestion for %s (month: %s)", pdf_path.name, source_month)

    tables = parse_flash_report(pdf_path, source_month=source_month)

    clean_month = source_month.replace("-", "_")
    output_paths = {}

    for table_name, df in tables.items():
        if df.empty:
            log.warning("Table %s is empty for %s", table_name, source_month)
            continue
        out_file = DATA_INTERIM / f"raw_{table_name}_{clean_month}.parquet"
        save_dataframe(df, out_file)
        output_paths[table_name] = out_file
        log.info("Saved %s (%d rows) to %s", table_name, len(df), out_file)

    log.info("Ingestion complete for %s. Outputs: %s", source_month, output_paths)
    return output_paths


if __name__ == "__main__":
    run()

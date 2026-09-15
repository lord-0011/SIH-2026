"""Stage: labels — generates data/processed/labels.parquet from panel data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.common.io import load_dataframe, save_dataframe
from src.common.logging_setup import get_logger
from src.labels.generator import generate_labels

log = get_logger("labels.run")


def run(config: dict[str, Any] | None = None) -> Path:
    """Entry point for labels stage."""
    log.info("Starting labels stage...")

    panel_path = Path("data/processed/panel.parquet")
    if not panel_path.exists():
        raise FileNotFoundError(f"Panel data not found at {panel_path}")

    panel_df = load_dataframe(panel_path)
    labels_df = generate_labels(panel_df, horizon=3, slip_threshold=3)

    output_path = Path("data/processed/labels.parquet")
    save_dataframe(labels_df, output_path)
    log.info("Labels stage completed successfully. Output saved to %s", output_path)
    return output_path


if __name__ == "__main__":
    run()

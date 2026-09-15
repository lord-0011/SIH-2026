"""Stage: features — feature engineering runner.

Reads data/processed/panel.parquet, computes snapshot CUF and causal trajectory DERIVED features,
writes data/processed/features.parquet, and emits reports/feature_manifest.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.common.logging_setup import get_logger
from src.features.builder import (
    compute_feature_table,
    get_cuf_feature_names,
    get_derived_feature_names,
)

log = get_logger("features")


def run(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute the feature engineering pipeline stage."""
    panel_path = Path("data/processed/panel.parquet")
    if not panel_path.exists():
        raise FileNotFoundError(
            f"Required panel input {panel_path} does not exist. Run STEP_04 first."
        )

    log.info(f"Loading panel from {panel_path}...")
    panel_df = pd.read_parquet(panel_path)
    log.info(
        f"Loaded panel: {len(panel_df)} rows across {panel_df['project_id'].nunique()} projects."
    )

    features_df, manifest = compute_feature_table(panel_df)

    out_features_path = Path("data/processed/features.parquet")
    out_features_path.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_parquet(out_features_path, index=False)
    log.info(
        f"Saved feature table to {out_features_path} ({len(features_df)} rows, {len(features_df.columns)} columns)."
    )

    # Add summary stats to manifest
    null_rates = (features_df.isnull().sum() / len(features_df) * 100).round(2).to_dict()
    manifest["null_rates_pct"] = null_rates
    manifest["total_rows"] = len(features_df)

    manifest_path = Path("reports/feature_manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    log.info(f"Saved feature manifest to {manifest_path}.")

    cuf_cols = get_cuf_feature_names()
    derived_cols = get_derived_feature_names()

    print("\n=======================================================")
    print("STEP_06 FEATURE ENGINEERING: PIPELINE SUMMARY")
    print("=======================================================")
    print(f"Total rows in feature table: {len(features_df):,}")
    print(f"Total features engineered:   {len(cuf_cols) + len(derived_cols)} features")
    print(f"  - CUF Snapshot Features:   {len(cuf_cols)}")
    print(f"  - DERIVED Features:        {len(derived_cols)}")
    print(f"Feature table saved to:      {out_features_path}")
    print(f"Manifest saved to:           {manifest_path}")

    print("\nCUF FEATURES:")
    for col in cuf_cols:
        print(f"  [CUF]     {col:<35} null: {null_rates.get(col, 0.0):>5.2f}%")

    print("\nDERIVED FEATURES:")
    for col in derived_cols:
        print(f"  [DERIVED] {col:<35} null: {null_rates.get(col, 0.0):>5.2f}%")

    return {
        "features_path": str(out_features_path),
        "manifest_path": str(manifest_path),
        "row_count": len(features_df),
        "cuf_feature_count": len(cuf_cols),
        "derived_feature_count": len(derived_cols),
        "features_df": features_df,
        "manifest": manifest,
    }


if __name__ == "__main__":
    run()

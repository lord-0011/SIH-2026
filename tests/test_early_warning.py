"""Real-data integration tests for early warning trend detection (STEP_12).

Guarded with pytest.skip on clean CI runners lacking DVC assets.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.common.io import load_dataframe
from src.early_warning.detector import compute_early_warnings

EARLY_WARNING_PATH = Path("data/processed/early_warning.parquet")
RISK_SCORES_PATH = Path("data/processed/risk_scores.parquet")
FEATURES_PATH = Path("data/processed/features.parquet")


@pytest.fixture(scope="module")
def early_warning_df() -> pd.DataFrame:
    if not EARLY_WARNING_PATH.exists():
        pytest.skip(f"Early warning data not found at {EARLY_WARNING_PATH} (DVC-tracked)")
    return load_dataframe(EARLY_WARNING_PATH)


@pytest.fixture(scope="module")
def risk_scores_df() -> pd.DataFrame:
    if not RISK_SCORES_PATH.exists():
        pytest.skip(f"Risk scores not found at {RISK_SCORES_PATH} (DVC-tracked)")
    return load_dataframe(RISK_SCORES_PATH)


@pytest.fixture(scope="module")
def features_df() -> pd.DataFrame:
    if not FEATURES_PATH.exists():
        pytest.skip(f"Features not found at {FEATURES_PATH} (DVC-tracked)")
    return load_dataframe(FEATURES_PATH)


def test_early_warning_parquet_completeness(early_warning_df: pd.DataFrame):
    """Parquet must have exact 18,860 rows and zero nulls in all critical evidence columns."""
    assert len(early_warning_df) == 18860

    critical_cols = [
        "project_id",
        "report_month",
        "sector",
        "is_road",
        "data_sufficiency",
        "risk_score",
        "risk_band",
        "early_warning",
        "warning_status",
        "warning_strength",
        "triggers_fired",
        "score_rising_fired",
        "gap_widening_fired",
        "velocity_divergence_fired",
    ]
    for col in critical_cols:
        assert col in early_warning_df.columns, f"Missing column: {col}"
        assert early_warning_df[col].isnull().sum() == 0, f"Column {col} has nulls"


def test_steady_high_concrete_real_project(early_warning_df: pd.DataFrame):
    """Concrete real-world project 400145 in steady/declining HIGH band must NEVER fire score_rising."""
    p400145 = early_warning_df[early_warning_df["project_id"] == "400145"].sort_values(
        "report_month"
    )
    assert len(p400145) >= 3, "Project 400145 must have at least 3 months history"

    # In every observed month, its score was flat or falling (44.8, 44.8, 44.3, 42.4, 42.4, 43.6)
    # score_rising_2m must NEVER fire for project 400145
    assert not p400145[
        "score_rising_fired"
    ].any(), "Project 400145 unexpectedly fired score_rising_2m"


def test_real_data_causal_leakage_invariance(
    risk_scores_df: pd.DataFrame,
    features_df: pd.DataFrame,
    early_warning_df: pd.DataFrame,
):
    """INVARIANT: Truncating data at T=2026-02 produces identical warnings at T as the full dataset."""
    target_month = "2026-02"

    # Truncate inputs to <= 2026-02
    risk_trunc = risk_scores_df[risk_scores_df["report_month"] <= target_month].copy()
    feat_trunc = features_df[features_df["report_month"] <= target_month].copy()

    recomputed_trunc = compute_early_warnings(risk_trunc, feat_trunc)

    full_t = early_warning_df[early_warning_df["report_month"] == target_month].sort_values(
        "project_id"
    )
    trunc_t = recomputed_trunc[recomputed_trunc["report_month"] == target_month].sort_values(
        "project_id"
    )

    assert len(full_t) == len(trunc_t)
    assert (full_t["project_id"].values == trunc_t["project_id"].values).all()

    # Compare key evidence and status fields
    assert (full_t["early_warning"].values == trunc_t["early_warning"].values).all()
    assert (full_t["warning_status"].values == trunc_t["warning_status"].values).all()
    assert (full_t["warning_strength"].values == trunc_t["warning_strength"].values).all()
    assert (full_t["triggers_fired"].values == trunc_t["triggers_fired"].values).all()
    assert (full_t["score_rising_fired"].values == trunc_t["score_rising_fired"].values).all()
    assert (full_t["gap_widening_fired"].values == trunc_t["gap_widening_fired"].values).all()
    assert (
        full_t["velocity_divergence_fired"].values == trunc_t["velocity_divergence_fired"].values
    ).all()


def test_latest_month_sector_separation(early_warning_df: pd.DataFrame):
    """Latest month (2026-07) must separate Non-Roads validation regime from Roads transfer regime."""
    latest = early_warning_df[early_warning_df["report_month"] == "2026-07"]
    assert len(latest) == 1800

    nr = latest[~latest["is_road"]]
    roads = latest[latest["is_road"]]

    assert len(nr) == 787
    assert len(roads) == 1013

    # Both subsets must have active warnings and valid strength counts
    assert nr["early_warning"].sum() > 0
    assert roads["early_warning"].sum() > 0

    # Ensure every active warning carries non-empty triggers_fired
    active_nr = nr[nr["early_warning"]]
    assert (active_nr["triggers_fired"] != "none").all()
    assert (active_nr["warning_strength"] >= 1).all()

"""Tests for label generation and active-target filtering."""

from pathlib import Path

import pandas as pd
import pytest

from src.common.io import load_dataframe


@pytest.fixture(scope="module")
def labels_df() -> pd.DataFrame:
    path = Path("data/processed/labels.parquet")
    assert path.exists(), "labels.parquet must exist"
    return load_dataframe(path)


def test_labels_total_rows(labels_df: pd.DataFrame):
    """Total label rows must match panel rows exactly (18,860)."""
    assert len(labels_df) == 18860


def test_temporal_split_monotonicity(labels_df: pd.DataFrame):
    """Split categories must strictly match report_month definitions."""
    train_months = labels_df[labels_df["split"] == "train"]["report_month"].unique()
    val_months = labels_df[labels_df["split"] == "val"]["report_month"].unique()
    test_months = labels_df[labels_df["split"] == "test"]["report_month"].unique()

    # Every row assigned to train, val, test must strictly match its calendar window
    assert set(train_months).issubset(
        {"2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12"}
    )
    assert set(val_months).issubset({"2026-01", "2026-02"})
    assert set(test_months).issubset({"2026-03", "2026-04"})

    # All rows in terminal months (2026-05, 2026-06, 2026-07) MUST be censored (horizon < 3)
    terminal_splits = labels_df[labels_df["report_month"] >= "2026-05"]["split"].unique()
    assert set(terminal_splits) == {"censored"}


def test_active_target_filter_invariant(labels_df: pd.DataFrame):
    """No row in filtered usable set may have an already-expired revised date at T."""
    filtered = labels_df[labels_df["is_usable_filtered"]]
    assert not filtered["is_target_expired"].any()


def test_clean_transition_excludes_first_population(labels_df: pd.DataFrame):
    """First-population artifacts (null -> date) must not be counted as clean existing moves."""
    first_pop_slips = labels_df[labels_df["is_first_pop"] & (labels_df["slip_amount_months"] >= 3)]
    # In labels generator, is_clean_pos_raw requires is_exist_move
    assert not first_pop_slips["is_clean_pos_raw"].any()


def test_usable_filtered_counts(labels_df: pd.DataFrame):
    """Filtered usable rows must be 10,947 with 1,871 clean positives."""
    filtered = labels_df[labels_df["is_usable_filtered"]]
    assert len(filtered) == 10947
    assert (filtered["target_slip_3m_ge3m"] == 1).sum() == 1871

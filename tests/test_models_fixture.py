"""CI fixture tests for modeling pipeline (non-skipping, runs on synthetic data).

Validates end-to-end training, validation tuning, test evaluation, near-label ablation,
and secondary transfer on synthetic data without requiring DVC assets.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.models.trainer import prepare_datasets, train_and_evaluate_all


@pytest.fixture
def synthetic_features_and_labels() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create a minimal synthetic features and labels dataset spanning train, val, and test months."""
    np.random.seed(42)
    months = [
        "2025-07",
        "2025-08",
        "2025-09",
        "2025-10",
        "2025-11",
        "2025-12",
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
    ]
    projects = [
        ("P_NR_1", "Railways", False),
        ("P_NR_2", "Power", False),
        ("P_NR_3", "Coal", False),
        ("P_NR_4", "Petroleum", False),
        ("P_RD_1", "Roads & Highways", True),
        ("P_RD_2", "Roads & Highways", True),
    ]

    feat_rows = []
    label_rows = []

    for pid, sec, is_rd in projects:
        for m in months:
            # Features
            feat_rows.append(
                {
                    "project_id": pid,
                    "report_month": m,
                    "cost_escalation_amt": float(np.random.uniform(0, 500)),
                    "cost_escalation_pct": float(np.random.uniform(0, 50)),
                    "exp_utilization": float(np.random.uniform(0.1, 0.9)),
                    "planned_duration_months": 36.0,
                    "elapsed_duration_months": float(np.random.uniform(6, 30)),
                    "remaining_duration_months": float(np.random.uniform(6, 30)),
                    "schedule_variance_months": float(np.random.uniform(0, 12)),
                    "delay_to_date_months": float(np.random.uniform(0, 6)),
                    "financial_physical_gap": float(np.random.uniform(-10, 20)),
                    "state_count": 1,
                    "project_size_band": "Mega",
                    "ministry": "Ministry of Infrastructure",
                    "sector": sec,
                    "sector_hist_event_rate": 0.15 if not is_rd else 0.40,
                    "cost_growth_rate_3mo": float(np.random.uniform(0, 10)),
                    "monthly_exp_change": float(np.random.uniform(5, 50)),
                    "exp_velocity_3mo": float(np.random.uniform(10, 80)),
                    "exp_acceleration_3mo": float(np.random.uniform(-5, 5)),
                    "monthly_progress_change": float(np.random.uniform(0.5, 5.0)),
                    "progress_velocity_3mo": float(np.random.uniform(2, 10)),
                    "progress_acceleration_3mo": float(np.random.uniform(-1, 1)),
                    "progress_stagnation": False,
                    "gap_change_3mo": float(np.random.uniform(-2, 5)),
                    "recent_deterioration": False,
                    "first_revised_date_entered_in_trailing_3mo": False,
                }
            )

            # Labels
            if m <= "2025-12":
                split = "train"
            elif m <= "2026-02":
                split = "val"
            else:
                split = "test"

            # Synthetic target
            target = int(np.random.binomial(1, 0.2 if not is_rd else 0.4))

            label_rows.append(
                {
                    "project_id": pid,
                    "report_month": m,
                    "sector": sec,
                    "is_road": is_rd,
                    "target_slip_3m_ge3m": target,
                    "is_clean_pos_raw": bool(target == 1),
                    "is_first_pop": False,
                    "is_target_expired": False,
                    "is_usable_unfiltered": True,
                    "is_usable_filtered": True,
                    "slip_amount_months": 4.0 if target == 1 else 0.0,
                    "split": split,
                }
            )

    features_df = pd.DataFrame(feat_rows)
    labels_df = pd.DataFrame(label_rows)
    return features_df, labels_df


def test_prepare_datasets_temporal_split_integrity(synthetic_features_and_labels):
    """Verify that train, val, and test matrices respect strict temporal ordering."""
    features_df, labels_df = synthetic_features_and_labels
    data = prepare_datasets(features_df, labels_df, apply_active_target_filter=True)

    # Train months must strictly be <= 2025-12
    train_months = data["nr_train_df"]["report_month"].unique()
    assert all(m <= "2025-12" for m in train_months)

    # Val months must strictly be in 2026-01..2026-02
    val_months = data["nr_val_df"]["report_month"].unique()
    assert all("2026-01" <= m <= "2026-02" for m in val_months)

    # Test months must strictly be in 2026-03..2026-04
    test_months = data["nr_test_df"]["report_month"].unique()
    assert all("2026-03" <= m <= "2026-04" for m in test_months)

    # Roads test must strictly contain road projects in test window
    roads_test_months = data["roads_test_df"]["report_month"].unique()
    assert all("2026-03" <= m <= "2026-04" for m in roads_test_months)
    assert data["roads_test_df"]["is_road"].all()


def test_models_pipeline_synthetic_end_to_end(synthetic_features_and_labels):
    """Verify that the full modeling pipeline runs end-to-end on synthetic data and outputs valid metrics."""
    features_df, labels_df = synthetic_features_and_labels
    output = train_and_evaluate_all(features_df, labels_df)

    results = output["results"]
    models = output["models"]

    # Check headline results
    headline = results["headline_nonroads_test"]
    assert len(headline) == 4

    for m_res in headline:
        assert m_res["pr_auc"] is not None
        assert 0.0 <= m_res["pr_auc"] <= 1.0
        assert 0.0 <= m_res["roc_auc"] <= 1.0
        assert 0.0 <= m_res["brier_score"] <= 1.0
        assert 0.0 <= m_res["ece"] <= 1.0
        assert 0.0 <= m_res["precision_at_10pct"] <= 1.0

    # Check models dict
    assert "model_baseline" in models
    assert "model_logistic_cuf" in models
    assert "model_lightgbm_cuf" in models
    assert "model_lightgbm_full" in models
    assert "model_lightgbm_ablation" in models

    # Check near-label ablation structure
    abl = results["near_label_ablation"]
    assert "with_near_label" in abl
    assert "without_near_label" in abl
    assert "dropped_features" in abl
    assert abl["dropped_features"] == ["schedule_variance_months", "delay_to_date_months"]

    # Check secondary roads transfer structure
    roads = results["roads_transfer_analysis"]
    assert "caveat" in roads
    assert len(roads["test_metrics"]) == 4

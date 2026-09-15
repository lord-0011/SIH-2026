"""Tests for models training, evaluation metrics, temporal split integrity, and near-label ablation."""

import json
from pathlib import Path

import joblib
import pytest

RESULTS_PATH = Path("data/processed/models/evaluation_results.json")
MODELS_DIR = Path("data/processed/models")


@pytest.fixture(scope="module")
def eval_results() -> dict:
    if not RESULTS_PATH.exists():
        pytest.skip(f"Evaluation results not found at {RESULTS_PATH} (DVC-tracked)")
    with open(RESULTS_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_models_artifacts_exist():
    """All 4 model checkpoints and scalers must be saved on disk."""
    if not RESULTS_PATH.exists():
        pytest.skip(f"Model checkpoints not found at {MODELS_DIR} (DVC-tracked)")
    expected_files = [
        "model_baseline.joblib",
        "scaler_baseline.joblib",
        "model_logistic_cuf.joblib",
        "scaler_cuf.joblib",
        "model_lightgbm_cuf.joblib",
        "model_lightgbm_full.joblib",
        "model_lightgbm_ablation.joblib",
        "evaluation_results.json",
    ]
    for fname in expected_files:
        p = MODELS_DIR / fname
        assert p.exists(), f"Expected artifact missing: {p}"
        if p.suffix == ".joblib":
            obj = joblib.load(p)
            assert obj is not None


def test_headline_benchmark_results(eval_results: dict):
    """Headline Non-Roads test set results must answer both problem statement questions positively."""
    headline = eval_results["headline_nonroads_test"]
    assert len(headline) == 4

    m1 = headline[0]  # Baseline
    m2 = headline[1]  # Logistic CUF
    m3 = headline[2]  # LightGBM CUF
    m4 = headline[3]  # LightGBM Full

    # Confirm test sample size and positive count
    assert m1["total_samples"] == 1373
    assert m1["positive_count"] == 116

    # Q1: Does CUF alone predict? (Logistic CUF PR-AUC > Baseline PR-AUC)
    assert m2["pr_auc"] > m1["pr_auc"]
    assert m2["pr_auc"] >= 0.28

    # Q2: Does ML beat statistical baseline? (LightGBM PR-AUC > Baseline and Logistic)
    assert m3["pr_auc"] > m2["pr_auc"]
    assert m3["pr_auc"] >= 0.40
    assert m4["pr_auc"] >= 0.40


def test_near_label_ablation_integrity(eval_results: dict):
    """Model must not collapse when near-label features are removed."""
    abl = eval_results["near_label_ablation"]
    w_pr = abl["with_near_label"]["pr_auc"]
    wo_pr = abl["without_near_label"]["pr_auc"]

    # PR-AUC without near-label features must remain high (> 0.40)
    assert wo_pr >= 0.40
    # Difference should be modest or positive, proving it's not a mere currently-late detector
    assert wo_pr >= w_pr - 0.05


def test_roads_transfer_metrics_caveat(eval_results: dict):
    """Roads transfer analysis must carry the explicit onboarding caveat."""
    roads_res = eval_results["roads_transfer_analysis"]
    assert "caveat" in roads_res
    assert "transfer test of the Non-Roads-trained model" in roads_res["caveat"]
    assert len(roads_res["test_metrics"]) == 4
    for m in roads_res["test_metrics"]:
        assert m["total_samples"] == 1901
        assert m["positive_count"] == 827

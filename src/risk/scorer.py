"""Risk scoring and probability calibration engine for the PAIMANA Platform.

Transforms raw model estimates into calibrated probabilities and 0-100 Project Risk Scores,
derives quantile risk bands (LOW/MED/HIGH/CRITICAL), and attaches data sufficiency flags.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from src.common.logging_setup import get_logger
from src.models.metrics import compute_ece
from src.models.trainer import _clean_column_names, prepare_datasets

log = get_logger("risk.scorer")

# Fixed production band cutoffs derived from Validation distribution (percentiles 50, 80, 92)
BAND_CUTOFFS = {
    "low_med": 4.6,
    "med_high": 36.1,
    "high_crit": 55.9,
}


def fit_platt_calibrator(
    raw_probs_val: np.ndarray,
    y_val: np.ndarray,
    random_state: int = 42,
) -> LogisticRegression:
    """Fit a Platt scaling (logistic sigmoid) calibrator strictly on the validation fold."""
    log.info("Fitting Platt calibrator on %d validation samples...", len(y_val))
    calibrator = LogisticRegression(C=1.0, solver="lbfgs", random_state=random_state)
    calibrator.fit(raw_probs_val.reshape(-1, 1), y_val)
    return calibrator


def calibrate_probabilities(
    calibrator: LogisticRegression,
    raw_probs: np.ndarray,
) -> np.ndarray:
    """Transform raw model probabilities into calibrated probabilities using fitted Platt scaler."""
    return calibrator.predict_proba(raw_probs.reshape(-1, 1))[:, 1]


def compute_risk_score(calibrated_probs: np.ndarray) -> np.ndarray:
    """Map calibrated probability [0, 1] monotonically to a 0-100 risk score."""
    return np.round(np.clip(calibrated_probs * 100.0, 0.0, 100.0), 1)


def assign_risk_band(score: float, cutoffs: dict[str, float] | None = None) -> str:
    """Assign LOW, MEDIUM, HIGH, or CRITICAL band based on score cutoffs."""
    c = cutoffs or BAND_CUTOFFS
    if score < c["low_med"]:
        return "LOW"
    elif score < c["med_high"]:
        return "MEDIUM"
    elif score < c["high_crit"]:
        return "HIGH"
    else:
        return "CRITICAL"


def compute_data_sufficiency(panel_df: pd.DataFrame) -> pd.DataFrame:
    """Compute observation history depth and data sufficiency indicator (NFR-4).

    Rules:
      - observed_months_to_date: cumulative distinct reporting months observed for the project up to T.
      - data_sufficiency:
          'PROVISIONAL' if observed_months_to_date <= 2 (trajectory history too thin for reliable momentum).
          'SUFFICIENT' if observed_months_to_date >= 3 (standard reliable trajectory depth).
    """
    sorted_df = panel_df.sort_values(["project_id", "report_month"])
    obs_count = sorted_df.groupby("project_id").cumcount() + 1
    sufficiency = np.where(obs_count <= 2, "PROVISIONAL", "SUFFICIENT")

    return pd.DataFrame(
        {
            "project_id": sorted_df["project_id"].values,
            "report_month": sorted_df["report_month"].values,
            "observed_months_to_date": obs_count.values,
            "data_sufficiency": sufficiency,
        }
    )


def generate_risk_scores(
    features_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    panel_df: pd.DataFrame,
    model: Any,
    cutoffs: dict[str, float] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Execute end-to-end probability calibration, risk scoring, and sanity-checking.

    Outputs:
      - risk_scores_df: DataFrame with 18,860 rows containing raw/calibrated probs, scores, bands, sufficiency.
      - summary: Dictionary containing calibration diagnostics and per-band realized rates.
    """
    log.info("Preparing validation and test datasets for calibration...")
    data = prepare_datasets(features_df, labels_df, apply_active_target_filter=True)

    X_val = data["X_val_no_near"]
    y_val = data["y_val"]
    X_test = data["X_test_no_near"]
    y_test = data["y_test"]

    # 1. Raw predictions on Val and Test
    raw_p_val = model.predict_proba(X_val)[:, 1]
    raw_p_test = model.predict_proba(X_test)[:, 1]

    ece_raw_test = compute_ece(y_test, raw_p_test)

    # 2. Fit Platt calibrator on Val
    calibrator = fit_platt_calibrator(raw_p_val, y_val)
    cal_p_test = calibrate_probabilities(calibrator, raw_p_test)
    ece_cal_test = compute_ece(y_test, cal_p_test)

    # 3. Determine or verify cutoffs
    active_cutoffs = cutoffs or BAND_CUTOFFS

    # 4. Score the entire features DataFrame (all 18,860 rows across all sectors and months)
    cuf_numeric = [
        "cost_escalation_amt",
        "cost_escalation_pct",
        "exp_utilization",
        "planned_duration_months",
        "elapsed_duration_months",
        "remaining_duration_months",
        "financial_physical_gap",
        "state_count",
    ]
    derived_numeric = [
        "sector_hist_event_rate",
        "cost_growth_rate_3mo",
        "monthly_exp_change",
        "exp_velocity_3mo",
        "exp_acceleration_3mo",
        "monthly_progress_change",
        "progress_velocity_3mo",
        "progress_acceleration_3mo",
        "progress_stagnation",
        "gap_change_3mo",
        "recent_deterioration",
        "first_revised_date_entered_in_trailing_3mo",
    ]
    cat_cols = ["project_size_band", "sector"]

    train_cols = data["X_train_no_near"].columns.tolist()
    all_cats = _clean_column_names(pd.get_dummies(features_df[cat_cols], drop_first=True))
    all_X = _clean_column_names(
        pd.concat([features_df[cuf_numeric + derived_numeric].fillna(0), all_cats], axis=1)
    )
    all_X = all_X.reindex(columns=train_cols, fill_value=0)

    raw_p_all = model.predict_proba(all_X)[:, 1]
    cal_p_all = calibrate_probabilities(calibrator, raw_p_all)
    scores_all = compute_risk_score(cal_p_all)
    bands_all = [assign_risk_band(s, active_cutoffs) for s in scores_all]

    # Data sufficiency
    suff_df = compute_data_sufficiency(panel_df)

    risk_df = pd.DataFrame(
        {
            "project_id": features_df["project_id"].values,
            "report_month": features_df["report_month"].values,
            "sector": features_df["sector"].values,
            "raw_probability": np.round(raw_p_all, 4),
            "calibrated_probability": np.round(cal_p_all, 4),
            "risk_score": scores_all,
            "risk_band": bands_all,
        }
    )

    risk_df = risk_df.merge(suff_df, on=["project_id", "report_month"], how="left")

    # Merge label metadata
    label_cols = [
        "project_id",
        "report_month",
        "target_slip_3m_ge3m",
        "is_usable_filtered",
        "split",
    ]
    risk_df = risk_df.merge(labels_df[label_cols], on=["project_id", "report_month"], how="left")

    # 5. Sanity check per-band realized rates on held-out Non-Roads test set
    test_scores = compute_risk_score(cal_p_test)
    test_bands = [assign_risk_band(s, active_cutoffs) for s in test_scores]
    test_eval_df = pd.DataFrame(
        {
            "score": test_scores,
            "band": test_bands,
            "realized_slip": y_test,
        }
    )

    band_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    band_metrics = {}
    prev_rate = -1.0
    is_strictly_increasing = True

    for b in band_order:
        b_df = test_eval_df[test_eval_df["band"] == b]
        cnt = len(b_df)
        pos = int(b_df["realized_slip"].sum()) if cnt > 0 else 0
        rate = float(np.round((pos / cnt) * 100.0, 2)) if cnt > 0 else 0.0
        min_s = float(b_df["score"].min()) if cnt > 0 else 0.0
        max_s = float(b_df["score"].max()) if cnt > 0 else 0.0

        if rate <= prev_rate:
            is_strictly_increasing = False
        prev_rate = rate

        band_metrics[b] = {
            "count": cnt,
            "realized_positives": pos,
            "realized_event_rate_pct": rate,
            "min_score": min_s,
            "max_score": max_s,
        }

    summary = {
        "production_model": "LightGBM (Ablated: No Near-Label Features)",
        "calibration_method": "Platt Scaling (Logistic Sigmoid on Validation Block)",
        "calibration_metrics": {
            "test_ece_before": round(ece_raw_test, 4),
            "test_ece_after": round(ece_cal_test, 4),
            "ece_reduction_pct": round((1.0 - ece_cal_test / ece_raw_test) * 100.0, 1),
        },
        "score_mapping": "Score = round(100 * calibrated_probability, 1)",
        "band_cutoffs": active_cutoffs,
        "nonroads_test_band_validation": {
            "sample_size": len(y_test),
            "clean_positives": int(np.sum(y_test)),
            "base_rate_pct": round(float(np.mean(y_test) * 100.0), 2),
            "is_strictly_monotonic_increasing": is_strictly_increasing,
            "bands": band_metrics,
        },
        "data_sufficiency_rules": {
            "provisional_threshold": "<= 2 observed months",
            "sufficient_threshold": ">= 3 observed months",
        },
    }

    log.info(
        "Risk scoring completed. Non-Roads Test ECE: %.4f -> %.4f. Monotonicity satisfied: %s",
        ece_raw_test,
        ece_cal_test,
        is_strictly_increasing,
    )

    return risk_df, summary

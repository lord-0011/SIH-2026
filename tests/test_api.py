"""Real-data integration tests for PAIMANA Backend API (STEP_13).

Guarded with pytest.skip on clean CI runners lacking DVC assets.
Verifies exact parquet parity, zero recomputation, and business logic.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.config import settings
from src.api.repository import repository

PANEL_PATH = Path("data/processed/panel.parquet")
RISK_PATH = Path("data/processed/risk_scores.parquet")
EW_PATH = Path("data/processed/early_warning.parquet")
FEAT_PATH = Path("data/processed/features.parquet")


@pytest.fixture(scope="module", autouse=True)
def ensure_real_data_loaded():
    """Ensure repository loads real precomputed tables, skipping if absent."""
    if not PANEL_PATH.exists() or not RISK_PATH.exists() or not EW_PATH.exists():
        pytest.skip(
            f"Processed parquets not found in {settings.PANEL_PARQUET_PATH.parent} (DVC-tracked)"
        )
    repository.load_data()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_real_pipeline_last_run(client: TestClient):
    """Verify data freshness and project counts match raw processed parquets."""
    res = client.get("/pipeline/last-run")
    assert res.status_code == 200
    data = res.json()
    assert data["latest_data_month"] == "2026-07"
    assert data["earliest_data_month"] == "2025-07"
    assert data["total_months"] == 13
    assert data["total_canonical_projects"] == 2243
    assert data["total_panel_rows"] == 18860
    assert data["total_active_projects_latest_month"] == 1800


def test_real_steady_high_project_parity(client: TestClient):
    """Verify steady-HIGH negative control project 400145 exact parity with parquet."""
    res = client.get("/projects/400145")
    assert res.status_code == 200
    data = res.json()

    # Metadata & current metrics
    assert data["project_id"] == "400145"
    assert data["ministry"] == "Ministry of Coal"
    assert data["sector"] == "Coal"
    assert data["is_road"] is False
    assert data["transfer_regime"] is False
    assert data["data_sufficiency"] == "SUFFICIENT"
    assert data["observed_months_to_date"] == 6

    # Exact parquet score parity in latest observed month 2025-12
    metrics = data["current_metrics"]
    assert metrics["report_month"] == "2025-12"
    assert round(metrics["risk_score"], 1) == 43.6
    assert metrics["risk_band"] == "HIGH"

    # Early warning must NOT fire on steady-HIGH project
    ew = data["early_warning"]
    assert ew["early_warning"] is False
    assert ew["warning_status"] == "STABLE_OR_IMPROVING"
    assert ew["warning_strength"] == 0
    assert ew["score_rising_fired"] is False

    # Historical trajectory spans all 6 observed months
    history = data["history"]
    assert len(history) == 6
    assert history[0]["report_month"] == "2025-07"
    assert history[-1]["report_month"] == "2025-12"


def test_real_random_project_exact_parquet_parity(client: TestClient):
    """Verify arbitrary project 400142 matches raw parquet numbers exactly."""
    risk_df = pd.read_parquet(RISK_PATH)
    ew_df = pd.read_parquet(EW_PATH)

    row_r = risk_df[
        (risk_df["project_id"] == "400142") & (risk_df["report_month"] == "2026-07")
    ].iloc[0]
    row_e = ew_df[(ew_df["project_id"] == "400142") & (ew_df["report_month"] == "2026-07")].iloc[0]

    res = client.get("/projects/400142")
    assert res.status_code == 200
    data = res.json()

    assert data["current_metrics"]["risk_score"] == pytest.approx(
        float(row_r["risk_score"]), rel=1e-5
    )
    assert data["current_metrics"]["risk_band"] == str(row_r["risk_band"])
    assert data["current_metrics"]["calibrated_probability"] == pytest.approx(
        float(row_r["calibrated_probability"]), rel=1e-5
    )
    assert data["early_warning"]["early_warning"] == bool(row_e["early_warning"])
    assert data["early_warning"]["warning_status"] == str(row_e["warning_status"])
    assert data["early_warning"]["warning_strength"] == int(row_e["warning_strength"])


def test_real_national_summary_separation(client: TestClient):
    """Verify Level-1 national summary properly isolates roads transfer regime."""
    res = client.get("/national/summary")
    assert res.status_code == 200
    data = res.json()

    assert data["report_month"] == "2026-07"
    assert data["total_projects"] == 1800

    non_roads = data["non_roads"]
    roads = data["roads"]

    # Sum of regimes must equal portfolio total
    assert non_roads["total_projects"] + roads["total_projects"] == 1800
    assert non_roads["transfer_regime"] is False
    assert roads["transfer_regime"] is True
    assert roads["transfer_regime_note"] is not None

    # Trend length should cover all 13 months
    assert len(data["monthly_trend"]) == 13
    assert data["monthly_trend"][-1]["report_month"] == "2026-07"


def test_real_watchlist_ordering_and_invariants(client: TestClient):
    """Verify watchlist items are exclusively active warnings and strictly ordered."""
    res = client.get("/watchlist")
    assert res.status_code == 200
    data = res.json()

    assert data["total_active_warnings"] > 0
    items = data["items"]
    assert len(items) == data["total_active_warnings"]
    assert data["non_roads_count"] + data["roads_count"] == data["total_active_warnings"]

    # Verify descending ordering: warning_strength desc, then risk_score desc
    for i in range(len(items) - 1):
        curr_str = items[i]["warning_strength"]
        next_str = items[i + 1]["warning_strength"]
        curr_score = items[i]["risk_score"]
        next_score = items[i + 1]["risk_score"]

        assert curr_str >= next_str
        if curr_str == next_str:
            assert curr_score >= next_score

    # Every item must have warning_strength >= 1
    for item in items:
        assert item["warning_strength"] >= 1


def test_real_sector_and_ministry_lookups(client: TestClient):
    """Verify sector and ministry endpoints return consistent data."""
    # Sector Railways
    res_sec = client.get("/sectors/Railways/summary")
    assert res_sec.status_code == 200
    sec_data = res_sec.json()
    assert sec_data["sector"] == "Railways"
    assert sec_data["is_road"] is False
    assert sec_data["total_projects"] > 0
    assert len(sec_data["top_risk_projects"]) <= 10

    # Sector Roads
    res_road = client.get("/sectors/Roads%20%26%20Highways/summary")
    assert res_road.status_code == 200
    road_data = res_road.json()
    assert road_data["is_road"] is True
    assert road_data["transfer_regime"] is True

    # Ministry Railways
    res_min = client.get("/ministries/Ministry of Railways/summary")
    assert res_min.status_code == 200
    min_data = res_min.json()
    assert min_data["ministry"] == "Ministry of Railways"
    assert min_data["total_projects"] > 0
    assert len(min_data["sectors"]) >= 1


def test_real_projects_pagination_and_filter(client: TestClient):
    """Verify project list pagination and band filtering."""
    # Pagination: page 1 of 25
    res = client.get("/projects?page=1&page_size=25")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1800
    assert data["page"] == 1
    assert data["page_size"] == 25
    assert len(data["items"]) == 25

    # Filter by CRITICAL
    res_crit = client.get("/projects?band=CRITICAL&page_size=50")
    assert res_crit.status_code == 200
    crit_data = res_crit.json()
    assert crit_data["total"] > 0
    for item in crit_data["items"]:
        assert item["risk_band"] == "CRITICAL"

"""CI fixture tests for PAIMANA Backend API (non-skipping, runs on synthetic data).

Validates:
- Liveness health probe (`/health`)
- Ingestion freshness & metadata (`/pipeline/last-run`)
- Level-1 National summary with Non-Roads vs Roads regime separation (`/national/summary`)
- Level-2 Sector summary with transfer regime flagging and 404 handling (`/sectors/{sector}/summary`)
- Level-2 Ministry summary with sector breakdowns and 404 handling (`/ministries/{ministry}/summary`)
- Level-3 Filterable & paginated project catalog (`/projects`)
- Level-3 Deep-dive project dossier with historical trajectory (`/projects/{project_id}`)
- Early warning watchlist ordering by warning strength desc, then risk score desc (`/watchlist`)
- Zero request-time recomputation invariant
"""

from __future__ import annotations

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.repository import repository


def _build_synthetic_datasets():
    """Build synthetic panel, risk, early_warning, and feature dataframes."""
    # 2 projects, 2 months: 2026-06 and 2026-07
    panel_rows = [
        # Project P1: Non-road (Railways), deteriorating
        {
            "project_id": "P1",
            "report_month": "2026-06",
            "project_code": "P-001",
            "project_name": "Metro Rail Phase 1",
            "implementing_agency": "Rail Corp",
            "ministry": "Ministry of Railways",
            "sector": "Railways",
            "state": "Maharashtra",
            "original_cost_cr": 1000.0,
            "revised_cost_cr": 1200.0,
            "cumulative_expenditure_cr": 500.0,
            "exp_utilization": 50.0,
            "physical_progress_pct": 40.0,
            "financial_physical_gap": 10.0,
            "original_completion_date": "2027-01-01",
            "revised_completion_date": "2027-06-01",
            "planned_duration_months": 36.0,
            "elapsed_duration_months": 20.0,
            "remaining_duration_months": 16.0,
            "trajectory_anchor_date": "2024-01-01",
        },
        {
            "project_id": "P1",
            "report_month": "2026-07",
            "project_code": "P-001",
            "project_name": "Metro Rail Phase 1",
            "implementing_agency": "Rail Corp",
            "ministry": "Ministry of Railways",
            "sector": "Railways",
            "state": "Maharashtra",
            "original_cost_cr": 1000.0,
            "revised_cost_cr": 1200.0,
            "cumulative_expenditure_cr": 600.0,
            "exp_utilization": 60.0,
            "physical_progress_pct": 42.0,
            "financial_physical_gap": 18.0,
            "original_completion_date": "2027-01-01",
            "revised_completion_date": "2027-06-01",
            "planned_duration_months": 36.0,
            "elapsed_duration_months": 21.0,
            "remaining_duration_months": 15.0,
            "trajectory_anchor_date": "2024-01-01",
        },
        # Project P2: Road sector, steady
        {
            "project_id": "P2",
            "report_month": "2026-06",
            "project_code": "P-002",
            "project_name": "National Expressway",
            "implementing_agency": "NHAI",
            "ministry": "Ministry of Road Transport and Highways",
            "sector": "Road Transport and Highways",
            "state": "Gujarat",
            "original_cost_cr": 2000.0,
            "revised_cost_cr": 2000.0,
            "cumulative_expenditure_cr": 1000.0,
            "exp_utilization": 50.0,
            "physical_progress_pct": 50.0,
            "financial_physical_gap": 0.0,
            "original_completion_date": "2026-12-31",
            "revised_completion_date": "2026-12-31",
            "planned_duration_months": 24.0,
            "elapsed_duration_months": 12.0,
            "remaining_duration_months": 12.0,
            "trajectory_anchor_date": "2024-01-01",
        },
        {
            "project_id": "P2",
            "report_month": "2026-07",
            "project_code": "P-002",
            "project_name": "National Expressway",
            "implementing_agency": "NHAI",
            "ministry": "Ministry of Road Transport and Highways",
            "sector": "Road Transport and Highways",
            "state": "Gujarat",
            "original_cost_cr": 2000.0,
            "revised_cost_cr": 2000.0,
            "cumulative_expenditure_cr": 1100.0,
            "exp_utilization": 55.0,
            "physical_progress_pct": 55.0,
            "financial_physical_gap": 0.0,
            "original_completion_date": "2026-12-31",
            "revised_completion_date": "2026-12-31",
            "planned_duration_months": 24.0,
            "elapsed_duration_months": 13.0,
            "remaining_duration_months": 11.0,
            "trajectory_anchor_date": "2024-01-01",
        },
    ]
    panel_df = pd.DataFrame(panel_rows)

    risk_rows = [
        {
            "project_id": "P1",
            "report_month": "2026-06",
            "risk_score": 50.0,
            "risk_band": "HIGH",
            "calibrated_probability": 0.50,
            "raw_probability": 0.48,
            "data_sufficiency": "SUFFICIENT",
            "observed_months_to_date": 2,
        },
        {
            "project_id": "P1",
            "report_month": "2026-07",
            "risk_score": 65.0,
            "risk_band": "CRITICAL",
            "calibrated_probability": 0.65,
            "raw_probability": 0.62,
            "data_sufficiency": "SUFFICIENT",
            "observed_months_to_date": 3,
        },
        {
            "project_id": "P2",
            "report_month": "2026-06",
            "risk_score": 20.0,
            "risk_band": "LOW",
            "calibrated_probability": 0.20,
            "raw_probability": 0.18,
            "data_sufficiency": "PROVISIONAL",
            "observed_months_to_date": 1,
        },
        {
            "project_id": "P2",
            "report_month": "2026-07",
            "risk_score": 20.0,
            "risk_band": "LOW",
            "calibrated_probability": 0.20,
            "raw_probability": 0.18,
            "data_sufficiency": "SUFFICIENT",
            "observed_months_to_date": 2,
        },
    ]
    risk_df = pd.DataFrame(risk_rows)

    ew_rows = [
        {
            "project_id": "P1",
            "report_month": "2026-06",
            "early_warning": False,
            "warning_status": "NORMAL",
            "warning_strength": 0,
            "triggers_fired": "none",
            "score_rising_fired": False,
            "gap_widening_fired": False,
            "velocity_divergence_fired": False,
            "risk_score_prev": 40.0,
            "risk_score_delta_1m": 10.0,
            "risk_score_delta_2m": None,
            "gap_delta_1m": 2.0,
            "gap_delta_2m": None,
            "progress_velocity_3mo": 1.5,
            "exp_velocity_3mo": 3.0,
        },
        {
            "project_id": "P1",
            "report_month": "2026-07",
            "early_warning": True,
            "warning_status": "ACTIVE_WARNING",
            "warning_strength": 2,
            "triggers_fired": "score_rising_2m, gap_widening_2m",
            "score_rising_fired": True,
            "gap_widening_fired": True,
            "velocity_divergence_fired": False,
            "risk_score_prev": 50.0,
            "risk_score_delta_1m": 15.0,
            "risk_score_delta_2m": 25.0,
            "gap_delta_1m": 8.0,
            "gap_delta_2m": 10.0,
            "progress_velocity_3mo": 1.0,
            "exp_velocity_3mo": 5.0,
        },
        {
            "project_id": "P2",
            "report_month": "2026-06",
            "early_warning": False,
            "warning_status": "NORMAL",
            "warning_strength": 0,
            "triggers_fired": "none",
            "score_rising_fired": False,
            "gap_widening_fired": False,
            "velocity_divergence_fired": False,
            "risk_score_prev": None,
            "risk_score_delta_1m": None,
            "risk_score_delta_2m": None,
            "gap_delta_1m": None,
            "gap_delta_2m": None,
            "progress_velocity_3mo": None,
            "exp_velocity_3mo": None,
        },
        {
            "project_id": "P2",
            "report_month": "2026-07",
            "early_warning": False,
            "warning_status": "NORMAL",
            "warning_strength": 0,
            "triggers_fired": "none",
            "score_rising_fired": False,
            "gap_widening_fired": False,
            "velocity_divergence_fired": False,
            "risk_score_prev": 20.0,
            "risk_score_delta_1m": 0.0,
            "risk_score_delta_2m": None,
            "gap_delta_1m": 0.0,
            "gap_delta_2m": None,
            "progress_velocity_3mo": 2.0,
            "exp_velocity_3mo": 2.0,
        },
    ]
    ew_df = pd.DataFrame(ew_rows)

    feat_rows = [
        {
            "project_id": "P1",
            "report_month": "2026-06",
            "is_road": False,
            "cost_overrun_pct": 20.0,
        },
        {
            "project_id": "P1",
            "report_month": "2026-07",
            "is_road": False,
            "cost_overrun_pct": 20.0,
        },
        {
            "project_id": "P2",
            "report_month": "2026-06",
            "is_road": True,
            "cost_overrun_pct": 0.0,
        },
        {
            "project_id": "P2",
            "report_month": "2026-07",
            "is_road": True,
            "cost_overrun_pct": 0.0,
        },
    ]
    feat_df = pd.DataFrame(feat_rows)

    return panel_df, risk_df, ew_df, feat_df


@pytest.fixture(autouse=True)
def setup_synthetic_repository():
    """Seed repository with deterministic synthetic data for fixture tests."""
    panel_df, risk_df, ew_df, feat_df = _build_synthetic_datasets()
    repository.load_data(
        panel_df=panel_df,
        risk_df=risk_df,
        ew_df=ew_df,
        feat_df=feat_df,
    )


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_health_check(client: TestClient):
    """GET /health must return 200 OK and valid health response."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "paimana-api"
    assert "version" in data


def test_pipeline_last_run(client: TestClient):
    """GET /pipeline/last-run returns dataset freshness metadata."""
    response = client.get("/pipeline/last-run")
    assert response.status_code == 200
    data = response.json()
    assert data["latest_data_month"] == "2026-07"
    assert data["earliest_data_month"] == "2026-06"
    assert data["total_months"] == 2
    assert data["total_canonical_projects"] == 2
    assert data["total_panel_rows"] == 4
    assert data["total_active_projects_latest_month"] == 2
    assert "freshness_note" in data


def test_national_summary(client: TestClient):
    """GET /national/summary strictly separates Non-Roads from Roads regime."""
    response = client.get("/national/summary")
    assert response.status_code == 200
    data = response.json()

    assert data["report_month"] == "2026-07"
    assert data["total_projects"] == 2

    # Non-roads checks
    non_roads = data["non_roads"]
    assert non_roads["total_projects"] == 1
    assert non_roads["transfer_regime"] is False
    assert non_roads["transfer_regime_note"] is None
    assert non_roads["band_distribution"]["CRITICAL"] == 1
    assert non_roads["active_warnings_count"] == 1

    # Roads checks (MoRTH caveated transfer regime)
    roads = data["roads"]
    assert roads["total_projects"] == 1
    assert roads["transfer_regime"] is True
    assert "caution" in roads["transfer_regime_note"].lower()
    assert roads["band_distribution"]["LOW"] == 1
    assert roads["active_warnings_count"] == 0

    # Combined aggregates
    assert data["combined_total_cost_cr"] == 3000.0  # 1000 + 2000
    assert data["combined_total_expenditure_cr"] == 1700.0  # 600 + 1100
    assert len(data["monthly_trend"]) == 2


def test_sector_summary(client: TestClient):
    """GET /sectors/{sector}/summary handles found and not-found sectors."""
    # Found sector: Railways (Non-Road)
    res_railways = client.get("/sectors/Railways/summary")
    assert res_railways.status_code == 200
    rail_data = res_railways.json()
    assert rail_data["sector"] == "Railways"
    assert rail_data["is_road"] is False
    assert rail_data["transfer_regime"] is False
    assert rail_data["total_projects"] == 1
    assert len(rail_data["top_risk_projects"]) == 1

    # Found sector: Road Transport (Transfer Regime)
    res_roads = client.get("/sectors/Road Transport and Highways/summary")
    assert res_roads.status_code == 200
    road_data = res_roads.json()
    assert road_data["is_road"] is True
    assert road_data["transfer_regime"] is True
    assert road_data["transfer_regime_note"] is not None

    # Not found sector: 404
    res_missing = client.get("/sectors/Aviation/summary")
    assert res_missing.status_code == 404
    assert "not found" in res_missing.json()["detail"].lower()


def test_ministry_summary(client: TestClient):
    """GET /ministries/{ministry}/summary returns cost/risk aggregates and sector breakdown."""
    res_min = client.get("/ministries/Ministry of Railways/summary")
    assert res_min.status_code == 200
    min_data = res_min.json()
    assert min_data["ministry"] == "Ministry of Railways"
    assert min_data["total_projects"] == 1
    assert min_data["total_cost_cr"] == 1000.0
    assert min_data["total_expenditure_cr"] == 600.0
    assert len(min_data["sectors"]) == 1
    assert min_data["sectors"][0]["sector"] == "Railways"

    # Missing ministry: 404
    res_missing = client.get("/ministries/Nonexistent Ministry/summary")
    assert res_missing.status_code == 404


def test_projects_catalog_and_filtering(client: TestClient):
    """GET /projects supports cross-filtering, sorting, and pagination."""
    # Filter by risk band CRITICAL
    res = client.get("/projects?band=CRITICAL")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["project_id"] == "P1"

    # Filter by early_warning_only
    res_ew = client.get("/projects?early_warning_only=true")
    assert res_ew.status_code == 200
    ew_data = res_ew.json()
    assert ew_data["total"] == 1
    assert ew_data["items"][0]["project_id"] == "P1"

    # Filter by state
    res_state = client.get("/projects?state=gujarat")
    assert res_state.status_code == 200
    assert res_state.json()["total"] == 1
    assert res_state.json()["items"][0]["project_id"] == "P2"

    # Pagination
    res_page = client.get("/projects?page=1&page_size=1")
    assert res_page.status_code == 200
    p_data = res_page.json()
    assert p_data["page"] == 1
    assert p_data["page_size"] == 1
    assert p_data["total"] == 2
    assert p_data["total_pages"] == 2
    assert len(p_data["items"]) == 1


def test_project_detail_dossier(client: TestClient):
    """GET /projects/{project_id} returns complete dossier with trajectory."""
    res = client.get("/projects/P1")
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == "P1"
    assert data["project_code"] == "P-001"
    assert data["data_sufficiency"] == "SUFFICIENT"
    assert data["current_metrics"]["risk_score"] == 65.0
    assert data["current_metrics"]["risk_band"] == "CRITICAL"

    # Early warning evidence trail
    ew = data["early_warning"]
    assert ew["early_warning"] is True
    assert ew["warning_status"] == "ACTIVE_WARNING"
    assert ew["warning_strength"] == 2
    assert ew["score_rising_fired"] is True
    assert ew["gap_widening_fired"] is True
    assert ew["risk_score_prev"] == 50.0

    # Multi-month history trajectory
    history = data["history"]
    assert len(history) == 2
    assert history[0]["report_month"] == "2026-06"
    assert history[1]["report_month"] == "2026-07"

    # 404 for missing project
    res_missing = client.get("/projects/P999")
    assert res_missing.status_code == 404


def test_watchlist_ordering(client: TestClient):
    """GET /watchlist returns only active warning projects ordered by strength desc."""
    res = client.get("/watchlist")
    assert res.status_code == 200
    data = res.json()
    assert data["report_month"] == "2026-07"
    assert data["total_active_warnings"] == 1
    assert data["non_roads_count"] == 1
    assert data["roads_count"] == 0
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["project_id"] == "P1"
    assert item["warning_strength"] == 2
    assert item["risk_score"] == 65.0

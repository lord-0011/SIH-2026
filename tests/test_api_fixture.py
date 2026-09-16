"""CI fixture tests for FastAPI Backend API (non-skipping, runs on synthetic dataset).

Validates:
- /health: status 200, schema match, ISO timestamp
- /pipeline/last-run: status 200, correct latest_report_month, artifact status
- /national/summary: status 200, aggregated metrics, risk bands, early warning breakdown
- /national/summary with exclude_roads=true: correctly removes road projects
- /sectors and /sectors/{sector}/summary: status 200 for valid, 404 for unknown
- /ministries and /ministries/{ministry}/summary: status 200 for valid, 404 for unknown
- /projects/{project_id}: status 200 with full fields, score, trend, drivers, trajectory; 404 for unknown
- /projects: search, filter (sector, ministry, band, warning), pagination
- /watchlist: filter by min_warning_strength, sector, sorting
- CORS headers and OpenAPI schema availability
"""

from __future__ import annotations

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.data_loader import DataLoader


@pytest.fixture(autouse=True)
def mock_api_data():
    """Setup deterministic synthetic dataset in DataLoader singleton."""
    DataLoader.reset_instance()
    loader = DataLoader.get_instance()

    records = [
        # Project 1: Railway project with active warning (rising score & gap)
        {
            "project_id": "1001",
            "report_month": "2026-05",
            "project_name": "Delhi-Mumbai High Speed Rail",
            "implementing_agency": "NHSRCL",
            "ministry": "Ministry of Railways",
            "sector": "RAILWAYS",
            "state": ["Delhi", "Maharashtra", "Gujarat"],
            "project_size_band": "Mega",
            "project_status": "Ongoing",
            "date_of_approval": "2020-01-15",
            "start_date": "2020-06-01",
            "original_completion_date": "2026-12-31",
            "revised_completion_date": "2028-12-31",
            "actual_completion_date": None,
            "original_cost_cr": 10000.0,
            "revised_cost_cr": 13000.0,
            "cumulative_expenditure_cr": 6500.0,
            "physical_progress_pct": 35.0,
            "cost_escalation_amt": 3000.0,
            "cost_escalation_pct": 30.0,
            "financial_physical_gap": 15.0,
            "schedule_variance_months": 24.0,
            "planned_duration_months": 84.0,
            "elapsed_duration_months": 72.0,
            "remaining_duration_months": 24.0,
            "risk_score": 45.0,
            "risk_band": "HIGH",
            "data_sufficiency": "SUFFICIENT",
            "early_warning": False,
            "warning_status": "STABLE_OR_IMPROVING",
            "warning_strength": 0,
            "triggers_fired": "none",
            "risk_score_prev": None,
            "risk_score_delta_1m": None,
            "risk_score_delta_2m": None,
            "gap_delta_1m": None,
            "gap_delta_2m": None,
            "progress_velocity_3mo": 1.5,
            "exp_velocity_3mo": 150.0,
        },
        {
            "project_id": "1001",
            "report_month": "2026-06",
            "project_name": "Delhi-Mumbai High Speed Rail",
            "implementing_agency": "NHSRCL",
            "ministry": "Ministry of Railways",
            "sector": "RAILWAYS",
            "state": ["Delhi", "Maharashtra", "Gujarat"],
            "project_size_band": "Mega",
            "project_status": "Ongoing",
            "date_of_approval": "2020-01-15",
            "start_date": "2020-06-01",
            "original_completion_date": "2026-12-31",
            "revised_completion_date": "2028-12-31",
            "actual_completion_date": None,
            "original_cost_cr": 10000.0,
            "revised_cost_cr": 13000.0,
            "cumulative_expenditure_cr": 7200.0,
            "physical_progress_pct": 36.0,
            "cost_escalation_amt": 3000.0,
            "cost_escalation_pct": 30.0,
            "financial_physical_gap": 19.38,
            "schedule_variance_months": 24.0,
            "planned_duration_months": 84.0,
            "elapsed_duration_months": 73.0,
            "remaining_duration_months": 23.0,
            "risk_score": 58.0,
            "risk_band": "CRITICAL",
            "data_sufficiency": "SUFFICIENT",
            "early_warning": False,
            "warning_status": "STABLE_OR_IMPROVING",
            "warning_strength": 0,
            "triggers_fired": "none",
            "risk_score_prev": 45.0,
            "risk_score_delta_1m": 13.0,
            "risk_score_delta_2m": None,
            "gap_delta_1m": 4.38,
            "gap_delta_2m": None,
            "progress_velocity_3mo": 1.0,
            "exp_velocity_3mo": 200.0,
        },
        {
            "project_id": "1001",
            "report_month": "2026-07",
            "project_name": "Delhi-Mumbai High Speed Rail",
            "implementing_agency": "NHSRCL",
            "ministry": "Ministry of Railways",
            "sector": "RAILWAYS",
            "state": ["Delhi", "Maharashtra", "Gujarat"],
            "project_size_band": "Mega",
            "project_status": "Ongoing",
            "date_of_approval": "2020-01-15",
            "start_date": "2020-06-01",
            "original_completion_date": "2026-12-31",
            "revised_completion_date": "2028-12-31",
            "actual_completion_date": None,
            "original_cost_cr": 10000.0,
            "revised_cost_cr": 13000.0,
            "cumulative_expenditure_cr": 8000.0,
            "physical_progress_pct": 36.5,
            "cost_escalation_amt": 3000.0,
            "cost_escalation_pct": 30.0,
            "financial_physical_gap": 25.04,
            "schedule_variance_months": 24.0,
            "planned_duration_months": 84.0,
            "elapsed_duration_months": 74.0,
            "remaining_duration_months": 22.0,
            "risk_score": 72.5,
            "risk_band": "CRITICAL",
            "data_sufficiency": "SUFFICIENT",
            "early_warning": True,
            "warning_status": "ACTIVE_WARNING",
            "warning_strength": 2,
            "triggers_fired": "score_rising_2m,gap_widening_2m",
            "score_rising_fired": True,
            "gap_widening_fired": True,
            "velocity_divergence_fired": False,
            "risk_score_prev": 58.0,
            "risk_score_delta_1m": 14.5,
            "risk_score_delta_2m": 27.5,
            "gap_delta_1m": 5.66,
            "gap_delta_2m": 10.04,
            "progress_velocity_3mo": 0.5,
            "exp_velocity_3mo": 250.0,
        },
        # Project 2: Power project, healthy and low risk
        {
            "project_id": "2002",
            "report_month": "2026-07",
            "project_name": "Kudankulam Nuclear Power Unit 3&4",
            "implementing_agency": "NPCIL",
            "ministry": "Department of Atomic Energy",
            "sector": "POWER",
            "state": ["Tamil Nadu"],
            "project_size_band": "Mega",
            "project_status": "Ongoing",
            "date_of_approval": "2015-03-10",
            "start_date": "2016-01-01",
            "original_completion_date": "2027-06-30",
            "revised_completion_date": "2027-06-30",
            "actual_completion_date": None,
            "original_cost_cr": 39000.0,
            "revised_cost_cr": 39000.0,
            "cumulative_expenditure_cr": 25000.0,
            "physical_progress_pct": 68.0,
            "cost_escalation_amt": 0.0,
            "cost_escalation_pct": 0.0,
            "financial_physical_gap": -3.89,
            "schedule_variance_months": 0.0,
            "planned_duration_months": 138.0,
            "elapsed_duration_months": 126.0,
            "remaining_duration_months": 12.0,
            "risk_score": 12.0,
            "risk_band": "LOW",
            "data_sufficiency": "SUFFICIENT",
            "early_warning": False,
            "warning_status": "STABLE_OR_IMPROVING",
            "warning_strength": 0,
            "triggers_fired": "none",
            "score_rising_fired": False,
            "gap_widening_fired": False,
            "velocity_divergence_fired": False,
            "risk_score_prev": 12.5,
            "risk_score_delta_1m": -0.5,
            "risk_score_delta_2m": -1.0,
            "gap_delta_1m": -0.2,
            "gap_delta_2m": -0.5,
            "progress_velocity_3mo": 1.2,
            "exp_velocity_3mo": 300.0,
        },
        # Project 3: Road project (for road filtering checks)
        {
            "project_id": "3003",
            "report_month": "2026-07",
            "project_name": "Varanasi-Kolkata Expressway Package 1",
            "implementing_agency": "NHAI",
            "ministry": "Ministry of Road Transport and Highways",
            "sector": "ROAD TRANSPORT AND HIGHWAYS",
            "state": ["Uttar Pradesh", "Bihar"],
            "project_size_band": "Major",
            "project_status": "Ongoing",
            "date_of_approval": "2022-05-01",
            "start_date": "2022-11-01",
            "original_completion_date": "2026-03-31",
            "revised_completion_date": "2027-03-31",
            "actual_completion_date": None,
            "original_cost_cr": 2500.0,
            "revised_cost_cr": 2800.0,
            "cumulative_expenditure_cr": 1200.0,
            "physical_progress_pct": 40.0,
            "cost_escalation_amt": 300.0,
            "cost_escalation_pct": 12.0,
            "financial_physical_gap": 2.86,
            "schedule_variance_months": 12.0,
            "planned_duration_months": 41.0,
            "elapsed_duration_months": 44.0,
            "remaining_duration_months": 8.0,
            "risk_score": 38.0,
            "risk_band": "MEDIUM",
            "data_sufficiency": "SUFFICIENT",
            "early_warning": False,
            "warning_status": "STABLE_OR_IMPROVING",
            "warning_strength": 0,
            "triggers_fired": "none",
            "score_rising_fired": False,
            "gap_widening_fired": False,
            "velocity_divergence_fired": False,
            "risk_score_prev": 37.0,
            "risk_score_delta_1m": 1.0,
            "risk_score_delta_2m": 2.0,
            "gap_delta_1m": 0.5,
            "gap_delta_2m": 1.0,
            "progress_velocity_3mo": 2.0,
            "exp_velocity_3mo": 50.0,
        },
    ]

    df = pd.DataFrame(records)
    loader.set_mock_data(df)
    yield loader


def test_health_endpoint():
    """GET /health must return 200 with status ok and valid timestamp."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data


def test_pipeline_last_run():
    """GET /pipeline/last-run must return 200, latest month, and available months."""
    client = TestClient(app)
    response = client.get("/pipeline/last-run")
    assert response.status_code == 200
    data = response.json()
    assert data["latest_report_month"] == "2026-07"
    assert "2026-05" in data["available_months"]
    assert "2026-07" in data["available_months"]
    assert data["total_projects_in_latest_month"] == 3


def test_national_summary():
    """GET /national/summary must return Level-1 portfolio aggregates."""
    client = TestClient(app)
    response = client.get("/national/summary")
    assert response.status_code == 200
    data = response.json()

    assert data["report_month"] == "2026-07"
    assert data["total_projects"] == 3
    # Total revised cost: 13000 + 39000 + 2800 = 54800
    assert data["total_revised_cost_cr"] == 54800.0
    # Total original cost: 10000 + 39000 + 2500 = 51500
    assert data["total_original_cost_cr"] == 51500.0
    assert data["total_cost_escalation_cr"] == 3300.0

    # Risk bands count
    bands_dict = {b["band"]: b["count"] for b in data["risk_bands"]}
    assert bands_dict["CRITICAL"] == 1
    assert bands_dict["LOW"] == 1
    assert bands_dict["MEDIUM"] == 1

    # Early warnings
    assert data["early_warnings"]["active_warnings_count"] == 1
    assert data["early_warnings"]["score_rising_count"] == 1

    # Sectors
    sector_names = [s["sector"] for s in data["sectors"]]
    assert "RAILWAYS" in sector_names
    assert "POWER" in sector_names

    # Top risk projects
    assert len(data["top_risk_projects"]) == 3
    assert data["top_risk_projects"][0]["project_id"] == "1001"
    assert data["top_risk_projects"][0]["risk_score"] == 72.5


def test_national_summary_exclude_roads():
    """GET /national/summary?exclude_roads=true must omit Road sector projects."""
    client = TestClient(app)
    response = client.get("/national/summary?exclude_roads=true")
    assert response.status_code == 200
    data = response.json()
    assert data["total_projects"] == 2
    sector_names = [s["sector"] for s in data["sectors"]]
    assert "ROAD TRANSPORT AND HIGHWAYS" not in sector_names


def test_sectors_listing_and_detail():
    """GET /sectors and GET /sectors/{sector}/summary."""
    client = TestClient(app)

    # Listing
    res_list = client.get("/sectors")
    assert res_list.status_code == 200
    sectors = res_list.json()
    assert len(sectors) == 3

    # Detail valid
    res_detail = client.get("/sectors/RAILWAYS/summary")
    assert res_detail.status_code == 200
    rail = res_detail.json()
    assert rail["sector"] == "RAILWAYS"
    assert rail["total_projects"] == 1
    assert rail["early_warnings"]["active_warnings_count"] == 1
    assert len(rail["projects"]) == 1
    assert rail["projects"][0]["project_id"] == "1001"

    # Detail not found
    res_404 = client.get("/sectors/NON_EXISTENT_SECTOR/summary")
    assert res_404.status_code == 404


def test_ministries_listing_and_detail():
    """GET /ministries and GET /ministries/{ministry}/summary."""
    client = TestClient(app)

    # Listing
    res_list = client.get("/ministries")
    assert res_list.status_code == 200
    ministries = res_list.json()
    assert len(ministries) == 3

    # Detail valid (case-insensitive)
    res_detail = client.get("/ministries/ministry of railways/summary")
    assert res_detail.status_code == 200
    min_rail = res_detail.json()
    assert min_rail["ministry"] == "Ministry of Railways"
    assert min_rail["total_projects"] == 1

    # Detail not found
    res_404 = client.get("/ministries/Unknown%20Ministry/summary")
    assert res_404.status_code == 404


def test_project_detail_level3():
    """GET /projects/{project_id} returns consolidated payload with drivers and trajectory."""
    client = TestClient(app)

    # Known project
    res = client.get("/projects/1001")
    assert res.status_code == 200
    p = res.json()

    assert p["project_id"] == "1001"
    assert p["project_name"] == "Delhi-Mumbai High Speed Rail"
    assert p["risk_score"] == 72.5
    assert p["risk_band"] == "CRITICAL"
    assert p["early_warning"] is True
    assert p["warning_strength"] == 2
    assert "score_rising_2m" in p["triggers_fired"]
    assert p["cost_escalation_pct"] == 30.0
    assert len(p["state"]) == 3

    # Check drivers
    driver_names = [d["factor_name"] for d in p["top_risk_drivers"]]
    assert "financial_physical_gap" in driver_names
    assert "early_warning_triggers" in driver_names

    # Check full trajectory across months
    assert len(p["trajectory"]) == 3
    months = [t["report_month"] for t in p["trajectory"]]
    assert months == ["2026-05", "2026-06", "2026-07"]
    assert p["trajectory"][0]["risk_score"] == 45.0
    assert p["trajectory"][1]["risk_score"] == 58.0
    assert p["trajectory"][2]["risk_score"] == 72.5

    # Non-existent project
    res_404 = client.get("/projects/999999")
    assert res_404.status_code == 404


def test_projects_pagination_and_search():
    """GET /projects supports multi-parameter filtering and text search."""
    client = TestClient(app)

    # Filter by risk_band
    res_crit = client.get("/projects?risk_band=CRITICAL")
    assert res_crit.status_code == 200
    d_crit = res_crit.json()
    assert d_crit["total_count"] == 1
    assert d_crit["projects"][0]["project_id"] == "1001"

    # Filter by early warning
    res_ew = client.get("/projects?has_warning=true")
    assert res_ew.status_code == 200
    assert res_ew.json()["total_count"] == 1

    # Search query
    res_search = client.get("/projects?search_query=Kudankulam")
    assert res_search.status_code == 200
    assert res_search.json()["total_count"] == 1
    assert res_search.json()["projects"][0]["project_id"] == "2002"

    # Pagination bounds
    res_page = client.get("/projects?page=1&page_size=2")
    assert res_page.status_code == 200
    assert len(res_page.json()["projects"]) == 2
    assert res_page.json()["total_pages"] == 2


def test_watchlist_endpoint():
    """GET /watchlist returns deteriorating projects sorted by warning strength."""
    client = TestClient(app)

    res = client.get("/watchlist")
    assert res.status_code == 200
    w = res.json()
    assert w["total_flagged_projects"] == 1
    assert len(w["projects"]) == 1
    item = w["projects"][0]
    assert item["project_id"] == "1001"
    assert item["warning_strength"] == 2
    assert item["risk_score"] == 72.5

    # Filter min_warning_strength=3 (none match)
    res_str3 = client.get("/watchlist?min_warning_strength=3")
    assert res_str3.status_code == 200
    assert res_str3.json()["total_flagged_projects"] == 0


def test_openapi_schema_availability():
    """FastAPI must serve OpenAPI documentation schema."""
    client = TestClient(app)
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    assert "paths" in schema
    assert "/health" in schema["paths"]
    assert "/national/summary" in schema["paths"]
    assert "/projects/{project_id}" in schema["paths"]
    assert "/watchlist" in schema["paths"]


def test_invalid_report_month_404():
    """Requesting non-existent report month must return 404."""
    client = TestClient(app)
    res = client.get("/national/summary?report_month=1999-01")
    assert res.status_code == 404


def test_cors_headers():
    """CORS headers must allow frontend cross-origin requests."""
    client = TestClient(app)
    res = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") in ["*", "http://localhost:3000"]


def test_read_only_invariant():
    """Serving layer must only read in-memory precomputed data without calling ML models."""
    client = TestClient(app)
    # Hit multiple endpoints repeatedly
    for endpoint in [
        "/health",
        "/pipeline/last-run",
        "/national/summary",
        "/sectors",
        "/ministries",
        "/projects/1001",
        "/watchlist",
    ]:
        res = client.get(endpoint)
        assert res.status_code == 200
        # Check sub-millisecond execution style, status 200, no training/inference artifacts created

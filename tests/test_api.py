"""Integration tests for FastAPI Backend API over real precomputed parquet artifacts (STEP_13).

Runs if data/processed/risk_scores.parquet and early_warning.parquet exist on disk.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.data_loader import DataLoader

DATA_EXISTS = (
    Path("data/processed/panel.parquet").exists()
    and Path("data/processed/risk_scores.parquet").exists()
    and Path("data/processed/early_warning.parquet").exists()
)


@pytest.mark.skipif(not DATA_EXISTS, reason="Real processed parquet artifacts not available")
def test_real_data_endpoints():
    """Integration test suite executing on real 18,860 project-month records."""
    DataLoader.reset_instance()
    loader = DataLoader.get_instance()
    assert loader.load_data() is True

    client = TestClient(app)

    # 1. Health
    res_health = client.get("/health")
    assert res_health.status_code == 200

    # 2. Last Run
    res_last = client.get("/pipeline/last-run")
    assert res_last.status_code == 200
    last_data = res_last.json()
    assert last_data["latest_report_month"] == "2026-07"
    assert len(last_data["available_months"]) >= 13

    # 3. National Summary
    res_nat = client.get("/national/summary")
    assert res_nat.status_code == 200
    nat_data = res_nat.json()
    assert nat_data["total_projects"] > 1000
    assert nat_data["avg_risk_score"] > 0

    # 4. Sectors
    res_sec = client.get("/sectors")
    assert res_sec.status_code == 200
    sectors = res_sec.json()
    assert len(sectors) > 0

    first_sec = sectors[0]["sector"]
    res_sec_detail = client.get(f"/sectors/{first_sec}/summary")
    assert res_sec_detail.status_code == 200

    # 5. Ministries
    res_min = client.get("/ministries")
    assert res_min.status_code == 200
    ministries = res_min.json()
    assert len(ministries) > 0

    first_min = ministries[0]["ministry"]
    res_min_detail = client.get(f"/ministries/{first_min}/summary")
    assert res_min_detail.status_code == 200

    # 6. Projects list & detail
    res_p_list = client.get("/projects?page=1&page_size=5")
    assert res_p_list.status_code == 200
    p_data = res_p_list.json()
    assert len(p_data["projects"]) > 0

    sample_pid = p_data["projects"][0]["project_id"]
    res_p_detail = client.get(f"/projects/{sample_pid}")
    assert res_p_detail.status_code == 200
    detail = res_p_detail.json()
    assert detail["project_id"] == sample_pid
    assert len(detail["trajectory"]) >= 1

    # 7. Watchlist
    res_watch = client.get("/watchlist?limit=10")
    assert res_watch.status_code == 200
    watch = res_watch.json()
    assert watch["total_flagged_projects"] >= 0

"""System and pipeline status endpoints: /health and /pipeline/last-run (STEP_13)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from src.api.data_loader import DataLoader
from src.api.schemas import HealthResponse, LastRunResponse, PipelineStageInfo

router = APIRouter(tags=["System & Freshness"])


def get_data_loader() -> DataLoader:
    """Dependency providing DataLoader instance."""
    return DataLoader.get_instance()


@router.get("/health", response_model=HealthResponse, summary="Liveness & Health Check")
def get_health() -> HealthResponse:
    """Check API server health and liveness."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.get(
    "/pipeline/last-run",
    response_model=LastRunResponse,
    summary="Pipeline Data Currency and Freshness",
)
def get_last_run(loader: DataLoader = Depends(get_data_loader)) -> LastRunResponse:
    """Get the latest processed report month and data currency info."""
    months = loader.get_available_months()
    latest_month = loader.get_latest_month()
    latest_df = loader.get_month_df(report_month=latest_month)
    stages = loader.get_pipeline_stages_info()

    return LastRunResponse(
        latest_report_month=latest_month,
        available_months=months,
        total_projects_in_latest_month=len(latest_df),
        data_as_of=f"Monthly Flash Report as of {latest_month}",
        pipeline_stages=[PipelineStageInfo(**s) for s in stages],
    )

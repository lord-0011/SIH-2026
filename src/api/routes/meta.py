"""Metadata and health check routes."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.models import HealthResponse, PipelineLastRunResponse
from src.api.repository import repository

router = APIRouter(tags=["Metadata"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Liveness probe verifying the API service is active and responsive."""
    return HealthResponse()


@router.get("/pipeline/last-run", response_model=PipelineLastRunResponse)
def get_pipeline_last_run() -> PipelineLastRunResponse:
    """Data freshness, report month coverage, and ingestion metadata."""
    return repository.get_last_run_metadata()

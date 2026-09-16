"""National Level-1 portfolio overview endpoint: /national/summary (STEP_13)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.data_loader import DataLoader
from src.api.schemas import NationalSummaryResponse

router = APIRouter(prefix="/national", tags=["Level-1 National Portfolio"])


def get_data_loader() -> DataLoader:
    """Dependency providing DataLoader instance."""
    return DataLoader.get_instance()


@router.get(
    "/summary",
    response_model=NationalSummaryResponse,
    summary="Get Level-1 National Portfolio Summary",
)
def get_national_summary(
    report_month: str | None = Query(
        None,
        description="Report month in YYYY-MM format (defaults to latest available month, e.g., '2026-07')",
    ),
    exclude_roads: bool = Query(
        False,
        description="Whether to exclude Road Transport & Highways sector from national totals",
    ),
    loader: DataLoader = Depends(get_data_loader),
) -> NationalSummaryResponse:
    """Return portfolio-level aggregates, cost overruns, risk distributions, and early warnings."""
    summary = loader.get_national_summary(report_month=report_month, exclude_roads=exclude_roads)
    if summary is None:
        raise HTTPException(
            status_code=404,
            detail=f"No portfolio data found for report month '{report_month or loader.get_latest_month()}'.",
        )
    return NationalSummaryResponse(**summary)

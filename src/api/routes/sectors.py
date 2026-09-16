"""Sector level-2 summary routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from src.api.models import SectorSummaryResponse
from src.api.repository import repository

router = APIRouter(tags=["Sectors"])


@router.get("/sectors/{sector}/summary", response_model=SectorSummaryResponse)
def get_sector_summary(
    sector: str,
    report_month: str | None = Query(
        None,
        description="Target report month (YYYY-MM). Defaults to latest observed month.",
    ),
) -> SectorSummaryResponse:
    """Level-2 Sector Breakdown.

    Returns sector portfolio aggregates, risk distribution, top high-risk projects,
    national benchmarks, and explicitly flags transfer regime if the sector is Road Transport.
    """
    result = repository.get_sector_summary(sector=sector, report_month=report_month)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Sector '{sector}' not found in the portfolio for report month.",
        )
    return result

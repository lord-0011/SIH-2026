"""National level-1 summary routes."""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.models import NationalSummaryResponse
from src.api.repository import repository

router = APIRouter(tags=["National"])


@router.get("/national/summary", response_model=NationalSummaryResponse)
def get_national_summary(
    report_month: str | None = Query(
        None,
        description="Target report month (YYYY-MM). Defaults to latest observed month (e.g. 2026-07).",
    )
) -> NationalSummaryResponse:
    """Level-1 National Portfolio Overview.

    Separates the primary validation regime (Non-Roads: Railways, Power, Coal, etc.)
    from the caveated transfer regime (Roads: MoRTH). Surfaces combined aggregates
    and 13-month historical risk trends.
    """
    return repository.get_national_summary(report_month=report_month)

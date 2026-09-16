"""Ministry level-2 summary routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from src.api.models import MinistrySummaryResponse
from src.api.repository import repository

router = APIRouter(tags=["Ministries"])


@router.get("/ministries/{ministry}/summary", response_model=MinistrySummaryResponse)
def get_ministry_summary(
    ministry: str,
    report_month: str | None = Query(
        None,
        description="Target report month (YYYY-MM). Defaults to latest observed month.",
    ),
) -> MinistrySummaryResponse:
    """Level-2 Ministry Overview.

    Returns ministry cost/expenditure aggregates, risk distribution, active warnings,
    and constituent sector breakdowns.
    """
    result = repository.get_ministry_summary(ministry=ministry, report_month=report_month)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Ministry '{ministry}' not found in the portfolio for report month.",
        )
    return result

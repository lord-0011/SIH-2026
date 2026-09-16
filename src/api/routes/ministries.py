"""Ministry Level-2 endpoints: /ministries and /ministries/{ministry}/summary (STEP_13)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.data_loader import DataLoader
from src.api.schemas import MinistryDetailResponse, MinistrySummaryItem

router = APIRouter(prefix="/ministries", tags=["Level-2 Ministries"])


def get_data_loader() -> DataLoader:
    """Dependency providing DataLoader instance."""
    return DataLoader.get_instance()


@router.get(
    "",
    response_model=list[MinistrySummaryItem],
    summary="List All Ministries Summary",
)
def list_ministries(
    report_month: str | None = Query(
        None,
        description="Report month (YYYY-MM). Defaults to latest available month.",
    ),
    loader: DataLoader = Depends(get_data_loader),
) -> list[MinistrySummaryItem]:
    """Get high-level summary metrics across all administrative ministries."""
    items = loader.list_ministries(report_month=report_month)
    return [MinistrySummaryItem(**item) for item in items]


@router.get(
    "/{ministry}/summary",
    response_model=MinistryDetailResponse,
    summary="Get Level-2 Ministry Detailed Summary",
)
def get_ministry_summary(
    ministry: str,
    report_month: str | None = Query(
        None,
        description="Report month (YYYY-MM). Defaults to latest available month.",
    ),
    loader: DataLoader = Depends(get_data_loader),
) -> MinistryDetailResponse:
    """Get ministry metrics, risk band breakdown, early warnings, and affiliated projects."""
    detail = loader.get_ministry_detail(ministry=ministry, report_month=report_month)
    if detail is None:
        raise HTTPException(
            status_code=404,
            detail=f"Ministry '{ministry}' not found in report month '{report_month or loader.get_latest_month()}'.",
        )
    return MinistryDetailResponse(**detail)

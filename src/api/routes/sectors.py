"""Sector Level-2 endpoints: /sectors and /sectors/{sector}/summary (STEP_13)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.data_loader import DataLoader
from src.api.schemas import SectorDetailResponse, SectorSummaryItem

router = APIRouter(prefix="/sectors", tags=["Level-2 Sectors"])


def get_data_loader() -> DataLoader:
    """Dependency providing DataLoader instance."""
    return DataLoader.get_instance()


@router.get(
    "",
    response_model=list[SectorSummaryItem],
    summary="List All Sectors Summary",
)
def list_sectors(
    report_month: str | None = Query(
        None,
        description="Report month (YYYY-MM). Defaults to latest available month.",
    ),
    loader: DataLoader = Depends(get_data_loader),
) -> list[SectorSummaryItem]:
    """Get high-level summary metrics across all infrastructure sectors."""
    items = loader.list_sectors(report_month=report_month)
    return [SectorSummaryItem(**item) for item in items]


@router.get(
    "/{sector}/summary",
    response_model=SectorDetailResponse,
    summary="Get Level-2 Sector Detailed Summary",
)
def get_sector_summary(
    sector: str,
    report_month: str | None = Query(
        None,
        description="Report month (YYYY-MM). Defaults to latest available month.",
    ),
    loader: DataLoader = Depends(get_data_loader),
) -> SectorDetailResponse:
    """Get sector metrics, risk band breakdown, early warnings, and ministry projects."""
    detail = loader.get_sector_detail(sector=sector, report_month=report_month)
    if detail is None:
        raise HTTPException(
            status_code=404,
            detail=f"Sector '{sector}' not found in report month '{report_month or loader.get_latest_month()}'.",
        )
    return SectorDetailResponse(**detail)

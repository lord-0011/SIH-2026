"""Early Warning Watchlist endpoint: /watchlist (STEP_13)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.api.data_loader import DataLoader
from src.api.schemas import WatchlistResponse

router = APIRouter(prefix="/watchlist", tags=["Early Warning Watchlist"])


def get_data_loader() -> DataLoader:
    """Dependency providing DataLoader instance."""
    return DataLoader.get_instance()


@router.get(
    "",
    response_model=WatchlistResponse,
    summary="Get Early Warning Watchlist (Deteriorating Projects)",
)
def get_watchlist(
    report_month: str | None = Query(
        None,
        description="Report month (YYYY-MM). Defaults to latest available month.",
    ),
    min_warning_strength: int = Query(
        1,
        ge=1,
        le=3,
        description="Minimum number of active deterioration triggers (1-3)",
    ),
    sector: str | None = Query(None, description="Filter watchlist by sector"),
    limit: int = Query(50, ge=1, le=500, description="Max projects to return"),
    loader: DataLoader = Depends(get_data_loader),
) -> WatchlistResponse:
    """Return projects exhibiting multi-month deterioration trends sorted by warning strength and risk score."""
    result = loader.get_watchlist(
        report_month=report_month,
        min_warning_strength=min_warning_strength,
        sector=sector,
        limit=limit,
    )
    return WatchlistResponse(**result)

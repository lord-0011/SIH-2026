"""Watchlist routes for deteriorating projects."""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.models import WatchlistResponse
from src.api.repository import repository

router = APIRouter(tags=["Watchlist"])


@router.get("/watchlist", response_model=WatchlistResponse)
def get_watchlist(
    report_month: str | None = Query(
        None,
        description="Target report month (YYYY-MM). Defaults to latest observed month.",
    ),
    regime: str | None = Query(
        None,
        description="Portfolio regime filter ('non_roads' or 'roads'). Defaults to combined.",
    ),
) -> WatchlistResponse:
    """Early Warning Watchlist.

    Surfaces projects exhibiting active deterioration (score trend rising, gap widening,
    or physical vs expenditure velocity divergence) sorted strictly by warning strength
    descending then risk score descending.
    """
    return repository.get_watchlist(report_month=report_month, regime=regime)

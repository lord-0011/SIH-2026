"""Project catalog and detailed dossier routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from src.api.models import PaginatedProjectsResponse, ProjectDetailResponse
from src.api.repository import repository

router = APIRouter(tags=["Projects"])


@router.get("/projects", response_model=PaginatedProjectsResponse)
def list_projects(
    report_month: str | None = Query(
        None,
        description="Target report month (YYYY-MM). Defaults to latest observed month.",
    ),
    band: str | None = Query(
        None,
        description="Filter by risk band (LOW, MEDIUM, HIGH, CRITICAL).",
    ),
    sector: str | None = Query(
        None,
        description="Filter by sector name (case-insensitive substring or exact).",
    ),
    ministry: str | None = Query(
        None,
        description="Filter by ministry name (case-insensitive substring or exact).",
    ),
    state: str | None = Query(
        None,
        description="Filter by state name (case-insensitive substring or exact).",
    ),
    early_warning_only: bool = Query(
        False,
        description="If True, return only projects with active early warning triggers.",
    ),
    data_sufficiency: str | None = Query(
        None,
        description="Filter by data sufficiency status (SUFFICIENT or PROVISIONAL).",
    ),
    sort_by: str = Query(
        "risk_score",
        description="Column to sort by (risk_score, physical_progress_pct, cumulative_expenditure_cr, original_cost_cr, warning_strength).",
    ),
    order: str = Query(
        "desc",
        description="Sort direction: 'asc' or 'desc'.",
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number (1-indexed).",
    ),
    page_size: int = Query(
        50,
        ge=1,
        le=200,
        description="Items per page (max 200).",
    ),
) -> PaginatedProjectsResponse:
    """Filterable, paginated project catalog.

    Supports cross-filtering by sector, ministry, state, risk band, data sufficiency,
    and early warning status, with flexible sorting and pagination.
    """
    return repository.get_projects(
        report_month=report_month,
        band=band,
        sector=sector,
        ministry=ministry,
        state=state,
        early_warning_only=early_warning_only,
        data_sufficiency=data_sufficiency,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
    )


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
def get_project_detail(
    project_id: str,
) -> ProjectDetailResponse:
    """Level-3 Deep-Dive Project Dossier.

    Returns full project metadata, latest risk score & band, early warning causal
    evidence trail, current physical/financial metrics, and complete multi-month
    historical trajectory without request-time recomputation.
    """
    detail = repository.get_project_detail(project_id=project_id)
    if detail is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found in the portfolio.",
        )
    return detail

"""Project Level-3 endpoints: /projects and /projects/{project_id} (STEP_13)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.data_loader import DataLoader
from src.api.schemas import PaginatedProjectsResponse, ProjectDetailResponse

router = APIRouter(prefix="/projects", tags=["Level-3 Projects"])


def get_data_loader() -> DataLoader:
    """Dependency providing DataLoader instance."""
    return DataLoader.get_instance()


@router.get(
    "",
    response_model=PaginatedProjectsResponse,
    summary="Search & Paginate Infrastructure Projects",
)
def list_projects(
    report_month: str | None = Query(
        None,
        description="Report month (YYYY-MM). Defaults to latest available month.",
    ),
    sector: str | None = Query(None, description="Filter by sector"),
    ministry: str | None = Query(None, description="Filter by ministry"),
    risk_band: str | None = Query(
        None, description="Filter by risk band (LOW, MEDIUM, HIGH, CRITICAL, PROVISIONAL)"
    ),
    has_warning: bool | None = Query(
        None, description="Filter by active early warning status (true/false)"
    ),
    search_query: str | None = Query(
        None, description="Text search on project name, id, or implementing agency"
    ),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    loader: DataLoader = Depends(get_data_loader),
) -> PaginatedProjectsResponse:
    """Search and paginate projects with multi-criteria filtering."""
    result = loader.get_paginated_projects(
        report_month=report_month,
        sector=sector,
        ministry=ministry,
        risk_band=risk_band,
        has_warning=has_warning,
        search_query=search_query,
        page=page,
        page_size=page_size,
    )
    return PaginatedProjectsResponse(**result)


@router.get(
    "/{project_id}",
    response_model=ProjectDetailResponse,
    summary="Get Level-3 Project Deep Dive",
)
def get_project_detail(
    project_id: str,
    report_month: str | None = Query(
        None,
        description="Report month (YYYY-MM). Defaults to latest available month.",
    ),
    loader: DataLoader = Depends(get_data_loader),
) -> ProjectDetailResponse:
    """Get project metadata, financial snapshots, calibrated risk score, early warning triggers, top risk drivers, and full monthly trajectory."""
    detail = loader.get_project_detail(project_id=project_id, report_month=report_month)
    if detail is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found in dataset.",
        )
    return ProjectDetailResponse(**detail)

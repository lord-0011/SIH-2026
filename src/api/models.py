"""Pydantic response models for the PAIMANA Backend API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness health check response."""

    status: str = Field(default="healthy", description="Service health status")
    service: str = Field(default="paimana-api", description="Service identifier")
    version: str = Field(default="1.0.0", description="API version")


class PipelineLastRunResponse(BaseModel):
    """Pipeline execution metadata and data freshness."""

    latest_data_month: str = Field(..., description="Most recent report month observed")
    earliest_data_month: str = Field(..., description="Earliest report month in the corpus")
    total_months: int = Field(..., description="Number of sequential observed monthly reports")
    total_canonical_projects: int = Field(..., description="Total distinct canonical projects")
    total_panel_rows: int = Field(..., description="Total project-month observed rows in panel")
    total_active_projects_latest_month: int = Field(
        ..., description="Number of ongoing projects in the latest report month"
    )
    freshness_note: str = Field(..., description="Human-readable freshness caveat")


class BandDistribution(BaseModel):
    """Count of projects in each quantile risk band."""

    LOW: int = 0
    MEDIUM: int = 0
    HIGH: int = 0
    CRITICAL: int = 0


class MonthlyTrendPoint(BaseModel):
    """Historical monthly summary for national risk trend charts."""

    report_month: str
    total_projects: int
    avg_risk_score: float
    critical_count: int
    high_count: int
    active_warnings_count: int
    non_roads_avg_risk_score: float | None = None
    non_roads_critical_count: int | None = None
    non_roads_active_warnings: int | None = None
    roads_avg_risk_score: float | None = None
    roads_critical_count: int | None = None
    roads_active_warnings: int | None = None


class RegimeSectorItem(BaseModel):
    """Sector summary item within a specific regime."""

    sector: str
    total_projects: int
    high_critical_count: int
    critical_count: int = 0
    high_count: int = 0
    active_warnings: int = 0
    avg_risk_score: float
    is_road: bool
    transfer_regime: bool


class RegimeMinistryItem(BaseModel):
    """Ministry escalation item within a specific regime."""

    ministry: str
    total_projects: int
    avg_risk_score: float
    critical_count: int = 0
    active_warnings: int
    score_delta_1m: float | None = None


class NationalSubSummary(BaseModel):
    """Sub-summary for a specific sector regime (Non-Roads vs Roads)."""

    total_projects: int
    total_cost_cr: float = 0.0
    total_expenditure_cr: float = 0.0
    avg_risk_score: float
    band_distribution: BandDistribution
    active_warnings_count: int
    warning_strength_distribution: dict[str, int]
    data_sufficiency_counts: dict[str, int]
    transfer_regime: bool = False
    transfer_regime_note: str | None = None
    sectors: list[RegimeSectorItem] = Field(default_factory=list)
    ministries: list[RegimeMinistryItem] = Field(default_factory=list)


class NationalSummaryResponse(BaseModel):
    """Level-1 National Dashboard Summary."""

    report_month: str
    total_projects: int
    non_roads: NationalSubSummary = Field(
        ..., description="Primary headline validation regime (Railways, Power, Coal, etc.)"
    )
    roads: NationalSubSummary = Field(..., description="Secondary caveated transfer regime (MoRTH)")
    combined_total_cost_cr: float
    combined_total_expenditure_cr: float
    combined_avg_progress_pct: float
    combined_band_distribution: BandDistribution
    combined_active_warnings: int
    monthly_trend: list[MonthlyTrendPoint]


class ProjectSummaryItem(BaseModel):
    """Compact project item for lists, search, and sector views."""

    project_id: str
    project_name: str
    ministry: str
    sector: str
    state: str
    is_road: bool
    transfer_regime: bool
    data_sufficiency: str
    risk_score: float
    risk_band: str
    calibrated_probability: float
    early_warning: bool
    warning_status: str
    warning_strength: int
    triggers_fired: str
    original_cost_cr: float
    cumulative_expenditure_cr: float
    physical_progress_pct: float


class PaginatedProjectsResponse(BaseModel):
    """Filterable, paginated project catalog."""

    total: int
    page: int
    page_size: int
    total_pages: int
    report_month: str
    items: list[ProjectSummaryItem]


class SectorSummaryResponse(BaseModel):
    """Level-2 Sector Summary."""

    sector: str
    report_month: str
    is_road: bool
    transfer_regime: bool
    transfer_regime_note: str | None = None
    total_projects: int
    total_cost_cr: float
    total_expenditure_cr: float
    avg_physical_progress_pct: float
    avg_risk_score: float
    band_distribution: BandDistribution
    active_warnings_count: int
    top_risk_projects: list[ProjectSummaryItem]
    national_benchmarks: dict[str, Any]


class MinistrySectorItem(BaseModel):
    """Sector summary within a ministry."""

    sector: str
    total_projects: int
    avg_risk_score: float
    active_warnings: int


class MinistrySummaryResponse(BaseModel):
    """Level-2 Ministry Summary."""

    ministry: str
    report_month: str
    total_projects: int
    total_cost_cr: float
    total_expenditure_cr: float
    avg_risk_score: float
    band_distribution: BandDistribution
    active_warnings_count: int
    sectors: list[MinistrySectorItem]


class ProjectTrajectoryPoint(BaseModel):
    """Monthly historical trajectory point for a single project."""

    report_month: str
    risk_score: float
    risk_band: str
    calibrated_probability: float
    physical_progress_pct: float
    cumulative_expenditure_cr: float
    financial_physical_gap: float
    early_warning: bool
    warning_status: str
    warning_strength: int
    triggers_fired: str


class EarlyWarningEvidence(BaseModel):
    """Causal evidence trail explaining early warning status."""

    early_warning: bool
    warning_status: str
    warning_strength: int
    triggers_fired: str
    score_rising_fired: bool
    gap_widening_fired: bool
    velocity_divergence_fired: bool
    risk_score_prev: float | None = None
    risk_score_delta_1m: float | None = None
    risk_score_delta_2m: float | None = None
    gap_delta_1m: float | None = None
    gap_delta_2m: float | None = None
    progress_velocity_3mo: float | None = None
    exp_velocity_3mo: float | None = None


class ProjectCurrentMetrics(BaseModel):
    """Current snapshot metrics for a single project."""

    report_month: str
    risk_score: float
    risk_band: str
    calibrated_probability: float
    raw_probability: float
    original_cost_cr: float
    revised_cost_cr: float
    cumulative_expenditure_cr: float
    exp_utilization: float
    physical_progress_pct: float
    financial_physical_gap: float
    original_completion_date: str | None = None
    revised_completion_date: str | None = None
    planned_duration_months: float | None = None
    elapsed_duration_months: float | None = None
    remaining_duration_months: float | None = None
    trajectory_anchor_date: str | None = None


class ProjectDetailResponse(BaseModel):
    """Level-3 Comprehensive Project Dossier."""

    project_id: str
    project_code: str
    project_name: str
    implementing_agency: str
    ministry: str
    sector: str
    state: str
    is_road: bool
    transfer_regime: bool
    transfer_regime_note: str | None = None
    data_sufficiency: str
    observed_months_to_date: int
    current_metrics: ProjectCurrentMetrics
    early_warning: EarlyWarningEvidence
    history: list[ProjectTrajectoryPoint]


class WatchlistItem(BaseModel):
    """Project on the deteriorating watchlist."""

    project_id: str
    project_name: str
    ministry: str
    sector: str
    is_road: bool
    transfer_regime: bool
    data_sufficiency: str
    risk_score: float
    risk_band: str
    warning_strength: int
    triggers_fired: str
    score_delta_1m: float | None = None
    score_delta_2m: float | None = None
    gap_delta_1m: float | None = None
    progress_velocity_3mo: float | None = None
    exp_velocity_3mo: float | None = None
    physical_progress_pct: float


class WatchlistResponse(BaseModel):
    """Deteriorating projects watchlist."""

    report_month: str
    total_active_warnings: int
    non_roads_count: int
    roads_count: int
    items: list[WatchlistItem]

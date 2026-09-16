"""Pydantic request and response schemas for PAIMANA FastAPI Serving Layer (STEP_13).

Provides strongly-typed models with validation, descriptions, and OpenAPI schemas
for Health, Last-Run, National, Sector, Ministry, Project, and Watchlist endpoints.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# System & Freshness Models
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field("ok", description="Liveness status")
    version: str = Field("1.0.0", description="API version")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")


class PipelineStageInfo(BaseModel):
    """Metadata about a precomputed pipeline stage artifact."""

    name: str = Field(..., description="Stage name")
    path: str = Field(..., description="Artifact path")
    exists: bool = Field(..., description="Whether artifact file exists")
    rows: int | None = Field(None, description="Row count if loaded")


class LastRunResponse(BaseModel):
    """Pipeline freshness and data currency response schema."""

    latest_report_month: str = Field(
        ..., description="Most recent report month in processed data (YYYY-MM)"
    )
    available_months: list[str] = Field(
        ..., description="List of all available report months in chronological order"
    )
    total_projects_in_latest_month: int = Field(
        ..., description="Total active observed projects in latest month"
    )
    data_as_of: str = Field(..., description="Human-readable currency indicator")
    pipeline_stages: list[PipelineStageInfo] = Field(
        default_factory=list, description="Status of pipeline artifacts"
    )


# ---------------------------------------------------------------------------
# Common Breakdown Models
# ---------------------------------------------------------------------------


class RiskBandCount(BaseModel):
    """Counts and percentages for risk bands."""

    band: str = Field(..., description="Risk band name: LOW, MEDIUM, HIGH, CRITICAL, PROVISIONAL")
    count: int = Field(..., description="Number of projects in band")
    percentage: float = Field(..., description="Share of projects in band (0-100%)")


class EarlyWarningSummary(BaseModel):
    """Summary metrics of active early warning triggers."""

    active_warnings_count: int = Field(..., description="Number of projects with active warning")
    active_warning_rate_pct: float = Field(
        ..., description="Percentage of projects with active warning"
    )
    score_rising_count: int = Field(
        ..., description="Projects triggered by 2-month rising risk score"
    )
    gap_widening_count: int = Field(
        ..., description="Projects triggered by 2-month widening physical-financial gap"
    )
    velocity_divergence_count: int = Field(
        ..., description="Projects triggered by velocity divergence"
    )
    strength_1_count: int = Field(..., description="Warnings with 1 trigger active")
    strength_2_count: int = Field(..., description="Warnings with 2 triggers active")
    strength_3_count: int = Field(..., description="Warnings with 3 triggers active")


class ProjectQuickSummary(BaseModel):
    """Compact project representation for list and summary endpoints."""

    project_id: str = Field(..., description="Canonical project ID")
    project_name: str = Field(..., description="Project name")
    sector: str = Field(..., description="Sector")
    ministry: str = Field(..., description="Ministry")
    original_cost_cr: float = Field(..., description="Original sanctioned cost in Crore INR")
    revised_cost_cr: float = Field(..., description="Latest revised cost in Crore INR")
    cost_escalation_pct: float = Field(..., description="Cost escalation percentage")
    physical_progress_pct: float = Field(..., description="Physical progress percentage (0-100)")
    risk_score: float = Field(..., description="Calibrated risk score (0-100)")
    risk_band: str = Field(..., description="Risk band: LOW, MEDIUM, HIGH, CRITICAL, PROVISIONAL")
    early_warning: bool = Field(..., description="Whether project has an active early warning")
    warning_status: str = Field(
        ..., description="ACTIVE_WARNING, STABLE_OR_IMPROVING, INSUFFICIENT_HISTORY, STALE_HISTORY"
    )
    warning_strength: int = Field(..., description="Number of fired triggers (0-3)")
    triggers_fired: str = Field(..., description="Comma-delimited list of active triggers")


# ---------------------------------------------------------------------------
# National Level-1 Summary Models
# ---------------------------------------------------------------------------


class SectorSummaryItem(BaseModel):
    """High-level summary per sector."""

    sector: str = Field(..., description="Sector name")
    total_projects: int = Field(..., description="Total projects in sector")
    total_original_cost_cr: float = Field(..., description="Sum of original cost in Cr")
    total_revised_cost_cr: float = Field(..., description="Sum of revised cost in Cr")
    total_cost_escalation_cr: float = Field(..., description="Total cost escalation in Cr")
    avg_cost_escalation_pct: float = Field(..., description="Average cost escalation %")
    avg_physical_progress_pct: float = Field(..., description="Average physical progress %")
    avg_risk_score: float = Field(..., description="Average risk score")
    critical_risk_count: int = Field(..., description="Number of CRITICAL band projects")
    high_risk_count: int = Field(..., description="Number of HIGH band projects")
    active_warnings_count: int = Field(..., description="Projects with early warning")


class MinistrySummaryItem(BaseModel):
    """High-level summary per ministry."""

    ministry: str = Field(..., description="Ministry name")
    total_projects: int = Field(..., description="Total projects in ministry")
    total_original_cost_cr: float = Field(..., description="Sum of original cost in Cr")
    total_revised_cost_cr: float = Field(..., description="Sum of revised cost in Cr")
    total_cost_escalation_cr: float = Field(..., description="Total cost escalation in Cr")
    avg_cost_escalation_pct: float = Field(..., description="Average cost escalation %")
    avg_physical_progress_pct: float = Field(..., description="Average physical progress %")
    avg_risk_score: float = Field(..., description="Average risk score")
    critical_risk_count: int = Field(..., description="Number of CRITICAL band projects")
    high_risk_count: int = Field(..., description="Number of HIGH band projects")
    active_warnings_count: int = Field(..., description="Projects with early warning")


class NationalSummaryResponse(BaseModel):
    """Level-1 National Portfolio Overview response schema."""

    report_month: str = Field(..., description="Selected report month (YYYY-MM)")
    total_projects: int = Field(..., description="Total projects monitored")
    total_original_cost_cr: float = Field(
        ..., description="Total original cost across portfolio (Cr)"
    )
    total_revised_cost_cr: float = Field(
        ..., description="Total revised cost across portfolio (Cr)"
    )
    total_expenditure_cr: float = Field(..., description="Total cumulative expenditure (Cr)")
    total_cost_escalation_cr: float = Field(..., description="Total cost escalation amount (Cr)")
    portfolio_cost_escalation_pct: float = Field(
        ..., description="Portfolio-wide cost escalation percentage"
    )
    avg_physical_progress_pct: float = Field(..., description="Mean physical progress percentage")
    avg_financial_physical_gap: float = Field(
        ..., description="Mean gap between expenditure utilization and physical progress"
    )
    avg_risk_score: float = Field(..., description="Mean calibrated risk score across all projects")
    risk_bands: list[RiskBandCount] = Field(..., description="Distribution of risk bands")
    early_warnings: EarlyWarningSummary = Field(..., description="Early warning detection summary")
    sectors: list[SectorSummaryItem] = Field(..., description="Sector breakdown")
    top_risk_projects: list[ProjectQuickSummary] = Field(
        ..., description="Top 10 highest risk projects"
    )


# ---------------------------------------------------------------------------
# Sector Level-2 Models
# ---------------------------------------------------------------------------


class SectorDetailResponse(BaseModel):
    """Level-2 Sector Summary response schema."""

    sector: str = Field(..., description="Sector name")
    report_month: str = Field(..., description="Report month (YYYY-MM)")
    total_projects: int = Field(..., description="Total projects in sector")
    total_original_cost_cr: float = Field(..., description="Total original cost in Cr")
    total_revised_cost_cr: float = Field(..., description="Total revised cost in Cr")
    total_expenditure_cr: float = Field(..., description="Total expenditure in Cr")
    total_cost_escalation_cr: float = Field(..., description="Total cost escalation in Cr")
    avg_cost_escalation_pct: float = Field(..., description="Mean cost escalation percentage")
    avg_physical_progress_pct: float = Field(..., description="Mean physical progress percentage")
    avg_financial_physical_gap: float = Field(..., description="Mean financial physical gap")
    avg_risk_score: float = Field(..., description="Mean risk score in sector")
    risk_bands: list[RiskBandCount] = Field(..., description="Distribution of risk bands in sector")
    early_warnings: EarlyWarningSummary = Field(
        ..., description="Early warning breakdown in sector"
    )
    ministries: list[MinistrySummaryItem] = Field(
        ..., description="Ministries operating in this sector"
    )
    projects: list[ProjectQuickSummary] = Field(..., description="Projects in this sector")


# ---------------------------------------------------------------------------
# Ministry Level-2 Models
# ---------------------------------------------------------------------------


class MinistryDetailResponse(BaseModel):
    """Level-2 Ministry Summary response schema."""

    ministry: str = Field(..., description="Ministry name")
    report_month: str = Field(..., description="Report month (YYYY-MM)")
    total_projects: int = Field(..., description="Total projects under ministry")
    total_original_cost_cr: float = Field(..., description="Total original cost in Cr")
    total_revised_cost_cr: float = Field(..., description="Total revised cost in Cr")
    total_expenditure_cr: float = Field(..., description="Total expenditure in Cr")
    total_cost_escalation_cr: float = Field(..., description="Total cost escalation in Cr")
    avg_cost_escalation_pct: float = Field(..., description="Mean cost escalation percentage")
    avg_physical_progress_pct: float = Field(..., description="Mean physical progress percentage")
    avg_financial_physical_gap: float = Field(..., description="Mean financial physical gap")
    avg_risk_score: float = Field(..., description="Mean risk score under ministry")
    risk_bands: list[RiskBandCount] = Field(
        ..., description="Distribution of risk bands in ministry"
    )
    early_warnings: EarlyWarningSummary = Field(
        ..., description="Early warning breakdown in ministry"
    )
    sectors: list[SectorSummaryItem] = Field(..., description="Sectors within this ministry")
    projects: list[ProjectQuickSummary] = Field(..., description="Projects under this ministry")


# ---------------------------------------------------------------------------
# Project Level-3 Models
# ---------------------------------------------------------------------------


class ProjectHistoricalPoint(BaseModel):
    """Single monthly observation in project historical trajectory."""

    report_month: str = Field(..., description="Observation month (YYYY-MM)")
    risk_score: float = Field(..., description="Calibrated risk score (0-100)")
    risk_band: str = Field(..., description="Risk band")
    physical_progress_pct: float = Field(..., description="Physical progress percentage")
    cumulative_expenditure_cr: float = Field(..., description="Cumulative expenditure in Cr")
    exp_utilization: float = Field(..., description="Expenditure utilization ratio (0-1+)")
    financial_physical_gap: float = Field(..., description="Financial physical gap (%)")
    progress_velocity_3mo: float = Field(..., description="3-month rolling progress velocity")
    exp_velocity_3mo: float = Field(..., description="3-month rolling expenditure velocity")
    early_warning: bool = Field(..., description="Whether early warning fired")
    warning_status: str = Field(..., description="Warning status")
    triggers_fired: str = Field(..., description="Triggers fired")


class ProjectRiskDriver(BaseModel):
    """Key predictive risk driver factor explaining project score."""

    factor_name: str = Field(..., description="Identifier of the risk driver")
    display_name: str = Field(..., description="Human-readable driver description")
    value: Any = Field(..., description="Observed value")
    benchmark: str | None = Field(None, description="Contextual benchmark or threshold")
    severity: str = Field(..., description="HIGH, MEDIUM, LOW, NEUTRAL")
    explanation: str = Field(..., description="Explanation of risk impact")


class ProjectDetailResponse(BaseModel):
    """Level-3 Project Deep Dive consolidated payload."""

    # Identification
    project_id: str = Field(..., description="Canonical project ID")
    project_name: str = Field(..., description="Official project title")
    implementing_agency: str | None = Field(None, description="Implementing agency / PSU")
    ministry: str = Field(..., description="Administrative ministry")
    sector: str = Field(..., description="Sector classification")
    state: list[str] = Field(default_factory=list, description="State(s) spanned by project")
    project_size_band: str = Field(..., description="Mega (>=1000cr) / Major")
    project_status: str = Field(..., description="Reported status (Ongoing, Completed, etc.)")

    # Timeline & Milestone Dates
    date_of_approval: str | None = Field(None, description="Date of formal government approval")
    start_date: str | None = Field(None, description="Work commencement date")
    original_completion_date: str | None = Field(
        None, description="Original targeted completion date"
    )
    revised_completion_date: str | None = Field(None, description="Current revised completion date")
    actual_completion_date: str | None = Field(
        None, description="Actual commissioning date if complete"
    )

    # Financials & Current Snapshot
    report_month: str = Field(..., description="Current data reporting month (YYYY-MM)")
    original_cost_cr: float = Field(..., description="Original sanctioned cost in Cr")
    revised_cost_cr: float = Field(..., description="Revised sanctioned cost in Cr")
    cumulative_expenditure_cr: float = Field(..., description="Cumulative expenditure to date (Cr)")
    cost_escalation_amt_cr: float = Field(..., description="Cost escalation amount (Cr)")
    cost_escalation_pct: float = Field(..., description="Cost escalation percentage")
    physical_progress_pct: float = Field(..., description="Physical completion progress (0-100%)")
    financial_physical_gap: float = Field(
        ..., description="Gap between expenditure utilization and physical progress"
    )
    schedule_variance_months: float = Field(..., description="Schedule delay/variance in months")
    planned_duration_months: float = Field(..., description="Planned duration in months")
    elapsed_duration_months: float = Field(..., description="Elapsed duration in months")
    remaining_duration_months: float = Field(
        ..., description="Remaining duration to targeted completion"
    )

    # Risk & Early Warning Assessment
    risk_score: float = Field(..., description="Calibrated risk score (0-100)")
    risk_band: str = Field(..., description="Risk band: LOW, MEDIUM, HIGH, CRITICAL, PROVISIONAL")
    data_sufficiency: str = Field(..., description="SUFFICIENT or PROVISIONAL")
    early_warning: bool = Field(..., description="Whether project has an active early warning")
    warning_status: str = Field(..., description="Warning status classification")
    warning_strength: int = Field(..., description="Count of active deterioration triggers (0-3)")
    triggers_fired: str = Field(..., description="Active trigger list")

    # Trend Deltas
    risk_score_prev: float | None = Field(None, description="Prior month risk score")
    risk_score_delta_1m: float | None = Field(None, description="1-month score change")
    risk_score_delta_2m: float | None = Field(None, description="2-month score change")
    gap_delta_1m: float | None = Field(None, description="1-month financial-physical gap change")
    gap_delta_2m: float | None = Field(None, description="2-month financial-physical gap change")

    # Interpretability & Trajectory
    top_risk_drivers: list[ProjectRiskDriver] = Field(
        default_factory=list, description="Top explanatory risk drivers"
    )
    trajectory: list[ProjectHistoricalPoint] = Field(
        default_factory=list, description="Full historical monthly trajectory"
    )


# ---------------------------------------------------------------------------
# Watchlist Models
# ---------------------------------------------------------------------------


class WatchlistItem(BaseModel):
    """Detailed early warning watchlist entry for deteriorating projects."""

    project_id: str = Field(..., description="Canonical project ID")
    project_name: str = Field(..., description="Project name")
    sector: str = Field(..., description="Sector")
    ministry: str = Field(..., description="Ministry")
    report_month: str = Field(..., description="Current report month")
    risk_score: float = Field(..., description="Calibrated risk score (0-100)")
    risk_band: str = Field(..., description="Risk band")
    warning_status: str = Field(..., description="Warning status")
    warning_strength: int = Field(..., description="Warning strength (1-3)")
    triggers_fired: str = Field(..., description="Triggers that fired")
    risk_score_prev: float | None = Field(None, description="Prior score")
    risk_score_delta_1m: float | None = Field(None, description="1-month score delta")
    risk_score_delta_2m: float | None = Field(None, description="2-month score delta")
    financial_physical_gap: float = Field(..., description="Financial physical gap (%)")
    gap_delta_1m: float | None = Field(None, description="1-month gap delta")
    gap_delta_2m: float | None = Field(None, description="2-month gap delta")
    progress_velocity_3mo: float = Field(..., description="3-month progress velocity (%/mo)")
    exp_velocity_3mo: float = Field(..., description="3-month expenditure velocity (Cr/mo)")
    revised_cost_cr: float = Field(..., description="Revised cost in Cr")
    physical_progress_pct: float = Field(..., description="Physical progress %")


class WatchlistResponse(BaseModel):
    """Response schema for early warning watchlist."""

    report_month: str = Field(..., description="Report month")
    total_flagged_projects: int = Field(..., description="Count of projects on watchlist")
    min_warning_strength_filter: int = Field(..., description="Filter threshold applied")
    projects: list[WatchlistItem] = Field(..., description="List of deteriorating projects")


# ---------------------------------------------------------------------------
# Project Pagination Models
# ---------------------------------------------------------------------------


class PaginatedProjectsResponse(BaseModel):
    """Paginated list of projects response."""

    report_month: str = Field(..., description="Selected report month")
    total_count: int = Field(..., description="Total matching projects")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total pages available")
    projects: list[ProjectQuickSummary] = Field(..., description="List of project items")

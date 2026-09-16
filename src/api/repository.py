"""In-memory Data Repository for PAIMANA Backend API.

Loads precomputed parquets read-only, merges them on (project_id, report_month),
and serves sliced views without recomputing or drifting from verified numbers.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.api.config import settings
from src.api.models import (
    BandDistribution,
    EarlyWarningEvidence,
    MinistrySectorItem,
    MinistrySummaryResponse,
    MonthlyTrendPoint,
    NationalSubSummary,
    NationalSummaryResponse,
    PaginatedProjectsResponse,
    PipelineLastRunResponse,
    ProjectCurrentMetrics,
    ProjectDetailResponse,
    ProjectSummaryItem,
    ProjectTrajectoryPoint,
    SectorSummaryResponse,
    WatchlistItem,
    WatchlistResponse,
)

log = logging.getLogger(__name__)


class DataRepository:
    """Read-only in-memory repository over verified processed tables."""

    def __init__(self) -> None:
        self.df: pd.DataFrame = pd.DataFrame()
        self.latest_month: str = "2026-07"
        self.earliest_month: str = "2025-07"
        self.months_list: list[str] = []
        self._is_loaded: bool = False

    def load_data(
        self,
        panel_df: pd.DataFrame | None = None,
        risk_df: pd.DataFrame | None = None,
        ew_df: pd.DataFrame | None = None,
        feat_df: pd.DataFrame | None = None,
    ) -> None:
        """Load and merge precomputed tables into an in-memory unified DataFrame."""
        if panel_df is None:
            if not settings.PANEL_PARQUET_PATH.exists():
                log.warning("Panel parquet not found at %s", settings.PANEL_PARQUET_PATH)
                return
            panel_df = pd.read_parquet(settings.PANEL_PARQUET_PATH)

        if risk_df is None:
            if not settings.RISK_SCORES_PARQUET_PATH.exists():
                log.warning(
                    "Risk scores parquet not found at %s", settings.RISK_SCORES_PARQUET_PATH
                )
                return
            risk_df = pd.read_parquet(settings.RISK_SCORES_PARQUET_PATH)

        if ew_df is None:
            if not settings.EARLY_WARNING_PARQUET_PATH.exists():
                log.warning(
                    "Early warning parquet not found at %s", settings.EARLY_WARNING_PARQUET_PATH
                )
                return
            ew_df = pd.read_parquet(settings.EARLY_WARNING_PARQUET_PATH)

        if feat_df is None:
            if not settings.FEATURES_PARQUET_PATH.exists():
                log.warning("Features parquet not found at %s", settings.FEATURES_PARQUET_PATH)
                return
            feat_df = pd.read_parquet(settings.FEATURES_PARQUET_PATH)

        # Merge carefully on project_id and report_month without duplicating columns
        merged = panel_df.copy()

        # Risk columns to merge
        risk_cols_to_use = [
            c
            for c in risk_df.columns
            if c in ["project_id", "report_month"] or c not in merged.columns
        ]
        merged = merged.merge(
            risk_df[risk_cols_to_use], on=["project_id", "report_month"], how="inner"
        )

        # Early warning columns to merge
        ew_cols_to_use = [
            c
            for c in ew_df.columns
            if c in ["project_id", "report_month"] or c not in merged.columns
        ]
        merged = merged.merge(ew_df[ew_cols_to_use], on=["project_id", "report_month"], how="inner")

        # Feature columns to merge
        feat_cols_to_use = [
            c
            for c in feat_df.columns
            if c in ["project_id", "report_month"] or c not in merged.columns
        ]
        merged = merged.merge(
            feat_df[feat_cols_to_use], on=["project_id", "report_month"], how="inner"
        )

        # Ensure project_id is string
        merged["project_id"] = merged["project_id"].astype(str)
        merged["is_road"] = merged["sector"].astype(str).str.lower().str.contains("road")
        merged["transfer_regime"] = merged["is_road"]

        self.df = merged
        self.months_list = sorted(self.df["report_month"].unique().tolist())
        if self.months_list:
            self.earliest_month = self.months_list[0]
            self.latest_month = self.months_list[-1]

        self._is_loaded = True
        log.info(
            "DataRepository loaded: %d rows, %d distinct projects, months %s to %s",
            len(self.df),
            self.df["project_id"].nunique(),
            self.earliest_month,
            self.latest_month,
        )

    def is_loaded(self) -> bool:
        return self._is_loaded

    def get_last_run_metadata(self) -> PipelineLastRunResponse:
        """Return pipeline metadata and data freshness."""
        total_projects = self.df["project_id"].nunique() if not self.df.empty else 0
        latest_active = (
            len(self.df[self.df["report_month"] == self.latest_month]) if not self.df.empty else 0
        )
        return PipelineLastRunResponse(
            latest_data_month=self.latest_month,
            earliest_data_month=self.earliest_month,
            total_months=len(self.months_list),
            total_canonical_projects=total_projects,
            total_panel_rows=len(self.df),
            total_active_projects_latest_month=latest_active,
            freshness_note=(
                f"Data verified as of {self.latest_month}. Serving precomputed batch outputs."
            ),
        )

    def get_national_summary(self, report_month: str | None = None) -> NationalSummaryResponse:
        """Level-1 National Dashboard Summary."""
        target_month = report_month or self.latest_month
        m_df = self.df[self.df["report_month"] == target_month]

        # Split into Non-Roads (Primary validation regime) and Roads (Secondary transfer regime)
        nr_df = m_df[~m_df["is_road"]]
        roads_df = m_df[m_df["is_road"]]

        def _compute_regime_sub(sub: pd.DataFrame, is_roads: bool) -> NationalSubSummary:
            cnt = len(sub)
            if cnt == 0:
                return NationalSubSummary(
                    total_projects=0,
                    avg_risk_score=0.0,
                    band_distribution=BandDistribution(),
                    active_warnings_count=0,
                    warning_strength_distribution={"1": 0, "2": 0, "3": 0},
                    data_sufficiency_counts={"SUFFICIENT": 0, "PROVISIONAL": 0},
                    transfer_regime=is_roads,
                    transfer_regime_note=(
                        "Onboarded Dec 2025 with expired backlog dates; interpret with caution"
                        if is_roads
                        else None
                    ),
                )
            bands = sub["risk_band"].value_counts().to_dict()
            str_dist = {
                "1": int((sub["warning_strength"] == 1).sum()),
                "2": int((sub["warning_strength"] == 2).sum()),
                "3": int((sub["warning_strength"] == 3).sum()),
            }
            suff_dist = {
                "SUFFICIENT": int((sub["data_sufficiency"] == "SUFFICIENT").sum()),
                "PROVISIONAL": int((sub["data_sufficiency"] == "PROVISIONAL").sum()),
            }
            return NationalSubSummary(
                total_projects=cnt,
                avg_risk_score=round(float(sub["risk_score"].mean()), 1),
                band_distribution=BandDistribution(
                    LOW=int(bands.get("LOW", 0)),
                    MEDIUM=int(bands.get("MEDIUM", 0)),
                    HIGH=int(bands.get("HIGH", 0)),
                    CRITICAL=int(bands.get("CRITICAL", 0)),
                ),
                active_warnings_count=int(sub["early_warning"].sum()),
                warning_strength_distribution=str_dist,
                data_sufficiency_counts=suff_dist,
                transfer_regime=is_roads,
                transfer_regime_note=(
                    "Onboarded Dec 2025 with expired backlog dates; interpret with caution"
                    if is_roads
                    else None
                ),
            )

        nr_sub = _compute_regime_sub(nr_df, is_roads=False)
        roads_sub = _compute_regime_sub(roads_df, is_roads=True)

        combined_bands = m_df["risk_band"].value_counts().to_dict() if len(m_df) > 0 else {}
        comb_orig_cost = float(m_df["original_cost_cr"].sum()) if len(m_df) > 0 else 0.0
        comb_cum_exp = float(m_df["cumulative_expenditure_cr"].sum()) if len(m_df) > 0 else 0.0
        comb_prog = float(m_df["physical_progress_pct"].mean()) if len(m_df) > 0 else 0.0

        # Historical monthly trend
        trend_points = []
        for m in self.months_list:
            sub_m = self.df[self.df["report_month"] == m]
            crit = int((sub_m["risk_band"] == "CRITICAL").sum())
            high = int((sub_m["risk_band"] == "HIGH").sum())
            warn = int(sub_m["early_warning"].sum())
            avg_s = round(float(sub_m["risk_score"].mean()), 1) if len(sub_m) > 0 else 0.0
            trend_points.append(
                MonthlyTrendPoint(
                    report_month=m,
                    total_projects=len(sub_m),
                    avg_risk_score=avg_s,
                    critical_count=crit,
                    high_count=high,
                    active_warnings_count=warn,
                )
            )

        return NationalSummaryResponse(
            report_month=target_month,
            total_projects=len(m_df),
            non_roads=nr_sub,
            roads=roads_sub,
            combined_total_cost_cr=round(comb_orig_cost, 2),
            combined_total_expenditure_cr=round(comb_cum_exp, 2),
            combined_avg_progress_pct=round(comb_prog, 2),
            combined_band_distribution=BandDistribution(
                LOW=int(combined_bands.get("LOW", 0)),
                MEDIUM=int(combined_bands.get("MEDIUM", 0)),
                HIGH=int(combined_bands.get("HIGH", 0)),
                CRITICAL=int(combined_bands.get("CRITICAL", 0)),
            ),
            combined_active_warnings=int(m_df["early_warning"].sum()) if len(m_df) > 0 else 0,
            monthly_trend=trend_points,
        )

    def get_sector_summary(
        self, sector: str, report_month: str | None = None
    ) -> SectorSummaryResponse | None:
        """Level-2 Sector Summary."""
        target_month = report_month or self.latest_month
        m_df = self.df[self.df["report_month"] == target_month]
        sec_clean = sector.strip().lower()
        sec_df = m_df[m_df["sector"].astype(str).str.lower() == sec_clean]
        if len(sec_df) == 0:
            sec_df = m_df[
                m_df["sector"].astype(str).str.lower().str.contains(sec_clean, regex=False)
            ]

        if len(sec_df) == 0:
            return None

        actual_sector_name = sec_df["sector"].iloc[0]
        is_road = bool(sec_df["is_road"].iloc[0])

        bands = sec_df["risk_band"].value_counts().to_dict()
        top_projects_df = sec_df.sort_values("risk_score", ascending=False).head(10)
        top_projects = [
            ProjectSummaryItem(
                project_id=str(row["project_id"]),
                project_name=str(row["project_name"]),
                ministry=str(row["ministry"]),
                sector=str(row["sector"]),
                state=str(row.get("state", "Multi-State")),
                is_road=bool(row["is_road"]),
                transfer_regime=bool(row["transfer_regime"]),
                data_sufficiency=str(row["data_sufficiency"]),
                risk_score=float(row["risk_score"]),
                risk_band=str(row["risk_band"]),
                calibrated_probability=float(row["calibrated_probability"]),
                early_warning=bool(row["early_warning"]),
                warning_status=str(row["warning_status"]),
                warning_strength=int(row["warning_strength"]),
                triggers_fired=str(row["triggers_fired"]),
                original_cost_cr=float(row["original_cost_cr"]),
                cumulative_expenditure_cr=float(row["cumulative_expenditure_cr"]),
                physical_progress_pct=float(row["physical_progress_pct"]),
            )
            for _, row in top_projects_df.iterrows()
        ]

        # National non-roads benchmarks for comparison
        nr_all = m_df[~m_df["is_road"]]
        benchmarks = {
            "national_non_roads_avg_score": (
                round(float(nr_all["risk_score"].mean()), 1) if len(nr_all) > 0 else 0.0
            ),
            "national_non_roads_critical_pct": (
                round(float((nr_all["risk_band"] == "CRITICAL").mean() * 100.0), 1)
                if len(nr_all) > 0
                else 0.0
            ),
            "national_non_roads_active_warning_pct": (
                round(float(nr_all["early_warning"].mean() * 100.0), 1) if len(nr_all) > 0 else 0.0
            ),
        }

        return SectorSummaryResponse(
            sector=actual_sector_name,
            report_month=target_month,
            is_road=is_road,
            transfer_regime=is_road,
            transfer_regime_note=(
                "Onboarded Dec 2025 with expired backlog dates; interpret with caution"
                if is_road
                else None
            ),
            total_projects=len(sec_df),
            total_cost_cr=round(float(sec_df["original_cost_cr"].sum()), 2),
            total_expenditure_cr=round(float(sec_df["cumulative_expenditure_cr"].sum()), 2),
            avg_physical_progress_pct=round(float(sec_df["physical_progress_pct"].mean()), 1),
            avg_risk_score=round(float(sec_df["risk_score"].mean()), 1),
            band_distribution=BandDistribution(
                LOW=int(bands.get("LOW", 0)),
                MEDIUM=int(bands.get("MEDIUM", 0)),
                HIGH=int(bands.get("HIGH", 0)),
                CRITICAL=int(bands.get("CRITICAL", 0)),
            ),
            active_warnings_count=int(sec_df["early_warning"].sum()),
            top_risk_projects=top_projects,
            national_benchmarks=benchmarks,
        )

    def get_ministry_summary(
        self, ministry: str, report_month: str | None = None
    ) -> MinistrySummaryResponse | None:
        """Level-2 Ministry Summary."""
        target_month = report_month or self.latest_month
        m_df = self.df[self.df["report_month"] == target_month]
        min_clean = ministry.strip().lower()
        min_df = m_df[m_df["ministry"].astype(str).str.lower() == min_clean]
        if len(min_df) == 0:
            min_df = m_df[
                m_df["ministry"].astype(str).str.lower().str.contains(min_clean, regex=False)
            ]

        if len(min_df) == 0:
            return None

        actual_ministry_name = min_df["ministry"].iloc[0]
        bands = min_df["risk_band"].value_counts().to_dict()

        # Sectors inside ministry
        sec_items = []
        for sec, s_df in min_df.groupby("sector"):
            sec_items.append(
                MinistrySectorItem(
                    sector=str(sec),
                    total_projects=len(s_df),
                    avg_risk_score=round(float(s_df["risk_score"].mean()), 1),
                    active_warnings=int(s_df["early_warning"].sum()),
                )
            )

        return MinistrySummaryResponse(
            ministry=actual_ministry_name,
            report_month=target_month,
            total_projects=len(min_df),
            total_cost_cr=round(float(min_df["original_cost_cr"].sum()), 2),
            total_expenditure_cr=round(float(min_df["cumulative_expenditure_cr"].sum()), 2),
            avg_risk_score=round(float(min_df["risk_score"].mean()), 1),
            band_distribution=BandDistribution(
                LOW=int(bands.get("LOW", 0)),
                MEDIUM=int(bands.get("MEDIUM", 0)),
                HIGH=int(bands.get("HIGH", 0)),
                CRITICAL=int(bands.get("CRITICAL", 0)),
            ),
            active_warnings_count=int(min_df["early_warning"].sum()),
            sectors=sec_items,
        )

    def get_projects(
        self,
        report_month: str | None = None,
        band: str | None = None,
        sector: str | None = None,
        ministry: str | None = None,
        state: str | None = None,
        early_warning_only: bool = False,
        warning_strength_min: int | None = None,
        data_sufficiency: str | None = None,
        sort_by: str = "risk_score",
        order: str = "desc",
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedProjectsResponse:
        """Filterable and paginated project list."""
        target_month = report_month or self.latest_month
        sub = self.df[self.df["report_month"] == target_month].copy()

        if band:
            sub = sub[sub["risk_band"].astype(str).str.upper() == band.strip().upper()]
        if sector:
            sub = sub[sub["sector"].astype(str).str.lower() == sector.strip().lower()]
        if ministry:
            sub = sub[sub["ministry"].astype(str).str.lower() == ministry.strip().lower()]
        if state:
            sub = sub[sub["state"].astype(str).str.lower() == state.strip().lower()]
        if early_warning_only:
            sub = sub[sub["early_warning"]]
        if warning_strength_min is not None:
            sub = sub[sub["warning_strength"] >= warning_strength_min]
        if data_sufficiency:
            sub = sub[
                sub["data_sufficiency"].astype(str).str.upper() == data_sufficiency.strip().upper()
            ]

        # Sorting
        ascending = order.lower() == "asc"
        valid_sort_cols = [
            "risk_score",
            "project_name",
            "original_cost_cr",
            "physical_progress_pct",
            "warning_strength",
        ]
        sort_col = sort_by if sort_by in valid_sort_cols else "risk_score"
        sub = sub.sort_values(sort_col, ascending=ascending)

        total_records = len(sub)
        page = max(1, page)
        page_size = max(1, min(page_size, 200))
        total_pages = int(np.ceil(total_records / page_size)) if total_records > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_df = sub.iloc[start_idx:end_idx]

        items = [
            ProjectSummaryItem(
                project_id=str(row["project_id"]),
                project_name=str(row["project_name"]),
                ministry=str(row["ministry"]),
                sector=str(row["sector"]),
                state=str(row.get("state", "Multi-State")),
                is_road=bool(row["is_road"]),
                transfer_regime=bool(row["transfer_regime"]),
                data_sufficiency=str(row["data_sufficiency"]),
                risk_score=float(row["risk_score"]),
                risk_band=str(row["risk_band"]),
                calibrated_probability=float(row["calibrated_probability"]),
                early_warning=bool(row["early_warning"]),
                warning_status=str(row["warning_status"]),
                warning_strength=int(row["warning_strength"]),
                triggers_fired=str(row["triggers_fired"]),
                original_cost_cr=float(row["original_cost_cr"]),
                cumulative_expenditure_cr=float(row["cumulative_expenditure_cr"]),
                physical_progress_pct=float(row["physical_progress_pct"]),
            )
            for _, row in page_df.iterrows()
        ]

        return PaginatedProjectsResponse(
            total=total_records,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            report_month=target_month,
            items=items,
        )

    def get_project_detail(self, project_id: str) -> ProjectDetailResponse | None:
        """Level-3 Full Project Dossier."""
        p_history = self.df[self.df["project_id"] == str(project_id).strip()].sort_values(
            "report_month"
        )
        if len(p_history) == 0:
            return None

        # Most recent observed row for current status
        current_row = p_history.iloc[-1]
        is_road = bool(current_row["is_road"])

        current_metrics = ProjectCurrentMetrics(
            report_month=str(current_row["report_month"]),
            risk_score=float(current_row["risk_score"]),
            risk_band=str(current_row["risk_band"]),
            calibrated_probability=float(current_row["calibrated_probability"]),
            raw_probability=float(
                current_row.get("raw_probability", current_row["calibrated_probability"])
            ),
            original_cost_cr=float(current_row["original_cost_cr"]),
            revised_cost_cr=float(
                current_row.get("revised_cost_cr", current_row["original_cost_cr"])
            ),
            cumulative_expenditure_cr=float(current_row["cumulative_expenditure_cr"]),
            exp_utilization=float(current_row.get("exp_utilization", 0.0)),
            physical_progress_pct=float(current_row["physical_progress_pct"]),
            financial_physical_gap=float(current_row.get("financial_physical_gap", 0.0)),
            original_completion_date=(
                str(current_row["original_completion_date"])
                if pd.notna(current_row["original_completion_date"])
                else None
            ),
            revised_completion_date=(
                str(current_row["revised_completion_date"])
                if pd.notna(current_row["revised_completion_date"])
                else None
            ),
            planned_duration_months=(
                float(current_row["planned_duration_months"])
                if pd.notna(current_row.get("planned_duration_months"))
                else None
            ),
            elapsed_duration_months=(
                float(current_row["elapsed_duration_months"])
                if pd.notna(current_row.get("elapsed_duration_months"))
                else None
            ),
            remaining_duration_months=(
                float(current_row["remaining_duration_months"])
                if pd.notna(current_row.get("remaining_duration_months"))
                else None
            ),
            trajectory_anchor_date=(
                str(current_row["trajectory_anchor_date"])
                if pd.notna(current_row.get("trajectory_anchor_date"))
                else None
            ),
        )

        ew_evidence = EarlyWarningEvidence(
            early_warning=bool(current_row["early_warning"]),
            warning_status=str(current_row["warning_status"]),
            warning_strength=int(current_row["warning_strength"]),
            triggers_fired=str(current_row["triggers_fired"]),
            score_rising_fired=bool(current_row.get("score_rising_fired", False)),
            gap_widening_fired=bool(current_row.get("gap_widening_fired", False)),
            velocity_divergence_fired=bool(current_row.get("velocity_divergence_fired", False)),
            risk_score_prev=(
                float(current_row["risk_score_prev"])
                if pd.notna(current_row.get("risk_score_prev"))
                else None
            ),
            risk_score_delta_1m=(
                float(current_row["risk_score_delta_1m"])
                if pd.notna(current_row.get("risk_score_delta_1m"))
                else None
            ),
            risk_score_delta_2m=(
                float(current_row["risk_score_delta_2m"])
                if pd.notna(current_row.get("risk_score_delta_2m"))
                else None
            ),
            gap_delta_1m=(
                float(current_row["gap_delta_1m"])
                if pd.notna(current_row.get("gap_delta_1m"))
                else None
            ),
            gap_delta_2m=(
                float(current_row["gap_delta_2m"])
                if pd.notna(current_row.get("gap_delta_2m"))
                else None
            ),
            progress_velocity_3mo=(
                float(current_row["progress_velocity_3mo"])
                if pd.notna(current_row.get("progress_velocity_3mo"))
                else None
            ),
            exp_velocity_3mo=(
                float(current_row["exp_velocity_3mo"])
                if pd.notna(current_row.get("exp_velocity_3mo"))
                else None
            ),
        )

        history_points = [
            ProjectTrajectoryPoint(
                report_month=str(row["report_month"]),
                risk_score=float(row["risk_score"]),
                risk_band=str(row["risk_band"]),
                calibrated_probability=float(row["calibrated_probability"]),
                physical_progress_pct=float(row["physical_progress_pct"]),
                cumulative_expenditure_cr=float(row["cumulative_expenditure_cr"]),
                financial_physical_gap=float(row.get("financial_physical_gap", 0.0)),
                early_warning=bool(row["early_warning"]),
                warning_status=str(row["warning_status"]),
                warning_strength=int(row["warning_strength"]),
                triggers_fired=str(row["triggers_fired"]),
            )
            for _, row in p_history.iterrows()
        ]

        return ProjectDetailResponse(
            project_id=str(current_row["project_id"]),
            project_code=str(current_row.get("project_code", current_row["project_id"])),
            project_name=str(current_row["project_name"]),
            implementing_agency=str(current_row.get("implementing_agency", "N/A")),
            ministry=str(current_row["ministry"]),
            sector=str(current_row["sector"]),
            state=str(current_row.get("state", "Multi-State")),
            is_road=is_road,
            transfer_regime=is_road,
            transfer_regime_note=(
                "Onboarded Dec 2025 with expired backlog dates; interpret with caution"
                if is_road
                else None
            ),
            data_sufficiency=str(current_row["data_sufficiency"]),
            observed_months_to_date=int(current_row["observed_months_to_date"]),
            current_metrics=current_metrics,
            early_warning=ew_evidence,
            history=history_points,
        )

    def get_watchlist(
        self,
        report_month: str | None = None,
        sector: str | None = None,
        ministry: str | None = None,
        min_strength: int = 1,
    ) -> WatchlistResponse:
        """Watchlist of deteriorating projects (early_warning == True)."""
        target_month = report_month or self.latest_month
        m_df = self.df[self.df["report_month"] == target_month]

        # Filter strictly to active warnings
        w_df = m_df[m_df["early_warning"] & (m_df["warning_strength"] >= min_strength)].copy()

        if sector:
            w_df = w_df[w_df["sector"].astype(str).str.lower() == sector.strip().lower()]
        if ministry:
            w_df = w_df[w_df["ministry"].astype(str).str.lower() == ministry.strip().lower()]

        # Sorted by warning_strength desc, then risk_score desc
        w_df = w_df.sort_values(["warning_strength", "risk_score"], ascending=[False, False])

        items = [
            WatchlistItem(
                project_id=str(row["project_id"]),
                project_name=str(row["project_name"]),
                ministry=str(row["ministry"]),
                sector=str(row["sector"]),
                is_road=bool(row["is_road"]),
                transfer_regime=bool(row["transfer_regime"]),
                data_sufficiency=str(row["data_sufficiency"]),
                risk_score=float(row["risk_score"]),
                risk_band=str(row["risk_band"]),
                warning_strength=int(row["warning_strength"]),
                triggers_fired=str(row["triggers_fired"]),
                score_delta_1m=(
                    float(row["risk_score_delta_1m"])
                    if pd.notna(row.get("risk_score_delta_1m"))
                    else None
                ),
                score_delta_2m=(
                    float(row["risk_score_delta_2m"])
                    if pd.notna(row.get("risk_score_delta_2m"))
                    else None
                ),
                gap_delta_1m=(
                    float(row["gap_delta_1m"]) if pd.notna(row.get("gap_delta_1m")) else None
                ),
                progress_velocity_3mo=(
                    float(row["progress_velocity_3mo"])
                    if pd.notna(row.get("progress_velocity_3mo"))
                    else None
                ),
                exp_velocity_3mo=(
                    float(row["exp_velocity_3mo"])
                    if pd.notna(row.get("exp_velocity_3mo"))
                    else None
                ),
                physical_progress_pct=float(row["physical_progress_pct"]),
            )
            for _, row in w_df.iterrows()
        ]

        nr_cnt = int((~w_df["is_road"]).sum()) if len(w_df) > 0 else 0
        roads_cnt = int(w_df["is_road"].sum()) if len(w_df) > 0 else 0

        return WatchlistResponse(
            report_month=target_month,
            total_active_warnings=len(items),
            non_roads_count=nr_cnt,
            roads_count=roads_cnt,
            items=items,
        )


repository = DataRepository()

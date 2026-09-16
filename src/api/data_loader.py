"""Read-only data repository and query engine for FastAPI serving layer (STEP_13).

Strictly reads precomputed tables (panel.parquet, features.parquet, risk_scores.parquet,
early_warning.parquet). Does NOT run ML models or pipeline mutations at request time.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.common.config import DATA_PROCESSED

log = logging.getLogger(__name__)


class DataLoader:
    """Singleton repository managing precomputed project and risk datasets."""

    _instance: DataLoader | None = None

    def __init__(self, data_dir: Path | str = DATA_PROCESSED):
        self.data_dir = Path(data_dir)
        self._df: pd.DataFrame | None = None
        self._panel_df: pd.DataFrame | None = None
        self._features_df: pd.DataFrame | None = None
        self._risk_df: pd.DataFrame | None = None
        self._ew_df: pd.DataFrame | None = None
        self._is_loaded = False
        self._last_loaded_at: datetime | None = None

    @classmethod
    def get_instance(cls, data_dir: Path | str = DATA_PROCESSED) -> DataLoader:
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = DataLoader(data_dir=data_dir)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (useful for test isolation)."""
        cls._instance = None

    def load_data(self, force_reload: bool = False) -> bool:
        """Load and merge precomputed processed parquet tables into memory."""
        if self._is_loaded and not force_reload:
            return True

        panel_path = self.data_dir / "panel.parquet"
        features_path = self.data_dir / "features.parquet"
        risk_path = self.data_dir / "risk_scores.parquet"
        ew_path = self.data_dir / "early_warning.parquet"

        if not (panel_path.exists() and risk_path.exists() and ew_path.exists()):
            log.warning("Required processed parquet files not found in %s", self.data_dir)
            self._is_loaded = False
            return False

        try:
            self._panel_df = pd.read_parquet(panel_path)
            self._risk_df = pd.read_parquet(risk_path)
            self._ew_df = pd.read_parquet(ew_path)
            if features_path.exists():
                self._features_df = pd.read_parquet(features_path)
            else:
                self._features_df = pd.DataFrame()

            # Merge into unified lookup table
            # Base keys: project_id, report_month
            self._panel_df["project_id"] = self._panel_df["project_id"].astype(str)
            self._risk_df["project_id"] = self._risk_df["project_id"].astype(str)
            self._ew_df["project_id"] = self._ew_df["project_id"].astype(str)

            # Deduplicate columns before merge
            ew_cols = [
                c
                for c in self._ew_df.columns
                if c
                not in [
                    "sector",
                    "is_road",
                    "data_sufficiency",
                    "risk_score",
                    "risk_band",
                    "financial_physical_gap",
                    "progress_velocity_3mo",
                    "exp_velocity_3mo",
                ]
            ]
            merged = self._panel_df.merge(
                self._risk_df[
                    [
                        c
                        for c in self._risk_df.columns
                        if c not in ["project_name", "sector", "ministry", "implementing_agency"]
                    ]
                ],
                on=["project_id", "report_month"],
                how="left",
            )
            merged = merged.merge(
                self._ew_df[ew_cols],
                on=["project_id", "report_month"],
                how="left",
            )

            if not self._features_df.empty:
                self._features_df["project_id"] = self._features_df["project_id"].astype(str)
                feat_cols_to_add = [
                    c
                    for c in self._features_df.columns
                    if c not in merged.columns
                    and c not in ["sector", "ministry", "project_size_band"]
                ] + ["project_id", "report_month"]
                merged = merged.merge(
                    self._features_df[feat_cols_to_add],
                    on=["project_id", "report_month"],
                    how="left",
                )

            # Fill defaults for missing risk/warning indicators if any
            merged["risk_score"] = merged["risk_score"].fillna(0.0).astype(float)
            merged["risk_band"] = merged["risk_band"].fillna("PROVISIONAL").astype(str)
            merged["data_sufficiency"] = (
                merged["data_sufficiency"].fillna("PROVISIONAL").astype(str)
            )
            merged["early_warning"] = merged["early_warning"].fillna(False).astype(bool)
            merged["warning_status"] = (
                merged["warning_status"].fillna("INSUFFICIENT_HISTORY").astype(str)
            )
            merged["warning_strength"] = merged["warning_strength"].fillna(0).astype(int)
            merged["triggers_fired"] = merged["triggers_fired"].fillna("none").astype(str)

            # Cost and escalation defaults
            if "cost_escalation_amt" not in merged.columns:
                merged["cost_escalation_amt"] = (
                    merged["revised_cost_cr"] - merged["original_cost_cr"]
                ).clip(lower=0)
            if "cost_escalation_pct" not in merged.columns:
                orig = merged["original_cost_cr"].replace(0, np.nan)
                merged["cost_escalation_pct"] = np.round(
                    (merged["cost_escalation_amt"] / orig) * 100.0, 2
                ).fillna(0.0)

            if "financial_physical_gap" not in merged.columns:
                exp_util = (
                    merged["cumulative_expenditure_cr"]
                    / merged["revised_cost_cr"].replace(0, np.nan)
                ).fillna(0.0)
                merged["financial_physical_gap"] = np.round(
                    (exp_util * 100.0) - merged["physical_progress_pct"], 2
                )

            # Ensure clean string types for grouping
            merged["sector"] = merged["sector"].fillna("Unclassified").astype(str)
            merged["ministry"] = merged["ministry"].fillna("Unclassified").astype(str)
            merged["project_name"] = merged["project_name"].fillna("Unnamed Project").astype(str)

            self._df = merged
            self._is_loaded = True
            self._last_loaded_at = datetime.now(UTC)
            log.info(
                "DataLoader successfully loaded %d unified project-month records", len(self._df)
            )
            return True
        except Exception as e:
            log.error("Failed to load data into DataLoader: %s", e, exc_info=True)
            self._is_loaded = False
            return False

    def set_mock_data(self, df: pd.DataFrame) -> None:
        """Explicitly set unified dataframe (for testing/mocking)."""
        self._df = df.copy()
        self._is_loaded = True
        self._last_loaded_at = datetime.now(UTC)

    @property
    def df(self) -> pd.DataFrame:
        """Get active unified dataframe."""
        if not self._is_loaded or self._df is None:
            self.load_data()
        if self._df is None or self._df.empty:
            return pd.DataFrame()
        return self._df

    def get_pipeline_stages_info(self) -> list[dict[str, Any]]:
        """Return information about existing pipeline parquet files."""
        stages = [
            ("panel", self.data_dir / "panel.parquet"),
            ("features", self.data_dir / "features.parquet"),
            ("labels", self.data_dir / "labels.parquet"),
            ("risk_scores", self.data_dir / "risk_scores.parquet"),
            ("early_warning", self.data_dir / "early_warning.parquet"),
        ]
        res = []
        for name, p in stages:
            exists = p.exists()
            rows = None
            if exists:
                try:
                    df_stage = pd.read_parquet(p)
                    rows = len(df_stage)
                except Exception:
                    pass
            res.append(
                {
                    "name": name,
                    "path": str(p),
                    "exists": exists,
                    "rows": rows,
                }
            )
        return res

    def get_available_months(self) -> list[str]:
        """Return sorted unique report months."""
        if self.df.empty or "report_month" not in self.df.columns:
            return []
        return sorted([str(m) for m in self.df["report_month"].dropna().unique()])

    def get_latest_month(self) -> str:
        """Get latest available report month (e.g., '2026-07')."""
        months = self.get_available_months()
        return months[-1] if months else "2026-07"

    def get_month_df(
        self, report_month: str | None = None, exclude_roads: bool = False
    ) -> pd.DataFrame:
        """Filter dataset for a given report month and optional road exclusion."""
        if self.df.empty:
            return pd.DataFrame()
        month = report_month or self.get_latest_month()
        sub = self.df[self.df["report_month"] == month]
        if exclude_roads and "sector" in sub.columns:
            sub = sub[~sub["sector"].str.lower().str.contains("road")]
        return sub

    def get_national_summary(
        self,
        report_month: str | None = None,
        exclude_roads: bool = False,
    ) -> dict[str, Any] | None:
        """Compute Level-1 National Portfolio Overview."""
        sub = self.get_month_df(report_month=report_month, exclude_roads=exclude_roads)
        if sub.empty:
            return None

        actual_month = report_month or self.get_latest_month()
        total_projects = len(sub)
        orig_cost = float(sub["original_cost_cr"].sum())
        rev_cost = float(sub["revised_cost_cr"].sum())
        cum_exp = float(sub["cumulative_expenditure_cr"].sum())
        cost_esc = float(sub["cost_escalation_amt"].sum())
        cost_esc_pct = round((cost_esc / orig_cost * 100.0), 2) if orig_cost > 0 else 0.0

        avg_phys_prog = round(float(sub["physical_progress_pct"].mean()), 2)
        avg_gap = round(float(sub["financial_physical_gap"].mean()), 2)
        avg_risk = round(float(sub["risk_score"].mean()), 2)

        # Risk band distribution
        bands_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "PROVISIONAL"]
        band_counts = sub["risk_band"].value_counts().to_dict()
        risk_bands = []
        for b in bands_order:
            cnt = int(band_counts.get(b, 0))
            pct = round((cnt / total_projects * 100.0), 2) if total_projects > 0 else 0.0
            risk_bands.append({"band": b, "count": cnt, "percentage": pct})

        # Early warning metrics
        ew_active = sub[sub["early_warning"]]
        active_cnt = len(ew_active)
        active_rate = round((active_cnt / total_projects * 100.0), 2) if total_projects > 0 else 0.0

        score_rising_cnt = int((sub.get("score_rising_fired", pd.Series(0))).sum())
        gap_widening_cnt = int((sub.get("gap_widening_fired", pd.Series(0))).sum())
        vel_div_cnt = int((sub.get("velocity_divergence_fired", pd.Series(0))).sum())

        str_counts = sub["warning_strength"].value_counts().to_dict()

        early_warnings = {
            "active_warnings_count": active_cnt,
            "active_warning_rate_pct": active_rate,
            "score_rising_count": score_rising_cnt,
            "gap_widening_count": gap_widening_cnt,
            "velocity_divergence_count": vel_div_cnt,
            "strength_1_count": int(str_counts.get(1, 0)),
            "strength_2_count": int(str_counts.get(2, 0)),
            "strength_3_count": int(str_counts.get(3, 0)),
        }

        # Sector breakdown
        sectors = self.list_sectors(report_month=actual_month, exclude_roads=exclude_roads)

        # Top 10 high risk projects
        top_risk_df = sub.sort_values(
            by=["risk_score", "cost_escalation_amt"], ascending=[False, False]
        ).head(10)
        top_risk_projects = [self._row_to_quick_summary(r) for _, r in top_risk_df.iterrows()]

        return {
            "report_month": actual_month,
            "total_projects": total_projects,
            "total_original_cost_cr": round(orig_cost, 2),
            "total_revised_cost_cr": round(rev_cost, 2),
            "total_expenditure_cr": round(cum_exp, 2),
            "total_cost_escalation_cr": round(cost_esc, 2),
            "portfolio_cost_escalation_pct": cost_esc_pct,
            "avg_physical_progress_pct": avg_phys_prog,
            "avg_financial_physical_gap": avg_gap,
            "avg_risk_score": avg_risk,
            "risk_bands": risk_bands,
            "early_warnings": early_warnings,
            "sectors": sectors,
            "top_risk_projects": top_risk_projects,
        }

    def list_sectors(
        self,
        report_month: str | None = None,
        exclude_roads: bool = False,
    ) -> list[dict[str, Any]]:
        """List summary metrics for all sectors."""
        sub = self.get_month_df(report_month=report_month, exclude_roads=exclude_roads)
        if sub.empty:
            return []

        res = []
        for sector_name, grp in sub.groupby("sector"):
            tot_p = len(grp)
            orig = float(grp["original_cost_cr"].sum())
            rev = float(grp["revised_cost_cr"].sum())
            esc = float(grp["cost_escalation_amt"].sum())
            esc_pct = round((esc / orig * 100.0), 2) if orig > 0 else 0.0
            avg_p = round(float(grp["physical_progress_pct"].mean()), 2)
            avg_r = round(float(grp["risk_score"].mean()), 2)
            crit = int((grp["risk_band"] == "CRITICAL").sum())
            high = int((grp["risk_band"] == "HIGH").sum())
            ew = int(grp["early_warning"].sum())

            res.append(
                {
                    "sector": str(sector_name),
                    "total_projects": tot_p,
                    "total_original_cost_cr": round(orig, 2),
                    "total_revised_cost_cr": round(rev, 2),
                    "total_cost_escalation_cr": round(esc, 2),
                    "avg_cost_escalation_pct": esc_pct,
                    "avg_physical_progress_pct": avg_p,
                    "avg_risk_score": avg_r,
                    "critical_risk_count": crit,
                    "high_risk_count": high,
                    "active_warnings_count": ew,
                }
            )
        return sorted(res, key=lambda x: x["total_projects"], reverse=True)

    def get_sector_detail(
        self,
        sector: str,
        report_month: str | None = None,
    ) -> dict[str, Any] | None:
        """Get Level-2 Sector Detail."""
        sub = self.get_month_df(report_month=report_month)
        if sub.empty:
            return None

        # Case-insensitive match on sector
        matched = sub[sub["sector"].str.strip().str.lower() == sector.strip().lower()]
        if matched.empty:
            return None

        actual_sector = str(matched["sector"].iloc[0])
        actual_month = report_month or self.get_latest_month()

        total_projects = len(matched)
        orig_cost = float(matched["original_cost_cr"].sum())
        rev_cost = float(matched["revised_cost_cr"].sum())
        cum_exp = float(matched["cumulative_expenditure_cr"].sum())
        cost_esc = float(matched["cost_escalation_amt"].sum())
        cost_esc_pct = round((cost_esc / orig_cost * 100.0), 2) if orig_cost > 0 else 0.0
        avg_phys = round(float(matched["physical_progress_pct"].mean()), 2)
        avg_gap = round(float(matched["financial_physical_gap"].mean()), 2)
        avg_risk = round(float(matched["risk_score"].mean()), 2)

        # Risk bands
        bands_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "PROVISIONAL"]
        band_counts = matched["risk_band"].value_counts().to_dict()
        risk_bands = []
        for b in bands_order:
            cnt = int(band_counts.get(b, 0))
            pct = round((cnt / total_projects * 100.0), 2) if total_projects > 0 else 0.0
            risk_bands.append({"band": b, "count": cnt, "percentage": pct})

        # Early warnings
        ew_active = matched[matched["early_warning"]]
        active_cnt = len(ew_active)
        active_rate = round((active_cnt / total_projects * 100.0), 2) if total_projects > 0 else 0.0
        str_counts = matched["warning_strength"].value_counts().to_dict()

        early_warnings = {
            "active_warnings_count": active_cnt,
            "active_warning_rate_pct": active_rate,
            "score_rising_count": int((matched.get("score_rising_fired", pd.Series(0))).sum()),
            "gap_widening_count": int((matched.get("gap_widening_fired", pd.Series(0))).sum()),
            "velocity_divergence_count": int(
                (matched.get("velocity_divergence_fired", pd.Series(0))).sum()
            ),
            "strength_1_count": int(str_counts.get(1, 0)),
            "strength_2_count": int(str_counts.get(2, 0)),
            "strength_3_count": int(str_counts.get(3, 0)),
        }

        # Ministries breakdown within sector
        ministries = []
        for min_name, grp in matched.groupby("ministry"):
            m_orig = float(grp["original_cost_cr"].sum())
            m_rev = float(grp["revised_cost_cr"].sum())
            m_esc = float(grp["cost_escalation_amt"].sum())
            m_esc_pct = round((m_esc / m_orig * 100.0), 2) if m_orig > 0 else 0.0
            ministries.append(
                {
                    "ministry": str(min_name),
                    "total_projects": len(grp),
                    "total_original_cost_cr": round(m_orig, 2),
                    "total_revised_cost_cr": round(m_rev, 2),
                    "total_cost_escalation_cr": round(m_esc, 2),
                    "avg_cost_escalation_pct": m_esc_pct,
                    "avg_physical_progress_pct": round(
                        float(grp["physical_progress_pct"].mean()), 2
                    ),
                    "avg_risk_score": round(float(grp["risk_score"].mean()), 2),
                    "critical_risk_count": int((grp["risk_band"] == "CRITICAL").sum()),
                    "high_risk_count": int((grp["risk_band"] == "HIGH").sum()),
                    "active_warnings_count": int(grp["early_warning"].sum()),
                }
            )

        # Project list sorted by risk score desc
        sorted_projects = matched.sort_values(
            by=["risk_score", "revised_cost_cr"], ascending=[False, False]
        )
        project_items = [self._row_to_quick_summary(r) for _, r in sorted_projects.iterrows()]

        return {
            "sector": actual_sector,
            "report_month": actual_month,
            "total_projects": total_projects,
            "total_original_cost_cr": round(orig_cost, 2),
            "total_revised_cost_cr": round(rev_cost, 2),
            "total_expenditure_cr": round(cum_exp, 2),
            "total_cost_escalation_cr": round(cost_esc, 2),
            "avg_cost_escalation_pct": cost_esc_pct,
            "avg_physical_progress_pct": avg_phys,
            "avg_financial_physical_gap": avg_gap,
            "avg_risk_score": avg_risk,
            "risk_bands": risk_bands,
            "early_warnings": early_warnings,
            "ministries": sorted(ministries, key=lambda x: x["total_projects"], reverse=True),
            "projects": project_items,
        }

    def list_ministries(self, report_month: str | None = None) -> list[dict[str, Any]]:
        """List summary metrics for all ministries."""
        sub = self.get_month_df(report_month=report_month)
        if sub.empty:
            return []

        res = []
        for min_name, grp in sub.groupby("ministry"):
            tot_p = len(grp)
            orig = float(grp["original_cost_cr"].sum())
            rev = float(grp["revised_cost_cr"].sum())
            esc = float(grp["cost_escalation_amt"].sum())
            esc_pct = round((esc / orig * 100.0), 2) if orig > 0 else 0.0
            avg_p = round(float(grp["physical_progress_pct"].mean()), 2)
            avg_r = round(float(grp["risk_score"].mean()), 2)
            crit = int((grp["risk_band"] == "CRITICAL").sum())
            high = int((grp["risk_band"] == "HIGH").sum())
            ew = int(grp["early_warning"].sum())

            res.append(
                {
                    "ministry": str(min_name),
                    "total_projects": tot_p,
                    "total_original_cost_cr": round(orig, 2),
                    "total_revised_cost_cr": round(rev, 2),
                    "total_cost_escalation_cr": round(esc, 2),
                    "avg_cost_escalation_pct": esc_pct,
                    "avg_physical_progress_pct": avg_p,
                    "avg_risk_score": avg_r,
                    "critical_risk_count": crit,
                    "high_risk_count": high,
                    "active_warnings_count": ew,
                }
            )
        return sorted(res, key=lambda x: x["total_projects"], reverse=True)

    def get_ministry_detail(
        self,
        ministry: str,
        report_month: str | None = None,
    ) -> dict[str, Any] | None:
        """Get Level-2 Ministry Detail."""
        sub = self.get_month_df(report_month=report_month)
        if sub.empty:
            return None

        # Case-insensitive match
        matched = sub[sub["ministry"].str.strip().str.lower() == ministry.strip().lower()]
        if matched.empty:
            return None

        actual_min = str(matched["ministry"].iloc[0])
        actual_month = report_month or self.get_latest_month()

        total_projects = len(matched)
        orig_cost = float(matched["original_cost_cr"].sum())
        rev_cost = float(matched["revised_cost_cr"].sum())
        cum_exp = float(matched["cumulative_expenditure_cr"].sum())
        cost_esc = float(matched["cost_escalation_amt"].sum())
        cost_esc_pct = round((cost_esc / orig_cost * 100.0), 2) if orig_cost > 0 else 0.0
        avg_phys = round(float(matched["physical_progress_pct"].mean()), 2)
        avg_gap = round(float(matched["financial_physical_gap"].mean()), 2)
        avg_risk = round(float(matched["risk_score"].mean()), 2)

        # Risk bands
        bands_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "PROVISIONAL"]
        band_counts = matched["risk_band"].value_counts().to_dict()
        risk_bands = []
        for b in bands_order:
            cnt = int(band_counts.get(b, 0))
            pct = round((cnt / total_projects * 100.0), 2) if total_projects > 0 else 0.0
            risk_bands.append({"band": b, "count": cnt, "percentage": pct})

        # Early warnings
        ew_active = matched[matched["early_warning"]]
        active_cnt = len(ew_active)
        active_rate = round((active_cnt / total_projects * 100.0), 2) if total_projects > 0 else 0.0
        str_counts = matched["warning_strength"].value_counts().to_dict()

        early_warnings = {
            "active_warnings_count": active_cnt,
            "active_warning_rate_pct": active_rate,
            "score_rising_count": int((matched.get("score_rising_fired", pd.Series(0))).sum()),
            "gap_widening_count": int((matched.get("gap_widening_fired", pd.Series(0))).sum()),
            "velocity_divergence_count": int(
                (matched.get("velocity_divergence_fired", pd.Series(0))).sum()
            ),
            "strength_1_count": int(str_counts.get(1, 0)),
            "strength_2_count": int(str_counts.get(2, 0)),
            "strength_3_count": int(str_counts.get(3, 0)),
        }

        # Sector breakdown inside this ministry
        sectors = []
        for sec_name, grp in matched.groupby("sector"):
            s_orig = float(grp["original_cost_cr"].sum())
            s_rev = float(grp["revised_cost_cr"].sum())
            s_esc = float(grp["cost_escalation_amt"].sum())
            s_esc_pct = round((s_esc / s_orig * 100.0), 2) if s_orig > 0 else 0.0
            sectors.append(
                {
                    "sector": str(sec_name),
                    "total_projects": len(grp),
                    "total_original_cost_cr": round(s_orig, 2),
                    "total_revised_cost_cr": round(s_rev, 2),
                    "total_cost_escalation_cr": round(s_esc, 2),
                    "avg_cost_escalation_pct": s_esc_pct,
                    "avg_physical_progress_pct": round(
                        float(grp["physical_progress_pct"].mean()), 2
                    ),
                    "avg_risk_score": round(float(grp["risk_score"].mean()), 2),
                    "critical_risk_count": int((grp["risk_band"] == "CRITICAL").sum()),
                    "high_risk_count": int((grp["risk_band"] == "HIGH").sum()),
                    "active_warnings_count": int(grp["early_warning"].sum()),
                }
            )

        # Project list sorted by risk score desc
        sorted_projects = matched.sort_values(
            by=["risk_score", "revised_cost_cr"], ascending=[False, False]
        )
        project_items = [self._row_to_quick_summary(r) for _, r in sorted_projects.iterrows()]

        return {
            "ministry": actual_min,
            "report_month": actual_month,
            "total_projects": total_projects,
            "total_original_cost_cr": round(orig_cost, 2),
            "total_revised_cost_cr": round(rev_cost, 2),
            "total_expenditure_cr": round(cum_exp, 2),
            "total_cost_escalation_cr": round(cost_esc, 2),
            "avg_cost_escalation_pct": cost_esc_pct,
            "avg_physical_progress_pct": avg_phys,
            "avg_financial_physical_gap": avg_gap,
            "avg_risk_score": avg_risk,
            "risk_bands": risk_bands,
            "early_warnings": early_warnings,
            "sectors": sorted(sectors, key=lambda x: x["total_projects"], reverse=True),
            "projects": project_items,
        }

    def get_project_detail(
        self,
        project_id: str,
        report_month: str | None = None,
    ) -> dict[str, Any] | None:
        """Get Level-3 Project Detail with latest snapshot, drivers, and full trajectory."""
        if self.df.empty:
            return None

        # Filter by project_id
        p_df = self.df[self.df["project_id"].astype(str) == str(project_id).strip()]
        if p_df.empty:
            return None

        # Sort chronologically by report_month
        p_df = p_df.sort_values("report_month")

        # Snapshot row
        target_month = report_month or self.get_latest_month()
        month_rows = p_df[p_df["report_month"] == target_month]
        if not month_rows.empty:
            row = month_rows.iloc[-1]
        else:
            row = p_df.iloc[-1]  # fallback to most recent observed month for this project

        # State handling (convert list or str)
        raw_state = row.get("state", [])
        if isinstance(raw_state, list):
            state_list = [str(s) for s in raw_state]
        elif pd.notna(raw_state) and str(raw_state) != "":
            state_list = [s.strip() for s in str(raw_state).split(",") if s.strip()]
        else:
            state_list = []

        # Drivers
        drivers = self._compute_project_risk_drivers(row)

        # Trajectory
        trajectory = []
        for _, t_row in p_df.iterrows():
            trajectory.append(
                {
                    "report_month": str(t_row["report_month"]),
                    "risk_score": round(float(t_row.get("risk_score", 0.0)), 2),
                    "risk_band": str(t_row.get("risk_band", "PROVISIONAL")),
                    "physical_progress_pct": round(
                        float(t_row.get("physical_progress_pct", 0.0)), 2
                    ),
                    "cumulative_expenditure_cr": round(
                        float(t_row.get("cumulative_expenditure_cr", 0.0)), 2
                    ),
                    "exp_utilization": (
                        round(float(t_row.get("exp_utilization", 0.0)), 3)
                        if pd.notna(t_row.get("exp_utilization"))
                        else 0.0
                    ),
                    "financial_physical_gap": round(
                        float(t_row.get("financial_physical_gap", 0.0)), 2
                    ),
                    "progress_velocity_3mo": (
                        round(float(t_row.get("progress_velocity_3mo", 0.0)), 2)
                        if pd.notna(t_row.get("progress_velocity_3mo"))
                        else 0.0
                    ),
                    "exp_velocity_3mo": (
                        round(float(t_row.get("exp_velocity_3mo", 0.0)), 2)
                        if pd.notna(t_row.get("exp_velocity_3mo"))
                        else 0.0
                    ),
                    "early_warning": bool(t_row.get("early_warning", False)),
                    "warning_status": str(t_row.get("warning_status", "INSUFFICIENT_HISTORY")),
                    "triggers_fired": str(t_row.get("triggers_fired", "none")),
                }
            )

        # Format dates nicely
        def _fmt_date(val: Any) -> str | None:
            if pd.isna(val) or val is None or str(val).strip() in ["", "NaT", "nan", "None"]:
                return None
            return str(val)[:10]

        return {
            "project_id": str(row["project_id"]),
            "project_name": str(row["project_name"]),
            "implementing_agency": (
                str(row["implementing_agency"])
                if pd.notna(row.get("implementing_agency"))
                else None
            ),
            "ministry": str(row["ministry"]),
            "sector": str(row["sector"]),
            "state": state_list,
            "project_size_band": str(row.get("project_size_band", "Major")),
            "project_status": str(row.get("project_status", "Ongoing")),
            "date_of_approval": _fmt_date(row.get("date_of_approval")),
            "start_date": _fmt_date(row.get("start_date")),
            "original_completion_date": _fmt_date(row.get("original_completion_date")),
            "revised_completion_date": _fmt_date(row.get("revised_completion_date")),
            "actual_completion_date": _fmt_date(row.get("actual_completion_date")),
            "report_month": str(row["report_month"]),
            "original_cost_cr": round(float(row.get("original_cost_cr", 0.0)), 2),
            "revised_cost_cr": round(float(row.get("revised_cost_cr", 0.0)), 2),
            "cumulative_expenditure_cr": round(float(row.get("cumulative_expenditure_cr", 0.0)), 2),
            "cost_escalation_amt_cr": round(float(row.get("cost_escalation_amt", 0.0)), 2),
            "cost_escalation_pct": round(float(row.get("cost_escalation_pct", 0.0)), 2),
            "physical_progress_pct": round(float(row.get("physical_progress_pct", 0.0)), 2),
            "financial_physical_gap": round(float(row.get("financial_physical_gap", 0.0)), 2),
            "schedule_variance_months": (
                round(float(row.get("schedule_variance_months", 0.0)), 1)
                if pd.notna(row.get("schedule_variance_months"))
                else 0.0
            ),
            "planned_duration_months": (
                round(float(row.get("planned_duration_months", 0.0)), 1)
                if pd.notna(row.get("planned_duration_months"))
                else 0.0
            ),
            "elapsed_duration_months": (
                round(float(row.get("elapsed_duration_months", 0.0)), 1)
                if pd.notna(row.get("elapsed_duration_months"))
                else 0.0
            ),
            "remaining_duration_months": (
                round(float(row.get("remaining_duration_months", 0.0)), 1)
                if pd.notna(row.get("remaining_duration_months"))
                else 0.0
            ),
            "risk_score": round(float(row.get("risk_score", 0.0)), 2),
            "risk_band": str(row.get("risk_band", "PROVISIONAL")),
            "data_sufficiency": str(row.get("data_sufficiency", "PROVISIONAL")),
            "early_warning": bool(row.get("early_warning", False)),
            "warning_status": str(row.get("warning_status", "INSUFFICIENT_HISTORY")),
            "warning_strength": int(row.get("warning_strength", 0)),
            "triggers_fired": str(row.get("triggers_fired", "none")),
            "risk_score_prev": (
                round(float(row["risk_score_prev"]), 2)
                if pd.notna(row.get("risk_score_prev"))
                else None
            ),
            "risk_score_delta_1m": (
                round(float(row["risk_score_delta_1m"]), 2)
                if pd.notna(row.get("risk_score_delta_1m"))
                else None
            ),
            "risk_score_delta_2m": (
                round(float(row["risk_score_delta_2m"]), 2)
                if pd.notna(row.get("risk_score_delta_2m"))
                else None
            ),
            "gap_delta_1m": (
                round(float(row["gap_delta_1m"]), 2) if pd.notna(row.get("gap_delta_1m")) else None
            ),
            "gap_delta_2m": (
                round(float(row["gap_delta_2m"]), 2) if pd.notna(row.get("gap_delta_2m")) else None
            ),
            "top_risk_drivers": drivers,
            "trajectory": trajectory,
        }

    def _compute_project_risk_drivers(self, row: pd.Series) -> list[dict[str, Any]]:
        """Extract top explanatory risk driver factors for a project snapshot."""
        drivers = []

        # 1. Financial Physical Gap
        gap = float(row.get("financial_physical_gap", 0.0))
        if gap > 20.0:
            drivers.append(
                {
                    "factor_name": "financial_physical_gap",
                    "display_name": "Severe Financial-Physical Divergence",
                    "value": f"+{gap:.1f}%",
                    "benchmark": "< 10.0%",
                    "severity": "HIGH",
                    "explanation": f"Expenditure utilization exceeds physical progress by {gap:.1f}%, signaling capital burn ahead of works.",
                }
            )
        elif gap > 10.0:
            drivers.append(
                {
                    "factor_name": "financial_physical_gap",
                    "display_name": "Moderate Financial-Physical Gap",
                    "value": f"+{gap:.1f}%",
                    "benchmark": "< 10.0%",
                    "severity": "MEDIUM",
                    "explanation": f"Expenditure lead is {gap:.1f}% higher than physical milestone execution.",
                }
            )

        # 2. Schedule Variance / Delay
        sched_var = (
            float(row.get("schedule_variance_months", 0.0))
            if pd.notna(row.get("schedule_variance_months"))
            else 0.0
        )
        if sched_var > 24.0:
            drivers.append(
                {
                    "factor_name": "schedule_variance_months",
                    "display_name": "Substantial Milestone Delay",
                    "value": f"{sched_var:.0f} months",
                    "benchmark": "0 months",
                    "severity": "HIGH",
                    "explanation": f"Completion target has slipped by {sched_var:.0f} months over baseline schedule.",
                }
            )
        elif sched_var > 6.0:
            drivers.append(
                {
                    "factor_name": "schedule_variance_months",
                    "display_name": "Schedule Extension",
                    "value": f"{sched_var:.0f} months",
                    "benchmark": "0 months",
                    "severity": "MEDIUM",
                    "explanation": f"Target deadline deferred by {sched_var:.0f} months.",
                }
            )

        # 3. Cost Escalation
        esc_pct = float(row.get("cost_escalation_pct", 0.0))
        if esc_pct > 30.0:
            drivers.append(
                {
                    "factor_name": "cost_escalation_pct",
                    "display_name": "Heavy Cost Overrun",
                    "value": f"+{esc_pct:.1f}%",
                    "benchmark": "< 10.0%",
                    "severity": "HIGH",
                    "explanation": f"Revised cost exceeds original sanction by {esc_pct:.1f}%.",
                }
            )
        elif esc_pct > 10.0:
            drivers.append(
                {
                    "factor_name": "cost_escalation_pct",
                    "display_name": "Cost Escalation",
                    "value": f"+{esc_pct:.1f}%",
                    "benchmark": "< 10.0%",
                    "severity": "MEDIUM",
                    "explanation": f"Sanction cost escalated by {esc_pct:.1f}%.",
                }
            )

        # 4. Progress Velocity / Stagnation
        p_vel = (
            float(row.get("progress_velocity_3mo", 0.0))
            if pd.notna(row.get("progress_velocity_3mo"))
            else 0.0
        )
        if p_vel <= 0.2 and float(row.get("physical_progress_pct", 0.0)) < 95.0:
            drivers.append(
                {
                    "factor_name": "progress_velocity_3mo",
                    "display_name": "Stagnant Physical Execution",
                    "value": f"{p_vel:.2f}% / month",
                    "benchmark": "> 1.5% / month",
                    "severity": "HIGH",
                    "explanation": "Physical work completion has ground to a standstill over recent 3-month window.",
                }
            )

        # 5. Early Warning Trend
        if bool(row.get("early_warning", False)):
            triggers = str(row.get("triggers_fired", ""))
            drivers.append(
                {
                    "factor_name": "early_warning_triggers",
                    "display_name": "Active Deterioration Trend",
                    "value": triggers,
                    "benchmark": "none",
                    "severity": "HIGH",
                    "explanation": f"Early warning engine flagged multi-month worsening trend: {triggers}.",
                }
            )

        if not drivers:
            drivers.append(
                {
                    "factor_name": "nominal_progress",
                    "display_name": "Steady Trajectory",
                    "value": "Nominal",
                    "benchmark": "Nominal",
                    "severity": "LOW",
                    "explanation": "Project operates within expected milestone velocity and cost envelope.",
                }
            )

        return drivers

    def get_watchlist(
        self,
        report_month: str | None = None,
        min_warning_strength: int = 1,
        sector: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Get deteriorating early warning watchlist."""
        sub = self.get_month_df(report_month=report_month)
        actual_month = report_month or self.get_latest_month()

        if sub.empty:
            return {
                "report_month": actual_month,
                "total_flagged_projects": 0,
                "min_warning_strength_filter": min_warning_strength,
                "projects": [],
            }

        # Filter by active early warning and minimum strength
        cond = (sub["early_warning"]) & (sub["warning_strength"] >= min_warning_strength)
        if sector and sector.strip():
            cond = cond & (sub["sector"].str.strip().str.lower() == sector.strip().lower())

        flagged = sub[cond].sort_values(
            by=["warning_strength", "risk_score", "cost_escalation_amt"],
            ascending=[False, False, False],
        )

        total_flagged = len(flagged)
        items = []
        for _, r in flagged.head(limit).iterrows():
            items.append(
                {
                    "project_id": str(r["project_id"]),
                    "project_name": str(r["project_name"]),
                    "sector": str(r["sector"]),
                    "ministry": str(r["ministry"]),
                    "report_month": str(r["report_month"]),
                    "risk_score": round(float(r.get("risk_score", 0.0)), 2),
                    "risk_band": str(r.get("risk_band", "PROVISIONAL")),
                    "warning_status": str(r.get("warning_status", "ACTIVE_WARNING")),
                    "warning_strength": int(r.get("warning_strength", 1)),
                    "triggers_fired": str(r.get("triggers_fired", "")),
                    "risk_score_prev": (
                        round(float(r["risk_score_prev"]), 2)
                        if pd.notna(r.get("risk_score_prev"))
                        else None
                    ),
                    "risk_score_delta_1m": (
                        round(float(r["risk_score_delta_1m"]), 2)
                        if pd.notna(r.get("risk_score_delta_1m"))
                        else None
                    ),
                    "risk_score_delta_2m": (
                        round(float(r["risk_score_delta_2m"]), 2)
                        if pd.notna(r.get("risk_score_delta_2m"))
                        else None
                    ),
                    "financial_physical_gap": round(float(r.get("financial_physical_gap", 0.0)), 2),
                    "gap_delta_1m": (
                        round(float(r["gap_delta_1m"]), 2)
                        if pd.notna(r.get("gap_delta_1m"))
                        else None
                    ),
                    "gap_delta_2m": (
                        round(float(r["gap_delta_2m"]), 2)
                        if pd.notna(r.get("gap_delta_2m"))
                        else None
                    ),
                    "progress_velocity_3mo": (
                        round(float(r.get("progress_velocity_3mo", 0.0)), 2)
                        if pd.notna(r.get("progress_velocity_3mo"))
                        else 0.0
                    ),
                    "exp_velocity_3mo": (
                        round(float(r.get("exp_velocity_3mo", 0.0)), 2)
                        if pd.notna(r.get("exp_velocity_3mo"))
                        else 0.0
                    ),
                    "revised_cost_cr": round(float(r.get("revised_cost_cr", 0.0)), 2),
                    "physical_progress_pct": round(float(r.get("physical_progress_pct", 0.0)), 2),
                }
            )

        return {
            "report_month": actual_month,
            "total_flagged_projects": total_flagged,
            "min_warning_strength_filter": min_warning_strength,
            "projects": items,
        }

    def get_paginated_projects(
        self,
        report_month: str | None = None,
        sector: str | None = None,
        ministry: str | None = None,
        risk_band: str | None = None,
        has_warning: bool | None = None,
        search_query: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Search and paginate project list with multi-criteria filtering."""
        sub = self.get_month_df(report_month=report_month)
        actual_month = report_month or self.get_latest_month()

        if sub.empty:
            return {
                "report_month": actual_month,
                "total_count": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "projects": [],
            }

        filtered = sub.copy()

        if sector and sector.strip():
            filtered = filtered[
                filtered["sector"].str.strip().str.lower() == sector.strip().lower()
            ]
        if ministry and ministry.strip():
            filtered = filtered[
                filtered["ministry"].str.strip().str.lower() == ministry.strip().lower()
            ]
        if risk_band and risk_band.strip():
            filtered = filtered[
                filtered["risk_band"].str.strip().str.upper() == risk_band.strip().upper()
            ]
        if has_warning is not None:
            filtered = filtered[filtered["early_warning"] == has_warning]
        if search_query and search_query.strip():
            q = search_query.strip().lower()
            name_match = filtered["project_name"].astype(str).str.lower().str.contains(q)
            id_match = filtered["project_id"].astype(str).str.lower().str.contains(q)
            agency_match = (
                filtered.get("implementing_agency", pd.Series(""))
                .astype(str)
                .str.lower()
                .str.contains(q)
            )
            filtered = filtered[name_match | id_match | agency_match]

        # Sort by risk score desc
        filtered = filtered.sort_values(
            by=["risk_score", "revised_cost_cr"], ascending=[False, False]
        )

        total_count = len(filtered)
        total_pages = max(1, int(np.ceil(total_count / page_size)))
        page_clamped = min(max(1, page), total_pages) if total_count > 0 else 1

        start_idx = (page_clamped - 1) * page_size
        end_idx = start_idx + page_size

        page_df = filtered.iloc[start_idx:end_idx]
        items = [self._row_to_quick_summary(r) for _, r in page_df.iterrows()]

        return {
            "report_month": actual_month,
            "total_count": total_count,
            "page": page_clamped,
            "page_size": page_size,
            "total_pages": total_pages,
            "projects": items,
        }

    def _row_to_quick_summary(self, r: pd.Series) -> dict[str, Any]:
        """Convert a row series into ProjectQuickSummary dict."""
        orig = float(r.get("original_cost_cr", 0.0))
        rev = float(r.get("revised_cost_cr", 0.0))
        esc_pct = float(r.get("cost_escalation_pct", 0.0))
        return {
            "project_id": str(r["project_id"]),
            "project_name": str(r["project_name"]),
            "sector": str(r["sector"]),
            "ministry": str(r["ministry"]),
            "original_cost_cr": round(orig, 2),
            "revised_cost_cr": round(rev, 2),
            "cost_escalation_pct": round(esc_pct, 2),
            "physical_progress_pct": round(float(r.get("physical_progress_pct", 0.0)), 2),
            "risk_score": round(float(r.get("risk_score", 0.0)), 2),
            "risk_band": str(r.get("risk_band", "PROVISIONAL")),
            "early_warning": bool(r.get("early_warning", False)),
            "warning_status": str(r.get("warning_status", "INSUFFICIENT_HISTORY")),
            "warning_strength": int(r.get("warning_strength", 0)),
            "triggers_fired": str(r.get("triggers_fired", "none")),
        }

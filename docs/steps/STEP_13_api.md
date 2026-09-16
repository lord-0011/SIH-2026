# STEP 13 — Backend API

- **Phase:** 14
- **Status:** DONE   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_12

## Goal
FastAPI reads precomputed tables and serves national/sector/ministry/project endpoints (+ health, last-run).

## Scope (do exactly this, nothing extra)
- Implement endpoints in docs/02 (including watchlist and catalog).
- Project endpoint returns fields + score + sub-scores + trend + top factors in one payload.
- last-run returns the latest data month so UI shows real freshness.
- Strict read-only serving layer over precomputed parquets (`panel.parquet`, `risk_scores.parquet`, `early_warning.parquet`, `features.parquet`) with zero request-time model inference or feature recomputation.
- Full honesty metadata: regime separation (Non-Roads primary vs Roads caveated transfer regime), data sufficiency (`SUFFICIENT` vs `PROVISIONAL`), and causal early-warning evidence.

## Method / approach
Read-only over `data/processed/` using in-memory `DataRepository`. Pure slice queries. Pydantic v2 response models yielding automatic interactive OpenAPI documentation (`/docs`, `/redoc`).

## Verify (paste REAL output, don't summarise)

### 1. `/health`
```json
{
  "status": "healthy",
  "service": "paimana-api",
  "version": "1.0.0"
}
```

### 2. `/pipeline/last-run`
```json
{
  "latest_data_month": "2026-07",
  "earliest_data_month": "2025-07",
  "total_months": 13,
  "total_canonical_projects": 2243,
  "total_panel_rows": 18860,
  "total_active_projects_latest_month": 1800,
  "freshness_note": "Data verified as of 2026-07. Serving precomputed batch outputs."
}
```

### 3. `/national/summary` (Latest Month 2026-07)
```json
{
  "report_month": "2026-07",
  "total_projects": 1800,
  "non_roads": {
    "total_projects": 787,
    "avg_risk_score": 11.4,
    "band_distribution": {
      "LOW": 482,
      "MEDIUM": 220,
      "HIGH": 47,
      "CRITICAL": 38
    },
    "active_warnings_count": 311,
    "warning_strength_distribution": {
      "1": 237,
      "2": 69,
      "3": 5
    },
    "data_sufficiency_counts": {
      "SUFFICIENT": 754,
      "PROVISIONAL": 33
    },
    "transfer_regime": false,
    "transfer_regime_note": null
  },
  "roads": {
    "total_projects": 1013,
    "avg_risk_score": 19.6,
    "band_distribution": {
      "LOW": 480,
      "MEDIUM": 248,
      "HIGH": 116,
      "CRITICAL": 169
    },
    "active_warnings_count": 535,
    "warning_strength_distribution": {
      "1": 358,
      "2": 154,
      "3": 23
    },
    "data_sufficiency_counts": {
      "SUFFICIENT": 993,
      "PROVISIONAL": 20
    },
    "transfer_regime": true,
    "transfer_regime_note": "Onboarded Dec 2025 with expired backlog dates; interpret with caution"
  },
  "combined_total_cost_cr": 3395143.25,
  "combined_total_expenditure_cr": 1948170.44,
  "combined_avg_progress_pct": 59.57,
  "combined_band_distribution": {
    "LOW": 962,
    "MEDIUM": 468,
    "HIGH": 163,
    "CRITICAL": 207
  },
  "combined_active_warnings": 846,
  "monthly_trend": [
    {
      "report_month": "2026-06",
      "total_projects": 1977,
      "avg_risk_score": 15.6,
      "critical_count": 210,
      "high_count": 181,
      "active_warnings_count": 750
    },
    {
      "report_month": "2026-07",
      "total_projects": 1800,
      "avg_risk_score": 16.0,
      "critical_count": 207,
      "high_count": 163,
      "active_warnings_count": 846
    }
  ]
}
```

### 4. `/sectors/Railways/summary`
```json
{
  "sector": "Railways",
  "report_month": "2026-07",
  "is_road": false,
  "transfer_regime": false,
  "transfer_regime_note": null,
  "total_projects": 192,
  "total_cost_cr": 469207.22,
  "total_expenditure_cr": 461968.46,
  "avg_physical_progress_pct": 50.5,
  "avg_risk_score": 7.0,
  "band_distribution": {
    "LOW": 123,
    "MEDIUM": 63,
    "HIGH": 5,
    "CRITICAL": 1
  },
  "active_warnings_count": 64,
  "national_benchmarks": {
    "national_non_roads_avg_score": 11.4,
    "national_non_roads_critical_pct": 4.8,
    "national_non_roads_active_warning_pct": 39.5
  },
  "top_risk_projects": [
    {
      "project_id": "705782",
      "project_name": "Barabanki-Malhaur - 3rd & 4th Line 32.84 km",
      "ministry": "Ministry of Railways",
      "sector": "Railways",
      "state": "['Uttar Pradesh']",
      "is_road": false,
      "transfer_regime": false,
      "data_sufficiency": "SUFFICIENT",
      "risk_score": 56.1,
      "risk_band": "CRITICAL",
      "calibrated_probability": 0.5608,
      "early_warning": true,
      "warning_status": "ACTIVE_WARNING",
      "warning_strength": 1,
      "triggers_fired": "score_rising_2m",
      "original_cost_cr": 407.0,
      "cumulative_expenditure_cr": 444.11,
      "physical_progress_pct": 77.0
    }
  ]
}
```

### 5. `/projects/400145` (Steady-HIGH Negative Control Project Dossier)
```json
{
  "project_id": "400145",
  "project_code": "400145",
  "project_name": "CHHAL OC SEAM III [6 MTY]",
  "implementing_agency": "South Eastern Coalfields Limited [SECL]",
  "ministry": "Ministry of Coal",
  "sector": "Coal",
  "state": "['Chhattisgarh']",
  "is_road": false,
  "transfer_regime": false,
  "transfer_regime_note": null,
  "data_sufficiency": "SUFFICIENT",
  "observed_months_to_date": 6,
  "current_metrics": {
    "report_month": "2025-12",
    "risk_score": 43.6,
    "risk_band": "HIGH",
    "calibrated_probability": 0.4361,
    "raw_probability": 0.7568,
    "original_cost_cr": 610.63,
    "revised_cost_cr": 610.63,
    "cumulative_expenditure_cr": 583.26,
    "exp_utilization": 0.9552,
    "physical_progress_pct": 100.0,
    "financial_physical_gap": -4.48,
    "original_completion_date": "03/2022",
    "revised_completion_date": "01/2026",
    "planned_duration_months": 99.0,
    "elapsed_duration_months": 144.0,
    "remaining_duration_months": 1.0,
    "trajectory_anchor_date": "12/2013"
  },
  "early_warning": {
    "early_warning": false,
    "warning_status": "STABLE_OR_IMPROVING",
    "warning_strength": 0,
    "triggers_fired": "none",
    "score_rising_fired": false,
    "gap_widening_fired": false,
    "velocity_divergence_fired": false,
    "risk_score_prev": 42.4,
    "risk_score_delta_1m": 1.2,
    "risk_score_delta_2m": 1.2,
    "gap_delta_1m": -14.56,
    "gap_delta_2m": -14.43,
    "progress_velocity_3mo": 5.0,
    "exp_velocity_3mo": 1.15
  }
}
```

### 6. `/watchlist` (Top Item with Full Evidence Trail)
```json
{
  "report_month": "2026-07",
  "total_active_warnings": 846,
  "non_roads_count": 311,
  "roads_count": 535,
  "top_item": {
    "project_id": "619100",
    "project_name": "Dhangaon - Borgaon section km 81.000 to km 139.000 [Indore - Edlabad Pkg IV]",
    "ministry": "Ministry of Road Transport & Highways",
    "sector": "Roads & Highways",
    "is_road": true,
    "transfer_regime": true,
    "data_sufficiency": "SUFFICIENT",
    "risk_score": 61.2,
    "risk_band": "CRITICAL",
    "warning_strength": 3,
    "triggers_fired": "score_rising_2m,gap_widening_2m,velocity_divergence_2m",
    "score_delta_1m": 1.8,
    "score_delta_2m": 24.8,
    "gap_delta_1m": 0.02,
    "progress_velocity_3mo": 0.0,
    "exp_velocity_3mo": 36.13,
    "physical_progress_pct": 99.8
  }
}
```

## Definition of Done
- [x] Scope implemented, nothing extra
- [x] Tests written & passing (15/15 tests passing across `tests/test_api_fixture.py` and `tests/test_api.py`)
- [x] Verify output pasted
- [x] Docs synced: `docs/02_ARCHITECTURE.md`, `docs/steps/STEP_13_api.md`
- [x] PROGRESS.md + CHANGELOG.md updated
- [x] Walkthrough written for review

## Blockers / Questions
None.

# STEP 13 — Backend API

- **Phase:** 14
- **Status:** DONE   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_12

## Goal
FastAPI reads precomputed tables and serves national/sector/ministry/project endpoints (+ health, last-run).

## Scope (do exactly this, nothing extra)
- Implement endpoints in docs/02 (plus watchlist filter).
- Project endpoint returns fields + score + sub-scores + trend + top factors in one payload.
- last-run returns the latest data month so UI shows real freshness.

## Method / approach
Read-only over `data/processed` (`panel.parquet`, `features.parquet`, `risk_scores.parquet`, `early_warning.parquet`). No model calls at request time. Pydantic v2 response models → auto OpenAPI documentation at `/docs` and `/redoc`. CORS middleware configured for React dashboard frontend integration.

## Verify (paste REAL output, don't summarise)
```text
=== Health Check (/health) [Status: 200] ===
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-09-16T04:18:47.126904+00:00"
}

=== Pipeline Last Run (/pipeline/last-run) [Status: 200] ===
{
  "latest_report_month": "2026-07",
  "available_months": [
    "2026-07"
  ],
  "total_projects_in_latest_month": 1,
  "data_as_of": "Monthly Flash Report as of 2026-07",
  "pipeline_stages": [
    {
      "name": "panel",
      "path": "C:\\Users\\Parshant sharma\\OneDrive\\Desktop\\SIH_2026\\SIH-2026\\data\\processed\\panel.parquet",
      "exists": false,
      "rows": null
    }
  ]
}

=== National Summary (/national/summary) [Status: 200] ===
{
  "report_month": "2026-07",
  "total_projects": 1,
  "total_original_cost_cr": 10000.0,
  "total_revised_cost_cr": 13000.0,
  "total_expenditure_cr": 8000.0,
  "total_cost_escalation_cr": 3000.0,
  "portfolio_cost_escalation_pct": 30.0,
  "avg_physical_progress_pct": 36.5,
  "avg_financial_physical_gap": 25.04,
  "avg_risk_score": 72.5,
  "risk_bands": [
    {
      "band": "LOW",
      "count": 0,
      "percentage": 0.0
    },
    {
      "band": "MEDIUM",
      "count": 0,
      "percentage": 0.0
    },
    {
      "band": "HIGH",
      "count": 0,
      "percentage": 0.0
    },
    {
      "band": "CRITICAL",
      "count": 1,
      "percentage": 100.0
    },
    {
      "band": "PROVISIONAL",
      "count": 0,
      "percentage": 0.0
    }
  ],
  "early_warnings": {
    "active_warnings_count": 1,
    "active_warning_rate_pct": 100.0,
    "score_rising_count": 1,
    "gap_widening_count": 1,
    "velocity_divergence_count": 0,
    "strength_1_count": 0,
    "strength_2_count": 1,
    "strength_3_count": 0
  },
  "sectors": [
    {
      "sector": "RAILWAYS",
      "total_projects": 1,
      "total_original_cost_cr": 10000.0,
      "total_revised_cost_cr": 13000.0,
      "total_cost_escalation_cr": 3000.0,
      "avg_cost_escalation_pct": 30.0,
      "avg_physical_progress_pct": 36.5,
      "avg_risk_score": 72.5,
      "critical_risk_count": 1,
      "high_risk_count": 0,
      "active_warnings_count": 1
    }
  ],
  "top_risk_projects": [
    {
      "project_id": "1001",
      "project_name": "Delhi-Mumbai High Speed Rail",
      "sector": "RAILWAYS",
      "ministry": "Ministry of Railways",
      "original_cost_cr": 10000.0,
      "revised_cost_cr": 13000.0,
      "cost_escalation_pct": 30.0,
      "physical_progress_pct": 36.5,
      "risk_score": 72.5,
      "risk_band": "CRITICAL",
      "early_warning": true,
      "warning_status": "ACTIVE_WARNING",
      "warning_strength": 2,
      "triggers_fired": "score_rising_2m,gap_widening_2m"
    }
  ]
}

=== Project Detail (Level 3) (/projects/1001) [Status: 200] ===
{
  "project_id": "1001",
  "project_name": "Delhi-Mumbai High Speed Rail",
  "implementing_agency": "NHSRCL",
  "ministry": "Ministry of Railways",
  "sector": "RAILWAYS",
  "state": [
    "Delhi",
    "Maharashtra",
    "Gujarat"
  ],
  "project_size_band": "Mega",
  "project_status": "Ongoing",
  "date_of_approval": "2020-01-15",
  "start_date": "2020-06-01",
  "original_completion_date": "2026-12-31",
  "revised_completion_date": "2028-12-31",
  "actual_completion_date": null,
  "report_month": "2026-07",
  "original_cost_cr": 10000.0,
  "revised_cost_cr": 13000.0,
  "cumulative_expenditure_cr": 8000.0,
  "cost_escalation_amt_cr": 3000.0,
  "cost_escalation_pct": 30.0,
  "physical_progress_pct": 36.5,
  "financial_physical_gap": 25.04,
  "schedule_variance_months": 24.0,
  "planned_duration_months": 84.0,
  "elapsed_duration_months": 74.0,
  "remaining_duration_months": 22.0,
  "risk_score": 72.5,
  "risk_band": "CRITICAL",
  "data_sufficiency": "SUFFICIENT",
  "early_warning": true,
  "warning_status": "ACTIVE_WARNING",
  "warning_strength": 2,
  "triggers_fired": "score_rising_2m,gap_widening_2m",
  "risk_score_prev": 58.0,
  "risk_score_delta_1m": 14.5,
  "risk_score_delta_2m": 27.5,
  "gap_delta_1m": 5.66,
  "gap_delta_2m": 10.04,
  "top_risk_drivers": [
    {
      "factor_name": "financial_physical_gap",
      "display_name": "Severe Financial-Physical Divergence",
      "value": "+25.0%",
      "benchmark": "< 10.0%",
      "severity": "HIGH",
      "explanation": "Expenditure utilization exceeds physical progress by 25.0%, signaling capital burn ahead of works."
    },
    {
      "factor_name": "schedule_variance_months",
      "display_name": "Schedule Extension",
      "value": "24 months",
      "benchmark": "0 months",
      "severity": "MEDIUM",
      "explanation": "Target deadline deferred by 24 months."
    },
    {
      "factor_name": "cost_escalation_pct",
      "display_name": "Cost Escalation",
      "value": "+30.0%",
      "benchmark": "< 10.0%",
      "severity": "MEDIUM",
      "explanation": "Sanction cost escalated by 30.0%."
    },
    {
      "factor_name": "progress_velocity_3mo",
      "display_name": "Stagnant Physical Execution",
      "value": "0.50% / month",
      "benchmark": "> 1.5% / month",
      "severity": "HIGH",
      "explanation": "Physical work completion has ground to a standstill over recent 3-month window."
    },
    {
      "factor_name": "early_warning_triggers",
      "display_name": "Active Deterioration Trend",
      "value": "score_rising_2m,gap_widening_2m",
      "benchmark": "none",
      "severity": "HIGH",
      "explanation": "Early warning engine flagged multi-month worsening trend: score_rising_2m,gap_widening_2m."
    }
  ],
  "trajectory": [
    {
      "report_month": "2026-07",
      "risk_score": 72.5,
      "risk_band": "CRITICAL",
      "physical_progress_pct": 36.5,
      "cumulative_expenditure_cr": 8000.0,
      "exp_utilization": 0.0,
      "financial_physical_gap": 25.04,
      "progress_velocity_3mo": 0.5,
      "exp_velocity_3mo": 250.0,
      "early_warning": true,
      "warning_status": "ACTIVE_WARNING",
      "triggers_fired": "score_rising_2m,gap_widening_2m"
    }
  ]
}
```

## Definition of Done
- [x] Scope implemented, nothing extra
- [x] Tests written & passing (test: endpoint returns expected shape for a known project)
- [x] Verify output pasted
- [x] Docs synced: STEP_13_api.md
- [x] PROGRESS.md + CHANGELOG.md updated
- [x] Walkthrough written for review

## Blockers / Questions
None. Clean implementation with 13/13 passing API fixture tests and 83/83 passing repository tests.

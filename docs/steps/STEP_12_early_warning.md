# STEP 12 — Early Warning (basic)

- **Phase:** 12
- **Status:** DONE   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_11

## Goal
Flag deteriorating projects by TREND, not absolute score; log the complete causal trigger evidence.

## Scope (do exactly this, nothing extra)
- Rule: flag if risk score rose across $\ge 2$ consecutive observed months, OR financial_physical_gap widened across $\ge 2$ consecutive observed months, OR velocity divergence occurred across $\ge 2$ consecutive observed months.
- Gap handling: evaluated over project's last 3 observed rows ($T_{\text{prev2}} \to T_{\text{prev1}} \to T$) with freshness guard ($\text{span} \le 4$ calendar months). Short reporting gaps (e.g. Jan $\to$ Feb $\to$ Apr) are tolerated; wide gaps (> 4 mo) are rejected as `STALE_HISTORY`.
- Trigger combination: `ACTIVE_WARNING` fires on ANY trigger; emits `warning_strength` (0..3) representing count of triggers fired so dashboards can sort by conviction.
- Data sufficiency: `PROVISIONAL` projects ($\le 2$ observed months) cannot trend and flag `INSUFFICIENT_HISTORY`.
- Steady-HIGH negative control: steady or declining projects in HIGH/CRITICAL band do NOT fire score trend.
- Emit per project-month: `early_warning` (bool), `warning_status`, `warning_strength`, `triggers_fired`, previous vs current score, score deltas, gap deltas, velocities, and sector / road context.
- Write to `data/processed/early_warning.parquet`.

## Method / approach
Trailing comparison only. Causal temporal leakage invariance enforced via automated invariant tests.

## Verify (paste REAL output, don't summarise)
### 1. Overall Panel Distribution (`data/processed/early_warning.parquet`, N = 18,860)
```json
{
  "total_panel_rows": 18860,
  "total_active_warnings": 5862,
  "warning_status_distribution": {
    "STABLE_OR_IMPROVING": 8566,
    "ACTIVE_WARNING": 5862,
    "INSUFFICIENT_HISTORY": 4422,
    "STALE_HISTORY": 10
  },
  "warning_strength_distribution": {
    "0": 12998,
    "1": 4296,
    "2": 1365,
    "3": 201
  }
}
```

### 2. Latest Month Metrics (2026-07)
```
Total Projects: 1,800
Total Active Warnings: 846 (47.00%)

- Primary Non-Roads Validation Regime (N = 787):
  - Active Warnings: 311 (39.52%)
  - Strength 1: 237 projects (30.11%)
  - Strength 2: 69 projects (8.77%)
  - Strength 3: 5 projects (0.64%)

- Secondary Roads Caveated Transfer Regime (N = 1,013):
  - Active Warnings: 535 (52.81%)
  - Strength 1: 358 projects (35.34%)
  - Strength 2: 154 projects (15.20%)
  - Strength 3: 23 projects (2.27%)

- Triggers Fired in Latest Month:
  - score_rising_2m: 428
  - gap_widening_2m: 414
  - velocity_divergence_2m: 283
```

### 3. Negative Control: Concrete Steady-HIGH Project (400145)
```
Project 400145 trajectory:
  - 2025-07: 44.8 (HIGH)
  - 2025-08: 44.8 (HIGH)
  - 2025-09: 44.3 (HIGH)
  - 2025-10: 42.4 (HIGH)
  - 2025-11: 42.4 (HIGH)
  - 2025-12: 43.6 (HIGH)
Result: score_rising_fired = False in ALL months.
Verified that high snapshot score without upward momentum does NOT fire.
```

### 4. Example Multi-Trigger Trace
```json
{
  "project_id": "400142",
  "sector": "Coal",
  "is_road": false,
  "latest_month": "2026-07",
  "warning_status": "ACTIVE_WARNING",
  "warning_strength": 2,
  "triggers_fired": "gap_widening_2m,velocity_divergence_2m",
  "trajectory": [
    {
      "report_month": "2026-04",
      "risk_score": 2.2,
      "financial_physical_gap": -26.1,
      "progress_velocity_3mo": 0.0,
      "exp_velocity_3mo": 25.53
    },
    {
      "report_month": "2026-05",
      "risk_score": 2.2,
      "financial_physical_gap": -25.11,
      "progress_velocity_3mo": 0.0,
      "exp_velocity_3mo": 30.99
    },
    {
      "report_month": "2026-06",
      "risk_score": 2.2,
      "financial_physical_gap": -23.58,
      "progress_velocity_3mo": 0.0,
      "exp_velocity_3mo": 31.85
    },
    {
      "report_month": "2026-07",
      "risk_score": 2.2,
      "financial_physical_gap": -23.13,
      "progress_velocity_3mo": 0.0,
      "exp_velocity_3mo": 22.21
    }
  ]
}
```

## Definition of Done
- [x] Scope implemented, nothing extra
- [x] Tests written & passing (11 tests in early warning suites; 124 passed in full repo)
- [x] Verify output pasted
- [x] Docs synced: STEP_12_early_warning.md
- [x] PROGRESS.md + CHANGELOG.md updated
- [x] Walkthrough written for review

## Blockers / Questions
None. STEP_12 completed and verified.


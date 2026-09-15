# STEP 03 — Entity Matching

- **Phase:** 2
- **Status:** DONE   <!-- NOT STARTED | IN PROGRESS | BLOCKED | DONE -->
- **Depends on:** STEP_02

## Goal
Assign a canonical project_id to every record across months using Project Code as the primary key, with fallback cascade exception handling, strict umbrella legacy code protection, concurrency invariant enforcement, and mid-window arrival trajectory anchoring for STEP_04.

## Scope & Implementation
1. **Direct Join on Project Code**: Post-fix, `project_code` is 100.00% populated in all 18,601 ongoing records, unique per month, and stable across months. Assigned `canonical_project_id = project_code` with `match_confidence = "exact_code"`.
2. **Fallback Cascade (Exception Handler)**: Retained for records lacking `project_code` (resolves via unique non-umbrella `legacy_ocms_code` -> `pmgid` -> composite name/agency/approval key).
3. **Umbrella Legacy Protection & Reconciled Counts**:
   - **26 single-month concurrent umbrella legacy codes**: Mapped to >1 `project_code` simultaneously in the same monthly report (e.g. NHAI corridor EPC packages).
   - **30 corpus-wide umbrella legacy codes**: Mapped to >1 `project_code` across the pooled 13 months.
   - **Reconciliation**: The 4-code difference (`N12000133`, `N12000134`, `N12000135`, `N22000602`) reflects source legacy-label reassignments across distinct physical steel/rail projects between Feb and Mar 2026 (Bokaro, Bhilai, Battery Cyclon, Dallirajhara-Rowghat), while `project_code` remained 100% stable.
   - Never collapse umbrella codes: Distinct `project_code`s are guaranteed to receive distinct `canonical_project_id`s.
4. **Concurrency Invariant**: Two records in the same `report_month` never share a `canonical_project_id`. Holds with 0 duplicates across all 13 months.
5. **Mid-Window Arrival & Trajectory Anchoring (STEP_04 Ready)**:
   - Total distinct canonical projects: **2,243**
   - Baseline projects (<= 2025-11): **902**
   - Total mid-window arrivals (>= 2025-12): **1,341**
     - MoRTH mid-window arrivals: **1,187** (onboarded in waves: Dec 584, Jan 282, Feb 247, etc.)
     - Other ministries mid-window arrivals: **154**
   - Trajectory anchor date (`trajectory_anchor_date`): Populated for 100% of all 1,341 mid-window arrivals using their actual approval/start date, ensuring STEP_04 measures project velocity from true inception rather than first reporting month.

## Verify (Real Output Sourced from Data)

### Monthly Matching Audit (`data/interim/matching_audit.csv`)
| Month | Total Records | Exact Code Matches | Fallback Matches | Unmatched | Distinct Projects | Mid-Window Active | MoRTH Mid Active | Non-MoRTH Mid Active |
|---|---|---|---|---|---|---|---|---|
| 2025-07 | 791 | 791 | 0 | 0 | 791 | 0 | 0 | 0 |
| 2025-08 | 800 | 800 | 0 | 0 | 800 | 0 | 0 | 0 |
| 2025-09 | 794 | 794 | 0 | 0 | 794 | 0 | 0 | 0 |
| 2025-10 | 820 | 820 | 0 | 0 | 820 | 0 | 0 | 0 |
| 2025-11 | 823 | 823 | 0 | 0 | 823 | 0 | 0 | 0 |
| 2025-12 | 1,392 | 1,392 | 0 | 0 | 1,392 | 603 | 584 | 19 |
| 2026-01 | 1,702 | 1,702 | 0 | 0 | 1,702 | 916 | 863 | 53 |
| 2026-02 | 1,948 | 1,948 | 0 | 0 | 1,948 | 1,171 | 1,108 | 63 |
| 2026-03 | 1,941 | 1,941 | 0 | 0 | 1,941 | 1,183 | 1,120 | 63 |
| 2026-04 | 1,981 | 1,981 | 0 | 0 | 1,981 | 1,237 | 1,137 | 100 |
| 2026-05 | 1,987 | 1,987 | 0 | 0 | 1,987 | 1,270 | 1,149 | 121 |
| 2026-06 | 1,847 | 1,847 | 0 | 0 | 1,847 | 1,144 | 1,022 | 122 |
| 2026-07 | 1,775 | 1,775 | 0 | 0 | 1,775 | 1,135 | 993 | 142 |
| **Total** | **18,601** | **18,601** | **0** | **0** | **2,243 (unique)** | **1,341 (unique)** | **1,187 (unique)** | **154 (unique)** |

## Definition of Done
- [x] Scope implemented, direct join + fallback cascade exception handler
- [x] Tests written & passing (`tests/test_matching_fixture.py` in CI, `tests/test_matching.py` locally)
- [x] Concurrency invariant and no-merge invariant verified across all 13 months
- [x] Adversarial Bokaro/Bhilai legacy swap test implemented
- [x] Trajectory anchor dates verified for all 1,341 mid-window arrivals
- [x] Docs synced: STEP_03_matching.md, docs/03_DATA_INVENTORY.md §C#5
- [x] PROGRESS.md + CHANGELOG.md updated
- [x] Walkthrough written for review

# 03 — Data Inventory (FILL FROM REAL FILES — this is the Phase-4 gate)

> This document is the single place where facts about *our actual dataset* live.
> Numbers here must be SOURCED (Rule 2). Anything not yet confirmed is a
> `TODO(confirm-from-data)` and MUST be resolved in Phase 4 before Phase 5 starts.
> Do not copy assumptions from the master design doc into here as if confirmed.

## A. What we physically hold
- [x] `reports/FlashReport_April2026.pdf` — 163 pages, text-layer PDF, 6 tables. CONFIRMED by
  direct inspection. Contains Table 6 (All Ongoing Projects, 1,981 rows), Table 3
  (Completed Projects During Month, 9 rows), Table 4 (Newly Added, 55 rows), Tables 1/2/5 (roll-ups).
- [x] 13 consecutive monthly Flash Reports physically held in `reports/` covering July 2025 → July 2026.
  Plus 1 quarterly report (`QPISR_QR_1st_2025-26 (1).pdf`, 261 pages).

### File manifest (confirmed from data across all 13 months)
| Month | File | Pages | Layout | Ongoing Table | Ongoing Projects | MoRTH Projects | Completed Projects | Newly Added Projects | Orig Cost (Rs Cr) |
|---|---|---|---|---|---|---|---|---|---|
| 2025-07 | reports/FlashReport_July_2025.pdf | 67 | Early | Table 4 | 791 | 0 | 0 (N/A) | 0 (N/A) | 2,386,335.28 |
| 2025-08 | reports/FlashReport_August_2025.pdf | 67 | Early | Table 4 | 800 | 0 | 0 (N/A) | 0 (N/A) | 2,375,332.37 |
| 2025-09 | reports/FlashReport_September_2025.pdf | 72 | Modern | Table 6 | 794 | 0 | 6 | 34 | 2,533,121.98 |
| 2025-10 | reports/FlashReport_October_2025.pdf | 73 | Modern | Table 6 | 820 | 0 | 6 | 35 | 2,552,631.73 |
| 2025-11 | reports/FlashReport_November_2025.pdf | 73 | Modern | Table 6 | 823 | 0 | 13 | 21 | 2,418,198.30 |
| 2025-12 | reports/FlashReport_December_2025.pdf | 108 | Modern | Table 6 | 1,392 | 584 | 17 | 20 | 2,968,247.55 |
| 2026-01 | reports/FlashReport_January_2026 (1).pdf | 134 | Modern | Table 6 | 1,702 | 863 | 3 | 203 | 3,371,816.32 |
| 2026-02 | reports/FlashReport_February_2026.pdf | 168 | Modern | Table 6 | 1,948 | 1,108 | 9 | 268 | 3,632,088.32 |
| 2026-03 | reports/FlashReport_March_2026.pdf | 157 | Modern | Table 6 | 1,941 | 1,120 | 25 | 12 | 3,588,861.17 |
| 2026-04 | reports/FlashReport_April2026.pdf | 163 | Modern | Table 6 | 1,981 | 1,137 | 9 | 55 | 3,712,662.01 |
| 2026-05 | reports/FlashReport_May2026.pdf | 163 | Modern | Table 6 | 1,987 | 1,149 | 16 | 35 | 3,709,724.65 |
| 2026-06 | reports/FlashReport_June_2026.pdf | 161 | Modern | Table 6 | 1,847 | 1,022 | 130 | 17 | 3,561,721.07 |
| 2026-07 | reports/FlashReport_July_2026.pdf | 153 | Modern | Table 6 | 1,775 | 993 | 25 | 36 | 3,370,138.22 |
| 2025-Q1 | reports/QPISR_QR_1st_2025-26 (1).pdf | 261 | Quarterly | N/A | Quarterly Status | N/A | N/A | N/A | N/A |

## B. Confirmed field set (from Ongoing Tables)
Sl.No, Project Name, Implementing Agency, Project Code, Legacy OCMS Code (modern), PMGID (modern), State,
Date of Approval, Start Date (modern), Original/Target DoC, Revised DoC, Original Cost (Rs Cr),
Revised Cost (Rs Cr), Cumulative Expenditure (Rs Cr), Physical Progress (%);
grouped by Ministry → Sector. Both Revised Cost and Revised Completion Date are confirmed populated across all 13 months.

## C. Questions Phase 4 EDA MUST answer (each becomes a sourced number)
1. **CONFIRMED**: exact monthly coverage — 13 consecutive months held (2025-07 through 2026-07). All 13 months successfully ingested into `data/interim/raw_ongoing_<YYYY_MM>.parquet`.
2. **CONFIRMED**: format consistency vs coverage axes:
   - *Format axis*: 2025-07 and 2025-08 use Early format (Ongoing is Table 4; no Completed/Newly Added tables). From 2025-09 onward, reports use Modern format (Ongoing is Table 6; Completed is Table 3; Newly Added is Table 4).
   - *Coverage axis*: MoRTH (Ministry of Road Transport & Highways) is absent in 2025-07 through 2025-11 (non-MoRTH baseline is ~800–823 projects). MoRTH is incrementally integrated starting in Dec 2025 (584 projects) -> Jan 2026 (863 projects) -> Feb 2026 (1,108 projects) -> peaking at 1,149 in May 2026 -> 993 in July 2026.
3. `TODO`: observations-per-project distribution — how many projects have long enough trajectories (e.g. >=6 months) for trend features + a forward-window label?
4. **CONFIRMED**: realized-outcome count — exactly **259** project completions observed across the 11 modern months' Table 3 ("Completed Projects During Month") tables, computed by summing the `completed_row_count` column in `data/interim/ingestion_summary.csv` (6 + 6 + 13 + 17 + 3 + 9 + 25 + 9 + 16 + 130 + 25 = 259; July–August 2025 early layout had no Table 3). *Concentration note*: This set is heavily concentrated in a single month — June 2026 alone accounts for 130 completions (~127 of which are MoRTH road packages), meaning the effective independent validation sample across all other months and sectors is much smaller (129 projects across 10 months) than the gross 259 total suggests.
5. `TODO`: entity stability — how often does Project Code change for the same project? population rate of Legacy OCMS Code and PMGID across the full window.
6. `TODO`: usable rows per candidate horizon (N=3,6,12 months) — determines which horizon is even viable (see LABEL_SPEC).
7. **CONFIRMED**: structural breaks — large jump in project count (823 -> 1,987) between Nov 2025 and May 2026 is proven to be MoRTH onboarding integration, not a change in reporting convention of other sectors.

## D. Known data-quality caveats (source: April report notes)
- A named set of project IDs excluded some months "due to inconsistency in Cumulative Expenditure" → treat as reporting gap, NOT ordinary missingness.
- Projects with revised cost below Rs.150 cr flagged "under reconciliation" → revised cost can move down; threshold not perfectly stable.
- 335 of 1,981 projects in April have revised < original cost (mostly legitimate downward revisions); STEP_02 must quantify.

## E. Sanity anchors (authoritative Table 1 reproduction across all 13 months)
Every month reproduced its own published Table 1 grand total and cost sum with 100% fidelity:
| Month | Table 1 Published Projects | Extracted Ongoing Rows | Table 1 Orig Cost (Cr) | Extracted Orig Cost (Cr) | Match Status |
|---|---|---|---|---|---|
| 2025-07 | 791 | 791 | 2,386,335.28 | 2,386,335.28 | PASS (100%) |
| 2025-08 | 800 | 800 | 2,375,332.37 | 2,375,332.37 | PASS (100%) |
| 2025-09 | 794 | 794 | 2,533,121.98 | 2,533,121.98 | PASS (100%) |
| 2025-10 | 820 | 820 | 2,552,631.73 | 2,552,631.73 | PASS (100%) |
| 2025-11 | 823 | 823 | 2,418,198.30 | 2,418,198.30 | PASS (100%) |
| 2025-12 | 1,392 | 1,392 | 2,968,247.55 | 2,968,247.55 | PASS (100%) |
| 2026-01 | 1,702 | 1,702 | 3,371,816.32 | 3,371,816.32 | PASS (100%) |
| 2026-02 | 1,948 | 1,948 | 3,632,088.32 | 3,632,088.32 | PASS (100%) |
| 2026-03 | 1,941 | 1,941 | 3,588,861.17 | 3,588,861.17 | PASS (100%) |
| 2026-04 | 1,981 | 1,981 | 3,712,662.01 | 3,712,662.01 | PASS (100%) |
| 2026-05 | 1,987 | 1,987 | 3,709,724.65 | 3,709,724.65 | PASS (100%) |
| 2026-06 | 1,847 | 1,847 | 3,561,721.07 | 3,561,721.07 | PASS (100%) |
| 2026-07 | 1,775 | 1,775 | 3,370,138.22 | 3,370,138.22 | PASS (100%) |

## GATE: Phase 5 may not begin while any Section-C TODO is unresolved.
Run: `grep -rn "confirm-from-data" docs/03_DATA_INVENTORY.md`

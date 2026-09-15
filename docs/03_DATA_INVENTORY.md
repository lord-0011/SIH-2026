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

### File manifest (fill in)
| Month | File | Format (PDF / CSV / xlsx / other) | Same table structure as April? |
|-------|------|-----------------------------------|-------------------------------|
| 2025-07 | reports/FlashReport_July_2025.pdf | PDF text-layer (67 pp) | No (Ongoing is Table 4; MoRTH excluded in this month) |
| 2025-08 | reports/FlashReport_August_2025.pdf | PDF text-layer (67 pp) | No (Ongoing is Table 4) |
| 2025-09 | reports/FlashReport_September_2025.pdf | PDF text-layer (72 pp) | No (Ongoing is Table 4) |
| 2025-10 | reports/FlashReport_October_2025.pdf | PDF text-layer (73 pp) | No (Ongoing is Table 4) |
| 2025-11 | reports/FlashReport_November_2025.pdf | PDF text-layer (73 pp) | No (Ongoing is Table 4) |
| 2025-12 | reports/FlashReport_December_2025.pdf | PDF text-layer (108 pp) | Transition structure |
| 2026-01 | reports/FlashReport_January_2026 (1).pdf | PDF text-layer (134 pp) | Transition structure |
| 2026-02 | reports/FlashReport_February_2026.pdf | PDF text-layer (168 pp) | Yes (Table 6 All Ongoing) |
| 2026-03 | reports/FlashReport_March_2026.pdf | PDF text-layer (157 pp) | Yes (Table 6 All Ongoing) |
| 2026-04 | reports/FlashReport_April2026.pdf | PDF text-layer (163 pp) | Reference (Table 6 All Ongoing, 1,981 projects) |
| 2026-05 | reports/FlashReport_May2026.pdf | PDF text-layer (163 pp) | Yes (Table 6 All Ongoing) |
| 2026-06 | reports/FlashReport_June_2026.pdf | PDF text-layer (161 pp) | Yes (Table 6 All Ongoing) |
| 2026-07 | reports/FlashReport_July_2026.pdf | PDF text-layer (153 pp) | Yes (Table 6 All Ongoing) |
| 2025-Q1 | reports/QPISR_QR_1st_2025-26 (1).pdf | PDF text-layer (261 pp) | No (Quarterly Status Report) |

## B. Confirmed field set (from April Table 6)
Sl.No, Project Name, Implementing Agency, Project Code, Legacy OCMS Code, PMGID, State,
Date of Approval, Start Date, Original/Target DoC, Revised DoC, Original Cost (Rs Cr),
Revised Cost (Rs Cr), Cumulative Expenditure (Rs Cr), Physical Progress (%);
grouped by Ministry → Sector. NO free-text remarks field exists.

`TODO(confirm-from-data)`: does the *actual* CUF export we hold have MORE fields than
the public PDF surfaces (milestones, contractor, land acquisition)? List any extras.

## C. Questions Phase 4 EDA MUST answer (each becomes a sourced number)
1. `TODO`: exact monthly coverage — 13 consecutive months held (2025-07 through 2026-07). Confirm if Jan-June 2025 exist elsewhere.
2. `TODO`: format consistency — confirmed that 2025-07 to 2025-11 use Table 4 for Ongoing (67-73 pages, MoRTH excluded), transitioning in 2025-12/2026-01 to Table 6 structure (150-168 pages).
3. `TODO`: observations-per-project distribution — how many projects have long enough
   trajectories (e.g. >=6 months) for trend features + a forward-window label?
4. `TODO`: realized-outcome count — total projects across all months' "Completed
   Projects During Month" tables (this sizes our honest validation set).
5. `TODO`: entity stability — how often does Project Code change for the same project?
   population rate of Legacy OCMS Code and PMGID across the full window.
6. `TODO`: usable rows per candidate horizon (N=3,6,12 months) — determines which
   horizon is even viable (see LABEL_SPEC).
7. `TODO`: structural breaks — any month where a field's distribution jumps (e.g. sudden
   spike in progress=0 or =100) suggesting a reporting-convention change.

## D. Known data-quality caveats (source: April report notes)
- A named set of project IDs excluded some months "due to inconsistency in Cumulative
  Expenditure" → treat as reporting gap, NOT ordinary missingness.
- Projects with revised cost below Rs.150 cr flagged "under reconciliation" → revised
  cost can move down; threshold not perfectly stable.

## E. Sanity anchors (use to prove the parser is correct)
April 2026 totals reproduced by parser (`src.ingestion.parser` verified in `tests/test_ingestion_april.py`):
- 1,981 ongoing projects (reproduced: 1,981); 17 ministries (reproduced: 17); 22 sectors (reproduced: 22)
- Original cost: Rs 3,712,662.01 Cr (≈ Rs 37.13 lakh cr) (reproduced: 3,712,662.01 Cr)
- Revised cost: Rs 4,278,402.37 Cr (≈ Rs 42.78 lakh cr) (reproduced: 4,278,402.37 Cr)
- Cum. expenditure: Rs 2,036,107.49 Cr (≈ Rs 20.36 lakh cr) (reproduced: 2,036,107.49 Cr)
- Table 3 Completed: 9 projects (reproduced: 9)
- Table 4 Newly Added: 55 projects (reproduced: 55)

## GATE: Phase 5 may not begin while any Section-C TODO is unresolved.
Run: `grep -rn "confirm-from-data" docs/03_DATA_INVENTORY.md`

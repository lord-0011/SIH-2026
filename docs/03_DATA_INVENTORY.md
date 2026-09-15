# 03 — Data Inventory (FILL FROM REAL FILES — this is the Phase-4 gate)

> This document is the single place where facts about *our actual dataset* live.
> Numbers here must be SOURCED (Rule 2). Anything not yet confirmed is a
> `TODO(confirm-from-data)` and MUST be resolved in Phase 4 before Phase 5 starts.
> Do not copy assumptions from the master design doc into here as if confirmed.

## A. What we physically hold
- [x] `FlashReport_April2026.pdf` — 163 pages, text-layer PDF, 6 tables. CONFIRMED by
  direct inspection. Contains Table 6 (All Ongoing Projects, 1,981 rows), Table 3
  (Completed Projects During Month), Table 4 (Newly Added), Tables 1/2/5 (roll-ups).
- [ ] Monthly data Q1 2025 → July 2026 (~19 months). Adi states we have this.
  `TODO(confirm-from-data)`: list every file, its month, and its format below.

### File manifest (fill in)
| Month | File | Format (PDF / CSV / xlsx / other) | Same table structure as April? |
|-------|------|-----------------------------------|-------------------------------|
| 2026-04 | FlashReport_April2026.pdf | PDF text-layer | (reference) |
| ... | `TODO(confirm-from-data)` | | |

## B. Confirmed field set (from April Table 6)
Sl.No, Project Name, Implementing Agency, Project Code, Legacy OCMS Code, PMGID, State,
Date of Approval, Start Date, Original/Target DoC, Revised DoC, Original Cost (Rs Cr),
Revised Cost (Rs Cr), Cumulative Expenditure (Rs Cr), Physical Progress (%);
grouped by Ministry → Sector. NO free-text remarks field exists.

`TODO(confirm-from-data)`: does the *actual* CUF export we hold have MORE fields than
the public PDF surfaces (milestones, contractor, land acquisition)? List any extras.

## C. Questions Phase 4 EDA MUST answer (each becomes a sourced number)
1. `TODO`: exact monthly coverage — do we have all 19 months? which are missing?
2. `TODO`: format consistency — any month with a different table structure / field defs?
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
April 2026 totals to reproduce exactly after parsing:
- 1,981 ongoing projects; 17 ministries; 22 sectors
- Original cost ≈ Rs 37.13 lakh cr; Revised ≈ Rs 42.78 lakh cr; Cum. exp ≈ Rs 20.36 lakh cr
If the parser doesn't reproduce these, the parser is wrong — fix before trusting any month.

## GATE: Phase 5 may not begin while any Section-C TODO is unresolved.
Run: `grep -rn "confirm-from-data" docs/03_DATA_INVENTORY.md`

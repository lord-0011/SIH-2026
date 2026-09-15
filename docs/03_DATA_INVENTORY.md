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
3. **CONFIRMED**: observations-per-project distribution (computed by `src/eda/eda_gate.py` off `data/processed/panel.parquet`):
   - **All 2,243 canonical projects**:
     - $\ge 3$ observed months: **2,138 projects (95.32%)**
     - $\ge 6$ observed months: **1,948 projects (86.85%)**
     - $\ge 9$ observed months: **768 projects (34.24%)**
     - $\ge 12$ observed months: **639 projects (28.49%)**
     - Exactly 13 observed months: **557 projects (24.83%)**
     - Median observed months: **8.0 months** (p10=4, p25=6, p50=8, p75=12, p90=13).
   - **Baseline cohort (902 projects first observed in Jul/Aug 2025)**:
     - $\ge 3$ observed months: **855 (94.79%)**
     - $\ge 6$ observed months: **805 (89.25%)**
     - $\ge 9$ observed months: **768 (85.14%)**
     - $\ge 12$ observed months: **639 (70.84%)**
     - Median observed months: **13.0 months**.
   - **Mid-window arrivals (1,341 projects arriving Dec 2025+)**:
     - $\ge 3$ observed months: **1,283 (95.67%)**
     - $\ge 6$ observed months: **1,143 (85.23%)**
     - $\ge 9$ observed months: **0 (0.00%)** — *by construction*, since the window has only 8 months remaining after Dec 2025 onboarding.
     - Median observed months: **7.0 months**.
   - **Conclusion**: 86.85% of projects have $\ge 6$ observed months, providing strong support for trailing 3-month rolling trend features plus forward-looking windowed labels.
4. **CONFIRMED**: realized-outcome count — exactly **259** gross completed project records across 11 modern months' Table 3 ("Completed Projects During Month") tables (6 + 6 + 13 + 17 + 3 + 9 + 25 + 9 + 16 + 130 + 25 = 259).
   - **Reversible completion finding**: Direct cross-month join (`ongoing_month > completion_month`) identified exactly **1** reversible project (`705635`, Southern Railway, Trivandrum-Kanyakumari; completed in Feb 2026, reappeared ongoing Mar–Jul 2026).
   - **Clean irreversible validation anchor**: exactly **258** completed projects (100% satisfying $\text{Completed} \land \text{Never seen ongoing afterward}$).
   - **Outcomes breakdown (N = 258)**:
     - Cost overrun (>0 Cr): **97 projects (37.60%)**
     - Schedule slip (>0 months): **92 projects (35.66%)** (22 with unpopulated/dash dates in Table 3)
     - Both cost overrun & schedule slip: **31 projects (12.02%)**
     - Neither (on-time and on-budget): **100 projects (38.76%)**
   - **Concentration caveat**: June 2026 alone accounts for 130 completions (121 of which are NHAI/MoRTH road packages), meaning the effective independent validation sample across all other months and sectors is **128 projects** (or 137 projects outside June road packages).
5. **CONFIRMED**: entity stability & canonical resolution:
   - `project_code` is **100.00% populated** across all 18,601 ongoing records, 259 completed records, and 736 newly added records (0 null project codes).
   - **Per-month uniqueness**: 100% unique per month (`nunique(project_code) == len(df)` across all 13 months; 0 intra-month duplicates).
   - **Cross-month stability**: **0 cross-month renames** (`(legacy_ocms_code, project_name)` maps to multiple `project_code`s: exactly 0).
   - **Corpus-wide distinct canonical projects**: exactly **2,243** distinct projects across the 13-month window.
   - **Umbrella legacy codes reconciled**: exactly **26** single-month concurrent umbrella legacy codes (e.g. NHAI corridor EPC package splits); exactly **30** corpus-wide umbrella legacy codes. The 4-code difference (`N12000133`, `N12000134`, `N12000135`, `N22000602`) reflects source reporting swaps across distinct physical steel/rail projects (Bokaro, Bhilai, Battery Cyclon, Dallirajhara) between Feb and Mar 2026, while `project_code`s remained 100% stable.
   - **Mid-window arrivals (>= 2025-12)**: **1,341** total projects (1,187 MoRTH + 154 other ministries). All 1,341 have `trajectory_anchor_date` populated from their actual sanction/start date for STEP_04 trajectory anchoring.
6. **CONFIRMED**: usable rows per candidate horizon (computed by `src/eda/eda_gate.py` applying Scheme A exclusion rule: row at month $T$ is usable only if project has $\ge N$ future observed months after $T$):
   - **$N = 3$ months (Optimal / Viable)**:
     - Usable labeled rows: **12,300 rows** (65.2% of panel).
     - Cost-risk positives ($\Delta \text{cost\_escalation} > 0\%$): **237 rows (1.93% class rate)**; at $\ge 5\%$: **188 rows (1.53%)**.
     - Schedule-risk positives ($\Delta \text{delay} \ge 1\text{ mo}$): **4,531 rows (36.84% class rate)**; at $\ge 3\text{ mo}$: **3,933 rows (31.98%)**; at $\ge 6\text{ mo}$: **2,708 rows (22.02%)**.
   - **$N = 6$ months (Secondary / Restricted)**:
     - Usable labeled rows: **6,258 rows** (33.2% of panel).
     - Cost-risk positives ($>0\%$): **272 rows (4.35%)**; at $\ge 5\%$: **220 rows (3.52%)**.
     - Schedule-risk positives ($\ge 1\text{ mo}$): **2,638 rows (42.15%)**; at $\ge 3\text{ mo}$: **2,510 rows (40.11%)**.
   - **$N = 12$ months (Non-viable)**:
     - Usable labeled rows: **557 rows** (2.95% of panel; restricted exclusively to baseline projects from July 2025; completely drops all 1,341 mid-window arrivals).
     - Cost-risk positives: **115 rows (20.65%)**.
     - Schedule-risk positives ($\ge 1\text{ mo}$): **265 rows (47.58%)**.
   - **Structural Break Finding for Target Fields**:
     - *Cost revision downward spike*: Dec 2025 onwards, downward cost revisions jump from 4.25% to ~17% due to MoRTH road packages tendering below initial administrative estimates.
     - *Revised completion date reporting surge*: In March 2026, `revised_completion_date` population jumps from 50.56% to **82.12%** (+31.56 percentage points) as MoSPI systematically backfilled revised target dates for 616 projects.
   - **Target Recommendation**: Recommend **Schedule-Risk** at **Horizon $N = 3$ months** as the primary prediction target for Level 1 MVP. Schedule revisions occur actively and continuously with balanced class distributions (32%–37%), whereas cost escalation is rare (1.9% at N=3) because cost revisions require formal cabinet/CCEA approvals.
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

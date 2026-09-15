# SIH 2026 — Problem Statement 26103
# Master Engineering Document: PAIMANA Predictive Infrastructure Risk Platform

**Prepared for:** Smart India Hackathon 2026 — Problem Statement ID 26103
**Sponsoring Organization:** Ministry of Statistics and Programme Implementation (MoSPI), Data Informatics & Innovation Division (DIID)
**Category:** Software | **Theme:** Smart Automation — AI for Infrastructure Monitoring
**Document Type:** Full engineering specification, phase breakdown, and requirements document
**Status:** Pre-development design document (no code has been written yet; this document precedes implementation)

---

## Table of Contents

1. Executive Summary
2. The Sponsoring Ecosystem: MoSPI, IPMD, OCMS, and PAIMANA
3. Problem Statement 26103 — Full Restatement and Interpretation
4. Distinguishing Official Requirements from Our Design Choices
5. Smart India Hackathon 2026 — Official Process Phases and How Our Work Maps to Them
6. Data Landscape: What We Have, What We Don't, and What We Must Determine
7. Full Requirement List (Functional and Non-Functional)
8. System Architecture — End to End
9. Project Development Phases (Phase 0 through Phase 18) — Deep Explanation of Each
10. Data Schema and Longitudinal Dataset Design
11. Feature Engineering Catalogue
12. Label Design, Prediction Targets, and the Censoring Problem
13. Modeling Strategy: Statistical Baselines vs Machine Learning
14. Evaluation Framework
15. Project Risk Score Design
16. Early Warning System Design
17. Explainability Layer
18. LLM Project Intelligence Assistant
19. Dashboard Specification (Three Levels + Watchlist)
20. Backend Architecture and APIs
21. Technology Stack and Justification
22. Data Quality, Governance, and Validation Rules
23. Risks, Limitations, and Honest Constraints
24. MVP Definition vs High-End Version
25. Hardware and Local Development Plan
26. Team Execution Plan and SIH Submission Timeline
27. Glossary of Terms
28. Appendix: Open Questions Requiring Data Inspection

---

## 1. Executive Summary

The Ministry of Statistics and Programme Implementation (MoSPI) operates a national infrastructure project monitoring system called PAIMANA (Project Assessment, Infrastructure Monitoring and Analytics for Nation-building), the modernized successor to the two-decade-old OCMS (Online Computerised Monitoring System). PAIMANA tracks nearly 2,000 ongoing Central Sector Infrastructure Projects, each costing Rs. 150 crore or more, across 17 Central Ministries/Departments and 22 infrastructure sectors, representing an original project cost base of approximately Rs. 37.13 lakh crore and a revised cost base of approximately Rs. 42.78 lakh crore, with roughly Rs. 20.36 lakh crore already spent as of the April 2026 reporting period.

PAIMANA today is a **descriptive** system. It can answer "what has happened" — current cost, current expenditure, current physical progress, current status — extremely well, because it is fed by monthly structured submissions from implementing agencies through role-based access and APIs on the IPM portal. What it cannot yet do is answer "what is likely to happen" — which of these ~2,000 projects is quietly heading toward a cost overrun or a schedule slip *before* that overrun or slip becomes visible in the numbers everyone already tracks.

Problem Statement 26103 asks participating teams to close that gap: to build a system that moves PAIMANA from descriptive monitoring toward **predictive and prescriptive monitoring** — predicting cost overruns, predicting schedule/time overruns, scoring project risk, generating early warnings, explaining the reasons behind each warning, benchmarking similar projects against each other, and exposing all of this through both a human-facing dashboard and a natural-language assistant, without ever letting that assistant invent facts about a project.

Our approach is built around one central design discipline that a large share of competing teams are likely to overlook: **our supervised outcome labels are heavily right-censored.** Because we are only able to observe roughly nineteen months of monthly project snapshots (Q1 2025 through July 2026), and because the vast majority of the ~2,000 tracked projects have not yet reached completion within that window, we cannot honestly claim to know the "final" cost overrun or "final" schedule delay for most projects in our dataset — we only know their status as of the last month we observed them. A system that pretends otherwise will produce a dashboard that looks confident and is actually built on a statistically invalid labeling scheme. Our entire label design, evaluation strategy, and even our headline claims to the judges are built around treating this honestly: using a genuinely realized-outcome subset (projects that completed *during* our observation window, for which we have true before/after figures) for rigorous validation, and using a windowed, near-term "early warning" formulation — not a lifetime-outcome formulation — for the majority of projects that are still ongoing.

This document is the complete pre-coding design specification for the project: what MoSPI is actually asking for, what we are choosing to build beyond the letter of the problem statement, the full technical architecture, every development phase in depth, the data schema, the feature catalogue, the modeling and validation strategy, the risk-scoring and early-warning design, the explainability and LLM-assistant design, the dashboard specification, the technology stack and why each component was chosen, the data quality rules we will enforce, the honest limitations of what we can claim, the MVP versus high-end scope split, and the execution timeline mapped against the actual Smart India Hackathon 2026 calendar.

---

## 2. The Sponsoring Ecosystem: MoSPI, IPMD, OCMS, and PAIMANA

### 2.1 Ministry of Statistics and Programme Implementation (MoSPI)

MoSPI is the central government ministry responsible for national statistical coordination, macroeconomic data (GDP, national accounts, price indices), survey-based statistics, and — relevant to this project — programme and project monitoring for large infrastructure investments made across other central ministries. MoSPI does not itself build roads, railways, or airports; instead, it operates as an oversight and monitoring authority that other ministries and their implementing agencies report into. This matters architecturally: our system is being designed for an **oversight body**, not an **executing body**. The primary user of our dashboard is not the engineer building an airport terminal — it is a central analyst or decision-maker who needs to know, across the entire national infrastructure portfolio, which handful of projects (out of nearly 2,000) deserve their limited attention this month. Every design decision in this document — the emphasis on ranking and triage over precise point predictions, the emphasis on explanation over raw scores, the emphasis on trend over snapshot — follows from this single fact about who the end user actually is.

### 2.2 Infrastructure & Project Monitoring Division (IPMD)

IPMD is the specific division inside MoSPI responsible for monitoring Central Sector Infrastructure Projects costing Rs. 150 crore and above. This threshold is not incidental — it defines the entire scope of the dataset we will work with. Projects below this cost threshold are simply outside PAIMANA's universe and outside the scope of this problem statement, no matter how operationally important they might be. Our system's insights, therefore, can only ever speak to the behavior of large-scale, high-cost infrastructure projects — a fact worth stating plainly to SIH judges rather than implying our findings generalize to all government projects.

### 2.3 From OCMS to PAIMANA

OCMS (Online Computerised Monitoring System), operational since 2006, was the original monitoring system and accumulated close to two decades of historical project data. PAIMANA is its modernized successor — a web-based integrated project-monitoring platform and a national repository of infrastructure project information, into which Ministries, Departments, and Implementing Agencies submit monthly updates through role-based access and APIs (the "IPM portal," indiainvestmentgrid.gov.in, is the submission-side interface referenced in the April 2026 Flash Report).

This history matters for two concrete reasons in our design:

First, it explains why our project-level records carry **three separate identifiers** — Project Code (the current PAIMANA-era code), Legacy OCMS Code, and PMGID — rather than one clean primary key. This is a direct artifact of the OCMS-to-PAIMANA migration: some projects retained continuity of identity across systems and carry a Legacy OCMS Code, some do not (shown as "-" in the source data), and PMGID appears to be a third, possibly cross-system identifier used elsewhere in government (likely the PRAGATI/PM Gati Shakti ecosystem — this needs confirmation, not assumption). Any entity-matching logic we build must treat all three as candidate join keys and resolve conflicts explicitly rather than trusting a single field.

Second, it is the reason the problem statement itself repeatedly distinguishes between "data theoretically available through nearly two decades of OCMS/PAIMANA history" and "data actually available to our team." The hackathon problem statement invites teams to imagine what could be done with the full historical archive, but our practical dataset is only the roughly nineteen-month window we actually possess (Q1 2025 through July 2026). This document treats that distinction as load-bearing, not decorative — see Section 6 and Section 12.

### 2.4 What PAIMANA Captures Today (Descriptive Layer)

Based on direct inspection of the April 2026 PAIMANA Flash Report (163 pages, six structured tables), PAIMANA today captures, per project, per monthly reporting cycle:

- Project identity: Project Name, Implementing Agency, Project Code, Legacy OCMS Code, PMGID
- Administrative context: Ministry/Department, Sector (e.g., Aviation & Aviation Infrastructure, Railways, Roads & Highways, Water Resources, Urban Public Transport, Energy, Coal, Steel, Healthcare, Education, Real Estate), State (including multi-state projects)
- Timeline fields: Date of Approval, Start Date, Original/Target Date of Completion (DoC), Revised DoC
- Financial fields: Original Cost, Revised Cost (both in Rs. Crore), Cumulative Expenditure (Rs. Crore)
- Progress field: Physical Progress (%)
- Roll-up/aggregate tables: Ministry-wise ongoing project totals, State-wise ongoing project totals, Completed Projects (during the reporting month, with actual completion dates and final costs), Newly Added Projects (during the reporting month), and a special North Eastern Region roll-up

This is a genuinely rich structured dataset — richer than a bare aggregate statistics table — but it is entirely **descriptive**: every field describes a state of affairs as observed, none of it is a prediction, a risk score, or a forward-looking signal. That gap between "rich descriptive data" and "zero predictive layer" is precisely the gap Problem Statement 26103 asks us to fill.


## 10. Data Schema and Longitudinal Dataset Design

### 10.1 Raw Source Schema (as confirmed from the April 2026 Flash Report, Table 6)

| Field | Type | Notes |
|---|---|---|
| Sl.No | integer | Report-local row number; not stable across months, never used as an identifier |
| Project Name | text | Free text, can be long and multi-line in the source PDF |
| Implementing Agency | text | Appears in parentheses beneath Project Name |
| Project Code | string | Primary current-era identifier; can be blank/absent for some records |
| Legacy OCMS Code | string | Often "-" (absent); populated for projects with pre-PAIMANA history |
| PMGID | string | Third identifier system; population rate to be confirmed in Phase 4 EDA |
| State | text/categorical | Multi-state projects list multiple states in one field — requires explicit multi-valued handling, not naive single-category treatment |
| Date of Approval | MM/YYYY | |
| Start Date | MM/YYYY | Shown in parentheses beneath Date of Approval |
| Original/Target Date of Completion (DoC) | MM/YYYY | |
| Revised DoC | MM/YYYY | Shown in parentheses beneath Original DoC; "-" if no revision has occurred |
| Original Cost | numeric, Rs. Crore | |
| Revised Cost | numeric, Rs. Crore | Shown in parentheses beneath Original Cost |
| Cumulative Expenditure | numeric, Rs. Crore | |
| Physical Progress | numeric, percent (0-100) | |
| Ministry / Sector | categorical (hierarchical) | Encoded structurally via section headers in the source table, not as an explicit per-row column — must be carried down/forward-filled correctly during parsing |

### 10.2 Additional Source Tables (confirmed)

- **Completed Projects During Month** (Table 3): adds Actual Date of Completion alongside Original/Target DoC and Revised DoC, and final Original/Revised Cost and Cumulative Expenditure at completion — this is the realized-outcome source described in Section 12.
- **Newly Added Projects During Month** (Table 4): gives a project's baseline figures at first entry into PAIMANA, useful for confirming a project's true starting snapshot.
- **Ministry-wise / State-wise Ongoing Projects** (Tables 1, 2) and **North Eastern Region** roll-up (Table 5): aggregate cross-checks only, not used as row-level model input.

### 10.3 Target Longitudinal Schema (project-month panel)

```
project_id            -- canonical ID resolved in Phase 2 (not raw Project Code)
report_month           -- YYYY-MM, the source Flash Report month
project_name
implementing_agency
ministry
sector
state                   -- normalized to a list/array type to support multi-state projects
project_size_band       -- derived: Mega (>= Rs.1000cr original cost) vs Major (< Rs.1000cr), per source-report convention
date_of_approval
start_date
original_completion_date
revised_completion_date        -- nullable; null means "no revision recorded as of this report_month"
original_cost_cr
revised_cost_cr                -- equal to original_cost_cr until first revision
cumulative_expenditure_cr
physical_progress_pct
data_quality_flag        -- e.g., "excluded_this_month_expenditure_inconsistency", populated from source report notes where available
match_confidence          -- from Phase 2 entity matching
is_completed_this_month   -- boolean, true only for rows sourced from the Completed Projects table
actual_completion_date    -- populated only when is_completed_this_month is true, or for later months once known
```

Every derived feature (Section 11) is computed as an additional column joined onto this panel, keyed on (project_id, report_month), never mutating the source-derived columns above — this separation is deliberate, so that any feature can be recomputed or corrected without re-running the ingestion/matching/panel-construction phases.

---

## 11. Feature Engineering Catalogue

Each feature below is explicitly tagged **[CUF]** if computable directly from Common Upload Form fields alone (i.e., the raw schema in Section 10.1/10.3 without any cross-project or historical computation), or **[DERIVED]** if it requires either historical/trajectory computation or cross-project context. This tagging is what makes Phase 6's and Phase 9's mandated CUF-only vs CUF+derived comparison possible.

**Cost Features**
- Cost Escalation Amount = revised_cost_cr − original_cost_cr **[CUF]**
- Cost Escalation Percentage = Cost Escalation Amount / original_cost_cr × 100 **[CUF]**
- Cost Growth Rate = change in Cost Escalation Percentage per elapsed month since approval **[DERIVED — requires trajectory]**

**Expenditure Features**
- Expenditure Utilization Ratio = cumulative_expenditure_cr / revised_cost_cr **[CUF]**
- Monthly Expenditure Change = expenditure this month − expenditure last month **[DERIVED — requires trajectory]**
- Expenditure Velocity = rolling average of Monthly Expenditure Change over trailing 3 months **[DERIVED]**
- Expenditure Acceleration = change in Expenditure Velocity over trailing 3 months **[DERIVED]**

**Physical Progress Features**
- Monthly Progress Change **[DERIVED]**
- Progress Velocity (rolling average) **[DERIVED]**
- Progress Acceleration **[DERIVED]**
- Progress Stagnation Flag = true if Progress Velocity ≈ 0 for 3+ consecutive months while project is not yet complete **[DERIVED]**

**Schedule Features**
- Planned Duration = original_completion_date − start_date **[CUF]**
- Elapsed Duration = report_month − start_date **[CUF]**
- Remaining Duration (planned) = original_completion_date − report_month **[CUF]**
- Schedule Variance = revised_completion_date − original_completion_date, where populated **[CUF]**
- Delay Duration (to date) = max(0, report_month − original_completion_date) if not yet complete **[CUF]**

**Financial-vs-Physical Features**
- Financial Progress = Expenditure Utilization Ratio (as a percent, for direct comparability with Physical Progress) **[CUF]**
- Financial-Physical Gap = Financial Progress − Physical Progress **[CUF]**
- Change in Financial-Physical Gap over trailing 3 months **[DERIVED]**

**Trajectory / Trend Features**
- Rolling averages and rolling volatility (standard deviation) of Progress Velocity, Expenditure Velocity, and the Financial-Physical Gap **[DERIVED]**
- Recent Deterioration Flag = simultaneous adverse movement in at least two of {Progress Velocity declining, Expenditure Velocity rising disproportionately to Progress Velocity, Financial-Physical Gap widening} over the trailing 2–3 months **[DERIVED]**

**Project Context Features**
- Ministry, Sector, State (as categorical encodings) **[CUF]**
- Project Size Band (Mega vs Major) **[CUF]**
- Implementing Agency (as a categorical encoding, and optionally as an agency-level historical track record — see Historical Sector/Agency Behaviour below) **[CUF for the raw field; DERIVED for the agency-level historical aggregate]**
- Historical Sector/Ministry/Agency Behaviour = aggregate historical rate of cost/schedule events observed among other projects sharing the same sector, ministry, or agency, computed only from months strictly prior to the current report_month to avoid leakage **[DERIVED]**

Every **[DERIVED]** feature above is computed strictly from information available up to and including the current report_month, per the leakage discipline in Section 12.3 — none of them are permitted to use any later month's data, even indirectly through a rolling computation that accidentally spans past the cutoff.


## 12. Label Design, Prediction Targets, and the Censoring Problem

### 12.1 The Core Problem, Stated Precisely

We hold roughly nineteen months of monthly snapshots (Q1 2025 through July 2026) of a population defined, by construction, as "currently ongoing" infrastructure projects. A project appearing in our panel as "ongoing" with no recorded cost overrun as of its most recent observed month is not the same statistical fact as a project that has been confirmed to complete without ever experiencing a cost overrun — the ongoing project may simply not have reached the point in its lifecycle where an overrun would become visible yet. Treating "no overrun observed as of the last snapshot" as equivalent to "will never have an overrun" is a textbook case of **right-censoring**, and any label scheme that ignores this will silently bias the model toward under-predicting risk, because a large share of the "negative" labels in a naively-constructed training set are not true negatives at all — they are simply "not yet resolved."

### 12.2 Two Separate, Honestly-Scoped Label Schemes

**Scheme A — Windowed near-term event label (used for the ongoing-project panel, the majority of our data).** At report_month T, using only information available up to and including T, the label asks: does this project exhibit a significant new adverse signal — a cost-escalation-percentage increase beyond a threshold determined in Phase 4's EDA, or a newly-introduced/increased schedule variance — within the window T+1 through T+N? This reframes the prediction task from "will this project ever have a problem" (which requires knowing its full future, which we do not have) to "will a new problem signal emerge soon" (which only requires observing N months forward from T, a much weaker and much more honestly satisfiable requirement given our ~19-month data window).

**Scheme B — Realized-outcome label (used only for the smaller Completed Projects subset).** For a project whose actual completion appears in one of our stacked "Completed Projects During Month" tables, the true outcome is genuinely known: actual final cost versus original cost, actual completion date versus original target date. No windowing or censoring adjustment is needed here because the outcome has actually occurred and been observed. This subset is our validation anchor — the closest thing we have to unambiguous ground truth — but it is almost certainly too small in absolute number (to be confirmed exactly in Phase 4) to serve as the primary training set for a model that needs to generalize across ~2,000 projects.

### 12.3 Leakage Discipline (Concrete Rules)

1. Any feature computed for a row at report_month T must use only source data whose own report_month is ≤ T.
2. Rolling/trend features (velocity, acceleration, rolling volatility) must be computed using only the trailing window ending at T, never a centered or forward window.
3. The label for a row at report_month T (Scheme A) must be computed only from source data in the window (T, T+N], and a row must be excluded from the training set entirely (not labeled as a negative) if fewer than N future months are actually observed for that project — a project that hasn't been tracked long enough after T to know the Scheme A answer is not a confirmed negative, it is unknown, and must be treated as unknown.
4. Historical aggregate features (e.g., sector-level historical event rate) must be computed using only projects' outcomes from strictly prior months relative to the row being featurized — never including the current row's own future in its own contextual aggregate.
5. Train/validation/test splits (Phase 9) must be temporal (rolling-origin), never random k-fold, for exactly the reasons in rule 1–4: random folds would let information from a "future" month leak into a model that is validated as if it only knew the "past."

### 12.4 Sample Size Honesty

Given ~19 months of data and a required forward window of N months for Scheme A, the number of rows with a fully-observed label shrinks as N grows (a 12-month-forward label requires 12 months of subsequent observation, meaning only rows from the *first* 7 of our 19 months can even have a fully-resolved 12-month-forward label). This is exactly why Phase 4's EDA must report the actual usable-row count at each candidate horizon before Phase 5 commits to one — a horizon chosen for "how early warning should conceptually work" without checking whether enough rows actually support it is not a viable design decision, however reasonable it sounds on paper.

---

## 13. Modeling Strategy: Statistical Baselines vs Machine Learning

### 13.1 Why This Comparison Is a Requirement, Not a Nicety

The problem statement explicitly asks whether AI/ML provides meaningful gains over conventional statistical approaches for this specific monitoring task. Given our confirmed data volume (tens of thousands of panel rows at most, likely far fewer usable rows once Scheme A's forward-window requirement is applied), it is a live, genuinely open empirical question — not a foregone conclusion — whether a flexible model like gradient boosting meaningfully outperforms a well-specified logistic regression or hazard model on this amount of data. Assuming ML wins because the hackathon theme is "Smart Automation" would be exactly the kind of unexamined assumption this document is built to avoid.

### 13.2 Statistical Baselines

- **Logistic Regression**: the standard, well-understood classification baseline for Scheme A's windowed binary label; also useful as a linear, coefficient-interpretable model whose coefficients are themselves a (crude) explainability tool.
- **Discrete-Time Survival/Hazard Model**: the statistically correct treatment of Scheme A given censoring — models the probability of the adverse event occurring in interval T+1..T+N conditional on not having occurred by T, which is a more honest formal statement of exactly the question Scheme A is trying to answer.
- **Linear Regression** (if a continuous overrun-percentage regression target is pursued for the Scheme B realized-outcome subset, as a supplementary analysis rather than the primary deliverable, given the subset's likely small size).

### 13.3 Machine Learning Models

- **Gradient Boosting** (one library, chosen once — XGBoost, LightGBM, or CatBoost — and used consistently) as the primary ML candidate, given its strong track record on structured/tabular data of exactly this shape (mixed categorical and numeric features, moderate row count, meaningful nonlinear interactions between e.g. sector and progress-velocity).
- **Random Forest** as a secondary reference point, useful specifically because its variance behavior differs from boosting and it provides a useful sanity check on whether boosting's typically stronger performance is a genuine pattern in this data or an artifact of hyperparameter tuning on a small validation set.

### 13.4 The Comparison Itself

For each of the two targets (cost-risk, schedule-risk) and each of the two feature sets (CUF-only, CUF+derived), we report the full metric suite (Section 14) for both the best statistical model and the best ML model, evaluated on the identical temporal test split. The headline comparison MoSPI is asking for is then a direct, four-cell-per-target reading of that table: does CUF+derived beat CUF-only (does additional engineering help), and does ML beat the statistical baseline (does model flexibility help) — and, importantly, we report both answers even if one or both turn out to be "no, not meaningfully," because that is itself a genuine, useful, and expected type of finding for a data volume this size, and stating it plainly is more credible than overclaiming.


## 14. Evaluation Framework

### 14.1 Metrics and Why Each Is Included

- **ROC-AUC**: standard discrimination metric; included because it is widely understood and comparable across the statistical-vs-ML comparison, but not relied upon alone because it can be misleadingly optimistic under class imbalance.
- **PR-AUC (Precision-Recall AUC)**: given that significant cost/schedule events are very likely a minority class among all project-months, PR-AUC is a more honest measure of how well the model actually identifies the rare positive cases that matter operationally, and is weighted more heavily than ROC-AUC in our own internal judgment of model quality.
- **Calibration** (e.g., a calibration curve / Brier score): a risk score that claims "80% probability" should genuinely correspond to an ~80% empirical event rate among similarly-scored projects; this matters specifically because the Phase 11 risk score is presented to decision-makers as a probability-like number, and an uncalibrated score would be actively misleading even if its ranking (AUC) were good.
- **Early-Warning Lead Time**: for projects in the realized-outcomes (Scheme B) subset, how many months before the actual adverse event does the model's flag first trigger, on average — this is the metric most directly tied to the system's actual operational purpose (giving decision-makers time to intervene), and is arguably more important to report to judges than any single accuracy number.
- **False-Alarm Rate**: among projects flagged as high-risk, what fraction do not go on to show the adverse event within the observed window — critical because a system with a high false-alarm rate will be ignored by its human users regardless of its AUC, a well-documented failure mode of alerting systems generally.

### 14.2 Reporting Format

For every one of the sixteen evaluated configurations (2 targets × 2 feature sets × 2 model families), we report all five metrics above in one master comparison table, with the temporal test-window month range stated explicitly alongside every row, and the exact usable-row count for that configuration stated explicitly as well — since, per Section 12.4, the usable-row count can differ meaningfully across configurations depending on the forward-window requirement, and presenting metrics without their supporting sample size would understate how much statistical uncertainty surrounds each number.

---

## 15. Project Risk Score Design

### 15.1 Design Principles

The risk score is not a separate model — it is a **combination and calibration layer** over the outputs of the cost-risk and schedule-risk models already validated in Phases 7–9. Three principles govern its construction:

1. **Calibrate before combining.** Raw model outputs (particularly from gradient boosting) are not inherently well-calibrated probabilities; each underlying model's output is calibrated independently (via Platt scaling or isotonic regression, chosen based on which better fits the calibration curve observed in Phase 9) before being combined into a single score.
2. **Combine on evidence, not convention.** The relative weighting of cost-risk versus schedule-risk in the combined score is chosen by testing candidate weightings against the Scheme B realized-outcomes subset (which weighting best separates projects that were later confirmed to have overrun from those that were not), rather than assumed to be 50/50.
3. **Derive bands from the data, not round numbers.** The LOW/MEDIUM/HIGH/CRITICAL cutoffs are set using the actual empirical distribution of combined scores (e.g., quantile-based bands), then sanity-checked against the realized-outcomes subset to confirm that projects with confirmed historical overruns predominantly fall in the higher bands under the chosen cutoffs — round numbers like 30/60/80 are a starting hypothesis to test, not a design conclusion to assume.

### 15.2 What the Score Explicitly Does Not Claim

The risk score is a probability-informed triage signal, not a certified prediction of what will happen to any individual project. Given the honest sample-size and censoring constraints described throughout this document, individual project-level scores — especially for projects with few observed months — should be presented with a data-sufficiency indicator (per NFR-4), and the dashboard and any presentation to judges should describe the score as "the model's current best estimate given available history," never as a certainty.

---

## 16. Early Warning System Design

### 16.1 Trend, Not Snapshot

A project's early-warning status is determined by the trajectory of its risk score and underlying drivers over its trailing months, not by its current absolute score alone. Two projects can have an identical current risk score of 65 — one arriving there after three months of steady worsening, the other arriving there after three months of steady improvement from a much higher starting point — and these represent meaningfully different situations for a decision-maker, even though a snapshot-only system would treat them identically.

### 16.2 Trigger Logic

**MVP version:** flag if risk score has risen for at least two consecutive months, or if the financial-physical gap has widened for at least two consecutive months.

**High-end version:** a rolling-window slope test applied independently to the risk-score series, the physical-progress-velocity series, and the expenditure-velocity series, requiring adverse movement in at least two of the three simultaneously before triggering — reducing the false-alarm rate relative to any single-signal trigger, since a single volatile input (e.g., one month of unusually low reported progress, possibly itself a reporting artifact per Section 22) should not alone be sufficient to raise an alert.

### 16.3 Output Format

Every early warning is emitted with: current risk score, previous risk score (one month prior), the risk trend direction and magnitude, the specific trigger evidence (which of the two-or-three signals fired), and a pointer to the Phase 10 explainability output for that project-month — never a bare "warning: true/false" flag with no supporting evidence, per NFR-3.

---

## 17. Explainability Layer

### 17.1 Why SHAP Specifically for the High-End Version

TreeSHAP (the SHAP variant specific to tree-ensemble models like gradient boosting and random forests) is chosen because it is both theoretically grounded (Shapley values from cooperative game theory, giving each feature a fair, additive attribution of its contribution to a specific prediction) and computationally exact and efficient for tree ensembles specifically — unlike model-agnostic SHAP approximations, which are slower and only approximate. Since our primary ML model is a gradient-boosting tree ensemble, TreeSHAP is both the theoretically strongest and practically cheapest choice available, which is an unusually convenient alignment worth stating plainly rather than treating as an arbitrary tool choice.

### 17.2 MVP Fallback

If SHAP integration proves too time-consuming for the internal-hackathon deadline, the MVP fallback is: (a) the model's native global feature importances, applied as a static ranking, plus (b) a lightweight per-instance signal — for each feature, how far this project's value sits (in standard deviations, or percentile) from the training population's distribution for that feature. This does not give a true per-instance additive attribution the way SHAP does, but it gives a directionally similar "why is this project flagged" answer at a fraction of the implementation cost, and should be explicitly labeled in documentation as a simplified stand-in, not conflated with SHAP output.

### 17.3 Output Contract

For every project-month, the explainability layer outputs a ranked list of the top 3–5 features contributing to that project's current risk score, each with a plain-language description (e.g., "physical progress has stalled for 3 consecutive months" rather than a raw feature name like `progress_velocity_3mo_rolling`), consumed identically by the dashboard (Section 19) and by the LLM assistant (Section 18) — a single explainability contract serving both interfaces guarantees they can never disagree with each other about why a project is flagged.


## 18. LLM Project Intelligence Assistant

### 18.1 Scope Boundary (Restated Because It Is Easy to Violate By Accident)

The assistant's role is strictly to phrase, in natural language, answers that are otherwise fully determined by the system's own already-validated structured outputs (risk scores, rankings, driver explanations, project fields). It must never be asked to independently judge a project's risk, never be given free rein to browse raw unvalidated data, and never be permitted to answer a factual question (a cost figure, a completion date) from anything other than a direct, verifiable retrieval from the Phase 14 backend.

### 18.2 Supported Query Patterns

- **Ranking queries** ("which railway projects have the highest delay risk?") → translated into a structured call against the backend's project-listing endpoint with sector and sort-order parameters, returning the backend's own ranked list verbatim, phrased in natural language.
- **Explanation queries** ("why is Project X high risk?") → translated into a retrieval of that project's Phase 10/17 explainability output, phrased in natural language, never independently reasoned about.
- **Comparative queries** ("how does Project X compare to similar projects?") → translated into a retrieval of that project's Phase 13 benchmarking summary.
- **Factual queries** ("what is Project X's current cost?") → a direct, single-field retrieval, with a test suite (Phase 16 deliverable) asserting exact match against the backend's own data on every such query, with zero tolerance for numeric drift or paraphrase-induced error.

### 18.3 Guardrails Against Hallucination

The implementation mechanism, not merely a policy: the assistant is built using a function-calling / tool-use pattern where the underlying language model is only ever permitted to call a small, fixed set of retrieval functions against the Phase 14 API and then phrase the returned JSON in natural language — it is never given open-ended access to generate numbers, dates, or project facts from its own parameters. This is a structural guarantee, not a prompt-level instruction that could be quietly violated under different phrasing of a user's question.

### 18.4 Model Choice

Consistent with the open-source-preference direction in Section 21 and the hardware discussion in Section 25.3, the assistant can be served by either a locally-run quantized open-source model (Llama, Qwen, or Mistral family) via Ollama or llama.cpp, or a hosted API, with the explicit tradeoff stated in Section 25.3 rather than treated as a settled choice at this stage of the design.

---

## 19. Dashboard Specification (Three Levels + Watchlist)

### 19.1 Level 1 — National Overview

Purpose: give a decision-maker, in a single screen, the state of the entire ~1,981-project national portfolio. Contents: total ongoing project count; high-risk and critical-risk project counts (per the Section 15 bands); a cost-risk distribution chart and a schedule-risk distribution chart; sector, ministry, and state distribution of risk; and an overall national risk-trend line over the available monthly history.

### 19.2 Level 2 — Sector / Ministry Drill-Down

Purpose: let a decision-maker responsible for, or interested in, a specific sector or ministry (e.g., Railways) see the same categories of information scoped to that sector: total projects in scope, high-risk count, average risk score, cost-risk and schedule-risk sub-distributions, the sector's own risk trend, and its benchmarking position relative to other sectors (e.g., "Railways currently has a higher median schedule-risk score than the national average").

### 19.3 Level 3 — Project Detail

Purpose: the actionable, per-project working view. Contents: full core project fields (name, ID, ministry, sector, state, original/revised cost, expenditure, physical progress, original/revised completion dates); the overall risk score and its cost-risk/schedule-risk/execution-risk sub-components; the risk-score trend chart over the project's observed history; the ranked top contributing factors from the explainability layer; the benchmarking summary; and a plain-language "recommended area for review" synthesized from the top contributing factor (e.g., "review recent expenditure disbursement against the current progress-payment schedule").

### 19.4 Watchlist View

Purpose: the single most directly actionable view for a time-constrained reviewer — a ranked list of the projects whose risk trend is deteriorating fastest as of the most recent reporting month, computed directly from the Section 16 early-warning engine's trigger evidence, rather than simply the projects with the highest absolute score (which the National Overview already shows).

---

## 20. Backend Architecture and APIs

### 20.1 Separation of Batch Pipeline and Serving Layer

The batch pipeline (Phases 1–13: ingestion through benchmarking) runs on a monthly cadence, matching PAIMANA's own monthly update cycle, and writes its output into a set of precomputed tables (the panel dataset, the feature table, the risk-score table, the early-warning table, the explainability table, the benchmarking table). The FastAPI serving layer (Phase 14) only ever reads from these precomputed tables — it never recomputes a model prediction on the fly in response to a dashboard request — which keeps API response times fast and predictable (per NFR-7) regardless of how computationally expensive the underlying modeling pipeline is.

### 20.2 Core Endpoints

- `GET /national/summary` — Level 1 dashboard data
- `GET /sectors/{sector}/summary` and `GET /ministries/{ministry}/summary` — Level 2 dashboard data
- `GET /projects/{project_id}` — Level 3 dashboard data, including risk trend, explainability, and benchmarking in one payload
- `GET /watchlist` — Watchlist view data
- `POST /assistant/query` — the LLM assistant's internal structured-query endpoint (Section 18.2), also independently callable for testing/validation
- `GET /health` and `GET /pipeline/last-run` — operational endpoints confirming the serving layer is up and stating when the underlying batch pipeline last refreshed, so the dashboard can honestly display "data as of [month]" rather than implying real-time freshness the monthly-cadence pipeline cannot actually provide

### 20.3 Database

PostgreSQL, run via Docker for local development and any eventual deployment, storing both the raw/validated panel dataset and the precomputed pipeline output tables described above. Given the confirmed data volume (tens of thousands of panel rows, a few thousand at most in any single precomputed table), no special-case scaling consideration (partitioning, sharding, read replicas) is warranted — a single PostgreSQL instance is more than sufficient, and reaching for anything more elaborate would be unjustified engineering complexity for this data volume.


## 21. Technology Stack and Justification

| Layer | Choice | Why |
|---|---|---|
| Data processing | Python, Pandas | Standard, well-documented tooling sufficient for our confirmed small-to-moderate data volume (tens of thousands of rows); Polars/Spark would be unjustified complexity at this scale |
| PDF extraction | pdfplumber, pdftotext (poppler-utils) | Confirmed to work cleanly on the April 2026 report's text-layer PDF structure during our own inspection; no need for OCR since the source is not scanned |
| Database | PostgreSQL (via Docker) | Open-source, relationally appropriate for our structured panel/feature/output tables, and directly runnable on the development laptop |
| Statistical models | scikit-learn (logistic regression), `lifelines` or `scikit-survival` (discrete-time/hazard modeling) | Standard, well-tested open-source implementations; `lifelines` specifically supports the discrete-time survival framing central to our censoring-aware label design |
| ML models | XGBoost or LightGBM (one chosen and used consistently) | Strong, well-documented performance on structured/tabular data of this shape; native ARM64 support on Apple Silicon confirmed |
| Explainability | SHAP (TreeSHAP) | Theoretically grounded and computationally efficient specifically for tree-ensemble models, as detailed in Section 17.1 |
| Backend API | FastAPI | Lightweight, fast, auto-generates OpenAPI documentation (directly useful for Phase 18's documentation deliverable), native async support if needed for the LLM assistant's retrieval calls |
| Frontend | React, Tailwind CSS, Recharts/Plotly | Directly matches the dashboard specification in Section 19; Recharts for standard trend/distribution charts, Plotly where more complex interactive visualization is warranted |
| LLM | Open-source (Llama/Qwen/Mistral family) via Ollama/llama.cpp for local/offline capability, or a hosted API for demo reliability | See the explicit tradeoff in Section 25.3; not finalized as a single choice at this stage of the design, deliberately |
| Infrastructure | Docker, Docker Compose | Enables the one-command local deployment target in Phase 17, and runs natively on Apple Silicon |

This stack is explicitly **not finalized** in the sense that any single component could reasonably be swapped for a comparable open-source alternative if a concrete problem is discovered during implementation (e.g., if LightGBM shows an ARM64-specific issue during Phase 8, switching to XGBoost is a contained, low-cost change) — per the original problem brief's own instruction, technology choices are to be driven by demonstrated requirement, not by preference or hype, and this table should be revisited, not treated as fixed, if Phase 4's EDA reveals a data characteristic (e.g., a much larger row count than currently expected) that changes the calculus.

---

## 22. Data Quality, Governance, and Validation Rules

### 22.1 Categories of Data Quality Issue to Check For

- Missing values (distinguished, per Section 10.3's `data_quality_flag`, from genuine "not yet applicable" cases such as a project with no revised cost because no revision has occurred)
- Duplicate projects (two rows in the same month resolving, on inspection, to the same real-world project — a Phase 2 entity-matching failure mode, not merely a Phase 1 parsing artifact)
- Project ID changes across months (handled by Phase 2's multi-key matching procedure, never assumed away)
- Inconsistent project names for the same underlying project (used only as a fallback signal in Phase 2's matching procedure, never as a primary key, given known real-world variation in naming/punctuation/abbreviation)
- Date inconsistencies (e.g., a start date after an approval date, or a revised completion date before the original approval date)
- Negative values where none should exist (negative cost, negative expenditure, negative progress)
- Revised cost less than original cost (not necessarily an error — the source report itself notes this can be a genuine downward revision under reconciliation — but flagged for review rather than silently accepted or silently rejected)
- Expenditure exceeding revised cost (plausible in some real-world reporting-timing scenarios but flagged for review)
- Physical progress outside the 0–100 range
- Sudden, unexplained large changes in any numeric field month-to-month (flagged via a simple statistical outlier check, e.g., a change exceeding several standard deviations of that field's typical month-to-month change across the whole portfolio)
- Missing monthly observations for a project that is neither newly added nor completed nor explicitly excluded via a source-stated data-quality note (the genuinely ambiguous missingness case that Phase 3 must decide how to treat, project by project, rather than assume)
- Project additions and removals from month to month, cross-checked against the Newly Added Projects and Completed Projects tables specifically, so that a project's disappearance from the "ongoing" table can usually be explained (it completed, or it was explicitly excluded) rather than left as an unexplained gap

### 22.2 The Governing Principle

Per the original problem brief and preserved as a first-class rule in this document: **anomalous records are never silently deleted.** Every flagged record is resolved, in the following priority order, into one of: (a) genuine data (kept as-is), (b) a known accounting/reporting convention (kept, with an explanatory flag), (c) a reporting or system change (kept, with an explanatory flag, and cross-checked against whether it affects other projects in the same month, which would indicate a systemic rather than project-specific cause), (d) a genuine error (corrected if a confident correction is possible, otherwise excluded with an explicit, logged reason), or (e) a legitimate revision (kept as-is — e.g., a genuine downward cost revision, which is a real and informative event, not noise to be smoothed away).


## 23. Risks, Limitations, and Honest Constraints

This section exists to be read aloud to judges, not hidden from them. Stating these plainly is, per our own analysis in Sections 3.2 and 5, a differentiator rather than a weakness.

**23.1 Censoring is the central statistical risk.** Most of our ~1,981 tracked projects have not yet reached completion within our ~19-month observation window, meaning most "no overrun observed" labels are not confirmed negatives — they are simply unresolved. Our entire Section 12 label design exists to manage this honestly, but it cannot be eliminated; it can only be acknowledged, worked around via the windowed (Scheme A) formulation, and cross-checked against the smaller genuinely-resolved (Scheme B) subset.

**23.2 Sample size is a hard constraint, not a preference.** ~19 months of data, an unknown-until-Phase-4 number of projects with sufficiently long observed trajectories, and a likely small Scheme B realized-outcomes subset together mean that any single evaluated configuration's metrics (Section 14) carry real statistical uncertainty. We commit to reporting usable-row counts alongside every metric specifically so this uncertainty is visible rather than implied away by a single clean-looking number.

**23.3 Our data is not the full OCMS/PAIMANA history.** The problem statement's own background material references nearly two decades of OCMS-era historical data; we do not have access to that full archive, only the ~19-month held window. Any claim to judges about our system's predictive validity must be scoped explicitly to "based on the data available to our team," not implied to reflect validation against the full historical record.

**23.4 No unstructured/free-text signal exists in our confirmed data source.** The original idea of extracting risk signals from unstructured project remarks (from the initial problem-framing brief) is not supported by the April 2026 Flash Report's structure, which contains no free-text remarks field; this capability is dropped from scope rather than pursued without a data source.

**23.5 Reporting-format drift across the 19-month window is an open, unverified risk.** PAIMANA is a relatively recent modernization of OCMS, and it is plausible (though not confirmed) that field definitions, the Rs. 150 crore eligibility threshold's application, or table structures shifted at some point within our window. Phase 4's EDA is explicitly tasked with checking for this, and Phase 22's validation rules are designed to catch its symptoms (e.g., a sudden portfolio-wide shift in a field's distribution) even if the underlying cause is never fully confirmed.

**23.6 The LLM assistant's guardrails are only as strong as the retrieval boundary around it.** Any future extension of the assistant's capabilities (e.g., allowing it to answer more open-ended analytical questions) must preserve the strict retrieval-only architecture in Section 18.3; loosening this boundary for convenience would reintroduce exactly the hallucination risk the problem statement explicitly warns against.

**23.7 Our system evaluates infrastructure projects that are already large and already tracked.** By construction (the Rs. 150 crore PAIMANA eligibility threshold), our findings and our model's behavior say nothing about smaller government projects; this scope boundary should be stated explicitly rather than left for a judge to assume otherwise.

---

## 24. MVP Definition vs High-End Version

### 24.1 MVP (target: LPU internal hackathon, September 2026)

- Longitudinal dataset built from held Q1 2025–July 2026 data (Phases 1–4)
- A single target (cost-risk **or** schedule-risk, chosen based on which shows a larger usable-row count in Phase 4's EDA) with the Scheme A windowed label
- One statistical baseline (logistic regression) and one ML model (gradient boosting), evaluated on a temporal split, on both CUF-only and CUF+derived feature sets
- A basic 0–100 risk score with data-derived bands
- A basic two-consecutive-month-trend early-warning rule
- Feature-importance-based explainability (SHAP as a stretch if time permits)
- A working three-level dashboard (national, sector/ministry, project), without the watchlist view or benchmarking module unless time permits
- No LLM assistant required for MVP; a static "top contributing factors" text panel replaces it
- Local Docker-based deployment sufficient for a live demo

### 24.2 High-End Version (target: online evaluation and grand finale, October–December 2026)

- Both targets (cost-risk and schedule-risk)
- Full Scheme A + Scheme B dual-label design, including the discrete-time hazard/survival statistical baseline
- Full SHAP-based explainability
- Full trend-based early-warning logic (simultaneous multi-signal trigger)
- Benchmarking module
- Watchlist dashboard view
- LLM Project Intelligence Assistant with the full retrieval-constrained architecture
- Fully documented, reproducible deployment (data dictionary, model card, deployment guide)

---

## 25. Hardware and Local Development Plan

### 25.1 Confirmed Development Hardware

MacBook, Apple M5 chip, 16GB unified memory, 512GB storage.

### 25.2 Fit Against Pipeline Stages

- **PDF extraction and data cleaning (Phases 1–3):** CPU-bound, not memory-bound; trivial on this hardware.
- **The panel dataset itself:** on the order of tens of thousands of rows and a few dozen columns given our confirmed project count and observation window — comfortably fits in memory alongside everything else running on the laptop.
- **Statistical and ML model training (Phases 7–9):** neither logistic regression, hazard modeling, nor gradient boosting at this row count requires a GPU; training times are seconds to low minutes on this CPU.
- **SHAP computation (Phase 10):** TreeSHAP is efficient specifically because it is exact-and-fast for tree ensembles; feasible at this data volume without special hardware.
- **Docker (Postgres, FastAPI, React dev servers) running concurrently:** feasible within 16GB as long as other memory-heavy applications (many browser tabs, a full IDE, etc.) are not simultaneously competing for the same memory during a live demo — worth explicitly rehearsing the demo machine's exact running-application set ahead of the grand finale to avoid an avoidable memory-pressure slowdown during jury evaluation.

### 25.3 The One Real Constraint: Local LLM Serving

A quantized 7B-parameter open-source model requires roughly 4–6GB just to load, which is a meaningfully larger share of 16GB than any other single component in this stack, and directly competes with Docker and development tooling running at the same time. Two options, with an explicit tradeoff rather than a single mandated choice:

- **Local model (Ollama/llama.cpp, a 7B or smaller quantized model):** supports a genuine "runs fully offline, no external dependency" story, which is a meaningful architectural point in a government-context system, but risks noticeable slowness or memory pressure during a live demo if run alongside the rest of the stack.
- **Hosted API:** removes the local memory constraint entirely and is likely faster and more reliable for a live demo, at the cost of an external dependency that would need to be explicitly and honestly disclosed as a production consideration (data residency, availability) rather than glossed over.

Our recommendation for the actual SIH demo stages specifically: use a hosted API for the live-demo reliability, and describe local/open-source deployment as the documented production-path answer to "why open source" in the Phase 18 model card and pitch materials — this is consistent with the Section 21 stack table's own note that the LLM serving choice is deliberately left open pending a concrete decision closer to the demo date.


## 26. Team Execution Plan and SIH Submission Timeline

Mapped against the confirmed SIH 2026 calendar (Section 5):

| Period | SIH Milestone | Our Corresponding Work |
|---|---|---|
| Now – early September 2026 | Internal preparation window before LPU's internal hackathon | Phases 0–9 (problem understanding through initial statistical/ML model comparison), targeting the single-target MVP scope from Section 24.1 |
| LPU Internal Hackathon (September 2026) | Team must be shortlisted and nominated by LPU's SPOC to represent the institution | MVP dashboard (Phases 11, 14, 15) demoable end-to-end; a clear, honest presentation of the CUF-vs-derived and statistical-vs-ML findings even at MVP scale |
| October – November 2026 | Online evaluation: idea PPT and demo video pre-screening, national shortlisting | Phase 18 documentation deliverables prepared for this stage specifically (idea PPT, demo video); high-end-version work (Section 24.2) underway in parallel, prioritizing whichever components most strengthen the written/video submission (likely: the second target, and SHAP explainability, since both directly strengthen the evidentiary story a screening panel can evaluate from a video/PPT alone, ahead of components that only matter in a live setting, like the LLM assistant) |
| December 2026 | 36-hour Grand Finale at a nodal center, live jury evaluation | Full high-end version (Section 24.2) as close to complete as possible; MVP retained and rehearsed as a guaranteed-working fallback demo path in case any high-end component is unstable under live conditions; team logistics per the confirmed 6-member, minimum-1-female team composition rule (Section 5), to be reconfirmed against LPU's own SIH circular |

### 26.1 Sequencing Discipline

Because Phases 0–5 (problem understanding through target/horizon definition) are entirely prerequisite to every later phase, no team member should begin Phase 6 (feature engineering) work, let alone Phase 7/8 (modeling) work, until Phase 4's EDA has produced actual numbers answering the six open questions in Section 6.2 and Phase 5 has finalized the label specification in writing. This is the single most important process discipline in this entire plan: it is far cheaper to spend an extra few days confirming data feasibility in Phase 4 than to discover a fatal labeling flaw after Phase 8 has already produced a model.

---

## 27. Glossary of Terms

- **PAIMANA** — Project Assessment, Infrastructure Monitoring and Analytics for Nation-building; MoSPI's current web-based project-monitoring platform.
- **OCMS** — Online Computerised Monitoring System; PAIMANA's pre-modernization predecessor, operational since 2006.
- **IPMD** — Infrastructure & Project Monitoring Division, the MoSPI division operating PAIMANA.
- **CUF** — Common Upload Form; the standard monthly data-submission form used by implementing agencies to feed project data into PAIMANA.
- **DoC** — Date of Completion (Original/Target DoC and Revised DoC are distinct fields in the source data).
- **PMGID** — a project identifier field present in the source data, believed but not yet confirmed to relate to the PRAGATI/PM Gati Shakti government project-tracking ecosystem; treated in this document strictly as an empirically observed candidate join key, not as an assumed-understood system.
- **Right-Censoring** — the statistical condition in which the true outcome of an observation (here, a project's eventual cost/schedule outcome) is unknown because the observation period ended before the outcome occurred or failed to occur; the central statistical constraint this entire design is built around (Section 12).
- **Mega vs Major Project** — a size classification observed directly in the source report's own legend: Mega if original cost ≥ Rs. 1,000 crore, Major if below that threshold (both are already within the broader Rs. 150 crore-and-above PAIMANA eligibility population).
- **TreeSHAP** — the SHAP (SHapley Additive exPlanations) variant specific to tree-ensemble models, used for per-instance explainability (Section 17).
- **Scheme A / Scheme B labels** — this document's own naming (not an official MoSPI term) for, respectively, the windowed near-term-event label used across the full ongoing-project panel, and the realized-outcome label used only for the smaller Completed Projects subset (Section 12.2).

---

## 28. Appendix: Open Questions Requiring Data Inspection

Restated from Section 6.2 for visibility as a standalone checklist, since these are the gating items for Phase 4 and, transitively, for every phase after it:

1. Exact monthly coverage and format consistency of the held Q1 2025–July 2026 data (separate Flash-Report-equivalent extracts vs. a single merged file; consistent table structure across all 19 months vs. any mid-window format revision).
2. Per-project observation depth across the 19-month window (how many projects have long-enough trajectories to support trend/velocity features and a meaningful forward-window label).
3. Total realized-outcome (Scheme B) sample size across all 19 months' stacked Completed Projects tables.
4. Entity-matching stability across 19 months (Project Code change frequency; Legacy OCMS Code and PMGID population rate across the full window, not just the single April snapshot inspected so far).
5. Any structural/format drift in field definitions, units, or the Rs. 150 crore eligibility rule's application across the 19-month window.
6. The precise, complete Common Upload Form field list as actually available to our team, as distinct from the subset of fields that happen to be surfaced in the public-facing Flash Report PDF we have directly inspected so far.

No phase past Phase 4 in this document should be treated as final until these six items are answered with real numbers from the actual held dataset, rather than the reasonable-but-unconfirmed assumptions this document has necessarily used in their place.

---

*End of document.*

## 3. Problem Statement 26103 — Full Restatement and Interpretation

**Official Title:** "Use case on web-based integrated project-monitoring platform"
**Problem Statement ID:** 26103
**Organization:** Ministry of Statistics and Programme Implementation (MoSPI)
**Department:** Data Informatics & Innovation Division (DIID)
**Category:** Software
**Theme:** Smart Automation (broader theme: "AI for Infrastructure Monitoring")

### 3.1 What the Problem Statement Says, In Its Own Terms

The official problem statement background establishes that IPMD/MoSPI monitors Central Sector Infrastructure Projects (Rs. 150 crore and above) across infrastructure ministries; that this monitoring has existed since 2006 (OCMS) and was modernized into PAIMANA; and that PAIMANA is updated monthly through role-based access and APIs, capturing cost, expenditure, timelines, progress, milestones, agencies, status, and other project-monitoring fields.

It then states the core problem in almost these exact terms: the existing framework provides strong *descriptive* monitoring — it can tell decision-makers what has already happened — but there is no mechanism to move from *descriptive* monitoring ("what has happened") to *predictive* monitoring ("what is likely to happen") and, ideally, to *prescriptive* / decision-support monitoring ("what should decision-makers investigate or prioritize"). The system we are asked to design should identify, before they fully materialize, projects likely to experience: (1) cost escalation/cost overruns, (2) schedule/time overruns, (3) implementation risks, (4) milestone delays, and (5) other emerging execution problems.

The listed **possible** (explicitly stated as indicative and non-exhaustive) outcomes are:

  a. Cost Overrun Prediction Model
  b. Time Overrun Prediction Model
  c. Project Risk Scoring Framework
  d. Early Warning Alert System
  e. Benchmarking and Comparative Analytics Module
  f. Cost Escalation Driver Analysis Module
  g. AI-powered Monitoring Dashboard
  h. LLM-enabled Project Intelligence Assistant
  i. Documentation and deployment framework

The problem statement also explicitly requires us to assess predictive performance using the fields that already exist in the **Common Upload Form (CUF)** — the standard monthly submission form implementing agencies use to feed PAIMANA — both on their own and combined with additional derived/external variables, and to compare statistical methods against machine learning methods to determine whether AI/ML genuinely adds value over simpler techniques, rather than assuming it does because the theme says "Smart Automation."

### 3.2 Our Interpretation, Stated Plainly

Read as a whole, Problem Statement 26103 is not asking for a single predictive model bolted onto PAIMANA. It is asking for an **evidence-based decision-support layer** whose primary duty is triage: out of nearly 2,000 tracked projects, tell a time-constrained decision-maker which handful deserve attention this month, why, and how confident the system is in that judgment — and to do so using the data MoSPI already collects (the CUF fields), with an honest, tested answer to whether additional derived signals or more sophisticated modeling are actually worth the added complexity.

We interpret "predictive monitoring" as meaning: given everything known about a project up to the current reporting month, estimate the probability that it will show a significant new cost-escalation or schedule-slip signal in the near future. We interpret "prescriptive monitoring" as meaning: not just a number, but a ranked, explained, trend-aware output that tells a reviewer *where to look first* and *why* — this is the difference between a model output and a decision-support system, and it is the difference our design is built around.

### 3.3 What Our System Is, In One Sentence

**A system that ingests PAIMANA's existing monthly project-monitoring submissions, reconstructs each project's history as a time-ordered trajectory rather than a single snapshot, estimates — using both a simple statistical baseline and a machine learning model, and using only CUF-derived and CUF-adjacent fields — the near-term probability that each ongoing project will develop a significant cost or schedule problem, converts that estimate into an explained, trend-aware risk score, surfaces it through a three-level dashboard and a natural-language assistant that answers questions strictly from the system's own validated outputs, and is honest, in its own presentation to judges, about exactly how much of its dataset is genuinely resolved outcome versus still-open and unresolved.**

### 3.4 What We Are Producing (Concrete Deliverables)

By the end of development, we will have produced:

1. A cleaned, matched, longitudinal **project-month panel dataset** built from the raw monthly PAIMANA Flash Report data we hold (Q1 2025 – July 2026), with an explicit, auditable entity-matching layer resolving Project Code / Legacy OCMS Code / PMGID inconsistencies across months.
2. A separate, smaller **realized-outcomes dataset** built by stacking every month's "Completed Projects During Month" table, giving true before/after cost and schedule figures for projects that actually finished within our observation window — used for honest validation rather than for large-scale training.
3. A documented **feature engineering pipeline** producing cost, expenditure, physical-progress, schedule, financial-physical-gap, and trajectory/trend features per project per month, with an explicit, versioned separation between "CUF-only" features and "CUF + derived" features to satisfy the problem statement's explicit comparison requirement.
4. Two trained prediction pathways per target (cost-risk and schedule-risk): one statistical baseline (logistic regression, and a discrete-time survival/hazard model as the more rigorous statistical treatment of censoring) and one machine learning model (gradient boosting), each evaluated on a temporally-honest split, each evaluated separately on CUF-only vs CUF+derived features.
5. A **Project Risk Score** (0–100, with data-derived rather than arbitrary thresholds) combining cost-risk, schedule-risk, and a small number of validated execution-risk signals, computed monthly per project.
6. An **Early Warning Engine** that tracks each project's risk-score trajectory over the trailing months and flags genuine *deterioration*, not merely a high absolute score.
7. An **Explainability Layer** producing SHAP-based (or feature-importance-based, if time-constrained) per-project, per-month driver explanations.
8. A **Benchmarking Module** comparing a project's key ratios (expenditure-to-progress, cost growth rate) against peers in the same sector/ministry/size band.
9. A **backend API** (FastAPI) serving all of the above to a **three-level web dashboard** (national → sector/ministry → project, plus a watchlist view) and to an **LLM-enabled Project Intelligence Assistant** that answers natural-language questions strictly by querying the system's own validated, structured outputs — never inventing project facts.
10. Full documentation: this design document, a data dictionary, a model card describing evaluation results and honest limitations, and a deployment/setup guide.

---

## 4. Distinguishing Official Requirements from Our Design Choices

This distinction is preserved deliberately and consistently throughout this document, because presenting our implementation choices as if MoSPI had mandated them would be both technically dishonest and strategically weaker in front of judges, who are likely to probe exactly this boundary.

**Explicitly required by the problem statement (MoSPI's own words):**
- Move from descriptive to predictive/prescriptive monitoring of Central Sector Infrastructure Projects.
- Address cost overruns, schedule/time overruns, implementation risk, milestone delay, and other emerging execution problems.
- Evaluate predictive performance using existing Common Upload Form (CUF) fields, and separately assess whether additional derived/external variables improve on CUF-only performance.
- Compare statistical approaches against machine learning approaches to justify (or not justify) the use of AI/ML.
- The nine listed possible outcomes (cost overrun model, time overrun model, risk scoring framework, early warning system, benchmarking module, cost-escalation driver-analysis module, AI-powered dashboard, LLM-enabled assistant, documentation/deployment) — explicitly flagged by MoSPI itself as indicative and non-exhaustive, not a mandatory checklist.

**Our own implementation choices, not requirements from MoSPI:**
- SHAP specifically as the explainability method (any faithful explanation method would satisfy the requirement).
- XGBoost/LightGBM/CatBoost as the specific gradient-boosting library.
- A 6-month or 12-month prediction horizon for the "early warning" window.
- A 0–100 numeric risk score with LOW/MEDIUM/HIGH/CRITICAL bands.
- The specific project-month longitudinal schema and its exact column set.
- The specific dashboard layout (three levels plus a watchlist).
- The specific choice of open-source LLM family (Llama/Qwen/Mistral) versus a hosted API.
- The decision to treat censoring via a hazard-style windowed label rather than attempting to force a lifetime-outcome label onto incomplete data.

Every one of these implementation choices is defensible and will be defended on its technical merits in this document — but none of them should ever be presented to judges as something MoSPI itself specified.


## 5. Smart India Hackathon 2026 — Official Process Phases and How Our Work Maps to Them

SIH 2026 is organized by the Ministry of Education's Innovation Cell (MIC) and AICTE. Based on the official published timeline, the hackathon proceeds through the following stages:

| Calendar Period | Official SIH Activity | What We Must Have Ready |
|---|---|---|
| August 2026 | Official launch, SPOC (Single Point of Contact) registration closes, problem statements released to institutions | Problem statement selected and understood (done — this document is that step); team formed |
| September 2026 | Institutions conduct **internal hackathons** to shortlist and nominate teams to represent the institution nationally | A working prototype and a presentation-ready idea sufficient to win LPU's internal round: this is where our **MVP** (Section 24) must exist in demonstrable form |
| October – November 2026 | **Online evaluation**: pre-screening of idea PPTs by an expert panel, shortlisting of national finalists | A polished idea PPT/pitch deck, a demo video, and — critically — a system that can withstand scrutiny on the specific technical claims in this document (censoring treatment, CUF-vs-derived comparison, statistical-vs-ML comparison) |
| December 2026 | **Grand Finale**: a 36-hour continuous on-site hackathon at a nodal center, in front of a jury, alongside other national finalist teams | A fully working, demo-ready, live system — this is where the **high-end version** (Section 24) should be as close to complete as possible, with the MVP as an always-working fallback |

Team composition rules to keep in mind for internal planning (per current published SIH rules): teams are typically fixed at six student members from the same institution, with a minimum of one female team member mandatory, and up to two faculty or industry mentors permitted. Cross-department membership within the same institution is allowed. (These are current published rules as of this document's preparation and should be re-confirmed against LPU's own SIH internal-hackathon circular before finalizing the team, since institution-level administration of SIH details can vary slightly.)

### 5.1 Why This Timeline Changes Our Engineering Priorities

The single most important consequence of this calendar is that **the internal hackathon in September 2026 requires a working, demonstrable MVP well before the "real" SIH evaluation even begins.** This means our Phase 0–18 breakdown (Section 9) cannot be planned as one long uninterrupted eighteen-phase march toward a final product; it must be planned as two nested cycles:

- **Cycle 1 (target: internal hackathon, September 2026):** Phases 0 through roughly Phase 12–14 compressed into a working, narrower-scope MVP — one target (either cost-risk or schedule-risk, not necessarily both), one statistical baseline, one ML model, a basic risk score, and a minimal but real dashboard. This must be good enough to win the internal round on its own.
- **Cycle 2 (target: online evaluation and grand finale, October 2026 – December 2026):** Expansion to the full eighteen-phase scope — both targets, the hazard-style censoring treatment fully implemented, SHAP explainability, the benchmarking module, the early-warning trend logic, and the LLM assistant.

This two-cycle structure is reflected directly in the phase-by-phase breakdown in Section 9, where each phase is marked as **MVP-critical** or **high-end/stretch**.


## 6. Data Landscape: What We Have, What We Don't, and What We Must Determine

### 6.1 What We Have Confirmed, By Direct Inspection

We have directly inspected the April 2026 PAIMANA Flash Report (a 163-page PDF, text-layer present, generated via Microsoft Reporting Services and subsequently processed through iLovePDF). This inspection — not assumption — confirms the following:

- **1,981 ongoing projects** as of April 2026, across 17 Central Ministries/Departments and 22 sectors, with an aggregate original cost of approximately Rs. 37,12,662 crore, an aggregate revised cost of approximately Rs. 42,78,402 crore, and cumulative expenditure of approximately Rs. 20,36,107 crore (47.59% of revised cost).
- A per-project record structure (Table 6, "All Ongoing Projects") containing: Sl.No, Project Name, Implementing Agency, Project Code, Legacy OCMS Code, PMGID, State (including multi-state entries), Date of Approval, Start Date, Original/Target Date of Completion, Revised Date of Completion, Original Cost (Rs. Crore), Revised Cost (Rs. Crore), Cumulative Expenditure (Rs. Crore), and Physical Progress (%). Records are grouped hierarchically by Ministry, then by Sector.
- A **"Completed Projects During Month" table** (Table 3) — a small monthly list (single digits to low tens of projects for April 2026) giving each completed project's actual date of completion alongside its original/target date of completion, revised date of completion, and final cost figures. This table is the single most valuable discovery for our labeling strategy (see Section 12) because it is the only place in the source data where a **true, non-censored, realized outcome** exists.
- A **"Newly Added Projects During Month" table** (Table 4) giving newly onboarded projects' baseline cost and timeline figures — useful for identifying each project's true starting snapshot rather than assuming the first month we happen to observe it is its actual start.
- Ministry-wise and State-wise roll-up tables (Tables 1 and 2) and a North Eastern Region-specific roll-up (Table 5) — useful for sanity-checking our own aggregate computations against MoSPI's own published totals, and for confirming sector/ministry classification consistency.
- Explicit, source-stated **data quality caveats**: a named set of project IDs excluded from a given month's report "due to inconsistency in Cumulative Expenditure," to be republished once corrected; and a caveat that projects showing revised cost below the Rs. 150 crore eligibility threshold "may or may not be correct," with data "under reconciliation." Both of these are direct, source-provided evidence that our data validation stage (Section 22) must treat certain missingness and certain apparent anomalies as *known reporting artifacts*, not silently as errors to be dropped.
- **No free-text remarks, notes, or narrative field exists anywhere in the report.** Every field is structured (numeric, categorical, or date). This directly rules out one idea floated in the original problem-framing brief — using an LLM to extract risk signals from unstructured project remarks — as unsupported by this specific data source. It does not rule out an LLM assistant layered on top of the structured outputs (Section 18), which remains fully viable.

We separately hold monthly project-monitoring data covering approximately Q1 2025 through July 2026 (~19 months), understood to be in a form derived from the same underlying PAIMANA/CUF submissions as the April Flash Report, though not necessarily in the identical PDF Flash Report format for every month.

### 6.2 What We Do Not Yet Know and Must Determine Before Finalizing Targets

The following are open questions this document deliberately does not answer with invented numbers, because answering them requires actually loading and inspecting the full Q1 2025–July 2026 dataset:

1. **Exact monthly coverage.** Do we hold all ~19 monthly snapshots as separate Flash-Report-equivalent extracts, or a single already-merged file? If separate, are all 19 months in the same tabular structure as the April report, or do earlier months use a different template (PAIMANA appears to have had at least one reporting-format revision historically, given the OCMS legacy)?
2. **Per-project observation depth.** How many of the ~1,981 currently-ongoing projects actually appear in most or all 19 months (i.e., have a long enough trajectory to support trend/velocity features), versus how many are recent additions with only a handful of observed months?
3. **Realized-outcome sample size.** How many total projects appear across all 19 months' "Completed Projects During Month" tables? This single number determines whether our realized-outcomes dataset (Section 12) is large enough to support any quantitative validation claim at all, or whether it will need to be treated as a small, qualitative "spot-check" set.
4. **Entity stability.** Across 19 months, how often does Project Code change for what is otherwise the same project (by name, agency, and approval date)? How complete is Legacy OCMS Code and PMGID population across the full window, versus the many "-" placeholders visible in the April snapshot alone?
5. **Format drift.** Does column structure, units, or field definition change at any point across the 19-month window (e.g., a mid-window revision to how "Physical Progress" is calculated, or a threshold change to the Rs. 150 crore eligibility rule)?
6. **CUF field list, precisely.** The problem statement requires evaluating "existing CUF fields" specifically. We have inferred the CUF's likely field set from what appears in the published Flash Report, but the actual Common Upload Form used by implementing agencies may capture additional fields not surfaced in the public-facing Flash Report (e.g., milestone-level detail, contractor information, land-acquisition status) that could be available to us as a competing team but are not visible in the PDF alone. This needs to be confirmed against whatever raw dataset we actually hold, rather than inferred solely from a public report designed for readability.

None of Sections 9 through 24 below should be read as claiming these questions are answered — they describe the correct, defensible design assuming reasonable assumptions, and each phase in Section 9 that depends on one of these open questions says so explicitly.


## 7. Full Requirement List

### 7.1 Functional Requirements

**FR-1 — Data Ingestion.** The system shall ingest monthly PAIMANA project-monitoring extracts (PDF Flash Reports and/or any structured export we hold), parsing project-level records into a normalized intermediate format, preserving the source month of every record.

**FR-2 — Data Validation.** The system shall validate every ingested record against a documented rule set (Section 22) before it enters the longitudinal dataset, logging every rejected or flagged record with a human-readable reason rather than silently dropping it.

**FR-3 — Entity Matching.** The system shall resolve project identity across months using Project Code, Legacy OCMS Code, and PMGID as candidate keys, with an explicit, auditable conflict-resolution procedure, and shall produce a matching confidence indicator per project per month rather than a binary match/no-match decision.

**FR-4 — Longitudinal Dataset Construction.** The system shall construct a project-month panel dataset, one row per (project_id, report_month), from the validated, matched monthly records.

**FR-5 — Feature Engineering.** The system shall compute, per project per month, the full feature catalogue described in Section 11, tagged by whether each feature is derivable from CUF fields alone or requires additional derivation, to support the mandated CUF-only vs CUF+derived comparison.

**FR-6 — Label Construction.** The system shall construct (a) a windowed, near-term "emerging risk signal" label for the full ongoing-project panel, and (b) a realized-outcome label set from the stacked "Completed Projects During Month" tables, with an explicit, documented, leakage-safe procedure for each (Section 12).

**FR-7 — Cost Overrun Prediction.** The system shall produce, per project per month, a probability estimate that the project will exhibit a significant new cost-escalation signal within the defined forward window, using both a statistical baseline model and a machine learning model.

**FR-8 — Time Overrun Prediction.** The system shall produce, per project per month, an equivalent probability estimate for schedule/time-overrun signals, using the same dual-model approach.

**FR-9 — CUF-Only vs CUF+Derived Comparison.** The system shall report, for both FR-7 and FR-8, model performance separately when restricted to CUF-only features versus when additional derived features are included, using the metrics in Section 14.

**FR-10 — Statistical vs ML Comparison.** The system shall report, for both FR-7 and FR-8, the performance delta between the statistical baseline and the machine learning model, on the same temporal split, to support an evidence-based judgment on whether ML materially outperforms simpler methods for this data volume.

**FR-11 — Project Risk Score.** The system shall combine cost-risk and schedule-risk probability estimates (and any additional validated execution-risk signals) into a single 0–100 Project Risk Score per project per month, with data-derived risk-band thresholds.

**FR-12 — Early Warning Detection.** The system shall track each project's risk score trajectory across the trailing months and flag projects showing genuine deterioration (rising risk, worsening financial-physical gap, slowing progress velocity), distinct from merely flagging a high absolute score.

**FR-13 — Explainability.** The system shall generate, for every risk score and every early warning, a ranked list of the top contributing factors, computed via a model-faithful explanation method (SHAP or equivalent feature-importance method).

**FR-14 — Benchmarking.** The system shall compute, for each project, comparative statistics (e.g., expenditure-to-progress ratio percentile) against a defined peer group (same sector, similar cost band, similar project stage).

**FR-15 — Dashboard: National Level.** The system shall expose a national-overview view showing total projects, high-risk and critical-risk project counts, risk distribution by cost and schedule dimension, sector/ministry/state distribution, and overall risk trend.

**FR-16 — Dashboard: Sector/Ministry Level.** The system shall expose a drill-down view scoped to a selected sector or ministry, showing the same categories of statistics restricted to that scope, plus sector-level benchmarking.

**FR-17 — Dashboard: Project Level.** The system shall expose a per-project view showing all core project fields, the current risk score and its sub-components, the risk trend over time, the ranked contributing factors, and a recommended area for review.

**FR-18 — Dashboard: Watchlist.** The system shall expose a watchlist view surfacing the projects whose risk trend is deteriorating fastest as of the latest reporting month.

**FR-19 — LLM Project Intelligence Assistant.** The system shall expose a natural-language query interface that answers questions about project risk strictly by retrieving and formatting the system's own validated, structured outputs (risk scores, rankings, driver explanations), and shall not generate project facts that are not present in its retrieved context.

**FR-20 — Documentation and Deployment.** The system shall be accompanied by a data dictionary, a model card documenting evaluation results and limitations, and a deployment guide sufficient for a third party to reproduce the running system.

### 7.2 Non-Functional Requirements

**NFR-1 — Temporal Integrity.** No feature or label computation shall use information from a reporting month later than the month for which a prediction is being made (see Section 12.3 on leakage discipline). This is treated as a correctness requirement, not a best-practice suggestion.

**NFR-2 — Auditability.** Every stage of the pipeline (validation, matching, feature engineering, labeling, scoring) shall produce a log or artifact sufficient to trace any single project's final risk score back to the raw source records that produced it.

**NFR-3 — Explainability-by-Default.** No risk score shall be surfaced in the dashboard or through the LLM assistant without an accompanying explanation of its top contributing factors; a bare number is not an acceptable output anywhere in the user-facing system.

**NFR-4 — Honest Uncertainty Communication.** Wherever a prediction is based on a small or censored sample (Section 12), the system shall surface a confidence or data-sufficiency indicator alongside the prediction, rather than presenting all risk scores with uniform apparent confidence.

**NFR-5 — Local Reproducibility.** The full pipeline (excluding, optionally, the LLM component if a hosted API is used for the assistant) shall be runnable end-to-end on a single development laptop with 16GB RAM, given the confirmed data volume (Section 25).

**NFR-6 — Open-Source Preference.** Technology choices shall default to open-source tools unless a specific requirement cannot be reasonably met by one, consistent with the stack direction in Section 21.

**NFR-7 — Performance.** Dashboard queries against the precomputed risk-score and feature tables shall return within a small number of seconds for the full ~2,000-project national view, given the confirmed data volume; this is achievable without special-case optimization because the dataset is small by data-engineering standards (tens of thousands of rows).

**NFR-8 — Scope Traceability.** Every implemented feature shall be traceable to either an explicit item in Section 3's official requirement list or an explicit item in Section 4's "our design choices" list; nothing shall be built that cannot be justified under one of the two.


## 8. System Architecture — End to End

```
                              PAIMANA / CUF MONTHLY SUBMISSIONS
                              (Flash Reports + held Q1'25-Jul'26 data)
                                          │
                                          ▼
                              ┌─────────────────────────┐
                              │   DATA INGESTION LAYER   │   (Section 9, Phase 1-2)
                              │  PDF/text parsing,       │
                              │  schema normalization    │
                              └────────────┬─────────────┘
                                           ▼
                              ┌─────────────────────────┐
                              │  DATA VALIDATION LAYER   │   (Section 22)
                              │  rule checks, anomaly    │
                              │  flags, quality logging  │
                              └────────────┬─────────────┘
                                           ▼
                              ┌─────────────────────────┐
                              │  ENTITY MATCHING LAYER   │   (Section 9, Phase 2)
                              │  Project Code / Legacy   │
                              │  OCMS Code / PMGID       │
                              │  reconciliation          │
                              └────────────┬─────────────┘
                                           ▼
                              ┌─────────────────────────┐
                              │  LONGITUDINAL PANEL      │   (Section 10)
                              │  project_id × report_    │
                              │  month dataset           │
                              └────────────┬─────────────┘
                                           ▼
                              ┌─────────────────────────┐
                              │  FEATURE ENGINEERING     │   (Section 11)
                              │  cost / expenditure /    │
                              │  progress / schedule /   │
                              │  trajectory features     │
                              └────────────┬─────────────┘
                                           ▼
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                              ▼
       ┌─────────────────────────┐                  ┌─────────────────────────┐
       │   COST-RISK MODELS      │                  │  SCHEDULE-RISK MODELS   │
       │ statistical + ML,       │                  │ statistical + ML,       │
       │ CUF-only + CUF+derived  │                  │ CUF-only + CUF+derived  │
       └────────────┬─────────────┘                  └────────────┬─────────────┘
                    └──────────────────────┬──────────────────────┘
                                           ▼
                              ┌─────────────────────────┐
                              │     PROJECT RISK ENGINE  │   (Section 15)
                              │   0-100 combined score   │
                              └────────────┬─────────────┘
                                           ▼
                              ┌─────────────────────────┐
                              │   EARLY WARNING ENGINE   │   (Section 16)
                              │   trend / deterioration  │
                              │   detection              │
                              └────────────┬─────────────┘
                                           ▼
                              ┌─────────────────────────┐
                              │  EXPLAINABILITY ENGINE   │   (Section 17)
                              │  SHAP / driver ranking   │
                              └────────────┬─────────────┘
                                           ▼
                              ┌─────────────────────────┐
                              │   BENCHMARKING MODULE    │   (Section 9, Phase 13)
                              └────────────┬─────────────┘
                                           ▼
                              ┌─────────────────────────┐
                              │   BACKEND API (FastAPI)  │   (Section 20)
                              └──────┬─────────────┬──────┘
                                     ▼             ▼
                       ┌─────────────────┐  ┌─────────────────────┐
                       │  WEB DASHBOARD  │  │  LLM ASSISTANT       │
                       │  (React)        │  │  (retrieval-         │
                       │  3 levels +     │  │  constrained, no     │
                       │  watchlist      │  │  invented facts)     │
                       └────────┬────────┘  └──────────┬───────────┘
                                └──────────┬────────────┘
                                           ▼
                                   DECISION-MAKER
                          (MoSPI / IPMD analyst, reviewer)
```

Every box in this diagram corresponds to one or more named phases in Section 9, and every arrow represents a data-flow boundary at which we enforce a validation or leakage check (per NFR-1 and NFR-2 above). No box is permitted to reach "back" into a later stage's output — this is the concrete architectural enforcement of the temporal-leakage discipline described in Section 12.3.


## 9. Project Development Phases — Deep Explanation of Each

Each phase below is described in four parts: **What** (the concrete work), **Why** (the reasoning that makes this phase necessary and why it sits where it does in the sequence), **How** (the specific technical approach), and **Deliverable / Exit Criteria** (what must exist for the phase to be considered done). Every phase is tagged **[MVP-CRITICAL]** or **[HIGH-END / STRETCH]** per the two-cycle plan in Section 5.1.

---

### PHASE 0 — Problem Understanding and Data Discovery [MVP-CRITICAL]

**What.** Read and fully internalize the official problem statement 26103; inventory every document and dataset we actually hold (the April 2026 Flash Report PDF, and the Q1 2025–July 2026 held data); produce this design document itself as the artifact of this phase.

**Why.** The single most common failure mode in hackathon projects — and the one this entire document is structured to avoid — is beginning implementation before the team agrees on what is actually being asked for and what data actually exists to support it. Every subsequent phase depends on the decisions made here; a mistake at Phase 0 (e.g., assuming two decades of OCMS history is available, or assuming a "final outcome" label is computable for all projects) propagates through every later phase and is far more expensive to fix in Phase 12 than to get right in Phase 0.

**How.** Direct inspection of source PDFs using text-extraction tooling (not assumption or memory of "what government reports usually look like"); explicit written interpretation of the problem statement, separating MoSPI's actual words from any assumed elaboration; a written, falsifiable list of open questions (Section 6.2) that implementation must not silently paper over.

**Deliverable / Exit Criteria.** This document. A confirmed inventory of held data (file list, page counts, table structures). A written list of unresolved open questions that Phase 4 (EDA) is explicitly tasked with closing.

---

### PHASE 1 — Data Discovery and Schema Extraction [MVP-CRITICAL]

**What.** For every monthly data source we hold (whether PDF Flash Reports or a different structured extract), extract the raw project-level records into a common intermediate tabular format, without yet cleaning, matching, or feature-engineering anything.

**Why.** PDFs — even text-layer PDFs like the April 2026 Flash Report — are laid out for human readability, not machine parsing: values are visually grouped (e.g., Original Cost and Revised Cost appear as one visual cell with the revised figure in parentheses; Date of Approval and Start Date are similarly paired). A schema-extraction phase, separated from downstream cleaning, forces us to get the raw parsing logic correct and testable before any cleaning logic has a chance to mask a parsing bug as a "known data quality issue."

**How.** For text-layer PDFs: `pdftotext -layout` or `pdfplumber` to preserve row/column structure, followed by a hand-written parser (regular-expression or position-based) tuned specifically to the "All Ongoing Projects," "Completed Projects During Month," and "Newly Added Projects" table layouts observed in the April report — including correctly splitting the paired fields (Original Cost / Revised Cost; Date of Approval / Start Date; Original DoC / Revised DoC) into separate columns. If held monthly data is already in a structured format (CSV/Excel/database export) rather than PDF, this phase becomes schema alignment rather than PDF parsing — this must be determined by direct inspection (see open question 6.2.1) before committing engineering time to a PDF parser that may not be needed for most months.

**Deliverable / Exit Criteria.** One raw, unvalidated table per source month, with every field the source table contains, tagged with its source month and source document. A parsing test suite confirming at least the April 2026 month reproduces the known aggregate totals (1,981 projects, ~Rs. 37.13 lakh crore original cost, etc.) as a sanity check that parsing logic is correct before trusting it on other months.

---

### PHASE 2 — Data Cleaning and Entity Matching [MVP-CRITICAL]

**What.** Clean each month's raw table (type coercion, unit normalization, whitespace/encoding cleanup) and resolve project identity across months using Project Code, Legacy OCMS Code, and PMGID as candidate join keys.

**Why.** This is, in our judgment, the single hardest and most consequential engineering phase in the entire project, and the one most likely to be under-invested in by competing teams who rush to modeling. If entity matching is wrong — if the same real-world project is treated as two different projects because its Project Code changed, or two different real-world projects are silently merged because they share a placeholder "-" identifier — every downstream trajectory feature (progress velocity, expenditure acceleration, trend features) computed on that mismatched trajectory is meaningless, and no amount of modeling sophistication downstream can recover from it.

**How.** Build a match-confidence procedure rather than a single deterministic join: attempt a match on PMGID first if populated for both records; fall back to Project Code; fall back to Legacy OCMS Code; and where none of the three agree, fall back to a fuzzy match on (Project Name similarity + Implementing Agency + State + Approval Date proximity) as a last resort, flagged as low-confidence rather than silently accepted. Every match — high-confidence or low-confidence — is logged with the evidence used to make it, so any downstream anomaly can be traced back to ask "was this actually the same project?" Cross-check the resulting matched project count and aggregate totals against the Ministry-wise and State-wise roll-up tables (Tables 1 and 2 of the Flash Report) as an independent sanity check.

**Deliverable / Exit Criteria.** A canonical `project_id` assigned to every raw record across all months, with an explicit match-confidence field. A written audit report quantifying: how many projects matched with high confidence on all three IDs; how many required fallback matching; how many could not be confidently matched at all (and are therefore excluded or flagged for manual review, never silently merged).

---

### PHASE 3 — Build the Longitudinal Project-Month Dataset [MVP-CRITICAL]

**What.** Assemble the cleaned, matched monthly records into a single panel dataset: one row per (project_id, report_month), sorted chronologically within each project.

**Why.** This is the structural realization of the core insight from the original problem brief: monthly snapshots must not be treated as independent cross-sections, because a project's *trajectory* over time — is progress accelerating or stalling, is the financial-physical gap widening — is a fundamentally different and more powerful signal than any single month's snapshot can provide. This phase converts nineteen separate flat files into one dataset structured to support that trajectory analysis.

**How.** A left-join-style panel construction keyed on (project_id, report_month), explicitly deciding — and documenting — the semantics of a missing month for a given project: does its absence mean "not yet added," "completed and dropped off," "temporarily excluded due to a data-quality flag" (as the April report explicitly notes happens for a named set of project IDs), or a genuine reporting gap. This decision must be made per-project rather than assumed globally, since the April report itself demonstrates that at least one of these reasons (data-quality exclusion) is real and distinguishable from ordinary missingness if the accompanying report notes are captured.

**Deliverable / Exit Criteria.** The panel dataset, with a documented missingness-reason field per project-month gap. Row-count and project-count sanity checks against each source month's known totals.

---

### PHASE 4 — Exploratory Data Analysis [MVP-CRITICAL]

**What.** Systematic, question-driven exploration of the panel dataset to close the open questions listed in Section 6.2: per-project observation depth, realized-outcome sample size, entity-matching stability, and CUF field completeness.

**Why.** This phase exists specifically to prevent the failure mode of designing a sophisticated prediction target (Phase 5) on paper and only discovering during modeling (Phase 8) that the data cannot actually support it — for instance, discovering there are only a handful of projects with a 12-month-forward observation window, making a 12-month horizon target statistically meaningless. EDA here is not decorative visualization; it is a feasibility gate that Phase 5 is not permitted to bypass.

**How.** Compute, and report as concrete numbers (not estimates): the distribution of observed-months-per-project; the total count of realized-outcome projects across all stacked "Completed Projects During Month" tables; the proportion of projects with populated Legacy OCMS Code and PMGID versus placeholder values; the distribution of cost, sector, and ministry to confirm representativeness; and a check for any structural break in field definitions across the 19-month window (e.g., a sudden shift in how many projects report Physical Progress as exactly 0 or exactly 100, which can indicate a reporting-convention change rather than a real state).

**Deliverable / Exit Criteria.** A written EDA report directly answering each of the six open questions in Section 6.2 with real numbers. A go/no-go decision, backed by those numbers, on the specific prediction horizon(s) that Phase 5 will use.

---

### PHASE 5 — Define Targets and Prediction Horizons [MVP-CRITICAL]

**What.** Finalize, in light of Phase 4's findings, the exact label definitions and forward-looking prediction windows for both the cost-risk and schedule-risk targets, and the labeling procedure for the realized-outcomes dataset.

**Why.** This is the phase where the censoring problem identified in Section 12 must be resolved on paper, in writing, before a single model is trained — not discovered as an inconvenient surprise during evaluation. Getting this phase wrong silently produces a model that appears to perform well in offline validation and is unusable or misleading in the dashboard, because the offline "ground truth" it was validated against was itself invalid.

**How.** For the ongoing-project panel: define the target as a windowed, near-term event — e.g., "will this project's cost-escalation percentage increase by at least X points, or will a schedule slip beyond Y months first appear, within the N months following the current reporting month" — with X, Y, and N chosen based on Phase 4's actual observed distributions, not round numbers picked in advance. For the realized-outcomes dataset: define the target directly from the true before/after figures in the stacked "Completed Projects During Month" tables — actual completion date versus original/target date, and final cost versus original cost — with no windowing needed, since the outcome is genuinely known.

**Deliverable / Exit Criteria.** A written label specification document, with the exact formula for each target, the chosen horizon(s) and their Phase-4-derived justification, and the exact leakage boundary (which fields/months are permitted as input for a label computed at month T).


### PHASE 6 — Feature Engineering [MVP-CRITICAL]

**What.** Compute the full feature set described in Section 11 for every (project_id, report_month) row, tagged as CUF-only-derivable or requiring additional derivation.

**Why.** This is where the raw panel dataset becomes model-ready, and where the problem statement's explicit CUF-vs-CUF+derived comparison requirement is operationalized: without this tagging, we would be unable to honestly answer "how much predictive power exists in the currently captured data alone" versus "would additional variables help," which is one of the two comparisons the problem statement explicitly asks us to make.

**How.** Compute cost features (escalation amount and percentage, cost growth rate over time), expenditure features (utilization ratio, monthly change, velocity, acceleration), physical-progress features (monthly change, velocity, acceleration, stagnation flags), schedule features (elapsed vs. planned duration, schedule variance, delay duration), the financial-physical gap and its change over time, and trajectory features (rolling averages and volatility of the above, computed only over trailing months relative to the row's own report_month — never using future months, per the leakage discipline established in Phase 5). Context features (ministry, sector, state, project size band, mega-vs-major classification per the Rs. 1,000 crore threshold visible in the source report's own notes) round out the feature set.

**Deliverable / Exit Criteria.** A versioned feature table joined to the panel dataset, with an explicit CUF-only feature subset and a CUF+derived full feature set, both computable independently so Phase 8's comparison experiment can be run cleanly.

---

### PHASE 7 — Build Statistical Baselines [MVP-CRITICAL]

**What.** Train logistic regression (for the classification formulation of each target) and, for the high-end version, a discrete-time hazard/survival model that explicitly accounts for censoring in the ongoing-project panel.

**Why.** The problem statement explicitly requires demonstrating whether machine learning provides meaningful gains over conventional statistical approaches — this cannot be demonstrated without first building the statistical baseline properly and fairly, on the same features and the same temporal split the ML model will later use. Skipping straight to gradient boosting "because it usually wins" would leave us unable to answer a question MoSPI explicitly asked, and would be scientifically indefensible if a judge asks "did you actually test this, or assume it."

**How.** Logistic regression with standard regularization, fit separately on CUF-only and CUF+derived feature sets, evaluated on the temporal split defined in Phase 9. For the high-end version, a discrete-time survival model (treating each project-month as an at-risk interval and modeling the hazard of a cost/schedule event occurring in that interval) as the statistically rigorous treatment of the censoring problem — this is a stronger and more defensible baseline than logistic regression alone precisely because it does not require pretending non-events are "confirmed negatives" when they may simply not have happened yet.

**Deliverable / Exit Criteria.** Trained baseline models for both targets, both feature sets, with recorded performance metrics (Section 14) ready for direct comparison against Phase 8's ML models.

---

### PHASE 8 — Build ML Models [MVP-CRITICAL]

**What.** Train a gradient-boosting model (a single library — XGBoost, LightGBM, or CatBoost, chosen once and used consistently rather than compared against each other, to conserve hackathon time for more consequential comparisons) and a random forest as a secondary reference point, on the same feature sets and the same temporal split as Phase 7's baselines.

**Why.** This phase exists to be directly, fairly compared against Phase 7 — not to independently "find the best model." The value of this phase is entirely in the comparison it enables, not in the model itself.

**How.** Gradient boosting classifier fit separately on CUF-only and CUF+derived feature sets, with hyperparameters tuned via the temporal validation fold (never via random k-fold, to avoid leaking future information into hyperparameter selection). Feature importance extracted natively as a first-pass explainability signal, ahead of the dedicated SHAP work in Phase 10.

**Deliverable / Exit Criteria.** Trained ML models for both targets, both feature sets, with performance metrics recorded in the exact same format as Phase 7's baselines, enabling a direct side-by-side statistical-vs-ML comparison table.

---

### PHASE 9 — Temporal Validation and Evaluation [MVP-CRITICAL]

**What.** Formalize and apply the rolling-origin (forward-chaining) temporal train/validation/test split across all models built in Phases 7 and 8, and compute the full metric suite from Section 14.

**Why.** A model can look excellent under random k-fold cross-validation and be nearly useless in production if evaluated this way, because random folds let the model implicitly learn from months that, in deployment, would not yet have occurred relative to the prediction point. Given only ~19 months of data, this discipline is harder to apply than in a data-rich setting — the test window will necessarily be short — and this phase must document that constraint honestly rather than pretend a robust three-way split exists when the calendar does not support one.

**How.** Partition the 19-month window into an early training block, a middle validation block (used for hyperparameter selection), and the most recent months as a held-out test block; report exact month boundaries and project counts per block. Evaluate all four model/feature-set combinations per target (statistical/CUF-only, statistical/CUF+derived, ML/CUF-only, ML/CUF+derived) — eight evaluated configurations per target, sixteen total across both targets — using ROC-AUC, PR-AUC, calibration, early-warning lead time, and false-alarm rate as defined in Section 14.

**Deliverable / Exit Criteria.** A single comparison table (per target) reporting all eight configurations' metrics side by side, forming the direct evidentiary basis for the problem statement's required CUF-vs-derived and statistical-vs-ML comparisons.

---

### PHASE 10 — Explainability [HIGH-END for full SHAP / MVP for basic feature importance]

**What.** For the chosen production model(s), generate per-project, per-month explanations of the top contributing factors behind each risk prediction.

**Why.** The problem statement explicitly lists explainability-adjacent outcomes (a Cost Escalation Driver Analysis Module) and, independent of that, a risk score without an explanation is operationally close to useless to the decision-maker this system is built for (Section 2.1) — "82% risk" tells a reviewer nothing about where to direct their limited attention.

**How.** For the MVP, use the gradient-boosting model's native feature importances plus a simple per-instance breakdown (e.g., how far each feature's value sits from the training population's typical range) as a lightweight, fast-to-implement stand-in. For the high-end version, implement SHAP (TreeSHAP for the gradient-boosting model specifically, which is computationally efficient and exact for tree ensembles, unlike model-agnostic SHAP variants) to produce genuine per-instance, per-feature contribution values.

**Deliverable / Exit Criteria.** For any given project and month, a ranked list of the top three to five contributing factors to that project's risk score, in the same format the dashboard (Phase 15) and LLM assistant (Phase 16) will consume.

---

### PHASE 11 — Risk Scoring [MVP-CRITICAL]

**What.** Combine the cost-risk and schedule-risk probability estimates (and, in the high-end version, additional validated execution-risk signals) into a single 0–100 Project Risk Score per project per month, with empirically-derived risk-band thresholds.

**Why.** Decision-makers need a single, comparable number to triage nearly 2,000 projects; two separate probabilities (cost-risk, schedule-risk) do not by themselves support ranking "which project needs attention first" without a combination rule, and an arbitrarily chosen combination rule (e.g., simple averaging with no justification) would be exactly the kind of unvalidated design choice this document is built to avoid.

**How.** Calibrate each underlying model's raw output into a true probability (via Platt scaling or isotonic regression, checked against the calibration metric from Phase 9) before combining, since raw gradient-boosting outputs are not inherently well-calibrated probabilities. Combine calibrated cost-risk and schedule-risk probabilities via a documented rule (e.g., a weighted combination validated against the realized-outcomes dataset from Phase 5, rather than an arbitrary 50/50 split assumed without evidence). Map the combined probability to a 0–100 scale via a monotonic transform, then derive LOW/MEDIUM/HIGH/CRITICAL band cutoffs from the actual score distribution (e.g., quantile-based cutoffs), and sanity-check those cutoffs against the realized-outcomes dataset — do projects that historically escalated or slipped tend to fall into the higher bands under this cutoff scheme?

**Deliverable / Exit Criteria.** A documented, calibrated, validated risk-scoring formula; a monthly-updated risk score for every project in the panel; a written justification for the chosen risk-band cutoffs referencing the realized-outcomes validation.

---

### PHASE 12 — Early Warning Engine [MVP-CRITICAL for basic version, HIGH-END for full trend logic]

**What.** Track each project's risk-score trajectory over its trailing months and generate an early-warning flag when genuine deterioration is detected, distinct from a static "is the current score high" check.

**Why.** The problem statement's own framing example is explicit that the system "should not merely say 'Project has 82% risk'" — it should detect deterioration over time. A snapshot-only risk score, however well-calibrated, does not fulfill this requirement on its own; the early-warning behavior is a genuinely separate capability layered on top of the risk score.

**How.** For the MVP: a simple rule — flag a project if its risk score has increased for at least two consecutive months, or if its financial-physical gap (expenditure-to-progress ratio) has widened for at least two consecutive months. For the high-end version: a more principled trend-detection approach (e.g., a rolling-window slope test on the risk-score time series, combined with the same slope test on physical-progress velocity and expenditure velocity, requiring simultaneous adverse movement across at least two of the three before triggering a warning, to reduce false-alarm rate).

**Deliverable / Exit Criteria.** A per-project, per-month early-warning boolean/level, with the specific trend evidence that triggered it logged alongside the flag (feeding directly into Phase 10's explainability output).


### PHASE 13 — Benchmarking [HIGH-END / STRETCH]

**What.** Compute, for each project, comparative statistics against a defined peer group (same sector, similar cost band, similar project stage, and where meaningful, similar geography).

**Why.** A risk score in isolation cannot tell a reviewer whether a project's numbers are unusual — a project's expenditure-to-progress ratio might look concerning in absolute terms but be entirely typical for its sector (e.g., early-stage land-acquisition-heavy projects often show low physical progress against real expenditure for reasons unrelated to risk). Benchmarking supplies the comparative context that turns a raw number into a meaningful signal, directly supporting the problem statement's "Benchmarking and Comparative Analytics Module" outcome.

**How.** Define peer groups using the categorical context features already present (sector, ministry, a project-size band derived from the Mega-vs-Major Rs. 1,000 crore threshold visible in the source report's own legend, and a project-stage bucket derived from elapsed-duration-as-a-fraction-of-planned-duration). Compute each project's percentile rank within its peer group on key ratios (expenditure-to-progress, cost growth rate, schedule variance), and surface any ratio where a project sits in an extreme percentile (e.g., top or bottom decile) as a benchmarking-derived signal, feeding into the explainability output alongside the model-derived drivers.

**Deliverable / Exit Criteria.** A per-project benchmarking summary (e.g., "this project's expenditure-to-progress ratio is in the 92nd percentile among comparable Railways-sector projects of similar size"), computed and refreshed alongside the monthly risk score.

---

### PHASE 14 — Backend API [MVP-CRITICAL]

**What.** Build the FastAPI backend service exposing the panel dataset, risk scores, early-warning flags, explainability outputs, and benchmarking summaries to both the dashboard and the LLM assistant.

**Why.** Separating the modeling/scoring pipeline (Phases 1–13, which run as a batch process on a monthly cadence, matching PAIMANA's own monthly update cycle) from the serving layer (this phase) keeps the system's two very different performance profiles cleanly separated: the pipeline is compute-heavy but infrequent, while the API must be fast and always-available for interactive dashboard use.

**How.** Endpoints organized around the three dashboard levels: a national-summary endpoint, a sector/ministry-scoped endpoint, and a project-detail endpoint (returning core fields, risk score and sub-scores, trend history, and top contributing factors in one payload to minimize round trips), plus a watchlist endpoint and a structured query endpoint the LLM assistant calls internally (never exposing raw model internals to the LLM, only the same validated structured outputs the dashboard itself consumes — this is the concrete mechanism, not just a policy statement, by which we prevent the assistant from inventing facts, per FR-19).

**Deliverable / Exit Criteria.** A running FastAPI service with documented endpoints (auto-generated OpenAPI schema), backed by the precomputed risk-score and feature tables, tested against the dashboard's actual query patterns.

---

### PHASE 15 — Dashboard [MVP-CRITICAL]

**What.** Build the React-based three-level dashboard (national, sector/ministry, project) plus the watchlist view, per the specification in Section 19.

**Why.** This is the primary interface through which the intended end user (Section 2.1's central MoSPI/IPMD analyst) actually consumes the system's output; no matter how sound the modeling, the project fails its actual purpose if this layer is not usable by a time-constrained reviewer scanning nearly 2,000 projects.

**How.** React with Tailwind CSS for layout and styling, Recharts or Plotly for the distribution and trend visualizations described in Section 19, consuming the FastAPI backend's endpoints directly. Each level surfaces the explainability output (Phase 10) inline rather than requiring a separate click-through, per NFR-3 (no risk score without an accompanying explanation).

**Deliverable / Exit Criteria.** A working, navigable dashboard covering all four views (national, sector/ministry, project, watchlist), demonstrable end to end from the live backend rather than from static mock data.

---

### PHASE 16 — LLM Project Intelligence Assistant [HIGH-END / STRETCH for MVP cycle, targeted for full build in high-end cycle]

**What.** Build a natural-language query interface that answers questions about project risk by retrieving and formatting the system's own validated, structured outputs.

**Why.** The problem statement explicitly lists this as a possible outcome, but is equally explicit — in both the official framing and our own design discipline — that the numerical prediction itself must not depend on the LLM, and that the LLM must never invent project facts. This phase exists specifically as a natural-language convenience layer over an already-correct system, not as a substitute for the modeling work in Phases 5–12.

**How.** A retrieval/function-calling pattern: the assistant receives a natural-language question (e.g., "which railway projects have the highest delay risk"), translates it into a structured call against the Phase 14 backend's query endpoint (never against raw, unvalidated data), retrieves the actual ranked results and their associated driver explanations, and generates only the natural-language phrasing of an answer that is otherwise fully determined by the retrieved structured data. Explanation-style questions ("why is Project X high risk") are answered by retrieving that project's Phase 10 explainability output and phrasing it in natural language, never by asking the LLM to reason about the project independently.

**Deliverable / Exit Criteria.** A working query interface handling both ranking-style questions and explanation-style questions, with a test suite confirming that answers to fact-style questions (e.g., "what is Project X's current cost") always match the backend's own structured data exactly, with zero tolerance for invented figures.

---

### PHASE 17 — Deployment [MVP-CRITICAL for a working local/demo deployment, HIGH-END for a fully documented production-style deployment]

**What.** Package and deploy the full system (backend, dashboard, database, and the LLM component if used) in a form that can be demonstrated live and, ideally, reproduced by a third party.

**Why.** A system that only runs on one team member's laptop in an undocumented state is a serious risk at both the internal-hackathon and grand-finale stages, where live demonstration and, in the case of the grand finale, jury scrutiny of the actual running system are central to evaluation.

**How.** Containerize the backend, database (PostgreSQL), and dashboard via Docker, with a documented `docker-compose` setup runnable on the development laptop described in Section 25; for the LLM component, default to a hosted API for demo reliability (Section 25.3) with local-model deployment documented as the production-path answer rather than depended upon for the live demo itself.

**Deliverable / Exit Criteria.** A one-command (or clearly documented multi-step) local deployment procedure, tested on a clean checkout, sufficient for a judge or teammate to run the full system independently.

---

### PHASE 18 — Documentation and Hackathon Presentation [MVP-CRITICAL]

**What.** Produce the data dictionary, the model card (documenting the Phase 9 evaluation results and the honest limitations from Section 23), the deployment guide, and the pitch materials (idea PPT, demo video, live-demo script) required at each SIH evaluation stage (Section 5).

**Why.** The online-evaluation stage of SIH (Section 5) is a paper/video screening before any live demonstration occurs — a technically excellent system with a weak or dishonest presentation of its own limitations can be screened out before a judge ever sees the running system, while a presentation that proactively and clearly states what the system can and cannot claim (per Section 23) is, per our own analysis in Section 3.2 and Section 23, one of the strongest available differentiators against competing teams.

**How.** The model card explicitly states, in plain language, the realized-outcomes sample size, the temporal validation window and its limitations, and the CUF-vs-derived and statistical-vs-ML comparison results — including if the answer to "does ML help" turns out to be "not by much, given this data volume," since an honest negative result, properly explained, is more credible to a technically literate jury than an inflated claim.

**Deliverable / Exit Criteria.** Data dictionary, model card, deployment guide, idea PPT, and demo video/script — each cross-referenced against this design document so that every claim made to judges traces back to an actual, demonstrated result rather than an aspiration.


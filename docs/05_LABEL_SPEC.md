# 05 — Label Specification (target, censoring, leakage)

> Finalized in STEP_05 (EDA Feasibility Gate). All thresholds, horizons, and class support figures
> are sourced directly from empirical distributions in `reports/eda_gate_summary.json` generated from
> `data/processed/panel.parquet`. All parameters and definitions confirmed.

---

## 1. Primary Target Decision: Schedule-Risk Transition

- **Target Concept**: Near-term forward schedule delay transition on projects with established timelines.
- **Horizon ($N$)**: **3 months** ($N = 3$).
- **Delay Threshold ($Y$)**: **$\ge 3$ months** ($Y \ge 3$).
- **Class Balance**: **2,744 clean transition positives** across **12,300 usable panel rows** (**22.31% positive rate**).
- **Secondary Role for Cost-Risk**: Cost-risk (cost escalation $>0\%$) exhibits only a 1.93% positive base rate (237 events over $N=3$ across the entire panel). Cost escalation is demoted from the classification label and retained as a causal trailing feature and secondary monitoring indicator.

---

## 2. Exact Positive Definition (Leakage-Safe)

A panel observation at project $i$ and month $T$ is labeled **POSITIVE** ($Y_{i,T} = 1$) if and only if **BOTH** of the following conditions hold:

1. **Established Target Existed at $T$**:
   A valid, non-null `revised_completion_date` existed at or before month $T$ (`revised_completion_date_T` is not null).
   - **Leakage-Safe Rule**: This condition is evaluated strictly using observation data with $\text{report\_month} \le T$.

2. **Genuine Outward Transition in Forward Window**:
   Within the forward window $(T, T+3]$, the project's maximum observed effective target date slips by at least 3 months relative to its established target at $T$:
   $$\max_{t \in (T, T+3]} \left( \text{effective\_completion\_date}_{i,t} \right) - \text{effective\_completion\_date}_{i,T} \ge 3 \text{ months}$$
   where the latest revised date in the window is strictly greater than the revised date at $T$.

A panel observation is labeled **NEGATIVE** ($Y_{i,T} = 0$) if it meets the eligibility criteria (has $\ge 3$ future observed months in the panel) and condition (2) does not occur (i.e. the project stays on schedule or slips by $< 3$ months).

---

## 3. The First-Population Exclusion Rule (Contamination Prevention)

> [!CRITICAL]
> **Load-Bearing Contamination Rule**: A project with a null `revised_completion_date` at $T$ that has a revised date populated for the first time within $(T, T+3]$ is a **DATA-REPORTING EVENT**, NOT an operational schedule slip label.
>
> **The model must NEVER be trained on the gross 3,933 forward slips — only on the 2,744 clean transitions.**

### Empirical Sourcing from STEP_05
In STEP_05 EDA decomposition, out of 3,933 gross forward slips:
- **1,120 (28.48%)** were first-population events (`revised_date` null at $T$, newly entered in $(T, T+3]$).
- **812 of those 1,120 events (72.50%)** occurred in a single month (**March 2026**), reflecting bulk administrative back-population by MoSPI rather than sudden project failure.
- Filtering out these 1,120 administrative artifacts isolates **2,744 genuine operational transitions** (22.31% positive rate across all 12,300 rows; 33.27% among established projects).

### Rule Specification
- If `revised_completion_date` is null at $T$, any subsequent appearance of a revised date in $(T, T+3]$ is treated as a **Data Reporting Event**.
- It is **EXCLUDED** from the positive label. If the project otherwise exhibits no transition from an existing revised date, it is assigned $Y_{i,T} = 0$.

---

## 4. Exclusion & Censoring Rules (Scheme A)

Our dataset covers 13 consecutive months (July 2025 – July 2026) of ongoing projects. Most have not finished, so "no overrun observed yet" is right-censored.

1. **Trailing Truncation Rule**:
   If a project has fewer than $N=3$ observed months after $T$ in the panel (i.e. $T \in \{\text{May 2026}, \text{June 2026}, \text{July 2026}\}$ or the project terminates before $T+3$), that row is **UNKNOWN**.
   - It is **DROPPED** from training and evaluation.
   - It must **NEVER** be imputed or assumed negative ($Y \ne 0$).

2. **Usable Row Count**:
   Applying this rule preserves exactly **12,300 usable project-month rows** (65.2% of the 18,860 panel rows).

---

## 5. Candidate Feature Note for STEP_06 (Causal Indicator)

While first-population events are excluded from the *forward label* to avoid training on data-entry artifacts, the event of a project receiving its first revised date is often an early warning signal that something changed.

- **STEP_06 Feature Candidate**: Create a binary feature `first_revised_date_entered_in_trailing_k` indicating whether a revised date was populated for the first time in the trailing window $(T-k, T]$.
- **Causality Requirement**: This feature must be evaluated strictly on data with $\text{report\_month} \le T$.

---

## 6. Scheme B — Realized-Outcome Validation Anchor (Honesty & Model Card Caveats)

For completed projects appearing in Table 3 ("Completed Projects During Month"), true final outcomes are known (actual vs. original completion date; final vs. original cost).

### Ground-Truth Reversibility Rule & Clean Anchor
- **Total Completed Records**: 259 records.
- **Provisional / Reversible Exclusion**: Project `705635` (*Southern Railway, Trivandrum-Kanyakumari*) completed in `2026-02` but reappeared in Table 6 Ongoing from `2026-03` to `2026-07`. Any reversible project is excluded.
- **Clean Realized-Outcome Set**: Exactly **258 projects** (97 cost overruns, 92 schedule slips, 31 both, 100 neither).

### Honesty Note for Model Card and Evaluation
> [!WARNING]
> **Sector Concentration & Effective Sample Size**:
> June 2026 contains 130 completions (121 in Roads & Highways).
> - Of the 92 clean realized schedule slips, approximately 32 are in the concentrated June road cohort.
> - Outside June road packages, our model validates against **~60 independent realized schedule slips** (and 92 overall across 258 clean completed projects).
> - Evaluations and presentation decks must plainly state: *"We validate schedule-risk predictions against ~60 independent realized slips (92 overall across 258 completed projects)"*, avoiding any misleading claims of thousands of completed ground-truth validations.

---

## 7. Leakage Rules (Enforced by Automated Tests)

1. **Features at $T$**: Compute using only data where $\text{report\_month} \le T$. Rolling statistics use trailing windows ending at $T$.
2. **Labels at $T$**: Compute using only forward window $(T, T+N]$. Insufficient future $\implies$ drop row.
3. **Cross-Sectional / Historical Priors**: Historical aggregates (e.g. sector delay rates) use only months strictly $< T$.
4. **Validation Splits**: Splits are temporal/rolling-origin splits (e.g. train on months up to $T_{\text{split}}$, test on subsequent months), never random k-fold cross-validation.
5. **Continuous Enforcement**: Each feature and label function in `src/` must have a dedicated test asserting zero leakage.


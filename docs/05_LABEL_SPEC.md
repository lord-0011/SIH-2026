# 05 — Label Specification (target, censoring, leakage)

> Finalised in Phase 5, AFTER Phase 4 confirms usable-row counts. Until then, thresholds
> below are candidates marked `TODO(confirm-from-data)`. Do not train on a horizon Phase
> 4 hasn't shown to have enough rows.

## The censoring problem (why we can't use "final outcome")
Our data is ~19 months of *ongoing* projects. Most have not finished, so "no overrun
observed yet" is NOT "will never overrun" — it's right-censored (unknown). A naive
"overrun=1 if revised>original at last snapshot" label mislabels unresolved projects as
negatives and biases the model to under-predict risk.

## Scheme A — windowed near-term label (PRIMARY, used for the ongoing panel)
At month T, using ONLY data with month <= T, predict:
> Does a significant NEW adverse signal appear in window (T, T+N]?
> - cost-risk: cost_escalation_pct rises by >= X points, OR
> - schedule-risk: new/increased schedule variance beyond Y months

- N (horizon): `TODO(confirm-from-data)` — candidates 3/6/12; pick from Phase-4 row counts
- X, Y (thresholds): `TODO(confirm-from-data)` — set from Phase-4 observed distributions
- EXCLUSION RULE: if a project has fewer than N observed months after T, that row is
  UNKNOWN — drop it from training, do NOT label it negative.

## Scheme B — realized-outcome label [STRETCH for L1, but capture the data now]
For projects appearing in "Completed Projects During Month" tables (Table 3), the true outcome is
known (actual vs original completion date; final vs original cost). Small set; used as an
honest validation anchor, not primary training data. Sourced total = 259 completed records.

### Ground-Truth Reversibility Rule & Exclusion (Discovered in STEP_04)
A completion in MoSPI reporting is NOT guaranteed to be irrevocable:
- **Provisional / Reversible Completion**: Project `705635` (*Southern Railway, Trivandrum-Kanyakumari*)
  appeared in Table 3 Completed in `2026-02`, but subsequently reappeared in Table 6 Ongoing
  from `2026-03` to `2026-07` (5 months) with its completion target revised to `06/2028`.
- **Exclusion Rule**: Any project that reappears in Ongoing in any month strictly *after* its appearance
  in Table 3 Completed must be **EXCLUDED** from the Scheme B ground truth validation set.
- **Clean Realized-Outcome Set**: Exactly **258** projects satisfy the clean condition:
  $$\text{Clean Anchor} = \text{Completed in Table 3} \land \text{Never observed ongoing afterward}$$
  (Note: Heavily concentrated in June 2026 with 130 road packages, so effective independent sample size is ~129).

## Leakage rules (tested, not trusted)
1. Feature at T uses only month <= T. Rolling = trailing window ending at T.
2. Label at T uses only window (T, T+N]. Insufficient future → exclude row.
3. Historical aggregates (sector event rate) use only months strictly < T.
4. Splits are temporal/rolling-origin, never random k-fold.
Each feature/label fn has a pytest asserting no month > cutoff is read.

## MVP decision
Level 1 builds ONE target (cost-risk OR schedule-risk) with Scheme A. Choose the one
with more usable rows at the chosen N (Phase 4 decides). Record the choice here + charter.

# 00 — Project Charter (Level 1: LPU Internal Hackathon)

## Purpose
Build a predictive risk & early-warning layer on PAIMANA project-monitoring data that
tells a MoSPI/IPMD reviewer **which of ~2,000 infrastructure projects to look at first,
and why**, before problems fully surface.

## The one-sentence system
Ingest PAIMANA monthly data → rebuild each project's trajectory → engineer features →
predict near-term cost/schedule overrun risk (statistical + ML) → 0-100 explained risk
score → early-warning on deterioration → serve via API + dashboard.

## Primary user
A central analyst/decision-maker (oversight, not execution). Consequence: we optimise
for **ranking & triage + explanation**, not precise point predictions.

---

## LEVEL-1 MVP SCOPE (what must exist to win the internal hackathon)

IN SCOPE (build these):
- Longitudinal project-month dataset from our held data (ingestion → matching → panel)
- ONE prediction target — cost-risk **or** schedule-risk, whichever has more usable rows
  (decided in Phase 4 EDA, not now)
- ONE statistical baseline (logistic regression) + ONE ML model (gradient boosting)
- Evaluation on a temporal split, reported for **CUF-only vs CUF+derived** features and
  **statistical vs ML** (both comparisons the PS explicitly asks for)
- 0-100 risk score with data-derived bands
- Basic early-warning rule (risk up / financial-physical gap widening 2 months running)
- Feature-importance-based explanation (top contributing factors) per project
- FastAPI backend + React dashboard: National → Sector/Ministry → Project (3 levels)

OUT OF SCOPE for Level 1 — marked `[STRETCH]` everywhere (do NOT block on these):
- Second prediction target
- Discrete-time survival/hazard model
- Full SHAP (feature importance stand-in is fine for L1)
- Benchmarking module
- Watchlist dashboard view
- LLM Project Intelligence Assistant
- Full production Docker/deploy polish

## Definition of Done (Level 1)
1. Pipeline runs end-to-end from raw data to a populated risk-score table on Adi's Mac.
2. Dashboard shows all 3 levels from the live API (not mock data).
3. Evaluation doc has the filled CUF-vs-derived and statistical-vs-ML comparison table
   with **sourced numbers and honest sample sizes**.
4. Demo script (`docs/10_DEMO_SCRIPT.md`) rehearsed; MVP is the guaranteed-working path.
5. All docs synced (`docs/09_DOC_SYNC_RULES.md`); no unresolved Phase-4 data TODOs.

## What makes us win (differentiators — say these to judges)
- We treat **right-censoring** honestly instead of faking "final outcome" labels.
- We answer the PS's actual questions: does CUF-only data predict? does ML beat stats?
  — and we report the answer even if it's "not by much," which is more credible.
- Every risk score carries an **explanation** + a **data-sufficiency** caveat.
- Early warning is **trend-based**, not a static score.

## Honest constraints (also say these — see docs/03 and master doc §23)
Only ~19 months of data; most projects unresolved (censored); our data ≠ full OCMS
archive; no free-text field so no NLP-on-remarks; possible reporting-format drift across
months (Phase 4 checks this).

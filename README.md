# PAIMANA Predictive Risk Platform — SIH 2026 (PS 26103)

Predictive / early-warning layer on top of MoSPI's PAIMANA infrastructure-project
monitoring data. Moves PAIMANA from **descriptive** ("what happened") to
**predictive** ("what is likely to happen") monitoring: predicts cost & schedule
overrun risk, scores it 0-100, explains why, and flags deteriorating projects early.

**This repo targets LEVEL 1 first: the LPU internal hackathon (September 2026).**
Scope here is the MVP defined in `docs/00_PROJECT_CHARTER.md` §MVP. Stretch/high-end
items are marked `[STRETCH]` everywhere and are NOT required to win Level 1.

---

## How to navigate this repo (read in this order)

| # | Document | Read it to understand |
|---|----------|-----------------------|
| 0 | `docs/00_PROJECT_CHARTER.md` | What we're building for Level 1, scope in/out, definition of done |
| 1 | `docs/01_TECH_STACK.md` | Every tool, version, and why; local setup |
| 2 | `docs/02_ARCHITECTURE.md` | System diagram + how the `src/` folders map to the pipeline |
| 3 | `docs/03_DATA_INVENTORY.md` | **What data we actually hold** (fill from real files before Phase 4) |
| 4 | `docs/DATA_SHARING.md` | **Data sharing via DVC + Google Drive** (how team shares heavy artifacts) |
| 5 | `docs/04_DATA_SCHEMA.md` | Panel dataset schema + MVP feature catalogue |
| 6 | `docs/05_LABEL_SPEC.md` | Target definition, censoring & leakage rules |
| 7 | `docs/06_PHASES.md` | Phase plan for Level 1 with exit criteria |
| 8 | `docs/steps/STEP_*.md` | One granular, actionable spec per build step |
| 9 | `docs/08_EVALUATION.md` | Metrics + the comparison tables we must fill |
| 10| `docs/09_DOC_SYNC_RULES.md` | **The rule: update docs after every implementation** |
| 11| `docs/10_DEMO_SCRIPT.md` | The Level-1 pitch + live demo run sheet |

## Live-state files (updated constantly, not just at milestones)

- `PROGRESS.md` — current status of every step; the single source of truth for "where are we"
- `CHANGELOG.md` — append-only log of every implementation, dated
- `ANTIGRAVITY.md` — operating manual for the Antigravity coding agent

## Golden rule

**No implementation is "done" until its related docs are updated in the same change.**
See `docs/09_DOC_SYNC_RULES.md`. This is enforced, not optional.

## Data setup

Data (raw reports + pipeline outputs) is tracked with DVC on a shared Google Drive,
NOT in git. After cloning:
```bash
pip install -r requirements.txt
dvc pull
```
- **Regenerated data?** -> `dvc add <path> && dvc push && git commit <path>.dvc && git push`
- **Pulling others' work?** -> `git pull && dvc pull`
See `docs/DATA_SHARING.md` for full instructions.

## Repo layout

```
paimana-risk/
├── README.md               ← you are here
├── ANTIGRAVITY.md          ← agent operating manual + rules
├── PROGRESS.md             ← live status of every step
├── CHANGELOG.md            ← append-only implementation log
├── requirements.txt        ← Python deps
├── docker-compose.yml      ← Postgres + api + frontend (stub for now)
├── docs/                   ← all specifications (see table above)
│   ├── DATA_SHARING.md     ← DVC + Google Drive sharing guide
│   └── steps/              ← STEP_00 .. STEP_16
├── src/                    ← pipeline code, one folder per stage
│   ├── ingestion/          ← PDF/extract → raw tables      (Phase 1)
│   ├── validation/         ← data-quality rules            (Phase 2)
│   ├── matching/           ← entity matching across months (Phase 2)
│   ├── panel/              ← build project-month panel      (Phase 3)
│   ├── features/           ← feature engineering            (Phase 6)
│   ├── labels/             ← label construction             (Phase 5)
│   ├── models/             ← statistical + ML models        (Phase 7-9)
│   ├── risk/               ← 0-100 risk score               (Phase 11)
│   ├── early_warning/      ← trend/deterioration detection  (Phase 12)
│   ├── api/                ← FastAPI serving layer          (Phase 14)
│   └── common/             ← shared config, logging, io
├── data/                   ← GITIGNORED. Govt data never committed.
│   ├── raw/                ← original monthly reports as received
│   ├── interim/            ← parsed/cleaned intermediate tables
│   └── processed/          ← panel, features, labels, scores
├── reports/                ← raw Flash Report PDFs (tracked via DVC)
├── notebooks/              ← EDA only; findings graduate into docs
├── tests/                  ← pytest; leakage + parsing tests live here
└── frontend/               ← React dashboard (Phase 15)
```

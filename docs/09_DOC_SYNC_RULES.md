# 09 — Documentation Sync Rules (ENFORCED)

The core rule you asked for: **docs and code never drift apart.** Every implementation
updates its related documents in the *same* change. A step whose code is written but
whose docs are stale is **not done** and must be rejected in review.

This file is short on purpose — it must be obeyed literally.

---

## Rule 0 — The two live files are ALWAYS updated

After *any* implementation work, no matter how small:

1. **`PROGRESS.md`** — move the step's status, tick its checklist, record blockers.
2. **`CHANGELOG.md`** — append a dated entry (newest at top).

If you did work and these two are untouched, the work is not finished.

## Rule 1 — The Sync Map: when you touch X, you update Y

| When you implement / change ... | You MUST update ... |
|---------------------------------|---------------------|
| A parser in `src/ingestion/` | `docs/03_DATA_INVENTORY.md` (fields/coverage found), `docs/04_DATA_SCHEMA.md` (raw schema if changed) |
| Anything that reveals real dataset facts (counts, coverage, sample sizes) | `docs/03_DATA_INVENTORY.md` — replace every `TODO(confirm-from-data)` you resolved |
| Any stage generating/updating data artifacts (`data/`, `reports/`) | `docs/DATA_SHARING.md` (track with DVC pointer, push to remote) |
| Validation rules in `src/validation/` | `docs/04_DATA_SCHEMA.md` §Validation rules table |
| Matching logic in `src/matching/` | `docs/steps/STEP_03_matching.md` §Method, and note match-confidence stats in `docs/03_DATA_INVENTORY.md` |
| Panel builder in `src/panel/` | `docs/04_DATA_SCHEMA.md` §Panel schema (if columns change) |
| A feature in `src/features/` | `docs/04_DATA_SCHEMA.md` §Feature catalogue (add row, tag CUF vs DERIVED) |
| Label logic in `src/labels/` | `docs/05_LABEL_SPEC.md` (definition, horizon, thresholds actually chosen) |
| A model in `src/models/` | `docs/08_EVALUATION.md` (results table), model card section |
| Risk-score formula in `src/risk/` | `docs/05_LABEL_SPEC.md`? no → dedicated §in `docs/08_EVALUATION.md` + charter |
| Early-warning rules in `src/early_warning/` | `docs/steps/STEP_13_early_warning.md` §Trigger logic |
| API endpoints in `src/api/` | `docs/02_ARCHITECTURE.md` §Endpoints |
| Tech/dependency/version change | `docs/01_TECH_STACK.md` + `requirements.txt` |
| A phase's exit criteria met | `docs/06_PHASES.md` (mark phase complete) + `PROGRESS.md` |
| A decision that contradicts a doc | Change the DOC FIRST (with Adi's ok), then the code. Never leave code that silently disagrees with a doc. |

## Rule 2 — Numbers in docs are sourced

Any dataset number written into a doc (project count, usable rows per horizon, match
rate, metric value) must be reproducible by a named script or notebook. Write the source
in parentheses, e.g. `1,981 ongoing projects (src/ingestion, april_2026)`. No unsourced
numbers — that is how fabricated facts sneak in.

## Rule 3 — `TODO(confirm-from-data)` is a real gate

Docs written before we inspected the full dataset (esp. `03_DATA_INVENTORY.md`) contain
`TODO(confirm-from-data)` markers. These are not optional. **Phase 5 (label definition)
must not start until every marker Phase 4 is responsible for is resolved with a real
number.** Grep for them before declaring a phase done: `grep -rn "confirm-from-data" docs/`.

## Rule 4 — Review checks sync, not just code

Claude's review of any step explicitly checks: does PROGRESS reflect reality? Does
CHANGELOG have the entry? Are the mapped docs updated? Are there unsourced numbers or
unresolved TODOs that should now be closed? A step with good code and stale docs fails
review.

## Rule 5 — The doc index stays valid

If you add or rename a doc, update the navigation table in `README.md` and this file's
Sync Map in the same change.

---

### Quick pre-commit checklist (paste into every step's walkthrough)

```
[ ] PROGRESS.md updated (status + checklist + blockers)
[ ] CHANGELOG.md entry appended (dated, newest on top)
[ ] Sync Map docs for touched code updated
[ ] All numbers in docs are sourced (Rule 2)
[ ] grep confirm-from-data: any I resolved are now removed
[ ] README nav + this Sync Map still valid (Rule 5)
[ ] DVC pointers updated & pushed if data changed (docs/DATA_SHARING.md)
```

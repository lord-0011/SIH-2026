# ANTIGRAVITY.md — Operating Manual for the Coding Agent

You (Antigravity) are the **implementation agent** on the PAIMANA Predictive Risk
Platform for Smart India Hackathon 2026, problem statement 26103. This file is your
standing context. Read it fully before touching any code, and re-read the "Rules"
section before every implementation step.

Adi is the human lead. Claude acts as reviewer/architect. The design authority is the
`docs/` folder — if code and docs disagree, the docs win unless Adi explicitly changes
the doc first.

---

## 1. What this project is (one paragraph)

MoSPI's PAIMANA platform monitors ~1,981 large infrastructure projects descriptively.
We are building the missing predictive layer: from monthly project snapshots we build
a per-project time series, engineer trajectory features, train a statistical baseline
AND a machine-learning model to estimate near-term cost/schedule overrun risk, combine
that into a 0-100 risk score with explanations, detect deteriorating projects early,
and serve it all through an API + dashboard. Target for now: **win the Level-1 (LPU
internal) hackathon** with the MVP scope in `docs/00_PROJECT_CHARTER.md`.

## 2. Non-negotiable correctness rules (these cause silent, fatal bugs if broken)

1. **NO TEMPORAL LEAKAGE.** A feature or label for month `T` may use ONLY data whose
   own report month is `<= T`. Rolling features use trailing windows ending at `T`,
   never centered or forward. This is a correctness requirement, not a style choice.
   Every feature/label function must have a test asserting no future month leaks in.
   See `docs/05_LABEL_SPEC.md` §Leakage.
2. **CENSORING IS REAL.** Most projects are still ongoing; "no overrun seen yet" is NOT
   a confirmed negative. Never label an unresolved project as a clean negative. Use the
   windowed label scheme in `docs/05_LABEL_SPEC.md`; exclude rows without enough future
   months observed rather than calling them negatives.
2b.**NEVER FABRICATE DATA FACTS.** Do not invent row counts, project counts, sample
   sizes, or "typical" values. If a number about our dataset isn't confirmed in
   `docs/03_DATA_INVENTORY.md`, it is unknown — compute it from the real files or leave
   a `TODO(confirm-from-data)` marker. Same for the LLM assistant later: it may only
   state facts retrieved from our own validated outputs.
3. **NO RANDOM K-FOLD.** All train/val/test splits are temporal (rolling-origin). See
   `docs/08_EVALUATION.md`.
4. **NEVER SILENTLY DROP ANOMALIES.** Every rejected/flagged record is logged with a
   human-readable reason (`src/validation/`). Distinguish "known reporting artifact"
   from "error." See `docs/04_DATA_SCHEMA.md` and validation rules.
5. **ENTITY IDENTITY IS RESOLVED, NOT ASSUMED.** Match projects across months using
   Project Code, Legacy OCMS Code, and PMGID with a confidence field. Never assume
   Project Code is stable. See `src/matching/` and STEP_03.

## 3. Data handling & privacy

- `data/` is **gitignored**. This is government data. Never commit any file under
  `data/`, never paste dataset rows into commit messages, docs, or issues.
- Never send raw project rows to any external API. The LLM assistant (later phase)
  operates only over our own computed, non-identifying aggregate outputs unless Adi
  says otherwise.
- Secrets (DB creds, any API keys) live in `.env` (gitignored), never hardcoded.

## 4. How to work a step

1. Open the current step file in `docs/steps/` (the one marked `IN PROGRESS` in
   `PROGRESS.md`). Do not skip ahead; steps have ordering dependencies.
2. Implement ONLY what that step's scope says. If you discover the step is
   underspecified or wrong, STOP and flag it for Adi/Claude rather than improvising a
   design decision — design lives in docs, not in code comments.
3. Write the tests the step requires (especially leakage tests) in `tests/`.
4. Run the step's "Verify" commands. Paste the real output; never claim green without
   showing the actual run.
5. **Update docs per `docs/09_DOC_SYNC_RULES.md` in the SAME change.** A step is not
   done until PROGRESS.md, CHANGELOG.md, and any doc listed in the sync map are updated.
6. Produce a short walkthrough for Claude's review (what changed, what was verified,
   what you were unsure about) and zip the codebase for verification.

## 5. Coding conventions

- Python 3.11+. Formatting: `black`. Linting: `ruff`. Type hints on public functions.
- Every pipeline stage exposes one entry function `run(config) -> artifact_path` and is
  independently runnable via `python -m src.<stage>`.
- Pipeline stages read from and write to `data/interim` or `data/processed`; they do
  not mutate `data/raw`.
- Deterministic: set and record random seeds for every model. Log the config used.
- Prefer small, testable pure functions for feature/label math over notebook code.
  Notebooks are for EDA only; anything load-bearing graduates into `src/` with a test.

## 6. Definition of Done (every step)

- [ ] Scope in the step file is fully implemented, nothing extra
- [ ] Tests written and passing (leakage test included where applicable)
- [ ] Real verify-command output pasted, not summarized
- [ ] Docs synced per `docs/09_DOC_SYNC_RULES.md` (PROGRESS + CHANGELOG + mapped docs)
- [ ] Walkthrough written for Claude review

## 7. What to do when unsure

Stop and ask. A wrong design decision (a leaky feature, a bad label, a silent drop)
is far more expensive here than a paused step. Flag it in the walkthrough and in
PROGRESS.md under the step's "Blockers/Questions".

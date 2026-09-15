# Data Sharing (DVC + Google Drive)

Data is **not** stored in git. The code repo holds only tiny `.dvc` pointer files;
the actual raw reports and pipeline outputs live in a shared Google Drive folder,
versioned by DVC and linked to the code commit that produced them.

**Golden rule:** code and docs go in git; data goes in DVC/Drive; git holds a pointer
that links the two. Never `git add` a `.parquet`, a `.csv` output, or the raw PDFs.

---

## What is tracked where

| Path | Where it lives | Why |
|------|----------------|-----|
| `src/`, `docs/`, `tests/`, `*.md`, configs, `.github/` | **git** | source of truth, text, merges cleanly |
| `reports/` (raw Flash Report PDFs) | **DVC → Drive** | large binaries, shared once, not regenerated |
| `data/interim/`, `data/processed/` (parquet, ingestion_summary.csv) | **DVC → Drive** | derived artifacts, generated once, shared |
| `.env` | **nowhere** (each machine local) | secrets; only `.env.example` is committed |
| `.venv/`, caches | **nowhere** | local, regenerate with `pip install` |

---

## First-time setup (ONE person, already done if the remote exists)

```bash
pip install "dvc[gdrive]"
dvc init
git add .dvc .dvcignore && git commit -m "chore: init DVC"

# Drive folder ID = the part after /folders/ in the folder URL
dvc remote add -d gdrive gdrive://<DRIVE_FOLDER_ID>
git add .dvc/config && git commit -m "chore: add gdrive remote"

dvc add data/interim data/processed reports
git add data/interim.dvc data/processed.dvc reports.dvc .gitignore
git commit -m "data: track pipeline data + raw reports via DVC"
dvc push          # uploads real files to Drive (browser auth first time)
git push
```

After `dvc add reports`, confirm the PDFs left git:
```bash
git ls-files reports/     # must return NOTHING
# if it lists PDFs from an old commit:  git rm -r --cached reports/ && git commit
```

## Every teammate / every Antigravity machine (after clone)

```bash
git clone <repo> && cd SIH2026
pip install -r requirements.txt "dvc[gdrive]"
dvc pull          # downloads the exact data others generated — NO regeneration
```

---

## Daily workflow (keeps everyone in sync)

**You changed/regenerated data** (parser change, new month, new features, new scores):
```bash
dvc add data/processed            # (or whichever path changed)
dvc push                          # upload the new data to Drive
git add data/processed.dvc
git commit -m "data: <what changed> (after STEP_xx)"
git push
```

**You want others' latest work:**
```bash
git pull                          # gets code + updated .dvc pointers
dvc pull                          # gets the matching data
```

Because the `.dvc` pointer is committed next to the code, `git pull` + `dvc pull`
always give you data that matches the code you just pulled. That is the link plain
file-sharing loses — do not bypass it by emailing zips around.

---

## Rules for the coding agent (Antigravity) — add to definition-of-done

- Any step that **produces or changes data** under `data/` or `reports/` must, in the
  same change: `dvc add <path>` → `dvc push` → commit the updated `.dvc` file. A step is
  not done if new data exists only on the agent's local machine.
- Never `git add` a `.parquet`, output `.csv`, or a raw PDF. If `git status` shows one
  staged, stop — it belongs in DVC.
- Do not commit `.env`. Only `.env.example`.
- When reporting a step, state the data version: which `.dvc` files changed and that
  `dvc push` succeeded, alongside the usual green-CI evidence.

## Troubleshooting

- **`dvc pull` says "no remote"**: you're on an old clone — `git pull` first to get
  `.dvc/config`, then `dvc pull`.
- **Browser auth loop / Google rate limit**: the default gdrive app is shared; for a
  6-person team it's fine. If it throttles, switch to a DVC service account later — not
  needed for the hackathon.
- **Merge conflict on a `.dvc` file**: it's plain text (an md5 hash). Take the newer
  hash, `git commit`, then `dvc pull` to fetch that version. Never conflicts on the
  binary itself, because the binary isn't in git.

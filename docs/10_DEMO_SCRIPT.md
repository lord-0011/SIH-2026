# 10 — Level-1 Demo & Pitch Run Sheet

## Narrative arc (2-3 min pitch, then live demo)
1. Problem: PAIMANA tells you what happened, not what's about to go wrong; ~2,000
   projects, a reviewer can't watch them all.
2. Our system: predicts near-term cost/schedule risk, ranks + explains, flags
   deteriorating projects early. Show the National dashboard.
3. Drill: National → Railways → one high-risk project. Show score, trend, top factors,
   recommended review area.
4. The credible part (differentiator): we handle censoring honestly; we tested whether
   CUF data alone predicts and whether ML beats stats — show the comparison table.
5. Honest limits slide: ~19 months, most projects unresolved, our data ≠ full archive.

## Live demo run sheet (rehearse on the demo machine)
- [ ] `docker compose up -d db` running; API up (`/health` 200)
- [ ] Dashboard loads National from live API (not mock)
- [ ] One scripted drill-down path that definitely works
- [ ] Fallback: screenshots/video if network or memory misbehaves
- [ ] Close other heavy apps (browser tabs, IDE) — 16GB, avoid demo-time slowdown

## Judge Q&A prep (anticipate)
- "Where's your ground truth?" → Scheme B completed-projects set + honest censoring story
- "Why not just XGBoost everything?" → we compared vs logistic; report the real delta
- "Is 19 months enough?" → no, and we say so; that's why targets are near-term windows
- "Does the LLM make up numbers?" → assistant is [STRETCH]; when built it's retrieval-only

## Deliverables checklist for the round
- [ ] Idea PPT  - [ ] Demo video  - [ ] Live system  - [ ] This run sheet rehearsed
- [ ] Team: 6 members, ≥1 female (reconfirm vs LPU SPOC circular)

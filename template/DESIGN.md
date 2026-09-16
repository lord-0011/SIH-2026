# design.md — PAIMANA Predictive Risk Platform (Design System)
## Product framing (read first)
This is NOT the public PAIMANA data portal. It is an internal **decision-support cockpit**
for a MoSPI/IPMD analyst who must triage ~2,000 infrastructure projects and find the
handful that are deteriorating. Optimise every screen for: scanning, ranking, and
"where do I look first." Density over decoration. It should read as a serious government
analytics tool, not a consumer dashboard.
## Theme: Light, institutional, government-analytics
- Overall: clean white/near-white canvas, generous whitespace, crisp hairline borders.
  Calm and authoritative. No gradients on content, no drop-shadows heavier than a subtle
  card lift. Flat, data-first.
## Color tokens (use these exact values everywhere)
- --bg-page:        #F5F7FA   (app background)
- --bg-surface:     #FFFFFF   (cards, panels, tables)
- --bg-subtle:      #EEF2F7   (table header row, hover, chips)
- --border:         #DCE3EC   (hairline dividers, card borders)
- --text-primary:   #1A2233   (headings, key numbers)
- --text-secondary: #5A6472   (labels, captions, secondary)
- --text-muted:     #8A94A6   (disabled, footnotes)
- --brand-primary:  #0B4DA2   (MoSPI institutional blue — primary actions, active nav)
- --brand-primary-hover: #093E82
- --brand-accent:   #F79A1E   (saffron accent — sparingly: highlights, one CTA)
- --focus-ring:     #2E7CE4
### Risk band colors (SEMANTIC — never reuse for anything else)
These map to the model's LOW/MEDIUM/HIGH/CRITICAL bands. Use consistently on every screen.
- --risk-low:       #2E9E5B   text on #E7F5EC bg   (LOW)
- --risk-medium:    #C99A06   text on #FBF3D6 bg   (MEDIUM)
- --risk-high:      #E8730C   text on #FCE9D6 bg   (HIGH)
- --risk-critical:  #C6362F   text on #FBE0DE bg   (CRITICAL)
- --warning-active: #C6362F   (early-warning "deteriorating" flag — pairs with a trend-up arrow)
- --data-provisional: #8A94A6 (hatched/greyed treatment for PROVISIONAL / low-confidence rows)
## Typography
- Font: "Inter", system-ui, sans-serif. (Numbers: use tabular-nums / font-variant-numeric
  so columns of figures align.)
- Scale: page title 28/600; section head 20/600; card metric 32/700; card label 13/500 uppercase
  tracked; body 14/400; table cell 14/400; caption 12/400.
- Key metrics (counts, scores) are the loudest thing on screen. Labels are quiet uppercase.
## Layout & components
- Left vertical nav rail (icon + label), 240px, --bg-surface, active item --brand-primary.
  Sections: National Overview · Sectors/Ministries · Projects · Watchlist · Assistant.
- Top bar: breadcrumb + "data as of <month>" freshness pill (right-aligned, --bg-subtle).
  ALWAYS show data freshness — this tool is monthly-cadence, never imply real-time.
- Cards: --bg-surface, 1px --border, 8px radius, 20px padding, subtle shadow only.
- KPI/stat cards: big tabular number, small uppercase label above, tiny trend delta below
  (green down / red up arrow — for RISK, up is bad; be explicit with color+arrow, never
  color alone, for accessibility).
- Tables are the workhorse: sticky header (--bg-subtle), zebra off (use hairlines), risk
  band shown as a pill in its own column, sortable columns, row hover --bg-subtle. Right-
  align all numeric columns.
- Risk score shown as: the 0–100 number + a colored band pill. Never the number alone.
- Every risk score/warning must show WHY inline or one hover away (top contributing
  factors) — no bare scores (this is a hard product rule).
- Charts: thin lines, muted grid (--border), brand-primary series, risk colors only for
  risk series. Recharts-style. No 3D, no pie charts for risk distribution (use a horizontal
  stacked bar of the 4 bands).
## Accessibility & government norms
- WCAG AA contrast. Never encode meaning in color alone (band pills carry text labels too).
- Support an accessibility affordance in the top bar (font-size, contrast) like real gov
  portals. Keep the Ashoka-emblem / MoSPI lineage in the header so it reads as official,
  but the body is a modern analytics app.
## Tone of copy
Terse, factual, analyst-facing. "312 projects deteriorating this month", not "Uh oh!".
Numbers first. State uncertainty plainly ("validated on 116 held-out outcomes").
## Screens to generate (keep all consistent with the above)
1. National Overview  2. Sector/Ministry drill-down  3. Project detail
4. Early-Warning Watchlist  5. (optional) Assistant
---
name: pai-dashboard-project
description: "presentations.ai rebrand clone of Gamma's dashboard exploration (nik-dashboard-explorations.vercel.app) at ~/projects/pai-dashboard"
metadata: 
  node_type: memory
  type: project
  originSessionId: 17d06ddd-2ebe-4a47-a123-7d5bc371bd52
---

Clone of Gamma designer Nik Payne's dashboard prototype (https://nik-dashboard-explorations.vercel.app/, V9 "unified teamspaces" view) rebuilt from scratch at `~/projects/pai-dashboard` (static: index.html, styles.css, app.js — no build step). Rebranded to presentations.ai: brand indigo #3F53D8, "P" logo mark, "gamma" → "presentation" everywhere (New presentation, Presentation options, *.presentations.site). Sample workspace kept as "DoorDash Business"; single-workspace mode uses "Tejas's Workspace".

Built July 2026. ALL 18 variants cloned and switchable via the yellow bottom pill: V1–V9, nav options A–C ("Create with Presentations.ai" era, Acme Corp), mobile options A–D (phone frame, purple accent, drawer/bottom-nav), 🔬 comparison table (competitor matrix + org-chart boards), 🌈 exploration (6 sub-tabs). Architecture: version-dispatch in app.js — VCFG config per desktop version (v2–v9 share one renderer), separate renderers for v1/nav/mobile/compare/explore. LIVE at https://tequilatejas.github.io/pai-dashboard/ (repo TequilaTejas/pai-dashboard, Pages from main branch root; push to redeploy). Local preview: `python3 -m http.server 8644` in the project dir (ports 8642/8643 are used by hocus/fyrr stores). Reference screenshots of the original captured with Playwright live in the session scratchpad only.

Related: [[tejas-profile]] (works at Presentations.ai).

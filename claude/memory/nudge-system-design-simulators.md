---
name: nudge-system-design-simulators
description: Nudge simulators live at tequilatejas.github.io/nudge-system-design (snapshot mirror); no push access to upstream tejasdua143 repo
metadata: 
  node_type: memory
  type: project
  originSessionId: 8ebd6d88-1ac0-425a-b735-7198b0c6a391
---

The Smart Nudge system lives at `tejasdua143/nudge-system-design` — 5 branches (main, gh-pages, experiment/frontend-integration, feature/remove-gen-speed-pres-refresh, archive/v1), each with its own **different** copy of `simulator/index.html`. Full engine specs in `specs/` and weight maps in `config/`.

**Tejas's GitHub account (TequilaTejas) has read-only access to that upstream repo** (`push: false`) — fallout from the `tejasdua143` lockout, same as [[tejasdua-com-site]]. Nothing can be deployed to it.

Workaround, deployed 2026-07-13: **https://tequilatejas.github.io/nudge-system-design/** — a public mirror repo under TequilaTejas serving all 5 branch simulators side by side (one directory per branch) plus `flow.html`, a walkthrough of the 8-stage nudge pipeline with a live playground that runs the real weight maps.

**Why:** upstream GitHub Pages only serves the `gh-pages` branch, so there's no way to get a live URL for any other branch's simulator without deploying elsewhere.

**How to apply:** the mirror is a **snapshot, not a live sync** — upstream commits do not propagate. Re-run the extract-and-push (git archive each branch's `simulator/` into a per-branch dir) to refresh. For a quick one-off preview of any branch file without deploying, `raw.githack.com/<owner>/<repo>/<branch>/<path>` renders it live.

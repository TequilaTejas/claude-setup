---
name: tejasdua-com-site
description: "OLD retro-arcade portfolio — no longer on tejasdua.com (domain moved 2026-08-19); still served at tequilatejas.github.io/tejasdua.com"
metadata: 
  node_type: memory
  type: project
  originSessionId: 71f570bc-52fa-464b-9dd7-10408b0a78a5
  modified: 2026-08-19T13:21:14.725Z
---

`~/projects/tejasdua.com` is Tejas's **live** personal portfolio and is distinct from the Next.js `~/portfolio` (/life) project in [[portfolio-project]]. Plain static HTML/CSS/JS (no build): `index.html`, `css/style.css`, `js/{gate,menu,drift,franky,contact}.js`. Single-stage GSAP clip-path menu; retro-arcade "brand" aesthetic — Handjet pixel display + IBM Plex Mono, warm near-black + ember (OKLCH), hard 2px borders with offset shadows, no rounded/soft cards. Design system is the source of truth in `DESIGN_TEJAS.md` (read before visual edits). Client-side password gate (deterrence only) in `js/gate.js`; djb2 hash `3312522844` (set sessionStorage `td-gate` to that to bypass locally). Pages: Work, AI Experiments, About, Contact (+ hidden Playground/Writing, cs-pai case study). Assets/photos are stand-in Unsplash awaiting real ones.

**Hosting (changed 2026-07-05):** originally deployed from `tejasdua143/tejasdua.com` via GitHub Pages, but Tejas **lost access to the `tejasdua143` GitHub account**. Migrated to **`TequilaTejas/tejasdua.com`** (his working account; `gh` is authed as TequilaTejas). GitHub Pages serves `main` at root; custom domain `tejasdua.com` reclaimed by **verifying the domain** under TequilaTejas (DNS TXT challenge) to release the locked account's stale claim. Domain registered at **Hostinger** (DNS zone there): apex A → GitHub Pages IPs `185.199.108-111.153`, `www` CNAME → `tequilatejas.github.io`. Local remotes: `origin` = TequilaTejas repo, `upstream-old` = dead tejasdua143 repo.

**How to apply:** never push to / rely on `tejasdua143` — it's inaccessible. Deploy = commit to `main` and `git push origin main` (Pages auto-builds). No screenshot tooling in-repo; reuse Playwright from `~/portfolio/node_modules` against a local `python -m http.server`.

**Superseded (2026-08-19):** the `tejasdua.com` custom domain was detached from this repo and moved to [[tejas-100x-portfolio]] (`TequilaTejas/tejasdua-portfolio`). This arcade site is now the "My Old Portfolio" link, served only at `tequilatejas.github.io/tejasdua.com`. DNS at Hostinger unchanged.

---
name: hocus-store-project
description: "Hocus Store — Horcus creator gift-card storefront at ~/projects/hocus-store, staged on GitHub Pages under TequilaTejas"
metadata: 
  node_type: memory
  type: project
  originSessionId: a5f73ec1-4224-4612-9d11-bea179127e9f
  modified: 2026-07-31T19:04:23.350Z
---

Hocus Store: static creator storefront (gift cards & game top-ups) for streamer "Horcus" at `~/projects/hocus-store`. Originally cloned from tejasdua143/hocus-store (read-only — that account is locked out, see [[tejasdua-com-site]]); origin now points to TequilaTejas/hocus-store, with the old repo kept as `upstream`. Staging = GitHub Pages: https://tequilatejas.github.io/hocus-store/ (Pages builds from main, root). No build step — everything lives in `index.html`; `wireframes.html` is a frozen before-copy. Local preview convention (per repo CLAUDE.md): python http.server on port 8642, open in browser after every change.

Aug 2026: Digital Games section added below Merch (uncommitted as of Aug 1). Winning concept = "Marquee + Shelf" (chosen over Poster Wall/Spotlight Rail/Tabbed Shelf in `games-lab.html`, kept as design reference): 16:9 marquee holding poster art 6s then fading in muted trailer (content-ratio zoom crops baked letterbox bars, 4-layer progressive-blur bottom, trimmed logo bottom-left, lime chip top-right, price+CTA bottom-right) + 4 capsule cards + View all games. New screens `#gamepdp` (gallery walks a 5-rung media fallback ladder: trailer→screens→Ken Burns hero→poster-on-blur→branded placeholder; Silksong is deliberately poster-only, Celeste screens-only) and `#gamesbrowse` (poster-wall grid, genre tabs). Data = `DIGITAL_GAMES` array (a `GAMES` name already existed for gift-card search). Assets hotlinked from Steam CDN; publisher logo.pngs ship with baked transparent padding — trim at ingest (PIL getbbox), e.g. `assets/lab/cp2077-logo.png`. "Get key" reuses the previously-dead `coModal` checkout (real gift-card flow uses `openRzp`, untouched).

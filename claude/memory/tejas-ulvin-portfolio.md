---
name: tejas-ulvin-portfolio
description: "ulvin.xyz-style canvas portfolio at ~/projects/tejas-ulvin; 8 static pages, port 8649, gradient placeholder photos to swap"
metadata: 
  node_type: memory
  type: project
  originSessionId: d6d6fc01-0bb2-4f9f-aa57-f0b1191479ab
  modified: 2026-08-05T23:19:10.341Z
---

Portfolio rebuild inspired by ulvin.xyz (a Framer template by Ulvin Omarov) at `~/projects/tejas-ulvin`, built 2026-08-06. Static HTML/CSS/JS, no build step. Preview: `python3 -m http.server 8649` then `open -a "Dia" http://localhost:8649`.

Design system: Figma/Framer-canvas theme — top + left rulers, 100px grid background, cyan selection handles (`.sel` + `.h` corners), Slack-brand palette (#36c5f0 / #2eb67d / #ecb22e / #e01e5a, ink #111212, brown #522e29). Fonts: Silkscreen (pixel display, stand-in for their custom "Flux"), Inter, DM Mono, Just Me Again Down Here (handwriting).

Pages: index, about (BIO/STORY/WORK side toolbar + timeline), contact (2-step sticky-note form), playground (draggable polaroids), 4 case studies generated from `gen_cs.py` template (scratchpad, ephemeral): OneThing, Cutroom, Pacer, Lockin — see [[onething-app]], [[cutroom-project]], [[pacer-project]], [[lockin-project]].

Content is Tejas's own (not copied from the source site); photos are gradient placeholders labeled for swapping. Iterated with a Playwright screenshot-compare loop against reference captures (2 iterations to converge).

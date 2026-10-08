---
name: romantasy-aop-project
description: "Cloned Pocket FM Romantasy AOP report with a comment + highlight layer at ~/projects/romantasy-aop, served on port 8652"
metadata: 
  node_type: memory
  type: project
  originSessionId: 469a6616-d7a3-4f0a-8884-c81063be3d7f
  modified: 2026-09-03T08:16:51.607Z
---

Static clone of https://trfhmm.csb.app/ (Pocket FM "Romantasy Genre AOP", 14-section internal report) at `~/projects/romantasy-aop`, with an annotation layer added on 2026-09-03. Preview: `python3 -m http.server 8652` then open in Dia (see [[previews-in-dia]]).

The original is a CodeSandbox React app whose CSS is entirely inline styles, so the clone is a DOM dump of `#root` wrapped in a shell. `_doc-body.html` keeps the raw dump.

Annotation layer picked via [[crazy-four-skill]]: **Docs Rail** (option A of 4) — selection toolbar with 4 highlight colours plus Comment, comment cards in a 340px right rail anchored to their mark with Google-Docs collision pushing, dashed leader line to the active card. Anchoring is character offsets into the document's text-node stream (SVG excluded), so it survives reloads. Persistence is localStorage key `romantasy-aop-annotations-v1`, with JSON export/import.

**Why:** Tejas asked for a faithful clone plus commenting and highlighting; the rail beat margin-dots/mode-toggle/canvas because the doc is long and reviewers read threads in sequence.

**How to apply:** Port 8652 is this project. Ports 8642–8651 are already claimed by other projects (8651 serves the tejas-100x portfolio).

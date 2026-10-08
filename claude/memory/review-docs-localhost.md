---
name: review-docs-localhost
description: "Tejas wants review docs/plans served as local HTML on localhost, not published as Claude artifacts"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 978c77bf-46f1-4d87-8005-f22fac3fcb3b
---

When sharing plans, docs, or anything for Tejas to review as a rendered page, serve the HTML file locally (python3 -m http.server on a free port) and `open` the localhost URL. Do not publish Claude artifacts for review material.

**Why:** Tejas asked for this after the Undertow plan was published as an artifact (July 2026); they prefer reviewing in their own browser off localhost.

**How to apply:** Write the HTML to the scratchpad or project dir, start a background http.server (their projects use 864x ports: 8642 hocus, 8643 fyrr, 8644 pai-dashboard; 8645 used for the [[undertow-project]] plan), then `open <url>` per their CLAUDE.md rule.

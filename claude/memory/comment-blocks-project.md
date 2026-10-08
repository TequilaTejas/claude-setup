---
name: comment-blocks-project
description: WOBM vs TAB comment-problem analysis per 10-episode block (eps 1–100) at ~/projects/comment-blocks, port 8653
metadata:
  type: project
---
Built 2026-10-08. ~/projects/comment-blocks: index.html report (render.py + template.html + notes.json), labelled_comments.csv, taxonomy.md (12 problem labels + 3 non-problem). Sonnet agents hand-labelled 3,347 comments blind to show. Served on localhost:8653.
Key finding: WOBM complains less than TAB overall (50% vs 76%) but spikes on voice eps 1–10 (ad-vs-app narrator mismatch, +15pts) and sexual/disturbing content eps 31–50 and 91–100 (ep 35, 42, 99).

**Why:** user wanted block-wise problem % benchmarked vs TAB. **How to apply:** reuse taxonomy/render pipeline for other shows; see [[tab-benchmark-data]], [[wobm-multicast-reskins]]. Parallel agents sharing the scratchpad clobbered each other's temp files: tell agents to use unique temp names.

Update 2026-10-08: summary report (activation + voice) at summary.html via summary_render.py. PUBLIC at https://tequilatejas.github.io/wobm-activation-voice/ (repo TequilaTejas/wobm-activation-voice; site copy in ~/projects/wobm-activation-voice-site, index=summary, blocks.html=block report). User chose public Pages over artifact. Activation data source: ~/projects/wobm-activation (port 8654).

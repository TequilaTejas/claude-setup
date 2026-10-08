---
name: ascii-orchestration-diagrams
description: Tejas wants ASCII diagrams of agent orchestration/flows in every plan or multi-agent explanation
metadata: 
  node_type: memory
  type: feedback
  originSessionId: afb04a45-76fe-435c-a591-330288ddd8da
---

When presenting plans, pipelines, or anything involving multiple agents, include an ASCII diagram showing how the agents flow (who feeds whom, where humans review, where loops occur).

**Why:** Tejas asked for this on 2026-07-10 while building [[cutroom-project]]: "whenever you make plans and this stuff moving forward i need you to make agent orchastration ascii diagrams for me to make it easy to understand how each agents flows". He is a product designer; he parses structure visually faster than from prose.

**How to apply:** Draw the diagram in a code block with boxes and arrows. Mark human checkpoints (e.g. `[YOU]` or ✋), autonomous loops, and parallel fan-outs distinctly. Keep it narrow enough for a terminal. Prose explains; the diagram carries the structure.

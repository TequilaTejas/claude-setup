---
name: model-split-build-vs-plan
description: "Tejas wants Sonnet/Opus subagents to write code; Fable only plans, orchestrates, and reviews"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 978c77bf-46f1-4d87-8005-f22fac3fcb3b
  modified: 2026-08-09T15:19:13.811Z
---

Fable does not write implementation code directly. Delegate building to subagents with model overrides (`opus` for hard/architectural work, `sonnet` for well-specified modules and fixes). Fable plans, writes agent specs, orchestrates, and reviews the output.

**Why:** Tejas set this rule during the [[undertow-project]] kickoff (July 2026): "use sonnet and opus only to build - fable is only for planning and reviewing."

**How to apply:** For any implementation request, spawn Agent calls with `model: "opus"` or `model: "sonnet"` and a detailed spec, then review the result as Fable. Pairs with [[multi-agent-tmux-setup]] and the [[ascii-orchestration-diagrams]] preference for showing the agent flow.

**Exception (Aug 2026):** For the [[jupiter-emi-project]] Revolut-language rebuild, Tejas ordered the opposite: "use fable 5 only. no subagents using lower models." When he flags quality-critical design work, everything runs on Fable 5 — ask if unsure which regime applies.

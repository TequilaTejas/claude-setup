---
name: undertow-project
description: "Undertow — macOS attention copilot at ~/projects/undertow; intent-based LLM judge, no blocking; M0 = prove the judge"
metadata: 
  node_type: memory
  type: project
  originSessionId: 978c77bf-46f1-4d87-8005-f22fac3fcb3b
---

Undertow (working title): clean-sheet macOS 14+ menu bar app, Swift/SwiftUI, at ~/projects/undertow. Distinct from [[onething-app]].

Core idea: user declares a one-sentence intent; app senses behavior (NSWorkspace, AX, event tap, ScreenCaptureKit later) and an LLM judge scores screen activity against intent. Graded interventions instead of blocking (periphery dim → soft question → interruption; grayscale/viscous-scroll "attention physics"). Re-entry snapshots, flow protection, AirPods posture/nod module (CMHeadphoneMotionManager) at M3.5.

Milestones: M0 prove the judge (HUD verdicts only, checkpoint ≥90% accuracy) → M1 staged interventions + nod-to-confirm → M2 re-entry → M3 physics + flow protection → M3.5 body module → M4 personalization. Privacy: on-device sensing; LLM gets distilled summary only (Haiku-class).

Plan doc: scratchpad HTML served on port 8645 (July 2026); move to ~/projects/undertow/docs/ once repo exists. Build work is delegated per [[model-split-build-vs-plan]]; M0 scaffold kicked off with an Opus agent 2026-07-15.

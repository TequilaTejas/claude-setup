---
name: pacer-project
description: "Pacer — focus timer + whiteboard-interview coach at ~/projects/pacer; TequilaTejas/pacer, live on Pages, port 8645 preview"
metadata: 
  node_type: memory
  type: project
  originSessionId: 981f7664-3ab3-4603-a815-89386410c67f
  modified: 2026-07-22T20:38:09.693Z
---

Pacer: static web app (index.html/styles.css/app.js, no build) at ~/projects/pacer. Live at https://tequilatejas.github.io/pacer/ (repo TequilaTejas/pacer, Pages from main). Local preview port 8645 (hocus 8642, fyrr 8643, pai 8644).

Whiteboard-only (plain Timer mode removed at Tejas's request); coach built on Tejas's own 13-step senior-PD framework (clarify → objectives → reframe → users/stakeholders → pain points → HMWs → ideate → effort/impact → pros/cons → JTBD → wireframes → risks → metrics → summary). Whiteboard plans (tuned by Tejas): 60-min = 12/12/9/21/6 (Frame it / Pain→ideas / Prioritize / Design / Wrap); 75-min = 12/17/9/30/7 Frame/Pain→ideas/Prioritize/Design/Wrap (replaces old 90 — real 90-min interviews are 5 intro + 75 whiteboard + 10 questions). Pros & cons lives in Pain→ideas; user segments and stakeholder analysis are separate Frame-it items. Chime (WebAudio synth) + voice (speechSynthesis) nudges; phase-change nudges call out unchecked items; wake lock; Date.now()-based timing survives tab throttle; localStorage resume. Pacing model (v1.4, per-phase entry timers): phases NEVER auto-advance; "Next phase" only way forward, "Finish session" ends. Each phase's timer starts at entry (phaseEnteredMs/phaseDeadlineMs): ahead → next phase gets FULL planned time and badge holds steady "Ahead by X" (netAheadMs = originalEnd − max(elapsed, deadline)); behind → next phase's timer shrunk by the overrun (min 1 min) so you catch up in that phase, voice announces reduced minutes. Time-up voice at own deadline + nags every 2 min (behind / still-ahead / wrap-up variants). Done screen: "Finished X early" / "Went X over". v1 deliberately lean: no session logging (deferred), checklists hardcoded. Built by Sonnet agent per [[model-split-build-vs-plan]]; dark theme with #74F994 accent like [[fyrr-store-project]].

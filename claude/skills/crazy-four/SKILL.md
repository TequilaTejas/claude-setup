---
name: crazy-four
description: Before designing or redesigning any screen or flow, present exactly four divergent approaches (flow, layout, information presentation, UI treatment) with ASCII mockups, then let the user pick one before building anything.
---

# Crazy Four

Before building any screen, pitch four approaches and let the user pick. Never start building screen one of a design task without running this.

## When it triggers

- Any new screen, new flow, or major redesign of an existing screen.
- Per screen, not per project. Each screen in a flow gets its own four options, unless the user says "carry this direction" for the rest of the flow.

## The four must actually diverge

Each approach answers all four dimensions, and no two approaches may share the same answer on any of them:

1. **Flow** — how the user enters, how many steps, how it exits. Not just reordered buttons; a different journey.
2. **Layout** — the structural skeleton: sheet vs full-screen takeover vs card stack vs canvas vs split view.
3. **Information presentation** — what shows first, what is withheld, how progressive disclosure works, what hierarchy says about intent.
4. **Interaction, motion, UI tech** — the defining gesture or transition, and the technique powering it: spring physics, streamed generative UI, Lottie/Rive, CSS 3D, canvas. At least one of the four approaches must be the risky, futuristic one.

## Format per approach

- Name plus one-line premise.
- ASCII flow diagram: entry → steps → exits.
- ASCII layout sketch of the key screen.
- "What changes" — max 5 bullets, covering the four dimensions.
- Tech note: library or technique, and whether the current stack can run it. Never pitch tech the prototype cannot actually run.

Keep each pitch under ~150 words. Depth goes into the build, not the pitch.

## Deciding

- Present all four, then ask via AskUserQuestion with the ASCII layout sketch as each option's preview.
- You may mark one "(Recommended)" and say why in one line. Do not soften the other three to make it win.
- When the user picks with notes, fold the notes in and build. Do not re-pitch.

## Guardrails

- Honest to platform and brand context.
- Shared constraints (copy rules, accessibility, fixed behavior) apply to all four; state them once, not per approach.

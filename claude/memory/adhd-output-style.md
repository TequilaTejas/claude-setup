---
name: adhd-output-style
description: "Always apply the i-have-adhd skill — action-first, numbered steps, no preamble/closers, state restated each turn"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8a1f170d-1fec-46d1-96a4-8f6f3805fe02
  modified: 2026-08-07T19:03:50.070Z
---

Tejas asked (2026-07-19) that every reply follow the `i-have-adhd` skill, installed at `~/.claude/skills/i-have-adhd` from https://github.com/ayghri/i-have-adhd. Also encoded in `~/.claude/CLAUDE.md` under "Output style (always on)".

**Why:** Reader has ADHD; small working memory, starting is hardest, vague estimates fail, buried wins don't register.

**How to apply:** First line = next concrete action or the answer. Number multi-step work. Restate progress each turn ("step 3 of 5 done"). End with one sub-two-minute next action. No preamble, no recaps, no closing pleasantries. Specific time estimates. Cap lists at 5. Offer tangents separately. Pairs with [[stop-slop preferences implied by CLAUDE.md]].

**Escalation (2026-08-08):** Tejas flagged replies as far too long ("u write too much shit"). Hard cap: a few short lines per reply unless he asks for detail. Applies to prototype UI copy too — terse. No feature-by-feature recaps of builds; one line + what to check.

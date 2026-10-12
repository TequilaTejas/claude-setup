---
name: creative-audits-batch-oct
description: "Creative audits of 4 shows (Mad Vampire Lord's Bride, The Vampire Prince, The Last Howl, Marked by the Rogues) at ~/projects/creative-audits, served on port 8901"
metadata:
  node_type: memory
  type: project
  originSessionId: 583369cf-3790-49b9-8be1-787515d37815
  modified: 2026-10-06T21:13:31.964Z
---

Ran the `creative-audit` skill on 4 shows in parallel (2026-10-07) at `~/projects/creative-audits/<slug>/audit.html` (+ claims.json for `audit-validation`). Served with `python3 -m http.server 8901` from that folder.

Headline findings:
- The Last Howl (306 eps, 7 acts): wolf question answered with a substitute wolf (Helga dead, Astrid new, ep 169/198); "prove she was framed" never cleared publicly; child question open at finale.
- Mad Vampire Lord's Bride (564 eps, 20 acts): romance fully paid; spy premise defused at ep 127; finale 546-564 handed to grown son (replace, not pause).
- Marked by the Rogues (710 eps, 16 acts): Ethan's regret (promise clause) dropped; off-promise endings double after ep 451; Naira/Lyra name retcon ep 460.
- The Vampire Prince (665 eps, 20 acts): 8 breaks; leads absent 376-500 for side couples (pause for Evie); Gavriel ~replaced 593-665; H12 left open as sequel tease.

**Process lessons (apply next run):** give every agent a private `mktemp -d` dir (shared scratchpad collided across shows with same ep ranges); normalise lead keys before merge; never merge arcs until file count == expected windows; leads-repair needed for alias leads (Gavrael=Gavriel). Orchestration scripts in `_prompts/` (gen.py, next.py queue, normalize.py, harvest.py, AUTHOR_SPEC.md, CLUSTER_SPEC.md) are reusable. Related: [[scentless-yet-chosen-audit]].

**2026-10-08 · Mr. Cortez (The Royal Accident):** single ~5.4K-word ad/pilot script (no ep headers, ends on install CTA) → full pipeline skipped; hand-read scaled audit at `mr-cortez/audit.html` (6 inferred segments S1–S6, Q1–Q8). Headline: cold open sells revenge, minute 21 makes Javier a co-victim, final cliff is love-triangle jealousy (Sophie the drugger not linked back). Short scripts → do the scaled version, don't spin up agents.

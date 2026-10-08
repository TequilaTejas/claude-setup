---
name: scentless-yet-chosen-audit
description: "Creative audit (hook/promise analysis) of the 327-ep werewolf-romance show \"Scentless, Yet Chosen\""
metadata: 
  node_type: memory
  type: project
  originSessionId: 4b6a5fd4-5048-4128-ab99-f2b3c0847173
  modified: 2026-09-17T10:38:54.354Z
---

Ran the full `creative-audit` skill pipeline on "Scentless, Yet Chosen" (327 episodes, from two docx scripts in Downloads) at `~/projects/scentless-yet-chosen-audit`. Report: `audit.html`, served locally on port 8899 (`python3 -m http.server 8899`).

**Why this project is structurally unusual:** it's really two sequential rejected-heroine romances stitched into one season. Couple 1 (Caroline/Draven) fully resolves every one of its hooks by episode 165 — almost exactly the midpoint. The show then hands its narration to a second couple (Ava/Joseph, plus a third-act villain/love-triangle figure, Kenneth) for the remaining ~160 episodes, explicitly announced in-script at episode 170.

**Top findings, in case of a follow-up ask ("what did the audit say"):**
- Strongest hook (masked-stranger/paternity mystery) pays off cleanly onscreen, ep2→126.
- The show's own explicitly-stated "vindication" promise (ep1) is raised once and closed via a single offscreen line at ep61, then never mentioned again in 266 more episodes.
- A real production bug: episodes 211 and 212 are word-for-word identical scripts (confirmed by direct diff, not just extraction).
- A genuine retcon: Ella's fake pregnancy is conclusively disproved onscreen at ep96 (DNA test), then the exact same "discovery" is re-narrated as new information at ep236, ~140 episodes later.
- Biggest structural finding: Caroline and Draven (the show's own title characters) are completely absent from the final 5 episodes, including the literal season finale — the show replaces its original leads rather than pausing them.
- 4 hooks (Ava's true nature/witch blood, Steward's reckoning, Odelia's disappearance, Kenneth's agenda) are still open at the finale — legitimately, since the show acknowledges them as unresolved cliffhangers for a next season, not silently dropped.

**Process note for next time:** the skill's hook_health.py tool caught 3 of my first-draft hooks as under-evidenced (fewer than 6 phrasings or 5 matched episodes) and refused to score them — 2 of those turned out to be genuinely thin in the raw script (not just under-harvested) and got replaced with better-evidenced hooks (Linda-the-mole, Odelia's disappearance) found by grepping the ledger's raw threads for character names. Worth trusting that refusal rather than padding.

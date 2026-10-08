---
name: wobm-multicast-reskins
description: Transferring WOBM multicast speaker labels onto 5 reskinned scripts; tooling at ~/projects/wobm-multicast
metadata:
  type: project
---
Wolves of Blood Moon (Pocket FM) ep script has a multicast-annotated version (~/Downloads/Wolves_of_Blood_Moon_Hybrid_Narrator_Multicast_.docx). Tejas has 5 reskins (other worlds) needing the same speaker labels + delivery tags.

- Tooling: ~/projects/wobm-multicast/annotate.py <reskin.docx> <out.docx> <names.json>; check.py verifies word-level label parity (target: 0 mismatch runs). greek.json = example names config.
- All 5 done 2026-09-25: Greek Gods Academy, Vampire Slayers, Penny Dreadful, Dragon Rider Academy, Devil Mafia → ~/Downloads/<name> - WOBM Reskin - Multicast Annotated.docx. Penny was the heaviest rewrite (74% word match) and needed one manual override (json `overrides`).
- sus.py flags dialogue under NARRATOR / narration under characters; the WOBM source itself has 8 such quirks (Alice reads 'They were legendary…' narration).
- Labels renamed to reskin character names (THEA, NYLA…); offered to keep WOBM names instead if voice team prefers.

**Why:** consistent casting across reskin variants for Meta promo audio.
**How to apply:** for each new reskin, write a names json (label_map + word_map), run annotate.py, then check.py, then flag reskin leftovers without editing text.

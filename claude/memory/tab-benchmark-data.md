---
name: tab-benchmark-data
description: Canonical TAB (The Alpha's Bride) benchmark data lives at ~/Downloads/TAB Data/TAB_FULL_701eps.csv — always use it for Pocket FM cliff-report benchmarking
metadata:
  type: reference
---

The Alpha's Bride (TAB) benchmark data for Pocket FM cliff reports / donor briefs lives at `/Users/tejas/Downloads/TAB Data/`. Always read TAB from here rather than from whatever TAB rows a show's data pack happens to ship.

Canonical file: **`TAB_FULL_701eps.csv`** — TAB eps 1–701, 163.6 cumulative hours, show_id `cbc35fa13bbe154873ec97f78f2b4cf4b66c7d31`. Deep enough to benchmark every show in the batch (the longest, The Vampire Prince, is 665 eps). `tools/normalise.py` in ~/projects/cliff-donor points at it by default.

`old-250ep/` holds the first export (eps 1–250, 45.5 hr). Too short — it left ~48% of Mad Vampire Lord's Bride unbenchmarkable and made a recovery look like a continued decline. Don't use it.

CMS column names differ from the spec in CONTEXT_TRANSFER.md and from what `toolkit/analyse.py` expects:
- `CB D0+ d7` = level (spec: `LDAU (Modified)`)
- `CB D0+ Drop% d7` = per-episode drop (spec: `Drop % (Modified)`)
- `Duration cum. (Hr)` (spec: `Duration cum. (HR)`), `Story No.` (spec: `Story no.`), `Show ID` (spec: `show_id`)
`tools/normalise.py` handles the rename and merges TAB in.

Two data quirks to expect: TAB's own ep 11 shows a +47.6% LDAU rise (pre-ep-51 sampling noise, below the ep-51 baseline, ignore), and a show's final episode often carries `LDAU=0` with a blank drop — a hole, not a drop to zero. Exclude it.

Related: [[cliff-donor-project]]

---
name: episodic-retention-report-format
description: "LOCKED house format for Pocket FM episodic retention analysis reports (xlsx, 2 pages) — Key Spikes first, no separate recommendations block, pointer-annotated charts"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8ed7abec-3551-41ca-937d-0c833c16eea7
  modified: 2026-09-08T09:34:34.433Z
---

Standing, locked format for episodic retention analysis deliverables (CMS episodic export → xlsx). Confirmed 2026-09-08 on "Marked by the Rogues" and "Crushed & Crowned" — Tejas said "lock structure once and for all, all remaining analysis should be done exactly like that." Reusable builder: `report_template.py` (built during that session — recreate from this spec if not found on disk, it wasn't saved into a project directory).

**Page 1 order, exactly:**
1. Title + subtitle (show name, episode count, "Benchmarked vs The Alpha's Bride (701 eps)", snapshot date)
2. One-line bold headline stat directly under the subtitle — the single punchline (e.g. "Fix the Ep 605 break first — the single biggest deviation from benchmark").
3. **KEY SPIKES table — goes first, immediately after the headline.** Columns: Episode | Event | Drop (×100) / vs TAB | What's happening. There is **no separate "What to Improve" section** — fold every actionable call directly into the relevant spike row's "What's happening" text (self-contained, e.g. "...this is the single biggest problem — start any pacing review here"), never as a cross-reference to a recommendations block that no longer exists.
4. OVERALL bar + bullets — supporting narrative only: the net retention-vs-TAB stat, early-funnel read, completion-rate/engagement read, release-cadence note.
5. Three charts, always in this order: (a) Drop%×100 / MA10 / MA50, (b) Listening DAU per episode, (c) Retention Index vs TAB (both indexed to 100 at Ep 51). **Every chart gets red diamond pointer markers with episode-number data labels at the problem episodes** — the worst point of each actionable spike/slow-bleed cluster from the Key Spikes table (skip clusters explicitly marked "no action needed"). Built via a 4th "pointer" series per chart: a column that's blank everywhere except the marked episodes, `marker=diamond` red, `graphicalProperties.line.noFill=True` (no connecting line), `dLbls.showCatName=True` so the label reads the episode number, chart-level `displayBlanksAs="gap"`.

Page 2 "Raw Data": all episodes, LDAU/Drop%/MA10/MA50 (raw + ×100 helper cols), TAB LDAU aligned by episode, both retention indices, and the 3 pointer-marker helper columns the charts read from.

**Always benchmark against The Alpha's Bride (TAB).** Per [[tab-benchmark-data]]: `~/Downloads/TAB Data/TAB_FULL_701eps.csv`, show_id `cbc35fa13bbe154873ec97f78f2b4cf4b66c7d31`. Block ratio = show block-drop ÷ TAB block-drop at the same episode range, both baselined at Ep 51. This catches slow-bleed underperformance invisible to a self-relative spike scan (e.g. Rogues ep 391-450: 1.6-2.2x TAB with no single episode over -3.4%).

**Always hunt for spikes, not just block averages — report 3-4+, call out clustering.** Individual-episode drop-rate outliers (excluding batch-opener episodes). When spike days sit close together, name the cluster and its day-count rather than picking one worst episode from it.

**Never write "n/a" in the Drop (×100) / vs TAB column, even for a noise-floor or non-spike row.** There is always a real number available — the LDAU range, the raw ratio (labeled "unreliable" if it's noise-floor territory), or the absolute figure (e.g. "6 LDAU / 0.5% of Ep 1" for a finale row). Put the actual number in and caveat it in the text next to it; don't blank the cell. (Corrected on The Fae Chronicles 2026-09-08 — Tejas: "it's stupid that you have left N/A in the summary.")

**Noise floor caveat when audience gets small** (per [[cliff-donor-project]]'s Beast Taming Mother lesson): below a few hundred absolute LDAU, flag that single-episode swings are noisy but multi-block trends (sustained losses across many consecutive blocks) are still real signal — say so explicitly in the footnote/Overall section rather than silently trusting or silently dismissing small-N data (Crushed & Crowned ep 490+ used this framing).

**Why:** First version (Rogues v1) had no benchmark and a purely descriptive page 1 — corrected to recommendations-first. Second correction (this entry): the recommendations lived in a separate "What to Improve" block below Key Spikes; Tejas wants Key Spikes at the very top with the action calls folded directly into it, and wants the problem points visible on the graphs themselves via pointers, not just described in table text.

**How to apply:** Every future show's episodic retention xlsx follows this exact structure without being asked again.

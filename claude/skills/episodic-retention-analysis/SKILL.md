---
name: episodic-retention-analysis
description: Analyze a Pocket FM-style show's episodic retention CSV export into a 2-page xlsx report — Key Spikes table up top (recommendations folded in, never a separate section), benchmarked against The Alpha's Bride, pointer-annotated charts. Use whenever asked to do an "episodic retention analysis" on a show's episodic CSV export.
---

# Episodic Retention Analysis

Turns a CMS episodic-performance CSV export into a locked-format 2-page xlsx:
page 1 is judgment (Key Spikes + Overall + 3 charts), page 2 is the raw data
those charts read from. The format is fixed — don't redesign it — but every
number and every row of narrative on page 1 requires a human (or your) read
of the actual data. This skill will not write a good report if you skip
straight to the template; the diagnostic pass is most of the work.

Two scripts do the mechanical parts:
- `scripts/diagnose.py` — run this FIRST on every new show. Prints
  benchmark ratios, individual spikes, release-cadence structure, and
  noise-floor warnings. It does not decide what matters — you do, from its
  output.
- `scripts/report_template.py` — `build_report()` renders the locked xlsx
  once you've written the content. It does not pick spikes or write prose.

## Step 1 — Validate the input file before trusting it

```
python scripts/diagnose.py "<path to show CSV>"
```

It auto-checks the Show ID column for you and refuses to proceed silently
mixed. Two failure modes to know about, both seen in practice:

- **The CSV is mixed with another show's rows** (usually The Alpha's Bride
  benchmark rows bundled into the same export). `diagnose.py` prints a
  warning and the show_ids found — re-run with `--show-id <id>`. Never
  trust a row count at face value; a "969-row" file that should be 268
  episodes is a silent bug waiting to corrupt every stat downstream.
- **The raw CSV wasn't in the show's folder at all.** If someone already
  built a retention xlsx for this show in a different format, its "raw
  data" sheet often carries the original CMS columns verbatim — pull it
  out with openpyxl (`data_only=True`) and write it back to a CSV. Get
  every column through `Moving Avg 50` (last CMS column) — an off-by-one
  column slice silently drops it and `report_template.py` will KeyError.

Two column-name schemas exist across exports — `diagnose.py` and
`report_template.py` both already handle the fallback:
`CB D0+ Drop% overall` (newer exports) vs `CB D0+ Drop% d7` (older/TAB
exports). Don't assume either name; use `r.get(...)` with a fallback.

## Step 2 — Run the diagnostic, read all of it

The output has five sections. What each one is for:

1. **Basics** — Ep1/Ep51/final LDAU, retention %, TAB's retention % at the
   same episode. This is your headline stat, but see the caveats below
   before you trust it at face value.
2. **Release cadence** — batch count, mega-dump warnings (>=15 episodes on
   one Launch Date), hiatus warnings (>=14-day gaps). **Read this before
   the block ratios below** — a block whose window sits inside a mega-dump
   date didn't decay over weeks, it decayed within hours of a binge, and
   the TAB ratio for it means something different.
3. **Block-level benchmark ratios** — 20-episode blocks from Ep51, each
   show block's drop ÷ TAB's drop over the same episode range. `>=1.5x`
   or `<=0.5x` is flagged. This is where "the story problem" usually
   surfaces — but always cross-reference against section 2 and the
   noise-floor check first.
4. **Top 20 individual-episode spikes** — single-day drop-rate outliers,
   batch openers already excluded (a batch opener shows an LDAU *rise*
   from returning readers, not a drop — including it would be noise).
5. **Completion rate (%90 Comp) trend** — the engagement-quality check.
   If this stays flat through a retention break, the break is a
   return/churn problem, not a story-quality problem for people who show
   up — say so, it's a genuinely useful distinction every time.

## Step 3 — The judgment calls (this is the actual skill)

**TAB is the fixed benchmark — not a hedge, not "one data point among
many."** Use it as the standard throughout. The genre-mismatch caveat
still applies (say so when it's not a romantasy), but don't soften TAB's
role as the comparison every show gets measured against.

**Every finding and every suggestion comes from the data — never from
guessing what an episode title implies about plot content**, unless
you're citing an already-verified prior diagnosis (see below). "Titles
read as lower-stakes filler" or similar narrative color is speculation
wearing a confident tone — cut it. What the data actually shows: where
retention falls, by how much, against TAB, and whether completion or
monetization moved with it. Stick to that.

**Never flag a window wider than 100 episodes without a specific,
data-driven reason the whole span is genuinely one finding.** Don't
default to reporting the full extent of a run of TAB-ratio-flagged
20-episode blocks just because they happen to sit next to each other —
that produces vague, unactionable ranges like "Ep 1-887" or "Ep 291-470."
Instead:
- Narrow to the tightest range that's actually justified — the specific
  cluster of days, or the specific stretch where a self-relative or
  completion-funnel signal is sharp (per the techniques below).
- If a genuinely uniform underperformance really does run past 100
  episodes with no internal variation, say so explicitly and name why
  you're confident it's one continuous thing rather than several
  concatenated blocks (e.g. "block ratios are flat at 1.8-2.2x for all
  N blocks with no step changes" — a real, stated reason, not silence).
- A release-cadence or noise-floor caveat covering a wide range is fine
  to state as context, but the *actionable* suggestion inside that range
  should still be pinned to the tightest defensible window (see the
  self-relative-acceleration and completion-funnel techniques above —
  both usually produce a range well under 100 episodes).
(Locked 2026-09-08 — Tejas: "dont give me inputs above 100 episodes
without any reason, if there is a genuine case, give me a genuine
understanding.")

**A "spike" is a day or tight cluster of days; a "slow bleed" is a
20+ episode stretch with no single dramatic day but a sustained elevated
ratio.** Report both kinds in Key Spikes — a self-relative spike scan
alone misses slow bleeds entirely (they only show up against the TAB
ratio). Always report **at least 3-4 rows**. When spike days sit close
together, name it as one clustered row ("7 elevated-drop days within an
11-episode span") rather than picking the single worst day and discarding
the rest — the clustering is itself the signal.

**Release-cadence distortion.** If a block's dramatic ratio traces to a
mega-dump or sits right after a long hiatus, say so explicitly and
caveat the ratio as an artifact — but still name the single sharpest
individual day within it if one exists; that day can be real signal even
when the aggregate ratio is inflated by compressed release timing.

**Noise floor.** Below a few hundred absolute LDAU, one or two listeners
leaving swings a ratio several-fold. Once the show's baseline (Ep51) LDAU
is small, or once the run falls under ~50 LDAU partway through:
- Say so explicitly, scope your conclusions to the range where the
  numbers are still large enough to trust, and mark the rest **directional
  only** — report the shape (keeps shrinking / recovers / stays flat), not
  the specific multiples.
- **Never write "n/a"** in the Drop column for one of these rows. There is
  always a real number — the LDAU range, the raw ratio labeled
  "(unreliable)", or an absolute figure like "6 LDAU / 0.5% of Ep 1" for a
  finale row. Blank cells read as sloppy; caveated real numbers read as
  rigorous.

**Shows longer than TAB's 701-episode benchmark.** No ratio applies past
Ep701 — say that plainly, report the raw LDAU trend for the tail instead
("8,028→5,129 LDAU, 63.9% retained"), and don't force a comparison.

**A release-cadence caveat is not an excuse to stop looking.** It invalidates exactly one thing — the TAB block-ratio comparison, because that comparison assumes both shows release on the same real-time cadence. It does NOT invalidate:
- **Self-relative acceleration**: compare each block's drop rate to the show's OWN prior block (not TAB's). A reader still consumes episodes in sequence even inside a same-day dump, so a point where the show's own churn rate suddenly doubles is real content signal, calendar-independent. Flag it (`>=1.5x` the prior block, or `<=0.6x` for a genuine deceleration worth noting positively), but only trust it where the audience is still large enough that a couple of listeners can't manufacture a 2x swing (same noise-floor threshold as everywhere else in this method).
- **Monetization step-changes**: check `ep_coins` / `ep_pu` for a jump from ~0 to real numbers — that's a paywall lock, and it's worth reporting on its own terms (e.g. "post-paywall audience decays at half the pre-paywall rate" is a real, positive finding, independent of release timing).
- **The completion funnel** (see below) — also calendar-independent.
When you catch yourself writing "this ratio is a release-cadence artifact" and stopping there, that's the signal to run these three checks before finalizing the report — a dump-compressed show still has real, actionable content signal in it, just not in the TAB ratio. (Corrected on "Danger I Can't Resist" 2026-09-08 — Tejas: "this release gaps should not be the problem honestly. can you look for other signals.")

**When a mega-dump makes the audience-size ratio unusable, don't stop there — check the completion funnel (%10/%25/%50/%75/%90 Comp) instead.** Release-cadence distortion breaks the *audience-departure* signal (LDAU-based ratios), but it does NOT break the *completion* signal, because completion is measured within a single episode regardless of when that episode was consumed. Compare `%50 Comp` against `%90 Comp` for each block: if `%50` stays high (~95%+) while `%90` collapses, readers are reaching most of the episode and bailing near the end — a real, release-cadence-immune content signal, often sharper and more specific than anything the block ratio can tell you. Rule out episode-length and monetization-gate explanations (check `Duration (Hr)` and `ep_coins`/`ep_pu` for a step change at the same boundary) before attributing it to content. If the same shape recurs more than once in a show, say so explicitly — a repeated mechanic is a stronger finding than a single occurrence. (Found on The Eclipse Princess 2026-09-08 — three recurring collapses, Ep 581-600/841-860/895-910, each %90 Comp cratering to 19-42% while %50 Comp held 96-99%, tracking with grim title clusters at each occurrence.)

**Genre mismatch.** If the show isn't a romantasy (progression fantasy,
cultivation, etc.) while TAB is, say the benchmark is being used for
retention-curve *shape* only, not as a validated story-trope match.

**Reuse a verified prior diagnosis if one exists.** If this show has
already had its story read by a human or a prior analysis (character
names, plot beats, a confirmed break cause), cite that instead of
re-guessing from episode titles alone — it's more accurate and it's
faster. Only fall back to titles-and-numbers inference when nothing else
exists, and say plainly that's what you're doing.

**Always benchmark against The Alpha's Bride (TAB).** Canonical file:
`~/Downloads/TAB Data/TAB_FULL_701eps.csv`, show_id
`cbc35fa13bbe154873ec97f78f2b4cf4b66c7d31`. This is `report_template.py`'s
default; override with `tab_path=`/`tab_show_id=` if your team keeps the
benchmark file elsewhere.

## Step 4 — Write the page-1 content

Page 1's structure is locked — don't redesign it, just fill it in:

1. **Title + subtitle** (show name, episode count, "Benchmarked vs The
   Alpha's Bride (701 eps)", any one-line context — acquired/paywall show,
   burst release cadence, whatever's relevant).
2. **One bold headline sentence** directly under the subtitle — the single
   punchline a reader should walk away with even if they read nothing
   else.
3. **KEY SPIKES table — first thing on the page**, before any narrative.
   Columns: Episode | Event | Drop (×100) / vs TAB | What's happening.
   There is **no separate "recommendations" or "what to improve" section**
   — fold every actionable call directly into the relevant row's "What's
   happening" text, self-contained (never "see Recommendation 2" — that
   section doesn't exist).
4. **OVERALL bar + bullets** — supporting narrative only: net
   retention-vs-TAB stat, early-funnel read, completion-rate/engagement
   read, release-cadence note. Nothing here should be the *first* place a
   reader learns something important — that's what Key Spikes is for.
5. **Three charts, always in this order**: (a) Drop%×100 / MA10 / MA50,
   (b) Listening DAU per episode, (c) Retention Index vs TAB (both
   indexed to 100 at Ep51). Every chart gets red diamond pointer markers
   with episode-number labels at the worst point of each *actionable*
   cluster from Key Spikes (skip clusters marked "no action needed").

Page 2 "Raw Data" needs no authoring — `build_report()` populates it
entirely from the source CSV plus the TAB alignment columns the charts
read from.

## Step 5 — Build it

```python
import sys
sys.path.insert(0, "<path to this skill>/scripts")
from report_template import build_report

build_report(
    show_name="...",
    csv_path="...",
    out_path=".../<Show Name> - Episodic Retention Analysis.xlsx",
    headline="...",
    spike_rows=[
        ("Ep X–Y", "Event label", "up to -N.N\nR.Rx TAB", "Self-contained what's-happening text..."),
        ...
    ],
    overall_bullets=[...],
    chart_markers=[ep1, ep2, ...],   # worst point of each actionable cluster
    subtitle_extra="...",             # optional one-liner context
    footnote_extra="...",             # optional, appends to the standard footnote
    show_id_filter=None,              # set if the CSV needed filtering in Step 1
)
```

## Step 6 — Sanity-check before sharing

- Re-open the file and check `Raw Data` row count matches the show's real
  episode count (catches the mixed-show-id bug immediately).
- Check no cell in the Drop column reads "n/a" — every row should carry a
  real number.
- Eyeball the three charts for the red pointer markers landing where you
  expect.

## Output convention

When doing a batch of shows in one sitting, put them all in one dated
folder (e.g. `Updated Episodic retention analysis/`) rather than scattered
across each show's own source folder — makes it a single thing to hand
off.

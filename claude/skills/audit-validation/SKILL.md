---
name: audit-validation
description: Produce the extended version of a Creative Audit, validated against what listeners actually did. Takes the Creative Audit plus a show's episodic retention export and its episode-tagged comments, and renders a second, separate HTML document that contains everything the audit said and adds a verdict to each finding: which ones the data supports, which cost nothing measurable, which drops the audit missed, which are not creative problems at all, what listeners said at those episodes, and a ranked set of fixes with the measured cost of each. The original audit is left untouched and both documents stand alone. Use after `creative-audit` when retention and comments are available, on a request like "validate the audit", "check this against the data", or "what did the numbers say".
---

# Audit validation

The Creative Audit reads scripts and says what a show does. This skill asks a
different question: **did any of it cost the show listeners?**

## The output is report 1 plus the data, not a companion to it

The document this skill produces is the **extended version** of the Creative Audit. It
carries every section of the audit — the promise, the cast, the ten questions, the acts
in order, the resolutions, the broken promises, the trouble zones, the cliffhanger
ledger — and adds a verdict beside each one, the measurements behind it, what listeners
said there, and the fixes. A reader who has never seen report 1 can read report 2 alone.

**Both documents are kept, separately.** The audit is the script-only record and must
stay that way: it is the independent read, and a reader needs to be able to see what
the scripts said before any number touched it. Never edit the audit to add data, and
never delete it once the extended report exists.

This is done by **importing the audit's own renderer**, not by copying its prose:

```python
m = load_audit('build.py')      # the show's Creative Audit renderer
m.ranked_table(m.HOOKS, health) # its sections, its authored constants
m.act_blocks(...)
```

One content source, two documents, and they cannot drift apart. Rebuild the audit after
building the extended report and diff it: it must come back byte-identical.

It needs three inputs and will not run without all three.

| Input | What it is |
|---|---|
| **The Creative Audit** | `audit.html` and the JSON files beside it, from `creative-audit` |
| **Episodic retention** | the show's per-episode export: drop rate, listeners, completion, revenue |
| **Comments** | listener comments tagged to episodes |

---

## The rule that matters most here

> **A creative finding and a retention drop are two different claims. Do not let
> either one become evidence for the other by assumption.**

The Creative Audit was deliberately built without retention data so its findings
could not be circular. That discipline is only worth something if this skill keeps
the two apart until the moment it compares them. Never go back and re-weight a
creative finding because the data disagreed; record the disagreement.

**Most creative findings will not move retention, and that is the point.** On the
first show this ran against, seven of nine trouble zones sat between 0.85x and 1.01x
of the show's own baseline. Those are real craft problems that cost nothing
measurable. Saying so is the most useful thing this document does, because it stops a
team spending a rewrite on a problem no listener noticed.

---

## Five verdicts, and every finding gets one

| Verdict | Means |
|---|---|
| **CONFIRMED** | the audit flagged it and the data agrees: drop is meaningfully above the show's own baseline |
| **NO COST** | the audit flagged it and the data is flat. A craft note, not a retention problem |
| **MISSED** | the data shows a real drop and the audit has nothing there |
| **CONTESTED** | the two disagree in a way that needs a human: e.g. drop is high but comments blame something the audit did not look at |
| **NOT CREATIVE** | the drop is real and large, and the cause is outside the script: a price change, a narrator swap, a delivery fault. `trap_check.py` assigns this, and it is the most useful verdict on the page, because nobody else in the pipeline is looking for it |

A document that returns all CONFIRMED has almost certainly fitted itself to the
answer. Expect a spread.

---

## The four tags used inside an act

The verdicts above are for the whole-show tables. Inside an act, every problem carries
tags instead, and the distinction that matters is what counts as proof.

| tag | means | applies to |
|---|---|---|
| **Validated by data** | measured cost: the zone is CONFIRMED against both baselines | content-led problems |
| **Validated by comments** | listeners complained here at well above this show's own rate | either |
| **Story may explain** | a blind read found something structural | data-led problems |
| **Cause outside the script** | a paywall, a narrator change, a delivery fault | either |
| **Not explained** | nothing accounts for it, and the card says so | either |

**Story evidence never reads as "validated".** A judgment about a script is subjective
and the word does not apply to it. A blind read is an explanation, not proof, and the
card says that in those words.

**Never force a story onto a number.** When the data shows a problem and neither the
comments nor a blind read accounts for it, the card says we are not sure and blames
nothing. An invented cause is worse than an admitted gap, because someone will act on
it.

**Comment validation is a rate, not a count.** A busy stretch has more of everything.
The test is the share of complaints against the show's own complaint share, and it
needs a floor of a few comments before it means anything.

---

## Phase 0 · Repair the level series, and never confuse it with the rate

```bash
python toolkit/repair_levels.py --data data.json --out data.json
```

**`Drop %` is not the decline in `LDAU`.** They are two different measures in the same
export. On the first show this ran against, episode 200's audience level fell 0.078%
while its drop column read 1.539%, and at episode 560 the level *rose* while the drop
column read 3.83%. Both columns are real.

This matters because of one specific mistake, which this skill made and shipped:
**cost was derived by compounding the rate against the level.** Every "listeners lost"
figure on the page was inflated, some by twenty times, and the ranking of the fixes was
wrong. A headcount is a headcount. Read it off the level.

- **rate** (`vs_show`, `vs_benchmark`) → how fast people left. This drives the verdicts.
- **level** (`level_excess`) → how many people. This drives the cost and the ranking.

Report both, and say plainly that they disagree where they do.

The repair itself fixes three defects, all real: a level that **rises** more than 12%
(a double-count), a **zero or missing** level on a real episode, and a **one-episode dip
that recovers** (audience cannot come back, so a V is an artifact of that row). Small
upward wiggles under 12% are measurement noise and are left alone — an early version
treated them as defects and flagged 140 of 665 episodes, because one low outlier made
every episode after it look like a rise.

It also computes the **survival headline**: of 100 listeners at the baseline episode,
how many reach the end. Put that number on the page. On the first show it was 8.

---

## Phase 1 · Load and normalise

```bash
python toolkit/load_data.py --retention <csv> --comments <csv> \
       --show "The Vampire Prince" --out data.json
```

### The retention export

Column names vary between exports. The loader maps them; check what it found.

| What it needs | Names seen so far |
|---|---|
| episode number | `Story No.`, `Story no.` |
| drop rate | `CB D0+ Drop% d7`, `Drop % (Modified)` |
| listeners | `CB D0+ d7`, `LDAU (Modified)` |
| cumulative hours | `Duration cum. (Hr)` |
| completion | `%10 Comp` … `%90 Comp` |
| revenue | `ep_revenue`, `ep_pu`, `ep_coins` |

**The file usually contains two shows.** One is the subject; the other is a benchmark
that the export includes for comparison. Pass `--show` and check the loader's report
of what else it found.

### Five traps, all of which have actually happened

1. **Early-episode falloff is not a creative problem.** Episode 1-10 drop is
   dominated by people sampling the show and leaving. On the first show this ran
   against, eps 1-10 showed **6.26x** the baseline, higher than anything else in 665
   episodes. **Baseline everything from episode 51.**
2. **Paywall and free-window boundaries.** A single block an order of magnitude
   beyond anything else, often with comments about episodes no longer being free.
   Never let one drive a creative conclusion.
3. **Delivery faults self-heal.** A spike that recovers within about twenty episodes,
   with comments about episodes arriving out of order, is an ops problem.
4. **Release dumps.** A cluster of episodes published at once after a gap.
5. **Comments are written by survivors.** The people who left are not in the comment
   file. On the first show this ran against, episodes 105-125 were the second-worst
   CONFIRMED zone in the show — 1,981 listeners above baseline walked out — and the
   comments there run **129 delight to 55 complaint, with nobody saying they are
   leaving**. A happy comment section is not evidence a stretch is working. Use
   comments to learn *what* the people who stayed were struggling with, and let
   retention tell you *whether* people stayed. Never read silence as approval.

### The comments

Each row needs an episode number, the text, and ideally a like count. Episode numbers
usually live inside `story_title` as `Ep 490 - But...`. The loader parses both that
and a bare `episode_number` column.

---

## Phase 2 · Test every creative claim

```bash
python toolkit/test_claims.py --audit <dir with the audit JSONs> --data data.json \
       --out verdicts.json
```

For each trouble zone, broken promise, dead run and act boundary in the audit, it
computes the drop rate across those episodes against two baselines: **the show's own
median from ep 51**, and **the benchmark show at the same cumulative hour**. Matching
on hours rather than episode numbers matters, because episode lengths differ between
shows.

It also runs the reverse: every ten-episode block ranked by drop, with whether any
creative finding covers it. Uncovered blocks above the threshold become **MISSED**,
and contiguous blocks merge into one zone — reporting them separately split one
paywall event into three findings and made each look smaller than the thing happening.

Two rules here were learned the hard way, and both hid real damage:

- **A show's own baseline flatters its late episodes.** The people still listening at
  episode 500 are the committed ones, so a late disaster can score under the threshold
  and look fine. The narrator-swap bleed scored 1.26x and 1.33x against the show and
  **1.77x and 2.11x against the benchmark**. Test both; a block clears only if it
  clears both.
- **Only a CONFIRMED finding explains a block.** A NO COST finding explains nothing by
  definition. While wide findings counted as cover, a 150-episode cast-bloat zone that
  averaged out to 0.99x concealed a 20-episode bleed worth 1,146 listeners inside it.

---

## Phase 2a · Classify every comment

```bash
python toolkit/dump_comments.py --data data.json --out sentiment_batches/ --balanced 13
# one agent per batch, references/sentiment-prompt.md
```

The per-episode reaction curve needs a bucket for **every** comment, not a read of a
few windows. Fan out: roughly 450 comments per agent, each returning per-episode counts
of positive, negative, production, money and neutral, plus the loudest comment in each
direction.

**One bucket per comment, with a fixed precedence** (money > production > negative >
positive > neutral) so two agents given the same batch return close to the same
numbers. A comment that loves the story and hates the narrator is `production`: that
distinction is the whole point, because it separates a writing problem from a
casting one.

Counts must reconcile against the source. An agent whose per-episode numbers do not sum
to the batch total has skipped comments, and the curve will be wrong in a way nobody
notices.

---

## Phase 2b · Check the cause before you believe the zone

```bash
python toolkit/trap_check.py --data data.json --verdicts verdicts.json \
       --reads comment_reads/ --out verdicts.json
```

Run this **after** the comment reads, and re-run it whenever a read lands. It asks one
question of every CONFIRMED and MISSED zone: *is this a script problem at all?* It
looks for a revenue-per-listener step that never reverses, a drop shaped like a spike
with a decay rather than a stretch, an episode-length change, and a comment majority
blaming the narrator or the paywall. Any of those flips the zone to **NOT CREATIVE**.

On the first show this ran against it flipped the two largest drops in 665 episodes:

| zone | was | cause |
|---|---|---|
| eps 551-590, 2.02x, 2,507 listeners | MISSED | paywall at ep 564 — revenue per 1,000 listeners went 78 → 123 → 157 and never came back; drop spiked to 10.5% on a single episode and decayed over sixteen |
| eps 291-310, 1.30x, 1,146 listeners | MISSED | narrator swap at ep 291 — 303 of 516 comments in the window are about the voice, 43 said they were leaving |

Both had been written up as the show's biggest missed creative problems. A writers'
room would have spent two rewrites on a pricing decision and a casting decision.

**Comment evidence is only admissible for episodes a theme actually names.** An early
version let a 41-episode comment window that overlapped four episodes of a 71-episode
finding assign that whole finding a production cause.

---

### One more trap, specific to the extended report

**An act overlapping a NOT CREATIVE zone has a contaminated number.** A paywall inside
an act raises that act's drop rate and none of it is writing. On the first show, Act 18
read 1.75x, the worst of twenty acts, purely because the price change at episode 564
sits inside it. The acts table marks these in their own column, and the worst-act claim
names the worst **clean** act. Never let a contaminated act headline a section.

---

## Phase 2c · Let the data pick the episodes, then read them blind

```bash
python toolkit/detect_events.py --data data.json --claims claims.json --out events.json
# then one agent per batch of flagged episodes, references/episode-read-prompt.md
```

Testing creative findings against data can only ever confirm or clear something
someone already believed. This runs the other direction. Five detectors run **inside
each act** with no reference to the script:

| detector | fires when |
|---|---|
| `drop_spike` | an episode's drop stands far above the act's own median |
| `level_step` | the largest one-episode fall in headcount, well above the act's median |
| `completion_dip` | far fewer people finish this episode than finish the act's others |
| `comment_surge` | an episode draws many times the act's median comment count |
| `revenue_step` | revenue per listener steps up and does not return: a pricing boundary |

Then **send agents to read the flagged episodes without telling them why they were
chosen.** An agent told a drop happened will find a reason for it. One asked only to
describe an episode reports what is there, and the `odd` field is where the answer
usually is.

On the first show this found what no creative reading had: an episode of 471 words,
third-shortest of 666, that dissolved the story's central obstacle by declaration and
was abandoned by 85% of listeners; an episode with zero dialogue and both leads absent;
and two finale scripts shipped as open working drafts with revision marks and a
duplicated scene still in them.

It also clears things. The episode at the centre of the show's loudest comment surge
came back **structurally ordinary**, which is how the narrator swap was confirmed as
the cause rather than the writing.

---

## Phase 3 · Read the comments where it matters

Comment volume alone says little; a spike can be love or fury. **Send agents to read
the comments at the episodes the first two phases identified**, using
`references/comment-read-prompt.md`.

Each agent gets one episode window and returns what listeners are actually saying:
confusion, complaint, delight, what they name, and whether they mention the thing the
audit flagged. Agents never see the creative finding they are testing, for the same
reason the arc pass never saw the hooks.

**The most useful comment evidence is specific.** "Listeners are confused" is worth
nothing. "Eleven comments at eps 290-310 ask which brother is speaking" is a finding
with a fix attached.

---

## Phase 4 · Rank by cost, then suggest

Every problem that reaches the document carries a measured cost: **how many listeners
left across those episodes above what the show's own baseline would predict.** That
number is what orders the list. A craft note with no cost goes in the NO COST table
and gets no recommendation.

Each recommendation must name:

- **the episodes** to change
- **what the data says** happened there
- **what listeners said**, quoted
- **what the audit says** is wrong creatively
- **one concrete change**, specific enough to brief a writer

**Never recommend a fix for a NO COST finding.** The discipline of this document is
that it only asks for work where work is owed.

---

## Phase 5 · Build the document

```bash
python toolkit/dump_comments.py --data data.json --out comment_windows/ \
       --windows 105-125 555-595 592-662 645-665          # Phase 3 input

# the extended report: report 1 plus the data, act by act
python toolkit/build_validation.py --claims claims.json --verdicts verdicts.json \
       --data data.json --reads comment_reads/ --notes notes.json \
       --audit-build build.py --ledger ledger.json --health health.json \
       --transit transit.json --arcs arcs.json \
       --events events.json --episode-reads episode_reads/ --sentiment sentiment/ \
       --title "Show Name" --out validation.html

# add --mark-data for a temporary review copy that tints every block the data added

# drop --audit-build and the four audit inputs to get the short companion document
# instead. Prefer the extended report: it is what the reader is asking for.
```

Everything numeric is read from `verdicts.json` and `data.json`. Everything authored
lives in `notes.json`, so the toolkit renders any show without being edited:

```json
{
  "subhead": "Does the creative audit hold up?",
  "headline": "<b>One or two sentences.</b> The answer, before any chart.",
  "cleared_note": "Why a flat verdict is not an acquittal of the craft note.",
  "finding_notes": {
    "<finding label, exactly as it appears in verdicts.json>":
      "One line: what this verdict means for this finding."
  },
  "solutions": [
    {"title": "…", "priority": "high|medium|low",
     "problem": "…", "data": "…", "comments": "…",
     "do": "one concrete change, specific enough to brief a writer",
     "where": "eps 561-590", "confidence": "high — two passes agree"}
  ]
}
```

A label in `finding_notes` that matches nothing is ignored silently, so check the
labels against `verdicts.json` rather than retyping them from the audit.

### Structure

```
  logline · what the show promises · who you need to know      from the audit
  What the data did to this read        the headline, the verdict counters, the method

  PART I    The story, act by act          the spine of the document

    Act N · Name
      Summary                             the act's own story, from the audit
      Hook and content led analysis       running hooks as tags · informational
      Content led problems                drift + broken promises, expandable
                                          tags visible collapsed, evidence inside
      Data led analysis                   retention across the act vs benchmark
                                          loss across the act vs benchmark
                                          listener reaction, episode by episode
      Data led problems                   what the detectors found, expandable
                                          validated by comments · story may explain
                                          · cause outside the script · not explained
      What to do in this act              one box

  ── Across the whole show ──────────────────────────────────────────────

  The acts, priced
  PART II   The questions that hold the show up
  PART III  The whole show at once         audit charts, then the data charts
  PART IV   Resolutions and broken promises
  PART V    Where the show loses people
  PART VI   What the data confirmed
  PART VII  What this audit missed
  PART VIII Real, large, and not the script
  PART IX   What cost nothing
  PART X    What listeners actually say
  PART XI   What to do

  The cliffhanger ledger
  Appendix  the run in ten-episode blocks
  Method and limits
```

The acts are **composed here, not borrowed**. The audit's `act_shell`, `hooks_in`,
`breaks_in` and `drift_in` supply the act and its three joins as data; this renderer
decides the shape. That is why the act can look different in the two documents without
the audit changing, and why the audit must still rebuild byte-identical afterwards.

Cards are native `<details>`. No JavaScript anywhere, including here.

Parts are numbered **as they are emitted**, so a verdict that comes back empty leaves no
gap in the numbering.

Parts II, III and IV render one two-column block per finding: **the story problem on
the left, the measurement on the right.** The `<aside>` must sit inside `.act-body` or
the grid collapses — the build asserts this, because it has silently broken before.

### Charts

Inline SVG, no JavaScript, same house style as the Creative Audit. Hover readouts are
visible elements, not `<title>`.

| Chart | Shows |
|---|---|
| **Drop across the run** | per-episode drop with the show's baseline, creative zones shaded behind, benchmark as a second line |
| **Cost by finding** | listeners lost above baseline, per finding, ordered |
| **Comment volume and heat** | comments per episode, with the negative share |
| **Completion curve** | `%90 Comp` across the run: within-episode dropout, which drop rate cannot see |

A bar that looks like a proportion **is** one. Every episode axis carries the act
boundaries from the audit, so the two documents can be read side by side.

---

## Before you ship

- [ ] Everything baselined from episode 51, and the early falloff excluded by name?
- [ ] Benchmark matched on cumulative hours, not episode numbers?
- [ ] Every large block checked against the five traps before any creative reading?
- [ ] Every finding carries one of the four verdicts?
- [ ] Is there a spread of verdicts, or did everything come back CONFIRMED?
- [ ] Every NO COST finding left without a recommendation?
- [ ] `trap_check.py` run after the comment reads, and every flip read and believed?
- [ ] Any NOT CREATIVE zone kept out of the creative recommendations?
- [ ] Part numbering sequential on the rendered page, with no gaps where a verdict
      came back empty?
- [ ] `<meta charset="utf-8">` present — without it every middot renders as mojibake?
- [ ] Does any headline number appear twice on the page with two different values?
- [ ] Is every cost figure taken from the level series, never compounded from the rate?
- [ ] Is the survival headline on the page?
- [ ] Do the authored notes quote the same numbers the charts compute, after any
      change to how cost is measured?
- [ ] Does the extended report contain every section of the audit, and can it be read
      by someone who has never seen report 1?
- [ ] Does the audit still rebuild byte-identical after the extended report is built?
- [ ] Are both documents on disk, the audit untouched?
- [ ] Is every act in the acts table, including any that ends before the baseline and
      cannot be priced?
- [ ] Is any act whose number is contaminated by a NOT CREATIVE zone marked as such?
- [ ] Every recommendation naming episodes, data, a listener quote, and one change?
- [ ] Comment quotes checked against the source file, not an agent's summary?
- [ ] Charts proportional, act boundaries drawn, no JavaScript?
- [ ] Does the document say plainly which claims are measured and which are inferred?

## Limits to state in the output

- **Retention is measured. Creative causation is inferred.** A drop at an episode says
  people left. It does not say why. Comments are the only witness, and they are a
  self-selected few hundred out of many thousands who said nothing.
- **A CONFIRMED finding is a correlation.** The audit found a craft problem and the
  data found a drop in the same place. Say that, not that one caused the other.
- **A NO COST verdict is not an acquittal of the craft note.** It says the problem did
  not show up as churn in this run.
- **Late findings are tested on a hardened audience.** By episode 650 the remaining
  listeners will finish almost anything, so a break that would cost listeners at
  episode 100 can score 1.05x at 660. Say this beside every finale verdict rather than
  letting a flat number read as a clean bill of health.
- **Comments are written by survivors**, and they measure anger, not departure. The
  second-worst CONFIRMED zone on the first show ran 129 delight to 55 complaint with
  nobody saying they were leaving, while 1,981 listeners walked out.
- **Completion rate rises across a run on its own**, because the surviving audience is
  more committed. Read the completion curve against its own trend, never absolutely.
- **A cause the trap check names is a mechanism, not a proof.** A revenue step plus a
  matching comment theme is strong evidence. A revenue step alone is a hypothesis.
- **Comment themes are read by agents, not computed.** Counts are real; the grouping
  is judgment, and should be labelled as such.
- **Thresholds are choices.** Put them on the page so a reader can disagree with the
  line rather than with the conclusion.
- **Rate and level answer different questions and can disagree.** A stretch can run at
  the show's own baseline rate and still shed more listeners than baseline predicts, and
  a late stretch can post a terrible rate while losing almost nobody. Never derive one
  from the other.
- **Sentiment counts are read by agents against a fixed precedence.** They are
  reproducible, not objective. State the rule on the page.

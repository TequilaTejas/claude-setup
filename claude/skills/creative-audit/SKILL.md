---
name: creative-audit
description: Read every script of a serialized-audio show and produce the Creative Audit — a plain-language HTML report on what the show promises, the acts it moves through, the questions that hold a listener, which episodes actually keep each one alive, where nothing is live at all, and which promises the show breaks. Two independent agent passes, one for questions and one for acts, that never see each other. Script-only: no retention data, no listener comments, no benchmark, so nothing it finds can be circular. Use for a "creative audit", "hook audit", "opening promises", or "which promises does this show make and keep" from a folder of episode scripts. The report it writes is the input to the `audit-validation` skill, which tests these findings against retention and comments.
---

# Creative audit

This skill reads every script of a serialised show and reports on four things, at
four different sizes.

| | | |
|---|---|---|
| **The opening promise** | the whole show | what fantasy, emotion or transformation the first few minutes promise |
| **Arcs** | 40-120 episodes | the stretches the story moves through |
| **Hooks** | cross arcs | what a listener is still holding on to |
| **Cliffhangers** | one episode | how each ending earns the next episode, **and whether it earns it for the right reason** |

**Read [`references/taxonomy.md`](references/taxonomy.md) before you start.** It
defines all four precisely and shows how to tell them apart. Confusing a hook with a
cliffhanger, or a promise with a plot, produces a report that is fluent and wrong.

The measurement that matters most and is easiest to miss: **a cliffhanger has two
independent scores.** How hard it pushes, and whether it pushes on what the show
promised. An ending can be gripping and still lose the listener, because it is
gripping about the wrong thing.

**Script only.** No episodic CSV, no LDAU, no drop-%, no benchmark show. If a data
pack is present, ignore everything but `scripts/` and `scripts_txt/`. Anything this
report says about listener attention is **inferred from the script** and must be
labelled that way.

Sibling skill: `master-brief-generation` does the retention-data diagnosis. This one
deliberately does not. Do not borrow its metric.

---

## Write for someone who knows nothing

This matters as much as the analysis. Assume your reader has never heard of the
show, does not know a single character's name, and does not know what a "hook" is.

- **Name people the first time.** Not "Mara" but "Mara, the human woman married off
  to the enemy prince to buy a peace."
- **No invented jargon.** If the show has a term, explain it in the same sentence.
- **Say the number in words that mean something.** Not "recurrence 1 of 3" but "the
  show mentions it in 17 of the 663 episodes it stays open."
- **Short sentences.** One idea each.
- **Codes need a key.** `H1`, `B2`, `D3` are fine in tables because they keep tables
  narrow, but the page must explain them before first use.
- **Describe, do not grade, in the left column.** "The show answers this in one line
  of narration" belongs on the left. "This is the clearest broken promise on the
  page" belongs in the panel on the right.

Bad: *H5 opens ep 251, resolves 663, pull 11/12, verdict paid late.*

Good: *Question 5: who is the second man living inside Kel's body? The show asks it
at episode 251 and answers it at episode 663. That is 412 episodes of waiting.*

---

## The one rule carried over

> **Go to the raw script. Form your own read. Never inherit a prior one.**

Do not build hooks from episode summaries written by someone else, a creative brief,
or an earlier analysis. A summary records *what happened*. A hook is *what was asked
and left hanging*. A show's best hook is often a single line of dialogue that a
summary drops.

When you write that a hook opened at ep 37 and closed at ep 204, you must have read
ep 37 and ep 204.

---

## The pipeline

**Two passes read the scripts, and they must not see each other.**

```
                        scripts_txt/
                   ╱                  ╲
    ╔═════════ HOOK PASS ═══════╗   ╔══════ ARC PASS ═══════╗
    ║ N agents x 25 eps         ║   ║ 2 offset passes,      ║
    ║ extraction-prompt.md      ║   ║ 50 eps each           ║
    ║                           ║   ║ arc-prompt.md         ║
    ║ records, block summary,   ║   ║ never sees the hooks  ║
    ║ what it hands on/picks up ║   ║                       ║
    ╚═══════════════════════════╝   ╚═══════════════════════╝
              │                                │
    build_summary.py -> summary.md    merge_arcs.py -> arcs.json
    merge_extract.py -> ledger.json   consensus >=2 agents, evidence
              │                       attached to every boundary
              │                                │
    YOU: cluster into 10-12 hooks     one agent per act writes it
         -> analysis.json                  act-story-prompt.md
              │                                │
    hook_health.py -> health.json     arc_transit.py -> transit.json
              │                                │
              ╰───────────────┬────────────────╯
                              ▼
                    build_audit.py -> audit.html

  Where the two passes agree, that agreement is evidence.
  Where they disagree, the disagreement is a finding.
```

**Gates:** `split_scripts.py` exits 1 on a gap · `merge_extract.py` exits 1 on a
missing episode · `merge_arcs.py` rejects single-agent turns · `hook_health.py`
exits 1 rather than score a hook it cannot see · `build_audit.py` validates the HTML.

## Phase 1 · Prepare the scripts

Input is CMS production scripts. Two formats appear: plain prose, and audio
production scripts with `[SFX: ...]` and `[MUSIC: ...]` cues mixed into the prose.
Both split on the same `Ep N — Title` header. Typical episode is 7-10 KB, 400-500
lines. A 665-episode show is about 5.3 MB.

```bash
python toolkit/split_scripts.py --in pack/scripts --out pack/scripts_txt
```

Writes zero-padded `epNNNN.txt` and prints a gap report. **Read the gap report.**
It exits 1 on a missing episode, a duplicate, or a file under 2 KB, because any of
those changes what you can claim about how long a question stayed open.

State the episode count, the range, and any gaps on the finished page.

---

## Phase 2 · One read, in batches

5 MB will not fit in one honest read, so fan out. **25 episodes per agent.** Launch
them in one message so they run together. There is a hard cap of 20 concurrent
agents; plan waves around it.

Each agent gets `references/extraction-prompt.md` **verbatim**, with `{DIR}`,
`{FIRST}`, `{LAST}`, `{OUT}` and `{LEADS}` filled in. The identical wording is what
makes 27 separate reads mergeable. `{LEADS}` must name the show's leads; never let
an agent decide for itself who the protagonist is.

**Do not raise the batch size for a long show.** A 665-episode show is 27 agents,
not 14 agents reading 50 each. Run it in **two waves** and inspect the first wave
before spending the second. A flaw found at episode 350 costs half what the same
flaw costs at 665.

### What each agent returns

| Output | Why |
|---|---|
| Episode records | the raw material |
| **A plain summary of its 25 episodes** | becomes part of the whole-show summary |
| **`open_at_end`** | questions still hanging when its block finishes |
| **`open_at_start`** | questions already running when its block began |

### The handoff lists are how the batches get joined

Each agent sees 25 episodes and nothing else. That independence is deliberate: no
agent can inherit another's mistake. The cost is that a question opened in block 1
and answered in block 12 looks like two unrelated events.

```
  agent sees:   [ ep 251 ──────── ep 275 ]
  the truth:    [ ep 3 ──────────────────────────── ep 287 ]
                 ↑ block 1 reports an open that never closes
                              block 12 reports a close with no open ↑
```

`open_at_end` and `open_at_start` are the relay baton. Block 1 lists what it is
handing on. Block 2 lists what was already running when it started. Where those
match, a thread crosses the seam.

### Inspect wave 1 before wave 2

Pull three episode records and read them as a person would.

- Are the questions phrased as questions?
- Does `evidence` point at a line in the script, or paraphrase the plot?
- **Is any field being interpreted differently by different batches?**

That last one is the killer. Noise is survivable; inconsistency is not. Three fields
have already been caught meaning different things in different batches: `lead` on a
two-hander show, `absent` versus merely powerless, and `new_names` meaning new-to-
batch versus new-to-show.

### Repairing one field without re-running everything

If a field comes back inconsistent, do not re-run the whole extraction.
`references/leads-repair-prompt.md` is a single-field re-read at 50 episodes per
agent, emitting only `{ep, leads, note}`.

```bash
python toolkit/merge_extract.py --dir extract/ --leads extract/leads/ --out ledger.json
```

The merger prefers a repair record over the extraction's own value and drops the
complaints the repair fixed. Write an equivalent focused prompt for any other field
that needs it: one judgment per episode, no plot summary, no evaluation.

---

## Phase 3 · Build the summary, then the ledger

### 3a · The summary of the whole script

```bash
python toolkit/build_summary.py --dir extract/ --out summary.md [--threshold 0.45]
```

Joins the 27 block summaries into one document, then matches every block's
`open_at_end` against the next block's `open_at_start` and reports three counts:

- **carried across** — threads that provably cross the seam
- **left hanging** — a block handed something on and the next block never claimed it
- **unclaimed** — a block treats something as already running that nobody handed on

Both of the last two mean either the show genuinely dropped a thread at that exact
point, or two agents used different words for the same thing. Check a few by hand.
If **nothing** carried across, the agents did not fill in the handoff lists and the
file is not trustworthy.

**Read `summary.md` before you cluster.** It is the only artifact that shows the
whole story at once, and it is what tells you which of the raw questions actually
matter.

### 3b · The ledger

```bash
python toolkit/merge_extract.py --dir extract/ --leads extract/leads/ \
       --out ledger.json --first 1 --last 665
```

Validates every record, discards anything an agent invented outside its declared
range, bounds the report to `--first/--last`, and derives what no single agent could
see: thread timelines, per-lead agency, episodes ending without a question, re-run
beats, and first-appearance normalised across the whole show. **Exits 1 on a missing
episode.** Re-run that batch rather than proceeding.

---

## Phase 4 · Mark the acts — a separate pass that must not see the hooks

Acts are found by their own agents, reading the same scripts, who are never given
the hook list, the hook prompt, or any hook output.

**This separation is the point.** When one process picks both the hooks and the acts,
the act boundaries land where the hooks turn, and the report then "discovers" that
hooks turn at act boundaries. That is not a finding; it is the boundary drawing
itself. Keep the passes apart and any agreement between them becomes real evidence,
while disagreement becomes a finding of its own.

### Two offset passes

```
  pass A   1-50, 51-100, 101-150, …          50 episodes each
  pass B   26-75, 76-125, 126-175, …         offset by 25
```

Every episode is read twice, by agents with different window edges. A turn one agent
sees alone is that reader's opinion; a turn two agents see independently is
structure. Each agent gets `references/arc-prompt.md` verbatim and answers one
question: **does the story turn inside this window, where, and why?**

Three kinds of turn count: **structural** (flashback, time skip, POV handover),
**situation** (location, cast, balance of power), **question** (what the stretch is
about). Most 50-episode windows contain zero, one or two.

### Consensus decides the count, not you

```bash
python toolkit/merge_arcs.py --dir arcs_raw/ --last 665 --out arcs.json
```

```
  a turn becomes a boundary when  >= 2 independent agents mark within +/- 4 episodes
                             and  their combined confidence >= 4
                             and  the resulting act is >= --min-act episodes
```

**The act count is a property of the show.** One show may give six acts, another
thirty. Do not reach for a round number. The only parameter you own is `--min-act`,
which exists to stop a single scene becoming an act.

Everything rejected is kept in the file, so you can see what was thrown out and why.
`--acts N` caps the count by demoting the weakest boundary repeatedly until N remain;
the demoted turns are recorded as `beats` rather than discarded. **Do not cap by
taking the strongest N**: on a show whose strong turns cluster early that leaves one
enormous act at the end.

Every act carries `boundary_evidence`: which agents agreed, their confidence, what
kind of turn, the spread of their marks, and why.

### Then write the acts, one agent each

```
  one agent per act, reading exactly that act's episodes
  contract: references/act-story-prompt.md
```

Each returns a **name** (two to four words, concrete), **three paragraphs of story**
between 700 and 1,100 characters, and **one line of judgment**. Story only in the
paragraphs; the single judgment line is the only place an opinion goes.

No agent writes about a stretch it has not read, and none of them see the hooks
either. An agent reading a whole act also sees things the 25-episode extraction
windows structurally cannot: repeated beats, a reveal that arrives as an aside, a
stretch that stacks five turns into fourteen episodes.

### Name the promise

One sentence, from `summary.md`: the fantasy, emotion or transformation the first few
minutes offer. See `references/taxonomy.md` §1. It goes in `arcs.json` and is passed
to every extraction agent as `{PROMISE}`, so cliffhanger alignment is scored against
it. **Change the promise and the extraction has to be re-run.**

---

## Phase 5 · Cluster into hooks

`ledger.json` holds several hundred raw questions. Most are the same handful of
hooks rephrased. This step is judgment, and it is the least protected step in the
pipeline, so do it with `summary.md` open.

### Clustering

Two raw questions belong to one hook if answering one answers the other. Merge
aggressively. Name each hook as a real question in a listener's voice, not a topic
label: `Who destroyed her body, and will they pay for it?` not `Revenge arc`.

### The pull rubric — score every candidate out of 12

**Score all the candidates before you choose any of them.** Selecting first and
scoring second produces a rubric that agrees with a decision it never made. The first
run of this skill did exactly that: every hook scored 3 on stakes, because anything
important enough to be picked was, by definition, high stakes. The axis measured
nothing.

These four axes are chosen because a real hook **can score 0 on each of them**.

| Axis | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| **Recurrence** | mentioned once, never again | occasional, long silences | re-touched in most stretches | drives the cliffhanger repeatedly |
| **Specificity** | vague someday ("will she find happiness") | a named goal | a named goal with an obstacle | named, dated and witnessed ("the trial, in three days, before the court") |
| **Ownership** | a character the listener has no stake in | a secondary character | a lead, but about someone else's business | the lead's own fate |
| **Consequence** | answering changes nothing | a scene or a relationship shifts | the direction of the story changes | the show becomes a different show |

**Dropped: stakes and centrality.** Neither could fail. Any question that survives
clustering has high stakes and sits near the centre, so both scored 3 on everything
and added nothing. Ownership and consequence measure what those two were reaching
for, in a way that can come back low.

**Ownership is the axis that earns its place.** A beautifully built arc belonging to
characters the listener met halfway through the show scores 1 here, and should. It is
the only axis that separates *this is well made* from *this is what the audience came
for*.

### How many hooks

**Between 10 and 12.** Fewer than 10 and a long show's shape is lost; more than 12 and
the report stops being readable. Rank every candidate by pull and take the top 10 to
12, breaking at a natural gap in the scores if there is one.

Record how many candidates you scored, and say on the page what the cut-off was. A
show where the 13th candidate scored the same as the 10th is a show with more spines
than the report shows, and the reader deserves to know that.

**Span is a column, never a score.** How long a question stays open is context. A
280-episode span with high recurrence is a spine. The same span with low recurrence
is a **dangling thread**, and the row must say so.

### Write `analysis.json`

```json
{"hooks": [
  {"code": "H1",
   "q": "What is Kel really, and why is he warm?",
   "opens": 2, "resolves": 97, "ended": "onscreen",
   "members": ["every phrasing of this question found in ledger.json"]}
]}
```

`members` is what the counting depends on. A hook the show discusses constantly in
wording you did not list will look dead. Harvest phrasings from `threads_raw` rather
than typing them from memory.

`ended`: `onscreen` · `offscreen` · `deflected` · `dropped` · `null` for never.

---

## Phase 6 · Count what the show did with each hook

```bash
python toolkit/hook_health.py --ledger ledger.json --analysis analysis.json --out health.json
```

Four counted measures per hook, no judgment:

| Measure | Question it answers |
|---|---|
| **Touch rate** | how often the show remembers it |
| **Longest silence** | the biggest run of episodes nobody mentions it |
| **Moved vs restated** | did the episode push it, or circle it |
| **How it ended** | on screen, off screen, dodged, or never |

Those give a verdict: **WORKING**, **STALLING**, **GONE QUIET**, or **BROKEN**.

> **`moved vs restated` is the weakest of the four.** It uses the per-episode `beat`
> field as a proxy, because agents rate almost every question force 2-3 and that
> field cannot separate advancing from mentioning. Treat a low score as worth a look,
> not as proof.

**The tool exits 1 when it cannot see a hook properly** (under 6 phrasings or under
5 matched episodes) and says so in plain words. A hook that fails this check is
**unknown, not quiet**. Add phrasings and run it again. Never publish a verdict the
tool refused to stand behind.

---

## Phase 7 · Judge coverage, not lateness

**A hook opening at episode 155 is not late.** It is only a problem if nothing else
was live at 155. What matters is whether the listener, at any given episode, has
something to wonder about.

`build_audit.py` computes this with `live_counts()`. A hook counts as live at an
episode only if it is open **and** the show raised it within the last
`LIVE_WINDOW` (10) episodes. A question nobody has mentioned in fifty episodes is
still unanswered, but it is not holding anyone.

The output is a density chart plus a table of **dead runs**: stretches of four or
more consecutive episodes where nothing at all was live. Those runs are the finding.
A gap between two bars on the timeline is not.

**For a long hook, report continuity neutrally.** A 500-episode question will have
quiet patches. Say where the quietest one is and how long, then leave it, unless the
coverage chart shows other questions were also quiet there. `continuity_note()`
writes this sentence and deliberately does not grade it.

---

## Phase 8 · What each act does with each hook

```bash
python toolkit/arc_transit.py --arcs arcs.json --health health.json --out transit.json
```

Every hook alive when an arc ends does exactly one of five things:

| | |
|---|---|
| **carried** | alive going in, alive coming out |
| **closed** | the arc answers it on its way out |
| **dropped** | alive going in, never meaningfully touched again |
| **opened** | the new arc plants it |
| **revived** | quiet a long time, and the new arc picks it back up |

That gives a reading per boundary: *"this arc ends with 4 hooks alive; it carries 2,
closes 1, drops 1, and opens 3."* **An arc that drops more than it carries is where a
listener has least reason to continue.**

Hooks are what carry attention across an arc change. A show that closes an arc
cleanly but hands nothing forward has to win its audience again from scratch.

---

## Phase 9 · Resolutions, breakage, drift

### Broken promises — the six kinds

| Code | Break | Test |
|---|---|---|
| **B1 · Retcon** | stated, then contradicted as if never said | quote the stating line and the contradicting line |
| **B2 · Offscreen close** | answered in a gap, reported after the fact | the answering scene does not exist |
| **B3 · Deflation** | stakes quietly lowered before the payoff | compare stakes at open with stakes one episode before close |
| **B4 · Substitution** | a different question answered in its place | the original question, asked plainly, is still open |
| **B5 · Drop** | never answered, never acknowledged | search the whole run to be sure |
| **B6 · Deferred past use** | answered so late it no longer pays | latency above ~80 episodes |

Every break needs **a quoted line at the promise and a quoted line at the break**,
each with an episode number. A break you cannot quote twice is a suspicion, not a
finding.

### Narrative drift — the six signals

Drift is always an episode **range**, never one episode.

| Code | Signal | How to detect it from the script |
|---|---|---|
| **D1** | **Nothing live** | from `live_counts()`: a run of episodes where no question is being raised |
| **D2** | **Lead stops driving** | `leads` shows passive or absent across a run. **Check the finale**: a lead who returns and owns the ending was paused, not replaced |
| **D3** | **Cast bloat, untrackable names** | `first_appearance` well above the show's own rate; or names a listener cannot tell apart. Audio has no spelling |
| **D4** | **Repetition** | `beat: "re-runs"` clustering with the lead's position unchanged |
| **D5** | **Pacing** | episodes ending with `posed_as_question: false`; a single conversation spread over several episodes |
| **D6** | **Other** | any other creative reason a listener drifts. **Name the mechanism.** Never use D6 to avoid defining something |

Severity: **mild** (a listener notices), **marked** (skips), **severe** (leaves).
Always labelled as inferred.

**The trap.** A stretch handed to a second couple is not automatically drift. In one
show the leads appeared in ~39% of a 160-episode stretch and it held, because they
returned and owned the finale. In another the same move was fatal. The distinction
is **pause versus replace**, and only the finale settles it.

---

## Phase 10 · Build the page

```bash
python toolkit/build_audit.py --ledger ledger.json --title "Show Name" \
       --out audit.html --health health.json
```

Fill `LOGLINE`, `LEAD`, `CHECKED`, `HOOKS`, `BREAKS`, `DRIFT`, `LEDGER` at the top
of the script. Everything countable is computed from `health.json`, never typed.

### Page structure

```
  The promise, in one line          the strongest question and its fate
  Checked, not assumed              what was read, what was inferred

  PART I    The questions that hold the show up
              ranked table, hover a pull score or a verdict for why
              timeline, with act boundaries and numbered trouble bands
              the band key: every band named, each row a link to its detail

  PART II   The story, act by act                    ← the spine of the report
              per act: what happens in the story, then what the analysis found
              questions the act planted / answered / kept working / ignored
              promises it breaks · trouble that overlaps it
              across the whole show: how many questions were live at once

  PART III  Resolutions and broken promises
              each break quoted twice, with a link back to its act

  PART IV   Where the show loses people
              each trouble spot: the story first, then the evidence

  The cliffhanger ledger            30-50 load-bearing episodes
  Supplementary data                per-episode strips, worst-first table
```

**Part II is the report.** Everything else is a different view of what is in it. A
reader who only reads the acts should still get the whole diagnosis.

### The act renderer is four things, and they are separable

`act_blocks` used to do four jobs at once: render the act, join and render the hooks
inside it, join and render the promises it breaks, join and render the trouble zones
overlapping it. Everything came out fused into one HTML string, so any other document
wanting the same facts in a different shape had to either edit this renderer or cut up
its output.

It is now split:

```python
act_shell(arc, i, stories)          # the act: number, name, episodes, summary
hooks_in(arc, hooks, health, last)  # DATA: the four hook states for this act
breaks_in(arc, breaks)              # DATA: promises that break inside it
drift_in(arc, drift)                # DATA: zones overlapping it, and by how much
```

Three pure joins on episode range, each returning **data, not markup**. `act_blocks`
composes them back into exactly what this report renders, and `act_extras` is a
renderer over the joins rather than a filter-and-render in one step.

**Keep it that way.** An act is one thing; the hooks, promises and trouble zones inside
it are three others. The `audit-validation` skill renders the same joins in a different
shape, and it can only do that because the joins return data.

**The test is a byte-identical rebuild.** After touching any of these, rebuild the audit
and diff it against the previous file. If it differs, the refactor changed the report
and something is wrong.

### Every act block

```
  ACT n · Name · Episodes a–b
  WHAT HAPPENS IN THE STORY
    900-1,200 characters, story only, no evaluation
  [one line of judgment, and only here]
  ═══════════════════════════════════════════════
  WHAT THE ANALYSIS FOUND HERE      n working · n hanging · n broken
  THE QUESTIONS          cards: status tag, the question, a bar, the journey
  PROMISES BROKEN HERE   cards
  TROUBLE HERE           cards
```

Cards flow in a responsive grid. **Do not put the findings in a side panel**: an act
with three paragraphs of story and eleven findings leaves half a two-column row
empty, and it gets worse the more the act contains.

### Rules the renderer enforces, learned the hard way

| Rule | Why |
|---|---|
| A bar that looks like a proportion **is** one | A bar was multiplied by 6 and clamped, so 21 of 96 episodes drew full |
| Hover readouts are visible elements, not `<title>` | Native tooltips need a slow hover on a 1px target |
| Scope hover CSS to the hit rect | `.ephit rect{}` wiped the readout's own background |
| Number things once, up front | Trouble spots were numbered by whichever renderer ran first |
| Number by reading order, not draw order | The band key read 5, 1, 4, 2, 6, 3 because numbering came from paint order |
| Codes mean something | H-numbers now follow the episode a question is asked, so H1 is the first |
| One rank per row | A rank column and a hook code on the same row fight each other |
| Every jump target highlights on arrival | `:target` plus a back link, or the reader lands in a list of five and cannot tell which |
| Every dead run must be covered by a declared trouble zone | Two metrics disagreed for weeks and the page showed both |

### The hook block, and the part that breaks

Left column tells the question straight. Right panel carries the verdict. **Never
put verdict language in the left column.**

```html
<section class="act">
  <div class="act-head">
    <span class="act-num">H1</span><h3>Who destroyed her body?</h3>
    <span class="act-eps">Opens ep 3 · answered ep 287</span>
  </div>
  <div class="act-body">
    <div class="story"><div class="col-h">What the script asks</div><p>…</p></div>
    <aside class="aud cliff">
      <div class="aud-h">The verdict</div>
      <div class="aud-status">Answered late · open for 284 episodes</div>
      <p class="aud-ret">…</p>
      <div class="cmts"><div class="cmts-h">In the script</div>
        <blockquote>…<cite>— ep 3</cite></blockquote></div>
    </aside>
  </div>
</section>
```

**The `<aside>` must sit INSIDE `.act-body`.** Put it after the closing `</div>` and
the two-column grid silently collapses into one unreadable stream while the markup
still looks fine. Verify in a browser:
`getComputedStyle(document.querySelector('.act-body')).gridTemplateColumns` returns
two values, e.g. `512px 300px`.

**Check at a viewport wider than 900px.** `house.css` collapses to one column at
`max-width:820px` by design. A narrow window reports a defect that is not there.

`aud hold` for a kept promise, `aud cliff` for a broken or dangling one.

### House style

`assets/house.css` verbatim. Cream editorial, Georgia headings. **Static HTML only,
no JavaScript.** Charts are hand-built inline SVG.

Classes: `wrap` `eyebrow` `sub` `meta` `rule` `part` `sec` `secn` `logline` `lead`
`note` `readnote` `two` `card` `castrow` `act` `act-head` `act-num` `act-eps`
`act-body` `story` `col-h` `aud` `aud-h` `aud-status` `aud-ret` `cmts` `cmts-h`
`diag` `pattern` `big` `bt` `c` `tk` `ad` `stw` `state` `bl`. Rows: `tr.flag` red,
`tr.near` amber. Badges: `stw hold` / `stw near` / `stw flag`. **Add no new CSS.**

### Validate every build

```python
from html.parser import HTMLParser; HTMLParser().feed(html)
import re; assert not re.findall(r'&(?!amp;|lt;|gt;|quot;|#\d+;|nbsp;|#x[0-9a-fA-F]+;)', html)
```

The unescaped `&` is the recurring defect, arriving through titles and character
pairs ("Crushed & Crowned", "Zeke & Alicia").

---

## Phase 11 · Export the claims, so the audit can be tested

```bash
python toolkit/export_claims.py --build build.py --transit transit.json \
       --out claims.json
```

The audit's findings live as authored constants inside the renderer: `HOOKS`,
`BREAKS`, `DRIFT`, `CAST`, `ACT_STORIES`. That is fine for producing this report and
useless to anything else. `export_claims.py` lifts them into `claims.json` as data:
the promise, the ten questions with their pull axes and verdicts, every break with the
episode it was promised and the episode it broke, every trouble zone with its range and
severity, the acts with their boundaries, and the cast.

`claims.json` is the contract between this skill and `audit-validation`. Without it the
validation pass has nothing to test, and anyone wanting to check these findings has to
parse a Python file.

**Export after the report is final, not before.** The file must agree with what the
page says, and the numbering of breaks and trouble zones must match the numbering the
page renders, or a verdict lands under the wrong heading in the second document.

`toolkit/arc_view.py` renders the four-layer arc grid that Part IV used to carry. That
part is switched off in the renderer (`SHOW_PART_IV = False`) because everything it
showed now appears inside the acts, where it has context. The script is kept for shows
where the grid is worth having.

---

## Before you ship

- [ ] Gap report read; episode count and range stated on the page?
- [ ] Zero episodes missing from `ledger.json`?
- [ ] `summary.md` read before clustering, and its seam counts sane?
- [ ] No two of the top hooks are the same question rephrased?
- [ ] Each hook named as a question a listener would ask, not a topic label?
- [ ] Opening and answering episodes **read**, not inferred?
- [ ] `hook_health.py` exited 0 — no hook published that the tool refused to score?
- [ ] Lateness never treated as a fault on its own; dead runs used instead?
- [ ] Long hooks given a neutral continuity sentence, not a verdict?
- [ ] Every break quoted twice with episode numbers?
- [ ] Low-recurrence long threads labelled **dangling**, not counted as pull?
- [ ] D2 checked against the finale: pause or replace?
- [ ] Nothing filed under D6 without a named mechanism?
- [ ] **Would a reader who has never heard of this show understand every sentence?**
- [ ] Two-column grid verified in a browser at >900px?
- [ ] Verdict language kept out of the left column?
- [ ] HTML parses; zero unescaped `&`?
- [ ] Promise written as fantasy/emotion/transformation, not as plot?
- [ ] Arcs tile the whole run with no gaps?
- [ ] Cliffhanger strength and alignment scored **independently** — is there at least
      one high-push, off-promise episode, or did the scorer collapse the two axes?
- [ ] Page states plainly that no retention data was used?

## Known gaps in this skill

Written down because they are easy to forget once a report looks finished.

1. ~~Arc boundaries are ungrounded.~~ **Closed.** Boundaries now come from two
   offset passes of agents who never see the hooks, and survive only on two-agent
   consensus. Every boundary carries its evidence. The act count is whatever the
   show gives. The one parameter left is `--min-act`.
2. **Hook selection has no coverage check.** Nothing reports what fraction of the
   raw questions the chosen hooks account for. If ten hooks explain 40% of what the
   agents logged, the list is wrong and the report will not say so.
3. **Analysis lives inside the renderer.** `HOOKS`, `BREAKS`, `DRIFT`, `LEDGER` and
   `ACT_STORIES` are Python constants in `build_audit.py`. That means the analysis
   cannot be diffed, cannot be validated against a schema, and a typo breaks a
   script rather than failing a check. Moving them to `analysis.json` is the single
   highest-value refactor left.
4. **Metrics can drift apart.** Trouble zones are authored from one signal and dead
   runs computed from another. They disagreed for a long time and the page showed
   both. Reconcile them every run: every dead run must fall inside a declared zone.
5. **The act stories are the one place an agent's opinion reaches the page
   unchecked.** Each act's judgment line is written by a single agent with no second
   reader. The stories themselves are verifiable — every proper noun should appear in
   that act's own scripts, which is worth checking — but the judgment line is not.
6. **No calibration batch.** Field ambiguity is still found mid-run by luck. Two
   agents reading the same 25 episodes, compared, would catch it for the price of
   one extra agent.

## Limits to state in the output

- The script is **evidence**; listener attention is **inferred**. This report reads
  what the script asks and whether it answers. It does not measure engagement.
- Pull scores are a rubric applied by judgment. Show the axis breakdown so a reader
  can disagree with a number rather than with the conclusion.
- **The counted measures depend on wording.** A hook is found by matching phrasings.
  Say so on the page, and never present a hook the health tool refused to score.
- Drift severity is the softest claim on the page. Label it.

**If unsure, prefer the smaller checkable claim.** The worst output is a confident,
fluent, wrong one.

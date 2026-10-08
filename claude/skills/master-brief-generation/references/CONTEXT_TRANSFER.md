# CONTEXT TRANSFER — Producing Cliff Reports, Donor Briefs and Donor Shortlist Reviews

**Read this in full before doing anything. You have no prior context and this document assumes none.**

You are working for Pocket FM, a serialized-audio platform. Shows run 300–700
episodes of roughly 9–10 minutes each. This document tells you how to produce
three related deliverables, in the exact house format, and — more importantly —
how to avoid the specific mistakes that have already been made and corrected on
this project.

---

## 0 · THE THREE DELIVERABLES AND HOW THEY RELATE

| # | Artifact | Question it answers | Format |
|---|---|---|---|
| 1 | **Cliff report / master brief** | Where and why did this show lose its audience? | HTML |
| 2 | **Donor search brief** | Spec for an external crawler to find a "donor" show whose engine we can graft on | Markdown |
| 3 | **Donor shortlist review** | Is the crawler's candidate list any good? | HTML |

They run in that order. A **stitch** = cut a declining show at a chosen episode
and continue with the *engine* of a different, better-retaining show ("the
donor"), reskinned into this world and cast.

---

## 1 · THE ONE RULE THAT MATTERS MOST

> **Go to the raw data. Form your own diagnosis. Never inherit a prior read.**

Every serious error on this project came from trusting a summary, a creative
brief, or an earlier analysis instead of re-reading the episode summaries and
the comments. One master brief named the wrong villain and shipped, because the
character was assumed rather than traced through the summaries. Another called a
show a "vampire romance" when the word "vampire" does not appear until episode
137.

If you find yourself writing a causal claim, ask: **did I read the episodes that
prove it, or did I infer it?** If inferred, go and check.

---

## 2 · THE DATA PACK

A pack arrives as a zip. Typical layout:

```
NOTES.md                                  (may be empty — do not rely on it)
show_id.txt
data/episodic/Episodic_Level_<Show>_and_TAB.csv
data/episodic-summaries/<slug>/EPISODIC_SUMMARIES_001-NNN.md
data/inapp-comments/<slug>/*.csv
data/sheet/ , data/whale/ , data/reports/   (usually not needed)
```

### 2.1 The episodic CSV

Contains **two shows**: the subject show and the benchmark, **The Alpha's Bride
(TAB)**, `show_id = cbc35fa13bbe154873ec97f78f2b4cf4b66c7d31`.

Columns you need (there are ~30; ignore the rest):

| Column | Meaning |
|---|---|
| `show_id` | which show the row belongs to |
| `Story no.` | episode number |
| `Duration cum. (HR)` | cumulative hours into the show at this episode |
| `LDAU (Modified)` | listeners still active — the **level** |
| `Drop % (Modified)` | per-episode drop — the **rate** (multiply by 100) |

### 2.2 Episode summaries

Two formats exist. **Try both**, do not assume:

```python
patterns = [r'\*\*Episode (\d+) — (.+?)\*\*\n(.*?)(?=\n\*\*Episode |\Z)',
            r'### Episode (\d+) — (.+?)\n(.*?)(?=\n### Episode |\Z)']
```

If your parse returns 0 episodes, you used the wrong pattern — check the file
head before proceeding.

### 2.3 Comments

Column layouts vary **between files in the same pack**. Handle all of these:

- an `episode_number` column, or an `Ep N - …` prefix inside `story_title`
- the text column may be `comment` **or** `comment_text`

Merge every CSV in the comments folder; bucket by episode number.

---

## 3 · THE CORE METRIC

**Block drop-rate ratio** = the show's mean drop-% in a block ÷ TAB's mean
drop-% at the **same cumulative hour**.

```python
tab_at = lambda H: min(TAB, key=lambda e: abs(hr(TAB, e) - H))
ratio  = mean(dr(SHOW, e) for e in block) / mean(dr(TAB, tab_at(hr(SHOW, e))) for e in block)
```

**Match on hours, not episode numbers.** Episode lengths differ between shows.

Blocks of 10 episodes for shows under ~450 episodes, 20 for longer.

| Ratio | Meaning |
|---|---|
| ≤1.0 | holding at or better than the hit's pace |
| 1.3–1.6 | mild |
| **≥1.6** | genuine flag |
| ≥2.5 | severe |

**LEVEL vs RATE — do not confuse them.** *Level* is the % of the ep-51 audience
still listening. *Rate* is how fast they are leaving right now. A late block can
show a huge ratio simply because TAB is flat by then. Always report both.

Baseline the level at **episode 51** (before that, curves are dominated by
sampling noise).

Also compute a survival headline: of 100 listeners at hour X, how many reach
hour Y, for the show and for TAB. Pick a window **inside clean data** (see §4).

---

## 4 · THE FOUR TRAPS — these have all actually happened

### Trap 1 · Corrupt LDAU rows

Retention level can only fall. Any episode whose `LDAU (Modified)` exceeds the
previous by **>12%** is a data defect.

*Real cases:* **The Vampire Prince ep 270** = 15,019 against neighbours of
~7,500. **The Wolfless Deviant ep 183** = 9,311 against ~4,660. Both exact
double-counts. Uncorrected, VP appeared to *gain* 6,900 listeners.

**Fix:** interpolate that episode out of the level curve. The `Drop %` column is
usually unaffected, so your ratios are fine — but check.

### Trap 2 · Paywall / free-window boundaries

Many shows run a free daily-unlock window that ends before the finale.
When it closes, the curve falls off a cliff. **This is not a story failure.**

*Real cases:* **WD ep 241–250 = 33×** (level 38% → 10% in ten episodes).
**VP ep 551–570 = 6.75×**, with listeners explicitly saying free episodes had
stopped and the last hundred chapters had to be bought (665 − 100 = 565 ✓).

**Detection:** a single block an order of magnitude beyond anything else in the
show, plus production/paywall complaints spiking above that show's baseline
(VP: 13% vs a 2–5% baseline). Note that a paywall block may show a *low*
complaint rate — people who hit a wall leave silently. Magnitude is the stronger
signal.

**Never let a paywall block drive the diagnosis or the cut point.**

### Trap 3 · Delivery faults that self-heal

*Real case:* **The Last Howl 321–340** ran 2.9× and 3.6×, with comments
reporting episodes arriving out of order and repeating. By 351 it was back to
**1.08×**. Story breaks do not recover; delivery faults do.

**Rule:** a spike that reverts within ~2 blocks is an **edit/ops fix**, not a
reason to stitch.

### Trap 4 · Release dumps

*Real case:* **Crushed and Crowned's** finale zone showed 5–15×. A comment at ep
504 explains it: ~30 episodes dumped after six months of no free episodes.

---

**Standing rule:** before you attribute any large block to story, check it
against all four traps. In four of the five shows analysed so far, **the single
largest number on the chart was not a story problem.**

---

## 5 · DELIVERABLE 1 — THE CLIFF REPORT / MASTER BRIEF (HTML)

### 5.1 Structure — follow exactly

1. Eyebrow line, `<h1>` show name, subtitle, meta line (episode count, data sources)
2. **Logline** — one paragraph, the premise as if to a first-time reader
3. **Who's who** — 5–6 `castrow` entries
4. **The problem, in one line** — a `lead` block with the headline finding and the survival number, plus a `note` box titled **"Checked, not assumed"** listing any data corrections made
5. **Part I · The story, in full** — a `readnote` explaining the layout, then 8–9 acts
6. **Part II · Why it breaks** — the charts, then the mechanism
7. **Part III · What to do** — "The stitch": two cut-option cards + a "three rules for the continuation" note

### 5.2 The act layout — the part most often got wrong

Each act is a **two-column grid**: story left, audience panel right.

```html
<section class="act">
  <div class="act-head">
    <span class="act-num">Act 1</span><h3>Title</h3>
    <span class="act-eps">Episodes 1–30</span>
  </div>
  <div class="act-body">
    <div class="story">
      <div class="col-h">What happens in the story</div>
      <p>…</p><p>…</p>
    </div>
    <aside class="aud cliff">
      <div class="aud-h">The audience here</div>
      <div class="aud-status">…</div>
      <p class="aud-ret">…</p>
      <div class="cmts"><div class="cmts-h">In their words</div>
        <blockquote>…<cite>— ep 171</cite></blockquote></div>
    </aside>
  </div>
</section>
```

**The `<aside>` must be INSIDE `.act-body`.** In the original briefs it was
placed after the closing `</div>`, so the two-column grid never formed and the
story and analysis ran together in one unreadable stream. Verify with a browser:
`getComputedStyle(document.querySelector('.act-body')).gridTemplateColumns`
should return two values, e.g. `512px 300px`.

### 5.3 Story and commentary must not mix

The left column is **story only** — what happens, told straight, present tense,
no evaluation. Sentences like *"this is the show working"*, *"a genuinely strong
twist"*, *"the audience does not read this as strength"* belong in the **panel**,
not the story. Act headers carry only the act name and episode range — no
diagnostic tag.

Aim for **~900–1,200 characters per act body** (3–4 real paragraphs). Two thin
sentences per act is the most common quality failure.

### 5.4 Charts

Two stacked SVG charts in one `<figure>`:

- **Top:** level curve — show vs TAB, both normalised to their own ep-51 = 100%.
- **Bottom:** per-block ratio bars, with a dashed green line at 1.0× ("benchmark pace").

Colour bars by severity (green <1.3, amber 1.3–1.6, red ≥1.6) and use a
**distinct colour (brown) plus a label** for any paywall/artifact zone, so the
chart does not contradict the text. Mark boundary episodes with dashed vertical
lines. Stagger label anchors so they do not collide, and give the viewBox enough
height that axis labels are not clipped.

### 5.5 The evidence table

A section titled **"Every flagged block — the evidence table"** between the
charts and the mechanism, with columns: *Episodes · vs benchmark · What is
happening in the story · Type*. The **Type** column is the point — it separates
`creative` from `monetization` from `post-paywall · not comparable`. Highlight
flagged rows.

### 5.6 Validation — run every time

```python
from html.parser import HTMLParser; HTMLParser().feed(html)          # must not raise
import re; assert not re.findall(r'&(?!amp;|lt;|gt;|quot;|#\d+;|nbsp;|#x[0-9a-fA-F]+;)', html)
```

The unescaped `&` is a recurring defect — it comes from show titles like
"Crushed & Crowned" and character pairs like "Zeke & Alicia". Escape to `&amp;`.

---

## 6 · DELIVERABLE 2 — THE DONOR SEARCH BRIEF (Markdown)

Written for an **external crawler with zero context**. It must be entirely
self-contained: no reference to the platform, the benchmark, or any other
document.

### Fixed section structure — §0 to §13

```
0.  What this task is, in one paragraph
1.  Glossary (every term used below)
2.  The show you are continuing — full plot summary
3.  The characters (who a donor must map onto)
4.  The world / setting
5.  Why we are stitching, and the evidence   ← block-ratio table
6.  WHERE TO CUT — the entry point, with justification
7.  What the donor must supply + the trap unique to this show
8.  THE SCREEN — auto-reject gates, numbered S1…S6
9.  Engine classes + the 7-axis rubric + worked examples
10. Where to search + search vocabulary (and anti-vocabulary)
11. How to run it — two passes
12. What to deliver — exact output schema per candidate
13. Honest caveats
```

### The rubric

Seven axes, each scored **0 / 1 / 2**, total out of 14. Some axes are **gates**:
a 0 there caps the candidate at REJECT regardless of total. **The axes and the
gates are show-specific** — they encode how *that* show failed. Examples:

- A show that died of a couple-swap makes "stays the leads' story" a gate.
- A show whose heroine already won adds an axis for "fits a heroine who has already won".

Bands: **12–14 COMMISSION · 9–11 STRONG · 6–8 CONDITIONAL · gate-0 or ≤5 REJECT.**
(One brief uses 13–14 / 11–12 / 8–10; keep whichever the sibling briefs use and
say which.)

### Screen items

Number them **S1–S6** so reviews can cite codes. They are the *specific* moves
that killed this show — importing another show built on them repeats the
failure.

---

## 7 · DELIVERABLE 3 — THE DONOR SHORTLIST REVIEW (HTML)

Reviews a crawler's output. Sections, in order:

1. **Logline** — read this first: is the file trustworthy, and what is the headline?
2. **The finding that matters most** — the single most decision-relevant thing
3. **The top picks stress-tested** — 3 `deck` cards: what you buy / what you owe
4. **What the crawl got right** — credit, honestly
5. **Things to fix or watch**
6. **How to read this page (start here)** — the taxonomy legend (below)
7. **The ranked field** — the full audited table
8. **Send to a verification round** — 4 `qbox` items
9. **Collisions** — titles booked across multiple jobs
10. **Crawl status** — blockers, stale lanes

### The taxonomy legend — mandatory

Without it the table is unreadable. It must contain: the **seven dimensions in
plain English** with a Gate? column and what a 2 vs a 0 means; a note on which
axes are gates *for this show*; the **grade key**; **two worked examples**
(one clean pass, one gate-fail); and a **shorthand paragraph** explaining the
S-codes, the collision notation and Tier A/B.

Write scores as `2/2/1/2/1/2/2` (slashes, not middots) and mark 0s in red.

### Standing review checks

- Is the ranked #1 actually *available*? (Blocked lanes, unverified hours, and
  titles already committed to another show are common.)
- Do several candidates score identically? Then it is a tie, not a ranking —
  re-rank by availability.
- Does a single blended "fit /100" hide a problem a per-axis score would expose?
  (In one crawl a "Fit 94" concealed a 165-hour title against a 75-episode runway.)
- **Collisions:** the same strong donors win top seats on several shows and each
  licence can be spent once.

---

## 8 · HOUSE STYLE

Use the supplied `house.css` verbatim. Cream editorial aesthetic, Georgia
headings. Static HTML only — **no JavaScript, no interactive charts**. Charts are
hand-built inline SVG.

Key classes: `wrap` `eyebrow` `sub` `meta` `rule` `logline` `sec` `secn` `lead`
`note` `two` `card` `part` `castrow` `act` `act-head` `act-num` `act-eps`
`act-body` `story` `col-h` `aud` `aud-h` `aud-status` `aud-ret` `cmts` `figure`.

Generate HTML from a **Python script**, not by hand — you will need to
regenerate several times, and the numbers must come from the data, not be typed.

---

## 9 · THE FIVE SHOWS ALREADY ANALYSED — verified findings

Use these as calibration and as worked examples. All were checked against raw
summaries and comments.

| Show | Eps | Verified diagnosis |
|---|---|---|
| **The Last Howl** | 465 | Best holder; converges to TAB parity. **321–340 = delivery bug that self-heals to 1.08×.** Real exodus **391–420 (2.1×, 3.4×, 2.5×)** when a prodigy infant takes over the story. |
| **Seduced by Darkness** | 395 | Royal forced-marriage romance (**vampire revealed only at ep 137**). Out-performs TAB (0.31×) for the whole first half. Peak at the ring, **ep 209–210**. Breaks **221–230 at 4.6×**: the heroine becomes a **spectator** in Sebastian's backstory and a prior love, **Alyssa**, is installed retroactively. Ends in a **couple-swap** — the final 12 episodes belong to Zeke and Alicia; the leads are absent. |
| **Crushed and Crowned** | 572 | Reverse-harem; holds clean to **ep 160**, including a good spellcraft twist. Breaks **161–180 (3.9×)**: Olivia severs the bond as revenge on mates just proved innocent, a love-polygon opens, she relocates. **The forgery was by the triplets' parents and the spell by Anita's father — NOT by Damien**, who is the triplets' uncle and the one who rescues her from traffickers. Reckoning arrives ~ep 243, ~80 episodes late. Finale zone = release dump. |
| **The Wolfless Deviant** | 427 | Strongest hook, leakiest show — **never reaches TAB parity**. Worst genuine bleed **151–170 (2.2–2.5×)** where **both leads marry other people**. **Ep 241–250 = 33× = the free window closing, not story.** |
| **The Vampire Prince** | 665 | Strongest holder in the set (**0.21×**). Breaks **291–310 (2.11×)** on **trackability** — a 30-episode flashback plus a hero split into **Gavriel / Gavrael**, one letter apart, indistinguishable in audio. **551–570 = 6.75% = paywall at ~ep 565.** |

### The most important calibration case

**The Vampire Prince, ep 331–490.** The show hands most of its screen time to a
*second couple* — the leads appear in only ~39% of those episodes — and
retention **holds** (0.88–1.31×). In Seduced by Darkness the same move was
fatal. The difference is **pause vs replace**: in VP the leads return and own the
finale. Do not flag a secondary-couple stretch as a failure without checking
whether the leads come back.

---

## 10 · THE FAILURE MODES OBSERVED SO FAR

Derived from those five shows only. **All five are romance-driven supernatural
serials — this is a strong prior for Romantasy and untested elsewhere.**

| Mode | Measured cost |
|---|---|
| Lead stops driving | 2.1–3.9× |
| Lead becomes a spectator in someone else's backstory | **4.6×** |
| Protagonist identity untrackable (names, timelines) | 2.11× |
| Permanent handoff to another couple | terminal |
| Central relationship stalled by a rival marriage | 2.2–2.5× |
| Central question resolves with nothing to replace it | the vacuum that follows |

---

## 11 · WORKING METHOD — the sequence that works

1. Unzip; read `NOTES.md` and confirm the show_id.
2. Parse the episodic CSV; **check LDAU monotonicity** (Trap 1).
3. Compute the block table **before reading any story**. Let the numbers tell you where to look.
4. Pull comments for every flagged window; compute the production/paywall complaint rate against the show's own baseline.
5. **Classify each flagged block** — creative / monetization / delivery / post-paywall.
6. Only now read the episode summaries: the hook, each flagged window, and the finale.
7. Verify every causal claim (who did what to whom) by tracing it through the summaries. Search for the character name across all episodes rather than trusting one summary line.
8. Write the generator script; build; validate; **render in a browser and look at it**.
9. Re-read your own story column: have you smuggled commentary into it?

### Before you ship, check

- [ ] LDAU anomalies found and interpolated?
- [ ] Every large block classified against the four traps?
- [ ] Two-column grid verified in a browser (not just in the markup)?
- [ ] Story column free of evaluation?
- [ ] Act bodies ~900+ characters?
- [ ] Charts consistent with the text (artifact zones distinctly coloured and labelled)?
- [ ] HTML parses; zero unescaped `&`?
- [ ] Every causal claim traced to specific episodes?
- [ ] Survival headline computed from a clean (non-paywall) window?

---

## 14 · THE TOOLKIT — runnable code, use it

`toolkit/` contains working scripts. **Use them rather than rewriting the
parsing and the metric from scratch** — the traps in §4 are already implemented,
and they were validated against the hand-verified diagnoses.

### Step 1 — the numeric pass (before reading any story)

```bash
python toolkit/analyse.py --pack ./unzipped_pack
```

It parses the episodic CSV, both summary formats and every comments layout;
detects corrupt LDAU rows; builds the block table; **classifies every block** as
`holds` / `mild` / `CREATIVE · genuine flag` / `ARTIFACT · …`; prints comment
quotes for each flagged window; writes `analysis.json`.

Validated against the real packs: it catches **WD ep 183** and **VP ep 270**
(corrupt LDAU), flags **WD 241–250 at 32.7×** and **VP 551–570 at 6.75×** as
artifacts, and correctly keeps **VP 291–310 at 2.11×** as a genuine creative
flag while noting the narrator complaints.

> Two heuristics deliberately require corroboration, because the first version
> got these wrong: a self-healing spike is only called a delivery fault if
> **delivery complaints are also elevated** (a real break can be followed by
> recovery too), and paywall/delivery calls need at least **5 matching comments**,
> not just a high rate on a thin sample.

### Step 2 — the report

```bash
python toolkit/build_report.py --pack ./unzipped_pack --title "Show Name" --out report.html
```

A working skeleton: it draws both charts from the real numbers, builds the
evidence table, and lays out the two-column acts **correctly**. Fill in
`LOGLINE`, `LEAD`, `CAST`, `ACTS` and the stitch text at the top of the file
after reading the summaries. It validates the HTML and counts unescaped `&` on
every run.

**The scripts do the arithmetic. You do the reading.** The classifier tells you
*where* to look and which windows are artifacts; it cannot tell you *why* a
creative flag happened. That still requires reading the episodes and tracing
every causal claim.

---

## 12 · HONEST LIMITS TO STATE IN ANY OUTPUT

- Retention is measured; **story causation is inferred.** Say which is which.
- A stitch fixes structure. It does not fix appeal, casting or promo.
- The block ratio is a comparison against one benchmark show. It is a good
  yardstick, not a law of nature.
- If a claim rests on an unread stretch, say so rather than smoothing over it.

---

## 13 · IF YOU ARE UNSURE

Prefer the smaller, checkable claim. A brief that says *"the audience left here,
and these are the three things happening in these episodes"* is more useful than
one that names a cause it cannot prove. The most damaging output on this project
was not an incomplete brief — it was a **confident, fluent, wrong** one.

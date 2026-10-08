---
name: cliff-donor-project
description: Pocket FM cliff-report / donor-brief workspace at ~/projects/cliff-donor — show lanes in tmux session "cliff"; Last Howl + Vampire Prince packs shipped
metadata:
  type: project
---

Pocket FM cliff reports, donor search briefs and donor shortlist reviews. Workspace: `~/projects/cliff-donor` (created 2026-09-07, not a git repo yet).

Layout: `CONTEXT_TRANSFER.md` (the playbook — read in full before any run), `house.css`, `toolkit/` (analyse.py, build_report.py from the handover), `examples/` (3 reference deliverables), `tools/normalise.py`, `tools/lane-check.sh`, `shows/<slug>/{pack,out}`.

Five shows in flight, one lane each, tmux session `cliff` windows 1-5:
- `1-mad-vamp` Mad Vampire Lord's Bride — 1065fb8ca1ec3059ca836b40d86aaffc36de541e
- `2-beast` Beast Taming Mother — 0b75dbac2b2d4e6eb4754c95fe55c0695c3182e3
- `3-vprince` The Vampire Prince — f0a7d4ef8deccecc51d8be555fab047cde6d80c4
- `4-rogues` Marked by the Rogues — dfa25cba360cfb646cba1bfe808e195bc38eba68
- `5-blood` Blood King's Human Bride — 87a1d48d582eae5334d6c180206c67e0162480a5

**Why:** Tejas wants the 5 run in parallel with separate outputs per show, driven manually from tmux windows rather than from one chat session.

**How to apply:** Lane 1 (Mad Vampire Lord's Bride) is complete as of 2026-09-07: cliff report at `shows/mad-vampire-lords-bride/out/report.html`, served on port 8654. Diagnosis — strong holder (0.44x from ep 21-160), two breaks, both the same move: **221-240 at 1.84x** (momentum replaced by bedroom interlude plus POV handed to investigators and to Ereves, a new antagonist introduced at ep 227) and **461-480 at 1.91x** (Belle imprisoned in a breeding house while Cordelia wears her face at home). Recommended cut: ~ep 220. Survival ep51-563: 19/100 vs the benchmark's 30.

The show supplies its own control case: at 341-380 Belle is out of her body for twenty episodes and the block runs **0.65x**, because she is driving on the other side and Rohan's whole plot is recovering her. Absent-while-driving survives; absent-while-passive-with-an-impostor does not. That is a sharper version of CONTEXT_TRANSFER.md §9's pause-vs-replace rule and belongs in the §10 failure-mode table, along with both measured modes above.

Lane 2 (`beast-taming-mother`) is complete: the CMS ships this show as **Mother of Ruins**, same show_id, and it is **cultivation/progression fantasy, not romantasy** — so CONTEXT_TRANSFER.md §10's failure modes (derived from five romance serials, explicitly untested elsewhere) were not applied, and the TAB benchmark is a genre away. Report at `shows/beast-taming-mother/out/report.html`, port 8655.

**The scale finding matters beyond this show.** Mother of Ruins carries **180 listeners at ep 51** against TAB's 684,760, and 11 by the end. `tools/analyse2.py` now computes a per-block noise floor — what one departing listener is worth in ratio units — and marks a block `below resolution` when that exceeds 1.5x. Past ep 190 one leaver swings the ratio 2.15x–6.70x, so the dramatic late numbers (7.66x at 221–230 beside 0.61x at 241–250) are two or three individuals, not signal. **Always check absolute listener counts before diagnosing.** Report is scoped to eps 1–190 with the unresolvable zone shaded on the chart and greyed in the table.

Verified break at **151–190** (1.62x, 4.74x, 2.97x, 2.98x; level 64%→32%): the show swaps genre from progression fantasy to noble-court revenge melodrama, hands ~13 of eps 163–179 to antagonist Valeria Lopez's POV (Elara absent from 164 and 169 entirely), and from ep 191 makes the protagonist a drained "battery" while her husband leaves the continent. First tell is ep 151, where Elara gives the arc's prize to a secondary character. Recommended cut: ~ep 150. Ep 268 is a season-break cliffhanger, not a finale.

Trap 2 was excluded on **monetization data instead of comments**: `ep_coins` shows the free window ending at ep 85, and the blocks straddling it run 0.79x/0.93x. Useful technique when a pack ships no comments.

Lane 4 (`marked-by-the-rogues`) is **paused mid-run, stopped by Tejas 2026-09-07**. Numeric pass is complete and all four traps are checked; the story read is 577/710 episodes done, **missing eps 1-89 and 580-623** (the second range covers the break window). To resume, relaunch summarisation agents for just those two ranges — everything else is on disk under `pack/data/episodic-summaries/marked-by-the-rogues/`. Tell agents not to fork sub-agents; forks dying mid-write caused the losses.

Lane 4 findings so far: strong holder (0.36x-0.95x across ~600 eps), 28,043 listeners at ep 51 so no resolution problem, one severe break at **601-620 (3.19x)** dated precisely to **ep 603** (drop% 1.6-2.0% through 602, then 6.0/5.5/7.9%, elevated through 614, persisting across a batch boundary so not a release artifact). Reverse-harem: Evaline Greystone, wolfless and pregnant, bonded to all four Thorne brothers (River, Kieran, Oscar, Draven). Draven goes "soul dead" at ep 454.

**Two method fixes came out of this lane, both already in the tools:**
1. `tools/analyse2.py` is now **release-schedule aware**. CONTEXT_TRANSFER.md §4 Trap 1 says a >12% LDAU rise is a corrupt double-count — that is **wrong for weekly-release shows**, where the first episode of each new batch legitimately rises as lapsed listeners return. All four "corrupt" rows here were batch openers. The analyser now reads Launch Date (carried through by `tools/normalise.py`), exempts batch openers, and reports them as `reengagement_rises`. This also corrected the Mother of Ruins report, whose ep 192 was a batch opener rather than the explanation originally given.
2. `tools/interlude_density.py` counts episodes whose summaries record no plot movement, per block. Useful negative result on this show: its three most interlude-heavy blocks (5-8 no-plot episodes out of 20) are among its **best-holding**, because in a reverse-harem the intimacy is the product. Interludes alone do not cause a break.

**Seduced by Darkness** (lane `seduced-by-darkness`, show_id e4f8551dfd99f7...) — master brief COMPLETE 2026-09-07. Report at `shows/seduced-by-darkness/out/report.html`, copy in ~/Downloads. 901 episodes, 17,110 listeners at ep 51, all 901 summarised.

**This show is in CONTEXT_TRANSFER.md §9 and the recorded diagnosis does not reproduce.** §9 describes a 395-episode show breaking at 221-230 at 4.6x and ending in a couple-swap to Zeke and Alicia. This export has 901 eps; ep 901 is titled "( Finale )" in the script and resolves on Izabelle and Sebastian. The Zeke/Alicia substitution is real but sits at **eps 291-360**, mid-show — in a 395-ep cut it would have looked like the ending. The show recovers and finishes ahead of benchmark pace. So §10's "permanent handoff to another couple — terminal" is too strong: here it is temporary, costs ~2/3 of remaining audience, bleeds for ~100 eps, and is survived.

**Method finding — episode-length distortion.** The house block ratio compares drop PER EPISODE. This show's episodes grow 5.4→10.4 min mid-run, which inflates the ratio on its own. `tools/analyse2.py` now also computes `ratio_per_min` (drop ÷ that episode's runtime) and warns when episode length varies >25% within a show. Normalised, the break peak moves from 361-380 back to **321-340** — exactly where the lead is absent from 8/10 episodes — and §9's 221-230 flag is **vindicated** at 2.27x vs neighbours of 1.13x/1.18x, a block the per-episode metric shows as a harmless 1.15x. All four shows analysed have shorter episodes than TAB (1.33x-1.97x more episodes per hour), so 1.0x never meant per-hour parity.

**Control case worth reusing:** this show performs the lead-substitution twice. Eps 291-360 (leads sidelined, Zeke/Alicia take over) costs 1.61-2.29x; eps 557-596 (both leads entirely absent, Lilith/Kyle take over) costs only 1.16-1.46x. Also eps 496-515, leads unconscious 20 episodes, costs nothing. Absence is survivable; being demoted to a supporting player in another couple's story is not. Caveat stated in the brief: survivorship explains part of the second gap.

Also new: `tools/xlsx_to_csv.py` (this pack shipped retention as .xlsx not CSV).

**Serving gotcha:** ports 8654/8655/8656 are occupied (8656 by an unrelated pre-existing "The Vampire Prince" server). Always verify a preview by grepping the served <h1>, not by curl status — a busy port returns 200 from the wrong server. Seduced by Darkness serves on 8660.

Lane `blood-kings-human-bride` is still blocked on data (the-vampire-prince is now complete, see below); lane 4 marked-by-the-rogues is paused (see above). Per lane, Tejas drops the raw CMS episodic export plus scripts; `tools/lane-check.sh` reports readiness, `tools/normalise.py` fixes CMS column names, `tools/docx_scripts.py` splits .docx script bundles into per-episode text, `tools/analyse2.py` does the numeric pass (stands in for `toolkit/analyse.py`, which needs comments the packs don't ship). Packs so far carry **full scripts, not episode summaries** — six Sonnet subagents over ~94 episodes each produce them in ~15 min. The Vampire Prince already has a verified prior diagnosis in CONTEXT_TRANSFER.md §9 — per the doc's one rule, re-derive from raw data rather than inheriting that read.

**The Last Howl** (lane `the-last-howl`) — all three deliverables COMPLETE 2026-09-09. Master brief
`shows/the-last-howl/out/report.html`, donor brief `out/LH_E400_Donor_Search_Brief.md`+`.docx`, shortlist
`out/donor_shortlist_review.html`; all four mirrored to ~/Downloads. Preview port **8662** (8661 is taken
by another server).

**This pack was thinner than the others and needed a new tool.** It ships a **block-level sheet only**
(47 blocks of 10 eps: Listeners, %Ep1, %Prev, Cum Hrs) — no per-episode LDAU — so `tools/analyse2.py`
does not apply. Wrote `tools/analyse_blocks.py`: converts %Prev over n episodes to a per-episode drop,
matches blocks to TAB on cumulative hours, and also reports `ratio_per_min` and a one-listener noise
floor. **Two traps in the TAB export that will bite every future lane:** (1) the `Drop% d7` column is
**intra-episode completion, not churn** — using it gives ratios wrong by ~5x; build the comparison from
the ep-over-ep fall in `CB D0+ d7`. (2) **TAB ep 11 is a corrupt +47.6% LDAU rise** and must be
interpolated, or blocks touching it go negative.

Verified diagnosis: best holder in the set, breaks at **401–430 (2.67x / 5.81x / 2.56x)**. The engine
dies earlier, at **ep 382**, where Valerie's last self-driven fight fully resolves and nothing high-power
opens behind it; retention lags 18 episodes because the birth is still a promised payoff, and 391–400 is
the show's best block in 200 episodes at 0.63x. From ep 403 a one-month-old drives the plot; at 429 he
says "Kill her, Mom" and she obeys; the ep-465 finale belongs to Denver and Paris. **CONTEXT_TRANSFER §9
said the exodus was 391–420 — close, but the cut is at 400, not 390: 391–400 holds.** Second flag
231–280 (Vegas mafia swap, heroine drugged and rescued, then 40 eps of spice with no question) is real
but recoverable. 321–330 is delivery, not story. Cuts: PRIMARY ~400 (runway >=10h), ALT ~382 (>=20h, no
child on the board).

**Watch out:** the `Last Howl.docx` in the user's pack calls 401–465 "a slight, natural decay" — it is
the largest number on the chart. Filed as `pack/PRIOR_READ_do_not_inherit.docx`.

**A comments CSV for this show was sitting in ~/Downloads, not in the pack folder** — always check
~/Downloads for `<show> comments.csv` before writing "no comments in this pack". It is a 48-comment
sample covering eps 1–306 only, but 19% of it is production complaints (broken audio, repeated episodes,
background music drowning speech at 261–306), which is what types 321–330 as delivery.

**Donor crawl (ep 400 seat) — the finding is the shelf, not the shortlist.** Live four-lane crawl,
1,003 titles: GoodNovel 558 (search returns JSON with `totalWords`, so hours = words/10k, verified —
this is the strongest lane by far), Wattpad 191 (API `length` is a CHARACTER count; live reading time is
client-rendered so hours stayed unverified; heavy third-party fanfic = RIGHTS fails), Amazon/KU 109
(needs `curl --compressed`; page counts absent from the SERP so zero verifiable rows). Blocked and
documented: WebNovel 403, Inkitt 403, AnyStories 202 WAF, MoboReader 404, NovelCat 301. **GoodNovel
chapter bodies are app-gated; a book page exposes only ~10 first + ~8 most-read chapter titles, so no row
can be deep-read from outside the app.** Result: **no COMMISSION-grade donor**, two STRONG (*The Luna
That Broke The Alpha Council*, *The Full Moon Murders*), one CONDITIONAL, third top-3 seat left
deliberately EMPTY. Reason: this genre's commercial engine is **the rise** (rejected/abandoned/wolfless
heroine comes back), which is *The Last Howl*'s own first twenty episodes — so **screen item S6 (re-run
of our own opening) rejected most of the field, while S1 (child protagonist) rejected almost nothing.**
On any future post-triumph cut, expect the same and consider whether an earlier seam with a longer
runway is worth its cost.

**The Vampire Prince** (lane `the-vampire-prince`) — all three deliverables COMPLETE 2026-09-09, shipped
as `~/Downloads/The Vampire Prince — Cliff Report & Donor Pack/` (numbered 1/2/3 + README + Findings +
crawl data), mirroring the Last Howl pack layout. Preview port **8670/8671** (8651–8662 are all occupied
by stale servers from earlier sessions — always `lsof -nP -iTCP -sTCP:LISTEN` first, a busy port answers
200 from the wrong server).

**The comments export changed the diagnosis, so never ship a VP-style brief before checking for one.**
`~/Downloads/The Vampire Prince comments.csv` arrived a day after the first brief: 5,790 rows, **5,605
bind to an episode** via `story_title` ("Ep NNN - Title"). Three findings the curve alone could not give:

1. **The wound is confusion, not tedium.** "lost/confused" runs **0.8%** across eps 1–220, **13.9%**
   inside the 235–264 flashback, **2.1%** immediately after; "boring/dragging" stays flat at ~2–3%
   throughout. Screen donors for comprehension, not pace. Confusion starts at **ep 223**, before the
   flashback — but that earlier confusion is *engaged* (listeners theorising), which is fine; it turns
   *abandoning* once the block runs.
2. **281–320 is a narrator swap, not a story break.** The old brief called 301–320 (1.84×) "the worst
   creative block in the show". Narrator complaints are **62%** of comments at 281–300 and **51%** at
   301–320 against a 3–5% baseline; the substitution lands at **ep 291** (87/106 comments) and the
   original returns at **ep 310** (52/62). The curve decays from the block she returns, with no story
   event to explain it. A second swap at **ep 507** costs almost nothing (1.07×) — a voice change is
   expensive early and survivable late. **This is a fifth trap for CONTEXT_TRANSFER §4.**
3. **Paywall corroborated** at 564–565 ("buy the last 100 chapters"; 665−100=565 ✓). **False positive
   rejected:** the 661–680 coin-complaint spike is people chasing a 100-coin finale reward, not a wall.

Two entries were graded, per Tejas: **~ep 234** (primary repair, runway 200–300 eps / ≥25h) and **~ep 562**
(alternative, ≥13h). Entry B needed two extra screen items that do not exist at A — **S7 concealed-identity
is spent** (the audience already knows who Gavriel is) and **S8 position inversion** (our Evie is a queen;
rise-from-nothing engines demote her). Between them S7 and S8 removed nearly the whole shelf.

**Crawl result mirrors The Last Howl's, for the same structural reason.** 853 rows → 805 unique (GoodNovel
459, Wattpad 261, Kindle 133), 42 page-fetched, 14 audited. **No COMMISSION-grade donor at either entry:**
Entry A returned 3 STRONG, Entry B returned **1**, seats 2 and 3 left deliberately empty. The shelf sells
*the arrival* — a girl delivered to a vampire/fae court by treaty, purchase or curse — which is this show's
own eps 1–60; five of fourteen audited rows open that way. Lane notes: **GoodNovel book pages are
`/book/{id}`, not `/novel/{id}`** (the latter 404s as "This page does not exist"), and the search payload's
`totalWords` remains the best hours basis anywhere. **Wattpad live reading time is `>21h 51m<` in the DOM**,
not the "N hours, M minutes" string the LH lane looked for — with that fixed the re-base worked and moved
rows by under 1.5h, far less than the 6× werewolf-shelf trap, because the lane already read characters
rather than raw `length`. Mobo returns its **trending rail instead of the query** (searching "vampire
prince" yields "Jilted Wife Returns As A Billionaire Heiress"); WebNovel + Inkitt CF-403; AnyStories 202
WAF; Dreame app-gated; **0 of 133 Kindle rows carried a page count on the SERP**, so KU contributed zero
certified hours.

`tools/comments.py` (new) profiles a comments CSV into per-block complaint-family rates.
`tools/md2html.py` (new) + `textutil -convert docx` is the md→docx path on this machine — no pandoc, no
python-docx. Verify the docx by round-tripping `textutil -convert txt -stdout` and eyeballing, not by
assuming.

Also: playwright is installed for python3 but only `chromium_headless_shell-1243` is downloaded — launch
with `executable_path=~/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell`.
No pandoc on this machine; `shows/the-last-howl/build_shortlist.py` sits beside a hand-rolled minimal
docx writer used to mirror the brief.

Related: [[tab-benchmark-data]], [[multi-agent-tmux-setup]], [[review-docs-localhost]], [[previews-in-dia]]

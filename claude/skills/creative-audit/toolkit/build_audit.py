#!/usr/bin/env python3
"""Render the hook audit HTML.

    python build_audit.py --ledger ledger.json --title "Show Name" --out audit.html

Fill LOGLINE, LEAD, CHECKED, HOOKS, BREAKS, DRIFT, LEDGER below after reading the
scripts. The script lays out the two-column hook blocks correctly (the <aside> INSIDE
.act-body, which is the defect that keeps recurring), renders every table, and
validates on each run.

Static HTML only. No JavaScript.
"""
import argparse, html, json, pathlib, re, sys
from html.parser import HTMLParser

try:
    import arc_view                      # same directory
except ImportError:                      # arcs are optional; the report works without
    arc_view = None

# ═════════════════════════════════════════════════════════════════════════════
# FILL THESE IN. Episode numbers come from ledger.json, not from memory.
# ═════════════════════════════════════════════════════════════════════════════

LOGLINE = """
The premise in one paragraph, as if to a first-time listener. No evaluation.
"""

# The show's strongest hook and whether it is kept.
LEAD = """
<b>The headline.</b> One or two sentences naming the strongest hook and its fate.
"""

# Every episode range actually read, and anything inferred rather than read.
CHECKED = [
    "Read in full: eps 1–268 (all CMS scripts, 2.5 MB).",
    "Resolution episodes re-read individually: 141, 204, 287.",
    "Inferred, not read: nothing.",
]

# Ranked strongest first. pull = (stakes, specificity, recurrence, centrality), each 0-3.
# verdict: paid | paid late | deflected | offscreen | broken | dangling | open at finale
HOOKS = [
    {
        "code": "H1",
        "q": "Who destroyed her body, and will they pay for it?",
        "kind": "debt",
        "opens": 3,
        "resolves": 287,
        "pull": (3, 3, 3, 2),   # recurrence, specificity, ownership, consequence
        "verdict": "paid late",
        "story": [
            "What the script asks, told straight. Present tense. No evaluation — "
            "verdict language belongs in the panel.",
            "How the script keeps asking it.",
            "How it ends.",
        ],
        "status": "Paid late · 284 episodes open",
        "panel": "One or two sentences of verdict.",
        "quotes": [("the line from the script that poses it", 3),
                   ("the line that answers it", 287)],
        "note": "",          # optional extra line in the ranked table
    },
]

# code: B1 retcon · B2 offscreen close · B3 deflation · B4 substitution
#       B5 drop · B6 deferred past use
BREAKS = [
    {
        "code": "B2",
        "hook": "H4",
        "title": "The betrothal is settled in a gap",
        "what": "What was promised, and what arrived instead.",
        "promised": ("quoted line at the promise", 37),
        "broke": ("quoted line at the break", 141),
    },
]

# code: D1 promise vacuum · D2 lead stops driving · D3 cast bloat
#       D4 repetition and stall · D5 pacing · D6 other (name the mechanism)
# severity: mild | marked | severe
DRIFT = [
    {
        "code": "D1",
        "eps": (88, 110),
        "signal": "Promise vacuum",
        "severity": "marked",
        "evidence": "No hook of pull >=8 live. 14 of 23 episodes end without posing "
                    "a question.",
        "prose": ["A paragraph on the mechanism, grounded in specific episodes."],
    },
]

# Rows only where the episode carries weight: a top-ten hook opens or closes, a
# promise breaks, or a drift zone starts or ends. ~30-50 rows for a 270-ep show.
# flag=True tints the row (a break, or a drift zone opening).
LEDGER = [
    {"ep": 3, "cliff": "What the episode leaves hanging.",
     "open": "H1", "note": "H1 opens", "flag": False},
]

# Who the listener needs to hold in their head. 5-6 entries, in the order the show
# introduces them. Say who they are, not what they mean.
CAST = [
    ("Name", "Who they are in one line, for someone who has never heard of this show."),
]

# One entry per arc id in arcs.json. Left column of each act block.
# Story only: what happens, told straight. No evaluation. Verdict language belongs
# in the panel on the right.
ACT_STORIES = {
    "A1": {"story": ["What happens in this act, in plain words, for someone who has "
                     "never heard of this show. 900 characters or so, three or four "
                     "real paragraphs."],
           "note": "One optional sentence of judgment. This is the only place it goes."},
}

SUBTITLE = "The promises this show makes, and whether it keeps them"

# ═════════════════════════════════════════════════════════════════════════════
# Rendering. Nothing below needs editing.
# ═════════════════════════════════════════════════════════════════════════════

AXES = ("recurrence", "specificity", "ownership", "consequence")
VERDICT_CLASS = {
    "paid": "hold", "paid late": "near", "deflected": "flag", "offscreen": "flag",
    "broken": "flag", "dangling": "flag", "open at finale": "flag",
}
SEV_CLASS = {"mild": "near", "marked": "near", "severe": "flag"}


def e_(s):
    return e(s)


def e(s):
    """Escape for HTML text. The unescaped & is the recurring defect."""
    return html.escape(str(s), quote=False)


def ps(paras):
    return "".join(f"<p>{e(p)}</p>" for p in paras)



# ── act blocks: the story arc by arc, and what the questions did in each ─────
def arc_hooks(arc, hooks, health, last):
    """Two things decide a question's place in an act, and they are independent:

        does it CLOSE here, or is it still open when the act ends?
        did it START here, or was it carried in from an earlier act?

    That gives four states, grouped under two headings. Whether the act actually
    raised the question is a separate fact, carried on the card as a count, not a
    fifth category: a question can be carried in and ignored, or carried in and
    worked hard, and both are still 'carried in'.
    """
    lo, hi = arc["from"], arc["to"]
    hh = {h["code"]: h for h in (health or {}).get("hooks", [])}
    out = {"carried_open": [], "started_open": [],
           "carried_closed": [], "started_closed": []}
    for h in hooks:
        op = h["opens"]
        cl = h.get("resolves")
        end = cl or last
        if op > hi or end < lo:
            continue
        inside = [x for x in (hh.get(h["code"], {}).get("touch_eps") or [])
                  if lo <= x <= hi]
        starts_here = lo <= op <= hi
        ends_here = bool(cl) and lo <= cl <= hi
        key = (("started_" if starts_here else "carried_")
               + ("closed" if ends_here else "open"))
        out[key].append((h, len(inside)))
    for k in out:
        out[k].sort(key=lambda pair: pair[0]["opens"])
    return out


ROLE_STYLE = {
    "carried_open":   ("CARRIED IN",       "#8a6d21", "#f3ead0"),
    "started_open":   ("STARTS HERE",      "#8a6d21", "#f3ead0"),
    "carried_closed": ("CARRIED IN, ANSWERED HERE", "#3d6b3f", "#e3ece1"),
    "started_closed": ("OPENS AND CLOSES HERE",     "#3d6b3f", "#e3ece1"),
}
GROUPS = (
    ("Still open when this act ends", ("carried_open", "started_open")),
    ("Answered in this act",          ("carried_closed", "started_closed")),
)


def _acts_touched(h, arcs, health):
    """Which act numbers actually raise this question."""
    hh = next((k for k in (health or {}).get("hooks", []) if k["code"] == h["code"]), {})
    touches = hh.get("touch_eps") or []
    return [i for i, a in enumerate(arcs, 1)
            if any(a["from"] <= x <= a["to"] for x in touches)]


def hook_line(h, n, arcs, health, last, here_i, role):
    """One question inside an act. The tag says which of the four states it is in;
    the bar says how much of the act actually raised it, which is a separate fact."""
    label, ink, bg = ROLE_STYLE[role]
    here = arcs[here_i]
    act_len = here["to"] - here["from"] + 1
    share = n / max(1, act_len)
    pct = f'{100 * share:.0f}%'
    cl = h.get("resolves")

    if role == "started_closed":
        journey = f'Opened at {h["opens"]} and answered at {cl}, inside this act.'
    elif role == "carried_closed":
        journey = (f'Asked in Act {_act_of(h["opens"], arcs)} and answered here, '
                   f'at episode {cl}.')
    elif role == "started_open":
        journey = (f'Opens here. Answered in Act {_act_of(cl, arcs)}.' if cl
                   else 'Opens here and is never answered.')
    else:
        journey = (f'Asked in Act {_act_of(h["opens"], arcs)}. '
                   + (f'Answered in Act {_act_of(cl, arcs)}.' if cl
                      else 'Never answered.'))

    ignored = ('' if n else
               '<span class="tagx" style="background:#efd9d4;color:#9a3b28;'
               'margin-left:5px">NOT RAISED HERE</span>')
    bar = (f'<span style="display:inline-block;width:74px;height:7px;'
           f'background:#e6e0d3;border-radius:4px;overflow:hidden;vertical-align:0">'
           f'<span style="display:block;width:{share * 100:.0f}%;height:100%;'
           f'background:{"#3d6b3f" if n else "#c9c2b4"}"></span></span>')
    return (f'<div class="actx-card">'
            f'<span class="tagx" style="background:{bg};color:{ink}">{label}</span>'
            f'{ignored}'
            f'<div class="q"><b>{e(h["code"])}</b> \u00b7 {e(h["q"])}</div>'
            f'<div class="m">{bar}<span>raised in <b>{n}</b> of {act_len} eps '
            f'<span style="color:#a49a89">({pct})</span></span></div>'
            f'<div class="j">{e(journey)}</div></div>')


def _act_of(ep, arcs):
    for i, a in enumerate(arcs, 1):
        if a["from"] <= ep <= a["to"]:
            return i
    return "?"


def breaks_in(arc, breaks):
    """Pure join: which promises break inside this act. Returns data, not markup.

    An act is one thing and the promises, hooks and trouble zones inside it are three
    others. Keeping the joins separate from the rendering is what lets a second report
    show the same facts in a different shape without touching this one."""
    lo, hi = arc["from"], arc["to"]
    return [b for b in (breaks or []) if lo <= b["broke"][1] <= hi]


def drift_in(arc, drift):
    """Pure join: which trouble zones overlap this act, and by how much."""
    lo, hi = arc["from"], arc["to"]
    out = []
    for d in (drift or []):
        a0, b0 = d["eps"]
        if a0 <= hi and b0 >= lo:
            out.append({**d,
                        "_inside": max(0, min(b0, hi) - max(a0, lo) + 1),
                        "_span": hi - lo + 1})
    return out


# `arc_hooks` is already a pure join and returns the four hook states for an act.
# Named here so the three joins read as a set.
hooks_in = arc_hooks


def act_shell(arc, i, stories):
    """The act and nothing else: its number, name, episode range and summary.

    No hooks, no promises, no trouble. Those are joined on separately by whoever is
    rendering, so an act section can be composed differently in another document."""
    story = stories.get(arc["id"], {})
    paras = story.get("story") or [arc.get("about", "")]
    note = story.get("note")
    return (f'<div class="act-head">'
            f'<span class="act-num">Act {i}</span>'
            f'<h3>{e(arc.get("name", arc["id"]))}</h3>'
            f'<span class="act-eps">Episodes {arc["from"]}{NDASH}{arc["to"]}'
            f'</span></div>'
            f'<div class="story" style="margin-top:14px">'
            f'<div class="col-h">What happens in the story</div>{ps(paras)}</div>'
            + (f'<div class="note" style="margin:4px 0 0;max-width:820px">'
               f'{e(note)}</div>' if note else ''))


def act_extras(arc, breaks, drift):
    """Broken promises and trouble spots that belong to this act.

    Everything an act contains should be visible from inside the act. Part II and
    Part III still carry the full account; these are the pointers into them."""
    lo, hi = arc["from"], arc["to"]
    out, out2 = "", ""

    mine = breaks_in(arc, breaks)
    for b in mine:
        out += (f'<div class="actx-card">'
                f'<span class="tagx" style="background:#efd9d4;color:#9a3b28">'
                f'BROKEN \u00b7 ep {b["broke"][1]}</span>'
                f'<div class="q">{e(b.get("title", ""))}</div>'
                + (f'<div style="font-size:12px;color:#5f584c;line-height:1.45;'
                   f'margin-top:5px">{e(b["what"][:150])}'
                   + ('\u2026' if len(b["what"]) > 150 else '') + '</div>'
                   if b.get("what") else '')
                + f'<div class="j">Promised at episode {b["promised"][1]}. '
                f'<a href="#break-{b.get("_n", 1)}" style="color:#8a8173">'
                f'both quotes \u2192</a></div></div>')

    zones = drift_in(arc, drift)
    for d in zones:
        a0, b0 = d["eps"]
        inside, span = d["_inside"], d["_span"]
        ink, bg = (("#9a3b28", "#efd9d4") if d["severity"] == "severe"
                   else ("#8a6d21", "#f3ead0"))
        out2 += (f'<div class="actx-card">'
                 f'<span class="tagx" style="background:{bg};color:{ink}">'
                 f'{e(SEV_WORD[d["severity"]].upper())}</span>'
                 f'<div class="q">{e(d["signal"])}</div>'
                 + (f'<div style="font-size:12px;color:#5f584c;line-height:1.45;'
                    f'margin-top:5px">{e(d["story"])}</div>' if d.get("story") else '')
                 + f'<div class="j">Episodes {a0}\u2013{b0}, covering <b>{inside}</b> '
                 f'of this act\u2019s {span}. '
                 f'<a href="#trouble-{d.get("_n", 1)}" style="color:#8a8173">'
                 f'the evidence \u2192</a></div></div>')
    return out, out2


SEP = " \u00b7 "
NDASH = "\u2013"
APOS = "\u2019"


def act_blocks(arcs, hooks, health, last, stories, breaks=None, drift=None):
    """Story on top, findings as labelled groups of cards below.

    Three groups, always in this order and always separated, so a reader knows which
    kind of thing they are looking at: the questions, the promises the act breaks,
    and the stretches of trouble that overlap it."""
    out = []
    for i, arc in enumerate(arcs, 1):
        st = arc_hooks(arc, hooks, health, last)
        story = stories.get(arc["id"], {})
        paras = story.get("story") or [arc.get("about", "")]
        broke_cards, trouble_cards = act_extras(arc, breaks, drift)

        still_open = len(st["carried_open"]) + len(st["started_open"])
        closed = len(st["carried_closed"]) + len(st["started_closed"])
        started = len(st["started_open"]) + len(st["started_closed"])
        ignored = sum(1 for k in st for _, n in st[k] if n == 0)
        bits = []
        if started:
            bits.append(f'{started} opened here')
        if closed:
            bits.append(f'{closed} answered here')
        if still_open:
            bits.append(f'{still_open} left open')
        if ignored:
            bits.append(f'{ignored} not raised at all')
        if broke_cards:
            bits.append(f'{broke_cards.count("actx-card")} promise'
                        f'{"" if broke_cards.count("actx-card") == 1 else "s"} broken')
        if trouble_cards:
            bits.append(f'{trouble_cards.count("actx-card")} trouble spot'
                        f'{"" if trouble_cards.count("actx-card") == 1 else "s"}')

        groups = ""
        # the questions, in two categories of two
        for title, keys in GROUPS:
            cards = "".join(hook_line(h, n, arcs, health, last, i - 1, k)
                            for k in keys for h, n in st[k])
            if cards:
                groups += (f'<div class="actx-group"><h4>{title}'
                           f'<span style="float:right;font-weight:400;'
                           f'text-transform:none;letter-spacing:0;color:#a49a89">'
                           f'bar = share of this act{APOS}s episodes</span></h4>'
                           f'<div class="actx-cards">{cards}</div></div>')
        for title, cards, hint in (
                ("Promises broken here", broke_cards, ""),
                ("Trouble here", trouble_cards, "")):
            if cards:
                groups += (f'<div class="actx-group"><h4>{title}'
                           + (f'<span style="float:right;font-weight:400;'
                              f'text-transform:none;letter-spacing:0;color:#a49a89">'
                              f'{hint}</span>' if hint else '')
                           + f'</h4><div class="actx-cards">{cards}</div></div>')

        note = story.get("note")
        out.append(
            f'<section class="actx" id="act-{i}" style="scroll-margin-top:18px">'
            # Story first and unqualified. The counts are what the analysis found;
            # the story is what the analysis is about, and it earns the top of the act.
            + act_shell(arc, i, stories)
            + (f'<div class="actx-found"><span>What the analysis found here</span>'
               f'<span class="actx-sum">{e(SEP.join(bits))}</span></div>'
               if groups else '')
            + groups + '</section>')
    return "".join(out)


def hook_block(h, health=None):
    total = sum(h["pull"])
    cls = "hold" if h["verdict"].startswith("paid") else "cliff"
    span = (f"Opens ep {h['opens']} · "
            + (f"resolves ep {h['resolves']}" if h.get("resolves")
               else "never resolves"))
    axes = ", ".join(f"{a} {v}" for a, v in zip(AXES, h["pull"]))
    quotes = "".join(
        f"<blockquote>{e(q)}<cite>— ep {n}</cite></blockquote>"
        for q, n in h.get("quotes", []))
    cmts = (f'<div class="cmts"><div class="cmts-h">In the script</div>{quotes}</div>'
            if quotes else "")
    cn = continuity_note(health, h["code"]) if health else ""
    note = (f'<p class="aud-ret" style="color:#6b6357">{e(cn)}</p>' if cn else "")
    # The <aside> MUST sit inside .act-body or the two-column grid silently collapses.
    return (
        f'<section class="act"><div class="act-head">'
        f'<span class="act-num">{e(h["code"])}</span><h3>{e(h["q"])}</h3>'
        f'<span class="act-eps">{e(span)}</span></div>'
        f'<div class="act-body">'
        f'<div class="story"><div class="col-h">What the script asks</div>'
        f'{ps(h["story"])}</div>'
        f'<aside class="aud {cls}"><div class="aud-h">The verdict</div>'
        f'<div class="aud-status">{e(h["status"])}</div>'
        f'<p class="aud-ret">Pull <b>{total}/12</b> — {e(axes)}. {e(h["panel"])}</p>'
        f'{note}{cmts}</aside>'
        f'</div></section>')


DASH = "\u2014"

TIP_CSS = """
/* Wider page. house.css caps .wrap at 900px, which suits a printed brief but wastes
   half a laptop screen on tables and charts. Overridden here rather than in
   house.css, which is shared with the sibling skill.
   Prose is NOT widened: a line longer than about 75 characters is harder to read,
   not easier. The extra width goes to tables, charts and the act panels. */
.wrap{max-width:1320px;padding-left:40px;padding-right:40px}
/* one shared measure in px: `ch` differs between the serif body and the sans
   notes, so a ch cap made blocks that should line up look ragged */
.logline,.lead,.note,.readnote,.diag,.pattern{max-width:880px}
.act-story p,.story p{max-width:none}
/* the story column is capped so prose stays readable; the panel takes the rest */
.act-body{grid-template-columns:minmax(0,760px) 400px;gap:40px}
/* Act blocks do NOT use the two-column act layout. A story of three paragraphs
   beside a panel of eleven findings leaves half the row empty, and the imbalance
   gets worse the more an act contains. Story on top, findings as cards below,
   which balances at any count. */
.actx{border-top:2px solid #c9bfa8;padding-top:26px;margin:44px 0 0}
.actx .act-num{font-size:11px;letter-spacing:.14em}
.actx .act-head h3{font-size:27px}
.actx .story{max-width:820px}
.actx-group{margin-top:20px}
.actx-group>h4{font-family:'Helvetica Neue',Arial,sans-serif;font-size:10px;
  letter-spacing:.13em;text-transform:uppercase;color:#8a8173;font-weight:700;
  margin:0 0 9px;padding-bottom:5px;border-bottom:1px solid #e4ddd0}
.actx-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(248px,1fr));
  gap:11px}
.actx-card{background:#faf8f3;border:1px solid #eee7d9;border-radius:7px;
  padding:11px 13px}
.actx-card .q{font-size:13px;color:#2a2620;line-height:1.4;margin-top:6px}
.actx-card .m{font-family:'Helvetica Neue',Arial,sans-serif;font-size:10.5px;
  color:#6b6357;margin-top:7px;display:flex;align-items:center;gap:8px}
.actx-card .j{font-family:'Helvetica Neue',Arial,sans-serif;font-size:10.5px;
  color:#a49a89;margin-top:3px}
.tagx{display:inline-block;padding:1px 7px;border-radius:3px;
  font-family:'Helvetica Neue',Arial,sans-serif;font-size:9.5px;
  letter-spacing:.05em;font-weight:700}
/* Jumping from an act card to the detail used to drop you in a list of five with
   no signal about which one you came for. :target lights up the arrival, pure CSS. */
:target{animation:landed 2.4s ease-out}
:target>.act-head h3,h3:target{background:#fdf3d6;box-shadow:0 0 0 6px #fdf3d6;
  border-radius:3px}
@keyframes landed{0%{background:#fdf3d6}70%{background:#fdf3d6}100%{background:transparent}}
.backlink{display:inline-block;font-family:'Helvetica Neue',Arial,sans-serif;
  font-size:10.5px;color:#8a8173;text-decoration:none;border:1px solid #e4ddd0;
  border-radius:4px;padding:2px 8px;margin-bottom:9px;background:#faf8f3}
.backlink:hover{border-color:#c9bfa8;color:#3a352e}
/* The findings are secondary to the story above them, and the divider says so. */
/* Native SVG <title> needs a slow hover on a 1px target, which is unusable on a
   665-episode chart. This shows a real readout instead: every episode carries a
   hidden label pinned to the same spot, and :hover reveals just that one. */
/* Scope these to the hit rect only. Targeting `rect` wiped the readout's own
   background, which is also a rect inside the same group. */
.ephit .hit{fill:transparent}
.ephit:hover .hit{fill:#1c1a17;fill-opacity:.08}
.ephit .lbl,.ephit text{opacity:0;pointer-events:none}
.ephit:hover .lbl,.ephit:hover text{opacity:1}
.actx-found{display:flex;justify-content:space-between;align-items:baseline;gap:16px;
  margin:30px 0 4px;padding-top:11px;border-top:2px solid #1c1a17;
  font-family:'Helvetica Neue',Arial,sans-serif}
.actx-found>span:first-child{font-size:10px;letter-spacing:.13em;text-transform:uppercase;
  color:#1c1a17;font-weight:700}
.actx-sum{font-size:11.5px;color:#8a8173;text-align:right}
.actx .story p{font-size:15.5px;line-height:1.66}
.actx .story .col-h{margin-bottom:11px}
figure svg{max-width:100%}
table{font-size:13px}
@media(max-width:1000px){
  .wrap{padding-left:22px;padding-right:22px}
  .act-body{grid-template-columns:1fr}
}

.tw{position:relative;display:inline-block;cursor:help}
.tw>.tt{visibility:hidden;opacity:0;position:absolute;z-index:40;right:0;top:130%;
  width:330px;background:#fdfbf6;color:#2a2620;border:1px solid #d8d0bd;
  border-radius:7px;padding:11px 13px;box-shadow:0 6px 22px rgba(28,26,23,.16);
  font-family:'Helvetica Neue',Arial,sans-serif;font-size:11.5px;line-height:1.5;
  text-align:left;transition:opacity .12s;white-space:normal;font-weight:400}
.tw:hover>.tt{visibility:visible;opacity:1}
.tt b{color:#1c1a17}
.tt .h{font-size:10px;letter-spacing:.07em;text-transform:uppercase;color:#a49a89;
  border-bottom:1px solid #e4ddd0;padding-bottom:5px;margin-bottom:7px}
.tt .ax{display:flex;justify-content:space-between;gap:10px;margin-top:7px}
.tt .ax b{white-space:nowrap}
.tt .r{color:#5f584c;margin:1px 0 0}
.tt .n{color:#8a8173;font-style:italic;margin-top:8px;padding-top:6px;
  border-top:1px solid #efe9db}
"""

VERDICT_WHY = {
    "paid": "The show answers this on the page, in a scene, while people still care.",
    "paid late": "The show does answer it on the page, but so long after the question "
                 "was last alive that most of the waiting was silence.",
    "deflected": "A character asks it outright and the show moves past without "
                 "answering it.",
    "offscreen": "The answer happens between episodes and is reported afterwards. "
                 "There is no scene where it happens.",
    "broken": "The show states something will happen and then withdraws it.",
    "dangling": "Never answered, and the show stopped raising it long before the end.",
    "open at finale": "Still unanswered when the show ends.",
}
AXIS_MEANS = {
    "recurrence": "how often the show comes back to it",
    "specificity": "how concrete the question is",
    "ownership": "whose question it is",
    "consequence": "what changes once it is answered",
}


def recurrence_reason(h, health):
    """Computed, not judged: the actual episode counts behind the score."""
    if not health:
        return ""
    hh = next((k for k in health.get("hooks", []) if k["code"] == h["code"]), None)
    if not hh:
        return ""
    op = hh["opens"]
    cl = hh.get("resolves") or health.get("last_ep")
    n_open = cl - op + 1
    hits = len([x for x in hh.get("touch_eps") or [] if op <= x <= cl])
    return (f'Raised in <b>{hits} of the {n_open} episodes</b> it was open, about '
            f'{100 * hits / max(1, n_open):.0f} in every 100. '
            f'Longest silence <b>{hh.get("longest_silence", "?")} episodes</b>.')


def pull_tip(h, health):
    reasons = h.get("pull_why") or {}
    rows = []
    for axis, v in zip(AXES, h["pull"]):
        why = (recurrence_reason(h, health) if axis == "recurrence"
               else reasons.get(axis, ""))
        rows.append(f'<div class="ax"><b>{e(axis.capitalize())}</b>'
                    f'<span>{v} of 3</span></div>'
                    f'<div class="r">{why or e(AXIS_MEANS[axis])}</div>')
    return (f'<div class="tt"><div class="h">Pull {sum(h["pull"])} out of 12</div>'
            + "".join(rows)
            + '<div class="n">Every candidate was scored before any were chosen, so a '
              'low score is a finding, not a hook that lost a beauty contest.</div>'
            '</div>')


def verdict_tip(h):
    res, op = h.get("resolves"), h["opens"]
    where = (f'Asked at episode <b>{op}</b>, answered at <b>{res}</b>, '
             f'{res - op} episodes later.' if res else
             f'Asked at episode <b>{op}</b> and never answered.')
    extra = h.get("verdict_why") or ""
    return (f'<div class="tt"><div class="h">{e(h["verdict"])}</div>'
            f'<div class="r">{where}</div>'
            f'<div class="r" style="margin-top:6px">'
            f'{e(VERDICT_WHY.get(h["verdict"], ""))}</div>'
            + (f'<div class="n">{e(extra)}</div>' if extra else '')
            + '</div>')


def ranked_table(hooks, health=None):
    rows = []
    for h in hooks:
        total = sum(h["pull"])
        res = h.get("resolves")
        span = (res - h["opens"]) if res else None
        cls = VERDICT_CLASS.get(h["verdict"], "")
        kind = h.get("kind")
        span_txt = f'{span} eps' if span is not None else DASH
        tag = (f'<span style="display:inline-block;margin-left:7px;padding:1px 6px;'
               f'border:1px solid #ddd5c4;border-radius:9px;font-size:9.5px;'
               f'font-family:Helvetica Neue,Arial;color:#8a8173;vertical-align:1px">'
               f'{e(kind)}</span>' if kind else "")
        rows.append(
            f'<tr{" class=flag" if cls == "flag" else ""}>'
            f'<td class="bt"><b>{e(h["code"])}</b> \u00b7 {e(h["q"])}{tag}'
            + (f'<br><span style="color:#8a8173">{e(h["note"])}</span>'
               if h.get("note") else "")
            + f'</td>'
            f'<td class="c">{h["opens"]}</td>'
            f'<td class="c">{res if res else "never"}</td>'
            f'<td class="c">{span_txt}</td>'
            f'<td class="c"><span class="tw"><b>{total}</b>/12'
            f'<span style="border-bottom:1px dotted #c9bfa8"></span>'
            f'{pull_tip(h, health)}</span></td>'
            f'<td class="c"><span class="tw"><span class="stw {cls}">'
            f'{e(h["verdict"])}</span>{verdict_tip(h)}</span></td></tr>')
    return (
        '<table><thead><tr><th>The question</th>'
        '<th>Asked at</th><th>Answered at</th><th>Stays open</th>'
        '<th>Pull</th><th>Verdict</th>'
        '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>')


def resolutions_table(hooks):
    rows = []
    for h in hooks:
        res = h.get("resolves")
        cls = VERDICT_CLASS.get(h["verdict"], "")
        rows.append(
            f'<tr{" class=flag" if cls == "flag" else ""}>'
            f'<td class="c"><b>{e(h["code"])}</b></td>'
            f'<td class="c">{res if res else "—"}</td>'
            f'<td class="bt">{e(h["status"])}</td>'
            f'<td class="c"><span class="stw {cls}">{e(h["verdict"])}</span></td></tr>')
    return ('<table><thead><tr><th>Hook</th><th>Closes</th><th>How it closes</th>'
            '<th>Verdict</th></tr></thead><tbody>' + "".join(rows) + '</tbody></table>')


def _act_for(ep, arcs):
    for i, a in enumerate(sorted(arcs or [], key=lambda a: a["from"]), 1):
        if a["from"] <= ep <= a["to"]:
            return i, a.get("name", a["id"])
    return None, None


def breaks_section(breaks, arcs=None):
    if not breaks:
        return ('<div class="note"><b>No broken promises found.</b> Every stated '
                'promise traced to a payoff on screen.</div>')
    out = []
    for k, b in enumerate(breaks, 1):
        b["_n"] = k
        pq, pn = b["promised"]
        bq, bn = b["broke"]
        ai, an = _act_for(bn, arcs)
        back = (f'<a class="backlink" href="#act-{ai}">\u2190 Act {ai}, {e(an)}</a>'
                if ai else '')
        out.append(
            f'<section class="act" id="break-{k}" style="scroll-margin-top:18px">'
            f'{back}'
            f'<div class="act-head">'
            f'<span class="act-num">{e(b["code"])}</span>'
            f'<h3>{e(b.get("title") or b["hook"])}</h3>'
            f'<span class="act-eps">{e(b["hook"])} · ep {pn} → ep {bn}</span></div>'
            f'<div class="act-body">'
            f'<div class="story"><div class="col-h">What broke</div>'
            f'{ps([b["what"]])}</div>'
            f'<aside class="aud cliff"><div class="aud-h">Both sides quoted</div>'
            f'<div class="cmts"><div class="cmts-h">The promise</div>'
            f'<blockquote>{e(pq)}<cite>— ep {pn}</cite></blockquote>'
            f'<div class="cmts-h">The break</div>'
            f'<blockquote>{e(bq)}<cite>— ep {bn}</cite></blockquote></div>'
            f'</aside></div></section>')
    return "".join(out)


def drift_section(drift, arcs=None):
    if not drift:
        return '<div class="note"><b>No drift zones found.</b></div>'
    rows = []
    for d in drift:
        a, b = d["eps"]
        cls = SEV_CLASS.get(d["severity"], "")
        rows.append(
            f'<tr{" class=flag" if cls == "flag" else ""}>'
            f'<td class="c">{a}–{b}</td>'
            f'<td class="c"><b>{e(d["code"])}</b></td>'
            f'<td>{e(d["signal"])}</td>'
            f'<td class="c"><span class="stw {cls}">{e(d["severity"])}</span></td>'
            f'<td class="bt">{e(d["evidence"])}</td></tr>')
    table = ('<table><thead><tr><th>Episodes</th><th>Code</th><th>Signal</th>'
             '<th>Severity</th><th>Evidence in the script</th></tr></thead><tbody>'
             + "".join(rows) + '</tbody></table>')
    numbered = sorted(drift, key=lambda x: x["eps"][0])
    for n, d in enumerate(numbered, start=1):
        d["_n"] = n
    def _back(d):
        ai, an = _act_for(d["eps"][0], arcs)
        return (f'<a class="backlink" href="#act-{ai}">\u2190 Act {ai}, {e(an)}</a><br>'
                if ai else '')
    prose = "".join(
        _back(d) +
        f'<h3 id="trouble-{d["_n"]}" style="font-family:Georgia,serif;font-size:17px;'
        f'margin:26px 0 8px;scroll-margin-top:18px">'
        f'<span style="display:inline-block;width:19px;height:19px;line-height:19px;'
        f'border-radius:50%;background:#efe9db;color:#6b6357;font-size:11px;'
        f'text-align:center;font-family:Helvetica Neue,Arial;vertical-align:2px;'
        f'margin-right:7px">{d["_n"]}</span>'
        f'Episodes {d["eps"][0]}–{d["eps"][1]} · {e(d["signal"])}</h3>'
        + (f'<div style="max-width:820px;margin:6px 0 10px 26px;font-size:15px;'
           f'line-height:1.6;color:#2a2620">{e(d["story"])}</div>'
           if d.get("story") else '')
        + f'<div style="font-family:Helvetica Neue,Arial;font-size:11.5px;'
          f'color:#8a8173;margin:0 0 12px 26px;padding-left:11px;'
          f'border-left:2px solid #e4ddd0"><b>The evidence:</b> '
          f'{e(d.get("evidence", ""))}</div>'
        + ps(d["prose"]) for d in numbered)
    return table + prose


def ledger_table(rows):
    out = []
    for r in rows:
        out.append(
            f'<tr{" class=flag" if r.get("flag") else ""}>'
            f'<td class="c">{r["ep"]}</td>'
            f'<td class="bt">{e(r["cliff"])}</td>'
            f'<td class="c">{e(r.get("open") or "—")}</td>'
            f'<td class="bt">{e(r.get("note") or "")}</td></tr>')
    return ('<table><thead><tr><th>Ep</th><th>What the episode leaves hanging</th>'
            '<th>Threads open</th><th>Note</th></tr></thead><tbody>'
            + "".join(out) + '</tbody></table>')





# ── how many questions are live at once ──────────────────────────────────────
LIVE_WINDOW = 10   # a question keeps a listener wondering ~10 eps after it was raised


def live_counts(health, window=LIVE_WINDOW):
    """Per episode: which hooks are open AND were actually raised recently.

    Formally open is not the same as alive. A question the show has not mentioned
    for fifty episodes is not holding anyone. Only touches count."""
    last = health.get("last_ep") or 1
    per = []
    for ep in range(1, last + 1):
        live = []
        for h in health.get("hooks") or []:
            op = h["opens"]
            cl = h.get("resolves") or last
            if not (op <= ep <= cl):
                continue
            if any(ep - window <= x <= ep for x in h.get("touch_eps") or []):
                live.append(h["code"])
        per.append(live)
    return per


def dead_runs(per, minimum=4):
    """Runs of consecutive episodes where nothing at all is live."""
    runs, cur = [], []
    for i, live in enumerate(per, start=1):
        if not live:
            cur.append(i)
        else:
            if len(cur) >= minimum:
                runs.append((cur[0], cur[-1], len(cur)))
            cur = []
    if len(cur) >= minimum:
        runs.append((cur[0], cur[-1], len(cur)))
    return runs


def coverage_chart(health, arcs=None):
    per = live_counts(health)
    if not per:
        return "", []
    last = len(per)
    L, W, H2 = 44.0, 812.0, 108.0
    top = max(1, max(len(x) for x in per))
    x = lambda ep: L + W * (ep - 1) / max(1, last - 1)
    w = max(0.75, W / last)
    o = [f'<svg viewBox="0 0 900 {H2 + 92:.0f}" width="100%" role="img" '
         f'aria-label="How many questions are live at each episode">']
    for k in range(1, top + 1):
        y = H2 - H2 * k / top
        o.append(f'<line x1="{L}" y1="{y:.1f}" x2="{L + W}" y2="{y:.1f}" '
                 f'stroke="#e4ddd0" stroke-width="1"/>')
        o.append(f'<text x="{L - 7}" y="{y + 3.5:.1f}" font-size="9" fill="#a49a89" '
                 f'text-anchor="end" font-family="Helvetica Neue,Arial">{k}</text>')
    act_of = {}
    for k, a in enumerate(sorted(arcs or [], key=lambda a: a["from"]), 1):
        for ep in range(a["from"], a["to"] + 1):
            act_of[ep] = (k, a.get("name", a["id"]))

    for i, live in enumerate(per):
        n = len(live)
        if n == 0:
            o.append(f'<rect x="{x(i + 1):.2f}" y="{H2 - 3:.1f}" width="{w:.2f}" '
                     f'height="4" fill="#9a3b28"/>')
            continue
        h = H2 * n / top
        o.append(f'<rect x="{x(i + 1):.2f}" y="{H2 - h:.1f}" width="{w:.2f}" '
                 f'height="{h:.1f}" fill="#3d6b3f" opacity=".72"/>')

    # One hover target per episode, each carrying a readout pinned to the top-left of
    # the plot so it never chases the pointer or falls off the edge.
    for i, live in enumerate(per):
        ep = i + 1
        act = act_of.get(ep)
        head = f'ep {ep}' + (f'  \u00b7  Act {act[0]}, {act[1]}' if act else '')
        body = (f'{len(live)} live: ' + ', '.join(live) if live
                else 'nothing live \u2014 no question was being raised')
        o.append(f'<g class="ephit">'
                 f'<rect class="hit" x="{x(ep):.2f}" y="0" '
                 f'width="{max(w, 1.1):.2f}" height="{H2:.1f}"/>'
                 f'<rect class="lbl" x="{L}" y="{H2 + 36:.1f}" width="580" '
                 f'height="21" rx="4" fill="#1c1a17"/>'
                 f'<text x="{L + 11}" y="{H2 + 51:.1f}" font-size="11.5" '
                 f'font-family="Helvetica Neue,Arial">'
                 f'<tspan fill="#f4f1ec" font-weight="700">{e(head)}</tspan>'
                 f'<tspan fill="#8a8173">   \u2014   </tspan>'
                 f'<tspan fill="#c9bfa8">{e(body)}</tspan></text>'
                 f'</g>')
    # act boundaries, so the peaks and holes can be read against the story
    arcs_s = sorted(arcs or [], key=lambda a: a["from"])
    for a in arcs_s[1:]:
        bx = x(a["from"])
        o.append(f'<line x1="{bx:.1f}" y1="0" x2="{bx:.1f}" y2="{H2:.1f}" '
                 f'stroke="#8a8173" stroke-width="1" stroke-dasharray="4,3" '
                 f'opacity=".5"/>')
    for i, a in enumerate(arcs_s, 1):
        x0, x1 = x(a["from"]), x(min(a["to"], last))
        if x1 - x0 > 26:
            o.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{H2 + 27:.1f}" font-size="7.5" '
                     f'fill="#8a8173" text-anchor="middle" '
                     f'font-family="Helvetica Neue,Arial">Act {i}</text>')
    for ep in range(0, last + 1, 100):
        e2 = max(1, ep)
        o.append(f'<text x="{x(e2):.1f}" y="{H2 + 15:.1f}" font-size="9" fill="#a49a89" '
                 f'text-anchor="middle" font-family="Helvetica Neue,Arial">{e2}</text>')
    o.append(f'<text x="{L}" y="{H2 + 72:.1f}" font-size="9" fill="#8a8173" '
             f'font-family="Helvetica Neue,Arial">hover any point for the episode, the '
             f'act, and which questions were live there</text>')
    o.append(f'<text x="{L}" y="{H2 + 84:.1f}" font-size="9" fill="#9a3b28" '
             f'font-family="Helvetica Neue,Arial">red marks along the bottom are '
             f'episodes where nothing at all was live</text>')
    o.append('</svg>')
    return ('<figure style="margin:16px 0 10px"><div style="overflow-x:auto">'
            + "".join(o) + '</div></figure>'), dead_runs(per)


def dead_table(runs):
    if not runs:
        return ('<div class="note">There is no stretch of four or more episodes where '
                'the listener had nothing to wonder about.</div>')
    rows = "".join(
        f'<tr class="flag"><td class="c">{a}\u2013{b}</td><td class="c">{n}</td>'
        f'<td class="bt">Nothing the show had asked was still being raised.</td></tr>'
        for a, b, n in runs)
    return ('<table><thead><tr><th>Episodes</th><th>How many</th>'
            '<th>What was live</th></tr></thead><tbody>' + rows + '</tbody></table>')


def continuity_note(health, code):
    """Neutral sentence about the biggest quiet patch inside one hook."""
    for h in health.get("hooks") or []:
        if h["code"] != code:
            continue
        q = h.get("longest_silence") or 0
        span = h.get("span") or 1
        if q < 25 or q < span * 0.15:
            return ""
        eps = sorted(h.get("touch_eps") or [])
        where = ""
        for a, b in zip(eps, eps[1:]):
            if b - a == q:
                where = f" (roughly episodes {a} to {b})"
                break
        return (f'Its quietest patch runs about {q} episodes{where}. Worth noticing '
                f'rather than worrying about, unless other questions were also quiet '
                f'there.')
    return ""


# ── the hook timeline ────────────────────────────────────────────────────────
V_COL = {"paid": "#3d6b3f", "paid late": "#8a6d21", "deflected": "#9a3b28",
         "offscreen": "#9a3b28", "broken": "#9a3b28", "dangling": "#9a3b28",
         "open at finale": "#9a3b28"}
SEV_BAND = {"severe": "#efd9d4", "marked": "#f3ead0", "mild": "#faf7f0"}


SEV_WORD = {"severe": "severe", "marked": "worth watching", "mild": "mild"}


def band_key(drift):
    """Names every shaded band. Without this the bands are unreadable.

    Numbered left to right, so the key reads 1, 2, 3 down the page and matches the
    order the tabs appear across the chart."""
    ordered = sorted(drift, key=lambda d: d["eps"][0])
    for n, d in enumerate(ordered, start=1):
        d["_n"] = n
    rows = "".join(
        f'<tr style="cursor:pointer">'
        f'<td class="c"><a href="#trouble-{d["_n"]}" style="color:#6b6357;'
        f'text-decoration:none"><b>{d["_n"]}</b></a></td>'
        f'<td class="c"><a href="#trouble-{d["_n"]}" style="color:#3a352e;'
        f'text-decoration:none">{d["eps"][0]}\u2013{d["eps"][1]}</a></td>'
        f'<td class="c"><span class="stw '
        f'{"flag" if d["severity"] == "severe" else "near"}">'
        f'{e(SEV_WORD[d["severity"]])}</span></td>'
        f'<td class="bt"><a href="#trouble-{d["_n"]}" style="color:#3a352e;'
        f'text-decoration:none">{e(d["signal"])}'
        f'<span style="color:#a49a89;font-family:Helvetica Neue,Arial;font-size:10px">'
        f'  \u2192 read the detail</span></a></td></tr>'
        for d in ordered)
    return ('<table style="margin-top:2px"><thead><tr><th></th><th>Episodes</th>'
            '<th>How bad</th><th>What the trouble is</th></tr></thead><tbody>'
            + rows + '</tbody></table>')


def timeline(hooks, drift, last_ep, arcs=None):
    """One row per question, open to close, over the whole run. Drift zones behind.

    Rows run in the order the show asks the questions, matching the H-numbers, so the
    chart reads as a staircase rather than a scramble. The ranked table above is
    sorted by pull; this one is sorted by time, and the codes tie them together."""
    hooks = sorted(hooks, key=lambda h: h["opens"])
    L, R, TOP, ROW = 116, 856, 54, 25
    H = TOP + ROW * len(hooks) + 52
    x = lambda ep: L + (R - L) * (ep - 1) / max(1, last_ep - 1)
    o = [f'<svg viewBox="0 0 900 {H}" width="100%" role="img" '
         f'aria-label="Hook timeline across {last_ep} episodes">']

    # Two separate concerns, previously conflated into one ordering:
    #   numbering  runs left to right, because that is how a reader scans
    #   painting   runs widest first, so a narrow band inside a wide one survives
    for n, d in enumerate(sorted(drift, key=lambda d: d["eps"][0]), start=1):
        d["_n"] = n
    for d in sorted(drift, key=lambda d: -(d["eps"][1] - d["eps"][0])):
        a, b = d["eps"]
        w = max(2, x(b) - x(a))
        o.append(f'<rect x="{x(a):.1f}" y="{TOP - 16}" width="{w:.1f}" '
                 f'height="{ROW * len(hooks) + 18}" fill="{SEV_BAND[d["severity"]]}"/>')
    # numbered tab above each band, staggered on two rows so none collide
    for d in sorted(drift, key=lambda d: d["eps"][0]):
        a, b = d["eps"]
        cx = x(a) + max(2, x(b) - x(a)) / 2
        ty = TOP - 30 if d["_n"] % 2 else TOP - 20
        o.append(f'<a href="#trouble-{d["_n"]}">'
                 f'<circle cx="{cx:.1f}" cy="{ty - 3.5:.1f}" r="6.5" fill="#f4f1ec" '
                 f'stroke="#c9bfa8" stroke-width="1"/>'
                 f'<text x="{cx:.1f}" y="{ty:.1f}" font-size="8" fill="#6b6357" '
                 f'text-anchor="middle" font-family="Helvetica Neue,Arial">'
                 f'{d["_n"]}</text></a>')

    for ep in range(0, last_ep + 1, 100):
        e2 = max(1, ep)
        o.append(f'<line x1="{x(e2):.1f}" y1="{TOP - 12}" x2="{x(e2):.1f}" '
                 f'y2="{TOP + ROW * len(hooks) + 2}" stroke="#e4ddd0" stroke-width="1"/>')
        o.append(f'<text x="{x(e2):.1f}" y="{TOP + ROW * len(hooks) + 17}" font-size="9.5" '
                 f'fill="#a49a89" text-anchor="middle" font-family="Helvetica Neue,Arial">'
                 f'{e2}</text>')

    for i, h in enumerate(hooks):
        y = TOP + i * ROW
        op = h["opens"]
        cl = h.get("resolves") or last_ep
        col = V_COL.get(h["verdict"], "#9a3b28")
        dash = ' stroke-dasharray="3,3"' if not h.get("resolves") else ''
        o.append(f'<text x="{L - 10}" y="{y + 4}" font-size="10.5" fill="#3a352e" '
                 f'text-anchor="end" font-family="Helvetica Neue,Arial" font-weight="700">'
                 f'{h["code"]}</text>')
        o.append(f'<line x1="{x(op):.1f}" y1="{y}" x2="{x(cl):.1f}" y2="{y}" '
                 f'stroke="{col}" stroke-width="7" stroke-linecap="round" opacity=".85"{dash}/>')
        o.append(f'<circle cx="{x(op):.1f}" cy="{y}" r="3.6" fill="{col}"/>')
        if h.get("resolves"):
            o.append(f'<circle cx="{x(cl):.1f}" cy="{y}" r="3.6" fill="#f4f1ec" '
                     f'stroke="{col}" stroke-width="2"/>')
        o.append(f'<text x="{x(op):.1f}" y="{y - 7}" font-size="8.5" fill="#8a8173" '
                 f'font-family="Helvetica Neue,Arial">{op}</text>')

    # arc boundaries, so a hook can be read against the stretch it lives in
    for a in sorted(arcs or [], key=lambda a: a["from"])[1:]:
        bx = x(a["from"])
        o.append(f'<line x1="{bx:.1f}" y1="{TOP - 12}" x2="{bx:.1f}" '
                 f'y2="{TOP + ROW * len(hooks) + 4}" stroke="#8a8173" stroke-width="1" '
                 f'stroke-dasharray="4,3" opacity=".55"/>')
    for a in sorted(arcs or [], key=lambda a: a["from"]):
        x0, x1 = x(a["from"]), x(min(a["to"], last_ep))
        if x1 - x0 > 40:
            o.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{TOP + ROW * len(hooks) + 32}" '
                     f'font-size="8" fill="#8a8173" text-anchor="middle" '
                     f'font-family="Helvetica Neue,Arial">'
                     f'{e(a.get("name", a["id"])[:18])}</text>')
    o.append('</svg>')
    return ('<figure style="margin:18px 0 26px"><div style="overflow-x:auto">'
            + "".join(o) + '</div></figure>')


# ── supplementary: episode-by-episode engagement strips ──────────────────────
def strips(health, top=None):
    """One row per hook, every row on the SAME episode axis so they can be compared
    down the column. Green: the show touched that question in that episode. Grey:
    the question was open and the episode ignored it. Blank: not open yet, or
    already answered."""
    if not health:
        return ""
    hooks = sorted(health.get("hooks") or [], key=lambda h: h["opens"])
    if top:
        hooks = hooks[:top]
    if not hooks:
        return ""
    last = health.get("last_ep") or max(h.get("resolves") or 0 for h in hooks) or 1
    L, W, BH, GAP = 44.0, 812.0, 19.0, 12.0
    x = lambda ep: L + W * (ep - 1) / max(1, last - 1)
    w = max(0.75, W / max(1, last))

    rows, y = [], 0.0
    for h in hooks:
        op = h["opens"]
        cl = h.get("resolves") or last
        hit = set(h.get("touch_eps") or [])
        n = len([e for e in range(op, cl + 1) if e in hit])
        N = cl - op + 1
        # open-but-quiet ground, then a mark for every episode that touches it
        rows.append(f'<rect x="{x(op):.2f}" y="{y:.1f}" width="{max(1, x(cl) - x(op)):.2f}" '
                    f'height="{BH}" fill="#e8e2d6"/>')
        for e in sorted(hit):
            if op <= e <= cl:
                rows.append(f'<rect x="{x(e):.2f}" y="{y:.1f}" '
                            f'width="{max(0.9, w):.2f}" height="{BH}" fill="#3d6b3f"/>')
        rows.append(f'<text x="{L - 7}" y="{y + BH / 2 + 3.5}" font-size="9.5" '
                    f'fill="#3a352e" text-anchor="end" font-weight="700" '
                    f'font-family="Helvetica Neue,Arial">{e_(h["code"])}</text>')
        rows.append(f'<text x="{L + W + 6}" y="{y + BH / 2 + 3.5}" font-size="9" '
                    f'fill="#6b6357" font-family="Helvetica Neue,Arial">'
                    f'{n}/{N}</text>')
        y += BH + GAP

    # one hover column per episode, reporting the state of every question at once
    hits = []
    plot_h = y - GAP
    for ep in range(1, last + 1):
        raised, ignored = [], []
        for h in hooks:
            op = h["opens"]
            cl = h.get("resolves") or last
            if not (op <= ep <= cl):
                continue
            (raised if ep in set(h.get("touch_eps") or []) else ignored).append(h["code"])
        bits = []
        if raised:
            bits.append("raised in " + ", ".join(raised))
        if ignored:
            bits.append("open but ignored in " + ", ".join(ignored))
        body = " \u00b7 ".join(bits) if bits else "no question open yet"
        hits.append(
            f'<g class="ephit">'
            f'<rect class="hit" x="{x(ep):.2f}" y="0" width="{max(w, 1.1):.2f}" '
            f'height="{plot_h:.1f}"/>'
            f'<rect class="lbl" x="{L}" y="{plot_h + 22:.1f}" width="700" height="21" '
            f'rx="4" fill="#1c1a17"/>'
            f'<text x="{L + 11}" y="{plot_h + 37:.1f}" font-size="11.5" '
            f'font-family="Helvetica Neue,Arial">'
            f'<tspan fill="#f4f1ec" font-weight="700">ep {ep}</tspan>'
            f'<tspan fill="#8a8173">   \u2014   </tspan>'
            f'<tspan fill="#c9bfa8">{e_(body)}</tspan></text></g>')

    axis = []
    for ep in range(0, last + 1, 50):
        e2 = max(1, ep)
        axis.append(f'<line x1="{x(e2):.1f}" y1="0" x2="{x(e2):.1f}" y2="{y - GAP:.1f}" '
                    f'stroke="#f4f1ec" stroke-width="1"/>')
    for ep in range(0, last + 1, 100):
        e2 = max(1, ep)
        axis.append(f'<text x="{x(e2):.1f}" y="{y + 4:.1f}" font-size="9" fill="#a49a89" '
                    f'text-anchor="middle" font-family="Helvetica Neue,Arial">{e2}</text>')

    svg = (f'<figure style="margin:14px 0 8px"><div style="overflow-x:auto">'
           f'<svg viewBox="0 0 900 {y + 48:.0f}" width="100%" role="img" '
           f'aria-label="Which episodes touch each question">'
           + "".join(axis) + "".join(rows) + "".join(hits) + '</svg></div></figure>')

    # the reading list underneath, in words
    lines = []
    for h in sorted(hooks, key=lambda h: (len([e for e in h.get("touch_eps") or []
                    if h["opens"] <= e <= (h.get("resolves") or last)])
                    / max(1, (h.get("resolves") or last) - h["opens"] + 1))):
        op = h["opens"]
        cl = h.get("resolves") or last
        N = cl - op + 1
        n = len([e for e in (h.get("touch_eps") or []) if op <= e <= cl])
        pct = 100.0 * n / max(1, N)
        lines.append(
            f'<tr{" class=flag" if pct < 8 else ""}><td class="c"><b>{e_(h["code"])}</b></td>'
            f'<td class="bt">{e_(h["q"])}</td>'
            f'<td class="c">{op}\u2013{cl}</td><td class="c">{N}</td>'
            f'<td class="c"><b>{n}</b></td><td class="c">{pct:.0f} in 100</td>'
            f'<td class="c">{h.get("longest_silence", "")}</td></tr>')
    table = ('<table><thead><tr><th></th><th>The question</th><th>Open across</th>'
             '<th>Episodes it was open</th><th>Episodes that mention it</th>'
             '<th>Rate</th><th>Longest gap</th></tr></thead><tbody>'
             + "".join(lines) + '</tbody></table>')
    return svg + table


def build(title, ledger, health=None, transit=None, arcs_meta=None):
    rng = ledger.get("range", [None, None])
    n = ledger.get("episodes_present", "?")
    meta = (f'{n} episodes · eps {rng[0]}–{rng[1]} · CMS production scripts read in '
            f'full · <b>script only — no retention data</b>')
    # Hidden from the page, kept in the file. CHECKED is the provenance record: what
    # was read, what was inferred. Flip SHOW_CHECKED to put it back on the page.
    SHOW_CHECKED = False
    # Part I's explainer, hidden from the page. The table's hover states carry the
    # same information at the point of use. Flip to put the paragraph back.
    SHOW_PART1_INTRO = False
    part1_intro = '<div class="readnote">Questions are numbered in the order the show asks them, so <b>H1</b> is the first question it plants and <b>H10</b> the last. The table is sorted by <b>pull</b>, a score out of 12 built from four things: how often the show comes back to the question, how concrete it is, whose question it is, and how much changes once it is answered.<br><br><b>Hover any pull score to see how it was scored. Hover any verdict to see why it was given.</b><br><br>How long a question stays open is context, not credit. A question the show leaves open for hundreds of episodes and rarely mentions is a thread let go, not a question holding anyone. Each question then gets its own block below: what the show asks on the left, the verdict on the right.</div>' if SHOW_PART1_INTRO else ""
    checked = "".join(f"<li>{e(c)}</li>" for c in CHECKED)
    checked_block = ("" if not SHOW_CHECKED else
        f'<div class="note"><b>Checked, not assumed</b><ul>{checked}</ul>'
        'Listener attention is <b>inferred from the script</b>. This report measures '
        'what the script asks and whether it answers; it does not measure '
        'engagement.</div>')
    cast_block = ("" if not CAST else
        '<div class="sec"><div class="secn">Who you need to know</div></div>'
        + "".join(f'<div class="castrow"><div class="castname">{e(n)}</div>'
                  f'<div class="castbio">{e(b)}</div></div>' for n, b in CAST))
    cov_chart, dead = (coverage_chart(health, (transit or {}).get('arcs'))
                       if health else ("", []))

    # Number the trouble spots and the breaks once, here, so every section that
    # references them agrees. They used to be numbered inside whichever renderer ran
    # first, which made the labels depend on page order.
    for n, d in enumerate(sorted(DRIFT, key=lambda d: d["eps"][0]), start=1):
        d["_n"] = n
    for n, b in enumerate(BREAKS, start=1):
        b["_n"] = n

    promise = (arcs_meta or {}).get("promise", "")

    # Part IV (the arc grid and the crossings table) is switched off: everything it
    # showed now appears inside the acts, where it has context. Flip to re-enable.
    SHOW_PART_IV = False
    arc_section = ""

    act_section = ""
    if transit and health:
        act_section = (
            '<div class="rule"></div>'
            '<div class="part">Part II \u00b7 The story, act by act</div>'
            '<div class="readnote">This is the show itself, in order, one act at a '
            'time. Each act opens with what happens in the story. Under that, what '
            'the analysis found there: the questions the act planted, answered, kept '
            'working or ignored, any promise it breaks, and any stretch of trouble '
            'that overlaps it.<br><br>'
            'Every other part of this report is a different view of what is in '
            'here.</div>'
            + act_blocks(sorted(transit["arcs"], key=lambda a: a["from"]),
                         HOOKS, health, transit.get("last_ep") or 665, ACT_STORIES,
                         BREAKS, DRIFT))

    sv = strips(health)
    strips_section = ("" if not sv else
        '<div class="sec"><div class="secn">Across the whole show: which episodes '
        'actually raised each question</div></div>'
        '<div class="readnote">'
        'A question can stay unanswered for hundreds of episodes while the show barely '
        'mentions it. Being unanswered is not the same as being alive.<br><br>'
        'Each row below is one question. Every row uses the same episode scale, so you '
        'can read straight down a column and see how many questions were live at any '
        'point in the show.<br><br>'
        '<b>Green</b> means that episode did something with the question. '
        '<b>Grey</b> means the question was hanging and that episode ignored it. '
        '<b>Blank</b> means the question had not been asked yet, or was already '
        'answered. The number on the right is how many episodes touched it, out of how '
        'many it was open for.</div>' + sv)

    return f"""<!doctype html>
<meta charset="utf-8">
<title>{e(title)} — Creative audit</title>
<link rel="stylesheet" href="house.css">
<style>{TIP_CSS}</style>
<div class="wrap">

<div class="eyebrow">Creative audit · opening promises</div>
<h1>{e(title)}</h1>
<div class="sub">{e(SUBTITLE)}</div>
<div class="meta">{meta}</div>
<div class="rule"></div>

<div class="logline">{e(LOGLINE.strip())}</div>

<div class="sec"><div class="secn">What the show promises</div></div>
<div class="lead">{LEAD.strip()}</div>

{cast_block}
{checked_block}

<div class="part">Part I · The questions that hold the show up</div>
{part1_intro}
{ranked_table(HOOKS, health)}

{act_section}

<div class="sec"><div class="secn">Across the whole show: every question, start to finish</div></div>
<div class="readnote">Having read the acts, this is every question at once. Each bar is one question. It starts where the show first asks
it and ends where the show answers it. <b>Green</b> means the answer happens on
screen. <b>Amber</b> means it arrives very late. <b>Red</b> means the question was
dodged, answered off screen, or never answered at all.<br><br>
The shaded strips behind the bars are stretches where something is going wrong.
<b>Pink is worse than amber.</b> Each one is numbered and named in the key below the
chart, and explained in full in Part IV.<br><br>
A bar only shows that a question was unanswered, not that the show was doing anything
with it. The chart after this one shows that.</div>
{timeline(HOOKS, DRIFT, rng[1] or 665, (transit or {}).get('arcs'))}
{band_key(DRIFT)}

<div class="sec"><div class="secn">Across the whole show: how many questions were live at once</div></div>
<div class="readnote">Having read the acts, this is all of them at once. It does not
matter when a question starts. A question that opens at episode 155 is not late if
others were carrying the show until then. What matters is whether the listener, at
any given episode, had something to wonder about.<br><br>
A question counts as live only if the show actually raised it in the last
{LIVE_WINDOW} episodes. One nobody has mentioned for fifty episodes is still
unanswered, but it is not holding anyone.</div>
{cov_chart}
{dead_table(dead)}

{strips_section}


<div class="part">Part III · Resolutions and broken promises</div>
<div class="sec"><div class="secn">How each hook closes</div></div>
{resolutions_table(HOOKS)}
<div class="sec"><div class="secn">Broken promises</div></div>
<div class="readnote">Each break is quoted twice — the line that makes the promise,
and the line that withdraws it. <b>B1</b> retcon · <b>B2</b> offscreen close ·
<b>B3</b> deflation · <b>B4</b> substitution · <b>B5</b> drop · <b>B6</b> deferred
past use.</div>
{breaks_section(BREAKS, (transit or {}).get('arcs'))}

<div class="part">Part IV · Where the show loses people</div>
<div class="readnote"><b>D1</b> promise vacuum · <b>D2</b> lead stops driving ·
<b>D3</b> cast bloat or untrackable names · <b>D4</b> repetition and stall ·
<b>D5</b> pacing · <b>D6</b> other, mechanism named. Severity is the softest claim
on this page: it is judgment from the script, not measurement.</div>
{drift_section(DRIFT, (transit or {}).get('arcs'))}

<div class="part">The cliffhanger ledger</div>
<div class="readnote">The receipts. One row for every episode that carries weight — a
hook opening or closing, a promise breaking, a drift zone starting or ending. Every
claim above has a row here.</div>
{ledger_table(LEDGER)}

{arc_section}

<div class="rule"></div>
<div class="note"><b>Limits.</b> The script is evidence; listener attention is
inferred. Pull scores are a rubric applied by judgment — the axis breakdown is shown
so you can disagree with a number rather than the conclusion. No retention data was
used anywhere in this report.</div>

</div>
"""


def validate(doc):
    bad = []
    try:
        HTMLParser().feed(doc)
    except Exception as ex:
        bad.append(f'HTML does not parse: {ex}')
    amp = re.findall(r'&(?!amp;|lt;|gt;|quot;|#\d+;|nbsp;|#x[0-9a-fA-F]+;)', doc)
    if amp:
        bad.append(f'{len(amp)} unescaped & — escape to &amp;')
    if 'class="aud' in doc:
        for m in re.finditer(r'<div class="act-body">(.*?)</section>', doc, re.S):
            if '<aside' not in m.group(1):
                bad.append('an <aside> is outside .act-body — the grid will collapse')
                break
    if '<script' in doc.lower():
        bad.append('JavaScript present — this format is static HTML only')
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ledger', required=True)
    ap.add_argument('--title', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--health', help='health.json from hook_health.py; adds the '
                                     'supplementary per-episode strips at the end')
    ap.add_argument('--transit', help='transit.json from arc_transit.py; adds Part IV, '
                                      'the four-layer arc view')
    ap.add_argument('--arcs', help='arcs.json, for the promise text on the chart')
    a = ap.parse_args()

    ledger = json.loads(pathlib.Path(a.ledger).read_text())
    health = json.loads(pathlib.Path(a.health).read_text()) if a.health else None
    transit = json.loads(pathlib.Path(a.transit).read_text()) if a.transit else None
    arcs_meta = json.loads(pathlib.Path(a.arcs).read_text()) if a.arcs else None
    doc = build(a.title, ledger, health, transit, arcs_meta)
    bad = validate(doc)

    out = pathlib.Path(a.out)
    out.write_text(doc, encoding='utf-8')
    css = out.parent / 'house.css'
    if not css.exists():
        src = pathlib.Path(__file__).resolve().parent.parent / 'assets' / 'house.css'
        if src.exists():
            css.write_text(src.read_text())
            print(f'copied house.css -> {css}')

    print(f'wrote {out}  ({len(doc):,} bytes)')
    print(f'  hooks {len(HOOKS)} · breaks {len(BREAKS)} · drift zones {len(DRIFT)} '
          f'· ledger rows {len(LEDGER)}'
          + (f' · arcs {len(transit["arcs"])}' if transit else ''))
    if bad:
        print('\nVALIDATION FAILED:')
        for b in bad:
            print(f'  {b}')
        sys.exit(1)
    print('  validation passed')
    print(f'\nNow open it and LOOK at it:  open {out}')
    print('  Widen the window past 900px first — house.css collapses to one\n'
          '  column at <=820px by design — then in the console .act-body\n'
          '  gridTemplateColumns must return TWO values, e.g. 512px 300px.')


if __name__ == '__main__':
    main()

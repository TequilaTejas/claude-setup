#!/usr/bin/env python3
"""Render the validation document: creative findings tested against listener data.

    python build_validation.py --claims claims.json --verdicts verdicts.json \
        --data data.json --reads comment_reads/ --notes notes.json \
        --title "Show Name" --out validation.html

Everything numeric comes from verdicts.json and data.json. Everything authored comes
from notes.json, so the same toolkit renders any show. Static HTML, no JavaScript;
hover readouts are CSS-only and every chart carries per-episode targets.
"""
import argparse, html, json, pathlib, re
from collections import Counter

e = html.escape

VERDICT_CLASS = {'CONFIRMED': 'flag', 'MISSED': 'flag', 'CONTESTED': 'near',
                 'NOT CREATIVE': 'near', 'NO COST': 'hold'}
VERDICT_COLOR = {'CONFIRMED': '#9a3b28', 'MISSED': '#7a2d5a',
                 'CONTESTED': '#b07d2b', 'NOT CREATIVE': '#5a6b7a',
                 'NO COST': '#3d6b3f'}
KIND_LABEL = {'trouble': 'Drift zone', 'break': 'Broken promise',
              'hook_close': 'Hook close', 'missed': 'Data-first'}
MOOD_COLOR = {'delight': '#3d6b3f', 'complaint': '#9a3b28', 'confusion': '#b07d2b',
              'production': '#5a6b7a', 'money': '#7a2d5a'}

MARK_CSS = """
/* ---- TEMPORARY review overlay: --mark-data only. Shows which parts of this
   document the data added, so the extended report can be skimmed against the
   Creative Audit it grew from. Delete this block and the flag when done. ---- */
.dnew{position:relative;background:rgba(58,110,165,.13);
  box-shadow:inset 0 0 0 2px rgba(58,110,165,.75);border-radius:4px;
  padding:14px 15px 15px;margin:22px 0}
.dnew::before{content:"ADDED BY THE DATA";position:absolute;top:-10px;left:14px;
  background:#3a6ea5;color:#fff;font-family:Helvetica Neue,Arial;font-size:9px;
  font-weight:700;letter-spacing:.13em;padding:3px 9px 2px;border-radius:3px;
  box-shadow:0 1px 3px rgba(0,0,0,.18)}
.dnew .part{margin-top:4px}
.dnew .dnew{background:none;box-shadow:none;padding:0;margin:14px 0}
.dnew .dnew::before{display:none}
.dkey{position:sticky;top:0;z-index:50;background:#1c1a17;color:#f4f1ec;
  font-family:Helvetica Neue,Arial;font-size:11.5px;padding:9px 16px;
  margin:0 0 4px;line-height:1.5}
.dkey b{color:#9dc0e8}

/* ---- act section v2: cards, tags, hook tags ---- */
.pcard{border:1px solid #ddd5c6;border-radius:5px;margin:9px 0;background:#fbf9f5;
  overflow:hidden}
.pcard[open]{background:#fff;border-color:#cdc5b6}
.pcard>summary{list-style:none;cursor:pointer;padding:10px 13px;display:flex;
  gap:9px;align-items:center;flex-wrap:wrap}
.pcard>summary::-webkit-details-marker{display:none}
.pcard>summary::before{content:"\25B8";color:#a49a89;font-size:11px;flex:none}
.pcard[open]>summary::before{content:"\25BE"}
.pc-title{font-size:14px;font-weight:600;color:#2a2620;flex:1;min-width:180px;
  line-height:1.35}
.pc-tags{display:flex;gap:5px;flex-wrap:wrap}
.pc-meta{font-size:10.5px;color:#a49a89;letter-spacing:.04em;white-space:nowrap;
  font-family:Helvetica Neue,Arial;width:100%;padding-left:19px}
.pc-body{padding:2px 14px 14px 32px;border-top:1px solid #ece5d8}
.pc-h{font-family:Helvetica Neue,Arial;font-size:9.5px;letter-spacing:.1em;
  text-transform:uppercase;color:#8a8173;font-weight:700;margin:12px 0 3px}
.vtag{font-family:Helvetica Neue,Arial;font-size:9.5px;font-weight:700;
  letter-spacing:.06em;text-transform:uppercase;padding:3px 8px 2px;border-radius:3px;
  white-space:nowrap}
.htags{display:flex;gap:6px;flex-wrap:wrap}
.htag{font-size:11.5px;line-height:1.4;padding:4px 10px;border-radius:12px;
  max-width:100%}
.htag b{font-family:Helvetica Neue,Arial;font-size:10px;letter-spacing:.06em;
  margin-right:4px}
.chips{display:flex;gap:5px;flex-wrap:wrap;margin:7px 0 0}
.chip{font-family:Helvetica Neue,Arial;font-size:10.5px;padding:2px 8px;
  border-radius:10px;background:#ece5d8;color:#5a5347;white-space:nowrap}
.chip.warn{background:#f3e0d9;color:#8a3a24}
.chip.ok{background:#e2ebe1;color:#2f5a32}
.dfsub{font-size:11.5px;color:#8a8173;line-height:1.5;
  font-family:Helvetica Neue,Arial}
.dfcap{font-size:13px;line-height:1.55;color:#4a4438;margin:4px 0 0}
.dfstat{font-variant-numeric:tabular-nums}
"""

_EVENTS = {}
_EPREADS = {}
_SENT = {}

# Front-end switch only. The content-first panel is still computed, its numbers still
# feed the acts table and every verdict section below, and nothing leaves the JSON.
# Flip to True to put the per-act panel back on the page.
SHOW_CONTENT_FIRST = False

TIP_CSS = """
/* ---- validation overrides. house.css is used verbatim; this is additive. ---- */
.wrap{max-width:1180px}
.vtab{width:100%;border-collapse:collapse;font-size:13.5px;margin:14px 0 6px}
.vtab th{text-align:left;font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;
  color:#8a8173;border-bottom:1px solid #d9d0c0;padding:7px 9px 6px;font-weight:600}
.vtab td{padding:8px 9px;border-bottom:1px solid #ece5d8;vertical-align:top}
.vtab tr.flag td{background:#fbf2ef}
.vtab tr.near td{background:#fbf7ec}
.vtab tr.hold td{background:#f3f6f1}
.vtab td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;
  font-family:Helvetica Neue,Arial}
.vb{display:inline-block;font-size:9.5px;letter-spacing:.07em;text-transform:uppercase;
  font-weight:700;padding:2px 7px 1px;border-radius:3px;color:#fff;white-space:nowrap;
  font-family:Helvetica Neue,Arial}
.vb.CONFIRMED{background:#9a3b28}.vb.MISSED{background:#7a2d5a}
.vb.CONTESTED{background:#b07d2b}.vb.NOCOST{background:#3d6b3f}
.vb.NOTCREATIVE{background:#5a6b7a}
/* Per-episode hover readout. Scope fills to the hit rect only: targeting bare
   `rect` wiped the readout's own dark background and made it unreadable. */
.ephit .hit{fill:transparent}
.ephit:hover .hit{fill:#1c1a17;fill-opacity:.08}
.ephit .lbl,.ephit text{opacity:0;pointer-events:none}
.ephit:hover .lbl,.ephit:hover text{opacity:1}
.chartnote{font-size:11.5px;color:#8a8173;margin:2px 0 18px;line-height:1.5}
.q{margin:9px 0;padding:8px 0 8px 13px;border-left:2px solid #d9d0c0;font-size:13px;
  line-height:1.55;color:#3a342c}
.q cite{display:block;font-style:normal;font-size:10.5px;color:#8a8173;margin-top:4px;
  letter-spacing:.04em}
.sol{border:1px solid #d9d0c0;border-radius:5px;padding:0;margin:16px 0;overflow:hidden}
.sol-h{background:#f3eee4;padding:10px 15px;border-bottom:1px solid #d9d0c0;
  display:flex;gap:11px;align-items:baseline;flex-wrap:wrap}
.sol-n{font-family:Helvetica Neue,Arial;font-size:10.5px;font-weight:700;
  letter-spacing:.1em;color:#8a8173}
.sol-h h4{margin:0;font-size:16.5px;font-weight:600;flex:1;min-width:260px}
.sol-b{padding:13px 15px 15px}
.sol-b dl{margin:0;display:grid;grid-template-columns:108px 1fr;gap:7px 16px;
  font-size:13px;line-height:1.58}
.sol-b dt{font-size:10px;letter-spacing:.09em;text-transform:uppercase;color:#8a8173;
  font-weight:600;font-family:Helvetica Neue,Arial;padding-top:3px}
.sol-b dd{margin:0}
@media (max-width:700px){.sol-b dl{grid-template-columns:1fr;gap:2px 0}
  .sol-b dt{padding-top:9px}}
.kv{display:flex;gap:26px;flex-wrap:wrap;margin:10px 0 4px}
.kv div{min-width:96px}
.kv b{display:block;font-family:Helvetica Neue,Arial;font-size:23px;font-weight:600;
  line-height:1.15;font-variant-numeric:tabular-nums}
.kv span{font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;color:#8a8173}
"""



def cost(f):
    """The cost of a finding, in listeners, taken from the LEVEL series.

    `excess_listeners` is the old rate-derived figure and is kept in the JSON for
    comparison only. It compounds a drop rate against a headcount, which inflates the
    answer, so nothing on the page may use it. Negative means the stretch held better
    than the show's own baseline predicts."""
    v = f.get('level_excess')
    return 0 if v is None else v


def fmt(n):
    return f'{n:,.0f}'


def ratio(r):
    return f'{r:.2f}×'


# ---------------------------------------------------------------- charts

def bleed_map(sweep, findings, last_ep):
    """Excess listeners lost per 10-episode block, with each creative zone marked
    underneath. This is the chart that answers 'where does the show actually leak'."""
    if not sweep:
        return ''
    L, W, H = 52.0, 800.0, 150.0
    blocks = sorted(sweep, key=lambda s: s['episodes'][0])
    top = max(1.0, max(abs(cost(b)) for b in blocks))
    bw = W / len(blocks)
    x = lambda i: L + bw * i
    o = [f'<svg viewBox="0 0 900 {H + 150:.0f}" width="100%" role="img" '
         f'aria-label="Listeners lost above baseline, per ten episodes">']
    for frac in (0, .25, .5, .75, 1.0):
        gy = H - H * frac
        o.append(f'<line x1="{L}" y1="{gy:.1f}" x2="{L + W}" y2="{gy:.1f}" '
                 f'stroke="#e4ddd0" stroke-width="1"/>')
        o.append(f'<text x="{L - 7}" y="{gy + 3.5:.1f}" font-size="9" fill="#a49a89" '
                 f'text-anchor="end" font-family="Helvetica Neue,Arial">'
                 f'{fmt(top * frac)}</text>')
    # which verdict, if any, covers each block
    cover = {}
    for f in findings:
        for i, b in enumerate(blocks):
            if b['episodes'][0] <= f['to'] and f['from'] <= b['episodes'][1]:
                cur = cover.get(i)
                rank = {'MISSED': 4, 'CONFIRMED': 3, 'NOT CREATIVE': 2,
                        'CONTESTED': 1, 'NO COST': 0}
                if cur is None or rank[f['verdict']] > rank[cur[0]]:
                    cover[i] = (f['verdict'], f['label'])
    for i, b in enumerate(blocks):
        h = H * abs(cost(b)) / top
        v = cover.get(i)
        col = VERDICT_COLOR[v[0]] if v else '#c3bbac'
        o.append(f'<rect x="{x(i) + .7:.2f}" y="{H - h:.1f}" '
                 f'width="{bw - 1.4:.2f}" height="{max(h, .8):.1f}" fill="{col}" '
                 f'opacity=".84"/>')
    for i, b in enumerate(blocks):
        lo, hi = b['episodes']
        v = cover.get(i)
        head = f'eps {lo}–{hi}'
        body = (f'{fmt(cost(b))} listeners vs baseline  ·  '
                f'{ratio(b["vs_show"])} the show’s own rate  ·  '
                f'{ratio(b["vs_benchmark"])} benchmark  ·  '
                f'{b["comments"]} comments')
        tail = f'   —   {v[0]}: {v[1]}' if v else '   —   no creative finding here'
        o.append(f'<g class="ephit">'
                 f'<rect class="hit" x="{x(i):.2f}" y="0" width="{bw:.2f}" '
                 f'height="{H:.1f}"/>'
                 f'<rect class="lbl" x="{L}" y="{H + 30:.1f}" width="812" height="38" '
                 f'rx="4" fill="#1c1a17"/>'
                 f'<text x="{L + 11}" y="{H + 45:.1f}" font-size="11.5" '
                 f'font-family="Helvetica Neue,Arial">'
                 f'<tspan fill="#f4f1ec" font-weight="700">{e(head)}</tspan>'
                 f'<tspan fill="#c9bfa8">{e(tail)}</tspan></text>'
                 f'<text x="{L + 11}" y="{H + 60:.1f}" font-size="11" '
                 f'fill="#8a8173" font-family="Helvetica Neue,Arial">{e(body)}</text>'
                 f'</g>')
    for i, b in enumerate(blocks):
        if i % 5 == 0:
            o.append(f'<text x="{x(i) + bw / 2:.1f}" y="{H + 16:.1f}" font-size="9" '
                     f'fill="#a49a89" text-anchor="middle" '
                     f'font-family="Helvetica Neue,Arial">{b["episodes"][0]}</text>')
    # legend
    ly = H + 86
    lx = L
    for v in ('MISSED', 'CONFIRMED', 'NOT CREATIVE', 'CONTESTED', 'NO COST'):
        if not any(c[0] == v for c in cover.values()):
            continue
        o.append(f'<rect x="{lx:.0f}" y="{ly - 8:.0f}" width="9" height="9" '
                 f'fill="{VERDICT_COLOR[v]}"/>')
        o.append(f'<text x="{lx + 14:.0f}" y="{ly:.0f}" font-size="10" fill="#6b6354" '
                 f'font-family="Helvetica Neue,Arial">{v}</text>')
        lx += 26 + 7.0 * len(v)
    o.append(f'<rect x="{lx:.0f}" y="{ly - 8:.0f}" width="9" height="9" fill="#c3bbac"/>')
    o.append(f'<text x="{lx + 14:.0f}" y="{ly:.0f}" font-size="10" fill="#6b6354" '
             f'font-family="Helvetica Neue,Arial">no finding</text>')
    o.append('</svg>')
    return ('<figure style="margin:16px 0 4px"><div style="overflow-x:auto">'
            + ''.join(o) + '</div></figure>')


def curve(eps, bench, zones, last_ep):
    """Per-episode drop rate against the benchmark, zones shaded. Hover gives the
    exact episode number, which is the whole reason this chart exists."""
    L, W, H = 52.0, 800.0, 128.0
    series = [(int(k), v) for k, v in sorted(eps.items(), key=lambda kv: int(kv[0]))]
    series = [(ep, d) for ep, d in series if ep >= 2]
    if not series:
        return ''
    vals = [abs(d['drop']) for _, d in series if d.get('drop') is not None]
    top = max(.02, sorted(vals)[int(len(vals) * .995)])
    x = lambda ep: L + W * (ep - 1) / max(1, last_ep - 1)
    y = lambda v: H - H * min(abs(v), top) / top
    o = [f'<svg viewBox="0 0 900 {H + 120:.0f}" width="100%" role="img" '
         f'aria-label="Episode-over-episode drop rate against the benchmark">']
    for frac in (0, .5, 1.0):
        gy = H - H * frac
        o.append(f'<line x1="{L}" y1="{gy:.1f}" x2="{L + W}" y2="{gy:.1f}" '
                 f'stroke="#e4ddd0" stroke-width="1"/>')
        o.append(f'<text x="{L - 7}" y="{gy + 3.5:.1f}" font-size="9" fill="#a49a89" '
                 f'text-anchor="end" font-family="Helvetica Neue,Arial">'
                 f'{top * frac * 100:.0f}%</text>')
    for z in zones:
        x0, x1 = x(max(z['from'], 1)), x(min(z['to'], last_ep))
        o.append(f'<rect x="{x0:.1f}" y="0" width="{max(x1 - x0, 1):.1f}" '
                 f'height="{H:.1f}" fill="{VERDICT_COLOR[z["verdict"]]}" '
                 f'opacity=".10"/>')
    bpts = [f'{x(ep):.1f},{y(bench.get(str(ep)) or 0):.1f}' for ep, _ in series
            if bench.get(str(ep)) is not None]
    if bpts:
        o.append(f'<polyline points="{" ".join(bpts)}" fill="none" stroke="#a49a89" '
                 f'stroke-width="1" stroke-dasharray="3,3"/>')
    pts = [f'{x(ep):.1f},{y(d["drop"] or 0):.1f}' for ep, d in series]
    o.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#1c1a17" '
             f'stroke-width="1.1" opacity=".8"/>')
    zone_of = {}
    for z in zones:
        for ep in range(z['from'], z['to'] + 1):
            zone_of.setdefault(ep, z)
    w = max(.9, W / last_ep)
    for ep, d in series:
        b = bench.get(str(ep))
        z = zone_of.get(ep)
        head = f'ep {ep}'
        body = (f'{abs(d["drop"] or 0) * 100:.1f}% drop'
                + (f'  ·  benchmark {abs(b) * 100:.1f}%' if b is not None else '')
                + (f'  ·  {fmt(d["listen"])} listeners'
                   if d.get('listen') else '')
                + (f'  ·  {d["title"]}' if d.get('title') else ''))
        tail = f'   —   {z["verdict"]}: {z["label"]}' if z else ''
        o.append(f'<g class="ephit">'
                 f'<rect class="hit" x="{x(ep) - w / 2:.2f}" y="0" '
                 f'width="{w:.2f}" height="{H:.1f}"/>'
                 f'<rect class="lbl" x="{L}" y="{H + 26:.1f}" width="812" height="38" '
                 f'rx="4" fill="#1c1a17"/>'
                 f'<text x="{L + 11}" y="{H + 41:.1f}" font-size="11.5" '
                 f'font-family="Helvetica Neue,Arial">'
                 f'<tspan fill="#f4f1ec" font-weight="700">{e(head)}</tspan>'
                 f'<tspan fill="#c9bfa8">{e(tail)}</tspan></text>'
                 f'<text x="{L + 11}" y="{H + 56:.1f}" font-size="11" fill="#8a8173" '
                 f'font-family="Helvetica Neue,Arial">{e(body)}</text></g>')
    for ep in range(1, last_ep + 1, 50):
        o.append(f'<text x="{x(ep):.1f}" y="{H + 15:.1f}" font-size="9" '
                 f'fill="#a49a89" text-anchor="middle" '
                 f'font-family="Helvetica Neue,Arial">{ep}</text>')
    o.append(f'<text x="{L}" y="{H + 86:.0f}" font-size="10" fill="#6b6354" '
             f'font-family="Helvetica Neue,Arial">solid: this show  ·  '
             f'dashed: benchmark, matched on cumulative hours  ·  '
             f'shaded: a creative finding, tinted by verdict</text>')
    o.append('</svg>')
    return ('<figure style="margin:16px 0 4px"><div style="overflow-x:auto">'
            + ''.join(o) + '</div></figure>')


def completion(eps, zones, last_ep):
    """Share of listeners who reach 90% of the episode. Drop rate sees people who do
    not come back; this sees people who stop partway through and never say so. A
    stretch can hold its audience episode to episode and still be losing them inside
    each one, and nothing else on this page would show that."""
    series = [(int(k), v) for k, v in sorted(eps.items(), key=lambda kv: int(kv[0]))
              if v.get('c90') is not None]
    if len(series) < 20:
        return ''
    L, W, H = 52.0, 800.0, 120.0
    lo = min(v['c90'] for _, v in series)
    hi = max(v['c90'] for _, v in series)
    pad = max(.02, (hi - lo) * .08)
    lo, hi = max(0.0, lo - pad), min(1.0, hi + pad)
    x = lambda ep: L + W * (ep - 1) / max(1, last_ep - 1)
    y = lambda c: H - H * (c - lo) / max(1e-9, hi - lo)
    o = [f'<svg viewBox="0 0 900 {H + 104:.0f}" width="100%" role="img" '
         f'aria-label="Share of listeners finishing each episode">']
    for frac in (0, .5, 1.0):
        c = lo + (hi - lo) * frac
        gy = y(c)
        o.append(f'<line x1="{L}" y1="{gy:.1f}" x2="{L + W}" y2="{gy:.1f}" '
                 f'stroke="#e4ddd0" stroke-width="1"/>')
        o.append(f'<text x="{L - 7}" y="{gy + 3.5:.1f}" font-size="9" fill="#a49a89" '
                 f'text-anchor="end" font-family="Helvetica Neue,Arial">'
                 f'{c * 100:.0f}%</text>')
    for z in zones:
        x0, x1 = x(max(z['from'], 1)), x(min(z['to'], last_ep))
        o.append(f'<rect x="{x0:.1f}" y="0" width="{max(x1 - x0, 1):.1f}" '
                 f'height="{H:.1f}" fill="{VERDICT_COLOR[z["verdict"]]}" '
                 f'opacity=".10"/>')
    # 20-episode rolling mean, so the trend is readable under the per-episode noise
    win = 20
    roll = []
    for i, (ep, _) in enumerate(series):
        seg = [v['c90'] for _, v in series[max(0, i - win // 2):i + win // 2 + 1]]
        roll.append(f'{x(ep):.1f},{y(sum(seg) / len(seg)):.1f}')
    # Build the point list outside the f-string: 3.9 cannot reuse the same quote
    # character inside a nested f-string expression.
    raw = ' '.join(f'{x(ep):.1f},{y(v["c90"]):.1f}' for ep, v in series)
    o.append(f'<polyline points="{raw}" fill="none" stroke="#1c1a17" '
             f'stroke-width=".8" opacity=".28"/>')
    o.append(f'<polyline points="{" ".join(roll)}" fill="none" stroke="#3d6b3f" '
             f'stroke-width="1.8"/>')
    zone_of = {}
    for z in zones:
        for ep in range(z['from'], z['to'] + 1):
            zone_of.setdefault(ep, z)
    w = max(.9, W / last_ep)
    for ep, v in series:
        z = zone_of.get(ep)
        body = (f'{v["c90"] * 100:.1f}% finish the episode'
                + (f'  ·  {v["c50"] * 100:.1f}% reach halfway'
                   if v.get('c50') is not None else '')
                + (f'  ·  {v["dur"] * 60:.0f} min' if v.get('dur') else '')
                + (f'  ·  {v["title"]}' if v.get('title') else ''))
        tail = f'   —   {z["verdict"]}: {z["label"]}' if z else ''
        o.append(f'<g class="ephit">'
                 f'<rect class="hit" x="{x(ep) - w / 2:.2f}" y="0" width="{w:.2f}" '
                 f'height="{H:.1f}"/>'
                 f'<rect class="lbl" x="{L}" y="{H + 24:.1f}" width="812" height="38" '
                 f'rx="4" fill="#1c1a17"/>'
                 f'<text x="{L + 11}" y="{H + 39:.1f}" font-size="11.5" '
                 f'font-family="Helvetica Neue,Arial">'
                 f'<tspan fill="#f4f1ec" font-weight="700">ep {ep}</tspan>'
                 f'<tspan fill="#c9bfa8">{e(tail)}</tspan></text>'
                 f'<text x="{L + 11}" y="{H + 54:.1f}" font-size="11" fill="#8a8173" '
                 f'font-family="Helvetica Neue,Arial">{e(body)}</text></g>')
    for ep in range(1, last_ep + 1, 50):
        o.append(f'<text x="{x(ep):.1f}" y="{H + 15:.1f}" font-size="9" fill="#a49a89" '
                 f'text-anchor="middle" font-family="Helvetica Neue,Arial">{ep}</text>')
    o.append(f'<text x="{L}" y="{H + 84:.0f}" font-size="10" fill="#6b6354" '
             f'font-family="Helvetica Neue,Arial">faint: each episode  ·  '
             f'green: 20-episode rolling mean  ·  '
             f'shaded: a creative finding, tinted by verdict</text>')
    o.append('</svg>')
    return ('<figure style="margin:16px 0 4px"><div style="overflow-x:auto">'
            + ''.join(o) + '</div></figure>')


def verdict_bars(findings, th):
    """Every finding as a bar: how much faster listeners left inside it than the show's
    own baseline. Threshold lines are drawn, so a reader can see how close a call was.
    Bar length is true proportion of the axis — never multiplied, never clamped."""
    if not findings:
        return ''
    rows = sorted(findings, key=lambda f: -f['vs_show'])
    L, W = 270.0, 500.0
    rh, gap = 21.0, 4.0
    top = max(1.45, max(f['vs_show'] for f in rows) * 1.04)
    H = len(rows) * (rh + gap) + 34
    x = lambda r: L + W * r / top
    o = [f'<svg viewBox="0 0 900 {H + 74:.0f}" width="100%" role="img" '
         f'aria-label="How fast listeners left inside each creative finding">']
    for t in (1.0, th['confirm'], th['miss']):
        o.append(f'<line x1="{x(t):.1f}" y1="10" x2="{x(t):.1f}" y2="{H - 24:.1f}" '
                 f'stroke="#8a8173" stroke-width="1" '
                 f'stroke-dasharray="{"" if t == 1.0 else "4,3"}" opacity=".55"/>')
        lab = ('baseline' if t == 1.0 else
               f'confirm {t:g}×' if t == th['confirm'] else f'miss {t:g}×')
        o.append(f'<text x="{x(t):.1f}" y="{H - 12:.1f}" font-size="9.5" '
                 f'fill="#8a8173" text-anchor="middle" '
                 f'font-family="Helvetica Neue,Arial">{lab}</text>')
    for i, f in enumerate(rows):
        yy = 10 + i * (rh + gap)
        bw = max(x(f['vs_show']) - L, 1.0)
        o.append(f'<rect x="{L}" y="{yy:.1f}" width="{bw:.1f}" height="{rh:.1f}" '
                 f'fill="{VERDICT_COLOR[f["verdict"]]}" opacity=".82"/>')
        lbl = f['label'] if len(f['label']) <= 40 else f['label'][:38] + '…'
        o.append(f'<text x="{L - 9}" y="{yy + rh / 2 + 3.8:.1f}" font-size="11" '
                 f'fill="#3a342c" text-anchor="end" '
                 f'font-family="Helvetica Neue,Arial">{e(lbl)}</text>')
        o.append(f'<text x="{L + bw + 7:.1f}" y="{yy + rh / 2 + 3.8:.1f}" '
                 f'font-size="10.5" fill="#6b6354" '
                 f'font-family="Helvetica Neue,Arial">{ratio(f["vs_show"])}  '
                 f'{fmt(cost(f))} lost</text>')
        o.append(f'<title>{e(f["label"])} — eps {f["from"]}–{f["to"]}, '
                 f'{ratio(f["vs_show"])} the show’s own drop rate, '
                 f'{fmt(cost(f))} listeners above baseline, '
                 f'{f["verdict"]}</title>')
    o.append('</svg>')
    return ('<figure style="margin:16px 0 4px"><div style="overflow-x:auto">'
            + ''.join(o) + '</div></figure>')


def mood_chart(reads):
    """One stacked bar per comment window: what listeners in that stretch were doing.
    Bars are normalised to the busiest window so volume stays visible."""
    reads = [r for r in reads if r.get('mood')]
    if not reads:
        return ''
    reads = sorted(reads, key=lambda r: r['window'][0])
    kinds = ['delight', 'complaint', 'confusion', 'production', 'money']
    L, W, H = 52.0, 790.0, 140.0
    top = max(1, max(sum(r['mood'].get(k, 0) for k in kinds) for r in reads))
    bw = min(72.0, W / len(reads) - 16)
    step = W / len(reads)
    o = [f'<svg viewBox="0 0 900 {H + 104:.0f}" width="100%" role="img" '
         f'aria-label="What listeners are doing in each window">']
    for frac in (0, .5, 1.0):
        gy = H - H * frac
        o.append(f'<line x1="{L}" y1="{gy:.1f}" x2="{L + W}" y2="{gy:.1f}" '
                 f'stroke="#e4ddd0" stroke-width="1"/>')
        o.append(f'<text x="{L - 7}" y="{gy + 3.5:.1f}" font-size="9" fill="#a49a89" '
                 f'text-anchor="end" font-family="Helvetica Neue,Arial">'
                 f'{top * frac:.0f}</text>')
    for i, r in enumerate(reads):
        cx = L + step * i + (step - bw) / 2
        tot = sum(r['mood'].get(k, 0) for k in kinds)
        yy = H
        for k in kinds:
            n = r['mood'].get(k, 0)
            if not n:
                continue
            h = H * n / top
            yy -= h
            o.append(f'<rect x="{cx:.1f}" y="{yy:.1f}" width="{bw:.1f}" '
                     f'height="{h:.1f}" fill="{MOOD_COLOR[k]}" opacity=".84">'
                     f'<title>eps {r["window"][0]}–{r["window"][1]}: {n} {k}</title>'
                     f'</rect>')
        o.append(f'<text x="{cx + bw / 2:.1f}" y="{H + 15:.1f}" font-size="9.5" '
                 f'fill="#6b6354" text-anchor="middle" '
                 f'font-family="Helvetica Neue,Arial">'
                 f'{r["window"][0]}–{r["window"][1]}</text>')
        o.append(f'<text x="{cx + bw / 2:.1f}" y="{H + 28:.1f}" font-size="9" '
                 f'fill="#a49a89" text-anchor="middle" '
                 f'font-family="Helvetica Neue,Arial">{r.get("total_comments", tot)} '
                 f'read</text>')
    lx = L
    for k in kinds:
        if not any(r['mood'].get(k) for r in reads):
            continue
        o.append(f'<rect x="{lx:.0f}" y="{H + 50:.0f}" width="9" height="9" '
                 f'fill="{MOOD_COLOR[k]}"/>')
        o.append(f'<text x="{lx + 14:.0f}" y="{H + 58:.0f}" font-size="10" '
                 f'fill="#6b6354" font-family="Helvetica Neue,Arial">{k}</text>')
        lx += 26 + 7.0 * len(k)
    o.append('</svg>')
    return ('<figure style="margin:16px 0 4px"><div style="overflow-x:auto">'
            + ''.join(o) + '</div></figure>')


# ---------------------------------------------------------------- blocks

def comments_for(f, reads, limit=3):
    """Quotes from any window overlapping this finding. A finding with no comment
    window gets nothing — we never borrow a quote from a different stretch."""
    out = []
    for r in reads:
        lo, hi = r['window']
        if hi < f['from'] or f['to'] < lo:
            continue
        for t in r.get('themes', []):
            for q in t.get('quotes', []):
                out.append((t.get('count', 0), q.get('likes', 0), t['theme'], q))
    out.sort(key=lambda x: (-x[0], -x[1]))
    return out[:limit]


def finding_block(f, reads, note):
    """One finding, told as a story problem on the left and a measurement on the
    right. The verdict never appears in the left column."""
    # house.css has no `aud near`; amber is `spend`. Using a class that does not
    # exist drops the left border silently and the panel loses its verdict colour.
    cls = {'CONFIRMED': 'cliff', 'MISSED': 'turn', 'CONTESTED': 'spend',
           'NOT CREATIVE': 'beyond'}.get(f['verdict'], 'hold')
    span = f'eps {f["from"]}–{f["to"]}' if f['to'] != f['from'] else f'ep {f["from"]}'
    story = f.get('story') or f.get('what') or ''
    paras = ''.join(f'<p>{e(p.strip())}</p>' for p in re.split(r'\n\s*\n', story)
                    if p.strip()) or '<p>—</p>'
    if note:
        paras += f'<p>{e(note)}</p>'
    qs = comments_for(f, reads)
    cmts = ''
    if qs:
        rows = ''.join(
            f'<blockquote>{e(q["text"])}<cite>— ep {q.get("ep", "?")}'
            + (f', {q["likes"]} likes' if q.get('likes') else '')
            + f' · {e(theme)}</cite></blockquote>'
            for _, _, theme, q in qs)
        cmts = (f'<div class="cmts"><div class="cmts-h">What listeners said here</div>'
                f'{rows}</div>')
    bench = (f' · {ratio(f["vs_benchmark"])} the benchmark'
             if f.get('vs_benchmark') else '')
    trap = ''
    if f.get('cause_evidence'):
        items = ''.join(f'<li style="margin:5px 0">{e(x)}</li>'
                        for x in f['cause_evidence'])
        was = (f' Recorded as {f["verdict_was"]} until the cause was checked.'
               if f.get('verdict_was') else '')
        trap = (f'<div class="cmts"><div class="cmts-h">Why this is not a script '
                f'problem</div><ul style="margin:4px 0 0;padding-left:17px;'
                f'font-size:12.5px;line-height:1.5;color:#4a443b">{items}</ul>'
                f'<p style="margin:7px 0 0;font-size:11.5px;color:#8a8173">'
                f'Cause: {e(f.get("cause") or "—")}.{e(was)}</p></div>')
    return (f'<section class="act">'
            f'<div class="act-head">'
            f'<span class="act-num">{e(f.get("code") or f["verdict"][:2])}</span>'
            f'<h3>{e(f["label"])}</h3>'
            f'<span class="act-eps">{span} · '
            f'{e(KIND_LABEL.get(f.get("kind"), ""))}</span></div>'
            f'<div class="act-body">'
            f'<div class="story"><div class="col-h">What happens in the story</div>'
            f'{paras}</div>'
            f'<aside class="aud {cls}">'
            f'<div class="aud-h">What the data says</div>'
            f'<div class="aud-status">'
            f'<span class="vb {f["verdict"].replace(" ", "")}">{f["verdict"]}</span>'
            f'</div>'
            f'<p class="aud-ret">Listeners left <b>{ratio(f["vs_show"])}</b> faster '
            f'than this show’s own baseline{bench}. '
            f'<b>{fmt(cost(f))}</b> listeners above what the '
            f'{f["n"]}-episode stretch should have cost. '
            f'{f["comments"]} comments in the window.</p>'
            f'{trap}{cmts}</aside></div></section>')


def solution_block(s, i):
    def row(k, v):
        return f'<dt>{e(k)}</dt><dd>{v}</dd>' if v else ''
    return (f'<div class="sol"><div class="sol-h">'
            f'<span class="sol-n">FIX {i}</span><h4>{e(s["title"])}</h4>'
            + (f'<span class="stw {"flag" if s.get("priority") == "high" else "near" if s.get("priority") == "medium" else "hold"}">'
               f'{e(s.get("priority", "")) } priority</span>' if s.get('priority') else '')
            + f'</div><div class="sol-b"><dl>'
            + row('The problem', e(s.get('problem', '')))
            + row('Data behind it', e(s.get('data', '')))
            + row('Listeners', e(s.get('comments', '')))
            + row('Do this', f'<b>{e(s["do"])}</b>' if s.get('do') else '')
            + row('Where', e(s.get('where', '')))
            + row('Confidence', e(s.get('confidence', '')))
            + f'</dl></div></div>')


def roman(n):
    vals = [(10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
    out = ''
    for v, sym in vals:
        while n >= v:
            out += sym
            n -= v
    return out


# ---------------------------------------------------------------- page

def build(claims, v, data, reads, notes, title, css):
    th = v['thresholds']
    findings = list(v['tested']) + list(v['missed'])
    for f in findings:
        f.setdefault('label', f.get('title', '—'))
    byv = {k: [f for f in findings if f['verdict'] == k]
           for k in ('MISSED', 'CONFIRMED', 'NOT CREATIVE', 'CONTESTED',
                     'NO COST')}
    eps = data['episodes']
    last = v['last_ep']
    n_comments = sum(len(c) for c in data['comments'].values())
    read_total = sum(r.get('total_comments', 0) for r in reads)
    notes_f = notes.get('finding_notes', {})
    o = []
    A = o.append
    # Number parts as they are emitted. Hardcoding the numerals left gaps whenever a
    # verdict came back empty, and the page read I, II, IV, VI, VII, VIII.
    _pn = [0]

    def PART(label):
        _pn[0] += 1
        A(f'<div class="part">Part {roman(_pn[0])} · {label}</div>')

    A(f'<div class="wrap">')
    A(f'<div class="eyebrow">Validation · creative findings tested against '
      f'listener data</div>')
    A(f'<h1>{e(title)}</h1>')
    A(f'<div class="sub">{e(notes.get("subhead", "Does the creative audit hold up?"))}'
      f'</div>')
    A(f'<div class="meta">{last} episodes · {fmt(eps[str(v["baseline_from"])]["listen"])} '
      f'listeners at the ep {v["baseline_from"]} baseline · benchmark '
      f'{e(data["benchmark"])}, matched on cumulative hours · {fmt(n_comments)} '
      f'comments · {len(findings)} creative findings tested</div>')
    A('<div class="rule"></div>')

    # the answer, up top
    A(f'<div class="lead">{notes.get("headline", "")}</div>')
    A(f'<div class="kv">')
    for k in ('MISSED', 'CONFIRMED', 'NOT CREATIVE', 'CONTESTED', 'NO COST'):
        if byv[k]:
            A(f'<div><b style="color:{VERDICT_COLOR[k]}">{len(byv[k])}</b>'
              f'<span>{k}</span></div>')
    # Only a zone the data says cost something can be "the worst": summing excess
    # over a flat 150-episode finding beat the real 40-episode disaster on width
    # alone.
    charged = [f for f in findings if f['verdict'] != 'NO COST']
    if charged:
        worst = max(charged, key=lambda f: cost(f))
        A(f'<div><b>{fmt(cost(worst))}</b><span>worst single zone, '
          f'eps {worst["from"]}–{worst["to"]}</span></div>')
    A(f'<div><b>{fmt(read_total)}</b><span>comments read in full</span></div>')
    A('</div>')

    A(f'<div class="note"><h4>How a finding was tested</h4>'
      f'<p>Every zone, broken promise and hook close in the Creative Audit was turned '
      f'into a span of episodes, and the drop rate inside that span was compared with '
      f'two things: this show’s own rate from episode {v["baseline_from"]} onward, and '
      f'{e(data["benchmark"])} at the same cumulative listening hours — not the same '
      f'episode number, because these shows have different episode lengths.</p>'
      f'<p>Episodes 1–{v["baseline_from"] - 1} are excluded from the baseline. Early '
      f'drop is sampling, not story: everyone who opens episode 1 is counted, '
      f'including people who never intended to listen.</p>'
      f'<p><b>CONFIRMED</b> — the creative finding is there and listeners left faster '
      f'than {th["confirm"]:g}× baseline inside it. '
      f'<b>NO COST</b> — the finding is real in the script and cost nothing '
      f'measurable. <b>MISSED</b> — listeners left at {th["miss"]:g}× or worse in a '
      f'stretch the audit never flagged. <b>CONTESTED</b> — the data points the '
      f'opposite way from the script read.</p>'
      f'<p>A NO COST verdict does not mean the script problem is not a problem. It '
      f'means it did not show up as churn in this run, and that fixing it is a craft '
      f'decision rather than a retention one.</p></div>')

    # ---- Part I · the scoreboard
    PART('The scoreboard')
    A('<div class="sec"><div class="secn">Where the show actually leaks</div>')
    A('<div class="readnote">Each bar is ten episodes. Height is how many listeners '
      'were lost above what that stretch should have cost at the show’s own rate. '
      'Colour is the verdict of whichever creative finding covers that stretch; grey '
      'means the audit found nothing there. Hover any bar for the episode range, the '
      'rate, and the comment count.</div>')
    A(bleed_map(v['sweep'], findings, last))
    A('<div class="chartnote">Read the grey spikes first. A grey spike is a stretch '
      'losing listeners that the script read did not predict.</div>')

    A('<div class="secn">Every finding, measured</div>')
    A(verdict_bars(findings, th))
    A('<table class="vtab"><thead><tr><th>Finding</th><th>Kind</th>'
      '<th class="num">Episodes</th><th class="num">vs baseline</th>'
      '<th class="num">vs benchmark</th><th class="num">Listeners vs baseline</th>'
      '<th class="num">Comments</th><th>Verdict</th></tr></thead><tbody>')
    for f in sorted(findings, key=lambda f: -f['vs_show']):
        A(f'<tr class="{VERDICT_CLASS[f["verdict"]]}">'
          f'<td>{e(f["label"])}</td>'
          f'<td style="font-size:12px;color:#6b6354">'
          f'{e(KIND_LABEL.get(f.get("kind"), "—"))}</td>'
          f'<td class="num">{f["from"]}–{f["to"]}</td>'
          f'<td class="num">{ratio(f["vs_show"])}</td>'
          f'<td class="num">{ratio(f["vs_benchmark"]) if f.get("vs_benchmark") else "—"}</td>'
          f'<td class="num">{fmt(cost(f))}</td>'
          f'<td class="num">{f["comments"]}</td>'
          f'<td><span class="vb {f["verdict"].replace(" ", "")}">{f["verdict"]}</span>'
          f'</td></tr>')
    A('</tbody></table>')
    A('<div class="chartnote">Sorted by how fast listeners left, not by how serious '
      'the script problem looked.</div>')

    A('<div class="secn">The full run, with the findings laid over it</div>')
    A('<div class="readnote">Solid line is this show’s episode-over-episode drop. '
      'Dashed is the benchmark at the same cumulative hours. Shaded bands are creative '
      'findings, tinted by verdict. Hover anywhere for the exact episode number, its '
      'drop, and its title.</div>')
    A(curve(eps, data['benchmark_drop_at'], findings, last))

    comp = completion(eps, findings, last)
    if comp:
        A('<div class="secn">Who finishes the episode they started</div>')
        A('<div class="readnote">Drop rate counts people who do not come back. This '
          'counts people who stop partway through and never return to that episode. A '
          'stretch can hold its audience from episode to episode and still be losing '
          'them inside every one, and that is a different problem with a different '
          'fix.</div>')
        A(comp)
    A('</div>')

    # ---- Part II · confirmed
    if byv['CONFIRMED']:
        PART('What the data confirmed')
        A('<div class="sec"><div class="readnote">The script read and the listener '
          'numbers agree here. Two passes that could not see each other landed on the '
          'same episodes, which is the strongest thing this document can say.</div>')
        for f in sorted(byv['CONFIRMED'], key=lambda f: -f['vs_show']):
            A(finding_block(f, reads, notes_f.get(f['label'])))
        A('</div>')

    # ---- Part III · missed
    if byv['MISSED']:
        PART('What the audit missed')
        A('<div class="sec"><div class="readnote">Listeners left fastest here, and the '
          'Creative Audit has no zone for it. Either the script problem is of a kind a '
          'script read cannot see, or it is not a script problem at all — production, '
          'paywall, release gap. Both are findings.</div>')
        for f in sorted(byv['MISSED'], key=lambda f: -f['vs_show']):
            A(finding_block(f, reads, notes_f.get(f['label'])))
        A('</div>')

    # ---- Part IV · not creative
    if byv['NOT CREATIVE']:
        PART('Real, large, and not the script')
        A('<div class="sec"><div class="readnote">These stretches lose listeners '
          'faster than anywhere else in the show, and the cause sits outside the '
          'script: a price change, a voice change, a delivery fault. They are in this '
          'document because a creative audit cannot see them and a writers’ room '
          'cannot fix them. Sending a rewrite at one of these spends a draft on a '
          'pricing decision.</div>')
        nc = sum(max(0, cost(f)) for f in byv['NOT CREATIVE'])
        # Denominator is loss the report actually attributes to a cause. Summing over
        # every finding double-counts: four separate findings all cover eps 660-665.
        tot = sum(max(0, cost(f)) for f in findings
                  if f['verdict'] != 'NO COST')
        A(f'<div class="kv"><div><b>{fmt(nc)}</b><span>listeners lost outside the '
          f'script</span></div><div><b>{nc / max(1, tot) * 100:.0f}%</b>'
          f'<span>of loss this report can attribute</span></div></div>')
        for f in sorted(byv['NOT CREATIVE'], key=lambda f: -cost(f)):
            A(finding_block(f, reads, notes_f.get(f['label'])))
        A('</div>')

    # ---- Part V · contested
    if byv['CONTESTED']:
        PART('What the data contradicted')
        A('<div class="sec">')
        for f in byv['CONTESTED']:
            A(finding_block(f, reads, notes_f.get(f['label'])))
        A('</div>')

    # ---- Part V · cleared
    PART('What cost nothing')
    A('<div class="sec">')
    A(f'<div class="readnote">{e(notes.get("cleared_note", ""))}</div>')
    A('<table class="vtab"><thead><tr><th>Finding</th><th class="num">Episodes</th>'
      '<th class="num">vs baseline</th><th class="num">Listeners vs baseline</th>'
      '<th>What it means</th></tr></thead><tbody>')
    for f in sorted(byv['NO COST'], key=lambda f: -f['vs_show']):
        A(f'<tr class="hold"><td>{e(f["label"])}</td>'
          f'<td class="num">{f["from"]}–{f["to"]}</td>'
          f'<td class="num">{ratio(f["vs_show"])}</td>'
          f'<td class="num">{fmt(cost(f))}</td>'
          f'<td style="font-size:12.5px;color:#4a4438">'
          f'{e(notes_f.get(f["label"], "Real in the script, invisible in the data."))}'
          f'</td></tr>')
    A('</tbody></table></div>')

    # ---- Part VI · listeners
    if reads:
        PART('What listeners actually say')
        A('<div class="sec"><div class="readnote">Agents read every comment in each '
          'window without being told what the audit claimed about it, for the same '
          'reason the arc pass never saw the hooks. Counts are comments, not '
          'estimates.</div>')
        A(mood_chart(reads))
        for r in sorted(reads, key=lambda r: r['window'][0]):
            A(f'<div class="card" style="margin:16px 0">'
              f'<h4 style="margin:0 0 6px">eps {r["window"][0]}–{r["window"][1]} · '
              f'{r.get("total_comments", 0)} comments</h4>'
              f'<p style="margin:0 0 10px">{e(r.get("summary", ""))}</p>')
            for t in sorted(r.get('themes', []), key=lambda t: -t.get('count', 0))[:4]:
                A(f'<div style="margin:11px 0 0"><b style="font-size:13px">'
                  f'{e(t["theme"])}</b> '
                  f'<span style="font-size:11px;color:#8a8173;letter-spacing:.04em">'
                  f'· {t.get("count", 0)} comments · {e(t.get("kind", ""))}</span></div>')
                for q in t.get('quotes', [])[:2]:
                    A(f'<div class="q">{e(q["text"])}<cite>— ep {q.get("ep", "?")}'
                      + (f', {q["likes"]} likes' if q.get('likes') else '')
                      + '</cite></div>')
            A('</div>')
        A('</div>')

    # ---- Part VII · solutions
    sols = notes.get('solutions', [])
    if sols:
        PART('What to do')
        A('<div class="sec"><div class="readnote">Ordered by how much the data says is '
          'at stake, not by how easy the fix is. Every one names the measurement and '
          'the listener evidence behind it, so a fix can be argued with.</div>')
        for i, s in enumerate(sols, 1):
            A(solution_block(s, i))
        A('</div>')

    # ---- appendix
    A('<div class="part">Appendix · The run in ten-episode blocks</div>')
    A('<div class="sec"><table class="vtab"><thead><tr><th class="num">Episodes</th>'
      '<th class="num">Mean drop</th><th class="num">vs baseline</th>'
      '<th class="num">vs benchmark</th><th class="num">Listeners vs baseline</th>'
      '<th class="num">Comments</th><th>Finding covering it</th>'
      '</tr></thead><tbody>')
    for b in sorted(v['sweep'], key=lambda s: s['episodes'][0]):
        lo, hi = b['episodes']
        hit = [f for f in findings if lo <= f['to'] and f['from'] <= hi]
        best = max(hit, key=lambda f: f['vs_show']) if hit else None
        cls = ('flag' if b['vs_show'] >= th['miss'] else
               'near' if b['vs_show'] >= th['confirm'] else '')
        A(f'<tr class="{cls}"><td class="num">{lo}–{hi}</td>'
          f'<td class="num">{abs(b["mean_drop"]) * 100:.2f}%</td>'
          f'<td class="num">{ratio(b["vs_show"])}</td>'
          f'<td class="num">{ratio(b["vs_benchmark"])}</td>'
          f'<td class="num">{fmt(cost(b))}</td>'
          f'<td class="num">{b["comments"]}</td>'
          f'<td style="font-size:12px;color:#6b6354">'
          f'{e(best["label"]) if best else "—"}</td></tr>')
    A('</tbody></table></div>')

    A(f'<div class="rule"></div><div class="meta">Retention and comments supplied; '
      f'creative findings from the Creative Audit of the same show. Drop rates are '
      f'episode-over-episode listener counts. Verdicts are thresholds applied to '
      f'measured rates, not judgments. Quotes are verbatim.</div>')
    A('</div>')

    # The charset declaration is not optional. Served without it, every middot and
    # curly quote on the page renders as mojibake.
    return (f'<!doctype html>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{e(title)} · Validation</title>\n<style>{css}</style>\n'
            f'<style>{TIP_CSS}</style>\n' + '\n'.join(o))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--claims', required=True)
    ap.add_argument('--verdicts', required=True)
    ap.add_argument('--data', required=True)
    ap.add_argument('--reads', default=None, help='directory of comment-read JSON')
    ap.add_argument('--notes', default=None, help='authored prose + solutions')
    ap.add_argument('--css', default=str(pathlib.Path(__file__).parent.parent
                                         / 'assets' / 'house.css'))
    ap.add_argument('--title', required=True)
    ap.add_argument('--out', required=True)
    # The extended report: report 1 plus the data, in report 1's order. Point
    # --audit-build at the show's Creative Audit renderer and pass the same inputs it
    # takes. Without these the companion document is built instead.
    ap.add_argument('--audit-build', help="the show's audit renderer (build.py)")
    ap.add_argument('--ledger')
    ap.add_argument('--health')
    ap.add_argument('--transit')
    ap.add_argument('--arcs')
    # Temporary review aid: tint every block the data added, so the extended report can
    # be skimmed against the audit it grew from. Off by default; the clean document
    # never carries it.
    ap.add_argument('--events', help='events.json from detect_events.py')
    ap.add_argument('--episode-reads', help='directory of blind episode-read JSON')
    ap.add_argument('--sentiment', help='directory of per-episode sentiment JSON')
    ap.add_argument('--mark-data', action='store_true',
                    help='overlay the data-added sections for review')
    a = ap.parse_args()

    claims = json.loads(pathlib.Path(a.claims).read_text())
    v = json.loads(pathlib.Path(a.verdicts).read_text())
    data = json.loads(pathlib.Path(a.data).read_text())
    notes = json.loads(pathlib.Path(a.notes).read_text()) if a.notes else {}
    reads = []
    if a.reads:
        for p in sorted(pathlib.Path(a.reads).glob('*.json')):
            reads.append(json.loads(p.read_text()))

    css = pathlib.Path(a.css).read_text()
    if a.audit_build:
        for need in ('ledger', 'transit', 'health'):
            if not getattr(a, need):
                ap.error(f'--audit-build needs --{need} too; the extended report '
                         f'renders the audit’s own sections and they take its inputs')
        m = load_audit(a.audit_build)
        global _EVENTS, _EPREADS, _SENT
        _EVENTS = (json.loads(pathlib.Path(a.events).read_text())
                   if a.events else {})
        _EPREADS = {}
        if a.episode_reads:
            for q in sorted(pathlib.Path(a.episode_reads).glob('*.json')):
                for r_ in (json.loads(q.read_text()).get('episodes') or []):
                    _EPREADS[r_['ep']] = r_
        _SENT = {}
        if a.sentiment:
            for q in sorted(pathlib.Path(a.sentiment).glob('*.json')):
                _SENT.update(json.loads(q.read_text()).get('episodes') or {})
        jl = lambda p_: json.loads(pathlib.Path(p_).read_text()) if p_ else None
        h = build_extended(m, claims, v, data, reads, notes, a.title,
                           jl(a.ledger), jl(a.health), jl(a.transit), jl(a.arcs), css,
                           mark=a.mark_data)
    else:
        h = build(claims, v, data, reads, notes, a.title, css)

    from html.parser import HTMLParser
    HTMLParser().feed(h)
    bad = re.findall(r'&(?!amp;|lt;|gt;|quot;|#\d+;|nbsp;|#x[0-9a-fA-F]+;)', h)
    assert not bad, f'{len(bad)} unescaped ampersands'
    assert h.count('<aside') == h.count('</aside>'), 'unbalanced aside'
    assert '<meta charset="utf-8">' in h, 'missing charset — page will render mojibake'
    for mm in re.finditer(r'<div class="act-body">(.*?)</section>', h, re.S):
        assert '<aside' in mm.group(1), 'aside fell outside .act-body — grid collapses'

    pathlib.Path(a.out).write_text(h, encoding='utf-8')
    print(f'wrote {a.out}  {len(h) / 1024:.0f} KB'
          + ('  [extended: audit + data]' if a.audit_build else '  [companion]')
          + ('  [REVIEW OVERLAY ON]' if a.mark_data else ''))
    if a.audit_build:
        print(f'  data-first events: '
              f'{sum(len(x.get("events") or []) for x in _EVENTS.values())} '
              f'across {len(_EVENTS)} acts · episodes read blind: {len(_EPREADS)}'
              f' · episodes with sentiment: {len(_SENT)}')
    c = Counter(f['verdict'] for f in list(v['tested']) + list(v['missed']))
    print('  verdicts: ' + ', '.join(f'{k} {n}' for k, n in c.most_common()))
    print(f'  comment windows read: {len(reads)}')
    print(f'  solutions: {len(notes.get("solutions", []))}')



# ---------------------------------------------------------------- the extended report
# Report 2 is report 1 plus the data. It imports the Creative Audit's own renderer and
# calls its section functions, so the creative content is never copied or retyped: one
# source, two documents, and they cannot drift apart.

def load_audit(path):
    import importlib.util
    spec = importlib.util.spec_from_file_location('audit_renderer', path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def win(data, lo, hi):
    """Drop stats for an episode range. Same arithmetic as test_claims.window, kept
    local so the renderer has no import dependency on the tester."""
    eps = data['episodes']
    d = [eps[str(x)]['drop'] for x in range(lo, hi + 1)
         if str(x) in eps and eps[str(x)]['drop'] is not None]
    if not d:
        return None
    base = data['baseline_drop']
    bench = [data['benchmark_drop_at'].get(str(x)) for x in range(lo, hi + 1)]
    bench = [b for b in bench if b is not None]
    mean_drop = sum(d) / len(d)
    start = eps.get(str(lo), {}).get('listen') or 0
    expected = start * (1 - abs(base)) ** len(d)
    actual = start * (1 - abs(mean_drop)) ** len(d)

    # --- cost, from the LEVEL series rather than the rate.
    # `drop` and `listen` are different measures: at ep 200 this show's level fell
    # 0.078% while its drop column read 1.539%. Compounding the rate against the level
    # to derive "listeners lost" mixes the two and inflates the answer, which is the
    # one thing the donor brief says never to do. Cost is a headcount, so take it from
    # the headcount.
    lv = lambda x: (eps.get(str(x)) or {}).get('listen')
    s_lvl, e_lvl = lv(lo), lv(hi)
    k = hi - lo
    if s_lvl and e_lvl and k > 0:
        per = data.get('level', {}).get('per_episode_decline')
        if per is None:
            per = 0.0
        predicted = s_lvl * (1 - per) ** k
        level_lost = s_lvl - e_lvl
        level_excess = level_lost - (s_lvl - predicted)
    else:
        level_lost = level_excess = None

    return {'n': len(d), 'mean_drop': mean_drop,
            'vs_show': abs(mean_drop) / abs(base) if base else 0,
            'vs_benchmark': (abs(mean_drop) / abs(sum(bench) / len(bench))
                             if bench and sum(bench) else 0),
            'excess_listeners': max(0, expected - actual),
            'level_from': s_lvl, 'level_to': e_lvl,
            'level_lost': level_lost,
            'level_excess': level_excess,
            'comments': sum(len(data['comments'].get(str(x), []))
                            for x in range(lo, hi + 1))}


def join_table(findings, kind, caption):
    """One compact row per creative finding, carrying the verdict. This is the join
    between the two reports: the code in the left column is the same code the audit
    section above it uses."""
    rows = [f for f in findings if f.get('kind') == kind and f.get('ref')]
    if not rows:
        return ''
    rows.sort(key=lambda f: (f['ref'][0], int(re.sub(r'\D', '', f['ref']) or 0)))
    body = ''.join(
        f'<tr class="{VERDICT_CLASS[f["verdict"]]}">'
        f'<td><b>{e(f["ref"])}</b></td>'
        f'<td>{e(f["label"])}</td>'
        f'<td class="num">{f["from"]}–{f["to"]}</td>'
        f'<td class="num">{ratio(f["vs_show"])}</td>'
        f'<td class="num">{ratio(f["vs_benchmark"]) if f.get("vs_benchmark") else "—"}</td>'
        f'<td class="num">{fmt(cost(f))}</td>'
        f'<td class="num">{f["comments"]}</td>'
        f'<td><span class="vb {f["verdict"].replace(" ", "")}">{f["verdict"]}</span></td>'
        f'</tr>' for f in rows)
    return (f'<div class="readnote">{e(caption)}</div>'
            f'<table class="vtab"><thead><tr><th></th><th>Finding</th>'
            f'<th class="num">Episodes tested</th><th class="num">vs baseline</th>'
            f'<th class="num">vs benchmark</th><th class="num">Listeners vs baseline</th>'
            f'<th class="num">Comments</th><th>Verdict</th></tr></thead>'
            f'<tbody>{body}</tbody></table>')


def acts_vs_data(acts, data, th, findings=()):
    """Every act, priced. The acts are the spine of the Creative Audit, so this is the
    chart that joins the two reports most directly: which acts actually cost something."""
    # An act that ends before the baseline episode cannot be measured at all. Keep the
    # row and say so: dropping it silently made this table disagree with the act list
    # directly above it, which is worse than an honest blank.
    # An act overlapping a NOT CREATIVE zone has a contaminated number: a paywall
    # inside it raises its drop rate and none of that is writing. Say so in the row.
    # Act 18 of the first show read 1.75x, the worst in 665 episodes, purely because
    # the price change at ep 564 sits inside it.
    nc = [f for f in findings if f.get('verdict') == 'NOT CREATIVE']
    rows, unmeasured = [], []
    for a in sorted(acts, key=lambda a: a['from']):
        w = win(data, max(a['from'], 51), a['to']) if a['to'] >= 51 else None
        hit = [f for f in nc if a['from'] <= f['to'] and f['from'] <= a['to']]
        if w:
            rows.append({**a, **w, 'contaminated': hit})
        else:
            unmeasured.append(a)
    if not rows:
        return ''
    L, W = 250.0, 520.0
    rh, gap = 19.0, 3.0
    top = max(1.4, max(r['vs_show'] for r in rows) * 1.04)
    H = len(rows) * (rh + gap) + 30
    x = lambda r: L + W * r / top
    o = [f'<svg viewBox="0 0 900 {H + 20:.0f}" width="100%" role="img" '
         f'aria-label="Every act, by how fast listeners left inside it">']
    for t in (1.0, th['confirm']):
        o.append(f'<line x1="{x(t):.1f}" y1="6" x2="{x(t):.1f}" y2="{H - 22:.1f}" '
                 f'stroke="#8a8173" stroke-width="1" '
                 f'stroke-dasharray="{"" if t == 1.0 else "4,3"}" opacity=".55"/>')
        o.append(f'<text x="{x(t):.1f}" y="{H - 10:.1f}" font-size="9.5" fill="#8a8173" '
                 f'text-anchor="middle" font-family="Helvetica Neue,Arial">'
                 f'{"baseline" if t == 1.0 else f"confirm {t:g}×"}</text>')
    for i, r in enumerate(rows):
        yy = 6 + i * (rh + gap)
        bw = max(x(r['vs_show']) - L, 1.0)
        col = ('#9a3b28' if r['vs_show'] >= th['confirm']
               else '#b07d2b' if r['vs_show'] >= 1.1 else '#3d6b3f')
        o.append(f'<rect x="{L}" y="{yy:.1f}" width="{bw:.1f}" height="{rh:.1f}" '
                 f'fill="{col}" opacity=".8"/>')
        nm = r['name'] if len(r['name']) <= 26 else r['name'][:24] + '…'
        o.append(f'<text x="{L - 9}" y="{yy + rh / 2 + 3.6:.1f}" font-size="10.5" '
                 f'fill="#3a342c" text-anchor="end" '
                 f'font-family="Helvetica Neue,Arial">{e(r["id"])} · {e(nm)}</text>')
        o.append(f'<text x="{L + bw + 7:.1f}" y="{yy + rh / 2 + 3.6:.1f}" '
                 f'font-size="10" fill="#6b6354" font-family="Helvetica Neue,Arial">'
                 f'{ratio(r["vs_show"])}  {fmt(cost(r))} lost</text>')
        o.append(f'<title>{e(r["id"])} {e(r["name"])} — eps {r["from"]}–{r["to"]}, '
                 f'{ratio(r["vs_show"])} baseline, {fmt(cost(r))} '
                 f'listeners above it, {r["comments"]} comments</title>')
    o.append('</svg>')
    clean = [r for r in rows if not r.get('contaminated')]
    worst = max(clean or rows, key=lambda r: r['vs_show'])
    dirty = sorted((r for r in rows if r.get('contaminated')),
                   key=lambda r: -r['vs_show'])
    # The table must read in act order. Appending the unmeasurable acts after the
    # measured ones put Act 1 at the bottom of a list of twenty acts.
    blank = {a['id']: a for a in unmeasured}
    body = ''
    for a in sorted(list(rows) + list(unmeasured), key=lambda x: x['from']):
        if a['id'] in blank:
            body += (f'<tr><td><b>{e(a["id"])}</b></td><td>{e(a["name"])}</td>'
                     f'<td class="num">{a["from"]}–{a["to"]}</td>'
                     f'<td class="num">{a["to"] - a["from"] + 1}</td>'
                     f'<td colspan="4" style="font-size:12px;color:#8a8173">not '
                     f'measurable — this act ends before episode 51, and everything '
                     f'before 51 is sampling rather than story</td>'
                     f'<td></td></tr>')
            continue
        r = a
        cont = r.get('contaminated')
        cls = ('near' if cont else
               'flag' if r['vs_show'] >= th['confirm'] else
               'near' if r['vs_show'] >= 1.1 else '')
        why = ('; '.join(f'{f["cause"] or "outside the script"}, eps '
                         f'{f["from"]}–{f["to"]}' for f in cont) if cont else '')
        body += (f'<tr class="{cls}">'
                 f'<td><b>{e(r["id"])}</b></td><td>{e(r["name"])}</td>'
                 f'<td class="num">{r["from"]}–{r["to"]}</td>'
                 f'<td class="num">{r["to"] - r["from"] + 1}</td>'
                 f'<td class="num">{abs(r["mean_drop"]) * 100:.2f}%</td>'
                 f'<td class="num">{ratio(r["vs_show"])}</td>'
                 f'<td class="num">{fmt(cost(r))}</td>'
                 f'<td class="num">{r["comments"]}</td>'
                 f'<td style="font-size:11.5px;color:#8a8173">'
                 f'{e(why) if why else ""}</td></tr>')
    return (f'<div class="readnote">The same acts as above, priced. Bar length is how '
            f'fast listeners left inside the act against the show’s own baseline from '
            f'episode 51. Episodes before 51 are excluded, so the first act is '
            f'measured from 51 onward, and an act ending before 51 cannot be priced '
            f'at all. The worst act the data can blame on writing is '
            f'<b>{e(worst["id"])} · {e(worst["name"])}</b> at '
            f'{ratio(worst["vs_show"])}.'
            + (f' <b>{e(dirty[0]["id"])} · {e(dirty[0]["name"])}</b> reads higher at '
               f'{ratio(dirty[0]["vs_show"])}, but a cause outside the script sits '
               f'inside it, so that number is not a verdict on the act. Acts in that '
               f'position are marked in the last column.' if dirty else '')
            + '</div>'
            f'<figure style="margin:14px 0 4px"><div style="overflow-x:auto">'
            + ''.join(o) + '</div></figure>'
            f'<table class="vtab"><thead><tr><th></th><th>Act</th>'
            f'<th class="num">Episodes</th><th class="num">Length</th>'
            f'<th class="num">Mean drop</th><th class="num">vs baseline</th>'
            f'<th class="num">Listeners vs baseline</th><th class="num">Comments</th>'
            f'<th>Number contaminated by</th>'
            f'</tr></thead><tbody>{body}</tbody></table>')


def build_extended(m, claims, v, data, reads, notes, title,
                   ledger, health, transit, arcs_meta, css, mark=False):
    """Report 1 with the data folded in, in report 1's own order.

    `m` is the Creative Audit's renderer module. Every creative section below is its
    output, called with its own authored constants. Nothing creative is re-authored
    here; this function decides order and inserts the measurements."""
    th = v['thresholds']
    findings = list(v['tested']) + list(v['missed'])
    for f in findings:
        f.setdefault('label', f.get('title', '—'))
    byv = {k: [f for f in findings if f['verdict'] == k]
           for k in ('MISSED', 'CONFIRMED', 'NOT CREATIVE', 'CONTESTED', 'NO COST')}
    eps, last = data['episodes'], v['last_ep']
    arcs = (transit or {}).get('arcs')
    last_script = (ledger.get('range') or [None, last])[1] or last
    notes_f = notes.get('finding_notes', {})
    events = _EVENTS or {}
    reads_by_ep = _EPREADS or {}
    sentiment = _SENT or {}
    n_comments = sum(len(c) for c in data['comments'].values())
    read_total = sum(r.get('total_comments', 0) for r in reads)

    # The audit numbers its trouble zones by sorted start episode and its breaks by
    # list order, inside its own build(). Replicate that here or the D and B labels in
    # this document will not match the ones in the audit.
    for n, d in enumerate(sorted(m.DRIFT, key=lambda d: d['eps'][0]), start=1):
        d['_n'] = n
    for n, b in enumerate(m.BREAKS, start=1):
        b['_n'] = n

    o = []
    A = o.append
    _pn = [0]

    def part_html(label):
        _pn[0] += 1
        return f'<div class="part">Part {roman(_pn[0])} · {label}</div>'

    def PART(label):
        A(part_html(label))

    def D(*parts):
        """Emit a block the data added. Under --mark-data it gets the review overlay;
        otherwise it is emitted exactly as it would have been."""
        html = ''.join(x for x in parts if x)
        A(f'<div class="dnew">{html}</div>' if mark else html)

    A('<div class="wrap">')
    if mark:
        A('<div class="dkey">TEMPORARY REVIEW OVERLAY · everything in a '
          '<b>blue box</b> is what the data added to the Creative Audit. Everything '
          'outside one is the audit, unchanged. Rebuild without '
          '<b>--mark-data</b> for the clean document.</div>')
    A('<div class="eyebrow">Creative audit · validated against listener data</div>')
    A(f'<h1>{e(title)}</h1>')
    A(f'<div class="sub">{e(getattr(m, "SUBTITLE", ""))}</div>')
    A(f'<div class="meta">{ledger.get("episodes_present", last)} episodes · scripts '
      f'read in full · {fmt((eps.get(str(v["baseline_from"])) or {}).get("listen") or 0)} '
      f'listeners at the ep {v["baseline_from"]} baseline · benchmark '
      f'{e(data["benchmark"])}, matched on cumulative hours · {fmt(n_comments)} '
      f'comments, {fmt(read_total)} read in full</div>')
    A('<div class="rule"></div>')

    A(f'<div class="logline">{e(m.LOGLINE.strip())}</div>')
    A('<div class="sec"><div class="secn">What the show promises</div></div>')
    A(f'<div class="lead">{m.LEAD.strip()}</div>')

    if getattr(m, 'CAST', None):
        A('<div class="sec"><div class="secn">Who you need to know</div></div>')
        A(''.join(f'<div class="castrow"><div class="castname">{e(nm)}</div>'
                  f'<div class="castbio">{e(bio)}</div></div>' for nm, bio in m.CAST))

    # --- what the data did to the creative read, stated before any of it
    _d = ['<div class="sec"><div class="secn">What the data did to this '
          'read</div></div>',
          f'<div class="lead">{notes.get("headline", "")}</div>', '<div class="kv">']
    A = _d.append
    for k in ('MISSED', 'CONFIRMED', 'NOT CREATIVE', 'CONTESTED', 'NO COST'):
        if byv[k]:
            A(f'<div><b style="color:{VERDICT_COLOR[k]}">{len(byv[k])}</b>'
              f'<span>{k}</span></div>')
    charged = [f for f in findings if f['verdict'] != 'NO COST']
    if charged:
        w = max(charged, key=lambda f: cost(f))
        A(f'<div><b>{fmt(cost(w))}</b><span>worst single zone, '
          f'eps {w["from"]}–{w["to"]}</span></div>')
    A(f'<div><b>{fmt(read_total)}</b><span>comments read in full</span></div>')
    A('</div>')
    A(f'<div class="note"><h4>How a finding was tested</h4>'
      f'<p>Every hook close, broken promise and trouble zone below carries a verdict. '
      f'Each one was turned into a span of episodes, and the drop rate inside that span '
      f'compared with two things: this show’s own rate from episode '
      f'{v["baseline_from"]} onward, and {e(data["benchmark"])} at the same cumulative '
      f'listening hours rather than the same episode number.</p>'
      f'<p>Episodes 1–{v["baseline_from"] - 1} are excluded from the baseline. Early '
      f'drop is sampling, not story.</p>'
      f'<p><b>CONFIRMED</b> — the finding is there and listeners left faster than '
      f'{th["confirm"]:g}× baseline inside it. <b>NO COST</b> — real in the script, '
      f'flat in the data. <b>MISSED</b> — listeners left at {th["miss"]:g}× or worse '
      f'where this audit found nothing. <b>NOT CREATIVE</b> — the drop is real and the '
      f'cause sits outside the script. <b>CONTESTED</b> — the two point opposite ways.'
      f'</p><p>Retention is measured. Creative causation is inferred. A verdict says '
      f'people left, not why.</p></div>')
    A = o.append
    D(*_d)

    # --- Part I is the acts. This is the primary structure of the document: the show
    # in order, one chunk at a time, with both directions of analysis inside the act
    # they belong to. Every cross-cutting view lives below, after the acts.
    if transit and health:
        PART('The story, act by act')
        A('<div class="readnote">This is the show itself, in order, one act at a time, '
          'and it is the spine of this document. Each act carries four things: what '
          'happens in the story, what the script analysis found there, what the data '
          'says about those same episodes, and what the data singles out on its own '
          'before anyone looked at the script.<br><br>'
          'Those last two are different directions and both are here deliberately. '
          '<b>Content first</b> takes a creative finding and asks whether it cost '
          'anything. <b>Data first</b> takes the numbers, picks the episodes they point '
          'at, and sends someone to read those episodes without telling them why. One '
          'can only confirm what someone already suspected. The other can find what '
          'nobody was looking for.<br><br>'
          'Everything after the acts is the same material viewed across the whole show '
          'at once.</div>')
        # Composed act by act from the audit's three pure joins, not borrowed as
        # finished HTML: the acts here carry the same facts in a different shape.
        adv = notes.get('act_advice', {})
        nev = notes.get('event_notes', {})
        base_neg = show_negative_rate(sentiment)
        for i, act in enumerate(sorted(claims['acts'], key=lambda a: a['from']), 1):
            A(act_section_v2(act, i, m, data, findings, events, reads_by_ep,
                             sentiment, base_neg, health,
                             transit.get('last_ep') or last_script,
                             adv.get(act['id']), nev, mark))

    A('<div class="rule"></div>')
    A('<div class="part" style="margin-top:8px">Across the whole show</div>')
    A('<div class="readnote">Everything below is the same analysis, aggregated. The acts '
      'above are where it is actionable; these views are where it is comparable.</div>')

    D('<div class="sec"><div class="secn">The acts, priced</div></div>',
      acts_vs_data(claims['acts'], data, th, findings))

    # --- Part: hooks
    PART('The questions that hold the show up')
    A(m.ranked_table(m.HOOKS, health))
    D('<div class="sec"><div class="secn">What happened when each question '
      'closed</div></div>',
      join_table(findings, 'hook_close',
                 'Each question tested across the eleven episodes around its close. '
                 'Closing a question is where a show is most exposed: the listener has '
                 'what they came for, and something else has to be live or they leave.'))

    # --- Part: the whole show at once, script charts then data charts on the same scale
    PART('The whole show at once')
    A('<div class="sec"><div class="secn">Every question, start to finish</div></div>')
    A('<div class="readnote">Each bar is one question. It starts where the show first '
      'asks it and ends where the show answers it. <b>Green</b> means the answer '
      'happens on screen. <b>Amber</b> means it arrives very late. <b>Red</b> means the '
      'question was dodged, answered off screen, or never answered at all.<br><br>'
      'The shaded strips behind the bars are stretches where something is going wrong. '
      '<b>Pink is worse than amber.</b></div>')
    A(m.timeline(m.HOOKS, m.DRIFT, last_script, arcs))
    A(m.band_key(m.DRIFT))

    if health:
        cov, dead = m.coverage_chart(health, arcs)
        A('<div class="sec"><div class="secn">How many questions were live at '
          'once</div></div>')
        A('<div class="readnote">A question counts as live only if the show actually '
          f'raised it in the last {m.LIVE_WINDOW} episodes. One nobody has mentioned '
          'for fifty episodes is still unanswered, but it is not holding anyone.</div>')
        A(cov)
        A(m.dead_table(dead))
        sv = m.strips(health)
        if sv:
            A('<div class="sec"><div class="secn">Which episodes actually raised each '
              'question</div></div>')
            A('<div class="readnote"><b>Green</b> means that episode did something with '
              'the question. <b>Grey</b> means the question was hanging and that '
              'episode ignored it. <b>Blank</b> means it had not been asked yet, or was '
              'already answered.</div>')
            A(sv)

    _d = ['<div class="sec"><div class="secn">And where the show actually lost '
          'people</div></div>']
    A = _d.append
    A(f'<div class="readnote">The same {last} episodes, measured. Each bar is ten '
      f'episodes; '
      'height is how many listeners were lost above what that stretch should have cost '
      'at the show’s own rate. Colour is the verdict of whichever finding covers it, '
      'grey where this audit found nothing. Read the grey spikes first: a grey spike is '
      'a stretch bleeding listeners that the script read did not predict.</div>')
    A(bleed_map(v['sweep'], findings, last))
    A('<div class="sec"><div class="secn">The run, with the findings laid over '
      'it</div></div>')
    A('<div class="readnote">Solid is this show’s episode-over-episode drop, dashed is '
      'the benchmark at the same cumulative hours, shaded bands are findings tinted by '
      'verdict. Hover anywhere for the exact episode.</div>')
    A(curve(eps, data['benchmark_drop_at'], findings, last))
    comp = completion(eps, findings, last)
    if comp:
        A('<div class="sec"><div class="secn">Who finishes the episode they '
          'started</div></div>')
        A('<div class="readnote">Drop rate counts people who do not come back. This '
          'counts people who stop partway through. Read it against its own trend, not '
          'absolutely: completion climbs across any long run, because the audience '
          'still listening at episode 500 is the committed one.</div>')
        A(comp)
    A = o.append
    D(*_d)

    # --- Part: resolutions and breaks
    PART('Resolutions and broken promises')
    A('<div class="sec"><div class="secn">How each hook closes</div></div>')
    A(m.resolutions_table(m.HOOKS))
    A('<div class="sec"><div class="secn">Broken promises</div></div>')
    A('<div class="readnote">Each break is quoted twice, the line that makes the '
      'promise and the line that withdraws it. <b>B1</b> retcon · <b>B2</b> offscreen '
      'close · <b>B3</b> deflation · <b>B4</b> substitution · <b>B5</b> drop · '
      '<b>B6</b> deferred past use.</div>')
    A(m.breaks_section(m.BREAKS, arcs))
    D('<div class="sec"><div class="secn">What each break cost</div></div>',
      join_table(findings, 'break',
                 'Each break tested across the eleven episodes around the episode it '
                 'breaks. A break late in a run is tested on a hardened audience: by '
                 'episode 650 the listeners left will finish almost anything, so a flat '
                 'verdict there is weaker evidence than the same verdict at '
                 'episode 100.'))

    # --- Part: drift
    PART('Where the show loses people')
    A('<div class="readnote"><b>D1</b> promise vacuum · <b>D2</b> lead stops driving · '
      '<b>D3</b> cast bloat or untrackable names · <b>D4</b> repetition and stall · '
      '<b>D5</b> pacing · <b>D6</b> other, mechanism named. Severity is judgment from '
      'the script. The verdict under each zone is measurement.</div>')
    A(m.drift_section(m.DRIFT, arcs))
    D('<div class="sec"><div class="secn">What each zone cost</div></div>',
      join_table(findings, 'trouble',
                 'Each zone tested across its own episode range. A wide zone averages '
                 'itself out: a 150-episode zone can read flat while a bad twenty '
                 'episodes hide inside it, which is why the bleed map above is read '
                 'separately.'))

    # --- the verdict parts
    if byv['CONFIRMED']:
        _d = [part_html('What the data confirmed'),
              '<div class="sec"><div class="readnote">The script read and the listener '
              'numbers agree here. Two passes that could not see each other landed on '
              'the same episodes.</div>']
        for f in sorted(byv['CONFIRMED'], key=lambda f: -f['vs_show']):
            _d.append(finding_block(f, reads, notes_f.get(f['label'])))
        _d.append('</div>')
        D(*_d)

    if byv['MISSED']:
        _d = [part_html('What this audit missed'),
              '<div class="sec"><div class="readnote">Listeners left fastest here and '
              'the script read has no zone for it.</div>']
        for f in sorted(byv['MISSED'], key=lambda f: -f['vs_show']):
            _d.append(finding_block(f, reads, notes_f.get(f['label'])))
        _d.append('</div>')
        D(*_d)

    if byv['NOT CREATIVE']:
        _d = [part_html('Real, large, and not the script')]
        A = _d.append
        A('<div class="sec"><div class="readnote">These stretches lose listeners faster '
          'than anywhere else in the show, and the cause sits outside the script: a '
          'price change, a voice change, a delivery fault. They are in this document '
          'because a script read cannot see them and a writers’ room cannot fix them. '
          'Sending a rewrite at one of these spends a draft on a pricing '
          'decision.</div>')
        nc = sum(max(0, cost(f)) for f in byv['NOT CREATIVE'])
        tot = sum(max(0, cost(f)) for f in charged) or 1
        A(f'<div class="kv"><div><b>{fmt(nc)}</b><span>listeners lost outside the '
          f'script</span></div><div><b>{nc / tot * 100:.0f}%</b><span>of loss this '
          f'report can attribute</span></div></div>')
        for f in sorted(byv['NOT CREATIVE'], key=lambda f: -cost(f)):
            A(finding_block(f, reads, notes_f.get(f['label'])))
        A('</div>')
        A = o.append
        D(*_d)

    if byv['CONTESTED']:
        _d = [part_html('What the data contradicted'), '<div class="sec">']
        for f in byv['CONTESTED']:
            _d.append(finding_block(f, reads, notes_f.get(f['label'])))
        _d.append('</div>')
        D(*_d)

    _d = [part_html('What cost nothing')]
    A = _d.append
    A('<div class="sec">')
    A(f'<div class="readnote">{e(notes.get("cleared_note", ""))}</div>')
    A('<table class="vtab"><thead><tr><th></th><th>Finding</th>'
      '<th class="num">Episodes</th><th class="num">vs baseline</th>'
      '<th class="num">Listeners vs baseline</th><th>What it means</th></tr></thead><tbody>')
    for f in sorted(byv['NO COST'], key=lambda f: -f['vs_show']):
        A(f'<tr class="hold"><td><b>{e(f.get("ref") or "")}</b></td>'
          f'<td>{e(f["label"])}</td>'
          f'<td class="num">{f["from"]}–{f["to"]}</td>'
          f'<td class="num">{ratio(f["vs_show"])}</td>'
          f'<td class="num">{fmt(cost(f))}</td>'
          f'<td style="font-size:12.5px;color:#4a4438">'
          f'{e(notes_f.get(f["label"], "Real in the script, invisible in the data."))}'
          f'</td></tr>')
    A('</tbody></table></div>')
    A = o.append
    D(*_d)

    if reads:
        _d = [part_html('What listeners actually say')]
        A = _d.append
        A('<div class="sec"><div class="readnote">Agents read every comment in each '
          'window without being told what this audit claimed about it, for the same '
          'reason the arc pass never saw the hooks. Counts are comments, not '
          'estimates.<br><br>Comments are written by the people who stayed. A warm '
          'comment section is not evidence a stretch is working: the worst stretch in '
          'the first two hundred episodes runs two to one delighted.</div>')
        A(mood_chart(reads))
        for r in sorted(reads, key=lambda r: r['window'][0]):
            A(f'<div class="card" style="margin:16px 0">'
              f'<h4 style="margin:0 0 6px">eps {r["window"][0]}–{r["window"][1]} · '
              f'{r.get("total_comments", 0)} comments</h4>'
              f'<p style="margin:0 0 10px">{e(r.get("summary", ""))}</p>')
            for t in sorted(r.get('themes', []), key=lambda t: -t.get('count', 0))[:4]:
                A(f'<div style="margin:11px 0 0"><b style="font-size:13px">'
                  f'{e(t["theme"])}</b> <span style="font-size:11px;color:#8a8173;'
                  f'letter-spacing:.04em">· {t.get("count", 0)} comments · '
                  f'{e(t.get("kind", ""))}</span></div>')
                for q in t.get('quotes', [])[:2]:
                    A(f'<div class="q">{e(q["text"])}<cite>— ep {q.get("ep", "?")}'
                      + (f', {q["likes"]} likes' if q.get('likes') else '')
                      + '</cite></div>')
            A('</div>')
        A('</div>')
        A = o.append
        D(*_d)

    sols = notes.get('solutions', [])
    if sols:
        _d = [part_html('What to do')]
        A = _d.append
        A('<div class="sec"><div class="readnote">Ordered by how much the data says is '
          'at stake, not by how easy the fix is. Every one names the measurement and '
          'the listener evidence behind it, so it can be argued with. Nothing that came '
          'back NO COST gets a recommendation.</div>')
        for i, s in enumerate(sols, 1):
            A(solution_block(s, i))
        A('</div>')
        A = o.append
        D(*_d)

    A('<div class="part">The cliffhanger ledger</div>')
    A('<div class="readnote">The receipts. One row for every episode that carries '
      'weight: a hook opening or closing, a promise breaking, a trouble zone starting '
      'or ending.</div>')
    A(m.ledger_table(m.LEDGER))

    _d = ['<div class="part">Appendix · The run in ten-episode blocks</div>']
    A = _d.append
    A('<div class="sec"><table class="vtab"><thead><tr><th class="num">Episodes</th>'
      '<th class="num">Mean drop</th><th class="num">vs baseline</th>'
      '<th class="num">vs benchmark</th><th class="num">Listeners vs baseline</th>'
      '<th class="num">Comments</th><th>Finding covering it</th></tr></thead><tbody>')
    for b in sorted(v['sweep'], key=lambda s: s['episodes'][0]):
        lo, hi = b['episodes']
        hit = [f for f in findings if lo <= f['to'] and f['from'] <= hi]
        best = max(hit, key=lambda f: f['vs_show']) if hit else None
        cls = ('flag' if b['vs_show'] >= th['miss'] else
               'near' if b['vs_show'] >= th['confirm'] else '')
        A(f'<tr class="{cls}"><td class="num">{lo}–{hi}</td>'
          f'<td class="num">{abs(b["mean_drop"]) * 100:.2f}%</td>'
          f'<td class="num">{ratio(b["vs_show"])}</td>'
          f'<td class="num">{ratio(b["vs_benchmark"])}</td>'
          f'<td class="num">{fmt(cost(b))}</td>'
          f'<td class="num">{b["comments"]}</td>'
          f'<td style="font-size:12px;color:#6b6354">'
          f'{e(best["label"]) if best else "—"}</td></tr>')
    A('</tbody></table></div>')
    A = o.append
    D(*_d)

    A('<div class="rule"></div>')
    A('<div class="note"><b>Limits.</b> The script is evidence and listener attention '
      'is measured, but creative causation is inferred: a drop says people left, not '
      'why. Pull scores are a rubric applied by judgment. Comment themes are read by '
      'agents, so the counts are real and the grouping is judgment. Thresholds are '
      'choices and are printed above so you can disagree with the line rather than the '
      'conclusion. A NO COST verdict late in the run may mean only that the audience '
      'still listening had already decided to finish.</div>')
    A('</div>')

    return (f'<!doctype html>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{e(title)} · Creative audit, validated</title>\n'
            f'<style>{css}</style>\n<style>{m.TIP_CSS}</style>\n'
            f'<style>{TIP_CSS}</style>\n'
            + (f'<style>{MARK_CSS}</style>\n' if mark else '') + '\n'.join(o))


def act_data_panel(a, data, findings, reads, th, advice=None):
    """The data for one act, rendered to sit inside the audit's own act section.

    Uses the audit's `actx-group` shell so it reads as another group of findings in the
    act rather than a bolt-on. Returns '' for an act the data cannot speak to."""
    w = win(data, max(a['from'], 51), a['to']) if a['to'] >= 51 else None
    hits = [f for f in findings
            if a['from'] <= f['to'] and f['from'] <= a['to']
            and f['verdict'] != 'NO COST']
    nc = [f for f in hits if f['verdict'] == 'NOT CREATIVE']

    themes = []
    for r in reads:
        lo, hi = r['window']
        if hi < a['from'] or a['to'] < lo:
            continue
        for t in r.get('themes', []):
            inside = [x for x in (t.get('episodes') or []) if a['from'] <= x <= a['to']]
            if inside:
                themes.append((t.get('count', 0), t, inside))
    themes.sort(key=lambda x: -x[0])

    if not w and not themes and not advice:
        return ''

    # the headline sentence, written from the numbers rather than asserted
    if not w:
        verdict_line = ('Not measurable. This act ends before episode 51, and '
                        'everything before 51 is people sampling the show rather than '
                        'leaving a story.')
        tone = 'beyond'
    else:
        r_show, r_bench = w['vs_show'], w['vs_benchmark']
        if nc:
            # Built outside the f-string: 3.9 cannot reuse a quote character inside a
            # nested f-string expression.
            causes = '; '.join(
                f'{f["cause"] or "not creative"}, eps {f["from"]}\u2013{f["to"]}'
                for f in nc)
            # "1.00x faster" is not a sentence. Say what the ratio actually is.
            lead_in = (f'Listeners left {ratio(r_show)} faster than this show’s own '
                       f'baseline here' if r_show >= 1.08 else
                       f'This act sits at {ratio(r_show)} this show’s own baseline and '
                       f'{ratio(r_bench)} the benchmark')
            verdict_line = (
                f'{lead_in}, and a cause outside the script sits inside this act '
                f'({causes}), so neither number is a verdict on the writing.')
            tone = 'spend'
        elif r_show >= th['confirm']:
            verdict_line = (f'Listeners left {ratio(r_show)} faster than this show’s own '
                            f'baseline across this act, and {ratio(r_bench)} the '
                            f'benchmark. This act cost something.')
            tone = 'cliff'
        elif r_show >= 1.08 or r_bench >= 1.25:
            verdict_line = (f'Mild. {ratio(r_show)} this show’s baseline and '
                            f'{ratio(r_bench)} the benchmark'
                            + (' — the show’s own rate looks fine here and the '
                               'benchmark does not, which means this act holds its own '
                               'audience while losing ground to what a comparable show '
                               'would keep.' if r_bench >= 1.25 and r_show < 1.08
                               else '.'))
            tone = 'spend'
        else:
            verdict_line = (f'Flat. {ratio(r_show)} this show’s baseline and '
                            f'{ratio(r_bench)} the benchmark. Nothing measurable went '
                            f'wrong here.')
            tone = 'hold'

    stats = ''
    if w:
        cells = [(f'{abs(w["mean_drop"]) * 100:.2f}%', 'drop per episode'),
                 (ratio(w['vs_show']), 'vs this show'),
                 (ratio(w['vs_benchmark']), 'vs benchmark'),
                 (fmt(cost(w)), 'listeners vs baseline'),
                 (str(w['comments']), 'comments')]
        stats = ('<div class="kv" style="margin:2px 0 10px">'
                 + ''.join(f'<div style="min-width:84px"><b style="font-size:18px">'
                           f'{v_}</b><span>{e(l_)}</span></div>' for v_, l_ in cells)
                 + '</div>')

    found = ''
    if hits:
        found = ('<p style="margin:8px 0 0;font-size:12.5px;line-height:1.55">'
                 '<b>Findings inside this act:</b> '
                 + '; '.join(f'<span class="vb {f["verdict"].replace(" ", "")}">'
                             f'{f["verdict"]}</span> {e(f.get("ref") or "")} '
                             f'{e(f["label"])} (eps {f["from"]}–{f["to"]})'
                             for f in hits) + '</p>')

    said = ''
    if themes:
        rows = ''
        for n_, t, inside in themes[:2]:
            q = (t.get('quotes') or [None])[0]
            rows += (f'<div style="margin:7px 0 0;font-size:12.5px;line-height:1.5">'
                     f'<b>{n_} comments</b> · {e(t.get("kind", ""))} · '
                     f'{e(t["theme"])}'
                     + (f'<div class="q" style="margin:4px 0 0">{e(q["text"])}'
                        f'<cite>— ep {q.get("ep", "?")}'
                        + (f', {q["likes"]} likes' if q.get('likes') else '')
                        + '</cite></div>' if q else '') + '</div>')
        said = (f'<div style="margin:10px 0 0"><div class="col-h">What listeners said '
                f'in these episodes</div>{rows}</div>')

    do = ''
    if advice:
        do = (f'<div style="margin:12px 0 0;padding:9px 12px;background:#f3eee4;'
              f'border-radius:4px"><div class="col-h" style="margin-bottom:3px">'
              f'What to do here</div>'
              f'<p style="margin:0;font-size:13px;line-height:1.55">{e(advice)}</p>'
              f'</div>')

    # Hidden from the page, kept in the file. The advice survives on its own, because
    # it is the part of this panel a reader acts on.
    if not SHOW_CONTENT_FIRST:
        if not advice:
            return ''
        return (f'<div class="actx-group"><h4>What to do in this act</h4>'
                f'<div class="aud {tone}" style="max-width:none;margin:0">'
                f'<p style="margin:0;font-size:13.5px;line-height:1.6">'
                f'{e(advice)}</p></div></div>')

    return (f'<div class="actx-group">'
            f'<h4>Content first · did what the script analysis found cost anything</h4>'
            f'<div class="aud {tone}" style="max-width:none;margin:0">'
            f'{stats}'
            f'<p class="aud-ret" style="margin:0">{verdict_line}</p>'
            f'{found}{said}{do}</div></div>')


def inject_act_data(acts_html, acts, data, findings, reads, th, advice_map, mark=False,
                    events=None, reads_by_ep=None, notes_ev=None):
    """Put each act's data panel inside that act's own section.

    The audit renders all twenty acts in one string, and its act numbering and
    cross-act hook lookups depend on seeing the whole list, so the panels cannot be
    produced by calling it once per act. Every section it emits ends with a literal
    `</section>` and none are nested, so splitting on that is exact rather than a
    guess. The split count is asserted against the act count: if the audit's markup
    ever changes, this fails loudly instead of silently attaching panels to the wrong
    acts."""
    parts = acts_html.split('</section>')
    tail = parts.pop()                      # whatever follows the last act
    ordered = sorted(acts, key=lambda a: a['from'])
    assert len(parts) == len(ordered), (
        f'{len(parts)} act sections but {len(ordered)} acts — the audit’s act markup '
        f'changed and the panels would attach to the wrong acts')
    out = []
    for seg, a in zip(parts, ordered):
        # content first: the creative finding, then whether it cost anything
        panel = act_data_panel(a, data, findings, reads, th, advice_map.get(a['id']))
        # data first: what the numbers point at, explained by a blind read
        df = (data_first_block(a, events or {}, reads_by_ep or {}, data,
                               notes_ev or {}, findings)
              if events is not None else '')
        if mark:
            if panel:
                panel = f'<div class="dnew">{panel}</div>'
            if df:
                df = f'<div class="dnew">{df}</div>'
        out.append(seg + panel + df + '</section>')
    return ''.join(out) + tail

# ---------------------------------------------------------------- data-first, per act

EVENT_LABEL = {
    'drop_spike': 'Drop spike',
    'level_step': 'Audience step',
    'completion_dip': 'People stop inside the episode',
    'comment_surge': 'Comment surge',
    'revenue_step': 'Pricing boundary',
}
EVENT_COLOR = {
    'drop_spike': '#9a3b28', 'level_step': '#7a2d5a',
    'completion_dip': '#b07d2b', 'comment_surge': '#3a6ea5',
    'revenue_step': '#5a6b7a',
}


def explains(ev, read, findings=(), data=None):
    """Does the script account for what the data singled out?

    This is a rule, not a judgment, and the page says so. A reader can disagree with
    the rule rather than with a verdict that came from nowhere.

    Order matters. A known non-creative cause wins: an episode inside a paywall or a
    narrator swap is explained by that, whatever else the script is doing, and saying
    otherwise would have this section contradict the verdict table elsewhere in the
    document."""
    if ev['kind'] == 'revenue_step':
        return ('not a story matter', 'strong',
                'A pricing boundary. Nothing in the script causes this and no rewrite '
                'changes it.')
    nc = [f for f in findings
          if f.get('verdict') == 'NOT CREATIVE'
          and f['from'] <= ev['ep'] <= f['to']]
    if nc:
        causes = '; '.join(f'{f["cause"] or "outside the script"}, eps '
                          f'{f["from"]}\u2013{f["to"]}' for f in nc)
        extra = ''
        if read and (read.get('odd') or 'nothing').strip().lower() not in (
                'nothing', 'none', ''):
            extra = (f' The blind read does note something about the episode itself: '
                     f'{read["odd"]} That is worth fixing on craft, but it is not what '
                     f'moved this number.')
        return ('not a story matter', 'strong',
                f'This episode sits inside a stretch with a cause outside the script '
                f'({causes}).{extra}')
    if not read:
        return ('not read', 'none', 'This episode has not been read yet.')

    reasons = []
    if (read.get('odd') or 'nothing').strip().lower() not in ('nothing', 'none', ''):
        reasons.append(f'the episode is structurally unusual: {read["odd"]}')
    if read.get('shape') in ('re-runs', 'digression'):
        reasons.append(f'its shape is \u201c{read["shape"]}\u201d, which is the show '
                       f'marking time rather than moving')
    if read.get('recap_share') == 'lots':
        reasons.append('much of it restates what the listener already knows')
    if read.get('poses_question') is False:
        reasons.append('it ends without posing a question, so nothing pulls the '
                       'listener into the next episode')
    if read.get('lead_role') in ('absent', 'present_passive'):
        reasons.append(f'the lead is {read["lead_role"].replace("_", " ")} in it')

    if len(reasons) >= 2:
        return ('the script explains this', 'strong',
                'Read blind, without being told what the data showed, '
                + '; '.join(reasons) + '.')
    if reasons:
        return ('the script partly explains this', 'partial',
                'Read blind, one thing stands out and no more: ' + reasons[0] + '. '
                'One structural oddity is weaker evidence than several.')
    return ('nothing in the script accounts for it', 'none',
            'Read blind, this episode is ordinary: it escalates, poses a question, the '
            'lead drives it, and it does not lean on recap. Whatever moved the number '
            'is not on the page, which points at delivery, release timing, or noise.')


def data_first_block(act, events, reads_by_ep, data, notes_ev, findings=()):
    """What the numbers single out inside one act, and what reading those episodes found.

    The other direction from the rest of this document: nothing here starts from a
    creative claim. The detectors run on the data alone, then the flagged episodes are
    read blind and the two are put side by side."""
    evs = (events.get(act['id'], {}) or {}).get('events') or []
    if not evs:
        return ('<div class="actx-group">'
                '<h4>Data first · what the numbers single out, read blind</h4>'
                '<div class="aud hold" style="max-width:none;margin:0">'
                '<p class="aud-ret" style="margin:0">Nothing in this act stands out to '
                'any of the five detectors: no drop spike, no step in audience, no '
                'episode people abandon partway through, no comment surge, no pricing '
                'boundary. The data has no question to ask of these episodes.</p>'
                '</div></div>')
    rows = []
    for ev in sorted(evs, key=lambda x: x['ep']):
        read = reads_by_ep.get(ev['ep'])
        verdict, strength, why = explains(ev, read, findings, data)
        override = notes_ev.get(str(ev['ep']))
        col = EVENT_COLOR.get(ev['kind'], '#6b6354')
        cmts = sorted((data['comments'].get(str(ev['ep'])) or []),
                      key=lambda c: -c.get('likes', 0))[:2]
        cm = ''
        if cmts:
            cm = ('<div style="margin:8px 0 0">'
                  + ''.join(f'<div class="q" style="margin:5px 0">{e(c["text"][:300])}'
                            + (f'<cite>{c["likes"]} likes</cite>' if c.get('likes')
                               else '') + '</div>' for c in cmts) + '</div>')
        story = ''
        if read:
            tags = ' · '.join(x for x in [
                read.get('shape'), f'lead {read.get("lead_role", "?")}',
                ('ends on a question' if read.get('poses_question')
                 else 'ends without a question'),
                (f'{read["scene_count"]} scenes' if read.get('scene_count') else ''),
                (f'recap: {read["recap_share"]}' if read.get('recap_share') else ''),
            ] if x)
            story = (f'<p style="margin:7px 0 0;font-size:13px;line-height:1.55">'
                     f'<b>What is on the page:</b> {e(read.get("what_happens", ""))}'
                     f'</p>'
                     + (f'<p style="margin:5px 0 0;font-size:12.5px;line-height:1.5;'
                        f'color:#6b6354"><b>Ends on:</b> '
                        f'{e(read.get("ends_on", ""))}</p>'
                        if read.get('ends_on') else '')
                     + f'<p style="margin:5px 0 0;font-size:11px;color:#8a8173;'
                       f'letter-spacing:.04em;font-family:Helvetica Neue,Arial">'
                       f'{e(tags)}</p>')
        rows.append(
            f'<div style="border-left:3px solid {col};padding:2px 0 2px 13px;'
            f'margin:16px 0">'
            f'<div style="font-family:Helvetica Neue,Arial;font-size:10.5px;'
            f'letter-spacing:.09em;text-transform:uppercase;color:{col};'
            f'font-weight:700">{e(EVENT_LABEL.get(ev["kind"], ev["kind"]))} · '
            f'episode {ev["ep"]}</div>'
            f'<p style="margin:4px 0 0;font-size:13.5px;line-height:1.5">'
            f'<b>The number:</b> {e(ev["what"])}</p>'
            f'{story}{cm}'
            f'<p style="margin:8px 0 0;font-size:12.5px;line-height:1.55;'
            f'padding:7px 10px;background:#f3eee4;border-radius:3px">'
            f'<b>{e(verdict.capitalize())}</b>'
            f'<span style="font-family:Helvetica Neue,Arial;font-size:9.5px;'
            f'letter-spacing:.08em;text-transform:uppercase;color:#8a8173;'
            f'margin-left:7px">evidence: {e(strength)}</span><br>'
            f'{e(override or why)}</p>'
            f'</div>')
    return (f'<div class="actx-group">'
            f'<h4>Data first · what the numbers single out, read blind</h4>'
            f'<div class="readnote" style="margin:2px 0 4px">Nothing below starts from '
            f'the script. Five detectors run on the numbers alone, and the episodes they '
            f'flag were then read by someone who was not told why they had been '
            f'chosen. Where the reading and the number agree, the explanation is '
            f'earned rather than assumed.</div>'
            + ''.join(rows) + '</div>')


# Keep this last. It has been deleted twice by edits that sliced the file between two
# anchors, and a missing entry point fails silently: the script runs, defines
# everything, writes nothing and exits 0. After editing this file, check that the last
# line is still `main()`.

# ============================================================ act section, v2
# Per act: summary · running hooks as tags · content-led problems · data-led
# analysis · data-led problems · what to do. The acts are composed here from the
# audit's three pure joins rather than borrowed as finished HTML, so this document
# can show the same facts in its own shape without touching the audit.

TAG_STYLE = {
    'data':     ('#9a3b28', '#f3e0d9', 'Validated by data'),
    'comments': ('#3a6ea5', '#dde7f2', 'Validated by comments'),
    'story':    ('#8a6d21', '#f3ead0', 'Story may explain'),
    'outside':  ('#5a6b7a', '#e3e8ec', 'Cause outside the script'),
    'none':     ('#6b6354', '#ece5d8', 'Not explained'),
}


def tag(kind, extra=''):
    ink, bg, label = TAG_STYLE[kind]
    return (f'<span class="vtag" style="background:{bg};color:{ink}">'
            f'{e(label)}{e(extra)}</span>')


def sent_for(sentiment, lo, hi):
    """Comment buckets summed across an episode range."""
    out = {k: 0 for k in ('positive', 'negative', 'production', 'money', 'neutral')}
    for n in range(lo, hi + 1):
        row = sentiment.get(str(n))
        if not row:
            continue
        for k in out:
            out[k] += row.get(k, 0) or 0
    out['total'] = sum(out.values())
    return out


def comments_validate(sentiment, base_rate, lo, hi, floor=6):
    """Do listeners themselves mark this stretch as a problem?

    The test is the share of negative comments against the show's own negative share,
    not a raw count: a busy stretch has more of everything. Returns (bool, sentence)."""
    s = sent_for(sentiment, lo, hi)
    n = s['total']
    if n < floor:
        return False, (f'Only {n} comment{"" if n == 1 else "s"} in these episodes, '
                       f'too few to read as a signal.')
    bad = s['negative'] + s['production']
    share = bad / n
    if base_rate and share >= base_rate * 1.5:
        return True, (f'{bad} of {n} comments here are complaints, '
                      f'{share * 100:.0f}% against {base_rate * 100:.0f}% across the '
                      f'show: {share / base_rate:.1f} times the normal rate.')
    return False, (f'{bad} of {n} comments here are complaints, {share * 100:.0f}% '
                   f'against {base_rate * 100:.0f}% across the show. Listeners do not '
                   f'single these episodes out.')


def arc_retention(act, data):
    """Retention across the arc: this show against the benchmark at matched hours,
    both indexed to the first episode of the act."""
    lo, hi = act['from'], act['to']
    eps, bl = data['episodes'], data.get('benchmark_level_at') or {}
    pts = [(n, (eps.get(str(n)) or {}).get('listen'), bl.get(str(n)))
           for n in range(lo, hi + 1)]
    pts = [(n, a, b) for n, a, b in pts if a]
    if len(pts) < 3:
        return ''
    a0 = pts[0][1]
    b0 = next((b for _, _, b in pts if b), None)
    L, W, H = 46.0, 700.0, 104.0
    x = lambda n: L + W * (n - lo) / max(1, hi - lo)
    ys = [a / a0 * 100 for _, a, _ in pts] + (
        [b / b0 * 100 for _, _, b in pts if b] if b0 else [])
    top, bot = max(ys), min(ys)
    pad = max(1.0, (top - bot) * .12)
    top, bot = top + pad, bot - pad
    y = lambda v: H - H * (v - bot) / max(.001, top - bot)
    o = [f'<svg viewBox="0 0 {L + W + 46:.0f} {H + 40:.0f}" width="100%" role="img" '
         f'aria-label="Retention across this act against the benchmark">']
    for v in (bot, (bot + top) / 2, top):
        o.append(f'<line x1="{L}" y1="{y(v):.1f}" x2="{L + W}" y2="{y(v):.1f}" '
                 f'stroke="#e4ddd0" stroke-width="1"/>')
        o.append(f'<text x="{L - 6}" y="{y(v) + 3.5:.1f}" font-size="9" fill="#a49a89" '
                 f'text-anchor="end" font-family="Helvetica Neue,Arial">'
                 f'{v:.0f}%</text>')
    if b0:
        bp = ' '.join(f'{x(n):.1f},{y(b / b0 * 100):.1f}' for n, _, b in pts if b)
        o.append(f'<polyline points="{bp}" fill="none" stroke="#a49a89" '
                 f'stroke-width="1.4" stroke-dasharray="4,3"/>')
    sp = ' '.join(f'{x(n):.1f},{y(a / a0 * 100):.1f}' for n, a, _ in pts)
    o.append(f'<polyline points="{sp}" fill="none" stroke="#9a3b28" '
             f'stroke-width="1.9"/>')
    bw = W / max(1, len(pts))
    for n, a, b in pts:
        body = (f'{a:,.0f} listeners  ·  {a / a0 * 100:.1f}% of this act’s start'
                + (f'  ·  benchmark {b / b0 * 100:.1f}%' if b and b0 else ''))
        o.append(f'<g class="ephit">'
                 f'<rect class="hit" x="{x(n) - bw / 2:.2f}" y="0" '
                 f'width="{max(bw, 1.2):.2f}" height="{H:.1f}"/>'
                 f'<rect class="lbl" x="{L}" y="{H + 6:.1f}" width="{W:.0f}" '
                 f'height="20" rx="3" fill="#1c1a17"/>'
                 f'<text x="{L + 9}" y="{H + 19:.1f}" font-size="10.5" '
                 f'font-family="Helvetica Neue,Arial">'
                 f'<tspan fill="#f4f1ec" font-weight="700">ep {n}</tspan>'
                 f'<tspan fill="#c9bfa8">   {e(body)}</tspan></text></g>')
    o.append(f'<text x="{L}" y="{H + 34:.0f}" font-size="9.5" fill="#8a8173" '
             f'font-family="Helvetica Neue,Arial">solid: this show   ·   '
             f'dashed: benchmark at the same cumulative hours   ·   '
             f'both indexed to episode {lo}</text>')
    o.append('</svg>')
    return ('<figure style="margin:8px 0 2px"><div style="overflow-x:auto">'
            + ''.join(o) + '</div></figure>')


def arc_loss(act, data):
    """Loss across the act, against the benchmark over the same stretch. Two bars and
    the headcount, because this is the number a producer argues about."""
    lo, hi = act['from'], act['to']
    eps, bl = data['episodes'], data.get('benchmark_level_at') or {}
    a0 = (eps.get(str(lo)) or {}).get('listen')
    a1 = (eps.get(str(hi)) or {}).get('listen')
    b0, b1 = bl.get(str(lo)), bl.get(str(hi))
    if not a0 or not a1:
        return ''
    show = (a0 - a1) / a0 * 100
    bench = ((b0 - b1) / b0 * 100) if b0 and b1 else None
    lost = a0 - a1
    per = (data.get('level') or {}).get('per_episode_decline') or 0
    expected = a0 - a0 * (1 - per) ** (hi - lo)
    excess = lost - expected
    W = 300.0
    top = max(show, bench or 0, 1) * 1.15
    def bar(v, col, label, sub):
        return (f'<div style="margin:5px 0">'
                f'<div style="display:flex;justify-content:space-between;'
                f'font-size:11px;color:#6b6354;font-family:Helvetica Neue,Arial">'
                f'<span>{e(label)}</span><span>{v:.1f}%</span></div>'
                f'<div style="height:9px;background:#ece5d8;border-radius:3px;'
                f'overflow:hidden"><i style="display:block;height:100%;'
                f'width:{min(v / top * 100, 100):.1f}%;background:{col}"></i></div>'
                f'<div style="font-size:10.5px;color:#a49a89;margin-top:2px">'
                f'{e(sub)}</div></div>')
    bars = bar(show, '#9a3b28', 'this show', f'{lost:,.0f} listeners over {hi - lo + 1} '
                                            f'episodes')
    if bench is not None:
        bars += bar(bench, '#a49a89', 'benchmark',
                    'the same cumulative hours of a comparable title')
    verdict = ('worse than the benchmark' if bench is not None and show > bench * 1.1
               else 'better than the benchmark' if bench is not None and show * 1.1 < bench
               else 'level with the benchmark' if bench is not None else '')
    return (f'<div style="display:grid;grid-template-columns:1fr 220px;gap:22px;'
            f'align-items:start;margin:10px 0 2px">'
            f'<div style="max-width:{W:.0f}px">{bars}</div>'
            f'<div><div class="dfstat" style="font-family:Helvetica Neue,Arial;'
            f'font-size:22px;font-weight:600">{excess:+,.0f}</div>'
            f'<div style="font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;'
            f'color:#8a8173;font-family:Helvetica Neue,Arial">listeners above or below '
            f'what this act should have cost</div>'
            + (f'<div style="font-size:11.5px;color:#6b6354;margin-top:6px">'
               f'{e(verdict)}</div>' if verdict else '')
            + f'</div></div>')


def arc_reaction(act, data, sentiment):
    """What listeners felt, episode by episode across the act. Positive above the line,
    complaints below, so the shape of the act's reception is readable at a glance."""
    lo, hi = act['from'], act['to']
    rows = []
    for n in range(lo, hi + 1):
        r = sentiment.get(str(n))
        if r:
            rows.append((n, r))
    if not rows:
        return ('<div class="dfsub" style="margin:6px 0 2px">No comments were left on '
                'these episodes, so there is no reaction to read here.</div>')
    L, W, H = 46.0, 700.0, 46.0
    top = max(max(r.get('positive', 0) for _, r in rows),
              max(r.get('negative', 0) + r.get('production', 0) + r.get('money', 0)
                  for _, r in rows), 1)
    x = lambda n: L + W * (n - lo) / max(1, hi - lo)
    bw = max(1.4, W / max(1, hi - lo + 1) - .6)
    o = [f'<svg viewBox="0 0 {L + W + 46:.0f} {H * 2 + 34:.0f}" width="100%" '
         f'role="img" aria-label="Listener reaction across this act">']
    o.append(f'<line x1="{L}" y1="{H:.1f}" x2="{L + W}" y2="{H:.1f}" '
             f'stroke="#cdc5b6" stroke-width="1"/>')
    for n, r in rows:
        p = r.get('positive', 0)
        neg = r.get('negative', 0)
        prod = r.get('production', 0) + r.get('money', 0)
        if p:
            o.append(f'<rect x="{x(n) - bw / 2:.2f}" y="{H - H * p / top:.2f}" '
                     f'width="{bw:.2f}" height="{H * p / top:.2f}" fill="#3d6b3f" '
                     f'opacity=".85"/>')
        yy = H
        for v, col in ((neg, '#9a3b28'), (prod, '#5a6b7a')):
            if v:
                bh = H * v / top
                o.append(f'<rect x="{x(n) - bw / 2:.2f}" y="{yy:.2f}" '
                         f'width="{bw:.2f}" height="{bh:.2f}" fill="{col}" '
                         f'opacity=".85"/>')
                yy += bh
    for n, r in rows:
        tot = sum(r.get(k, 0) for k in
                  ('positive', 'negative', 'production', 'money', 'neutral'))
        body = (f'{tot} comments  ·  {r.get("positive", 0)} positive, '
                f'{r.get("negative", 0)} negative about the story, '
                f'{r.get("production", 0)} production, {r.get("money", 0)} money, '
                f'{r.get("neutral", 0)} neutral')
        o.append(f'<g class="ephit">'
                 f'<rect class="hit" x="{x(n) - bw / 2 - .3:.2f}" y="0" '
                 f'width="{bw + .6:.2f}" height="{H * 2:.1f}"/>'
                 f'<rect class="lbl" x="{L}" y="{H * 2 + 2:.1f}" width="{W:.0f}" '
                 f'height="19" rx="3" fill="#1c1a17"/>'
                 f'<text x="{L + 9}" y="{H * 2 + 14.5:.1f}" font-size="10.5" '
                 f'font-family="Helvetica Neue,Arial">'
                 f'<tspan fill="#f4f1ec" font-weight="700">ep {n}</tspan>'
                 f'<tspan fill="#c9bfa8">   {e(body)}</tspan></text></g>')
    o.append(f'<text x="{L - 6}" y="{H / 2:.1f}" font-size="9" fill="#3d6b3f" '
             f'text-anchor="end" font-family="Helvetica Neue,Arial">liked</text>')
    o.append(f'<text x="{L - 6}" y="{H * 1.5:.1f}" font-size="9" fill="#9a3b28" '
             f'text-anchor="end" font-family="Helvetica Neue,Arial">complained</text>')
    o.append(f'<text x="{L}" y="{H * 2 + 30:.0f}" font-size="9.5" fill="#8a8173" '
             f'font-family="Helvetica Neue,Arial">green: enjoying it   ·   '
             f'red: unhappy with the story   ·   slate: narration, audio or price   '
             f'·   neutral comments are not drawn</text>')
    o.append('</svg>')
    return ('<figure style="margin:8px 0 2px"><div style="overflow-x:auto">'
            + ''.join(o) + '</div></figure>')


def card(title, tags, meta, body, open_=False):
    """A collapsed card showing title and tags; the evidence is inside. Native
    <details>, so it works with no JavaScript."""
    return (f'<details class="pcard"{" open" if open_ else ""}>'
            f'<summary><span class="pc-title">{title}</span>'
            f'<span class="pc-tags">{tags}</span>'
            + (f'<span class="pc-meta">{e(meta)}</span>' if meta else '')
            + f'</summary><div class="pc-body">{body}</div></details>')


def content_problems(act, m, findings, sentiment, base_neg, data):
    """Narrative drift and broken promises inside this act, each with the evidence that
    validates it. Tags are visible collapsed; the proof is inside."""
    lo, hi = act['from'], act['to']
    arc = {'from': lo, 'to': hi, 'id': act['id'], 'name': act.get('name', '')}
    zones = m.drift_in(arc, m.DRIFT)
    brks = m.breaks_in(arc, m.BREAKS)
    if not zones and not brks:
        return ('<p class="dfsub" style="margin:4px 0 0">No narrative drift and no '
                'broken promises were found in this act.</p>')

    def find_for(ref):
        return next((f for f in findings if f.get('ref') == ref), None)

    out = []
    for d in zones:
        ref = f'D{d.get("_n", "")}'
        f_ = find_for(ref)
        a0, b0 = d['eps']
        tags, body = '', ''
        # data
        if f_ and f_['verdict'] == 'CONFIRMED':
            tags += tag('data')
            body += (f'<div class="pc-h">The data that validates it</div>'
                     f'<div class="kv" style="margin:4px 0 10px">'
                     f'<div><b>{ratio(f_["vs_show"])}</b><span>this show’s baseline'
                     f'</span></div>'
                     f'<div><b>{ratio(f_["vs_benchmark"])}</b><span>the benchmark'
                     f'</span></div>'
                     f'<div><b>{fmt(f_.get("level_excess") or 0)}</b>'
                     f'<span>listeners above what it should cost</span></div>'
                     f'<div><b>{f_["n"]}</b><span>episodes measured</span></div></div>'
                     f'<p class="dfcap">Measured across eps {f_["from"]}–{f_["to"]}, '
                     f'listeners left {ratio(f_["vs_show"])} faster than this show’s '
                     f'own rate from episode 51 onward, and {ratio(f_["vs_benchmark"])} '
                     f'the benchmark at the same cumulative hours.</p>')
        elif f_ and f_['verdict'] == 'NOT CREATIVE':
            tags += tag('outside')
            body += (f'<div class="pc-h">Why this is not a writing problem</div>'
                     + ''.join(f'<p class="dfcap">{e(x)}</p>'
                               for x in (f_.get('cause_evidence') or [])))
        # comments
        okc, why = comments_validate(sentiment, base_neg, a0, b0)
        if okc:
            tags += tag('comments')
        body += (f'<div class="pc-h">What listeners said</div>'
                 f'<p class="dfcap">{e(why)}</p>')
        if not tags:
            tags = tag('none')
            body += (f'<div class="pc-h">Not explained</div>'
                     f'<p class="dfcap">This reads as a problem in the script, and '
                     f'neither the retention numbers nor the comments single these '
                     f'episodes out. It may still be worth fixing on craft. We are not '
                     f'sure it cost anything.</p>')
        body += (f'<div class="pc-h">What the script analysis says</div>'
                 f'<p class="dfcap">{e(d.get("story") or "")}</p>'
                 + (f'<p class="dfcap" style="color:#6b6354">'
                    f'{e(d.get("evidence") or "")}</p>' if d.get('evidence') else ''))
        out.append(card(f'{e(d["signal"])}', tags,
                        f'eps {a0}–{b0} · {d["_inside"]} of this act’s {d["_span"]} '
                        f'episodes · {e(d["severity"])}', body))

    for b in brks:
        n_ = b.get('_n', '')
        f_ = find_for(f'B{n_}')
        tags, body = '', ''
        if f_ and f_['verdict'] == 'CONFIRMED':
            tags += tag('data')
            body += (f'<div class="pc-h">The data that validates it</div>'
                     f'<div class="kv" style="margin:4px 0 10px">'
                     f'<div><b>{ratio(f_["vs_show"])}</b><span>this show’s baseline'
                     f'</span></div>'
                     f'<div><b>{ratio(f_["vs_benchmark"])}</b><span>the benchmark'
                     f'</span></div>'
                     f'<div><b>{fmt(f_.get("level_excess") or 0)}</b>'
                     f'<span>listeners above baseline</span></div></div>')
        elif f_ and f_['verdict'] == 'NO COST':
            body += (f'<div class="pc-h">What the data says</div>'
                     f'<p class="dfcap">Measured across eps {f_["from"]}–{f_["to"]}, '
                     f'this sits at {ratio(f_["vs_show"])} the show’s own baseline. '
                     f'The break is real in the script and cost nothing measurable '
                     f'here. Late in a run that is weak evidence either way: the '
                     f'audience still listening will finish almost anything.</p>')
        bl_, bp = b['broke'][1], b['promised'][1]
        okc, why = comments_validate(sentiment, base_neg, max(bl_ - 3, 1), bl_ + 3)
        if okc:
            tags += tag('comments')
        body += (f'<div class="pc-h">What listeners said</div>'
                 f'<p class="dfcap">{e(why)}</p>')
        if not tags:
            tags = tag('none')
        body += (f'<div class="pc-h">The promise and the withdrawal</div>'
                 f'<p class="dfcap">{e(b.get("what", ""))}</p>'
                 f'<p class="dfcap" style="color:#6b6354">Promised at episode {bp}, '
                 f'broken at episode {bl_}.</p>')
        out.append(card(e(b.get('title', '')), tags,
                        f'{b.get("code", "")} · broken at ep {bl_}', body))
    return ''.join(out)


def data_problems(act, events, reads_by_ep, data, findings, sentiment, base_neg,
                  notes_ev):
    """What the numbers singled out in this act, validated against comments and story.

    Story evidence never reads as "validated": it is an explanation, not proof, and an
    event nothing explains says so rather than being handed a cause."""
    evs = (events.get(act['id'], {}) or {}).get('events') or []
    if not evs:
        return ('<p class="dfsub" style="margin:4px 0 0">Nothing in this act stands out '
                'to any of the five detectors: no drop spike, no step in audience, no '
                'episode people abandon partway through, no comment surge, no pricing '
                'boundary.</p>')
    out = []
    for i, ev in enumerate(sorted(evs, key=lambda x: x['ep']), 1):
        ep_ = ev['ep']
        read = reads_by_ep.get(ep_)
        nc = [f for f in findings if f.get('verdict') == 'NOT CREATIVE'
              and f['from'] <= ep_ <= f['to']]
        tags, body = '', ''
        body += (f'<div class="pc-h">The number</div>'
                 f'<p class="dfcap">{e(ev["what"])}</p>')
        if ev['kind'] == 'revenue_step' or nc:
            tags += tag('outside')
        okc, why = comments_validate(sentiment, base_neg, max(ep_ - 2, 1), ep_ + 2,
                                     floor=4)
        if okc:
            tags += tag('comments')
        s_ = sent_for(sentiment, max(ep_ - 2, 1), ep_ + 2)
        row = sentiment.get(str(ep_)) or {}
        quotes = ''
        for k, lbl in (('top_negative', 'the loudest complaint'),
                       ('top_positive', 'the loudest praise')):
            if row.get(k):
                quotes += (f'<div class="q" style="margin:5px 0">{e(row[k])}'
                           f'<cite>— ep {ep_}, {lbl}</cite></div>')
        body += (f'<div class="pc-h">What listeners said</div>'
                 f'<p class="dfcap">{e(why)}</p>{quotes}')
        if read:
            odd = (read.get('odd') or 'nothing').strip()
            has_odd = odd.lower() not in ('nothing', 'none', '')
            if has_odd or read.get('poses_question') is False \
                    or read.get('lead_role') in ('absent', 'present_passive') \
                    or read.get('shape') in ('re-runs', 'digression') \
                    or read.get('recap_share') == 'lots':
                if 'Cause outside' not in tags:
                    tags += tag('story')
            chips = ''.join(f'<span class="chip {k}">{e(t)}</span>'
                            for k, t in read_chips(read))
            body += (f'<div class="pc-h">The story at this episode, read blind</div>'
                     f'<p class="dfcap">{e(read.get("what_happens", ""))}</p>'
                     + (f'<p class="dfcap" style="color:#6b6354"><b>Ends on:</b> '
                        f'{e(read.get("ends_on", ""))}</p>' if read.get('ends_on')
                        else '')
                     + (f'<p class="dfcap"><b>What is unusual about it:</b> {e(odd)}</p>'
                        if has_odd else '')
                     + f'<div class="chips">{chips}</div>'
                     + f'<p class="dfsub" style="margin-top:7px">The episode was read '
                       f'without telling the reader why it had been chosen. This is an '
                       f'explanation, not proof: it is a judgment about a script, and '
                       f'the word validated is not used for it.</p>')
        if not tags:
            tags = tag('none')
            body += (f'<div class="pc-h">Not explained</div>'
                     f'<p class="dfcap">The number is real and neither the comments nor '
                     f'a blind read of the episode accounts for it. We are not sure why '
                     f'this happened, and nothing in the script is being blamed for '
                     f'it.</p>')
        if notes_ev.get(str(ep_)):
            body += f'<p class="dfcap"><b>Note.</b> {e(notes_ev[str(ep_)])}</p>'
        out.append(card(f'Problem {i} · {e(EVENT_LABEL.get(ev["kind"], ev["kind"]))}',
                        tags, f'episode {ep_}', body))
    return ''.join(out)


def hook_tags(act, m, health, last):
    """Running hooks as tags. Which questions this act carries, opens and answers,
    stated plainly and not scored. Informational, per the brief for this section."""
    arc = {'from': act['from'], 'to': act['to'], 'id': act['id'],
           'name': act.get('name', '')}
    st = m.hooks_in(arc, m.HOOKS, health, last)
    groups = [('started_open', 'Opens here, still open', '#9a3b28', '#f3e0d9'),
              ('started_closed', 'Opens and closes here', '#2f5a32', '#e2ebe1'),
              ('carried_open', 'Carried in, still open', '#8a6d21', '#f3ead0'),
              ('carried_closed', 'Carried in, answered here', '#2f5a32', '#e2ebe1')]
    out = ''
    for key, label, ink, bg in groups:
        items = st.get(key) or []
        if not items:
            continue
        tags = ''
        for h, n in items:
            q = h.get('q') or h.get('question') or h['code']
            touched = ('' if n is None else
                       f' · touched in {n} of {act["to"] - act["from"] + 1}')
            tags += (f'<span class="htag" style="background:{bg};color:{ink}">'
                     f'<b>{e(h["code"])}</b> {e(q)}'
                     f'<span style="opacity:.7">{e(touched)}</span></span>')
        out += (f'<div style="margin:9px 0 0"><div class="pc-h" '
                f'style="margin-bottom:5px">{e(label)}</div>'
                f'<div class="htags">{tags}</div></div>')
    if not out:
        return ('<p class="dfsub" style="margin:4px 0 0">No question opens, closes or '
                'is carried through this act.</p>')
    return out


def act_section_v2(act, i, m, data, findings, events, reads_by_ep, sentiment,
                   base_neg, health, last, advice, notes_ev, mark=False):
    """One act, in the shape the brief asks for.

    Summary · hooks as tags · content-led problems · data-led analysis · data-led
    problems · what to do. Composed from the audit's three pure joins, so this can
    change without the audit changing."""
    arc = {'from': act['from'], 'to': act['to'], 'id': act['id'],
           'name': act.get('name', '')}
    wrap = (lambda h: f'<div class="dnew">{h}</div>') if mark else (lambda h: h)

    sec = f'<section class="actx" id="act-{i}" style="scroll-margin-top:18px">'
    sec += m.act_shell(arc, i, m.ACT_STORIES)

    sec += (f'<div class="actx-group"><h4>Hook and content led analysis</h4>'
            f'<div class="dfsub" style="margin:0 0 2px">The questions running through '
            f'this act. Informational: nothing here is a problem by itself.</div>'
            f'{hook_tags(act, m, health, last)}</div>')

    sec += wrap(f'<div class="actx-group"><h4>Content led problems</h4>'
                f'<div class="dfsub" style="margin:0 0 8px">Narrative drift and broken '
                f'promises found by reading the scripts. Open a card for the evidence '
                f'behind its tags.</div>'
                f'{content_problems(act, m, findings, sentiment, base_neg, data)}'
                f'</div>')

    sec += wrap(f'<div class="actx-group"><h4>Data led analysis</h4>'
                f'<div class="pc-h" style="margin:6px 0 0">Retention across the act, '
                f'against the benchmark</div>{arc_retention(act, data)}'
                f'<div class="pc-h" style="margin:14px 0 0">Loss across the act</div>'
                f'{arc_loss(act, data)}'
                f'<div class="pc-h" style="margin:14px 0 0">Listener reaction, episode '
                f'by episode</div>{arc_reaction(act, data, sentiment)}</div>')

    sec += wrap(f'<div class="actx-group"><h4>Data led problems</h4>'
                f'<div class="dfsub" style="margin:0 0 8px">Found by five detectors '
                f'running on the numbers alone, with no reference to the script. Where '
                f'a card says the story may explain it, that is an explanation and not '
                f'proof.</div>'
                f'{data_problems(act, events, reads_by_ep, data, findings, sentiment, base_neg, notes_ev)}'
                f'</div>')

    if advice:
        sec += wrap(f'<div class="actx-group"><h4>What to do in this act</h4>'
                    f'<div class="aud hold" style="max-width:none;margin:0">'
                    f'<p style="margin:0;font-size:13.5px;line-height:1.6">'
                    f'{e(advice)}</p></div></div>')
    return sec + '</section>'


def read_chips(read):
    """The blind read compressed to signals, so the page carries facts not paragraphs."""
    if not read:
        return []
    c = []
    lr = read.get('lead_role')
    if lr in ('absent', 'present_passive'):
        c.append(('warn', 'lead ' + lr.replace('_', ' ')))
    elif lr:
        c.append(('ok', 'lead ' + lr.replace('_', ' ')))
    if read.get('poses_question') is False:
        c.append(('warn', 'ends without a question'))
    elif read.get('poses_question'):
        c.append(('ok', 'ends on a question'))
    if read.get('recap_share') == 'lots':
        c.append(('warn', 'mostly recap'))
    elif read.get('recap_share'):
        c.append(('', f'recap: {read["recap_share"]}'))
    if read.get('shape'):
        c.append(('warn' if read['shape'] in ('re-runs', 'digression') else '',
                  read['shape']))
    sc = read.get('scene_count')
    if sc:
        c.append(('warn' if sc <= 1 else '',
                  f'{sc} scene' + ('' if sc == 1 else 's')))
    return c


def show_negative_rate(sentiment):
    """The show's own complaint share, so a stretch is compared with its own normal."""
    tot = bad = 0
    for row in (sentiment or {}).values():
        n = sum(row.get(k, 0) or 0 for k in
                ('positive', 'negative', 'production', 'money', 'neutral'))
        tot += n
        bad += (row.get('negative', 0) or 0) + (row.get('production', 0) or 0)
    return (bad / tot) if tot else 0.0


# Keep this last. It has been deleted twice by edits that sliced the file between two
# anchors, and a missing entry point fails silently: the script runs, defines
# everything, writes nothing and exits 0. After editing this file, check that the last
# line is still `main()`.
if __name__ == '__main__':
    main()

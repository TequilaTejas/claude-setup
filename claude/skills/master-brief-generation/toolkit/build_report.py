# -*- coding: utf-8 -*-
"""
build_report.py — STEP 2. A working skeleton for the cliff-report HTML.

Reads analysis.json (from analyse.py), draws both charts from the real numbers,
and lays out the two-column acts correctly. YOU supply the story: fill in CAST,
ACTS, LOGLINE, LEAD and the stitch text after reading the summaries.

    python build_report.py --pack ./pack --title "The Vampire Prince" --out report.html

Then ALWAYS validate:
    python -c "from html.parser import HTMLParser as H,re;s=open('report.html').read();H().feed(s)"
and open it in a browser to confirm the two columns actually render.
"""
import argparse, json, os, re

def esc(t): return str(t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ----------------------------------------------------------------- FILL THESE IN
LOGLINE = "ONE PARAGRAPH: the premise as if to a first-time reader."
LEAD    = "THE HEADLINE FINDING: where it holds, where it breaks, and the survival number."
CHECKED = ("Data corrections made before this read: … "
           "(list any corrupt LDAU rows and any paywall boundary found).")
CAST = [("Character", "One line on who they are and what they do in the show."),]
# (num, title, "Episodes A–B", css_class, [story paragraphs], status, panel_text, [(quote, ep)])
ACTS = [("1", "Act title", "Episodes 1–30", "hold",
         ["Story paragraph. Story ONLY - no evaluation, that goes in the panel.",
          "Second paragraph. Aim for 3-4 paragraphs, ~900-1200 characters total."],
         "What the audience did here, in a few words",
         "The retention read for this act, with the ratio and what it means.",
         [("a real listener comment", 171)]),]
STITCH_H2 = "Cut before X — and keep Y"
STITCH_CARDS = [("1 · Cut at ~ep N (recommended)", "Why here, and what the continuation must do."),
                ("2 · Or cut at ~ep M (alternative)", "The fallback and what it costs.")]
STITCH_NOTE = "<b>The three rules for the continuation:</b> …"
# --------------------------------------------------------------------------------

def svg(blocks, levels, title):
    X0, X1, TY0, TY1 = 64, 690, 44, 296
    eps = sorted(int(k) for k in levels)
    lo, hi = eps[0], eps[-1]
    X = lambda e: X0 + (e - lo) / max(hi - lo, 1) * (X1 - X0)
    base = levels[str(lo)]
    CY = lambda v: TY1 - (v / 100) * (TY1 - TY0)
    g = "".join(
        f'<line x1="{X0}" y1="{CY(v):.0f}" x2="{X1}" y2="{CY(v):.0f}" stroke="#ece5d8"/>'
        f'<text x="{X0-8}" y="{CY(v)+3:.0f}" text-anchor="end" font-size="9" fill="#9a9080">{v}%</text>'
        for v in (100, 80, 60, 40, 20))
    pts = " ".join(f"{X(e):.1f},{CY(100*levels[str(e)]/base):.1f}" for e in eps)
    curve = (g + f'<polyline points="{pts}" fill="none" stroke="#1c1a17" stroke-width="2.4"/>'
             f'<text x="{X0}" y="{TY0-20}" font-size="10.5" fill="#6b6357">'
             f'% of the ep-{lo} audience still listening</text>')
    BY0, BY1, rmax = 340, 426, 3.0
    BY = lambda v: BY1 - min(v, rmax) / rmax * (BY1 - BY0)
    bg = "".join(
        f'<line x1="{X0}" y1="{BY(v):.0f}" x2="{X1}" y2="{BY(v):.0f}" stroke="#ece5d8"/>'
        f'<text x="{X0-8}" y="{BY(v)+3:.0f}" text-anchor="end" font-size="9" fill="#9a9080">{v}\u00d7</text>'
        for v in (1, 2, 3))
    bars = ""
    for b in blocks:
        if not b.get("ratio"): continue
        x = X(b["ep_lo"]); w = max(3, (X(b["ep_hi"]) - X(b["ep_lo"])) * 0.85)
        art = str(b.get("type", "")).startswith("ARTIFACT")
        col = "#8a6d3b" if art else ("#c1523a" if b["ratio"] >= 1.6
              else ("#cba83f" if b["ratio"] >= 1.3 else "#9bb59a"))
        bars += (f'<rect x="{x:.0f}" y="{BY(b["ratio"]):.1f}" width="{w:.0f}" '
                 f'height="{BY1-BY(b["ratio"]):.1f}" fill="{col}"/>')
        if b["ratio"] > rmax:
            bars += (f'<text x="{x+w/2:.0f}" y="{BY0-3:.0f}" text-anchor="middle" '
                     f'font-size="8" fill="#8a6d3b" font-weight="700">{b["ratio"]:.1f}\u00d7</text>')
    bars += (f'<line x1="{X0}" y1="{BY(1.0):.0f}" x2="{X1}" y2="{BY(1.0):.0f}" '
             f'stroke="#3d6b3f" stroke-width="1.3" stroke-dasharray="5 3"/>'
             f'<text x="{X0}" y="{BY0-6:.0f}" font-size="10.5" fill="#6b6357">'
             f'drop-rate vs benchmark per block (green = benchmark pace; brown = artifact, not story)</text>')
    return (f'<svg viewBox="0 0 700 452" xmlns="http://www.w3.org/2000/svg" '
            f'style="width:100%;height:auto">{curve}{bg}{bars}</svg>')

def evidence_table(blocks):
    rows = ""
    for b in blocks:
        if not b.get("ratio") or b["ratio"] < 1.3: continue
        art = str(b.get("type", "")).startswith("ARTIFACT")
        rows += (f'<tr class="{"flag" if not art else ""}"><td class="c">{b["ep_lo"]}\u2013{b["ep_hi"]}</td>'
                 f'<td class="c">{b["ratio"]}\u00d7</td>'
                 f'<td class="bt">FILL IN: what is happening in the story here.</td>'
                 f'<td>{esc(b.get("type",""))}</td></tr>')
    return ('<table><thead><tr><th>Episodes</th><th>vs benchmark</th>'
            '<th>What is happening in the story</th><th>Type</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True); ap.add_argument("--title", required=True)
    ap.add_argument("--css", default="house.css"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    A = json.load(open(os.path.join(a.pack, "analysis.json")))
    CSS = open(a.css).read() + (
        ".story .col-h{font-family:'Helvetica Neue',Arial,sans-serif;font-size:10.5px;"
        "letter-spacing:.14em;text-transform:uppercase;color:#a49a89;font-weight:700;margin-bottom:9px}"
        ".story p{font-size:15px;line-height:1.62;color:#2a2620;margin:0 0 12px}"
        ".aud{border-left:3px solid #c9bfa8}"
        ".readnote{background:#f6f2e9;border:1px solid #e0d8c8;border-radius:9px;padding:13px 16px;"
        "margin:10px 0 22px;font-size:13.5px;color:#4a443b;line-height:1.55}"
        "table{width:100%;border-collapse:collapse;margin:14px 0;font-size:13.5px}"
        "thead th{text-align:left;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;"
        "color:#8a8175;font-weight:700;border-bottom:1.5px solid #ded7ca;padding:7px 9px}"
        "tbody td{padding:8px 9px;border-bottom:1px solid #ece5d8;vertical-align:top}"
        "td.c{text-align:center;font-family:ui-monospace,Menlo,monospace;font-size:12.5px}"
        "tr.flag{background:#f8eee4}"
        "@media(max-width:820px){.act-body{grid-template-columns:1fr}.aud{position:static}}")
    cast = "".join(f'<div class="castrow"><div class="castname">{esc(n)}</div>'
                   f'<div class="castbio">{d}</div></div>' for n, d in CAST)
    acts = ""
    for num, title, eps, cls, paras, status, ret, quotes in ACTS:
        body = "".join(f"<p>{p}</p>" for p in paras if p and p.strip())
        cm = ""
        if quotes:
            cm = ('<div class="cmts"><div class="cmts-h">In their words</div>' +
                  "".join(f'<blockquote>{esc(q)}<cite>\u2014 ep {e}</cite></blockquote>'
                          for q, e in quotes) + '</div>')
        acts += (f'<section class="act"><div class="act-head">'
                 f'<span class="act-num">Act {num}</span><h3>{esc(title)}</h3>'
                 f'<span class="act-eps">{esc(eps)}</span></div>'
                 f'<div class="act-body"><div class="story">'
                 f'<div class="col-h">What happens in the story</div>{body}</div>'
                 f'<aside class="aud {cls}"><div class="aud-h">The audience here</div>'
                 f'<div class="aud-status">{status}</div>'
                 f'<p class="aud-ret">{ret}</p>{cm}</aside></div></section>')
    cards = "".join(f'<div class="card"><h3>{esc(h)}</h3><p class="big">{t}</p></div>'
                    for h, t in STITCH_CARDS)
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(a.title)} \u2014 Story &amp; Diagnosis</title><style>{CSS}</style></head>
<body><div class="wrap">
<div class="eyebrow">Creative Team Brief \u00b7 Story &amp; Diagnosis \u00b7 Master</div>
<h1>{esc(a.title)}</h1>
<p class="sub">The whole story, told for a first-time reader \u2014 and where it loses its audience</p>
<p class="meta">Story from a full read of the summaries \u00b7 retention read hour-for-hour vs The Alpha's Bride (TAB)</p>
<div class="rule"></div>
<p class="logline">{LOGLINE}</p>
<div class="sec"><div class="secn">Who's who</div>{cast}</div>
<div class="sec"><div class="secn">The problem, in one line</div>
<div class="lead">{LEAD}</div>
<div class="note"><b>Checked, not assumed.</b> {CHECKED}</div></div>
<span class="part">Part I \u00b7 The story, in full</span>
<div class="sec"><div class="secn">How the story progresses</div>
<div class="readnote"><b>How to read this section.</b> The left column is <b>the story only</b>.
The panel on the right is <b>the diagnosis</b> \u2014 what the audience did there, on the numbers.</div>
{acts}</div>
<span class="part">Part II \u00b7 Why it breaks</span>
<div class="sec"><div class="secn">What the audience did \u2014 on the numbers</div>
<figure>{svg(A['blocks'], A['levels'], a.title)}<figcaption>Top: level curve.
Bottom: drop-rate vs benchmark per block. Brown blocks are artifacts, not story.</figcaption></figure></div>
<div class="sec"><div class="secn">Every flagged block \u2014 the evidence table</div>
{evidence_table(A['blocks'])}</div>
<span class="part">Part III \u00b7 What to do</span>
<div class="sec"><div class="secn">The stitch</div><h2>{esc(STITCH_H2)}</h2>
<div class="two">{cards}</div><div class="note">{STITCH_NOTE}</div></div>
</div></body></html>"""
    open(a.out, "w").write(html)
    from html.parser import HTMLParser
    HTMLParser().feed(html)
    bad = re.findall(r"&(?!amp;|lt;|gt;|quot;|#\d+;|nbsp;|#x[0-9a-fA-F]+;)", html)
    print(f"wrote {a.out} ({len(html)} chars) | parses OK | unescaped &: {len(bad)}")
    if bad: print("   FIX THESE - unescaped ampersands break rendering")

if __name__ == "__main__":
    main()

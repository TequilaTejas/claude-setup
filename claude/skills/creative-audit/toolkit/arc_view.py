GREEN, AMBER, RED, GREY = "#3d6b3f", "#8a6d21", "#9a3b28", "#c9c2b4"
BAND = {2: GREEN, 1: AMBER, 0: RED}
LIVE_WINDOW = 10


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _alive_in(hook, lo, hi):
    """Did the show actually raise this hook inside this arc?"""
    return any(lo <= t <= hi for t in hook.get("touch_eps") or [])


def _open_in(hook, lo, hi, last):
    """Was it unanswered at any point inside this arc?"""
    op = hook["opens"]
    cl = hook.get("resolves") or last
    return op <= hi and cl >= lo


def stack(transit, health, episodes, promise_text):
    """A grid, not a timeline. One row per hook, one cell per arc.

    Two states only, so there is nothing to memorise:
      solid  the show is actively raising it in this arc
      faint  unanswered, but the show is not mentioning it
    """
    arcs = sorted(transit["arcs"], key=lambda a: a["from"])
    last = transit.get("last_ep") or max(a["to"] for a in arcs)
    hooks = sorted(health["hooks"], key=lambda h: h["opens"])
    scored = [e for e in episodes
              if isinstance((e.get("cliff") or {}).get("alignment"), int)]

    L, W = 232.0, 610.0
    ARC_Y, ARC_H, ROW, GAP = 40.0, 30.0, 22.0, 3.0
    HOOK_Y = ARC_Y + ARC_H + 12
    END_Y = HOOK_Y + ROW * len(hooks) + 16
    H = (END_Y + 46) if scored else (END_Y + 16)

    # each arc gets width in proportion to its episodes
    total = sum(a["to"] - a["from"] + 1 for a in arcs)
    xs, run = {}, L
    for a in arcs:
        w = W * (a["to"] - a["from"] + 1) / total
        xs[a["id"]] = (run, w)
        run += w

    o = [f'<svg viewBox="0 0 900 {H:.0f}" width="100%" role="img" '
         f'aria-label="Which arcs keep each hook alive">']

    # promise, on one line above everything
    pt = promise_text.strip()
    if len(pt) > 128:
        pt = pt[:128].rsplit(" ", 1)[0] + "\u2026"
    o.append(f'<text x="10" y="18" font-size="8.5" fill="#a49a89" '
             f'font-family="Helvetica Neue,Arial" letter-spacing=".08em">'
             f'PROMISED</text>')
    o.append(f'<text x="76" y="18" font-size="10.5" fill="#3a352e" '
             f'font-family="Georgia,serif">{esc(pt)}</text>')

    # arc headers
    for a in arcs:
        x0, w = xs[a["id"]]
        o.append(f'<rect x="{x0:.1f}" y="{ARC_Y}" width="{w - 2:.1f}" height="{ARC_H}" '
                 f'fill="#efe9db" rx="3"/>')
        if w > 46:
            o.append(f'<text x="{x0 + w / 2 - 1:.1f}" y="{ARC_Y + 13}" font-size="9" '
                     f'fill="#2a2620" text-anchor="middle" font-family="Georgia,serif">'
                     f'{esc(a.get("name", a["id"])[:18])}</text>')
            o.append(f'<text x="{x0 + w / 2 - 1:.1f}" y="{ARC_Y + 24}" font-size="7.5" '
                     f'fill="#a49a89" text-anchor="middle" '
                     f'font-family="Helvetica Neue,Arial">{a["from"]}\u2013{a["to"]}</text>')
        else:
            o.append(f'<text x="{x0 + w / 2 - 1:.1f}" y="{ARC_Y + 19}" font-size="8" '
                     f'fill="#6b6357" text-anchor="middle" '
                     f'font-family="Helvetica Neue,Arial">{esc(a["id"])}</text>')

    # one row per hook, one cell per arc
    for i, h in enumerate(hooks):
        y = HOOK_Y + i * ROW
        label = h["q"].rstrip("?")
        if len(label) > 34:
            label = label[:34].rsplit(" ", 1)[0] + "\u2026"
        o.append(f'<text x="{L - 32}" y="{y + 12}" font-size="9" fill="#3a352e" '
                 f'text-anchor="end" font-family="Helvetica Neue,Arial">'
                 f'{esc(label)}</text>')
        o.append(f'<text x="{L - 10}" y="{y + 12}" font-size="9" fill="#6b6357" '
                 f'text-anchor="end" font-weight="700" '
                 f'font-family="Helvetica Neue,Arial">{esc(h["code"])}</text>')
        for a in arcs:
            x0, w = xs[a["id"]]
            lo, hi = a["from"], a["to"]
            if not _open_in(h, lo, hi, last):
                continue
            live = _alive_in(h, lo, hi)
            o.append(f'<rect x="{x0:.1f}" y="{y + GAP:.1f}" width="{w - 2:.1f}" '
                     f'height="{ROW - GAP * 2:.1f}" rx="2" '
                     f'fill="{"#3d6b3f" if live else "#e4ded1"}" '
                     f'opacity="{"0.82" if live else "1"}"/>')
        cl = h.get("resolves")
        endx = (xs[arcs[-1]["id"]][0] + xs[arcs[-1]["id"]][1]) + 8
        if cl:
            o.append(f'<text x="{endx:.1f}" y="{y + 13}" font-size="10" fill="{GREEN}" '
                     f'font-family="Helvetica Neue,Arial">\u2713</text>')
        else:
            o.append(f'<text x="{endx:.1f}" y="{y + 13}" font-size="10" fill="{RED}" '
                     f'font-family="Helvetica Neue,Arial">\u2717</text>')

    # endings, only when there is data for them
    if scored:
        o.append(f'<text x="{L - 10}" y="{END_Y + 12}" font-size="8.5" fill="#a49a89" '
                 f'text-anchor="end" font-family="Helvetica Neue,Arial" '
                 f'letter-spacing=".08em">ENDINGS</text>')
        for a in arcs:
            x0, w = xs[a["id"]]
            inside = [e for e in scored if a["from"] <= e["ep"] <= a["to"]]
            if not inside:
                continue
            mean = sum((e["cliff"]["alignment"]) for e in inside) / len(inside)
            col = GREEN if mean >= 1.5 else AMBER if mean >= 0.9 else RED
            o.append(f'<rect x="{x0:.1f}" y="{END_Y + 4:.1f}" width="{w - 2:.1f}" '
                     f'height="11" rx="2" fill="{col}" opacity=".8"/>')
            o.append(f'<text x="{x0 + w / 2 - 1:.1f}" y="{END_Y + 30}" font-size="8" '
                     f'fill="#6b6357" text-anchor="middle" '
                     f'font-family="Helvetica Neue,Arial">{mean:.1f}</text>')
    o.append('</svg>')
    return ('<figure style="margin:16px 0 10px"><div style="overflow-x:auto">'
            + "".join(o) + '</div></figure>')


def crossing_table(transit):
    """What each arc hands to the next one."""
    rows = []
    for c in transit["crossings"]:
        t = c["tally"]
        bad = t["dropped"] > t["carried"]
        ev = " ".join(f'{k}<span style="color:#8a8173">&#8239;{v[:4]}</span>'
                      for k, v in sorted(c["events"].items()))
        rows.append(
            f'<tr{" class=flag" if bad else ""}>'
            f'<td class="c">{c["at"]}</td>'
            f'<td class="bt">{esc(c["from_name"])} &#8594; {esc(c["to_name"])}</td>'
            f'<td class="c">{t["carried"]}</td><td class="c">{t["closed"]}</td>'
            f'<td class="c"><b>{t["dropped"]}</b></td><td class="c">{t["opened"]}</td>'
            f'<td class="c">{t["revived"]}</td>'
            f'<td class="bt">{esc(c["reading"])}</td></tr>')
    return ('<table><thead><tr><th>At ep</th><th>Crossing from, to</th>'
            '<th>Carried</th><th>Closed</th><th>Dropped</th><th>Opened</th>'
            '<th>Revived</th><th>Reading</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table>')

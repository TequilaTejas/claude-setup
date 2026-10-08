#!/usr/bin/env python3
"""Work out what happens to every hook at every arc boundary.

    python arc_transit.py --arcs arcs.json --health health.json --out transit.json

Arcs are authored, not detected: you read the whole-script summary and mark where
the story turns. This tool does not second-guess those boundaries. It measures what
the show does with each hook as it crosses them.

`arcs.json`:
    {"arcs": [{"id": "A1", "name": "The Wedding", "from": 1, "to": 96,
               "about": "one plain sentence a stranger would understand"}]}

At each boundary every hook that was alive does exactly one of five things:

    carried   alive going in, alive coming out
    closed    the arc answers it on the way out
    dropped   alive going in, never meaningfully touched again
    opened    the new arc plants it
    revived   long quiet, and the new arc picks it back up

A boundary that drops more than it carries is where a listener has least reason to
continue. That is the number this tool exists to produce.
"""
import argparse, json, pathlib

LIVE_WINDOW = 10      # a hook counts as alive if raised within this many episodes
REVIVE_QUIET = 40     # quiet at least this long before a touch counts as a revival


def alive_at(hook, ep, window=LIVE_WINDOW):
    """Open at this episode AND actually raised recently."""
    op, cl = hook["opens"], hook.get("resolves")
    if ep < op or (cl and ep > cl):
        return False
    return any(ep - window <= t <= ep for t in hook.get("touch_eps") or [])


def touched_in(hook, lo, hi):
    return [t for t in hook.get("touch_eps") or [] if lo <= t <= hi]


def arc_state(hook, arc, nxt, last_ep):
    """What this arc does with this hook. None if the hook is not its business."""
    lo, hi = arc["from"], arc["to"]
    op, cl = hook["opens"], hook.get("resolves")
    inside = touched_in(hook, lo, hi)
    before = touched_in(hook, 1, lo - 1)

    if op > hi or (cl and cl < lo):
        return None                                   # not this arc's concern

    if lo <= op <= hi:
        return "opened"
    if cl and lo <= cl <= hi:
        return "closed"
    if not inside:
        return "absent"                               # open on paper, silent here
    if before and (min(inside) - max(before)) >= REVIVE_QUIET:
        return "revived"
    return "carried"


def boundary(hook, arc, nxt):
    """What happens to this hook as the story crosses out of `arc`."""
    end = arc["to"]
    cl = hook.get("resolves")
    if cl and arc["from"] <= cl <= end:
        return "closed"
    was = bool(touched_in(hook, max(arc["from"], end - LIVE_WINDOW * 3), end))
    will = bool(touched_in(hook, nxt["from"], min(nxt["to"], nxt["from"] + LIVE_WINDOW * 3)))
    if was and will:
        return "carried"
    if was and not will:
        return "dropped"
    if not was and will:
        return "revived"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arcs', required=True)
    ap.add_argument('--health', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    arcs = json.loads(pathlib.Path(a.arcs).read_text())["arcs"]
    health = json.loads(pathlib.Path(a.health).read_text())
    hooks, last = health["hooks"], health.get("last_ep")
    arcs.sort(key=lambda x: x["from"])

    gaps = [(a1["to"], a2["from"]) for a1, a2 in zip(arcs, arcs[1:])
            if a2["from"] != a1["to"] + 1]

    grid = {}
    for arc in arcs:
        for h in hooks:
            s = arc_state(h, arc, None, last)
            if s:
                grid[f'{arc["id"]}|{h["code"]}'] = s

    crossings = []
    for arc, nxt in zip(arcs, arcs[1:]):
        events = {}
        for h in hooks:
            b = boundary(h, arc, nxt)
            if b:
                events[h["code"]] = b
        opened = [h["code"] for h in hooks if nxt["from"] <= h["opens"] <= nxt["to"]]
        for c in opened:
            events.setdefault(c, "opened")
        tally = {k: sum(1 for v in events.values() if v == k)
                 for k in ("carried", "closed", "dropped", "opened", "revived")}
        crossings.append({
            "at": arc["to"], "from": arc["id"], "to": nxt["id"],
            "from_name": arc.get("name"), "to_name": nxt.get("name"),
            "events": events, "tally": tally,
            "reading": ("hands over more than it drops" if tally["carried"] >= tally["dropped"]
                        else "drops more than it hands over")})

    out = {"arcs": arcs, "grid": grid, "crossings": crossings,
           "gaps": gaps, "last_ep": last}
    pathlib.Path(a.out).write_text(json.dumps(out, indent=2, ensure_ascii=False))

    print(f'wrote {a.out}\n')
    print(f'{"arc":<22} {"eps":>11}  ' + "  ".join(h["code"].rjust(4) for h in hooks))
    ab = {"opened": "OPEN", "carried": "cont", "closed": "END", "revived": "back",
          "absent": " -- "}
    for arc in arcs:
        cells = "  ".join(ab.get(grid.get(f'{arc["id"]}|{h["code"]}'), "    "), )
        cells = "  ".join(ab.get(grid.get(f'{arc["id"]}|{h["code"]}'), "    ")
                          for h in hooks)
        print(f'{arc["name"][:21]:<22} {str(arc["from"])+"-"+str(arc["to"]):>11}  {cells}')
    print()
    for c in crossings:
        t = c["tally"]
        print(f'  ep {c["at"]:>4}  {c["from_name"][:16]:<17} -> {c["to_name"][:16]:<17} '
              f'carried {t["carried"]}  closed {t["closed"]}  dropped {t["dropped"]}  '
              f'opened {t["opened"]}  revived {t["revived"]}   {c["reading"]}')
    if gaps:
        print(f'\n  WARNING: arcs do not join cleanly: {gaps}')
        print('  Every episode should belong to exactly one arc.')


if __name__ == '__main__':
    main()

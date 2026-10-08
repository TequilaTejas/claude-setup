#!/usr/bin/env python3
"""Turn independent arc proposals into acts, by consensus.

    python merge_arcs.py --dir arcs_raw/ --last 665 --out arcs.json

Every episode is read by two agents whose windows are offset, so a real turn is seen
by two people who never spoke. A turn that only one agent marks is not a boundary; it
is one reader's opinion. That is the whole point of running the pass twice.

Consensus rule
    a turn becomes a boundary when >= MIN_AGREE agents mark within +/- TOLERANCE
    episodes of each other, and the cluster's combined confidence clears MIN_WEIGHT

Nothing here looks at hooks. `arc_align.py` measures the overlap afterwards, which
is only meaningful because this step could not see it.
"""
import argparse, collections, json, pathlib, sys

TOLERANCE = 4      # episodes: two marks this close are the same turn
MIN_AGREE = 2      # independent agents who must see it
MIN_WEIGHT = 4     # summed confidence across the cluster
MIN_ACT = 20       # episodes: shorter than this and it is a scene, not an act


def load(d):
    out = []
    for p in sorted(pathlib.Path(d).glob('*.json')):
        try:
            b = json.loads(p.read_text())
        except json.JSONDecodeError as ex:
            print(f'  BAD JSON {p.name}: {ex}', file=sys.stderr)
            continue
        lo, hi = (b.get('window') or [None, None])[:2]
        for t in b.get('turns', []):
            ep = t.get('ep')
            if not isinstance(ep, int):
                continue
            if isinstance(lo, int) and not (lo <= ep <= hi):
                print(f'  {p.name}: turn at {ep} outside window {lo}-{hi}, discarded',
                      file=sys.stderr)
                continue
            out.append({**t, 'file': p.name, 'window': [lo, hi]})
    return out


def cluster(turns, tol=TOLERANCE):
    """Group nearby marks from different agents into one candidate turn."""
    groups = []
    for t in sorted(turns, key=lambda x: x['ep']):
        if groups and t['ep'] - groups[-1][-1]['ep'] <= tol:
            groups[-1].append(t)
        else:
            groups.append([t])
    out = []
    for g in groups:
        agents = {t['file'] for t in g}
        weight = sum(t.get('confidence') or 1 for t in g)
        # the episode the strongest voice named, ties going to the earlier one
        best = sorted(g, key=lambda t: (-(t.get('confidence') or 1), t['ep']))[0]
        kinds = sorted({k for t in g for k in (t.get('kinds') or [])})
        out.append({
            'ep': best['ep'], 'agents': len(agents), 'weight': weight,
            'kinds': kinds,
            'spread': [min(t['ep'] for t in g), max(t['ep'] for t in g)],
            'why': best.get('why', ''),
            'before': best.get('before', ''), 'after': best.get('after', ''),
            'marks': [{'ep': t['ep'], 'confidence': t.get('confidence'),
                       'by': t['file'], 'why': t.get('why', '')} for t in g],
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('--last', type=int, required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--min-agree', type=int, default=MIN_AGREE)
    ap.add_argument('--min-act', type=int, default=MIN_ACT)
    ap.add_argument('--acts', type=int, help='cap the act count: keep the strongest '
                    'N-1 boundaries and record the rest as beats inside their act. '
                    'Nothing is discarded; the weaker turns are still in the file.')
    a = ap.parse_args()

    turns = load(a.dir)
    if not turns:
        raise SystemExit(f'no turns proposed under {a.dir}')
    cands = cluster(turns)

    accepted, rejected = [], []
    for c in cands:
        if c['agents'] >= a.min_agree and c['weight'] >= MIN_WEIGHT:
            accepted.append(c)
        else:
            rejected.append(c)

    # Two boundaries closer than --min-act make an act too short to be an act. Drop
    # the WEAKER of the pair, not the later one: an earlier version dropped by
    # position and threw away ep 235, a two-agent structural turn, because it
    # happened to fall 15 episodes after another one.
    accepted.sort(key=lambda c: c['ep'])
    kept, dropped_short = [], []
    for c in accepted:
        if kept and c['ep'] - kept[-1]['ep'] < a.min_act:
            prev = kept[-1]
            if (c['weight'], c['agents']) > (prev['weight'], prev['agents']):
                kept[-1] = c              # the newcomer is stronger; it replaces
                dropped_short.append(prev)
            else:
                dropped_short.append(c)
        else:
            kept.append(c)
    # the final act has to clear the bar too, which the spacing check never saw
    while len(kept) > 1 and (a.last - kept[-1]['ep'] + 1) < a.min_act:
        dropped_short.append(kept.pop())

    # Reducing to N acts: repeatedly demote the single weakest boundary until N-1
    # remain. Taking the globally strongest N-1 does NOT work: on this show the
    # strongest turns all cluster in the first half, which left a 358-episode act
    # at the end. Demoting one at a time keeps the acts balanced, because every
    # removal is judged against what it merges.
    beats = []
    while a.acts and len(kept) > a.acts - 1:
        weakest = min(kept, key=lambda c: (c['weight'], c['agents']))
        kept.remove(weakest)
        beats.append(weakest)
    beats.sort(key=lambda c: c['ep'])

    bounds = [1] + [c['ep'] for c in kept]
    arcs = []
    for i, lo in enumerate(bounds):
        hi = (bounds[i + 1] - 1) if i + 1 < len(bounds) else a.last
        src = kept[i - 1] if i else None
        arcs.append({
            'id': f'A{i+1}', 'name': f'Act {i+1}', 'from': lo, 'to': hi,
            'about': (src or {}).get('after', ''),
            'boundary_evidence': None if not src else {
                'agents_agreeing': src['agents'], 'confidence': src['weight'],
                'kinds': src['kinds'], 'spread': src['spread'],
                'why': src['why'], 'marks': src['marks']},
        })

    pathlib.Path(a.out).write_text(json.dumps(
        {'arcs': arcs, 'beats': beats, 'rejected': rejected,
         'folded_in': dropped_short},
        indent=2, ensure_ascii=False))

    print(f'wrote {a.out}\n')
    print(f'  {len(turns)} turns proposed by {len({t["file"] for t in turns})} agents')
    print(f'  clustered into {len(cands)} candidates\n')
    print(f'{"ep":>5} {"agents":>7} {"conf":>5}  {"kinds":<28} boundary')
    for c in cands:
        mark = ('KEPT  ' if c in kept else
                'folded' if c in dropped_short else 'reject')
        print(f'{c["ep"]:>5} {c["agents"]:>7} {c["weight"]:>5}  '
              f'{",".join(c["kinds"])[:28]:<28} {mark}  {c["why"][:46]}')
    if beats:
        print(f'\n  {len(beats)} turns kept as beats inside acts, not act breaks:')
        for b in beats:
            print(f'    ep {b["ep"]:>4}  weight {b["weight"]}  {b["why"][:56]}')
    print(f'\n  {len(arcs)} acts:')
    for x in arcs:
        ev = x['boundary_evidence']
        print(f'    {x["id"]:<4} {x["from"]:>4}-{x["to"]:<4} ({x["to"]-x["from"]+1:>3} eps)  '
              + ('opens the show' if not ev else
                 f'{ev["agents_agreeing"]} agents agree, {",".join(ev["kinds"])}'))
    if len(arcs) < 4:
        print('\n  WARNING: fewer than 4 acts. Either the show really is that '
              'unbroken, or\n  the agents disagreed and consensus threw everything '
              'out. Check --min-agree.')
    print('\n  Names are placeholders. Name the acts yourself; the boundaries are '
          'the measured part.')


if __name__ == '__main__':
    main()

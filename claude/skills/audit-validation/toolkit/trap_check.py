#!/usr/bin/env python3
"""Mechanical cause check: is a drop zone creative at all?

    python trap_check.py --data data.json --verdicts verdicts.json \
        --reads comment_reads/ --out verdicts.json

Runs before any creative reading. A large drop with a revenue step, a duration change,
or a production/money comment majority is not a story problem, and telling a writers'
room to fix it burns a rewrite on a pricing decision.

On the first show this ran against, the worst drop in 665 episodes — 3.30x baseline at
eps 561-570 — turned out to be a paywall move at ep 563: revenue per thousand
listeners went from 80 to 131 in four episodes and never came back, drop spiked to
10.5% on that single episode and decayed to baseline over sixteen, and nineteen
comments in the window said the free episodes had stopped. It had been written up as
the show's biggest missed creative problem.
"""
import argparse, json, pathlib


def rev_per_k(eps, ep):
    v = eps.get(str(ep))
    if not v or not v.get('revenue') or not v.get('listen'):
        return None
    return v['revenue'] / v['listen'] * 1000


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def check(f, eps, reads, last_ep):
    """Return (cause, evidence) or (None, []). Order matters: a monetisation step
    outranks everything, because it moves every other number on the page."""
    lo, hi = f['from'], f['to']
    ev = []
    cause = None

    # --- monetisation: a step in revenue per listener that does not come back
    before = mean([rev_per_k(eps, e) for e in range(max(2, lo - 20), lo)])
    inside = mean([rev_per_k(eps, e) for e in range(lo, hi + 1)])
    after = mean([rev_per_k(eps, e) for e in range(hi + 1, min(hi + 21, last_ep + 1))])
    if before and inside and inside / before >= 1.25:
        persists = after is not None and after / before >= 1.20
        # find the episode it steps at
        # Take the biggest step in the neighbourhood, not the first one over the
        # line: scanning forward from `lo` and breaking reports the zone's own start
        # episode whenever the real step is a few episodes inside it.
        step_at, best = None, 1.0
        for e_ in range(max(3, lo - 5), min(hi + 6, last_ep - 4)):
            w0 = mean([rev_per_k(eps, x) for x in range(max(2, e_ - 5), e_)])
            w1 = mean([rev_per_k(eps, x) for x in range(e_ + 1, e_ + 6)])
            if w0 and w1 and w1 / w0 > best:
                step_at, best = e_, w1 / w0
        if best < 1.20:
            step_at = None
        ev.append(f'Revenue per 1,000 listeners goes from {before:.0f} before the zone '
                  f'to {inside:.0f} inside it'
                  + (f' and {after:.0f} after, so it does not come back'
                     if persists else f' and {after:.0f} after' if after else '')
                  + (f'. The step lands at ep {step_at}.' if step_at else '.'))
        if persists:
            cause = 'monetisation'

    # --- shape: one sharp episode then a decay is a boundary, not a story stretch
    drops = [(e_, abs((eps.get(str(e_)) or {}).get('drop') or 0))
             for e_ in range(lo, hi + 1) if eps.get(str(e_))]
    base = mean([abs((eps.get(str(e_)) or {}).get('drop') or 0)
                 for e_ in range(max(2, lo - 20), lo) if eps.get(str(e_))])
    if drops and base:
        peak_ep, peak = max(drops, key=lambda t: t[1])
        tail = mean([d for e_, d in drops if e_ > peak_ep + 10])
        if peak / base >= 3.0 and tail and tail / base <= 1.6:
            ev.append(f'The drop is a spike, not a stretch: {peak * 100:.1f}% at ep '
                      f'{peak_ep} against {base * 100:.1f}% before the zone, decaying '
                      f'to {tail * 100:.1f}% within the zone. A story problem degrades '
                      f'gradually; a boundary spikes once and recovers.')
            cause = cause or 'boundary'

    # --- duration: episodes changing length changes drop rate mechanically
    d_before = mean([(eps.get(str(e_)) or {}).get('dur') for e_ in range(max(2, lo - 20), lo)])
    d_inside = mean([(eps.get(str(e_)) or {}).get('dur') for e_ in range(lo, hi + 1)])
    if d_before and d_inside and abs(d_inside / d_before - 1) >= 0.20:
        ev.append(f'Episode length changes here: {d_before * 60:.1f} min before the '
                  f'zone, {d_inside * 60:.1f} min inside it.')
        cause = cause or 'duration'

    # --- what listeners blame, when we have read them
    # Comment evidence is only admissible for episodes a theme actually names.
    # Window-level mood counts leak: a 41-episode read overlapping four episodes of a
    # 71-episode finding once handed that whole finding a production cause.
    nonstory, story, named = 0, 0, []
    for r in reads:
        rl, rh = r['window']
        if rh < lo or hi < rl:
            continue
        for t in r.get('themes', []):
            t_eps = [x for x in (t.get('episodes') or []) if lo <= x <= hi]
            if not t_eps:
                continue
            # scale the theme's count by the share of its episodes inside this zone
            share = len(t_eps) / max(1, len(t.get('episodes') or [1]))
            n = t.get('count', 0) * share
            if t.get('kind') in ('production', 'money'):
                nonstory += n
                named.append((n, t))
            elif t.get('kind') in ('complaint', 'confusion', 'leaving'):
                story += n
    if named and nonstory >= 0.45 * max(1.0, nonstory + story):
        named.sort(key=lambda x: -x[0])
        ev.append(f'Listeners here blame things outside the script '
                  f'({nonstory:.0f} of {nonstory + story:.0f} negative comments that '
                  f'name an episode in this range): '
                  + '; '.join(f'{t["count"]} comments on {t["theme"]}'
                              for _, t in named[:2]) + '.')
        cause = cause or 'production'
    elif named:
        ev.append(f'Listeners do complain about things outside the script here '
                  f'({nonstory:.0f} of {nonstory + story:.0f} negative comments), but '
                  f'story complaints outnumber them, so the comments alone do not \n'
                  'explain this drop.')
    return cause, ev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--verdicts', required=True)
    ap.add_argument('--reads', default=None)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    data = json.loads(pathlib.Path(a.data).read_text())
    v = json.loads(pathlib.Path(a.verdicts).read_text())
    reads = []
    if a.reads:
        for p in sorted(pathlib.Path(a.reads).glob('*.json')):
            reads.append(json.loads(p.read_text()))

    eps, last = data['episodes'], v['last_ep']
    flipped = []
    for f in list(v['tested']) + list(v['missed']):
        cause, ev = check(f, eps, reads, last)
        f['cause'], f['cause_evidence'] = cause, ev
        # Only a zone the data says is bad can be reclassified. A NO COST zone with a
        # revenue step is just a price change that cost nothing; leave it alone.
        if cause in ('monetisation', 'boundary', 'duration', 'production') \
                and f['verdict'] in ('MISSED', 'CONFIRMED'):
            f['verdict_was'] = f['verdict']
            f['verdict'] = 'NOT CREATIVE'
            flipped.append(f)

    pathlib.Path(a.out).write_text(json.dumps(v, indent=1))
    print(f'wrote {a.out}')
    if flipped:
        print(f'\n  {len(flipped)} zone(s) reclassified NOT CREATIVE — '
              f'do not send these to the writers:')
        for f in flipped:
            print(f'    {f.get("label", f.get("title"))}  eps {f["from"]}-{f["to"]}  '
                  f'{f["verdict_was"]} -> NOT CREATIVE  ({f["cause"]})')
            for x in f['cause_evidence']:
                print(f'        · {x}')
    else:
        print('  no zone reclassified; every drop survives the trap check')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Data-first pass: find what the numbers single out, act by act, before reading.

    python detect_events.py --data data.json --claims claims.json --out events.json

The forward test asks whether a creative finding cost anything. That can only ever
confirm or clear things someone already believed. This runs the other direction: inside
each act, find the episodes the data points at on its own, with no reference to the
audit, so those episodes can then be read and explained.

Five detectors, each objective and each reporting its own arithmetic:

  drop_spike     an episode whose drop rate stands far above the act's own median
  level_step     the single largest one-episode fall in audience headcount
  completion_dip an episode far more people abandon partway through than usual
  comment_surge  an episode drawing far more comments than the act's median
  revenue_step   a persistent jump in revenue per listener: a pricing boundary

Nothing here is a finding yet. These are questions for the reading pass.
"""
import argparse, json, pathlib, statistics as st


def med(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


def detect(act, eps, base_drop, k=3):
    lo, hi = max(act['from'], 2), act['to']
    rng = [n for n in range(lo, hi + 1) if str(n) in eps]
    if len(rng) < 4:
        return []
    g = lambda n, f: (eps.get(str(n)) or {}).get(f)
    ev = []

    drops = [abs(g(n, 'drop') or 0) for n in rng]
    m_drop = med(drops) or 0
    for n in rng:
        dv = abs(g(n, 'drop') or 0)
        if m_drop and dv >= max(m_drop * 2.0, abs(base_drop) * 2.0):
            ev.append({'ep': n, 'kind': 'drop_spike', 'score': dv / m_drop,
                       'what': f'{dv * 100:.1f}% drop against a {m_drop * 100:.1f}% '
                               f'median for this act, {dv / m_drop:.1f} times it'})

    steps = []
    for n in rng[1:]:
        a_, b_ = g(n - 1, 'listen'), g(n, 'listen')
        if a_ and b_:
            steps.append((n, a_ - b_, (a_ - b_) / a_))
    if steps:
        n, lost, frac = max(steps, key=lambda t: t[1])
        med_lost = med([x[1] for x in steps]) or 0
        if lost > 0 and med_lost and lost >= med_lost * 3:
            ev.append({'ep': n, 'kind': 'level_step', 'score': lost / max(med_lost, 1),
                       'what': f'{lost:,.0f} listeners gone in one episode, '
                               f'{frac * 100:.1f}% of the audience and '
                               f'{lost / med_lost:.1f} times this act’s median episode'})

    c90 = [(n, g(n, 'c90')) for n in rng if g(n, 'c90') is not None]
    if len(c90) >= 6:
        m_c = med([c for _, c in c90])
        for n, c in c90:
            if m_c and c <= m_c * 0.78:
                ev.append({'ep': n, 'kind': 'completion_dip', 'score': m_c / max(c, .01),
                           'what': f'only {c * 100:.0f}% finish this episode against '
                                   f'{m_c * 100:.0f}% across the act: people are '
                                   f'stopping inside it, not after it'})

    cmts = [(n, len((eps.get(str(n)) or {}).get('_comments', []))) for n in rng]
    ev_c = []
    for n in rng:
        ev_c.append((n, (eps.get(str(n)) or {}).get('_ncomments', 0)))
    m_cm = med([c for _, c in ev_c]) or 0
    for n, c in ev_c:
        if m_cm >= 2 and c >= max(m_cm * 4, 12):
            ev.append({'ep': n, 'kind': 'comment_surge', 'score': c / max(m_cm, 1),
                       'what': f'{c} comments against a median of {m_cm:.0f} for this '
                               f'act, {c / max(m_cm, 1):.0f} times as many'})

    rpl = []
    for n in rng:
        r_, l_ = g(n, 'revenue'), g(n, 'listen')
        if r_ and l_:
            rpl.append((n, r_ / l_ * 1000))
    if len(rpl) >= 8:
        for i in range(3, len(rpl) - 4):
            b4 = st.mean([x[1] for x in rpl[max(0, i - 4):i]])
            af = st.mean([x[1] for x in rpl[i + 1:i + 5]])
            if b4 and af / b4 >= 1.20:
                ev.append({'ep': rpl[i][0], 'kind': 'revenue_step',
                           'score': af / b4,
                           'what': f'revenue per 1,000 listeners steps from '
                                   f'{b4:.0f} to {af:.0f} here and does not return: '
                                   f'a pricing boundary, not a story beat'})
                break

    # keep the strongest, and never two events within three episodes of each other
    ev.sort(key=lambda x: -x['score'])
    kept = []
    for x in ev:
        if all(abs(x['ep'] - y['ep']) > 3 or x['kind'] == y['kind'] for y in kept):
            if not any(y['ep'] == x['ep'] and y['kind'] == x['kind'] for y in kept):
                kept.append(x)
        if len(kept) >= k:
            break
    return kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--claims', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--per-act', type=int, default=3)
    a = ap.parse_args()

    data = json.loads(pathlib.Path(a.data).read_text())
    claims = json.loads(pathlib.Path(a.claims).read_text())
    eps = data['episodes']
    for n, cs in data['comments'].items():
        if n in eps:
            eps[n]['_ncomments'] = len(cs)

    out = {}
    for act in sorted(claims['acts'], key=lambda x: x['from']):
        out[act['id']] = {
            'act': {k: act[k] for k in ('id', 'name', 'from', 'to')},
            'events': detect(act, eps, data['baseline_drop'], a.per_act),
        }

    pathlib.Path(a.out).write_text(json.dumps(out, indent=1))
    tot = sum(len(v['events']) for v in out.values())
    print(f'wrote {a.out}  ·  {tot} events across {len(out)} acts\n')
    for aid, v in out.items():
        act = v['act']
        if not v['events']:
            print(f'  {aid:4s} eps {act["from"]:3d}-{act["to"]:3d}  '
                  f'nothing stands out')
            continue
        print(f'  {aid:4s} eps {act["from"]:3d}-{act["to"]:3d}  {act["name"]}')
        for x in v['events']:
            print(f'         ep {x["ep"]:3d}  {x["kind"]:15s} {x["what"]}')


if __name__ == '__main__':
    main()

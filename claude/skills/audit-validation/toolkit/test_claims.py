#!/usr/bin/env python3
"""Test every Creative Audit claim against retention, and search for what it missed.

    python test_claims.py --claims claims.json --data data.json --out verdicts.json

Two directions, and both matter:

  audit -> data   every trouble zone, break and act: is drop above baseline there?
  data -> audit   every block the show actually bleeds: does the audit explain it?

Five verdicts. CONFIRMED, NO COST, MISSED, CONTESTED, and NOT CREATIVE,
which trap_check.py assigns afterwards. A run that returns all
CONFIRMED has fitted itself to the answer.
"""
import argparse, json, pathlib, statistics as st

CONFIRM_AT = 1.25      # x the show's own baseline before a flagged zone is CONFIRMED
MISS_AT = 1.35         # x baseline before an unexplained block is a MISSED finding
# A show's own baseline flatters its late episodes: the people still listening at ep
# 500 are the committed ones, so a late disaster can sit under 1.35x and look fine.
# The benchmark does not have that problem. On the first show this ran against, the
# narrator swap at ep 291 cost 1,146 listeners and scored 1.26x and 1.33x vs_show —
# under the threshold, invisible — while scoring 1.77x and 2.11x vs the benchmark.
MISS_BENCH_AT = 1.60   # x benchmark, paired with the lower bar below
MISS_SHOW_FLOOR = 1.20 # x baseline required alongside a benchmark-triggered miss
BLOCK = 10             # episode block size for the data-first sweep
EARLY = 51             # everything before this is sampling, never a finding


def window(data, lo, hi):
    """Drop stats for an episode range, against both baselines."""
    eps = data['episodes']
    d = [eps[str(e)]['drop'] for e in range(lo, hi + 1)
         if str(e) in eps and eps[str(e)]['drop'] is not None]
    if not d:
        return None
    base = data['baseline_drop']
    bench = [data['benchmark_drop_at'].get(str(e)) for e in range(lo, hi + 1)]
    bench = [b for b in bench if b is not None]
    listeners = [eps[str(e)]['listen'] for e in range(lo, hi + 1)
                 if str(e) in eps and eps[str(e)].get('listen') is not None]
    mean = st.mean(d)
    # Rate-derived "listeners lost", kept for continuity but NOT the cost figure.
    excess = sum(max(0.0, base - x) * (listeners[i] if i < len(listeners) else 0)
                 for i, x in enumerate(d))

    # Cost comes from the LEVEL series, not the rate. `drop` and `listen` are
    # different measures: at ep 200 this show's level fell 0.078% while its drop
    # column read 1.539%. Compounding a rate against a level to get a headcount mixes
    # the two, which the donor brief says never to do, and it inflated every cost on
    # the page. A headcount is a headcount: read it off the level.
    lv = lambda x: (eps.get(str(x)) or {}).get('listen')
    s_lvl, e_lvl, k = lv(lo), lv(hi), hi - lo
    level_lost = level_excess = None
    if s_lvl and e_lvl and k > 0:
        per = (data.get('level') or {}).get('per_episode_decline') or 0.0
        level_lost = s_lvl - e_lvl
        level_excess = level_lost - (s_lvl - s_lvl * (1 - per) ** k)
    return {
        'episodes': [lo, hi], 'n': len(d),
        'mean_drop': mean,
        'vs_show': mean / base if base else None,
        'vs_benchmark': (mean / st.mean(bench)) if bench and st.mean(bench) else None,
        'excess_listeners': round(excess),
        'level_from': s_lvl, 'level_to': e_lvl,
        'level_lost': round(level_lost) if level_lost is not None else None,
        'level_excess': round(level_excess) if level_excess is not None else None,
        'comments': sum(len(data['comments'].get(str(e), []))
                        for e in range(lo, hi + 1)),
    }


def verdict_for(w, flagged):
    if w is None:
        return 'NO DATA'
    r = w['vs_show'] or 0
    if flagged:
        return 'CONFIRMED' if r >= CONFIRM_AT else 'NO COST'
    b = w['vs_benchmark'] or 0
    if r >= MISS_AT:
        return 'MISSED'
    if r >= MISS_SHOW_FLOOR and b >= MISS_BENCH_AT:
        return 'MISSED'
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--claims', required=True)
    ap.add_argument('--data', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    claims = json.loads(pathlib.Path(a.claims).read_text())
    data = json.loads(pathlib.Path(a.data).read_text())
    base = data['baseline_drop']
    last = max(int(e) for e in data['episodes'])

    tested = []
    # `ref` is the join key between this file and the Creative Audit's own labels, so
    # the extended report can put a verdict beside the finding it belongs to. The
    # numbering must match the audit renderer exactly: it numbers trouble zones by
    # sorted start episode and breaks by list order. Numbering them any other way puts
    # the right verdict under the wrong heading.
    for n, d in enumerate(sorted(claims['trouble'], key=lambda x: x['from']), 1):
        w = window(data, d['from'], d['to'])
        tested.append({'kind': 'trouble', 'label': d['signal'], 'ref': f'D{n}',
                       'code': d.get('code'),
                       'severity': d['severity'], 'story': d.get('story', ''),
                       'from': d['from'], 'to': d['to'],
                       'verdict': verdict_for(w, True), **(w or {})})
    for n, b in enumerate(claims['breaks'], 1):
        lo = max(EARLY, b['broke_ep'] - 5)
        w = window(data, lo, min(last, b['broke_ep'] + 5))
        tested.append({'kind': 'break', 'label': b['title'], 'ref': f'B{n}',
                       'code': b.get('code'),
                       'from': lo, 'to': min(last, b['broke_ep'] + 5),
                       'hook': b.get('hook'), 'what': b.get('what', ''),
                       'verdict': verdict_for(w, True), **(w or {})})
    for h in claims['hooks']:
        if not h.get('resolves'):
            continue
        lo = max(EARLY, h['resolves'] - 5)
        w = window(data, lo, min(last, h['resolves'] + 5))
        tested.append({'kind': 'hook_close', 'label': h['question'],
                       'code': h['code'], 'ref': h['code'], 'from': lo,
                       'to': min(last, h['resolves'] + 5),
                       'hook_verdict': h['verdict'],
                       'verdict': verdict_for(w, True), **(w or {})})

    # data -> audit: what bleeds that the audit does not explain.
    # "Explained" means ANY tested finding covers it, not just a trouble zone: a
    # block sitting under a break or a hook close is already accounted for, and an
    # earlier version reported those blocks twice, once as CONFIRMED and again as
    # MISSED.
    # Only a CONFIRMED finding explains a block. A NO COST finding explains nothing
    # by definition — the data says that stretch cost nothing — so a bleeding block
    # inside one is still unexplained. This matters most for wide findings: a
    # 150-episode "cast bloat" zone averaged out to 0.99x and, while it counted as
    # cover, it hid a 20-episode narrator-swap bleed worth 1,146 listeners inside it.
    covered = [(t['from'], t['to']) for t in tested if t['verdict'] == 'CONFIRMED']
    missed, sweep, raw_missed = [], [], []
    for lo in range(EARLY, last + 1, BLOCK):
        hi = min(lo + BLOCK - 1, last)
        w = window(data, lo, hi)
        if not w:
            continue
        sweep.append(w)
        if any(c[0] <= hi and c[1] >= lo for c in covered):
            continue
        if verdict_for(w, False) == 'MISSED':
            raw_missed.append((lo, hi))

    # Contiguous blocks are one event, not three. Reporting them separately split the
    # paywall bleed into "eps 561-570", "571-580", "581-590" and made each look
    # smaller than the thing actually happening.
    for lo, hi in raw_missed:
        if missed and lo == missed[-1]['to'] + 1:
            missed[-1]['to'] = hi
        else:
            missed.append({'from': lo, 'to': hi})
    for m in missed:
        w = window(data, m['from'], m['to'])
        m.update({'kind': 'missed', 'verdict': 'MISSED',
                  'label': f'Unexplained drop, eps {m["from"]}-{m["to"]}', **w})
    missed.sort(key=lambda x: -(x['vs_show'] or 0))

    out = {'baseline_drop': base, 'baseline_from': EARLY, 'last_ep': last,
           'thresholds': {'confirm': CONFIRM_AT, 'miss': MISS_AT},
           'tested': tested, 'missed': missed, 'sweep': sweep}
    pathlib.Path(a.out).write_text(json.dumps(out, indent=2, ensure_ascii=False))

    counts = {}
    for t in tested + missed:
        counts[t['verdict']] = counts.get(t['verdict'], 0) + 1
    print(f'wrote {a.out}\n')
    print(f'  baseline drop from ep{EARLY}: {base*100:.2f}%')
    print(f'  verdicts: ' + ', '.join(f'{k} {v}' for k, v in sorted(counts.items())))
    print(f'\n  {"finding":<44}{"eps":>11}{"vs show":>9}{"lost":>9}  verdict')
    for t in sorted(tested + missed, key=lambda x: -(x.get('vs_show') or 0))[:16]:
        print(f'  {t["label"][:42]:<44}{str(t["from"])+"-"+str(t["to"]):>11}'
              f'{(t.get("vs_show") or 0):>8.2f}x{t.get("excess_listeners", 0):>9,}'
              f'  {t["verdict"]}')
    if counts.get('CONFIRMED', 0) == len(tested):
        print('\n  WARNING: every flagged finding came back CONFIRMED. Check the '
              'threshold and the baseline before believing it.')


if __name__ == '__main__':
    main()

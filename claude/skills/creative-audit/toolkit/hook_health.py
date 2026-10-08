#!/usr/bin/env python3
"""Score each hook on whether the show is actually keeping it alive.

    python hook_health.py --ledger ledger.json --analysis analysis.json --out health.json

`analysis.json` is where you write down the hooks you settled on after reading the
whole-script summary. Each hook lists the raw questions that belong to it, so this
tool can find every episode that touches it.

Nothing here is a judgment. Four things get counted:

  touch rate      how often the show remembers this question
  longest silence the biggest run of episodes where nobody mentions it
  moved vs said   did the episode push the question somewhere, or circle it.
                  This uses the episode's `beat` field as a proxy. It is the weakest
                  of the four. Treat a low score as worth a look, not as proof.
  how it ended    on screen, off screen, dodged, or never

Those four give a verdict: WORKING, STALLING, GONE QUIET, or BROKEN.
"""
import argparse, difflib, json, pathlib, re, sys

STOP = set("a an the is are was were will would can could do does did to of in on at "
           "for and or but if it its he she they them his her their this that with "
           "be been being have has had who what why when how".split())


def key(q):
    return set(w for w in re.findall(r"[a-z']+", (q or '').lower()) if w not in STOP)


def same(a, b, thresh=0.55):
    ka, kb = key(a), key(b)
    if not ka or not kb:
        return False
    jac = len(ka & kb) / len(ka | kb)
    if jac >= thresh:
        return True
    return difflib.SequenceMatcher(None, " ".join(sorted(ka)),
                                   " ".join(sorted(kb))).ratio() >= 0.82


def touches(episodes, members):
    """{ep: 'moved'|'restated'} for every episode that touches this hook."""
    hits = {}
    for e in episodes:
        n, how = e['ep'], None
        # a close always moves it: the question got an answer
        for c in e.get('closes') or []:
            if any(same(c.get('q'), m) for m in members):
                how = 'moved'
        # an open moves it only if the episode pushes hard (force 2-3);
        # a force-1 mention is the show remembering the thread, not advancing it
        # `force` cannot separate advancing from mentioning: agents rate almost
        # everything 2-3. The per-episode `beat` field is the only signal that does.
        if how is None:
            for o in e.get('opens') or []:
                if any(same(o.get('q'), m) for m in members):
                    how = 'restated' if e.get('beat') == 're-runs' else 'moved'
                    break
        # the episode ended on this thread without opening or closing anything
        if how is None:
            cl = (e.get('cliff') or {}).get('text') or ''
            if any(same(cl, m) for m in members):
                how = 'restated'
        if how:
            hits[n] = how
    return hits


def verdict(touch_rate, silence, moved_pct, ended, span):
    """Counted, not judged. Order matters: the worst true statement wins."""
    if ended in ('offscreen', 'deflected', 'dropped'):
        return 'BROKEN', f'the show answered it {ended.replace("dropped", "never")}'
    if ended is None:
        return 'BROKEN', 'never answered'
    if silence >= max(40, span * 0.35):
        return 'GONE QUIET', f'nobody mentions it for {silence} episodes'
    if moved_pct < 40:
        return 'STALLING', f'only {moved_pct:.0f}% of the episodes that touch it move it'
    if touch_rate > 25:
        return 'STALLING', f'touched once every {touch_rate:.0f} episodes'
    return 'WORKING', f'touched every {touch_rate:.0f} episodes and answered on screen'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ledger', required=True)
    ap.add_argument('--analysis', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    led = json.loads(pathlib.Path(a.ledger).read_text())
    ana = json.loads(pathlib.Path(a.analysis).read_text())
    episodes = led['episodes']
    last = led.get('range', [1, episodes[-1]['ep']])[1]

    rows, thin = [], []
    for h in ana['hooks']:
        members = h.get('members') or [h['q']]
        hits = touches(episodes, members)
        eps = sorted(hits)
        if len(eps) < 5 or len(members) < 6:
            thin.append((h['code'], len(members), len(eps)))
        op = h.get('opens') or (eps[0] if eps else 1)
        cl = h.get('resolves')
        end = cl if cl else last
        span = max(1, end - op)
        inside = [n for n in eps if op <= n <= end] or [op]
        gaps = [b - a2 for a2, b in zip(inside, inside[1:])] or [span]
        silence = max(gaps + [inside[0] - op, end - inside[-1]])
        moved = sum(1 for n in inside if hits.get(n) == 'moved')
        moved_pct = 100.0 * moved / max(1, len(inside))
        rate = span / max(1, len(inside))
        v, why = verdict(rate, silence, moved_pct, h.get('ended'), span)
        rows.append({'code': h['code'], 'q': h['q'], 'opens': op, 'resolves': cl,
                     'span': span, 'touches': len(inside), 'touch_rate': round(rate, 1),
                     'longest_silence': silence, 'moved_pct': round(moved_pct),
                     'ended': h.get('ended'), 'verdict': v, 'why': why,
                     'touch_eps': inside})

    order = {'WORKING': 0, 'STALLING': 1, 'GONE QUIET': 2, 'BROKEN': 3}
    rows.sort(key=lambda r: (order[r['verdict']], -r['span']))
    pathlib.Path(a.out).write_text(json.dumps({'last_ep': last, 'hooks': rows},
                                              indent=2, ensure_ascii=False))

    print(f'wrote {a.out}\n')
    print(f'{"":4} {"verdict":<11} {"span":>5} {"touch":>6} {"quiet":>6} {"moved":>6}  question')
    for r in rows:
        print(f'{r["code"]:<4} {r["verdict"]:<11} {r["span"]:>5} '
              f'{r["touch_rate"]:>6} {r["longest_silence"]:>6} {r["moved_pct"]:>5}%  '
              f'{r["q"][:58]}')
    if thin:
        print('\n  NOT ENOUGH EVIDENCE TO TRUST THESE:')
        for code, nm, ne in thin:
            print(f'    {code}: {nm} phrasings matched {ne} episodes')
        print('\n  A hook is found by matching the wording people used. If you only')
        print('  gave it a few phrasings, it will look quiet even when the show talks')
        print('  about it constantly. Add more wordings to that hook\'s "members" list')
        print('  in analysis.json, then run this again. Until then, treat the verdicts')
        print('  above for those hooks as unknown, not as findings.')
        sys.exit(1)


if __name__ == '__main__':
    main()

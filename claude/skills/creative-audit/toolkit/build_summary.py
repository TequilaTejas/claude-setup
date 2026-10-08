#!/usr/bin/env python3
"""Stitch the per-block summaries into one summary of the whole script.

    python build_summary.py --dir extract/ --out summary.md

Each batch agent read 25 episodes and wrote three things: a plain summary of those
25, the questions that were already running when it started, and the questions still
unanswered when it finished. This joins them.

The joins are the point. Where block N's `open_at_end` matches block N+1's
`open_at_start`, a thread crosses the seam between two agents who never spoke. Those
matches are what turn 27 isolated reads into one story.

Output is Markdown, meant to be read by a person and by the model doing the
clustering. It reports every unmatched handoff, because an unmatched one is either a
thread the show genuinely dropped at that exact seam, or two agents describing the
same thread in different words. Both are worth looking at.
"""
import argparse, difflib, json, pathlib, re, sys

STOP = set("a an the is are was were will would can could do does did to of in on at "
           "for and or but if it its he she they them his her their this that with "
           "be been being have has had who what why when how".split())


def key(q):
    """Loose fingerprint so two agents phrasing one question differently still match."""
    words = [w for w in re.findall(r"[a-z']+", (q or '').lower()) if w not in STOP]
    return " ".join(sorted(set(words)))


def similar(a, b):
    ka, kb = key(a), key(b)
    if not ka or not kb:
        return 0.0
    wa, wb = set(ka.split()), set(kb.split())
    jac = len(wa & wb) / len(wa | wb)
    return max(jac, difflib.SequenceMatcher(None, ka, kb).ratio())


def load(d):
    out = []
    for p in sorted(pathlib.Path(d).glob('*.json')):
        try:
            b = json.loads(p.read_text())
        except json.JSONDecodeError as ex:
            print(f'  skipping {p.name}: bad JSON ({ex})', file=sys.stderr)
            continue
        if 'episodes' not in b:
            continue
        rng = b.get('batch') or [None, None]
        out.append({'file': p.name, 'lo': rng[0], 'hi': rng[1],
                    'summary': (b.get('summary') or '').strip(),
                    'start': b.get('open_at_start') or [],
                    'end': b.get('open_at_end') or [],
                    'inherited': b.get('inherited') or []})
    out.sort(key=lambda x: (x['lo'] is None, x['lo']))
    return out


def stitch(blocks, thresh):
    """Match each block's open_at_end against the next block's open_at_start."""
    seams = []
    for a, b in zip(blocks, blocks[1:]):
        matched, used = [], set()
        for i, e in enumerate(a['end']):
            best, score = None, 0.0
            for j, s in enumerate(b['start']):
                if j in used:
                    continue
                sc = similar(e.get('q'), s.get('q'))
                if sc > score:
                    best, score = j, sc
            if best is not None and score >= thresh:
                used.add(best)
                matched.append((e, b['start'][best], score))
        seams.append({
            'from': a, 'to': b, 'matched': matched,
            'dropped': [e for k, e in enumerate(a['end'])
                        if not any(e is m[0] for m in matched)],
            'unclaimed': [s for j, s in enumerate(b['start']) if j not in used]})
    return seams


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True, help='directory of batch JSON')
    ap.add_argument('--out', required=True, help='Markdown file to write')
    ap.add_argument('--threshold', type=float, default=0.45,
                    help='similarity needed to call two questions the same (0-1)')
    a = ap.parse_args()

    blocks = load(a.dir)
    if not blocks:
        raise SystemExit(f'no batch JSON with an "episodes" key under {a.dir}')
    missing = [b['file'] for b in blocks if not b['summary']]
    seams = stitch(blocks, a.threshold)

    L = ['# Summary of the whole script', '',
         f'Built from {len(blocks)} blocks covering episodes '
         f'{blocks[0]["lo"]}-{blocks[-1]["hi"]}. Each block was read by a different '
         f'agent that saw nothing outside its own 25 episodes.', '',
         '---', '', '## The story, block by block', '']
    for b in blocks:
        L += [f'### Episodes {b["lo"]}-{b["hi"]}', '',
              b['summary'] or '_This block did not write a summary._', '']

    L += ['---', '', '## Where the blocks join', '',
          'Each agent listed the questions still hanging when its last episode ended, '
          'and the questions already running when its first episode began. Where those '
          'two lists agree, a thread crosses from one agent to the next.', '']
    tot_m = tot_d = tot_u = 0
    for s in seams:
        m, d, u = len(s['matched']), len(s['dropped']), len(s['unclaimed'])
        tot_m, tot_d, tot_u = tot_m + m, tot_d + d, tot_u + u
        L += [f'### ep {s["from"]["hi"]} → ep {s["to"]["lo"]}', '',
              f'**{m} carried across.**' if m else '**Nothing carried across.**', '']
        for e, st, sc in s['matched']:
            L.append(f'- {e.get("q")}')
        if d:
            L += ['', f'**{d} left hanging here and not picked up.** Either the show '
                      f'drops them at this point, or the next agent described them '
                      f'differently:', '']
            L += [f'- {e.get("q")} _(last raised ep {e.get("last_touched", "?")})_'
                  for e in s['dropped']]
        if u:
            L += ['', f'**{u} the next block treats as already running, that the '
                      f'previous block never handed on:**', '']
            L += [f'- {st.get("q")}' for st in s['unclaimed']]
        L.append('')

    L += ['---', '', '## How well the blocks joined', '',
          f'- carried across seams: **{tot_m}**',
          f'- left hanging, unclaimed: **{tot_d}**',
          f'- appeared without being handed on: **{tot_u}**', '']
    if tot_m == 0:
        L.append('> No thread crossed any seam. Either the agents did not fill in the '
                 'handoff lists, or they phrased the same question so differently that '
                 'nothing matched. Check a couple by hand before trusting this file.')
    elif tot_d > tot_m:
        L.append('> More threads were left hanging than carried across. Usually this '
                 'means agents phrased questions differently rather than the show '
                 'dropping that many. Lower --threshold and look again.')
    if missing:
        L.append(f'> Blocks with no summary: {", ".join(missing)}')

    pathlib.Path(a.out).write_text("\n".join(L), encoding='utf-8')
    words = sum(len(b['summary'].split()) for b in blocks)
    print(f'wrote {a.out}')
    print(f'  blocks {len(blocks)} · summary {words:,} words · seams {len(seams)}')
    print(f'  carried {tot_m} · hanging {tot_d} · unclaimed {tot_u}')
    if missing:
        print(f'  NO SUMMARY: {missing}')


if __name__ == '__main__':
    main()

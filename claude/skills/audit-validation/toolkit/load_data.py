#!/usr/bin/env python3
"""Load a retention export and a comments file into one normalised data.json.

    python load_data.py --retention <csv> --comments <csv> \
           --show "The Vampire Prince" --out data.json

Column names differ between exports, so every field is looked up through a list of
aliases and the loader reports what it actually matched. Read that report: a silently
missing column produces a document full of confident zeros.

The retention export usually carries a second show as a benchmark. Pass --show to
name the subject; whatever else is in the file is treated as the benchmark, matched
on cumulative hours rather than episode number because episode lengths differ.
"""
import argparse, csv, json, pathlib, re, statistics as st, sys

csv.field_size_limit(10 ** 7)

ALIASES = {
    'ep':      ['Story No.', 'Story no.', 'story_no', 'Episode', 'episode_number'],
    'drop':    ['CB D0+ Drop% d7', 'Drop % (Modified)', 'Drop %', 'drop_pct'],
    'listen':  ['CB D0+ d7', 'LDAU (Modified)', 'LDAU', 'listeners'],
    'hours':   ['Duration cum. (Hr)', 'Duration cum (Hr)', 'cum_hours'],
    'dur':     ['Duration (Hr)', 'duration_hr'],
    'c90':     ['%90 Comp', 'pct_90_comp'],
    'c50':     ['%50 Comp', 'pct_50_comp'],
    'revenue': ['ep_revenue', 'revenue'],
    'title':   ['Story Title', 'story_title', 'title'],
    'show':    ['Show Title', 'show_title'],
}
BASELINE_FROM = 51      # before this, drop is sampling, not story


def pick(fieldnames, names):
    low = {f.lower().strip(): f for f in fieldnames if f}
    for n in names:
        if n in fieldnames:
            return n
        if n.lower() in low:
            return low[n.lower()]
    return None


def num(x):
    try:
        return float(str(x).replace('%', '').replace(',', ''))
    except (TypeError, ValueError):
        return None


def load_retention(path, subject):
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
    if not rows:
        raise SystemExit(f'{path} is empty')
    cols = {k: pick(rows[0].keys(), v) for k, v in ALIASES.items()}
    print('  retention columns matched:')
    for k in ('ep', 'drop', 'listen', 'hours', 'c90', 'revenue'):
        print(f'    {k:<9} -> {cols[k] or "NOT FOUND"}')
    for need in ('ep', 'drop'):
        if not cols[need]:
            raise SystemExit(f'cannot continue without a {need} column')

    shows = {}
    for r in rows:
        name = (r.get(cols['show']) or 'unknown').strip()
        e = num(r.get(cols['ep']))
        if e is None:
            continue
        rec = {'ep': int(e)}
        for k in ('drop', 'listen', 'hours', 'dur', 'c90', 'c50', 'revenue'):
            rec[k] = num(r.get(cols[k])) if cols[k] else None
        rec['title'] = (r.get(cols['title']) or '').strip()
        shows.setdefault(name, {})[int(e)] = rec

    names = sorted(shows, key=lambda n: -len(shows[n]))
    print(f'\n  shows in the file: '
          + ', '.join(f'{n} ({len(shows[n])} eps)' for n in names))
    if subject not in shows:
        raise SystemExit(f'--show "{subject}" not in the file. Options: {names}')
    bench = [n for n in names if n != subject]
    print(f'  subject: {subject}   benchmark: {bench[0] if bench else "none"}')
    return shows[subject], (shows[bench[0]] if bench else {}), (bench[0] if bench else None)


def load_comments(path, subject=None):
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
    if not rows:
        return {}
    cols = rows[0].keys()
    c_text = pick(cols, ['comment', 'comment_text', 'text'])
    c_ep = pick(cols, ['episode_number', 'episode', 'story_no'])
    c_story = pick(cols, ['story_title', 'title'])
    c_like = pick(cols, ['like_count', 'likes'])
    c_show = pick(cols, ['show_title', 'show'])
    print(f'\n  comment columns: text -> {c_text}, episode -> '
          f'{c_ep or c_story + " (parsed)"}, likes -> {c_like}')

    out, unparsed = {}, 0
    for r in rows:
        if subject and c_show and (r.get(c_show) or '').strip() != subject:
            continue
        ep = num(r.get(c_ep)) if c_ep else None
        if ep is None and c_story:
            m = re.match(r'\s*ep\.?\s*(\d+)', r.get(c_story) or '', re.I)
            ep = int(m.group(1)) if m else None
        if ep is None:
            unparsed += 1
            continue
        out.setdefault(int(ep), []).append({
            'text': (r.get(c_text) or '').strip(),
            'likes': int(num(r.get(c_like)) or 0) if c_like else 0,
        })
    total = sum(len(v) for v in out.values())
    print(f'  {total} comments across {len(out)} episodes'
          + (f'   ({unparsed} had no episode and were dropped)' if unparsed else ''))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--retention', required=True)
    ap.add_argument('--comments')
    ap.add_argument('--show', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    print('loading')
    sub, bench, bench_name = load_retention(a.retention, a.show)
    comments = load_comments(a.comments, a.show) if a.comments else {}

    drops = {e: r['drop'] for e, r in sub.items() if r['drop'] is not None}
    late = [v for e, v in drops.items() if e >= BASELINE_FROM]
    baseline = st.median(late) if late else None

    # The benchmark is matched on cumulative hours, because episode lengths differ.
    # Both its RATE and its LEVEL are carried: the rate drives the ratios, the level
    # draws the curve an act is compared against. An earlier version imported only the
    # rate, and every per-act "vs benchmark" curve silently lost its second line.
    bench_at, bench_level = {}, {}
    if bench:
        bl = [(r['hours'], r['listen']) for r in bench.values()
              if r.get('hours') is not None and r.get('listen') is not None]
        for e, r in sub.items():
            if r.get('hours') is not None and bl:
                bench_level[e] = min(bl, key=lambda q: abs(q[0] - r['hours']))[1]
        bh = [(r['hours'], r['drop']) for r in bench.values()
              if r.get('hours') is not None and r.get('drop') is not None]
        for e, r in sub.items():
            if r.get('hours') is None or not bh:
                continue
            bench_at[e] = min(bh, key=lambda p: abs(p[0] - r['hours']))[1]

    early = [v for e, v in drops.items() if e < BASELINE_FROM]
    out = {
        'show': a.show, 'benchmark': bench_name,
        'baseline_from': BASELINE_FROM,
        'baseline_drop': baseline,
        'episodes': {str(e): sub[e] for e in sorted(sub)},
        'benchmark_drop_at': {str(e): v for e, v in bench_at.items()},
        'benchmark_level_at': {str(e): v for e, v in bench_level.items()},
        'comments': {str(e): v for e, v in sorted(comments.items())},
    }
    pathlib.Path(a.out).write_text(json.dumps(out, ensure_ascii=False))

    print(f'\nwrote {a.out}')
    print(f'  episodes            : {len(sub)}')
    print(f'  baseline drop (ep{BASELINE_FROM}+): {baseline * 100:.2f}%' if baseline else '')
    if early:
        print(f'  eps 1-{BASELINE_FROM - 1} mean drop : {st.mean(early) * 100:.2f}%'
              f'  ({st.mean(early) / baseline:.1f}x baseline)')
        print(f'    ^ early sampling, NOT a creative problem. Excluded from baseline.')
    if comments:
        busiest = sorted(comments, key=lambda e: -len(comments[e]))[:5]
        print(f'  busiest comment eps : '
              + ', '.join(f'{e} ({len(comments[e])})' for e in busiest))


if __name__ == '__main__':
    main()

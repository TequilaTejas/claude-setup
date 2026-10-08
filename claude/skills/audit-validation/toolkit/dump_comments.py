#!/usr/bin/env python3
"""Write one plain-text file per episode window, for the comment agents to read.

    python dump_comments.py --data data.json --windows 110-120 561-590 --out comment_windows/

Agents read text, not JSON-in-CSV. This also keeps each agent's input to exactly its
own window, so it cannot accidentally quote a comment from somewhere else.
"""
import argparse, json, pathlib


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--windows', nargs='+', help='e.g. 110-120 561-590')
    ap.add_argument('--balanced', type=int, metavar='N',
                    help='instead of named windows, split the whole run into N batches '
                         'of roughly equal comment count, for the sentiment pass')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    data = json.loads(pathlib.Path(a.data).read_text())
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    if not a.windows and not a.balanced:
        ap.error('pass --windows for named ranges or --balanced N for the whole run')

    windows = a.windows
    if a.balanced:
        # Equal comment count per batch, not equal episode count. Comment volume is
        # wildly uneven across a run — one episode drew 106 and most drew under ten —
        # so splitting by episode hands one agent ten times another's work.
        C = data['comments']
        eps = sorted((int(k) for k in C), key=int)
        total = sum(len(C[str(e)]) for e in eps)
        target = total / a.balanced
        windows, cur, n = [], [], 0
        for e_ in eps:
            cur.append(e_)
            n += len(C[str(e_)])
            if n >= target and len(windows) < a.balanced - 1:
                windows.append(f'{cur[0]}-{cur[-1]}')
                cur, n = [], 0
        if cur:
            windows.append(f'{cur[0]}-{cur[-1]}')

    for w in windows:
        lo, hi = (int(x) for x in w.split('-'))
        lines, n = [], 0
        for ep in range(lo, hi + 1):
            cs = data['comments'].get(str(ep), [])
            if not cs:
                continue
            lines.append(f'\n===== EPISODE {ep}  ({len(cs)} comments) =====')
            for c in sorted(cs, key=lambda x: -x['likes']):
                n += 1
                lines.append(f'[{c["likes"]} likes] {c["text"]}')
        f = out / f'eps_{lo}_{hi}.txt'
        f.write_text(f'Comments for episodes {lo}-{hi}\n'
                     f'{n} comments total\n' + "\n".join(lines), encoding='utf-8')
        print(f'  {f}  {n} comments')


if __name__ == '__main__':
    main()

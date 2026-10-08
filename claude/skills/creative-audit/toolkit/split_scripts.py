#!/usr/bin/env python3
"""Split CMS .docx scripts into one zero-padded .txt per episode.

    python split_scripts.py --in pack/scripts --out pack/scripts_txt

Reads every .docx in --in, splits on the `Ep N` header, writes epNNNN.txt, and
prints a gap report. Read the gap report: missing or duplicate episode numbers
change what you can claim about a span.

No dependency on python-docx; a .docx is a zip of XML.
"""
import argparse, pathlib, re, sys, zipfile
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
# Packs label episodes differently, and some use two labels at once: a real header
# ("Ep 367 — Very Soon") followed by a restatement in the body ("Chapter 367: Very
# Soon"). Treating every form as a header therefore invents duplicates. Instead,
# work out which label THIS pack uses, then honour only that one.
FAMILIES = [
    ('ep',      re.compile(r'^\s*(?:ep|episode)\.?\s*(\d{1,4})\s*(?:[—–\-:·|]\s*)?(.*)$', re.I)),
    ('chapter', re.compile(r'^\s*(?:chapter|chap)\.?\s*(\d{1,4})\s*(?:[—–\-:·|]\s*)?(.*)$', re.I)),
    ('part',    re.compile(r'^\s*(?:part|pt)\.?\s*(\d{1,4})\s*(?:[—–\-:·|]\s*)?(.*)$', re.I)),
    ('number',  re.compile(r'^\s*(\d{1,4})\s*[.)]\s*(.*)$')),
]


def head_match(line, pattern):
    """-> (episode number, title) or None."""
    m = pattern.match(line or '')
    if not m:
        return None
    return int(m.group(1)), (m.group(2) or '').strip()


def detect_family(lines):
    """Pick the label this pack uses: the one yielding the longest run of distinct,
    mostly increasing numbers. Ties go to the earlier family, so a real 'Ep N' header
    always beats a 'Chapter N' restatement of the same number in the body."""
    best = None
    for name, pat in FAMILIES:
        nums = [head_match(l, pat)[0] for l in lines if head_match(l, pat)]
        if not nums:
            continue
        distinct = len(set(nums))
        rising = sum(1 for a, b in zip(nums, nums[1:]) if b > a)
        score = (distinct, rising)
        if best is None or score > best[0]:
            best = (score, name, pat, distinct)
    return best


def paragraphs(path):
    with zipfile.ZipFile(path) as z:
        name = 'word/document.xml'
        if name not in z.namelist():
            raise SystemExit(f'{path.name}: no {name} — is this really a .docx?')
        root = ET.fromstring(z.read(name))
    for p in root.iter(f'{W}p'):
        txt = ''.join(t.text or '' for t in p.iter(f'{W}t'))
        # adjacent runs in the XML produce doubled spaces; collapse them
        yield re.sub(r'[ \t\u00a0]{2,}', ' ', txt).strip()


def split(paths):
    """-> {ep: (title, [lines])}, duplicates, and the label family detected."""
    all_lines = [l for path in paths for l in paragraphs(path)]
    found = detect_family(all_lines)
    if not found:
        return {}, [], None
    (_, family, pat, _) = found

    eps, dupes, cur = {}, [], None
    for path in paths:
        for line in paragraphs(path):
            m = head_match(line, pat) if line else None
            if m:
                n = m[0]
                if n in eps:
                    dupes.append((n, path.name))
                cur = n
                eps[n] = (m[1], [])
            elif cur is not None and line:
                eps[cur][1].append(line)
    return eps, dupes, family


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='src', required=True)
    ap.add_argument('--out', dest='dst', required=True)
    a = ap.parse_args()

    paths = sorted(pathlib.Path(a.src).glob('*.docx'))
    paths = [p for p in paths if not p.name.startswith('~$')]
    if not paths:
        raise SystemExit(f'no .docx under {a.src}')
    print(f'reading {len(paths)} file(s):')
    for p in paths:
        print(f'  {p.name}')

    eps, dupes, family = split(paths)
    if not eps:
        raise SystemExit(
            'No episode headers matched.\n'
            'Accepted: "Ep 1", "Episode 1", "Ep. 1", "Chapter 1", "Part 1", "1." —\n'
            'each optionally followed by a dash, colon or middot and a title.\n'
            'Print the first 20 lines of a .docx and widen HEAD in this script.')

    out = pathlib.Path(a.dst)
    out.mkdir(parents=True, exist_ok=True)
    thin = []
    for n, (title, lines) in sorted(eps.items()):
        head = f'Ep {n}' + (f' — {title}' if title else '')
        body = '\n\n'.join(lines)
        (out / f'ep{n:04d}.txt').write_text(head + '\n\n' + body + '\n', encoding='utf-8')
        if len(body) < 2000:
            thin.append((n, len(body)))

    nums = sorted(eps)
    lo, hi = nums[0], nums[-1]
    missing = [n for n in range(lo, hi + 1) if n not in eps]

    print(f'\nwrote {len(eps)} episodes to {out}/  (ep {lo}–{hi})')
    print(f'  episode label used: "{family}"  (other labels in the text were '
          f'treated as body copy)')
    print('=' * 52)
    print('GAP REPORT')
    print(f'  missing   : {missing if missing else "none"}')
    print(f'  duplicates: {dupes if dupes else "none"}')
    print(f'  thin (<2KB, suspect split): {thin if thin else "none"}')
    if lo != 1:
        print(f'  NOTE: numbering starts at {lo}, not 1')
    print('=' * 52)
    if missing or dupes or thin:
        print('Resolve these before extraction. A gap changes what you can claim\n'
              'about a hook span.')
        sys.exit(1)


if __name__ == '__main__':
    main()

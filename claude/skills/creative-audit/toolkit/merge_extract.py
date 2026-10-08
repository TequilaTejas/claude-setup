#!/usr/bin/env python3
"""Merge per-batch extraction JSON into one ledger.

    python merge_extract.py --dir extract/ --out ledger.json [--first 1 --last 268]

Validates every record against the schema in references/extraction-prompt.md,
reports episodes missing from the batches, and builds the raw thread timeline.
Exits non-zero on any missing episode: re-run that batch rather than proceeding.
"""
import argparse, collections, json, pathlib, sys

# 'decision' and 'choice' were produced by real agents and are valid kinds of
# question; rejecting them threw complaints on sound records.
KINDS = {'threat', 'mystery', 'relationship', 'identity', 'goal', 'debt',
         'decision', 'choice'}
HOWS = {'onscreen', 'offscreen', 'deflected', 'dropped'}
LEADS = {'drives', 'present_passive', 'absent'}
BEATS = {'new', 'escalates', 're-runs'}
# a cliffhanger can equally pose a mystery or a question outright
CTYPES = {'threat', 'reveal', 'arrival', 'decision', 'mystery', 'question',
          'none'}


def load(d):
    batches = []
    for p in sorted(pathlib.Path(d).glob('*.json')):
        try:
            batches.append((p.name, json.loads(p.read_text())))
        except json.JSONDecodeError as e:
            print(f'  BAD JSON {p.name}: {e}', file=sys.stderr)
    if not batches:
        raise SystemExit(f'no .json under {d}')
    return batches


def validate(name, b):
    """-> list of complaint strings."""
    bad = []
    lo, hi = (b.get('batch') or [None, None])[:2]
    for e in b.get('episodes', []):
        n = e.get('ep')
        at = f'{name} ep{n}'
        if not isinstance(n, int):
            bad.append(f'{name}: episode with no integer ep: {e!r:.80}')
            continue
        if e.get('flag') == 'FILE MISSING':
            continue
        if isinstance(lo, int) and not (lo <= n <= hi):
            bad.append(f'{at}: outside declared batch {lo}-{hi} — DISCARD, the agent '
                       f'guessed across batches')
        for o in e.get('opens') or []:
            if not o.get('q', '').strip():
                bad.append(f'{at}: open with empty q')
            if o.get('kind') not in KINDS:
                bad.append(f'{at}: bad kind {o.get("kind")!r}')
            if o.get('force') not in (1, 2, 3):
                bad.append(f'{at}: bad force {o.get("force")!r}')
            if not str(o.get('evidence', '')).strip():
                bad.append(f'{at}: open "{o.get("q", "")[:40]}" has no evidence')
        for c in e.get('closes') or []:
            if not c.get('q', '').strip():
                bad.append(f'{at}: close with empty q')
            if c.get('how') not in HOWS:
                bad.append(f'{at}: bad how {c.get("how")!r}')
        ld = e.get('leads')
        if isinstance(ld, dict):
            for who, v in ld.items():
                if v not in LEADS:
                    bad.append(f'{at}: bad leads[{who}] {v!r}')
        elif e.get('lead') in LEADS:
            bad.append(f'{at}: LEGACY single `lead` field — ambiguous for a two-lead '
                       f'show; re-run this batch with the {{LEADS}} prompt')
        else:
            bad.append(f'{at}: no usable leads/lead field')
        if e.get('beat') not in BEATS:
            bad.append(f'{at}: bad beat {e.get("beat")!r}')
        cl = e.get('cliff')
        if isinstance(cl, dict) and cl.get('type') not in CTYPES:
            bad.append(f'{at}: bad cliff.type {cl.get("type")!r}')
    return bad


def _name_of(nm):
    """Agents return new_names as a bare string or as {name, note?}. Accept both."""
    if isinstance(nm, dict):
        return str(nm.get('name') or '').strip()
    return str(nm or '').strip()


def _first_appearance(eps, nums):
    """{episode: [names first named at that episode, show-wide]}.

    Batches disagree on whether `new_names` means new-to-batch or new-to-show, so the
    show-wide first mention is the only comparable figure."""
    seen, out = set(), {}
    for n in nums:
        names = [_name_of(nm) for nm in (eps[n].get('new_names') or [])]
        fresh = [nm for nm in names if nm and nm not in seen]
        seen.update(fresh)
        if fresh:
            out[str(n)] = fresh
    return out


def _agency(eps, nums):
    """Per-lead episodes where that lead is not driving. Falls back to the legacy
    single `lead` field, marking it ambiguous so it is not mistaken for per-lead data."""
    out = collections.defaultdict(list)
    for n in nums:
        ld = eps[n].get('leads')
        if isinstance(ld, dict):
            for who, v in ld.items():
                if v in ('present_passive', 'absent'):
                    out[who].append(n)
        elif eps[n].get('lead') in ('present_passive', 'absent'):
            out['(unnamed lead — LEGACY, ambiguous)'].append(n)
    return dict(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--leads', help='dir of single-field repair JSON (see '
                                    'references/leads-repair-prompt.md); overrides '
                                    'the extraction batches for the leads field')
    ap.add_argument('--first', type=int)
    ap.add_argument('--last', type=int)
    a = ap.parse_args()

    batches = load(a.dir)
    print(f'merging {len(batches)} batch file(s)')

    eps, seen, complaints, discarded = {}, collections.Counter(), [], []
    inherited = []
    for name, b in batches:
        complaints += validate(name, b)
        for q in b.get('inherited') or []:
            inherited.append({**q, 'batch': b.get('batch')})
        blo, bhi = (b.get('batch') or [None, None])[:2]
        for e in b.get('episodes', []):
            n = e.get('ep')
            if not isinstance(n, int):
                continue
            if isinstance(blo, int) and not (blo <= n <= bhi):
                discarded.append((name, n))      # agent guessed outside its range
                continue
            seen[n] += 1
            eps.setdefault(n, e)

    if not eps:
        raise SystemExit('no valid episodes in any batch')

    repaired = 0
    if a.leads:
        for rp in sorted(pathlib.Path(a.leads).glob('*.json')):
            try:
                r = json.loads(rp.read_text())
            except json.JSONDecodeError as ex:
                complaints.append(f'{rp.name}: bad JSON: {ex}')
                continue
            for rec in r.get('episodes', []):
                n, ld = rec.get('ep'), rec.get('leads')
                if isinstance(n, int) and isinstance(ld, dict) and n in eps:
                    eps[n]['leads'] = ld
                    eps[n].pop('lead', None)          # legacy value is now superseded
                    if rec.get('note'):
                        eps[n]['leads_note'] = rec['note']
                    repaired += 1
        # repaired records satisfy the schema; drop the legacy complaints they fixed
        complaints[:] = [c for c in complaints if 'LEGACY single `lead`' not in c]
        print(f'leads repair: overlaid {repaired} episode(s) from {a.leads}')

    nums = sorted(eps)
    lo = a.first if a.first else nums[0]
    hi = a.last if a.last else nums[-1]
    # --first/--last bound the report, not just the gap check: an episode outside the
    # declared range must not inflate the counts below.
    outside = [n for n in nums if not (lo <= n <= hi)]
    for n in outside:
        del eps[n]
        seen.pop(n, None)
    nums = sorted(eps)
    if not nums:
        raise SystemExit(f'no episodes inside the declared range {lo}-{hi}')
    missing = [n for n in range(lo, hi + 1) if n not in eps]
    dupes = [n for n, c in seen.items() if c > 1]
    filemissing = [n for n, e in eps.items() if e.get('flag') == 'FILE MISSING']

    # raw thread timeline: every distinct question string, first open -> close
    threads = collections.OrderedDict()
    for n in nums:
        e = eps[n]
        for o in e.get('opens') or []:
            t = threads.setdefault(o['q'], {'q': o['q'], 'kind': o.get('kind'),
                                            'opens': n, 'touches': [], 'closed': None,
                                            'how': None, 'max_force': 0})
            t['touches'].append(n)
            t['max_force'] = max(t['max_force'], o.get('force') or 0)
        for c in e.get('closes') or []:
            t = threads.get(c['q'])
            if t is None:
                t = threads.setdefault(c['q'], {'q': c['q'], 'kind': None, 'opens': None,
                                                'touches': [], 'closed': None, 'how': None,
                                                'max_force': 0, 'note': 'closed without a '
                                                'recorded open — likely inherited'})
            if t['closed'] is None:
                t['closed'], t['how'] = n, c.get('how')

    for t in threads.values():
        o, c = t['opens'], t['closed']
        t['span'] = (c - o) if (isinstance(o, int) and isinstance(c, int)) else None
        t['recurrence'] = len(set(t['touches']))
        t['last_touch'] = max(t['touches']) if t['touches'] else None

    drift = {
        'no_question_eps': [n for n in nums
                            if not ((eps[n].get('cliff') or {}).get('posed_as_question'))],
        'lead_not_driving': _agency(eps, nums),
        'reruns': [n for n in nums if eps[n].get('beat') == 're-runs'],
        'flags': [{'ep': n, 'flag': eps[n]['flag']} for n in nums if eps[n].get('flag')],
        'new_names_by_ep': {str(n): [_name_of(x) for x in eps[n]['new_names']]
                            for n in nums if eps[n].get('new_names')},
        # Batches disagree on whether new_names means new-to-batch or new-to-show, so
        # derive first-appearance globally: the earliest episode any batch names them.
        'first_appearance': _first_appearance(eps, nums),
    }

    out = {
        'range': [lo, hi],
        'episodes_present': len(eps),
        'inherited': inherited,
        'episodes': [eps[n] for n in nums],
        'threads_raw': list(threads.values()),
        'drift_signals': drift,
    }
    pathlib.Path(a.out).write_text(json.dumps(out, indent=2, ensure_ascii=False))

    print(f'\nwrote {a.out}')
    print('=' * 52)
    print(f'  episodes      : {len(eps)} of {hi - lo + 1} in range {lo}-{hi}'
          + (f'   ({len(outside)} outside the range, excluded)' if outside else ''))
    if a.leads:
        stale = [n for n in nums if not isinstance(eps[n].get('leads'), dict)]
        print(f'  leads repaired: {repaired}'
              + (f'   STILL LEGACY: {stale[:20]}' if stale else '   (all episodes)'))
    print(f'  raw threads   : {len(threads)}   (cluster these by hand — most are '
          f'the same hook rephrased)')
    print(f'  inherited     : {len(inherited)}')
    print(f'  missing       : {missing if missing else "none"}')
    print(f'  FILE MISSING  : {filemissing if filemissing else "none"}')
    print(f'  overlapping   : {sorted(dupes) if dupes else "none"}')
    print(f'  discarded     : {discarded if discarded else "none"}'
          f'{"   (out-of-range guesses)" if discarded else ""}')
    print(f'  no question at episode end : {len(drift["no_question_eps"])} eps')
    for who, eplist in (drift['lead_not_driving'] or {}).items():
        print(f'  not driving · {who:<28}: {len(eplist)} eps')
    print(f'  re-run beats               : {len(drift["reruns"])} eps')
    fa = drift['first_appearance']
    print(f'  distinct named characters  : {sum(len(v) for v in fa.values())} '
          f'(first-appearance normalised show-wide)')
    print(f'  agent flags                : {len(drift["flags"])}')
    print('=' * 52)

    if complaints:
        print(f'\n{len(complaints)} SCHEMA COMPLAINT(S):')
        for c in complaints[:40]:
            print(f'  {c}')
        if len(complaints) > 40:
            print(f'  … and {len(complaints) - 40} more')

    if missing:
        print('\nMISSING EPISODES — re-run those batches before Phase 3.')
        sys.exit(1)
    if complaints:
        sys.exit(2)


if __name__ == '__main__':
    main()

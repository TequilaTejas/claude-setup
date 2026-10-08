#!/usr/bin/env python3
"""Export everything the Creative Audit claims, as data.

    python export_claims.py --build build.py --out claims.json

The audit's findings live as Python constants inside the show's build script, which
makes them unreadable to anything else. This lifts them into one file so another
tool -- the `audit-validation` skill -- can test them without importing a renderer.

It imports the build script rather than parsing it, so what comes out is exactly what
the report renders. Nothing is re-derived here.
"""
import argparse, importlib.util, json, pathlib, sys


def load(path):
    p = pathlib.Path(path).resolve()
    spec = importlib.util.spec_from_file_location('showbuild', p)
    mod = importlib.util.module_from_spec(spec)
    sys.argv = [str(p)]                      # the module parses argv at main() only
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', required=True, help="the show's build.py")
    ap.add_argument('--arcs', help='arcs.json, to carry act names and evidence through')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    m = load(a.build)
    arcs = json.loads(pathlib.Path(a.arcs).read_text())['arcs'] if a.arcs else []

    claims = {
        'promise': getattr(m, 'LEAD', '').strip(),
        'hooks': [
            {'code': h['code'], 'question': h['q'], 'kind': h.get('kind'),
             'opens': h['opens'], 'resolves': h.get('resolves'),
             'pull': sum(h['pull']), 'pull_axes': list(h['pull']),
             'verdict': h['verdict'], 'status': h.get('status', ''),
             'note': h.get('note', '')}
            for h in getattr(m, 'HOOKS', [])],
        'breaks': [
            {'code': b['code'], 'hook': b.get('hook'), 'title': b.get('title', ''),
             'what': b.get('what', ''),
             'promised_ep': b['promised'][1], 'promised_line': b['promised'][0],
             'broke_ep': b['broke'][1], 'broke_line': b['broke'][0]}
            for b in getattr(m, 'BREAKS', [])],
        'trouble': [
            {'code': d['code'], 'from': d['eps'][0], 'to': d['eps'][1],
             'signal': d['signal'], 'severity': d['severity'],
             'story': d.get('story', ''), 'evidence': d.get('evidence', ''),
             'prose': d.get('prose', [])}
            for d in getattr(m, 'DRIFT', [])],
        'acts': [
            {'id': x['id'], 'name': x.get('name'), 'from': x['from'], 'to': x['to'],
             'boundary_evidence': x.get('boundary_evidence')}
            for x in arcs],
        'act_notes': {k: v.get('note', '')
                      for k, v in getattr(m, 'ACT_STORIES', {}).items()},
        'cast': [{'name': n, 'who': w} for n, w in getattr(m, 'CAST', [])],
    }
    pathlib.Path(a.out).write_text(json.dumps(claims, indent=2, ensure_ascii=False))

    print(f'wrote {a.out}')
    for k in ('hooks', 'breaks', 'trouble', 'acts'):
        print(f'  {k:<9} {len(claims[k])}')
    notes = sum(1 for v in claims['act_notes'].values() if v)
    print(f'  act notes {notes}   (judgment lines, one per act)')
    if not claims['trouble']:
        print('\n  WARNING: no trouble zones found. Check that --build points at the '
              'show\'s build.py, not the skill template.')


if __name__ == '__main__':
    main()

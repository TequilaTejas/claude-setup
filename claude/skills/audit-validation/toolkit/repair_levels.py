#!/usr/bin/env python3
"""Repair the retention LEVEL series before anything reads it.

    python repair_levels.py --data data.json --out data.json

Audience level can only fall. Any episode where it rises is a data defect, and the
donor brief documents real cases: The Vampire Prince ep 270 arrived as 15,019 against
neighbours of ~7,500, an exact double-count, which made the show look like it gained
6,900 listeners. Uncorrected, every level-based number downstream is wrong.

Three defects, all seen in real packs:
  · a spike above the previous episode (double-count)    -> interpolate
  · a zero or missing level on a real episode            -> interpolate
  · a slow rise across several episodes (late-run noise) -> interpolate

The `drop` column is a separate metric and is left alone.
"""
import argparse, json, pathlib

RISE = 1.12     # >12% above the previous level is a defect, per the donor brief
DIP = 0.05      # a one-episode fall that recovers by >5% next episode is an artifact


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--from-ep', type=int, default=2)
    a = ap.parse_args()

    d = json.loads(pathlib.Path(a.data).read_text())
    eps = d['episodes']
    nums = sorted(int(k) for k in eps)
    last = nums[-1]

    lv = {n: (eps[str(n)] or {}).get('listen') for n in nums}
    bad = []

    # 1 · zero or missing level on a real episode
    for n in nums:
        if n >= a.from_ep and (lv[n] is None or lv[n] <= 0):
            bad.append((n, lv[n], 'zero or missing'))

    # 2 · a spike above the previous episode: a double-count.
    #     Compare against the immediately previous episode only. An earlier version
    #     held the last *accepted* value as the reference, so one low outlier made
    #     every episode after it look like a rise and flagged 140 of 665 episodes.
    # 3 · a one-episode dip that recovers: audience level cannot come back, so a V is
    #     an artifact of that single row, not behaviour.
    #     Small upward wiggles below RISE are measurement noise and are left alone:
    #     69 of them exist in this show and none is a defect.
    for i, n in enumerate(nums):
        if n < a.from_ep or not lv[n]:
            continue
        pv = lv.get(n - 1)
        nx = lv.get(n + 1)
        if pv and lv[n] > pv * RISE:
            bad.append((n, lv[n], f'spike, {lv[n] / pv:.2f}x the previous episode'))
        elif pv and nx and lv[n] < pv * (1 - DIP) and nx > lv[n] * (1 + DIP):
            bad.append((n, lv[n],
                        f'dips {(1 - lv[n] / pv) * 100:.1f}% and recovers '
                        f'{(nx / lv[n] - 1) * 100:.1f}% next episode'))

    badset = {n for n, _, _ in bad}

    def nearest_good(n, step):
        k = n + step
        while 1 <= k <= last:
            if k not in badset and lv.get(k):
                return k, lv[k]
            k += step
        return None, None

    for n, _, _ in bad:
        ln, lvl = nearest_good(n, -1)
        rn, rvl = nearest_good(n, +1)
        if lvl is not None and rvl is not None:
            f = (n - ln) / (rn - ln)
            fixed = lvl + (rvl - lvl) * f
        elif lvl is not None:
            fixed = lvl
        elif rvl is not None:
            fixed = rvl
        else:
            continue
        eps[str(n)]['listen'] = round(fixed, 1)
        eps[str(n)]['listen_repaired'] = True

    # survival headline, computed from the repaired level series
    base = d.get('baseline_from', 51)
    good = [n for n in nums if n >= base and (eps[str(n)] or {}).get('listen')]
    if good:
        a0, b0 = eps[str(good[0])]['listen'], eps[str(good[-1])]['listen']
        n_eps = good[-1] - good[0]
        d['level'] = {
            'from_ep': good[0], 'to_ep': good[-1],
            'from_listeners': a0, 'to_listeners': b0,
            'survival_pct': b0 / a0 * 100,
            'per_episode_decline': 1 - (b0 / a0) ** (1 / n_eps) if n_eps else 0,
            'repaired_episodes': sorted(badset),
        }

    pathlib.Path(a.out).write_text(json.dumps(d))
    print(f'wrote {a.out}')
    print(f'  {len(bad)} level defect(s) repaired by interpolation:')
    for n, was, why in bad[:20]:
        print(f'    ep {n}: {was} — {why} -> {eps[str(n)]["listen"]:,.1f}')
    if len(bad) > 20:
        print(f'    … and {len(bad) - 20} more')
    L = d.get('level')
    if L:
        print(f'\n  SURVIVAL: of 100 listeners at ep {L["from_ep"]}, '
              f'{L["survival_pct"]:.1f} reach ep {L["to_ep"]}  '
              f'({L["from_listeners"]:,.0f} -> {L["to_listeners"]:,.0f})')
        print(f'  baseline level decline: {L["per_episode_decline"] * 100:.4f}% '
              f'per episode')


if __name__ == '__main__':
    main()

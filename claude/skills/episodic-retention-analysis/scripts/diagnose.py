#!/usr/bin/env python3
"""
Diagnostic pass for a Pocket FM-style episodic retention CSV export.

Run this FIRST, before writing a single Key Spikes row. It prints everything
a human needs to make the judgment calls the report requires: benchmark
ratios, individual-episode spikes, release-cadence structure (batches,
same-day dumps, hiatuses), and noise-floor warnings for small-audience shows.

Usage:
    python diagnose.py "<path to show CSV>" [--show-id SHOW_ID] \
        [--tab-path "<path to TAB CSV>"] [--tab-show-id TAB_SHOW_ID]

--show-id: only needed if the CSV export is mixed with another show's rows
    (this happens — always check the unique Show ID count before trusting
    a file; see SKILL.md step 1).
"""
import argparse
import csv
import statistics
from collections import Counter

DEFAULT_TAB_PATH = "/Users/tejas/Downloads/TAB Data/TAB_FULL_701eps.csv"
DEFAULT_TAB_SHOW_ID = "cbc35fa13bbe154873ec97f78f2b4cf4b66c7d31"

MEGA_DUMP_THRESHOLD = 15   # episodes on one Launch Date -> flag as a same-day dump
HIATUS_DAYS = 14           # gap between batches -> flag as a real hiatus
SMALL_SHOW_BASELINE = 1000 # Ep51 LDAU below this -> noise-floor warning mode
NOISE_FLOOR_LDAU = 50      # absolute LDAU below this -> per-episode numbers are noise


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load(path, show_id_filter=None):
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    data = []
    for r in rows:
        if show_id_filter and r.get("Show ID") != show_id_filter:
            continue
        drop = r.get("CB D0+ Drop% overall")
        if drop in (None, ""):
            drop = r.get("CB D0+ Drop% d7")
        data.append({
            "ep": int(r["Story No."]),
            "title": r["Story Title"],
            "ldau": int(r["Total LDAU"]),
            "drop": fnum(drop),
            "launch": r["Launch Date"],
            "comp90": fnum(r.get("%90 Comp")),
        })
    data.sort(key=lambda x: x["ep"])
    return data


def check_mixed_show_ids(path):
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    ids = {}
    for r in rows:
        ids.setdefault(r["Show ID"], set()).add(r["Show Title"])
    return ids


def block_drops(data, block=20, min_ep=51, max_ep=None):
    max_ep = max_ep or data[-1]["ep"]
    blocks = []
    for start in range(min_ep, max_ep + 1, block):
        br = [d for d in data if start <= d["ep"] < start + block]
        if len(br) < 2:
            continue
        s, e = br[0]["ldau"], br[-1]["ldau"]
        if s == 0:
            continue
        blocks.append({
            "range": f"{br[0]['ep']}-{br[-1]['ep']}",
            "start_ep": br[0]["ep"],
            "s": s, "e": e,
            "drop": (s - e) / s,
        })
    return blocks


def find_batch_openers(data):
    openers = set()
    for i in range(1, len(data)):
        if data[i]["launch"] != data[i - 1]["launch"]:
            openers.add(data[i]["ep"])
    return openers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--show-id", default=None)
    ap.add_argument("--tab-path", default=DEFAULT_TAB_PATH)
    ap.add_argument("--tab-show-id", default=DEFAULT_TAB_SHOW_ID)
    args = ap.parse_args()

    print(f"=== Show ID check: {args.csv_path} ===")
    ids = check_mixed_show_ids(args.csv_path)
    if len(ids) > 1:
        print(f"  WARNING: file contains {len(ids)} distinct show_ids — pass --show-id to filter:")
        for sid, titles in ids.items():
            print(f"    {sid}  {titles}")
        if not args.show_id:
            print("  (proceeding WITHOUT a filter will corrupt every stat below — re-run with --show-id)")
            return
    else:
        (sid, titles), = ids.items()
        print(f"  clean single-show file: {titles} ({sid})")

    show = load(args.csv_path, args.show_id)
    tab = load(args.tab_path, args.tab_show_id)
    n = len(show)
    tab_by_ep = {d["ep"]: d for d in tab}

    print(f"\n=== Basics ===")
    print(f"  episodes: {n}")
    print(f"  Ep1 LDAU: {show[0]['ldau']}")
    if n > 50:
        baseline = show[50]["ldau"]
        final = show[-1]
        print(f"  Ep51 LDAU (baseline): {baseline}")
        print(f"  final Ep{final['ep']} LDAU: {final['ldau']}  ({final['title']})")
        print(f"  retention Ep51->final: {final['ldau']/baseline*100:.1f}%")

        cap_ep = min(final["ep"], 701)
        tab_baseline = tab[50]["ldau"]
        tf = tab_by_ep.get(cap_ep)
        show_at_cap = next((d for d in show if d["ep"] == cap_ep), None)
        if tf and show_at_cap:
            tab_ret = tf["ldau"] / tab_baseline
            show_ret_at_cap = show_at_cap["ldau"] / baseline
            ratio = show_ret_at_cap / tab_ret if tab_ret else None
            print(f"  show retention Ep51->{cap_ep}: {show_ret_at_cap*100:.1f}%  (fair comparison point)")
            print(f"  TAB retention Ep51->{cap_ep}: {tab_ret*100:.1f}%")
            if ratio:
                print(f"  -> benchmark ratio at Ep{cap_ep}: {ratio:.2f}x TAB's retention "
                      f"({'beats' if ratio > 1 else 'trails'} benchmark)")
        if final["ep"] > 701:
            print(f"  NOTE: show runs {final['ep'] - 701} episodes past TAB's 701-ep tracked range —")
            print(f"        anything past Ep701 is directional only, no benchmark ratio applies.")
            print(f"        (the 'retention Ep51->final' line above is NOT comparable to TAB's number —")
            print(f"         use the Ep51->{cap_ep} figures above for the fair headline stat.)")
        if baseline < SMALL_SHOW_BASELINE:
            print(f"  NOISE-FLOOR WARNING: Ep51 baseline ({baseline}) is small.")
            print(f"        Watch for the episode where LDAU first drops below {NOISE_FLOOR_LDAU} —")
            print(f"        past that point, treat block ratios as directional only, not diagnosis.")
    else:
        print("  fewer than 51 episodes — baseline convention doesn't apply, judge case by case.")

    print(f"\n=== Release cadence ===")
    launch_counts = Counter(d["launch"] for d in show)
    print(f"  {len(launch_counts)} distinct release batches over {n} episodes")
    mega_dumps = {d: c for d, c in launch_counts.items() if c >= MEGA_DUMP_THRESHOLD}
    if mega_dumps:
        print(f"  MEGA-DUMP WARNING: {len(mega_dumps)} date(s) carried >= {MEGA_DUMP_THRESHOLD} episodes:")
        for d, c in sorted(mega_dumps.items()):
            print(f"    {d}: {c} episodes")
        print(f"  -> any block whose window falls inside one of these dates compresses real time;")
        print(f"     read its TAB ratio as a release-cadence artifact first, story signal second.")
    dates_sorted = sorted(launch_counts.keys())
    from datetime import datetime
    gaps = []
    for a, b in zip(dates_sorted, dates_sorted[1:]):
        da = datetime.fromisoformat(a.split(" ")[0])
        db = datetime.fromisoformat(b.split(" ")[0])
        gap = (db - da).days
        if gap >= HIATUS_DAYS:
            gaps.append((a, b, gap))
    if gaps:
        print(f"  HIATUS WARNING: {len(gaps)} gap(s) of >= {HIATUS_DAYS} days between batches:")
        for a, b, g in gaps:
            print(f"    {a} -> {b}  ({g} days)")

    print(f"\n=== Block-level benchmark ratios (20-ep blocks from Ep51) ===")
    if n > 51:
        max_ep = min(n, 701)
        cb = block_drops(show, max_ep=max_ep)
        tb = block_drops(tab, max_ep=max_ep)
        tb_map = {b["start_ep"]: b for b in tb}
        for b in cb:
            t = tb_map.get(b["start_ep"])
            if not t or not t["drop"]:
                continue
            ratio = b["drop"] / t["drop"]
            flag = "  <<<" if (ratio >= 1.5 or ratio <= 0.5) else ""
            print(f"  {b['range']:>10}  drop={b['drop']*100:5.1f}%  tab={t['drop']*100:5.1f}%  "
                  f"ratio={ratio:5.2f}x  start_ldau={b['s']:>7}{flag}")

    print(f"\n=== Top 20 individual-episode spikes (excl. Ep1, excl. batch openers) ===")
    openers = find_batch_openers(show)
    cand = [d for d in show if d["ep"] > 1 and d["ep"] not in openers and d["drop"] is not None]
    cand.sort(key=lambda d: d["drop"])
    for d in cand[:20]:
        print(f"  ep{d['ep']:>4} {d['title'][:38]:<38} {d['drop']*100:6.2f}%  ldau={d['ldau']}")

    print(f"\n=== Completion rate (%90 Comp) trend, 80-ep windows ===")
    for start in range(1, n, 80):
        block = [d["comp90"] for d in show if start <= d["ep"] < start + 80 and d["comp90"] is not None]
        if block:
            print(f"  {start}-{start+79}: {statistics.mean(block)*100:.1f}%")

    print(f"\nDone. Cross-reference this output against SKILL.md's decision rules")
    print(f"to draft Key Spikes rows, the headline, and Overall bullets by hand.")


if __name__ == "__main__":
    main()

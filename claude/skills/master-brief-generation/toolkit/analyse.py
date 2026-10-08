# -*- coding: utf-8 -*-
"""
analyse.py — STEP 1 of producing a cliff report. Run this BEFORE reading any story.

Does the whole numeric pass on a data pack:
  * parses the episodic CSV, the summaries and every comments file
  * finds corrupt LDAU rows (Trap 1) and interpolates the level curve
  * builds the block-ratio table against the TAB benchmark
  * classifies every flagged block against the four traps
  * prints comment quotes for each flagged window

Usage:
    python analyse.py --pack /path/to/unzipped_pack --show-id <id>
    python analyse.py --pack ./pack            # show_id read from show_id.txt

Output: a printed report + analysis.json for the generator to consume.
"""
import argparse, csv, glob, json, os, re, sys
from collections import defaultdict

TAB_ID = "cbc35fa13bbe154873ec97f78f2b4cf4b66c7d31"

def fv(x):
    try: return float(str(x).replace("%", "").strip())
    except Exception: return None

# ------------------------------------------------------------------ loading
def load_episodic(path):
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8", errors="replace")))
    shows = defaultdict(dict)
    for r in rows:
        try: n = int(float(r["Story no."]))
        except Exception: continue
        shows[r["show_id"]][n] = r
    return shows

def load_summaries(path):
    txt = open(path, encoding="utf-8").read()
    eps = {}
    for pat in (r"\*\*Episode (\d+) — (.+?)\*\*\n(.*?)(?=\n\*\*Episode |\Z)",
                r"### Episode (\d+) — (.+?)\n(.*?)(?=\n### Episode |\Z)"):
        for m in re.finditer(pat, txt, re.S):
            eps[int(m.group(1))] = (m.group(2).strip(), re.sub(r"\s+", " ", m.group(3).strip()))
        if eps: break
    return eps

def load_comments(folder):
    """Handles every column layout seen in the packs so far."""
    by_ep = defaultdict(list)
    for f in glob.glob(os.path.join(folder, "**", "*.csv"), recursive=True):
        for r in csv.DictReader(open(f, encoding="utf-8", errors="replace")):
            c = (r.get("comment") or r.get("comment_text") or "").strip()
            e = r.get("episode_number")
            if not e:
                m = re.search(r"Ep\s*(\d+)", str(r.get("story_title")))
                e = m.group(1) if m else None
            try: e = int(float(e))
            except Exception: continue
            if c: by_ep[e].append(c)
    return by_ep

# ------------------------------------------------------- trap 1: corrupt LDAU
def clean_levels(show, lo, hi):
    """Level can only fall. A >12% rise is a data defect (VP ep270, WD ep183)."""
    es = [e for e in range(lo, hi + 1) if e in show]
    lv = {e: fv(show[e]["LDAU (Modified)"]) for e in es}
    bad = []
    for i, e in enumerate(es):
        if i == 0 or i == len(es) - 1: continue
        pv, nx = lv[es[i - 1]], lv[es[i + 1]]
        if lv[e] and pv and lv[e] > pv * 1.12:
            bad.append((e, lv[e], pv)); lv[e] = (pv + nx) / 2.0
    return lv, bad

# ------------------------------------------------------------- the block table
def block_table(SHOW, TAB, lv, lo, hi, size):
    hr = lambda m, e: fv(m[e]["Duration cum. (HR)"])
    dr = lambda m, e: abs(fv(m[e]["Drop % (Modified)"])) * 100
    tab_at = lambda H: min(TAB, key=lambda e: abs(hr(TAB, e) - H))
    base, out, prev = lv[lo], [], None
    for s in range(lo, hi + 1, size):
        t = min(s + size - 1, hi)
        es = [e for e in range(s, t + 1) if e in SHOW]
        # a trailing stub (e.g. 2 episodes) yields a meaningless ratio - drop it
        if len(es) < max(3, size // 2): continue
        a = sum(dr(SHOW, e) for e in es) / len(es)
        b = sum(dr(TAB, tab_at(hr(SHOW, e))) for e in es) / len(es)
        lost = (prev - lv[es[-1]]) if prev else 0
        out.append(dict(ep_lo=s, ep_hi=t, show_drop=round(a, 2), tab_drop=round(b, 2),
                        ratio=round(a / b, 2) if b else None,
                        level_pct=round(100 * lv[es[-1]] / base, 1), lost=round(lost)))
        prev = lv[es[-1]]
    return out

# --------------------------------------------- the four traps -> classification
# Three DISTINCT complaint classes. Lumping them together inflates the baseline
# and stops the paywall rule from ever firing (learned the hard way on VP).
PAYWALL  = re.compile(r"coin|unlock|free (?:episode|series|chapter)|no longer free|"
                      r"have to (?:pay|buy)|purchase|refund|expensive|"
                      r"last episode for the day|paywall", re.I)
DELIVERY = re.compile(r"repeat|repeated|out of order|same episode|already heard|"
                      r"glitch|not loading|won'?t play|skipped|duplicate", re.I)
NARRATOR = re.compile(r"narrator|voice actor|new voice|change[sd]? the (?:voice|narrator)|"
                      r"hate (?:her|his) voice", re.I)

def rates(by_ep, lo, hi):
    tot = pw = dl = nr = 0
    for e in range(lo, hi + 1):
        for c in by_ep.get(e, []):
            tot += 1
            if PAYWALL.search(c):  pw += 1
            if DELIVERY.search(c): dl += 1
            if NARRATOR.search(c): nr += 1
    return dict(n=tot, paywall=pw, delivery=dl, narrator=nr)

def classify(blocks, by_ep):
    """Assign a type to every block. ARTIFACT types must NOT be diagnosed as story.

    Order matters: the cheapest, most decisive evidence first.
      1. paywall complaints elevated        -> monetization boundary
      2. magnitude an order beyond the show -> monetization boundary
      3. self-heals AND delivery complaints -> delivery fault
      4. otherwise, ratio decides
    A spike that self-heals but has NO delivery complaints is a genuine break
    that happened to be followed by recovery - do not call it an artifact.
    """
    if not blocks: return
    lo_all, hi_all = min(b["ep_lo"] for b in blocks), max(b["ep_hi"] for b in blocks)
    whole = rates(by_ep, lo_all, hi_all)
    base_pw = whole["paywall"] / whole["n"] if whole["n"] else 0.0
    base_dl = whole["delivery"] / whole["n"] if whole["n"] else 0.0
    for i, b in enumerate(blocks):
        r = b["ratio"]
        rr = rates(by_ep, b["ep_lo"], b["ep_hi"])
        b["comments_n"] = rr["n"]
        b["paywall_rate"]  = round(rr["paywall"] / rr["n"], 3) if rr["n"] else None
        b["delivery_rate"] = round(rr["delivery"] / rr["n"], 3) if rr["n"] else None
        b["narrator_rate"] = round(rr["narrator"] / rr["n"], 3) if rr["n"] else None
        if r is None:
            b["type"] = "unknown"; continue
        others = [x["ratio"] for j, x in enumerate(blocks) if j != i and x["ratio"]]
        nxt  = blocks[i + 1]["ratio"] if i + 1 < len(blocks) else None
        nxt2 = blocks[i + 2]["ratio"] if i + 2 < len(blocks) else None
        pw_hot = (rr["n"] >= 10 and rr["paywall"] >= 5
                  and (rr["paywall"] / rr["n"]) >= max(0.08, 2.5 * max(base_pw, 0.005)))
        dl_hot = (rr["n"] >= 10 and rr["delivery"] >= 5
                  and (rr["delivery"] / rr["n"]) >= max(0.08, 2.5 * max(base_dl, 0.005)))
        if r < 1.3 and not pw_hot:
            b["type"] = "holds"
        elif pw_hot and r >= 1.6:
            b["type"] = (f"ARTIFACT · paywall/free-window "
                         f"({rr['paywall']}/{rr['n']} comments vs {base_pw:.0%} baseline)")
        elif others and r >= 5 * max(others):
            b["type"] = "ARTIFACT · magnitude discontinuity (paywall/free-window?)"
        elif dl_hot and r >= 1.6 and nxt and nxt <= 1.3 and (nxt2 is None or nxt2 <= 1.3):
            b["type"] = (f"ARTIFACT · delivery fault, self-heals "
                         f"({rr['delivery']}/{rr['n']} delivery complaints)")
        elif r >= 1.6:
            extra = " · NOTE narrator complaints elevated" if (
                rr["n"] >= 10 and rr["narrator"] / rr["n"] >= 0.10) else ""
            b["type"] = "CREATIVE · genuine flag" + extra
        else:
            b["type"] = "mild"

# --------------------------------------------------------------------- driver
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", required=True)
    ap.add_argument("--show-id")
    ap.add_argument("--block", type=int, default=0, help="block size; 0 = auto")
    ap.add_argument("--start", type=int, default=51)
    a = ap.parse_args()

    epis = glob.glob(os.path.join(a.pack, "**", "Episodic_Level_*.csv"), recursive=True)
    if not epis: sys.exit("No Episodic_Level_*.csv found under --pack")
    shows = load_episodic(epis[0])
    sid = a.show_id
    if not sid:
        p = glob.glob(os.path.join(a.pack, "**", "show_id.txt"), recursive=True)
        if p: sid = open(p[0]).read().strip()
    if sid not in shows:
        sid = next(k for k in shows if k != TAB_ID)
    SHOW, TAB = shows[sid], shows[TAB_ID]
    lo, hi = a.start, max(SHOW)
    size = a.block or (10 if hi <= 450 else 20)
    print(f"show_id={sid}  episodes {min(SHOW)}-{hi}  block={size}")

    lv, bad = clean_levels(SHOW, lo, hi)
    print(f"\nTRAP 1 — corrupt LDAU rows: {len(bad)}")
    for e, v, p in bad:
        print(f"   ep{e}: LDAU {v:.0f} vs previous {p:.0f}  (+{100*(v/p-1):.0f}%) -> interpolated")

    sm = glob.glob(os.path.join(a.pack, "**", "EPISODIC_SUMMARIES_*.md"), recursive=True)
    eps = load_summaries(sm[0]) if sm else {}
    cdir = glob.glob(os.path.join(a.pack, "**", "inapp-comments"), recursive=True)
    by_ep = load_comments(cdir[0]) if cdir else {}
    print(f"summaries parsed: {len(eps)} | comments: {sum(len(v) for v in by_ep.values())} "
          f"across {len(by_ep)} episodes")

    blocks = block_table(SHOW, TAB, lv, lo, hi, size)
    classify(blocks, by_ep)
    print(f"\n{'block':>12} {'show':>6} {'TAB':>6} {'ratio':>7} {'level':>7} {'lost':>7}  type")
    for b in blocks:
        print(f"{b['ep_lo']:>5}-{b['ep_hi']:<6} {b['show_drop']:>6} {b['tab_drop']:>6} "
              f"{str(b['ratio'])+'x':>7} {str(b['level_pct'])+'%':>7} {b['lost']:>7}  {b['type']}")

    flagged = [b for b in blocks if b["type"].startswith("CREATIVE")]
    print(f"\nCREATIVE flags: {[(b['ep_lo'], b['ep_hi'], b['ratio']) for b in flagged]}")
    print("ARTIFACTS (do NOT diagnose as story):")
    for b in blocks:
        if b["type"].startswith("ARTIFACT"):
            print(f"   ep {b['ep_lo']}-{b['ep_hi']} {b['ratio']}x — {b['type']}")

    for b in flagged[:6]:
        print(f"\n--- comments, ep {b['ep_lo']}-{b['ep_hi']} ---")
        n = 0
        for e in range(b["ep_lo"], b["ep_hi"] + 1):
            for c in by_ep.get(e, [])[:2]:
                print(f"  [{e}] {c[:130]}"); n += 1
                if n >= 8: break
            if n >= 8: break

    json.dump(dict(show_id=sid, block_size=size, corrupt_ldau=bad, blocks=blocks,
                   levels={str(k): v for k, v in lv.items()}),
              open(os.path.join(a.pack, "analysis.json"), "w"), indent=1)
    print(f"\nwrote {os.path.join(a.pack, 'analysis.json')}")
    print("\nNEXT: read the summaries for the hook, each CREATIVE window, and the finale.")
    print("Trace every causal claim by searching the character name across ALL episodes.")

if __name__ == "__main__":
    main()

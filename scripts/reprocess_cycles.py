"""Recompute the per-cycle table of every published run from its saved coefficients.csv with the bin-averaged method
of cycle_stats.py (fixes the over-weighting of the motion-table kicks in the first post-processing).

    python3 scripts/reprocess_cycles.py <ci-results checkout> [run dir glob ...]
Rewrites forces_summary.json (cycles, method note) and keeps the old table as forces_summary_v1.json.
"""
import glob, json, math, os, shutil, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from cycle_stats import cycle_table

root = sys.argv[1]
pats = [p for p in sys.argv[2:] if not p.startswith("--")] or ["phase2b/*", "phase34/*", "phase5/*", "anim/*", "tetests/*", "phase34b/*"]
PER = {0.14: 1 / 0.14, 0.18: 1 / 0.18, 0.06: 1 / 0.06}
for pat in pats:
    for d in sorted(glob.glob(os.path.join(root, pat))):
        fj, fc = os.path.join(d, "forces_summary.json"), os.path.join(d, "coefficients.csv")
        if not (os.path.exists(fj) and os.path.exists(fc)):
            continue
        S = json.load(open(fj))
        if S.get("cycle_method") == "bin-averaged" and "--force" not in sys.argv:
            continue
        fstar = S.get("reference", {}).get("fstar", 0.14)
        T = 1 / fstar
        D = np.genfromtxt(fc, delimiter=",", names=True)
        if D.size < 50:
            continue
        if not os.path.exists(os.path.join(d, "forces_summary_v1.json")):
            shutil.copy(fj, os.path.join(d, "forces_summary_v1.json"))
        old = [c["eta"] for c in json.load(open(os.path.join(d, "forces_summary_v1.json")))["cycles"]]
        S["cycles"] = cycle_table(D["t"], D["CX"], D["CY"], D["CM"], D["CP"], T, S["swept_height"], 2 * math.pi * fstar)
        S["cycles_complete"] = len(S["cycles"])
        S["cycle_method"] = "bin-averaged"
        json.dump(S, open(fj, "w"), indent=1)
        new = [c["eta"] for c in S["cycles"]]
        if old and new:
            print(f"{os.path.relpath(d, root):24s} last cycle eta {old[-1]:7.3f} -> {new[-1]:7.3f}")

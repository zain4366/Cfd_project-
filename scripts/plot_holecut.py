"""Pictures and counts of the overset hole cutting at several moments of the cycle.

    python3 scripts/plot_holecut.py <case dir> <output dir>

Reads, for every written time, the cell centres (C, from postProcess -func writeCellCentres) and the
overset cell types (cellTypes: 0 calculated, 1 interpolated, 2 hole) written by dynamicOversetFvMesh.
"""
import os, re, sys, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import params as P
from foamio import read_internal

case, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)


def times(case):
    t = []
    for d in os.listdir(case):
        try:
            t.append((float(d), d))
        except ValueError:
            pass
    return [d for _, d in sorted(t)]


tdirs = [d for d in times(case) if os.path.exists(os.path.join(case, d, "C"))]
rows, frames = [], []
for d in tdirs:
    ct = os.path.join(case, d, "cellTypes")
    if not os.path.exists(ct):
        rows.append(dict(time=float(d), note="no cellTypes field written")); continue
    types = read_internal(ct, False)
    C = read_internal(os.path.join(case, d, "C"), True)
    if types is None or C is None:
        rows.append(dict(time=float(d), note="uniform field")); continue
    cnt = {k: int((types == v).sum()) for k, v in (("calculated", 0), ("interpolated", 1), ("hole", 2))}
    rows.append(dict(time=float(d), t_over_T=round(float(d) / P.PERIOD, 4), **cnt))
    frames.append((float(d), C, types))

json.dump(rows, open(os.path.join(out, "cell_types.json"), "w"), indent=1)
with open(os.path.join(out, "cell_types.md"), "w") as f:
    f.write("| t/T | calculated | interpolated | hole |\n|---|---|---|---|\n")
    for r in rows:
        if "hole" in r:
            f.write(f"| {r['t_over_T']:.3f} | {r['calculated']} | {r['interpolated']} | {r['hole']} |\n")
        else:
            f.write(f"| {r['time']:.4f} | {r.get('note')} | | |\n")
print(open(os.path.join(out, "cell_types.md")).read())

if frames:
    pick = [frames[int(round(k * (len(frames) - 1) / 4))] for k in range(4)] if len(frames) >= 4 else frames
    colours = {0: ("0.82", 0.4, "calculated"), 1: ("C0", 2.0, "interpolated (donor/acceptor)"), 2: ("C3", 2.0, "hole (inside the foil)")}
    for name, box in (("holecut_overlap", (-2.3, 2.3, -2.6, 2.6)), ("holecut_foil", None)):
        fig, axs = plt.subplots(1, len(pick), figsize=(4.2 * len(pick), 4.6), dpi=150)
        axs = np.atleast_1d(axs)
        for ax, (t, C, ty) in zip(axs, pick):
            h = P.heave(t)
            b = box or (-0.9, 0.9, h - 0.9, h + 0.9)
            sel = (C[:, 0] > b[0]) & (C[:, 0] < b[1]) & (C[:, 1] > b[2]) & (C[:, 1] < b[3])
            for v in (2, 0, 1):                      # holes first, interpolated cells on top
                col, s, lab = colours[v]
                m = sel & (ty == v)
                ax.scatter(C[m, 0], C[m, 1], s=s, c=col, lw=0, label=lab)
            ax.set_xlim(b[0], b[1]); ax.set_ylim(b[2], b[3]); ax.set_aspect("equal")
            ax.set_title(f"t/T = {t / P.PERIOD:.2f}   heave {h:+.2f}c, pitch {P.pitch_deg(t):+.0f}°", fontsize=9)
        axs[0].legend(loc="lower left", fontsize=7, markerscale=4)
        fig.suptitle("Overset cell types while the foil moves through one cycle", fontsize=11)
        fig.tight_layout(); fig.savefig(os.path.join(out, name + ".png")); plt.close(fig)

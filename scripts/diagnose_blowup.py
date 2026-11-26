"""Find where a diverging run first goes wrong: for every written time, the cells with the largest |U| and Courant number.

    python3 scripts/diagnose_blowup.py <case dir> <output .md>
Needs ASCII U, Co and C (cell centres) in each time folder.
"""
import glob, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from foamio import read_internal
import params as P

case, out = sys.argv[1], sys.argv[2]
times = sorted((d for d in glob.glob(os.path.join(case, "[0-9]*")) if os.path.isdir(d) and float(os.path.basename(d)) > 0),
               key=lambda d: float(os.path.basename(d)))
L = ["| step | time | max abs U | where (x, y) | r from pivot | angle | max Co | where (x, y) |", "|---|---|---|---|---|---|---|---|"]
dt = None
for d in times:
    t = float(os.path.basename(d))
    if not all(os.path.exists(os.path.join(d, f)) for f in ("U", "C")):
        continue
    U = read_internal(os.path.join(d, "U"), True); C = read_internal(os.path.join(d, "C"), True)
    Co = read_internal(os.path.join(d, "Co"), False) if os.path.exists(os.path.join(d, "Co")) else None
    if U is None or C is None:
        continue
    yp = P.H0 * math.cos(P.omega() * t)            # pivot = centre of the mesh, moves with the heave
    mag = np.linalg.norm(U, axis=1); i = int(np.argmax(mag))
    r = math.hypot(C[i, 0], C[i, 1] - yp); ang = math.degrees(math.atan2(C[i, 1] - yp, C[i, 0]))
    row = f"| {t / (P.PERIOD / 4000):.0f} | {t:.5f} | {mag[i]:.3g} | ({C[i, 0]:.4f}, {C[i, 1]:.4f}) | {r:.4f} | {ang:+.1f}° |"
    if Co is not None:
        j = int(np.argmax(Co)); row += f" {Co[j]:.3g} | ({C[j, 0]:.4f}, {C[j, 1]:.4f}) |"
    else:
        row += " | |"
    L.append(row)
    top = np.argsort(mag)[-8:][::-1]
    L.append("|  | top cells: " + "; ".join(f"{mag[k]:.2g} at ({C[k, 0]:.3f},{C[k, 1]:.3f})" for k in top) + " | | | | | | |")
open(out, "w").write("\n".join(L) + "\n"); print("\n".join(L))

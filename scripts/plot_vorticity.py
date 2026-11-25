"""Vorticity around the foil at the latest written time (reconstructed case).

    python3 scripts/plot_vorticity.py <case dir> <output png>

Uses O-grid cells inside the O-grid and background cells outside it, so the overlap is not drawn twice.
"""
import os, re, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
sys.path.insert(0, os.path.dirname(__file__))
import params as P
from foamio import read_internal

case, png = sys.argv[1], sys.argv[2]
times = sorted((float(d), d) for d in os.listdir(case) if re.fullmatch(r"[\d.eE+-]+", d) and float(d) > 0)
t, d = times[-1]
C = read_internal(os.path.join(case, d, "C"), True)
W = read_internal(os.path.join(case, d, "vorticity"), True)[:, 2]
opt = lambda f: read_internal(os.path.join(case, d, f), False) if os.path.exists(os.path.join(case, d, f)) else None
Z = opt("zoneID"); ty = opt("cellTypes")
h = P.heave(t)
r = np.hypot(C[:, 0], C[:, 1] - h)
keep = np.ones(len(C), bool) if Z is None else (((Z > 0.5) & (r < P.R_OSET - 0.05)) | ((Z < 0.5) & (r >= P.R_OSET - 0.05)))
if ty is not None:
    keep &= ty != 2
box = (C[:, 0] > -2) & (C[:, 0] < 8) & (np.abs(C[:, 1]) < 3.5)
keep &= box
tri = mtri.Triangulation(C[keep, 0], C[keep, 1])
xm = C[keep, 0][tri.triangles].mean(1); ym = C[keep, 1][tri.triangles].mean(1)
th = np.radians(P.pitch_deg(t))
xl, yl = xm * np.cos(-th) - (ym - h) * np.sin(-th), xm * np.sin(-th) + (ym - h) * np.cos(-th)   # into the foil frame
inside = (xl > -P.XP) & (xl < 1 - P.XP) & (np.abs(yl) < 0.08)
tri.set_mask(inside | (np.max(np.hypot(np.diff(C[keep, 0][tri.triangles], axis=1), np.diff(C[keep, 1][tri.triangles], axis=1)), axis=1) > 0.3))
fig, ax = plt.subplots(figsize=(10, 4.2), dpi=160)
cf = ax.tricontourf(tri, np.clip(W[keep], -10, 10), levels=np.linspace(-10, 10, 41), cmap="RdBu_r", extend="both")
xs = (1 - np.cos(np.linspace(0, np.pi, 101))) / 2
yt = 5 * P.THICK * (0.2969 * np.sqrt(xs) - 0.126 * xs - 0.3516 * xs**2 + 0.2843 * xs**3 - 0.1015 * xs**4)
xb = np.r_[xs, xs[::-1]] - P.XP; yb = np.r_[yt, -yt[::-1]]
ax.fill(xb * np.cos(th) - yb * np.sin(th), h + xb * np.sin(th) + yb * np.cos(th), color="k")
ax.set_aspect("equal"); ax.set_xlim(-2, 8); ax.set_ylim(-3.5, 3.5)
ax.set_title(f"Vorticity ωz c/U at t/T = {t / P.PERIOD:.2f} (red = counter-clockwise)", fontsize=10)
fig.colorbar(cf, ax=ax, shrink=0.8, ticks=[-10, -5, 0, 5, 10]); fig.tight_layout(); fig.savefig(png)

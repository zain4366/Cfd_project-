"""Animate one cycle: vorticity around the moving foil + the force/power history with a moving marker.

    python3 scripts/make_animation.py <reconstructed case dir> <output dir> <coefficients.csv>

Every written time folder needs C (cell centres) and vorticity. Writes frames/, <name>.gif, <name>.mp4 (if ffmpeg
is installed) and four stills (t/T = 0, 0.25, 0.5, 0.75 of the animated cycle).
"""
import os, re, shutil, subprocess, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
sys.path.insert(0, os.path.dirname(__file__))
import params as P
from foamio import read_internal

case, out, coef = sys.argv[1], sys.argv[2], sys.argv[3]
name = f"case{P.CASE}"
os.makedirs(os.path.join(out, "frames"), exist_ok=True)
T = P.PERIOD
times = sorted((float(d), d) for d in os.listdir(case) if re.fullmatch(r"[\d.eE+-]+", d) and float(d) > 0
               and os.path.exists(os.path.join(case, d, "vorticity")) and os.path.exists(os.path.join(case, d, "C")))
times = [td for td in times if td[0] >= times[-1][0] - T * (1 + 1e-6)]        # the last cycle only
D = np.genfromtxt(coef, delimiter=",", names=True)
c0 = times[0][0]
sel = (D["t"] >= c0 - 1e-9) & (D["t"] <= times[-1][0] + 1e-9)
ph_all = (D["t"][sel] - c0) / T
xs = (1 - np.cos(np.linspace(0, np.pi, 101))) / 2
yt = 5 * P.THICK * (0.2969 * np.sqrt(xs) - 0.126 * xs - 0.3516 * xs**2 + 0.2843 * xs**3 - 0.1015 * xs**4)
xb = np.r_[xs, xs[::-1]] - P.XP; yb = np.r_[yt, -yt[::-1]]
X0, X1, Y0, Y1 = -1.6, 6.4, -2.6, 2.6
thick = lambda x: 5 * P.THICK * (0.2969 * np.sqrt(x) - 0.126 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1015 * x**4)
from cycle_stats import phase_bins
kc = int(round(c0 / T)); nb = 400
ph_b = (np.arange(nb) + 0.5) / nb
trace = {key: phase_bins(D["t"], D[key], T, kc, nb) for key in ("CY", "CP")}   # bin-averaged: no motion-table steps
fields = {}
pngs = []
for k, (t, d) in enumerate(times):
    C = read_internal(os.path.join(case, d, "C"), True)
    W = read_internal(os.path.join(case, d, "vorticity"), True)[:, 2]
    keep = (C[:, 0] > X0 - 0.5) & (C[:, 0] < X1 + 0.5) & (C[:, 1] > Y0 - 0.5) & (C[:, 1] < Y1 + 0.5)
    h = P.heave(t); th = np.radians(P.pitch_deg(t))
    fields[f"f{k:03d}"] = np.c_[C[keep, 0], C[keep, 1], W[keep]].astype(np.float32)
    fields[f"t{k:03d}"] = np.float64(t)
    tri = mtri.Triangulation(C[keep, 0], C[keep, 1])
    xm = C[keep, 0][tri.triangles].mean(1); ym = C[keep, 1][tri.triangles].mean(1)
    xl = xm * np.cos(-th) - (ym - h) * np.sin(-th); yl = xm * np.sin(-th) + (ym - h) * np.cos(-th)
    xs_l = np.clip(xl + P.XP, 0, 1)                                    # chordwise position of the centroid
    inside = (xl > -P.XP) & (xl < 1 - P.XP) & (np.abs(yl) < thick(xs_l))   # only triangles inside the real profile
    edge = np.max(np.hypot(np.diff(C[keep, 0][tri.triangles], axis=1), np.diff(C[keep, 1][tri.triangles], axis=1)), axis=1)
    tri.set_mask(inside | (edge > 0.3 + 0.25 * np.hypot(xm, ym - h)))
    fig = plt.figure(figsize=(10, 6.4), dpi=110)
    ax = fig.add_axes([0.06, 0.36, 0.86, 0.58]); cax = fig.add_axes([0.93, 0.40, 0.012, 0.50])
    cf = ax.tricontourf(tri, np.clip(W[keep], -10, 10), levels=np.linspace(-10, 10, 41), cmap="RdBu_r", extend="both")
    ax.fill(xb * np.cos(th) - yb * np.sin(th), h + xb * np.sin(th) + yb * np.cos(th), color="k", zorder=3)
    ax.plot([0], [h], "o", color="w", ms=2.5, zorder=4)
    ax.axhline(P.H0, color="0.5", lw=0.5, ls=":"); ax.axhline(-P.H0, color="0.5", lw=0.5, ls=":")
    ax.set_aspect("equal"); ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1)
    ax.set_xlabel("x / c"); ax.set_ylabel("y / c")
    ax.set_title(f"Kinsey & Dumas Case {P.CASE}: f* = {P.FSTAR}, θ₀ = {P.THETA0:g}°, Re = 1100 (OpenFOAM, rigid moving mesh)    "
                 f"t/T = {(t - c0) / T:.2f}", fontsize=10)
    fig.colorbar(cf, cax=cax, ticks=[-10, -5, 0, 5, 10]); cax.set_title("ω c/U", fontsize=8)
    bx = fig.add_axes([0.06, 0.07, 0.86, 0.2])
    for key, lab, col in (("CY", "C_Y (lift)", "C0"), ("CP", "C_P (power)", "C3")):
        bx.plot(ph_b, trace[key], color=col, lw=1.3, label=lab)
    bx.axvline((t - c0) / T, color="k", lw=1)
    bx.axhline(0, color="0.6", lw=0.6)
    bx.set_xlim(0, 1); bx.set_xlabel("t / T"); bx.grid(alpha=0.3); bx.legend(fontsize=8, loc="upper right", ncol=2)
    p = os.path.join(out, "frames", f"frame_{k:03d}.png"); fig.savefig(p); plt.close(fig); pngs.append(p)
print(len(pngs), "frames")
np.savez_compressed(os.path.join(out, f"{name}_fields_last_cycle.npz"), **fields)   # x, y, ω_z per frame (plot window)
from PIL import Image
ims = [Image.open(p).convert("P", palette=Image.ADAPTIVE, colors=255) for p in pngs[:-1]]     # last frame = first of next cycle
ims[0].save(os.path.join(out, f"{name}_vorticity.gif"), save_all=True, append_images=ims[1:], duration=60, loop=0, optimize=True)
if shutil.which("ffmpeg"):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "16", "-i", os.path.join(out, "frames", "frame_%03d.png"),
                    "-frames:v", str(len(pngs) - 1), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "veryfast", os.path.join(out, f"{name}_vorticity.mp4")], check=False)
n = len(pngs) - 1
for q in (0, 0.25, 0.5, 0.75):
    shutil.copy(pngs[int(round(q * n))], os.path.join(out, f"{name}_still_tT{int(q * 100):02d}.png"))
print("done")

"""2x2 LinkedIn video: Cases I, II, III side by side at the same phase t/T (quadrants 1-3), efficiency bars (quadrant 4).
    python3 make_grid_video.py <anim root> <out dir> [loops]"""
import math, os, sys, subprocess
from multiprocessing import Pool
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri

ROOT, OUT = sys.argv[1], sys.argv[2]
LOOPS = int(sys.argv[3]) if len(sys.argv) > 3 else 4
FR = os.path.join(OUT, "frames"); os.makedirs(FR, exist_ok=True)
sys.path.insert(0, "/home/claude/cfd_project-/scripts")
from cycle_stats import phase_bins

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.linewidth": 0.8})
CASES = {"I": dict(f=0.14, th=76.33, eta=33.67, kd=33.7, col="#1f5fa8", tag="vortex in step with the heave"),
         "II": dict(f=0.18, th=60.0, eta=10.90, kd=11.4, col="#e07a1f", tag="attached flow, lift lags the heave"),
         "III": dict(f=0.06, th=60.0, eta=12.38, kd=12.3, col="#2e7d4f", tag="vortex shed early, slow heave")}
XP, THICK = 1 / 3, 0.15
xs = (1 - np.cos(np.linspace(0, np.pi, 121))) / 2
yt = 5 * THICK * (0.2969 * np.sqrt(xs) - 0.126 * xs - 0.3516 * xs**2 + 0.2843 * xs**3 - 0.1015 * xs**4)
XB, YB = np.r_[xs, xs[::-1]] - XP, np.r_[yt, -yt[::-1]]
X0, X1, Y0, Y1 = -1.4, 6.5, -2.0, 2.0
LEV = np.linspace(-6, 6, 61)
# quadrant origins (figure fractions): top-left, top-right, bottom-left; bottom-right = bars
Q = {"I": (0.0, 0.47), "II": (0.5, 0.47), "III": (0.0, 0.0)}
QW, QH = 0.5, 0.47


def load(case):
    d = np.load(os.path.join(ROOT, f"case{case}", "animation", f"case{case}_fields_last_cycle.npz"))
    n = len([k for k in d.files if k.startswith("f")]) - 1
    frames = [(float(d[f"t{k:03d}"]), d[f"f{k:03d}"]) for k in range(n)]
    D = np.genfromtxt(os.path.join(ROOT, f"case{case}", "coefficients.csv"), delimiter=",", names=True)
    T = 1 / CASES[case]["f"]
    kc = int(round(frames[0][0] / T))
    return frames, phase_bins(D["t"], D["CP"], T, kc, 400), T


def panel(fig, case, k):
    frames, cp, T = DATA[case]
    t, F = frames[k]
    P = CASES[case]; ox, oy = Q[case]
    om = 2 * math.pi * P["f"]
    h = math.cos(om * t); th = math.radians(P["th"] * math.sin(om * t))
    x, y, w = F[:, 0].astype(float), F[:, 1].astype(float), F[:, 2].astype(float)
    tri = mtri.Triangulation(x, y)
    xm = x[tri.triangles].mean(1); ym = y[tri.triangles].mean(1)
    edge = np.max(np.hypot(np.diff(x[tri.triangles], axis=1), np.diff(y[tri.triangles], axis=1)), axis=1)
    tri.set_mask(edge > 0.3 + 0.25 * np.hypot(xm, ym - h))
    fig.text(ox + 0.02, oy + QH - 0.035, f"Case {case}", fontsize=17, fontweight="bold", color=P["col"])
    fig.text(ox + 0.02, oy + QH - 0.068, f"f* = {P['f']:.2f},  θ₀ = {P['th']:g}°  ·  {P['tag']}", fontsize=13, color="0.25")
    fig.text(ox + QW - 0.02, oy + QH - 0.035, f"η = {P['eta']:.1f} %", fontsize=17, fontweight="bold", color=P["col"], ha="right")
    fig.text(ox + QW - 0.112, oy + QH - 0.035, f"paper {P['kd']:.1f} %  |", fontsize=12.5, color="0.4", ha="right")
    ax = fig.add_axes([ox + 0.02, oy + 0.012, QW - 0.04, QH - 0.093]); ax.set_anchor("C")
    cf = ax.tricontourf(tri, np.clip(w, -6, 6), levels=LEV, cmap="RdBu_r", extend="both")
    ax.fill(XB * math.cos(th) - YB * math.sin(th), h + XB * math.sin(th) + YB * math.cos(th), color="#d9d9d9", ec="0.15", lw=1.0, zorder=3)
    ax.plot([0], [h], "o", color="0.15", ms=3, zorder=4)
    for yy in (1, -1):
        ax.axhline(yy, color="0.6", lw=0.5, ls=":")
    ax.annotate("", xy=(-0.85, 1.75), xytext=(-1.3, 1.75), arrowprops=dict(arrowstyle="->", color="0.25", lw=1.2))
    ax.text(-1.3, 1.85, "U", fontsize=10, color="0.25")
    ax.set_aspect("equal"); ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1)
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color(P["col"]); sp.set_linewidth(1.5)
    return cf


def render(job):
    k, path = job
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
    fig.text(0.5, 0.965, "One foil, three motions: energy harvesting by an oscillating NACA 0015 foil (OpenFOAM, Re = 1100, 2D laminar)",
             ha="center", fontsize=19, fontweight="bold")
    fig.text(0.5, 0.935, f"all three cases shown at the same point of their cycle:  t / T = {k / 100:4.2f}", ha="center", fontsize=13,
             family="DejaVu Sans Mono", color="0.3")
    for c in CASES:
        cf = panel(fig, c, k)
    # quadrant 4: efficiency bars, power timing of the three cases, colour bar
    ox, oy = 0.5, 0.0
    fig.text(ox + 0.02, oy + QH - 0.035, "Efficiency and power timing", fontsize=17, fontweight="bold")
    ax = fig.add_axes([ox + 0.045, oy + 0.15, 0.19, 0.24])
    cs = list(CASES); xx = np.arange(3)
    ax.bar(xx - 0.2, [CASES[c]["eta"] for c in cs], 0.38, color=[CASES[c]["col"] for c in cs], label="OpenFOAM")
    ax.bar(xx + 0.2, [CASES[c]["kd"] for c in cs], 0.38, color="0.72", label="Kinsey & Dumas 2008")
    for i, c in enumerate(cs):
        ax.text(i - 0.2, CASES[c]["eta"] + 0.8, f"{CASES[c]['eta']:.1f}", ha="center", fontsize=11, color=CASES[c]["col"], fontweight="bold")
        ax.text(i + 0.2, CASES[c]["kd"] + 0.8, f"{CASES[c]['kd']:.1f}", ha="center", fontsize=11, color="0.4")
    ax.set_xticks(xx, [f"Case {c}" for c in cs], fontsize=12)
    ax.set_ylabel("efficiency η [%]", fontsize=11); ax.set_ylim(0, 42); ax.tick_params(labelsize=10)
    ax.legend(fontsize=10.5, frameon=False, loc="upper right", handles=[plt.Rectangle((0, 0), 1, 1, color="0.35"), plt.Rectangle((0, 0), 1, 1, color="0.72")],
              labels=["OpenFOAM (colour)", "Kinsey & Dumas 2008"])
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    px = fig.add_axes([ox + 0.285, oy + 0.15, 0.2, 0.24])
    pb = (np.arange(400) + 0.5) / 400; ph = k / 100
    for c in cs:
        cp = DATA[c][1]
        px.plot(pb, cp, color=CASES[c]["col"], lw=1.8, label=f"Case {c}")
        px.plot([ph], [cp[min(int(ph * 400), 399)]], "o", color=CASES[c]["col"], ms=6)
    px.axhline(0, color="0.5", lw=0.7); px.axvline(ph, color="0.1", lw=1.0)
    px.set_xlim(0, 1); px.set_ylim(-0.9, 1.7); px.set_xlabel("t / T", fontsize=11); px.set_ylabel("power coefficient C_P", fontsize=11)
    px.tick_params(labelsize=10); px.grid(alpha=0.3); px.legend(fontsize=10, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.13))
    for sp in ("top", "right"):
        px.spines[sp].set_visible(False)
    cax = fig.add_axes([ox + 0.045, oy + 0.06, 0.2, 0.013])
    cb = fig.colorbar(cf, cax=cax, orientation="horizontal", ticks=[-6, -3, 0, 3, 6]); cb.ax.tick_params(labelsize=10)
    fig.text(ox + 0.255, oy + 0.066, "vorticity ωc/U (red = counter-clockwise)", fontsize=11, color="0.3", va="center")
    fig.text(ox + 0.045, oy + 0.018, "NACA 0015, heave ±1 chord, pivot c/3  ·  rigid moving O-grid, pimpleFoam  ·  65k cells, far field 80c",
             fontsize=10, color="0.45")
    fig.add_artist(plt.Line2D([0.5, 0.5], [0.02, 0.92], color="0.85", lw=1))
    fig.add_artist(plt.Line2D([0.02, 0.98], [0.47, 0.47], color="0.85", lw=1))
    fig.savefig(path); plt.close(fig)
    return path


def init(d):
    global DATA
    DATA = d


if __name__ == "__main__":
    data = {c: load(c) for c in CASES}
    n = min(len(data[c][0]) for c in CASES)
    jobs = [(k, os.path.join(FR, f"g_{k:03d}.png")) for k in range(n)]
    with Pool(2, initializer=init, initargs=(data,)) as pool:
        paths = pool.map(render, jobs, chunksize=4)
    with open(os.path.join(OUT, "list_grid.txt"), "w") as f:
        for _ in range(LOOPS):
            for p in paths:
                f.write(f"file '{p}'\nduration 0.04\n")
    mp4 = os.path.join(OUT, "kinsey_dumas_three_cases_grid.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(OUT, "list_grid.txt"),
                    "-vf", "fps=25,format=yuv420p", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-movflags", "+faststart", mp4], check=True)
    print(mp4, n * LOOPS / 25, "s")

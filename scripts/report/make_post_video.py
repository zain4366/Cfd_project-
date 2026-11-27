"""LinkedIn-style video: vorticity around the oscillating foil for Kinsey & Dumas Cases I, II, III, with the lift and
power of the cycle and a closing efficiency chart.   python3 make_post_video.py <anim root> <out dir>
<anim root>/case{I,II,III}/animation/case*_fields_last_cycle.npz and <anim root>/case*/coefficients.csv (animations.yml)."""
import importlib, math, os, sys, subprocess
from multiprocessing import Pool
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from PIL import Image

ROOT, OUT = sys.argv[1], sys.argv[2]
FR = os.path.join(OUT, "frames"); os.makedirs(FR, exist_ok=True)
sys.path.insert(0, "/home/claude/cfd_project-/scripts")
from cycle_stats import phase_bins

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13, "axes.linewidth": 0.8})
CASES = {"I": dict(f=0.14, th=76.33, eta=33.67, kd=33.7, tag="high-efficiency case",
                   note="A leading-edge vortex grows on the foil\nduring each stroke and leaves at the\nstroke reversal: lift stays in step with\nthe heave almost all cycle."),
         "II": dict(f=0.18, th=60.0, eta=10.90, kd=11.4, tag="faster, smaller pitch",
                    note="Effective angle only ~12°: the flow stays\nattached, no leading-edge vortex. Lift lags\nthe heave by ~55°, so near each reversal\nthe foil gives energy back."),
         "III": dict(f=0.06, th=60.0, eta=12.38, kd=12.3, tag="slow, large angle",
                     note="Effective angle ~39°: a big vortex separates\nby mid-stroke and is shed early. Large\nforces, but the foil heaves slowly,\nso little power is extracted.")}
XP, THICK = 1 / 3, 0.15
xs = (1 - np.cos(np.linspace(0, np.pi, 121))) / 2
yt = 5 * THICK * (0.2969 * np.sqrt(xs) - 0.126 * xs - 0.3516 * xs**2 + 0.2843 * xs**3 - 0.1015 * xs**4)
XB, YB = np.r_[xs, xs[::-1]] - XP, np.r_[yt, -yt[::-1]]
thick = lambda x: 5 * THICK * (0.2969 * np.sqrt(x) - 0.126 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1015 * x**4)
X0, X1, Y0, Y1 = -1.6, 6.4, -2.25, 2.25
LEV = np.linspace(-6, 6, 61)
W, H, DPI = 19.2, 10.8, 100
REPEAT = 2                                  # cycles shown per case


def load(case):
    d = np.load(os.path.join(ROOT, f"case{case}", "animation", f"case{case}_fields_last_cycle.npz"))
    n = len([k for k in d.files if k.startswith("f")]) - 1          # the last frame repeats the first of the next cycle
    frames = [(float(d[f"t{k:03d}"]), d[f"f{k:03d}"]) for k in range(n)]
    D = np.genfromtxt(os.path.join(ROOT, f"case{case}", "coefficients.csv"), delimiter=",", names=True)
    T = 1 / CASES[case]["f"]
    kc = int(round(frames[0][0] / T))
    tr = {k: phase_bins(D["t"], D[k], T, kc, 400) for k in ("CY", "CP")}
    return frames, tr, T


def render(job):
    case, k, rep, path = job
    frames, tr, T = DATA[case]
    t, F = frames[k]
    P = CASES[case]
    om = 2 * math.pi * P["f"]
    h = math.cos(om * t); th = math.radians(P["th"] * math.sin(om * t))
    x, y, w = F[:, 0].astype(float), F[:, 1].astype(float), F[:, 2].astype(float)
    tri = mtri.Triangulation(x, y)
    xm = x[tri.triangles].mean(1); ym = y[tri.triangles].mean(1)
    xl = xm * math.cos(-th) - (ym - h) * math.sin(-th); yl = xm * math.sin(-th) + (ym - h) * math.cos(-th)
    inside = (xl > -XP) & (xl < 1 - XP) & (np.abs(yl) < thick(np.clip(xl + XP, 0, 1)))
    edge = np.max(np.hypot(np.diff(x[tri.triangles], axis=1), np.diff(y[tri.triangles], axis=1)), axis=1)
    tri.set_mask(edge > 0.3 + 0.25 * np.hypot(xm, ym - h))      # the foil is drawn on top of its own cells

    fig = plt.figure(figsize=(W, H), dpi=DPI)
    fig.text(0.035, 0.955, "Oscillating foil extracting energy from a stream (Kinsey & Dumas 2008 cases), Re = 1100, 2D laminar, OpenFOAM pimpleFoam",
             fontsize=17, fontweight="bold")
    ph = (t - frames[0][0]) / T
    fig.text(0.035, 0.915, f"Case {case}  ({P['tag']})    f* = fc/U = {P['f']:.2f}    θ₀ = {P['th']:g}°    "
             f"t U / c = {t - frames[0][0] + rep * T:6.2f}    t / T = {ph:4.2f}", fontsize=14, family="DejaVu Sans Mono")
    ax = fig.add_axes([0.04, 0.33, 0.62, 0.565]); ax.set_anchor("W")
    cf = ax.tricontourf(tri, np.clip(w, -6, 6), levels=LEV, cmap="RdBu_r", extend="both")
    ax.fill(XB * math.cos(th) - YB * math.sin(th), h + XB * math.sin(th) + YB * math.cos(th), color="#d9d9d9", ec="0.15", lw=1.2, zorder=3)
    ax.plot([0], [h], "o", color="0.15", ms=4, zorder=4)
    ax.plot([-1.25, -1.25], [-1, 1], color="0.35", lw=1.0, zorder=2)                        # heave range marker
    ax.annotate("", xy=(-0.95, 1.9), xytext=(-1.45, 1.9), arrowprops=dict(arrowstyle="->", color="0.2", lw=1.4))
    ax.text(-1.45, 2.0, "U", fontsize=12, color="0.2")
    for yy in (1, -1):
        ax.axhline(yy, color="0.6", lw=0.6, ls=":")
    ax.set_aspect("equal"); ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1)
    ax.set_xlabel("x / c", fontsize=12); ax.set_ylabel("y / c", fontsize=12)
    fig.canvas.draw(); bb = ax.get_position()
    cax = fig.add_axes([bb.x1 + 0.008, bb.y0 + 0.03, 0.01, bb.height - 0.06])
    cb = fig.colorbar(cf, cax=cax, ticks=[-6, -4, -2, 0, 2, 4, 6]); cb.set_label("Vorticity  ω c / U  [-]", fontsize=12)
    bx = fig.add_axes([0.04, 0.075, 0.92, 0.19])
    pb = (np.arange(400) + 0.5) / 400
    bx.plot(pb, tr["CY"], color="#1f5fa8", lw=2, label="Lift coefficient  C_Y")
    bx.plot(pb, tr["CP"], color="#c0392b", lw=2, label="Power coefficient  C_P")
    bx.fill_between(pb, 0, tr["CP"], where=tr["CP"] > 0, color="#c0392b", alpha=0.12, lw=0)
    bx.fill_between(pb, 0, tr["CP"], where=tr["CP"] < 0, color="0.3", alpha=0.18, lw=0)
    i = min(int(ph * 400), 399)
    bx.axvline(ph, color="0.1", lw=1.2)
    bx.plot([ph], [tr["CY"][i]], "o", color="#1f5fa8", ms=8); bx.plot([ph], [tr["CP"][i]], "o", color="#c0392b", ms=8)
    bx.axhline(0, color="0.5", lw=0.7)
    bx.set_xlim(0, 1); bx.set_ylim(-2.4, 2.4); bx.set_xlabel("t / T  (one flapping cycle)", fontsize=12)
    bx.set_ylabel("coefficient [-]", fontsize=12); bx.grid(alpha=0.3)
    bx.legend(loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=12, ncol=2, frameon=False)
    bx.text(1.0, 1.04, "red area: the flow does work on the foil    grey area: the foil gives energy back", transform=bx.transAxes,
            ha="right", fontsize=11.5, color="0.35")
    tx = fig.add_axes([0.745, 0.33, 0.235, 0.565]); tx.axis("off")
    tx.text(0, 0.97, "Power-extraction efficiency η", fontsize=16, fontweight="bold", va="top")
    tx.text(0, 0.84, f"OpenFOAM (65k cells)   {P['eta']:4.1f} %", fontsize=15, color="#1f5fa8", family="DejaVu Sans Mono", va="top")
    tx.text(0, 0.76, f"Kinsey & Dumas 2008    {P['kd']:4.1f} %", fontsize=15, color="0.25", family="DejaVu Sans Mono", va="top")
    tx.text(0, 0.60, "What you see", fontsize=16, fontweight="bold", va="top")
    tx.text(0, 0.52, P["note"], fontsize=13.5, color="0.2", va="top", linespacing=1.5)
    tx.text(0, 0.10, "NACA 0015, heave ±1 chord, pivot c/3\nred = counter-clockwise vorticity", fontsize=12, color="0.4", va="top", linespacing=1.5)
    fig.savefig(path); plt.close(fig)
    return path


def end_card(path):
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    fig.text(0.5, 0.88, "Same foil, same Reynolds number: the motion decides the efficiency", ha="center", fontsize=26, fontweight="bold")
    ax = fig.add_axes([0.12, 0.2, 0.5, 0.58])
    cs = ["I", "II", "III"]; xx = np.arange(3)
    ax.bar(xx - 0.19, [CASES[c]["eta"] for c in cs], 0.36, color="#1f5fa8", label="OpenFOAM (this work)")
    ax.bar(xx + 0.19, [CASES[c]["kd"] for c in cs], 0.36, color="0.65", label="Kinsey & Dumas 2008")
    for i, c in enumerate(cs):
        ax.text(i - 0.19, CASES[c]["eta"] + 0.6, f"{CASES[c]['eta']:.1f}", ha="center", fontsize=15, color="#1f5fa8")
        ax.text(i + 0.19, CASES[c]["kd"] + 0.6, f"{CASES[c]['kd']:.1f}", ha="center", fontsize=15, color="0.3")
    ax.set_xticks(xx, [f"Case {c}\nf* {CASES[c]['f']:.2f}, θ₀ {CASES[c]['th']:g}°" for c in cs], fontsize=14)
    ax.set_ylabel("efficiency η  [%]", fontsize=15); ax.set_ylim(0, 40); ax.legend(fontsize=14, frameon=False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    tx = fig.add_axes([0.66, 0.2, 0.31, 0.58]); tx.axis("off")
    lines = [("Case I", "a leading-edge vortex forms each stroke and\nleaves at reversal, in step with the heave: 33.7 %"),
             ("Case II", "flow stays attached, lift lags the heave,\npitching costs power: 10.9 %"),
             ("Case III", "vortex separates by mid-stroke,\nthe foil heaves too slowly: 12.4 %"),
             ("Verification", "3 meshes, 3 time steps, 5 domain sizes;\nfar field matters most: η = 33.0 + 34/R")]
    for k, (a, b) in enumerate(lines):
        tx.text(0, 0.95 - k * 0.26, a, fontsize=16, fontweight="bold")
        tx.text(0, 0.91 - k * 0.26, b, fontsize=13.5, va="top", color="0.25")
    fig.text(0.5, 0.06, "NACA 0015, heave amplitude = chord, pivot at c/3, Re = 1100  ·  rigid moving O-grid, 2D laminar pimpleFoam",
             ha="center", fontsize=13, color="0.35")
    fig.savefig(path); plt.close(fig)


def blend(a, b, n, start):
    A, B = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    out = []
    for j in range(1, n + 1):
        p = os.path.join(FR, f"x_{start}_{j:02d}.png"); Image.blend(A, B, j / (n + 1)).save(p); out.append(p)
    return out


def init(d):
    global DATA
    DATA = d


if __name__ == "__main__":
    data = {c: load(c) for c in CASES}
    jobs = []
    for c in CASES:
        n = len(data[c][0])
        for rep in range(REPEAT):
            for k in range(n):
                jobs.append((c, k, rep, os.path.join(FR, f"c{c}_{rep}_{k:03d}.png")))
    with Pool(2, initializer=init, initargs=(data,)) as pool:
        paths = pool.map(render, jobs, chunksize=4)
    end = os.path.join(FR, "end.png"); end_card(end)
    seq, by = [], {}
    for j, p in zip(jobs, paths):
        by.setdefault(j[0], []).append(p)
    order = list(CASES)
    for i, c in enumerate(order):
        seq += by[c]
        nxt = by[order[i + 1]][0] if i + 1 < len(order) else end
        seq += blend(by[c][-1], nxt, 12, c)
    seq += [end] * 100
    with open(os.path.join(OUT, "list.txt"), "w") as f:
        for p in seq:
            f.write(f"file '{p}'\nduration 0.04\n")
    mp4 = os.path.join(OUT, "kinsey_dumas_oscillating_foil.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(OUT, "list.txt"),
                    "-vf", "fps=25,format=yuv420p", "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-movflags", "+faststart", mp4], check=True)
    print(mp4, len(seq), "frames,", len(seq) / 25, "s")

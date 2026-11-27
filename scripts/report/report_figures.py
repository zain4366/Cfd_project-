"""Report figures (300 dpi) from the published runs.  python3 report_figures.py <ci-results checkout> <out dir>"""
import json, os, sys, gzip, re
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
REPO = "/home/claude/cfd_project-"
REF = json.load(open(f"{REPO}/reference/kinsey_dumas_2008_cases.json"))
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9,
                     "legend.fontsize": 8, "savefig.dpi": 300, "savefig.bbox": "tight", "axes.grid": True, "grid.alpha": 0.3,
                     "axes.spines.top": False, "axes.spines.right": False})
BLUE, ORANGE, GREY, RED, GREEN = "#1f5fa8", "#e07a1f", "#6b6b6b", "#b8322a", "#2e7d4f"
CASES = {"I": (0.14, 76.33), "II": (0.18, 60.0), "III": (0.06, 60.0)}
XP, THICK = 1 / 3, 0.15
xs = (1 - np.cos(np.linspace(0, np.pi, 101))) / 2
yt = 5 * THICK * (0.2969 * np.sqrt(xs) - 0.126 * xs - 0.3516 * xs**2 + 0.2843 * xs**3 - 0.1015 * xs**4)
XB, YB = np.r_[xs, xs[::-1]] - XP, np.r_[yt, -yt[::-1]]


def run(path):
    d = os.path.join(SRC, path)
    fs = json.load(open(os.path.join(d, "forces_summary.json")))
    D = np.genfromtxt(os.path.join(d, "coefficients.csv"), delimiter=",", names=True)
    return fs, D


sys.path.insert(0, "/home/claude/cfd_project-/scripts")
from cycle_stats import phase_bins


def phase_avg(D, T, first, last):
    ph = (np.arange(200) + 0.5) / 200
    return ph, {k: np.mean([phase_bins(D["t"], D[k], T, c) for c in range(first, last)], axis=0) for k in ("CX", "CY", "CM", "CP")}


def save(fig, name):
    fig.savefig(os.path.join(OUT, name)); plt.close(fig); print(name)


# ---- 1 kinematics
f, th0 = CASES["I"]; T = 1 / f; w = 2 * np.pi * f
fig, (a, b) = plt.subplots(2, 1, figsize=(7.0, 5.6), gridspec_kw={"height_ratios": [1, 1.1]})
tt = np.linspace(0, 1, 400)
a.plot(tt, np.cos(2 * np.pi * tt), color=BLUE, label="heave h/c")
a2 = a.twinx(); a2.plot(tt, th0 * np.sin(2 * np.pi * tt), color=ORANGE, label="pitch θ (deg)")
a.set_xlabel("t / T"); a.set_ylabel("h / c", color=BLUE); a2.set_ylabel("θ (deg)", color=ORANGE); a2.grid(False)
a2.spines["right"].set_visible(True)
a.set_title("(a) Prescribed motion, Case I")
for k in range(12):
    t = k / 12 * T; h = np.cos(w * t); th = np.radians(th0 * np.sin(w * t))
    x = 2.2 * k / 12 * 4.0
    b.fill(x + XB * np.cos(th) - YB * np.sin(th), h + XB * np.sin(th) + YB * np.cos(th), color=BLUE if k < 6 else ORANGE, alpha=0.85)
    b.plot(x, h, "k.", ms=2)
b.axhline(1, color=GREY, lw=0.6, ls=":"); b.axhline(-1, color=GREY, lw=0.6, ls=":")
b.annotate("", xy=(-1.2, 1.0), xytext=(-1.2, -1.0), arrowprops=dict(arrowstyle="<->", lw=0.8))
b.text(-1.3, 0, "2H₀", ha="right", va="center")
b.set_aspect("equal"); b.set_xlim(-2.4, 9.0); b.set_ylim(-1.8, 1.8); b.set_xlabel("x / c (positions spread along x for clarity)"); b.set_ylabel("y / c")
b.set_title("(b) Foil every T/12: downstroke (blue), upstroke (orange)")
fig.tight_layout(); save(fig, "fig01_kinematics.png")

# ---- 2 method cost
fig, ax = plt.subplots(figsize=(6.4, 2.6))
labels = ["Overset, inverseDistance\n(Courant ≤ 1)", "Overset, trackingInverseDistance\n(Courant ≤ 1)", "Rigid moving mesh\n(T/2000, medium, 20c)"]
hours = [6.86 * 13546 / 3600, 10.61 * 34904 / 3600, 3105 / 10 / 3600]
bars = ax.barh(labels, hours, color=[GREY, GREY, BLUE])
ax.set_xscale("log"); ax.set_xlabel("wall-clock hours per flapping cycle on a 4-core runner (log scale)")
for bb, h in zip(bars, hours):
    ax.text(h * 1.15, bb.get_y() + bb.get_height() / 2, f"{h:.1f} h" if h > 1 else f"{h * 60:.1f} min", va="center")
ax.set_xlim(0.03, 600); ax.grid(axis="y", visible=False); ax.invert_yaxis()
fig.tight_layout(); save(fig, "fig02_method_cost.png")

# ---- 3 cycle convergence
fig, ax = plt.subplots(figsize=(6.4, 3.0))
for p, lab, c, m in (("phase34/base", "medium, 20c", GREY, "s"), ("phase34/R80", "medium, 80c", ORANGE, "^"),
                     ("phase5/caseI_medium", "medium, 80c, limiter", BLUE, "o"), ("phase5/caseI_fine", "fine, 80c, limiter", "k", "D")):
    fs, _ = run(p)
    ax.plot([c_["cycle"] for c_ in fs["cycles"]], [c_["eta"] for c_ in fs["cycles"]], marker=m, ms=4, color=c, lw=1, label=lab)
ax.axhline(33.7, color="k", ls="--", lw=0.8); ax.text(14.2, 33.7, "K&D 33.7 %", va="center", fontsize=8)
ax.set_xlabel("cycle"); ax.set_ylabel("η per cycle (%)"); ax.set_ylim(32.5, 44); ax.legend(ncol=2); ax.set_xlim(0.5, 16.5)
ax.set_title("Start-up transient: η settles after 4 to 6 cycles; larger domains settle more slowly")
fig.tight_layout(); save(fig, "fig03_cycle_convergence.png")

# ---- 4 time step
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.8))
for p, lab, c, ls in (("phase34/base", "T/2000", BLUE, "-"), ("phase34/dt4000", "T/4000", ORANGE, "--"), ("phase34/dt8000", "T/8000", "k", ":")):
    fs, D = run(p); ph, A = phase_avg(D, T, 4, fs["cycles_complete"])
    axs[0].plot(ph, A["CY"], color=c, ls=ls, label=lab); axs[1].plot(ph, A["CP"], color=c, ls=ls, label=lab)
axs[0].set_ylabel("C_Y"); axs[1].set_ylabel("C_P")
for a_ in axs: a_.set_xlabel("t / T")
axs[0].legend(); axs[0].set_title("(a) lift"); axs[1].set_title("(b) power")
fig.tight_layout(); save(fig, "fig04_time_step.png")

# ---- 5 domain fit
dom = []
for R, p in ((12, "phase34/R12"), (20, "phase34/base"), (40, "phase34/R40"), (60, "phase34/R60"), (80, "phase34/R80")):
    fs, _ = run(p); dom.append((R, fs["cycles"][-1]["eta"]))
Rs = np.array([d[0] for d in dom], float); es = np.array([d[1] for d in dom])
k, e0 = np.polyfit(1 / Rs[Rs >= 20], es[Rs >= 20], 1)
json.dump(dict(eta_inf=e0, slope=k, points=dom), open(os.path.join(OUT, "domain_fit.json"), "w"), indent=1)
fig, ax = plt.subplots(figsize=(6.0, 3.2))
x = np.linspace(0, 0.09, 50)
ax.plot(x, e0 + k * x, color=BLUE, lw=1, label=f"fit (R ≥ 20c): η = {e0:.2f} + {k:.1f}/R")
ax.plot(1 / Rs, es, "o", color=BLUE, ms=6, label="OpenFOAM, medium mesh, cycle 10")
ax.plot(0, e0, "o", mfc="white", mec=BLUE, ms=8, mew=1.5)
ax.annotate(f"infinite domain\n{e0:.2f} %", (0, e0), xytext=(0.006, e0 - 0.9), fontsize=8, arrowprops=dict(arrowstyle="-", lw=0.6))
for R, e in dom:
    ax.annotate(f"{R}c", (1 / R, e), xytext=(0, -13), textcoords="offset points", ha="center", fontsize=8)
ax.axhline(33.7, color="k", ls="--", lw=0.8, label="Kinsey & Dumas 33.7 %")
ax.axhline(32.2, color=GREY, ls=":", lw=1, label="WaterLily (FYP) 32.2 %")
ax.set_xlabel("1 / R   (R = far-field radius in chords)"); ax.set_ylabel("η (%)"); ax.set_xlim(-0.003, 0.09); ax.legend(loc="lower right")
fig.tight_layout(); save(fig, "fig05_domain_fit.png")

# ---- 6 mesh study
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9))
pts = []
for p, lab, c in (("phase34/coarse_l", "coarse", GREY), ("phase34/base_l", "medium", BLUE), ("phase34/fine_l", "fine", "k")):
    fs, D = run(p); mi = json.load(open(os.path.join(SRC, p, "mesh_info.json")))
    use = [c_["eta"] for c_ in fs["cycles"] if c_["cycle"] > 4]; pts.append((mi["cells"], np.mean(use), lab))
    ph, A = phase_avg(D, T, 4, fs["cycles_complete"]); axs[1].plot(ph, A["CM"], color=c, lw=1.1, label=lab)
axs[0].plot([1 / np.sqrt(n) for n, _, _ in pts], [e for _, e, _ in pts], "o-", color=BLUE)
for n, e, lab in pts:
    right = lab != "coarse"
    axs[0].annotate(f"{lab}, {n:,} cells:\n{e:.2f} %", (1 / np.sqrt(n), e), xytext=(8 if right else -8, 0), textcoords="offset points",
                    fontsize=7.5, ha="left" if right else "right", va="center")
axs[0].set_xlabel("1 / √N  (N = cells)"); axs[0].set_ylabel("η (%), far field 20c"); axs[0].set_xlim(0, 0.0105); axs[0].set_ylim(34.1, 35.3)
axs[0].set_title("(a) efficiency against mesh size"); axs[1].set_title("(b) pivot moment, averaged cycle")
axs[1].set_xlabel("t / T"); axs[1].set_ylabel("C_M"); axs[1].legend()
fig.tight_layout(); save(fig, "fig06_mesh_study.png")

# ---- 7 fine-mesh divergence: Courant history
fig, ax = plt.subplots(figsize=(6.0, 2.8))
for p, lab, c in (("phase34/fine", "fine, no limiter", RED), ("phase34/fine_l", "fine, limited corrected 0.33", BLUE), ("phase34/base", "medium, no limiter", GREY)):
    co = [float(l.split()[-1]) for l in gzip.open(os.path.join(SRC, p, "log.solver.gz"), "rt") if l.startswith("Courant")][2:]
    co = co[::1][:160]
    ax.semilogy(range(1, len(co) + 1), co, color=c, lw=1.2, label=lab)
ax.set_xlabel("time step"); ax.set_ylabel("maximum Courant number"); ax.legend(); ax.set_ylim(1, 1e6)
ax.set_title("Fine mesh at T/2000: without the limiter the maximum Courant number grows without bound\nfrom the first steps (the solver stops at step 77); with it, it settles like the medium mesh")
fig.tight_layout(); save(fig, "fig07_fine_divergence.png")

# ---- 8 cases efficiency
P5 = {}
for c in CASES:
    for lev in ("medium", "fine"):
        fs, D = run(f"phase5/case{c}_{lev}")
        sk = 8 if c in ("I", "II") else 4
        P5[(c, lev)] = (fs, D, sk, np.mean([c_["eta"] for c_ in fs["cycles"] if c_["cycle"] > sk]))
fig, ax = plt.subplots(figsize=(6.4, 3.0))
for i, c in enumerate(CASES):
    r = REF[c]
    ax.plot([i - 0.32, i + 0.32], [r["eta_percent"]] * 2, color="k", lw=2, label="Kinsey & Dumas (2008)" if i == 0 else None)
    for dx, lev, mk, fc in ((-0.15, "medium", "o", "white"), (0.05, "fine", "D", BLUE)):
        v = P5[(c, lev)][3]
        ax.plot(i + dx, v, mk, mec=BLUE, mfc=fc, ms=7, label=f"OpenFOAM {lev}" if i == 0 else None)
        ax.annotate(f"{v:.2f}", (i + dx, v), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=7.5)
    if "waterlily_fyp" in r:
        ax.plot(i + 0.22, r["waterlily_fyp"]["eta_percent"], "s", color=GREY, ms=6, label="WaterLily (FYP)" if i == 0 else None)
        ax.annotate(f"{r['waterlily_fyp']['eta_percent']}", (i + 0.22, r["waterlily_fyp"]["eta_percent"]), xytext=(0, -13), textcoords="offset points", ha="center", fontsize=7.5, color=GREY)
ax.set_xticks(range(3)); ax.set_xticklabels([f"Case {c}\nf* = {CASES[c][0]}, θ₀ = {CASES[c][1]:g}°" for c in CASES])
ax.set_ylabel("η (%)"); ax.set_ylim(0, 40); ax.legend(loc="upper right"); ax.grid(axis="x", visible=False)
fig.tight_layout(); save(fig, "fig08_cases_efficiency.png")

# ---- 9-11 averaged cycles per case
for n_, c in enumerate(CASES):
    f, th0 = CASES[c]; Tc = 1 / f
    fig, axs = plt.subplots(2, 2, figsize=(7.2, 4.8), sharex=True)
    wl = f"{REPO}/reference/waterlily_case{c}_c64_cycle.csv"
    wl = np.genfromtxt(wl, delimiter=",", names=True) if os.path.exists(wl) else None
    for lev, col, lw in (("medium", ORANGE, 1.0), ("fine", BLUE, 1.5)):
        fs, D, sk, eta = P5[(c, lev)]
        ph, A = phase_avg(D, Tc, sk, fs["cycles_complete"])
        for a_, key in zip(axs.flat, ("CY", "CM", "CX", "CP")):
            a_.plot(ph, A[key], color=col, lw=lw, label=f"OpenFOAM {lev} (η {eta:.1f} %)")
    if wl is not None:
        for a_, key in zip(axs.flat, ("CY", "CM", "CX", "CP")):
            a_.plot(wl["t_over_T"], wl[key], color=GREY, lw=0.9, ls="--", label=f"WaterLily FYP (η {REF[c]['waterlily_fyp']['eta_percent']} %)")
    for a_, lab in zip(axs.flat, ("C_Y (lift)", "C_M (pivot moment)", "C_X (drag)", "C_P (power)")):
        a_.set_ylabel(lab)
    axs[1, 0].set_xlabel("t / T"); axs[1, 1].set_xlabel("t / T")
    h_, l_ = axs[0, 0].get_legend_handles_labels()
    fig.suptitle(f"Case {c}: f* = {f}, θ₀ = {th0:g}°   (Kinsey & Dumas η = {REF[c]['eta_percent']} %)", fontsize=9.5)
    fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.legend(h_, l_, loc="lower center", ncol=3, frameon=False)
    save(fig, f"fig{9 + n_:02d}_case{c}_cycle.png")

# ---- 12 power split
fig, ax = plt.subplots(figsize=(6.0, 2.8))
rows = []
for i, c in enumerate(CASES):
    f, th0 = CASES[c]; w = 2 * np.pi * f; fs, D, sk, eta = P5[(c, "fine")]
    sel = D["t"] >= sk / f
    t = D["t"][sel]; Vy = -w * np.sin(w * t); Om = np.radians(th0) * w * np.cos(w * t)
    ph_h, ph_p = np.mean(D["CY"][sel] * Vy), np.mean(D["CM"][sel] * Om)
    rows.append((c, ph_h, ph_p, ph_h + ph_p))
    ax.bar(i - 0.2, ph_h, 0.38, color=BLUE, label="heave part  mean(C_Y V_y / U)" if i == 0 else None)
    ax.bar(i + 0.2, ph_p, 0.38, color=ORANGE, label="pitch part  mean(C_M Ω c / U)" if i == 0 else None)
    ax.annotate(f"{ph_h:.3f}", (i - 0.2, ph_h), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=7.5)
    ax.annotate(f"{ph_p:+.3f}", (i + 0.2, max(ph_p, 0)), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=7.5)
ax.axhline(0, color="k", lw=0.6); ax.set_xticks(range(3)); ax.set_xticklabels([f"Case {c}" for c in CASES])
ax.set_ylabel("mean power coefficient"); ax.legend(); ax.grid(axis="x", visible=False)
fig.tight_layout(); save(fig, "fig12_power_split.png")
json.dump(rows, open(os.path.join(OUT, "power_split.json"), "w"), indent=1)

# ---- 13 workflow
fig, ax = plt.subplots(figsize=(7.2, 1.55)); ax.axis("off")
steps = ["params.py\nf*, θ₀,\nmesh level", "gmsh (Python)\nO-grid +\npolar ring", "gmshToFoam\nchangeDictionary\ncheckMesh", "pimpleFoam\nrigid solidBody\nmotion, 4 ranks",
         "post_forces.py\nC_X, C_Y, C_M,\nC_P, η per cycle", "ci-results\nbranch: logs,\nCSV, figures"]
bw, gap = 1.25, 0.22
for i, s_ in enumerate(steps):
    x = i * (bw + gap)
    ax.add_patch(FancyBboxPatch((x, 0), bw, 0.8, boxstyle="round,pad=0.03", fc="#fdf0e4" if i == 3 else "#eaf1f8", ec=BLUE, lw=0.8))
    ax.text(x + bw / 2, 0.4, s_, ha="center", va="center", fontsize=6.2, linespacing=1.25)
    if i < len(steps) - 1:
        ax.annotate("", xy=(x + bw + gap - 0.03, 0.4), xytext=(x + bw + 0.03, 0.4), arrowprops=dict(arrowstyle="->", lw=0.9))
W = len(steps) * bw + (len(steps) - 1) * gap
ax.text(W / 2, 0.98, "one GitHub Actions job per run (ubuntu-24.04, 4 cores, 16 GB, ≤ 6 h); a matrix runs a whole study in parallel", ha="center", fontsize=7.8, color=GREY)
ax.set_xlim(-0.08, W + 0.08); ax.set_ylim(-0.08, 1.08)
save(fig, "fig13_workflow.png")
print("done")

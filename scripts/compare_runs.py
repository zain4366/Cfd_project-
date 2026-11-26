"""Phase 3 + 4: collect the rigid-mesh Case I runs and compare them.

    python3 scripts/compare_runs.py <folder with one sub-folder per run> <output folder> [--skip 4]

Each run folder holds coefficients.csv (from post_forces.py), forces_summary.json, mesh_info.json.
Averages use the cycles after the first `--skip` (start-up) cycles.

Runs (folder names):
  base                    medium mesh, T/2000, far field 20c  (Phase 3 baseline = Kinsey & Dumas' settings)
  coarse, fine            coarse / fine mesh, no limiter (the fine mesh diverges)
  coarse_l, base_l, fine_l  mesh study with the laplacian limiter "limited corrected 0.33"
  dt1000, dt4000, dt8000  time-step study on the medium mesh (T/1000 diverges)
  R12, R40, R60, R80      domain-size study
  medium_lim, medium_outer4  other solver settings on the medium mesh
"""
import argparse, json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import params as P
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("runs"); ap.add_argument("out"); ap.add_argument("--skip", type=int, default=4)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ref = json.load(open(os.path.join(ROOT, "reference", "kinsey_dumas_2008_caseI.json")))
wl = np.genfromtxt(os.path.join(ROOT, "reference", "waterlily_caseI_c64_cycle.csv"), delimiter=",", names=True)
T = P.PERIOD; w = P.omega()
D_SWEPT = 2.565          # swept height in chords (post_forces.py computes the same value from the geometry)

LABEL = dict(base="medium, T/2000, R = 20c", coarse="coarse, T/2000", fine="fine, T/2000",
             coarse_l="coarse + limiter", base_l="medium + limiter", fine_l="fine + limiter",
             dt1000="medium, T/1000", dt4000="medium, T/4000", dt8000="medium, T/8000",
             R12="far field 12c", R40="far field 40c", R60="far field 60c", R80="far field 80c",
             medium_lim="medium + gradient limiter", medium_outer4="medium + 4 outer loops")
STUDIES = {                                   # (run, label); the finest / largest last
    "mesh (with limiter)": [("coarse_l", "coarse"), ("base_l", "medium"), ("fine_l", "fine")],
    "mesh (no limiter)": [("coarse", "coarse"), ("base", "medium"), ("fine", "fine")],
    "time step": [("dt1000", "T/1000"), ("base", "T/2000"), ("dt4000", "T/4000"), ("dt8000", "T/8000")],
    "domain": [("R12", "12c"), ("base", "20c"), ("R40", "40c"), ("R60", "60c"), ("R80", "80c")],
    "solver settings": [("medium_outer4", "4 outer loops"), ("medium_lim", "gradient limiter"),
                        ("base_l", "laplacian limiter"), ("base", "as baseline")],
}
PLOT_STUDIES = ("mesh (with limiter)", "time step", "domain")


def peak(y):
    return float(np.max(np.abs(np.convolve(y, np.ones(7) / 7, mode="same"))))


def load(name):
    d = os.path.join(a.runs, name)
    f = os.path.join(d, "coefficients.csv")
    if not os.path.exists(f):
        return None
    D = np.genfromtxt(f, delimiter=",", names=True)
    t = D["t"]; CX, CY, CM, CP = D["CX"], D["CY"], D["CM"], D["CP"]
    ncyc = int(np.floor(t[-1] / T + 1e-6))
    cyc, phase = [], []
    for k in range(ncyc):
        tt = np.linspace(k * T, (k + 1) * T, 201)[:-1] + T / 400
        cx, cy, cm, cp = (np.interp(tt, t, v) for v in (CX, CY, CM, CP))
        ph = w * tt
        A, B = np.mean(cy * np.cos(ph)), np.mean(cy * np.sin(ph))
        cyc.append(dict(cycle=k + 1, eta=100 * np.mean(cp) / D_SWEPT, CX=float(np.mean(cx)), CY_peak=peak(cy),
                        CM_peak=peak(cm), timing=(math.degrees(math.atan2(B, A)) + 270) % 360 - 180))
        phase.append(np.c_[cx, cy, cm, cp])
    info = {}
    for fn in ("mesh_info.json", "forces_summary.json"):
        p = os.path.join(d, fn)
        if os.path.exists(p):
            info[fn] = json.load(open(p))
    use = [c for c in cyc if c["cycle"] > a.skip]
    avg = {k: float(np.mean([c[k] for c in use])) for k in ("eta", "CX", "CY_peak", "CM_peak", "timing")} if use else None
    std = {k: float(np.std([c[k] for c in use])) for k in ("eta", "CX", "CY_peak", "CM_peak")} if use else None
    ph = np.mean(phase[a.skip:], axis=0) if len(phase) > a.skip else None
    tm = info.get("forces_summary.json", {}).get("timing", {})
    ex = os.path.join(d, "solver_exit.txt")
    finished = os.path.exists(ex) and "reached endTime" in open(ex).read()
    diverged = bool((not finished) and (not np.all(np.isfinite(CP)) or np.nanmax(np.abs(CX)) > 1e3 or len(cyc) <= a.skip))
    return dict(name=name, finished=finished, diverged=diverged, t_end=float(t[-1] / T), steps=tm.get("steps"), cycles=cyc, avg=avg, std=std, n_avg=len(use), phase=ph,
                cells=info.get("mesh_info.json", {}).get("cells"), s_per_step=tm.get("s_per_step"),
                min_per_cycle=60 * tm["wall_h_per_cycle"] if tm.get("wall_h_per_cycle") else None,
                max_courant=tm.get("max_courant"))


runs = {n: r for n in LABEL if (r := load(n))}
good = {n: r for n, r in runs.items() if not r["diverged"]}
if not runs:
    print("no runs found"); sys.exit(0)
json.dump({n: {k: v for k, v in r.items() if k != "phase"} for n, r in runs.items()},
          open(os.path.join(a.out, "phase34_summary.json"), "w"), indent=1)


def pct(v, r):
    return 100 * (v - r) / r


def fmt(r, k, nd=3):
    return f"{r['avg'][k]:.{nd}f}" if r and r["avg"] else "n/a"


L = []
b = runs.get("base")
if b and b["avg"]:
    L += [f"## Phase 3: Case I baseline (medium mesh, T/2000, far field 20c), average of cycles {a.skip + 1}-{b['cycles'][-1]['cycle']}", "",
          "| | η % | mean C_X | peak C_Y | peak C_M | lift timing |", "|---|---|---|---|---|---|"]
    for c in b["cycles"]:
        L.append(f"| cycle {c['cycle']} | {c['eta']:.2f} | {c['CX']:.3f} | {c['CY_peak']:.3f} | {c['CM_peak']:.3f} | {c['timing']:+.1f}° |")
    av, sd = b["avg"], b["std"]
    L.append(f"| **average** | **{av['eta']:.2f} ± {sd['eta']:.2f}** | **{av['CX']:.3f}** | **{av['CY_peak']:.3f}** | **{av['CM_peak']:.3f}** | **{av['timing']:+.1f}°** |")
    L.append(f"| Kinsey & Dumas | {ref['eta_percent']} | {ref['CX_mean']} | {ref['CY_peak']} | {ref['CM_peak']} | ≈ 0° |")
    W = ref["waterlily_fyp"]
    L.append(f"| WaterLily (FYP) | {W['eta_percent']} | {W['CX_mean']} | {W['CY_peak']} | {W['CM_peak']} | within 3° |")
    L.append(f"| difference from K&D | {av['eta'] - ref['eta_percent']:+.2f} points ({pct(av['eta'], ref['eta_percent']):+.1f} %) | "
             f"{pct(av['CX'], ref['CX_mean']):+.1f} % | {pct(av['CY_peak'], ref['CY_peak']):+.1f} % | {pct(av['CM_peak'], ref['CM_peak']):+.1f} % | |")
    L.append("")

L += [f"## Phase 4: independence studies (each value = average of cycles {a.skip + 1} onward)", ""]
for study, members in STUDIES.items():
    L += [f"### {study}", "", "| run | cells | η % | mean C_X | peak C_Y | peak C_M | s/step | min/cycle | max Courant |",
          "|---|---|---|---|---|---|---|---|---|"]
    for n, lab in members:
        r = runs.get(n)
        if not r:
            L.append(f"| {lab} | | not run | | | | | | |"); continue
        if r["diverged"] or not r["avg"]:
            L.append(f"| {lab} | {r['cells'] or ''} | diverged after {r['steps'] or '?'} steps (t/T = {r['t_end']:.2f}) | | | | | | |"); continue
        L.append(f"| {lab} | {r['cells'] or ''} | {r['avg']['eta']:.2f} | {fmt(r, 'CX')} | {fmt(r, 'CY_peak')} | {fmt(r, 'CM_peak')} | "
                 f"{r['s_per_step'] or 0:.2f} | {r['min_per_cycle'] or 0:.1f} | {r['max_courant'] or 0:.1f} |")
    ok = [n for n, _ in members if n in runs and runs[n]["avg"] and not runs[n]["diverged"]]
    vals = [runs[n]["avg"]["eta"] for n in ok]
    if len(vals) >= 2:
        L.append(f"\nη spread across the {len(vals)} converged runs: {max(vals) - min(vals):.2f} points; change between the last two: "
                 f"{vals[-1] - vals[-2]:+.2f} points ({pct(vals[-1], vals[-2]):+.1f} %).")
    if study == "mesh (with limiter)" and len(vals) == 3 and all(runs[n]["cells"] for n, _ in members):
        f1, f2, f3 = vals[2], vals[1], vals[0]                                  # fine, medium, coarse
        N1, N2, N3 = (runs[n]["cells"] for n in ("fine_l", "base_l", "coarse_l"))
        r21, r32 = math.sqrt(N1 / N2), math.sqrt(N2 / N3)
        e32, e21 = f3 - f2, f2 - f1
        if e21 != 0 and e32 / e21 > 0:                                         # monotonic: Celik et al. (2008) GCI
            p = abs(math.log(abs(e32 / e21))) / math.log(r21)                   # equal ratios assumed for the order
            ext = (r21 ** p * f1 - f2) / (r21 ** p - 1)
            gci = 1.25 * abs((f1 - f2) / f1) / (r21 ** p - 1) * 100
            L.append(f"Grid convergence index (Celik et al. 2008): refinement ratios {r32:.2f} / {r21:.2f}, observed order p = {p:.2f}, "
                     f"extrapolated η = {ext:.2f} %, GCI(fine) = {gci:.2f} %.")
        else:
            L.append("Mesh results are not monotonic (oscillatory convergence); GCI is not defined, the spread above is the uncertainty.")
    L.append("")
open(os.path.join(a.out, "phase34_summary.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L))

# ---------------------------------------------------------------- figures
t200 = (np.arange(200) + 0.5) / 200
fig, ax = plt.subplots(figsize=(8, 4.2), dpi=140)
for n, r in good.items():
    ax.plot([c["cycle"] for c in r["cycles"]], [c["eta"] for c in r["cycles"]], "o-" if n == "base" else ".-",
            lw=2 if n == "base" else 1, ms=5, label=LABEL[n])
ax.axhline(ref["eta_percent"], color="k", ls="--", lw=1, label="Kinsey & Dumas 33.7 %")
ax.axhline(ref["waterlily_fyp"]["eta_percent"], color="gray", ls=":", lw=1, label="WaterLily (FYP) 32.2 %")
ax.axvspan(0.5, a.skip + 0.5, color="0.9", zorder=0); ax.text(a.skip / 2 + 0.5, ax.get_ylim()[1], "start-up (not averaged)", ha="center", va="top", fontsize=8)
ax.set_xlabel("cycle"); ax.set_ylabel("η per cycle (%)"); ax.grid(alpha=0.3); ax.legend(fontsize=7, ncol=2)
fig.tight_layout(); fig.savefig(os.path.join(a.out, "eta_per_cycle.png")); plt.close(fig)

if b and b["phase"] is not None:
    fig, axs = plt.subplots(2, 2, figsize=(10, 6.5), dpi=140)
    for i, (ax, key, lab) in enumerate(zip(axs.flat, ("CY", "CM", "CX", "CP"), ("C_Y (lift)", "C_M (pivot)", "C_X (drag)", "C_P (power)"))):
        ax.plot(t200, b["phase"][:, [1, 2, 0, 3][i]], lw=1.6, label=f"OpenFOAM rigid mesh (mean of cycles {a.skip + 1}-{b['cycles'][-1]['cycle']})")
        ax.plot(wl["t_over_T"], wl[key], ls="--", lw=1.2, label="WaterLily, FYP")
        ax.set_ylabel(lab); ax.set_xlabel("t / T"); ax.grid(alpha=0.3)
    axs[0, 0].legend(fontsize=7)
    fig.suptitle(f"Case I baseline: η = {b['avg']['eta']:.1f} % (Kinsey & Dumas 33.7 %, WaterLily 32.2 %)", fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(a.out, "baseline_cycle_loads.png")); plt.close(fig)

for study, members in [(k, STUDIES[k]) for k in PLOT_STUDIES]:
    have = [(n, lab) for n, lab in members if n in good and good[n]["phase"] is not None]
    if len(have) < 2:
        continue
    fig, axs = plt.subplots(2, 2, figsize=(10, 6.5), dpi=140)
    for i, (ax, lab_) in enumerate(zip(axs.flat, ("C_Y (lift)", "C_M (pivot)", "C_X (drag)", "C_P (power)"))):
        for n, lab in have:
            ax.plot(t200, runs[n]["phase"][:, [1, 2, 0, 3][i]], lw=1.2, label=f"{lab}: η = {runs[n]['avg']['eta']:.1f} %")
        ax.set_ylabel(lab_); ax.set_xlabel("t / T"); ax.grid(alpha=0.3)
    axs[0, 0].legend(fontsize=8)
    fig.suptitle(f"{study.capitalize()} study: cycle-averaged loads", fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(a.out, f"study_{study.split(' ')[0]}.png")); plt.close(fig)

fig, axs = plt.subplots(1, 3, figsize=(11, 3.6), dpi=140, sharey=True)
for ax, (study, members) in zip(axs, [(k, STUDIES[k]) for k in PLOT_STUDIES]):
    xs = [(lab, good[n]) for n, lab in members if n in good and good[n]["avg"]]
    if not xs:
        continue
    ax.errorbar(range(len(xs)), [r["avg"]["eta"] for _, r in xs], yerr=[r["std"]["eta"] for _, r in xs], fmt="o-", capsize=4)
    ax.set_xticks(range(len(xs))); ax.set_xticklabels([l for l, _ in xs])
    ax.axhline(ref["eta_percent"], color="k", ls="--", lw=1); ax.axhline(ref["waterlily_fyp"]["eta_percent"], color="gray", ls=":", lw=1)
    ax.set_title(study); ax.grid(alpha=0.3)
axs[0].set_ylabel("η (%)  (bars: cycle-to-cycle spread)")
fig.suptitle("Phase 4: η against mesh, time step and domain size (dashed: Kinsey & Dumas, dotted: WaterLily)", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(a.out, "independence_eta.png")); plt.close(fig)
print("figures written to", a.out)

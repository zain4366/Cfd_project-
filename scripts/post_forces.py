"""Forces -> coefficients, power and efficiency per cycle, compared with Kinsey & Dumas and the FYP WaterLily result.

    python3 scripts/post_forces.py <case dir> <output dir> [--log <solver log>]

Definitions (same as the FYP):
  C_X, C_Y = force / (0.5 rho U^2 c span);  C_M = moment about the moving pivot / (0.5 rho U^2 c^2 span)
  C_P = C_Y * V_y / U + C_M * Omega * c / U         (power extracted from the flow)
  eta = mean(C_P) * c / d,  d = height swept by the foil (computed from the geometry)
  peaks = largest |7-sample moving average| in a cycle resampled to 200 points
  lift timing = phase of the first harmonic of C_Y relative to the heave velocity (0 = in step)
"""
import argparse, glob, json, math, os, re, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import params as P

ap = argparse.ArgumentParser()
ap.add_argument("case"); ap.add_argument("out"); ap.add_argument("--log")
ap.add_argument("--csv", help="re-process a saved coefficients.csv instead of postProcessing/forces")
ap.add_argument("--label", help="name of this run in the plots (default: read the mesh motion type)")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
if not a.label:
    dm = os.path.join(a.case, "constant", "dynamicMeshDict")
    a.label = "OpenFOAM overset" if os.path.exists(dm) and "dynamicOversetFvMesh" in open(dm).read() else "OpenFOAM rigid moving mesh"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_dat(name):
    rows = []
    for d in sorted(glob.glob(os.path.join(a.case, "postProcessing", "forces", "*")), key=lambda p: float(os.path.basename(p))):
        f = os.path.join(d, name)
        if not os.path.exists(f):
            continue
        for line in open(f):
            if line.startswith("#") or not line.strip():
                continue
            v = line.replace("(", " ").replace(")", " ").split()
            try:
                rows.append([float(x) for x in v[:4]])
            except ValueError:
                pass
    if not rows:
        return None
    r = np.array(rows)
    _, idx = np.unique(r[:, 0], return_index=True)     # restarts can repeat times: keep the first of each
    return r[np.sort(idx)]


w = P.omega(); th0 = math.radians(P.THETA0)
if a.csv:
    D = np.genfromtxt(a.csv, delimiter=",", names=True)
    t, CX, CY, CM = D["t"], D["CX"], D["CY"], D["CM"]
else:
    F = read_dat("force.dat"); M = read_dat("moment.dat")
    if F is None or M is None:
        print("no force data yet"); sys.exit(0)
    n = min(len(F), len(M)); F, M = F[:n], M[:n]
    t = F[:, 0]; span = P.ZTHICK; q = 0.5 * span
    yp = P.H0 * np.cos(w * t)                               # pivot height
    CX = F[:, 1] / q; CY = F[:, 2] / q
    CM = (M[:, 3] + yp * F[:, 1]) / q                       # moment moved from the origin to the pivot
Vy = -P.H0 * w * np.sin(w * t)
Om = th0 * w * np.cos(w * t)
CP = CY * Vy + CM * Om


def swept_height():
    xs = (1 - np.cos(np.linspace(0, np.pi, 201))) / 2
    yt = 5 * P.THICK * (0.2969 * np.sqrt(xs) - 0.126 * xs - 0.3516 * xs**2 + 0.2843 * xs**3 - 0.1015 * xs**4)
    xb = np.r_[xs, xs] - P.XP; yb = np.r_[yt, -yt]
    lo, hi = 1e9, -1e9
    for tt in np.linspace(0, P.PERIOD, 1441):
        th = math.radians(P.pitch_deg(tt))
        y = P.heave(tt) + xb * math.sin(th) + yb * math.cos(th)
        lo, hi = min(lo, y.min()), max(hi, y.max())
    return hi - lo


d = swept_height()
T = P.PERIOD
ncyc = int(np.floor(t[-1] / T + 1e-9))
ref = json.load(open(os.path.join(ROOT, "reference", "kinsey_dumas_2008_caseI.json")))


def peak(y):
    k = np.convolve(y, np.ones(7) / 7, mode="same")
    return float(np.max(np.abs(k)))


cycles = []
for k in range(ncyc):
    tt = np.linspace(k * T, (k + 1) * T, 201)[:-1] + T / 400
    m = (t >= k * T) & (t <= (k + 1) * T)
    if m.sum() < 20:
        continue
    cx, cy, cm, cp = (np.interp(tt, t, v) for v in (CX, CY, CM, CP))
    ph = w * tt
    A, B = np.mean(cy * np.cos(ph)), np.mean(cy * np.sin(ph))
    timing = (math.degrees(math.atan2(B, A)) + 90 + 180) % 360 - 180   # heave velocity ~ cos(ph + 90 deg)
    cycles.append(dict(cycle=k + 1, eta=100 * np.mean(cp) / d, CP=float(np.mean(cp)), CX=float(np.mean(cx)),
                       CY_peak=peak(cy), CM_peak=peak(cm), lift_timing_deg=timing))

timing = {}
if a.log and os.path.exists(a.log):
    txt = open(a.log, errors="ignore").read()
    ex = [float(v) for v in re.findall(r"ExecutionTime = ([\d.eE+-]+) s", txt)]
    co = [float(v) for v in re.findall(r"Courant Number mean: [\d.eE+-]+ max: ([\d.eE+-]+)", txt)]
    dts = [float(v) for v in re.findall(r"^deltaT = ([\d.eE+-]+)", txt, flags=re.M)]
    if ex:
        timing = dict(steps=len(ex), wall_s=ex[-1], s_per_step=ex[-1] / len(ex), sim_time=float(t[-1]),
                      wall_h_per_cycle=ex[-1] / max(t[-1] / T, 1e-9) / 3600,
                      max_courant=max(co) if co else None, last_deltaT=dts[-1] if dts else None,
                      steps_per_cycle_now=(T / dts[-1]) if dts else (T / np.median(np.diff(t[-50:])) if len(t) > 50 else None))

summary = dict(sim_time=float(t[-1]), cycles_complete=len(cycles), swept_height=d, cycles=cycles, timing=timing, reference=ref)
json.dump(summary, open(os.path.join(a.out, "forces_summary.json"), "w"), indent=1)
np.savetxt(os.path.join(a.out, "coefficients.csv"), np.c_[t, t / T, CX, CY, CM, CP], delimiter=",",
           header="t,t_over_T,CX,CY,CM,CP", comments="", fmt="%.6g")

lines = [f"Simulated time {t[-1]:.3f} c/U = {t[-1] / T:.2f} cycles; swept height d = {d:.3f} c", ""]
if timing:
    spc = timing.get("steps_per_cycle_now")
    lines += [f"Cost: {timing['steps']} steps, {timing['s_per_step']:.2f} s/step, {60 * timing['wall_h_per_cycle']:.1f} min per cycle; "
              f"max Courant {timing['max_courant']}, steps per cycle {spc:.0f}" if spc else "", ""]
lines += ["| | η % | mean C_X | peak C_Y | peak C_M | lift timing |", "|---|---|---|---|---|---|"]
for c in cycles:
    lines.append(f"| cycle {c['cycle']} | {c['eta']:.1f} | {c['CX']:.3f} | {c['CY_peak']:.3f} | {c['CM_peak']:.3f} | {c['lift_timing_deg']:+.0f}° |")
lines.append(f"| Kinsey & Dumas | {ref['eta_percent']} | {ref['CX_mean']} | {ref['CY_peak']} | {ref['CM_peak']} | ≈ 0° |")
w_ = ref["waterlily_fyp"]
lines.append(f"| WaterLily (FYP) | {w_['eta_percent']} | {w_['CX_mean']} | {w_['CY_peak']} | {w_['CM_peak']} | within 3° |")
open(os.path.join(a.out, "forces_summary.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))

# ---------------------------------------------------------------- figures
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, axs = plt.subplots(4, 1, figsize=(9, 8.5), dpi=140, sharex=True)
for ax, y, lab in zip(axs, (CY, CM, CX, CP), ("C_Y (lift)", "C_M (pivot)", "C_X (drag)", "C_P (power)")):
    ax.plot(t / T, y, lw=0.7); ax.set_ylabel(lab); ax.grid(alpha=0.3)
axs[-1].set_xlabel("t / T")
fig.suptitle(f"{a.label}, Case I: force history", fontsize=11); fig.tight_layout()
fig.savefig(os.path.join(a.out, "force_history.png")); plt.close(fig)

if cycles:
    k = cycles[-1]["cycle"] - 1
    m = (t >= k * T) & (t <= (k + 1) * T)
    wl = np.genfromtxt(os.path.join(ROOT, "reference", "waterlily_caseI_c64_cycle.csv"), delimiter=",", names=True)
    fig, axs = plt.subplots(2, 2, figsize=(10, 6.5), dpi=140)
    for ax, y, key, lab in zip(axs.flat, (CY, CM, CX, CP), ("CY", "CM", "CX", "CP"), ("C_Y", "C_M", "C_X", "C_P")):
        ax.plot(t[m] / T - k, y[m], color="C0", lw=1.2, label=f"{a.label} (cycle {k + 1})")
        ax.plot(wl["t_over_T"], wl[key], color="C1", lw=1.2, ls="--", label="WaterLily, FYP (64 cells)")
        ax.set_ylabel(lab); ax.set_xlabel("t / T"); ax.grid(alpha=0.3)
    axs[0, 0].legend(fontsize=8)
    fig.suptitle(f"One cycle of Case I: η = {cycles[-1]['eta']:.1f} % (Kinsey & Dumas 33.7 %, WaterLily 32.2 %)", fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(a.out, "cycle_loads.png")); plt.close(fig)

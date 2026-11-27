"""Phase 5: compare Kinsey & Dumas Cases I, II, III (medium and fine meshes, far field 80c) with the paper and WaterLily.

    python3 scripts/compare_cases.py <folder with caseI_medium, caseI_fine, ...> <output folder>

Averages use the settled cycles only: Case I cycles 9-14, Case II 9-16, Case III 5-8 (see SKIP).
"""
import json, os, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = json.load(open(os.path.join(ROOT, "reference", "kinsey_dumas_2008_cases.json")))
CASES = ("I", "II", "III")
SKIP = {"I": 8, "II": 8, "III": 4}
DOMAIN_SLOPE = 34.1   # Case I: eta(R) = eta_inf + 34.1/R (Phase 4, medium mesh); used only for Case I
KEYS = (("eta", "η %"), ("CX", "mean C_X"), ("CY_peak", "peak C_Y"), ("CM_peak", "peak C_M"))


def load(case, level):
    d = os.path.join(src, f"case{case}_{level}")
    f = os.path.join(d, "forces_summary.json")
    if not os.path.exists(f):
        return None
    S = json.load(open(f))
    use = [c for c in S["cycles"] if c["cycle"] > SKIP[case]]
    avg = {k: float(np.mean([c[k] for c in use])) for k, _ in KEYS}
    avg["timing"] = float(np.mean([c["lift_timing_deg"] for c in use]))
    spread = float(np.ptp([c["eta"] for c in use]))
    D = np.genfromtxt(os.path.join(d, "coefficients.csv"), delimiter=",", names=True)
    T = 1 / REF[case]["fstar"]
    ph = (np.arange(200) + 0.5) / 200
    curves = np.mean([[np.interp((k + ph) * T, D["t"], D[c]) for c in ("CX", "CY", "CM", "CP")]
                      for k in range(SKIP[case], S["cycles_complete"])], axis=0)
    cells = json.load(open(os.path.join(d, "mesh_info.json"))).get("cells") if os.path.exists(os.path.join(d, "mesh_info.json")) else None
    return dict(avg=avg, spread=spread, n=len(use), first=SKIP[case] + 1, last=S["cycles_complete"], curves=curves, cells=cells,
                min_per_cycle=60 * S["timing"]["wall_h_per_cycle"], eta_cycles=[c["eta"] for c in S["cycles"]])


R = {(c, l): r for c in CASES for l in ("medium", "fine") if (r := load(c, l))}
L = ["## Phase 5: Kinsey & Dumas Table 2 cases, far field 80c, laplacian limiter", "",
     "| Case | f*, θ₀ | Source | Cycles averaged | η % | mean C_X | peak C_Y | peak C_M | lift timing |",
     "|---|---|---|---|---|---|---|---|---|"]
summary = {}
for c in CASES:
    ref = REF[c]
    tag = f"{ref['fstar']}, {ref['theta0']:g}°"
    for lev in ("medium", "fine"):
        r = R.get((c, lev))
        if not r:
            continue
        a = r["avg"]
        L.append(f"| {c} | {tag} | OpenFOAM {lev} ({r['cells']:,} cells) | {r['first']}-{r['last']} | {a['eta']:.2f} | {a['CX']:.3f} | "
                 f"{a['CY_peak']:.3f} | {a['CM_peak']:.3f} | {a['timing']:+.0f}° |")
        summary[f"{c}_{lev}"] = dict(a, cells=r["cells"], cycles=[r["first"], r["last"]], eta_spread=r["spread"], min_per_cycle=r["min_per_cycle"])
    L.append(f"| {c} | {tag} | **Kinsey & Dumas** | | **{ref['eta_percent']}** | {ref['CX_mean']} | {ref['CY_peak']} | {ref['CM_peak']} | |")
    if "waterlily_fyp" in ref:
        w = ref["waterlily_fyp"]
        L.append(f"| {c} | {tag} | WaterLily (FYP) | | {w['eta_percent']} | {w['CX_mean']} | {w['CY_peak']} | {w['CM_peak']} | |")
L += ["", "### Difference from Kinsey & Dumas", "", "| Case | Mesh | η (points) | η (%) | mean C_X | peak C_Y | peak C_M |", "|---|---|---|---|---|---|---|"]
for c in CASES:
    ref = REF[c]
    for lev in ("medium", "fine"):
        r = R.get((c, lev))
        if not r:
            continue
        a = r["avg"]
        pc = lambda k, rk: 100 * (a[k] - ref[rk]) / ref[rk]
        L.append(f"| {c} | {lev} | {a['eta'] - ref['eta_percent']:+.2f} | {pc('eta', 'eta_percent'):+.1f} % | {pc('CX', 'CX_mean'):+.1f} % | "
                 f"{pc('CY_peak', 'CY_peak'):+.1f} % | {pc('CM_peak', 'CM_peak'):+.1f} % |")
if ("I", "fine") in R:
    corr = DOMAIN_SLOPE / 80
    L += ["", f"Case I domain correction (Phase 4 slope 34.1/R at 80c = {corr:.2f} points): medium "
          f"{R[('I', 'medium')]['avg']['eta'] - corr:.2f} %, fine {R[('I', 'fine')]['avg']['eta'] - corr:.2f} % for an infinite domain "
          "(Kinsey & Dumas 33.7 %). The slope was measured for Case I only; Cases II and III are reported at 80c."]
L += ["", "Cycle-to-cycle spread of η over the averaged cycles: " +
      ", ".join(f"Case {c} {l} {R[(c, l)]['spread']:.2f}" for c in CASES for l in ("medium", "fine") if (c, l) in R) + " points."]
open(os.path.join(out, "phase5_summary.md"), "w").write("\n".join(L) + "\n")
json.dump(summary, open(os.path.join(out, "phase5_summary.json"), "w"), indent=1)
print("\n".join(L))

# --- efficiency per case: OpenFOAM medium / fine against the paper and WaterLily
fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=140)
for i, c in enumerate(CASES):
    ref = REF[c]
    ax.plot([i - 0.3, i + 0.3], [ref["eta_percent"]] * 2, color="k", lw=2, label="Kinsey & Dumas" if i == 0 else None)
    if "waterlily_fyp" in ref:
        ax.plot(i + 0.2, ref["waterlily_fyp"]["eta_percent"], "s", color="0.55", ms=7, label="WaterLily (FYP)" if i == 0 else None)
    for dx, lev, mk in ((-0.16, "medium", "o"), (0.04, "fine", "D")):
        if (c, lev) in R:
            v = R[(c, lev)]["avg"]["eta"]
            ax.plot(i + dx, v, mk, color="C0", ms=7, mfc="white" if lev == "medium" else "C0",
                    label=f"OpenFOAM {lev}, 80c" if i == 0 else None)
            ax.annotate(f"{v:.1f}", (i + dx, v), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=8)
    ax.annotate(f"paper {ref['eta_percent']}", (i + 0.3, ref["eta_percent"]), textcoords="offset points", xytext=(4, -3), fontsize=8)
    if "waterlily_fyp" in ref:
        ax.annotate(f"{ref['waterlily_fyp']['eta_percent']}", (i + 0.2, ref["waterlily_fyp"]["eta_percent"]), textcoords="offset points", xytext=(0, -14), ha="center", fontsize=8, color="0.4")
ax.set_xticks(range(3)); ax.set_xticklabels([f"Case {c}\nf* {REF[c]['fstar']}, θ₀ {REF[c]['theta0']:g}°" for c in CASES])
ax.set_ylabel("η (%)"); ax.set_ylim(0, 40); ax.grid(axis="y", alpha=0.3); ax.legend(fontsize=8, loc="upper right")
ax.set_title("Efficiency of the three Kinsey & Dumas cases", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(out, "eta_cases.png")); plt.close(fig)

# --- one averaged cycle per case
for c in CASES:
    have = [l for l in ("medium", "fine") if (c, l) in R]
    if not have:
        continue
    wl_csv = os.path.join(ROOT, "reference", f"waterlily_case{c}_c64_cycle.csv")
    wl = np.genfromtxt(wl_csv, delimiter=",", names=True) if os.path.exists(wl_csv) else None
    ph = (np.arange(200) + 0.5) / 200
    fig, axs = plt.subplots(2, 2, figsize=(10, 6.5), dpi=140)
    for j, (ax, key, lab) in enumerate(zip(axs.flat, ("CY", "CM", "CX", "CP"), ("C_Y (lift)", "C_M (pivot)", "C_X (drag)", "C_P (power)"))):
        col = {"CY": 1, "CM": 2, "CX": 0, "CP": 3}[key]
        for lev, ls in zip(have, ("-", "-")):
            ax.plot(ph, R[(c, lev)]["curves"][col], lw=1.6 if lev == "fine" else 1.1, alpha=1 if lev == "fine" else 0.7,
                    label=f"OpenFOAM {lev}, 80c (η {R[(c, lev)]['avg']['eta']:.1f} %)")
        if wl is not None:
            ax.plot(wl["t_over_T"], wl[key], "--", color="0.45", lw=1.2, label=f"WaterLily, FYP (η {REF[c]['waterlily_fyp']['eta_percent']} %)")
        ax.set_xlabel("t / T"); ax.set_ylabel(lab); ax.grid(alpha=0.3)
    axs[0, 0].legend(fontsize=7)
    fig.suptitle(f"Case {c} (f* {REF[c]['fstar']}, θ₀ {REF[c]['theta0']:g}°): one averaged cycle; Kinsey & Dumas η = {REF[c]['eta_percent']} %", fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(out, f"cycle_loads_case{c}.png")); plt.close(fig)
print("figures written to", out)

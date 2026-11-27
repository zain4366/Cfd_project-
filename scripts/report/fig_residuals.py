"""Residual history of the final Case I fine-mesh run (fig14_residuals.png).
    python3 fig_residuals.py <log.solver.gz> <out dir>"""
import gzip, json, os, re, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

src, out = sys.argv[1], sys.argv[2]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9,
                     "legend.fontsize": 7.5, "savefig.dpi": 300, "savefig.bbox": "tight", "axes.grid": True, "grid.alpha": 0.3,
                     "axes.spines.top": False, "axes.spines.right": False})
T = 1 / 0.14
num = r"([-+0-9.eE]+)"
rows, cur = [], None
for line in gzip.open(src, "rt", errors="ignore"):
    if line.startswith("Time = "):
        if cur and "pfin" in cur:
            rows.append(cur)
        cur = {"t": float(line.split()[2]), "it": 0, "p": []}
    elif cur is None:
        continue
    elif line.startswith("PIMPLE: iteration"):
        cur["it"] = int(line.split()[2])
    elif "Solving for Ux" in line:
        r0 = float(re.search(r"Initial residual = " + num, line).group(1))
        cur["ux1" if cur["it"] == 1 else "ux2"] = r0
    elif "Solving for p," in line:
        m = re.search(r"Initial residual = " + num + r", Final residual = " + num, line)
        cur["p"].append(float(m.group(1)))
        cur["pfin"] = float(m.group(2))
    elif line.startswith("time step continuity errors"):
        cur["cont"] = abs(float(re.search(r"sum local = " + num, line).group(1)))
t = np.array([r["t"] for r in rows]) / T
ux1 = np.array([r.get("ux1", np.nan) for r in rows]); ux2 = np.array([r.get("ux2", np.nan) for r in rows])
p1 = np.array([r["p"][0] for r in rows]); plast = np.array([r["p"][-1] for r in rows])
pfin = np.array([r["pfin"] for r in rows]); cont = np.array([r.get("cont", np.nan) for r in rows])
print(len(rows), "steps,", t[-1], "cycles")

fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [1.6, 1]})
k = max(1, len(t) // 4000)
ser = [(ux1, "Uₓ, initial (1st outer loop)", "#1f5fa8"), (ux2, "Uₓ, initial (2nd outer loop)", "#7aa6d6"),
       (p1, "p, initial (1st corrector)", "#e07a1f"), (plast, "p, initial (last corrector)", "#f2b47a"),
       (pfin, "p, final (last corrector)", "#b8322a"), (cont, "continuity error (sum local)", "#6b6b6b")]
for y, lab, col in ser:
    ax[0].semilogy(t[::k], y[::k], lw=0.6, color=col, label=lab)
ax[0].set_xlabel("t / T (cycles)"); ax[0].set_ylabel("residual"); ax[0].set_xlim(0, t[-1])
ax[0].set_title("(a) whole run, every %d%s step" % (k, "th" if k > 3 else ("nd" if k == 2 else "st")))
m = t >= t[-1] - 1
for y, lab, col in ser:
    ax[1].semilogy(t[m] - (t[-1] - 1), y[m], lw=0.6, color=col)
ax[1].set_xlabel("t / T within the last cycle"); ax[1].set_xlim(0, 1); ax[1].set_title("(b) last cycle, every step")
ax[0].set_ylim(1e-18, 1); ax[1].set_ylim(1e-18, 1)
fig.legend(*ax[0].get_legend_handles_labels(), loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.12), frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(out, "fig14_residuals.png")); plt.close(fig)
s = {"steps": len(rows), "cycles": float(t[-1]),
     "ux1_median": float(np.nanmedian(ux1)), "ux2_median": float(np.nanmedian(ux2)), "p1_median": float(np.median(p1)),
     "pfin_max": float(np.max(pfin)), "pfin_median": float(np.median(pfin)), "cont_max": float(np.nanmax(cont)),
     "drop_outer": float(np.nanmedian(ux1 / ux2))}
json.dump(s, open(os.path.join(out, "residuals.json"), "w"), indent=1); print(s)

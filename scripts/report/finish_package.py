import csv, json, os, shutil, glob
P = "AE471_data"; S = os.path.join(P, "01_summary_tables")
rows = {r["run"]: r for r in json.load(open(os.path.join(S, "all_runs_summary.json")))}
def wcsv(name, head, data):
    with open(os.path.join(S, name), "w", newline="") as f:
        w = csv.writer(f); w.writerow(head); [w.writerow(d) for d in data]
g = lambda r, k, n=4: ("" if r.get(k) is None else (f"{r[k]:.{n}f}" if isinstance(r[k], float) else r[k]))
K = ["eta_percent", "mean_CX", "peak_CY", "peak_CM", "lift_timing_deg"]
wcsv("time_step_study.csv", ["run", "steps_per_cycle", "status", *K, "max_courant", "min_per_cycle"],
     [[n, rows[n]["steps_per_cycle"], rows[n]["status"], *[g(rows[n], k) for k in K], g(rows[n], "max_courant", 1), g(rows[n], "min_per_cycle", 1)] for n in ("dt1000", "base", "dt4000", "dt8000")])
dom = json.load(open("figs/domain_fit.json"))
wcsv("domain_study.csv", ["far_field_c", "run", "cells", "eta_cycle10_percent", "eta_avg_cycles5to10_percent", "eta_fit_percent", "mean_CX", "peak_CM"],
     [[R, n, rows[n]["cells"], f"{e:.4f}", g(rows[n], "eta_percent"), f"{dom['eta_inf'] + dom['slope'] / R:.4f}", g(rows[n], "mean_CX"), g(rows[n], "peak_CM")]
      for (R, e), n in zip(dom["points"], ("R12", "base", "R40", "R60", "R80"))] + [["inf", "fit", "", "", "", f"{dom['eta_inf']:.4f}", "", ""]])
wcsv("mesh_study.csv", ["run", "mesh", "cells", "laplacian", "status", *K, "min_per_cycle"],
     [[n, rows[n]["mesh"], rows[n]["cells"], rows[n]["laplacian"], rows[n]["status"], *[g(rows[n], k) for k in K], g(rows[n], "min_per_cycle", 1)]
      for n in ("coarse_l", "base_l", "fine_l", "xfine_l", "coarse", "base", "fine")])
KD = json.load(open("/home/claude/cfd_project-/reference/kinsey_dumas_2008_cases.json"))
data = []
for c in ("I", "II", "III"):
    for lev in ("medium", "fine"):
        r = rows[f"case{c}_{lev}"]; data.append([c, f"OpenFOAM {lev}", r["cells"], *[g(r, k) for k in K]])
    data.append([c, "Kinsey & Dumas 2008", 72000, KD[c]["eta_percent"], KD[c]["CX_mean"], KD[c]["CY_peak"], KD[c]["CM_peak"], ""])
    if "waterlily_fyp" in KD[c]:
        w = KD[c]["waterlily_fyp"]; data.append([c, "WaterLily (FYP, 64 cells/chord)", "", w["eta_percent"], w["CX_mean"], w["CY_peak"], w["CM_peak"], ""])
wcsv("cases_comparison.csv", ["case", "source", "cells", *K], data)
ps = json.load(open("figs/power_split.json"))
wcsv("power_split_fine_mesh.csv", ["case", "heave_part_mean_CY_Vy", "pitch_part_mean_CM_Omega", "total_mean_CP"], [[c, f"{a:.5f}", f"{b:.5f}", f"{t:.5f}"] for c, a, b, t in ps])
json.dump(dom, open(os.path.join(S, "domain_fit.json"), "w"), indent=1)
# figures, reference, overset, scripts
F = os.path.join(P, "09_figures_300dpi"); os.makedirs(F, exist_ok=True)
for f in glob.glob("figs/*.png"): shutil.copy(f, F)
R_ = os.path.join(P, "11_reference_data"); os.makedirs(R_, exist_ok=True)
for f in glob.glob("/home/claude/cfd_project-/reference/*"):
    if not f.endswith(".pdf"): shutil.copy(f, R_)
O = os.path.join(P, "00_overset_phase1"); os.makedirs(O, exist_ok=True)
for f in glob.glob("/home/claude/cfd_project-/docs/phase1/*"): shutil.copy(f, O)
SC = os.path.join(P, "12_scripts_snapshot"); os.makedirs(SC, exist_ok=True)
for f in glob.glob("/home/claude/cfd_project-/scripts/*"):
    if os.path.isfile(f) and not f.endswith(".pyc"): shutil.copy(f, SC)
shutil.copy("report_figures.py", SC); shutil.copy("build_package.py", SC)
print("ok")

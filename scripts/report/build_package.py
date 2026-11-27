"""Collect every run's data from the ci-results checkout into a clean, documented package."""
import csv, glob, gzip, json, os, re, shutil, sys
import numpy as np
SRC, DST = sys.argv[1], sys.argv[2]
os.makedirs(DST, exist_ok=True)
FSTAR = {0.14: "I", 0.18: "II", 0.06: "III"}

STUDY = {  # run -> (folder, study, description)
 "phase2b/rigid_medium": ("02_phase2_first_test", "Phase 2 first test", "medium, T/2000, 20c, 3 cycles"),
 "phase34/base": ("03_phase3_baseline", "Phase 3 baseline", "medium, T/2000, far field 20c"),
 "phase34/dt1000": ("04_phase4_time_step", "time step", "medium, T/1000 (diverged)"),
 "phase34/dt4000": ("04_phase4_time_step", "time step", "medium, T/4000"),
 "phase34/dt8000": ("04_phase4_time_step", "time step", "medium, T/8000"),
 "phase34/R12": ("05_phase4_domain", "domain", "medium, far field 12c"),
 "phase34/R40": ("05_phase4_domain", "domain", "medium, far field 40c"),
 "phase34/R60": ("05_phase4_domain", "domain", "medium, far field 60c"),
 "phase34/R80": ("05_phase4_domain", "domain", "medium, far field 80c"),
 "phase34/coarse_l": ("06_phase4_mesh", "mesh (limiter)", "coarse + laplacian limiter"),
 "phase34/base_l": ("06_phase4_mesh", "mesh (limiter)", "medium + laplacian limiter"),
 "phase34/fine_l": ("06_phase4_mesh", "mesh (limiter)", "fine + laplacian limiter"),
 "phase34/xfine_l": ("06_phase4_mesh", "mesh (limiter)", "extra-fine + laplacian limiter (diverged)"),
 "phase34/coarse": ("06_phase4_mesh", "mesh (no limiter)", "coarse, no limiter"),
 "phase34/fine": ("06_phase4_mesh", "mesh (no limiter)", "fine, no limiter (diverged)"),
 "phase34/coarse4000": ("06_phase4_mesh", "mesh at T/4000", "coarse, T/4000"),
 "phase34/fine4000": ("06_phase4_mesh", "mesh at T/4000", "fine, T/4000 (diverged)"),
 "phase34/medium_lim": ("07_phase4_solver_settings", "solver settings", "medium + velocity-gradient limiter"),
 "phase34/medium_outer4": ("07_phase4_solver_settings", "solver settings", "medium + 4 PIMPLE outer loops"),
 "phase34/coarse_lim": ("07_phase4_solver_settings", "solver settings", "coarse + velocity-gradient limiter"),
 "phase34/coarse_outer4": ("07_phase4_solver_settings", "solver settings", "coarse + 4 PIMPLE outer loops"),
 "phase34/fine_lim": ("07_phase4_solver_settings", "solver settings", "fine + velocity-gradient limiter (diverged)"),
 "phase34/fine_outer4": ("07_phase4_solver_settings", "solver settings", "fine + 4 PIMPLE outer loops (diverged)"),
 "phase5/caseI_medium": ("08_phase5_cases", "Case I", "medium, 80c, limiter"),
 "phase5/caseI_fine": ("08_phase5_cases", "Case I", "fine, 80c, limiter"),
 "phase5/caseII_medium": ("08_phase5_cases", "Case II", "medium, 80c, limiter"),
 "phase5/caseII_fine": ("08_phase5_cases", "Case II", "fine, 80c, limiter"),
 "phase5/caseIII_medium": ("08_phase5_cases", "Case III", "medium, 80c, limiter, T/4000"),
 "phase5/caseIII_fine": ("08_phase5_cases", "Case III", "fine, 80c, limiter, T/4000"),
}
SKIP = lambda run, case: (8 if case in ("I", "II") else 4) if run.startswith("phase5") else (2 if run.startswith("phase2b") else 4)

def grab(p, pat, conv=str):
    if not os.path.exists(p): return None
    m = re.search(pat, open(p).read()); return conv(m.group(1)) if m else None

rows = []
for run, (folder, study, desc) in STUDY.items():
    d = os.path.join(SRC, run)
    if not os.path.isdir(d): print("missing", run); continue
    name = run.split("/")[1]
    o = os.path.join(DST, folder, name); os.makedirs(o, exist_ok=True)
    fs = json.load(open(os.path.join(d, "forces_summary.json"))) if os.path.exists(os.path.join(d, "forces_summary.json")) else None
    if fs is None and os.path.exists(os.path.join(d, "progress", "forces_summary.json")):
        fs = json.load(open(os.path.join(d, "progress", "forces_summary.json")))
    mi = json.load(open(os.path.join(d, "mesh_info.json"))) if os.path.exists(os.path.join(d, "mesh_info.json")) else {}
    case = FSTAR.get(round(fs["reference"].get("fstar", 0.14), 2), "I") if fs else "I"
    exitt = open(os.path.join(d, "solver_exit.txt")).read() if os.path.exists(os.path.join(d, "solver_exit.txt")) else ""
    finished = "reached endTime" in exitt
    dt = grab(os.path.join(d, "controlDict"), r"\ndeltaT\s+([\d.eE+-]+);", float)
    lap = grab(os.path.join(d, "fvSchemes"), r"laplacianSchemes\s*\{[^}]*default\s+([^;]+);")
    period = mi.get("period") or (1 / {"I": 0.14, "II": 0.18, "III": 0.06}[case])
    spc = round(period / dt) if dt else None
    cf = os.path.join(d, "coefficients.csv") if os.path.exists(os.path.join(d, "coefficients.csv")) else os.path.join(d, "progress", "coefficients.csv")
    if os.path.exists(cf): shutil.copy(cf, os.path.join(o, "coefficients_time_history.csv"))
    cyc = fs["cycles"] if fs else []
    diverged = (not finished) and (len(cyc) == 0 or any(abs(c["CX"]) > 1e3 for c in cyc))
    if cyc and not diverged:
        with open(os.path.join(o, "per_cycle.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["cycle", "eta_percent", "mean_CP", "mean_CX", "peak_CY", "peak_CM", "lift_timing_deg"])
            for c in cyc: w.writerow([c["cycle"], f"{c['eta']:.4f}", f"{c['CP']:.5f}", f"{c['CX']:.5f}", f"{c['CY_peak']:.5f}", f"{c['CM_peak']:.5f}", f"{c['lift_timing_deg']:.2f}"])
    for f_ in ("forces_summary.md", "forces_summary.json", "mesh_info.json", "controlDict", "fvSchemes", "fvSolution", "dynamicMeshDict",
               "log.checkMesh", "log_tail.txt", "solver_exit.txt", "cycle_loads.png", "force_history.png", "vorticity_latest.png"):
        if os.path.exists(os.path.join(d, f_)): shutil.copy(os.path.join(d, f_), os.path.join(o, f_))
    sk = SKIP(run, case)
    use = [c for c in cyc if c["cycle"] > sk] if not diverged else []
    avg = lambda k: float(np.mean([c[k] for c in use])) if use else None
    tm = (fs or {}).get("timing", {})
    rows.append(dict(run=name, study=study, description=desc, case=case, mesh=mi.get("level"), cells=mi.get("cells"),
                     far_field_c=mi.get("R_far"), steps_per_cycle=spc, laplacian=lap, status="diverged" if diverged else ("finished" if finished else "stopped at time limit"),
                     cycles=len(cyc), averaged_cycles=f"{sk + 1}-{len(cyc)}" if use else "",
                     eta_percent=avg("eta"), eta_last_cycle=cyc[-1]["eta"] if use else None, mean_CX=avg("CX"), peak_CY=avg("CY_peak"),
                     peak_CM=avg("CM_peak"), lift_timing_deg=avg("lift_timing_deg"), s_per_step=tm.get("s_per_step"),
                     min_per_cycle=60 * tm["wall_h_per_cycle"] if tm.get("wall_h_per_cycle") and not diverged else None, max_courant=tm.get("max_courant") if not diverged else None))
os.makedirs(os.path.join(DST, "01_summary_tables"), exist_ok=True)
keys = list(rows[0].keys())
with open(os.path.join(DST, "01_summary_tables", "all_runs_summary.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, keys); w.writeheader()
    for r in rows: w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else ("" if v is None else v)) for k, v in r.items()})
json.dump(rows, open(os.path.join(DST, "01_summary_tables", "all_runs_summary.json"), "w"), indent=1)
print(len(rows), "runs")
for r in rows: print(f"{r['run']:15s} {r['status']:10s} {r['cells']} {r['far_field_c']} {r['steps_per_cycle']} {r['laplacian']!s:28s} eta={r['eta_percent']}")

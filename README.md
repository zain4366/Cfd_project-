# AE-471 CFD course project: overset reproduction of Kinsey & Dumas (2008)

**Team:** Zain Ul Abideen (466576), Ahmed Mukhtar Bukhari (461298). **Pathway B, research paper reproduction.**

We reproduce the power-extraction efficiency of an oscillating NACA 0015 airfoil from
T. Kinsey and G. Dumas, "Parametric Study of an Oscillating Airfoil in a Power-Extraction Regime", *AIAA Journal* 46(6), 1318–1330, 2008, doi:10.2514/1.26253.
Case I: Re = 1100, f\* = fc/U = 0.14, heave amplitude H₀ = c, pitch amplitude θ₀ = 76.33°, pivot at c/3, heave leading pitch by 90°. Published efficiency **η = 33.7 %**; our independent WaterLily (immersed-boundary) result from the FYP is 32.2 %.

Everything runs on **GitHub Actions** with **OpenFOAM (ESI, v2412)** and **gmsh**, using an **overset mesh**: a body-fitted O-grid that moves with the foil, laid over a fixed Cartesian background.

## How the mesh is built

| Part | Tool | Details |
|---|---|---|
| O-grid around the foil | gmsh (Python API) → `gmshToFoam` | Structured, 3 blocks (upper, lower, blunt trailing edge), radius 1.2c around the pivot, first cell 0.002c (medium), one cell thick |
| Background | `blockMesh` (generated) | 24 × 36 chords; uniform fine box x ∈ [−2, 6], y ∈ [−2.8, 2.8] covering every foil position; graded outside (growth 1.1) |
| Joining | `mergeMeshes`, `topoSet`, `setFields` | `zoneID` 0 = background, 1 = O-grid; the O-grid is the cellZone `movingZone` |
| Motion | `tabulated6DoFMotion` | Table from `scripts/make_mesh_inputs.py`: heave h = H₀cos(2πf t), pitch θ = θ₀sin(2πf t) about the pivot, zero at t = 0 |
| Solver | `overPimpleDyMFoam`, laminar, ν = 1/1100 | Inlet U = 1, outlet p = 0, slip top/bottom, moving wall on the foil |

Three mesh levels (background cell 0.045 / 0.030 / 0.020 c, refinement ratio 1.5) are defined in [`scripts/params.py`](scripts/params.py).

## Plan

| Phase | What | Status |
|---|---|---|
| 0 | Install OpenFOAM + gmsh on a runner, run an official overset tutorial | running |
| 1 | Build the three meshes, `checkMesh`, move the mesh through one cycle, check hole cutting | running |
| 2 | Case I, medium mesh, 2 cycles: sensible forces, time per cycle | |
| 3 | Case I baseline, 10 cycles, average the last 6 | |
| 4 | Verification: 3 meshes, 2 time steps, domain check | |
| 5 | Trend cases: Case II and other pitch amplitudes | |
| 6 | Post-processing and report | |

## Where the results are

Each workflow commits its logs, tables and pictures to the **`ci-results`** branch (`phase0/`, `phase1/<level>/`), so they can be read without opening the Actions page. Run locally (Linux with OpenFOAM v2412 and `pip install gmsh`):

```
bash scripts/build_mesh.sh medium run/medium out/medium
bash scripts/motion_test.sh run/medium/main out/medium 200
```

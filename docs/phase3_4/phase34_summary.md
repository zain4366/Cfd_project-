## Phase 3: Case I baseline (medium mesh, T/2000, far field 20c), average of cycles 5-10

| | η % | mean C_X | peak C_Y | peak C_M | lift timing |
|---|---|---|---|---|---|
| cycle 1 | 41.87 | 2.506 | 3.166 | 0.909 | -9.5° |
| cycle 2 | 35.44 | 2.115 | 1.945 | 0.667 | +1.4° |
| cycle 3 | 34.93 | 2.089 | 1.905 | 0.642 | +1.7° |
| cycle 4 | 34.75 | 2.082 | 1.888 | 0.635 | +1.7° |
| cycle 5 | 34.71 | 2.080 | 1.880 | 0.631 | +1.7° |
| cycle 6 | 34.66 | 2.077 | 1.881 | 0.631 | +1.7° |
| cycle 7 | 34.63 | 2.076 | 1.880 | 0.630 | +1.7° |
| cycle 8 | 34.66 | 2.077 | 1.879 | 0.630 | +1.7° |
| cycle 9 | 34.62 | 2.075 | 1.879 | 0.630 | +1.7° |
| cycle 10 | 34.66 | 2.077 | 1.878 | 0.629 | +1.7° |
| **average** | **34.66 ± 0.03** | **2.077** | **1.880** | **0.630** | **+1.7°** |
| Kinsey & Dumas | 33.7 | 2.014 | 1.91 | 0.646 | ≈ 0° |
| WaterLily (FYP) | 32.2 | 2.11 | 1.98 | 0.67 | within 3° |
| difference from K&D | +0.96 points (+2.8 %) | +3.1 % | -1.6 % | -2.5 % | |

## Phase 4: independence studies (each value = average of cycles 5 onward)

### mesh (with limiter)

| run | cells | η % | mean C_X | peak C_Y | peak C_M | s/step | min/cycle | max Courant |
|---|---|---|---|---|---|---|---|---|
| coarse | 14560 | 34.28 | 2.096 | 1.904 | 0.579 | 0.04 | 1.4 | 6.9 |
| medium | 28907 | 34.57 | 2.086 | 1.891 | 0.592 | 0.10 | 3.5 | 10.2 |
| fine | 58696 | 35.07 | 2.096 | 1.918 | 0.581 | 0.36 | 12.0 | 17.7 |
| extra-fine | 120960 | diverged after 77 steps (t/T = 0.04) | | | | | | |

η spread across the 3 converged runs: 0.79 points; change between the last two: +0.50 points (+1.5 %).
GCI from the three finest meshes (coarse_l, base_l, fine_l):
The changes do not shrink with refinement (ratio of successive changes ≥ 1 or sign change), so GCI is not defined; the change between the two finest meshes is the mesh uncertainty.

### mesh (no limiter)

| run | cells | η % | mean C_X | peak C_Y | peak C_M | s/step | min/cycle | max Courant |
|---|---|---|---|---|---|---|---|---|
| coarse | 14560 | 34.55 | 2.094 | 1.896 | 0.605 | 0.05 | 1.5 | 7.4 |
| medium | 28907 | 34.66 | 2.077 | 1.880 | 0.630 | 0.15 | 5.1 | 13.0 |
| fine | 58696 | diverged after 77 steps (t/T = 0.04) | | | | | | |

η spread across the 2 converged runs: 0.11 points; change between the last two: +0.11 points (+0.3 %).

### time step

| run | cells | η % | mean C_X | peak C_Y | peak C_M | s/step | min/cycle | max Courant |
|---|---|---|---|---|---|---|---|---|
| T/1000 | 28907 | diverged after 87 steps (t/T = 0.09) | | | | | | |
| T/2000 | 28907 | 34.66 | 2.077 | 1.880 | 0.630 | 0.15 | 5.1 | 13.0 |
| T/4000 | 28907 | 34.65 | 2.077 | 1.885 | 0.633 | 0.10 | 6.8 | 7.1 |
| T/8000 | 28907 | 34.65 | 2.077 | 1.888 | 0.634 | 0.12 | 15.7 | 4.1 |

η spread across the 3 converged runs: 0.01 points; change between the last two: +0.01 points (+0.0 %).

### domain

| run | cells | η % | mean C_X | peak C_Y | peak C_M | s/step | min/cycle | max Courant |
|---|---|---|---|---|---|---|---|---|
| 12c | 27219 | 35.65 | 2.123 | 1.932 | 0.660 | 0.10 | 3.4 | 13.0 |
| 20c | 28907 | 34.66 | 2.077 | 1.880 | 0.630 | 0.15 | 5.1 | 13.0 |
| 40c | 31228 | 33.83 | 2.040 | 1.844 | 0.605 | 0.12 | 4.0 | 13.0 |
| 60c | 32494 | 33.57 | 2.029 | 1.837 | 0.598 | 0.12 | 3.9 | 13.0 |
| 80c | 33338 | 33.46 | 2.024 | 1.835 | 0.595 | 0.12 | 4.0 | 13.0 |

η spread across the 5 converged runs: 2.18 points; change between the last two: -0.11 points (-0.3 %).

### solver settings

| run | cells | η % | mean C_X | peak C_Y | peak C_M | s/step | min/cycle | max Courant |
|---|---|---|---|---|---|---|---|---|
| 4 outer loops | 28907 | 34.64 | 2.077 | 1.886 | 0.632 | 0.23 | 7.8 | 13.1 |
| gradient limiter | 28907 | 34.68 | 2.079 | 1.882 | 0.631 | 0.11 | 3.8 | 12.8 |
| laplacian limiter | 28907 | 34.57 | 2.086 | 1.891 | 0.592 | 0.10 | 3.5 | 10.2 |
| as baseline | 28907 | 34.66 | 2.077 | 1.880 | 0.630 | 0.15 | 5.1 | 13.0 |

η spread across the 4 converged runs: 0.11 points; change between the last two: +0.09 points (+0.3 %).

### domain: 1/R fit

The far-field cases drift for longer as the domain grows, so the fit uses the last cycle (10) of each run. Fit over R ≥ 20c: **η(R) = 32.95 + 34.1/R** (η in %, R in chords).

| R | η at cycle 10 | fit | difference |
|---|---|---|---|
| 12c | 35.66 | 35.80 | -0.14 |
| 20c | 34.66 | 34.66 | +0.00 |
| 40c | 33.81 | 33.81 | -0.00 |
| 60c | 33.52 | 33.52 | +0.00 |
| 80c | 33.38 | 33.38 | +0.00 |

Extrapolated infinite-domain efficiency: **32.95 %** (Kinsey & Dumas 33.7 %, WaterLily 32.2 %). Domain error at 20c: 1.71 points; at 80c: 0.43 points.


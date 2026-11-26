## Phase 3: Case I baseline (medium mesh, T/2000, far field 20c), average of cycles 5-10

| | η % | mean C_X | peak C_Y | peak C_M | lift timing |
|---|---|---|---|---|---|
| cycle 1 | 42.29 | 2.506 | 2.944 | 0.912 | -8.1° |
| cycle 2 | 35.57 | 2.120 | 1.956 | 0.670 | +1.4° |
| cycle 3 | 35.00 | 2.092 | 1.915 | 0.645 | +1.8° |
| cycle 4 | 34.87 | 2.087 | 1.897 | 0.638 | +1.7° |
| cycle 5 | 34.79 | 2.083 | 1.891 | 0.634 | +1.7° |
| cycle 6 | 34.76 | 2.082 | 1.889 | 0.633 | +1.7° |
| cycle 7 | 34.75 | 2.081 | 1.888 | 0.633 | +1.7° |
| cycle 8 | 34.74 | 2.081 | 1.888 | 0.632 | +1.7° |
| cycle 9 | 34.74 | 2.081 | 1.888 | 0.632 | +1.7° |
| cycle 10 | 34.74 | 2.080 | 1.888 | 0.632 | +1.7° |
| **average** | **34.75 ± 0.02** | **2.081** | **1.889** | **0.633** | **+1.7°** |
| Kinsey & Dumas | 33.7 | 2.014 | 1.91 | 0.646 | ≈ 0° |
| WaterLily (FYP) | 32.2 | 2.11 | 1.98 | 0.67 | within 3° |
| difference from K&D | +1.05 points (+3.1 %) | +3.3 % | -1.1 % | -2.0 % | |

## Phase 4: independence studies (each value = average of cycles 5 onward)

### mesh (with limiter)

| run | cells | η % | mean C_X | peak C_Y | peak C_M | s/step | min/cycle | max Courant |
|---|---|---|---|---|---|---|---|---|
| coarse | | not run | | | | | | |
| medium | | not run | | | | | | |
| fine | | not run | | | | | | |

### mesh (no limiter)

| run | cells | η % | mean C_X | peak C_Y | peak C_M | s/step | min/cycle | max Courant |
|---|---|---|---|---|---|---|---|---|
| coarse | 14560 | 34.65 | 2.098 | 1.899 | 0.608 | 0.05 | 1.5 | 7.4 |
| medium | 28907 | 34.75 | 2.081 | 1.889 | 0.633 | 0.15 | 5.1 | 13.0 |
| fine | 58696 | diverged after 77 steps (t/T = 0.04) | | | | | | |

η spread across the 2 converged runs: 0.10 points; change between the last two: +0.10 points (+0.3 %).

### time step

| run | cells | η % | mean C_X | peak C_Y | peak C_M | s/step | min/cycle | max Courant |
|---|---|---|---|---|---|---|---|---|
| T/1000 | 28907 | diverged after 87 steps (t/T = 0.09) | | | | | | |
| T/2000 | 28907 | 34.75 | 2.081 | 1.889 | 0.633 | 0.15 | 5.1 | 13.0 |
| T/4000 | 28907 | 34.74 | 2.081 | 1.894 | 0.636 | 0.10 | 6.8 | 7.1 |
| T/8000 | | not run | | | | | | |

η spread across the 2 converged runs: 0.02 points; change between the last two: -0.02 points (-0.0 %).

### domain

| run | cells | η % | mean C_X | peak C_Y | peak C_M | s/step | min/cycle | max Courant |
|---|---|---|---|---|---|---|---|---|
| 12c | 27219 | 35.74 | 2.127 | 1.942 | 0.662 | 0.10 | 3.4 | 13.0 |
| 20c | 28907 | 34.75 | 2.081 | 1.889 | 0.633 | 0.15 | 5.1 | 13.0 |
| 40c | 31228 | 33.92 | 2.044 | 1.847 | 0.608 | 0.12 | 4.0 | 13.0 |
| 60c | | not run | | | | | | |
| 80c | | not run | | | | | | |

η spread across the 3 converged runs: 1.82 points; change between the last two: -0.83 points (-2.4 %).

### solver settings

| run | cells | η % | mean C_X | peak C_Y | peak C_M | s/step | min/cycle | max Courant |
|---|---|---|---|---|---|---|---|---|
| 4 outer loops | | not run | | | | | | |
| gradient limiter | 28907 | 34.78 | 2.083 | 1.891 | 0.634 | 0.11 | 3.8 | 12.8 |
| laplacian limiter | | not run | | | | | | |
| as baseline | 28907 | 34.75 | 2.081 | 1.889 | 0.633 | 0.15 | 5.1 | 13.0 |

η spread across the 2 converged runs: 0.02 points; change between the last two: -0.02 points (-0.1 %).


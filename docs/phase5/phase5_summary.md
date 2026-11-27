## Phase 5: Kinsey & Dumas Table 2 cases, far field 80c, laplacian limiter

| Case | f*, θ₀ | Source | Cycles averaged | η % | mean C_X | peak C_Y | peak C_M | lift timing |
|---|---|---|---|---|---|---|---|---|
| I | 0.14, 76.33° | OpenFOAM medium (33,338 cells) | 9-14 | 33.38 | 2.033 | 1.856 | 0.559 | -1° |
| I | 0.14, 76.33° | OpenFOAM fine (65,395 cells) | 9-14 | 33.77 | 2.040 | 1.872 | 0.541 | -0° |
| I | 0.14, 76.33° | **Kinsey & Dumas** | | **33.7** | 2.014 | 1.91 | 0.646 | |
| I | 0.14, 76.33° | WaterLily (FYP) | | 32.2 | 2.11 | 1.98 | 0.67 | |
| II | 0.18, 60° | OpenFOAM medium (33,338 cells) | 9-16 | 11.54 | 0.708 | 1.291 | 0.299 | -54° |
| II | 0.18, 60° | OpenFOAM fine (65,395 cells) | 9-16 | 11.23 | 0.724 | 1.298 | 0.305 | -55° |
| II | 0.18, 60° | **Kinsey & Dumas** | | **11.4** | 0.69 | 1.256 | 0.299 | |
| II | 0.18, 60° | WaterLily (FYP) | | 15.2 | 0.691 | 1.299 | 0.234 | |
| III | 0.06, 60° | OpenFOAM medium (33,338 cells) | 5-8 | 12.21 | 1.252 | 2.033 | 0.567 | -22° |
| III | 0.06, 60° | OpenFOAM fine (65,395 cells) | 5-8 | 12.39 | 1.257 | 2.053 | 0.577 | -22° |
| III | 0.06, 60° | **Kinsey & Dumas** | | **12.3** | 1.256 | 2.03 | 0.597 | |

### Difference from Kinsey & Dumas

| Case | Mesh | η (points) | η (%) | mean C_X | peak C_Y | peak C_M |
|---|---|---|---|---|---|---|
| I | medium | -0.32 | -1.0 % | +0.9 % | -2.8 % | -13.5 % |
| I | fine | +0.07 | +0.2 % | +1.3 % | -2.0 % | -16.3 % |
| II | medium | +0.14 | +1.2 % | +2.6 % | +2.8 % | +0.0 % |
| II | fine | -0.17 | -1.5 % | +5.0 % | +3.3 % | +2.0 % |
| III | medium | -0.09 | -0.7 % | -0.3 % | +0.2 % | -5.0 % |
| III | fine | +0.09 | +0.8 % | +0.0 % | +1.1 % | -3.4 % |

Case I domain correction (Phase 4 slope 34.1/R at 80c = 0.43 points): medium 32.95 %, fine 33.35 % for an infinite domain (Kinsey & Dumas 33.7 %). The slope was measured for Case I only; Cases II and III are reported at 80c.

Cycle-to-cycle spread of η over the averaged cycles: Case I medium 0.03, Case I fine 0.06, Case II medium 0.01, Case II fine 0.02, Case III medium 0.00, Case III fine 0.02 points.

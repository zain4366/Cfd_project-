## Phase 5: Kinsey & Dumas Table 2 cases, far field 80c, laplacian limiter

| Case | f*, θ₀ | Source | Cycles averaged | η % | mean C_X | peak C_Y | peak C_M | lift timing |
|---|---|---|---|---|---|---|---|---|
| I | 0.14, 76.33° | OpenFOAM medium (33,338 cells) | 9-14 | 33.28 | 2.029 | 1.852 | 0.557 | -1° |
| I | 0.14, 76.33° | OpenFOAM fine (65,395 cells) | 9-14 | 33.67 | 2.037 | 1.870 | 0.537 | -0° |
| I | 0.14, 76.33° | **Kinsey & Dumas** | | **33.7** | 2.014 | 1.91 | 0.646 | |
| I | 0.14, 76.33° | WaterLily (FYP) | | 32.2 | 2.11 | 1.98 | 0.67 | |
| II | 0.18, 60° | OpenFOAM medium (33,338 cells) | 9-16 | 11.20 | 0.700 | 1.282 | 0.302 | -54° |
| II | 0.18, 60° | OpenFOAM fine (65,395 cells) | 9-16 | 10.90 | 0.716 | 1.288 | 0.308 | -55° |
| II | 0.18, 60° | **Kinsey & Dumas** | | **11.4** | 0.69 | 1.256 | 0.299 | |
| II | 0.18, 60° | WaterLily (FYP) | | 15.2 | 0.691 | 1.299 | 0.234 | |
| III | 0.06, 60° | OpenFOAM medium (33,338 cells) | 5-8 | 12.20 | 1.251 | 2.032 | 0.566 | -22° |
| III | 0.06, 60° | OpenFOAM fine (65,395 cells) | 5-8 | 12.38 | 1.256 | 2.052 | 0.576 | -22° |
| III | 0.06, 60° | **Kinsey & Dumas** | | **12.3** | 1.256 | 2.03 | 0.597 | |

### Difference from Kinsey & Dumas

| Case | Mesh | η (points) | η (%) | mean C_X | peak C_Y | peak C_M |
|---|---|---|---|---|---|---|
| I | medium | -0.42 | -1.2 % | +0.7 % | -3.0 % | -13.8 % |
| I | fine | -0.03 | -0.1 % | +1.1 % | -2.1 % | -16.8 % |
| II | medium | -0.20 | -1.7 % | +1.4 % | +2.1 % | +1.1 % |
| II | fine | -0.50 | -4.4 % | +3.8 % | +2.5 % | +3.0 % |
| III | medium | -0.10 | -0.8 % | -0.4 % | +0.1 % | -5.3 % |
| III | fine | +0.08 | +0.7 % | -0.0 % | +1.1 % | -3.5 % |

Case I domain correction (Phase 4 slope 34.1/R at 80c = 0.43 points): medium 32.85 %, fine 33.24 % for an infinite domain (Kinsey & Dumas 33.7 %). The slope was measured for Case I only; Cases II and III are reported at 80c.

Cycle-to-cycle spread of η over the averaged cycles: Case I medium 0.06, Case I fine 0.05, Case II medium 0.02, Case II fine 0.01, Case III medium 0.01, Case III fine 0.01 points.

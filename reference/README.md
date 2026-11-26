# Reference data

- `kinsey_dumas_2008_caseI.json`: published Case I values from Kinsey & Dumas (2008), *AIAA J.* 46(6), 1318–1330 (efficiency, mean drag coefficient, peak lift and moment coefficients). The PDF is not stored here (copyright).
- `waterlily_caseI_c64_cycle.csv`: our own independent result from the FYP (WaterLily.jl immersed-boundary solver, 64 cells/chord, average of 6 cycles): one cycle of C_X, C_Y, C_M (about the pivot) and C_P against t/T, with t = 0 at the top of the stroke (same convention as here). Its efficiency is 32.2 %.
- `kinsey_dumas_2008_cases.json`: Kinsey & Dumas Table 2 values (72 000 cells, 2 000 steps per cycle) for Case I (f* 0.14, θ₀ 76.33°), Case II (f* 0.18, θ₀ 60°) and Case III (f* 0.06, θ₀ 60°), with the FYP WaterLily values where they exist. Scripts pick the case from the environment variable `KD_CASE` (default I).
- `waterlily_caseII_c64_cycle.csv`: the FYP WaterLily Case II cycle (64 cells/chord). WaterLily's Case II efficiency (15.2 %) is well above the paper's 11.4 %, a discrepancy the FYP never resolved; Phase 5 gives an independent check.

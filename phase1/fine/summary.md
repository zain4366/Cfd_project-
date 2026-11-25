## Mesh level: fine

- background cells 177072, O-grid cells 38918, total 215990
- background cell 0.02 c, foil points per side 158, radial cells 122, first wall cell 0.0013 c

| checkMesh | cells | result | max non-orthogonality | max skewness | max aspect ratio |
|---|---|---|---|---|---|
| O-grid | 38918 | Mesh OK | 61.82852622 | 1.009866969 | 6.486409481 |
| background | 177072 | Mesh OK | 0 | 2.630304572e-13 | 69.20372798 |
| merged | 215990 | Mesh OK | 61.82852622 | 1.009866969 | 69.20372798 |

**motion_timing.txt**
```
moveDynamicMesh: 200 steps in 852 s
```

**orphans.txt**
```
no line mentioning orphans in the log
```

**Overset cell types during the cycle**

| t/T | calculated | interpolated | hole |
|---|---|---|---|
| 0.0000 | no cellTypes field written | | |
| 0.125 | 215219 | 413 | 358 |
| 0.250 | 215226 | 426 | 338 |
| 0.375 | 215203 | 426 | 361 |
| 0.500 | 215234 | 428 | 328 |
| 0.625 | 215220 | 413 | 357 |
| 0.750 | 215226 | 426 | 338 |
| 0.875 | 215203 | 426 | 361 |
| 1.000 | 215234 | 428 | 328 |


## Mesh level: medium

- background cells 90514, O-grid cells 17091, total 107605
- background cell 0.03 c, foil points per side 105, radial cells 81, first wall cell 0.002 c

| checkMesh | cells | result | max non-orthogonality | max skewness | max aspect ratio |
|---|---|---|---|---|---|
| O-grid | 17091 | Mesh OK | 61.51965399 | 1.07589234 | 7.280151426 |
| background | 90514 | Mesh OK | 0 | 1.791648568e-13 | 46.16640689 |
| merged | 107605 | Mesh OK | 61.51965399 | 1.07589234 | 46.16640689 |

**motion_timing.txt**
```
moveDynamicMesh: 200 steps in 420 s
```

**orphans.txt**
```
no line mentioning orphans in the log
```

**Overset cell types during the cycle**

| t/T | calculated | interpolated | hole |
|---|---|---|---|
| 0.0000 | no cellTypes field written | | |
| 0.125 | 107150 | 273 | 182 |
| 0.250 | 107150 | 284 | 171 |
| 0.375 | 107149 | 277 | 179 |
| 0.500 | 107149 | 287 | 169 |
| 0.625 | 107150 | 273 | 182 |
| 0.750 | 107150 | 284 | 171 |
| 0.875 | 107149 | 277 | 179 |
| 1.000 | 107149 | 287 | 169 |


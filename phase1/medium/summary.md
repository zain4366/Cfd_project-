## Mesh level: medium

- background cells 90514, O-grid cells 17091, total 107605
- background cell 0.03 c, foil points per side 105, radial cells 81, first wall cell 0.002 c

| checkMesh | cells | result | max non-orthogonality | max skewness | max aspect ratio |
|---|---|---|---|---|---|
| O-grid | 17091 | Mesh OK | 61.51965399 | 1.07589234 | 150.7749273 |
| background | 90514 | Mesh OK | 0 | 1.791648568e-13 | 46.16640689 |
| merged | 107605 | Mesh OK | 61.51965399 | 1.07589234 | 46.16640689 |

**motion_timing.txt**
```
moveDynamicMesh: 200 steps in 559 s
```

**orphans.txt**
```
no line mentioning orphans in the log
```

**Overset cell types during the cycle**

| t/T | calculated | interpolated | hole |
|---|---|---|---|
| 0.0000 | no cellTypes field written | | |
| 0.125 | 16880 | 10 | 90507 |
| 0.250 | 16880 | 5 | 90509 |
| 0.375 | 16880 | 14 | 90504 |
| 0.500 | 16880 | 5 | 90510 |
| 0.625 | 16880 | 10 | 90507 |
| 0.750 | 16880 | 5 | 90509 |
| 0.875 | 16880 | 14 | 90504 |
| 1.000 | 16880 | 5 | 90510 |


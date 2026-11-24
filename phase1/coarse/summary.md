## Mesh level: coarse

- background cells 47600, O-grid cells 7560, total 55160
- background cell 0.045 c, foil points per side 70, radial cells 54, first wall cell 0.003 c

| checkMesh | cells | result | max non-orthogonality | max skewness | max aspect ratio |
|---|---|---|---|---|---|
| O-grid | 7560 | Mesh OK | 61.08115403 | 1.137997768 | 97.34255232 |
| background | 47600 | Mesh OK | 0 | 1.578986033e-13 | 30.83328698 |
| merged | 55160 | Mesh OK | 61.08115403 | 1.137997768 | 30.83328698 |

**motion_timing.txt**
```
moveDynamicMesh: 200 steps in 199 s
```

**orphans.txt**
```
no line mentioning orphans in the log
```

**Overset cell types during the cycle**

| t/T | calculated | interpolated | hole |
|---|---|---|---|
| 0.0000 | no cellTypes field written | | |
| 0.125 | 7420 | 3 | 47598 |
| 0.250 | 7420 | 3 | 47598 |
| 0.375 | 7420 | 8 | 47594 |
| 0.500 | 7420 | 1 | 47599 |
| 0.625 | 7420 | 3 | 47598 |
| 0.750 | 7420 | 3 | 47598 |
| 0.875 | 7420 | 8 | 47594 |
| 1.000 | 7420 | 1 | 47599 |


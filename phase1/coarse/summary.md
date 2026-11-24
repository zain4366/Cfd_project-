## Mesh level: coarse

- background cells 47600, O-grid cells 7560, total 55160
- background cell 0.045 c, foil points per side 70, radial cells 54, first wall cell 0.003 c

| checkMesh | cells | result | max non-orthogonality | max skewness | max aspect ratio |
|---|---|---|---|---|---|
| O-grid | 7560 | Mesh OK | 61.08115403 | 1.137997768 | 5.175229378 |
| background | 47600 | Mesh OK | 0 | 1.578986033e-13 | 30.83328698 |
| merged | 55160 | Mesh OK | 61.08115403 | 1.137997768 | 30.83328698 |

**motion_timing.txt**
```
moveDynamicMesh: 200 steps in 109 s
```

**orphans.txt**
```
no line mentioning orphans in the log
```

**Overset cell types during the cycle**

| t/T | calculated | interpolated | hole |
|---|---|---|---|
| 0.0000 | no cellTypes field written | | |
| 0.125 | 54883 | 184 | 93 |
| 0.250 | 54881 | 190 | 89 |
| 0.375 | 54882 | 184 | 94 |
| 0.500 | 54886 | 192 | 82 |
| 0.625 | 54883 | 184 | 93 |
| 0.750 | 54881 | 190 | 89 |
| 0.875 | 54882 | 184 | 94 |
| 1.000 | 54886 | 192 | 82 |


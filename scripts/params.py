"""Single source of truth for geometry, kinematics and mesh levels (units: c = 1, U = 1)."""
import math

# ---- Kinsey & Dumas (2008) Case I, same convention as the FYP WaterLily code (kd_core.jl)
RE      = 1100.0
NU      = 1.0 / RE
FSTAR   = 0.14                  # f c / U
THETA0  = 76.33                 # pitch amplitude, deg (positive = counter-clockwise = nose down)
H0      = 1.0                   # heave amplitude / c
XP      = 1.0 / 3.0             # pivot from leading edge / c
THICK   = 0.15                  # NACA 0015, open trailing edge (coefficient -0.1015, as in kd_core.jl)
PERIOD  = 1.0 / FSTAR           # T = c / (f* U)
# heave h(t) = H0 cos(2 pi f t)   (heave leads pitch by 90 deg)
# pitch th(t) = THETA0 sin(2 pi f t)
# At t = 0 the foil is at the top (h = H0) with zero pitch: the component mesh is built there,
# so the tabulated motion is zero at t = 0 (no jump at the start).

# ---- component (O-grid) and background
R_OSET  = 1.2                   # radius of the overset O-grid, centred on the pivot
ZTHICK  = 0.1                   # 2D: one cell in z for both meshes
DOMAIN  = dict(x0=-6.0, x1=18.0, y0=-18.0, y1=18.0)       # 24 x 36 chords (36 tall as in the FYP domain check)
INNER   = dict(x0=-2.0, x1=6.0, y0=-2.8, y1=2.8)          # uniform fine box: covers the O-grid at every heave position + near wake
GROWTH  = 1.10                  # background cell growth outside the fine box

LEVELS = {
    #          background cell  points per foil side  TE points  first wall cell
    "coarse": dict(h=0.045, ns=70,  nte=3, a=0.0030),
    "medium": dict(h=0.030, ns=105, nte=4, a=0.0020),
    "fine":   dict(h=0.020, ns=158, nte=6, a=0.0013),
}

def omega():
    return 2 * math.pi * FSTAR

def heave(t):
    return H0 * math.cos(omega() * t)

def pitch_deg(t):
    return THETA0 * math.sin(omega() * t)

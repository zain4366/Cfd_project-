"""Generate everything the overset mesh needs for one refinement level.

    python3 scripts/make_mesh_inputs.py --level medium --case run/medium/main --comp run/medium/component.msh --figs out/medium

Writes
  <case>/system/blockMeshDict   background Cartesian mesh (fine uniform box + graded far field)
  <case>/constant/motion.dat    tabulated heave + pitch (tabulated6DoFMotion), zero at t = 0
  <comp>                        gmsh O-grid around the NACA 0015 (msh 2.2, one cell thick), if gmsh is installed
  <figs>/*.png                  pictures of both meshes
"""
import argparse, json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import params as P

HEADER = """FoamFile
{{
    version     2.0;
    format      ascii;
    class       {cls};
    object      {obj};
}}
"""


# ----------------------------------------------------------------- helpers
def progression(a, L, N):
    """ratio q such that N cells starting at size a fill length L"""
    lo, hi = 1.0 + 1e-9, 3.0
    for _ in range(200):
        q = 0.5 * (lo + hi)
        s = a * (q**N - 1) / (q - 1)
        lo, hi = (q, hi) if s < L else (lo, q)
    return q


def graded(L, h, r):
    """cells and total expansion for a block of length L whose first cell is h, growing at r"""
    n = max(1, math.ceil(math.log(1 + L * (r - 1) / h) / math.log(r)))
    # rescale r so the block is filled exactly with n cells starting at h
    q = progression(h, L, n) if n > 1 else 1.0
    return n, q ** (n - 1), q


def naca_half_thickness(x, t=P.THICK):
    return 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1015 * x**4)


# ----------------------------------------------------------------- background
def background(case, lev):
    D, I, h, r = P.DOMAIN, P.INNER, lev["h"], P.GROWTH
    def axis(a0, i0, i1, a1):
        nl, el, ql = graded(i0 - a0, h, r)          # cells shrink towards the fine box
        nm = round((i1 - i0) / h)
        nr, er, qr = graded(a1 - i1, h, r)
        nodes = [i0 - h * (ql**k - 1) / (ql - 1) if ql > 1 else i0 - h * k for k in range(nl + 1)][::-1]
        nodes += list(np.linspace(i0, i1, nm + 1))[1:]
        nodes += [i1 + h * (qr**k - 1) / (qr - 1) if qr > 1 else i1 + h * k for k in range(1, nr + 1)]
        return [a0, i0, i1, a1], [nl, nm, nr], [1.0 / el, 1.0, er], np.array(nodes)
    X, NX, GX, xn = axis(D["x0"], I["x0"], I["x1"], D["x1"])
    Y, NY, GY, yn = axis(D["y0"], I["y0"], I["y1"], D["y1"])
    vid = lambda i, j, k: k * 16 + j * 4 + i
    verts = [f"    ({X[i]:.6g} {Y[j]:.6g} {[0, P.ZTHICK][k]:.6g})" for k in range(2) for j in range(4) for i in range(4)]
    blocks = []
    for j in range(3):
        for i in range(3):
            v = [vid(i, j, 0), vid(i + 1, j, 0), vid(i + 1, j + 1, 0), vid(i, j + 1, 0),
                 vid(i, j, 1), vid(i + 1, j, 1), vid(i + 1, j + 1, 1), vid(i, j + 1, 1)]
            blocks.append(f"    hex ({' '.join(map(str, v))}) ({NX[i]} {NY[j]} 1) simpleGrading ({GX[i]:.6g} {GY[j]:.6g} 1)")
    def faces(kind):
        out = []
        for m in range(3):
            if kind == "inlet":  out.append((vid(0, m, 0), vid(0, m, 1), vid(0, m + 1, 1), vid(0, m + 1, 0)))
            if kind == "outlet": out.append((vid(3, m, 0), vid(3, m + 1, 0), vid(3, m + 1, 1), vid(3, m, 1)))
            if kind == "bottom": out.append((vid(m, 0, 0), vid(m + 1, 0, 0), vid(m + 1, 0, 1), vid(m, 0, 1)))
            if kind == "top":    out.append((vid(m, 3, 0), vid(m, 3, 1), vid(m + 1, 3, 1), vid(m + 1, 3, 0)))
        if kind == "frontAndBack":
            for j in range(3):
                for i in range(3):
                    out.append((vid(i, j, 0), vid(i, j + 1, 0), vid(i + 1, j + 1, 0), vid(i + 1, j, 0)))
                    out.append((vid(i, j, 1), vid(i + 1, j, 1), vid(i + 1, j + 1, 1), vid(i, j + 1, 1)))
        return "\n".join(f"            ({' '.join(map(str, f))})" for f in out)
    ptype = dict(inlet="patch", outlet="patch", top="patch", bottom="patch", frontAndBack="empty")
    bnd = "\n".join(f"    {n}\n    {{\n        type {t};\n        faces\n        (\n{faces(n)}\n        );\n    }}" for n, t in ptype.items())
    txt = (HEADER.format(cls="dictionary", obj="blockMeshDict") + "\nscale 1;\n\nvertices\n(\n" + "\n".join(verts) +
           "\n);\n\nblocks\n(\n" + "\n".join(blocks) + "\n);\n\nedges ();\n\nboundary\n(\n" + bnd + "\n);\n")
    os.makedirs(os.path.join(case, "system"), exist_ok=True)
    open(os.path.join(case, "system", "blockMeshDict"), "w").write(txt)
    return xn, yn, sum(NX) * sum(NY)


# ----------------------------------------------------------------- motion table
def motion(case, cycles=14, per_cycle=400):
    n = cycles * per_cycle + 1
    lines = []
    for k in range(n):
        t = k * P.PERIOD / per_cycle
        lines.append(f"({t:.8g} ((0 {P.heave(t) - P.H0:.10g} 0) (0 0 {P.pitch_deg(t):.10g})))")
    os.makedirs(os.path.join(case, "constant"), exist_ok=True)
    open(os.path.join(case, "constant", "motion.dat"), "w").write(f"{n}\n(\n" + "\n".join(lines) + "\n)\n")


# ----------------------------------------------------------------- component O-grid
def component(path, lev, figs, R=None, outer="overset", dang_deg=8.0, nr=None, far=None, far_growth=1.07):
    import gmsh
    R = R or P.R_OSET
    yc = P.H0                                   # O-grid centred on the pivot, built at the t = 0 position (top, zero pitch)
    xs = (1 - np.cos(np.linspace(0, np.pi, 241))) / 2
    yt = naca_half_thickness(xs)
    N_r = nr
    for N in ([] if nr else range(10, 400)):    # overset: radial cells chosen so the outer cell ~ background cell
        q = progression(lev["a"], R - P.XP, N)
        if lev["a"] * q ** (N - 1) <= 1.05 * lev["h"]:
            N_r = N; break
    gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 1); gmsh.model.add("foil")
    g = gmsh.model.geo
    LE = g.addPoint(-P.XP, yc, 0)
    pu = [LE] + [g.addPoint(x - P.XP, yc + y, 0) for x, y in zip(xs[1:], yt[1:])]
    pl = [LE] + [g.addPoint(x - P.XP, yc - y, 0) for x, y in zip(xs[1:], yt[1:])]
    TEu, TEl = pu[-1], pl[-1]
    C0 = g.addPoint(0, yc, 0)
    dang = math.radians(dang_deg)       # half-angle of the far end of the trailing-edge block
    Cu = g.addPoint(R * math.cos(dang), yc + R * math.sin(dang), 0)
    Cd = g.addPoint(R * math.cos(dang), yc - R * math.sin(dang), 0)
    Cl = g.addPoint(-R, yc, 0)
    sU, sL = g.addSpline(pu), g.addSpline(pl)                    # LE -> TE upper / lower
    te = g.addLine(TEl, TEu)                                     # blunt trailing edge
    aU, aL, aT = g.addCircleArc(Cu, C0, Cl), g.addCircleArc(Cd, C0, Cl), g.addCircleArc(Cd, C0, Cu)
    lTEu, lTEl, lLE = g.addLine(TEu, Cu), g.addLine(TEl, Cd), g.addLine(LE, Cl)   # radial lines, airfoil -> circle
    loops = {
        "upper": [sU, lTEu, aU, -lLE],
        "lower": [lLE, -aL, -lTEl, -sL],
        "te":    [lTEl, aT, -lTEu, -te],
    }
    corners = {"upper": [LE, TEu, Cu, Cl], "lower": [LE, Cl, Cd, TEl], "te": [TEl, Cd, Cu, TEu]}
    surf = {k: g.addPlaneSurface([g.addCurveLoop(v)]) for k, v in loops.items()}
    m = g.mesh
    for c in (sU, sL, aU, aL):
        m.setTransfiniteCurve(c, lev["ns"], "Bump", 0.25)
    for c in (te, aT):
        m.setTransfiniteCurve(c, lev["nte"])
    for c, L in ((lTEu, R - (1 - P.XP)), (lTEl, R - (1 - P.XP)), (lLE, R - P.XP)):
        m.setTransfiniteCurve(c, N_r + 1, "Progression", progression(lev["a"], L, N_r))
    for k, s in surf.items():
        m.setTransfiniteSurface(s, cornerTags=corners[k]); m.setRecombine(2, s)
    order = ["upper", "lower", "te"]
    far_arcs = ()
    if far:                                     # rigid mesh: polar ring from the O-grid circle out to the far field
        Fu = g.addPoint(far * math.cos(dang), yc + far * math.sin(dang), 0)
        Fd = g.addPoint(far * math.cos(dang), yc - far * math.sin(dang), 0)
        Fl = g.addPoint(-far, yc, 0)
        FU, FL, FT = g.addCircleArc(Fu, C0, Fl), g.addCircleArc(Fd, C0, Fl), g.addCircleArc(Fd, C0, Fu)
        rU, rD, rL = g.addLine(Cu, Fu), g.addLine(Cd, Fd), g.addLine(Cl, Fl)
        far_arcs = (FU, FL, FT)
        h_in = lev["a"] * progression(lev["a"], R - P.XP, N_r) ** (N_r - 1)        # last radial cell of the inner ring
        n_out = max(4, math.ceil(math.log(1 + (far - R) * (far_growth - 1) / h_in) / math.log(far_growth)))
        loops.update({"outer_upper": [rU, FU, -rL, -aU], "outer_lower": [rL, -FL, -rD, aL], "outer_te": [rD, FT, -rU, -aT]})
        corners.update({"outer_upper": [Cu, Fu, Fl, Cl], "outer_lower": [Cl, Fl, Fd, Cd], "outer_te": [Cd, Fd, Fu, Cu]})
        for k in ("outer_upper", "outer_lower", "outer_te"):
            surf[k] = g.addPlaneSurface([g.addCurveLoop(loops[k])])
        for c in (FU, FL):
            m.setTransfiniteCurve(c, lev["ns"], "Bump", 0.25)       # same angular distribution as the inner arcs: radial lines
        m.setTransfiniteCurve(FT, lev["nte"])
        for c in (rU, rD, rL):
            m.setTransfiniteCurve(c, n_out + 1, "Progression", progression(h_in, far - R, n_out))
        for k in ("outer_upper", "outer_lower", "outer_te"):
            m.setTransfiniteSurface(surf[k], cornerTags=corners[k]); m.setRecombine(2, surf[k])
        order += ["outer_upper", "outer_lower", "outer_te"]
    ext = g.extrude([(2, surf[k]) for k in order], 0, 0, P.ZTHICK, numElements=[1], recombine=True)
    g.synchronize()
    tops, vols, foil, oset = [], [], [], []
    for i, k in enumerate(order):
        top, vol, lat = ext[6 * i], ext[6 * i + 1], ext[6 * i + 2:6 * i + 6]
        assert top[0] == 2 and vol[0] == 3, ext
        tops.append(top[1]); vols.append(vol[1])
        for crv, lt in zip(loops[k], lat):
            if abs(crv) in (sU, sL, te): foil.append(lt[1])
            if abs(crv) in (far_arcs or (aU, aL, aT)): oset.append(lt[1])
    # sanity: every foil face lies on the airfoil, every overset face on the circle
    for s in foil:
        b = gmsh.model.getBoundingBox(2, s); assert b[0] > -P.XP - 1e-6 and b[3] < 1 - P.XP + 1e-6, ("foil", s, b)
    for s in oset:
        b = gmsh.model.getBoundingBox(2, s); assert max(abs(b[0]), abs(b[3])) > 0.9 * (far or R) * math.cos(dang), (outer, s, b)
    gmsh.model.addPhysicalGroup(2, sorted(set(foil)), name="foil")
    gmsh.model.addPhysicalGroup(2, sorted(set(oset)), name=outer)
    gmsh.model.addPhysicalGroup(2, [surf[k] for k in order] + tops, name="frontAndBack")
    gmsh.model.addPhysicalGroup(3, vols, name="component")
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.removeDuplicateNodes()
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.write(path)
    # ---- picture data: quads of the z = 0 faces
    quads = []
    for k in order:
        et, _, nt = gmsh.model.mesh.getElements(2, surf[k])
        tags, coords, _ = gmsh.model.mesh.getNodes(2, surf[k], includeBoundary=True)
        xy = {t: (coords[3 * i], coords[3 * i + 1]) for i, t in enumerate(tags)}
        for typ, conn in zip(et, nt):
            npe = 4 if typ == 3 else 3
            for e in range(len(conn) // npe):
                quads.append([xy[n] for n in conn[npe * e:npe * e + npe]])
    ncells = len(quads)
    gmsh.finalize()
    return quads, N_r, ncells


# ----------------------------------------------------------------- figures
def figures(figs, xn, yn, quads, lev_name):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    os.makedirs(figs, exist_ok=True)
    def bg(ax, lw=0.25):
        for x in xn: ax.plot([x, x], [yn[0], yn[-1]], color="0.75", lw=lw)
        for y in yn: ax.plot([xn[0], xn[-1]], [y, y], color="0.75", lw=lw)
    # 1. whole domain (background only, every 2nd line)
    fig, ax = plt.subplots(figsize=(9, 6.5), dpi=150)
    for x in xn[::2]: ax.plot([x, x], [yn[0], yn[-1]], color="0.6", lw=0.2)
    for y in yn[::2]: ax.plot([xn[0], xn[-1]], [y, y], color="0.6", lw=0.2)
    ax.add_patch(plt.Circle((0, P.H0), P.R_OSET, fill=False, color="C3", lw=1))
    ax.set_aspect("equal"); ax.set_title(f"{lev_name}: background mesh (every 2nd line) and O-grid outline"); ax.set_xlabel("x/c"); ax.set_ylabel("y/c")
    fig.tight_layout(); fig.savefig(os.path.join(figs, "mesh_domain.png")); plt.close(fig)
    if quads is None:
        return
    # 2. overlap region at t = 0
    fig, ax = plt.subplots(figsize=(9, 6), dpi=170)
    bg(ax); ax.add_collection(PolyCollection(quads, facecolor="none", edgecolor="C0", lw=0.25))
    ax.set_xlim(-2.2, 2.2); ax.set_ylim(-0.6, 2.6); ax.set_aspect("equal")
    ax.set_title(f"{lev_name}: O-grid (blue) over the background (grey) at t = 0"); fig.tight_layout()
    fig.savefig(os.path.join(figs, "mesh_overlap.png")); plt.close(fig)
    # 3. leading and trailing edge close-ups
    fig, axs = plt.subplots(1, 2, figsize=(11, 5), dpi=170)
    for ax, (cx, w, t) in zip(axs, [(-P.XP, 0.12, "leading edge"), (1 - P.XP, 0.06, "trailing edge")]):
        ax.add_collection(PolyCollection(quads, facecolor="none", edgecolor="C0", lw=0.3))
        ax.set_xlim(cx - w, cx + w); ax.set_ylim(P.H0 - w, P.H0 + w); ax.set_aspect("equal"); ax.set_title(f"{lev_name}: {t}")
    fig.tight_layout(); fig.savefig(os.path.join(figs, "mesh_edges.png")); plt.close(fig)


# ----------------------------------------------------------------- main
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", default="medium", choices=list(P.LEVELS))
    ap.add_argument("--case", required=True)
    ap.add_argument("--comp")
    ap.add_argument("--figs")
    ap.add_argument("--rigid", action="store_true", help="single O-grid to 20c that moves rigidly (no overset)")
    a = ap.parse_args()
    if a.rigid:
        lev = P.LEVELS[a.level]
        motion(a.case)
        quads, N_r, ncomp = component(a.comp, lev, a.figs, outer="farfield", far=P.R_FAR, far_growth=P.FAR_GROWTH)
        if a.figs:
            os.makedirs(a.figs, exist_ok=True)
            import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
            from matplotlib.collections import PolyCollection
            for name, (x0, x1, y0, y1) in (("mesh_rigid_far", (-21, 21, -20, 22)), ("mesh_rigid_near", (-1.5, 3.0, -0.5, 2.5)),
                                           ("mesh_rigid_le", (-0.45, -0.21, 0.88, 1.12)), ("mesh_rigid_te", (0.61, 0.73, 0.94, 1.06))):
                fig, ax = plt.subplots(figsize=(7, 6), dpi=160)
                ax.add_collection(PolyCollection(quads, facecolor="none", edgecolor="C0", lw=0.25))
                ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.set_title(f"rigid O-grid, {a.level}: {name[11:]}")
                fig.tight_layout(); fig.savefig(os.path.join(a.figs, name + ".png")); plt.close(fig)
        info = dict(level=a.level, mode="rigid", cells=ncomp, radial_cells=N_r, R_far=P.R_FAR, **lev, period=P.PERIOD)
        print(json.dumps(info))
        if a.figs:
            json.dump(info, open(os.path.join(a.figs, "mesh_info.json"), "w"), indent=1)
        sys.exit(0)
    lev = P.LEVELS[a.level]
    xn, yn, nbg = background(a.case, lev)
    motion(a.case)
    quads, N_r, ncomp = (None, None, 0)
    if a.comp:
        quads, N_r, ncomp = component(a.comp, lev, a.figs)
    if a.figs:
        figures(a.figs, xn, yn, quads, a.level)
    info = dict(level=a.level, background_cells=nbg, component_cells=ncomp, total_cells=nbg + ncomp,
                radial_cells=N_r, **lev, period=P.PERIOD)
    print(json.dumps(info))
    if a.figs:
        json.dump(info, open(os.path.join(a.figs, "mesh_info.json"), "w"), indent=1)

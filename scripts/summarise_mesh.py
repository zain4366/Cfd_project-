"""Collect the key numbers of one mesh level into summary.md (also printed for the Actions job summary)."""
import os, re, sys, json

out = sys.argv[1]
level = os.path.basename(os.path.normpath(out))


def grab(path, pat, cast=str):
    if not os.path.exists(path):
        return None
    m = re.findall(pat, open(path, errors="ignore").read())
    return cast(m[-1]) if m else None


lines = [f"## Mesh level: {level}", ""]
info = os.path.join(out, "mesh_info.json")
if os.path.exists(info):
    d = json.load(open(info))
    lines += [f"- background cells {d['background_cells']}, O-grid cells {d['component_cells']}, total {d['total_cells']}",
              f"- background cell {d['h']} c, foil points per side {d['ns']}, radial cells {d['radial_cells']}, first wall cell {d['a']} c", ""]
lines += ["| checkMesh | cells | result | max non-orthogonality | max skewness | max aspect ratio |", "|---|---|---|---|---|---|"]
for name, f in (("O-grid", "log.checkMesh"), ("background", "log.checkMesh.background"), ("merged", "log.checkMesh.merged")):
    p = os.path.join(out, f)
    if not os.path.exists(p):
        lines.append(f"| {name} | – | log missing | | | |"); continue
    txt = open(p, errors="ignore").read()
    ok = "Mesh OK" if "Mesh OK" in txt else (re.findall(r"Failed \d+ mesh checks", txt) or ["?"])[-1]
    ncell = grab(p, r"cells:\s+(\d+)")
    nonorth = grab(p, r"non-orthogonality Max:\s+([\d.eE+-]+)")
    skew = grab(p, r"Max skewness = ([\d.eE+-]+)")
    ar = grab(p, r"Max aspect ratio = ([\d.eE+-]+)")
    lines.append(f"| {name} | {ncell} | {ok} | {nonorth} | {skew} | {ar} |")
for f in ("motion_timing.txt", "orphans.txt"):
    p = os.path.join(out, f)
    if os.path.exists(p):
        lines += ["", f"**{f}**", "```", open(p).read().strip()[:2000], "```"]
p = os.path.join(out, "cell_types.md")
if os.path.exists(p):
    lines += ["", "**Overset cell types during the cycle**", "", open(p).read()]
txt = "\n".join(lines)
open(os.path.join(out, "summary.md"), "w").write(txt + "\n")
print(txt)

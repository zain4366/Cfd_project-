"""Minimal readers for ASCII OpenFOAM field files."""
import re
import numpy as np


def read_internal(path, vector):
    txt = open(path).read()
    i = txt.index("internalField")
    head = txt[i:i + 200]
    if "nonuniform" not in head:
        return None
    m = re.search(r"internalField\s+nonuniform\s+List<\w+>\s*(\d+)\s*\(", txt[i:])
    n = int(m.group(1)); start = i + m.end()
    if vector:
        body = txt[start:]
        vals = np.array(re.findall(r"\(([^()]*)\)", body[: body.find("\n)\n") + 2])[:n], dtype=object)
        return np.array([list(map(float, v.split())) for v in vals])
    body = txt[start: txt.find(")", start)]
    return np.array(body.split()[:n], dtype=float)

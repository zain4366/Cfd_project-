"""Build 2x2 still composites for the report and copy the animations into the data package.

    python3 add_anims.py <anim root with case{I,II,III}/animation/>
"""
import json, os, shutil, sys
from PIL import Image, ImageDraw, ImageFont

root = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "report", "img")
SIZES = os.path.join(HERE, "report", "img_sizes.json")
PKG = os.path.join(HERE, "AE471_data", "10_animations")
os.makedirs(PKG, exist_ok=True)
sizes = json.load(open(SIZES))
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
except OSError:
    font = ImageFont.load_default()

for c in ("I", "II", "III"):
    d = os.path.join(root, f"case{c}", "animation")
    if not os.path.isdir(d):
        print("missing", c); continue
    tiles = []
    for q, lab in (("00", "0"), ("25", "0.25"), ("50", "0.5"), ("75", "0.75")):
        im = Image.open(os.path.join(d, f"case{c}_still_tT{q}.png")).convert("RGB")
        tile = im.crop((165, 44, 870, 500))
        dr = ImageDraw.Draw(tile)
        txt = f"t/T = {lab}"
        x0, y0 = 80, 18
        bb = dr.textbbox((x0, y0), txt, font=font)
        dr.rectangle((bb[0] - 6, bb[1] - 4, bb[2] + 6, bb[3] + 4), fill="white", outline="black")
        dr.text((x0, y0), txt, fill="black", font=font)
        tiles.append(tile)
    cbar = Image.open(os.path.join(d, f"case{c}_still_tT00.png")).convert("RGB").crop((985, 40, 1095, 430))
    w, h = tiles[0].size
    out = Image.new("RGB", (2 * w + cbar.width + 10, 2 * h), "white")
    for i, t in enumerate(tiles):
        out.paste(t, ((i % 2) * w, (i // 2) * h))
    out.paste(cbar, (2 * w + 5, h - cbar.height // 2))
    name = f"anim_{c}.png"
    out.save(os.path.join(IMG, name))
    sizes[name] = list(out.size)
    for f in os.listdir(d):
        if f.endswith(".npz"):
            continue                      # last-cycle fields (26 MB each) stay on the ci-results branch
        shutil.copy(os.path.join(d, f), os.path.join(PKG, f))
    print("composite", name, out.size)
json.dump(sizes, open(SIZES, "w"), indent=1)

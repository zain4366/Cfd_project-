"""Glass-style LinkedIn thumbnail: full-bleed vorticity (dark diverging map) with a frosted-glass results card."""
import math, sys
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT, OUT, CASE, K = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
VMAX = float(sys.argv[5]) if len(sys.argv) > 5 else 4.0
X0 = float(sys.argv[6]) if len(sys.argv) > 6 else -0.9
SPAN = float(sys.argv[7]) if len(sys.argv) > 7 else 7.6
PAR = {"I": (0.14, 76.33), "II": (0.18, 60.0), "III": (0.06, 60.0)}
f, th0 = PAR[CASE]
d = np.load(f"{ROOT}/case{CASE}/animation/case{CASE}_fields_last_cycle.npz")
t = float(d[f"t{K:03d}"]); F = d[f"f{K:03d}"].astype(float)
x, y, w = F[:, 0], F[:, 1], F[:, 2]
om = 2 * math.pi * f; h = math.cos(om * t); th = math.radians(th0 * math.sin(om * t))
cmap = LinearSegmentedColormap.from_list("darkdiv", ["#7fe3ff", "#1f7fd6", "#123a7a", "#0a0f1e", "#7a1f2a", "#e0452e", "#ffc07a"])
W, H = 1920, 1080
fig = plt.figure(figsize=(W / 100, H / 100), dpi=100); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
fig.patch.set_facecolor("#0a0f1e")
tri = mtri.Triangulation(x, y)
xm = x[tri.triangles].mean(1); ym = y[tri.triangles].mean(1)
edge = np.max(np.hypot(np.diff(x[tri.triangles], axis=1), np.diff(y[tri.triangles], axis=1)), axis=1)
tri.set_mask(edge > 0.3 + 0.25 * np.hypot(xm, ym - h))
ax.tricontourf(tri, np.clip(w, -VMAX, VMAX), levels=np.linspace(-VMAX, VMAX, 81), cmap=cmap, extend="both")
XP = 1 / 3; xs = (1 - np.cos(np.linspace(0, np.pi, 121))) / 2
yt = 0.75 * (0.2969 * np.sqrt(xs) - 0.126 * xs - 0.3516 * xs**2 + 0.2843 * xs**3 - 0.1015 * xs**4)
XB, YB = np.r_[xs, xs[::-1]] - XP, np.r_[yt, -yt[::-1]]
for j in range(8):                                     # ghost outlines: the foil's path through one cycle
    tg = (j + 0.5) / 8 / f; hg = math.cos(om * tg); thg = math.radians(th0 * math.sin(om * tg))
    ax.fill(XB * math.cos(thg) - YB * math.sin(thg), hg + XB * math.sin(thg) + YB * math.cos(thg), fc=(1, 1, 1, 0.07), ec=(1, 1, 1, 0.18), lw=0.8, zorder=2)
    if False: ax.plot(0, 0, color="white", lw=0.8, alpha=0.10, zorder=2)
ax.fill(XB * math.cos(th) - YB * math.sin(th), h + XB * math.sin(th) + YB * math.cos(th), color="#e8edf5", ec="white", lw=1.5, zorder=3)
x0 = X0; span = SPAN
ax.set_xlim(x0, x0 + span); ax.set_ylim(-span * H / W / 2 + 0.0, span * H / W / 2)
fig.savefig(f"{OUT}/bg.png", facecolor=fig.get_facecolor()); plt.close(fig)

bg = Image.open(f"{OUT}/bg.png").convert("RGB").resize((W, H))
# vignette
vy, vx = np.mgrid[0:H, 0:W]; r = np.hypot((vx - W * 0.35) / W, (vy - H * 0.5) / H)
vig = np.clip(1.0 - 0.9 * np.clip(r - 0.25, 0, 1), 0.35, 1)
bg = Image.fromarray((np.asarray(bg) * vig[..., None]).astype(np.uint8))
card = (800, 150, 1840, 930); R = 40
# frosted glass: heavy blur + white tint inside the card, soft shadow, light border, top sheen
mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).rounded_rectangle(card, R, fill=255)
blur = bg.filter(ImageFilter.GaussianBlur(28))
tint = Image.blend(blur, Image.new("RGB", (W, H), (235, 242, 255)), 0.16)
shadow = Image.new("L", (W, H), 0); ImageDraw.Draw(shadow).rounded_rectangle((card[0] + 10, card[1] + 24, card[2] + 10, card[3] + 24), R, fill=170)
shadow = shadow.filter(ImageFilter.GaussianBlur(30))
img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), bg, shadow)
img = Image.composite(tint, img, mask)
sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sheen)
for i in range(260):                                    # soft diagonal highlight in the upper part of the glass
    a = int(38 * (1 - i / 260) ** 2)
    sd.line([(card[0], card[1] + i), (card[2], card[1] + i - 120)], fill=(255, 255, 255, a), width=1)
sm = Image.new("L", (W, H), 0); ImageDraw.Draw(sm).rounded_rectangle(card, R, fill=255)
sheen.putalpha(ImageChops.multiply(sheen.getchannel("A"), sm))
img = Image.alpha_composite(img.convert("RGBA"), sheen)
bd = ImageDraw.Draw(img)
bd.rounded_rectangle(card, R, outline=(255, 255, 255, 150), width=2)
bd.rounded_rectangle((card[0] + 2, card[1] + 2, card[2] - 2, card[3] - 2), R - 2, outline=(255, 255, 255, 40), width=1)

over = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(over)
B = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"; SB = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
Rg = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"; Md = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
fnt = lambda p, s: ImageFont.truetype(p, s)
L = card[0] + 70
d.text((L, card[1] + 62), "ONE FOIL  ·  THREE MOTIONS", font=fnt(SB, 30), fill=(200, 225, 255, 255))
d.text((L, card[1] + 108), "How it moves decides\nhow much energy it harvests", font=fnt(B, 58), fill=(255, 255, 255, 255), spacing=10)
rows = [("Case I", "vortex in step with the heave", "33.7", "33.7", (90, 170, 255)),
        ("Case II", "attached flow, lift lags", "10.9", "11.4", (255, 165, 80)),
        ("Case III", "vortex shed too early", "12.4", "12.3", (110, 220, 150))]
y0 = card[1] + 285
for i, (c, tag, eta, kd, col) in enumerate(rows):
    yy = y0 + i * 132
    if i:
        d.line([(L, yy - 22), (card[2] - 70, yy - 22)], fill=(255, 255, 255, 50), width=1)
    d.ellipse((L, yy + 22, L + 22, yy + 44), fill=col + (255,))
    d.text((L + 42, yy + 6), c, font=fnt(SB, 38), fill=(255, 255, 255, 255))
    d.text((L + 42, yy + 54), tag, font=fnt(Rg, 26), fill=(215, 225, 240, 230))
    big = fnt(B, 84); s = f"{eta}%"
    tw = d.textlength(s, font=big)
    d.text((card[2] - 70 - tw, yy - 8), s, font=big, fill=col + (255,))
    pk = f"paper {kd}%"; sw = d.textlength(pk, font=fnt(Rg, 24))
    d.text((card[2] - 70 - sw, yy + 80), pk, font=fnt(Rg, 24), fill=(210, 220, 235, 210))
d.text((L, card[3] - 78), "OpenFOAM reproduction of Kinsey & Dumas (2008)  ·  NACA 0015, Re = 1100",
       font=fnt(Md, 25), fill=(225, 235, 250, 235))
# small label on the flow side
d.text((60, H - 70), f"Case {CASE} vorticity  ·  faint outlines: the foil's path through one cycle", font=fnt(Md, 24), fill=(220, 230, 245, 200))
img = Image.alpha_composite(img, over).convert("RGB")
img.save(f"{OUT}/thumb_{CASE}_{K}.jpg", quality=93); print("ok")

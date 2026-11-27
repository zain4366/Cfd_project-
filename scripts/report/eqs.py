import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, json, os
plt.rcParams.update({"mathtext.fontset": "stix", "font.family": "STIXGeneral"})
E = {
 "eq1": r"$h(t) = H_0\cos(2\pi f t), \qquad \theta(t) = \theta_0 \sin(2\pi f t)$",
 "eq2": r"$f^{*} = \dfrac{f c}{U}, \qquad Re = \dfrac{U c}{\nu} = 1100$",
 "eq3": r"$C_X = \dfrac{F_x}{\frac{1}{2}\rho U^2 c}, \qquad C_Y = \dfrac{F_y}{\frac{1}{2}\rho U^2 c}, \qquad C_M = \dfrac{M}{\frac{1}{2}\rho U^2 c^2}$",
 "eq4": r"$C_P = C_Y\,\dfrac{V_y}{U} + C_M\,\dfrac{\Omega c}{U}, \qquad \eta = \overline{C}_P\,\dfrac{c}{d}$",
 "eq5": r"$\nabla\cdot\mathbf{u} = 0, \qquad \dfrac{\partial \mathbf{u}}{\partial t} + \left[(\mathbf{u}-\mathbf{u}_m)\cdot\nabla\right]\mathbf{u} = -\dfrac{\nabla p}{\rho} + \nu\nabla^2\mathbf{u}$",
 "eq6": r"$\eta(R) = \eta_\infty + \dfrac{k}{R}$",
 "eqkin": r"$\alpha_{T/4} = \arctan\left(\dfrac{2\pi f^{*} H_0}{c}\right) - \theta_0, \qquad \chi = \dfrac{\theta_0}{\arctan\left(2\pi f^{*} H_0/c\right)}$",
 "eqer": r"$E_r = \dfrac{\left|\phi_{CFD} - \phi_{ref}\right|}{\left|\phi_{ref}\right|} \times 100\,\%$",
}
sizes = {}
for k, s in E.items():
    fig = plt.figure(figsize=(0.01, 0.01)); fig.text(0, 0, s, fontsize=13)
    p = f"eq/{k}.png"; fig.savefig(p, dpi=300, bbox_inches="tight", pad_inches=0.03, transparent=False, facecolor="white"); plt.close(fig)
    from PIL import Image; sizes[k] = Image.open(p).size
json.dump(sizes, open("eq_sizes.json", "w")); print(sizes)

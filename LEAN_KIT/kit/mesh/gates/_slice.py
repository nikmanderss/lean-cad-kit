"""R5 survey helper (my own, read-only on the meshes): true plane sections of one or more STL meshes, plotted. (a gate tool: kit mesh gate _slice --job <J> --tag <T> -- <args>)"""
import sys, struct
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def section(T, ax, val):
    if ax == 3:
        d = (T - P0 - val * NN) @ NN
    else:
        d = T[:, :, ax] - val
    s = np.sign(d)
    s[s == 0] = 1e-9
    m = ~((s > 0).all(1) | (s < 0).all(1))
    T = T[m]; d = d[m]
    segs = []
    for i, j in ((0, 1), (1, 2), (2, 0)):
        pass
    P = []
    for e in ((0, 1), (1, 2), (2, 0)):
        a, b = e
        da, db = d[:, a], d[:, b]
        cross = (da * db) < 0
        t = np.where(cross, da / np.where(cross, da - db, 1), 0)
        pt = T[:, a] + t[:, None] * (T[:, b] - T[:, a])
        P.append((cross, pt))
    out = []
    c0, p0 = P[0]; c1, p1 = P[1]; c2, p2 = P[2]
    for ca, pa, cb, pb in ((c0, p0, c1, p1), (c1, p1, c2, p2), (c0, p0, c2, p2)):
        mm = ca & cb
        out.append(np.stack([pa[mm], pb[mm]], 1))
    return np.concatenate(out, 0)


def proj(seg, ax):
    if ax == 3:
        return np.stack([(seg - P0) @ UU, seg[:, :, 2]], -1)
    if ax == 0:
        return seg[:, :, [1, 2]]
    if ax == 1:
        return seg[:, :, [0, 2]]
    return seg[:, :, [1, 0]]


out = sys.argv[1]; axn = sys.argv[2]; ax = "xyzn".index(axn)
import os as _os
if ax == 3:
    _pl = [float(t) for t in _os.environ["PLANE"].split(",")]
    P0 = np.array(_pl[:3]); NN = np.array(_pl[3:]); NN = NN / np.linalg.norm(NN)
    UU = np.cross(NN, [0, 0, 1.0]); UU = UU / np.linalg.norm(UU)
    if _os.environ.get("UFLIP") == "1":
        UU = -UU
vals = [float(v) for v in sys.argv[3].split(",")]
u0, u1, v0, v1 = [float(t) for t in sys.argv[4].split()]
specs = [s.split("=", 1) for s in sys.argv[5].split(";")]
title = sys.argv[6] if len(sys.argv) > 6 else ""
cols = ["#1f3fbf", "#e8631a", "#18a018", "#b01ab0"]
widths = [2.2, 1.1, 1.0, 1.0]
meshes = []
for lab, p in specs:
    T = read_stl(p.strip())
    lo = np.array([-1e9] * 3); hi = np.array([1e9] * 3)
    meshes.append((lab, T))
lab_u = {0: "y", 1: "x", 2: "y", 3: "u"}[ax]; lab_v = {0: "z", 1: "z", 2: "x", 3: "z"}[ax]
import os
n = len(vals)
asp = (v1 - v0) / (u1 - u0)
nc = int(os.environ.get("NC", "1")); nr = (n + nc - 1) // nc
pw = float(os.environ.get("PW", "11")) / nc
fig, axs = plt.subplots(nr, nc, figsize=(pw * nc, (pw * asp + 0.5) * nr + 0.3), squeeze=False)
for k in range(n, nr * nc):
    axs[k // nc][k % nc].axis("off")
for k, val in enumerate(vals):
    a_ = axs[k // nc][k % nc]
    for i, (lab, T) in enumerate(meshes):
        c = T.mean(1)
        seg = section(T, ax, val)
        s2 = proj(seg, ax)
        m = ((s2[:, :, 0] >= u0 - 2) & (s2[:, :, 0] <= u1 + 2) & (s2[:, :, 1] >= v0 - 2) & (s2[:, :, 1] <= v1 + 2)).any(1)
        if i == 0 and os.environ.get("FILL", "1") == "1":
            S = s2
            res = float(os.environ.get("RES", "0.05"))
            vv = np.arange(v0 + res / 2, v1, res); uu = np.arange(u0 + res / 2, u1, res)
            img = np.zeros((len(vv), len(uu)), np.uint8)
            a0 = S[:, 0, :]; b0 = S[:, 1, :]
            for r, v in enumerate(vv):
                cr = ((a0[:, 1] - v) * (b0[:, 1] - v)) < 0
                if not cr.any():
                    continue
                t = (v - a0[cr, 1]) / (b0[cr, 1] - a0[cr, 1])
                xs = np.sort(a0[cr, 0] + t * (b0[cr, 0] - a0[cr, 0]))
                for q in range(0, len(xs) - 1, 2):
                    i0 = np.searchsorted(uu, xs[q]); i1 = np.searchsorted(uu, xs[q + 1])
                    img[r, i0:i1] = 1
            a_.imshow(np.where(img[..., None] == 1, np.array([[[0.72, 0.80, 0.95]]]), np.array([[[1.0, 1.0, 1.0]]])),
                      origin="lower", extent=(u0, u1, v0, v1), interpolation="nearest", zorder=0)
        lc = LineCollection(s2[m], colors=cols[i % 4], linewidths=widths[i % 4], label=lab, zorder=2 + i)
        a_.add_collection(lc)
    a_.set_xlim(u0, u1); a_.set_ylim(v0, v1); a_.set_aspect("equal")
    a_.grid(True, which="major", color="#bbbbbb", lw=0.5)
    a_.minorticks_on(); a_.grid(True, which="minor", color="#e6e6e6", lw=0.3)
    a_.set_xlabel(lab_u + " (mm)"); a_.set_ylabel(lab_v + " (mm)")
    a_.set_title("%s   plane %s = %.2f" % (title, axn, val), fontsize=9)
    if k == 0 and len(meshes) > 1:
        a_.legend(loc="upper right", fontsize=8)
plt.tight_layout()
plt.savefig(out, dpi=110)
print(out)

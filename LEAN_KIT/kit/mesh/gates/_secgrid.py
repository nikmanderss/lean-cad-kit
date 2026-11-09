"""review2/R1 - a grid of true planar sections (before blue thick, after red thin), one window, many stations. (a gate tool: kit mesh gate _secgrid --job <J> --tag <T> -- <args>)"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else ".")
from _sec import read_stl, slice_mesh

before, after, axn, rng, win, out = sys.argv[1:7]
title = sys.argv[7] if len(sys.argv) > 7 else ""
ncol = int(sys.argv[8]) if len(sys.argv) > 8 else 5
ax = "xyz".index(axn); uv = [i for i in range(3) if i != ax]
v0, v1, st = [float(t) for t in rng.split()]
vals = np.arange(v0, v1 + 1e-9, st)
win = [float(t) for t in win.split()]
lo = np.array([win[0], win[2]]); hi = np.array([win[1], win[3]])
B = read_stl(before); A = read_stl(after)
def pre(M):
    c = M.reshape(-1, 3)
    m = np.ones(len(M), bool)
    for k, (a, b) in zip(uv, ((win[0], win[1]), (win[2], win[3]))):
        m &= (M[:, :, k].max(1) >= a - 2) & (M[:, :, k].min(1) <= b + 2)
    m &= (M[:, :, ax].max(1) >= v0 - 1) & (M[:, :, ax].min(1) <= v1 + 1)
    return M[m]
B = pre(B); A = pre(A)
nrow = int(np.ceil(len(vals) / ncol))
asp = (win[3] - win[2]) / (win[1] - win[0])
fig, axs = plt.subplots(nrow, ncol, figsize=(3.3 * ncol, 3.3 * ncol / ncol * asp * nrow + 0.8), dpi=100, squeeze=False)
for i, v in enumerate(vals):
    g = axs[i // ncol][i % ncol]
    for M, col, lw in ((B, "#2060d0", 2.2), (A, "#e03020", 0.9)):
        m = (M[:, :, ax].min(1) <= v) & (M[:, :, ax].max(1) >= v)
        s = slice_mesh(M[m], ax, v)[:, :, uv]
        g.add_collection(LineCollection(s, colors=col, linewidths=lw))
    g.set_xlim(win[0], win[1]); g.set_ylim(win[2], win[3]); g.set_aspect("equal")
    g.set_title("%s = %.2f" % (axn, v), fontsize=8)
    g.tick_params(labelsize=6)
    span = win[1] - win[0]
    maj = 0.5 if span <= 5 else (1.0 if span <= 12 else 2.0)
    g.set_xticks(np.arange(np.ceil(win[0] / maj) * maj, win[1] + 1e-9, maj))
    g.set_yticks(np.arange(np.ceil(win[2] / maj) * maj, win[3] + 1e-9, maj))
    g.grid(color="#cccccc", lw=0.4)
for j in range(len(vals), nrow * ncol):
    axs[j // ncol][j % ncol].axis("off")
fig.suptitle("%s  (blue before, red after; grid %s mm; axes %s,%s)" % (title, "0.5" if (win[1]-win[0]) <= 5 else ("1" if (win[1]-win[0]) <= 12 else "2"), "xyz"[uv[0]], "xyz"[uv[1]]), fontsize=10)
fig.tight_layout(); fig.savefig(out); print(out)

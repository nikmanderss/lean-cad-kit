"""review2/R1 - map of how far the frozen HEATSINK region's surface moved in the edit (distance of each region sample (a gate tool: kit mesh gate _frozenmap --job <J> --tag <T> -- <args>)"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from _sec import read_stl
from _frozen import sample, dist_to_mesh

reg, bef, aft, box, out, title = sys.argv[1:7]
b = [float(t) for t in box.split()]; lo = np.array(b[0::2]); hi = np.array(b[1::2])
R = read_stl(reg)
m = np.all((R.max(1) >= lo) & (R.min(1) <= hi), 1)
P = sample(R[m], per=0.25)
P = P[np.all((P >= lo) & (P <= hi), 1)]
ds = []
for f in (bef, aft):
    T = read_stl(f)
    mm = np.all((T.max(1) >= lo - 3) & (T.min(1) <= hi + 3), 1)
    ds.append(dist_to_mesh(P, T[mm]))
fig, axs = plt.subplots(2, 2, figsize=(14, 10), dpi=100)
for r, (lab, d) in enumerate(zip(("before (control)", "after"), ds)):
    o = np.argsort(d)
    for c, (i, j, nm) in enumerate(((1, 2, "y-z (seen from outboard)"), (0, 1, "x-y (seen from above)"))):
        g = axs[r][c]
        sc = g.scatter(P[o, i], P[o, j], c=d[o], s=1.2, cmap="inferno_r", vmin=0, vmax=0.8)
        g.set_aspect("equal"); g.set_title("%s  %s: heatsink samples moved > 0.05 mm: %d of %d, max %.2f mm" % (lab, nm, (d > 0.05).sum(), len(d), d.max()), fontsize=8)
        g.set_xlabel("xyz"[i] + " mm"); g.set_ylabel("xyz"[j] + " mm"); g.grid(lw=0.3)
        plt.colorbar(sc, ax=g, fraction=0.03, label="distance to mesh, mm")
fig.suptitle(title, fontsize=11)
fig.tight_layout(); fig.savefig(out); print(out)
_dd = ds[1] - ds[0]
print("FROZEN %s: %d of %d sample(s) moved > 0.05 mm beyond the control (max %.3f mm) -> %s"
      % (title, int((_dd > 0.05).sum()), len(_dd), float(_dd.max()), "HELD" if (_dd > 0.05).sum() == 0 else "*** MOVED ***"))

"""selftest_keepgrid.py - the keep's cut placement (rebuild/_keepgrid.py, 31ai) without a kernel.
Cases: a horizontal skin (a lip) keeps the z planes off it; KEEP_OFFSET moves the planes and the grid still covers the window;
a boundary face where the original runs flat along the plane is estimated wide (grazing) and one across it narrow; grow()
takes the grazing face's kept bin and never a forced one."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild"))
import _keepgrid as KG
ok = 0; bad = 0
def check(cond, what):
    global ok, bad
    if cond: ok += 1; print("  ok   " + what)
    else: bad += 1; print("  FAIL " + what)

xs, ys = np.meshgrid(np.linspace(0.2, 8.8, 30), np.linspace(0.2, 8.8, 30)); n = xs.size
S = np.vstack([np.stack([xs.ravel(), ys.ravel(), np.full(n, 1.35)], 1), np.stack([xs.ravel(), ys.ravel(), np.full(n, 2.35)], 1)])
N = np.vstack([np.tile([0, 0, 1.0], (n, 1)), np.tile([0, 0, -1.0], (n, 1))])
g0, rep = KG.choose_offsets([0, 0, 0], 3.0, S, N, clear=0.3)
planes = g0[2] + 3.0 * np.arange(-1, 5)
dmin = min(abs(z - p) for z in (1.35, 2.35) for p in planes)
check(dmin >= 0.3 - 1e-9, "z planes kept >= 0.3 mm off a near-parallel skin (nearest %.2f mm; within-clear count %d)" % (dmin, rep[2]["within_clear"]))
check(g0[2] <= 0.0 + 1e-9 and g0[2] > -3.0 - 1e-9, "the grid starts at or below the window (g0 z %.3f)" % g0[2])
g1, rep1 = KG.choose_offsets([0, 0, 0], 3.0, S, N, clear=0.3, extra=(0.0, 0.0, 1.2))
sh = ((g1[2] - g0[2]) % 3.0)
check(abs(sh - 1.2) < 1e-9 and g1[2] <= 1e-9, "KEEP_OFFSET 1.2 shifts the z planes by 1.2 mm (got %.3f), origin %.3f <= 0" % (sh, g1[2]))
rb = np.zeros((3, 1, 3), bool); rb[:, :, 0] = True; fz = np.zeros_like(rb)
g = np.array([0.0, 0.0, 0.0]); zp = 3.0
pts_flat = np.array([[1.0, 1.5, zp + 0.1], [4.0, 1.5, zp - 0.1]]); nrm_flat = np.array([[0, 0, 1.0], [0, 0, 1.0]]); d_flat = np.array([0.05, 0.05])
pts_cross = np.array([[7.0, 1.5, zp + 0.05]]); nrm_cross = np.array([[1.0, 0, 0]]); d_cross = np.array([0.05])
faces = KG.boundary_widths(rb, fz, g, 3.0, np.vstack([pts_flat, pts_cross]), np.vstack([nrm_flat, nrm_cross]), np.concatenate([d_flat, d_cross]), slab=0.3)
wf = max(e["width"] for e in faces if e["kept"][0] in (0, 1)); wc = max(e["width"] for e in faces if e["kept"][0] == 2)
check(wf > 0.15, "a skin running flat along the cut plane reads WIDE (%.2f mm for a 0.05 mm deviation)" % wf)
check(wc < 0.1, "a skin crossing the cut plane reads narrow (%.3f mm)" % wc)
r2, ng = KG.grow(rb, fz, faces, 0.15)
check(ng == 2 and r2[0, 0, 1] and r2[1, 0, 1] and not r2[2, 0, 1], "grow() takes the two grazing faces' kept bins and not the crossing one (%d grown)" % ng)
fz2 = np.zeros_like(rb); fz2[0, 0, 1] = True
faces2 = KG.boundary_widths(rb, fz2, g, 3.0, np.vstack([pts_flat, pts_cross]), np.vstack([nrm_flat, nrm_cross]), np.concatenate([d_flat, d_cross]), slab=0.3)
r3, ng3 = KG.grow(rb, fz2, faces2, 0.15)
check(not r3[0, 0, 1], "a FORCED kept bin is never grown into (%d grown)" % ng3)
cl = KG.clusters(np.array([[0, 0, 0], [0.5, 0, 0], [20, 20, 20]], float), cell=6.0, top=4)
check(len(cl) == 2 and cl[0][0] == 2, "clusters(): the most populous place first")
print("%d passed, %d FAILED" % (ok, bad))
sys.exit(1 if bad else 0)

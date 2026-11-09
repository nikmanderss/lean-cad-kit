"""review2/R1 - trace the air pocket under the outboard skin: the new-air component holding a probe point, (a gate tool: kit mesh gate _cave --job <J> --tag <T> -- <args>)"""
import sys
import numpy as np
from scipy import ndimage as nd
from _sec import read_stl
from _vox import occupancy

bef, aft, box, h, p = sys.argv[1:6]
box = [float(t) for t in box.split()]; h = float(h); p = np.array([float(t) for t in p.split(",")])
ob, xs, ys, zs = occupancy(read_stl(bef), box, h)
oa, _, _, _ = occupancy(read_stl(aft), box, h)
newair = ob & ~oa
L, n = nd.label(newair)
ijk = tuple(int(np.argmin(np.abs(a - v))) for a, v in zip((xs, ys, zs), p))
c = L[ijk]
print("probe voxel", ijk, "after solid?", oa[ijk], "before solid?", ob[ijk], "new-air component", c)
if c == 0:
    sys.exit()
m = L == c
w = np.argwhere(m)
print("component: %.3f mm3, x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (m.sum() * h ** 3, xs[w[:, 0].min()], xs[w[:, 0].max()], ys[w[:, 1].min()], ys[w[:, 1].max()], zs[w[:, 2].min()], zs[w[:, 2].max()]))
oldair = ~ob & ~oa
mouth = m & nd.binary_dilation(oldair, structure=nd.generate_binary_structure(3, 1))
w2 = np.argwhere(mouth)
print("mouth voxels %d" % len(w2))
if len(w2):
    Lm, nm = nd.label(mouth, structure=np.ones((3, 3, 3)))
    for k in range(1, nm + 1):
        ww = np.argwhere(Lm == k)
        print("   mouth part %d: %d vox, x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (k, len(ww), xs[ww[:, 0].min()], xs[ww[:, 0].max()], ys[ww[:, 1].min()], ys[ww[:, 1].max()], zs[ww[:, 2].min()], zs[ww[:, 2].max()]))
sgn = 1 if p[0] > 0 else -1
solid_after_x = (np.flip(np.cumsum(np.flip(oa, 0), 0), 0) > 0) if sgn > 0 else (np.cumsum(oa, 0) > 0)
roofed = m & solid_after_x
w3 = np.argwhere(roofed)
print("roofed (solid outboard of it, outboard = %s x)" % ("+" if sgn > 0 else "-")); print("roofed new air: %.3f mm3" % (roofed.sum() * h ** 3))
if len(w3):
    print("   x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (xs[w3[:, 0].min()], xs[w3[:, 0].max()], ys[w3[:, 1].min()], ys[w3[:, 1].max()], zs[w3[:, 2].min()], zs[w3[:, 2].max()]))
    th = []
    for (i, j, k) in w3:
        col = oa[i + 1:, j, k] if sgn > 0 else oa[:i, j, k][::-1]
        if col.size == 0 or not col[0]:
            continue
        run = np.argmin(col) if (~col).any() else col.size
        th.append((run * h, ys[j], zs[k]))
    th = np.array(th)
    if len(th):
        print("   roof thickness along +x: min %.2f mm, median %.2f mm" % (th[:, 0].min(), np.median(th[:, 0])))
        for r in th[np.argsort(th[:, 0])][:5]:
            print("      %.2f mm at y %.2f z %.2f" % tuple(r))
np.savez_compressed("cave_%s.npz" % ("P" if p[0] > 0 else "M"), m=m, oa=oa, ob=ob, xs=xs, ys=ys, zs=zs)

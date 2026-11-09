"""review2/R1 - occupancy of before and after in a box by x-ray parity per (y,z) column; ADD / REM volumes, (a gate tool: kit mesh gate _vox --job <J> --tag <T> -- <args>)"""
import sys, struct
import numpy as np
from scipy import ndimage as nd
from _sec import read_stl


def occupancy(T, box, h):
    x0, x1, y0, y1, z0, z1 = box
    ys = np.arange(y0 + h / 2, y1, h) + 0.00137
    zs = np.arange(z0 + h / 2, z1, h) + 0.00071
    xs = np.arange(x0 + h / 2, x1, h)
    m = (T[:, :, 1].max(1) >= y0) & (T[:, :, 1].min(1) <= y1) & (T[:, :, 2].max(1) >= z0) & (T[:, :, 2].min(1) <= z1)
    T = T[m]
    occ = np.zeros((len(xs), len(ys), len(zs)), bool)
    cy = 1.0
    tymin = T[:, :, 1].min(1); tymax = T[:, :, 1].max(1); tzmin = T[:, :, 2].min(1); tzmax = T[:, :, 2].max(1)
    A = T[:, 0]; B = T[:, 1]; C = T[:, 2]
    for j, y in enumerate(ys):
        mj = (tymin <= y) & (tymax >= y)
        idx = np.nonzero(mj)[0]
        if len(idx) == 0:
            continue
        a = A[idx]; b = B[idx]; c = C[idx]
        zmin = tzmin[idx]; zmax = tzmax[idx]
        for k, z in enumerate(zs):
            mk = (zmin <= z) & (zmax >= z)
            if not mk.any():
                continue
            aa = a[mk]; bb = b[mk]; cc = c[mk]
            v0 = bb[:, 1:] - aa[:, 1:]; v1 = cc[:, 1:] - aa[:, 1:]; v2 = np.array([y, z]) - aa[:, 1:]
            den = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]
            ok = np.abs(den) > 1e-14
            den = np.where(ok, den, 1)
            u = (v2[:, 0] * v1[:, 1] - v1[:, 0] * v2[:, 1]) / den
            v = (v0[:, 0] * v2[:, 1] - v2[:, 0] * v0[:, 1]) / den
            hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1)
            if not hit.any():
                continue
            xc = (aa[hit, 0] + u[hit] * (bb[hit, 0] - aa[hit, 0]) + v[hit] * (cc[hit, 0] - aa[hit, 0]))
            xc = np.sort(xc)
            cnt = np.searchsorted(xc, xs)
            occ[:, j, k] = (cnt % 2) == 1
    return occ, xs, ys, zs


if __name__ == "__main__":
    bef, aft, box, h, out = sys.argv[1:6]
    box = [float(t) for t in box.split()]; h = float(h)
    ob, xs, ys, zs = occupancy(read_stl(bef), box, h)
    oa, _, _, _ = occupancy(read_stl(aft), box, h)
    v = h ** 3
    add = oa & ~ob; rem = ob & ~oa
    print("box", box, "h", h, "grid", ob.shape)
    print("solid before %.1f mm3, after %.1f mm3, ADD %.1f mm3, REM %.1f mm3, net %+.1f" % (ob.sum() * v, oa.sum() * v, add.sum() * v, rem.sum() * v, (oa.sum() - ob.sum()) * v))
    for lab, g in (("ADD", add), ("REM", rem)):
        L, n = nd.label(g)
        if n == 0:
            continue
        sz = nd.sum(g, L, range(1, n + 1)) * v
        order = np.argsort(-sz)
        print(" %s components %d; largest:" % (lab, n))
        for i in order[:8]:
            w = np.argwhere(L == i + 1)
            lo = w.min(0); hi = w.max(0)
            print("   %8.2f mm3  x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (sz[i], xs[lo[0]], xs[hi[0]], ys[lo[1]], ys[hi[1]], zs[lo[2]], zs[hi[2]]))
    for lab, o in (("before", ob), ("after", oa)):
        L, n = nd.label(~o)
        border = set(np.unique(np.concatenate([L[0].ravel(), L[-1].ravel(), L[:, 0].ravel(), L[:, -1].ravel(), L[:, :, 0].ravel(), L[:, :, -1].ravel()])))
        enc = [i for i in range(1, n + 1) if i not in border]
        print(" %s: air components %d, enclosed (not reaching the box wall) %d" % (lab, n, len(enc)))
        for i in enc[:10]:
            w = np.argwhere(L == i)
            lo = w.min(0); hi = w.max(0)
            print("   void %.3f mm3  x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (len(w) * v, xs[lo[0]], xs[hi[0]], ys[lo[1]], ys[hi[1]], zs[lo[2]], zs[hi[2]]))
        Ls, ns = nd.label(o)
        print(" %s: solid components %d (sizes %s)" % (lab, ns, sorted([round(float(s) * v, 3) for s in nd.sum(o, Ls, range(1, ns + 1))])[-5:]))
    np.savez_compressed(out, ob=ob, oa=oa, xs=xs, ys=ys, zs=zs)

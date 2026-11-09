"""review2/R1 - does a frozen region's surface survive the edit? Sample the region's triangles inside a box and (a gate tool: kit mesh gate _frozen --job <J> --tag <T> -- <args>)"""
import sys
import numpy as np
from scipy.spatial import cKDTree
from _sec import read_stl


def pt_tri_dist(p, a, b, c):
    ab = b - a; ac = c - a; ap = p - a
    d1 = np.einsum("ij,ij->i", ab, ap); d2 = np.einsum("ij,ij->i", ac, ap)
    bp = p - b; d3 = np.einsum("ij,ij->i", ab, bp); d4 = np.einsum("ij,ij->i", ac, bp)
    cp = p - c; d5 = np.einsum("ij,ij->i", ab, cp); d6 = np.einsum("ij,ij->i", ac, cp)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = va + vb + vc; den = np.where(np.abs(den) < 1e-18, 1e-18, den)
    v = vb / den; w = vc / den
    q = a + ab * v[:, None] + ac * w[:, None]
    m = (d1 <= 0) & (d2 <= 0); q[m] = a[m]
    m = (d3 >= 0) & (d4 <= d3); q[m] = b[m]
    m = (d6 >= 0) & (d5 <= d6); q[m] = c[m]
    m = (vc <= 0) & (d1 >= 0) & (d3 <= 0); t = d1 / np.where(d1 - d3 == 0, 1e-18, d1 - d3); q[m] = (a + ab * t[:, None])[m]
    m = (vb <= 0) & (d2 >= 0) & (d6 <= 0); t = d2 / np.where(d2 - d6 == 0, 1e-18, d2 - d6); q[m] = (a + ac * t[:, None])[m]
    m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
    t = (d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1e-18, (d4 - d3) + (d5 - d6)); q[m] = (b + (c - b) * t[:, None])[m]
    return np.linalg.norm(p - q, axis=1)


def dist_to_mesh(P, T, K=24):
    C = T.mean(1)
    tr = cKDTree(C)
    _, idx = tr.query(P, k=K)
    best = np.full(len(P), np.inf)
    for k in range(K):
        t = T[idx[:, k]]
        best = np.minimum(best, pt_tri_dist(P, t[:, 0], t[:, 1], t[:, 2]))
    return best


def sample(T, per=0.15):
    out = []
    for t in T:
        e = max(np.linalg.norm(t[1] - t[0]), np.linalg.norm(t[2] - t[0]), np.linalg.norm(t[2] - t[1]))
        n = max(2, int(np.ceil(e / per)))
        for i in range(n + 1):
            for j in range(n + 1 - i):
                u = i / n; v = j / n
                out.append(t[0] + u * (t[1] - t[0]) + v * (t[2] - t[0]))
    return np.array(out)


if __name__ == "__main__":
    reg, bef, aft, box = sys.argv[1:5]
    tol = float(sys.argv[5]) if len(sys.argv) > 5 else 0.02
    b = [float(t) for t in box.split()]; lo = np.array(b[0::2]); hi = np.array(b[1::2])
    R = read_stl(reg)
    m = np.all((R.max(1) >= lo) & (R.min(1) <= hi), 1)
    P = sample(R[m])
    P = P[np.all((P >= lo) & (P <= hi), 1)]
    print("region %s: %d triangles meet the box, %d samples inside it" % (reg.split("/")[-1], m.sum(), len(P)))
    for lab, f in (("before", bef), ("after", aft)):
        T = read_stl(f)
        mm = np.all((T.max(1) >= lo - 3) & (T.min(1) <= hi + 3), 1)
        d = dist_to_mesh(P, T[mm])
        off = d > tol
        print("  %-6s: samples off the surface by > %.2f mm: %d (max %.3f mm, p99 %.3f)" % (lab, tol, off.sum(), d.max(), np.percentile(d, 99)))
        if off.any():
            Q = P[off]
            print("          off samples x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (Q[:, 0].min(), Q[:, 0].max(), Q[:, 1].min(), Q[:, 1].max(), Q[:, 2].min(), Q[:, 2].max()))
            np.save("_frozen_off_%s_%s.npy" % (reg.replace("\\", "/").split("/")[-1][:-4], lab), np.c_[Q, d[off]])

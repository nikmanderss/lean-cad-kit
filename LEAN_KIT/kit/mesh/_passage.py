import sys, struct
import numpy as np


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def clear_rays(T, lo, hi, ax, step):
    m = np.all(T.max(1) >= lo, 1) & np.all(T.min(1) <= hi, 1)
    T = T[m]
    u, v = [k for k in range(3) if k != ax]
    gu = np.arange(lo[u] + step / 2, hi[u], step); gv = np.arange(lo[v] + step / 2, hi[v], step)
    U, V = np.meshgrid(gu, gv, indexing="ij"); U = U.ravel(); V = V.ravel()
    blocked = np.zeros(len(U), bool)
    for t in T:
        a, b, c = t[:, u], t[:, v], t[:, ax]
        bb = (U >= a.min()) & (U <= a.max()) & (V >= b.min()) & (V <= b.max()) & ~blocked
        if not bb.any():
            continue
        idx = np.where(bb)[0]
        p0 = np.array([a[0], b[0]]); e1 = np.array([a[1] - a[0], b[1] - b[0]]); e2 = np.array([a[2] - a[0], b[2] - b[0]])
        det = e1[0] * e2[1] - e1[1] * e2[0]
        if abs(det) < 1e-14:
            continue
        du = U[idx] - p0[0]; dv = V[idx] - p0[1]
        s = (du * e2[1] - dv * e2[0]) / det; r = (e1[0] * dv - e1[1] * du) / det
        inside = (s >= 0) & (r >= 0) & (s + r <= 1)
        w = c[0] + s * (c[1] - c[0]) + r * (c[2] - c[0])
        hit = inside & (w >= lo[ax]) & (w <= hi[ax])
        blocked[idx[hit]] = True
    return (~blocked).sum(), len(U)


if __name__ == "__main__":
    base, after, box = sys.argv[1], sys.argv[2], [float(t) for t in sys.argv[3].split()]
    step = float(sys.argv[4]) if len(sys.argv) > 4 else 0.2
    label = sys.argv[5] if len(sys.argv) > 5 else ""
    lo, hi = np.array(box[0::2]), np.array(box[1::2])
    B, A = read_stl(base), read_stl(after)
    out = []
    for ax, nm in enumerate("xyz"):
        cb, n = clear_rays(B, lo, hi, ax, step); ca, _ = clear_rays(A, lo, hi, ax, step)
        verdict = "same" if ca == cb else ("CLOSED" if ca == 0 < cb else ("NARROWED" if ca < cb else "wider"))
        out.append("%s: %d -> %d clear of %d (%s)" % (nm, cb, ca, n, verdict))
    print("%-28s %s" % (label, " | ".join(out)))

import os, sys, struct
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ccseam as S


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    t = a["v"].reshape(-1, 3, 3).astype(np.float64)
    q = np.round(t.reshape(-1, 3) / 1e-7).astype(np.int64)
    u, inv = np.unique(q, axis=0, return_inverse=True)
    return u * 1e-7, inv.reshape(-1, 3)


stem = sys.argv[1]; tol = float(sys.argv[2]) if len(sys.argv) > 2 else 0.15
VA, TA = read_stl(stem + "_bodyhole.stl"); VB, TB = read_stl(stem + "_patchcore.stl")
VA, TA = S._weld(VA, TA, 1e-7); VB, TB = S._weld(VB, TB, 1e-7)
LA, _, _ = S._loops(TA); LB, _, _ = S._loops(TB)
LA = [l for l in LA if len(l) >= 3]; LB = [l for l in LB if len(l) >= 3]
IA = [(VA[l].mean(0), float(np.ptp(VA[l], 0).max())) for l in LA]
IB = [(VB[l].mean(0), float(np.ptp(VB[l], 0).max())) for l in LB]
bad_all = []
for b, lb in enumerate(LB):
    best = None
    for a, la in enumerate(LA):
        d = cKDTree(VA[la]).query(VB[lb])[0]
        s = np.percentile(d, 90)
        if best is None or s < best[0]:
            best = (s, a)
    a = best[1]; la = LA[a]
    PA, QA, sA, cA = S._poly(VA, la)
    t, _ = S._project_param(PA, QA, sA, cA, VB[lb])
    VAc, TAc, VBc, TBc, pairs, worst, far = S._pair_loops_monotone(VA.copy(), TA.copy(), la, VB.copy(), TB.copy(), lb, tol)
    seg_a = VA[np.asarray(la)]; seg_b = VA[np.roll(np.asarray(la), -1)]
    def dist_poly(P):
        out = np.full(len(P), 1e9)
        for i in range(0, len(seg_a), 2000):
            A_ = seg_a[i:i + 2000]; B_ = seg_b[i:i + 2000]; AB = B_ - A_
            t_ = np.clip(np.einsum("pij,ij->pi", P[:, None, :] - A_[None], AB) / np.maximum((AB * AB).sum(1), 1e-18), 0, 1)
            C_ = A_[None] + t_[..., None] * AB[None]
            out = np.minimum(out, np.linalg.norm(P[:, None, :] - C_, axis=2).min(1))
        return out
    dP = dist_poly(VB[lb])
    print("patch loop %d (%d pts, centre %s, size %.1f) <-> body loop %d (%d pts): monotone worst %.3f, beyond tol %d;"
          " orthogonal: max %.3f, beyond tol %d"
          % (b, len(lb), np.round(IB[b][0], 1).tolist(), IB[b][1], a, len(la), worst, far, dP.max(), int((dP > tol).sum())))
    for i in np.where(dP > tol)[0][:10]:
        print("    shape miss at %s  %.3f mm from the body loop" % (np.round(VB[lb][i], 2).tolist(), dP[i]))
        bad_all.append(VB[lb][i])
if bad_all:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    B_ = np.array(bad_all); fig, ax = plt.subplots(1, 3, figsize=(18, 6))
    for k, (i, j) in enumerate(((0, 1), (1, 2), (0, 2))):
        for lb in LB: ax[k].plot(VB[lb][:, i], VB[lb][:, j], ".", ms=1, c="0.6")
        ax[k].plot(B_[:, i], B_[:, j], "r.", ms=6); ax[k].set_aspect("equal")
    fig.savefig(stem + "_seamdiag.png", dpi=80); print("wrote", stem + "_seamdiag.png")

import os, sys, struct
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def write_stl(p, T):
    T = np.asarray(T, dtype=np.float32)
    N = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); L = np.linalg.norm(N, axis=1); N = N / np.maximum(L, 1e-20)[:, None]
    rec = np.zeros(len(T), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    rec["n"] = N; rec["v"] = T.reshape(-1, 9)
    with open(p, "wb") as f:
        f.write(b"the agent _ccneedle".ljust(80, b" ")); f.write(struct.pack("<I", len(T))); f.write(rec.tobytes())


def index(T):
    V, inv = np.unique(np.round(T.reshape(-1, 3), 6), axis=0, return_inverse=True)
    return V, inv.reshape(-1, 3)


def edge_counts(F, nv):
    E = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    k = E[:, 0].astype(np.int64) * (nv + 1) + E[:, 1]
    _, c = np.unique(k, return_counts=True)
    return int((c == 1).sum()), int((c > 2).sum())


inp, outp = sys.argv[1], sys.argv[2]
box = [float(t) for t in sys.argv[3].split()]; lo = np.array(box[0::2]); hi = np.array(box[1::2])
SO = float(os.environ.get("CC_STANDOFF", "0.15")); TURN = float(os.environ.get("CC_TURN", "120"))
TIP = float(os.environ.get("CC_TIPTURN", "150")); TIP2 = float(os.environ.get("CC_TIPTURN2", "135"))
T = read_stl(inp)
V, F = index(T)
N = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); A = np.linalg.norm(N, axis=1)
Nu = N / np.maximum(A, 1e-18)[:, None]
open0, nm0 = edge_counts(F, len(V))
newv = np.ones(len(V), bool)
if os.environ.get("CC_REF"):
    R = read_stl(os.environ["CC_REF"]); RV = np.unique(np.round(R.reshape(-1, 3), 6), axis=0)
    d, _ = cKDTree(RV).query(V, distance_upper_bound=1e-5)
    newv = ~np.isfinite(d)
E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); t = np.tile(np.arange(len(F)), 3)
Es = np.sort(E, 1); key = Es[:, 0].astype(np.int64) * (len(V) + 1) + Es[:, 1]; o = np.argsort(key, kind="stable")
ks = key[o]; ts = t[o]; Eo = Es[o]
same = ks[1:] == ks[:-1]; a = ts[:-1][same]; b = ts[1:][same]; ed = Eo[:-1][same]
ang = np.degrees(np.arccos(np.clip((Nu[a] * Nu[b]).sum(1), -1, 1)))
mid = (V[ed[:, 0]] + V[ed[:, 1]]) / 2
sel = (A[a] > 1e-12) & (A[b] > 1e-12) & (ang > TURN) & np.all((mid >= lo) & (mid <= hi), 1) & (newv[ed[:, 0]] | newv[ed[:, 1]])
P = mid[sel]; EV = ed[sel]; AN = ang[sel]
print("%s: %d triangles, open %d, non-manifold %d; %d folded edge(s) over %.0f deg in the box" % (
    os.path.basename(inp), len(F), open0, nm0, len(P), TURN))
vt = cKDTree(V)
vf_i = F.ravel(); vf_t = np.repeat(np.arange(len(F)), 3); oo = np.argsort(vf_i, kind="stable")
vf_i = vf_i[oo]; vf_t = vf_t[oo]; starts = np.searchsorted(vf_i, np.arange(len(V) + 1))


def tris_of(vs):
    return np.unique(np.concatenate([vf_t[starts[v]:starts[v + 1]] for v in vs])) if len(vs) else np.zeros(0, int)


def loops_of(Fr):
    # boundary edges
    D = np.vstack([Fr[:, [0, 1]], Fr[:, [1, 2]], Fr[:, [2, 0]]])
    k = np.sort(D, 1); kk = k[:, 0].astype(np.int64) * (len(V) + 1) + k[:, 1]
    u, inv_, c = np.unique(kk, return_inverse=True, return_counts=True)
    bd = D[c[inv_] == 1]
    nxt = {}
    for s, e in bd:
        if s in nxt:
            return None
        nxt[int(s)] = int(e)
    loops = []; seen = set()
    for s in list(nxt):
        if s in seen:
            continue
        l = [s]; seen.add(s); cur = nxt[s]
        while cur != s:
            if cur in seen or cur not in nxt:
                return None
            l.append(cur); seen.add(cur); cur = nxt[cur]
        loops.append(l)
    return loops


def earclip(P2):
    idx = list(range(len(P2))); out = []
    area = 0.5 * np.sum(P2[:, 0] * np.roll(P2[:, 1], -1) - np.roll(P2[:, 0], -1) * P2[:, 1])
    sgn = 1.0 if area > 0 else -1.0
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1; done = False
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            p0, p1, p2 = P2[i0], P2[i1], P2[i2]
            cr = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])
            if cr * sgn <= 1e-12:
                continue
            ok = True
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                q = P2[j]
                d1 = (p1[0] - p0[0]) * (q[1] - p0[1]) - (p1[1] - p0[1]) * (q[0] - p0[0])
                d2 = (p2[0] - p1[0]) * (q[1] - p1[1]) - (p2[1] - p1[1]) * (q[0] - p1[0])
                d3 = (p0[0] - p2[0]) * (q[1] - p2[1]) - (p0[1] - p2[1]) * (q[0] - p2[0])
                if d1 * sgn >= 0 and d2 * sgn >= 0 and d3 * sgn >= 0:
                    ok = False; break
            if ok:
                out.append((i0, i1, i2)); idx.pop(k); done = True; break
        if not done:
            return None
    if len(idx) == 3:
        out.append(tuple(idx))
    return out


removed = np.zeros(len(F), bool); newtris = []; ncut = 0
if len(P):
    tr = cKDTree(P); pairs = tr.query_pairs(0.6, output_type="ndarray")
    G = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(P), len(P)))
    nc, lab = connected_components(G, directed=False)
    for c in range(nc):
        cv = np.unique(EV[lab == c].ravel()); cpts = V[cv]; cen = cpts.mean(0)
        ring = np.array([i for i in vt.query_ball_point(cen, 1.5) if np.linalg.norm(V[i] - cen) > 0.5 and i not in set(cv)])
        if len(ring) < 12:
            continue
        Rg = V[ring]; mu = Rg.mean(0); _, _, Wt = np.linalg.svd(Rg - mu); nrm = Wt[2]; e1 = Wt[0]; e2 = Wt[1]
        u = (Rg - mu) @ e1; v = (Rg - mu) @ e2; h = (Rg - mu) @ nrm
        M = np.c_[u * u, u * v, v * v, u, v, np.ones_like(u)]; coef, *_ = np.linalg.lstsq(M, h, rcond=None)
        fit = float(np.percentile(np.abs(M @ coef - h), 95))
        uc = (cpts - mu) @ e1; vc = (cpts - mu) @ e2; hc = (cpts - mu) @ nrm
        off = np.abs(np.c_[uc * uc, uc * vc, vc * vc, uc, vc, np.ones_like(uc)] @ coef - hc)
        so = float(off.max()); mt = float(AN[lab == c].max()); ext = float(np.linalg.norm(cpts.max(0) - cpts.min(0)))
        if so < SO or fit > 0.5 * so:
            continue
        if mt < TIP and not (mt >= TIP2 and ext <= 1.2 * so + 0.6):
            print("  cluster at x %.2f y %.2f z %.2f: stand-off %.3f mm, %.2f mm long, but its sharpest fold turns only %.0f deg - "
                  "a crease, not a fin; NOT cut" % (cen[0], cen[1], cen[2], so, ext, mt)); continue
        vs = set(cv.tolist()); good = None
        for grow in range(6):
            ft = tris_of(np.array(sorted(vs)))
            ft = ft[~removed[ft]]
            lp = loops_of(F[ft])
            if lp is not None and len(lp) == 1:
                L = np.array(lp[0]); q = V[L]
                uq = (q - mu) @ e1; vq = (q - mu) @ e2; hq = (q - mu) @ nrm
                offq = np.abs(np.c_[uq * uq, uq * vq, vq * vq, uq, vq, np.ones_like(uq)] @ coef - hq)
                if offq.max() < max(0.05, 2 * fit):
                    P2 = np.c_[(q - mu) @ e1, (q - mu) @ e2]
                    ec = earclip(P2)
                    if ec is not None:
                        good = (ft, L, ec); break
            vs |= set(F[ft].ravel().tolist())
        if good is None:
            print("  cluster at x %.2f y %.2f z %.2f: stand-off %.3f mm (fit %.3f) - NOT cut, no clean single loop" % (
                cen[0], cen[1], cen[2], so, fit)); continue
        ft, L, ec = good
        tri_new = [(L[i], L[j], L[k]) for i, j, k in ec]
        rm2 = removed.copy(); rm2[ft] = True
        Ftest = np.vstack([F[~rm2], np.array(newtris + tri_new)])
        o1, n1 = edge_counts(Ftest, len(V))
        if o1 > open0 or n1 > nm0:
            print("  cluster at x %.2f y %.2f z %.2f: stand-off %.3f mm - NOT cut, the fill would raise open %d->%d / nm %d->%d" % (
                cen[0], cen[1], cen[2], so, open0, o1, nm0, n1)); continue
        removed[ft] = True; newtris += tri_new; ncut += 1
        print("  CUT needle at x %.2f y %.2f z %.2f: stand-off %.3f mm off a surround fitting to %.3f, tip fold %.0f deg, %.2f mm long; %d triangle(s) out, %d in" % (
            cen[0], cen[1], cen[2], so, fit, mt, ext, len(ft), len(tri_new)))
Fo = np.vstack([F[~removed]] + ([np.array(newtris)] if newtris else []))
o2, n2 = edge_counts(Fo, len(V))
print("result: %d triangles, open %d (was %d), non-manifold %d (was %d); %d needle(s) cut" % (
    len(Fo), o2, open0, n2, nm0, ncut))
if o2 > open0 or n2 > nm0:
    print("REFUSED: topology would worsen"); sys.exit(2)
if os.environ.get("CC_DRY") != "1":
    write_stl(outp, V[Fo]); print("wrote", outp)
sys.exit(0 if removed.any() else 3)

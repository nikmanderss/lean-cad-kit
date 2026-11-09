# open edges
import os, sys, struct, json
import numpy as np


def say(*a):
    print(*a, flush=True)


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def write_stl(p, V, T):
    tri = V[T].astype(np.float32)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1
    rec = np.zeros(len(tri), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    rec["n"] = n / ln[:, None]; rec["v"] = tri.reshape(-1, 9)
    with open(p, "wb") as f:
        f.write(b"the agent nmfix".ljust(80, b" ")); f.write(struct.pack("<I", len(tri))); f.write(rec.tobytes())


def counts(T):
    e = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
    _, c = np.unique(e, axis=0, return_counts=True)
    return int((c == 1).sum()), int((c > 2).sum())


tri = read_stl(os.environ["CC_IN"])
q = np.round(tri.reshape(-1, 3) / 1e-6).astype(np.int64)
u_, inv = np.unique(q, axis=0, return_inverse=True)
V = u_ * 1e-6; T = inv.reshape(-1, 3)
T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
o0, n0 = counts(T)
say("in : %d triangles, open %d, non-manifold %d" % (len(T), o0, n0))
nT = len(T)
E = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
Es = np.sort(E, 1)
ue, ei, ec = np.unique(Es, axis=0, return_inverse=True, return_counts=True)
ei = ei.ravel()
joined = {}
tri_of = {}
for j, k in enumerate(ei):
    tri_of.setdefault(k, []).append(j % nT)
Nrm = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
Nrm /= np.linalg.norm(Nrm, axis=1)[:, None] + 1e-30
bad_edges = 0
refmid = None
if os.environ.get("CC_REF"):
    from scipy.spatial import cKDTree
    rt = read_stl(os.environ["CC_REF"]); rq = np.round(rt.reshape(-1, 3) / 1e-6).astype(np.int64)
    ru, rinv = np.unique(rq, axis=0, return_inverse=True); RT = rinv.reshape(-1, 3)
    re_ = np.sort(np.vstack([RT[:, [0, 1]], RT[:, [1, 2]], RT[:, [2, 0]]]), 1)
    rue, rc = np.unique(re_, axis=0, return_counts=True); rn = rue[rc > 2]
    refmid = cKDTree((ru[rn[:, 0]] + ru[rn[:, 1]]) * 0.5e-6) if len(rn) else None
    say("reference %s: %d non-manifold edge(s) of its own, left joined" % (os.path.basename(os.environ["CC_REF"]), len(rn)))
kept_ref = 0
for k, ts in tri_of.items():
    if len(ts) == 2:
        joined[k] = [tuple(ts)]
    elif len(ts) > 2 and refmid is not None and refmid.query((V[ue[k][0]] + V[ue[k][1]]) * 0.5)[0] < 1e-5:
        joined[k] = [(ts[0], t_) for t_ in ts[1:]]; kept_ref += 1
    elif len(ts) > 2:
        a, b = ue[k]
        ax = V[b] - V[a]; ax /= np.linalg.norm(ax) + 1e-30
        r0 = np.cross(ax, [1.0, 0.0, 0.0])
        if np.linalg.norm(r0) < 0.1:
            r0 = np.cross(ax, [0.0, 1.0, 0.0])
        r0 /= np.linalg.norm(r0); r1 = np.cross(ax, r0)
        ang = []
        for t in ts:
            w = [x for x in T[t] if x != a and x != b][0]
            d = V[w] - V[a]
            ang.append(np.arctan2(d @ r1, d @ r0))
        sides = []
        for t, a_ in zip(ts, ang):
            tau = -np.sin(a_) * r0 + np.cos(a_) * r1
            sides.append(1 if (-Nrm[t]) @ tau > 0 else -1)
        order = sorted(range(len(ts)), key=lambda i: (round(ang[i], 6), sides[i]))
        ts_s = [ts[i] for i in order]; an_s = [ang[i] for i in order]
        m = len(ts_s)
        best = None
        for off in (0, 1):
            pairs = [(ts_s[(off + 2 * i) % m], ts_s[(off + 2 * i + 1) % m],
                      an_s[(off + 2 * i) % m], an_s[(off + 2 * i + 1) % m]) for i in range(m // 2)]
            ok = 0
            for tA, tB, aA, aB in pairs:
                mid = 0.5 * (aA + aB) + (np.pi if aB < aA else 0.0)
                bis = np.cos(mid) * r0 + np.sin(mid) * r1
                if Nrm[tA] @ bis < 0 and Nrm[tB] @ bis < 0:
                    ok += 1
            if best is None or ok > best[0]:
                best = (ok, pairs)
        joined[k] = [(p[0], p[1]) for p in best[1]]
        if best[0] < len(best[1]):
            bad_edges += 1
adj = {}
for k, prs in joined.items():
    a, b = ue[k]
    for tA, tB in prs:
        adj.setdefault(a, []).append((tA, tB)); adj.setdefault(b, []).append((tA, tB))
vt = {}
for t in range(nT):
    for x in T[t]:
        vt.setdefault(int(x), []).append(t)
newV = [V.copy()]; T2 = T.copy(); nxt = len(V); split = 0; moved = {}
NUDGE = float(os.environ.get("CC_NUDGE", "0.002"))
for x, ts in vt.items():
    if len(ts) < 2:
        continue
    parent = {t: t for t in ts}
    def f(t):
        while parent[t] != t:
            parent[t] = parent[parent[t]]; t = parent[t]
        return t
    for tA, tB in adj.get(x, []):
        if tA in parent and tB in parent:
            ra, rb = f(tA), f(tB)
            if ra != rb:
                parent[rb] = ra
    roots = {}
    for t in ts:
        roots.setdefault(f(t), []).append(t)
    if len(roots) < 2:
        continue
    for i, (rt, group) in enumerate(roots.items()):
        nm_ = -Nrm[group].sum(0); ln_ = np.linalg.norm(nm_)
        disp = (NUDGE * nm_ / ln_) if ln_ > 1e-9 else np.zeros(3)
        if i == 0:
            moved[x] = disp
            continue
        newV.append((V[x] + disp)[None]); split += 1
        for t in group:
            T2[t][T2[t] == x] = nxt
        nxt += 1
V2 = np.vstack(newV)
for x, d_ in moved.items():
    V2[x] = V2[x] + d_
o1, n1 = counts(T2)
say("out: %d triangles (none removed), open %d, non-manifold %d; vertices split %d; edges whose pairing could not"
    " close every wedge %d; the reference's own left joined %d" % (len(T2), o1, n1, split, bad_edges, kept_ref))
write_stl(os.environ["CC_OUT"], V2, T2)
json.dump({"in": [len(T), o0, n0], "out": [len(T2), o1, n1], "split": split, "unpaired_wedges": bad_edges},
          open(os.environ["CC_OUT"] + ".json", "w"), indent=1)
say("wrote %s" % os.environ["CC_OUT"])

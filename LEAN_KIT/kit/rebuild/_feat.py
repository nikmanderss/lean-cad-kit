# kit rebuild
# over the
import numpy as np
from scipy.spatial import cKDTree


def _unit(v):
    return v / np.maximum(np.linalg.norm(v, axis=1), 1e-12)[:, None]


def feature_edges(VB, TB, deg=25.0, planes=(), ptol=1e-3, normals=False):
    """The base mesh's sharp edges: edges shared by two triangles whose normals differ by >= deg, split into CONVEX
    (the far vertex of the second triangle lies behind the first's plane - material inside, outward normals) and CONCAVE.
    Edges with both ends in one of `planes` [(c, n), ...] (the window walls: the base is cut there, not shaped) are dropped.
    Returns (convex, concave): (k, 2) arrays of vertex ids into VB - or, with normals=True, ((segs, nA, nB), ...) with
    the two face normals of every segment."""
    n = _unit(np.cross(VB[TB[:, 1]] - VB[TB[:, 0]], VB[TB[:, 2]] - VB[TB[:, 0]]))
    e = np.vstack([TB[:, [0, 1]], TB[:, [1, 2]], TB[:, [2, 0]]]); es = np.sort(e, axis=1); et = np.tile(np.arange(len(TB)), 3)
    o = np.lexsort((es[:, 1], es[:, 0])); es = es[o]; et = et[o]
    same = np.all(es[1:] == es[:-1], axis=1); pa = et[:-1][same]; pb = et[1:][same]; ea = es[:-1][same]
    sharp = np.einsum("ij,ij->i", n[pa], n[pb]) < np.cos(np.radians(deg))
    pa, pb, ea = pa[sharp], pb[sharp], ea[sharp]
    if not len(ea):
        return np.zeros((0, 2), int), np.zeros((0, 2), int)
    tb = TB[pb]; m = (tb != ea[:, [0]]) & (tb != ea[:, [1]]); far = tb[np.arange(len(tb)), np.argmax(m, axis=1)]
    convex = np.einsum("ij,ij->i", VB[far] - VB[ea[:, 0]], n[pa]) < 0
    keep = np.ones(len(ea), bool)
    for c, nn in planes:
        c = np.asarray(c, float); nn = np.asarray(nn, float); nn = nn / np.linalg.norm(nn)
        keep &= ~((np.abs((VB[ea[:, 0]] - c) @ nn) < ptol) & (np.abs((VB[ea[:, 1]] - c) @ nn) < ptol))
    if normals:
        cv = convex & keep; cc = ~convex & keep
        return (ea[cv], n[pa][cv], n[pb][cv], pa[cv], pb[cv]), (ea[cc], n[pa][cc], n[pb][cc], pa[cc], pb[cc])
    return ea[convex & keep], ea[~convex & keep]


def face_regions(VB, TB, deg=25.0):
    """label every base triangle by the FACE it belongs to: triangles connected across edges that are not sharp (< deg)"""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    n = _unit(np.cross(VB[TB[:, 1]] - VB[TB[:, 0]], VB[TB[:, 2]] - VB[TB[:, 0]]))
    e = np.vstack([TB[:, [0, 1]], TB[:, [1, 2]], TB[:, [2, 0]]]); es = np.sort(e, axis=1); et = np.tile(np.arange(len(TB)), 3)
    o = np.lexsort((es[:, 1], es[:, 0])); es = es[o]; et = et[o]
    same = np.all(es[1:] == es[:-1], axis=1); pa = et[:-1][same]; pb = et[1:][same]
    smooth = np.einsum("ij,ij->i", n[pa], n[pb]) >= np.cos(np.radians(deg))
    g = coo_matrix((np.ones(int(smooth.sum())), (pa[smooth], pb[smooth])), shape=(len(TB), len(TB)))
    return connected_components(g, directed=False)[1]


class EdgeLocator:
    """the closest point on a set of base segments, by a KD-tree of dense samples (spacing sp) + the exact projection
    onto the sample's own segment; nA / nB (optional) are the two face normals of every segment"""
    def __init__(self, VB, segs, sp, nA=None, nB=None, rA=None, rB=None):
        self.segs = np.asarray(segs, int); self.nA = nA; self.nB = nB; self.rA = rA; self.rB = rB
        self.A = VB[segs[:, 0]]; self.B = VB[segs[:, 1]]; d = self.B - self.A; self.L2 = np.maximum(np.einsum("ij,ij->i", d, d), 1e-18)
        P = []; S = []
        for k in range(len(segs)):
            m = max(2, int(np.ceil(np.sqrt(self.L2[k]) / sp)) + 1); t = np.linspace(0.0, 1.0, m)[:, None]
            P.append(self.A[k] + d[k] * t); S.append(np.full(m, k))
        self.P = np.vstack(P) if P else np.zeros((0, 3)); self.S = np.concatenate(S) if S else np.zeros(0, int)
        self.kd = cKDTree(self.P) if len(self.P) else None
        self.n = len(segs)

    def nearest(self, X):
        """(distance to the nearest segment, the closest point on it, the segment id) for every row of X"""
        if self.kd is None or not len(X):
            return np.full(len(X), np.inf), np.asarray(X, float).copy(), np.full(len(X), -1)
        _, j = self.kd.query(X, workers=-1); k = self.S[j]
        d = self.B[k] - self.A[k]; t = np.clip(np.einsum("ij,ij->i", X - self.A[k], d) / self.L2[k], 0.0, 1.0)
        Q = self.A[k] + d * t[:, None]
        return np.linalg.norm(X - Q, axis=1), Q, k


def restore(V, T, ipd, loc, side, reach, depth, snap, where=None, label="convex", say=print):
    """Put back the vertices of (V, T) that cut a sharp edge of the base. `ipd`: vtkImplicitPolyDataDistance on the base
    (negative INSIDE the base); `loc`: EdgeLocator over the base's convex (side=+1) or concave (side=-1) feature edges.
    A candidate lies on the wrong side of the base by more than `snap` and at most `depth` (deeper is the opening's work
    or a removed lump - not a corner cut), within `reach` of an edge, and (where given) inside one of the boxes `where`
    [[x0 x1 y0 y1 z0 z1], ...]. Nearest-to-the-edge first, each candidate goes ONTO the edge unless that would put all three
    vertices of a triangle on it (degenerate) - then onto the base face it belongs to (the closest surface point); a move
    that would fold or collapse a triangle is not taken. Returns (V', stats)."""
    V = np.asarray(V, float).copy(); T = np.asarray(T, int)
    st = {"label": label, "candidates": 0, "to_edge": 0, "to_face": 0, "refused_fold": 0, "left": 0, "depth_before_p50": 0.0, "depth_before_max": 0.0}
    if loc.n == 0 or not len(V):
        say("  feature restore (%s): no edges" % label); return V, st
    de, Q, _ = loc.nearest(V)
    near = de <= reach
    if where is not None and len(where):
        inb = np.zeros(len(V), bool)
        for b in where:
            inb |= (V[:, 0] >= b[0]) & (V[:, 0] <= b[1]) & (V[:, 1] >= b[2]) & (V[:, 1] <= b[3]) & (V[:, 2] >= b[4]) & (V[:, 2] <= b[5])
        near &= inb
    idx = np.nonzero(near)[0]
    if not len(idx):
        say("  feature restore (%s): no vertex within %.2f mm of an edge" % (label, reach)); return V, st
    cp = [0.0, 0.0, 0.0]; dsg = np.zeros(len(idx)); CP = np.zeros((len(idx), 3))
    for a, i in enumerate(idx):
        dsg[a] = ipd.EvaluateFunctionAndGetClosestPoint(V[i], cp); CP[a] = cp
    wrong = (-dsg * side > snap) & (-dsg * side <= depth)
    cand = idx[wrong]; CPc = CP[wrong]; dec = de[cand]
    st["candidates"] = int(len(cand))
    if not len(cand):
        say("  feature restore (%s): %d vertices near an edge, none cut it by more than %.3f mm" % (label, len(idx), snap)); return V, st
    st["depth_before_p50"] = round(float(np.percentile(np.abs(dsg[wrong]), 50)), 4); st["depth_before_max"] = round(float(np.abs(dsg[wrong]).max()), 4)
    order = np.argsort(T.ravel()); vidx = T.ravel()[order]; tidx = np.repeat(np.arange(len(T)), 3)[order]
    starts = np.searchsorted(vidx, np.arange(len(V) + 1))
    online = np.zeros(len(V), bool)
    def tri_n(tl):
        P = V[T[tl]]; return np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    def try_move(i, q, tl, n0):
        old = V[i].copy(); V[i] = q; n1 = tri_n(tl); a0 = np.linalg.norm(n0, axis=1); a1 = np.linalg.norm(n1, axis=1)
        if np.any(np.einsum("ij,ij->i", n0, n1) <= 0.0) or np.any(a1 < 0.05 * np.maximum(a0, 1e-12)):
            V[i] = old; return False
        return True
    for a in np.argsort(dec):
        i = int(cand[a]); tl = tidx[starts[i]:starts[i + 1]]; n0 = tri_n(tl)
        degenerate = False
        for t in tl:
            if all(online[v] or v == i for v in T[t]): degenerate = True; break
        if not degenerate and try_move(i, Q[i], tl, n0):
            online[i] = True; st["to_edge"] += 1
        elif try_move(i, CPc[a], tl, n0):
            st["to_face"] += 1
        else:
            st["refused_fold"] += 1
    st["left"] = st["candidates"] - st["to_edge"] - st["to_face"] - st["refused_fold"]
    say("  feature restore (%s): %d vertices cut a sharp edge by %.3f-%.3f mm (p50 %.3f): %d put back ON the edge, %d onto their face, %d refused (a triangle would fold)"
        % (label, st["candidates"], snap, st["depth_before_max"], st["depth_before_p50"], st["to_edge"], st["to_face"], st["refused_fold"]))
    return V, st


def pull_chords(V, T, ipd, loc, side, reach, snap, where=None, label="convex", say=print, passes=4):
    """THE CHORD PULL. The marching-cubes vertices all lie ON the base's faces (the field is exact there), so what cuts a
    sharp edge is not a vertex but a TRIANGLE that spans the corner: a mesh edge from face A to face B whose chord dips
    inside the material (measured on a section: 42 % of the edge samples outside the piece with only 208 vertices inside
    it). Every such chord - its midpoint on the wrong side of the base by more than `snap`, within `reach` of a sharp
    edge - is removed by moving the chord's end that is nearer the sharp edge ONTO it: the chord then lies in one face.
    A move that makes a triangle degenerate (its three vertices on the edge line, the middle one between the other two)
    is taken and the triangle dissolved: it is dropped and its neighbour across the outer edge is split at the middle
    vertex, which keeps the mesh closed and manifold. A move that would fold a triangle is not taken. Nearest first,
    repeated until no chord dips (at most `passes`). Returns (V', T', stats)."""
    V = np.asarray(V, float).copy(); T0 = np.asarray(T, int)
    st = {"label": label, "passes": 0, "chords": 0, "moved": 0, "dissolved": 0, "split": 0, "refused": 0, "chords_left": 0}
    if loc.n == 0 or not len(V):
        return V, T0.copy(), st
    tris = [list(map(int, t)) for t in T0]; alive = [True] * len(tris)
    inc = [set() for _ in range(len(V))]
    for k, t in enumerate(tris):
        for v in t: inc[v].add(k)
    de_v, Q_v, _ = loc.nearest(V); online = de_v < 1e-6
    S = {"V": V, "de": de_v, "Q": Q_v, "on": online}
    def split_chord(u, v):
        """the chord u-v is split by a new vertex ON the line (the point nearest its midpoint); the two triangles on it
        become four. No vertex moves, so nothing can fold. Refused when the line point is not between the chord's ends
        or coincides with a vertex, or the edge is not on exactly two live triangles."""
        V = S["V"]; both = [k for k in inc[u] & inc[v] if alive[k]]
        if len(both) != 2: return False
        m0 = 0.5 * (V[u] + V[v]); dq, q, _ = loc.nearest(m0[None, :]); q = q[0]
        d = V[v] - V[u]; L2 = float(d @ d)
        if L2 < 1e-18: return False
        tt = float((q - V[u]) @ d) / L2
        if not (0.05 < tt < 0.95): return False
        for k in both:
            for w in tris[k]:
                if np.linalg.norm(V[w] - q) < 1e-6: return False
        m = len(V); S["V"] = np.vstack([V, q[None, :]]); S["de"] = np.append(S["de"], 0.0); S["Q"] = np.vstack([S["Q"], q[None, :]]); S["on"] = np.append(S["on"], True)
        inc.append(set())
        for k in both:
            t = tris[k]; i_u = t.index(u); fwd = t[(i_u + 1) % 3] == v; w = [x for x in t if x not in (u, v)][0]
            n_t = np.cross(S["V"][t[1]] - S["V"][t[0]], S["V"][t[2]] - S["V"][t[0]])
            new1 = [u, m, w] if fwd else [v, m, w]; new2 = [m, v, w] if fwd else [m, u, w]
            alive[k] = False
            for x in t: inc[x].discard(k)
            for nt in (new1, new2):
                tris.append(nt); alive.append(True); kk = len(tris) - 1
                for x in nt: inc[x].add(kk)
        st["split"] += 1
        return True
    def area_n(t):
        P = S["V"][t]; return np.cross(P[1] - P[0], P[2] - P[0])
    def other_tri(p, r, not_k):
        for k in inc[p] & inc[r]:
            if k != not_k and alive[k]: return k
        return None
    def dissolve(k):
        """the degenerate triangle k (three vertices on the line): drop it, split its outer-edge neighbour at the middle vertex"""
        V = S["V"]; online = S["on"]; t = tris[k]; P = V[t]
        best = None
        for m in range(3):
            p, r = t[(m + 1) % 3], t[(m + 2) % 3]; d = V[r] - V[p]; L2 = float(d @ d)
            if L2 < 1e-18: return False
            tt = float((V[t[m]] - V[p]) @ d) / L2
            if 1e-6 < tt < 1 - 1e-6 and np.linalg.norm(V[t[m]] - (V[p] + d * tt)) < 1e-6: best = (t[m], p, r); break
        if best is None: return False
        q, p, r = best; u = other_tri(p, r, k)
        if u is None: return False
        tu = tris[u]
        if all(online[v] for v in tu): return False
        x = [v for v in tu if v not in (p, r)]
        if len(x) != 1: return False
        x = x[0]; i_p = tu.index(p); fwd = tu[(i_p + 1) % 3] == r
        n_u = area_n(tu); new1 = [p, q, x] if fwd else [r, q, x]; new2 = [q, r, x] if fwd else [q, p, x]
        if float(area_n(new1) @ n_u) <= 0 or float(area_n(new2) @ n_u) <= 0: return False
        def count(a_, b_, skip):
            return sum(1 for kk in inc[a_] & inc[b_] if alive[kk] and kk not in skip)
        if count(q, x, (k, u)) != 0 or count(p, q, (k, u)) != 1 or count(q, r, (k, u)) != 1 or count(p, x, (k, u)) != 1 or count(r, x, (k, u)) != 1:
            return False
        alive[k] = False; alive[u] = False
        for v in t: inc[v].discard(k)
        for v in tu: inc[v].discard(u)
        for nt in (new1, new2):
            tris.append(nt); alive.append(True); kk = len(tris) - 1
            for v in nt: inc[v].add(kk)
        st["dissolved"] += 1
        return True
    def try_move(i, target=None, retry=True):
        V = S["V"]; Q_v = S["Q"]; online = S["on"]; de_v = S["de"]
        tl = [k for k in inc[i] if alive[k]]
        n0 = [area_n(tris[k]) for k in tl]; old = V[i].copy(); V[i] = Q_v[i] if target is None else target
        if retry:
            alts = []
            for k in tl:
                t = tris[k]; ab = [v for v in t if v != i and online[v]]
                if len(ab) == 2:
                    a_, b_ = ab; d = V[b_] - V[a_]; L2 = float(d @ d)
                    if L2 > 1e-18:
                        tt = min(max(float((old - V[a_]) @ d) / L2, 0.05), 0.95); alts.append(V[a_] + d * tt)
            V[i] = old
            if try_move(i, None, False): return True
            for q in sorted(alts, key=lambda q: float(np.linalg.norm(q - old))):
                if try_move(i, q, False): return True
            return False
        degen = []
        for k, nn0 in zip(tl, n0):
            t = tris[k]; nn1 = area_n(t); a0 = np.linalg.norm(nn0); a1 = np.linalg.norm(nn1)
            if all(online[v] or v == i for v in t) and a1 < 1e-6 * max(a0, 1e-12) + 1e-12:
                degen.append(k); continue
            if float(nn0 @ nn1) <= 0.0 or a1 < 0.05 * max(a0, 1e-12):
                V[i] = old; return False
        online[i] = True; de_v[i] = 0.0
        for k in degen:
            if alive[k] and not dissolve(k):
                V[i] = old; online[i] = False; de_v[i] = float(loc.nearest(V[i:i + 1])[0][0]); return False
        return True
    for p in range(passes):
        V = S["V"]; de_v = S["de"]; online = S["on"]
        E = set()
        for k, t in enumerate(tris):
            if not alive[k]: continue
            for a_, b_ in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])): E.add((min(a_, b_), max(a_, b_)))
        E = np.array(sorted(E), int)
        mid = 0.5 * (V[E[:, 0]] + V[E[:, 1]]); de, _, _ = loc.nearest(mid); near = de <= reach
        if where is not None and len(where):
            inb = np.zeros(len(E), bool)
            for b in where:
                inb |= (mid[:, 0] >= b[0]) & (mid[:, 0] <= b[1]) & (mid[:, 1] >= b[2]) & (mid[:, 1] <= b[3]) & (mid[:, 2] >= b[4]) & (mid[:, 2] <= b[5])
            near &= inb
        idx = np.nonzero(near)[0]
        if not len(idx): break
        d = np.array([ipd.EvaluateFunction(mid[i]) for i in idx]); dip = idx[(-d * side) > snap]
        if p == 0: st["chords"] = int(len(dip))
        st["chords_left"] = int(len(dip))
        if not len(dip): break
        st["passes"] = p + 1
        u, v = E[dip, 0], E[dip, 1]; nearer = de_v[u] <= de_v[v]; pick = np.where(nearer, u, v); far = np.where(nearer, v, u)
        partner = {}
        for a_, b_ in zip(pick, far): partner.setdefault(int(a_), []).append(int(b_))
        cand = np.unique(pick); cand = cand[~online[cand]]; cand = cand[np.argsort(de_v[cand])]
        moved = 0
        for i in cand:
            i = int(i)
            if S["on"][i]: continue
            if try_move(i): moved += 1; continue
            done = False
            for j in partner.get(i, []):
                if not S["on"][j] and S["de"][j] <= reach and try_move(j): moved += 1; done = True; break
            if not done:
                for j in partner.get(i, []):
                    if split_chord(i, j): moved += 1; done = True
            if not done: st["refused"] += 1
        st["moved"] += moved
        if moved == 0: break
    V = S["V"]
    T = np.array([t for k, t in enumerate(tris) if alive[k]], int)
    say("  chord pull (%s): %d spanning chords; %d vertices moved onto the edge in %d pass(es), %d degenerate triangles dissolved, %d chords split at the edge, %d refused; %d chords left; %d vertices, %d triangles now"
        % (label, st["chords"], st["moved"], st["passes"], st["dissolved"], st["split"], st["refused"], st["chords_left"], len(V), len(T)))
    return V, T, st


def corners_of(VB, segs, deg=25.0):
    """the base's sharp CORNERS on its feature edges: a vertex where the feature polyline ends, branches, or turns by
    more than deg - a piece whose vertices all lie on the faces still caps such a corner with a flat triangle"""
    if not len(segs): return np.zeros((0, 3))
    inc = {}
    for k, (a, b) in enumerate(segs):
        inc.setdefault(int(a), []).append(k); inc.setdefault(int(b), []).append(k)
    out = []
    for v, ks in inc.items():
        if len(ks) != 2: out.append(v); continue
        d = []
        for k in ks:
            a, b = segs[k]; o = b if a == v else a; vec = VB[o] - VB[v]; d.append(vec / max(np.linalg.norm(vec), 1e-12))
        if float(d[0] @ d[1]) > -np.cos(np.radians(deg)): out.append(v)
    return VB[np.array(out, int)] if out else np.zeros((0, 3))


def pull_corners(V, T, piece_poly_fn, C, side, reach, snap, label="convex", say=print, passes=2):
    """every sharp corner of the base that the piece cuts (lies on the wrong side of the piece by more than snap, with no
    piece vertex within snap of it) gets the nearest piece vertex within reach moved onto it (no fold). Returns (V', stats)."""
    V = np.asarray(V, float).copy(); T = np.asarray(T, int)
    st = {"label": label, "corners": int(len(C)), "cut": 0, "moved": 0, "refused": 0}
    if not len(C) or not len(V): return V, st
    order = np.argsort(T.ravel()); vidx = T.ravel()[order]; tidx = np.repeat(np.arange(len(T)), 3)[order]
    starts = np.searchsorted(vidx, np.arange(len(V) + 1))
    def tri_n(tl):
        P = V[T[tl]]; return np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    kd = cKDTree(V)
    for p in range(passes):
        f = piece_poly_fn(V, T)
        dpc = np.array([f.EvaluateFunction(c) for c in C])
        cut = np.nonzero((dpc * side) > snap)[0]
        if p == 0: st["cut"] = int(len(cut))
        if not len(cut): break
        moved = 0
        for ci in cut:
            c = C[ci]; dd, jj = kd.query(c, k=4)
            if dd[0] <= snap: continue
            ok = False
            for d_, j in zip(dd, jj):
                if d_ > reach: break
                j = int(j); tl = tidx[starts[j]:starts[j + 1]]; n0 = tri_n(tl); old = V[j].copy(); V[j] = c; n1 = tri_n(tl)
                a0 = np.linalg.norm(n0, axis=1); a1 = np.linalg.norm(n1, axis=1)
                if np.any(np.einsum("ij,ij->i", n0, n1) <= 0.0) or np.any(a1 < 0.05 * np.maximum(a0, 1e-12)): V[j] = old; continue
                ok = True; moved += 1; break
            if not ok: st["refused"] += 1
        st["moved"] += moved
        kd = cKDTree(V)
        if moved == 0: break
    say("  corner pull (%s): %d sharp corners, %d cut by the piece, %d given a vertex, %d refused (a fold)" % (label, st["corners"], st["cut"], st["moved"], st["refused"]))
    return V, st


def pull_edges(V, T, piece_poly_fn, loc, side, reach, snap, label="convex", say=print, passes=3):
    """THE EDGE SWEEP - the restore judged by the thing the gate measures: every sample of the base's sharp edges (loc.P,
    h/4 apart) that lies on the wrong side of the piece by more than `snap` gets the nearest piece vertex within `reach`
    moved onto it (no fold). This catches what the chord pull cannot see: a thin wedge the grid field itself rounds (a 29
    deg wedge loses its last ~0.4 mm at h 0.2 - the field, not the triangulation), and a crest capped by triangles whose
    vertices all sit on the faces. Returns (V', stats)."""
    V = np.asarray(V, float).copy(); T = np.asarray(T, int)
    st = {"label": label, "samples": int(len(loc.P)), "cut_before": 0, "moved": 0, "refused": 0, "cut_after": 0}
    if loc.n == 0 or not len(V): return V, st
    order = np.argsort(T.ravel()); vidx = T.ravel()[order]; tidx = np.repeat(np.arange(len(T)), 3)[order]
    starts = np.searchsorted(vidx, np.arange(len(V) + 1))
    def tri_n(tl):
        P = V[T[tl]]; return np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    P = loc.P
    for p in range(passes + 1):
        f = piece_poly_fn(V, T); dpc = np.array([f.EvaluateFunction(c) for c in P])
        cut = np.nonzero((dpc * side) > snap)[0]
        if p == 0: st["cut_before"] = int(len(cut))
        st["cut_after"] = int(len(cut))
        if not len(cut) or p == passes: break
        kd = cKDTree(V); taken = np.zeros(len(V), bool); moved = 0
        for ci in cut[np.argsort(-dpc[cut] * side)]:
            c = P[ci]; dd, jj = kd.query(c, k=6)
            if dd[0] <= snap: continue
            ok = False
            for d_, j in zip(dd, jj):
                if d_ > reach: break
                j = int(j)
                if taken[j]: continue
                tl = tidx[starts[j]:starts[j + 1]]; n0 = tri_n(tl); old = V[j].copy(); V[j] = c; n1 = tri_n(tl)
                a0 = np.linalg.norm(n0, axis=1); a1 = np.linalg.norm(n1, axis=1)
                cosn = np.einsum("ij,ij->i", n0, n1) / np.maximum(a0 * a1, 1e-18)
                if np.any(cosn <= 0.34) or np.any(a1 < 0.05 * np.maximum(a0, 1e-12)): V[j] = old; continue
                taken[j] = True; ok = True; moved += 1; break
            if not ok: st["refused"] += 1
        st["moved"] += moved
        if moved == 0: break
    say("  edge sweep (%s): %d edge samples, %d cut by the piece before, %d vertices moved onto them, %d refused (a fold); %d still cut" % (label, st["samples"], st["cut_before"], st["moved"], st["refused"], st["cut_after"]))
    return V, st


def insert_crest(V, T, loc, reach, snap, ipd=None, say=print, label="convex", lift_max=None, do_moves=True, do_splits=True, region_of=None):
    """THE CREST INSERTION - the restore that moves nothing. The marching-cubes vertices lie ON the base's faces; the sharp
    edge between two faces is cut because no mesh edge runs along it. Every mesh edge that CROSSES a sharp edge (one end
    nearer face A, the other nearer face B, the two faces of that segment) is split at its point nearest the crest, and
    the new vertex is put ON the crest; the two triangles on the edge become four. The crest is then a chain of mesh
    edges, the face vertices stay where they are, nothing moves, nothing can fold. A vertex already on the crest counts
    as neither side. Returns (V', T', stats)."""
    V = np.asarray(V, float); T = np.asarray(T, int)
    st = {"label": label, "crossing": 0, "inserted": 0, "moved": 0, "flipped": 0, "skipped": 0}
    if loc.n == 0 or not len(V) or loc.nA is None:
        say("  crest insertion (%s): nothing to do" % label); return V.copy(), T.copy(), st
    lift_max = (0.67 * reach) if lift_max is None else lift_max
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); E = np.unique(np.sort(e, axis=1), axis=0)
    mid = 0.5 * (V[E[:, 0]] + V[E[:, 1]]); de, _, k = loc.nearest(mid); near = np.nonzero(de <= reach)[0]
    if ipd is not None and len(near):
        onb = np.array([ipd.EvaluateFunction(V[i]) <= snap for i in np.unique(E[near].ravel())])
        onb_of = dict(zip(np.unique(E[near].ravel()), onb))
        near = near[np.array([onb_of[E[i, 0]] and onb_of[E[i, 1]] for i in near], bool)]
    if not len(near):
        say("  crest insertion (%s): no mesh edge within %.2f mm of a sharp edge" % (label, reach)); return V.copy(), T.copy(), st
    u = E[near, 0]; v = E[near, 1]
    if loc.rA is not None and region_of is not None:
        ru = region_of(V[u]); rv = region_of(V[v])
        pair = {}
        for kk in range(loc.n): pair.setdefault((int(loc.rA[kk]), int(loc.rB[kk])), []).append(kk)
        kk = np.full(len(near), -1)
        cand = (ru != rv)
        for j in np.nonzero(cand)[0]:
            segs_j = pair.get((int(ru[j]), int(rv[j]))) or pair.get((int(rv[j]), int(ru[j])))
            if not segs_j: continue
            if len(segs_j) == 1: kk[j] = segs_j[0]; continue
            m_ = mid[near[j]]; A_ = loc.A[segs_j]; d_ = loc.B[segs_j] - A_
            tt = np.clip(np.einsum("ij,ij->i", m_ - A_, d_) / np.maximum(np.einsum("ij,ij->i", d_, d_), 1e-18), 0, 1)
            kk[j] = segs_j[int(np.argmin(np.linalg.norm(m_ - (A_ + d_ * tt[:, None]), axis=1)))]
        cross = kk >= 0; k_near = np.where(cross, kk, k[near])
        A = loc.A[k_near]
    else:
        A = loc.A[k[near]]; nA = loc.nA[k[near]]; nB = loc.nB[k[near]]
        def side_of(P):
            dA = np.abs(np.einsum("ij,ij->i", P - A, nA)); dB = np.abs(np.einsum("ij,ij->i", P - A, nB))
            on = (dA <= snap) & (dB <= snap)
            return np.where(on, 0, np.where(dA < dB, 1, 2))
        su = side_of(V[u]); sv = side_of(V[v])
        cross = (su != 0) & (sv != 0) & (su != sv); k_near = k[near]
    st["crossing"] = int(cross.sum())
    if not cross.any():
        say("  crest insertion (%s): no mesh edge crosses a sharp edge" % label); return V.copy(), T.copy(), st
    P0 = V[u[cross]]; P1 = V[v[cross]]; Q0 = A[cross]; Q1 = loc.B[k_near[cross]]
    d1 = P1 - P0; d2 = Q1 - Q0; r = P0 - Q0
    a_ = np.einsum("ij,ij->i", d1, d1); b_ = np.einsum("ij,ij->i", d1, d2); c_ = np.einsum("ij,ij->i", d2, d2)
    d_ = np.einsum("ij,ij->i", d1, r); e_ = np.einsum("ij,ij->i", d2, r); den = a_ * c_ - b_ * b_
    sN = np.where(den > 1e-18, (b_ * e_ - c_ * d_) / np.maximum(den, 1e-18), 0.5); sN = np.clip(sN, 0.0, 1.0)
    tN = np.clip((b_ * sN + e_) / np.maximum(c_, 1e-18), 0.0, 1.0)
    Pm = P0 + d1 * sN[:, None]; Qm = Q0 + d2 * tN[:, None]; gap = np.linalg.norm(Pm - Qm, axis=1)
    uc = u[cross]; vc = v[cross]
    near_u = np.linalg.norm(Qm - V[uc], axis=1); near_v = np.linalg.norm(Qm - V[vc], axis=1); half = 0.5 * (reach / 3.0)
    V = V.copy(); moved = {}
    for j in (np.nonzero((np.minimum(near_u, near_v) <= half) & (gap <= lift_max))[0] if do_moves else []):
        w = int(uc[j]) if near_u[j] <= near_v[j] else int(vc[j])
        if w not in moved: moved[w] = Qm[j]
    ok = (sN > 0.02) & (sN < 0.98) & (gap <= lift_max) & (np.minimum(near_u, near_v) > half)
    st["skipped"] = int((~ok).sum())
    dvall, _, _ = loc.nearest(V); oncrest = np.nonzero(dvall <= snap)[0]
    kdc = cKDTree(V[oncrest]) if len(oncrest) else None
    tri_of = {}
    for k, (a, b, c) in enumerate(T):
        for x, y in ((a, b), (b, c), (c, a)): tri_of.setdefault((min(x, y), max(x, y)), []).append(k)
    flips = {}
    newid = {}; NV = []; seen = {}
    for j in (np.nonzero(ok)[0] if do_splits else []):
        if int(uc[j]) in moved or int(vc[j]) in moved: continue
        key = (int(min(uc[j], vc[j])), int(max(uc[j], vc[j])))
        if key in newid or key in flips: continue
        if kdc is not None:
            dd, jj = kdc.query(Qm[j])
            if dd <= half:
                w = int(oncrest[jj]); tl = tri_of.get(key, [])
                if len(tl) == 2 and any(w in T[t] for t in tl): flips[key] = w
                continue
        qk = tuple(np.round(Qm[j] / (half + 1e-12)).astype(int))
        if qk in seen: continue
        seen[qk] = True; newid[key] = len(V) + len(NV); NV.append(Qm[j])
    T = T.copy(); nflip = 0
    for (a, b), w in flips.items():
        tl = tri_of[(a, b)]; t1, t2 = [list(T[t]) for t in tl]
        if w not in t1: t1, t2 = t2, t1; tl = tl[::-1]
        z = [x for x in t2 if x not in (a, b)][0]
        if z == w: continue
        i_a = t1.index(a); fwd = t1[(i_a + 1) % 3] == b
        u_, v_ = (a, b) if fwd else (b, a)
        n1 = [w, u_, z]; n2 = [w, z, v_]
        if (min(w, z), max(w, z)) in tri_of: continue
        T[tl[0]] = n1; T[tl[1]] = n2; nflip += 1
    st["flipped"] = nflip
    if moved:
        order = np.argsort(T.ravel()); vidx = T.ravel()[order]; tidx = np.repeat(np.arange(len(T)), 3)[order]
        starts = np.searchsorted(vidx, np.arange(len(V) + 1)); mv = 0
        for w, q in moved.items():
            tl = tidx[starts[w]:starts[w + 1]]; P = V[T[tl]]; n0 = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); old = V[w].copy(); V[w] = q
            P = V[T[tl]]; n1 = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); a0 = np.linalg.norm(n0, axis=1); a1 = np.linalg.norm(n1, axis=1)
            if np.any(np.einsum("ij,ij->i", n0, n1) <= 0.0) or np.any(a1 < 0.05 * np.maximum(a0, 1e-12)): V[w] = old
            else: mv += 1
        st["moved"] = mv
    if not NV:
        say("  crest insertion (%s): %d crossing edges, %d ends moved onto the crest, %d edges flipped, none splittable" % (label, st["crossing"], st.get("moved", 0), st.get("flipped", 0))); return V, T.copy(), st
    V2 = np.vstack([V, np.array(NV)]); out = []
    def mid_of(a, b):
        return newid.get((min(a, b), max(a, b)))
    for a, b, c in T:
        a, b, c = int(a), int(b), int(c)
        m = [mid_of(a, b), mid_of(b, c), mid_of(c, a)]; kk = sum(x is not None for x in m)
        if kk == 0: out.append((a, b, c)); continue
        if kk == 1:
            while m[0] is None: a, b, c = b, c, a; m = m[1:] + m[:1]
            out += [(a, m[0], c), (m[0], b, c)]
        elif kk == 2:
            while m[2] is not None: a, b, c = b, c, a; m = m[1:] + m[:1]
            out += [(a, m[0], m[1]), (m[0], b, m[1]), (a, m[1], c)]
        else:
            out += [(a, m[0], m[2]), (m[0], b, m[1]), (m[2], m[1], c), (m[0], m[1], m[2])]
    T2 = np.array(out, int); st["inserted"] = len(NV)
    say("  crest insertion (%s): %d mesh edges cross a sharp edge, %d split by a vertex ON it, %d ends moved onto it, %d flipped across a crest vertex (%d skipped: the crossing at an end, or over %.2f mm away); %d vertices, %d triangles now"
        % (label, st["crossing"], len(NV), st.get("moved", 0), st.get("flipped", 0), st["skipped"], lift_max, len(V2), len(T2)))
    return V2, T2, st


def _region_fn(VB, TB, lab):
    """points -> the base face (region label) of each point's closest base triangle, by vtk's static cell locator"""
    import vtk
    from vtk.util import numpy_support as nps
    pts = vtk.vtkPoints(); pts.SetData(nps.numpy_to_vtk(np.ascontiguousarray(VB, dtype=np.float64), deep=1))
    cells = vtk.vtkCellArray(); arr = np.hstack([np.full((len(TB), 1), 3, dtype=np.int64), np.asarray(TB).astype(np.int64)]).ravel()
    cells.SetCells(len(TB), nps.numpy_to_vtkIdTypeArray(arr, deep=1)); pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(cells)
    locator = vtk.vtkStaticCellLocator(); locator.SetDataSet(pd); locator.BuildLocator()
    cp = [0.0, 0.0, 0.0]; cid = vtk.reference(0); sub = vtk.reference(0); d2 = vtk.reference(0.0)
    def region_of(P):
        out = np.empty(len(P), int)
        for i, p in enumerate(np.asarray(P, float)):
            locator.FindClosestPoint(p, cp, cid, sub, d2); out[i] = lab[int(cid.get())]
        return out
    return region_of


def _piece_poly_fn(V, T):
    import vtk
    from vtk.util import numpy_support as nps
    pts = vtk.vtkPoints(); pts.SetData(nps.numpy_to_vtk(np.ascontiguousarray(V, dtype=np.float64), deep=1))
    cells = vtk.vtkCellArray(); arr = np.hstack([np.full((len(T), 1), 3, dtype=np.int64), np.asarray(T).astype(np.int64)]).ravel()
    cells.SetCells(len(T), nps.numpy_to_vtkIdTypeArray(arr, deep=1)); pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(cells)
    f = vtk.vtkImplicitPolyDataDistance(); f.SetInput(pd); return f


def run_all(V, T, VB, TB, ipd, h, say=print, deg=25.0, reach=None, depth=None, snap=0.03, sp=None, planes=(), protect=()):
    """the whole restore as rb_blend / rb_decimate call it: the crest inserted into the mesh on the convex edges everywhere
    and on the concave edges inside the PROTECT boxes, then the sharp corners given a vertex, then any vertex that still
    cuts an edge put back. Defaults scale with the grid: reach 3h, depth 2h, sample spacing h/4. Returns (V', T', [stats...])."""
    reach = 3.0 * h if reach is None else reach; depth = 2.0 * h if depth is None else depth; sp = h / 4.0 if sp is None else sp
    (cvx, cA, cB, pA, pB), (ccv, vA, vB, qA, qB) = feature_edges(VB, TB, deg, planes, normals=True)
    lab = face_regions(VB, TB, deg)
    say("  feature edges of the base (>= %g deg, off the wall planes): %d convex, %d concave between %d faces; reach %.2f depth %.2f mm" % (deg, len(cvx), len(ccv), int(lab.max()) + 1, reach, depth))
    region_of = _region_fn(VB, TB, lab)
    out = []; locc = EdgeLocator(VB, cvx, sp, cA, cB, lab[pA], lab[pB])
    for p in range(3):
        V, T, st = insert_crest(V, T, locc, reach, snap, ipd=ipd, say=say, label="convex pass %d" % (p + 1), region_of=region_of, do_splits=False); out.append(st)
        if not st["moved"] and not st["flipped"]: break
    V, st = pull_corners(V, T, _piece_poly_fn, corners_of(VB, cvx, deg), +1, reach, snap, label="convex", say=say); out.append(st)
    V, st = restore(V, T, ipd, locc, +1, reach, depth, snap, label="convex", say=say); out.append(st)
    V, st = pull_edges(V, T, _piece_poly_fn, locc, +1, min(reach, 1.0 * h), snap, label="convex", say=say); out.append(st)
    if len(protect) and len(ccv):
        mid = 0.5 * (VB[ccv[:, 0]] + VB[ccv[:, 1]]); inb = np.zeros(len(ccv), bool)
        for b in protect:
            inb |= (mid[:, 0] >= b[0]) & (mid[:, 0] <= b[1]) & (mid[:, 1] >= b[2]) & (mid[:, 1] <= b[3]) & (mid[:, 2] >= b[4]) & (mid[:, 2] <= b[5])
        if inb.any():
            locv = EdgeLocator(VB, ccv[inb], sp, vA[inb], vB[inb], lab[qA[inb]], lab[qB[inb]])
            for p in range(3):
                V, T, st = insert_crest(V, T, locv, reach, snap, ipd=ipd, say=say, label="concave in PROTECT pass %d" % (p + 1), region_of=region_of, do_splits=False); out.append(st)
                if not st["moved"] and not st["flipped"]: break
            V, st = pull_corners(V, T, _piece_poly_fn, corners_of(VB, ccv[inb], deg), -1, reach, snap, label="concave in PROTECT", say=say); out.append(st)
            V, st = restore(V, T, ipd, locv, -1, reach, depth, snap, where=protect, label="concave in PROTECT", say=say); out.append(st)
            V, st = pull_edges(V, T, _piece_poly_fn, locv, -1, min(reach, 1.0 * h), snap, label="concave in PROTECT", say=say); out.append(st)
    return V, T, out

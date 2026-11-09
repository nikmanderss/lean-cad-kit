import numpy as np

CORNER_DEG = 50.0
STEP_MM = 0.1
PLANE_TOL = 0.01
SIDE_TOL = 1e-5
GUIDE_TOL = 0.05
PLATE_MAX_DEG = 80.0
PLATE_FIT = 0.005
# over the
# NURBS_RIM
# NURBS_RIM
import os as _os
NURBS = (_os.environ.get("NURBS", "1") or "1").strip() not in ("0", "", "off", "no")
NURBS_LOOSE_RIM = float(_os.environ.get("NURBS_LOOSE_RIM", "0.5") or 0.5)
NURBS_RIM = float(_os.environ.get("NURBS_RIM", "0.10") or 0.10)
NURBS_WALL_RIM = float(_os.environ.get("NURBS_WALL_RIM", "0.02") or 0.02)
NURBS_TOL = float(_os.environ.get("NURBS_TOL", "0.01") or 0.01)
NURBS_STEP = float(_os.environ.get("NURBS_STEP", "1.0") or 1.0)
NURBS_MAXSEG = int(_os.environ.get("NURBS_MAXSEG", "40") or 40); NURBS_MAXDEG = int(_os.environ.get("NURBS_MAXDEG", "8") or 8)
PRINT_TOL = 0.30
                       # recorded
def wall_trade_rim():
    """R7W A4 (verify-span-fill finding 11): the rim a WALL face's fill may trade to for a flatter interior - NURBS_RIM, only when the agent loosened
    NURBS_WALL_RIM over its 0.02 default (the agent's 0.08); at the default the wall keeps its strict rim (the frame check's - sn3 / sn5; 0.02 -> 0.10 is untested
    downstream). None = no trade past the face's own rim (the fillet caps' 0.02 and every caller that hands span_face no trade_rim)"""
    return NURBS_RIM if NURBS_WALL_RIM > 0.02 + 1e-9 else None


def _unit(v):
    n = np.linalg.norm(v); return v / n if n > 1e-12 else v


def _arc(P):
    d = np.linalg.norm(np.diff(P, axis=0), axis=1); return np.concatenate([[0.0], np.cumsum(d)])


def resample(P, n):
    """n points along the polyline P by arc length (the ends exact)"""
    P = np.asarray(P, float)
    if len(P) == 1: return np.repeat(P, n, axis=0)
    s = _arc(P); L = s[-1]
    if L < 1e-12: return np.repeat(P[:1], n, axis=0)
    t = np.linspace(0, L, n)
    return np.stack([np.interp(t, s, P[:, k]) for k in range(3)], 1)


def order_loop(polys, tol=1e-3):
    """polylines (each an edge's samples, any direction) -> one closed loop of samples, with the index where each edge starts.
    Returns (loop (N,3), starts [i0, i1, ...], order [(edge index, reversed)])"""
    left = list(range(len(polys))); out = [np.asarray(polys[left.pop(0)], float)]; order = [(0, False)]
    while left:
        tail = out[-1][-1]; best = None
        for k in left:
            Q = np.asarray(polys[k], float)
            for d, rev in ((np.linalg.norm(Q[0] - tail), False), (np.linalg.norm(Q[-1] - tail), True)):
                if best is None or d < best[0]: best = (d, k, rev)
        d, k, rev = best
        if d > max(tol, 0.05): raise ValueError("the boundary does not close end to end (a %.3f mm gap)" % d)
        Q = np.asarray(polys[k], float); out.append(Q[::-1] if rev else Q); order.append((k, rev)); left.remove(k)
    starts = []; pts = []
    for Q in out:
        starts.append(len(pts)); pts.extend(Q[:-1].tolist() if len(Q) > 1 else Q.tolist())
    loop = np.array(pts, float)
    if np.linalg.norm(loop[0] - out[-1][-1]) > max(tol, 0.05): raise ValueError("the boundary's last edge does not return to its first")
    return loop, starts, order


def corners_of(loop, starts, corner_deg=CORNER_DEG):
    """the loop's corners: a turn sharper than corner_deg at an edge joint (within an edge the decided curve has no corner)"""
    n = len(loop); out = []
    for s in starts:
        a = loop[s] - loop[(s - 1) % n]; b = loop[(s + 1) % n] - loop[s]
        if np.linalg.norm(a) < 1e-9 or np.linalg.norm(b) < 1e-9: continue
        ang = np.degrees(np.arccos(np.clip(_unit(a) @ _unit(b), -1, 1)))
        if ang >= corner_deg: out.append(s)
    return sorted(set(out))


def four_corners(loop, starts, corner_deg=CORNER_DEG):
    """four positions (indices into loop) that split it into the four sides of the face, and how they were chosen"""
    n = len(loop); s = _arc(np.vstack([loop, loop[:1]])); L = s[-1]
    cs = corners_of(loop, starts, corner_deg)
    def side_len(a, b): return (s[b] - s[a]) % L if b != a else L
    def pick4(c):
        import itertools
        best = None
        for q in itertools.combinations(c, 4):
            m = min(side_len(q[i], q[(i + 1) % 4]) for i in range(4))
            if best is None or m > best[0]: best = (m, q)
        return list(best[1])
    def at_len(target):
        return int(np.argmin(np.abs(s[:-1] - (target % L))))
    def split_longest(q):
        q = sorted(q); lens = [side_len(q[i], q[(i + 1) % len(q)]) for i in range(len(q))]; i = int(np.argmax(lens))
        q.append(at_len(s[q[i]] + lens[i] / 2)); return sorted(q)
    how = "%d corner(s)" % len(cs)
    if len(cs) >= 4: q = pick4(cs) if len(cs) > 4 else cs
    elif len(cs) == 3: q = split_longest(cs)
    elif len(cs) == 2: q = split_longest(split_longest(cs))
    elif len(cs) == 1: q = sorted([cs[0]] + [at_len(s[cs[0]] + L * k / 4) for k in (1, 2, 3)])
    else: q = [at_len(L * k / 4) for k in range(4)]
    q = sorted(set(q))
    while len(q) < 4: q = split_longest(q)
    return q[:4], how


def sides_of(loop, q):
    """the four sides as polylines (each from corner k to corner k+1 along the loop)"""
    n = len(loop); out = []
    for k in range(4):
        a, b = q[k], q[(k + 1) % 4]
        idx = list(range(a, b + 1)) if b > a else list(range(a, n)) + list(range(0, b + 1))
        out.append(loop[idx])
    return out


def side_pieces(loop, starts, q):
    """the four sides as lists of polylines, one per edge piece (split at every edge joint inside the side): each piece is one smooth decided
    curve, so it is approximated on its own; the joints become C0 knots of the side"""
    n = len(loop); sset = set(starts); out = []
    for k in range(4):
        a, b = q[k], q[(k + 1) % 4]
        idx = list(range(a, b + 1)) if b > a else list(range(a, n)) + list(range(0, b + 1))
        pieces = []; cur = [idx[0]]
        for i in idx[1:]:
            cur.append(i)
            if (i % n) in sset and i != idx[-1]: pieces.append(loop[cur]); cur = [i]
        if len(cur) > 1: pieces.append(loop[cur])
        out.append([p for p in pieces if len(p) > 1])
    return out


def planar(loop, tol=PLANE_TOL):
    """(is planar, centre, normal) of the boundary samples"""
    P = np.asarray(loop, float); c = P.mean(0); _, sv, vh = np.linalg.svd(P - c, full_matrices=False); n = vh[2]
    return bool(np.abs((P - c) @ n).max() <= tol), c, n



def _curve_of(P, tol=SIDE_TOL):
    """one degree-3 B-spline curve within tol of the polyline P (a straight piece is exact)"""
    import Part
    from FreeCAD import Vector as V3
    P = np.asarray(P, float)
    if len(P) < 2: raise ValueError("a side piece with one point")
    ch = P[-1] - P[0]; L = np.linalg.norm(ch)
    straight = L > 1e-9 and np.abs(np.cross(P - P[0], _unit(ch))).max() <= tol if len(P) > 2 else True
    if straight:
        c = Part.LineSegment(V3(*P[0]), V3(*P[-1])).toBSpline(); c.increaseDegree(3); return c
    if len(P) < 6: P = resample(P, 6)
    c = Part.BSplineCurve(); c.approximate(Points=[V3(*p) for p in P], DegMin=3, DegMax=3, Tolerance=tol, Continuity="C2")
    if c.isRational(): raise ValueError("a rational curve from approximate")
    return c


def side_curve(pieces, tol=SIDE_TOL):
    """the side's pieces (polylines, end to end) -> ONE B-spline curve, parameter 0..1 in proportion to arc length (join concatenates
    PARAMETER ranges: a 2 mm piece after a 14 mm one would own half the side's parameter and shear the patch against the opposite side -
    a section span2: thin strips folded on that alone), C0 at the joints"""
    cs = [_curve_of(p, tol) for p in pieces]; t0 = 0.0
    for c_, p_ in zip(cs, pieces):
        L_ = max(_arc(np.asarray(p_, float))[-1], 1e-6); c_.scaleKnotsToBounds(t0, t0 + L_); t0 += L_
    c = cs[0]
    for c2 in cs[1:]:
        if not c.join(c2): raise ValueError("a side's pieces do not join end to end")
    c.scaleKnotsToBounds(0.0, 1.0)
    # two pieces
    if len(cs) > 1:
        for ki in range(c.NbKnots - 2, 0, -1):
            try:
                m_ = c.getMultiplicities()[ki]
                if m_ >= 3: c.removeKnot(ki + 1, 1, tol * 10)
            except Exception: pass
    return c


def _compat(c1, c2, tol=1e-9):
    """insert each curve's knots into the other so both share one knot vector"""
    for src, dst in ((c1, c2), (c2, c1)):
        for k, m in zip(src.getKnots(), src.getMultiplicities()):
            if k <= tol or k >= 1 - tol: continue
            cur = 0
            for k2, m2 in zip(dst.getKnots(), dst.getMultiplicities()):
                if abs(k2 - k) <= tol: cur = m2
            if m > cur: dst.insertKnot(k, m - cur, tol)


def _insert_knots(s, which, knots, mults, tol=1e-9):
    cur = dict((round(k, 12), m) for k, m in zip(s.getUKnots() if which == "u" else s.getVKnots(), s.getUMultiplicities() if which == "u" else s.getVMultiplicities()))
    ks = []; ms = []
    for k, m in zip(knots, mults):
        if k <= tol or k >= 1 - tol: continue
        have = 0
        for k2, m2 in cur.items():
            if abs(k2 - k) <= tol: have = m2
        if m > have: ks.append(k); ms.append(m - have)
    if ks:
        if which == "u": s.insertUKnots(ks, ms, tol)
        else: s.insertVKnots(ks, ms, tol)


def coons_surface(B, R, T, Lf):
    """the Coons patch of four B-spline sides as ONE B-spline surface: B (u 0->1 at v 0), T (u 0->1 at v 1), Lf (v 0->1 at u 0), R (v 0->1 at
    u 1), corners coincident. = ruled(B,T) + ruled(Lf,R) - bilinear(corners), all three raised to degree 3x3 on the union knot grid and
    summed pole by pole."""
    import Part
    from FreeCAD import Vector as V3
    for c in (B, R, T, Lf):
        if c.Degree < 3: c.increaseDegree(3)
        c.scaleKnotsToBounds(0.0, 1.0)
    _compat(B, T); _compat(Lf, R)
    KU, MU = B.getKnots(), B.getMultiplicities(); KV, MV = Lf.getKnots(), Lf.getMultiplicities()
    pb, pt = B.getPoles(), T.getPoles(); pl, pr = Lf.getPoles(), R.getPoles()
    s1 = Part.BSplineSurface(); s1.buildFromPolesMultsKnots([[pb[i], pt[i]] for i in range(len(pb))], MU, [2, 2], KU, [0.0, 1.0], False, False, 3, 1)
    s1.increaseDegree(3, 3); _insert_knots(s1, "v", KV, MV)
    s2 = Part.BSplineSurface(); s2.buildFromPolesMultsKnots([list(pl), list(pr)], [2, 2], MV, [0.0, 1.0], KV, False, False, 1, 3)
    s2.increaseDegree(3, 3); _insert_knots(s2, "u", KU, MU)
    s3 = Part.BSplineSurface(); s3.buildFromPolesMultsKnots([[pb[0], pt[0]], [pb[-1], pt[-1]]], [2, 2], [2, 2], [0.0, 1.0], [0.0, 1.0], False, False, 1, 1)
    s3.increaseDegree(3, 3); _insert_knots(s3, "u", KU, MU); _insert_knots(s3, "v", KV, MV)
    P1, P2, P3 = s1.getPoles(), s2.getPoles(), s3.getPoles()
    nu, nv = len(P1), len(P1[0])
    if (len(P2), len(P2[0])) != (nu, nv) or (len(P3), len(P3[0])) != (nu, nv): raise ValueError("the three Coons surfaces do not share one pole grid (%dx%d, %dx%d, %dx%d)" % (nu, nv, len(P2), len(P2[0]), len(P3), len(P3[0])))
    P = [[P1[i][j] + P2[i][j] - P3[i][j] for j in range(nv)] for i in range(nu)]
    s = Part.BSplineSurface(); s.buildFromPolesMultsKnots(P, s1.getUMultiplicities(), s1.getVMultiplicities(), s1.getUKnots(), s1.getVKnots(), False, False, 3, 3)
    return s


def refine(s, lu, lv, step=1.0, cap=48):
    """insert knots so the pole grid is about `step` mm (so added lines have poles to move)"""
    for which, L, K in (("u", lu, s.getUKnots()), ("v", lv, s.getVKnots())):
        n_ = int(np.clip(round(L / step), 4, cap)); have = set(round(k, 9) for k in K)
        new = [k for k in np.linspace(0, 1, n_ + 1)[1:-1] if all(abs(k - h) > 1e-6 for h in have)]
        if new: _insert_knots(s, which, [float(k) for k in new], [1] * len(new))
    return s


def _basis_full(t, kf, deg):
    """B-spline basis functions (len(t) x npoles) on the full knot vector kf"""
    t = np.clip(np.asarray(t, float), kf[deg], kf[-deg - 1] - 1e-12); m = len(kf) - 1
    N = np.zeros((len(t), m))
    for i in range(m): N[:, i] = (t >= kf[i]) & (t < kf[i + 1])
    for p in range(1, deg + 1):
        Nn = np.zeros((len(t), m - p))
        for i in range(m - p):
            a = (t - kf[i]) / (kf[i + p] - kf[i]) if kf[i + p] > kf[i] else 0.0
            b = (kf[i + p + 1] - t) / (kf[i + p + 1] - kf[i + 1]) if kf[i + p + 1] > kf[i + 1] else 0.0
            Nn[:, i] = a * N[:, i] + b * N[:, i + 1]
        N = Nn
    return N


def guide_pull(s, guides, step=1.0, lam=0.02):
    """move the surface's INTERIOR poles so it passes through the added lines (polylines inside the face); the border poles stay.
    Returns (max distance of the lines from the surface before, after)"""
    from FreeCAD import Vector as V3
    uk = np.repeat(s.getUKnots(), s.getUMultiplicities()); vk = np.repeat(s.getVKnots(), s.getVMultiplicities())
    P = s.getPoles(); nu, nv = len(P), len(P[0]); PA = np.array([[[p.x, p.y, p.z] for p in row] for row in P])
    Q = []; UV = []
    for G in guides:
        G = np.asarray(G, float); G = resample(G, max(6, int(_arc(G)[-1] / (0.5 * step)) + 1))
        for g in G:
            try: u, v = s.parameter(V3(*g))
            except Exception: continue
            if 1e-6 < u < 1 - 1e-6 and 1e-6 < v < 1 - 1e-6: Q.append(g); UV.append((u, v))
    if not Q: return 0.0, 0.0
    Q = np.array(Q); UV = np.array(UV)
    S0 = np.array([[q.x, q.y, q.z] for q in (s.value(float(a), float(b)) for a, b in UV)]); r = Q - S0; before = float(np.linalg.norm(r, axis=1).max())
    Bu = _basis_full(UV[:, 0], uk, 3); Bv = _basis_full(UV[:, 1], vk, 3)
    touch = np.zeros((nu, nv), bool)
    for k in range(len(UV)):
        iu = np.nonzero(Bu[k] > 1e-9)[0]; iv = np.nonzero(Bv[k] > 1e-9)[0]
        if len(iu) and len(iv): touch[iu.min():iu.max() + 1, iv.min():iv.max() + 1] = True
    for _ in range(2):
        g = touch.copy(); g[1:, :] |= touch[:-1, :]; g[:-1, :] |= touch[1:, :]; g[:, 1:] |= touch[:, :-1]; g[:, :-1] |= touch[:, 1:]; touch = g
    touch[0, :] = touch[-1, :] = touch[:, 0] = touch[:, -1] = False
    inner = [(i, j) for i in range(1, nu - 1) for j in range(1, nv - 1) if touch[i, j]]
    if not inner: return before, before
    idx = {ij: n for n, ij in enumerate(inner)}; ncol = len(inner)
    try:
        import scipy.sparse as _sp
        from scipy.sparse.linalg import spsolve as _spsolve
    except Exception:
        _sp = None
    if _sp is None and ncol > 4000:
        raise ValueError("an added line on a %d x %d-pole patch needs a sparse solve (%d unknowns) and scipy is missing in this FreeCAD - split the face with a wire or make the line a split" % (nu, nv, ncol))
    ar, ac, av = [], [], []
    for k in range(len(UV)):
        iu = np.nonzero(Bu[k] > 1e-12)[0]; iv = np.nonzero(Bv[k] > 1e-12)[0]
        for i in iu:
            for j in iv:
                n_ = idx.get((int(i), int(j)))
                if n_ is not None: ar.append(k); ac.append(n_); av.append(float(Bu[k, i] * Bv[k, j]))
    dr, dc, dv = [], [], []; nrow = 0
    for (i, j) in inner:
        for (a, b, c) in (((i - 1, j), (i, j), (i + 1, j)), ((i, j - 1), (i, j), (i, j + 1))):
            for q_, w_ in ((a, 1.0), (b, -2.0), (c, 1.0)):
                if q_ in idx: dr.append(nrow); dc.append(idx[q_]); dv.append(w_)
            nrow += 1
    if _sp is not None:
        A = _sp.coo_matrix((av, (ar, ac)), shape=(len(UV), ncol)).tocsr(); D = _sp.coo_matrix((dv, (dr, dc)), shape=(nrow, ncol)).tocsr()
        M = (A.T @ A + lam * (D.T @ D)).tocsc()
        d = np.stack([_spsolve(M, A.T @ r[:, c_]) for c_ in range(3)], 1)
    else:
        A = np.zeros((len(UV), ncol)); A[ar, ac] = av; D = np.zeros((nrow, ncol)); D[dr, dc] = dv
        M = A.T @ A + lam * (D.T @ D); d = np.linalg.lstsq(M, A.T @ r, rcond=None)[0]
    d = np.asarray(d).reshape(ncol, 3)
    for n, (i, j) in enumerate(inner):
        s.setPole(i + 1, j + 1, V3(*(PA[i, j] + d[n])))
    S1 = np.array([[q.x, q.y, q.z] for q in (s.value(float(a), float(b)) for a, b in UV)]); after = float(np.linalg.norm(Q - S1, axis=1).max())
    return before, after


def _basis_uniform(t, nc, deg=3):
    kn = np.concatenate([np.zeros(deg), np.linspace(0, 1, nc - deg + 1), np.ones(deg)])
    return _basis_full(t, kn, deg)[:, :nc]


def plate_surface(loop, guides=(), vox_normals=None, step=1.0, cap=48, margin=3.0, max_deg=PLATE_MAX_DEG):
    """THE PLATE: the face as a height field over its own best-fit plane - the smoothest surface (least bending) through its edges and
    its added lines, wider than the face by `margin` and TRIMMED by the wire afterwards. For the face a Coons patch cannot span: a
    concave outline (an L, a U, a notch), many corners. Refused when the face is not single-valued over its plane (the voxel's normals
    turn more than max_deg from it: a face that wraps) - that face is split with a wire. Returns (surface, info)."""
    import Part
    from FreeCAD import Vector as V3
    P = np.asarray(loop, float); c = P.mean(0); _, _, vh = np.linalg.svd(P - c, full_matrices=False); e1, e2, n = vh[0], vh[1], vh[2]
    info = {}
    if vox_normals is not None and len(vox_normals):
        ang = np.degrees(np.arccos(np.clip(np.abs(np.asarray(vox_normals) @ n), 0, 1))); info["turn_p95_deg"] = round(float(np.percentile(ang, 95)), 1)
        if np.percentile(ang, 95) > max_deg: raise ValueError("the face turns %.0f deg from its own plane (over %g) - not a height field: split it with a wire" % (np.percentile(ang, 95), max_deg))
    data = [P] + [resample(np.asarray(G, float), max(6, int(_arc(np.asarray(G, float))[-1] / (0.5 * step)) + 1)) for G in guides]
    D3 = np.vstack(data); X = (D3 - c) @ e1; Y = (D3 - c) @ e2; Zh = (D3 - c) @ n
    lo = np.array([X.min() - margin, Y.min() - margin]); hi = np.array([X.max() + margin, Y.max() + margin]); ext = hi - lo
    nu = int(np.clip(round(ext[0] / step) + 3, 4, cap)); nv = int(np.clip(round(ext[1] / step) + 3, 4, cap))
    u = (X - lo[0]) / ext[0]; v = (Y - lo[1]) / ext[1]
    Bu = _basis_uniform(u, nu); Bv = _basis_uniform(v, nv)
    A = (Bu[:, :, None] * Bv[:, None, :]).reshape(len(u), nu * nv)
    idx = np.arange(nu * nv).reshape(nu, nv); rows = []
    for (a, b, cc) in ((idx[:-2, :], idx[1:-1, :], idx[2:, :]), (idx[:, :-2], idx[:, 1:-1], idx[:, 2:]), (idx[:-1, :-1], None, None)):
        if b is None:
            for i in range(nu - 1):
                for j in range(nv - 1):
                    r = np.zeros(nu * nv); r[idx[i, j]] = 1; r[idx[i + 1, j + 1]] = 1; r[idx[i + 1, j]] = -1; r[idx[i, j + 1]] = -1; rows.append(r)
            continue
        for x0, x1, x2 in zip(a.ravel(), b.ravel(), cc.ravel()):
            r = np.zeros(nu * nv); r[x0] = 1; r[x1] = -2; r[x2] = 1; rows.append(r)
    Dm = np.array(rows)
    lam = 1e-3 * len(u) / (nu * nv); h = None
    for _try in range(4):
        M = A.T @ A + lam * (Dm.T @ Dm); h = np.linalg.lstsq(M, A.T @ Zh, rcond=None)[0]
        res = np.abs(A @ h - Zh); info["fit_max_mm"] = round(float(res.max()), 4); info["fit_p95_mm"] = round(float(np.percentile(res, 95)), 4)
        if res.max() <= PLATE_FIT: break
        lam *= 0.1
    if res.max() > PLATE_FIT and step > 0.3 and max(nu, nv) < cap:
        return plate_surface(loop, guides, vox_normals, step * 0.5, cap, margin, max_deg)
    H = h.reshape(nu, nv)
    def grev(nc, deg=3):
        kf = np.concatenate([np.zeros(deg), np.linspace(0, 1, nc - deg + 1), np.ones(deg)]); return np.array([kf[i + 1:i + deg + 1].mean() for i in range(nc)])
    gu = grev(nu); gv = grev(nv)
    poles = [[V3(*(c + (lo[0] + ext[0] * gu[i]) * e1 + (lo[1] + ext[1] * gv[j]) * e2 + H[i, j] * n)) for j in range(nv)] for i in range(nu)]
    kn = lambda nc: ([float(x) for x in np.linspace(0, 1, nc - 2)], [4] + [1] * (nc - 4) + [4])
    uk, um = kn(nu); vk, vm = kn(nv)
    s = Part.BSplineSurface(); s.buildFromPolesMultsKnots(poles, um, vm, uk, vk, False, False, 3, 3)
    info.update({"nu": nu, "nv": nv, "lam": lam}); return s, info


def _uv_outline(s, border):
    """the face's outline in the surface's (u, v): the border's points IN LOOP ORDER projected (31bl; the per-edge polylines come in the
    caller's order and direction - taken as given they zigzag across the face and the even-odd mask is wrong: 381 of 1024 cells on one
    piece); None when the projection fails"""
    try:
        from FreeCAD import Vector as V3
        try:
            _l, _st, _od = order_loop([np.asarray(P, float) for P in border])
            border = [np.asarray(border[k_], float)[::-1] if rev_ else np.asarray(border[k_], float) for k_, rev_ in _od]
        except Exception:
            pass
        pts = np.vstack([np.asarray(P, float)[::max(1, len(P) // 30)] for P in border])
        uv = np.array([s.parameter(V3(*[float(x) for x in p])) for p in pts], float)
        return uv if len(uv) >= 3 and np.isfinite(uv).all() else None
    except Exception:
        return None


def _inside(px, py, poly):
    """even-odd point-in-polygon for the grid cells' centres (px, py arrays) against the (k, 2) outline"""
    x0, y0 = poly[:, 0], poly[:, 1]; x1, y1 = np.roll(x0, -1), np.roll(y0, -1)
    ins = np.zeros(px.shape, bool)
    for a, b, c, d in zip(x0, y0, x1, y1):
        if b == d: continue
        m = ((b > py) != (d > py)) & (px < (c - a) * (py - b) / (d - b) + a)
        ins ^= m
    return ins


def folds(s, n=33, border=None):
    """how many grid cells of the surface FOLD - face the opposite way from a NEIGHBOURING cell (the surface doubling back on itself: a Coons
    patch over a concave boundary, a fill that crosses itself). 31bl: the test was against the surface's MEAN normal, which called every band
    that wraps round more than 90 deg (a fillet strip along a U-shaped vane root) a fold and sent it to the plate rung - a fold is local. And
    only INSIDE the face (border given: the outline's (u, v) on the surface): a fill is approximated over an enlarged rectangle, and what it does
    outside the face does not matter (a 2.8 x 20 mm strip filled most of its domain with extrapolation that waved)."""
    try: u0, u1, v0, v1 = s.bounds()
    except Exception: u0, u1, v0, v1 = 0.0, 1.0, 0.0, 1.0
    us = np.linspace(u0, u1, n); vs = np.linspace(v0, v1, n)
    G = np.array([[[q.x, q.y, q.z] for q in (s.value(float(u), float(v)) for v in vs)] for u in us])
    du = G[1:, :-1] - G[:-1, :-1]; dv = G[:-1, 1:] - G[:-1, :-1]; N = np.cross(du, dv); A = np.linalg.norm(N, axis=-1)
    good = A > 1e-9
    if border is not None:
        uvp = _uv_outline(s, border)
        if uvp is not None:
            cu = 0.5 * (us[1:] + us[:-1]); cv = 0.5 * (vs[1:] + vs[:-1]); PU, PV = np.meshgrid(cu, cv, indexing="ij")
            good = good & _inside(PU, PV, uvp)
    if not good.any(): return 0, 0
    Nn = N / np.maximum(A, 1e-12)[..., None]
    bad = np.zeros(A.shape, bool)
    du_ = np.einsum("ijk,ijk->ij", Nn[1:, :], Nn[:-1, :]) < 0.0; gu_ = good[1:, :] & good[:-1, :]
    dv_ = np.einsum("ijk,ijk->ij", Nn[:, 1:], Nn[:, :-1]) < 0.0; gv_ = good[:, 1:] & good[:, :-1]
    bad[1:, :] |= du_ & gu_; bad[:-1, :] |= du_ & gu_; bad[:, 1:] |= dv_ & gv_; bad[:, :-1] |= dv_ & gv_
    if A.shape[0] > 2:
        d2 = (np.einsum("ijk,ijk->ij", Nn[2:, :], Nn[:-2, :]) < 0.0) & good[2:, :] & good[:-2, :] & ~good[1:-1, :]
        bad[2:, :] |= d2; bad[:-2, :] |= d2
    if A.shape[1] > 2:
        d2 = (np.einsum("ijk,ijk->ij", Nn[:, 2:], Nn[:, :-2]) < 0.0) & good[:, 2:] & good[:, :-2] & ~good[:, 1:-1]
        bad[:, 2:] |= d2; bad[:, :-2] |= d2
    return int((bad & good).sum()), int(good.sum())


def _thin(P, step):
    """every `step` mm along the polyline (the ends kept)"""
    P = np.asarray(P, float)
    if len(P) < 3: return P
    s_ = _arc(P); n = max(2, int(s_[-1] / step) + 1)
    idx = np.unique(np.searchsorted(s_, np.linspace(0, s_[-1], n)).clip(0, len(P) - 1))
    return P[idx]


def _nurbs_points(edge_polys, guide_polys, step, gstep=None):
    pts = []
    for P in edge_polys: pts += [p for p in _thin(P, step)]
    for P in (guide_polys or ()): pts += [p for p in _thin(P, NURBS_STEP if gstep is None else gstep)[1:-1]]
    uniq, seen = [], set()
    for p in pts:
        key = tuple(np.round(p, 3))
        if key not in seen: seen.add(key); uniq.append([float(x) for x in p])
    return uniq


def _nurbs_fill(P, init=None, enlarge=1.1, tol=None, maxseg=None):
    """the plate fill through the points -> ONE B-spline surface (needs FreeCAD). tol / maxseg: the approximation's (31bg: the finer pass)"""
    tol = NURBS_TOL if tol is None else float(tol); maxseg = NURBS_MAXSEG if maxseg is None else int(maxseg)
    import Part
    from FreeCAD import Vector as V3
    G = Part.GeomPlate
    bp = G.BuildPlateSurface(Degree=3, NbPtsOnCur=15, NbIter=3)
    if init is not None: bp.loadInitSurface(init)
    for p in P: bp.add(G.PointConstraint(V3(*p)))
    bp.perform()
    if not bp.isDone(): raise ValueError("the plate fill did not converge")
    try: return bp.surface().makeApprox(Tol3d=tol, MaxSegments=maxseg, MaxDegree=NURBS_MAXDEG, MaxDistance=tol, CritOrder=0, Continuity="C1", EnlargeCoeff=enlarge)
    except TypeError: return bp.surface().makeApprox(Tol3d=tol, MaxSegments=maxseg, MaxDegree=NURBS_MAXDEG, EnlargeCoeff=enlarge)


def _dev(bs, P):
    """the largest gap between the points and the surface (each point projected onto it)"""
    from FreeCAD import Vector as V3
    d = 0.0
    for p in P:
        v = V3(*[float(x) for x in p]); u_, v_ = bs.parameter(v); d = max(d, (bs.value(u_, v_) - v).Length)
    return d


def _rank_tries(tries, rim_tol, band=None, ceil=None):
    """R7W A4 - THE LADDER'S CHOICE BY ITS RIM AND ITS INTERIOR (no kernel: pinned in selftest_skin5). tries: (how, surface, rim mm, added-line dev mm, folds,
    note, rise mm) in ladder order - surface None for a try that failed, rise None where it was not measured. The rim rank first, as before: the FIRST try
    that does not fold and holds its rim within rim_tol (the one the ladder stopped at), else the least folding, then the smallest rim. Then THE INTERIOR
    (M-protect-fill finding A: on the vane plate the rim rank took a fill that bulged 6.7 mm into the designed slot over one whose rim missed by 0.01 mm
    more): when that fill RISES past its border's own height range by more than the print tolerance, a try that does not fold, misses its rim by no more than
    the kit's own fill rim (ceil: max(rim_tol, NURBS_RIM 0.10 - the agent's sn6, the miss the face build takes; measured in R7W: a 0.144 mm miss broke faces 17 / 19,
    0.089 / 0.090 built valid) and rises at least the print tolerance LESS is taken instead - among the flattest such tries (within the print tolerance of the
    lowest rise) the first that holds its rim, else the smallest rim. Returns (best, note): note None when the rim rank stood. verify-span-fill finding 11:
    ceil None = NO trade past rim_tol (the fillet caps' 0.02 kept) - a face's caller hands its trade rim (sk_build _nurbs_args: wall_trade_rim())."""
    band = PRINT_TOL if band is None else float(band); ceil = max(float(rim_tol), float(rim_tol) if ceil is None else float(ceil))
    ok = [t for t in tries if t[1] is not None]
    if not ok: return None, None
    held = [t for t in ok if t[4] == 0 and t[2] <= rim_tol]
    best = held[0] if held else min(ok, key=lambda t: (t[4] > 0, t[2] > rim_tol, t[2]))
    if best[4] or best[2] > rim_tol or best[6] is None or best[6] <= band: return best, None
    flat = [t for t in ok if t[4] == 0 and t[6] is not None and t[2] <= ceil and t[6] < best[6] - band]
    if not flat: return best, None
    hmin = min(t[6] for t in flat); near = [t for t in flat if t[6] <= hmin + band]; within = [t for t in near if t[2] <= rim_tol]
    alt = within[0] if within else min(near, key=lambda t: t[2])
    note = ("THE INTERIOR RANKED (R7W A4): the try that held its rim (%s start; %s: rim %.3f mm) RISES %.2f mm past its border's own height range - taken "
            "instead the %s start; %s: rim %.3f mm%s, rise %.2f mm (a rim miss within the kit's own fill rim beats a rise of millimetres)"
            % (best[0], best[5], best[2], best[6], alt[0], alt[5], alt[2], (" - over the %.2f limit, within the kit's %.2f fill rim (NURBS_RIM)" % (rim_tol, ceil)) if alt[2] > rim_tol else "", alt[6]))
    return alt, note


def nurbs_face(edge_polys, guide_polys, edges_start, rim_tol=None, loop=None, progress=None, trade_rim=None):
    """THE NURBS RUNG (31az, the agent's job_skin_build_nurbs.py): (surface, info) - the clean fill of the ladder of starts; ValueError when none holds its rim within
    NURBS_RIM without a fold. edges_start() -> the Coons / plate surface of the edges alone (the 'boundary blend' start). R7W A4: every try that does not fold
    and holds its rim within the kit's fill rim has its RISE past its border's own height range measured (_rise - the balloon instrument, on loop = the
    ordered boundary); the ladder stops early only at a try that holds its rim, does not fold and rises no more than the print tolerance; the choice is
    _rank_tries' (the rim, then the interior) - an override of the rim rank is said through progress and tagged in the "how"."""
    rim_tol = NURBS_RIM if rim_tol is None else float(rim_tol)
    if loop is None:
        try: loop = order_loop(edge_polys)[0]
        except Exception: loop = None
    rim = np.vstack([np.asarray(P, float)[::max(1, len(P) // 40)] for P in edge_polys])
    gchk = np.vstack([np.asarray(P, float)[::max(1, len(P) // 20)] for P in guide_polys]) if guide_polys else np.zeros((0, 3))
    cache = []; cache_ex = []
    def _blend():
        if cache_ex: raise cache_ex[0]
        if not cache:
            try: cache.append(edges_start())
            except Exception as ex_b: cache_ex.append(ex_b); raise
        return cache[0]
    tries = []; ceil = max(rim_tol, trade_rim if trade_rim is not None else rim_tol)
    for init_how, enl, st in (("mean plane", 1.1, NURBS_STEP), ("mean plane", 1.3, NURBS_STEP), ("boundary blend", 1.1, NURBS_STEP),
                              ("boundary blend", 1.3, NURBS_STEP), ("boundary blend", 1.2, 0.3), ("mean plane", 1.2, 0.3)):
        try:
            P_ = _nurbs_points(edge_polys, guide_polys, st)
            bs = _nurbs_fill(P_, _blend() if init_how == "boundary blend" else None, enl)
            f_, tot_ = folds(bs, border=edge_polys); r_ = _dev(bs, rim)
            tries.append((init_how, bs, r_, _dev(bs, gchk) if len(gchk) else 0.0, f_, "enlarge %.1f, edge points every %.1f mm, %d points" % (enl, st, len(P_)),
                          _rise(bs, edge_polys, guide_polys, loop) if (f_ == 0 and r_ <= ceil) else None))
        except Exception as ex:
            tries.append((init_how, None, 9e9, 9e9, 0, str(ex)[:80], None))
        t_ = tries[-1]
        if t_[1] is not None and t_[2] <= rim_tol and t_[4] == 0 and (t_[6] is None or t_[6] <= PRINT_TOL): break
    best, rank = _rank_tries(tries, rim_tol, ceil=trade_rim)
    if best is not None and len(gchk) and best[3] > GUIDE_TOL and best[2] <= rim_tol and best[4] == 0:
        try:
            P2 = _nurbs_points(edge_polys, guide_polys, 0.5, 0.5)
            bs2 = _nurbs_fill(P2, None, 1.1, NURBS_TOL / 2, NURBS_MAXSEG * 2); f2, _t2 = folds(bs2, border=edge_polys); r2 = _dev(bs2, rim); g2 = _dev(bs2, gchk)
            h2 = _rise(bs2, edge_polys, guide_polys, loop) if (f2 == 0 and r2 <= rim_tol) else None
            if f2 == 0 and r2 <= rim_tol and g2 < best[3] and (h2 is None or best[6] is None or h2 <= best[6] + PRINT_TOL):
                best = ("mean plane, the finer pass for the added lines", bs2, r2, g2, 0, "enlarge 1.1, edge points every 0.5 mm, %d points, approximation %.3f / %d segments" % (len(P2), NURBS_TOL / 2, NURBS_MAXSEG * 2), h2)
        except Exception:
            pass
    if best is None or best[4] or (best[2] > rim_tol and rank is None):
        raise ValueError(("the best NURBS fill misses its rim by %.3f mm (limit %.2f) / folds %d cells" % (best[2], rim_tol, best[4])) if best else
                         "no NURBS fill: %s" % "; ".join(t[5] for t in tries))
    how_, bs, rdev, gdev, f_, note, rise_ = best
    info = {"how": "NURBS fill (%s start; %s): rim %.3f mm (limit %.2f), added lines %.3f mm%s" % (how_, note, rdev, rim_tol, gdev,
                   ("; THE INTERIOR RANKED - the try that held its rim rose more (R7W A4)" if rank else "")), "nu": bs.NbUPoles, "nv": bs.NbVPoles,
            "guides": len(guide_polys or ()), "rim_mm": round(rdev, 4), "folds": f_, "nurbs": True,
            "tries": [[t[0], str(t[5])[:60], (None if t[1] is None else round(float(t[2]), 4)), (None if t[6] is None else round(float(t[6]), 2)), t[4]] for t in tries]}
    if rank:
        info["rank"] = rank
        if progress:
            try: progress(rank)
            except Exception: pass
    if guide_polys: info["guide_before"] = round(gdev, 3); info["guide_after"] = round(gdev, 3)
    return bs, info


def _greville_uv(s):
    """R7W A10 (round 5's C6, its tested form): the parameters where a B-spline surface's own basis peaks - every pole's Greville abscissa (the mean of
    its degree interior knots) and each knot span's centre, in u and in v (a periodic knot vector: its knots and span centres)"""
    out = []
    for nc, deg, kn, mu in ((s.NbUPoles, s.UDegree, s.getUKnots(), s.getUMultiplicities()), (s.NbVPoles, s.VDegree, s.getVKnots(), s.getVMultiplicities())):
        kn = np.asarray(kn, float); kf = np.repeat(kn, np.asarray(mu, int)); mids = 0.5 * (kn[:-1] + kn[1:])
        g = np.array([kf[i + 1:i + deg + 1].mean() for i in range(nc)]) if len(kf) == nc + deg + 1 else kn
        out.append(np.unique(np.r_[g, mids]))
    return out


def _rim_uv(s, pts):
    """R7W A4 (verify-span-fill finding 10): the (u, v) range of a fill's OWN border on its surface - its rim points' parameters - so its rise is read on the
    face, never on the enlarged margin the approximation adds round it (sf0's patch 8: 4.61 mm read on the margin, 5.9 mm off the face; the face rises 1.144).
    None when it cannot be read (the whole surface is then read, as before)"""
    try:
        try: from FreeCAD import Vector as V3
        except ImportError: V3 = lambda *a: a
        P = np.asarray(pts, float).reshape(-1, 3); P = P[::max(1, len(P) // 200)]
        uv = np.array([s.parameter(V3(*[float(x) for x in p])) for p in P], float)
        if len(uv) < 3 or not np.isfinite(uv).all(): return None
        u0, u1, v0, v1 = s.bounds()
        r = (max(u0, float(uv[:, 0].min())), min(u1, float(uv[:, 0].max())), max(v0, float(uv[:, 1].min())), min(v1, float(uv[:, 1].max())))
        return r if (r[1] > r[0] and r[3] > r[2]) else None
    except Exception:
        return None


class _Balloon(ValueError):
    """31bq NN (B17 (4)): the balloon refusal's own exception - a numpy LinAlgError is a ValueError too, and re-raising every ValueError dropped a good fill a rung"""


def _balloon(s, edge_polys, guide_polys, info, what, tail, refuse=True, progress=None, loop=None, uv=None):
    """31bq B17 (plate) / N (the NURBS fill too): a surface through its edges may not rise far above them INSIDE the face - its heights over the loop's own
    plane, sampled inside the loop polygon, stay within the loop's (and the added lines') height range plus max(PLATE_BALLOON_MM, PLATE_BALLOON_FRAC x the
    loop's size). Raises ValueError with the number; info["balloon_mm"] records the rise."""
    try:
        _P = np.asarray(loop, float).reshape(-1, 3) if (loop is not None and len(loop) >= 3) else np.vstack([np.asarray(x_, float) for x_ in edge_polys])
        _c = _P.mean(0); _, _, _vh = np.linalg.svd(_P - _c, full_matrices=False); _e1, _e2, _n = _vh[0], _vh[1], _vh[2]
        _hl = (_P - _c) @ _n; _x = (_P - _c) @ _e1; _y = (_P - _c) @ _e2; _diag = float(np.linalg.norm(_P.max(0) - _P.min(0)))
        _lim = max(float(_os.environ.get("PLATE_BALLOON_MM", "2.0") or 2.0), float(_os.environ.get("PLATE_BALLOON_FRAC", "0.15") or 0.15) * _diag)
        _poly2 = np.c_[_x, _y]
        if guide_polys:
            try: _Pg = np.vstack([np.asarray(x_, float) for x_ in guide_polys]); _hl = np.concatenate([_hl, (_Pg - _c) @ _n])
            except Exception: pass
        _u0, _u1, _v0, _v1 = s.bounds(); _hs = []
        if uv is not None: _u0, _u1, _v0, _v1 = [float(x_) for x_ in uv]
        _uu, _vv = np.meshgrid(np.linspace(_u0, _u1, 25), np.linspace(_v0, _v1, 25)); _Q = []
        for a_, b_ in zip(_uu.ravel(), _vv.ravel()):
            _q = s.value(float(a_), float(b_)); _Q.append([_q.x, _q.y, _q.z])
        try:
            # over the
            _gu_, _gv_ = _greville_uv(s)
            _gu_ = [a_ for a_ in _gu_ if _u0 - 1e-12 <= a_ <= _u1 + 1e-12]; _gv_ = [b_ for b_ in _gv_ if _v0 - 1e-12 <= b_ <= _v1 + 1e-12]
            for a_ in _gu_:
                for b_ in _gv_:
                    _q = s.value(float(a_), float(b_)); _Q.append([_q.x, _q.y, _q.z])
        except Exception as _exg:
            info["balloon_greville"] = "the Greville samples failed (%s) - the grid and the tessellation only" % str(_exg)[:60]
            try:
                if progress: progress("the %s's rise: %s" % (what, info["balloon_greville"]))
            except Exception: pass
        try:
            # MeshPart
            _tv_ = s.toShape(_u0, _u1, _v0, _v1); _ld_ = max(0.05, _lim / 8.0)
            try:
                import MeshPart as _MP
                _mq_ = _MP.meshFromShape(Shape=_tv_, LinearDeflection=_ld_, AngularDeflection=0.8, Relative=False); _tq_ = [[p_.x, p_.y, p_.z] for p_ in _mq_.Points]
            except Exception:
                _tq_ = [[q_.x, q_.y, q_.z] for q_ in _tv_.tessellate(_ld_)[0]]
            if _tq_: _Q = _Q + _tq_
            else: info["balloon_tess"] = "the surface's tessellation gave no point - the 25 x 25 grid only"
        except Exception as _ext:      # recorded
            info["balloon_tess"] = "the surface's tessellation failed (%s) - the 25 x 25 grid only" % str(_ext)[:60]
            try:
                if progress: progress("the %s's rise: %s" % (what, info["balloon_tess"]))
            except Exception: pass
        _Q = np.array(_Q); _in = _inside((_Q - _c) @ _e1, (_Q - _c) @ _e2, _poly2)
        _hs = [float(h_) for h_ in ((_Q - _c) @ _n)[_in]]
        if not _hs:      # recorded
            info["balloon_unmeasured"] = "no sample of the surface lies inside its loop (a degenerate or collinear loop)"
            if progress: progress("the %s's rise over its border could not be measured (%s) - not judged; the look decides" % (what, info["balloon_unmeasured"]))
        if _hs:
            _over = max(0.0, max(_hs) - float(_hl.max()), float(_hl.min()) - min(_hs)); info["balloon_mm"] = round(_over, 2)
            if _over > _lim:
                _msg = "the %s %s %.1f mm past its border's own height range (limit %.1f) - the surface rose inside the face where no edge holds it (31bq B17); %s - split it with a wire across the rise, or add a guide line there" % (what, "BALLOONS" if refuse else "RISES", _over, _lim, tail)
                if refuse: raise _Balloon(_msg)
                info["balloon_note"] = _msg[:300]
                if progress: progress(_msg + " (recorded, not refused: the pictures and the solid's self-intersection gate decide - 31bq N)")
            elif _over > PRINT_TOL:      # over the
                # recorded  recorded
                _msg = "the %s RISES %.1f mm past its border's own height range (under its size limit %.1f, over the %.2f mm print tolerance) - recorded, not refused: the look decides (R7W A4)" % (what, _over, _lim, PRINT_TOL)
                if not refuse: info["balloon_note"] = _msg[:300]
                if progress: progress(_msg)
    except _Balloon: raise
    except Exception as _ebx:      # recorded
        info["balloon_unmeasured"] = str(_ebx)[:120]
        try:
            if progress: progress("the %s's rise over its border could not be measured (%s) - not judged; the look decides" % (what, str(_ebx)[:80]))
        except Exception: pass


def _rise(s, edge_polys, guide_polys, loop):
    """R7W A4: a fill's rise past its border's own height range, read by the balloon instrument itself - silent, never a refusal; None when unmeasured"""
    inf = {}
    try: _balloon(s, edge_polys, guide_polys, inf, "NURBS fill", "", refuse=False, progress=None, loop=loop,
                  uv=_rim_uv(s, loop if loop is not None else np.vstack([np.asarray(x_, float) for x_ in edge_polys])))
    except Exception: return None
    return inf.get("balloon_mm")


try:
    from _busy import busy as _busy_ctx
except Exception:
    _busy_ctx = None
_SPAN_DEPTH = [0]
def span_face(edge_polys, guide_polys=(), corner_deg=CORNER_DEG, step=1.0, vox_normals=None, nurbs=None, rim_tol=None, progress=None, trade_rim=None):
    """31bq B02 (3): the span declares itself BUSY to the runner's watchdog (the recorded kills b9 / b16h / b17 were silent spans at the cap); the inner
    recursion (the Coons start) runs under the outer declaration"""
    if _busy_ctx is None or _SPAN_DEPTH[0] > 0: return _span_face_inner(edge_polys, guide_polys, corner_deg, step, vox_normals, nurbs, rim_tol, progress, trade_rim)
    _SPAN_DEPTH[0] += 1
    try:
        with _busy_ctx("span_face through %d edge(s)%s" % (len(edge_polys), (" + %d added line(s)" % len(guide_polys)) if guide_polys else ""), 900):
            return _span_face_inner(edge_polys, guide_polys, corner_deg, step, vox_normals, nurbs, rim_tol, progress, trade_rim)
    finally:
        _SPAN_DEPTH[0] -= 1
def _span_face_inner(edge_polys, guide_polys=(), corner_deg=CORNER_DEG, step=1.0, vox_normals=None, nurbs=None, rim_tol=None, progress=None, trade_rim=None):
    """THE SPAN LADDER: (kind, payload, info) - "plane": payload (centre, normal) - four or more edges in one plane, no added line;
    "nurbs" (31az, FIRST - the client: "prioritize using NURBS"): the plate fill through the edges and added lines as one B-spline, when it holds its
    rim and does not fold; "coons": the B-spline Coons patch of the four sides (the border exact) when it does not fold; "plate": the smoothest
    height field over the face's own plane through its edges and added lines, trimmed by the wire, when the Coons patch folds (a concave
    outline) and the face is single-valued over its plane; else ValueError - the face is split with a wire. payload = the Part surface.
    nurbs=False skips the NURBS rung for this face (NURBS_SKIP in skin-build: a face the client's pictures showed wavy as a fill)."""
    loop, starts, order = order_loop(edge_polys)
    isp, c, n = planar(loop)
    if isp and not guide_polys:
        return "plane", (c, n), {"corners": None, "how": "planar boundary"}
    if NURBS if nurbs is None else nurbs:
        if progress: progress("NURBS fill through its %d edge(s)%s" % (len(edge_polys), (" + %d added line(s)" % len(guide_polys)) if guide_polys else ""))
        try:
            bs, ninfo = nurbs_face(edge_polys, guide_polys, lambda: surface_of(*span_face(edge_polys, (), corner_deg, step, vox_normals, nurbs=False)[:2]), rim_tol, loop=loop, progress=progress, trade_rim=trade_rim)
            _balloon(bs, edge_polys, guide_polys, ninfo, "NURBS fill", "its rim held", refuse=False, progress=progress, loop=loop, uv=_rim_uv(bs, loop))      # recorded
            return "nurbs", bs, ninfo
        except Exception as ex:
            nurbs_why = str(ex)[:160]
    else:
        nurbs_why = "NURBS skipped for this face"
    q, how = four_corners(loop, starts, corner_deg)
    info = {"how": how, "corners": [loop[k].tolist() for k in q], "guides": len(guide_polys), "nurbs": nurbs_why}
    pieces = side_pieces(loop, starts, q)
    if progress: progress("Coons patch of its four sides (%s)" % how)
    try:
        B = side_curve(pieces[0]); R = side_curve(pieces[1]); T = side_curve(pieces[2]); Lf = side_curve(pieces[3])
        T.reverse(); Lf.reverse()
        s = coons_surface(B, R, T, Lf)
        info.update({"nu": s.NbUPoles, "nv": s.NbVPoles})
        if guide_polys:
            sd = sides_of(loop, q); lu = max(_arc(np.asarray(sd[0]))[-1], _arc(np.asarray(sd[2]))[-1]); lv = max(_arc(np.asarray(sd[1]))[-1], _arc(np.asarray(sd[3]))[-1])
            refine(s, lu, lv, step); info["nu"], info["nv"] = s.NbUPoles, s.NbVPoles
            b_, a_ = guide_pull(s, guide_polys, step); info["guide_before"] = round(b_, 3); info["guide_after"] = round(a_, 3)
        f_, tot_ = folds(s, border=edge_polys); info["folds"] = f_; info["cells"] = tot_
        info["c0"] = bool(any(m >= 3 for m in s.getUMultiplicities()[1:-1]) or any(m >= 3 for m in s.getVMultiplicities()[1:-1]))
        if f_ == 0: return "coons", s, info
        coons_why = "the Coons patch of its four sides folds (%d of %d cells)" % (f_, tot_)
    except ValueError as ex:
        coons_why = "no Coons patch: %s" % ex
    if (NURBS if nurbs is None else nurbs) and NURBS_LOOSE_RIM > 0 and (rim_tol is None or rim_tol < NURBS_LOOSE_RIM):
        # THE LOOSE NURBS RUNG  its rim allowed up to
        if progress: progress("NURBS fill again, its rim allowed up to %.2f mm (the Coons patch folded; the plate rung is the last resort)" % NURBS_LOOSE_RIM)
        try:
            bs, ninfo = nurbs_face(edge_polys, guide_polys, lambda: surface_of(*span_face(edge_polys, (), corner_deg, step, vox_normals, nurbs=False)[:2]), NURBS_LOOSE_RIM, loop=loop, progress=progress, trade_rim=trade_rim)
            _balloon(bs, edge_polys, guide_polys, ninfo, "NURBS fill (loose rim)", "its rim held within %.2f" % NURBS_LOOSE_RIM, refuse=False, progress=progress, loop=loop, uv=_rim_uv(bs, loop))
            ninfo = dict(ninfo); ninfo["loose_rim"] = NURBS_LOOSE_RIM; ninfo["coons"] = coons_why; ninfo["how"] = "%s; the rim allowed up to %.2f mm after the Coons patch folded" % (ninfo.get("how", "NURBS fill"), NURBS_LOOSE_RIM)
            return "nurbs", bs, ninfo
        except Exception as ex:
            nurbs_why = "%s; loose (%.2f): %s" % (nurbs_why, NURBS_LOOSE_RIM, str(ex)[:120])
    if progress: progress("PLATE through its edges%s (the Coons patch folded)" % (" and added lines" if guide_polys else ""))
    try:
        s, pinfo = plate_surface(loop, guide_polys, vox_normals, step)
    except ValueError as ex:
        raise ValueError("%s; %s; NURBS: %s" % (coons_why, ex, nurbs_why))
    info.update(pinfo); info["coons"] = coons_why
    if guide_polys: info["guide_after"] = pinfo.get("fit_max_mm")
    _balloon(s, edge_polys, guide_polys, info, "PLATE", "%s; NURBS: %s" % (coons_why, nurbs_why), loop=loop, progress=progress)      # recorded
    return "plate", s, info


def surface_of(kind, payload):
    """the Part surface for span_face's result (needs FreeCAD)"""
    import Part
    from FreeCAD import Vector as V3
    if kind == "plane":
        c, n = payload; return Part.Plane(V3(*c), V3(*n))
    return payload


def twin_pairs(cen, n, c, tol=2.0, own=0.3):
    """31br A3 (2026-10-30): the twin of each face across the plane (n, c) - {face: twin} for every face whose centroid, reflected, lands within tol of another face's
    centroid on the other side; a face within `own` of the plane is its own twin (left out); masters = the faces on the + side of the plane. cen: {face: centroid (3,)}"""
    out = {}
    if not cen: return out, set()
    keys = list(cen); C = np.asarray([cen[k] for k in keys], float); sd = C @ np.asarray(n, float) - float(c)
    R = C - 2.0 * sd[:, None] * np.asarray(n, float)[None, :]
    for i, k in enumerate(keys):
        if abs(sd[i]) < own: continue
        d = np.linalg.norm(C - R[i], axis=1); d[i] = 9e9
        d[np.sign(sd) == np.sign(sd[i])] = 9e9
        j = int(np.argmin(d))
        if d[j] <= tol: out[k] = keys[j]
    masters = {k for k, v in out.items() if sd[keys.index(k)] > 0 and out.get(v) == k}
    out = {k: v for k, v in out.items() if out.get(v) == k}
    return out, masters


def edge_polys(edges, step=STEP_MM):
    """Part edges -> polylines sampled every `step` mm"""
    out = []
    for e in edges:
        n = max(3, int(e.Length / step) + 1)
        out.append(np.array([[q.x, q.y, q.z] for q in e.discretize(Number=n)]))
    return out

# stations
import math
import numpy as np
import FreeCAD, Part

def V3(x): return FreeCAD.Vector(float(x[0]), float(x[1]), float(x[2]))
def P3(v): return np.array([v.x, v.y, v.z], float)
def unit(v):
    v = np.asarray(v, float); n = np.linalg.norm(v)
    return v / n if n > 1e-15 else v

def spine(S_, NLp, NLq, R, convex=False):
    """the locus of the ball centres along a crease: S + (R / cos(beta/2)) along the bisector of the two faces' normals (into the air on a
    concave crease, into the material on a convex one) - the same beta and bisector _fillet_lines uses"""
    S_ = np.asarray(S_, float)
    NLp = np.broadcast_to(np.asarray(NLp, float), S_.shape); NLq = np.broadcast_to(np.asarray(NLq, float), S_.shape)
    b_ = NLp + NLq; b_ = b_ / np.maximum(np.linalg.norm(b_, axis=1), 1e-9)[:, None]
    beta_ = np.arccos(np.clip(np.einsum("ij,ij->i", NLp, NLq), -1, 1)); d_ = R / np.maximum(np.cos(beta_ / 2.0), 0.2)
    return S_ + ((-d_ if convex else d_)[:, None]) * b_

def _seg_seg(p1, q1, p2, q2):
    d1 = q1 - p1; d2 = q2 - p2; r = p1 - p2
    a = d1 @ d1; e = d2 @ d2; f = d2 @ r; eps = 1e-18
    if a <= eps and e <= eps: s = t = 0.0
    elif a <= eps: s = 0.0; t = float(np.clip(f / e, 0, 1))
    else:
        c = d1 @ r
        if e <= eps: t = 0.0; s = float(np.clip(-c / a, 0, 1))
        else:
            b = d1 @ d2; den = a * e - b * b
            s = float(np.clip((b * f - c * e) / den, 0, 1)) if den > eps else 0.0
            t = (b * s + f) / e
            if t < 0: t = 0.0; s = float(np.clip(-c / a, 0, 1))
            elif t > 1: t = 1.0; s = float(np.clip((b - c) / a, 0, 1))
    c1 = p1 + d1 * s; c2 = p2 + d2 * t
    return s, t, float(np.linalg.norm(c1 - c2)), c1, c2

def vertex_ball(spine_a, spine_b, tol=1e-3):
    """where the two spines come closest: fractional stations ia / ib, arc lengths la / lb from each spine's first sample, the closest points,
    their midpoint C, the gap; meet = they meet (gap within tol) away from both spines' end samples - a CONCAVE corner; else the approach is at
    the junction stations - a CONVEX corner (the ball pivots about the third edge)"""
    A = np.asarray(spine_a, float); B = np.asarray(spine_b, float); best = None
    for i in range(len(A) - 1):
        for j in range(len(B) - 1):
            s, t, d, c1, c2 = _seg_seg(A[i], A[i + 1], B[j], B[j + 1])
            if best is None or d < best[0] - 1e-12: best = (d, i + s, j + t, c1, c2)
    d, fa, fb, c1, c2 = best
    la = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(A, axis=0), axis=1))]); lb = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(B, axis=0), axis=1))])
    ia = int(min(int(fa), len(A) - 2)); ib = int(min(int(fb), len(B) - 2))
    La = la[ia] + (fa - ia) * (la[ia + 1] - la[ia]); Lb = lb[ib] + (fb - ib) * (lb[ib + 1] - lb[ib])
    end_a = fa < 1e-9 or fa > len(A) - 1 - 1e-9; end_b = fb < 1e-9 or fb > len(B) - 1 - 1e-9
    return dict(ia=fa, ib=fb, la=float(La), lb=float(Lb), len_a=float(la[-1]), len_b=float(lb[-1]), Ca=c1, Cb=c2, C=0.5 * (c1 + c2),
                gap=float(d), meet=bool(d <= tol and not (end_a and end_b)), at_end_a=bool(end_a), at_end_b=bool(end_b))

def _frame(nrm):
    nrm = unit(nrm); a = np.array([1.0, 0, 0]) if abs(nrm[0]) < 0.9 else np.array([0, 1.0, 0])
    e1 = unit(np.cross(nrm, a)); e2 = np.cross(nrm, e1); return e1, e2, nrm

def halfspace(point, nrm, size=200.0):
    """a box standing on the plane through point, on the side nrm points to"""
    e1, e2, nn = _frame(nrm); p = np.asarray(point, float)
    pts = [p + size * (sx * e1 + sy * e2) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1))]
    return Part.Face(Part.makePolygon([V3(x) for x in pts])).extrude(V3(nn * size))

def one_face(shape, what="a trim"):
    fs = shape.Faces
    if len(fs) != 1: raise RuntimeError("%s left %d faces (one expected)" % (what, len(fs)))
    return fs[0]

def _pts_from(edge, start, n):
    """n points along the edge, running from the end nearest start"""
    P = np.array([[q.x, q.y, q.z] for q in edge.discretize(Number=n)])
    if np.linalg.norm(P[0] - np.asarray(start, float)) > np.linalg.norm(P[-1] - np.asarray(start, float)): P = P[::-1]
    return P

def seg(a, b, tol=1e-4):
    """the straight edge a -> b, or None when they coincide"""
    a = np.asarray(a, float); b = np.asarray(b, float)
    return Part.LineSegment(V3(a), V3(b)).toShape() if np.linalg.norm(b - a) > tol else None

def _path_point(path, s):
    """the point a fraction s along the polyline path"""
    P = [np.asarray(x, float) for x in path]; L = [np.linalg.norm(P[i + 1] - P[i]) for i in range(len(P) - 1)]; T = sum(L)
    if T < 1e-12: return P[0]
    d = s * T
    for i, l in enumerate(L):
        if d <= l or i == len(L) - 1: return P[i] + (P[i + 1] - P[i]) * (0.0 if l < 1e-12 else min(1.0, d / l))
        d -= l
    return P[-1]

def pivot_patch(end_a, end_b, J, axis, p_from, p_to, apex_path, n_rows=9, n_pts=17):
    """the CONVEX corner: the patch between blend a's end arc (p_from on face A -> Qa on the side face) and blend b's (p_to -> Qb), turning about
    the corner edge c (through J, direction axis) by the turn from p_from to p_to: rows of points turned about c, their shape blending from a's
    to b's, each row's apex point on apex_path (Qa -> Q0 -> Qb: the two offset ends and Q0 on c; one point when they coincide - then the exact
    revolve of arc a when the arcs are mirror images); returns (the BSpline surface, the turn in degrees, how far the pure revolve of arc a would
    miss arc b)"""
    axis = unit(axis); J = np.asarray(J, float)
    u = np.asarray(p_from, float) - J; u -= (u @ axis) * axis
    w = np.asarray(p_to, float) - J; w -= (w @ axis) * axis
    ang = math.degrees(math.atan2(float(axis @ np.cross(u, w)), float(u @ w)))
    Pa = _pts_from(end_a, p_from, n_pts); Pb = _pts_from(end_b, p_to, n_pts)
    Ra = FreeCAD.Rotation(V3(axis), ang); Pa_turned = np.array([J + P3(Ra.multVec(V3(x - J))) for x in Pa])
    gap = float(np.max(np.linalg.norm(Pa_turned - Pb, axis=1)))
    wj = (np.arange(n_pts) / (n_pts - 1.0)) ** 2
    rows = []
    for i in range(n_rows):
        s = i / (n_rows - 1.0); Ri = FreeCAD.Rotation(V3(axis), s * ang); Rj = FreeCAD.Rotation(V3(axis), (s - 1.0) * ang)
        A_ = np.array([J + P3(Ri.multVec(V3(x - J))) for x in Pa]); B_ = np.array([J + P3(Rj.multVec(V3(x - J))) for x in Pb])
        row = (1 - s) * A_ + s * B_; D = _path_point(apex_path, s) - row[-1]
        rows.append(row + wj[:, None] * D[None, :])
    rows = np.array(rows); rows[0] = Pa; rows[-1] = Pb
    apex_len = sum(np.linalg.norm(np.asarray(apex_path[i + 1], float) - np.asarray(apex_path[i], float)) for i in range(len(apex_path) - 1))
    degenerate = apex_len < 1e-3
    if degenerate:
        Q0 = np.asarray(apex_path[0], float)
        for i in range(n_rows): rows[i, -1] = Q0 - 0.003 * unit(Q0 - rows[i, -2])
    bs = Part.BSplineSurface(); bs.interpolate([[V3(x) for x in r] for r in rows])
    if degenerate:
        for i in range(1, bs.NbUPoles + 1): bs.setPole(i, bs.NbVPoles, V3(Q0))
    return bs, ang, gap

def _boundary_pts(b, start, n):
    """n points along a boundary given as an edge, a list of edges (a polyline of them), a list of points, or one point (degenerate)"""
    if b is None: return None
    if isinstance(b, Part.Shape) and b.ShapeType == "Edge": return _pts_from(b, start, n)
    if isinstance(b, (list, tuple)) and b and isinstance(b[0], Part.Shape):
        w = Part.Wire(Part.__sortEdges__(list(b))) if len(b) > 1 else b[0]
        P = np.array([P3(q) for q in w.discretize(Number=n)])
        return P if np.linalg.norm(P[0] - np.asarray(start, float)) <= np.linalg.norm(P[-1] - np.asarray(start, float)) else P[::-1]
    if isinstance(b, (list, tuple)) and b and not isinstance(b[0], Part.Shape) and len(np.asarray(b, float).shape) == 2:
        P = np.asarray(b, float)
        if len(P) == 1: return np.repeat(P, n, axis=0)
        return np.array([_path_point(P, s) for s in np.linspace(0, 1, n)]) if np.linalg.norm(P[0] - np.asarray(start, float)) <= np.linalg.norm(P[-1] - np.asarray(start, float)) else np.array([_path_point(P[::-1], s) for s in np.linspace(0, 1, n)])
    return np.repeat(np.asarray(b, float)[None, :], n, axis=0)

def coons_patch(L, R, B, T, n_s=9, n_t=17):
    """the surface THROUGH four boundaries: L (s = 0) and R (s = 1) run from the B side to the T side; B (t = 0) runs from L's start to R's start,
    T (t = 1) from L's end to R's end. Each is an edge, a polyline of edges, a list of points, or one point (a degenerate side - the apex of a
    corner patch). The bilinear Coons blend of the four, interpolated; a degenerate side's poles set on its point. Returns the BSpline surface."""
    Lp = _boundary_pts(L, None, n_t) if False else None
    def _ends(b):
        P = _boundary_pts(b, np.zeros(3), 3); return P[0], P[-1]
    Bp0, Bp1 = _ends(B); Tp0, Tp1 = _ends(T)
    Lpts = _boundary_pts(L, 0.5 * (Bp0 + Bp1), n_t); Rpts = _boundary_pts(R, 0.5 * (Bp0 + Bp1), n_t)
    Bpts = _boundary_pts(B, Lpts[0], n_s); Tpts = _boundary_pts(T, Lpts[-1], n_s)
    P00, P01, P10, P11 = Lpts[0], Lpts[-1], Rpts[0], Rpts[-1]
    grid = np.zeros((n_s, n_t, 3))
    for i, s in enumerate(np.linspace(0, 1, n_s)):
        for j, tt in enumerate(np.linspace(0, 1, n_t)):
            grid[i, j] = (1 - s) * Lpts[j] + s * Rpts[j] + (1 - tt) * Bpts[i] + tt * Tpts[i] - ((1 - s) * (1 - tt) * P00 + (1 - s) * tt * P01 + s * (1 - tt) * P10 + s * tt * P11)
    grid[0] = Lpts; grid[-1] = Rpts; grid[:, 0] = Bpts; grid[:, -1] = Tpts
    degB = np.linalg.norm(Bpts[-1] - Bpts[0]) < 1e-3 and all(np.linalg.norm(x - Bpts[0]) < 1e-3 for x in Bpts); degT = np.linalg.norm(Tpts[-1] - Tpts[0]) < 1e-3 and all(np.linalg.norm(x - Tpts[0]) < 1e-3 for x in Tpts)
    if degB:
        for i in range(n_s): grid[i, 0] = grid[i, 1] + 0.003 * unit(Bpts[0] - grid[i, 1])
    if degT:
        for i in range(n_s): grid[i, -1] = grid[i, -2] + 0.003 * unit(Tpts[0] - grid[i, -2])
    bs = Part.BSplineSurface(); bs.interpolate([[V3(x) for x in row] for row in grid])
    if degB:
        for i in range(1, bs.NbUPoles + 1): bs.setPole(i, 1, V3(Bpts[0]))
    if degT:
        for i in range(1, bs.NbUPoles + 1): bs.setPole(i, bs.NbVPoles, V3(Tpts[0]))
    return bs

def fan_patch(ma, mb, X, far_path, n_rows=9, n_pts=17):
    """the CONCAVE corner's closing face between two mitre edges that start at X (ma: X -> Qa on blend a, mb: X -> Qb on blend b): rows of points
    blending from ma to mb, their far ends along far_path (Qa -> J -> Qb: the side faces' edges up to the junction), the X column degenerate"""
    X = np.asarray(X, float)
    Pa = _pts_from(ma, X, n_pts); Pb = _pts_from(mb, X, n_pts)
    wj = (np.arange(n_pts) / (n_pts - 1.0)) ** 2
    rows = []
    for i in range(n_rows):
        s = i / (n_rows - 1.0); row = (1 - s) * Pa + s * Pb; D = _path_point(far_path, s) - row[-1]
        rows.append(row + wj[:, None] * D[None, :])
    rows = np.array(rows); rows[0] = Pa; rows[-1] = Pb
    for i in range(n_rows): rows[i, 0] = rows[i, 1] + 0.003 * unit(X - rows[i, 1])
    bs = Part.BSplineSurface(); bs.interpolate([[V3(x) for x in r] for r in rows])
    for i in range(1, bs.NbUPoles + 1): bs.setPole(i, 1, V3(X))
    return bs

def _on_both(p, Sa, Sb, it=60):
    """31bq YY (2): a point brought onto BOTH surfaces by averaged projections (each step the mean of its two feet) - a point of their intersection near it"""
    p = np.asarray(p, float)
    for _ in range(it):
        v = V3(p); ua, va = Sa.parameter(v); ub, vb = Sb.parameter(v); q = 0.5 * (P3(Sa.value(ua, va)) + P3(Sb.value(ub, vb)))
        if np.linalg.norm(q - p) < 1e-6: return q
        p = q
    return p

def mitre_gap(e_, faces, n=30):
    """31bq YY (2): how far the edge lies from the faces at worst (n + 1 samples along it)"""
    Q_ = [e_.valueAt(e_.FirstParameter + (e_.LastParameter - e_.FirstParameter) * q / float(n)) for q in range(n + 1)]
    return max(max(float(f_.distToShape(Part.Vertex(p_))[0]) for p_ in Q_) for f_ in faces)

def true_mitre(face_a, face_b, X, C, reach=0.15, reach_x=1.0, ok_gap=0.1):
    """the CONCAVE corner's one mitre: the intersection curve of the two blend surfaces from X (on the common face) to C (the contact on the corner
    edge), as one cubic edge with its ends set exactly on them; None when the two surfaces' intersection does not reach both within `reach`.
    31bq YY (B25): at X both blends run TANGENT to the common face - a glancing meet the kernel's section gives out on (fill18's 53 leg | 97: 0.28 mm
    short of X): within reach_x the section is CARRIED ON to X as it is to C; a carried curve is taken only when it lies within ok_gap of BOTH blends"""
    X = np.asarray(X, float); C = np.asarray(C, float)
    try: sec = face_a.section(face_b)
    except Exception: return None
    eds = [e for e in sec.Edges if e.Length > 1e-6]
    if not eds: return None
    def _d(e, p): return float(e.distToShape(Part.Vertex(V3(p)))[0])
    cur = min(eds, key=lambda e: _d(e, X)); dX_ = _d(cur, X)
    if dX_ > reach_x: return None
    got = [cur]; used = {cur.hashCode()}
    while _d(got[-1], C) > reach and len(got) < len(eds):
        tip = got[-1]; ends = [P3(tip.Vertexes[0].Point), P3(tip.Vertexes[-1].Point)]
        nxt = [e for e in eds if e.hashCode() not in used and min(np.linalg.norm(P3(v.Point) - q) for v in (e.Vertexes[0], e.Vertexes[-1]) for q in ends) < 0.05]
        if not nxt: break
        got.append(nxt[0]); used.add(nxt[0].hashCode())
    short = min(_d(e, C) for e in got)
    if short > 3.0: return None
    w = Part.Wire(Part.__sortEdges__(got)) if len(got) > 1 else got[0]
    n = max(12, int(w.Length / 0.1) + 1); P = np.array([P3(q) for q in w.discretize(Number=n)])
    if np.linalg.norm(P[0] - X) > np.linalg.norm(P[-1] - X): P = P[::-1]
    i0 = int(np.argmin(np.linalg.norm(P - X, axis=1))); i1 = int(np.argmin(np.linalg.norm(P - C, axis=1)))
    if i1 <= i0 + 2: return None
    P = P[i0:i1 + 1]
    if dX_ > reach: P = np.vstack([X[None, :], P])
    else: P[0] = X
    if short > reach:
        P = np.vstack([P, C[None, :]])
    else: P[-1] = C
    if dX_ > reach or short > reach:
        try:
            Sa_, Sb_ = face_a.Surface, face_b.Surface; segs_ = ([0] if dX_ > reach else []) + ([len(P) - 2] if short > reach else []); out_ = [P[0]]
            for i_ in range(1, len(P)):
                if (i_ - 1) in segs_:
                    a_, b_ = P[i_ - 1], P[i_]; m_ = int(np.linalg.norm(b_ - a_) / 0.03)
                    for k_ in range(1, m_ + 1): out_.append(_on_both(a_ + (b_ - a_) * k_ / float(m_ + 1), Sa_, Sb_))
                out_.append(P[i_])
            Q2_ = [out_[0]]
            for p_ in out_[1:-1]:
                if np.linalg.norm(p_ - Q2_[-1]) > 1e-3: Q2_.append(p_)
            if len(Q2_) > 1 and np.linalg.norm(out_[-1] - Q2_[-1]) <= 1e-3: Q2_[-1] = out_[-1]
            else: Q2_.append(out_[-1])
            if len(Q2_) >= 3: P = np.array(Q2_)
        except Exception: pass
    cv = Part.BSplineCurve(); cv.interpolate([V3(x) for x in P]); e_ = cv.toShape()
    if (dX_ > reach or short > reach) and ok_gap is not None:      # planar mitre
        try:
            if mitre_gap(e_, (face_a, face_b)) > ok_gap: return None
        except Exception: return None
    return e_

def mitre_edge(face, X, Qa, Qb, start, end, size=200.0):
    """the CONCAVE corner: the plane through X, Qa and Qb cut through the blend face - its section curve from start to end (two of those points),
    as one cubic edge with its ends set exactly on them; None when the plane misses the face there"""
    X = np.asarray(X, float); Qa = np.asarray(Qa, float); Qb = np.asarray(Qb, float)
    n = np.cross(Qa - X, Qb - X)
    if np.linalg.norm(n) < 1e-9: n = np.cross(Qa - X, np.array([0, 0, 1.0]))
    n = unit(n); e1, e2, nn = _frame(n)
    pl = Part.Face(Part.makePolygon([V3(X + size * (sx * e1 + sy * e2)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1))]))
    sec = face.section(pl); eds = [e for e in sec.Edges if e.Length > 1e-6]
    if not eds: return None
    S = np.asarray(start, float); E = np.asarray(end, float)
    def _d(e, p): return float(e.distToShape(Part.Vertex(V3(p)))[0])
    cur = min(eds, key=lambda e: _d(e, S)); got = [cur]; used = {cur.hashCode()}
    while _d(got[-1], E) > 0.05 and len(got) < len(eds):
        tip = got[-1]; ends = [P3(tip.Vertexes[0].Point), P3(tip.Vertexes[-1].Point)]
        nxt = [e for e in eds if e.hashCode() not in used and min(np.linalg.norm(P3(v.Point) - q) for v in (e.Vertexes[0], e.Vertexes[-1]) for q in ends) < 0.05]
        if not nxt: break
        got.append(nxt[0]); used.add(nxt[0].hashCode())
    w = Part.Wire(Part.__sortEdges__(got)) if len(got) > 1 else got[0]
    n_ = max(12, int(w.Length / 0.1) + 1); P = np.array([P3(q) for q in w.discretize(Number=n_)])
    if np.linalg.norm(P[0] - S) > np.linalg.norm(P[-1] - S): P = P[::-1]
    i0 = int(np.argmin(np.linalg.norm(P - S, axis=1))); i1 = int(np.argmin(np.linalg.norm(P - E, axis=1)))
    if i1 <= i0 + 2: return None
    P = P[i0:i1 + 1]; P[0] = S; P[-1] = E
    cv = Part.BSplineCurve(); cv.interpolate([V3(x) for x in P]); return cv.toShape()

def pivot_patch_bounded(end_a, end_b, J, axis, p_from, p_to, corner_arc_edge=None, apex_path=None, n_rows=9, n_pts=17, floor_on=None):
    """the CONVEX corner patch: the rotation of arc a about the corner edge towards arc b (G1 to both blends by construction). Its floor edge is the
    rotation's OWN trace of the common face's offset point (returned as an edge - the common face's border round the corner); its apex is the straight
    piece of the corner edge between the two contacts (one point when they coincide). Returns (surface, turn deg, floor edge)"""
    axis = unit(axis); J = np.asarray(J, float)
    u = np.asarray(p_from, float) - J; u -= (u @ axis) * axis
    w = np.asarray(p_to, float) - J; w -= (w @ axis) * axis
    ang = math.degrees(math.atan2(float(axis @ np.cross(u, w)), float(u @ w)))
    Pa = _pts_from(end_a, p_from, n_pts); Pb = _pts_from(end_b, p_to, n_pts)
    _wj_apex = (np.arange(n_pts) / (n_pts - 1.0)) ** 2
    if apex_path is not None and len(apex_path) >= 2 and float(np.linalg.norm(np.asarray(apex_path[0], float) - Pa[-1])) > float(np.linalg.norm(np.asarray(apex_path[-1], float) - Pa[-1])):
        apex_path = list(apex_path)[::-1]
    rows = []
    for i in range(n_rows):
        s = i / (n_rows - 1.0); Ri = FreeCAD.Rotation(V3(axis), s * ang); Rj = FreeCAD.Rotation(V3(axis), (s - 1.0) * ang)
        A_ = np.array([J + P3(Ri.multVec(V3(x - J))) for x in Pa]); B_ = np.array([J + P3(Rj.multVec(V3(x - J))) for x in Pb])
        w = s * s * (3 - 2 * s)
        row_ = (1 - w) * A_ + w * B_
        if apex_path is not None and len(apex_path) >= 2:      # corner edge
            row_ = row_ + _wj_apex[:, None] * (_path_point(apex_path, w) - row_[-1])[None, :]
        rows.append(row_)
    rows = np.array(rows); rows[0] = Pa; rows[-1] = Pb
    if floor_on is not None:
        tt = np.linspace(0, 1, n_pts)
        for i in range(1, n_rows - 1):
            try:
                uu, vv = floor_on.parameter(V3(rows[i, 0])); q = floor_on.value(uu, vv); d0 = P3(q) - rows[i, 0]
                rows[i] = rows[i] + ((1 - tt) ** 2)[:, None] * d0[None, :]
            except Exception: pass
    apex_len = float(np.linalg.norm(Pb[-1] - Pa[-1]))
    degenerate = apex_len < 1e-3
    if degenerate:
        Q0 = Pa[-1]
        for i in range(n_rows): rows[i, -1] = Q0 - 0.003 * unit(Q0 - rows[i, -2])
    bs = Part.BSplineSurface(); bs.interpolate([[V3(x) for x in r] for r in rows])
    if degenerate:
        for i in range(1, bs.NbUPoles + 1): bs.setPole(i, bs.NbVPoles, V3(Q0))
    u0, u1, v0, v1 = bs.bounds(); cands = []
    for cv in (bs.vIso(v0), bs.vIso(v1), bs.uIso(u0), bs.uIso(u1)):
        e = cv.toShape(); ends = [P3(e.Vertexes[0].Point), P3(e.Vertexes[-1].Point)]
        err = min(np.linalg.norm(ends[0] - Pa[0]) + np.linalg.norm(ends[1] - Pb[0]), np.linalg.norm(ends[0] - Pb[0]) + np.linalg.norm(ends[1] - Pa[0]))
        cands.append((float(err), e))
    floor = min(cands, key=lambda c: c[0])[1]
    return bs, ang, floor

def sphere_fan(arc_a, arc_b, far_arc, X, C, R, n_rows=9, n_pts=17):
    """31bq R7v (B26): THE VERTEX BALL's spherical triangle through three end arcs - arc_a and arc_b run from the ball's contact X on the common face to its contacts
    on the two side faces, far_arc between those two (the corner edge's own blend's end arc); rows blended from arc_a to arc_b, their far ends ON far_arc, every
    interior point put ON the sphere (C, R) - the X column degenerate (fan_patch's form; the 31bp prototype's sphere_patch_2 measured the revolve / the cut sphere
    within 0.12 mm of the kernel's own Sphere face). G1 to the three blends by geometry: all four are tangent to one ball along the arcs."""
    X = np.asarray(X, float); C = np.asarray(C, float)
    Pa = _pts_from(arc_a, X, n_pts); Pb = _pts_from(arc_b, X, n_pts); Pf = _pts_from(far_arc, Pa[-1], n_rows)
    rows = []
    for i in range(n_rows):
        s = i / (n_rows - 1.0); row = (1 - s) * Pa + s * Pb; row[-1] = Pf[i]
        for j in range(1, n_pts - 1): row[j] = C + R * unit(row[j] - C)
        rows.append(row)
    rows = np.array(rows); rows[0] = Pa; rows[-1] = Pb
    for i in range(n_rows): rows[i, 0] = rows[i, 1] + 0.003 * unit(X - rows[i, 1])
    bs = Part.BSplineSurface(); bs.interpolate([[V3(x) for x in r] for r in rows])
    for i in range(1, bs.NbUPoles + 1): bs.setPole(i, 1, V3(X))
    return bs

def refit_end(edge, old_pt, new_pt, step=0.2):
    """the edge re-fitted (cubic, C2, 1e-3) with the end nearest old_pt moved onto new_pt; the other end kept exactly"""
    n = max(6, int(edge.Length / step) + 1); P = np.array([[q.x, q.y, q.z] for q in edge.discretize(Number=n)])
    cv = Part.BSplineCurve(); cv.approximate(Points=[V3(x) for x in P], DegMin=3, DegMax=3, Tolerance=1e-3, Continuity="C2")
    at_start = np.linalg.norm(P[0] - np.asarray(old_pt, float)) <= np.linalg.norm(P[-1] - np.asarray(old_pt, float))
    cv.setPole(1, V3(new_pt if at_start else P[0])); cv.setPole(cv.NbPoles, V3(P[-1] if at_start else new_pt)); return cv.toShape()

def corner_arc(J, p_from, p_to, axis):
    """face A's border round a convex corner: the circular arc about the corner edge (J, axis) from p_from to p_to - the trace of the pivoting
    ball's contact on A (the pivot patch's own bottom edge)"""
    axis = unit(axis); J = np.asarray(J, float)
    u = np.asarray(p_from, float) - J; w = np.asarray(p_to, float) - J
    um = u - (u @ axis) * axis; wm = w - (w @ axis) * axis
    ang = math.atan2(float(axis @ np.cross(um, wm)), float(um @ wm)); half = FreeCAD.Rotation(V3(axis), math.degrees(0.5 * ang))
    mid = J + P3(half.multVec(V3(u)))
    return Part.Arc(V3(np.asarray(p_from, float)), V3(mid), V3(np.asarray(p_to, float))).toShape()

def mitre_trim(face_a, face_b, J, d_a, d_b, size=200.0):
    """the CONCAVE corner with c sharp: both blends swept to the junction, trimmed by the bisector plane through J (normal d_a + d_b: d_a along
    crease a INTO J, d_b along crease b OUT of J); returns the two trimmed faces and the plane's normal"""
    m = unit(np.asarray(d_a, float) + np.asarray(d_b, float))
    fa = one_face(face_a.common(halfspace(J, -m, size)), "the mitre of blend a"); fb = one_face(face_b.common(halfspace(J, m, size)), "the mitre of blend b")
    return fa, fb, m

def cross_point(e1, e2, tol=0.5):
    """where two edges cross (their closest points within tol): the midpoint, or None"""
    d, pts, _ = e1.distToShape(e2)
    if d > tol or not pts: return None
    a, b = pts[0]; return 0.5 * (P3(a) + P3(b))

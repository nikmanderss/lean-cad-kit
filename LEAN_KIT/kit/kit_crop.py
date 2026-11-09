"""kit_crop.py - `kit crop` and `kit splice`: THE MESH ROUTE'S UNIT OF WORK IS A CROP, NEVER THE BODY (2026-09-24).

the client, 2026-09-24: "the orchestrator had the whole body being processed multiple times in today's / last night's mesh
editing. This is extremely wasteful. Things like that should not be allowed unless there is absolutely no other way."
The route as it ran (MESH_JOB\\RECIPE.md v2): per piece, extract a region -> refine the WHOLE base at the core wall ->
weld the piece onto the WHOLE base (a 72-77 MB whole-body STL per piece) -> whole-mesh gates (~10 min per edit) -> a
final that refined the base at 27 cores and welded 27 pieces. The body was the operand of every step.

THE CROP.  kit crop <body.stl> --box x0 x1 y0 y1 z0 z1 [--margin 3] --out <crop.stl>
Cuts the body's tessellation on the six planes of the box grown by the margin. Triangles fully inside go to the crop;
triangles that straddle a wall are SPLIT on it (kitlib_render.split_at_plane, the same clip both ways, so the two sides
share their cut points); the crop's open loops on the walls are then CAPPED (ear-clipped, holes bridged) so the crop is
a CLOSED solid. Every field, sign, extract, core, weld and gate of the route runs on it, in seconds, and the caps sit a
margin away from the edit. Nothing of the body is written back at this point: the sidecar `<crop>.crop.json` records
the body, the box, the margin and the cap triangles, and that is all a splice needs.

THE SPLICE.  kit splice <edited_crop.stl> --crop <crop.json> --out <body2.stl> [--into <body.stl>]
             kit splice --pieces <list.json> --out <body2.stl> [--into <body.stl>]      (many pieces, ONE pass)
Cuts the target body FRESH at the same box (seconds, numpy), checks that what it finds there is the unedited crop
(so an earlier splice did not reach this box - the sequential case is safe by construction or refused), drops the
caps, checks the edited crop's rim against the fresh remainder's rim point for point (an edit that reached the crop
wall is REFUSED: widen the box), snaps and joins by exact vertex identity, and writes ONE body. Outside the boxes the
result is the target's own triangles by index - an identity proved by a count, not a tolerance.

Pure numpy; no kernel; binary STL through kitlib_render.
"""
import os, sys, json, time, hashlib
for _v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitlib_render as R


def _split_at(V, T, P, tol=0.02):
    """31bx (R4 F3): the triangle whose BOUNDARY edge holds a point of P (within tol of the segment, off its ends) is split at that point - the exact closure of a
    splice T-junction, where the print pass used to close the open-edge pair. Returns (V, T, the number split)."""
    V = np.asarray(V, float).copy(); T = np.asarray(T, int).copy(); n = 0
    if not len(T) or P is None or not len(P): return V, T, 0
    E = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
    u, cnt = np.unique(E, axis=0, return_counts=True); bnd = u[cnt == 1]
    for p in np.asarray(P, float):
        if not len(bnd): break
        A = V[bnd[:, 0]]; Bv = V[bnd[:, 1]]; ab = Bv - A; L2 = (ab * ab).sum(1); L2[L2 == 0] = 1e-30
        t = np.clip(((p - A) * ab).sum(1) / L2, 0.0, 1.0); d = np.linalg.norm(A + ab * t[:, None] - p, axis=1); k = int(np.argmin(d))
        if d[k] > tol or t[k] < 1e-3 or t[k] > 1.0 - 1e-3: continue
        a, b = int(bnd[k, 0]), int(bnd[k, 1])
        hit = np.where(((T == a) | (T == b)).sum(1) == 2)[0]
        if len(hit) != 1: continue
        ti = int(hit[0]); tri = [int(x) for x in T[ti]]; qi = len(V); V = np.vstack([V, p[None, :]])
        T[ti] = [qi if v == b else v for v in tri]; T = np.vstack([T, np.array([[qi if v == a else v for v in tri]], int)]); n += 1
        bnd = np.vstack([bnd[:k], bnd[k + 1:], np.sort(np.array([[a, qi], [qi, b]]), 1)])
    return V, T, n

COLLAPSE_MM = 1e-4
COLLAPSE_PASSES = 100

def _collapse_short(u, T2):
    """31ca (R4 F5): THE SHORT-EDGE COLLAPSE - every edge of T2 shorter than COLLAPSE_MM has its two vertices merged into one at their midpoint (each pass a set of
    edges with no vertex in common, shortest first; T2 re-indexed); the triangles that held both ends then repeat a vertex and the caller's test drops them. Nothing
    opens: the two triangles across a collapsed edge lose it, and their other edges pair with the neighbours. Repeated until no such edge remains, at most
    COLLAPSE_PASSES passes. Returns (u, T2, edges collapsed, passes, cap hit)."""
    u = np.asarray(u, float); T2 = np.asarray(T2, int); n = 0; passes = 0; cap = False
    while len(T2):
        E = np.vstack([T2[:, [0, 1]], T2[:, [1, 2]], T2[:, [2, 0]]]); E = E[E[:, 0] != E[:, 1]]
        if not len(E): break
        E = np.unique(np.sort(E, 1), axis=0); L = np.linalg.norm(u[E[:, 0]] - u[E[:, 1]], axis=1); s = np.where(L < COLLAPSE_MM)[0]
        if not len(s): break
        if passes >= COLLAPSE_PASSES: cap = True; break
        s = s[np.argsort(L[s], kind="stable")]; used = set(); mp = np.arange(len(u)); u = u.copy()
        for k in s:
            a, b = int(E[k, 0]), int(E[k, 1])
            if a in used or b in used: continue
            used.add(a); used.add(b); u[a] = 0.5 * (u[a] + u[b]); mp[b] = a; n += 1
        T2 = mp[T2]; passes += 1
    return u, T2, n, passes, cap

def _weld_degenerate(V, T, info=None):
    """31bz (R4 F5): the result as the STL will hold it - the vertices welded at float32 (an STL's own resolution), a triangle with a repeated vertex dropped (its two
    edges coincide: nothing opens); a triangle of three DISTINCT collinear vertices is counted and kept (dropping it would open a hole - it is a T-junction's business).
    printcheck had read 'degenerate (zero-area) facets - 1' on a spliced mesh where the print pass closed it a step later. 31ca: between the weld and the drop, the
    SHORT-EDGE COLLAPSE (_collapse_short: an edge under COLLAPSE_MM merged at its midpoint) - the facet the 31bz weld left was three distinct float32 vertices with a
    0.000045 mm edge, area 1.4e-9 mm2. Returns (V, T, dropped, collinear_kept); `info` (a dict) gets collapsed / collapse_passes / collapse_cap_hit."""
    V = np.asarray(V, float); T = np.asarray(T, int)
    if not len(T): return V, T, 0, 0
    q = V.astype(np.float32).astype(np.float64); u, inv = np.unique(q, axis=0, return_inverse=True); inv = np.asarray(inv).reshape(-1)
    T2 = inv[T]
    u, T2, _ncl, _npass, _cap = _collapse_short(u, T2)
    if info is not None: info.update({"collapsed": int(_ncl), "collapse_passes": int(_npass), "collapse_cap_hit": bool(_cap)})
    keep = (T2[:, 0] != T2[:, 1]) & (T2[:, 1] != T2[:, 2]) & (T2[:, 0] != T2[:, 2])
    P = u[T2[keep]]; area = 0.5 * np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1)
    return u, T2[keep], int((~keep).sum()), int((area <= 1e-9).sum())


WELD_TOL = 1e-6
ON_PLANE = 1e-6
ON_PLANE_F32 = 2e-3
RIM_TOL = 2e-3
BODY_SIZED = 400000


def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stl_count(path):
    """the triangle count out of a binary STL header, without reading the body"""
    try:
        with open(path, "rb") as fh:
            head = fh.read(84)
        if len(head) < 84:
            return 0
        n = int(np.frombuffer(head[80:84], "<u4")[0])
        return n if os.path.getsize(path) >= 84 + 50 * n else 0
    except OSError:
        return 0


def stl_bbox(path):
    """(lo, hi) of a binary STL's vertices, or None"""
    try:
        V, T = R.read_stl(path)
    except SystemExit:
        return None
    if len(V) == 0:
        return None
    return V.min(0).astype(float), V.max(0).astype(float)


SIDECARS = (".crop.json", ".extract.json")


def body_sized(path, body_extent=None):
    """(True, why) when an STL is the whole body rather than a crop or a patch: it has no local-by-construction sidecar
    (`<stem>.crop.json` from kit crop, `<stem>.extract.json` from the extract, or `<file>.base.json` from a refine whose
    `from` is a crop) AND either it holds more than BODY_SIZED triangles or it spans more than half of the body's extent
    on every axis (body_extent = (lo, hi), e.g. the union of the atlas boxes). A 124k-triangle body passes the count
    test and fails the extent test, which is the point."""
    stem = os.path.splitext(path)[0]
    if any(os.path.isfile(stem + s) for s in SIDECARS):
        return False, "carries a kit sidecar"
    if os.path.isfile(path + ".base.json"):
        try:
            src = str(json.load(open(path + ".base.json", encoding="utf-8")).get("from", ""))
        except (OSError, ValueError):
            src = ""
        if src.lower().endswith(".stl") and os.path.isfile(os.path.splitext(src)[0] + ".crop.json"):
            return False, "a refined crop"
    n = stl_count(path)
    if body_extent is not None:
        bb = stl_bbox(path)
        if bb is not None:
            lo, hi = body_extent
            span = np.asarray(hi, float) - np.asarray(lo, float)
            mine = bb[1] - bb[0]
            with np.errstate(divide="ignore", invalid="ignore"):
                frac = np.where(span > 0, mine / span, 0.0)
            if bool((frac > 0.5).all()):
                return True, "%s triangles spanning %d%% x %d%% x %d%% of the body" % (format(n, ","), *[int(100 * f) for f in frac])
            return False, "%s triangles inside %d%% x %d%% x %d%% of the body's extent" % (format(n, ","), *[int(100 * f) for f in frac])
    if n > BODY_SIZED:
        return True, "%s triangles, and no body extent on record to judge the span by (kit atlas extent)" % format(n, ",")
    return False, "%s triangles" % format(n, ",")


def _planes(box):
    """the six (point, inward normal) planes of a box; inside = (p - p0) . n >= 0 for all six"""
    x0, x1, y0, y1, z0, z1 = [float(v) for v in box]
    return [((x0, 0, 0), (1, 0, 0)), ((x1, 0, 0), (-1, 0, 0)), ((0, y0, 0), (0, 1, 0)), ((0, y1, 0), (0, -1, 0)),
            ((0, 0, z0), (0, 0, 1)), ((0, 0, z1), (0, 0, -1))]


def _grow(box, margin):
    return [box[0] - margin, box[1] + margin, box[2] - margin, box[3] + margin, box[4] - margin, box[5] + margin]


def _tri_keys(V, T):
    """one hashable key per triangle, independent of vertex order and of index order. The key is the triangle's
    coordinates AS FLOAT32 - what a binary STL holds - so a crop cut in float64 and read back from its STL, and the
    same box cut fresh from the same float32 body, key identically; a rounding to decimals would not (a value near a
    rounding boundary keys differently on the two sides a few per cent of the time)."""
    P = np.asarray(V, float)[np.asarray(T, int)].astype(np.float32)
    keys = []
    for tri in P:
        keys.append(tuple(sorted((float(v[0]), float(v[1]), float(v[2])) for v in tri)))
    return keys


def inside_body(points, V, T, chunk=250000):
    """True where a point is inside the closed surface (V, T): ray parity along each of the three axes, majority
    vote (a ray through a vertex or an edge, or through one of the body's own cracks, can miscount on one axis).
    Vectorised over triangles in chunks; a few hundred points against a 1.5 M-triangle body is seconds."""
    points = np.asarray(points, float).reshape(-1, 3)
    if len(points) == 0:
        return np.zeros(0, bool)
    V = np.asarray(V, float); T = np.asarray(T, int)
    votes = np.zeros(len(points), int)
    for ax in range(3):
        b, c = (ax + 1) % 3, (ax + 2) % 3
        cnt = np.zeros(len(points), int)
        for s in range(0, len(T), chunk):
            P = V[T[s:s + chunk]]
            A, B, C = P[:, 0], P[:, 1], P[:, 2]
            for i, q in enumerate(points):
                d1 = (B[:, b] - A[:, b]) * (q[c] - A[:, c]) - (B[:, c] - A[:, c]) * (q[b] - A[:, b])
                d2 = (C[:, b] - B[:, b]) * (q[c] - B[:, c]) - (C[:, c] - B[:, c]) * (q[b] - B[:, b])
                d3 = (A[:, b] - C[:, b]) * (q[c] - C[:, c]) - (A[:, c] - C[:, c]) * (q[b] - C[:, b])
                hit = ((d1 >= 0) & (d2 >= 0) & (d3 >= 0)) | ((d1 <= 0) & (d2 <= 0) & (d3 <= 0))
                area = d1 + d2 + d3
                hit &= np.abs(area) > 1e-18
                if not hit.any():
                    continue
                w1 = d2[hit] / area[hit]; w2 = d3[hit] / area[hit]; w3 = d1[hit] / area[hit]
                a_at = w1 * A[hit, ax] + w2 * B[hit, ax] + w3 * C[hit, ax]
                cnt[i] += int((a_at > q[ax]).sum())
        votes += (cnt % 2 == 1)
    return votes >= 2


def _compact(V, T):
    """drop the vertices T does not use"""
    T = np.asarray(T, int)
    if len(T) == 0:
        return np.zeros((0, 3)), T
    used, inv = np.unique(T.reshape(-1), return_inverse=True)
    return np.asarray(V, float)[used], np.asarray(inv).reshape(-1, 3)


def _open_edges(T):
    T = np.asarray(T, int)
    if len(T) == 0:
        return np.zeros((0, 2), int), 0
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); es = np.sort(e, axis=1)
    uniq, cnt = np.unique(es, axis=0, return_counts=True)
    return uniq[cnt == 1], int((cnt > 2).sum())


def health(V, T):
    """(open edges, non-manifold edges) of an index-welded mesh"""
    oe, nm = _open_edges(T)
    return int(len(oe)), nm


def _loops(segs):
    """closed loops (vertex index lists) from a list of edges; an open chain is dropped (it cannot be capped)"""
    adj = {}
    for a, b in segs:
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen, loops, open_chains = set(), [], 0
    for s in list(adj):
        if s in seen:
            continue
        loop, cur, prev = [s], s, None
        seen.add(s)
        closed = False
        while True:
            nxt = [q for q in adj.get(cur, []) if q != prev and (q not in seen or q == s)]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            if cur == s:
                closed = True
                break
            seen.add(cur); loop.append(cur)
            if len(loop) > 500000:
                break
        if closed and len(loop) >= 3:
            loops.append(loop)
        else:
            open_chains += 1
    return loops, open_chains


def _signed_area(P):
    return 0.5 * float(np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]))


def _bridge_holes(outer, holes):
    """ONE weakly-simple polygon from an outer loop (CCW) and its holes (CW): each hole is joined to the outer polygon
    by a bridge edge, rightmost hole first (the classic method; a bridge from the hole's rightmost vertex along +x to
    the nearest edge of the polygon so far). outer/holes are lists of (index, (x, y)). Returns the combined list."""
    poly = list(outer)
    for hole in sorted(holes, key=lambda h: -max(p[1][0] for p in h)):
        mi = max(range(len(hole)), key=lambda i: hole[i][1][0])
        hole = hole[mi:] + hole[:mi]
        M = np.asarray(hole[0][1], float)
        best, bi = None, -1
        for i in range(len(poly)):
            A = np.asarray(poly[i][1], float); B = np.asarray(poly[(i + 1) % len(poly)][1], float)
            if (A[1] > M[1]) == (B[1] > M[1]):
                continue
            if abs(B[1] - A[1]) < 1e-15:
                continue
            x = A[0] + (M[1] - A[1]) * (B[0] - A[0]) / (B[1] - A[1])
            if x >= M[0] - 1e-12 and (best is None or x < best):
                best, bi = x, i
        if bi < 0:
            continue
        A = np.asarray(poly[bi][1], float); B = np.asarray(poly[(bi + 1) % len(poly)][1], float)
        I = np.array([best, M[1]])
        pi = bi if A[0] >= B[0] else (bi + 1) % len(poly)
        P = np.asarray(poly[pi][1], float)
        def _inside(Q):
            def s(a, b, c):
                return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            d1, d2, d3 = s(M, I, Q), s(I, P, Q), s(P, M, Q)
            neg = (d1 < 0) or (d2 < 0) or (d3 < 0); pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
            return not (neg and pos)
        cand, cbest = pi, None
        for i in range(len(poly)):
            if i == pi:
                continue
            Q = np.asarray(poly[i][1], float)
            if not _inside(Q):
                continue
            prv = np.asarray(poly[i - 1][1], float); nxt = np.asarray(poly[(i + 1) % len(poly)][1], float)
            reflex = ((Q[0] - prv[0]) * (nxt[1] - Q[1]) - (Q[1] - prv[1]) * (nxt[0] - Q[0])) < 0
            if not reflex:
                continue
            ang = abs(np.arctan2(Q[1] - M[1], Q[0] - M[0]))
            if cbest is None or ang < cbest:
                cbest, cand = ang, i
        pi = cand
        poly = poly[:pi + 1] + hole + [hole[0]] + [poly[pi]] + poly[pi + 1:]
    return poly


def _cap_plane(V, loops, p0, n):
    """cap triangles (global index triples) for the closed loops lying on one plane: each outer loop is ear-clipped
    with its holes bridged in; an island inside a hole is its own outer. Oriented with normal -n (out of the crop)."""
    r2, u2 = R._plane_basis(n)
    P2 = [(V[lp] - p0) @ np.column_stack([r2, u2]) for lp in loops]
    depth = []
    for k in range(len(loops)):
        depth.append(sum(1 for j in range(len(loops)) if j != k and len(P2[j]) >= 3 and R._point_in_poly(P2[k][0], P2[j])))
    tris = []
    for k, lp in enumerate(loops):
        if depth[k] % 2 == 1:
            continue
        outer = [(lp[i], tuple(P2[k][i])) for i in range(len(lp))]
        if _signed_area(P2[k]) < 0:
            outer = outer[::-1]
        holes = []
        for j, lq in enumerate(loops):
            if j == k or depth[j] != depth[k] + 1 or not R._point_in_poly(P2[j][0], P2[k]):
                continue
            h = [(lq[i], tuple(P2[j][i])) for i in range(len(lq))]
            if _signed_area(P2[j]) > 0:
                h = h[::-1]
            holes.append(h)
        poly = _bridge_holes(outer, holes) if holes else outer
        pts = np.asarray([p for _, p in poly], float)
        for a, b, c in R._ear_clip(pts):
            tri = np.array([poly[a][0], poly[b][0], poly[c][0]])
            if len(set(tri.tolist())) < 3:
                continue
            q = V[tri]
            nn = np.cross(q[1] - q[0], q[2] - q[0])
            if nn @ n > 0:
                tri = tri[[0, 2, 1]]
            tris.append(tri)
    return tris


def _classify(V, T, planes, eps=1e-9):
    """(full_in, full_out, straddling) masks over T against the box's six planes; a vertex ON a plane counts inside.
    FULL_OUT IS 'SOME WALL HAS ALL THREE VERTICES OUTSIDE IT', NOT 'NO VERTEX INSIDE THE BOX': a triangle whose three
    vertices are each outside a different wall still passes through the box's corner (measured: the corner piece of
    a crop went missing and two of its four wall loops could not close). A triangle with no separating wall that
    still misses the box is partitioned and yields no inside piece - harmless."""
    P = np.asarray(V, float)[np.asarray(T, int)]
    inside_v = np.ones((len(T), 3), bool)
    separated = np.zeros(len(T), bool)
    for p0, n in planes:
        d = (P - np.asarray(p0, float)) @ np.asarray(n, float)
        inside_v &= d >= -eps
        separated |= (d < -eps).all(1)
    full_in = inside_v.all(1)
    full_out = separated & ~full_in
    return full_in, full_out, ~full_in & ~full_out


def _clip_convex(P, planes, eps=1e-9):
    """a convex polygon (list of 3-D points, in order) clipped to the inside of every plane - Sutherland-Hodgman"""
    poly = [np.asarray(p, float) for p in P]
    for p0, n in planes:
        if not poly:
            break
        p0 = np.asarray(p0, float); n = np.asarray(n, float)
        d = [float((p - p0) @ n) for p in poly]
        out = []
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            da, db = d[i], d[(i + 1) % len(poly)]
            if da >= -eps:
                out.append(a)
            if (da > eps and db < -eps) or (da < -eps and db > eps):
                w = da / (da - db)
                out.append(a + (b - a) * w)
        poly = out
    return poly


def _difference(P, Q, tol=1e-7):
    """triangles (3-D, the triangle's own winding) covering the TRIANGLE P MINUS its clipped part Q (Q convex, inside P,
    sharing P's winding). Every vertex used is a vertex of P or of Q - nothing is added on P's edges beyond the points
    of Q that lie there, so a neighbour that was not cut shares P's edges unchanged (no T-junction), and a neighbour
    that was cut shares exactly the points the box put on the common edge."""
    A, B, C = [np.asarray(p, float) for p in P]
    nrm = np.cross(B - A, C - A)
    L = float(np.linalg.norm(nrm))
    if L <= 0:
        return []
    nrm /= L
    u = B - A; u /= float(np.linalg.norm(u)); v = np.cross(nrm, u)
    scale = max(float(np.linalg.norm(B - A)), float(np.linalg.norm(C - A)), float(np.linalg.norm(C - B)))
    tol = tol * scale

    def to2(p):
        return np.array([float((p - A) @ u), float((p - A) @ v)])
    tri3 = [A, B, C]; tri2 = [to2(p) for p in tri3]
    Q3 = [np.asarray(q, float) for q in Q]
    if len(Q3) >= 3:
        area = 0.0
        q2 = [to2(q) for q in Q3]
        for i in range(len(q2)):
            area += q2[i][0] * q2[(i + 1) % len(q2)][1] - q2[(i + 1) % len(q2)][0] * q2[i][1]
        if area < 0:
            Q3 = Q3[::-1]
    m = len(Q3)
    nodes = []
    def _node(p):
        nodes.append(np.asarray(p, float)); return len(nodes) - 1
    corner_id = [_node(p) for p in tri3]
    q_node, on_edge = [], []
    for q in Q3:
        nid, where = None, None
        for k in range(3):
            if np.linalg.norm(q - tri3[k]) <= tol:
                nid, where = corner_id[k], ("corner", k); break
        if nid is None:
            for k in range(3):
                a, b = tri3[k], tri3[(k + 1) % 3]
                ab = b - a; L2 = float(ab @ ab)
                t = float((q - a) @ ab) / L2
                if -1e-9 <= t <= 1 + 1e-9 and np.linalg.norm(q - (a + ab * t)) <= tol:
                    nid, where = _node(q), ("edge", k, t); break
        if nid is None:
            nid, where = _node(q), ("interior",)
        q_node.append(nid); on_edge.append(where)
    on_boundary = [w[0] != "interior" for w in on_edge]
    q_index_of_node = {q_node[i]: i for i in range(m)}
    outer = []
    for k in range(3):
        outer.append(corner_id[k])
        pts = sorted([(w[2], q_node[i]) for i, w in enumerate(on_edge) if w[0] == "edge" and w[1] == k])
        outer.extend(nid for _, nid in pts if nid not in outer)
    n_out = len(outer)
    pos = {nid: i for i, nid in enumerate(outer)}
    qedge = set()
    for i in range(m):
        qedge.add((q_node[i], q_node[(i + 1) % m])); qedge.add((q_node[(i + 1) % m], q_node[i]))

    def nxt(nid):
        return outer[(pos[nid] + 1) % n_out]

    def _tris_of(poly_ids):
        pts = np.asarray([to2(nodes[i]) for i in poly_ids], float)
        out = []
        for a, b, c in R._ear_clip(pts):
            ia, ib, ic = poly_ids[a], poly_ids[b], poly_ids[c]
            if len({ia, ib, ic}) < 3:
                continue
            out.append([nodes[ia], nodes[ib], nodes[ic]])
        return out

    if not any(on_boundary):
        outer_l = [(nid, tuple(to2(nodes[nid]))) for nid in outer]
        hole = [(q_node[i], tuple(to2(nodes[q_node[i]]))) for i in range(m)][::-1]
        poly = _bridge_holes(outer_l, [hole])
        pts = np.asarray([p for _, p in poly], float)
        out = []
        for a, b, c in R._ear_clip(pts):
            ia, ib, ic = poly[a][0], poly[b][0], poly[c][0]
            if len({ia, ib, ic}) < 3:
                continue
            out.append([nodes[ia], nodes[ib], nodes[ic]])
        return out
    tris = []
    visited = set()
    starts = [nid for nid in outer if nid in q_index_of_node and (nid, nxt(nid)) not in qedge]
    for s in starts:
        if s in visited:
            continue
        poly, cur, guard = [s], s, 0
        while guard < 4 * (n_out + m) + 8:
            guard += 1
            while (cur, nxt(cur)) not in qedge:
                visited.add(cur)
                cur = nxt(cur)
                if cur == s:
                    break
                poly.append(cur)
                if cur in q_index_of_node:
                    break
            if cur == s:
                break
            i = q_index_of_node[cur]
            while True:
                i = (i - 1) % m
                nid = q_node[i]
                if nid == s:
                    cur = s; break
                poly.append(nid)
                if on_boundary[i]:
                    cur = nid; break
            if cur == s:
                break
        tris.extend(_tris_of(poly))
    return tris


def _refine_edges(P, pts, tol=1e-7):
    """the triangle P (3 points), whole, with every point of `pts` that lies strictly inside one of its edges inserted
    there - triangulated on those vertices alone, so a neighbour cut at the same point shares it. No point inside an
    edge: the triangle itself."""
    A, B, C = [np.asarray(p, float) for p in P]
    tri = [A, B, C]
    scale = max(float(np.linalg.norm(B - A)), float(np.linalg.norm(C - A)), float(np.linalg.norm(C - B)), 1e-12)
    tol = tol * scale
    on = {0: [], 1: [], 2: []}
    for q in pts:
        q = np.asarray(q, float)
        if any(np.linalg.norm(q - v) <= tol for v in tri):
            continue
        for k in range(3):
            a, b = tri[k], tri[(k + 1) % 3]
            ab = b - a; L2 = float(ab @ ab)
            if L2 <= 0:
                continue
            t = float((q - a) @ ab) / L2
            if 1e-9 < t < 1 - 1e-9 and np.linalg.norm(q - (a + ab * t)) <= tol:
                if all(abs(t - t2) > 1e-9 for t2, _ in on[k]):
                    on[k].append((t, q))
                break
    if not any(on.values()):
        return [P]
    poly = []
    for k in range(3):
        poly.append(tri[k])
        poly.extend(q for _, q in sorted(on[k], key=lambda x: x[0]))
    nrm = np.cross(B - A, C - A); L = float(np.linalg.norm(nrm))
    if L <= 0:
        return [P]
    nrm /= L; u = B - A; u /= float(np.linalg.norm(u)); v = np.cross(nrm, u)
    P2 = np.asarray([[float((p - A) @ u), float((p - A) @ v)] for p in poly], float)
    out = []
    for a, b, c in R._ear_clip(P2):
        if len({a, b, c}) < 3:
            continue
        out.append([poly[a], poly[b], poly[c]])
    return out or [P]


def _partition(V, sT, planes):
    """the straddling triangles cut by the BOX - not by six infinite planes. Each triangle's inside piece is its
    intersection with the box (a convex polygon, fanned); its outside piece is the triangle minus that polygon,
    triangulated on the triangle's own vertices plus the polygon's. Cutting along infinite planes instead put cut
    points on edges shared with triangles that were never cut, and every such point was a T-junction: an open-edge
    pair in the spliced body (measured 48 on a 3,376-triangle test body) and a false rim mismatch at the splice.
    Returns (inside_V, inside_T, outside_V, outside_T), each an unwelded soup."""
    V = np.asarray(V, float); sT = np.asarray(sT, int)
    ins, outs = [], []
    for tri in sT:
        P = V[tri]
        Q = _clip_convex(P, planes)
        if len(Q) >= 3:
            q2 = np.asarray(Q, float)
            area = 0.5 * float(np.linalg.norm(sum(np.cross(q2[i] - q2[0], q2[i + 1] - q2[0]) for i in range(1, len(q2) - 1))))
        else:
            area = 0.0
        tri_area = 0.5 * float(np.linalg.norm(np.cross(P[1] - P[0], P[2] - P[0])))
        # open edges
        if area <= 1e-20 * max(tri_area, 1e-30):
            # open edges
            outs.extend(_refine_edges(P, Q))
            continue
        for i in range(1, len(Q) - 1):
            ins.append([Q[0], Q[i], Q[i + 1]])
        if area >= tri_area * (1 - 1e-12):
            continue
        outs.extend(_difference(P, Q))
    iV = np.asarray(ins, float).reshape(-1, 3); oV = np.asarray(outs, float).reshape(-1, 3)
    return iV, np.arange(len(iV)).reshape(-1, 3), oV, np.arange(len(oV)).reshape(-1, 3)


def crop(V, T, box, margin=3.0, eps=1e-9):
    """(crop_V, crop_T, n_cap, remainder_V, remainder_T, report). The crop is closed (capped) and its LAST n_cap
    triangles are the caps; the remainder is the body minus the crop, open where the crop was."""
    V = np.asarray(V, float); T = np.asarray(T, int)
    gbox = _grow([float(v) for v in box], float(margin))
    planes = _planes(gbox)
    full_in, full_out, strad = _classify(V, T, planes, eps)
    inV, inT, outV, outT = _partition(V, T[strad], planes)
    cV = V[T[full_in]].reshape(-1, 3); cT = np.arange(len(cV)).reshape(-1, 3)
    if len(inT):
        cT = np.vstack([cT, inT + len(cV)]); cV = np.vstack([cV, inV])
    cV, cT, _, _ = R._weld(cV, cT, [], WELD_TOL)
    open_e, _ = _open_edges(cT)
    base_open = int(len(open_e))
    # open edges
    on_plane = [np.abs((cV - np.asarray(p0, float)) @ np.asarray(n, float)) <= ON_PLANE for p0, n in planes]
    lo = [gbox[0], gbox[2], gbox[4]]; hi = [gbox[1], gbox[3], gbox[5]]
    extra_V, corner_idx = [], {}

    def _corner(ix, iy, iz):
        key = (ix, iy, iz)
        if key not in corner_idx:
            corner_idx[key] = len(cV) + len(extra_V)
            extra_V.append([hi[0] if ix else lo[0], hi[1] if iy else lo[1], hi[2] if iz else lo[2]])
        return corner_idx[key]

    edge_segs = {}
    mids, mid_of = [], []
    for a in range(3):
        b, c = (a + 1) % 3, (a + 2) % 3
        for sb in (0, 1):
            for sc in (0, 1):
                pb, pc = 2 * b + sb, 2 * c + sc
                nodes = [int(i) for i in np.where(on_plane[pb] & on_plane[pc])[0]]
                coords = [(float(cV[i][a]), i) for i in nodes]
                cb = [(lo[a], ("corner", 0)), (hi[a], ("corner", 1))]
                allc = sorted(coords + cb, key=lambda t: t[0])
                for (ca, ia), (cb_, ib) in zip(allc[:-1], allc[1:]):
                    if cb_ - ca <= 1e-9:
                        continue
                    m = [0.0, 0.0, 0.0]
                    m[a] = 0.5 * (ca + cb_); m[b] = hi[b] if sb else lo[b]; m[c] = hi[c] if sc else lo[c]
                    mids.append(m); mid_of.append((pb, pc, ia, ib))
                edge_segs[(pb, pc)] = []
    inside = inside_body(mids, V, T) if mids else np.zeros(0, bool)

    def _node_index(tag, a_axis, sb, sc, b, c):
        if isinstance(tag, tuple) and tag[0] == "corner":
            ix = [0, 0, 0]; ix[a_axis] = tag[1]; ix[b] = sb; ix[c] = sc
            return _corner(ix[0], ix[1], ix[2])
        return int(tag)

    for (pb, pc, ia, ib), ins in zip(mid_of, inside):
        if not ins:
            continue
        b, sb = pb // 2, pb % 2; c, sc = pc // 2, pc % 2
        a = 3 - b - c
        edge_segs[(pb, pc)].append((_node_index(ia, a, sb, sc, b, c), _node_index(ib, a, sb, sc, b, c)))
    if extra_V:
        cV = np.vstack([cV, np.asarray(extra_V, float)])
    cap_T, open_chains, on_wall_tris = [], 0, 0
    for k, (p0, n) in enumerate(planes):
        p0 = np.asarray(p0, float); n = np.asarray(n, float)
        on = on_plane[k]
        on_wall_tris += int(on[cT].all(1).sum())
        segs = [(int(a_), int(b_)) for a_, b_ in open_e if on[a_] and on[b_]]
        for (pb, pc), ss in edge_segs.items():
            if k in (pb, pc):
                segs.extend(ss)
        if not segs:
            continue
        loops, oc = _loops(segs)
        open_chains += oc
        cap_T.extend(_cap_plane(cV, loops, p0, n))
    cap_T = np.asarray(cap_T, int).reshape(-1, 3)
    cT_all = np.vstack([cT, cap_T]) if len(cap_T) else cT
    rV, rT = _compact(V, T[full_out])
    if len(outT):
        rT = np.vstack([rT, outT + len(rV)]); rV = np.vstack([rV, outV])
    o_after, nm_after = health(cV, cT_all)
    rep = {"box": [float(v) for v in box], "margin": float(margin), "grown_box": gbox,
           "body_triangles": int(len(T)), "fully_inside": int(full_in.sum()), "fully_outside": int(full_out.sum()),
           "straddling": int(strad.sum()), "crop_triangles": int(len(cT)), "cap_triangles": int(len(cap_T)),
           "crop_open_edges_before_cap": base_open, "crop_open_edges_after_cap": o_after, "crop_nonmanifold": nm_after,
           "wall_loops_not_closed": open_chains, "body_triangles_lying_in_a_wall": on_wall_tris,
           "remainder_triangles": int(len(rT))}
    return cV, cT_all, int(len(cap_T)), rV, rT, rep


def _match_rim(A, B, tol):
    """for each point of A the index of a point of B within tol (or -1), by grid hashing"""
    if len(A) == 0 or len(B) == 0:
        return np.full(len(A), -1, int)
    cell = tol
    keys = {}
    kb = np.floor(B / cell).astype(np.int64)
    for i, k in enumerate(map(tuple, kb)):
        keys.setdefault(k, []).append(i)
    out = np.full(len(A), -1, int)
    ka = np.floor(A / cell).astype(np.int64)
    for i in range(len(A)):
        best, bj = tol, -1
        kx, ky, kz = ka[i]
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in keys.get((kx + dx, ky + dy, kz + dz), ()):
                        d = float(np.linalg.norm(A[i] - B[j]))
                        if d <= best:
                            best, bj = d, j
        out[i] = bj
    return out


def _load_piece(edited_path, sidecar_path):
    meta = json.load(open(sidecar_path, encoding="utf-8"))
    eV, eT = R.read_stl(edited_path)
    eV, eT, _, _ = R._weld(eV, eT, [], WELD_TOL)
    return meta, eV, eT


def splice_many(bV, bT, pieces, say=print):
    """pieces: list of (meta, eV, eT) - the sidecar dict and the EDITED crop, index-welded. Returns (V, T, report)
    or raises RuntimeError with the refusal. bV/bT: the target body (unwelded is fine)."""
    bV = np.asarray(bV, float); bT = np.asarray(bT, int)
    touched = np.zeros(len(bT), int)
    per = []
    for meta, eV, eT in pieces:
        gbox = meta["grown_box"]; planes = _planes(gbox)
        full_in, full_out, strad = _classify(bV, bT, planes)
        touched += ~full_out
        per.append((meta, eV, eT, planes, full_in, strad))
    clash = int((touched > 1).sum())
    if clash:
        raise RuntimeError("REFUSED: %d body triangle(s) lie in the grown boxes of two pieces. Grown boxes must not share a\n"
                           "  triangle - shrink a margin or make the two pieces one crop." % clash)
    keep = touched == 0
    rV, rT = _compact(bV, bT[keep])
    kept_by_index = int(keep.sum())
    rep = {"target_triangles": int(len(bT)), "kept_by_index": kept_by_index, "pieces": []}
    for meta, eV, eT, planes, full_in, strad in per:
        name = os.path.basename(meta.get("crop", "?"))
        fV = bV[bT[full_in]].reshape(-1, 3); fT = np.arange(len(fV)).reshape(-1, 3)
        inV, inT, outV, outT = _partition(bV, bT[strad], planes)
        if len(inT):
            fT = np.vstack([fT, inT + len(fV)]); fV = np.vstack([fV, inV])
        fresh_keys = set(_tri_keys(fV, fT))
        if not os.path.isfile(meta["crop"]):
            raise RuntimeError("REFUSED: the unedited crop %s is gone; the splice cannot prove the box is untouched." % meta["crop"])
        if _md5(meta["crop"]) != meta["crop_md5"]:
            raise RuntimeError("REFUSED: %s changed since it was cut (md5). Edit a COPY of the crop, never the crop itself." % meta["crop"])
        uV, uT = R.read_stl(meta["crop"])
        ncap = int(meta["cap_triangles"])
        u_keys = set(_tri_keys(uV, uT[:len(uT) - ncap] if ncap else uT))
        if fresh_keys != u_keys:
            full_keys = set(_tri_keys(bV[bT[full_in]].reshape(-1, 3), np.arange(int(full_in.sum()) * 3).reshape(-1, 3)))
            edited_inside = full_keys - u_keys
            ndiff = len(fresh_keys ^ u_keys)
            if edited_inside or ndiff > max(64, int(0.02 * len(u_keys))):
                raise RuntimeError("REFUSED: the target body inside %s's box is not the surface the crop was cut from (%d triangles differ,\n"
                                   "  %d of them fully inside the box - an edit, not a float32 boundary).\n"
                                   "  Another edit reached this box. Cut this crop again from the CURRENT body and redo its edit, or\n"
                                   "  splice this piece first." % (name, ndiff, len(edited_inside)))
            say("  %s: %d straddler triangle(s) key differently between the crop and the fresh cut (float32 boundary, under the %d "
                "threshold; every fully-inside triangle matches) - accepted" % (name, ndiff, max(64, int(0.02 * len(u_keys)))))
        # recorded
        cap_keys = set(tuple(tuple(v) for v in tri) for tri in meta["cap_keys"])
        e_keys = _tri_keys(eV, eT)
        is_cap = np.array([k in cap_keys for k in e_keys], bool)
        caps_found = int(is_cap.sum())
        if caps_found < ncap:
            say("  %s: %d of %d cap triangles were not found in the edited crop (the edit re-tessellated a wall?) -\n"
                "    any remaining triangles lying in a wall plane that the unedited crop did not have are dropped as caps too"
                % (name, ncap - caps_found, ncap))
            was_body = np.array([k in u_keys for k in e_keys], bool)
            for p0, n in planes:
                on = np.abs((eV - np.asarray(p0, float)) @ np.asarray(n, float)) <= ON_PLANE_F32
                is_cap |= on[eT].all(1) & ~was_body
        eT2 = eT[~is_cap]
        # open edges
        wV_w, wT_w, _, _ = R._weld(outV, outT, [], WELD_TOL) if len(outT) else (np.zeros((0, 3)), np.zeros((0, 3), int), None, None)
        oe_w, _ = _open_edges(wT_w)
        on_wall = np.zeros(len(wV_w), bool)
        for p0, n in planes:
            on_wall |= np.abs((wV_w - np.asarray(p0, float)) @ np.asarray(n, float)) <= ON_PLANE
        wall_rim_idx = np.unique(oe_w[on_wall[oe_w].all(1)]) if len(oe_w) else np.zeros(0, int)
        # open edges
        gb = np.asarray(meta["grown_box"], float)
        inbox = np.all((wV_w >= gb[0::2] - 1e-6) & (wV_w <= gb[1::2] + 1e-6), axis=1)
        wall_rim_idx = wall_rim_idx[inbox[wall_rim_idx]]
        wall_rim = wV_w[wall_rim_idx]
        oe_e, _ = _open_edges(eT2)
        on_e = np.zeros(len(eV), bool)
        for p0, n in planes:
            on_e |= np.abs((eV - np.asarray(p0, float)) @ np.asarray(n, float)) <= ON_PLANE_F32
        e_rim_idx = np.unique(oe_e[on_e[oe_e].all(1)]) if len(oe_e) else np.zeros(0, int)
        inbox_e = np.all((eV >= gb[0::2] - 2e-3) & (eV <= gb[1::2] + 2e-3), axis=1)
        e_rim_idx = e_rim_idx[inbox_e[e_rim_idx]]
        e_rim = eV[e_rim_idx]
        m = _match_rim(e_rim, wall_rim, RIM_TOL)
        tj = []
        if (m < 0).any() and len(wall_rim):
            we = oe_w[on_wall[oe_w].all(1)] if len(oe_w) else np.zeros((0, 2), int)
            we = we[inbox[we].all(1)] if len(we) else we
            for i in np.where(m < 0)[0]:
                p = e_rim[i]
                if not len(we):
                    break
                A_ = wV_w[we[:, 0]]; B_ = wV_w[we[:, 1]]; ab = B_ - A_
                L2 = (ab * ab).sum(1); L2[L2 == 0] = 1e-30
                t = np.clip(((p - A_) * ab).sum(1) / L2, 0.0, 1.0)
                Q = A_ + ab * t[:, None]
                d = np.linalg.norm(Q - p, axis=1); k = int(np.argmin(d))
                if d[k] <= 0.02:
                    tj.append((int(i), Q[k]))
            if len(tj) > 4:
                tj = []
        unmatched_e = int((m < 0).sum()) - len(tj)
        matched_w = set(int(j) for j in m if j >= 0)
        tj_w = []
        miss_w = [j for j in range(len(wall_rim)) if j not in matched_w]
        dup_w = []
        if miss_w and len(matched_w):
            MW = wall_rim[sorted(matched_w)]
            for j in list(miss_w):
                if float(np.min(np.linalg.norm(MW - wall_rim[j], axis=1))) <= 0.01:
                    dup_w.append(j)
            miss_w = [j for j in miss_w if j not in dup_w]
            if dup_w:
                say("  %s: %d remainder wall point(s) are near-duplicates (within 0.01 mm) of matched points - the edited crop merged them" % (name, len(dup_w)))
        if miss_w and len(e_rim_idx):
            ee = oe_e[on_e[oe_e].all(1)] if len(oe_e) else np.zeros((0, 2), int)
            ee = ee[inbox_e[ee].all(1)] if len(ee) else ee
            if len(ee):
                A_ = eV[ee[:, 0]]; B_ = eV[ee[:, 1]]; ab = B_ - A_
                L2 = (ab * ab).sum(1); L2[L2 == 0] = 1e-30
                for j in miss_w:
                    p = wall_rim[j]
                    t = np.clip(((p - A_) * ab).sum(1) / L2, 0.0, 1.0)
                    d = np.linalg.norm(A_ + ab * t[:, None] - p, axis=1)
                    if float(d.min()) <= 0.02:
                        tj_w.append(j)
            if len(tj_w) > 8:
                tj_w = []
        unmatched_w = int(len(wall_rim) - len(matched_w) - len(tj_w) - len(dup_w))
        if tj_w:
            say("  %s: %d remainder wall point(s) the edited crop lacks lie on its rim edges - accepted as T-junctions (closed exactly below)"
                % (name, len(tj_w)))
        if unmatched_e or unmatched_w:
            worst = 0.0
            if len(e_rim) and len(wall_rim):
                for i in np.where(m < 0)[0][:5]:
                    worst = max(worst, float(np.min(np.linalg.norm(wall_rim - e_rim[i], axis=1))))
            raise RuntimeError("REFUSED: %s's rim is not the remainder's rim - %d edited-crop wall point(s) with no partner within\n"
                               "  %.3f mm (nearest %.3f mm) and %d remainder wall point(s) unmatched. The edit reached the crop wall:\n"
                               "  widen the box (or the margin) and cut the crop again." % (name, unmatched_e, RIM_TOL, worst, unmatched_w))
        eV = eV.copy()
        ok_m = m >= 0
        eV[e_rim_idx[ok_m]] = wall_rim[m[ok_m]]
        for i, q in tj:
            eV[e_rim_idx[i]] = q
        if tj:
            say("  %s: %d wall point(s) the remainder lacks lie on its rim - snapped onto the rim edge (T-junction - closed exactly below)"
                % (name, len(tj)))
        _ns1 = _ns2 = 0
        if tj: outV, outT, _ns1 = _split_at(outV, outT, [q_ for _i, q_ in tj])
        if tj_w: eV, eT2, _ns2 = _split_at(eV, eT2, wall_rim[np.asarray(tj_w, int)])
        if tj or tj_w: say("  %s: T-junctions closed exactly - %d of %d remainder rim edge(s) and %d of %d edited rim edge(s) split at their point%s" % (name, _ns1, len(tj), _ns2, len(tj_w), "" if _ns1 + _ns2 == len(tj) + len(tj_w) else " (the rest left for the print pass)"))
        for pv, pt in ((outV, outT), (eV, eT2)):
            if len(pt):
                rT = np.vstack([rT, pt + len(rV)]); rV = np.vstack([rV, pv])
        rep["pieces"].append({"crop": name, "edited_triangles": int(len(eT)), "caps_dropped": int(is_cap.sum()),
                              "spliced": int(len(eT2)), "rim_points": int(len(wall_rim)), "t_junctions": len(tj) + len(tj_w),
                              "straddlers_split": int(strad.sum()), "fully_inside_replaced": int(full_in.sum())})
    V, T, _, _ = R._weld(rV, rT, [], WELD_TOL)
    _winfo = {}
    V, T, _ndeg, _ncol = _weld_degenerate(V, T, _winfo)      # collapsed
    rep["degenerate_dropped"] = int(_ndeg); rep["collinear_kept"] = int(_ncol)
    rep["edges_collapsed"] = int(_winfo.get("collapsed", 0)); rep["collapse_cap_hit"] = bool(_winfo.get("collapse_cap_hit", False))
    o0, nm0 = health(*R._weld(bV, bT, [], WELD_TOL)[:2])
    o1, nm1 = health(V, T)
    rep.update({"result_triangles": int(len(T)), "open_edges_target": o0, "open_edges_result": o1,
                "nonmanifold_target": nm0, "nonmanifold_result": nm1,
                "outside_identity": "%d of %d target triangles outside the boxes kept by index, unmoved" % (kept_by_index, kept_by_index)})
    return V, T, rep


def cmd_crop(args, kit):
    r"""kit crop <body.stl> --box x0 x1 y0 y1 z0 z1 [--margin 3] --out <crop.stl>

    Cut the body's tessellation down to the box grown by the margin and CAP it closed; write the crop and its
    `<crop>.crop.json` sidecar. Every mesh-route step then runs on the crop (CC_BASE=<crop.stl>); `kit splice`
    puts the edited crop back. Put the walls through material or through air, never along a face: a wall that
    coincides with a face is reported and should be moved. Give the body's STL, not a brep: a crop never spends
    a kernel call."""
    a = kit._kv(args)
    src = a["_"][0] if a["_"] else ""
    box = [float(v) for v in str(a.get("--box", "")).replace(",", " ").split()] if a.get("--box") else []
    out = a.get("--out", "")
    if not src or len(box) != 6 or not out:
        print(cmd_crop.__doc__); return 2
    if not os.path.isfile(src):
        print("kit crop: no such file: %s" % src); return 2
    if not src.lower().endswith(".stl"):
        print("kit crop: give the body's STL (the tessellation cache's, or `kit measure export`'s). A brep here would\n"
              "  spend a kernel call the crop does not need."); return 2
    if box[0] >= box[1] or box[2] >= box[3] or box[4] >= box[5]:
        print("kit crop: --box is x0 x1 y0 y1 z0 z1 with each min below its max"); return 2
    margin = float(a.get("--margin", 3.0))
    t0 = time.time()
    V, T = R.read_stl(src)
    print("kit crop: %s - %d triangles, box %s, margin %g" % (os.path.basename(src), len(T), " ".join("%g" % v for v in box), margin))
    cV, cT, ncap, rV, rT, rep = crop(V, T, box, margin)
    if rep["crop_triangles"] == 0:
        print("kit crop REFUSED: no triangle of the body lies in the grown box - the box misses the part."); return 2
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    R.write_stl(out, cV, cT)
    side = os.path.splitext(out)[0] + ".crop.json"
    caps = cT[len(cT) - ncap:] if ncap else np.zeros((0, 3), int)
    rep.update({"body": os.path.abspath(src), "body_md5": _md5(src), "crop": os.path.abspath(out), "crop_md5": _md5(out),
                "cap_keys": [[list(v) for v in k] for k in _tri_keys(cV, caps)],
                "when": time.strftime("%Y-%m-%d %H:%M:%S"), "secs": round(time.time() - t0, 1)})
    with open(side, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=1)
    print("  crop      : %d triangles (%d whole, %d cut from %d straddlers) + %d caps -> %s"
          % (rep["crop_triangles"], rep["fully_inside"], rep["crop_triangles"] - rep["fully_inside"], rep["straddling"], ncap, out))
    print("  closed    : open edges %d -> %d after capping; non-manifold %d   (open edges left are the body's OWN cracks inside the box)"
          % (rep["crop_open_edges_before_cap"], rep["crop_open_edges_after_cap"], rep["crop_nonmanifold"]))
    if rep["wall_loops_not_closed"]:
        print("  WARNING   : %d wall loop(s) did not close (a crack of the body's own crosses the wall) - that wall is not capped there"
              % rep["wall_loops_not_closed"])
    if rep["body_triangles_lying_in_a_wall"]:
        print("  WARNING   : %d body triangle(s) lie IN a wall plane - the wall runs along a face. Move the margin so every\n"
              "              wall passes through material or through air." % rep["body_triangles_lying_in_a_wall"])
    print("  remainder : %d triangles stay the body's own, by index (not written - the splice cuts the target fresh)" % rep["remainder_triangles"])
    print("  sidecar   : %s   (%.1f s)" % (side, rep["secs"]))
    print("  Run the route with CC_BASE=%s (never the body). Then:\n  kit splice <edited copy.stl> --crop \"%s\" --out <body2.stl>" % (os.path.abspath(out), side))
    return 0


def cmd_splice(args, kit):
    r"""kit splice <edited_crop.stl> --crop <crop.json> --out <body2.stl> [--into <body.stl>] [--dry-run]
    kit splice --pieces <list.json> --out <body2.stl> [--into <body.stl>] [--dry-run]

    The edited crop(s) back into the body, in ONE pass: the target (--into, default the crop's own body) is cut
    fresh at each box and must show the unedited crop there (another edit that reached the box is refused); the
    caps are dropped; each rim is matched to the remainder's point for point (an edit that reached a wall is
    refused - widen the box); the pieces are joined by exact vertex identity and one body is written. Outside the
    boxes the result is the target's own triangles by index. `<list.json>` is `[{"edited": <stl>, "crop": <json>},
    ...]` - splice every piece of a rework in one call rather than writing the body once per piece.
    --dry-run: every check and every line, nothing written. LINEAGE: without --into the target is the crop's OWN
    body, so two per-side pieces cut from one body and spliced separately keep only the second - the second goes
    --into the first's --out (a sibling splice from the same body in the same folder is warned about)."""
    a = kit._kv(args)
    dry = bool(a.get("--dry-run"))
    out = a.get("--out", ""); into = a.get("--into", "")
    pairs = []
    if a.get("--pieces"):
        try:
            lst = json.load(open(a["--pieces"], encoding="utf-8"))
        except (OSError, ValueError) as e:
            print("kit splice: cannot read --pieces %s (%s)" % (a["--pieces"], e)); return 2
        if isinstance(lst, dict):
            lst = lst.get("pieces", [])
        for it in lst:
            pairs.append((it.get("edited") or it.get("stl") or "", it.get("crop") or it.get("sidecar") or ""))
    else:
        src = a["_"][0] if a["_"] else ""
        pairs.append((src, a.get("--crop", "")))
    if not out or not pairs or not all(p[0] and p[1] for p in pairs):
        print(cmd_splice.__doc__); return 2
    for e, c in pairs:
        for p in (e, c):
            if not os.path.isfile(p):
                print("kit splice: no such file: %s" % p); return 2
    t0 = time.time()
    pieces = []
    for e, c in pairs:
        meta, eV, eT = _load_piece(e, c)
        meta["_edited"] = os.path.abspath(e)
        pieces.append((meta, eV, eT))
    target = into or pieces[0][0]["body"]
    if not os.path.isfile(target):
        print("kit splice: the target body %s is not there (give --into <body.stl>)" % target); return 2
    for meta, _, _ in pieces:
        if not into and os.path.abspath(meta["body"]) != os.path.abspath(target):
            print("kit splice: the pieces were cut from different bodies; say which one with --into"); return 2
    if not into and _md5(target) != pieces[0][0]["body_md5"]:
        print("kit splice: %s changed since the crop was cut (md5). If it is the body after another splice, say so\n"
              "  with --into %s - the splice then checks the box is untouched." % (os.path.basename(target), target)); return 2
    t_md5 = _md5(target)
    if not into:
        print("  target    : the crop's OWN body %s (no --into) - a second piece cut from this body goes --into %s,"
              " or it drops this one" % (os.path.basename(target), os.path.basename(out)))
        try:
            for f in os.listdir(os.path.dirname(os.path.abspath(out)) or "."):
                if f.endswith(".splice.json") and f != os.path.basename(os.path.splitext(out)[0]) + ".splice.json":
                    j = json.load(open(os.path.join(os.path.dirname(os.path.abspath(out)), f), encoding="utf-8"))
                    if j.get("target_md5") == t_md5 and os.path.abspath(j.get("out", "")) != os.path.abspath(out):
                        print("  WARNING   : %s already spliced a piece into this same body -> %s. If that piece belongs in this\n"
                              "              result too, run this splice --into %s (the two results are SIBLINGS otherwise)"
                              % (f, os.path.basename(j.get("out", "?")), j.get("out", "?")))
        except (OSError, ValueError):
            pass
    bV, bT = R.read_stl(target)
    print("kit splice: %d piece(s) into %s (%d triangles)%s" % (len(pieces), os.path.basename(target), len(bT), "  [DRY RUN - nothing is written]" if dry else ""))
    try:
        V, T, rep = splice_many(bV, bT, pieces)
    except RuntimeError as e:
        print("kit splice %s" % e); return 2
    rep.update({"target": os.path.abspath(target), "target_md5": t_md5, "out": os.path.abspath(out),
                "edited": [p[0]["_edited"] for p in pieces], "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                "secs": round(time.time() - t0, 1), "dry_run": dry})
    if not dry:
        os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
        R.write_stl(out, V, T)
        rep["out_md5"] = _md5(out)
        with open(os.path.splitext(out)[0] + ".splice.json", "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=1)
    for pc in rep["pieces"]:
        print("  %-28s caps dropped %d, spliced %d triangles, rim points %d, replaced %d whole + %d cut"
              % (pc["crop"], pc["caps_dropped"], pc["spliced"], pc["rim_points"], pc["fully_inside_replaced"], pc["straddlers_split"]))
    print("  result    : %d triangles -> %s   (%.1f s)" % (rep["result_triangles"], out if not dry else "(not written: --dry-run)", rep["secs"]))
    seam = rep["open_edges_result"] - rep["open_edges_target"]
    print("  health    : open edges %d -> %d (seam adds %+d); non-manifold %d -> %d"
          % (rep["open_edges_target"], rep["open_edges_result"], seam, rep["nonmanifold_target"], rep["nonmanifold_result"]))
    if seam > 0:
        # Not a refusal
        print("  WARNING   : the seam left %d open edge(s) - the print pass closes a few; tens of them are a rim that did not\n"
              "              meet (a solid crossing the crop wall, a T-junction) - render the seam before the next piece" % seam)
    print("  identity  : %s" % rep["outside_identity"])
    if rep.get("degenerate_dropped") or rep.get("collinear_kept") or rep.get("edges_collapsed"):
        print("  weld      : %d zero-area facet(s) dropped, %d edge(s) under 1e-4 mm collapsed (their two vertices merged at the midpoint - nothing opens); %d collinear facet(s) kept (three distinct vertices on a line: a T-junction's business, said to printcheck)"
              % (rep.get("degenerate_dropped", 0), rep.get("edges_collapsed", 0), rep.get("collinear_kept", 0)))
    if rep.get("collapse_cap_hit"):
        print("  weld      : the short-edge collapse stopped at its cap of %d passes with edges under 1e-4 mm left - LOOK at the seam before the next piece" % COLLAPSE_PASSES)
    print("  Next      : LOOK - kit render %s --box <the crop box> ... every frame opened; the voxel route then runs its gates (kit mesh gate _nmnew / _shells --job <J> --tag <T> -- <crop.stl> <this file>) and, at the round's end, kit printfile / kit printcheck (PRINT_READINESS.md)" % out)
    return 0

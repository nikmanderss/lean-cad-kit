# recorded
# ONE CURVE in both faces
import numpy as np
import FreeCAD, Part

TOL = 0.02
GAP_MIN = 1e-4      # 31bq R7Wn3b

def V3(x): return FreeCAD.Vector(float(x[0]), float(x[1]), float(x[2]))
def P3(v): return np.array([v.x, v.y, v.z], float)
def ends(e):
    """the edge's start and end IN ITS OWN ORIENTATION (31bq R7Wn3b: reversed() changes an edge's Orientation and not the order of its Vertexes - the walk's flipped edges
    read their far end as the start, and a graze at a flipped edge's end was looked for at its start): the kernel's firstVertex / lastVertex with the orientation honoured"""
    try: return P3(e.firstVertex(True).Point), P3(e.lastVertex(True).Point)
    except Exception:
        a, b = P3(e.Vertexes[0].Point), P3(e.Vertexes[-1].Point)
        return (b, a) if str(getattr(e, "Orientation", "Forward")) == "Reversed" else (a, b)

def pts(e, step=0.05, nmin=12):
    """samples along the edge, first to last vertex (a degenerate edge: its two ends)"""
    if e.Length < 1e-6: a, b = ends(e); return np.array([a, b])
    n = max(nmin, int(e.Length / step) + 1); P = np.array([P3(q) for q in e.discretize(Number=n)])
    a, _ = ends(e)
    return P if np.linalg.norm(P[0] - a) <= np.linalg.norm(P[-1] - a) else P[::-1]

def reend(edge, old_pt, new_pt, step=0.2):
    """the edge re-fitted (cubic, C2, 1e-3) with the end nearest old_pt moved onto new_pt, the other end kept exactly (sk_vertex.refit_end's form)"""
    n = max(6, int(edge.Length / step) + 1); P = np.array([[q.x, q.y, q.z] for q in edge.discretize(Number=n)])
    cv = Part.BSplineCurve(); cv.approximate(Points=[V3(x) for x in P], DegMin=3, DegMax=3, Tolerance=1e-3, Continuity="C2")
    at_start = np.linalg.norm(P[0] - np.asarray(old_pt, float)) <= np.linalg.norm(P[-1] - np.asarray(old_pt, float))
    cv.setPole(1, V3(new_pt if at_start else P[0])); cv.setPole(cv.NbPoles, V3(P[-1] if at_start else new_pt)); return cv.toShape()

def order(edges):
    """the loop's edges in walking order, each oriented so its end meets the next's start - THE INPUT OBJECTS THEMSELVES (31bq R7Wn3: Part.Wire(...).OrderedEdges hands back
    COPIES of every edge but the first - new hashCodes, not isSame - so the record's keys never matched the caller's loop and no piece was handed across (qq_R7Wn's 8 free
    edges); Part.__sortEdges__ keeps the objects but DROPS an edge whose end lies beyond its own tolerance from the chain - the GAP case this pass exists for). A nearest-end
    walk from the first edge: every edge kept, reversed() where its far end is the nearer (the orientation changes; the identity under isSame does not)."""
    E = [e for e in edges if e is not None]
    if len(E) < 2: return list(E)
    left = list(range(1, len(E))); o = [E[0]]; prev_end = ends(E[0])[1]
    while left:
        best = None
        for k in left:
            a, b = ends(E[k]); da = float(np.linalg.norm(a - prev_end)); db = float(np.linalg.norm(b - prev_end))
            if best is None or min(da, db) < best[0]: best = (min(da, db), k, db < da)
        _, k, flip = best; e = E[k].reversed() if flip else E[k]
        o.append(e); prev_end = ends(e)[1]; left.remove(k)
    return o

def _orient(e, start):
    """e turned so its START (in its own orientation) is the nearer end to `start` - a new edge (reend's B-spline, a split's piece) runs the WALK's way (31bq R7Wn3c)"""
    a, b = ends(e)
    return e.reversed() if np.linalg.norm(a - np.asarray(start, float)) > np.linalg.norm(b - np.asarray(start, float)) else e
def _orient_end(e, end):
    """e turned so its END is the nearer end to `end` (31bq R7Wn3c)"""
    a, b = ends(e)
    return e.reversed() if np.linalg.norm(b - np.asarray(end, float)) > np.linalg.norm(a - np.asarray(end, float)) else e

def same_edge(a, b, tol=1e-3):
    """ONE edge: the same object (isSame), or the same curve held as a COPY - its length and its midpoint within tol (the sharing report's own test, sk_build 31bp)"""
    try:
        if a.isSame(b): return True
        if abs(a.Length - b.Length) > tol: return False
        return (a.valueAt(0.5 * (a.FirstParameter + a.LastParameter)) - b.valueAt(0.5 * (b.FirstParameter + b.LastParameter))).Length <= tol
    except Exception:
        return False

def _dist(e, p): return float(e.distToShape(Part.Vertex(V3(p)))[0])
def _foot(e, p):
    d, pp, _ = e.distToShape(Part.Vertex(V3(p))); return float(d), P3(pp[0][0])

def growth_law(dd, band):
    """A CORNER against a GRAZE by the GROWTH LAW of the distance from the shared vertex (dd: the distances of the in-band run's samples, the vertex's own left out):
    at a corner d grows LINEARLY - its median half its max, its first quarter a quarter of the max; a tangent run departs quadratically or later (the real v9
    graze: 0.0004 mm for 0.03 mm, 0.0012 at 0.05, 0.025 at 0.12 - the median a tenth of the max, the first quarter inside the coincidence band). A graze: the
    median <= 0.35 x the max AND the first quarter of the run inside the coincidence band (tol / 10). Returns (is_graze, median, max, first-quarter max).
    The band-median test alone missed the real case (the run's tail lifts the median); the band-run test alone flagged every 90 deg corner."""
    dd = np.asarray(dd, float)
    if len(dd) == 0: return False, 0.0, 0.0, 0.0
    q = max(1, len(dd) // 4); med = float(np.median(dd)); mx = float(dd.max()); q1 = float(dd[:q].max())
    return bool(med <= 0.35 * mx and q1 <= band), med, mx, q1

def graze_decide(L, d, A_len, tol):
    """the decision on sampled arrays (pure numpy - pinned by the kit's selftest): L the arc length from the vertex per sample, d the distance to the neighbour per sample;
    the in-band run from the vertex inward (every sample within tol), a run under tol, one reaching 90 % of A, or one that fails the growth law is no graze.
    Returns (k - the last sample of the run, run length, max deviation) or None"""
    L = np.asarray(L, float); d = np.asarray(d, float); band = tol / 10.0
    k = 0
    while k + 1 < len(d) and d[k + 1] <= tol: k += 1
    if k == 0 or L[k] < tol or L[k] >= 0.9 * A_len: return None
    ok, med, mx, q1 = growth_law(d[1:k + 1], band)
    if not ok: return None
    return k, float(L[k]), float(d[1:k + 1].max())

def _graze(A, B, from_end, tol, reach=1.0):
    """A's end stretch (from its END if from_end else its START) that COINCIDES with B - within the coincidence band tol / 10 (two curves closer than that are one curve at
    the kernel's scale) - over a run of at least tol: (run length, max deviation, the cut sample, its foot on B) or None. A corner is no graze however sharp: at a corner of
    angle theta the distance to B grows as s * sin(theta) from the vertex, so the band's run is tol / (10 sin theta) - under tol for any corner over 5.7 deg; a tangent run
    (sin theta -> 0) stays in the band until the curve peels away. Sampled every 0.005 mm over the first `reach` mm from the vertex; the decision is graze_decide's."""
    if A.Length < 1e-6 or B.Length < 1e-6: return None
    S = pts(A, step=0.005, nmin=48)
    if from_end: S = S[::-1]
    Lc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(S, axis=0), axis=1))]); m = int(np.searchsorted(Lc, reach)) + 1
    S = S[:max(3, min(m, len(S)))]; L = Lc[:len(S)]
    d = np.array([_dist(B, p) for p in S])
    got = graze_decide(L, d, float(A.Length), tol)
    if got is None: return None
    k, run, dev = got; _, F = _foot(B, S[k])
    return dict(run=run, dev=dev, cut=S[k], foot=F, k=k, n=len(S))

def find_slivers(edges, tol=TOL):
    """the three sliver kinds of one closed loop, with their numbers; nothing moved"""
    E = order(edges); n = len(E); out = []; seen_v = set(); seen_pair = set()
    for i, e in enumerate(E):
        a, b = ends(e); nb = E[(i + 1) % n]; na, _ = ends(nb)
        g = float(np.linalg.norm(na - b))
        if GAP_MIN < g <= tol: out.append(dict(kind="gap", i=i, j=(i + 1) % n, d=g))
        if e.Length < tol: out.append(dict(kind="short", i=i, len=float(e.Length)))
        for j, from_end in (((i + 1) % n, True), ((i - 1) % n, False)):
            if n < 3 or j == i: continue
            vk = tuple(np.round(b if from_end else a, 5))
            if vk in seen_v: continue
            gz = _graze(e, E[j], from_end, tol)
            if gz: seen_v.add(vk); out.append(dict(kind="graze", i=i, j=j, at="end" if from_end else "start", **{k_: v_ for k_, v_ in gz.items() if k_ in ("run", "dev")}))
        for j in range(n):
            if j in (i, (i + 1) % n, (i - 1) % n) or (min(i, j), max(i, j)) in seen_pair: continue
            P = pts(e, step=0.1, nmin=12); dd = np.array([_dist(E[j], p) for p in P[1:-1]])
            if len(dd) and dd.min() <= tol: seen_pair.add((min(i, j), max(i, j))); out.append(dict(kind="near", i=i, j=j, d=float(dd.min())))
    return out

def clean_loop(edges, tol=TOL, say=None, frozen=None):
    """returns (edges_out, moves, handoff, repl): GAPS closed, SHORT edges dropped, GRAZES cut back (A ended at its foot on B, B split at F; B's piece V..F in handoff
    for the face across A - handoff[k]["cut_edge"] is the cut edge A' that face holds too). Every move's deviation <= tol; a stretch that deviates more is no sliver
    and is left. The loop stays closed. repl maps every ORIGINAL edge's hashCode that changed to {"mine": [the edges in this loop], "others": [the edges every OTHER
    face that held it takes]} - the shared-edge rule: ONE CURVE in both faces (a cut B: mine [B2], others [B1, B2]; a dropped short edge: [] / []) - never 'one object':
    the kernel's Part.Wire hands every face a copy of every edge but the first and the sew pairs the copies (31bq R7Wn4, verify-wire-clean d). A SHORT / GAP move
    carries "vmoves" [[old point, new point], ...] - the vertices it moved, for the caller's vertex-wide merge (C2).
    frozen: hashCodes of edges never to touch (the body's own wall edges - the frame, L114): a move that would cut, split or re-end one is skipped and recorded
    (kind "frozen")."""
    E = order(edges); moves = []; handoff = []; repl = {}
    orig = {}      # ORIGINAL  31bq R7Wn3
    for e in E:
        oh = next((x.hashCode() for x in edges if x is not None and e.isSame(x)), e.hashCode()); orig[e.hashCode()] = oh; orig[oh] = oh
    frozen = set(frozen or [])
    def _fz(e): return orig.get(e.hashCode(), e.hashCode()) in frozen or e.hashCode() in frozen
    def _rep(old, new_mine, new_others=None):
        """old (a current object) -> new objects, recorded against old's ORIGINAL hash. 31bq R7Wn4 (C1): a chain of moves on one original edge COMPOSES - the earlier
        record's pieces are kept and `old` is replaced INSIDE them by the new pieces (the first form overwrote the record: on a hairpin's second graze the first cut's
        handed piece A1 vanished from 'others' and the face across came out open by 0.486 mm - verify-wire-clean C1 / C2); an earlier record that does not hold `old`
        takes the new pieces beside its own, said in the moves"""
        oh = orig.get(old.hashCode(), old.hashCode()); nm = list(new_mine); no = list(new_mine if new_others is None else new_others)
        if oh in repl:
            def _sub(lst, add):
                out = []; hit = False
                for x in lst:
                    if (not hit) and x.isSame(old): out.extend(add); hit = True
                    else: out.append(x)
                if not hit:
                    raise RuntimeError("wire-clean: a move on an edge its earlier record does not hold (a stale object) - refused, the loop stands as built (31bq R7Wn4b, D2)")
                return out
            repl[oh] = {"mine": _sub(repl[oh]["mine"], nm), "others": _sub(repl[oh]["others"], no)}
        else: repl[oh] = {"mine": nm, "others": no}
        for x in nm + no: orig[x.hashCode()] = oh
    # recorded
    keep = []
    for i, e in enumerate(E):
        if e.Length < tol and len(E) > 3:
            prev = keep[-1] if keep else (E[-1] if i == 0 else None); nxt = E[(i + 1) % len(E)]
            if _fz(e) or (prev is not None and _fz(prev)) or _fz(nxt):
                moves.append(dict(kind="frozen", what="short", i=i, len=float(e.Length))); keep.append(e); continue
            a, b = ends(e); m = 0.5 * (a + b)
            if prev is None or np.linalg.norm(ends(prev)[1] - a) > tol or np.linalg.norm(ends(nxt)[0] - b) > tol:
                moves.append(dict(kind="short-skipped", i=i, len=float(e.Length), why="its neighbours' ends are not its own ends (an edge out of its place in the loop)")); keep.append(e); continue
            moves.append(dict(kind="short", len=float(e.Length), at=m.tolist(), move=float(np.linalg.norm(a - m)), vmoves=[[q_.tolist(), m.tolist()] for q_ in (a, b) if np.linalg.norm(q_ - m) > 1e-9]))
            _rep(e, [], [])
            if keep: keep[-1] = _orient(reend(prev, ends(prev)[1], m), ends(prev)[0]); _rep(prev, [keep[-1]])
            else: E[-1] = _orient(reend(prev, ends(prev)[1], m), ends(prev)[0]); _rep(prev, [E[-1]])
            E[(i + 1) % len(E)] = _orient(reend(nxt, ends(nxt)[0], m), m); _rep(nxt, [E[(i + 1) % len(E)]])
            if (i + 1) % len(E) == 0:
                for _kk in range(len(keep)):
                    if keep[_kk].isSame(nxt): keep[_kk] = E[0]; break
            if say: say("   wire-clean: edge %d is %.4f mm long (under the construction tolerance) - dropped, its neighbours joined at its middle (their ends move %.4f mm)" % (i, e.Length, float(np.linalg.norm(a - m))))
            continue
        keep.append(e)
    E = keep; n = len(E)
    i = 0
    while i < n and n >= 3:
        A = E[i]; done = False
        for j, from_end in (((i + 1) % n, True), ((i - 1) % n, False)):
            if j == i: continue
            B = E[j]
            if same_edge(A, B):
                if not any(m_.get("kind") == "doubled" and m_.get("i") in (i, j) for m_ in moves):
                    moves.append(dict(kind="doubled", i=i, j=j))
                    if say: say("   wire-clean: edges %d / %d are one edge held twice (a slit) - not cleaned against itself" % (i, j))
                continue
            gz = _graze(A, B, from_end, tol)
            if not gz: continue
            if _fz(A) or _fz(B):
                moves.append(dict(kind="frozen", what="graze", i=i, j=j, run=gz["run"], dev=gz["dev"]))
                if say: say("   wire-clean: edge %d's %s runs %.3f mm along its neighbour %d within %.4f mm - NOT cut: %s is a FROZEN edge (the body's own wall edge, L114, or a ready face's border - 31bq R7Wn4b)" % (i, "end" if from_end else "start", gz["run"], j, gz["dev"], "the edge" if _fz(A) else "the neighbour"))
                continue
            V = ends(A)[1] if from_end else ends(A)[0]; F = gz["foot"]
            try:
                prm = A.Curve.parameter(V3(gz["cut"])); lo, hi = sorted((A.FirstParameter, A.LastParameter))
                if not (lo + 1e-9 < prm < hi - 1e-9): continue
                subs = [x for x in A.split([prm]).Edges if x.Length > 1e-6]
                keepA = max(subs, key=lambda s: min(np.linalg.norm(p - V) for p in ends(s)))
                A2 = reend(keepA, gz["cut"], F); A2 = _orient(A2, ends(A)[0]) if from_end else _orient(A2, F)
                pb = B.Curve.parameter(V3(F)); lob, hib = sorted((B.FirstParameter, B.LastParameter))
                if lob + 1e-9 < pb < hib - 1e-9:
                    bs = [x for x in B.split([pb]).Edges if x.Length > 1e-6]
                    B1 = min(bs, key=lambda s: min(np.linalg.norm(p - V) for p in ends(s))); B2 = [s for s in bs if s is not B1][0]
                    B2 = reend(B2, ends(B2)[0] if np.linalg.norm(ends(B2)[0] - F) <= np.linalg.norm(ends(B2)[1] - F) else ends(B2)[1], F)
                    B2 = _orient(B2, F) if from_end else _orient_end(B2, F)
                else: B1 = None; B2 = B
                _rep(A, [A2]); _rep(B, [B2], [B1, B2] if B1 is not None else [B2]); E[i] = A2; E[j] = B2
                if B1 is not None: handoff.append(dict(edge=B1, cut_edge=A2, cut_orig=orig.get(A2.hashCode()), split_orig=orig.get(B2.hashCode()), between=[V.tolist(), F.tolist()], across="the edge that was cut (its other face reaches V along this piece)"))
                moves.append(dict(kind="graze", i=i, j=j, at="end" if from_end else "start", run=gz["run"], dev=gz["dev"], V=V.tolist(), F=F.tolist(), move=float(np.linalg.norm(gz["cut"] - F))))
                if say: say("   wire-clean: edge %d's %s runs %.3f mm along its neighbour %d within %.4f mm (a sliver the mesher tears) - cut back to its foot on it (the vertex moves %.3f mm along the neighbour, the geometry %.4f)" % (i, "end" if from_end else "start", gz["run"], j, gz["dev"], float(np.linalg.norm(V - F)), gz["dev"]))
                done = True; break
            except Exception as ex:
                moves.append(dict(kind="graze-failed", i=i, j=j, why=str(ex)[:80]))
        i += 1
    # recorded
    for i in range(n):
        a, b = ends(E[i]); nxt = E[(i + 1) % n]; na, nb_ = ends(nxt); g = float(np.linalg.norm(na - b))
        if GAP_MIN < g <= tol:
            if not _fz(nxt):
                new = _orient(reend(nxt, na, b), b); _rep(nxt, [new]); E[(i + 1) % n] = new; vm_ = [[na.tolist(), b.tolist()]]
            elif not _fz(E[i]):
                new = _orient(reend(E[i], b, na), a); _rep(E[i], [new]); E[i] = new; vm_ = [[b.tolist(), na.tolist()]]
            else:
                moves.append(dict(kind="frozen", what="gap", i=i, j=(i + 1) % n, d=g)); continue
            moves.append(dict(kind="gap", i=i, j=(i + 1) % n, move=g, vmoves=vm_))
            if say: say("   wire-clean: edges %d / %d met %.4f mm apart - joined" % (i, (i + 1) % n, g))
    return E, moves, handoff, repl

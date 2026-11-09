# kit rebuild
# over the
# _ccrefine.py
import os, sys, numpy as np, vtk
from vtk.util import numpy_support as nps
from scipy.spatial import cKDTree
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "mesh")); sys.path.insert(0, os.path.dirname(_HERE))


def _say0(*a): print(*a, flush=True)


def _pd(V, T):
    pts = vtk.vtkPoints(); pts.SetData(nps.numpy_to_vtk(np.ascontiguousarray(V, np.float64), deep=True))
    cells = vtk.vtkCellArray(); conn = np.empty((len(T), 4), np.int64); conn[:, 0] = 3; conn[:, 1:] = T
    cells.SetCells(len(T), nps.numpy_to_vtkIdTypeArray(conn.ravel(), deep=True))
    pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(cells); return pd


def _np(pd):
    V = nps.vtk_to_numpy(pd.GetPoints().GetData()).astype(float)
    if pd.GetNumberOfCells() == 0: return V, np.zeros((0, 3), int)
    T = nps.vtk_to_numpy(pd.GetPolys().GetData()).reshape(-1, 4)[:, 1:].astype(int)
    return V, T


def _weld(V, T, tol=1e-6):
    key = np.round(np.asarray(V, float) / tol).astype(np.int64)
    _, ui, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1)
    V = np.asarray(V, float)[ui]; T = inv[np.asarray(T, int)]
    T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
    return V, T


def health(V, T):
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); s = np.sort(e, 1)
    _, c = np.unique(s, axis=0, return_counts=True)
    return int((c == 1).sum()), int((c > 2).sum())


def extend_caps(V, T, walls, shift_mm):
    """the triangles lying on each wall plane are moved shift_mm outward along the wall's normal and a band of side
    triangles closes the gap (rb_blend's extrusion, with CLIP_OUT instead of E): the piece's caps lie CLIP_OUT past the
    walls so the reinsert's cut is transversal (L81), and so must the kept base's"""
    V2 = V.copy(); T2 = [T]; keep = np.ones(len(T), bool)
    for c, n, on in walls:
        if not on.any(): continue
        Tw = T[on]
        e = np.vstack([Tw[:, [0, 1]], Tw[:, [1, 2]], Tw[:, [2, 0]]]); es = np.sort(e, axis=1)
        _, idx, cnt = np.unique(es, axis=0, return_index=True, return_counts=True); be = e[idx[cnt == 1]]
        wv = np.unique(Tw); newid = {int(v): len(V2) + k for k, v in enumerate(wv)}
        V2 = np.vstack([V2, V[wv] + n * shift_mm])
        cap = np.vectorize(lambda v: newid[int(v)])(Tw)
        side = np.array([[a, b, newid[int(b)]] for a, b in be] + [[a, newid[int(b)], newid[int(a)]] for a, b in be])
        T2.append(cap); T2.append(side); keep &= ~on
    T2[0] = T[keep]
    return V2, np.vstack(T2)


def core_points(Fw, F0, xs, ys, zs, h, vmin=1.0, say=_say0):
    """grid nodes where the piece's field and the base's field disagree in sign, within 2h of either surface - the
    places the closing added or the opening removed; the core is these points grown by the margin. A changed component
    under vmin mm3 is NOT a core (measured 2026-10-01: a single flipped node - a 0.008 mm3 fill in a crevice of the hat's
    top - made a 1.5 mm ball whose wall met the flat surface tangentially; the piece's finer mesh resolved a separate
    1.2 mm rim there and the base's did not, and the join refused on an unpaired loop; below print tolerance such a change
    is nothing, and the base stays exact there)"""
    from scipy import ndimage
    changed = (Fw >= 0) != (F0 >= 0)
    lab, nlab = ndimage.label(changed)
    if nlab:
        vols = ndimage.sum(changed, lab, range(1, nlab + 1)) * h ** 3
        keep_ids = np.nonzero(vols >= vmin)[0] + 1
        say("  core components: %d changed, %d of them >= %.2f mm3 kept as cores (%.1f of %.1f mm3)" % (nlab, len(keep_ids), vmin, float(vols[keep_ids - 1].sum()) if len(keep_ids) else 0.0, float(vols.sum())))
        changed &= np.isin(lab, keep_ids)
    near = (np.abs(F0) <= 2 * h) | (np.abs(Fw) <= 2 * h)
    idx = np.argwhere(changed & near)
    return np.stack([xs[idx[:, 0]], ys[idx[:, 1]], zs[idx[:, 2]]], axis=1).astype(np.float32)


def base_self_intersections(V, T, say=_say0):
    """the base's OWN self-intersecting facet pairs (FreeCAD's check) - the sloppy original's laminations and crossing
    sheets. Measured 2026-10-01 on a section's content: 17 pairs where a 1.9 mm2 facet of the x- slot pocket is pierced by
    the pocket's own small facets. Kept exactly, that junk came back into the piece and no repair closed it (k10/k11: 6
    pairs left, the brep would be BOP-invalid). The marching-cubes level set of the same place is the clean union - so
    every such spot becomes a CORE (its points are added to E) and the resample is used there. Returns the pair centroids."""
    try:
        import Mesh
    except Exception as e:
        say("  (FreeCAD Mesh not importable: the base's self-intersections were not checked - %s)" % e); return np.zeros((0, 3), np.float32)
    m = Mesh.Mesh([tuple(map(float, V[i])) for t in T for i in t])
    si = m.getSelfIntersections()
    if not si: return np.zeros((0, 3), np.float32)
    C = []
    for t_ in si:
        for k in (int(t_[0]), int(t_[1])):
            C.append(np.mean([list(p_) for p_ in m.Facets[k].Points], axis=0))
    C = np.asarray(C, np.float32); nsi = len(si); del m, si
    say("  base self-intersections: %d facet pair(s) - %d core point(s) added there (the original's own junk is re-expressed, not kept)" % (nsi, len(C)))
    return C


def junk_cores(V, T, F0, xs, ys, zs, h, open_mm=0.0, lam_dist=0.5, lam_deg=5.0, say=_say0):
    """THE MATERIAL DECISION AT THE MESH LEVEL, for a base that is the content's own tessellation (the arrangement did not
    run): every triangle of the base that is JUNK is marked, and its centroid becomes a core point, so the resample is used
    there and the base is kept exactly only where it is clean. Measured 2026-10-01 on a section's content (31k triangles):
    1,531 triangles INTERNAL (inside the material by more than h/2 - the vanes' shells running through the spine, depth up
    to 3.8 mm; kept exactly they are inner sheets in a solid), 1,180 OUTSIDE the material (flaps and shards in air), and
    laminations - near-duplicate parallel sheets 0.1 mm apart on the slot pocket's wall - that every repair turned into
    self-intersections. Classes: internal (F0 > h/2 at the centroid), outside (F0 < -h/2), lamination (another triangle
    within lam_dist along the normal, facing the same way within lam_deg, overlapping in plan), thin (the material behind
    the triangle is thinner than 2 x open_mm + h: the opening removes it, so it is a core)."""
    V = np.asarray(V, float); T = np.asarray(T, int)
    C = V[T].mean(1); n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]); A = 0.5 * np.linalg.norm(n, axis=1); n /= (2 * A[:, None] + 1e-30)
    def f0(P):
        i = np.clip(np.round((P[:, 0] - xs[0]) / h).astype(int), 0, len(xs) - 1); j = np.clip(np.round((P[:, 1] - ys[0]) / h).astype(int), 0, len(ys) - 1)
        k = np.clip(np.round((P[:, 2] - zs[0]) / h).astype(int), 0, len(zs) - 1); return F0[i, j, k]
    f = f0(C)
    internal = f > 0.5 * h; outside = f < -0.5 * h
    thin = np.zeros(len(T), bool)
    if open_mm > 0:
        for t_ in np.arange(0.3, 2.0 * open_mm + h + 1e-6, 0.3):
            thin |= f0(C - n * t_) < 0
    # INTERNAL
    lam = np.zeros(len(T), bool)
    junk = internal | outside | lam | thin
    rep = {"triangles": int(len(T)), "internal": int(internal.sum()), "internal_area_mm2": round(float(A[internal].sum()), 1),
           "outside": int(outside.sum()), "outside_area_mm2": round(float(A[outside].sum()), 1), "lamination": int(lam.sum()),
           "thin": int(thin.sum()), "junk_total": int(junk.sum()), "junk_area_mm2": round(float(A[junk].sum()), 1)}
    say("  base junk -> cores: %d internal (%.0f mm2), %d outside (%.0f mm2), %d laminated, %d thin; %d of %d triangles (%.0f mm2) re-expressed, the rest kept exactly"
        % (rep["internal"], rep["internal_area_mm2"], rep["outside"], rep["outside_area_mm2"], rep["lamination"], rep["thin"], rep["junk_total"], len(T), rep["junk_area_mm2"]))
    return C[junk].astype(np.float32), rep


def refine_at_wall(V, T, fcore, L, say=_say0):
    """the mesh route's longest-edge bisection (kit\\mesh\\_ccrefine.py): every edge that crosses the core wall is split
    until it is shorter than L, each new vertex the midpoint of an existing edge (the surface is bit-for-bit the same
    shape), both triangles on an edge always splitting it together (no T-junction). vtkClipPolyData places its cut by
    LINEAR interpolation along each edge, which on a long edge is millimetres wrong - the base's planar faces have edges
    of 10-20 mm; the marching-cubes piece's are h."""
    Fc = None; nsplit = 0
    for it in range(60):
        E = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], 0); Es = np.sort(E, 1)
        U, inv = np.unique(Es, axis=0, return_inverse=True); inv = inv.ravel()
        nT = len(T); TE = inv.reshape(3, nT).T
        if Fc is None: Fc = fcore(V)
        elif len(Fc) < len(V): Fc = np.concatenate([Fc, fcore(V[len(Fc):])])
        F = Fc
        cross = (F[U[:, 0]] * F[U[:, 1]]) < 0
        ln = np.linalg.norm(V[U[:, 0]] - V[U[:, 1]], axis=1)
        mark = cross & (ln > L)
        tl = ln[TE]; LE = np.argmax(tl, axis=1); LEid = TE[np.arange(nT), LE]
        near_t = (np.abs(F[T]).min(1) < tl.max(1)) & (tl.max(1) > L)
        mark[LEid[near_t]] = True
        if not mark.any(): break
        while True:
            has = mark[TE].any(1); add = has & ~mark[LEid]
            if not add.any(): break
            mark[LEid[add]] = True
        mid = -np.ones(len(U), np.int64); mid[mark] = len(V) + np.arange(mark.sum())
        V = np.vstack([V, 0.5 * (V[U[mark, 0]] + V[U[mark, 1]])]); nsplit += int(mark.sum())
        Mi = mid[TE]; has = (Mi >= 0).any(1); out = [T[~has]]
        for k in range(3):
            s_ = has & (LE == k)
            if not s_.any(): continue
            q0, q1, q2 = T[s_, k], T[s_, (k + 1) % 3], T[s_, (k + 2) % 3]
            m0, m1, m2 = Mi[s_, k], Mi[s_, (k + 1) % 3], Mi[s_, (k + 2) % 3]
            a1 = m1 >= 0; a2 = m2 >= 0
            out += [np.stack([q0[~a2], m0[~a2], q2[~a2]], 1),
                    np.stack([q0[a2], m0[a2], m2[a2]], 1), np.stack([m0[a2], q2[a2], m2[a2]], 1),
                    np.stack([m0[~a1], q1[~a1], q2[~a1]], 1),
                    np.stack([m0[a1], q1[a1], m1[a1]], 1), np.stack([m0[a1], m1[a1], q2[a1]], 1)]
        T = np.concatenate(out, 0)
    return V, T, nsplit, it + 1


def remove_tiny_islands(V, T, f, keep_sign, max_extent=1.0):
    """islands of the OTHER sign smaller than max_extent (mm) are given this side's sign before the clip, so the clip never
    cuts a sub-millimetre hole or speck: a core wall nearly tangent to a surface makes them, and they have no partner on the
    other side (R4 run 4, 2026-10-01: a 0.4 mm island of f > 0 on the piece became a 4-edge unpaired loop; capped or
    collapsed it left one non-manifold seam edge and the repair ended solid False). keep_sign=-1: islands of f > 0 inside
    the piece's f < 0 region are flipped negative; keep_sign=+1: the body's f < 0 specks are flipped positive."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    other = (f > 0) if keep_sign < 0 else (f < 0)
    if not other.any(): return f, 0
    E = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    E = E[other[E[:, 0]] & other[E[:, 1]]]
    n = len(V)
    g = coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(n, n))
    ncomp, lab = connected_components(g, directed=False)
    lab = np.where(other, lab, -1)
    f = f.copy(); flipped = 0
    for c in np.unique(lab[lab >= 0]):
        idx = np.nonzero(lab == c)[0]
        ext = float(np.ptp(V[idx], 0).max()) if len(idx) > 1 else 0.0
        if ext < max_extent:
            f[idx] = -1e-3 if keep_sign < 0 else 1e-3; flipped += 1
    return f, flipped


def clip_by_core(V, T, fvals, inside):
    """vtkClipPolyData on point scalars = the core function at the vertices: inside keeps f < 0 (the core), else f > 0"""
    pd = _pd(V, T)
    arr = nps.numpy_to_vtk(np.ascontiguousarray(fvals, np.float64), deep=True); arr.SetName("core"); pd.GetPointData().SetScalars(arr)
    c = vtk.vtkClipPolyData(); c.SetInputData(pd); c.SetValue(0.0); c.SetInsideOut(1 if inside else 0)
    c.SetOutputPointsPrecision(vtk.vtkAlgorithm.DOUBLE_PRECISION); c.Update()
    tf = vtk.vtkTriangleFilter(); tf.SetInputData(c.GetOutput()); tf.PassLinesOff(); tf.PassVertsOff(); tf.Update()
    V2, T2 = _np(tf.GetOutput())
    return _weld(V2, T2, 1e-9)


def components_reaching_rim(V, T):
    """of the clipped piece, keep every component that has boundary edges (it reaches the core wall and pairs with a
    body loop there); a CLOSED floating fragment is a stray and is dropped and counted (the mesh route's rule)"""
    pd = _pd(V, T)
    cn = vtk.vtkPolyDataConnectivityFilter(); cn.SetInputData(pd); cn.SetExtractionModeToAllRegions(); cn.ColorRegionsOn(); cn.Update()
    ncomp = cn.GetNumberOfExtractedRegions()
    if ncomp <= 1: return V, T, int(ncomp), 0, 0
    co = cn.GetOutput()
    rid = nps.vtk_to_numpy(co.GetPointData().GetArray("RegionId")).astype(int)
    Vc, Tc = _np(co)
    e = np.vstack([Tc[:, [0, 1]], Tc[:, [1, 2]], Tc[:, [2, 0]]]); s_ = np.sort(e, 1)
    u, c = np.unique(s_, axis=0, return_counts=True)
    rim_regions = set(rid[np.unique(u[c == 1])].tolist())
    keep_t = np.isin(rid[Tc[:, 0]], list(rim_regions))
    dropped = ncomp - len(rim_regions)
    return Vc, Tc[keep_t], int(ncomp), int(dropped), int((~keep_t).sum())


def pinch_merge(V, T, pinch=0.05, rounds=3):
    """rb_repair's PINCH merge (L92), applied to the marching-cubes piece BEFORE the join: a micro-slit of open edges plus
    one non-manifold edge under `pinch` mm (the polish folding a vertex beside a held band) is merged at its endpoints.
    R4 run 4 (2026-10-01): such a slit inside a core became a 4-edge unpaired patch loop, the join capped it with a fan
    that left a non-manifold edge, and the repair could not close the hole it then cut - the piece stayed solid False.
    Returns V, T, (health before, health after, edges merged)."""
    h0 = health(V, T); merged = 0
    for _ in range(rounds):
        hb = health(V, T)
        if hb == (0, 0): break
        e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); es = np.sort(e, axis=1)
        u_, cnt_ = np.unique(es, axis=0, return_counts=True)
        bad = u_[cnt_ != 2]; L_ = np.linalg.norm(V[bad[:, 0]] - V[bad[:, 1]], axis=1)
        short = bad[L_ < pinch]
        if len(short) == 0: break
        mapping = np.arange(len(V)); Vk, Tk = V.copy(), T.copy()
        for a, b in short:
            a, b = int(mapping[a]), int(mapping[b])
            if a == b: continue
            mid = 0.5 * (V[a] + V[b]); V[a] = mid; V[b] = mid; mapping[b] = a
        while True:
            m2 = mapping[mapping]
            if np.array_equal(m2, mapping): break
            mapping = m2
        T = mapping[T]; V, T = _weld(V, T, 1e-9)
        ha = health(V, T)
        if sum(ha) >= sum(hb): V, T = Vk, Tk; break
        merged += int(len(short))
    return V, T, (h0, health(V, T), merged)


def _directed_loops(T):
    """the boundary of an oriented triangle mesh as directed cycles (a -> b as the triangle traverses it); a pinched rim
    (two cycles touching at a vertex) is walked as ONE Euler circuit (the mesh route's _loops stops at such a vertex)"""
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); s_ = np.sort(e, 1)
    u, inv, c = np.unique(s_, axis=0, return_inverse=True, return_counts=True); inv = inv.ravel()
    bnd = e[c[inv] == 1]
    out = {}
    for a, b in bnd: out.setdefault(int(a), []).append(int(b))
    loops = []
    for start in list(out):
        if not out.get(start): continue
        stack = [start]; circuit = []
        while stack:
            v = stack[-1]
            if out.get(v): stack.append(out[v].pop())
            else: circuit.append(stack.pop())
        circuit = circuit[::-1]
        if len(circuit) > 3: loops.append(circuit[:-1])
    return loops


def zipper_join(VA, TA, VB, TB, tol=0.5, say=_say0):
    """THE JOIN OF THE BURRITO'S KEEP-AND-WELD (2026-10-01): the body's rim (A, exact) and the piece's rim (B, marching
    cubes) are connected by a STRIP of triangles - the mesh route's zipper (kit/mesh/_ccweld.py: 'walks both loops and
    advances whichever side has the shorter next edge; no matching vertex counts, no snapping heuristic, no tolerance').
    No vertex moves and nothing is inserted, so the result is manifold by construction wherever the two rims are simple
    closed curves; A's rim stays bit-exact. Why not the point-merge (_ccseam.seam_merge): on a section its mutual
    insertion left micro-holes at a sharp-edge crossing whose closing made a folded flap - one non-manifold edge that no
    local repair cleared (R4 run 4, then k8/k9). The zipper was retired in the mesh route for a 23:1 point-density fan;
    here the rims are 0.3 and 0.2 mm apart in spacing. Returns V, T, report (V None when refused)."""
    rep = {}
    LA = _directed_loops(TA); LB = _directed_loops(TB)
    rep["loopsA"] = len(LA); rep["loopsB"] = len(LB)
    if not LA or not LB:
        rep["error"] = "no rim on one side (body %d loops, piece %d)" % (len(LA), len(LB)); return None, None, rep
    # collapsed
    # collapsed
    # collapsed
    TINY_B = float(os.environ.get("KEEP_TINY_B", "1.0")); TINY_A = float(os.environ.get("KEEP_TINY_A", "0.5"))
    def _collapse(Vx, Tx, loops):
        col = np.arange(len(Vx)); Vx = Vx.copy()
        for l in loops:
            l = np.asarray(l, int); Vx[l[0]] = Vx[l].mean(0); col[l[1:]] = l[0]
        Tx = col[Tx]; Tx = Tx[(Tx[:, 0] != Tx[:, 1]) & (Tx[:, 1] != Tx[:, 2]) & (Tx[:, 0] != Tx[:, 2])]
        return _weld(Vx, Tx, 1e-9)
    def _pair(LA, LB):
        tA = [cKDTree(VA[l]) for l in LA]; tB = [cKDTree(VB[l]) for l in LB]
        costAB = np.array([[np.percentile(tB[j].query(VA[la])[0], 90) for j in range(len(LB))] for la in LA]).reshape(len(LA), len(LB))
        costBA = np.array([[np.percentile(tA[i].query(VB[lb])[0], 90) for i in range(len(LA))] for lb in LB]).reshape(len(LB), len(LA))
        pairs = []
        for i in range(len(LA)):
            if len(LB) == 0: break
            j = int(np.argmin(costAB[i]))
            if int(np.argmin(costBA[j])) == i and max(costAB[i, j], costBA[j, i]) <= 3 * tol: pairs.append((i, j))
        return pairs
    for _round in range(2):
        pairs = _pair(LA, LB); uA = {i for i, _ in pairs}; uB = {j for _, j in pairs}
        tinyB = [LB[j] for j in range(len(LB)) if j not in uB and float(np.ptp(VB[LB[j]], 0).max()) < TINY_B]
        tinyA = [LA[i] for i in range(len(LA)) if i not in uA and float(np.ptp(VA[LA[i]], 0).max()) < TINY_A]
        if not tinyA and not tinyB: break
        if tinyB:
            VB, TB = _collapse(VB, TB, tinyB); LB = _directed_loops(TB)
            rep.setdefault("piece_tiny_loops_collapsed", []).extend(len(l) for l in tinyB)
            say("  piece rim: %d unpaired loop(s) under %.2f mm collapsed (grid artefacts): %s points" % (len(tinyB), TINY_B, [len(l) for l in tinyB]))
        if tinyA:
            VA, TA = _collapse(VA, TA, tinyA); LA = _directed_loops(TA)
            rep.setdefault("body_tiny_loops_collapsed", []).extend(len(l) for l in tinyA)
            say("  body rim: %d unpaired loop(s) under %.2f mm collapsed (specks of the base's mesh): %s points" % (len(tinyA), TINY_A, [len(l) for l in tinyA]))
    pairs = _pair(LA, LB)
    uA = {i for i, _ in pairs}; uB = {j for _, j in pairs}
    orphB = [(len(LB[j]), [round(float(v), 2) for v in VB[LB[j]].mean(0)], round(float(np.ptp(VB[LB[j]], 0).max()), 2)) for j in range(len(LB)) if j not in uB]
    orphA = [(len(LA[i]), [round(float(v), 2) for v in VA[LA[i]].mean(0)], round(float(np.ptp(VA[LA[i]], 0).max()), 2)) for i in range(len(LA)) if i not in uA]
    rep["loops_paired"] = len(pairs); rep["piece_loops_unpaired"] = orphB; rep["body_loops_unpaired"] = orphA
    if orphB or orphA:
        rep["error"] = ("unpaired rim loop(s) - piece %s, body %s: the core wall crosses a feature one mesh carries and the other does not "
                        "(a thin slit, a pinched fillet foot, a tangent wall); move the wall (KEEP_M) or the fade (FADE_IN)" % (orphB, orphA))
        return None, None, rep
    nA = len(VA); V = np.vstack([VA, VB]); strips = []; gaps = []
    for i, j in pairs:
        la = list(LA[i]); lb = [v + nA for v in LB[j]][::-1]
        d0 = np.linalg.norm(V[lb] - V[la[0]], axis=1); k0 = int(np.argmin(d0)); lb = lb[k0:] + lb[:k0]
        na, nb = len(la), len(lb); ia = ib = 0; out = []
        PA_ = V[la + la[:1]]; PB_ = V[lb + lb[:1]]
        cA = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(PA_, axis=0), axis=1))]); cA /= max(cA[-1], 1e-9)
        cB = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(PB_, axis=0), axis=1))]); cB /= max(cB[-1], 1e-9)
        while ia < na or ib < nb:
            a0, a1 = la[ia % na], la[(ia + 1) % na]; b0, b1 = lb[ib % nb], lb[(ib + 1) % nb]
            dA = np.linalg.norm(V[a1] - V[b0]); dB = np.linalg.norm(V[b1] - V[a0])
            SYNC = 0.01
            if ib >= nb: step_a = True
            elif ia >= na: step_a = False
            elif cA[ia] - cB[ib] > SYNC: step_a = False
            elif cB[ib] - cA[ia] > SYNC: step_a = True
            else: step_a = dA <= dB
            if step_a: out.append([a1, a0, b0]); gaps.append(dA); ia += 1
            else: out.append([b0, b1, a0]); gaps.append(dB); ib += 1
        strips.append(np.asarray(out, int))
    T = np.vstack([TA, TB + nA] + strips)
    T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
    V, T = _weld(V, T, 1e-9)
    gaps = np.asarray(gaps)
    rep["seam_xyz"] = np.vstack([VA[np.asarray(LA[i], int)] for i, _ in pairs]) if pairs else np.zeros((0, 3))
    rep["strip_triangles"] = int(sum(len(s_) for s_ in strips)); rep["seam_gap_p50"] = round(float(np.percentile(gaps, 50)), 4)
    rep["seam_gap_p99"] = round(float(np.percentile(gaps, 99)), 4); rep["seam_gap_max"] = round(float(gaps.max()), 4)
    h = health(V, T); rep["open_out"], rep["nonmanifold_out"] = h
    try:
        _k = int(np.argmax(gaps)); _ts = np.vstack(strips)[_k]; rep["seam_gap_max_at"] = [round(float(v), 2) for v in V[_ts].mean(0)]   # recorded
    except Exception: pass
    if gaps.max() > 2.0 * tol:
        rep["error"] = "a strip edge spans %.3f mm (> 2 x KEEP_TOL %.2f) at %s: the rims are apart there - a sharp edge the grid rounds, or a wall through a feature" % (gaps.max(), tol, rep.get("seam_gap_max_at"))
        return None, None, rep
    if h != (0, 0):
        rep["error"] = "the zipper left the mesh open/non-manifold %s (the inputs were closed): a rim that crosses itself" % (h,)
        return None, None, rep
    return V, T, rep


def snap_rim(VP, TP, VB, TB, rim_snap, h, say=_say0, relax_rings=3, relax_iter=3):
    """31ad - THE RIM SNAP (the mesh route's CC_SNAP, 0.25 proven: the extract walks every patch vertex within SNAP of a kept
    surface onto it - a sub-cell Newton move). Here the marching-cubes piece's RIM vertices (its boundary at the core wall) are
    moved onto the base's surface when they lie within rim_snap of it, a move that would fold a triangle refused; then the
    rings next to the rim are relaxed by a few windowed-sinc passes with the rim and the rest held, so the moved rim does not
    leave skinny folds behind it. Why: the MC rim is rounded 0.36-1.09 mm off the base where the core wall crosses a sharp
    edge (R4 runs 7-11, every strip-edge refusal and 96 of 105 of the repair's crossings sat there); the zipper then BRIDGED
    that gap with a strip that folds through its neighbours. With the rims on one surface the strip is short or absent and
    the join tolerance can come down toward the mesh route's 0.15. Returns V, report."""
    rep = {"rim_snap_mm": float(rim_snap)}
    if rim_snap <= 0: return VP, rep
    e = np.vstack([TP[:, [0, 1]], TP[:, [1, 2]], TP[:, [2, 0]]]); s_ = np.sort(e, 1); u, c = np.unique(s_, axis=0, return_counts=True)
    rim = np.unique(u[c == 1]); rep["rim_vertices"] = int(len(rim))
    if len(rim) == 0: return VP, rep
    ipd = vtk.vtkImplicitPolyDataDistance(); ipd.SetInput(_pd(VB, TB))
    V = np.asarray(VP, float).copy(); cp = [0.0, 0.0, 0.0]
    order = np.argsort(TP.ravel()); vidx = TP.ravel()[order]; tidx = np.repeat(np.arange(len(TP)), 3)[order]; starts = np.searchsorted(vidx, np.arange(len(V) + 1))
    moved = refused = far = 0; mv = []
    for i in rim:
        d = ipd.EvaluateFunctionAndGetClosestPoint(V[i], cp)
        if abs(d) > rim_snap: far += 1; continue
        q = np.array(cp); tl = tidx[starts[i]:starts[i + 1]]
        P0 = V[TP[tl]]; n0 = np.cross(P0[:, 1] - P0[:, 0], P0[:, 2] - P0[:, 0]); old = V[i].copy(); V[i] = q
        P1 = V[TP[tl]]; n1 = np.cross(P1[:, 1] - P1[:, 0], P1[:, 2] - P1[:, 0])
        if np.any(np.einsum("ij,ij->i", n0, n1) <= 0.0) or np.any(np.linalg.norm(n1, axis=1) < 0.05 * np.maximum(np.linalg.norm(n0, axis=1), 1e-12)):
            V[i] = old; refused += 1
        else: moved += 1; mv.append(abs(d))
    rep.update(rim_moved=int(moved), rim_refused_fold=int(refused), rim_beyond=int(far), rim_move_p50=round(float(np.median(mv)), 4) if mv else 0.0, rim_move_max=round(float(max(mv)), 4) if mv else 0.0)
    say("  rim snap %.2f: %d of %d rim vertices moved onto the base (p50 %.3f, max %.3f mm); %d refused (a triangle would fold), %d beyond the reach" % (rim_snap, moved, len(rim), rep["rim_move_p50"], rep["rim_move_max"], refused, far))
    if moved and relax_rings > 0 and relax_iter > 0:
        adj_a = np.concatenate([u[:, 0], u[:, 1]]); adj_b = np.concatenate([u[:, 1], u[:, 0]])
        ring = np.zeros(len(V), bool); ring[rim] = True; frontier = rim
        for _ in range(relax_rings):
            nb = adj_b[np.isin(adj_a, frontier)]; nb = nb[~ring[nb]]; ring[nb] = True; frontier = np.unique(nb)
        relax = ring.copy(); relax[rim] = False
        sm = vtk.vtkWindowedSincPolyDataFilter(); sm.SetInputData(_pd(V, TP)); sm.SetNumberOfIterations(relax_iter); sm.SetPassBand(0.1)
        sm.BoundarySmoothingOff(); sm.FeatureEdgeSmoothingOff(); sm.NonManifoldSmoothingOff(); sm.NormalizeCoordinatesOn(); sm.Update()
        V4 = nps.vtk_to_numpy(sm.GetOutput().GetPoints().GetData()).astype(float); V4[~relax] = V[~relax]
        d_ = np.linalg.norm(V4 - V, axis=1); V = V4
        rep.update(relax_vertices=int(relax.sum()), relax_move_max=round(float(d_.max()), 4))
        say("  rim relax: %d vertices in %d ring(s) next to the rim, %d sinc passes, max move %.3f mm" % (int(relax.sum()), relax_rings, relax_iter, float(d_.max())))
    return V, rep


def _jsonable(x):
    if isinstance(x, dict): return {str(k): _jsonable(v) for k, v in x.items() if not str(k).startswith("_")}
    if isinstance(x, (list, tuple)): return [_jsonable(v) for v in x]
    if isinstance(x, np.ndarray): return _jsonable(x.tolist()) if x.size <= 64 else "<array %s>" % (x.shape,)
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.floating,)): return float(x)
    if isinstance(x, (np.bool_,)): return bool(x)
    return x


def keep_and_weld(VB, TB, VP, TP, E, M, walls, clip_out, say=_say0, tol=0.3, refine_l=0.3, dump_dir=None, nm_ok=0, pinch=0.05, join="zipper", E_extra=None, rim_snap=0.0, h=0.2, open_ok=0, micro="best"):
    """dump_dir: where the two clipped halves (keep_base_outside.stl, keep_piece_inside.stl) and the core points are
    written on a refusal, so a refused seam can be looked at instead of guessed about (CONTRACT rule 0)"""
    import _ccseam as CS
    import kitlib_render as KR
    def _dump(VA_, TA_, VP_, TP_):
        if not dump_dir: return
        try:
            KR.write_stl(os.path.join(dump_dir, "keep_base_outside.stl"), VA_, TA_)
            KR.write_stl(os.path.join(dump_dir, "keep_piece_inside.stl"), VP_, TP_)
            np.savez(os.path.join(dump_dir, "keep_core.npz"), E=E, M=np.float32(M))
            say("  (refused: the two clipped halves and the core written beside the output: keep_base_outside.stl, keep_piece_inside.stl, keep_core.npz)")
        except Exception as e_: say("  (could not write the refusal dump: %s)" % e_)
    rep = {}
    Esi = np.asarray(E_extra, np.float32).reshape(-1, 3) if E_extra is not None else base_self_intersections(np.asarray(VB, float), np.asarray(TB, int), say)
    rep["base_self_intersection_points"] = int(len(Esi))
    if len(Esi): E = np.vstack([np.asarray(E, np.float32).reshape(-1, 3), Esi])
    rep.update(core_points=int(len(E)), margin_mm=float(M), tol_mm=float(tol))
    VP, TP, (hp0, hp1, npinch) = pinch_merge(np.asarray(VP, float).copy(), np.asarray(TP, int).copy(), pinch)
    rep["piece_pinch_merge"] = {"health_before": list(hp0), "health_after": list(hp1), "edges_merged": int(npinch)}
    if npinch or hp0 != (0, 0):
        say("  piece pinch merge (%.3f mm): health %s -> %s, %d edge(s) merged" % (pinch, hp0, hp1, npinch))
    if len(E) == 0:
        rep["error"] = "no core: the field never changed sign near the surface (nothing was closed or opened)"
        return None, None, rep
    kd = cKDTree(E)
    fcore = lambda P: kd.query(np.asarray(P, float), workers=-1)[0] - M
    VBx, TBx = extend_caps(VB, TB, walls, clip_out)
    VBx, TBx = _weld(VBx, TBx, 1e-9)
    hb0 = health(VBx, TBx); rep["base_in"] = {"triangles": int(len(TBx)), "open_nonmanifold": list(hb0)}
    VBr, TBr, nsplit, passes = refine_at_wall(VBx, TBx, fcore, refine_l, say)
    rep["refine"] = {"edges_split": int(nsplit), "passes": int(passes), "triangles": int(len(TBr)), "open_nonmanifold": list(health(VBr, TBr))}
    say("keep-and-weld: core %d points, margin %.1f mm; base %d triangles -> refined at the wall %d (%d edge splits, %d passes), health %s"
        % (len(E), M, len(TBx), len(TBr), nsplit, passes, rep["refine"]["open_nonmanifold"]))
    fB = fcore(VBr); fB, nb_ = remove_tiny_islands(VBr, TBr, fB, +1, 1.0)
    fP = fcore(VP); fP, np_ = remove_tiny_islands(VP, TP, fP, -1, 1.0)
    if nb_ or np_: say("  tiny islands under 1 mm given their side's sign before the clip: %d on the base, %d on the piece" % (nb_, np_))
    rep["tiny_islands_flipped"] = {"base": int(nb_), "piece": int(np_)}
    VA, TA = clip_by_core(VBr, TBr, fB, inside=False)
    VPi, TPi = clip_by_core(VP, TP, fP, inside=True)
    VPi, TPi, ncomp, ndrop, ndrop_t = components_reaching_rim(VPi, TPi)
    VPi, TPi = _weld(VPi, TPi, 1e-9)
    hA = health(VA, TA); hP = health(VPi, TPi)
    rep["base_outside"] = {"triangles": int(len(TA)), "open_nonmanifold": list(hA)}
    rep["piece_inside"] = {"triangles": int(len(TPi)), "components": int(ncomp), "closed_fragments_dropped": int(ndrop), "triangles_dropped": int(ndrop_t), "open_nonmanifold": list(hP)}
    say("  base outside the core: %d triangles, health %s; piece inside: %d triangles in %d component(s), %d closed fragment(s) dropped (%d triangles), health %s"
        % (len(TA), hA, len(TPi), ncomp, ndrop, ndrop_t, hP))
    if len(TA) == 0 or len(TPi) == 0:
        rep["error"] = "the clip left nothing on one side (base outside %d, piece inside %d)" % (len(TA), len(TPi)); _dump(VA, TA, VPi, TPi); return None, None, rep
    if rim_snap > 0:
        VPi, rep["rim_snap"] = snap_rim(VPi, TPi, VBr, TBr, rim_snap, h, say=say, relax_rings=int(os.environ.get("KEEP_RELAX_RINGS", "3")), relax_iter=int(os.environ.get("KEEP_RELAX_ITER", "3")))
        hP2 = health(VPi, TPi); rep["piece_inside"]["open_nonmanifold_after_snap"] = list(hP2)
    if join == "zipper":
        V, T, mrep = zipper_join(VA, TA, VPi, TPi, tol=tol, say=say)
    else:
        V, T, mrep = CS.seam_merge(VA, TA, VPi, TPi, tol=tol, assign=KR._assign, say=say, onto="A", tiny="collapse", micro=micro)
    rep["seam_xyz"] = mrep.pop("seam_xyz", None)
    rep["merge"] = _jsonable({k: v for k, v in mrep.items() if k != "far_points"}); rep["join"] = join
    if nm_ok > 0 and V is None and mrep.get("seam_open", 1) == 0 and 0 < int(mrep.get("nonmanifold_out", 99)) <= nm_ok and mrep.get("_V") is not None:
        V, T = mrep["_V"], mrep["_T"]
        rep["merge"]["taken_with_nonmanifold"] = int(mrep.get("nonmanifold_out")); rep["merge"]["nonmanifold_at"] = _jsonable(mrep.get("nonmanifold_at", []))[:nm_ok]
        say("  seam closed with %d non-manifold edge(s) (%s) - taken; the repair step merges them" % (int(mrep.get("nonmanifold_out")), rep["merge"]["nonmanifold_at"]))
    if open_ok > 0 and V is None and 0 < int(mrep.get("seam_open", 99)) <= open_ok and int(mrep.get("nonmanifold_out", 99)) <= int(mrep.get("nonmanifold_in", 0)) and mrep.get("_V") is not None:
        # open edges
        V, T = mrep["_V"], mrep["_T"]
        rep["merge"]["taken_with_open"] = int(mrep.get("seam_open")); rep["merge"]["micro_holes_open"] = _jsonable(mrep.get("micro_holes_open", []))[:40]
        say("  seam taken with %d open edge(s) beyond the inputs' own (%s) - the repair's fill closes them" % (int(mrep.get("seam_open")), mrep.get("micro_hole_method", "")))
    if V is None:
        rep["error"] = "seam merge refused: " + str(mrep.get("error")); rep["far_points"] = _jsonable(mrep.get("far_points", [])[:20])
        _dump(VA, TA, VPi, TPi); return None, None, rep
    V, T = _weld(V, T, 1e-9)
    h = health(V, T); rep["out"] = {"triangles": int(len(T)), "open_nonmanifold": list(h)}
    say("  joined (%s): %d loops paired, seam gap p50 %.3f / p99 %.3f / max %.3f mm, strip %d triangles; result %d triangles, health %s"
        % (join, mrep.get("loops_paired", 0), mrep.get("seam_gap_p50", 0.0), mrep.get("seam_gap_p99", 0.0), mrep.get("seam_gap_max", mrep.get("worst_mm", 0.0)), mrep.get("strip_triangles", 0), len(T), h))
    return V, T, rep

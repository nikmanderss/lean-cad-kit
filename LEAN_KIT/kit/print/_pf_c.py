# open edges
# over the
import os, sys, json, time, struct, math
import numpy as np
sys.path.insert(0, os.environ["KIT_HOME"])
import kitlib_render as R
import vtk
from vtk.util import numpy_support as ns
import Mesh

IN = os.environ["PF_IN"]; OUT = os.environ["PF_OUT"]; RJ = os.environ["PF_JSON"]
MAX_MB = float(os.environ.get("PF_MAX_MB", "100")); FILL_MAX = int(os.environ.get("PF_FILL_MAX", "5000"))
TAG = os.environ.get("PF_TAG", "kit printfile").encode("ascii", "replace")[:80]
DEC = os.environ.get("PF_DEC", "pro")
WELD = float(os.environ.get("PF_WELD", "1e-4"))
t0 = time.time()
rep = {"in": IN}


def say(*a):
    print(*a, flush=True)


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def write_stl(p, V, T, tag):
    tri = V[T].astype(np.float32)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1
    rec = np.zeros(len(tri), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    rec["n"] = n / ln[:, None]; rec["v"] = tri.reshape(-1, 9)
    with open(p, "wb") as f:
        f.write(tag.ljust(80, b" ")); f.write(struct.pack("<I", len(tri))); f.write(rec.tobytes())


def weld(tri, tol=None):
    """points merged within tol (FreeCAD's scale by default), degenerate and duplicate triangles dropped"""
    tol = WELD if tol is None else tol
    q = np.round(tri.reshape(-1, 3) / tol).astype(np.int64)
    u_, inv = np.unique(q, axis=0, return_inverse=True)
    V = u_ * tol; T = inv.reshape(-1, 3)
    T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
    Ts = np.sort(T, 1); _, first = np.unique(Ts, axis=0, return_index=True); T = T[np.sort(first)]
    return V, T


def edge_counts(T):
    e = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
    ue, inv, c = np.unique(e, axis=0, return_inverse=True, return_counts=True)
    return ue, inv.ravel(), c


def boundary_loops(T):
    """closed loops of open edges as vertex lists; junction vertices (three or more open edges) split them off.
    THE WALK IS UNDIRECTED (2026-09-24): a rim triangle wound the other way makes a directed walk fail silently
    and leave its hole open (24 open edges on R32 after the pinch cut). Each vertex with exactly two open edges
    is walked to its neighbours whatever the edges' directions; the cap's orientation is settled afterwards
    against the mesh's own directed open edges (`fill_loop`), which are left in `boundary_loops.open_dir`."""
    E = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    Es = np.sort(E, 1)
    ue, inv, c = np.unique(Es, axis=0, return_inverse=True, return_counts=True)
    inv = inv.ravel()
    openE = E[c[inv] == 1]
    boundary_loops.last_junctions = set()
    boundary_loops.open_dir = set((int(a), int(b)) for a, b in openE)
    if len(openE) == 0:
        return [], 0, 0
    adj = {}
    for a, b in openE:
        a = int(a); b = int(b)
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    junction = {v for v, n in adj.items() if len(n) > 2}
    boundary_loops.last_junctions = junction
    loops = []; used = set(); n_junc_edges = 0
    for a, b in openE:
        a = int(a); b = int(b)
        key = (min(a, b), max(a, b))
        if key in used:
            continue
        if a in junction or b in junction:
            n_junc_edges += 1; used.add(key); continue
        loop = [a]; prev = a; cur = b; used.add(key); ok = True
        while cur != a:
            loop.append(cur)
            if cur in junction:
                ok = False; break
            outs = [w for w in adj.get(cur, []) if w != prev and (min(cur, w), max(cur, w)) not in used]
            if len(outs) != 1:
                ok = False; break
            w = outs[0]; used.add((min(cur, w), max(cur, w))); prev, cur = cur, w
            if len(loop) > 200000:
                ok = False; break
        if ok and len(loop) >= 3:
            loops.append(loop)
    return loops, len(junction), n_junc_edges


def min_area_triangulation(P):
    """the triangulation of a closed 3-D polygon (points in loop order) with the least total area - dynamic
    programming over intervals, O(n^3) with the inner loop vectorised. Needs no projection, so a long thin loop
    that bends in space (a crack along a curved edge, the mouth of a film at a corner) closes without folds."""
    n = len(P)
    INF = 1e30
    W = np.full((n, n), INF); W[np.arange(n - 1), np.arange(1, n)] = 0.0
    K = np.full((n, n), -1, np.int64)
    for gap in range(2, n):
        i = np.arange(0, n - gap); j = i + gap
        for a, b in zip(i, j):
            ks = np.arange(a + 1, b)
            area = 0.5 * np.linalg.norm(np.cross(P[ks] - P[a], P[b] - P[a]), axis=1)
            tot = W[a, ks] + W[ks, b] + area
            m = int(np.argmin(tot)); W[a, b] = tot[m]; K[a, b] = ks[m]
    tris = []
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        k = int(K[a, b]); tris.append((a, k, b)); stack.append((a, k)); stack.append((k, b))
    return tris


def fill_loop(V, loop, nrm=None):
    """triangles (index triples) closing one boundary loop. Under 400 vertices: the minimum-area triangulation in
    3-D (no projection, no folds). Larger: ear clipping in the plane normal to the surface around the hole (the mean
    normal of the triangles on the loop; the loop's best-fit plane when that is degenerate). Only a COMPLETE
    triangulation (m - 2 triangles) is returned - a partial one leaves the loop open and hides that. The boundary runs
    a->b as the existing triangles wind, so the cap must wind the other way (b->a) to be consistent."""
    P = V[loop]
    if len(loop) <= 400:
        tris = min_area_triangulation(P)
    else:
        ctr = P.mean(0); Q = P - ctr
        u, s, vt = np.linalg.svd(Q, full_matrices=False)
        if nrm is not None and np.linalg.norm(nrm) > 0.3:
            nz = nrm / np.linalg.norm(nrm)
            e1 = vt[0] - (vt[0] @ nz) * nz
            if np.linalg.norm(e1) < 1e-6:
                e1 = vt[1] - (vt[1] @ nz) * nz
            e1 = e1 / np.linalg.norm(e1); e2 = np.cross(nz, e1)
        else:
            e1, e2 = vt[0], vt[1]
        tris = R._ear_clip(np.column_stack([Q @ e1, Q @ e2]))
        if len(tris) != len(loop) - 2:
            tris = R._ear_clip(np.column_stack([Q @ vt[0], Q @ vt[1]]))
    if len(tris) != len(loop) - 2:
        return []
    out = np.array([[loop[a], loop[b], loop[c]] for a, b, c in tris], np.int64)
    # open edges
    od = getattr(boundary_loops, "open_dir", None)
    if od:
        same = 0; opp = 0
        for a, b, c in out:
            for x, y in ((int(a), int(b)), (int(b), int(c)), (int(c), int(a))):
                if (x, y) in od:
                    same += 1
                elif (y, x) in od:
                    opp += 1
        if same > opp:
            out = out[:, [0, 2, 1]]
    else:
        L = np.array(loop); nxt = {int(L[i]): int(L[(i + 1) % len(L)]) for i in range(len(L))}
        agree = sum(1 for a, b, c in out for x, y in ((a, b), (b, c), (c, a)) if nxt.get(int(x)) == int(y))
        disagree = sum(1 for a, b, c in out for x, y in ((a, b), (b, c), (c, a)) if nxt.get(int(y)) == int(x))
        if agree > disagree:
            out = out[:, [0, 2, 1]]
    return out


def largest_shell(V, T, tmp):
    """the largest shell by FreeCAD's component split (what nmfix cut loose - zero-volume slivers - goes), and the rest."""
    write_stl(tmp, V, T, b"kit printfile tmp")
    m = Mesh.Mesh(tmp)
    comps = m.getSeparateComponents()
    comps.sort(key=lambda c_: -c_.CountFacets)
    dropped = []
    for c_ in comps[1:]:
        bb = c_.BoundBox
        dropped.append({"facets": c_.CountFacets, "volume": round(float(c_.Volume), 4),
                        "box": [round(v, 2) for v in (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax)]})
    tp = comps[0].Topology
    try:
        os.remove(tmp)
    except OSError:
        pass
    Vk, Tk = weld(np.asarray(tp[0], float)[np.asarray(tp[1], np.int64)])
    return Vk, Tk, len(comps), dropped


tri = read_stl(IN)
V, T = weld(tri)
ue, inv, c = edge_counts(T)
rep["in_counts"] = {"facets": int(len(T)), "open_edges": int((c == 1).sum()), "nonmanifold_edges": int((c > 2).sum())}
say("in : %d facets, open %d, non-manifold %d (%.0f s)" % (len(T), rep["in_counts"]["open_edges"], rep["in_counts"]["nonmanifold_edges"], time.time() - t0))
V, T, n_sh, dropped = largest_shell(V, T, OUT + ".tmp.stl")
rep["loose"] = {"shells": n_sh, "dropped": dropped[:40], "dropped_facets": int(sum(d_["facets"] for d_ in dropped))}
say("loose: %d shell(s), largest kept, %d dropped (%d facets) (%.0f s)" % (n_sh, len(dropped), rep["loose"]["dropped_facets"], time.time() - t0))
# open edges
def fill_rounds(V, T, label):
    st = {"loops": 0, "filled": 0, "triangles_added": 0, "flaps_removed": 0, "skipped_loops": [], "junction_vertices": 0, "junction_triangles_cut": 0}
    for rnd in range(6):
        P = V[T]; TN = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); TN = TN / (np.linalg.norm(TN, axis=1)[:, None] + 1e-30)
        vtn = np.zeros((len(V), 3)); np.add.at(vtn, T[:, 0], TN); np.add.at(vtn, T[:, 1], TN); np.add.at(vtn, T[:, 2], TN)
        loops, n_junc, n_junc_edges = boundary_loops(T)
        st["junction_vertices"] = n_junc
        if not loops and n_junc:
            jv = boundary_loops.last_junctions
            if st["junction_triangles_cut"] == 0 and jv:
                m = np.isin(T[:, 0], list(jv)) | np.isin(T[:, 1], list(jv)) | np.isin(T[:, 2], list(jv))
                st["junction_triangles_cut"] = int(m.sum()); T = T[~m]
                say("%s round %d: %d junction vertices with %d open edges - %d triangles on them cut, refilling" % (label, rnd + 1, n_junc, n_junc_edges, st["junction_triangles_cut"]))
                continue
        if not loops:
            ue, inv, c = edge_counts(T)
            if int((c > 2).sum()) and not st.get("pinch_triangles_cut"):
                nm = (c > 2)[inv].reshape(3, -1).any(0)
                st["pinch_triangles_cut"] = int(nm.sum()); T = T[~nm]
                say("%s round %d: no loops but %d non-manifold edge(s) - %d triangles on them cut, refilling" % (label, rnd + 1, int((c > 2).sum()), st["pinch_triangles_cut"]))
                continue
            break
        say("%s round %d: %d closed boundary loop(s), %d junction vertices with %d open edges at them" % (label, rnd + 1, len(loops), n_junc, n_junc_edges))
        added = []
        for lp in loops:
            if len(lp) > FILL_MAX:
                st["skipped_loops"].append(len(lp)); continue
            f = fill_loop(V, lp, vtn[lp].sum(0))
            if len(f):
                added.append(f)
            else:
                st["skipped_loops"].append(len(lp))
        st["loops"] += len(loops); st["filled"] += len(added)
        if not added:
            break
        caps = np.vstack(added); st["triangles_added"] += len(caps)
        T = np.vstack([T, caps])
        Ts = np.sort(T, 1)
        _, first, cnt = np.unique(Ts, axis=0, return_index=True, return_counts=True)
        dup_keys = set(map(tuple, Ts[first[cnt > 1]]))
        if dup_keys:
            isdup = np.array([tuple(r) in dup_keys for r in Ts])
            st["flaps_removed"] += int(isdup.sum()); T = T[~isdup]
            say("  %d triangles were duplicated by caps (flaps) - both copies removed, refilling" % int(isdup.sum()))
            continue
        ue, inv, c = edge_counts(T)
        if int((c == 1).sum()) == 0:
            if int((c > 2).sum()) and not st.get("pinch_triangles_cut"):
                nm = (c > 2)[inv].reshape(3, -1).any(0)
                st["pinch_triangles_cut"] = int(nm.sum()); T = T[~nm]
                say("%s round %d: %d non-manifold edge(s) - %d triangles on them cut, refilling" % (label, rnd + 1, int((c > 2).sum()), st["pinch_triangles_cut"]))
                continue
            break
    ue, inv, c = edge_counts(T)
    st["open_after"] = int((c == 1).sum()); st["nonmanifold_after"] = int((c > 2).sum()); st["skipped_loops"] = st["skipped_loops"][:20]
    say("%s: %d loop(s) closed with %d triangles, %d flaps removed, %d skipped; open %d, non-manifold %d (%.0f s)"
        % (label, st["filled"], st["triangles_added"], st["flaps_removed"], len(st["skipped_loops"]), st["open_after"], st["nonmanifold_after"], time.time() - t0))
    return V, T, st


V, T, rep["fill"] = fill_rounds(V, T, "fill")
if rep["fill"]["open_after"]:
    tmp = OUT + ".fill.stl"; write_stl(tmp, V, T, b"kit printfile fill")
    m = Mesh.Mesh(tmp)
    try:
        m.fillupHoles(FILL_MAX)
        tp = m.Topology; V = np.asarray(tp[0], float); T = np.asarray(tp[1], np.int64)
        V, T = weld(V[T])
        ue, inv, c = edge_counts(T)
        rep["fill"]["fillupHoles"] = {"open_after": int((c == 1).sum()), "nonmanifold_after": int((c > 2).sum()), "facets": int(len(T))}
        say("fillupHoles: open %d, non-manifold %d (%.0f s)" % (rep["fill"]["fillupHoles"]["open_after"], rep["fill"]["fillupHoles"]["nonmanifold_after"], time.time() - t0))
    except Exception as e:
        rep["fill"]["fillupHoles"] = {"error": str(e)}; say("fillupHoles failed: %s" % e)
    try:
        os.remove(tmp)
    except OSError:
        pass
# over the
mb = len(T) * 50 / 1e6 + 84e-6
rep["decimate"] = {"mb_before": round(mb, 1), "facets_before": int(len(T))}
if mb > MAX_MB:
    target = int(MAX_MB * 0.92 * 1e6 / 50)
    red = 1.0 - target / float(len(T))
    say("decimate: %.1f MB over %.0f - %d -> %d facets (reduction %.3f), %s" % (mb, MAX_MB, len(T), target, red, DEC))
    pd = vtk.vtkPolyData()
    pts = vtk.vtkPoints(); pts.SetData(ns.numpy_to_vtk(np.ascontiguousarray(V), deep=True)); pd.SetPoints(pts)
    cells = np.hstack([np.full((len(T), 1), 3, np.int64), T.astype(np.int64)]).ravel()
    ca = vtk.vtkCellArray(); ca.SetCells(len(T), ns.numpy_to_vtkIdTypeArray(cells, deep=True)); pd.SetPolys(ca)

    def run_dec(kind):
        if kind == "quadric":
            d = vtk.vtkQuadricDecimation(); d.SetInputData(pd); d.SetTargetReduction(red); d.VolumePreservationOn()
        else:
            d = vtk.vtkDecimatePro(); d.SetInputData(pd); d.SetTargetReduction(red); d.PreserveTopologyOn()
            d.BoundaryVertexDeletionOff(); d.SplittingOff(); d.SetFeatureAngle(60.0)
        d.Update(); o = d.GetOutput()
        Vd = ns.vtk_to_numpy(o.GetPoints().GetData()).astype(float)
        Td = ns.vtk_to_numpy(o.GetPolys().GetData()).reshape(-1, 4)[:, 1:].astype(np.int64)
        return weld(Vd[Td])
    ue, inv, c = edge_counts(T)
    o_before = int((c == 1).sum()); n_before = int((c > 2).sum())
    Vd, Td = run_dec(DEC)
    ue, inv, cd = edge_counts(Td)
    od, nd = int((cd == 1).sum()), int((cd > 2).sum())
    say("  %s: %d facets, open %d (was %d), non-manifold %d (was %d) after the %g weld (%.0f s)" % (DEC, len(Td), od, o_before, nd, n_before, WELD, time.time() - t0))
    if (od > o_before + 50 or nd > n_before + 50) and DEC == "quadric":
        say("  quadric opened the mesh - DecimatePro with topology preserved instead")
        Vd, Td = run_dec("pro")
        ue, inv, cd = edge_counts(Td)
        od, nd = int((cd == 1).sum()), int((cd > 2).sum())
        say("  pro: %d facets, open %d, non-manifold %d (%.0f s)" % (len(Td), od, nd, time.time() - t0))
        rep["decimate"]["method"] = "pro (quadric opened the mesh)"
    else:
        rep["decimate"]["method"] = DEC
    V, T = Vd, Td
    rep["decimate"].update({"facets_after": int(len(T)), "open_after": od, "nonmanifold_after": nd, "reduction": round(red, 3)})
    if od:
        V, T, rep["refill"] = fill_rounds(V, T, "refill")
else:
    rep["decimate"]["method"] = "none needed"
P = V[T]
vol = float(np.einsum("ij,ij->i", P[:, 0], np.cross(P[:, 1], P[:, 2])).sum() / 6.0)
ue, inv, c = edge_counts(T)
write_stl(OUT, V, T, TAG)
mb = os.path.getsize(OUT) / 1e6
rep["out"] = {"file": OUT, "facets": int(len(T)), "points": int(len(V)), "MB": round(mb, 1), "volume": round(vol, 1),
              "open_edges": int((c == 1).sum()), "nonmanifold_edges": int((c > 2).sum())}
say("out: %d facets, %.1f MB, volume %.1f mm3, open %d, non-manifold %d -> %s (%.0f s)"
    % (len(T), mb, vol, rep["out"]["open_edges"], rep["out"]["nonmanifold_edges"], OUT, time.time() - t0))
json.dump(rep, open(RJ, "w"), indent=1)
say("DONE")

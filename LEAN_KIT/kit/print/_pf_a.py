# over the
import os, sys, json, time, struct
import numpy as np
import vtk
from vtk.util import numpy_support as ns

IN = os.environ["PF_IN"]; OUT = os.environ["PF_OUT"]; RJ = os.environ["PF_JSON"]
FILM = float(os.environ.get("PF_FILM", "0.35")); FILM_MAX = float(os.environ.get("PF_FILM_MAX_PCT", "2.0"))
KEEP = int(os.environ.get("PF_KEEP", "1"))
t0 = time.time()
rep = {"in": IN}


def say(*a):
    print(*a, flush=True)


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    if len(b) < 84 + n * 50:
        raise SystemExit("FAIL: %s is not a binary STL with %d facets" % (p, n))
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def write_stl(p, V, T, tag=b"kit printfile A"):
    tri = V[T].astype(np.float32)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1
    rec = np.zeros(len(tri), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    rec["n"] = n / ln[:, None]; rec["v"] = tri.reshape(-1, 9)
    with open(p, "wb") as f:
        f.write(tag.ljust(80, b" ")); f.write(struct.pack("<I", len(tri))); f.write(rec.tobytes())


def edge_counts(T):
    e = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
    ue, inv, c = np.unique(e, axis=0, return_inverse=True, return_counts=True)
    return ue, inv.ravel(), c


def polydata(V, T):
    pd = vtk.vtkPolyData()
    pts = vtk.vtkPoints(); pts.SetData(ns.numpy_to_vtk(np.ascontiguousarray(V), deep=True)); pd.SetPoints(pts)
    cells = np.hstack([np.full((len(T), 1), 3, np.int64), T.astype(np.int64)]).ravel()
    ca = vtk.vtkCellArray(); ca.SetCells(len(T), ns.numpy_to_vtkIdTypeArray(cells, deep=True)); pd.SetPolys(ca)
    return pd


def largest_shells(V, T, keep, tmp):
    """(V, T) of the `keep` largest shells and the list of the dropped ones, by FreeCAD's own component split
    (facets joined through shared edges). Goes through a temporary STL: building a Mesh from 2.6 M python
    triangles takes minutes, reading a file takes seconds."""
    import Mesh
    write_stl(tmp, V, T, b"kit printfile tmp")
    m = Mesh.Mesh(tmp)
    comps = m.getSeparateComponents()
    comps.sort(key=lambda c_: -c_.CountFacets)
    dropped = []
    for c_ in comps[keep:]:
        bb = c_.BoundBox
        dropped.append({"facets": c_.CountFacets, "volume": round(float(c_.Volume), 4),
                        "box": [round(v, 2) for v in (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax)]})
    Vs, Ts, off = [], [], 0
    for c_ in comps[:keep]:
        tp = c_.Topology
        Vs.append(np.asarray(tp[0], float)); Ts.append(np.asarray(tp[1], np.int64) + off); off += len(tp[0])
    try:
        os.remove(tmp)
    except OSError:
        pass
    return np.vstack(Vs), np.vstack(Ts), len(comps), dropped


tri = read_stl(IN)
say("in : %d facets (%.0f s)" % (len(tri), time.time() - t0))
q = np.round(tri.reshape(-1, 3) / 1e-6).astype(np.int64)
u_, inv = np.unique(q, axis=0, return_inverse=True)
V = u_ * 1e-6; T = inv.reshape(-1, 3)
n_in = len(T)
T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
P = V[T]; area = 0.5 * np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1)
T = T[area > 1e-9]
Ts = np.sort(T, 1); _, first = np.unique(Ts, axis=0, return_index=True)
T = T[np.sort(first)]
rep["weld"] = {"facets_in": int(n_in), "points": int(len(V)), "degenerate_or_duplicate_removed": int(n_in - len(T))}
ue, inv, c = edge_counts(T)
rep["after_weld"] = {"facets": int(len(T)), "open_edges": int((c == 1).sum()), "nonmanifold_edges": int((c > 2).sum())}
say("weld: %d facets, %d removed as degenerate/duplicate; open %d, non-manifold %d (%.0f s)"
    % (len(T), n_in - len(T), rep["after_weld"]["open_edges"], rep["after_weld"]["nonmanifold_edges"], time.time() - t0))
# cannot be read
V, T, n, dropped = largest_shells(V, T, KEEP, OUT + ".tmp.stl")
rep["fragments"] = {"shells_in": n, "kept": min(KEEP, n), "dropped": dropped[:60], "dropped_facets": int(sum(d_["facets"] for d_ in dropped))}
say("fragments: %d shell(s) in, %d kept, %d dropped (%d facets) (%.0f s)" % (n, min(KEEP, n), len(dropped), rep["fragments"]["dropped_facets"], time.time() - t0))
q = np.round(V / 1e-6).astype(np.int64); u_, inv = np.unique(q, axis=0, return_inverse=True)
V = u_ * 1e-6; T = inv.ravel()[T]

P = V[T]; ctr = P.mean(1)
N = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); area = 0.5 * np.linalg.norm(N, axis=1); N = N / (2 * area[:, None] + 1e-30)
film_mask = np.zeros(len(T), bool)
rep["film"] = {"mm": FILM}
if FILM > 0:
    cs = max(FILM, 1.0)
    lo3 = V.min(0) - 1.0
    dims = np.maximum(((V.max(0) + 1.0 - lo3) / cs).astype(np.int64) + 1, 1)

    def cell_ids(bmin, bmax):
        """(entry_cell_ids, entry_owner) for boxes bmin..bmax (k,3): every cell each box covers"""
        i0 = ((bmin - lo3) / cs).astype(np.int64); i1 = ((bmax - lo3) / cs).astype(np.int64)
        i0 = np.clip(i0, 0, dims - 1); i1 = np.clip(i1, 0, dims - 1)
        cnt = np.prod(i1 - i0 + 1, axis=1)
        owner = np.repeat(np.arange(len(bmin)), cnt)
        first = np.cumsum(cnt) - cnt
        loc = np.arange(cnt.sum()) - np.repeat(first, cnt)
        nx = (i1 - i0 + 1)[owner]
        lx = loc % nx[:, 0]; ly = (loc // nx[:, 0]) % nx[:, 1]; lz = loc // (nx[:, 0] * nx[:, 1])
        cx = i0[owner, 0] + lx; cy = i0[owner, 1] + ly; cz = i0[owner, 2] + lz
        return (cx * dims[1] + cy) * dims[2] + cz, owner
    tri_cells, tri_owner = cell_ids(P.min(1), P.max(1))
    o = np.argsort(tri_cells, kind="stable"); tri_cells = tri_cells[o]; tri_owner = tri_owner[o]
    a0 = ctr + N * 0.005; a1 = ctr + N * FILM
    ray_cells, ray_owner = cell_ids(np.minimum(a0, a1), np.maximum(a0, a1))
    say("film: grid %s cells of %.2f mm, %d triangle entries, %d ray entries (%.0f s)" % (tuple(int(d) for d in dims), cs, len(tri_cells), len(ray_cells), time.time() - t0))
    lo_i = np.searchsorted(tri_cells, ray_cells, side="left"); hi_i = np.searchsorted(tri_cells, ray_cells, side="right")
    npair = hi_i - lo_i
    best_t = np.full(len(T), np.inf); best_j = np.full(len(T), -1, np.int64)
    CH = 1500000
    order = np.arange(len(ray_cells))
    start = 0; total_pairs = int(npair.sum()); done = 0; last_said = 0
    say("film: %d candidate pairs to test (%.0f s)" % (total_pairs, time.time() - t0))
    while start < len(order):
        acc = np.cumsum(npair[start:])
        stop = start + int(np.searchsorted(acc, CH)) + 1
        sel = order[start:stop]
        cnt = npair[sel]
        if cnt.sum():
            ri = np.repeat(ray_owner[sel], cnt)
            first = np.repeat(lo_i[sel], cnt)
            offs = np.arange(cnt.sum()) - np.repeat(np.cumsum(cnt) - cnt, cnt)
            tj = tri_owner[first + offs]
            m = tj != ri
            ri = ri[m]; tj = tj[m]
            v0 = P[tj, 0]; e1 = P[tj, 1] - v0; e2 = P[tj, 2] - v0
            d = N[ri]
            pv = np.cross(d, e2); det = np.einsum("ij,ij->i", e1, pv)
            ok = np.abs(det) > 1e-12
            inv_det = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
            tv = ctr[ri] - v0
            u = np.einsum("ij,ij->i", tv, pv) * inv_det
            qv = np.cross(tv, e1)
            v = np.einsum("ij,ij->i", d, qv) * inv_det
            t = np.einsum("ij,ij->i", e2, qv) * inv_det
            hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > 0.005) & (t < FILM)
            if hit.any():
                ri = ri[hit]; tj = tj[hit]; t = t[hit]
                np.minimum.at(best_t, ri, t)
                mm = t <= best_t[ri] + 1e-12
                best_j[ri[mm]] = tj[mm]
            done += int(cnt.sum())
        start = stop
        if done - last_said >= 20000000 or start >= len(order):
            say("  %d of %d candidate pairs (%.0f s)" % (done, total_pairs, time.time() - t0)); last_said = done
    hit_rays = np.where(best_j >= 0)[0]
    j = best_j[hit_rays]
    facing = np.einsum("ij,ij->i", N[j], N[hit_rays]) < -0.9
    n_pairs = int(facing.sum())
    film_mask[hit_rays[facing]] = True; film_mask[j[facing]] = True
    n_film = int(film_mask.sum()); a_film = float(area[film_mask].sum())
    pct = 100.0 * a_film / max(float(area.sum()), 1e-9)
    say("film: %d wall triangles from %d facing pairs, %.1f mm2 (%.3f %% of the surface) (%.0f s)" % (n_film, n_pairs, a_film, pct, time.time() - t0))
    rep["film"].update({"wall_triangles": n_film, "pairs": n_pairs, "wall_mm2": round(a_film, 1), "pct_of_surface": round(pct, 3)})
    if pct > FILM_MAX:
        say("FAIL: the film walls are %.2f %% of the surface, over PF_FILM_MAX_PCT %.1f - a designed gap narrower than %.2f mm is being "
            "eaten; lower PF_FILM or raise the limit on purpose" % (pct, FILM_MAX, FILM))
        json.dump(rep, open(RJ, "w"), indent=1); sys.exit(1)
    if n_film:
        fi = np.where(film_mask)[0]
        cell = np.floor(ctr[fi] / 4.0).astype(np.int64)
        keys, kinv = np.unique(cell, axis=0, return_inverse=True); kinv = kinv.ravel()
        lab = np.arange(len(keys))
        kd = {tuple(k): i for i, k in enumerate(keys)}
        for _ in range(len(keys)):
            changed = False
            for i, k in enumerate(keys):
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            j = kd.get((k[0] + dx, k[1] + dy, k[2] + dz))
                            if j is not None and lab[j] < lab[i]:
                                lab[i] = lab[j]; changed = True
            if not changed:
                break
        cl = []
        for g in np.unique(lab):
            ii = fi[lab[kinv] == g]
            lo = ctr[ii].min(0); hi = ctr[ii].max(0)
            cl.append({"triangles": int(len(ii)), "mm2": round(float(area[ii].sum()), 1),
                       "box": [round(float(v), 1) for v in (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])]})
        cl.sort(key=lambda x: -x["mm2"])
        rep["film"]["clusters"] = cl
        rep["film"]["clusters_total"] = len(cl)
        say("   %d film cluster(s) in all, %.1f mm2; the 12 largest:" % (len(cl), float(sum(x["mm2"] for x in cl))))
        for x in cl[:12]:
            say("   film %7.1f mm2  %6d tris  box x %7.1f..%7.1f  y %7.1f..%7.1f  z %6.1f..%6.1f" % ((x["mm2"], x["triangles"]) + tuple(x["box"])))
    if film_mask.any():
        ue2, inv2, c2 = edge_counts(T)
        nT = len(T)
        tri_of = {}
        for k, e in enumerate(inv2):
            tri_of.setdefault(int(e), []).append(k % nT)
        walls = np.where(film_mask)[0]
        band = np.zeros(len(T), bool)
        for w in walls:
            for e in inv2[[w, w + nT, w + 2 * nT]]:
                for t in tri_of.get(int(e), []):
                    if t == w or film_mask[t] or band[t]:
                        continue
                    if float(N[t] @ N[w]) > 0.9:
                        continue
                    span = (V[T[t]] - ctr[w]) @ N[w]
                    if span.max() - span.min() <= 1.5 * FILM and abs(span).max() <= 1.5 * FILM:
                        band[t] = True
        rep["film"]["side_bands_removed"] = int(band.sum())
        say("film: %d side-band triangles removed with the walls" % int(band.sum()))
        film_mask |= band
    T = T[~film_mask]
# open edges
n_dang = 0
for _ in range(50):
    ue, inv, c = edge_counts(T)
    open_e = (c == 1)[inv].reshape(3, -1).sum(0)
    d = open_e >= 2
    if not d.any():
        break
    n_dang += int(d.sum()); T = T[~d]
rep["dangling_removed"] = n_dang
say("dangling: %d triangles removed (%.0f s)" % (n_dang, time.time() - t0))
used = np.unique(T); remap = -np.ones(len(V), np.int64); remap[used] = np.arange(len(used))
V2 = V[used]; T2 = remap[T]
ue, inv, c = edge_counts(T2)
rep["out"] = {"file": OUT, "facets": int(len(T2)), "points": int(len(V2)), "open_edges": int((c == 1).sum()), "nonmanifold_edges": int((c > 2).sum())}
write_stl(OUT, V2, T2)
say("out: %d facets, open %d, non-manifold %d -> %s (%.0f s)" % (len(T2), rep["out"]["open_edges"], rep["out"]["nonmanifold_edges"], OUT, time.time() - t0))
json.dump(rep, open(RJ, "w"), indent=1)
say("DONE")

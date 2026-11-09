# kit rebuild
import Mesh, os, sys, time, numpy as np
def _fail(m): print(m if str(m).startswith("FAIL") else "FAIL: " + str(m), flush=True); raise SystemExit(1)
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
TAG = os.environ.get("LK_TAG", "")
sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
src, out = os.environ["STL"], os.environ["OUT"]; T0 = time.time()
rd = R.read_stl(src); V, T = np.asarray(rd[0], float), np.asarray(rd[1], int)
key = np.round(V / 1e-4).astype(np.int64); _, ui, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1); V = V[ui]; T = inv[T]
def clean(V, T):
    T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
    _, uu = np.unique(np.sort(T, axis=1), axis=0, return_index=True); return V, T[np.sort(uu)]
V, T = clean(V, T)
# INTERNAL
if os.environ.get("INTERNAL_DROP", "1" if os.path.basename(out).startswith("arr_") else "0") == "1":
    try:
        _im, _icl = R.internal_triangles(V, T)
        if _im.any():
            T = T[~_im]
            print("internal triangles dropped: %d (%.3f mm2) in %d place(s) - %s" % (int(_im.sum()), sum(c["area_mm2"] for c in _icl), len(_icl), "; ".join("%.3f mm2 at %s" % (c["area_mm2"], c["at"]) for c in _icl[:6])), flush=True)
        else:
            print("internal triangles: none", flush=True)
    except Exception as _ex:
        print("internal-triangle check skipped: %r" % (_ex,), flush=True)
def to_mesh(V, T):
    tmp = os.path.join(os.path.dirname(out), "_tmp_repair.stl"); R.write_stl(tmp, V, T); return Mesh.Mesh(tmp)
# collapsed
SLIV = float(os.environ.get("SLIV", "0.01")); SLIV_A = float(os.environ.get("SLIV_A", "5e-4"))
for rnd in range(4):
    E = np.stack([np.linalg.norm(V[T[:, 1]] - V[T[:, 0]], axis=1), np.linalg.norm(V[T[:, 2]] - V[T[:, 1]], axis=1), np.linalg.norm(V[T[:, 0]] - V[T[:, 2]], axis=1)], axis=1)
    area = 0.5 * np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1)
    bad = np.nonzero((E.min(axis=1) < SLIV) | (area < SLIV_A))[0]
    if len(bad) == 0: break
    nb = [set() for _ in range(len(V))]
    for a, b, c in T: nb[a].update((b, c)); nb[b].update((a, c)); nb[c].update((a, b))
    order = np.argsort(T.ravel()); vidx = T.ravel()[order]; tidx = np.repeat(np.arange(len(T)), 3)[order]
    starts = np.searchsorted(vidx, np.arange(len(V) + 1))
    def tris_of(v): return tidx[starts[v]:starts[v + 1]]
    mapping = np.arange(len(V)); touched = np.zeros(len(V), bool); n = 0; refused = 0; flipped = 0
    for f in bad:
        t = T[f]; k = int(np.argmin(E[f])); u, w = int(t[k]), int(t[(k + 1) % 3])
        if touched[u] or touched[w] or E[f, k] > 0.15: continue
        if len(nb[u] & nb[w]) != 2: refused += 1; continue
        tl = np.unique(np.concatenate([tris_of(u), tris_of(w)]))
        P0 = V[T[tl]]; n0 = np.cross(P0[:, 1] - P0[:, 0], P0[:, 2] - P0[:, 0])
        mid = 0.5 * (V[u] + V[w]); ou, ow = V[u].copy(), V[w].copy(); V[u] = mid; V[w] = mid
        P1 = V[T[tl]]; n1 = np.cross(P1[:, 1] - P1[:, 0], P1[:, 2] - P1[:, 0])
        dying = np.array([u in T[j] and w in T[j] for j in tl])
        ok = np.all(np.einsum("ij,ij->i", n0, n1)[~dying] > 0.0)
        if not ok: V[u] = ou; V[w] = ow; flipped += 1; continue
        mapping[w] = u; touched[u] = touched[w] = True
        for q in (u, w): touched[list(nb[q])] = True
        n += 1
    T = mapping[T]; V, T = clean(V, T)
    print("sliver pass %d: %d candidates, %d collapsed, %d refused (link), %d refused (flip) -> %d facets" % (rnd, len(bad), n, refused, flipped, len(T)), flush=True)
for it in range(4):
    m = to_mesh(V, T); si = m.getSelfIntersections()
    print("iteration %d: %d self-intersecting pairs, solid %s, non-manifold %s, facets %d (%.0fs)" % (it, len(si), m.isSolid(), m.hasNonManifolds(), len(T), time.time() - T0), flush=True)
    if not si: break
    area = 0.5 * np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1)
    nb2 = [set() for _ in range(len(V))]
    for a, b, c in T: nb2[a].update((b, c)); nb2[b].update((a, c)); nb2[c].update((a, b))
    mapping = np.arange(len(V)); done = set(); Vk, Tk = V.copy(), T.copy()
    for p in si:
        a, b = int(p[0]), int(p[1]); f = a if area[a] <= area[b] else b
        if f in done: continue
        done.add(f); t = T[f]; L = [np.linalg.norm(V[t[(k + 1) % 3]] - V[t[k]]) for k in range(3)]; k = int(np.argmin(L))
        u, w = int(t[k]), int(t[(k + 1) % 3])
        if L[k] > 0.15: continue
        if len(nb2[u] & nb2[w]) != 2: continue
        while mapping[u] != u: u = int(mapping[u])
        while mapping[w] != w: w = int(mapping[w])
        if u == w: continue
        mid = 0.5 * (V[u] + V[w]); V[u] = mid; V[w] = mid; mapping[w] = u
    while True:
        m2 = mapping[mapping]
        if np.array_equal(m2, mapping): break
        mapping = m2
    T = mapping[T]; V, T = clean(V, T)
    if R.mesh_health(V, T) != (0, 0):
        V, T = Vk, Tk; print("  collapse would break the manifold - reverted, the remaining pairs stay", flush=True); break
key = np.round(V / 1e-6).astype(np.int64); _, ui, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1); V = V[ui]; T = inv[T]; V, T = clean(V, T)
# open edges
PINCH = float(os.environ.get("PINCH", "0.05"))
# does not reach
SLIT = float(os.environ.get("SLIT", "0.05"))
def _slit_pass(V, T):
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); es = np.sort(e, axis=1)
    u_, cnt_ = np.unique(es, axis=0, return_counts=True); bad = u_[cnt_ != 2]
    if len(bad) == 0: return V, T, 0
    ov = np.unique(bad); adj = {int(v): set() for v in ov}
    for a, b in bad: adj[int(a)].add(int(b)); adj[int(b)].add(int(a))
    P = V[ov]; D = np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2)
    for i, v in enumerate(ov):
        D[i, i] = 1e9
        for w in adj[int(v)]:
            j = np.searchsorted(ov, w)
            if j < len(ov) and ov[j] == w: D[i, j] = 1e9
    mapping = np.arange(len(V)); n = 0
    order = np.argsort(D.min(axis=1))
    for i in order:
        j = int(np.argmin(D[i]))
        if D[i, j] >= SLIT: break
        a, b = int(ov[i]), int(ov[j])
        while mapping[a] != a: a = int(mapping[a])
        while mapping[b] != b: b = int(mapping[b])
        if a == b: continue
        mid = 0.5 * (V[a] + V[b]); V[a] = mid; V[b] = mid; mapping[b] = a; n += 1
    while True:
        m2 = mapping[mapping]
        if np.array_equal(m2, mapping): break
        mapping = m2
    T = mapping[T]; V, T = clean(V, T)
    key_ = np.round(V / 1e-6).astype(np.int64); _, ui_, inv_ = np.unique(key_, axis=0, return_index=True, return_inverse=True); inv_ = inv_.reshape(-1); V = V[ui_]; T = inv_[T]; V, T = clean(V, T)
    return V, T, n
for rnd_s in range(3):
    h0 = R.mesh_health(V, T)
    if h0 == (0, 0): break
    Vk, Tk = V.copy(), T.copy(); V, T, n = _slit_pass(V, T); h1 = R.mesh_health(V, T)
    if n == 0: break
    if sum(h1) >= sum(h0): V, T = Vk, Tk; print("  slit: merging %d vertex pair(s) under %.3f mm did not help (%s -> %s) - reverted" % (n, SLIT, h0, h1), flush=True); break
    print("  slit: %d vertex pair(s) across slits under %.3f mm merged: health %s -> %s" % (n, SLIT, h0, h1), flush=True)
for rnd_p in range(3):
    h0 = R.mesh_health(V, T)
    if h0 == (0, 0): break
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]); es = np.sort(e, axis=1)
    u_, cnt_ = np.unique(es, axis=0, return_counts=True)
    bad = u_[cnt_ != 2]; L_ = np.linalg.norm(V[bad[:, 0]] - V[bad[:, 1]], axis=1)
    short = bad[L_ < PINCH]
    if len(short) == 0: print("  pinch: %d bad edge(s) but none under %.3f mm - left for FreeCAD's pass" % (len(bad), PINCH), flush=True); break
    mapping = np.arange(len(V)); Vk, Tk = V.copy(), T.copy()
    for a, b in short:
        a, b = int(mapping[a]), int(mapping[b])
        if a == b: continue
        mid = 0.5 * (V[a] + V[b]); V[a] = mid; V[b] = mid; mapping[b] = a
    while True:
        m2 = mapping[mapping]
        if np.array_equal(m2, mapping): break
        mapping = m2
    T = mapping[T]; V, T = clean(V, T)
    key = np.round(V / 1e-6).astype(np.int64); _, ui, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1); V = V[ui]; T = inv[T]; V, T = clean(V, T)
    h1 = R.mesh_health(V, T)
    if sum(h1) >= sum(h0): V, T = Vk, Tk; print("  pinch: merging %d edge(s) did not help (%s -> %s) - reverted" % (len(short), h0, h1), flush=True); break
    print("  pinch: %d edge(s) under %.3f mm merged: health %s -> %s" % (len(short), PINCH, h0, h1), flush=True)
if len(si) == 0 and it == 0:
    vol = abs(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum() / 6.0)
    print("FINAL: 0 pairs (verified at iteration 0), facets %d, volume %.1f; kit health %s" % (len(T), vol, R.mesh_health(V, T)), flush=True)
else:
    m = to_mesh(V, T); si = m.getSelfIntersections()
    print("FINAL: %d pairs, solid %s, non-manifold %s, facets %d, volume %.1f; kit health %s" % (len(si), m.isSolid(), m.hasNonManifolds(), len(T), m.Volume, R.mesh_health(V, T)), flush=True)
R.write_stl(out, V, T)
print("WROTE", out, flush=True)
# collapsed
m = Mesh.Mesh(out)
print("in: facets %d solid %s nonmanifold %s selfint-pairs %d vol %.1f" % (m.CountFacets, m.isSolid(), m.hasNonManifolds(), len(m.getSelfIntersections()), m.Volume), flush=True)
# recorded
SI_PLACED = None
try:
    _si0 = m.getSelfIntersections()
    _seam_p = os.path.join(os.path.dirname(os.path.abspath(src)), "keep_seam.npy")
    if _si0 and len(T) == m.CountFacets and os.path.exists(_seam_p):
        _seam = np.load(_seam_p)
        _ctr = V[T[np.array([int(p[0]) for p in _si0])]].mean(axis=1)
        if len(_seam):
            from scipy.spatial import cKDTree as _KD
            _d = _KD(np.asarray(_seam, float)).query(_ctr)[0]
            _near = int((_d < 0.5).sum()); _mid = int(((_d >= 0.5) & (_d < 2.0)).sum()); _far = int((_d >= 2.0).sum())
            print("self-intersections on the KEEP result: %d pair(s) - %d at the seam (< 0.5 mm), %d within 2 mm, %d elsewhere" % (len(_si0), _near, _mid, _far), flush=True)
            _o = np.argsort(_d); _rows = []
            for _i in list(_o[:8]) + list(_o[-4:][::-1]): _rows.append({"at": [round(float(v), 2) for v in _ctr[_i]], "seam_mm": round(float(_d[_i]), 3)})
            for _r in _rows[:12]: print("    pair at (%.1f, %.1f, %.1f), %.2f mm from the seam" % (_r["at"][0], _r["at"][1], _r["at"][2], _r["seam_mm"]), flush=True)
            SI_PLACED = {"pairs": int(len(_si0)), "at_seam": _near, "within_2mm": _mid, "elsewhere": _far, "placed": _rows, "seam_points": int(len(_seam))}
        else: SI_PLACED = {"pairs": int(len(_si0)), "seam_points": 0}
    elif _si0:
        print("self-intersections on the KEEP result: %d pair(s) (no seam record to place them against)" % len(_si0), flush=True)
        SI_PLACED = {"pairs": int(len(_si0)), "seam_points": 0}
except Exception as _ex: print("self-intersection placement skipped: %r" % (_ex,), flush=True)
m.removeDuplicatedPoints(); m.removeDuplicatedFacets()
REPAIR_ROUNDS = int(os.environ.get("REPAIR_ROUNDS", "12")); _last = None
for rnd in range(REPAIR_ROUNDS):
    if m.hasNonManifolds():
        m.removeNonManifolds(); m.fillupHoles(50); m.fixIndices()
    if not m.isSolid():                               # open edges
        m.fillupHoles(50); m.fixIndices()
    si = m.getSelfIntersections()
    print("round %d: facets %d solid %s nonmanifold %s selfint-pairs %d vol %.1f" % (rnd, m.CountFacets, m.isSolid(), m.hasNonManifolds(), len(si), m.Volume), flush=True)
    if not si and m.isSolid(): break
    if _last is not None and len(si) >= _last: print("  self-intersections no longer falling (%d) - stopping" % len(si), flush=True); break
    _last = len(si)
    if si:
        idx = sorted(set(int(t[0]) if m.Facets[int(t[0])].Area <= m.Facets[int(t[1])].Area else int(t[1]) for t in si))
        try: m.collapseFacets(idx); m.fillupHoles(50); m.fixIndices()
        except Exception as ex: print("collapseFacets failed:", ex); break
def _fan_fill(m):
    tmp = os.path.join(os.path.dirname(os.path.abspath(out)), "_tmp_fan.stl"); m.write(tmp)
    rd_ = R.read_stl(tmp); Vf, Tf = np.asarray(rd_[0], float), np.asarray(rd_[1], int)
    k_ = np.round(Vf / 1e-5).astype(np.int64); _, ui2, inv2 = np.unique(k_, axis=0, return_index=True, return_inverse=True); inv2 = inv2.reshape(-1); Vf = Vf[ui2]; Tf = inv2[Tf]
    added = 0
    for _r in range(5):
        dirs = {}
        for t in Tf:
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])): dirs[(int(a), int(b))] = 1
        opens = [(a, b) for (a, b) in dirs if (b, a) not in dirs]
        if not opens: break
        nxt = {a: b for a, b in opens}; used = set(); new = []
        for a, b in opens:
            if (a, b) in used: continue
            loop = [a]; cur = b; used.add((a, b))
            while cur != a and cur in nxt and len(loop) < 200:
                loop.append(cur); nx = nxt[cur]; used.add((cur, nx)); cur = nx
            if cur != a: continue
            for i in range(1, len(loop) - 1): new.append([loop[0], loop[i + 1], loop[i]])
        if not new: break
        Tf = np.vstack([Tf, np.array(new, int)]); added += len(new)
    if added: R.write_stl(tmp, Vf, Tf); m2 = Mesh.Mesh(tmp); return m2, added
    return m, 0
if not m.isSolid():
    m, _added = _fan_fill(m)
    print("  fan fill of the holes FreeCAD's removal left: %d triangle(s) added -> solid %s selfint-pairs %d" % (_added, m.isSolid(), len(m.getSelfIntersections())), flush=True)
    for rnd in range(3):
        si = m.getSelfIntersections()
        if not si: break
        idx = sorted(set(int(t[0]) if m.Facets[int(t[0])].Area <= m.Facets[int(t[1])].Area else int(t[1]) for t in si))
        try: m.collapseFacets(idx); m.fillupHoles(50); m.fixIndices()
        except Exception as ex: print("collapseFacets failed:", ex); break
        if not m.isSolid(): m, _a2 = _fan_fill(m)
        print("  after the fill, round %d: facets %d solid %s selfint-pairs %d" % (rnd, m.CountFacets, m.isSolid(), len(m.getSelfIntersections())), flush=True)
CLOSE_ROUNDS = int(os.environ.get("CLOSE_ROUNDS", "8"))
def _score(mm):
    si_ = len(mm.getSelfIntersections()); nm_ = bool(mm.hasNonManifolds()); sol_ = bool(mm.isSolid())
    return (0 if (sol_ and not nm_ and si_ == 0) else 1, int(nm_), si_, 0 if sol_ else 1)
def _nm_where(mm, n=4):
    """the places of the first n non-manifold edges (an edge on three or more facets), from the mesh's own topology - FreeCAD
    1.1.3's MeshObject has no getNonManifolds (R4 run 14 E1: every closing line printed the AttributeError, 31ae's mistake)"""
    try:
        pts, fcs = mm.Topology
        if not fcs: return []
        Tn = np.asarray(fcs, int)
        E = np.sort(np.concatenate([Tn[:, [0, 1]], Tn[:, [1, 2]], Tn[:, [2, 0]]]), axis=1)
        u, cnt = np.unique(E, axis=0, return_counts=True); bad = u[cnt > 2]
        if not len(bad): return []
        P = np.asarray([[q.x, q.y, q.z] for q in pts], float) if hasattr(pts[0], "x") else np.asarray(pts, float)
        mids = 0.5 * (P[bad[:, 0]] + P[bad[:, 1]])
        out = [tuple(round(float(c), 1) for c in mids[i]) for i in range(min(n, len(mids)))]
        if len(mids) > n: out.append("... %d in all" % len(mids))
        return out
    except Exception as _ex: return ["(%s)" % _ex]
best = m.copy(); best_s = _score(m); stale = 0
if best_s[0] != 0:
    print("  closing loop: start solid %s nonmanifold %s selfint %d%s" % (m.isSolid(), m.hasNonManifolds(), best_s[2], ("; non-manifold at %s" % _nm_where(m)) if best_s[1] else ""), flush=True)
for rnd in range(CLOSE_ROUNDS):
    if best_s[0] == 0: break
    if m.hasNonManifolds(): m.removeNonManifolds(); m.fillupHoles(50); m.fixIndices()
    if not m.isSolid(): m.fillupHoles(50); m.fixIndices()
    if not m.isSolid(): m, _a3 = _fan_fill(m)
    si = m.getSelfIntersections()
    if si:
        idx = sorted(set(int(t[0]) if m.Facets[int(t[0])].Area <= m.Facets[int(t[1])].Area else int(t[1]) for t in si))
        try: m.collapseFacets(idx); m.fillupHoles(50); m.fixIndices()
        except Exception as ex: print("collapseFacets failed:", ex)
    sc = _score(m)
    print("  closing round %d: solid %s nonmanifold %s selfint %d facets %d%s" % (rnd, m.isSolid(), m.hasNonManifolds(), sc[2], m.CountFacets, ("; non-manifold at %s" % _nm_where(m)) if sc[1] else ""), flush=True)
    if sc < best_s: best, best_s, stale = m.copy(), sc, 0
    else: stale += 1
    if stale >= 2: print("  closing loop: no improvement for 2 rounds - the best state is kept", flush=True); break
m = best
m.harmonizeNormals()
print("out: facets %d solid %s nonmanifold %s selfint-pairs %d vol %.1f" % (m.CountFacets, m.isSolid(), m.hasNonManifolds(), len(m.getSelfIntersections()), m.Volume), flush=True)
m.write(out); _si = len(m.getSelfIntersections()); _ok = bool(m.isSolid()) and not m.hasNonManifolds() and _si == 0
print("FINAL mesh -> %s: facets %d solid %s nonmanifold %s selfint %d vol %.1f" % (out, m.CountFacets, m.isSolid(), m.hasNonManifolds(), _si, m.Volume), flush=True)
# INTERNAL
# INTERNAL
INTERNAL_MAX = float(os.environ.get("INTERNAL_MAX", "0.5")); _icl_final = []
if _ok and (os.path.basename(out).startswith("arr_") or os.environ.get("INTERNAL_GATE") == "1"):
    try:
        _rdF = R.read_stl(out); _VF, _TF = np.asarray(_rdF[0], float), np.asarray(_rdF[1], int)
        _kF = np.round(_VF / 1e-5).astype(np.int64); _, _uF, _iF = np.unique(_kF, axis=0, return_index=True, return_inverse=True); _VF = _VF[_uF]; _TF = _iF.reshape(-1)[_TF]
        _, _icl_final = R.internal_triangles(_VF, _TF)
        _big = [c for c in _icl_final if c["area_mm2"] >= INTERNAL_MAX]
        print("inside check (a triangle with material on both sides): %d place(s)%s" % (len(_icl_final), (" - " + "; ".join("%.3f mm2 at %s" % (c["area_mm2"], c["at"]) for c in _icl_final[:6])) if _icl_final else ""), flush=True)
        if _big:
            _ok = False
            print("REFUSED: %d buried sheet(s) of %.2f mm2 or more - a solid True mesh whose inside depends on the ray direction (R4 run 16's crown pit); the cause is upstream: stage M's internal faces for the base, the blend's join for a piece" % (len(_big), INTERNAL_MAX), flush=True)
    except Exception as _ex:
        print("inside check skipped: %r" % (_ex,), flush=True)
import json
json.dump({"tag": TAG, "source": os.environ["STL"], "out": out, "levers": {"SLIV": SLIV, "SLIV_A": SLIV_A, "PINCH": PINCH, "SLIT": SLIT}, "facets": int(m.CountFacets), "solid": bool(m.isSolid()), "nonmanifold": bool(m.hasNonManifolds()),
           "self_intersections": int(_si), "self_intersections_placed": SI_PLACED, "volume_mm3": round(float(m.Volume), 1), "passed": _ok, "internal_31aj": _icl_final},
          open(os.path.join(os.path.dirname(os.path.abspath(out)), "REBUILD_arrmesh.json" if os.path.basename(out).startswith("arr_") else "REBUILD_mesh.json"), "w"), indent=1)   # kit rebuild
if not _ok:
    _fail("FAIL: the mesh finish could not close %s - FINAL solid %s nonmanifold %s selfint %d%s (the output is not a result; the cause is upstream: for a piece the blend's RESULT health and keep-and-weld lines, for the arrangement's base stage M's face census and its internal faces)" % (os.path.basename(src), m.isSolid(), m.hasNonManifolds(), _si, (", buried sheets %d" % len([c for c in _icl_final if c["area_mm2"] >= INTERNAL_MAX])) if _icl_final else ""))

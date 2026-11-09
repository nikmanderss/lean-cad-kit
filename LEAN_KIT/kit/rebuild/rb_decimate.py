# kit rebuild
# does not exist
import os, sys, numpy as np, vtk
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
def _fail(m): print(m if str(m).startswith("FAIL") else "FAIL: " + str(m), flush=True); raise SystemExit(1)
TAG = os.environ.get("LK_TAG", "")
from vtk.util import numpy_support as nps
from scipy.spatial import cKDTree
sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
def _arg(name, i):
    v = os.environ.get(name)
    if v not in (None, ""): return v
    if len(sys.argv) > i and not sys.argv[i].lower().endswith(".py"): return sys.argv[i]
    _fail("rb_decimate: %s not set (env %s or argument %d)" % (name, name, i))
src, out, target = _arg("STL", 1), _arg("OUT", 2), float(_arg("REDUCTION", 3))
V, T = R.read_stl(src)[:2]; V = np.asarray(V, float); T = np.asarray(T, int)
key = np.round(V / 1e-5).astype(np.int64); _, ui, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1); V = V[ui]; T = inv[T]
DECIM_MODE = os.environ.get("DECIM", "quadric"); DECERR = float(os.environ.get("DECERR", "0.1"))
BAND = float(os.environ.get("BAND", "0"))
ACCUM = os.environ.get("ACCUM", "0") == "1"
VOLPRES = os.environ.get("VOLPRES", "1") == "1"
DEC_SNAPBACK = float(os.environ.get("DEC_SNAPBACK", "0"))
import json
_recp = os.path.join(os.path.dirname(os.path.abspath(out)), "REBUILD_blend.json")
try: _rec = json.load(open(_recp, encoding="utf-8"))
except (OSError, ValueError): _rec = None
_walls = [(np.array(w[:3], float), np.array(w[3:], float) / max(np.linalg.norm(w[3:]), 1e-12)) for w in ((_rec or {}).get("walls") or []) if len(w) == 6]
_protect = [[float(v) for v in b] for b in ((_rec or {}).get("protect") or []) if len(b) == 6]
_clip_out = float(((_rec or {}).get("levers") or {}).get("CLIP_OUT", 0.0))
def _near_walls(P, band):
    """distance of every point to the nearest wall plane (the cap plane = the wall shifted CLIP_OUT outward) and to the nearest PROTECT box (0 inside)"""
    dw = np.full(len(P), np.inf)
    for c, n in _walls: dw = np.minimum(dw, np.abs((P - (c + n * _clip_out)) @ n))
    db = np.full(len(P), np.inf)
    for b in _protect:
        dx = np.maximum(np.maximum(b[0] - P[:, 0], P[:, 0] - b[1]), 0.0); dy = np.maximum(np.maximum(b[2] - P[:, 1], P[:, 1] - b[3]), 0.0); dz = np.maximum(np.maximum(b[4] - P[:, 2], P[:, 2] - b[5]), 0.0)
        db = np.minimum(db, np.sqrt(dx * dx + dy * dy + dz * dz))
    return dw, db
def _pd(Vx, Tx):
    pd = vtk.vtkPolyData(); pts = vtk.vtkPoints(); pts.SetData(nps.numpy_to_vtk(np.ascontiguousarray(Vx), deep=True)); pd.SetPoints(pts)
    cells = vtk.vtkCellArray(); conn = np.hstack([np.full((len(Tx), 1), 3), Tx]).astype(np.int64).ravel(); cells.SetCells(len(Tx), nps.numpy_to_vtkIdTypeArray(conn, deep=True)); pd.SetPolys(cells); return pd
def _np(o):
    V2 = nps.vtk_to_numpy(o.GetPoints().GetData()).astype(float); c = nps.vtk_to_numpy(o.GetPolys().GetData()).reshape(-1, 4)[:, 1:]; return V2, c
def _health(Vx, Tx):
    e = np.vstack([Tx[:, [0, 1]], Tx[:, [1, 2]], Tx[:, [2, 0]]]); s = np.sort(e, 1); u, c = np.unique(s, axis=0, return_counts=True)
    return int((c == 1).sum()), int((c > 2).sum()), u[c > 2]
def _dups(Tx):
    s = np.sort(Tx, axis=1); _, c = np.unique(s, axis=0, return_counts=True); return int((c > 1).sum())
def _decimate(Vx, Tx, mode, open_mesh):
    """one decimator call; returns V, T (welded at 1e-5, degenerates dropped) + the raw non-manifold census BEFORE the weld"""
    pd = _pd(Vx, Tx)
    if mode == "quadric":
        dec = vtk.vtkQuadricDecimation(); dec.SetInputData(pd); dec.SetTargetReduction(target); dec.SetVolumePreservation(1 if VOLPRES else 0); dec.Update()
    else:
        dec = vtk.vtkDecimatePro(); dec.SetInputData(pd); dec.SetTargetReduction(target)
        dec.BoundaryVertexDeletionOff(); dec.PreserveTopologyOn(); dec.SetFeatureAngle(35.0); dec.SplittingOff()
        dec.SetErrorIsAbsolute(1); dec.SetAbsoluteError(DECERR)
        if ACCUM: dec.AccumulateErrorOn()
        dec.Update()
    V2, c = _np(dec.GetOutput()); Vraw = V2.copy()
    raw_open, raw_nm, raw_nm_edges = _health(V2, c[(c[:, 0] != c[:, 1]) & (c[:, 1] != c[:, 2]) & (c[:, 0] != c[:, 2])]); raw_dups = _dups(c)
    key = np.round(V2 / 1e-5).astype(np.int64); _, ui, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1); V2 = V2[ui]; T2 = inv[c]
    T2 = T2[(T2[:, 0] != T2[:, 1]) & (T2[:, 1] != T2[:, 2]) & (T2[:, 0] != T2[:, 2])]
    _, uu = np.unique(np.sort(T2, axis=1), axis=0, return_index=True); T2 = T2[np.sort(uu)]
    if mode != "quadric":
        print("  %s raw output: %d triangles, open %d, non-manifold %d edge(s), duplicate triangles %d (before the 1e-5 weld; the mesh %s)" % (mode, len(c), raw_open, raw_nm, raw_dups, "is open on purpose (the band's rim)" if open_mesh else "was closed"), flush=True)
        if raw_nm:
            print("    non-manifold edges at: %s" % [tuple(np.round(0.5 * (Vraw[e[0]] + Vraw[e[1]]), 2)) for e in raw_nm_edges[:8]], flush=True)
    return V2, T2
if BAND > 0 and (_walls or _protect):
    dw, db = _near_walls(V, BAND); near = (dw <= BAND) | (db <= BAND)
    band_t = near[T].any(axis=1); Tb = T[band_t]; Ti = T[~band_t]
    mode = DECIM_MODE
    if mode == "quadric":
        print("BAND %.2f with DECIM=quadric: the quadric moves the interior's rim off the band's (no vertex lock) - the interior is decimated by DecimatePro instead (BoundaryVertexDeletionOff keeps the shared rim vertex for vertex)" % BAND, flush=True); mode = "pro"
    print("BAND %.2f mm round %d wall plane(s) and %d PROTECT box(es): %d triangles kept exact, %d decimated (%s)" % (BAND, len(_walls), len(_protect), len(Tb), len(Ti), mode), flush=True)
    V2i, T2i = _decimate(V, Ti, mode, open_mesh=True)
    V2 = np.vstack([V, V2i]); T2 = np.vstack([Tb, T2i + len(V)])
    key = np.round(V2 / 1e-9).astype(np.int64); _, ui, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1); V2 = V2[ui]; T2 = inv[T2]
    T2 = T2[(T2[:, 0] != T2[:, 1]) & (T2[:, 1] != T2[:, 2]) & (T2[:, 0] != T2[:, 2])]
    used = np.unique(T2); remap = -np.ones(len(V2), np.int64); remap[used] = np.arange(len(used)); V2 = V2[used]; T2 = remap[T2]
    ho, hn, _ = _health(V2, T2)
    print("  band re-attached: %d triangles, health (open %d, non-manifold %d)%s" % (len(T2), ho, hn, "" if (ho, hn) == (0, 0) else "   <-- the rim did not re-attach vertex for vertex: a decimator moved or deleted a rim vertex"), flush=True)
    DECIM_USED = mode + "+band"
else:
    V2, T2 = _decimate(V, T, DECIM_MODE, open_mesh=False); DECIM_USED = DECIM_MODE; Tb = np.zeros((0, 3), int)
if DEC_SNAPBACK > 0:
    _ipd = vtk.vtkImplicitPolyDataDistance(); _ipd.SetInput(_pd(V, T)); _cp = [0.0, 0.0, 0.0]
    _order = np.argsort(T2.ravel()); _vidx = T2.ravel()[_order]; _tidx = np.repeat(np.arange(len(T2)), 3)[_order]; _starts = np.searchsorted(_vidx, np.arange(len(V2) + 1))
    _moved = _refused = 0; _mv = []
    for i in range(len(V2)):
        d = _ipd.EvaluateFunctionAndGetClosestPoint(V2[i], _cp)
        if abs(d) < 1e-6 or abs(d) > DEC_SNAPBACK: continue
        q = np.array(_cp); tl = _tidx[_starts[i]:_starts[i + 1]]
        P0 = V2[T2[tl]]; n0 = np.cross(P0[:, 1] - P0[:, 0], P0[:, 2] - P0[:, 0]); old_ = V2[i].copy(); V2[i] = q
        P1 = V2[T2[tl]]; n1 = np.cross(P1[:, 1] - P1[:, 0], P1[:, 2] - P1[:, 0])
        if np.any(np.einsum("ij,ij->i", n0, n1) <= 0.0) or np.any(np.linalg.norm(n1, axis=1) < 0.05 * np.maximum(np.linalg.norm(n0, axis=1), 1e-12)): V2[i] = old_; _refused += 1
        else: _moved += 1; _mv.append(abs(d))
    print("snap-back %.2f: %d vertices walked back onto the input surface (p50 %.3f, max %.3f mm), %d refused (a triangle would fold)" % (DEC_SNAPBACK, _moved, np.median(_mv) if _mv else 0, max(_mv) if _mv else 0, _refused), flush=True)
FEAT = os.environ.get("FEAT", "0") == "1"; FEAT_REC = []
if FEAT:
    _base = (_rec or {}).get("source", "")
    if not _rec or not os.path.isfile(_base):
        print("feature restore: SKIPPED - %s (the blend's record and base are needed: %s)" % ("no REBUILD_blend.json beside the output" if not _rec else "the blend's base is missing", _base), flush=True)
    else:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _feat
        VB, TB = R.read_stl(_base)[:2]; VB = np.asarray(VB, float); TB = np.asarray(TB, int)
        kb = np.round(VB / 1e-5).astype(np.int64); _, ub, ib = np.unique(kb, axis=0, return_index=True, return_inverse=True); ib = ib.reshape(-1); VB = VB[ub]; TB = ib[TB]
        ipd = vtk.vtkImplicitPolyDataDistance(); ipd.SetInput(_pd(VB, TB))
        _lv = _rec.get("levers") or {}; _h = float(_lv.get("h", 0.2))
        _planes = [(w[:3], w[3:]) for w in (_rec.get("walls") or []) if len(w) == 6]
        V2, T2, FEAT_REC = _feat.run_all(V2, T2, VB, TB, ipd, _h, say=lambda *a: print(*a, flush=True), deg=float(_lv.get("EDGE_DEG", 25)),
                                         reach=float(os.environ.get("FEAT_REACH", _lv.get("FEAT_REACH", 3.0 * _h))), depth=float(os.environ.get("FEAT_DEPTH", _lv.get("FEAT_DEPTH", 2.0 * _h))),
                                         snap=max(float(_lv.get("SNAP", 0.03)), 0.03), planes=_planes, protect=_rec.get("protect") or [])
def dense(V_, T_, s):
    A, B, C = V_[T_[:, 0]], V_[T_[:, 1]], V_[T_[:, 2]]
    L = np.maximum(np.maximum(np.linalg.norm(B - A, axis=1), np.linalg.norm(C - B, axis=1)), np.linalg.norm(A - C, axis=1))
    n = np.maximum(1, np.ceil(L / s).astype(int)); outp = []
    for k in np.unique(n):
        m = n == k; ij = np.array([(i, j) for i in range(k + 1) for j in range(k + 1 - i)], float) / k
        P = A[m][:, None, :] + (B[m] - A[m])[:, None, :] * ij[None, :, 0:1] + (C[m] - A[m])[:, None, :] * ij[None, :, 1:2]
        outp.append(P.reshape(-1, 3))
    return np.vstack(outp)
d1, _ = cKDTree(dense(V, T, 0.1)).query(V2, workers=-1)
d2, _ = cKDTree(dense(V2, T2, 0.1)).query(V, workers=-1)
vol = abs(np.einsum("ij,ij->i", V2[T2[:, 0]], np.cross(V2[T2[:, 1]], V2[T2[:, 2]])).sum() / 6.0)
print("decimated %d -> %d triangles; dev new->old p99 %.3f max %.3f; old->new p99 %.3f max %.3f; volume %.1f; health %s" % (len(T), len(T2), np.percentile(d1, 99), d1.max(), np.percentile(d2, 99), d2.max(), vol, R.mesh_health(V2, T2)), flush=True)
_worst = np.argsort(-d2)[:5]; print("  largest old->new moves at: %s" % [(tuple(np.round(V[i], 1)), round(float(d2[i]), 3)) for i in _worst], flush=True)
ZONES = {}
if _walls or _protect:
    dw, db = _near_walls(V, 2.0)
    for k, b in enumerate(_protect):
        m = (V[:, 0] >= b[0]) & (V[:, 0] <= b[1]) & (V[:, 1] >= b[2]) & (V[:, 1] <= b[3]) & (V[:, 2] >= b[4]) & (V[:, 2] <= b[5])
        if m.sum(): ZONES["protect_%d" % k] = (int(m.sum()), round(float(np.percentile(d2[m], 99)), 3), round(float(d2[m].max()), 3))
    m = dw <= 2.0
    if m.sum(): ZONES["walls_2mm"] = (int(m.sum()), round(float(np.percentile(d2[m], 99)), 3), round(float(d2[m].max()), 3))
    print("  old->new INSIDE the PROTECT boxes and within 2 mm of the walls (n, p99, max): %s   <-- the deviation STEP 4's seam census sees; under 0.15 or the seam will not pass" % ZONES, flush=True)
json.dump({"tag": TAG, "source": src, "out": out, "reduction": target, "decimator": DECIM_USED, "dec_error_cap": DECERR, "band_mm": BAND, "band_triangles": int(len(Tb)), "accumulate_error": ACCUM, "volume_preservation": VOLPRES, "snapback_mm": DEC_SNAPBACK, "triangles_in": int(len(T)), "triangles_out": int(len(T2)), "dev_new_to_old_p99": round(float(np.percentile(d1, 99)), 4), "dev_new_to_old_max": round(float(d1.max()), 4),
           "dev_old_to_new_p99": round(float(np.percentile(d2, 99)), 4), "dev_old_to_new_max": round(float(d2.max()), 4), "volume_mm3": round(float(vol), 1), "health_open_nonmanifold": [int(x) for x in R.mesh_health(V2, T2)],
           "zones_old_to_new": ZONES, "feature_restore": FEAT_REC},
          open(os.path.join(os.path.dirname(os.path.abspath(out)), "REBUILD_decimate.json"), "w"), indent=1)
R.write_stl(out, V2, T2)

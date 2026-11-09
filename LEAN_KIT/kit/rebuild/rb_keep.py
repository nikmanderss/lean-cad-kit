# kit rebuild
# content.brep
# kit rebuild
import os, sys, json, time, numpy as np, Part, FreeCAD
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
def _fail(m): print(m if str(m).startswith("FAIL") else "FAIL: " + str(m), flush=True); raise SystemExit(1)
TAG = os.environ.get("LK_TAG", "")
sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _keepgrid as KG
import vtk
from vtk.util import numpy_support as nps
from scipy.spatial import cKDTree
V3 = FreeCAD.Vector; T0 = time.time()
def say(*a): print("%5.0fs " % (time.time() - T0), *a, flush=True)
RUN = os.environ.get("RUN") or _fail("RUN not set")
def P(n): return os.path.join(RUN, n)
PIECE = os.environ.get("PIECE", P("piece.brep")); ORIG = os.environ.get("ORIG", P("content.brep")); WINDOW = os.environ.get("WINDOW", P("window_solid.brep"))
for f in (PIECE, ORIG, WINDOW):
    if not os.path.isfile(f): _fail("FAIL: %s is missing - kit rebuild brep / region make it" % f)
TOL = float(os.environ.get("KEEP_TOL", "0.1")); CELL = float(os.environ.get("KEEP_CELL", "2.0")); SAMP = float(os.environ.get("KEEP_SAMP", "0.15"))
DEV = float(os.environ.get("KEEP_DEV", "0.02")); FROZEN_TOL = float(os.environ.get("FROZEN_TOL", "0.15")); IN_CONTENT = float(os.environ.get("IN_CONTENT", "0.9"))
OUT_DIR = os.environ.get("OUT_DIR") or P("keep"); os.makedirs(OUT_DIR, exist_ok=True)
pr = os.environ.get("PROTECT")
if pr is None:
    try: pr = ";".join(" ".join("%g" % v for v in b) for b in json.load(open(P("REBUILD_blend.json"))).get("protect", []))
    except (OSError, ValueError): pr = ""
PROTECT = [[float(v) for v in b.split()] for b in pr.split(";") if b.strip()]
for b in PROTECT:
    if len(b) != 6: _fail("FAIL: PROTECT box needs six numbers x0 x1 y0 y1 z0 z1, got %r" % b)
FROZEN = []
if os.environ.get("FROZEN"):
    try: FROZEN = json.load(open(os.environ["FROZEN"]))
    except (OSError, ValueError) as ex: _fail("FAIL: FROZEN %s could not be read (%s)" % (os.environ["FROZEN"], ex))

ws = Part.Shape(); ws.importBrep(WINDOW); window = ws.Solids[0]
HS = []
for f in window.Faces:
    if type(f.Surface).__name__ != "Plane": _fail("FAIL: the window has a non-planar face - rb_region writes a box cut by planes")
    c = f.CenterOfMass; n = f.normalAt(*f.Surface.parameter(c))
    HS.append((np.array([c.x, c.y, c.z]), np.array([n.x, n.y, n.z]) / max(n.Length, 1e-12)))
def in_window(X, tol=1e-4):
    m = np.ones(len(X), bool)
    for c, n in HS: m &= ((X - c) @ n) <= tol
    return m
ct = Part.Shape(); ct.importBrep(ORIG); csols = sorted(ct.Solids, key=lambda s: -s.Volume); cmain = csols[0]; leftovers = csols[1:]
pc = Part.Shape(); pc.importBrep(PIECE); pieces = sorted([s for s in pc.Solids if abs(s.Volume) >= 0.5], key=lambda s: -abs(s.Volume))
if not pieces: _fail("FAIL: %s holds no solid" % PIECE)
keep_p = [pieces[0]]; dropped_c = []
for s in pieces[1:]:
    try: fr = s.common(cmain).Volume / abs(s.Volume)
    except Exception: fr = -1.0
    if fr >= IN_CONTENT: keep_p.append(s)
    else: dropped_c.append(round(abs(s.Volume), 2))
pieces = keep_p
say("piece: %d solid(s) %.1f mm3 (%d detached component(s) not the original's: %s); original: %d solid(s) %.1f mm3; window %.1f mm3"
    % (len(pieces), sum(abs(s.Volume) for s in pieces), len(dropped_c), dropped_c, len(csols), sum(s.Volume for s in csols), window.Volume))

def tess(shapes, dev):
    Vs, Ts, off = [], [], 0
    for s in shapes:
        V, T, _ = R.tess_shape(s, dev=dev); Vs.append(V); Ts.append(T + off); off += len(V)
    return np.vstack(Vs), np.vstack(Ts)
VO, TO = tess(csols, DEV)
VN, TN = tess(pieces + leftovers, DEV)
say("tessellated: original %d triangles, new %d" % (len(TO), len(TN)))
def on_any_plane(V, T, tol=1e-3):
    m = np.zeros(len(T), bool)
    for c, n in HS: m |= np.all(np.abs((V[T] - c) @ n) < tol, axis=1)
    return m
TOs = TO[~on_any_plane(VO, TO)]
def dense(V, T, s, normals=False):
    """surface samples at most s apart; with normals=True also the unit normal of the triangle each sample lies on"""
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    L = np.maximum(np.maximum(np.linalg.norm(B - A, axis=1), np.linalg.norm(C - B, axis=1)), np.linalg.norm(A - C, axis=1))
    k = np.maximum(1, np.ceil(L / s).astype(int)); out = []; outn = []
    nrm = np.cross(B - A, C - A); nrm /= np.maximum(np.linalg.norm(nrm, axis=1), 1e-12)[:, None]
    for kk in np.unique(k):
        m = k == kk; ij = np.array([(i, j) for i in range(kk + 1) for j in range(kk + 1 - i)], float) / kk
        pts = (A[m][:, None, :] + (B[m] - A[m])[:, None, :] * ij[None, :, 0:1] + (C[m] - A[m])[:, None, :] * ij[None, :, 1:2])
        out.append(pts.reshape(-1, 3))
        if normals: outn.append(np.repeat(nrm[m], len(ij), axis=0))
    X = np.vstack(out) if out else np.zeros((0, 3))
    return (X, np.vstack(outn) if outn else np.zeros((0, 3))) if normals else X
SO, NO = dense(VO, TOs, SAMP, normals=True); wO = in_window(SO); SO, NO = SO[wO], NO[wO]
SN = dense(VN, TN, SAMP); SN = SN[in_window(SN, tol=-1e-4)]
def polydata(V, T):
    pd = vtk.vtkPolyData(); pts = vtk.vtkPoints(); pts.SetData(nps.numpy_to_vtk(np.ascontiguousarray(V, dtype=float), deep=True)); pd.SetPoints(pts)
    ca = vtk.vtkCellArray(); conn = np.hstack([np.full((len(T), 1), 3), T]).astype(np.int64).ravel(); ca.SetCells(len(T), nps.numpy_to_vtkIdTypeArray(conn, deep=True)); pd.SetPolys(ca)
    return pd
def dist_to(V, T, X):
    """unsigned distance from every point of X to the triangle mesh (V, T) - exact, VTK's point-to-triangle"""
    if not len(X): return np.zeros(0)
    ipd = vtk.vtkImplicitPolyDataDistance(); ipd.SetInput(polydata(V, T))
    xin = nps.numpy_to_vtk(np.ascontiguousarray(X, dtype=float), deep=True); out = vtk.vtkDoubleArray()
    ipd.FunctionValue(xin, out)
    return np.abs(nps.vtk_to_numpy(out))
dO = dist_to(VN, TN, SO)
dN = dist_to(VO, TOs, SN)
say("surface samples: original %d (%.2f %% further than %.2f mm from the new surface, max %.3f), new %d (%.2f %%, max %.3f)"
    % (len(SO), 100.0 * (dO > TOL).mean() if len(dO) else 0, TOL, dO.max() if len(dO) else 0, len(SN), 100.0 * (dN > TOL).mean() if len(dN) else 0, dN.max() if len(dN) else 0))

# over the
bbw = window.BoundBox; lo = np.array([bbw.XMin, bbw.YMin, bbw.ZMin]); hi = np.array([bbw.XMax, bbw.YMax, bbw.ZMax])
try: _extra = [float(v) for v in os.environ.get("KEEP_OFFSET", "0 0 0").split()]
except ValueError: _fail("FAIL: KEEP_OFFSET takes three numbers dx dy dz (mm), got %r" % os.environ.get("KEEP_OFFSET"))
if len(_extra) != 3: _fail("FAIL: KEEP_OFFSET takes three numbers dx dy dz (mm), got %r" % os.environ.get("KEEP_OFFSET"))
CLEAR = float(os.environ.get("KEEP_CLEAR", "0.3"))
g0, grid_rep = KG.choose_offsets(lo, CELL, SO, NO, ax_deg=20.0, clear=CLEAR, k=40, extra=_extra)
nb = np.ceil((hi - g0) / CELL).astype(int) + 1
say("bins: %d x %d x %d of %.1f mm; the grid planes kept off the skins that run along them: %s%s" % (nb[0], nb[1], nb[2], CELL,
    "; ".join("%s %d of %d near-parallel samples within %.2f mm of a plane (clearance %.2f)" % ("xyz"[a], r["within_clear"], r["near_parallel"], CLEAR, r["clearance"]) for a, r in enumerate(grid_rep)),
    ("; moved by hand KEEP_OFFSET %s" % _extra) if any(abs(v) > 0 for v in _extra) else ""))
def bin_of(X):
    return np.clip(np.floor((X - g0) / CELL).astype(int), 0, nb - 1)
changed = np.zeros(nb, bool); why = np.zeros(nb, np.int8)
for X, d in ((SO, dO), (SN, dN)):
    m = d > TOL
    if m.any():
        ii = bin_of(X[m]); changed[ii[:, 0], ii[:, 1], ii[:, 2]] = True; why[ii[:, 0], ii[:, 1], ii[:, 2]] = 1
n_surf = int(changed.sum())
H = CELL / 3.0; gs0 = g0 + H / 2.0; ns = nb * 3
occO, _ = R.inside_vote(VO, TO, gs0, ns, H)
occN, _ = R.inside_vote(VN, TN, gs0, ns, H)
def occ_at(occ, X):
    """the sub-grid's occupancy at the points X (nearest cell; outside the grid = air)"""
    I = np.floor((X - gs0) / H + 0.5).astype(int)
    ok = np.all((I >= 0) & (I < ns), axis=1); out = np.zeros(len(X), bool)
    out[ok] = occ[I[ok, 0], I[ok, 1], I[ok, 2]]; return out
internalO = occ_at(occO, SO + NO * H) & occ_at(occO, SO - NO * H)
lam_bins = np.zeros(nb, bool)
m = (dO > TOL) & internalO
if m.any():
    ii = bin_of(SO[m]); lam_bins[ii[:, 0], ii[:, 1], ii[:, 2]] = True
vis = np.zeros(nb, bool)
for X, d in ((SO[~internalO], dO[~internalO]), (SN, dN)):
    m = d > TOL
    if m.any():
        ii = bin_of(X[m]); vis[ii[:, 0], ii[:, 1], ii[:, 2]] = True
flip = occO != occN
if flip.any():
    I = np.argwhere(flip); X = gs0 + I * H
    win = in_window(X); I, X = I[win], X[win]
    if len(X):
        kd = cKDTree(np.vstack([SO, SN])); dd, _ = kd.query(X, workers=-1)
        far = dd > TOL + SAMP
        bi = (I[far] // 3)
        changed[bi[:, 0], bi[:, 1], bi[:, 2]] = True; why[bi[:, 0], bi[:, 1], bi[:, 2]] |= 2
        say("material: %d sub-grid point(s) flip air/solid; %d of them further than %.2f mm from both surfaces" % (len(X), int(far.sum()), TOL + SAMP))
lam_only = changed & ~vis & ~(why == 2) & lam_bins
say("CHANGED bins: %d (%d by a surface moving, %d more by material flipping); %d of them only by a LAMINATION inside the material that the piece fills (%d %% of the original's surface samples are such laminations)"
    % (int(changed.sum()), n_surf, int(changed.sum()) - n_surf, int(lam_only.sum()), int(round(100.0 * internalO.mean())) if len(SO) else 0))

# ORIGINAL
ZONE_REP = {}
try:
    _wz = float(os.environ.get("WALL_ZONE", "1.5")); _vis = ~internalO
    _ab = P("arr_base.stl"); _hasA = os.path.isfile(_ab)
    if _hasA:
        _ra = R.read_stl(_ab); VA_, TA_ = np.asarray(_ra[0], float), np.asarray(_ra[1], int)
    _walls = []
    try: _walls = [w for w in json.load(open(P("walls.json"))) if len(w) == 6]
    except Exception: _walls = []
    def _zone(name, m):
        if m.sum() < 5: return
        r = {"n": int(m.sum()), "piece_p99": round(float(np.percentile(dO[m], 99)), 3), "piece_max": round(float(dO[m].max()), 3)}
        txt = "piece p99 %.3f max %.3f" % (r["piece_p99"], r["piece_max"])
        if _hasA:
            dA_ = dist_to(VA_, TA_, SO[m]); iw = int(np.argmax(dA_))
            r.update({"base_p99": round(float(np.percentile(dA_, 99)), 3), "base_max": round(float(dA_.max()), 3), "base_worst_at": [round(float(v), 1) for v in SO[m][iw]]})
            txt += "; BASE (arr_base) p99 %.3f max %.3f at %s" % (r["base_p99"], r["base_max"], r["base_worst_at"])
        ZONE_REP[name] = r; say("BASE vs ORIGINAL at %s: %d visible samples - %s%s" % (name, r["n"], txt, "   <-- over the seam ceiling: the base (the arrangement) is what STEP 4 will measure here" if r.get("base_max", 0) > 0.15 else ""))
    for k, w in enumerate(_walls):
        c = np.array(w[:3], float); n = np.array(w[3:], float); n /= max(np.linalg.norm(n), 1e-12)
        _zone("wall %d (n %s)" % (k, [round(float(v), 2) for v in n]), (np.abs((SO - c) @ n) <= _wz) & _vis)
    for k, b in enumerate(PROTECT):
        _zone("PROTECT box %d" % k, (SO[:, 0] >= b[0]) & (SO[:, 0] <= b[1]) & (SO[:, 1] >= b[2]) & (SO[:, 1] <= b[3]) & (SO[:, 2] >= b[4]) & (SO[:, 2] <= b[5]) & _vis)
except Exception as _ex: say("base-vs-original zones skipped: %r" % (_ex,))

forced = np.zeros(nb, bool); protect_rep = []
I = np.argwhere(np.ones(nb, bool)); blo = g0 + I * CELL; bhi = blo + CELL
for k, b in enumerate(PROTECT):
    hit = (blo[:, 0] < b[1]) & (bhi[:, 0] > b[0]) & (blo[:, 1] < b[3]) & (bhi[:, 1] > b[2]) & (blo[:, 2] < b[5]) & (bhi[:, 2] > b[4])
    J = I[hit]; was = int(changed[J[:, 0], J[:, 1], J[:, 2]].sum())
    inb = (SO[:, 0] >= b[0]) & (SO[:, 0] <= b[1]) & (SO[:, 1] >= b[2]) & (SO[:, 1] <= b[3]) & (SO[:, 2] >= b[4]) & (SO[:, 2] <= b[5]) & ~internalO
    dev_in = float(dO[inb].max()) if inb.any() else 0.0
    protect_rep.append({"box": b, "bins_met": int(hit.sum()), "bins_changed_by_the_piece": was, "piece_deviation_inside_mm": round(dev_in, 3)})
    say("PROTECT %s: cut out of the region exactly (the original stays to the box's face); the piece strays up to %.2f mm from the original inside it%s" % (b, dev_in, " - its blend did NOT keep the base there (PROTECT in the blend, a tight box): the step at the box face is that size" if dev_in > TOL else " (within the keep tolerance: no step at the box face)"))
frozen_rep = []
for fz in FROZEN:
    name = fz.get("name", "?"); sp = fz.get("surface", ""); bok = bool(fz.get("buried_ok"))
    if not sp or not os.path.isfile(sp):
        frozen_rep.append({"name": name, "error": "surface file missing: %s" % sp}); say("FROZEN %s: surface file missing (%s) - NOT CHECKED" % (name, sp)); continue
    fs_ = Part.Shape(); fs_.importBrep(sp)
    faces = [f for f in fs_.Faces if f.BoundBox.intersect(bbw)]
    if not faces:
        frozen_rep.append({"name": name, "faces_in_window": 0}); say("FROZEN %s: no face in the window" % name); continue
    ftol = float(fz.get("tol") or FROZEN_TOL)
    VF, TF = R.tess_shape(Part.makeCompound(faces), dev=DEV)[:2]
    SF, NF = dense(VF, TF, SAMP, normals=True); w = in_window(SF, tol=-1e-4); SF, NF = SF[w], NF[w]
    if not len(SF):
        frozen_rep.append({"name": name, "faces_in_window": 0}); say("FROZEN %s: no face in the window" % name); continue
    # ORIGINAL
    internal = occ_at(occO, SF + NF * H) & occ_at(occO, SF - NF * H)
    bi = bin_of(SF); inchg = changed[bi[:, 0], bi[:, 1], bi[:, 2]] & ~forced[bi[:, 0], bi[:, 1], bi[:, 2]] & ~internal
    dF = dist_to(VN, TN, SF[inchg]); off = dF > ftol
    cut = 0; buried = 0; recreated = int((~off).sum())
    if off.any():
        Xo = SF[inchg][off]
        ins = R.points_inside(Xo, VN, TN)
        cut_m = ~ins; bur_m = ins; cut = int(cut_m.sum()); buried = int(bur_m.sum())
        badm = cut_m | (bur_m & (not bok))
        if badm.any():
            bb2 = bin_of(Xo[badm]); forced[bb2[:, 0], bb2[:, 1], bb2[:, 2]] = True
    kept_exact = int((~inchg & ~internal).sum())
    frozen_rep.append({"name": name, "tol_mm": ftol, "samples": int(len(SF)), "internal_not_judged": int(internal.sum()), "in_kept_bins_exact": kept_exact, "in_changed_bins_recreated": recreated,
                       "cut_into": cut, "buried": buried, "buried_ok": bok})
    say("FROZEN %s: %d samples in the window (%d inside the body's own material on both sides: a lamination, not judged) - %d in KEPT bins (exact), %d recreated within %.2f mm in changed bins, %d BURIED%s, %d CUT INTO%s"
        % (name, len(SF), int(internal.sum()), kept_exact, recreated, ftol, buried, " (buried_ok)" if bok else (" -> those bins KEPT (no buried_ok)" if buried else ""), cut, " -> those bins KEPT" if cut else ""))
fchg = changed & forced
rebuild = changed & ~forced
SEAM_MAX = float(os.environ.get("SEAM_MAX", "0.15")); GROW = int(os.environ.get("KEEP_GROW", "3"))
grow_rep = []; bfaces = []; left = []
try:
    _vm = ~internalO; _VS, _VN, _Vd = SO[_vm], NO[_vm], dO[_vm]; _slab = max(0.3, 1.5 * SAMP)
    for _r in range(GROW):
        bfaces = KG.boundary_widths(rebuild, forced, g0, CELL, _VS, _VN, _Vd, slab=_slab)
        over = [e for e in bfaces if e["width"] > SEAM_MAX]
        if not over: break
        rebuild, _ng = KG.grow(rebuild, forced, over, SEAM_MAX)
        grow_rep.append({"round": _r + 1, "faces_over": len(over), "bins_grown": int(_ng), "widest_mm": round(over[0]["width"], 3), "widest_at": [round(v, 1) for v in over[0]["at"]]})
        say("cut check round %d: %d rebuilt|kept face(s) would leave a seam over %.2f mm (the widest %.2f at %s) - %d kept bin(s) behind them grown into the region" % (_r + 1, len(over), SEAM_MAX, over[0]["width"], [round(v, 1) for v in over[0]["at"]], _ng))
        if not _ng: break
    bfaces = KG.boundary_widths(rebuild, forced, g0, CELL, _VS, _VN, _Vd, slab=_slab)
    left = [e for e in bfaces if e["width"] > SEAM_MAX]
    say("CUTS: %d face(s) between rebuilt and kept bins carry samples; %d estimated over SEAM_MAX %.2f after %d growth round(s)%s" % (len(bfaces), len(left), SEAM_MAX, len(grow_rep),
        (" - the widest %.2f mm at %s (look at it in the orbit; a forced bin behind it, or KEEP_GROW spent: move the grid - KEEP_OFFSET - or the window's wall)" % (left[0]["width"], [round(v, 1) for v in left[0]["at"]])) if left else " - none left"))
except Exception as _ex:
    say("cut check skipped: %r" % (_ex,))

def _shift(a, sh, ax):
    o = np.zeros_like(a); src = [slice(None)] * 3; dst = [slice(None)] * 3
    if sh > 0: src[ax] = slice(0, -sh); dst[ax] = slice(sh, None)
    else: src[ax] = slice(-sh, None); dst[ax] = slice(0, sh)
    o[tuple(dst)] = a[tuple(src)]; return o
nbr = np.zeros(nb, bool)
for ax in range(3):
    for sh in (1, -1): nbr |= _shift(rebuild, sh, ax)
seam_through = fchg & nbr
step_mm = 0.0
if seam_through.any():
    bo = bin_of(SO); m = seam_through[bo[:, 0], bo[:, 1], bo[:, 2]] & ~internalO
    step_mm = float(dO[m].max()) if m.any() else 0.0
say("REBUILT bins: %d; FORCED KEPT where the piece had changed: %d, %d of them beside a rebuilt bin - the seam there crosses the piece's change (up to %.2f mm): STEP 4 measures the step; the cure is the piece (PROTECT in the blend, a moved wall)"
    % (int(rebuild.sum()), int(fchg.sum()), int(seam_through.sum()), step_mm))
np.savez_compressed(P("keep_bins.npz"), g0=g0, cell=CELL, nb=nb, changed=changed, forced=forced, rebuild=rebuild, why=why)

kr = P("keep_region.brep")
if os.path.isfile(kr): os.replace(kr, kr + ".stale")
rec = {"tag": TAG, "piece": PIECE, "orig": ORIG, "KEEP_TOL": TOL, "KEEP_CELL": CELL, "KEEP_SAMP": SAMP, "FROZEN_TOL": FROZEN_TOL,
       "grid": grid_rep, "keep_offset": _extra, "cut_growth": grow_rep, "cuts_over_seam_max_left": [{"width_mm": round(e["width"], 3), "at": [round(v, 1) for v in e["at"]], "axis": "xyz"[e["axis"]]} for e in left[:20]],
       "grid_origin": [float(v) for v in g0], "bins": [int(v) for v in nb], "changed": int(changed.sum()), "rebuilt": int(rebuild.sum()),
       "forced_kept": int(fchg.sum()), "forced_beside_rebuilt": int(seam_through.sum()), "seam_step_mm": round(step_mm, 3), "lamination_only_bins": int(lam_only.sum()),
       "lamination_share_of_orig_samples": round(float(internalO.mean()), 4) if len(SO) else 0.0, "protect": protect_rep, "frozen": frozen_rep, "base_vs_original_zones": ZONE_REP,
       "detached_components_dropped": dropped_c, "samples": {"orig": int(len(SO)), "new": int(len(SN))},
       "max_dev": {"orig_to_new": float(dO.max()) if len(dO) else 0.0, "new_to_orig": float(dN.max()) if len(dN) else 0.0}}
if not rebuild.any():
    rec.update({"region_mm3": 0.0, "verdict": "NOTHING CHANGED"})
    json.dump(rec, open(P("REBUILD_keep.json"), "w"), indent=1)
    print("KEEP: NOTHING CHANGED - every bin of the window reproduces the original within %.2f mm (or is forced kept); there is nothing to reinsert" % TOL, flush=True); raise SystemExit(0)
boxes = []
runs = {}
for i in range(nb[0]):
    for j in range(nb[1]):
        col = rebuild[i, j]; k = 0
        while k < nb[2]:
            if col[k]:
                k0 = k
                while k < nb[2] and col[k]: k += 1
                runs.setdefault((i, k0, k - 1), []).append(j)
            else: k += 1
rows = {}
for (i, k0, k1), js in runs.items():
    js = sorted(js); a = js[0]; prev = js[0]
    for j in js[1:] + [None]:
        if j is None or j != prev + 1:
            rows.setdefault((a, prev, k0, k1), []).append(i)
            if j is not None: a = j
        if j is not None: prev = j
for (j0, j1, k0, k1), is_ in rows.items():
    is_ = sorted(is_); a = is_[0]; prev = is_[0]
    for i in is_[1:] + [None]:
        if i is None or i != prev + 1:
            boxes.append((a, prev, j0, j1, k0, k1))
            if i is not None: a = i
        if i is not None: prev = i
say("rebuilt bins merged into %d box(es)" % len(boxes))
solids = []
for (i0, i1, j0, j1, k0, k1) in boxes:
    o = g0 + np.array([i0, j0, k0]) * CELL; e = (np.array([i1, j1, k1]) - np.array([i0, j0, k0]) + 1) * CELL
    solids.append(Part.makeBox(float(e[0]), float(e[1]), float(e[2]), V3(*[float(v) for v in o])))
U = solids[0] if len(solids) == 1 else solids[0].fuse(solids[1:])
try:
    U2 = U.removeSplitter()
    if U2.isValid() and abs(U2.Volume - U.Volume) < 1e-6 * max(U.Volume, 1.0): U = U2
except Exception: pass
reg = U.common(window)
for b in PROTECT:
    pb = Part.makeBox(b[1] - b[0], b[3] - b[2], b[5] - b[4], V3(b[0], b[2], b[4]))
    reg = reg.cut(pb)
rsol = [s for s in reg.Solids if s.Volume > 1e-6]
# ORIGINAL
keep_full = []; rsol2 = []
pmain = pieces[0] if len(pieces) == 1 else Part.makeCompound(pieces)
for c in rsol:
    try: vo = cmain.common(c).Volume; vp = sum(x.Volume for x in pmain.common(c).Solids)
    except Exception: vo = vp = -1.0
    if vo >= 0.999 * c.Volume:
        bbc = c.BoundBox; keep_full.append({"mm3": round(c.Volume, 2), "piece_fill": round(vp / c.Volume, 3) if vp >= 0 else None, "box": [round(v, 1) for v in (bbc.XMin, bbc.XMax, bbc.YMin, bbc.YMax, bbc.ZMin, bbc.ZMax)]})
        say("  region component %.1f mm3 lies INSIDE the original's material (the piece fills %.0f %% of it) - the original is kept there%s" % (c.Volume, 100.0 * vp / c.Volume if vp >= 0 else -1, "; THE PIECE HAS A VOID INSIDE THE BODY THERE (an arrangement cell dropped at a wall corner, SPIKE_V?) - a defect of the piece, not re-expressed" if 0 <= vp < 0.99 * c.Volume else " (a lamination it fills: nothing to re-express)"))
        continue
    rsol2.append(c)
rsol = rsol2
if not rsol: _fail("FAIL: the rebuilt bins do not meet the window (the region came out empty) - nothing written")
region = rsol[0] if len(rsol) == 1 else Part.makeCompound(rsol)
okv = all(s.isValid() for s in rsol)
region.exportBrep(kr)
inside = cmain.common(region).Volume
say("keep_region.brep: %d solid(s), %d faces, %.1f mm3 of the window's %.1f (%.0f %%), valid %s; the original's material inside it %.1f of %.1f mm3 (%.0f %% re-expressed, %.0f %% kept exactly)"
    % (len(rsol), sum(len(s.Faces) for s in rsol), sum(s.Volume for s in rsol), window.Volume, 100.0 * sum(s.Volume for s in rsol) / window.Volume, okv,
       inside, cmain.Volume, 100.0 * inside / max(cmain.Volume, 1e-9), 100.0 - 100.0 * inside / max(cmain.Volume, 1e-9)))
bo = bin_of(SO[~internalO]); kept_area = float((~rebuild[bo[:, 0], bo[:, 1], bo[:, 2]]).mean()) if len(bo) else 1.0
rec.update({"region_mm3": round(sum(s.Volume for s in rsol), 2), "region_solids": len(rsol), "region_faces": int(sum(len(s.Faces) for s in rsol)), "inside_material_kept": keep_full,
            "region_valid": bool(okv), "orig_in_region_mm3": round(inside, 2), "orig_surface_kept_exact": round(kept_area, 4), "boxes": len(boxes)})
json.dump(rec, open(P("REBUILD_keep.json"), "w"), indent=1)
def subdivide(V, T, lmax, depth=4):
    for _ in range(depth):
        A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        L = np.maximum(np.maximum(np.linalg.norm(B - A, axis=1), np.linalg.norm(C - B, axis=1)), np.linalg.norm(A - C, axis=1))
        big = L > lmax
        if not big.any(): break
        Tb = T[big]; n0 = len(V)
        M = np.vstack([(V[Tb[:, 0]] + V[Tb[:, 1]]) / 2, (V[Tb[:, 1]] + V[Tb[:, 2]]) / 2, (V[Tb[:, 2]] + V[Tb[:, 0]]) / 2])
        k = len(Tb); m01 = n0 + np.arange(k); m12 = n0 + k + np.arange(k); m20 = n0 + 2 * k + np.arange(k)
        new = np.vstack([np.stack([Tb[:, 0], m01, m20], 1), np.stack([m01, Tb[:, 1], m12], 1), np.stack([m20, m12, Tb[:, 2]], 1), np.stack([m01, m12, m20], 1)])
        V = np.vstack([V, M]); T = np.vstack([T[~big], new])
    return V, T
capm = on_any_plane(VO, TO); Vp, Tp = subdivide(VO, TO[~capm], CELL)
bt = bin_of(Vp[Tp].mean(axis=1))
col = np.full((len(Tp), 3), (0.62, 0.64, 0.68))
col[rebuild[bt[:, 0], bt[:, 1], bt[:, 2]]] = (0.95, 0.55, 0.15)
col[fchg[bt[:, 0], bt[:, 1], bt[:, 2]]] = (0.25, 0.75, 0.35)
cx = Vp[Tp].mean(axis=1)
for b in PROTECT:
    col[(cx[:, 0] >= b[0]) & (cx[:, 0] <= b[1]) & (cx[:, 1] >= b[2]) & (cx[:, 1] <= b[3]) & (cx[:, 2] >= b[4]) & (cx[:, 2] <= b[5])] = (0.25, 0.75, 0.35)
try:
    bv = bin_of(Vp); rv = rebuild[bv[:, 0], bv[:, 1], bv[:, 2]]; rt = rv[Tp]
    col[rt.any(axis=1) & ~rt.all(axis=1)] = (0.92, 0.12, 0.12)
except Exception as _ex: say("cut lines not drawn: %r" % (_ex,))
frames = []
ttl = "grey KEPT exactly (%.0f %%), orange REBUILT (%d bins of %.1f mm), green FORCED KEPT, RED = the CUTS (kept meets rebuilt): judge every red line" % (100 * kept_area, int(rebuild.sum()), CELL)
views = {"above": R.look(fwd=0.25, left=0.2, up=-1.0), "below": R.look(fwd=0.25, left=-0.2, up=1.0), "fromP": R.look(left=-1.0, up=-0.2), "fromM": R.look(left=1.0, up=-0.2),
         "fore": R.look(fwd=-1.0, up=-0.3), "aft": R.look(fwd=1.0, up=-0.3), "iso_fore": R.look(fwd=0.8, left=-0.5, up=-0.5), "iso_aft_below": R.look(fwd=-0.7, left=0.5, up=0.6)}
for nm, d in views.items():
    try:
        pth = os.path.join(OUT_DIR, "keep_cuts_%s.png" % nm)
        R.render(pth, [("m", Vp, Tp, col)], d, W=1300, title="CUTS %s: %s" % (nm, ttl)); frames.append(os.path.basename(pth))
    except Exception as _ex: say("cut frame %s not made: %r" % (nm, _ex))
try:
    pts = [e["at"] for e in (left or bfaces)[:60] if e.get("at") is not None and e["width"] > 0.05]
    for k, (cnt, cen, plo, phi) in enumerate(KG.clusters(np.array(pts, float), cell=6.0, top=3) if pts else []):
        boxl = np.minimum(plo, cen - 4.0); boxh = np.maximum(phi, cen + 4.0)
        foc = np.array([[x, y, z] for x in (boxl[0], boxh[0]) for y in (boxl[1], boxh[1]) for z in (boxl[2], boxh[2])], float)
        for dn, d in (("a", R.look(fwd=0.5, left=0.4, up=-0.7)), ("b", R.look(fwd=-0.5, left=-0.4, up=0.5))):
            pth = os.path.join(OUT_DIR, "keep_cuts_close%d%s.png" % (k + 1, dn))
            R.render(pth, [("m", Vp, Tp, col)], d, W=1200, focus=foc, title="CUTS CLOSE-UP %d%s: the cut estimated %s here - is a red line running ALONG a skin or a thin lip?" % (k + 1, dn, "over the seam ceiling" if left else "widest"))
            frames.append(os.path.basename(pth))
except Exception as _ex: say("cut close-ups not made: %r" % (_ex,))
try:
    import hashlib
    _md5 = hashlib.md5(open(kr, "rb").read()).hexdigest()
    json.dump({"tag": TAG, "region": kr, "region_md5": _md5, "frames": frames, "cuts_over_seam_max_left": len(left), "grid": grid_rep, "keep_offset": _extra},
              open(os.path.join(OUT_DIR, "CUTS.json"), "w"), indent=1)
except Exception as _ex: say("CUTS.json not written: %r" % (_ex,))
say("THE ORBIT OF THE CUTS: %d frame(s) in %s - OPEN EVERY ONE and judge every red line: a cut that runs along a skin, through a thin lip or rib, or across a feature being fixed is MOVED (KEEP_OFFSET, the window's walls) and the keep run again; then `kit rebuild judge --job <J> --what keep --verdict ok --note \"<what the frames show>\"` - the reinsert refuses without it" % (len(frames), OUT_DIR))
print("KEEP -> %s: %d bin(s) rebuilt, %d forced kept, %.0f %% of the original's surface kept exactly; pictures in %s (OPEN EVERY ONE) (%.0fs)"
      % (kr, int(rebuild.sum()), int(fchg.sum()), 100 * kept_area, OUT_DIR, time.time() - T0), flush=True)

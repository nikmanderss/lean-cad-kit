# kit rebuild
# over the
import sys, os, time, numpy as np
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
def _fail(m): print(m if str(m).startswith("FAIL") else "FAIL: " + str(m), flush=True); raise SystemExit(1)
TAG = os.environ.get("LK_TAG", "")
sys.path.insert(0, os.environ["KIT_HOME"])
import kitlib_render as R
import vtk
from vtk.util import numpy_support as nps
from scipy import ndimage
from scipy.spatial import cKDTree
def _arg(name, i, default=None):
    v = os.environ.get(name)
    if v not in (None, ""): return v
    if len(sys.argv) > i and not sys.argv[i].lower().endswith(".py"): return sys.argv[i]
    if default is None: _fail("rb_blend: %s not set (env %s or argument %d)" % (name, name, i))
    return default
src = _arg("STL", 1); out = _arg("OUT", 2); RB = float(_arg("R", 3, "3.0")); h = float(_arg("H", 4, "0.2"))
W = float(_arg("W", 5, "5.0")); E = float(_arg("E", 6, "6.0"))
R_SMALL = float(os.environ.get("R_SMALL", "1.0")); V_BIG = float(os.environ.get("V_BIG", "50.0"))
WIN = [float(v) for v in (os.environ.get("WIN") or _fail("WIN not set")).split()]
SAMP = float(os.environ.get("SAMP", "0.08")); BAND = 3 * h
T0 = time.time()
def say(*a): print("%6.0fs " % (time.time() - T0), *a, flush=True)
rd = R.read_stl(src); V, T = np.asarray(rd[0], float), np.asarray(rd[1], int)
key = np.round(V / 1e-5).astype(np.int64); _, ui, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1); V = V[ui]; T = inv[T]
say("base %d triangles, %d welded vertices" % (len(T), len(V)))
try:   # INTERNAL
    _imB, _iclB = R.internal_triangles(V, T)
    say("the base's inside check: %s" % (("%d place(s) with material on both sides of a triangle - %s" % (len(_iclB), "; ".join("%.3f mm2 at %s" % (c["area_mm2"], c["at"]) for c in _iclB[:6]))) if _iclB else "no triangle has material on both sides"))
    del _imB
except Exception as _ex: say("the base's inside check skipped: %r" % (_ex,))
def _parse_zones(txt):
    out = []
    for zs in [z for z in (txt or "").split(";") if z.strip()]:
        tok = zs.split(); nums = [t for t in tok if "=" not in t]; opts = dict(t.split("=", 1) for t in tok if "=" in t)
        if len(nums) != 6 or not opts or not set(opts) <= {"flat", "r", "open", "smooth"}:
            _fail("FAIL: a ZONES entry is 'x0 x1 y0 y1 z0 z1' and one or more of flat=<mm> r=<mm> open=<mm> smooth=<mm>, got %r" % zs)
        b = [float(v) for v in nums]
        if not (b[0] < b[1] and b[2] < b[3] and b[4] < b[5]): _fail("FAIL: a ZONES box needs x0 < x1, y0 < y1, z0 < z1, got %r" % zs)
        out.append((b, {k: float(v) for k, v in opts.items()}))
    return out
ZONES = _parse_zones(os.environ.get("ZONES", "")); ZONE_W = float(os.environ.get("ZONE_W", "1.5"))
ZONE_R = sorted(set(o["r"] for _b, o in ZONES if "r" in o))
KEEP_E_EXTRA = None
if os.environ.get("KEEP", "0") == "1":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _keepweld, gc
    KEEP_E_EXTRA = _keepweld.base_self_intersections(V, T, say); gc.collect()
import json
PL = json.load(open(os.environ["WALLS"])) if os.environ.get("WALLS") else [[WIN[0], 0, 0, -1, 0, 0], [WIN[1], 0, 0, 1, 0, 0], [0, WIN[2], 0, 0, -1, 0], [0, WIN[3], 0, 0, 1, 0], [0, 0, WIN[4], 0, 0, -1], [0, 0, WIN[5], 0, 0, 1]]
walls = []
for cx, cy, cz, nx_, ny_, nz_ in PL:
    c = np.array([cx, cy, cz], float); n = np.array([nx_, ny_, nz_], float); n /= np.linalg.norm(n)
    dist = (V - c) @ n
    on = np.all(np.abs(dist[T]) < 1e-3, axis=1)
    if on.sum(): walls.append((c, n, on))
V2 = V.copy(); T2 = [T]
for c, n, on in walls:
    Tw = T[on]
    e = np.vstack([Tw[:, [0, 1]], Tw[:, [1, 2]], Tw[:, [2, 0]]]); es = np.sort(e, axis=1)
    _, idx, cnt = np.unique(es, axis=0, return_index=True, return_counts=True); be = e[idx[cnt == 1]]
    wv_ids = np.unique(Tw); shift = n * E
    newid = {int(v): len(V2) + k for k, v in enumerate(wv_ids)}
    V2 = np.vstack([V2, V[wv_ids] + shift])
    cap = np.vectorize(lambda v: newid[int(v)])(Tw)
    side = np.array([[a, b, newid[int(b)]] for a, b in be] + [[a, newid[int(b)], newid[int(a)]] for a, b in be])
    T2.append(cap); T2.append(side)
    say("wall plane c=(%.1f %.1f %.1f) n=(%.2f %.2f %.2f): %d triangles extruded %.0f mm, %d boundary edges" % (c[0], c[1], c[2], n[0], n[1], n[2], on.sum(), E, len(be)))
keep = np.ones(len(T), bool)
for c, n, on in walls: keep &= ~on
T2[0] = T[keep]; TE = np.vstack(T2); VE = V2
lo = VE.min(0) - (RB + 4 * h); hi = VE.max(0) + (RB + 4 * h)
_gm = os.environ.get("GRID_MIRROR_X", "auto").strip().lower()
if _gm == "auto": _gm = "0" if abs(WIN[0] + WIN[1]) < 1e-6 else "none"
if _gm not in ("none", ""):
    _mx = float(_gm); nx = 2 * int(np.ceil(max(_mx - lo[0], hi[0] - _mx) / h)); x0 = _mx - nx / 2.0 * h + h / 2.0
else:
    nx = int(np.ceil((hi[0] - lo[0]) / h)) + 1; x0 = lo[0]
ny = int(np.ceil((hi[1] - lo[1]) / h)) + 1; y0 = lo[1]; nz = int(np.ceil((hi[2] - lo[2]) / h)) + 1; z0 = lo[2]
x0 += 0.37 * h; y0 += 0.29 * h; z0 += 0.43 * h
xs = x0 + h * np.arange(nx); ys = y0 + h * np.arange(ny); zs = z0 + h * np.arange(nz)
say("grid %d x %d x %d = %.1f M at %.2f mm (%s)" % (nx, ny, nz, nx * ny * nz / 1e6, h, ("centred on the mirror plane x = %g" % float(_gm)) if _gm not in ("none", "") else "on the window's own extent"))
INSIDE = os.environ.get("INSIDE", "vote").strip().lower()
if INSIDE == "zparity":
    ZR = R.ZRays(VE, TE, cell=2.0)
    inside = np.zeros((nx, ny, nz), bool)
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            for za, zb in ZR.solid_runs(x, y):
                k0 = int(np.ceil((za - z0) / h)); k1 = int(np.floor((zb - z0) / h))
                if k1 >= k0: inside[i, j, max(k0, 0):min(k1, nz - 1) + 1] = True
    say("inside (z-ray parity, INSIDE=zparity - the control): %.0f mm3" % (inside.sum() * h ** 3))
elif INSIDE == "vote":
    inside, _occ3 = R.inside_vote(VE, TE, np.array([x0, y0, z0]), (nx, ny, nz), h)
    _dis = (_occ3[0] != inside) | (_occ3[1] != inside) | (_occ3[2] != inside); _nd = int(_dis.sum())
    if _nd:
        _I = np.argwhere(_dis)
        if len(_I) > 20000: _I = _I[np.random.RandomState(3).choice(len(_I), 20000, replace=False)]
        _P = np.stack([xs[_I[:, 0]], ys[_I[:, 1]], zs[_I[:, 2]]], axis=1)
        _lab = R.cluster_points(_P, 3.0 * h); _cl = []
        for _g in np.unique(_lab):
            _m = _lab == _g; _cl.append((int(_m.sum()), _P[_m].mean(axis=0)))
        _cl.sort(key=lambda c: -c[0])
        say("inside (3-axis winding vote): %.0f mm3; the three ray directions DISAGREE at %d voxel(s) in %d place(s) - the vote decides (one axis alone would have built them): %s" % (inside.sum() * h ** 3, _nd, len(_cl), "; ".join("%d at (%.1f, %.1f, %.1f)" % (n_, c_[0], c_[1], c_[2]) for n_, c_ in _cl[:8])))
        del _I, _P, _lab
    else:
        say("inside (3-axis winding vote): %.0f mm3; the three ray directions agree everywhere" % (inside.sum() * h ** 3))
    del _occ3, _dis
else: _fail("FAIL: INSIDE is vote or zparity, not %r" % INSIDE)
def dense_samples(V_, T_, s):
    A, B, C = V_[T_[:, 0]], V_[T_[:, 1]], V_[T_[:, 2]]
    L = np.maximum(np.maximum(np.linalg.norm(B - A, axis=1), np.linalg.norm(C - B, axis=1)), np.linalg.norm(A - C, axis=1))
    n = np.maximum(1, np.ceil(L / s).astype(int)); out = []
    for k in np.unique(n):
        m = n == k; ij = np.array([(i, j) for i in range(k + 1) for j in range(k + 1 - i)], float) / k
        P = A[m][:, None, :] + (B[m] - A[m])[:, None, :] * ij[None, :, 0:1] + (C[m] - A[m])[:, None, :] * ij[None, :, 1:2]
        out.append(P.reshape(-1, 3))
    return np.vstack(out)
S1 = dense_samples(VE, TE, SAMP); kd1 = cKDTree(S1)
say("surface samples %d" % len(S1))
edt_out = ndimage.distance_transform_edt(~inside, sampling=(h, h, h)).astype(np.float32)
edt_in = ndimage.distance_transform_edt(inside, sampling=(h, h, h)).astype(np.float32)
sdf = np.where(inside, -edt_in, edt_out).astype(np.float32); del edt_out, edt_in
band = (np.abs(sdf - RB) <= BAND) | (np.abs(sdf - R_SMALL) <= BAND) | (np.abs(sdf) <= BAND)
for _zr in ZONE_R: band |= np.abs(sdf - _zr) <= BAND
idx = np.argwhere(band); P = np.stack([xs[idx[:, 0]], ys[idx[:, 1]], zs[idx[:, 2]]], axis=1)
d, _ = kd1.query(P, workers=-1); d = d.astype(np.float32)
d1 = sdf.copy(); d1[band] = np.where(inside[band], -d, d)
say("d1 exact on %d band voxels (%.1f %%)" % (len(idx), 100.0 * len(idx) / band.size))
def level_mesh(field, level):
    img = vtk.vtkImageData(); img.SetDimensions(nx, ny, nz); img.SetOrigin(x0, y0, z0); img.SetSpacing(h, h, h)
    arr = nps.numpy_to_vtk(np.ascontiguousarray(field.ravel(order="F")), deep=True); arr.SetName("f"); img.GetPointData().SetScalars(arr)
    fe = vtk.vtkFlyingEdges3D(); fe.SetInputData(img); fe.SetValue(0, level); fe.ComputeNormalsOff(); fe.Update()
    return fe.GetOutput()
def closing_field(Rc):
    """F >= 0 inside the rolling-ball closing of radius Rc: dilation level set meshed, distance to it exact in a band"""
    Ds = level_mesh(d1, Rc); DVc = nps.vtk_to_numpy(Ds.GetPoints().GetData()).astype(float)
    Dm = d1 <= Rc; edt = ndimage.distance_transform_edt(Dm, sampling=(h, h, h)).astype(np.float32)
    b2 = Dm & (np.abs(edt - Rc) <= BAND); i2 = np.argwhere(b2); P2 = np.stack([xs[i2[:, 0]], ys[i2[:, 1]], zs[i2[:, 2]]], axis=1)
    d2c, _ = cKDTree(DVc).query(P2, workers=-1); edt[b2] = d2c.astype(np.float32)
    say("closing R %.1f: dilated surface %d vertices, d2 exact on %d voxels" % (Rc, len(DVc), len(i2)))
    return np.minimum(Rc - d1, edt - Rc), DVc
F, DV = closing_field(RB)
F0 = -d1
if R_SMALL > 0 and R_SMALL < RB:
    added = (F >= 0) & ~inside; lab, nlab = ndimage.label(added)
    vols = ndimage.sum(added, lab, range(1, nlab + 1)) * h ** 3
    big_ids = [i + 1 for i, v in enumerate(vols) if v >= V_BIG]
    zone = np.isin(lab, big_ids)
    say("fills: %d components, %d of them >= %.0f mm3 (%.0f of %.0f mm3) keep R %.1f; the rest get R %.1f" % (nlab, len(big_ids), V_BIG, vols[[i - 1 for i in big_ids]].sum() if big_ids else 0, vols.sum(), RB, R_SMALL))
    Fs, _ = closing_field(R_SMALL)
    dz = ndimage.distance_transform_edt(~zone, sampling=(h, h, h)).astype(np.float32)
    wz = np.clip(1.0 - dz / 1.5, 0.0, 1.0)
    F = Fs + wz * (F - Fs); del Fs, dz, wz
# over the
KEEP = os.environ.get("KEEP", "0") == "1"; KEEP_M = float(os.environ.get("KEEP_M", "1.5"))
FADE_IN = (KEEP_M + 1.0) if KEEP else 0.0
OPEN = float(os.environ.get("OPEN", "0.4"))
if OPEN > 0:
    Cs = level_mesh(F, 0.0); CV = nps.vtk_to_numpy(Cs.GetPoints().GetData()).astype(float)
    Cm = F >= 0; eC = ndimage.distance_transform_edt(Cm, sampling=(h, h, h)).astype(np.float32)
    bC = Cm & (np.abs(eC - OPEN) <= BAND); iC = np.argwhere(bC); PC = np.stack([xs[iC[:, 0]], ys[iC[:, 1]], zs[iC[:, 2]]], axis=1)
    dC, _ = cKDTree(CV).query(PC, workers=-1); eC[bC] = dC.astype(np.float32)
    G = np.where(Cm, eC - OPEN, -1.0).astype(np.float32)
    Es = level_mesh(G, 0.0); EV = nps.vtk_to_numpy(Es.GetPoints().GetData()).astype(float)
    Em = G >= 0; eE = ndimage.distance_transform_edt(~Em, sampling=(h, h, h)).astype(np.float32)
    bE = (np.abs(eE - OPEN) <= BAND) & ~Em; iE = np.argwhere(bE); PE = np.stack([xs[iE[:, 0]], ys[iE[:, 1]], zs[iE[:, 2]]], axis=1)
    dE, _ = cKDTree(EV).query(PE, workers=-1); eE[bE] = dE.astype(np.float32)
    Fo = np.where(Em, G + OPEN, OPEN - eE).astype(np.float32)
    removed = ((F >= 0) & ~(Fo >= 0)).sum() * h ** 3
    say("opening %.2f: %.1f mm3 of fins/slivers removed (closed surface %d vertices, eroded %d)" % (OPEN, removed, len(CV), len(EV)))
    F = Fo; del Cs, CV, eC, G, Es, EV, eE, Fo
X, Y, Z = np.meshgrid(xs.astype(np.float32), ys.astype(np.float32), zs.astype(np.float32), indexing="ij")
Fw = F
WALLT = np.ones(F.shape, np.float32) if ZONES else None
for c, n, on in walls:
    dpl = np.abs((X - c[0]) * n[0] + (Y - c[1]) * n[1] + (Z - c[2]) * n[2])
    tt = np.clip((dpl - FADE_IN) / max(W - FADE_IN, 1e-6), 0.0, 1.0).astype(np.float32)
    Fw = (1.0 - tt) * F0 + tt * Fw
    if WALLT is not None: WALLT *= tt
PROTECT = [[float(v) for v in b.split()] for b in os.environ.get("PROTECT", "").split(";") if b.strip()]
PROTECT_W = float(os.environ.get("PROTECT_W", "2.0"))
for b in PROTECT:
    if len(b) != 6: _fail("FAIL: PROTECT box needs six numbers x0 x1 y0 y1 z0 z1, got %r" % b)
    dx = np.maximum(np.maximum(b[0] - X, X - b[1]), 0.0); dy = np.maximum(np.maximum(b[2] - Y, Y - b[3]), 0.0); dz = np.maximum(np.maximum(b[4] - Z, Z - b[5]), 0.0)
    dout = np.sqrt(dx * dx + dy * dy + dz * dz)
    tt = np.clip((dout - FADE_IN) / PROTECT_W, 0.0, 1.0).astype(np.float32)
    Fw = (1.0 - tt) * F0 + tt * Fw
    say("protected void %s: the base kept inside%s, faded over %.1f mm outside" % (b, (" and within %.1f mm of it" % FADE_IN) if FADE_IN else "", PROTECT_W))
# over the
ZONE_REC = []
if ZONES:
    def _sub(b, m):
        i0 = max(0, int(np.floor((b[0] - m - x0) / h))); i1 = min(nx, int(np.ceil((b[1] + m - x0) / h)) + 1)
        j0 = max(0, int(np.floor((b[2] - m - y0) / h))); j1 = min(ny, int(np.ceil((b[3] + m - y0) / h)) + 1)
        k0 = max(0, int(np.floor((b[4] - m - z0) / h))); k1 = min(nz, int(np.ceil((b[5] + m - z0) / h)) + 1)
        return (slice(i0, i1), slice(j0, j1), slice(k0, k1))
    def _mesh_at(field, level, org):
        img = vtk.vtkImageData(); img.SetDimensions(*field.shape); img.SetOrigin(*[float(v) for v in org]); img.SetSpacing(h, h, h)
        arr = nps.numpy_to_vtk(np.ascontiguousarray(field.ravel(order="F")), deep=True); arr.SetName("f"); img.GetPointData().SetScalars(arr)
        fe = vtk.vtkFlyingEdges3D(); fe.SetInputData(img); fe.SetValue(0, level); fe.ComputeNormalsOff(); fe.Update()
        return nps.vtk_to_numpy(fe.GetOutput().GetPoints().GetData()).astype(float) if fe.GetOutput().GetNumberOfPoints() else np.zeros((0, 3))
    def _opening_sub(Fin, Ro, gx, gy, gz):
        """the OPENING of {Fin >= 0} at radius Ro on a sub-grid (axes gx gy gz): erosion by the distance to the meshed surface,
        dilation by the distance to the meshed eroded surface - exact in a band, as the window's own OPEN"""
        org = (gx[0], gy[0], gz[0])
        CV = _mesh_at(Fin, 0.0, org); Cm = Fin >= 0
        eC = ndimage.distance_transform_edt(Cm, sampling=(h, h, h)).astype(np.float32)
        bC = Cm & (np.abs(eC - Ro) <= BAND); iC = np.argwhere(bC)
        if len(CV) and len(iC): eC[bC] = cKDTree(CV).query(np.stack([gx[iC[:, 0]], gy[iC[:, 1]], gz[iC[:, 2]]], axis=1), workers=-1)[0].astype(np.float32)
        G = np.where(Cm, eC - Ro, -1.0).astype(np.float32)
        EV = _mesh_at(G, 0.0, org); Em = G >= 0
        eE = ndimage.distance_transform_edt(~Em, sampling=(h, h, h)).astype(np.float32)
        bE = (np.abs(eE - Ro) <= BAND) & ~Em; iE = np.argwhere(bE)
        if len(EV) and len(iE): eE[bE] = cKDTree(EV).query(np.stack([gx[iE[:, 0]], gy[iE[:, 1]], gz[iE[:, 2]]], axis=1), workers=-1)[0].astype(np.float32)
        return np.where(Em, G + Ro, Ro - eE).astype(np.float32)
    _closing_cache = {}
    if Fw is F: Fw = Fw.copy()
    if any("flat" in zo for _zb, zo in ZONES):
        _TC = V[T].mean(axis=1); _TNr = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]); _TA = 0.5 * np.linalg.norm(_TNr, axis=1)
        _TN = _TNr / np.maximum(2.0 * _TA, 1e-12)[:, None]
    def _flatten(zb, depth, gx, gy, gz):
        """31ak: the base's surface just outside the box, fitted (a quadratic height over its plane, trimmed) and continued across
        the box: returns (ok, (field, taper), what it did) - the field is minus the height above that surface, the taper limits it
        to within `depth` of it"""
        lo = np.array([zb[0], zb[2], zb[4]]); hi = np.array([zb[1], zb[3], zb[5]]); ring = ZONE_W + 1.0
        ins = np.all((_TC >= lo) & (_TC <= hi), axis=1) & (_TA > 1e-6)
        if ins.sum() < 3: return False, None, "only %d base triangles inside the box - it holds no surface to rebuild" % int(ins.sum())
        # over the
        nm = (_TN[ins] * _TA[ins][:, None]).sum(0); nm = nm / max(np.linalg.norm(nm), 1e-12)
        inb = np.all((_TC >= lo - ring) & (_TC <= hi + ring), axis=1) & ~np.all((_TC >= lo) & (_TC <= hi), axis=1) & (_TA > 1e-6)
        n_ = _TN[inb]; a_ = _TA[inb]; c_ = _TC[inb]
        kp = (n_ @ nm) > np.cos(np.radians(35.0))
        if kp.sum() < 12: return False, None, "only %d base triangles round the box face the way the surface inside it does - draw the box bigger or round one surface" % int(kp.sum())
        nm = (n_[kp] * a_[kp][:, None]).sum(0); nm = nm / max(np.linalg.norm(nm), 1e-12)
        c_, a_ = c_[kp], a_[kp]
        c0 = (c_ * a_[:, None]).sum(0) / a_.sum()
        e1 = np.cross(nm, [1.0, 0.0, 0.0])
        if np.linalg.norm(e1) < 0.3: e1 = np.cross(nm, [0.0, 1.0, 0.0])
        e1 = e1 / np.linalg.norm(e1); e2 = np.cross(nm, e1)
        d_ = c_ - c0; U = d_ @ e1; Vq = d_ @ e2; S = d_ @ nm
        A = np.stack([np.ones_like(U), U, Vq, U * U, U * Vq, Vq * Vq], axis=1); wt = np.sqrt(a_); m = np.ones(len(U), bool)
        FLAT_TRIM = float(os.environ.get("FLAT_TRIM", "0.1")); coef = np.zeros(3); res = S.copy(); ncol = 3
        for ncol in ((3, 6) if len(U) >= 24 else (3,)):
            for _i in range(6):
                coef = np.linalg.lstsq(A[m][:, :ncol] * wt[m][:, None], S[m] * wt[m], rcond=None)[0]; res = S - A[:, :ncol] @ coef
                m2 = np.abs(res) <= FLAT_TRIM
                if m2.sum() < 12 or (m2 == m).all(): break
                m = m2
        coef = np.concatenate([coef, np.zeros(6 - len(coef))])
        rms = float(np.sqrt(np.mean(res[m] ** 2)))
        GX, GY, GZ = np.meshgrid(gx, gy, gz, indexing="ij")
        Px = GX - c0[0]; Py = GY - c0[1]; Pz = GZ - c0[2]; del GX, GY, GZ
        u = Px * e1[0] + Py * e1[1] + Pz * e1[2]; v = Px * e2[0] + Py * e2[1] + Pz * e2[2]; sx = Px * nm[0] + Py * nm[1] + Pz * nm[2]; del Px, Py, Pz
        bas = [np.ones_like(u), u, v, u * u, u * v, v * v]
        hgt = sx - sum(cf * b_ for cf, b_ in zip(coef, bas))
        tap = np.clip((depth + 0.5 - np.abs(hgt)) / 0.5, 0.0, 1.0).astype(np.float32)
        return True, ((-hgt).astype(np.float32), tap), "the surface round it continued across it - %d base triangles, normal (%.2f %.2f %.2f), rms %.3f mm, within %.2f mm of it" % (int(m.sum()), nm[0], nm[1], nm[2], rms, depth)
    for zb, zo in ZONES:
        reach = max(zo.get("r", 0.0), 2.0 * zo.get("open", 0.0), 3.0 * zo.get("smooth", 0.0), zo.get("flat", 0.0))
        sl = _sub(zb, ZONE_W + reach + 6 * h); gx, gy, gz = xs[sl[0]], ys[sl[1]], zs[sl[2]]
        Xs, Ys, Zs = X[sl], Y[sl], Z[sl]
        dx = np.maximum(np.maximum(zb[0] - Xs, Xs - zb[1]), 0.0); dy = np.maximum(np.maximum(zb[2] - Ys, Ys - zb[3]), 0.0); dz = np.maximum(np.maximum(zb[4] - Zs, Zs - zb[5]), 0.0)
        w = np.clip(1.0 - np.sqrt(dx * dx + dy * dy + dz * dz) / max(ZONE_W, 1e-6), 0.0, 1.0).astype(np.float32) * WALLT[sl]; del dx, dy, dz
        F_sub = Fw[sl].copy(); before = F_sub >= 0; done = []
        if zo.get("flat", 0) > 0:
            _ok, _ft, _what = _flatten(zb, zo["flat"], gx, gy, gz)
            if _ok:
                F_sub = F_sub + w * _ft[1] * (_ft[0] - F_sub); done.append("flatten: " + _what)
            else: done.append("flatten SKIPPED: " + _what)
        if "r" in zo:
            if zo["r"] not in _closing_cache: _closing_cache[zo["r"]] = closing_field(zo["r"])[0]
            F_sub = F_sub + w * (_closing_cache[zo["r"]][sl] - F_sub); done.append("closing r %.2f" % zo["r"])
        if zo.get("open", 0) > 0:
            F_sub = F_sub + w * (_opening_sub(F_sub, zo["open"], gx, gy, gz) - F_sub); done.append("opening %.2f" % zo["open"])
        if zo.get("smooth", 0) > 0:
            F_sub = F_sub + w * (ndimage.gaussian_filter(F_sub, sigma=zo["smooth"] / h, mode="nearest").astype(np.float32) - F_sub); done.append("smoothing sigma %.2f" % zo["smooth"])
        after = F_sub >= 0; add_ = float((after & ~before).sum() * h ** 3); rem_ = float((before & ~after).sum() * h ** 3)
        Fw[sl] = F_sub
        _ovl = [pb for pb in PROTECT if pb[0] <= zb[1] + ZONE_W and pb[1] >= zb[0] - ZONE_W and pb[2] <= zb[3] + ZONE_W and pb[3] >= zb[2] - ZONE_W and pb[4] <= zb[5] + ZONE_W and pb[5] >= zb[4] - ZONE_W]
        say("zone %s: %s - material added %.1f mm3, removed %.1f mm3 (faded over %.1f mm, never at a window wall)%s" % (zb, ", ".join(done), add_, rem_, ZONE_W,
            ("; it meets PROTECT box(es) %s - inside a box the keep restores the original, near its faces this zone changes the box-face seam%s" % (_ovl, "; r= over a box FILLS the opening" if "r" in zo else "")) if _ovl else ""))
        ZONE_REC.append({"box": zb, "ops": zo, "added_mm3": round(add_, 1), "removed_mm3": round(rem_, 1), "meets_protect": _ovl})
        del F_sub, before, after, w, Xs, Ys, Zs
    _closing_cache.clear()
if WALLT is not None: del WALLT
del X, Y, Z
if os.environ.get("DUMP"): np.savez(os.environ["DUMP"], d1=d1, F=Fw, xs=xs, ys=ys, zs=zs, inside=inside)
ADDED_FULL = float(((F >= 0) & ~inside).sum() * h ** 3); ADDED_FADED = float(((Fw >= 0) & ~inside).sum() * h ** 3)
say("closing: added %.0f mm3 (full), %.0f mm3 (faded at the walls)" % (ADDED_FULL, ADDED_FADED))
surf = level_mesh(Fw, 0.0)
clip = vtk.vtkClipClosedSurface(); planes = vtk.vtkPlaneCollection()
CLIP_OUT = float(os.environ.get("CLIP_OUT", "0.0"))
for c, n, on in walls:
    pl = vtk.vtkPlane(); pl.SetOrigin(*[float(v) for v in (c + n * CLIP_OUT)]); pl.SetNormal(*[float(-v) for v in n]); planes.AddItem(pl)
if os.environ.get("CLIP_BOX", "0") == "1":
    for ax in range(3):
        for wv, sgn in ((WIN[2 * ax], -1), (WIN[2 * ax + 1], +1)):
            pl = vtk.vtkPlane(); o = [0.0, 0.0, 0.0]; o[ax] = wv; nn = [0.0, 0.0, 0.0]; nn[ax] = -sgn; pl.SetOrigin(*o); pl.SetNormal(*nn); planes.AddItem(pl)
clip.SetInputData(surf); clip.SetClippingPlanes(planes); clip.GenerateFacesOn(); clip.SetTolerance(1e-6); clip.Update()
tri = vtk.vtkTriangleFilter(); tri.SetInputConnection(clip.GetOutputPort()); tri.Update()
w = vtk.vtkSTLWriter(); w.SetFileName(out); w.SetInputConnection(tri.GetOutputPort()); w.SetFileTypeToBinary(); w.Write()
rd2 = R.read_stl(out); V3, T3 = np.asarray(rd2[0], float), np.asarray(rd2[1], int)
WELD = float(os.environ.get('WELD', '0.005'))
key = np.round(V3 / WELD).astype(np.int64); _, ui, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1); V3 = V3[ui]; T3 = inv[T3]
T3 = T3[(T3[:, 0] != T3[:, 1]) & (T3[:, 1] != T3[:, 2]) & (T3[:, 0] != T3[:, 2])]
_, uu = np.unique(np.sort(T3, axis=1), axis=0, return_index=True); T3 = T3[np.sort(uu)]
SNAP = float(os.environ.get("SNAP", "0.03"))
if SNAP > 0:
    pdb = vtk.vtkPolyData(); ptb = vtk.vtkPoints(); ptb.SetData(nps.numpy_to_vtk(np.ascontiguousarray(VE), deep=True)); pdb.SetPoints(ptb)
    cb = vtk.vtkCellArray(); conn = np.hstack([np.full((len(TE), 1), 3), TE]).astype(np.int64).ravel(); cb.SetCells(len(TE), nps.numpy_to_vtkIdTypeArray(conn, deep=True)); pdb.SetPolys(cb)
    ipd = vtk.vtkImplicitPolyDataDistance(); ipd.SetInput(pdb)
    cp = [0.0, 0.0, 0.0]; moved = 0; V3 = V3.copy()
    capax = {}
    for wi, (c, n, on) in enumerate(walls): capax[wi] = np.abs((V3 - (c + n * CLIP_OUT)) @ n) < 1e-5
    order = np.argsort(T3.ravel()); vidx = T3.ravel()[order]; tidx = np.repeat(np.arange(len(T3)), 3)[order]
    starts = np.searchsorted(vidx, np.arange(len(V3) + 1))
    def tri_normals(Vx, tl):
        P = Vx[T3[tl]]; n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); return n
    reverted = 0; skipped_edge = 0
    EDGE_DEG = float(os.environ.get("EDGE_DEG", "25"))
    tn = np.cross(V3[T3[:, 1]] - V3[T3[:, 0]], V3[T3[:, 2]] - V3[T3[:, 0]])
    vn = np.zeros((len(V3), 3)); np.add.at(vn, T3[:, 0], tn); np.add.at(vn, T3[:, 1], tn); np.add.at(vn, T3[:, 2], tn)
    vn /= np.maximum(np.linalg.norm(vn, axis=1), 1e-12)[:, None]
    bn = np.cross(VE[TE[:, 1]] - VE[TE[:, 0]], VE[TE[:, 2]] - VE[TE[:, 0]]); bn /= np.maximum(np.linalg.norm(bn, axis=1), 1e-12)[:, None]
    kdbc = cKDTree(VE[TE].mean(axis=1)); cos_lim = np.cos(np.radians(EDGE_DEG))
    FLAT_DEG = float(os.environ.get("FLAT_DEG", "0.5")); cos_flat = np.cos(np.radians(FLAT_DEG))
    eb = np.vstack([TE[:, [0, 1]], TE[:, [1, 2]], TE[:, [2, 0]]]); ebs = np.sort(eb, axis=1); et = np.tile(np.arange(len(TE)), 3)
    o = np.lexsort((ebs[:, 1], ebs[:, 0])); ebs = ebs[o]; et = et[o]
    same = np.all(ebs[1:] == ebs[:-1], axis=1); pa = et[:-1][same]; pb = et[1:][same]
    planar = np.ones(len(TE), bool); dots = np.einsum("ij,ij->i", bn[pa], bn[pb]); badp = dots < cos_flat
    planar[pa[badp]] = False; planar[pb[badp]] = False
    skipped_curved = 0
    for i in range(len(V3)):
        d = ipd.EvaluateFunctionAndGetClosestPoint(V3[i], cp)
        if abs(d) <= SNAP:
            _, jt = kdbc.query(cp)
            if abs(float(vn[i] @ bn[jt])) < cos_lim: skipped_edge += 1; continue
            if not planar[jt]: skipped_curved += 1; continue
            q = np.array(cp)
            for wi, m in capax.items():
                if m[i]:
                    c, n, on = walls[wi]; cc = c + n * CLIP_OUT; q = q - ((q - cc) @ n) * n
            tl = tidx[starts[i]:starts[i + 1]]
            n0 = tri_normals(V3, tl); old_ = V3[i].copy(); V3[i] = q; n1 = tri_normals(V3, tl)
            a0 = np.linalg.norm(n0, axis=1); a1 = np.linalg.norm(n1, axis=1)
            if np.any(np.einsum("ij,ij->i", n0, n1) <= 0.0) or np.any(a1 < 0.05 * np.maximum(a0, 1e-12)):
                V3[i] = old_; reverted += 1              # not taken
            else: moved += 1
    say("  (%d snaps refused because a triangle would fold, %d skipped at sharp edges, %d skipped on curved faces)" % (reverted, skipped_edge, skipped_curved))
    say("snap %.2f: %d of %d vertices moved onto the base faces" % (SNAP, moved, len(V3)))
# over the
FEAT = os.environ.get("FEAT", "0") == "1"; FEAT_REC = []
if FEAT:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _feat
    pdo = vtk.vtkPolyData(); pto = vtk.vtkPoints(); pto.SetData(nps.numpy_to_vtk(np.ascontiguousarray(V), deep=True)); pdo.SetPoints(pto)
    co = vtk.vtkCellArray(); conno = np.hstack([np.full((len(T), 1), 3), T]).astype(np.int64).ravel(); co.SetCells(len(T), nps.numpy_to_vtkIdTypeArray(conno, deep=True)); pdo.SetPolys(co)
    ipdo = vtk.vtkImplicitPolyDataDistance(); ipdo.SetInput(pdo)
    FEAT_REACH = float(os.environ.get("FEAT_REACH", 3.0 * h)); FEAT_DEPTH = float(os.environ.get("FEAT_DEPTH", 2.0 * h))
    V3, T3, FEAT_REC = _feat.run_all(V3, T3, V, T, ipdo, h, say=say, deg=float(os.environ.get("EDGE_DEG", "25")), reach=FEAT_REACH, depth=FEAT_DEPTH,
                                     snap=max(SNAP, 0.03), planes=[(c, n) for c, n, on in walls], protect=PROTECT)
    capax = {}
    for wi, (c, n, on) in enumerate(walls): capax[wi] = np.abs((V3 - (c + n * CLIP_OUT)) @ n) < 1e-5
    if SNAP <= 0:
        pdb = vtk.vtkPolyData(); ptb = vtk.vtkPoints(); ptb.SetData(nps.numpy_to_vtk(np.ascontiguousarray(VE), deep=True)); pdb.SetPoints(ptb)
        cb = vtk.vtkCellArray(); conn = np.hstack([np.full((len(TE), 1), 3), TE]).astype(np.int64).ravel(); cb.SetCells(len(TE), nps.numpy_to_vtkIdTypeArray(conn, deep=True)); pdb.SetPolys(cb)
        ipd = vtk.vtkImplicitPolyDataDistance(); ipd.SetInput(pdb)
POLISH = int(os.environ.get("POLISH", "10"))
POLISH_PB = float(os.environ.get("POLISH_PB", "0.1")); POLISH_NM = os.environ.get("POLISH_NM", "1") == "1"
if POLISH > 0:
    snapped = np.zeros(len(V3), bool)
    if SNAP > 0:
        for i in range(len(V3)):
            if abs(ipd.EvaluateFunction(V3[i])) <= SNAP: snapped[i] = True
    for wi, m in capax.items(): snapped |= m
    HOLD_W = float(os.environ.get("HOLD_W", "0.6"))
    for c, n, on in walls: snapped |= np.abs((V3 - (c + n * CLIP_OUT)) @ n) < HOLD_W + CLIP_OUT
    pdr = vtk.vtkPolyData(); ptr = vtk.vtkPoints(); ptr.SetData(nps.numpy_to_vtk(np.ascontiguousarray(V3), deep=True)); pdr.SetPoints(ptr)
    cr = vtk.vtkCellArray(); conn = np.hstack([np.full((len(T3), 1), 3), T3]).astype(np.int64).ravel(); cr.SetCells(len(T3), nps.numpy_to_vtkIdTypeArray(conn, deep=True)); pdr.SetPolys(cr)
    sm = vtk.vtkWindowedSincPolyDataFilter(); sm.SetInputData(pdr); sm.SetNumberOfIterations(POLISH); sm.SetPassBand(POLISH_PB); sm.BoundarySmoothingOff(); sm.FeatureEdgeSmoothingOff(); sm.SetNonManifoldSmoothing(1 if POLISH_NM else 0); sm.NormalizeCoordinatesOn(); sm.Update()
    V4 = nps.vtk_to_numpy(sm.GetOutput().GetPoints().GetData()).astype(float)
    V4[snapped] = V3[snapped]
    mv = np.linalg.norm(V4 - V3, axis=1)
    say("polish %d passes (pass band %g, non-manifold smoothing %s): %d blend vertices moved, median %.4f max %.4f mm; %d face/cap vertices held" % (POLISH, POLISH_PB, "on" if POLISH_NM else "off", int((~snapped).sum()), np.median(mv[~snapped]) if (~snapped).any() else 0, mv.max(), int(snapped.sum())))
    V3 = V4
    POLISH2 = int(os.environ.get("POLISH2", "5"))
    if POLISH2 > 0:
        moved_mask = np.zeros(len(V3), bool)
        for i in range(len(V3)):
            if abs(ipd.EvaluateFunction(V3[i])) <= 1e-6: moved_mask[i] = True
        for wi, m in capax.items(): moved_mask |= m
        for c, n, on in walls: moved_mask |= np.abs((V3 - (c + n * CLIP_OUT)) @ n) < HOLD_W + CLIP_OUT
        hold = moved_mask | ~snapped
        pdr2 = vtk.vtkPolyData(); ptr2 = vtk.vtkPoints(); ptr2.SetData(nps.numpy_to_vtk(np.ascontiguousarray(V3), deep=True)); pdr2.SetPoints(ptr2)
        cr2 = vtk.vtkCellArray(); conn2 = np.hstack([np.full((len(T3), 1), 3), T3]).astype(np.int64).ravel(); cr2.SetCells(len(T3), nps.numpy_to_vtkIdTypeArray(conn2, deep=True)); pdr2.SetPolys(cr2)
        sm2 = vtk.vtkWindowedSincPolyDataFilter(); sm2.SetInputData(pdr2); sm2.SetNumberOfIterations(POLISH2); sm2.SetPassBand(POLISH_PB); sm2.BoundarySmoothingOff(); sm2.FeatureEdgeSmoothingOff(); sm2.SetNonManifoldSmoothing(1 if POLISH_NM else 0); sm2.NormalizeCoordinatesOn(); sm2.Update()
        V5 = nps.vtk_to_numpy(sm2.GetOutput().GetPoints().GetData()).astype(float); V5[hold] = V3[hold]
        mv2 = np.linalg.norm(V5 - V3, axis=1)
        say("polish2 %d passes on %d curved-face vertices: median %.4f max %.4f mm" % (POLISH2, int((~hold).sum()), np.median(mv2[~hold]) if (~hold).any() else 0, mv2.max()))
        V3 = V5
# over the
KEEP_REC = {}
if KEEP:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import _keepweld, gc
    for _nm in ("S1", "kd1", "sdf", "d1", "band", "idx", "P", "d", "DV", "edt", "surf", "clip", "tri", "planes", "pdb", "cb", "ptb"):
        if _nm in globals(): del globals()[_nm]
    gc.collect()
    KEEP_TOL = float(os.environ.get("KEEP_TOL", "0.5")); KEEP_L = float(os.environ.get("KEEP_L", "0.3")); KEEP_VMIN = float(os.environ.get("KEEP_VMIN", "1.0"))
    E_core = _keepweld.core_points(Fw, F0, xs, ys, zs, h, vmin=KEEP_VMIN, say=say)
    if os.environ.get("DUMP"): R.write_stl(os.path.splitext(os.environ["DUMP"])[0] + "_mc.stl", V3, T3)
    KEEP_NM = int(os.environ.get("KEEP_NM", "0")); PINCH = float(os.environ.get("PINCH", "0.05")); KEEP_JOIN = os.environ.get("KEEP_JOIN", "zipper")
    KEEP_RIMSNAP = float(os.environ.get("KEEP_RIMSNAP", "0"))
    KEEP_OPEN_OK = int(os.environ.get("KEEP_OPEN_OK", "0")); KEEP_MICRO = os.environ.get("KEEP_MICRO", "best")   # open edges
    Vk, Tk, KEEP_REC = _keepweld.keep_and_weld(V, T, V3, T3, E_core, KEEP_M, walls, CLIP_OUT, say=say, tol=KEEP_TOL, refine_l=KEEP_L, dump_dir=os.path.dirname(os.path.abspath(out)), nm_ok=KEEP_NM, pinch=PINCH, join=KEEP_JOIN, E_extra=KEEP_E_EXTRA, rim_snap=KEEP_RIMSNAP, h=h, open_ok=KEEP_OPEN_OK, micro=KEEP_MICRO)
    KEEP_SEAM = None
    if isinstance(KEEP_REC, dict):
        KEEP_SEAM = KEEP_REC.pop("seam_xyz", None)
        if KEEP_SEAM is None and isinstance(KEEP_REC.get("merge"), dict): KEEP_SEAM = KEEP_REC["merge"].pop("seam_xyz", None)
    KEEP_REC = _keepweld._jsonable(KEEP_REC)
    KEEP_REC["levers"] = {"KEEP_M": KEEP_M, "KEEP_TOL": KEEP_TOL, "KEEP_L": KEEP_L, "KEEP_VMIN": KEEP_VMIN, "KEEP_NM": KEEP_NM, "PINCH": PINCH, "FADE_IN": FADE_IN, "KEEP_JOIN": KEEP_JOIN, "KEEP_RIMSNAP": KEEP_RIMSNAP, "KEEP_OPEN_OK": KEEP_OPEN_OK, "KEEP_MICRO": KEEP_MICRO}
    if Vk is None:
        say("FAIL: keep-and-weld refused - %s" % KEEP_REC.get("error"))
        json.dump({"tag": TAG, "source": src, "out": out, "keep_weld": KEEP_REC}, open(os.path.join(os.path.dirname(os.path.abspath(out)), "REBUILD_blend.json"), "w"), indent=1)
        _fail("FAIL: keep-and-weld refused - %s (the marching-cubes piece alone was NOT written; KEEP=0 runs the old route)" % KEEP_REC.get("error"))
    V3, T3 = Vk, Tk
R.write_stl(out, V3, T3)
vol = np.einsum("ij,ij->i", V3[T3[:, 0]], np.cross(V3[T3[:, 1]], V3[T3[:, 2]])).sum() / 6.0
hl = R.mesh_health(V3, T3)
say("RESULT %s: %d triangles (welded, cleaned), volume %.1f mm3, health (open, non-manifold) %s" % (out, len(T3), abs(vol), hl))
if KEEP and KEEP_SEAM is not None:
    # recorded
    try:
        np.save(os.path.join(os.path.dirname(os.path.abspath(out)), "keep_seam.npy"), np.asarray(KEEP_SEAM, float))
        KEEP_REC["seam_points"] = int(len(KEEP_SEAM))
    except Exception as _ex: say("seam points not written: %r" % (_ex,))
# kit accept
json.dump({"tag": TAG, "source": src, "out": out, "levers": {"R": RB, "h": h, "W": W, "E": E, "R_SMALL": R_SMALL, "V_BIG": V_BIG, "OPEN": OPEN, "CLIP_OUT": CLIP_OUT,
           "SNAP": SNAP, "EDGE_DEG": float(os.environ.get("EDGE_DEG", "25")), "FLAT_DEG": float(os.environ.get("FLAT_DEG", "0.5")), "POLISH": POLISH,
           "POLISH2": int(os.environ.get("POLISH2", "5")), "POLISH_PB": POLISH_PB, "POLISH_NM": int(POLISH_NM), "HOLD_W": float(os.environ.get("HOLD_W", "0.6")), "WELD": WELD, "SAMP": SAMP,
           "FEAT": int(FEAT), "FEAT_REACH": float(os.environ.get("FEAT_REACH", 3.0 * h)), "FEAT_DEPTH": float(os.environ.get("FEAT_DEPTH", 2.0 * h))},
           "feature_restore": FEAT_REC, "KEEP": int(KEEP), "FADE_IN": FADE_IN, "keep_weld": KEEP_REC,
           "walls": [[float(v) for v in c] + [float(v) for v in n] for c, n, on in walls], "protect": PROTECT, "protect_w": PROTECT_W, "inside_test_31aj": INSIDE, "zones_31aj": ZONE_REC, "zone_w": ZONE_W, "added_mm3_full": round(ADDED_FULL, 1), "added_mm3_faded": round(ADDED_FADED, 1),
           "triangles": int(len(T3)), "volume_mm3": round(abs(float(vol)), 1), "health_open_nonmanifold": [int(x) for x in hl]},
          open(os.path.join(os.path.dirname(os.path.abspath(out)), "REBUILD_blend.json"), "w"), indent=1)

import io, json, os, sys, time
import numpy as np
from scipy import ndimage
sys.path.insert(0, os.environ["KIT_HOME"])
import kitlib as K, Part, FreeCAD
import kitlib_render as KR

V = FreeCAD.Vector
t0 = time.time()
SRC = os.path.dirname(os.path.abspath(__file__))
HERE = os.environ.get("CC_WORK") or SRC
_TAG = os.environ.get("LK_TAG", "")
STATUS = os.path.join(HERE, "status_ccextract%s.json" % _TAG)

SHAPE = os.environ["CC_SHAPE"]
BOX = [float(t) for t in os.environ["CC_BOX"].split()]
DEV = float(os.environ.get("CC_DEV", "0.08"))
H = float(os.environ.get("CC_H", "0.15"))
R_CLOSE = float(os.environ.get("CC_CLOSE", "1.2"))
R_OPEN = float(os.environ.get("CC_OPEN", "0.35"))
SIGMA = float(os.environ.get("CC_SIGMA", "0.45"))
PAD = float(os.environ.get("CC_PAD", "2.0"))
OUT_STL = os.environ.get("CC_OUT_STL", "")
GROW = float(os.environ.get("CC_GROW", "0") or 0)
GROW_SHRINK = float(os.environ.get("CC_GROW_SHRINK", "0.15") or 0)
if GROW < 0 or (GROW > 0 and GROW_SHRINK <= 0):
    print("FAIL: CC_GROW %.3f / CC_GROW_SHRINK %.3f - a copy for kit union must grow (> 0) in the edit zone AND shrink (> 0) at the "
          "walls: a copy that coincides with the body there is unioned as a patchwork of hair-thin slivers" % (GROW, GROW_SHRINK), flush=True)
    raise SystemExit(2)

# open edges
# open edges
# open edges
_band_chk = float(os.environ.get("CC_BAND", "4.0"))
_box_chk = [float(t) for t in os.environ["CC_BOX"].split()]
_min_dim = min(_box_chk[1] - _box_chk[0], _box_chk[3] - _box_chk[2], _box_chk[5] - _box_chk[4])
if _band_chk < max(3.0, 0.25 * _min_dim):
    print("WARNING: band %.2f mm is narrow for a box whose smallest dimension is %.1f mm. A steep "
          "cross-fade fragments the field - measured 42 regions and 56 open edges at band 1.5 on a 17 mm "
          "box, against 1 region and 0 open edges at band 4.0. Watch the region count."
          % (_band_chk, _min_dim), flush=True)


def say(*a):
    print(*a, flush=True)


say("== extract the region's surface from the cleaned field ==")
MESH_MODE = SHAPE.lower().endswith(".stl")
if MESH_MODE:
    s = None
    _b = open(SHAPE, "rb").read(); _n = int(np.frombuffer(_b[80:84], "<u4")[0])
    _rec = np.frombuffer(_b[84:84 + _n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    _tri = _rec["v"].reshape(-1, 3, 3).astype(np.float64)
    _q = np.round(_tri.reshape(-1, 3) / 1e-6).astype(np.int64)
    _u, _inv = np.unique(_q, axis=0, return_inverse=True)
    Vv = _u * 1e-6; T = _inv.reshape(-1, 3)
    T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
    F = np.full(len(T), -1, int)
    del _b, _rec, _tri, _q, _u, _inv
    say("body: MESH %s - %d vertices, %d triangles (MESH MODE: the field is this mesh's own; keepers and frozen regions "
        "from CC_REGION_MESHES)" % (os.path.basename(SHAPE), len(Vv), len(T)))
else:
    s = Part.Shape()
    s.importBrep(SHAPE)
    say("body: %d faces, %d solid(s), valid=%s" % (len(s.Faces), len(s.Solids), s.isValid()))
    Vv, T, F = K.tess(s, DEV)
    Vv = np.asarray(Vv, float)
    T = np.asarray(T, int)
    F = np.asarray(F, int)
    say("mesh: %d vertices, %d triangles (dev %.3f)" % (len(Vv), len(T), DEV))

_REGION_IDS = {}


def _region_face_id(name):
    """mesh mode: the synthetic face id of an atlas region, marking the body triangles on that region's surface"""
    if name in _REGION_IDS:
        return _REGION_IDS[name]
    rdir = os.environ.get("CC_REGION_MESHES", "").strip()
    p_ = os.path.join(rdir, name + ".stl") if rdir else ""
    if not rdir or not os.path.isfile(p_):
        say("FAIL: mesh mode needs CC_REGION_MESHES=<folder of <region>.stl> holding %s.stl (kit mesh regions writes them)" % name)
        raise SystemExit(2)
    rv, rt = KR.read_stl(p_); rv = np.asarray(rv, float); rt = np.asarray(rt, int)
    rlo = rv.min(0); rhi = rv.max(0)
    rc = rv[rt].mean(1)
    near = ((rc[:, 0] > BOX[0] - 8) & (rc[:, 0] < BOX[1] + 8) & (rc[:, 1] > BOX[2] - 8) & (rc[:, 1] < BOX[3] + 8)
            & (rc[:, 2] > BOX[4] - 8) & (rc[:, 2] < BOX[5] + 8))
    fid = 100000 + len(_REGION_IDS); _REGION_IDS[name] = fid
    if not near.any():
        say("  region %s: no surface near the box" % name); return fid
    rt = rt[near]
    bc = Vv[T].mean(1)
    cand = np.where((bc[:, 0] > rlo[0] - 0.5) & (bc[:, 0] < rhi[0] + 0.5) & (bc[:, 1] > rlo[1] - 0.5) & (bc[:, 1] < rhi[1] + 0.5)
                    & (bc[:, 2] > rlo[2] - 0.5) & (bc[:, 2] < rhi[2] + 0.5) & (F < 0))[0]
    if len(cand):
        d_ = KR.point_tri_dist(bc[cand], rv, rt)
        hit = cand[d_ <= 0.08]
        F[hit] = fid
        say("  region %s: %d body triangle(s) on its surface near the box (of %d candidates)" % (name, len(hit), len(cand)))
    return fid

_SPINE_RULE = all(os.environ.get(k_, "").strip() for k_ in ("CC_SPINE_X", "CC_SPINE_Z", "CC_VANE_AREA")) and not MESH_MODE
if MESH_MODE and all(os.environ.get(k_, "").strip() for k_ in ("CC_SPINE_X", "CC_SPINE_Z", "CC_VANE_AREA")):
    say("keepers: the built-in vane/spine rule needs B-rep faces and is OFF in mesh mode - name the vanes and spine in CC_KEEP_REGIONS")
SPINE_X = float(os.environ.get("CC_SPINE_X", "0") or 0)
SPINE_Z = float(os.environ.get("CC_SPINE_Z", "0") or 0)
VANE_AREA = float(os.environ.get("CC_VANE_AREA", "0") or 0)
KEEPBAND = float(os.environ.get("CC_KEEPBAND", "0.6"))
keepf = set()
vanef = set()
spinef = set()
if not _SPINE_RULE:
    say("keepers: the built-in vane/spine rule is OFF (CC_SPINE_X, CC_SPINE_Z and CC_VANE_AREA are not all set);"
        " keepers come from CC_KEEP_REGIONS / CC_KEEP_FACES_AT / CC_FREEZE_REGIONS")
for i_, f_ in (enumerate(s.Faces) if _SPINE_RULE else ()):
    bb_ = f_.BoundBox
    if (bb_.XMax < BOX[0] - 8 or bb_.XMin > BOX[1] + 8 or bb_.YMax < BOX[2] - 8
            or bb_.YMin > BOX[3] + 8 or bb_.ZMax < BOX[4] - 8 or bb_.ZMin > BOX[5] + 8):
        continue
    try:
        ob_ = f_.optimalBoundingBox()
    except Exception:
        ob_ = bb_
    pr_ = f_.ParameterRange
    try:
        n_ = f_.normalAt(0.5 * (pr_[0] + pr_[1]), 0.5 * (pr_[2] + pr_[3]))
    except Exception:
        n_ = V(0, 0, 0)
    t_ = type(f_.Surface).__name__
    if f_.Area >= VANE_AREA and ob_.XMin < BOX[0] - 1 and ob_.XMax > BOX[1] + 1 and abs(n_.x) < 0.30:
        keepf.add(i_); vanef.add(i_)
    elif t_ == "Plane" and abs(abs(n_.x) - 1.0) < 1e-3 and abs(abs(f_.Surface.Position.x) - SPINE_X) < 0.05:
        keepf.add(i_); spinef.add(i_)
    elif abs(ob_.ZMin - SPINE_Z) < 0.05 and abs(ob_.ZMax - SPINE_Z) < 0.05:
        keepf.add(i_); spinef.add(i_)
    elif ob_.ZMin > SPINE_Z + 2.5 and n_.z > 0.8:
        keepf.add(i_); spinef.add(i_)
def _manifest_path():
    """the atlas FACE manifest (region -> from_faces, 1-based face numbers of the model of record). A lever with no
    default in the kit: `kit mesh` fills CC_ATLAS_MANIFEST from the project's atlas record when it can; otherwise
    name it. (It defaulted to one project's ATLAS folder while this script lived there.)"""
    p_ = os.environ.get("CC_ATLAS_MANIFEST", "").strip()
    if not p_ or not os.path.isfile(p_):
        say("FAIL: CC_KEEP_REGIONS / CC_FREEZE_REGIONS need the atlas face manifest - set CC_ATLAS_MANIFEST=<manifest.json>"
            " (region -> from_faces). None is set%s." % (" and %s does not exist" % p_ if p_ else ""))
        raise SystemExit(2)
    return p_


_KR = [r_.strip() for r_ in os.environ.get("CC_KEEP_REGIONS", "").split(",") if r_.strip()]
if _KR and MESH_MODE:
    _nk0 = len(keepf)
    for r_ in _KR:
        keepf.add(_region_face_id(r_))
    say("  CC_KEEP_REGIONS %s (mesh mode): %d region surface(s) are keepers" % (",".join(_KR), len(keepf) - _nk0))
elif _KR:
    _manp_k = _manifest_path()
    _man_k = json.load(io.open(_manp_k, encoding="utf-8"))
    _nk0 = len(keepf)
    for r_ in _KR:
        for f_ in _man_k[r_]["from_faces"]:
            i_ = int(f_) - 1
            bb_ = s.Faces[i_].BoundBox
            if not (bb_.XMax < BOX[0] - 8 or bb_.XMin > BOX[1] + 8 or bb_.YMax < BOX[2] - 8
                    or bb_.YMin > BOX[3] + 8 or bb_.ZMax < BOX[4] - 8 or bb_.ZMin > BOX[5] + 8):
                keepf.add(i_)
    say("  CC_KEEP_REGIONS %s: %d more keeper face(s) near the box" % (",".join(_KR), len(keepf) - _nk0))
_KFA = [q_.split() for q_ in os.environ.get("CC_KEEP_FACES_AT", "").split(";") if q_.strip()]
if _KFA and MESH_MODE:
    say("FAIL: CC_KEEP_FACES_AT needs B-rep faces; in mesh mode hold a surface with CC_KEEP_REGIONS / CC_FREEZE_REGIONS instead")
    raise SystemExit(2)
if _KFA:
    _nk1 = len(keepf)
    for q_ in _KFA:
        pq_ = V(float(q_[0]), float(q_[1]), float(q_[2])); vq_ = Part.Vertex(pq_); best_ = []
        for i_, f_ in enumerate(s.Faces):
            bb_ = f_.BoundBox
            if (bb_.XMin - 0.5 <= pq_.x <= bb_.XMax + 0.5 and bb_.YMin - 0.5 <= pq_.y <= bb_.YMax + 0.5
                    and bb_.ZMin - 0.5 <= pq_.z <= bb_.ZMax + 0.5):
                best_.append((f_.distToShape(vq_)[0], i_))
        best_.sort()
        if not best_ or best_[0][0] > 0.3:
            say("  CC_KEEP_FACES_AT %s: NO face within 0.3 mm (nearest %s)" % (" ".join(q_), best_[:1])); continue
        for d_, i_ in best_:
            if d_ <= best_[0][0] + 0.02:
                keepf.add(i_)
        say("  CC_KEEP_FACES_AT %s: face(s) %s at %.3f mm" % (" ".join(q_), [i_ + 1 for d_, i_ in best_ if d_ <= best_[0][0] + 0.02], best_[0][0]))
    say("  CC_KEEP_FACES_AT: %d more keeper face(s)" % (len(keepf) - _nk1))
say("keepers: %d face(s) - %d vane, %d spine - protected to %.2f mm"
    % (len(keepf), len(vanef), len(spinef), KEEPBAND))

g0 = np.array([BOX[0], BOX[2], BOX[4]]) - PAD
g1 = np.array([BOX[1], BOX[3], BOX[5]]) + PAD
nx, ny, nz = [max(8, int(np.ceil((g1[a] - g0[a]) / H)) + 1) for a in range(3)]
say("grid %d x %d x %d = %.2f M cells at %.3f mm (pad %.2f mm of air all round)"
    % (nx, ny, nz, nx * ny * nz / 1e6, H, PAD))

A, Bv, Cv = Vv[T[:, 0]], Vv[T[:, 1]], Vv[T[:, 2]]
tmin = np.minimum(np.minimum(A, Bv), Cv)
tmax = np.maximum(np.maximum(A, Bv), Cv)
sel = ((tmax[:, 0] >= g0[0]) & (tmin[:, 0] <= g1[0]) & (tmax[:, 1] >= g0[1]) & (tmin[:, 1] <= g1[1]))
Ai, Bi, Ci = A[sel], Bv[sel], Cv[sel]
nrm = np.cross(Bi - Ai, Ci - Ai)
ok = np.linalg.norm(nrm, axis=1) > 1e-12
Ai, Bi, Ci, nrm = Ai[ok], Bi[ok], Ci[ok], nrm[ok]
signz = np.sign(nrm[:, 2])
say("triangles over the footprint: %d" % len(Ai))

i0 = np.maximum(0, np.floor((np.minimum(np.minimum(Ai[:, 0], Bi[:, 0]), Ci[:, 0]) - g0[0]) / H).astype(int))
i1 = np.minimum(nx - 1, np.ceil((np.maximum(np.maximum(Ai[:, 0], Bi[:, 0]), Ci[:, 0]) - g0[0]) / H).astype(int))
j0 = np.maximum(0, np.floor((np.minimum(np.minimum(Ai[:, 1], Bi[:, 1]), Ci[:, 1]) - g0[1]) / H).astype(int))
j1 = np.minimum(ny - 1, np.ceil((np.maximum(np.maximum(Ai[:, 1], Bi[:, 1]), Ci[:, 1]) - g0[1]) / H).astype(int))
ax, ay = Ai[:, 0], Ai[:, 1]
e1x, e1y = Bi[:, 0] - ax, Bi[:, 1] - ay
e2x, e2y = Ci[:, 0] - ax, Ci[:, 1] - ay
den = e1x * e2y - e2x * e1y
hits = {}
_JX, _JY = H * 1.41421356e-4, H * 1.73205081e-4
for t in np.where(np.abs(den) > 1e-14)[0]:
    for ii in range(i0[t], i1[t] + 1):
        px = g0[0] + ii * H + _JX
        for jj in range(j0[t], j1[t] + 1):
            py = g0[1] + jj * H + _JY
            wx, wy = px - ax[t], py - ay[t]
            u = (wx * e2y[t] - e2x[t] * wy) / den[t]
            v = (e1x[t] * wy - wx * e1y[t]) / den[t]
            if u < 0.0 or v < 0.0 or u + v > 1.0:
                continue
            p = Ai[t] + u * (Bi[t] - Ai[t]) + v * (Ci[t] - Ai[t])
            hits.setdefault((ii, jj), []).append((p[2], signz[t]))

G = np.zeros((nx, ny, nz), bool)
for (ii, jj), lst in hits.items():
    lst.sort()
    w = 0
    for a in range(len(lst) - 1):
        w += lst[a][1]
        if w != 0:
            ka = int(np.ceil((lst[a][0] - g0[2]) / H))
            kb = int(np.floor((lst[a + 1][0] - g0[2]) / H))
            if kb >= 0 and ka < nz:
                G[ii, jj, max(0, ka):min(nz, kb + 1)] = True
vox0 = int(G.sum())
say("voxelised: %d cells = %.1f mm3, %.0f s" % (vox0, vox0 * H ** 3, time.time() - t0))

_tv = time.time()
VOTE, _occ3 = KR.inside_vote(Vv, T, g0, (nx, ny, nz), H)
H_VOTE, G0_VOTE = H, g0.copy()
SIGNFAR = float(os.environ.get("CC_SIGNFAR", "1.5"))
say("inside/outside vote, 3 ray directions: %d solid cells; single-direction disagreements x %d, y %d, z %d (%.0f s)"
    % (int(VOTE.sum()), int((_occ3[0] != VOTE).sum()), int((_occ3[1] != VOTE).sum()),
       int((_occ3[2] != VOTE).sum()), time.time() - _tv))
SIGN_FIX = {}


def _fix_sign(field, g0_, h_, tag):
    """flip the sign wherever the vote contradicts it, more than SIGNFAR vote-cells from the surface"""
    ii_ = np.clip(np.rint((np.arange(field.shape[0]) * h_ + g0_[0] - G0_VOTE[0]) / H_VOTE).astype(int), 0, VOTE.shape[0] - 1)
    jj_ = np.clip(np.rint((np.arange(field.shape[1]) * h_ + g0_[1] - G0_VOTE[1]) / H_VOTE).astype(int), 0, VOTE.shape[1] - 1)
    kk_ = np.clip(np.rint((np.arange(field.shape[2]) * h_ + g0_[2] - G0_VOTE[2]) / H_VOTE).astype(int), 0, VOTE.shape[2] - 1)
    vo = VOTE[np.ix_(ii_, jj_, kk_)]
    bad = (np.abs(field) > SIGNFAR * H_VOTE) & ((field < 0) != vo)
    nb = int(bad.sum())
    deep = float(np.abs(field[bad]).max()) if nb else 0.0
    out = np.where(bad, -field, field).astype(field.dtype)
    SIGN_FIX[tag] = {"cells": nb, "deepest_mm": round(deep, 3)}
    say("  SIGN CHECK (%s): %d cell(s) where the nearest triangle's sign contradicted the vote, deepest %.2f mm - %s"
        % (tag, nb, deep, "corrected" if nb else "none to correct"))
    return out
if not vox0:
    say("FAIL: no material in the box.")
    raise SystemExit(1)


import vtk
from vtk.util import numpy_support

# over the
_vtk_log = os.path.join(HERE, "vtk_messages.log")
_ow = vtk.vtkFileOutputWindow()
_ow.SetFileName(_vtk_log)
_ow.SetFlush(0)
_ow.SetInstance(_ow)
vtk.vtkOutputWindow.SetInstance(_ow)
vtk.vtkObject.GlobalWarningDisplayOff()

t = time.time()
HALO = float(os.environ.get("CC_HALO", "6.0"))
keep = ((tmax[:, 0] >= g0[0] - HALO) & (tmin[:, 0] <= g1[0] + HALO)
        & (tmax[:, 1] >= g0[1] - HALO) & (tmin[:, 1] <= g1[1] + HALO)
        & (tmax[:, 2] >= g0[2] - HALO) & (tmin[:, 2] <= g1[2] + HALO))
Tl = T[keep]
used = np.unique(Tl)
remap = -np.ones(len(Vv), np.int64)
remap[used] = np.arange(len(used))
Vl = Vv[used]
Tl = remap[Tl]
pts = vtk.vtkPoints()
pts.SetData(numpy_support.numpy_to_vtk(np.ascontiguousarray(Vl, np.float64), deep=True))
cells = vtk.vtkCellArray()
conn = np.empty((len(Tl), 4), np.int64)
conn[:, 0] = 3
conn[:, 1:] = Tl
cells.SetCells(len(Tl), numpy_support.numpy_to_vtkIdTypeArray(conn.ravel(), deep=True))
body_pd = vtk.vtkPolyData()
body_pd.SetPoints(pts)
body_pd.SetPolys(cells)
say("local polydata for the distance query: %d of %d triangles within %.1f mm of the grid (%.0f s)"
    % (len(Tl), len(T), HALO, time.time() - t))

# over the
SLAB_CELLS = 10_000_000


def _sample(imp_, g0_, dims_, h_, tag_):
    n0_, n1_, n2_ = dims_
    per = max(2, int(SLAB_CELLS // max(1, n0_ * n1_)))
    out = np.empty((n0_, n1_, n2_), np.float32)
    k = 0; ts_ = time.time(); nsl = 0
    while k < n2_:
        k1 = min(n2_, k + per)
        if k1 == n2_ - 1:
            k1 = n2_
        s_ = vtk.vtkSampleFunction()
        s_.SetImplicitFunction(imp_)
        s_.SetSampleDimensions(n0_, n1_, k1 - k)
        s_.SetModelBounds(float(g0_[0]), float(g0_[0] + (n0_ - 1) * h_), float(g0_[1]), float(g0_[1] + (n1_ - 1) * h_),
                          float(g0_[2] + k * h_), float(g0_[2] + (k1 - 1) * h_))
        s_.ComputeNormalsOff(); s_.SetOutputScalarTypeToFloat(); s_.Update()
        a_ = numpy_support.vtk_to_numpy(s_.GetOutput().GetPointData().GetScalars()).reshape(k1 - k, n1_, n0_).transpose(2, 1, 0)
        out[:, :, k:k1] = a_
        nsl += 1
        say("  %s: slab %d (z planes %d-%d of %d) %.0f s" % (tag_, nsl, k, k1 - 1, n2_, time.time() - ts_))
        k = k1
    return out


t = time.time()
imp = vtk.vtkImplicitPolyDataDistance()
imp.SetInput(body_pd)
raw = _sample(imp, g0, (nx, ny, nz), H, "distance, coarse grid")
say("true signed distance over the grid: %.0f s, range %.2f .. %.2f mm"
    % (time.time() - t, raw.min(), raw.max()))
_ZB = [[float(t_) for t_ in b_.split()] for b_ in os.environ.get("CC_ZBRIDGE", "").split(";") if b_.strip()]


def _zbridge(f, g0_, h_, tag):
    if not _ZB:
        return f
    n0, n1, n2 = f.shape
    xs = g0_[0] + np.arange(n0) * h_; ys = g0_[1] + np.arange(n1) * h_; zs = g0_[2] + np.arange(n2) * h_
    for b_ in _ZB:
        k0 = int(np.clip(round((b_[4] - g0_[2]) / h_), 0, n2 - 1)); k1 = int(np.clip(round((b_[5] - g0_[2]) / h_), 0, n2 - 1))
        if k1 - k0 < 2:
            continue
        dxy = np.minimum(np.minimum(xs - b_[0], b_[1] - xs)[:, None], np.minimum(ys - b_[2], b_[3] - ys)[None, :])
        mxy = np.clip(dxy / 1.0, 0.0, 1.0); mxy = (mxy * mxy * (3.0 - 2.0 * mxy)).astype(np.float32)
        A = f[:, :, k0].copy(); B = f[:, :, k1].copy(); ch = 0
        for k in range(k0 + 1, k1):
            t_ = (zs[k] - zs[k0]) / (zs[k1] - zs[k0])
            new = f[:, :, k] + mxy * ((1.0 - t_) * A + t_ * B - f[:, :, k])
            ch += int(((new < 0) != (f[:, :, k] < 0)).sum()); f[:, :, k] = new
        say("  ZBRIDGE (%s) x %.1f..%.1f y %.1f..%.1f between the sections at z %.2f and %.2f: %d cell(s) changed side"
            % (tag, b_[0], b_[1], b_[2], b_[3], zs[k0], zs[k1], ch))
    return f

_UNION = [p_.strip() for p_ in os.environ.get("CC_UNION_STL", "").split(";") if p_.strip()]


def _union(f, g0_, h_, shape_, tag):
    if not _UNION:
        return f
    import vtk as _vtk
    from vtk.util import numpy_support as _ns
    n0_, n1_, n2_ = shape_
    for p_ in _UNION:
        if not os.path.isfile(p_):
            say("FAIL: CC_UNION_STL names %s, which does not exist" % p_); raise SystemExit(2)
        uv, ut = KR.read_stl(p_); uv = np.asarray(uv, float); ut = np.asarray(ut, int)
        _q = np.round(uv / 1e-6).astype(np.int64); _u, _inv = np.unique(_q, axis=0, return_inverse=True)
        uv = _u * 1e-6; ut = _inv.reshape(-1)[ut]
        ut = ut[(ut[:, 0] != ut[:, 1]) & (ut[:, 1] != ut[:, 2]) & (ut[:, 0] != ut[:, 2])]
        _P = uv[ut]; _vol = float((np.cross(_P[:, 1], _P[:, 2]) * _P[:, 0]).sum() / 6.0)
        if _vol <= 0:
            say("FAIL: %s is wound inward (signed volume %.1f mm3) - the union would read as air" % (os.path.basename(p_), _vol))
            raise SystemExit(2)
        _e = np.sort(np.concatenate([ut[:, [0, 1]], ut[:, [1, 2]], ut[:, [2, 0]]]), axis=1)
        _, _cnt = np.unique(_e, axis=0, return_counts=True)
        if (_cnt != 2).any():
            say("FAIL: %s is not closed (%d edge(s) not shared by exactly two triangles)" % (os.path.basename(p_), int((_cnt != 2).sum())))
            raise SystemExit(2)
        _pts = _vtk.vtkPoints(); _pts.SetData(_ns.numpy_to_vtk(np.ascontiguousarray(uv, np.float64), deep=True))
        _cells = _vtk.vtkCellArray(); _conn = np.empty((len(ut), 4), np.int64); _conn[:, 0] = 3; _conn[:, 1:] = ut
        _cells.SetCells(len(ut), _ns.numpy_to_vtkIdTypeArray(_conn.ravel(), deep=True))
        _pd = _vtk.vtkPolyData(); _pd.SetPoints(_pts); _pd.SetPolys(_cells)
        _imp = _vtk.vtkImplicitPolyDataDistance(); _imp.SetInput(_pd)
        _d = _sample(_imp, g0_, (n0_, n1_, n2_), h_, "union %s, %s" % (os.path.basename(p_), tag))
        _added = int(((_d < 0) & (f >= 0)).sum())
        _lo = uv.min(0); _hi = uv.max(0)
        _margin = min(_lo[0] - g0_[0], _lo[1] - g0_[1], _lo[2] - g0_[2],
                      g0_[0] + (n0_ - 1) * h_ - _hi[0], g0_[1] + (n1_ - 1) * h_ - _hi[1], g0_[2] + (n2_ - 1) * h_ - _hi[2])
        f = np.minimum(f, _d).astype(np.float32)
        say("  UNION (%s): %s - %d triangles, %.0f mm3, %d cell(s) turned solid; solid's box clears the grid by %.1f mm%s"
            % (tag, os.path.basename(p_), len(ut), _vol, _added, _margin, "" if _margin >= 2.0 else "  ** TOO CLOSE TO THE WALL - grow the box **"))
        del _d
    return f


raw = _fix_sign(raw, g0, H, "coarse")
raw = _zbridge(raw, g0, H, "coarse")
raw = _union(raw, g0, H, (nx, ny, nz), "coarse")


def ball(rmm):
    r = max(1, int(round(rmm / H)))
    z, y, x = np.ogrid[-r:r + 1, -r:r + 1, -r:r + 1]
    return (x * x + y * y + z * z) <= r * r + 1e-9


bc, bo = ball(R_CLOSE), ball(R_OPEN)
t = time.time()
cln = ndimage.grey_dilation(ndimage.grey_erosion(raw, footprint=bc), footprint=bc)
say("CLOSE r=%.2f in distance space: gaps under %.2f mm welded (%.0f s)" % (R_CLOSE, 2 * R_CLOSE, time.time() - t))
t = time.time()
cln = ndimage.grey_erosion(ndimage.grey_dilation(cln, footprint=bo), footprint=bo)
say("OPEN  r=%.2f in distance space: features under %.2f mm removed (%.0f s)" % (R_OPEN, 2 * R_OPEN, time.time() - t))
cln = ndimage.gaussian_filter(cln, SIGMA / H, mode="nearest")

HF = float(os.environ.get("CC_HFINE", "0"))
if HF > 0 and HF < H:
    t = time.time()
    fx, fy, fz = [max(8, int(np.ceil((g1[a] - g0[a]) / HF)) + 1) for a in range(3)]
    say("fine grid for the output: %d x %d x %d = %.2f M cells at %.3f mm"
        % (fx, fy, fz, fx * fy * fz / 1e6, HF))
    cln = ndimage.zoom(cln, (fx / float(nx), fy / float(ny), fz / float(nz)), order=1)
    say("  cleaned field upsampled %.0f s" % (time.time() - t))
    t = time.time()
    raw = _sample(imp, g0, (fx, fy, fz), HF, "distance, fine grid")
    say("  body distance re-sampled on the fine grid, %.0f s" % (time.time() - t))
    raw = _fix_sign(raw, g0, HF, "fine")
    raw = _zbridge(raw, g0, HF, "fine")
    raw = _union(raw, g0, HF, (fx, fy, fz), "fine")
    nx, ny, nz, H = fx, fy, fz, HF
    cln = cln[:nx, :ny, :nz]
    if cln.shape != raw.shape:
        pad = [(0, max(0, raw.shape[a] - cln.shape[a])) for a in range(3)]
        cln = np.pad(cln, pad, mode="edge")[:nx, :ny, :nz]

t = time.time()
ktri = T[np.isin(F, list(keepf))] if keepf else np.zeros((0, 3), int)
if len(ktri):
    ku = np.unique(ktri)
    kr = -np.ones(len(Vv), np.int64)
    kr[ku] = np.arange(len(ku))
    kp = vtk.vtkPoints()
    kp.SetData(numpy_support.numpy_to_vtk(np.ascontiguousarray(Vv[ku], np.float64), deep=True))
    kc = vtk.vtkCellArray()
    kconn = np.empty((len(ktri), 4), np.int64)
    kconn[:, 0] = 3
    kconn[:, 1:] = kr[ktri]
    kc.SetCells(len(ktri), numpy_support.numpy_to_vtkIdTypeArray(kconn.ravel(), deep=True))
    keep_pd = vtk.vtkPolyData()
    keep_pd.SetPoints(kp)
    keep_pd.SetPolys(kc)
    kimp = vtk.vtkImplicitPolyDataDistance()
    kimp.SetInput(keep_pd)
    d_keep = np.abs(_sample(kimp, g0, (nx, ny, nz), H, "distance to the keepers"))
    say("distance to the keepers: %d triangles, %.0f s" % (len(ktri), time.time() - t))
else:
    d_keep = np.full((nx, ny, nz), 1e6, np.float32)
    say("no keeper faces found - nothing is being protected, check the classification")

EDITREACH = float(os.environ.get("CC_EDITREACH", "0"))
EDITRAMP = float(os.environ.get("CC_EDITRAMP", "1.0"))


def _dist_to(faces):
    """distance from every grid cell to the given face set, on the current grid"""
    tri = T[np.isin(F, list(faces))] if faces else np.zeros((0, 3), int)
    if not len(tri):
        return np.full((nx, ny, nz), 1e6, np.float32)
    uu = np.unique(tri)
    rr = -np.ones(len(Vv), np.int64)
    rr[uu] = np.arange(len(uu))
    pp = vtk.vtkPoints()
    pp.SetData(numpy_support.numpy_to_vtk(np.ascontiguousarray(Vv[uu], np.float64), deep=True))
    cc = vtk.vtkCellArray()
    cn = np.empty((len(tri), 4), np.int64)
    cn[:, 0] = 3
    cn[:, 1:] = rr[tri]
    cc.SetCells(len(tri), numpy_support.numpy_to_vtkIdTypeArray(cn.ravel(), deep=True))
    pdd = vtk.vtkPolyData()
    pdd.SetPoints(pp)
    pdd.SetPolys(cc)
    imp_ = vtk.vtkImplicitPolyDataDistance()
    imp_.SetInput(pdd)
    return np.abs(_sample(imp_, g0, (nx, ny, nz), H, "distance to %d face(s)" % len(faces)))


w_edit = None
if EDITREACH > 0:
    _t = time.time()
    d_vane = _dist_to(vanef)
    d_spine = _dist_to(spinef)
    d_both = np.maximum(d_vane, d_spine)
    w_edit = np.clip((EDITREACH + EDITRAMP - d_both) / max(EDITRAMP, 1e-6), 0.0, 1.0)
    w_edit = (w_edit * w_edit * (3.0 - 2.0 * w_edit)).astype(np.float32)
    say("edit mask: within %.2f mm of BOTH a vane and the spine (ramp %.2f), %.1f pct of cells open to "
        "cleaning, %.0f s" % (EDITREACH, EDITRAMP, 100.0 * (w_edit > 0.5).mean(), time.time() - _t))

BAND = float(os.environ.get("CC_BAND", "4.0"))
ii = (np.arange(nx) * H + g0[0])[:, None, None]
jj = (np.arange(ny) * H + g0[1])[None, :, None]
kk = (np.arange(nz) * H + g0[2])[None, None, :]
d_wall = np.minimum(ii - BOX[0], BOX[1] - ii)
d_wall = np.minimum(d_wall, jj - BOX[2])
d_wall = np.minimum(d_wall, BOX[3] - jj)
d_wall = np.minimum(d_wall, kk - BOX[4])
d_wall = np.minimum(d_wall, BOX[5] - kk).astype(np.float32)
w = np.clip(d_wall / max(BAND, 1e-6), 0.0, 1.0)
w = w * w * (3.0 - 2.0 * w)
KEEP_HARD = float(os.environ.get("CC_KEEPHARD", "0.35"))
# released
_KRB = [b_.split() for b_ in os.environ.get("CC_KEEP_RELEASE_BOXES", "").split(";") if b_.strip()]
if _KRB:
    _rel = None
    for _b in _KRB:
        _b = [float(t_) for t_ in _b]
        _d = np.minimum(np.minimum(np.minimum(ii - _b[0], _b[1] - ii), np.minimum(jj - _b[2], _b[3] - jj)),
                        np.minimum(kk - _b[4], _b[5] - kk)).astype(np.float32)
        _w = np.clip((_d + 1.0) / 1.0, 0.0, 1.0); _w = _w * _w * (3.0 - 2.0 * _w)
        _rel = _w if _rel is None else np.maximum(_rel, _w)
        del _d
    d_keep = (d_keep + _rel * 1e3).astype(np.float32)
    say("  CC_KEEP_RELEASE_BOXES: keepers released in %d box(es), %.1f pct of cells" % (len(_KRB), 100.0 * (_rel > 0.5).mean()))
    del _rel
wk = np.clip((d_keep - KEEP_HARD) / max(KEEPBAND - KEEP_HARD, 1e-6), 0.0, 1.0)
wk = wk * wk * (3.0 - 2.0 * wk)
if w_edit is not None:
    w = w * w_edit

# MESH_JOB
_EBS = [b_.split() for b_ in os.environ.get("CC_EDITBOX", "").split(";") if b_.strip()]
if _EBS and all(len(b_) == 6 for b_ in _EBS):
    _ebr = float(os.environ.get("CC_EDITBOXRAMP", "1.0"))
    _webu = None
    for EDITBOX in _EBS:
        _eb = [float(t_) for t_ in EDITBOX]
        _din = np.minimum(np.minimum(np.minimum(ii - _eb[0], _eb[1] - ii), np.minimum(jj - _eb[2], _eb[3] - jj)),
                          np.minimum(kk - _eb[4], _eb[5] - kk)).astype(np.float32)
        _web = np.clip(_din / max(_ebr, 1e-6), 0.0, 1.0)
        _web = _web * _web * (3.0 - 2.0 * _web)
        _webu = _web if _webu is None else np.maximum(_webu, _web)
        del _din
        say("  EDIT BOX %s (ramp %.2f mm)" % (" ".join("%.1f" % v for v in _eb), _ebr))
    w = w * _webu
    say("  edit region (%d box(es)): cleaning allowed in %.1f pct of cells, the body's own everywhere else"
        % (len(_EBS), 100.0 * (_webu > 0.5).mean()))
    del _web, _webu

FREEZE = [r_.strip() for r_ in os.environ.get("CC_FREEZE_REGIONS", "").split(",") if r_.strip()]
_ffn = set(); _fz_names = {}
if FREEZE:
    if MESH_MODE:
        for r_ in FREEZE:
            fid_ = _region_face_id(r_)
            if (F == fid_).any():
                _ffn.add(fid_); _fz_names[fid_] = r_
    else:
        _manp = _manifest_path()
        _man = json.load(io.open(_manp, encoding="utf-8"))
        _ff = set()
        for r_ in FREEZE:
            _ff |= {int(f_) - 1 for f_ in _man[r_]["from_faces"]}
        _ffn = set()
        for f_ in _ff:
            bb_ = s.Faces[f_].BoundBox
            if not (bb_.XMax < BOX[0] - 8 or bb_.XMin > BOX[1] + 8 or bb_.YMax < BOX[2] - 8
                    or bb_.YMin > BOX[3] + 8 or bb_.ZMax < BOX[4] - 8 or bb_.ZMin > BOX[5] + 8):
                _ffn.add(f_)
    if _ffn:
        _t = time.time()
        _dfz = _dist_to(_ffn)
        _wf = np.clip((_dfz - KEEP_HARD) / max(KEEPBAND - KEEP_HARD, 1e-6), 0.0, 1.0)
        _wf = (_wf * _wf * (3.0 - 2.0 * _wf)).astype(np.float32)
        w = w * _wf
        say("  FROZEN %s: %d face(s) near the box held exactly (both sides) within %.2f mm, %.0f s"
            % (",".join(FREEZE), len(_ffn), KEEP_HARD, time.time() - _t))
        del _dfz, _wf
    else:
        say("  FROZEN %s: no face of them near the box" % ",".join(FREEZE))

_w_grow = (w * wk).astype(np.float32) if GROW > 0 else None
KEEP_ADD = os.environ.get("CC_KEEP_ADD", "0") == "1"
if KEEP_ADD:
    adds = (cln < raw)
    w = np.where(adds, w, w * wk).astype(np.float32)
    say("  keeper protection is ONE-SIDED: it holds where the field would CUT a keeper (%.0f %% of cells)"
        .replace("%%", "pct") % (100.0 * (~adds).mean()))
    say("  and stands aside where it would ADD material against one, so a notch between two keepers fills")
else:
    w = w * wk

ZLID = float(os.environ.get("CC_ZLID", "0"))
ZRAMP = float(os.environ.get("CC_ZRAMP", "2.0"))
if ZLID > 0:
    wz = np.clip((ZLID - kk) / max(ZRAMP, 1e-6), 0.0, 1.0).astype(np.float32)
    wz = wz * wz * (3.0 - 2.0 * wz)
    w = w * wz
    say("  LID at z %.2f (ramp %.2f mm): above it the field is the body's own, so the roof is untouched"
        % (ZLID, ZRAMP))
sdf = w * cln + (1.0 - w) * raw
_SKIN = float(os.environ.get("CC_KEEPSKIN", "0"))
if _SKIN > 0:
    sdf = np.where(w > 1e-3, np.minimum(sdf, d_keep - _SKIN), sdf).astype(np.float32)
    say("  KEEPER SKIN %.2f mm inside the edit region: thin keeper edges are held, buried by the skin" % _SKIN)
EDITED = np.abs(sdf - raw)
say("band %.2f mm at the walls, keeper band %.2f mm: %.0f %% of cells fully cleaned, %.0f %% the body's own"
    % (BAND, KEEPBAND, 100.0 * (w > 0.999).mean(), 100.0 * (w < 0.001).mean()))
say("  within %.2f mm of a keeper the field is the body's own EXACTLY; it ramps to fully cleaned by %.2f mm"
    % (KEEP_HARD, KEEPBAND))

if os.environ.get("CC_ADDONLY", "0") == "1":
    _rem = int(((sdf > 0) & (raw < 0)).sum())
    sdf = np.minimum(sdf, raw).astype(np.float32)
    say("ADDONLY: the field is the union of the body and the rebuild - %d cell(s) the rebuild would have REMOVED kept solid"
        % _rem)
elif os.environ.get("CC_ADDONLY_BOXES", "").strip():
    _ramp = float(os.environ.get("CC_EDITBOXRAMP", "1.0"))
    _m = None
    for _b in [b_.split() for b_ in os.environ["CC_ADDONLY_BOXES"].split(";") if b_.strip()]:
        _b = [float(t_) for t_ in _b]
        _d = np.minimum(np.minimum(np.minimum(ii - _b[0], _b[1] - ii), np.minimum(jj - _b[2], _b[3] - jj)),
                        np.minimum(kk - _b[4], _b[5] - kk)).astype(np.float32)
        _w = np.clip(_d / max(_ramp, 1e-6), 0.0, 1.0); _w = _w * _w * (3.0 - 2.0 * _w)
        _m = _w if _m is None else np.maximum(_m, _w)
        del _d
    _rem = int((((sdf > 0) & (raw < 0)) & (_m > 0.5)).sum())
    sdf = (sdf + _m * (np.minimum(sdf, raw) - sdf)).astype(np.float32)
    say("ADDONLY inside %d box(es): %d cell(s) the rebuild would have removed there kept solid; elsewhere it may trim"
        % (len(os.environ["CC_ADDONLY_BOXES"].split(";")), _rem))
    del _m

if os.environ.get("CC_SEAL1", "0") == "1":
    _air = sdf > 0
    _thin = np.zeros(sdf.shape, bool)
    for _ax in range(3):
        _a = np.roll(sdf, 1, axis=_ax); _b = np.roll(sdf, -1, axis=_ax)
        _thin |= _air & (_a < 0) & (_b < 0)
        del _a, _b
    _thin &= (w > 1e-3)
    _ns = int(_thin.sum())
    if _ns:
        _ix = np.argwhere(_thin)
        _lo = g0 + _ix.min(0) * H; _hi = g0 + _ix.max(0) * H
        sdf = np.where(_thin, np.float32(-0.25 * H), sdf).astype(np.float32)
        say("SEAL1: %d one-cell air node(s) between solids made solid (a contact, not an opening), extent x %.1f..%.1f"
            " y %.1f..%.1f z %.1f..%.1f" % (_ns, _lo[0], _hi[0], _lo[1], _hi[1], _lo[2], _hi[2]))
    else:
        say("SEAL1: no one-cell air layer between solids")
    del _air, _thin

if GROW > 0:
    _wg = _w_grow if ZLID <= 0 else (_w_grow * wz).astype(np.float32)
    _was = float((sdf < 0).sum()) * H ** 3
    sdf = (sdf - GROW * _wg + GROW_SHRINK * (1.0 - _wg)).astype(np.float32)
    say("GROW (route A2, a copy for kit union): OUT %.2f mm x the grow weight, IN %.2f mm x (1 - it) - %.1f pct of cells grown "
        "fully, %.1f pct shrunk fully, the copy crosses the body at weight %.2f; field solid %.1f -> %.1f mm3. The reinsertion "
        "gate's wall/keeper tolerance is SKIPPED: those zones are shrunk on purpose so the union never touches them"
        % (GROW, GROW_SHRINK, 100.0 * (_wg > 0.999).mean(), 100.0 * (_wg < 0.001).mean(), GROW_SHRINK / (GROW + GROW_SHRINK),
           _was, float((sdf < 0).sum()) * H ** 3))
    if os.environ.get("CC_ADDONLY", "0") != "1":
        say("  (CC_ADDONLY is not 1: the union only ADDS, so any trim the rebuild makes is lost - set CC_ADDONLY=1 for a copy)")
    del _wg, _w_grow

pc = max(1, int(round(PAD / H / 2)))
big_pos = float(abs(sdf).max() + 1.0)
sdf[:pc, :, :] = sdf[-pc:, :, :] = big_pos
sdf[:, :pc, :] = sdf[:, -pc:, :] = big_pos
sdf[:, :, :pc] = sdf[:, :, -pc:] = big_pos
say("capped the outer %d cells to air so the patch closes" % pc)
field_vol = float((sdf < 0).sum()) * H ** 3
say("the field encloses %.1f mm3 (the raw body in this box held %.1f)" % (field_vol, vox0 * H ** 3))

import vtk
from vtk.util import numpy_support

img = vtk.vtkImageData()
img.SetDimensions(nx, ny, nz)
img.SetSpacing(H, H, H)
img.SetOrigin(float(g0[0]), float(g0[1]), float(g0[2]))
arr = numpy_support.numpy_to_vtk(np.ascontiguousarray(sdf.transpose(2, 1, 0).ravel()),
                                 deep=True, array_type=vtk.VTK_FLOAT)
arr.SetName("sdf")
img.GetPointData().SetScalars(arr)

fe = vtk.vtkFlyingEdges3D()
fe.SetInputData(img)
fe.SetValue(0, 0.0)
fe.ComputeNormalsOff()
fe.ComputeGradientsOff()
fe.Update()
poly = fe.GetOutput()
say("")
say("flying edges: %d points, %d triangles" % (poly.GetNumberOfPoints(), poly.GetNumberOfCells()))

clean = vtk.vtkCleanPolyData()
clean.SetInputData(poly)
clean.Update()
poly = clean.GetOutput()

fe_e = vtk.vtkFeatureEdges()
fe_e.SetInputData(poly)
fe_e.BoundaryEdgesOn()
fe_e.NonManifoldEdgesOn()
fe_e.FeatureEdgesOff()
fe_e.ManifoldEdgesOff()
fe_e.Update()
n_open = fe_e.GetOutput().GetNumberOfCells()

conn = vtk.vtkPolyDataConnectivityFilter()
conn.SetInputData(poly)
conn.SetExtractionModeToAllRegions()
conn.ColorRegionsOn()
conn.Update()
n_reg = conn.GetNumberOfExtractedRegions()
DISCARDED = []
if n_reg > 1 and os.environ.get("CC_LARGEST", "1") == "1":
    try:
        _co = conn.GetOutput()
        _rid = numpy_support.vtk_to_numpy(_co.GetPointData().GetArray("RegionId"))
        _pts = numpy_support.vtk_to_numpy(_co.GetPoints().GetData())
        _sz = numpy_support.vtk_to_numpy(conn.GetRegionSizes())
        _keep = int(np.argmax(_sz))
        for _r in range(len(_sz)):
            if _r == _keep or _sz[_r] == 0:
                continue
            _P = _pts[_rid == _r]
            if not len(_P):
                continue
            DISCARDED.append({"cells": int(_sz[_r]),
                              "box": [round(float(v), 2) for v in (_P[:, 0].min(), _P[:, 0].max(), _P[:, 1].min(),
                                                                   _P[:, 1].max(), _P[:, 2].min(), _P[:, 2].max())]})
    except Exception as _e:
        DISCARDED.append({"cells": -1, "box": None, "error": "could not size the discarded regions: %s" % _e})
    big = vtk.vtkPolyDataConnectivityFilter()
    big.SetInputData(poly)
    big.SetExtractionModeToLargestRegion()
    big.Update()
    say("  %d regions -> kept the largest only (%d -> %d triangles); DISCARDED %d region(s):"
        % (n_reg, poly.GetNumberOfCells(), big.GetOutput().GetNumberOfCells(), len(DISCARDED)))
    for _d in sorted(DISCARDED, key=lambda d: -d["cells"])[:12]:
        say("      %7d cells   box %s" % (_d["cells"], " ".join("%.1f" % v for v in (_d["box"] or []))))
    say("  the weld refuses a core that reaches any of them - a discarded region inside a core is a hole")
    if FREEZE and _ffn:
        try:
            _fzm = np.isin(F, list(_ffn))
            _fcen = np.asarray(Vv, float)[T[_fzm]].mean(1); _fid = F[_fzm]
            for _d in DISCARDED:
                if not _d.get("box"):
                    continue
                _b = _d["box"]
                _lo = np.array([_b[0], _b[2], _b[4]]); _hi = np.array([_b[1], _b[3], _b[5]])
                _gap = np.linalg.norm(np.maximum(0.0, np.maximum(_lo - _fcen, _fcen - _hi)), axis=1)
                _i = int(np.argmin(_gap))
                _d["nearest_frozen"] = {"region": _fz_names.get(int(_fid[_i]), str(int(_fid[_i]))), "mm": round(float(_gap[_i]), 3)}
                if _gap[_i] <= 1.0:
                    say("  WARNING: a discarded region (%d cells, box %s) lies %.2f mm from FROZEN %s - the field closed a feature\n"
                        "           OF THAT REGION (a bore, a groove) and the weld would plug it. Widen or move the box, or keep\n"
                        "           the region with CC_KEEP_REGIONS; do not weld this patch as it is."
                        % (_d["cells"], " ".join("%.1f" % v for v in _b), _gap[_i], _d["nearest_frozen"]["region"]))
        except Exception as _e:
            say("  (could not measure the discarded regions against the frozen surfaces: %s)" % _e)
    poly = big.GetOutput()
    n_reg = 1

tri = vtk.vtkTriangleFilter()
tri.SetInputData(poly)
tri.PassLinesOff()
tri.PassVertsOff()
tri.Update()
poly = tri.GetOutput()
try:
    _pp = numpy_support.vtk_to_numpy(poly.GetPoints().GetData()).astype(float)
    _pt = numpy_support.vtk_to_numpy(poly.GetPolys().GetData()).reshape(-1, 4)[:, 1:]
    _sv = float(np.einsum("ij,ij->i", _pp[_pt[:, 0]], np.cross(_pp[_pt[:, 1]], _pp[_pt[:, 2]])).sum() / 6.0)
    if _sv < 0:
        _rs = vtk.vtkReverseSense(); _rs.SetInputData(poly); _rs.ReverseCellsOn(); _rs.ReverseNormalsOn(); _rs.Update()
        poly = _rs.GetOutput()
        say("  winding: the shell came out INWARD (signed volume %.1f mm3) - reversed to face out" % _sv)
    else:
        say("  winding: faces out (signed volume %.1f mm3)" % _sv)
except Exception as _e:
    say("  winding could not be checked: %s" % str(_e)[:80])
try:
    mp = vtk.vtkMassProperties()
    mp.SetInputData(poly)
    vol = float(mp.GetVolume())
except Exception as _e:
    vol = float("nan")
    say("  volume could not be computed: %s" % str(_e)[:80])

say("after cleaning: %d points, %d triangles" % (poly.GetNumberOfPoints(), poly.GetNumberOfCells()))
say("  boundary + non-manifold edges : %d   %s" % (n_open, "CLOSED" if n_open == 0 else "*** OPEN ***"))
say("  connected regions             : %d" % n_reg)
say("  enclosed volume               : %.1f mm3   (voxels say %.1f, ratio %.4f)"
    % (vol, field_vol, vol / max(1e-9, field_vol)))

SNAP = float(os.environ.get("CC_SNAP", "0"))
if SNAP > 0 and keepf and GROW > 0:
    say("SNAP skipped (CC_GROW): a grown copy must never lie ON a keeper - the union would meet it on a shared surface")
elif SNAP > 0 and keepf and not len(ktri):
    say("SNAP skipped: the keepers named hold no triangle near the box - nothing to snap onto (the classification line above says so)")
elif SNAP > 0 and keepf:
    t = time.time()
    vpts = poly.GetPoints()
    n_moved, worst = 0, 0.0
    kd = vtk.vtkImplicitPolyDataDistance()
    kd.SetInput(keep_pd)
    for i_ in range(vpts.GetNumberOfPoints()):
        q = list(vpts.GetPoint(i_))
        d0 = kd.EvaluateFunction(q[0], q[1], q[2])
        if abs(d0) > SNAP:
            continue
        for _ in range(3):
            d_ = kd.EvaluateFunction(q[0], q[1], q[2])
            g = [0.0, 0.0, 0.0]
            kd.EvaluateGradient(q, g)
            gn = (g[0] * g[0] + g[1] * g[1] + g[2] * g[2]) ** 0.5
            if gn < 1e-9:
                break
            q = [q[a] - d_ * g[a] / (gn * gn) for a in range(3)]
        mv = ((q[0] - vpts.GetPoint(i_)[0]) ** 2 + (q[1] - vpts.GetPoint(i_)[1]) ** 2
              + (q[2] - vpts.GetPoint(i_)[2]) ** 2) ** 0.5
        if mv <= 2.0 * H:
            vpts.SetPoint(i_, q[0], q[1], q[2])
            n_moved += 1
            worst = max(worst, mv)
    poly.Modified()
    say("")
    say("SNAP: %d vertices within %.2f mm of a keeper walked onto it exactly; largest move %.4f mm (%.0f s)"
        % (n_moved, SNAP, worst, time.time() - t))
    fe2 = vtk.vtkFeatureEdges(); fe2.SetInputData(poly)
    fe2.BoundaryEdgesOn(); fe2.NonManifoldEdgesOn(); fe2.FeatureEdgesOff(); fe2.ManifoldEdgesOff()
    fe2.Update()
    say("  after snapping: boundary + non-manifold edges %d  %s"
        % (fe2.GetOutput().GetNumberOfCells(),
           "(unchanged - snapping moves vertices, never connectivity)"
           if fe2.GetOutput().GetNumberOfCells() == n_open else "*** CHANGED - investigate ***"))

pimp = vtk.vtkImplicitPolyDataDistance()
pimp.SetInput(poly)


def on_patch(P, signed=False):
    """distance from each point to the patch; `signed`: negative inside it (the patch is written facing out)"""
    d = np.array([pimp.EvaluateFunction(float(q[0]), float(q[1]), float(q[2])) for q in P])
    return d if signed else np.abs(d)


def tri_samples(tris, lim):
    """vertices plus centroids of the given triangles, kept inside `lim`"""
    if not len(tris):
        return np.zeros((0, 3))
    v = Vv[np.unique(tris)]
    c = Vv[tris].mean(axis=1)
    P = np.vstack([v, c])
    m = ((P[:, 0] >= lim[0]) & (P[:, 0] <= lim[1]) & (P[:, 1] >= lim[2]) & (P[:, 1] <= lim[3])
         & (P[:, 2] >= lim[4]) & (P[:, 2] <= lim[5]))
    return P[m]


say("")
say("REINSERTION GATE - does the patch REPRODUCE the surfaces that must survive?")
if os.environ.get("CC_GATE_BOX"):
    say("  measured only inside CC_GATE_BOX %s - where the patch will be used" % os.environ["CC_GATE_BOX"])
say("  (points sampled ON the body, distance measured TO the patch)")
GROW_REPORT = {}
if GROW > 0:
    say("  CC_GROW %.2f: REPORT ONLY - a copy for kit union reproduces nothing on purpose (grown %.2f in the edit zone, shrunk %.2f"
        " at the walls and held surfaces); each zone also says how far the body stands OUTSIDE the copy" % (GROW, GROW, GROW_SHRINK))
TOL = float(os.environ.get("CC_MATCHTOL", "0.10"))
GATE_WHERE = {}
KEEP_HARD_Z = float(os.environ.get("CC_KEEPHARD", "0.40"))
inner = [BOX[0] + 1.0, BOX[1] - 1.0, BOX[2] + 1.0, BOX[3] - 1.0, BOX[4] + 1.0, BOX[5] - 1.0]
worst = 0.0
_zones = {}
_unmeasured = []
kt = T[np.isin(F, list(keepf))] if keepf else np.zeros((0, 3), int)
_ks = tri_samples(kt, inner)
if len(_ks):
    _dw = np.array([
        min(q[0] - BOX[0], BOX[1] - q[0], q[1] - BOX[2], BOX[3] - q[1], q[2] - BOX[4], BOX[5] - q[2])
        for q in _ks])
    _wq = np.clip(_dw / max(BAND, 1e-6), 0.0, 1.0)
    _wq = _wq * _wq * (3.0 - 2.0 * _wq)
    _eps = float(os.environ.get("CC_EDITED_EPS", "0.02"))
    _gi = np.clip(np.rint((_ks - g0) / H).astype(int), 0, np.array(EDITED.shape) - 1)
    _em = np.zeros(len(_ks), np.float32)
    for _dx in (0, 1):
        for _dy in (0, 1):
            for _dz in (0, 1):
                _q = np.minimum(_gi + np.array([_dx, _dy, _dz]), np.array(EDITED.shape) - 1)
                _em = np.maximum(_em, EDITED[_q[:, 0], _q[:, 1], _q[:, 2]])
    _protected = _ks[_em <= _eps]
    _edited = _ks[_em > _eps]
else:
    _protected = _edited = np.zeros((0, 3))
for nm, P in (("keepers in the PROTECTED band", _protected),
              ("keepers in the EDIT zone (report only)", _edited),
              ("the body at the box walls", np.vstack([tri_samples(
                  T, [BOX[0] - 0.5, BOX[0] + 0.5, BOX[2], BOX[3], BOX[4], BOX[5]]),
                  tri_samples(T, [BOX[1] - 0.5, BOX[1] + 0.5, BOX[2], BOX[3], BOX[4], BOX[5]]),
                  tri_samples(T, [BOX[0], BOX[1], BOX[2] - 0.5, BOX[2] + 0.5, BOX[4], BOX[5]]),
                  tri_samples(T, [BOX[0], BOX[1], BOX[3] - 0.5, BOX[3] + 0.5, BOX[4], BOX[5]]),
                  tri_samples(T, [BOX[0], BOX[1], BOX[2], BOX[3], BOX[4] - 0.5, BOX[4] + 0.5]),
                  tri_samples(T, [BOX[0], BOX[1], BOX[2], BOX[3], BOX[5] - 0.5, BOX[5] + 0.5])])
               if True else np.zeros((0, 3)))):
    # MESH_JOB
    if len(P) and os.environ.get("CC_GATE_BOX"):
        _gb = [float(t_) for t_ in os.environ["CC_GATE_BOX"].split()]
        P = P[(P[:, 0] >= _gb[0]) & (P[:, 0] <= _gb[1]) & (P[:, 1] >= _gb[2]) & (P[:, 1] <= _gb[3])
              & (P[:, 2] >= _gb[4]) & (P[:, 2] <= _gb[5])]
    if len(P) and _ZB:
        _inb = np.zeros(len(P), bool)
        for b_ in _ZB:
            _inb |= ((P[:, 0] >= b_[0]) & (P[:, 0] <= b_[1]) & (P[:, 1] >= b_[2]) & (P[:, 1] <= b_[3])
                     & (P[:, 2] >= b_[4]) & (P[:, 2] <= b_[5]))
        if _inb.any():
            say("  %-28s %d sample(s) inside CC_ZBRIDGE boxes left out (the body there is replaced on purpose)" % (nm, int(_inb.sum())))
        P = P[~_inb]
    if not len(P):
        # NOT MEASURED  NOT MEASURED
        say("  %-28s NOT MEASURED - 0 sample points%s" % (nm, " inside CC_GATE_BOX" if os.environ.get("CC_GATE_BOX") else ""))
        _zones[nm] = None
        if "report only" not in nm:
            _unmeasured.append(nm)
        continue
    if len(P) > 40000:
        P = P[np.linspace(0, len(P) - 1, 40000).astype(int)]
    ds_ = on_patch(P, signed=True); d_ = np.abs(ds_)
    _zones[nm] = round(float(d_.max()), 4)
    if "report only" not in nm and GROW <= 0:
        worst = max(worst, float(d_.max()))
    say("  %-28s %6d points   mean %6.4f  p99 %6.4f  MAX %6.4f mm"
        % (nm, len(P), d_.mean(), np.percentile(d_, 99), d_.max()))
    # over the
    if GROW <= 0 and "report only" not in nm:
        _over = np.where(d_ > TOL)[0]
        if len(_over):
            _Po = P[_over]; _do = d_[_over]
            _walls = []
            for _q in _Po:
                _dd = [(_q[0] - BOX[0], "x-min"), (BOX[1] - _q[0], "x-max"), (_q[1] - BOX[2], "y-min"),
                       (BOX[3] - _q[1], "y-max"), (_q[2] - BOX[4], "z-min"), (BOX[5] - _q[2], "z-max")]
                _mn = min(_dd, key=lambda t_: t_[0])
                _walls.append(_mn[1] if _mn[0] <= 0.75 else "inside")
            _per_wall = {}
            for _w in _walls:
                _per_wall[_w] = _per_wall.get(_w, 0) + 1
            say("  %-28s %d sample(s) over %.2f mm - per wall: %s" % ("", len(_over), TOL,
                ", ".join("%s %d" % (k_, v_) for k_, v_ in sorted(_per_wall.items(), key=lambda t_: -t_[1]))))
            _k = np.floor(_Po / 3.0).astype(int)
            _uk, _inv, _cnt = np.unique(_k, axis=0, return_inverse=True, return_counts=True)
            _inv = np.asarray(_inv).reshape(-1)
            _clusters = []
            for _j in np.argsort(-_cnt)[:6]:
                _Pi = _Po[_inv == _j]
                _clusters.append({"samples": int(_cnt[_j]), "worst_mm": round(float(_do[_inv == _j].max()), 4),
                                  "box": [round(float(v_), 2) for v_ in np.concatenate([_Pi.min(0), _Pi.max(0)])[[0, 3, 1, 4, 2, 5]]]})
                say("      cluster %5d sample(s)  worst %.4f  box x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f"
                    % (int(_cnt[_j]), float(_do[_inv == _j].max()), *_clusters[-1]["box"]))
            _top = np.argsort(-_do)[:50]
            GATE_WHERE[nm] = {"over_tolerance": int(len(_over)), "per_wall": _per_wall, "clusters": _clusters,
                              "worst_samples": [[round(float(_Po[i_][0]), 3), round(float(_Po[i_][1]), 3), round(float(_Po[i_][2]), 3),
                                                 round(float(_do[i_]), 4), _walls[i_]] for i_ in _top]}
            _dom = max(_per_wall, key=_per_wall.get)
            if _dom != "inside":
                say("      -> the misses sit on the %s wall: a crack or film of the body's own crosses it there (check MEASUREMENTS.md)."
                    " Move THAT wall (a few mm either way), never the gate box." % _dom)
    if GROW > 0:
        _pk = int((ds_ < -0.01).sum())
        GROW_REPORT[nm] = {"samples": int(len(ds_)), "outside_min_mm": round(float(ds_.min()), 4),
                           "outside_mean_mm": round(float(ds_.mean()), 4), "poke_through": _pk}
        say("  %-28s body outside the copy by min %+.4f / mean %+.4f mm; the copy pokes through it (> 0.01 mm) at %d of %d"
            % ("", ds_.min(), ds_.mean(), _pk, len(ds_)))
_MATES = GROW > 0 or (worst <= TOL and "the body at the box walls" not in _unmeasured)
if GROW > 0:
    say("  verdict: SKIPPED (CC_GROW %.2f) - a grown copy is judged by kit union (closed, volume window) and kit splice (seam)%s"
        % (GROW, ", not by reproduction" if "the body at the box walls" not in _unmeasured else "; no body sample at the walls to report"))
elif "the body at the box walls" in _unmeasured:
    say("  verdict: NOT MEASURED - no body sample at the box walls%s. A gate with zero samples is a FAIL (R23):\n"
        "           widen CC_GATE_BOX to reach the extract box's walls, or check the box holds any body at all."
        % (" inside CC_GATE_BOX" if os.environ.get("CC_GATE_BOX") else ""))
else:
    say("  verdict: worst %.4f mm against a tolerance of %.2f mm -> %s%s"
        % (worst, TOL, "MATES" if _MATES else "*** does not reproduce them to tolerance ***",
           "   (keepers: none in the box - the wall zone alone decided)" if "keepers in the PROTECTED band" in _unmeasured else ""))

# recorded
if OUT_STL:
    _out = OUT_STL if _MATES else (OUT_STL[:-4] + "_REFUSED.stl" if OUT_STL.lower().endswith(".stl")
                                   else OUT_STL + "_REFUSED")
    w = vtk.vtkSTLWriter()
    w.SetFileName(_out)
    w.SetInputData(poly)
    w.SetFileTypeToBinary()
    w.Write()
    say("  wrote %s (%.1f MB)%s" % (_out, os.path.getsize(_out) / 1e6,
                                    "" if _MATES else "   <- REFUSED: look at it, do not weld it"))
    json.dump(dict({"patch": _out, "box": BOX, "discarded_regions": DISCARDED,
                    "gate": ("GROWN - a copy for kit union, never the weld" if GROW > 0 else "MATES" if _MATES else "REFUSED")},
                   **({"grow": {"grow_mm": GROW, "shrink_mm": GROW_SHRINK}} if GROW > 0 else {})),
              io.open(os.path.splitext(_out)[0] + ".extract.json", "w", encoding="utf-8"), indent=1)

json.dump({"state": "done" if _MATES else "REFUSED",
           "gate": {"name": "reinsertion", "verdict": ("SKIPPED (CC_GROW: a copy for kit union)" if GROW > 0 else "MATES" if _MATES else
                                                       ("NOT MEASURED" if "the body at the box walls" in _unmeasured else "does not reproduce")),
                    "worst_mm": round(float(worst), 4), "tolerance_mm": TOL, "by_zone": _zones, "not_measured": _unmeasured,
                    "where": GATE_WHERE,
                    "zone_model": "edit zone = where the final field differs from the body's own by > CC_EDITED_EPS"},
           "grow": ({"grow_mm": GROW, "shrink_mm": GROW_SHRINK, "body_outside_copy_by_zone": GROW_REPORT} if GROW > 0 else None),
           "sign_check": SIGN_FIX,
           "box": BOX, "field_volume": round(field_vol, 1),
           "tris": poly.GetNumberOfCells(),
           "open_edges": int(n_open), "regions": int(n_reg), "volume": round(vol, 1),
           "discarded_regions": DISCARDED,

           "levers": {"h": H, "close": R_CLOSE, "open": R_OPEN, "sigma": SIGMA, "pad": PAD, "dev": DEV}},
          io.open(STATUS, "w", encoding="utf-8"), indent=1)
say("")
say("%.0f s" % (time.time() - t0))
say("DONE" if _MATES else "DONE - BUT THE REINSERTION GATE REFUSED")
if not _MATES:
    raise SystemExit(2)

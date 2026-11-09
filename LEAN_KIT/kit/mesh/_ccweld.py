# over the
import io, json, os, sys, time
import numpy as np
sys.path.insert(0, os.environ["KIT_HOME"])
import kitlib as K, Part, FreeCAD
import MeshPart
import vtk
from vtk.util import numpy_support

_ow = vtk.vtkFileOutputWindow()
_ow.SetFileName(os.path.join(os.environ.get("CC_WORK") or os.path.dirname(os.path.abspath(__file__)), "vtk_messages.log"))
_ow.SetFlush(0)
vtk.vtkOutputWindow.SetInstance(_ow)
vtk.vtkObject.GlobalWarningDisplayOff()

V = FreeCAD.Vector
t0 = time.time()
SRC = os.path.dirname(os.path.abspath(__file__))
HERE = os.environ.get("CC_WORK") or SRC
TAG = os.environ.get("LK_TAG", "X")
STATUS = os.path.join(HERE, "status_ccweld%s.json" % (TAG if TAG != "X" else ""))

BODY = os.environ["CC_BODY"]
PATCH = os.environ["CC_PATCH"]
# CC_CORE_BLOB
# MESH_JOB
BLOB = os.environ.get("CC_CORE_BLOB", "").strip()
if BLOB:
    from scipy.spatial import cKDTree as _BKD
    _bz = np.load(BLOB)
    BLOB_E = np.asarray(_bz["E"], float); BLOB_M = float(_bz["M"])
    BLOB_MI = np.asarray(_bz["Mi"], float) if "Mi" in _bz.files else None
    BLOB_T = _BKD(BLOB_E)
    CEN = list(0.5 * (BLOB_E.min(0) + BLOB_E.max(0)))
    RAD = list(0.5 * (BLOB_E.max(0) - BLOB_E.min(0)) + BLOB_M)
else:
    CEN = [float(t) for t in os.environ["CC_CORE_CEN"].split()]
    RAD = [float(t) for t in os.environ["CC_CORE_RAD"].split()]
DEV = float(os.environ.get("CC_DEV", "0.08"))
DECIM = float(os.environ.get("CC_DECIM", "0.0"))
DECERR = float(os.environ.get("CC_DECERR", "0.04"))
OUT = os.environ.get("CC_OUT", "")


def say(*a):
    print(*a, flush=True)


def stats(pd, label):
    fe = vtk.vtkFeatureEdges(); fe.SetInputData(pd)
    fe.BoundaryEdgesOn(); fe.NonManifoldEdgesOn(); fe.FeatureEdgesOff(); fe.ManifoldEdgesOff(); fe.Update()
    cn = vtk.vtkPolyDataConnectivityFilter(); cn.SetInputData(pd)
    cn.SetExtractionModeToAllRegions(); cn.Update()
    say("  %-28s %8d tri  open/non-manifold %6d  regions %4d"
        % (label, pd.GetNumberOfCells(), fe.GetOutput().GetNumberOfCells(),
           cn.GetNumberOfExtractedRegions()))
    return fe.GetOutput().GetNumberOfCells()


say("== keep and weld ==")

# open edges
import hashlib


def _md5(p_):
    h_ = hashlib.md5()
    with open(p_, "rb") as f_:
        for blk in iter(lambda: f_.read(1 << 20), b""):
            h_.update(blk)
    return h_.hexdigest()


def _proven_mesh(p_):
    try:
        rec_ = json.load(io.open(p_ + ".base.json", encoding="utf-8"))
        return rec_.get("md5") == _md5(p_)
    except Exception:
        return False


_bn = os.path.basename(BODY).lower()
_bank = os.path.normcase(os.path.join("claude_code", "bank"))
_ok_named = [os.path.normcase(os.path.abspath(p_)) for p_ in os.environ.get("CC_BASE_OK", "").split(";") if p_.strip()]
_is_brep_base = _bn.endswith(".brep") and _bank in os.path.normcase(os.path.abspath(BODY))


def _is_crop(p_):
    """a crop cut by `kit crop` (its sidecar's md5 matches), or a refined base whose source is such a crop - an
    UNEDITED piece of the body by construction, so a valid base (2026-09-24)"""
    try:
        side_ = os.path.splitext(p_)[0] + ".crop.json"
        if os.path.isfile(side_):
            return json.load(io.open(side_, encoding="utf-8")).get("crop_md5") == _md5(p_)
        rec_ = json.load(io.open(p_ + ".base.json", encoding="utf-8"))
        src_ = str(rec_.get("from", ""))
        return rec_.get("md5") == _md5(p_) and src_.lower().endswith(".stl") and _is_crop(src_)
    except Exception:
        return False


_is_base = _is_brep_base or (_bn == "body_mesh.stl" and os.path.dirname(os.path.abspath(BODY)) == HERE) \
    or os.path.normcase(os.path.abspath(BODY)) in _ok_named \
    or (_bn.endswith(".stl") and (_proven_mesh(BODY) or _is_crop(BODY)))
CHAIN_OK = os.environ.get("CC_CHAIN_OK", "").strip()
if not _is_base and not CHAIN_OK:
    say("REFUSED: the body %s is not the model of record, a crop of it, or the family's shared base." % os.path.basename(BODY))
    say("  L12: do not chain cards - fuse every piece onto ONE unchanged base. A base that already carries a weld")
    say("  puts this core's wall across the last weld's seam; measured 2026-09-22, that alone left an orphan loop")
    say("  and about 1,068 open edges. Weld onto a `kit crop` of the base (the crop flow), claude_code\\bank\\<model>.brep")
    say("  or body_mesh.stl, and combine the pieces afterwards (kit splice). If the client has approved chaining for this case,")
    say("  set CC_CHAIN_OK to their words.")
    json.dump({"state": "REFUSED", "why": "chained base (L12)", "body": BODY},
              io.open(STATUS, "w", encoding="utf-8"), indent=1)
    raise SystemExit(2)
if CHAIN_OK and not _is_base:
    say("CHAINED BASE ALLOWED by CC_CHAIN_OK: %s" % CHAIN_OK)

t = time.time()
if BODY.lower().endswith((".stl", ".ast")):
    _r = vtk.vtkSTLReader(); _r.SetFileName(BODY); _r.Update()
    _c = vtk.vtkCleanPolyData(); _c.SetInputData(_r.GetOutput())
    _c.ToleranceIsAbsoluteOn(); _c.SetAbsoluteTolerance(1e-6); _c.PointMergingOn(); _c.Update()
    _pd = _c.GetOutput()
    BV = np.asarray(numpy_support.vtk_to_numpy(_pd.GetPoints().GetData()), float)
    BT = numpy_support.vtk_to_numpy(_pd.GetPolys().GetData()).reshape(-1, 4)[:, 1:].astype(int)
    say("body read from MESH %s: %d points, %d triangles (%.0f s)"
        % (os.path.basename(BODY), len(BV), len(BT), time.time() - t))
else:
    sh = Part.Shape(); sh.importBrep(BODY)
    say("body: %d faces, %d solid(s), valid=%s" % (len(sh.Faces), len(sh.Solids), sh.isValid()))
    m = MeshPart.meshFromShape(Shape=sh, LinearDeflection=DEV, AngularDeflection=0.4, Relative=False)
    m.removeDuplicatedPoints()
    tp = m.Topology
    BV = np.asarray(tp[0], float); BT = np.asarray(tp[1], int)
    say("body meshed with meshFromShape: %d points, %d triangles (%.0f s)" % (len(BV), len(BT), time.time() - t))


def to_pd(Vv, T):
    pts = vtk.vtkPoints()
    pts.SetData(numpy_support.numpy_to_vtk(np.ascontiguousarray(Vv, np.float64), deep=True))
    cells = vtk.vtkCellArray()
    conn = np.empty((len(T), 4), np.int64); conn[:, 0] = 3; conn[:, 1:] = T
    cells.SetCells(len(T), numpy_support.numpy_to_vtkIdTypeArray(conn.ravel(), deep=True))
    pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(cells)
    return pd


body_pd = to_pd(BV, BT)
_tf0 = vtk.vtkTriangleFilter(); _tf0.SetInputData(to_pd(BV, BT)); _tf0.PassLinesOff(); _tf0.PassVertsOff(); _tf0.Update()
_mp0 = vtk.vtkMassProperties(); _mp0.SetInputData(_tf0.GetOutput()); _body_in_vol = _mp0.GetVolume()
stats(body_pd, "body (baseline)")

# bit-identical
if not BODY.lower().endswith((".stl", ".ast")) or os.environ.get("CC_DUMP_BASE", "").strip() == "1":
    _w = vtk.vtkSTLWriter()
    _w.SetFileName(os.path.join(HERE, "body_mesh_%s.stl" % os.environ.get("LK_TAG", "X")))
    _w.SetInputData(body_pd)
    _w.SetFileTypeToBinary()
    _w.Write()
    say("  wrote body_mesh_%s.stl (the exact mesh the clip saw)" % os.environ.get("LK_TAG", "X"))
    if _is_base:
        _bmp = os.path.join(HERE, "body_mesh_%s.stl" % os.environ.get("LK_TAG", "X"))
        json.dump({"md5": _md5(_bmp), "from": BODY, "kind": "brep" if _is_brep_base else "proven mesh",
                   "note": "an UNEDITED body mesh - a valid base for another weld while this md5 matches"},
                  io.open(_bmp + ".base.json", "w", encoding="utf-8"), indent=1)
else:
    say("  body mesh not re-written (an STL base is already the exact mesh the clip sees; CC_DUMP_BASE=1 to write it)")

r = vtk.vtkSTLReader(); r.SetFileName(PATCH); r.Update()
patch_pd = r.GetOutput()
stats(patch_pd, "patch as extracted")

_side = os.path.splitext(PATCH)[0] + ".extract.json"
if os.path.exists(_side):
    try:
        _disc = json.load(io.open(_side, encoding="utf-8")).get("discarded_regions", []) or []
    except Exception as _e:
        _disc = []
        say("NOTE: could not read %s (%s) - discarded regions NOT checked" % (os.path.basename(_side), _e))
    _clo = [c - r_ for c, r_ in zip(CEN, RAD)]; _chi = [c + r_ for c, r_ in zip(CEN, RAD)]

    def _reaches(b_):
        if not all(b_[2 * k] <= _chi[k] + 1.0 and b_[2 * k + 1] >= _clo[k] - 1.0 for k in range(3)):
            return False
        if BLOB:
            _blo = np.array(b_[0::2]); _bhi = np.array(b_[1::2])
            _dd = np.linalg.norm(np.maximum(np.maximum(_blo - BLOB_E, 0.0), BLOB_E - _bhi), axis=1).min()
            return bool(_dd <= BLOB_M + 1.0)
        _rnd = float(os.environ.get("CC_CORE_ROUND", "0"))
        q_ = [min(max(CEN[k], b_[2 * k]), b_[2 * k + 1]) for k in range(3)]
        s_ = [abs(q_[k] - CEN[k]) / (RAD[k] + 1.0) for k in range(3)]
        return sum(v_ ** (2.0 / _rnd) if _rnd > 0 else v_ ** 2 for v_ in s_) <= 1.0
    _speck = [d for d in _disc if d.get("box") and max(d["box"][1] - d["box"][0], d["box"][3] - d["box"][2],
                                                       d["box"][5] - d["box"][4]) < 0.30]
    for d in _speck:
        if _reaches(d["box"]):
            say("  a discarded SPECK near the core, set aside: %s cells, %.2f mm across"
                % (d.get("cells"), max(d["box"][1] - d["box"][0], d["box"][3] - d["box"][2], d["box"][5] - d["box"][4])))
    _hit = [d for d in _disc if d.get("box") and d not in _speck and _reaches(d["box"])]
    if BLOB and _hit:
        _deep = []
        for d in _hit:
            b_ = d["box"]
            _pts = np.array([[x_, y_, z_] for x_ in b_[0:2] for y_ in b_[2:4] for z_ in b_[4:6]], float)
            if BLOB_MI is None:
                _fv = BLOB_T.query(_pts)[0] - BLOB_M
            else:
                _dk, _ik = BLOB_T.query(_pts, k=16); _fv = (_dk - BLOB_MI[_ik]).min(1)
            if float(_fv.max()) < -1.0:
                _deep.append(d)
                say("  a discarded fragment DEEP inside the core (%.1f mm from its wall), set aside: %s cells, box %s"
                    % (-float(_fv.max()), d.get("cells"), " ".join("%.1f" % v for v in b_)))
        _hit = [d for d in _hit if d not in _deep]
    if _hit:
        say("REFUSED: %d region(s) the extract DISCARDED lie inside this core - each is surface the weld will not"
            " have, and its rim becomes a hole:" % len(_hit))
        for d in _hit[:8]:
            say("     %7s cells   box %s" % (d.get("cells"), " ".join("%.1f" % v for v in d["box"])))
        say("  Rebuild the extract so it does not split (a wider reach, a softer ramp), or move the core off them.")
        json.dump({"state": "REFUSED", "why": "a discarded extract region lies inside the core", "regions": _hit},
                  io.open(STATUS, "w", encoding="utf-8"), indent=1)
        raise SystemExit(2)
    say("extract record: %d discarded region(s), none inside this core" % len(_disc))
else:
    say("NOTE: no %s beside the patch - it predates the record, so discarded regions cannot be checked here."
        % os.path.basename(_side))

# DIFFERENT
ROUND = float(os.environ.get("CC_CORE_ROUND", "0"))
if BLOB:
    core = None
    say("core: EDIT ZONE - within %.2f mm of %d disagreement points (%s), bounding box centre (%.1f %.1f %.1f)"
        " half-extents (%.1f %.1f %.1f)" % (BLOB_M, len(BLOB_E), os.path.basename(BLOB), CEN[0], CEN[1], CEN[2],
                                             RAD[0], RAD[1], RAD[2]))
elif ROUND > 0:
    core = vtk.vtkSuperquadric()
    core.SetCenter(0.0, 0.0, 0.0)
    core.SetScale(RAD[0], RAD[1], RAD[2])
    core.SetSize(1.0)
    core.SetThetaRoundness(ROUND)
    core.SetPhiRoundness(ROUND)
    tr = vtk.vtkTransform()
    tr.Translate(CEN[0], CEN[1], CEN[2])
    tr.Inverse()
    core.SetTransform(tr)
    say("core: ROUNDED BOX centre (%.1f %.1f %.1f) half-extents (%.1f %.1f %.1f) roundness %.2f"
        % (CEN[0], CEN[1], CEN[2], RAD[0], RAD[1], RAD[2], ROUND))
else:
    tr = vtk.vtkTransform()
    tr.Translate(CEN[0], CEN[1], CEN[2])
    tr.Scale(RAD[0], RAD[1], RAD[2])
    tr.Inverse()
    core = vtk.vtkSphere()
    core.SetCenter(0.0, 0.0, 0.0)
    core.SetRadius(1.0)
    core.SetTransform(tr)
    say("core: ellipsoid centre (%.1f %.1f %.1f) radii (%.1f %.1f %.1f)"
        % (CEN[0], CEN[1], CEN[2], RAD[0], RAD[1], RAD[2]))


def clip(pd, inside, label):
    c = vtk.vtkClipPolyData()
    if BLOB:
        _pp = numpy_support.vtk_to_numpy(pd.GetPoints().GetData())
        if BLOB_MI is None:
            _f = (BLOB_T.query(_pp)[0] - BLOB_M).astype(np.float64)
        else:
            _dk, _ik = BLOB_T.query(_pp, k=16)
            _f = (_dk - BLOB_MI[_ik]).min(1).astype(np.float64)
        _pd2 = vtk.vtkPolyData(); _pd2.ShallowCopy(pd)
        _arr = numpy_support.numpy_to_vtk(_f, deep=True); _arr.SetName("core")
        _pd2.GetPointData().SetScalars(_arr)
        c.SetInputData(_pd2)
    else:
        c.SetInputData(pd)
        c.SetClipFunction(core)
    c.SetValue(0.0)
    c.SetInsideOut(1 if inside else 0)
    c.SetOutputPointsPrecision(vtk.vtkAlgorithm.DOUBLE_PRECISION)
    c.Update()
    o = c.GetOutput()
    stats(o, label)
    return o


say("")
say("clipping:")
# over the
NEARMARG = float(os.environ.get("CC_NEARMARG", "2.0"))
CENa = np.asarray(CEN, float)
RADa = np.asarray(RAD, float)
_bp = numpy_support.vtk_to_numpy(body_pd.GetPoints().GetData())
_bt = []
_ids = vtk.vtkIdList()
for _c in range(body_pd.GetNumberOfCells()):
    body_pd.GetCellPoints(_c, _ids)
    if _ids.GetNumberOfIds() == 3:
        _bt.append([_ids.GetId(0), _ids.GetId(1), _ids.GetId(2)])
_bt = np.asarray(_bt, int)
_lo = CENa - RADa - NEARMARG
_hi = CENa + RADa + NEARMARG
_tv = _bp[_bt]
_near = ((_tv >= _lo).all(2) & (_tv <= _hi).all(2)).any(1) |         ((_tv.min(1) <= _hi) & (_tv.max(1) >= _lo)).all(1)
say("  body triangles near the core (clipped): %d, far (passed through untouched): %d"
    % (int(_near.sum()), int((~_near).sum())))
B_near = clip(to_pd(_bp, _bt[_near]), False, "  near-core body, clipped")
B_far = to_pd(_bp, _bt[~_near])
_apb = vtk.vtkAppendPolyData()
_apb.AddInputData(B_near)
_apb.AddInputData(B_far)
_apb.Update()
B_out = _apb.GetOutput()
stats(B_out, "body OUTSIDE the core (kept)")
P_in = clip(patch_pd, True, "patch INSIDE the core")
if P_in.GetNumberOfCells() == 0:
    say("FAIL: the core encloses none of the patch - wrong centre or radii.")
    raise SystemExit(1)

# neighbouring feature
# boundary edges
cn = vtk.vtkPolyDataConnectivityFilter()
cn.SetInputData(P_in)
cn.SetExtractionModeToAllRegions()
cn.ColorRegionsOn()
cn.Update()
_nreg = cn.GetNumberOfExtractedRegions()
if _nreg > 1:
    _co = cn.GetOutput()
    _sizes = numpy_support.vtk_to_numpy(cn.GetRegionSizes())
    _prid = numpy_support.vtk_to_numpy(_co.GetPointData().GetArray("RegionId"))
    _ppts = numpy_support.vtk_to_numpy(_co.GetPoints().GetData())
    _fe = vtk.vtkFeatureEdges(); _fe.SetInputData(_co)
    _fe.BoundaryEdgesOn(); _fe.NonManifoldEdgesOff(); _fe.FeatureEdgesOff(); _fe.ManifoldEdgesOff(); _fe.Update()
    _open = set()
    if _fe.GetOutput().GetNumberOfPoints():
        from scipy.spatial import cKDTree as _KD
        _bpts = numpy_support.vtk_to_numpy(_fe.GetOutput().GetPoints().GetData())
        _d, _i = _KD(_ppts).query(_bpts, k=1)
        _open = {int(_prid[j]) for j, dd in zip(_i, _d) if dd < 1e-9}
    _keep_ids = sorted(_open) if _open else [int(np.argmax(_sizes))]
    _drop = [r for r in range(_nreg) if r not in _keep_ids]
    _cs = vtk.vtkPolyDataConnectivityFilter(); _cs.SetInputData(P_in)
    _cs.SetExtractionModeToSpecifiedRegions()
    for r in _keep_ids:
        _cs.AddSpecifiedRegion(int(r))
    _cs.Update()
    _cl2 = vtk.vtkCleanPolyData(); _cl2.SetInputData(_cs.GetOutput()); _cl2.SetTolerance(0.0); _cl2.Update()
    P_in = _cl2.GetOutput()
    say("  patch inside the core: %d component(s); kept %d that reach the core wall, dropped %d closed fragment(s) (%d cells)"
        % (_nreg, len(_keep_ids), len(_drop), int(sum(int(_sizes[r]) for r in _drop))))
stats(P_in, "patch, components kept")

PCLEAN = float(os.environ.get("CC_PCLEAN", "0.0"))
if PCLEAN > 0:
    pc = vtk.vtkCleanPolyData()
    pc.SetInputData(P_in)
    pc.ToleranceIsAbsoluteOn()
    pc.SetAbsoluteTolerance(PCLEAN)
    pc.PointMergingOn()
    pc.Update()
    tfc = vtk.vtkTriangleFilter()
    tfc.SetInputData(pc.GetOutput())
    tfc.PassLinesOff()
    tfc.PassVertsOff()
    tfc.Update()
    P_in = tfc.GetOutput()
    stats(P_in, "patch cleaned (merge within %.4f mm)" % PCLEAN)

SMOOTH = int(os.environ.get("CC_SMOOTH", "0"))
if SMOOTH > 0:
    sm = vtk.vtkWindowedSincPolyDataFilter()
    sm.SetInputData(P_in)
    sm.SetNumberOfIterations(SMOOTH)
    sm.SetPassBand(float(os.environ.get("CC_PASSBAND", "0.05")))
    sm.SetFeatureAngle(float(os.environ.get("CC_FEATANG", "50.0")))
    sm.BoundarySmoothingOff()
    sm.FeatureEdgeSmoothingOff()
    sm.NonManifoldSmoothingOff()
    sm.NormalizeCoordinatesOn()
    sm.Update()
    _before = numpy_support.vtk_to_numpy(P_in.GetPoints().GetData()).copy()
    P_in = sm.GetOutput()
    _after = numpy_support.vtk_to_numpy(P_in.GetPoints().GetData())
    _d = np.linalg.norm(_after - _before, axis=1)
    stats(P_in, "patch smoothed (%d iter, passband %s)" % (SMOOTH, os.environ.get("CC_PASSBAND", "0.05")))
    say("     it moved the patch: mean %.4f  p99 %.4f  MAX %.4f mm" % (_d.mean(), np.percentile(_d, 99),
                                                                       _d.max()))

if DECIM > 0:
    n_before = P_in.GetNumberOfCells()
    d = vtk.vtkDecimatePro()
    d.SetInputData(P_in)
    d.SetTargetReduction(DECIM)
    d.BoundaryVertexDeletionOff()
    d.PreserveTopologyOn()
    d.SetFeatureAngle(35.0)
    d.SplittingOff()
    d.SetMaximumError(DECERR)
    d.Update()
    P_in = d.GetOutput()
    got = 1.0 - P_in.GetNumberOfCells() / float(max(1, n_before))
    stats(P_in, "patch decimated (asked %.0f%%, got %.1f%%, error cap %.3f mm)"
          % (100 * DECIM, 100 * got, DECERR))


def loops_of(pd):
    """Trace closed boundary loops from the boundary EDGES directly.

    vtkStripper was used first and dropped every loop the clip had made: it returns polylines and does not
    reliably close them (first id != last id), so a test for an explicitly closed strip found 0 of 14 body
    loops and 0 of 3 patch loops. Building the adjacency and walking it is a few lines and cannot be fooled
    by how the stripper happens to break a curve into segments.
    """
    fe = vtk.vtkFeatureEdges(); fe.SetInputData(pd)
    fe.BoundaryEdgesOn(); fe.FeatureEdgesOff(); fe.NonManifoldEdgesOff(); fe.ManifoldEdgesOff(); fe.Update()
    o = fe.GetOutput()
    if o.GetNumberOfPoints() == 0:
        return []
    pts = numpy_support.vtk_to_numpy(o.GetPoints().GetData())
    key = {}
    remap = np.empty(len(pts), np.int64)
    uniq = []
    for i_, q in enumerate(pts):
        k = (round(float(q[0]), 6), round(float(q[1]), 6), round(float(q[2]), 6))
        if k not in key:
            key[k] = len(uniq)
            uniq.append(q)
        remap[i_] = key[k]
    uniq = np.asarray(uniq, float)
    adj = {}
    lines = o.GetLines()
    lines.InitTraversal()
    ids = vtk.vtkIdList()
    while lines.GetNextCell(ids):
        n_ = ids.GetNumberOfIds()
        for k in range(n_ - 1):
            u, v = int(remap[ids.GetId(k)]), int(remap[ids.GetId(k + 1)])
            if u == v:
                continue
            adj.setdefault(u, set()).add(v)
            adj.setdefault(v, set()).add(u)
    seen, out = set(), []
    for start in adj:
        if start in seen or len(adj[start]) != 2:
            continue
        loop, cur, prev = [start], start, None
        seen.add(start)
        while True:
            nxt = None
            for c in adj[cur]:
                if c != prev and (c not in seen or c == start):
                    nxt = c
                    break
            if nxt is None or nxt == start:
                break
            loop.append(nxt)
            seen.add(nxt)
            prev, cur = cur, nxt
        if len(loop) >= 4:
            out.append(uniq[loop])
    return out


# boundary edges  over the

def on_core(L, slack=1.15):
    return bool(np.all(np.abs(L - CENa) <= RADa * slack + 0.5))


if os.environ.get("CC_DUMP_PARTS"):
    _stem = os.path.splitext(os.environ["CC_OUT"])[0]
    for _pd, _nm in ((B_out, "_bodyhole.stl"), (P_in, "_patchcore.stl")):
        _tw = vtk.vtkSTLWriter(); _tw.SetFileName(_stem + _nm); _tw.SetInputData(_pd)
        _tw.SetFileTypeToBinary(); _tw.Write()
        say("dumped %s (%d triangles)" % (_stem + _nm, _pd.GetNumberOfCells()))

_la_all, _lb_all = loops_of(B_out), loops_of(P_in)
say("")
say("boundary loops traced: body %d, patch %d" % (len(_la_all), len(_lb_all)))
for nm, LL in (("body", _la_all), ("patch", _lb_all)):
    for k, L in enumerate(LL):
        c = L.mean(0)
        say("   %-5s loop %2d: %5d pts  centroid (%8.2f %9.2f %8.2f)  %s"
            % (nm, k, len(L), c[0], c[1], c[2], "ON THE CORE" if on_core(L) else "elsewhere"))
LA = [L for L in _la_all if on_core(L)]
LB = [L for L in _lb_all if on_core(L)]
say("kept: body %d, patch %d" % (len(LA), len(LB)))
if not LA or not LB:
    say("FAIL: one side has no closed boundary loop - the core is not cleanly crossing the surface.")
    raise SystemExit(1)

pairs = []
used = set()
for i, A in enumerate(LA):
    best, bd = None, 1e18
    for j, B in enumerate(LB):
        if j in used:
            continue
        dd = float(np.linalg.norm(A.mean(0) - B.mean(0)))
        if dd < bd:
            best, bd = j, dd
    if best is None:
        break
    MAXPAIR = float(os.environ.get("CC_MAXPAIR", "6.0"))
    if bd > MAXPAIR:
        say("   body loop %d has NO patch loop within %.1f mm (nearest %.1f) - left unpaired, the seam "
            "there will stay open" % (i, MAXPAIR, bd))
        continue
    used.add(best)
    pairs.append((i, best, bd))
    say("   pair: body %d <-> patch %d, centroids %.2f mm apart" % (i, best, bd))
if len(pairs) != len(LA) or len(LA) != len(LB):
    say("WARNING: %d body loops, %d patch loops, %d pairs - an unpaired loop will be left open"
        % (len(LA), len(LB), len(pairs)))


def zipper(A, B):
    """Triangulate the ribbon between two closed polylines. Walks both, advancing whichever side's next
    edge is shorter. Needs no matching vertex counts and no tolerance."""
    na, nb = len(A), len(B)
    j0 = int(np.argmin(np.linalg.norm(B - A[0], axis=1)))
    B = np.roll(B, -j0, axis=0)
    ta = A[1 % na] - A[0]
    tb = B[1 % nb] - B[0]
    if float(np.dot(ta, tb)) < 0:
        B = np.vstack([B[:1], B[1:][::-1]])
    emitted = set()

    pairidx = {}
    if len(A) and len(B):
        from scipy.spatial import cKDTree
        tr_ = cKDTree(A)
        dd_, ii_ = tr_.query(B, distance_upper_bound=1e-6)
        for j_, (dist_, i_) in enumerate(zip(dd_, ii_)):
            if dist_ < 1e-6 and i_ < len(A):
                pairidx[j_] = int(i_)

    def lab(side, k):
        """one label per POINT, not per (loop, index)"""
        if side == "B" and k in pairidx:
            return ("A", pairidx[k])
        return (side, k)

    def emit(t):
        t = tuple(lab(sd, k) for sd, k in t)
        key = tuple(sorted(t))
        if key in emitted or len(set(t)) < 3:
            return
        emitted.add(key)
        tris.append(t)

    tris, i, j = [], 0, 0
    while i < na or j < nb:
        adv_a = (j >= nb) or (i < na and
                              np.linalg.norm(A[(i + 1) % na] - B[j % nb]) <=
                              np.linalg.norm(A[i % na] - B[(j + 1) % nb]))
        if adv_a:
            emit((("A", i % na), ("A", (i + 1) % na), ("B", j % nb)))
            i += 1
        else:
            emit((("A", i % na), ("B", (j + 1) % nb), ("B", j % nb)))
            j += 1
    return B, tris


say("")
_dp = vtk.vtkImplicitPolyDataDistance(); _dp.SetInput(P_in)
_db = vtk.vtkImplicitPolyDataDistance(); _db.SetInput(B_out)
say("seam gap (what the ribbon has to span - the client's fingernail threshold is 0.15 mm):")
for _bi, _pi, _cd in pairs:
    _A, _B = LA[_bi], LB[_pi]
    _da = np.array([abs(_dp.EvaluateFunction(float(q[0]), float(q[1]), float(q[2]))) for q in _A])
    _db_ = np.array([abs(_db.EvaluateFunction(float(q[0]), float(q[1]), float(q[2]))) for q in _B])
    say("   pair %d/%d  body vertices off the patch : mean %.4f  p95 %.4f  MAX %.4f mm"
        % (_bi, _pi, _da.mean(), np.percentile(_da, 95), _da.max()))
    say("             patch vertices off the body : mean %.4f  p95 %.4f  MAX %.4f mm"
        % (_db_.mean(), np.percentile(_db_, 95), _db_.max()))

SEAMSTEP = float(os.environ.get("CC_SEAMSTEP", "0"))


def resample_loop(L, step):
    """walk a closed polyline at a fixed arc-length spacing, staying ON it"""
    if step <= 0 or len(L) < 4:
        return L
    seg = np.linalg.norm(np.roll(L, -1, axis=0) - L, axis=1)
    per = float(seg.sum())
    if per <= step * 3:
        return L
    n = max(3, int(round(per / step)))
    want = np.arange(n) * (per / n)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    out = []
    for s in want:
        k = int(np.searchsorted(cum, s, side="right") - 1)
        k = min(max(k, 0), len(L) - 1)
        d = seg[k]
        t = 0.0 if d <= 1e-12 else (s - cum[k]) / d
        out.append(L[k] + t * (L[(k + 1) % len(L)] - L[k]))
    return np.asarray(out, float)


JOIN = os.environ.get("CC_JOIN", "seamweld").strip().lower()
SEAMTOL = float(os.environ.get("CC_SEAMTOL", "0.15"))
ZIPWHY = os.environ.get("CC_ZIPPER_WHY", "").strip()
if SEAMTOL > 0.15 + 1e-12:
    say("REFUSED: CC_SEAMTOL %.3f is above the 0.15 mm ceiling, which may only be reduced." % SEAMTOL)
    raise SystemExit(2)
if JOIN not in ("seamweld", "zipper", "seammerge"):
    say("REFUSED: CC_JOIN must be seamweld, seammerge or zipper, not %r" % JOIN)
    raise SystemExit(2)
if JOIN == "zipper" and not ZIPWHY:
    say("REFUSED: the zipper is the RETIRED join (route A gate 2, 2026-09-22) - its seam bridged 3.3 mm on the")
    say("  accepted V2 and nothing held it to 0.15. The join is kit seamweld. To run the zipper for a")
    say("  comparison, set CC_ZIPPER_WHY to the reason; the status file records it and the result is not a deliverable.")
    raise SystemExit(2)
extraV, extraT = [], []
if JOIN == "seammerge":
    import kitlib_render as KR
    sys.path.insert(0, SRC)
    import _ccseam as CS

    def _pd_np2(pd_):
        tf_ = vtk.vtkTriangleFilter(); tf_.SetInputData(pd_); tf_.PassLinesOff(); tf_.PassVertsOff(); tf_.Update()
        o_ = tf_.GetOutput()
        return (np.asarray(numpy_support.vtk_to_numpy(o_.GetPoints().GetData()), float),
                numpy_support.vtk_to_numpy(o_.GetPolys().GetData()).reshape(-1, 4)[:, 1:].astype(int))
    say("seammerge (explicit ordered partners, tolerance %.3f mm):" % SEAMTOL)
    _VA, _TA = _pd_np2(B_out); _VB, _TB = _pd_np2(P_in)
    _WV, _WT, _rep = CS.seam_merge(_VA, _TA, _VB, _TB, tol=SEAMTOL, assign=KR._assign)
    _rep.pop("_V", None); _rep.pop("_T", None)
    say("   loops %s and %s, %s paired, %s unrelated; worst gap %.4f mm, largest move %.4f mm, micro-holes capped %s"
        % (_rep.get("loopsA"), _rep.get("loopsB"), _rep.get("loops_paired"), _rep.get("loops_unrelated"),
           _rep.get("worst_mm", 0), _rep.get("largest_move_mm", 0), _rep.get("micro_holes_capped", 0)))
    if _WV is None:
        say("REFUSED by the seam: %s" % _rep.get("error", "the weld could not be made"))
        json.dump({"state": "REFUSED", "join": "seammerge", "why": _rep.get("error", ""), "report": _rep,
                   "seconds": round(time.time() - t0, 1)},
                  io.open(STATUS, "w", encoding="utf-8"), indent=1, default=float)
        raise SystemExit(2)
    say("   seam open %s, open edges out %s (inputs' own elsewhere), non-manifold %s (inputs %s); patch facing "
        "agreement near the rim %s -> %s; directed edges used twice %s"
        % (_rep.get("seam_open"), _rep.get("open_out"), _rep.get("nonmanifold_out"), _rep.get("nonmanifold_in"),
           _rep.get("facing_agreement_near_rim"), "FLIPPED to face out" if _rep.get("patch_flipped") else "kept",
           _rep.get("same_direction_edges_out")))
    res = to_pd(_WV, _WT)
    tfl = vtk.vtkTriangleFilter(); tfl.SetInputData(res); tfl.PassLinesOff(); tfl.PassVertsOff(); tfl.Update()
    res = tfl.GetOutput()
    ribbon = None
elif JOIN == "seamweld":
    import kitlib_render as KR

    def _pd_np(pd_):
        tf_ = vtk.vtkTriangleFilter(); tf_.SetInputData(pd_); tf_.PassLinesOff(); tf_.PassVertsOff(); tf_.Update()
        o_ = tf_.GetOutput()
        return (np.asarray(numpy_support.vtk_to_numpy(o_.GetPoints().GetData()), float),
                numpy_support.vtk_to_numpy(o_.GetPolys().GetData()).reshape(-1, 4)[:, 1:].astype(int))

    def _rimof(V_, T_):
        e_ = np.vstack([T_[:, [0, 1]], T_[:, [1, 2]], T_[:, [2, 0]]])
        u_, c_ = np.unique(np.sort(e_, axis=1), axis=0, return_counts=True)
        return [(int(x_), int(y_)) for x_, y_ in u_[c_ == 1]]
    say("seamweld (kit seamweld's weld_rims, tolerance %.3f mm):" % SEAMTOL)
    _VA, _TA = _pd_np(B_out); _VB, _TB = _pd_np(P_in)
    _VA, _TA, _r1, _ = KR._weld(_VA, _TA, [], SEAMTOL * 1e-3)
    _VB, _TB, _r2, _ = KR._weld(_VB, _TB, [], SEAMTOL * 1e-3)
    _rA, _rB = _rimof(_VA, _TA), _rimof(_VB, _TB)
    _WV, _WT, _rep = KR.weld_rims(_VA, _TA, _rA, _VB, _TB, _rB, tol=SEAMTOL, require_all_paired=False)
    say("   loops %s and %s, %s paired, %s unrelated (the part's own open edges, left alone)"
        % (_rep.get("loopsA"), _rep.get("loopsB"), _rep.get("loops_paired"), _rep.get("loops_unrelated", 0)))
    if _WV is None:
        say("REFUSED by the seam: %s" % _rep.get("error", "the weld could not be made"))
        say("  The core wall must sit on surface the edit did not touch - run `kit coreplace` on this patch.")
        json.dump({"state": "REFUSED", "join": "seamweld", "why": _rep.get("error", ""), "chain_ok": CHAIN_OK,
                   "core_cen": CEN, "core_rad": RAD, "seconds": round(time.time() - t0, 1)},
                  io.open(STATUS, "w", encoding="utf-8"), indent=1)
        raise SystemExit(2)
    say("   rim refined %d -> %d and %d -> %d edges; worst rim vertex moved %.4f mm; non-manifold %d"
        % (_rep["rimA_edges0"], _rep["rimA_edges"], _rep["rimB_edges0"], _rep["rimB_edges"],
           _rep["worst_mm"], _rep["nonmanifold_out"]))
    res = to_pd(_WV, _WT)
    tfl = vtk.vtkTriangleFilter(); tfl.SetInputData(res); tfl.PassLinesOff(); tfl.PassVertsOff(); tfl.Update()
    res = tfl.GetOutput()
    ribbon = None
else:
    say("zippering (RETIRED join, comparison only - CC_ZIPPER_WHY: %s):" % ZIPWHY)
for (ia, ib, dd) in (pairs if JOIN == "zipper" else []):
    A, B = LA[ia], LB[ib]
    if SEAMSTEP > 0:
        nA0, nB0 = len(A), len(B)
        A = resample_loop(A, SEAMSTEP)
        B = resample_loop(B, SEAMSTEP)
        say("   pair %d/%d resampled at %.3f mm: body %d -> %d, patch %d -> %d"
            % (ia, ib, SEAMSTEP, nA0, len(A), nB0, len(B)))
    B2, tris = zipper(A, B)
    base = len(extraV)
    extraV.extend([tuple(q) for q in A])
    off = len(extraV)
    extraV.extend([tuple(q) for q in B2])
    for (sa, a), (sb, b), (sc, c) in tris:
        f = lambda s, k: (base + k) if s == "A" else (off + k)
        extraT.append((f(sa, a), f(sb, b), f(sc, c)))
    say("   loop pair %d/%d: %d + %d points -> %d ribbon triangles" % (ia, ib, len(A), len(B2), len(tris)))

if JOIN == "zipper":
    ribbon = to_pd(np.asarray(extraV, float), np.asarray(extraT, int)) if extraT else None

    ap = vtk.vtkAppendPolyData()
    ap.AddInputData(B_out)
    ap.AddInputData(P_in)
    if ribbon is not None:
        ap.AddInputData(ribbon)
    ap.Update()
    cl = vtk.vtkCleanPolyData()
    cl.SetInputData(ap.GetOutput())
    cl.SetTolerance(0.0)
    cl.PointMergingOn()
    cl.Update()
    res = cl.GetOutput()
    tfl = vtk.vtkTriangleFilter(); tfl.SetInputData(res); tfl.PassLinesOff(); tfl.PassVertsOff(); tfl.Update()
    res = tfl.GetOutput()
say("")
say("result:")
nb = stats(res, "welded")

mp = vtk.vtkMassProperties(); mp.SetInputData(res)
try:
    vol = float(mp.GetVolume())
except Exception:
    vol = float("nan")
_refvol = sh.Volume if "sh" in dir() else _body_in_vol
say("  enclosed volume %.1f mm3 (the body is %.1f)" % (vol, _refvol))

_rv = numpy_support.vtk_to_numpy(res.GetPoints().GetData())
_ov = numpy_support.vtk_to_numpy(body_pd.GetPoints().GetData())
_olo, _ohi = _ov.min(0) - 0.001, _ov.max(0) + 0.001
_bad = ((_rv < _olo) | (_rv > _ohi)).any(1) | ~np.isfinite(_rv).all(1)
if _bad.any():
    say("  *** SPIKE GATE: %d result vertices lie outside the body's own extent ***" % int(_bad.sum()))
    for _q in _rv[_bad][:5]:
        say("        (%10.3f %10.3f %10.3f)" % (_q[0], _q[1], _q[2]))
    raise SystemExit("refusing to write a mesh with a vertex outside the part")
say("  spike gate: every result vertex is inside the body's own extent")

if OUT:
    w = vtk.vtkSTLWriter(); w.SetFileName(OUT); w.SetInputData(res); w.SetFileTypeToBinary(); w.Write()
    say("  wrote %s (%.1f MB)" % (OUT, os.path.getsize(OUT) / 1e6))

json.dump({"state": "done", "join": JOIN, "zipper_why": ZIPWHY if JOIN == "zipper" else "",
           "seam_tol": SEAMTOL, "chain_ok": CHAIN_OK, "body_tris": int(len(BT)), "kept": int(B_out.GetNumberOfCells()),
           "patch": int(P_in.GetNumberOfCells()), "ribbon": int(len(extraT)),
           "result_tris": int(res.GetNumberOfCells()), "open_edges": int(nb),
           "volume": round(vol, 1), "decim": DECIM, "seconds": round(time.time() - t0, 1)},
          io.open(STATUS, "w", encoding="utf-8"), indent=1)
say("")
say("%.0f s" % (time.time() - t0))
say("DONE")

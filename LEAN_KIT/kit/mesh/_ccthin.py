import io, json, os, sys, time
import numpy as np
sys.path.insert(0, os.environ["KIT_HOME"])
import vtk

HERE = os.environ.get("CC_WORK") or os.path.dirname(os.path.abspath(__file__))
_ow = vtk.vtkFileOutputWindow()
_ow.SetFileName(os.path.join(HERE, "vtk_messages.log"))
_ow.SetFlush(0)
vtk.vtkOutputWindow.SetInstance(_ow)
vtk.vtkObject.GlobalWarningDisplayOff()

t0 = time.time()
BOX = [float(t) for t in os.environ["CC_BOX"].split()]
THIN = float(os.environ.get("CC_THIN", "0.70"))
HARD = float(os.environ.get("CC_HARD", "0.50"))
OFF = float(os.environ.get("CC_OFF", "0.01"))
MAXT = float(os.environ.get("CC_MAXT", "40.0"))


def say(*a):
    print(*a, flush=True)


def read(path):
    r = vtk.vtkSTLReader()
    r.SetFileName(path)
    r.Update()
    return r.GetOutput()


pd = read(os.environ["CC_RESULT"])
nf = vtk.vtkPolyDataNormals()
nf.SetInputData(pd)
nf.ComputeCellNormalsOn()
nf.ComputePointNormalsOff()
nf.SplittingOff()
nf.ConsistencyOn()
nf.AutoOrientNormalsOn()
nf.Update()
pd = nf.GetOutput()
N = pd.GetCellData().GetNormals()
say("mesh: %d triangles" % pd.GetNumberOfCells())

tree = vtk.vtkOBBTree()
tree.SetDataSet(pd)
tree.SetTolerance(1e-9)
tree.BuildLocator()

ids = vtk.vtkIdList()
pts = vtk.vtkPoints()
cells = []
for c in range(pd.GetNumberOfCells()):
    pd.GetCellPoints(c, ids)
    if ids.GetNumberOfIds() != 3:
        continue
    p = np.asarray([pd.GetPoint(ids.GetId(k)) for k in range(3)], float)
    ctr = p.mean(0)
    if not (BOX[0] <= ctr[0] <= BOX[1] and BOX[2] <= ctr[1] <= BOX[3] and BOX[4] <= ctr[2] <= BOX[5]):
        continue
    cells.append((c, p, ctr))
say("triangles inside the region: %d" % len(cells))

need = []
for c, p, ctr in cells:
    e = np.array([np.linalg.norm(p[1] - p[0]), np.linalg.norm(p[2] - p[1]), np.linalg.norm(p[0] - p[2])])
    s = e.sum() / 2.0
    ar = 0.5 * float(np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0])))
    if ar <= 1e-12 or s <= 0:
        need.append((c, 1e9, ar))
        continue
    inr = ar / s
    need.append((c, float(e.max() / (2.0 * inr)), ar))
asp = np.array([n[1] for n in need])
area = np.array([n[2] for n in need])
say("")
say("NEEDLE TRIANGLES (aspect = longest edge / 2*inradius; 1 is equilateral)")
for lim in (10, 30, 100, 1000):
    say("   aspect over %5d : %6d triangles, %8.4f mm2 total" % (lim, int((asp > lim).sum()),
                                                                 float(area[asp > lim].sum())))

say("")
say("WALL THICKNESS by inward ray from each triangle (MJF PA12: %.2f mm is the reliability floor, "
    "%.2f mm the hard minimum)" % (THIN, HARD))
hits = vtk.vtkPoints()
cids = vtk.vtkIdList()
th = []
_cells = cells
if os.environ.get("CC_NEWREF"):
    from scipy.spatial import cKDTree as _KD
    import struct as _st
    _b = open(os.environ["CC_NEWREF"], "rb").read(); _n = _st.unpack("<I", _b[80:84])[0]
    _a = np.frombuffer(_b[84:84 + _n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    _bc = _a["v"].reshape(-1, 3, 3).astype(np.float64).mean(1)
    _bc = _bc[np.all((_bc >= np.array(BOX[0::2]) - 1) & (_bc <= np.array(BOX[1::2]) + 1), 1)]
    if len(_bc):
        _d = _KD(_bc).query(np.array([x[2] for x in cells]))[0]
        _cells = [x for x, dd in zip(cells, _d) if dd > 1e-4]
    say("   CC_NEWREF: rays from the %d new triangle(s) only (of %d in the region)" % (len(_cells), len(cells)))
step = max(1, len(_cells) // int(os.environ.get("CC_SAMPLE", "20000")))
for c, p, ctr in _cells[::step]:
    n = np.asarray(N.GetTuple(c), float)
    nn = np.linalg.norm(n)
    if nn < 1e-9:
        continue
    n /= nn
    a = ctr - n * OFF
    b = ctr - n * MAXT
    hits.Reset()
    cids.Reset()
    if tree.IntersectWithLine(a, b, hits, cids) == 0 or hits.GetNumberOfPoints() == 0:
        continue
    q = np.asarray(hits.GetPoint(0), float)
    th.append((float(np.linalg.norm(q - ctr)), c, ctr))
if not th:
    say("   no rays returned - nothing to report")
    raise SystemExit(0)
t = np.array([x[0] for x in th])
say("   %d rays" % len(t))
for lo, hi in ((0.0, 0.20), (0.20, HARD), (HARD, THIN), (THIN, 1.5), (1.5, 1e9)):
    n_ = int(((t >= lo) & (t < hi)).sum())
    say("   %5.2f to %6s mm : %6d   share %.1f pct" % (lo, ("%.2f" % hi) if hi < 1e8 else "inf", n_,
                                                       100.0 * n_ / len(t)))
say("   min %.4f  p01 %.4f  median %.4f mm" % (t.min(), np.percentile(t, 1), np.median(t)))
say("")
say("   the thinnest places:")
for d, c, ctr in sorted(th)[:8]:
    say("      %.4f mm at (%7.2f %8.2f %7.2f)" % (d, ctr[0], ctr[1], ctr[2]))

json.dump({"state": "done", "rays": len(t), "min_mm": float(t.min()),
           "under_hard": int((t < HARD).sum()), "under_thin": int((t < THIN).sum()),
           "needles_over_100": int((asp > 100).sum()), "seconds": round(time.time() - t0, 1)},
          io.open(os.path.join(HERE, "status_ccthin%s.json" % os.environ.get("LK_TAG", "")), "w", encoding="utf-8"), indent=1)
say("")
say("%.0f s" % (time.time() - t0))
say("DONE")

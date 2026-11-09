# KIT INSTRUMENT `diag_sign_field` - does a field's sign call AIR solid? nearest-triangle sign against six-ray parity, per region.
# Run: kit tool diag_sign_field --job <JOB> --set KEY=VALUE ...   (output lands in that job's folder)
# Inputs: CC_SHAPE (the brep)  CC_DEV  CC_BOX (the extract box)  CC_REGIONS "name:x0,x1,y0,y1,z0,z1;..."  CC_STEP  CC_OUTDIR. The check that the extract's sign fix holds on a real part.
import os, sys, json
import numpy as np
sys.path.insert(0, os.environ["KIT_HOME"])
import kitlib as K, Part
import vtk
from vtk.util import numpy_support as ns

os.makedirs(os.environ.get("CC_OUTDIR", "."), exist_ok=True)
_ow = vtk.vtkFileOutputWindow(); _ow.SetFileName(os.path.join(os.environ.get("CC_OUTDIR", "."), "vtk_messages.log"))
vtk.vtkOutputWindow.SetInstance(_ow); vtk.vtkObject.GlobalWarningDisplayOff()


def say(*a):
    print(*a, flush=True)


s = Part.Shape(); s.importBrep(os.environ["CC_SHAPE"])
DEV = float(os.environ.get("CC_DEV", "0.08"))
Vv, T, F = K.tess(s, DEV)
Vv = np.asarray(Vv, float); T = np.asarray(T, int)
say("body meshed exactly as the extract does: %d vertices, %d triangles (dev %.2f)" % (len(Vv), len(T), DEV))
BOX = [float(t) for t in os.environ["CC_BOX"].split()]
HALO = 6.0 + 3.0


def polydata(Vs, Ts):
    pts = vtk.vtkPoints(); pts.SetData(ns.numpy_to_vtk(np.ascontiguousarray(Vs, np.float64), deep=True))
    conn = np.empty((len(Ts), 4), np.int64); conn[:, 0] = 3; conn[:, 1:] = Ts
    cells = vtk.vtkCellArray(); cells.SetCells(len(Ts), ns.numpy_to_vtkIdTypeArray(conn.ravel(), deep=True))
    pd = vtk.vtkPolyData(); pd.SetPoints(pts); pd.SetPolys(cells); return pd


tmin = Vv[T].min(1); tmax = Vv[T].max(1)
keep = ((tmax[:, 0] >= BOX[0] - HALO) & (tmin[:, 0] <= BOX[1] + HALO) & (tmax[:, 1] >= BOX[2] - HALO)
        & (tmin[:, 1] <= BOX[3] + HALO) & (tmax[:, 2] >= BOX[4] - HALO) & (tmin[:, 2] <= BOX[5] + HALO))
Tl = T[keep]; used = np.unique(Tl); rm = -np.ones(len(Vv), np.int64); rm[used] = np.arange(len(used))
local = polydata(Vv[used], rm[Tl])
full = polydata(Vv, T)
imp = vtk.vtkImplicitPolyDataDistance(); imp.SetInput(local)
obb = vtk.vtkOBBTree(); obb.SetDataSet(full); obb.BuildLocator()

fe = vtk.vtkFeatureEdges(); fe.SetInputData(full)
fe.BoundaryEdgesOn(); fe.NonManifoldEdgesOn(); fe.FeatureEdgesOff(); fe.ManifoldEdgesOff(); fe.Update()
EP = ns.vtk_to_numpy(fe.GetOutput().GetPoints().GetData()) if fe.GetOutput().GetNumberOfPoints() else np.zeros((0, 3))
say("the body mesh's own open + non-manifold edge points: %d" % len(EP))

DIRS = np.array([[1, 0.013, 0.021], [-1, 0.017, -0.011], [0.019, 1, 0.013], [-0.023, -1, 0.017],
                 [0.011, 0.021, 1], [-0.013, 0.015, -1]], float)
DIRS /= np.linalg.norm(DIRS, axis=1)[:, None]


def parity_inside(p):
    votes = 0
    for d in DIRS:
        q = p + d * 600.0
        pts = vtk.vtkPoints()
        obb.IntersectWithLine(p, q, pts, None)
        votes += pts.GetNumberOfPoints() % 2
    return votes >= 4


STEP = float(os.environ.get("CC_STEP", "1.0"))
out = {}
for spec in os.environ["CC_REGIONS"].split(";"):
    nm, b = spec.split(":")
    b = [float(t) for t in b.split(",")]
    g = np.mgrid[b[0]:b[1] + 1e-6:STEP, b[2]:b[3] + 1e-6:STEP, b[4]:b[5] + 1e-6:STEP].reshape(3, -1).T
    sd = np.array([imp.EvaluateFunction(tuple(p)) for p in g])
    ins = np.array([parity_inside(p) for p in g])
    field_in = sd < 0
    wrong = field_in & ~ins
    near = 0
    if len(EP):
        m = ((EP[:, 0] >= b[0] - 10) & (EP[:, 0] <= b[1] + 10) & (EP[:, 1] >= b[2] - 10) & (EP[:, 1] <= b[3] + 10)
             & (EP[:, 2] >= b[4] - 10) & (EP[:, 2] <= b[5] + 10))
        near = int(m.sum())
    out[nm] = {"points": int(len(g)), "field_says_inside": int(field_in.sum()), "rays_say_inside": int(ins.sum()),
               "field_inside_but_rays_outside": int(wrong.sum()),
               "worst_wrong_depth_mm": round(float(-sd[wrong].min()), 2) if wrong.any() else 0.0,
               "open_edge_points_within_10mm": near}
    say("")
    say("%s  (%d points, %.1f mm grid)" % (nm, len(g), STEP))
    say("   the extract's field says INSIDE : %5d" % field_in.sum())
    say("   six-ray parity says INSIDE      : %5d" % ins.sum())
    say("   field INSIDE but rays OUTSIDE   : %5d   %s" % (wrong.sum(),
        ("worst: the field claims %.2f mm deep in solid" % -sd[wrong].min()) if wrong.any() else ""))
    say("   body open-edge points within 10 mm: %d" % near)
json.dump(out, open(os.path.join(os.environ.get("CC_OUTDIR", "."), "sign_field.json"), "w"), indent=1)
say("DONE")

# KIT INSTRUMENT `diag_openedges` - where are a mesh's own open edges - grouped into loops, sized, placed, written out to render.
# Run: kit tool diag_openedges --job <JOB> --set KEY=VALUE ...   (output lands in that job's folder)
# Inputs: CC_MESH  CC_OUTDIR  CC_TAG
import os, sys, json
import numpy as np
sys.path.insert(0, os.environ["KIT_HOME"])
import vtk
from vtk.util import numpy_support as ns

os.makedirs(os.environ["CC_OUTDIR"], exist_ok=True)
_ow = vtk.vtkFileOutputWindow(); _ow.SetFileName(os.path.join(os.environ["CC_OUTDIR"], "vtk_oe.log"))
vtk.vtkOutputWindow.SetInstance(_ow); vtk.vtkObject.GlobalWarningDisplayOff()

r = vtk.vtkSTLReader(); r.SetFileName(os.environ["CC_MESH"]); r.Update()
c = vtk.vtkCleanPolyData(); c.SetInputData(r.GetOutput()); c.Update()
pd = c.GetOutput()
fe = vtk.vtkFeatureEdges(); fe.SetInputData(pd)
fe.BoundaryEdgesOn(); fe.NonManifoldEdgesOn(); fe.FeatureEdgesOff(); fe.ManifoldEdgesOff(); fe.Update()
o = fe.GetOutput()
n = o.GetNumberOfCells()
print("%s: %d triangles, %d open + non-manifold edges" % (os.path.basename(os.environ["CC_MESH"]),
                                                           pd.GetNumberOfCells(), n), flush=True)
if n == 0:
    print("DONE", flush=True); raise SystemExit(0)
P = ns.vtk_to_numpy(o.GetPoints().GetData())
L = ns.vtk_to_numpy(o.GetLines().GetData()).reshape(-1, 3)[:, 1:]
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
key = {}
rid = np.empty(len(P), np.int64)
for i, q in enumerate(P):
    k = (round(float(q[0]), 5), round(float(q[1]), 5), round(float(q[2]), 5))
    rid[i] = key.setdefault(k, len(key))
E = rid[L]
g = coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(len(key), len(key)))
ncc, lab = connected_components(g, directed=False)
U = np.zeros((len(key), 3))
U[rid] = P
groups = []
for k in range(ncc):
    verts = np.where(lab == k)[0]
    edges = E[lab[E[:, 0]] == k]
    if not len(edges):
        continue
    seg = np.linalg.norm(U[edges[:, 0]] - U[edges[:, 1]], axis=1)
    groups.append((len(edges), float(seg.sum()), U[verts].mean(0), U[verts].min(0), U[verts].max(0)))
groups.sort(key=lambda t: -t[0])
print("%d chain(s) of open edges:" % len(groups), flush=True)
print("   %6s %8s   %-26s  %-40s" % ("edges", "len mm", "centroid", "extent x / y / z"), flush=True)
for ne, ln, cc, lo, hi in groups:
    print("   %6d %8.2f   (%7.2f %8.2f %6.2f)   x %6.1f..%6.1f  y %7.1f..%7.1f  z %5.1f..%5.1f"
          % (ne, ln, cc[0], cc[1], cc[2], lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]), flush=True)
w = vtk.vtkPolyDataWriter()
json.dump([{"edges": g[0], "length_mm": round(g[1], 2), "centroid": [round(float(v), 2) for v in g[2]],
            "min": [round(float(v), 2) for v in g[3]], "max": [round(float(v), 2) for v in g[4]]}
           for g in groups],
          open(os.path.join(os.environ["CC_OUTDIR"], "openedges_%s.json" % os.environ["CC_TAG"]), "w"), indent=1)
print("DONE", flush=True)

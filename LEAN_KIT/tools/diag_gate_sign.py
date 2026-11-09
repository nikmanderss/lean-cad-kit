# KIT INSTRUMENT `diag_gate_sign` - is a reinsertion-gate miss an ADD (the intended fill) or a CUT (damage to surface that should survive)?
# Run: kit tool diag_gate_sign --job <JOB> --set KEY=VALUE ...   (output lands in that job's folder)
# Inputs: CC_BODY  CC_PATCH  CC_BOX "x0 x1 y0 y1 z0 z1"  CC_TOL (0.10)  CC_OUTDIR
import os, sys, json
import numpy as np
sys.path.insert(0, os.environ["KIT_HOME"])
import vtk
from vtk.util import numpy_support as ns
from scipy.spatial import cKDTree

os.makedirs(os.environ["CC_OUTDIR"], exist_ok=True)
_ow = vtk.vtkFileOutputWindow(); _ow.SetFileName(os.path.join(os.environ["CC_OUTDIR"], "vtk_sign.log"))
vtk.vtkOutputWindow.SetInstance(_ow); vtk.vtkObject.GlobalWarningDisplayOff()


def say(*a):
    print(*a, flush=True)


def read(p):
    r = vtk.vtkSTLReader(); r.SetFileName(p); r.Update()
    return r.GetOutput()


def tri_samples(pd, box, per=3):
    """points ON the surface: triangle centroids plus the midpoints toward each vertex."""
    P = ns.vtk_to_numpy(pd.GetPoints().GetData())
    T = ns.vtk_to_numpy(pd.GetPolys().GetData()).reshape(-1, 4)[:, 1:]
    tri = P[T]
    c = tri.mean(1)
    m = ((c[:, 0] >= box[0]) & (c[:, 0] <= box[1]) & (c[:, 1] >= box[2]) & (c[:, 1] <= box[3])
         & (c[:, 2] >= box[4]) & (c[:, 2] <= box[5]))
    tri = tri[m]; c = c[m]
    return np.vstack([c] + [0.5 * (c + tri[:, k]) for k in range(per)])


BODY, PATCH = read(os.environ["CC_BODY"]), read(os.environ["CC_PATCH"])
BOX = [float(t) for t in os.environ["CC_BOX"].split()]
TOL = float(os.environ.get("CC_TOL", "0.10"))
inner = [BOX[0] + 1, BOX[1] - 1, BOX[2] + 1, BOX[3] - 1, BOX[4] + 1, BOX[5] - 1]
S = tri_samples(BODY, inner)
say("body samples in the inner box: %d  (ALL body surface there - a superset of the gate's keepers)" % len(S))

PP = ns.vtk_to_numpy(PATCH.GetPoints().GetData())
kd = cKDTree(PP)
d, j = kd.query(S)
miss = d > TOL
say("samples the patch misses by more than %.2f mm: %d (%.1f %%), max %.4f mm"
    % (TOL, int(miss.sum()), 100.0 * miss.mean(), float(d.max())))

sdf = vtk.vtkImplicitPolyDataDistance(); sdf.SetInput(BODY)
q = PP[j[miss]]
side = np.array([sdf.EvaluateFunction(tuple(p)) for p in q])
add = side > 0
res = {"samples": int(len(S)), "missed": int(miss.sum()), "max_mm": round(float(d.max()), 4),
       "ADD": {"n": int(add.sum()), "max_mm": round(float(d[miss][add].max()), 4) if add.any() else 0.0},
       "CUT": {"n": int((~add).sum()), "max_mm": round(float(d[miss][~add].max()), 4) if (~add).any() else 0.0}}
say("")
say("of the missed samples, the nearest patch point is:")
say("   OUTSIDE the body (material ADDED - the notch fill KEEP_ADD allows): %6d   worst %.4f mm"
    % (res["ADD"]["n"], res["ADD"]["max_mm"]))
say("   INSIDE  the body (material CUT   - a surface that should survive):  %6d   worst %.4f mm"
    % (res["CUT"]["n"], res["CUT"]["max_mm"]))
for lab, m in (("ADD", add), ("CUT", ~add)):
    if m.any():
        pts = S[miss][m]
        big = d[miss][m] > 1.0
        say("   %s samples over 1 mm: %d, at x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f"
            % (lab, int(big.sum()), *(sum(([pts[big][:, k].min(), pts[big][:, k].max()] for k in range(3)), [])
                                        if big.any() else [0] * 6)))
        res[lab]["over_1mm"] = int(big.sum())
json.dump(res, open(os.path.join(os.environ["CC_OUTDIR"], "gate_sign_%s.json"
                                 % os.path.splitext(os.path.basename(os.environ["CC_PATCH"]))[0]), "w"), indent=1)
np.savez_compressed(os.path.join(os.environ["CC_OUTDIR"], "gate_sign_%s.npz"
                                 % os.path.splitext(os.path.basename(os.environ["CC_PATCH"]))[0]),
                    pts=S[miss], d=d[miss], add=add)
say("DONE")

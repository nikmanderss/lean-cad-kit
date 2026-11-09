# KIT INSTRUMENT `diag_loops` - what IS each boundary loop a weld left unmatched: partner within 6 mm, patch off the real body, graze angle.
# Run: kit tool diag_loops --job <JOB> --set KEY=VALUE ...   (output lands in that job's folder)
# Inputs: CC_BODYHOLE CC_PATCHCORE (the halves _ccweld writes with CC_DUMP_PARTS)  CC_BODY  CC_CORE_CEN  CC_CORE_RAD  CC_OUTDIR. One STL per loop, to render.
import os, sys, json
import numpy as np
sys.path.insert(0, os.environ["KIT_HOME"])
import vtk
from vtk.util import numpy_support as ns

os.makedirs(os.environ["CC_OUTDIR"], exist_ok=True)
_ow = vtk.vtkFileOutputWindow(); _ow.SetFileName(os.path.join(os.environ["CC_OUTDIR"], "vtk.log"))
vtk.vtkOutputWindow.SetInstance(_ow); vtk.vtkObject.GlobalWarningDisplayOff()


def say(*a):
    print(*a, flush=True)


def read(p):
    r = vtk.vtkSTLReader(); r.SetFileName(p); r.Update()
    c = vtk.vtkCleanPolyData(); c.SetInputData(r.GetOutput()); c.Update()
    return c.GetOutput()


def loops_of(pd):
    fe = vtk.vtkFeatureEdges(); fe.SetInputData(pd)
    fe.BoundaryEdgesOn(); fe.FeatureEdgesOff(); fe.NonManifoldEdgesOff(); fe.ManifoldEdgesOff(); fe.Update()
    o = fe.GetOutput()
    if o.GetNumberOfPoints() == 0:
        return []
    pts = ns.vtk_to_numpy(o.GetPoints().GetData())
    key, remap, uniq = {}, np.empty(len(pts), np.int64), []
    for i, q in enumerate(pts):
        k = (round(float(q[0]), 6), round(float(q[1]), 6), round(float(q[2]), 6))
        if k not in key:
            key[k] = len(uniq); uniq.append(q)
        remap[i] = key[k]
    uniq = np.asarray(uniq, float)
    adj = {}
    ln = o.GetLines(); ln.InitTraversal(); ids = vtk.vtkIdList()
    while ln.GetNextCell(ids):
        for k in range(ids.GetNumberOfIds() - 1):
            u, v = int(remap[ids.GetId(k)]), int(remap[ids.GetId(k + 1)])
            if u != v:
                adj.setdefault(u, set()).add(v); adj.setdefault(v, set()).add(u)
    seen, out = set(), []
    for s in adj:
        if s in seen or len(adj[s]) != 2:
            continue
        loop, cur, prev = [s], s, None
        seen.add(s)
        while True:
            nxt = None
            for c in adj[cur]:
                if c != prev and (c not in seen or c == s):
                    nxt = c; break
            if nxt is None or nxt == s:
                break
            loop.append(nxt); seen.add(nxt); prev, cur = cur, nxt
        if len(loop) >= 4:
            out.append(uniq[loop])
    return out


CEN = np.array([float(t) for t in os.environ["CC_CORE_CEN"].split()])
RAD = np.array([float(t) for t in os.environ["CC_CORE_RAD"].split()])
OUT = os.environ["CC_OUTDIR"]; os.makedirs(OUT, exist_ok=True)
BH, PC, BODY = read(os.environ["CC_BODYHOLE"]), read(os.environ["CC_PATCHCORE"]), read(os.environ["CC_BODY"])
say("body-with-hole %d tri, patch-in-core %d tri, full body %d tri"
    % (BH.GetNumberOfCells(), PC.GetNumberOfCells(), BODY.GetNumberOfCells()))


def on_core(L):
    return bool(np.all(np.abs(L - CEN) <= RAD * 1.15 + 0.5))


LB = [L for L in loops_of(BH) if on_core(L)]
LP = [L for L in loops_of(PC) if on_core(L)]
say("loops on the core: body-with-hole %d, patch %d" % (len(LB), len(LP)))

dist = vtk.vtkImplicitPolyDataDistance(); dist.SetInput(BODY)

P = ns.vtk_to_numpy(PC.GetPoints().GetData())
polys = ns.vtk_to_numpy(PC.GetPolys().GetData()).reshape(-1, 4)[:, 1:]
tri = P[polys]
tc = tri.mean(1)
tn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
ta = 0.5 * np.linalg.norm(tn, axis=1)
tn = tn / np.maximum(np.linalg.norm(tn, axis=1), 1e-12)[:, None]
from scipy.spatial import cKDTree
kd = cKDTree(tc)

rows = []
for which, LL in (("patch", LP), ("body", LB)):
    for k, L in enumerate(LL):
        c = L.mean(0)
        length = float(np.linalg.norm(np.diff(np.vstack([L, L[:1]]), axis=0), axis=1).sum())
        others = LB if which == "patch" else LP
        dmin = min([float(np.linalg.norm(o.mean(0) - c)) for o in others] or [1e9])
        row = {"side": which, "loop": k, "pts": len(L), "length_mm": round(length, 2),
               "centroid": [round(float(v), 2) for v in c],
               "bbox_min": [round(float(v), 2) for v in L.min(0)],
               "bbox_max": [round(float(v), 2) for v in L.max(0)],
               "nearest_partner_mm": round(dmin, 2), "partnered": dmin <= 6.0}
        if which == "patch":
            near = sorted(set(i for q in L for i in kd.query_ball_point(q, 1.0)))
            if near:
                near = np.array(near)
                d = np.array([abs(dist.EvaluateFunction(tuple(p))) for p in tc[near]])
                g = (L - CEN) / (RAD ** 2)
                g = g / np.maximum(np.linalg.norm(g, axis=1), 1e-12)[:, None]
                gm = g.mean(0); gm = gm / max(np.linalg.norm(gm), 1e-12)
                nm = (tn[near] * ta[near, None]).sum(0); nm = nm / max(np.linalg.norm(nm), 1e-12)
                cross_deg = float(np.degrees(np.arccos(np.clip(abs(float(nm @ gm)), 0, 1))))
                row.update({"adj_tris": int(len(near)), "adj_area_mm2": round(float(ta[near].sum()), 2),
                            "patch_to_body_mean_mm": round(float(d.mean()), 3),
                            "patch_to_body_max_mm": round(float(d.max()), 3),
                            "patch_normal": [round(float(v), 3) for v in nm],
                            "crossing_angle_deg": round(90.0 - cross_deg, 1)})
                cells = vtk.vtkCellArray()
                for i in near:
                    cells.InsertNextCell(3); [cells.InsertCellPoint(int(v)) for v in polys[i]]
                sub = vtk.vtkPolyData(); sub.SetPoints(PC.GetPoints()); sub.SetPolys(cells)
                w = vtk.vtkSTLWriter(); w.SetFileName(os.path.join(OUT, "loop_patch_%d.stl" % k))
                w.SetInputData(sub); w.SetFileTypeToBinary(); w.Write()
        rows.append(row)

say("")
say("%-6s %4s %6s %8s  %-26s %9s %8s %9s %9s %7s"
    % ("side", "loop", "pts", "len mm", "centroid", "partner", "adj mm2", "->body", "->bodyMX", "cross"))
for r in rows:
    say("%-6s %4d %6d %8.1f  (%7.2f %8.2f %6.2f) %8.1f%s %8s %9s %9s %7s"
        % (r["side"], r["loop"], r["pts"], r["length_mm"], *r["centroid"], r["nearest_partner_mm"],
           " " if r["partnered"] else "!", r.get("adj_area_mm2", "-"),
           r.get("patch_to_body_mean_mm", "-"), r.get("patch_to_body_max_mm", "-"),
           r.get("crossing_angle_deg", "-")))
json.dump(rows, open(os.path.join(OUT, "loops.json"), "w"), indent=1)
say("")
say("! = no loop on the other side within 6 mm.  ->body = patch triangles next to the loop, distance to the")
say("REAL body surface.  cross = angle at which the core wall crosses the patch (90 = straight across, near")
say("0 = tangent, which is the clip-artefact signature).")
say("DONE")

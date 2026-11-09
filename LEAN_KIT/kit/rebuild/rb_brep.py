# kit rebuild
import os, sys, time, numpy as np, Part, FreeCAD, Mesh
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
TAG = os.environ.get("LK_TAG", "")
T0 = time.time(); src = os.environ["STL"]; out = os.environ["OUT"]
if not os.path.isfile(src) or os.path.getsize(src) < 1000: print("FAIL: rb_brep: the input STL is missing or empty (%s) - the step before it refused or was never run; nothing to convert" % src, flush=True); raise SystemExit(1)
m = Mesh.Mesh(src); comps = m.getSeparateComponents() if m.countComponents() > 1 else [m]
comps.sort(key=lambda c: -c.CountFacets); sols = []; MIN_MM3 = float(os.environ.get("MIN_MM3", "0.5"))
for c in comps:
    pts = [(p.x, p.y, p.z) for p in c.Points]; fac = [(f.PointIndices[0], f.PointIndices[1], f.PointIndices[2]) for f in c.Facets]
    sh = Part.Shape(); sh.makeShapeFromMesh((pts, fac), 0.001, True)
    shell = sh.Shells[0] if sh.Shells else Part.Shell(sh.Faces); so = Part.Solid(shell)
    if so.Volume < 0: so.reverse()
    try:
        su = so.removeSplitter()
        if su.isValid() and abs(su.Volume - so.Volume) < 0.5: print("    coplanar triangles merged: %d -> %d faces" % (len(so.Faces), len(su.Faces)), flush=True); so = su
        else: print("    removeSplitter result rejected (valid %s vol %.2f)" % (su.isValid(), su.Volume), flush=True)
    except Exception as ex: print("    removeSplitter refused:", ex, flush=True)
    if abs(so.Volume) < MIN_MM3: print("  component dropped (%.3f mm3 < MIN_MM3)" % so.Volume, flush=True); continue
    sols.append(so); print("  component -> solid: valid %s vol %.2f faces %d" % (so.isValid(), so.Volume, len(so.Faces)), flush=True)
comp = Part.makeCompound(sols); comp.exportBrep(out)
print("piece: %d solid(s), total %.1f mm3, all valid %s, faces %d (%.0fs); WROTE %s" % (len(sols), sum(x.Volume for x in sols), all(x.isValid() for x in sols), sum(len(x.Faces) for x in sols), time.time() - T0, out), flush=True)
import json
json.dump({"tag": TAG, "source": os.environ["STL"], "out": out, "MIN_MM3": MIN_MM3, "solids": [round(x.Volume, 2) for x in sols], "faces": int(sum(len(x.Faces) for x in sols)), "all_valid": bool(all(x.isValid() for x in sols))},
          open(os.path.join(os.path.dirname(os.path.abspath(out)), "REBUILD_brep.json"), "w"), indent=1)

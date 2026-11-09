# CC_OUTDIR
import os, sys, time
sys.path.insert(0, os.environ["KIT_HOME"])
import Part, MeshPart

TAG = os.environ.get("LK_TAG", "")
DEV = float(os.environ.get("CC_DEV", "0.02"))
os.makedirs(os.environ["CC_OUTDIR"], exist_ok=True)
for nm in [r.strip() for r in os.environ["CC_REGIONS"].split(",") if r.strip()]:
    t = time.time()
    s = Part.Shape(); s.importBrep(os.path.join(os.environ["CC_SRCDIR"], nm + ".brep"))
    m = MeshPart.meshFromShape(Shape=s, LinearDeflection=DEV, AngularDeflection=0.2, Relative=False)
    out = os.path.join(os.environ["CC_OUTDIR"], nm + ".stl")
    m.write(out)
    print("%-22s %4d faces -> %8d facets  %s  (%.0f s)" % (nm, len(s.Faces), m.CountFacets, out, time.time() - t), flush=True)
print("DONE")

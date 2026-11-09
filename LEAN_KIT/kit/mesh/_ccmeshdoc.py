import os, time
import FreeCAD as App
import Mesh

t0 = time.time()
doc = App.newDocument("meshes")
import json
if os.environ.get("CC_MESHES_JSON"):
    _specs = [(d["name"], d.get("label", d["name"]), d["path"]) for d in json.load(open(os.environ["CC_MESHES_JSON"], encoding="utf-8"))]
else:
    _specs = [tuple(s.split("|")) for s in os.environ["CC_MESHES"].split(";") if s.strip()]
for name, label, path in _specs:
    m = Mesh.Mesh(path)
    o = doc.addObject("Mesh::Feature", name)
    o.Mesh = m
    o.Label = label
    print("added %-18s %8d facets  %s" % (name, m.CountFacets, label), flush=True)
doc.recompute()
doc.saveAs(os.environ["CC_OUT"])
print("wrote %s (%.1f MB) in %.0f s" % (os.environ["CC_OUT"], os.path.getsize(os.environ["CC_OUT"]) / 1e6, time.time() - t0))
print("DONE")

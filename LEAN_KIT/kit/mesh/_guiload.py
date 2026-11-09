# CC_OUTDIR
import os, json, traceback
import FreeCAD as App
import FreeCADGui as Gui

out = os.environ["CC_OUTDIR"]; os.makedirs(out, exist_ok=True)
rep = {"file": os.environ["CC_FCSTD"], "objects": {}, "errors": []}
try:
    doc = App.openDocument(os.environ["CC_FCSTD"])
    Gui.activateWorkbench("MeshWorkbench") if hasattr(Gui, "activateWorkbench") else None
    gdoc = Gui.getDocument(doc.Name)
    for o in doc.Objects:
        vo = gdoc.getObject(o.Name)
        e = {"type": o.TypeId, "label": o.Label, "visible": bool(vo.Visibility) if vo else None}
        for p in ("ShapeColor", "DiffuseColor"):
            if vo is not None and hasattr(vo, p):
                try: e[p] = [round(float(c), 3) for c in (getattr(vo, p)[0] if p == "DiffuseColor" and getattr(vo, p) else getattr(vo, p))][:3]
                except Exception as ex: e[p] = str(ex)
        if vo is not None and hasattr(vo, "ShapeAppearance"):
            try: e["appearance_diffuse"] = [round(float(c), 3) for c in vo.ShapeAppearance[0].DiffuseColor][:3]
            except Exception as ex: e["appearance_diffuse"] = str(ex)
        if o.TypeId == "Mesh::Feature":
            e["facets"] = o.Mesh.CountFacets
        rep["objects"][o.Name] = e
    v = gdoc.activeView()
    v.viewIsometric(); v.fitAll()
    v.saveImage(os.path.join(out, "gui_at_open.png"), 1400, 1000, "Current")
    v.viewBottom(); v.fitAll()
    v.saveImage(os.path.join(out, "gui_at_open_below.png"), 1400, 1000, "Current")
    for o in doc.Objects:
        vo = gdoc.getObject(o.Name)
        if vo is not None: vo.Visibility = (o.TypeId != "Mesh::Feature")
    v.viewIsometric(); v.fitAll()
    v.saveImage(os.path.join(out, "gui_region_map.png"), 1400, 1000, "Current")
except Exception:
    rep["errors"].append(traceback.format_exc())
json.dump(rep, open(os.path.join(out, "gui_load.json"), "w"), indent=1)
os._exit(0)

# KIT INSTRUMENT `diag_plancut` - a plan cut (constant z) through the body with feature stations drawn across it.
# Run: kit tool diag_plancut --job <JOB> --set KEY=VALUE ...   (output lands in that job's folder)
# Inputs: CC_BODY  CC_Z "z z ..."  CC_WIN "x0 x1 y0 y1"  CC_STATIONS "label=y ..."  [CC_LUMPS]  CC_OUTDIR
import os, sys, json
import numpy as np
sys.path.insert(0, os.environ["KIT_HOME"])
import vtk
from vtk.util import numpy_support as ns
from PIL import Image, ImageDraw

os.makedirs(os.environ["CC_OUTDIR"], exist_ok=True)
_ow = vtk.vtkFileOutputWindow(); _ow.SetFileName(os.path.join(os.environ["CC_OUTDIR"], "vtk_plan.log"))
vtk.vtkOutputWindow.SetInstance(_ow); vtk.vtkObject.GlobalWarningDisplayOff()
r = vtk.vtkSTLReader(); r.SetFileName(os.environ["CC_BODY"]); r.Update(); BODY = r.GetOutput()
X0, X1, Y0, Y1 = [float(t) for t in os.environ["CC_WIN"].split()]
W = 1000
S = W / (X1 - X0)
H = int((Y1 - Y0) * S)
ST = [(t.split("=")[0], float(t.split("=")[1])) for t in os.environ.get("CC_STATIONS", "").split()]


def px(x, y):
    return (x - X0) * S, (Y1 - y) * S + 44


for z in [float(t) for t in os.environ["CC_Z"].split()]:
    pl = vtk.vtkPlane(); pl.SetOrigin(0, 0, z); pl.SetNormal(0, 0, 1)
    c = vtk.vtkCutter(); c.SetInputData(BODY); c.SetCutFunction(pl); c.Update()
    o = c.GetOutput()
    im = Image.new("RGB", (W, H + 44), (12, 12, 16)); dr = ImageDraw.Draw(im)
    for g in range(int(np.ceil(X0)), int(X1) + 1):
        if g % 5 == 0:
            a, _ = px(g, 0); dr.line([a, 44, a, H + 44], fill=(34, 34, 44) if g % 10 else (58, 58, 72))
    for g in range(int(np.ceil(Y0)), int(Y1) + 1):
        if g % 5 == 0:
            _, b = px(0, g); dr.line([0, b, W, b], fill=(34, 34, 44) if g % 10 else (58, 58, 72))
    if o.GetNumberOfPoints():
        P = ns.vtk_to_numpy(o.GetPoints().GetData())
        L = ns.vtk_to_numpy(o.GetLines().GetData()).reshape(-1, 3)[:, 1:]
        for a, b in L:
            pa, pb = px(*P[a][:2]), px(*P[b][:2])
            dr.line([pa, pb], fill=(230, 230, 240), width=2)
    for nm, y in ST:
        _, b = px(0, y); dr.line([0, b, W, b], fill=(255, 200, 0), width=1)
        dr.text((6, b - 14), nm, fill=(255, 200, 0))
    dr.rectangle([0, 0, W, 42], fill=(0, 0, 0))
    dr.text((6, 4), "PLAN CUT through the body at the height of the lumps.  WHITE = body outline.  "
                    "YELLOW = each vane's measured position.", fill=(255, 255, 90))
    dr.text((6, 22), "Grid 5 mm (brighter every 10 mm).  The rear of the part is at the top of the page.",
            fill=(200, 200, 200))
    p = os.path.join(os.environ["CC_OUTDIR"], "T4_plan_z%d.png" % int(round(z * 10)))
    im.save(p); print(p, flush=True)
print("DONE", flush=True)

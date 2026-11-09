# KIT INSTRUMENT `diag_section` - a true cross-section of body AND patch in one plane at one scale - a membrane over air vs a proud fill.
# Run: kit tool diag_section --job <JOB> --set KEY=VALUE ...   (output lands in that job's folder)
# Inputs: CC_BODY CC_PATCH  CC_Y (planes of constant y)  CC_WIN "x0 x1 z0 z1"  CC_OUTDIR  [CC_MARK "x z"]
import os, sys
import numpy as np
sys.path.insert(0, os.environ["KIT_HOME"])
import vtk
from vtk.util import numpy_support as ns
from PIL import Image, ImageDraw

os.makedirs(os.environ["CC_OUTDIR"], exist_ok=True)      # CC_OUTDIR  does not exist
_ow = vtk.vtkFileOutputWindow(); _ow.SetFileName(os.path.join(os.environ["CC_OUTDIR"], "vtk_sec.log"))
vtk.vtkOutputWindow.SetInstance(_ow); vtk.vtkObject.GlobalWarningDisplayOff()


def read(p):
    """an STL as it was; a .brep (31bm - the agent's b12: the tool drew four empty frames of a .brep and said nothing) tessellated here into a mesh beside
    the pictures (MeshPart 0.05 mm / 0.1 rad, the kit's look tessellation) and cut as the STL would be; anything else, or an empty mesh, refused"""
    if p.lower().endswith(".brep"):
        import Part, MeshPart
        sh = Part.Shape(); sh.importBrep(p)
        m = MeshPart.meshFromShape(Shape=sh, LinearDeflection=0.05, AngularDeflection=0.1)
        q = os.path.join(os.environ["CC_OUTDIR"], "_section_%s.stl" % os.path.splitext(os.path.basename(p))[0]); m.write(q)
        print("diag_section: %s is a B-rep - tessellated to %s (%d facets) and sectioned as a mesh" % (os.path.basename(p), os.path.basename(q), m.CountFacets), flush=True); p = q
    elif not p.lower().endswith(".stl"):
        sys.exit("diag_section: %s is neither .stl nor .brep - nothing to section" % p)
    r = vtk.vtkSTLReader(); r.SetFileName(p); r.Update(); o = r.GetOutput()
    if o.GetNumberOfPoints() == 0: sys.exit("diag_section: %s read as an EMPTY mesh - nothing to section" % p)
    return o


def cut(pd, y):
    pl = vtk.vtkPlane(); pl.SetOrigin(0, y, 0); pl.SetNormal(0, 1, 0)
    c = vtk.vtkCutter(); c.SetInputData(pd); c.SetCutFunction(pl); c.Update()
    o = c.GetOutput()
    if o.GetNumberOfPoints() == 0:
        return []
    P = ns.vtk_to_numpy(o.GetPoints().GetData())
    L = ns.vtk_to_numpy(o.GetLines().GetData()).reshape(-1, 3)[:, 1:]
    return [(P[a], P[b]) for a, b in L]


BODY, PATCH = read(os.environ["CC_BODY"]), read(os.environ["CC_PATCH"])
X0, X1, Z0, Z1 = [float(t) for t in os.environ["CC_WIN"].split()]
W = 1000
S = W / (X1 - X0)
H = int((Z1 - Z0) * S)
mark = [float(t) for t in os.environ.get("CC_MARK", "").split()] if os.environ.get("CC_MARK") else None


def px(p):
    return ((p[0] - X0) * S, (Z1 - p[2]) * S)


for y in [float(t) for t in os.environ["CC_Y"].split()]:
    im = Image.new("RGB", (W, H + 40), (12, 12, 16)); dr = ImageDraw.Draw(im)
    for g in range(int(np.ceil(X0)), int(X1) + 1):
        if g % 2 == 0:
            gx = (g - X0) * S; dr.line([gx, 40, gx, H + 40], fill=(32, 32, 40) if g % 10 else (60, 60, 75))
    for g in range(int(np.ceil(Z0)), int(Z1) + 1):
        if g % 2 == 0:
            gz = (Z1 - g) * S + 40; dr.line([0, gz, W, gz], fill=(32, 32, 40) if g % 10 else (60, 60, 75))
    for a, b in cut(BODY, y):
        pa, pb = px(a), px(b); dr.line([pa[0], pa[1] + 40, pb[0], pb[1] + 40], fill=(225, 225, 235), width=3)
    for a, b in cut(PATCH, y):
        pa, pb = px(a), px(b); dr.line([pa[0], pa[1] + 40, pb[0], pb[1] + 40], fill=(60, 140, 255), width=2)
    if mark:
        mx, mz = px([mark[0], 0, mark[1]]); dr.ellipse([mx - 14, mz + 40 - 14, mx + 14, mz + 40 + 14],
                                                       outline=(255, 40, 40), width=3)
    dr.rectangle([0, 0, W, 38], fill=(0, 0, 0))
    dr.text((6, 4), "SECTION at y %.1f.  WHITE = %s (CC_BODY).  BLUE = %s (CC_PATCH)." % (y, os.path.basename(os.environ["CC_BODY"]), os.path.basename(os.environ["CC_PATCH"])),
            fill=(255, 255, 90))
    dr.text((6, 20), "grid 2 mm (bright every 10 mm).  Red ring = where the unmatched loop crosses this plane.",
            fill=(200, 200, 200))
    p = os.path.join(os.environ["CC_OUTDIR"], "T2_section_%d.png" % int(round(abs(y) * 10)))
    im.save(p); print(p, flush=True)
print("DONE", flush=True)

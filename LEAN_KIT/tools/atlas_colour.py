# KIT INSTRUMENT `atlas_colour` - build the COLOURED REVIEW MODEL of a region map: one object per region, each a
# flat colour, labelled [DEFINITION|EDIT], plus the legend and the facemap that turns the client's picks back into
# body faces.
# Run: kit tool atlas_colour --job <JOB> --set ATLAS_MANIFEST=<manifest.json> --set ATLAS_TEMPLATE=<any GUI-saved
#      FCStd with a Part object> --set ATLAS_OUT=<Deliverables\<REV>\model\<name>.FCStd> [--set ATLAS_REGIONS=...]
# Inputs: ATLAS_MANIFEST (atlas_split's or atlas_features' manifest.json)  ATLAS_REGIONS (their regions.json, for
#         the statuses; optional)  ATLAS_TEMPLATE  ATLAS_OUT  ATLAS_TITLE (optional)
# The colour layout is the one that displays in FreeCAD 1.1: ONE object per region, a count=1
# ShapeAppearance payload plus a ShapeColor, the ViewProvider block taken from a GUI-saved file (a headless save
# writes no GuiDocument.xml at all - HOW_TO_DELIVER_A_COLOURED_MODEL.md). Check the result with `kit deliverycheck`.
#
# THE CLIENT'S CORRECTION CHANNEL. The client clicks a face in the map and pastes FreeCAD's selection line; `FaceN` there
# is LOCAL to the region's object. The facemap written beside the model is what `kit atlas faces --facemap`
# reads to turn that pick back into a body face.
import os, sys, re, json, uuid, struct, zipfile, shutil, tempfile, colorsys
sys.path.insert(0, os.environ["KIT_HOME"])
import FreeCAD as App
import Part


def say(*a):
    print(*a, flush=True)


MAN = json.load(open(os.environ["ATLAS_MANIFEST"], encoding="utf-8"))
ST = json.load(open(os.environ["ATLAS_REGIONS"], encoding="utf-8")) if os.environ.get("ATLAS_REGIONS") else {}
OUT = os.environ["ATLAS_OUT"]
TITLE = os.environ.get("ATLAS_TITLE") or os.path.splitext(os.path.basename(OUT))[0]
stem = os.path.splitext(OUT)[0]


def tags(nm):
    r = ST.get(nm, {})
    return r.get("definition", "-"), r.get("edit", "-")


cols = {nm: tuple(int(v) for v in spec.get("rgb", [205, 205, 210])) for nm, spec in MAN.items()}
_close = []
_nm = list(cols)
for i in range(len(_nm)):
    for j in range(i + 1, len(_nm)):
        a, b = cols[_nm[i]], cols[_nm[j]]
        if sum((a[k] - b[k]) ** 2 for k in range(3)) ** 0.5 < 30:
            _close.append((_nm[i], _nm[j]))
if _close:
    say("WARNING: %d pair(s) of regions have colours that are hard to tell apart: %s"
        % (len(_close), "; ".join("%s/%s" % p for p in _close[:10])))

doc = App.newDocument(re.sub(r"[^A-Za-z0-9_]", "_", TITLE)[:40] or "ATLAS_MAP")
made = []
for nm, spec in MAN.items():
    sh = Part.Shape(); sh.importBrep(spec["brep"])
    o = doc.addObject("Part::Feature", re.sub(r"[^A-Za-z0-9_]", "_", nm))
    o.Shape = sh
    _d, _e = tags(nm)
    o.Label = "[%s|%s] %s  (%d faces, %.0f mm2)" % (_d, _e, nm, spec["pieces"], spec["area"])
    made.append((o.Name, nm, cols[nm], spec))
tmp = tempfile.mkdtemp()
nogui = os.path.join(tmp, "nogui.FCStd")
doc.recompute(); doc.saveAs(nogui)


def pack(r, g, b, a=255):
    return ((r << 24) | (g << 16) | (b << 8) | a) & 0xFFFFFFFF


def one_material(r, g, b):
    buf = bytearray(struct.pack("<I", 1))
    buf += struct.pack("<I", pack(0x55, 0x55, 0x55)) + struct.pack("<I", pack(r, g, b))
    buf += struct.pack("<I", pack(0x88, 0x88, 0x88)) + struct.pack("<I", pack(0x00, 0x00, 0x00))
    buf += struct.pack("<f", 0.9) + struct.pack("<f", 0.0) + struct.pack("<II", 0, 0)
    u = str(uuid.uuid4()).encode("ascii")
    return bytes(buf + struct.pack("<I", len(u)) + u)


tz = zipfile.ZipFile(os.environ["ATLAS_TEMPLATE"])
g = tz.read("GuiDocument.xml").decode("utf-8", "replace")
head = g[:g.index("<ViewProviderData")]
blk0 = None
for m in re.finditer(r'<ViewProvider name="([^"]+)".*?</ViewProvider>\s*', g, re.S):
    if "ShapeAppearance" in m.group(0) and "MaterialList" in m.group(0):
        blk0, tname = m.group(0), m.group(1)
        break
if blk0 is None:
    say("REFUSED: the template has no Part object's view provider with a ShapeAppearance - save any Part object"
        " from the FreeCAD GUI and pass that file"); raise SystemExit(2)
blk0 = re.sub(r'<Property name="LineColorArray".*?</Property>\s*', '', blk0, flags=re.S)
blk0 = re.sub(r'<Property name="PointColorArray".*?</Property>\s*', '', blk0, flags=re.S)
blocks, payloads = [], {}
for objname, nm, col, spec in made:
    b = blk0.replace('name="%s"' % tname, 'name="%s"' % objname)
    b = re.sub(r'<MaterialList file="[^"]+"', '<MaterialList file="mat_%s"' % objname, b)
    b = re.sub(r'<Property name="ShapeColor".*?</Property>\s*', '', b, flags=re.S)
    scp = ('<Property name="ShapeColor" type="App::PropertyColor" status="1">'
           '<PropertyColor value="%d"/></Property>' % pack(col[0], col[1], col[2]))
    b = b.replace('<Property name="AngularDeflection"', scp + '<Property name="AngularDeflection"', 1)
    b = re.sub(r'(<Property name="Visibility"[^>]*>\s*<Bool value=")\w+', r'\g<1>true', b)
    b = re.sub(r'<Properties Count="\d+"', '<Properties Count="%d"' % len(re.findall(r'<Property name=', b)), b)
    blocks.append(b)
    payloads["mat_%s" % objname] = one_material(*col)
gui = head + '<ViewProviderData Count="%d">\n' % len(blocks) + "".join(blocks) + \
      '</ViewProviderData>\n  <Camera settings=""/>\n</Document>\n'
with zipfile.ZipFile(nogui) as zi, zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zo:
    for e in [x for x in zi.namelist() if x != "GuiDocument.xml"]:
        zo.writestr(zi.getinfo(e), zi.read(e))
    for k, v in payloads.items():
        zo.writestr(k, v)
    zo.writestr("GuiDocument.xml", gui)
shutil.rmtree(tmp, ignore_errors=True)
say("wrote %s (%.1f MB), %d region object(s)" % (OUT, os.path.getsize(OUT) / 1e6, len(made)))

fmap = {nm: {str(i + 1): int(fid) for i, fid in enumerate(spec["from_faces"])} for _o, nm, _c, spec in made}
json.dump(fmap, open(stem + "_facemap.json", "w", encoding="utf-8"), indent=1)
ml = ["# %s - what FreeCAD calls a face, and which body face it came from" % TITLE, "",
      "Click a face and paste FreeCAD's selection line. `FaceN` is LOCAL to the object; the table below (and",
      "`%s_facemap.json`, which `kit atlas faces --facemap` reads) turns it into a body face." % os.path.basename(stem),
      "A face that crossed a region boundary was CUT on it, so one body face can appear in two objects.", ""]
for objname, nm, col, spec in made:
    ids = spec["from_faces"]
    ml += ["## %s  (%d faces, rgb%s)" % (nm, len(ids), col), "", "_%s_" % spec.get("note", ""), "", "```"]
    for a0 in range(0, len(ids), 10):
        ml.append("  " + "  ".join("F%-4d=%-5d" % (a0 + k + 1, ids[a0 + k]) for k in range(min(10, len(ids) - a0))))
    ml += ["```", ""]
open(stem + "_facemap.md", "w", encoding="utf-8").write("\n".join(ml) + "\n")
lg = ["# %s - the legend" % TITLE, "", "One object per region, each a flat colour, labelled `[DEFINITION|EDIT]`.", "",
      "| colour | object | definition | edit | faces | area mm2 | what it is |", "|---|---|---|---|---|---|---|"]
for objname, nm, col, spec in made:
    _d, _e = tags(nm)
    lg.append("| rgb(%d,%d,%d) | %s | %s | %s | %d | %.0f | %s |" % (col[0], col[1], col[2], nm, _d, _e, spec["pieces"],
                                                                   spec["area"], spec.get("note", "")))
open(stem + "_legend.md", "w", encoding="utf-8").write("\n".join(lg) + "\n")
say("wrote %s_legend.md, %s_facemap.md and .json" % (stem, stem))
say("DONE - check it with `kit deliverycheck`, then open it in the FreeCAD GUI: only a GUI shows the colour")

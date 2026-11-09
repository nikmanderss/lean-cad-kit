"""kit_deliver.py - `kit deliver`: THE DELIVERY RECIPE, one command (2026-09-24; the mesh half ported 2026-09-24 late).

the client, 2026-09-24: "Model deliveries should have a recipe that includes the atlas, extraneous components,
reference objects, marker blocks and the model being edited. All intelligently organized and edited with
default views setup that speed up my review (hiding the right thing, camera angle etc.)."

the client, 2026-09-24, on the first R32 print delivery (three meshes and the atlas objects loose at the top level):
"the freecad delivery is not at all right. The entire colored atlas should be in an unexpanded, hidden part.
Look at other models." And on the second (the atlas grouped, still no assembly, reference or markers):
"Freecad delivery is still not right. Look at R26 delivery structure and update that with the 4 models you
have in R32 currently." THE STRUCTURE IS THE PREVIOUS DELIVERY'S, ALWAYS: G1_PRINT (shown, expanded),
G2_ASSEMBLY (coloured, hidden), G3_REFERENCE (hidden), G4_MARKERS (hidden) - and every new thing goes INTO a
group: the model being reviewed into G1_PRINT, the atlas into one hidden collapsed group, source meshes into
one hidden collapsed group. Nothing loose at the top level.

31br B2 / B5 (2026-10-30, a fixture project - the client: "The agent also needs instructions on how to add new bodys to the document" / "better mapping to the agent for how to place
and rotate parts"): --add-body appends Part::Feature bodies (the brep its own payload, the GUI's object block, a 4-property view provider - ShapeColor paints it), each into a
group; a placement (`place=` on a body or a mesh spec) is written the way FreeCAD READS it back (kit_place.py: the brep's location for a body, the XML Placement for a mesh);
a --target swap carries the template body's own Placement into the swapped brep (it had been reset to identity - probe P2). The atlas map is NOT a body carrier.

What it builds, by ZIP SURGERY and never by opening the document (`freecadcmd` has no GUI half and writes
no GuiDocument.xml - every colour and visibility flag would be lost; HOW_TO_DELIVER_A_COLOURED_MODEL.md):

  <REV>_<name>.FCStd  =  the TEMPLATE (the previous delivery: a GUI-saved FCStd holding the groups, the
                         assembly parts, reference objects and marker blocks with their colours)
                       + B-REP delivery (--target): the MODEL OF RECORD swapped into the template's body object
                       + MESH delivery (--mesh): Mesh::Feature objects (the print file, its sources) lifted from
                         a throw-away headless document, each placed in the group its spec names
                       + the ATLAS MAP's region objects, copied from the coloured map, inside ONE hidden and
                         collapsed group (--atlas-group; refused while the map is behind the bank)
                       + visibility set per group, ShapeColor stated on every coloured part
                       + a default camera (iso | top | front | ... , framed on the body)
  then `kit deliverycheck` on the result, in the same call.

The project scripts it replaced (the brep swap of 2026-09-16, the map and mesh objects of 2026-09-23) are its
prior art; every gate they carried is here: the file table (orphan/missing) empty, every Properties Count true, both XML files parse,
visibility agreeing in both files, Objects/ObjectData/ViewProviderData counts equal to the blocks present,
every group link and dependency naming an object that exists, and payloads written AFTER the XML that
references them (K-ZIPORDER: FreeCAD reads the zip as one stream).
"""
import os, re, sys, json, time, zipfile, struct
import xml.etree.ElementTree as ET
import kit_place as _KP

SHOW_DEFAULT_PREFIX = ("G1_", "COVER", "Cover")
HIDE_DEFAULT_PREFIX = ("G2_", "G3_", "G4_", "P_", "MARKER", "SCAN", "DATUM", "REF_")
# thumbnail
# thumbnails/Thumbnail.png
# thumbnail
# Thumbnail  thumbnail
# thumbnail
FC_OWN_ENTRIES = ("thumbnails/Thumbnail.png",)

CAMERAS = {
    "iso":    "0.742906 0.307722 0.594473  1.21713",
    "top":    "0 0 1  0",
    "front":  "1 0 0  1.5707964",
    "right":  "0.57735 0.57735 0.57735  2.0943952",
    "left":   "-0.57735 0.57735 0.57735  4.1887903",
    "rear":   "0 0.70710677 0.70710677  3.1415927",
    "bottom": "1 0 0  3.1415927",
}


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _block(xml, tag, name, start=0):
    """(i, j) of `<tag name="name" ...> ... </tag>` in xml from `start`, or None."""
    i = xml.find('<%s name="%s"' % (tag, name), start)
    if i == -1:
        return None
    j = xml.find("</%s>" % tag, i)
    if j == -1:
        return None
    return i, j + len("</%s>" % tag)


def _setvis(xml, tag, name, val):
    b = _block(xml, tag, name)
    if not b:
        return xml, False
    seg = xml[b[0]:b[1]]
    m = re.search(r'(<Property name="Visibility"[^>]*>\s*<Bool value=")(\w+)(")', seg)
    if not m:
        return xml, False
    seg = seg[:m.start(2)] + ("true" if val else "false") + seg[m.end(2):]
    return xml[:b[0]] + seg + xml[b[1]:], True


def _setvis_text(seg, val):
    """the Visibility flag inside one block of text"""
    return re.sub(r'(<Property name="Visibility"[^>]*>\s*<Bool value=")(\w+)(")',
                  lambda m: m.group(1) + ("true" if val else "false") + m.group(3), seg, count=1)


def _count(xml, pat):
    m = re.search(pat, xml)
    return int(m.group(1)) if m else None


def _set_count(xml, pat, n):
    m = re.search(pat, xml)
    return xml[:m.start(1)] + str(n) + xml[m.end(1):] if m else xml


def _diffuse(raw):
    """(r, g, b) of material 0's diffuse slot in a ShapeAppearance payload - bytes [a, b, g, r]."""
    d = raw[8:12]
    return d[3], d[2], d[1]


def _camera_xml(kind, bbox):
    """an OrthographicCamera framed on the body's box, looking from `kind`."""
    (x0, y0, z0), (x1, y1, z1) = bbox
    cx, cy, cz = (x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0
    ext = max(x1 - x0, y1 - y0, z1 - z0) * 1.15
    dirs = {"iso": (1, -1, 1), "top": (0, 0, 1), "front": (0, -1, 0), "right": (1, 0, 0), "left": (-1, 0, 0),
            "rear": (0, 1, 0), "bottom": (0, 0, -1)}
    d = dirs.get(kind, dirs["iso"])
    nrm = (d[0] ** 2 + d[1] ** 2 + d[2] ** 2) ** 0.5
    dist = ext * 2.5
    pos = (cx + d[0] / nrm * dist, cy + d[1] / nrm * dist, cz + d[2] / nrm * dist)
    s = ("  OrthographicCamera {\n    viewportMapping ADJUST_CAMERA\n    position %.3f %.3f %.3f\n"
         "    orientation %s\n    nearDistance %.3f\n    farDistance %.3f\n    aspectRatio 1\n"
         "    focalDistance %.3f\n    height %.3f\n\n  }\n" % (pos[0], pos[1], pos[2], CAMERAS.get(kind, CAMERAS["iso"]),
                                                           dist - ext, dist + ext, dist, ext))
    return '<Camera settings="%s"/>' % s.replace("\n", "&#10;").replace('"', "&quot;")


# collapsed
def _group_obj_xml(name, label, members):
    links = "".join('                        <Link value="%s"/>\n' % m for m in members)
    return ('<Object name="%s" Extensions="True">\n'
            '            <Extensions Count="1">\n'
            '                <Extension type="App::GroupExtension" name="GroupExtension">\n'
            '                </Extension>\n'
            '            </Extensions>\n'
            '            <Properties Count="5" TransientCount="1">\n'
            '                <_Property name="_GroupTouched" type="App::PropertyBool" status="100663424"/>\n'
            '                <Property name="ExpressionEngine" type="App::PropertyExpressionEngine" status="67108864">\n'
            '                    <ExpressionEngine count="0">\n'
            '                    </ExpressionEngine>\n'
            '                </Property>\n'
            '                <Property name="Group" type="App::PropertyLinkList">\n'
            '                    <LinkList count="%d">\n%s'
            '                    </LinkList>\n'
            '                </Property>\n'
            '                <Property name="Label" type="App::PropertyString" status="134217728">\n'
            '                    <String value="%s"/>\n'
            '                </Property>\n'
            '                <Property name="Label2" type="App::PropertyString" status="67108992">\n'
            '                    <String value=""/>\n'
            '                </Property>\n'
            '                <Property name="Visibility" type="App::PropertyBool" status="648">\n'
            '                    <Bool value="false"/>\n'
            '                </Property>\n'
            '            </Properties>\n'
            '        </Object>') % (name, len(members), links, _esc(label))


def _group_vp_xml(name, rank):
    return ('<ViewProvider name="%s" expanded="0" treeRank="%d" Extensions="True">\n'
            '            <Extensions Count="1">\n'
            '                <Extension type="Gui::ViewProviderGroupExtension" name="ViewProviderGroupExtension">\n'
            '                </Extension>\n'
            '            </Extensions>\n'
            '            <Properties Count="5" TransientCount="0">\n'
            '                <Property name="DisplayMode" type="App::PropertyEnumeration" status="1">\n'
            '                    <Integer value="0"/>\n'
            '                </Property>\n'
            '                <Property name="OnTopWhenSelected" type="App::PropertyEnumeration" status="1">\n'
            '                    <Integer value="0"/>\n'
            '                </Property>\n'
            '                <Property name="SelectionStyle" type="App::PropertyEnumeration" status="1">\n'
            '                    <Integer value="0"/>\n'
            '                </Property>\n'
            '                <Property name="ShowInTree" type="App::PropertyBool" status="1">\n'
            '                    <Bool value="true"/>\n'
            '                </Property>\n'
            '                <Property name="Visibility" type="App::PropertyBool" status="1">\n'
            '                    <Bool value="false"/>\n'
            '                </Property>\n'
            '            </Properties>\n'
            '        </ViewProvider>') % (name, rank)


def _add_member(doc, gname, member):
    """`member` appended to the template group `gname`: its Group link list AND its dependency row."""
    b = _block(doc, "Object", gname, doc.find("<ObjectData"))
    if not b:
        raise RuntimeError("%s is not an object of the template - a group a spec names must be a template group or a --group" % gname)
    blk = doc[b[0]:b[1]]
    m = re.search(r'<Property name="Group" type="App::PropertyLinkList"[^>]*>\s*<LinkList count="(\d+)"\s*(/>|>.*?</LinkList>)', blk, re.S)
    if not m:
        raise RuntimeError("%s is not a group (no Group link list)" % gname)
    n = int(m.group(1)) + 1
    if m.group(2) == "/>":
        new = ('<Property name="Group" type="App::PropertyLinkList">\n                    <LinkList count="%d">\n'
               '                        <Link value="%s"/>\n                    </LinkList>' % (n, member))
    else:
        new = re.sub(r'<LinkList count="\d+"', '<LinkList count="%d"' % n, m.group(0), count=1)
        new = new.replace("</LinkList>", '    <Link value="%s"/>\n                    </LinkList>' % member)
    blk = blk[:m.start()] + new + blk[m.end():]
    doc = doc[:b[0]] + blk + doc[b[1]:]
    md = re.search(r'<ObjectDeps Name="%s" Count="(\d+)"\s*(/>|>.*?</ObjectDeps>)' % re.escape(gname), doc, re.S)
    if md:
        cnt = int(md.group(1)) + 1
        body = "" if md.group(2) == "/>" else md.group(2)[1:].replace("</ObjectDeps>", "").rstrip()
        newd = '<ObjectDeps Name="%s" Count="%d">%s\n            <Dep Name="%s"/>\n        </ObjectDeps>' % (gname, cnt, body, member)
        doc = doc[:md.start()] + newd + doc[md.end():]
    return doc


def _mesh_vp_template(path, zin_template, tdoc, tgui):
    """(view-provider block, its zip, its object name) of a GUI-saved Mesh::Feature that carries a MaterialList - the
    pattern every delivered mesh's view provider is cut from. `path` names a file to take it from; otherwise the
    template's own meshes (a reference scan, say) serve."""
    if path:
        z = zipfile.ZipFile(path, "r")
        if "GuiDocument.xml" not in z.namelist():
            raise RuntimeError("--vptemplate %s has no GuiDocument.xml (saved headless) - it carries no view providers" % path)
        d = z.read("Document.xml").decode("utf-8"); g = z.read("GuiDocument.xml").decode("utf-8")
    else:
        z, d, g = zin_template, tdoc, tgui
    for nm in re.findall(r'<Object type="Mesh::Feature" name="([^"]+)"', d):
        b = _block(g, "ViewProvider", nm)
        if b and "<MaterialList" in g[b[0]:b[1]]:
            return g[b[0]:b[1]], z, nm
    raise RuntimeError("no Mesh::Feature view provider with a MaterialList in %s - give --vptemplate <a GUI-saved FCStd "
                       "holding one coloured mesh>" % (path or "the template"))


def build(template, shape, out, target, label="", drop=(), show=(), hide=(), atlas_map=None, atlas_regions=None,
          camera="iso", bbox=None, say=print, meshes=(), meshdoc=None, vptemplate=None, atlas_group=None, groups=(), bodies=(), target_place_xml=None, placeholder_label=""):
    """Build the delivery FCStd. Raises RuntimeError with the gate that refused.

    meshes: [{"name", "vis", "rgb", "group"}] lifted from `meshdoc` (a headless document holding exactly those
    Mesh::Feature objects, `_ccmeshdoc.py`); each goes into `group` - a template group or one of `groups`.
    atlas_group: (name, label) - the map's region objects inside this one hidden, collapsed group; None = loose.
    groups: [(name, label)] new hidden, collapsed groups (for the source meshes).
    bodies: [{"name", "label", "path" (a .brep - already PLACED when the spec carried place=), "vis", "rgb", "group", "place_xml", "place_desc"}] - 31br B2: a
    Part::Feature each, appended; target_place_xml: the swapped body's <PropertyPlacement .../> (31br B5: the carry, or identity under --drop-placement)."""
    zin = zipfile.ZipFile(template, "r")
    names = zin.namelist()
    if "GuiDocument.xml" not in names:
        raise RuntimeError("the template %s has no GuiDocument.xml - it was saved headless and carries no colours; "
                           "use a GUI-saved file as the template" % template)
    doc0 = zin.read("Document.xml").decode("utf-8")
    gui0 = zin.read("GuiDocument.xml").decode("utf-8")
    doc, gui = doc0, gui0
    meshes = list(meshes or ())
    groups = list(groups or ())
    bodies = list(bodies or ())
    if not target and not meshes and not bodies:
        raise RuntimeError("nothing to deliver: --target (the B-rep swap), --add-body (Part::Feature bodies) or --mesh (Mesh::Feature objects)")
    has_deps = 'Dependencies="1"' in re.search(r"<Objects [^>]*>", doc).group(0)
    next_id = max(int(x) for x in re.findall(r' id="(\d+)"', doc)) + 1
    payload = {}
    added = []
    new_objs = []
    vis_new = {}

    brp = None
    if target:
        b = _block(doc, "Object", target, doc.find("<ObjectData"))
        if not b:
            raise RuntimeError("%s is not an object of the template (Document.xml). --target names the body object." % target)
        blk = doc[b[0]:b[1]]
        # HasherIndex
        m = re.search(r'<Part\b[^>]*?\bfile="([^"]+)"[^>]*/>', blk)
        if not m:
            raise RuntimeError("%s carries no Part shape file - it is not a Part::Feature" % target)
        brp = m.group(1)
        newblk = blk[:m.start()] + '<Part file="%s"/>' % brp + blk[m.end():]
        if not label and placeholder_label:      # takes the body's own name
            _curl = re.search(r'<Property name="Label" type="App::PropertyString"[^>]*>\s*<String value="([^"]*)"', newblk)
            if _curl and _curl.group(1).startswith("PLACEHOLDER_BODY"):
                label = placeholder_label; say("label  : the template's PLACEHOLDER_BODY takes the body's own name, %s (--label names another)" % label)
        if label:
            newblk = re.sub(r'(<Property name="Label" type="App::PropertyString"[^>]*>\s*<String value=")[^"]*(")',
                            lambda mm: mm.group(1) + _esc(label) + mm.group(2), newblk, count=1)
        if target_place_xml:
            newblk = re.sub(r'<PropertyPlacement [^/]*/>', target_place_xml, newblk, count=1)
        doc = doc[:b[0]] + newblk + doc[b[1]:]
        say("body   : %s -> %s (%.1f MB)%s" % (target, brp, os.path.getsize(shape) / 1e6, ("  label " + label) if label else ""))

    dropped_files = set()
    for nm in drop:
        k = _block(doc, "Object", nm, doc.find("<ObjectData"))
        if k:
            for mm in re.finditer(r'file="([^"]+)"', doc[k[0]:k[1]]):
                dropped_files.add(mm.group(1))
            doc = doc[:k[0]] + doc[k[1]:]
            doc = re.sub(r'\s*<Object type="[^"]+" name="%s" id="\d+"\s*/>' % re.escape(nm), "", doc)
            doc = re.sub(r'\s*<ObjectDeps Name="%s" Count="\d+"\s*(/>|>.*?</ObjectDeps>)' % re.escape(nm), "", doc, flags=re.S)
            doc = re.sub(r'\s*<Dep Name="%s"\s*/>' % re.escape(nm), "", doc)
            doc = re.sub(r'\s*<Link value="%s"\s*/>' % re.escape(nm), "", doc)
        g = _block(gui, "ViewProvider", nm)
        if g:
            for mm in re.finditer(r'file="([^"]+)"', gui[g[0]:g[1]]):
                dropped_files.add(mm.group(1))
            gui = gui[:g[0]] + gui[g[1]:]
            gui = re.sub(r'\s*<Expand name="%s"\s*/>' % re.escape(nm), "", gui)
        say("dropped: %s%s" % (nm, "" if (k or g) else "  (not in the template)"))
    doc = re.sub(r'<LinkList count="\d+">(.*?)</LinkList>',
                 lambda m: '<LinkList count="%d">%s</LinkList>' % (len(re.findall(r"<Link value=", m.group(1))), m.group(1)), doc, flags=re.S)
    doc = re.sub(r'<ObjectDeps Name="([^"]+)" Count="\d+">(.*?)</ObjectDeps>',
                 lambda m: '<ObjectDeps Name="%s" Count="%d">%s</ObjectDeps>' % (m.group(1), len(re.findall(r"<Dep Name=", m.group(2))), m.group(2)), doc, flags=re.S)
    gui = re.sub(r'<Expand  count="\d+">(.*?)</Expand>',
                 lambda m: '<Expand  count="%d">%s</Expand>' % (len(re.findall(r"<Expand name=", m.group(1))), m.group(1)), gui, count=1, flags=re.S)

    def _append(typ, nm, blk, vblk, deps=()):
        """one object: declaration, dependency row, data block, view provider"""
        nonlocal doc, gui, next_id
        if re.search(r'<Object type="[^"]+" name="%s"' % re.escape(nm), doc):
            raise RuntimeError("object %s collides with an object of the template; rename it" % nm)
        oid = next_id; next_id += 1
        if has_deps:
            drow = ('        <ObjectDeps Name="%s" Count="%d"%s\n' % (nm, len(deps), "/>" if not deps else
                    ">\n" + "".join('            <Dep Name="%s"/>\n' % d for d in deps) + "        </ObjectDeps>"))
            i0 = doc.index("<Objects "); i1 = doc.find("<Object type=", i0)
            i = doc.rfind("\n", 0, i1) + 1 if i1 != -1 else doc.index("</Objects>")
            doc = doc[:i] + drow + doc[i:]
        i = doc.index("</Objects>")
        doc = doc[:i] + '        <Object type="%s" name="%s" id="%d" />\n    ' % (typ, nm, oid) + doc[i:]
        i = doc.index("</ObjectData>")
        doc = doc[:i] + "        " + blk + "\n    " + doc[i:]
        i = gui.index("</ViewProviderData>")
        gui = gui[:i] + "        " + vblk + "\n        " + gui[i:]
        new_objs.append(nm)
        return oid

    if atlas_map:
        zm = zipfile.ZipFile(atlas_map, "r")
        mdoc = zm.read("Document.xml").decode("utf-8")
        mgui = zm.read("GuiDocument.xml").decode("utf-8") if "GuiDocument.xml" in zm.namelist() else ""
        if not mgui:
            raise RuntimeError("the atlas map %s has no GuiDocument.xml (saved headless) - render it with kit atlas render" % atlas_map)
        shown = atlas_group is None
        for typ, nm in re.findall(r'<Object type="([^"]+)" name="([^"]+)"[^>]*/>', mdoc):
            k = _block(mdoc, "Object", nm, mdoc.find("<ObjectData"))
            if not k:
                continue
            blk = mdoc[k[0]:k[1]]
            for f in set(re.findall(r'file="([^"]+)"', blk)):
                nf = "ATLAS_%s" % f
                blk = blk.replace('file="%s"' % f, 'file="%s"' % nf)
                payload[nf] = zm.read(f)
            if atlas_regions and nm in atlas_regions:
                r = atlas_regions[nm]
                blk = re.sub(r'(<Property name="Label" type="App::PropertyString"[^>]*>\s*<String value=")[^"]*(")',
                             lambda mm: mm.group(1) + _esc("[%s|%s] %s" % (r.get("definition_status", "?"), r.get("edit_status", "?"), nm)) + mm.group(2),
                             blk, count=1)
            g = _block(mgui, "ViewProvider", nm)
            if not g:
                raise RuntimeError("atlas object %s has no view provider in the map - its colour would be lost" % nm)
            vblk = mgui[g[0]:g[1]]
            for f in set(re.findall(r'file="([^"]+)"', vblk)):
                nf = "ATLAS_%s" % f
                vblk = vblk.replace('file="%s"' % f, 'file="%s"' % nf)
                payload[nf] = zm.read(f)
            _append(typ, nm, _setvis_text(blk, shown), _setvis_text(vblk, shown))
            added.append(nm); vis_new[nm] = shown
        say("atlas  : %d region object(s) from %s%s" % (len(added), os.path.basename(atlas_map),
                                                         "" if shown else ", hidden inside %s" % atlas_group[0]))

    mesh_names = []
    if meshes:
        if not meshdoc or not os.path.isfile(meshdoc):
            raise RuntimeError("--mesh needs the throw-away mesh document (built by _ccmeshdoc.py); none at %s" % meshdoc)
        zmd = zipfile.ZipFile(meshdoc, "r")
        mdoc = zmd.read("Document.xml").decode("utf-8")
        have = sorted(re.findall(r'<Object type="Mesh::Feature" name="([^"]+)"', mdoc))
        want = sorted(m["name"] for m in meshes)
        if have != want:
            raise RuntimeError("the mesh document holds %s but the specs name %s" % (have, want))
        tvp, tz, tvp_name = _mesh_vp_template(vptemplate, zin, doc0, gui0)
        tfiles = set(re.findall(r'file="([^"]+)"', tvp))
        tapp = re.search(r'<MaterialList file="([^"]+)"', tvp).group(1)
        for m in meshes:
            nm = m["name"]
            k = _block(mdoc, "Object", nm, mdoc.find("<ObjectData"))
            blk = mdoc[k[0]:k[1]]
            for f in set(re.findall(r'file="([^"]+)"', blk)):
                nf = "MESH_%s_%s" % (nm, f)
                blk = blk.replace('file="%s"' % f, 'file="%s"' % nf)
                payload[nf] = zmd.read(f)
            if m.get("place_xml"):
                blk, _np = re.subn(r'<PropertyPlacement [^/]*/>', m["place_xml"], blk, count=1)
                if not _np:
                    raise RuntimeError("mesh %s: its object block carries no Placement property to set (the mesh document's form changed)" % nm)
            vblk = tvp.replace('name="%s"' % tvp_name, 'name="%s"' % nm, 1)
            vblk = re.sub(r'treeRank="-?\d+"', 'treeRank="%d"' % next_id, vblk, count=1)
            for f in tfiles:
                nf = "MESH_%s_%s" % (nm, f)
                vblk = vblk.replace('file="%s"' % f, 'file="%s"' % nf)
                raw = tz.read(f)
                if f == tapp:
                    r_, g_, b_ = m["rgb"]
                    raw = bytearray(raw); raw[8:12] = bytes([0xFF, b_, g_, r_]); raw = bytes(raw)
                payload[nf] = raw
            _append("Mesh::Feature", nm, _setvis_text(blk, m["vis"]), _setvis_text(vblk, m["vis"]))
            mesh_names.append(nm); vis_new[nm] = bool(m["vis"])
            say("mesh   : %s -> %s (%s, #%02x%02x%02x)%s" % (nm, m["group"], "shown" if m["vis"] else "hidden", *m["rgb"], (" placed: " + m["place_desc"]) if m.get("place_desc") else ""))

    # the brep's own location
    body_names = []
    for b_ in bodies:
        nm = b_["name"]
        if not os.path.isfile(b_["path"]):
            raise RuntimeError("body %s: no file at %s" % (nm, b_["path"]))
        ent = "BODY_%s.brp" % nm
        payload[ent] = open(b_["path"], "rb").read()
        pxml = b_.get("place_xml") or _KP.IDENTITY_XML
        blk = ('<Object name="%s">\n'
               '            <Properties Count="7" TransientCount="0">\n'
               '                <Property name="ExpressionEngine" type="App::PropertyExpressionEngine" status="67108864">\n'
               '                    <ExpressionEngine count="0">\n'
               '                    </ExpressionEngine>\n'
               '                </Property>\n'
               '                <Property name="Label" type="App::PropertyString" status="134217728">\n'
               '                    <String value="%s"/>\n'
               '                </Property>\n'
               '                <Property name="Label2" type="App::PropertyString" status="67108992">\n'
               '                    <String value=""/>\n'
               '                </Property>\n'
               '                <Property name="Placement" type="App::PropertyPlacement" status="8388608">\n'
               '                    %s\n'
               '                </Property>\n'
               '                <Property name="Shape" type="Part::PropertyPartShape">\n'
               '                    <Part file="%s"/>\n'
               '                </Property>\n'
               '                <Property name="ShapeMaterial" type="Materials::PropertyMaterial">\n'
               '                    <PropertyMaterial uuid="7f9fd73b-50c9-41d8-b7b2-575a030c1eeb"/>\n'
               '                </Property>\n'
               '                <Property name="Visibility" type="App::PropertyBool" status="648">\n'
               '                    <Bool value="%s"/>\n'
               '                </Property>\n'
               '            </Properties>\n'
               '        </Object>') % (nm, _esc(b_["label"]), pxml, ent, "true" if b_["vis"] else "false")
        r_, g_, bb_ = b_["rgb"]; col = (r_ << 24) | (g_ << 16) | (bb_ << 8) | 255
        vblk = ('<ViewProvider name="%s" expanded="0">\n'
                '            <Properties Count="4" TransientCount="0">\n'
                '                <Property name="ShapeColor" type="App::PropertyColor" status="1">\n'
                '                    <PropertyColor value="%d"/>\n'
                '                </Property>\n'
                '                <Property name="DiffuseColor" type="App::PropertyColorList" status="1">\n'
                '                    <ColorList file="" version="1"/>\n'
                '                </Property>\n'
                '                <Property name="Transparency" type="App::PropertyPercent" status="1">\n'
                '                    <Integer value="%d"/>\n'
                '                </Property>\n'
                '                <Property name="Visibility" type="App::PropertyBool" status="1">\n'
                '                    <Bool value="%s"/>\n'
                '                </Property>\n'
                '            </Properties>\n'
                '        </ViewProvider>') % (nm, col, int(b_.get("transparency", 0) or 0), "true" if b_["vis"] else "false")
        _append("Part::Feature", nm, blk, vblk)
        body_names.append(nm); vis_new[nm] = bool(b_["vis"])
        say("body   : %s -> %s (%s, #%02x%02x%02x, %.1f MB)%s" % (nm, b_["group"], "shown" if b_["vis"] else "hidden", r_, g_, bb_, len(payload[ent]) / 1e6,
                                                                   (" placed: " + b_["place_desc"]) if b_.get("place_desc") else " (the brep's own location, if any)"))

    members = {}
    for m in meshes:
        members.setdefault(m["group"], []).append(m["name"])
    for b_ in bodies:
        members.setdefault(b_["group"], []).append(b_["name"])
    new_labels = dict(groups)
    if atlas_group and added:
        members.setdefault(atlas_group[0], []).extend(added)
        new_labels[atlas_group[0]] = atlas_group[1]
    for gname, glabel in new_labels.items():
        mem = members.get(gname, [])
        if not mem:
            raise RuntimeError("--group %s has no members (no spec names it)" % gname)
        oid = next_id
        _append("App::DocumentObjectGroup", gname, _group_obj_xml(gname, glabel, mem), _group_vp_xml(gname, oid), deps=mem)
        vis_new[gname] = False
        say("group  : %s (hidden, collapsed) <- %s" % (gname, ", ".join(mem)))
    for gname, mem in members.items():
        if gname in new_labels:
            continue
        for nm in mem:
            doc = _add_member(doc, gname, nm)
        say("group  : %s (template) <- %s" % (gname, ", ".join(mem)))
        if any(vis_new.get(nm) for nm in mem) and gname not in show and gname not in hide:
            _gvis = re.search(r'<ViewProvider name="%s".*?<Property name="Visibility"[^>]*>\s*<Bool value="(\w+)"' % re.escape(gname), gui, re.S)
            if _gvis and _gvis.group(1).lower() != "true":
                show = list(show) + [gname]; say("group  : %s SHOWN - a shown body went into it (the template kept it hidden; --hide %s keeps it so)" % (gname, gname))

    doc = _set_count(doc, r'<Objects Count="(\d+)"', len(re.findall(r'<Object type="[^"]+" name="', doc)))
    doc = _set_count(doc, r'<ObjectData Count="(\d+)"', len(re.findall(r'<Object name="', doc)))
    gui = _set_count(gui, r'<ViewProviderData Count="(\d+)"', len(re.findall(r'<ViewProvider name="', gui)))

    allnames = re.findall(r'<ViewProvider name="([^"]+)"', gui)
    vis = {}
    for nm in allnames:
        if nm in vis_new:
            vis[nm] = vis_new[nm]
        elif nm == target or nm in show:
            vis[nm] = True
        elif nm in hide:
            vis[nm] = False
        elif nm.startswith(HIDE_DEFAULT_PREFIX):
            vis[nm] = False
        elif nm.startswith(SHOW_DEFAULT_PREFIX):
            vis[nm] = True
        else:
            vis[nm] = None
    for nm, v in vis.items():
        if v is None:
            continue
        gui, _ = _setvis(gui, "ViewProvider", nm, v)
        doc, _ = _setvis(doc, "Object", nm, v)
    _allvis = {}
    for _nm in allnames:
        _bv = _block(gui, "ViewProvider", _nm); _mv = re.search(r'<Property name="Visibility"[^>]*>\s*<Bool value="(\w+)"', gui[_bv[0]:_bv[1]]) if _bv else None
        if _mv: _allvis[_nm] = (_mv.group(1).lower() == "true")
    say("shown  : %s" % ", ".join(sorted(n for n, v in _allvis.items() if v)))
    say("hidden : %s" % ", ".join(sorted(n for n, v in _allvis.items() if v is False)))

    ncol = 0
    for m in list(re.finditer(r'<ViewProvider name="([^"]+)"', gui)):
        nm = m.group(1)
        g = _block(gui, "ViewProvider", nm)
        seg = gui[g[0]:g[1]]
        ml = re.search(r'<MaterialList file="([^"]+)"', seg)
        if not ml:
            continue
        try:
            raw = payload[ml.group(1)] if ml.group(1) in payload else zin.read(ml.group(1))
            r, g_, b_ = _diffuse(raw)
        except Exception:
            continue
        val = (r << 24) | (g_ << 16) | (b_ << 8) | 255
        if '<Property name="ShapeColor"' in seg:
            seg = re.sub(r'(<Property name="ShapeColor"[^>]*>\s*<PropertyColor value=")\d+(")',
                         lambda mm: mm.group(1) + str(val) + mm.group(2), seg, count=1)
        else:
            k = seg.find('<Property name="ShapeAppearance"')
            if k == -1:
                continue
            k2 = seg.find("</Property>", k) + len("</Property>")
            prop = ('\n                <Property name="ShapeColor" type="App::PropertyColor" status="1">\n'
                    '                    <PropertyColor value="%d"/>\n                </Property>' % val)
            seg = seg[:k2] + prop + seg[k2:]
            seg = re.sub(r'(<Properties Count=")(\d+)(")', lambda mm: mm.group(1) + str(int(mm.group(2)) + 1) + mm.group(3), seg, count=1)
        gui = gui[:g[0]] + seg + gui[g[1]:]
        ncol += 1
    say("colour : ShapeColor stated on %d object(s)" % ncol)

    if camera and bbox:
        cam = _camera_xml(camera, bbox)
        if re.search(r"<Camera settings=\"[^\"]*\"\s*/>", gui):
            gui = re.sub(r"<Camera settings=\"[^\"]*\"\s*/>", cam, gui, count=1)
        else:
            gui = gui.replace("</Document>", "    %s\n</Document>" % cam, 1)
        say("camera : %s, framed on the body" % camera)

    bad = []
    for nm_, txt in (("Document.xml", doc), ("GuiDocument.xml", gui)):
        try:
            ET.fromstring(txt)
        except ET.ParseError as e:
            bad.append("%s does not parse: %s" % (nm_, e))
    for lab, xml, cpat, bpat in (("Objects", doc, r'<Objects Count="(\d+)"', r'<Object type="[^"]+" name="'),
                                 ("ObjectData", doc, r'<ObjectData Count="(\d+)"', r'<Object name="'),
                                 ("ViewProviderData", gui, r'<ViewProviderData Count="(\d+)"', r'<ViewProvider name="')):
        declared = _count(xml, cpat); present = len(re.findall(bpat, xml))
        if declared != present:
            bad.append("%s Count=%s but %d blocks present - FreeCAD loads exactly Count and drops the rest" % (lab, declared, present))
    for vp in re.findall(r"<ViewProvider name=.*?</ViewProvider>", gui, re.S):
        nmv = re.search(r'name="([^"]+)"', vp).group(1)
        dn = re.search(r'<Properties Count="(\d+)"', vp)
        if dn and int(dn.group(1)) != len(re.findall(r"<Property name=", vp)):
            bad.append("view provider %s: Properties Count %s, %d properties" % (nmv, dn.group(1), len(re.findall(r"<Property name=", vp))))
    declared_names = re.findall(r'<Object type="[^"]+" name="([^"]+)"', doc)
    if len(declared_names) != len(set(declared_names)):
        bad.append("duplicate object names: %s" % sorted(n for n in set(declared_names) if declared_names.count(n) > 1))
    ids = re.findall(r'<Object type="[^"]+" name="[^"]+" id="(\d+)"', doc)
    if len(ids) != len(set(ids)):
        bad.append("duplicate object ids")
    data_names = set(re.findall(r'<Object name="([^"]+)"', doc)); vp_names = set(re.findall(r'<ViewProvider name="([^"]+)"', gui))
    for nm in declared_names:
        if nm not in data_names: bad.append("%s is declared but has no data block" % nm)
        if nm not in vp_names: bad.append("%s has no view provider" % nm)
    for nm in set(re.findall(r'<Link value="([^"]+)"', doc)) | set(re.findall(r'<Dep Name="([^"]+)"', doc)):
        if nm not in data_names:
            bad.append("a group links %s, which is not an object of the document" % nm)
    entries = set(n for n in names if n not in ("Document.xml", "GuiDocument.xml") and n not in FC_OWN_ENTRIES) - dropped_files      # thumbnail
    if target:
        entries = {n for n in entries if not n.startswith(target + ".Shape.Map")}
    entries |= set(payload)
    refs = set(re.findall(r'file="([^"]+)"', doc)) | set(re.findall(r'file="([^"]+)"', gui))
    orphan = sorted(entries - refs); missing = sorted(refs - entries)
    if orphan: bad.append("orphan zip entries (no reference): %s" % orphan[:8])
    if missing: bad.append("missing zip entries (referenced, absent): %s" % missing[:8])
    for nm, v in vis.items():
        if v is None:
            continue
        gv = re.search(r'<ViewProvider name="%s".*?<Property name="Visibility"[^>]*>\s*<Bool value="(\w+)"' % re.escape(nm), gui, re.S)
        dv = re.search(r'<Object name="%s"(?: [^>]*)?>.*?<Property name="Visibility"[^>]*>\s*<Bool value="(\w+)"' % re.escape(nm), doc, re.S)
        want = "true" if v else "false"
        if gv and dv and not (gv.group(1) == dv.group(1) == want):
            bad.append("%s visibility gui %s / doc %s, wanted %s" % (nm, gv.group(1), dv.group(1), want))
    if bad:
        raise RuntimeError("REFUSED - " + "; ".join(bad))

    # thumbnail  recorded
    stale_thumbs = sorted(n for n in names if n in FC_OWN_ENTRIES)
    if stale_thumbs:
        say("thumbnail: %s DROPPED - the template's own picture of the PREVIOUS model (kit deliver draws none: zip surgery, no kernel; FreeCAD writes a fresh one at its next GUI save)" % ", ".join(stale_thumbs))
    # GuiDocument
    newshape = open(shape, "rb").read() if (target and shape) else None
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    tmp = out + ".tmp"
    gui_refs = set(re.findall(r'file="([^"]+)"', gui))
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zout:
        zout.writestr("Document.xml", doc.encode("utf-8"))
        for n in names:
            if n in dropped_files or n in ("Document.xml", "GuiDocument.xml") or (target and n.startswith(target + ".Shape.Map")) or n in FC_OWN_ENTRIES:      # thumbnail
                continue
            if n in gui_refs:
                continue                                    # GuiDocument
            zout.writestr(n, newshape if n == brp else zin.read(n))
        for f, b_ in payload.items():
            if f not in gui_refs:
                zout.writestr(f, b_)
        zout.writestr("GuiDocument.xml", gui.encode("utf-8"))
        for n in names:
            if n in gui_refs and n not in dropped_files and n not in ("Document.xml", "GuiDocument.xml"):
                zout.writestr(n, zin.read(n))
        for f, b_ in payload.items():
            if f in gui_refs:
                zout.writestr(f, b_)
    zin.close()
    os.replace(tmp, out)
    say("WROTE  : %s (%.1f MB)" % (out, os.path.getsize(out) / 1e6))
    return {"out": out, "body_entry": brp, "added": added, "meshes": mesh_names, "bodies": body_names, "groups": sorted(new_labels),
            "dropped": sorted(dropped_files), "colours": ncol,
            "thumbnail_dropped": stale_thumbs,      # thumbnail
            "thumbnail": ("DROPPED %s - the template's picture of the previous model; kit deliver draws none (zip surgery, no kernel) - FreeCAD writes a fresh one at its next GUI save" % ", ".join(stale_thumbs)) if stale_thumbs else "none in the template",
            "shown": sorted(n for n, v in vis.items() if v), "hidden": sorted(n for n, v in vis.items() if v is False)}


def _stem(name_, rev_):
    """31bq TT (B35 (1')): a file stem with its REV prefix stripped however it was written - separators (space, _, -) collapsed to one _, none leading or
    trailing, the REV taken off the front as many times as it stands there (R33__X, _R33_X, 'R33 _X', R33_-R33_X -> X)"""
    s_ = re.sub(r"[\s_\-]+", "_", str(name_ or "")).strip("_"); r_ = re.sub(r"[\s_\-]+", "_", str(rev_ or "")).strip("_")
    while r_ and s_.lower().startswith(r_.lower()) and (len(s_) == len(r_) or s_[len(r_)] == "_"):
        s_ = s_[len(r_):].lstrip("_")
    return s_


def _deliver_name(raw_, rev_, root_):
    """31bq TT (B35 (1')): the delivery's stem and what to say about it - the --name stripped of the REV; empty (a bare REV, or nothing) -> the project's own
    name, stripped the same way (root R33_MYPART + --name R33 had given R33_R33_MYPART), else MODEL; a bare-REV --name is SAID (it was replaced silently)"""
    nm_ = _stem(raw_, rev_); said_ = ""
    if not nm_:
        nm_ = _stem(os.path.basename(os.path.normpath(root_)).upper(), rev_) or "MODEL"
        if str(raw_ or "").strip(): said_ = "kit deliver: --name %r is the REV alone - the file is named by the project: %s_%s" % (raw_, rev_, nm_)
    return nm_, said_


def _place_fields(kind, name, place):
    """31br B5: the placement of a spec -> (place dict | None, its XML | None, its words | None); a bad one raises ValueError naming the object"""
    if place is None or place == "" or (isinstance(place, dict) and not place):
        return None, None, None
    try:
        pl = _KP.parse_place_field(place) if isinstance(place, str) else _KP.parse_place_json(place)
    except ValueError as e:
        raise ValueError("%s %s: %s" % (kind, name, e))
    if pl is None or _KP.is_identity(pl):
        return None, None, None
    return pl, _KP.xml_placement(pl), _KP.describe(pl)


def _one_body(name, label, path, shown, rgb, group, raw="", place=None):
    """31br B2: one --add-body spec. The path is a .brep; a place= rides as a placement dict (baked by cmd() before build())."""
    if not str(path).lower().endswith(".brep"):
        raise ValueError("body %s: a body is a .brep (got %s) - a mesh goes in with --mesh" % (name, path))
    if not os.path.isfile(path):
        raise ValueError("body %s: no file at %s" % (name, path))
    d = _one_mesh(name, label, path, shown, rgb, group, raw=raw)
    d["place"], d["place_xml"], d["place_desc"] = _place_fields("body", name, place)
    return d


def _parse_bodies(spec):
    """--add-body "name|label|path.brep|shown(1/0)|r,g,b|group[|place=dx,dy,dz,ax,ay,az,deg[,px,py,pz]];..." (31br B2 / B5; several specs by ; or several --add-body)"""
    out = []
    for s in [x for x in (spec or "").split(";") if x.strip()]:
        t = [x.strip() for x in s.split("|")]
        if len(t) == 7 and t[6].lower().startswith("place="):
            out.append(_one_body(*t[:6], raw=s, place=t[6]))
        elif len(t) == 6:
            out.append(_one_body(*t, raw=s))
        else:
            raise ValueError("a body spec has six fields name|label|path.brep|shown|r,g,b|group, or seven with place=dx,dy,dz,ax,ay,az,deg[,px,py,pz] last - got %d in %r"
                             " (labels may not contain ; or |; the JSON form --mesh-file takes any label: {\"bodies\": [{\"name\", \"label\", \"path\", \"shown\", \"rgb\", \"group\", \"place\": {...}}]})" % (len(t), s))
    return out


def _template_placement(template, target):
    """31br B5: the template body's own <PropertyPlacement> as a placement dict (None when the object or the property is not there)"""
    try:
        z = zipfile.ZipFile(template, "r"); d = z.read("Document.xml").decode("utf-8"); z.close()
    except (OSError, KeyError, zipfile.BadZipFile):
        return None
    b = _block(d, "Object", target, d.find("<ObjectData"))
    return _KP.parse_xml_placement(d[b[0]:b[1]]) if b else None


def _one_mesh(name, label, path, shown, rgb, group, raw="", place=None):
    if not os.path.isfile(path):
        raise ValueError("mesh %s: no file at %s" % (name, path))
    try:
        if isinstance(rgb, str):
            rgb = tuple(int(c) for c in rgb.split(","))
        rgb = tuple(int(c) for c in rgb)
        assert len(rgb) == 3 and all(0 <= c <= 255 for c in rgb)
    except Exception:
        raise ValueError("mesh %s: colour is r,g,b in 0-255, got %r" % (name, rgb))
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
        raise ValueError("mesh %s: the object name is letters, digits and _ only" % name)
    vis = shown if isinstance(shown, bool) else str(shown).strip().lower() in ("1", "true", "yes")
    d = {"name": name, "label": label, "path": path, "vis": vis, "rgb": rgb, "group": group}
    d["place"], d["place_xml"], d["place_desc"] = _place_fields("mesh", name, place)
    return d


def _parse_meshes(spec):
    """--mesh "name|label|path.stl|shown(1/0)|r,g,b|group;..."

    THE LABEL SHARES THE SPEC'S DELIMITERS (2026-09-25, lessons K20 / R33 notes 24: the R33 delivery was refused because
    its label read "films closed; decimated" - one ';' split the spec, and the message named none of it). A spec that
    does not parse now says WHICH character in WHICH field did it, and points at --mesh-file, the JSON form that takes
    any label at all."""
    out = []
    for s in [x for x in (spec or "").split(";") if x.strip()]:
        t = [x.strip() for x in s.split("|")]
        if len(t) == 7 and t[6].lower().startswith("place="):
            out.append(_one_mesh(*t[:6], raw=s, place=t[6])); continue
        if len(t) != 6:
            hint = ""
            if len(t) < 6 and (spec or "").count(";") >= 1:
                hint = (" - a ';' inside a label splits the spec (this piece has %d fields). Labels may not contain ';' or '|';"
                        " write the specs as JSON with --mesh-file <specs.json> instead" % len(t))
            elif len(t) > 6:
                hint = " - a '|' inside a label adds a field. Labels may not contain ';' or '|'; use --mesh-file <specs.json>"
            raise ValueError("a mesh spec has six fields name|label|path.stl|shown|r,g,b|group (a seventh, place=dx,dy,dz,ax,ay,az,deg, is optional) - got %r%s" % (s, hint))
        out.append(_one_mesh(*t, raw=s))
    return out


def _parse_mesh_file(path):
    """--mesh-file <specs.json>: [{"name":..,"label":..,"path":..,"shown":true,"rgb":[r,g,b],"group":..}, ...]
    (or {"meshes": [...], "groups": [{"name":..,"label":..}, ...]}) - any label, no delimiter rules."""
    import json
    try:
        d = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError("--mesh-file %s: %s" % (path, e))
    lst = d.get("meshes", []) if isinstance(d, dict) else d
    grp = d.get("groups", []) if isinstance(d, dict) else []
    out = []
    for it in lst:
        try:
            out.append(_one_mesh(it["name"], it.get("label", it["name"]), it["path"], it.get("shown", it.get("vis", False)),
                                 it.get("rgb", [200, 200, 200]), it["group"], place=it.get("place")))
        except KeyError as e:
            raise ValueError("--mesh-file %s: a mesh entry lacks %s (name, path, group are required)" % (path, e))
    bodies = []
    for it in (d.get("bodies", []) if isinstance(d, dict) else []):
        try:
            bodies.append(_one_body(it["name"], it.get("label", it["name"]), it["path"], it.get("shown", it.get("vis", True)),
                                    it.get("rgb", [200, 200, 200]), it["group"], place=it.get("place")))
        except KeyError as e:
            raise ValueError("--mesh-file %s: a body entry lacks %s (name, path, group are required)" % (path, e))
    groups = []
    for g in grp:
        nm = (g.get("name") if isinstance(g, dict) else str(g)) or ""
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", nm):
            raise ValueError("--mesh-file %s: group %r: the object name is letters, digits and _ only" % (path, nm))
        groups.append((nm, (g.get("label") if isinstance(g, dict) else nm) or nm))
    return out, groups, bodies


def _parse_groups(spec):
    out = []
    for s in [x for x in (spec or "").split(";") if x.strip()]:
        nm, lab = (s.split("|", 1) + [""])[:2]
        nm = nm.strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", nm):
            raise ValueError("group %r: the object name is letters, digits and _ only" % nm)
        out.append((nm, (lab or nm).strip()))
    return out


def cmd(args, kit):
    r"""kit deliver <REV> --template <previous delivery.FCStd> [--target <body object> [--model <brep>] [--drop-placement]]
                [--add-body "name|label|path.brep|shown|r,g,b|group[|place=dx,dy,dz,ax,ay,az,deg[,px,py,pz]];..."] (several; 31br B2 / B5)
                [--mesh "name|label|path.stl|shown|r,g,b|group[|place=...];..."] [--group "name|label;..."]
                [--mesh-file <specs.json>: [{"name","label","path","shown","rgb":[r,g,b],"group"},...] or
                 {"meshes":[...],"groups":[{"name","label"},...],"bodies":[{"name","label","path","shown","rgb","group","place":{"translate":[..],"rotate":[ax,ay,az,deg],"about":[..]}}]}
                 - any label; ';' and '|' are the --mesh / --add-body forms' delimiters]
                [--atlas-group "name|label" | --atlas-loose] [--map <map.FCStd>] [--vptemplate <gui-saved.FCStd>]
                [--name <stem>] [--label "..."] [--drop a,b] [--show a,b] [--hide a,b]
                [--camera iso|top|front|right|left|rear|bottom] [--no-atlas "<why>"]
                [--review <dir> | --no-review "<why>"] [--recreate-waived "<the client's words>"]
                [--trial "<the client's request, in the client's words>" --model <the job's body_trial.brep>]

    31av - A TRIAL, ON THE CLIENT'S REQUEST ONLY (the client 2026-10-07: "There was a trial delivery I opened, I'm fine with only getting them on my request, it
    would be wasteful to make one every time"): --trial writes the trial body (a piece sewn in as a look, not yet accepted) as
    Deliverables\<REV>\review\<REV>_<name>_TRIAL.FCStd - review material, not a delivery: no atlas objects, no review dir asked (the trial's own
    review_body frames are its look), recorded with their words; never Deliverables\<REV>\model\.

    THE DELIVERY RECIPE (the client, 2026-09-24): the previous delivery's structure (G1_PRINT shown, G2_ASSEMBLY /
    G3_REFERENCE / G4_MARKERS hidden) + the model being reviewed + the atlas map's objects in ONE hidden collapsed
    group, by zip surgery; then `kit deliverycheck`.
      B-rep round : --target <the template's body object>; the model of record is swapped into it.
      Mesh round  : --mesh, one spec per Mesh::Feature - the print file into G1_PRINT shown, its sources into a
                    --group of their own hidden; --drop the template's body when the mesh replaces it.
      Bodies      : --add-body, one spec per Part::Feature (31br B2 - a fixture's parts, a new project's first bodies): each goes INTO a
                    template group or a --group; a `place=` turns and moves it (31br B5: rotate deg about the axis through the point, THEN
                    translate - baked into a copy of the brep, the XML Placement written to match: what FreeCAD reads back). A brep placed by
                    `kit place` needs no place= (its location rides). A --target swap keeps the template body's own Placement the same way
                    (it used to reset to identity); --drop-placement sits the swapped body at its brep's own location instead.
                    THE ATLAS MAP (--map / kit tool atlas_colour) IS NOT A BODY CARRIER - the gates read that group as the atlas.
    Refused while the atlas map is behind the model of record (kit atlas render), or while a frozen region's
    recreate is owed, unless --no-atlas gives the client's reason.
    """
    G = kit.G
    if not args or args[0].startswith("-"):
        print(cmd.__doc__); return 2
    rev = args[0]
    template = kit._opt(args, "--template", "")
    target = kit._opt(args, "--target", "")
    try:
        meshes = _parse_meshes(kit._opt(args, "--mesh", ""))
        groups = _parse_groups(kit._opt(args, "--group", ""))
        _ab = kit._all(args, "--add-body") if hasattr(kit, "_all") else ([kit._opt(args, "--add-body", "")] if kit._opt(args, "--add-body", "") else [])      # --add-body
        bodies = _parse_bodies(";".join(x for x in _ab if x))
        if kit._opt(args, "--mesh-file", ""):
            m2, g2, b2 = _parse_mesh_file(kit._opt(args, "--mesh-file", ""))
            meshes += m2; groups += g2; bodies += b2
        _dup = sorted({x["name"] for x in bodies if [y["name"] for y in bodies + meshes].count(x["name"]) > 1} | {x["name"] for x in meshes if [y["name"] for y in bodies + meshes].count(x["name"]) > 1})
        if _dup:
            raise ValueError("an object name is used twice in the specs: %s" % ", ".join(_dup))
    except ValueError as e:
        print("kit deliver: %s" % e); return 2
    if not template:
        print("kit deliver: --template <the previous delivery: a GUI-saved FCStd holding the groups, assembly, reference and\n"
              "  marker objects> is required."); return 2
    if not os.path.isfile(template):
        print("kit deliver: --template names a file that does not exist: %s" % template); return 2
    if not target and not meshes and not bodies:
        print("kit deliver: --target <the template's body object name> (a B-rep swap), --add-body <specs> (Part::Feature bodies) or --mesh <specs> (a mesh delivery) is required."); return 2
    trial = (kit._opt(args, "--trial", "") or "").strip()
    if kit._flag(args, "--trial") and not trial:
        trial = " "
    if trial:
        if len(trial.strip()) < 15:
            print("kit deliver REFUSED: --trial carries the client's request in the client's words (the client 2026-10-07: \"I'm fine with only getting them on my request\") -\n"
                  "  a trial file is made when the client asks for one, never on every trial."); return 2
        if not target or not kit._opt(args, "--model", ""):
            print("kit deliver REFUSED: --trial is the trial's B-rep body: --target <the template's body object> --model <the job's body_trial.brep>\n"
                  "  (never the model of record - that is a real delivery, without --trial)."); return 2
    model = ""
    if target:
        model = kit._resolve_project_path(kit._opt(args, "--model", "")) or kit._model_of_record()
        if kit._opt(args, "--model", "") and not os.path.isfile(model):
            _jd8 = os.path.dirname(os.path.abspath(model)); _tj8 = {}
            try: _tj8 = json.load(open(os.path.join(_jd8, "TRIAL.json"), encoding="utf-8")) if os.path.isfile(os.path.join(_jd8, "TRIAL.json")) else {}
            except (OSError, ValueError): _tj8 = {}
            print("kit deliver: no such file: %s%s" % (model, ("\n  The trial was ACCEPTED (%s) - its body is now %s (--model that file)" % (_tj8.get("accepted_when"), os.path.join(_jd8, "body_new.brep")))
                                                      if (_tj8.get("accepted") and os.path.basename(model).lower() == "body_trial.brep") else "")); return 2
        if not model or not os.path.isfile(model):
            print("kit deliver: no model of record (--model <brep>, or open the session)."); return 2
        if not kit._real_path(model).lower().endswith(".brep"):
            print("kit deliver: the model must be a .brep (the bank's); got %s (its real path %s)" % (model, kit._real_path(model))); return 2
    if trial:
        _jd = os.path.dirname(os.path.abspath(model)); _tjp = os.path.join(_jd, "TRIAL.json"); _no = []
        try: _tj = json.load(open(_tjp, encoding="utf-8")) if os.path.isfile(_tjp) else None
        except (OSError, ValueError): _tj = None
        _mm = kit._md5(model)
        if _tj is None: _no.append("%s has no TRIAL.json beside it - it is not a trial's body" % model)
        else:
            if not _tj.get("done"): _no.append("the trial's STEP 4 did not finish (TRIAL.json)")
            _cpass = _tj.get("check_pass") if _tj.get("check_pass") is not None else str(_tj.get("check", "")).strip().startswith("CHECK PASS")
            if not _cpass: _no.append("the trial's STEP 4 was not CHECK PASS (%s)" % str(_tj.get("check", ""))[:90])
            _bn = os.path.basename(model).lower()
            if _bn == "body_trial.brep" and _mm != _tj.get("trial_body_md5"): _no.append("body_trial.brep is not the body that trial's STEP 4 checked (md5 %s; TRIAL.json trial_body_md5 %s)" % (_mm[:8], str(_tj.get("trial_body_md5"))[:8]))
            elif _bn == "body_new.brep" and not (_tj.get("accepted") and _mm == _tj.get("body_md5")): _no.append("body_new.brep is not the ACCEPTED trial's body (TRIAL.json accepted %s, body_md5 %s; the file %s)" % (bool(_tj.get("accepted")), str(_tj.get("body_md5"))[:8], _mm[:8]))
            elif _bn not in ("body_trial.brep", "body_new.brep"): _no.append("--model is %s - a trial file is the trial's body_trial.brep (or an accepted trial's body_new.brep)" % os.path.basename(model))
        if _no:
            print("kit deliver REFUSED: --trial ships a trial that passed its own check, as that trial's body (31bq R7W D4):\n    %s" % "\n    ".join(_no)); return 2
    elif target:
        _jobs = G._read(G._p(kit.ROOT, G.JOBS), {}) or {}
        _applied = [n_ for n_, j_ in _jobs.items() if isinstance(j_, dict) and j_.get("applied_to") and kit._same_file(j_["applied_to"], model)]
        _promo = [p_ for p_ in ((G.session(kit.ROOT) or {}).get("promotions") or []) if kit._same_file(p_.get("to") or "", model)]
        _injobs, _jwhy = kit._jobs_file(model)
        _inbank = kit._in_folder(model, os.path.join(kit.ROOT, "claude_code", "bank"))
        if not _applied and (_injobs or (_promo and not _inbank)):
            print("kit deliver REFUSED: %s is %s and no APPLIED job stands behind it (no job's `kit apply` wrote it) - a delivery ships the model a\n"
                  "  job's apply made, through the gate (kit accept -> kit apply --job <J>). A look at a trial body is `kit deliver --trial` (31bq R7W D7)."
                  % (model, _jwhy if _injobs else "a model of record reached by a promotion (%s)" % (_promo[-1].get("note") or "no note")))
            return 2
    doc = G.atlas_load(kit.ROOT)
    regs = (doc or {}).get("regions", {})
    atlas_map = None
    why = kit._opt(args, "--no-atlas", "") or (("TRIAL on the client's request - a look at the real model, not a delivery: %s" % trial) if trial else "")
    _dfr = G.atlas_defer_active(kit.ROOT)
    if _dfr and not doc:
        print("  atlas  : DEFERRED (\"%s\", %s) - no atlas objects in this delivery, no --no-atlas owed (31bv B1)" % (_dfr.get("until"), _dfr.get("when")))
        if not why: why = "atlas deferred on the client's word: %s" % _dfr.get("until")
    if doc and regs:
        behind, msg = kit.atlas_behind(doc)
        owed = G.atlas_recreate_owed(kit.ROOT)
        if owed and not why:
            print("kit deliver REFUSED: a frozen region's recreate is OWED - %s. Measure it back (kit atlas recreated <r>\n"
                  "  --result <file>) or give the client's reason with --no-atlas \"...\"." % ", ".join(sorted(owed))); return 2
        if behind and not why:
            print("kit deliver REFUSED: %s.\n  The atlas is maintained on the latest brep (the client, 2026-09-24). Render it, or give the client's reason\n"
                  "  with --no-atlas \"...\" (recorded in the delivery's status)." % msg); return 2
        if not behind and not trial:
            atlas_map = (doc.get("rendered") or {}).get("out")
            if atlas_map and not os.path.isfile(atlas_map):
                print("kit deliver REFUSED: the rendered atlas map is missing on disk: %s" % atlas_map); return 2
    elif not why:
        print("kit deliver: NOTE - this project has no atlas; delivering without map objects. (kit atlas init when CAD exists.)")
    if kit._opt(args, "--map", ""):
        atlas_map = kit._opt(args, "--map", "")          # recorded
        if not os.path.isfile(atlas_map):
            print("kit deliver: --map %s does not exist" % atlas_map); return 2
    atlas_group = None
    if atlas_map and not kit._flag(args, "--atlas-loose"):
        ag = kit._opt(args, "--atlas-group", "") or "G5_ATLAS|5  REGION ATLAS  (coloured, hidden - tick the group to paint it)"
        try:
            atlas_group = _parse_groups(ag)[0]
        except (ValueError, IndexError) as e:
            print("kit deliver: --atlas-group %s" % e); return 2
    name, _said_nm = _deliver_name(kit._opt(args, "--name", ""), rev, kit.ROOT)
    if _said_nm: print(_said_nm)
    if name.upper().endswith("_STAGING"):
        print("kit deliver REFUSED: the name %r ends in _STAGING - its file would be another delivery's staging file (31bq B35); choose another --name" % name); return 2
    import leangate as _LGd; _droot = _LGd.records_root(kit.ROOT)
    out = os.path.join(_droot, "Deliverables", rev, "model", "%s_%s.FCStd" % (rev, name))
    if trial:
        out = os.path.join(_droot, "Deliverables", rev, "review", "%s_%s_TRIAL.FCStd" % (rev, name))
        os.makedirs(os.path.dirname(out), exist_ok=True)
    final_out = out; out = out[:-6] + "_STAGING.FCStd"
    if os.path.exists(final_out):
        try:
            with open(final_out, "r+b"):
                pass
            os.rename(final_out, final_out)
        except OSError as e:
            print("kit deliver REFUSED: %s exists and is LOCKED by another program (%s) - it is open in a viewer. Close it there,\n"
                  "  then run this again; nothing was built." % (final_out, e.__class__.__name__)); return 2
    drop = [x for x in (kit._opt(args, "--drop", "") or "").split(",") if x]
    show = [x for x in (kit._opt(args, "--show", "") or "").split(",") if x]
    hide = [x for x in (kit._opt(args, "--hide", "") or "").split(",") if x]
    camera = (kit._opt(args, "--camera", "iso") or "iso").lower()
    if camera not in CAMERAS:
        print("kit deliver: --camera is one of %s" % ", ".join(CAMERAS)); return 2
    shown_meshes = [m for m in meshes if m["vis"]]; shown_bodies = [b_ for b_ in bodies if b_["vis"]]
    bbox = _bbox_of(model) if model else (_bbox_of(shown_bodies[0]["path"]) if shown_bodies else (_bbox_of_stl(shown_meshes[0]["path"]) if shown_meshes else None))
    print("kit deliver: %s\n  model   : %s\n  template: %s\n  atlas   : %s%s"
          % (out, model or ", ".join("%s (%s)" % (x["name"], x["group"]) for x in list(bodies) + list(meshes)), template,
             atlas_map or ("SKIPPED - " + why if why else "none"), (" -> group %s" % atlas_group[0]) if atlas_group else ""))
    meshdoc = None
    if meshes:
        jobdir = os.path.join(_droot, "claude_code", "jobs", "DELIVER_%s_%s" % (rev, name))
        os.makedirs(jobdir, exist_ok=True)
        meshdoc = os.path.join(jobdir, "meshdoc.FCStd")
        env = dict(os.environ)
        _mj = os.path.join(jobdir, "meshdoc_specs.json")
        with open(_mj, "w", encoding="utf-8") as fh:
            json.dump([{"name": m["name"], "label": m["label"], "path": m["path"]} for m in meshes], fh)
        env["CC_MESHES_JSON"] = _mj
        env["CC_OUT"] = meshdoc
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mesh", "_ccmeshdoc.py")
        if os.path.exists(meshdoc):
            os.remove(meshdoc)
        print("  meshdoc : %s (%d mesh(es), freecadcmd)" % (meshdoc, len(meshes)))
        rc, _ = kit.sh([kit.freecad(), script], 1800, log=os.path.join(jobdir, "log_meshdoc.txt"), env=env, cwd=jobdir, outputs=(meshdoc,))
        if rc != 0 or not os.path.isfile(meshdoc):
            print("kit deliver: the mesh document was not written (rc %s) - %s" % (rc, os.path.join(jobdir, "log_meshdoc.txt"))); return 2
    _pjob = os.path.join(_droot, "claude_code", "jobs", "DELIVER_%s_%s" % (rev, name)); _placed = []; model_for_build = model; target_place_xml = None
    if target:
        _tpl_pl = _template_placement(template, target)
        if kit._flag(args, "--drop-placement"):
            target_place_xml = _KP.IDENTITY_XML
            if _tpl_pl and not _KP.is_identity(_tpl_pl):
                print("  placement: the template's %s carries a Placement (%s) - DROPPED (--drop-placement): the swapped body sits at its brep's own location" % (target, _KP.describe(_tpl_pl)))
        elif _tpl_pl and not _KP.is_identity(_tpl_pl):
            os.makedirs(_pjob, exist_ok=True); _pm = os.path.join(_pjob, "placed_%s.brep" % target); _plog = os.path.join(_pjob, "log_place_%s.txt" % target)
            print("  placement: the template's %s carries a Placement (%s) - CARRIED: baked into a copy of the model (%s; freecadcmd) so FreeCAD reads it back;\n"
                  "             --drop-placement sits the body at its brep's own location instead (31br B5)" % (target, _KP.describe(_tpl_pl), _pm))
            rc_, res_ = _KP.run_kernel(kit, model, _pm, _tpl_pl, log=_plog)
            if rc_ != 0:
                print("kit deliver: the placement step for %s FAILED (rc %s) - %s" % (target, rc_, _plog)); return 2
            if res_ and res_.get("location_before"):
                print("  placement: NOTE - the model %s carried a location of its own (%s); the template's Placement was composed ON TOP of it. If the model was already placed, run again with --drop-placement" % (os.path.basename(model), res_["location_before"]))
            _placed.append({"object": target, "from": model, "placed": _pm, "placement": _tpl_pl, "result": res_}); model_for_build = _pm
    for b_ in bodies:
        if b_.get("place"):
            os.makedirs(_pjob, exist_ok=True); _pm = os.path.join(_pjob, "placed_%s.brep" % b_["name"]); _plog = os.path.join(_pjob, "log_place_%s.txt" % b_["name"])
            print("  placement: %s - %s (baked into %s; freecadcmd)" % (b_["name"], b_["place_desc"], _pm))
            rc_, res_ = _KP.run_kernel(kit, b_["path"], _pm, b_["place"], log=_plog)
            if rc_ != 0:
                print("kit deliver: the placement step for %s FAILED (rc %s) - %s" % (b_["name"], rc_, _plog)); return 2
            if res_ and res_.get("location_before"):
                print("  placement: NOTE - %s carried a location of its own (%s); place= was composed ON TOP of it (a brep from `kit place` needs no place=)" % (os.path.basename(b_["path"]), res_["location_before"]))
            _placed.append({"object": b_["name"], "from": b_["path"], "placed": _pm, "placement": b_["place"], "result": res_}); b_["path_src"] = b_["path"]; b_["path"] = _pm
    try:
        rep = build(template, model_for_build, out, target, label=kit._opt(args, "--label", "") or ("TRIAL (not accepted) - %s" % trial.strip()[:60] if trial else ""), drop=drop, show=show, hide=hide,
                    placeholder_label=(os.path.splitext(os.path.basename(model))[0] if (target and model and not trial and not kit._opt(args, "--label", "")) else ""),
                    atlas_map=atlas_map, atlas_regions=regs, camera=camera, bbox=bbox, say=lambda *a: print("  " + " ".join(str(x) for x in a)),
                    meshes=meshes, meshdoc=meshdoc, vptemplate=kit._opt(args, "--vptemplate", ""), atlas_group=atlas_group, groups=groups, bodies=bodies, target_place_xml=target_place_xml)
    except RuntimeError as e:
        print("kit deliver %s" % e); return 2
    rep.update({"rev": rev, "model": model, "model_md5": kit._md5(model) if model else "", "template": template, "atlas_map": atlas_map,
                "atlas_group": atlas_group, "mesh_specs": meshes, "no_atlas_why": why, "when": G._now(), "camera": camera,
                "trial": trial.strip() or None})
    rep.update({"body_specs": bodies, "placements": _placed, "model_for_build": model_for_build})
    _sfx = "_TRIAL" if trial else ""
    _dj = os.path.join(os.path.dirname(out), "%s_%s%s_STAGING.delivery.json" % (rev, name, _sfx)); _dj_final = os.path.join(os.path.dirname(out), "%s_%s%s.delivery.json" % (rev, name, _sfx))
    try:
        rep["out"] = out; rep["final_out"] = locals().get("final_out", out)
        with open(_dj, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=1)
    except OSError as _e_dj:
        print("kit deliver: the delivery record %s was NOT written (%s) - the file has no record beside it (31bq B35)" % (_dj, _e_dj))
    print("kit deliver: built. Now the check (the three grey faults, the counts, the entry order):")
    body = target or (shown_bodies[0]["name"] if shown_bodies else (shown_meshes[0]["name"] if shown_meshes else ""))
    chk = [out] + (["--body", body] if body else [])
    for k in ("--review", "--no-review", "--recreate-waived"):
        v = kit._opt(args, k, "")
        if v:
            chk += [k, v]
    if trial and not kit._opt(args, "--review", "") and not kit._opt(args, "--no-review", ""):
        chk += ["--no-review", "TRIAL on the client's request (a look at the real model; its review_body frames are its look): %s" % trial.strip()]
    if trial and not kit._opt(args, "--recreate-waived", ""):
        chk += ["--recreate-waived", "TRIAL on the client's request - not a delivery: %s" % trial.strip()]
    rc = kit.cmd_deliverycheck(chk)
    if rc:
        print("kit deliver: deliverycheck did NOT pass - the file stays STAGED at %s and is not a delivery (the previous %s, if any, is untouched - 31bq B35)." % (out, os.path.basename(final_out)))
    else:
        try:
            os.replace(out, final_out); out = final_out; print("kit deliver: deliverycheck passed - PROMOTED to %s" % final_out)
            try:
                rep["out"] = final_out
                with open(_dj, "w", encoding="utf-8") as fh: json.dump(rep, fh, indent=1)
                os.replace(_dj, _dj_final)
            except OSError as _e_dj2:
                print("kit deliver: the delivery record was NOT promoted to %s (%s) - the record beside the file may be an OLDER delivery's (model_md5) (31bq B35)" % (_dj_final, _e_dj2))
        except OSError as _e:
            print("kit deliver: deliverycheck passed but the staged file could not be promoted to %s (%s) - it stays at %s" % (final_out, _e, out)); rc = 2
        if trial and rc == 0:
            print("kit deliver: TRIAL written - %s. Review material on the client's request (\"%s\"); it is NOT a delivery." % (out, trial.strip()[:120]))
    return rc


def _placed_bbox(brep):
    """31bs W40 (2026-11-03): a body kit place wrote carries its placement as the brep's LOCATION, and the .brep text's triples are the RAW geometry before it - the frame map
    (claude_code\\PLACEMENTS.json, written by kit place) holds the placed bbox the kernel measured; read from there when the body is in it, else None"""
    try:
        d = os.path.dirname(os.path.abspath(brep)); root = None
        for _ in range(8):
            if os.path.isfile(os.path.join(d, "claude_code", "PLACEMENTS.json")):
                root = d; break
            if os.path.dirname(d) == d: break
            d = os.path.dirname(d)
        if root is None:
            return None
        key = os.path.relpath(os.path.abspath(brep), root).replace("\\", "/")
        rec = (json.load(open(os.path.join(root, "claude_code", "PLACEMENTS.json"), encoding="utf-8")) or {}).get(key) or {}
        if rec.get("md5"):
            import hashlib
            try:
                if hashlib.md5(open(brep, "rb").read()).hexdigest() != rec["md5"]: return None
            except OSError:
                return None
        else:
            try:
                if rec.get("when") and os.path.getmtime(brep) > time.mktime(time.strptime(rec["when"], "%Y-%m-%d %H:%M:%S")) + 5:
                    return None
            except (ValueError, OSError):
                return None
        bb = ((rec.get("result") or {}).get("bbox"))
        if bb and len(bb) == 6:
            return ((float(bb[0]), float(bb[2]), float(bb[4])), (float(bb[1]), float(bb[3]), float(bb[5])))
    except Exception:
        pass
    return None


def _bbox_of(brep):
    """the body's bounding box read off the .brep text (no kernel) - the camera only needs it roughly. 31bs W40: a body the frame map knows is framed where it was PLACED."""
    _pb = _placed_bbox(brep)
    if _pb is not None:
        return _pb
    try:
        import numpy as np
        pts = []
        with open(brep, "r", encoding="ascii", errors="ignore") as fh:
            for i, ln in enumerate(fh):
                if i > 400000:
                    break
                t = ln.split()
                if len(t) == 3:
                    try:
                        pts.append((float(t[0]), float(t[1]), float(t[2])))
                    except ValueError:
                        pass
        if len(pts) >= 4:
            a = np.array(pts)
            if len(pts) < 40:
                return (tuple(a.min(0)), tuple(a.max(0)))
            lo = np.percentile(a, 1, axis=0); hi = np.percentile(a, 99, axis=0)
            return (tuple(lo), tuple(hi))
    except Exception:
        pass
    return ((-150, -300, -20), (150, 0, 100))


def _bbox_of_stl(path):
    """the bounding box of a binary STL (no kernel); an ASCII one gets the default frame."""
    try:
        import numpy as np
        with open(path, "rb") as fh:
            head = fh.read(84)
        if len(head) < 84 or head[:5] == b"solid" and os.path.getsize(path) != 84 + 50 * struct.unpack("<I", head[80:84])[0]:
            return ((-150, -300, -20), (150, 0, 100))
        n = struct.unpack("<I", head[80:84])[0]
        rec = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        a = np.fromfile(path, dtype=rec, count=n, offset=84)["v"].reshape(-1, 3)
        return (tuple(float(x) for x in a.min(axis=0)), tuple(float(x) for x in a.max(axis=0)))
    except Exception:
        return ((-150, -300, -20), (150, 0, 100))

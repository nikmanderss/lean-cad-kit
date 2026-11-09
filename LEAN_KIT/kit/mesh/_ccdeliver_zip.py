# GuiDocument
# collapsed
import os, re, sys, zipfile, json
import xml.etree.ElementTree as ET


def say(*a):
    print(*a, flush=True)


v6 = zipfile.ZipFile(os.environ["CC_MAP"])
md = zipfile.ZipFile(os.environ["CC_MESHDOC"])
tpl = zipfile.ZipFile(os.environ["CC_VPTEMPLATE"])
doc = v6.read("Document.xml").decode("utf-8")
gui = v6.read("GuiDocument.xml").decode("utf-8")
mdoc = md.read("Document.xml").decode("utf-8")
view = {}
for spec in [s for s in os.environ["CC_MESHVIEW"].split(";") if s.strip()]:
    nm, vis, col = spec.split(":")
    view[nm] = (vis == "1", tuple(int(c) for c in col.split(",")))

if not os.environ.get("CC_ATLAS", "").strip():
    sys.exit("REFUSED: CC_ATLAS (the project's claude_code\\ATLAS.json) is not set - no default in the kit; kit mesh fills it")
atl = json.load(open(os.environ["CC_ATLAS"], encoding="utf-8"))["regions"]


def _relabel(m):
    blk = m.group(0); name = m.group(1)
    if name not in atl:
        return blk
    r = atl[name]
    return re.sub(r'(<Property name="Label" type="App::PropertyString"[^>]*>\s*<String value=")\[[^\]]*\]',
                  lambda k: k.group(1) + "[%s|%s]" % (r.get("definition_status", "?"), r.get("edit_status", "?")),
                  blk, count=1)


doc = re.sub(r'<Object name="([^"]+)"(?: [^>]*)?>.*?</Object>', _relabel, doc, flags=re.S)

decl = re.findall(r'<Object type="Mesh::Feature" name="([^"]+)"[^>]*/>', mdoc)
if sorted(decl) != sorted(view):
    sys.exit("REFUSED: CC_MESHVIEW lists %s but the mesh document holds %s" % (sorted(view), sorted(decl)))
next_id = max(int(x) for x in re.findall(r' id="(\d+)"', doc)) + 1
ids = {}
decl_xml = ""
for nm in decl:
    ids[nm] = next_id; next_id += 1
    decl_xml += '        <Object type="Mesh::Feature" name="%s" id="%d" />\n' % (nm, ids[nm])
deps_xml = ""
if 'Dependencies="1"' in re.search(r"<Objects [^>]*>", doc).group(0):
    for nm in decl:
        deps_xml += '        <ObjectDeps Name="%s" Count="0"/>\n' % nm
data_xml = ""
payload = {}
for nm in decl:
    blk = re.search(r'<Object name="%s"(?: [^>]*)?>.*?</Object>' % re.escape(nm), mdoc, re.S).group(0)
    blk = re.sub(r'(<Property name="Visibility" type="App::PropertyBool"[^>]*>\s*<Bool value=")(true|false)(")',
                 lambda k: k.group(1) + ("true" if view[nm][0] else "false") + k.group(3), blk)
    for f in re.findall(r'file="([^"]+)"', blk):
        if f in v6.namelist():
            sys.exit("REFUSED: mesh payload name %s collides with a v6 entry" % f)
        payload[f] = md.read(f)
    data_xml += "        " + blk + "\n"
# collapsed
# collapsed
group_xml = group_vp = ""; n_group = 0
if os.environ.get("CC_GROUP", "").strip():
    gname, glabel = (os.environ["CC_GROUP"].split("|", 1) + [""])[:2]
    glabel = glabel or gname
    members = [n for t, n in re.findall(r'<Object type="([^"]+)" name="([^"]+)"', doc) if n not in decl and n != gname]
    if not members:
        sys.exit("REFUSED: CC_GROUP set but the map document holds no objects to group")
    gid = next_id; next_id += 1; n_group = 1
    decl_xml += '        <Object type="App::DocumentObjectGroup" name="%s" id="%d" />\n' % (gname, gid)
    if 'Dependencies="1"' in re.search(r"<Objects [^>]*>", doc).group(0):
        deps_xml += '        <ObjectDeps Name="%s" Count="%d">\n%s        </ObjectDeps>\n' % (
            gname, len(members), "".join('            <Dep Name="%s"/>\n' % n for n in members))
    links = "".join('                        <Link value="%s"/>\n' % n for n in members)
    group_xml = ('        <Object name="%s" Extensions="True">\n'
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
                 '        </Object>\n') % (gname, len(members), links, glabel.replace("&", "&amp;").replace('"', "&quot;").replace("'", "&apos;"))
    group_vp = ('        <ViewProvider name="%s" expanded="0" treeRank="%d" Extensions="True">\n'
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
                '        </ViewProvider>\n') % (gname, gid)
    say("group %s: %d map objects inside, hidden, collapsed" % (gname, len(members)))
m = re.search(r'<Objects Count="(\d+)"([^>]*)>', doc)
n0 = int(m.group(1))
doc = doc.replace(m.group(0), '<Objects Count="%d"%s>' % (n0 + len(decl) + n_group, m.group(2)), 1)
i = doc.index("</Objects>"); doc = doc[:i] + deps_xml + decl_xml + "    " + doc[i:]
m = re.search(r'<ObjectData Count="(\d+)">', doc)
doc = doc.replace(m.group(0), '<ObjectData Count="%d">' % (int(m.group(1)) + len(decl) + n_group), 1)
i = doc.index("</ObjectData>"); doc = doc[:i] + data_xml + group_xml + "    " + doc[i:]

if os.environ.get("CC_HIDE_MAP") == "1":
    gui = re.sub(r"<ViewProvider name=.*?</ViewProvider>",
                 lambda k: re.sub(r'(<Property name="Visibility" type="App::PropertyBool"[^>]*>\s*<Bool value=")true(")',
                                  r"\1false\2", k.group(0)), gui, flags=re.S)
tg = tpl.read("GuiDocument.xml").decode("utf-8")
_vpn = os.environ.get("CC_VPNAME", "").strip()
if _vpn:
    _m = re.search(r'<ViewProvider name="%s".*?</ViewProvider>' % re.escape(_vpn), tg, re.S)
else:
    _m = next((m_ for m_ in re.finditer(r'<ViewProvider name="([^"]+)".*?</ViewProvider>', tg, re.S) if "<MaterialList" in m_.group(0)), None)
if not _m:
    sys.exit("REFUSED: no Mesh::Feature view provider%s in the template %s (a GUI-saved FCStd holding one coloured mesh)"
             % (" named %s" % _vpn if _vpn else " with a MaterialList", os.environ["CC_VPTEMPLATE"]))
tvp = _m.group(0)
_vpn = _vpn or re.search(r'<ViewProvider name="([^"]+)"', tvp).group(1)
tapp_name = re.search(r'<MaterialList file="([^"]+)"', tvp).group(1)
tapp = tpl.read(tapp_name)
vp_xml = ""
for nm in decl:
    vis, (r, g, b) = view[nm]
    app_name = "ShapeAppearance_%s" % nm
    blk = tvp.replace('name="%s"' % _vpn, 'name="%s"' % nm, 1)
    blk = re.sub(r'treeRank="\d+"', 'treeRank="%d"' % ids[nm], blk, count=1)
    blk = blk.replace('file="%s"' % tapp_name, 'file="%s"' % app_name)
    blk = re.sub(r'(<Property name="Visibility" type="App::PropertyBool"[^>]*>\s*<Bool value=")(true|false)(")',
                 lambda k: k.group(1) + ("true" if vis else "false") + k.group(3), blk)
    app = bytearray(tapp); app[8:12] = bytes([0xFF, b, g, r])
    payload[app_name] = bytes(app)
    vp_xml += "        " + blk + "\n"
m = re.search(r'<ViewProviderData Count="(\d+)">', gui)
gui = gui.replace(m.group(0), '<ViewProviderData Count="%d">' % (int(m.group(1)) + len(decl) + n_group), 1)
i = gui.index("</ViewProviderData>"); gui = gui[:i] + vp_xml + group_vp + "        " + gui[i:]

bad = []
for nm_, txt in (("Document.xml", doc), ("GuiDocument.xml", gui)):
    try:
        ET.fromstring(txt)
    except ET.ParseError as e:
        bad.append("%s does not parse: %s" % (nm_, e))
entries = [n for n in v6.namelist() if n not in ("Document.xml", "GuiDocument.xml")] + list(payload)
refs = set(re.findall(r'file="([^"]+)"', doc)) | set(re.findall(r'file="([^"]+)"', gui))
orphan = sorted(set(entries) - refs); missing = sorted(refs - set(entries))
if orphan: bad.append("orphan entries (no reference): %s" % orphan)
if missing: bad.append("missing entries (referenced, not in the zip): %s" % missing)
for vp in re.findall(r"<ViewProvider name=.*?</ViewProvider>", gui, re.S):
    nmv = re.search(r'name="([^"]+)"', vp).group(1)
    decl_n = int(re.search(r'<Properties Count="(\d+)"', vp).group(1))
    real_n = len(re.findall(r"<Property name=", vp))
    if decl_n != real_n: bad.append("view provider %s: Properties Count %d, %d properties" % (nmv, decl_n, real_n))
for nm in decl:
    gv = re.search(r'<ViewProvider name="%s".*?<Property name="Visibility"[^>]*>\s*<Bool value="(\w+)"' % nm, gui, re.S).group(1)
    dv = re.search(r'<Object name="%s"(?: [^>]*)?>.*?<Property name="Visibility"[^>]*>\s*<Bool value="(\w+)"' % nm, doc, re.S).group(1)
    want = "true" if view[nm][0] else "false"
    if not (gv == dv == want): bad.append("%s visibility gui %s doc %s want %s" % (nm, gv, dv, want))
n_obj = len(re.findall(r"<Object type=", doc)); n_vp = len(re.findall(r"<ViewProvider name=", gui))
say("objects %d, view providers %d, file table %d refs / %d entries" % (n_obj, n_vp, len(refs), len(entries)))
if n_obj != n_vp: bad.append("objects %d but view providers %d" % (n_obj, n_vp))
if bad:
    for b_ in bad: say("REFUSED:", b_)
    sys.exit(2)

# GuiDocument
out = os.environ["CC_OUT"]; tmp = out + ".tmp"
with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("Document.xml", doc.encode("utf-8"))
    for it in v6.infolist():
        if it.filename in ("Document.xml", "GuiDocument.xml"): continue
        z.writestr(it.filename, v6.read(it.filename), compress_type=zipfile.ZIP_DEFLATED)
    # GuiDocument
    # GuiDocument
    for f, b_ in payload.items():
        if not f.startswith("ShapeAppearance_"):
            z.writestr(f, b_, compress_type=zipfile.ZIP_DEFLATED)
    z.writestr("GuiDocument.xml", gui.encode("utf-8"))
    for f, b_ in payload.items():
        if f.startswith("ShapeAppearance_"):
            z.writestr(f, b_, compress_type=zipfile.ZIP_DEFLATED)
os.replace(tmp, out)
say("wrote %s (%.1f MB): %d v6 entries copied, %d added (%s); map %s at open"
    % (out, os.path.getsize(out) / 1e6, len(v6.namelist()) - 2, len(payload), ", ".join(payload),
       "HIDDEN" if os.environ.get("CC_HIDE_MAP") == "1" else "shown"))
say("DONE")

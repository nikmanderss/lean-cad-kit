# KIT INSTRUMENT `atlas_transfer` - carry an APPROVED region atlas onto a NEWER model of record: every face of the new
# body is assigned to the approved region whose surface it lies on, and the surface no approved region has (the edit)
# is named as such. This is how "the atlas is maintained on the latest brep at all times" (the client, 2026-09-24) is done
# without re-running the human corrections that built the atlas (face numbers do not carry across a revision).
# Run: kit tool atlas_transfer --job ATLAS --set ATLAS_SHAPE=<new body.brep> --set ATLAS_JSON=<claude_code\ATLAS.json>
#      --set ATLAS_OUTDIR=<folder> [--set ATLAS_TOL=0.5] [--set ATLAS_DEV=0.1]
# Inputs: ATLAS_SHAPE  ATLAS_JSON (its regions carry `surface_file`, the approved region's faces as a brep compound,
#         and `rgb`)  ATLAS_OUTDIR  ATLAS_TOL (mm: a triangle further than this from every approved piece is NEW)
# Output: manifest.json in atlas_features' format (per region: brep compound, rgb, pieces, area, from_faces, note),
#         regions.json (definition/edit statuses), transfer.json (how each face was placed) - then `atlas_colour`
#         builds the coloured map from the manifest.
#
# HOW A FACE FINDS ITS REGION, cheapest first:
#  1. IDENTITY - the same face (surface type, area, centre of mass, extents to 1e-3) exists in one approved region's
#     surface file: it is that region's. After a local edit this is nearly every face of the body.
#  2. SURFACE - the face's underlying SURFACE (the plane, cylinder or spline itself, not its trim) carries pieces in
#     the approved regions: if all of them are in one region the face is that region's; if the pieces lie in several
#     (the atlas CUT this face on a boundary) the face's triangles each take the region of the nearest piece and the
#     face goes to the region owning most of its AREA - reported MIXED, because a whole face is the unit here.
#  3. NEW - a face on a surface no approved region carries is new surface. It goes to the region whose recorded box
#     holds it and which a job EDITED (the atlas's `edited_by`), else to `_NEW_SURFACE` - a region of its own in
#     the map, so the client sees the edit the moment the map opens.
# Nothing here changes a definition: an approved region stays approved; the map is re-made on the new body.
import os, sys, json, time
sys.path.insert(0, os.environ["KIT_HOME"])
import FreeCAD as App
import Part


def say(*a):
    print(*a, flush=True)


T0 = time.time()
SHAPE = os.environ["ATLAS_SHAPE"]
ATLAS = json.load(open(os.environ["ATLAS_JSON"], encoding="utf-8"))
OUT = os.environ.get("ATLAS_OUTDIR") or os.getcwd()
TOL = float(os.environ.get("ATLAS_TOL", "0.5"))
DEV = float(os.environ.get("ATLAS_DEV", "0.1"))
ROOT = os.environ.get("KIT_PROJECT") or os.path.dirname(os.path.dirname(os.path.abspath(os.environ["ATLAS_JSON"])))
os.makedirs(OUT, exist_ok=True)

PALETTE = [(230, 76, 60), (52, 152, 219), (46, 204, 113), (241, 196, 15), (155, 89, 182), (26, 188, 156), (230, 126, 34),
           (149, 165, 166), (192, 57, 43), (41, 128, 185), (39, 174, 96), (243, 156, 18), (142, 68, 173), (22, 160, 133),
           (211, 84, 0), (127, 140, 141)]


def face_sig(f):
    c = f.CenterOfMass; b = f.BoundBox
    return (type(f.Surface).__name__, round(f.Area, 3), round(c.x, 3), round(c.y, 3), round(c.z, 3),
            round(b.XMin, 3), round(b.XMax, 3), round(b.YMin, 3), round(b.YMax, 3), round(b.ZMin, 3), round(b.ZMax, 3))


def surf_sig(f):
    """the underlying SURFACE, independent of the trim: its type and three fixed points on it."""
    s = f.Surface
    try:
        pts = [s.value(u, v) for u, v in ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0))]
        return (type(s).__name__,) + tuple(round(q, 3) for p in pts for q in (p.x, p.y, p.z))
    except Exception:
        return ("?",) + face_sig(f)[1:]


sh = Part.Shape(); sh.importBrep(SHAPE)
faces = sh.Faces
say("body: %d faces, %.0f mm2" % (len(faces), sum(f.Area for f in faces)))

regions = ATLAS.get("regions", {})
ident = {}
bysurf = {}
rgb = {}
loaded = []
for i, (name, r) in enumerate(regions.items()):
    sf = r.get("surface_file")
    if not sf:
        say("  %-24s NO surface_file - cannot transfer it; its faces will read as new or fall to neighbours" % name); continue
    p = sf if os.path.isabs(sf) else os.path.join(ROOT, sf)
    if not os.path.isfile(p):
        say("  %-24s surface file missing: %s" % (name, p)); continue
    rs = Part.Shape(); rs.importBrep(p)
    for f in rs.Faces:
        ident.setdefault(face_sig(f), name)
        bysurf.setdefault(surf_sig(f), {}).setdefault(name, []).append(f)
    rgb[name] = tuple(r.get("rgb") or PALETTE[i % len(PALETTE)])
    loaded.append(name)
    say("  %-24s %5d approved pieces" % (name, len(rs.Faces)))
say("tables: %d pieces, %d surfaces, %d regions  (%.0f s)" % (len(ident), len(bysurf), len(loaded), time.time() - T0))
if not ident:
    say("REFUSED: no approved region surface could be loaded - nothing to transfer. A map made now would call the whole\n"
        "  body NEW SURFACE, which is a report of the tool's inputs, not of the part. Check the atlas's surface_file paths.")
    raise SystemExit(2)

assign = {}
report = {"identity": 0, "surface": 0, "cut": 0, "new": 0, "mixed": [], "moved": [], "new_faces": []}
boxes = {n: r.get("box") for n, r in regions.items() if r.get("box")}
edited = {n for n, r in regions.items() if r.get("edited_by")}


def nearest_region_by_pieces(face, cands):
    """{region: area} of the face that each candidate region's pieces cover - an exact 2-D boolean on the shared
    surface (`face.common(pieces)`), milliseconds per region; what no piece covers is NEW surface."""
    share = {}
    covered = 0.0
    for nm, pieces in cands.items():
        try:
            a = face.common(Part.Compound(pieces)).Area
        except Exception:
            a = 0.0
        if a > 1e-6:
            share[nm] = a; covered += a
    rest = face.Area - covered
    if rest > max(1e-3 * face.Area, 0.05):
        share["_NEW_SURFACE"] = rest
    return share


def _point_on(pc):
    """a point ON the piece's own surface near its centre - the centre of mass of a curved piece lies off the
    surface by the sagitta, which is more than the tolerance on a big skin patch."""
    com = pc.CenterOfMass
    try:
        u, v = pc.Surface.parameter(com)
        if pc.isPartOfDomain(u, v):
            return pc.valueAt(u, v)
    except Exception:
        pass
    try:
        u0, u1, v0, v1 = pc.ParameterRange
        u, v = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
        if pc.isPartOfDomain(u, v):
            return pc.valueAt(u, v)
    except Exception:
        pass
    return com


def pieces_on(face):
    """{region: area} of approved pieces that LIE ON this face (by bounding-box overlap, then the piece's centre of
    mass within TOL of the face) - the fallback when a cut piece carries a re-parameterised copy of the surface, so
    neither the face nor the surface signature can find it."""
    b = face.BoundBox
    share = {}
    ncand = 0
    for nm, lst in allpieces.items():
        rb = boxes.get(nm)
        if rb and (rb[0] > b.XMax + 2 or rb[1] < b.XMin - 2 or rb[2] > b.YMax + 2 or rb[3] < b.YMin - 2 or rb[4] > b.ZMax + 2 or rb[5] < b.ZMin - 2):
            continue                          # recorded
        for pc in lst:
            pb = pc.BoundBox
            if pb.XMin > b.XMax + 0.5 or pb.XMax < b.XMin - 0.5 or pb.YMin > b.YMax + 0.5 or pb.YMax < b.YMin - 0.5 \
                    or pb.ZMin > b.ZMax + 0.5 or pb.ZMax < b.ZMin - 0.5 or pc.Area > face.Area * 1.01:
                continue
            pt = _point_on(pc)
            if type(face.Surface).__name__ in ("Plane", "Cylinder", "Cone", "Sphere", "Toroid"):
                try:
                    u, v = face.Surface.parameter(pt)
                    if (face.Surface.value(u, v) - pt).Length > TOL:
                        continue
                except Exception:
                    pass
            try:
                ncand += 1
                d = face.distToShape(Part.Vertex(pt))[0]
            except Exception:
                continue
            if d <= TOL:
                share[nm] = share.get(nm, 0.0) + pc.Area
    covered = sum(share.values())
    say("  fallback: face %.0f mm2, %d candidate piece(s) tested, %.0f mm2 covered  (%.0f s)" % (face.Area, ncand, covered, time.time() - T0))
    rest = face.Area - covered
    if rest > max(1e-2 * face.Area, 0.05):
        share["_NEW_SURFACE"] = rest
    return share


allpieces = {}
for key, holders in bysurf.items():
    for nm, lst in holders.items():
        allpieces.setdefault(nm, []).extend(lst)

for fi, f in enumerate(faces):
    if fi and fi % 500 == 0:
        say("  ... %d of %d faces placed (%d identity, %d surface, %d cut, %d new)  %.0f s"
            % (fi, len(faces), report["identity"], report["surface"], report["cut"], report["new"], time.time() - T0))
    s = face_sig(f)
    if s in ident:
        assign[fi] = ident[s]; report["identity"] += 1
        continue
    holders = bysurf.get(surf_sig(f), {})
    if len(holders) == 1:
        assign[fi] = next(iter(holders)); report["surface"] += 1
        continue
    if holders:
        share = nearest_region_by_pieces(f, holders)
        report["cut"] += 1
    else:
        share = {}
    if not share or (share.get("_NEW_SURFACE", 0.0) > 0.5 * f.Area):
        share2 = pieces_on(f)
        if share2 and share2.get("_NEW_SURFACE", 0.0) < share.get("_NEW_SURFACE", f.Area):
            share = share2; report["cut"] += 1 if not holders else 0
    tot = sum(share.values())
    win = max(share, key=share.get) if share else "_NEW_SURFACE"
    if win == "_NEW_SURFACE":
        c = f.CenterOfMass
        home = [n for n in edited if boxes.get(n) and boxes[n][0] <= c.x <= boxes[n][1] and boxes[n][2] <= c.y <= boxes[n][3] and boxes[n][4] <= c.z <= boxes[n][5]]
        if home:
            win = home[0]
            report["moved"].append({"face": fi + 1, "to": win, "why": "new surface inside the box of a region a job edited"})
        else:
            report["new_faces"].append(fi + 1)
        report["new"] += 1
    if share and tot and share[win] / tot < 0.9 and len(share) > 1:
        report["mixed"].append({"face": fi + 1, "to": win, "share": {k: round(v / tot, 3) for k, v in share.items()}})
    assign[fi] = win
say("assigned: %d by identity, %d by surface, %d cut faces by nearest piece, %d new; %d mixed  (%.0f s)"
    % (report["identity"], report["surface"], report["cut"], report["new"], len(report["mixed"]), time.time() - T0))
if report["new"] > 0.5 * len(faces):
    say("REFUSED: %d of %d faces read as NEW SURFACE. A local edit changes a few faces; half the body being new means the\n"
        "  approved surfaces and this body do not correspond (wrong model, wrong atlas, or a tolerance far too tight)."
        % (report["new"], len(faces)))
    raise SystemExit(2)

man, regs_out = {}, {}
order = loaded + (["_NEW_SURFACE"] if "_NEW_SURFACE" in assign.values() else [])
for name in order:
    fids = [fi for fi, n in assign.items() if n == name]
    if not fids:
        say("  %-24s EMPTY on this body" % name); continue
    comp = Part.Compound([faces[fi] for fi in fids])
    p = os.path.join(OUT, name + ".brep"); comp.exportBrep(p)
    area = sum(faces[fi].Area for fi in fids)
    r = regions.get(name, {})
    man[name] = {"brep": p, "rgb": list(rgb.get(name, (255, 40, 200))), "pieces": len(fids), "area": area,
                 "from_faces": [fi + 1 for fi in fids],
                 "note": r.get("what_it_is", "surface no approved region has - the edit, or a re-split face")}
    regs_out[name] = {"rgb": man[name]["rgb"], "definition": r.get("definition_status", "NEW" if name == "_NEW_SURFACE" else "DRAFT"),
                      "edit": r.get("edit_status", "OPEN"), "note": man[name]["note"]}
    say("  %-24s %5d faces %9.0f mm2%s" % (name, len(fids), area, "   <- NEW SURFACE, not in any approved region" if name == "_NEW_SURFACE" else ""))
json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
json.dump(regs_out, open(os.path.join(OUT, "regions.json"), "w"), indent=1)
report["body"] = SHAPE; report["faces"] = len(faces); report["tol"] = TOL; report["secs"] = round(time.time() - T0)
json.dump(report, open(os.path.join(OUT, "transfer.json"), "w"), indent=1)
tot_area = sum(v["area"] for v in man.values()); body_area = sum(f.Area for f in faces)
say("total %.0f mm2 of %.0f (%.2f pct) - every face assigned once" % (tot_area, body_area, 100.0 * tot_area / max(body_area, 1e-9)))
if abs(tot_area - body_area) > 1e-3 * body_area:
    say("REFUSED: the regions' area does not add back up to the body's"); raise SystemExit(2)
say("DONE %.0f s" % (time.time() - T0))

# kit rebuild
# content.brep  ORIGINAL
# REBUILD_region.json
# recorded
# kit rebuild
import os, sys, json, time, Part, FreeCAD
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
def _fail(m): print(m if str(m).startswith("FAIL") else "FAIL: " + str(m), flush=True); raise SystemExit(1)
TAG = os.environ.get("LK_TAG", "")
V3 = FreeCAD.Vector; T0 = time.time()
BODY = os.environ.get("BODY") or _fail("BODY not set"); RUN = os.environ.get("RUN") or _fail("RUN not set"); os.makedirs(RUN, exist_ok=True)
WIN = [float(t) for t in (os.environ.get("WIN") or _fail("WIN not set")).split()]
planes = []
for spec in [p for p in os.environ.get("PLANES", "").split(";") if p.strip()]:
    v = [float(t) for t in spec.split()]; n = V3(*v[3:]); n.normalize(); planes.append((V3(*v[:3]), n))
b = Part.Shape(); b.importBrep(BODY)
if len(b.Solids) != 1:      # the skin route edits ONE solid
    _fail("FAIL: the skin route edits ONE solid - %s is a compound of %d solids: copy the solid to edit out first (`kit tool extract --set \"BOX=...\"` on a job made from it, then `kit newjob <J> --from <the extract>`), or run this job on that solid's own brep (31bw B4)" % (os.path.basename(BODY), len(b.Solids)))
body = b.Solids[0]
print("body %s: %d faces, %d solid(s) (%.0fs)" % (os.path.basename(BODY), len(body.Faces), len(b.Solids), time.time() - T0), flush=True)
region = Part.makeBox(WIN[1] - WIN[0], WIN[3] - WIN[2], WIN[5] - WIN[4], V3(WIN[0], WIN[2], WIN[4]))
for c, n in planes:
    region = region.cut(Part.Plane(c, n).toShape(-400, 400, -400, 400).extrude(n * 400))
content = body.common(region)
sols = sorted(content.Solids, key=lambda s: -s.Volume)
print("region %.1f mm3; content %.1f mm3 in %d solid(s): %s (%.0fs)" % (region.Volume, content.Volume, len(sols), [round(s.Volume, 1) for s in sols[:6]], time.time() - T0), flush=True)
region.exportBrep(os.path.join(RUN, "window_solid.brep")); content.exportBrep(os.path.join(RUN, "content.brep"))
stale = [f for f in ("state.json", "cells_split.brep", "cells_seq.brep", "cells_seq.json", "cells_seq_done.json", "cells.json", "cells.brep", "cells_meta_partial.json", "arr_base.stl", "arr_shell_solid.brep", "arr_unified.brep",
                     "keep_region.brep", "keep_bins.npz", "REBUILD_keep.json", "keep_frozen.json", "_region_used.brep", "_local_res.bin", "_reinsert_state.json") if os.path.isfile(os.path.join(RUN, f))]
for f in stale:
    try: os.replace(os.path.join(RUN, f), os.path.join(RUN, f + ".stale"))
    except OSError: pass
if stale: print("previous arrangement files renamed .stale (a new edit region): %s" % ", ".join(stale), flush=True)
walls = []
for ax in range(3):
    for wv, sgn in ((WIN[2 * ax], -1), (WIN[2 * ax + 1], 1)):
        touch = any(abs([f.BoundBox.XMin, f.BoundBox.YMin, f.BoundBox.ZMin][ax] - wv) < 1e-4 and abs([f.BoundBox.XMax, f.BoundBox.YMax, f.BoundBox.ZMax][ax] - wv) < 1e-4 for f in content.Faces)
        if touch:
            c = [0.0, 0.0, 0.0]; c[ax] = wv; nn = [0.0, 0.0, 0.0]; nn[ax] = float(sgn); walls.append(c + nn)
for c, n in planes: walls.append([c.x, c.y, c.z, n.x, n.y, n.z])
json.dump(walls, open(os.path.join(RUN, "walls.json"), "w"))
warn = []
for c in walls:
    n = V3(*c[3:])
    for f in content.Faces:
        try: fn = f.normalAt(*f.Surface.parameter(f.CenterOfMass))
        except Exception: continue
        q = f.CenterOfMass; dc = abs((q - V3(*c[:3])).dot(n))
        if dc < 1e-3: continue
        if abs(fn.dot(n)) > 0.94 and f.distToShape(Part.Plane(V3(*c[:3]), n).toShape(-400, 400, -400, 400))[0] < 0.05 and f.Area > 5: warn.append((c[:3], round(f.Area, 1)))
if warn:
    print("WARNING: %d content face(s) over 5 mm2 lie within 20 deg of a cut plane and touch it - that plane grazes a skin; expect a sub-voxel wedge at the seam (move the plane if you can): %s" % (len(warn), warn[:4]), flush=True)
    graze_refused = not os.environ.get("GRAZE_OK", "").strip()
    if not graze_refused: print("GRAZE_OK: building on a grazing wall anyway - %s" % os.environ["GRAZE_OK"].strip(), flush=True)
else:
    graze_refused = False
bb = content.BoundBox; big = Part.makeBox(bb.XLength + 16, bb.YLength + 16, bb.ZLength + 16, V3(bb.XMin - 8, bb.YMin - 8, bb.ZMin - 8)); loc = body.common(big)
coinc = []; sections = []
for c in walls:
    n = V3(*c[3:]); cc = V3(*c[:3]); a_sec = 0.0; a_air = 0.0
    for f in content.Faces:
        if type(f.Surface).__name__ != "Plane": continue
        try: fn = f.normalAt(*f.Surface.parameter(f.CenterOfMass))
        except Exception: continue
        if abs((f.CenterOfMass - cc).dot(n)) > 1e-3 or abs(abs(fn.dot(n)) - 1) > 1e-4: continue
        vs, ts = f.tessellate(0.5)
        for t in ts:
            p0, p1, p2 = vs[t[0]], vs[t[1]], vs[t[2]]; area = (p1 - p0).cross(p2 - p0).Length / 2.0; ce = (p0 + p1 + p2) * (1.0 / 3.0) + n * 0.05
            if any(s.isInside(ce, 1e-6, True) for s in loc.Solids): a_sec += area
            else: a_air += area
    sections.append(round(a_sec, 1))
    if a_air > 1.0: coinc.append((c[:3], round(a_air, 1)))
    print("wall n=(%.2f %.2f %.2f): section %.1f mm2%s" % (n.x, n.y, n.z, a_sec, ("; DESIGN FACE IN THE PLANE %.1f mm2 (air beyond)" % a_air) if a_air > 1.0 else ""), flush=True)
if coinc: print("WARNING: a design face lies in a cut plane (%s): the piece will carry a CLIP_OUT lip over it - move that plane by at least 1 mm" % coinc, flush=True)
A_SMALL = float(os.environ.get("A_SMALL", "1.0")); SURF_MAX = int(os.environ.get("SURF_MAX", "30"))
big = [f for f in sols[0].Faces if f.Area >= A_SMALL] if sols else []
keys = set(); ncurved = 0
for f in big:
    if type(f.Surface).__name__ == "Plane":
        n = f.normalAt(*f.Surface.parameter(f.CenterOfMass)); c = f.CenterOfMass
        if n.z < 0 or (n.z == 0 and (n.y < 0 or (n.y == 0 and n.x < 0))): n = -n
        keys.add((round(n.x, 1), round(n.y, 1), round(n.z, 1), round(c.dot(n) / 0.5)))
    else: ncurved += 1
nsurf = len(keys) + ncurved
if os.environ.get("SHELVED_OK"):
    print("design surfaces: %d (%d planes after merging coplanar ones, %d curved) among %d faces of the content's main solid over %g mm2 - the sequential split (the default) applies them one at a time: planes ~0 s each, a curved one 3-425 s (a section: 47-52 tools, 33-40 min over 11-12 calls)%s"
          % (nsurf, len(keys), ncurved, len(big), A_SMALL, "; over ~%d the one-fuse form (SPLIT=single) fails - never use it here; an edit region this busy may be split in two (local boxes that do not overlap)" % SURF_MAX if nsurf > SURF_MAX else ""), flush=True)
else: print("design surfaces: %d (%d planes after merging coplanar ones, %d curved) among %d faces of the content's main solid" % (nsurf, len(keys), ncurved, len(big)), flush=True)
try:
    sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R; import numpy as np
    od = os.path.join(RUN, "review"); os.makedirs(od, exist_ok=True)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sk_lib as K
    _cp = os.path.join(RUN, "content.brep")
    V, T, FID, MQc = K.piece_mesh(_cp if os.path.isfile(_cp) else None, content, cache_dir=od, say=lambda m_: print(m_, flush=True)); V = np.asarray(V, float); T = np.asarray(T, int); FID = np.asarray(FID, int)
    C = np.full((len(T), 3), (0.95, 0.6, 0.2)); _bb = content.BoundBox; _fb = (_bb.XMin, _bb.XMax, _bb.YMin, _bb.YMax, _bb.ZMin, _bb.ZMax)
    ttl = "PRE-FLIGHT: the edit region's content, %d solid(s) %.0f mm3, %d design surfaces%s, %d wall(s)%s" % (len(sols), content.Volume, nsurf, (" (limit ~%d)" % SURF_MAX) if os.environ.get("SHELVED_OK") else "", len(walls), ", GRAZING" if warn else "")
    for nm, d in {"iso": R.look(fwd=0.6, left=-0.5, up=-0.6), "above": R.look(up=-1.0)}.items():
        K.view_meshes(R, os.path.join(od, "preflight_%s.png" % nm), [(V, T, FID, MQc, C)], d, _fb, 1200, "pre-flight %s" % nm, ttl, ["The content opaque, smooth-shaded within each face; a red RENDER DEFECTIVE banner across the frame = NO EVIDENCE."])
        print("pre-flight pictures: %s (preflight_iso.png, preflight_above.png) - OPEN THEM before building" % od, flush=True)
except Exception as ex:
    print("pre-flight picture not made (%s)" % str(ex)[:80], flush=True)
cut_frames = []
try:
    import numpy as np, hashlib
    sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
    od = os.path.join(RUN, "review"); os.makedirs(od, exist_ok=True)
    hs_ = [(np.array(w[:3], float), np.array(w[3:], float) / max(np.linalg.norm(w[3:]), 1e-12)) for w in walls]
    hs_ += [(np.array([WIN[0], 0, 0]), np.array([-1.0, 0, 0])), (np.array([WIN[1], 0, 0]), np.array([1.0, 0, 0])), (np.array([0, WIN[2], 0]), np.array([0, -1.0, 0])),
            (np.array([0, WIN[3], 0]), np.array([0, 1.0, 0])), (np.array([0, 0, WIN[4]]), np.array([0, 0, -1.0])), (np.array([0, 0, WIN[5]]), np.array([0, 0, 1.0]))]
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sk_lib as K
    VL, TL, FL, MQl = K.piece_mesh(None, loc, cache_dir=od, say=lambda m_: print(m_, flush=True)); VL = np.asarray(VL, float); TL = np.asarray(TL, int); FL = np.asarray(FL, int)
    VL0, TL0 = VL, TL
    VL, TL, FL = K.mesh_outside_region(R, VL, TL, FL, hs_)
    MQl = K.cut_quality(MQl, VL0, TL0, VL, TL, FL, hs_)
    print("the body round the edit region, cut on the walls: %d triangles, open edges %d (%d expected - on a wall plane or the body's rim), %d crack(s) of the cut%s" % (len(TL), MQl["open_edges"], MQl["expected_open"], MQl.get("cut_cracks", 0), " - RENDER DEFECTIVE" if MQl.get("cut_cracks") else ""), flush=True)
    _cp = os.path.join(RUN, "content.brep")
    VC, TC, FC, MQc = K.piece_mesh(_cp if os.path.isfile(_cp) else None, content, cache_dir=od, say=lambda m_: print(m_, flush=True)); VC = np.asarray(VC, float); TC = np.asarray(TC, int); FC = np.asarray(FC, int)
    onw_list = []
    for w in walls:
        c_ = np.array(w[:3], float); n_ = np.array(w[3:], float); n_ /= max(np.linalg.norm(n_), 1e-12)
        onw_list.append(np.all(np.abs((VC[TC] - c_) @ n_) < 1e-3, axis=1))
    onw = np.any(onw_list, axis=0) if onw_list else np.zeros(len(TC), bool)
    CC_ = np.full((len(TC), 3), (0.95, 0.6, 0.2)); CC_[onw] = (0.92, 0.12, 0.12)
    meshes_fit = [(VL, TL, FL, MQl, (0.55, 0.57, 0.62)), (VC, TC, FC, MQc, (0.95, 0.6, 0.2), 0.05)]; QREC = {}
    meshes_cut = [(VC, TC, FC, MQc, CC_)]                                                            # the content ALONE
    ttl = "THE EDIT REGION'S CUTS - the content ALONE: RED = the body's section on a wall (where that wall cuts the body: judge every red face - it crosses skins and lands in thick material; never along a skin, through a thin lip or rib, or through the feature being fixed; where a wall passes through air there is no red), orange = the content's own skins%s" % (" - GRAZING WARNED" if warn else "")
    ttl_fit = "THE CONTENT IN ITS PLACE: grey = the body round the edit region (cut exactly on the walls), orange = the content filling the hole - the lines where orange meets grey ARE the walls; the cut faces themselves are covered here (see region_cuts_*)"
    views = {}
    for k_, w in enumerate(walls):
        n_ = np.array(w[3:], float); n_ /= max(np.linalg.norm(n_), 1e-12); views["wall%d" % k_] = -n_
    views["iso_fore"] = R.look(fwd=0.8, left=-0.5, up=-0.5); views["iso_aft_below"] = R.look(fwd=-0.7, left=0.5, up=0.6)
    foc = np.array([[x, y, z] for x in (WIN[0] - 3, WIN[1] + 3) for y in (WIN[2] - 3, WIN[3] + 3) for z in (WIN[4] - 3, WIN[5] + 3)], float)
    fbc = K.fbox_of(foc); MQ2 = K.merge_quality([MQl, MQc])
    for nm, d in views.items():
        pth = os.path.join(od, "region_cuts_%s.png" % nm)
        if nm.startswith("wall"):
            k_w = int(nm[4:]); w = walls[k_w]
            hd = "CUTS %s FACE-ON (its outward normal (%.2f %.2f %.2f) through (%.1f %.1f %.1f)) - the content ALONE: RED = THIS wall's section (where it cuts the body: judge it - it crosses skins and lands in thick material; never along a skin, through a thin lip or rib, or through the feature being fixed; through air there is no red), DULL = the other walls' sections (each judged in its own frame), orange = the content's own skins%s" % (nm, w[3], w[4], w[5], w[0], w[1], w[2], " - GRAZING WARNED" if warn else "")
            C_k = np.full((len(TC), 3), (0.95, 0.6, 0.2)); C_k[onw] = (0.55, 0.42, 0.42); C_k[onw_list[k_w]] = (0.92, 0.12, 0.12); parts = [(VC, TC, FC, MQc, C_k)]
            lg = "The content alone, face-on to %s: RED = THIS wall's section (the body's cut on it - judge it here), DULL = the other walls' sections (each judged in its own frame; a wall edge-on here shows only as the outline), orange = its skins; a red RENDER DEFECTIVE banner across the frame = NO EVIDENCE." % nm
        else:
            hd = "CUTS %s: %s" % (nm, ttl); lg = "The content alone, opaque: RED = its faces in a wall plane (the body's section there - the cut), orange = its skins; smooth-shaded within each face; a red RENDER DEFECTIVE banner across the frame = NO EVIDENCE."; parts = meshes_cut
        K.view_meshes(R, pth, parts, d, fbc, 1300, "CUTS %s" % nm, hd, [lg])
        cut_frames.append(os.path.basename(pth)); QREC[os.path.basename(pth)] = {k_: v for k_, v in K.frame_quality(MQc, fbc).items() if k_ != "crack_pts_in_frame"}
    for nm in ("iso_fore", "iso_aft_below"):
        pth = os.path.join(od, "region_fit_%s.png" % nm)
        K.view_meshes(R, pth, meshes_fit, views[nm], fbc, 1300, "FIT %s" % nm, "FIT %s: %s" % (nm, ttl_fit), ["Grey = the body round the edit region, cut on the walls; orange = the content in its place; smooth-shaded within each face; a red RENDER DEFECTIVE banner across the frame = NO EVIDENCE."])
        cut_frames.append(os.path.basename(pth)); QREC[os.path.basename(pth)] = {k_: v for k_, v in K.frame_quality(MQ2, fbc).items() if k_ != "crack_pts_in_frame"}
    json.dump({"tag": TAG, "content_md5": hashlib.md5(open(os.path.join(RUN, "content.brep"), "rb").read()).hexdigest(), "frames": cut_frames, "walls": walls, "grazing": warn,
               "frame_info": {k_: {"quality": q_} for k_, q_ in QREC.items()},
               "mesh_quality": {k_: MQ2.get(k_) for k_ in ("tris", "dev_mm", "ang_rad", "open_edges", "seams", "cracks", "gap_max_mm", "dev_p99_mm", "nang_p99_deg", "defective_mesh", "why_mesh", "defective", "why", "how", "parts")}},
              open(os.path.join(od, "CUTS_REGION.json"), "w"), indent=1)
    if any(q_.get("defective") for q_ in QREC.values()): print("RENDER DEFECTIVE: %d of %d cut frame(s) stamped - NO EVIDENCE; the judge refuses the set" % (sum(1 for q_ in QREC.values() if q_.get("defective")), len(QREC)), flush=True)
    print("THE ORBIT OF THE CUTS: %d frame(s) - review\\region_cuts_*.png (the content alone, its section faces RED = the cuts: one frame FACE-ON to each wall + two isos) and review\\region_fit_*.png (in its place in the body) - OPEN EVERY ONE and judge every red face; a wall in the wrong place is moved (WIN / PLANES) and the region run again; then `kit rebuild judge --job <J> --what region --verdict ok --note \"<what the frames show>\"` - kit rebuild skin-source and the reinsert's STEP 1 refuse without it" % len(cut_frames), flush=True)
except Exception as ex:
    print("the orbit of the cuts NOT made (%s) - the arrangement will refuse until it exists: run the region again" % str(ex)[:120], flush=True)
json.dump({"tag": TAG, "body": BODY, "window": WIN, "planes": [[c.x, c.y, c.z, n.x, n.y, n.z] for c, n in planes], "walls": walls, "content_mm3": round(content.Volume, 1), "content_solids": [round(s.Volume, 1) for s in sols], "grazing_faces": warn, "graze_ok": os.environ.get("GRAZE_OK", "").strip() or None, "wall_sections_mm2": sections, "design_faces_in_planes": coinc,
           "design_surfaces": nsurf, "surf_max": SURF_MAX, "cut_frames": cut_frames,
           "protect": [[float(v) for v in bx.split()] for bx in os.environ.get("PROTECT", "").split(";") if len(bx.split()) == 6]}, open(os.path.join(RUN, "REBUILD_region.json"), "w"), indent=1)
print("REGION -> %s: window_solid.brep, content.brep, walls.json (%d walls), REBUILD_region.json (%.0fs)" % (RUN, len(walls), time.time() - T0), flush=True)
if graze_refused:
    print("FAIL: a cut plane grazes a design skin (the WARNING above; the record is written). Move that wall - an edit region's walls cross skins, they do not run along them - or pass GRAZE_OK=\"<why this wall must stay>\" to build on it anyway (the reason goes into the record).", flush=True); raise SystemExit(1)

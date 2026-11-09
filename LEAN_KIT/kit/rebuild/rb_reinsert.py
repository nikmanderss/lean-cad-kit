# kit rebuild
# kit rebuild
# raw fuse
# recorded
# over the
import os, sys, json, time, collections, re, math, numpy as np, Part, FreeCAD
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
def _fail(m): print(m if str(m).startswith("FAIL") else "FAIL: " + str(m), flush=True); raise SystemExit(1)
TAG = os.environ.get("LK_TAG", "")   # kit rebuild
sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from _busy import busy
# kit rebuild  raw fuse
V3 = FreeCAD.Vector; T0 = time.time(); STEP = os.environ.get("STEP", "1"); RUN = os.environ["RUN"]
G = float(os.environ.get("G", "3.0")); SHRINK = float(os.environ.get("SHRINK", "2.0")); CLIP_OUT = float(os.environ.get("CLIP_OUT", "0.1")); MIN_KEEP = float(os.environ.get("MIN_KEEP", "10.0"))
PL = json.load(open(os.environ.get("WALLS", os.path.join(RUN, "walls.json")))); planes = [(np.array(p[:3], float), np.array(p[3:], float) / np.linalg.norm(p[3:])) for p in PL]
def P(p): return os.path.join(RUN, p)
def say(*a): print("%5.0fs " % (time.time() - T0), *a, flush=True)
def need(*names):
    """the files an earlier STEP left; a missing one is said by name (an importBinary on a missing file is an 'Unknown C++ exception')"""
    for nm in names:
        if not os.path.isfile(P(nm)): _fail("FAIL: %s is missing from %s - it is written by STEP %s%s; run that STEP first" % (nm, RUN, {"_local.bin": 1, "_rest.bin": 1, "_localbox.brep": 1, "_local_res.bin": 2, "_reinsert_state.json": 2, "body_new.brep": 3}.get(nm, "?"), " (a TRIAL's STEP 3 writes it too and the runner keeps the trial's as body_trial.brep after its STEP 4 - 31bx R6 F11)" if nm == "body_new.brep" else ""))
def on_plane(f, c, n, tol=1e-3):
    if type(f.Surface).__name__ != "Plane": return False
    q = f.CenterOfMass; q = np.array([q.x, q.y, q.z]); nn = f.normalAt(*f.Surface.parameter(f.CenterOfMass)); nn = np.array([nn.x, nn.y, nn.z])
    return abs((q - c) @ n) < tol and abs(abs(nn @ n) - 1) < 1e-4
def plane_of(f):
    """(point, unit normal) of a planar face, or None"""
    if type(f.Surface).__name__ != "Plane": return None
    q = f.CenterOfMass; nn = f.normalAt(*f.Surface.parameter(q))
    n = np.array([nn.x, nn.y, nn.z]); return np.array([q.x, q.y, q.z]), n / max(np.linalg.norm(n), 1e-12)
def width_of(f):
    """the width a face can hold: 2A/P (a strip of width w and length L: 2wL/2(w+L) -> w for L >> w)"""
    per = sum(e.Length for e in f.Edges); return 2.0 * f.Area / max(per, 1e-9)
_BOP_KINDS = ("InvalidCurveOnSurface", "SelfIntersect", "SelfIntersectingWire", "BadOrientation", "BadOrientationOfSubshape", "NotClosed", "GeomAbs_C0", "UnorientableShape",
              "FreeEdge", "InvalidToleranceValue", "IntersectingWires", "NotConnected", "InvalidSameParameterFlag", "InvalidSameRangeFlag", "InvalidDegeneratedFlag",
              "TooSmallEdge", "NonRecoverableFace", "IncompatibilityOfVertex", "IncompatibilityOfEdge", "IncompatibilityOfFace", "InvalidPointOnCurve",
              "InvalidPointOnCurveOnSurface", "InvalidPointOnSurface", "No3DCurve", "Multiple3DCurve", "Invalid3DCurve", "NoCurveOnSurface",
              "InvalidCurveOnClosedSurface", "InvalidMultiConnexity", "InvalidRange", "EmptyWire", "RedundantEdge", "NoSurface", "InvalidWire", "RedundantWire",
              "InvalidImbricationOfWires", "EmptyShell", "RedundantFace", "InvalidImbricationOfShells", "SubshapeNotInShape", "InvalidPolygonOnTriangulation",
              "EnclosedRegion", "CheckFail", "OperationAborted", "NotValid", "BadType")
_BOP_NORM = {re.sub(r"[\s\-_]", "", k).lower(): k for k in _BOP_KINDS}
def bop_kind(line):
    """31bq B07 (2): the KIND a check(True) line names, as FreeCAD 1.1 writes it - the BOP checker ("Error in Face: BOPAlgo SelfIntersect") and the BRep checker
    ("Self-intersecting wire", "Unorientable shape", "Invalid curve on surface", "No error") - matched with spaces, hyphens and case removed; a line no kind matches
    is kept as its own kind (`Other: <the line>`), so a failing check is NEVER an empty record (the first form matched CamelCase names only - the BRep checker's
    lines fell through, kinds came back {} and {} <= cosmetics passed anything)"""
    s = line.strip()
    if not s or s.lower().startswith("bop check found"): return None
    s2 = re.sub(r"^error in \w+\s*:\s*", "", s, flags=re.I); s2 = re.sub(r"^bopalgo\s+", "", s2, flags=re.I)
    key = re.sub(r"[\s\-_]", "", s2).lower()
    if key in _BOP_NORM: return _BOP_NORM[key]
    for k_ in _BOP_NORM:
        if k_ in key: return _BOP_NORM[k_]
    if key == "noerror": return "CheckFailedNoDetail"
    return "Other: %s" % s[:60]
def bop_report(s):
    """check(True) on one solid: (ok, {kind: count}, first line) - the kinds by bop_kind (B07 (2))"""
    try:
        s.check(True); return True, {}, ""
    except Exception as ex:
        lines = [l for l in str(ex).splitlines() if l.strip()]; kinds = collections.Counter()
        for l in lines:
            k_ = bop_kind(l)
            if k_: kinds[k_] += 1
        if not kinds: kinds["Other: %s" % (lines[0][:60] if lines else str(ex)[:60])] = 1
        return False, dict(kinds), (lines[1] if len(lines) > 1 else (lines[0] if lines else str(ex)[:80]))
def seam_census(shape, region, bb, old=None, tol=1e-3):
    """faces of `shape` (inside bb) lying ON a planar face of `region` - the seam: a step or a lip, never a merged contact.
    Faces the OLD shape already had there (a design face in the plane) are subtracted. Returns (n, area, widest, rows)."""
    rfaces = [(f, plane_of(f)) for f in region.Faces if plane_of(f) is not None]
    def onregion(f):
        pf = plane_of(f)
        if pf is None or not bb.isInside(f.CenterOfMass): return None
        q, n = pf
        for rf, (c, rn) in rfaces:
            if abs((q - c) @ rn) < tol and abs(abs(n @ rn) - 1) < 1e-4 and rf.distToShape(Part.Vertex(f.CenterOfMass))[0] < tol: return rf
        return None
    oldk = set()
    if old is not None:
        for s in old.Solids:
            for f in s.Faces:
                if onregion(f) is not None: oldk.add((round(f.CenterOfMass.x, 3), round(f.CenterOfMass.y, 3), round(f.CenterOfMass.z, 3), round(f.Area, 3)))
    rows = []
    for f in shape.Faces:
        rf = onregion(f)
        if rf is None: continue
        key = (round(f.CenterOfMass.x, 3), round(f.CenterOfMass.y, 3), round(f.CenterOfMass.z, 3), round(f.Area, 3))
        if key in oldk: continue
        c, n = plane_of(f); rows.append((width_of(f), f.Area, [round(float(v), 2) for v in n], [round(float(v), 1) for v in c]))
    rows.sort(key=lambda r: -r[0])
    seam_census.faces = [f for f in shape.Faces if onregion(f) is not None and (round(f.CenterOfMass.x, 3), round(f.CenterOfMass.y, 3), round(f.CenterOfMass.z, 3), round(f.Area, 3)) not in oldk]
    return len(rows), sum(r[1] for r in rows), (rows[0][0] if rows else 0.0), rows
def load_protect():
    """the PROTECT boxes: the lever, else what the keep step used (REBUILD_keep.json), else what the blend ran with, else the region's record (31bq R7d (A3)); the
    record they came from is load_protect.source. R7W tester-findings (T4 4.5): PROTECT set EMPTY (or blank) is UNSET - only None had fallen back, so PROTECT=''
    checked 0 boxes and STEP 4 said CHECK PASS on fill15's body whose PROTECT voids change +28.1 / +18.4 %; and the CHECK line never said where its boxes came from"""
    pr = os.environ.get("PROTECT"); load_protect.source = "the lever PROTECT"
    if pr is not None and not pr.strip():
        say("PROTECT is set EMPTY (%r) - read as UNSET: the boxes come from the job's records (an empty lever is never 'no box'; R7W tester-findings)" % pr); pr = None
    if pr is None:
        load_protect.source = "none - the lever unset and no record of the job (REBUILD_keep.json / REBUILD_blend.json / REBUILD_region.json) holds a box"
        for rec, key, who in (("REBUILD_keep.json", "protect", "the keep's"), ("REBUILD_blend.json", "protect", "the blend's"), ("REBUILD_region.json", "protect", "the region's")):
            try:
                v = json.load(open(P(rec))).get(key) or []
                boxes = [x["box"] if isinstance(x, dict) else x for x in v]
                if boxes: pr = ";".join(" ".join("%g" % float(t) for t in b) for b in boxes); load_protect.source = "%s record %s" % (who, rec); break
            except (OSError, ValueError, KeyError, TypeError, AttributeError): continue      # unreadable
        if pr is None: pr = ""
    boxes = [[float(v) for v in b.split()] for b in pr.split(";") if b.strip()]
    for b in boxes:
        if len(b) != 6: _fail("FAIL: PROTECT box needs six numbers x0 x1 y0 y1 z0 z1, got %r" % b)
    return boxes
load_protect.source = None
def shrunk_window(region, rung):
    shr = region
    for (c, n) in planes:
        shr = shr.cut(Part.Plane(V3(*(c - n * rung)), V3(*n)).toShape(-400, 400, -400, 400).extrude(V3(*(n * 400))))
    return shr

def _same_piece(step):
    """31bq R7W route-end D1: STEP 3 / 4 continue the STEP 2 that sewed THIS piece. The local result on disk (_local_res.bin, _reinsert_state.json) is
    the LAST STEP 2's; a STEP 2 refused or never run for this piece left another piece's there (route-end 2026-10-22: a refused trial STEP 2, then STEP 3
    sewed a 10-20 scratch run's fill14 state into the body). Refused by name: no piece_md5, another piece's md5, another run's id."""
    import hashlib
    need("_reinsert_state.json")
    try: st_ = json.load(open(P("_reinsert_state.json")))
    except (OSError, ValueError) as ex: _fail("FAIL: STEP %s - _reinsert_state.json cannot be read (%s) - run STEP 2 again" % (step, ex))
    pc_ = os.environ.get("PIECE", P("piece.brep"))
    try: pm_ = hashlib.md5(open(pc_, "rb").read()).hexdigest()
    except OSError as ex: _fail("FAIL: STEP %s - the piece %s cannot be read to tie the local result to it (%s)" % (step, pc_, ex))
    sm_ = st_.get("piece_md5")
    if not sm_: _fail("FAIL: STEP %s REFUSED - the local result on disk (_reinsert_state.json) names no piece (no piece_md5 - a STEP 2 of an older kit, or a copy from another job): it is not shown to be THIS piece's sew. Run STEP 2 for this piece first (31bq R7W D1)" % step)
    if sm_ != pm_: _fail("FAIL: STEP %s REFUSED - the local result on disk was sewn from ANOTHER piece (_reinsert_state.json piece_md5 %s; %s now %s): a STEP 2 refused or never run for this piece left it. Run STEP 2 for this piece first (31bq R7W D1)" % (step, sm_[:8], os.path.basename(pc_), pm_[:8]))
    rid_ = (os.environ.get("LK_RUN_ID") or "").strip()
    if rid_ and st_.get("run_id") != rid_: _fail("FAIL: STEP %s REFUSED - the local result on disk is from STEP 2 run %s, not run %s that this trial started (31bq R7W D1)" % (step, st_.get("run_id") or "(none)", rid_))
    return st_

if STEP == "1":
    b = Part.Shape(); b.importBrep(os.environ["BODY"]); body = b.Solids[0]
    rg = Part.Shape(); rg.importBrep(P("window_solid.brep")); region = rg.Solids[0]; bb = region.BoundBox
    _lo = [bb.XMin - G, bb.YMin - G, bb.ZMin - G]; _hi = [bb.XMax + G, bb.YMax + G, bb.ZMax + G]; _mv = []
    for _f in body.Faces:
        if type(_f.Surface).__name__ != "Plane": continue
        _fb = _f.BoundBox; _ext = [(_fb.XMin, _fb.XMax), (_fb.YMin, _fb.YMax), (_fb.ZMin, _fb.ZMax)]
        for _ax in range(3):
            if _ext[_ax][1] - _ext[_ax][0] > 1e-4: continue
            _v = _ext[_ax][0]
            for _side, _arr in ((0, _lo), (1, _hi)):
                if abs(_arr[_ax] - _v) < 0.05:
                    _arr[_ax] = (_v - 0.5) if _side == 0 else (_v + 0.5); _mv.append("%s%s %.2f -> %.2f" % ("-+"[_side], "xyz"[_ax], _v, _arr[_ax]))
    if _mv: say("local box: %d plane(s) lay on a body face and moved 0.5 mm outward (%s) - a box plane on a body face leaves the ring sew open (31bx R6 F8)" % (len(_mv), "; ".join(_mv)))
    box = Part.makeBox(_hi[0] - _lo[0], _hi[1] - _lo[1], _hi[2] - _lo[2], V3(_lo[0], _lo[1], _lo[2]))
    with busy("reinsert STEP 1: body.common(box) and body.cut(box) on the body of record", 900): local = body.common(box); rest = body.cut(box)
    try:
        dv = body.Volume - local.Volume - rest.Volume
        if abs(dv) > 1.0: say("NOTE: Part.Volume reads body - local - rest = %+.2f mm3 (K-LOCALBOOL) - on a self-intersecting body Part.Volume is not a ruler (L85, 11,000 mm3 off on R31); STEP 3's sew across the box faces and STEP 4's census are the checks that count" % dv)
    except Exception: pass
    print("local: %d solid(s) %d faces %.0f mm3, shells per solid %s | rest: valid %s %d solid(s) %d faces (%.0fs)" % (len(local.Solids), len(local.Faces), local.Volume, [len(s.Shells) for s in local.Solids], rest.isValid(), len(rest.Solids), len(rest.Faces), time.time() - T0), flush=True)
    local.exportBinary(P("_local.bin")); rest.exportBinary(P("_rest.bin")); box.exportBrep(P("_localbox.brep"))
    try:
        def mvol(sh):
            V, T, _ = R.tess_shape(sh, dev=0.1); V = np.asarray(V, float); T = np.asarray(T, int)
            return abs(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum() / 6.0)
        vols = {"body_mesh_mm3": round(mvol(body), 1), "local_mesh_mm3": round(mvol(local), 1)}
        json.dump(vols, open(P("_reinsert_vols.json"), "w")); say("mesh volumes: body %.1f, local %.1f mm3 (the ruler for STEP 3)" % (vols["body_mesh_mm3"], vols["local_mesh_mm3"]))
    except Exception as ex:
        say("mesh volumes not taken (%s)" % str(ex)[:80])
    try:
        ct = Part.Shape(); ct.importBrep(P("content.brep")); caps = [f for so in ct.Solids for f in so.Faces if any(on_plane(f, c, n) for c, n in planes)]
        if caps: Part.makeCompound(caps).exportBrep(P("wall_caps.brep")); print("wall_caps.brep: %d face(s) of the body's own section on the wall planes, %.1f mm2 - a finishing-pass piece builds its caps FROM these (JOIN=sew)" % (len(caps), sum(f.Area for f in caps)), flush=True)
    except Exception as ex:
        print("wall_caps.brep not written (%s)" % str(ex)[:80], flush=True)
    print("saved", flush=True)

elif STEP == "2":
    need("_local.bin", "_localbox.brep")
    lo = Part.Shape(); lo.importBinary(P("_local.bin")); local = lo
    rg = Part.Shape(); rg.importBrep(P("window_solid.brep")); window = rg.Solids[0]
    bx = Part.Shape(); bx.importBrep(P("_localbox.brep")); bb = bx.BoundBox
    pc = Part.Shape(); pc.importBrep(os.environ.get("PIECE", P("piece.brep"))); pieces = sorted([s for s in pc.Solids if abs(s.Volume) >= 0.5], key=lambda s: -abs(s.Volume))
    if not pieces: _fail("FAIL: the piece holds no solid over 0.5 mm3")
    ct = Part.Shape(); ct.importBrep(P("content.brep")); csols = sorted(ct.Solids, key=lambda s: -s.Volume); cmain = csols[0]; leftovers = csols[1:]
    # ORIGINAL
    IN_CONTENT = float(os.environ.get("IN_CONTENT", "0.9")); dropped_c = []
    if len(pieces) > 1:
        keep = [pieces[0]]
        for s in pieces[1:]:
            try:
                fr = s.common(cmain).Volume / s.Volume
            except Exception as ex:
                fr = -1.0; print("  component %.2f mm3: the containment test threw (%s) - dropped" % (s.Volume, str(ex)[:60]), flush=True)
            if fr >= IN_CONTENT:
                keep.append(s); print("  component %.2f mm3: %.0f %% inside the original - kept" % (s.Volume, 100 * fr), flush=True)
            else:
                dropped_c.append({"mm3": round(s.Volume, 2), "inside": round(max(fr, 0.0), 3)}); print("  component %.2f mm3: only %.0f %% inside the original - DROPPED (material the original does not have)" % (s.Volume, 100 * max(fr, 0.0)), flush=True)
        pieces = keep
    bop = []
    for i, s in enumerate(pieces):
        t1 = time.time(); ok, kinds, first = bop_report(s)
        tolE = max((e.Tolerance for e in s.Edges), default=0.0); tolV = max((v.Tolerance for v in s.Vertexes), default=0.0)
        bop.append({"solid": i, "mm3": round(s.Volume, 1), "faces": len(s.Faces), "check_true": ok, "kinds": kinds, "max_edge_tol": round(tolE, 4), "max_vertex_tol": round(tolV, 4)})
        say("piece solid %d: %.1f mm3, %d faces, max edge tol %.3g, max vertex tol %.3g, check(True) %s%s (%.1fs)" % (i, s.Volume, len(s.Faces), tolE, tolV, "OK" if ok else "FAILED", "" if ok else " - %s" % kinds, time.time() - t1))
    bad = [b for b in bop if not b["check_true"]]
    BOP_OK = os.environ.get("BOP_OK", "").strip()
    _COSMETIC = {"InvalidCurveOnSurface", "InvalidSameParameterFlag", "InvalidSameRangeFlag", "InvalidToleranceValue", "TooSmallEdge"}
    GAP_TOL = 0.02
    _GAPKINDS = {"InvalidCurveOnSurface", "InvalidSameParameterFlag", "InvalidSameRangeFlag", "InvalidToleranceValue"}
    _si_ok = False; _rec_ok = False; _gap_ = float("inf"); _rec_why = []; _why_ = []; PIECE_MD5 = None; _tse_ok_ = False; _tse_noncap_ = []; _tse_ = []; _tse_pass_f_ = []; _mic_ = {}
    _kinds_all = set(k_ for b in bad for k_ in (b.get("kinds") or {}))
    try:
        import hashlib as _hl
        _pc_ = os.environ.get("PIECE", P("piece.brep"))
        try: PIECE_MD5 = _hl.md5(open(_pc_, "rb").read()).hexdigest() if os.path.isfile(_pc_) else None
        except OSError: PIECE_MD5 = None
        _sic = os.path.join(RUN, "skin", "solid_c.json")
        if os.path.isfile(_sic):
            _sj = json.load(open(_sic, encoding="utf-8")) or {}
            _dep_ = lambda x_: (x_[3] if len(x_) > 3 else x_[2])      # UNMEASURED depth
            _pm_ = _sj.get("piece_md5")
            if not _pm_: _rec_why.append("the record names no piece (no piece_md5 - an older build, or its md5 failed)")
            elif PIECE_MD5 and PIECE_MD5 != _pm_: _rec_why.append("the record is another piece's (piece_md5 %s, this piece %s)" % (str(_pm_)[:8], PIECE_MD5[:8]))
            elif not PIECE_MD5: _rec_why.append("the piece file could not be read to compare")
            _rec_ok = not _rec_why; _why_ = list(_rec_why)
            if "self_intersections" not in _sj: _why_.append("the record holds no crossing list (an older build)")
            if "si_searched" not in _sj: _why_.append("the record predates the crossing search's completion flag (an older build)")
            elif not _sj.get("si_searched", False): _why_.append("its crossing search did not complete")
            try: _unm_ = int(_sj.get("si_unmeasured_pairs") or 0)
            except (TypeError, ValueError): _unm_ = 1
            if _unm_: _why_.append("%d face pair(s) were not measured" % _unm_)
            _deep_ = []; _unm_d_ = []; _nan_d_ = []      # UNMEASURED depth
            for x_ in (_sj.get("self_intersections") or []):
                try: _d_ = float(_dep_(x_))
                except (TypeError, ValueError, IndexError): _d_ = float("nan")
                if len(x_) > 3 and x_[3] is None: _unm_d_.append(x_)
                elif not math.isfinite(_d_): _nan_d_.append(x_)
                elif _d_ > 0.30: _deep_.append(x_)
            def _fx_(x_, how_):
                try: return "%s x %s %.2f mm %s" % (x_[0], x_[1], float(x_[3] if how_ == "deep" else x_[2]), how_)
                except (TypeError, ValueError, IndexError): return "%s" % (list(x_)[:4],)
            if _deep_: _why_.append("%d crossing(s) deeper than 0.30 mm (%s%s)" % (len(_deep_), ", ".join(_fx_(x_, "deep") for x_ in _deep_[:4]), " ..." if len(_deep_) > 4 else ""))
            if _unm_d_: _why_.append("%d crossing(s) of UNMEASURED depth (%s%s) - not cleared: nothing measured them under 0.30 mm; skin-build again with the current kit measures every crossing's depth" % (len(_unm_d_), ", ".join(_fx_(x_, "along") for x_ in _unm_d_[:4]), " ..." if len(_unm_d_) > 4 else ""))
            if _nan_d_: _why_.append("%d crossing(s) whose depth is not a number (%s)" % (len(_nan_d_), [list(x_)[:4] for x_ in _nan_d_[:3]]))
            _sfj_ = list(_sj.get("si_self_faces") or []); _sfj_how_ = "their own check(True) says SelfIntersect"
            if "si_self_faces" not in _sj and (_sj.get("check_selfintersect") or "SelfIntersect" in str(_sj.get("check", ""))):      # check_faces
                _sfj_ = [b_.get("face") for b_ in (_sj.get("check_faces") or []) if "SelfIntersect" in str(b_.get("check", ""))]; _sfj_how_ = "the record's check_faces marks SelfIntersect - an older record with no si_self_faces"
                if not _sfj_: _why_.append("the record predates the per-face self-crossing list (si_self_faces) and its check_faces name no face (an older build)")
            if _sfj_: _why_.append("%d face(s) cross THEMSELVES (%s - never measured by depth): %s%s" % (len(_sfj_), _sfj_how_, _sfj_[:12], (" +%d more" % (len(_sfj_) - 12)) if len(_sfj_) > 12 else ""))
            _si_ok = not _why_
            # check_faces
            _tse_ = [b_ for b_ in (_sj.get("check_faces") or []) if "TooSmallEdge" in str(b_.get("check", ""))]
            # wire_clean  micro_edges
            # COSMETIC like
            # check_faces
            try:
                for m_ in (((_sj.get("wire_clean") or {}).get("micro_edges") or []) if _rec_ok else []): _mic_.setdefault((int(m_["patch"]), (m_.get("sub") or None)), []).append(float(m_["len"]))
            except Exception: _mic_ = {}
            def _tse_len_(b_):
                _m = re.search(r"an edge ([0-9.]+) mm long", str(b_.get("what", "")))
                try: return float(_m.group(1)) if _m else None
                except (TypeError, ValueError): return None
            def _tse_pass_(b_):
                try: _ls = _mic_.get((int(b_.get("patch")), (b_.get("sub") or None)))
                except (TypeError, ValueError): _ls = None
                if not _ls: return False
                _l = _tse_len_(b_)
                return True if _l is None else any(abs(_l - x_) <= 0.01 for x_ in _ls)
            _tse_pass_f_ = [b_.get("face") for b_ in _tse_ if str(b_.get("rung", "")) != "cap" and _tse_pass_(b_)]
            _tse_noncap_ = [b_.get("face") for b_ in _tse_ if str(b_.get("rung", "")) != "cap" and b_.get("face") not in _tse_pass_f_]
            _tse_ok_ = bool(_rec_ok) and bool(_tse_) and not _tse_noncap_
            if _rec_ok:
                try: _g_ = float(_sj.get("edge_off_max")); _gap_ = _g_ if math.isfinite(_g_) else float("inf")      # unreadable
                except (TypeError, ValueError): _gap_ = float("inf")
            # over the  UNMEASURED
            _egu_ = None
            if "edge_gaps_unmeasured" in _sj:
                try: _egu_ = 1 if isinstance(_sj.get("edge_gaps_unmeasured"), bool) else int(float(_sj.get("edge_gaps_unmeasured")))
                except (TypeError, ValueError, OverflowError): _egu_ = 1
            if _egu_ and _rec_ok: _gap_ = float("inf")
            if _kinds_all & _GAPKINDS:
                if _egu_: say("BOP gate: %d edge gap(s) of this piece were NOT MEASURED by the build (solid_c.json edge_gaps_unmeasured %s) - its largest measured gap is over the rest only: the edge gaps are UNMEASURED, not clear, and its curve-on-surface failures are no cosmetics (R7W tester-findings (6))" % (_egu_, _sj.get("edge_gaps_unmeasured_detail") or _sj.get("edge_gaps_unmeasured")))
                elif _egu_ is None and _rec_ok: say("BOP gate: the record predates the unmeasured-gap count (no edge_gaps_unmeasured - an older build): its edge_off_max is read as it stands (R7W tester-findings (6))")
            if "SelfIntersect" in _kinds_all and not _si_ok: say("BOP gate: the build's self-intersection record does not clear the piece's self-touches - %s (31bq B07)" % "; ".join(_why_))
            if (_kinds_all & _GAPKINDS) and not _rec_ok: say("BOP gate: the edges' gap is not measured for THIS piece (%s) - its curve-on-surface failures are not cosmetics (31bq PP)" % "; ".join(_rec_why))
        elif _kinds_all & (_GAPKINDS | {"SelfIntersect"}): say("BOP gate: the build's record skin\\solid_c.json is missing - the piece's self-touches and edge gaps are not measured, so they are not cosmetics (31bq PP)")
    except Exception as _exg:
        _si_ok = False; _rec_ok = False; say("BOP gate: the build's record could not be read (%s) - nothing is cleared as cosmetic (31bq PP)" % str(_exg)[:80])
    if bad and not BOP_OK:
        def _cosmetic(b):
            ks_ = set((b.get("kinds") or {}).keys()); allowed_ = (_COSMETIC - (set() if _rec_ok else _GAPKINDS) - (set() if _tse_ok_ else {"TooSmallEdge"})) | ({"SelfIntersect"} if _si_ok else set())
            tol_ = max(float(b.get("max_edge_tol") or 0), float(b.get("max_vertex_tol") or 0), (_gap_ if (_rec_ok and (ks_ & _GAPKINDS)) else 0.0))
            return ks_ <= allowed_ and math.isfinite(tol_) and tol_ <= GAP_TOL
        _cos = [b for b in bad if _cosmetic(b)]
        if _rec_ok and math.isfinite(_gap_) and _gap_ > GAP_TOL and (_kinds_all & _GAPKINDS): say("BOP gate: the build measured an edge %.3f mm off its face on this piece (solid_c.json edge_off_max, the pcurve's gap included) - over the client's %.2f mm bound on an edge gap (Q2, 2026-10-19), not a cosmetic (31bq B07 (4) / R7d)" % (_gap_, GAP_TOL))
        _vt_ = [b for b in bad if max(float(b.get("max_vertex_tol") or 0), float(b.get("max_edge_tol") or 0)) > GAP_TOL]
        if _vt_: say("BOP gate: an EDGE / VERTEX tolerance over the client's %.2f mm bound on solid(s) %s (edge %s, vertex %s mm) - no cosmetic (Q2: edge tolerances under 0.02; 31bq PP / R7d - the 0.30 mm print tolerance is the self-touch DEPTH's bound alone)" % (GAP_TOL, [b["solid"] for b in _vt_], [b.get("max_edge_tol") for b in _vt_], [b.get("max_vertex_tol") for b in _vt_]))
        if "TooSmallEdge" in _kinds_all and not _tse_ok_: say("BOP gate: TooSmallEdge is a cosmetic only on the CAPS' own body edges and on the WIRE-CLEAN PASS's own cut-back pieces under 0.1 mm (the client's Q2 2026-10-19; the client 2026-10-23) - %s (31bq R7d / R7Wn5)" % (("the build names it on NON-cap face(s) %s (check_faces) that hold no pass-made edge of that length" % _tse_noncap_[:8]) if _tse_noncap_ else ("the build's record names no face for it" if _rec_ok else "no record of THIS piece names its faces")))
        if _tse_pass_f_: say("BOP gate: TooSmallEdge on face(s) %s is the WIRE-CLEAN PASS's own cut-back piece (%s) - an edge the construction tolerance left, its geometry moved under 0.02 mm, the sew pairs it: a COSMETIC like the caps' own edges (the client 2026-10-23, the plan's G4 (a)) - cleared without BOP_OK (31bq R7Wn5)" % (_tse_pass_f_[:8], ", ".join("face %s (patch %s%s): %s mm" % (b_.get("face"), b_.get("patch"), b_.get("sub") or "", " / ".join("%.4f" % l_ for l_ in (_mic_.get((int(b_.get("patch")), (b_.get("sub") or None))) or [])[:3])) for b_ in _tse_ if b_.get("face") in _tse_pass_f_[:6])))
        if _kinds_all & {"GeomAbs_C0", "InvalidDegeneratedFlag"}: say("BOP gate: %s - not in the client's cosmetic list (Q2: the caps' own body edges, edge tolerances under 0.02, self-touches under 0.30): BOP_OK with its reason until the client rules on it (31bq R7d)" % ", ".join(sorted(_kinds_all & {"GeomAbs_C0", "InvalidDegeneratedFlag"})))
        if len(_cos) == len(bad):
            say("BOP gate: %d piece solid(s) fail check(True) on cosmetics only (%s) - passed without BOP_OK (31bq B07 / R7d, the client's Q2: the caps' own edges, edge and vertex tolerances and edge gaps under %.2f mm, self-touches under the 0.30 mm print tolerance, THIS piece's record%s)"
                % (len(bad), "; ".join("solid %d %s" % (b["solid"], b["kinds"]) for b in bad), GAP_TOL, ("; the client 2026-10-23: the wire-clean pass's own cut-back pieces under 0.1 mm on face(s) %s - R7Wn5" % _tse_pass_f_[:8]) if _tse_pass_f_ else ""))
            bad = []
    if bad and not BOP_OK:
        _fail("FAIL: %d piece solid(s) fail the BOP check (check(True)): %s - the BOP gate lines above name what is NOT a cosmetic here (an EDGE / VERTEX TOLERANCE over 0.02 mm, a crossing deeper than 0.30 mm, an unmeasured one; a self-touch under 0.30 mm passes by itself - 31bx R6 F7). A piece like this breaks every boolean, in every construction (B47, B53, S16 - 2026-09-30), and a body that carries its faces breaks the next edit. Fix the piece (its edges on its faces: edge tolerance under 0.01 mm; no self-intersecting wire; K-C0EDGE for a C0 edge), or BOP_OK=\"<why>\" to go on anyway (recorded). Nothing saved."
              % (len(bad), "; ".join("solid %d %s" % (b["solid"], b["kinds"]) for b in bad)))
    if bad: say("BOP_OK: fusing %d BOP-invalid piece solid(s) anyway - %s" % (len(bad), BOP_OK))
    JOIN = os.environ.get("JOIN", "fuse").strip().lower()
    REGION = os.environ.get("REGION", "").strip()
    if REGION.lower() in ("none", "-", "window"): REGION = ""
    elif not REGION and os.path.isfile(P("keep_region.brep")): REGION = P("keep_region.brep")
    reg_solid = None
    if REGION:
        rs = Part.Shape(); rs.importBrep(REGION); rsol = [s for s in rs.Solids if s.Volume > 1e-6]
        if not rsol: _fail("FAIL: REGION %s holds no solid" % REGION)
        reg_solid = rsol[0] if len(rsol) == 1 else Part.makeCompound(rsol)
        say("REGION %s: %d solid(s), %d faces, %.1f mm3 (the edit region is %.1f) - the piece replaces THIS, the rest of the edit region is kept as the body's own" % (os.path.basename(REGION), len(rsol), len(reg_solid.Faces), reg_solid.Volume, window.Volume))
    if JOIN == "sew":
        if REGION: _fail("FAIL: JOIN=sew needs the piece's caps on the WINDOW's planes (wall_caps.brep) - it cannot join on another region (REGION=%s; the runner takes keep_region.brep as the default when the keep step ran). `--set REGION=none` for a sew; JOIN=fuse is the join for a keep region." % REGION)
        SEW_TOL = float(os.environ.get("SEWTOL", "1e-6")); MATCH_MM = float(os.environ.get("SEW_MATCH", "1e-3"))
        lc = local.cut(window); say("JOIN=sew: local minus the edit region: %d solid(s) %d faces vol %.1f" % (len(lc.Solids), len(lc.Faces), lc.Volume))
        wall_lc = [f for f in lc.Faces if bb.isInside(f.CenterOfMass) and any(on_plane(f, c, n) for c, n in planes)]
        def same(a, b): return (a.CenterOfMass - b.CenterOfMass).Length < MATCH_MM and abs(a.Area - b.Area) < 1e-3 * max(a.Area, 1.0)
        put = pieces + leftovers; drop_lc = set(); unmatched = []; matched = 0
        if not any(on_plane(f, c, n) for f in pieces[0].Faces for c, n in planes):
            _fail("FAIL: JOIN=sew - the piece has NO face lying in a wall plane (its caps sit elsewhere - CLIP_OUT past the walls?). A sewn piece is clipped at the planes EXACTLY and its caps are the body's own section faces (wall_caps.brep).")
        for so in put:
            for f in so.Faces:
                if any(on_plane(f, c, n) for c, n in planes):
                    hit = [g for g in wall_lc if same(f, g)]
                    if hit: drop_lc.add(hit[0].hashCode()); matched += 1
                    else: unmatched.append((round(f.Area, 2), [round(v, 1) for v in (f.CenterOfMass.x, f.CenterOfMass.y, f.CenterOfMass.z)]))
        if unmatched:
            _fail("FAIL: JOIN=sew - %d cap face(s) of the piece have no matching face on the body's cut (area, centre): %s. The piece's caps must be the body's own section faces (wall_caps.brep), edge for edge; a fuse will not join what a sew cannot." % (len(unmatched), unmatched[:4]))
        body_unmatched = [(round(g.Area, 2), [round(v, 1) for v in (g.CenterOfMass.x, g.CenterOfMass.y, g.CenterOfMass.z)]) for g in wall_lc if g.hashCode() not in drop_lc]
        if body_unmatched:
            _fail("FAIL: JOIN=sew - %d section face(s) of the BODY on the walls have no cap on the piece (area, centre): %s - the piece does not reach the body there (a wedge, a missing leftover) and the cut would stay exposed. Build the piece on every face of wall_caps.brep." % (len(body_unmatched), body_unmatched[:4]))
        keep_faces = [f for f in lc.Faces if f.hashCode() not in drop_lc] + [f for so in put for f in so.Faces if not any(on_plane(f, c, n) for c, n in planes)]
        comp = Part.makeCompound(keep_faces); comp.sewShape(SEW_TOL)
        shells = sorted(comp.Shells, key=lambda x: -len(x.Faces)); closed = [x for x in shells if x.isClosed()]
        sols = []
        for sh in closed:
            so = Part.Solid(sh)
            if so.Volume < 0: so.reverse()
            sols.append(so)
        expected = lc.Volume + sum(x.Volume for x in put); got = sum(x.Volume for x in sols)
        ok = bool(sols) and len(closed) == len(shells) and all(x.isValid() for x in sols) and abs(got - expected) < max(0.001 * expected, 1.0)
        print("  sewn: %d cap pair(s) merged both ways; %d shell(s), %d closed; solids %s valid %s; volume %.1f against expected %.1f (%+.1f) -> %s" % (matched, len(shells), len(closed), [round(x.Volume, 1) for x in sols], [x.isValid() for x in sols], got, expected, got - expected, "PASS" if ok else "FAIL"), flush=True)
        if not ok: _fail("FAIL: JOIN=sew did not close (an open shell or the volume is off) - nothing saved")
        lr = Part.makeCompound(sols)
        lr.exportBinary(P("_local_res.bin"))
        json.dump({"join": "sew", "region": P("window_solid.brep"), "region_mm3": round(window.Volume, 1), "shrink_used": 0.0, "clip_out": 0.0, "caps_merged": matched, "components_dropped": dropped_c, "in_content": IN_CONTENT, "bop": bop, "bop_ok": BOP_OK or None, "expected_mm3": round(expected, 1), "got_mm3": round(got, 1), "piece_md5": PIECE_MD5, "run_id": (os.environ.get("LK_RUN_ID") or "").strip() or None}, open(P("_reinsert_state.json"), "w"))
        print("saved (JOIN=sew, %d caps merged; %d detached component(s) dropped)" % (matched, len(dropped_c)), flush=True); raise SystemExit(0)
    # raw fuse
    # recorded
    ladder = [float(t) for t in os.environ.get("SHRINK_LADDER", "%g 1 0.5 0.3" % SHRINK).split()]
    if ladder[0] != SHRINK: ladder = [SHRINK] + [v for v in ladder if v != SHRINK]
    fuzz = [float(t) for t in os.environ.get("FUZZY", "0").split()]
    lr = None; used = None; used_f = None; state = {}
    for rung in (ladder if reg_solid is None else [None]):
        region = reg_solid if reg_solid is not None else shrunk_window(window, rung)
        t1 = time.time()
        with busy("reinsert STEP 2: local.cut(region)", 600): lc = local.cut(region)
        say("%s: body side = local - region: %d solid(s) %d faces %.1f mm3, shells per solid %s (%.0fs)" % ("REGION" if rung is None else "SHRINK %g" % rung, len(lc.Solids), len(lc.Faces), lc.Volume, [len(s.Shells) for s in lc.Solids], time.time() - t1))
        tools = []; trim_rep = []
        for kind, src in [("piece", s) for s in pieces] + [("leftover", s) for s in leftovers]:
            try: t = src.common(region)
            except Exception as ex:
                _fail("FAIL: %s cut by region threw (%s) - the piece cannot be cut by the region" % (kind, str(ex)[:80]))
            ts = [s for s in t.Solids if s.Volume > 1e-6]
            trim_rep.append({"kind": kind, "mm3": round(src.Volume, 1), "in_region_mm3": round(sum(s.Volume for s in ts), 1), "solids": len(ts)})
            say("  %s %.1f mm3 -> %.1f mm3 inside the region (%d solid(s), %d faces)" % (kind, src.Volume, sum(s.Volume for s in ts), len(ts), sum(len(s.Faces) for s in ts)))
            tools += ts
        if not tools: _fail("FAIL: nothing of the piece lies inside the region - the region and the piece do not meet")
        overlap = 0.0
        for i in range(len(tools)):
            for j in range(i + 1, len(tools)):
                if tools[i].BoundBox.intersect(tools[j].BoundBox):
                    try: overlap += tools[i].common(tools[j]).Volume
                    except Exception: pass
        expected = lc.Volume + sum(x.Volume for x in tools) - overlap
        say("  tools %d, %.1f mm3 (%.1f overlapping each other); expected union %.1f" % (len(tools), sum(x.Volume for x in tools), overlap, expected))
        tools.sort(key=lambda x: -len(x.Faces))
        for f in fuzz:
            t1 = time.time()
            try:
                cand = lc; failed_tool = None
                for ti, tl in enumerate(tools):
                    t2 = time.time(); v0 = cand.Volume
                    with busy("reinsert STEP 2: the fuse of tool %d/%d (%d faces)" % (ti + 1, len(tools), len(tl.Faces)), 900): cand = cand.fuse(tl, f) if f > 0 else cand.fuse(tl)
                    gain = cand.Volume - v0
                    say("    tool %d/%d (%d faces, %.1f mm3): gained %+.2f mm3, %d faces, %d solid(s) (%.0fs)" % (ti + 1, len(tools), len(tl.Faces), tl.Volume, gain, len(cand.Faces), len(cand.Solids), time.time() - t2))
                    if abs(gain - tl.Volume) > max(0.01 * tl.Volume, 0.5): failed_tool = (ti, tl.Volume, gain)
                if failed_tool is not None: say("  tool %d gained %.2f of its %.2f mm3 - the union lost material there" % failed_tool)
            except Exception as ex:
                say("  fuzzy %g: fuse threw: %s" % (f, str(ex)[:120])); continue
            vols = sorted((round(x.Volume, 1) for x in cand.Solids), reverse=True)
            tol = max(0.001 * expected, 2.0)
            def inner(sh):
                voids, degen = [], 0
                for s_ in sh.Solids:
                    for x in s_.Shells[1:]:
                        v = abs(Part.Solid(x).Volume) if x.isClosed() else 0.0
                        if v > 0.01: voids.append(round(v, 3))
                        else: degen += 1
                return voids, degen
            v_lc, d_lc = inner(lc); v_c, d_c = inner(cand)
            gained = len(v_c) > len(v_lc) or sum(v_c) > sum(v_lc) + 0.01
            degen_gained = d_c > d_lc
            zero_solids = [x for x in cand.Solids if x.Volume < 1.0]
            if zero_solids:
                keep_s = [x for x in cand.Solids if x.Volume >= 1.0]
                say("  %d zero-volume solid(s) dropped from the fuse result (%s mm3)" % (len(zero_solids), [round(x.Volume, 3) for x in zero_solids]))
                cand = Part.makeCompound(keep_s) if len(keep_s) != 1 else keep_s[0]
            ok = cand.isValid() and abs(cand.Volume - expected) < tol and len(cand.Solids) <= len(lc.Solids) and not gained and not degen_gained
            say("  fuzzy %g: valid %s solids %d %s faces %d vol %.1f against expected %.1f (%+.2f, tol %.1f); inner shells with volume %s (body side %s), degenerate %d%s%s (%.0fs) -> %s"
                % (f, cand.isValid(), len(cand.Solids), vols[:4], len(cand.Faces), cand.Volume, expected, cand.Volume - expected, tol, v_c, v_lc, d_c, "  ENCLOSED VOID GAINED (K-TRAP)" if gained else "", "  DEGENERATE SHELL GAINED (STEP 3's sew cannot close it - the rung fails here, 31ad)" if degen_gained else "", time.time() - t1, "PASS" if ok else "FAILED - next"))
            if ok:
                lr = cand; used = rung; used_f = f
                n_s, a_s, w_s, rows = seam_census(cand, region, bb, old=local)
                say("  seam faces left on the region's planes: %d, %.2f mm2, widest %.3f mm (STEP 4 judges them against SEAM_MAX)" % (n_s, a_s, w_s))
                state = {"join": "fuse", "region": REGION or ("shrunk edit region SHRINK %g" % rung), "region_mm3": round(region.Volume, 1), "shrink_used": used, "fuzzy_used": used_f, "ladder": ladder if reg_solid is None else None, "inner_voids_mm3": v_c, "degenerate_shells": d_c,
                         "fuzzy_ladder": fuzz, "clip_out": 0.0, "components_dropped": dropped_c, "in_content": IN_CONTENT, "bop": bop, "bop_ok": BOP_OK or None, "trim": trim_rep, "overlap_mm3": round(overlap, 2),
                         "expected_mm3": round(expected, 1), "got_mm3": round(cand.Volume, 1), "seam_faces": n_s, "seam_mm2": round(a_s, 2), "seam_widest_mm": round(w_s, 3), "piece_md5": PIECE_MD5, "run_id": (os.environ.get("LK_RUN_ID") or "").strip() or None}
                if reg_solid is None:
                    region.exportBrep(P("_region_used.brep")); state["region"] = P("_region_used.brep"); state["region_kind"] = "shrunk edit region SHRINK %g" % rung
                else: state["region_kind"] = "REGION"
                break
        if lr is not None: break
    if lr is None:
        _fail("FAIL: the local fuse failed on every rung %s x FUZZY %s. With both sides cut by the same solid the kernel has no coincident skins to lose; what is left is the piece itself - its BOP report above, or a solid of it that does not reach the region. Nothing saved." % (ladder if reg_solid is None else ["REGION"], fuzz))
    lr.exportBinary(P("_local_res.bin")); json.dump(state, open(P("_reinsert_state.json"), "w"))
    print("saved (%s, fuzzy %g; %d detached component(s) dropped; seam widest %.3f mm)" % (state["region_kind"] if "region_kind" in state else state["region"], used_f, len(dropped_c), state["seam_widest_mm"]), flush=True)

elif STEP == "3":
    need("_rest.bin", "_local_res.bin", "_localbox.brep")
    _same_piece("3")
    re_ = Part.Shape(); re_.importBinary(P("_rest.bin")); rest = re_.Solids[0]
    lr = Part.Shape(); lr.importBinary(P("_local_res.bin")); loc = [s for s in lr.Solids if s.Volume >= MIN_KEEP]
    dropped = [round(s.Volume, 2) for s in lr.Solids if s.Volume < MIN_KEEP]
    bx = Part.Shape(); bx.importBrep(P("_localbox.brep")); bb = bx.BoundBox
    lims = [(0, bb.XMin), (0, bb.XMax), (1, bb.YMin), (1, bb.YMax), (2, bb.ZMin), (2, bb.ZMax)]
    def on_box(f):
        if type(f.Surface).__name__ != "Plane": return False
        fb = f.BoundBox
        for ax, v in lims:
            lo_ = [fb.XMin, fb.YMin, fb.ZMin][ax]; hi_ = [fb.XMax, fb.YMax, fb.ZMax][ax]
            if abs(lo_ - v) < 1e-4 and abs(hi_ - v) < 1e-4: return True
        return False
    fr = [f for f in rest.Faces if not on_box(f)]; fl = [f for s in loc for f in s.Faces if not on_box(f)]
    def touches_box(f):
        for e in f.Edges:
            eb = e.BoundBox
            for ax, v in lims:
                lo_ = [eb.XMin, eb.YMin, eb.ZMin][ax]; hi_ = [eb.XMax, eb.YMax, eb.ZMax][ax]
                if abs(lo_ - v) < 1e-4 and abs(hi_ - v) < 1e-4: return True
        return False
    ring = [f for f in fr + fl if touches_box(f)]; far = [f for f in fr + fl if not touches_box(f)]
    comp = Part.makeCompound(ring)
    with busy("reinsert STEP 3: the ring sew of %d faces" % len(ring), 600): comp.sewShape(float(os.environ.get("SEWTOL", "0.01")))
    sewn = list(comp.Faces)
    say("ring sew: %d face(s) with an edge in a box plane sewn (%d from the rest, %d from the local result); %d interior faces untouched" % (len(ring), sum(1 for f in fr if touches_box(f)), sum(1 for f in fl if touches_box(f)), len(far)))
    shell = Part.Shell(far + sewn)
    if not shell.isClosed():
        import collections
        cnt = collections.Counter()
        for f in shell.Faces:
            for e in f.Edges: cnt[e.hashCode()] += 1
        _fail("FAIL: the shell is not closed after the ring sew (%d edge(s) used once) - a box face the local result does not meet: a box plane on a body face (STEP 1 moves one outward since 31bx R6 F8 - run STEP 1 again with this kit), or G changed between STEP 1 and now" % sum(1 for c in cnt.values() if c == 1))
    shells = [shell]; inner = []
    res = Part.Solid(shell)
    if res.Volume < 0: res.reverse()
    if not res.isValid(): _fail("FAIL: the body sewn from rest + the local result is not a valid solid (the shell closed). Nothing saved.")
    def mvol(sh):
        V, T, _ = R.tess_shape(sh, dev=0.1); V = np.asarray(V, float); T = np.asarray(T, int)
        return abs(np.einsum("ij,ij->i", V[T[:, 0]], np.cross(V[T[:, 1]], V[T[:, 2]])).sum() / 6.0)
    mv = mvol(res); mvl = mvol(Part.makeCompound(loc)) if loc else 0.0
    ruler = ""
    try:
        vols = json.load(open(P("_reinsert_vols.json"))); d_body = mv - vols["body_mesh_mm3"]; d_local = mvl - vols["local_mesh_mm3"]
        ruler = "; by the mesh ruler the body changed %+.0f mm3 and the local result %+.0f (they agree within %.0f)" % (d_body, d_local, abs(d_body - d_local))
        if abs(d_body - d_local) > max(50.0, 0.02 * abs(d_local) + 20.0): ruler += "   <-- they DISAGREE: material went missing or appeared at the box faces (K-LOCALBOOL)"
    except (OSError, ValueError, KeyError): pass
    print("body_new: valid %s faces %d solids %d; mesh volume %.0f mm3 (Part.Volume %.0f is not a ruler here)%s; local solids dropped under %.0f mm3: %s (%.0fs)" % (res.isValid(), len(res.Faces), 1, mv, res.Volume, ruler, MIN_KEEP, dropped, time.time() - T0), flush=True)
    res.exportBrep(P("body_new.brep"))
    st = {}
    try: st = json.load(open(P("_reinsert_state.json"))); SHRINK = float(st.get("shrink_used") or 0.0)
    except (OSError, ValueError): pass
    json.dump({"tag": TAG, "body": os.environ.get("BODY"), "piece": os.environ.get("PIECE", P("piece.brep")), "G": G, "join": st.get("join", "fuse"), "region": st.get("region"), "region_mm3": st.get("region_mm3"), "SHRINK": SHRINK, "shrink_ladder": st.get("ladder"), "fuzzy_used": st.get("fuzzy_used"), "caps_merged": st.get("caps_merged"), "CLIP_OUT": st.get("clip_out", 0.0),
               "bop": st.get("bop"), "bop_ok": st.get("bop_ok"), "expected_mm3": st.get("expected_mm3"), "got_mm3": st.get("got_mm3"), "seam_faces": st.get("seam_faces"), "seam_mm2": st.get("seam_mm2"), "seam_widest_mm": st.get("seam_widest_mm"),
               "components_dropped": st.get("components_dropped", []), "piece_md5": st.get("piece_md5"), "faces": len(res.Faces), "valid": bool(res.isValid()), "mesh_volume_mm3": round(mv, 1), "local_result_mesh_mm3": round(mvl, 1), "ruler": ruler.strip("; "), "dropped_mm3": dropped, "ring_faces_sewn": len(ring)}, open(P("REBUILD_reinsert.json"), "w"), indent=1)
    print("saved body_new.brep (%.0fs)" % (time.time() - T0), flush=True)

elif STEP == "4":
    need("body_new.brep", "_localbox.brep", "_local.bin", "_local_res.bin", "_reinsert_state.json")
    _same_piece("4")
    st = json.load(open(P("_reinsert_state.json")))
    f = Part.Shape(); f.importBrep(P("body_new.brep")); fin = f.Solids[0]
    bx = Part.Shape(); bx.importBrep(P("_localbox.brep")); bb = bx.BoundBox
    old = Part.Shape(); old.importBinary(P("_local.bin")); newl = Part.Shape(); newl.importBinary(P("_local_res.bin"))
    rp = st.get("region"); region = None
    if rp and os.path.isfile(rp):
        rs = Part.Shape(); rs.importBrep(rp); region = rs
    else:
        rg = Part.Shape(); rg.importBrep(P("window_solid.brep")); region = rg.Solids[0] if st.get("join") == "sew" else shrunk_window(rg.Solids[0], float(st.get("shrink_used") or 0.0))
    say("STEP 2 joined by %s on %s (%.1f mm3)" % (st.get("join"), st.get("region_kind", os.path.basename(str(rp))), float(st.get("region_mm3") or region.Volume)))
    SEAM_MAX = float(os.environ.get("SEAM_MAX", "0.15")); PROTECT_TOL = float(os.environ.get("PROTECT_TOL", "2.0"))
    bad = []
    n_s, a_s, w_s, rows = seam_census(fin, region, bb, old=old)
    say("SEAM: %d face(s) of the new body lie on the region's planes beyond the old body's own there: %.2f mm2, widest %.3f mm (2A/P)" % (n_s, a_s, w_s))
    for w, a, n, c in rows[:6]:
        say("   width %.3f mm, %.2f mm2, on the plane with normal (%.2f %.2f %.2f)%s" % (w, a, n[0], n[1], n[2], "   <-- over SEAM_MAX %.2f" % SEAM_MAX if w > SEAM_MAX else ""))
    if w_s > SEAM_MAX: bad.append("a seam face %.3f mm wide (SEAM_MAX %.2f): the piece's section at that plane differs from the body's - a step or a lip the print will show; a wall through a changed feature, a grazing wall (L82), or a keep bin whose neighbour the piece changed" % (w_s, SEAM_MAX))
    try:
        wide = [f for f in seam_census.faces if width_of(f) > 0.1]
        if not wide:
            import glob as _glob
            stale = _glob.glob(os.path.join(RUN, "review_body", "seam_*.png")) + ([P("seam_faces.brep")] if os.path.isfile(P("seam_faces.brep")) else [])
            for _f in stale:
                try: os.remove(_f)
                except OSError: pass
            if stale: say("no seam face over 0.1 mm: %d stale seam picture(s)/file(s) of an earlier build removed" % len(stale))
        if wide:
            Part.makeCompound(wide).exportBrep(P("seam_faces.brep"))
            od = os.path.join(RUN, "review_body"); os.makedirs(od, exist_ok=True)
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sk_lib as K
            Vl, Tl, Fl, MQl = K.piece_mesh(None, newl, cache_dir=od, say=say); Vl = np.asarray(Vl, float); Tl = np.asarray(Tl, int); Fl = np.asarray(Fl, int)
            Vs, Ts, Fs, MQs = K.piece_mesh(None, Part.makeCompound(wide), cache_dir=od, say=say); Vs = np.asarray(Vs, float); Ts = np.asarray(Ts, int); Fs = np.asarray(Fs, int)
            ttl = "SEAM: %d face(s) wider than 0.1 mm in red (widest %.2f mm, SEAM_MAX %.2f) on the local result" % (len(wide), w_s, SEAM_MAX)
            _bb = newl.BoundBox; _fb = (_bb.XMin, _bb.XMax, _bb.YMin, _bb.YMax, _bb.ZMin, _bb.ZMax)
            for nm, d in {"above": R.look(fwd=0.3, left=0.2, up=-1.0), "below": R.look(fwd=0.3, left=-0.2, up=1.0), "iso": R.look(fwd=0.7, left=-0.5, up=-0.5)}.items():
                K.view_meshes(R, os.path.join(od, "seam_%s.png" % nm), [(Vl, Tl, Fl, MQl, (0.62, 0.64, 0.68)), (Vs, Ts, Fs, MQs, (0.95, 0.15, 0.1), 0.3)], d, _fb, 1300, "seam %s" % nm, ttl,
                              ["Grey = the local result, RED = the seam faces wider than 0.1 mm; smooth-shaded within each face; a red RENDER DEFECTIVE banner across the frame = NO EVIDENCE."])
            say("seam_faces.brep (%d faces) and review_body\\seam_*.png written - OPEN THEM" % len(wide))
    except Exception as ex:
        say("the seam picture was not made (%s)" % str(ex)[:80])
    prot = []; boxes = load_protect()
    say("PROTECT: %d box(es) from %s" % (len(boxes), load_protect.source))
    if boxes:
        Vo_, To_, _ = R.tess_shape(old, dev=0.05); Vo_ = np.asarray(Vo_, float); To_ = np.asarray(To_, int)
        Vn_, Tn_, _ = R.tess_shape(newl, dev=0.05); Vn_ = np.asarray(Vn_, float); Tn_ = np.asarray(Tn_, int)
    def material_in(V_, T_, b, h=0.25):
        n = [max(2, int(round((b[2 * a + 1] - b[2 * a]) / h))) for a in range(3)]
        g0 = np.array([b[0], b[2], b[4]]) + h / 2.0
        occ, _ = R.inside_vote(V_, T_, g0, n, h)
        return float(occ.sum()) * h ** 3
    for b in boxes:
        vb = (b[1] - b[0]) * (b[3] - b[2]) * (b[5] - b[4])
        try:
            vo = material_in(Vo_, To_, b); vn = material_in(Vn_, Tn_, b)
        except Exception as ex:
            say("PROTECT %s: the material test threw (%s) - NOT TAKEN" % (b, str(ex)[:60])); bad.append("PROTECT %s not measured" % b); continue
        d = vn - vo; pct = 100.0 * d / max(vb, 1e-9); fl = abs(d) > max(1.0, PROTECT_TOL / 100.0 * vb)
        prot.append({"box": b, "old_mm3": round(vo, 2), "new_mm3": round(vn, 2), "box_mm3": round(vb, 1), "delta_mm3": round(d, 2), "delta_pct_of_box": round(pct, 2), "refused": fl})
        say("PROTECT %s: material %.1f -> %.1f mm3 of %.1f (%+.1f %% of the box)%s" % (b, vo, vn, vb, pct, "   <-- REFUSED: a protected void changed" if fl else ""))
        if fl: bad.append("PROTECT box %s changed by %+.1f mm3 (%+.1f %% of the box; PROTECT_TOL %.1f %%): the designed void is not what it was" % (b, d, pct, PROTECT_TOL))
    def inner(sh):
        voids, degen = [], 0
        for s_ in sh.Solids:
            for x in s_.Shells[1:]:
                v = abs(Part.Solid(x).Volume) if x.isClosed() else 0.0
                if v > 0.01: voids.append(round(v, 3))
                else: degen += 1
        return voids, degen
    v_old, d_old = inner(old); v_new, d_new = inner(newl)
    gained = len(v_new) > len(v_old) or sum(v_new) > sum(v_old) + 0.01
    sh_old = v_old; sh_new = v_new
    say("SHELLS: inner voids before %s mm3, after %s mm3; degenerate (zero-volume) shells after %d%s" % (v_old, v_new, d_new, "   <-- a void was made (K-TRAP)" if gained else ""))
    if gained: bad.append("the local result gained an enclosed void %s mm3 (powder trapped, K-TRAP): the piece has air where the body had material inside" % v_new)
    ok = not bad and fin.isValid() and len(f.Solids) == 1
    json.dump({"tag": TAG, "join": st.get("join"), "region": rp, "seam": {"faces": n_s, "mm2": round(a_s, 2), "widest_mm": round(w_s, 3), "SEAM_MAX": SEAM_MAX, "worst": rows[:10]}, "protect": prot, "protect_source": load_protect.source, "PROTECT_TOL": PROTECT_TOL, "shells": {"before": sh_old, "after": sh_new},
               "valid": bool(fin.isValid()), "solids": len(f.Solids), "faces": len(fin.Faces), "refused": bad, "verdict": "PASS" if ok else "FAIL"}, open(P("REBUILD_check.json"), "w"), indent=1)
    for b in bad: print("REFUSED: %s" % b, flush=True)
    print("CHECK %s: valid %s, %d solid(s), %d faces; seam %d face(s) %.2f mm2 widest %.3f mm; PROTECT boxes %d checked (from %s)" % ("PASS" if ok else "FAIL", fin.isValid(), len(f.Solids), len(fin.Faces), n_s, a_s, w_s, len(prot), load_protect.source), flush=True)

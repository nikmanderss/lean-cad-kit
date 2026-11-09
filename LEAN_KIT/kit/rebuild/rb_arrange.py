# kit rebuild
# kit rebuild
# over the
# ORIGINAL
# INTERNAL
import math, os, sys, time, json, collections, numpy as np, Part, FreeCAD
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
TAG = os.environ.get("LK_TAG", "")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from _busy import busy
TOOL_ALLOW = float(os.environ.get("TOOL_ALLOW", "900"))
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_arr_prefix.py")).read().split("# ---------------------------------------------------------------- adjacency, convexity")[0]
exec(src)
STAGE = os.environ.get("STAGE", "A")
PROTECT_A = PROTECT_P
LEVEL_WALL = float(os.environ.get("LEVEL_WALL", "0.15")); LEVEL_VERTS = os.environ.get("LEVEL_VERTS", "1") == "1"
if STAGE == "A":
    T1 = time.time(); STAGE = os.environ.get("STAGE", "A"); NMAX = int(os.environ.get("NMAX", "99")); LEVEL = float(os.environ.get("LEVEL", "0.8"))
    def garea(r): return sum(D[i]["area"] for i in range(len(F)) if REP.get(i, i) == r)
    reps = sorted(set(REP.get(i, i) for i in range(len(F)) if design_face(i) and D[i]["wpts"]), key=lambda r: -garea(r))
    use = []; DUP = {}
    try: WALLS_A = [w for w in json.load(open(os.path.join(RUN, "walls.json"))) if len(w) == 6]
    except Exception: WALLS_A = []
    OLD_USE = set()
    if os.environ.get("SPLIT", "seq") == "more" and os.path.exists(os.path.join(RUN, "cells.json")):
        try: OLD_USE = set(int(u) for u in json.load(open(os.path.join(RUN, "cells.json")))["use"])
        except Exception: OLD_USE = set()
    for r in reps:
        dup = None
        if r in OLD_USE: use.append(r); continue
        for k in use:
            def _touches(rr):
                for i in range(len(F)):
                    if REP.get(i, i) != rr: continue
                    b = F[i].BoundBox
                    if not (b.XMin > WIN[0] + 0.05 and b.XMax < WIN[1] - 0.05 and b.YMin > WIN[2] + 0.05 and b.YMax < WIN[3] - 0.05 and b.ZMin > WIN[4] + 0.05 and b.ZMax < WIN[5] - 0.05): return True
                    for pb in PROTECT_A:
                        if b.XMax >= pb[0] and b.XMin <= pb[1] and b.YMax >= pb[2] and b.YMin <= pb[3] and b.ZMax >= pb[4] and b.ZMin <= pb[5]: return True
                    for vx in F[i].Vertexes:
                        p_ = vx.Point
                        for w in WALLS_A:
                            n_ = FreeCAD.Vector(*w[3:]); n_.normalize()
                            if abs((p_ - FreeCAD.Vector(*w[:3])).dot(n_)) < 0.05: return True
                return False
            touches = _touches(r)
            small = garea(r) < float(os.environ.get("DUP_FRAC", "0.25")) * garea(k) and not touches
            lev = LEVEL if small else float(os.environ.get("LEVEL0", "0.5")); deg = float(os.environ.get("LEVEL_DEG", "12.0")) if small else float(os.environ.get("LEVEL0_DEG", "5.0"))
            if touches: lev = min(lev, LEVEL_WALL)
            if D[k]["n"].dot(D[r]["n"]) < math.cos(math.radians(deg)): continue
            try:
                grp = [i for i in range(len(F)) if REP.get(i, i) == r]
                vals = [abs(signed(k, p)) for i in grp for p, n in D[i]["wpts"]]
                if LEVEL_VERTS: vals += [abs(signed(k, vx.Point)) for i in grp for vx in F[i].Vertexes if in_win(vx.Point)]
                dmax = max(vals)
            except Exception: continue
            if dmax < lev: dup = k; DUP[r] = (k, round(dmax, 3), lev); break
        if dup is None: use.append(r)
    if DUP: print("  merged as duplicates (face -> tool, max deviation, the bound): %s" % " ".join("f%d->f%d(%.3f<%.2f)" % (r + 1, k + 1, d, lv) for r, (k, d, lv) in sorted(DUP.items())), flush=True)
    use = use[:NMAX]
    CELLS_P = os.path.join(RUN, "cells.brep"); META_P = os.path.join(RUN, "cells.json")
    import sys, numpy as np
    sys.path.insert(0, os.environ["KIT_HOME"])
    import kitlib_render as R
    _t = time.time(); MV, MT, _ = R.tess_shape(big, dev=0.02); ZR = R.ZRays(MV, MT, cell=2.0)
    def inside_mesh(p):
        for z0, z1 in ZR.solid_runs(p.x, p.y):
            if z0 - 1e-6 <= p.z <= z1 + 1e-6: return True
        return False
    print("  mesh for the inside test: %d triangles (%.0fs)" % (len(MT), time.time() - _t), flush=True)
    if STAGE == "A" or not os.path.exists(META_P):
        print("design surfaces %d, using %d: %s" % (len(reps), len(use), " ".join("f%d" % (r + 1) for r in use)), flush=True)
        shells = [bound_shell(r, +1) for r in use]
        print("  tools: %d planes, %d curved (faces per curved tool: %s)" % (sum(1 for r in use if D[r]["plane"]), sum(1 for r in use if not D[r]["plane"]), " ".join("f%d:%d" % (r + 1, len(SHELLS[(r, 1)].Faces)) for r in use if not D[r]["plane"])), flush=True)
        print("  planarized interior faces: %s" % " ".join("f%d(%.2f)" % (r + 1, D[r]["dev"]) for r in use if D[r]["plane"] and D[r]["kind"] != "Plane"), flush=True)
        t = time.time()
        SPLIT_P = os.path.join(RUN, "cells_split.brep"); SPLIT = os.environ.get("SPLIT", "seq"); MORE = SPLIT == "more"
        OLD_META = None
        if MORE:
            _sd = os.path.join(RUN, "cells_seq_done.json")
            if not (os.path.exists(CELLS_P) and os.path.exists(META_P) and os.path.exists(_sd)): _fail("FAIL: SPLIT=more needs the finished split on disk (cells.brep, cells.json, cells_seq_done.json) - run the plain split first")
            OLD_META = json.load(open(META_P)); _old_use = [int(u) for u in OLD_META["use"]]
            _missing = [u for u in _old_use if u not in use]
            if _missing: _fail("FAIL: SPLIT=more needs the new tool set to contain the old - %d old tool(s) are not in it (%s): a tool cannot be unapplied; re-split from scratch (rename cells.* aside)" % (len(_missing), " ".join("f%d" % (u + 1) for u in _missing)))
            _new = [u for u in use if u not in _old_use]
            print("SPLIT=more: %d tools before, %d new to apply (%s)" % (len(_old_use), len(_new), " ".join("f%d" % (u + 1) for u in _new) or "none"), flush=True)
            if not _new and not os.path.exists(SPLIT_P):
                res = Part.Shape(); res.importBrep(CELLS_P); cells = res.Solids; print("cells: %d (loaded, no new tool)" % len(cells), flush=True)
        elif os.path.exists(CELLS_P) and not os.path.exists(SPLIT_P):
            _fail("FAIL: cells.brep exists (a finished split) - a second split would leave cells.json mismatched with it. To add tools to it: --set SPLIT=more; to split from scratch: rename cells.brep / cells.json / cells_meta_partial.json / cells_seq_done.json aside")
        if os.path.exists(SPLIT_P):
            res = Part.Shape(); res.importBrep(SPLIT_P); cells = res.Solids; print("cells: %d (loaded)" % len(cells), flush=True)
        elif MORE and not _new: pass
        else:
            FUZZ = float(os.environ.get("FUZZ", "1e-5"))
            if SPLIT == "single":
                with busy("arrange: the one generalFuse of %d tools" % len(shells), TOOL_ALLOW): res, gmap = win.generalFuse(shells, FUZZ)
                cells = res.Solids
                print("cells: %d (one fuse, fuzzy %g, %.0fs)" % (len(cells), FUZZ, time.time() - t), flush=True)
                res.exportBrep(SPLIT_P)
            else:
                # recorded
                SEQ_P = os.path.join(RUN, "cells_seq.brep"); SEQ_J = os.path.join(RUN, "cells_seq.json")
                if MORE and not os.path.exists(SEQ_J):
                    _st0 = json.load(open(os.path.join(RUN, "cells_seq_done.json")))
                    st = {"saved_done": list(_st0.get("saved_done", [])), "dropped": list(_st0.get("dropped", [])), "attempting": None, "clock": dict(_st0.get("clock", {})), "more_from": list(_st0.get("saved_done", []))}
                    import shutil; shutil.copy2(CELLS_P, SEQ_P)
                    for _f in (CELLS_P, META_P, os.path.join(RUN, "cells_seq_done.json")):
                        if os.path.exists(_f) and not os.path.exists(_f + ".before_more"): shutil.copy2(_f, _f + ".before_more")
                    _pp = os.path.join(RUN, "cells_meta_partial.json")
                    if os.path.exists(_pp): os.remove(_pp)
                    json.dump(st, open(SEQ_J, "w"))
                else: st = json.load(open(SEQ_J)) if os.path.exists(SEQ_J) else {"saved_done": [], "dropped": [], "attempting": None, "clock": {}}
                if st.get("attempting") is not None:
                    r_ = st["attempting"]; st["dropped"].append([r_, "its split did not return before the kill (the previous run)"]); st["attempting"] = None
                    json.dump(st, open(SEQ_J, "w")); print("  tool f%d DROPPED: its split did not return in the previous run" % (r_ + 1), flush=True)
                order = [r for r in use if D[r]["plane"]] + [r for r in use if not D[r]["plane"]]
                dropped_ids = {d[0] for d in st["dropped"]}; done = list(st["saved_done"])
                vwin0 = (WIN[1] - WIN[0]) * (WIN[3] - WIN[2]) * (WIN[5] - WIN[4])
                TOOL_VOLCHECK = os.environ.get("TOOL_VOLCHECK", "1") == "1"
                if os.path.exists(SEQ_P):
                    cur = Part.Shape(); cur.importBrep(SEQ_P); cur = Part.Compound(cur.Solids); print("  split resumes: %d tools in the saved partition, %d dropped, %d cells" % (len(done), len(st["dropped"]), len(cur.Solids)), flush=True)
                    if TOOL_VOLCHECK:
                        with busy("arrange: the volume check of the saved partition (%d cells)" % len(cur.Solids), 600):
                            _vs = [s_.Volume for s_ in cur.Solids]
                        _ng = sum(1 for v_ in _vs if v_ < 0); _vt = sum(_vs)
                        if _ng or abs(_vt - vwin0) > 1e-3 * vwin0:
                            _fail("FAIL: the saved partition (cells_seq.brep) is broken - %d reversed solid(s), the cells sum to %.1f of the window's %.1f mm3. Set cells_seq.brep / cells_seq.json aside (rename) and resume from the finished split (SPLIT=more) - nothing was built on it" % (_ng, _vt, vwin0))
                else: cur = win
                CLIP = os.environ.get("CLIP_TOOLS", "1") == "1"
                clipbox = Part.makeBox(WIN[1] - WIN[0] + 4.0, WIN[3] - WIN[2] + 4.0, WIN[5] - WIN[4] + 4.0, FreeCAD.Vector(WIN[0] - 2.0, WIN[2] - 2.0, WIN[4] - 2.0))
                def _save():
                    cur.exportBrep(SEQ_P); st["saved_done"] = list(done); json.dump(st, open(SEQ_J, "w"))
                tsave = time.time()
                for r in order:
                    if r in done or r in dropped_ids: continue
                    if time.time() - T1 > BUDGET:
                        _save(); print("STAGE A split PAUSED after %d of %d tools (%d cells) - run again" % (len(done) + len(st["dropped"]), len(order), len(cur.Solids)), flush=True); raise SystemExit(0)
                    if time.time() - tsave > 45.0 and len(done) > len(st["saved_done"]): _save(); tsave = time.time()
                    tool = bound_shell(r, +1)
                    if CLIP:
                        try:
                            tc = tool.common(clipbox)
                            if tc.Faces: tool = Part.Compound(tc.Faces)
                        except Exception as ex: print("  f%d: clip refused (%r) - the whole tool is used" % (r + 1, ex), flush=True)
                    st["attempting"] = r; json.dump(st, open(SEQ_J, "w"))
                    t0 = time.time(); n0 = len(cur.Solids)
                    try:
                        with busy("arrange: the split by tool f%d on %d cells" % (r + 1, n0), TOOL_ALLOW): res, gmap = cur.generalFuse([tool], FUZZ)
                        sols = res.Solids
                        if len(sols) < n0: raise RuntimeError("the split returned %d cells, had %d" % (len(sols), n0))
                        if TOOL_VOLCHECK:
                            with busy("arrange: the volume check of %d cells after f%d" % (len(sols), r + 1), 600):
                                _vs = [s_.Volume for s_ in sols]
                            _ng = sum(1 for v_ in _vs if v_ < 0); _vt = sum(_vs)
                            if _ng or abs(_vt - vwin0) > 1e-3 * vwin0:
                                raise RuntimeError("the split returned a broken partition: %d reversed solid(s), the cells sum to %.1f of the window's %.1f mm3" % (_ng, _vt, vwin0))
                        cur = Part.Compound(sols); done.append(r)
                    except Exception as ex:
                        st["dropped"].append([r, "the split refused: %r" % (ex,)]); dropped_ids.add(r)
                        print("  tool f%d DROPPED: %r (%.0fs)" % (r + 1, ex, time.time() - t0), flush=True)
                    st["attempting"] = None; st["clock"][str(r)] = round(time.time() - t0, 1)
                    print("  f%d %s: %d -> %d cells (%.0fs)" % (r + 1, "plane" if D[r]["plane"] else D[r]["kind"], n0, len(cur.Solids), time.time() - t0), flush=True)
                res = cur; cells = res.Solids
                vwin = (WIN[1] - WIN[0]) * (WIN[3] - WIN[2]) * (WIN[5] - WIN[4]); vcells = res.Volume
                st["saved_done"] = list(done)
                print("cells: %d (sequential, %d tools, %d dropped, fuzzy %g, %.0fs this call); cell volume %.1f of the window's %.1f (%.3f %%)" % (len(cells), len(done), len(st["dropped"]), FUZZ, time.time() - t, vcells, vwin, 100.0 * vcells / vwin), flush=True)
                if st["dropped"]: print("  tools dropped (their surfaces are decided by the classification): %s" % "; ".join("f%d - %s" % (d[0] + 1, d[1]) for d in st["dropped"]), flush=True)
                if abs(vcells - vwin) > 1e-3 * vwin: _fail("FAIL: the cells do not fill the window (%.1f of %.1f mm3) - the split lost material" % (vcells, vwin))
                res.exportBrep(SPLIT_P)
                try: os.remove(SEQ_P)
                except Exception: pass
                json.dump(st, open(os.path.join(RUN, "cells_seq_done.json"), "w"))
                try: os.remove(SEQ_J)
                except Exception: pass
            if time.time() - T1 > 100: print("STAGE A split saved - run again to classify", flush=True); raise SystemExit(0)
        face_tool = {}
        def inner(c):
            p = c.CenterOfMass
            if c.isInside(p, 1e-6, True): return p
            for fc in c.Faces[:10]:
                try:
                    q = fc.CenterOfMass; u_, v_ = fc.Surface.parameter(q); q = fc.valueAt(u_, v_); n = fc.normalAt(u_, v_)
                    for t_ in (0.3, 0.1, 0.03):
                        if c.isInside(q - n * t_, 1e-6, True): return q - n * t_
                except Exception: pass
            return p
        t = time.time()
        PARTIAL = os.path.join(RUN, "cells_meta_partial.json")
        meta = json.load(open(PARTIAL)) if os.path.exists(PARTIAL) else []
        k0 = len(meta)
        if k0: print("  classification resumes at cell %d" % k0, flush=True)
        OLDK = {}
        if MORE:
            if OLD_META is None: OLD_META = json.load(open(META_P))
            for m_ in OLD_META["meta"]: OLDK[(round(m_["vol"], 3), round(m_["pt"][0], 2), round(m_["pt"][1], 2), round(m_["pt"][2], 2))] = m_["frac"]
            _carried = 0
        for k in range(k0, len(cells)):
            c = cells[k]
            if time.time() - T1 > 150:
                json.dump(meta, open(PARTIAL, "w")); print("STAGE A classification PAUSED at %d/%d - run again" % (k, len(cells)), flush=True); raise SystemExit(0)
            if k % 500 == 0 and k > k0: print("  classified %d/%d (%.0fs)" % (k, len(cells), time.time() - t), flush=True)
            p = inner(c)
            if MORE:
                _key = (round(c.Volume, 3), round(p.x, 2), round(p.y, 2), round(p.z, 2))
                if _key in OLDK:
                    faces = [[fc.hashCode(), -1, round(fc.CenterOfMass.x, 2), round(fc.CenterOfMass.y, 2), round(fc.CenterOfMass.z, 2), round(fc.Area, 1)] for fc in c.Faces]
                    meta.append({"k": k, "vol": c.Volume, "area": c.Area, "frac": OLDK[_key], "pt": [p.x, p.y, p.z], "faces": faces, "carried": 1}); _carried += 1; continue
            pts = [p]
            for fc in c.Faces[:4]:
                try:
                    q = fc.CenterOfMass; u_, v_ = fc.Surface.parameter(q); q = fc.valueAt(u_, v_); n = fc.normalAt(u_, v_)
                    if c.isInside(q - n * 0.2, 1e-6, True): pts.append(q - n * 0.2)
                except Exception: pass
            ins = sum(1 for q in pts if inside_mesh(q)); frac = ins / float(len(pts))
            faces = [[fc.hashCode(), face_tool.get(fc.hashCode(), -1), round(fc.CenterOfMass.x, 2), round(fc.CenterOfMass.y, 2), round(fc.CenterOfMass.z, 2), round(fc.Area, 1)] for fc in c.Faces]
            meta.append({"k": k, "vol": c.Volume, "area": c.Area, "frac": frac, "pt": [p.x, p.y, p.z], "faces": faces})
        print("classified (%.0fs): material (frac>=0.5) %d cells %.0f mm3; mixed (0<frac<1) %d%s" % (time.time() - t, sum(1 for m in meta if m["frac"] >= 0.5), sum(m["vol"] for m in meta if m["frac"] >= 0.5), sum(1 for m in meta if 0 < m["frac"] < 1), ("; %d cells carried over from the saved split, %d classified anew" % (_carried, len(meta) - _carried)) if MORE else ""), flush=True)
        if MORE and os.path.exists(SPLIT_P): os.replace(SPLIT_P, CELLS_P)
        elif not os.path.exists(CELLS_P): os.replace(SPLIT_P, CELLS_P)
        _sd = os.path.join(RUN, "cells_seq_done.json"); _dropped = json.load(open(_sd))["dropped"] if os.path.exists(_sd) else []
        json.dump({"use": use, "meta": meta, "tools_dropped": [[int(d[0]) + 1, d[1]] for d in _dropped], "dups": {str(int(r) + 1): [int(k) + 1, d, lv] for r, (k, d, lv) in DUP.items()},
                   "levers": {k_: os.environ.get(k_) for k_ in ("A_SMALL", "LEVEL", "LEVEL_DEG", "LEVEL0", "LEVEL0_DEG", "DUP_FRAC", "LEVEL_WALL", "LEVEL_VERTS", "PROTECT_FACES", "T_MIN", "SPLIT")}}, open(META_P, "w"))
        print("STAGE A done (%.0fs)" % (time.time() - T1), flush=True)
        raise SystemExit(0)

else:
    sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
    T1 = time.time()
    M = json.load(open(os.path.join(RUN, "cells.json"))); meta = M["meta"]; use = M["use"]
    DUPS = {int(r) - 1: (int(v[0]), float(v[1]), float(v[2])) for r, v in (M.get("dups") or {}).items()}
    res = Part.Shape(); res.importBrep(os.path.join(RUN, "cells.brep")); cells = res.Solids
    def _fkey(fc):
        c_ = fc.CenterOfMass; return (fc.hashCode(), round(fc.Area, 4), round(c_.x, 3), round(c_.y, 3), round(c_.z, 3))
    fmap = collections.defaultdict(list); HK = {}
    for k, c in enumerate(cells):
        hs_ = [_fkey(fc) for fc in c.Faces]; HK[k] = hs_
        for h in hs_: fmap[h].append(k)
        if k % 2000 == 0 and k: print("  face identity: %d/%d cells (%.0fs)" % (k, len(cells), time.time() - T1), flush=True)
    nb = collections.defaultdict(set)
    for h, ks in fmap.items():
        for a_ in ks:
            for b_ in ks:
                if a_ != b_: nb[a_].add(b_)
    print("faces shared by exactly two cells: %d, by one: %d, by more: %d" % (sum(1 for v in fmap.values() if len(v) == 2), sum(1 for v in fmap.values() if len(v) == 1), sum(1 for v in fmap.values() if len(v) > 2)), flush=True)
    sys.path.insert(0, os.environ["KIT_HOME"])
    MV, MT, _ = R.tess_shape(big, dev=0.02); ZR = R.ZRays(MV, MT, cell=2.0)
    def inside_mesh(p):
        for z0, z1 in ZR.solid_runs(p[0], p[1]):
            if z0 - 1e-6 <= p[2] <= z1 + 1e-6: return True
        return False
    FRAC_BOX = os.environ.get("FRAC_BOX", "loose").strip().lower()
    def _cbox(c):
        if FRAC_BOX == "optimal":
            try: return c.optimalBoundingBox(False, False)
            except Exception: pass
        return c.BoundBox
    rng = np.random.RandomState(7); nre = 0; _nmix = sum(1 for m in meta if 0.0 < m["frac"] < 1.0); _k = 0
    for m in meta:
        if not (0.0 < m["frac"] < 1.0): continue
        _k += 1
        if _k % 25 == 0: print("  re-classifying mixed cell %d/%d (%.0fs)" % (_k, _nmix, time.time() - T1), flush=True)
        c = cells[m["k"]]; b = _cbox(c); pts = []
        for i in range(5):
            for j in range(5):
                for kk in range(5):
                    p = (b.XMin + (i + 0.5) / 5.0 * b.XLength, b.YMin + (j + 0.5) / 5.0 * b.YLength, b.ZMin + (kk + 0.5) / 5.0 * b.ZLength)
                    if c.isInside(FreeCAD.Vector(*p), 1e-6, True): pts.append(p)
        if len(pts) >= 6:
            m["frac"] = sum(1 for p in pts if inside_mesh(p)) / float(len(pts)); nre += 1
    print("mixed cells re-classified: %d (of %d mixed; FRAC_BOX %s)" % (nre, _nmix, FRAC_BOX), flush=True)
    WALL_ZONE = float(os.environ.get("WALL_ZONE", "1.5"))
    try: WALLS_M = [w for w in json.load(open(os.path.join(RUN, "walls.json"))) if len(w) == 6]
    except Exception: WALLS_M = []
    def bbox_in_zone(b, grow=0.0):
        """does the BoundBox b reach within WALL_ZONE of a wall plane, or meet a PROTECT box (grown)"""
        if meets_protect(b, grow): return True
        cs = [FreeCAD.Vector(x, y, z) for x in (b.XMin, b.XMax) for y in (b.YMin, b.YMax) for z in (b.ZMin, b.ZMax)]
        for w in WALLS_M:
            c_ = FreeCAD.Vector(*w[:3]); n_ = FreeCAD.Vector(*w[3:]); n_.normalize()
            ds = [(q - c_).dot(n_) for q in cs]
            if min(ds) <= WALL_ZONE + grow and max(ds) >= -WALL_ZONE - grow: return True
        return False
    def frac125(c):
        b = _cbox(c); pts = []
        for i in range(5):
            for j in range(5):
                for kk in range(5):
                    p = (b.XMin + (i + 0.5) / 5.0 * b.XLength, b.YMin + (j + 0.5) / 5.0 * b.YLength, b.ZMin + (kk + 0.5) / 5.0 * b.ZLength)
                    if c.isInside(FreeCAD.Vector(*p), 1e-6, True): pts.append(p)
        if len(pts) < 6: return None
        return sum(1 for p in pts if inside_mesh(p)) / float(len(pts))
    REFINE_RAW = os.environ.get("REFINE_ZONES", "0").strip().lower(); REFINE = REFINE_RAW not in ("", "0", "off", "no")
    REF_FRAC = float(os.environ.get("REFINE_FRAC", "0.98")); REF_MAX = int(os.environ.get("REFINE_MAX", "60"))
    refined_rep = {"cells": 0, "faces": 0, "new_cells": 0, "skipped": []}
    if REFINE:
        t_r = time.time(); tool_faces = set(int(u) for u in use)
        def _fkey_geo(fc):
            c_ = fc.CenterOfMass; return (round(fc.Area, 4), round(c_.x, 3), round(c_.y, 3), round(c_.z, 3))
        cand = []; nz = 0
        if REFINE_RAW == "census":
            _ccp = os.path.join(RUN, "census_cells.json")
            try: _cc = json.load(open(_ccp))
            except Exception: _fail("FAIL: REFINE_ZONES=census needs census_cells.json from an arrange-m on this split without REFINE (it writes it) - run arrange-m once without REFINE_ZONES")
            _st = os.stat(os.path.join(RUN, "cells.brep"))
            if _cc.get("refined") or int(_cc.get("n_cells", -1)) != len(cells) or (_cc.get("cells_brep") or {}).get("size") != _st.st_size:
                _fail("FAIL: census_cells.json is not from this split (cells %s vs %d, cells.brep %s vs %d bytes, refined %s) - run arrange-m once without REFINE_ZONES on this split first" % (_cc.get("n_cells"), len(cells), (_cc.get("cells_brep") or {}).get("size"), _st.st_size, _cc.get("refined")))
            _seen = set()
            for r_ in _cc.get("cells", []):
                k_ = int(r_["k"])
                if k_ in _seen or not (0 <= k_ < len(cells)): continue
                _seen.add(k_)
                try: f5 = frac125(cells[k_])
                except Exception: f5 = None
                cand.append((-1.0 if f5 is None else f5, k_))
            nz = len(cand)
            print("refine (census): %d cell(s) named by the census of %s (tag %s): %s" % (len(cand), _cc.get("when"), _cc.get("tag"), " ".join("%d" % k_ for _, k_ in cand)), flush=True)
        else:
            with busy("arrange-m: the 125-point fraction of every cell in the zones", 600):
                for m in meta:
                    c = cells[m["k"]]; b = c.BoundBox
                    if not bbox_in_zone(b, 0.0): continue
                    nz += 1
                    f5 = frac125(c)
                    if f5 is None or f5 >= REF_FRAC or f5 <= 1.0 - REF_FRAC: continue
                    cand.append((abs(f5 - 0.5), f5, m["k"]))
            cand.sort(); cand = [(f5, k) for _, f5, k in cand[:REF_MAX]]
            print("refine: %d cell(s) meet the zones; %d are MIXED at 125 points (fraction between %.2f and %.2f); the %d most mixed are re-split" % (nz, len(cand), 1.0 - REF_FRAC, REF_FRAC, len(cand)), flush=True)
        done_cells = set(); newsols = []; drop_cells = set()
        for f5, k in cand:
            if k in done_cells: continue
            if any(o in done_cells for o in nb[k]): refined_rep["skipped"].append([int(k), "a neighbour was refined already (its shared face is split on one side only)"]); continue
            c = cells[k]; b = c.BoundBox
            cross = []
            for i in range(len(F)):
                if i in WALL or REP.get(i, i) in tool_faces: continue
                fb = F[i].BoundBox
                if not (fb.XMax >= b.XMin - 0.05 and fb.XMin <= b.XMax + 0.05 and fb.YMax >= b.YMin - 0.05 and fb.YMin <= b.YMax + 0.05 and fb.ZMax >= b.ZMin - 0.05 and fb.ZMin <= b.ZMax + 0.05): continue
                if D[i]["area"] < 0.05: continue
                try:
                    cm = c.common(F[i])
                    if cm.Area > 0.02: cross.append(i)
                except Exception: pass
            if not cross: refined_rep["skipped"].append([int(k), "no face of the original crosses it"]); continue
            nbs = [o for o in nb[k] if o not in done_cells]
            group = [k] + nbs
            clip = Part.makeBox(b.XLength + 0.02, b.YLength + 0.02, b.ZLength + 0.02, FreeCAD.Vector(b.XMin - 0.01, b.YMin - 0.01, b.ZMin - 0.01))
            tools = []
            for i in cross:
                try:
                    tc = F[i].common(clip)
                    if tc.Faces: tools.append(Part.Compound(tc.Faces))
                except Exception: pass
            if not tools: refined_rep["skipped"].append([int(k), "the crossing faces could not be clipped"]); continue
            try:
                with busy("arrange-m: refine cell %d (+%d neighbours) by %d face(s)" % (k, len(nbs), len(tools)), 300): rr, _ = Part.Compound([cells[g] for g in group]).generalFuse(tools, 1e-5)
                sols = rr.Solids
                v0 = sum(cells[g].Volume for g in group); v1 = sum(x.Volume for x in sols)
                if abs(v1 - v0) > 1e-3 * max(v0, 1.0) or len(sols) < len(group): raise RuntimeError("volume %.3f -> %.3f, %d -> %d cells" % (v0, v1, len(group), len(sols)))
            except Exception as ex:
                refined_rep["skipped"].append([int(k), "the local split refused: %r" % (ex,)]); continue
            for g in group: done_cells.add(g); drop_cells.add(g)
            newsols.extend(sols); refined_rep["cells"] += 1; refined_rep["faces"] += len(tools); refined_rep["new_cells"] += len(sols) - len(group)
            print("  refined cell %d (vol %.2f, 125-pt fraction %.2f) with %d neighbour(s) by %s -> %d cells (%.0fs)" % (k, c.Volume, f5, len(nbs), " ".join("f%d" % (i + 1) for i in cross), len(sols), time.time() - t_r), flush=True)
            if time.time() - t_r > 240: print("  refine: time budget reached - the rest left as they are", flush=True); break
        if drop_cells:
            keep_cells = [c for k_, c in enumerate(cells) if k_ not in drop_cells]; keep_meta = [m for m in meta if m["k"] not in drop_cells]
            cells = keep_cells + newsols; meta = []
            for k_, c in enumerate(cells):
                if k_ < len(keep_meta):
                    m = dict(keep_meta[k_]); m["k"] = k_; meta.append(m)
                else:
                    f5 = frac125(c)
                    if f5 is None:
                        p = c.CenterOfMass; pts = [p]
                        for fc in c.Faces[:4]:
                            try:
                                q = fc.CenterOfMass; u_, v_ = fc.Surface.parameter(q); q = fc.valueAt(u_, v_); n = fc.normalAt(u_, v_)
                                if c.isInside(q - n * 0.2, 1e-6, True): pts.append(q - n * 0.2)
                            except Exception: pass
                        f5 = sum(1 for q in pts if inside_mesh((q.x, q.y, q.z))) / float(len(pts))
                    p = c.CenterOfMass
                    meta.append({"k": k_, "vol": c.Volume, "area": c.Area, "frac": f5, "pt": [p.x, p.y, p.z], "faces": [[fc.hashCode(), -1, round(fc.CenterOfMass.x, 2), round(fc.CenterOfMass.y, 2), round(fc.CenterOfMass.z, 2), round(fc.Area, 1)] for fc in c.Faces], "refined": 1})
            fmap = collections.defaultdict(list); HK = {}; _geo = collections.defaultdict(list)
            for k_, c in enumerate(cells):
                hs_ = [_fkey(fc) for fc in c.Faces]; HK[k_] = hs_
                for h in hs_: fmap[h].append(k_); _geo[h[1:]].append(h)
            for g_, hs_ in _geo.items():
                if len(hs_) > 1:
                    allk = sorted(set(k_ for h in hs_ for k_ in fmap[h]))
                    for h in hs_: fmap[h] = allk
            nb = collections.defaultdict(set)
            for h, ks in fmap.items():
                for a_ in ks:
                    for b_ in ks:
                        if a_ != b_: nb[a_].add(b_)
            print("refined: %d cell(s) by %d face(s) -> %d more cells; %d skipped; faces shared by exactly two cells: %d, by one: %d, by more: %d (%.0fs)" % (refined_rep["cells"], refined_rep["faces"], refined_rep["new_cells"], len(refined_rep["skipped"]), sum(1 for v in fmap.values() if len(v) == 2), sum(1 for v in fmap.values() if len(v) == 1), sum(1 for v in fmap.values() if len(v) > 2), time.time() - t_r), flush=True)
        for sk in refined_rep["skipped"][:10]: print("  refine skipped cell %d: %s" % (sk[0], sk[1]), flush=True)
    mat = {m["k"] for m in meta if m["frac"] >= 0.5}
    SPIKE_V = float(os.environ.get("SPIKE_V", "6.0")); nsp = 0; nsp_full = []
    SPIKE_DENSE = os.environ.get("SPIKE_DENSE", "1") == "1"; sp_drop = []
    for m in meta:
        if m["k"] in mat and m["vol"] < SPIKE_V and m["frac"] < 0.95:
            n_ = nb[m["k"]]
            if any(o not in mat for o in n_) or len(n_) < 4:
                f125 = None; _why = "not measured (SPIKE_DENSE 0)"
                if SPIKE_DENSE:
                    try:
                        f125 = frac125(cells[m["k"]]); _why = "" if f125 is not None else "no fraction: under 6 of the 125 grid points inside the cell's box"
                    except Exception as _ex: f125 = None; _why = "the measurement raised %r" % (_ex,)
                if f125 is not None and f125 >= 0.95: nsp_full.append([int(m["k"]), round(m["vol"], 2), round(m["frac"], 2), round(f125, 2)]); continue
                mat.discard(m["k"]); nsp += 1; sp_drop.append([int(m["k"]), round(m["vol"], 2), round(m["frac"], 2), None if f125 is None else round(f125, 2), _why])
    print("corner spikes dropped: %d%s" % (nsp, ("; %d candidate(s) kept - measured full at 125 points: %s" % (len(nsp_full), " ".join("cell %d (%.2f mm3, %.2f -> %.2f)" % tuple(x) for x in nsp_full[:10]))) if nsp_full else ""), flush=True)
    try:
        _spz = [x for x in sp_drop if bbox_in_zone(cells[x[0]].BoundBox, 0.0)]
        if _spz: print("  dropped where STEP 4 measures (within %.1f mm of a wall or meeting a PROTECT box): %s" % (WALL_ZONE, "; ".join("cell %d (%.2f mm3, %.2f at 5 points, %s)" % (x[0], x[1], x[2], ("%.2f at 125" % x[3]) if x[3] is not None else x[4]) for x in _spz[:12])), flush=True)
    except Exception as _ex: print("  dropped-spike listing skipped: %r" % (_ex,), flush=True)
    keep = set(mat)
    V_SLIVER = float(os.environ.get("V_SLIVER", "0.0")); nsl = 0
    for m in meta:
        if m["k"] in keep and m["vol"] < V_SLIVER and any(o not in keep for o in nb[m["k"]]): keep.discard(m["k"]); nsl += 1
    print("exposed sliver cells dropped: %d" % nsl, flush=True)
    ngp = 0; ngv = 0; gap_zone = []
    PROTECT_GAP = os.environ.get("PROTECT_GAP", "bbox"); GAP_V = float(os.environ.get("GAP_V", "0"))
    for m in meta:
        if m["k"] in mat: continue
        thick = 2.0 * m["vol"] / m["area"] if m["area"] > 0 else 0
        if thick >= GAP: continue
        c = cells[m["k"]]
        if PROTECT_A:
            if PROTECT_GAP == "com":
                cc = c.CenterOfMass
                if any(pb[0] <= cc.x <= pb[1] and pb[2] <= cc.y <= pb[3] and pb[4] <= cc.z <= pb[5] for pb in PROTECT_A): ngp += 1; continue
            elif meets_protect(c.BoundBox, 0.3): ngp += 1; continue
        if GAP_V > 0 and m["vol"] > GAP_V: ngv += 1; continue
        fcs = sorted(c.Faces, key=lambda f_: -f_.Area)[:2]
        if len(fcs) == 2 and all(any(o in mat for o in fmap[_fkey(f_)] if o != m["k"]) for f_ in fcs):
            keep.add(m["k"])
            if bbox_in_zone(c.BoundBox, 0.0):
                cc = c.CenterOfMass; gap_zone.append([int(m["k"]), round(m["vol"], 2), round(thick, 2), [round(cc.x, 1), round(cc.y, 1), round(cc.z, 1)]])
    if PROTECT_A: print("gap cells inside a PROTECT box left as air: %d (by %s)" % (ngp, PROTECT_GAP), flush=True)
    if GAP_V > 0: print("gap cells over GAP_V %.1f mm3 left as air: %d" % (GAP_V, ngv), flush=True)
    if gap_zone:
        print("gap cells FILLED where STEP 4 measures (within %.1f mm of a wall or meeting a PROTECT box): %d - cell, mm3, 2V/A, at" % (WALL_ZONE, len(gap_zone)), flush=True)
        for g_ in sorted(gap_zone, key=lambda g: -g[1])[:12]: print("    cell %d: %.2f mm3, %.2f mm, at %s" % (g_[0], g_[1], g_[2], g_[3]), flush=True)
    # corner edge
    nm_fix = []
    if os.environ.get("MANIFOLD_FIX", "1") == "1":
        try:
            def _ekey(e):
                m_ = e.valueAt(0.5 * (e.FirstParameter + e.LastParameter)); return (e.hashCode(), round(e.Length, 4), round(m_.x, 3), round(m_.y, 3), round(m_.z, 3))
            FR = {m_["k"]: m_ for m_ in meta}; ECELLS = collections.defaultdict(set)
            with busy("arrange-m: the edge map of %d cells (the manifold check)" % len(cells), 900):
                for k, c in enumerate(cells):
                    for e in c.Edges: ECELLS[_ekey(e)].add(k)
            for _rnd in range(6):
                ecount = collections.Counter()
                for k in keep:
                    for fc in cells[k].Faces:
                        if any(o in keep for o in fmap[_fkey(fc)] if o != k): continue
                        for e in fc.Edges: ecount[_ekey(e)] += 1
                bad = [ek for ek, n_ in ecount.items() if n_ > 2]
                if not bad: break
                moved = False
                for ek in bad:
                    around = ECELLS.get(ek, set()); kept_ = [k for k in around if k in keep]; air_ = [k for k in around if k not in keep]
                    if len(kept_) < 2: continue
                    cand = sorted(air_, key=lambda k: -FR[k]["frac"]) if air_ else []
                    if cand and FR[cand[0]]["frac"] > 0.0:
                        keep.add(cand[0]); nm_fix.append(["added", int(cand[0]), round(FR[cand[0]]["frac"], 2), round(FR[cand[0]]["vol"], 2)]); moved = True
                    else:
                        sm = min(kept_, key=lambda k: FR[k]["vol"]); keep.discard(sm); nm_fix.append(["dropped", int(sm), round(FR[sm]["frac"], 2), round(FR[sm]["vol"], 2)]); moved = True
                if not moved: break
            print("non-manifold kept-cell edges resolved: %d change(s)%s" % (len(nm_fix), (" - " + "; ".join("%s cell %d (fraction %.2f, %.2f mm3)" % tuple(x) for x in nm_fix[:12])) if nm_fix else " (none found)"), flush=True)
        except Exception as _ex: print("non-manifold check skipped: %r" % (_ex,), flush=True)
    faces = []; owner = []
    for k in sorted(keep):
        for fc in cells[k].Faces:
            if any(o in keep for o in fmap[_fkey(fc)] if o != k): continue
            faces.append(fc); owner.append(k)
    # INTERNAL
    INT_FIX = os.environ.get("INTERNAL_FIX", "1") == "1"; int_rep = {"checked": 0, "dropped": 0, "area_mm2": 0.0, "at": [], "reverted": False}
    faces_all = list(faces)
    if INT_FIX:
        try:
            EPS_I = 0.002; GC = 2.0; gidx = collections.defaultdict(list); vbox = {}
            for k in keep:
                P_ = [vx.Point for vx in cells[k].Vertexes]
                if not P_: continue
                bx = (min(q.x for q in P_) - 0.5, max(q.x for q in P_) + 0.5, min(q.y for q in P_) - 0.5, max(q.y for q in P_) + 0.5, min(q.z for q in P_) - 0.5, max(q.z for q in P_) + 0.5)
                vbox[k] = bx
                for gi in range(int(math.floor(bx[0] / GC)), int(math.floor(bx[1] / GC)) + 1):
                    for gj in range(int(math.floor(bx[2] / GC)), int(math.floor(bx[3] / GC)) + 1):
                        for gk in range(int(math.floor(bx[4] / GC)), int(math.floor(bx[5] / GC)) + 1):
                            gidx[(gi, gj, gk)].append(k)
            def _kept_at(pt, excl):
                for k2 in gidx.get((int(math.floor(pt.x / GC)), int(math.floor(pt.y / GC)), int(math.floor(pt.z / GC))), ()):
                    if k2 == excl: continue
                    bx = vbox[k2]
                    if not (bx[0] <= pt.x <= bx[1] and bx[2] <= pt.y <= bx[3] and bx[4] <= pt.z <= bx[5]): continue
                    try:
                        if cells[k2].isInside(pt, 1e-7, False): return k2
                    except Exception: pass
                return None
            def _probes(fc):
                out = []
                try:
                    u0, u1, v0, v1 = fc.ParameterRange
                    for a_, b_ in ((0.5, 0.5), (0.3, 0.3), (0.7, 0.7), (0.3, 0.7), (0.7, 0.3), (0.5, 0.2), (0.5, 0.8)):
                        u = u0 + (u1 - u0) * a_; v = v0 + (v1 - v0) * b_
                        if fc.isPartOfDomain(u, v): out.append((fc.valueAt(u, v), fc.normalAt(u, v)))
                        if len(out) >= 3: break
                except Exception: pass
                if not out:
                    try: q_ = fc.CenterOfMass; u, v = fc.Surface.parameter(q_); out.append((fc.valueAt(u, v), fc.normalAt(u, v)))
                    except Exception: pass
                return out
            keepf = []; dropped = []
            with busy("arrange-m: the internal-face check of %d outer faces" % len(faces), 900):
                for fi, (fc, k) in enumerate(zip(faces, owner)):
                    if fi % 1000 == 0 and fi: print("  internal-face check: %d/%d faces (%.0fs)" % (fi, len(faces), time.time() - T1), flush=True)
                    pr = _probes(fc); internal = bool(pr)
                    for q_, n_ in pr:
                        p1 = q_ + n_ * EPS_I; p2 = q_ - n_ * EPS_I
                        try: far = p2 if cells[k].isInside(p1, 1e-7, False) else p1
                        except Exception: internal = False; break
                        if _kept_at(far, k) is None: internal = False; break
                    int_rep["checked"] += 1
                    if internal: dropped.append(fc)
                    else: keepf.append(fc)
            if dropped:
                def _ek(e):
                    m_ = e.valueAt(0.5 * (e.FirstParameter + e.LastParameter)); return (e.hashCode(), round(e.Length, 4), round(m_.x, 3), round(m_.y, 3), round(m_.z, 3))
                _idx = {id(f_): i_ for i_, f_ in enumerate(faces_all)}
                Dset = set(_idx[id(f_)] for f_ in dropped); EF = collections.defaultdict(list)
                for i_, f_ in enumerate(faces_all):
                    for e in f_.Edges: EF[_ek(e)].append(i_)
                _back = 0
                while True:
                    unsafe = set()
                    for i_ in Dset:
                        for e in faces_all[i_].Edges:
                            fs_ = EF[_ek(e)]
                            if (len(fs_) - sum(1 for j_ in fs_ if j_ in Dset)) not in (0, 2): unsafe.add(i_); break
                    if not unsafe: break
                    Dset -= unsafe; _back += len(unsafe)
                if _back: print("  internal-face check: %d of the %d would leave an edge open - kept for arrange-f's internal-triangle drop" % (_back, len(dropped)), flush=True)
                dropped = [faces_all[i_] for i_ in sorted(Dset)]; keepf = [f_ for i_, f_ in enumerate(faces_all) if i_ not in Dset]
            if dropped:
                int_rep["dropped"] = len(dropped); int_rep["area_mm2"] = round(sum(f_.Area for f_ in dropped), 3)
                for f_ in sorted(dropped, key=lambda f_: -f_.Area)[:8]:
                    c_ = f_.CenterOfMass; int_rep["at"].append([round(c_.x, 2), round(c_.y, 2), round(c_.z, 2), round(f_.Area, 3)])
                faces = keepf
            print("internal faces (material on both sides, by geometry): %d of %d outer faces%s" % (len(dropped), int_rep["checked"], (" dropped, %.3f mm2 - the largest at %s" % (int_rep["area_mm2"], "; ".join("(%.1f, %.1f, %.1f) %.3f mm2" % tuple(a_) for a_ in int_rep["at"][:6]))) if dropped else ""), flush=True)
        except Exception as _ex:
            faces = faces_all; print("internal-face check skipped: %r" % (_ex,), flush=True)
    print("  building the outer shell from %d faces" % len(faces), flush=True)
    with busy("arrange-m: Part.Shell of %d faces" % len(faces), 600): sh = Part.Shell(faces)
    if INT_FIX and len(faces) != len(faces_all) and not sh.isClosed():
        int_rep["reverted"] = True
        print("  the internal-face drop left the shell OPEN - reverted: the shell is built from all %d faces as before (arrange-f's internal-triangle drop is the remaining cure)" % len(faces_all), flush=True)
        faces = faces_all
        with busy("arrange-m: Part.Shell of %d faces" % len(faces), 600): sh = Part.Shell(faces)
    print("outer shell: %d faces closed %s valid %s (%.0fs)" % (len(sh.Faces), sh.isClosed(), sh.isValid(), time.time() - T1), flush=True)
    if not sh.isClosed(): _fail("FAIL: the outer shell is not closed - the kept cells do not share their faces (a split that did not keep face identity, or a dropped tool's cells); nothing written")
    sol = Part.Solid(sh)
    if sol.Volume < 0: sol.reverse()
    print("as solid: valid %s vol %.1f (%.1f %%)" % (sol.isValid(), sol.Volume, 100 * sol.Volume / big.Volume), flush=True)
    try:
        with busy("arrange-m: removeSplitter", 600): su = sol.removeSplitter()
        print("unified: faces %d valid %s vol %.1f; faces < 0.01 mm2: %d" % (len(su.Faces), su.isValid(), su.Volume, sum(1 for f in su.Faces if f.Area < 0.01)), flush=True)
        su.exportBrep(os.path.join(RUN, "arr_unified.brep"))
    except Exception as ex: print("unify refused: %r" % (ex,), flush=True)
    # open edges
    # confirmed
    _dev = float(os.environ.get("DEV", "0.03"))
    with busy("arrange-m: the tessellation of the shell solid", 600): V_, T_ = sol.tessellate(_dev)
    # kit rebuild
    _none = []; _small = 0
    try:
        _sc = sol.copy()
        for _i, _f in enumerate(_sc.Faces):
            if _f.Area < 0.01: _small += 1
            try: _tv, _tt = _f.tessellate(_dev)
            except Exception: _tv, _tt = [], []
            if len(_tt) == 0: _none.append((_i, _f))
        print("face census (on a copy, after the shell's tessellation): %d faces; %d under 0.01 mm2; %d give the tessellation NO triangle%s" % (len(_sc.Faces), _small, len(_none), ":" if _none else ""), flush=True)
        for _i, _f in _none[:20]:
            _c = _f.CenterOfMass; _b = _f.BoundBox
            print("    face %d at (%.1f, %.1f, %.1f) area %.4f mm2, extent %.2f x %.2f x %.2f, %s, %d edges" % (_i, _c.x, _c.y, _c.z, _f.Area, _b.XLength, _b.YLength, _b.ZLength, _f.Surface.__class__.__name__, len(_f.Edges)), flush=True)
        del _sc
    except Exception as _ex: print("face census skipped: %r" % (_ex,), flush=True)
    V_ = np.array([[p.x, p.y, p.z] for p in V_], float); T_ = np.array(T_, int)
    key = np.round(V_ / float(os.environ.get("WELD", "0.01"))).astype(np.int64); _, idx, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1)
    V2 = V_[idx]; T2 = inv[T_]
    T2 = T2[(T2[:, 0] != T2[:, 1]) & (T2[:, 1] != T2[:, 2]) & (T2[:, 0] != T2[:, 2])]
    h = R.mesh_health(V2, T2)
    print("mesh: %d verts %d tris; health %s (%.0fs)" % (len(V2), len(T2), h, time.time() - T1), flush=True)
    if h != (0, 0):
        try:
            _E = np.sort(np.concatenate([T2[:, [0, 1]], T2[:, [1, 2]], T2[:, [2, 0]]]), axis=1)
            _u, _cnt = np.unique(_E, axis=0, return_counts=True); _bad = _u[_cnt != 2]
            _adj = collections.defaultdict(set)
            for _a, _b in _bad: _adj[int(_a)].add(int(_b)); _adj[int(_b)].add(int(_a))
            _seen = set(); _chains = []
            for _v0 in list(_adj):
                if _v0 in _seen: continue
                _st = [_v0]; _comp = []
                while _st:
                    _v = _st.pop()
                    if _v in _seen: continue
                    _seen.add(_v); _comp.append(_v); _st.extend(_adj[_v] - _seen)
                _chains.append(_comp)
            _chains.sort(key=len, reverse=True)
            print("  open-edge chains in the raw mesh: %d (the finish's work); the largest:" % len(_chains), flush=True)
            for _comp in _chains[:8]:
                _P = V2[_comp]; _lo = _P.min(axis=0); _hi = _P.max(axis=0)
                print("    %d vertices, extent %.1f x %.1f x %.1f mm at (%.1f, %.1f, %.1f)" % (len(_comp), _hi[0] - _lo[0], _hi[1] - _lo[1], _hi[2] - _lo[2], _P[:, 0].mean(), _P[:, 1].mean(), _P[:, 2].mean()), flush=True)
        except Exception as _ex: print("  open-edge chains: not located (%r)" % (_ex,), flush=True)
    import struct
    # kit rebuild
    out = os.path.join(RUN, "arr_base_raw.stl")
    with open(out, "wb") as f:
        f.write(b"\0" * 80); f.write(struct.pack("<I", len(T2)))
        for t in T2:
            a, b, c = V2[t[0]], V2[t[1]], V2[t[2]]; n = np.cross(b - a, c - a); ln = np.linalg.norm(n); n = n / ln if ln > 0 else n
            f.write(struct.pack("<3f", *n)); f.write(struct.pack("<9f", *a, *b, *c)); f.write(b"\0\0")
    print("wrote", out, "- RAW: `kit rebuild arrange-f` makes arr_base.stl from it (the gate)", flush=True)
    if h != (0, 0): print("  the raw mesh is not watertight (%s): the finish's job; a FINAL that does not close there is the finding" % (h,), flush=True)
    sol.exportBrep(os.path.join(RUN, "arr_shell_solid.brep"))
    # ORIGINAL
    # over the
    # recorded
    ZONE_REP = {}; ATTR = []
    try:
        import vtk
        from vtk.util import numpy_support as nps
        with busy("arrange-m: the BASE census (samples, distances, the attribution)", 900):
            MVa = np.asarray(MV, float); MTa = np.asarray(MT, int)
            def _on_plane(Vv, Tt):
                m = np.zeros(len(Tt), bool)
                for w in WALLS_M:
                    c_ = np.array(w[:3], float); n_ = np.array(w[3:], float); n_ = n_ / max(np.linalg.norm(n_), 1e-12)
                    m |= np.all(np.abs((Vv[Tt] - c_) @ n_) < 1e-3, axis=1)
                return m
            TOs = MTa[~_on_plane(MVa, MTa)]
            def _dense(Vv, Tt, sp):
                A, B, C = Vv[Tt[:, 0]], Vv[Tt[:, 1]], Vv[Tt[:, 2]]
                L = np.maximum(np.maximum(np.linalg.norm(B - A, axis=1), np.linalg.norm(C - B, axis=1)), np.linalg.norm(A - C, axis=1))
                k_ = np.maximum(1, np.ceil(L / sp).astype(int)); out = []; outn = []
                nrm = np.cross(B - A, C - A); nrm /= np.maximum(np.linalg.norm(nrm, axis=1), 1e-12)[:, None]
                for kk in np.unique(k_):
                    m = k_ == kk; ij = np.array([(i, j) for i in range(kk + 1) for j in range(kk + 1 - i)], float) / kk
                    pts = (A[m][:, None, :] + (B[m] - A[m])[:, None, :] * ij[None, :, 0:1] + (C[m] - A[m])[:, None, :] * ij[None, :, 1:2])
                    out.append(pts.reshape(-1, 3)); outn.append(np.repeat(nrm[m], len(ij), axis=0))
                return (np.vstack(out), np.vstack(outn)) if out else (np.zeros((0, 3)), np.zeros((0, 3)))
            SO, NO = _dense(MVa, TOs, 0.15)
            inw = np.ones(len(SO), bool)
            for w in WALLS_M:
                c_ = np.array(w[:3], float); n_ = np.array(w[3:], float); n_ = n_ / max(np.linalg.norm(n_), 1e-12); inw &= ((SO - c_) @ n_) <= 1e-4
            SO, NO = SO[inw], NO[inw]
            zones = []; inz = np.zeros(len(SO), bool)
            for k_, w in enumerate(WALLS_M):
                c_ = np.array(w[:3], float); n_ = np.array(w[3:], float); n_ = n_ / max(np.linalg.norm(n_), 1e-12)
                m = np.abs((SO - c_) @ n_) <= WALL_ZONE; zones.append(("wall %d (n %s)" % (k_, [round(float(v), 2) for v in n_]), m)); inz |= m
            for k_, b in enumerate(PROTECT_A):
                m = (SO[:, 0] >= b[0]) & (SO[:, 0] <= b[1]) & (SO[:, 1] >= b[2]) & (SO[:, 1] <= b[3]) & (SO[:, 2] >= b[4]) & (SO[:, 2] <= b[5]); zones.append(("PROTECT box %d" % k_, m)); inz |= m
            idx = np.nonzero(inz)[0]; SZ = SO[idx]; NZ = NO[idx]
            pd = vtk.vtkPolyData(); pts_ = vtk.vtkPoints(); pts_.SetData(nps.numpy_to_vtk(np.ascontiguousarray(V2, dtype=float), deep=True)); pd.SetPoints(pts_)
            ca = vtk.vtkCellArray(); conn = np.hstack([np.full((len(T2), 1), 3), T2]).astype(np.int64).ravel(); ca.SetCells(len(T2), nps.numpy_to_vtkIdTypeArray(conn, deep=True)); pd.SetPolys(ca)
            ipd = vtk.vtkImplicitPolyDataDistance(); ipd.SetInput(pd)
            xin = nps.numpy_to_vtk(np.ascontiguousarray(SZ, dtype=float), deep=True); dout = vtk.vtkDoubleArray(); ipd.FunctionValue(xin, dout)
            dZ = np.abs(nps.vtk_to_numpy(dout))
            vis = np.ones(len(SZ), bool); far = np.nonzero(dZ > 0.1)[0]
            for i_ in far:
                p_ = SZ[i_]; n_ = NZ[i_]
                if inside_mesh(tuple(p_ + n_ * 0.15)) and inside_mesh(tuple(p_ - n_ * 0.15)): vis[i_] = False
            zi = {int(i_): j_ for j_, i_ in enumerate(idx)}
            for name, m in zones:
                sel = np.array([zi[int(i_)] for i_ in np.nonzero(m)[0]], int)
                sel = sel[vis[sel]] if len(sel) else sel
                if len(sel) < 5: continue
                d_ = dZ[sel]; iw = int(np.argmax(d_)); worst = SZ[sel][iw]
                r_ = {"n": int(len(sel)), "base_p99": round(float(np.percentile(d_, 99)), 3), "base_max": round(float(d_.max()), 3), "base_worst_at": [round(float(v), 1) for v in worst]}
                ZONE_REP[name] = r_
                print("BASE vs ORIGINAL at %s: %d visible samples - p99 %.3f max %.3f at %s%s" % (name, r_["n"], r_["base_p99"], r_["base_max"], r_["base_worst_at"], "   <-- over the seam ceiling: STEP 4 will measure this" if r_["base_max"] > 0.15 else ""), flush=True)
                if r_["base_max"] <= 0.15: continue
                pw = FreeCAD.Vector(*[float(v) for v in worst]); vx = Part.Vertex(pw)
                def _status(i):
                    if i in WALL: return "WALL (window cap)"
                    r0 = REP.get(i, i)
                    if r0 in use: return "TOOL f%d" % (i + 1) if r0 == i else "on tool f%d's own surface (SAME group)" % (r0 + 1)
                    if r0 in DUPS: return "DUPLICATE of tool f%d (max %.3f under the bound %.2f): merged away" % (DUPS[r0][0], DUPS[r0][1], DUPS[r0][2])
                    if not design_face(i): return "SMALL %.2f mm2 (under A_SMALL %.1f)" % (D[i]["area"], A_SMALL)
                    nsk = D[i].get("skin", 0)
                    if not D[i]["wpts"]: return ("all %d window samples SKIN (material behind thinner than T_MIN): not a design surface" % nsk) if nsk else "no window samples: not a design surface"
                    if i in GAPW: return "gap wall (f%d, %.1f mm2) - its group f%d not taken" % (i + 1, D[i]["area"], r0 + 1)
                    return "its group f%d not taken (%.1f mm2)" % (r0 + 1, D[i]["area"])
                orig_faces = []
                for i in range(len(F)):
                    fb = F[i].BoundBox
                    if not (fb.XMin - 0.3 <= pw.x <= fb.XMax + 0.3 and fb.YMin - 0.3 <= pw.y <= fb.YMax + 0.3 and fb.ZMin - 0.3 <= pw.z <= fb.ZMax + 0.3): continue
                    try: dd = F[i].distToShape(vx)[0]
                    except Exception: continue
                    if dd < 0.05: orig_faces.append((i, round(dd, 3), _status(i)))
                def _tools_of(c):
                    out = []
                    for fc in c.Faces:
                        try: cc = fc.CenterOfMass; nn = fc.normalAt(*fc.Surface.parameter(cc))
                        except Exception: out.append("?"); continue
                        hit = None
                        for r in use:
                            try:
                                if abs(signed(r, cc)) < 0.03 and abs(nn.dot(D[r]["n"])) > 0.7: hit = "f%d" % (r + 1); break
                            except Exception: pass
                        if hit is None and on_wall_pt(cc, nn): hit = "wall"
                        out.append(hit or "?")
                    return out
                def on_wall_pt(cc, nn):
                    for w in WALLS_M:
                        c_ = FreeCAD.Vector(*w[:3]); n_ = FreeCAD.Vector(*w[3:]); n_.normalize()
                        if abs((cc - c_).dot(n_)) < 0.05 and abs(nn.dot(n_)) > 0.9: return True
                    return False
                best_k = None; best_d = 9e9; in_air = None
                for m_ in meta:
                    c = cells[m_["k"]]; b = c.BoundBox
                    if not (b.XMin - 0.3 <= pw.x <= b.XMax + 0.3 and b.YMin - 0.3 <= pw.y <= b.YMax + 0.3 and b.ZMin - 0.3 <= pw.z <= b.ZMax + 0.3): continue
                    if m_["k"] in keep:
                        try: dd = c.distToShape(vx)[0]
                        except Exception: continue
                        if dd < best_d: best_d = dd; best_k = m_["k"]
                    elif in_air is None and c.isInside(pw, 1e-4, True): in_air = m_["k"]
                a_ = {"zone": name, "at": r_["base_worst_at"], "base_off_mm": r_["base_max"], "original_faces": [[int(i) + 1, dd, st] for i, dd, st in orig_faces]}
                print("  the original's faces there: %s" % ("; ".join("f%d %s" % (i + 1, st) for i, dd, st in orig_faces) or "none within 0.05 mm (the sample is between faces)"), flush=True)
                if best_k is not None:
                    m_ = meta[best_k]; c = cells[best_k]; f5 = frac125(c)
                    a_["base_cell"] = {"k": int(best_k), "vol": round(m_["vol"], 2), "frac5": round(m_["frac"], 2), "frac125": None if f5 is None else round(f5, 2), "gap_filled": best_k not in mat, "refined": bool(m_.get("refined")), "tools": _tools_of(c)}
                    print("  the base's surface there belongs to kept cell %d: %.2f mm3, fraction %.2f at 5 points / %s at 125, %s, bounded by %s" % (best_k, m_["vol"], m_["frac"], "-" if f5 is None else "%.2f" % f5, "GAP-FILLED (an air cell the gap rule filled)" if best_k not in mat else ("material (refined)" if m_.get("refined") else "material"), " ".join(a_["base_cell"]["tools"])), flush=True)
                if in_air is not None:
                    m_ = meta[in_air]; c = cells[in_air]; f5 = frac125(c)
                    a_["air_cell"] = {"k": int(in_air), "vol": round(m_["vol"], 2), "frac5": round(m_["frac"], 2), "frac125": None if f5 is None else round(f5, 2), "tools": _tools_of(c)}
                    print("  the original's surface there lies inside DROPPED cell %d (air in the base): %.2f mm3, fraction %.2f at 5 points / %s at 125, bounded by %s%s" % (in_air, m_["vol"], m_["frac"], "-" if f5 is None else "%.2f" % f5, " ".join(a_["air_cell"]["tools"]), " - material the base is MISSING" if (f5 or 0) > 0.05 else ""), flush=True)
                ATTR.append(a_)
        # over the
        try:
            _cb = os.path.join(RUN, "cells.brep"); _st = os.stat(_cb); _rows = []
            for a_ in ATTR:
                _fs = [int(f_[0]) for f_ in a_.get("original_faces", [])]
                if a_.get("base_cell"): _rows.append({"k": int(a_["base_cell"]["k"]), "role": "kept", "zone": a_["zone"], "at": a_["at"], "faces": _fs})
                if a_.get("air_cell"): _rows.append({"k": int(a_["air_cell"]["k"]), "role": "dropped", "zone": a_["zone"], "at": a_["at"], "faces": _fs})
            _cc = {"tag": TAG, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "cells_brep": {"size": _st.st_size, "mtime": int(_st.st_mtime)}, "n_cells": len(cells), "refined": bool(refined_rep["cells"]), "cells": _rows}
            _cn = "census_cells_refined.json" if refined_rep["cells"] else "census_cells.json"
            json.dump(_cc, open(os.path.join(RUN, _cn), "w"), indent=1)
            print("census cells: %d named (%s) -> %s%s" % (len(_rows), " ".join("%s %d" % (r_["role"], r_["k"]) for r_ in _rows[:12]) or "none", _cn, "" if refined_rep["cells"] else " - `--set REFINE_ZONES=census` on the next arrange-m re-splits them"), flush=True)
        except Exception as _ex2: print("census cells not written: %r" % (_ex2,), flush=True)
    except Exception as _ex: print("BASE census skipped: %r" % (_ex,), flush=True)
    # kit accept
    rec = {"tag": TAG, "source": SRC, "window": WIN, "levers": {k: os.environ.get(k) for k in ("A_SMALL", "LEVEL", "LEVEL_DEG", "LEVEL0", "LEVEL0_DEG", "DUP_FRAC", "GAP", "SPIKE_V", "V_SLIVER", "PLANE_TOL", "TOL", "T_MIN", "V_MIN")},
           "design_surfaces": [{"face": int(r) + 1, "kind": D[r]["kind"], "area_mm2": round(D[r]["area"], 2), "plane": bool(D[r]["plane"]),
                                "normal": [round(D[r]["n"].x, 4), round(D[r]["n"].y, 4), round(D[r]["n"].z, 4)], "centre": [round(D[r]["c"].x, 3), round(D[r]["c"].y, 3), round(D[r]["c"].z, 3)],
                                "merged_into_it": [int(i) + 1 for i in range(len(F)) if REP.get(i, i) == r and i != r]} for r in use],
           "walls": [int(i) + 1 for i in sorted(WALL)], "gap_walls": [int(i) + 1 for i in sorted(GAPW)],
           "cells": {"total": len(cells), "material": int(len(mat)), "kept": int(len(keep)), "spikes_dropped": int(nsp), "gap_cells_filled": int(sum(1 for m_ in meta if m_["k"] in keep and m_["k"] not in mat))},
           "tools_dropped": M.get("tools_dropped", []), "dups": M.get("dups", {}),
           "levers_31af": {k_: os.environ.get(k_) for k_ in ("PROTECT", "PROTECT_GAP", "GAP_V", "LEVEL_WALL", "LEVEL_VERTS", "PROTECT_FACES", "REFINE_ZONES", "REFINE_FRAC", "REFINE_MAX", "WALL_ZONE", "SPLIT")},
           "gap_cells_filled_in_zones": gap_zone, "gap_cells_left_as_air": {"protect": int(ngp), "over_gap_v": int(ngv)}, "refined": refined_rep,
           "same_split_31ai": [[int(i) + 1, int(r) + 1, round(float(dv), 3)] for i, r, dv in SAME_SPLIT], "manifold_fix_31ai": nm_fix, "spikes_measured_full_31ai": nsp_full, "internal_faces_31aj": int_rep, "spikes_dropped_31aj": sp_drop[:200], "frac_box_31aj": FRAC_BOX, "base_vs_original_zones": ZONE_REP, "attribution": ATTR,
           "volume_mm3": {"original": round(big.Volume, 1), "arrangement": round(sol.Volume, 1)}, "mesh_raw": {"triangles": int(len(T2)), "health_open_nonmanifold": list(h), "faces_without_triangles": int(len(_none)), "faces_under_0p01mm2": int(_small)}}
    json.dump(rec, open(os.path.join(RUN, "REBUILD_arrangement.json"), "w"), indent=1)
    print("RECORD -> %s (%d design surfaces)" % (os.path.join(RUN, "REBUILD_arrangement.json"), len(use)), flush=True)

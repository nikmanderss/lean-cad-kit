"""selftest_skin5.py - kit 31aw (2026-10-08), without a kernel: THE FACE THROUGH ITS EDGES and the client's answers of 10-08.
the client: "No to voxel smoothing"; "More lines should be added as needed to give the face the required shape"; "Merge smooth preferred with fallback
to stitch"; "If splitting faces is needed add a wire to the wireframe"; "2 commands, 3 picture sets ... confirm with hit/miss picture type";
"If a trial passes, do not rebuild it, do not reinsert it. Yes to orbit, 2 reviewers"; "stop calling it a window"; "two copies, not unlimited.
Best so far and working".
Cases: sk_span's numpy geometry (the loop ordered end to end, corners by turn, four corners on a 3- / 5-cornered face, the side pieces split
at every joint, a planar boundary); the picture cache (a frame drawn from the same key is a HIT and stays; another key removes it); the
composites skin-layout / skin-lines (their inner steps in order, NET_PICS=0 inside skin-lines); the trial's second review and its acceptance
(two shards over the real model's frames; ok refused before them; PROMOTED: body_trial.brep -> body_new.brep, the piece judged ok, review_body a
COMPLETE review, a real STEP 2 / skin-build of the same piece refused after it); the design file (sections to levers; DESIGN=best); the levers
known to the runner; "window" gone from the runner's and the scripts' messages (the frozen region "windows" untouched); the scripts' 31aw lines."""
import os, sys, json, shutil, tempfile, hashlib, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kit_rebuild as KR
ok = 0; bad = 0
def check(cond, what):
    global ok, bad
    if cond: ok += 1; print("  ok   " + what)
    else: bad += 1; print("  FAIL " + what)
md = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()
def w(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w" if isinstance(s, str) else "wb").write(s)

def opened31cb(root_, *pngs):
    import leangate as lg_31cb, time as tm_31cb
    d_ = os.path.join(lg_31cb.records_root(root_), ".claude"); os.makedirs(d_, exist_ok=True)
    with open(os.path.join(d_, "looks.jsonl"), "a") as fh_:
        for p_ in pngs: fh_.write(json.dumps({"png": p_, "png_n": os.path.normcase(os.path.abspath(p_)).replace("\\", "/"), "opened": tm_31cb.time(), "when": "now", "box": None, "defective": False}) + "\n")

root = tempfile.mkdtemp(prefix="skin5_"); job = "JOB5"; folder = os.path.join(root, "claude_code", "jobs", job); sk = os.path.join(folder, "skin")
os.makedirs(os.path.join(sk, "review")); os.makedirs(os.path.join(folder, "review_body")); os.makedirs(os.path.join(root, ".claude"))
json.dump({"window": [-6.0, 6.0, 0.0, 4.0, -1.0, 1.0], "planes": []}, open(os.path.join(folder, "REBUILD_region.json"), "w"))
try:
    os.environ["RUN"] = folder; os.environ.pop("PICS", None)
    sys.path.insert(0, os.path.join(HERE, "rebuild"))
    import sk_span as SP
    import sk_lib as K
    _c3 = {0: np.array([10.0, -110.0, 80.0]), 1: np.array([-10.0, -110.0, 80.0]), 2: np.array([0.1, -120.0, 85.0]), 3: np.array([5.0, -130.0, 70.0]), 4: np.array([-5.0, -130.0, 71.5]), 5: np.array([-5.0, -90.0, 70.0])}
    _tp, _tm = SP.twin_pairs(_c3, np.array([1.0, 0.0, 0.0]), 0.0, 2.0)
    check(_tp == {0: 1, 1: 0, 3: 4, 4: 3} and _tm == {0, 3}, "31br A3: twin_pairs - 0/1 and 3/4 (1.5 mm off) paired both ways, the + side the master; the face on the plane and the unmatched face left out %s %s" % (_tp, _tm))
    _tp2, _tm2 = SP.twin_pairs(_c3, np.array([1.0, 0.0, 0.0]), 0.0, 1.0)
    check(_tp2 == {0: 1, 1: 0} and _tm2 == {0}, "31br A3: a tighter tolerance drops the 1.5 mm pair (%s)" % (_tp2,))
    check(SP.twin_pairs({}, np.array([1.0, 0.0, 0.0]), 0.0) == ({}, set()), "31br A3: no faces, no pairs")
    _sbd3 = open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read()
    check("def _a3_mirror_surface(" in _sbd3 and "SP.twin_pairs(_cen3, MP[0], MP[1], TWIN_CEN_MM)" in _sbd3 and "_a3_mirror_surface(pi, pol_s, mid_s, subs_)" in _sbd3 and "_a3_mirror_surface(pi, polys_, None)" in _sbd3
          and 'TWIN_MIRROR = os.environ.get("TWIN_MIRROR", "1") == "1"' in _sbd3 and "spanned on its own (31br A3)" in _sbd3 and "chg = sorted(chg, key=lambda p3:" in _sbd3,
          "31br A3: sk_build pairs the changed faces, spans the masters first, gives a twin its master's surface reflected (whole face and per piece) and says the fallback")
    def poly(a, b, n=30): return np.linspace(0, 1, n)[:, None] * (np.asarray(b, float) - np.asarray(a, float))[None, :] + np.asarray(a, float)[None, :]
    quad = [poly((0, 0, 0), (10, 0, 0)), poly((10, 0, 0), (10, 6, 0)), poly((0, 6, 0), (10, 6, 0)), poly((0, 6, 0), (0, 0, 0))]
    loop, starts, order = SP.order_loop(quad)
    check(len(starts) == 4 and [o[0] for o in order] == [0, 1, 2, 3] and order[2][1] is True, "the boundary ordered end to end, a backwards edge reversed")
    cs = SP.corners_of(loop, starts); q, how = SP.four_corners(loop, starts)
    check(len(cs) == 4 and q == cs and how == "4 corner(s)", "four corners at the four right-angle joints")
    pieces = SP.side_pieces(loop, starts, q)
    check([len(p) for p in pieces] == [1, 1, 1, 1], "each side one piece (no joint inside a side)")
    isp, c, n = SP.planar(loop)
    check(isp and abs(abs(n[2]) - 1) < 1e-9, "a flat boundary is seen as planar (the face is a plane)")
    k_, pay_, inf_ = SP.span_face(quad)
    check(k_ == "plane" and inf_["how"] == "planar boundary", "span_face: a planar boundary with no added line -> a plane, no kernel needed")
    pent = [poly((0, 0, 0), (10, 0, 1)), poly((10, 0, 1), (12, 4, 1)), poly((12, 4, 1), (6, 8, 0)), poly((6, 8, 0), (0, 5, 1)), poly((0, 5, 1), (0, 0, 0))]
    loop5, st5, _ = SP.order_loop(pent); q5, how5 = SP.four_corners(loop5, st5); p5 = SP.side_pieces(loop5, st5, q5)
    check(len(SP.corners_of(loop5, st5)) == 5 and how5 == "5 corner(s)" and len(q5) == 4 and sorted(len(p) for p in p5) == [1, 1, 1, 2], "a 5-cornered face: four corners chosen, the fifth a joint inside one side (two pieces)")
    tri = [poly((0, 0, 0), (12, 0, 0)), poly((12, 0, 0), (6, 5, 0.5)), poly((6, 5, 0.5), (0, 0, 0))]
    loop3, st3, _ = SP.order_loop(tri); q3, how3 = SP.four_corners(loop3, st3)
    check(how3 == "3 corner(s)" and len(q3) == 4, "a 3-cornered face: the longest side split so the patch has four sides")
    try:
        SP.order_loop([poly((0, 0, 0), (10, 0, 0)), poly((10, 0, 0), (10, 6, 0)), poly((10, 6, 0), (0, 6, 0)), poly((0, 6, 0), (0, 1, 0))]); gap = False
    except ValueError: gap = True
    check(gap, "a boundary that does not close is refused (a 1 mm gap)")
    check(SP.SIDE_TOL <= 1e-4 and SP.PLATE_FIT <= 0.01 and SP.PLATE_MAX_DEG >= 60, "the span's own numbers: sides within 1e-5, the plate's border within 0.005, a face turning past 80 deg is no plate")
    K.OUT = os.path.join(sk, "review"); K._PICS_REC = {}; K.PIC_HITS.clear(); K.PIC_MISSES.clear()
    w(os.path.join(sk, "a.json"), '{"a": 1}'); k1 = K.pic_key(os.path.join(sk, "a.json"), pics="quick"); k2 = K.pic_key(os.path.join(sk, "a.json"), pics="full")
    p1 = os.path.join(K.OUT, "LAYOUT_01_x.png"); w(p1, b"png")
    check(not K.pic_hit(p1, k1), "a frame with no record is not a HIT")
    K.pic_mark(p1, k1)
    check(K.pic_hit(p1, k1) and os.path.isfile(os.path.join(K.OUT, ".pictures.json")), "a frame marked with its key is a HIT next time (the record on disk)")
    check(not K.pic_hit(p1, k2), "another picture set (full) is another key - not a HIT")
    n_ = K.clear_frames("LAYOUT_", k1)
    check(n_ == 0 and os.path.isfile(p1), "clear_frames keeps the HIT frame")
    w(os.path.join(sk, "a.json"), '{"a": 2}'); k3 = K.pic_key(os.path.join(sk, "a.json"), pics="quick")
    n_ = K.clear_frames("LAYOUT_", k3)
    check(n_ == 1 and not os.path.isfile(p1) and k3 != k1, "the input changed: the frame is removed (a MISS to draw)")
    check("MISS" in K.pic_report() and "HIT" in K.pic_report(), "the report line names both counts")
    class G:
        @staticmethod
        def session(root): return {}
    class Kit:
        LEVER_PREFIXES = ("LK_", "KITX_")
        def __init__(self, root): self.ROOT = root; self.HERE = HERE; self.G = G; self.ENV = {}
        @staticmethod
        def _opt(args, name, default=None): return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default
        @staticmethod
        def _all(args, name): return [args[i + 1] for i, a in enumerate(args) if a == name and i + 1 < len(args)]
        def freecad(self): return "freecadcmd"
        def _wallclock(self): raise RuntimeError("THE GATES PASSED")
        def cmd_state(self, a): pass
    kit = Kit(root); out = []
    say = lambda *a: out.append(" ".join(str(x) for x in a))
    import builtins
    def run(*a):
        out.clear(); p0 = builtins.print; builtins.print = lambda *x, **k: out.append(" ".join(str(y) for y in x))
        try: return KR.cmd(list(a), kit)
        except RuntimeError as ex: return "passed" if "GATES PASSED" in str(ex) else str(ex)
        finally: builtins.print = p0
    w(os.path.join(folder, "piece.stl"), b"\0" * 84); w(os.path.join(folder, "body.brep"), b"a body"); w(os.path.join(folder, "wall_caps.brep"), b"caps")
    B = "BODY=" + os.path.join(folder, "body.brep")
    for lv in ("FIT", "CORNER_DEG", "SPAN_STEP", "OFF_TOL", "ADD", "FILLETS", "ADD_SNAP", "NET_PICS", "DESIGN"):
        check(lv in KR.LEVERS, "the runner knows the 31aw lever %s" % lv)
    # skin-layout  first refusal
    w(os.path.join(sk, "patches_labels.json"), '{"patches": [], "merge_smooth": {}}')
    rc = run("skin-layout", "--job", job, "--tag", "c1", "--set", B)
    o = "\n".join(out)
    check("skin-layout: skin-rim" in o and rc == "passed", "skin-layout runs skin-rim (its gates: the feature map first) %s" % rc)
    json.dump({"plane": "x 0", "when": "2026-10-08 09:00:00", "tag": "sl1", "step": "skin-labels"}, open(os.path.join(sk, "MIRROR_DECISION.json"), "w"))
    rc = run("skin-layout", "--job", job, "--tag", "c2", "--set", B)
    check("skin-rim -> skin-mirror" in "\n".join(out), "a symmetric edit: skin-layout = skin-rim then skin-mirror WHAT=layout (the mirror's picture set after the layout's)")
    rc = run("skin-lines", "--job", job, "--tag", "c3", "--set", B)
    o = "\n".join(out)
    check("skin-lines: skin-network -> skin-frame -> skin-wires" in o and rc == 2 and "stopped at skin-network" in o, "skin-lines = network -> frame -> wires; it stops at skin-network's first gate with the reason")
    # skin-source  voxel step is now getting skipped
    for st_ in ("arrange", "arrange-m", "arrange-f", "blend", "repair", "review"):
        rc = run(st_, "--job", job, "--tag", "v1", "--set", B, "--set", "R=3")
        check(rc == 2 and "voxel step is now getting skipped" in "\n".join(out), "31ba: %s is SHELVED (refused without SHELVED_OK) [%s]" % (st_, "\n".join(out)[-200:].replace("\n", " | ")))
    check("skin-source" in [x[0] for x in KR.STEPS] and KR.STEPS[[x[0] for x in KR.STEPS].index("skin-source")][1] == "sk_source.py", "31ba: kit rebuild skin-source is a step (sk_source.py)")
    check(all(st_ in KR.SHELVED for st_ in KR.VOXEL) and "skin-source" in KR.SKIN, "31ba: the six voxel steps are in SHELVED; skin-source is a skin step")
    src_ = os.path.join(folder, "source.stl"); pc_ = os.path.join(folder, "piece.stl")
    w(pc_, b"voxel"); d_ = KR.step_defaults("skin-points", folder, "")
    if d_ is not None:
        check(os.path.basename(d_.get("STL", "")) == "piece.stl", "31ba: a job with no source.stl and a piece.stl (a SHELVED_OK voxel run): the skin steps' STL is piece.stl (%s)" % os.path.basename(d_.get("STL", "")))
    w(src_, b"source mesh")
    rc = run("skin-points", "--job", job, "--tag", "v2", "--set", B, "--plan")
    check("source.stl" in "\n".join(out), "31ba: with source.stl in the job, the skin steps' STL is the source mesh (--plan prints it)")
    rc = run("skin-source", "--job", job, "--tag", "v3", "--set", B, "--plan")
    check(rc != 2 or "wall_caps.brep is missing" not in "\n".join(out), "31ba: skin-source needs no caps (it runs before STEP 1)")
    sksrc = open(os.path.join(HERE, "rebuild", "sk_source.py"), encoding="utf-8").read()
    check("source.stl" in sksrc and "MeshPart" in sksrc and "weld(" in sksrc and "REBUILD_source.json" in sksrc, "31ba: sk_source tessellates content.brep (MeshPart, welded) -> source.stl + its record")
    spn = open(os.path.join(HERE, "rebuild", "sk_span.py"), encoding="utf-8").read(); sbd = open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read()
    check('"nurbs", bs, ninfo' in spn and "def nurbs_face" in spn and 'NURBS_RIM' in spn and "_nurbs_args(pi)" in sbd and '"nurbs": return "nurbs"' in sbd, "31az: the NURBS rung is first in span_face; sk_build names it (rung nurbs)")
    swr = open(os.path.join(HERE, "rebuild", "sk_wires.py"), encoding="utf-8").read(); slb = open(os.path.join(HERE, "rebuild", "sk_lib.py"), encoding="utf-8").read()
    check("no longer drawn" not in swr and "geometry that was wanted to be kept" in swr and 'WIRE_OCC' in swr and "def view_occluded" in slb and "def draw_occluded" in slb,
          "31bb: the trace is drawn again (the source mesh is the original - kept geometry); the WIRE_* frames drawn with hidden lines hidden")
    sys.path.insert(0, os.path.join(HERE, "rebuild")); import sk_lib as SKL
    try:
        import scipy
        HAVE_SCIPY = True
    except ImportError:
        HAVE_SCIPY = False; print("  skip 31bb: fid_labels not exercised - this python has no scipy (run the suite under FreeCAD's python for it)")
    if HAVE_SCIPY:
        fid = np.array([0, 0, 1, 1, 2, 2, 3, 3]); ta = np.arange(7); tb = np.arange(1, 8); Cn = np.c_[np.arange(8, dtype=float), np.zeros(8), np.zeros(8)]
        dih = np.ones(7, bool); dih[5] = False
        tl, nabs, nown = SKL.fid_labels(fid, [0, 2], ta, tb, dih, Cn)
        check(list(tl[:2]) == [0, 0] and list(tl[4:6]) == [2, 2], "31bb: a face with a point keeps its own triangles (exact labels)")
        check(list(tl[2:4]) == [0, 0], "31bb: a face with no point is absorbed WHOLE by one kept neighbour (its far edge stays a B-rep edge) - %s" % tl[2:4].tolist())
        check(tl[6] == tl[7] and tl[6] == 2 and nown == 0 and nabs == 4, "31bd: an unseeded face behind a crease is absorbed across it (no point = not kept, whatever the angle); counts %d absorbed, %d own" % (nabs, nown))
        tl3, nabs3, nown3 = SKL.fid_labels(np.array([0, 0, 1, 1, 5, 5, 6, 6]), [0], np.array([0, 1, 2, 4, 5, 6]), np.array([1, 2, 3, 5, 6, 7]), np.ones(6, bool), None)
        check(list(tl3[:4]) == [0, 0, 0, 0] and tl3[4] == tl3[5] == tl3[6] == tl3[7] and tl3[4] <= -30000 and nown3 == 1, "31bd: faces nothing kept touches become ONE face of their own (connected group) - %s" % tl3.tolist())
        tl2, nabs2, nown2 = SKL.fid_labels(fid, [0, 1, 2, 3], ta, tb, dih, Cn)
        check(list(tl2) == list(fid) and nabs2 == 0 and nown2 == 0, "31bb: every face with a point -> the labels are the face indices, nothing absorbed")
    srg = open(os.path.join(HERE, "rebuild", "sk_regions.py"), encoding="utf-8").read(); sed_ = open(os.path.join(HERE, "rebuild", "sk_edges.py"), encoding="utf-8").read(); slab = open(os.path.join(HERE, "rebuild", "sk_labels.py"), encoding="utf-8").read()
    check("K.brep_source()" in srg and "fid=fid" in srg and "sys.exit(0)" in srg, "31bb: skin-regions on a B-rep source writes the mesh record with the face index and stops (no pictures)")
    check("K.brep_source()" in sed_ and "content_base.stl" not in sed_.split("K.brep_source()")[1][:600] and "K.orig_mesh(R, Part)" in sed_, "31bb: skin-edges compares against K.orig_mesh (no bare content_base.stl read); nothing on a B-rep source")
    check('FID = np.asarray(Z["fid"]' in slab and "K.fid_labels(FID, seeded_faces" in slab and "if FID is not None:" in slab and 'r_["kind"] = "orig"' in slab, "31bb: skin-labels lays the layout from the face index on a B-rep source; every kept original face is kind orig")
    check("Segments=True" in sksrc_ if (sksrc_ := open(os.path.join(HERE, "rebuild", "sk_source.py"), encoding="utf-8").read()) else False, "31bb: sk_source asks the mesher for one segment per face (the face index of every triangle)")
    check("source_fid.npz" in sksrc_ and "FID = FID[keep]" in sksrc_, "31bb: sk_source writes source_fid.npz aligned with source.stl's triangles (the degenerate drop applied to both)")
    os.makedirs(os.path.join(sk, "review"), exist_ok=True)
    pj_ = os.path.join(sk, "patches.json"); w(pj_, '{"patches": [{"patch": 0, "kind": "changed"}]}')
    json.dump({"what": "layout", "verdict": "ok", "md5": md(pj_), "when": "2026-10-08 12:13:08", "note": "the voxel layout"}, open(os.path.join(sk, "review", "LAYOUT_JUDGED.json"), "w"))
    json.dump({"tag": "sr5r", "levers": {"skin-labels": {"ON_MM": "0.3"}}}, open(os.path.join(sk, "LAYOUT_LOCK.json"), "w"))
    json.dump({"spots": [{"id": 1, "box": [0, 1, 0, 1, 0, 1], "tries": ["a", "b", "c"], "locked": True}]}, open(os.path.join(sk, "RESTART.json"), "w"))
    check(KR.standing_ok(folder, "layout") is not None, "31bc: before the restart the voxel layout's ok stands")
    json.dump({"source_md5": "abc123def456", "triangles": 10}, open(os.path.join(folder, "REBUILD_source.json"), "w"))
    n_ = KR.restart_on_new_source(folder, say)
    check(n_ >= 1 and KR.standing_ok(folder, "layout") is None and json.load(open(os.path.join(sk, "review", "LAYOUT_JUDGED.json")))["verdict"] == "superseded",
          "31bc: a new source mesh supersedes the standing layout ok (%s)" % n_)
    check(not os.path.isfile(os.path.join(sk, "LAYOUT_LOCK.json")) and any(f.startswith("LAYOUT_LOCK_superseded_") for f in os.listdir(sk)), "31bc: the layout lock is set aside (renamed with the time)")
    rs_ = KR.restart_state(folder)
    check(rs_.get("spots") == [] and rs_.get("source_md5") == "abc123def456", "31bc: the tries are cleared and the source's md5 recorded")
    check(KR.restart_on_new_source(folder, say) == -1, "31bc: skin-source run again on the same content changes nothing")
    rc = run("skin-labels", "--job", job, "--tag", "r1", "--set", B, "--plan")
    check("would replace the layout" not in "\n".join(out), "31bc: skin-labels after the restart is not an undo of the superseded ok")
    # --supersede  skin-labels
    w(pj_, '{"patches": [{"patch": 0, "kind": "changed"}, {"patch": 1, "kind": "orig"}]}')
    json.dump({"what": "layout", "verdict": "ok", "md5": md(pj_), "when": "2026-10-08 21:12:07", "note": "b4 layout"}, open(os.path.join(sk, "review", "LAYOUT_JUDGED.json"), "w"))
    json.dump({"what": "wires", "verdict": "ok", "md5": "x", "when": "2026-10-08 21:19:00", "note": "b4 wires"}, open(os.path.join(sk, "review", "WIRES_JUDGED.json"), "w"))
    json.dump({"what": "points", "verdict": "ok", "md5": "y", "when": "2026-10-08 16:00:00", "note": "b2 points"}, open(os.path.join(sk, "review", "POINTS_JUDGED.json"), "w"))
    json.dump({"tag": "b4", "levers": {"skin-labels": {"MASTER": "+"}}}, open(os.path.join(sk, "LAYOUT_LOCK.json"), "w"))
    rs0_ = KR.restart_state(folder); rs0_["rounds"] = [{"md5": "m1", "boxes": [], "note": "round 1", "when": "2026-10-08 18:00:00"}, {"md5": "m2", "boxes": [], "note": "round 2", "when": "2026-10-08 19:00:00"}]; KR._restart_save(folder, rs0_)
    check(KR.standing_ok(folder, "layout") is not None, "31bf: before the kit update the b4 layout's ok stands")
    n_ = KR.supersede_for_kit_update(folder, "31bf: the face-level mirror", say)
    check(n_ == 2 and KR.standing_ok(folder, "layout") is None and json.load(open(os.path.join(sk, "review", "LAYOUT_JUDGED.json")))["verdict"] == "superseded"
          and "kit update" in json.load(open(os.path.join(sk, "review", "WIRES_JUDGED.json")))["note"], "31bf: --supersede supersedes the layout's and the wires' oks (%s), the reason in their notes" % n_)
    check(json.load(open(os.path.join(sk, "review", "POINTS_JUDGED.json")))["verdict"] == "ok" and os.path.isfile(os.path.join(sk, "LAYOUT_LOCK.json")) and len(KR.restart_state(folder).get("rounds", [])) == 2,
          "31bf: the points' ok, the layout lock and the layout rounds stay (no round counted)")
    rc = run("skin-labels", "--job", job, "--tag", "r2", "--set", B, "--plan")
    check("would replace the layout" not in "\n".join(out), "31bf: skin-labels after --supersede is not an undo")
    json.dump({"what": "layout", "verdict": "ok", "md5": md(pj_), "when": "2026-10-09 09:00:00", "note": "again"}, open(os.path.join(sk, "review", "LAYOUT_JUDGED.json"), "w"))
    rc = run("skin-points", "--job", job, "--tag", "r3", "--set", B, "--supersede", "31bf")      # skin-rim  --supersede
    check(rc == 2 and "--supersede is skin-labels' or skin-rim's" in "\n".join(out) and KR.standing_ok(folder, "layout") is not None, "31bf / 31br A2: --supersede on a step that re-makes no layout is refused and supersedes nothing")
    # skin-build
    kf_ = KR.build_kit_faults(["   43s  face 16: SPAN FAILED - the boundary does not close end to end (a 4.786 mm gap)", "  112s  patch   2 orig    NOT VALID - look at it", "FAIL: the skin's shell did not close - 34 free edge(s)"])
    check(len(kf_) == 2 and "4.786" in kf_[0], "31bg: a boundary gap and an invalid face are kit lines (%d found)" % len(kf_))
    check(KR.build_kit_faults(["    4s  face 0: SPAN FAILED - the Coons patch of its four sides folds (427 of 1024 cells) - split it with a wire", "FAIL: the skin's shell did not close - 2 free edge(s)"]) == [],
          "31bg: a fold that asks for a split is the shape's failure, not the kit's - it counts")
    check(KR.kit_fault_faces(kf_) == {16, 2}, "31bh: the kit lines name the faces whose spots are not counted (%s) - the agent's own failures elsewhere still count" % sorted(KR.kit_fault_faces(kf_)))
    check(KR.ROUNDS_MAX == 5, "31bk: five layout rounds before the points re-pick (the client: 'Up the number of attempts to 5')")
    w(pj_, '{"patches": [{"patch": 0, "kind": "changed"}, {"patch": 1, "kind": "orig"}, {"patch": 2, "kind": "cap"}]}')
    okj_ = {"what": "layout", "verdict": "ok", "md5": md(pj_), "when": "2026-10-09 22:44:48", "note": "b13 layout"}
    json.dump(okj_, open(os.path.join(sk, "review", "LAYOUT_JUDGED.json"), "w"))
    json.dump({"what": "wires", "verdict": "ok", "md5": "w", "when": "2026-10-09 22:50:00", "note": "b13 wires"}, open(os.path.join(sk, "review", "WIRES_JUDGED.json"), "w"))
    w(os.path.join(folder, "BUILD_LOG.md"), "# BUILD LOG\n\n| when | tag | step | levers | the line | rc | s |\n|---|---|---|---|---|---|---|\n"
      "| 2026-10-09 22:45:52 | b13 | skin-network | - | ok | 0 | 49 |\n| 2026-10-09 22:45:57 | b13 | skin-frame | - | ok | 0 | 1 |\n"
      "| 2026-10-09 22:46:10 | b13 | skin-wires | - | kit rebuild REFUSED: no verdict on the layout | 2 | 0 |\n")
    check(KR.standing_ok(folder, "layout") is not None and KR.downstream_failure_since(folder, "layout", okj_) is None, "31bk: steps that ran (rc 0) or were refused by a gate (rc 2) overturn nothing")
    with open(os.path.join(folder, "BUILD_LOG.md"), "a") as fh: fh.write("| 2026-10-09 22:52:32 | b13 | skin-wires | END_MM=0.55 | kit: renamed LINES_carried.json -> LINES_carried.json.KILLED (written by a killed step) | 137 | 361 |\n")
    f_ = KR.downstream_failure_since(folder, "layout", okj_)
    check(f_ and f_["step"] == "skin-wires" and f_["rc"] == "137", "31bk: a downstream step KILLED after the ok is found in the BUILD_LOG (%s)" % (f_ and f_["tag"]))
    r0_ = len(KR.restart_state(folder).get("rounds", []))
    n_ = KR.supersede_after_failure(folder, "layout", okj_, f_, say)
    check(n_ == 2 and KR.standing_ok(folder, "layout") is None and "KILLED" in json.load(open(os.path.join(sk, "review", "LAYOUT_JUDGED.json")))["note"]
          and len(KR.restart_state(folder).get("rounds", [])) == r0_ + 1, "31bk: the layout's and the wires' oks are superseded with the failure as the reason, and it is a layout round")
    json.dump(dict(okj_, when="2026-10-09 23:30:00"), open(os.path.join(sk, "review", "LAYOUT_JUDGED.json"), "w"))
    check(KR.downstream_failure_since(folder, "layout", KR.standing_ok(folder, "layout")) is None, "31bk: a failure BEFORE a newer ok does not overturn that ok")
    check(KR._refused_bump(folder, "layout", md(pj_)) == 1 and KR._refused_bump(folder, "layout", md(pj_)) == 2 and KR._refused_bump(folder, "layout", "other") == 1,
          "31bk: refusals are counted per judged ok - the first is a refusal, the second a strike; another ok starts at one")
    sl_ = open(os.path.join(HERE, "rebuild", "sk_labels.py"), encoding="utf-8").read(); sb_ = open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read()
    check("if FID is None:   # 31bc: NO HOLE CUT" in sl_ and 'r_["face_src"] = int(np.bincount(fv_).argmax())' in sl_, "31bc: no hole cut on a B-rep source; an unseeded area names its original face for FEATURES")
    check('HOLES = os.environ.get("HOLES", "1")' in sb_ and "Part.Face(S_, [w_] + list(inner_))" in sb_ and "inner wires reversed" in sb_, "31bc: skin-build makes a face with its inner wires (a real hole kept)")
    sp_ = open(os.path.join(HERE, "rebuild", "sk_points.py"), encoding="utf-8").read(); se_ = open(os.path.join(HERE, "rebuild", "sk_edges.py"), encoding="utf-8").read()
    check("fi = int(FID[int(t_)])" in sp_ and "the census counts the CONTENT's faces" in sp_, "31bc: on a B-rep source a point's face is its source triangle's; the census counts the content's faces")
    check("BREP_SRC = K.brep_source()" in se_ and "[] if BREP_SRC else VIEWS" in se_, "31bc: skin-edges measures nothing and draws no measure pictures on a B-rep source")
    sw_ = open(os.path.join(HERE, "rebuild", "sk_wires.py"), encoding="utf-8").read(); sf_ = open(os.path.join(HERE, "rebuild", "sk_features.py"), encoding="utf-8").read()
    check('SELF_MM = float(os.environ.get("SELF_MM", "0.5"))' in sw_ and "one-sided: no twin chain" in sw_ and "ONE-SIDED BORDERS (31bd)" in sw_, "31bd: a chain is its own twin only when its mirror lies on it; a one-sided chain is left and said")
    check("its ends %s and %s are ONE point on this layout" in sw_ and "RAILS_used.json" in sw_, "31bd: a rail with coincident ends is refused by name; rails last used on another corner numbering are warned")
    check('CARRY_FIT = float(os.environ.get("CARRY_FIT", "1.0"))' in sw_ and "carried %s does not fit this chain" in sw_ and "CARRIED DECISIONS NOT DRAWN (31bd)" in sw_, "31bd: a carried LINE / ARC that does not fit its new chain is not drawn (TO DECIDE)")
    check("were written for another layout's numbering" in sw_ and "_raw_add = []; _raw_fil = []\n" in sw_, "31bd: _add / _fillets of a LINES file for another numbering are not applied (TO DECIDE)")
    check("_alias[int(p_[\"face_src\"])] = int(_m)" in sf_ and "a feature map is side-free" in sf_, "31bd: FEATURES ids of the twin side name their master's face")
    check("TWINS AFTER THE MERGES (31be)" in sf_ and "K.repair_twins(PJ, live, absorbed, remap, newp, say)" in sf_, "31be: twins are paired again from the raw layout's grp pairs (sk_lib.repair_twins)")
    import sk_lib as SKL2
    # mirror_of
    PJr = [{"patch": 0, "kind": "cap"}, {"patch": 1, "kind": "cap"},
           {"patch": 2, "kind": "orig", "grp": 2, "label": 2}, {"patch": 3, "kind": "orig", "grp": 3, "label": 3}, {"patch": 4, "kind": "orig", "grp": 4, "label": 4},
           {"patch": 5, "kind": "orig", "grp": 2, "mirror_of": 2, "label": -600002}, {"patch": 6, "kind": "orig", "grp": 3, "mirror_of": 3, "label": -600003},
           {"patch": 7, "kind": "orig", "grp": 4, "mirror_of": 4, "label": -600004}, {"patch": 8, "kind": "changed", "grp": 8, "label": 8}]
    live = [0, 1, 2, 4, 6, 7, 8]; absorbed = {0: [], 1: [], 2: [3], 4: [], 6: [5], 7: [], 8: []}
    remap = {p: i for i, p in enumerate(live)}
    newp = [dict((k, v) for k, v in PJr[p].items()) for p in live]
    for i, p in enumerate(live): newp[i]["patch"] = i
    rep, asym, badg = SKL2.repair_twins(PJr, live, absorbed, remap, newp, lambda *a, **k: None)
    g2 = newp[remap[2]]["grp"]; g6 = newp[remap[6]]["grp"]
    check(rep == 1 and g2 == g6 and newp[remap[6]].get("mirror_of") == remap[2] and "mirror_of" not in newp[remap[2]], "31be: the survivor 2 (holding 3) is paired with survivor 6 (holding 5): one pair, the twin's mirror_of = the master (%s)" % [rep, g2, g6, newp[remap[6]].get("mirror_of")])
    check(newp[remap[4]]["grp"] == 4 and newp[remap[7]]["grp"] == 4 and newp[remap[7]].get("mirror_of") == 4, "31be: a clean pair (4/7) is untouched")
    check(not badg and not asym and newp[remap[8]]["grp"] == 8, "31be: no group of three, no asymmetry, the plane-spanning single keeps its own grp")
    cnt = {}
    for r in newp:
        if r.get("kind") != "cap" and r.get("grp") is not None: cnt[r["grp"]] = cnt.get(r["grp"], 0) + 1
    check(all(v in (1, 2) for v in cnt.values()), "31be: after the repair every non-cap grp has 1 or 2 members (the agent's selftest)")
    # mirror_of  mirror_of
    PJs = [dict(r) for r in PJr]; PJs[5]["mirror_of"] = 0
    newp2 = [dict((k, v) for k, v in PJs[p].items()) for p in live]
    for i, p in enumerate(live): newp2[i]["patch"] = i
    rep2, asym2, badg2 = SKL2.repair_twins(PJs, live, absorbed, remap, newp2, lambda *a, **k: None)
    check(rep2 == 1 and not badg2 and newp2[remap[6]]["grp"] == newp2[remap[2]]["grp"], "31be: a stale mirror_of (a wall cap) cannot mislead the pairing - the grp pairs decide")
    sl2_ = open(os.path.join(HERE, "rebuild", "sk_labels.py"), encoding="utf-8").read()
    check("_master_new = {r_[\"grp\"]: r_[\"patch\"] for r_ in newp if \"mirror_of\" not in r_" in sl2_, "31be: skin-labels writes mirror_of in its final numbering")
    se2_ = open(os.path.join(HERE, "rebuild", "sk_edges.py"), encoding="utf-8").read()
    check("_by_hash.setdefault(_e.hashCode(), []).append(_fi)" in se2_ and "sIN.isInside" in se2_ and "ancestorsOfType" not in se2_.split("_faces_of = ")[1][:200], "31bd: skin-edges maps every edge's faces once and classifies inside on the content (no per-edge ancestor map)")
    kr_ = open(os.path.join(HERE, "kit_rebuild.py"), encoding="utf-8").read()
    check('r["_by_time"] = True' in kr_ and "by time: the newest run of the step" in kr_, "31bd: the layout lock falls back to the newest run of a step on record")
    for s_ in ("hooks/lookgate.py", "kit_rebuild.py"):
        import warnings
        with warnings.catch_warnings(record=True) as wl_:
            warnings.simplefilter("always"); compile(open(os.path.join(HERE, "..", s_) if s_.startswith("hooks") else os.path.join(HERE, s_), encoding="utf-8").read(), s_, "exec")
        check(not [x for x in wl_ if "escape" in str(x.message)], "31bc: no SyntaxWarning (invalid escape) in %s" % s_)
    bt = os.path.join(folder, "body_trial.brep"); w(bt, b"trial body"); rv = os.path.join(folder, "review_body")
    for f in ("iso_1.png", "iso_2.png", "below_1.png", "stations_1.png"): w(os.path.join(rv, f), b"png")
    json.dump({"kind": "trial", "frames": ["iso_1.png", "iso_2.png", "below_1.png", "stations_1.png"], "md5": md(bt), "tag": "tr1"}, open(os.path.join(rv, "TRIAL_LOOK.json"), "w"))
    pp = os.path.join(sk, "piece_skin.brep"); w(pp, b"the piece")
    json.dump({"why": "see it in the body", "when": "2026-10-08 10:00:00", "tag": "tr1", "piece_md5": md(pp), "done": True, "check": "CHECK PASS: 1 solid, seam 0"}, open(os.path.join(folder, "TRIAL.json"), "w"))
    json.dump({"why": "see it in the body", "when": "2026-10-08 10:00:00", "tag": "tr1", "piece_md5": md(pp), "done": True, "check": "CHECK PASS: 1 solid, seam 0"}, open(os.path.join(folder, "TRIAL.json"), "w"))
    if not os.path.isfile(os.path.join(folder, "walls.json")): w(os.path.join(folder, "walls.json"), b"[]")
    rc = run("reinsert", "--job", job, "--tag", "tr1", "--set", B, "--set", "STEP=3", "--set", "TRIAL=see it in the body", "--set", "PIECE=" + pp)
    check(rc == 2 and "continues the trial STEP 2 that sewed THIS piece" in " ".join(out) and "did not finish" in " ".join(out), "31bq R7W D1: a trial STEP 3 whose STEP 2 never finished for this piece is refused by name (got %r)" % (rc,))
    json.dump({"piece_md5": md(pp), "check": "BOP check found the following errors:\nError in Face: BOPAlgo SelfIntersect", "check_selfintersect": True, "self_intersections": [], "si_searched": True,
               "si_unmeasured_pairs": 0, "si_self_faces": [3], "edge_off_max": 0.001}, open(os.path.join(sk, "solid_c.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "trial", "--verdict", "ok", "--note", "the real model: the spine one clean face, the vanes smooth, the seam without a step on every wall"], kit, say)
    check(rc == 2 and "TWO reviewers" in " ".join(out), "a trial's ok is refused before its two reviewers")
    out.clear(); rc = KR.second(["--job", job, "--what", "trial", "--assign"], kit, say)
    st = json.load(open(KR._second_path(folder, "trial")))
    check(rc == 0 and len(st["assigned"]) == 2 and "REAL MODEL" in " ".join(out) and "stations" in " ".join(out).lower(), "second --what trial: two shards over review-body's frames of the real model, the trial brief")
    r_ok = json.dumps({"frames_opened": st["assigned"]["0"], "verdict": "pass", "defects": [], "poor_frames": []})
    out.clear(); rc = KR.second(["--job", job, "--what", "trial", "--shard", "0", "--result", r_ok], kit, say)
    r_ok1 = json.dumps({"frames_opened": st["assigned"]["1"], "verdict": "pass", "defects": [{"frame": st["assigned"]["1"][0], "severity": "note", "size": "small", "what": "a faint ripple on the vane"}], "poor_frames": []})
    out.clear(); rc = KR.second(["--job", job, "--what", "trial", "--shard", "1", "--result", r_ok1], kit, say)
    check(rc == 0 and "passed its two reviewers" in " ".join(out), "both shards in, no blocker: the trial may be judged ok")
    out.clear(); rc = KR.judge(["--job", job, "--what", "trial", "--verdict", "ok", "--note", "the real model: the spine one clean face, the vanes smooth, the seam without a step on every wall"], kit, say)
    check(rc == 2 and "cross THEMSELVES [3]" in " ".join(out) and os.path.isfile(bt) and not os.path.isfile(os.path.join(folder, "body_new.brep")),
          "31bq R7W D9: a piece whose faces cross themselves (its build record) is NOT accepted - refused by name before anything is renamed")
    _c2 = {"piece_md5": md(pp), "check": "", "self_intersections": [], "si_searched": True, "si_unmeasured_pairs": 0, "si_self_faces": []}
    _nj = ["--job", job, "--what", "trial", "--verdict", "ok", "--note", "the real model: the spine one clean face, the vanes smooth, the seam without a step on every wall"]
    json.dump(_c2, open(os.path.join(sk, "solid_c.json"), "w")); out.clear(); rc = KR.judge(_nj, kit, say)
    check(rc == 2 and "NOT READ" in " ".join(out) and os.path.isfile(bt), "31bq R7Wr (C2): a build record with NO edge_off_max refuses the acceptance (the gap NOT READ, no BOP_OK) - nothing renamed")
    json.dump(dict(_c2, edge_off_max=0.001, edge_gaps_unmeasured=1), open(os.path.join(sk, "solid_c.json"), "w")); out.clear(); rc = KR.judge(_nj, kit, say)
    check(rc == 2 and "NOT MEASURED" in " ".join(out) and os.path.isfile(bt), "31bq R7Wr (C2): an edge gap the build could not measure (edge_gaps_unmeasured 1) refuses the acceptance without BOP_OK")
    json.dump([1, 2, 3], open(os.path.join(sk, "solid_c.json"), "w")); out.clear()
    try: rc = KR.judge(_nj, kit, say); _tb = False
    except Exception: rc = None; _tb = True
    check(rc == 2 and not _tb and "not an object" in " ".join(out) and os.path.isfile(bt), "31bq R7Wr (C2): a record that is JSON but a LIST refuses the acceptance by name - no Traceback (it had crashed the judge)")
    opened31cb(root, *[os.path.join(rv, f) for f in ("iso_1.png", "iso_2.png", "below_1.png", "stations_1.png")])
    json.dump({"piece_md5": md(pp), "check": "", "self_intersections": [], "si_searched": True, "si_unmeasured_pairs": 0, "si_self_faces": [], "edge_off_max": 0.001}, open(os.path.join(sk, "solid_c.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "trial", "--verdict", "ok", "--note", "the real model: the spine one clean face, the vanes smooth, the seam without a step on every wall"], kit, say)
    o = " ".join(out); tj = json.load(open(os.path.join(folder, "TRIAL.json")))
    check(rc == 0 and "ACCEPTED" in o and os.path.isfile(os.path.join(folder, "body_new.brep")) and not os.path.isfile(bt) and tj.get("accepted"),
          "a trial judged ok is PROMOTED: body_trial.brep is body_new.brep, TRIAL.json accepted - nothing rebuilt or re-sewn")
    rs = json.load(open(os.path.join(rv, "review_state.json")))
    check(rs.get("state") == "COMPLETE" and rs["counts"]["frames"] == 4, "review_body is a COMPLETE review (kit check --review reads it)")
    pj_ = json.load(open(os.path.join(sk, "review", "PIECE_JUDGED.json")))
    check(pj_.get("verdict") == "ok" and pj_.get("by") == "trial", "the piece is judged ok by the acceptance (its standing ok)")
    rc = run("reinsert", "--job", job, "--tag", "r2", "--set", B, "--set", "STEP=2", "--set", "PIECE=" + pp)
    check(rc == 2 and "do not" in " ".join(out) and "ACCEPTED" in " ".join(out), "a real STEP 2 after the accepted trial is refused (\"do not reinsert it\")")
    check(os.path.isfile(os.path.join(folder, "body_new.brep")) and not os.path.isfile(bt) and "renamed body_trial.brep" not in " ".join(out),
          "31bq R7W D2: the refused step leaves the accepted body_new.brep where it is (it had been renamed body_trial.brep first)")
    rc = run("skin-build", "--job", job, "--tag", "b2", "--set", B)
    check(rc == 2 and "ACCEPTED" in " ".join(out), "a skin-build of the same piece after the accepted trial is refused (\"do not rebuild it\")")
    json.dump({"features": {"spine": [1, 2]}, "lines": {"3": {"kind": "LINE", "why": "the spine's edge is straight"}, "_add": [], "_fillets": []}, "rails": [{"name": "r", "a": "c0", "b": "c1", "has": ["spine"], "why": "straight"}],
               "points": {"PTS_BOX": "0 1 0 1 0 1 | a test box with its reason"}}, open(os.path.join(sk, "DESIGN.json"), "w"))
    os.remove(os.path.join(folder, "TRIAL.json"))
    rc = run("skin-features", "--job", job, "--tag", "d1", "--set", B)
    o = "\n".join(out)
    check("design  : FEATURES from DESIGN.json" in o and os.path.isfile(os.path.join(sk, "DESIGN_features.json")), "skin-features takes FEATURES from the design file when none is given")
    rc = run("skin-wires", "--job", job, "--tag", "d2", "--set", B)
    o = "\n".join(out)
    check("LINES from DESIGN.json" in o and "RAILS from DESIGN.json" in o, "skin-wires takes LINES and RAILS from it (the _add / _fillets ride inside LINES)")
    rc = run("skin-wires", "--job", job, "--tag", "d3", "--set", B, "--set", "LINES=" + os.path.join(sk, "DESIGN_lines.json"))
    check("RAILS from DESIGN.json" in "\n".join(out) and "LINES from DESIGN" not in "\n".join(out), "a lever given on the line wins over the design file")
    KR.design_best(folder, say, "a test")
    check(os.path.isfile(os.path.join(sk, "DESIGN_best.json")), "DESIGN_best.json: the second copy (two copies, never more)")
    json.dump({"features": {"vane": [5]}}, open(os.path.join(sk, "DESIGN.json"), "w"))
    rc = run("skin-features", "--job", job, "--tag", "d4", "--set", B, "--set", "DESIGN=best")
    check("from DESIGN_best.json" in "\n".join(out) and json.load(open(os.path.join(sk, "DESIGN_features.json"))) == {"spine": [1, 2]}, "--set DESIGN=best reads the best copy back")
    import re
    srcs = {f: open(os.path.join(HERE, "rebuild", f), encoding="utf-8").read() for f in ("sk_build.py", "sk_lib.py", "sk_wires.py", "sk_rim.py", "sk_labels.py", "sk_points.py", "rb_reinsert.py", "rb_region.py")}
    srcs["kit_rebuild.py"] = open(os.path.join(HERE, "kit_rebuild.py"), encoding="utf-8").read()
    left = {f: len(re.findall(r'say\(\s*"[^"\n]*(?<![A-Za-z_])window(?![A-Za-z0-9_])', s)) for f, s in srcs.items()}
    check(sum(left.values()) == 0, "no say() line of the runner or the scripts calls the edit region a window (%s)" % {k: v for k, v in left.items() if v})
    sb = srcs["sk_build.py"]; sw = srcs["sk_wires.py"]; sr = srcs["sk_rim.py"]
    check('FIT = (os.environ.get("FIT", "span")' in sb and "SP.span_face(" in sb and "SPLITS" in sb and "makeFillet" in sb, "skin-build: FIT=span the method, the splits, the kernel fillets")
    check('"_add"' in sw and '"_fillets"' in sw and "guides.brep" in sw and "fillets.json" in sw and "CUTS" in sw, "skin-wires: the added lines (_add: guide | split), the fillets, the border cuts")
    check("changed faces owning a wall edge of the edit region" in sr and "wall_edges" in sr and 'say("SEAM CREASE RISK' not in sr, "31bq B49: skin-rim says the changed faces owning a wall edge in ONE quiet line (the SEAM CREASE RISK line gone), the count in patches.json wall_edges")
    la = open(os.path.join(HERE, "..", "tools", "look_at.py"), encoding="utf-8").read()
    check("LINES_ONLY" in la, "look_at draws a lines-only shape")
    check("TRIAL_BRIEF" in srcs["kit_rebuild.py"] and "promote_trial" in srcs["kit_rebuild.py"], "the runner: the trial brief and the promotion")
finally:
    shutil.rmtree(root, ignore_errors=True)

try:
    import numpy as _np, sys as _sys, os as _os
    _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "rebuild")); import sk_lib as _K
    _S = _np.c_[_np.linspace(0, 10, 101), _np.zeros(101), _np.zeros(101)]; _w = _K.taper_weights(_S, 2.0)
    check(abs(_w[0]) < 1e-9 and abs(_w[-1]) < 1e-9 and abs(_w[50] - 1) < 1e-9 and 0 < _w[10] < 1, "taper_weights: 0 at both ends, 1 in the middle, rising over the run-out")
    _w1 = _K.taper_weights(_S, 2.0, ends=(1,)); check(abs(_w1[0] - 1) < 1e-9 and abs(_w1[-1]) < 1e-9, "taper_weights: one end only")
    _ws = _K.taper_weights(_S[:21], 2.0); check(_ws.max() < 0.999, "taper_weights: a crease shorter than two run-outs never reaches the full radius")
except Exception as _ex: check(False, "taper_weights raised %s" % _ex)
try:
    import numpy as _np
    _sb = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    check('_sp = float(np.mean(np.einsum("ij,ij->i", FO[p_]["D"], NL[q_]))); _sq = float(np.mean(np.einsum("ij,ij->i", FO[q_]["D"], NL[p_]))); _sense = _sp + _sq' in _sb and "convex = _sense < 0" in _sb
          and "kd_p.query(S_[m_], k=min(8" not in _sb and "the master's sense is taken" in _sb and '"sense": round(_sense, 3)' in _sb,
          "31bo fix 1: skin-build decides a crease's sense from BOTH faces' material directions against the other's normal (mirror-invariant), a twin takes its master's sense when they differ, the record carries the number")
    _Dp, _nq, _Dq, _np_ = _np.array([[-1.0, 0, 0]] * 5), _np.array([[-1.0, 0, 0]] * 5), _np.array([[0, 0, 1.0]] * 5), _np.array([[0, 0, 1.0]] * 5)
    _in = float(_np.mean(_np.einsum("ij,ij->i", _Dp, _nq)) + _np.mean(_np.einsum("ij,ij->i", _Dq, _np_)))
    _Dq2, _nq2 = _np.array([[0, 0, -1.0]] * 5), _np.array([[1.0, 0, 0]] * 5)
    _out = float(_np.mean(_np.einsum("ij,ij->i", _Dp, _nq2)) + _np.mean(_np.einsum("ij,ij->i", _Dq2, _np_)))
    _out_sw = float(_np.mean(_np.einsum("ij,ij->i", _Dq2, _np_)) + _np.mean(_np.einsum("ij,ij->i", _Dp, _nq2)))
    _in_m = float(_np.mean(_np.einsum("ij,ij->i", _Dp * _np.array([-1, 1, 1]), _nq * _np.array([-1, 1, 1]))) + _np.mean(_np.einsum("ij,ij->i", _Dq * _np.array([-1, 1, 1]), _np_ * _np.array([-1, 1, 1]))))
    check(_in > 0 and _out < 0 and _out_sw == _out and _in_m == _in, "the sense formula: an inside corner (a floor meeting a wall) reads concave, a box edge convex, the same with the faces swapped and under a mirror across x")
except Exception as _ex: check(False, "the 31bo sense pin raised %s" % _ex)
try:
    import numpy as _np
    def _mesh(zsign):
        V = _np.array([[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0], [0, 0, 4.0 * zsign], [0, 4, 4.0 * zsign]], float)
        Ff = [[0, 1, 2], [0, 2, 3]]
        Fw = [[0, 3, 5], [0, 5, 4]]
        F = _np.array(Ff + Fw); pid = _np.array([0, 0, 1, 1]); return V, F, pid
    _S = _np.c_[_np.zeros(9), _np.linspace(0, 4, 9), _np.zeros(9)]
    V1, F1, P1 = _mesh(+1); s_in, n_in = _K.crease_sense(V1, F1, P1, 0, 1, _S); s_in2, _ = _K.crease_sense(V1, F1, P1, 1, 0, _S)
    V2, F2, P2 = _mesh(-1); s_out, n_out = _K.crease_sense(V2, F2, P2, 0, 1, _S); s_out2, _ = _K.crease_sense(V2, F2, P2, 1, 0, _S)
    Vm = V1.copy(); Vm[:, 1] = 4 - Vm[:, 1]; Fm = F1[:, ::-1]; s_m, _ = _K.crease_sense(Vm, Fm, P1, 0, 1, _S)
    check(s_in is not None and s_in > 0.9 and abs(s_in2 - s_in) < 1e-9 and n_in >= 1 and s_out is not None and s_out < -0.9 and abs(s_out2 - s_out) < 1e-9 and abs(s_m - s_in) < 1e-9,
          "crease_sense: an inside corner reads +1 (concave), an outside corner -1 (convex), the same with the faces swapped and under a reflection")
    _far = _np.c_[_np.full(5, 3.0), _np.linspace(0, 4, 5), _np.zeros(5)]
    check(_K.crease_sense(V1, F1, P1, 0, 1, _far)[0] is None, "crease_sense: a line off the mesh border (no shared edge within 0.5 mm) says so (None) - the D test is the fallback")
    _sb2 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    check("K.crease_sense(Vu, F, pid, p_, q_, S_)" in _sb2 and "CONVEX OR CONCAVE NOT DECIDED" in _sb2 and 'crease by %s' in _sb2, "skin-build decides the sense by the mesh dihedral first, the two faces' sides as the fallback, refuses by name when neither decides, and says which on the line")
except Exception as _ex: check(False, "the crease_sense pin raised %s" % _ex)
try:
    import sk_lib as _K3c
    _P = np.array([[0.0, 0.0, 0.0], [13.78, 0.0, 0.0]]); _Q = _K3c.polyline_samples(_P, 0.1)
    from scipy.spatial import cKDTree as _ckd
    _dmid = float(_ckd(_Q).query(np.array([6.89, 0.0, 0.0]))[0]); _dvert = float(_ckd(_P).query(np.array([6.89, 0.0, 0.0]))[0])
    check(len(_Q) >= 138 and _dmid < 0.06 and abs(_dvert - 6.89) < 1e-6 and np.allclose(_Q[0], _P[0]) and np.allclose(_Q[-1], _P[-1]),
          "31bo fix 3c: polyline_samples puts points every 0.1 mm along a 13.78 mm edge (its ends kept) - the middle of the edge is 0 from the border, where the nearest VERTEX read 6.89 mm (b13's chains 50 / 116 / 68)")
    _P2 = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0]]); _Q2 = _K3c.polyline_samples(_P2, 0.5)
    check(len(_Q2) == 5 and np.allclose(_Q2[1], [0.5, 0, 0]) and np.allclose(_Q2[3], [1.0, 0.5, 0]) and len(_K3c.polyline_samples(_P2[:1], 0.5)) == 1,
          "31bo fix 3c: polyline_samples follows every segment of a bent path; a single point is returned as it is")
    _sn3c = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_network.py"), encoding="utf-8").read()
    check(_sn3c.count("K.polyline_samples(P") == 2 and '"CAP|ORIG": "section"' in _sn3c and '"ORIG|CAP": "section"' not in _sn3c,
          "31bo fix 3c: skin-network's reach test and its mesh deviation are taken along the raw border's segments; the CAP|ORIG via label matches the sorted type (it had said 'projected' since 31al)")
except Exception as _ex: check(False, "the fix 3c pin raised %s" % _ex)
try:
    _sn3d = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_network.py"), encoding="utf-8").read()
    check(_sn3d.count("points NOT projected: the surface is over JMOVE_MAX") == 2 and "points NOT moved onto it: the shared edge is over JMOVE_MAX" in _sn3d and "if best[0] > JMOVE_MAX: far_ += 1; continue" in _sn3d,
          "31bo fix 3d: every branch of skin-network keeps a point its projection (or the move onto a shared original edge) would carry over JMOVE_MAX - the ORIG|ORIG branches too, counted and said (b13's mixed chains 58 / 89)")
except Exception as _ex: check(False, "the fix 3d pin raised %s" % _ex)
try:
    _sbL = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    _swL = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_wires.py"), encoding="utf-8").read()
    check("def _leg_entries(f_):" in _sbL and "SPLIT_END = [" in _sbL and "if SPLIT_END[e_]: continue" in _sbL and "SPLIT_END[e_] or (FIL_TAPER and" in _sbL and "key_ = len(ALL_E); ALL_E.append(ALL_E[k][int(fl[\"leg\"])])" in _sbL
          and "FIL_MERGE[key_] = fl" in _sbL and "FIL_HOLD[(key_, f)]" in _sbL and '"fillet": key_}' in _sbL and 'J_ends_ = [np.asarray(fl["J"][0], float)' in _sbL and "_done_ = {int(fl_[\"chain\"]) for fl_ in FIL_MERGE.values()}" in _sbL,
          "31bp: a _fillets entry with \"leg\" makes one blend per piece of the chain cut by a split ending on it - each leg its own crease (the piece, not NE[k]), a split end always tapers (the corner stays a point), each leg held and merged under its own key, the kernel stage knows the chain by the record")
    check('with "leg": "all"' in _sbL.replace("\\", "") and "a fillet PER LEG needs a split" in _sbL, "31bp: the corner refusal names the per-leg form; a leg on an uncut line is refused by name")
    check('"leg" is "all"' in _swL.replace("\\\"", '"') or 'is \\"all\\"' in _swL, "31bp: skin-wires validates \"leg\"")
    check('({"leg": f_["leg"]} if f_.get("leg") is not None else {})' in _swL and _swL.count('"leg": f_["leg"]') >= 2 and "decided PER LEG" in _swL, "31bp: skin-wires carries \"leg\" into fillets.json for the line and its twin, and says the per-leg decision beside the room line")
except Exception as _ex: check(False, "the 31bp pin raised %s" % _ex)
try:
    _sbR = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    _krR = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit_rebuild.py"), encoding="utf-8").read()
    check('RIBBON_MM = float(os.environ.get("RIBBON_MM", "0.3")' in _sbR and "RIBBONS = {}" in _sbR and "TANGENT RIBBONS (31bp)" in _sbR and "rib_s = [rp_ for rp_, roe_ in RIBBONS.get(pi, [])" in _sbR and '"RIBBON_MM", "RIBBON_STEP"' in _krR,
          "31bp: a changed face beside a blend by lines is filled through a tangent ribbon (a row of points RIBBON_MM inside it on the blend's tangent plane along the offset line), riding with the split piece that holds the offset line; the levers registered")
except Exception as _ex: check(False, "the 31bp ribbon pin raised %s" % _ex)
try:
    _swC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_wires.py"), encoding="utf-8").read()
    check("_chain_entries" in _swC and "share no junction" in _swC and '"chain": _cid, "pos": i_, "n": len(ks_)' in _swC and "is its own mirror" in _swC and "FILLET CHAIN %d (31bp)" in _swC,
          "31bp: a _fillets chain entry {\"lines\": [...], \"r\"} is checked as a path (consecutive lines share a junction), expanded to one record per line with chain / pos / n, and mirrored as a chain (or said to be its own mirror)")
except Exception as _ex: check(False, "the 31bp chain-wires pin raised %s" % _ex)
try:
    _sbC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    _svC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_vertex.py"), encoding="utf-8").read()
    check("import sk_vertex as VX" in _sbC and "def _chain_members" in _sbC and "CHAIN_END" in _sbC and "THE CHAIN ASSEMBLY" in _sbC and "VX.vertex_ball(" in _sbC and "_span_corner(" in _sbC and "VX.coons_patch(" in _sbC and "VX.mitre_edge(" in _sbC and "_cut_chain_at(" in _sbC and "def _meet_pass" in _sbC and "UNSHARED COPIES" in _sbC
          and "def vertex_ball" in _svC and "def coons_patch" in _svC and "def mitre_edge" in _svC and "def seg" in _svC and "def corner_arc" in _svC,
          "31bp: skin-build blends a fillet chain as ONE: each member swept at full R to the junction it shares with the next (no taper, no cap), the corner edge cut once at Q0, the corner decided by the rolling ball (sk_vertex: CONVEX - the patch between the two end arcs and the corner arc on the common face; CONCAVE - each blend's mitre edge on the plane through X and the contacts, a sliver between), a side offset meeting the corner edge cut there (the cut-cap) or eased onto it, every corner face spanned by the kit's own ladder through its edges, the common face's strip one chain, and the UNSHARED COPIES report naming every edge two faces hold as copies")
    check("need_x = 2.5 * (1.0 - 0.5 * sum(1 for x_ in (0, 1) if CHAIN_END[x_] or NO_TAPER[x_])" in _sbC, "31bp: the line-length cap of a blend by lines counts only its run-outs - a chain end (patched or capped) has none")
    _krC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit_rebuild.py"), encoding="utf-8").read()
    check('CHAIN_MODE = (os.environ.get("CHAIN_MODE", "corner")' in _sbC and 'if CHAIN_MODE != "corner": K._fail(' in _sbC and 'if CHAIN_MODE == "caps":' not in _sbC and '"CHAIN_MODE"' not in _krC,
          "31bp: the chain blend has ONE route - the rolling-ball corner; the cone-caps route is retired (refused by name with its measurement: 20-23 free edges on the agent's b23 copy) and its lever unregistered (L144)")
except Exception as _ex: check(False, "the 31bp chain-build pin raised %s" % _ex)
try:
    _spC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_span.py"), encoding="utf-8").read()
    _krC2 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit_rebuild.py"), encoding="utf-8").read()
    check('NURBS_LOOSE_RIM = float(_os.environ.get("NURBS_LOOSE_RIM", "0.5")' in _spC and "THE LOOSE NURBS RUNG" in _spC and "its rim allowed up to" in _spC and '"NURBS_LOOSE_RIM"' in _krC2,
          "31bp: the span ladder tries the NURBS fill again with its rim allowed up to NURBS_LOOSE_RIM (0.5) when the Coons patch folds, before the plate rung (the plate left its border's envelope on the agent's keel halves); the lever is registered")
    _sbD = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    check("THE CONTACTS PASS:" in _sbD and '["target"]' in _sbD and "a linear ramp over the" in _sbD and "VX.true_mitre(" in _sbD and "planar mitre" in _sbD,
          "31bp: at a concave junction the two members share ONE contact on the corner edge (the member short of it swept again onto the other's contact, before any corner is built) and ONE mitre (the blend surfaces' own intersection, else the first's planar mitre for both); an eased end is a linear ramp over the whole crease")
except Exception as _ex: check(False, "the 31bp span / contacts pin raised %s" % _ex)
try:
    _sbE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    _svE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_vertex.py"), encoding="utf-8").read()
    check("the crease's SENSE changes there" in _sbE and 'if bool(fa["convex"]) != bool(fb["convex"]):' in _sbE and "the corner is CONCAVE by the common face's own geometry" in _sbE,
          "31bp fix 6b: a fillet chain ENDS where the crease's sense changes (a fillet meeting a round is no rolling-ball corner: both blends taper to that junction), and a convex reading of the spines yields to the two offset lines crossing on the common face (the mitre)")
    check("if at_end_:" in _sbE and "VX.refit_end(pe_, _end_vertex([pe_], X_), snap_to) if i_ in at_end_" in _sbE,
          "31bp fix 6b: the concave cut at a point that is a piece's end still moves that end onto the one X (the two legs' offsets ended 0.068 mm apart at a V apex)")
    check("bs.vIso(v0), bs.vIso(v1), bs.uIso(u0), bs.uIso(u1)" in _svE and "rows[i, -1] = Q0 - 0.003 * unit(Q0 - rows[i, -2])" in _svE and "floor.setPole(1, V3(Pa[0]))" not in _svE,
          "31bp fix 6b: the corner patch's floor edge is the surface's OWN boundary iso (the curve its natural-bounds face holds) and the degenerate apex's hair column lies before the apex along each row (the blends' end arcs kept to their last 0.003 mm)")
    check('for form_ in (("taper", "taper-long", "cap") if cap else ("taper", "taper-long")):' in _sbE and "takes the CAP" in _sbE and 'em_ = int(np.argmin([np.linalg.norm(np.asarray(x_, float) - Je_) for x_ in m_["_ends"]]))' in _sbE and "the strips will NOT close there" in _sbE,
          "31bp fix 6c: a freed chain end whose taper does not fit (the width rule beside the junction) takes the kit's cap form; the member's end is found by the junction point, not by the record's index; a member that takes neither is said as a strip that will not close")
    _krE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kitlib_render.py"), encoding="utf-8").read()
    _rbE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "rb_review_body.py"), encoding="utf-8").read()
    _wcE = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks", "wallclock.py"), encoding="utf-8").read()
    _kr2 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit_rebuild.py"), encoding="utf-8").read()
    check("def _section_segs_loop" in _krE and "np.take_along_axis(pts, order[:, 0]" in _krE and 'print("   station %s = %+.0f: %d segment(s) unchanged (on both bodies within %.2f mm), %d OLD only, %d NEW only (%.1f s)"' in _rbE,
          "31bp fix 7: kitlib_render.section_segs is vectorised (the loop form kept beside it for the equivalence test) and review-body prints a line per station (a silent 313 s loop was killed at the cap)")
    check('re.match(r"`(kit\\s+[^`]+)`\\s*$", cells[0])' in _wcE and "cap = max(int(budget_min * 60 * 2), 360)" in _kr2,
          "31bp fix 7: the wall clock reads the runner's own `kit rebuild <step>` rows (every step had run on the 3-minute unnamed budget) and the runner's cap is floored at the 360 s it was - no step capped lower than before")
except Exception as _ex: check(False, "the 31bp fix 6b / 6c / 7 pin raised %s" % _ex)
# recorded  over the
try:
    import numpy as _np
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import kitlib_render as _R
    _A = _np.array([[[0, -100, 10], [50, -100, 10]], [[0, -100, 20], [0, -100, 30]]], float); _B = _A.copy(); _B[1, :, 2] += 0.5
    _mA = _R.match_segs(_A, _B, 0, 2, 0.1); _mB = _R.match_segs(_B, _A, 0, 2, 0.1)
    check(bool(_mA[0]) and not bool(_mA[1]) and bool(_mB[0]) and not bool(_mB[1]) and len(_R.match_segs(_np.zeros((0, 2, 3)), _B, 0, 2)) == 0,
          "31bp fix 7b: match_segs - a segment lying on the other section (within 0.1 mm) is matched, one 0.5 mm off is not, from either side; an empty set matches nothing")
    _rbF = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "rb_review_body.py"), encoding="utf-8").read()
    _krF = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit_rebuild.py"), encoding="utf-8").read()
    check("R.match_segs(sa, sb, au_, av_, SEC_TOL)" in _rbF and "GREEN: unchanged (both bodies within %.2f mm)   YELLOW: old body only   BLUE: %s only" in _rbF and '"STATIONS_%s.json" % TAG' in _rbF,
          "31bp fix 7b: review-body's stations draw a line both bodies share ONCE in green and only the differences yellow (old) / blue (new), the counts per station recorded (both reviewers of b27b read coincident 3 px / 1 px lines as 'yellow only' / 'blue at another z' where the kernel says the bodies are identical)")
    check("In the station frames GREEN is a section line both bodies share" in _krF and 'kit._opt(args, "--ruling")' in _krF and 'rec["blockers_overruled"] = _overruled' in _krF and "ON THE CLIENT'S RULING" in _krF and "never ok" not in _krF.split("trial (after review-body of a TRIAL reinsert)")[1][:400],
          "31bp fix 7b: the trial brief gives the reviewers the colour key; the trial judge accepts an ok over the reviewers' blockers only with the client's recorded --ruling and a note disposing of each (L134), said in the BUILD_LOG row; the usage no longer calls a trial 'never ok'")
except Exception as _ex: check(False, "the 31bp fix 7b pin raised %s" % _ex)
try:
    _kpC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit.py"), encoding="utf-8").read()
    check('_V2, _T2, _ = K.R.tess_shape(res, dev=0.025)' in _kpC and '_Vb2, _Tb2, _ = K.R.tess_shape(_b2, dev=0.025)' in _kpC and '_bj.get("vol_tess_0.025")' in _kpC and '"dvol_tess_half_deflection": _dt2' in _kpC and 'the two meshes disagree with each other too' in _kpC and "_ruler_ok = abs(kvb - tvb)" not in _kpC,
          "31bp fix 7c: when kit check's kernel and mesh volume deltas disagree, a THIRD measurement decides - both bodies meshed again at half the deflection: the two meshes agreeing while the kernel stands apart is a NOTE (Part.Volume is no ruler on that body), the meshes disagreeing too is the FAIL naming both; the base's own kernel-to-mesh gap is no calibration (the agent's b27b: 11,737 mm3 on a healthy 1.3 L body)")
except Exception as _ex: check(False, "the 31bp fix 7c pin raised %s" % _ex)
try:
    _kpD = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit.py"), encoding="utf-8").read()
    _lgD = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "leangate.py"), encoding="utf-8").read()
    check('rep["dvol_local"] = float(_dl)' in _kpD and 'rep["dvol_local_spread"] = float(abs(_dlk - _dlm))' in _kpD and '"jobdir": (os.path.join(ROOT, "claude_code", "jobs", _jb) if _jb else "")' in _kpD and '_local = cj.get("dvol_local")' in _lgD and "the local ruler (the piece against the region's content)" in _lgD and '_skin = bool(cj.get("skin_piece")) or _local is not None' in _lgD and 'tol = max(abs(w) * 0.05, 1.0, _spread)' in _lgD,
          "31bp fix 7d / 31bq SS (B21): kit check records the LOCAL ruler (the burrito's piece against the region's content, the kernel's volumes cross-checked by their meshes) and kit accept REPORTS the change by it (a skin edit's volume is reported, the pictures decide), naming which ruler (the whole-body mesh delta carries a litre's tessellation spread - b27b: -405 / -375 against the local -348)")
except Exception as _ex: check(False, "the 31bp fix 7d pin raised %s" % _ex)
try:
    _sbG = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    check("its own surface's normals taken along the crease" in _sbG and 'if kind[f] == "orig" and (PJ[f].get("face") is not None):' in _sbG,
          "31bp fix 8: at a crease on an ORIGINAL face the blend takes that face's own surface normals, the layout mesh giving only the sign (an absorbed strip's normals had put the 77 / 56 blends 66 deg off the vane underside)")
    check('RIBBON_MM = float(os.environ.get("RIBBON_MM", "0.3") or 0)' in _sbG and "def _ribbon_ok(S_plain, S_rib, kind_r, n_=7):" in _sbG and "the tangent ribbon TAKEN" in _sbG and "the tangent ribbon REFUSED" in _sbG,
          "31bp fix 8: the tangent ribbon is ON by default with a per-face acceptance - the piece filled plain and through the ribbon, the ribbon fill taken only as a NURBS fill inside the plain fill's envelope (max(2 mm, 3 x RIBBON_MM) of growth, max(1 mm, 3 x RIBBON_MM) of distance), else the plain fill stands and the ridge is said")
except Exception as _ex: check(False, "the 31bp fix 8 pin raised %s" % _ex)
try:
    import sk_lib as _K9
    _V9 = np.array([[0, 0, 0], [2, 0, 0], [0, 1, 0], [2, 1, 0], [0, 0, -1], [2, 0, -1], [0, 1, -1], [2, 1, -1]], float)
    _F9 = np.array([[0, 1, 3], [0, 3, 2], [4, 7, 5], [4, 6, 7]]); _P9 = np.array([7, 7, 7, 7])
    _nf9, _nl9, _i9 = _K9.local_face_normals(_V9, _F9, _P9, 7, np.array([[1.0, 0.0, 0.0], [1.5, 0.5, 0.0]]))
    _plain = np.cross(_V9[_F9[:, 1]] - _V9[_F9[:, 0]], _V9[_F9[:, 2]] - _V9[_F9[:, 0]]); _plain = (_plain / np.linalg.norm(_plain, axis=1)[:, None]).mean(0)
    check(_nl9 is not None and float(_nl9[:, 2].min()) > 0.99 and _i9["excluded"] >= 2 and float(np.linalg.norm(_plain)) < 1e-6 and float(_nf9[2]) > 0.99,
          "31bp fix 9: a face's normal at a crease is its OWN SHEET's - on a thin plate the plain k-mean of the nearest triangles is zero while local_face_normals gives the top sheet's +z (the far side %s triangle(s) excluded)" % _i9.get("excluded"))
    _nf9b, _nl9b, _i9b = _K9.local_face_normals(_V9, _F9, _P9, 7, np.array([[1.0, 0.0, -1.0]]))
    check(_nl9b is not None and float(_nl9b[0, 2]) < -0.99, "31bp fix 9: the same point on the BOTTOM sheet gets the bottom sheet's -z (the sheet is decided by the true distance, not the centroid)")
    _sb9 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read(); _sw9 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_wires.py"), encoding="utf-8").read()
    check("n_f, n_loc, _inf9 = K.local_face_normals(Vu, F, pid, f, S_)" in _sb9 and "_nf, out_, _inf9 = K.local_face_normals(Vu, F, _pid, f_, S_)" in _sw9 and "between the two faces' OUTWARD normals at its middle" in _sb9 and "if so.isInside(_qn + _n1 * 0.05, 1e-6, True): _n1 = _n1 * (-1.0)" in _sb9,
          "31bp fix 9: skin-build's blend normals and skin-wires' room line take the sheet normals; the crease AS BUILT is measured between OUTWARD normals (an unsigned angle read 58 for a 122 deg crease)")
except Exception as _ex: check(False, "the 31bp fix 9 pin raised %s" % _ex)
try:
    import sk_lib as _K9b
    _V = np.array([[0, 0, 0], [2, 0, 0], [0, 1, 0], [2, 1, 0], [0, -1, 1], [2, -1, 1]], float)
    _F = np.array([[0, 1, 3], [0, 3, 2], [1, 0, 4], [1, 4, 5]]); _P = np.array([1, 1, 2, 2])
    _S = np.array([[0.5, 0, 0], [1.0, 0, 0], [1.5, 0, 0]])
    _sA, _nA = _K9b.crease_side(_V, _F, _P, 1, 2, _S, np.tile([0.0, 1.0, 0.0], (3, 1)))
    _sAw, _ = _K9b.crease_side(_V, _F, _P, 1, 2, _S, np.tile([0.0, -1.0, 0.0], (3, 1)))
    _sB, _nB = _K9b.crease_side(_V, _F, _P, 2, 1, _S, np.tile([0.0, -0.7071, 0.7071], (3, 1)))
    check(_sA == 1.0 and _nA >= 1 and _sAw == -1.0 and _sB == 1.0, "31bp fix 9b: crease_side reads a face's side at the crease from the shared mesh edges' far vertices - +1 for the proposed direction into the face, -1 for the wrong side, on both faces (%s / %s / %s edges %d)" % (_sA, _sAw, _sB, _nA))
    _sN, _nN = _K9b.crease_side(_V, _F, _P, 1, 2, np.array([[1.0, 5.0, 0.0]]), np.array([[0.0, 1.0, 0.0]]))
    check(_sN is None and _nN == 0, "31bp fix 9b: a line that lies off the mesh border (no shared edge within 0.5 mm) gives no verdict - the vote and the borders then decide as before")
    _sb9b = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    check("K.crease_side(Vu, F, pid, f, (q_ if f == p_ else p_), S_, D_)" in _sb9b and "would have put the offset on the OTHER side (fix 9b)" in _sb9b and "_topo9 = (_sd9 is not None and abs(_sd9) >= 0.5)" in _sb9b,
          "31bp fix 9b: skin-build's offset side is the mesh topology's first (the centroid vote and the borders behind it, a disagreement said) - the agent's b27b 77 / 56: the chamfer's vote was undecided and the border fallback laid the offset 0.84 mm beyond the crease")
except Exception as _ex: check(False, "the 31bp fix 9b pin raised %s" % _ex)
try:
    _sb9f = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    check('_EXT = {int(e__): float(c__["extend"]) for e__, c__ in (f_.get("chain_c") or {}).items() if c__.get("extend")}' in _sb9f and "THE EXTEND PASS, before anything else" in _sb9f and "_seen_x = set()" in _sb9f and '_passes_ = ["settle", "build"]' in _sb9f and 'mx_["chain_c"][str(ex_)]["extend"] = float(min(sh_x * 1.25 + 0.1' in _sb9f and "& core_; S_in = S_[in_] if in_.any() else S_" in _sb9f and "_kink > max(3.0 * _med, 0.5 * float(_turn[_i]))" in _sb9f and "EXT_TURN_MAX" not in _sb9f,
          "31bp fix 9c-9f: a chain member whose side offset falls short of the corner edge at a CONCAVE junction (the corner's sense from the unextended spines, in the assembly's extend pass) is swept PAST the junction - the ball rolls on until it touches the next wall - and laid again; at a convex junction it pivots and never rolls past; the extended samples are not the width rule's; a corner inside a crease is a KINK, never a smooth tight arc (the agent's c2: the 1.6 mm stem tip, the rounded keel apex)")
except Exception as _ex: check(False, "the 31bp fix 9c-9f pin raised %s" % _ex)
try:
    _sb11 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    _sw11 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_wires.py"), encoding="utf-8").read()
    check("31bp fix 11: A BURIED FACE" in _sb11 and 'BUR_ = set(int(x) for x in (f_.get("buried") or [])' in _sb11 and "source surface %d stands for it there" in _sb11 and "does not reach the crease" in _sb11 and 'if f in SRCF: _sd9, _nd9 = None, 0' in _sb11 and "if SRCF: _msc_m = _msc; _msc = None" in _sb11 and 'or f in SRCF' in _sb11
          and 'is a list of ORIGINAL face numbers the blend buries' in _sw11 and _sw11.count('"buried": [int(x_) for x_ in f_["buried"]]') == 4,
          "31bp fix 11: a _fillets entry may name the original faces it BURIES; where the mesh beside the crease on a face is a buried face's, that face's own source surface stands for it (normals, offset, side from its unburied triangles; the sense from the material directions), said by name, refused when the surface does not reach the crease; sk_wires carries \"buried\" to every record")
except Exception as _ex: check(False, "the 31bp fix 11 pin raised %s" % _ex)
try:
    _sb11b = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    check("31bp fix 11b: THE HOST'S SURFACE IS ONE OF ITS OWN UNBURIED ORIGINAL FACES" in _sb11b and "is itself a BURIED face - its own unburied original" in _sb11b and "if d_reach <= BURIED_REACH: src_ = int(c_); break" in _sb11b and "if int(x_) >= 0 and int(x_) not in BUR_ and int(x_) not in _nopt_: cands_[int(x_)] = int(((fidn_ == x_) & near_).sum())" in _sb11b,
          "31bp fix 11b: the surface that stands for a buried crease is one of the host's own UNBURIED original faces (those nearest the crease first, the recorded source first among them, the first that reaches), never the buried face itself - the agent's c4 layout gave the -x crown pieces the end faces as their recorded source")
except Exception as _ex: check(False, "the 31bp fix 11b pin raised %s" % _ex)
# does not reach
try:
    _sb3 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    _sn3 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_network.py"), encoding="utf-8").read()
    _sw3 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_wires.py"), encoding="utf-8").read()
    _kr3 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit_rebuild.py"), encoding="utf-8").read()
    check("def _to_strip(E_, k_f, fl_):" in _sb3 and "def _cut_all(eds_x, splits_x):" in _sb3 and "_cut_applied" in _sb3 and "on the crease of fillet %d, to its strip's border" in _sb3 and 'eds_m = _flat_e([fl["lines"][fl["p"]][0]' in _sb3,
          "31bo fix 2: a split ending ON a fillet's crease moves to the strip's border (the offset line, cut there), the piece cutter defers a split to the piece that holds both its ends, a split never placed is refused with its ends, the blend's wire takes the offset line's pieces")
    check('FIL_SMOOTH_MM = float(os.environ.get("FIL_SMOOTH_MM", "1.5")' in _sb3 and "gaussian_filter1d as _gf" in _sb3 and '"FIL_SMOOTH_MM"' in _kr3,
          "31bo fix 2b: the local normals along a crease are smoothed over FIL_SMOOTH_MM before the offset lines are laid (the keel-root offset line waved 0.36 mm between 0.2 mm samples); the lever is registered")
    check('CREASE_TURN_MAX = float(os.environ.get("CREASE_TURN_MAX", "45")' in _sb3 and "has a CORNER inside it" in _sb3 and "EITHER make the corner a junction" in _sb3 and '"CREASE_TURN_MAX"' in _kr3,
          "31bo fix 2c: a crease whose tangent turns more than CREASE_TURN_MAX within 1.5 mm has a corner - the fillet by lines is refused by name with the corner and both ways out; the lever is registered")
    check("far_faces = []" in _sn3 and "do NOT reach this border" in _sn3 and '"mesh_dev": round(mdev, 4), "far_faces"' in _sn3 and "on the original surface of face %d only" in _sn3 and "SURFACES THAT DO NOT REACH THEIR BORDER" in _sn3,
          "31bo fix 3: skin-network asks per original surface whether it REACHES the border (the median distance of the raw border's points, JMOVE_MAX) and projects onto the ones that do - both, one, or the mesh border - said and recorded with every chain's deviation from its own mesh path")
    check("def _reaching(k, p, q, S):" in _sw3 and "prs = _reaching(k, p, q, S)" in _sw3 and "prs_ = _reaching(k_, p_, q_, S)" in _sw3 and 'JMOVE_MAX = float(os.environ.get("JMOVE_MAX", "0.5"))' in _sw3 and "if len(_kp) >= 4: Cp = Cp[_kp]; C = C[_kp]" in _sw3,
          "31bo fix 3: skin-wires lays a chain only on the surfaces that reach it (skin-network's far_faces, or measured) - in the ladder and in the mirrored remake - and thins the points a projection drove together before the fit")
except Exception as _ex: check(False, "the 31bo fixes 2-3 pin raised %s" % _ex)
try:
    _kpB = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit.py"), encoding="utf-8").read()
    _i8 = _kpB.index("_FG, _FFAR_C, _FFAR_A = "); _j8 = _kpB.index('_t0 = _tm.time(); rep["face_classes"] = None', _i8)
    _g8 = {"np": np}; exec(_kpB[_i8:_j8].replace("%%", "%"), _g8)
    def _q8(p0, p1, p2, p3): return [np.array([p0, p1, p2], float), np.array([p0, p2, p3], float)]
    def _m8(faces):
        V_ = []; T_ = []; F_ = []
        for fi_, tris_ in enumerate(faces):
            for t_ in tris_:
                k_ = len(V_); V_.extend(list(t_)); T_.append([k_, k_ + 1, k_ + 2]); F_.append(fi_)
        return np.array(V_, float), np.array(T_), np.array(F_)
    _X, _Y, _Z = 100.0, 20.0, 20.0
    _bar8 = [_q8((0, 0, 0), (_X, 0, 0), (_X, _Y, 0), (0, _Y, 0)), _q8((0, 0, _Z), (_X, 0, _Z), (_X, _Y, _Z), (0, _Y, _Z)), _q8((0, 0, 0), (_X, 0, 0), (_X, 0, _Z), (0, 0, _Z)),
             _q8((0, _Y, 0), (_X, _Y, 0), (_X, _Y, _Z), (0, _Y, _Z)), _q8((0, 0, 0), (0, _Y, 0), (0, _Y, _Z), (0, 0, _Z)), _q8((_X, 0, 0), (_X, _Y, 0), (_X, _Y, _Z), (_X, 0, _Z))]
    _A8 = [_g8["_fhs"]([11, 19, 6, 14, 14, 21])]; _cls8 = _g8["_fclasses"]; _fm8 = _g8["_far_match"]
    _cb8, _cenb8, _arb8, _ = _cls8(*_m8(_bar8), 6, {}, _A8, _A8, 0.5)
    check(list(_cb8) == [3, 0, 3, 3, 3, 3], "31bq B08 (check-faces): the bar's top face - two 100 mm triangles crossing box A with no vertex near it - is INSIDE by the separating-axis test (a vertex / centroid sample called it FAR); the other five FAR (%s)" % [int(x_) for x_ in _cb8])
    _in8 = _q8((11, 6, _Z), (19, 6, _Z), (19, 14, _Z), (11, 14, _Z))
    _ring8 = _q8((0, 0, _Z), (11, 0, _Z), (11, _Y, _Z), (0, _Y, _Z)) + _q8((19, 0, _Z), (_X, 0, _Z), (_X, _Y, _Z), (19, _Y, _Z)) + _q8((11, 0, _Z), (19, 0, _Z), (19, 6, _Z), (11, 6, _Z)) + _q8((11, 14, _Z), (19, 14, _Z), (19, _Y, _Z), (11, _Y, _Z))
    _cr8, _cenr8, _arr8, _ = _cls8(*_m8([_bar8[0], _in8, _bar8[2], _bar8[3], _bar8[4], _bar8[5], _ring8]), 7, {}, _A8, _A8, 0.5)
    _far8 = _fm8(_cb8, _cenb8, _arb8, _cr8, _cenr8, _arr8, 1e-4, 1e-6)
    check(list(_cr8) == [3, 0, 3, 3, 3, 3, 2] and int((_cr8 == 0).sum()) - int((_cb8 == 0).sum()) == 0 and not _far8[2] and not _far8[3],
          "31bq B08 (check-faces): a PURE box-wall split (the top face cut along box A's walls: the inner rectangle + the outer ring) is INSIDE 1 -> 1 and WALL-ADJACENT 0 -> 1, the five far faces matched mesh to mesh - a 0 budget passes (the centre count read +1 inside and failed)")
    _cw8, _, _, _ = _cls8(*_m8([_q8((12, 7, 14), (18, 7, 14), (18, 13, 14), (12, 13, 14)), _q8((12, 7, 14), (60, 7, 14), (60, 13, 14), (12, 13, 14))]), 2, {}, _A8, _A8, 0.5)
    check(list(_cw8) == [1, 2], "31bq B08 (check-faces): a floor lying ON box A's wall z 14 inside its rectangle is ON A WALL (not inside); the same strip running out of the rectangle is WALL-ADJACENT (%s)" % [int(x_) for x_ in _cw8])
    _cn8, _, _, _ = _cls8(*_m8([[np.array([(-50, 14.3, 17), (80, 14.3, 17), (15, 14.3, 120)], float)], [np.array([(-50, 15.0, 17), (80, 15.0, 17), (15, 15.0, 120)], float)]]), 2, {}, _A8, _A8, 0.5)
    check(list(_cn8) == [2, 3], "31bq B08 (check-faces): a big triangle passing 0.3 mm beside box A (every vertex far) is WALL-ADJACENT; 1.0 mm beside it, FAR (%s)" % [int(x_) for x_ in _cn8])
    _bar9 = [_q8((0, 0, 0), (99, 0, 0), (99, _Y, 0), (0, _Y, 0))] + _bar8[1:5] + [_q8((99, 0, 0), (99, _Y, 0), (99, _Y, _Z), (99, 0, _Z))]
    _c98, _cen98, _ar98, _ = _cls8(*_m8(_bar9), 6, {}, _A8, _A8, 0.5); _far9 = _fm8(_cb8, _cenb8, _arb8, _c98, _cen98, _ar98, 1e-4, 1e-6)
    check(len(_far9[2]) == 2 and len(_far9[3]) == 2, "31bq B08 (check-faces): the end face moved 1 mm far from box A (and the bottom face shortened with it) - 2 far faces new or moved, 2 of the base's gone: the far change is caught with the face count unchanged (%s / %s)" % (_far9[2], _far9[3]))
    _sl8 = (np.vstack([_A8[0][0], [[15, 10, 17]]]), np.vstack([_A8[0][1], [[0, 0.70710678, 0.70710678]]]))
    _cs8, _, _, _ = _cls8(*_m8([[np.array([(12, 13.5, 20.5), (18, 13.5, 20.5), (15, 13.9, 20.9)], float)], [np.array([(12, 7, 15), (18, 7, 15), (15, 8, 16)], float)]]), 2, {}, [_sl8], [_sl8], 0.5)
    check(list(_cs8) == [3, 0], "31bq B08 (check-faces): against an edit region cut by a plane (the window + PLANES), a triangle beyond the plane is outside (FAR) and one inside it INSIDE (%s)" % [int(x_) for x_ in _cs8])
    check('rep["faces_in_box"], rep["faces_in_box_base"] = _nr[0], _nb[0]' in _kpB and "changed far from every edit region box - nothing may change there" in _kpB and "face count INSIDE the edit region grew by" in _kpB
          and "_bshape = K.load" not in _kpB and "if _open.any() and _fine_mesh() is not None:" in _kpB and '"_localbox.brep"' in _kpB and '"REBUILD_region.json"' in _kpB and 'j.get("mesher") == _mesher()' in _kpB,
          "31bq B08 (check-faces): the template judges the INSIDE class against the budget and fails a far change by name, keeps faces_in_box / faces_in_box_base for the readers, classes against the job's edit region and the reinsert's local box, never loads the base B-rep for the count (the fine mesh only when a column opened), and re-meshes a cache record another mesher made")
    _ap8 = _g8["_fapart"]([[11, 19, 6, 14, 14, 21], [71, 79, 6, 14, 14, 21]], [8, 22, 3, 17, 11, 24])
    _er8 = [_g8["_fhs"]([11, 19, 6, 14, 14, 21])] + [_g8["_fhs"](b_) for b_ in _ap8]; _pr8 = _er8 + [_g8["_fhs"]([8, 22, 3, 17, 11, 24])]
    _pk8 = _q8((73, 8, _Z), (77, 8, _Z), (77, 12, _Z), (73, 12, _Z))
    _c58, _, _, _ = _cls8(*_m8([_bar8[1], _pk8]), 2, {}, _er8, _pr8, 0.5)
    check(_ap8 == [[71, 79, 6, 14, 14, 21]] and [int(x_) for x_ in _c58] == [0, 0], "31bq B08 C1 (V5): with a job's region A (local box A + 3), the --box B apart from it joins the edit region - a face in B is INSIDE and the budget judges it (%s, %s)" % (_ap8, [int(x_) for x_ in _c58]))
    _st8 = [_q8((19.0, 7 + k_, _Z), (19.9, 7 + k_, _Z), (19.9, 7.9 + k_, _Z), (19.0, 7.9 + k_, _Z)) for k_ in range(8)]
    _c38, _, _, _ = _cls8(*_m8([_bar8[1]] + _st8), 9, {}, _A8, _A8, 0.5)
    _nb38 = [1, 0, 0, 5, 0]; _nr38 = [int((_c38 == k_).sum()) for k_ in range(5)]; _nr38[3] = 5
    _wl38 = _g8["_fwall_limit"](_nb38, _nr38, 4.0); _wl28 = _g8["_fwall_limit"]([1, 0, 0, 5, 0], [1, 0, 2, 5, 0], 4.0); _wlr = _g8["_fwall_limit"]([132, 0, 28, 4605, 0], [69, 0, 141, 4605, 0], 4.0)
    check(_nr38[2] == 8 and _wl38[2] and not _wl28[2] and not _wlr[2],
          "31bq B08 C2 (V3): eight slivers beside box A's wall read WALL-ADJACENT 0 -> 8 - over WALL_GROW_X 4 x (1 + 0): FAILS; a wall split's 2 fragments (V2) and fill15's real +113 against 4 x 160 pass (%s %s %s)" % (_wl38, _wl28, _wlr))
    check('_bj_path = None      # 31bq B08 C3' in _kpB and 'if _bj_path: _rec_save(_bj_path, _bj)' in _kpB and '"wallx": wallx' in _kpB and 'WALL_GROW_X = %g (%s)' in _kpB,
          "31bq B08 C2 / C3: kit check takes --wall-grow-x (env WALL_GROW_X, suggested 4) into the template; a cache write that failed forgets the record's path and the ruler never stamps a record whose npz it could not write")
except Exception as _ex: check(False, "the 31bq B08 (check-faces) pin raised %r" % (_ex,))
# the instrument of B20
try:
    import ast as _astR, re as _reR
    _sbR = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read(); _trR = _astR.parse(_sbR)
    _gR = {"re": _reR, "np": np, "_BLAME_NOTE": []}
    for _n in _trR.body:
        if isinstance(_n, _astR.FunctionDef) and _n.name in ("_dup_entries", "_dup_text", "_wtxt"): exec(_astR.get_source_segment(_sbR, _n), _gR)
        if isinstance(_n, _astR.Assign) and any(getattr(_t, "id", "") == "_KIT_SPLIT_RE" for _t in _n.targets): exec(_astR.get_source_segment(_sbR, _n), _gR)
        if isinstance(_n, _astR.If) and "FIL_RERUN" in _astR.get_source_segment(_sbR, _n.test):
            for _m in _astR.walk(_n):
                if isinstance(_m, _astR.FunctionDef) and _m.name in ("_blame", "_nfree", "_class", "_class_lines"):
                    _code = _astR.get_source_segment(_sbR, _m); exec("\n".join(_l[_m.col_offset:] if _l.startswith(" " * _m.col_offset) else _l for _l in _code.splitlines()), _gR)
    _D = _gR["_dup_entries"]
    check(_D([{"line": 77, "chain": 1}, {"line": 93, "chain": 1}, {"line": 77, "chain": 3}]) == [(77, ["chain 1", "chain 3"])] and _D([{"line": 54, "leg": 0}, {"line": 54, "leg": 1}]) == []
          and _D([{"line": 54, "leg": "all"}, {"line": 54, "leg": 1}]) != [] and _D([{"line": 54, "leg": 1}, {"line": 54, "leg": 1}]) != [],
          "31bq R7W (M4): a crease (line, leg) decided in two _fillets entries is found by name - two chains, a whole line and one of its legs, a leg twice; two legs of one line are two creases")
    check('_dups0 = _dup_entries(FILLETS)' in _sbR and "THE LINES PASS IS REFUSED before any sweep" in _sbR and "_dups_p = _dup_entries(FILLETS)" in _sbR and _sbR.index("def _dup_entries(fils_):") < _sbR.index("_dups0 = _dup_entries(FILLETS)"),
          "31bq R7W (M4): the lines pass's pre-pass refuses it before any sweep (FIL_MERGE is keyed by the line: the second record overwrote the first and both chains assembled on it - vR5x z2's 26 free edges); the parent refuses it before it launches the lines child, the sharp piece standing")
    check(_gR["_wtxt"]({"why": "fillet chain 3, members 110 leg 0 + 110 leg 1 + 114 leg 0 + 114 leg 1 + 116 leg 0, by lines", "fillet": 7}).endswith("116 leg 0, by lines") and len(_gR["_wtxt"]({"why": "x" * 120})) == 80
          and _sbR.count("% (_wtxt(") >= 3,
          "31bq R7W (M9, A3 finding 5): a KIT split's name is printed WHOLE in the three split-failure texts (cut at 80 a 5-member legged list lost the retry's anchor ', by lines, from ['); an agent's why still cut at 80")
    _SI16F = "FAIL: THE SOLID SELF-INTERSECTS beyond the 0.30 mm print tolerance: faces 37 (patch 18F, fillet of line 56 leg 0) x 38 (patch 18F, fillet of line 56 leg 1) 4.16 mm deep (1.40 along) - a face runs through its neighbour"
    _SI16 = "FAIL: THE SOLID SELF-INTERSECTS beyond the 0.30 mm print tolerance: faces 37 (patch 18F, fillet) x 38 (patch 18F, fillet) 4.16 mm deep (1.40 along) - a face runs through its neighbour"
    _NV = "FAIL: the closed shell did not make a valid solid - the face(s) not valid themselves: face 37 (patch 18F, fillet of line 56 leg 0)"
    _L17 = [29, 30, 32, 34, 36, 39, 53, 55, 56, 74, 77, 91, 93, 97, 110, 114, 116]
    check("SELF-INTERSECTS" in (_gR["_class"]([_SI16F], 1) or "") and _gR["_class_lines"]([_SI16F, "   70s  FILLET BY LINES on line 74: not made - the room"], _L17) == [56] and _gR["_class_lines"]([_SI16], _L17) == []
          and "NOT VALID" in (_gR["_class"]([_NV], 1) or "") and _gR["_class_lines"]([_NV], _L17) == [56],
          "31bq R7W (M1, A3 findings 1 / 2 / 6): a crossing or an invalid solid is retried without the blend lines ITS OWN failure line names (fill16's pair as the fixed kit names it -> [56]; a member not made beside it is no part of it) - fill16's text as the old kit wrote it names none")
    check("CRASHED" in (_gR["_class"](["   90s  sameParameter on the shell: True; max edge tolerance 0.8; free edges after 0"], 1) or "") and "NO VERDICT" in (_gR["_class"](["(no verdict: the lines child exited 0 without its SKIN BUILD PASS line - 31bq R7W)"], 1) or ""),
          "31bq R7W (M9, A3 finding 9): a lines child that exits 1 with no FAIL line is a crash, one that exits 0 without its SKIN BUILD PASS line gave no verdict - neither is an open shell to blame")
    _OPEN = ["   80s  shell: 76 faces, closed False, free edges 17", "FAIL: the skin's shell did not close - 17 free edge(s) (skin\\free_c.brep; `kit rebuild skin-look` draws them red)"]
    check(_gR["_nfree"](_OPEN) == 17 and _gR["_nfree"](["   99s  sameParameter on the shell: True; max edge tolerance 0.1; free edges after 3"]) == 3,
          "31bq R7W (M9, A3 finding 3): the retry's free-edge count is the child's own FAIL line (the optional sameParameter line only as the last fallback - with SAMEPARAM=0 the 'no better' stop never fired)")
    _STR = "   60s  face 6 piece B: SPAN FAILED - a split (fillet chain 2 by lines, from [1.0, 2.0, 3.0] to [4.0, 5.0, 6.0]): its ends (0.00 / 0.73 mm from the nearest border vertices) are not both on one piece of the face"
    _END = "   55s     fillet chain 2: the members' strip ends on face 6 (31bq R7W): 34 [1.0, 2.0, 3.0] [2.0, 2.0, 3.0]; 39 [2.0, 2.0, 3.0] [2.5, 2.5, 3.0]; 77 [3.0, 4.0, 5.0] [4.0, 5.0, 6.0]"
    _CH2 = "   20s  FILLET CHAIN 2 (31bp): 7 member(s) round face 6 - ['34', '39', '55', '74', '77', '93', '110']; 6 shared junction(s) get a corner patch"
    check(_gR["_blame"](_L17, [_CH2, _END, _STR])[0] == [77] and _gR["_blame"](_L17, [_CH2, _STR])[0] == [34, 39, 55, 74, 77, 93, 110]
          and _gR["_blame"](_L17, ["   60s  face 18 piece F (fillet of line 56 leg 0): SPAN FAILED - the surface does not take its loop"])[0] == [56],
          "31bq R7W (M9, A3 finding 4; M1): a chain's common-face strip failure blames the member whose strip END lies at the failing end (77), the whole chain only when no end matches; a blend face's own SPAN FAILED blames its line")
    check('rec["fillet_line"] = int(FIL_MERGE[fk_]["chain"])' in _sbR and "for i, p, eds, S_given, sub_, fk_ in _todo_faces:" in _sbR and 'r__.get("fillet_name")) if r__.get("fillet_name") is not None' in _sbR
          and "the face(s) not valid themselves" in _sbR and '"valid": bool(f_.isValid()), "sub": pf_[k_].get("sub")' in _sbR and "fillet of line %s)" in _sbR,
          "31bq R7W (M1, A3 finding 1): the blend's line reaches its FACE RECORD (the sub-record's FIL_MERGE key -> rec fillet_line / fillet_name), so the crossing, check(True)'s per-face line, a blend piece's SPAN FAILED and the invalid solid's FAIL line name it ('fillet of line N' had been in no real log)")
    check("THE HOLE'S OWN TWO POINTS" in _sbR and "def _term_A(i__, e__):" in _sbR and "only=_miss_edges" in _sbR and "def _crease_path(pa_, pb_, kks_, cut=True, tol=0.05, only=None):" in _sbR and "a HOLE NOT closed" in _sbR
          and _sbR.index("_sub_rng = []") < _sbR.index("_bnd = {}"),
          "31bq R7W (M2, A1 finding 1): a hole between two sub-chains is closed by the missing member(s)' own crease between the WALK'S OWN two points (never the nearest vertex pair: a trapezoid / U foot drew a chord, the loop branched); a fill whose ends are not on those creases is refused by name")
    check("ITS OWN SENSE IS DECIDED" in _sbR and "TWIN_BETA_TOL = 10.0; TWIN_T_TOL = 0.15" in _sbR and "def _twin_cause(bur_, mbur_, faces_):" in _sbR and _sbR.index("def _twin_cause(bur_, mbur_, faces_):") < _sbR.index("ITS OWN SENSE IS DECIDED"),
          "31bq R7W (M3, A1 finding 2): a twin whose own sense is DECIDED and contradicts its master's is turned only when its crease is the master's mirror (beta / t alike); else refused by name with the likely cause (its buried ids, their mirror twins)")
    check('with busy("edge gaps on %d faces" % len(so.Faces), 900)' in _sbR and 'res["edge_gaps_unmeasured"] = int(_une + _unp)' in _sbR and "return nraised, worst_off, worst_pc, un_e, un_p" in _sbR,
          "31bq R7W (M12): _edge_gaps declares itself to the runner's watchdog (40-47 s silent on a 49-face solid) and counts the edges / pcurves it could not measure (solid_c.json edge_gaps_unmeasured)")
    check("SI_TOUCH_MM = 0.05" in _sbR and "face pair(s) TOUCH" in _sbR and "standing SHARP" in _sbR and '_chk)) + globals().get("_FSUF", "")' in _sbR and _sbR.index('_FSUF = ""') < _sbR.index('_chk = "check(True) OK"'),
          "31bq R7W (M9, A2 finding 7 / A3 finding 7): the PASS line names a crossing by its faces and a touch as a count, and a LINES pass's PASS line names every decided line it did not make and why")
    check("def _not_borders(i_, eds_):" in _sbR and "NOT A BORDER - given %d edge(s) that are NOT a border of it" in _sbR and _sbR.index("def _not_borders(i_, eds_):") < _sbR.index("_nb_, _lp_ = _not_borders(i, eds)") and "in the OUTER loop - the face is made WITH it" in _sbR
          and "the instrument of B20" in _sbR and "the agent's b6" not in _sbR[_sbR.index("def _not_borders(i_, eds_):"):_sbR.index("NOT_BORDER = []")],
          "31bq R6 / R7W (the foreign-edge patch hunk A - the instrument of B20, which stays OPEN): the face stage names every edge a face is given that is no border of it, its loop in the face stage's own order (the outer named as such), an unmeasured distance NOT MEASURED")
    check("def _seg_off_face(e_, f_):" in _sbR and "return dm_, ds_" in _sbR and '_offg_, _offs_ = _seg_off_face(seg_, A)' in _sbR and '"NOT MEASURED"' in _sbR and _sbR.index("def _seg_off_face(e_, f_):") < _sbR.index("_offg_, _offs_ = _seg_off_face(seg_, A)"),
          "31bq R6 / R7W (hunk B, B04 (3)): a straight end line is laid only where it lies on the face against its OWN mesh (the untrimmed surface had read 0 for a chord across a hole of a planar face); an unmeasured one is NOT MEASURED, never laid silently")
    check("A MEMBER LEFT WITH AN OPEN END IS NOT MADE" in _sbR and 'if _pass == "settle": _open_.add(f0_.get("key"))' in _sbR and '_passes_.insert(_ip_, "settle")' in _sbR and "FILLET CHAIN %d: no member is made - face %d keeps its whole border there" in _sbR,
          "31bq R6 / R7W (hunk C, B04 (3)): a chain member whose freed end fits neither the taper nor the cap is dropped after the settle pass (the chain's hole grows, its neighbours freed in another settle) - its strips had been handed to two faces they could not close (fill7j / 7k / 8)")
except Exception as _ex: check(False, "the 31bq R7W (build-chain-retry) pins raised %s" % _ex)
try:
    import ast as _astV, types as _tyV, tempfile as _tfV, io as _ioV, contextlib as _clV, re as _reV, json as _jsV
    _sbV = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read(); _trV = _astV.parse(_sbV)
    _segV = lambda n_: _astV.get_source_segment(_sbV, n_)
    _gV = {"os": os, "sys": sys, "re": _reV, "json": _jsV, "np": np}
    _RETV = None
    for _n in _trV.body:
        if isinstance(_n, _astV.FunctionDef) and _n.name in ("_dup_entries", "_dup_text", "_span_advice"): exec(_segV(_n), _gV)
        if isinstance(_n, _astV.Assign) and any(getattr(_t, "id", "") == "_KIT_SPLIT_RE" for _t in _n.targets): exec(_segV(_n), _gV)
        if isinstance(_n, _astV.If) and "FIL_RERUN" in _segV(_n.test): _RETV = _n
    class _PopV(object):
        script = []; envs = []
        def __init__(self, a_, env=None, **k_):
            ln_, self.rc = _PopV.script.pop(0); _PopV.envs.append(dict(env or {})); self.stdout = iter([l_ + "\n" for l_ in ln_])
        def wait(self): return self.rc
    _CH2V = "   20s  FILLET CHAIN 2 (31bp): 7 member(s) round face 6 - ['34', '39', '55', '74', '77', '93', '110']; 6 shared junction(s) get a corner patch"
    def _openV(n_, ch_): return ([_CH2V, "   80s  shell: 76 faces, closed False, free edges %d" % n_] + ["   81s     free edge 1.200 mm on chain %d concave pair [6, 18] (0.0010 from it) - owned by patch 6, mid [0, 0, 0]" % c_ for c_ in ch_] + ["FAIL: the skin's shell did not close - %d free edge(s) (skin\\free_c.brep; `kit rebuild skin-look` draws them red)" % n_], 1)
    _SIV = (["   90s  shell: 76 faces, closed True, free edges 0", _CH2V, "FAIL: THE SOLID SELF-INTERSECTS beyond the 0.30 mm print tolerance: faces 37 (patch 18F, fillet of line 56 leg 0) x 38 (patch 18F, fillet of line 56 leg 1) 4.16 mm deep (1.40 along) - a face runs through its neighbour"], 1)
    _L17V = [29, 30, 32, 34, 36, 39, 53, 55, 56, 74, 77, 91, 93, 97, 110, 114, 116]
    _PopV.script = [_SIV, _openV(8, [36]), _openV(4, [29]), _openV(9, [91])]; _PopV.envs = []
    _skV = _tfV.mkdtemp(prefix="skin5_v1_")
    for _f in ("piece_skin.brep", "piece_faces.json", "solid_c.json", "build_c.json", "faces_c.brep", "shell_c.brep"): open(os.path.join(_skV, _f), "w").write("SHARP")
    _nsV = dict(_gV, SK=_skV, FIL_RERUN=list(_L17V), FILLETS=[{"line": x_} for x_ in _L17V], _PASS_LINE="SKIN BUILD PASS: 49 faces (the sharp piece)", __file__="sk_build.py", say=lambda *a_: None)
    _fakeV = _tyV.ModuleType("subprocess"); _fakeV.Popen = _PopV; _fakeV.PIPE = -1; _fakeV.STDOUT = -2; _oldV = sys.modules.get("subprocess"); sys.modules["subprocess"] = _fakeV; _bufV = _ioV.StringIO()
    try:
        with _clV.redirect_stdout(_bufV):
            try: exec(_segV(_RETV), _nsV)
            except SystemExit: pass
    finally:
        if _oldV is not None: sys.modules["subprocess"] = _oldV
    _oV = _bufV.getvalue()
    check(len(_PopV.envs) == 4 and "no better than the 0 before" not in _oV and "fewer than the 8 before" in _oV and "no better than the 4 before: no further retry" in _oV,
          "31bq R7W (the verifier's V1): after a crossing stage (a closed shell, count 0) the first open shell's count is the retry's baseline - 8 -> 4 goes on, 4 -> 9 stops (%d children; the 0 had stopped the improving retry)" % len(_PopV.envs))
    _gtV = _sbV[_sbV.index('_chk = "check(True) OK"'):_sbV.index("# 31ax: a fillet the kernel failed is made by DRAWN LINES")]
    class _FV(Exception): pass
    def _ffV(m_): raise _FV(m_)
    _saidV = []
    _ggV = {"res": {"faces": 75, "closed": True, "valid": True, "check_faces": [], "self_intersections": [[2, 40, 0.14, 0.0], [40, 42, 0.14, 0.0]], "check": "OK"}, "FRAME": True,
            "K": _tyV.SimpleNamespace(_fail=_ffV), "say": lambda *a_: _saidV.append(" ".join(map(str, a_))), "print": lambda *a_, **k_: _saidV.append(" ".join(map(str, a_)))}
    try: exec(_gtV, _ggV); _okV = True
    except Exception as _exV: _okV = False; _saidV.append("raised %r" % _exV)
    check(_okV and any(s_.startswith("SKIN BUILD PASS: 75 faces") and "2 face pair(s) TOUCH" in s_ for s_ in _saidV),
          "31bq R7W: the gate slice (`_chk =` to the lines pass) runs alone on {res, FRAME, K, say, print} as build-depth's pin runs it - the made / sharp suffix above it, read by globals() (%s)" % (" | ".join(_saidV)[:120]))
except Exception as _ex: check(False, "the 31bq R7W (build-chain-retry, verification) pins raised %s" % _ex)
try:
    import types as _tyC
    _sbC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read(); _LC = _sbC.split("\n")
    _i0C = next(i_ for i_, l_ in enumerate(_LC) if l_.strip() == "# THE STRIPS"); _i1C = next(i_ for i_ in range(_i0C, len(_LC)) if _LC[i_].strip() == 'if os.environ.get("FIL_DBG") == "1":')
    import textwrap as _twC, ast as _astC
    _codeC = compile(_twC.dedent("\n".join(_LC[_i0C:_i1C])), "sk_build.py:strips", "exec")
    class _VecC(object):
        def __init__(s, x, y=None, z=None):
            if y is None: x, y, z = x
            s.x, s.y, s.z = float(x), float(y), float(z)
        def distanceToPoint(s, o): return float(np.linalg.norm(np.array([s.x - o.x, s.y - o.y, s.z - o.z])))
        @property
        def Length(s): return float(np.linalg.norm([s.x, s.y, s.z]))
        def __sub__(s, o): return _VecC(s.x - o.x, s.y - o.y, s.z - o.z)
    class _VxC(object):
        def __init__(s, p): p = np.asarray(p, float); s.X, s.Y, s.Z = p; s.Point = _VecC(p)
    class _VsC(object):
        def __init__(s, v): s.p = np.array([v.x, v.y, v.z])
    class _SegC(object):
        _n = 0
        def __init__(s, a, b, tag=""):
            s.a = np.asarray(a, float); s.b = np.asarray(b, float); s.tag = tag; _SegC._n += 1; s.id = _SegC._n
            s.Vertexes = [_VxC(s.a), _VxC(s.b)]; s.Length = float(np.linalg.norm(s.b - s.a)); s.FirstParameter = 0.0; s.LastParameter = s.Length
            s.Curve = _tyC.SimpleNamespace(parameter=lambda v: s._par(np.array([v.x, v.y, v.z])))
        def _par(s, p):
            d = s.b - s.a; L2 = float(d @ d)
            return 0.0 if L2 < 1e-18 else float(np.clip((p - s.a) @ d / L2, 0, 1)) * s.Length
        def valueAt(s, u): return _VecC(s.a + (s.b - s.a) * (u / max(s.Length, 1e-12)))
        def distToShape(s, o):
            p = o.p; u = s._par(p); q = s.a + (s.b - s.a) * (u / max(s.Length, 1e-12))
            return float(np.linalg.norm(q - p)), [(_VecC(q), _VecC(p))], [("Edge", 0, u)]
        def isSame(s, o): return o is s
        def hashCode(s): return s.id
        def split(s, prms):
            u = prms[0]; m = s.a + (s.b - s.a) * (u / s.Length)
            return _tyC.SimpleNamespace(Edges=[_SegC(s.a, m, s.tag + "a"), _SegC(m, s.b, s.tag + "b")])
        def toShape(s): return s
    _PartC = _tyC.SimpleNamespace(Vertex=lambda v_: _VsC(v_), LineSegment=lambda a_, b_: _SegC([a_.x, a_.y, a_.z], [b_.x, b_.y, b_.z], "STRAIGHT"))
    _V3C = lambda *a_: _VecC(*a_) if len(a_) == 3 else _VecC(a_[0])
    _gC = {"np": np, "Part": _PartC, "V3": _V3C, "os": os, "THIN_FIL": 0.3, "kind": ["orig"], "_seg_off_face": (lambda e_, f_: (0.0, None)), "_CUT_WHY": {}}
    for _n in _astC.parse(_sbC).body:
        if isinstance(_n, _astC.FunctionDef) and _n.name in ("_flat_e", "_vpt", "_cut_chain_at", "_cut_chain_once", "_crease_path", "_frags"): exec(_astC.get_source_segment(_sbC, _n), _gC)
        if isinstance(_n, _astC.ClassDef) and _n.name == "_Uncut": exec(_astC.get_source_segment(_sbC, _n), _gC)
    _PC = [np.array(p_, float) for p_ in ([0, 0, 0], [5, 0, 0], [5, 5, 0], [0, 5, 0])]
    _AE = [None] + [_SegC(_PC[a_], _PC[b_], "crease%d" % (a_ + 1)) for a_, b_ in ((0, 1), (1, 2), (2, 3), (3, 0))]
    _memC = [{"line": k_, "_ends": [_PC[(k_ - 1) % 4], _PC[k_ % 4]], "_edge": _AE[k_], "leg": None} for k_ in (1, 2, 3, 4)]
    def _flC(k_, ce_):
        a_, b_ = _PC[(k_ - 1) % 4], _PC[k_ % 4]; pa_ = a_ + [0, 0.5, 0] if ce_[0] else a_; pb_ = b_ + [0, 0.5, 0] if ce_[1] else b_
        return {"name": str(k_), "key": k_, "J": (a_, b_), "chain_end": ce_, "ends": {0: [None, None]}, "lines": {0: (_SegC(pa_, pb_, "off%d" % k_),)}, "meet": {0: [None, None]}, "PEND": {0: [pa_, pb_]}}
    _flsC = [_flC(1, [True, False]), _flC(2, [False, False]), _flC(4, [False, True])]
    _saidC = []; _gC["say"] = lambda m_: _saidC.append(m_); _nsC = dict(_gC); _nsC.update({"fls": _flsC, "_ch": {"members": _memC}, "A": 0, "ALL_E": _AE, "arcs_A": {}, "_cid": 0})
    for _f in ("_crease_path", "_cut_chain_once", "_cut_chain_at", "_frags"): _nsC[_f] = _tyC.FunctionType(_gC[_f].__code__, _nsC, _f, _gC[_f].__defaults__)
    exec(_codeC, _nsC)
    _vsC = {}
    for _e in _nsC["strip_A"]:
        for _p in (_e.a, _e.b): _k = tuple(np.round(_p, 4)); _vsC[_k] = _vsC.get(_k, 0) + 1
    _endsC = sorted(_k for _k, _n in _vsC.items() if _n == 1)
    check(_endsC == [(0.0, 5.0, 0.0), (5.0, 5.0, 0.0)] and any("a closed chain - the strip starts at the hole" in s_ for s_ in _saidC) and not any(_e.tag == "crease3" for _e in _nsC["strip_A"]),
          "31bq R7W (the closed chain): a ring with member 3 not made and a sense change - the walk starts at the hole's end and the strip is an OPEN path ending at the hole's two ends J2 / J3, the hole's crease left as the face's border (ends %s)" % _endsC)
except Exception as _ex: check(False, "the 31bq R7W (the closed chain) pin raised %r" % _ex)
# over the
try:
    import sk_span as _SPr
    _S1 = object()
    _tq = [("mean plane", _S1, 0.0954, 0.0, 0, "enlarge 1.1, edge points every 1.0 mm, 163 points", 0.00),
           ("mean plane", _S1, 0.0900, 0.0, 0, "enlarge 1.3, edge points every 1.0 mm, 163 points", 0.02),
           ("boundary blend", None, 9e9, 9e9, 0, "the PLATE BALLOONS 11.6 mm past its border", None), ("boundary blend", None, 9e9, 9e9, 0, "the PLATE BALLOONS 11.6 mm", None),
           ("boundary blend", None, 9e9, 9e9, 0, "the PLATE BALLOONS 11.6 mm", None),
           ("mean plane", _S1, 0.0586, 0.0, 0, "enlarge 1.2, edge points every 0.3 mm, 551 points", 6.73)]
    _b, _n = _SPr._rank_tries(_tq, 0.08, ceil=0.10)
    check(_b is _tq[1] and bool(_n) and "RISES 6.73 mm" in _n and "over the 0.08 limit, within the kit's 0.10 fill rim" in _n,
          "R7W A4: on qq11's vane plate (patch 4) the ladder takes the 1.3 / 1.0 mm try (rim 0.090 over the 0.08 lever, rise 0.02) over the one that held its rim and rose 6.73 mm into the designed slot - said why (the wall's trade rim 0.10 handed)")
    _b, _n = _SPr._rank_tries(_tq, 0.08)
    check(_b is _tq[5] and _n is None, "R7W A4 (verify-span-fill 11): with no trade rim handed (a fillet cap's 0.02, a wall at the default NURBS_WALL_RIM) nothing is taken past the face's own rim")
    check(_SPr.wall_trade_rim() is (_SPr.NURBS_RIM if _SPr.NURBS_WALL_RIM > 0.02 + 1e-9 else None), "R7W A4 (verify-span-fill 11): a wall face trades to NURBS_RIM only at a loosened NURBS_WALL_RIM (here %s)" % _SPr.NURBS_WALL_RIM)
    _b, _n = _SPr._rank_tries([("mean plane", _S1, 0.1091, 0.0, 0, "1.1", 0.0), ("mean plane", _S1, 0.054, 0.0, 0, "1.3", 0.0)], 0.08)
    check(_b[2] == 0.054 and _n is None, "R7W A4: c1's vane plate - the try that holds its rim and does not rise stands (the rim rank, no note)")
    _b, _n = _SPr._rank_tries([("a", _S1, 0.05, 0.0, 0, "a", 3.9), ("b", _S1, 0.12, 0.0, 0, "b", 3.8), ("c", _S1, 0.20, 0.0, 0, "c", 3.95)], 0.08)
    check(_b[0] == "a" and _n is None, "R7W A4: a rise every try shares (a face that curves past its border's plane-height range) never trades the held rim - the interior must gain more than the print tolerance")
    _b, _n = _SPr._rank_tries([("a", _S1, 0.05, 0.0, 0, "a", 5.0), ("b", _S1, 0.35, 0.0, 0, "b", 0.0)], 0.08)
    check(_b[0] == "a" and _n is None, "R7W A4: a flatter try whose rim misses by more than the 0.30 print tolerance is never taken")
    _b, _n = _SPr._rank_tries([("boundary blend", _S1, 0.052, 0.0, 0, "enlarge 1.3, edge points every 1.0 mm, 32 points", 4.24), ("mean plane", _S1, 0.144, 0.0, 0, "enlarge 1.2, edge points every 0.3 mm, 113 points", 1.33)], 0.10)
    check(_b[0] == "boundary blend" and _n is None, "R7W A4: a flatter try that misses its rim by more than the kit's own fill rim (NURBS_RIM 0.10) is never taken - measured on the qq11 copy (sf1): faces 17 / 19 traded to a 0.144 mm miss and the face build could not take the loop (SPAN FAILED, the shell open)")
    _b, _n = _SPr._rank_tries([("a", _S1, 0.07, 0.0, 0, "a", 0.10), ("b", _S1, 0.02, 0.0, 0, "b", 0.10)], 0.08)
    check(_b[0] == "a" and _n is None, "R7W A4: the rim rank keeps the FIRST try that holds its rim in ladder order (the one the ladder stopped at) - never a later smaller rim")
    _b, _n = _SPr._rank_tries([("a", _S1, 0.05, 0.0, 0, "a", 5.0), ("b", _S1, 0.09, 0.0, 3, "b", 0.0), ("c", _S1, 0.09, 0.0, 0, "c", None)], 0.08)
    check(_b[0] == "a" and _n is None, "R7W A4: a flatter try that folds, or one whose rise was not measured, is never taken over the held rim")
    _b, _n = _SPr._rank_tries([("a", _S1, 0.05, 0.0, 0, "a", None), ("b", _S1, 0.09, 0.0, 0, "b", 0.0)], 0.08)
    check(_b[0] == "a" and _n is None, "R7W A4: an unmeasured rise on the held-rim try keeps the rim rank (nothing to rank by)")
    _b, _n = _SPr._rank_tries([("a", _S1, 0.02, 0.0, 0, "a", 6.0), ("b", _S1, 0.07, 0.0, 0, "b", 0.10), ("c", _S1, 0.05, 0.0, 0, "c", 0.35)], 0.08)
    check(_b[0] == "b" and bool(_n) and "over the" not in _n, "R7W A4: among the flat tries (within the print tolerance of the lowest rise) the first that holds its rim wins, in ladder order")
except Exception as _ex: check(False, "the R7W span-fill rank pin raised %s" % _ex)
try:
    import sk_span as _SPr
    class _P3:
        def __init__(s_, x, y, z): s_.x, s_.y, s_.z = x, y, z
    class _FakeSurf:
        def __init__(s_, L, H, u0, v0, w):
            s_.L, s_.H, s_.u0, s_.v0, s_.w = L, H, u0, v0, w; s_.NbUPoles = s_.NbVPoles = 39; s_.UDegree = s_.VDegree = 3
        def bounds(s_): return 0.0, 1.0, 0.0, 1.0
        def getUKnots(s_): return [float(x) for x in np.linspace(0, 1, 37)]
        getVKnots = getUKnots
        def getUMultiplicities(s_): return [4] + [1] * 35 + [4]
        getVMultiplicities = getUMultiplicities
        def value(s_, u, v): return _P3(u * s_.L, v * s_.L, s_.H * float(np.exp(-((u - s_.u0) ** 2 + (v - s_.v0) ** 2) / (2 * s_.w ** 2))))
        def toShape(s_, *a): raise RuntimeError("no kernel in this suite")
    _kf = np.concatenate([[0.0] * 3, np.linspace(0, 1, 37), [1.0] * 3]); _g20 = float(_kf[21:24].mean())
    _sq = [poly((0, 0, 0), (30, 0, 0)), poly((30, 0, 0), (30, 30, 0)), poly((30, 30, 0), (0, 30, 0)), poly((0, 30, 0), (0, 0, 0))]
    _lp = _SPr.order_loop(_sq)[0]
    _inf = {}; _said = []
    try: _SPr._balloon(_FakeSurf(30.0, 10.0, _g20, _g20, 0.003), _sq, [], _inf, "PLATE", "t", refuse=True, progress=_said.append, loop=_lp); _ref = False
    except _SPr._Balloon: _ref = True
    check(_ref and abs(float(_inf.get("balloon_mm") or 0) - 10.0) < 0.05 and abs(min(abs(_g20 - k_ / 24.0) for k_ in range(25)) - 0.0139) < 0.002,
          "R7W A10: a 10 mm spike of the surface's own basis at a pole's Greville point, 0.014 (parameter) from the nearest 25 x 25 grid sample and unseen by the grid, is REFUSED on the PLATE (limit 6.4) - the Greville samples read it whole")
    _inf = {}; _said = []
    _SPr._balloon(_FakeSurf(30.0, 3.0, _g20, _g20, 0.003), _sq, [], _inf, "NURBS fill", "its rim held", refuse=False, progress=_said.append, loop=_lp)
    check("RISES 3.0 mm" in str(_inf.get("balloon_note")) and "under its size limit 6.4" in str(_inf.get("balloon_note")) and any("RISES 3.0 mm" in m_ for m_ in _said),
          "R7W A4 (B): a NURBS fill's rise under the size limit but over the 0.30 print tolerance is recorded as its note (the build's summary names it) and SAID")
    _inf = {}; _said = []
    _SPr._balloon(_FakeSurf(30.0, 0.2, _g20, _g20, 0.003), _sq, [], _inf, "NURBS fill", "its rim held", refuse=False, progress=_said.append, loop=_lp)
    check(_inf.get("balloon_note") is None and not any("rises" in m_ or "RISES" in m_ for m_ in _said) and abs(float(_inf.get("balloon_mm") or 0) - 0.2) < 0.01,
          "R7W A4 (B): a rise under the 0.30 print tolerance is recorded (balloon_mm) and not said")
    _spR = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_span.py"), encoding="utf-8").read()
    check("under-reads by at most that" not in _spR and "_gu_, _gv_ = _greville_uv(s)" in _spR and "[:2]), rim_tol, loop=loop, progress=progress, trade_rim=trade_rim)" in _spR and "[:2]), NURBS_LOOSE_RIM, loop=loop, progress=progress, trade_rim=trade_rim)" in _spR
          and "and (t_[6] is None or t_[6] <= PRINT_TOL): break" in _spR and "best, rank = _rank_tries(tries, rim_tol, ceil=trade_rim)" in _spR and "h2 <= best[6] + PRINT_TOL" in _spR,
          "R7W A4 / A10: the PP comment's false bound gone; the Greville samples in _balloon; both NURBS rungs hand nurbs_face the loop and progress; the ladder stops early only at a flat held rim; the finer pass may not rise more")
except Exception as _ex: check(False, "the R7W span-fill balloon pin raised %s" % _ex)
try:
    import importlib.util as _ilu
    _sp3 = _ilu.spec_from_file_location("sk_span_pin3", os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_span.py")); _M3 = _ilu.module_from_spec(_sp3); _sp3.loader.exec_module(_M3)
    class _BS3:
        def __init__(s_, i): s_.i = i; s_.NbUPoles = s_.NbVPoles = 9
    def _run3(script, rim_tol, trade_rim=None):
        calls = []
        def _fill(P, init=None, enlarge=1.1, tol=None, maxseg=None):
            i = len(calls); calls.append(i)
            if i >= len(script) or script[i] is None: raise ValueError("scripted: no fill")
            return _BS3(i)
        _M3._nurbs_fill = _fill; _M3.folds = lambda bs, border=None: (script[bs.i][1], 100); _M3._dev = lambda bs, P: script[bs.i][0]; _M3._rise = lambda bs, e, g, l: script[bs.i][2]
        _sq3 = [np.linspace(np.array(a, float), np.array(b, float), 31) for a, b in (((0, 0, 0), (30, 0, 0)), ((30, 0, 0), (30, 30, 0)), ((30, 30, 0), (0, 30, 0)), ((0, 30, 0), (0, 0, 0)))]
        bs, info = _M3.nurbs_face(_sq3, [], lambda: None, rim_tol, trade_rim=trade_rim); return bs.i + 1, info["rim_mm"], info.get("rank")
    _r = _run3([(0.015, 0, 0.45), (0.098, 0, 0.0)], 0.02)
    check(_r[0] == 1 and abs(_r[1] - 0.015) < 1e-9 and _r[2] is None, "R7W A4 (verify-span-fill 11, its E2): a fillet cap (_span_corner(rim_tol=0.02), no trade rim) keeps its held 0.015 rim - never the 0.098 flat try")
    _r = _run3([(0.0954, 0, 0.0), (0.090, 0, 0.02), None, None, None, (0.0586, 0, 6.73)], 0.08, trade_rim=0.10)
    check(_r[0] == 2 and abs(_r[1] - 0.090) < 1e-9 and bool(_r[2]), "R7W A4 (its E7): qq11's patch 4 at the 0.08 wall lever with the trade rim 0.10 handed takes try 2 (rim 0.090, rise 0.02) over try 6's 6.73 mm rise")
    _r = _run3([(0.0954, 0, 0.0), (0.090, 0, 0.02), None, None, None, (0.0586, 0, 6.73)], 0.08)
    check(_r[0] == 6 and _r[2] is None, "R7W A4 (verify-span-fill 11): the same ladder with no trade rim handed keeps the held 0.059 try (the control's choice)")
    # over the
    class _P3b:
        def __init__(s_, x, y, z): s_.x, s_.y, s_.z = x, y, z
    class _Fold:
        L = 30.0; NbUPoles = NbVPoles = 20; UDegree = VDegree = 3
        def bounds(s_): return 0.0, 1.3, 0.0, 1.0
        def getUKnots(s_): return [float(x) for x in np.linspace(0, 1.3, 18)]
        def getVKnots(s_): return [float(x) for x in np.linspace(0, 1.0, 18)]
        def getUMultiplicities(s_): return [4] + [1] * 16 + [4]
        getVMultiplicities = getUMultiplicities
        def value(s_, u, v):
            x = s_.L * (u if u <= 1.0 else 2.0 - u); z = 5.0 * float(np.exp(-((u - 1.15) ** 2) / (2 * 0.02 ** 2))) if u > 1.0 else 0.0
            return _P3b(x, s_.L * v, z)
        def parameter(s_, p): return (float(p[0]) / s_.L, float(p[1]) / s_.L)
        def toShape(s_, *a): raise RuntimeError("no kernel in this suite")
    _sqF = [poly((0, 0, 0), (30, 0, 0)), poly((30, 0, 0), (30, 30, 0)), poly((30, 30, 0), (0, 30, 0)), poly((0, 30, 0), (0, 0, 0))]; _lpF = _SPr.order_loop(_sqF)[0]
    _iw = {}; _SPr._balloon(_Fold(), _sqF, [], _iw, "NURBS fill", "t", refuse=False, progress=None, loop=_lpF)
    _rf = _SPr._rise(_Fold(), _sqF, [], _lpF); _uvF = _SPr._rim_uv(_Fold(), _lpF)
    check(float(_iw.get("balloon_mm") or 0) > 2.0 and _rf is not None and _rf < 0.05 and _uvF is not None and abs(_uvF[1] - 1.0) < 1e-6,
          "R7W A4 (verify-span-fill 10): a rise on the enlarged margin folded back over the face is read by the whole surface (%.2f) and NOT by the face's own uv range (%s; the rim's u up to %s)" % (float(_iw.get("balloon_mm") or 0), _rf, None if _uvF is None else round(_uvF[1], 3)))
except Exception as _ex: check(False, "the R7W span-fill verify pin raised %s" % _ex)
try:
    _swW = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_wires.py"), encoding="utf-8").read()
    _sbW = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    _krW = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit_rebuild.py"), encoding="utf-8").read()
    def _grabW(name):
        i_ = _swW.index("def %s(" % name); ls_ = _swW[i_:].split("\n"); o_ = [ls_[0]]
        for l_ in ls_[1:]:
            if l_.strip() and not l_.startswith((" ", "\t")): break
            o_.append(l_)
        return "\n".join(o_) + "\n"
    import re as _reW, hashlib as _hlW
    _gW = {"_re_w": _reW, "hashlib": _hlW, "json": json}
    for _fW in ("_strip_carry", "_new_add_id", "_add_match"): exec(_grabW(_fW), _gW)
    _pfx = lambda f_: "[carried from face %s by its drawn ends] " % f_
    _w0 = "fix 11: cross curve at y -110"; _w1 = "fix 11: cross curve at y -120"
    _dr = [{"entry": i_, "face": 18, "role": "guide", "mirror_of": None, "why": w_, "edge": i_} for i_, w_ in enumerate([_pfx(17) + _pfx(18) + _w0, _pfx(17) + _pfx(18) + _w1])]
    _m1, _ = _gW["_add_match"]({"face": 18, "role": "guide", "why": _pfx(17) + _pfx(18) + _w1}, 0, _dr)
    _dd = [{"entry": i_, "face": 18, "role": "guide", "mirror_of": None, "why": _w0, "edge": i_} for i_ in (0, 1)]
    _m2, _y2 = _gW["_add_match"]({"face": 18, "role": "guide", "why": _w0}, 0, _dd)
    _di = [dict(r_, add_id="a%010d" % i_) for i_, r_ in enumerate(_dd)]
    _m3, _ = _gW["_add_match"]({"face": 18, "role": "guide", "why": _w0, "id": "a0000000001"}, 0, _di)
    check(_m1 is not None and _m1["edge"] == 1 and _m2 is None and "cannot be told" in str(_y2) and _m3 is not None and _m3["edge"] == 1
          and _gW["_strip_carry"](_pfx(19) + _pfx(18) + "[carried from lines [3, 4]] " + _w1) == _w1,
          "31bq R7W (M5, B1 1): an _add entry is matched to the last run's drawn edge by the kit's id, else by face + role + its WHOLE reason with the carry tags stripped (a deleted first entry no longer carries the second onto its edge after two carries); two candidates are TO DECIDE, never the first")
    check("_add_match(a_, ai_, _pgr)" in _swW and "id=(str(m_.get(\"add_id\") or \"\").strip() or _new_add_id(a_, ai_))" in _swW and "_strip_carry(a_.get(\"why\", \"\"))[:300]" in _swW
          and "\"add_id\": (str(a_.get(\"id\") or \"\").strip() or _new_add_id(a_, ai_))" in _swW and _swW.count("_strip_carry(f_.get(\"why\", \"\"))[:300]") == 2,
          "31bq R7W (M5): the carried entry gets ONE tag (the old ones stripped) and the matched line's id; every drawn line records its id; a fillet's carry tag is replaced too")
    _rd = dict(_reW.findall(r'\("([A-Z_]+)", "([0-9.]+)"\)', _swW[_swW.index("ROOM_DEF = ("):_swW.index("ROOM_DEF = (") + 400]))
    _bd = {k_: _reW.search(r'environ\.get\("%s", "([0-9.]+)"\)' % k_, _sbW).group(1) for k_ in _rd}
    _kl = _reW.search(r"ROOM_LEVERS = \(([^)]*)\)", _krW).group(1)
    check(_rd and _rd == _bd and sorted(_reW.findall(r'"([A-Z_]+)"', _kl)) == sorted(_rd),
          "31bq R7W (M8): the room levers are ONE decision - sk_wires' ROOM_DEF defaults equal sk_build's own (%s) and kit_rebuild's ROOM_LEVERS names the same levers" % ", ".join("%s %s" % kv for kv in sorted(_rd.items())))
    check("\"room_levers\": ROOM_LV}" in _swW and "\"room_levers\": dict(ROOM_LV)," in _swW and "def room_levers_check(folder, env):" in _krW and "okl_, whyl_ = room_levers_check(folder, env)" in _krW and "THE ROOM LEVERS DIFFER" in _krW,
          "31bq R7W (M8): skin-wires records the levers its room line used (fillets.json, WIRES_LOOK.json); the runner's skin-build gate refuses a build whose levers differ, by name")
    check("def _across(T__, ridge__):" in _swW and "K.mesh_plane_section(Vu, T__[m__], _u_, c__)" in _swW and "_gap_ = ~_hit" in _swW and "np.abs((_Sq - S_) @ _u_) > _st_" not in _swW
          and "if a_.get(\"span\") is not None:" in _swW and "span_=a_.get(\"span\")" in _swW and "follows_nopoint" in _swW and "the curve is interpolated across that stretch" in _swW and "spans that stretch straight" not in _swW,
          "31bq R7W (M6, NEW #9): a trace sample is a GAP only where no triangle of its face crosses the plane normal to the line (OO's 'nearest point a step along the line' rule removed), the curve interpolated across it; a region the design closes is the entry's \"span\"; the faces it follows and those the points dropped are said")
    check("def _end_note(r_, X_):" in _swW and "_end_note(r_, P_[i_])" in _swW and "a trace takes no \\\"via\\\" points" in _swW and "_twin_fid(x_) not in _present" in _swW and "_left9 = sorted(set(" in _swW and "line_off_max=LINE_OFF_MAX)" in _swW,
          "31bq R7W (B1 6 / 7 / 5 / 9 / 11): an added line's END off the part names the border it sits on (and a moved junction); a trace's remedy no longer offers \"via\"; a buried id whose mirror twin is on the group is no 'wrong id'; a twin chain partly written names the twins left sharp; LINE_OFF_MAX is in the WIRE frames' key")
except Exception as _ex: check(False, "the 31bq R7W wires pins raised %s" % _ex)
try:
    import io as _io, contextlib as _cl, math as _m, tempfile as _tfm, json as _js, hashlib as _hm, shutil as _sh
    _rbs = open(os.path.join(HERE, "rebuild", "rb_reinsert.py"), encoding="utf-8").read()
    _lp = _rbs[_rbs.index("def load_protect():"):_rbs.index("load_protect.source = None\n") + len("load_protect.source = None\n")]
    _tdp = _tfm.mkdtemp(prefix="skin5_tf_"); _js.dump({"protect": [[0, 1, 0, 1, 0, 1], [2, 3, 2, 3, 2, 3]]}, open(os.path.join(_tdp, "REBUILD_region.json"), "w"))
    def _ff(m_): raise RuntimeError(m_)
    _gp = {"os": os, "json": _js, "P": lambda p_: os.path.join(_tdp, p_), "say": lambda *a_: None, "_fail": _ff}
    exec(_lp, _gp); _pv = os.environ.get("PROTECT"); os.environ["PROTECT"] = ""
    try: _bx = _gp["load_protect"](); _src = _gp["load_protect"].source
    finally:
        if _pv is None: os.environ.pop("PROTECT", None)
        else: os.environ["PROTECT"] = _pv
    check(len(_bx) == 2 and "REBUILD_region.json" in str(_src), "R7W tester-findings (1): PROTECT='' is UNSET - the region's 2 boxes are checked and their record named (%s)" % (_src,))
    _kt = open(os.path.join(HERE, "kit.py"), encoding="utf-8").read(); _i = _kt.index("# 31bq B16: a self-intersection the build itself recorded"); _j = _kt.index("if worst > 0.3: fails.append", _i)
    _skd = os.path.join(_tdp, "skin"); os.makedirs(_skd); _sic = os.path.join(_skd, "solid_c.json"); _blk = _kt[_i:_j].replace("%(sic)r", repr(_sic)).replace("%%", "%")
    _pp = os.path.join(_skd, "piece_skin.brep"); open(_pp, "w").write("P"); _mk = _hm.md5(b"P").hexdigest()
    _kb = {"self_intersections": [], "si_searched": True, "si_unmeasured_pairs": 0, "piece_md5": _mk, "si_self_faces": [], "edge_off_max": 0.01, "check": "OK", "check_selfintersect": False}
    def _kc(rec_):
        open(_sic, "w").write(rec_ if isinstance(rec_, str) else _js.dumps(rec_)); _g = {"os": os, "json": _js, "fails": [], "rep": {}}
        with _cl.redirect_stdout(_io.StringIO()): exec(_blk, _g)
        return _g["fails"]
    _f0 = _kc(_kb); _f1 = _kc({k_: v_ for k_, v_ in _kb.items() if k_ != "edge_off_max"}); _f2 = _kc("[1, 2]"); _f3 = _kc(dict(_kb, edge_gaps_unmeasured=3))
    check(not _f0 and any("NOT READ" in x_ for x_ in _f1) and any("cannot be read" in x_ for x_ in _f2) and any("NOT MEASURED" in x_ for x_ in _f3),
          "R7W tester-findings (2) / (6): kit check FAILS an edge gap it cannot read, a record that is JSON but no object and edge gaps the build could not measure; the clean record passes")
    _gi = _rbs.index("    _COSMETIC = {"); _gj = _rbs.index("    if bad and not BOP_OK:\n        _fail(", _gi); _gb = "\n".join(l_[4:] for l_ in _rbs[_gi:_gj].splitlines()) + "\n"
    def _gate(rec_):
        open(_sic, "w").write(_js.dumps(rec_)); _bad = [{"solid": 0, "kinds": {"InvalidCurveOnSurface": 1}, "max_edge_tol": 0.01, "max_vertex_tol": 0.01, "check_true": False}]
        _g = {"os": os, "json": _js, "math": _m, "RUN": _tdp, "P": lambda p_: os.path.join(_tdp, p_), "say": lambda *a_: None, "bad": _bad, "BOP_OK": ""}
        _pe = os.environ.get("PIECE"); os.environ["PIECE"] = _pp
        try: exec(_gb, _g)
        finally:
            if _pe is None: os.environ.pop("PIECE", None)
            else: os.environ["PIECE"] = _pe
        return _g["bad"]
    check(not _gate(dict(_kb, edge_gaps_unmeasured=0)) and _gate(dict(_kb, edge_gaps_unmeasured=3)) and not _gate(_kb),
          "R7W tester-findings (6): the reinsert gate refuses a curve-on-surface piece whose edge gaps went UNMEASURED; 0 and an older record (no key) pass as before")
    _sh.rmtree(_tdp, ignore_errors=True)
except Exception as _ex: check(False, "the R7W tester-findings pin raised %r" % (_ex,))
# skin-build
# NOT CLEARED
try:
    import textwrap as _twX, types as _tyX, math as _mX
    from scipy.spatial import cKDTree as _ckdX
    _sbX = open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read(); _slX = open(os.path.join(HERE, "rebuild", "sk_lib.py"), encoding="utf-8").read()
    _iX = _slX.index("def _closest_pt_tri("); _LX = _slX[_iX:].splitlines(); _bodyX = [_LX[0]]
    for _lX in _LX[1:]:
        if _lX.strip() and not _lX.startswith((" ", "\t")): break
        _bodyX.append(_lX)
    _gX = {"np": np}; exec("\n".join(_bodyX), _gX)
    _BX = _twX.dedent(_sbX[_sbX.index("            _fs = so.Faces; _eh = "):_sbX.index('            with busy("self-intersection search')])
    class _P3X:
        def __init__(s, p): s.x, s.y, s.z = float(p[0]), float(p[1]), float(p[2])
    class _EX:
        def hashCode(s): return id(s)
    class _FX:
        def __init__(s, V, T): s.V = np.asarray(V, float); s.T = np.asarray(T, int); s.Edges = [_EX()]
        def hashCode(s): return id(s)
        def copy(s): return s
        def tessellate(s, tol): return [_P3X(v) for v in s.V], [tuple(int(i) for i in t) for t in s.T]
    class _SecX:
        def __init__(s, f, df, a, b): s.f, s.df, s.FirstParameter, s.LastParameter, s.Length = f, df, a, b, float(b - a)
        def valueAt(s, t): return _P3X(s.f(t))
        def tangentAt(s, t): return _P3X(s.df(t))
    def _nsX(faces):
        g_ = {"np": np, "cKDTree": _ckdX, "K": _tyX.SimpleNamespace(_closest_pt_tri=_gX["_closest_pt_tri"]), "Part": _tyX.SimpleNamespace(Vertex=lambda *a: a), "so": _tyX.SimpleNamespace(Faces=faces), "res": {}, "say": lambda *a: None}
        exec(_BX, g_); return g_
    def _quadX(fun, u0, u1, v0, v1):
        V_ = [fun(u0, v0), fun(u1, v0), fun(u1, v1), fun(u0, v1)]; return _FX(V_, [(0, 1, 2), (0, 2, 3)])
    def _shareX(a, b): e_ = _EX(); a.Edges.append(e_); b.Edges.append(e_)
    _fanX = _FX([(0, 0, 0), (1, 0, 0), (1, 0.5, 0), (0.5, 1, 0), (0, 1, 0), (1, 1, 0)], [(0, 2, 3), (0, 1, 2), (0, 3, 4), (2, 5, 3)]); _g7X = _nsX([_fanX]); _M7X = _g7X["_fmesh"](_fanX)
    check(_g7X["_foot"](_M7X, np.array([-0.3, -0.3, 0.1]))[3] is False and _g7X["_foot"](_M7X, np.array([0.6, 0.6, 0.2]))[3] is True,
          "31bq R7W (A7): a foot AT a border vertex - a point past a fan's corner reached through its middle triangle - is no true foot; an interior foot is (a way had run on past the other face's corner: 6.42 mm for a 0.108 mm way in 480 of 720 fan orders)")
    _cX, _sX = _mX.cos(_mX.radians(10.0)), _mX.sin(_mX.radians(10.0))
    _PX = _quadX(lambda u, v: (u, v, 0.0), -10, 10, 1, 8); _SX = _quadX(lambda u, v: (u, v, 0.0), -10, 10, -1, 1); _QX = _quadX(lambda u, v: (u, v, 0.0), -10, 10, -8, -1)
    _WX = _quadX(lambda u, v: (u, v * _cX, v * _sX), -9, 9, -7.5, 7.5); _shareX(_PX, _SX); _shareX(_SX, _QX)
    _d8X = _nsX([_PX, _SX, _QX, _WX])["_si_depth"](_SX, _WX, [_SecX(lambda t: (t, 0.0, 0.0), lambda t: (1.0, 0.0, 0.0), -9.0, 9.0)], 1, 3)
    check(_d8X[0] is not None and abs(_d8X[0] - 1.302) < 0.03 and _d8X[2] is not None and len(_d8X[2]) == 2,
          "31bq R7W (A8): a crossing through a NARROW face reads its deep arm under the faces beyond it (the reference the other face and its neighbours; the pair the LARGER face): a 2 mm strip at 10 deg -> %s (truth 1.302; the smaller-face rule read 0.173 and passed)" % (None if _d8X[0] is None else round(_d8X[0], 3)))
    _FlX = _quadX(lambda u, v: (u, v, 0.0), -10, 10, -8, 8); _WlX = _quadX(lambda u, v: (u, 0.0, v), -9, 9, -0.05, 6.0); _WrX = _quadX(lambda u, v: (u, 1.0, v), -9, 9, 6.0, -0.05)
    _BtX = _quadX(lambda u, v: (u, v, -0.05), -9, 9, 1.0, 0.0); _TpX = _quadX(lambda u, v: (u, v, 6.0), -9, 9, 0.0, 1.0)
    for _aX, _bX in ((_WlX, _BtX), (_WrX, _BtX), (_WlX, _TpX), (_WrX, _TpX)): _shareX(_aX, _bX)
    _dfX = _nsX([_FlX, _WlX, _WrX, _BtX, _TpX])["_si_depth"](_FlX, _WlX, [_SecX(lambda t: (t, 0.0, 0.0), lambda t: (1.0, 0.0, 0.0), -9.0, 9.0)], 0, 1)
    check(_dfX[0] is not None and abs(_dfX[0] - 0.05) < 0.01, "31bq R7W (A8): a fin's bottom 0.05 mm through a floor in a closed piece reads %s (truth 0.05) - the surface beyond the fin's wall bounds the floor's arm" % (None if _dfX[0] is None else round(_dfX[0], 3)))
    _rhoX, _tX = 20.0, _mX.tan(_mX.radians(8.0)); _fzX = lambda x: _mX.sqrt(_rhoX * _rhoX - x * x) - _rhoX; _dxX = _mX.sqrt(8 * _rhoX * 0.015)
    def _gxX(fz, xs):
        xs = np.unique(np.round(np.concatenate([[-6.0], xs[(xs > -6.0) & (xs < 6.0)], [6.0]]), 9)); ys = np.arange(-2.0, 2.0 + 1e-9, 0.5); n_ = len(xs)
        V_ = [[x, y, fz(x)] for y in ys for x in xs]; T_ = []
        for j in range(len(ys) - 1):
            for i in range(n_ - 1):
                a, b, c, d = j * n_ + i, j * n_ + i + 1, (j + 1) * n_ + i, (j + 1) * n_ + i + 1; T_ += [(a, b, d), (a, d, c)]
        return _FX(V_, T_)
    _RnX = _gxX(_fzX, (np.arange(-60, 61) + 0.5721694229026519) * _dxX); _WnX = _gxX(lambda x: _fzX(x) + _tX * x, (np.arange(-80, 81) + 0.13157852062726105) * _dxX * 0.83)
    _d6X = _nsX([_RnX, _WnX])["_si_depth"](_RnX, _WnX, [_SecX(lambda t: (0.0, t, 0.0), lambda t: (0.0, 1.0, 0.0), -2.0, 2.0)], 0, 1)
    check(_d6X[0] is not None and _d6X[0] > 0.6, "31bq R7W (A6): a deep crossing at 8 deg whose meshes disagree near the section reads %s (the unsigned walk 0.775) - the side and a crossing back only past the band (2 x 0.015 mm); R5a's walk read 0.000" % (None if _d6X[0] is None else round(_d6X[0], 3)))
    _sX8, _cX8 = _mX.sin(_mX.radians(8.0)), _mX.cos(_mX.radians(8.0)); _vpX = 2.9 / _cX8
    class _FKX(_FX):
        def __init__(s, fun, u0, u1, v0, v1, vk):
            V_ = [fun(u0, v0), fun(u1, v0), fun(u1, v1), fun(u0, v1)]; _FX.__init__(s, V_, [(0, 1, 2), (0, 2, 3)]); s.fun = fun; s.dom = (u0, u1, v0, v1); s.vk = vk
            O_ = np.asarray(fun(0.0, 0.0), float); s.O = O_; s.A = np.asarray(fun(1.0, 0.0), float) - O_; s.B = np.asarray(fun(0.0, 1.0), float) - O_
            S_ = _tyX.SimpleNamespace(); S_.parameter = lambda v: tuple(float(x) for x in np.linalg.lstsq(np.array([s.A, s.B]).T, np.array([v.x, v.y, v.z]) - s.O, rcond=None)[0]); S_.value = lambda u, v: _P3X(s.O + u * s.A + v * s.B); s.Surface = S_
        def normalAt(s, u, v): n_ = np.cross(s.A, s.B); return _P3X(n_ / np.linalg.norm(n_))
        def isPartOfDomain(s, u, v): return s.dom[0] - 1e-9 <= u <= s.dom[1] + 1e-9 and s.dom[2] - 1e-9 <= v <= s.dom[3] + 1e-9
        def distToShape(s, vx):
            p_ = np.array(vx, float); u, v = s.Surface.parameter(_P3X(p_)); uc = min(max(u, s.dom[0]), s.dom[1]); vc = min(max(v, s.dom[2]), s.vk); q_ = s.O + uc * s.A + vc * s.B
            return float(np.linalg.norm(p_ - q_)), [(_P3X(q_), _P3X(p_))], [("Face" if (uc == u and vc == v) else "Edge", 0, None, "Vertex", 0, None)]
    _RkX = _FKX(lambda u, v: (u, v, 0.0), -10, 10, -8.0, 3.0, 2.0); _WkX = _FKX(lambda u, v: (u, v * _cX8, -v * _sX8), -9, 9, -7.5, _vpX, _vpX - 1.0)
    _nkX = _nsX([_RkX, _WkX]); _nkX["Part"] = _tyX.SimpleNamespace(Vertex=lambda *a: a); _nkX["V3"] = lambda x, y, z: _P3X((x, y, z))
    _dkX = _nkX["_si_depth"](_RkX, _WkX, [_SecX(lambda t: (t, 0.0, 0.0), lambda t: (1.0, 0.0, 0.0), -9.0, 9.0)], 0, 1)
    check(_dkX[0] is not None and _dkX[0] > 0.39 and _nkX["_si_kcut"][0] == 0, "31bq R7W (A8, 2nd round): a 0.41 mm crossing whose faces' distToShape says Edge 1 mm short of the mesh, the pcurve domain the mesh's: read %s, %d way(s) cut back - the kernel confirms by the projection's trimmed domain, never the support type (the support type had read 0.280 and PASSED)" % (None if _dkX[0] is None else round(_dkX[0], 3), _nkX["_si_kcut"][0]))
    # not taken
    _FlU = _quadX(lambda u, v: (u, v, 0.0), -10, 10, -8, 8); _WlU = _quadX(lambda u, v: (u, 0.0, v), -9, 9, -0.05, 6.0); _WrU = _quadX(lambda u, v: (u, 1.0, v), -9, 9, 6.0, -0.05)
    _BtU = _quadX(lambda u, v: (u, v, -0.05), -9, 9, 1.0, 0.0); _TpU = _quadX(lambda u, v: (u, v, 6.0), -9, 9, 0.0, 1.0)
    for _aX, _bX in ((_WlU, _BtU), (_WrU, _BtU), (_WlU, _TpU), (_WrU, _TpU)): _shareX(_aX, _bX)
    def _noMesh(tol): raise RuntimeError("crafted: no mesh")
    _BtU.tessellate = _noMesh
    _nuX = _nsX([_FlU, _WlU, _WrU, _BtU, _TpU]); _duX = _nuX["_si_depth"](_FlU, _WlU, [_SecX(lambda t: (t, 0.0, 0.0), lambda t: (1.0, 0.0, 0.0), -9.0, 9.0)], 0, 1)
    check(_duX[0] is not None and abs(_duX[0] - 0.05) < 0.01 and _nuX["_si_inc"], "31bq R7W (A8, 2nd round): the closed fin 0.05 mm through a floor with its bottom UNMESHED reads %s (truth 0.05; 7.998 FAIL when the union's loss was silent) - the incomplete reference's reading is not taken as the larger, and the pair is recorded (si_depth_incomplete %s)" % (None if _duX[0] is None else round(_duX[0], 3), _nuX["_si_inc"]))
    _gtX = _sbX[_sbX.index('_chk = "check(True) OK"'):_sbX.index("# 31ax: a fillet the kernel failed is made by DRAWN LINES")]
    class _FailX(Exception): pass
    def _gateX(rec):
        def _f(m): raise _FailX(m)
        _said = []; g_ = {"res": dict(rec), "FRAME": True, "K": _tyX.SimpleNamespace(_fail=_f), "say": lambda *a: _said.append(" ".join(str(x) for x in a)), "print": lambda *a, **k: _said.append(" ".join(str(x) for x in a))}
        try: exec(_gtX, g_); return "PASS", " | ".join(_said)
        except _FailX as ex: return "FAIL", str(ex)
    _bX9 = {"faces": 75, "closed": True, "valid": True, "check_faces": []}; _SIX = "BOP check found the following errors:\nError in Face: BOPAlgo SelfIntersect\n"
    _v1, _t1 = _gateX(dict(_bX9, self_intersections=[[2, 40, 0.14, None]], check=_SIX, check_selfintersect=True))
    _v2, _t2 = _gateX(dict(_bX9, self_intersections=[[2, 40, 0.5, None]], check="BOP check found the following errors:\nError in Face: BOPAlgo InvalidCurveOnSurface\n", check_selfintersect=False))
    _v3, _t3 = _gateX(dict(_bX9, self_intersections=[[2, 40, 0.14, 0.0], [40, 42, 0.14, 0.0]], check=_SIX, check_selfintersect=True))
    _v4, _t4 = _gateX(dict(_bX9, self_intersections=[[2, 40, 0.14, 0.5]], check=_SIX, check_selfintersect=True))
    check(_v1 == "FAIL" and "NOT CLEARED" in _t1 and "UNMEASURED depth" in _t1 and "faces 2 x 40 (0.14 mm along)" in _t1 and _t1.startswith("FAIL: THE SOLID SELF-INTERSECTS"),
          "31bq R7W (A9): the build's own gate - an UNMEASURED depth under a check(True) that says SelfIntersect is NOT CLEARED, said with its faces (it had been cleared by its 0.14 mm length; the reinsert gate and kit check refuse the same record)")
    check(_v2 == "PASS" and "UNMEASURED" in _t2 and "noted, not judged" in _t2 and _v3 == "PASS" and _v4 == "FAIL" and "0.50 mm deep" in _t4,
          "31bq R7W (A9): without SelfIntersect an unmeasured depth is noted, not judged (as kit check), whatever its length; measured 0.00 touches pass; a measured 0.5 mm crossing fails by its depth")
except Exception as _ex: check(False, "the 31bq R7W build-depth pin raised %s" % _ex)
# skin-build
# makeFillet
# makeFillet  recorded
# FIL_RERUN
try:
    import ast as _astK, types as _tyK, contextlib as _clK
    _sbK = open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read()
    _iK = _sbK.index("    if FILLETS and so.isValid():\n"); _jK = _sbK.index("    if nfil:      # 31bq R5g", _iK)
    _blkK = "\n".join(l_[4:] if l_.startswith("    ") else l_ for l_ in _sbK[_iK:_jK].splitlines()) + "\n"
    _defsK = [_astK.get_source_segment(_sbK, _n) for _n in _astK.parse(_sbK).body if isinstance(_n, _astK.FunctionDef) and _n.name in ("_flat_e", "_kernel_chain_of")]
    class _VK(object):
        def __init__(s, p): s.X, s.Y, s.Z = [float(x) for x in p]; s.x, s.y, s.z = s.X, s.Y, s.Z
    class _EK(object):
        """a stand-in edge of line k: a straight 5 mm segment"""
        def __init__(s, k, a, b): s.k = k; s.a = np.array(a, float); s.b = np.array(b, float); s.Length = float(np.linalg.norm(s.b - s.a)); s.Vertexes = [_VK(a), _VK(b)]; s.FirstParameter = 0.0; s.LastParameter = 1.0
        def valueAt(s, t): return _VK(s.a + float(t) * (s.b - s.a))
        def distToShape(s, v):
            p_ = np.array([v.x, v.y, v.z]); t_ = float(np.clip((p_ - s.a) @ (s.b - s.a) / max(s.Length ** 2, 1e-12), 0.0, 1.0)); return (float(np.linalg.norm(s.a + t_ * (s.b - s.a) - p_)), None, None)
        def isSame(s, o): return o is s
    class _SoK(object):
        """a stand-in solid: its edges the lines' segments; makeFillet SUCCEEDS on the lines in ok_ (a valid solid of the same volume), raises on the rest; every call counted"""
        def __init__(s, edges, ok_, calls): s.Edges = edges; s.Faces = []; s.ShapeType = "Solid"; s.Volume = 100.0; s._ok = ok_; s._calls = calls
        def isValid(s): return True
        def makeFillet(s, r, sel):
            s._calls.append(sel[0].k)
            if sel[0].k in s._ok: return _SoK(s.Edges, s._ok, s._calls)
            raise RuntimeError("BRep_API: command not done")
    def _runK(fils, ok_lines, pairs=None, frecs=None, sok=None):
        edges = [_EK(k, (float(k), 0.0, 0.0), (float(k), 5.0, 0.0)) for k in range(60)]; calls = []; said = []; tdK = tempfile.mkdtemp(prefix="skin5_ck_")
        g_ = {"np": np, "json": json, "os": os, "FILLETS": fils, "FIL_MERGE": {}, "EDGES": edges, "so": _SoK(edges, set(ok_lines), calls), "res": {"fillets": []},
              "nfil": 0, "fil_failed": [], "CREASE_BUILT": {}, "_sok_k": list(sok or []), "FILLET_LINES": set(), "FIT": "span", "CREASE_MIN_DEG": 8.0, "SK": tdK,
              "CH": [{"pair": list((pairs or {}).get(k, [1, 2]))} for k in range(60)], "frec": list(frecs or []), "_rung": lambda r: r.get("rung"),
              "K": _tyK.SimpleNamespace(wall_dist=lambda P: np.full(len(P), 99.0), md5=lambda p: "x"), "Part": _tyK.SimpleNamespace(Vertex=lambda m: m),
              "busy": lambda *a, **k: _clK.nullcontext(), "say": lambda *a: said.append(" ".join(str(x) for x in a)),
              "_check_members": lambda *a, **k: [], "_fillet_lines": lambda *a, **k: {"width_ok": True}}
        for d_ in _defsK: exec(d_, g_)
        envK = {x_: os.environ.pop(x_, None) for x_ in ("FILLET_DROPPED", "FILLET_RERUN")}
        try: exec(_blkK, g_)
        finally:
            for x_, v_ in envK.items():
                if v_ is not None: os.environ[x_] = v_
            shutil.rmtree(tdK, ignore_errors=True)
        return g_, said, calls
    gX, sX, cX = _runK([{"line": 20, "r": 1.5, "why": "a round"}, {"line": 21, "r": 1.5, "why": "the agent's sharp line", "sharp_ok": True}], {20, 21}, sok=[21])
    check(cX == [20] and any(r_.get("line") == 21 and r_.get("how") == "sharp_ok" and not r_.get("ok") for r_ in gX["res"]["fillets"]) and gX.get("FIL_RERUN") == [],
          "31bx X76: the kernel never tries a sharp_ok line - its record says sharp_ok; no lines pass is owed for it alone")
    gY, sY, cY = _runK([{"line": 20, "r": 1.5, "why": "a round"}, {"line": 21, "r": 1.5, "why": "the agent's sharp line", "sharp_ok": True}], set(), sok=[21])
    check(cY == [20] and gY.get("FIL_RERUN") == [20, 21], "31bx X76: a lines pass owed for a failed line carries the sharp_ok line too (the child records it NOT MADE by the agent's word and frees its chain-mates' ends)")
    _chK = [{"line": 10, "r": 1.5, "chain": 0, "pos": 0, "why": "a foot"}, {"line": 11, "r": 1.5, "chain": 0, "pos": 1, "why": "a foot"}, {"line": 12, "r": 1.5, "chain": 0, "pos": 2, "why": "a foot"}]
    gA, sA, cA = _runK(_chK, {11})
    _skA = [l_ for l_ in sA if "FILLET by the kernel SKIPPED on line 11 " in l_ and "a member of fillet chain 0 - the chain is one blend with corners, made by the lines pass" in l_]
    _recA = [r_ for r_ in gA["res"]["fillets"] if r_.get("line") == 11]
    check(bool(_skA) and sorted(gA.get("FIL_RERUN") or []) == [10, 11, 12] and gA["nfil"] == 0 and cA == [] and bool(_recA) and _recA[0].get("ok") is False and "a member of fillet chain 0" in str(_recA[0].get("why")),
          "31bq R7W chain-kernel: a chain of three lines with the kernel able to round the middle one - line 11 SKIPPED by name ('a member of fillet chain 0'), never handed to makeFillet, recorded, and in the lines pass's list with its neighbours (FIL_RERUN %s; kernel calls %s; rounded %d)" % (gA.get("FIL_RERUN"), cA, gA["nfil"]))
    gB, sB, cB = _runK([{"line": 20, "r": 1.5, "why": "a single round"}], {20})
    check(gB["nfil"] == 1 and any("FILLET: line 20 rounded at R 1.5" in l_ for l_ in sB) and gB.get("FIL_RERUN") == [] and cB == [20],
          "31bq R7W chain-kernel: a single-line entry the kernel can round is made by the kernel as before (rounded %d, FIL_RERUN %s)" % (gB["nfil"], gB.get("FIL_RERUN")))
    gC, sC, cC = _runK([{"line": 30, "r": 1.5, "chain": 3, "pos": 0, "why": "one line"}, {"line": 40, "r": 1.5, "chain": 4, "pos": 0, "leg": "all", "why": "two legs"}, {"line": 41, "r": 1.5, "chain": 4, "pos": 1, "why": "its partner"}], {30, 40, 41})
    check(gC["nfil"] == 1 and cC == [30] and sorted(gC.get("FIL_RERUN") or []) == [40, 41],
          "31bq R7W chain-kernel: a one-line chain entry is a single line (tried, rounded); a member with legs counts as its line - both members of a two-line chain skipped (kernel calls %s, FIL_RERUN %s)" % (cC, gC.get("FIL_RERUN")))
    gD, sD, cD = _runK([{"line": 50, "r": 1.5, "why": "between two fills"}], {50}, pairs={50: [5, 6]}, frecs=[{"patch": 5, "rung": "nurbs"}, {"patch": 6, "rung": "nurbs"}])
    check(gD["nfil"] == 0 and cD == [] and any("SKIPPED on line 50 " in l_ and "both faces are fills" in l_ for l_ in sD) and gD.get("FIL_RERUN") == [50],
          "31bq R7W chain-kernel: B55 stands beside it - a single line between two fills is still skipped for that reason (FIL_RERUN %s)" % gD.get("FIL_RERUN"))
except Exception as _ex: check(False, "the 31bq R7W chain-kernel pin raised %r" % (_ex,))
# 0 cracks
try:
    import ast as _astW
    _scW = open(os.path.join(HERE, "rebuild", "sk_clean.py"), encoding="utf-8").read(); _gW = {"np": np}
    for _n in _astW.parse(_scW).body:
        if isinstance(_n, _astW.FunctionDef) and _n.name in ("growth_law", "graze_decide"): exec(_astW.get_source_segment(_scW, _n), _gW)
    _gd = _gW["graze_decide"]; _gl = _gW["growth_law"]; _tolW = 0.02
    _L = np.arange(0.0, 0.5 + 1e-9, 0.005)
    _corner = _gd(_L, _L * np.sin(np.radians(30.0)), 5.0, _tolW)
    _corner90 = _gd(_L, _L * 1.0, 5.0, _tolW)
    check(_corner is None and _corner90 is None, "31bq R7W wire-clean: a CORNER (30 deg, 90 deg - the distance growing linearly from the vertex) is NO graze (%s / %s)" % (_corner, _corner90))
    _dv9 = np.where(_L <= 0.03, 0.0004, 0.0004 + 0.025 * ((_L - 0.03) / 0.09) ** 2)
    _gv9 = _gd(_L, _dv9, 5.0, _tolW)
    check(_gv9 is not None and 0.09 <= _gv9[1] <= 0.13 and _gv9[2] <= _tolW, "31bq R7W wire-clean: the v9 GRAZE's profile (0.0004 mm for 0.03 mm, then quadratic) IS a graze - the run %s mm, the deviation %s <= tol" % (None if _gv9 is None else round(_gv9[1], 3), None if _gv9 is None else round(_gv9[2], 4)))
    _dhp = np.where(_L <= 0.33, 0.0015, 0.0015 + 0.5 * (_L - 0.33))
    _ghp = _gd(_L, _dhp, 5.0, _tolW)
    check(_ghp is not None and 0.30 <= _ghp[1] <= 0.40, "31bq R7W wire-clean: a HAIRPIN inside the coincidence band for 0.33 mm is a graze of run %s" % (None if _ghp is None else round(_ghp[1], 3)))
    _off = _gd(_L, np.full(len(_L), 0.05), 5.0, _tolW)
    _short = _gd(_L[:3], np.array([0.0, 0.001, 0.001]), 5.0, _tolW)
    _long = _gd(_L, np.full(len(_L), 0.001), 0.5, _tolW)
    check(_off is None and _short is None and _long is None, "31bq R7W wire-clean: a 0.05-off stretch, a run under the tolerance and a run over 90 %% of the edge are NO graze (%s / %s / %s)" % (_off, _short, _long))
    _okq, _med, _mx, _q1 = _gl(np.array([0.0004, 0.0004, 0.0005, 0.001, 0.004, 0.010, 0.018]), _tolW / 10.0); _okc, _medc, _mxc, _q1c = _gl(np.array([0.003, 0.006, 0.009, 0.012, 0.015, 0.018]), _tolW / 10.0)
    check(_okq and not _okc and _med <= 0.35 * _mx and _medc > 0.35 * _mxc, "31bq R7W wire-clean: the growth law - a quadratic profile's median %.4f <= 0.35 x max %.3f and its first quarter %.4f inside the band; a linear profile's median %.4f is half its max %.3f (no graze)" % (_med, _mx, _q1, _medc, _mxc))
    _sbW = open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read()
    check(("WIRE-CLEAN (31bq R7W): %d loop(s) of %d cleaned at the construction tolerance" in _sbW or "WIRE-CLEAN (31bq R7W): %d loop(s) of %d read cleaned at the construction tolerance" in _sbW) and ("frozen=_wc_frozen" in _sbW or "frozen=_frz_" in _sbW) and "_CL.same_edge(e_, _oe)" in _sbW and "is NOBODY'S - face" in _sbW and _sbW.index("# ---- 31bq R7W WIRE-CLEAN") < _sbW.index("def _loop_area_and_corner(eds_):"),
          "31bq R7W wire-clean: sk_build holds the pass before the face loop - the summary line, the frozen body edges, the match by geometry (the object or a copy), the sliver between two faces nobody's")
    check("def clean_loop(edges, tol=TOL, say=None, frozen=None):" in _scW and "def same_edge(a, b, tol=1e-3):" in _scW and "def growth_law(dd, band):" in _scW and "TOL = 0.02" in _scW,
          "31bq R7W wire-clean: sk_clean's API - clean_loop(frozen=), same_edge (the sharing report's test), growth_law, TOL 0.02 (the construction tolerance, never the 0.30 print tolerance)")
    # .OrderedEdges
    for _n in _astW.parse(_scW).body:
        if isinstance(_n, _astW.FunctionDef) and _n.name in ("P3", "ends", "order"): exec(_astW.get_source_segment(_scW, _n), _gW)
    class _FV:
        def __init__(s, x, y, z=0.0): s.x, s.y, s.z = float(x), float(y), float(z)
        @property
        def Point(s): return s
    class _FE:      # firstVertex(True)
        def __init__(s, a, b, k, rev=False): s.Vertexes = [_FV(*a), _FV(*b)]; s._k = k; s._rev = rev; s.Length = float(np.hypot(a[0] - b[0], a[1] - b[1])); s.Orientation = "Reversed" if rev else "Forward"
        def hashCode(s): return s._k
        def isSame(s, o): return getattr(o, "_k", None) == s._k
        def reversed(s): return _FE((s.Vertexes[0].x, s.Vertexes[0].y), (s.Vertexes[1].x, s.Vertexes[1].y), s._k, not s._rev)
        def firstVertex(s, orient=False): return s.Vertexes[1] if (orient and s._rev) else s.Vertexes[0]
        def lastVertex(s, orient=False): return s.Vertexes[0] if (orient and s._rev) else s.Vertexes[1]
    _epsO = 1e-5; _endsW = _gW["ends"]
    _fk = [_FE((0, 0), (10, 0), 11), _FE((0, 10), (10, 10 + _epsO), 12), _FE((10, _epsO), (10, 10), 13), _FE((0 - _epsO, 10), (0, 0), 14)]
    try: _oW = list(_gW["order"](_fk)); _exO = None
    except Exception as _e: _oW = []; _exO = _e
    _walkO = len(_oW) == 4 and all(float(np.linalg.norm(_endsW(_oW[i])[1] - _endsW(_oW[(i + 1) % 4])[0])) < 0.05 for i in range(4))
    _flipW = len(_oW) == 4 and any(e._rev for e in _oW)
    check(len(_oW) == 4 and sorted(e.hashCode() for e in _oW) == [11, 12, 13, 14] and _walkO and _flipW, "31bq R7W wire-clean (R7Wn3 / 3b): order() keeps the loop's OWN edge objects and every one of them - four out-of-order edges with their ends 1e-5 apart, one against the loop, come back as the same four (hashes %s), in walking order by the orientation-aware ends() %s, the one against the loop flipped %s%s; Part.Wire hands back copies of every edge but the first and __sortEdges__ drops a gapped edge - qq_R7Wn's handoff reached no face; a flipped edge's ends read by its Vertexes' order missed face 6F's graze (wcq1)" % (sorted(e.hashCode() for e in _oW), _walkO, _flipW, "" if _exO is None else "; order() raised %r" % (_exO,)))
    check("31bq R7Wn3b" in _scW and "firstVertex(True)" in _astW.get_source_segment(_scW, next(n for n in _astW.parse(_scW).body if isinstance(n, _astW.FunctionDef) and n.name == "ends")) and "GAP_MIN < g <= tol" in _scW and getattr(_gW.get("GAP_MIN"), "real", None) is not None if False else ("31bq R7Wn3b" in _scW and "firstVertex(True)" in _astW.get_source_segment(_scW, next(n for n in _astW.parse(_scW).body if isinstance(n, _astW.FunctionDef) and n.name == "ends")) and _scW.count("GAP_MIN < g <= tol") == 2 and "GAP_MIN = 1e-4" in _scW),
          "31bq R7W wire-clean (R7Wn3b): ends() reads the kernel's orientation-aware firstVertex / lastVertex, and a gap under GAP_MIN 1e-4 mm (the kernel's own vertex tolerance) is never joined - at both gap sites")
    _srcO = _astW.get_source_segment(_scW, next(n for n in _astW.parse(_scW).body if isinstance(n, _astW.FunctionDef) and n.name == "order"))
    _srcC = _astW.get_source_segment(_scW, next(n for n in _astW.parse(_scW).body if isinstance(n, _astW.FunctionDef) and n.name == "clean_loop"))
    check("31bq R7Wn3" in _scW and "Part.Wire(Part." not in _srcO and "Part.__sortEdges__(" not in _srcO and ".OrderedEdges" not in _srcO.split('"""')[-1] and "e.isSame(x)" in _srcC, "31bq R7W wire-clean (R7Wn3): sk_clean's order() CALLS no Part.Wire and no Part.__sortEdges__ (its docstring may name them), and clean_loop keys its record by the INPUT edge each ordered edge isSame")
    check("WIRE_CLEAN_TOL" in KR.LEVERS, "31bq R7W wire-clean (R7Wn (2)): WIRE_CLEAN_TOL is a registered lever - `--set WIRE_CLEAN_TOL=0` is taken by the runner and a stray shell value is stripped from the step's env (an unregistered lever is refused as one nothing reads, and would have ridden in from the shell)")
except Exception as _exW: check(False, "the 31bq R7W wire-clean pin raised %r" % (_exW,))
try:
    _sbR7 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    _svR7 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_vertex.py"), encoding="utf-8").read()
    check("their mean (each %.3f mm from its own)" not in _sbR7 and "_M4 = 0.5 * (_Pa4 + _Pb4)" not in _sbR7 and "swept ON %.2f mm past the junction so their offsets on face %d cross" in _sbR7
          and '_pass == "settle" and not vb_["meet"] and dab_ <= 0.3 and dqa_ <= 1e-3' in _sbR7 and 'mx_["chain_c"][str(ex_)]["extend"] = _ext7' in _sbR7,
          "31bq R7W (A5): a CONVEX corner with one contact and a floor under THIN_MM is MITRED - the two blends swept on past the junction to their own intersection in the settle pass (ZZ (4)'s one-arc merge, an edge off both blends, is gone)")
    check("FACE SANITY - every face of the solid read against" in _sbR7 and 'K._fail("FAIL: FACE SANITY - ' in _sbR7 and "def _mesh_props(f_, dev=0.02):" in _sbR7 and "def _mesh_vol(d__):" in _sbR7
          and "_vtol = 0.75 * _area_m * 0.01 + 5.0" in _sbR7 and "_gap_e = max(dv_, _pg_e)" in _sbR7,
          "31bq R7W (A5): FACE SANITY - every solid face's kernel area against its own mesh and its built record, the solid's kernel volume against its mesh's; a failure FAILS the build by name (qq6's face 37: -1.8e18 mm2 had passed)")
    check("def _built_of(k__):" in _sbR7 and "j_ = _built_of(k_)" in _sbR7 and "j__ = _built_of(k__)" in _sbR7 and "_SH_IDX = [_same_built(f_) for f_ in sh.Faces]" in _sbR7 and "_BHASH" not in _sbR7 and "matched to no built face BY POSITION" in _sbR7,
          "31bq R7W (A5): the faces are named by their BUILT record (by position through the shell, else their own mesh) - never by the kernel's centre + area of a face that may be corrupt; a shell face matched to no built face is said as measured (the verifier's change 4)")
    check("_fs_unm.append(k_)" in _sbR7 and '"unmeshed_not_taken": [int(x_) for x_ in _fs_unm]' in _sbR7 and 'if "FAIL: FACE SANITY" in _ln: return "closed the shell but FAILED FACE SANITY' in _sbR7 and "_fs_mis.append((k_, a_k, m_k))" in _sbR7 and '"mismatch_noted":' in _sbR7 and "why_.append(\"its kernel area %.3f mm2 against its own mesh's %.3f\"" not in _sbR7,
          "31bq R7W (A5, the verifier's changes 1 / 3 and the kit maintainer's decision R7Wo): an unmeshable face is NOT TAKEN, never a FAIL (the agent's accepted b27b and c1 hold such faces); the retry classifier reads a FACE SANITY failure of the lines child; a finite kernel area off the face's own mesh is NOTED and recorded, never a FAIL (a valid 31bp piece's face read 14.9 against 15.9)")
    check("MITRE_CHOICE" not in _sbR7 and "def _test_face" not in _sbR7 and "MITRE_INFO" not in _svR7, "31bq R7W (vertex-corner): MITRE CHOICE is OUT whole - the verifier showed it no kernel decision (every candidate ties, the label 'by the kernel' wrong) and it made the 56 legs worse (the planar mitre 0.312 against 0.216)")
except Exception as _ex: check(False, "the 31bq R7W vertex-corner pin raised %s" % _ex)
# skin-build
# corner edge
try:
    _swM7 = open(os.path.join(HERE, "rebuild", "sk_wires.py"), encoding="utf-8").read()
    def _grabM7(name):
        i_ = _swM7.index("\ndef %s(" % name) + 1; ls_ = _swM7[i_:].split("\n"); o_ = [ls_[0]]
        for l_ in ls_[1:]:
            if l_.strip() and not l_.startswith((" ", "\t")): break
            o_.append(l_)
        return "\n".join(o_) + "\n"
    _gM7 = {"np": np}
    for _fM7 in ("_room_meet", "_room_border_at", "_room_end_kinds", "_room_taper_ends", "_room_width"): exec(_grabM7(_fM7), _gM7)
    def _lnM7(a, b, step): n_ = max(3, int(np.linalg.norm(np.asarray(b, float) - np.asarray(a, float)) / step) + 1); return np.asarray(a, float)[None] + np.linspace(0, 1, n_)[:, None] * (np.asarray(b, float) - np.asarray(a, float))[None]
    _S7 = _lnM7([0, 0, 0], [10, 0, 0], 0.3); _t7 = np.full(len(_S7), 1.32); _D7 = np.tile([0, 1.0, 0], (len(_S7), 1))
    _b30 = _lnM7([0, 0, 0], 8.0 * np.array([np.cos(np.radians(30)), np.sin(np.radians(30)), 0]), 0.1); _far7 = _lnM7([-6, 6, 0], [16, 6, 0], 0.1)
    _w7 = K.taper_weights(_S7, max(1.5 * 1.32, 1.0), ends=(0, 1))
    _mu = _gM7["_room_meet"](_S7 + _t7[:, None] * _D7, _b30, _S7[0], 0.15, 0.3); _mt = _gM7["_room_meet"](_S7 + (_t7 * _w7)[:, None] * _D7, _b30, _S7[0], 0.15, 0.3)
    check(_mu[0] and abs(_mu[2] - 2.64) < 0.1 and not _mt[0] and _mt[2] < 0.3,
          "31bq R7W (M7): the MEET on the UNTAPERED offset - a border leaving the junction at 30 deg is met %.2f mm from it (%.3f mm), as skin-build's meet pass finds it; the TAPERED offset runs into the junction and cannot meet it (%.2f mm from it - the PP skip's dead test)" % (_mu[2], _mu[1], _mt[2]))
    _te = _gM7["_room_taper_ends"]
    check(_te([True, False], [False, False], [[False, False], [False, False]], True) == (1,) and _te([False, False], [True, False], [[True, True], [True, True]], True) == (0,)
          and _te([False, False], [False, False], [[True, False], [True, False]], True) == (1,) and _te([False, False], [False, False], [[True, False], [False, False]], True) == (0, 1)
          and _te([False, False], [False, False], [[False, False], [False, False]], False) == () and _te([False, False], [True, False], [[False, False], [False, False]], False) == (0,),
          "31bq R7W (M7): the taper as skin-build's TAPER_ENDS - never a chain end, always a split end (FIL_TAPER=0 too), a free end unless BOTH faces meet (met on one only: it tapers), none with FIL_TAPER=0")
    _lg0 = _lnM7([0, 0, 0], [5.1, 0, 0], 0.3); _lg1 = _lnM7([5.1, 0, 0], [10.2, 0, 0], 0.3); _l97 = _lnM7([10.2, 0, 0], [14, 2, 0], 0.3)
    _pc7 = [(53, 0, _lg0[0], _lg0[-1]), (53, 1, _lg1[0], _lg1[-1]), (97, None, _l97[0], _l97[-1])]
    _sb7 = [("chain", 53, _lnM7([0, 0, 0], [10.2, 0, 0], 0.1)), ("chain", 52, _lnM7([10.2, 0, 0], [10.2, 0, 5], 0.1)), ("wall", (2, 3), _lnM7([-3, 0, 5], [12, 0, 5], 0.1))]
    _k0 = _gM7["_room_end_kinds"](_lg0, (_lg0[0], _lg1[-1]), _pc7, (53, 0), _sb7, [[5.15, 0.0, 0.0], [5.0, 0.0, 4.0]], 53)
    _k1 = _gM7["_room_end_kinds"](_lg0, (_lg0[0], _lg1[-1]), _pc7, (53, 0), _sb7, [], 53)
    _k2 = _gM7["_room_end_kinds"](_lg1, (_lg0[0], _lg1[-1]), _pc7, (53, 1), _sb7, [[5.15, 0.0, 0.0]], 53)
    _k3 = _gM7["_room_end_kinds"](_lg1, (_lg0[0], _lg1[-1]), None, (53, 1), _sb7, [[5.15, 0.0, 0.0]], 53)
    check(_k0 == ([False, True], [False, False], [None, ("split", None)]) and _k1 == ([False, False], [False, True], [None, None])
          and _k2 == ([True, True], [False, False], [("split", None), ("chain", 52)]) and _k3 == ([False, False], [True, False], [None, None]),
          "31bq R7W (M7): the end kinds as skin-build's - a split end inside a chain is a CHAIN END (this line's other leg the partner, the split on the side face the corner; no such split: a split end that tapers); a junction shared with the next member is a chain end, its corner edge the side face's border leaving it; no chain context: a split end (%s / %s / %s / %s)" % (_k0, _k1, _k2, _k3))
    _im7 = np.nonzero((np.linalg.norm(_S7 - _S7[0], axis=1) > _t7) & (np.linalg.norm(_S7 - _S7[-1], axis=1) > _t7))[0]
    _cut7, _ = _gM7["_room_width"](_S7, _im7, _D7, _t7, np.full(len(_S7), 0.3), [("chain", 5, _far7)], 0.3)
    _ctl7, _ = _gM7["_room_width"](_S7, _im7, _D7, _t7 * _w7, 0.3 * _w7, [("chain", 1, _b30), ("chain", 5, _far7)], 0.3)
    check(_cut7 is None and _ctl7 is not None and _ctl7[2] == 1,
          "31bq R7W (M7): a junction met on both faces - its border CUT, the strip untapered there - fits, as skin-build builds it; the tapered strip measured against that border (the PP form) reads 'lower R' %.3f mm from border %s" % ((_ctl7 or [0])[0], (_ctl7 or [0, 0, "?"])[2]))
    check("_tap = _room_taper_ends(_ce, _se, [_met[f_] for f_ in pq_], FIL_TAPER_W)" in _swM7 and "best_, clear_ = _room_width(S_, im_, Dall_, ts_, THIN_ROOM * _wtap, others_, 0.3)" in _swM7
          and "_room_meet(S_ + ts0_[:, None] * _Dof[f_], _b[2], J_, 0.15, THIN_ROOM)" in _swM7 and "dm_, jm_ = _kp.query(Oall_)" not in _swM7 and "            _CHXI = {}" in _swM7
          and "\"ends\": _er}" in _swM7 and "    MEET_TOL = 0.15" in open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read(),
          "31bq R7W (M7): the room block decides each end with these functions (the meet on the untapered offset at sk_build's MEET_TOL 0.15, the taper, the width; the PP skip on the tapered offset gone) and records each face's end decision in fillets.json (room ends)")
except Exception as _exM7: check(False, "the 31bq R7W M7 pins raised %r" % (_exM7,))
try:
    import textwrap as _twF, types as _tyF, math as _mF
    from scipy.spatial import cKDTree as _ckdF
    _sbF = open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read(); _slF = open(os.path.join(HERE, "rebuild", "sk_lib.py"), encoding="utf-8").read()
    _iF = _slF.index("def _closest_pt_tri("); _LF = _slF[_iF:].splitlines(); _bodyF = [_LF[0]]
    for _lF in _LF[1:]:
        if _lF.strip() and not _lF.startswith((" ", "\t")): break
        _bodyF.append(_lF)
    _gF = {"np": np}; exec("\n".join(_bodyF), _gF)
    _BF = _twF.dedent(_sbF[_sbF.index("            _fs = so.Faces; _eh = "):_sbF.index('            with busy("self-intersection search')])
    class _P3F:
        def __init__(s, p): s.x, s.y, s.z = float(p[0]), float(p[1]), float(p[2])
    class _EF:
        def hashCode(s): return id(s)
    class _FF:
        def __init__(s, V, T): s.V = np.asarray(V, float); s.T = np.asarray(T, int); s.Edges = [_EF()]
        def hashCode(s): return id(s)
        def copy(s): return s
        def tessellate(s, tol): return [_P3F(v) for v in s.V], [tuple(int(i) for i in t) for t in s.T]
        @property
        def BoundBox(s): lo_, hi_ = s.V.min(0), s.V.max(0); return _tyF.SimpleNamespace(XMin=lo_[0], YMin=lo_[1], ZMin=lo_[2], XMax=hi_[0], YMax=hi_[1], ZMax=hi_[2])
    class _SecF:
        def __init__(s, f, df, a, b): s.f, s.df, s.FirstParameter, s.LastParameter, s.Length = f, df, a, b, float(b - a)
        def valueAt(s, t): return _P3F(s.f(t))
        def tangentAt(s, t): return _P3F(s.df(t))
    def _nsF(faces):
        g_ = {"np": np, "cKDTree": _ckdF, "K": _tyF.SimpleNamespace(_closest_pt_tri=_gF["_closest_pt_tri"]), "Part": _tyF.SimpleNamespace(Vertex=lambda *a: a), "so": _tyF.SimpleNamespace(Faces=faces), "res": {}, "say": lambda *a: None}
        exec(_BF, g_); return g_
    def _quadF(fun, u0, u1, v0, v1, nv=1):
        vs_ = np.linspace(v0, v1, nv + 1); V_ = []; T_ = []
        for v_ in vs_: V_ += [fun(u0, v_), fun(u1, v_)]
        for k_ in range(nv): a_ = 2 * k_; T_ += [(a_, a_ + 1, a_ + 3), (a_, a_ + 3, a_ + 2)]
        return _FF(V_, T_)
    def _shareF(a, b): e_ = _EF(); a.Edges.append(e_); b.Edges.append(e_)
    _secF = [_SecF(lambda t: (t, 0.0, 0.0), lambda t: (1.0, 0.0, 0.0), -9.0, 9.0)]
    _cF, _sF = _mF.cos(_mF.radians(3.0)), _mF.sin(_mF.radians(3.0))
    def _stripsF(extra=None):
        st_ = [_quadF(lambda u, v: (u, v, 0.0), -10, 10, -6.5 + k_, -5.5 + k_) for k_ in range(13)]
        for k_ in range(12): _shareF(st_[k_], st_[k_ + 1])
        W_ = _quadF(lambda u, v: (u, v * _cF, -v * _sF), -9, 9, -7.5, 7.5, nv=6)
        fs_ = st_ + [W_] + ([extra] if extra is not None else [])
        if extra is not None: _shareF(st_[12], extra)
        return fs_
    _fa = _stripsF(); _ga = _nsF(_fa); _da = _ga["_si_depth"](_fa[6], _fa[13], _secF, 6, 13)
    check(_da[0] is not None and abs(_da[0] - 6.5 / _cF * _sF) < 0.02, "31bq R7W fix-depth-F3F4 (F.4): a floor of 1 mm strips crossed at 3 deg reads its deep arm under the strips beyond R's neighbours: %s (truth %.3f; R and its neighbours alone read 0.079 and PASSED it)" % (None if _da[0] is None else round(_da[0], 3), 6.5 / _cF * _sF))
    _aF, _chF, _tF = 0.10, 0.15, 1.0
    _Fl = _quadF(lambda u, v: (u, v, 0.0), -10, 10, -8, 8); _Wl = _quadF(lambda u, v: (u, 0.0, v), -9, 9, -_aF, 6.0)
    _Cl = _quadF(lambda u, s: (u, s * _chF, -_aF - s * _chF), -9, 9, 1.0, 0.0); _Bt = _quadF(lambda u, v: (u, v, -_aF - _chF), -9, 9, _tF - _chF, _chF)
    _Cr = _quadF(lambda u, s: (u, _tF - s * _chF, -_aF - s * _chF), -9, 9, 0.0, 1.0); _Wr = _quadF(lambda u, v: (u, _tF, v), -9, 9, 6.0, -_aF); _Tp = _quadF(lambda u, v: (u, v, 6.0), -9, 9, 0.0, _tF)
    for _x, _y in ((_Wl, _Cl), (_Cl, _Bt), (_Bt, _Cr), (_Cr, _Wr), (_Wl, _Tp), (_Wr, _Tp)): _shareF(_x, _y)
    _fb = [_Fl, _Wl, _Cl, _Bt, _Cr, _Wr, _Tp]; _gb = _nsF(_fb)
    _ob = all(float(np.mean(_gb["_fmesh"](_f)["N"] @ _n)) > 0.99 for _f, _n in ((_Wl, (0, -1, 0)), (_Cl, (0, -0.7071, -0.7071)), (_Bt, (0, 0, -1)), (_Cr, (0, 0.7071, -0.7071)), (_Wr, (0, 1, 0)), (_Tp, (0, 0, 1))))
    _db = _gb["_si_depth"](_Fl, _Wl, _secF, 0, 1)
    check(_ob and _db[0] is not None and abs(_db[0] - (_aF + _chF)) < 0.02, "31bq R7W fix-depth-F3F4 (F.4): a VALID fin (every face outward: %s) 0.25 mm through a floor reads the floor's arm inside it, %s (one ring - the wall and its neighbours - read 0.352 and FAILED it)" % (_ob, None if _db[0] is None else round(_db[0], 3)))
    _ru = _ga["_rmesh"](6, 13); _rng = np.random.RandomState(7); _bad = 0
    for _p in np.c_[_rng.uniform(-9, 9, 300), _rng.uniform(-8, 8, 300), _rng.uniform(-1.5, 1.0, 300)]:
        _all = [_ga["_foot1"](_M, _p) for _M in _ru["mem"]]; _dm = min(r_[1] for r_ in _all)
        _k = sorted(range(len(_all)), key=lambda k_: (_all[k_][1] > _dm + 1e-7, not _all[k_][3], _all[k_][1], k_))[0]
        _q, _d, _t, _tf = _all[_k]; _tf = _tf or _ga["_on_seam"](_ru, _k, _q, _t); _r2 = _ga["_foot"](_ru, _p)
        if not (abs(_r2[1] - _d) < 1e-12 and int(_r2[2]) == int(_ru["toff"][_k] + _t) and bool(_r2[3]) == bool(_tf)): _bad += 1
    check(_bad == 0 and len(_ru["mem"]) == 13, "31bq R7W fix-depth-F3F4 (F.4): the union's queries prune by the members' boxes EXACTLY - %d of 300 feet differ from the foot over every member (members %d)" % (_bad, len(_ru["mem"])))
    # recorded
    _xf = _quadF(lambda u, v: (u, 6.5, v), -10, 10, -6.0, -4.0)
    def _noMeshF(tol): raise RuntimeError("crafted: no mesh")
    _xf.tessellate = _noMeshF
    _fd = _stripsF(extra=_xf); _gd = _nsF(_fd); _dd = _gd["_si_depth"](_fd[6], _fd[13], _secF, 6, 13)
    check(_dd[0] is not None and abs(_dd[0] - _da[0]) < 1e-9 and not _gd["_si_inc"], "31bq R7W fix-depth-F3F4 (F.4): a member with no mesh 4 mm from the walking face leaves the reference whole (read %s, as without it; recorded incomplete: %s)" % (None if _dd[0] is None else round(_dd[0], 3), _gd["_si_inc"]))
except Exception as _ex: check(False, "the 31bq R7W fix-depth-F3F4 pin raised %r" % (_ex,))
try:
    import textwrap as _twV, types as _tyV, math as _mV
    from scipy.spatial import cKDTree as _ckdV
    _sbV = open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read(); _slV = open(os.path.join(HERE, "rebuild", "sk_lib.py"), encoding="utf-8").read()
    _iV = _slV.index("def _closest_pt_tri("); _LV = _slV[_iV:].splitlines(); _bodyV = [_LV[0]]
    for _lV in _LV[1:]:
        if _lV.strip() and not _lV.startswith((" ", "\t")): break
        _bodyV.append(_lV)
    _gV = {"np": np}; exec("\n".join(_bodyV), _gV)
    _BV = _twV.dedent(_sbV[_sbV.index("            _fs = so.Faces; _eh = "):_sbV.index('            with busy("self-intersection search')])
    class _P3V:
        def __init__(s, p): s.x, s.y, s.z = float(p[0]), float(p[1]), float(p[2])
    class _EV:
        def hashCode(s): return id(s)
    class _FV:
        def __init__(s, V, T): s.V = np.asarray(V, float); s.T = np.asarray(T, int); s.Edges = [_EV()]
        def hashCode(s): return id(s)
        def copy(s): return s
        def tessellate(s, tol): return [_P3V(v) for v in s.V], [tuple(int(i) for i in t) for t in s.T]
    class _SecV:
        def __init__(s, f, df, a, b): s.f, s.df, s.FirstParameter, s.LastParameter, s.Length = f, df, a, b, float(b - a)
        def valueAt(s, t): return _P3V(s.f(t))
        def tangentAt(s, t): return _P3V(s.df(t))
    def _nsV(faces):
        g_ = {"np": np, "cKDTree": _ckdV, "K": _tyV.SimpleNamespace(_closest_pt_tri=_gV["_closest_pt_tri"]), "Part": _tyV.SimpleNamespace(Vertex=lambda *a: a), "so": _tyV.SimpleNamespace(Faces=faces), "res": {}, "say": lambda *a: None}
        exec(_BV, g_); return g_
    def _quadV(fun, u0, u1, v0, v1):
        return _FV([fun(u0, v0), fun(u1, v0), fun(u0, v1), fun(u1, v1)], [(0, 1, 3), (0, 3, 2)])
    def _shareV(a, b): e_ = _EV(); a.Edges.append(e_); b.Edges.append(e_)
    _s45, _c45 = _mV.sin(_mV.radians(45.0)), _mV.cos(_mV.radians(45.0)); _zt = 0.6 * _s45
    _RV = _quadV(lambda u, v: (u, v, 0.0), -10, 10, -0.2, 0.2); _WV = _quadV(lambda u, v: (u, v * _c45, v * _s45), -9, 9, -1.0, 0.6)
    _S1V = _quadV(lambda u, v: (u, v, 0.0), -10, 10, -6.0, -0.2); _S2V = _quadV(lambda u, v: (u, v, 0.0), -10, 10, 0.2, 5.0)
    _NwV = _quadV(lambda u, v: (u, v, _zt), -9, 9, _zt, 5.0); _XV = _quadV(lambda u, v: (u, 5.0, v), -9, 9, _zt, 0.0)
    for _aV, _bV in ((_S1V, _RV), (_RV, _S2V), (_WV, _NwV), (_S2V, _XV), (_XV, _NwV)): _shareV(_aV, _bV)
    _fV = [_RV, _WV, _S1V, _S2V, _NwV, _XV]; _gnV = _nsV(_fV)
    _okV = all(float(np.mean(_gnV["_fmesh"](_f)["N"] @ np.array(_n, float))) > 0.99 for _f, _n in ((_RV, (0, 0, 1)), (_WV, (0, -_c45, _s45)), (_S1V, (0, 0, 1)), (_S2V, (0, 0, 1)), (_NwV, (0, 0, 1)), (_XV, (0, 1, 0))))
    _dV = _gnV["_si_depth"](_RV, _WV, [_SecV(lambda t: (t, 0.0, 0.0), lambda t: (1.0, 0.0, 0.0), -9.0, 9.0)], 0, 1)
    check(_okV and _dV[0] is not None and _dV[0] > 0.30, "31bq R7W fix-depth-F3F4 (the verifier's change 1): a face 1.0 mm through a 0.4 mm floor strip at 45 deg, its top neighbour joined to the floor through the solid (every face outward: %s), reads %s - over the 0.30 gate (penetration 0.707; its own neighbour cutting its outside arm had read 0.248 and PASSED it; one ring 0.421)" % (_okV, None if _dV[0] is None else round(_dV[0], 3)))
except Exception as _exV: check(False, "the 31bq R7W fix-depth-F3F4 (verifier's change 1) pin raised %r" % (_exV,))
# skin-build
# ORIGINAL
# skin-build
try:
    import ast as _astN, textwrap as _twN
    _swN = open(os.path.join(HERE, "rebuild", "sk_wires.py"), encoding="utf-8").read()
    _ndN = next(n_ for n_ in _astN.walk(_astN.parse(_swN)) if isinstance(n_, _astN.FunctionDef) and n_.name == "_nrm_at")
    _srcN = _twN.dedent("\n".join(_swN.splitlines()[_ndN.lineno - 1:_ndN.end_lineno])) + "\n"
    class _VN:
        def __init__(s, x, y, z): s.x, s.y, s.z = float(x), float(y), float(z)
    class _KN:
        nl = None
        @staticmethod
        def local_face_normals(Vu, F, pid, f, S): n_ = np.asarray(_KN.nl, float); return n_.mean(0), n_.copy(), {"excluded": 0, "nearest_mm": 0.1}
    class _CylN:
        def parameter(s, p): return float(np.arctan2(p.y, p.x)), float(p.z)
        def value(s, u, v): return _VN(5.0 * np.cos(u), 5.0 * np.sin(u), v)
        def normal(s, u, v): return _VN(np.cos(u), np.sin(u), 0.0)
    class _FaceN: Surface = _CylN()
    def _nsN(kind, nl, demote=(), fil=1.5, jmove=0.5):
        _KN.nl = nl; sd_ = []
        g_ = {"np": np, "K": _KN, "Vu": None, "F": None, "_pid": None, "PJ": [{"kind": kind, "face": 7}, {"kind": kind, "face": 7}], "DEMOTE": set(demote), "BF": {7: _FaceN()},
              "V3": lambda x, y, z: _VN(x, y, z), "JMOVE_MAX": jmove, "FIL_SMOOTH_W": fil, "_SAID9": set(), "_SAIDN": set(), "say": lambda *a: sd_.append(" ".join(str(x) for x in a)), "_said": sd_}
        exec(_srcN, g_); return g_
    def _angN(a, b): return np.degrees(np.arccos(np.clip(np.sum(np.asarray(a, float) * np.asarray(b, float), axis=-1), -1.0, 1.0)))
    _SN = np.stack([np.linspace(0, 9.9, 34), np.zeros(34), np.zeros(34)], 1); _nlN = np.tile([0.0, 0.0, 1.0], (34, 1)); _jN = 17
    _nlN[_jN] = [0.0, -np.sin(np.radians(25)), np.cos(np.radians(25))]
    _o1 = _nsN("changed", _nlN)["_nrm_at"](0, _SN); _o0 = _nsN("changed", _nlN, fil=0.0)["_nrm_at"](0, _SN)
    _d1 = float(max(_angN(_o1[_jN], _o1[_jN - 1]), _angN(_o1[_jN], _o1[_jN + 1]))); _d0 = float(max(_angN(_o0[_jN], _o0[_jN - 1]), _angN(_o0[_jN], _o0[_jN + 1])))
    _z1 = float(_angN(_o1[_jN], [0.0, 0.0, 1.0]))
    check(_d1 < 3.0 and _z1 < 3.0 and _d0 > 20.0 and float(np.abs(np.linalg.norm(_o1, axis=1) - 1.0).max()) < 1e-9,
          "31bq R7W (fix-wires-normals): a CHANGED face's normals are SMOOTHED along the line over FIL_SMOOTH_MM 1.5 as skin-build's (sk_build 588-595) - a 25 deg jump at one sample reads %.1f deg off its neighbours and %.1f off the sheet (FIL_SMOOTH_MM 0: %.1f, the raw form)" % (_d1, _z1, _d0))
    # ORIGINAL
    _thN = np.radians(np.linspace(0.0, 90.0, 27)); _SC = np.stack([5.0 * np.cos(_thN), 5.0 * np.sin(_thN), np.zeros(27)], 1)
    _fcN = (np.floor(_thN / np.radians(45.0)).clip(0, 1) + 0.5) * np.radians(45.0); _fac = -np.stack([np.cos(_fcN), np.sin(_fcN), np.zeros(27)], 1)
    _ex = np.stack([np.cos(_thN), np.sin(_thN), np.zeros(27)], 1)
    _gO = _nsN("orig", _fac); _oO = _gO["_nrm_at"](0, _SC)
    _dO = float(_angN(_oO, -_ex).max()); _dF = float(_angN(_fac, -_ex).max())
    check(_dO < 1e-4 and _dF > 15.0 and not _gO["_said"],
          "31bq R7W (fix-wires-normals): an ORIGINAL face's normals are its own SURFACE's at each sample (sk_build 573-585), signed by the sheet - on a cylinder R 5 under coarse facets %.1f deg off the exact normal (facing inward) the line reads %.2g deg off the exact inward normal" % (_dF, _dO))
    # skin-build
    _oD = _nsN("orig", _fac, demote=(0,))["_nrm_at"](0, _SC); _oDc = _nsN("changed", _fac)["_nrm_at"](0, _SC)
    check(float(np.abs(_oD - _oDc).max()) < 1e-12 and float(_angN(_oD, -_ex).max()) > 5.0 and float(np.abs(_oD - _fac).max()) > 0.05,
          "31bq R7W (fix-wires-normals): a DEMOTED original face (wires_demote.json - skin-build's kind 'changed') takes the smoothed sheet as a changed face does, not its surface (%.1f deg off it)" % float(_angN(_oD, -_ex).max()))
    # skin-build
    _SF = _SC * 1.2; _gF = _nsN("orig", _fac); _oF = _gF["_nrm_at"](0, _SF); _gF["_nrm_at"](0, _SF)
    check(float(_angN(_oF, -_ex).max()) < 1e-4 and not _gF["_said"],
          "31bq R7W (verify-wires-normals): an original surface 1 mm from the line (over JMOVE_MAX 0.5) still gives its own normals, as skin-build reads it - no fallback, nothing said")
    class _BadN:
        def parameter(s, p): raise RuntimeError("no parameter")
    class _FaceB: Surface = _BadN()
    _gB = _nsN("orig", _fac); _gB["BF"] = {7: _FaceB()}; _oB = _gB["_nrm_at"](0, _SC); _gB["_nrm_at"](0, _SC); _oBc = _nsN("changed", _fac)["_nrm_at"](0, _SC)
    check(float(np.abs(_oB - _oBc).max()) < 1e-12 and float(np.abs(_oB - _fac).max()) > 0.05 and len([l_ for l_ in _gB["_said"] if "could not be taken" in l_ and "skin-build's own fallback" in l_]) == 1,
          "31bq R7W (verify-wires-normals): an original surface whose normals cannot be taken leaves the smoothed sheet - skin-build's own fallback (sk_build 586-587) - said once per face over two calls")
    import re as _reN
    _rdN = dict(_reN.findall(r'\("([A-Z_]+)", "([0-9.]+)"\)', _swN[_swN.index("ROOM_DEF = ("):_swN.index("ROOM_DEF = (") + 400]))
    _sbN = open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read(); _krN = open(os.path.join(HERE, "kit_rebuild.py"), encoding="utf-8").read()
    check(_rdN.get("FIL_SMOOTH_MM") == "1.5" and 'FIL_SMOOTH_MM = float(os.environ.get("FIL_SMOOTH_MM", "1.5") or 1.5)' in _sbN and '"FIL_SMOOTH_MM"' in _reN.search(r"ROOM_LEVERS = \(([^)]*)\)", _krN).group(1)
          and 'FIL_SMOOTH_W = float(os.environ.get("FIL_SMOOTH_MM", "1.5") or 1.5)' in _swN,
          "31bq R7W (fix-wires-normals): FIL_SMOOTH_MM is a room lever - in sk_wires' ROOM_DEF at sk_build's own default 1.5 and in kit_rebuild's ROOM_LEVERS (the runner carries it from the live piece's build; the build gate compares it), read by the room line as the build reads it")
    check("normals as the build's - smoothed along the line over FIL_SMOOTH_MM %g on changed faces; the original surface's own on original faces (31bq R7W fix-wires-normals)" in _swN
          and "if (_kf.query(inner_ + 0.5 * _tt * _D0)[0] > _kf.query(inner_ - 0.5 * _tt * _D0)[0]).mean() > 0.5: Dall_ = -Dall_      # the side the face lies on" in _swN,
          "31bq R7W (fix-wires-normals): the room line says once per run how it reads the normals; the side vote and the offset are read from the same normals as before (the side NOT changed)")
except Exception as _exN: check(False, "the 31bq R7W fix-wires-normals pins raised %r" % (_exN,))
try:
    _scN4 = open(os.path.join(HERE, "rebuild", "sk_clean.py"), encoding="utf-8").read(); _sbN4 = open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read(); _rbN4 = open(os.path.join(HERE, "rebuild", "rb_reinsert.py"), encoding="utf-8").read()
    check("if oh in repl:" in _scN4 and "def _sub(lst, add):" in _scN4 and ('kind="compose-append"' in _scN4 or "a move on an edge its earlier record does not hold" in _scN4), "31bq R7Wn4 (C1): _rep COMPOSES a chain of moves on one original edge - the earlier record's pieces kept, `old` replaced inside them (the hairpin's second graze had overwritten the first cut's handed piece); R7Wn4b: a compose that finds no edge is refused")
    check('kind="short-skipped"' in _scN4 and "prev = keep[-1] if keep else (E[-1] if i == 0 else None)" in _scN4 and "vmoves=[[q_.tolist(), m.tolist()] for q_ in (a, b)" in _scN4 and "vmoves=vm_" in _scN4,
          "31bq R7Wn4 (C6 / C2): a short edge is dropped only where its neighbours' ends are its own, a short first edge joins the loop's last edge, and every SHORT / GAP move names the vertices it moved")
    check('kind="doubled"' in _scN4 and "ONE CURVE in both faces" in _scN4, "31bq R7Wn4 (b / C8): a doubled edge is not grazed against itself; the docstring says one CURVE in both faces, never one object")
    check("_wf = list(_todo_faces)" in _sbN4 and "_todo_faces[:] = _wf" in _sbN4 and "def _wc_closed(L_, tol_):" in _sbN4 and "order_loops(list(_edsw), tol=_WC_TOL)" in _sbN4
          and "_wc_vx += 1" in _sbN4 and 'res["wire_clean"] = globals().get("WC_RECORD")' in _sbN4 and 'os.environ.get("WIRE_CLEAN_DRY", "0") == "1"' in _sbN4 and "loop(s) NOT cleaned" in _sbN4 and ('if _subw in ("FV", "F*"): continue' in _sbN4 or 'if _subw in ("FV", "F*"): _wc_notread += 1; continue' in _sbN4),
          "31bq R7Wn4 (C2 / C3 / C4 / C5 / C7 / G10): the block works on a copy and commits at the end, reads a loop closed within the construction tolerance, skips and freezes the ready faces, re-ends other faces' edges on a moved vertex, says every skipped loop, records the pass-made micro edges, and WIRE_CLEAN_DRY=1 is the census")
    check("wire_clean" in _rbN4 and "micro_edges" in _rbN4 and ("plan G4" in _rbN4 or "G4 (a)" in _rbN4), "31bq R7Wn4 (C4): the BOP gate names a TooSmallEdge on a face holding a pass-made micro edge as the pass's (R7Wn5: the client's (a) - a cosmetic)")
except Exception as _exN4: check(False, "the 31bq R7Wn4 pins raised %r" % (_exN4,))
try:
    _sc5 = open(os.path.join(HERE, "rebuild", "sk_clean.py"), encoding="utf-8").read(); _sb5 = open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read(); _rb5 = open(os.path.join(HERE, "rebuild", "rb_reinsert.py"), encoding="utf-8").read()
    check('raise RuntimeError("wire-clean: a move on an edge its earlier record does not hold' in _sc5 and "if keep[_kk].isSame(nxt): keep[_kk] = E[0]; break" in _sc5,
          "31bq R7Wn4b (D2): a compose that does not find its edge is REFUSED by name (never a silent append), and the short edge at the loop's seam replaces its stale next in `keep`")
    check("seen_v = set(); seen_pair = set()" in _sc5 and "if vk in seen_v: continue" in _sc5 and "(min(i, j), max(i, j)) in seen_pair" in _sc5, "31bq R7Wn4b (D3): the census counts a graze once per shared vertex and a near stretch once per pair")
    check("is put back at its junction (31bq R7Wn4b)" in _sb5 and "_wc_read += 1" in _sb5 and "a NECK under the construction tolerance the pass cannot decide" in _sb5 and "def _wc_take(t_, new_eds, old_eds):" in _sb5
          and '"sub": _s_, "face": _wc_name(t_)' in _sb5 and "loop(s) of %d read cleaned" in _sb5 and "or a ready face's border - 31bq R7Wn4b" in _sc5 and '"loops_read": _wc_read' in _sb5,
          "31bq R7Wn4b (D1 / D4 / D5 / D6 / D7): a short edge the loop walk left out is spliced back, a neck refuses the loop, the frozen message names both kinds, the summary counts the loops read, the micro record carries the face's sub and name")
    import tempfile as _tf5, math as _m5, re as _re5
    _i5 = _rb5.index("    _COSMETIC = {"); _j5 = _rb5.index("    if bad and not BOP_OK:\n        _fail(", _i5); _BLK5 = "\n".join(l[4:] for l in _rb5[_i5:_j5].splitlines()) + "\n"
    _td5 = _tf5.mkdtemp(prefix="r7wn5_gate_"); os.makedirs(os.path.join(_td5, "skin")); _pc5 = os.path.join(_td5, "skin", "piece_skin.brep"); open(_pc5, "w").write("PIECE N5"); _MD5 = hashlib.md5(open(_pc5, "rb").read()).hexdigest()
    def _gate5(rec, kinds):
        _sic = os.path.join(_td5, "skin", "solid_c.json")
        if rec is None:
            if os.path.isfile(_sic): os.remove(_sic)
        else: json.dump(rec, open(_sic, "w"))
        _said = []; _bad = [{"solid": 0, "kinds": dict((k, 1) for k in kinds), "max_edge_tol": 0.01, "max_vertex_tol": 0.01, "check_true": False}]
        _g = {"os": os, "json": json, "math": _m5, "re": _re5, "RUN": _td5, "P": lambda p_: os.path.join(_td5, p_), "say": lambda s_: _said.append(s_), "bad": _bad, "BOP_OK": ""}
        _old = os.environ.get("PIECE"); os.environ["PIECE"] = _pc5
        try: exec(_BLK5, _g)
        finally:
            if _old is None: os.environ.pop("PIECE", None)
            else: os.environ["PIECE"] = _old
        return ("PASS" if not _g["bad"] else "REFUSE"), _said, _g
    _cf5 = [{"face": 1, "patch": 1, "rung": "cap", "what": "a too-small edge (BOP): the body's own 0.10 mm section edge", "check": "Error in Edge: BOPAlgo TooSmallEdge"},
            {"face": 22, "patch": 9, "rung": "nurbs", "sub": None, "what": "a too-small edge (BOP): an edge 0.10 mm long with its tolerance raised to its gap", "check": "Error in Edge: BOPAlgo TooSmallEdge"},
            {"face": 52, "patch": 28, "rung": "orig", "sub": None, "what": "a too-small edge (BOP): an edge 0.06 mm long with its tolerance raised to its gap", "check": "Error in Edge: BOPAlgo TooSmallEdge"},
            {"face": 54, "patch": 29, "rung": "fillet", "sub": "F", "what": "a too-small edge (BOP): an edge 0.06 mm long with its tolerance raised to its gap", "check": "Error in Edge: BOPAlgo TooSmallEdge"}]
    _base5 = {"self_intersections": [], "si_searched": True, "si_unmeasured_pairs": 0, "piece_md5": _MD5, "edge_off_max": 0.01, "si_self_faces": [], "edge_gaps_unmeasured": 0}
    _micAll = [{"patch": 28, "sub": None, "face": "28", "len": 0.0612, "mid": [0, 0, 0]}, {"patch": 29, "sub": "F", "face": "29F", "len": 0.0612, "mid": [0, 0, 0]}]
    _r, _s, _g = _gate5(dict(_base5, check_faces=[_cf5[0], _cf5[2], _cf5[3]], wire_clean={"micro_edges": _micAll}), ["TooSmallEdge"])
    check(_r == "PASS" and _g["_tse_pass_f_"] == [52, 54] and any("COSMETIC like the caps' own edges (the client 2026-10-23" in x and "[52, 54]" in x for x in _s),
          "31bq R7Wn5 (the client 10-23, G4 (a)): TooSmallEdge on faces 52 (patch 28) / 54 (patch 29F) holding the pass's 0.0612 mm pieces + the cap's own: PASS without BOP_OK, the faces named as the pass's cut-back (got %s, %s)" % (_r, _g["_tse_pass_f_"]))
    _r, _s, _g = _gate5(dict(_base5, check_faces=[_cf5[0], _cf5[2], _cf5[3]]), ["TooSmallEdge"])
    check(_r == "REFUSE" and _g["_tse_noncap_"] == [52, 54], "31bq R7Wn5: the same faces with NO wire_clean record (an older build): REFUSE - non-cap TooSmallEdge faces %s, nothing cleared (got %s)" % (_g["_tse_noncap_"], _r))
    _r, _s, _g = _gate5(dict(_base5, check_faces=[_cf5[0], _cf5[2], _cf5[3]], wire_clean={"micro_edges": [{"patch": 28, "sub": None, "len": 0.0612, "mid": [0, 0, 0]}, {"patch": 29, "sub": None, "len": 0.0612, "mid": [0, 0, 0]}]}), ["TooSmallEdge"])
    check(_r == "REFUSE" and _g["_tse_pass_f_"] == [52] and _g["_tse_noncap_"] == [54], "31bq R7Wn5 (D7): the micro edges keyed by patch AND sub - a record naming (29, None) clears face 52 (28, None) and NOT face 54 (29, F) (got %s / %s)" % (_g["_tse_pass_f_"], _g["_tse_noncap_"]))
    _r, _s, _g = _gate5(dict(_base5, check_faces=[_cf5[1]], wire_clean={"micro_edges": [{"patch": 9, "sub": None, "len": 0.05, "mid": [0, 0, 0]}]}), ["TooSmallEdge"])
    check(_r == "REFUSE" and _g["_tse_pass_f_"] == [] and _g["_tse_noncap_"] == [22] and not any("COSMETIC like" in x for x in _s),
          "31bq R7Wn5 (D7's control): a 0.05 mm pass-made edge on patch 9 does NOT clear face 22's own 0.10 mm TooSmallEdge (the length in check_faces' text matched within 0.01) - REFUSE, not named as the pass's (got %s)" % (_r,))
    _r, _s, _g = _gate5(dict(_base5, piece_md5="0" * 32, check_faces=[_cf5[2]], wire_clean={"micro_edges": _micAll}), ["TooSmallEdge"])
    check(_r == "REFUSE" and _g["_tse_pass_f_"] == [], "31bq R7Wn5: another piece's record clears nothing (got %s, %s)" % (_r, _g["_tse_pass_f_"]))
    _r, _s, _g = _gate5(dict(_base5, check_faces=[_cf5[0], _cf5[2]], wire_clean={"micro_edges": _micAll}), ["TooSmallEdge", "InvalidCurveOnSurface"])
    check(_r == "PASS", "31bq R7Wn5: with the gap kinds under 0.02 beside it the piece still passes as cosmetics only (got %s)" % (_r,))
except Exception as _exN5: check(False, "the 31bq R7Wn4b / R7Wn5 pins raised %r" % (_exN5,))
try:
    import ast as _astB, types as _tyB
    _svB = open(os.path.join(HERE, "rebuild", "sk_vertex.py"), encoding="utf-8").read(); _sbB = open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read()
    _tvB = _astB.parse(_svB); _fnB = {n.name: n for n in _tvB.body if isinstance(n, _astB.FunctionDef)}
    class _VecB(object):
        def __init__(self, x, y, z): self.x, self.y, self.z = float(x), float(y), float(z)
    class _SurfB(object):
        def __init__(self): self.rows = None; self.poles = {}
        def interpolate(self, rows): self.rows = [[(p.x, p.y, p.z) for p in r] for r in rows]; self.NbUPoles = len(rows); self.NbVPoles = len(rows[0])
        def setPole(self, i, j, v): self.poles[(i, j)] = (v.x, v.y, v.z)
    _fcB = _tyB.SimpleNamespace(Vector=_VecB); _ptB = _tyB.SimpleNamespace(BSplineSurface=_SurfB)
    class _ArcB(object):
        def __init__(self, C, R, p, q): self.C, self.R, self.p, self.q = np.asarray(C, float), float(R), np.asarray(p, float), np.asarray(q, float)
        def discretize(self, Number=10):
            a = (self.p - self.C) / self.R; b = (self.q - self.C) / self.R; w = np.arccos(np.clip(a @ b, -1, 1))
            return [_VecB(*(self.C + self.R * (np.sin((1 - t) * w) * a + np.sin(t * w) * b) / np.sin(w))) for t in np.linspace(0, 1, int(Number))]
    _nsB = {"np": np, "FreeCAD": _fcB, "Part": _ptB, "math": __import__("math")}
    for _nB in ("V3", "P3", "unit", "_pts_from", "sphere_fan"):
        exec(compile(_astB.Module(body=[_fnB[_nB]], type_ignores=[]), "sk_vertex.py:" + _nB, "exec"), _nsB)
    _aB = _fnB["sphere_fan"].args; _sigB = [a.arg for a in _aB.args]; _dfB = [getattr(d, "value", None) for d in _aB.defaults]
    _CB = np.array([1.0, -2.0, 3.0]); _RB = 1.5; _XB = _CB + _RB * np.array([0.0, 0.0, -1.0]); _PaB = _CB + _RB * np.array([1.0, 0.0, 0.0]); _PbB = _CB + _RB * np.array([0.0, 1.0, 0.0])
    _bsB = _nsB["sphere_fan"](_ArcB(_CB, _RB, _XB, _PaB), _ArcB(_CB, _RB, _XB, _PbB), _ArcB(_CB, _RB, _PaB, _PbB), _XB, _CB, _RB)
    _rwB = np.asarray(_bsB.rows, float); _inB = _rwB[1:-1, 1:-1]; _dvB = np.abs(np.linalg.norm(_inB - _CB, axis=2) - _RB)
    _fcolB = _rwB[:, -1]; _farB = np.array([[q.x, q.y, q.z] for q in _ArcB(_CB, _RB, _PaB, _PbB).discretize(9)])
    check(_sigB == ["arc_a", "arc_b", "far_arc", "X", "C", "R", "n_rows", "n_pts"] and _dfB == [9, 17] and _rwB.shape == (9, 17, 3) and float(_dvB.max()) < 1e-9
          and np.allclose(_rwB[0, 1:], np.array([[q.x, q.y, q.z] for q in _ArcB(_CB, _RB, _XB, _PaB).discretize(17)])[1:]) and np.allclose(_rwB[-1, 1:], np.array([[q.x, q.y, q.z] for q in _ArcB(_CB, _RB, _XB, _PbB).discretize(17)])[1:])
          and np.allclose(_fcolB, _farB) and all(np.allclose(_bsB.poles.get((i, 1), (9e9, 0, 0)), _XB) for i in range(1, 10)) and float(np.abs(np.linalg.norm(_rwB[:, 0] - _rwB[:, 1], axis=1) - 0.003).max()) < 1e-9,
          "31bq R7W merge-B26 (B26 R7v): sk_vertex.sphere_fan(arc_a, arc_b, far_arc, X, C, R, n_rows=9, n_pts=17) - the vertex ball's spherical triangle: 9 x 17 rows to the surface's interpolate, every interior point ON the ball (worst %.1e mm off R %g), the first / last row arc a / arc b, the far column the far arc, the X column a 0.003 mm hair whose poles are set on X (sig %s, defaults %s)" % (float(_dvB.max()), _RB, _sigB, _dfB))
    check("_VERTEX_C = {}; _VERTEX_J = {}; _VX_SIDE = {}" in _sbB and "if _cid is None and k in _VERTEX_C and not f_.get(\"_vertex_pass\"): continue" in _sbB and "31bq R7v (B26): THE VERTEX PASS" in _sbB
          and "surf_s = VX.sphere_fan(arc_a, arc_b, arc_c, X_A, C_v, R_v)" in _sbB and "THE TRIANGLE'S EDGES ARE THE FAN'S OWN BOUNDARY ISOS" in _sbB and "_vs = _VX_SIDE.get((fl_[\"key\"], int(f)))" in _sbB
          and "_ext6_ = mx_[\"chain_c\"][str(ex_)].pop(\"extend\", None)" in _sbB and "THE CONTACT ON THE COMMON FACE IS THE TWO OFFSETS' OWN CROSSING" in _sbB and "THE TWIN JUNCTION TAKES ITS MASTER'S BALL" in _sbB,
          "31bq R7W merge-B26 (B26 R7v..R7v6b): sk_build holds a corner edge's fillet of the chain's R for the VERTEX PASS (the ball's station), sweeps the members cut back to it with no extension past the junction (R7v6a), the contact on the common face the offsets' own crossing (R7v5), the twin junction the master's ball reflected (R7v3), the sphere triangle through sphere_fan with the fan's own boundary isos as its edges (R7v6b), the side faces' strips L-shaped")
    _tbB = _astB.parse(_sbB); _vxB = next((n for n in _tbB.body if isinstance(n, _astB.FunctionDef) and n.name == "_vx_id"), None)
    _nsV = {"np": np}; exec(compile(_astB.Module(body=[_vxB], type_ignores=[]), "sk_build.py:_vx_id", "exec"), _nsV) if _vxB is not None else None
    _JB = np.array([-5.8, -123.3, 86.7]); _kB = _nsV["_vx_id"]({"name": "32", "key": 32}, {"name": "53 leg 0", "key": 141}, _JB) if _vxB is not None else None
    _k2B = _nsV["_vx_id"]({"name": "53 leg 0", "key": 7}, {"name": "32", "key": 3}, _JB + 1e-4) if _vxB is not None else None
    _k3B = _nsV["_vx_id"]({"name": "53 leg 1"}, {"name": "97"}, -_JB * np.array([1, -1, -1])) if _vxB is not None else None
    _lnB = _sbB.split("\n"); _useB = [i for i, l in enumerate(_lnB) if "_vx_id(" in l and not l.lstrip().startswith("def _vx_id")]
    _idxB = [i for i, l in enumerate(_lnB) if "_VERTEX_J" in l and "min(ia_" in l]
    check(_vxB is not None and _kB == _k2B and _kB != _k3B and _kB == (("32", "53 leg 0"), (-5.8, -123.3, 86.7))
          and "_VERTEX_J[_vx_id(fa, fb, Ja)] = int(kk_v)" in _sbB and "if _vx_id(fa, fb, Ja) in _VERTEX_J: continue" in _sbB and "_vxk = _vx_id(fa, fb, Ja)" in _sbB and not _idxB
          and _useB and _vxB.lineno - 1 < min(_useB),
          "31bq R7W merge-B26 (B26's latent seam): a vertex junction is keyed by its IDENTITY - _vx_id(two members' names in either order, the junction rounded) %s - at the vertex pass's write, the contacts-pass skip and the build pass's lookup, and by no fls index (%d line(s) still do): the B04 (3) re-settle REBUILDS fls when it drops a member, and the index key went stale - the ball's junction fell to the corner as before with its members already cut back" % (_kB, len(_idxB)))
    # recorded
    _dlB = [l for l in _lnB if "it was held for the ball: it is NOT made by lines" in l]; _swB = [l for l in _lnB if "corner edge" in l and "fillet is made as a single blend" in l]
    _rbB = next((n for n in _tbB.body if isinstance(n, _astB.For) and "_VERTEX_C" in _astB.get_source_segment(_sbB, n.iter)), None)
    _saidB = []; _nsR = {"np": np, "FILLET_LINES": {52, 95, 77, 12, 33}, "FIL_MERGE": {12: {}}, "FIL_NOT_MADE": {}, "say": lambda m_: _saidB.append(m_),
                        "_VERTEX_C": {52: {"cid": 0, "J": np.array([-5.8, -123.3, 86.7]), "done": True}, 95: {"cid": 0, "J": np.array([5.8, -123.3, 86.7]), "done": False, "single": True},
                                      77: {"cid": 1, "J": np.array([1.0, 2.0, 3.0]), "done": False}, 12: {"cid": 1, "J": np.array([0.0, 0.0, 0.0]), "done": False}, 40: {"cid": 2, "J": np.array([0.0, 1.0, 0.0]), "done": False, "single": True}}}
    if _rbB is not None: exec(compile(_astB.Module(body=[_rbB], type_ignores=[]), "sk_build.py:the declined-ball record", "exec"), _nsR)
    _fnmB = _nsR["FIL_NOT_MADE"]
    check(len(_dlB) == 4 and not _swB and _rbB is not None and sorted(_fnmB) == [77, 95] and "was declined" in _fnmB.get(95, "") and "no vertex pass reached" in _fnmB.get(77, "") and len(_saidB) == 2,
          "31bq R7W merge-B26 (B26, measure-B26's SEEN): a vertex ball DECLINED leaves its held corner-edge fillet NOT made - its four decline lines say so (%d; 'made as a single blend' left: %d) and the record block reads V_[\"single\"] (set and read nowhere before): the declined line and one no vertex pass reached go into FIL_NOT_MADE (the PASS line names them sharp) and are said once; a made ball, a line not in this pass, a line swept after all do not (%s)" % (len(_dlB), len(_swB), sorted(_fnmB)))
except Exception as _exB: check(False, "the 31bq R7W merge-B26 pins raised %r" % (_exB,))
try:
    _sbJ = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    check("NOREACH[int(e_)] = {" in _sbJ and "if _dotD < -0.2 or _gapJ < THIN_FIL:" in _sbJ and "CANNOT REACH the corner edge" in _sbJ and "\"noreach\": True}" in _sbJ,
          "31bq R7W W2 (R7Wj): the short_ branch records a chain end whose corner edge leaves the junction against the offset (axis . D < -0.2) or whose nearest point on it is the junction (within THIN_MM) as NOREACH - not ramped")
    check("\"noreach\": {int(k__): dict(v__) for k__, v__ in NOREACH.items()}" in _sbJ, "31bq R7W W2 (R7Wj): the member's record carries noreach")
    check("if _noreach_at(fa, ea_) is not None or _noreach_at(fb, eb_) is not None: continue" in _sbJ, "31bq R7W W2 (R7Wj): the contacts pass skips a noreach junction (a sweep onto the other's end would land off the edge)")
    check("_nra = _noreach_at(fa, ea_); _nrb = _noreach_at(fb, eb_)" in _sbJ and "the chain ENDS at that junction - %s and %s taper to it" in _sbJ and "THE WAY OUT is a layout / lines decision" in _sbJ and (_sbJ.count("_give_up(ia_, ea_); _give_up(ib_, eb_)") + _sbJ.count("_give_up(ia_, ea_, cap=False); _give_up(ib_, eb_, cap=False)")) >= 4,
          "31bq R7W W2 (R7Wj): the settle pass gives both members' ends up at a noreach junction (the taper) and says the way out")
    import ast as _astJ
    _tJ = _astJ.parse(_sbJ); _fnJ = next((n for n in _tJ.body if isinstance(n, _astJ.FunctionDef) and n.name == "_noreach_at"), None); _nsJ = {}
    if _fnJ is not None: exec(compile(_astJ.Module(body=[_fnJ], type_ignores=[]), "sk_build.py:_noreach_at", "exec"), _nsJ)
    _useJ = [i for i, l in enumerate(_sbJ.split("\n")) if "_noreach_at(" in l and not l.lstrip().startswith("def _noreach_at")]
    check(_fnJ is not None and _fnJ.lineno - 1 < min(_useJ) and _nsJ["_noreach_at"]({"noreach": {0: {"mm": 0.87}}}, 0) == {"mm": 0.87} and _nsJ["_noreach_at"]({"noreach": {"1": {"mm": 0.3}}}, 1) == {"mm": 0.3}
          and _nsJ["_noreach_at"]({"noreach": {0: {"mm": 0.87}}}, 1) is None and _nsJ["_noreach_at"]({}, 0) is None,
          "31bq R7W W2 (R7Wj): _noreach_at stands above its first caller and reads the record by int or str key, None without")
except Exception as _exJ: check(False, "the 31bq R7W W2 (R7Wj) pins raised %r" % (_exJ,))
try:
    _sbJb = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    check("m_[\"chain_lines\"] = sorted({int(x_[\"line\"]) for x_ in mem})" in _sbJb and "CHAIN_LINES = set(int(x_) for x_ in (f_.get(\"chain_lines\") or []))" in _sbJb
          and "_mate_ = (f == CHAIN_A and kk in CHAIN_LINES and kk != k and str(e_) in CHAIN_C)" in _sbJb and "is chain-mate %d's crease - no border to cut" in _sbJb,
          "31bq R7W W2 (R7Wj b): a freed chain end on the common face does not cut a chain-mate's crease - it tapers there (the chain's lines on the member record)")
    _lnJb = _sbJb.split("\n"); _iB2 = next(i for i, l in enumerate(_lnJb) if "CHAIN_LINES = set(int(x_)" in l); _iB3 = next(i for i, l in enumerate(_lnJb) if "_mate_ = (f == CHAIN_A and kk in CHAIN_LINES" in l)
    check(_iB2 < _iB3, "31bq R7W W2 (R7Wj b): CHAIN_LINES is bound before the meet pass reads it")
except Exception as _exJb: check(False, "the 31bq R7W W2 (R7Wj b) pins raised %r" % (_exJb,))
# recorded
try:
    _sbJc = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    check("class _NoRoom(RuntimeError):" in _sbJc and _sbJc.count("_e_nr = _NoRoom(") == 2 and "_e_nr.at = np.asarray(cross_[2], float); raise _e_nr" in _sbJc and "_e_nr.at = None; raise _e_nr" in _sbJc,
          "31bq R7W W2 (R7Wj c): both width-rule refusals are _NoRoom and carry the place where the room ends")
    check("TAPER_RUN = {int(k__): float(v__) for k__, v__ in (f_.get(\"taper_run\") or {}).items()}" in _sbJc and "_ro_e = {int(e__): max(run_out_, TAPER_RUN.get(int(e__), 0.0)) for e__ in TAPER_ENDS}" in _sbJc and "np.minimum.reduce([K.taper_weights(S_, _ro_e[int(e__)], ends=(int(e__),)) for e__ in TAPER_ENDS])" in _sbJc,
          "31bq R7W W2 (R7Wj c): the taper's run-out is per end - a member's taper_run lengthens one end")
    check("def _give_up(i_, e_, cap=True):" in _sbJc and "for form_ in ((\"taper\", \"taper-long\", \"cap\") if cap else (\"taper\", \"taper-long\")):" in _sbJc and "TAPERS FROM WHERE THE ROOM ENDS" in _sbJc
          and "_give_up(ia_, ea_, cap=False); _give_up(ib_, eb_, cap=False)" in _sbJc and "_open_why[f0_.get(\"key\")] = _wo_" in _sbJc and "_owhy_ = _open_why.get(fx_.get(\"key\")" in _sbJc,
          "31bq R7W W2 (R7Wj c): the freed end's ladder taper / taper from where the room ends / cap, no cap at a reflex-corner junction, the open end's why recorded and read by the drop line")
    _Sc = np.column_stack([np.linspace(0.0, 6.0, 61), np.zeros(61), np.zeros(61)])
    _w1 = K.taper_weights(_Sc, 1.0, ends=(0, 1)); _w2 = np.minimum.reduce([K.taper_weights(_Sc, 1.0, ends=(0,)), K.taper_weights(_Sc, 1.0, ends=(1,))]); _w3 = np.minimum.reduce([K.taper_weights(_Sc, 2.5, ends=(0,)), K.taper_weights(_Sc, 1.0, ends=(1,))])
    check(np.allclose(_w1, _w2) and abs(_w3[10] - K.taper_weights(_Sc, 2.5, ends=(0,))[10]) < 1e-12 and _w3[10] < _w1[10] and abs(_w3[-11] - _w1[-11]) < 1e-12,
          "31bq R7W W2 (R7Wj c): per-end taper weights equal the one-call form at equal run-outs and lengthen one end alone (s 1.0: %.3f against %.3f)" % (_w3[10], _w1[10]))
except Exception as _exJc: check(False, "the 31bq R7W W2 (R7Wj c) pins raised %r" % (_exJc,))
try:
    _sbJd = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    check("_mate_ = (f == CHAIN_A and kk in CHAIN_LINES and kk != k and str(e_) in CHAIN_C)" in _sbJd and "for Jv_ in (v_.get(\"J\") or [])) for v_ in FIL_MERGE.values()):" in _sbJd and "but no made member of it ends there (dropped or failed)" in _sbJd and "                if _mate_:\n" in _sbJd,
          "31bq R7W W2 (R7Wj d): the chain-mate rule reads FIL_MERGE - a dropped or failed mate's crease is a sharp border met as a free end's")
    check("if _pass == \"settle\" and fa.get(\"key\") in _open_: continue" in _sbJd and "if hit is not None and _pass == \"settle\" and fls[hit[0]].get(\"key\") in _open_: continue" in _sbJd,
          "31bq R7W W2 (R7Wj d): the settle pass skips an OPEN member and a junction whose partner is OPEN")
    _lnJd = _sbJd.split("\n"); _iD1 = next(i for i, l in enumerate(_lnJd) if "_mate_ = (f == CHAIN_A" in l); _iD1b = next(i for i, l in enumerate(_lnJd) if l.rstrip() == "                if _mate_:")
    check(0 < _iD1b - _iD1 <= 8 and "is chain-mate %d's crease - no border to cut" in "\n".join(_lnJd[_iD1b:_iD1b + 8]), "31bq R7W W2 (R7Wj d): the made-mate test guards the no-border branch (R7Wj b) directly")
except Exception as _exJd: check(False, "the 31bq R7W W2 (R7Wj d) pins raised %r" % (_exJd,))
try:
    _sbF16 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    check("m_[\"freed\"] = sorted(set(int(x_) for x_ in (m_.get(\"freed\") or [])) | {int(em_)})" in _sbF16 and "FREED = set(int(x_) for x_ in (f_.get(\"freed\") or []))" in _sbF16
          and "if SPLIT_END[e_j] or CHAIN_END[e_j] or str(e_j) in CHAIN_C or e_j in FREED: continue" in _sbF16,
          "31bq R7W W2 (F.16): an end that is or was a chain end gives no border reference for the face's side")
    check("_Fo16 = BF[int(PJ[f][\"face\"])]" in _sbF16 and "_Fo16.isPartOfDomain(_uu16, _vv16)" in _sbF16 and "if _ins16[1] and not _ins16[0]:" in _sbF16 and "set by its OWN B-rep face" in _sbF16,
          "31bq R7W W2 (F.16): on an original face the face's own B-rep decides the side - the offset's side inside, the other outside, else turned and said")
    _lnF16 = _sbF16.split("\n"); _iA = next(i for i, l in enumerate(_lnF16) if "_Fo16 = BF[int(PJ[f]" in l); _iB = next(i for i, l in enumerate(_lnF16) if l.startswith("        O_ = S_ + t_[:, None] * D_")); _iC = next(i for i, l in enumerate(_lnF16) if "elif _dref9: D_ = -D_" in l)
    check(_iC < _iA < _iB, "31bq R7W W2 (F.16): the B-rep arbiter runs after the mesh / vote / border decision and before the offset is laid")
except Exception as _exF16: check(False, "the 31bq R7W W2 (F.16) pins raised %r" % (_exF16,))
try:
    _sbP = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_build.py"), encoding="utf-8").read()
    check("check(True) FAILS on %d face(s): %s%s" in _sbP and "and %d more (skin\\\\solid_c.json check_faces names them all)" in _sbP and "check(True) FAILS on face(s) %s\" % \", \".join" not in _sbP,
          "31bq P12: the PASS line names the count of failing check(True) faces and says when its list of 12 is cut")
    _fmt = "check(True) FAILS on %d face(s): %s%s" % (18, ", ".join("%d (x)" % i for i in range(12)), (" and %d more (skin\\solid_c.json check_faces names them all)" % 6))
    check(_fmt.startswith("check(True) FAILS on 18 face(s): 0 (x), 1 (x)") and _fmt.endswith("11 (x) and 6 more (skin\\solid_c.json check_faces names them all)"), "31bq P12: the form with 18 failing faces names 12 and 'and 6 more'")
except Exception as _exP: check(False, "the 31bq P12 pins raised %r" % (_exP,))
# corner edge
try:
    import re as _re31
    _rbd = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild"); _sbB = open(os.path.join(_rbd, "sk_build.py"), encoding="utf-8").read(); _spB = open(os.path.join(_rbd, "sk_points.py"), encoding="utf-8").read(); _swB = open(os.path.join(_rbd, "sk_wires.py"), encoding="utf-8").read(); _krB = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit_rebuild.py"), encoding="utf-8").read()
    check("if len(pv_) >= 3: _, _, vh_ = np.linalg.svd(pv_ - pv_.mean(0), full_matrices=False)" in _spB and "the SVD of one point has one row" in _spB, "31br G4a: a restart spot with fewer than three centroids takes the default iso directions - the pick never crashes on its pictures")
    check(all("31br D3 (2026-10-29): a crash's TRACEBACK reaches the log" in x for x in (_sbB, _spB, _swB)) and all("init_globals={\"_SK_INNER\": True}" in x for x in (_sbB, _spB, _swB)), "31br D3: sk_build / sk_points / sk_wires print a crash's traceback (the runpy shim, the inner run marked by init_globals)")
    check("def _sweep_declined(kk_, V_):" in _sbB and _sbB.count("_sweep_declined(int(kk_v), V_)") == 5 and "made as a SINGLE blend at its decided R after the vertex ball was declined" in _sbB, "31br D1: every declined vertex ball sweeps its held corner-edge fillet as a single blend (four decline paths)")
    _iH = _sbB.index("def _sweep_declined(kk_, V_):"); _iC = _sbB.index("_sweep_declined(int(kk_v), V_)"); check(_iH < _iC, "31br D1: the helper is defined above its first call")
    check("the _add / _fillets SHAPES are checked here, in the first second" in _swB and "ONE member is \\\"line\\\"" in _swB, "31br D5: the LINES file's _add / _fillets shapes are checked right after the read; a one-element lines is taken as line")
    check("LINES CARRIED on the same network (31br D8)" in _swB and "CARRY=drop" in _swB, "31br D8: a same-network LINES file carries the last run's decisions it lacks, said; CARRY=drop drops them")
    _w9 = _re31.sub(r"\s*\[carried from chain[^\]]*\]", "", "the keel's straight run, 17.0 mm [carried from chain 82 (0.00 mm)]"); check(_w9 == "the keel's straight run, 17.0 mm" and "31br D9: the carry suffix is the kit's" in _swB, "31br D9: the carry suffix is stripped before the reason's lengths are read (%r)" % _w9)
    _ln9 = "    8s  face 4: SPAN FAILED - piece A of 2 (chains [30, 33, 99], 4 edges, 3 added line(s); x -33.6..33.6 y -122.8..-100.4 z 67.1..87.5): the PLATE BALLOONS 813.4 mm"
    _m9 = _re31.search(r"face\s+(\d+): SPAN FAILED - piece \S+ of \d+ \(chains \[[^\]]*\], \d+ edges?, (\d+) added line", _ln9)
    check(_m9 is not None and _m9.group(1) == "4" and _m9.group(2) == "3" and "def wires_try_faces(out):" in _krB and "def wires_refusal(folder, step):" in _krB and "or wires_refusal(folder, step)" in _krB and "_wf = wires_try_faces(out)" in _krB,
          "31br G4b: d10's SPAN FAILED line reads as face 4 with 3 added lines - a WIRES try; three lock skin-build until skin-wires runs again (the refusal wired beside the points' lock)")
except Exception as _ex31: check(False, "the 31br batch 1 pins raised %r" % (_ex31,))
try:
    import re as _re32, tempfile as _tf32, json as _js32, importlib.util as _iu32
    _kd32 = os.path.dirname(os.path.abspath(__file__)); _rb32 = os.path.join(_kd32, "rebuild")
    _rd = lambda *p: open(os.path.join(*p), encoding="utf-8", errors="replace").read()
    _sb = _rd(_rb32, "sk_build.py"); _sw = _rd(_rb32, "sk_wires.py"); _sp = _rd(_rb32, "sk_points.py"); _sl = _rd(_rb32, "sk_lib.py"); _kr = _rd(_kd32, "kit_rebuild.py"); _kp = _rd(_kd32, "kit.py"); _lg = _rd(_kd32, "leangate.py")
    _wc = _rd(_kd32, "..", "hooks", "wallclock.py"); _gd = _rd(_kd32, "..", "hooks", "guard.py"); _la = _rd(_kd32, "..", "tools", "look_at.py"); _et = _rd(_kd32, "..", "EDIT_TYPES.md"); _bs = _rd(_kd32, "..", "BURRITO_STEPS.md")
    check("if os.environ.get(\"SKIN_PREFLIGHT\") == \"1\":" in _sb and _sb.index("if os.environ.get(\"SKIN_PREFLIGHT\") == \"1\":") < _sb.index("# ---- 5. shell, solid") and "\"span_failed\": _pf_sf" in _sb and "\"pieces_failed\": _pf_pcs" in _sb,
          "31br G1 / G2: sk_build in preview mode records every changed face's span and every decided line's verdict (skin\\preflight.json) and ends BEFORE the shell")
    check("_env9[\"SKIN_PREFLIGHT\"] = \"1\"" in _sw and "\"preflight\": PREVIEW" in _sw and "PREVIEW VERDICT - THE BUILD WOULD FAIL (31br G1)" in _sw and "not_made_unaccepted" in _sw and _sw.count("\"sharp_ok\": _sok_of(f_,") == 4,
          "31br G1 / G2: skin-wires launches the preview child after its records, writes its verdict into WIRES_LOOK.json 'preflight'; a fillet entry's \"sharp_ok\" accepts it sharp")
    check("_pf = cuts.get(\"preflight\")" in _kr and "was NOT TAKEN" in _kr and "the PREVIEW says skin-build would FAIL on this wireframe" in _kr and "sk(\"preflight.json\")" in _kr and "\"PREFLIGHT\", \"TRACE_TUBE_MM\", \"ADD_VIA_TOL\"" in _kr,
          "31br G1 / G2: the judge refuses a wires ok without a taken, passed preview; preflight.json is a declared output; the three levers are registered")
    check("tags\", \"*\", \"points1000.json\"" in _sp and "OLD = json.load(open(_PREV_PTS" in _sp and "its close-ups could not be set up" in _sp, "31br G4a (2)(3): the KEEP falls back to the newest tag copy of the points; a spot whose close-up fails never fails the pick")
    _spec = _iu32.spec_from_file_location("_kr32", os.path.join(_kd32, "kit_rebuild.py")); _krm = _iu32.module_from_spec(_spec); _spec.loader.exec_module(_krm)
    _wf = _krm.wires_try_faces("   17s  face 4: SPAN FAILED - piece E of 5 (chains [7, 30, 33, 99], 6 edges, 2 added line(s); x -10.8..10.8): the Coons patch folds\nFAIL: the skin's shell did not close - 14 free edge(s)")
    check(isinstance(_wf, dict) and list(_wf) == [4] and _wf[4].startswith("face 4: SPAN FAILED - piece E of 5") and "shell did not close" not in _wf[4], "31br G4b (2): the wires try's record is the face's own SPAN FAILED line, not the shell's FAIL line")
    with _tf32.TemporaryDirectory() as _td:
        _skd = os.path.join(_td, "skin"); os.makedirs(_skd)
        _g0 = [{"face": 4, "role": "split", "kind": "CUBIC", "ends": [[0, 0, 0], [1, 1, 1]], "why": "the belly"}]
        _js32.dump(_g0, open(os.path.join(_skd, "guides.json"), "w")); _js32.dump({"network_md5": "n1", "chains": [{"chain": 7, "pair": [4, 9], "rung": "ARC", "decided": True}]}, open(os.path.join(_skd, "wire_simplify.json"), "w"))
        _s1 = _krm._face_lines_sig(_td, 4); _s9 = _krm._face_lines_sig(_td, 9); _s0 = _krm._face_lines_sig(_td, 2)
        check(_s1 != "none" and _s9 != "none" and _s0 == "none" and _s1 != _s9, "31br G4b (3): a face's lines signature reads its added lines and its borders' decisions; a face with none is 'none'")
        _t_lock = time.time() - 100
        _js32.dump({"spots": [], "wires": {"4": {"tries": [{"tag": "a"}, {"tag": "b"}, {"tag": "c"}], "locked_at": _t_lock, "lines_sig": _s1, "network_md5": "n1"}}}, open(os.path.join(_skd, "RESTART.json"), "w"))
        os.utime(os.path.join(_skd, "wire_simplify.json"), (_t_lock - 50, _t_lock - 50))
        _r1 = _krm.wires_refusal(_td, "skin-build"); check(_r1 is not None and "has not run since the lock" in _r1, "31br G4b (3): no wires run since the lock - refused")
        os.utime(os.path.join(_skd, "wire_simplify.json"), None)
        _r2 = _krm.wires_refusal(_td, "skin-build"); check(_r2 is not None and "UNCHANGED" in _r2, "31br G4b (3): a wires run with the face's lines UNCHANGED keeps the lock, said (a tester agent's E2)")
        _g0[0]["ends"] = [[0, 0, 0], [2, 2, 2]]; _js32.dump(_g0, open(os.path.join(_skd, "guides.json"), "w"))
        _r3 = _krm.wires_refusal(_td, "skin-build"); _rs = _js32.load(open(os.path.join(_skd, "RESTART.json")))
        check(_r3 is None and "released" in _rs["wires"]["4"] and "changed" in _rs["wires"]["4"].get("released_why", ""), "31br G4b (3): the lock releases when the lines at that face CHANGE")
        _js32.dump({"spots": [], "wires": {"4": {"tries": [{"tag": "a"}, {"tag": "b"}, {"tag": "c"}], "locked_at": _t_lock, "lines_sig": _krm._face_lines_sig(_td, 4), "network_md5": "n1"}}}, open(os.path.join(_skd, "RESTART.json"), "w"))
        _js32.dump({"taken": True, "span_failed": [], "faces": {"4": {"span": "nurbs"}}}, open(os.path.join(_skd, "preflight.json"), "w"))
        _r4 = _krm.wires_refusal(_td, "skin-build"); check(_r4 is None and "preview" in _js32.load(open(os.path.join(_skd, "RESTART.json")))["wires"]["4"].get("released_why", ""), "31br G4b (3): the lock releases when the new wires run's PREVIEW spans the face")
        _pg = _krm.step_page("skin-wires", _kd32); check(_pg.startswith("  page    : THE SKIN-WIRES PAGE") and "THE PIECE RULE" in _pg and "PREVIEW" in _pg and len(_pg.splitlines()) < 40 and set(_krm.step_pages_list(_kd32)) >= {"skin-points", "skin-features", "skin-wires", "skin-build", "skin-look", "judge"},
              "31br I1: the six step pages exist; skin-wires' page carries the piece rule and the preview, under 40 lines, printed as 'page' lines")
        check("_pg = step_page(step)" in _kr and "if cls == \"burrito\" and \"--step\" in args:" in _kp, "31br I1: the runner prints the page at the step; kit howto burrito --step prints it alone")
        _spec2 = _iu32.spec_from_file_location("_wc32", os.path.join(_kd32, "..", "hooks", "wallclock.py")); _wcm = _iu32.module_from_spec(_spec2); _spec2.loader.exec_module(_wcm)
        os.makedirs(os.path.join(_td, "claude_code"))
        open(os.path.join(_td, "claude_code", "WALL_CLOCKS.md"), "w", encoding="utf-8").write("| job | typical | samples (s) | red flag at 1.5x | notes |\n|---|---|---|---|---|\n| `kit rebuild skin-build` | **96 s** | 96 | **144 s** | x |\n| `kit rebuild skin-build LINES=1` | **500 s** | 500 | **750 s** | x |\n| `kit rebuild skin-look` | **66 s** | 66 | **99 s** | x |\n| `kit rebuild skin-look LOOK_MODE=full` | **268 s** | 268 | **402 s** | x |\n")
        _b1 = _wcm.budget_for("python kit.py rebuild skin-build --job X --tag t", "Bash", _td); _b2 = _wcm.budget_for("python kit.py rebuild skin-look --job X --set LOOK_MODE=full", "Bash", _td); _b3 = _wcm.budget_for("python kit.py rebuild skin-look --job X --set LOOK_MODE=quick", "Bash", _td)
        check(abs(_b1[0] - 500 * 1.5 / 60) < 1e-6 and "mode rows" in _b1[1] and abs(_b2[0] - 268 * 1.5 / 60) < 1e-6 and "LOOK_MODE=full" in _b2[1] and abs(_b3[0] - 268 * 1.5 / 60) < 1e-6,
              "31br D12 (a): a typed line without the mode takes the family's largest typical; with the mode its own row (an unknown mode row falls to the family) - got %s / %s / %s" % (_b1, _b2, _b3))
        check("LOOK_MODE=%s" in _kr and "row += \" LINES=%d\"" in _kr, "31br D12 (a): the runner records the mode row (skin-look LOOK_MODE=, skin-build LINES=)")
        _jb = os.path.join(_td, "claude_code", "jobs"); os.makedirs(os.path.join(_jb, "REAL_JOB")); os.makedirs(os.path.join(_jb, "REBUILD_X_chnf")); os.makedirs(os.path.join(_jb, "SCRATCH")); open(os.path.join(_jb, "SCRATCH", ".setup_side"), "w").write("")
        open(os.path.join(_td, "claude_code", "STATE_NOW.md"), "w").write("x"); time.sleep(0.05)
        for _n in ("REBUILD_X_chnf", "SCRATCH"):
            for _i in range(4): open(os.path.join(_jb, _n, "a%d.json" % _i), "w").write("{}")
        _nb, _fb, _hs = _wcm.state_behind(_td); check(os.path.basename(_fb) == "REAL_JOB" and _nb == 0, "31br D12 (c): a `_chnf` folder or one holding .setup_side is never the newest job counted (got %s, %d)" % (_fb, _nb))
    check("if sid:      # 31br D12 (b)" in _wc and "str(int(time.time()))[-6:]" not in _wc.split("if sid:      # 31br D12 (b)")[1][:600], "31br D12 (b): a background launch with no id in the reply registers no watch")
    check("for _kp in _kps:" in _gd and "_kps.append(_m)" in _gd and _gd.count("_kps.append(_m)") == 2, "31br D12 (e): the guard judges every kit call of the line (its own pipe stretch)")
    check("not j.get(\"applied_to\")" in _lg and "edit_type" in _lg.split("not j.get(\"applied_to\")")[0][-200:], "31br D12 (d): a burrito job keeps its frames until `kit apply --job` (applied_to), not kit accept's gate mark")
    _spec3 = _iu32.spec_from_file_location("_sl32", os.path.join(_rb32, "sk_lib.py"))
    try:
        _slm = _iu32.module_from_spec(_spec3); _spec3.loader.exec_module(_slm)
        _p1 = [{"face": 7, "region": 0, "off_mm2": 12.0, "removed_mm2": 11.0, "filled_mm2": 1.0, "drop": (1, "the slot is closed"), "blend": None}, {"face": 8, "region": 0, "off_mm2": 12.0, "removed_mm2": 1.0, "filled_mm2": 11.0, "drop": (1, "the slot is closed"), "blend": None}]
        _slm.classify_parts(_p1, {"no_points": [7, 8]}); check(_p1[0]["cls"] == "removed" and "never removal" in _p1[0]["why"] and _p1[1]["cls"] == "dropped", "31br G3: a drop box excuses FILLING (cls dropped), never REMOVAL (cls removed, named) - d8 / d9's keel")
    except Exception as _exsl: check("r_[\"cls\"] = \"removed\"" in _sl, "31br G3: the classify rule is in sk_lib (the module could not be imported here: %s)" % str(_exsl)[:80])
    check("ends_too" in _sb and "31br D1 (c)" in _sb and "\"members\": sorted({int(_m0[\"line\"])}" in _sb and "if not V_.get(\"_final\"):" in _sb and "_fillet_lines(dict(f_, check_only=True, ends_too=True))" in _sb and "at the junction its side face is a WEDGE" in _sb and "_sd9 = globals().get(\"_sweep_declined\")" in _sb and _sb.index("_sd9 = globals().get(\"_sweep_declined\")") < _sb.index("_w9 = \"held for the vertex ball"),
          "31br D1 (b): the single blend after a declined ball is swept only where its side faces have room AT the junction (the width rule with ends_too); the retry's not-reached path tries the same")
    check("def _clip_guides(gp_, polys_, pi_):" in _sb and _sb.count("_clip_guides([np.array(") == 2 and _sb.index("def _clip_guides(") < _sb.index("_clip_guides([np.array("), "31br D2: the lines pass clips a face's guides to its loop of this pass at both span sites; the helper above its callers")
    check("_nopt_" in _sb and _sb.count("int(x_) not in _nopt_") == 2 and "not a source surface for the host (31br D4" in _sb, "31br D4: a face the points dropped is no source surface for a buried host, said")
    check("ADD_VIA_TOL = float(os.environ.get(\"ADD_VIA_TOL\"" in _sw and "_ADD_POLES[\"n\"] = a_.get(\"poles\")" in _sw and "a line is drawn THROUGH the points you give it or not at all" in _sw and "\"via_dev_mm\": _ADD_POLES.get(\"dev\")" in _sw,
          "31br D6: an added line's cubic through more than two via points is measured against them and refused over ADD_VIA_TOL; \"poles\": n on the entry; the deviation recorded and said")
    check("TRACE_TUBE_MM = float(os.environ.get(\"TRACE_TUBE_MM\"" in _sw and _sw.count("> TRACE_TUBE_MM: continue") == 2 and "_pnT = None" in _sw and "a_[\"span\"] == \"face\"" in _sw and "if span_ == \"face\" else" in _sw, "31br D10: the trace follows its face within the tube SIDEWAYS of the line's own plane (both paths); \"span\": \"face\" interpolates across the whole face")
    check("SUBJ = [i for i in sel if BOX[0] <= 0.5 *" in _la and "subject faces in view from that camera" in _la and "def _cut_for(d_):" in _la and "K.view_piece(R, path, _V2, _T2, _F2, _C2, d, tuple(BOX)" in _la, "31br D11: look_at's subject is the faces centred in the box, the share per face said, a hidden one named; SECTION cuts the camera's half away")
    check("def _cut_mesh(d_):" in _la and "def _cap_make():" in _la and "Part::FaceMakerBullseye" in _la and "cut by their centres" not in _la and "the cap faces the camera" in _la and "polylines=box_lines + list(_cpl)" in _la,
          "31br D11b: the SECTION clips every straddling triangle AT the plane (nothing by centroid) and caps the cut with the kernel's section, outlined, turned toward the camera (the agent's render_section_shred)")
    check(all("PROJECT_FACTS section 6" in x for x in (_kp, _et, _bs, _lg)) and "ruled open), never round enclosed air" not in _kp and "is RULED OPEN (PROJECT_FACTS, 2026-09-21)" not in _et, "31br D13: the four slot texts read the project's ruling (PROJECT_FACTS section 6, the newest line), none hard-codes 'ruled open'")
    check("LINES PASS - FAILED, FIRST THE THREE THINGS (31br I2):" in _sb and _sb.index("rc_, out_ = _lines_child(FIL_RERUN)") < _sb.index("FIRST THE THREE THINGS"), "31br I2: after a failed lines pass the three things are printed first")
    _rx1 = r"\b(cannot|can't|can not|could not|couldn't|unable to) be (built|made|blended|spanned|filled|rounded)\b|\bkit (cannot|can't|could not)\b|\bunbuildable\b|\bnot buildable\b"; _rx2 = r"\b(tag|build|run|try|tried)\b\s*[:=#]?\s*[A-Za-z]*\d[A-Za-z0-9_-]*|\b[a-z]{1,4}\d{1,3}[a-z]?[a-z0-9]{0,4}\b"
    _n1 = "the vane-2 curl and the crown knife edge cannot be built by the kit"; _n2 = "the crown knife edge cannot be built by the kit - tried as tag d7, PLATE BALLOONS 110 mm"; _n3 = "every line where its feature's edge is, one simple curve, both sides alike"
    check(bool(_re32.search(_rx1, _n1, _re32.I)) and not _re32.search(_rx2, _n1) and bool(_re32.search(_rx2, _n2)) and not _re32.search(_rx1, _n3, _re32.I) and "31br I3" in _kr, "31br I3: a note stating a limit without a build tag is refused; with the tag, or a plain note, it passes")
except Exception as _ex32: check(False, "the 31br batch 2 pins raised %r" % (_ex32,))
# nothing to pick
try:
    import tempfile as _tf4c, json as _js4c, importlib.util as _iu4c, numpy as _np4c
    _kd4c = os.path.dirname(os.path.abspath(__file__))
    _kr4c = open(os.path.join(_kd4c, "kit_rebuild.py"), encoding="utf-8", errors="replace").read(); _sp4c = open(os.path.join(_kd4c, "rebuild", "sk_points.py"), encoding="utf-8", errors="replace").read()
    check("def _spot_candidates(folder, box):" in _kr4c and "def release_void_spots(folder, say=print):" in _kr4c and _kr4c.count("release_void_spots(folder") >= 4
          and "holds NO source-triangle centroid - nothing to pick there" in _sp4c and "LOCKED = [s_ for s_ in LOCKED if np.any(_inbox(Cn, s_[\"box\"]))]" in _sp4c,
          "31br G4c: the candidate count, the release at the gate / the judge / before skin-points / at the lock, and sk_points' own line")
    _spec4 = _iu4c.spec_from_file_location("_kr4c", os.path.join(_kd4c, "kit_rebuild.py")); _krm4 = _iu4c.module_from_spec(_spec4); _spec4.loader.exec_module(_krm4)
    with _tf4c.TemporaryDirectory() as _td4:
        _sk4 = os.path.join(_td4, "skin"); os.makedirs(_sk4)
        _np4c.savez(os.path.join(_sk4, "regions.npz"), Vu=_np4c.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]], float), F=_np4c.array([[0, 1, 2], [1, 3, 2]]), vreg=_np4c.zeros(4, int))
        _js4c.dump({"points": [[0.33, 0.33, 0.0, 7]]}, open(os.path.join(_sk4, "points1000.json"), "w"))
        check(_krm4._spot_candidates(_td4, [0, 1, 0, 1, -1, 1]) == 2 and _krm4._spot_candidates(_td4, [22, 26, -122, -118, 77, 81]) == 0 and _krm4._spot_candidates(os.path.join(_td4, "nowhere"), [0, 1, 0, 1, 0, 1]) is None,
              "31br G4c: the candidate count reads the source centroids inside the box; None when the mesh cannot be read")
        _dg6 = _krm4._points_inside(_td4, [0, 1, 0, 1, -1, 1])
        _js4c.dump({"spots": [{"id": 5, "box": [22, 26, -122, -118, 77, 81], "tries": [{"what": "skin-build", "md5": "a", "why": "x", "when": "t"}] * 3, "locked": True, "locked_at": "t", "points_at_lock": "d:0"},
                              {"id": 6, "box": [0, 1, 0, 1, -1, 1], "tries": [{"what": "skin-build", "md5": "a", "why": "x", "when": "t"}] * 3, "locked": True, "locked_at": "t", "points_at_lock": _dg6}]},
                   open(os.path.join(_sk4, "RESTART.json"), "w"))
        _ref4 = _krm4.restart_refusal(_td4, "skin-labels"); _st4 = _js4c.load(open(os.path.join(_sk4, "RESTART.json")))
        check(_ref4 is not None and "1 SPOT(S)" in _ref4 and "spot 6" in _ref4 and "spot 5" not in _ref4 and [s["id"] for s in _st4["spots"] if s.get("locked")] == [6]
              and any(h.get("spot") == 5 and "nothing to pick" in h.get("why", "") for h in _st4.get("history", [])),
              "31br G4c: the gate releases the spot with nothing to pick (the history says why) and still refuses for the spot that has points to pick")
        _ok4, _why4 = _krm4.points_judged(_td4, say=lambda *a: None)
        check(_ok4 is False and "spot(s) [6]" in _why4, "31br G4c: the judge still holds the spot whose points are unchanged - the release is only for a spot with nothing to pick")
        _js4c.dump({"spots": [{"id": 5, "box": [22, 26, -122, -118, 77, 81], "tries": [{"what": "skin-build", "md5": "a", "why": "x", "when": "t"}] * 3, "locked": True, "locked_at": "t", "points_at_lock": "d:0"}]},
                   open(os.path.join(_sk4, "RESTART.json"), "w"))
        _ok5, _why5 = _krm4.points_judged(_td4, say=lambda *a: None)
        check(_ok5 is True and "[5]" in _why5, "31br G4c: a points verdict with only a nothing-to-pick spot locked passes and names it released")
        _js4c.dump({"spots": []}, open(os.path.join(_sk4, "RESTART.json"), "w")); _said4 = []
        for _m4 in ("m1", "m2", "m3"): _krm4.record_try(_td4, "skin-build", _m4, "FAIL: the shell did not close", [[22, 26, -122, -118, 77, 81]], say=lambda *a: _said4.append(" ".join(str(x) for x in a)))
        _st5 = _js4c.load(open(os.path.join(_sk4, "RESTART.json")))
        check(_st5["spots"] and not _st5["spots"][0].get("locked") and _st5["spots"][0].get("void") and len(_st5["spots"][0]["tries"]) == 3 and any("NOT a points spot" in s for s in _said4),
              "31br G4c: three failed tries at a box with nothing to pick never lock it - said, the tries kept on record")
        _said4b = []
        for _m4 in ("m1", "m2", "m3"): _krm4.record_try(_td4, "skin-build", _m4, "FAIL: the shell did not close", [[0, 1, 0, 1, -1, 1]], say=lambda *a: _said4b.append(" ".join(str(x) for x in a)))
        check(any(s.get("locked") for s in _js4c.load(open(os.path.join(_sk4, "RESTART.json")))["spots"]) and any("THREE FAILED TRIES AT SPOT" in s for s in _said4b),
              "31br G4c: three failed tries at a box WITH centroids still lock it (the restart rule unchanged where it applies)")
except Exception as _ex4c: check(False, "the 31br G4c pins raised %r" % (_ex4c,))

try:
    _kd44 = os.path.dirname(os.path.abspath(__file__))
    _sf44 = open(os.path.join(_kd44, "rebuild", "sk_features.py"), encoding="utf-8", errors="replace").read(); _kp44 = open(os.path.join(_kd44, "kit.py"), encoding="utf-8", errors="replace").read()
    check("_raw_of = {remap[p]: p for p in live}" in _sf44 and "in the FINAL numbering after the merges (the MERGED lines above use the layout's raw ids" in _sf44 and "(raw %d)" in _sf44,
          "31br G4c4: the still-small line says it is the final numbering and gives each face's raw id where it differs")
    check("said in full once per 6 h, last at %s; `kit status` says why" in _kp44 and "(guard still not running — said once above)" not in _kp44, "31br G4c4: the guard's once line says when it was said and where the reason is")
except Exception as _ex44: check(False, "the 31br G4c4 pins raised %r" % (_ex44,))

try:
    _kd51 = os.path.dirname(os.path.abspath(__file__))
    _sl51 = open(os.path.join(_kd51, "rebuild", "sk_look.py"), encoding="utf-8", errors="replace").read(); _kr51 = open(os.path.join(_kd51, "kit_rebuild.py"), encoding="utf-8", errors="replace").read()
    check("FACES = sorted({int(x_) for x_" in _sl51 and "if FACES: MODE = \"faces\"" in _sl51 and "LOOK_MODE=full REFUSED (31br L1" in _sl51 and "def _flagged_faces():" in _sl51 and "FACES_LOOKED.json" in _sl51
          and "for fi in (FACES if FACES else (okf if MODE == \"full\" else HIDDEN)):" in _sl51 and "if not FACES and rg in (\"cap\", \"orig\", \"flat\"): continue" in _sl51 and "\"faces_looked\": (sorted(set(FACES) - set(UNSEEN)) if FACES else FACES)" in _sl51 and "if MODE == \"quick\":      # 31br L1" in _sl51,
          "31br L1: skin-look FACES=<ids> draws only those faces (any kind), records the look as mode faces with the faces looked at, and LOOK_MODE=full is refused while a check(True) face of this piece has no targeted look")
    check("\"FACES\", \"LOOK_FULL_OK\"" in _kr51 and "a TARGETED one (FACES=%s) - a redo / move may be judged on it, an ok may not" in _kr51 and "lk.get(\"mode\") in (\"quick\", \"faces\")" in _kr51
          and "if ranked2 is None and verdict in (\"redo\", \"move\"):" in _kr51 and "elif verdict == \"ok\" and (ranked2 is None or not ok2):" in _kr51 and "THE CHECK FACES FIRST (31br L1" in _kr51 and "\"faces\" if str(env.get(\"FACES\") or \"\").strip() else" in _kr51,
          "31br L1: the runner registers the levers, refuses an ok on a targeted look, refuses the second review on it, records a REDO / MOVE of the piece without the second review (an OK still needs it), routes skin-build's NEXT to the check faces, and clocks the faces mode on its own row")
except Exception as _ex51: check(False, "the 31br L1 pins raised %r" % (_ex51,))

try:
    _kd1b = os.path.dirname(os.path.abspath(__file__)); _rb1b = os.path.join(_kd1b, "rebuild")
    _sb1b = open(os.path.join(_rb1b, "sk_build.py"), encoding="utf-8", errors="replace").read(); _sl1b = open(os.path.join(_rb1b, "sk_look.py"), encoding="utf-8", errors="replace").read()
    check("for r_ in frec if r_.get(\"fail\")]" in _sb1b and "if _pp not in _pf_sf: _pf_sf.append(_pp)" in _sb1b and "_pf_nfail_stage" in _sb1b and "for r_ in frec if \"valid\" in r_ and r_.get(\"fail\")]" not in _sb1b,
          "31br G1b: the preview's pieces_failed takes every face-stage record with a failure (a split piece appended before 'valid', a face whose 'valid' was deleted), its face joins span_failed, the stage's count is cross-checked")
    check("31br D3" in _sl1b and "_SK_INNER" in _sl1b, "31br G1b: sk_look.py carries the D3 traceback shim")
    _frec = [{"patch": 27, "sub": "A", "fail": "the surface does not take its loop"}, {"patch": 5, "fail": "its border crosses itself"}, {"patch": 9, "sub": None, "valid": True}]
    _recs = {12: {"span": "nurbs", "fail": "the Coons patch folds"}, 27: {"span": "split"}, 5: {"span": "nurbs"}, 9: {"span": "plane"}}
    _chg = [12, 27, 5, 9]; _pf_faces = {str(p): {"span": _recs[p].get("span"), "fail": _recs[p].get("fail")} for p in _chg}
    _pf_sf = sorted(int(p) for p in _chg if "fail" in _recs[p]); _pf_pcs = [{"patch": r.get("patch"), "sub": r.get("sub"), "fail": str(r.get("fail"))[:300]} for r in _frec if r.get("fail")]
    for p__ in _pf_pcs:
        _pp = int(p__["patch"])
        if _pp not in _pf_sf: _pf_sf.append(_pp)
        if str(_pp) in _pf_faces and not _pf_faces[str(_pp)].get("fail"): _pf_faces[str(_pp)]["fail"] = ("piece %s: " % p__["sub"] if p__.get("sub") else "") + p__["fail"]
    check(sorted(set(_pf_sf)) == [5, 12, 27] and _pf_faces["27"]["fail"].startswith("piece A: the surface") and _pf_faces["5"]["fail"].startswith("its border") and _pf_faces["9"]["fail"] is None and len(_pf_pcs) == 2,
          "31br G1b (the rule on crafted records): the split piece's and the self-crossing face's failures reach span_failed and the faces' records; the valid face stays clean")
except Exception as _ex1b: check(False, "the 31br G1b pins raised %r" % (_ex1b,))

# 31br D5b  more poles than points
try:
    import io as _io5b, contextlib as _cl5b
    _sw5b = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_wires.py"), encoding="utf-8").read()
    check("31br D5b" in _sw5b and "more poles than points" in _sw5b and "min(8, len(_P6), int(_ADD_POLES.get(\"n\") or 4))" in _sw5b, "31br D5b: the text - the read refuses poles over via + 2, the fit clamps to the points (the belt)")
    _i0 = _sw5b.index("        for _i5, _a5 in enumerate(_raw_l.get(\"_add\") or []):"); _i1 = _sw5b.index("        for _i5, _f5 in enumerate(_raw_l.get(\"_fillets\") or []):")
    _blk5b = "\n".join(l_[8:] for l_ in _sw5b[_i0:_i1].split("\n"))
    def _run5b(entry):
        g_ = {"_raw_l": {"_add": [entry]}}; buf_ = _io5b.StringIO()
        try:
            with _cl5b.redirect_stdout(buf_): exec(compile(_blk5b, "d5b", "exec"), g_)
        except ValueError as e_: return str(e_), buf_.getvalue()
        return None, buf_.getvalue()
    def _e5(via, poles=None, **kw): return dict({"face": 11, "role": "split", "kind": "CUBIC", "from": "c3", "to": "c19", "via": [[0.0, 0.0, float(i_)] for i_ in range(via)], "why": "the lid's upper edge along y -97.5"}, **({"poles": poles} if poles is not None else {}), **kw)
    _r1, _ = _run5b(_e5(5, 8)); check(_r1 is not None and "more poles than points" in _r1 and "7 = 5 via + the two ends" in _r1 and "31br D5b" in _r1, "31br D5b: poles 8 with 5 via points (the agent's d19 first form) REFUSED at the read, the rule said: %s" % str(_r1)[:90])
    _r2, _ = _run5b(_e5(3, 5)); check(_r2 is None, "31br D5b: poles 5 with 3 via points (the agent's d19 second form - poles = points) passes the read")
    _r3, _ = _run5b(_e5(7, 9)); check(_r3 is not None and "outside 4..8" in _r3, "31br D5b: poles 9 is outside 4..8 - refused by name")
    _r4, _o4 = _run5b(_e5(2, 6)); check(_r4 is None and "is ignored" in _o4, "31br D5b: poles with two via points is ignored and said (the line is interpolated exactly)")
    _r5, _ = _run5b(_e5(7)); check(_r5 is None, "31br D5b: an entry without poles passes the read as before")
    _r6, _ = _run5b(_e5(5, "eight")); check(_r6 is not None and "whole number" in _r6, "31br D5b: a non-number poles is refused by name")
    _r7, _o7 = _run5b(_e5(5, 8, trace=True)); check(_r7 is None and "ignored on a traced line" in _o7, "31br D5b: poles on a traced line is ignored and said")
except Exception as _ex5b: check(False, "the 31br D5b pins raised %r" % (_ex5b,))
# --supersede  skin-rim
try:
    import tempfile as _tfA2, json as _jsA2, time as _tmA2, hashlib as _hlA2, builtins as _biA2
    _rootA2 = _tfA2.mkdtemp(prefix="skin5_a2_"); _jobA2 = "JOBA2"; _fA2 = os.path.join(_rootA2, "claude_code", "jobs", _jobA2); _skA2 = os.path.join(_fA2, "skin"); _rvA2 = os.path.join(_skA2, "review")
    os.makedirs(_rvA2, exist_ok=True); os.makedirs(os.path.join(_rootA2, ".claude"), exist_ok=True)
    def _wA2(p, s):
        with open(p, "wb" if isinstance(s, bytes) else "w") as fh: fh.write(s)
    def _mdA2(p): return _hlA2.md5(open(p, "rb").read()).hexdigest()
    _kitA2 = Kit(_rootA2); _outA2 = []; _sayA2 = lambda *a: _outA2.append(" ".join(str(x) for x in a))
    def _runA2(*a):
        _outA2.clear(); p0 = _biA2.print; _biA2.print = lambda *x, **k: _outA2.append(" ".join(str(y) for y in x))
        try: return KR.cmd(list(a), _kitA2)
        except RuntimeError as ex: return "passed" if "GATES PASSED" in str(ex) else str(ex)
        finally: _biA2.print = p0
    check(all(x in KR.STATE_FILES for x in ("review/LAYOUT_LOOK.json", "review/WIRES_LOOK.json", "review/PIECE_LOOK.json", "review/LOOK_JUDGED.json", "review/FACES_LOOKED.json", "preflight.json", "guides.json", "fillets.json")),
          "31br A2 (a): the state carries the look records, the verdicts beside them and the wires' bound records")
    _pjA = os.path.join(_skA2, "patches.json"); _lkA = os.path.join(_rvA2, "LAYOUT_LOOK.json"); _frA = os.path.join(_rvA2, "LAYOUT_01_orbit_000.png")
    _wA2(_pjA, '{"patches": [{"patch": 0, "kind": "changed", "bbox": [0, 1, 0, 1, 0, 1]}]}'); _wA2(_frA, b"\x89PNG A"); _wA2(_lkA, _jsA2.dumps({"frames": ["LAYOUT_01_orbit_000.png"], "md5": _mdA2(_pjA), "tag": "sA", "pics": "full"}))
    _jsA2.dump({"what": "layout", "verdict": "ok", "md5": _mdA2(_pjA), "when": "2026-10-29 15:45:10", "note": "layout A"}, open(os.path.join(_rvA2, "LAYOUT_JUDGED.json"), "w"))
    _fsA = KR.save_state(_fA2, "sA", _sayA2, quiet=True)
    check("review/LAYOUT_LOOK.json" in _fsA and "review/LAYOUT_01_orbit_000.png" in _fsA, "31br A2 (a): save_state keeps the look record AND the frame it lists (%s)" % sorted(k for k in _fsA if k.startswith("review/")))
    _wA2(_pjA, '{"patches": [{"patch": 0, "kind": "changed", "bbox": [0, 2, 0, 2, 0, 2]}]}'); _wA2(_frA, b"\x89PNG B"); _wA2(_lkA, _jsA2.dumps({"frames": ["LAYOUT_01_orbit_000.png"], "md5": _mdA2(_pjA), "tag": "sB", "pics": "full"}))
    _jsA2.dump({"what": "layout", "verdict": "ok", "md5": _mdA2(_pjA), "when": "2026-10-29 17:56:39", "note": "layout B"}, open(os.path.join(_rvA2, "LAYOUT_JUDGED.json"), "w"))
    KR.save_state(_fA2, "sB", _sayA2, quiet=True)
    rcA = _runA2("restore", "--job", _jobA2, "--tag", "sA")
    check(rcA == 0 and _jsA2.load(open(_lkA))["tag"] == "sA" and open(_frA, "rb").read() == b"\x89PNG A" and "look records and their frames are back" in "\n".join(_outA2),
          "31br A2 (a): restore sA puts back layout A's look record AND its frame (the live B's saved as _live_ first) - %s" % ("\n".join(_outA2)[:80]))
    _stB = os.path.join(_fA2, "tags", "sB", "STATE.json"); _sj = _jsA2.load(open(_stB)); _sj["files"] = {k: v for k, v in _sj["files"].items() if not (k.startswith("review/") and (k.endswith("_LOOK.json") or k.endswith(".png")))}; _jsA2.dump(_sj, open(_stB, "w"))
    rcB = _runA2("restore", "--job", _jobA2, "--tag", "sB")
    check(rcB == 0 and not os.path.isfile(_lkA) and "SAVED BEFORE 31br A2" in "\n".join(_outA2), "31br A2 (a): a state saved before A2 brings no look record - the live one (another build's) is removed and said")
    # recorded
    _frX = os.path.join(_rvA2, "look", "look_163552_1.png"); os.makedirs(os.path.dirname(_frX), exist_ok=True); _wA2(_frX, b"\x89PNG X")
    import leangate as _lgA2
    _normA2 = lambda p: os.path.normcase(os.path.abspath(p)).replace("\\", "/")
    with open(os.path.join(_lgA2.records_root(_rootA2), ".claude", "looks.jsonl"), "a") as fh: fh.write(_jsA2.dumps({"png": _frX, "png_n": _normA2(_frX), "opened": _tmA2.time() + 2, "when": "now", "box": None, "defective": False}) + "\n")
    rcJ0 = _runA2("judge", "--job", _jobA2, "--what", "layout", "--verdict", "ok", "--note", "layout B: every face one surface, both sides alike, nothing missing - judged on nothing")
    check(rcJ0 == 2 and "is missing - the layout step writes the frames" in "\n".join(_outA2), "31br A2 (b): an OK on a missing frames record is still refused")
    rcJ1 = _runA2("judge", "--job", _jobA2, "--what", "layout", "--verdict", "redo", "--frame", "look/look_163552_1.png", "--face", "0", "--note", "look_163552_1 shows the original at the x 24 side wall - the wall outline turns where the layout has one face")
    _ljB = _jsA2.load(open(os.path.join(_rvA2, "LAYOUT_JUDGED.json")))
    check(rcJ1 == 0 and _ljB.get("verdict") == "redo" and _ljB.get("frames_record") == "missing" and "frames record is missing" in "\n".join(_outA2),
          "31br A2 (b): a REDO on an opened picture is recorded on a MISSING frames record, the record says so (%s)" % ("\n".join(_outA2)[-160:].replace("\n", " | ")))
    _wA2(_lkA, _jsA2.dumps({"frames": ["LAYOUT_01_orbit_000.png"], "md5": "0000notthislayout", "tag": "sZ", "pics": "full"})); _wA2(_frA, b"\x89PNG Z")
    _jsA2.dump({"what": "layout", "verdict": "ok", "md5": _mdA2(_pjA), "when": "2026-10-29 17:56:39", "note": "layout B again"}, open(os.path.join(_rvA2, "LAYOUT_JUDGED.json"), "w"))
    rcJ2 = _runA2("judge", "--job", _jobA2, "--what", "layout", "--verdict", "ok", "--note", "layout B: every face one surface, both sides alike, nothing missing - on stale frames")
    check(rcJ2 == 2 and "the frames show an earlier" in "\n".join(_outA2), "31br A2 (b): an OK on a stale frames record is still refused")
    rcJ3 = _runA2("judge", "--job", _jobA2, "--what", "layout", "--verdict", "redo", "--frame", "look/look_163552_1.png", "--face", "0", "--note", "look_163552_1 shows the original at the x 24 side wall - the wall outline turns where the layout has one face")
    _ljC = _jsA2.load(open(os.path.join(_rvA2, "LAYOUT_JUDGED.json")))
    check(rcJ3 == 0 and _ljC.get("verdict") == "redo" and _ljC.get("frames_record") == "stale", "31br A2 (b): a REDO on an opened picture is recorded on a STALE frames record too")
    rcJ4 = _runA2("judge", "--job", _jobA2, "--what", "layout", "--verdict", "redo", "--face", "0", "--note", "no picture cited at all - this redo must still need one (the overturn rule)")
    check(rcJ4 == 2, "31br A2 (b): a REDO with NO picture on a stale record is refused as before (the rule needs the picture)")
    # --supersede  skin-rim
    _jsA2.dump({"what": "layout", "verdict": "ok", "md5": _mdA2(_pjA), "when": "2026-10-29 17:56:39", "note": "layout B once more"}, open(os.path.join(_rvA2, "LAYOUT_JUDGED.json"), "w"))
    _wA2(os.path.join(_fA2, "wall_caps.brep"), b"caps"); _wA2(os.path.join(_fA2, "body.brep"), b"a body"); _wA2(os.path.join(_fA2, "source.stl"), b"source mesh"); _wA2(os.path.join(_skA2, "patches_labels.json"), '{"merge_smooth": 1}')
    _BA2 = "BODY=" + os.path.join(_fA2, "body.brep")
    rcS = _runA2("skin-rim", "--job", _jobA2, "--tag", "a2r", "--set", _BA2, "--supersede", "the client 2026-10-29 17:1x: close the slit with a single plane - a new feature map on the d15 points")
    check(rcS != 2 and KR.standing_ok(_fA2, "layout") is None and "the client's word on the design" in "\n".join(_outA2) and "would replace the layout" not in "\n".join(_outA2),
          "31br A2 (c): skin-rim --supersede \"<the client's words>\" supersedes the standing layout ok (no strike) and the step goes on to its gates (%s)" % rcS)
    rcS2 = _runA2("skin-points", "--job", _jobA2, "--tag", "a2p", "--set", _BA2, "--supersede", "x")
    check(rcS2 == 2 and "skin-labels' or skin-rim's" in "\n".join(_outA2), "31br A2 (c): --supersede on another step is still refused, naming both steps")
    _sp5 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "STEP_PAGES.md"), encoding="utf-8").read()
    check("31br A2" in _sp5 and "--supersede" in _sp5, "31br A2: the step pages say it (the judge's REDO on an opened picture; skin-rim --supersede)")
    _swT = open(os.path.join(HERE, "rebuild", "sk_wires.py"), encoding="utf-8").read(); _spT = open(os.path.join(HERE, "rebuild", "STEP_PAGES.md"), encoding="utf-8").read()
    check('for _kf in ("legs", "poles", "dev_max", "via", "grow_out", "cut_in", "inflections"):' in _swT and "the twin's fit fields are its master's" in _swT
          and 'recs[b_]["apex"] = [[round(float(v), 3) for v in (np.asarray(p_, float) - 2.0 * (float(np.asarray(p_, float) @ MN) - MC) * MN)] for p_ in recs[a_]["apex"]]' in _swT
          and 'else: recs[b_].pop("apex", None)' in _swT and "and that border chain is DRAWN PER LEG, the apex kept - 31bu A5 / 31bw A5b" in _spT,
          "31bw A5b (TB7 F1 / F2): a kit-mirrored twin's record carries its master's fit fields with the apex reflected, the page's LEVERS line says the per-leg draw")
    _swU = open(os.path.join(HERE, "rebuild", "sk_wires.py"), encoding="utf-8").read()
    _npU = {}
    exec("import re as _re_w\n" + _swU[_swU.index("    def _npoles_of(rung_, poles_):"):_swU.index("    def _edge_form(e_):")].replace("\n    ", "\n")[4:], _npU)
    _npf = _npU["_npoles_of"]
    check(_npf("MULTI7", 13) == 13 and _npf("MULTI7", None) == 7 and _npf("CUBIC", 13) == 13 and _npf("CUBIC", None) == 4 and _npf("LINE", 2) == 4 and _npf("V(CUBIC+ARC)", 13) == 13 and _npf("MULTI3", None) == 4 and _npf("ARC", "x") == 4,
          "31bw (TB7b F1 / TB7c F1): _npoles_of - the record's own count first (the drawn curve's), else the rung's MULTI<n>, else 4, never under 4")
    check("def redraw(M_, A, B, rec_, apex=None, form=None):" in _swU and "edges_out[b_] = redraw(blend_ends(_Sm, B0, B1), B0, B1, recs[a_], apex=_apx, form=_fa)" in _swU
          and "if np.linalg.norm(_Sm[0] - B0) > np.linalg.norm(_Sm[0] - B1): _Sm = _Sm[::-1]" in _swU and 'return _one(M_, rung_, npl_ or _npoles_of(rung_, rec_.get("poles")), kind_).toShape()' in _swU
          and "_er = redraw(0.5 * (rs(S) + rs(Rf)), A, B, recs[k], apex=_apx, form=_fk)" in _swU and 'kinds_ = [str(l_.get("rung") or "CUBIC") for l_ in legs_] or rung_[2:].rstrip(")").split("+")' in _swU
          and 'if "ON_ORIG" in kx:' not in _swU and "redraw(samp(Ma, 0.05), B0, B1, recs[a_][\"rung\"])" not in _swU
          and 'recs[b_]["dev_master"] = recs[a_].get("dev_max"); recs[b_]["dev_max"] = round(float(cKDTree(_Db).query(_Sb)[0].max()), 4)' in _swU
          and 'recs[b_]["legs_of"] = "chain %d (the master\'s per-leg fit, reflected)" % a_' in _swU,
          "31bw (TB7b F1 / F2): the mirrored twin drawn as its master's mirror carried to its own ends in the master's form (the own-twin average the same way), its own dev_max measured with the master's as dev_master")
    check("def _edge_form(e_):" in _swU and 'def _one(Sx, kx, npl, kind=None):' in _swU and "bs_.approximate(" not in _swU[_swU.index("    def _one("):_swU.index("    def redraw(")]
          and 'kind_ = kind or (base_ if base_ in ("LINE", "ARC") else "BSPLINE")' in _swU and 'recs[k]["dev_fit"] = recs[k].get("dev_max")' in _swU and '"poles": (len(cvx.getPoles()) if hasattr(cvx, "getPoles") else' in _swU
          and 'kind_, npl_ = form if form else (None, None)' in _swU and '_npoles_of(kx, (legs_[j_].get("poles") if j_ < len(legs_) else None))' in _swU and 'if _fa: recs[b_]["drawn_form"]' in _swU and 'recs[k]["drawn_form"]' in _swU and "the record's own count FIRST" in _swU
          and "in the master EDGE's own kind and pole count" in _spT and _spT.count("A kit-mirrored twin chain is DRAWN as its master's mirror image") == 0,
          "31bw (TB7c F1): a twin or an own-twin average is drawn in the master EDGE's own kind and pole count (_edge_form), never by the kernel's approximation; the average's own dev_max measured (dev_fit the fit's); a leg's record carries its poles; the page says it once")
    _klT = open(os.path.join(HERE, "..", "KERNEL_LESSONS.md"), encoding="utf-8").read()
    check("def _mirror_snapped(e_, A_, B_):" in _swU and "_snap = _mirror_snapped(Ma, B0, B1)" in _swU and "if _snap is not None: edges_out[b_] = _snap" in _swU
          and "c_.setPole(1, V3(*A_)); c_.setPole(int(c_.NbPoles), V3(*B_)); return c_.toShape()" in _swU and "Part.LineSegment(V3(*A_), V3(*B_)).toShape()" in _swU
          and _swU.index("_snap = _mirror_snapped(Ma, B0, B1)") < _swU.index("edges_out[b_] = redraw(blend_ends(_Sm, B0, B1), B0, B1, recs[a_], apex=_apx, form=_fa)")
          and "## K-C0-DIST" in _klT and "IS its master's exact mirror image, only its end points moved" in _spT,
          "31bw h (TB7c F3): a kit-mirrored twin is the master's EXACT mirror image with its end points snapped onto its own junctions - never a refit of the mirror's samples (the sampled form only as the fallback for an unknown curve kind, said); K-C0-DIST in KERNEL_LESSONS; the page says it")
    import ast as _astV, textwrap as _twV, numpy as _npV
    check("def _self_averaged(e_, A_, B_):" in _swU and "_avg = _self_averaged(_e0s, A, B)" in _swU and 'if not isinstance(_avg, str): edges_out[k] = _avg; recs[k]["self_form"] = "poles"' in _swU and 'return "its mirror runs the other way and its knot vector is not symmetric' in _swU and "no pole-level average (%s)" in _swU
          and "if _moved > _self_dev:" in _swU and 'recs[k]["self_form"] = "kept"' in _swU and 'recs[k]["self_form"] = "sampled"' in _swU
          and "bs_.buildFromPolesMultsKnots([V3(*p) for p in M_], mu_, [float(u) for u in kn_], False, int(c_.Degree))" in _swU and "if c_.isRational(): return \"a rational B-spline" in _swU
          and _swU.index("_avg = _self_averaged(_e0s, A, B)") < _swU.index("_er = redraw(0.5 * (rs(S) + rs(Rf)), A, B, recs[k], apex=_apx, form=_fk)")
          and "averaged with its mirror at the POLE LEVEL" in _spT,
          "31bw j (TB7c F5): an own-twin chain is averaged with its mirror at the POLE level (exact; a grown cubic's fold kept) - the sampled form only where no pole-level form exists, and only when it moves the line off itself less than its asymmetry (else kept, said)")
    check("SHORT for a blend: a member with a FREE end needs 2.5 t of line for its run-out" in _swU and "is NO CORNER - skin-build refuses the chain there" in _swU and 'on this member (not swept), or R under %.2f on the chain' in _swU,
          "31bw m / 31bx K35: the room line's short-member sentence says what the build does (the cap at a free end, full R between chain junctions, the refusal at a junction that is no corner) and the ways out")
    _Pj = _npV.array([[-5.0, 0.0, 0.0], [1.02, -3.0, 0.0], [-1.0, -3.0, 0.0], [5.0, 0.0, 0.0]]); _Qj = _Pj.copy(); _Qj[:, 0] = -_Qj[:, 0]; _Mj = 0.5 * (_Pj + _Qj[::-1])
    check(abs(_Mj[1][0] - 1.01) < 1e-9 and abs(_Mj[2][0] + 1.01) < 1e-9 and _Mj[1][0] > 0 > _Mj[2][0] and _npV.allclose(_Mj, 0.5 * (_Mj + (_Mj * [-1, 1, 1])[::-1])),
          "31bw j: the pole-level average of a folded cubic with its reversed mirror keeps the fold (the inner poles stay crossed, x +1.01 / -1.01) and is exactly symmetric")
    _swV = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "sk_wires.py"), encoding="utf-8").read()
    _gV = {"np": _npV, "HAIRPIN_FOUND": [{"chain": 7, "apex": [10.0, 0.0, 0.0]}, {"chain": 7, "apex": [0.2, 0.0, 0.0]}, {"chain": 8, "apex": [5.0, 0.0, 0.0]}]}
    for _fnV in ("_apex_legs",):
        _nV = next(n for n in _astV.walk(_astV.parse(_swV)) if isinstance(n, _astV.FunctionDef) and n.name == _fnV); exec(_twV.dedent(_astV.get_source_segment(_swV, _nV)), _gV)
    _SV = _npV.vstack([_npV.column_stack([_npV.linspace(0, 10, 101), _npV.zeros(101), _npV.zeros(101)]), _npV.column_stack([_npV.linspace(10, 0, 101)[1:], _npV.linspace(0, 1.0, 101)[1:], _npV.zeros(100)])])
    _legsV = _gV["_apex_legs"](7, _SV); _legs8 = _gV["_apex_legs"](8, _SV); _legs9 = _gV["_apex_legs"](9, _SV)
    check(_legsV == [100] and _legs8 == [50] and _legs9 == [], "31bw A5b: _apex_legs finds the apex sample of a V (index %s of 201; the apex 0.2 mm from the end is the end; chain 8's own apex %s; a chain with no entry none)" % (_legsV, _legs8))
    check("def _fit_open(k, S, strict, rec, prs, p, q, L, tl, ta_, tc, mp_, grow):" in _swV and "legs_ = _apex_legs(k, S) if strict < 2 else []" in _swV and 'rung = "V(%s)" % "+".join' in _swV
          and 'rec["legs"] = legrecs_; rec["apex"]' in _swV and "HAIRPIN at a split's end - %s (31bw A5b)" in _swV and 'r["rung"] if r.get("legs") else final_kind(e_)' in _swV
          and '"V": (200, 255, 255)' in _swV and 'if rung_.startswith("V(") and len(M_) >= 6:' in _swV and "_SIMPLIFIED = True      # 31bw A5b" in _swV
          and "DRAWN PER LEG at that end (31bw A5b" in _sp5 and "## L157." in open(os.path.join(os.path.dirname(HERE), "BURRITO_STEPS.md"), encoding="utf-8").read()
          and "since 31bw A5b the wires draw that chain PER LEG" in open(os.path.join(os.path.dirname(HERE), "EDIT_TYPES.md"), encoding="utf-8").read(),
          "31bw A5b: the per-leg draw (the fit extracted, the legs joined at the apex, the V rung kept and coloured, the twin redrawn per leg, the late find said), the page, L157, the card")
    # 31bw K34  released
    _stK = KR.restart_state(_fA2); _stK["spots"] = [{"id": 5, "box": [22.0, 26.0, -121.85, -117.85, 77.28, 81.28], "tries": ["d10", "d11", "d12"], "locked": True, "locked_at": "2026-10-29 09:44:47"}]; KR._restart_save(_fA2, _stK)
    rcK0 = _runA2("restore", "--job", _jobA2, "--tag", "sA")
    check(rcK0 == 2 and "--release-spots" in "\n".join(_outA2) and "the points are owed at spot(s) [5]" in "\n".join(_outA2), "31bw K34: a restore under a later build's spot lock is refused naming --release-spots")
    rcK1 = _runA2("restore", "--job", _jobA2, "--tag", "sA", "--release-spots", "short")
    check(rcK1 == 2 and "twelve characters" in "\n".join(_outA2), "31bw K34: a short reason is refused")
    rcK2 = _runA2("restore", "--job", _jobA2, "--tag", "sA", "--release-spots", "the K34 pin: back to state sA on purpose, the d12 locks belong to a later build")
    _stK2 = KR.restart_state(_fA2); _hK = [h for h in _stK2.get("history", []) if "31bw K34" in str(h.get("why", ""))]
    check(rcK2 == 0 and not [sp for sp in _stK2.get("spots", []) if sp.get("locked")] and _hK and _hK[-1].get("spot") == 5 and "RELEASED on your word" in "\n".join(_outA2),
          "31bw K34: --release-spots releases the lock into the history with the reason and the restore goes on (rc %s)" % rcK2)
    _lk31 = os.path.join(_rvA2, "LAYOUT_LOOK.json"); _f31a = os.path.join(_rvA2, "LAYOUT_01_orbit_000.png"); _f31b = os.path.join(_rvA2, "LAYOUT_02_orbit_090.png")
    _wA2(_f31a, b"\x89PNG K31a"); _wA2(_f31b, b"\x89PNG K31b"); _tmA2.sleep(0.05)
    _wA2(_lk31, _jsA2.dumps({"frames": ["LAYOUT_01_orbit_000.png", "LAYOUT_02_orbit_090.png"], "md5": _mdA2(_pjA), "tag": "k31", "pics": "full"}))
    try: os.remove(os.path.join(_rvA2, "LAYOUT_JUDGED.json"))
    except OSError: pass
    with open(os.path.join(_lgA2.records_root(_rootA2), ".claude", "looks.jsonl"), "a") as fh: fh.write(_jsA2.dumps({"png": _f31a, "png_n": _normA2(_f31a), "opened": _tmA2.time() + 2, "when": "now", "box": None, "defective": False}) + "\n")
    rc31a = _runA2("judge", "--job", _jobA2, "--what", "layout", "--verdict", "ok", "--note", "K31 pin: the layout judged ok with its second frame never opened - must be refused")
    check(rc31a == 2 and "were never opened since they were drawn" in "\n".join(_outA2) and "LAYOUT_02_orbit_090.png" in "\n".join(_outA2), "31bw K31: a layout OK with one frame never opened is refused, the frame named")
    with open(os.path.join(_lgA2.records_root(_rootA2), ".claude", "looks.jsonl"), "a") as fh: fh.write(_jsA2.dumps({"png": _f31b, "png_n": _normA2(_f31b), "opened": _tmA2.time() + 2, "when": "now", "box": None, "defective": False}) + "\n")
    rc31b = _runA2("judge", "--job", _jobA2, "--what", "layout", "--verdict", "ok", "--note", "K31 pin: the layout judged ok with both frames opened - past the opened check")
    check("were never opened" not in "\n".join(_outA2), "31bw K31: with every frame opened the ok passes the opened check (rc %s: %s)" % (rc31b, "\n".join(_outA2)[-120:].replace("\n", " | ")))
    _lj31 = os.path.join(_lgA2.records_root(_rootA2), ".claude", "looks.jsonl"); _ljd31 = os.path.join(_rvA2, "LAYOUT_JUDGED.json")
    _ljb31 = open(_ljd31, "rb").read() if os.path.isfile(_ljd31) else None; os.replace(_lj31, _lj31 + ".31cb")
    try:
        if _ljb31 is not None: os.remove(_ljd31)
        rc31c = _runA2("judge", "--job", _jobA2, "--what", "layout", "--verdict", "ok", "--note", "31cb H-F3 pin: the layout judged ok in a project that never opened a picture - must be refused")
        _o31c = "\n".join(_outA2)
        check(rc31c == 2 and "2 of the 2 frames were never opened since they were drawn" in _o31c and "LAYOUT_01_orbit_000.png" in _o31c and "LAYOUT_02_orbit_090.png" in _o31c and not os.path.isfile(_ljd31),
              "31cb H-F3: with NO looks.jsonl (no picture ever opened) a layout OK is refused, every frame named as never opened, nothing recorded (rc %s: %s)" % (rc31c, _o31c[-160:].replace("\n", " | ")))
    finally:
        os.replace(_lj31 + ".31cb", _lj31)
        if _ljb31 is not None: open(_ljd31, "wb").write(_ljb31)
except Exception as _exA2: check(False, "the 31br A2 pins raised %r" % (_exA2,))
try:
    import ast as _astK, textwrap as _twK
    _slk = open(os.path.join(HERE, "rebuild", "sk_look.py"), encoding="utf-8").read()
    check("31bs K28 (2026-11-03" in _slk and "UNSEEN.append(fi)" in _slk and "NO iso frame of it: it is NOT recorded as looked at" in _slk, "31bs K28: the targeted look SAYS a face it cannot draw (not valid / over LOOK_TOL_MAX / no triangle) and counts it UNSEEN")
    check("_seenF = sorted(set(FACES) - set(UNSEEN))" in _slk and '"faces_unseen": (list(UNSEEN) if FACES else [])' in _slk and "| set(FACES))" not in _slk, "31bs K28: FACES_LOOKED.json takes the SEEN faces only and the look record carries faces_unseen")
    _swk = open(os.path.join(HERE, "rebuild", "sk_wires.py"), encoding="utf-8").read()
    check('for _r in FIL_RECS: _r["sharp_ok"] = int(_r.get("line")) in _sok_lines' not in _swk and "31bs K29 (2026-11-03): each record" in _swk, "31bs K29: the re-keying of sharp_ok from the raw LINES file by line number is gone; the summary reads the records")
    check(_swk.count('"sharp_ok": _sok_of(f_,') == 4 and 'bool(f_.get("sharp_ok"))' not in _swk and '_sk9 = {}' in _swk, "31bs K29: the four record sites decide sharp_ok through _sok_of (the twin with its master)")
    _fnK = next(n for n in _astK.walk(_astK.parse(_swk)) if isinstance(n, _astK.FunctionDef) and n.name == "_sok_of")
    _gK = {}; exec(_twK.dedent(_astK.get_source_segment(_swk, _fnK)), _gK); _sok = _gK["_sok_of"]
    check(_sok({"sharp_ok": True}, 36) and _sok({"sharp_ok": True}, 91, 36) and _sok({"sharp_ok": [36]}, 36) and _sok({"sharp_ok": [36]}, 91, 36) and not _sok({"sharp_ok": [36]}, 50)
          and not _sok({"sharp_ok": [36]}, 50, 53) and not _sok({}, 36) and not _sok({"sharp_ok": []}, 36),
          "31bs K29: _sok_of - True on the entry accepts its line AND its kit-mirrored twin; a list names the members and a twin is accepted when its master is; else False")
    check("_seam = bool(_e.isSeam(_f))" in _slk and "(2 if _seam else 1)" in _slk, "31bt TJ1 F1: a periodic face's seam edge counts for both its sides - never a free edge (a bore had drawn two free-edge frames on a closed plate)")
    check("its iso views are taken along its axis" in _slk and _slk.count("UNSEEN.append(fi)") == 1 and "no face of the piece can be meshed" in _slk and '"band": bool(band_)' in _slk, "31bs T3 F1 / 31bt band: a zero-normal face (a hole's bore) is DRAWN along its axis and recorded like any face - never UNSEEN; no meshable face is a plain refusal")
    _slb = open(os.path.join(HERE, "rebuild", "sk_lib.py"), encoding="utf-8").read(); _sbd = open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read()
    check("_PICS_DEL = set()" in _slb and "disk.update(_PICS_REC)" in _slb and "_PICS_DEL.add(f_)" in _slb, "31bu T3 F4: the picture record is saved by merging with the file on disk (this run's records and removals) - never an empty map over another step's")
    check('re.match(r"^F(?:S|C|M|V|\\d)", str(r.get("sub") or "")) or r.get("fillet_name")' in _sbd and 'startswith("F"): return "fillet"' not in _sbd, "31bu A3e: a blend is F<n> / FS / FC / FM / FV or a fillet_name - a split face's sixth piece (the bare F) is no blend")
    check("def _kind(f_):" in _slk and _slk.count("rg or _kind(f)") == 5 and 'rg or "curved"' not in _slk, "31bu TJ1: a face with no rung is named by its surface kind, not curved")
    check(_swk.count('["sharp_ok"] = _sok_of(') == 6 and "_sok_of(f_, int(k2), k_)" in _swk and "FIL_RECS[_mb9 + i_][\"sharp_ok\"] = _sok_of(f_, ks_[i_], int(k2))" in _swk and 'FIL_RECS[-1]["sharp_ok"] = _sok_of(f_, k0, k2); FIL_RECS.append(' in _swk, "31bs T4 F1 / 31bt / TJ4 F3: each place that gives a twin its master re-decides the twin's sharp_ok with that master, and wherever the KIT makes the pair (a self-mirror chain, a mirrored chain, a mirrored line) the master's with its twin - a list naming either number accepts both")
    import ast as _astH
    _gH = {"np": np, "HAIRPIN_DEG": 120.0, "HAIRPIN_MM": 1.0, "HAIRPIN_NEAR": 3.0, "CH": [{"pair": [0, 1]}, {"pair": [0, 2]}], "FREC": [{"kind": "net"}, {"kind": "net"}], "_HP_RAW": {}}
    for _n in _astH.parse(_swk).body:
        if isinstance(_n, _astH.FunctionDef) and _n.name in ("_hp_turn", "_hp_near"): exec(_astH.get_source_segment(_swk, _n), _gH)
    _tH = np.linspace(0, 1, 101); _tn = 5 * np.tan(np.radians(10))
    _V = np.vstack([np.stack([-5 + 5 * _tH, (1 - _tH) * _tn, 0 * _tH], 1), np.stack([-5 * _tH, -_tH * _tn, 0 * _tH], 1)[1:]])
    _A = np.stack([3 * np.cos(np.radians(60 + 60 * _tH)), 3 * np.sin(np.radians(60 + 60 * _tH)), 0 * _tH], 1)
    _L = np.stack([-5 + 10 * _tH, 0 * _tH, 0 * _tH], 1)
    _gH["_HP_RAW"] = {0: _V, 1: _A}
    _tv = _gH["_hp_turn"](_V, 100, 1.0); _ta = _gH["_hp_turn"](_A, 50, 1.0); _tl = _gH["_hp_turn"](_L, 50, 1.0); _te = _gH["_hp_turn"](_V, 2, 1.0)
    check(_tv is not None and 150 < _tv < 170 and _ta is not None and 10 < _ta < 30 and _tl is not None and _tl < 1 and _te is None, "31bu A5: the chord turn - 160 deg at a 20 deg V's apex, 19 deg on an arc of radius 3, 0 on a line, None inside a chain's end (%s / %s / %s / %s)" % (_tv, _ta, _tl, _te))
    _h1 = _gH["_hp_near"](np.array([0.3, 0.2, 0.0]), 0, 1.0); _h2 = _gH["_hp_near"](np.array([0.0, 3.0, 0.0]), 0, 1.0); _h3 = _gH["_hp_near"](np.array([0.0, 0.0, 0.0]), 2, 1.0); _h4 = _gH["_hp_near"](np.array([-3.5, 0.62, 0.0]), 0, 1.0); _h5 = _gH["_hp_near"](np.array([-2.5, 0.44, 0.0]), 0, 1.0)
    check(_h1 is not None and _h1[0] == 0 and _h1[2] > 150 and _h1[3] < 0.5 and _h2 is None and _h3 is None and _h4 is None and _h5 is not None and 2.4 < _h5[3] < 2.6, "31bu A5: _hp_near - the apex found 0.4 mm from an end beside it on the V's chain and 2.5 mm from an end down a leg; none at the arc's middle (19 deg), none for a face the V does not border, none 3.5 mm down a leg (beyond HAIRPIN_NEAR)")
    # MORE THAN ONE WAY
    import types as _tyA
    from scipy.spatial import cKDTree as _ckA
    _sbA = open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read(); _saidA = []
    class _EdA:
        Length = 1.0; FirstParameter = 0.0; LastParameter = 1.0
        def valueAt(self, t): return _tyA.SimpleNamespace(x=float(t), y=0.0, z=0.0)
        def discretize(self, Number=3): return [_tyA.SimpleNamespace(x=i / float(Number - 1), y=0.0, z=0.0) for i in range(Number)]
    class _FcA:
        Edges = [_EdA()]; Vertexes = [_tyA.SimpleNamespace(X=0.0, Y=0.0, Z=0.0), _tyA.SimpleNamespace(X=1.0, Y=0.0, Z=1.0)]
    _KA = _tyA.SimpleNamespace(WIN=(-10.0, 10.0, 0.0, 20.0, -10.0, 10.0), wall_of=lambda P: (2, 0.0))
    _gA = {"np": np, "K": _KA, "cKDTree": _ckA, "say": lambda *a: _saidA.append(" ".join(str(x) for x in a)), "BODY_E": {5: (7, 0, 0)}, "BFc": [_FcA()],
           "Vu": np.array([[0, 0, 0], [1, 0, 0], [0, 0.2, 1], [0, 10, 0], [0, 10, 2], [2, 10, 0]], float), "F": np.array([[0, 1, 2], [3, 4, 5]]), "pid": np.array([7, 7]),
           "walls": [(np.array([1.0, 0, 0]), -10.0), (np.array([-1.0, 0, 0]), -10.0), (np.array([0, 1.0, 0]), 0.0), (np.array([0, -1.0, 0]), -20.0), (np.array([0, 0, 1.0]), -10.0), (np.array([0, 0, -1.0]), -10.0)]}
    for _n in _astH.parse(_sbA).body:
        if isinstance(_n, _astH.FunctionDef) and _n.name in ("_a6_dir", "_a6_wall_name", "_a6_say"): exec(_astH.get_source_segment(_sbA, _n), _gA)
        if isinstance(_n, _astH.Assign) and any(getattr(_t, "id", "") in ("A6_WALL_MM", "A6_TOUCH_MM", "A6_SAID") for _t in _n.targets): exec(_astH.get_source_segment(_sbA, _n), _gA)
    _rA = _gA["_a6_say"](7); _gA["_a6_say"](8)
    check(len(_saidA) == 1 and _rA == _saidA[0] and "face 7 AT THE WALL" in _rA and "its 2 triangles face +y" in _rA and "MORE THAN ONE WAY" in _rA and "wall y 0.00, a 1.0 mm stretch: the body's own surface there faces -y" in _rA and "(1 triangle(s) with an edge on it)" in _rA and "nv_ >= 2" in _sbA and "A FLIP" in _rA and _gA["A6_SAID"].get(7) == _rA and 8 not in _gA["A6_SAID"],
          "31bu A6: the SPAN FAILED face owning a wall edge says the stretch's facing from the triangle with an EDGE on it (-y), the face's dominant facing (+y), the cone over 90 (more than one way) and the flip, kept in A6_SAID; a face owning no wall edge says nothing (%s)" % (_saidA[:1],))
    check(_sbA.count("; _a6_say(pi)") == 1 and _sbA.count("_a6_say(i)") == 2 and "AT THE WALL TOO (31bu A6" in open(os.path.join(HERE, "rebuild", "STEP_PAGES.md"), encoding="utf-8").read(), "31bu A6: the line follows the three SPAN FAILED sites; the page's piece rule names the facing at the wall")
    check('r"AT THE WALL|SPAN FAILED|' in _swk and '(4000 if "AT THE WALL" in _ln9 else 420)' in _swk and '"at_the_wall": A6_SAID.get(int(pi_))' in _sbA, "31bu A6 (TK3 F2): the preview child's AT THE WALL line passes sk_wires' filter whole and preflight.json keeps it with the face")
    check("_hp_refuse(P_, q, ai_, nm_, mirrored, ADD_SNAP)" in _swk and "role_=str(a_.get(\"role\", \"\")).lower(), ai_=ai_, nm_=\"from\"" in _swk and "LINES_NET == NET_MD5:" in _swk and '"hairpin_ends": HAIRPIN_FOUND' in _swk and '"HAIRPIN_DEG", "HAIRPIN_MM")' in open(os.path.join(HERE, "kit_rebuild.py"), encoding="utf-8").read(), "31bu A5: the early check on this numbering's file, the belt in _end_pt for a split's [x, y, z] end, the record in WIRES_LOOK, the levers registered")
    check("HAIRPIN at a split's end - %s (31bw A5b)" in _swk and "HAIRPIN_OK" not in _swk and 'K._fail("FAIL: " + msg_)' not in _swk and "a split's end lies at a HAIRPIN apex of this face's border (said at the read" in _swk and "HAIRPIN_OK" not in open(os.path.join(HERE, "rebuild", "STEP_PAGES.md"), encoding="utf-8").read(), "31bu A5 (TK3 F1): the hairpin is SAID at the read, never refused (the agent's d15 riser split at a 173 deg apex built); the preview's verdict names it for a face it fails; no HAIRPIN_OK anywhere")
except Exception as _exK: check(False, "the 31bs skin5 pins raised %r" % (_exK,))
print("\n[31bx round 1] the skin route's fixes (FIX_LEDGER_31bx X59 X75 X76 X77 X78 X79 X81 X82 X84 X85 X86 X87 X88 X90 X91 X96)")
try:
    _rd5 = lambda *p: open(os.path.join(os.path.dirname(os.path.abspath(__file__)), *p), encoding="utf-8").read()
    _kr5 = _rd5("kit_rebuild.py"); _sw5 = _rd5("rebuild", "sk_wires.py"); _sb5 = _rd5("rebuild", "sk_build.py"); _ri5 = _rd5("rebuild", "rb_reinsert.py"); _rb5 = _rd5("rebuild", "rb_review_body.py")
    check("env[k],      # 31bx (R1 F2)" in _kr5 and 'env[k][:87] + "..."' not in _kr5, "31bx R1 F2: --plan prints a lever's value whole")
    check('what in ("region", "layout", "wires", "skin", "trial")' in _kr5, "31bx R5 F1: the region judge's ok is held to the every-frame-opened check")
    check('"sharp_ok": bool(k_ in _sok_pf)' in _sb5 and 'stands SHARP by your sharp_ok (31bx X76) - not swept' in _sb5 and 'FIL_RERUN = sorted(set(list(FILLET_LINES) + fil_failed + _sok_k))' in _sb5 and "FILLETS = [f_ for f_ in FILLETS if not f_.get(\"sharp_ok\")]" not in _sb5
          and '_sok_pre = sorted(' in _sw5 and 'and not r_.get("sharp_ok")))      # 31bx (R5 F2)' not in _sw5 and 'preflight_child.txt' in _sw5 and 'fillet chain \\d+: junction' in _sw5 and "NOT swept: they stand sharp on purpose" in _sw5,
          "31bx X76 (R5 F2): a sharp_ok line stays in its chain - never swept, recorded NOT MADE by the agent's word so its chain-mates' ends are freed; the kernel never tries it; the preview child takes it with the others and lists it apart; the junction lines pass the filter and the child's whole log is kept")
    check("this end was FREED because its chain-mate at the junction was not made or the two offsets do not meet there" in _sb5, "31bx R5 F3: the open-end refusal says why the end was freed and that a smaller R can free one")
    check('if rc == 0: say("  next    : %s" % nxt)' in _kr5 and "the step did not finish (rc %s)" in _kr5 and "no pictures - NET_PICS=0" in _kr5 and "THIS RUN DREW THE QUICK SET" in _kr5, "31bx R5 F4 / R6 D7: the next line only after a step that ran, reads NET_PICS, names PICS=full on a quick run")
    check('_inv9 = list(PREVIEW.get("faces_invalid") or [])' in _sw5 and "or _nm9 or _inv9) else \"fail\"" in _sw5 and 'list(_pf.get("faces_invalid") or []))' in _kr5, "31bx R6 F1: faces built but NOT VALID fail the preview's verdict and the judge")
    check('rec["dec_set_aside"] = "a CLOSED chain takes no LINE / ARC / CUBIC decision' in _sw5 and "made again tighter after a crossing (strict %d): the decision %s is set aside" in _sw5 and "decision(s) SET ASIDE (said above" in _sw5, "31bx R6 F2: a decision set aside (a closed chain, a crossing re-make) is said per chain and counted in the DECIDED line")
    check('("region", "ok"): "kit rebuild skin-source' in _kr5 and '("wires", "ok"): "kit rebuild skin-build' in _kr5 and 'say("  next    : %s" % (_nxj % job))' in _kr5, "31bx R6 F5: the judge's next lines per what and verdict")
    check("names no file in any of the places a relative path is read from" in _kr5 and 'for k_ in ("FEATURES", "LINES", "RAILS", "STL", "BODY", "NEW", "PIECE", "SHAPE")' not in _kr5 and 'k_ in ("FEATURES", "LINES", "RAILS", "STL", "BODY", "NEW", "PIECE", "SHAPE")' in _kr5, "31bx R6 F6: a relative file lever is resolved against the cwd, the root, claude_code, the job folder - or refused by name")
    check('"skin-features": "layout",      # 31bx (R6 F9)' in _kr5 and "the same map as the judged layout's (skin\\\\features.json)" in _kr5, "31bx R6 F9: skin-features over a judged layout is refused unless its map is the judged one's")
    check("the BOP gate lines above name what is NOT a cosmetic here" in _ri5 and "lay on a body face and moved 0.5 mm outward" in _ri5 and "a box plane on a body face (STEP 1 moves one outward since 31bx R6 F8" in _ri5 and "a TRIAL's STEP 3 writes it too" in _ri5, "31bx R6 F7 / F8 / F11: the BOP FAIL names the non-cosmetic, a local-box plane on a body face moves outward, STEP 3's line and need() say the cause")
    check("lie outside the bodies" in _rb5, "31bx R6 F11: review-body's stations stay inside the bodies")
    _pg = KR.step_page("region"); _pg2 = KR.step_page("skin-points")
    check("THE REGION ROW 1 (BURRITO_STEPS.md, THE SKIN ROUTE - no page of its own)" in _pg and "content.brep" in _pg and "THE SKIN-POINTS PAGE" in _pg2, "31bx R6 D1: a step with no page prints its row of THE SKIN ROUTE table; a step with a page keeps it")
    check("judge it - kit rebuild judge --what look --verdict ok|redo|move" in _kr5 and "The front half is the REGION step and skin-source" in _kr5, "31bx R6 F11: skin-look's next names the judge; the help's voxel sentence is right")
    check("are NO CORNER - the crease runs through a face boundary on the far side turning under CREASE_TURN_MAX" in _sb5 and 'if record and _nc_ == "nocorner":' in _sb5 and 'if kind_ != "chain" or not (turn_ < turn_max_): return None' in _sb5 and "def _turn_at(Ja_):" in _sb5
          and "def _straight_at(" not in _sb5 and "STRAIGHT_DEG" not in _sb5 and "THE REACH TO X" not in _sb5 and 'mx_["chain_c"][str(ex_)]["extend"] = float(min(sh_x * 1.25 + 0.1' in _sb5 and '"STRAIGHT_DEG"' not in _kr5
          and "is NO CORNER - skin-build refuses the chain there" in _sw5 and "is NO CORNER: skin-build refuses a chain across it by name" in _sp5,
          "31bx K35 (the client 11-06): no corner form where no corner is - a far-side face boundary the crease runs through (under CREASE_TURN_MAX, kind chain) refuses the chain by name with the two ways out; a split's apex is the agent's junction; edit n's reach-to-X and edit l's STRAIGHT rule are gone; the room line, the page and the card say it")
    check("LIMITS 3 (31bx K35): a crease you will FILLET must be ONE line between corners" in _sp5 and "as ONE feature, one line and one blend - the preview PASSES" in _sp5,
          "31bx K35 (q): the features page's LIMITS 3 says the one-crease rule where the layout is decided (measured on the stem foot: one feature, one line, one blend - PASS)")
except Exception as _e5:
    check(False, "31bx round 1 pins ran (%s)" % str(_e5)[:160])
try:
    _fz = tempfile.mkdtemp(prefix="sk5_31bz_"); os.makedirs(os.path.join(_fz, "skin", "review"))
    open(os.path.join(_fz, "BUILD_LOG.md"), "w").write("# BUILD LOG\n\n| when | tag | step | levers | the line | rc | s |\n|---|---|---|---|---|---|---|\n| 2026-11-06 12:00:00 | f2 | skin-wires | PREFLIGHT=1 | PREVIEW VERDICT - THE BUILD WOULD FAIL | 0 | 85 |\n")
    _okz = {"what": "layout", "verdict": "ok", "md5": "x", "when": "2026-11-06 11:59:00"}
    _pfz = os.path.join(_fz, "skin", "preflight.json")
    json.dump({"tag": "f2", "verdict": "fail", "span_failed": [], "pieces_failed": [], "faces_invalid": [{"patch": 5, "sub": None}]}, open(_pfz, "w"))
    _tz = time.mktime(time.strptime("2026-11-06 12:01:00", "%Y-%m-%d %H:%M:%S")); os.utime(_pfz, (_tz, _tz))
    _f1 = KR.downstream_failure_since(_fz, "layout", _okz)
    check(bool(_f1) and _f1["step"] == "skin-wires (the preview)" and _f1["rc"] == "preview" and "built NOT VALID [5]" in _f1["line"], "31bz R6 F1: a FAILED preview newer than the layout's ok overturns it (rc 0 in the BUILD_LOG) - the line names the invalid face (%s)" % (_f1 and _f1["line"]))
    _t0 = time.mktime(time.strptime("2026-11-06 11:58:00", "%Y-%m-%d %H:%M:%S")); os.utime(_pfz, (_t0, _t0))
    check(KR.downstream_failure_since(_fz, "layout", _okz) is None, "31bz R6 F1: a failed preview OLDER than the ok overturns nothing")
    json.dump({"tag": "f2", "verdict": "pass"}, open(_pfz, "w")); os.utime(_pfz, (_tz, _tz))
    check(KR.downstream_failure_since(_fz, "layout", _okz) is None, "31bz R6 F1: a PASSING preview overturns nothing")
    json.dump({"tag": "f2", "verdict": "fail", "span_failed": [3]}, open(_pfz, "w")); os.utime(_pfz, (_tz, _tz))
    check(KR.downstream_failure_since(_fz, "wires", {"what": "wires", "verdict": "ok", "when": "2026-11-06 11:59:00"}) is None, "31bz R6 F1: the preview's record overturns the LAYOUT's ok only (the wires' own judge reads it already)")
    shutil.rmtree(_fz, ignore_errors=True)
    _sbz = _rd5("rebuild", "sk_build.py"); _swz = _rd5("rebuild", "sk_wires.py"); _spz = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "STEP_PAGES.md"), encoding="utf-8").read()
    check("does not clear such a junction" not in _sbz and "does not clear it" not in _swz and "does not clear it" not in _spz and "or accept the member that lies between the no-corner junctions sharp" in _sbz
          and "or accept the member that lies between the no-corner junctions sharp" in _swz and "or accept the member that lies between the no-corner junctions sharp" in _spz,
          "31bz R5 F1 -> 31ca: the NO CORNER message, the room line and the page offer sharp_ok again - the gate skips a junction whose member is sharp_ok (31ca: the NO CORNER message, the room line and the page offer sharp_ok again)")
except Exception as _ez:
    check(False, "31bz pins ran (%s)" % str(_ez)[:160])
print("\n[31ca] the NO CORNER gate skips a junction whose member is sharp_ok (R5 F1)")
try:
    _sb6 = _rd5("rebuild", "sk_build.py")
    _blk6 = _sb6.split("# >>> 31ca R5 F1 THE NO CORNER DECISION\n", 1)[1].split("# <<< 31ca R5 F1 THE NO CORNER DECISION", 1)[0]
    _ns6 = {}; exec(_blk6, _ns6); _nca = _ns6["_nocorner_at"]
    _J6 = [(55, 74, 8.0, "chain"), (74, 77, 8.0, "chain")]
    _r_ok = [_nca(a_, b_, t_, k_, {74}, 45.0) for a_, b_, t_, k_ in _J6]; _r_no = [_nca(a_, b_, t_, k_, set(), 45.0) for a_, b_, t_, k_ in _J6]
    check(_r_ok == ["sharp_ok", "sharp_ok"] and "nocorner" not in _r_ok, "31ca R5 F1: \"sharp_ok\": [74] on the middle member - both junctions skipped (said), no NO CORNER refusal: %s" % _r_ok)
    check(_r_no == ["nocorner", "nocorner"], "31ca R5 F1: ...without sharp_ok - both junctions NO CORNER, the chain refused: %s" % _r_no)
    check(_nca(55, 74, 8.0, "split", set(), 45.0) is None and _nca(55, 74, 80.0, "chain", set(), 45.0) is None and _nca(55, 74, 8.0, "chain", {55}, 45.0) == "sharp_ok",
          "31ca R5 F1: ...a split's apex and a real corner (80 deg) are no NO CORNER; either member sharp_ok skips the junction")
    check("_nc_ = _nocorner_at(k_, int(mem[partner[0]][\"line\"]), _turnJ, kind_c, _sok_nc, CREASE_TURN_MAX)" in _sb6 and 'if record and _nc_ == "nocorner":' in _sb6
          and "stands SHARP by your sharp_ok, so no corner form is needed: its chain-mates taper to it (31ca R5 F1" in _sb6 and "(31bx K35; sharp_ok" not in _sb6
          and "the crease turns %s deg at them, per member end - 31bx K35" in _sb6, "31ca R5 F1: _chain_members calls the decision, refuses only 'nocorner', says the skipped junction; the chain's line still says every junction's turn")
except Exception as _e6:
    check(False, "31ca R5 F1 pins ran (%s)" % str(_e6)[:160])
print("\n[31ca] the step pages: the short names, second, restore (R7 D4)")
try:
    _p_pts = KR.step_page("points"); _p_sec = KR.step_page("second"); _p_rst = KR.step_page("restore"); _p_lay = KR.step_page("layout"); _p_no = KR.step_page("nosuch")
    check(_p_pts.startswith("  page    : THE SKIN-POINTS PAGE") and KR.step_page("wires").startswith("  page    : THE SKIN-WIRES PAGE") and "THE SKIN-RIM ROW" in KR.step_page("rim"),
          "31ca R7 D4: a short name is its skin step's - points / wires their pages, rim its route-table row")
    check("no page of its own - the route table's row:" in _p_sec and "second --what skin" in _p_sec, "31ca R7 D4: `second` - the route table's row whose command names it (the second review): %s" % _p_sec[:160])
    check("no page of its own - the route table's row:" in _p_rst and "| 15 | skin-build |" in _p_rst, "31ca R7 D4: `restore` - the skin-build row, where the row's what names `kit rebuild restore`: %s" % _p_rst[:160])
    check("skin-layout" in _p_lay and _p_lay != "", "31ca R7 D4: `layout` -> skin-layout's row")
    _nm = KR.step_names()
    check(_p_no == "" and all(x in _nm for x in ("points", "skin-points", "second", "restore", "layout", "lines", "judge", "reinsert", "review-body", "region")),
          "31ca R7 D4: an unknown name has no page and step_names lists every name taken (kit howto prints them)")
    check("the names it takes: %s" in _rd5("kit.py") and "_krp.step_names(HERE)" in _rd5("kit.py"), "31ca R7 D4: kit howto burrito --step <unknown> lists the names it takes")
except Exception as _e7:
    check(False, "31ca R7 D4 pins ran (%s)" % str(_e7)[:160])
print("%d passed, %d FAILED" % (ok, bad))
sys.exit(1 if bad else 0)

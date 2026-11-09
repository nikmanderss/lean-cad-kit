"""selftest_skin2.py - kit 31an (2026-10-07, the client's answers on R4 skin 1), without a kernel.
the client: "Remember the process worked as I had it, it was only missing focus on simplifying the geometry instead of following the voxel
improvements so closely ... it is just direction to the agent and its sub agents that need refinement."
Cases: the mirror plane (any plane), the window's own symmetry, the layout made on one side and mirrored (a strip missing on one side
comes back as the mirror of the other's, a face spanning the plane stays one), the face ladder's rung 1 (orig) and the twin rule, the
flat test, the two iso views; the RESTART (three failed tries lock every step after skin-points until a NEW point selection is judged),
the SECOND REVIEWER before a skin `ok` (shards, a shard that skipped frames refused, defects ranked largest first, a blocker refuses
`ok` and is a try), the suggested values and the one range that refuses, the symmetry decision kept from skin-labels, the build log's
rows and key lines, and the kill that confirms the process tree is gone."""
import os, sys, json, shutil, tempfile, hashlib, subprocess, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kit_rebuild as KR
ok = 0; bad = 0
def check(cond, what):
    global ok, bad
    if cond: ok += 1; print("  ok   " + what)
    else: bad += 1; print("  FAIL " + what)

def opened31cb(root_, *pngs):
    import leangate as lg_31cb, time as tm_31cb
    d_ = os.path.join(lg_31cb.records_root(root_), ".claude"); os.makedirs(d_, exist_ok=True)
    with open(os.path.join(d_, "looks.jsonl"), "a") as fh_:
        for p_ in pngs: fh_.write(json.dumps({"png": p_, "png_n": os.path.normcase(os.path.abspath(p_)).replace("\\", "/"), "opened": tm_31cb.time(), "when": "now", "box": None, "defective": False}) + "\n")

root = tempfile.mkdtemp(prefix="skin2_"); job = "JOB2"; folder = os.path.join(root, "claude_code", "jobs", job)
os.makedirs(os.path.join(folder, "skin", "review"))
WIN = [-6.0, 6.0, 0.0, 4.0, -1.0, 1.0]
json.dump({"window": WIN, "planes": []}, open(os.path.join(folder, "REBUILD_region.json"), "w"))
md = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()
try:
    os.environ["RUN"] = folder
    sys.path.insert(0, os.path.join(HERE, "rebuild"))
    import sk_lib as K
    n, c = K.mirror_plane("x 0"); check(np.allclose(n, [1, 0, 0]) and c == 0.0, "MIRROR \"x 0\" is the plane x = 0")
    n2, c2 = K.mirror_plane("0 2 0 4"); check(np.allclose(n2, [0, 1, 0]) and abs(c2 - 2.0) < 1e-12, "a general plane \"nx ny nz c\" is normalised (y = 2)")
    check(K.mirror_plane("") is None, "an empty MIRROR = not symmetric")
    try:
        K.mirror_plane("q 3"); check(False, "a malformed MIRROR raises")
    except ValueError:
        check(True, "a malformed MIRROR raises")
    check(np.allclose(K.reflect(np.array([[1.0, 2, 3]]), *K.mirror_plane("x 2")), [[3, 2, 3]]), "reflect across x = 2")
    check(K.window_symmetric(*K.mirror_plane("x 0"))[0] and not K.window_symmetric(*K.mirror_plane("x 2"))[0], "the window is its own mirror across x = 0, not across x = 2")
    check(not K.window_symmetric(*K.mirror_plane("x 9"))[0], "a plane outside the window is refused (both sides must be inside it)")
    flat = K.is_flat(np.random.RandomState(0).rand(80, 3) * [10, 10, 0.02])
    bump = K.is_flat(np.c_[np.random.RandomState(1).rand(80, 2) * 10, np.random.RandomState(2).rand(80) * 0.5])
    check(flat[0] and not bump[0], "the flat rung: a 0.02 mm sheet is flat, a 0.5 mm bump is not")
    dd = K.iso_dirs(np.array([0, 0, 1.0]), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]))
    ang = [np.degrees(np.arccos(-np.dot(d, [0, 0, 1]))) for d in dd]
    check(len(dd) == 2 and all(50 < a < 60 for a in ang) and not np.allclose(dd[0], dd[1]), "two iso views of a face, ~55 deg off its normal, never straight on (%s)" % np.round(ang, 1).tolist())
    vb = K.views(close=False, below=True)
    check(len(vb) == 14 and sum(1 for v in vb if v[0].startswith("below_")) == 4, "the whole-window views include four from BELOW")
    xs = np.arange(-6, 6.001, 0.5); ys = np.arange(0, 4.001, 0.5)
    V = np.array([[x, y, 0.0] for x in xs for y in ys]); ny = len(ys)
    F = []
    for i in range(len(xs) - 1):
        for j in range(ny - 1):
            a = i * ny + j; b = a + ny
            F += [[a, b, a + 1], [b, b + 1, a + 1]]
    F = np.array(F); T3 = V[F]; Cn = T3.mean(1); Nr = np.cross(T3[:, 1] - T3[:, 0], T3[:, 2] - T3[:, 0]); At = 0.5 * np.linalg.norm(Nr, axis=1); Nn = Nr / (2 * At)[:, None]
    pid = np.where(Cn[:, 0] < -3, 1, np.where(Cn[:, 0] < -1, 2, np.where(Cn[:, 0] <= 1, 3, 4)))
    new, info = K.mirror_layout(Cn, Nn, At, F, pid, np.zeros(len(F), bool), np.array([1.0, 0, 0]), 0.0, master="auto", say=lambda *a: None)
    _, mi = K.knn(Cn, K.reflect(Cn, np.array([1.0, 0, 0]), 0.0), 1)
    plus = Cn[:, 0] > 1.3
    twin_ok = all((new[t] == new[mi[t]] + K.MIRROR_OFF) or (new[t] == new[mi[t]] and new[t] == 3) for t in np.nonzero(plus)[0])
    check(info["master"] == "-" and twin_ok, "the side with more faces is the master; every + triangle carries its mirror's face (the missing strip is back as a twin)")
    check(3 in info["cross"] and (new[np.abs(Cn[:, 0]) < 0.9] == 3).all(), "a face that spans the plane stays ONE face across it")
    check(not np.isin(new, [4]).any(), "the + side's own wrong face (one face where the - side has two) is gone")
    pts_patch = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1]); pf = np.array([77, 77, 77, 77, 77, 88, 88, 88, -1]); pon = pf >= 0
    pats = [{"patch": 0, "kind": "changed"}, {"patch": 1, "kind": "changed"}, {"patch": 2, "kind": "cap"}]
    n_o = K.orig_rung(pats, pts_patch, pf, pon, 0.9, 3)
    check(n_o == 1 and pats[0]["kind"] == "orig" and pats[0]["face"] == 77 and pats[1]["kind"] == "changed" and pats[1]["face_src"] == 88,
          "rung 1: a face whose points all lie on one original face keeps it; one with an OFF point is fitted (but knows its source)")
    tw = [{"patch": 0, "kind": "orig", "grp": 5, "face": 77}, {"patch": 1, "kind": "changed", "grp": 5}]
    check(K.same_kind_groups(tw) == 1 and tw[0]["kind"] == "changed", "a face and its mirror twin are the same kind: orig only when both are")
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
    kit = Kit(root); out = []
    say = lambda *a: out.append(" ".join(str(x) for x in a))
    def run(*a):
        out.clear(); import builtins; p0 = builtins.print; builtins.print = lambda *x, **k: out.append(" ".join(str(y) for y in x))
        try: return KR.cmd(list(a), kit)
        except RuntimeError as ex: return "passed" if "GATES PASSED" in str(ex) else str(ex)
        finally: builtins.print = p0
    open(os.path.join(folder, "piece.stl"), "wb").write(b"\0" * 84); open(os.path.join(folder, "body.brep"), "wb").write(b"a body")
    open(os.path.join(folder, "wall_caps.brep"), "wb").write(b"caps")
    B = "BODY=" + os.path.join(folder, "body.brep")
    sd = KR.step_defaults("skin-build", folder, "")
    check(sd.get("LAM") == "0.5" and sd.get("VOXCHECK") == "0" and sd.get("FRAME_TOL") == "0.02" and sd.get("PLANE") == "1", "skin-build's suggestions: LAM 0.5, VOXCHECK 0, FRAME_TOL 0.02, PLANE 1")
    rc = run("skin-build", "--job", job, "--tag", "b1", "--set", B, "--set", "FRAME_TOL=0.2")
    check(rc == 2 and "outside" in " ".join(out) and "0.15" in " ".join(out), "FRAME_TOL over the 0.15 seam ceiling is refused - the one kind of refusal on a value")
    nfb = os.path.join(folder, "skin", "network_frame.brep"); open(nfb, "wb").write(b"the wireframe skin-wires drew")
    rc = run("skin-build", "--job", job, "--tag", "b1", "--set", B, "--set", "LAM=0.03")
    check(rc == 2 and "THE WIREFRAME comes before the faces" in " ".join(out), "31as: skin-build is refused until the wireframe is judged (judge --what wires)")
    for f in ("WIRE_01_orbit_000.png",): open(os.path.join(folder, "skin", "review", f), "wb").write(b"png")
    json.dump({"kind": "wires", "frames": ["WIRE_01_orbit_000.png"], "md5": md(nfb)}, open(os.path.join(folder, "skin", "review", "WIRES_LOOK.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "wires", "--verdict", "ok", "--note", "every line where its feature's edge is: spine top straight, vane edges arcs"], kit, say)
    check(rc == 2 and "NOT TAKEN" in " ".join(out) and "no measurement at all" in " ".join(out), "31bq R7c (R5j): a wires record with NO lines_against_part (drawn before OO) is NOT TAKEN - the ok refused by name")
    json.dump({"kind": "wires", "frames": ["WIRE_01_orbit_000.png"], "md5": md(nfb), "lines_against_part": {"taken": True, "worst_mm": 0.1}}, open(os.path.join(folder, "skin", "review", "WIRES_LOOK.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "wires", "--verdict", "ok", "--note", "every line where its feature's edge is: spine top straight, vane edges arcs"], kit, say)
    check(rc == 2 and "PREVIEW" in " ".join(out) and "NOT TAKEN" in " ".join(out), "31br G1 / G2: a wires record with NO preview (drawn before 31br, or PREFLIGHT=0) is NOT TAKEN - the ok refused by name")
    json.dump({"kind": "wires", "frames": ["WIRE_01_orbit_000.png"], "md5": md(nfb), "lines_against_part": {"taken": True, "worst_mm": 0.1}, "preflight": {"taken": True, "verdict": "fail", "span_failed": [4], "pieces_failed": [], "not_made_unaccepted": [36]}}, open(os.path.join(folder, "skin", "review", "WIRES_LOOK.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "wires", "--verdict", "ok", "--note", "every line where its feature's edge is: spine top straight, vane edges arcs"], kit, say)
    check(rc == 2 and "would FAIL" in " ".join(out) and "[4]" in " ".join(out) and "[36]" in " ".join(out), "31br G1 / G2: a preview that failed (a face that cannot be spanned, a fillet not made and not accepted sharp) refuses the ok, naming both")
    json.dump({"kind": "wires", "frames": ["WIRE_01_orbit_000.png"], "md5": md(nfb), "lines_against_part": {"taken": True, "worst_mm": 0.1}, "preflight": {"taken": True, "verdict": "pass", "span_failed": [], "pieces_failed": [], "not_made_unaccepted": []}}, open(os.path.join(folder, "skin", "review", "WIRES_LOOK.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "wires", "--verdict", "ok", "--note", "the crown knife edge cannot be built by the kit, left as it is"], kit, say)
    check(rc == 2 and "31br I3" in " ".join(out), "31br I3: a note that states a LIMIT with no build tag is refused (after the preview passed)")
    opened31cb(root, os.path.join(folder, "skin", "review", "WIRE_01_orbit_000.png"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "wires", "--verdict", "ok", "--note", "every line where its feature's edge is: spine top straight, vane edges arcs"], kit, say)
    check(rc == 0, "31as: the wireframe judged ok on its WIRE_* frames")
    rc = run("skin-build", "--job", job, "--tag", "b1", "--set", B, "--set", "LAM=0.03")
    check(rc == "passed" and any("suggested 0.5" in l for l in out), "any other value is the agent's: taken, printed beside the suggestion")
    _fjp = os.path.join(folder, "skin", "fillets.json")
    _rl = {k_: {"value": v_, "default": v_, "set": False} for k_, v_ in (("TAPER_X", "3"), ("TAPER_MIN", "1.0"), ("FIL_TAPER", "1"), ("THIN_MM", "0.3"), ("CREASE_MIN_DEG", "8"), ("BURIED_MIN", "0.3"), ("BURIED_REACH", "2.0"), ("FIL_SMOOTH_MM", "1.5"))}
    json.dump({"network_frame_md5": md(nfb), "tag": "w1", "fillets": [{"line": 3, "r": 1.5, "why": "a test"}], "room_levers": _rl}, open(_fjp, "w"))
    rc = run("skin-build", "--job", job, "--tag", "b1", "--set", B, "--set", "TAPER_X=1.5")
    check(rc == 2 and "THE ROOM LEVERS DIFFER" in " ".join(out) and "TAPER_X 3 where this build runs TAPER_X 1.5" in " ".join(out) and "--set TAPER_X=1.5" in " ".join(out),
          "31bq R7W (M8): a skin-build at TAPER_X 1.5 on wires whose room line used 3 is REFUSED by name, both ways out said")
    rc = run("skin-build", "--job", job, "--tag", "b1", "--set", B)
    check(rc == "passed" and any("room    :" in l and "agree" in l and "TAPER_X 3" in l and "FIL_SMOOTH_MM 1.5" in l for l in out), "31bq R7W (M8): the same levers (the build's default = the wires' recorded default) pass, said")
    rc = run("skin-build", "--job", job, "--tag", "b1", "--set", B, "--set", "FIL_SMOOTH_MM=3")
    check(rc == 2 and "THE ROOM LEVERS DIFFER" in " ".join(out) and "FIL_SMOOTH_MM 1.5 where this build runs FIL_SMOOTH_MM 3" in " ".join(out) and "--set FIL_SMOOTH_MM=3" in " ".join(out),
          "31bq R7W (fix-wires-normals): FIL_SMOOTH_MM is a room lever - a build smoothing its normals over 3 mm on wires whose room line smoothed over 1.5 is REFUSED by name, both ways out said")
    _rl["TAPER_X"] = {"value": "1.5", "default": "3", "set": True}; json.dump({"network_frame_md5": md(nfb), "tag": "w2", "fillets": [{"line": 3, "r": 1.5, "why": "a test"}], "room_levers": _rl}, open(_fjp, "w"))
    rc = run("skin-build", "--job", job, "--tag", "b1", "--set", B)
    check(rc == 2 and "TAPER_X 1.5 where this build runs TAPER_X 3" in " ".join(out), "31bq R7W (M8): wires at TAPER_X 1.5 (set there, or carried from an earlier build) and a build at its default 3 - refused")
    rc = run("skin-build", "--job", job, "--tag", "b1", "--set", B, "--set", "TAPER_X=1.50")
    check(rc == "passed", "31bq R7W (M8): ...the same value written another way (1.50) passes")
    json.dump({"network_frame_md5": md(nfb), "tag": "w0", "fillets": [{"line": 3, "r": 1.5, "why": "a test"}]}, open(_fjp, "w"))
    rc = run("skin-build", "--job", job, "--tag", "b1", "--set", B, "--set", "TAPER_X=1.5")
    check(rc == "passed" and any("room    :" in l and "NOT TAKEN" in l for l in out), "31bq R7W (M8): a record written before R7W (no room_levers) is NOT TAKEN - said, neither a pass nor a refusal")
    os.remove(_fjp)
    open(nfb, "wb").write(b"skin-frame ran again: a new frame, not the judged wireframe")
    rc = run("skin-build", "--job", job, "--tag", "b1", "--set", B)
    check(rc == 2 and "earlier" in " ".join(out), "31as: a changed network_frame.brep (skin-frame or skin-wires again) needs its wires judged again")
    json.dump({"kind": "wires", "frames": ["WIRE_01_orbit_000.png"], "md5": md(nfb), "lines_against_part": {"taken": True, "worst_mm": 0.1}, "preflight": {"taken": True, "verdict": "pass", "span_failed": [], "pieces_failed": [], "not_made_unaccepted": []}}, open(os.path.join(folder, "skin", "review", "WIRES_LOOK.json"), "w"))
    KR.judge(["--job", job, "--what", "wires", "--verdict", "ok", "--note", "the new wireframe looked at again, every line where it belongs"], kit, say)
    rc = run("skin-labels", "--job", job, "--tag", "l1", "--set", B)
    check(rc == 2 and "MIRROR" in " ".join(out), "skin-labels refuses without the symmetry decision (MIRROR, its CARD lever)")
    json.dump({"plane": "x 0", "step": "skin-labels"}, open(os.path.join(folder, "skin", "MIRROR_DECISION.json"), "w"))
    check(KR.step_defaults("skin-build", folder, "").get("MIRROR") == "x 0", "the later steps take MIRROR from skin-labels' decision")
    rc = run("skin-build", "--job", job, "--tag", "b2", "--set", B, "--set", "MIRROR=y 0")
    check(rc == 2 and "differs from the card's decision" in " ".join(out), "a later step with another plane is refused")
    A = [1.0, 2.0, 1.0, 2.0, -0.5, 0.5]; Bx = [-4.0, -3.0, 2.0, 3.0, -0.5, 0.5]
    pts = os.path.join(folder, "skin", "points1000.json")
    json.dump({"points": [[1.5, 1.5, 0, 7, 0.01, "grid"], [-3.5, 2.5, 0, 8, 0.01, "grid"], [0, 0, 0, 9, 0.01, "grid"]]}, open(pts, "w"))
    KR.record_try(folder, "layout", "md5-0", "a wavy border at A", [A], say)
    KR.record_try(folder, "layout", "md5-1", "A again", [A], say)
    KR.record_try(folder, "layout", "md5-1", "the same layout again", [A], say)
    KR.record_try(folder, "layout", "md5-1", "B once", [Bx], say)
    sp = {x["id"]: x for x in KR.restart_state(folder)["spots"]}
    check(len(sp) == 2 and sorted(len(x["tries"]) for x in sp.values()) == [1, 2] and not any(x.get("locked") for x in sp.values()),
          "tries are counted PER SPOT (A twice - the same artefact twice counts once - and B once): nothing locked")
    out.clear(); KR.record_try(folder, "skin", "md5-3", "crumpled at A", [[1.2, 1.8, 1.2, 1.8, -0.2, 0.2]], say)
    sp = sorted(KR.restart_state(folder)["spots"], key=lambda x: x["id"])
    check(sp[0].get("locked") and not sp[1].get("locked") and "BACK TO THE POINTS THERE" in " ".join(out), "the THIRD try at spot A locks spot A only (a failure inside A is A)")
    rc = run("skin-rim", "--job", job, "--tag", "r1", "--set", B)
    check(rc == 2 and "THE POINTS ARE OWED AT 1 SPOT" in " ".join(out), "while spot A is locked every step after skin-points is refused - and the refusal names A only")
    rc = run("skin-points", "--job", job, "--tag", "p1", "--set", B)
    check(rc == "passed", "skin-points itself runs (the restart IS point selection)")
    for f in ("SP7d_01_orbit_000.png",): open(os.path.join(folder, "skin", "review", f), "wb").write(b"png")
    json.dump({"kind": "points", "frames": ["SP7d_01_orbit_000.png"], "md5": md(pts)}, open(os.path.join(folder, "skin", "review", "POINTS_LOOK.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "points", "--verdict", "ok", "--note", "the same points as before, judged again without a change"], kit, say)
    check(rc == 2 and "SAME" in " ".join(out), "the SAME points inside spot A cannot unlock it")
    json.dump({"points": [[1.5, 1.5, 0, 7, 0.01, "grid"], [1.2, 1.7, 0, 11, 0.01, "box"], [-3.5, 2.5, 0, 8, 0.01, "grid+kept"], [0, 0, 0, 9, 0.01, "grid+kept"]]}, open(pts, "w"))
    json.dump({"kind": "points", "frames": ["SP7d_01_orbit_000.png"], "md5": md(pts)}, open(os.path.join(folder, "skin", "review", "POINTS_LOOK.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "points", "--verdict", "ok", "--note", "a box of points at A so the keel end's face is asked for"], kit, say)
    st_ = KR.restart_state(folder)
    check(rc == 0 and not any(x.get("locked") for x in st_["spots"]) and len(st_["spots"]) == 1 and len(st_["spots"][0]["tries"]) == 1,
          "new points INSIDE spot A unlock it; spot B keeps its one try (its points were never touched)")
    plj = os.path.join(folder, "skin", "patches_labels.json"); json.dump({"patches": []}, open(plj, "w"))
    rc = run("skin-rim", "--job", job, "--tag", "r1", "--set", B)
    check(rc == 2 and "THE FEATURE MAP" in " ".join(out), "31as: skin-rim refuses skin-labels' raw layout - THE FEATURE MAP (skin-features) comes first")
    json.dump({"patches": [], "merge_smooth": {"FEATURES": "features.json", "log": []}}, open(plj, "w"))
    rc = run("skin-rim", "--job", job, "--tag", "r1", "--set", B)
    check(rc == "passed", "after the restart the layout steps run again")
    pj = os.path.join(folder, "skin", "patches.json"); json.dump({"patches": [{"patch": 5, "kind": "changed", "bbox": [5, 6, 0, 1, -0.5, 0.5]}]}, open(pj, "w"))
    for f in ("LAYOUT_01_orbit_000.png",): open(os.path.join(folder, "skin", "review", f), "wb").write(b"png")
    json.dump({"kind": "layout", "frames": ["LAYOUT_01_orbit_000.png"], "md5": md(pj)}, open(os.path.join(folder, "skin", "review", "LAYOUT_LOOK.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "layout", "--verdict", "redo", "--note", "face 5 has a saw-toothed border along the crown"], kit, say)
    check(rc == 2 and "name every place" in " ".join(out), "a redo that names no place is refused - the tries are counted per spot")
    out.clear(); rc = KR.judge(["--job", job, "--what", "layout", "--verdict", "redo", "--note", "face 5 has a saw-toothed border along the crown", "--face", "5"], kit, say)
    st_ = KR.restart_state(folder)
    check(rc == 0 and len(st_["spots"]) == 1 and st_["spots"][0]["box"][0] < 5 < st_["spots"][0]["box"][1], "--face 5 is its box (+1 mm); spot B, not named, passed and starts again")
    pc = os.path.join(folder, "skin", "piece_skin.brep"); open(pc, "wb").write(b"piece one")
    json.dump({"piece_md5": md(pc), "faces": [{"face": 12, "rung": "fit", "area_mm2": 862.0, "bbox": [-3, 3, 0, 2, -0.5, 0.5]}]}, open(os.path.join(folder, "skin", "piece_faces.json"), "w"))
    fr = ["SKIN_look_01_orbit_000.png", "SKIN_look_02_below_045.png", "SKIN_look_face012_iso1.png", "SKIN_look_face012_iso2.png"]
    for f in fr: open(os.path.join(folder, "skin", "review", f), "wb").write(b"png")
    opened31cb(root, *[os.path.join(folder, "skin", "review", f) for f in fr])
    json.dump({"kind": "skin", "frames": fr, "md5": md(pc), "frame_info": {"SKIN_look_face012_iso1.png": {"subject": "face", "face": 12, "area_mm2": 862.0},
               "SKIN_look_face012_iso2.png": {"subject": "face", "face": 12, "area_mm2": 862.0}}, "mesh_quality": {"defective": False, "cracks": 0}, "original_faces": {"taken": True}}, open(os.path.join(folder, "skin", "review", "PIECE_LOOK.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "skin", "--verdict", "ok", "--note", "every face simple, clean borders, no lump seen anywhere"], kit, say)
    check(rc == 2 and "second" in " ".join(out).lower(), "a skin ok is refused until the SECOND REVIEWER has judged the piece")
    out.clear(); rc = KR.judge(["--job", job, "--what", "skin", "--verdict", "redo", "--note", "face 12 looks lumpy from here, redo it at once", "--face", "12"], kit, say)
    check(rc == 0 and "needs none" in " ".join(out).lower(), "31br L1 (the client 2026-10-29): a REDO of the piece on an opened frame is RECORDED without the second review and says so - the full review is not spent on a piece known wrong; only an OK waits for it")
    for _jf in (os.path.join(folder, "skin", "review", "PIECE_JUDGED.json"),):      # recorded
        if os.path.isfile(_jf): os.remove(_jf)
    out.clear(); rc = KR.second(["--job", job, "--what", "skin", "--brief", "--shards", "2"], kit, say)
    st = json.load(open(os.path.join(folder, "skin", "review", "SECOND_skin.json")))
    check(rc == 0 and len(st["assigned"]) == 2 and sum(len(g) for g in st["assigned"].values()) == 4 and "LUMP" in " ".join(out), "--brief: contiguous shards covering every frame, and the reviewer's brief (the client's standard)")
    rc = KR.second(["--job", job, "--what", "skin", "--shard", "0", "--result", json.dumps({"frames_opened": [fr[0]], "defects": [], "verdict": "pass"})], kit, say)
    check(rc == 2, "a shard that did not open every frame it was given is refused")
    KR.second(["--job", job, "--what", "skin", "--shard", "0", "--result", json.dumps({"frames_opened": fr[:2], "defects": [{"frame": fr[1], "what": "a dimple", "severity": "flaw", "size": "small"}], "verdict": "pass"})], kit, say)
    out.clear(); KR.second(["--job", job, "--what", "skin", "--shard", "1", "--result", json.dumps({"frames_opened": fr[2:], "defects": [{"frame": "SKIN_look_face012_iso1", "what": "crumpled", "severity": "blocker", "size": "large", "face": 12}], "verdict": "fail"})], kit, say)
    txt = " ".join(out)
    check("crumpled" in txt and txt.index("crumpled") < txt.index("a dimple") and "862" in txt, "the defects come back ranked LARGEST first (the 862 mm2 face before the small dimple)")
    sp12 = [x for x in KR.restart_state(folder)["spots"] if x["box"][0] < 0 < x["box"][1]]
    check(len(sp12) == 1 and len(sp12[0]["tries"]) == 1, "the second reviewer's blocker is a try AT ITS FACE (face 12's box from piece_faces.json)")
    out.clear(); rc = KR.judge(["--job", job, "--what", "skin", "--verdict", "ok", "--note", "every face simple, clean borders, no lump seen anywhere"], kit, say)
    check(rc == 2 and "blocker" in " ".join(out), "the agent cannot call `ok` over the second reviewer's blocker")
    out.clear(); rc = KR.second(["--job", job, "--what", "skin", "--shard", "1", "--result", json.dumps({"frames_opened": fr[2:], "defects": [{"frame": fr[2], "what": "torn", "severity": " Blocker ", "size": " Large", "face": 12}], "verdict": "fail "})], kit, say)
    check(rc == 0 and "1 blocker" in " ".join(out).lower(), "31bq B14: a ' Blocker ' / 'fail ' shard result counts its blocker (normalised)")
    _t14 = " ".join(out); check("torn" in _t14 and "a dimple" in _t14 and _t14.index("torn") < _t14.index("a dimple"), "31bq RR (B14 pin): a ' Large' ' Blocker ' ranks before a small flaw (the normalised size)")
    out.clear(); rc = KR.judge(["--job", job, "--what", "skin", "--verdict", "ok", "--note", "every face simple, clean borders, no lump seen anywhere"], kit, say)
    check(rc == 2 and "blocker" in " ".join(out), "...and the agent's ok is refused over it")
    _sp2 = os.path.join(folder, "skin", "review", "SECOND_skin.json"); _st2 = json.load(open(_sp2))
    _st2["results"]["1"] = {"verdict": "fail ", "defects": [{"frame": fr[2], "what": "scuffed", "severity": "flaw", "size": "small"}], "poor": [], "when": "x"}; json.dump(_st2, open(_sp2, "w"))
    _ok2, _msg2, _rk2 = KR.second_verdict(folder, pc)
    check(_ok2 is False and _rk2 is not None and "1 blocker" in _msg2, "31bq RR (B14 pin): a 'fail ' verdict with only a flaw counts as a blocker (an older record's unstripped verdict)")
    # severity
    out.clear(); rc = KR.second(["--job", job, "--what", "skin", "--shard", "1", "--result", json.dumps({"frames_opened": fr[2:], "defects": [{"frame": fr[2], "what": "torn", "blocker": True, "size": "large"}], "verdict": "fail"})], kit, say)
    check(rc == 2 and "severity" in " ".join(out) and "REFUSED" in " ".join(out), "31bp: a shard result whose defect carries no severity (blocker | flaw | note) is refused by name, nothing recorded")
    out.clear(); rc = KR.second(["--job", job, "--what", "skin", "--shard", "1", "--result", json.dumps({"frames_opened": fr[2:], "defects": [], "verdict": "redo"})], kit, say)
    check(rc == 2 and "pass" in " ".join(out) and "fail" in " ".join(out), "31bp: a shard result whose verdict is not pass | fail is refused by name")
    out.clear(); rc = KR.second(["--job", job, "--what", "skin", "--assign"], kit, say)
    check("THE RESULT, exactly this JSON" in " ".join(out), "31bp: the --assign brief prints the result schema")
    out.clear(); rc = KR.judge(["--job", job, "--what", "skin", "--verdict", "redo", "--note", "face 12 crumpled under the spine - its points next", "--face", "12"], kit, say)
    sp12 = [x for x in KR.restart_state(folder)["spots"] if x["box"][0] < 0 < x["box"][1]]
    check(rc == 0 and len(sp12) == 1 and len(sp12[0]["tries"]) == 1, "after the complete review the redo is recorded; the same piece at the same spot counts once")
    os.makedirs(os.path.join(root, ".claude"), exist_ok=True)
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "hooks")); import lookgate as LG
    opened31cb(root, os.path.join(folder, "skin", "review", "LAYOUT_01_orbit_000.png"))
    json.dump({"patches": [{"patch": 5, "kind": "changed", "bbox": [5, 6, 0, 1, -0.5, 0.5]}, {"patch": 6, "kind": "orig"}]}, open(pj, "w"))
    json.dump({"kind": "layout", "frames": ["LAYOUT_01_orbit_000.png"], "md5": md(pj)}, open(os.path.join(folder, "skin", "review", "LAYOUT_LOOK.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "layout", "--verdict", "ok", "--note", "every face one simple surface, both sides alike, nothing missing"], kit, say)
    check(rc == 0 and KR.standing_ok(folder, "layout"), "the layout judged ok on its pictures - it stands")
    rc = run("skin-labels", "--job", job, "--tag", "l9", "--set", B, "--set", "MIRROR=x 0")
    st_ = LG._dd_load(root)
    check(rc == 2 and "THE TWO WAYS TO RE-MAKE IT" in " ".join(out) and "first refusal" in " ".join(out) and not st_.get("owed"),
          "31bk: re-running skin-labels over a standing ok is REFUSED the first time, the two ways named, no strike")
    rc = run("skin-labels", "--job", job, "--tag", "l9b", "--set", B, "--set", "MIRROR=x 0")
    st_ = LG._dd_load(root)
    check(rc == 2 and st_["owed"] and "undo work" in st_["owed"]["sentence"] and "after the refusal that named the two ways" in st_["owed"]["sentence"],
          "31bk: the SECOND attempt against the same ok is the strike (\"I tried to undo work the renders said was good\")")
    LG.check(root, "Bash", {"command": 'echo "%s"' % LG.apology(st_["owed"]["n"], "x")}, folder)
    _row31bk = "| 2099-01-01 00:00:01 | l9 | skin-wires | - | kit: KILLED | 137 | 361 |" + chr(10)
    open(os.path.join(folder, "BUILD_LOG.md"), "a", encoding="utf-8").write(_row31bk)
    rc = run("skin-labels", "--job", job, "--tag", "l9c", "--set", B, "--set", "MIRROR=x 0")
    check("OVERTURNED" in " ".join(out) and "skin-wires l9 KILLED" in " ".join(out) and KR.standing_ok(folder, "layout") is None,
          "31bk: a later step KILLED on the layout overturns its ok - skin-labels runs by itself (the line says which step)")
    _bl = os.path.join(folder, "BUILD_LOG.md"); _txt = open(_bl, encoding="utf-8").read().replace(_row31bk, ""); open(_bl, "w", encoding="utf-8").write(_txt)
    json.dump({"kind": "layout", "frames": ["LAYOUT_01_orbit_000.png"], "md5": md(pj)}, open(os.path.join(folder, "skin", "review", "LAYOUT_LOOK.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "layout", "--verdict", "ok", "--note", "every face one simple surface, both sides alike, nothing missing"], kit, say)
    check(rc == 0 and KR.standing_ok(folder, "layout"), "31bk: judged ok again after the overturn - it stands again")
    LG._record_measure(root, {"what": "edge tolerance", "box": [0, 1, 0, 1, 0, 1]})
    out.clear(); rc = KR.judge(["--job", job, "--what", "layout", "--verdict", "redo", "--note", "the edge tolerance number says face 5 is off by 0.2 mm", "--face", "5"], kit, say)
    check(rc == 2 and "A number does not overturn a picture" in " ".join(out) and LG._dd_load(root)["owed"], "a redo of an ok'd layout with no picture is refused - and a strike")
    LG.check(root, "Bash", {"command": 'echo "silly dum dum"'}, folder)
    # RENDER DEFECTIVE
    os.makedirs(os.path.join(root, ".claude"), exist_ok=True)
    bad_ = os.path.join(folder, "skin", "review", "LAYOUT_03_below_135.png"); open(bad_, "wb").write(b"png")
    with open(os.path.join(root, ".claude", "frames.jsonl"), "a") as fh:
        fh.write(json.dumps({"png": bad_, "png_n": LG._norm(bad_), "box": [0, 1, 0, 1, 0, 1], "defective": True, "quality": {"defective": True, "why": "6130 crack edge(s) between faces (a torn seam)"}}) + "\n")
    time.sleep(0.05); LG.record_open(root, bad_); n0_ = len(LG._dd_load(root)["strikes"])
    out.clear(); rc = KR.judge(["--job", job, "--what", "layout", "--verdict", "redo", "--note", "face 5's border is saw-toothed along the crown, seen from below", "--face", "5", "--frame", bad_], kit, say)
    check(rc == 2 and "RENDER DEFECTIVE" in " ".join(out) and KR.standing_ok(folder, "layout") and len(LG._dd_load(root)["strikes"]) == n0_,
          "31bn: a redo citing a frame stamped RENDER DEFECTIVE is refused - the ok stands, no strike (%s)" % " ".join(out)[-100:])
    shot = os.path.join(folder, "skin", "review", "LAYOUT_02_below_045.png"); open(shot, "wb").write(b"png")
    time.sleep(0.05); LG.record_open(root, shot)
    out.clear(); rc = KR.judge(["--job", job, "--what", "layout", "--verdict", "redo", "--note", "face 5's border is saw-toothed along the crown, seen from below", "--face", "5", "--frame", shot], kit, say)
    check(rc == 0 and not KR.standing_ok(folder, "layout"), "a redo citing a picture opened after the ok and after the measurement overturns it")
    rc = run("skin-labels", "--job", job, "--tag", "l9", "--set", B, "--set", "MIRROR=x 0")
    check(rc == "passed", "once overturned by a picture, the layout's steps run again")
    class KitRun(Kit):
        ran = []
        def _wallclock(self): return None
        def _judge_output(self, o, rc, log, name): return rc
        def cmd_clock(self, a): pass
        def cmd_state(self, a): pass
        def sh(self, cmdline, cap, log, env, cwd=None, outputs=None):
            r_ = env["RUN"]; s_ = env.get("STEP"); scr = os.path.basename(cmdline[-1])
            KitRun.ran.append((scr, s_, os.path.isfile(os.path.join(r_, "body_new.brep"))))
            if scr == "rb_reinsert.py" and s_ == "3":
                open(os.path.join(r_, "body_new.brep"), "wb").write(b"the trial's body"); json.dump({"faces": 1}, open(os.path.join(r_, "REBUILD_reinsert.json"), "w"))
                return 0, "saved body_new.brep"
            if scr == "rb_reinsert.py" and s_ == "4":
                json.dump({"verdict": "PASS"}, open(os.path.join(r_, "REBUILD_check.json"), "w")); return 0, "CHECK PASS seam 0"
            if scr == "rb_review_body.py":
                os.makedirs(os.path.join(r_, "review_body"), exist_ok=True)
                open(os.path.join(r_, "review_body", "trial_whole_iso.png"), "wb").write(b"png"); return 0, "DONE"
            return 0, "STEP %s done" % s_
    kr = KitRun(root); kr.ENV = {"min_free_gb": 0.0}
    def run2(*a):
        out.clear(); import builtins; p0 = builtins.print; builtins.print = lambda *x, **k: out.append(" ".join(str(y) for y in x))
        try: return KR.cmd(list(a), kr)
        finally: builtins.print = p0
    pc2 = os.path.join(folder, "skin", "piece_skin.brep"); open(pc2, "wb").write(b"piece trial")
    open(os.path.join(folder, "window_solid.brep"), "wb").write(b"w"); json.dump([], open(os.path.join(folder, "walls.json"), "w"))
    rc = run("reinsert", "--job", job, "--tag", "t1", "--set", "STEP=2", "--set", B)
    check(rc == 2 and ("no verdict on the skin" in " ".join(out) or "judged 'redo'" in " ".join(out) or "earlier" in " ".join(out)), "a real STEP 2 still waits for the piece's verdict (%s)" % " ".join(out)[-160:])
    lj_ = os.path.join(folder, "skin", "review", "LOOK_JUDGED.json")
    if os.path.isfile(lj_): os.remove(lj_)
    json.dump({"kind": "skin", "frames": fr, "md5": md(pc2), "mode": "quick", "mesh_quality": {"defective": False, "cracks": 0}, "original_faces": {"taken": True}}, open(os.path.join(folder, "skin", "review", "PIECE_LOOK.json"), "w"))
    rc = run("reinsert", "--job", job, "--tag", "t1", "--set", "STEP=2", "--set", B, "--set", "TRIAL=look at the real model before the full review")
    check(rc == 2 and "THE LOOK FIRST" in " ".join(out), "31az: a TRIAL is refused until the piece's quick look is judged ok")
    LG_ = KR._lookgate(kit); os.makedirs(os.path.join(root, ".claude"), exist_ok=True)
    open(os.path.join(root, ".claude", "looks.jsonl"), "w").close()
    out.clear(); rc = KR.judge(["--job", job, "--what", "look", "--verdict", "ok", "--note", "every frame: the spine one clean face, the vanes smooth, nothing missing"], kit, say)
    check(rc == 2 and "never opened" in " ".join(out), "31az: a look verdict on frames nobody opened is refused")
    time.sleep(1.1)
    for f_ in fr: LG_.record_open(root, os.path.join(folder, "skin", "review", f_))
    # RENDER DEFECTIVE
    json.dump({"kind": "skin", "frames": fr, "md5": md(pc2), "mode": "quick", "mesh_quality": {"defective": False, "cracks": 0}, "frame_info": {fr[0]: {"quality": {"defective": True, "why": "6130 crack edge(s) between faces (a torn seam)"}}}},
              open(os.path.join(folder, "skin", "review", "PIECE_LOOK.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "look", "--verdict", "ok", "--note", "every frame: the spine one clean face, the vanes smooth, nothing missing"], kit, say)
    check(rc == 2 and "RENDER DEFECTIVE" in " ".join(out) and "crack" in " ".join(out) and not os.path.isfile(lj_),
          "31bn: a look verdict on a set holding a RENDER DEFECTIVE frame is refused with the frame's reason - no verdict written")
    json.dump({"kind": "skin", "frames": fr, "md5": md(pc2), "mode": "quick", "mesh_quality": {"defective": False, "cracks": 0}, "frame_info": {fr[0]: {"quality": {"defective": False}}}, "original_faces": {"taken": True}},
              open(os.path.join(folder, "skin", "review", "PIECE_LOOK.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "look", "--verdict", "redo", "--note", "the keel end is a bulb in below_045 - wrong there", "--face", "12"], kit, say)
    check(rc == 0 and any("rework the edit" in l for l in out), "31az: a look redo names its place, counts a try, and sends the agent back to the lines / points")
    # NOT TAKEN
    _plj = os.path.join(folder, "skin", "review", "PIECE_LOOK.json"); _rl = json.load(open(_plj))
    for _of, _want in (({"taken": False, "fault": True, "why": "a KIT FAULT - KeyError: 'fid' (sk_look.py line 300)"}, 2), (None, 2), ({"taken": False, "applies": False, "why": "a voxel source"}, 0)):
        _r2 = dict(_rl); _r2.pop("original_faces", None)
        if _of is not None: _r2["original_faces"] = _of
        json.dump(_r2, open(_plj, "w")); out.clear(); rc = KR.judge(["--job", job, "--what", "look", "--verdict", "ok", "--note", "every frame: the spine one clean face, the vanes smooth, nothing missing"], kit, say)
        check(rc == _want and ((rc == 0) or ("NOT TAKEN" in " ".join(out) and ("KIT FAULT" in " ".join(out) if _of else "before 31bq B18" in " ".join(out)))),
              "31bq B18 (R7W): judge --what look ok with the original's faces %s -> rc %s (%s)" % ("NOT TAKEN (a kit fault)" if _of and not _of.get("taken") and _of.get("applies") is not False else ("not measured: does not apply" if _of else "absent"), rc, " ".join(out)[:140]))
    json.dump(_rl, open(_plj, "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "look", "--verdict", "ok", "--note", "every frame: the spine one clean face, the vanes smooth, nothing missing"], kit, say)
    check(rc == 0 and os.path.isfile(lj_), "31az: kit rebuild judge --what look ok on the quick look's frames, every one opened (%s)" % " ".join(out)[-120:])
    rc = run("reinsert", "--job", job, "--tag", "t1", "--set", "STEP=2", "--set", B, "--set", "TRIAL=look at the real model before the full review")
    check(rc == 2 and "mirror checks should pass before creating a real model" in " ".join(out), "a TRIAL of a symmetric edit waits for the piece's mirror check (the client)")
    json.dump({"plane": "x 0", "pass": True, "unpaired": [], "pairs": [[1, 2]], "md5": md(pc2)}, open(os.path.join(folder, "skin", "mirror_piece.json"), "w"))
    rc = run2("reinsert", "--job", job, "--tag", "t1", "--set", "STEP=2", "--set", B, "--set", "TRIAL=look at the real model before the full review")
    check(rc == 0 and json.load(open(os.path.join(folder, "TRIAL.json")))["done"] is False, "mirror-checked, the TRIAL's STEP 2 runs without the piece's verdict (TRIAL.json written)")
    rc = run("reinsert", "--job", job, "--tag", "t1", "--set", "STEP=3", "--set", B)
    check(rc == 2 and "the last STEP 2 was a TRIAL" in " ".join(out), "STEP 3 without TRIAL while a trial is in progress is refused (a trial's body is never body_new)")
    rc = run("reinsert", "--job", job, "--tag", "t1", "--set", "STEP=3", "--set", B, "--set", "TRIAL=look at the real model before the full review")
    check(rc == "passed", "STEP 3 with TRIAL runs")
    bt = os.path.join(folder, "body_trial.brep"); open(bt, "wb").write(b"a trial body"); os.makedirs(os.path.join(folder, "review_body"), exist_ok=True)
    for f in ("rb_01_top.png",): open(os.path.join(folder, "review_body", f), "wb").write(b"png")
    json.dump({"kind": "trial", "frames": ["rb_01_top.png"], "md5": md(bt)}, open(os.path.join(folder, "review_body", "TRIAL_LOOK.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "trial", "--verdict", "ok", "--note", "the real model looks right from every side shown"], kit, say)
    check(rc == 2 and "TWO reviewers" in " ".join(out), "a trial's ok waits for its two reviewers (31aw: an accepted trial IS the model; 31ar's 'never' withdrawn by the client 10-08)")
    out.clear(); rc = KR.judge(["--job", job, "--what", "trial", "--verdict", "redo", "--note", "face 12 crumples under the spine in the real body", "--face", "12"], kit, say)
    check(rc == 0 and any(len(x["tries"]) >= 1 for x in KR.restart_state(folder)["spots"]), "a trial's redo names its place and counts a try there (the restart sees the trial loop)")
    json.dump({"kind": "skin", "frames": fr, "md5": md(pc2), "mode": "quick", "mesh_quality": {"defective": False, "cracks": 0}}, open(os.path.join(folder, "skin", "review", "PIECE_LOOK.json"), "w"))
    out.clear(); rc = KR.second(["--job", job, "--what", "skin"], kit, say)
    check(rc == 2 and "QUICK" in " ".join(out), "the second reviewer refuses a quick look - it reviews the full one")
    json.dump({"kind": "skin", "frames": fr, "md5": md(pc2), "mode": "full", "mesh_quality": {"defective": False, "cracks": 0}}, open(os.path.join(folder, "skin", "review", "PIECE_LOOK.json"), "w"))
    out.clear(); rc = KR.second(["--job", job, "--what", "skin"], kit, say)
    check(rc == 0 and "THE SECOND REVIEW" in " ".join(out), "`kit rebuild second` with no --shard prints the assignment (kit.py strips --brief; --assign or nothing)")
    TR = "TRIAL=look at the real model before the full review"; bn = os.path.join(folder, "body_new.brep")
    open(bn, "wb").write(b"left by an interrupted trial STEP 4")
    rc = run2("reinsert", "--job", job, "--tag", "t2", "--set", "STEP=3", "--set", B, "--set", TR)
    check(rc == 0 and "renamed body_trial.brep" in " ".join(out) and KitRun.ran[-1] == ("rb_reinsert.py", "3", False),
          "while a trial stands, a body_new.brep left by an interrupted STEP 4 is renamed body_trial.brep before anything reads it")
    check(not os.path.isfile(bn) and open(bt, "rb").read() == b"the trial's body" and os.path.isfile(os.path.join(folder, "REBUILD_reinsert_trial.json"))
          and not os.path.isfile(os.path.join(folder, "REBUILD_reinsert.json")), "the trial's STEP 3 leaves its body as body_trial.brep, never body_new.brep")
    rc = run2("reinsert", "--job", job, "--tag", "t2", "--set", "STEP=4", "--set", B)
    check(rc == 2 and "the last STEP 2 was a TRIAL" in " ".join(out), "a real STEP 4 after a trial's STEP 3 is refused")
    rc = run2("reinsert", "--job", job, "--tag", "t2", "--set", "STEP=4", "--set", B, "--set", TR)
    tj_ = json.load(open(os.path.join(folder, "TRIAL.json")))
    check(rc == 0 and KitRun.ran[-1] == ("rb_reinsert.py", "4", True) and not os.path.isfile(bn) and os.path.isfile(bt)
          and os.path.isfile(os.path.join(folder, "REBUILD_check_trial.json")) and tj_["done"] is True,
          "the trial's STEP 4 reads the body under rb_reinsert's name for the run only; after it: body_trial.brep, REBUILD_check_trial.json, the trial done")
    rc = run2("reinsert", "--job", job, "--tag", "t3", "--set", "STEP=3", "--set", B)
    check(rc == 2 and "the last STEP 2 was a TRIAL" in " ".join(out), "a FINISHED trial still refuses a real STEP 3 on what it sewed (only a real STEP 2 ends it)")
    rc = run2("review-body", "--job", job, "--tag", "t2", "--set", B)
    ev = json.load(open(os.path.join(folder, "env_review-body_t2.json"))); tl = json.load(open(os.path.join(folder, "review_body", "TRIAL_LOOK.json")))
    check(rc == 0 and os.path.basename(ev["NEW"]) == "body_trial.brep" and ev["TAG"] == "trial" and "trial_whole_iso.png" in tl["frames"] and tl["md5"] == md(bt),
          "review-body reviews the trial's body by default and lists its frames in TRIAL_LOOK.json (the trial's judge reads them)")
    rc = run2("reinsert", "--job", job, "--tag", "t3", "--set", "STEP=3", "--set", B, "--set", TR, "--bg")
    check(rc == 2 and "foreground" in " ".join(out), "a trial's STEP 3 / 4 is never run in the background (its body is renamed when it ends)")
    json.dump({"what": "skin", "verdict": "ok", "md5": md(pc2), "when": time.strftime("%Y-%m-%d %H:%M:%S"), "note": "selftest"}, open(os.path.join(folder, "skin", "review", "PIECE_JUDGED.json"), "w"))
    rc = run2("reinsert", "--job", job, "--tag", "r1", "--set", "STEP=2", "--set", B)
    check(rc == 0 and not os.path.isfile(os.path.join(folder, "TRIAL.json")), "a REAL STEP 2 that runs (the piece judged, mirror-checked) ends the trial")
    rc = run2("reinsert", "--job", job, "--tag", "r1", "--set", "STEP=3", "--set", B, "--set", TR)
    check(rc == 2 and "continues a trial that STEP 2 started" in " ".join(out), "TRIAL on STEP 3 with no trial STEP 2 before it is refused")
    open(bn, "wb").write(b"a real body")
    rc = run2("reinsert", "--job", job, "--tag", "t4", "--set", "STEP=2", "--set", B, "--set", TR)
    check(rc == 0 and not os.path.isfile(bn) and open(os.path.join(folder, "body_new_before_trial.brep"), "rb").read() == b"a real body"
          and json.load(open(os.path.join(folder, "TRIAL.json")))["done"] is False, "a trial's STEP 2 keeps a real body_new.brep aside (body_new_before_trial.brep) and records TRIAL.json")
    lp = os.path.join(folder, "BUILD_LOG.md")
    KR.log_row(folder, "b9", "skin-build", {"LAM": "0.5"}, KR.key_line("x\n   12s FACE LADDER: 7 kept\nSKIN BUILD PASS: 57 faces\nDONE"), 0, 41)
    rows = [l for l in open(lp, encoding="utf-8") if l.startswith("| 20")]
    check(any("SKIN BUILD PASS: 57 faces" in r and "LAM=0.5" in r for r in rows) and any("judge skin" in r for r in rows), "every run and judgement is a BUILD_LOG.md row (the verdict line, the levers set)")
    check(KR.key_line("a\nFAIL: THE FRAME CHECK - 2 edges\nb").startswith("FAIL:"), "a step's FAIL line is its key line")
    _ban = "FreeCAD 1.1.3, Libs: 1.1.3R20260725 (Git shallow)\n(C) 2001-2026 FreeCAD contributors\nFreeCAD is free and open-source software licensed under the terms of LGPL2+ license.\n"
    check(KR.key_line(_ban) == "" and KR.key_line(_ban.replace("(C)", "\u00a9")) == "", "31bq RR (B46): a banner-only output has NO key line (never the LGPL line) - the (C) and the \u00a9 forms")
    check(KR.key_line("   20s SOURCE -> source.stl + source_fid.npz: 18834 triangles\n   20s next: kit rebuild reinsert --set STEP=1 (the caps), then skin-regions -> skin-edges\nDONE\n" + _ban).startswith("SOURCE ->"), "31bq RR (B46): skin-source's row is its SOURCE line, not the next-step advice")
    check(KR.key_line("   93s edges built 134 (arc 21, line 40); failed 0\n   93s edge residual against its surfaces/planes: p50 0.0 p95 0.0 max 0.0 mm\n   93s junctions with fewer than 3 edges: 0 of 90\n" + _ban).startswith("edges built 134"), "31bq RR (B46): skin-network's row is its edges-built line")
    check(KR.key_line("    4s FRAME v2: 41 skin faces with wall stretches; wall junctions placed 42, unplaced 0\nDONE\n" + _ban).startswith("FRAME v2:"), "31bq RR (B46): skin-frame's row is its FRAME v2 line")
finally:
    shutil.rmtree(root, ignore_errors=True)
_proj = tempfile.mkdtemp(prefix="skin2proj_"); os.makedirs(os.path.join(_proj, "claude_code")); os.environ["KIT_PROJECT"] = _proj
import kit as KIT
if os.name == "nt":
    _grand = "import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); time.sleep(60)"
    p = subprocess.Popen([sys.executable, "-c", _grand], creationflags=0x08000000)
    time.sleep(2.0)
    kids = [str(pid) for pid, ppid, _c in KIT._win_procs() if ppid == p.pid]
    left = KIT._kill_tree(p, [sys.executable, "x.py"])
    time.sleep(0.5)
    gone = all(not KIT._alive(int(k)) for k in kids)
else:
    p = subprocess.Popen([sys.executable, "-c", "import subprocess, time; subprocess.Popen(['sleep', '60']); time.sleep(60)"], start_new_session=True)
    time.sleep(1.0)
    kids = subprocess.run(["pgrep", "-P", str(p.pid)], capture_output=True, text=True).stdout.split()
    left = KIT._kill_tree(p, [sys.executable, "x.py"])
    time.sleep(0.5)
    gone = all(subprocess.run(["kill", "-0", k], capture_output=True).returncode != 0 for k in kids)
check(kids and left == [] and gone and p.poll() is not None, "the kill ends the step AND its child, and confirms it (%d child, left %r)" % (len(kids), left))
_bk = KIT._brief_keep
_kept = ["   12s    3 face pair(s) with overlapping boxes could not be measured for a crossing (the kernel's distance or section raised) - unmeasured, not clear (31bq B16)",
         "    4s    original face(s) named in FEATURES that no patch comes from: [1734] (a typo, or the points gave them no face)",
         "    4s    frame face 3 (2.1 mm2): its wall edge(s) at [[1, 2, 3]] get no face of their own - PTS_BOX there", "    4s    FACE 5 IN 2 PIECES: [1.0, 2.0] mm2",
         "    4s    body face 1 edge 2: owner 3 could not hold the rim, 4 has it", "    9s    the shell not closed", "    9s    Error in Face: BOPAlgo SelfIntersect",
         "    9s    an Exception while processing file", "    9s    face 3 invalid as built", "    9s    Warning: the sew left 2 faces"]
_lost = [x_ for x_ in _kept if not _bk(x_)]
check(not _lost, "31bq UU (B56): --brief keeps every finding the round-4 skeptic found dropped %s" % ([x_[:50] for x_ in _lost] or ""))
check(not _bk("   12s    face 3: spanning 5 edge(s) + 0 added line(s) - NURBS fill first, then Coons, then plate") and not _bk("[leangate] the next step is kit look") and _bk("SKIN BUILD PASS: 76 faces"),
      "31bq UU (B56): ...and still drops the advice (an indented sub-line, a [leangate] note) while a verdict line prints")
_kept5 = ["    4s     fillet line 32: R 1.5 needs t 3.76 mm of each face (beta 136 deg) - more than the line's 7.5 mm / 2.5: R capped to 0.805 (a fillet by lines needs 2.5 t of line for its run-out(s))",
          "   12s     chain 0: no mirrored chain - line(s) [54] have no twin within 1.5 mm; decide the other side's chain by name",
          "   29s     fillet chain 2: face 2's strip had gap(s) [(0, 23.2)] where a member is missing or stands with an open end - closed by the missing member's own crease piece, else a straight end line",
          "[leangate] VOLUME CHANGE -389.0 mm3 by the local ruler (the piece against the region's content) against the card's -348.0 - reported, not judged; the pictures decide (31bq B21).",
          "[leangate] APPLY GATE PASSED - the check and the look are this job's - reported, not judged against the card",
          "   16s     fillet chain 2: CONVEX corner at [0.0, -101.0, 77.5] turns 17 deg with ONE contact and a floor of 0.21 mm - under the print tolerance (THIN_MM 0.3): NO corner face; the two blends share ONE end arc"]
_lost5 = [x_ for x_ in _kept5 if not _bk(x_)]
check(not _lost5, "31bq R5c (B56 / NEW #33): --brief keeps the capped R, the missing mirror, the strip gap, accept's VOLUME and GATE PASSED lines %s" % ([x_[:50] for x_ in _lost5] or ""))
check(not _bk("   12s    face 3: spanning 5 edge(s) + 0 added line(s) - NURBS fill first, then Coons, then plate") and not _bk("[leangate] the next step is kit look"),
      "31bq R5c: ...and the advice still drops")
# skin-features  live layout
_bf = tempfile.mkdtemp(prefix="skin2_bf_"); os.makedirs(os.path.join(_bf, "skin")); os.makedirs(os.path.join(_bf, "tags", "f1"))
for _p in (os.path.join(_bf, "skin", "patches_labels.json"), os.path.join(_bf, "tags", "f1", "patches_labels.json")): open(_p, "w").write('{"patches": [], "merge_smooth": 1}')
json.dump({"_step": "skin-features", "_tag": "f1", "_when": "2026-10-16 16:14:00", "THIN_MM": "0.4", "TINY": "7"}, open(os.path.join(_bf, "env_skin-features_f1.json"), "w"))
_lk = {"when": "2026-10-16 16:14:30", "tag": "f1", "levers": {"skin-features": {k_: ("7" if k_ == "TINY" else None) for k_ in KR.LOCKED_LEVERS["skin-features"] if k_ != "THIN_MM"}}, "from": {}, "not_on_record": []}
json.dump(_lk, open(os.path.join(_bf, "skin", "LAYOUT_LOCK.json"), "w")); _said = []
_d1 = KR.lock_backfill(_bf, KR.layout_lock(_bf), "skin-features", _said.append, write=True); _lk2 = KR.layout_lock(_bf)
check(_d1 and _d1[0][:2] == ("THIN_MM", "0.4") and (_lk2["levers"]["skin-features"].get("THIN_MM") == "0.4") and _lk2.get("backfilled") and "env_skin-features_f1.json" in _said[0] and "live layout" in _said[0],
      "R7W tester-findings: a lock with no THIN_MM key is backfilled from the run that made the live layout (0.4), written with a note and said")
_said = []; check(KR.lock_backfill(_bf, KR.layout_lock(_bf), "skin-features", _said.append) == [] and not _said, "...and a lock that holds the key is left as it is")
os.remove(os.path.join(_bf, "env_skin-features_f1.json")); _lk3 = dict(_lk); _lk3["levers"] = {"skin-features": dict(_lk["levers"]["skin-features"])}; _said = []
_d3 = KR.lock_backfill(_bf, _lk3, "skin-features", _said.append, write=False)
check(_d3 == [] and "THIN_MM" not in _lk3["levers"]["skin-features"] and bool(_said) and "left FREE" in _said[0],
      "...and with no run of skin-features on record it is said by name and left free")
shutil.rmtree(_bf, ignore_errors=True)
# kit accept  REBUILD_source.json
_mr = tempfile.mkdtemp(prefix="skin2_mr_"); _mj = os.path.join(_mr, "claude_code", "jobs", "JOBM"); os.makedirs(_mj)
json.dump({"window": WIN, "planes": [], "body": "body.brep", "tag": "c1"}, open(os.path.join(_mj, "REBUILD_region.json"), "w"))
json.dump({"tag": "c1", "content_md5": "d333", "source_md5": "3cc9", "faces": 142, "triangles": 18834}, open(os.path.join(_mj, "REBUILD_source.json"), "w"))
json.dump({"tag": "c1", "verdict": "PASS", "protect_source": "the region's record"}, open(os.path.join(_mj, "REBUILD_check.json"), "w"))
class _KM: ROOT = _mr
_okm, _msgm = KR.merge_record(_KM(), "JOBM", None, say=lambda *a: None)
_stm = (json.load(open(os.path.join(_mj, "REBUILD.json"), encoding="utf-8")).get("steps") or {}) if _okm else {}
check(_okm and (_stm.get("source") or {}).get("source_md5") == "3cc9" and "source" in _msgm and (_stm.get("check") or {}).get("protect_source") == "the region's record",
      "R7W fix-small (F.15): kit accept's merge carries REBUILD_source.json (the skin route's own record) and each merged record WHOLE (REBUILD_check.json's protect_source) - %s" % str(_msgm)[:140])
shutil.rmtree(_mr, ignore_errors=True)
# REBUILD_source.json
# unreadable
def _fbf_job(root_, name_, damaged=False):
    j_ = os.path.join(root_, "claude_code", "jobs", name_)
    for d_ in ("skin/review", "review_body", "review"): os.makedirs(os.path.join(j_, *d_.split("/")))
    w_ = lambda rel, obj: json.dump(obj, open(os.path.join(j_, *rel.split("/")), "w", encoding="utf-8"))
    old_ = time.time() - 15 * 86400
    w_("REBUILD_region.json", {"tag": "r1", "window": WIN, "planes": [], "body": "body.brep", "content_mm3": 120.0, "protect": [[1, 2, 1, 2, 0, 1]]})
    w_("REBUILD_blend.json", {"tag": "v4a", "levers": {"R": 3.0, "OPEN": 0.0}, "added_mm3_faded": 773.6})
    w_("REBUILD_source.json", {"tag": "s1", "when": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 7 * 86400)), "content_md5": "d3335122aa", "source_md5": "3cc9b224bb",
                               "faces": 142, "triangles": 18834, "body_faces_mapped": 135, "unmapped_faces": []})
    w_("REBUILD_reinsert.json", {"tag": "t1", "G": 3.0, "join": "sew", "faces": 4807, "valid": True, "bop_ok": "the caps' own edges"})
    w_("REBUILD_check.json", {"tag": "t1", "verdict": "PASS", "refused": [], "protect": [], "protect_source": "the region's record", "seam": {"faces": 0}})
    for f_ in ("REBUILD_region.json", "REBUILD_blend.json"): os.utime(os.path.join(j_, f_), (old_, old_))
    pp_ = os.path.join(j_, "skin", "piece_skin.brep"); open(pp_, "wb").write(b"the skin piece"); pm_ = md(pp_)
    w_("skin/points1000.json", {"NPTS": 2314, "kept": [518, 536, 1095], "no_points": [1096], "levers": {"PTS_DROP": "0 1 0 1 0 1"}, "lever_whys": {"PTS_DROP": ["the slot closed"]},
                                "frame_faces": {"518": 1}, "frame_faces_no_point": []})
    if damaged: open(os.path.join(j_, "skin", "features.json"), "w").write("{not json")
    else: w_("skin/features.json", {"spine_top": [1100, 1101], "vane1_top": [1113], "_why": {"spine_top": "one smooth top", "vane1_top": "the vane"}})
    w_("skin/patches.json", {"patches": [{"kind": "orig"}, {"kind": "changed"}, {"kind": "cap"}, {"kind": "cap"}]})
    w_("skin/LAYOUT_LOCK.json", {"when": "w", "tag": "f1", "levers": {"skin-features": {"THIN_MM": "0.3"}}}); w_("skin/MIRROR_DECISION.json", {"plane": "x 0"})
    w_("skin/wire_simplify.json", {"skin_edges": 79, "counts": {"LINE": 20, "ARC": 28, "CUBIC": 21, "MULTI5": 4, "MULTI9": 3}, "chains": [{"chain": 1, "decided": "its reason"}, {"chain": 2}],
                                   "lines": "C:\\j\\skin\\LINES_c2.json"})
    if not damaged: w_("skin/guides.json", {"guides": [{"role": "split"}, {"role": "split"}, {"role": "guide"}]})
    w_("skin/fillets.json", {"fillets": [{"line": 30, "r": 1.5, "chain": 0, "buried": [1734]}], "room_levers": {"TAPER_X": {"value": "3"}}})
    sc_ = {"faces": 68, "volume": 12068.8, "valid": True, "closed": True, "free_edges": 0, "edge_off_max": 0.2896, "pcurve_gap_max": 0.2, "self_intersections": [[10, 42, 0.15, 0.002]],
           "si_self_faces": [], "edge_gaps_unmeasured": 0, "si_depth_incomplete": {}, "face_sanity": {"n_bad": 0, "mismatch_noted": [], "volume_mesh": 12069.0}, "check_faces": [{"face": 1}], "piece_md5": pm_}
    w_("skin/solid_c.json", [sc_] if damaged else sc_)
    w_("skin/piece_faces.json", {"piece_md5": pm_, "faces": [{"rung": "nurbs"}, {"rung": "nurbs"}, {"rung": "cap"}, {"rung": "fillet"}]})
    w_("skin/review/PIECE_LOOK.json", {"md5": ("another piece" if damaged else pm_), "mode": "quick", "frames": ["a.png", "b.png"], "tag": "b1", "mesh_quality": {"defective": False, "cracks": 0},
                                       "original_faces": {"taken": True, "named": [{"group": "region 1", "named_mm2": 3.2}]}})
    w_("TRIAL.json", {"done": True, "accepted": True, "accepted_when": "2026-10-16 12:38:39", "check": "CHECK PASS: valid True", "piece_md5": pm_, "body_md5": "bb01"})
    w_("review_body/SECOND_trial.json", {"md5": "bb01", "results": {"0": {"verdict": "fail ", "defects": [{"severity": " Blocker "}, {"severity": "flaw"}]}, "1": {"verdict": "pass", "defects": []}}})
    w_("review_body/TRIAL_JUDGED.json", {"verdict": "ok", "when": "2026-10-16 12:38:39", "ruling": "the client's word", "blockers_overruled": [{"what": "a blocker"}]})
    return j_, pm_
def _fbf_dossier(root_, name_):
    dx_ = os.path.join(root_, "claude_code", "dossier"); os.makedirs(os.path.join(dx_, name_))
    json.dump({name_: {"name": name_, "dir": os.path.join("claude_code", "dossier", name_)}}, open(os.path.join(dx_, "DOSSIER.json"), "w"))
    return lambda: [a_.get("text") for a_ in (json.load(open(os.path.join(dx_, "DOSSIER.json"), encoding="utf-8")).get(name_) or {}).get("added", [])]
_fb = tempfile.mkdtemp(prefix="skin2_fbf_")
class _KF: ROOT = _fb
_fj, _fpm = _fbf_job(_fb, "JOBS"); _flines = _fbf_dossier(_fb, "vanes")
try:
    _fok, _fmsg = KR.merge_record(_KF(), "JOBS", "vanes", say=lambda *a: None); _fx = None
except Exception as _e:
    _fok, _fmsg, _fx = False, "", "%s: %s" % (type(_e).__name__, _e)
_frec = json.load(open(os.path.join(_fj, "REBUILD.json"), encoding="utf-8")) if _fok else {}
def _fg(d_, *k_):
    for x_ in k_:
        d_ = d_.get(x_) if isinstance(d_, dict) else None
    return d_
_fbf = _frec.get("built_from") or {}; _fst = _frec.get("steps") or {}; _g = lambda *k_: _fg(_fbf, *k_)
check(_fok and _fbf.get("route") == "skin" and all(k_ in _fbf for k_ in ("region", "source", "points", "features", "layout", "wires", "piece", "look", "trial", "reinsert", "check", "records_left_out")),
      "R7W fix-built-from: a skin-route job's built_from is THE SKIN FORM - route skin, the source / points / wires / piece / trial sections (%s%s)" % (str(_fmsg)[:100], _fx or ""))
check([x_.get("record") for x_ in (_fbf.get("records_left_out") or [])] == ["REBUILD_blend.json"] and "blend" not in _fst and all(k_ in _fst for k_ in ("region", "source", "reinsert", "check"))
      and "REBUILD_blend.json (v4a" in str(_fmsg), "R7W fix-built-from: the voxel-era REBUILD_blend.json (older than the source) is LEFT OUT of the steps and NAMED with its date; the older region record and the newer reinsert / check stay")
check(_g("piece", "faces") == 68 and _g("piece", "volume") == 12068.8 and _g("piece", "piece_md5") == _fpm and _g("piece", "rungs") == {"nurbs": 2, "cap": 1, "fillet": 1}
      and _g("piece", "face_sanity", "volume_mesh") == 12069.0 and _g("piece", "check_faces") == 1 and _g("piece", "not_in_record") == [],
      "R7W fix-built-from: the piece - solid_c.json's faces / volume / face sanity, the piece file's md5, the rungs of piece_faces.json")
check(_g("source", "content_md5") == "d3335122aa" and _g("points", "kept") == 3 and _g("points", "NPTS") == 2314 and _g("points", "lever_whys") == {"PTS_DROP": ["the slot closed"]}
      and _g("features", "features") == 2 and _g("features", "_why", "spine_top") == "one smooth top" and _g("layout", "faces_by_kind") == {"orig": 1, "changed": 1, "cap": 2}
      and _g("layout", "mirror_plane") == "x 0" and _g("region", "protect") == [[1, 2, 1, 2, 0, 1]], "R7W fix-built-from: the source, the points with their levers' reasons, the features with their _why, the layout by kind, the region's boxes")
check(_g("wires", "skin_edges") == 79 and _g("wires", "counts", "MULTI") == 7 and _g("wires", "decided") == 1 and _g("wires", "lines_file") == "LINES_c2.json" and _g("wires", "add") == {"split": 2, "guide": 1}
      and (_g("wires", "fillets") or [{}])[0].get("buried") == [1734] and isinstance(_g("wires", "room_levers"), dict), "R7W fix-built-from: the wires - edges, counts (MULTI summed), decided, the LINES file, the _add by role, the fillets with buried, room_levers")
check(_g("look", "original_faces", "measure") == "TAKEN" and _g("look", "original_faces", "named") == 1 and _g("trial", "accepted") is True and _g("trial", "same_piece") is True
      and _g("trial", "second", "shards", "0", "blockers") == 1 and _g("trial", "second", "of_this_trial") is True and _g("trial", "judged", "blockers_overruled") == 1
      and _g("reinsert", "bop_ok") == "the caps' own edges" and _g("check", "protect_source") == "the region's record",
      "R7W fix-built-from: the look of THIS piece (its measure of the original's faces), the trial (accepted, the same piece, the reviewers' blockers, the ruling), reinsert's BOP_OK, check's protect source")
_fl = _flines()
check(len(_fl) == 1 and _fl[0].startswith("built from (skin route): job JOBS, source d3335122 (142 faces, 18834 triangles)") and "3 faces kept by 2314 points, 2 features" in _fl[0]
      and "79 wires (1 decided, 1 fillets); the piece 68 faces, 12068.8 mm3, valid True, edge gap 0.2896; trial accepted 2026-10-16 12:38:39; check PASS" in _fl[0] and "1 record(s) older than the source left out" in _fl[0],
      "R7W fix-built-from: the dossier's built-from line is the skin form's (%s)" % (_fl[0][:90] if _fl else "no line"))
_fj2, _fpm2 = _fbf_job(_fb, "JOBD", damaged=True)
try:
    _fok2, _fmsg2 = KR.merge_record(_KF(), "JOBD", None, say=lambda *a: None); _fx2 = None
except Exception as _e:
    _fok2, _fmsg2, _fx2 = False, "", "%s: %s" % (type(_e).__name__, _e)
_fbf = (json.load(open(os.path.join(_fj2, "REBUILD.json"), encoding="utf-8")).get("built_from") or {}) if _fok2 else {}
check(_fok2 and "unreadable" in str(_g("features", "absent")) and "guides.json absent" in str(_g("wires", "add", "absent")) and "not an object" in str(_g("piece", "solid", "absent"))
      and str(_fbf.get("look", "")).startswith("no look of this piece") and _g("piece", "piece_md5") == _fpm2,
      "R7W fix-built-from: a damaged skin job (features.json not JSON, guides.json missing, solid_c.json a list, the look of another piece) - the merge finishes, each SAID in its section (%s)" % (_fx2 or str(_fmsg2)[:80]))
_fv = os.path.join(_fb, "v"); _fvj = os.path.join(_fv, "claude_code", "jobs", "JOBV"); os.makedirs(_fvj); _flv = _fbf_dossier(_fv, "vanes")
json.dump({"tag": "s4k1", "window": WIN, "planes": [], "body": "body.brep"}, open(os.path.join(_fvj, "REBUILD_region.json"), "w"))
json.dump({"tag": "s4k43a", "design_surfaces": [{"face": 11, "kind": "BSplineSurface"}], "cells": {"kept": 3970}}, open(os.path.join(_fvj, "REBUILD_arrangement.json"), "w"))
json.dump({"tag": "s4k4a", "levers": {"R": 3.0, "OPEN": 0.0}}, open(os.path.join(_fvj, "REBUILD_blend.json"), "w"))
class _KV: ROOT = _fv
_fokv, _fmsgv = KR.merge_record(_KV(), "JOBV", "vanes", say=lambda *a: None)
_fbf = json.load(open(os.path.join(_fvj, "REBUILD.json"), encoding="utf-8")).get("built_from") or {}
check(_fokv and _fbf.get("design_surfaces_used") == 1 and (_fbf.get("cells") or {}).get("kept") == 3970 and "records_left_out" not in _fbf and "blend" in (json.load(open(os.path.join(_fvj, "REBUILD.json"), encoding="utf-8")).get("steps") or {})
      and (_flv() or [""])[0].startswith("built from: job JOBV, 1 design surfaces of body.brep"), "R7W fix-built-from: a job WITHOUT REBUILD_source.json keeps the old (voxel) form - its summary, its steps, its old dossier line")
check(_fbf.get("route") == "voxel", "R7W fix-built-from: ...and names it (built_from.route voxel)")
shutil.rmtree(_fb, ignore_errors=True)
shutil.rmtree(_proj, ignore_errors=True)
print("%d passed, %d FAILED" % (ok, bad))
sys.exit(1 if bad else 0)

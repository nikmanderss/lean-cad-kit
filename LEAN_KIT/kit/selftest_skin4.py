"""selftest_skin4.py - kit 31av (2026-10-07), without a kernel: the client's answers on the agent's R4 skin 2 loop and the render study.
the client: "Yes to changing it through points, it should still be able to have the lines that build it tweaked without selecting new points";
"2. yes" (layout rounds); "Yes keep what is correct" (the line decisions); "Yes to less picture but no to having any single step without them";
"Yes to outline. Yes to border label"; "Save each build state"; "What happens after mirror check if not that?"; "I'm fine with only getting
them on my request" (a trial file).
Cases: the quick picture set (four orbits above, two below, close-ups where the last redo pointed) and the full set unchanged; the line
decisions carried to a new numbering (the same two features, the nearest middle, within 3 mm; new borders listed); the layout lock (the first ok
fixes the section-wide levers, from the run that made the live layout - by md5, not by recency; a step not on record is said, not guessed; a
different value refused, the locked value taken); an ok refused on a quick set; three layout rounds lock every place they named; the judge's
--frame must be a picture in the job's own folder; a build's whole state saved and put back (the live state kept first, a file the state did not
have removed, refused while the points are owed); the mirror check's next line; look_at in one colour with the box's outline, in the job's picture
folder; kit deliver --trial refused without the client's words or the trial's body; the build and wire scripts' 31av lines present."""
import os, sys, json, shutil, tempfile, hashlib, subprocess, time, re
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

root = tempfile.mkdtemp(prefix="skin4_"); job = "JOB4"; folder = os.path.join(root, "claude_code", "jobs", job); sk = os.path.join(folder, "skin")
os.makedirs(os.path.join(sk, "review")); os.makedirs(os.path.join(root, ".claude"))
json.dump({"window": [-6.0, 6.0, 0.0, 4.0, -1.0, 1.0], "planes": []}, open(os.path.join(folder, "REBUILD_region.json"), "w"))
try:
    os.environ["RUN"] = folder; os.environ.pop("PICS", None)
    sys.path.insert(0, os.path.join(HERE, "rebuild"))
    import sk_lib as K
    full = [v[0] for v in K.views(close=False, below=False, pics="full")]
    check(full == ["orbit_%03d" % a for a in range(0, 360, 45)] + ["top", "bottom"], "PICS full: the views as before (8 orbits, straight down and up)")
    q = [v[0] for v in K.views(close=False, below=False, pics="quick")]
    check(q == list(K.QUICK_VIEWS) and len(q) == 6, "PICS quick: four orbits above and two from below - the underside is always looked at (%s)" % q)
    check(K.PICS == "full", "the script default is the full set (the runner suggests quick for the loop's steps)")
    json.dump({"spots": [{"id": 1, "box": [0, 1, 0, 1, 0, 0.5], "tries": [{"when": "2026-10-07 15:00:00"}]},
                         {"id": 2, "box": [2, 3, 1, 2, 0, 0.5], "tries": [{"when": "2026-10-07 16:00:00"}]},
                         {"id": 3, "box": [-3, -2, 1, 2, 0, 0.5], "tries": [{"when": "2026-10-07 14:00:00"}]}]}, open(os.path.join(sk, "RESTART.json"), "w"))
    qc = [v[0] for v in K.views(close=True, pics="quick")]
    check(qc == list(K.QUICK_VIEWS) + ["spot2", "spot1"], "quick close-ups: only where the last redos pointed, newest first, two at most (%s)" % qc[6:])
    os.remove(os.path.join(sk, "RESTART.json"))
    check(len(K.BORDER_NOTE) == 2 and "VOXEL" in K.BORDER_NOTE[0] and "WIRE_" in K.BORDER_NOTE[1], "the border caption: the voxel's triangles, not the model's edge")
    w(os.path.join(sk, "x.json"), "{}"); lk_ = K.write_look("layout", [os.path.join(sk, "review", "L.png")], os.path.join(sk, "x.json"))
    check(json.load(open(lk_)).get("pics") == "full", "every look record says which set it is (the judge reads it)")
    os.remove(lk_)
    prev = [{"chain": 0, "sig": ["spine", "vane"], "mid": [0, 0, 0], "dec": {"kind": "LINE", "why": "the spine's edge is straight"}},
            {"chain": 1, "sig": ["spine", "vane"], "mid": [10, 0, 0], "dec": {"kind": "ARC", "why": "the vane's edge is one arc [carried from chain 7]"}},
            {"chain": 2, "sig": ["CAP", "spine"], "mid": [0, 5, 0], "dec": None},
            {"chain": 3, "sig": ["keel", "plate"], "mid": [0, -5, 0], "dec": {"kind": "CUBIC", "why": "the keel meets the plate in one curve"}}]
    cur = [{"chain": 0, "sig": ["vane", "spine"], "mid": [10.5, 0, 0]}, {"chain": 1, "sig": ["spine", "vane"], "mid": [0.2, 0, 0]},
           {"chain": 2, "sig": ["keel", "plate"], "mid": [0, -9, 0]}, {"chain": 3, "sig": ["fin", "keel"], "mid": [0, 0, 0]},
           {"chain": 4, "sig": ["CAP", "spine"], "mid": [0, 5, 0]}]
    car, todo = K.carry_lines(prev, cur, 3.0)
    check(car.get("0", {}).get("kind") == "ARC" and car.get("1", {}).get("kind") == "LINE", "each new chain takes the decision of the old one between the same features, nearest middle")
    check(car["0"]["why"] == "the vane's edge is one arc [carried from chain 1]", "the reason is kept, the carry noted once (not stacked)")
    check(sorted(k for k, _ in todo) == [2, 3] and "2" not in car and "4" not in car, "a line 4 mm off and a new pair of features are left TO DECIDE; a cap's chain is not listed")
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
    def run(*a):
        out.clear(); import builtins; p0 = builtins.print; builtins.print = lambda *x, **k: out.append(" ".join(str(y) for y in x))
        try: return KR.cmd(list(a), kit)
        except RuntimeError as ex: return "passed" if "GATES PASSED" in str(ex) else str(ex)
        finally: builtins.print = p0
    w(os.path.join(folder, "piece.stl"), b"\0" * 84); w(os.path.join(folder, "body.brep"), b"a body"); w(os.path.join(folder, "wall_caps.brep"), b"caps")
    B = "BODY=" + os.path.join(folder, "body.brep")
    check(KR.step_defaults("skin-labels", folder, "").get("PICS") == "quick" and KR.step_defaults("skin-wires", folder, "").get("PICS") == "quick"
          and "PICS" not in KR.step_defaults("skin-look", folder, ""), "the runner suggests PICS quick for the loop's steps (skin-look keeps LOOK_MODE)")
    # live layout  skin-labels
    w(os.path.join(sk, "patches_labels_raw.json"), '{"patches": "raw A"}'); w(os.path.join(folder, "tags", "sl1", "patches_labels.json"), '{"patches": "raw A"}')
    w(os.path.join(folder, "tags", "sl0", "patches_labels.json"), '{"patches": "raw OTHER"}')
    json.dump({"_when": "2026-10-07 15:00:00", "_tag": "sl1", "OPEN_MM": "0.5", "BAND": "1.0", "MIRROR": "x 0", "ON_MM": "0.3"}, open(os.path.join(folder, "env_skin-labels_sl1.json"), "w"))
    json.dump({"_when": "2026-10-07 16:00:00", "_tag": "sl0", "OPEN_MM": "0.7", "MIRROR": "x 0"}, open(os.path.join(folder, "env_skin-labels_sl0.json"), "w"))
    w(os.path.join(sk, "patches_labels.json"), '{"patches": "features B", "merge_smooth": {}}'); w(os.path.join(folder, "tags", "sf1", "patches_labels.json"), '{"patches": "features B", "merge_smooth": {}}')
    json.dump({"_when": "2026-10-07 15:10:00", "_tag": "sf1", "MAX_AREA": "3"}, open(os.path.join(folder, "env_skin-features_sf1.json"), "w"))
    pj = os.path.join(sk, "patches.json"); w(pj, '{"patches": [{"patch": 0, "bbox": [0, 1, 0, 1, 0, 1]}]}')
    w(os.path.join(sk, "review", "LAYOUT_01_orbit_045.png"), b"png")
    opened31cb(root, os.path.join(sk, "review", "LAYOUT_01_orbit_045.png"))
    json.dump({"kind": "layout", "frames": ["LAYOUT_01_orbit_045.png"], "md5": md(pj), "pics": "quick", "tag": "sr1"}, open(os.path.join(sk, "review", "LAYOUT_LOOK.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "layout", "--verdict", "ok", "--note", "every face one simple surface, both sides alike, nothing missing"], kit, say)
    check(rc == 2 and "QUICK set" in " ".join(out) and "PICS=full" in " ".join(out), "an ok on a QUICK set is refused - the full set once, then ok")
    check(not os.path.isfile(KR._lock_path(folder)), "... and nothing is locked by a refused judgement")
    json.dump({"kind": "layout", "frames": ["LAYOUT_01_orbit_045.png"], "md5": md(pj), "pics": "full", "tag": "sr1"}, open(os.path.join(sk, "review", "LAYOUT_LOOK.json"), "w"))
    out.clear(); rc = KR.judge(["--job", job, "--what", "layout", "--verdict", "ok", "--note", "every face one simple surface, both sides alike, nothing missing"], kit, say)
    lk = KR.layout_lock(folder) or {}
    check(rc == 0 and lk.get("levers", {}).get("skin-labels", {}).get("OPEN_MM") == "0.5" and lk["levers"]["skin-labels"].get("BAND") == "1.0",
          "the FIRST ok fixes the layout's section-wide levers - from the run that made the live layout (by md5: sl1's 0.5, not the newer sl0's 0.7)")
    check(any("next    :" in l and "skin-mirror" in l and "skin-network" in l for l in out), "31bx R6 F5: the judge names the next step (a layout ok: skin-mirror on a symmetric edit, then skin-network -> skin-frame -> skin-wires)")
    check(lk["levers"].get("skin-features", {}).get("MAX_AREA") == "3" and lk["levers"]["skin-labels"].get("A_NOISE") is None, "the feature map's thresholds too; an unset lever is locked at the script's own value")
    check("skin-rim" in lk.get("not_on_record", []) and "NOT on record" in " ".join(out), "a step whose run is not on record is SAID, never guessed")
    check("FEATURES" not in lk["levers"].get("skin-features", {}), "the feature map (FEATURES) is not locked - the client's question on it is open")
    rc = run("skin-features", "--job", job, "--tag", "sf2", "--set", B, "--set", "MAX_AREA=60")
    check(rc == 2 and "fixed when its first layout was judged ok" in " ".join(out) and "MAX_AREA=60" in " ".join(out), "a different section-wide value after the first ok is refused, by name")
    rc = run("skin-features", "--job", job, "--tag", "sf2", "--set", B)
    check(rc == "passed" and any("locked" in l and "MAX_AREA" in l and "= 3" in l for l in out), "a run without it takes the locked value (printed \"locked\")")
    rc = run("skin-labels", "--job", job, "--tag", "sl2", "--set", B, "--set", "MIRROR=x 0", "--set", "OPEN_MM=0.7")
    check(rc == 2 and "OPEN_MM=0.7" in " ".join(out) and "locked at 0.5" in " ".join(out), "skin-labels' OPEN_MM is held at the first ok's 0.5 (the agent's six re-splits)")
    out.clear(); rc = run("skin-features", "--job", job, "--tag", "sfx", "--set", B, "--set", "FEATURES=no_such_map_31bx.json")
    check(rc == 2 and "names no file in any of the places a relative path is read from" in " ".join(out), "31bx R6 F6: a relative file lever that names no file in any of the places is refused by name (%s)" % " ".join(out)[-160:].replace("\n", " | "))
    rc = run("skin-features", "--job", job, "--tag", "sf3", "--set", B, "--set", "MAX_AREA=3.0")
    check(rc == "passed", "the same value written another way (3.0 for 3) is the same value")
    for i, spot in enumerate(("0 1 0 1 0 1", "4 5 2 3 0 1", "-5 -4 2 3 0 1", "8 9 2 3 0 1", "-9 -8 2 3 0 1")):
        w(pj, '{"patches": [{"patch": 0, "bbox": [0, 1, 0, 1, 0, 1]}], "round": %d}' % i)
        json.dump({"kind": "layout", "frames": ["LAYOUT_01_orbit_045.png"], "md5": md(pj), "pics": "quick", "tag": "sr%d" % (i + 2)}, open(os.path.join(sk, "review", "LAYOUT_LOOK.json"), "w"))
        out.clear(); rc = KR.judge(["--job", job, "--what", "layout", "--verdict", "redo", "--note", "round %d: a face at this place folds over its neighbour" % i, "--spot", spot], kit, say)
    st = KR.restart_state(folder)
    check(rc == 0 and len([s for s in st["spots"] if s.get("locked")]) == 5 and "5 LAYOUT ROUNDS" in " ".join(out) and not st.get("rounds"),
          "31bk: the fifth layout round without a passing build locks EVERY place the rounds named (five different spots - the per-spot count alone never fired)")
    check(KR.restart_refusal(folder, "skin-labels") is not None, "... and every step after skin-points waits for the points there")
    out.clear(); rc = KR.restore_cmd(["--job", job, "--tag", "nothing"], kit, say)
    check(rc == 2 and "no saved state" in " ".join(out), "restore: no saved state for a tag is said")
    w(os.path.join(sk, "network_frame.brep"), "N1"); w(os.path.join(sk, "piece_skin.brep"), "S1")
    w(os.path.join(sk, "review", "WIRES_JUDGED.json"), json.dumps({"verdict": "ok", "md5": md(os.path.join(sk, "network_frame.brep"))}))
    files = KR.save_state(folder, "b1", say)
    check({"patches.json", "network_frame.brep", "piece_skin.brep", "review/WIRES_JUDGED.json"} <= set(files) and os.path.isfile(os.path.join(folder, "tags", "b1", "STATE.json")),
          "a build's state: the layout, the wires, the piece and the verdicts on them (tags\\b1\\STATE.json)")
    out.clear(); rc = KR.restore_cmd(["--job", job, "--tag", "b1"], kit, say)
    check(rc == 2 and "points are owed" in " ".join(out), "restore is refused while the points are owed at a spot (it would bring back the points being replaced)")
    st["spots"] = []; KR._restart_save(folder, st)
    p_live = open(pj).read(); w(pj, '{"patches": "a later layout"}'); w(os.path.join(sk, "piece_skin.brep"), "S2"); w(os.path.join(sk, "features.json"), '{"later": [1]}')
    out.clear(); rc = KR.restore_cmd(["--job", job, "--tag", "b1"], kit, say)
    lives = [d for d in os.listdir(os.path.join(folder, "tags")) if d.startswith("_live_")]
    check(rc == 0 and open(pj).read() == p_live and open(os.path.join(sk, "piece_skin.brep")).read() == "S1", "restore puts the build's layout and piece back")
    check(not os.path.isfile(os.path.join(sk, "features.json")), "a file the saved state did not have is removed (no file of another build stays as this one's)")
    check(lives and "features.json" in json.load(open(os.path.join(folder, "tags", lives[0], "STATE.json")))["files"], "the live state is kept first (tags\\_live_*) - a restore can be undone")
    check(json.load(open(os.path.join(sk, "review", "WIRES_JUDGED.json")))["verdict"] == "ok" and "verdicts it carried came back" in " ".join(out), "the verdicts on those artefacts come back with them (md5-bound)")
    n_store = len(os.listdir(os.path.join(folder, "tags", "_states"))); KR.save_state(folder, "b2", say)
    check(len(os.listdir(os.path.join(folder, "tags", "_states"))) == n_store, "a file shared by builds is stored once (content-addressed)")
    KR.record_round(folder, "m1", [[0, 1, 0, 1, 0, 1]], "one round", say)
    out.clear(); KR.rounds_reset(folder, say)
    check(not KR.restart_state(folder).get("rounds") and "start again" in " ".join(out), "a build that passes starts the layout rounds again")
    w(pj, '{"patches": [{"patch": 0, "bbox": [0, 1, 0, 1, 0, 1]}], "round": "ok"}')
    json.dump({"kind": "layout", "frames": ["LAYOUT_01_orbit_045.png"], "md5": md(pj), "pics": "full", "tag": "sr9"}, open(os.path.join(sk, "review", "LAYOUT_LOOK.json"), "w"))
    out.clear(); KR.judge(["--job", job, "--what", "layout", "--verdict", "ok", "--note", "every face one simple surface, both sides alike, nothing missing"], kit, say)
    outside = os.path.join(root, "Deliverables", "R33", "review", "x.png"); w(outside, b"png")
    out.clear(); rc = KR.judge(["--job", job, "--what", "layout", "--verdict", "redo", "--frame", outside, "--note", "the keel end's face is a bulb on this picture, seen from below", "--face", "0"], kit, say)
    check(rc == 2 and "THE PICTURE MUST BE THE JOB'S" in " ".join(out), "a --frame outside the job's picture folder does not count - the folder is named (Deliverables is the client's)")
    if os.path.isfile(os.path.join(root, ".claude", "dumdum.json")):
        st_ = json.load(open(os.path.join(root, ".claude", "dumdum.json"))); st_["owed"] = None; json.dump(st_, open(os.path.join(root, ".claude", "dumdum.json"), "w"))
    inside = os.path.join(sk, "review", "look", "look_1.png"); w(inside, b"png")
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), "hooks")); import lookgate as LG
    time.sleep(1.1)
    with open(os.path.join(root, ".claude", "looks.jsonl"), "a") as fh: fh.write(json.dumps({"png": inside, "png_n": LG._norm(inside), "opened": time.time()}) + "\n")
    out.clear(); rc = KR.judge(["--job", job, "--what", "layout", "--verdict", "redo", "--frame", "look\\look_1.png" if os.sep == "\\" else "look/look_1.png",
                               "--note", "the keel end's face is a bulb on this picture, seen from below", "--face", "0"], kit, say)
    check(rc == 0, "a look_at picture in the job's folder, opened after the ok, overturns it (cited as look\\<name>.png)")
    class KitRun(Kit):
        def _wallclock(self): return None
        def _judge_output(self, o, rc, log, name): return rc
        def cmd_clock(self, a): pass
        def sh(self, cmdline, cap, log, env, cwd=None, outputs=None): return 0, "MIRROR CHECK PASS: every face of the piece has its mirror partner"
    kr = KitRun(root); kr.ENV = {"min_free_gb": 0.0}
    def run2(*a):
        out.clear(); import builtins; p0 = builtins.print; builtins.print = lambda *x, **k: out.append(" ".join(str(y) for y in x))
        try: return KR.cmd(list(a), kr)
        finally: builtins.print = p0
    rc = run2("skin-mirror", "--job", job, "--tag", "m1", "--set", B, "--set", "WHAT=piece")
    check(rc == 2 and "THE LOOK FIRST" in " ".join(out), "31az: the piece mirror check is refused until the quick look is judged ok")
    os.makedirs(os.path.join(sk, "review"), exist_ok=True)
    for f_ in ("SKIN_look_01_orbit_045.png",): open(os.path.join(sk, "review", f_), "wb").write(b"png")
    json.dump({"kind": "skin", "frames": ["SKIN_look_01_orbit_045.png"], "md5": md(os.path.join(sk, "piece_skin.brep")), "mode": "quick", "mesh_quality": {"defective": False, "cracks": 0}}, open(os.path.join(sk, "review", "PIECE_LOOK.json"), "w"))
    json.dump({"what": "look", "verdict": "ok", "md5": md(os.path.join(sk, "piece_skin.brep")), "when": time.strftime("%Y-%m-%d %H:%M:%S"), "note": "selftest"}, open(os.path.join(sk, "review", "LOOK_JUDGED.json"), "w"))
    rc = run2("skin-mirror", "--job", job, "--tag", "m1", "--set", B, "--set", "WHAT=piece")
    check(rc == 0 and any("next" in l and "PASS - the piece is its own mirror" in l and "TRIAL" in l for l in out), "after a piece mirror check that passes, the next line is the TRIAL")
    rc = run2("skin-mirror", "--job", job, "--tag", "m2", "--set", B, "--set", "WHAT=layout")
    check(rc == 0 and any("next" in l and "skin-network" in l for l in out), "after a layout mirror check that passes, the next line is skin-network")
    stl = os.path.join(folder, "box.stl"); tri = []
    P = np.array([[x, y, z] for x in (0, 4) for y in (0, 4) for z in (0, 2)], float)
    for a, b_, c in ((0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)):
        tri.append((P[a], P[b_], P[c]))
    rec = np.zeros(len(tri), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])); rec["v"] = np.array(tri, np.float32)
    with open(stl, "wb") as fh: fh.write(b"\0" * 80 + np.uint32(len(tri)).tobytes() + rec.tobytes())
    e = dict(os.environ); e.update({"KIT_HOME": HERE, "BOX": "1 2 1 2 0 2", "SHAPE": stl, "CC_OUTDIR": folder, "PYTHONIOENCODING": "utf-8"})
    p = subprocess.run([sys.executable, os.path.join(os.path.dirname(HERE), "tools", "look_at.py")], env=e, capture_output=True, text=True, timeout=120, cwd=folder)
    pics = [f for f in os.listdir(os.path.join(sk, "review", "look")) if f.startswith("look_") and f != "look_1.png"]
    check(p.returncode == 0 and len(pics) == 1, "look_at writes its picture in the job's picture folder (skin\\review\\look\\) [%s]" % (p.stdout + p.stderr).strip()[-120:])
    if pics:
        from PIL import Image
        im = np.asarray(Image.open(os.path.join(sk, "review", "look", pics[0])).convert("RGB")).reshape(-1, 3).astype(int)
        warm = np.sum((np.abs(im[:, 0] - im[:, 2]) > 70) & (im[:, 0] > 150) & (im[:, 1] > 100) & (im[:, 1] < 200))
        yellow = np.sum((im[:, 0] > 230) & (im[:, 1] > 200) & (im[:, 2] < 80))
        check(yellow > 50, "the subject is the yellow OUTLINE of its box (%d px)" % yellow)
        check(warm < 0.2 * yellow, "no band of warm triangles - the shape is one colour (%d warm px)" % warm)
    import kit_deliver as KD
    class DKit:
        ROOT = root; G = G
        @staticmethod
        def _opt(args, name, default=None): return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default
        @staticmethod
        def _flag(args, name): return name in args
    tpl = os.path.join(root, "tpl.FCStd"); w(tpl, b"zip")
    out.clear(); import builtins; p0 = builtins.print; builtins.print = lambda *x, **k: out.append(" ".join(str(y) for y in x))
    try:
        rc1 = KD.cmd(["R33", "--template", tpl, "--target", "Body", "--model", os.path.join(folder, "body.brep"), "--trial", "yes"], DKit())
        o1 = " ".join(out); out.clear()
        rc2 = KD.cmd(["R33", "--template", tpl, "--target", "Body", "--trial", "the client: send me the trial model of a section to open"], DKit())
        o2 = " ".join(out)
    finally:
        builtins.print = p0
    check(rc1 == 2 and "the client's request in the client's words" in o1, "kit deliver --trial is refused without the client's request in the client's words")
    check(rc2 == 2 and "body_trial.brep" in o2, "kit deliver --trial is refused without the trial's body (--model) - never the model of record")
    _cases = [("R33_X", "X"), ("R33__X", "X"), ("_R33_X", "X"), ("R33 _X", "X"), ("R33_-R33_X", "X"), ("r33-r33_MYPART", "MYPART"), ("MYPART", "MYPART"), ("R930_X", "R930_X")]
    _bad = [(a_, KD._stem(a_, "R33"), b_) for a_, b_ in _cases if KD._stem(a_, "R33") != b_]
    check(not _bad, "31bq TT (B35): the stem drops the REV however it was written, and only the REV (R930_X kept) %s" % (_bad or ""))
    _n1, _s1 = KD._deliver_name("R33", "R33", os.path.join(root, "R33_MYPART")); _n2, _s2 = KD._deliver_name("R33_", "R33", os.path.join(root, "r33")); _n3, _s3 = KD._deliver_name("", "R33", os.path.join(root, "MYPART"))
    check(_n1 == "MYPART" and "REV alone" in _s1 and _n2 == "MODEL" and _n3 == "MYPART" and _s3 == "", "31bq TT (B35): a bare-REV --name falls to the project's name, stripped too (R33_MYPART -> the project, never R33_R33_MYPART) and SAID; no --name says nothing (%r %r %r)" % (_n1, _n2, _n3))
    # thumbnails/Thumbnail.png
    import zipfile as _zf
    _dx = ('<?xml version="1.0" encoding="utf-8"?>\n<Document SchemaVersion="4">\n    <Objects Count="1" Dependencies="1">\n        <ObjectDeps Name="Body" Count="0"/>\n'
           '        <Object type="Part::Feature" name="Body" id="1" />\n    </Objects>\n    <ObjectData Count="1">\n        <Object name="Body">\n'
           '            <Properties Count="2" TransientCount="0">\n                <Property name="Shape" type="Part::PropertyPartShape" status="1">\n'
           '                    <Part file="Body.Shape.brp"/>\n                </Property>\n                <Property name="Visibility" type="App::PropertyBool" status="1">\n'
           '                    <Bool value="true"/>\n                </Property>\n            </Properties>\n        </Object>\n    </ObjectData>\n</Document>\n')
    _gx = ('<?xml version="1.0" encoding="utf-8"?>\n<Document SchemaVersion="1">\n    <ViewProviderData Count="1">\n        <ViewProvider name="Body" expanded="0" treeRank="1">\n'
           '            <Properties Count="1" TransientCount="0">\n                <Property name="Visibility" type="App::PropertyBool" status="1">\n'
           '                    <Bool value="true"/>\n                </Property>\n            </Properties>\n        </ViewProvider>\n    </ViewProviderData>\n</Document>\n')
    def _tz(p_, extra_):
        with _zf.ZipFile(p_, "w") as z_:
            z_.writestr("Document.xml", _dx); z_.writestr("GuiDocument.xml", _gx); z_.writestr("Body.Shape.brp", "brep"); z_.writestr("thumbnails/Thumbnail.png", b"\x89PNG")
            for n_ in extra_: z_.writestr(n_, b"x")
    _shp = os.path.join(root, "shape_tf5.brep"); w(_shp, b"brep v2")
    _t5a = os.path.join(root, "tpl_thumb.FCStd"); _t5b = os.path.join(root, "tpl_thumb_foo.FCStd"); _tz(_t5a, []); _tz(_t5b, ["foo.png"])
    # thumbnail  thumbnail
    # thumbnail
    # recorded
    _has5 = True; _said5 = []
    try: _r5a = KD.build(_t5a, _shp, os.path.join(root, "out_tf5a.FCStd"), "Body", say=lambda *a_: _said5.append(" ".join(str(x_) for x_ in a_)), camera=None); _e5a = ""
    except RuntimeError as _ex5: _r5a = None; _e5a = str(_ex5)
    try: KD.build(_t5b, _shp, os.path.join(root, "out_tf5b.FCStd"), "Body", say=lambda *a_: None, camera=None); _e5b = ""
    except RuntimeError as _ex5: _e5b = str(_ex5)
    if _r5a is not None:
        with _zf.ZipFile(os.path.join(root, "out_tf5a.FCStd")) as _zq: _has5 = "thumbnails/Thumbnail.png" in _zq.namelist(); _n5 = sorted(_zq.namelist())
    check(_r5a is not None and not _has5 and (_r5a or {}).get("thumbnail_dropped") == ["thumbnails/Thumbnail.png"] and "DROPPED" in str((_r5a or {}).get("thumbnail")) and any("thumbnail" in l_ and "DROPPED" in l_ for l_ in _said5),
          "R7W fix-small (F.6): the template delivers (its thumbnail is no orphan) and the delivery holds NO thumbnails/Thumbnail.png - the previous model's picture dropped, said and recorded %s" % (_e5a[:120] or ""))
    _t5c = os.path.join(root, "tpl_nothumb.FCStd")
    with _zf.ZipFile(_t5c, "w") as z_: z_.writestr("Document.xml", _dx); z_.writestr("GuiDocument.xml", _gx); z_.writestr("Body.Shape.brp", "brep")
    try: _r5c = KD.build(_t5c, _shp, os.path.join(root, "out_tf5c.FCStd"), "Body", say=lambda *a_: None, camera=None)
    except RuntimeError as _ex5: _r5c = {"err": str(_ex5)}
    check((_r5c or {}).get("thumbnail_dropped") == [] and (_r5c or {}).get("thumbnail") == "none in the template", "R7W fix-small (F.6): a template with no thumbnail delivers and records 'none in the template' (%s)" % str(_r5c)[:120])
    check("orphan" in _e5b and "foo.png" in _e5b and "Thumbnail" not in _e5b, "...and an unreferenced foo.png is still an orphan, refused by name (%s)" % _e5b[:120])
    # HasherIndex
    import kit_place as KP
    _p1 = KP.placement((10, 20, 30), (1, 0, 0, -90)); _r1 = KP._rot((1.0, 0.0, 0.0), -90, (0.0, 1.0, 0.0)); _r2 = KP._rot((1.0, 0.0, 0.0), -90, (0.0, 0.0, 1.0))
    check(tuple(round(x, 6) for x in _p1["base"]) == (10.0, 20.0, 30.0) and round(_p1["q"][3], 4) == 0.7071 and round(_p1["q"][0], 4) == -0.7071
          and tuple(round(x, 6) for x in _r1) == (0.0, 0.0, -1.0) and tuple(round(x, 6) for x in _r2) == (0.0, 1.0, 0.0),
          "31br B5: -90 deg about X turns y to -Z and z to +Y (a fixture's boards' PCBA -> fixture frame), the quaternion (x, y, z, w) = (-0.7071, 0, 0, 0.7071), the base the translation")
    _p2 = KP.placement((0, 0, 0), (0, 0, 1, 90), (10, 0, 0))
    check(tuple(round(x, 6) for x in _p2["base"]) == (10.0, -10.0, 0.0), "31br B5: a turn about a point off the origin folds into the base (90 about z through (10, 0, 0) -> base (10, -10, 0)) %s" % (_p2["base"],))
    _x1 = KP.xml_placement(_p1); _pb = KP.parse_xml_placement(_x1)
    check('Px="10.0000000000000000"' in _x1 and 'A="-1.5707963267948966"' in _x1 and 'Ox="1.0000000000000000"' in _x1 and _pb is not None
          and tuple(round(x, 6) for x in _pb["base"]) == (10.0, 20.0, 30.0) and round(abs(_pb["angle_deg"]), 3) == 90.0 and round(abs(_pb["axis"][0]), 6) == 1.0,
          "31br B5: the PropertyPlacement XML in FreeCAD's form (Px.., Q0..Q3, A in radians, O the axis) and read back to the same numbers")
    check(KP.is_identity(KP.placement()) and KP.IDENTITY_XML.count('"0.0000000000000000"') == 9 and 'Q3="1.0000000000000000"' in KP.IDENTITY_XML, "31br B5: the identity XML (Q3 = 1, the axis z)")
    _pf = KP.parse_place_field("place=1,2,3,0,0,1,90"); _pf3 = KP.parse_place_field("1,2,3"); _pf10 = KP.parse_place_field("place=0,0,0,0,0,1,90,10,0,0")
    check(tuple(_pf["translate"]) == (1.0, 2.0, 3.0) and _pf["angle_deg"] == 90.0 and _pf3["rotate"] is None and tuple(_pf3["base"]) == (1.0, 2.0, 3.0) and tuple(round(x, 6) for x in _pf10["base"]) == (10.0, -10.0, 0.0),
          "31br B5: place= takes 3, 7 or 10 numbers (translate; + axis and degrees; + the point)")
    _e1 = _e2 = _e3 = ""
    try: KP.parse_place_field("place=1,2")
    except ValueError as _ex: _e1 = str(_ex)
    try: KP.parse_place_field("place=a,b,c")
    except ValueError as _ex: _e2 = str(_ex)
    try: KP.placement((0, 0, 0), (0, 0, 0, 45))
    except ValueError as _ex: _e3 = str(_ex)
    check("got 2" in _e1 and "takes numbers" in _e2 and "zero vector" in _e3, "31br B5: a wrong count, a non-number and a zero axis are refused by name (%s | %s | %s)" % (_e1[:40], _e2[:40], _e3[:40]))
    _pj = KP.parse_place_json({"translate": [-44.15, 65.14, 96.20], "rotate": [1, 0, 0, -90]})
    check(tuple(_pj["base"]) == (-44.15, 65.14, 96.2) and _pj["angle_deg"] == -90.0 and KP.parse_place_json(None) is None and KP.parse_place_json({}) is None, "31br B5: the JSON form {translate, rotate, about} (the second project's own numbers)")
    _bp = os.path.join(root, "b1.brep"); w(_bp, "brep one"); _bs = os.path.join(root, "m1.stl"); w(_bs, b"\0" * 84)
    _bl = KD._parse_bodies("B1|first body|%s|1|10,20,30|G9;B2|second (placed)|%s|0|1,2,3|G9|place=1,2,3,0,0,1,90" % (_bp, _bp))
    check(len(_bl) == 2 and _bl[0]["place"] is None and _bl[0]["place_xml"] is None and _bl[1]["place"]["angle_deg"] == 90.0 and _bl[1]["place_xml"].startswith("<PropertyPlacement") and "rotate 90.00 deg" in _bl[1]["place_desc"] and _bl[1]["vis"] is False,
          "31br B2: --add-body specs parse - six fields, or seven with place= last; the placement's XML and words ride the spec")
    _eb = {}
    for _k, _s in (("stl", "B3|x|%s|1|1,2,3|G9" % _bs), ("missing", "B4|x|%s|1|1,2,3|G9" % os.path.join(root, "nope.brep")), ("fields", "B5|x|%s|1|1,2,3" % _bp), ("place", "B6|x|%s|1|1,2,3|G9|place=1,2" % _bp), ("name", "B 7|x|%s|1|1,2,3|G9" % _bp)):
        try: KD._parse_bodies(_s); _eb[_k] = ""
        except ValueError as _ex: _eb[_k] = str(_ex)
    check("a body is a .brep" in _eb["stl"] and "no file at" in _eb["missing"] and "six fields" in _eb["fields"] and "got 2" in _eb["place"] and "letters, digits and _" in _eb["name"],
          "31br B2: an .stl body, a missing file, a short spec, a bad place= and a bad name are refused by name %s" % {k: v[:40] for k, v in _eb.items()})
    _ml = KD._parse_meshes("M1|lab|%s|1|1,2,3|G9|place=5,6,7" % _bs)
    check(len(_ml) == 1 and tuple(_ml[0]["place"]["base"]) == (5.0, 6.0, 7.0) and 'Px="5.0000000000000000"' in _ml[0]["place_xml"], "31br B5: a --mesh spec takes place= as its seventh field")
    _jf = os.path.join(root, "specs_b2.json"); w(_jf, json.dumps({"meshes": [], "groups": [{"name": "G8", "label": "eight"}], "bodies": [{"name": "J1", "label": "a; label | with delimiters", "path": _bp, "shown": True, "rgb": [9, 8, 7], "group": "G8", "place": {"translate": [1, 1, 1], "rotate": [0, 1, 0, 30]}}]}))
    _jm, _jg, _jb = KD._parse_mesh_file(_jf)
    check(_jm == [] and _jg == [("G8", "eight")] and len(_jb) == 1 and _jb[0]["label"] == "a; label | with delimiters" and _jb[0]["place"]["angle_deg"] == 30.0, "31br B2: the JSON form carries \"bodies\" with any label and a place object")
    # collides
    _tb = os.path.join(root, "tpl_bodies.FCStd")
    with _zf.ZipFile(_tb, "w") as z_: z_.writestr("Document.xml", _dx); z_.writestr("GuiDocument.xml", _gx); z_.writestr("Body.Shape.brp", "brep")
    _bl2 = KD._parse_bodies("B1|first body|%s|1|10,20,30|G9;B2|second (placed)|%s|0|1,2,3|G9|place=1,2,3,0,0,1,90" % (_bp, _bp))
    _said_b = []
    try: _rb = KD.build(_tb, None, os.path.join(root, "out_bodies.FCStd"), "", say=lambda *a_: _said_b.append(" ".join(str(x_) for x_ in a_)), camera=None, groups=[("G9", "nine")], bodies=_bl2); _eb2 = ""
    except RuntimeError as _ex: _rb = None; _eb2 = str(_ex)
    _ok_b = False
    if _rb is not None:
        with _zf.ZipFile(os.path.join(root, "out_bodies.FCStd")) as _zq:
            _n = _zq.namelist(); _d = _zq.read("Document.xml").decode("utf-8"); _g = _zq.read("GuiDocument.xml").decode("utf-8"); _pay = _zq.read("BODY_B1.brp")
        import xml.etree.ElementTree as _ET; _ET.fromstring(_d); _ET.fromstring(_g)
        _b2blk = _d[_d.find('<Object name="B2"'):]; _b2blk = _b2blk[:_b2blk.find("</Object>")]
        _ok_b = ("BODY_B1.brp" in _n and "BODY_B2.brp" in _n and _pay == b"brep one" and '<Object type="Part::Feature" name="B1"' in _d and '<Object type="Part::Feature" name="B2"' in _d
                 and '<Objects Count="4"' in _d and '<ObjectData Count="4"' in _d and '<ViewProviderData Count="4"' in _g and KP.xml_placement(_bl2[1]["place"]) in _b2blk
                 and '<Bool value="false"/>' in _b2blk and re.search(r'<ViewProvider name="B1".*?<PropertyColor value="%d"/>' % ((10 << 24) | (20 << 16) | (30 << 8) | 255), _g, re.S) is not None
                 and re.search(r'<Object name="G9".*?<Link value="B1"/>.*?<Link value="B2"/>', _d, re.S) is not None and _rb.get("bodies") == ["B1", "B2"] and _rb.get("groups") == ["G9"]
                 and any("placed: rotate 90.00 deg" in l_ for l_ in _said_b) and any("the brep's own location" in l_ for l_ in _said_b))
    check(_ok_b, "31br B2: two bodies appended by zip surgery - their payload entries, Part::Feature blocks in the GUI's form, the counts (Body + 2 + the group), the placed one's XML Placement, hidden in both files, the colour as ShapeColor, both linked by the new group, said %s" % (_eb2[:160] or ""))
    _dupe = KD._parse_bodies("Body|collides|%s|1|1,2,3|G9" % _bp)
    try: KD.build(_tb, None, os.path.join(root, "out_dupe.FCStd"), "", say=lambda *a_: None, camera=None, groups=[("G9", "nine")], bodies=_dupe); _ed = ""
    except RuntimeError as _ex: _ed = str(_ex)
    check("collides" in _ed, "31br B2: a body named like a template object is refused (%s)" % _ed[:80])
    try: KD.build(_tb, None, os.path.join(root, "out_none.FCStd"), "", say=lambda *a_: None, camera=None); _en = ""
    except RuntimeError as _ex: _en = str(_ex)
    check("--add-body" in _en, "31br B2: nothing to deliver names --add-body beside --target and --mesh (%s)" % _en[:80])
    # HasherIndex
    _dxh = _dx.replace('<Part file="Body.Shape.brp"/>', '<Part HasherIndex="0" ElementMap="15.70200.5" file="Body.Shape.brp"/>').replace(
        '                <Property name="Visibility" type="App::PropertyBool" status="1">\n                    <Bool value="true"/>\n                </Property>\n            </Properties>\n        </Object>',
        '                <Property name="Visibility" type="App::PropertyBool" status="1">\n                    <Bool value="true"/>\n                </Property>\n                <Property name="Placement" type="App::PropertyPlacement" status="8388608">\n                    '
        + KP.xml_placement(KP.placement((0, -22, 0))) + '\n                </Property>\n            </Properties>\n        </Object>').replace('<Properties Count="2" TransientCount="0">\n                <Property name="Shape"', '<Properties Count="3" TransientCount="0">\n                <Property name="Shape"')
    _th = os.path.join(root, "tpl_hasher.FCStd")
    with _zf.ZipFile(_th, "w") as z_: z_.writestr("Document.xml", _dxh); z_.writestr("GuiDocument.xml", _gx); z_.writestr("Body.Shape.brp", "brep")
    _tp = KD._template_placement(_th, "Body")
    check(_tp is not None and tuple(round(x, 6) for x in _tp["base"]) == (0.0, -22.0, 0.0) and not KP.is_identity(_tp) and KD._template_placement(_th, "Nope") is None,
          "31br B5: the template body's own Placement is read (REF_CONVERTER's Py -22 form); an absent object gives None")
    try:
        _rh = KD.build(_th, _shp, os.path.join(root, "out_hasher.FCStd"), "Body", say=lambda *a_: None, camera=None, target_place_xml=KP.IDENTITY_XML); _eh = ""
        with _zf.ZipFile(os.path.join(root, "out_hasher.FCStd")) as _zq: _dh = _zq.read("Document.xml").decode("utf-8"); _bh = _zq.read("Body.Shape.brp")
    except RuntimeError as _ex: _rh = None; _eh = str(_ex); _dh = ""; _bh = b""
    check(_rh is not None and '<Part file="Body.Shape.brp"/>' in _dh and "HasherIndex" not in _dh and _bh == b"brep v2" and KP.IDENTITY_XML in _dh and 'Py="-22.' not in _dh,
          "31br B2 / B5: a body whose Part tag starts with HasherIndex is swapped (the live kit had refused it as 'not a Part::Feature'); --drop-placement writes the identity XML (%s)" % _eh[:100])
    class PKit:
        ROOT = root
        @staticmethod
        def _opt(args, name, default=None): return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default
        @staticmethod
        def _flag(args, name): return name in args
    out.clear(); builtins.print = lambda *x, **k: out.append(" ".join(str(y) for y in x))
    try:
        _k1 = KP.cmd([_bp, "--translate", "1", "2", "3"], PKit()); _o1 = " ".join(out); out.clear()
        _k2 = KP.cmd([_bp, "--out", os.path.join(root, "b1_placed.brep")], PKit()); _o2 = " ".join(out); out.clear()
        _k3 = KP.cmd([_bp, "--out", os.path.join(root, "b1_placed.brep"), "--rotate", "1 0 0"], PKit()); _o3 = " ".join(out); out.clear()
        _k4 = KP.cmd([_bp, "--out", os.path.join(root, "b1_placed.stl"), "--translate", "1", "2", "3"], PKit()); _o4 = " ".join(out); out.clear()
        _k5 = KP.cmd([_bp, "--out", _bp, "--translate", "1", "2", "3"], PKit()); _o5 = " ".join(out); out.clear()
    finally:
        builtins.print = p0
    check(_k1 == 2 and "--out" in _o1 and _k2 == 2 and "nothing to do" in _o2 and _k3 == 2 and "four numbers" in _o3 and _k4 == 2 and "keeps the input's kind" in _o4 and _k5 == 2 and "the input itself" in _o5,
          "31br B5: kit place refuses - no --out, no move, a three-number --rotate, a kind change, the input as its own output - each by name, before any kernel")
    _pr, _pk = KP.record(root, os.path.join(root, "claude_code", "jobs", "J", "x_placed.brep"), {"from": "a", "why": "test"})
    _prd = json.load(open(_pr, encoding="utf-8"))
    check(_pr == os.path.join(root, "claude_code", "PLACEMENTS.json") and _pk == "claude_code/jobs/J/x_placed.brep" and _prd[_pk]["why"] == "test", "31br B5: the frame map claude_code\\PLACEMENTS.json, one row per placed file, keyed by its path under the project")
    import re as _re_b5; _tm = open(os.path.join(HERE, "templates", "t_move.py"), encoding="utf-8").read(); _kl = open(os.path.join(HERE, "kitlib.py"), encoding="utf-8").read()
    check("rot_axis=" in _tm and "rot_deg=" in _tm and "rot_about=" in _tm and "K.place(" in _tm and "def rotate(shape, axis, deg, about" in _kl and "def place(shape, dx" in _kl, "31br B5: t_move turns first then moves through kitlib.place; kitlib.rotate exists")
    _md = open(os.path.join(HERE, "mesh", "_ccmeshdoc.py"), encoding="utf-8").read()
    check("CC_MESHES_JSON" in _md and 'os.environ["CC_MESHES"]' in _md, "31br B3: the mesh document reads its specs as JSON (any label) and still takes the old form")
    sw = open(os.path.join(HERE, "rebuild", "sk_wires.py"), encoding="utf-8").read(); sb = open(os.path.join(HERE, "rebuild", "sk_build.py"), encoding="utf-8").read()
    check("K.carry_lines(" in sw and "LINES_carried.json" in sw and "_network_md5" in sw, "skin-wires carries the decisions to a new numbering (LINES_carried.json)")
    check("fit_bspline(Cp, 4)" in sw and "ON_TOL" in sw and "_apply_demotions" in sw and "wires_demote.json" in sw, "skin-wires: a decided line on an original face is ONE span, or the face leaves its surface - said")
    check("network_frame_md5" in sb and 'kind[i] == "orig"' in sb and "check_faces" in sb, "skin-build reads the demotions for THIS wireframe only and names the faces failing check(True)")
    for f in ("sk_labels.py", "sk_rim.py", "sk_features.py"):
        check("K.BORDER_NOTE" in open(os.path.join(HERE, "rebuild", f), encoding="utf-8").read(), "%s captions its borders as the voxel's" % f)
    check('pics="full"' in open(os.path.join(HERE, "rebuild", "sk_look.py"), encoding="utf-8").read(), "skin-look's set is LOOK_MODE's, never PICS")
    # skin-wires
    sl_ = open(os.path.join(HERE, "rebuild", "sk_look.py"), encoding="utf-8").read(); sli_ = open(os.path.join(HERE, "rebuild", "sk_lib.py"), encoding="utf-8").read()
    check("T[sel]" not in sl_ and "VT=(V, T[sel])" not in sl_, "skin-look's face frames never cut the mesh by centroid (31bl: the cut drew shards)")
    check("LOOK_ANG" in sl_ and "ang=(LOOK_ANG" in sl_, "skin-look tessellates the piece with an angular deflection (LOOK_ANG)")
    check("ang=None" in open(os.path.join(HERE, "kitlib_render.py"), encoding="utf-8").read() and "AngularDeflection" in open(os.path.join(HERE, "kitlib_render.py"), encoding="utf-8").read(), "tess_shape takes an angular deflection (31bl)")
    check("VIEW_OF_STEP = {" in sli_ and all(k_ in sli_ for k_ in ("skin-points", "skin-wires", "skin-mirror", "SKIN_look face iso", "review_body")), "sk_lib.VIEW_OF_STEP names the locked view of every picture set")
    check("K.view_occluded(" in sw, "skin-wires draws the OCCLUDED wireframe (the locked view)")
    # over the
    Vf_ = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [1, 0, 1], [1, 1, 1]], float)
    Tf_ = np.array([[0, 1, 2], [0, 2, 3], [1, 4, 5], [1, 5, 2]])
    own_ = np.array([True, True, False, False]); Ps_ = Vf_[Tf_[:2]].mean(1)
    check(abs(K.visible_fraction(Vf_, Tf_, own_, Ps_, (0, 0, -1)) - 1.0) < 1e-9, "visible_fraction: the floor seen from above - all of it")
    check(K.visible_fraction(Vf_, Tf_, own_, Ps_, K._unit(np.array([-1.0, 0.0, -0.3]))) == 0.0, "visible_fraction: the floor from the +x side, low over the wall - none of it")
    check(abs(K.visible_fraction(Vf_, Tf_, own_, Ps_, K._unit(np.array([1.0, 0.0, -0.3]))) - 1.0) < 1e-9, "visible_fraction: the floor from the -x side - all of it")
    check(len(K.iso_dirs4(np.array([0, 0, 1.0]), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]))) == 4 and K.iso_dirs4(np.array([0, 0, 1.0]), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]))[:2] == K.iso_dirs(np.array([0, 0, 1.0]), np.array([1.0, 0, 0]), np.array([0, 1.0, 0])), "iso_dirs4: the four corners of the face's frame, iso_dirs its first two")
    check("K.visible_fraction(" in sl_ and "K.iso_dirs4(" in sl_ and "LOOK_VIS" in sl_ and "_blocked" not in sl_, "skin-look picks the face frame's corners by what they SEE (visible_fraction, LOOK_VIS), never by a one-ray probe")
    check("A FILLET NEEDS ROOM" in sb and "does not choose" in sb and "FILLET ROOM on line" in sw and "A FILLET NEEDS ROOM" in sw, "the room rule is said as the one CAD-generic instruction where a fillet is decided (skin-wires) and where it is made (skin-build)")
    check("TAPER_ENDS" in sb and "K.taper_weights(" in sb and "NO CREASE" in sb and "progress=" in sb and '"nurbs_why": (None if kind_ == "nurbs"' in sb, "31bm: the blend tapers to the junction, a border that is no crease is refused, every span rung prints, the NURBS reason is kept on the success path")
    check("NO CREASE AS BUILT" in sb and "fillet_creases.json" in sb and "thn_" in sb, "31bm: the crease is measured on the BUILT faces at the kernel stage and told to the lines pass; the width rule's margin tapers with the blend")
    check("K.taper_weights(" in sw and "NO CREASE" in sw, "31bm: the wires' room line tapers and refuses a border that is no crease")
    check("LINES REASON CHECK" in sw and "keyed to the WRONG CHAIN" in sw, "31bm: a LINES reason is checked against the chain it is keyed to")
    check('.endswith(".brep")' in open(os.path.join(os.path.dirname(HERE), "tools", "diag_section.py"), encoding="utf-8").read() and "MeshPart" in open(os.path.join(os.path.dirname(HERE), "tools", "diag_section.py"), encoding="utf-8").read(), "31bm: diag_section sections a .brep (tessellated) and refuses an unknown kind")
    check("progress=None" in open(os.path.join(HERE, "rebuild", "sk_span.py"), encoding="utf-8").read(), "sk_span.span_face takes a progress callback")
    _Vt = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], float); _Tt = np.array([[0, 2, 1], [0, 1, 3], [1, 2, 3], [0, 3, 2]])
    _q = K.mesh_quality(_Vt, _Tt, np.arange(4), closed=True); check(_q["cracks"] == 0 and _q["facet_p99_deg"] == 0 and not _q["defective"], "mesh_quality: a closed tetrahedron of four faces - no crack, no facet inside a face")
    _q = K.mesh_quality(_Vt, _Tt[:3], np.arange(3), closed=True); check(_q["cracks"] == 3 and _q["defective"] and "crack" in _q["why"], "mesh_quality: a triangle missing from a closed solid = 3 crack edges, DEFECTIVE")
    _q = K.mesh_quality(_Vt, _Tt, np.zeros(4, int), closed=True); check(_q["facet_p99_deg"] > 50 and not _q["defective"], "mesh_quality: the tetra as one face - its facets measured (90 / 54.7 deg), not a defect by themselves (the surface check judges coarseness)")
    _Vs = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], float); _q = K.mesh_quality(_Vs, np.array([[0, 1, 2], [0, 2, 3]]), np.zeros(2, int), closed=False, judge_open=False)
    check(_q["cracks"] == 0 and _q["open_edges"] == 4 and _q["facet_p99_deg"] == 0 and not _q["defective"], "mesh_quality: an open flat sheet with an unknown rim (judge_open=False) - its 4 open edges counted, no crack, facets 0")
    check("def view_piece(" in sli_ and "def piece_mesh(" in sli_ and "K.view_piece(" in sl_ and "K.piece_mesh(" in sl_, "31bn: skin-look draws every frame with THE PIECE VIEW on the one piece mesh")
    _la = open(os.path.join(os.path.dirname(HERE), "tools", "look_at.py"), encoding="utf-8").read(); check("K.view_piece(" in _la and "K.piece_mesh(" in _la and "keep = np.all(" not in _la, "31bn: look_at draws the piece view - opaque, the whole shape, no clipped triangles")
    check("RENDER DEFECTIVE" in open(os.path.join(HERE, "kit_rebuild.py"), encoding="utf-8").read() and "def frame_defective" in open(os.path.join(os.path.dirname(HERE), "hooks", "lookgate.py"), encoding="utf-8").read(), "31bn: a DEFECTIVE frame is no evidence - the judge and the look gate refuse it")
    _X = np.array([0, 20, 0, 5, 15, 10.0]); _Y = np.array([0, 0, 20, 5, 5, 15.0]); _Z = np.array([10, 10, 10, 2, 2, 2.0])
    _ID, _ZB, _BW = K.rasterize(_X, _Y, _Z, np.array([[0, 1, 2], [3, 4, 5]]), 24, 24)
    check(_ID[7, 10] == 1 and abs(_ZB[7, 10] - 2.0) < 1e-9 and _ID[2, 2] == 0 and abs(_ZB[2, 2] - 10.0) < 1e-9 and _ID[23, 23] == -1,
          "rasterize: a TRUE z-buffer - the near small triangle wins its pixels, the far big one keeps the rest, the background is -1 (the painter's order by mean depth painted hidden faces over visible ones)")
    check(abs(_BW[7, 10].sum() - 1.0) < 1e-9 and (_BW[7, 10] >= -1e-6).all(), "rasterize: the winner's barycentric weights at the pixel sum to one")
    _Vc = np.array([[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0], [10, 0, 10], [10, 10, 10.0]]); _Tc = np.array([[0, 1, 2], [0, 2, 3], [1, 4, 5], [1, 5, 2]])
    _N = K.vertex_normals(_Vc, _Tc, np.array([0, 0, 1, 1]))
    check(abs(abs(_N[0, 1, 2]) - 1.0) < 1e-9 and abs(abs(_N[2, 0, 0]) - 1.0) < 1e-9, "vertex_normals: on a 90-deg crease between two faces each corner keeps its own face's normal (the crease stays sharp)")
    _Vs = np.array([[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0], [20, 0, 1], [20, 10, 1.0]]); _N2 = K.vertex_normals(_Vs, _Tc, np.array([0, 0, 0, 0]))
    check(0.95 < abs(_N2[0, 1, 2]) < 0.9999 and abs(_N2[0, 1, 0]) > 0.01, "vertex_normals: inside ONE face a vertex between two facets 5.7 deg apart takes their mean (smooth shading, no facet line)")
    _Pb = np.array([[x, y, z] for x in (0, 4) for y in (0, 4) for z in (0, 2)], float)
    _Vb = np.vstack([_Pb, [[4, 2, 2.0]]])
    _Tb = np.array([(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 8), (1, 8, 7), (1, 7, 3)])
    _q = K.mesh_quality(_Vb, _Tb, np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 5]), closed=True, tol=0.02)
    check(_q["open_edges"] == 3 and _q["seams"] == 3 and _q["cracks"] == 0 and not _q["defective"], "the crack rule: a T-junction (three open edges that lie on each other) is a SEAM, closed - not a crack (look_at on region.brep was stamped on 255 of them)")
    _q = K.mesh_quality(_Vb, _Tb[:-1], np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]), closed=True, tol=0.02)
    check(_q["cracks"] >= 2 and _q["defective"] and "crack" in _q["why"], "the crack rule: a triangle missing from the box leaves edges open by millimetres - CRACKS, DEFECTIVE")
    _q = K.mesh_quality(_Vb, _Tb[:-1], np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]), closed=False, tol=0.02, expected=np.array([[2, 2, 2.0], [0, 2, 2.0], [2, 4, 2.0], [1, 3, 2.0], [3, 3, 2.0]]))
    check(_q["expected_open"] >= 2 and _q["cracks"] <= 1, "the crack rule: open edges on a KNOWN rim (points on the B-rep edges that bound the meshed faces) are expected, not cracks")
    from PIL import Image as _Im, ImageDraw as _Dr
    _ls = K._wrap(_Dr.Draw(_Im.new("RGB", (8, 8))), " ".join(["word"] * 60), K.F16, 300)
    check(len(_ls) > 3 and all(_Dr.Draw(_Im.new("RGB", (8, 8))).textbbox((0, 0), l_, font=K.F16)[2] <= 300 for l_ in _ls), "the captions WRAP to the frame (70 frames of the full look had their legend and quality line cut off)")
    _ql = K.quality_line({"tris": 10, "dev_mm": 0.02, "ang_rad": 0.05, "dev_p99_mm": 0.0568, "nang_p99_deg": 3.75, "open_edges": 3, "expected_open": 0, "seams": 3, "cracks": 0, "gap_tol_mm": 0.02})
    check("0.057 mm off" in _ql and "3.75 deg" in _ql and "3 seams" in _ql and "0 cracks" in _ql, "the quality line prints the record's own numbers (the reviewers found two different ones)")
    try: K.view_piece(None, "x.png", _Vb, _Tb, np.zeros(len(_Tb), int), np.ones((len(_Tb), 3)), (0, 0, -1), (0, 4, 0, 4, 0, 2), 100, "t", "h", [], quality=None); _raised = False
    except ValueError: _raised = True
    check(_raised, "view_piece REQUIRES the mesh's quality - a piece picture without its verdict is not made")
    _fq = K.frame_quality({"cracks": 2, "crack_pts": [[50, 50, 50], [1, 1, 1]], "gap_tol_mm": 0.02, "gap_max_mm": 1.1, "why_mesh": "", "defective": True, "why": "2 crack edge(s)"}, (0, 4, 0, 4, 0, 2))
    check(_fq["cracks_in_frame"] == 1 and _fq["defective"] and "in this frame" in _fq["why"], "frame_quality: a crack inside the frame's box stamps THAT frame")
    _fq = K.frame_quality({"cracks": 2, "crack_pts": [[50, 50, 50], [60, 1, 1]], "gap_tol_mm": 0.02, "gap_max_mm": 1.1, "why_mesh": "", "defective": True, "why": "2 crack edge(s)"}, (0, 4, 0, 4, 0, 2))
    check(_fq["cracks_in_frame"] == 0 and not _fq["defective"] and "none in this frame" in K.quality_line(_fq), "frame_quality: cracks elsewhere in the mesh do not stamp a frame that does not show them (region.brep: 4 gaps on one wall, a look at the vane root is sound) - the line says so")
    _fq = K.frame_quality({"cracks": 0, "crack_pts": [], "why_mesh": "the mesh stands 0.5 mm off", "defective": True, "why": "the mesh stands 0.5 mm off"}, (0, 4, 0, 4, 0, 2))
    check(_fq["defective"] and "0.5 mm" in _fq["why"], "frame_quality: the mesh's own defect (deviation, lean, coarseness) stamps every frame")
    # NO triangles
    _qu = {"cracks": 0, "crack_pts": [], "why_mesh": "", "defective": True, "why": "face(s) [7] ... NO triangles", "unmeshed_faces": [7], "unmeshed_boxes": [[1.0, 3.0, 1.0, 3.0, 0.5, 1.5]]}
    _fu1 = K.frame_quality(_qu, (0, 4, 0, 4, 0, 2)); _fu2 = K.frame_quality(_qu, (10, 14, 10, 14, 0, 2))
    _mu = K.merge_quality([dict(_qu, tris=5), {"tris": 3, "cracks": 0, "defective": False, "why": "", "why_mesh": "", "unmeshed_faces": [], "unmeshed_boxes": []}])
    check(_fu1["defective"] and "NO triangles" in _fu1["why"] and _fu1["unmeshed_in_frame"] == [7] and not _fu2["defective"] and _fu2["unmeshed_in_frame"] == [] and _mu["unmeshed_faces"] == [7] and K.frame_quality(_mu, (0, 4, 0, 4, 0, 2))["defective"],
          "31bq R7W: a face of the piece with NO triangles stamps every frame whose box meets its edges' box RENDER DEFECTIVE (a hole is no evidence - L142), not the frames away from it; a merged frame carries it")
    check("unmeshed.append(" in sli_ and "if not af_ >= 1e-4: continue" in sli_ and "es_[0].BoundBox" in sli_, "31bq R7W: piece_mesh records every face with no triangles (|area| >= 1e-4 mm2) with its B-rep EDGES' box")
    check(K.scale_bar_mm(0.07, 1000) == 10.0 and K.scale_bar_mm(0.009, 900) == 2.0 and K.scale_bar_mm(0.002, 900) == 1.0, "the scale bar is 10 / 5 / 2 / 1 mm - whichever fits in 40 % of the frame (a close-up's 10 mm bar ran off the edge)")
    _fq = K.frame_quality({"cracks": 1, "crack_pts": [[2, 2, 1]], "gap_tol_mm": 0.02, "gap_max_mm": 1.1, "why_mesh": "", "defective": True, "why": "x"}, (0, 4, 0, 4, 0, 2))
    check(_fq["crack_pts_in_frame"] == [[2.0, 2.0, 1.0]] and "ringed red" in _fq["why"], "a stamped frame carries WHERE its cracks are (ringed red on the picture)")
    _mq = K.merge_quality([{"tris": 10, "dev_mm": 0.02, "ang_rad": 0.05, "open_edges": 0, "cracks": 0, "crack_pts": [], "dev_p99_mm": 0.01, "nang_p99_deg": 1.0, "defective": False, "defective_mesh": False, "why": "", "why_mesh": "", "edge_tol_max": 0.1},
                           {"tris": 5, "dev_mm": 0.02, "ang_rad": 0.05, "open_edges": 3, "cracks": 1, "crack_pts": [[9, 9, 9]], "dev_p99_mm": 0.03, "nang_p99_deg": 2.0, "defective": True, "defective_mesh": False, "why": "1 crack", "why_mesh": "", "edge_tol_max": 0.3}])
    check(_mq["tris"] == 15 and _mq["cracks"] == 1 and _mq["crack_pts"] == [[9, 9, 9]] and _mq["dev_p99_mm"] == 0.03 and _mq["edge_tol_max"] == 0.3 and _mq["defective"] and not _mq["defective_mesh"] and _mq["parts"] == 2,
          "merge_quality: a frame of several meshes - the sums, the worst deviations, every crack's place, defective when any part is")
    import kitlib_render as _Rk
    _o = os.path.join(root, "two.png"); _R = _Rk
    _q0 = {"tris": 12, "dev_mm": 0.02, "ang_rad": 0.05, "open_edges": 0, "cracks": 0, "crack_pts": [], "dev_p99_mm": 0.0, "nang_p99_deg": 0.0, "defective": False, "defective_mesh": False, "why": "", "why_mesh": "", "edge_tol_max": 0.0}
    _Tc8 = np.vstack([_Tb[:10], [[1, 5, 7], [1, 7, 3]]])
    _r = K.view_meshes(_R, _o, [(_Vb[:8], _Tc8, np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]), _q0, (0.6, 0.6, 0.9)), (_Vb[:8] + np.array([6.0, 0, 0]), _Tc8, np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]), _q0, (0.9, 0.5, 0.3))],
                       (-0.45, -0.45, -0.77), (0, 10, 0, 4, 0, 2), 300, "two boxes", "TWO BOXES - the piece view of several meshes", ["two cubes"], clip=((5.0, 0, 0), (1.0, 0, 0)))
    from PIL import Image as _Im2
    _im = np.asarray(_Im2.open(_o).convert("RGB")).reshape(-1, 3).astype(int)
    check(_r == "MISS" and os.path.isfile(_o) and (np.sum((_im[:, 2] > _im[:, 0] + 30)) > 500) and (np.sum((_im[:, 0] > _im[:, 2] + 60) & (_im[:, 0] > 120) & (_im[:, 1] < 0.75 * _im[:, 0])) < 50),
          "view_meshes: two meshes in one frame, their own tints, the clip plane drops the second (the orange cube beyond x 5 is not drawn)")
    _st = {}; _o2 = os.path.join(root, "cut.png")
    K.view_meshes(_R, _o2, [(_Vb[:8], _Tc8, np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]), _q0, (0.6, 0.6, 0.9))], (-0.45, -0.45, -0.77), (0, 4, 0, 4, 0, 2), 300, "cut", "A CUT BOX", ["x"],
                  clip=((2.0, 0, 0), (1.0, 0, 0)), stats=_st, subject_box=((0, 2), (0, 4), (0, 2)))
    check(_st.get("cut", {}).get("closed") == 1 and _st.get("drawn_px", 0) > 100 and _st.get("subject_px", 0) > 100 and _st.get("mmpx"), "view_meshes: a clip plane is a REAL capped cut (one closed loop) and the stats say what the frame shows (kit review's gate)")
    _stP = {}; _oP = os.path.join(root, "plate_subject.png")
    _VP = np.array([[0, 0, 0], [100, 0, 0], [100, 100, 0], [0, 100, 0.0]]); _TP = np.array([[0, 1, 2], [0, 2, 3]]); _qP = dict(_q0, tris=2)
    K.view_meshes(_R, _oP, [(_VP, _TP, np.zeros(2, int), _qP, (0.6, 0.6, 0.9))], (0, 0, -1), (0, 100, 0, 100, -1, 1), 300, "plate", "A PLATE", ["x"], stats=_stP, subject_box=((45, 55), (45, 55), (-1, 1)))
    _mm = float(_stP.get("mmpx") or 1.0); _exp = (10.0 / _mm) ** 2
    check(_stP.get("subject_tris", 0) == 0 and 0.8 * _exp < _stP.get("subject_px", 0) < 1.25 * _exp and _stP.get("drawn_px", 0) > 4 * _exp,
          "31bu TK6 F2: the subject is the box's pixels by their surface point - a 10 mm box on a two-triangle plate counts %d px (the box's %d, no triangle centred in it)" % (_stP.get("subject_px", 0), int(_exp)))
    _stL = {}; _oL = os.path.join(root, "lid_occluded.png")      # over the
    _VL = np.array([[0, 0, 10], [100, 0, 10], [100, 100, 10], [0, 100, 10.0]])
    K.view_meshes(_R, _oL, [(_VL, _TP, np.zeros(2, int), _qP, (0.6, 0.6, 0.9))], (0, 0, -1), (0, 100, 0, 100, -1, 11), 300, "lid", "A LID", ["x"], stats=_stL, subject_box=((45, 55), (45, 55), (-1, 1)))
    check(_stL.get("subject_px", 0) == 0 and _stL.get("box_px", 0) > 0 and _stL.get("occluded_px", 0) >= 0.9 * _stL.get("box_px", 1) and _stP.get("occluded_px", 1) == 0 and _stP.get("box_px", 0) > 0,
          "31bv K32: a lid over the box reads OCCLUDED (subject 0, %d of %d footprint pixels covered); the plate's box seen from above reads 0 covered" % (_stL.get("occluded_px", 0), _stL.get("box_px", 0)))
    try:
        import zipfile as _zfT, re as _reT
        _tp = os.path.join(os.path.dirname(HERE), "templates", "BLANK_MODEL.FCStd"); _zt = _zfT.ZipFile(_tp); _dt = _zt.read("Document.xml").decode("utf-8"); _gt = _zt.read("GuiDocument.xml").decode("utf-8")
        _objs = dict((n_, t_) for t_, n_ in _reT.findall(r'<Object type="([^"]+)" name="([^"]+)"', _dt))
        check(all(k in _objs for k in ("G1_PRINT", "G2_ASSEMBLY", "G3_REFERENCE", "G4_MARKERS", "G5_SOURCE", "G0_PALETTE", "MARKER_BOX", "MARKER_PYRAMID", "PLACEHOLDER_BODY", "COLOUR_PRINT", "COLOUR_ASSEMBLY", "COLOUR_REFERENCE", "COLOUR_MARKER"))
              and len(_objs) == 13 and not any(n_.lower().startswith("meshkernel") or n_.startswith("P_") for n_ in _zt.namelist()) and os.path.getsize(_tp) < 200000
              and _gt.count('name="ShapeColor"') >= 5 and not _reT.search("|".join(_reT.escape(w_) for w_ in ("user", "", "", "MYPART", "My Projects", "R35_", "R31_", "Windscreen", "Bike") if len(w_) > 2), _dt + _gt, _reT.I)
              and not any(_reT.search(r"hidden|\bAD\b|the client&apos;s", _l) for _l in _reT.findall(r'<String value="([^"]*)"', _dt)),
              "31bv B1: templates\\BLANK_MODEL.FCStd - 13 objects (the five groups, the two markers, the placeholder, the four colour shapes), no mesh or part payload of its source, under 200 KB, the colours stated, no private word (%d objects, %d bytes)" % (len(_objs), os.path.getsize(_tp)))
    except Exception as _exT: check(False, "31bv B1: the template pin raised %r" % (_exT,))
    try:
        _ax3 = (np.array([0, 0, 1.0]), np.array([1.0, 0, 0]), np.array([0, 1.0, 0]))
        _zb0 = np.full((100, 100), np.inf); _zb0[:, :46] = 2.0
        _bc1 = _R.box_cover(_zb0, (40, 60, 40, 60, 5, 10), *_ax3, 0.0, 100.0, 1.0, 100, 100)
        _zb1 = np.full((100, 100), 20.0)
        _bc2 = _R.box_cover(_zb1, (40, 60, 40, 60, 5, 10), *_ax3, 0.0, 100.0, 1.0, 100, 100)
        _zb2 = np.full((100, 100), np.inf); _zb2[:, :20] = 1.0
        _bc3 = _R.box_cover(_zb2, (40, 60, 40, 60, 5, 10), *_ax3, 0.0, 100.0, 1.0, 100, 100)
        _capm = np.zeros((100, 100), bool); _capm[:, :] = True
        _bc4 = _R.box_cover(_zb1, (40, 60, 40, 60, 5, 10), *_ax3, 0.0, 100.0, 1.0, 100, 100, cap_mask=_capm)
        check(_bc4 == (400, 400, 400), "31bx R1 F4: box_cover - the CUT FACE's pixels cover the box whatever their depth (a capped frame had read 'look ok' on the cap alone): the plate behind as a cap reads 400 / 400 / 400 (got %s)" % (_bc4,))
        check(_bc1 == (400, 120, 120) and _bc2 == (400, 400, 0) and _bc3 == (400, 0, 0),
              "31bv TB2 F2: box_cover - a wall over 6 of the box's 20 columns reads 400 footprint / 120 drawn / 120 covered (the old rule: 120 of 400, a MISS), a plate behind 400 / 400 / 0, an empty footprint 400 / 0 / 0 (got %s %s %s)" % (_bc1, _bc2, _bc3))
        _stE = {}; _oE = os.path.join(root, "empty_window.png")
        _mmE = _R.render(_oE, [("body", np.zeros((0, 3)), np.zeros((0, 3), int), np.zeros((0, 3)))], np.array([0, 0, -1.0]), W=200, focus=np.array([[0, 0, 0], [10, 10, 5.0]]), title="EMPTY", subject_box=((0, 10), (0, 10), (0, 5)), stats=_stE)
        check(os.path.isfile(_oE) and (_stE.get("drawn_px") or 0) == 0 and (_stE.get("subject_px") or 0) == 0 and bool(_mmE), "31bv TB2 F3: a render with no triangle in its window draws an empty frame and reads MISS (drawn 0, subject 0) instead of dying on np.vstack (stats %s)" % {k_: _stE.get(k_) for k_ in ("drawn_px", "subject_px", "box_px")})
        check(isinstance(_stE.get("box_px"), int) and _stE.get("box_px") > 0 and _stE.get("box_drawn_px") == 0 and _stE.get("occluded_px") == 0,
              "31bv TB4 F1: the footprint counts are numbers on an empty frame - footprint %s px, drawn 0, covered 0 (never null)" % _stE.get("box_px"))
    except Exception as _exC: check(False, "31bv TB2 F2 / F3: the box_cover / empty-render pins raised %r" % (_exC,))
    _o3 = os.path.join(root, "bias.png")
    _Vq = np.array([[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0.0]]); _Tq = np.array([[0, 1, 2], [0, 2, 3]]); _qq = dict(_q0, tris=2)
    K.view_meshes(_R, _o3, [(_Vq, _Tq, np.zeros(2, int), _qq, (0.6, 0.6, 0.9)), (_Vq, _Tq, np.zeros(2, int), _qq, (0.95, 0.15, 0.1), 0.3)], (0, 0, -1), (0, 4, 0, 4, -1, 1), 200, "bias", "BIAS", ["x"])
    _im3 = np.asarray(_Im2.open(_o3).convert("RGB")).reshape(-1, 3).astype(int)
    check(np.sum((_im3[:, 0] > _im3[:, 2] + 60) & (_im3[:, 0] > 120) & (_im3[:, 1] < 0.75 * _im3[:, 0])) > 2000 and np.sum(_im3[:, 2] > _im3[:, 0] + 30) < 50,
          "view_meshes: a part biased toward the camera wins where two skins coincide (the seam faces on the body, the content against the body round it)")
    _Vo, _To, _Fo = K.mesh_outside_region(_Rk, _Vb[:8], _Tc8, np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]), [((1.0, 0, 0), (-1.0, 0, 0)), ((3.0, 0, 0), (1.0, 0, 0))])
    _Po = _Vo[_To]; _Ao = 0.5 * np.linalg.norm(np.cross(_Po[:, 1] - _Po[:, 0], _Po[:, 2] - _Po[:, 0]), axis=1).sum()
    _cx = _Vo[_To].mean(1)[:, 0]
    check(abs(_Ao - 40.0) < 1e-6 and not np.any((_cx > 1.0 + 1e-9) & (_cx < 3.0 - 1e-9)) and len(_To) > 12,
          "mesh_outside_region: a box cut on the region's planes keeps exactly the outside (its area the box's 64 mm2 minus the slab's 24; no triangle in the slab; the straddling ones split, not dropped)")
    _pl = [((1.0, 0, 0), (-1.0, 0, 0)), ((3.0, 0, 0), (1.0, 0, 0))]
    _qs = dict(_q0, how="MeshPart whole shape", seams=0, gap_max_mm=0.0)
    _qe = K.cut_quality(_qs, _Vb[:8], _Tc8, _Vo, _To, _Fo, _pl)
    _cx8 = _Vb[:8][_Tc8].mean(1)[:, 0]; _keep = ~((_cx8 > 1.0) & (_cx8 < 3.0))
    _qr = K.cut_quality(_qs, _Vb[:8], _Tc8, _Vb[:8], _Tc8[_keep], np.array([0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5])[_keep], _pl)
    check(_qe["cracks"] == 0 and not _qe["defective"] and _qe["open_edges"] == _qe["expected_open"] and _qe["open_edges"] > 0 and "cut on the walls" in _qe["how"] and _qe["tris"] == len(_To)
          and _qr["cracks"] > 0 and _qr["defective"] and "ragged trim" in _qr["why"] and len(_qr["crack_pts"]) == _qr["cracks"],
          "cut_quality: the DRAWN cut is judged - an exact cut's open edges all lie on a wall plane (expected, 0 cracks); a whole-triangle trim leaves open edges on neither a plane nor the source's rim = cracks, the frames stamped (b20t7's ragged rim read clean before)")
    _rr = open(os.path.join(HERE, "rebuild", "rb_region.py"), encoding="utf-8").read()
    check("meshes_cut = [(VC, TC, FC, MQc, CC_)]" in _rr and 'region_fit_%s.png' in _rr and "K.cut_quality(MQl, VL0, TL0, VL, TL, FL, hs_)" in _rr and "the content ALONE" in _rr
          and 'views["wall%d" % k_] = -n_' in _rr and "(0.95, 0.6, 0.2), 0.05)" in _rr and "a red band" not in _rr and "C_k[onw_list[k_w]] = (0.92, 0.12, 0.12)" in _rr and "C_k[onw] = (0.55, 0.42, 0.42)" in _rr,
          "31bn fix 5g/5h: the region's cut frames are the content ALONE with its section faces red (the cut itself - covered in any correct picture of body and content together), ONE FACE-ON VIEW PER WALL (only that wall's section red, the others dull) + two isos, two fit frames show it plain orange in the body, the drawn cut body carries its own verdict, and the footer names the RENDER DEFECTIVE banner")
    for _f, _needle in (("rebuild/rb_review_body.py", "K.view_meshes("), ("rebuild/rb_region.py", "K.view_meshes("), ("rebuild/rb_reinsert.py", "K.view_meshes("), ("rebuild/sk_mirror.py", "K.view_piece("), ("job_render_arc.py", "K.view_meshes("), ("job_tess_cache.py", "K.piece_mesh(")):
        _src = open(os.path.join(HERE, _f), encoding="utf-8").read()
        check(_needle in _src and ("R.render(" not in _src or _f == "rebuild/rb_reinsert.py"), "31bn fix 5: %s draws the real model through THE PIECE VIEW (%s), not the old renderer" % (_f, _needle))
    import re as _re
    check(not _re.search(r"^\s*(import|from) (Part|FreeCAD|MeshPart)", open(os.path.join(HERE, "job_render_arc.py"), encoding="utf-8").read(), _re.M) and not _re.search(r"^(import|from) (Part|FreeCAD|MeshPart)", open(os.path.join(HERE, "rebuild", "sk_lib.py"), encoding="utf-8").read(), _re.M),
          "the review shards stay numpy-only: no kernel import in job_render_arc, none at sk_lib's module level")
    check('"quality"' in open(os.path.join(HERE, "kitlib_render.py"), encoding="utf-8").read() and "REVIEW_BODY_quality.json" in open(os.path.join(HERE, "kit_rebuild.py"), encoding="utf-8").read(),
          "the tessellation cache and the trial's look carry the mesh's quality (the judge refuses a stamped region / trial set)")
    check("K.pic_hit(path, LKEY)" in sl_ and "K.clear_frames(PREFIX" in sl_ and "K.pic_mark(path, LKEY)" in sl_ and 'pic_report("SKIN_look")' in sl_, "skin-look reuses the kit's HIT / MISS pictures (31aw)")
    check("LOOK_VIS" in open(os.path.join(HERE, "kit_rebuild.py"), encoding="utf-8").read() and "LOOK_VIS" in open(os.path.join(os.path.dirname(HERE), "hooks", "lookgate.py"), encoding="utf-8").read(), "LOOK_VIS is a registered lever and no design decision")
    # ORIGINAL
    # stations
    try:
        _bx = lambda x0, x1, y0, y1, z0, z1: (np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], float),
                                              np.array([(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]))
        def _rf(V_, T_, n_):
            for _ in range(n_):
                Vl_ = list(V_); md_ = {}; Tn_ = []
                def _m(a, b):
                    k = (min(a, b), max(a, b))
                    if k not in md_: md_[k] = len(Vl_); Vl_.append(0.5 * (Vl_[a] + Vl_[b]))
                    return md_[k]
                for a, b, c in T_:
                    ab, bc, ca = _m(a, b), _m(b, c), _m(c, a); Tn_ += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
                V_ = np.array(Vl_, float); T_ = np.array(Tn_, int)
            return V_, T_
        _Vp, _Tp = _rf(*_bx(0, 10, 0, 10, 0, 4), 3)
        _P = np.random.RandomState(0).uniform([-2, -2, -2], [12, 12, 6], (1500, 3))
        _d, _t, _s = K.dist_capped(_P, _Vp, _Tp, cap=1.0, need_over=0.5)
        _Q = K._closest_pt_tri(_P[:, None, :], _Vp[_Tp[:, 0]][None], _Vp[_Tp[:, 1]][None], _Vp[_Tp[:, 2]][None]); _dx = np.linalg.norm(_Q - _P[:, None, :], axis=2).min(1)
        _ex = (_dx <= 1.0) & (_d > 0.5); _in = np.all((_P >= [0, 0, 0]) & (_P <= [10, 10, 4]), axis=1); _of = _dx > 0.5
        check(_ex.any() and np.abs(_d[_ex] - _dx[_ex]).max() < 1e-9 and not ((_d > 0.5) != (_dx > 0.5)).any() and (_d >= _dx - 1e-9).all() and (_d[_dx > 1.0] >= 1.0 - 1e-9).all(),
              "31bq B18: dist_capped is EXACT up to the cap where the bound is over need_over, never nearer than the truth, at least the cap beyond it - the brute force's classification at 0.5 mm on every point")
        check((_s[_of & _in] < 0).all() and (_s[_of & ~_in] > 0).all(), "31bq B18: dist_capped's side - a point inside an outward-wound mesh reads -1, outside +1")
        _d2, _t2, _s2 = K.dist_capped(_P, _Vp, _Tp, cap=1.0, need_over=0.5, chunk=37)
        check(np.array_equal(_d, _d2) and np.array_equal(_s, _s2), "31bq B18 (R7W): dist_capped in chunks of 37 pairs gives the same distances and sides (the R6 form held every pair at once: 705 MB on the fill piece)")
        _Vo, _To = _rf(*_bx(0, 10, 0, 10, 0, 4), 3); _co = _Vo[_To].mean(1); _fo = np.zeros(len(_To), np.int64)
        for _i, (_a, _b) in enumerate([(0, 0.0), (0, 10.0), (1, 0.0), (1, 10.0), (2, 0.0), (2, 4.0)]): _fo[np.abs(_co[:, _a] - _b) < 1e-9] = _i + 1
        _Vd = np.array([[3, 3, 5.5], [7, 3, 5.5], [7, 7, 5.5], [3, 7, 5.5]], float); _Td = np.array([[0, 1, 2], [0, 2, 3]])
        _Vk = np.array([[0.8, 4, 1], [0.8, 6, 1], [0.8, 6, 3], [0.8, 4, 3]], float); _Tk = np.array([[0, 2, 1], [0, 3, 2]])
        _fsrc = np.concatenate([np.where(_fo == 6, -9, _fo), [7, 7], [8, 8]])
        _st, _smp = K.faces_against_piece(np.vstack([_Vo, _Vd, _Vk]), np.vstack([_To, _Td + len(_Vo), _Tk + len(_Vo) + 4]), _fsrc, *_rf(*_bx(0, 10, 0, 10, 0, 4), 4))
        check(sorted(_st) == [1, 2, 3, 4, 5, 7, 8] and all(_st[f_]["off_mm2"] == 0.0 for f_ in (1, 2, 3, 4, 5)) and abs(_st[7]["removed_mm2"] - 16.0) < 0.01 and _st[7]["max_mm"] is None
              and abs(_st[8]["filled_mm2"] - 4.0) < 0.01 and abs(_st[8]["max_mm"] - 0.8) < 1e-6 and len(_smp) == 7 and np.array_equal(_fsrc[_smp[6]], _smp[1]),
              "31bq B18: faces_against_piece - the box's faces on the piece, a cap left out, a 16 mm2 pad 1.5 mm proud all REMOVED (over the cap), a 4 mm2 floor 0.8 mm inside all FILLED; each sample's SOURCE triangle returned (its layout face is its own triangle's)")
        _Vs_, _Ts_ = _rf(*_bx(4.4, 5.6, 4.4, 5.6, 4.0, 5.2), 2); _cs_ = _Vs_[_Ts_].mean(1); _kb = _cs_[:, 2] > 4.0 + 1e-9; _Ts_ = _Ts_[_kb]; _cs_ = _cs_[_kb]; _fb = np.full(len(_Ts_), -1, np.int64)
        for _i, (_a, _b) in enumerate([(0, 4.4), (0, 5.6), (1, 4.4), (1, 5.6), (2, 5.2)]): _fb[np.abs(_cs_[:, _a] - _b) < 1e-9] = 21 + _i
        _stb, _smpb = K.faces_against_piece(np.vstack([_Vo, _Vs_]), np.vstack([_To, _Ts_ + len(_Vo)]), np.concatenate([_fo, _fb]), *_rf(*_bx(0, 10, 0, 10, 0, 4), 4))
        _Sb, _SFb, _SWb, _db = _smpb[0], _smpb[1], _smpb[2], _smpb[3]; _labb, _arb = K.off_regions(_Sb, _SWb, _db > K.VANISH_MM)
        _rb = sorted(set(_labb[np.isin(_SFb, [21, 22, 23, 24, 25]) & (_db > K.VANISH_MM)].tolist()))
        _pb = [{"face": f_, "region": _rb[0], "off_mm2": float(_SWb[(_labb == _rb[0]) & (_SFb == f_)].sum()), "drop": None, "blend": (0.0, [], {})} for f_ in (21, 22, 23, 24, 25)] if len(_rb) == 1 else []
        K.classify_parts(_pb, {"respanned": {f_: True for f_ in range(30)}, "merged": {}})
        _nb = K.name_regions(_pb, _arb)
        check(all(_stb[f_]["off_mm2"] < K.VANISH_MM2 for f_ in range(21, 26)) and len(_rb) == 1 and _arb[_rb[0]] >= K.VANISH_MM2 and _nb.get(_rb[0], {}).get("named") is True,
              "31bq B18 (R7W, the skeptic's finding 1): a 1.2 mm boss of five faces, each under %.0f mm2 off, is ONE REGION of %.1f mm2 - NAMED (the per-face rule had named nothing)" % (K.VANISH_MM2, _arb[_rb[0]] if len(_rb) == 1 else -1))
        _S5 = lambda f_, o_, **kw: dict({"face": f_, "region": 0, "off_mm2": o_, "drop": None, "blend": (0.0, [], {})}, **kw)
        _L = K.classify_parts([_S5(10, 5.0, drop=(1, "the client: no hole there - the slot under the spine closed")), _S5(11, 5.0), _S5(12, 5.0, blend=(0.9, [30], {30: 1.1})), _S5(13, 5.0, drop=(3, None)),
                               _S5(14, 5.0), _S5(15, 5.0), _S5(16, 5.0), _S5(17, 5.0), _S5(18, 5.0, blend=(0.3, [30], {30: 1.1}))],
                              {"no_points": {10, 13, 14}, "buried_of": {11: [34]}, "merged": {15: True}, "respanned": {15: True, 16: True, 18: True}, "in_piece": {17: False}, "feat_of": {15: "vane_top"}, "feat_why": {"vane_top": "the lens merged, no step"}})
        _cl = {r_["face"]: r_["cls"] for r_ in _L}; _wy = {r_["face"]: r_["why"] for r_ in _L}
        check(_cl == {10: "dropped", 11: "buried", 12: "blend", 13: "unreasoned", 14: "absorbed", 15: "feature", 16: "own", 17: "lost", 18: "own"} and "the client: no hole there" in _wy[10] and "NO REASON" in _wy[13]
              and "line(s) [30]" in _wy[12] and "the lens merged, no step" in _wy[15] and set(K.VANISH_BY_RECORD) == {"dropped", "buried", "blend"} and "unreasoned" not in K.VANISH_BY_RECORD,
              "31bq B18 (R7W): classify_parts - a box WITH its reason, a burial and a decided blend's strip remove; a REASONLESS box (31bq B22), the pick, the feature map, a re-span, nothing are NAMED; a part 30 %% in a strip is no blend (%s)" % _cl)
        _nr = K.name_regions([dict(_S5(10, 1.5), cls="dropped"), dict(_S5(13, 1.0), cls="unreasoned"), dict(_S5(12, 9.0), region=1, cls="own"), dict(_S5(16, 1.0), region=2, cls="lost")], [2.5, 9.0, 1.0])
        check(set(_nr) == {0, 1} and _nr[0]["named"] is False and abs(_nr[0]["named_mm2"] - 1.0) < 1e-9 and _nr[1]["named"] is True,
              "31bq B18 (R7W): name_regions - a region under VANISH_MM2 did not leave; one whose unaccounted parts are under it stands by its records; one over it is NAMED (%s)" % _nr)
        _nr2 = K.name_regions([dict(_S5(10, 1.5), cls="dropped"), dict(_S5(13, 1.0), cls="unreasoned"), dict(_S5(19, 1.2), cls="own")], [3.7])
        check(_nr2[0]["named"] is True and abs(_nr2[0]["named_mm2"] - 2.2) < 1e-9, "31bq B18 (R7W): a region's unaccounted parts SUM (1.0 unreasoned + 1.2 own = 2.2 mm2: NAMED; the reasoned box's 1.5 does not count)")
        _nr3 = K.name_regions([dict(_S5(31, 12.8, blend=(0.62, [30], {30: 1.5})), cls="blend")], [12.8]); _nr4 = K.name_regions([dict(_S5(31, 12.8, blend=(1.0, [30], {30: 1.5})), cls="blend")], [12.8])
        _wb = K.classify_parts([_S5(31, 12.8, blend=(0.62, [30], {30: 1.5}))], {"respanned": {31: True}})[0]
        check(_nr3[0]["named"] is True and abs(_nr3[0]["named_mm2"] - 4.864) < 1e-9 and _nr4[0]["named"] is False and _wb["cls"] == "blend" and "BEYOND any decided blend's strip" in _wb["why"],
              "31bq B18 (R7W, the verifier's D4): a blend part accounts only for its TIED share - 62 %% of 12.8 mm2 in the strip leaves 4.86 mm2 unaccounted: NAMED; a part wholly in the strip is not (%s / %s)" % (_nr3, _nr4))
        _Sx = np.array([[5.0, 0.5, 0.0], [5.0, 0.5, 0.0], [5.0, 3.0, 0.0], [5.0, 0.5, 0.0]]); _bl = [{"line": 7, "pair": (3, 4), "crease": np.array([[0.0, 0, 0], [10.0, 0, 0]]), "t": 1.0}]
        _tie = K.blend_tie(_Sx, np.array([3, 3, 3, 9]), np.array([True, False, True, True]), _bl)
        check(list(_tie) == [7, -1, -1, -1] and list(K.blend_tie(_Sx, np.array([3, 3, 3, 9]), np.ones(4, bool), [])) == [-1, -1, -1, -1],
              "31bq B18 (R7W, the skeptic's finding 2): blend_tie - a sample is the DECIDED blend's only nearest a blend face, on one of the line's two layout faces, within t + %.1f mm of its crease; no decided line, no blend (%s)" % (K.VANISH_MM, list(_tie)))
        _Vc4 = np.array([[0, 0, 0], [10, 0, 0], [10, 5, 0], [0, 5, 0], [0, 0, 5], [10, 0, 5]], float); _Tc4 = np.array([[0, 1, 2], [0, 2, 3], [0, 4, 5], [0, 5, 1]])
        _tt, _bt = K.crease_t(1.5, _Vc4, _Tc4, np.array([0, 0, 1, 1]), (0, 1), np.array([[0.0, 0, 0], [10.0, 0, 0]]))
        check(abs(_bt - 90.0) < 1e-6 and abs(_tt - 1.5) < 1e-9 and K.crease_t(1.5, _Vc4, _Tc4, np.array([0, 0, 1, 1]), (0, 7), np.array([[0.0, 0, 0], [10.0, 0, 0]]))[1] is None,
              "31bq B18 (R7W): crease_t - two layout faces at 90 deg: beta 90, t = R (L141); a side with no triangle: t = R, beta unknown")
        _db = K.drop_boxes({"levers": {"PTS_DROP": "-4.7 4.7 -118.95 -108.15 72.7 83.0 | the slot under the spine closed - the client: no hole there; 9.55 10.35 -140.95 -133.65 89.5 89.7; 1 2 3 4 5 6"},
                            "lever_whys": {"PTS_DROP": [{"box": [9.55, 10.35, -140.95, -133.65, 89.5, 89.7], "why": "the crown overhang's sliver blends away"}]}})
        check([w_ for _, w_ in _db] == ["the slot under the spine closed - the client: no hole there", "the crown overhang's sliver blends away", None] and _db[0][0] == [-4.7, 4.7, -118.95, -108.15, 72.7, 83.0] and K.drop_boxes(None) == [],
              "31bq B18 (R7W): drop_boxes - the reason after '|' (31bq B22's form), else lever_whys' entry of the same box, else None (a box from before B22)")
        _Vbx, _Tbx = _bx(0, 10, 0, 10, 0, 4); _Vpd, _Tpd = _bx(3, 7, 3, 7, 4, 5.5); _Vold = np.vstack([_Vbx, _Vpd]); _Told = np.vstack([_Tbx, _Tpd + len(_Vbx)])
        _sp = os.path.join(root, "vanished_section.png")
        _sc = K.section_frame(_Rk, _sp, (_Vold, _Told), (_Vbx, _Tbx), 1, 5.0, ((-1.0, 11.0), (-1.0, 7.0)), K.VANISH_MM, "a pad the piece lost", ["the pad's outline yellow"], quality=_q0)
        _sc2 = K.section_frame(_Rk, os.path.join(root, "vanished_section2.png"), (_Vbx, _Tbx), (_Vbx, _Tbx), 1, 5.0, ((-1.0, 11.0), (-1.0, 7.0)), K.VANISH_MM, "the same", ["all green"], quality=_q0)
        from PIL import Image as _Im4
        _yel = lambda p_: int(((lambda a_: (a_[:, 0] > 200) & (a_[:, 1] > 180) & (a_[:, 2] < 120))(np.asarray(_Im4.open(p_).convert("RGB")).reshape(-1, 3).astype(int))).sum())
        check(os.path.isfile(_sp) and _sc["old_only"] >= 3 and _sc["new_only"] == 0 and _sc["both"] >= 4 and _sc2["old_only"] == 0 and _sc2["new_only"] == 0 and _sc2["both"] >= 4
              and _yel(_sp) - _yel(os.path.join(root, "vanished_section2.png")) > 500,
              "31bq B18 (R7W, the skeptic's finding 4): section_frame - the original's pad drawn YELLOW (the original only), the shared box GREEN, nothing BLUE; identical meshes all green (%s / %s)" % (_sc, _sc2))
        for _nm, _ky in (("SKIN_vtest_a.png", "key-A"), ("SKIN_vtest_b.png", "key-B")):
            open(os.path.join(K.OUT, _nm), "wb").write(b"png"); K.pic_mark(os.path.join(K.OUT, _nm), _ky)
        K.clear_frames("SKIN_vtest_", "key-A", also=("key-B",)); _kept = sorted(f_ for f_ in os.listdir(K.OUT) if f_.startswith("SKIN_vtest_"))
        K.clear_frames("SKIN_vtest_", "key-A"); _kept2 = sorted(f_ for f_ in os.listdir(K.OUT) if f_.startswith("SKIN_vtest_"))
        check(_kept == ["SKIN_vtest_a.png", "SKIN_vtest_b.png"] and _kept2 == ["SKIN_vtest_a.png"], "31bq B18 (R7W): clear_frames keeps a HIT of an `also` key - skin-look's vanished frames carry their own key (%s / %s)" % (_kept, _kept2))
        check("K.faces_against_piece(" in sl_ and "K.off_regions(" in sl_ and "K.classify_parts(" in sl_ and "K.name_regions(" in sl_ and "K.blend_tie(" in sl_ and "K.drop_boxes(" in sl_ and "K.section_frame(" in sl_
              and "K.view_meshes(" in sl_ and "ORIGINAL FACES AGAINST THE PIECE" in sl_ and "NOT TAKEN" in sl_ and "a KIT FAULT" in sl_ and '"original_faces": VAN' in sl_ and "ORIGINAL_FACES.json" in sl_
              and "also=(VKEY,)" in sl_ and '"fillets.json"' not in sl_.split("LKEY = K.pic_key(")[1].split("\n")[0] and "SKIN_look vanished" in sli_,
              "31bq B18: skin-look measures the original's faces against the piece in REGIONS, names what no record accounts for, frames each named region (a section + the piece view, their own picture key), says NOT TAKEN - a kit fault named - when it cannot")
    except Exception as _ex: check(False, "the 31bq B18 pins raised %s: %s" % (type(_ex).__name__, _ex))
    try:
        _rbb = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rebuild", "rb_review_body.py"), encoding="utf-8").read()
        check("def _clip_segs(segs, ax):" in _rbb and "sa = _clip_segs(R.section_segs(VA, TA, ax, c), ax); sb = _clip_segs(R.section_segs(V, T, ax, c), ax)" in _rbb and "def clip(Vx, Tx):" not in _rbb,
              "31bp: the station overlays cut the WHOLE mesh of each body and keep the segments that reach the region's window - no triangle is dropped by its centroid (the agent's b23 reviewers saw an old floor line with no blue partner where the kernel's sections were identical)")
    except Exception as _ex: check(False, "the 31bp station pin raised %s" % _ex)
    try:
        import check_names as _CN
        _F7 = {"a1": ('g = (X + 1 for _ in range(2))\nX = 5\nprint(list(g))\n', 0, 0),
               "a2": ('Y = list(X + 1 for _ in range(2))\nX = 5\n', 1, 0),
               "a4": ('g = (X for _ in range(2))\nfirst = next(g)\nX = 5\n', 1, 0),
               "a6": ('g = (X for _ in range(1))\ng = iter([0])\nprint(list(g))\nX = 5\n', 0, 0),
               "a8": ('g = (X for _ in range(1))\ndef f():\n    return list(g)\nf()\nX = 5\n', 1, 0),
               "a11": ('g = (X for _ in range(1))\ndef f(k):\n    if k:\n        return list(g)\n    return []\nf(0)\nX = 5\nprint(list(g))\n', 0, 1),
               "b1": ('Y = [(Z := i) for i in range(3)]\nprint(Z)\nZ = 10\n', 0, 0),
               "b4": ('def f():\n    return Z\nprint(f())\nY = [(Z := i) for i in range(2)]\n', 1, 0),
               "b5": ('def f():\n    return Z\nY = [(Z := i) for i in range(2)]\nprint(f())\n', 0, 0),
               "b9": ('g = ((W := i) for i in range(2))\nprint(W)\nW = 5\nlist(g)\n', 1, 0),
               "x1": ('for k in range(1):\n    g = (X for _ in range(1))\n    print(list(g))\nX = 5\n', 1, 0),
               "a4a": ('g = (X for _ in range(1))\nif False:\n    g = []\nprint(list(g))\nX = 5\n', 1, 0),
               "a4c": ('g = (X for _ in range(1))\nX = next(g)\n', 1, 0)}
        _got7 = {}
        for _k7, (_s7, _n7, _u7) in _F7.items():
            _p7 = os.path.join(root, "f7_%s.py" % _k7); open(_p7, "w", encoding="utf-8").write(_s7)
            _h7, _q7 = _CN.check(_p7); _got7[_k7] = (len(_h7), len(_q7))
        _bad7 = {k_: (v_, _F7[k_][1:]) for k_, v_ in _got7.items() if v_ != _F7[k_][1:]}
        check(not _bad7, "R7W fix-small (F.7): check_names reads a stored generator expression where it is CONSUMED and a comprehension's walrus as a MODULE bind - each case as Python runs it (NAMEs, UNCERTAINs) %s" % (_bad7 or ""))
        _h4 = _CN.check(os.path.join(root, "f7_a4.py"))[0]
        check(bool(_h4) and _h4[0][1] == "X" and "consumed on line 2" in _h4[0][2], "R7W fix-small (F.7): a stored generator consumed before its global is bound is named AT ITS CONSUMER (%s)" % (_h4[:1] or ""))
    except Exception as _ex: check(False, "the R7W fix-small F.7 pins raised %s: %s" % (type(_ex).__name__, _ex))
    try:
        import threading as _thK, kit_place as _KPK, kit_deliver as _KDK
        _ts = open(os.path.join(HERE, "templates", "t_split.py"), encoding="utf-8").read()
        check(_ts.count('"x": K.box(') == 0 and "lo = K.box(*LO); hi = K.box(*HI)" in _ts and "one side of the split would be empty (31bs K23)" in _ts,
              "31bs K23: t_split builds the chosen axis's two boxes only - no K.box call inside a dict literal, lo / hi from the axis's tuples, a value outside the axis's range refused by name")
        _kpt = open(os.path.join(HERE, "kit_place.py"), encoding="utf-8").read(); _ib = _kpt.index("    if bake:")
        check(_kpt.index("s.Placement = App.Placement()", _ib) < _kpt.index("s = s.transformGeometry(fpl.multiply(old).toMatrix())", _ib) < _kpt.index("    else:", _ib),
              "31bs K27: the bake sets the Placement to identity BEFORE transformGeometry(fpl * old) - the raw geometry, the probe's P4 (the located input had landed twice)")
        _rk = tempfile.mkdtemp(prefix="k26_"); os.makedirs(os.path.join(_rk, "claude_code"))
        _pm = os.path.join(_rk, "claude_code", "PLACEMENTS.json")
        w(_pm, "{not json"); _refused = None
        try: _KPK.record(_rk, os.path.join(_rk, "claude_code", "x.brep"), {"a": 1})
        except OSError as _e26: _refused = str(_e26)
        check(_refused is not None and "NOT overwritten" in _refused and open(_pm).read() == "{not json", "31bs K26: an EXISTING frame map that does not read as JSON REFUSES the write (never an empty map over it): %s" % (_refused or "")[:60])
        os.remove(_pm); _errs = []
        def _wr(i_):
            try: _KPK.record(_rk, os.path.join(_rk, "claude_code", "b%d.brep" % i_), {"i": i_})
            except Exception as _e: _errs.append(str(_e))
        _ths = [_thK.Thread(target=_wr, args=(i_,)) for i_ in range(12)]
        for _t in _ths: _t.start()
        for _t in _ths: _t.join()
        _m26 = json.load(open(_pm, encoding="utf-8"))
        check(len(_m26) == 12 and not _errs and not [f_ for f_ in os.listdir(os.path.dirname(_pm)) if ".tmp" in f_ or f_.endswith(".lock")], "31bs K26: twelve writers at once keep every entry under the lock (%d of 12, %d error(s)); no .tmp left behind%s" % (len(_m26), len(_errs), (" - " + "; ".join(e_[:120] for e_ in _errs[:2])) if _errs else ""))
        open(_pm + ".lock", "w").write("1 stale"); os.utime(_pm + ".lock", (time.time() - 3600, time.time() - 3600))
        _KPK.record(_rk, os.path.join(_rk, "claude_code", "c.brep"), {"c": 1})
        check("claude_code/c.brep" in json.load(open(_pm, encoding="utf-8")) and not os.path.exists(_pm + ".lock"), "31bs K26: a stale lock (over LOCK_STALE_S old) is taken over and the write lands")
        json.dump({"claude_code/bank/P.brep": {"result": {"bbox": [-44.15, 5.85, 61.41, 86.69, 46.2, 121.11]}}}, open(_pm, "w"))
        os.makedirs(os.path.join(_rk, "claude_code", "bank")); w(os.path.join(_rk, "claude_code", "bank", "P.brep"), "DBRep_DrawableShape\n0 0 0\n10 10 10\n")
        _bbW = _KDK._bbox_of(os.path.join(_rk, "claude_code", "bank", "P.brep"))
        check(_bbW == ((-44.15, 61.41, 46.2), (5.85, 86.69, 121.11)), "31bs W40: the delivery's camera frames a PLACED body where the frame map says it sits (%s), not on the raw text's triples" % (_bbW,))
        json.dump({"claude_code/bank/P.brep": {"when": "2026-01-01 00:00:00", "result": {"bbox": [-44.15, 5.85, 61.41, 86.69, 46.2, 121.11]}}}, open(_pm, "w"))
        check(_KDK._bbox_of(os.path.join(_rk, "claude_code", "bank", "P.brep")) != ((-44.15, 61.41, 46.2), (5.85, 86.69, 121.11)), "31bs T2 F7: a frame-map entry OLDER than the brep (another placement's, left by a refused record) does not frame the camera")
        check("for _try in range(40):" in _kpt and "os.remove(tmp)" in _kpt, "31bs T2 F4: the record retries the replace and never leaves its tmp")
        import hashlib as _hl4; _md4 = _hl4.md5(open(os.path.join(_rk, "claude_code", "bank", "P.brep"), "rb").read()).hexdigest()
        json.dump({"claude_code/bank/P.brep": {"when": "2026-01-01 00:00:00", "md5": _md4, "result": {"bbox": [-44.15, 5.85, 61.41, 86.69, 46.2, 121.11]}}}, open(_pm, "w"))
        check(_KDK._bbox_of(os.path.join(_rk, "claude_code", "bank", "P.brep")) == ((-44.15, 61.41, 46.2), (5.85, 86.69, 121.11)), "31bt md5: a record whose md5 is THIS file's frames the camera whatever its date (the md5 names the file, the mtime rule is for records without one)")
        json.dump({"claude_code/bank/P.brep": {"when": "2099-01-01 00:00:00", "md5": "0" * 32, "result": {"bbox": [-44.15, 5.85, 61.41, 86.69, 46.2, 121.11]}}}, open(_pm, "w"))
        check(_KDK._bbox_of(os.path.join(_rk, "claude_code", "bank", "P.brep")) != ((-44.15, 61.41, 46.2), (5.85, 86.69, 121.11)), "31bt md5: a record whose md5 is another file's does not frame the camera, however new its date")
        check('entry["md5"] = __import__("hashlib").md5(' in _kpt, "31bt md5: kit place records the written file's md5")
        w(os.path.join(_rk, "claude_code", "bank", "Q.brep"), "DBRep_DrawableShape\n" + "".join("%d %d %d\n" % (x_, y_, z_) for x_ in (0, 10) for y_ in (0, 20) for z_ in (0, 30)))
        check(_KDK._bbox_of(os.path.join(_rk, "claude_code", "bank", "Q.brep")) == ((0.0, 0.0, 0.0), (10.0, 20.0, 30.0)), "31bt TJ3 F1: a body with no frame-map record and a box's 8 triples is framed on its own triples, not on the generic default")
        _klb = open(os.path.join(HERE, "kitlib.py"), encoding="utf-8").read()
        check("foc = np.array([[x_, y_, z_] for x_ in (x0, x1) for y_ in (y0, y1) for z_ in (z0, z1)], float)" in _klb and "foc = Vv[np.unique(T[m])] if m.any() else None" not in _klb, "31bu K18: a boxed look is framed on the box's eight corners - before and after on one window by construction (the triangles found in the box had set it)")
        check("kitlib.load: no such file" in _klb, "31bu T8 F4: kitlib.load refuses a missing path by name")
        shutil.rmtree(_rk, ignore_errors=True)
    except Exception as _exK: check(False, "the 31bs skin4 pins raised %s: %s" % (type(_exK).__name__, _exK))
finally:
    shutil.rmtree(root, ignore_errors=True)
print("\n[31bx round 1] the instruments, the templates and the frames (FIX_LEDGER_31bx X43 X44 X50 X60 X61 X63 X71 X72 X80 X89)")
try:
    _rd = lambda *p: open(os.path.join(HERE, *p), encoding="utf-8").read()
    _la = _rd("..", "tools", "look_at.py"); _kr = _rd("kitlib_render.py"); _sl = _rd("rebuild", "sk_lib.py"); _sr = _rd("rebuild", "sk_rim.py"); _kd = _rd("kit_dossier.py")
    check("(0.45, -0.45, -0.77), (0.45, 0.45, -0.77), (-0.45, 0.45, -0.77)" in _la and "(0.45, 0.45, 0.77)" not in _la, "31bx R6 F10: look_at's four default cameras are four distinct quadrants (two opposite pairs had given four pictures of eight)")
    check("np.isfinite(zbuf) & (own >= 0)" in _kr and "cap_mask=(own == -2)" in _kr and "cap_mask=None" in _kr, "31bx R1 F4: the renderer's subject pixels exclude the cut face (own -2) and box_cover takes the cap mask")
    check("cap_tris=None" in _sl and "caps_.append(np.asarray(is_cap, bool)" in _sl and "cap_mask=_capm" in _sl, "31bx R1 F4: the piece view carries its cap triangles through view_meshes into the subject count and the cover")
    check("def _title_bars(dr, im, title, axes):" in _sl and _sl.count("_title_bars(dr, im, title, R.axes_label(r3, u3))") == 3 and "K._wrap(_od0" in _sr, "31bx R5 F5 / R6 F11: the frame titles are wrapped to the frame (three views) and the SP12 / LAYOUT legends too")
    check("hold no material (the body spans" in _kd and "no station along %s crosses material inside the box" in _kd and 'e.get("partial") and "--force" not in rest' in _kd, "31bx R1 F3: the dossier skips a station in the air, refuses an axis with none and takes a PARTIAL dossier again")
    check('isinstance(P["open_faces"], str)' in _rd("templates", "t_shell.py"), "31bx R1 F6: t_shell takes a bare '+z' as one face")
    check("0 = none (both REQUIRED, 0 is the answer" in _rd("templates", "t_hole.py") and "v along normal x udir" in _rd("templates", "t_revolve.py"), "31bx R1 D8 / D9: the hole's counterbore and the revolve's v axis said in the templates")
    _tc = _rd("templates", "t_cutter.py")
    check("cross_margin_mm=0.30," in _tc and "float(cs[0]) - _cm, float(W_fin[i, 0])" in _tc and '"cross_margin_mm", "boundary", "sweep"' in _tc and "_cl = res.copy().removeSplitter()" in _tc, "31bx R2 F1: the cutter's stations carry a cross margin (signed into the card) and the result is cleaned")
    check('mouths = P.get("mouths")' in _rd("templates", "t_gapfill.py") and 'P.get("mouths", "any")' not in _rd("templates", "t_gapfill.py"), "31bx R2 F2: t_gapfill reads mouths without a silent 'any'")
except Exception as _e4:
    check(False, "31bx round 1 pins ran (%s)" % str(_e4)[:160])
print("\n[31ca] the dossier's material test by triangles (R1 F1)")
try:
    _kd2 = open(os.path.join(HERE, "kit_dossier.py"), encoding="utf-8").read()
    _blk = _kd2.split("# >>> 31ca R1 F1 THE MATERIAL TEST\n", 1)[1].split("# <<< 31ca R1 F1 THE MATERIAL TEST", 1)[0]
    _ns = {"np": np}; exec(_blk, _ns)
    _Vp = np.array([[0, 0, 0], [100, 0, 0], [100, 100, 0], [0, 100, 0]], float); _Tp = np.array([[0, 1, 2], [0, 2, 3]])
    _bxc = [45, 55, 45, 55, -5, 5]; _stc = [46.667, 50.0, 53.333]                                              # stations
    _k, _s, _r, _n = _ns["_material_stations"](_Vp, _Tp, _bxc, 0, _stc)
    check(_n == 2 and _k == _stc and not _s and _r == (45.0, 55.0), "31ca R1 F1: a 10 mm box at a plate's centre - the plate's two triangles meet it (no vertex inside: the 31bx test had refused), every station kept, %s" % ((_n, _k, _s, _r),))
    _k, _s, _r, _n = _ns["_material_stations"](_Vp, _Tp, [45, 55, 45, 55, -5, 5], 2, [-3.333, 0.0, 3.333])
    check(_k == [0.0] and _s == [-3.333, 3.333], "31ca R1 F1: ...along z only the station in the plate's plane meets it, the two in the air are skipped, %s" % ((_k, _s),))
    _k, _s, _r, _n = _ns["_material_stations"](_Vp, _Tp, [45, 55, 45, 55, 45, 55], 0, _stc)
    check(_n == 0 and _k == [] and _r is None, "31ca R1 F1: the same box 50 mm above the plate - no triangle meets it, no station kept (the take refuses), %s" % ((_n, _k, _r),))
    # stations
    _Vs = np.array([[x_, y_, z_] for x_ in (0, 100) for y_ in (0, 100) for z_ in (0, 10)], float)
    _Ts = np.array([[0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3], [0, 4, 5], [0, 5, 1], [2, 3, 7], [2, 7, 6], [0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5]])
    _k, _s, _r, _n = _ns["_material_stations"](_Vs, _Ts, [20, 40, 10, 30, -2, 12], 2, [0.333, 5.0, 9.667])
    check(_k == [0.333, 5.0, 9.667] and not _s and _r == (0.0, 10.0), "31ca 2b R1 F1: a closed slab along z - the three stations inside the solid KEPT by the span 0..10 (the surface test had skipped all three), %s" % ((_k, _s, _r),))
    _k, _s, _r, _n = _ns["_material_stations"](_Vs, _Ts, [8, 22, 13, 27, -2, 20], 2, [1.667, 9.0, 16.333])
    check(_k == [1.667, 9.0] and _s == [16.333], "31ca 2b R1 F1: ...a box with air above - z 16.33 in the air SKIPPED, the two in the solid kept, %s" % ((_k, _s),))
    _tri = np.array([[[0, 0, 0], [10, 0, 0], [0, 10, 0]]], float)
    check(_ns["_tri_meets_box"](_tri, [6, 6, -1], [7, 7, 1]).tolist() == [False] and _ns["_tri_meets_box"](_tri, [4, 4, -1], [5, 5, 1]).tolist() == [True], "31ca R1 F1: the separating-axis test - a box beyond a triangle's hypotenuse (inside its bounding box) is separated, a box inside it is met")
    check("no station along %s crosses material inside the box" in _kd2 and "--axis <x|y|z>" in _kd2 and "_material_stations(V, T, bx, ax, list(__STATIONS__))" in _kd2, "31ca R1 F1: the take calls it and an axis with no station is refused naming --axis")
except Exception as _e5:
    check(False, "31ca R1 F1 pins ran (%s)" % str(_e5)[:160])
print("%d passed, %d FAILED" % (ok, bad))
sys.exit(1 if bad else 0)

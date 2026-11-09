"""selftest_skin.py - THE SKIN ROUTE's gates and its window (kit 31al, 2026-10-06), without a kernel.
the client, 2026-10-06: "There is a new burrito process and it works. The old process gets ~1/2 shelved and the new process needs
gates/hooks/setup so it can be tested on new edit regions."
Cases: sk_lib's walls and distances equal the agent's section-4 skinlib exactly (so the port changed no number on the run that worked);
its views come from the job's window and its changed regions; the SHELVED steps and JOIN=fuse refuse without SHELVED_OK and run
with it; a skin step refuses until reinsert STEP 1 wrote wall_caps.brep (the caps FIRST) and STEP 1 needs no piece; skin-network
refuses until the layout is judged and - on a symmetric edit - mirror-checked on THAT layout; the reinsert's STEP 2 refuses a skin
piece until it is judged and mirror-checked; the judge refuses frames of an earlier artefact."""
import os, sys, json, shutil, tempfile, hashlib, struct
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

root = tempfile.mkdtemp(prefix="skin_"); job = "JOBS"; folder = os.path.join(root, "claude_code", "jobs", job)
os.makedirs(os.path.join(folder, "skin", "review"))
WIN = [-24.0, 24.0, -150.0, -95.5, 65.0, 100.0]; PL = [0.0, -141.1483, 90.0, 0.0, -0.8191520442889919, -0.5735764363510462]
json.dump({"window": WIN, "planes": [PL]}, open(os.path.join(folder, "REBUILD_region.json"), "w"))
json.dump([[-24.0, 0, 0, -1, 0, 0], [24.0, 0, 0, 1, 0, 0], [0, -95.5, 0, 0, 1, 0], [0, 0, 65.0, 0, 0, -1], PL], open(os.path.join(folder, "walls.json"), "w"))
def stl(path):
    with open(path, "wb") as fh:
        fh.write(b"\0" * 80 + struct.pack("<I", 1) + struct.pack("<12fH", 0, 0, 1, 0, -120, 80, 1, -120, 80, 0, -119, 80, 0))
stl(os.path.join(folder, "piece.stl")); open(os.path.join(folder, "body.brep"), "wb").write(b"a body")
try:
    os.environ["RUN"] = folder
    sys.path.insert(0, os.path.join(HERE, "rebuild"))
    import sk_lib as K
    RAKE_P = np.array(PL[:3]); RAKE_N = np.array(PL[3:])
    P = np.random.RandomState(1).uniform([-30, -155, 60], [30, -90, 105], (4000, 3))
    d_cc = np.stack([P[:, 0] - WIN[0], WIN[1] - P[:, 0], P[:, 1] - WIN[2], WIN[3] - P[:, 1], P[:, 2] - WIN[4], WIN[5] - P[:, 2], -((P - RAKE_P) @ RAKE_N)], axis=1).min(axis=1)
    check(np.allclose(K.wall_dist(P), d_cc, atol=1e-9), "sk_lib.wall_dist equals the agent's section-4 skinlib on 4000 points (max diff %.1e)" % np.abs(K.wall_dist(P) - d_cc).max())
    in_cc = ((P[:, 0] >= WIN[0] - 0.2) & (P[:, 0] <= WIN[1] + 0.2) & (P[:, 1] >= WIN[2] - 0.2) & (P[:, 1] <= WIN[3] + 0.2) & (P[:, 2] >= WIN[4] - 0.2) & (P[:, 2] <= WIN[5] + 0.2) & (((P - RAKE_P) @ RAKE_N) <= 0.2))
    check((K.inwin(P, 0.2) == in_cc).all(), "sk_lib.inwin equals the agent's (margin 0.2)")
    check(len(K.WALLS) == 7 and K.wall_of(np.array([[-24.0, -120, 80], [-24.0, -100, 70]]))[0] == 0, "seven walls (six box planes + the cut plane), x0 first - the order the agent's caps are indexed by")
    v = K.views()
    check(len(v) == 10 and v[0][2] == tuple(WIN), "views without regions: 8 orbits + top + bottom over the job's window")
    json.dump({"regions": [{"id": 0, "status": "remake", "area_mm2": 300.0, "bbox": [3, -122, 72, 18, -109, 88], "centre": [10, -115, 80]}]}, open(os.path.join(folder, "skin", "regions.json"), "w"))
    v = K.views()
    check(len(v) == 11 and v[-1][0] == "close_R0" and abs(v[-1][2][0] - 0.0) < 1e-9, "a close-up at each changed region, framed on its box + 3 mm")
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
        def freecad(self): raise RuntimeError("THE GATES PASSED")
        def _wallclock(self): return None
    kit = Kit(root); out = []
    def run(*a):
        out.clear(); import builtins; p0 = builtins.print; builtins.print = lambda *x, **k: out.append(" ".join(str(y) for y in x))
        try: return KR.cmd(list(a), kit)
        except RuntimeError as ex: return "passed" if "GATES PASSED" in str(ex) else str(ex)
        finally: builtins.print = p0
    B = "BODY=" + os.path.join(folder, "body.brep")
    rc = run("decimate", "--job", job, "--tag", "t1", "--set", "REDUCTION=0.99", "--set", B)
    check(rc == 2 and "SHELVED" in " ".join(out), "decimate is SHELVED: refused without SHELVED_OK")
    rc = run("decimate", "--job", job, "--tag", "t1", "--set", "REDUCTION=0.99", "--set", B, "--set", "SHELVED_OK=a selftest of the shelving")
    check(rc == "passed", "decimate with SHELVED_OK=\"<why>\" goes on (got %r)" % (rc,))
    rc = run("skin-regions", "--job", job, "--tag", "t2", "--set", B)
    check(rc == 2 and "REINSERT FACES COME FIRST" in " ".join(out), "a skin step refuses before reinsert STEP 1 wrote wall_caps.brep")
    open(os.path.join(folder, "window_solid.brep"), "wb").write(b"w")
    rc = run("reinsert", "--job", job, "--tag", "t3", "--set", "STEP=1", "--set", B)
    check(rc == 2 and "THE CUTS ARE JUDGED BEFORE THE SKIN ROUTE" in " ".join(out), "31bq R7W D10: reinsert STEP 1 refuses without a region ok on content.brep (got %r)" % (rc,))
    open(os.path.join(folder, "content.brep"), "wb").write(b"content"); os.makedirs(os.path.join(folder, "review"), exist_ok=True)
    json.dump({"what": "region", "verdict": "ok", "note": "the selftest's cuts", "md5": KR._md5(os.path.join(folder, "content.brep")), "when": "2026-10-22 14:00:00"}, open(os.path.join(folder, "review", "REGION_CUTS_JUDGED.json"), "w"))
    rc = run("reinsert", "--job", job, "--tag", "t3", "--set", "STEP=1", "--set", B)
    dd = KR.step_defaults("reinsert", folder, "")
    check(rc == "passed" and dd.get("JOIN") == "sew" and dd.get("REGION") == "none", "reinsert STEP 1 runs with NO piece (the caps first); the join defaults to sew, REGION to none (got %r, %r, %r)" % (rc, dd.get("JOIN"), dd.get("REGION")))
    json.dump({"source_md5": "c1aaaaaa", "triangles": 3}, open(os.path.join(folder, "REBUILD_source.json"), "w")); KR.restart_on_new_source(folder, lambda *a, **k: None)
    rc = run("reinsert", "--job", job, "--tag", "t3b", "--set", "STEP=1", "--set", B)
    check(rc == "passed" and KR.cuts_verdict(folder, "region")[0], "31bq R7Wr (verify-route-end C1): a new source's RESTART keeps the region's verdict (the cuts are judged on content.brep) - STEP 1 after skin-source is not refused (got %r)" % (rc,))
    open(os.path.join(folder, "wall_caps.brep"), "wb").write(b"caps")
    rc = run("skin-regions", "--job", job, "--tag", "t2", "--set", B)
    check(rc == "passed", "with wall_caps.brep the skin steps run")
    rc = run("skin-network", "--job", job, "--tag", "t4", "--set", B)
    check(rc == 2 and "MIRROR" in " ".join(out), "skin-network refuses without the card's MIRROR decision (an empty value is a decision)")
    pj = os.path.join(folder, "skin", "patches.json"); json.dump({"patches": [1, 2]}, open(pj, "w"))
    rc = run("skin-network", "--job", job, "--tag", "t4", "--set", B, "--set", "MIRROR=")
    check(rc == 2 and "no verdict on the layout" in " ".join(out), "skin-network refuses until the layout is judged")
    for f in ("SP8_01_top.png", "SP12_01_wall0.png"): open(os.path.join(folder, "skin", "review", f), "wb").write(b"png")
    md = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()
    json.dump({"kind": "layout", "frames": ["SP8_01_top.png", "SP12_01_wall0.png"], "md5": md(pj)}, open(os.path.join(folder, "skin", "review", "LAYOUT_LOOK.json"), "w"))
    opened31cb(root, *[os.path.join(folder, "skin", "review", f) for f in ("SP8_01_top.png", "SP12_01_wall0.png")])
    say = lambda *a: out.append(" ".join(str(x) for x in a))
    out.clear(); rc = KR.judge(["--job", job, "--what", "layout", "--verdict", "ok", "--note", "every face one simple surface, both sides alike, nothing missing"], kit, say)
    check(rc == 0 and KR.cuts_verdict(folder, "layout")[0], "the layout judged ok on its frames")
    rc = run("skin-network", "--job", job, "--tag", "t4", "--set", B, "--set", "MIRROR=")
    check(rc == "passed", "a judged layout on an edit the card says is not symmetric: skin-network runs")
    # skin-labels
    json.dump({"plane": "x 0", "step": "skin-labels"}, open(os.path.join(folder, "skin", "MIRROR_DECISION.json"), "w"))
    rc = run("skin-network", "--job", job, "--tag", "t4", "--set", B, "--set", "MIRROR=x 0")
    check(rc == 2 and "no mirror check of the layout" in " ".join(out), "a symmetric edit: skin-network refuses without the layout's mirror check")
    mj = os.path.join(folder, "skin", "mirror_layout.json")
    json.dump({"plane": "x 0", "pass": False, "unpaired": [{"id": 7}], "pairs": [], "md5": md(pj)}, open(mj, "w"))
    rc = run("skin-network", "--job", job, "--tag", "t4", "--set", B, "--set", "MIRROR=x 0")
    check(rc == 2 and "FAILED" in " ".join(out), "a failed mirror check keeps skin-network shut")
    json.dump({"plane": "x 0", "pass": True, "unpaired": [], "pairs": [[1, 2]], "md5": md(pj)}, open(mj, "w"))
    rc = run("skin-network", "--job", job, "--tag", "t4", "--set", B, "--set", "MIRROR=x 0")
    check(rc == "passed" and json.load(open(os.path.join(folder, "skin", "MIRROR_DECISION.json")))["plane"] == "x 0", "a passed mirror check on THIS layout opens it; the decision is recorded")
    json.dump({"patches": [1, 2, 3]}, open(pj, "w"))
    rc = run("skin-network", "--job", job, "--tag", "t4", "--set", B, "--set", "MIRROR=x 0")
    check(rc == 2 and "earlier" in " ".join(out), "the layout changed: its old verdicts no longer count")
    pc = os.path.join(folder, "skin", "piece_skin.brep"); open(pc, "wb").write(b"the piece")
    rc = run("reinsert", "--job", job, "--tag", "t5", "--set", "STEP=2", "--set", B)
    check(rc == 2 and "no verdict on the skin" in " ".join(out), "reinsert STEP 2 refuses a skin piece nobody looked at")
    for f in ("SKIN_look_01_orbit_000.png",): open(os.path.join(folder, "skin", "review", f), "wb").write(b"png")
    opened31cb(root, os.path.join(folder, "skin", "review", "SKIN_look_01_orbit_000.png"))
    json.dump({"kind": "skin", "mesh_quality": {"defective": False, "cracks": 0}, "frames": ["SKIN_look_01_orbit_000.png"], "md5": md(pc), "original_faces": {"taken": True}}, open(os.path.join(folder, "skin", "review", "PIECE_LOOK.json"), "w"))
    out.clear(); KR.second(["--job", job, "--what", "skin", "--brief", "--shards", "1"], kit, say)
    KR.second(["--job", job, "--what", "skin", "--shard", "0", "--result", json.dumps({"shard": 0, "frames_opened": ["SKIN_look_01_orbit_000"], "defects": [], "verdict": "pass"})], kit, say)
    out.clear(); rc = KR.judge(["--job", job, "--what", "skin", "--verdict", "ok", "--note", "simple faces, clean borders, no lump or fold, both sides alike"], kit, say)
    rc = run("reinsert", "--job", job, "--tag", "t5", "--set", "STEP=2", "--set", B)
    check(rc == 2 and "mirror check of the piece" in " ".join(out), "judged, but the edit is symmetric: STEP 2 refuses without the piece's mirror check")
    json.dump({"plane": "x 0", "pass": True, "unpaired": [], "pairs": [[1, 2]], "md5": md(pc)}, open(os.path.join(folder, "skin", "mirror_piece.json"), "w"))
    rc = run("reinsert", "--job", job, "--tag", "t5", "--set", "STEP=2", "--set", B)
    check(rc == "passed", "judged and mirror-checked: the sew goes on (got %r)" % (rc,))
    rc = run("reinsert", "--job", job, "--tag", "t5", "--set", "STEP=2", "--set", B, "--set", "JOIN=fuse")
    check(rc == 2 and "SHELVED" in " ".join(out), "reinsert JOIN=fuse is SHELVED")
    open(pc, "wb").write(b"the piece, rebuilt")
    rc = run("reinsert", "--job", job, "--tag", "t5", "--set", "STEP=2", "--set", B)
    check(rc == 2 and "earlier" in " ".join(out), "a rebuilt piece needs a new look")
finally:
    shutil.rmtree(root, ignore_errors=True)
print("%d passed, %d FAILED" % (ok, bad))
sys.exit(1 if bad else 0)

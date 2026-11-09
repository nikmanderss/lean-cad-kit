"""selftest_skin3.py - kit 31as (2026-10-07), without a kernel: THE FEATURE MAP (sk_features.py) and THE WIREFRAME (sk_wires.py) as kit steps.
the client: "Feature map and wireframe: - should be CAD generic kit steps. They work correctly for the process and adjusting them makes step 4 complete
correctly, they do not rely on a step 4 finish to make it into the kit."
Cases: sk_features RUN on a synthetic layout (numpy + PIL only) - symmetric (a V across x 0) and not - the features merged, a small smooth face
joined, a V's crease kept, the raw layout kept and re-used, FEATURES recorded for skin-wires and dropped when not given, the pictures drawn, a
malformed FEATURES refused; sk_wires compiled and free of a section (no x > 0.3 master side, no ON_VOX, numbers behind SHOW_NUMBERS, any mirror
plane or none for RAILS); the runner's order (skin-features after skin-labels, skin-wires after skin-frame) and outputs.
At the port (2026-10-07 13:5x, not repeated here - it needs the agent's job folder): sk_features against the agent's job_skin_merge_smooth.py on the same two
synthetic layouts gave byte-identical patches_labels.npz and patch lists."""
import os, sys, json, shutil, tempfile, subprocess, hashlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ok = 0; bad = 0
def check(cond, what):
    global ok, bad
    if cond: ok += 1; print("  ok   " + what)
    else: bad += 1; print("  FAIL " + what)
md = lambda p: hashlib.md5(open(p, "rb").read()).hexdigest()
SKF = os.path.join(HERE, "rebuild", "sk_features.py"); SKW = os.path.join(HERE, "rebuild", "sk_wires.py")

def make_job(run, sym):
    """a 10 x 10 mm V (z = 0.3 |x|, the crease on x = 0): master side x < 0 - A (x < -2, an ORIGINAL face 101) with a 0.5 mm2 sliver D
    (104), B (-2..-1.5, 102), C (-1.5..0, 103); the + side their mirror twins (labels + 1e6). Not symmetric: six faces, no mirror."""
    os.makedirs(os.path.join(run, "skin", "review"), exist_ok=True)
    json.dump({"window": [-5.0, 5.0, 0.0, 10.0, -1.0, 3.0], "planes": []}, open(os.path.join(run, "REBUILD_region.json"), "w"))
    nx, ny = 40, 20; xs = np.linspace(-5, 5, nx + 1); ys = np.linspace(0, 10, ny + 1)
    X, Y = np.meshgrid(xs, ys, indexing="ij"); V = np.stack([X.ravel(), Y.ravel(), (0.3 * np.abs(X)).ravel()], 1)
    idx = lambda i, j: i * (ny + 1) + j; T = []
    for i in range(nx):
        for j in range(ny):
            a, b, c, d = idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1); T += [[a, b, c], [a, c, d]]
    F = np.array(T); np.savez(os.path.join(run, "skin", "regions.npz"), Vu=V, F=F)
    Cn = V[F].mean(1); N = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]); N /= np.linalg.norm(N, axis=1)[:, None]
    ax = np.abs(Cn[:, 0]); side = np.sign(Cn[:, 0])
    base = np.where(ax > 2.0, 0, np.where(ax > 1.5, 1, 2)); base[(ax > 2.0) & (Cn[:, 1] < 0.5) & (ax < 3.0)] = 3
    fsrc = {0: 101, 1: 102, 2: 103, 3: 104}
    if sym:
        patch = np.where(side < 0, base, base + 4); PJ = []
        for t in (0, 1):
            for k in range(4):
                PJ.append({"patch": k + 4 * t, "kind": "orig" if k == 0 else "changed", "label": fsrc[k] + 1000000 * t, "grp": k, "mirror_of": None if t == 0 else k,
                           "face_src": fsrc[k], "src": ("master %d" if t == 0 else "mirror of %d") % k, **({"face": fsrc[k]} if k == 0 else {})})
        json.dump({"plane": "x 0"}, open(os.path.join(run, "skin", "MIRROR_DECISION.json"), "w")); mir = {"master": "-", "plane": "x 0"}
        feat = {"flank": [101, 102, 104], "spine": [103], "_why": {"flank": "the three flank faces are one smooth side (the synthetic layout)", "spine": "the spine is its own face (the synthetic layout)"}}
    else:
        patch = np.where(side < 0, base, np.where(ax > 1.0, 4, 5))
        PJ = [{"patch": k, "kind": "changed", "label": 100 + k, "grp": None, "mirror_of": None, "face_src": 100 + k, "src": "p%d" % k} for k in range(6)]
        mir = None; feat = {"left": [100, 101, 103], "mid": [102], "_why": {"left": "the left faces are one feature (the synthetic layout)", "mid": "the middle face stays its own (the synthetic layout)"}}
    lab = np.array([PJ[p]["label"] for p in patch])
    np.savez(os.path.join(run, "skin", "patches_labels.npz"), lab=lab, patch=patch, Nn=N)
    json.dump({"source": "selftest", "mirror": mir, "patches": PJ}, open(os.path.join(run, "skin", "patches_labels.json"), "w"), indent=1)
    json.dump(feat, open(os.path.join(run, "FEAT.json"), "w"))
    return run

def run_feat(run, **env):
    e = dict(os.environ); e.update({"RUN": run, "KIT_HOME": HERE, "PYTHONIOENCODING": "utf-8"}); e.pop("FEATURES", None)
    e.update({k: str(v) for k, v in env.items()})
    p = subprocess.run([sys.executable, SKF], env=e, capture_output=True, text=True, timeout=300)
    return p.returncode, p.stdout + p.stderr

root = tempfile.mkdtemp(prefix="skin3_")
try:
    # THE FEATURE MAP
    run = make_job(os.path.join(root, "sym"), True)
    rc, out = run_feat(run, FEATURES=os.path.join(run, "FEAT.json"))
    J = json.load(open(os.path.join(run, "skin", "patches_labels.json"))); sk = [p for p in J["patches"] if p["kind"] != "cap"]
    check(rc == 0 and "FACES: 2 skin faces" in out, "symmetric: the features merge the eight faces to one per side (FACES: 2 skin faces) [%s]" % out.strip().splitlines()[-3:] if rc else "symmetric: the features merge the eight faces to one per side (FACES: 2 skin faces)")
    Z = np.load(os.path.join(run, "skin", "patches_labels.npz")); Rg = np.load(os.path.join(run, "skin", "regions.npz"))
    Cn = Rg["Vu"][Rg["F"]].mean(1)
    check(len(set(Z["patch"][Cn[:, 0] < 0])) == 1 and len(set(Z["patch"][Cn[:, 0] > 0])) == 1 and set(Z["patch"][Cn[:, 0] < 0]) != set(Z["patch"][Cn[:, 0] > 0]),
          "a face and its own twin across the plane stay TWO faces - the V keeps its crease")
    check(all(p["kind"] == "changed" for p in sk), "a merged face over an original surface and others is fitted (kind changed), never the original stretched")
    check(os.path.isfile(os.path.join(run, "skin", "patches_labels_raw.json")) and json.load(open(os.path.join(run, "skin", "patches_labels_raw.json")))["patches"][0]["kind"] == "orig",
          "skin-labels' own layout is kept as patches_labels_raw.* (every run works from it)")
    check(json.load(open(os.path.join(run, "skin", "features.json"))) == json.load(open(os.path.join(run, "FEAT.json"))), "the FEATURES used are recorded (skin\\features.json - skin-wires' RAILS read it)")
    pics = sorted(f for f in os.listdir(os.path.join(run, "skin", "review")) if f.startswith("FEAT_"))
    check(len([f for f in pics if f.startswith("FEAT_labels_")]) == 6 and len([f for f in pics if f.startswith("FEAT_features_")]) == 6, "the pictures: FEAT_labels_* (the ids) and FEAT_features_* (named), six views each")
    check("merge_smooth" in J and J["merge_smooth"]["FEATURES"], "the layout carries the step's record (skin-rim checks it: the feature map came first)")
    n1 = md(os.path.join(run, "skin", "patches_labels.npz"))
    rc, out = run_feat(run, FEATURES=os.path.join(run, "FEAT.json"))
    check(rc == 0 and md(os.path.join(run, "skin", "patches_labels.npz")) == n1 and "skin-labels' layout kept" not in out,
          "run again with the same FEATURES: the same layout, from the kept raw one (not from its own output)")
    rc, out = run_feat(run)
    check(rc == 0 and not os.path.isfile(os.path.join(run, "skin", "features.json")) and "no FEATURES" in out and "FACES:" in out,
          "without FEATURES: only the smooth merges, the old feature record dropped (L119), the agent told to name the features")
    json.dump({"flank": "101"}, open(os.path.join(run, "BAD.json"), "w"))
    rc, out = run_feat(run, FEATURES=os.path.join(run, "BAD.json"))
    check(rc != 0 and "FAIL: FEATURES" in out, "a FEATURES that is not {feature: [ids]} is refused with the shape it must have")
    rc, out = run_feat(run, FEATURES=os.path.join(run, "FEAT.json"), SHOW_NUMBERS="0")
    check(rc == 0 and "mm2" not in out and "border" not in out.split("FACES:")[0].split("FEATURES")[-1], "31ar: no sizes on the screen unless SHOW_NUMBERS=1")
    run2 = make_job(os.path.join(root, "nosym"), False)
    rc, out = run_feat(run2, FEATURES=os.path.join(run2, "FEAT.json"))
    check(rc == 0 and "FACES: 2 skin faces" in out and "UNITED" not in out, "not symmetric (no mirror decision): the same step, no twins, no plane")
    import ast
    src = open(SKW, encoding="utf-8").read(); ast.parse(src)
    check(True, "sk_wires.py compiles")
    code = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
    check("m_[0] > 0.3" not in code and "side < 0 else" not in code and "for side in (-1.0, 1.0)" not in code,
          "no section-4 side left: the chain numbers and the rails follow skin-labels' master side on ANY plane (or none)")
    check("ON_VOX =" not in code and "on_voxel(" not in code, "ON_VOX (a line laid back onto the voxel) is not ported - the client: \"'that follow the voxel's original design lines,' IS WRONG\"")
    check("if SHOW_NUMBERS:" in code and "num(" in code, "31ar: the deviations and distances are behind SHOW_NUMBERS")
    check('K.write_look("wires"' in code and "corners.json" in code and "CORNERS_" in code, "it writes WIRES_LOOK.json (the judge's frames), corners.json and the CORNERS_* pictures")
    sys.path.insert(0, os.path.join(HERE, "rebuild")); os.environ["RUN"] = run
    import importlib, sk_lib as K; importlib.reload(K)
    K.write_look("wires", [os.path.join(run, "skin", "review", "FEAT_labels_top.png")], os.path.join(run, "skin", "patches_labels.npz"))
    check(os.path.isfile(os.path.join(run, "skin", "review", "WIRES_LOOK.json")), "sk_lib.write_look knows the wires' look (WIRES_LOOK.json)")
    import kit_rebuild as KR
    order = [k for k, _, _, _, _ in KR.STEPS]
    check(order.index("skin-features") == order.index("skin-labels") + 1 and order.index("skin-rim") == order.index("skin-features") + 1,
          "the runner: skin-labels -> skin-features -> skin-rim")
    check(order.index("skin-wires") == order.index("skin-frame") + 1 and order.index("skin-build") == order.index("skin-wires") + 1,
          "the runner: skin-frame -> skin-wires -> skin-build")
    check(all(x in KR.LEVERS for x in ("FEATURES", "LINES", "RAILS", "MAX_AREA", "TOL_LINE", "WIRE_PICS")) and "skin-features" in KR.SKIN and "skin-wires" in KR.AFTER_POINTS,
          "their levers are known, they are skin steps, and the restart's lock covers them")
    outs = KR.step_outputs("skin-wires", {"RUN": run}); outs2 = KR.step_outputs("skin-features", {"RUN": run})
    check(any(o.endswith("network_frame.brep") for o in outs) and any(o.endswith("patches_labels.json") for o in outs2), "their outputs are declared (kept per tag; .FAILED / .KILLED on a failure)")
    check("wires" in KR.JUDGED and KR.JUDGED["wires"][3].endswith("network_frame.brep"), "`kit rebuild judge --what wires` judges the frames of THIS network_frame.brep")
    import sk_lib as K2
    def strip_(prof, ny=10, L=10.0):
        Vs = []; Ts = []; n_ = len(prof)
        for y in np.linspace(0, L, ny + 1):
            for x, z in prof: Vs.append((x, y, z))
        for j in range(ny):
            for i in range(n_ - 1):
                a = j * n_ + i; b = a + 1; c = a + n_; d = c + 1; Ts += [[a, c, b], [b, c, d]]
        return np.array(Vs, float), np.array(Ts)
    th = np.linspace(np.pi, 2 * np.pi, 13)
    VU, TU = strip_([(-2.0, 6.0 - k) for k in range(6)] + [(2 * np.cos(t), 2 * np.sin(t)) for t in th] + [(2.0, float(k)) for k in range(1, 7)])
    VA = np.array([(-6.0, 0, -1), (-6.0, 10, -1), (-6.0, 10, 3), (-6.0, 0, 3)]); TA = np.array([[0, 2, 1], [0, 3, 2]])
    VB = np.array([(6.0, 0, -1), (6.0, 10, -1), (6.0, 10, 3), (6.0, 0, 3)]); TB = np.array([[0, 1, 2], [0, 2, 3]])
    Vm = np.vstack([VU, VA, VB]); Tm = np.vstack([TU, TA + len(VU), TB + len(VU) + len(VA)]); fm = np.concatenate([np.zeros(len(TU), int), np.ones(2, int), np.full(2, 2)])
    NSm, ARm = K2.face_area_normals(Vm, Tm, fm, 3); Nm = NSm / np.linalg.norm(NSm, axis=1)[:, None]
    Pm = Vm[Tm]; crm = 0.5 * np.cross(Pm[:, 1] - Pm[:, 0], Pm[:, 2] - Pm[:, 0])
    Cm = np.array([(Pm.mean(1)[fm == k] * np.linalg.norm(crm[fm == k], axis=1)[:, None]).sum(0) / ARm[k] for k in range(3)])
    vn = np.zeros_like(Vm)
    for q_ in range(3): np.add.at(vn, Tm[:, q_], crm)
    idx = np.unique(Tm[fm == 0].ravel()); jn = idx[np.argmin(np.linalg.norm(Vm[idx] - Cm[0], axis=1))]
    old = np.array([vn[jn] / np.linalg.norm(vn[jn]), Nm[1], Nm[2]])
    mn_, mc_ = K2.mirror_plane("x 0")
    _, u_old, _ = K2.mirror_pairs(Cm, ARm, old, np.sqrt(ARm), mn_, mc_, 1.5, 0.35)
    p_new, u_new, _ = K2.mirror_pairs(Cm, ARm, Nm, np.sqrt(ARm), mn_, mc_, 1.5, 0.35)
    check(u_old == [0] and abs(old[0][0]) > 0.9, "31at: the bug reproduced - a U spanning the plane, its direction taken where the surface is nearest its centre of mass (on an arm), is UNPAIRED")
    check(u_new == [] and (0, 0) in p_new and (1, 2) in p_new and abs(Nm[0][0]) < 1e-6, "31at: by its area-weighted normal the U pairs with itself, and the mirror twins still pair")
    Nz = Nm.copy(); Nz[0] = 0.0
    p_z, u_z, _ = K2.mirror_pairs(Cm, ARm, Nz, np.sqrt(ARm), mn_, mc_, 1.5, 0.35)
    check(u_z == [] and (0, 0) in p_z, "31at: a face with no direction (its normals cancel - a tube) is held to centre and area only")
    Csh = Cm.copy(); Csh[0][0] = 2.5
    _, u_sh, _ = K2.mirror_pairs(Csh, ARm, Nm, np.sqrt(ARm), mn_, mc_, 1.5, 0.35)
    check(0 in u_sh, "31at: a face off the plane with no twin is still UNPAIRED - the fix pairs a symmetric face, not any face")
    runm = make_job(os.path.join(root, "mir"), True)
    Zl = np.load(os.path.join(runm, "skin", "patches_labels.npz")); pidl = Zl["patch"]
    np.savez(os.path.join(runm, "skin", "patches.npz"), patch=pidl)
    json.dump({"patches": [{"patch": k, "kind": "changed"} for k in range(8)]}, open(os.path.join(runm, "skin", "patches.json"), "w"))
    def run_mirror(rn):
        e = dict(os.environ); e.update({"RUN": rn, "KIT_HOME": HERE, "WHAT": "layout", "MIRROR": "x 0", "PYTHONIOENCODING": "utf-8"})
        p_ = subprocess.run([sys.executable, os.path.join(HERE, "rebuild", "sk_mirror.py")], env=e, capture_output=True, text=True, timeout=300)
        return p_.returncode, p_.stdout + p_.stderr
    rc, out = run_mirror(runm)
    check(rc == 0 and "MIRROR CHECK PASS" in out and json.load(open(os.path.join(runm, "skin", "mirror_layout.json")))["pass"], "sk_mirror WHAT=layout runs on the pairing in sk_lib: a symmetric layout PASSES")
    pid2 = pidl.copy(); pid2[pid2 == 5] = 4; np.savez(os.path.join(runm, "skin", "patches.npz"), patch=pid2)
    json.dump({"patches": [{"patch": k, "kind": "changed"} for k in (0, 1, 2, 3, 4, 6, 7)]}, open(os.path.join(runm, "skin", "patches.json"), "w"))
    rc, out = run_mirror(runm)
    check(rc != 0 and "UNPAIRED" in out and "FAIL: THE MIRROR CHECK" in out, "a face missing on one side still FAILS the check (UNPAIRED, with its place)")
finally:
    shutil.rmtree(root, ignore_errors=True)
print("%d passed, %d FAILED" % (ok, bad))
sys.exit(1 if bad else 0)

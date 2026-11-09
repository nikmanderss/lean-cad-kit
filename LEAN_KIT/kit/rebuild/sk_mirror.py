# skin-rim
# kit rebuild  skin-network
# is its own mirror
import os, sys, json
if not globals().get("_SK_INNER"):      # 31br D3 (2026-10-29): a crash's TRACEBACK reaches the log
    import runpy as _rp3, traceback as _tb3
    try: _rp3.run_path(os.path.abspath(__file__), init_globals={"_SK_INNER": True}, run_name="__main__")
    except SystemExit: raise
    except BaseException:
        print("TRACEBACK (31br D3) - the crash's place:\n" + _tb3.format_exc(), flush=True); raise
    raise SystemExit(0)
import numpy as np
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sk_lib as K; RUN = K.RUN; K.need_window()
WHAT = os.environ.get("WHAT", "layout").strip().lower()
MIRROR = os.environ.get("MIRROR", "").strip() or (K.mirror_decision() or "")   # skin-labels
TOL = float(os.environ.get("MIRROR_TOL", "1.5")); AREA = float(os.environ.get("MIRROR_AREA", "0.35"))
if WHAT not in ("layout", "piece"): K._fail("FAIL: WHAT is layout or piece, not %r" % WHAT)
if not MIRROR: K._fail("FAIL: MIRROR is empty - the mirror check needs the plane the edit is symmetric about (\"x 0\"); an edit that is not symmetric has no mirror check")
try:
    MN, MC = K.mirror_plane(MIRROR)
except ValueError as _ex:
    K._fail("FAIL: %s" % _ex)
SK = K.SK; OUT = K.OUT


def refl(P):
    return K.reflect(P, MN, MC)


if WHAT == "layout":
    src = os.path.join(SK, "patches.json")
    if not os.path.isfile(src): K._fail("FAIL: skin\\patches.json is missing - `kit rebuild skin-rim` writes the layout")
    Z = np.load(os.path.join(SK, "regions.npz")); Vu, F = Z["Vu"], Z["F"]
    pid = np.load(os.path.join(SK, "patches.npz"))["patch"]
    PJ = json.load(open(src, encoding="utf-8"))["patches"]
    Tv = Vu[F]; Cn = Tv.mean(1); Nr = np.cross(Tv[:, 1] - Tv[:, 0], Tv[:, 2] - Tv[:, 0]); At = 0.5 * np.linalg.norm(Nr, axis=1)
    faces = []
    for p in PJ:
        m = pid == p["patch"]
        if not m.any(): continue
        a = float(At[m].sum()); c = (Cn[m] * At[m, None]).sum(0) / max(a, 1e-12); n = Nr[m].sum(0)
        faces.append({"id": int(p["patch"]), "kind": p.get("kind", "?"), "c": c, "a": a, "n": n / max(np.linalg.norm(n), 1e-12), "size": float(np.sqrt(a))})
    TRI = (Vu, F, pid); MQm = K.mesh_quality(np.asarray(Vu, float), np.asarray(F, int), np.asarray(pid, int), closed=False, judge_open=False); MQm.update({"dev_mm": 0.05, "how": "the layout's source mesh"})
else:
    import Part, FreeCAD
    src = os.path.join(SK, "piece_skin.brep")
    if not os.path.isfile(src): K._fail("FAIL: skin\\piece_skin.brep is missing - `kit rebuild skin-build` writes the piece")
    sh = Part.Shape(); sh.importBrep(src)
    okf = [i for i, f in enumerate(sh.Faces) if f.isValid()]
    Vp, Tp, Fp, _mq = K.piece_mesh(src, sh, faces=(None if len(okf) == len(sh.Faces) else okf)); Vp = np.asarray(Vp, float); Tp = np.asarray(Tp, int); FIDp = np.asarray(okf)[np.asarray(Fp, int)] if len(okf) != len(sh.Faces) else np.asarray(Fp, int)
    TRI = (Vp, Tp, FIDp); MQm = _mq
    NS, AR = K.face_area_normals(Vp, Tp, FIDp, len(sh.Faces))
    faces = []; nweak = 0; nold = 0
    for i, f in enumerate(sh.Faces):
        cm = f.CenterOfMass; c = np.array([cm.x, cm.y, cm.z])
        n = NS[i].copy(); how = "area-weighted"
        if AR[i] > 0:
            m_ = np.nonzero(FIDp == i)[0]; P_ = Vp[Tp[m_]]; cr_ = np.cross(P_[:, 1] - P_[:, 0], P_[:, 2] - P_[:, 0]); k_ = int(np.argmax(np.linalg.norm(cr_, axis=1)))
            try:
                u, v = f.Surface.parameter(FreeCAD.Vector(*P_[k_].mean(0))); nn = f.normalAt(u, v)
                if float(cr_[k_] @ np.array([nn.x, nn.y, nn.z])) < 0: n = -n
            except Exception:
                pass
            st = float(np.linalg.norm(n)) / max(float(AR[i]), 1e-12)
            if st < 0.2: n = np.zeros(3); how = "no direction (its normals cancel)"; nweak += 1
        else:
            try:
                u, v = f.Surface.parameter(cm); nn = f.normalAt(u, v); n = np.array([nn.x, nn.y, nn.z]); how = "the normal at its centre (no tessellation)"; nold += 1
            except Exception:
                n = np.zeros(3); how = "no direction"
        faces.append({"id": i, "kind": "face", "c": c, "a": float(f.Area), "n": n / max(np.linalg.norm(n), 1e-12) if np.linalg.norm(n) > 0 else n,
                      "size": float(np.sqrt(max(f.Area, 0))), "how": how})
    print("piece faces' directions: area-weighted normals (31at)%s%s" % ((", %d whose normals cancel pair by centre and area" % nweak) if nweak else "",
          (", %d not tessellated keep the normal at their centre" % nold) if nold else ""), flush=True)
print("mirror check of the %s: %d faces, plane %s" % (WHAT, len(faces), MIRROR), flush=True)

C = np.array([f["c"] for f in faces]); A = np.array([f["a"] for f in faces]); N = np.array([f["n"] for f in faces]); S = np.array([f["size"] for f in faces])
Rc = refl(C)
pairs, unp, mate = K.mirror_pairs(C, A, N, S, MN, MC, TOL, AREA)
side = lambda i: "on the plane" if abs(float(K.mirror_side(C[i], MN, MC))) < max(TOL, 0.25 * S[i]) else ("+" if float(K.mirror_side(C[i], MN, MC)) > 0 else "-")
plus = sum(1 for i in range(len(faces)) if side(i) == "+"); minus = sum(1 for i in range(len(faces)) if side(i) == "-")
print("faces: %d on the + side, %d on the - side, %d on the plane; pairs %d (%d self-paired on the plane); UNPAIRED %d"
      % (plus, minus, len(faces) - plus - minus, len(pairs), sum(1 for i, j in pairs if i == j), len(unp)), flush=True)
for i in unp:
    print("   UNPAIRED %s %d (%s): %.1f mm2 at (%.1f, %.1f, %.1f), %s side - no face of like area at its mirror (%.1f, %.1f, %.1f)"
          % ("patch" if WHAT == "layout" else "face", faces[i]["id"], faces[i]["kind"], A[i], C[i][0], C[i][1], C[i][2], side(i), Rc[i][0], Rc[i][1], Rc[i][2]), flush=True)
worst = sorted(((float(np.linalg.norm(Rc[i] - C[j])), abs(A[i] - A[j]), i, j) for i, j in pairs if i != j), reverse=True)[:5]
for dc, da, i, j in worst:
    print("   loosest pair %d|%d: centres %.2f mm apart after the mirror, areas %.1f / %.1f mm2" % (faces[i]["id"], faces[j]["id"], dc, A[i], A[j]), flush=True)
rec = {"what": WHAT, "plane": MIRROR, "pass": not unp, "faces": len(faces), "plus": plus, "minus": minus, "pairs": [[faces[i]["id"], faces[j]["id"]] for i, j in pairs],
       "unpaired": [{"id": faces[i]["id"], "kind": faces[i]["kind"], "area_mm2": round(A[i], 2), "centre": [round(float(v), 2) for v in C[i]], "side": side(i)} for i in unp],
       "checked": os.path.relpath(src, RUN), "md5": K.md5(src), "tag": K.TAG, "tol_mm": TOL, "area_frac": AREA,
       "direction": "area-weighted normal (31at)" if WHAT == "piece" else "summed triangle normals"}

# over the
V_, T_, own = TRI
pal = np.array(K.PALETTE); colr = np.full((len(faces), 3), 0.55)
for k, (i, j) in enumerate(pairs): colr[i] = pal[k % len(pal)]; colr[j] = pal[k % len(pal)]
for i in unp: colr[i] = (1.0, 0.12, 0.12)
idmap = {f["id"]: k for k, f in enumerate(faces)}
Ct = np.array([colr[idmap[int(o)]] if int(o) in idmap else (0.4, 0.4, 0.4) for o in own])
frames = []
MKEY = K.pic_key(src, plane=MIRROR, what=WHAT)
for nm, d in (("top", (0, 0, -1)), ("bottom", (0, 0, 1))):
    path = os.path.join(OUT, "MIRROR_%s_%s.png" % (WHAT, nm))
    if K.pic_hit(path, MKEY): frames.append(os.path.basename(path)); continue
    _ttl = "MIRROR CHECK of the %s - %s - %s: %d pair(s), %d UNPAIRED (red)" % (WHAT, nm, "PASS" if not unp else "FAIL", len(pairs), len(unp))
    K.view_piece(R, path, V_, T_, np.asarray(own, int), Ct, d, K.WIN, 1400, "mirror %s" % nm, _ttl, ["The pairs in matching colours, UNPAIRED red; smooth-shaded within each face; a red RENDER DEFECTIVE banner across the frame = NO EVIDENCE."], quality=MQm)
    K.pic_mark(path, MKEY); frames.append(os.path.basename(path))
rec["frames"] = frames
print(K.pic_report("MIRROR_%s_*" % WHAT), flush=True)
with open(os.path.join(SK, "mirror_%s.json" % WHAT), "w", encoding="utf-8") as fh:
    json.dump(rec, fh, indent=1)
print("skin\\mirror_%s.json written; pictures %s" % (WHAT, ", ".join(frames)), flush=True)
if unp:
    K._fail("FAIL: THE MIRROR CHECK of the %s - %d face(s) with no partner across %s (the client 2026-10-06: a face on one side with no partner on the other is a defect) - fix the %s and run it again"
            % (WHAT, len(unp), MIRROR, "layout (skin-labels / skin-rim)" if WHAT == "layout" else "piece (the layout, then skin-build)"))
print("MIRROR CHECK PASS: every face of the %s has its mirror partner" % WHAT, flush=True)
print("DONE", flush=True)

# kit rebuild
# crumpled
# kit rebuild
# ORIGINAL
# ORIGINAL_FACES.json  NOT TAKEN
import os, sys, json, glob
if not globals().get("_SK_INNER"):      # 31br D3 (2026-10-29): a crash's TRACEBACK reaches the log
    import runpy as _rp3, traceback as _tb3
    try: _rp3.run_path(os.path.abspath(__file__), init_globals={"_SK_INNER": True}, run_name="__main__")
    except SystemExit: raise
    except BaseException:
        print("TRACEBACK (31br D3) - the crash's place:\n" + _tb3.format_exc(), flush=True); raise
    raise SystemExit(0)
import numpy as np
import Part, FreeCAD
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sk_lib as K; RUN = K.RUN; K.need_window()
from PIL import Image, ImageDraw
SK = K.SK; OUT = K.OUT
shp = os.environ.get("SHAPE") or (os.path.join(SK, "piece_skin.brep") if os.path.isfile(os.path.join(SK, "piece_skin.brep")) else os.path.join(SK, "shell_c.brep"))
if not os.path.isfile(shp): K._fail("FAIL: no skin to look at (%s) - `kit rebuild skin-build` writes it" % shp)
PREFIX = os.environ.get("LOOK_PREFIX", "SKIN_look")
try:
    _old_look = json.load(open(os.path.join(OUT, "PIECE_LOOK.json"), encoding="utf-8")); OLD_INFO = _old_look.get("frame_info") or (_old_look.get("info") or {}).get("frame_info") or {}
except (OSError, ValueError, AttributeError): OLD_INFO = {}
sh = Part.Shape(); sh.importBrep(shp)
# open edges
_ecount = {}
for _f in sh.Faces:
    for _e in _f.Edges:
        try: _seam = bool(_e.isSeam(_f))
        except Exception: _seam = False
        _ecount[_e.hashCode()] = _ecount.get(_e.hashCode(), 0) + (2 if _seam else 1)
FREE_E = [e for e in sh.Edges if _ecount.get(e.hashCode(), 0) == 1 and e.Length > 1e-6]
frp = os.path.join(SK, "free_c.brep")
if os.path.isfile(frp): print("free_c.brep is not read - the piece's own edges say where it is open (%d free edge(s))" % len(FREE_E), flush=True)
LOOK_TOL_MAX = float(os.environ.get("LOOK_TOL_MAX", "1.0") or 1.0)
_big = [i for i, f in enumerate(sh.Faces) if f.isValid() and max([e.Tolerance for e in f.Edges] + [0.0]) > LOOK_TOL_MAX]
okf = [i for i, f in enumerate(sh.Faces) if f.isValid() and i not in _big]
def _kind(f_):
    try: return type(f_.Surface).__name__.lower()
    except Exception: return "curved"
if _big: print("faces %s carry an edge tolerance over LOOK_TOL_MAX %g mm - drawn by their edges only (yellow), not shaded (31bl)" % (_big, LOOK_TOL_MAX), flush=True)
if not okf: K._fail("FAIL: no face of the piece can be meshed - every face is not valid or carries an edge tolerance over LOOK_TOL_MAX %g mm (31bs T3 F1): raise LOOK_TOL_MAX, or look at the build first" % LOOK_TOL_MAX)
# LOOK_ANG
LOOK_ANG = float(os.environ.get("LOOK_ANG", "0") or 0)
# LOOK_VIS
LOOK_VIS = float(os.environ.get("LOOK_VIS", "0.6") or 0.6)
# MeshPart
# LOOK_ANG
V, T, FID, MQ = K.piece_mesh(shp, sh, faces=(None if len(okf) == len(sh.Faces) else okf), ang=(LOOK_ANG if LOOK_ANG > 0 else None), say=lambda m_: print(m_, flush=True))
V = np.asarray(V, float); T = np.asarray(T, int); FID = np.asarray(FID, int)
print("piece %s: %d faces, %d drawn shaded (valid), the rest by their edges%s" % (os.path.basename(shp), len(sh.Faces), len(okf), (" - RENDER DEFECTIVE: %s - these frames are NO EVIDENCE" % MQ["why_mesh"]) if MQ.get("defective_mesh") else ((" - the mesh has %d crack(s): the frames that show one are stamped" % MQ["cracks"]) if MQ.get("cracks") else "")), flush=True)
LKEY = K.pic_key(shp, os.path.join(SK, "piece_faces.json"), LOOK_ANG=LOOK_ANG, LOOK_VIS=LOOK_VIS, LOOK_TOL_MAX=LOOK_TOL_MAX, PIC_DEV=K.PIC_DEV, PIC_ANG=K.PIC_ANG, view="piece31bn4", free=len(FREE_E), mesh_q=("%s|%s" % (MQ.get("defective"), MQ.get("why", "")[:60])),
                 LOOK_MIN=os.environ.get("LOOK_MIN_MM2", "2.0"), PIC_W=int(getattr(R, "PIC_W", 0) or 0), prefix=PREFIX)
# skin-wires  fillets.json
VKEY = K.pic_key(shp, os.path.join(SK, "piece_faces.json"), *[os.path.join(SK, f_) for f_ in ("regions.npz", "patches.npz", "patches.json", "features.json", "points1000.json", "fillets.json", "network.json", "network_frame.brep")],
                 view="vanished-r7w", PIC_DEV=K.PIC_DEV, PIC_ANG=K.PIC_ANG, VANISH=(K.VANISH_MM, K.VANISH_MM2, K.VANISH_LINK, K.VANISH_CAP, K.VANISH_FRAMES), mesh_q=("%s|%s" % (MQ.get("defective"), MQ.get("why", "")[:60])), PIC_W=int(getattr(R, "PIC_W", 0) or 0), prefix=PREFIX)
K.clear_frames(PREFIX + "_", LKEY, also=(VKEY,))
rng = np.random.RandomState(3); fc = rng.uniform(0.45, 0.85, (len(sh.Faces), 3)); FIDg = np.asarray(okf)[FID]; C = fc[FIDg]
dz = lambda e, s_: np.array([[q.x, q.y, q.z] for q in e.discretize(Number=max(2, int(e.Length / s_)))])
okset = set(okf)
bad_e = [dz(e, 0.05) for i, f in enumerate(sh.Faces) if i not in okset for e in f.Edges if e.Length > 1e-6]
fpolys = [dz(e, 0.03) for e in FREE_E]
print("shell faces %d, edges %d, free edges (the piece's own) %d" % (len(sh.Faces), len(sh.Edges), len(fpolys)), flush=True)
# skin-build
RUNG = {}
try:
    PFJ = json.load(open(os.path.join(SK, "piece_faces.json"), encoding="utf-8"))
    if PFJ.get("piece_md5") == K.md5(shp): RUNG = {int(r["face"]): r for r in PFJ["faces"]}
    else: print("piece_faces.json is of another piece - every curved face gets its iso views", flush=True)
except (OSError, ValueError):
    print("no piece_faces.json - every curved face gets its iso views", flush=True)
frames = []; FINFO = {}
def QREC(fbox):
    fq = K.frame_quality(MQ, fbox)
    return {"defective": bool(fq.get("defective")), "why": fq.get("why", ""), "tris": MQ.get("tris"), "dev_p99_mm": MQ.get("dev_p99_mm"), "nang_p99_deg": MQ.get("nang_p99_deg"),
            "cracks": MQ.get("cracks"), "cracks_in_frame": fq.get("cracks_in_frame"), "seams": MQ.get("seams"), "open_edges": MQ.get("open_edges")}
def look(name, d, fbox, W, title, head, lines, light=None, VT=None, Cc=None, outline=None, info=None, free_hidden=False):
    path = os.path.join(OUT, name + ".png")
    if K.pic_hit(path, LKEY):
        frames.append(path); _i = dict(OLD_INFO.get(os.path.basename(path)) or (info or {"subject": "?"})); _i["quality"] = QREC(fbox); FINFO[os.path.basename(path)] = _i; return
    Vv, Tt = (V, T) if VT is None else VT
    pls = [(P, (235, 235, 235), 1, (), True) for P in (outline or [])] + [(P, (255, 200, 0), 3, (), True) for P in bad_e] + [(P, (255, 30, 30), 4, (), free_hidden) for P in fpolys]
    K.view_piece(R, path, Vv, Tt, FIDg, C if Cc is None else Cc, d, fbox, W, title, head, lines, polylines=pls, light=light, quality=MQ)
    frames.append(path); K.pic_mark(path, LKEY)
    info = dict(info or {"subject": "?"}); info["quality"] = QREC(fbox)
    FINFO[os.path.basename(path)] = info
LEG = ["Each face its own tint, its borders shaded dark; no other edges drawn. Yellow = the edges of a face that is not valid (not shaded). Red = an edge only one face holds, where it is in view.",
       "A white dashed line = the part of the subject face's border hidden behind the piece. Smooth shading from the surface's own normals; a crease between faces stays sharp.",
       "Judge the SHAPE: one simple surface per face, clean borders, no lump, ripple, crumple or fold; both sides alike on a symmetric edit."]
k = 0
# kit rebuild
# kit rebuild
MODE = (os.environ.get("LOOK_MODE", "quick") or "quick").strip().lower()
if MODE not in ("quick", "full"): K._fail("FAIL: LOOK_MODE is quick or full, not %r" % MODE)
# recorded  FACES_LOOKED.json
# LOOK_MODE=full
import re as _re_l1
FACES = sorted({int(x_) for x_ in _re_l1.split(r"[,\s;]+", os.environ.get("FACES", "").strip()) if x_})
_PIECE_MD5 = K.md5(shp)
_SCP = os.path.join(SK, "solid_c.json"); _FLP = os.path.join(OUT, "FACES_LOOKED.json")
def _flagged_faces():
    """the faces the build's check(True) named for THIS piece (skin\\solid_c.json, its piece_md5); [] when the record is another piece's or missing"""
    try: _sc = json.load(open(_SCP, encoding="utf-8"))
    except (OSError, ValueError): return []
    if str(_sc.get("piece_md5") or "") != _PIECE_MD5: return []
    return sorted({int(c_["face"]) for c_ in (_sc.get("check_faces") or []) if isinstance(c_, dict) and c_.get("face") is not None})
def _faces_looked():
    try: return sorted(int(x_) for x_ in (json.load(open(_FLP, encoding="utf-8")).get(_PIECE_MD5) or []))
    except (OSError, ValueError, TypeError): return []
if FACES: MODE = "faces"
if MODE == "full" and not os.environ.get("LOOK_FULL_OK", "").strip():
    _flag = _flagged_faces(); _miss = [f_ for f_ in _flag if f_ not in _faces_looked()]
    if _miss: K._fail("FAIL: LOOK_MODE=full REFUSED (31br L1, the client 2026-10-29: 'Why are you running a full review ... if you know it has issues?'): the build's check(True) names face(s) %s of this piece and NO targeted look has shown face(s) %s - first `kit rebuild skin-look --set FACES=%s` (their two iso views each, seconds), open the frames, judge: a real defect -> `judge --what look --verdict redo --face <n>` (no second review needed) and fix the lines / the points there; a tolerance-level flag or the body's own cap face -> say so in the note. LOOK_FULL_OK=\"<why>\" overrides, recorded." % (_flag, _miss, ",".join(str(x_) for x_ in _miss)))
QUICK = ("orbit_045", "orbit_135", "orbit_225", "orbit_315", "below_045", "below_135", "below_225", "below_315")
VIEWS_ = K.views(close=True, below=True, pics="full") if MODE == "full" else ([] if MODE == "faces" else [v for v in K.views(close=False, below=True, pics="full") if v[0] in QUICK])
if MODE == "faces": print("LOOK_MODE faces (31br L1 - THE TARGETED LOOK): the two iso views of face(s) %s only, no whole-piece frame; a redo / move may be judged on them, an ok may not (the quick look is the piece's look)" % FACES, flush=True)
else: print("LOOK_MODE %s: %d whole-piece / close-up view(s)%s" % (MODE, len(VIEWS_), "" if MODE == "full" else " - no per-face iso views (LOOK_MODE=full for the second reviewer)"), flush=True)
# crumpled
for nm, dv, fb, W, ttl in VIEWS_:
    k += 1
    look("%s_%s" % (PREFIX, nm), dv, fb, W, ttl, "SKIN LOOK  the remade skin as built (%d faces) - %s" % (len(sh.Faces), ttl), LEG, info={"subject": "whole" if not nm.startswith("close_") else nm})
    if nm.startswith("close_"):
        k += 1
        look("%s_%s_grazing" % (PREFIX, nm), dv, fb, W, ttl + " - GRAZING light", "SKIN LOOK  %s under a grazing light (lumps and ripples show)" % ttl, LEG, light="grazing", info={"subject": nm})
LOOK_MIN = float(os.environ.get("LOOK_MIN_MM2", "2.0"))
Cn_ = V[T].mean(axis=1); nfl = 0
# none of the
HIDDEN = []; LOOK_HIDDEN = float(os.environ.get("LOOK_HIDDEN", "0.05") or 0.05)
if MODE == "quick":      # 31br L1
    try:
        _qd = [np.asarray(dv, float) for nm, dv, fb, W, ttl in VIEWS_]
        _ar = np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1)
        for fi in okf:
            rg = RUNG.get(fi, {}).get("rung")
            if rg in ("cap", "orig", "flat"): continue
            f = sh.Faces[fi]
            if f.Area < LOOK_MIN: continue
            if not rg and isinstance(f.Surface, (Part.Plane, Part.Cylinder)): continue
            tm = FIDg == fi
            if not tm.any(): continue
            idx = np.nonzero(tm)[0]; idx = idx[_ar[idx] > 1e-12]
            if not len(idx): continue
            w_ = _ar[idx]; w_ = w_ / max(float(w_.sum()), 1e-12)
            pick = np.random.RandomState(7).choice(idx, size=min(48, len(idx)), replace=len(idx) < 48, p=w_)
            Ps_ = Cn_[pick]
            best = max(K.visible_fraction(V, T, tm, Ps_, dv) for dv in _qd)
            if best < LOOK_HIDDEN: HIDDEN.append(fi); print("   face %d (%s, %.1f mm2) is in view from NONE of the quick look's %d cameras (%.0f %% at best)" % (fi, rg or "?", f.Area, len(_qd), 100 * best), flush=True)
        if HIDDEN: print("HIDDEN FROM THE QUICK LOOK: face(s) %s - one frame each from the camera that sees them follows (31bq B39)" % HIDDEN, flush=True)
        else: print("the quick look's %d cameras see every changed face (over %.0f %% of its points in some frame)" % (len(_qd), 100 * LOOK_HIDDEN), flush=True)
    except Exception as _exh:
        print("   the quick look's visibility check failed (%s) - no hidden-face frames" % str(_exh)[:80], flush=True)
if FACES:
    _badf = [f_ for f_ in FACES if f_ < 0 or f_ >= len(sh.Faces)]
    if _badf: K._fail("FAIL: FACES names face(s) %s - the piece has faces 0..%d (the SKIN BUILD PASS line's check(True) list and piece_faces.json number them)" % (_badf, len(sh.Faces) - 1))
UNSEEN = []      # recorded
for fi in (FACES if FACES else (okf if MODE == "full" else HIDDEN)):
    f = sh.Faces[fi]; rg = RUNG.get(fi, {}).get("rung")
    if not FACES and rg in ("cap", "orig", "flat"): continue
    if not FACES and not rg and isinstance(f.Surface, (Part.Plane, Part.Cylinder)): continue
    if not FACES and f.Area < LOOK_MIN: continue
    tm = FIDg == fi
    if not tm.any():
        if FACES:      # 31bs K28 (2026-11-03  FACES_LOOKED.json
            # LOOK_MODE=full  recorded
            _whyU = ("it is NOT VALID (check(True) - the kernel's own verdict)" if not f.isValid() else ("its edge tolerance is over LOOK_TOL_MAX %g mm" % LOOK_TOL_MAX if fi in _big else "no triangle of the piece mesh is its"))
            print("   face %d (%s, %.1f mm2): %s - drawn by its edges only (yellow), NO iso frame of it: it is NOT recorded as looked at (31bs K28); the full look stays shut on it until a targeted look draws it (LOOK_TOL_MAX raised over its edge tolerance; `kit tool look_at` shows it but records no look), or LOOK_FULL_OK=\"<why>\" (recorded)" % (fi, rg or _kind(f), f.Area, _whyU), flush=True)
            UNSEEN.append(fi)
        continue
    Pf = V[np.unique(T[tm].ravel())]; Nr = np.cross(V[T[tm, 1]] - V[T[tm, 0]], V[T[tm, 2]] - V[T[tm, 0]]).sum(0)
    band_ = False
    if np.linalg.norm(Nr) < 1e-9:
        if not FACES: continue
        _Nt = np.cross(V[T[tm, 1]] - V[T[tm, 0]], V[T[tm, 2]] - V[T[tm, 0]]); _vn = np.linalg.svd(_Nt, full_matrices=False)[2]
        Nr = _vn[2] * max(float(np.linalg.norm(_Nt, axis=1).sum()), 1e-9); band_ = True
        print("   face %d (%s, %.1f mm2): its net normal is zero (a closed band) - its iso views are taken along its axis (%s) (31bt)" % (fi, rg or _kind(f), f.Area, " ".join("%.3f" % x_ for x_ in _vn[2])), flush=True)
    ct_ = Cn_[tm][np.argmin(np.linalg.norm(Cn_[tm] - Pf.mean(0), axis=1))]
    try:
        if sh.Solids and sh.isInside(FreeCAD.Vector(*(ct_ + 0.05 * Nr / np.linalg.norm(Nr))), 1e-4, True): Nr = -Nr
    except Exception: pass
    # LOOK_VIS
    # over the
    Pf_c = Cn_[tm]; rs_ = np.random.RandomState(7)
    Af_ = 0.5 * np.linalg.norm(np.cross(V[T[tm, 1]] - V[T[tm, 0]], V[T[tm, 2]] - V[T[tm, 0]]), axis=1); Af_ = Af_ / max(Af_.sum(), 1e-12)
    Ps_ = Pf_c[rs_.choice(len(Pf_c), size=min(48, int((Af_ > 0).sum())), replace=False, p=Af_)]
    def _vis(d_): return K.visible_fraction(V, T, tm, Ps_, d_)
    def _pool(n_, tilts):
        out_ = []
        for tilt_ in tilts:
            for j_, dv_ in enumerate(K.iso_dirs4(n_, vh[0], vh[1], tilt_)): out_.append((_vis(dv_), tilt_, j_, dv_))
        return out_
    def _pick(pool_, need=LOOK_VIS):
        got_ = []
        for p_ in sorted(pool_, key=lambda q_: (-min(q_[0], 0.9), -q_[1], -q_[0])):
            if p_[0] >= need and all(p_[2] != g_[2] for g_ in got_): got_.append(p_)
            if len(got_) == 2: break
        return got_
    _, _, vh = np.linalg.svd(Pf - Pf.mean(0), full_matrices=False)
    if band_ and abs(float(vh[0] @ Nr)) > 0.9 * float(np.linalg.norm(Nr)): vh = vh[[1, 0, 2]]
    lo = Pf.min(0); hi = Pf.max(0); m_ = max(2.0, 0.25 * float(np.max(hi - lo))); lo_ = lo - m_; hi_ = hi + m_
    Cc = np.where((FIDg == fi)[:, None], np.clip(fc[fi] * 1.15, 0, 1)[None, :], np.array([0.50, 0.52, 0.56])[None, :])
    fb = (lo_[0], hi_[0], lo_[1], hi_[1], lo_[2], hi_[2])
    border = [dz(e, 0.05) for e in f.Edges if e.Length > 1e-6]
    pool_ = _pool(Nr, (54.7,)); best_ = max(p_[0] for p_ in pool_)
    if best_ < LOOK_VIS:
        other_ = _pool(-Nr, (54.7,)); bo_ = max(p_[0] for p_ in other_)
        if bo_ > best_ + 0.25:
            print("face %d: the camera goes to the other side of the face - from there %.0f%% of it is in view against %.0f%%" % (fi, 100 * bo_, 100 * best_), flush=True)
            Nr = -Nr; pool_ = other_; best_ = bo_
    dirs_ = _pick(pool_)
    for tilt_ in (35.0, 20.0, 8.0):
        if len(dirs_) >= 2: break
        pool_ += _pool(Nr, (tilt_,)); dirs_ = _pick(pool_)
    if len(dirs_) < 2:      # LOOK_VIS
        for p_ in sorted(pool_, key=lambda q_: (-q_[0], -q_[1])):
            if all(p_[2] != g_[2] for g_ in dirs_): dirs_.append(p_)
            if len(dirs_) == 2: break
    dirs_ = sorted(dirs_[:2], key=lambda q_: q_[2])
    cov_ = None
    if max(p_[0] for p_ in pool_) < 0.05:
        bf_, bt_ = K.first_blocker(V, T, tm, Ps_, tuple(-Nr), FIDg); bf2_, bt2_ = K.first_blocker(V, T, tm, Ps_, tuple(Nr), FIDg)
        cov_ = min([x_ for x_ in ((bf_, bt_), (bf2_, bt2_)) if x_[0] is not None], key=lambda x_: x_[1], default=(None, None))
        if cov_[0] is not None:
            print("face %d (%s, %.1f mm2) is SEEN FROM NOWHERE: face %d lies %.2f mm in front of it - a slit of air or a pocket the piece encloses (requirement 2: gaps under the print tolerance and enclosed pockets are filled): decide the lines there (fill it, or drop the face)" % (fi, rg or _kind(f), f.Area, cov_[0], cov_[1]), flush=True)
    for j, (frac_, tilt_, cj_, dv) in enumerate(dirs_):
        note_ = ("" if tilt_ > 50 else " (tilt %.0f deg: no corner at a wider tilt sees the face)" % tilt_) + ("" if frac_ >= 0.9 else " (%.0f%% of the face in view)" % (100 * frac_))
        if band_: note_ = " (a closed band - viewed along its axis)" + note_
        if cov_ and cov_[0] is not None: note_ = " (SEEN FROM NOWHERE - %.0f%% of the face in view: face %d lies %.2f mm in front of it - a slit or an enclosed pocket)" % (100 * frac_, cov_[0], cov_[1])
        look("%s_face%03d_iso%d" % (PREFIX, fi, j + 1), dv, fb, 900, "face %d iso %d" % (fi, j + 1),
             "SKIN LOOK  FACE %d (%s, %.1f mm2) - iso view %d of 2, side light%s" % (fi, rg or _kind(f), f.Area, j + 1, note_),
             ["Face %d in its own tint, its neighbours grey - the whole piece, framed on the face. Look for a lump, ripple, crumple or fold on IT, and a wavy border." % fi,
              "Iso, never straight on (the client 2026-10-07): a lump hides when seen square to the face."], light="grazing", Cc=Cc, outline=border,
             info={"subject": "face", "face": fi, "rung": rg or _kind(f), "area_mm2": round(float(f.Area), 2), "tilt_deg": round(float(tilt_), 1), "in_view": round(float(frac_), 2),
                   "covered_by": (None if not cov_ or cov_[0] is None else {"face": int(cov_[0]), "mm": round(float(cov_[1]), 2)}), "band": bool(band_)})
    nfl += 1
print("faces given two iso views each: %d (fitted, %.1f mm2 or more)" % (nfl, LOOK_MIN), flush=True)
if fpolys:
    mids = np.array([P[len(P) // 2] for P in fpolys]); used = np.zeros(len(mids), bool); kk = 0
    for i in range(len(mids)):
        if used[i]: continue
        grp = np.linalg.norm(mids - mids[i], axis=1) < 6.0; used |= grp
        pts = np.vstack([fpolys[j] for j in np.nonzero(grp)[0]]); lo = pts.min(0) - 2.5; hi = pts.max(0) + 2.5
        fb = (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]); c = pts.mean(0)
        sel = np.linalg.norm(V[T].mean(axis=1) - c, axis=1) < 4
        nr = np.cross(V[T[sel, 1]] - V[T[sel, 0]], V[T[sel, 2]] - V[T[sel, 0]]).sum(0) if sel.any() else np.array([0, 0, 1.0])
        nr = nr / max(np.linalg.norm(nr), 1e-9)
        _, _, vh_ = np.linalg.svd(pts - pts.mean(0), full_matrices=False); none_ = np.zeros(len(T), bool)
        rs_ = np.random.RandomState(5); Pe_ = pts[rs_.choice(len(pts), size=min(60, len(pts)), replace=False)]
        pool_ = [(K.visible_fraction(V, T, none_, Pe_, dv_), s_, j_, dv_) for s_ in (1.0, -1.0) for j_, dv_ in enumerate(K.iso_dirs4(s_ * nr, vh_[0], vh_[1], 54.7))]
        pool_.sort(key=lambda q_: -q_[0]); got_ = []
        for p_ in pool_:
            if all((p_[1], p_[2]) != (g_[1], g_[2]) for g_ in got_): got_.append(p_)
            if len(got_) == 2: break
        for vn, (frac_, s_, j_, dv) in zip(("a", "b"), got_):
            note_ = (" - SEEN FROM NOWHERE (%.0f%% of the edges in view: another face covers them - a slit or a pocket)" % (100 * frac_)) if frac_ < 0.05 else ("" if frac_ >= 0.9 else " (%.0f%% of the edges in view)" % (100 * frac_))
            look("%s_free%02d%s" % (PREFIX, kk, vn), dv, fb, 1000, "free-edge cluster %d (%s)" % (kk, vn), "SKIN LOOK  free-edge cluster %d - %d free edge(s) - view %s%s" % (kk, int(grp.sum()), vn, note_),
                 ["Close-up where the shell is open: red = the free edge(s), full where in view, faint dotted where the piece hides them; faces tinted."], info={"subject": "free", "in_view": round(float(frac_), 2)}, free_hidden=True)
        kk += 1
    print("free-edge clusters: %d" % kk, flush=True)
# ORIGINAL
# over the
# NOT TAKEN  kit rebuild
import time as _vtime, traceback as _vtb
VAN = {"taken": False}
class _VanNotTaken(Exception): pass      # NOT TAKEN
def _vjson(p_):
    try: return json.load(open(p_, encoding="utf-8"))
    except (OSError, ValueError): return None
def _vframe(path, fbox, info, q_):
    fq_ = K.frame_quality(q_, fbox)
    info = dict(info); info["quality"] = {"defective": bool(fq_.get("defective")), "why": fq_.get("why", ""), "tris": q_.get("tris"), "cracks": q_.get("cracks"), "cracks_in_frame": fq_.get("cracks_in_frame"), "seams": q_.get("seams"), "open_edges": q_.get("open_edges")}
    frames.append(path); FINFO[os.path.basename(path)] = info
def _vblends(fil, Vs, Fs, pp, say):
    """the DECIDED blends of THIS wireframe (fillets.json, bound to network_frame.brep by md5 - checked by the caller): each line's two layout faces (network.json's
    chain pair), its crease as drawn (network_frame.brep - the edge of the chain), its strip t (K.crease_t). [] and the reason when they cannot be read."""
    ents = [e_ for e_ in (fil.get("fillets") or []) if isinstance(e_, dict) and e_.get("line") is not None]
    if not ents: return [], ""
    try:
        NJ = _vjson(os.path.join(SK, "network.json")) or {}; CH = [c_ for c_ in (NJ.get("chains") or []) if c_.get("ok")]
        nsh = Part.Shape(); nsh.importBrep(os.path.join(SK, "network_frame.brep")); NE = nsh.Edges
        if len(NE) != len(CH): return [], "network_frame.brep holds %d edges for network.json's %d chains - the decided blends' creases are not read" % (len(NE), len(CH))
        out = []; skip_ = []
        for e_ in ents:
            L_ = int(e_["line"])
            if L_ < 0 or L_ >= len(CH) or int(CH[L_].get("chain", L_)) != L_ or len(CH[L_].get("pair") or []) != 2:
                skip_.append(L_); continue
            cr_ = np.array([[q_.x, q_.y, q_.z] for q_ in NE[L_].discretize(Number=max(3, int(NE[L_].Length / 0.2) + 1))], float)
            t_, b_ = K.crease_t(float(e_.get("r") or 0.0), Vs, Fs, pp, CH[L_]["pair"], cr_)
            out.append({"line": L_, "r": float(e_.get("r") or 0.0), "pair": tuple(int(x_) for x_ in CH[L_]["pair"]), "crease": cr_, "t": t_, "beta": b_})
        return out, ("decided line(s) %s not read - their chain is not at its own index in network.json (or has no two layout faces): no blend accounts for an original face there" % skip_) if skip_ else ""
    except Exception as ex_:
        return [], "the decided blends' creases could not be read (%s: %s) - no blend accounts for any original face in this look" % (type(ex_).__name__, str(ex_)[:120])
def _vanished():
    t0 = _vtime.time()
    if not K.brep_source(os.path.join(RUN, "source.stl")):
        return {"taken": False, "applies": False, "why": "the skin steps did not run on the job's own source mesh (source.stl, REBUILD_source.json) - a voxel source carries no original face per triangle: the measure does not apply"}
    try:
        Z_ = np.load(os.path.join(SK, "regions.npz")); Vs = np.asarray(Z_["Vu"], float); Fs = np.asarray(Z_["F"], int).reshape(-1, 3)
        fid = np.asarray(Z_["fid"], np.int64) if "fid" in Z_.files else None
    except (OSError, ValueError, KeyError) as ex_: raise _VanNotTaken("skin\\regions.npz is not readable (%s)" % str(ex_)[:80])
    if fid is None or len(fid) != len(Fs): raise _VanNotTaken("skin\\regions.npz carries no original face per triangle")
    if not RUNG: raise _VanNotTaken("piece_faces.json is not of this piece - the faces' rungs and layout faces are needed to say what the record says")
    try:
        pp = np.asarray(np.load(os.path.join(SK, "patches.npz"))["patch"], np.int64)
    except (OSError, ValueError, KeyError): pp = None
    if pp is None or len(pp) != len(fid): raise _VanNotTaken("skin\\patches.npz does not carry the layout face of every source triangle")
    ST, SMP = K.faces_against_piece(Vs, Fs, fid, V, T)
    if SMP is None: raise _VanNotTaken("the source mesh holds no original face")
    S, SF, SW, d, tri, side, src = SMP; off = d > K.VANISH_MM
    pfs = FIDg[np.maximum(tri, 0)]; isfil = np.array([RUNG.get(i_, {}).get("rung") == "fillet" for i_ in range(len(sh.Faces))], bool); S_fil = isfil[pfs]
    S_patch = pp[src]; At = 0.5 * np.linalg.norm(np.cross(Vs[Fs[:, 1]] - Vs[Fs[:, 0]], Vs[Fs[:, 2]] - Vs[Fs[:, 0]]), axis=1)
    PREC = {int(r_["patch"]): r_ for r_ in ((_vjson(os.path.join(SK, "patches.json")) or {}).get("patches") or []) if "patch" in r_}
    PFOF = {}
    for i_, r_ in RUNG.items(): PFOF.setdefault(int(r_.get("patch", -1)), []).append((int(i_), r_.get("rung")))
    PT = _vjson(os.path.join(SK, "points1000.json")) or {}; NOP = set(int(x_) for x_ in (PT.get("no_points") or []))
    patch_of = {}
    for f_ in ST:
        ti_ = np.nonzero(fid == f_)[0]
        if len(ti_): pv_, iv_ = np.unique(pp[ti_], return_inverse=True); patch_of[f_] = int(pv_[np.argmax(np.bincount(iv_, weights=At[ti_]))])
    MEM = {p_: set(int(x_) for x_ in np.unique(fid[(pp == p_) & (fid >= 0)])) for p_ in set(patch_of.values())}
    DROPS = K.drop_boxes(PT)
    fil = _vjson(os.path.join(SK, "fillets.json")) or {}; fil_note = ""; nfp = os.path.join(SK, "network_frame.brep")
    if fil and (not os.path.isfile(nfp) or fil.get("network_frame_md5") not in (None, K.md5(nfp) if os.path.isfile(nfp) else None)):
        fil = {}; fil_note = "skin\\fillets.json is of another wireframe - its \"buried\" lists and blends not read"
    buried_of = {}
    for e_ in (fil.get("fillets") or []):
        for x_ in (e_.get("buried") or []):
            try: buried_of.setdefault(int(x_), []).append(int(e_.get("line", -1)))
            except (TypeError, ValueError): pass
    BL, bl_note = _vblends(fil, Vs, Fs, pp, print)
    tie = K.blend_tie(S, S_patch, S_fil, BL) if BL else np.full(len(S), -1, np.int64); BT = {b_["line"]: b_["t"] for b_ in BL}
    FM = _vjson(os.path.join(SK, "features.json")) or {}; FWHY = dict(FM.get("_why") or {}) if isinstance(FM.get("_why"), dict) else {}
    FEAT = {k_: [int(x_) for x_ in v_] for k_, v_ in FM.items() if not str(k_).startswith("_") and isinstance(v_, list)}
    FOF = {x_: k_ for k_, v_ in FEAT.items() for x_ in v_}
    def _feat(f_):
        r_ = PREC.get(patch_of.get(f_, -1)) or {}
        for c_ in (f_, r_.get("face_src"), r_.get("face_src_master")):
            if c_ is not None and int(c_) in FOF: return FOF[int(c_)]
        return None
    merged = {}; respanned = {}; in_piece = {}; feat_of = {}
    for f_ in ST:
        p_ = patch_of.get(f_); pf_ = PFOF.get(p_, []) if p_ is not None else []
        in_piece[f_] = bool(pf_); respanned[f_] = any(rg_ not in ("orig", "cap", "fillet") for _, rg_ in pf_)
        merged[f_] = len((MEM.get(p_) or set()) - NOP) > 1; feat_of[f_] = _feat(f_)
    lab, areas = K.off_regions(S, SW, off)
    parts = []
    for r_ in [int(x_) for x_ in np.nonzero(areas >= K.VANISH_MM2)[0]]:
        mr_ = lab == r_
        for f_ in sorted(set(SF[mr_].tolist())):
            m_ = mr_ & (SF == f_); w_ = SW[m_]; wt_ = float(w_.sum())
            drop_ = None
            if f_ in NOP:
                for bi_, (b_, why_) in enumerate(DROPS):
                    Pm_ = S[m_]; ib_ = (Pm_[:, 0] >= min(b_[0], b_[1])) & (Pm_[:, 0] <= max(b_[0], b_[1])) & (Pm_[:, 1] >= min(b_[2], b_[3])) & (Pm_[:, 1] <= max(b_[2], b_[3])) & (Pm_[:, 2] >= min(b_[4], b_[5])) & (Pm_[:, 2] <= max(b_[4], b_[5]))
                    if w_[ib_].sum() >= 0.5 * wt_: drop_ = (bi_ + 1, why_); break
            tl_ = tie[m_]; lines_ = sorted(set(int(x_) for x_ in tl_[tl_ >= 0]))
            parts.append({"face": int(f_), "region": r_, "off_mm2": round(wt_, 3), "removed_mm2": round(float(w_[side[m_] > 0].sum()), 3), "filled_mm2": round(float(w_[side[m_] < 0].sum()), 3),
                          "max_mm": (round(float(d[m_].max()), 3) if float(d[m_].max()) <= K.VANISH_CAP else None), "drop": drop_,
                          "blend": (float(w_[tl_ >= 0].sum() / max(wt_, 1e-12)), lines_, {l_: BT.get(l_) for l_ in lines_})})
    K.classify_parts(parts, {"no_points": NOP, "buried_of": buried_of, "merged": merged, "respanned": respanned, "in_piece": in_piece, "feat_of": feat_of, "feat_why": FWHY})
    RV = K.name_regions(parts, areas)
    left_f = set(p_["face"] for p_ in parts); offf_ = set(int(x_) for x_ in np.unique(SF[off]))
    partly = sorted(((f_, ST[f_]["off_mm2"]) for f_ in offf_ - left_f), key=lambda x_: -x_[1])
    FEAT_NONE = []
    for k_, v_ in FEAT.items():
        ps_ = set(patch_of[x_] for x_ in v_ if x_ in patch_of)
        if ps_ and not any(PFOF.get(p_) for p_ in ps_): FEAT_NONE.append((k_, v_))
    GR = []
    for r_, rv_ in RV.items():
        if not rv_["named"]: continue
        pr_ = [p_ for p_ in parts if p_["region"] == r_]; nmp_ = [p_ for p_ in pr_ if p_["cls"] not in K.VANISH_BY_RECORD]
        bey_ = [p_ for p_ in pr_ if p_["cls"] == "blend" and float(p_["blend"][0]) < 1.0 - 1e-9]
        nmp_ = nmp_ + [{"face": p_["face"], "region": r_, "off_mm2": round(float(p_["off_mm2"]) * (1.0 - float(p_["blend"][0])), 3), "cls": "beyond_blend", "max_mm": p_.get("max_mm"),
                        "why": "beside the decided blend of line(s) %s, its part BEYOND that blend's strip - no record accounts for it" % sorted(p_["blend"][1])} for p_ in bey_]
        dm_ = max(nmp_, key=lambda p_: p_["off_mm2"])["face"]
        GR.append({"label": "region %d (%s)" % (r_, ("feature %s" % feat_of[dm_]) if feat_of.get(dm_) else ("layout face %s" % patch_of.get(dm_))), "region": r_, "parts": pr_, "named_parts": nmp_, "off_mm2": rv_["off_mm2"], "named_mm2": rv_["named_mm2"],
                   "mask": (lab == r_) & (np.isin(SF, [p_["face"] for p_ in nmp_ if p_["cls"] != "beyond_blend"]) | (np.isin(SF, [p_["face"] for p_ in bey_]) & (tie < 0)))})
    for k_, v_ in FEAT_NONE:
        m_ = off & np.isin(SF, v_)
        GR.append({"label": "feature %s (no face of the piece comes from it)" % k_, "region": None, "parts": [], "named_parts": [{"face": x_, "off_mm2": ST.get(x_, {}).get("off_mm2", 0.0), "cls": "lost", "why": "NOT ACCOUNTED FOR - FEATURE %s has NO FACE in the piece" % k_} for x_ in v_ if x_ in ST],
                   "off_mm2": round(float(SW[m_].sum()), 3), "named_mm2": round(float(SW[m_].sum()), 3), "mask": m_, "feature_none": k_})
    GR.sort(key=lambda g_: -g_["named_mm2"])
    byrec = sorted([(r_, rv_) for r_, rv_ in RV.items() if not rv_["named"]], key=lambda kv_: -kv_[1]["off_mm2"])
    _fmt = lambda p_: "%d (%.1f mm2 off - %s%s, %s)" % (p_["face"], p_["off_mm2"], "removed" if p_.get("removed_mm2", 0) >= p_.get("filled_mm2", 0) else "filled",
                                                     (", up to %.2f mm" % p_["max_mm"]) if p_.get("max_mm") is not None else (", over %.1f mm" % K.VANISH_CAP), p_["cls"])
    _whys = lambda ps_: "; ".join("%s: %s" % (", ".join(str(q_["face"]) for q_ in ps_ if q_["why"] == w_), w_) for w_ in sorted(set(q_["why"] for q_ in ps_), key=lambda x_: [q_["why"] for q_ in ps_].index(x_)))
    _inv = "" if len(okf) == len(sh.Faces) else " (%d invalid face(s) of the piece are not in its mesh - the original faces at them read off)" % (len(sh.Faces) - len(okf))
    nleft_ = len(left_f)
    print("ORIGINAL FACES AGAINST THE PIECE (31bq B18): %d original faces of the content measured (the caps left out) - %d on the piece, %d partly off (only in regions under %.0f mm2), %d LEFT IT in %d region(s) of %.0f mm2 or more over %.1f mm from the piece: %d region(s) NAMED (%.1f mm2 no record accounts for), %d by a record only (a drop box with its reason, a burial, a decided blend)%s%s%s"
          % (len(ST), len(ST) - len(offf_), len(partly), K.VANISH_MM2, nleft_, len(RV), K.VANISH_MM2, K.VANISH_MM, sum(1 for g_ in GR if g_["region"] is not None), sum(g_["named_mm2"] for g_ in GR if g_["region"] is not None), len(byrec),
             (" - " + fil_note) if fil_note else "", (" - " + bl_note) if bl_note else ("" if not BL else " - %d decided blend(s) read (their strips)" % len(BL)), _inv), flush=True)
    _vk = globals().get("VKEY") or LKEY
    SQ = K.source_quality(Vs, Fs); q2 = K.merge_quality([MQ, SQ]) or MQ
    Cp = np.tile(np.array([0.56, 0.58, 0.62]), (len(T), 1)); nfr_ = 0; GREC = []
    for gi_, g_ in enumerate(GR):
        fs_ = sorted(set(p_["face"] for p_ in g_["named_parts"])); m_ = g_["mask"]; fr_ = []
        rem_ = float(SW[m_ & (side > 0)].sum()); fil_ = float(SW[m_ & (side < 0)].sum()); ghost_ = fil_ > rem_
        cen_ = S[m_].mean(0) if m_.any() else None
        rec_why_ = _whys(g_["named_parts"]) if g_["named_parts"] else ""; byr_ = [p_ for p_ in g_["parts"] if p_["cls"] in K.VANISH_BY_RECORD]
        if nfr_ < K.VANISH_FRAMES and m_.any():
            nfr_ += 1; base_ = "%s_vanished_%02d" % (PREFIX, gi_ + 1); Pm_ = S[m_]
            lo_ = Pm_.min(0); hi_ = Pm_.max(0); ext_ = float(np.max(hi_ - lo_))
            cnt_ = [int((np.abs(Pm_[:, a_] - cen_[a_]) <= 0.3).sum()) for a_ in (0, 1, 2)]; ax_ = int(np.argmax(cnt_)); au_, av_ = [a_ for a_ in (0, 1, 2) if a_ != ax_]
            mg_ = max(3.0, 0.5 * ext_); win_ = ((float(lo_[au_] - mg_), float(hi_[au_] + mg_)), (float(lo_[av_] - mg_), float(hi_[av_] + mg_)))
            spath_ = os.path.join(OUT, base_ + "_section.png"); fbs_ = [0.0] * 6; fbs_[2 * au_], fbs_[2 * au_ + 1] = win_[0]; fbs_[2 * av_], fbs_[2 * av_ + 1] = win_[1]; fbs_[2 * ax_], fbs_[2 * ax_ + 1] = cen_[ax_] - 1.0, cen_[ax_] + 1.0
            sc_ = None
            if not K.pic_hit(spath_, _vk):
                sc_ = K.section_frame(R, spath_, (Vs, Fs), (V, T), ax_, float(cen_[ax_]), win_, K.VANISH_MM,
                                      "SKIN LOOK  NOT IN THE PIECE - %s: the SECTION %s = %.2f through it, as the station frames draw it - original face(s) %s, %.1f mm2 more than %.1f mm off the piece (%.1f removed, %.1f filled)" % (g_["label"], "xyz"[ax_], cen_[ax_], ", ".join(str(x_) for x_ in fs_[:12]) + (" ..." if len(fs_) > 12 else ""), g_["named_mm2"], K.VANISH_MM, rem_, fil_),
                                      ["GREEN = the original and the piece together (within %.1f mm, VANISH_MM - the rule's own band); YELLOW = the ORIGINAL only (old - its shape is not in the piece); BLUE = the PIECE only (new). A yellow line INSIDE the blue outline is a FILLED loss (material added over it), one standing OUTSIDE it a removed one." % K.VANISH_MM,
                                       "The record: %s." % (rec_why_[:700] or "-"), ("By a record beside it: %s." % _whys(byr_)[:300]) if byr_ else "",
                                       "Judge it: the design (say so in the look's note) or a feature lost - a lost one goes back to its points (PTS_BOX), its feature (FEATURES) or its lines, and is built again."], quality=q2)
                K.pic_mark(spath_, _vk)
            _vframe(spath_, tuple(fbs_), {"subject": "vanished", "view": "section", "group": g_["label"], "faces": fs_, "axis": "xyz"[ax_], "at": round(float(cen_[ax_]), 3), "segments": sc_}, q2); fr_.append(os.path.basename(spath_))
            # over the
            tg_ = np.unique(src[m_]); u_, inv_ = np.unique(Fs[tg_].ravel(), return_inverse=True); Vo_ = Vs[u_]; To_ = inv_.reshape(-1, 3); Po_ = Vo_[To_]
            no_ = np.cross(Po_[:, 1] - Po_[:, 0], Po_[:, 2] - Po_[:, 0]).sum(0)
            if np.linalg.norm(no_) < 1e-9: no_ = np.array([0.0, 0.0, 1.0])
            Pa_ = Po_.reshape(-1, 3); _, _, vh_ = np.linalg.svd(Pa_ - Pa_.mean(0), full_matrices=False)
            m2_ = max(2.0, 0.35 * ext_); fb_ = (lo_[0] - m2_, hi_[0] + m2_, lo_[1] - m2_, hi_[1] + m2_, lo_[2] - m2_, hi_[2] + m2_)
            Vc_ = np.vstack([V, Vo_]); Tc_ = np.vstack([T, To_ + len(V)]); own_ = np.r_[np.zeros(len(T), bool), np.ones(len(To_), bool)]
            Ps_ = Po_.mean(1)[np.random.RandomState(5).choice(len(To_), size=min(40, len(To_)), replace=False)]
            pool_ = [(K.visible_fraction(Vc_, Tc_, own_, Ps_, dv_), j_, dv_) for s_ in (1.0, -1.0) for j_, dv_ in enumerate(K.iso_dirs4(s_ * no_, vh_[0], vh_[1], 54.7))]
            pool_.sort(key=lambda q_: -q_[0]); vis_, _, dv_ = pool_[0]
            bias_ = float(np.linalg.norm(np.array(fb_[1::2]) - np.array(fb_[0::2]))) + 10.0 if ghost_ else 0.0
            ing_ = np.isin(fid, fs_); E_ = np.vstack([Fs[:, [0, 1]], Fs[:, [1, 2]], Fs[:, [2, 0]]]); Eg_ = np.tile(ing_, 3); Es_ = np.sort(E_, axis=1)
            o_ = np.lexsort((Es_[:, 1], Es_[:, 0])); Es_ = Es_[o_]; Eg_ = Eg_[o_]; same_ = np.all(Es_[1:] == Es_[:-1], axis=1)
            bd_ = np.zeros(len(Es_), bool); bd_[:-1] |= same_ & (Eg_[:-1] != Eg_[1:]); bd_[1:] |= same_ & (Eg_[:-1] != Eg_[1:]); bd_ &= Eg_
            sg_ = Es_[bd_]; sg_ = sg_[np.unique(sg_, axis=0, return_index=True)[1]] if len(sg_) else sg_
            inb_ = lambda X_: np.all((X_ >= np.array(fb_[0::2])) & (X_ <= np.array(fb_[1::2])), axis=1)
            sg_ = sg_[inb_(Vs[sg_[:, 0]]) | inb_(Vs[sg_[:, 1]])] if len(sg_) else sg_
            pls_ = [(np.array([Vs[a_], Vs[b_]]), (255, 60, 255), 2, (), True) for a_, b_ in sg_[:4000]]
            vpath_ = os.path.join(OUT, base_ + ".png")
            if not K.pic_hit(vpath_, _vk):
                K.view_meshes(R, vpath_, [(V, T, FIDg, MQ, Cp), (Vo_, To_, np.zeros(len(To_), int), SQ, np.array([0.96, 0.84, 0.12]), bias_)], dv_, fb_, 1000,
                              "original faces not in the piece - %s" % g_["label"],
                              "SKIN LOOK  NOT IN THE PIECE - %s: original face(s) %s - %.1f mm2 more than %.1f mm off the piece (%.1f removed, %.1f filled)%s" % (g_["label"], ", ".join(str(x_) for x_ in fs_[:12]) + (" ..." if len(fs_) > 12 else ""), g_["named_mm2"], K.VANISH_MM, rem_, fil_,
                                  " - GHOSTED: the original lies INSIDE the piece here (material added) and is drawn OVER it" if ghost_ else ""),
                              ["YELLOW = the ORIGINAL's surface of these faces where it lies more than %.1f mm from the built piece - OLD ONLY, as the station frames draw it: the shape that is NOT in the piece. %s MAGENTA = their borders on the original (faint dotted where hidden). The piece is grey." % (K.VANISH_MM,
                                   "GHOSTED: it lies inside the piece's material, drawn in front of the piece wherever it projects - the SECTION frame (%s) shows how deep." % os.path.basename(spath_) if ghost_ else "Depth-tested: it stands proud of the piece where you see it."),
                               "The record: %s." % (rec_why_[:700] or "-"),
                               "Judge it: the design (say so in the look's note) or a feature lost - a lost one goes back to its points (PTS_BOX), its feature (FEATURES) or its lines, and is built again."], polylines=pls_)
                K.pic_mark(vpath_, _vk)
            _vframe(vpath_, fb_, {"subject": "vanished", "view": "piece", "group": g_["label"], "faces": fs_, "ghosted": bool(ghost_), "in_view": round(float(vis_), 2)}, q2); fr_.append(os.path.basename(vpath_))
        g_["frames"] = fr_
        lay_ = sorted(set(patch_of[x_] for x_ in fs_ if x_ in patch_of))
        print("   NAMED %d (%s) - %s%s: %.1f mm2 off (%.1f no record accounts for; %.1f removed, %.1f filled): %s; the record: %s%s; its layout face(s) %s built as piece face(s) %s" % (
            gi_ + 1, ("frames " + " / ".join(fr_)) if fr_ else ("no frame: over VANISH_FRAMES %d" % K.VANISH_FRAMES if m_.any() else "no frame: none of its surface is off the piece (another face covers it)"),
            g_["label"], (" at [%.1f %.1f %.1f]" % tuple(cen_)) if cen_ is not None else "", g_["off_mm2"], g_["named_mm2"], rem_, fil_, ", ".join(_fmt(p_) for p_ in g_["named_parts"][:10]) + (" ..." if len(g_["named_parts"]) > 10 else ""),
            rec_why_[:600], ("; beside it by a record: " + ", ".join(_fmt(p_) for p_ in byr_[:6])) if byr_ else "", lay_,
            ", ".join("%d (%s)" % (i_, rg_) for p_ in lay_ for i_, rg_ in sorted(PFOF.get(p_, []))[:12]) or "none"), flush=True)
        GREC.append({"group": g_["label"], "region": g_["region"], "centre": [round(float(x_), 2) for x_ in cen_] if cen_ is not None else None, "off_mm2": g_["off_mm2"], "named_mm2": g_["named_mm2"],
                     "removed_mm2": round(rem_, 2), "filled_mm2": round(fil_, 2), "faces": fs_, "why": rec_why_[:1000], "frames": fr_, "layout_faces": lay_,
                     "parts": [{k_: p_.get(k_) for k_ in ("face", "off_mm2", "cls", "why")} for p_ in g_["named_parts"]]})
    for r_, rv_ in byrec:
        pr_ = [p_ for p_ in parts if p_["region"] == r_]; c_ = S[lab == r_].mean(0)
        nm_ = [p_ for p_ in pr_ if p_["cls"] not in K.VANISH_BY_RECORD]
        print("   by a record - region %d at [%.1f %.1f %.1f], %.1f mm2 off: %s - %s%s" % (r_, c_[0], c_[1], c_[2], rv_["off_mm2"], ", ".join(_fmt(p_) for p_ in pr_[:10]) + (" ..." if len(pr_) > 10 else ""),
              _whys([p_ for p_ in pr_ if p_["cls"] in K.VANISH_BY_RECORD])[:500], (" (beside it, %.1f mm2 no record accounts for - under VANISH_MM2: %s)" % (rv_["named_mm2"], _whys(nm_)[:300])) if nm_ else ""), flush=True)
    if partly: print("   partly off, in no region of %.0f mm2 (said, not framed): %s" % (K.VANISH_MM2, ", ".join("%d %.2f" % (f_, a_) for f_, a_ in partly[:16]) + (" ..." if len(partly) > 16 else "")), flush=True)
    if not FEAT_NONE and FEAT: print("   the feature map: every one of its %d features has a face in the piece" % len(FEAT), flush=True)
    nn_ = len(GR)
    if nn_: print("-> %d NAMED (%d region(s), %d feature(s) with no face): the original's shape there is not in the piece and no drop box with its reason, burial or decided blend removes it - open each frame (SKIN_look_vanished_*): the look's verdict says whether each is the design or a feature lost (%.1f s)" % (nn_, sum(1 for g_ in GR if g_["region"] is not None), len(FEAT_NONE), _vtime.time() - t0), flush=True)
    else: print("-> nothing named: every region that left the piece is removed by a record (%.1f s)" % (_vtime.time() - t0), flush=True)
    VAN_ = {"taken": True, "vanish_mm": K.VANISH_MM, "vanish_mm2": K.VANISH_MM2, "link_mm": K.VANISH_LINK, "measured": len(ST), "on_piece": len(ST) - len(offf_), "partly_off": len(partly), "left": nleft_,
            "regions_left": len(RV), "named": GREC, "by_record": [{"region": r_, "off_mm2": rv_["off_mm2"], "named_mm2": rv_["named_mm2"], "parts": [{k_: p_.get(k_) for k_ in ("face", "off_mm2", "cls", "why")} for p_ in parts if p_["region"] == r_]} for r_, rv_ in byrec],
            "partly_off_faces": [[f_, a_] for f_, a_ in partly], "features_with_no_face": [k_ for k_, _ in FEAT_NONE], "blends_read": len(BL), "notes": [x_ for x_ in (fil_note, bl_note) if x_], "seconds": round(_vtime.time() - t0, 1)}
    try:
        with open(os.path.join(OUT, "ORIGINAL_FACES.json"), "w", encoding="utf-8") as fh_:
            json.dump({"piece_md5": K.md5(shp), "summary": VAN_, "parts": [dict({k_: v_ for k_, v_ in p_.items() if k_ != "blend"}, blend_share=round(float(p_["blend"][0]), 3), blend_lines=list(p_["blend"][1])) for p_ in parts],
                       "faces": {str(f_): dict(s_, patch=patch_of.get(f_), feature=feat_of.get(f_), no_point=f_ in NOP) for f_, s_ in ST.items()}}, fh_, indent=0, default=str)
    except OSError as ex_: print("   ORIGINAL_FACES.json not written: %s" % ex_, flush=True)
    return VAN_
try:
    VAN = _vanished()
    if VAN.get("applies") is False: print("ORIGINAL FACES AGAINST THE PIECE (31bq B18): not measured - %s" % VAN["why"], flush=True)
except _VanNotTaken as _exv:
    VAN = {"taken": False, "why": str(_exv)[:300]}
    print("ORIGINAL FACES AGAINST THE PIECE (31bq B18): NOT TAKEN - %s - no face of the original is named or cleared by this look, and its ok is refused until the measure runs" % VAN["why"], flush=True)
except Exception as _exv:      # recorded
    _tbl = (_vtb.extract_tb(_exv.__traceback__) or [None])[-1]
    VAN = {"taken": False, "fault": True, "why": "a KIT FAULT - %s: %s (%s line %s)" % (type(_exv).__name__, str(_exv)[:200], os.path.basename(_tbl.filename) if _tbl else "?", _tbl.lineno if _tbl else "?")}
    print("ORIGINAL FACES AGAINST THE PIECE (31bq B18): NOT TAKEN - %s - a kit defect: no face of the original is named or cleared by this look, and its ok is refused until the measure runs" % VAN["why"], flush=True)
print(K.pic_report("SKIN_look"), flush=True)
if FACES:
    try: _fl_all = json.load(open(_FLP, encoding="utf-8"))
    except (OSError, ValueError): _fl_all = {}
    if not isinstance(_fl_all, dict): _fl_all = {}
    _seenF = sorted(set(FACES) - set(UNSEEN))
    _fl_all[_PIECE_MD5] = sorted(set(int(x_) for x_ in (_fl_all.get(_PIECE_MD5) or [])) | set(_seenF)); _fl_all["_when"] = _vtime.strftime("%Y-%m-%d %H:%M:%S")
    with open(_FLP, "w", encoding="utf-8") as _fh: json.dump(_fl_all, _fh, indent=1)
    _stillF = [f_ for f_ in _flagged_faces() if f_ not in _fl_all[_PIECE_MD5]]
    print("FACES LOOKED AT on this piece (%s): %s%s%s" % (_PIECE_MD5[:8], _fl_all[_PIECE_MD5], (" - UNSEEN (no iso frame, not recorded - 31bs K28): %s" % UNSEEN) if UNSEEN else "",
                                                      (" - the build's check(True) faces still without a look: %s" % _stillF) if _stillF else " - every face the build's check(True) named has its look: LOOK_MODE=full is open"), flush=True)
lk = K.write_look("skin", frames, shp, {"faces": len(sh.Faces), "free_edges_drawn": len(fpolys), "invalid_faces": len(sh.Faces) - len(okf), "frame_info": FINFO, "mode": MODE, "faces_looked": (sorted(set(FACES) - set(UNSEEN)) if FACES else FACES), "faces_unseen": (list(UNSEEN) if FACES else []), "look_full_ok": (os.environ.get("LOOK_FULL_OK") or "").strip() or None, "original_faces": VAN,
                                           "mesh_quality": dict({k_: MQ.get(k_) for k_ in ("tris", "dev_mm", "ang_rad", "open_edges", "expected_open", "seams", "cracks", "gap_max_mm", "dev_p99_mm", "nang_p99_deg", "edge_tol_max", "facet_p99_deg", "facet_max_deg", "defective_mesh", "why_mesh", "how")},
                                                                defective=bool(MQ.get("defective_mesh")) or any(bool((i_.get("quality") or {}).get("defective")) for i_ in FINFO.values()),
                                                                why=(MQ.get("why_mesh") or ("%d frame(s) show a crack" % sum(1 for i_ in FINFO.values() if (i_.get("quality") or {}).get("defective")))),
                                                                frames_defective=sum(1 for i_ in FINFO.values() if (i_.get("quality") or {}).get("defective")))})
_nd = sum(1 for i_ in FINFO.values() if (i_.get("quality") or {}).get("defective"))
if MQ.get("defective_mesh"): print("RENDER DEFECTIVE: every frame of this look is stamped - %s - the judge refuses them; the mesh must be made right first (PIC_DEV / PIC_ANG; an invalid face left out)" % MQ["why_mesh"], flush=True)
elif _nd: print("RENDER DEFECTIVE: %d frame(s) show a crack of the mesh and are stamped - the judge refuses the set; the mesh must be made right first (PIC_DEV / PIC_ANG; an invalid face left out)" % _nd, flush=True)
if MODE == "faces":
    print("PIECE_LOOK.json: %d frames of %s (THE TARGETED LOOK of face(s) %s) - open every one: a real defect -> `kit rebuild judge --job <J> --what look --verdict redo --frame <png> --face <n> --note \"<what it shows>\"` (no second review needed) and fix the lines / the points there; a tolerance-level flag -> say so; then the QUICK look for the piece's own verdict" % (len(frames), os.path.basename(shp), FACES), flush=True)
elif MODE == "full":
    print("PIECE_LOOK.json: %d frames of %s (the FULL look) - THE SECOND REVIEWER FIRST: `kit rebuild second --job <J> --what skin --assign` (one cad-reviewer per shard), then open every frame yourself and `kit rebuild judge --job <J> --what skin --verdict ok|redo --note \"<what they show>\"`" % (len(frames), os.path.basename(shp)), flush=True)
else:
    print("PIECE_LOOK.json: %d frames of %s (the QUICK look) - open every one: wrong -> fix the line / the points they point at and build again; right -> the REAL model: a TRIAL reinsert (`kit rebuild reinsert --set STEP=2 --set TRIAL=\"<why>\"`, mirror-checked first on a symmetric edit), or the FULL look (LOOK_MODE=full) for the second reviewer" % (len(frames), os.path.basename(shp)), flush=True)
print("DONE", flush=True)

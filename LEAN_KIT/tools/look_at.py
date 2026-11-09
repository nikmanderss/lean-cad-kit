# KIT INSTRUMENT `look_at` - ONE PICTURE AT WHAT IS ABOUT TO BE MEASURED (the look-before-measure gate's picture, kit 31am).
# Run: kit tool look_at --job <JOB> --set "BOX=x0 x1 y0 y1 z0 z1" [--set SHAPE=<.brep|.stl>] [--set WHAT="<what will be measured>"]
#      [--set VIEW="dx dy dz"] [--set VIEWS=1|2|4] [--set SECTION="x|y|z v"]
# Inputs: BOX (required: the subject - the box the measurement will read) SHAPE (default: the job's region.brep, the model of record's
#   read-only link, else content.brep) WHAT (the caption) VIEW (a look direction; default from above, aft and to the right) VIEWS (1) SECTION ("x|y|z v": the half of the part on the camera's side of that plane cut away and capped - the inside of an enclosed region shows; 31br D11)
#   CC_OUTDIR (the job folder; the picture goes to <it>\skin\review\look\ when the job has skin\review\ - the folder the judge reads - else <it>\look\)
# 31av (the client 2026-10-07: "Yes to outline"; the render study: the subject coloured triangle by triangle came out as a shredded orange band that is
# not the model): the shape is drawn in ONE colour and the subject is the yellow OUTLINE of its box. And (the client: "Deliverables review or claude code
# review? I think this is where the agents are getting confused"): the picture lands in the job's own picture folder, where `kit rebuild judge
# --frame` finds it (cited as look\<name>.png).
#
# the client, 2026-10-06: "For any step, in any process, the agent must be pushed to render review if a measurement is about to be taken in
# the next step. It can be as little as 1 image for the generic push but it must be gated to be properly targeted at the measurement
# subject in question." The guard (hooks\lookgate.py) refuses a measurement until a picture whose frame is AT its subject was opened;
# this makes that picture: the shape cut to the box (grown a margin so the subject's surroundings show), framed on the box, the box's
# edges drawn yellow. The renderer records the frame (kitlib_render.index_frame); the guard records the open. Read-only: it measures
# nothing and edits nothing.
import os, sys, time
import numpy as np
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
from PIL import Image, ImageDraw


def _fail(m):
    print(m if str(m).startswith("FAIL") else "FAIL: " + str(m), flush=True); raise SystemExit(1)


raw = os.environ.get("BOX", "").replace(",", " ").split()
try:
    b = [float(v) for v in raw]; assert len(b) == 6
except (ValueError, AssertionError):
    _fail("FAIL: BOX is six numbers \"x0 x1 y0 y1 z0 z1\" - the box the measurement will read; got %r" % os.environ.get("BOX", ""))
BOX = [min(b[0], b[1]), max(b[0], b[1]), min(b[2], b[3]), max(b[2], b[3]), min(b[4], b[5]), max(b[4], b[5])]
_base = os.environ.get("CC_OUTDIR") or os.getcwd()
OUT = os.path.join(_base, "skin", "review", "look") if os.path.isdir(os.path.join(_base, "skin", "review")) else os.path.join(_base, "look")
os.makedirs(OUT, exist_ok=True)
SHAPE = os.environ.get("SHAPE", "")
if not SHAPE:
    for cand in ("region.brep", "content.brep"):
        if os.path.isfile(cand): SHAPE = cand; break
elif not os.path.isabs(SHAPE) and not os.path.isfile(SHAPE):
    _job = os.getcwd(); _root = os.path.dirname(os.path.dirname(os.path.dirname(_job))) if os.path.basename(os.path.dirname(_job)).lower() == "jobs" else os.path.dirname(_job)
    for _b in (os.environ.get("KIT_CALLER_CWD") or "", os.path.join(_root, "claude_code"), _root):
        if _b and os.path.isfile(os.path.join(_b, SHAPE)):
            print("SHAPE: %s -> %s (resolved against %s)" % (SHAPE, os.path.normpath(os.path.join(_b, SHAPE)), _b), flush=True); SHAPE = os.path.normpath(os.path.join(_b, SHAPE)); break
if not SHAPE or not os.path.isfile(SHAPE):
    _own = [c_ for c_ in ("region.brep", "content.brep") if os.path.isfile(c_)]
    _fail("FAIL: SHAPE %r is not a file (tried as given, against the folder you ran from, claude_code\\ and the project root)%s" % (SHAPE,
          (" - the job holds %s: --set SHAPE=%s names it" % (" / ".join(_own), _own[0])) if _own else " - the job has no region.brep / content.brep: --set SHAPE=<the file you will measure>"))
WHAT = os.environ.get("WHAT", "").strip()
size = max(BOX[1] - BOX[0], BOX[3] - BOX[2], BOX[5] - BOX[4]); M = max(3.0, 0.5 * size)
lo = np.array([BOX[0] - M, BOX[2] - M, BOX[4] - M]); hi = np.array([BOX[1] + M, BOX[3] + M, BOX[5] + M])
sys.path.insert(0, os.path.join(os.environ["KIT_HOME"], "rebuild")); import sk_lib as K
LINES_ONLY = []; FID = None; MQ = None; TINT = None
if SHAPE.lower().endswith(".stl"):
    V, T = R.read_stl(SHAPE); V = np.asarray(V, float); T = np.asarray(T); FID = np.zeros(len(T), int); MQ = K.mesh_quality(V, T, FID, closed=False, judge_open=False)
    C = V[T].mean(axis=1); TINT = np.all((C >= lo) & (C <= hi), axis=1)
else:
    import Part
    s = Part.Shape(); s.importBrep(SHAPE)
    sel = [i for i, f in enumerate(s.Faces) if not (f.BoundBox.XMax < lo[0] or f.BoundBox.XMin > hi[0] or f.BoundBox.YMax < lo[1] or f.BoundBox.YMin > hi[1]
                                                     or f.BoundBox.ZMax < lo[2] or f.BoundBox.ZMin > hi[2])]
    if not sel and not s.Faces and s.Edges:
        # guides.brep
        for e in s.Edges:
            bb = e.BoundBox
            if bb.XMax < lo[0] or bb.XMin > hi[0] or bb.YMax < lo[1] or bb.YMin > hi[1] or bb.ZMax < lo[2] or bb.ZMin > hi[2]: continue
            LINES_ONLY.append(np.array([[q.x, q.y, q.z] for q in e.discretize(Number=max(2, int(e.Length / 0.1) + 1))]))
        if not LINES_ONLY: _fail("FAIL: no edge of %s comes near the box %s - is it the right shape, the right box?" % (SHAPE, BOX))
        V = np.vstack(LINES_ONLY); T = np.zeros((0, 3), int)
    elif not sel: _fail("FAIL: no face of %s comes near the box %s - is it the right shape, the right box?" % (SHAPE, BOX))
    else:
        okf = [i for i, f in enumerate(s.Faces) if f.isValid()]
        V, T, FID, MQ = K.piece_mesh(SHAPE, s, faces=(None if len(okf) == len(s.Faces) else okf), cache_dir=OUT, say=lambda m_: print(m_, flush=True))
        V = np.asarray(V, float); T = np.asarray(T, int); FID = np.asarray(FID, int)
        if len(okf) != len(s.Faces): FID = np.asarray(okf)[FID]
        TINT = np.isin(FID, np.asarray(sel))
        SUBJ = [i for i in sel if BOX[0] <= 0.5 * (s.Faces[i].BoundBox.XMin + s.Faces[i].BoundBox.XMax) <= BOX[1] and BOX[2] <= 0.5 * (s.Faces[i].BoundBox.YMin + s.Faces[i].BoundBox.YMax) <= BOX[3] and BOX[4] <= 0.5 * (s.Faces[i].BoundBox.ZMin + s.Faces[i].BoundBox.ZMax) <= BOX[5]]
        SUBJ_T = np.isin(FID, np.asarray(SUBJ)) if SUBJ else None
if not LINES_ONLY:
    rng_ = np.random.RandomState(3); fc_ = rng_.uniform(0.45, 0.85, (int(FID.max()) + 1 if len(FID) else 1, 3))
    col = np.where(TINT[:, None], fc_[np.maximum(FID, 0)], np.array([0.50, 0.52, 0.56])[None, :])
dirs = [(-0.45, -0.45, -0.77), (0.45, -0.45, -0.77), (0.45, 0.45, -0.77), (-0.45, 0.45, -0.77)]
SHARE = {}
if os.environ.get("VIEW"):
    try:
        _v = [float(v) for v in os.environ["VIEW"].replace(",", " ").split()]
        if len(_v) != 3 or np.linalg.norm(_v) < 1e-9: raise ValueError
        dirs = [tuple(_v)] + dirs
    except ValueError: _fail("FAIL: VIEW is three numbers \"dx dy dz\" (a look direction, not all zero); got %r" % os.environ.get("VIEW", ""))
SEC = None
if os.environ.get("SECTION", "").strip() and not LINES_ONLY:
    try:
        _sx = os.environ["SECTION"].replace(",", " ").split(); _ax = "xyz".index(_sx[0].lower()); _at = float(_sx[1]); SEC = (_ax, _at)
    except (ValueError, IndexError): _fail("FAIL: SECTION is \"x|y|z <value>\" - the plane whose near half (the camera's side) is cut away; got %r" % os.environ.get("SECTION", ""))
def _cut_for(d_):
    """the triangles kept for a camera looking along d_: without SECTION all of them; with it the half beyond the plane from the camera"""
    if SEC is None or not len(T): return np.ones(len(T), bool)
    _n = np.zeros(3); _n[SEC[0]] = 1.0; _s = float(np.asarray(d_, float) @ _n)
    if abs(_s) < 1e-9: return np.ones(len(T), bool)
    return ((V[T].mean(axis=1)[:, SEC[0]] - SEC[1]) * _s) >= 0.0
if SEC is not None and not LINES_ONLY: print("SECTION: the part cut EXACTLY by the plane %s = %g - the half on the camera's side left out of the picture, the cut face capped by the kernel's section (31br D11b)" % ("xyz"[SEC[0]], SEC[1]), flush=True)
_CAP = None


def _cap_make():
    """31br D11b: the kernel's own SECTION of the shape at the plane - its faces (holes kept: Part::FaceMakerBullseye) tessellated as the cap, its wires as the outline; made once.
    A mesh subject has no kernel shape: the cut stays open, said. Returns (V, T, outline polylines, the note)."""
    global _CAP
    if _CAP is not None: return _CAP
    if SEC is None: _CAP = (np.zeros((0, 3)), np.zeros((0, 3), int), [], ""); return _CAP
    if SHAPE.lower().endswith(".stl"): _CAP = (np.zeros((0, 3)), np.zeros((0, 3), int), [], "a mesh subject: no kernel section - the cut is open (no cap)"); return _CAP
    try:
        import Part
        from FreeCAD import Base
        _nv = [0.0, 0.0, 0.0]; _nv[SEC[0]] = 1.0
        _ws = [w for w in s.slice(Base.Vector(*_nv), float(SEC[1])) if w.isClosed()]
        if not _ws: _CAP = (np.zeros((0, 3)), np.zeros((0, 3), int), [], "the plane misses the shape: nothing to cap"); return _CAP
        try: _fcs = Part.makeFace(_ws, "Part::FaceMakerBullseye").Faces
        except Exception: _fcs = [Part.Face(w) for w in _ws]
        _Vs, _Ts, _off = [], [], 0
        for _f in _fcs:
            _vs, _ts = _f.tessellate(0.05)
            if not _ts: continue
            _Vs.append(np.array([[q.x, q.y, q.z] for q in _vs], float)); _Ts.append(np.array(_ts, int) + _off); _off += len(_vs)
        _pl = [(np.array([[q.x, q.y, q.z] for q in w.discretize(Number=max(2, int(w.Length / 0.2) + 1))]), (35, 35, 35), 2, ()) for w in _ws]
        _CAP = (np.vstack(_Vs) if _Vs else np.zeros((0, 3)), np.vstack(_Ts) if _Ts else np.zeros((0, 3), int), _pl,
                "capped: the kernel's section (%d face(s), grey, outlined)" % len(_fcs))
    except Exception as _e:
        _CAP = (np.zeros((0, 3)), np.zeros((0, 3), int), [], "the cap could not be made (%s): the cut is open" % str(_e)[:80])
    return _CAP


def _cut_mesh(d_):
    """31br D11b (the agent's render_section_shred): the SECTION cut EXACTLY at the plane for a camera looking along d_ - a triangle wholly on the camera's side is dropped, one wholly beyond
    is kept, a STRADDLING one is clipped at the plane to its kept polygon (one or two triangles with the face's own id and tint, so the shading and the depth test hold); nothing is
    kept or dropped by its centroid (that drew a saw-tooth front edge with the faces behind showing through). The cap (_cap_make) is added, its triangles turned toward the camera.
    Returns (V, T, FID, colours, cap outline polylines, the cap note)."""
    if SEC is None or not len(T): return V, T, FID, col, [], ""
    _ax, _at = SEC; _n = np.zeros(3); _n[_ax] = 1.0; _s = float(np.asarray(d_, float) @ _n)
    if abs(_s) < 1e-9: return V, T, FID, col, [], "the camera lies in the plane: no cut"
    _kv = ((V[:, _ax] - _at) * _s) >= 0.0; _kt = _kv[T]; _nk = _kt.sum(axis=1)
    _full = _nk == 3; _mix = (_nk == 1) | (_nk == 2)
    _V2 = [V]; _T2 = [T[_full]]; _F2 = [FID[_full]]; _C2 = [col[_full]]; _base = len(V)
    if _mix.any():
        _Tm, _Fm, _Cm, _km = T[_mix], FID[_mix], col[_mix], _kt[_mix]
        _nV, _nT, _nF, _nC = [], [], [], []
        def _X(p_, q_):
            _t = (_at - V[p_, _ax]) / (V[q_, _ax] - V[p_, _ax]); return V[p_] + _t * (V[q_] - V[p_])
        for _i in range(len(_Tm)):
            _tri, _k = _Tm[_i], _km[_i]; _one = int(_k.sum()) == 1
            _r = int(np.nonzero(_k if _one else ~_k)[0][0])
            _a, _b, _c = _tri[_r], _tri[(_r + 1) % 3], _tri[(_r + 2) % 3]
            _p1, _p2 = _X(_a, _b), _X(_c, _a); _j = _base + len(_nV); _nV += [_p1, _p2]
            if _one: _nT.append([_a, _j, _j + 1]); _nF.append(_Fm[_i]); _nC.append(_Cm[_i])
            else: _nT += [[_j, _b, _c], [_j, _c, _j + 1]]; _nF += [_Fm[_i], _Fm[_i]]; _nC += [_Cm[_i], _Cm[_i]]
        _V2.append(np.array(_nV)); _T2.append(np.array(_nT, int)); _F2.append(np.array(_nF, int)); _C2.append(np.array(_nC))
    _V2 = np.vstack(_V2); _T2 = np.vstack(_T2); _F2 = np.concatenate(_F2); _C2 = np.vstack(_C2)
    _cV, _cT, _cpl, _note = _cap_make()
    if len(_cT):
        _cT = np.asarray(_cT, int).copy(); _P = _cV[_cT]; _fn = np.cross(_P[:, 1] - _P[:, 0], _P[:, 2] - _P[:, 0])
        _flip = (_fn @ np.asarray(d_, float)) > 0; _cT[_flip] = _cT[_flip][:, [0, 2, 1]]          # the cap faces the camera
        _T2 = np.vstack([_T2, _cT + len(_V2)]); _V2 = np.vstack([_V2, _cV])
        _F2 = np.concatenate([_F2, np.full(len(_cT), (int(FID.max()) + 1) if len(FID) else 0)]); _C2 = np.vstack([_C2, np.tile(np.array([[0.80, 0.78, 0.72]]), (len(_cT), 1))])
    return _V2, _T2, _F2, _C2, _cpl, _note
SUBJ_SHARES = {}
if os.environ.get("VIEW"):
    pass
elif not LINES_ONLY and TINT is not None and TINT.any():
    Cc_ = V[T].mean(axis=1); _subm = globals().get("SUBJ_T"); inb_ = (TINT if _subm is None else _subm) & np.all((Cc_ >= lo) & (Cc_ <= hi), axis=1)
    if inb_.any():
        A_ = 0.5 * np.linalg.norm(np.cross(V[T[inb_, 1]] - V[T[inb_, 0]], V[T[inb_, 2]] - V[T[inb_, 0]]), axis=1); A_ = A_ / max(A_.sum(), 1e-12)
        Ps_ = Cc_[inb_][np.random.RandomState(7).choice(int(inb_.sum()), size=min(60, int((A_ > 0).sum())), replace=False, p=A_)]
        cands_ = [tuple(np.asarray(d_, float) / np.linalg.norm(d_)) for d_ in dirs] + [tuple(-np.asarray(d_, float) / np.linalg.norm(d_)) for d_ in dirs]
        def _score(d_):
            _k = _cut_for(d_)
            return K.visible_fraction(V, T[_k], inb_[_k], Ps_, d_) if _k.all() or inb_[_k].any() else 0.0
        scored_ = sorted(((_score(d_), d_) for d_ in cands_), key=lambda s_: -s_[0])
        dirs = [d_ for _, d_ in scored_]; SHARE = {d_: f_ for f_, d_ in scored_}
        print("camera: %.0f%% of the subject in view from the best of 8 directions (%.0f%% from the default)%s" % (100 * scored_[0][0], 100 * dict((d_, f_) for f_, d_ in scored_)[cands_[0]],
              (" - the subject: %d face(s) centred in the box %s (the %d other faces touching it are context)" % (len(globals().get("SUBJ") or []), (globals().get("SUBJ") or [])[:12], len(sel) - len(globals().get("SUBJ") or []))) if _subm is not None else " - NO face is centred in the box: the subject is every face touching it (name a tighter box)"), flush=True)
        if _subm is not None:
            _db = scored_[0][1]; _kb = _cut_for(_db)
            for _fi in (globals().get("SUBJ") or []):
                _mf = (FID == _fi) & np.all((Cc_ >= lo) & (Cc_ <= hi), axis=1) & _kb
                if not _mf.any(): SUBJ_SHARES[_fi] = 0.0; continue
                _Pf = Cc_[_mf][np.random.RandomState(11).choice(int(_mf.sum()), size=min(40, int(_mf.sum())), replace=False)]
                try: SUBJ_SHARES[_fi] = float(K.visible_fraction(V, T[_kb], _mf[_kb], _Pf, _db))
                except Exception: SUBJ_SHARES[_fi] = float("nan")
            _hid = [f_ for f_, v_ in SUBJ_SHARES.items() if v_ == v_ and v_ < 0.2]
            print("subject faces in view from that camera: %s%s" % (", ".join("face %d %.0f%%" % (f_, 100 * v_) for f_, v_ in sorted(SUBJ_SHARES.items(), key=lambda kv_: kv_[1])[:12]),
                  ((" - face(s) %s are under 20 %% in view: under this SECTION a face on the camera's side of the plane is CUT AWAY by design - look from the other side (VIEW) or move the plane for them (31br D11)" % _hid) if SEC is not None else
                   (" - face(s) %s are HIDDEN (under 20 %% in view from every direction tried): this picture is no evidence of them - cut the part (SECTION=\"x|y|z <value>\") or use skin-look's per-face frames (31br D11)" % _hid)) if _hid else ""), flush=True)
n = max(1, min(4, int(os.environ.get("VIEWS", "1") or 1)))
corners = np.array([[x, y, z] for x in BOX[:2] for y in BOX[2:4] for z in BOX[4:]], float)
EDGES = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]
stamp = time.strftime("%H%M%S"); out = []
for k, d in enumerate(dirs[:n]):
    d = np.array(d, float); d = d / np.linalg.norm(d)
    path = os.path.join(OUT, "look_%s_%d.png" % (stamp, k + 1))
    _sh = SHARE.get(tuple(d)) if SHARE else None
    ttl = "LOOK AT %s%s%s" % (" ".join("%g" % round(v, 2) for v in BOX), (" - " + WHAT) if WHAT else "", ("" if _sh is None or _sh >= 0.9 else (" (%.0f%% of the subject in view)" % (100 * _sh) if _sh >= 0.05 else " (SEEN FROM NOWHERE: %.0f%% of the subject in view - the part covers it from every side)" % (100 * _sh))))
    if LINES_ONLY:
        mmpx = R.render(path, [("s", corners, np.array([[0, 1, 2]]), np.array([[0.1, 0.1, 0.12]]))], d, W=1100, pad=1.5, focus=corners, title=ttl, edges=False)
        d3, r3, u3 = R.basis(d); x0 = (corners @ r3).min() - 1.5; y1 = (corners @ u3).max() + 1.5
        im = Image.open(path).convert("RGB"); dr = ImageDraw.Draw(im)
        for P_ in LINES_ONLY:
            Q_ = np.stack([(P_ @ r3 - x0) / mmpx, (y1 - P_ @ u3) / mmpx], 1); dr.line([tuple(q) for q in Q_], fill=(120, 220, 255), width=2)
        P2 = np.stack([(corners @ r3 - x0) / mmpx, (y1 - corners @ u3) / mmpx], 1)
        for a, c in EDGES: dr.line([tuple(P2[a]), tuple(P2[c])], fill=(255, 220, 40), width=3)
        im.save(path)
    else:
        box_lines = [(np.linspace(corners[a], corners[c], 40), (255, 220, 40), 3, ()) for a, c in EDGES]
        _V2, _T2, _F2, _C2, _cpl, _cnote = _cut_mesh(d)
        if SEC is not None and k == 0: print("SECTION: %s; %d triangle(s) clipped at the plane" % (_cnote, int(((_kt_ := ((((V[:, SEC[0]] - SEC[1]) * float(d[SEC[0]])) >= 0.0)[T]).sum(axis=1)) % 3 != 0).sum())), flush=True)
        K.view_piece(R, path, _V2, _T2, _F2, _C2, d, tuple(BOX), 1100, ttl, ttl,
                     ["The whole shape, opaque, framed on the box (yellow, dotted where it is behind the part); the faces within %g mm of the box (by their bounding box) in their own tints, the rest grey." % M,
                      "Smooth shading from the surface's own normals within each face (a crease between faces stays sharp). The mesh line below says how fine; a red RENDER DEFECTIVE banner across the frame means it is NO EVIDENCE."
                      + (" SECTION %s = %g: the part cut EXACTLY at the plane (every straddling triangle clipped there), the camera's half left out; the cut face %s." % ("xyz"[SEC[0]], SEC[1], _cnote or "open") if SEC is not None else "")],
                     polylines=box_lines + list(_cpl), quality=MQ)
    out.append(path)
FQ = K.frame_quality(MQ, tuple(BOX)) if (MQ and not LINES_ONLY) else None
print("LOOK: %d picture(s) of the box %s on %s (the piece view: opaque, the faces at the box tinted; the yellow outline = the subject's box)%s:" % (len(out), BOX, os.path.basename(SHAPE),
      (" - RENDER DEFECTIVE: %s" % FQ["why"]) if (FQ and FQ.get("defective")) else ((" - the mesh has %d crack(s) elsewhere, none in this box" % MQ["cracks"]) if (MQ and MQ.get("cracks")) else (" - the mesh's defect (%s) lies outside this box: these frames are sound (31br D11)" % str(MQ.get("why"))[:100]) if (MQ and MQ.get("defective")) else "")), flush=True)
for p in out: print("   %s" % p, flush=True)
print("OPEN IT (the Read tool) - the guard records the open - say in a sentence what it shows; then the measurement of this box may run.", flush=True)
print("DONE", flush=True)

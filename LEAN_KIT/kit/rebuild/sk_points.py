# kit rebuild
# kit rebuild
# ORIGINAL
# PRIOR ART
# over the
import os, sys, json, time
if not globals().get("_SK_INNER"):      # 31br D3 (2026-10-29): a crash's TRACEBACK reaches the log
    import runpy as _rp3, traceback as _tb3
    try: _rp3.run_path(os.path.abspath(__file__), init_globals={"_SK_INNER": True}, run_name="__main__")
    except SystemExit: raise
    except BaseException:
        print("TRACEBACK (31br D3) - the crash's place:\n" + _tb3.format_exc(), flush=True); raise
    raise SystemExit(0)
import numpy as np
import Part
from FreeCAD import Vector as V3
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sk_lib as K; RUN = K.RUN; K.need_window()
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw
import colorsys
NPTS = int(os.environ.get("NPTS", "1000")); ON_MM = float(os.environ.get("ON_MM", "0.10"))
SK = K.SK
OUT = K.OUT
T0 = time.time()
def say(*a): print("%5.0fs " % (time.time() - T0), *a, flush=True)
Z = np.load(os.path.join(SK, "regions.npz")); Vu, F, vreg = Z["Vu"], Z["F"], Z["vreg"]
FID = np.asarray(Z["fid"], np.int64) if "fid" in Z.files else None   # skin-source
P3 = Vu[F]; Cn = P3.mean(axis=1); At = 0.5 * np.linalg.norm(np.cross(P3[:, 1] - P3[:, 0], P3[:, 2] - P3[:, 0]), axis=1)
inside_win = K.wall_dist(Cn) > 0.3
# over the
area = At[inside_win].sum(); cell = np.sqrt(area / NPTS) * 0.85
for it in range(8):
    key = np.floor(Cn[inside_win] / cell).astype(np.int64)
    _, first = np.unique(key, axis=0, return_index=True)
    if len(first) > 1.15 * NPTS: cell *= 1.1
    elif len(first) < 0.85 * NPTS: cell /= 1.1
    else: break
idx = np.nonzero(inside_win)[0][first]; P = Cn[idx]; TIDX = list(idx)
say("points: %d on the %s (grid %.2f mm), edit region walls left out" % (len(P), "original's own mesh" if FID is not None else "voxel skin", cell))
SRC = ["grid"] * len(P)
LEVER_WHYS = {"PTS_BOX": [], "PTS_DROP": []}
def _boxes(s, lever="PTS_BOX"):
    """31bq B22 (the client 2026-10-19): every box carries ITS REASON - \"x0 x1 y0 y1 z0 z1 [spacing] | why\" (a deliberate PTS_DROP with no recorded reason was removed by a
    later session as 'no recorded reason' and the build went invalid - the agent's c1). The reasons go into points1000.json (levers / lever_whys)."""
    out = []
    for part in (s or "").split(";"):
        if not part.strip(): continue
        nums, _, why = part.partition("|")
        v = nums.replace(",", " ").split()
        if not v: continue
        try:
            b = [float(x) for x in v]
        except ValueError:
            K._fail("FAIL: a box is \"x0 x1 y0 y1 z0 z1 [spacing] | why\", not %r" % part.strip())
        if len(b) not in (6, 7): K._fail("FAIL: a box is six numbers (and a spacing for PTS_BOX) then \"| why\", not %r" % part.strip())
        if len(why.strip()) < 10: K._fail("FAIL: %s box %s carries no reason - the form is \"x0 x1 y0 y1 z0 z1 [spacing] | why\" (ten characters at least: which face it keeps or drops and why; 31bq B22 - a box without its reason was undone by a later session)" % (lever, " ".join(v)))
        LEVER_WHYS.setdefault(lever, []).append({"box": b, "why": why.strip()})
        out.append(b)
    return out
def _inbox(Q, b):
    return (Q[:, 0] >= min(b[0], b[1])) & (Q[:, 0] <= max(b[0], b[1])) & (Q[:, 1] >= min(b[2], b[3])) & (Q[:, 1] <= max(b[2], b[3])) & (Q[:, 2] >= min(b[4], b[5])) & (Q[:, 2] <= max(b[4], b[5]))
LOCKED = []
try:
    LOCKED = [sp_ for sp_ in json.load(open(os.path.join(SK, "RESTART.json"), encoding="utf-8")).get("spots", []) if sp_.get("locked")]
except (OSError, ValueError):
    LOCKED = []
for sp_ in [s_ for s_ in LOCKED if not np.any(_inbox(Cn, s_["box"]))]:      # nothing to pick
    say("THE RESTART, PER SPOT: spot %d %s holds NO source-triangle centroid - nothing to pick there; it is not a points spot and the runner releases it (31br G4c: its tries were the lines' or the build's)" % (sp_["id"], [round(v, 1) for v in sp_["box"]]))
LOCKED = [s_ for s_ in LOCKED if np.any(_inbox(Cn, s_["box"]))]
_PREV_PTS = os.path.join(SK, "points1000.json")
if bool(LOCKED) and not os.path.isfile(_PREV_PTS):
    try:
        import glob as _glob4
        _cands4 = sorted(_glob4.glob(os.path.join(RUN, "tags", "*", "points1000.json")), key=os.path.getmtime)
        if _cands4: _PREV_PTS = _cands4[-1]; say("THE RESTART, PER SPOT: skin\\points1000.json is missing (a crashed run renamed it) - the points KEPT outside the locked spots are the newest tag copy's: %s (31br G4a)" % os.path.relpath(_PREV_PTS, RUN))
    except Exception: pass
KEEP = os.environ.get("KEEP_POINTS", "1") == "1" and bool(LOCKED) and os.path.isfile(_PREV_PTS)
def _in_locked(Q):
    m_ = np.zeros(len(Q), bool)
    for sp_ in LOCKED: m_ |= _inbox(Q, sp_["box"])
    return m_
def _box_hits_spot(b):
    return any(not (max(b[0], b[1]) < sp_["box"][0] or min(b[0], b[1]) > sp_["box"][1] or max(b[2], b[3]) < sp_["box"][2] or min(b[2], b[3]) > sp_["box"][3]
                    or max(b[4], b[5]) < sp_["box"][4] or min(b[4], b[5]) > sp_["box"][5]) for sp_ in LOCKED)
OLD = []
if KEEP:
    OLD = json.load(open(_PREV_PTS, encoding="utf-8")).get("points") or []
    m_ = _in_locked(P); P = P[m_]; SRC = [s_ for s_, k_ in zip(SRC, m_) if k_]; TIDX = [t_ for t_, k_ in zip(TIDX, m_) if k_]
    OLD = [q for q in OLD if not _in_locked(np.array([q[:3]], float))[0]]
    say("THE RESTART, PER SPOT: %d locked spot(s) %s - %d point(s) outside them KEPT as they were; the grid gives %d new point(s) inside them"
        % (len(LOCKED), [(sp_["id"], [round(v, 1) for v in sp_["box"]]) for sp_ in LOCKED], len(OLD), len(P)))
for b in _boxes(os.environ.get("PTS_DROP", ""), "PTS_DROP"):
    if KEEP and not _box_hits_spot(b): K._fail("FAIL: PTS_DROP %s is outside every locked spot - the restart picks again only where the tries failed (the rest is kept)" % b[:6])
    k0 = len(P); m_ = ~_inbox(P, b); P = P[m_]; SRC = [s_ for s_, k_ in zip(SRC, m_) if k_]; TIDX = [t_ for t_, k_ in zip(TIDX, m_) if k_]
    say("PTS_DROP %s: %d point(s) taken out" % (b, k0 - len(P)))
for b in _boxes(os.environ.get("PTS_BOX", ""), "PTS_BOX"):
    if KEEP and not _box_hits_spot(b): K._fail("FAIL: PTS_BOX %s is outside every locked spot - the restart picks again only where the tries failed (the rest is kept)" % b[:6])
    sp_ = b[6] if len(b) == 7 else cell / 3.0
    cand = np.nonzero(inside_win & _inbox(Cn, b) & (_in_locked(Cn) if KEEP else True))[0]
    if not len(cand):
        say("PTS_BOX %s: no voxel skin inside the box (look at the SP7d frames again)" % b[:6]); continue
    key = np.floor(Cn[cand] / sp_).astype(np.int64); _, f_ = np.unique(key, axis=0, return_index=True)
    add = Cn[cand[f_]]; P = np.vstack([P, add]); SRC += ["box"] * len(add); TIDX += list(cand[f_])
    say("PTS_BOX %s: %d point(s) added at %.2f mm" % (b[:6], len(add), sp_))
body = Part.Shape(); body.importBrep(K.BODY); BF = body.Faces
sel = [i for i, f in enumerate(BF) if not (f.BoundBox.XMax < K.WIN[0] - 1 or f.BoundBox.XMin > K.WIN[1] + 1 or f.BoundBox.YMax < K.WIN[2] - 1
       or f.BoundBox.YMin > K.WIN[3] + 1 or f.BoundBox.ZMax < K.WIN[4] - 1 or f.BoundBox.ZMin > K.WIN[5] + 1)]
VO, TO, FO = R.tess_shape(body, 0.01, faces=sel); FO = np.asarray(sel)[FO]
kd = cKDTree(VO[TO].mean(axis=1))
FRAME_FACES = {}
if os.environ.get("FRAME_PTS", "1") == "1" and os.path.isfile(os.path.join(RUN, "wall_caps.brep")):
    FMM = float(os.environ.get("FRAME_PTS_MM", "1.5"))
    wc_ = Part.Shape(); wc_.importBrep(os.path.join(RUN, "wall_caps.brep"))
    wd_ = K.wall_dist(Cn); ok_ = (wd_ > 0.3) & (wd_ < FMM); kdF = cKDTree(Cn[ok_]); idF = np.nonzero(ok_)[0]
    add = []; add_t = []
    for e in wc_.Edges:
        S_ = np.array([[q.x, q.y, q.z] for q in e.discretize(Number=5)])[1:4]
        _, nn_ = kd.query(S_[1], k=12, workers=-1)
        best = None
        for fi in dict.fromkeys(FO[nn_].tolist()):
            try: d_ = BF[fi].distToShape(Part.Vertex(V3(*S_[1])))[0]
            except Exception: continue
            if best is None or d_ < best[0]: best = (d_, fi)
        if best is not None and best[0] < 0.01: FRAME_FACES.setdefault(int(best[1]), []).append([round(float(v), 2) for v in S_[1]])
        if not len(idF): continue
        dq, iq = kdF.query(S_, k=1)
        for dd, ii in zip(np.atleast_1d(dq), np.atleast_1d(iq)):
            if dd < 2.0 * FMM: add.append(Cn[idF[ii]]); add_t.append(int(idF[ii]))
    if add:
        add = np.array(add); add_t = np.array(add_t)
        _, u_ = np.unique(np.round(add, 3), axis=0, return_index=True); add = add[u_]; add_t = add_t[u_]
        if KEEP:
            kl_ = _in_locked(add); add = add[kl_]; add_t = add_t[kl_]
        far = (cKDTree(P).query(add)[0] > 0.2 if len(P) else np.ones(len(add), bool)) if len(add) else np.zeros(0, bool)
        P = np.vstack([P, add[far]]); SRC += ["frame"] * int(far.sum()); TIDX += list(add_t[far])
    say("FRAME_PTS: %d point(s) beside the %d edges of the reinsert faces (%.1f mm inside the edit region); %d original face(s) bound those edges"
        % (int(sum(1 for s_ in SRC if s_ == "frame")), len(wc_.Edges), FMM, len(FRAME_FACES)))
face = np.full(len(P), -1); dist = np.full(len(P), np.inf)
if FID is not None:
    # recorded
    for i, t_ in enumerate(TIDX):
        fi = int(FID[int(t_)]) if int(t_) >= 0 else -1
        if fi < 0: continue
        face[i] = fi; p = V3(*P[i])
        try:
            u, w = BF[fi].Surface.parameter(p); dist[i] = (BF[fi].Surface.value(u, w) - p).Length
        except Exception:
            dist[i] = 0.0
    say("faces by the source triangles (the B-rep source): %d points on %d original faces" % (int((face >= 0).sum()), len(np.unique(face[face >= 0]))))
else:
    _, nn = kd.query(P, k=24, workers=-1)
    for i, p_ in enumerate(P):
        p = V3(*p_)
        for fi in dict.fromkeys(FO[nn[i]].tolist()):
            f = BF[fi]
            try:
                u, w = f.Surface.parameter(p)
                if not f.isPartOfDomain(u, w): continue
                d = (f.Surface.value(u, w) - p).Length
            except Exception: continue
            if d < dist[i]: dist[i] = d; face[i] = fi
if KEEP and OLD:
    P = np.vstack([np.array([q[:3] for q in OLD], float), P]) if len(P) else np.array([q[:3] for q in OLD], float)
    face = np.concatenate([np.array([int(q[3]) for q in OLD]), face])
    dist = np.concatenate([np.array([float(q[4]) if q[4] is not None else np.inf for q in OLD]), dist])
    SRC = [(q[5] if len(q) > 5 else "grid") + "+kept" for q in OLD] + SRC
on = (face >= 0) & (dist <= ON_MM)
say("projected in %.0f s: ON an original face %d, OFF %d (nearest face further than %.2f mm or none)" % (time.time() - T0, int(on.sum()), int((~on).sum()), ON_MM))
fs = {}
for i in range(len(P)):
    if face[i] >= 0: fs.setdefault(int(face[i]), [0, 0]); fs[int(face[i])][0 if on[i] else 1] += 1
kept = sorted(f for f, (a, b) in fs.items() if b == 0); changed = sorted(f for f, (a, b) in fs.items() if b > 0)
if FID is not None: sel = sorted(int(x) for x in np.unique(FID[FID >= 0]))   # the census counts the CONTENT's faces
nopts = sorted(set(sel) - set(fs))
say("original faces in the edit region: %d - KEPT (all points ON) %d, CHANGED (some points OFF) %d, NO POINTS %d (%s)" % (len(sel), len(kept), len(changed), len(nopts),
    "absorbed by their neighbours in skin-labels - PTS_BOX one to keep it" if FID is not None else "small faces, or faces the voxel buried"))
for f in sorted(changed, key=lambda f: -fs[f][1])[:25]: say("   face %4d: %3d points ON, %3d OFF (area %.1f mm2)" % (f, fs[f][0], fs[f][1], BF[f].Area))
fr_miss = sorted(f for f in FRAME_FACES if fs.get(f, [0, 0])[0] == 0)
if FRAME_FACES:
    say("frame faces (original faces the reinsert faces' edges bound): %d; with ON points %d; WITH NO ON POINT %d %s"
        % (len(FRAME_FACES), len(FRAME_FACES) - len(fr_miss), len(fr_miss), fr_miss[:20]))
    for f in fr_miss[:20]:
        say("   frame face %d (%.1f mm2): its wall edge(s) at %s get no face of their own - PTS_BOX there, or say why it is to blend away"
            % (f, BF[f].Area, FRAME_FACES[f][:2]))
json.dump({"NPTS": len(P), "ON_MM": ON_MM, "points": [[round(float(x), 4) for x in P[i]] + [int(face[i]), round(float(dist[i]), 4) if np.isfinite(dist[i]) else None, SRC[i]] for i in range(len(P))],
           "kept": kept, "changed": changed, "no_points": nopts, "counts": {str(k): v for k, v in fs.items()},
           "frame_faces": {str(f): {"edge_mids": m_, "on": fs.get(f, [0, 0])[0], "off": fs.get(f, [0, 0])[1]} for f, m_ in FRAME_FACES.items()},
           "frame_faces_no_point": fr_miss, "levers": {k: os.environ.get(k, "") for k in ("NPTS", "ON_MM", "PTS_BOX", "PTS_DROP", "FRAME_PTS", "FRAME_PTS_MM")}, "lever_whys": LEVER_WHYS},
          open(os.path.join(SK, "points1000.json"), "w"), indent=0)
json.dump([{"face": int(f), "area_mm2": round(float(BF[f].Area), 2), "bbox": [round(v, 2) for v in (BF[f].BoundBox.XMin, BF[f].BoundBox.XMax, BF[f].BoundBox.YMin, BF[f].BoundBox.YMax, BF[f].BoundBox.ZMin, BF[f].BoundBox.ZMax)],
            "on": fs.get(f, [0, 0])[0], "off": fs.get(f, [0, 0])[1], "frame": f in FRAME_FACES} for f in sel],
          open(os.path.join(SK, "points_faces.json"), "w"), indent=0)
uf = sorted(fs); hue = {f: 0.10 + 0.78 * ((k * 0.618034) % 1.0) for k, f in enumerate(uf)}
EC = json.load(open(os.path.join(K.EDGEMAP, "edge_classes.json")))
oruns = [np.array(rr, float) for r in EC for rr in r["runs"]]
import glob as _glob
for _old in _glob.glob(os.path.join(OUT, "SP7d%s_*.png" % os.environ.get("SUFFIX", ""))):
    try: os.remove(_old)
    except OSError: pass
miss_mids = np.array([m_ for f in fr_miss for m_ in FRAME_FACES[f]], float).reshape(-1, 3)
_frames = []
SPOTV = []
for sp_ in LOCKED:
  try:
    bx_ = sp_["box"]; mt_ = _inbox(Cn, [bx_[0] - 1, bx_[1] + 1, bx_[2] - 1, bx_[3] + 1, bx_[4] - 1, bx_[5] + 1])
    if not mt_.any(): continue
    nr_ = np.cross(P3[mt_, 1] - P3[mt_, 0], P3[mt_, 2] - P3[mt_, 0]).sum(0)
    pv_ = Cn[mt_]
    if len(pv_) >= 3: _, _, vh_ = np.linalg.svd(pv_ - pv_.mean(0), full_matrices=False)
    else: vh_ = np.eye(3); say("   restart spot %d: %d triangle centroid(s) in its grown box - the default iso directions (31br G4a: the SVD of one point has one row; d13's crash)" % (sp_["id"], len(pv_)))
    if vh_.shape[0] < 3: vh_ = np.vstack([vh_, np.eye(3)])[:3]
    for j_, dv_ in enumerate(K.iso_dirs(nr_ if np.linalg.norm(nr_) > 1e-9 else vh_[2], vh_[0], vh_[1])):
        SPOTV.append(("spot%d_iso%d" % (sp_["id"], j_ + 1), dv_, (bx_[0] - 3, bx_[1] + 3, bx_[2] - 3, bx_[3] + 3, bx_[4] - 3, bx_[5] + 3), 1200,
                      "RESTART spot %d, iso %d - re-pick the points HERE" % (sp_["id"], j_ + 1)))
  except Exception as _exsp:
    say("   restart spot %s: its close-ups could not be set up (%s) - the pick stands, the default views only (31br G4a (3))" % (sp_.get("id"), str(_exsp)[:120]))
for k, (nm, d, fb, W, ttl) in enumerate(K.views(close=not SPOTV, below=True) + SPOTV):
    path = os.path.join(OUT, "SP7d%s_%02d_%s.png" % (os.environ.get("SUFFIX", ""), k + 1, nm)); foc = K.corners(fb); pad = 1.0; _frames.append(path)
    gb = (fb[0] - 4, fb[1] + 4, fb[2] - 4, fb[3] + 4, fb[4] - 4, fb[5] + 4)
    m = (Cn[:, 0] >= gb[0]) & (Cn[:, 0] <= gb[1]) & (Cn[:, 1] >= gb[2]) & (Cn[:, 1] <= gb[3]) & (Cn[:, 2] >= gb[4]) & (Cn[:, 2] <= gb[5])
    im, mmpx, x0, y1, r3, u3 = K.render_transparent(R, Vu, F[m], d, foc, W, pad)
    dr = ImageDraw.Draw(im); pr = lambda Q: [tuple(v) for v in np.stack([(Q @ r3 - x0) / mmpx, (y1 - Q @ u3) / mmpx], 1)]
    for Q in oruns: dr.line(pr(Q), fill=(255, 255, 255), width=1)
    pp = pr(P)
    for i, (x, y) in enumerate(pp):
        if on[i]:
            c = tuple(int(255 * v) for v in colorsys.hsv_to_rgb(hue[int(face[i])], 0.85, 1.0)); r = 3
            dr.ellipse([x - r, y - r, x + r, y + r], fill=c, outline=(0, 0, 0))
    for i, (x, y) in enumerate(pp):
        if not on[i]:
            r = 8; dr.ellipse([x - r, y - r, x + r, y + r], fill=(255, 20, 20), outline=(255, 255, 255), width=2)
            dr.line([x - 5, y - 5, x + 5, y + 5], fill=(255, 255, 255), width=2); dr.line([x - 5, y + 5, x + 5, y - 5], fill=(255, 255, 255), width=2)
    if len(miss_mids):
        for (x, y) in pr(miss_mids):
            r = 12; dr.ellipse([x - r, y - r, x + r, y + r], outline=(255, 40, 255), width=3)
    out = Image.new("RGB", (im.width, im.height + 134), (16, 16, 20)); od = ImageDraw.Draw(out)
    od.text((10, 8), "SP7d  %d POINTS, EACH GIVEN TO THE ORIGINAL FACE IT LIES ON - %s" % (len(P), ttl), fill=(255, 235, 120), font=K.F22); out.paste(im, (0, 40))
    if FID is not None:
        od.text((10, im.height + 48), "Each dot = one point on the original's own mesh, coloured by the original face it lies on. A face with NO dot is absorbed by its neighbours in", fill=(235, 235, 235), font=K.F16)
        od.text((10, im.height + 72), "skin-labels (PTS_BOX gives it one to keep it; PTS_DROP drops a face). White = the original wireframe. %d faces kept, %d with no point." % (len(kept), len(nopts)), fill=(235, 235, 235), font=K.F16)
    else:
        od.text((10, im.height + 48), "Each dot = one point of the voxel, coloured by the original face its projection lies in (within %.2f mm). RED = the voxel is off every original face" % ON_MM, fill=(235, 235, 235), font=K.F16)
        od.text((10, im.height + 72), "there (a changed area). White = the original wireframe (drawn over everything). %d faces kept, %d changed, %d with no point." % (len(kept), len(changed), len(nopts)), fill=(235, 235, 235), font=K.F16)
    od.text((10, im.height + 96), "MAGENTA RING = a reinsert-face edge whose original face got no ON point (%d face(s): %s) - it will get no face of its own." % (len(fr_miss), fr_miss[:8]), fill=(255, 140, 255), font=K.F16)
    _q = K.source_quality(Vu, F)
    try: K._stamp_if_defective(out, od, _q, 40)
    except Exception: pass
    out.save(path)
    if hasattr(R, "index_frame"): R.index_frame(path, fb, d, "SP7d " + ttl, quality=_q)
say("pictures SP7d_* written")
K.write_look("points", _frames, os.path.join(SK, "points1000.json"), {"points": len(P), "frame_faces_no_point": fr_miss,
             "restart_spots": [{"id": sp_["id"], "box": sp_["box"]} for sp_ in LOCKED], "kept_points": len(OLD)})
say("POINTS_LOOK.json: %d frames - after three failed tries `kit rebuild judge --what points` is required on THESE (the restart)" % len(_frames))
print("DONE", flush=True)

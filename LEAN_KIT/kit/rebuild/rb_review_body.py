# kit rebuild
import os, sys, time, json, numpy as np, Part
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
TAG = os.environ.get("LK_TAG", "")
sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sk_lib as K
T0 = time.time(); RUN = os.environ["RUN"]; OUT = os.environ.get("OUT_DIR") or os.path.join(RUN, "review_body"); os.makedirs(OUT, exist_ok=True); TAG = os.environ.get("TAG", "new")
WIN = [float(t) for t in os.environ["WIN"].split()]; M = 8.0
NEWP = os.environ.get("NEW", os.path.join(RUN, "body_new.brep")); f = Part.Shape(); f.importBrep(NEWP); fin = f.Solids[0]
# MeshPart
# open edges  RENDER DEFECTIVE
# REVIEW_BODY_quality.json
V, T, FID, MQ = K.piece_mesh(NEWP, fin, cache_dir=OUT, say=lambda m_: print(m_, flush=True)); V = np.asarray(V, float); T = np.asarray(T, int); FID = np.asarray(FID, int)
C = np.full((len(T), 3), (0.95, 0.6, 0.2)); QREC = {}; bb = fin.BoundBox; FB = (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax)
LEG = ["The new body opaque, smooth-shaded within each face (a crease between faces stays sharp); the quality line says how fine; a red RENDER DEFECTIVE banner across the frame = NO EVIDENCE."]
def frame(nm, d, fbox, head):
    path = os.path.join(OUT, "%s_%s.png" % (TAG, nm))
    K.view_meshes(R, path, [(V, T, FID, MQ, C)], d, fbox, 1400, "%s %s" % (TAG, nm), head, LEG)
    QREC[os.path.basename(path)] = K.frame_quality(MQ, fbox)
for nm, d in {"above": R.look(up=-1.0), "below": R.look(up=1.0), "iso": R.look(fwd=0.6, left=-0.5, up=-0.6), "iso_below": R.look(fwd=0.6, left=0.5, up=0.6)}.items():
    frame(nm, d, FB, "%s whole body %s" % (TAG, nm))
FR = (WIN[0] - M, WIN[1] + M, WIN[2] - M, WIN[3] + M, WIN[4], WIN[5])
for nm, d in {"region_above": R.look(fwd=0.4, left=0.3, up=-0.8), "region_below": R.look(fwd=0.4, left=-0.3, up=0.8), "region_aft": R.look(fwd=-0.9, left=0.3, up=-0.3), "region_side": R.look(left=-1.0, up=-0.2)}.items():
    frame(nm, d, FR, "%s region %s" % (TAG, nm))
json.dump({"frames": {k_: {kk: v for kk, v in q_.items() if kk != "crack_pts_in_frame"} for k_, q_ in QREC.items()},
           "mesh_quality": {k_: MQ.get(k_) for k_ in ("tris", "dev_mm", "ang_rad", "open_edges", "expected_open", "seams", "cracks", "gap_max_mm", "dev_p99_mm", "nang_p99_deg", "edge_tol_max", "defective_mesh", "why_mesh", "defective", "why", "how")},
           "shape": os.path.basename(NEWP), "md5": K.md5(NEWP)}, open(os.path.join(OUT, "REVIEW_BODY_quality.json"), "w", encoding="utf-8"), indent=1)
nd_ = sum(1 for q_ in QREC.values() if q_.get("defective"))
if nd_: print("RENDER DEFECTIVE: %d of %d frame(s) stamped - %s - they are NO EVIDENCE (the judge refuses the set)" % (nd_, len(QREC), MQ.get("why", "")), flush=True)
b = Part.Shape(); b.importBrep(os.environ["BODY"]); body = b.Solids[0]
VA, TA, _, _ = K.piece_mesh(os.environ["BODY"], body, cache_dir=OUT, say=lambda m_: print(m_, flush=True)); VA = np.asarray(VA, float); TA = np.asarray(TA, int)
def _clip_segs(segs, ax):
    segs = np.asarray(segs, float)
    if not len(segs): return segs
    au = 1 if ax == 0 else 0
    lo_, hi_ = (WIN[2] - M, WIN[3] + M) if ax == 0 else (WIN[0] - M, WIN[1] + M)
    u = segs[:, :, au]; segs = segs[(u.max(axis=1) >= lo_) & (u.min(axis=1) <= hi_)].copy()
    for a_, b_ in ((0, 1), (1, 0)):
        for bound_, side_ in ((lo_, -1.0), (hi_, 1.0)):
            ua = segs[:, a_, au]; ub = segs[:, b_, au]; out_ = (ua - bound_) * side_ > 0
            if out_.any():
                den_ = ub[out_] - ua[out_]; den_ = np.where(np.abs(den_) > 1e-12, den_, 1e-12); tt = ((bound_ - ua[out_]) / den_)[:, None]
                segs[out_, a_, :] = segs[out_, a_, :] + tt * (segs[out_, b_, :] - segs[out_, a_, :])
    return segs
def _st(env, lo, hi, n=6): return [float(t) for t in os.environ[env].split()] if os.environ.get(env) else [lo - 4.0, hi + 4.0] + [lo + (hi - lo) * (k + 0.5) / n for k in range(n)]
# UNCHANGED
SEC_TOL = float(os.environ.get("SEC_TOL", os.environ.get("SEAM_MAX", "0.15")) or 0.15); STATIONS = []
for ax, name, cs in ((1, "y", _st("STATIONS_Y", WIN[2], WIN[3])), (0, "x", _st("STATIONS_X", WIN[0], WIN[1]))):
    _ext = (float(min(VA[:, ax].min(), V[:, ax].min())) + 0.5, float(max(VA[:, ax].max(), V[:, ax].max())) - 0.5) if len(VA) and len(V) else None      # stations
    _drop = [c for c in cs if _ext and not (_ext[0] <= c <= _ext[1])]
    if _drop: print("   station(s) %s = %s lie outside the bodies (%s spans %.1f..%.1f) - not drawn (31bx R6 F11)" % (name, ["%+.0f" % c_ for c_ in _drop], name, _ext[0] - 0.5, _ext[1] + 0.5), flush=True)
    for c in [c_ for c_ in cs if c_ not in _drop]:
        t_st = time.time()
        sa = _clip_segs(R.section_segs(VA, TA, ax, c), ax); sb = _clip_segs(R.section_segs(V, T, ax, c), ax)
        au_, av_ = [a_ for a_ in (0, 1, 2) if a_ != ax]
        ma_ = R.match_segs(sa, sb, au_, av_, SEC_TOL); mb_ = R.match_segs(sb, sa, au_, av_, SEC_TOL)
        both_ = sb[mb_] if len(sb) else sb; old_only = sa[~ma_] if len(sa) else sa; new_only = sb[~mb_] if len(sb) else sb
        print("   station %s = %+.0f: %d segment(s) unchanged (on both bodies within %.2f mm), %d OLD only, %d NEW only (%.1f s)" % (name, c, int(mb_.sum()), SEC_TOL, len(old_only), len(new_only), time.time() - t_st), flush=True)
        STATIONS.append({"axis": name, "at": float(c), "unchanged": int(mb_.sum()), "old_only": int(len(old_only)), "new_only": int(len(new_only)), "tol_mm": SEC_TOL})
        R.draw_section(os.path.join(OUT, "%s_%s%+.0f.png" % (TAG, name, c)), [(both_, (90, 210, 110), 2), (old_only, (255, 215, 60), 3), (new_only, (80, 200, 255), 3)], ax,
                       "%s = %.0f   GREEN: unchanged (both bodies within %.2f mm)   YELLOW: old body only   BLUE: %s only" % (name, c, SEC_TOL, TAG), W=900, grid=10)
try:
    json.dump({"tag": TAG, "tol_mm": SEC_TOL, "stations": STATIONS}, open(os.path.join(OUT, "STATIONS_%s.json" % TAG), "w", encoding="utf-8"), indent=1)
    _out_ = [s_ for s_ in STATIONS if s_["at"] < WIN[2] or s_["at"] > WIN[3]] if True else []
    print("STATIONS: %d; outside the region's y range: %s" % (len(STATIONS), ", ".join("%s %+.0f: %d unchanged / %d old only / %d new only" % (s_["axis"], s_["at"], s_["unchanged"], s_["old_only"], s_["new_only"]) for s_ in STATIONS if s_["axis"] == "y" and (s_["at"] < WIN[2] or s_["at"] > WIN[3])) or "none"), flush=True)
except Exception as _ex: print("   the station record was not written: %s" % str(_ex)[:80], flush=True)
print("DONE -> %s (%.0fs)" % (OUT, time.time() - T0), flush=True)

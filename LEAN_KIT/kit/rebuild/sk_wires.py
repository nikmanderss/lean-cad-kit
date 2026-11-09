# skin-labels
# kit rebuild
# skin-frame  skin-build
# skin-frame  skin-frame
# corners.json  CORNERS_
# skin-features  features.json  FEATURES
# ORIGINAL
# skin-frame
# corners.json  over the
# CORNERS_
# FEATURES
import os, sys, json, time, shutil, hashlib, re as _re_w
if not globals().get("_SK_INNER"):      # 31br D3 (2026-10-29): a crash's TRACEBACK reaches the log
    import runpy as _rp3, traceback as _tb3
    try: _rp3.run_path(os.path.abspath(__file__), init_globals={"_SK_INNER": True}, run_name="__main__")
    except SystemExit: raise
    except BaseException:
        print("TRACEBACK (31br D3) - the crash's place:\n" + _tb3.format_exc(), flush=True); raise
    raise SystemExit(0)
import numpy as np
RUN = os.environ.get("RUN"); BODY = os.environ.get("BODY"); KIT_HOME = os.environ.get("KIT_HOME")
TOL_LINE = float(os.environ.get("TOL_LINE", "0.10")); TOL_ARC = float(os.environ.get("TOL_ARC", "0.10")); TOL_CUBIC = float(os.environ.get("TOL_CUBIC", "0.20"))
MAX_POLES = int(os.environ.get("MAX_POLES", "6")); GROW = os.environ.get("GROW", "1") == "1"; GROW_MAX = float(os.environ.get("GROW_MAX", "0.30"))
WIRE_PICS = os.environ.get("WIRE_PICS", "1") == "1"
LINES_P = os.environ.get("LINES", "").strip()
SHOW_NUMBERS = os.environ.get("SHOW_NUMBERS", "0") == "1"
TRACE_TUBE_MM = float(os.environ.get("TRACE_TUBE_MM", "2.0") or 0.0)
ADD_VIA_TOL = float(os.environ.get("ADD_VIA_TOL", "0.30") or 0.30)
import Part
from FreeCAD import Vector as V3
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
if not RUN or not BODY or not KIT_HOME:
    print("FAIL: RUN, BODY and KIT_HOME must be set (--set RUN=<job folder> --set BODY=<model of record>)", flush=True); raise SystemExit(1)
sys.path.insert(0, KIT_HOME); import kitlib_render as R
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sk_lib as K; K.need_window()
def num(fmt, *a): return (fmt % a) if SHOW_NUMBERS else ""
LINESPEC = {}; LINES_NET = None
if LINES_P:
    try:
        _raw_l = json.load(open(LINES_P, encoding="utf-8"))
        if not isinstance(_raw_l, dict): raise ValueError("not a json object {\"<chain>\": {\"kind\": ..., \"why\": ...}}")
        LINES_NET = _raw_l.get("_network_md5")       # LINES_carried.json
        LINESPEC = {k_: v_ for k_, v_ in _raw_l.items() if not str(k_).startswith("_")}
        bad_ = [k_ for k_, v_ in LINESPEC.items() if not str(k_).isdigit() or not isinstance(v_, dict) or str(v_.get("kind", "")).upper() not in ("LINE", "ARC", "CUBIC")]
        if bad_: raise ValueError("entries %s are not {\"<chain>\": {\"kind\": LINE|ARC|CUBIC, \"why\": ...}}" % bad_[:5])
        for v_ in LINESPEC.values(): v_["kind"] = str(v_["kind"]).upper()
        # the _add / _fillets SHAPES are checked here, in the first second
        for _i5, _a5 in enumerate(_raw_l.get("_add") or []):
            if not isinstance(_a5, dict) or _a5.get("face") is None or str(_a5.get("kind", "")).upper() not in ("LINE", "ARC", "CUBIC") or len(str(_a5.get("why", "")).strip()) < 3:
                raise ValueError("_add entry %d is not {\"face\": n, \"kind\": LINE|ARC|CUBIC, \"from\"/\"to\" or \"on\", \"why\": ...}: %s" % (_i5, str(_a5)[:120]))
            # 31br D5b
            # more poles than points
            # outside 4..8
            if _a5.get("poles") is not None:
                try: _p5 = int(_a5["poles"])
                except (TypeError, ValueError): raise ValueError("_add entry %d: \"poles\" is a whole number 4..8 (%r given) (31br D5b)" % (_i5, _a5.get("poles")))
                _nv5 = len(_a5.get("via") or []); _npt5 = _nv5 + 2
                if _p5 < 4 or _p5 > 8: raise ValueError("_add entry %d: \"poles\" %d is outside 4..8 (a cubic has 4 poles; the kit fits at most 8) (31br D5b)" % (_i5, _p5))
                if _a5.get("trace"): print("   LINES: _add entry %d: \"poles\" %d is ignored on a traced line (a trace interpolates its surface points) (31br D5b)" % (_i5, _p5), flush=True)
                elif _nv5 <= 2: print("   LINES: _add entry %d: \"poles\" %d is ignored - with %d via point(s) the line is interpolated exactly (a cubic through them; \"poles\" matters from three via points on) (31br D5b)" % (_i5, _p5, _nv5), flush=True)
                elif _p5 > _npt5: raise ValueError("_add entry %d (%s %s on face %s): \"poles\" %d with %d via points - more poles than points (%d = %d via + the two ends): the fit is underdetermined, the curve passes the points and swings between them (the agent's d19: 13.7 mm off the part, caught 72 s later by LINE_OFF_MAX). \"poles\" <= %d here (= an exact interpolation through the points); more shape needs more via points ON the surface, not more poles (31br D5b)"
                                                   % (_i5, str(_a5.get("role", "")).lower(), str(_a5.get("kind", "")).upper(), _a5.get("face"), _p5, _nv5, _npt5, _nv5, _npt5))
        for _i5, _f5 in enumerate(_raw_l.get("_fillets") or []):
            if not isinstance(_f5, dict): raise ValueError("_fillets entry %d is not an object: %s" % (_i5, str(_f5)[:120]))
            if isinstance(_f5.get("lines"), list) and len(_f5["lines"]) == 1 and _f5.get("line") is None:
                _f5["line"] = _f5["lines"][0]; del _f5["lines"]; print("   LINES: _fillets entry %d had \"lines\": [%s] - ONE member is \"line\": %s; taken as that (31br D5)" % (_i5, _f5["line"], _f5["line"]), flush=True)
            if _f5.get("line") is None and not (isinstance(_f5.get("lines"), list) and len(_f5["lines"]) >= 2): raise ValueError("_fillets entry %d names no line: a single blend is {\"line\": n, \"r\": R, \"why\": ...}, a chain {\"lines\": [n1, n2, ...], \"r\": R, \"why\": ...}: %s" % (_i5, str(_f5)[:120]))
            if not _f5.get("r") or float(_f5.get("r") or 0) <= 0: raise ValueError("_fillets entry %d needs \"r\" > 0: %s" % (_i5, str(_f5)[:120]))
            if len(str(_f5.get("why", "")).strip()) < 3: raise ValueError("_fillets entry %d carries no reason (\"why\"): %s" % (_i5, str(_f5)[:120]))
    except (OSError, ValueError, TypeError) as ex_:
        K._fail("FAIL: LINES %s: %s" % (LINES_P, ex_))
    nowhy_ = [k_ for k_, v_ in LINESPEC.items() if len(str(v_.get("why", "")).strip()) < 3]
    if nowhy_: K._fail("FAIL: LINES chain(s) %s carry no reason - every decided line says WHY (the client 2026-10-07: \"You must reason through the choices\")" % nowhy_[:8])
from scipy.spatial import cKDTree
from _busy import busy
T0 = time.time()
def say(*a): print("%5.0fs " % (time.time() - T0), *a, flush=True)
SK = K.SK; OUT = K.OUT; TAG = K.TAG
def P3(v): return np.array([v.X, v.Y, v.Z]) if hasattr(v, "X") else np.array([v.x, v.y, v.z])
NJ = json.load(open(os.path.join(SK, "network.json"))); CH = [c for c in NJ["chains"] if c.get("ok")]
FR = json.load(open(os.path.join(SK, "frame.json"))); FREC = FR["chains"]
PJ = json.load(open(os.path.join(SK, "patches.json")))["patches"]
src_brep = os.path.join(SK, "network_frame.brep"); raw_brep = os.path.join(SK, "network_frame_raw.brep")
# skin-frame  skin-frame
if (not os.path.isfile(raw_brep)) or os.path.getmtime(os.path.join(SK, "frame.json")) > os.path.getmtime(raw_brep) + 1.0:
    shutil.copy2(src_brep, raw_brep); say("skin-frame's network_frame.brep kept as network_frame_raw.brep")
nf = Part.Shape(); nf.importBrep(raw_brep); NE = nf.Edges
if len(NE) != len(CH) or len(FREC) != len(CH):
    K._fail("FAIL: network_frame_raw.brep (%d edges) / frame.json (%d chains) / network.json (%d ok chains) disagree - run skin-network and skin-frame again" % (len(NE), len(FREC), len(CH)))
body = Part.Shape(); body.importBrep(BODY); BF = body.Faces
Z = np.load(os.path.join(SK, "regions.npz")); Vu, F = Z["Vu"], Z["F"]
FID_W = np.asarray(Z["fid"]).astype(int) if "fid" in Z.files else None
Nr = np.cross(Vu[F[:, 1]] - Vu[F[:, 0]], Vu[F[:, 2]] - Vu[F[:, 0]])
vn = np.zeros_like(Vu)
for k in range(3): np.add.at(vn, F[:, k], Nr)
vn /= np.maximum(np.linalg.norm(vn, axis=1), 1e-12)[:, None]
kdv = cKDTree(Vu); kct = cKDTree(Vu[F].mean(1))
def outward(P):
    _, j = kdv.query(P, k=6, workers=-1); n = vn[j].mean(1); return n / np.maximum(np.linalg.norm(n, axis=1), 1e-12)[:, None]
wc_caps = Part.Shape(); wc_caps.importBrep(os.path.join(RUN, "wall_caps.brep")); FC_ = wc_caps.Faces
corner_pts = []; corner_key = {}
def _vid(v, b):
    p = np.array([v.X, v.Y, v.Z]); k_ = tuple(np.round(p, 4))
    if k_ not in corner_key: corner_key[k_] = len(corner_pts); corner_pts.append({"id": len(corner_pts), "xyz": [round(float(x), 5) for x in p], "caps": []})
    i_ = corner_key[k_]
    if b not in corner_pts[i_]["caps"]: corner_pts[i_]["caps"].append(b)
    return i_
cap_wall = []
for b_, f_ in enumerate(FC_):
    Pf_ = np.array([[v.X, v.Y, v.Z] for v in f_.Vertexes]); w_, _ = K.wall_of(Pf_); cap_wall.append(int(w_))
    for v in f_.Vertexes: _vid(v, b_)
for p_ in corner_pts:
    x_ = np.array(p_["xyz"]); p_["wall"] = int(np.argmin([abs(x_ @ n_ - c_) for n_, c_ in K.WALLS]))
json.dump({"corners": corner_pts, "cap_wall": cap_wall}, open(os.path.join(SK, "corners.json"), "w"), indent=1)
say("CORNERS: %d corners of the reinsert faces on %d cap face(s) (walls %s) -> skin\\corners.json (c<n> in RAILS)" % (len(corner_pts), len(FC_), sorted(set(cap_wall))))
# skin-network
# features.json
# skin-wires
# skin-network
# LINES_carried.json  _network_md5
CARRY_MM = float(os.environ.get("CARRY_MM", "3.0"))
CARRY_FIT = float(os.environ.get("CARRY_FIT", "1.0")); CARRY_REJ = []
NET_MD5 = K.md5(os.path.join(SK, "network.json"))
_fp0 = os.environ.get("FEATURES", "").strip() or os.path.join(SK, "features.json")
_fof0 = {}
if os.path.isfile(_fp0):
    try:
        for nm_, ids_ in json.load(open(_fp0, encoding="utf-8")).items():
            if str(nm_).startswith("_"): continue
            for x_ in ids_: _fof0.setdefault(int(x_), []).append(nm_)
    except (OSError, ValueError, TypeError, AttributeError):
        _fof0 = {}
_mf0 = {p_["grp"]: p_.get("face_src") for p_ in PJ if p_.get("mirror_of") is None and p_.get("grp") is not None}
def feat_sig(i):
    """the feature a skin face belongs to (its master's original face's feature; the original face id without a feature map)"""
    p_ = PJ[i]
    if p_["kind"] == "cap": return "CAP"
    f_ = _mf0.get(p_.get("grp"), p_.get("face_src"))
    if f_ is None: return "patch%d" % i
    fs_ = _fof0.get(int(f_))
    return fs_[-1] if fs_ else "f%d" % int(f_)
SIG = [sorted([feat_sig(int(c_["pair"][0])), feat_sig(int(c_["pair"][1]))]) for c_ in CH]
MID = [P3(NE[k_].discretize(Number=21)[10]) for k_ in range(len(CH))]
HAIRPIN_DEG = float(os.environ.get("HAIRPIN_DEG", "120") or 120); HAIRPIN_MM = float(os.environ.get("HAIRPIN_MM", "1.0") or 1.0); HAIRPIN_NEAR = 3.0
HAIRPIN_FOUND = []; _HP_RAW = {}
_SIMPLIFIED = False
def _hp_turn(S, m, w):
    """the chord turn at sample m of the polyline S: the chord ending at m against the chord starting at m, each of arc length w; None where the polyline ends inside either chord (a chain's
    end is a junction or a corner, never an apex of its own)"""
    seg = np.linalg.norm(np.diff(S, axis=0), axis=1)
    ia = m; acc = 0.0
    while ia > 0 and acc < w: acc += seg[ia - 1]; ia -= 1
    if acc < 0.7 * w: return None
    ib = m; acc = 0.0
    while ib < len(S) - 1 and acc < w: acc += seg[ib]; ib += 1
    if acc < 0.7 * w: return None
    u = S[m] - S[ia]; v = S[ib] - S[m]; nu = np.linalg.norm(u); nv = np.linalg.norm(v)
    if nu < 1e-9 or nv < 1e-9: return None
    return float(np.degrees(np.arccos(np.clip(float(u @ v) / (nu * nv), -1.0, 1.0))))
def _hp_near(P, q, snap):
    """the hairpin apex nearest the point P on the raw border chains of face q, or None: (chain, apex xyz, turn deg, the apex's distance from P) - only on a chain the end would snap to
    (its nearest raw sample within snap of P), the apex searched within HAIRPIN_NEAR of that sample along the chain"""
    best = None
    for k_, c_ in enumerate(CH):
        if q not in [int(x) for x in c_["pair"]] or FREC[k_]["kind"] == "wall_dropped": continue
        if k_ not in _HP_RAW:
            e0_ = NE[k_]; _HP_RAW[k_] = np.array([P3(x) for x in e0_.discretize(Number=max(25, int(e0_.Length / 0.1) + 1))])
        S_ = _HP_RAW[k_]; d_ = np.linalg.norm(S_ - P, axis=1); i_ = int(np.argmin(d_))
        if d_[i_] > snap: continue
        cum_ = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(S_, axis=0), axis=1))])
        for m_ in range(len(S_)):
            if abs(cum_[m_] - cum_[i_]) > HAIRPIN_NEAR: continue
            t_ = _hp_turn(S_, m_, HAIRPIN_MM)
            if t_ is None or t_ < HAIRPIN_DEG: continue
            dm_ = float(np.linalg.norm(S_[m_] - P))
            if best is None or t_ > best[2] + 1e-6 or (abs(t_ - best[2]) <= 1e-6 and dm_ < best[3]): best = (k_, S_[m_], t_, dm_)
    return best
def _hp_refuse(P, q, ai_, nm_, mir_, snap):
    """say (never refuse) a split's end that lies at a hairpin apex of face q's raw border, and record it (WIRES_LOOK hairpin_ends; the preview's verdict names it for a face it fails)"""
    h_ = _hp_near(np.asarray(P, float), int(q), snap)
    if h_ is None: return
    k_, X_, t_, dm_ = h_
    _jp = np.array([j_["pos"] for j_ in NJ["junctions"]], float) if NJ.get("junctions") else np.zeros((0, 3))
    nc_ = sorted(((float(np.linalg.norm(np.asarray(p_["xyz"], float) - X_)), int(p_["id"])) for p_ in corner_pts))[:3]
    nj_ = sorted(((float(np.linalg.norm(_jp[j_] - X_)), int(j_)) for j_ in range(len(_jp))))[:3]
    if any(h_.get("face") == int(q) and h_.get("entry") == ai_ and h_.get("end") == nm_ and bool(h_.get("mirrored")) == bool(mir_) for h_ in HAIRPIN_FOUND): return
    HAIRPIN_FOUND.append({"face": int(q), "entry": ai_, "end": nm_, "mirrored": bool(mir_), "chain": int(k_), "apex": [round(float(x), 3) for x in X_], "turn_deg": round(t_, 1), "apex_mm": round(dm_, 3),
                          "corners": [c_ for d_, c_ in nc_], "junctions": [j_ for d_, j_ in nj_]})
    say("   HAIRPIN at a split's end - %s (31bw A5b): _add split on face %d (entry %s%s): its '%s' end %s lies %.2f mm from the APEX of a HAIRPIN in border chain %d at (%.2f, %.2f, %.2f) - the raw border turns %.1f deg within %g mm there (HAIRPIN_DEG %g). "
        "The chain is drawn as TWO curves meeting at that apex - the apex kept as a corner of the border (rung V(...), pale cyan in WIRE_*) - so the split's end lands on it and the piece between the legs keeps its corner; before 31bw one smooth curve rounded the apex off (the agent's d14 / d19 lip, an 11 deg sliver). "
        "If the preview still fails the piece (a thin lip), end the split where a corner survives - a wall corner (nearest: %s) or a junction (nearest: %s) - or fold the hairpin's face into the feature (FEATURES, d19b)."
        % (("DRAWN PER LEG" if not _SIMPLIFIED else "found after the chains were drawn (a carried entry): the NEXT skin-wires run draws this chain per leg"), q, ai_, " mirrored" if mir_ else "", nm_, np.round(np.asarray(P, float), 2).tolist(), dm_, k_, X_[0], X_[1], X_[2], t_, HAIRPIN_MM, HAIRPIN_DEG,
           ", ".join("c%d (%.1f mm away)" % (c_, d_) for d_, c_ in nc_) or "none listed - CORNERS_*", ", ".join("j%d (%.1f mm away)" % (j_, d_) for d_, j_ in nj_) or "none"))
if LINES_P and (_raw_l.get("_add") or []) and LINES_NET == NET_MD5:
    _hp_md = os.path.join(SK, "MIRROR_DECISION.json"); _hp_mir = (json.load(open(_hp_md)).get("plane", "") if os.path.isfile(_hp_md) else "")
    _hp_MN, _hp_MC = (K.mirror_plane(_hp_mir) if _hp_mir else (None, None))
    _hp_grp = {}
    for _p in PJ:
        if _p["kind"] != "cap" and _p.get("grp") is not None: _hp_grp.setdefault(_p["grp"], []).append(_p["patch"])
    _hp_snap = float(os.environ.get("ADD_SNAP", "1.0") or 1.0)
    for _ai, _a in enumerate(_raw_l.get("_add") or []):
        if not isinstance(_a, dict) or str(_a.get("role", "")).lower() != "split": continue
        try: _q0 = int(_a.get("face"))
        except (TypeError, ValueError): continue
        if _q0 < 0 or _q0 >= len(PJ) or PJ[_q0]["kind"] == "cap": continue
        _sides = [(_q0, False)]
        if _hp_MN is not None:
            _g = PJ[_q0].get("grp"); _tw = [y for y in _hp_grp.get(_g, []) if y != _q0] if _g is not None else []
            _sides.append((_tw[0], True) if _tw else (_q0, True))
        for _nm in ("from", "to"):
            _sp = _a.get(_nm)
            if isinstance(_sp, str) and _sp[:1] in "cj" and _sp[1:].isdigit(): continue
            try: _P = np.array([float(x) for x in (_sp.split() if isinstance(_sp, str) else _sp)], float); assert _P.shape == (3,)
            except Exception: continue
            for _q, _m in _sides: _hp_refuse((K.reflect(_P[None, :], _hp_MN, _hp_MC)[0] if _m else _P), _q, _ai, _nm, _m, _hp_snap)
try:
    _prev = json.load(open(os.path.join(SK, "wire_simplify.json"), encoding="utf-8"))
except (OSError, ValueError):
    _prev = None
_prev_net = (_prev or {}).get("network_md5")
_PREV_CH = {int(c_["chain"]): c_ for c_ in ((_prev or {}).get("chains") or []) if c_.get("chain") is not None}
if LINES_NET and LINES_NET not in (NET_MD5, _prev_net):
    K._fail("FAIL: LINES %s was written for a network that is neither this one nor the last skin-wires run's - decide from this run's WIRE_* pictures "
            "(skin\\LINES_carried.json carries what still holds)" % LINES_P)
if _prev and _prev_net and _prev_net != NET_MD5:
    _base = {str(c_["chain"]): c_.get("dec") for c_ in (_prev.get("chains") or []) if c_.get("dec")}
    if LINES_P and LINES_NET != NET_MD5:
        _base = dict(LINESPEC)
    _pv = [{"chain": c_["chain"], "sig": c_.get("sig"), "mid": c_.get("mid"), "dec": _base.get(str(c_["chain"]))} for c_ in (_prev.get("chains") or [])]
    _cu = [{"chain": k_, "sig": SIG[k_], "mid": MID[k_].tolist()} for k_ in range(len(CH)) if FREC[k_]["kind"] != "wall_dropped"]
    _car, _todo = K.carry_lines(_pv, _cu, CARRY_MM)
    if LINES_P and LINES_NET == NET_MD5:
        _car.update(LINESPEC)
    LINESPEC = _car
    with open(os.path.join(SK, "LINES_carried.json"), "w", encoding="utf-8") as _fh:
        json.dump(dict({"_network_md5": NET_MD5, "_carried_from": _prev.get("tag")}, **LINESPEC), _fh, indent=1)
    say("LINES CARRIED: the chains were renumbered since the last skin-wires run (%s) - %d decision(s) carried to the new numbers (the same two features, "
        "the nearest middle within %g mm) -> skin\\LINES_carried.json" % (_prev.get("tag"), len(_car), CARRY_MM))
    if _todo:
        say("TO DECIDE - %d new line(s) with no earlier decision (their numbers are on this run's WIRE_* pictures): add each to skin\\LINES_carried.json with its "
            "reason, then skin-wires --set LINES=<that file>:" % len(_todo))
        for k_, why_ in _todo[:60]: say("   chain %3s  %s" % (k_, why_))
elif LINES_P and _prev and _prev_net == NET_MD5 and LINES_NET in (None, NET_MD5):
    # CARRY=drop
    _miss8 = {str(c_["chain"]): c_["dec"] for c_ in (_prev.get("chains") or []) if c_.get("dec") and str(c_["chain"]) not in LINESPEC and int(c_["chain"]) < len(CH) and FREC[int(c_["chain"])]["kind"] != "wall_dropped"}
    if _miss8:
        if (os.environ.get("CARRY", "").strip().lower() == "drop"): say("LINES: %d decision(s) of the last run (%s) are not in %s and CARRY=drop - DROPPED on purpose: chains %s" % (len(_miss8), _prev.get("tag"), os.path.basename(LINES_P), sorted(int(k_) for k_ in _miss8)))
        else:
            for k_, d_ in _miss8.items(): LINESPEC[k_] = dict(d_)
            say("LINES CARRIED on the same network (31br D8): %d decision(s) of the last run (%s) are not in %s - carried in, since a decision survives (L130): chains %s. To drop them on purpose: --set CARRY=drop" % (len(_miss8), _prev.get("tag"), os.path.basename(LINES_P), sorted(int(k_) for k_ in _miss8)))
elif not LINES_P and _prev and _prev_net == NET_MD5:
    LINESPEC = {str(c_["chain"]): c_["dec"] for c_ in (_prev.get("chains") or []) if c_.get("dec")}
    if LINESPEC: say("LINES: none given - the %d decision(s) of the last run (%s) stand (the same numbering)" % (len(LINESPEC), _prev.get("tag")))
def surf_proj(fi):
    S = BF[fi].Surface
    def pr(x):
        u, v = S.parameter(V3(*x)); q = S.value(u, v); return np.array([q.x, q.y, q.z])
    return pr
PROJ = {i: surf_proj(p["face"]) for i, p in enumerate(PJ) if p["kind"] == "orig" and p.get("face") is not None}
def alt_project(x, prs, it=40):
    for _ in range(it):
        x0 = x.copy()
        for pr in prs: x = pr(x)
        if np.linalg.norm(x - x0) < 1e-8: break
    return x
def chord_t(S):
    d = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(S, axis=0), axis=1))]); return d / max(d[-1], 1e-12)
def seg_dist(S, A, B):
    AB = B - A; t = np.clip((S - A) @ AB / max(AB @ AB, 1e-30), 0, 1); return np.linalg.norm(S - (A + t[:, None] * AB), axis=1)
def fit_arc(S):
    """one circular arc through both ends: the border's best plane, the centre on the ends' bisector in it (1-D least squares)"""
    A, B = S[0], S[-1]; hl = np.linalg.norm(B - A)
    if hl < 1e-6: return None, None
    c0 = S.mean(0); _, _, vt = np.linalg.svd(S - c0); nrm = vt[2]
    m = 0.5 * (A + B); ab = (B - A) / hl; w = np.cross(nrm, ab); w /= max(np.linalg.norm(w), 1e-12)
    def cost(h):
        c = m + h * w; r = np.linalg.norm(A - c); return np.sum((np.linalg.norm(S - c, axis=1) - r) ** 2)
    hs = np.concatenate([-np.logspace(-3, 3, 240)[::-1] * hl, np.logspace(-3, 3, 240) * hl])
    i = int(np.argmin([cost(x) for x in hs])); lo, hi = hs[max(i - 1, 0)], hs[min(i + 1, len(hs) - 1)]
    for _ in range(80):
        a1 = lo + 0.382 * (hi - lo); a2 = lo + 0.618 * (hi - lo)
        if cost(a1) < cost(a2): hi = a2
        else: lo = a1
    h = 0.5 * (lo + hi); c = m + h * w; r = np.linalg.norm(A - c)
    mid = S[len(S) // 2] - c; mid -= (mid @ nrm) * nrm; M = c + r * mid / max(np.linalg.norm(mid), 1e-12)
    rel = S - c; inpl = rel - (rel @ nrm)[:, None] * nrm
    dev = np.sqrt((np.linalg.norm(inpl, axis=1) - r) ** 2 + (rel @ nrm) ** 2)
    return (A, M, B, c, r, nrm), dev
def basis_matrix(t, npoles, deg):
    """B-spline basis (uniform open knots) at t, numpy Cox-de Boor"""
    nint = npoles - deg - 1
    U = np.concatenate([np.zeros(deg + 1), np.linspace(0, 1, nint + 2)[1:-1], np.ones(deg + 1)])
    t = np.clip(np.asarray(t, float), 0, 1)
    N = np.zeros((len(t), len(U) - 1))
    for i in range(len(U) - 1): N[:, i] = ((t >= U[i]) & (t < U[i + 1])).astype(float)
    last = int(np.max(np.nonzero(U[:-1] < U[1:])[0])); N[t >= 1.0, :] = 0.0; N[t >= 1.0, last] = 1.0
    for p in range(1, deg + 1):
        Nn = np.zeros((len(t), len(U) - 1 - p))
        for i in range(len(U) - 1 - p):
            d1 = U[i + p] - U[i]; d2 = U[i + p + 1] - U[i + 1]
            a = (t - U[i]) / d1 * N[:, i] if d1 > 0 else 0.0
            b = (U[i + p + 1] - t) / d2 * N[:, i + 1] if d2 > 0 else 0.0
            Nn[:, i] = a + b
        N = Nn
    mults = [deg + 1] + [1] * nint + [deg + 1]; knots = list(np.linspace(0, 1, nint + 2))
    return N, mults, knots
def fit_bspline(S, npoles, T=None, it=8):
    """one curve: degree 3, npoles poles, uniform open knots, ends pinned; least squares with parameter correction"""
    A, B = S[0], S[-1]; deg = min(3, npoles - 1); t = chord_t(S) if T is None else np.asarray(T, float).copy()
    tt = np.linspace(0, 1, 1500)
    for _ in range(it):
        Bm, mults, knots = basis_matrix(t, npoles, deg)
        rhs = S - Bm[:, :1] * A[None, :] - Bm[:, -1:] * B[None, :]
        Pin, *_ = np.linalg.lstsq(Bm[:, 1:-1], rhs, rcond=None); P = np.vstack([A, Pin, B])
        Cd = basis_matrix(tt, npoles, deg)[0] @ P
        _, j = cKDTree(Cd).query(S); t = tt[j]; t[0] = 0.0; t[-1] = 1.0
    C = basis_matrix(t, npoles, deg)[0] @ P
    c = Part.BSplineCurve(); c.buildFromPolesMultsKnots([V3(*p) for p in P], mults, knots, False, deg)
    return c, P, np.linalg.norm(S - C, axis=1), t, C
def grow_fit(S, npoles):
    """GROW: the cubic pushed outward until no border point lies outside it (signed along the voxel's outward normal), <= GROW_MAX"""
    n = outward(S); shift = np.zeros(len(S))
    c, P, dev, t, C = fit_bspline(S, npoles)
    for _ in range(10):
        d = ((S - C) * n).sum(1); d[0] = d[-1] = 0.0
        if d.max() <= 0.01: break
        shift = np.minimum(shift + np.clip(d, 0, None), GROW_MAX)
        Tg = S + shift[:, None] * n; Tg[0] = S[0]; Tg[-1] = S[-1]
        c, P, _, t, C = fit_bspline(Tg, npoles, T=t)
    dev = np.linalg.norm(S - C, axis=1); sgn = ((S - C) * n).sum(1)
    return c, P, dev, float(max(0.0, -sgn.min())), float(max(0.0, sgn.max()))
def inflections(P):
    """sign changes of the control polygon's turning (a single-curve border has none)"""
    if P is None or len(P) < 4: return 0
    d = np.diff(P, axis=0); cr = np.cross(d[:-1], d[1:]); nn = np.linalg.norm(cr, axis=1)
    if nn.max() < 1e-12: return 0
    ref = cr[np.argmax(nn)]; s = cr @ ref; s = np.sign(s[np.abs(s) > 1e-6 * np.abs(s).max()])
    return int((np.diff(s) != 0).sum()) if len(s) > 1 else 0
SMOOTH_DEG = float(os.environ.get("SMOOTH_DEG", "20")); TOL_SMOOTH = float(os.environ.get("TOL_SMOOTH", "1.0"))
_pz = np.load(os.path.join(SK, "patches.npz")); _pid = _pz["patch"]
_Nn = Nr / np.maximum(np.linalg.norm(Nr, axis=1), 1e-12)[:, None]
_Et = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); _Es = np.sort(_Et, 1); _tri = np.tile(np.arange(len(F)), 3)
_o = np.lexsort((_Es[:, 1], _Es[:, 0])); _Es = _Es[_o]; _tri = _tri[_o]; _same = np.all(_Es[1:] == _Es[:-1], axis=1)
_ta = _tri[:-1][_same]; _tb = _tri[1:][_same]; _m = _pid[_ta] != _pid[_tb]
_dih = np.degrees(np.arccos(np.clip((_Nn[_ta[_m]] * _Nn[_tb[_m]]).sum(1), -1, 1)))
_pp = np.sort(np.stack([_pid[_ta[_m]], _pid[_tb[_m]]], 1), 1)
PAIR_DIH = {}
for (a_, b_), d_ in zip(map(tuple, _pp), _dih): PAIR_DIH.setdefault((int(a_), int(b_)), []).append(d_)
PAIR_DIH = {k: float(np.percentile(v, 50)) for k, v in PAIR_DIH.items()}
def is_smooth(p, q): return PAIR_DIH.get((min(p, q), max(p, q)), 999.0) <= SMOOTH_DEG
# ORIGINAL
# skin-build
# wires_demote.json  skin-build
ON_TOL = float(os.environ.get("ON_TOL", "0.01"))
JMOVE_MAX = float(os.environ.get("JMOVE_MAX", "0.5"))   # does not reach
DEMOTE = {}; _DEMREQ = {}
_FAR_SAID = set()
def _reaching(k, p, q, S):
    """31bo: the original surfaces of p / q that REACH this chain (the median distance of its samples to the surface within JMOVE_MAX); a surface that
    does not (skin-network recorded it as far_faces, or it is measured here) is left out - laying a chain onto a surface beyond its own extent slid
    the agent's b13 chain 112 into a hairpin and the crossing re-make never returned"""
    far_ = set(int(x_) for x_ in (CH[k].get("far_faces") or []))
    out = []
    for x_ in (p, q):
        if x_ not in PROJ: continue
        if x_ in far_: continue
        try:
            sub_ = S[:: max(1, len(S) // 16)]; d_ = float(np.median([np.linalg.norm(PROJ[x_](s_.copy()) - s_) for s_ in sub_]))
        except Exception: d_ = 9e9
        if d_ > JMOVE_MAX:
            far_.add(x_)
            if (k, x_) not in _FAR_SAID: _FAR_SAID.add((k, x_)); say("   chain %d: the original surface of face %d is %.2f mm from this border (over JMOVE_MAX %g) - it does not reach it; the line is not laid onto it" % (k, x_, d_, JMOVE_MAX))
            continue
        out.append(PROJ[x_])
    return out
def _twins(x):
    g_ = PJ[x].get("grp")
    return [y_ for y_, p_ in enumerate(PJ) if g_ is not None and p_.get("grp") == g_ and y_ != x and p_["kind"] != "cap"]
def _demote(req):
    """apply the requested demotions (a face and its twins leave their original surface); returns the faces newly demoted"""
    new_ = set()
    for x_, why_ in req.items():
        for y_ in [x_] + _twins(x_):
            if y_ in PROJ and y_ not in DEMOTE:
                DEMOTE[y_] = why_; PROJ.pop(y_, None); new_.add(y_)
    return new_
def _fit_open(k, S, strict, rec, prs, p, q, L, tl, ta_, tc, mp_, grow):
    """the open chain's fit - the decided kind or the ladder (line, arc, cubic, more poles), laid back on an original surface where one reaches; the body of
    simplify_chain since 31as, extracted in 31bw A5b so a chain with a split's decided end at a hairpin apex is fitted PER LEG (each leg its own simple curve,
    the apex kept). Returns (curve, poles, rung, dev_max, via, grow_out, cut_in); rec takes the fit's notes (decided, carry, on, proj_shift, on_dev, demote_asked)."""
    A, B = S[0].copy(), S[-1].copy()
    both_fitted = not prs
    P = None; grow_out = 0.0; cut_in = 0.0; rung = None
    ldev = seg_dist(S, A, B)
    dec = LINESPEC.get(str(k))
    if dec and strict == 0 and "[carried from chain" in str(dec.get("why", "")):
        _fit = None
        try:
            import re as _re6
            # UNCHANGED
            _oc = _PREV_CH.get(int(k)) if _prev_net == NET_MD5 else _PREV_CH.get(int(_re6.findall(r"\[carried from chain (\d+)\]", str(dec.get("why", "")))[-1]))
            if _oc is not None and not _oc.get("carry_rejected") and abs(float(_oc.get("length") or -9.0) - L) <= 0.05 and float(np.linalg.norm(np.asarray(_oc.get("mid"), float) - MID[k])) <= 0.05: _fit = -1.0
        except Exception: pass
        if _fit is None and dec["kind"] == "LINE": _fit = float(ldev.max())
        elif _fit is None and dec["kind"] == "ARC":
            _ap, _ad = fit_arc(S); _fit = float(_ad.max()) if _ap is not None else 9e9
        if _fit is not None and _fit > CARRY_FIT:
            rec["carry_rejected"] = "carried %s does not fit this chain (%.2f mm off, CARRY_FIT %.2f) - TO DECIDE" % (dec["kind"], _fit, CARRY_FIT)
            CARRY_REJ.append((k, dec["kind"], _fit)); dec = None
    if dec and strict > 0:      # recorded
        rec["dec_set_aside"] = "made again tighter after a crossing (strict %d): the decision %s is set aside - drawn by the ladder (move the crossing: a split, or the neighbour's line)" % (strict, dec.get("kind"))
        say("   chain %d: your decision %s is SET ASIDE - %s (31bx R6 F2)" % (k, dec.get("kind"), rec["dec_set_aside"]))
    if dec and strict == 0:
        rec["decided"] = dec.get("why", "")
        if dec["kind"] == "LINE": rung = "LINE"; cv = Part.LineSegment(V3(*A), V3(*B)); dmax = float(ldev.max())
        elif dec["kind"] == "ARC":
            apar, adev = fit_arc(S)
            if apar is not None: rung = "ARC"; cv = Part.Arc(V3(*apar[0]), V3(*apar[1]), V3(*apar[2])); dmax = float(adev.max())
        if rung is None:
            cv, P, dev, _, _ = fit_bspline(S, 4); rung = "CUBIC"; dmax = float(dev.max())
        if dec.get("on"):
            prs_on = [surf_proj(int(fi)) for fi in dec["on"]]
            C_ = np.array([P3(x) for x in cv.toShape().discretize(Number=max(40, int(L / 0.2) + 1))])
            Cp_ = np.array([alt_project(x.copy(), prs_on) for x in C_]); Cp_[0] = A; Cp_[-1] = B
            cv, P, _, _, _ = fit_bspline(Cp_, 4); rung = "CUBIC"; rec["on"] = dec["on"]
    if rung is None and ldev.max() <= tl:
        rung = "LINE"; cv = Part.LineSegment(V3(*A), V3(*B)); dmax = float(ldev.max())
    if rung is None:
        apar, adev = fit_arc(S)
        if apar is not None and adev.max() <= ta_:
            rung = "ARC"; cv = Part.Arc(V3(*apar[0]), V3(*apar[1]), V3(*apar[2])); dmax = float(adev.max())
    if rung is None:
        best = None
        for npl in range(4, mp_ + 1):
            if both_fitted and grow: bc, P_, dev, go, ci = grow_fit(S, npl)
            else: bc, P_, dev, _, _ = fit_bspline(S, npl); go = ci = 0.0
            best = (npl, bc, P_, dev, go, ci)
            if dev.max() <= tc + (GROW_MAX if (both_fitted and grow) else 0.0): break
        npl, cv, P, dev, grow_out, cut_in = best
        rung = "CUBIC" if npl == 4 else "MULTI%d" % npl; dmax = float(dev.max())
    via = "free"
    if prs:
        m = max(40, int(L / 0.2) + 1)
        C = np.array([P3(x) for x in cv.toShape().discretize(Number=m)])
        Cp = np.array([alt_project(x.copy(), prs) for x in C]); Cp[0] = A; Cp[-1] = B
        _kp = [0]
        for _i in range(1, len(Cp)):
            if np.linalg.norm(Cp[_i] - Cp[_kp[-1]]) > 1e-4: _kp.append(_i)
        if _kp[-1] != len(Cp) - 1: _kp[-1] = len(Cp) - 1
        if len(_kp) >= 4: Cp = Cp[_kp]; C = C[_kp]
        dproj = float(np.linalg.norm(Cp - C, axis=1).max()); rec["proj_shift"] = round(dproj, 4)
        if dproj > 1e-5 and dec and strict == 0:
            cv1, P1, dev1, _, _ = fit_bspline(Cp, 4); on_dev = float(dev1.max()); rec["on_dev"] = round(on_dev, 4)
            if on_dev <= ON_TOL:
                cv = cv1; P = P1; via = "on %s, one span" % ("both original surfaces" if len(prs) == 2 else "the original surface"); rung = rung + "+ON_ORIG"
            else:
                for x_ in (p, q):
                    if x_ in PROJ:
                        _DEMREQ.setdefault(x_, "decided line %d (%s) is not one simple curve on its original surface" % (k, dec["kind"]))
                rec["demote_asked"] = True
        elif dproj > 1e-5:
            bs = Part.BSplineCurve()
            bs.approximate(Points=[V3(*x) for x in Cp], DegMin=3, DegMax=3, Tolerance=0.005, Continuity="C2", ParamType="ChordLength")
            cv = bs; via = "on %s" % ("both original surfaces" if len(prs) == 2 else "the original surface"); rung = rung + "+ON_ORIG"
    return cv, P, rung, dmax, via, grow_out, cut_in
def _apex_legs(k, S):
    """31bw A5b: the indices of S (the chain's polyline) where a split's DECIDED end lies at a hairpin apex of chain k (HAIRPIN_FOUND - the read's check): the chain is drawn per leg
    there, the apex kept as a corner. An apex under 0.5 mm from an end is the end (a junction already); apexes within three samples are one."""
    out = []
    for h_ in HAIRPIN_FOUND:
        if int(h_.get("chain", -1)) != int(k): continue
        X_ = np.asarray(h_["apex"], float); d_ = np.linalg.norm(S - X_, axis=1); m_ = int(np.argmin(d_))
        if d_[m_] > 0.5: continue
        cum_ = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(S, axis=0), axis=1))])
        if cum_[m_] < 0.5 or cum_[-1] - cum_[m_] < 0.5: continue
        if any(abs(m_ - o_) <= 3 for o_ in out): continue
        out.append(m_)
    return sorted(out)
def simplify_chain(k, strict=0):
    c = CH[k]; fr = FREC[k]; e0 = NE[k]
    if fr["kind"] == "wall_dropped": return e0, {"chain": k, "rung": "WALL_DROPPED", "sig": SIG[k]}
    p, q = [int(x) for x in c["pair"]]; kinds = (PJ[p]["kind"], PJ[q]["kind"])
    L = e0.Length; n = max(25, int(L / 0.1) + 1)
    S = np.array([P3(x) for x in e0.discretize(Number=n)])
    prs = _reaching(k, p, q, S)
    closed = bool(c.get("closed")) or bool(np.linalg.norm(S[0] - S[-1]) < 1e-6)
    if not closed: S = _shift_ends(S)
    rec = {"chain": k, "pair": [p, q], "kinds": list(kinds), "length": round(L, 3), "closed": closed, "raw": fr["kind"], "strict": strict,
           "sig": SIG[k], "mid": [round(float(v), 3) for v in MID[k]], "dec": LINESPEC.get(str(k))}
    if strict >= 2:
        rec.update({"rung": "RAW", "via": "skin-frame's own edge (a simplified one crossed a neighbour)", "dev_max": 0.0, "poles": 0, "inflections": 0})
        e0a, e0b = P3(e0.Vertexes[0].Point), P3(e0.Vertexes[-1].Point)
        if closed or (np.linalg.norm(e0a - S[0]) < 1e-7 and np.linalg.norm(e0b - S[-1]) < 1e-7): return e0, rec
        bs_ = Part.BSplineCurve()
        bs_.approximate(Points=[V3(*x) for x in S], DegMin=3, DegMax=3, Tolerance=0.002, Continuity="C2", ParamType="ChordLength")
        return bs_.toShape(), rec
    smooth = is_smooth(p, q); rec["smooth"] = smooth; rec["dihedral_p50"] = round(PAIR_DIH.get((min(p, q), max(p, q)), -1.0), 1)
    tl, ta_, tc = (TOL_LINE, TOL_ARC, TOL_CUBIC) if not smooth else (TOL_SMOOTH, TOL_SMOOTH, TOL_SMOOTH)
    if strict == 1: tl, ta_, tc = tl / 3, ta_ / 3, tc / 3
    mp_ = MAX_POLES if strict == 0 else 12; grow = GROW and strict == 0 and not smooth
    if closed:
        pts = S[:-1]; c0 = pts.mean(0); _, _, vt = np.linalg.svd(pts - c0); nrm = vt[2]
        rel = pts - c0; r_ = np.linalg.norm(rel - (rel @ nrm)[:, None] * nrm, axis=1); devc = np.abs(r_ - r_.mean()) + np.abs(rel @ nrm)
        if devc.max() <= ta_ and not prs:
            e = Part.Circle(V3(*c0), V3(*nrm), float(r_.mean())).toShape(); rung = "CIRCLE"; dmax = float(devc.max())
        else:
            bs = Part.BSplineCurve(); bs.approximate(Points=[V3(*x) for x in S], DegMin=3, DegMax=3, Tolerance=tc, Continuity="C2")
            e = bs.toShape(); rung = "CLOSED_SPLINE"; dmax = tc
        rec.update({"rung": rung, "dev_max": round(dmax, 4), "poles": 0, "inflections": 0})
        if rec.get("dec"):      # recorded
            rec["dec_set_aside"] = "a CLOSED chain takes no LINE / ARC / CUBIC decision - drawn as %s; split it with an _add line to decide its parts" % rung
            say("   chain %d: your decision %s is SET ASIDE - %s (31bx R6 F2)" % (k, (rec["dec"] or {}).get("kind"), rec["dec_set_aside"]))
        return e, rec
    A, B = S[0].copy(), S[-1].copy()
    legs_ = _apex_legs(k, S) if strict < 2 else []
    if not legs_:
        cv, P, rung, dmax, via, grow_out, cut_in = _fit_open(k, S, strict, rec, prs, p, q, L, tl, ta_, tc, mp_, grow)
    else:
        cuts_ = [0] + legs_ + [len(S) - 1]; parts_ = []; legrecs_ = []
        for i0_, i1_ in zip(cuts_[:-1], cuts_[1:]):
            Sx = S[i0_:i1_ + 1].copy(); Lx = float(np.linalg.norm(np.diff(Sx, axis=0), axis=1).sum())
            cvx, Px, rungx, dmaxx, viax, gox, cix = _fit_open(k, Sx, strict, rec, prs, p, q, Lx, tl, ta_, tc, mp_, grow)
            parts_.append(cvx); legrecs_.append({"rung": rungx, "dev_max": round(float(dmaxx), 4), "length": round(Lx, 3), "via": viax,
                                                  "poles": (len(cvx.getPoles()) if hasattr(cvx, "getPoles") else (2 if str(rungx).startswith("LINE") else 3))})
        bs_ = parts_[0] if isinstance(parts_[0], Part.BSplineCurve) else parts_[0].toBSpline()
        for cvx in parts_[1:]:
            nx_ = cvx if isinstance(cvx, Part.BSplineCurve) else cvx.toBSpline()
            if not bs_.join(nx_): K._fail("FAIL: chain %d: its legs at the hairpin apex could not be joined into one edge (31bw A5b)" % k)
        cv = bs_; P = None; rung = "V(%s)" % "+".join(r_["rung"].split("+")[0] for r_ in legrecs_); dmax = max(r_["dev_max"] for r_ in legrecs_)
        via = "per leg at a split's decided end, the apex kept (31bw A5b)"; grow_out = cut_in = 0.0
        rec["legs"] = legrecs_; rec["apex"] = [[round(float(v), 3) for v in S[m_]] for m_ in legs_]
    try:
        e = cv.toShape()
    except Exception as ex:
        K._fail("FAIL: chain %d: the simplified curve made no edge (%s)" % (k, str(ex)[:80]))
    ea, eb = P3(e.Vertexes[0].Point), P3(e.Vertexes[-1].Point)
    ok_ends = (np.linalg.norm(ea - A) < 1e-6 and np.linalg.norm(eb - B) < 1e-6) or (np.linalg.norm(ea - B) < 1e-6 and np.linalg.norm(eb - A) < 1e-6)
    if not ok_ends: K._fail("FAIL: chain %d: the simplified edge's ends moved (%.2e / %.2e mm)" % (k, np.linalg.norm(ea - A), np.linalg.norm(eb - B)))
    npoles = len(cv.getPoles()) if hasattr(cv, "getPoles") else (2 if rung.startswith("LINE") else 3)
    rec.update({"rung": rung, "via": via, "dev_max": round(dmax, 4), "poles": npoles, "grow_out": round(grow_out, 4), "cut_in": round(cut_in, 4),
                "inflections": inflections(P)})
    return e, rec
_md0 = os.path.join(SK, "MIRROR_DECISION.json"); _mir0 = json.load(open(_md0)).get("plane", "") if os.path.isfile(_md0) else ""
try: _master0 = (json.load(open(os.path.join(SK, "patches_labels.json"), encoding="utf-8")).get("mirror") or {}).get("master", "-")
except Exception: _master0 = "-"
MSIDE_ = 1.0 if _master0 == "+" else -1.0
JMOVE = {}
def _jk(x): return tuple(np.round(np.asarray(x, float), 4))
if _mir0:
    MN0, MC0 = K.mirror_plane(_mir0)
    ends_ = {}
    for k in range(len(CH)):
        if FREC[k]["kind"] == "wall_dropped": continue
        for v_ in (NE[k].Vertexes[0], NE[k].Vertexes[-1]): ends_[_jk(P3(v_.Point))] = P3(v_.Point)
    keys_ = list(ends_.keys()); pts_ = np.array([ends_[x] for x in keys_])
    wd_ = K.wall_dist(pts_); kd_ = cKDTree(pts_); nmv = 0; mx_ = 0.0
    for i_, (kk_, x_) in enumerate(zip(keys_, pts_)):
        if wd_[i_] < 1e-3: continue
        rx = K.reflect(x_[None, :], MN0, MC0)[0]; d_, j_ = kd_.query(rx)
        if d_ > 0.6: continue
        tgt = 0.5 * (x_ + K.reflect(pts_[j_][None, :], MN0, MC0)[0]) if j_ != i_ else x_ - (x_ @ MN0 - MC0) * MN0
        if np.linalg.norm(tgt - x_) > 1e-7: JMOVE[kk_] = tgt; nmv += 1; mx_ = max(mx_, float(np.linalg.norm(tgt - x_)))
    say("SYMMETRIC JUNCTIONS across %s: %d interior junction(s) set to the mean of themselves and their mirror partner%s" % (_mir0, nmv, num(" (moved up to %.3f mm)", mx_)))
_JK = list(JMOVE.keys()); _JKD = cKDTree(np.array(_JK)) if _JK else None
def _jmove(x):
    """the junction's new place, looked up by distance (1e-3 mm), never by rounded key: two chains' copies of one junction can round apart"""
    if _JKD is None: return None
    d_, i_ = _JKD.query(np.asarray(x, float))
    return JMOVE[_JK[i_]] if d_ < 1e-3 else None
RAILS_P = os.environ.get("RAILS", "").strip(); RAILS = []
if RAILS_P:
    try:
        RAILS = json.load(open(RAILS_P, encoding="utf-8"))
        if not isinstance(RAILS, list) or not all(isinstance(r_, dict) and r_.get("a") and r_.get("b") and r_.get("has") for r_ in RAILS):
            raise ValueError("not [{\"name\", \"a\", \"b\", \"has\": [features], \"why\"}]")
    except (OSError, ValueError) as ex_:
        K._fail("FAIL: RAILS %s: %s" % (RAILS_P, ex_))
    nowhy_ = [r_.get("name") for r_ in RAILS if len(str(r_.get("why", "")).strip()) < 3]
    if nowhy_: K._fail("FAIL: RAILS %s carry no reason - every rail says WHY it is one straight line" % nowhy_)
if RAILS:
    FEAT_P = os.environ.get("FEATURES", "").strip() or os.path.join(SK, "features.json")
    if not os.path.isfile(FEAT_P):
        K._fail("FAIL: RAILS name features and there is no feature map - kit rebuild skin-features --set FEATURES=<json> records skin\\features.json (or --set FEATURES=<json> here)")
    FM_ = json.load(open(FEAT_P, encoding="utf-8")); f_of_ = {}
    for nm_, ids_ in FM_.items():
        if str(nm_).startswith("_"): continue
        for x_ in ids_: f_of_.setdefault(int(x_), []).append(nm_)
    mf_ = {p_["grp"]: p_.get("face_src") for p_ in PJ if p_.get("mirror_of") is None and p_.get("grp") is not None}
    def featp(i):
        p_ = PJ[i]
        if p_["kind"] == "cap": return "CAP"
        f_ = mf_.get(p_.get("grp"), p_.get("face_src")); fs_ = f_of_.get(int(f_), ["?"]) if f_ is not None else ["?"]
        return fs_[0] if len(fs_) == 1 else (fs_[-1])
    CORNERS_ = {p_["id"]: np.array(p_["xyz"], float) for p_ in json.load(open(os.path.join(SK, "corners.json")))["corners"]}
    jfeat = {}
    for k in range(len(CH)):
        if FREC[k]["kind"] == "wall_dropped": continue
        fa_, fb_ = featp(int(CH[k]["pair"][0])), featp(int(CH[k]["pair"][1]))
        for v_ in (NE[k].Vertexes[0], NE[k].Vertexes[-1]):
            x0_ = P3(v_.Point); xm_ = _jmove(x0_); x_ = x0_ if xm_ is None else xm_
            key_ = _jk(x0_); jfeat.setdefault(key_, [x0_, x_, set(), []]); jfeat[key_][2].update((fa_, fb_)); jfeat[key_][3].append((fa_, fb_))
    SIDES_ = (-1.0, 1.0) if _mir0 else (None,)
    def rail_pt(n_, side):
        if n_.startswith("c") and n_[1:].isdigit():
            if int(n_[1:]) not in CORNERS_: K._fail("FAIL: rail end %s: no such corner (skin\\corners.json has c0..c%d - see CORNERS_*)" % (n_, len(CORNERS_) - 1))
            P_ = CORNERS_[int(n_[1:])]; return P_ if (side is None or side == MSIDE_) else K.reflect(P_[None, :], MN0, MC0)[0]
        if not n_.startswith("j:"): K._fail("FAIL: rail end %r is a corner \"c<n>\" or a junction \"j:<feature>+<feature>...\"" % n_)
        want = set(n_[2:].split("+")); cands = [v[1] for v in jfeat.values() if want <= v[2] and K.wall_dist(v[1][None, :])[0] > 1e-3 and (side is None or np.sign(v[1] @ MN0 - MC0) == side)]
        if not cands: K._fail("FAIL: rail end %s: no junction where %s all meet%s" % (n_, sorted(want), "" if side is None else " on side %+d" % side))
        return cands[0]
    nsnap = 0
    # RAILS_used.json
    _rails_carried = []
    try:
        _rails_md5 = K.md5(RAILS_P); _corners_md5 = K.md5(os.path.join(SK, "corners.json"))
        _ru = json.load(open(os.path.join(SK, "RAILS_used.json"), encoding="utf-8")) if os.path.isfile(os.path.join(SK, "RAILS_used.json")) else {}
        _same_file = _ru.get("rails_md5") == _rails_md5
        if _same_file and _ru.get("corners_md5") and _ru.get("corners_md5") != _corners_md5:
            # RAILS_used.json
            _oldc = {int(k_): np.asarray(v_, float) for k_, v_ in (_ru.get("corners_xyz") or {}).items()}
            if not _oldc:
                say("WARNING: RAILS %s was last used on ANOTHER corner numbering (run %s) and that run kept no corner places - c<n> may name a different corner now: check every rail on this run's CORNERS_* before trusting it" % (os.path.basename(RAILS_P), _ru.get("tag")))
            else:
                _ids6 = sorted(CORNERS_); _X6 = np.array([CORNERS_[i_] for i_ in _ids6])
                for rl_ in RAILS:
                    for end_ in ("a", "b"):
                        n_ = str(rl_[end_])
                        if n_.startswith("c") and n_[1:].isdigit() and int(n_[1:]) in _oldc:
                            d6_ = np.linalg.norm(_X6 - _oldc[int(n_[1:])], axis=1); j6_ = int(np.argmin(d6_))
                            if d6_[j6_] > 0.5: K._fail("FAIL: RAIL %s: its end %s (at %s on the numbering the file was written for, run %s) has no corner within 0.5 mm on this run's numbering - decide the rail again from this run's CORNERS_* (a RAILS file is known by its CONTENT: one re-checked on this run's CORNERS_* that keeps the same numbers needs a changed byte - a rail's why - or skin\\RAILS_used.json deleted; 31bq R5f)" % (rl_.get("name"), n_, np.round(_oldc[int(n_[1:])], 2).tolist(), _ru.get("tag")))
                            if "c%d" % _ids6[j6_] != n_: _rails_carried.append("%s.%s %s -> c%d" % (rl_.get("name"), end_, n_, _ids6[j6_])); rl_[end_] = "c%d" % _ids6[j6_]
                with open(os.path.join(SK, "RAILS_carried.json"), "w", encoding="utf-8") as _fh6: json.dump(RAILS, _fh6, indent=1)
                say("RAILS CARRIED (31bq OO): the corners were renumbered since %s was written (run %s) - %s -> skin\\RAILS_carried.json (use it from now on)" % (os.path.basename(RAILS_P), _ru.get("tag"), ("; ".join(_rails_carried)) if _rails_carried else "every rail end is the same corner by place"))
        _keep_ru = _same_file and bool(_ru.get("corners_xyz"))
        with open(os.path.join(SK, "RAILS_used.json"), "w", encoding="utf-8") as _fh:
            json.dump({"rails_md5": _rails_md5, "corners_md5": (_ru.get("corners_md5") if _keep_ru else _corners_md5), "tag": (_ru.get("tag") if _keep_ru else TAG), "last_tag": TAG, "file": RAILS_P,
                       "corners_xyz": (_ru.get("corners_xyz") if _keep_ru else {str(i_): [float(x) for x in CORNERS_[i_]] for i_ in CORNERS_})}, _fh, indent=1)
    except Exception as _exr6:
        say("   RAILS_used.json: not read / written (%s)" % str(_exr6)[:80])
    for rl in RAILS:
        for side in SIDES_:
            A_, B_ = rail_pt(rl["a"], side), rail_pt(rl["b"], side); AB = B_ - A_
            if float(np.linalg.norm(AB)) < 1e-6:
                K._fail("FAIL: RAIL %s: its ends %s and %s are ONE point on this layout (%s) - the corner numbers were decided on another run's CORNERS_*; "
                        "decide the rail again from this run's CORNERS_* pictures" % (rl.get("name"), rl["a"], rl["b"], np.round(A_, 2).tolist()))
            for key_, (x0_, x_, fs_, prs_) in jfeat.items():
                if K.wall_dist(x_[None, :])[0] < 1e-3 or (side is not None and np.sign(x_ @ MN0 - MC0) != side): continue
                if not (set(rl["has"]) <= fs_) or (set(rl.get("not", [])) & fs_): continue
                t_ = float(np.clip((x_ - A_) @ AB / max(AB @ AB, 1e-12), 0, 1)); q_ = A_ + t_ * AB
                if np.linalg.norm(q_ - x_) > float(rl.get("reach", 2.0)): continue
                JMOVE[_jk(x0_)] = q_; jfeat[key_][1] = q_; nsnap += 1
        say("RAIL %s: %s -> %s (%s)" % (rl["name"], rl["a"], rl["b"], rl.get("why", "")))
    _JK = list(JMOVE.keys()); _JKD = cKDTree(np.array(_JK)) if _JK else None
    say("RAILS: %d junction(s) put on their rail" % nsnap)
def _shift_ends(S):
    a_, b_ = _jmove(S[0]), _jmove(S[-1])
    if a_ is None and b_ is None: return S
    s_ = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(S, axis=0), axis=1))]); t_ = s_ / max(s_[-1], 1e-12)
    S = S.copy()
    if a_ is not None: S = S + (0.5 * (1 + np.cos(np.pi * t_)))[:, None] * (a_ - S[0])[None, :]
    if b_ is not None: S = S + (0.5 * (1 - np.cos(np.pi * t_)))[:, None] * (b_ - S[-1])[None, :]
    if a_ is not None: S[0] = a_
    if b_ is not None: S[-1] = b_
    return S
edges_out = []; recs = []
with busy("skin-wires: the first simplify pass over %d chains" % len(CH), 1500):
    for k in range(len(CH)):
        e, r = simplify_chain(k, 0); edges_out.append(e); recs.append(r)
        if k and k % 25 == 0: say("   simplify: %d of %d chains" % (k, len(CH)))
_SIMPLIFIED = True      # 31bw A5b
if CARRY_REJ:
    say("CARRIED DECISIONS NOT DRAWN (31bd): %d carried line(s) do not fit their new chain (further than CARRY_FIT %.2f mm) - drawn by the ladder instead;\n"
        "       decide each again for THIS numbering: %s" % (len(CARRY_REJ), CARRY_FIT, ", ".join("chain %d (%s %.1f mm off)" % x for x in CARRY_REJ[:20])))
def _apply_demotions(note=""):
    """31av: the faces a decided line could not stay one simple curve on leave their original surface (and their twins); their lines again"""
    for _r in range(3):
        req_ = {x_: w_ for x_, w_ in _DEMREQ.items() if x_ in PROJ}; _DEMREQ.clear()
        if not req_: return
        new_ = _demote(req_)
        redo_ = [k_ for k_ in range(len(CH)) if any(int(v_) in new_ for v_ in CH[k_]["pair"])]
        for k_ in redo_:
            e_, r_ = simplify_chain(k_, 0); edges_out[k_] = e_; recs[k_] = r_
        say("ORIGINAL SURFACE LEFT%s: face(s) %s leave their original surface (%s) - skin-build makes them flat or a smoothed fit; their %d line(s) are "
            "drawn again as decided. To keep a face on its surface, decide its line ON it (\"on\": [the original face]) or change its points"
            % (note, sorted(new_), "; ".join(sorted(set(req_.values())))[:240], len(redo_)))
_apply_demotions()
# skin-frame
CROSS_MM = float(os.environ.get("CROSS_MM", "0.05")); END_MM = float(os.environ.get("END_MM", "0.4"))
wc_ = Part.Shape(); wc_.importBrep(os.path.join(RUN, "wall_caps.brep"))
stretch = {int(q): v for q, v in FR.get("stretch", {}).items()}
def samp(e, step=0.05):
    n = max(3, int(e.Length / step) + 1); return np.array([P3(x) for x in e.discretize(Number=n)])
def face_edges(q):
    out = [("chain", k, edges_out[k]) for k, c in enumerate(CH) if recs[k]["rung"] != "WALL_DROPPED" and q in [int(x) for x in c["pair"]]]
    out += [("wall", (b, i), wc_.Faces[b].Edges[i]) for b, i in stretch.get(q, [])]
    return out
def crossings():
    found = []
    for q in range(len(PJ)):
        if PJ[q]["kind"] == "cap": continue
        fe = face_edges(q); sm = [samp(e) for _, _, e in fe]
        ends = [np.array([P3(e.Vertexes[0].Point), P3(e.Vertexes[-1].Point)]) for _, _, e in fe]
        for i in range(len(fe)):
            for j in range(i + 1, len(fe)):
                if fe[i][0] == "wall" and fe[j][0] == "wall": continue
                sh = [x for x in ends[i] for y in ends[j] if np.linalg.norm(x - y) < 0.05]
                A_, B_ = sm[i], sm[j]
                if sh:
                    mA = np.ones(len(A_), bool); mB = np.ones(len(B_), bool)
                    for x in sh:
                        mA &= np.linalg.norm(A_ - x, axis=1) > END_MM; mB &= np.linalg.norm(B_ - x, axis=1) > END_MM
                    A_, B_ = A_[mA], B_[mB]
                if not len(A_) or not len(B_): continue
                d, _ = cKDTree(B_).query(A_)
                if d.min() < CROSS_MM:
                    found.append((q, fe[i][:2], fe[j][:2], float(d.min()), A_[int(np.argmin(d))]))
    return found
# skin-frame
WALL_CLEAR = float(os.environ.get("WALL_CLEAR", "0.15")); EASE_MM = float(os.environ.get("EASE_MM", "1.5"))
def ease_off_wall(k_, wall_e, at):
    e0 = edges_out[k_]; S = samp(e0, 0.05); W_ = samp(wall_e, 0.02)
    wi, _ = K.wall_of(W_); n_in = K.WALLS[wi][0]
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(S, axis=0), axis=1))]); i0 = int(np.argmin(np.linalg.norm(S - at, axis=1)))
    w = np.where(np.abs(s - s[i0]) < EASE_MM, 0.5 * (1 + np.cos(np.pi * (s - s[i0]) / EASE_MM)), 0.0); w[0] = w[-1] = 0.0
    S2 = S + (WALL_CLEAR * w)[:, None] * n_in[None, :]
    bs = Part.BSplineCurve(); bs.approximate(Points=[V3(*x) for x in S2], DegMin=3, DegMax=3, Tolerance=0.005, Continuity="C2", ParamType="ChordLength")
    edges_out[k_] = bs.toShape(); recs[k_]["rung"] = recs[k_]["rung"] + "+CLEAR"; recs[k_]["wall_clear"] = WALL_CLEAR
for rnd in range(4):
    cr = crossings()
    if not cr: break
    bump = set(); asked_ = False
    for q, a_, b_, dmin, at in cr:
        walls_ = [x for x in (a_, b_) if x[0] == "wall"]; chains_ = [x for x in (a_, b_) if x[0] == "chain"]
        if walls_ and chains_ and recs[chains_[0][1]].get("rung", "").endswith("CLEAR") is False:
            b_i, e_i = walls_[0][1]
            ease_off_wall(chains_[0][1], wc_.Faces[b_i].Edges[e_i], at)
            say("   NEEDLE on face %d: chain %d ran along wall edge %s - eased into the edit region%s" % (q, chains_[0][1], walls_[0][1], num(" (%.3f mm off at (%.2f, %.2f, %.2f); eased %.2f mm)", dmin, at[0], at[1], at[2], WALL_CLEAR)))
            continue
        ondec_ = [k_ for t_, k_ in (a_, b_) if t_ == "chain" and recs[k_].get("decided") and "+ON_ORIG" in str(recs[k_].get("rung", ""))]
        if ondec_:
            for k_ in ondec_:
                for x_ in [int(v_) for v_ in CH[k_]["pair"]]:
                    if x_ in PROJ:
                        _DEMREQ.setdefault(x_, "decided line %d laid on its original surface crossed a neighbour on face %d" % (k_, q)); asked_ = True
            say("   CROSSING on face %d: %s and %s touch after decided line(s) %s were laid on an original surface - that surface is left, not the decision" % (q, a_, b_, ondec_))
            continue
        for t_, k_ in (a_, b_):
            if t_ == "chain": bump.add(k_)
        say("   CROSSING on face %d: %s and %s touch - made again tighter%s" % (q, a_, b_, num(" (%.3f mm apart at (%.2f, %.2f, %.2f))", dmin, at[0], at[1], at[2])))
    if asked_:
        _apply_demotions(" (a crossing)")
    with busy("NO CROSSINGS re-make: %d chain(s) simplified again tighter" % len(bump), 1500):
        for k_ in sorted(bump):
            e, r = simplify_chain(k_, min(2, recs[k_].get("strict", 0) + 1))
            if recs[k_].get("carry_rejected"): r["carry_rejected"] = recs[k_]["carry_rejected"]
            edges_out[k_] = e; recs[k_] = r
SYM_WIRES = os.environ.get("SYM_WIRES", "1") == "1"; END_BLEND = float(os.environ.get("END_BLEND", "2.0"))
_md = os.path.join(SK, "MIRROR_DECISION.json")
_mir = json.load(open(_md)).get("plane", "") if os.path.isfile(_md) else ""
if SYM_WIRES and _mir:
    MN, MC = K.mirror_plane(_mir)
    try: master = json.load(open(os.path.join(SK, "patches_labels.json"))).get("mirror", {}).get("master", "-")
    except Exception: master = "-"
    msign = -1.0 if master == "-" else 1.0
    grp_ = {}
    for p_ in PJ:
        if p_["kind"] != "cap" and p_.get("grp") is not None: grp_.setdefault(p_["grp"], []).append(p_["patch"])
    def twin(x):
        g = PJ[x].get("grp")
        if PJ[x]["kind"] == "cap" or g is None: return x
        m_ = [y for y in grp_.get(g, []) if y != x]
        return m_[0] if m_ else x
    live = [k for k in range(len(CH)) if recs[k]["rung"] != "WALL_DROPPED"]
    cent = {k: samp(edges_out[k], 0.2).mean(0) for k in live}
    bykey = {}
    for k in live: bykey.setdefault(frozenset(int(x) for x in CH[k]["pair"]), []).append(k)
    def blend_ends(S, A, B):
        s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(S, axis=0), axis=1))]); L = s[-1]; Lb = min(END_BLEND, 0.45 * L)
        wa = np.where(s < Lb, 0.5 * (1 + np.cos(np.pi * s / Lb)), 0.0); wb = np.where(L - s < Lb, 0.5 * (1 + np.cos(np.pi * (L - s) / Lb)), 0.0)
        S = S + wa[:, None] * (A - S[0])[None, :] + wb[:, None] * (B - S[-1])[None, :]; S[0] = A; S[-1] = B; return S
    def remake(S, k_):
        p_, q_ = [int(x) for x in CH[k_]["pair"]]; prs_ = _reaching(k_, p_, q_, S)
        if prs_:
            A, B = S[0].copy(), S[-1].copy(); S = np.array([alt_project(x.copy(), prs_) for x in S]); S[0] = A; S[-1] = B
        if len(S) < 4 or np.linalg.norm(S - (S[0] + np.outer(np.linspace(0, 1, len(S)), S[-1] - S[0])), axis=1).max() < 1e-4:
            return Part.LineSegment(V3(*S[0]), V3(*S[-1])).toShape()
        bs = Part.BSplineCurve(); bs.approximate(Points=[V3(*x) for x in S], DegMin=3, DegMax=3, Tolerance=0.005, Continuity="C2", ParamType="ChordLength")
        e_ = bs.toShape()
        ea_, eb_ = P3(e_.Vertexes[0].Point), P3(e_.Vertexes[-1].Point)
        if np.linalg.norm(ea_ - S[0]) > 1e-6 or np.linalg.norm(eb_ - S[-1]) > 1e-6: return None
        return e_
    nsym = nself = nmiss = 0; done = set(); onesided = []
    SELF_MM = float(os.environ.get("SELF_MM", "0.5"))
    def ends_of(e_): return P3(e_.Vertexes[0].Point), P3(e_.Vertexes[-1].Point)
    def _npoles_of(rung_, poles_):
        """the pole count a chain was drawn with: the record's own count FIRST (`poles` is the drawn curve's - cv.getPoles(); on an ON_ORIG chain the rung keeps the
        free fit's count, MULTI6 on a 73-pole edge), else the rung's MULTI<n>, else 4 (one cubic) - never under 4 (31bw, TB7b F1 / TB7c F1)"""
        try:
            if poles_: return max(4, int(poles_))
        except (TypeError, ValueError): pass
        m_ = _re_w.match(r"MULTI(\d+)", str(rung_ or ""))
        return max(4, int(m_.group(1))) if m_ else 4
    def _edge_form(e_):
        """the FORM an edge was drawn in - ('LINE' | 'ARC' | 'BSPLINE', its pole count) read off the edge's own curve; None when it cannot be read (31bw, TB7c F1)"""
        try:
            c_ = e_.Curve
            if isinstance(c_, (Part.Line, Part.LineSegment)): return ("LINE", None)
            if isinstance(c_, (Part.Circle, Part.ArcOfCircle)): return ("ARC", None)
            if hasattr(c_, "NbPoles"): return ("BSPLINE", int(c_.NbPoles))
        except Exception: pass
        return None
    def _mirror_snapped(e_, A_, B_):
        """31bw (TB7c F3): the kit-mirrored twin IS the master's exact mirror image - e_ is the master edge mirrored in the card's plane - and only its two END POINTS are moved onto the
        twin's own junctions A_ / B_ (the symmetric-junction pass leaves them within 1e-5 .. 1e-3 mm of the mirror's ends; 0.6 at most). A B-spline by its two end poles (the move fades out
        over the end span by the basis itself), a line rebuilt through the moved ends, an arc through them and its own midpoint. NOTHING IS RE-FITTED: a fresh fit of the mirror's samples
        cannot recover a cubic whose control polygon folds (the agent's d19 lid leg: fit_bspline's residual 0.148 mm on the leg's own samples - chain 52 came out 0.148 off its master's mirror
        with its apex angle 30 deg off; the testers' 0.46 was distToShape misreading a C0 edge - KERNEL_LESSONS K-C0-DIST). None for a curve kind not known here (the caller says so and
        falls back to the sampled form)."""
        try:
            c_ = e_.Curve
            if isinstance(c_, (Part.Line, Part.LineSegment)): return Part.LineSegment(V3(*A_), V3(*B_)).toShape()
            if isinstance(c_, (Part.Circle, Part.ArcOfCircle)):
                return Part.Arc(V3(*A_), e_.valueAt(0.5 * (e_.FirstParameter + e_.LastParameter)), V3(*B_)).toShape()
            if hasattr(c_, "setPole") and hasattr(c_, "NbPoles"):
                c_ = c_.copy()
                if abs(float(c_.FirstParameter) - float(e_.FirstParameter)) > 1e-9 or abs(float(c_.LastParameter) - float(e_.LastParameter)) > 1e-9: c_.segment(e_.FirstParameter, e_.LastParameter)
                a0_ = P3(c_.StartPoint)
                if np.linalg.norm(a0_ - A_) > np.linalg.norm(a0_ - B_): A_, B_ = B_, A_
                c_.setPole(1, V3(*A_)); c_.setPole(int(c_.NbPoles), V3(*B_)); return c_.toShape()
        except Exception:
            return None
        return None
    def _self_averaged(e_, A_, B_):
        """31bw (TB7c F5): an OWN-TWIN chain averaged with its mirror image AT THE POLE LEVEL - its poles and its mirror's (reversed when the mirror runs the other way, so both run
        the same way) averaged pairwise, the knots and multiplicities kept; a line by its ends, an arc through its ends and its averaged midpoint. The REASON (a string) for a kind or a knot vector
        with no such form (a rational, an approximated +ON_ORIG spline): the caller keeps the drawn line or takes the sampled form, the reason in its sym_note. The sampled form re-fitted the averaged
        samples at the edge's pole count and could not recover a GROWN cubic's folded control polygon: qq's chain 53 (its grown cubic 0.067 mm from its raw hump) was drawn 0.40 mm
        inside the hump, the laid-on self chains lost 0.08-0.14 the same way (probes\\probe_f5.txt) - F3's mechanism on the self chains."""
        try:
            c_ = e_.Curve
            if isinstance(c_, (Part.Line, Part.LineSegment)): return Part.LineSegment(V3(*A_), V3(*B_)).toShape()
            if isinstance(c_, (Part.Circle, Part.ArcOfCircle)):
                S_ = samp(e_, 0.05); R_ = K.reflect(S_, MN, MC)
                if np.linalg.norm(R_[0] - S_[0]) > np.linalg.norm(R_[0] - S_[-1]): R_ = R_[::-1]
                M_ = 0.5 * (S_ + R_)
                return Part.Arc(V3(*A_), V3(*M_[len(M_) // 2]), V3(*B_)).toShape()
            if isinstance(c_, Part.BSplineCurve):
                if c_.isRational(): return "a rational B-spline (its weights would need averaging too)"
                P_ = np.array([[p.x, p.y, p.z] for p in c_.getPoles()]); kn_ = np.array(c_.getKnots(), float); mu_ = [int(m) for m in c_.getMultiplicities()]
                if len(P_) < 2: return "fewer than two poles"
                Q_ = K.reflect(P_, MN, MC)
                if np.linalg.norm(Q_[0] - P_[0]) > np.linalg.norm(Q_[0] - P_[-1]):
                    if mu_ != mu_[::-1] or not np.allclose(kn_ - kn_[0], (kn_[-1] - kn_)[::-1], atol=1e-9): return "its mirror runs the other way and its knot vector is not symmetric (%d poles, an approximated spline)" % len(P_)
                    Q_ = Q_[::-1]
                M_ = 0.5 * (P_ + Q_); M_[0] = np.asarray(A_, float); M_[-1] = np.asarray(B_, float)
                bs_ = Part.BSplineCurve(); bs_.buildFromPolesMultsKnots([V3(*p) for p in M_], mu_, [float(u) for u in kn_], False, int(c_.Degree))
                return bs_.toShape()
            return "its curve kind %s" % type(c_).__name__
        except Exception as ex_: return "the kernel refused it: %r" % (ex_,)
    def _one(Sx, kx, npl, kind=None):
        """ONE line / arc / spline through the samples Sx in the master's own form: the KIND and the POLE COUNT of the master's own edge when they are known
        (_edge_form), else read off the rung kx and the record's count - a LINE, a 3-point ARC, else a B-spline of npl poles by the kit's own fit. Never the
        kernel's approximation: 31bw (TB7c F1) - approximating a +ON_ORIG master's samples at 0.005 had given a CUBIC+ON_ORIG chain's own-twin average 14 poles
        and a MULTI6+ON_ORIG one's 73 (two 'not one simple curve' borders drawn where the masters had none). 31bw (TB7b F1): a 4-pole refit of a 13-pole V leg
        had left chain 52 0.469 mm off its master's mirror while its record said 'mirror of chain 65' - the twin is drawn in the master's form."""
        kx = str(kx or ""); base_ = kx.split("+")[0]
        kind_ = kind or (base_ if base_ in ("LINE", "ARC") else "BSPLINE")
        if len(Sx) < 4 or kind_ == "LINE": return Part.LineSegment(V3(*Sx[0]), V3(*Sx[-1]))
        if kind_ == "ARC":
            try: return Part.Arc(V3(*Sx[0]), V3(*Sx[len(Sx) // 2]), V3(*Sx[-1]))
            except Exception: pass
        cvx, _, _, _, _ = fit_bspline(Sx, max(4, min(int(npl or 4), len(Sx) - 1))); return cvx
    def redraw(M_, A, B, rec_, apex=None, form=None):
        """the same line as its master, through A and B, shaped by the points M_ (the master's mirror image, or the mean of a chain and its own mirror) IN THE
        MASTER'S FORM - the kind and pole count of the master's own EDGE (form = _edge_form(edge); 31bw TB7c F1), else its rung and its record's count; a V per
        leg cut at the apex given (the master's apex reflected; the sharpest turn only when none is given); no blend, no new kind of fit (31bw A5b; TB7b F1)"""
        M_ = M_.copy(); M_[0] = A; M_[-1] = B
        rec_ = rec_ if isinstance(rec_, dict) else {"rung": str(rec_)}
        rung_ = str(rec_.get("rung") or ""); legs_ = rec_.get("legs") or []
        if rung_.startswith("V(") and len(M_) >= 6:
            cuts_ = []
            for x_ in (apex or []):
                i_ = int(np.argmin(np.linalg.norm(M_ - np.asarray(x_, float), axis=1)))
                if 2 <= i_ <= len(M_) - 3 and all(abs(i_ - c_) > 2 for c_ in cuts_): cuts_.append(i_)
            if not cuts_:
                turns_ = [((_hp_turn(M_, i_, HAIRPIN_MM) or 0.0), i_) for i_ in range(2, len(M_) - 2)]
                cuts_ = [max(turns_)[1]] if turns_ else [len(M_) // 2]
            cuts_ = sorted(cuts_)
            kinds_ = [str(l_.get("rung") or "CUBIC") for l_ in legs_] or rung_[2:].rstrip(")").split("+")
            idx_ = [0] + cuts_ + [len(M_) - 1]; parts_ = []
            for j_, (i0_, i1_) in enumerate(zip(idx_[:-1], idx_[1:])):
                kx = kinds_[j_] if j_ < len(kinds_) else "CUBIC"
                cvx = _one(M_[i0_:i1_ + 1], kx, _npoles_of(kx, (legs_[j_].get("poles") if j_ < len(legs_) else None)))
                parts_.append(cvx if isinstance(cvx, Part.BSplineCurve) else cvx.toBSpline())
            bs_ = parts_[0]
            for nx_ in parts_[1:]:
                if not bs_.join(nx_): bs_ = None; break
            if bs_ is not None: return bs_.toShape()
        kind_, npl_ = form if form else (None, None)
        return _one(M_, rung_, npl_ or _npoles_of(rung_, rec_.get("poles")), kind_).toShape()
    for k in live:
        if k in done: continue
        p_, q_ = [int(x) for x in CH[k]["pair"]]
        tk = frozenset((twin(p_), twin(q_)))
        cands = [k2 for k2 in bykey.get(tk, []) if k2 not in done]
        if not cands: nmiss += 1; continue
        mc = K.reflect(cent[k][None, :], MN, MC)[0]
        k2 = min(cands, key=lambda j: np.linalg.norm(cent[j] - mc))
        if k2 == k:
            S = samp(edges_out[k], 0.05); Rf = K.reflect(S, MN, MC)
            if np.linalg.norm(Rf[0] - S[0]) > np.linalg.norm(Rf[0] - S[-1]): Rf = Rf[::-1]
            n_ = min(len(S), len(Rf)); t_ = np.linspace(0, 1, n_)
            def rs(X):
                s_ = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(X, axis=0), axis=1))]); s_ /= max(s_[-1], 1e-12)
                return np.stack([np.interp(t_, s_, X[:, i]) for i in range(3)], 1)
            _self_dev = float(np.linalg.norm(rs(S) - rs(Rf), axis=1).max())
            if _self_dev > SELF_MM:
                recs[k]["sym"] = "one-sided: no twin chain (its faces %d/%d have no mirror twin; its mirror image is %.1f mm away) - left as it is" % (p_, q_, _self_dev)
                onesided.append((k, p_, q_, _self_dev)); nmiss += 1; done.add(k); continue
            A, B = ends_of(edges_out[k])
            if np.linalg.norm(A - S[0]) > np.linalg.norm(A - S[-1]): A, B = B, A
            try:
                _apx = [0.5 * (np.asarray(p_, float) + K.reflect(np.asarray(p_, float)[None, :], MN, MC)[0]) for p_ in (recs[k].get("apex") or [])]
                _fk = _edge_form(edges_out[k]); _e0s = edges_out[k]
                _avg = _self_averaged(_e0s, A, B)
                if not isinstance(_avg, str): edges_out[k] = _avg; recs[k]["self_form"] = "poles"
                else:
                    _er = redraw(0.5 * (rs(S) + rs(Rf)), A, B, recs[k], apex=_apx, form=_fk)
                    _moved = float(cKDTree(samp(_e0s, 0.05)).query(samp(_er, 0.05))[0].max())
                    if _moved > _self_dev:
                        recs[k]["self_form"] = "kept"; recs[k]["sym_note"] = "own twin: left as drawn - no pole-level average (%s) and the sampled average would move it %.3f mm off itself for an asymmetry of %.3f (31bw)" % (_avg, _moved, _self_dev)
                    else:
                        edges_out[k] = _er; recs[k]["self_form"] = "sampled"; recs[k]["sym_note"] = "own twin: the sampled average re-drawn in its own form - no pole-level average (%s) (31bw)" % _avg
                recs[k]["sym"] = "self"; nself += 1
                try:
                    _e0k = NE[k]; _Sk = np.array([P3(x) for x in _e0k.discretize(Number=max(25, int(_e0k.Length / 0.1) + 1))])
                    try: _Sk = _shift_ends(_Sk)
                    except Exception: pass
                    recs[k]["dev_fit"] = recs[k].get("dev_max"); recs[k]["dev_max"] = round(float(cKDTree(samp(edges_out[k], 0.05)).query(_Sk)[0].max()), 4); recs[k]["self_dev"] = round(_self_dev, 4)
                    if _fk: recs[k]["drawn_form"] = "%s%s" % (_fk[0], (" %d poles" % _fk[1]) if _fk[1] else "")
                except Exception as _exk:
                    recs[k]["dev_note"] = "the average's own deviation could not be measured (%s)" % str(_exk)[:60]
            except Exception: nmiss += 1
            done.add(k); continue
        a_, b_ = (k, k2) if (cent[k] @ MN - MC) * msign >= (cent[k2] @ MN - MC) * msign else (k2, k)
        Ma = edges_out[a_].mirror(V3(*(MN * MC)), V3(*MN))
        ma0, ma1 = ends_of(Ma); B0, B1 = ends_of(edges_out[b_])
        if np.linalg.norm(ma0 - B0) > np.linalg.norm(ma0 - B1): B0, B1 = B1, B0
        shift = max(np.linalg.norm(ma0 - B0), np.linalg.norm(ma1 - B1)); _fa = _edge_form(edges_out[a_])
        if shift < 1e-6: edges_out[b_] = Ma
        elif shift < 0.6:
            _snap = _mirror_snapped(Ma, B0, B1)
            if _snap is not None: edges_out[b_] = _snap
            else:
                _Sm = samp(Ma, 0.05)
                if np.linalg.norm(_Sm[0] - B0) > np.linalg.norm(_Sm[0] - B1): _Sm = _Sm[::-1]
                _apx = [(np.asarray(p_, float) - 2.0 * (float(np.asarray(p_, float) @ MN) - MC) * MN) for p_ in (recs[a_].get("apex") or [])]
                edges_out[b_] = redraw(blend_ends(_Sm, B0, B1), B0, B1, recs[a_], apex=_apx, form=_fa)
                recs[b_]["sym_note"] = "the mirror's samples re-drawn in the master's form - its curve kind %s has no exact snap (31bw)" % type(Ma.Curve).__name__
        else: nmiss += 1; done.update((a_, b_)); continue
        recs[b_]["sym"] = "mirror of chain %d (ends %.1e mm apart)" % (a_, shift); recs[b_]["rung"] = recs[a_]["rung"]; nsym += 1
        if _fa: recs[b_]["drawn_form"] = "%s%s" % (_fa[0], (" %d poles" % _fa[1]) if _fa[1] else "")
        for _kf in ("legs", "poles", "dev_max", "via", "grow_out", "cut_in", "inflections"):      # the twin's fit fields are its master's
            if _kf in recs[a_]: recs[b_][_kf] = json.loads(json.dumps(recs[a_][_kf]))
            else: recs[b_].pop(_kf, None)
        if recs[a_].get("apex"):
            recs[b_]["apex"] = [[round(float(v), 3) for v in (np.asarray(p_, float) - 2.0 * (float(np.asarray(p_, float) @ MN) - MC) * MN)] for p_ in recs[a_]["apex"]]
        else: recs[b_].pop("apex", None)
        try:
            _e0b = NE[b_]; _Sb = np.array([P3(x) for x in _e0b.discretize(Number=max(25, int(_e0b.Length / 0.1) + 1))])
            try: _Sb = _shift_ends(_Sb)
            except Exception: pass
            _Db = samp(edges_out[b_], 0.05)
            recs[b_]["dev_master"] = recs[a_].get("dev_max"); recs[b_]["dev_max"] = round(float(cKDTree(_Db).query(_Sb)[0].max()), 4)
            if recs[b_].get("legs"): recs[b_]["legs_of"] = "chain %d (the master's per-leg fit, reflected)" % a_
        except Exception as _exb:
            recs[b_]["dev_note"] = "the twin's own deviation could not be measured (%s)" % str(_exb)[:60]
        done.update((a_, b_))
    say("MIRRORED WIRES across %s: %d border(s) made from their master twin, %d own-twin border(s) averaged with their mirror, %d left as they were" % (_mir, nsym, nself, nmiss))
    if onesided:
        say("ONE-SIDED BORDERS (31bd): %d chain(s) have no twin chain - a face on one side lost its mirror twin (skin-features' merges, or an unsymmetric\n"
            "       layout); left as they are, NOT mirrored, NOT averaged: %s\n"
            "       A symmetric piece needs these paired: the layout's mirror check (skin-mirror WHAT=layout) says which faces have no twin."
            % (len(onesided), ", ".join("chain %d (faces %d/%d, %.1f mm off its mirror)" % x for x in onesided[:12])))
cr = crossings()
say("CROSSINGS left: %d%s" % (len(cr), "" if not cr else " - FACES %s" % sorted(set(c_[0] for c_ in cr))))
# CORNERS_
# skin-build
# "_fillets"
# skin-build
# guides.brep  fillets.json
ADD_SNAP = float(os.environ.get("ADD_SNAP", "1.0"))
if LINESPEC:
    import re as _re
    _twin = {}
    for k_, r_ in enumerate(recs):
        m_ = _re.search(r"mirror of chain (\d+)", str(r_.get("sym", "")))
        if m_: _twin[k_] = int(m_.group(1)); _twin[int(m_.group(1))] = k_
        elif str(r_.get("sym", "")) == "self": _twin[k_] = k_
    _bad = []; _warn = []
    for ks_, v_ in LINESPEC.items():
        k_ = int(ks_)
        if k_ >= len(CH): continue
        why_ = _re.sub(r"\s*\[carried from chain[^\]]*\]", "", str(v_.get("why", "")))      # 31br D9: the carry suffix is the kit's
        L_ = float(CH[k_].get("length") or 0.0)
        lens_ = [float(x) for x in _re.findall(r"(\d+(?:\.\d+)?)\s*mm\b", why_)]; tws_ = [int(x) for x in _re.findall(r"\btwin\s+(\d+)", why_)]
        len_ok = (not lens_) or any(abs(x - L_) <= max(1.0, 0.25 * L_) for x in lens_)
        tw_ok = (not tws_) or (k_ not in _twin) or any(x == _twin[k_] for x in tws_)
        if len_ok: continue
        cands_ = [j_ for j_ in range(len(CH)) if j_ != k_ and (not lens_ or any(abs(x - float(CH[j_].get("length") or 0.0)) <= max(0.5, 0.1 * x) for x in lens_))
                  and (not tws_ or any(x == _twin.get(j_, -1) for x in tws_))]
        msg_ = "chain %d's reason says %s%s but chain %d is %.1f mm%s%s" % (k_, ("%s mm" % " / ".join("%.1f" % x for x in lens_)) if lens_ else "", (" twin %s" % "/".join(str(x) for x in tws_)) if tws_ else "",
                                                                        k_, L_, (" (twin %d)" % _twin[k_]) if k_ in _twin else "", (" - the chain(s) that match the reason: %s" % cands_[:6]) if cands_ else "")
        if cands_ and not len_ok and not tw_ok: _bad.append(msg_)
        else: _warn.append(msg_)
    for m_ in _warn: say("   LINES REASON CHECK: " + m_ + " - the decision may be keyed to the wrong chain (the numbers on the LAST WIRE_* frames are the chains')")
    if _bad: K._fail("FAIL: a LINES decision is keyed to the WRONG CHAIN - its reason describes another: " + " | ".join(_bad[:4]) + " - re-key it (the chain numbers on the LAST WIRE_* frames)")
_raw_add = []; _raw_fil = []
for _src in ((LINES_P and _raw_l) or {}, ):
    _raw_add = list(_src.get("_add") or []); _raw_fil = list(_src.get("_fillets") or [])
def _strip_carry(s):
    """31bq R7W (M5, B1 1): a reason without the kit's own carry tags at its head - '[carried from face N by its drawn ends] ', '[carried from line N] ',
    '[carried from lines [..]] ' - all of them (they stacked once per carry and were never stripped: after one carry 19 characters of the agent's reason were
    compared, after two none)"""
    return _re_w.sub(r"^(\s*\[carried from (?:face|line|lines) (?:\[[^\]]*\]|[^\[\]])*\]\s*)+", "", str(s or "")).strip()
def _new_add_id(a_, ai_):
    """31bq R7W (M5): the id of an _add entry that has none (an agent's own entry) - from its own content and place, the same on every run of the same file"""
    return "a" + hashlib.md5(json.dumps([_strip_carry(a_.get("why")), str(a_.get("role", "")).lower(), str(a_.get("kind", "")).upper(), a_.get("face"), a_.get("from"), a_.get("to"), int(ai_)], default=str).encode("utf-8")).hexdigest()[:10]
def _add_match(a_, ai_, pgr):
    """31bq R7W (M5, B1 1): the last run's drawn edge for this _add entry - by the kit's own id when the entry carries one (skin\\LINES_carried.json holds them
    after a carry), else by its face, role and WHOLE reason with the kit's carry tags stripped. Two candidates are never decided by the first found or by the
    entry's index: a LINES list edited since the drawing run (an entry deleted, inserted or moved) had carried one entry onto its neighbour's drawn ends - the
    wrong face partition, nothing said. Returns (record, None) or (None, why the entry is TO DECIDE)"""
    ms_ = [g_ for g_ in pgr if g_.get("mirror_of") is None]
    aid_ = str(a_.get("id") or "").strip()
    if aid_:
        c_ = [g_ for g_ in ms_ if str(g_.get("add_id") or "") == aid_]
        if len(c_) == 1: return c_[0], None
        return None, (("its id %s names %d lines the last run drew" % (aid_, len(c_))) if c_ else ("its id %s is on no line the last run drew (an entry that run did not draw, or an id edited by hand)" % aid_))
    w_ = _strip_carry(a_.get("why")); ro_ = str(a_.get("role", "")).lower()
    try: fa_ = int(a_.get("face", -2))
    except (TypeError, ValueError): fa_ = -2
    c_ = [g_ for g_ in ms_ if str(g_.get("role", "")).lower() == ro_ and int(g_.get("face", -1)) == fa_ and _strip_carry(g_.get("why")) == w_]
    if len(c_) == 1: return c_[0], None
    if c_: return None, ("%d lines the last run drew share its face %s, role %s and reason (entries %s) - which one this entry is cannot be told: give each its own reason, or carry with skin\\LINES_carried.json (it holds their ids)" % (len(c_), fa_, ro_, sorted(int(g_.get("entry", -1)) for g_ in c_)))
    return None, "no line the last run drew has its face %s, role %s and reason - a new or rewritten entry: write it on this run's face numbers" % (fa_, ro_)
if LINES_P and (_raw_add or _raw_fil) and LINES_NET != NET_MD5:
    _carried_add = []; _carried_fil = []; _todo6 = []
    if _prev and _prev_net and LINES_NET == _prev_net:
        _pvc = {int(c_["chain"]): c_ for c_ in (_prev.get("chains") or []) if c_.get("sig") and c_.get("mid") is not None}
        def _new_chain(k_old):
            c_ = _pvc.get(int(k_old))
            if c_ is None: return None
            sc_ = sorted(str(x) for x in c_["sig"]); best_ = None
            for k2 in range(len(CH)):
                if FREC[k2]["kind"] == "wall_dropped" or SIG[k2] != sc_: continue
                d_ = float(np.linalg.norm(MID[k2] - np.asarray(c_["mid"], float)))
                if best_ is None or d_ < best_[0]: best_ = (d_, k2)
            return best_[1] if best_ is not None and best_[0] <= CARRY_MM else None
        for f_ in _raw_fil:
            if not isinstance(f_, dict): continue
            if f_.get("lines") is not None:
                nl_ = [_new_chain(x_) for x_ in f_["lines"]]
                _sk9 = {}
                if isinstance(f_.get("sharp_ok"), list): _sk9 = {"sharp_ok": [n2_ for n2_ in (_new_chain(x_) for x_ in f_["sharp_ok"] if str(x_).lstrip("-").isdigit()) if n2_ is not None]}
                if all(x_ is not None for x_ in nl_) and len(set(nl_)) == len(nl_): _carried_fil.append(dict(f_, lines=nl_, why=("[carried from lines %s] " % list(f_["lines"])) + _strip_carry(f_.get("why", ""))[:300], **_sk9))
                else: _todo6.append("_fillets chain %s: member(s) %s have no chain between the same two features within %g mm" % (list(f_["lines"]), [o_ for o_, n_ in zip(f_["lines"], nl_) if n_ is None], CARRY_MM))
            elif f_.get("line") is not None:
                n_ = _new_chain(f_["line"])
                if n_ is not None: _carried_fil.append(dict(f_, line=n_, why=("[carried from line %s] " % f_["line"]) + _strip_carry(f_.get("why", ""))[:300]))
                else: _todo6.append("_fillets line %s: no chain between the same two features within %g mm" % (f_["line"], CARRY_MM))
        _pg = None
        try:
            _pg = json.load(open(os.path.join(SK, "guides.json"), encoding="utf-8")); _pgb = Part.Shape(); _pgb.importBrep(os.path.join(SK, "guides.brep")); _pge = _pgb.Edges
        except Exception: _pg = None
        if _raw_add and _pg is not None and (_pg.get("network_frame_md5") or _pg.get("tag")):
            _pgr = [g_ for g_ in (_pg.get("guides") or []) if g_.get("role") in ("guide", "split")]
            _ct_ = cKDTree(Vu[F].mean(1))
            for ai_, a_ in enumerate(_raw_add):
                m_, nmw_ = _add_match(a_, ai_, _pgr)
                if m_ is None or int(m_.get("edge", -1)) >= len(_pge): _todo6.append("_add entry %d (%s %s on old face %s): %s (31bq R7W, B1 1 / B06 (7))" % (ai_, a_.get("role"), a_.get("kind"), a_.get("face"), nmw_ or "its drawn edge is not in the last run's guides.brep")); continue
                e_ = _pge[int(m_["edge"])]; pa_ = e_.Vertexes[0]; pb_ = e_.Vertexes[-1]; md_ = e_.valueAt(0.5 * (e_.FirstParameter + e_.LastParameter))
                _, j_ = _ct_.query([md_.x, md_.y, md_.z]); newf_ = int(_pid[j_])
                if PJ[newf_]["kind"] == "cap": _todo6.append("_add %s on old face %s: its middle now lies on a cap" % (a_.get("role"), a_.get("face"))); continue
                _carried_add.append(dict(a_, face=newf_, **{"from": [round(pa_.X, 4), round(pa_.Y, 4), round(pa_.Z, 4)], "to": [round(pb_.X, 4), round(pb_.Y, 4), round(pb_.Z, 4)]}, **({"own_mirror": True} if not any(g2_.get("mirror_of") is not None and int(g2_.get("mirror_of")) == int(m_.get("entry", -9)) for g2_ in _pgr) else {}), why=("[carried from face %s by its drawn ends] " % a_.get("face")) + _strip_carry(a_.get("why", ""))[:300], id=(str(m_.get("add_id") or "").strip() or _new_add_id(a_, ai_))))
        elif _raw_add: _todo6.append("%d _add entries: the last run's guides.json / guides.brep are not here to carry them by their ends" % len(_raw_add))
        say("LINES CARRIED (31bq B06): of %s's %d _add and %d _fillets entries written for the last run's numbering, %d _add and %d _fillets carried to this one (a fillet line by its two features and middle within %g mm; an added line by its drawn ends onto the face that holds them now)%s"
            % (os.path.basename(LINES_P), len(_raw_add), len(_raw_fil), len(_carried_add), len(_carried_fil), CARRY_MM, (" - TO DECIDE: " + "; ".join(_todo6[:12])) if _todo6 else ""))
        _raw_add, _raw_fil = _carried_add, _carried_fil
        try:
            with open(os.path.join(SK, "LINES_carried.json"), "r+", encoding="utf-8") as _fh:
                _lc = json.load(_fh); _lc["_add"] = _carried_add; _lc["_fillets"] = _carried_fil; _fh.seek(0); _fh.truncate(); json.dump(_lc, _fh, indent=1)
        except Exception as _exw6: say("   LINES_carried.json: the carried _add / _fillets were NOT written back (%s) - this run uses them; add them to that file before the next run" % str(_exw6)[:80])
    else:
        say("TO DECIDE - the %d _add and %d _fillets entries of %s were written for another layout's numbering (its _network_md5 %s; neither this run's %s nor the last skin-wires run's): NOT applied.\n"
            "       Re-add them on THIS layout's face and chain numbers (LAYOUT_* / WIRE_* pictures) in skin\\LINES_carried.json and run skin-wires again."
            % (len(_raw_add), len(_raw_fil), os.path.basename(LINES_P), (LINES_NET or "none")[:8], NET_MD5[:8]))
        _raw_add = []; _raw_fil = []
if os.environ.get("ADD", "").strip():
    try: _raw_add = list(json.load(open(os.environ["ADD"].strip(), encoding="utf-8")))
    except (OSError, ValueError) as ex_: K._fail("FAIL: ADD %s: %s" % (os.environ["ADD"], ex_))
if os.environ.get("FILLETS", "").strip():
    try: _raw_fil = list(json.load(open(os.environ["FILLETS"].strip(), encoding="utf-8")))
    except (OSError, ValueError) as ex_: K._fail("FAIL: FILLETS %s: %s" % (os.environ["FILLETS"], ex_))
LINE_OFF_MAX = float(os.environ.get("LINE_OFF_MAX", "0.5") or 0.5); LINES_PART = {"taken": False, "why": "not run"}
def _lines_against_part():
    """31bq B19: EVERY DECIDED LINE AND EVERY ADDED LINE IS MEASURED AGAINST THE PART (FAILURES 2026-10-09 17:13: the agent's straight chords sat 1.6-2.8 mm off a
    curved border and the WIRE frames showed nothing wrong) - point-to-triangle against the source mesh; over LINE_OFF_MAX the run is refused by name.
    31bq OO (B19 (a)): on EVERY run (the block sat inside the added-lines branch: a LINES file with no _add / _fillets measured nothing); a measurement that
    cannot complete is NOT TAKEN - said, and recorded for the judge (WIRES_LOOK.json lines_against_part); a traced line over the limit says WHERE and WHY.
    31bq R7f: a reading whose exact pass failed (sk_lib.CLOSEST_LAST) is an UPPER BOUND - said in the refusal, on the summary line and in the record."""
    _off_bad = []; _off_trace = []; _off_n = [0, 0]; _off_worst = 0.0; _nx_all = []
    _END_OFF = " - at its END (on the face's border): an end off the part is MOVED onto it - a corner, a junction or a point on the border; a trace keeps its ends and cannot cure one (31bq R5j)"
    def _end_note(r_, X_):
        """31bq R7W (B1 6): the border an added line's END sits on, named - its chain, decided or the ladder's, its own distance to the part there, and how far
        the kit moved its junction (SYMMETRIC JUNCTIONS / a RAIL). An end is snapped ONTO its face's border, so an end off the part is that border's (or the moved
        junction's): 'move the end onto the part' cannot cure it, and 'a border line decided off the part' blamed a decided line where none was"""
        try:
            q_ = int(r_.get("face")); X_ = np.asarray(X_, float); best_ = None
            for tag_, kid_, e_ in face_edges(q_):
                S2_ = samp(e_, 0.05); d2_ = np.linalg.norm(S2_ - X_, axis=1); j2_ = int(np.argmin(d2_))
                if best_ is None or d2_[j2_] < best_[0]: best_ = (float(d2_[j2_]), tag_, kid_, S2_, j2_)
            if best_ is None: return ""
            _d2, tag_, kid_, S2_, j2_ = best_
            if tag_ == "wall": return " - it sits on the body's wall edge %s there (the caps are the body's own faces)" % (list(kid_),)
            lo_ = max(0, j2_ - 4); hi_ = min(len(S2_), j2_ + 5); _, dd_ = K.closest_on_mesh(S2_[lo_:hi_], Vu, F, kct); off_ = float(np.max(dd_))
            at_j_ = j2_ <= 1 or j2_ >= len(S2_) - 2; mv_ = 0.0
            if at_j_:
                xe_ = S2_[0] if j2_ <= 1 else S2_[-1]; mv_ = float(min(np.linalg.norm(P3(NE[kid_].Vertexes[0].Point) - xe_), np.linalg.norm(P3(NE[kid_].Vertexes[-1].Point) - xe_)))
            rc_ = recs[kid_]
            return " - it sits on chain %d (%s %s), which itself lies %.2f mm off the part there%s: decide that border on the part%s (31bq R7W, B1 6)" % (kid_, "decided" if rc_.get("decided") else "the ladder's", str(rc_.get("rung", "?")).split("+")[0], off_,
                (" at its junction, which the kit moved %.2f mm (SYMMETRIC JUNCTIONS / a RAIL)" % mv_) if (at_j_ and mv_ > 0.01) else (" at its junction" if at_j_ else ""), ", or move that junction" if (at_j_ and mv_ > 0.01) else "")
        except Exception as ex_: return " - the border it sits on was not read (%s)" % str(ex_)[:60]
    def _not_exact():
        """31bq R7f: the last closest_on_mesh call's exactness - a reading whose exact pass failed is the nearest-64 UPPER BOUND (it can read HIGH, never low): a pass on
        it is sound, a refusal may be the instrument's - said in the refusal and on the summary line, recorded for the judge (the bare except had printed "exact")"""
        _l = getattr(K, "CLOSEST_LAST", None) or {}
        if _l.get("exact", True): return ""
        _w = str(_l.get("why", "?"))[:120]; _nx_all.append(_w)
        return " [NOT EXACT: the exact pass failed (%s) - the nearest-64 reading is an UPPER BOUND: the line may lie nearer the part than it reads]" % _w
    try:
        for k_ in range(len(CH)):
            if not recs[k_].get("decided") or edges_out[k_] is None: continue
            P_ = samp(edges_out[k_], 0.2); _, d_ = K.closest_on_mesh(P_, Vu, F, kct); _nx_ = _not_exact(); i_ = int(np.argmax(d_)); recs[k_]["off_source_mm"] = round(float(d_[i_]), 3); _off_n[0] += 1; _off_worst = max(_off_worst, float(d_[i_]))
            if _nx_: recs[k_]["off_source_exact"] = False
            if d_[i_] > LINE_OFF_MAX: _off_bad.append("chain %d (%s, decided): %.2f mm off the source at %s%s%s" % (k_, recs[k_].get("rung", "?"), d_[i_], np.round(P_[i_], 1).tolist(), _END_OFF if (i_ <= 1 or i_ >= len(P_) - 2) else "", _nx_))
        for e_, r_ in zip(GUIDE_EDGES, GUIDE_RECS):
            P_ = samp(e_, 0.2); _, d_ = K.closest_on_mesh(P_, Vu, F, kct); _nx_ = _not_exact(); i_ = int(np.argmax(d_)); r_["off_source_mm"] = round(float(d_[i_]), 3); _off_n[1] += 1; _off_worst = max(_off_worst, float(d_[i_]))
            if _nx_: r_["off_source_exact"] = False
            if d_[i_] > LINE_OFF_MAX and r_.get("trace"):
                ti_ = r_.get("trace_info") or {}
                _gw = None; _tw = None; _sw = 0.5; _gs = list(ti_.get("gaps") or [])
                try: _sw = float(ti_.get("step") or 0.5); _tw = float((P_[i_] - np.asarray(ti_["a"], float)) @ np.asarray(ti_["u"], float)); _gw = next((g_ for g_ in _gs if g_["t0"] - _sw <= _tw <= g_["t1"] + _sw), None)
                except Exception: _tw = None
                _more = (" (%d gap run(s) along it in all)" % len(_gs)) if len(_gs) > 1 else ""
                if _gw is not None and _gw.get("stated"):
                    why_ = "for %.1f mm, from %s to %s, it is interpolated across the original face(s) %s the entry names in \"span\" (a region the design closes) - stated in the entry, not refused%s" % (_gw["gap_mm"], _gw["gap_from"], _gw["gap_to"], ti_.get("span"), _more)
                elif _gw is not None:
                    why_ = "for %.1f mm, from %s to %s, no triangle of its face crosses the plane normal to the line - the face is not there across it (the nearest surface there is face %s's%s) - the curve is interpolated across that stretch (a cubic through the kept points either side)%s" % (_gw["gap_mm"], _gw["gap_from"], _gw["gap_to"], _gw.get("gap_face"), (", original %s" % _gw["gap_orig"]) if _gw.get("gap_orig") is not None else "", _more)
                elif _tw is not None and (_tw <= 2 * _sw or _tw >= float(ti_.get("len") or 0.0) - 2 * _sw):
                    why_ = "the worst point is at the trace's END (%.2f mm along the %.1f mm line), where it sits on the face's border - that border lies off the part there (a border line decided off the part carries its ends): check that border line, or end the trace elsewhere%s%s" % (_tw, float(ti_.get("len") or 0.0), _end_note(r_, P_[i_]), _more)
                else: why_ = "the trace lies on %s at its samples and leaves the part between them (the interpolation) - split the line there or end it elsewhere (a trace takes no \"via\" points: its curve follows its face between its own two ends - 31bq R7W, B1 7)%s" % (ti_.get("on", "its face's surface"), _more)
                _off_trace.append("traced _add %s on face %s: %.2f mm off the source at %s - %s" % (r_.get("kind"), r_.get("face"), d_[i_], np.round(P_[i_], 1).tolist(), why_))
            if d_[i_] > LINE_OFF_MAX and not r_.get("trace"): _off_bad.append("_add %s %s on face %s: %.2f mm off the source at %s%s%s" % (r_.get("role"), r_.get("kind"), r_.get("face"), d_[i_], np.round(P_[i_], 1).tolist(), (_END_OFF + _end_note(r_, P_[i_])) if (i_ <= 1 or i_ >= len(P_) - 2) else "", _nx_))
        _how_ex = ", exact" if not _nx_all else ("; the EXACT pass FAILED on %d of %d call(s) - %s - those readings are the nearest-64 UPPER BOUND, which can read HIGH: a pass on them is sound, a refusal may be the instrument's (31bq R7f)" % (len(_nx_all), _off_n[0] + _off_n[1], _nx_all[0]))
        say("LINES AGAINST THE PART: %d decided line(s) and %d added line(s) measured against the source mesh (point-to-triangle%s) - the worst %.2f mm off it (LINE_OFF_MAX %g)" % (_off_n[0], _off_n[1], _how_ex, _off_worst, LINE_OFF_MAX))
        if _off_trace: say("   traced line(s) over LINE_OFF_MAX - not refused (a trace follows its face where there is one): %s" % "; ".join(_off_trace))
        LINES_PART.clear(); LINES_PART.update({"taken": True, "worst_mm": round(_off_worst, 3), "decided": _off_n[0], "added": _off_n[1], "traced_over": _off_trace, "refused": _off_bad, "exact": not _nx_all, "not_exact": _nx_all[:5]})
    except Exception as _exo:
        LINES_PART.clear(); LINES_PART.update({"taken": False, "why": str(_exo)[:200]})
        say("LINES AGAINST THE PART: NOT TAKEN - the lines' distance to the source could not be measured (%s); the judge's record says so (WIRES_LOOK.json lines_against_part) - a check that did not run is no pass" % str(_exo)[:80])
    if _off_bad:
        _ends_only = all(_END_OFF in b_ for b_ in _off_bad); _any_end = any(_END_OFF in b_ for b_ in _off_bad)
        K._fail("FAIL: %d decided / added line(s) leave the part by more than LINE_OFF_MAX %g mm: %s. A straight chord across a curved border, or a split's end off the surface, builds a face the part does not have (FAILURES 2026-10-09): %s" % (len(_off_bad), LINE_OFF_MAX, "; ".join(_off_bad[:8]),
                ("move each END named onto the part (a corner c<n>, a junction j<n>, or a point on the border) - or, where the line names the border it sits on as off the part itself, decide that border on the part (31bq R7W, B1 6)" if _ends_only else
                 ("decide an ARC or a CUBIC, add \"via\" points on the surface, or \"trace\": true (a trace follows its face's own surface between its ends)" + ("; an END named off the part is moved onto it, not traced" if _any_end else "")))))
def _room_meet(O_, B_, J_, tol=0.15, thin=0.3):
    """31bq R7W (M7): skin-build's MEET at one end of a fillet line on one face (sk_build _fillet_lines, the meet pass): the border leaving the junction J_ is
    MET where the UNTAPERED offset line passes within tol of it (the build's MEET_TOL 0.15) at a point at least thin (THIN_MM) from J_ - the build cuts that
    border there and measures it no more. O_ the offset polyline (the crease samples moved t across the face), B_ the border's samples. The distance is point
    to SEGMENT both ways (the offset's 0.3 mm samples alone read a crossing up to 0.15 mm wide). Returns (met, the nearest distance, the meet point's
    distance from J_ - the meet point is the border's own)"""
    O_ = np.asarray(O_, float).reshape(-1, 3); B_ = np.asarray(B_, float).reshape(-1, 3); J_ = np.asarray(J_, float).reshape(3)
    if len(O_) < 2 or len(B_) < 1: return False, float("inf"), 0.0
    def _ps(P_, Q_):
        a_ = Q_[:-1]; ab_ = Q_[1:] - a_; L2_ = np.maximum((ab_ * ab_).sum(1), 1e-18)
        tt_ = np.clip(((P_[:, None, :] - a_[None]) * ab_[None]).sum(2) / L2_[None], 0.0, 1.0); X_ = a_[None] + tt_[:, :, None] * ab_[None]
        D_ = np.linalg.norm(X_ - P_[:, None, :], axis=2); j_ = np.argmin(D_, axis=1); r_ = np.arange(len(P_)); return D_[r_, j_], X_[r_, j_]
    dB_, _ = _ps(B_, O_); ib_ = int(np.argmin(dB_)); d_ = float(dB_[ib_]); E_ = B_[ib_]
    if len(B_) >= 2:
        dO_, XO_ = _ps(O_, B_); io_ = int(np.argmin(dO_))
        if float(dO_[io_]) < d_: d_ = float(dO_[io_]); E_ = XO_[io_]
    dJ_ = float(np.linalg.norm(E_ - J_))
    return bool(d_ <= tol and dJ_ >= thin), d_, dJ_
def _room_border_at(J_, borders_, k_self, tol=0.05):
    """31bq R7W (M7): the border of a face that LEAVES the junction J_ (sk_build _border_at / _corner_edge_at): a border of the face - a chain other than the crease
    k_self, or a body wall edge - whose end lies within tol of J_, the nearest; borders_ [(tag, kid, samples)]. Returns (tag, kid, samples) or None"""
    J_ = np.asarray(J_, float).reshape(3); best_ = None
    for tag_, kid_, P_ in borders_:
        if tag_ == "chain" and kid_ == k_self: continue
        P_ = np.asarray(P_, float).reshape(-1, 3)
        if not len(P_): continue
        d_ = min(float(np.linalg.norm(P_[0] - J_)), float(np.linalg.norm(P_[-1] - J_)))
        if d_ < tol and (best_ is None or d_ < best_[0]): best_ = (d_, tag_, kid_, P_)
    return None if best_ is None else best_[1:]
def _room_end_kinds(S_, line_ends_, pieces_, me_, side_borders_, side_splits_, k_self, tol=0.05, split_tol=0.3):
    """31bq R7W (M7): each end of a fillet line - or of one leg of it - as skin-build classes it (sk_build _chain_members / _fillet_lines): a CHAIN END where it meets
    the end of another piece of its chain (another member line's, or this line's OTHER LEG where a split cut it - the build takes a chain's cut line as its legs)
    and a corner edge leaves the junction on the SIDE face (a border of it other than the crease, or a split of it ending there - none: the build tapers there);
    a SPLIT END where the end is no end of the line itself (a split's cut) and no chain end; else a free junction end. S_ this piece's samples; line_ends_ the
    line's own two ends; pieces_ [(line, leg, start, end)] of its chain (None: no chain context - the build makes the lines single blends); me_ (line, leg) this
    piece; side_borders_ [(tag, kid, samples)] the side face's borders; side_splits_ the ends of the side face's splits. Returns (chain_end [b, b], split_end
    [b, b], corner [(tag, kid) | ("split", None) | None] x 2)"""
    S_ = np.asarray(S_, float); J2_ = (S_[0], S_[-1]); le_ = [np.asarray(x_, float).reshape(3) for x_ in line_ends_]
    split_ = [bool(min(float(np.linalg.norm(J_ - x_)) for x_ in le_) > 1e-3) for J_ in J2_]
    chain_ = [False, False]; corner_ = [None, None]
    if pieces_ is not None:
        for e_, J_ in enumerate(J2_):
            if not any((l2_, g2_) != tuple(me_) and min(float(np.linalg.norm(np.asarray(a_, float) - J_)), float(np.linalg.norm(np.asarray(b_, float) - J_))) < tol for l2_, g2_, a_, b_ in pieces_): continue
            b_ = _room_border_at(J_, side_borders_, k_self, tol)
            c_ = (b_[0], b_[1]) if b_ is not None else None
            if c_ is None and any(float(np.linalg.norm(np.asarray(x_, float).reshape(3) - J_)) < (split_tol if split_[e_] else tol) for x_ in (side_splits_ or [])): c_ = ("split", None)
            if c_ is not None: chain_[e_] = True; corner_[e_] = c_
    split_ = [bool(split_[e_] and not chain_[e_]) for e_ in (0, 1)]
    return chain_, split_, corner_
def _room_taper_ends(chain_end, split_end, met_pq, fil_taper=True):
    """31bq R7W (M7): the ends skin-build TAPERS (sk_build _fillet_lines' TAPER_ENDS): never a chain end (the member is swept at full R to the junction it shares
    with the next), always a split end that is no chain end (the corner stays a point), and a free junction end unless the offset line MEETS the border leaving
    it on BOTH faces (fil_taper: FIL_TAPER - an unmet end with FIL_TAPER=0 takes the cap). met_pq [[end 0, end 1] of face p, of face q]"""
    return tuple(e_ for e_ in (0, 1) if not chain_end[e_] and (split_end[e_] or (fil_taper and not all(bool(m_[e_]) for m_ in met_pq))))
def _room_width(S_, im_, D_, ts_, thn_, borders_, touch_mm=0.3):
    """31bq B36 (2) / PP (B36 (a)(b)) / R7W (M7): skin-build's WIDTH RULE estimated on the mesh (sk_build _fillet_lines) - the strip's cross-lines from each judged
    crease sample (im_: clear of the ends by the untapered t) to its offset point (D_ the offset direction on the face, ts_ the - tapered - t) against the face's
    borders_ [(tag, kid, samples)] within the (tapered) print tolerance thn_ (per sample of S_); the line itself, a meeting sibling and every border the build
    CUTS are not in borders_. A border within touch_mm of an end leaves the junction: the crease point itself is not held against it. Returns (best, clear) -
    best = (the nearest distance, tag, kid, the sample's index into im_, the face's width there) where a cross-line comes within the margin, else None; clear =
    the least margin left"""
    from scipy.spatial import cKDTree as _KD
    S_ = np.asarray(S_, float); im_ = np.asarray(im_, int); D_ = np.asarray(D_, float); inner_ = S_[im_]; Df_ = D_[im_]
    Of_ = (S_ + np.asarray(ts_, float)[:, None] * D_)[im_]; th_ = np.asarray(thn_, float)[im_]
    lam_ = np.linspace(0.0, 1.0, 7); segs_ = (inner_[:, None, :] + lam_[None, :, None] * (Of_ - inner_)[:, None, :]).reshape(-1, 3)
    best_ = None; clear_ = np.inf
    for tag_, kid_, P_ in borders_:
        P_ = np.asarray(P_, float).reshape(-1, 3); kp_ = _KD(P_)
        touch_ = min(float(np.linalg.norm(P_ - S_[0], axis=1).min()), float(np.linalg.norm(P_ - S_[-1], axis=1).min())) < touch_mm
        dsb_ = kp_.query(segs_)[0].reshape(len(im_), -1)
        if touch_: dsb_[:, 0] = np.inf
        viol_ = dsb_ - th_[:, None]; i_, l_ = np.unravel_index(int(np.argmin(viol_)), viol_.shape); dmin_ = float(dsb_[i_, l_]); clear_ = min(clear_, float(viol_[i_, l_]))
        if dmin_ < float(th_[i_]):
            jb_ = int(kp_.query(inner_[i_])[1]); w_ = float(max(0.0, (P_[jb_] - inner_[i_]) @ Df_[i_]))
            if best_ is None or dmin_ < best_[0]: best_ = (dmin_, tag_, kid_, i_, w_)
    return best_, clear_
GUIDE_RECS = []; GUIDE_EDGES = []; CUTS = []; ROOM_LV = {}
if _raw_add or _raw_fil:
    for a_ in _raw_add:
        if not isinstance(a_, dict) or a_.get("face") is None or str(a_.get("role", "")).lower() not in ("guide", "split") or str(a_.get("kind", "")).upper() not in ("LINE", "ARC", "CUBIC") or a_.get("from") is None or a_.get("to") is None:
            K._fail("FAIL: _add entry %s is not {\"face\", \"role\": guide|split, \"kind\": LINE|ARC|CUBIC, \"from\", \"to\", \"why\"}" % str(a_)[:120])
        if len(str(a_.get("why", "")).strip()) < 3: K._fail("FAIL: _add line on face %s carries no reason" % a_.get("face"))
        if int(a_["face"]) < 0 or int(a_["face"]) >= len(PJ) or PJ[int(a_["face"])]["kind"] == "cap": K._fail("FAIL: _add: face %s is not a skin face" % a_.get("face"))
        if a_.get("span") is not None:
            if not a_.get("trace"): K._fail("FAIL: _add on face %s: \"span\" names the ORIGINAL faces a TRACED line is interpolated across (the region the design closes under it) - a LINE / ARC / CUBIC does not follow the surface: add \"trace\": true or drop \"span\"" % a_.get("face"))
            if not (a_["span"] == "face" or (isinstance(a_["span"], list) and len(a_["span"]) and all(str(x_).lstrip("-").isdigit() for x_ in a_["span"]))): K._fail("FAIL: _add on face %s: \"span\" is a list of ORIGINAL face numbers (the faces of the region the design closes under the trace - the step's line for the trace names the ones it follows); got %r" % (a_.get("face"), a_.get("span")))
    _chain_entries = []; _seen_lines6 = {}
    for f_ in _raw_fil:
        if isinstance(f_, dict) and f_.get("lines") is not None and f_.get("line") is None:
            ks_ = f_.get("lines")
            if not isinstance(ks_, list) or len(ks_) < 2 or not all(str(x_).lstrip("-").isdigit() for x_ in ks_): K._fail("FAIL: _fillets chain entry %s: \"lines\" is a list of two or more chain numbers in path order" % str(f_)[:120])
            if not f_.get("r") or len(str(f_.get("why", "")).strip()) < 3: K._fail("FAIL: _fillets chain %s needs \"r\" and a reason" % ks_)
            if f_.get("buried") is not None and not (isinstance(f_["buried"], list) and all(str(x_).lstrip("-").isdigit() for x_ in f_["buried"])): K._fail("FAIL: _fillets chain %s: \"buried\" is a list of ORIGINAL face numbers the blend buries (the vane's end face put into the crown's feature); got %r" % (ks_, f_.get("buried")))
            ks_ = [int(x_) for x_ in ks_]
            if len(set(ks_)) != len(ks_): K._fail("FAIL: _fillets chain %s names line(s) %s twice - a chain is a path of distinct lines (31bq OO, B41 (e))" % (ks_, sorted(set(x_ for x_ in ks_ if ks_.count(x_) > 1))))
            for k_ in ks_:
                if k_ in _seen_lines6: K._fail("FAIL: _fillets: line %d is a member of two chains (%s and %s) - one blend per line (31bq OO, B41 (e))" % (k_, _seen_lines6[k_], ks_))
                _seen_lines6[k_] = ks_
            for k_ in ks_:
                if k_ < 0 or k_ >= len(CH) or recs[k_]["rung"] == "WALL_DROPPED": K._fail("FAIL: _fillets chain: line %d is not a skin edge" % k_)
            for a_, b_ in zip(ks_[:-1], ks_[1:]):
                ja_ = set(int(x_) for x_ in (CH[a_].get("junctions") or []) if x_ is not None); jb_ = set(int(x_) for x_ in (CH[b_].get("junctions") or []) if x_ is not None)
                if not (ja_ & jb_): K._fail("FAIL: _fillets chain %s: lines %d and %d share no junction (network.json: %s / %s) - a chain is a path, each line meeting the next at a junction" % (ks_, a_, b_, sorted(ja_), sorted(jb_)))
            _chain_entries.append(f_)
    _raw_fil = [f_ for f_ in _raw_fil if not (isinstance(f_, dict) and f_.get("lines") is not None and f_.get("line") is None)]
    _in_chain = {int(x_) for c_ in _chain_entries for x_ in c_["lines"]}
    _dup = [f_ for f_ in _raw_fil if isinstance(f_, dict) and f_.get("line") is not None and str(f_["line"]).lstrip("-").isdigit() and int(f_["line"]) in _in_chain]
    if _dup:
        say("FILLET CHAIN: line(s) %s are chain members and single entries both - the chain takes them (one blend each, at the chain's R); the single entries are dropped" % sorted(int(f_["line"]) for f_ in _dup))
        _raw_fil = [f_ for f_ in _raw_fil if f_ not in _dup]
    for f_ in _raw_fil:
        if not isinstance(f_, dict) or f_.get("line") is None or not f_.get("r"): K._fail("FAIL: _fillets entry %s is not {\"line\": <chain>, \"r\": <mm>, \"why\"} (or a chain: {\"lines\": [...], \"r\", \"why\"})" % str(f_)[:120])
        if len(str(f_.get("why", "")).strip()) < 3: K._fail("FAIL: _fillets line %s carries no reason" % f_.get("line"))
        if int(f_["line"]) < 0 or int(f_["line"]) >= len(CH) or recs[int(f_["line"])]["rung"] == "WALL_DROPPED": K._fail("FAIL: _fillets: line %s is not a skin edge" % f_.get("line"))
        if f_.get("leg") is not None and not (str(f_["leg"]).strip().lower() == "all" or (str(f_["leg"]).strip().isdigit())):
            K._fail("FAIL: _fillets line %s: \"leg\" is \"all\" (every leg - each piece between the line's junctions and the split ends on it) or a leg number; got %r" % (f_.get("line"), f_.get("leg")))
    JPOS_ = np.array([j_["pos"] for j_ in NJ["junctions"]], float) if NJ.get("junctions") else np.zeros((0, 3))
    try: CORN_ = {p_["id"]: np.array(p_["xyz"], float) for p_ in corner_pts}
    except Exception: CORN_ = {}
    _mirA = bool(_mir0)
    if _mirA:
        MNa, MCa = K.mirror_plane(_mir0)
        grpA = {}
        for p_ in PJ:
            if p_["kind"] != "cap" and p_.get("grp") is not None: grpA.setdefault(p_["grp"], []).append(p_["patch"])
        def twinA(x):
            g = PJ[x].get("grp")
            if PJ[x]["kind"] == "cap" or g is None: return x
            m_ = [y for y in grpA.get(g, []) if y != x]; return m_[0] if m_ else x
    def _border_of(q):
        """the face's border edges (its skin chains + its wall stretches) as (tag, edge, samples)"""
        out = []
        for tag_, k_, e_ in face_edges(q): out.append((tag_, k_, e_, samp(e_, 0.05)))
        return out
    def _end_pt(spec, q, border, mirrored, role_=None, ai_=None, nm_=None):
        """an end on the face's border: a corner, a junction or a point snapped to the border (within ADD_SNAP); returns (point, cut)"""
        if isinstance(spec, str) and spec.startswith("c") and spec[1:].isdigit():
            if int(spec[1:]) not in CORN_: K._fail("FAIL: _add end %s: no such corner (CORNERS_*)" % spec)
            P_ = CORN_[int(spec[1:])]
        elif isinstance(spec, str) and spec.startswith("j") and spec[1:].isdigit():
            if int(spec[1:]) >= len(JPOS_): K._fail("FAIL: _add end %s: no such junction (network.json has %d)" % (spec, len(JPOS_)))
            P_ = JPOS_[int(spec[1:])]
        else:
            try: P_ = np.array([float(x) for x in (spec.split() if isinstance(spec, str) else spec)], float); assert P_.shape == (3,)
            except Exception: K._fail("FAIL: _add end %r is \"c<n>\", \"j<n>\" or [x, y, z]" % (spec,))
        if mirrored: P_ = K.reflect(P_[None, :], MNa, MCa)[0]
        if role_ == "split" and not (isinstance(spec, str) and spec[:1] in "cj" and spec[1:].isdigit()): _hp_refuse(P_, q, ai_, nm_, mirrored, ADD_SNAP)
        best = None
        for tag_, k_, e_, S_ in border:
            d_ = np.linalg.norm(S_ - P_, axis=1); i_ = int(np.argmin(d_))
            if best is None or d_[i_] < best[0]: best = (d_[i_], tag_, k_, e_, S_[i_], i_, len(S_))
        if best is None or best[0] > ADD_SNAP: K._fail("FAIL: _add on face %d: the end %s is %.2f mm from the face's border (ADD_SNAP %g) - an added line starts and ends on the border (31br A4: a GUIDE may also end on an EARLIER split of the same face - list that split before it; a split may not end on a split)" % (q, spec, best[0] if best else 99, ADD_SNAP))
        d0, tag_, k_, e_, Q_, i_, n_ = best
        at_end = i_ <= 1 or i_ >= n_ - 2
        return Q_, (None if at_end else (tag_, k_, Q_))
    _ADD_POLES = {}
    _TRACE_INFO = {}
    _TRACE_PF = {}
    def _draw_add(kind_, A_, B_, via_, trace_, face_=None, span_=None):
        if trace_: kind_ = "CUBIC"
        if kind_ == "LINE": return Part.LineSegment(V3(*A_), V3(*B_)).toShape()
        if kind_ == "ARC":
            if len(via_) != 1: K._fail("FAIL: _add ARC needs exactly one \"via\" point")
            return Part.Arc(V3(*A_), V3(*via_[0]), V3(*B_)).toShape()
        if trace_:
            # ORIGINAL
            # skin-source
            # geometry that was wanted to be kept
            n_ = max(8, int(np.linalg.norm(B_ - A_) / 0.5) + 1); S_ = A_[None, :] + np.linspace(0, 1, n_)[:, None] * (B_ - A_)[None, :]
            _TRACE_INFO.clear()
            _u_ = (B_ - A_) / max(float(np.linalg.norm(B_ - A_)), 1e-12); _st_ = float(np.linalg.norm(B_ - A_)) / max(n_ - 1, 1)
            _fmask = (_pid == int(face_)) if face_ is not None else None
            _Ff = F[_fmask] if (_fmask is not None and _fmask.any()) else None
            _Tall = _Ff if (_Ff is not None and len(_Ff) >= 4) else F
            _span = (sorted(set(int(x) for x in np.unique(FID_W[_fmask]) if int(x) >= 0)) if (FID_W is not None and _fmask is not None and _fmask.any()) else []) if span_ == "face" else sorted(set(int(x) for x in (span_ or []) if str(x).lstrip("-").isdigit()))
            _T_ = _Tall
            if _span and FID_W is not None and _Ff is not None and len(_Ff) >= 4:
                _T_ = _Ff[~np.isin(FID_W[_fmask], _span)]
            try: _onpl = bool(_mirA and np.linalg.norm(K.reflect(A_[None, :], MNa, MCa)[0] - A_) < 0.1 and np.linalg.norm(K.reflect(B_[None, :], MNa, MCa)[0] - B_) < 0.1)
            except Exception: _onpl = False
            _pnT = None
            try:
                if _onpl: _pnT = np.asarray(MNa, float) / max(float(np.linalg.norm(MNa)), 1e-12)
                elif _Tall is not None and len(_Tall) >= 4:
                    _nT = np.cross(Vu[_Tall[:, 1]] - Vu[_Tall[:, 0]], Vu[_Tall[:, 2]] - Vu[_Tall[:, 0]]); _nT = _nT / np.maximum(np.linalg.norm(_nT, axis=1), 1e-12)[:, None]
                    _nT = _nT * np.where(_nT @ _nT.sum(0) < 0, -1.0, 1.0)[:, None]; _nm = _nT.mean(0); _nm = _nm - float(_nm @ _u_) * _u_; _cx = np.cross(_u_, _nm)
                    _pnT = (_cx / float(np.linalg.norm(_cx))) if (float(np.linalg.norm(_cx)) > 1e-6 and float(np.linalg.norm(_nm)) > 0.2) else None
            except Exception: _pnT = None
            def _across(T__, ridge__):
                """per interior sample: the crossing nearest it of the plane normal to the line there - by the ridge's segments (a trace on the mirror plane) or by
                the face's own triangles; returns (points, crossed)"""
                Q__ = S_.copy(); hit__ = np.zeros(len(S_), bool)
                if ridge__ is not None:
                    if not len(ridge__): return Q__, hit__
                    a__ = ridge__[:, 0]; b__ = ridge__[:, 1]; sa__ = a__ @ _u_; sb__ = b__ @ _u_; lo__ = np.minimum(sa__, sb__); hi__ = np.maximum(sa__, sb__)
                    for i__ in range(1, len(S_) - 1):
                        c__ = float(S_[i__] @ _u_); m__ = (lo__ <= c__) & (hi__ >= c__)
                        if not m__.any(): continue
                        den__ = sb__[m__] - sa__[m__]; ok__ = np.abs(den__) > 1e-12
                        tt__ = np.where(ok__, (c__ - sa__[m__]) / np.where(ok__, den__, 1.0), 0.5)
                        X__ = a__[m__] + tt__[:, None] * (b__[m__] - a__[m__])
                        if _pnT is not None and TRACE_TUBE_MM > 0:
                            _lnT = np.abs((X__ - S_[i__]) @ _pnT)
                            if float(np.min(_lnT)) > TRACE_TUBE_MM: continue
                            X__ = X__[_lnT <= TRACE_TUBE_MM]
                        j__ = int(np.argmin(np.linalg.norm(X__ - S_[i__], axis=1))); Q__[i__] = X__[j__]; hit__[i__] = True
                    return Q__, hit__
                if not len(T__): return Q__, hit__
                sv__ = Vu[T__] @ _u_; lo__ = sv__.min(1); hi__ = sv__.max(1)
                for i__ in range(1, len(S_) - 1):
                    c__ = float(S_[i__] @ _u_); m__ = (lo__ <= c__) & (hi__ >= c__)
                    if not m__.any(): continue
                    sg__ = K.mesh_plane_section(Vu, T__[m__], _u_, c__)
                    if not len(sg__): continue
                    if _pnT is not None and TRACE_TUBE_MM > 0:
                        _lnS = np.abs((np.asarray(sg__, float).reshape(-1, 2, 3) - S_[i__]) @ _pnT); _keepS = np.minimum(_lnS[:, 0], _lnS[:, 1]) <= TRACE_TUBE_MM
                        if float(np.min(np.minimum(_lnS[:, 0], _lnS[:, 1]))) > TRACE_TUBE_MM: continue
                        sg__ = np.asarray(sg__, float).reshape(-1, 2, 3)[_keepS]
                    q__, _d__ = K.nearest_on_segments(S_[i__][None, :], sg__); Q__[i__] = q__[0]; hit__[i__] = True
                return Q__, hit__
            _how_ = "its face's own surface across the line (the plane normal to the line at each sample, within TRACE_TUBE_MM %g mm sideways of the line's own plane)" % TRACE_TUBE_MM; _ridge = False
            try:
                _rgA = K.mesh_plane_section(Vu, _Tall, MNa, MCa) if _onpl else None
                _ridge = bool(_onpl and _rgA is not None and len(_rgA))
                if _ridge: _how_ = "its face's section by the mirror plane (its ridge), across the line at each sample"
                _rg_ = (K.mesh_plane_section(Vu, _T_, MNa, MCa) if _span else _rgA) if _ridge else None
                _Sq, _hit = _across(_T_, _rg_ if _ridge else None)
                _hitA = _across(_Tall, _rgA if _ridge else None)[1] if _span else _hit
            except Exception as _exa:
                _Sq, _dq = K.closest_on_mesh(S_, Vu, F, kct); _hit = np.ones(len(S_), bool); _hitA = _hit; _how_ = "the source mesh (its face's section failed: %s)" % str(_exa)[:60]
                if not bool((getattr(K, "CLOSEST_LAST", None) or {}).get("exact", True)): _how_ += " (NOT EXACT: the exact pass failed - %s - the nearest-64 point stands for the surface here; 31bq R7f)" % str((getattr(K, "CLOSEST_LAST", None) or {}).get("why", "?"))[:100]
            _gap_ = ~_hit; _gap_[0] = False; _gap_[-1] = False
            _dep_ = np.where(_hit, np.linalg.norm(_Sq - S_, axis=1), 0.0); _dep_[0] = 0.0; _dep_[-1] = 0.0
            _TRACE_INFO["on"] = _how_; _TRACE_INFO.update({"a": [float(x) for x in A_], "u": [float(x) for x in _u_], "len": float(np.linalg.norm(B_ - A_)), "step": float(_st_), "face": (int(face_) if face_ is not None else None),
                                                       "span": _span, "depth_mm": round(float(_dep_.max()), 3), "depth_at": [round(float(x), 2) for x in _Sq[int(np.argmax(_dep_))]]})
            try:
                if "pf" not in _TRACE_PF:
                    try: _TRACE_PF["pf"] = {int(r__["face"]): int(r__.get("on") or 0) for r__ in json.load(open(os.path.join(SK, "points_faces.json"), encoding="utf-8"))}
                    except Exception: _TRACE_PF["pf"] = {}
                _deep = np.nonzero(_hit & (_dep_ > LINE_OFF_MAX))[0]
                if len(_deep) and FID_W is not None:
                    _tj = K.closest_on_mesh(_Sq[_deep], Vu, F, kct, return_tri=True)[2]; _fo = {}
                    for _o, _dd in zip(FID_W[_tj], _dep_[_deep]): _fo[int(_o)] = max(_fo.get(int(_o), 0.0), float(_dd))
                    _TRACE_INFO["follows"] = [[o_, round(d_, 2)] for o_, d_ in sorted(_fo.items(), key=lambda x_: -x_[1])]
                    _TRACE_INFO["follows_nopoint"] = [o_ for o_, d_ in sorted(_fo.items(), key=lambda x_: -x_[1]) if _TRACE_PF["pf"].get(int(o_)) == 0]
                if _span and FID_W is not None and _Ff is not None:
                    _TRACE_INFO["span_missing"] = [x_ for x_ in _span if not bool(np.isin(x_, FID_W[_fmask]).any())]
                elif _span and FID_W is None: _TRACE_INFO["span_missing"] = list(_span)
            except Exception: pass
            try:
                if _onpl: _pn6 = MNa
                else:
                    _tn6 = K.closest_on_mesh(S_, Vu, _Tall, return_tri=True)[2]
                    _nn6 = np.cross(Vu[_Tall[_tn6, 1]] - Vu[_Tall[_tn6, 0]], Vu[_Tall[_tn6, 2]] - Vu[_Tall[_tn6, 0]]); _nn6 = _nn6 / np.maximum(np.linalg.norm(_nn6, axis=1), 1e-12)[:, None]
                    _nn6 = _nn6 * np.where(_nn6 @ _nn6.sum(0) < 0, -1.0, 1.0)[:, None]; _nm6 = _nn6.mean(0); _nm6 = _nm6 - float(_nm6 @ _u_) * _u_; _cx6 = np.cross(_u_, _nm6)
                    _pn6 = (_cx6 / max(float(np.linalg.norm(_cx6)), 1e-12)) if float(np.linalg.norm(_nm6)) > 0.2 else None
                if _pn6 is not None:
                    _ln6 = np.where(_hit, np.abs((_Sq - A_) @ _pn6), 0.0); _TRACE_INFO.update({"lean_mm": round(float(_ln6.max()), 3), "lean_at": [round(float(x), 2) for x in _Sq[int(np.argmax(_ln6))]]})
            except Exception: pass
            if _gap_.any():
                _gi = list(np.nonzero(_gap_)[0]); _runs = []; _ra = _rb = int(_gi[0])
                for _ix in _gi[1:] + [None]:
                    if _ix is not None and int(_ix) == _rb + 1: _rb = int(_ix); continue
                    _runs.append((_ra, _rb))
                    if _ix is not None: _ra = _rb = int(_ix)
                _gl = []
                for _ra, _rb in _runs:
                    _Ga, _Gb = S_[_ra], S_[_rb]; _fm = _om = None
                    try:
                        _jm = int(K.closest_on_mesh(0.5 * (_Ga + _Gb), Vu, F, kct, return_tri=True)[2][0]); _fm = int(_pid[_jm]); _om = (int(FID_W[_jm]) if FID_W is not None else None)
                    except Exception: pass
                    _nst = int(_hitA[_ra:_rb + 1].sum()) if _span else 0
                    _gl.append({"gap_mm": round(float(np.linalg.norm(_Gb - _Ga)) + _st_, 2), "gap_from": [round(float(x), 2) for x in _Ga], "gap_to": [round(float(x), 2) for x in _Gb], "gap_face": _fm, "gap_orig": _om,
                                "t0": round(float((_Ga - A_) @ _u_), 3), "t1": round(float((_Gb - A_) @ _u_), 3), "samples": int(_rb - _ra + 1), "stated": bool(_span and _nst == int(_rb - _ra + 1)), "stated_samples": _nst})
                _TRACE_INFO["gaps"] = _gl
                _TRACE_INFO.update({k_: v_ for k_, v_ in max(_gl, key=lambda g_: g_["gap_mm"]).items() if k_.startswith("gap_")})
            S_ = _Sq[~_gap_]
            S_[0] = A_; S_[-1] = B_
            if _onpl and not _ridge:
                try: S_ = 0.5 * (S_ + K.reflect(S_, MNa, MCa)); S_[0] = A_; S_[-1] = B_
                except Exception: pass
            try:
                _kp = sorted(set([0] + [i__ for i__ in range(1, len(S_) - 1) if np.linalg.norm(S_[i__] - S_[i__ - 1]) > 0.05] + [len(S_) - 1]))
                cv_ = Part.BSplineCurve(); cv_.interpolate([V3(*S_[i__]) for i__ in _kp]); return cv_.toShape()
            except Exception:
                cv_, _, _, _, _ = fit_bspline(S_, 4); return cv_.toShape()
        pts_ = [V3(*A_)] + [V3(*np.asarray(v, float)) for v in via_] + [V3(*B_)]
        if len(pts_) <= 4:
            cv_ = Part.BSplineCurve(); cv_.interpolate(pts_); return cv_.toShape()
        _P6 = np.array([[p.x, p.y, p.z] for p in pts_]); _np6 = 4
        try: _np6 = max(4, min(8, len(_P6), int(_ADD_POLES.get("n") or 4)))      # 31br D5b  more poles than points
        except Exception: _np6 = 4
        cv_, _, dev6_, _, _ = fit_bspline(_P6, _np6); _d6 = float(np.max(dev6_)) if len(dev6_) else 0.0
        _ADD_POLES["dev"] = _d6; _ADD_POLES["used"] = _np6
        if _d6 > ADD_VIA_TOL:
            K._fail("FAIL: _add %s with %d via points: one %s through them misses them by %.2f mm (ADD_VIA_TOL %g) - a line is drawn THROUGH the points you give it or not at all: fewer via points (a cubic takes two), or \"poles\": 5..8 on the entry (a B-spline with that many poles; the WIRE frames label it by its poles), or split the line (31br D6)"
                    % (kind_, len(via_), "cubic (4 poles)" if _np6 == 4 else "B-spline of %d poles" % _np6, _d6, ADD_VIA_TOL))
        return cv_.toShape()
    for ai_, a_ in enumerate(_raw_add):
        q0 = int(a_["face"]); sides_ = [(q0, False)]
        if _mirA and twinA(q0) != q0: sides_.append((twinA(q0), True))
        elif _mirA and not a_.get("own_mirror"):
            # is its own mirror
            try:
                _pa = [np.array([float(x) for x in (v.split() if isinstance(v, str) else v)], float) if not (isinstance(v, str) and v[:1] in "cj") else None for v in (a_["from"], a_["to"])]
                _own = all(p is not None for p in _pa) and (np.linalg.norm(K.reflect(_pa[0][None, :], MNa, MCa)[0] - _pa[1]) < 0.1 or np.linalg.norm(K.reflect(_pa[0][None, :], MNa, MCa)[0] - _pa[0]) < 0.1 and np.linalg.norm(K.reflect(_pa[1][None, :], MNa, MCa)[0] - _pa[1]) < 0.1)
            except Exception: _own = False
            if not _own: sides_.append((q0, True))
        for q_, mir_ in sides_:
            border_ = _border_of(q_)
            if str(a_.get("role", "")).lower() == "guide":
                for r4_ in GUIDE_RECS:
                    if int(r4_["face"]) == int(q_) and r4_["role"] == "split":
                        border_ = border_ + [("split", r4_["edge"], GUIDE_EDGES[r4_["edge"]], samp(GUIDE_EDGES[r4_["edge"]], 0.05))]
            A_, cutA = _end_pt(a_["from"], q_, border_, mir_, role_=str(a_.get("role", "")).lower(), ai_=ai_, nm_="from"); B_, cutB = _end_pt(a_["to"], q_, border_, mir_, role_=str(a_.get("role", "")).lower(), ai_=ai_, nm_="to")
            for _nm4, _c4 in (("from", cutA), ("to", cutB)):
                if _c4 is not None and _c4[0] == "split":
                    say("   _add guide entry %d%s on face %d: its '%s' end lies on the earlier SPLIT (edge %d) of this face - allowed since 31br A4: the build splits first, the guide pulls that piece's surface" % (ai_, " (mirrored)" if mir_ else "", q_, _nm4, _c4[1]))
            via_ = [np.asarray(v, float) for v in (a_.get("via") or [])]
            if mir_: via_ = [K.reflect(v[None, :], MNa, MCa)[0] for v in via_]
            _ADD_POLES.clear(); _ADD_POLES["n"] = a_.get("poles")
            try: e_ = _draw_add(str(a_["kind"]).upper(), A_, B_, via_, bool(a_.get("trace")), face_=int(q_), span_=a_.get("span"))
            except Exception as ex_: K._fail("FAIL: _add on face %d could not be drawn: %s" % (q_, str(ex_)[:100]))
            rec_ = {"face": q_, "role": str(a_["role"]).lower(), "kind": str(a_["kind"]).upper(), "edge": len(GUIDE_EDGES), "why": a_.get("why", ""), "trace": bool(a_.get("trace")),
                    "via_dev_mm": _ADD_POLES.get("dev"), "poles": _ADD_POLES.get("used"), "ends": [[float(x) for x in A_], [float(x) for x in B_]], "mirror_of": (ai_ if mir_ else None), "entry": ai_, "add_id": (str(a_.get("id") or "").strip() or _new_add_id(a_, ai_)), "trace_info": (dict(_TRACE_INFO) if a_.get("trace") else None), "span": ("face" if a_.get("span") == "face" else (sorted(int(x_) for x_ in a_["span"]) if a_.get("span") else None))}
            if _ADD_POLES.get("dev") is not None: say("   _add %s on face %d%s: %d via points, one %s through them - %.2f mm off them at most (ADD_VIA_TOL %g; 31br D6)" % (rec_["kind"], q_, " (mirrored)" if mir_ else "", len(via_), "cubic" if _ADD_POLES.get("used") == 4 else "B-spline of %s poles" % _ADD_POLES.get("used"), float(_ADD_POLES["dev"]), ADD_VIA_TOL))
            if a_.get("trace"):
                ti6_ = rec_["trace_info"] or {}; gs6_ = ti6_.get("gaps") or []; st6_ = [g_ for g_ in gs6_ if g_.get("stated")]; rg6_ = [g_ for g_ in gs6_ if not g_.get("stated")]; np6_ = ti6_.get("follows_nopoint") or []
                say("   traced _add %s on face %d%s: follows %s - at most %.2f mm off its chord (at %s)%s%s%s%s%s%s" % (rec_["kind"], q_, " (mirrored)" if mir_ else "", ti6_.get("on", "its face"), float(ti6_.get("depth_mm") or 0.0), ti6_.get("depth_at"),
                    ("; more than LINE_OFF_MAX %g off it on original face(s) %s" % (LINE_OFF_MAX, ", ".join("%d (%.2f mm%s)" % (o_, d_, ", NO point of its own - the points dropped it" if o_ in np6_ else "") for o_, d_ in ti6_["follows"][:6]))) if ti6_.get("follows") else "",
                    ("; it leaves its line's own plane by up to %.2f mm (at %s) - its face is not under the line there and the trace follows the face round it: look at it in the WIRE frames, or end / split the line there" % (float(ti6_["lean_mm"]), ti6_.get("lean_at"))) if float(ti6_.get("lean_mm") or 0.0) > LINE_OFF_MAX else "",
                    ("; interpolated across the entry's span %s for %.1f mm" % (ti6_.get("span"), sum(g_["gap_mm"] for g_ in st6_))) if st6_ else "",
                    ("; %d stretch(es) where no triangle of its face crosses the line's normal plane (%.1f mm in all) - interpolated across" % (len(rg6_), sum(g_["gap_mm"] for g_ in rg6_))) if rg6_ else "",
                    (" - original face(s) %s have NO point of their own (the points dropped them into face %d): where the design CLOSES that region (a slot or a hole the points dropped), name them in the entry's \"span\" and the trace is interpolated across them; where it does not, this is the face's own shape (the kit does not choose)" % (np6_, q_)) if (np6_ and not ti6_.get("span")) else "",
                    ("; the entry's span id(s) %s lie on no triangle of face %d (a wrong id, or the twin side's: list both sides' ids)" % (ti6_["span_missing"], q_)) if ti6_.get("span_missing") else ""))
            _dup = next((r2_ for r2_ in GUIDE_RECS if int(r2_["face"]) == int(q_) and r2_["role"] == rec_["role"] and (
                (np.linalg.norm(np.asarray(r2_["ends"][0]) - A_) < 0.1 and np.linalg.norm(np.asarray(r2_["ends"][1]) - B_) < 0.1) or
                (np.linalg.norm(np.asarray(r2_["ends"][0]) - B_) < 0.1 and np.linalg.norm(np.asarray(r2_["ends"][1]) - A_) < 0.1))), None)
            if _dup is not None:
                say("   _add entry %d%s on face %d is the same %s as entry %d%s (its ends within 0.1 mm) - one kept" % (ai_, " (mirrored)" if mir_ else "", q_, rec_["role"], _dup["entry"], " (mirrored)" if _dup.get("mirror_of") is not None else ""))
                continue
            for c_ in (cutA, cutB):
                if c_ is not None and rec_["role"] == "split":
                    tag_, k_, Q_ = c_
                    if tag_ == "wall":
                        near_ = sorted(((float(np.linalg.norm(np.asarray(P_, float) - np.asarray(Q_, float))), int(cid_)) for cid_, P_ in CORN_.items()))[:3]
                        K._fail("FAIL: _add split on face %d (entry %s) ends INSIDE a wall edge of the edit region at (%.2f, %.2f, %.2f) - the caps are the body's own section faces and are never cut (L114): end it at a corner on that wall (nearest: %s) or at a junction on the wall (j<n>)"
                                % (q_, ai_, Q_[0], Q_[1], Q_[2], ", ".join("c%d (%.1f mm away)" % (cid_, d_) for d_, cid_ in near_) or "none listed - CORNERS_*"))
                    CUTS.append({"face": q_, "edge": len(GUIDE_EDGES), "what": tag_, "chain": (k_ if tag_ == "chain" else None), "wall": (list(k_) if tag_ == "wall" else None), "at": [float(x) for x in Q_]})
            GUIDE_EDGES.append(e_); GUIDE_RECS.append(rec_)
    FIL_RECS = []
    if _raw_fil or _chain_entries:
        live_ = [k for k in range(len(CH)) if recs[k]["rung"] != "WALL_DROPPED"]
        centF = {k: samp(edges_out[k], 0.2).mean(0) for k in live_}
        def _own_ends(k__):
            try:
                _Sk = samp(edges_out[k__], 0.3); _Sf = samp(edges_out[k__], 0.02); _r = K.reflect(_Sk, MNa, MCa)
                return float(cKDTree(_Sf).query(_r)[0].max()) <= 0.1
            except Exception: return True
        def _twin_line(k0):
            if not _mirA: return None
            p_, q_ = [int(x) for x in CH[k0]["pair"]]; tk_ = frozenset((twinA(p_), twinA(q_))); mc_ = K.reflect(centF[k0][None, :], MNa, MCa)[0]
            if np.linalg.norm(mc_ - centF[k0]) < 0.5 and frozenset((p_, q_)) == tk_ and _own_ends(k0): return k0
            cands_ = [k2 for k2 in live_ if frozenset(int(x) for x in CH[k2]["pair"]) == tk_ and k2 != k0]
            if not cands_: return None
            k2 = min(cands_, key=lambda j: np.linalg.norm(centF[j] - mc_))
            return k2 if np.linalg.norm(centF[k2] - mc_) < 1.5 else None
        _cid = 0
        def _sok_of(f_, line_, master_=None):
            """31bs K29 (2026-11-03): an entry's "sharp_ok" for ONE record - True accepts its line(s) and their kit-mirrored twins; a list names members by number (a twin
            is accepted when its master is - the file names the master side's numbers); anything else is False. Decided here, where the record is built, and never
            re-keyed from the raw file by line number afterwards (a kit-mirrored twin, a carried file and the FILLETS env lost it - W49)."""
            v_ = f_.get("sharp_ok")
            if isinstance(v_, list):
                try: s_ = set(int(x_) for x_ in v_ if str(x_).lstrip("-").isdigit())
                except Exception: s_ = set()
                return (int(line_) in s_) or (master_ is not None and int(master_) in s_)
            return bool(v_)
        _written_ = {}      # none of the
        for f_ in _chain_entries:
            for x_ in f_["lines"]: _written_.setdefault(int(x_), "chain %s" % [int(y_) for y_ in f_["lines"]])
        for f_ in _raw_fil: _written_.setdefault(int(f_["line"]), "line %d" % int(f_["line"]))
        for f_ in _chain_entries:
            ks_ = [int(x_) for x_ in f_["lines"]]
            for i_, k_ in enumerate(ks_): FIL_RECS.append(dict({"line": k_, "r": float(f_["r"]), "sharp_ok": _sok_of(f_, k_), "why": f_.get("why", ""), "mirror_of": None, "chain": _cid, "pos": i_, "n": len(ks_)}, **({"buried": [int(x_) for x_ in f_["buried"]]} if f_.get("buried") else {})))
            say("FILLET CHAIN %d (31bp): lines %s blended as ONE chain at R %g - full R to every shared junction, a corner patch there; the taper only at its two free ends" % (_cid, ks_, float(f_["r"])))
            if _mirA:
                tw_ = [_twin_line(k_) for k_ in ks_]
                if set(x_ for x_ in tw_ if x_ is not None) == set(ks_):
                    _m31 = []
                    for i_, k_ in enumerate(ks_):      # mirror_of
                        k2 = tw_[i_]
                        try:
                            if k2 is not None and int(k2) != int(k_) and (float(centF[k_] @ MNa) - MCa) * MSIDE_ < (float(centF[int(k2)] @ MNa) - MCa) * MSIDE_: FIL_RECS[len(FIL_RECS) - len(ks_) + i_]["mirror_of"] = int(k2); FIL_RECS[len(FIL_RECS) - len(ks_) + i_]["sharp_ok"] = _sok_of(f_, k_, int(k2)); FIL_RECS[len(FIL_RECS) - len(ks_) + ks_.index(int(k2))]["sharp_ok"] = _sok_of(f_, int(k2), k_); _m31.append("%d <- %d" % (k_, int(k2)))
                        except Exception: pass
                    say("   chain %d is its own mirror (its lines' twins are its own lines) - one chain%s" % (_cid, ("; the members off the master side take their master-side twins as masters: %s" % ", ".join(_m31)) if _m31 else ""))
                elif any(x_ is None for x_ in tw_): say("   chain %d: no mirrored chain - line(s) %s have no twin within 1.5 mm; decide the other side's chain by name" % (_cid, [k_ for k_, x_ in zip(ks_, tw_) if x_ is None]))
                elif any(int(k2) in _written_ for k2 in tw_):
                    # over the
                    _ws_ = sorted(set(int(k2) for k2 in tw_ if int(k2) in ks_)); _wo_ = sorted(set(int(k2) for k2 in tw_ if int(k2) in _written_ and int(k2) not in ks_)); _m31 = []
                    for i_, k_ in enumerate(ks_):
                        k2 = int(tw_[i_])
                        try:
                            if k2 in _wo_ and (float(centF[k_] @ MNa) - MCa) * MSIDE_ < (float(centF[k2] @ MNa) - MCa) * MSIDE_: FIL_RECS[len(FIL_RECS) - len(ks_) + i_]["mirror_of"] = k2; FIL_RECS[len(FIL_RECS) - len(ks_) + i_]["sharp_ok"] = _sok_of(f_, k_, k2); _m31.append("%d <- %d" % (k_, k2))
                        except Exception: pass
                    say("   chain %d: its mirror - lines %s - is NOT added by the kit: %s (31bq R5f, B41 (e))%s" % (_cid, tw_, "; ".join(x_ for x_ in (
                        ("line(s) %s are this entry's own - decide the foot as ONE chain through the plane, or the other side by name" % _ws_) if _ws_ else "",
                        ("line(s) %s are decided by name in another entry (%s) - that entry is the other side" % (_wo_, ", ".join(sorted(set(_written_[x_] for x_ in _wo_))))) if _wo_ else "") if x_),
                        ("; the members off the master side take their written twins as masters: %s" % ", ".join(_m31)) if _m31 else ""))
                    _left9 = sorted(set(int(k2) for k2 in tw_ if int(k2) not in _written_))
                    if _left9: say("   chain %d: its mirror line(s) %s are decided by NO entry - they stay SHARP on the other side of a symmetric piece: write them (the foot as ONE chain through the plane, or the other side's chain whole by name) (31bq R7W, B1 9)" % (_cid, _left9))
                else:
                    _mb9 = len(FIL_RECS) - len(ks_)
                    for i_, k2 in enumerate(tw_): FIL_RECS[_mb9 + i_]["sharp_ok"] = _sok_of(f_, ks_[i_], int(k2))
                    _cid += 1
                    for i_, k2 in enumerate(tw_): FIL_RECS.append(dict({"line": int(k2), "r": float(f_["r"]), "sharp_ok": _sok_of(f_, int(k2), ks_[i_]), "why": f_.get("why", ""), "mirror_of": ks_[i_], "kit_mirror": True, "chain": _cid, "pos": i_, "n": len(tw_)}, **({"buried": [int(x_) for x_ in f_["buried"]]} if f_.get("buried") else {})))
                    say("   chain %d: its mirror - lines %s%s" % (_cid, tw_, ("; its \"buried\" ids are the master's %s - list BOTH sides' end faces in the entry, the kit does not mirror original-face ids (31bq B42)" % sorted(int(x_) for x_ in f_["buried"])) if f_.get("buried") else ""))
            _cid += 1
        for f_ in _raw_fil:
            k0 = int(f_["line"]); FIL_RECS.append(dict({"line": k0, "r": float(f_["r"]), "sharp_ok": _sok_of(f_, k0), "why": f_.get("why", ""), "mirror_of": None}, **({"leg": f_["leg"]} if f_.get("leg") is not None else {}), **({"buried": [int(x_) for x_ in f_["buried"]]} if f_.get("buried") else {})))
            if _mirA:
                p_, q_ = [int(x) for x in CH[k0]["pair"]]; tk_ = frozenset((twinA(p_), twinA(q_))); mc_ = K.reflect(centF[k0][None, :], MNa, MCa)[0]
                cands_ = [k2 for k2 in live_ if frozenset(int(x) for x in CH[k2]["pair"]) == tk_ and k2 != k0]
                if np.linalg.norm(mc_ - centF[k0]) < 0.5 and frozenset((p_, q_)) == tk_ and _own_ends(k0): say("   fillet line %d lies on the mirror plane - it is its own twin (one blend)" % k0); cands_ = []
                if cands_:
                    k2 = min(cands_, key=lambda j: np.linalg.norm(centF[j] - mc_))
                    if np.linalg.norm(centF[k2] - mc_) < 1.5 and int(k2) in _written_:
                        try:
                            if (float(centF[k0] @ MNa) - MCa) * MSIDE_ < (float(centF[int(k2)] @ MNa) - MCa) * MSIDE_: FIL_RECS[-1]["mirror_of"] = int(k2); FIL_RECS[-1]["sharp_ok"] = _sok_of(f_, k0, int(k2))
                        except Exception: pass
                        say("   fillet line %d: its mirror twin %d is decided by name too (%s) - NOT mirrored again by the kit (31bq R5f, B41 (e))%s" % (k0, int(k2), _written_[int(k2)], (" - line %d takes %d as its master" % (k0, int(k2))) if FIL_RECS[-1].get("mirror_of") is not None else ""))
                    elif np.linalg.norm(centF[k2] - mc_) < 1.5: FIL_RECS[-1]["sharp_ok"] = _sok_of(f_, k0, k2); FIL_RECS.append(dict({"line": k2, "r": float(f_["r"]), "sharp_ok": _sok_of(f_, k2, k0), "why": f_.get("why", ""), "mirror_of": k0, "kit_mirror": True}, **({"leg": f_["leg"]} if f_.get("leg") is not None else {}), **({"buried": [int(x_) for x_ in f_["buried"]]} if f_.get("buried") else {})))
        _cnt6 = {}
        for fr_ in FIL_RECS: _cnt6[int(fr_["line"])] = _cnt6.get(int(fr_["line"]), 0) + 1
        _twice6 = sorted(k_ for k_, n_ in _cnt6.items() if n_ > 1)
        if _twice6: K._fail("FAIL: _fillets: line(s) %s are decided TWICE - one blend per line: remove the repeated entry (a line written as two single entries, or as a single entry and a kit mirror) (31bq R5f, B41 (e))" % _twice6)
    # A FILLET NEEDS ROOM
    # kit measure
    # fillets.json  skin-build
    ROOM_DEF = (("TAPER_X", "3"), ("TAPER_MIN", "1.0"), ("FIL_TAPER", "1"), ("THIN_MM", "0.3"), ("CREASE_MIN_DEG", "8"), ("BURIED_MIN", "0.3"), ("BURIED_REACH", "2.0"), ("FIL_SMOOTH_MM", "1.5"))
    if FIL_RECS: ROOM_LV = {k_: {"value": (str(os.environ.get(k_, "")).strip() or d_), "default": d_, "set": bool(str(os.environ.get(k_, "")).strip())} for k_, d_ in ROOM_DEF}
    if FIL_RECS:
        try:
            THIN_ROOM = float(os.environ.get("THIN_MM", "0.3") or 0.3); CREASE_MIN_W = float(os.environ.get("CREASE_MIN_DEG", "8") or 8)
            FIL_TAPER_W = os.environ.get("FIL_TAPER", "1") != "0"; TAPER_X_W = float(os.environ.get("TAPER_X", "3") or 3); TAPER_MIN_W = float(os.environ.get("TAPER_MIN", "1.0") or 1.0)
            _Cn_all = Vu[F].mean(1)
            _SAID9 = set()
            FIL_SMOOTH_W = float(os.environ.get("FIL_SMOOTH_MM", "1.5") or 1.5); _SAIDN = set()
            def _nrm_at(f_, S_):
                """31bp fix 9 / 31bq R7W (fix-wires-normals, the plan's F.5b): THE BUILD'S NORMAL at each sample of the line (sk_build _fillet_lines' _local_normals,
                573-596) - the face's own sheet (sk_lib.local_face_normals: a thin / wrapping face's far side left out); on an ORIGINAL face (kind orig with its
                original face, not moved off its surface by a decided line - DEMOTE, which skin-build reads from wires_demote.json and builds as changed) its own
                SURFACE's normal at each sample, signed by the sheet there; on every other face the sheet's normals SMOOTHED along the line over FIL_SMOOTH_MM
                (a gaussian, sigma max(0.5, FIL_SMOOTH_MM / the samples' median step), mode nearest), as the build lays its offset lines. The raw per-sample mesh
                normals had read the changed face 20 / 3 of b27b114's 29 / 114 25.6-28.4 deg off the build's at a sample (beta 83 / t 1.32 against the build's
                69 / 1.03 - verify-wires-M7). An original surface is read however far it lies from the line, as the build reads it (sk_build 575-585 has no reach
                test - an original surface far from its border is the build's own to decide); where its normals cannot be taken the smoothed sheet stands, said
                once per face - the build's own fallback (sk_build 586-587). (31bq R7W verify-wires-normals: the JMOVE_MAX fallback removed - a lever the build never reads)"""
                _nf, out_, _inf9 = K.local_face_normals(Vu, F, _pid, f_, S_)
                if out_ is not None and _inf9.get("excluded") and f_ not in _SAID9:
                    _SAID9.add(f_); say("   fillet room: face %d is thin or wraps beside the line - %d of its nearest mesh triangles face the other way, left out of its normal (fix 9)" % (f_, _inf9["excluded"]))
                if out_ is None: return out_
                S_ = np.asarray(S_, float)
                if PJ[f_]["kind"] == "orig" and PJ[f_].get("face") is not None and f_ not in DEMOTE:      # ORIGINAL
                    try:
                        _So = BF[int(PJ[f_]["face"])].Surface; _ns = []
                        for i_, s_ in enumerate(S_):
                            _uu, _vv = _So.parameter(V3(*s_)); _nn = _So.normal(_uu, _vv)
                            _v = np.array([_nn.x, _nn.y, _nn.z], float); _v = _v / max(float(np.linalg.norm(_v)), 1e-9)
                            _ns.append(_v if float(_v @ out_[i_]) >= 0 else -_v)
                        return np.array(_ns)
                    except Exception as _exn:
                        if f_ not in _SAIDN:
                            _SAIDN.add(f_); say("   fillet room: face %d is an original face but its original surface %d's normals could not be taken (%s) - its sheet's normals, smoothed along the line, stand here (skin-build's own fallback - sk_build 586-587)" % (f_, int(PJ[f_]["face"]), str(_exn)[:60]))
                if FIL_SMOOTH_W > 0 and len(S_) > 4:
                    from scipy.ndimage import gaussian_filter1d as _gfn
                    _ds = float(np.median(np.linalg.norm(np.diff(S_, axis=0), axis=1))) or 0.3
                    out_ = np.stack([_gfn(out_[:, c_], max(0.5, FIL_SMOOTH_W / _ds), mode="nearest") for c_ in range(3)], 1)
                    out_ = out_ / np.maximum(np.linalg.norm(out_, axis=1), 1e-9)[:, None]
                return out_
            say("   fillet room: normals as the build's - smoothed along the line over FIL_SMOOTH_MM %g on changed faces; the original surface's own on original faces (31bq R7W fix-wires-normals)" % FIL_SMOOTH_W)
            BURIED_MIN_W = float(os.environ.get("BURIED_MIN", "0.3") or 0.3); _SAID38 = set()
            def _nrm_buried(f_, S_, bur_):
                """31bq B38: the host face's normals beside a buried crease - the buried faces' triangles are NOT read (the lip's mesh faces up, the crown faces down);
                where nothing unburied is near, the host's own unburied original surface stands (fix 11's rule, said)"""
                if bur_ and FID_W is None and "nofid" not in _SAID38:
                    _SAID38.add("nofid"); say("   fillet room: \"buried\" %s given but regions.npz carries no face index (fid) - the mesh stands as it is; run skin-regions again on this source" % sorted(bur_))
                if FID_W is None or not bur_: return _nrm_at(f_, S_), None
                pidb_ = np.array(_pid, dtype=int); pidb_[np.isin(FID_W, list(bur_))] = -1
                _nf, out_, _inf = K.local_face_normals(Vu, F, pidb_, f_, S_)
                Tf_ = np.nonzero(_pid == f_)[0]; Cf_ = Vu[F[Tf_]].mean(1) if len(Tf_) else np.zeros((0, 3))
                share_ = 0.0
                if len(Tf_):
                    _d1, _j1 = K.knn(Cf_, S_, 1); _j1 = np.asarray(_j1, int).reshape(-1); _d1 = np.asarray(_d1, float).reshape(-1)
                    near_ = _d1 < 2.5; share_ = float((np.isin(FID_W[Tf_[_j1]], list(bur_)) & near_).sum()) / max(1, int(near_.sum())) if near_.any() else 0.0
                if share_ < BURIED_MIN_W: return _nrm_at(f_, S_), share_
                if out_ is not None and len(out_) == len(S_) and float((_inf or {}).get("nearest_mm") or 0.0) <= float(os.environ.get("BURIED_REACH", "2.0") or 2.0):
                    if f_ not in _SAID38: _SAID38.add(f_); say("   fillet room: face %d's mesh beside the line is the BURIED face(s) %s (%.0f %% of the near samples) - its normals read from its unburied triangles only (31bq B38)" % (f_, sorted(bur_), 100 * share_))
                    return out_, share_
                # recorded
                cands_ = [int(x_) for x_ in np.unique(FID_W[Tf_]) if int(x_) >= 0 and int(x_) not in bur_]
                pj_ = PJ[f_].get("face") if PJ[f_].get("face") is not None else PJ[f_].get("face_src")
                if pj_ is not None and int(pj_) in cands_: cands_ = [int(pj_)] + [c_ for c_ in cands_ if c_ != int(pj_)]
                for c_ in cands_:
                    try:
                        S_o = BF[int(c_)].Surface; ns_ = []; dd_ = []
                        for s_ in S_:
                            uu_, vv_ = S_o.parameter(V3(*s_)); pt_ = S_o.value(uu_, vv_); nn_ = S_o.normal(uu_, vv_); v_ = np.array([nn_.x, nn_.y, nn_.z]); ns_.append(v_ / max(np.linalg.norm(v_), 1e-9)); dd_.append(float(pt_.distanceToPoint(V3(*s_))))
                        if float(np.median(dd_)) > float(os.environ.get("BURIED_REACH", "2.0") or 2.0): continue
                        ns_ = np.array(ns_)
                        if str(BF[int(c_)].Orientation) == "Reversed": ns_ = -ns_
                        say("   fillet room: face %d's mesh beside the line is the BURIED face(s) %s's (%.0f %% of the samples) - its own unburied original %d stands for it (fix 11)" % (f_, sorted(bur_), 100 * share_, int(c_)))
                        return ns_, share_
                    except Exception: continue
                if ("noreach", f_) not in _SAID38:
                    _SAID38.add(("noreach", f_)); say("   fillet room: face %d's mesh beside the line is the BURIED face(s) %s's (%.0f %% of the samples) and NO unburied surface of it reaches the line within BURIED_REACH %s mm - the room here is read off the buried face itself, an estimate that cannot hold: skin-build refuses this blend by name (make the host's surface reach the crease, or check the \"buried\" ids)" % (f_, sorted(bur_), 100 * share_, os.environ.get("BURIED_REACH", "2.0") or "2.0"))
                return _nrm_at(f_, S_), share_
            def _legs_of(k0_, S_):
                """31bq B37: a fillet decided PER LEG is measured per leg - the line's samples cut where a split ends on it (CUTS with this chain)"""
                cuts_ = [np.asarray(c_["at"], float) for c_ in CUTS if c_.get("chain") == k0_ and c_.get("at") is not None]
                if not cuts_: return [S_]
                idx_ = sorted(set(int(np.argmin(np.linalg.norm(S_ - c_, axis=1))) for c_ in cuts_ if np.linalg.norm(S_ - c_, axis=1).min() < 0.3))
                idx_ = [i_ for i_ in idx_ if 0 < i_ < len(S_) - 1]
                if not idx_: return [S_]
                legs_ = []; a_ = 0
                for i_ in idx_: legs_.append(S_[a_:i_ + 1]); a_ = i_
                legs_.append(S_[a_:]); return [l_ for l_ in legs_ if len(l_) >= 2]
            try:
                if FID_W is not None:
                    _Cfid = Vu[F].mean(1)
                    def _twin_fid(x_):
                        if not _mirA: return None
                        m__ = FID_W == int(x_)
                        if not m__.any(): return None
                        c__ = K.reflect(_Cfid[m__].mean(0)[None, :], MNa, MCa)[0]; d__, j__ = kct.query(c__)
                        return int(FID_W[j__]) if d__ < 1.0 else None
                    _all_b = {}; _side_b = {}; _kmm = {}
                    for fr_ in FIL_RECS:
                        if not fr_.get("buried"): continue
                        _ln = int(fr_["line"]); _ids = tuple(sorted(int(x_) for x_ in fr_["buried"]))
                        _fx = set(int(x_) for f_ in [int(x) for x in CH[_ln]["pair"]] for x_ in np.unique(FID_W[_pid == f_]))
                        _ga = ("chain", fr_.get("chain")) if fr_.get("chain") is not None else ("line", _ln)
                        if fr_.get("kit_mirror") and fr_.get("mirror_of") is not None: _kmm.setdefault(_ga, set()).add(int(fr_["mirror_of"]))
                        _sd = int(np.sign(float(centF[_ln] @ MNa) - MCa)) if (_mirA and fr_.get("chain") is not None) else 0
                        _all_b.setdefault((_ga, _ids), set()).update(_fx); _side_b.setdefault((_ga, _sd, _ids), set()).update(_fx)
                    for ((_kb, _ib), _ids), _present in _all_b.items():
                        _miss = [x_ for x_ in _ids if x_ not in _present and _twin_fid(x_) not in _present]
                        _nm = ("chain %s" % _ib) if _kb == "chain" else ("line %s" % _ib)
                        if _miss and len(_miss) < len(_ids): say("   fillet room: %s: \"buried\" %s - id(s) %s lie on NO member's face (a wrong id, or the other side's end face: list both sides' ids in the entry)" % (_nm, list(_ids), _miss))
                    for ((_kb, _ib), _sd, _ids), _present in _side_b.items():
                        if any(x_ in _present for x_ in _ids): continue
                        _nm = (("chain %s%s" % (_ib, (" (its %s side)" % ("+" if _sd > 0 else "-")) if _sd else "")) if _kb == "chain" else ("line %s" % _ib))
                        _tw = sorted(set(t_ for t_ in (_twin_fid(x_) for x_ in _ids) if t_ is not None and t_ in _present and t_ not in _ids))
                        if _tw and (_kb, _ib) in _kmm: say("   fillet room: %s is the KIT's mirror of line(s) %s - its \"buried\" %s (copied from that entry) lie on none of its faces, their MIRROR TWINS %s do: add %s to the entry of line(s) %s (one entry holds both sides' ids - the kit mirrors the lines, never the original-face ids; 31bq R5f, NEW #12)" % (_nm, sorted(_kmm[(_kb, _ib)]), list(_ids), _tw, _tw, sorted(_kmm[(_kb, _ib)])))
                        elif _tw: say("   fillet room: %s: its \"buried\" %s lie on none of its faces - their MIRROR TWINS %s do: list them in the entry for this side (the kit does not mirror original-face ids; 31bq B42)" % (_nm, list(_ids), _tw))
                        else: say("   fillet room: %s: \"buried\" %s lie on NO face of it (a wrong id, or the other side's end face: list both sides' ids in the entry)" % (_nm, list(_ids)))
            except Exception as _exb42: say("   fillet room: the \"buried\" ids were not checked (%s)" % str(_exb42)[:80])
            # skin-build
            _CHXI = {}
            try:
                for c_ in sorted(set(fr2_.get("chain") for fr2_ in FIL_RECS if fr2_.get("chain") is not None)):
                    ls_ = sorted(set(int(fr2_["line"]) for fr2_ in FIL_RECS if fr2_.get("chain") == c_)); com_ = set(int(x) for x in CH[ls_[0]]["pair"])
                    for l_ in ls_[1:]: com_ &= set(int(x) for x in CH[l_]["pair"])
                    if len(com_) != 1: continue
                    pcs_ = []
                    for l_ in ls_:
                        lg2_ = _legs_of(l_, samp(edges_out[l_], 0.3))
                        for li2_, P2_ in enumerate(lg2_): pcs_.append((l_, (li2_ if len(lg2_) > 1 else None), np.asarray(P2_[0], float), np.asarray(P2_[-1], float)))
                    _CHXI[c_] = {"A": next(iter(com_)), "pieces": pcs_}
            except Exception as _exc7:
                _CHXI = {}; say("   fillet room: the chains' pieces could not be read (%s) - every end is read with NO chain context (a free or a split end; no chain end): the room lines below may taper where skin-build does not" % str(_exc7)[:100])
            for fr_ in FIL_RECS:
                k0_ = int(fr_["line"]); r0_ = float(fr_["r"]); pq_ = [int(x) for x in CH[k0_]["pair"]]
                S_all = samp(edges_out[k0_], 0.3)
                bur_ = set(int(x_) for x_ in (fr_.get("buried") or []))
                legs_ = _legs_of(k0_, S_all) if (fr_.get("leg") is not None or fr_.get("chain") is not None) else [S_all]
                _only = int(str(fr_["leg"]).strip()) if (str(fr_.get("leg", "")).strip().lstrip("-").isdigit() and 0 <= int(str(fr_["leg"]).strip()) < len(legs_) and len(legs_) > 1) else None
                if fr_.get("leg") is not None and len(legs_) == 1: say("   fillet line %d is decided PER LEG but no split end lies on it here - the room is the whole line's" % k0_)
                for li_, S_ in enumerate(legs_):
                    if _only is not None and li_ != _only: continue
                    nm_ = ("line %d leg %d" % (k0_, li_)) if len(legs_) > 1 else ("line %d" % k0_)      # FILLET ROOM on line
                    L_ = float(np.linalg.norm(S_[-1] - S_[0]))
                    (Na_, sha_), (Nb_, shb_) = _nrm_buried(pq_[0], S_, bur_), _nrm_buried(pq_[1], S_, bur_)
                    if bur_ and max(sha_ or 0.0, shb_ or 0.0) < BURIED_MIN_W and FID_W is not None and any(np.isin(FID_W[_pid == f_], list(bur_)).any() for f_ in pq_): say("   fillet room on %s: \"buried\" %s matched nothing beside the line (%.0f %% / %.0f %% of the samples) - the layout mesh stands; check the ids or the line" % (nm_, sorted(bur_), 100 * (sha_ or 0), 100 * (shb_ or 0)))
                    if Na_ is None or Nb_ is None: continue
                    betas_ = np.degrees(np.arccos(np.clip((Na_ * Nb_).sum(1), -1, 1))); tans_ = np.tan(np.radians(np.minimum(betas_, 170.0)) / 2.0); ts0_ = r0_ * tans_
                    beta_ = float(np.median(betas_)); t_ = float(np.median(ts0_))
                    if beta_ < CREASE_MIN_W:
                        say("FILLET ROOM on %s (faces %d | %d): NO CREASE - the faces meet at %.0f deg (under CREASE_MIN_DEG %g); a fillet there rounds nothing: drop the entry, or decide the line that IS the corner" % (nm_, pq_[0], pq_[1], beta_, CREASE_MIN_W))
                        fr_.setdefault("room", []).append({"leg": (li_ if len(legs_) > 1 else None), "no_crease": True, "beta_deg": round(beta_, 1)}); continue
                    # skin-build  CHAIN_END
                    # TAPER_ENDS
                    # corner edge  corner edge
                    # corner edge
                    _sib_e = {}
                    if fr_.get("chain") is not None:
                        for r2_ in FIL_RECS:
                            if r2_.get("chain") == fr_.get("chain") and int(r2_["line"]) != k0_:
                                try: _sib_e[int(r2_["line"])] = samp(edges_out[int(r2_["line"])], 0.1)
                                except Exception: pass
                    _meets = {kk_ for kk_, P2_ in _sib_e.items() if min(float(np.linalg.norm(P2_ - S_[0], axis=1).min()), float(np.linalg.norm(P2_ - S_[-1], axis=1).min())) < 0.3}
                    _faces = [f_ for f_ in pq_ if PJ[f_]["kind"] != "cap"]
                    _fe = {f_: [(tag_, kid_, samp(e_, 0.1)) for tag_, kid_, e_ in face_edges(f_)] for f_ in pq_}
                    dA_ = np.linalg.norm(S_ - S_[0], axis=1); dB_ = np.linalg.norm(S_ - S_[-1], axis=1); im_ = np.nonzero((dA_ > ts0_) & (dB_ > ts0_))[0]
                    if not len(im_): im_ = np.array([len(S_) // 2])
                    inner_ = S_[im_]; _Dof = {}
                    for f_ in _faces:
                        _N_all = (Na_ if f_ == pq_[0] else Nb_); _T_all = np.gradient(S_, axis=0); Dall_ = np.cross(_N_all, _T_all); Dall_ /= np.maximum(np.linalg.norm(Dall_, axis=1), 1e-9)[:, None]
                        try:
                            _Cf = Vu[F[_pid == f_]].mean(1); _kf = cKDTree(_Cf); _tt = ts0_[im_][:, None]; _D0 = Dall_[im_]
                            if (_kf.query(inner_ + 0.5 * _tt * _D0)[0] > _kf.query(inner_ - 0.5 * _tt * _D0)[0]).mean() > 0.5: Dall_ = -Dall_      # the side the face lies on
                        except Exception: pass
                        _Dof[f_] = Dall_
                    _cx = _CHXI.get(fr_.get("chain")) if fr_.get("chain") is not None else None
                    _side = [f_ for f_ in pq_ if _cx is not None and f_ != _cx["A"]][:1]
                    _ce, _se, _cor = _room_end_kinds(S_, (S_all[0], S_all[-1]), (None if _cx is None else _cx["pieces"]), (k0_, (li_ if len(legs_) > 1 else None)),
                                                     (_fe.get(_side[0], []) if _side else []), [x_ for g_ in GUIDE_RECS if _side and g_.get("role") == "split" and int(g_["face"]) == _side[0] for x_ in g_["ends"]], k0_)
                    _met = {f_: [False, False] for f_ in pq_}; _mb = {f_: [None, None] for f_ in pq_}; _mrec = {f_: [None, None] for f_ in pq_}
                    for e_, J_ in enumerate((S_[0], S_[-1])):
                        if _ce[e_] or _se[e_]: continue
                        for f_ in _faces:
                            _b = _room_border_at(J_, _fe[f_], k0_)
                            if _b is None or _b[0] != "chain": continue
                            _ok, _dm, _dj = _room_meet(S_ + ts0_[:, None] * _Dof[f_], _b[2], J_, 0.15, THIN_ROOM)
                            _met[f_][e_] = bool(_ok); _mrec[f_][e_] = {"border": int(_b[1]), "nearest_mm": round(float(_dm), 3), "from_junction_mm": round(float(_dj), 3), "met": bool(_ok)}
                            if _ok: _mb[f_][e_] = ("chain", int(_b[1]))
                    _tap = _room_taper_ends(_ce, _se, [_met[f_] for f_ in pq_], FIL_TAPER_W)
                    _wtap = K.taper_weights(S_, max(TAPER_X_W * t_, TAPER_MIN_W), ends=_tap) if _tap else np.ones(len(S_))
                    ts_ = ts0_ * _wtap
                    _both = [e_ for e_ in (0, 1) if not _ce[e_] and not _se[e_] and _faces and all(_met[f_][e_] for f_ in pq_)]
                    if _both or os.environ.get("FIL_DBG") == "1":
                        _etx = []
                        for e_ in (0, 1):
                            if _ce[e_]: _etx.append(("end %d a CHAIN END (full R, no taper; the corner edge %s %s cut at the contact)" % (e_, _cor[e_][0], list(_cor[e_][1]) if isinstance(_cor[e_][1], tuple) else _cor[e_][1])) if _cor[e_][0] != "split" else ("end %d a CHAIN END (full R, no taper; its corner edge is a split of face %d - the blend ends there, no border cut)" % (e_, _side[0]))); continue
                            if _se[e_]: _etx.append("end %d a SPLIT END (tapers - the corner stays a point)" % e_); continue
                            _mm = ", ".join("face %d %s border %d (%.2f mm)" % (f_, "MEETS" if _mrec[f_][e_]["met"] else "does not meet", _mrec[f_][e_]["border"], _mrec[f_][e_]["nearest_mm"]) for f_ in _faces if _mrec[f_][e_])
                            _etx.append("end %d %s%s" % (e_, "TAPERS" if e_ in _tap else ("MEETS ON BOTH FACES - no taper, those borders cut there and not measured" if all(_met[f_][e_] for f_ in pq_) else "NOT TAPERED (FIL_TAPER=0: the cap)"), (" (%s)" % _mm) if _mm else " (no border leaves it)"))
                        say("   fillet room on %s: its ends as skin-build decides them - %s (31bq R7W, M7)" % (nm_, "; ".join(_etx)))
                    for f_ in _faces:
                        _cut = set()
                        for e_ in (0, 1):
                            if e_ in _tap: continue
                            if _mb[f_][e_] is not None: _cut.add(_mb[f_][e_])
                            if _ce[e_] and _side and f_ == _side[0] and _cor[e_] is not None and _cor[e_][0] != "split": _cut.add(tuple(_cor[e_]))
                        others_ = [(tag_, kid_, P_) for tag_, kid_, P_ in _fe[f_] if not (tag_ == "chain" and (kid_ == k0_ or kid_ in _meets)) and (tag_, kid_) not in _cut]
                        if not others_: continue
                        Dall_ = _Dof[f_]; Df_ = Dall_[im_]
                        _er = {"taper": list(_tap), "chain_end": list(_ce), "split_end": list(_se), "meet": _mrec[f_], "cut": [[c_[0], (list(c_[1]) if isinstance(c_[1], tuple) else c_[1])] for c_ in sorted(_cut, key=str)]}
                        best_, clear_ = _room_width(S_, im_, Dall_, ts_, THIN_ROOM * _wtap, others_, 0.3)
                        if best_ is None:
                            say("   fillet room on %s, face %d: the strip's cross-lines keep the print tolerance from every other border of the face (the build's width rule, estimated on the mesh) - it fits" % (nm_, f_))
                            fr_.setdefault("room", []).append({"leg": (li_ if len(legs_) > 1 else None), "face": f_, "fits": True, "clear_mm": (round(clear_, 3) if np.isfinite(clear_) else None), "ends": _er}); continue
                        dmin_, tag_, kid_, g_, w_ = best_; at_ = inner_[g_]; beta_g = float(betas_[im_][g_]); t_g = float(ts_[im_][g_]); r_fit_ = max(0.0, (w_ - THIN_ROOM) / max(float(tans_[im_][g_]), 1e-6))
                        what_ = ("the body's wall edge %s" % (list(kid_),)) if tag_ == "wall" else ("its border %d (faces %s)" % (kid_, [int(x) for x in CH[kid_]["pair"]]))
                        say("FILLET ROOM on %s (faces %d | %d), R %g: A FILLET NEEDS ROOM - a fillet of radius R touches each face t = R tan(beta/2) from the crease (beta %.0f deg here -> t = %.2f mm) and needs t + the print tolerance (%.2f) of face beside the crease; face %d has %.2f mm there before %s (at %s; the strip's cross-line comes %.2f mm from it). EITHER make room - move that border (a hole's rim, a neighbour's border) or fill the gap so the face is at least %.2f mm wide beside the crease, as the design intends - OR lower R to %.2f at most. skin-build's own width rule on the built strip decides (this line is the wires' estimate of it on the mesh - 31bq W / PP); the kit does not choose"
                            % (nm_, pq_[0], pq_[1], r0_, beta_g, t_g, THIN_ROOM, f_, w_, what_, np.round(at_, 1).tolist(), dmin_, t_g + THIN_ROOM, r_fit_))
                        fr_.setdefault("room", []).append({"leg": (li_ if len(legs_) > 1 else None), "face": f_, "width_mm": round(w_, 3), "t_mm": round(t_g, 3), "beta_deg": round(beta_g, 1), "r_fit": round(r_fit_, 3), "fits": False, "cross_mm": round(dmin_, 3), "ends": _er})
                    if L_ < 2.5 * t_: say("   fillet room on %s: the crease is %.1f mm long for t = %.2f - SHORT for a blend: a member with a FREE end needs 2.5 t of line for its run-out (skin-build caps R there so it fits); between two chain junctions it is swept at full R; a junction where the crease runs through a far-side face boundary turning under CREASE_TURN_MAX is NO CORNER - skin-build refuses the chain there: put the far side's faces in ONE feature so the crease is one line and one blend, or accept the member that lies between the no-corner junctions sharp (\"sharp_ok\": [<line>] on the chain's entry) - its chain-mates taper to those junctions (31bx K35; 31ca R5 F1) - the preview decides; if it still fails here: one feature on the far side so the crease is ONE chain, \"sharp_ok\" on this member (not swept), or R under %.2f on the chain" % (nm_, L_, t_, L_ / 2.5))
                if fr_.get("leg") is not None and len(legs_) > 1: say("   fillet line %d is decided PER LEG (\"leg\": %s): %d of its %d legs measured, each between the line's junctions and the split ends on it (skin-build sweeps each as its own crease, tapering to nothing at the corner)" % (k0_, fr_["leg"], (1 if _only is not None else len(legs_)), len(legs_)))
                if str(fr_.get("leg", "")).strip().lstrip("-").isdigit() and _only is None and len(legs_) > 1: say("   fillet line %d: \"leg\": %s is out of range (the line has %d legs, 0-based) - every leg measured (31bq B37)" % (k0_, fr_["leg"], len(legs_)))
        except Exception as _exr: say("   the fillet room check failed: %s" % str(_exr)[:80])
    _lines_against_part()
    _gb = os.path.join(SK, "guides.brep")
    if GUIDE_EDGES: Part.makeCompound(GUIDE_EDGES).exportBrep(_gb)
    elif os.path.isfile(_gb): os.remove(_gb)
    _md5n = K.md5(src_brep) if os.path.isfile(src_brep) else None
    with open(os.path.join(SK, "guides.json"), "w", encoding="utf-8") as _fh:
        json.dump({"network_frame_md5": None, "tag": TAG, "guides": GUIDE_RECS, "cuts": CUTS}, _fh, indent=1)
    with open(os.path.join(SK, "fillets.json"), "w", encoding="utf-8") as _fh:
        # 31bs K29 (2026-11-03): each record
        _sok_lines = sorted(set(int(_r["line"]) for _r in FIL_RECS if _r.get("sharp_ok") and str(_r.get("line", "")).lstrip("-").isdigit()))
        if _sok_lines: say("   fillet line(s) %s stand SHARP (\"sharp_ok\" on their entries; a twin is accepted with its master - 31bs T4 F1 / F3) - NOT swept: they stand sharp on purpose at the preview and the build (31bx R5 F2)" % _sok_lines)
        json.dump({"network_frame_md5": None, "tag": TAG, "fillets": FIL_RECS, "room_levers": ROOM_LV}, _fh, indent=1)
    ng_ = sum(1 for r_ in GUIDE_RECS if r_["role"] == "guide"); ns_ = sum(1 for r_ in GUIDE_RECS if r_["role"] == "split")
    say("ADDED LINES: %d guide(s) (a face's surface passes through them) and %d split(s) (a face made two) on %d face(s)%s; %d fillet(s) decided%s"
        % (ng_, ns_, len(set(r_["face"] for r_ in GUIDE_RECS)), (" - %d border line(s) cut where a split ends" % len(CUTS)) if CUTS else "", len(FIL_RECS),
           " (twins included)" if _mirA else ""))
else:
    _lines_against_part()
    for _f in ("guides.json", "guides.brep", "fillets.json"):
        try: os.remove(os.path.join(SK, _f))
        except OSError: pass
def final_kind(e_):
    """what the finished edge IS (the client 2026-10-07: teal must be a straight line): LINE when every point is within 0.01 mm of its chord, ARC
    when it lies on one circle within 0.01 mm, CUBIC when it is one B-spline span (at most 4 poles, degree <= 3), else MULTI<n poles>"""
    X = samp(e_, max(e_.Length / 60, 1e-3)); A_, B_ = X[0], X[-1]
    if seg_dist(X, A_, B_).max() < 0.01: return "LINE"
    c0 = X.mean(0); _, _, vt_ = np.linalg.svd(X - c0); nrm_ = vt_[2]
    if np.abs((X - c0) @ nrm_).max() < 0.01:
        Q_ = X - ((X - c0) @ nrm_)[:, None] * nrm_; u_ = (Q_ - c0) @ vt_[0]; v_ = (Q_ - c0) @ vt_[1]
        M_ = np.stack([u_, v_, np.ones_like(u_)], 1); sol_, *_ = np.linalg.lstsq(M_, u_ ** 2 + v_ ** 2, rcond=None)
        cu = sol_[0] / 2; cw = sol_[1] / 2; r_ = np.sqrt(max(sol_[2] + cu ** 2 + cw ** 2, 0))
        if np.abs(np.hypot(u_ - cu, v_ - cw) - r_).max() < 0.01: return "ARC"
    cv0 = e_.Curve
    if hasattr(cv0, "NbPoles") and cv0.NbPoles <= 4 and cv0.Degree <= 3: return "CUBIC"
    return "MULTI%d" % (cv0.NbPoles if hasattr(cv0, "NbPoles") else 99)
counts = {}
for e_, r in zip(edges_out, recs):
    if r["rung"] == "WALL_DROPPED": continue
    r["drawn"] = r["rung"]; r["rung"] = r["rung"] if r.get("legs") else final_kind(e_)
    counts[r["rung"]] = counts.get(r["rung"], 0) + 1
Part.makeCompound(edges_out).exportBrep(src_brep)
for _gf in ("guides.json", "fillets.json"):
    _gp = os.path.join(SK, _gf)
    if os.path.isfile(_gp):
        try:
            _gj = json.load(open(_gp, encoding="utf-8")); _gj["network_frame_md5"] = K.md5(src_brep)
            json.dump(_gj, open(_gp, "w", encoding="utf-8"), indent=1)
        except (OSError, ValueError): pass
# skin-build
with open(os.path.join(SK, "wires_demote.json"), "w", encoding="utf-8") as _fh:
    json.dump({"network_frame_md5": K.md5(src_brep), "tag": TAG, "demote": {str(x_): w_ for x_, w_ in sorted(DEMOTE.items())}}, _fh, indent=1)
if DEMOTE:
    say("ORIGINAL SURFACES: %d face(s) leave their original surface for skin-build's next rung - %s (skin\\wires_demote.json)" % (len(DEMOTE), sorted(DEMOTE)))
skin_recs = [r for r in recs if r["rung"] != "WALL_DROPPED"]
nst = sum(len(v) for v in FR.get("stretch", {}).values())
say("SKIN EDGES (the new wireframe): %d - %s; wall stretches (the body's own section-face edges, untouched) %d"
    % (len(skin_recs), ", ".join("%s %d" % kv for kv in sorted(counts.items())), nst))
dm = np.array([r["dev_max"] for r in skin_recs]) if skin_recs else np.zeros(1)
gw = [r for r in skin_recs if r.get("grow_out", 0) > 0.01]
say("GROW: %d border(s) between fitted faces pushed outward%s" % (len(gw), num(" (largest %.3f mm, GROW_MAX %.2f; a border point still outside its edge by up to %.3f mm)",
    max([r["grow_out"] for r in gw] or [0]), GROW_MAX, max([r.get("cut_in", 0) for r in skin_recs] or [0]))))
dec_ = [r for r in skin_recs if r.get("decided")]; _dsa = [r for r in skin_recs if r.get("dec_set_aside")]
say("DECIDED: %d of %d lines drawn as the agent decided them (LINES), the rest by the ladder; the voxel's old border is no measure of a decided line%s" % (len(dec_), len(skin_recs),
    ("; %d decision(s) SET ASIDE (said above, recorded as dec_set_aside): %s" % (len(_dsa), ", ".join("chain %s (%s)" % (r["chain"], str(r["dec_set_aside"]).split(" - ")[0]) for r in _dsa[:8]))) if _dsa else ""))
if SHOW_NUMBERS:
    say("border points off their simplified edge: p50 %.3f p95 %.3f max %.3f mm" % (np.median(dm), np.percentile(dm, 95), dm.max()))
    for r in sorted(skin_recs, key=lambda r: -r["dev_max"])[:10]:
        say("   chain %d faces %s (%s) %s, %.1f mm long: border off by up to %.3f mm%s" % (r["chain"], r["pair"], "|".join(r["kinds"]), r["rung"], r["length"], r["dev_max"],
            ("; %d inflection(s)" % r["inflections"]) if r.get("inflections") else ""))
multi = [r for r in skin_recs if r["rung"].startswith("MULTI")]
_lay = [r for r in multi if "+ON_ORIG" in str(r.get("drawn", ""))]; _mul = [r for r in multi if "+ON_ORIG" not in str(r.get("drawn", ""))]
if _mul: say("NOT ONE SIMPLE CURVE (more than 4 poles): %d chain(s) %s - their faces' points are the fix" % (len(_mul), [r["chain"] for r in _mul]))
if _lay: say("LAID ON AN ORIGINAL SURFACE with more than 4 poles: %d chain(s) %s - a free border projected onto the original face takes the poles the surface needs (the record's `drawn` says +ON_ORIG); to make it ONE simple curve DECIDE it in LINES - a decided line is refit as one cubic span on the surface within ON_TOL, else its face leaves the surface, said (31bw)" % (len(_lay), [r["chain"] for r in _lay]))
infl = [r for r in skin_recs if r.get("inflections")]
if infl: say("S-shaped (an inflection in its poles): %d chain(s) %s" % (len(infl), [r["chain"] for r in infl]))
def _js(o):
    if isinstance(o, (np.bool_,)): return bool(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    raise TypeError(type(o))
json.dump({"tag": TAG, "levers": {"TOL_LINE": TOL_LINE, "TOL_ARC": TOL_ARC, "TOL_CUBIC": TOL_CUBIC, "MAX_POLES": MAX_POLES, "GROW": GROW, "GROW_MAX": GROW_MAX, "ON_TOL": ON_TOL},
           "network_md5": NET_MD5, "lines": LINES_P or "(the last run's decisions)", "demoted": {str(x_): w_ for x_, w_ in DEMOTE.items()},
           "skin_edges": len(skin_recs), "wall_stretches": nst, "counts": counts, "chains": recs}, open(os.path.join(SK, "wire_simplify.json"), "w"), indent=0, default=_js)
# over the
if WIRE_PICS:
    COL = {"LINE": (60, 230, 255), "ARC": (80, 255, 120), "CUBIC": (255, 220, 40), "CIRCLE": (80, 255, 120), "CLOSED_SPLINE": (255, 120, 40), "V": (200, 255, 255)}
    polys = []; poly_faces = []
    for e, r in zip(edges_out, recs):
        if r["rung"] == "WALL_DROPPED": continue
        polys.append((np.array([P3(x) for x in e.discretize(Number=max(2, int(e.Length / 0.05)))]), COL.get("V" if r["rung"].startswith("V(") else r["rung"].split("+")[0], (255, 60, 200))))
        poly_faces.append(tuple(int(v) for v in (r.get("pair") or ())))
    stre = []
    try:
        wc = Part.Shape(); wc.importBrep(os.path.join(RUN, "wall_caps.brep"))
        for f in wc.Faces:
            for ed in f.Edges: stre.append(np.array([P3(x) for x in ed.discretize(Number=max(2, int(ed.Length / 0.1)))]))
    except Exception: pass
    ends = [P3(e.Vertexes[0].Point) for e, r in zip(edges_out, recs) if r["rung"] != "WALL_DROPPED"] + \
           [P3(e.Vertexes[-1].Point) for e, r in zip(edges_out, recs) if r["rung"] != "WALL_DROPPED"]
    juncs = np.array(ends) if ends else np.zeros((0, 3))
    LABELS = os.environ.get("WIRE_LABELS", "1") == "1"
    lab_pts = [(r["chain"], np.array([P3(x) for x in e.discretize(Number=3)])[1]) for e, r in zip(edges_out, recs) if r["rung"] != "WALL_DROPPED"]
    addp = [(np.array([P3(x) for x in e_.discretize(Number=max(2, int(e_.Length / 0.05)))]), r_["role"]) for e_, r_ in zip(GUIDE_EDGES, GUIDE_RECS)]
    _offc = lambda r_, base: (170, 0, 255) if float(r_.get("off_source_mm") or 0.0) > LINE_OFF_MAX else base
    _OFFL = (["Violet = an ADDED line OFF THE PART by more than LINE_OFF_MAX %g mm (the step's output says where and why); red dots = edge ends (junctions)." % LINE_OFF_MAX]
             if any(float(r_.get("off_source_mm") or 0.0) > LINE_OFF_MAX for r_ in GUIDE_RECS) else [])
    def draw(dr, proj):
        for P_ in stre: dr.line(proj(P_), fill=(150, 150, 160), width=1)
        for P_, col in polys: dr.line(proj(P_), fill=col, width=3)
        for (P_, role_), r_ in zip(addp, GUIDE_RECS): dr.line(proj(P_), fill=_offc(r_, (255, 150, 40) if role_ == "guide" else (255, 255, 255)), width=3)
        if len(juncs):
            for x, y in proj(juncs): dr.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 60, 40))
        if LABELS:
            for ck, m_ in lab_pts:
                if _mir0 and (m_ @ MN0 - MC0) * MSIDE_ < -0.3: continue
                (x, y), = proj(m_[None, :]); t_ = str(ck)
                dr.rectangle([x - 1, y - 7, x + 7 * len(t_) + 1, y + 7], fill=(0, 0, 0)); dr.text((x, y - 7), t_, fill=(255, 255, 255))
    leg = [((60, 230, 255), "straight line"), ((80, 255, 120), "one arc / circle"), ((255, 220, 40), "one cubic span (4 poles)"),
           ((255, 60, 200), "MORE than one span (not simple - fix its points)"), ((200, 255, 255), "a V - two legs meeting at a kept apex (a split's decided end; 31bw A5b)"),
           ((150, 150, 160), "the body's own wall edges"), ((255, 60, 40), "edge ends")]
    if GUIDE_RECS: leg += [((255, 150, 40), "ADDED line inside a face (its surface passes through it)"), ((255, 255, 255), "SPLIT line (the face is made two)")]
    if any(float(r_.get("off_source_mm") or 0.0) > LINE_OFF_MAX for r_ in GUIDE_RECS): leg += [((170, 0, 255), "VIOLET: an ADDED line OFF THE PART by more than LINE_OFF_MAX (a trace spanning where its face is not - the step's output says where)")]
    # WIRE_OCC
    OCC = os.environ.get("WIRE_OCC", "1") == "1"; LAB_ = None
    if OCC:
        try:
            LAB_ = np.load(os.path.join(SK, "patches.npz"))["patch"]
            if len(LAB_) != len(F): say("WIRE: skin\\patches.npz has %d labels for %d triangles - not this mesh's layout; the frames are drawn transparent" % (len(LAB_), len(F))); LAB_ = None
        except Exception as ex_:
            say("WIRE: no layout labels for the opaque view (%s) - the frames are drawn transparent" % str(ex_)[:80]); LAB_ = None
    OCC = OCC and LAB_ is not None
    def draw_top(dr, proj):
        if len(juncs):
            for x, y in proj(juncs): dr.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 60, 40))
        if LABELS:
            for ck, m_ in lab_pts:
                if _mir0 and (m_ @ MN0 - MC0) * MSIDE_ < -0.3: continue
                (x, y), = proj(m_[None, :]); t_ = str(ck)
                dr.rectangle([x - 1, y - 7, x + 7 * len(t_) + 1, y + 7], fill=(0, 0, 0)); dr.text((x, y - 7), t_, fill=(255, 255, 255))
    occ_lines = [(P_, (150, 150, 160), 1) for P_ in stre] + [(P_, col, 3, fc_) for (P_, col), fc_ in zip(polys, poly_faces)] \
                + [(P_, _offc(r_, (255, 150, 40) if role_ == "guide" else (255, 255, 255)), 3, (int(r_["face"]),)) for (P_, role_), r_ in zip(addp, GUIDE_RECS)]
    if OCC: leg = leg + [((120, 140, 150), "faint dotted = the same line where it is BEHIND the part (hidden)")]
    WKEY = K.pic_key(src_brep, os.path.join(SK, "guides.brep"), os.path.join(SK, "guides.json"), os.path.join(SK, "fillets.json"), os.path.join(SK, "regions.npz"), pics=K.PICS, labels=LABELS, occ=OCC, draw="r5f-violet", line_off_max=LINE_OFF_MAX)
    K.clear_frames("WIRE_", WKEY)
    nfr = 0; wire_frames = []
    for i, (nm, dv, fb, W, ttl) in enumerate(K.views(below=True)):
        p_ = os.path.join(OUT, "WIRE_%02d_%s.png" % (i + 1, nm))
        if OCC:
            K.view_occluded(R, p_, Vu, F, LAB_, dv, fb, W, ttl,
                "WIRE  THE WIREFRAME, HIDDEN LINES HIDDEN - %d skin edges (%s) - %s" % (len(skin_recs), ", ".join("%s %d" % kv for kv in sorted(counts.items())), ttl),
                ["Every border between two skin faces as ONE simple curve over the mesh drawn OPAQUE (each layout face its own tint, borders dark): cyan straight,",
                 "green one arc, yellow one cubic span, magenta = more than one span (that border's points are wrong). Grey = the edit region walls' body edges.",
                 "A line is full colour where it is ON or IN FRONT of the surface you see, faint dotted where it is BEHIND the part. Red = edge ends (junctions).",
                 "White numbers = the chain numbers LINES uses (the master side; a twin is its mirror).", K.RULE_31BH]
                + (["Faces leaving their original surface (a decided line is not one simple curve on it): %s" % sorted(DEMOTE)] if DEMOTE else [])
                + (["Orange = lines ADDED inside a face for its shape (_add role guide); white = SPLIT lines (_add role split): %d on faces %s" % (len(GUIDE_RECS), sorted(set(r_["face"] for r_ in GUIDE_RECS)))] if GUIDE_RECS else []) + _OFFL,
                occ_lines, legend=leg, key=WKEY, draw=draw_top); nfr += 1; wire_frames.append(p_)
            continue
        K.view(R, p_, Vu, F, dv, fb, W, ttl,
               "WIRE  THE WIREFRAME - %d skin edges (%s) - %s" % (len(skin_recs), ", ".join("%s %d" % kv for kv in sorted(counts.items())), ttl),
               ["Every border between two skin faces as ONE simple curve over the voxel (transparent): cyan straight, green one arc, yellow one cubic span,",
                "magenta = more than one span (that border's points are wrong). Grey = the edit region walls' body edges (exact, kept). Red = edge ends (junctions).",
                "White numbers = the chain numbers LINES uses (the master side; a twin is its mirror). Lines behind the voxel show through it.", K.RULE_31BH]
               + (["Faces leaving their original surface (a decided line is not one simple curve on it): %s" % sorted(DEMOTE)] if DEMOTE else [])
               + (["Orange = lines ADDED inside a face for its shape (_add role guide); white = SPLIT lines (_add role split): %d on faces %s" % (len(GUIDE_RECS), sorted(set(r_["face"] for r_ in GUIDE_RECS)))] if GUIDE_RECS else []) + _OFFL,
               draw=draw, legend=leg, key=WKEY); nfr += 1; wire_frames.append(p_)
    say("%s (WIRE_*: %d frames)" % (K.pic_report(), nfr))
    # kit rebuild  skin-build
    PREVIEW = {}
    # recorded
    if os.environ.get("PREFLIGHT", "1") != "1":
        PREVIEW = {"taken": False, "why": "PREFLIGHT=0 - the preview was skipped on purpose"}; say("PREVIEW (31br G1 / G2): skipped (PREFLIGHT=0) - the judge will refuse an ok on this record")
    else:
        import subprocess as _sp9, re as _re9
        _pf_recs = list(globals().get("FIL_RECS") or []); _pf_lines = sorted(set(int(r_["line"]) for r_ in _pf_recs if str(r_.get("line", "")).lstrip("-").isdigit()))
        _sok_pre = sorted(set(int(r_["line"]) for r_ in _pf_recs if r_.get("sharp_ok") and str(r_.get("line", "")).lstrip("-").isdigit()))
        _env9 = dict(os.environ); _env9["SKIN_PREFLIGHT"] = "1"; _env9["FILLET_RERUN"] = "0"; _env9.pop("FILLET_DROPPED", None)
        try: _benv9 = json.loads(os.environ.get("PREFLIGHT_BUILD_ENV") or "{}")      # skin-build
        except ValueError: _benv9 = {}
        if not isinstance(_benv9, dict) or not _benv9:      # skin-build  skin-build
            _benv9 = {}
            try:
                import glob as _gl9
                _fs9 = sorted(_gl9.glob(os.path.join(RUN, "env_skin-build_*.json")), key=os.path.getmtime)
                if _fs9: _benv9 = {k_: str(v_) for k_, v_ in json.load(open(_fs9[-1], encoding="utf-8")).items() if k_.isupper() and not k_.startswith("_") and k_ not in ("BODY", "RUN", "STL", "TAG") and str(v_).strip() != ""}
            except Exception: _benv9 = {}
            if not _benv9: _benv9 = {"FRAME": "1", "KEEP_NET": "1", "EDGE_FIX": "1", "W_EDGE": "400", "CTRL_MM": "1.0", "LAM": "0.5", "VOXCHECK": "0", "FRAME_TOL": "0.02", "PLANE": "1"}
        _took9 = sorted(k_ for k_, v_ in _benv9.items() if k_ not in os.environ and str(v_).strip() != "")
        for k_ in _took9: _env9[k_] = str(_benv9[k_])
        say("PREVIEW: the build's levers for the child - %s (%s; this step's own env wins where both hold a lever)" % (", ".join("%s=%s" % (k_, _env9[k_]) for k_ in _took9) or "none beyond this step's env",
            "the runner's skin-build defaults + the job's last build record" if os.environ.get("PREFLIGHT_BUILD_ENV") else "the job's last build record, else the card's proven set - no runner"))
        if _pf_lines: _env9["FILLET_LINES"] = ",".join(str(x_) for x_ in _pf_lines)
        else: _env9.pop("FILLET_LINES", None)
        _pfp = os.path.join(SK, "preflight.json")
        try: os.remove(_pfp)
        except OSError: pass
        say("PREVIEW (31br G1 / G2): the build's own ladder on this wireframe - every changed face spanned, %s, the face stage run; nothing sewn (a child of this step; its lines below say 'preview:' - its whole log: skin\\preflight_child.txt)"
            % (("the %d decided fillet line(s) %s swept%s" % (len(_pf_lines), _pf_lines, (" (%s standing SHARP by your sharp_ok - handed to the child, never swept)" % _sok_pre) if _sok_pre else "")) if _pf_lines else "no fillet decided"))
        _t9 = time.time(); _kept9 = []; _rc9 = None
        try:
            _pr9 = _sp9.Popen([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "sk_build.py")], env=_env9, cwd=os.getcwd(), stdout=_sp9.PIPE, stderr=_sp9.STDOUT, text=True, errors="replace", bufsize=1)
            for _ln9 in _pr9.stdout:
                _ln9 = _ln9.rstrip("\n"); _kept9.append(_ln9)
                if _re9.search(r"AT THE WALL|SPAN FAILED|: not made|NOT made|PREVIEW|FILLET BY LINES on line|FILLET CHAIN|fillet chain \d+: junction|TAPERS|NOT A BORDER|^FAIL:|^\s*\d+s\s+FAIL:|Traceback|Exception while|TRACEBACK|SPANNED:|FACES:|clipped to the face's loop", _ln9):
                    print("   preview: " + _re9.sub(r"^(\s*\d+s\s+)?FAIL:", r"\1the build would FAIL:", _ln9)[:(4000 if "AT THE WALL" in _ln9 else 420)], flush=True)
            _rc9 = _pr9.wait()
        except Exception as _ex9:
            say("PREVIEW: the child could not run (%s)" % str(_ex9)[:160])
        try:
            with open(os.path.join(SK, "preflight_child.txt"), "w", encoding="utf-8") as _fh9: _fh9.write("\n".join(_kept9) + "\n")
        except OSError: pass
        try: PREVIEW = json.load(open(_pfp, encoding="utf-8"))
        except (OSError, ValueError): PREVIEW = {}
        _secs9 = round(time.time() - _t9, 1)
        if not PREVIEW:
            _why9 = next((l_ for l_ in reversed(_kept9) if _re9.search(r"FAIL:|Exception while|Traceback", l_)), "no record and no FAIL line (rc %s)" % _rc9)
            PREVIEW = {"taken": False, "why": ("the preview child ended before its record: %s" % _re9.sub(r"^\s*\d+s\s+", "", _why9))[:600], "rc": _rc9, "secs": _secs9}
            say("PREVIEW: NOT TAKEN - %s - the judge will refuse an ok on this record; the build's own gate stopped it before any face: fix that first" % PREVIEW["why"][:300])
        else:
            _sok9 = sorted(set(int(r_["line"]) for r_ in _pf_recs if r_.get("sharp_ok") and str(r_.get("line", "")).lstrip("-").isdigit()))
            _nm9 = [int(k_) for k_ in (PREVIEW.get("not_made") or []) if int(k_) not in _sok9]
            _inv9 = list(PREVIEW.get("faces_invalid") or [])      # NOT VALID  skin-build
            PREVIEW.update({"taken": True, "rc": _rc9, "secs": _secs9, "sharp_ok": _sok9, "not_made_unaccepted": _nm9, "verdict": "pass" if not (PREVIEW.get("span_failed") or PREVIEW.get("pieces_failed") or _nm9 or _inv9) else "fail"})
            if _inv9:
                say("PREVIEW VERDICT - THE BUILD WOULD FAIL (31bx R6 F1): face(s) %s build but are NOT VALID - skin-build fails on them ('the closed shell did not make a valid solid - the face(s) not valid themselves'): the face's loop or surface is wrong there (a wrapping face - a cylinder's two halves put in one feature -, a self-crossing border): split it with a wire, or give its halves to different features; the judge is REFUSED on this record"
                    % ", ".join("%s%s" % (p_.get("patch"), p_.get("sub") or "") for p_ in _inv9[:8]))
            if PREVIEW.get("span_failed"):
                _fl9 = PREVIEW.get("faces") or {}
                _hp9 = {}
                for h_ in HAIRPIN_FOUND: _hp9.setdefault(int(h_["face"]), h_)
                for k_ in PREVIEW["span_failed"]:
                    h_ = _hp9.get(int(k_))
                    if h_: say("PREVIEW: face %s - a split's end lies at a HAIRPIN apex of this face's border (said at the read: entry %s%s, chain %s, the border turns %.1f deg, the end %.2f mm from the apex): the rounded apex is the likely cause of this failure - end that split on a corner (%s) or a junction (%s), or fold the hairpin's face into the feature (FEATURES) so the border becomes wall edges (d19b)"
                               % (k_, h_.get("entry"), " mirrored" if h_.get("mirrored") else "", h_.get("chain"), float(h_.get("turn_deg") or 0), float(h_.get("apex_mm") or 0), ", ".join("c%d" % c_ for c_ in (h_.get("corners") or [])) or "none listed", ", ".join("j%d" % j_ for j_ in (h_.get("junctions") or [])) or "none"))
                say("PREVIEW VERDICT - THE BUILD WOULD FAIL (31br G1): face(s) %s cannot be spanned on these lines - %s. Change the lines THERE before the judge: split the piece where its surface turns, or give the turning part to the neighbour it faces like (the piece's own SPAN FAILED line above names its chains and added lines); `kit rebuild judge --what wires --verdict ok` is REFUSED on this record"
                    % (PREVIEW["span_failed"], " | ".join("face %s: %s" % (k_, str((_fl9.get(str(k_)) or {}).get("fail") or "?")[:260]) for k_ in PREVIEW["span_failed"][:4])))
            if PREVIEW.get("pieces_failed"):
                say("PREVIEW VERDICT - THE FACE STAGE WOULD FAIL (31br G1 / G2): kit-made piece(s) %s - %s: a corner form the kit cannot make on these lines (lower R, end the chain there on purpose, or decide the corner edge); the judge is REFUSED on this record"
                    % (", ".join("%s%s" % (p_.get("patch"), p_.get("sub") or "") for p_ in PREVIEW["pieces_failed"][:6]), " | ".join(str(p_.get("fail"))[:200] for p_ in PREVIEW["pieces_failed"][:3])))
            if _nm9:
                _lr9 = PREVIEW.get("lines") or {}
                say("PREVIEW VERDICT - fillet line(s) %s would NOT be made (31br G2): %s - lower R or make room there (the room lines say where), or accept the line SHARP on purpose with \"sharp_ok\": true on its _fillets entry; the judge is REFUSED until then"
                    % (_nm9, " | ".join("line %s: %s" % (k_, str((_lr9.get(str(k_)) or {}).get("why") or "?")[:220]) for k_ in _nm9[:4])))
            if _sok9: say("PREVIEW: fillet line(s) %s stand SHARP by your \"sharp_ok\" - not swept (31bx R5 F2)" % _sok9)
            if PREVIEW["verdict"] == "pass":
                say("PREVIEW VERDICT - PASS (31br G1 / G2): every changed face spans and every decided fillet is made on this wireframe by the build's own ladder (%d face(s), %d fillet(s)%s, %.0f s) - levers not set on this step took the build's defaults: a build with other --set values may differ (the record names them); the preview ends BEFORE the shell - the solid's checks (faces crossing over 0.30 mm) are skin-build's, so this PASS is no BUILD PASS (31cb H-F4)" % (len(PREVIEW.get("faces") or {}), len(PREVIEW.get("made") or []), (", %d standing SHARP by your sharp_ok" % len(_sok9)) if _sok9 else "", _secs9))
        try: json.dump(PREVIEW, open(_pfp, "w", encoding="utf-8"), indent=1, default=str)
        except OSError: pass
    K.source_quality(Vu, F)
    K.write_look("wires", wire_frames, src_brep, {"skin_edges": len(skin_recs), "counts": counts, "decided": len([r for r in skin_recs if r.get("decided")]), "lines_against_part": dict(LINES_PART), "room_levers": dict(ROOM_LV), "preflight": PREVIEW,
                                                  "hairpin_ends": HAIRPIN_FOUND, "rails": [r_.get("name") for r_ in RAILS], "multi": [r["chain"] for r in skin_recs if r["rung"].startswith("MULTI")]})
CP_ = os.environ.get("CORNER_PICS", "auto").strip().lower()
if CP_ == "1" or (CP_ == "auto" and not RAILS):
    CKEY = K.pic_key(os.path.join(RUN, "wall_caps.brep"), os.path.join(SK, "corners.json"), os.path.join(SK, "regions.npz")); K.clear_frames("CORNERS_", CKEY)
    Xc_ = np.array([p_["xyz"] for p_ in corner_pts])
    cedges_ = [np.array([[q.x, q.y, q.z] for q in e.discretize(Number=max(2, int(e.Length / 0.1)))]) for f in FC_ for e in f.Edges]
    def cdraw(dr, proj):
        for E in cedges_: dr.line(proj(E), fill=(120, 220, 255), width=2)
        for p_, (x, y) in zip(corner_pts, proj(Xc_)):
            dr.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(255, 60, 40))
            t = "c%d" % p_["id"]; dr.rectangle([x + 5, y - 8, x + 5 + 8 * len(t), y + 8], fill=(0, 0, 0)); dr.text((x + 6, y - 8), t, fill=(255, 255, 120))
    vs_ = K.wall_views(FC_, cap_wall, pad=3.0) + [v for v in K.views(close=False, below=True, pics="full") if v[0] in ("top", "bottom", "orbit_045", "orbit_225", "below_135", "below_315")]
    for i, (nm, d, fb, W, ttl) in enumerate(vs_):
        K.view(R, os.path.join(OUT, "CORNERS_%02d_%s.png" % (i + 1, nm)), Vu, F, d, fb, W, ttl,
               "CORNERS  the reinsert faces' corners, numbered - %s" % ttl,
               ["Cyan = the edges of the reinsert faces (the body's own section faces on the edit region walls, step 1). Red = their corners, numbered c<n>:",
                "a RAIL runs between two of them (the master side's); every line of the new skin starts and ends on these (the client 2026-10-07)."], draw=cdraw, key=CKEY)
    say("pictures CORNERS_* (%d): %s" % (len(vs_), K.pic_report()))
say("next: OPEN every WIRE_* frame (WIRES_LOOK.json) - is each line where that feature's edge is, as simple as it can be? - then kit rebuild judge --what wires;")
say("      " + K.RULE_31BH)
say("      a line that is wrong: decide it again in LINES / RAILS (with its reason) and run skin-wires again; ok: kit rebuild skin-build")
print("DONE", flush=True)

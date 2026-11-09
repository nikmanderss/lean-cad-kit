# THE FEATURE MAP
# merge_smooth
# skin-labels  skin-rim  skin-labels
# FEATURES
# FEATURES
# MAX_AREA
# skin-labels
# skin-labels  skin-labels
# FEATURES  features.json  FEATURES  skin-wires
# FEATURES
# FEATURES  MAX_AREA
# FEATURES  skin-labels
import os, sys, json, time, shutil
if not globals().get("_SK_INNER"):      # 31br D3 (2026-10-29): a crash's TRACEBACK reaches the log
    import runpy as _rp3, traceback as _tb3
    try: _rp3.run_path(os.path.abspath(__file__), init_globals={"_SK_INNER": True}, run_name="__main__")
    except SystemExit: raise
    except BaseException:
        print("TRACEBACK (31br D3) - the crash's place:\n" + _tb3.format_exc(), flush=True); raise
    raise SystemExit(0)
import numpy as np
RUN = os.environ.get("RUN"); KIT_HOME = os.environ.get("KIT_HOME")
MAX_AREA = float(os.environ.get("MAX_AREA", "60")); TINY = float(os.environ.get("TINY", "3")); SMOOTH_DEG = float(os.environ.get("SMOOTH_DEG", "25"))
THIN_MM = float(os.environ.get("THIN_MM", "0.3"))
MAX_SPREAD = float(os.environ.get("MAX_SPREAD", "65")); UNITE = os.environ.get("UNITE", "1") == "1"; MIN_BORDER = float(os.environ.get("MIN_BORDER", "0.5"))
UNITE_MM = float(os.environ.get("UNITE_MM", "3.0")); UNITE_DEG = float(os.environ.get("UNITE_DEG", "10")); STRIP_HALF = float(os.environ.get("STRIP_HALF", "1.2"))
SHOW_NUMBERS = os.environ.get("SHOW_NUMBERS", "0") == "1"
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
if not RUN or not KIT_HOME:
    print("FAIL: RUN and KIT_HOME must be set (the runner sets them: kit rebuild skin-features --job <J> --tag <T>)", flush=True); raise SystemExit(1)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sk_lib as K; K.need_window()
T0 = time.time()
def say(*a): print("%5.0fs " % (time.time() - T0), *a, flush=True)
def num(fmt, *a): return (fmt % a) if SHOW_NUMBERS else ""
SK = K.SK; OUT = K.OUT
lj = os.path.join(SK, "patches_labels.json"); ln = os.path.join(SK, "patches_labels.npz")
rj = os.path.join(SK, "patches_labels_raw.json"); rn = os.path.join(SK, "patches_labels_raw.npz")
if not os.path.isfile(lj) or not os.path.isfile(ln):
    K._fail("FAIL: skin\\patches_labels.* is missing - `kit rebuild skin-labels` writes it")
# skin-labels  skin-labels
mine = False
try: mine = "merge_smooth" in json.load(open(lj, encoding="utf-8"))
except Exception: pass
fresh_raw = False
if (not os.path.isfile(rj)) or (not mine and os.path.getmtime(lj) > os.path.getmtime(rj) + 1.0):
    shutil.copy2(lj, rj); shutil.copy2(ln, rn); fresh_raw = True; say("skin-labels' layout kept as patches_labels_raw.*")
D = json.load(open(rj, encoding="utf-8")); PJ = D["patches"]; Z = np.load(rn); pid = Z["patch"].astype(np.int64).copy(); Nn = Z["Nn"]
LAB_RAW = Z["lab"].copy()
if not all(p["patch"] == i for i, p in enumerate(PJ)): K._fail("FAIL: patches_labels_raw.json is not indexed by patch - run skin-labels again")
R_ = np.load(os.path.join(SK, "regions.npz")); Vu, F = R_["Vu"], R_["F"]
P3_ = Vu[F]; Cn = P3_.mean(1); At = 0.5 * np.linalg.norm(np.cross(P3_[:, 1] - P3_[:, 0], P3_[:, 2] - P3_[:, 0]), axis=1)
mdf = os.path.join(SK, "MIRROR_DECISION.json")
md = json.load(open(mdf, encoding="utf-8")).get("plane", "") if os.path.isfile(mdf) else ""
mp = K.mirror_plane(md) if md else None
side_t = np.sign(Cn @ mp[0] - mp[1]) if mp else np.zeros(len(F))
Et = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); Es = np.sort(Et, 1); tri = np.tile(np.arange(len(F)), 3)
o = np.lexsort((Es[:, 1], Es[:, 0])); Es = Es[o]; tri = tri[o]; same = np.all(Es[1:] == Es[:-1], axis=1)
ta = tri[:-1][same]; tb = tri[1:][same]; el = np.linalg.norm(Vu[Es[:-1][same][:, 0]] - Vu[Es[:-1][same][:, 1]], axis=1)
dih = np.degrees(np.arccos(np.clip((Nn[ta] * Nn[tb]).sum(1), -1, 1)))
kind = {p["patch"]: p["kind"] for p in PJ}
grp = {p["patch"]: (p["grp"] if p.get("grp") is not None else ("own", p["patch"])) for p in PJ}
absorbed = {p["patch"]: [] for p in PJ}
def borders(pid):
    m = pid[ta] != pid[tb]; a = pid[ta][m]; b = pid[tb][m]; lo = np.minimum(a, b); hi = np.maximum(a, b)
    out = {}
    for x, y, L, d in zip(lo, hi, el[m], dih[m]): out.setdefault((int(x), int(y)), []).append((L, d))
    return {k: (float(np.sum([t[0] for t in v])), float(np.percentile([t[1] for t in v], 90))) for k, v in out.items()}
CACHE = {}
def refresh():
    CACHE["alive"] = set(int(x) for x in np.unique(pid)); CACHE["areas"] = np.bincount(pid, weights=At, minlength=len(PJ))
def area(p): return float(CACHE["areas"][p])
def spread(tm):
    """the angle (deg) within which 98 % of the face's area lies from its area-weighted mean normal"""
    nm = (Nn[tm] * At[tm, None]).sum(0); nm /= max(np.linalg.norm(nm), 1e-12)
    ang = np.degrees(np.arccos(np.clip(Nn[tm] @ nm, -1, 1))); o_ = np.argsort(ang); cw = np.cumsum(At[tm][o_]) / max(At[tm].sum(), 1e-12)
    return float(ang[o_][min(np.searchsorted(cw, 0.98), len(o_) - 1)])
def turn_ok(tm_new, tm_old):
    sn = spread(tm_new)
    if sn <= MAX_SPREAD: return True
    return len(tm_old) > 0 and sn <= spread(tm_old) + 5.0
def _ncomp(edges):
    """the number of connected pieces of the graph the edges make (numpy union-find - the same count scipy's connected_components gave)"""
    nodes, inv = np.unique(edges.ravel(), return_inverse=True); e = inv.reshape(-1, 2); c = np.arange(len(nodes))
    while True:
        lo = np.minimum(c[e[:, 0]], c[e[:, 1]]); old = c.copy()
        np.minimum.at(c, e[:, 0], lo); np.minimum.at(c, e[:, 1], lo); c = c[c]
        if np.array_equal(c, old): break
    return len(np.unique(c))
def nloops(tm):
    """the face's boundary loops: 1 = no hole"""
    T = F[tm]; E2 = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
    u_, c_ = np.unique(E2, axis=0, return_counts=True); bnd = u_[c_ == 1]
    if not len(bnd): return 0
    return _ncomp(bnd)
def side_of(p):
    s = float(np.mean(side_t[pid == p])) if (pid == p).any() else 0.0
    return -1 if s < -0.5 else (1 if s > 0.5 else 0)
def live_members(g): return sorted(p for p in grp if grp[p] == g and p in CACHE["alive"])
log = []
# FEATURES
FEATURES = os.environ.get("FEATURES", "").strip()
FM = {}
if FEATURES:
    try:
        FM = json.load(open(FEATURES, encoding="utf-8"))
        FM_WHY = FM.pop("_why", None) if isinstance(FM, dict) else None
        if not isinstance(FM, dict) or not all(isinstance(v, list) for v in FM.values()): raise ValueError("not {\"feature\": [face ids]}")
        if not isinstance(FM_WHY, dict): FM_WHY = {}
        _nowhy = [k_ for k_ in FM if len(str(FM_WHY.get(k_, "")).strip()) < 10]
        if _nowhy: raise ValueError("every feature carries its reason (31bq B22, the client 2026-10-19): add \"_why\": {\"<feature>\": \"<why these faces are one feature>\"} - missing for %s" % _nowhy)
    except (OSError, ValueError) as ex:
        K._fail("FAIL: FEATURES %s: %s - it is a json file {\"feature name\": [original face ids, the master side's], \"_why\": {\"feature name\": \"its reason\"}}" % (FEATURES, ex))
    master_face = {}
    for p_ in PJ:
        if p_.get("mirror_of") is None and p_.get("grp") is not None and p_.get("face_src") is not None: master_face[p_["grp"]] = int(p_["face_src"])
    # FEATURES
    _alias = {}
    for p_ in PJ:
        if p_.get("mirror_of") is not None and p_.get("face_src") is not None:
            _m = master_face.get(p_.get("grp"))
            if _m is not None and int(p_["face_src"]) != int(_m): _alias[int(p_["face_src"])] = int(_m)
    feat_of_face = {}; _naliased = 0
    for nm_, ids_ in FM.items():
        for x_ in ids_:
            _k = _alias.get(int(x_), int(x_)); _naliased += int(_k != int(x_))
            if nm_ not in feat_of_face.setdefault(_k, []): feat_of_face[_k].append(nm_)
    if _naliased: say("FEATURES: %d id(s) named the twin side's original faces - taken as their master's (a feature map is side-free)" % _naliased)
    feat = {}
    for p_ in PJ:
        if p_["kind"] == "cap": continue
        mf = master_face.get(p_.get("grp"), p_.get("face_src"))
        if mf is not None and int(mf) in feat_of_face and len(feat_of_face[int(mf)]) == 1: feat[p_["patch"]] = feat_of_face[int(mf)][0]
    _B0 = borders(pid)
    for p_ in PJ:
        if p_["kind"] == "cap" or p_["patch"] in feat: continue
        mf = master_face.get(p_.get("grp"), p_.get("face_src"))
        if mf is None or int(mf) not in feat_of_face: continue
        best_ = None
        for (a_, b_), (L_, d_) in _B0.items():
            q_ = b_ if a_ == p_["patch"] else (a_ if b_ == p_["patch"] else None)
            if q_ is None or q_ not in feat or feat[q_] not in feat_of_face[int(mf)]: continue
            if best_ is None or L_ > best_[0]: best_ = (L_, feat[q_])
        if best_: feat[p_["patch"]] = best_[1]
    refresh()
    par = {p: p for p in feat}
    def fnd(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for (a_, b_), (L_, d_) in borders(pid).items():
        if a_ in feat and b_ in feat and feat[a_] == feat[b_] and L_ >= MIN_BORDER:
            if side_of(a_) * side_of(b_) < 0: continue
            ra, rb = fnd(a_), fnd(b_)
            if ra != rb: par[max(ra, rb)] = min(ra, rb)
    nmerge = 0
    for p_ in sorted(feat):
        r_ = fnd(p_)
        if r_ != p_ and (pid == p_).any():
            pid[pid == p_] = r_; absorbed[r_] += [p_] + absorbed[p_]; nmerge += 1
            if kind[p_] != "orig" or kind[r_] != "orig" or PJ[p_].get("face") != PJ[r_].get("face"): kind[r_] = "changed"
    refresh()
    log.append(["features", FEATURES, nmerge])
    byf = {}
    for p_ in sorted(CACHE["alive"]):
        if p_ in feat: byf.setdefault(feat[p_], []).append(p_)
    say("FEATURES (%s): %d patch(es) joined their feature's face; faces per feature: %s" % (os.path.basename(FEATURES), nmerge, ", ".join("%s %d" % (k, len(v)) for k, v in sorted(byf.items()))))
    unknown = sorted(set(int(x) for ids_ in FM.values() for x in ids_) - set(int(p_.get("face_src")) for p_ in PJ if p_.get("face_src") is not None))
    if unknown: say("   original face(s) named in FEATURES that no patch comes from: %s (a typo, or the points gave them no face)" % unknown)
    unmapped = [p_ for p_ in sorted(CACHE["alive"]) if kind[p_] != "cap" and p_ not in feat]
    if unmapped: say("   patches in NO feature (left as they are): %s" % ", ".join("%d (%s%s)" % (p_, PJ[p_].get("src", "")[:28], num(", %.1f mm2", area(p_))) for p_ in unmapped))
    with open(os.path.join(SK, "features.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(FM, **{"_why": FM_WHY}), fh, indent=1)        # skin-wires
else:
    try: os.remove(os.path.join(SK, "features.json"))   # skin-wires
    except OSError: pass
    say("no FEATURES: only the smooth merges run. The feature map is the agent's - open FEAT_labels_* (every original face's id on the layout),")
    say("   name each one's FEATURE (\"A spine, A vane, a support\"), write {\"feature\": [ids]} and run again with --set FEATURES=<that json>")
refresh()
if UNITE and mp:
    B = borders(pid)
    for g in sorted(set(grp.values()), key=str):
        ms = [p for p in live_members(g) if kind[p] != "cap"]
        if len(ms) != 2: continue
        a, b = ms; bb = B.get((a, b))
        if not bb or bb[0] < max(MIN_BORDER, UNITE_MM) or bb[1] > min(SMOOTH_DEG, UNITE_DEG): continue
        tm = np.nonzero((pid == a) | (pid == b))[0]
        if not turn_ok(tm, np.nonzero(pid == a)[0]) or nloops(tm) != 1: continue
        same_surface = kind[a] == "orig" and kind[b] == "orig" and PJ[a].get("face") == PJ[b].get("face")
        pid[pid == b] = a; absorbed[a] += [b] + absorbed[b]; refresh()
        if not same_surface: kind[a] = "changed"
        log.append(["unite", a, b, round(bb[0], 2), round(bb[1], 1)])
        say("UNITED twin pair %d + %d into one face across the plane%s%s" % (a, b, num(" (border %.1f mm, %.0f deg)", bb[0], bb[1]), "" if same_surface else " - fitted"))
for rnd in range(80):
    refresh(); live = sorted(CACHE["alive"])
    B = borders(pid); nb = {}
    for (x, y), v in B.items(): nb.setdefault(x, {})[y] = v; nb.setdefault(y, {})[x] = v
    groups = sorted(set(grp[p] for p in live if kind[p] != "cap"), key=lambda g: max(area(p) for p in live_members(g)))
    done = False
    for g in groups:
        ms = live_members(g); ga = max(area(p) for p in ms)
        def _width(p):
            per = sum(L for q, (L, d) in nb.get(p, {}).items()); return (2.0 * area(p) / per) if per > 0 else 9e9
        thin = all(_width(p) < THIN_MM for p in ms)
        if ga >= MAX_AREA and not thin: break
        tiny = ga < TINY or thin
        cand = {}
        for p in ms:
            for q, (L, d) in nb.get(p, {}).items():
                if kind[q] == "cap" or grp[q] == g or L < MIN_BORDER: continue
                if d > SMOOTH_DEG and not tiny: continue
                cand[grp[q]] = cand.get(grp[q], 0.0) + L
        if not cand: continue
        def fitted_first(h): return (0 if any(kind[q] != "orig" for q in live_members(h)) else 1, -cand[h])
        for h in sorted(cand, key=fitted_first):
            hm = live_members(h)
            if len(ms) == 1 and side_of(ms[0]) == 0 and len(hm) == 2:
                _d = np.abs(Cn[pid == ms[0]] @ mp[0] - mp[1]) if mp else np.array([9e9])
                if _d.max() > STRIP_HALF: continue
            if all(kind[q] == "orig" for q in hm) and max(area(q) for q in hm) >= MAX_AREA and not thin: continue
            by_side = {side_of(q): q for q in hm}
            new = pid.copy()
            for p in ms:
                tp = np.nonzero(pid == p)[0]
                if len(hm) == 1: new[tp] = hm[0]; continue
                sp_ = side_of(p)
                if sp_ != 0 and sp_ in by_side: new[tp] = by_side[sp_]; continue
                for t_s in (-1, 1, 0):
                    sel = tp[side_t[tp] == t_s]
                    if len(sel): new[sel] = by_side.get(t_s if t_s != 0 else -1, hm[0])
            touched = set(int(x) for x in np.unique(new[np.isin(pid, ms)]))
            if any((not turn_ok(np.nonzero(new == q)[0], np.nonzero(pid == q)[0])) or nloops(np.nonzero(new == q)[0]) != 1 for q in touched): continue
            for q in touched:
                if kind[q] == "orig" and not thin: kind[q] = "changed"
                absorbed[q] += [p for p in ms if p not in touched] + [x for p in ms for x in absorbed[p]]
            pid = new; done = True
            log.append(["merge", ms, sorted(touched), round(ga, 2), round(cand[h], 2)])
            say("MERGED face(s) %s (%s%s) into %s%s" % (ms, ("a sliver %.2f mm wide" % min(_width(p) for p in ms)) if thin else ("a sliver" if tiny else "small, smooth"), num(", %.1f mm2", ga), sorted(touched), num(" (border %.1f mm)", cand[h])))
            break
        if done: break
    if not done: break
live = sorted(set(int(x) for x in np.unique(pid))); remap = {p: i for i, p in enumerate(live)}
newp = []
for p in live:
    r = {k: v for k, v in PJ[p].items() if k not in ("area_mm2", "tris", "spread_deg", "normal_strength")}
    r["patch"] = remap[p]; r["kind"] = kind[p]
    if kind[p] != "orig": r.pop("face", None)
    if r.get("mirror_of") is not None: r["mirror_of"] = remap.get(r["mirror_of"])     # skin-labels  mirror_of
    if absorbed[p]: r["merged_from"] = sorted(set(absorbed[p]))
    tm = pid == p; nm = (Nn[tm] * At[tm, None]).sum(0); s_ = float(np.linalg.norm(nm)); nm /= max(s_, 1e-12)
    r.update({"area_mm2": round(float(At[tm].sum()), 3), "tris": int(tm.sum()), "spread_deg": round(float(np.degrees(np.arccos(np.clip((Nn[tm] @ nm).min(), -1, 1)))), 1),
              "normal_strength": round(s_ / max(At[tm].sum(), 1e-12), 3)})
    newp.append(r)
# mirror_of  skin-labels
_repaired, _asym, _bad = K.repair_twins(PJ, live, absorbed, remap, newp, say)
if _repaired or _asym or _bad:
    say("TWINS AFTER THE MERGES (31be): %d pair(s) paired again from the raw layout's pairs%s%s" % (_repaired,
        ("; ASYMMETRIC: master %s's twins sit in %s - the merges were not mirrored, the mirror check will say so" % (", ".join(str(a) for a, _ in _asym), [h for _, h in _asym])) if _asym else "",
        ("; GROUPS OF MORE THAN TWO (a kit fault - say so in a NOTE): %s" % _bad) if _bad else ""))
pid2 = np.array([remap[int(x)] for x in pid]); lab2 = np.array([newp[i]["label"] for i in pid2])
K.same_kind_groups(newp)
np.savez_compressed(ln, lab=lab2, patch=pid2, Nn=Nn)
D2 = dict(D); D2["patches"] = newp; D2["merge_smooth"] = {"FEATURES": FEATURES or None, "UNITE_MM": UNITE_MM, "UNITE_DEG": UNITE_DEG, "STRIP_HALF": STRIP_HALF, "MAX_AREA": MAX_AREA,
                                                         "TINY": TINY, "SMOOTH_DEG": SMOOTH_DEG, "MAX_SPREAD": MAX_SPREAD, "UNITE": UNITE, "log": log, "tag": K.TAG,
                                                         "when": time.strftime("%Y-%m-%d %H:%M:%S")}
with open(lj, "w", encoding="utf-8") as fh:
    json.dump(D2, fh, indent=1)
nsk = sum(1 for r in newp if r["kind"] != "cap"); nor = sum(1 for r in newp if r["kind"] == "orig")
say("FACES: %d skin faces (%d on an original surface) + %d caps, from %d skin faces - %d merge(s), %d twin pair(s) united"
    % (nsk, nor, sum(1 for r in newp if r["kind"] == "cap"), sum(1 for r in PJ if r["kind"] != "cap"), sum(1 for e in log if e[0] == "merge"), sum(1 for e in log if e[0] == "unite")))
small = [r for r in sorted(newp, key=lambda r: r["area_mm2"]) if r["kind"] != "cap" and r["area_mm2"] < MAX_AREA]
_raw_of = {remap[p]: p for p in live}
if small: say("   still small (no smooth neighbour took them) - in the FINAL numbering after the merges (the MERGED lines above use the layout's raw ids; FEAT_features_* shows the final ones): face(s) %s"
              % ", ".join("%d%s %s%s" % (r["patch"], (" (raw %d)" % _raw_of[r["patch"]]) if _raw_of.get(r["patch"]) != r["patch"] else "", r["kind"], num(" %.1f mm2", r["area_mm2"])) for r in small))
# FEATURES
# FEATURES
import colorsys
sys.path.insert(0, KIT_HOME); import kitlib_render as R
from PIL import Image, ImageDraw
FL = os.environ.get("FEAT_LABELS", "auto").strip().lower()
os.makedirs(OUT, exist_ok=True)
have_labels = any(f.startswith("FEAT_labels_") for f in os.listdir(OUT))
want_labels = (FL == "1") or (FL == "auto" and (not FEATURES or fresh_raw or not have_labels))
for f_ in os.listdir(OUT):
    if f_.startswith("FEAT_features_") and f_.endswith(".png"): os.remove(os.path.join(OUT, f_))
    if want_labels and f_.startswith("FEAT_labels_") and f_.endswith(".png"): os.remove(os.path.join(OUT, f_))
LAB = LAB_RAW.astype(np.int64)
TWIN = LAB >= K.MIRROR_OFF; BASE = np.where(TWIN, LAB - K.MIRROR_OFF, LAB)
views = [("top", (0, 0, -1)), ("bottom", (0, 0, 1)), ("side_xneg", (1, 0, 0)), ("side_xpos", (-1, 0, 0)),
         ("iso_fl_below", tuple(-np.array([-0.5, -0.6, -0.62]) / np.linalg.norm([-0.5, -0.6, -0.62]))),
         ("iso_al_above", tuple(-np.array([-0.5, 0.6, 0.62]) / np.linalg.norm([-0.5, 0.6, 0.62])))]
if K.PICS == "quick":
    views = [v for v in views if v[0] in ("top", "bottom", "iso_fl_below", "iso_al_above")]
full = tuple(K.WIN); foc = K.corners(full); pad = 1.0
frames = []
def picture(mode):
    if mode == "features":
        f_of = {}; names = {}
        for i, (nm, ids) in enumerate(FM.items()):
            for x in ids: f_of[int(x)] = i
            names[i] = nm
        key = np.array([f_of.get(int(b), -1) for b in BASE])
        label_of = lambda k, m: names[k]
    else:
        key = LAB.copy(); names = {}
        label_of = lambda k, m: (str(int(k - K.MIRROR_OFF)) + "'") if k >= K.MIRROR_OFF else str(int(k))
    keys = [k for k in np.unique(key)]
    rng = {k: i for i, k in enumerate(keys)}
    pal = np.array([colorsys.hsv_to_rgb((i * 0.61803) % 1.0, 0.55 + 0.35 * ((i * 7) % 3) / 2, 0.95) for i in range(len(keys))])
    C = pal[[rng[k] for k in key]]
    C[key < 0] = (0.35, 0.35, 0.38)
    for nm, d in views:
        path = os.path.join(OUT, "FEAT_%s_%s.png" % (mode, nm))
        st = {}
        mmpx = R.render(path, [("v", Vu, F, C)], d, W=1500, pad=pad, focus=foc, title=nm, edges=False, stats=st)
        d3, r3, u3 = R.basis(d); x0 = (foc @ r3).min() - pad; y1 = (foc @ u3).max() + pad
        own = st["own"]; Hh, Ww = own.shape
        im = Image.open(path).convert("RGB"); dr = ImageDraw.Draw(im)
        for k in keys:
            if k < 0: continue
            m = key == k
            if At[m].sum() < 2.0: continue
            cen = (Cn[m] * At[m, None]).sum(0) / At[m].sum()
            idx = np.nonzero(m)[0]
            q = np.stack([(Cn[idx] @ r3 - x0) / mmpx, (y1 - Cn[idx] @ u3) / mmpx], 1).astype(int)
            ok = (q[:, 0] >= 0) & (q[:, 0] < Ww) & (q[:, 1] >= 0) & (q[:, 1] < Hh)
            if not ok.any(): continue
            vis = ok.copy(); vis[ok] = own[q[ok, 1], q[ok, 0]] == idx[ok]
            if not vis.any(): continue
            j = np.argmin(np.linalg.norm(Cn[idx[vis]] - cen, axis=1)); x, y = q[vis][j]
            txt = label_of(k, m)
            dr.rectangle([x - 2, y - 2, x + 8 * len(txt) + 2, y + 14], fill=(0, 0, 0)); dr.text((x, y), txt, fill=(255, 255, 120), font=K.F16)
        out = Image.new("RGB", (im.width, im.height + 108), (16, 16, 20)); od = ImageDraw.Draw(out)
        od.text((10, 8), "FEATURE MAP %s - %s - %s" % ("(the features, named)" if mode == "features" else "(skin-labels' layout: each original face's id; 1121' = the mirror of 1121)", nm, K.TAG), fill=(255, 235, 120), font=K.F22)
        out.paste(im, (0, 40))
        for i_, t_ in enumerate(K.BORDER_NOTE): od.text((10, im.height + 48 + 24 * i_), t_, fill=K.BORDER_COL, font=K.F16)
        _q = K.source_quality(Vu, F)
        try: K._stamp_if_defective(out, od, _q, 40)
        except Exception: pass
        out.save(path); frames.append(path)
        if hasattr(R, "index_frame"): R.index_frame(path, full, d, "FEATURE MAP %s %s" % (mode, nm), quality=_q)
drawn = []
if want_labels: picture("labels"); drawn.append("FEAT_labels_* (%d)" % len(views))
if FEATURES: picture("features"); drawn.append("FEAT_features_* (%d)" % len(views))
say("pictures: %s" % (", ".join(drawn) or "none new (FEAT_labels_* are current; FEAT_LABELS=1 draws them again)"))
say("next: open them; then `kit rebuild skin-rim` (THE EXACT FRAME on these faces) and judge its LAYOUT_* frames")
print("DONE", flush=True)

# kit rebuild  skin-rim
# skin-labels
# skin-labels
# PRIOR ART
import os, sys, json, time, colorsys
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
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
from PIL import Image, ImageDraw
RIM_MM = float(os.environ.get("RIM_MM", "0.8")); REACH_MM = float(os.environ.get("REACH_MM", "1.5"))
BREP_SRC = K.brep_source()
SK = K.SK; OUT = K.OUT
T0 = time.time()
def say(*a): print("%5.0fs " % (time.time() - T0), *a, flush=True)
def P3(v): return np.array([v.X, v.Y, v.Z]) if hasattr(v, "X") else np.array([v.x, v.y, v.z])
# skin-labels
Z = np.load(os.path.join(SK, "regions.npz")); Vu, F = Z["Vu"], Z["F"]
FIDt = np.asarray(Z["fid"], np.int64) if ("fid" in Z.files and BREP_SRC) else None
PZ = np.load(os.path.join(SK, "patches_labels.npz")); pid0 = PZ["patch"].copy(); lab0 = PZ["lab"]; Nn = PZ["Nn"]
PJ = json.load(open(os.path.join(SK, "patches_labels.json")))["patches"]
Tv = Vu[F]; Cn = Tv.mean(1); At = 0.5 * np.linalg.norm(np.cross(Tv[:, 1] - Tv[:, 0], Tv[:, 2] - Tv[:, 0]), axis=1)
E_ = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); Es = np.sort(E_, 1); tri = np.tile(np.arange(len(F)), 3)
o = np.lexsort((Es[:, 1], Es[:, 0])); Es = Es[o]; tri = tri[o]; same = np.all(Es[1:] == Es[:-1], axis=1)
ta = tri[:-1][same]; tb = tri[1:][same]
walls = list(K.WALLS)   # REBUILD_region.json
def wall_of(P): return K.wall_of(P)
if not os.path.isfile(os.path.join(RUN, "wall_caps.brep")): K._fail("FAIL: wall_caps.brep is missing - THE REINSERT FACES COME FIRST (the client 2026-10-06: \"Step 1 is get the perfect reinsert faces\"): kit rebuild reinsert --set STEP=1")
wc = Part.Shape(); wc.importBrep(os.path.join(RUN, "wall_caps.brep")); BFc = wc.Faces
Bwall = [wall_of(np.array([P3(v) for v in f.Vertexes]))[0] for f in BFc]
capp = [p for p in PJ if p["kind"] == "cap"]; capset = set(p["patch"] for p in capp)
cmap = {}; used = set()
for p in sorted(capp, key=lambda p: -p["area_mm2"]):
    cands = [(abs(BFc[b].Area - p["area_mm2"]), b) for b in range(len(BFc)) if Bwall[b] == p["wall"] and b not in used]
    if cands:
        d, b = min(cands)
        if d < 0.3 * BFc[b].Area + 0.5: cmap[p["patch"]] = b; used.add(b)
junk = [p["patch"] for p in capp if p["patch"] not in cmap]; capof = {b: c for c, b in cmap.items()}
assert len(cmap) == len(BFc), "a body cap face has no cap patch: %s" % [b for b in range(len(BFc)) if b not in used]
say("frame: %d body cap faces, each with its cap patch %s; junk voxel caps %s" % (len(BFc), cmap, junk))
ct = Part.Shape(); ct.importBrep(os.path.join(RUN, "content.brep")); cfs = [f for so in ct.Solids for f in so.Faces]
def onwall(f): return isinstance(f.Surface, Part.Plane) and wall_of(np.array([P3(v) for v in f.Vertexes]))[1] < 1e-3
ccaps = [f for f in cfs if onwall(f)]; cskin = [f for f in cfs if not onwall(f)]
body = Part.Shape(); body.importBrep(K.BODY); RB = body.Faces
wb = K.WIN; near = [i for i, f in enumerate(RB) if f.BoundBox.XMax >= wb[0] - 3 and f.BoundBox.XMin <= wb[1] + 3 and f.BoundBox.YMax >= wb[2] - 3 and f.BoundBox.YMin <= wb[3] + 3 and f.BoundBox.ZMax >= wb[4] - 3 and f.BoundBox.ZMin <= wb[5] + 3]
def rim_face_id(g, m):
    V_, T_ = g.tessellate(0.02); V_ = np.array([P3(q) for q in V_]); T_ = np.array(T_)
    c_ = V_[T_].mean(1) if len(T_) else V_; q = c_[np.argmin(np.linalg.norm(c_ - m, axis=1))]; pv = Part.Vertex(V3(*q))
    cand = [i for i in near if RB[i].BoundBox.isInside(V3(*q)) or RB[i].BoundBox.enlarge(0.05) is None]
    cand = [i for i in near if (RB[i].BoundBox.XMin - 0.05 <= q[0] <= RB[i].BoundBox.XMax + 0.05 and RB[i].BoundBox.YMin - 0.05 <= q[1] <= RB[i].BoundBox.YMax + 0.05 and RB[i].BoundBox.ZMin - 0.05 <= q[2] <= RB[i].BoundBox.ZMax + 0.05)]
    return min((RB[i].distToShape(pv)[0], i) for i in cand)
pats_of = {}
for p in PJ:
    if "face_src" in p: pats_of.setdefault(int(p["face_src"]), []).append(p["patch"])
noncap = ~np.isin(pid0, list(capset))
Tnc = cKDTree(Cn[noncap]); pnc = pid0[noncap]
def samples(e, step=0.05):
    n = max(3, int(e.Length / step) + 1); return np.array([P3(q) for q in e.discretize(Number=n)])
EI = []; ES = []; own = {}
for b, B in enumerate(BFc):
    cb = min(ccaps, key=lambda g: (g.CenterOfMass - B.CenterOfMass).Length + abs(g.Area - B.Area))
    for i, e in enumerate(B.Edges):
        S = samples(e); EI += [(b, i)] * len(S); ES.append(S)
        shr = [b2 for b2 in range(len(BFc)) if b2 != b and any(e.isSame(g) for g in BFc[b2].Edges)]
        if shr: own[(b, i)] = {"kind": "capcap", "caps": [b, shr[0]]}; continue
        ce = min(cb.Edges, key=lambda g: (g.CenterOfMass - e.CenterOfMass).Length + abs(g.Length - e.Length))
        nb = [g for g in cskin if any(ce.isSame(x) for x in g.Edges)]
        m = S[len(S) // 2]
        dd, rid = rim_face_id(nb[0], m) if nb else (99.0, -1)
        reach = {}
        for c_ in pats_of.get(rid, []):
            mk = pid0 == c_
            if mk.any(): reach[c_] = float(np.median(cKDTree(Cn[mk]).query(S)[0]))
        ok = {c_: r_ for c_, r_ in reach.items() if r_ < REACH_MM}
        if ok: who = min(ok, key=ok.get); how = "from its original face %d (%.2f mm off the voxel patch)" % (rid, ok[who])
        elif reach and BREP_SRC:
            # skin-frame
            who = min(reach, key=reach.get); how = "from its original face %d (a B-rep source: the edge lies on the face; its mesh %.2f mm off)" % (rid, reach[who])
        else:
            d_, ix = Tnc.query(S); vals, cnt = np.unique(pnc[ix], return_counts=True); vals_ok = [(c_, n_) for c_, n_ in zip(vals, cnt) if c_ not in junk]
            who = int(max(vals_ok, key=lambda t: t[1])[0]); how = "nearest voxel patch (original face %d has %s)" % (rid, ("patches %s, none within %.1f mm" % (list(reach), REACH_MM)) if reach else "no patch")
        own[(b, i)] = {"kind": "patch", "patch": int(who), "r31": int(rid), "r31_off": round(dd, 4), "how": how, "len": round(e.Length, 3),
                       "by_face": bool(ok) or bool(reach and BREP_SRC)}
ES = np.vstack(ES); EI = np.array(EI)
for (b, i), r in sorted(own.items()):
    say("   body face %d edge %2d %6.3f mm -> %s" % (b, i, BFc[b].Edges[i].Length, ("CAP|CAP (body faces %s)" % r["caps"]) if r["kind"] == "capcap" else ("patch %d, %s" % (r["patch"], r["how"]))))
d_e, ix_e = cKDTree(ES).query(Cn, workers=-1)
rim = d_e < RIM_MM
istrue = np.zeros(len(F), bool)
for c_, b in cmap.items():
    n, c0 = walls[Bwall[b]]
    istrue |= (pid0 == c_) & (np.abs(Cn @ n - c0) < 0.2) & ((Nn @ n) < -0.9)
import heapq
free = (rim & ~istrue) | np.isin(pid0, junk)
allow = {}
for t in np.nonzero(free)[0]:
    if not rim[t]: continue
    b, i = EI[ix_e[t]]; r = own[(b, i)]
    allow[t] = {capof[r["caps"][0]], capof[r["caps"][1]]} if r["kind"] == "capcap" else {r["patch"]}
nbt = [[] for _ in range(len(F))]
for x, y in zip(ta, tb): nbt[x].append(y); nbt[y].append(x)
pid = pid0.copy(); pid[free] = -1
def flood(restrict):
    hq = []
    for t in np.nonzero(pid >= 0)[0]:
        for u in nbt[t]:
            if pid[u] < 0: heapq.heappush(hq, (float(np.linalg.norm(Cn[u] - Cn[t])), int(u), int(pid[t])))
    n_ = 0
    while hq:
        dd, u, L = heapq.heappop(hq)
        if pid[u] >= 0: continue
        if L in junk: continue
        if restrict and u in allow and L not in allow[u]: continue
        pid[u] = L; n_ += 1
        for w in nbt[u]:
            if pid[w] < 0: heapq.heappush(hq, (dd + float(np.linalg.norm(Cn[w] - Cn[u])), int(w), L))
    return n_
n1 = flood(True); left = int((pid < 0).sum()); n2 = flood(False) if left else 0
ch = int((pid != pid0).sum())
say("rim (within %.1f mm of a cap edge): %d triangles, %d free; filled by an allowed face %d, by any neighbour %d; %d changed face; junk cap triangles left %d"
    % (RIM_MM, int(rim.sum()), int(free.sum()), n1, n2, ch, int(np.isin(pid, junk).sum())))
def comps_of(lbl):
    m = lbl[ta] == lbl[tb]; A = sp.coo_matrix((np.ones(int(m.sum())), (ta[m], tb[m])), shape=(len(F), len(F)))
    return connected_components(A, directed=False)[1]
cc = comps_of(pid); nstray = 0
for p_ in np.unique(pid):
    cs = np.unique(cc[pid == p_])
    if len(cs) > 1:
        ar = sorted([round(float(At[cc == c_].sum()), 3) for c_ in cs], reverse=True); nstray += 1
        say("   FACE %d IN %d PIECES: %s mm2" % (p_, len(cs), ar))
say("faces in more than one piece: %d" % nstray)
fin = {}
for (b, i), r in own.items():
    if r["kind"] == "capcap": fin["%d_%d" % (b, i)] = {"kind": "capcap", "caps": r["caps"]}; continue
    S = ES[EI[:, 0] == b]; S = ES[(EI[:, 0] == b) & (EI[:, 1] == i)]
    nn = ~np.isin(pid, list(capset)); _, ix = cKDTree(Cn[nn]).query(S); vals, cnt = np.unique(pid[nn][ix], return_counts=True)
    w = int(vals[np.argmax(cnt)])
    _rid = int(r.get("r31", -1))
    _w_has_rid = bool(FIDt is not None and ((pid0 == w) & (FIDt == _rid)).any())
    if w != r["patch"] and BREP_SRC and r.get("by_face") and not _w_has_rid:
        # two pieces
        # ORIGINAL
        # skin-frame
        say("   body face %d edge %d: the rim's mesh beside it is %d's, but the edge lies on original face %d - its owner %d stands (a B-rep source)" % (b, i, w, r["r31"], r["patch"])); w = r["patch"]
    fin["%d_%d" % (b, i)] = dict(r, patch_final=w)
    if w != r["patch"]: say("   body face %d edge %d: owner %d could not hold the rim, %d has it" % (b, i, r["patch"], w))
nv7 = 0
for p_ in range(len(PJ)):
    if PJ[p_].get("kind") != "orig" or not (pid == p_).any(): continue
    foreign = sorted(set(int(r["r31"]) for r in fin.values() if r.get("kind") == "patch" and int(r.get("patch_final", -1)) == p_
                         and int(r.get("r31", -1)) >= 0 and int(r["r31"]) != int(PJ[p_].get("face", -2))))
    if foreign:
        PJ[p_]["kind"] = "changed"; PJ[p_]["not_orig"] = "owns wall edges of original faces %s" % foreign; PJ[p_].pop("face", None); nv7 += 1
        say("   face %d (original face %s): owns wall edges of %s - fitted, not kept on the original surface" % (p_, PJ[p_].get("face_src"), foreign))
ids = [p_ for p_ in range(len(PJ)) if (pid == p_).any()]
remap = {p_: k for k, p_ in enumerate(ids)}; new_pid = np.array([remap[p_] for p_ in pid]) if False else np.vectorize(remap.get)(pid)
patches = []
for p_ in ids:
    rec = dict(PJ[p_]); tm = pid == p_; rec["patch"] = remap[p_]; rec["was"] = p_
    rec["area_mm2"] = round(float(At[tm].sum()), 3); rec["tris"] = int(tm.sum())
    _vb = Vu[np.unique(F[tm].ravel())]
    rec["bbox"] = [round(float(_vb[:, 0].min()), 3), round(float(_vb[:, 0].max()), 3), round(float(_vb[:, 1].min()), 3), round(float(_vb[:, 1].max()), 3),
                   round(float(_vb[:, 2].min()), 3), round(float(_vb[:, 2].max()), 3)]
    if rec["kind"] == "cap": rec["body_face"] = cmap[p_]
    patches.append(rec)
ndem = K.same_kind_groups(patches)
say("FACE LADDER rung 1 at the frame: %d orig face(s) owned another original face's wall edge -> fitted%s; %d face(s) stay on their original surface"
    % (nv7, (" (+%d mirror twin(s) demoted with them)" % ndem) if ndem else "", sum(1 for p in patches if p["kind"] == "orig")))
labn = np.array([PJ[p_]["label"] for p_ in range(len(PJ))])[pid]
np.savez_compressed(os.path.join(SK, "patches.npz"), lab=labn, patch=new_pid, Nn=Nn)
json.dump({"source": "SP8 layout + SP12 rim from the exact frame (wall_caps.brep)", "patches": patches}, open(os.path.join(SK, "patches.json"), "w"), indent=1)
json.dump({"owners": fin, "cap_map_new": {str(remap[c_]): b for c_, b in cmap.items()}, "remap": {str(k): v for k, v in remap.items()}}, open(os.path.join(SK, "frame_owner.json"), "w"), indent=0)
nk = {k: sum(1 for p in patches if p["kind"] == k) for k in ("changed", "cap", "orig")}
say("FACES: %d (%d skin: %d kept on the original surface, %d to the flat / fit rungs; %d caps = the %d body faces); junk caps dropped %d"
    % (len(patches), nk["changed"] + nk["orig"], nk["orig"], nk["changed"], nk["cap"], len(BFc), len(junk)))
_crease = {}
for key_, r_ in fin.items():
    if r_.get("kind") != "patch": continue
    pf_ = remap.get(int(r_.get("patch_final", -1)))
    if pf_ is None or patches[pf_]["kind"] != "changed": continue
    _crease.setdefault(pf_, [0, 0.0]); _crease[pf_][0] += 1; _crease[pf_][1] += float(r_.get("len", 0.0))
# wall_edges
say("   changed faces owning a wall edge of the edit region: %d of %d (skin\\patches.json wall_edges; a crease there shows in review-body's station frames after the trial)" % (len(_crease), nk["changed"]))
for p_, (n_, l_) in _crease.items(): patches[p_]["wall_edges"] = {"count": n_, "length_mm": round(l_, 2)}
json.dump({"source": "SP8 layout + SP12 rim from the exact frame (wall_caps.brep)", "patches": patches}, open(os.path.join(SK, "patches.json"), "w"), indent=1)
PAL = np.array([colorsys.hsv_to_rgb(hh, ss, vv) for hh, ss, vv in [(0.0, .75, .95), (0.08, .8, .95), (0.15, .8, .95), (0.3, .7, .85), (0.45, .75, .9), (0.55, .7, .95),
                 (0.65, .6, .95), (0.75, .6, .9), (0.85, .6, .95), (0.95, .4, .95), (0.12, .35, .75), (0.5, .35, .7)]])
inv = new_pid; adjp = {}; cr2 = inv[ta] != inv[tb]
for x, y in zip(inv[ta][cr2], inv[tb][cr2]): adjp.setdefault(int(x), set()).add(int(y)); adjp.setdefault(int(y), set()).add(int(x))
colr = {}
twin = {}
for i, p in enumerate(patches):
    if p.get("grp") is not None and p["kind"] != "cap": twin.setdefault(p["grp"], []).append(i)
for i in sorted(range(len(ids)), key=lambda i: -len(adjp.get(i, ()))):
    if i in colr: continue
    usedc = set(colr.get(j) for j in adjp.get(i, ()))
    mate = [j for j in twin.get(patches[i].get("grp"), []) if j != i and j in colr and colr[j] not in usedc]
    if mate: colr[i] = colr[mate[0]]; continue
    colr[i] = next(k for k in range(len(PAL)) if k not in usedc) if len(usedc) < len(PAL) else i % len(PAL)
pc = PAL[[colr[i] for i in range(len(ids))]]
for i, p in enumerate(patches):
    if p["kind"] == "cap": pc[i] = (0.35, 0.35, 0.40)
    elif p["kind"] == "orig": pc[i] = 0.55 * pc[i] + 0.45 * np.array([0.2, 0.45, 1.0])
C = pc[inv]
import glob as _glob
PKEY = K.pic_key(os.path.join(SK, "patches.json"), os.path.join(SK, "regions.npz"), os.path.join(RUN, "wall_caps.brep"), pics=K.PICS)
K.clear_frames("LAYOUT_", PKEY); K.clear_frames("SP12_", PKEY)
bd = inv[ta] != inv[tb]; segs = Vu[Es[:-1][same][bd]]; segtri = np.stack([ta[bd], tb[bd]], 1)
cap_lines = [(samples(BFc[b].Edges[i], 0.1), own[(b, i)]["kind"] == "capcap") for b in range(len(BFc)) for i in range(len(BFc[b].Edges))]
VIEWS = K.wall_views(BFc, Bwall)
for k, (nm_, d, fb, W, ttl) in enumerate(VIEWS):
    d = np.array(d) / np.linalg.norm(d)
    path = os.path.join(OUT, "SP12_%02d_%s.png" % (k + 1, nm_)); foc = K.corners(fb); pad = 1.0
    if K.pic_hit(path, PKEY): continue
    gb = (fb[0] - 4, fb[1] + 4, fb[2] - 4, fb[3] + 4, fb[4] - 4, fb[5] + 4)
    mm = K._clip_mask(Vu, F, gb) if hasattr(K, "_clip_mask") else ((Cn[:, 0] >= gb[0]) & (Cn[:, 0] <= gb[1]) & (Cn[:, 1] >= gb[2]) & (Cn[:, 1] <= gb[3]) & (Cn[:, 2] >= gb[4]) & (Cn[:, 2] <= gb[5]))
    st = {}
    mmpx = R.render(path, [("v", Vu, F[mm], C[mm])], d, W=W, pad=pad, focus=foc, title=ttl, edges=False, stats=st)
    try: K.stamp_png(path, K.source_quality(Vu, F))
    except Exception: pass
    d3, r3, u3 = R.basis(d); x0 = (foc @ r3).min() - pad; y1 = (foc @ u3).max() + pad
    own_px = st["own"]; sub = np.nonzero(mm)[0]; Hh, Ww = own_px.shape
    im = Image.open(path).convert("RGB"); dr = ImageDraw.Draw(im)
    pj = lambda P: np.stack([(P @ r3 - x0) / mmpx, (y1 - P @ u3) / mmpx], 1)
    for (A_, B_), t1_, t2_ in zip(segs, segtri[:, 0], segtri[:, 1]):
        q = pj(np.vstack([A_, B_])); mx, my = int(q[:, 0].mean()), int(q[:, 1].mean())
        win = own_px[max(0, my - 2):min(Hh, my + 3), max(0, mx - 2):min(Ww, mx + 3)].ravel(); win = win[win >= 0]
        if not len(win) or not np.isin(sub[win], [t1_, t2_]).any(): continue
        dr.line([tuple(q[0]), tuple(q[1])], fill=(255, 255, 255), width=2)
    for S, isc in cap_lines:
        q = pj(S); dr.line([tuple(x) for x in q], fill=(230, 30, 30) if isc else (0, 0, 0), width=2)
    _od0 = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    _h1 = K._wrap(_od0, "SP12  THE RIM FROM THE BODY'S OWN WALL FACES - %d faces - %s" % (len(patches), ttl), K.F22, im.width - 20)
    _l1 = K._wrap(_od0, "One colour per face; grey = the wall caps (the body's own section faces, exact). White = face borders the camera sees. Black = the body's wall-face edges each skin face must end on (drawn over everything). Red = a box corner the material spans: two caps meet there, no skin face. The frame is the WALL's box - the part beyond it is cut off by the frame, not by the model.", K.F16, im.width - 20)
    out = Image.new("RGB", (im.width, 12 + 28 * len(_h1) + im.height + 8 + 24 * (len(_l1) + len(K.BORDER_NOTE)) + 10), (16, 16, 20)); od = ImageDraw.Draw(out); _y = 8
    for t_ in _h1: od.text((10, _y), t_, fill=(255, 235, 120), font=K.F22); _y += 28
    out.paste(im, (0, _y)); _y += im.height + 8
    for t_ in _l1: od.text((10, _y), t_, fill=(235, 235, 235), font=K.F16); _y += 24
    for t_ in K.BORDER_NOTE: od.text((10, _y), t_, fill=K.BORDER_COL, font=K.F16); _y += 24
    out.save(path); K.pic_mark(path, PKEY)
say("pictures SP12_* written")
# skin-labels
# skin-network
_lay = []
for k, (nm_, d, fb, W, ttl) in enumerate(K.views(close=True, below=True)):
    d = np.array(d, float) / np.linalg.norm(d)
    path = os.path.join(OUT, "LAYOUT_%02d_%s.png" % (k + 1, nm_)); foc = K.corners(fb); pad = 1.0
    if K.pic_hit(path, PKEY): _lay.append(path); continue
    gb = (fb[0] - 4, fb[1] + 4, fb[2] - 4, fb[3] + 4, fb[4] - 4, fb[5] + 4)
    mm = K._clip_mask(Vu, F, gb) if hasattr(K, "_clip_mask") else ((Cn[:, 0] >= gb[0]) & (Cn[:, 0] <= gb[1]) & (Cn[:, 1] >= gb[2]) & (Cn[:, 1] <= gb[3]) & (Cn[:, 2] >= gb[4]) & (Cn[:, 2] <= gb[5]))
    st = {}
    mmpx = R.render(path, [("v", Vu, F[mm], C[mm])], d, W=W, pad=pad, focus=foc, title=ttl, edges=False, stats=st)
    try: K.stamp_png(path, K.source_quality(Vu, F))
    except Exception: pass
    d3, r3, u3 = R.basis(d); x0 = (foc @ r3).min() - pad; y1 = (foc @ u3).max() + pad
    own_px = st["own"]; sub = np.nonzero(mm)[0]; Hh, Ww = own_px.shape
    im = Image.open(path).convert("RGB"); dr = ImageDraw.Draw(im)
    pj = lambda P: np.stack([(P @ r3 - x0) / mmpx, (y1 - P @ u3) / mmpx], 1)
    for (A_, B_), t1_, t2_ in zip(segs, segtri[:, 0], segtri[:, 1]):
        q = pj(np.vstack([A_, B_])); mx, my = int(q[:, 0].mean()), int(q[:, 1].mean())
        win = own_px[max(0, my - 2):min(Hh, my + 3), max(0, mx - 2):min(Ww, mx + 3)].ravel(); win = win[win >= 0]
        if not len(win) or not np.isin(sub[win], [t1_, t2_]).any(): continue
        dr.line([tuple(q[0]), tuple(q[1])], fill=(255, 255, 255), width=2)
    _od0 = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    _h1 = K._wrap(_od0, "LAYOUT  THE FACES skin-network WILL BUILD ON - %d faces (%d kept on the original surface) - %s" % (len(patches), nk["orig"], ttl), K.F22, im.width - 20)
    _l1 = K._wrap(_od0, "One colour per face (mirror twins share one where they can); BLUE-TINTED = kept on the original's own surface; grey = the wall caps (exact). White = the borders the camera sees. Judge: every face one simple surface, clean borders, nothing missing, both sides alike on a symmetric edit.", K.F16, im.width - 20)
    out = Image.new("RGB", (im.width, 12 + 28 * len(_h1) + im.height + 8 + 24 * (len(_l1) + len(K.BORDER_NOTE)) + 10), (16, 16, 20)); od = ImageDraw.Draw(out); _y = 8
    for t_ in _h1: od.text((10, _y), t_, fill=(255, 235, 120), font=K.F22); _y += 28
    out.paste(im, (0, _y)); _y += im.height + 8
    for t_ in _l1: od.text((10, _y), t_, fill=(235, 235, 235), font=K.F16); _y += 24
    for t_ in K.BORDER_NOTE: od.text((10, _y), t_, fill=K.BORDER_COL, font=K.F16); _y += 24
    out.save(path); K.pic_mark(path, PKEY); _lay.append(path)
_fr = _lay + sorted(p for p in _glob.glob(os.path.join(OUT, "SP12_*.png")) if K.pic_hit(p, PKEY, count=False))
say(K.pic_report("LAYOUT_* / SP12_*"))
K.source_quality(Vu, F)
K.write_look("layout", _fr, os.path.join(SK, "patches.json"), {"faces": len(patches), "orig": nk["orig"]})
say("LAYOUT_LOOK.json: %d frames (LAYOUT_* the whole layout from above, below and close, SP12_* the rim at the walls) - all written by this run; open every one, then `kit rebuild judge --what layout`" % len(_fr))
print("DONE", flush=True)

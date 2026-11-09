# kit rebuild  skin-labels
# skin-rim
# recorded
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
import scipy.sparse as sp
from scipy.sparse.csgraph import dijkstra, connected_components
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw
import colorsys
A_NOISE = float(os.environ.get("A_NOISE", "0.5")); OPEN_MM = float(os.environ.get("OPEN_MM", "0.4")); ISLAND_MM2 = float(os.environ.get("ISLAND_MM2", "15")); WRAP_STRENGTH = float(os.environ.get("WRAP_STRENGTH", "0.75")); CREASE_DEG = float(os.environ.get("CREASE_DEG", "40")); BAR_MM = float(os.environ.get("BAR_MM", "0.25")); SMOOTH_R = float(os.environ.get("SMOOTH_R", "1.2")); SMOOTH_IT = int(os.environ.get("SMOOTH_IT", "4")); ON_MM = float(os.environ.get("ON_MM", "0.10"))
SK = K.SK
OUT = K.OUT
T0 = time.time()
def say(*a): print("%5.0fs " % (time.time() - T0), *a, flush=True)
Z = np.load(os.path.join(SK, "regions.npz")); Vu, F, vreg = Z["Vu"], Z["F"], Z["vreg"]
PTS = json.load(open(os.path.join(SK, "points1000.json")))
pts = np.array([p[:3] for p in PTS["points"]]); pf = np.array([p[3] for p in PTS["points"]]); pdist = np.array([p[4] if p[4] is not None else 99 for p in PTS["points"]])
ON = (pf >= 0) & (pdist <= ON_MM)
P3 = Vu[F]; Cn = P3.mean(axis=1); Nr = np.cross(P3[:, 1] - P3[:, 0], P3[:, 2] - P3[:, 0]); At = 0.5 * np.linalg.norm(Nr, axis=1); Nn = Nr / np.maximum(2 * At, 1e-12)[:, None]
walls = list(K.WALLS)   # REBUILD_region.json
tcap = np.full(len(F), -1)
for w, (n, c) in enumerate(walls):
    tcap[(np.abs(Cn @ n - c) < 0.15) & ((Nn @ n) < -0.95)] = w
capv = np.zeros(len(Vu), bool); capv[F[tcap >= 0].ravel()] = True
body = Part.Shape(); body.importBrep(K.BODY); BF = body.Faces
FID = np.asarray(Z["fid"], np.int64) if "fid" in Z.files else None   # skin-source
if FID is not None:
    Et0 = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); Es0 = np.sort(Et0, 1); tri0 = np.tile(np.arange(len(F)), 3)
    o0 = np.lexsort((Es0[:, 1], Es0[:, 0])); Es0 = Es0[o0]; tri0 = tri0[o0]; same0 = np.all(Es0[1:] == Es0[:-1], axis=1); ta0 = tri0[:-1][same0]; tb0 = tri0[1:][same0]
    dih0 = (Nn[ta0] * Nn[tb0]).sum(1) >= np.cos(np.radians(CREASE_DEG))
    seeded_faces = np.unique(pf[ON])
    tl, nabs, nown = K.fid_labels(FID, seeded_faces, ta0, tb0, dih0, Cn)
    say("B-REP SOURCE (31bb): every triangle labelled by its ORIGINAL FACE - %d of the %d original faces on the mesh have a point and are KEPT as they are;"
        " %d triangles of faces with no point absorbed by the kept neighbour with the longest border (smooth borders first, then across a crease over %.0f deg - 31bd);"
        " %d unseeded areas nothing kept touches became faces of their own. The borders between kept faces START as the B-rep's edges, the junctions its vertices"
        " - the starting reference: skin-features joins faces, skin-wires redraws, moves, splits any border (%s)"
        % (len(seeded_faces), len(np.unique(FID[FID >= 0])), nabs, CREASE_DEG, nown, K.RULE_31BH))
else:
    lab = np.full(len(Vu), -1, np.int64)
    NO_BANDS = os.environ.get("NO_BANDS", "1") == "1"
    fixv = (vreg >= 0) & (not NO_BANDS)
    lab[fixv] = -1000 - vreg[fixv]
    kdv = cKDTree(Vu); _, sv = kdv.query(pts[ON], workers=-1)
    seed_ok = ~fixv[sv]
    src = sv[seed_ok]; srcl = pf[ON][seed_ok]
    say("seeds: %d ON points -> %d vertices (%d fell in a changed region, left to it); faces with a seed %d" % (int(ON.sum()), len(np.unique(src)), int((~seed_ok).sum()), len(np.unique(srcl))))
    Ev = np.unique(np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1), axis=0)
    EM = {m_["idx"]: m_ for m_ in json.load(open(os.path.join(K.EDGEMAP, "edge_measure.json")))}
    EC = json.load(open(os.path.join(K.EDGEMAP, "edge_classes.json")))
    bpts = []
    for r in EC:
        m_ = EM.get(r["idx"])
        if m_ is None or m_["on_frac"] < 0.8: continue
        if not (r["cls"] == "convex" or (r["cls"] == "frozen" and r.get("cls_geom") == "convex")): continue
        for rr in r["runs"]:
            rr = np.array(rr, float); L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(rr, axis=0), axis=1))])
            sx = np.linspace(0, L[-1], max(2, int(L[-1] / 0.05) + 1)); bpts.append(np.stack([np.interp(sx, L, rr[:, k_]) for k_ in range(3)], 1))
    barv = np.zeros(len(Vu), bool)
    if bpts:
        dB, _ = cKDTree(np.vstack(bpts)).query(Vu, workers=-1); barv = dB < BAR_MM
    vnz = np.zeros_like(Vu)
    for k_ in range(3): np.add.at(vnz, F[:, k_], Nr)
    vnz /= np.maximum(np.linalg.norm(vnz, axis=1), 1e-12)[:, None]
    crease = (vnz[Ev[:, 0]] * vnz[Ev[:, 1]]).sum(1) < np.cos(np.radians(CREASE_DEG))
    say("barriers: %d vertices on %d crisp original edges the voxel follows; %d mesh edges across a crease over %.0f deg" % (int(barv.sum()), len(bpts), int(crease.sum()), CREASE_DEG))
    free = ~fixv & ~barv
    m = free[Ev[:, 0]] & free[Ev[:, 1]] & ~crease
    w_ = np.linalg.norm(Vu[Ev[m, 0]] - Vu[Ev[m, 1]], axis=1)
    G = sp.coo_matrix((np.concatenate([w_, w_]), (np.concatenate([Ev[m, 0], Ev[m, 1]]), np.concatenate([Ev[m, 1], Ev[m, 0]]))), shape=(len(Vu), len(Vu))).tocsr()
    src_u, first = np.unique(src, return_index=True); srcl_u = srcl[first]
    dist, pred, sources = dijkstra(G, indices=src_u, min_only=True, return_predecessors=True)
    reach = np.isfinite(dist) & free
    s2l = dict(zip(src_u.tolist(), srcl_u.tolist()))
    lab[reach] = np.array([s2l[int(s)] for s in sources[reach]])
    un = free & ~reach
    nnew = 0
    if un.any():
        mu = un[Ev[:, 0]] & un[Ev[:, 1]] & ~crease
        nc_, lc_ = connected_components(sp.coo_matrix((np.ones(int(mu.sum())), (Ev[mu, 0], Ev[mu, 1])), shape=(len(Vu), len(Vu))), directed=False)
        for cc_ in np.unique(lc_[un]):
            lab[un & (lc_ == cc_)] = -30000 - int(cc_); nnew += 1
    adjv = [[] for _ in range(len(Vu))]
    for x_, y_ in Ev: adjv[x_].append(y_); adjv[y_].append(x_)
    for rnd in range(30):
        todo = np.nonzero((lab == -1))[0]
        if not len(todo): break
        for v in todo:
            ls = [lab[u] for u in adjv[v] if lab[u] != -1 and (vnz[u] @ vnz[v]) > np.cos(np.radians(CREASE_DEG))]
            if ls: vals, cnts = np.unique(ls, return_counts=True); lab[v] = vals[cnts.argmax()]
    left = lab == -1
    if left.any():
        kk = cKDTree(Vu[~left]); _, j = kk.query(Vu[left], workers=-1); lab[left] = lab[~left][j]
    say("flood: %d vertices labelled from the seeds; %d seed-less areas closed off by barriers became faces of their own; barrier vertices given to a neighbour (%.0fs)" % (int(reach.sum()), nnew, time.time() - T0))
    seeded = sorted(set(int(x) for x in np.unique(lab[lab >= 0])))
    VO, TO, FO = R.tess_shape(body, 0.01, faces=seeded); FO = np.asarray(seeded)[FO]
    MDf = {f: K.MeshDist(VO, TO[FO == f], k=8) for f in seeded}
    a, b = Ev[:, 0], Ev[:, 1]
    tot_moved = 0; tot_checked = 0
    for it in range(40):
        bm = (lab[a] >= 0) & (lab[b] >= 0) & (lab[a] != lab[b])
        if not bm.any(): break
        vs = np.unique(np.concatenate([a[bm], b[bm]]))
        cand = {}
        for x, y in zip(a[bm], b[bm]):
            cand.setdefault(int(x), set()).update((int(lab[x]), int(lab[y]))); cand.setdefault(int(y), set()).update((int(lab[x]), int(lab[y])))
        best_d = {int(v): np.inf for v in vs}; best_f = {int(v): int(lab[v]) for v in vs}
        byf = {}
        for v, cs in cand.items():
            for f in cs: byf.setdefault(f, []).append(v)
        for f, vl in byf.items():
            d = MDf[f](Vu[vl])
            for v, dd in zip(vl, d):
                if dd < best_d[v] - 1e-6: best_d[v] = dd; best_f[v] = f
        moved = [v for v in vs if best_f[int(v)] != lab[v]]
        for v in moved: lab[v] = best_f[int(v)]
        tot_moved += len(moved); tot_checked += len(vs)
        if not moved: break
    say("border walk: %d round(s), %d vertex checks, %d moves - the borders between original-face labels now sit where the faces meet (%.0fs)" % (it + 1, tot_checked, tot_moved, time.time() - T0))
    vn = np.zeros_like(Vu)
    for k_ in range(3): np.add.at(vn, F[:, k_], Nr)
    vn /= np.maximum(np.linalg.norm(vn, axis=1), 1e-12)[:, None]
    for it2 in range(SMOOTH_IT):
        bm2 = lab[Ev[:, 0]] != lab[Ev[:, 1]]
        bv = np.unique(Ev[bm2].ravel()); bv = bv[~capv[bv]]
        nbs = kdv.query_ball_point(Vu[bv], SMOOTH_R, workers=-1)
        new = lab.copy(); ch = 0
        for v, nb in zip(bv, nbs):
            nb = np.asarray(nb); nb = nb[(vn[nb] @ vn[v]) > np.cos(np.radians(CREASE_DEG))]; nb = nb[~capv[nb]]
            if not len(nb): continue
            vals, cnts = np.unique(lab[nb], return_counts=True); mj = vals[cnts.argmax()]
            if mj != lab[v] and cnts.max() > 0.5 * len(nb): new[v] = mj; ch += 1
        lab = new
        say("border smoothing round %d: %d of %d border vertices relabelled" % (it2 + 1, ch, len(bv)))
        if not ch: break
    TL = lab[F]
    tl = np.where(TL[:, 0] == TL[:, 1], TL[:, 0], np.where(TL[:, 1] == TL[:, 2], TL[:, 1], np.where(TL[:, 0] == TL[:, 2], TL[:, 0], TL[:, 0])))
tl[tcap >= 0] = -100 - tcap[tcap >= 0]
Et = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); Es = np.sort(Et, 1); tri = np.tile(np.arange(len(F)), 3)
o = np.lexsort((Es[:, 1], Es[:, 0])); Es = Es[o]; tri = tri[o]; same = np.all(Es[1:] == Es[:-1], axis=1); ta = tri[:-1][same]; tb = tri[1:][same]
def comps(l):
    mm = l[ta] == l[tb]
    return connected_components(sp.coo_matrix((np.ones(int(mm.sum())), (ta[mm], tb[mm])), shape=(len(F), len(F))), directed=False)[1]
if FID is None:
    for it in range(15):
        c = comps(tl); ar = np.bincount(c, weights=At); small = np.nonzero(ar < A_NOISE)[0]
        if not len(small): break
        smk = np.isin(c, small); cr = c[ta] != c[tb]; best = {}
        for x, y in ((ta[cr], tb[cr]), (tb[cr], ta[cr])):
            mm = smk[x] & ~smk[y] & (tl[x] > -100) | (smk[x] & ~smk[y] & (tl[x] <= -1000))
            for cx, ly in zip(c[x[mm]], tl[y[mm]]):
                if ly <= -100 and ly > -1000: continue
                best.setdefault(cx, {}); best[cx][ly] = best[cx].get(ly, 0) + 1
        if not best: break
        for cx, d in best.items(): tl[c == cx] = max(d.items(), key=lambda kv: kv[1])[0]
    say("small pieces under %.1f mm2 joined their neighbour (%d rounds)" % (A_NOISE, it + 1))
# released
from collections import deque
def opening(tl):
    dih = (Nn[ta] * Nn[tb]).sum(1) >= np.cos(np.radians(CREASE_DEG))
    nbt = [[] for _ in range(len(F))]
    for x, y, ok in zip(ta, tb, dih):
        if ok: nbt[x].append(y); nbt[y].append(x)
    bd_ = tl[ta] != tl[tb]
    bmid = 0.5 * (Vu[Es[:-1][same][bd_][:, 0]] + Vu[Es[:-1][same][bd_][:, 1]])
    blab = np.stack([tl[ta[bd_]], tl[tb[bd_]]], 1)
    rel = np.zeros(len(F), bool)
    for l in np.unique(tl):
        if -1000 < l <= -100: continue
        tm = np.nonzero(tl == l)[0]
        mk = (blab[:, 0] == l) | (blab[:, 1] == l)
        if not mk.any(): continue
        d_, _ = cKDTree(bmid[mk]).query(Cn[tm], workers=-1)
        rel[tm[d_ < OPEN_MM]] = True
    new = tl.copy(); new[rel] = -9999
    q = deque(np.nonzero(~rel)[0].tolist())
    while q:
        t = q.popleft()
        for u in nbt[t]:
            if new[u] == -9999 and not (-1000 < new[t] <= -100): new[u] = new[t]; q.append(u)
    left = new == -9999; new[left] = tl[left]
    return new, int(rel.sum()), int((new != tl).sum())
if FID is None:
    tl, nrel, nchg = opening(tl)
    say("opening: %d border-band triangles released, %d of them went to another face (necks and slivers thinner than %.1f mm)" % (nrel, nchg, 2 * OPEN_MM))
if FID is None:
    for rnd in range(5):
        c = comps(tl); ar = np.bincount(c, weights=At); cr = c[ta] != c[tb]
        nbs = {}
        for x, y in zip(c[ta][cr], c[tb][cr]): nbs.setdefault(int(x), set()).add(int(y)); nbs.setdefault(int(y), set()).add(int(x))
        lab_of = {int(cc): int(tl[np.nonzero(c == cc)[0][0]]) for cc in np.unique(c)}
        merged = 0
        for cc, ns in nbs.items():
            if len(ns) == 1 and ar[cc] < ISLAND_MM2 and not (-1000 < lab_of[cc] <= -100):
                o_ = next(iter(ns))
                if -1000 < lab_of[o_] <= -100: continue
                tl[c == cc] = lab_of[o_]; merged += 1
        say("islands (one neighbour, under %.0f mm2) joined it: %d (round %d)" % (ISLAND_MM2, merged, rnd + 1))
        if not merged: break
def nloops(tset):
    T = F[tset]; E2 = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1)
    u_, c_ = np.unique(E2, axis=0, return_counts=True); bnd = u_[c_ == 1]
    if not len(bnd): return 0
    Gb = sp.coo_matrix((np.ones(len(bnd)), (bnd[:, 0], bnd[:, 1])), shape=(len(Vu), len(Vu)))
    return len(np.unique(connected_components(Gb, directed=False)[1][np.unique(bnd)]))
nxt = -20000
if FID is None:   # 31bc: NO HOLE CUT ON A B-REP SOURCE - a face pierced by a stem keeps its hole (the inner loop is a border like any other; skin-build
    for rnd in range(12):
        c = comps(tl); cut = 0
        for cc in np.unique(c[tl > -100]) if True else []:
            tm = np.nonzero(c == cc)[0]
            if tl[tm[0]] <= -100 and tl[tm[0]] > -1000: continue
            if nloops(tm) > 1:
                Pm = Cn[tm]; cen = Pm.mean(0); ww, vv = np.linalg.eigh(np.cov((Pm - cen).T)); side = (Pm - cen) @ vv[:, -1] > 0
                tl[tm[side]] = nxt; tl[tm[~side]] = nxt - 1; nxt -= 2; cut += 1
        for cc in np.unique(c[tl <= -1000]):
            tm = np.nonzero(c == cc)[0]
            if nloops(tm) > 1:
                Pm = Cn[tm]; cen = Pm.mean(0); ww, vv = np.linalg.eigh(np.cov((Pm - cen).T)); side = (Pm - cen) @ vv[:, -1] > 0
                tl[tm[side]] = nxt; tl[tm[~side]] = nxt - 1; nxt -= 2; cut += 1
        say("faces with a hole cut in two: %d (round %d)" % (cut, rnd + 1))
        if not cut: break
for rnd in range(3):
    c = comps(tl); nsplit = 0
    for cc in np.unique(c):
        tm = np.nonzero(c == cc)[0]
        if -1000 < tl[tm[0]] <= -100 or At[tm].sum() < 5.0: continue
        nm = (Nn[tm] * At[tm, None]).sum(0); st_ = np.linalg.norm(nm) / max(At[tm].sum(), 1e-12)
        if st_ >= WRAP_STRENGTH: continue
        nm /= max(np.linalg.norm(nm), 1e-12)
        a0 = Nn[tm][np.argmin(Nn[tm] @ nm)]; b0 = Nn[tm][np.argmax(Nn[tm] @ -a0)]
        cen = np.stack([a0, -a0])
        for _ in range(20):
            asg = (Nn[tm] @ cen.T).argmax(1)
            for j in range(2):
                mj = asg == j
                if mj.any(): v = (Nn[tm][mj] * At[tm][mj, None]).sum(0); cen[j] = v / max(np.linalg.norm(v), 1e-12)
        tl[tm[asg == 0]] = nxt; tl[tm[asg == 1]] = nxt - 1; nxt -= 2; nsplit += 1
    say("wrapping faces (normal strength under %.2f) split by their normals: %d (round %d)" % (WRAP_STRENGTH, nsplit, rnd + 1))
    if not nsplit: break
    for it3 in range(10):
        c = comps(tl); ar = np.bincount(c, weights=At); small = np.nonzero(ar < A_NOISE)[0]
        if not len(small): break
        smk = np.isin(c, small); cr = c[ta] != c[tb]; best = {}
        for x, y in ((ta[cr], tb[cr]), (tb[cr], ta[cr])):
            mm = smk[x] & ~smk[y]
            for cx, ly in zip(c[x[mm]], tl[y[mm]]):
                if -1000 < ly <= -100: continue
                best.setdefault(cx, {}); best[cx][ly] = best[cx].get(ly, 0) + 1
        if not best: break
        for cx, d in best.items(): tl[c == cx] = max(d.items(), key=lambda kv: kv[1])[0]
c = comps(tl); ids, inv = np.unique(c, return_inverse=True)
patches = []
for i, cc in enumerate(ids):
    tm = inv == i; l = int(tl[np.nonzero(tm)[0][0]])
    if -1000 < l <= -100: rec = {"patch": i, "kind": "cap", "wall": -100 - l, "src": "wall %d" % (-100 - l)}
    else:
        srcs = ("original face %d" % l) if l >= 0 else (("changed region R%d" % (-1000 - l)) if -20000 < l <= -1000 else ("an area the grid missed, closed by crisp edges" if l <= -30000 else "a half of a face cut for its hole"))
        rec = {"patch": i, "kind": "changed", "src": srcs}
        if l >= 0: rec["face_src"] = l
    rec.update({"label": l, "area_mm2": round(float(At[tm].sum()), 3), "tris": int(tm.sum())})
    nm = (Nn[tm] * At[tm, None]).sum(0); s_ = float(np.linalg.norm(nm)); nm /= max(s_, 1e-12)
    rec["spread_deg"] = round(float(np.degrees(np.arccos(np.clip((Nn[tm] @ nm).min(), -1, 1)))), 1); rec["normal_strength"] = round(s_ / max(At[tm].sum(), 1e-12), 3); rec["region"] = -1
    patches.append(rec)
nk = {k: sum(1 for p in patches if p["kind"] == k) for k in ("changed", "cap")}
nsrc_o = sum(1 for p in patches if "face_src" in p); nsrc_r = sum(1 for p in patches if p["src"].startswith("changed region"))
say("FINAL FACES: %d - %d from original faces with points, %d from changed regions, %d halves of holed faces, %d wall caps"
    % (len(patches), nsrc_o, nsrc_r, len(patches) - nsrc_o - nsrc_r - nk["cap"], nk["cap"]))
# recorded
# skin-mirror  skin-network  skin-build
# is its own mirror
MIRROR = os.environ.get("MIRROR", "").strip()
src_note = ("B-rep source: the original's faces by index (skin-source), faces with no point absorbed + caps" if FID is not None else "SP8 points (points1000.json) + changed regions + caps")
mirror_rec = None
iscap_t = np.array([patches[int(i)]["kind"] == "cap" for i in inv])
if MIRROR:
    try:
        MN, MC = K.mirror_plane(MIRROR)
    except ValueError as ex:
        K._fail("FAIL: %s" % ex)
    okw, whyw = K.window_symmetric(MN, MC)
    if not okw:
        K._fail("FAIL: MIRROR=%s - %s. A mirrored layout needs the whole symmetric edit in one edit region that is its own mirror: make the "
                "edit region symmetric (kit rebuild region), or --set MIRROR= (empty: the edit is not symmetric)" % (MIRROR, whyw))
    say("mirror: %s" % whyw)
    TWIN = {}
    if FID is not None:
        _fh = sorted(int(x) for x in np.unique(FID[FID >= 0]))
        _cent = {}; _area = {}
        for _f in _fh:
            try:
                _c = BF[_f].CenterOfMass; _cent[_f] = np.array([_c.x, _c.y, _c.z], float); _area[_f] = float(BF[_f].Area)
            except Exception:
                pass
        TWIN = K.face_twins(_cent, _area, MN, MC, tol_mm=float(os.environ.get("TWIN_MM", "0.5")), area_tol=float(os.environ.get("TWIN_AREA", "0.10")))
        newl, minfo = K.mirror_layout_faces(Cn, Nn, At, F, FID, inv.astype(np.int64), iscap_t, MN, MC, master=os.environ.get("MASTER", "auto").strip() or "auto",
                                            band=float(os.environ.get("BAND", "0.3")), twin_of=TWIN, vote_mm=float(os.environ.get("VOTE_MM", "2.0")), say=say)
    else:
        newl, minfo = K.mirror_layout(Cn, Nn, At, F, inv.astype(np.int64), iscap_t, MN, MC, master=os.environ.get("MASTER", "auto").strip() or "auto",
                                      band=float(os.environ.get("BAND", "0.3")), cross_min=float(os.environ.get("CROSS_MIN_MM2", "1.0")),
                                      a_noise=A_NOISE, frag=float(os.environ.get("FRAG_MM2", "5")), say=say)
    rec0 = {p["patch"]: p for p in patches}
    c2 = K.label_components(newl, ta, tb, len(F)); ids2, inv2 = np.unique(c2, return_inverse=True)
    newp = []
    for i in range(len(ids2)):
        tm = inv2 == i; l = int(newl[np.nonzero(tm)[0][0]])
        if l >= K.MIRROR_OFF:
            r0 = rec0[l - K.MIRROR_OFF]
            rec = {"patch": i, "kind": r0["kind"], "src": "mirror of " + r0["src"], "label": -(600000 + l - K.MIRROR_OFF), "mirror_of": l - K.MIRROR_OFF, "grp": l - K.MIRROR_OFF}
            if r0.get("face_src") is not None: rec["face_src_master"] = r0["face_src"]
        else:
            r0 = rec0[l]; rec = {k: v for k, v in r0.items() if k in ("kind", "src", "face_src", "label", "wall")}; rec["patch"] = i; rec["grp"] = l
        nm = (Nn[tm] * At[tm, None]).sum(0); s_ = float(np.linalg.norm(nm)); nm /= max(s_, 1e-12)
        rec.update({"area_mm2": round(float(At[tm].sum()), 3), "tris": int(tm.sum()), "spread_deg": round(float(np.degrees(np.arccos(np.clip((Nn[tm] @ nm).min(), -1, 1)))), 1),
                    "normal_strength": round(s_ / max(At[tm].sum(), 1e-12), 3), "region": -1})
        newp.append(rec)
    # mirror_of  skin-features
    # mirror_of
    _master_new = {r_["grp"]: r_["patch"] for r_ in newp if "mirror_of" not in r_ and r_.get("grp") is not None and r_.get("kind") != "cap"}
    for r_ in newp:
        if "mirror_of" in r_: r_["mirror_of"] = _master_new.get(r_.get("grp"), r_["mirror_of"])
    patches = newp; inv = inv2; ids = ids2
    tl = np.array([patches[int(i)]["label"] for i in inv])
    mirror_rec = dict(minfo, plane=MIRROR)
    if FID is not None:
        say("MIRRORED LAYOUT FACE BY FACE (31bf): master side %s kept (%d faces on +, %d on -); %d slave face(s) took their master twin's patch piece by piece; "
            "%d with no twin took WHOLE the master patch most of their mirror lands in (within VOTE_MM %.1f mm); %d absorbed by their slave neighbour; %d kept their own "
            "patch (nothing reached them); %d plane-centred face(s) mirrored half to half; %d stray piece(s) rejoined the neighbour they touch; %d face(s) span the plane, "
            "%d patch(es) are their own mirror. No twin: %s"
            % (minfo["master"], minfo["plus"], minfo["minus"], minfo["twins"], minfo["voted"], minfo["vote_mm"], minfo["absorbed"], len(minfo["own"]), minfo["halves"],
               minfo["detached"], len(minfo["cross"]), len(minfo["own_patches"]), minfo["no_twin"][:12]))
        _low = [v for v in minfo.get("votes", []) if v[3] < 0.8]
        if _low:
            say("   votes under 80 %%: " + "; ".join("face %d -> patch %d (%.0f %%, mirror %.2f mm, %s)" % (v[1], v[2], 100 * v[3], v[4], v[0]) for v in _low[:12]))
        if minfo.get("split"):
            say("   LABELS STILL IN TWO SLAVE PIECES after the mirror (a kit fault - say so in a NOTE): %s" % minfo["split"])
        src_note = "B-rep source: side %s kept, every slave face its master twin's patch, across %s" % (minfo["master"], MIRROR)
    else:
        say("MIRRORED LAYOUT: master side %s kept; %d slave triangles took the face at their mirror point (mirror distance p50 %.3f, p95 %.3f, max %.3f mm); "
            "%d face(s) span the plane, %d meet it only through a sliver (mirrored pairs); %d triangles had no like-facing master (filled from neighbours)"
            % (minfo["master"], minfo["slave_tris"], minfo["mirror_d_p50"], minfo["mirror_d_p95"], minfo["mirror_d_max"], len(minfo["cross"]), len(minfo["thin_pairs"]), minfo["no_like_facing"]))
        src_note = "SP8 points + caps, side %s kept and mirrored across %s" % (minfo["master"], MIRROR)
try:
    with open(os.path.join(SK, "MIRROR_DECISION.json"), "w", encoding="utf-8") as fh:
        json.dump({"plane": MIRROR, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "tag": K.TAG, "step": "skin-labels"}, fh)
except OSError:
    pass
# skin-network  skin-build  skin-rim
# skin-build
ORIG_FRAC = float(os.environ.get("ORIG_FRAC", "0.9")); ORIG_MIN = int(os.environ.get("ORIG_MIN", "3"))
_, pt_tri = cKDTree(Cn).query(pts, workers=-1); pt_patch = inv[pt_tri]
norig = K.orig_rung(patches, pt_patch, pf, ON, ORIG_FRAC, ORIG_MIN)
if FID is not None:
    for r_ in patches:
        if r_.get("kind") != "cap" and int(r_.get("label", -1)) >= 0 and r_.get("kind") != "orig":
            r_["kind"] = "orig"; r_["face"] = int(r_["label"]); r_["face_src"] = int(r_["label"]); norig += 1
    # FEATURES
    ABSORB_MM2 = float(os.environ.get("ABSORB_MM2", "2.0") or 2.0); ABSORB_FRAC = float(os.environ.get("ABSORB_FRAC", "0.05") or 0.05); nabs_ch = []; nabs_sp = 0
    for r_ in patches:
        if r_.get("kind") != "orig" or int(r_.get("label", -1)) < 0: continue
        tm_ = inv == int(r_["patch"]); ab_ = tm_ & (FID != int(r_["label"])) & (FID >= 0); a_ab = float(At[ab_].sum()); a_all = float(At[tm_].sum())
        if a_ab <= 0: continue
        r_["absorbed_mm2"] = round(a_ab, 2); r_["absorbed_faces"] = sorted(set(int(x) for x in FID[ab_]))
        if a_ab > ABSORB_MM2 and a_ab > ABSORB_FRAC * a_all:
            r_["kind"] = "changed"; r_.pop("face", None); r_["src"] = "original face %d + absorbed %s" % (int(r_["label"]), r_["absorbed_faces"][:6]); norig -= 1
            nabs_ch.append((int(r_["patch"]), int(r_["label"]), a_ab, a_all))
        else: nabs_sp += 1
    if nabs_ch or nabs_sp:
        say("FACE NAMING (31bl): %d kept face(s) absorbed more than a sliver of other original faces and are CHANGED, not orig - the ladder spans them (NURBS first)%s; %d kept their surface with only a speck absorbed (ABSORB_MM2 %g, ABSORB_FRAC %g)"
            % (len(nabs_ch), (": " + ", ".join("patch %d (original %d: %.1f of %.1f mm2 absorbed)" % t_ for t_ in nabs_ch[:8])) if nabs_ch else "", nabs_sp, ABSORB_MM2, ABSORB_FRAC))
    # FEATURES
    for r_ in patches:
        if r_.get("kind") != "cap" and r_.get("face_src") is None:
            tm_ = inv == int(r_["patch"]); fv_ = FID[tm_]; fv_ = fv_[fv_ >= 0]
            if len(fv_): r_["face_src"] = int(np.bincount(fv_).argmax())
if MIRROR:
    def _mirror_face(f, _cache={}):
        if f in _cache: return _cache[f]
        if FID is not None and TWIN:
            _cache[f] = TWIN.get(int(f)); return _cache[f]
        g0 = BF[f]; cg = g0.CenterOfMass; tgt = K.reflect(np.array([cg.x, cg.y, cg.z]), MN, MC); best = None
        for j, g in enumerate(BF):
            bb = g.BoundBox
            if not (bb.XMin - 1 <= tgt[0] <= bb.XMax + 1 and bb.YMin - 1 <= tgt[1] <= bb.YMax + 1 and bb.ZMin - 1 <= tgt[2] <= bb.ZMax + 1): continue
            c_ = g.CenterOfMass; dd = float(np.linalg.norm(np.array([c_.x, c_.y, c_.z]) - tgt))
            if dd < 0.5 and abs(g.Area - g0.Area) < 0.05 * g0.Area and (best is None or dd < best[0]): best = (dd, j)
        _cache[f] = best[1] if best else None; return _cache[f]
    msrc = {r["grp"]: r for r in patches if "mirror_of" not in r and r.get("kind") != "cap"}
    nfix = 0
    for r in patches:
        if "mirror_of" not in r or r["grp"] not in msrc: continue
        m_ = msrc[r["grp"]]
        if m_.get("face_src") is None: continue
        g = _mirror_face(int(m_["face_src"]))
        if g is None: continue
        r["face_src"] = g; nfix += 1
        if m_["kind"] == "orig": r["kind"] = "orig"; r["face"] = g
        elif r["kind"] == "orig": r["kind"] = "changed"; r.pop("face", None)
    say("twins given the mirror of their master's original face: %d" % nfix)
ndem = K.same_kind_groups(patches)
norig = sum(1 for r in patches if r["kind"] == "orig")
say("FACE LADDER rung 1: %d of %d skin faces lie on one original face and keep its surface (kind orig)%s; the rest go to the flat / fit rungs in skin-build"
    % (norig, sum(1 for r in patches if r["kind"] != "cap"), (" (%d demoted: a mirror twin not on an original surface)" % ndem) if ndem else ""))
np.savez_compressed(os.path.join(SK, "patches_labels.npz"), lab=tl, patch=inv, Nn=Nn)   # skin-rim
json.dump({"source": src_note, "mirror": mirror_rec, "orig_rung": {"ORIG_FRAC": ORIG_FRAC, "ORIG_MIN": ORIG_MIN, "orig": norig}, "patches": patches},
          open(os.path.join(SK, "patches_labels.json"), "w"), indent=1)
PAL = np.array([colorsys.hsv_to_rgb(hh, ss, vv) for hh, ss, vv in [(0.0, .75, .95), (0.08, .8, .95), (0.15, .8, .95), (0.3, .7, .85), (0.45, .75, .9), (0.55, .7, .95),
                 (0.65, .6, .95), (0.75, .6, .9), (0.85, .6, .95), (0.95, .4, .95), (0.12, .35, .75), (0.5, .35, .7)]])
adjp = {}
cr2 = inv[ta] != inv[tb]
for x, y in zip(inv[ta][cr2], inv[tb][cr2]): adjp.setdefault(int(x), set()).add(int(y)); adjp.setdefault(int(y), set()).add(int(x))
colr = {}
for i in sorted(range(len(ids)), key=lambda i: -len(adjp.get(i, ()))):
    used = set(colr.get(j) for j in adjp.get(i, ()))
    colr[i] = next(k for k in range(len(PAL)) if k not in used) if len(used) < len(PAL) else i % len(PAL)
pc = PAL[[colr[i] for i in range(len(ids))]]
for i, p in enumerate(patches):
    if p["kind"] == "cap": pc[i] = (0.35, 0.35, 0.40)
C = pc[inv]
bd = inv[ta] != inv[tb]; segs = Vu[Es[:-1][same][bd]]; segtri = np.stack([ta[bd], tb[bd]], 1)
for k, (nm_, d, fb, W, ttl) in enumerate(K.views()):
    path = os.path.join(OUT, "SP8_%02d_%s.png" % (k + 1, nm_)); foc = K.corners(fb); pad = 1.0
    gb = (fb[0] - 4, fb[1] + 4, fb[2] - 4, fb[3] + 4, fb[4] - 4, fb[5] + 4)
    mm = K._clip_mask(Vu, F, gb) if hasattr(K, "_clip_mask") else ((Cn[:, 0] >= gb[0]) & (Cn[:, 0] <= gb[1]) & (Cn[:, 1] >= gb[2]) & (Cn[:, 1] <= gb[3]) & (Cn[:, 2] >= gb[4]) & (Cn[:, 2] <= gb[5]))
    st = {}
    mmpx = R.render(path, [("v", Vu, F[mm], C[mm])], d, W=W, pad=pad, focus=foc, title=ttl, edges=False, stats=st)
    try: K.stamp_png(path, K.source_quality(Vu, F))
    except Exception: pass
    d3, r3, u3 = R.basis(d); x0 = (foc @ r3).min() - pad; y1 = (foc @ u3).max() + pad
    own = st["own"]; sub = np.nonzero(mm)[0]; Hh, Ww = own.shape
    im = Image.open(path).convert("RGB"); dr = ImageDraw.Draw(im)
    for (A_, B_), t1_, t2_ in zip(segs, segtri[:, 0], segtri[:, 1]):
        q = np.stack([(np.vstack([A_, B_]) @ r3 - x0) / mmpx, (y1 - np.vstack([A_, B_]) @ u3) / mmpx], 1)
        mx, my = int(q[:, 0].mean()), int(q[:, 1].mean())
        win = own[max(0, my - 2):min(Hh, my + 3), max(0, mx - 2):min(Ww, mx + 3)].ravel(); win = win[win >= 0]
        if not len(win) or not np.isin(sub[win], [t1_, t2_]).any(): continue
        dr.line([tuple(q[0]), tuple(q[1])], fill=(255, 255, 255), width=2)
    out = Image.new("RGB", (im.width, im.height + 148), (16, 16, 20)); od = ImageDraw.Draw(out)
    od.text((10, 8), "SP8  THE FINAL FACES DECIDED BY THE POINTS - %d faces - %s" % (len(patches), ttl), fill=(255, 235, 120), font=K.F22); out.paste(im, (0, 40))
    od.text((10, im.height + 48), "One colour per final face: each original face that got points, each changed region (the fix), the wall caps (grey, the exact faces). Faces that got", fill=(235, 235, 235), font=K.F16)
    od.text((10, im.height + 72), "no point are gone - their area went to their neighbours (blended away). White = the borders the camera sees, where each face's points overlap its neighbour's.", fill=(235, 235, 235), font=K.F16)
    for i_, t_ in enumerate(K.BORDER_NOTE): od.text((10, im.height + 96 + 24 * i_), t_, fill=K.BORDER_COL, font=K.F16)
    out.save(path)
say("pictures SP8_* written")
print("DONE", flush=True)

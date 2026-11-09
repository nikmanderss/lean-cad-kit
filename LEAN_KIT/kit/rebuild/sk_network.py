# kit rebuild  skin-network
import os, sys, json, time
if not globals().get("_SK_INNER"):      # 31br D3 (2026-10-29): a crash's TRACEBACK reaches the log
    import runpy as _rp3, traceback as _tb3
    try: _rp3.run_path(os.path.abspath(__file__), init_globals={"_SK_INNER": True}, run_name="__main__")
    except SystemExit: raise
    except BaseException:
        print("TRACEBACK (31br D3) - the crash's place:\n" + _tb3.format_exc(), flush=True); raise
    raise SystemExit(0)
import numpy as np
import Part, FreeCAD
from FreeCAD import Vector as V3
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sk_lib as K; RUN = K.RUN; K.need_window()
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter1d
JMERGE = float(os.environ.get("JMERGE", "0.5")); SMOOTH = float(os.environ.get("SMOOTH_MM", "0.8")); STEP = float(os.environ.get("STEP_MM", "0.5"))
SK = K.SK; OUT = K.OUT
NET_PICS = os.environ.get("NET_PICS", "1") == "1"   # kit rebuild
T0 = time.time()
def say(*a): print("%5.0fs " % (time.time() - T0), *a, flush=True)
Z = np.load(os.path.join(SK, "regions.npz")); Vu, F = Z["Vu"], Z["F"]
PZ = np.load(os.path.join(SK, "patches.npz")); pid = PZ["patch"]
PJ = json.load(open(os.path.join(SK, "patches.json")))["patches"]
kind = [p["kind"] for p in PJ]
body = Part.Shape(); body.importBrep(K.BODY); BF = body.Faces
walls = list(K.WALLS)   # REBUILD_region.json
E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); Es = np.sort(E, 1); tri = np.tile(np.arange(len(F)), 3)
o = np.lexsort((Es[:, 1], Es[:, 0])); Es = Es[o]; tri = tri[o]
same = np.all(Es[1:] == Es[:-1], axis=1)
ea = Es[:-1][same]; ta = tri[:-1][same]; tb = tri[1:][same]
bd = pid[ta] != pid[tb]
bE = ea[bd]; bP = np.sort(np.stack([pid[ta[bd]], pid[tb[bd]]], 1), 1)
vp = {}
for k in range(3):
    for v_, p_ in zip(F[:, k], pid): vp.setdefault(int(v_), set()).add(int(p_))
jv = np.array(sorted(v for v in np.unique(bE) if len(vp[int(v)]) >= 3))
say("border mesh edges %d between %d patch pairs; junction vertices %d" % (len(bE), len(np.unique(bP, axis=0)), len(jv)))
if len(jv):
    kdj = cKDTree(Vu[jv]); pairs = kdj.query_pairs(JMERGE)
    parent = list(range(len(jv)))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb
    roots = np.array([find(i) for i in range(len(jv))]); jr, jcl = np.unique(roots, return_inverse=True)
else: jcl = np.zeros(0, int); jr = []
vj = {int(v): int(c) for v, c in zip(jv, jcl)}
NJ = len(jr)
jpos = np.array([Vu[jv[jcl == c]].mean(0) for c in range(NJ)]) if NJ else np.zeros((0, 3))
jpat = [set().union(*[vp[int(v)] for v in jv[jcl == c]]) for c in range(NJ)]
say("junctions after merging those within %.2f mm: %d" % (JMERGE, NJ))
def surf_proj(fi):
    S = BF[fi].Surface
    def pr(x):
        u, v = S.parameter(V3(*x)); q = S.value(u, v); return np.array([q.x, q.y, q.z])
    return pr
def plane_proj(w):
    n, c = walls[w]
    return lambda x: x - (x @ n - c) * n
PROJ = {}
for i, p in enumerate(PJ):
    if p["kind"] == "orig": PROJ[i] = surf_proj(p["face"])
    elif p["kind"] == "cap": PROJ[i] = plane_proj(p["wall"])
JMOVE_MAX = float(os.environ.get("JMOVE_MAX", "0.5"))
def alt_project(x, pats, it=40):
    prs = [PROJ[p] for p in pats if p in PROJ]
    if not prs: return x, 0.0
    for _ in range(it):
        x0 = x.copy()
        for pr in prs: x = pr(x)
        if np.linalg.norm(x - x0) < 1e-7: break
    res = max(np.linalg.norm(pr(x) - x) for pr in prs)
    return x, float(res)
jres = []; jfar = []
for c in range(NJ):
    x0_ = jpos[c].copy(); x, r = alt_project(x0_.copy(), sorted(jpat[c])); mv_ = float(np.linalg.norm(x - x0_))
    if mv_ > JMOVE_MAX:
        jfar.append((c, mv_, sorted(jpat[c]))); jres.append(mv_); continue
    jpos[c] = x; jres.append(r)
jres = np.array(jres)
say("junctions placed: residual p50 %.2e max %.2e mm (distance to the surfaces / planes each must lie on)" % (np.median(jres) if len(jres) else 0, jres.max() if len(jres) else 0))
for c, mv_, pats_ in jfar:
    say("   junction %d (faces %s) NOT projected: the original surface of face(s) %s is %.2f mm from the mesh point there (over JMOVE_MAX %g) - the junction stays on the source mesh; that face does not reach it on its own surface (an absorbed face? decide its points, or let the face leave its surface)"
        % (c, pats_, [p_ for p_ in pats_ if PJ[p_]["kind"] == "orig"], mv_, JMOVE_MAX))
from collections import defaultdict
pairmap = defaultdict(list)
for (a, b), (p, q) in zip(bE, bP): pairmap[(int(p), int(q))].append((int(a), int(b)))
chains = []
for (p, q), edges in pairmap.items():
    adj = defaultdict(list)
    for a, b in edges: adj[a].append(b); adj[b].append(a)
    used = set()
    def walk(start, nxt):
        path = [start, nxt]; used.add(frozenset((start, nxt))); cur = nxt
        while cur not in vj and len(adj[cur]) == 2:
            n2 = [x for x in adj[cur] if frozenset((cur, x)) not in used]
            if not n2: break
            used.add(frozenset((cur, n2[0]))); path.append(n2[0]); cur = n2[0]
            if cur == start: break
        return path
    starts = [v for v in adj if v in vj or len(adj[v]) != 2]
    for s_ in starts:
        for n_ in adj[s_]:
            if frozenset((s_, n_)) in used: continue
            chains.append(((p, q), walk(s_, n_)))
    for a, b in edges:
        if frozenset((a, b)) in used: continue
        chains.append(((p, q), walk(a, b)))
say("chains: %d" % len(chains))
def jof(v): return vj.get(v, None)
def ctype(p, q):
    k = sorted([kind[p], kind[q]]); return "%s|%s" % (k[0].upper(), k[1].upper())
keep = []
for (pq, path) in chains:
    P = Vu[path]; L = float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum())
    ja, jb = jof(path[0]), jof(path[-1])
    closed = path[0] == path[-1] and ja is None
    if ja is not None and ja == jb and L < 2 * JMERGE + 0.5 and not closed: continue
    keep.append((pq, path, L, ja, jb, closed))
say("chains kept %d (dropped %d tiny ones inside one junction)" % (len(keep), len(chains) - len(keep)))
shared_cache = {}
def shared_edges(fa, fb):
    key = (min(fa, fb), max(fa, fb))
    if key not in shared_cache:
        shared_cache[key] = [e for e in BF[fa].Edges if any(e.isSame(g) for g in BF[fb].Edges)]
    return shared_cache[key]
edges_out = []; recs = []; nfail = 0
for ci, (pq, path, L, ja, jb, closed) in enumerate(keep):
    p, q = pq; ty = ctype(p, q)
    P = Vu[path].astype(float)
    if closed:
        Q = P[:-1]
        if len(Q) > 6: Q = np.stack([gaussian_filter1d(Q[:, k], max(1.0, SMOOTH / max(L / len(Q), 1e-3)), mode="wrap") for k in range(3)], 1)
    else:
        sig = max(1.0, SMOOTH / max(L / max(len(P) - 1, 1), 1e-3))
        Q = np.stack([gaussian_filter1d(P[:, k], sig, mode="nearest") for k in range(3)], 1) if len(P) > 4 else P.copy()
        if ja is not None: Q[0] = jpos[ja]
        if jb is not None: Q[-1] = jpos[jb]
    QQ = np.vstack([Q, Q[:1]]) if closed else Q
    Lc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(QQ, axis=0), axis=1))])
    n = max(3 if not closed else 6, int(Lc[-1] / STEP) + 1)
    ss = np.linspace(0, Lc[-1], n, endpoint=not closed)
    S = np.stack([np.interp(ss, Lc, QQ[:, k]) for k in range(3)], 1)
    cons = [x for x in (p, q) if x in PROJ]
    via = "smoothed"
    # does not reach
    far_faces = []
    if cons:
        Praw_ = K.polyline_samples(P, STEP); Praw_ = Praw_[1:-1] if len(Praw_) > 2 else Praw_
        for x_ in list(cons):
            try: d_x = float(np.median([np.linalg.norm(PROJ[x_](pt_) - pt_) for pt_ in Praw_[:: max(1, len(Praw_) // 24)]]))
            except Exception: d_x = 9e9
            if d_x > JMOVE_MAX: far_faces.append((int(x_), round(d_x, 3))); cons.remove(x_)
    if ty == "ORIG|ORIG":
        se = shared_edges(PJ[p]["face"], PJ[q]["face"])
        if se:
            d0 = min(e.distToShape(Part.Vertex(V3(*S[len(S) // 2])))[0] for e in se)
            d_med = float(np.median([min(e.distToShape(Part.Vertex(V3(*S[i_])))[0] for e in se) for i_ in range(0, len(S), max(1, len(S) // 12))])) if d0 < 0.4 else 9e9
            if d0 < 0.4 and d_med > JMOVE_MAX:
                via = "smoothed"; far_faces.append(("shared edge", round(d_med, 3)))
            if d0 < 0.4 and d_med <= JMOVE_MAX:
                via = "original edge"; far_ = 0
                for i in range(len(S)):
                    best = min(((e.distToShape(Part.Vertex(V3(*S[i])))[0], e) for e in se), key=lambda t: t[0])
                    # does not reach
                    if best[0] > JMOVE_MAX: far_ += 1; continue
                    pt = best[1].distToShape(Part.Vertex(V3(*S[i])))[1][0][0]; S[i] = (pt.x, pt.y, pt.z)
                if far_: via += " (%d of %d points NOT moved onto it: the shared edge is over JMOVE_MAX %g mm away there - the mesh border stands)" % (far_, len(S), JMOVE_MAX)
        if via == "smoothed" and len(cons) in (1, 2):
            via = "surface intersection" if len(cons) == 2 else "on the original surface of face %d only" % cons[0]
            far_ = 0
            for i in range(len(S)):
                x_ = alt_project(S[i], cons)[0]
                if np.linalg.norm(x_ - S[i]) > JMOVE_MAX: far_ += 1
                else: S[i] = x_
            if far_: via += " (%d of %d points NOT projected: the surface is over JMOVE_MAX %g mm away there)" % (far_, len(S), JMOVE_MAX)
        elif via == "smoothed":
            via = "mesh border (neither original surface reaches it)"
    elif cons:
        via = {"CAP|ORIG": "section", "CAP|CAP": "box edge", "CHANGED|ORIG": "on the original surface", "CAP|CHANGED": "on the wall plane"}.get(ty, "projected")
        far_ = 0
        for i in range(len(S)):
            x_ = alt_project(S[i], cons)[0]
            if np.linalg.norm(x_ - S[i]) > JMOVE_MAX: far_ += 1          # does not reach
            else: S[i] = x_
        if far_: via += " (%d of %d points NOT projected: the surface is over JMOVE_MAX %g mm away there)" % (far_, len(S), JMOVE_MAX)
    if far_faces:
        _fx = [(f_, d_) for f_, d_ in far_faces if f_ != "shared edge"]; _se = [d_ for f_, d_ in far_faces if f_ == "shared edge"]
        if _fx: via += " - original face(s) %s do NOT reach this border (%s mm from it, over JMOVE_MAX %g): their surface is not projected onto - an absorbed face? keep it by a point, or let the face leave its surface" % ([f_ for f_, _d in _fx], "/".join("%.2f" % _d for _f, _d in _fx), JMOVE_MAX)
        if _se: via += " - the faces' shared original edge lies %.2f mm from this border (over JMOVE_MAX %g): the border is not on it and was not dragged to it" % (_se[0], JMOVE_MAX)
    if not closed:
        if ja is not None: S[0] = jpos[ja]
        if jb is not None: S[-1] = jpos[jb]
    kp = [0]
    for i in range(1, len(S)):
        if np.linalg.norm(S[i] - S[kp[-1]]) > 1e-4: kp.append(i)
    S = S[kp]
    try:
        c = Part.BSplineCurve()
        if closed: c.interpolate([V3(*x) for x in S], PeriodicFlag=True)
        else:
            if len(S) == 2: c = Part.LineSegment(V3(*S[0]), V3(*S[1])).toBSpline()
            else: c.interpolate([V3(*x) for x in S])
        e = c.toShape()
    except Exception as ex:
        nfail += 1; recs.append({"chain": ci, "pair": [p, q], "type": ty, "ok": False, "err": str(ex)[:80]}); continue
    res = 0.0; mdev = 0.0; _kdP = cKDTree(K.polyline_samples(P, 0.1))
    for k in range(11):
        x = e.valueAt(e.FirstParameter + (e.LastParameter - e.FirstParameter) * k / 10); x = np.array([x.x, x.y, x.z])
        for pp in cons: res = max(res, float(np.linalg.norm(PROJ[pp](x) - x)))
        mdev = max(mdev, float(_kdP.query(x)[0]))
    edges_out.append(e)
    recs.append({"chain": ci, "edge": len(edges_out) - 1, "pair": [p, q], "type": ty, "via": via, "ok": True, "junctions": [ja, jb], "closed": closed,
                 "length": round(e.Length, 3), "points": len(S), "residual": round(res, 5), "mesh_dev": round(mdev, 4), "far_faces": [f_ for f_, _d in far_faces if f_ != "shared edge"], "shared_edge_off": ([d_ for f_, d_ in far_faces if f_ == "shared edge"] or [None])[0]})
types = defaultdict(int)
for r in recs:
    if r.get("ok"): types[r["type"]] += 1
say("edges built %d (%s); failed %d" % (len(edges_out), ", ".join("%s %d" % kv for kv in sorted(types.items())), nfail))
rr = np.array([r["residual"] for r in recs if r.get("ok")])
say("edge residual against its surfaces/planes: p50 %.4f p95 %.4f max %.4f mm" % (np.median(rr), np.percentile(rr, 95), rr.max()))
for r in sorted([r for r in recs if r.get("ok")], key=lambda r: -r["residual"])[:8]:
    say("   worst: chain %d %s via %s, %.2f mm long, residual %.4f, off its own mesh border by %.3f mm" % (r["chain"], r["type"], r["via"], r["length"], r["residual"], r.get("mesh_dev", 0.0)))
_md_ = sorted([r for r in recs if r.get("ok")], key=lambda r: -r.get("mesh_dev", 0.0))[:3]
if _md_ and _md_[0].get("mesh_dev", 0.0) > JMOVE_MAX: say("   OFF THE MESH: chain(s) %s run %s mm from the border they stand for (over JMOVE_MAX %g) - look at them in the WIRE frames" % ([r["chain"] for r in _md_ if r.get("mesh_dev", 0.0) > JMOVE_MAX], "/".join("%.2f" % r.get("mesh_dev", 0.0) for r in _md_ if r.get("mesh_dev", 0.0) > JMOVE_MAX), JMOVE_MAX))
_ff_ = [r for r in recs if r.get("ok") and (r.get("far_faces") or r.get("shared_edge_off"))]
if _ff_: say("   SURFACES THAT DO NOT REACH THEIR BORDER (31bo): %d chain(s) - %s" % (len(_ff_), ", ".join("chain %d: %s" % (r["chain"], ("face(s) %s" % r["far_faces"]) if r.get("far_faces") else "the shared original edge %.2f mm off" % r["shared_edge_off"]) for r in _ff_[:10])))
from collections import Counter
deg = Counter()
for r in recs:
    if r.get("ok") and not r["closed"]:
        for j in r["junctions"]:
            if j is not None: deg[j] += 1
bad_j = [j for j in range(NJ) if deg[j] < 3]
say("junctions with fewer than 3 edges: %d of %d (a junction must have >= 3)" % (len(bad_j), NJ))
Part.makeCompound(edges_out).exportBrep(os.path.join(SK, "network.brep"))
json.dump({"JMERGE": JMERGE, "junctions": [{"pos": [round(float(v), 5) for v in jpos[c]], "patches": sorted(int(x) for x in jpat[c]), "residual": float(jres[c])} for c in range(NJ)],
           "chains": recs}, open(os.path.join(SK, "network.json"), "w"), indent=0)
COLT = {"ORIG|ORIG": (60, 230, 255), "CAP|ORIG": (150, 150, 160), "CAP|CAP": (150, 150, 160), "CHANGED|ORIG": (255, 220, 40), "CHANGED|CHANGED": (255, 80, 200), "CAP|CHANGED": (255, 120, 40)}
polys = [(np.array([[x.x, x.y, x.z] for x in e.discretize(Number=max(2, int(e.Length / 0.05)))]), COLT.get(r["type"], (255, 255, 255)))
         for e, r in zip(edges_out, [r for r in recs if r.get("ok")])]
C = np.tile(np.array(K.VOX), (len(F), 1))
def draw(dr, proj):
    for P_, col in polys: dr.line(proj(P_), fill=col, width=2)
    for c in range(NJ):
        x, y = proj(jpos[c][None, :])[0]; dr.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 60, 40))
leg = [((60, 230, 255), "orig|orig (on the original edge / both surfaces)"), ((255, 220, 40), "orig|changed (on the original surface)"),
       ((255, 80, 200), "changed|changed"), ((150, 150, 160), "at an edit region wall"), ((255, 60, 40), "junction")]
NKEY = K.pic_key(os.path.join(SK, "network.brep"), os.path.join(SK, "regions.npz"), pics=K.PICS); K.clear_frames("SP4_", NKEY)
for i, (nm, dv, fb, W, ttl) in enumerate(K.views() if NET_PICS else []):
    K.view(R, os.path.join(OUT, "SP4_%02d_network_%s.png" % (i + 1, nm)), Vu, F, dv, fb, W, ttl,
           "SP4.%02d  THE EDGE NETWORK OF THE REMADE SKIN - %d edges, %d junctions - %s" % (i + 1, len(edges_out), NJ, ttl),
           ["Every border between two faces of the remade skin as ONE edge, built once and shared by both faces: cyan where two original surfaces meet (on",
            "their original edge or their intersection), yellow where a changed face meets an original surface (the edge lies on the original surface), magenta",
            "between changed faces, grey at the edit region walls. Red dots = junctions, each placed on every surface and plane that meets there."],
           draw=draw, C=C, legend=leg, key=NKEY)
say(K.pic_report("SP4_*") if NET_PICS else "pictures SP4_*: none this run (NET_PICS=0 - the wires' pictures are the set to open)")
print("DONE", flush=True)

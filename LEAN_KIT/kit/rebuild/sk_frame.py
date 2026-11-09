# kit rebuild  skin-frame
# PRIOR ART
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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sk_lib as K; RUN = K.RUN; SK = K.SK; K.need_window()
T0 = time.time()
def say(*a): print("%5.0fs " % (time.time() - T0), *a, flush=True)
def P3(v): return np.array([v.X, v.Y, v.Z]) if hasattr(v, "X") else np.array([v.x, v.y, v.z])
wc = Part.Shape(); wc.importBrep(os.path.join(RUN, "wall_caps.brep")); BFc = wc.Faces
FO = json.load(open(os.path.join(SK, "frame_owner.json"))); remap = {int(k): v for k, v in FO["remap"].items()}
cap_new = {int(c): int(b) for c, b in FO["cap_map_new"].items()}
PJ = json.load(open(os.path.join(SK, "patches.json")))["patches"]
assert all(PJ[c]["kind"] == "cap" for c in cap_new), "patches.json is not the SP12 layout frame_owner.json was written for"
BV = []; bkey = {}
VERT_TOL = float(os.environ.get("VERT_TOL", "1e-3"))
def vid(p):
    p = np.asarray(p, float)
    if len(BV):
        d = np.linalg.norm(np.asarray(BV, float) - p[None, :], axis=1); i = int(d.argmin())
        if d[i] <= VERT_TOL: return i
    BV.append(p); return len(BV) - 1
Bedges = [[(vid(P3(e.Vertexes[0])), vid(P3(e.Vertexes[-1]))) for e in f.Edges] for f in BFc]; BV = np.array(BV)
own = {}
for k, r in FO["owners"].items():
    b, i = [int(x) for x in k.split("_")]
    own[(b, i)] = None if r["kind"] == "capcap" else int(remap[int(r["patch_final"])])
stretch = {}
for (b, i), q in sorted(own.items()):
    if q is not None: stretch.setdefault(q, []).append([b, i])
skinset = {}
for b in range(len(BFc)):
    for i, (va, vb) in enumerate(Bedges[b]):
        for v in (va, vb):
            skinset.setdefault(v, set())
            if own[(b, i)] is not None: skinset[v].add(own[(b, i)])
fv = {v: s for v, s in skinset.items() if len(s) >= 2}
say("frame: %d body cap faces, %d edges (%d box corners), %d vertices; %d frame vertices where the skin face changes; skin faces on the walls %d"
    % (len(BFc), len(own), sum(1 for q in own.values() if q is None), len(BV), len(fv), len(stretch)))
NJ = json.load(open(os.path.join(SK, "network.json"))); J = NJ["junctions"]
net = Part.Shape(); net.importBrep(os.path.join(SK, "network.brep")); NE = net.Edges
CH = [c for c in NJ["chains"] if c.get("ok")]; assert len(CH) == len(NE)
JP = np.array([j["pos"] for j in J], float)
capset = set(cap_new)
jch = {}
for k, c in enumerate(CH):
    if not (set(c["pair"]) & capset):
        for x in c["junctions"]:
            if x is not None: jch.setdefault(x, []).append(k)
jv = {}; JN = JP.copy(); bad = []
for j in range(len(J)):
    ps = set(J[j]["patches"])
    if not (ps & capset) or j not in jch: continue
    S_ = ps - capset
    cand = [v for v, s in fv.items() if s == S_] or [v for v, s in fv.items() if S_ <= s] or [v for v, s in fv.items() if s <= S_]
    if not cand: bad.append(j); say("   JUNCTION %d (skin faces %s, caps %s): NO frame vertex has these skin faces" % (j, sorted(S_), sorted(ps & capset))); continue
    v = min(cand, key=lambda v: np.linalg.norm(BV[v] - JP[j])); jv[j] = v; JN[j] = BV[v]
mv = sorted(((float(np.linalg.norm(JN[j] - JP[j])), j) for j in jv), reverse=True)
say("wall junctions with a chain between skin faces: %d placed on frame vertices (moved p50 %.3f, max %.3f mm; over 0.05: %s); unplaced %d"
    % (len(jv), np.median([m for m, _ in mv]) if mv else 0, mv[0][0] if mv else 0, ", ".join("J%d %.3f" % (j, m) for m, j in mv if m > 0.05), len(bad)))
taken = {}
for j, v in jv.items(): taken.setdefault(v, []).append(j)
for v, js in taken.items():
    if len(js) > 1: say("   frame vertex %d takes junctions %s" % (v, js))
for v, s in fv.items():
    if v not in taken: say("   frame vertex %d (skin faces %s) at %s has no network junction - no chain between them ends on the wall there" % (v, sorted(s), np.round(BV[v], 2).tolist()))
def samples(e, n=None, step=0.2):
    n = n or max(3, int(e.Length / step) + 1); return np.array([[q.x, q.y, q.z] for q in e.discretize(Number=n)])
rec = []; edges_out = []
for k, c in enumerate(CH):
    p, q = [int(x) for x in c["pair"]]; ja, jb = c["junctions"]
    if p in capset or q in capset:
        rec.append({"chain": k, "kind": "wall_dropped", "pair": [p, q]}); edges_out.append(NE[k]); continue
    moved = [x for x in (ja, jb) if x is not None and x in jv and np.linalg.norm(JN[x] - JP[x]) > 1e-9]
    if not moved:
        rec.append({"chain": k, "kind": "net", "pair": [p, q]}); edges_out.append(NE[k]); continue
    S = samples(NE[k]); s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(S, axis=0), axis=1))]); L = s[-1]
    for jj, sd, end in ((ja, s, 0), (jb, L - s, -1)):
        if jj is None or jj not in jv: continue
        dv = JN[jj] - S[end]; Lb = min(0.9 * L, max(2.0, 4 * np.linalg.norm(dv)))
        w = np.where(sd < Lb, 0.5 * (1 + np.cos(np.pi * sd / Lb)), 0.0); S = S + w[:, None] * dv[None, :]
    if ja in jv: S[0] = JN[ja]
    if jb in jv: S[-1] = JN[jb]
    keep = [0]
    for i in range(1, len(S) - 1):
        if np.linalg.norm(S[i] - S[keep[-1]]) > 0.05: keep.append(i)
    if np.linalg.norm(S[-1] - S[keep[-1]]) < 0.05 and len(keep) > 1: keep[-1] = len(S) - 1
    else: keep.append(len(S) - 1)
    S = S[keep]
    if len(S) == 2: cv = Part.LineSegment(V3(*S[0]), V3(*S[1])).toBSpline()
    else: cv = Part.BSplineCurve(); cv.interpolate([V3(*x) for x in S])
    edges_out.append(cv.toShape())
    rec.append({"chain": k, "kind": "reended", "pair": [p, q], "shift": [round(float(np.linalg.norm(JN[x] - JP[x])), 4) if x in jv else 0.0 for x in (ja, jb)]})
    if max(rec[-1]["shift"]) > 0.05: say("   chain %d (faces %d/%d, %.2f mm) re-ended: ends moved %s mm" % (k, p, q, L, rec[-1]["shift"]))
Part.makeCompound(edges_out).exportBrep(os.path.join(SK, "network_frame.brep"))
def key(x): return tuple(np.round(np.asarray(x, float), 4))
ends = {}
for k, c in enumerate(CH):
    if rec[k]["kind"] == "wall_dropped": continue
    e = edges_out[k]
    if c["closed"]: continue
    for p in c["pair"]:
        for x in (P3(e.Vertexes[0]), P3(e.Vertexes[-1])): ends.setdefault(int(p), []).append(key(x))
for q, lst in stretch.items():
    for b, i in lst:
        va, vb = Bedges[b][i]
        if va == vb: continue
        ends.setdefault(q, []).extend([key(BV[va]), key(BV[vb])])
openp = []
for q, lst in sorted(ends.items()):
    cnt = {}
    for x in lst: cnt[x] = cnt.get(x, 0) + 1
    odd = [x for x, n in cnt.items() if n % 2]
    if odd:
        openp.append(q)
        say("   FACE %d: boundary does not close - %d loose end(s) at %s; its frame vertices without a junction: %s"
            % (q, len(odd), [list(x) for x in odd[:4]], [v for v, s_ in fv.items() if q in s_ and v not in taken]))
say("FRAME v2: %d skin faces with wall stretches; wall junctions placed %d, unplaced %d; chains %s; faces whose boundary does not close: %d %s"
    % (len(stretch), len(jv), len(bad), {kk: sum(1 for r in rec if r["kind"] == kk) for kk in ("net", "reended", "wall_dropped")}, len(openp), openp))
json.dump({"cap_body": {str(c): b for c, b in cap_new.items()}, "stretch": {str(q): v for q, v in stretch.items()}, "chains": rec,
           "junction_vertex": {str(j): int(v) for j, v in jv.items()}, "unplaced": bad, "open_faces": openp}, open(os.path.join(SK, "frame.json"), "w"), indent=0)
print("DONE", flush=True)

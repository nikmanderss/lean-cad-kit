# kit rebuild  skin-build
# PRIOR ART
# boundary edges  boundary edges
import os, sys, json, time, re
if not globals().get("_SK_INNER"):      # 31br D3 (2026-10-29): a crash's TRACEBACK reaches the log
    import runpy as _rp3, traceback as _tb3
    try: _rp3.run_path(os.path.abspath(__file__), init_globals={"_SK_INNER": True}, run_name="__main__")
    except SystemExit: raise
    except BaseException:
        print("TRACEBACK (31br D3) - the crash's place:\n" + _tb3.format_exc(), flush=True); raise
    raise SystemExit(0)
import numpy as np
import Part, FreeCAD
from FreeCAD import Vector as V3, Base
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sk_lib as K; RUN = K.RUN; K.need_window()
from _busy import busy
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree
KEEP_NET = os.environ.get("KEEP_NET", "0") == "1"; EDGE_FIX = os.environ.get("EDGE_FIX", "0") == "1"; RINGS = int(os.environ.get("RINGS", "5")); CTRL_MM = float(os.environ.get("CTRL_MM", "1.2")); W_EDGE = float(os.environ.get("W_EDGE", "30")); LAM = float(os.environ.get("LAM", "0.02")); NEAR_MM = float(os.environ.get("NEAR_MM", "0.6"))
# skin-labels  recorded
MIRROR_S = (os.environ.get("MIRROR") if os.environ.get("MIRROR") is not None else (K.mirror_decision() or "")).strip()
try:
    MP = K.mirror_plane(MIRROR_S)
except ValueError as _ex:
    K._fail("FAIL: %s" % _ex)
SYMFIT = os.environ.get("SYMFIT", "1") == "1"
TWIN_MIRROR = os.environ.get("TWIN_MIRROR", "1") == "1"
TWIN_CEN_MM = float(os.environ.get("TWIN_CEN_MM", "2.0") or 2.0)
TWIN_RIM_PLUS = float(os.environ.get("TWIN_RIM_PLUS", "0.05") or 0.05)
SHOW_NUMBERS = os.environ.get("SHOW_NUMBERS", "0") == "1"
FRAME_TOL = float(os.environ.get("FRAME_TOL", "0.02"))
FIT = (os.environ.get("FIT", "span") or "span").strip().lower()
CORNER_DEG = float(os.environ.get("CORNER_DEG", "50")); SPAN_STEP = float(os.environ.get("SPAN_STEP", "1.0"))
HOLES = os.environ.get("HOLES", "1") == "1"
NURBS_SKIP = set(int(x) for x in os.environ.get("NURBS_SKIP", "").replace(",", " ").split() if x.strip().lstrip("-").isdigit())
def _nurbs_args(pi):
    """the NURBS rung's arguments for layout face pi: off when the face is in NURBS_SKIP; a face that owns a body (wall) edge must hold its rim
    within NURBS_WALL_RIM (the agent's sn3 / sn5: wall-edge faces drifted and broke the frame check), any other within NURBS_RIM"""
    if pi in NURBS_SKIP: return {"nurbs": False}
    try: owns_wall = any(int(q_) == int(pi) for (q_, _b, _i) in BODY_E.values())
    except Exception: owns_wall = False
    return {"nurbs": None, "rim_tol": (SP.NURBS_WALL_RIM if owns_wall else None), "trade_rim": (SP.wall_trade_rim() if owns_wall else None)}      # NURBS_RIM
import sk_span as SP
import sk_vertex as VX
SK = K.SK; OUT = K.OUT
T0 = time.time()
for _stale in ("free_c.brep", "piece_skin.brep", "shell_c.brep", "solid_c.json", "piece_faces.json"):
    try: os.remove(os.path.join(K.SK, _stale))
    except OSError: pass
import re as _re
for _f in os.listdir(K.SK):
    if _re.match(r"^piece_\d+_[A-Z]\.brep$", _f) or _re.match(r"^fillet_\d+_(strip|crease|surf)\.brep$", _f):
        try: os.remove(os.path.join(K.SK, _f))
        except OSError: pass
def say(*a): print("%5.0fs " % (time.time() - T0), *a, flush=True)
Z = np.load(os.path.join(SK, "regions.npz")); Vu, F = Z["Vu"], Z["F"]
FID = np.asarray(Z["fid"]).astype(int) if "fid" in Z.files else None
pid = np.load(os.path.join(SK, "patches.npz"))["patch"]
PJ = json.load(open(os.path.join(SK, "patches.json")))["patches"]
NJ = json.load(open(os.path.join(SK, "network.json")))
net = Part.Shape(); net.importBrep(os.path.join(SK, "network.brep")); NE = net.Edges
CH = [c for c in NJ["chains"] if c.get("ok")]; assert len(CH) == len(NE)
JP = np.array([j["pos"] for j in NJ["junctions"]], float)
FRAME = os.environ.get("FRAME", "1") == "1"
if FRAME:
    FR = json.load(open(os.path.join(SK, "frame.json")))
    nf_ = Part.Shape(); nf_.importBrep(os.path.join(SK, "network_frame.brep")); NE = nf_.Edges; assert len(NE) == len(CH)
    wcs_ = Part.Shape(); wcs_.importBrep(os.path.join(RUN, "wall_caps.brep")); BFc = wcs_.Faces
    CAPB = {int(c): int(b) for c, b in FR["cap_body"].items()}
    dropped_ = {r["chain"] for r in FR["chains"] if r["kind"] == "wall_dropped"}
    ALL_E = [None if k in dropped_ else NE[k] for k in range(len(NE))]
    BODY_E = {}
    for q_, lst_ in FR["stretch"].items():
        for b_, i_ in lst_: BODY_E[len(ALL_E)] = (int(q_), int(b_), int(i_)); ALL_E.append(BFc[b_].Edges[i_])
    if FR.get("open_faces"): K._fail("FAIL: FRAME: frame.json lists faces whose boundary does not close: %s" % FR["open_faces"])
else: ALL_E = list(NE)
body = Part.Shape(); body.importBrep(K.BODY); BF = body.Faces
walls = list(K.WALLS)   # REBUILD_region.json
# THE PIECE RULE
A6_WALL_MM = 1.5; A6_TOUCH_MM = 0.15; A6_SAID = {}
def _a6_dir(v):
    v = np.asarray(v, float); L = float(np.linalg.norm(v))
    if L < 1e-12: return "undetermined"
    v = v / L; i = int(np.argmax(np.abs(v))); return "%s%s [%.2f %.2f %.2f]" % ("+" if v[i] > 0 else "-", "xyz"[i], v[0], v[1], v[2])
def _a6_wall_name(w):
    return ("%s %.2f" % ("xxyyzz"[w], K.WIN[w])) if w < 6 else "cut plane %d" % (w - 6)
def _a6_say(pi):
    """31bu A6: after a SPAN FAILED line - the facing at every wall stretch face pi owns, read from the triangles of this face that TOUCH the stretch (a vertex within A6_TOUCH_MM of it: the
    surface continuing across the wall right there; the band within A6_WALL_MM only when none touches, said), the face's DOMINANT facing (area-weighted) and its normal cone over every
    triangle (over 90 deg the face faces more than one way), the turn per stretch (A FLIP over 90 deg); the text said and kept (A6_SAID -> preflight.json); nothing for a face owning no wall
    (TK5 F1: a triangle counts for a stretch when it has an EDGE on it - two vertices within A6_TOUCH_MM; the one-vertex ones only when none has an edge there, said)
    edge. TK3 F3 (11-05): the first form took every triangle within 1.5 mm of the wall and 3 mm of the stretch's midpoint, area-weighted - three stretches read the same two triangles and a
    15 mm2 vane triangle hid the land's 140 deg flip; F4: the 146 deg cone was printed and not read."""
    try:
        own_ = [(b_, i_) for (q_, b_, i_) in BODY_E.values() if int(q_) == int(pi)]
        if not own_: return None
        vt_ = F[pid == pi]
        if len(vt_) < 1: return None
        n_ = np.cross(Vu[vt_[:, 1]] - Vu[vt_[:, 0]], Vu[vt_[:, 2]] - Vu[vt_[:, 0]]); a_ = np.linalg.norm(n_, axis=1); ok_ = a_ > 1e-9
        vt_ = vt_[ok_]; n_ = n_[ok_] / a_[ok_][:, None]; a_ = a_[ok_]; c_ = Vu[vt_].mean(1)
        md_ = (n_ * a_[:, None]).sum(0); md_ = md_ / max(float(np.linalg.norm(md_)), 1e-12)
        cone_ = float(np.degrees(np.arccos(np.clip(n_ @ md_, -1, 1))).max())
        wd_ = np.stack([c_ @ wn_ - wc_ for wn_, wc_ in walls], axis=1)
        capw_ = [K.wall_of(np.array([[v.X, v.Y, v.Z] for v in f_.Vertexes]))[0] for f_ in BFc]
        PV_ = Vu[vt_].reshape(-1, 3)
        parts_ = []
        for b_, i_ in own_:
            try: e_ = BFc[b_].Edges[i_]; w_ = int(capw_[b_]); S_ = np.array([[p.x, p.y, p.z] for p in e_.discretize(Number=max(3, int(float(e_.Length) / 0.2) + 1))], float)
            except Exception: continue
            nv_ = (cKDTree(S_).query(PV_)[0].reshape(-1, 3) <= A6_TOUCH_MM).sum(axis=1)
            tch_ = nv_ >= 2; how_ = "with an edge on it"
            if tch_.sum() < 1: tch_ = nv_ >= 1; how_ = "touching it at a vertex only - the neighbours' triangles, read with care"
            if tch_.sum() < 1:
                M_ = S_[len(S_) // 2]; tch_ = (np.abs(wd_[:, w_]) <= A6_WALL_MM) & (np.linalg.norm(c_ - M_, axis=1) <= max(3.0, 0.6 * float(e_.Length))); how_ = "none touches it - the nearest within %.1f mm" % A6_WALL_MM
            if tch_.sum() < 1: parts_.append("wall %s, a %.1f mm stretch: no triangle of this face touches it or lies within %.1f mm of it" % (_a6_wall_name(w_), float(e_.Length), A6_WALL_MM)); continue
            mw_ = (n_[tch_] * a_[tch_][:, None]).sum(0); mw_ = mw_ / max(float(np.linalg.norm(mw_)), 1e-12)
            spr_ = float(np.degrees(np.arccos(np.clip(n_[tch_] @ mw_, -1, 1))).max()); turn_ = float(np.degrees(np.arccos(np.clip(float(mw_ @ md_), -1, 1))))
            parts_.append("wall %s, a %.1f mm stretch: the body's own surface there faces %s (%d triangle(s) %s%s) - %.0f deg from the face's dominant facing%s"
                          % (_a6_wall_name(w_), float(e_.Length), _a6_dir(mw_), int(tch_.sum()), how_, (", spread %.0f deg" % spr_) if spr_ > 30 else "", turn_, " - A FLIP: no one surface faces both ways" if turn_ > 90 else ""))
        txt_ = ("   face %d AT THE WALL (31bu A6, the piece rule): its %d triangles face %s on the whole, within a cone of %.0f deg%s; %s - a piece owns only wall segments whose body surface faces like itself: "
                "give a segment facing the other way to the neighbour that faces like it (FEATURES), or end a split on the wall corner where the facing changes"
                % (pi, len(n_), _a6_dir(md_), cone_, " - THIS FACE FACES MORE THAN ONE WAY (the piece rule: one way)" if cone_ > 90 else "", "; ".join(parts_) or "no wall stretch could be read"))
        A6_SAID[int(pi)] = txt_; say(txt_); return txt_
    except Exception as ex_a6:
        txt_ = "   face %d AT THE WALL (31bu A6): not measured - %s" % (pi, str(ex_a6)[:80]); A6_SAID[int(pi)] = txt_; say(txt_); return txt_
kind = [p["kind"] for p in PJ]
# skin-wires
DEMOTED = {}
try:
    _wd = json.load(open(os.path.join(SK, "wires_demote.json"), encoding="utf-8"))
    if FRAME and _wd.get("network_frame_md5") == K.md5(os.path.join(SK, "network_frame.brep")):
        DEMOTED = {int(k_): v_ for k_, v_ in (_wd.get("demote") or {}).items()}
except (OSError, ValueError, TypeError):
    DEMOTED = {}
for _i in DEMOTED:
    if 0 <= _i < len(kind) and kind[_i] == "orig": kind[_i] = "changed"
if DEMOTED:
    say("ORIGINAL SURFACE LEFT (skin-wires): face(s) %s go to the flat / fit rungs - %s" % (sorted(DEMOTED), "; ".join(sorted(set(DEMOTED.values())))[:200]))
say("patches %d (%s); network %d edges, %d junctions" % (len(PJ), {k: kind.count(k) for k in set(kind)}, len(NE), len(JP)))
E_ = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); Es = np.sort(E_, 1); tri = np.tile(np.arange(len(F)), 3)
o = np.lexsort((Es[:, 1], Es[:, 0])); Es = Es[o]; tri = tri[o]; same = np.all(Es[1:] == Es[:-1], axis=1)
ta = tri[:-1][same]; tb = tri[1:][same]
TA = sp.coo_matrix((np.ones(2 * len(ta)), (np.concatenate([ta, tb]), np.concatenate([tb, ta]))), shape=(len(F), len(F))).tocsr()

def lscm(V, T):
    n = len(V); m = len(T)
    p0, p1, p2 = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    e1 = p1 - p0; l1 = np.linalg.norm(e1, axis=1); e1 = e1 / np.maximum(l1, 1e-12)[:, None]
    nr = np.cross(p1 - p0, p2 - p0); ar = 0.5 * np.linalg.norm(nr, axis=1); nr = nr / np.maximum(2 * ar, 1e-12)[:, None]
    e2 = np.cross(nr, e1)
    x = np.stack([np.zeros(m), l1, np.einsum("ij,ij->i", p2 - p0, e1)], 1); y = np.stack([np.zeros(m), np.zeros(m), np.einsum("ij,ij->i", p2 - p0, e2)], 1)
    sq = np.sqrt(np.maximum(2 * ar, 1e-12))
    rows, cols, wr, wi = [], [], [], []
    for j in range(3):
        k, l = (j + 1) % 3, (j + 2) % 3
        rows.append(np.arange(m)); cols.append(T[:, j]); wr.append((x[:, l] - x[:, k]) / sq); wi.append((y[:, l] - y[:, k]) / sq)
    rows = np.concatenate(rows); cols = np.concatenate(cols); wr = np.concatenate(wr); wi = np.concatenate(wi)
    Mr = sp.coo_matrix((wr, (rows, cols)), shape=(m, n)).tocsc(); Mi = sp.coo_matrix((wi, (rows, cols)), shape=(m, n)).tocsc()
    a = int(np.argmin(V.sum(1))); b = int(np.argmax(np.linalg.norm(V - V[a], axis=1))); L = float(np.linalg.norm(V[b] - V[a]))
    free = np.setdiff1d(np.arange(n), [a, b])
    A = sp.bmat([[Mr[:, free], -Mi[:, free]], [Mi[:, free], Mr[:, free]]]).tocsr()
    rhs = -np.concatenate([Mr[:, b].toarray().ravel() * L, Mi[:, b].toarray().ravel() * L])
    sol = spsolve((A.T @ A).tocsc(), A.T @ rhs)
    UV = np.zeros((n, 2)); UV[free, 0] = sol[:len(free)]; UV[free, 1] = sol[len(free):]; UV[b] = (L, 0.0)
    return UV

def basis(t, nc, deg=3):
    kn = np.concatenate([np.zeros(deg), np.linspace(0, 1, nc - deg + 1), np.ones(deg)])
    t = np.clip(np.asarray(t, float), 0, 1 - 1e-12)
    N = np.zeros((len(t), len(kn) - 1))
    for i in range(len(kn) - 1): N[:, i] = (t >= kn[i]) & (t < kn[i + 1])
    for p in range(1, deg + 1):
        Nn = np.zeros((len(t), len(kn) - 1 - p))
        for i in range(len(kn) - 1 - p):
            a = (t - kn[i]) / (kn[i + p] - kn[i]) if kn[i + p] > kn[i] else 0.0
            b = (kn[i + p + 1] - t) / (kn[i + p + 1] - kn[i + 1]) if kn[i + p + 1] > kn[i + 1] else 0.0
            Nn[:, i] = a * N[:, i] + b * N[:, i + 1]
        N = Nn
    return N[:, :nc]

class Patch(object):
    """a changed patch: LSCM map of the patch + rings, the locator, the fitted surface"""
    def __init__(self, pi):
        self.pi = pi
        sel = np.zeros(len(F), bool); sel[pid == pi] = True
        for _ in range(RINGS): sel = sel | (TA @ sel.astype(float) > 0)
        T = F[sel]; self.vids, Tl = np.unique(T, return_inverse=True); self.T = Tl.reshape(-1, 3); self.V = Vu[self.vids]
        UV = lscm(self.V, self.T)
        a3 = 0.5 * np.linalg.norm(np.cross(self.V[self.T[:, 1]] - self.V[self.T[:, 0]], self.V[self.T[:, 2]] - self.V[self.T[:, 0]]), axis=1).sum()
        a2 = 0.5 * np.abs(np.cross(UV[self.T[:, 1]] - UV[self.T[:, 0]], UV[self.T[:, 2]] - UV[self.T[:, 0]])).sum()
        UV *= np.sqrt(a3 / max(a2, 1e-12))
        self.flips = int((np.cross(UV[self.T[:, 1]] - UV[self.T[:, 0]], UV[self.T[:, 2]] - UV[self.T[:, 0]]) < 0).sum())
        self.lo = UV.min(0) - 0.3; self.hi = UV.max(0) + 0.3
        self.UVn = (UV - self.lo) / (self.hi - self.lo)
        self.kd = cKDTree(self.V[self.T].mean(axis=1))
    def locate(self, P):
        """3D points -> (normalised uv, distance) by the nearest of 10 candidate triangles (projection, clamped barycentrics)"""
        P = np.atleast_2d(P); _, nn = self.kd.query(P, k=min(10, len(self.T)), workers=-1)
        best_d = np.full(len(P), np.inf); best_uv = np.zeros((len(P), 2))
        for c in range(nn.shape[1]):
            Tt = self.T[nn[:, c]]; A = self.V[Tt[:, 0]]; B = self.V[Tt[:, 1]]; C = self.V[Tt[:, 2]]
            v0 = B - A; v1 = C - A; v2 = P - A
            d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1); d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
            den = np.maximum(d00 * d11 - d01 * d01, 1e-30)
            wv = (d11 * d20 - d01 * d21) / den; ww = (d00 * d21 - d01 * d20) / den; wu = 1 - wv - ww
            W = np.clip(np.stack([wu, wv, ww], 1), 0, None); W /= np.maximum(W.sum(1, keepdims=True), 1e-30)
            Q = W[:, :1] * A + W[:, 1:2] * B + W[:, 2:] * C; d = np.linalg.norm(P - Q, axis=1)
            uv = W[:, :1] * self.UVn[Tt[:, 0]] + W[:, 1:2] * self.UVn[Tt[:, 1]] + W[:, 2:] * self.UVn[Tt[:, 2]]
            m = d < best_d; best_d[m] = d[m]; best_uv[m] = uv[m]
        return best_uv, best_d
    def fit(self, bnd_uv, bnd_xyz):
        span = (self.hi - self.lo)
        self.nu = int(np.clip(np.ceil(span[0] / CTRL_MM) + 3, 4, 70)); self.nv = int(np.clip(np.ceil(span[1] / CTRL_MM) + 3, 4, 70))
        Vt_ = self.V; self.symfit = False
        if MP is not None and SYMFIT:
            Po = Vu[np.unique(F[pid == self.pi].ravel())]; sd = K.mirror_side(Po, MP[0], MP[1])
            if len(Po) and sd.min() < -0.3 and sd.max() > 0.3:
                _, j_ = cKDTree(self.V).query(K.reflect(self.V, MP[0], MP[1]), workers=-1)
                Vt_ = 0.5 * (self.V + K.reflect(self.V[j_], MP[0], MP[1])); self.symfit = True
        uv = np.vstack([self.UVn, bnd_uv]); X = np.vstack([Vt_, bnd_xyz])
        # boundary edges
        wv = np.ones(len(self.UVn))
        if len(bnd_xyz):
            dn, _ = cKDTree(bnd_xyz).query(self.V, workers=-1); wv[dn < NEAR_MM] = 0.05
        ownv = np.isin(self.vids, np.unique(F[pid == self.pi].ravel()))
        if os.environ.get("RING_W"): wv[~ownv] = float(os.environ["RING_W"])
        w = np.concatenate([wv, np.full(len(bnd_uv), W_EDGE)])
        Bu = basis(uv[:, 0], self.nu); Bv = basis(uv[:, 1], self.nv)
        iu = np.argsort(-Bu, axis=1)[:, :4]; iv = np.argsort(-Bv, axis=1)[:, :4]
        rows = np.repeat(np.arange(len(uv)), 16); cols = (iu[:, :, None] * self.nv + iv[:, None, :]).reshape(-1)
        vals = (np.take_along_axis(Bu, iu, 1)[:, :, None] * np.take_along_axis(Bv, iv, 1)[:, None, :]).reshape(-1)
        A = sp.coo_matrix((vals * np.repeat(np.sqrt(w), 16), (rows, cols)), shape=(len(uv), self.nu * self.nv)).tocsr()
        n = self.nu * self.nv; idx = np.arange(n).reshape(self.nu, self.nv)
        dr, dc, dv = [], [], []; r = 0
        for (a, b, c) in [(idx[:-2, :], idx[1:-1, :], idx[2:, :]), (idx[:, :-2], idx[:, 1:-1], idx[:, 2:])]:
            for x0, x1, x2 in zip(a.ravel(), b.ravel(), c.ravel()):
                dr += [r, r, r]; dc += [x0, x1, x2]; dv += [1.0, -2.0, 1.0]; r += 1
        D = sp.coo_matrix((dv, (dr, dc)), shape=(r, n)).tocsr()
        lam = LAM * (wv.sum() if os.environ.get("LAM_MODE", "all") == "vox" else w.sum()) / n
        M = (A.T @ A + lam * (D.T @ D)).tocsc()
        P = np.stack([spsolve(M, A.T @ (X[:, k] * np.sqrt(w))) for k in range(3)], 1).reshape(self.nu, self.nv, 3)
        kn = lambda nc: (list(np.linspace(0, 1, nc - 2)), [4] + [1] * (nc - 4) + [4])
        uk, um = kn(self.nu); vk, vm = kn(self.nv)
        bs = Part.BSplineSurface()
        bs.buildFromPolesMultsKnots([[V3(*P[i, j]) for j in range(self.nv)] for i in range(self.nu)], um, vm, uk, vk, False, False, 3, 3)
        self.bs = bs
        def ev(UVq): return np.array([[q.x, q.y, q.z] for q in (bs.value(float(a), float(b)) for a, b in UVq)])
        own = np.isin(self.vids, np.unique(F[pid == self.pi].ravel()))
        pin = np.nonzero(own)[0]; sub = pin[:: max(1, len(pin) // 1500)]
        dvox = np.linalg.norm(ev(self.UVn[sub]) - self.V[sub], axis=1)
        st = max(1, len(bnd_uv) // 800)
        dbnd = np.linalg.norm(ev(bnd_uv[::st]) - bnd_xyz[::st], axis=1) if len(bnd_uv) else np.zeros(1)
        return {"ctrl": [self.nu, self.nv], "flips": self.flips, "vox_p50": round(float(np.median(dvox)), 4), "vox_p95": round(float(np.percentile(dvox, 95)), 4),
                "vox_max": round(float(dvox.max()), 3), "edge_p95": round(float(np.percentile(dbnd, 95)), 4), "edge_max": round(float(dbnd.max()), 4), "symfit": self.symfit}


class _Surf(object):
    """a face's surface that is not a fit (31an: the plane rung) - only .bs is read when KEEP_NET=1"""
    def __init__(self, bs): self.bs = bs

def samples(e, step=0.3):
    n = max(3, int(e.Length / step) + 1)
    return np.array([[q.x, q.y, q.z] for q in e.discretize(Number=n)])
chg = [i for i, k in enumerate(kind) if k == "changed"]
pch = {}
for k, c in enumerate(CH):
    if ALL_E[k] is None: continue
    for p in c["pair"]: pch.setdefault(int(p), []).append(k)
if FRAME:
    for k, (q_, b_, i_) in BODY_E.items(): pch.setdefault(q_, []).append(k)
    say("FRAME: %d network chains dropped (the walls), %d body edges on %d skin faces, caps = the %d body faces" % (len(dropped_), len(BODY_E), len(FR["stretch"]), len(CAPB)))
PAT = {}; recs = {}
# skin-labels  skin-rim
PLANE = os.environ.get("PLANE", "1") == "1"; PLANE_P95 = float(os.environ.get("PLANE_P95", "0.08")); PLANE_MAX = float(os.environ.get("PLANE_MAX", "0.25")); nplane = 0
# skin-wires  guides.brep
# fillets.json
GUIDES = {}; SPLITS = {}; CUTS = []
try:
    _gj = json.load(open(os.path.join(SK, "guides.json"), encoding="utf-8"))
    if _gj.get("network_frame_md5") == K.md5(os.path.join(SK, "network_frame.brep")):
        _gs = Part.Shape(); _gs.importBrep(os.path.join(SK, "guides.brep")) if os.path.isfile(os.path.join(SK, "guides.brep")) else None; _ge = _gs.Edges if _gs.Edges else []
        for g_ in _gj.get("guides", []):
            if 0 <= int(g_["edge"]) < len(_ge): (SPLITS if g_.get("role") == "split" else GUIDES).setdefault(int(g_["face"]), []).append((g_, _ge[int(g_["edge"])]))
        CUTS = list(_gj.get("cuts") or [])
    elif _gj.get("guides"):
        say("added lines (skin\\guides.json) are of an EARLIER wireframe - ignored (L119); run skin-wires again")
except (OSError, ValueError, TypeError):
    GUIDES = {}; SPLITS = {}; CUTS = []
def _kchk(f_):
    """31bq S: the kernel's own words on a face - check(True)'s distinct lines (BOP noise dropped), or 'check(True) passes'"""
    try:
        f_.check(True); return "check(True) passes"
    except Exception as _e:
        return "; ".join(sorted(set(l_.strip() for l_ in str(_e).splitlines() if l_.strip() and "BOP" not in l_)))[:140] or str(_e)[:100]
def _prm_on(e_, pt_):
    """31bq B20 (2): the parameter of the point of edge e_ nearest pt_ - by the kernel's distToShape (Curve.parameter misses a point on the edge within
    tolerance: fix 5w's lesson at the corner-edge cut, the same miss at the split-end cuts); Curve.parameter is the fallback"""
    try:
        _d, _p, _i = e_.distToShape(Part.Vertex(pt_))
        if _i and _i[0][2] is not None: return float(_i[0][2])
    except Exception: pass
    return e_.Curve.parameter(pt_)
if CUTS and FIT == "span":
    for c_ in CUTS:
        if c_.get("what") == "wall": K._fail("FAIL: a SPLIT on face %s ends inside a wall edge of the edit region - the caps are the body's own faces and are not cut (L114): end it at the wall's corner (c<n>) instead" % c_.get("face"))
    if not KEEP_NET: K._fail("FAIL: SPLIT lines need KEEP_NET=1 (the network's own edges used unchanged)")
    for c_ in CUTS:
        k_ = int(c_["chain"]); e_ = ALL_E[k_]
        if e_ is None: continue
        pieces_ = e_ if isinstance(e_, list) else [e_]; out_ = []
        _dd_ = []
        for pe_ in pieces_:
            try: _dd_.append(float(pe_.distToShape(Part.Vertex(V3(*c_["at"])))[0]))
            except Exception: _dd_.append(9e9)
        _ib_ = int(np.argmin(_dd_)) if _dd_ else -1
        if _ib_ >= 0 and _dd_[_ib_] > 0.05: say("split: line %d stays UNCUT - the split's end is %.2f mm from it (over 0.05 mm; the split ends at the line's vertex instead) (31bq B20)" % (k_, _dd_[_ib_]))
        for _jp_, pe_ in enumerate(pieces_):
            if _jp_ != _ib_ or _dd_[_ib_] > 0.05: out_.append(pe_); continue
            try:
                prm_ = _prm_on(pe_, V3(*c_["at"])); lo_, hi_ = sorted((pe_.FirstParameter, pe_.LastParameter))
                if not (lo_ < prm_ < hi_): out_.append(pe_); continue
                w_ = pe_.split([prm_]); sub_ = [x_ for x_ in w_.Edges if x_.Length > 1e-4]
                out_.extend(sub_ if len(sub_) == 2 else [pe_])
            except Exception as ex_:
                out_.append(pe_); say("split: line %d could not be cut at the split's end (%s) - the split ends at the line's vertex instead" % (k_, str(ex_)[:60]))
        ALL_E[k_] = out_ if len(out_) > 1 else out_[0]
    say("SPLITS: %d border line(s) cut where a split ends" % sum(1 for e_ in ALL_E if isinstance(e_, list)))
def _split_edges(se_):
    """a split is one edge or a CHAIN of edges (31bl: a fillet's end line + offset line + end line)"""
    return list(se_) if isinstance(se_, (list, tuple)) else [se_]
def _split_ends(se_):
    """the two free ends of a split (an edge's vertices; a chain's - the end points that occur once)"""
    eds_ = _split_edges(se_)
    if len(eds_) == 1: return (np.array([eds_[0].Vertexes[0].X, eds_[0].Vertexes[0].Y, eds_[0].Vertexes[0].Z]), np.array([eds_[0].Vertexes[-1].X, eds_[0].Vertexes[-1].Y, eds_[0].Vertexes[-1].Z]))
    pts_ = [np.array([v.X, v.Y, v.Z]) for e_ in eds_ for v in (e_.Vertexes[0], e_.Vertexes[-1])]
    free_ = [P for P in pts_ if sum(1 for Q in pts_ if np.linalg.norm(P - Q) < 1e-6) == 1]
    if len(free_) != 2: return pts_[0], pts_[-1]
    return free_[0], free_[1]
def _wtxt(g_, n_=80):
    """31bq R7W (M9, A3 finding 5): a split's reason in a failure text - a KIT split's (a blend's strip: its record names the fillet) WHOLE, so the retry's anchored name
    (_KIT_SPLIT_RE: ', by lines, from [') survives a member list of any length (cut at 80 a chain of 5 legged members lost it: no blame, every blend lost, the agent's
    advice given); an agent's own why cut at n_"""
    w_ = str((g_ or {}).get("why", ""))
    return w_ if (g_ or {}).get("fillet") is not None else w_[:n_]
def _flat_e(lst):
    """the edges of a face: a cut chain is a list of pieces"""
    out = []
    for x in lst:
        if x is None: continue
        out.extend(x if isinstance(x, list) else [x])
    return out
FILLETS = []
try:
    _fj = json.load(open(os.path.join(SK, "fillets.json"), encoding="utf-8"))
    if _fj.get("network_frame_md5") == K.md5(os.path.join(SK, "network_frame.brep")): FILLETS = list(_fj.get("fillets", []))
    elif _fj.get("fillets"): say("fillets (skin\\fillets.json) are of an EARLIER wireframe - ignored (L119); run skin-wires again")
except (OSError, ValueError, TypeError):
    FILLETS = []
_sok_b = [f_ for f_ in FILLETS if f_.get("sharp_ok")]
if _sok_b:
    say("fillet line(s) %s stand SHARP by the agent's sharp_ok - not swept, not tried by the kernel (31bx R5 F2: the chain-mates end at its junctions as at an unmade member)" % sorted(set(int(f_["line"]) for f_ in _sok_b if str(f_.get("line", "")).lstrip("-").isdigit())))
def _kernel_chain_of(f_, fils_=None):
    """31bq R7W chain-kernel (the open list's F.2): the chain a _fillets record is a MEMBER of - a CHAIN entry of two or more distinct lines (a leg of a split
    line counts as its line); None for a single-line entry (the kernel's per-line fillet is tried on it as before). A chain is ONE blend with corners
    (BURRITO_STEPS L143 addendum 2) made by the lines pass's chain assembly - the mitre at a concave junction, the pivot patch at a convex one: the kernel
    rounding one member alone leaves a kernel face with no corner construction at its junctions beside the lines-made neighbours, and the chain SPLITS there
    (the blend-forms round's wfold / wfold2 copies: 34 / 55 / 110 rounded by the kernel, the shell open, the B03 retry dropping the sound 74 / 77)"""
    try: cid_ = f_.get("chain")
    except AttributeError: return None
    if cid_ is None: return None
    lines_ = set()
    for g_ in ((FILLETS if fils_ is None else fils_) or []):
        try:
            if g_.get("chain") is not None and str(g_.get("chain")) == str(cid_): lines_.add(int(g_["line"]))
        except (AttributeError, KeyError, TypeError, ValueError): continue
    return cid_ if len(lines_) >= 2 else None
def _dup_entries(fils_):
    """31bq R7W (M4, A1 finding 3): every crease decided in TWO _fillets entries - [(line, [the entries that hold it])]. A chain member, a single line and a "leg": "all"
    stand for the whole line; "leg": n for that leg alone (two legs of one line are two creases). FIL_MERGE is keyed by the line: a crease in two entries was swept twice,
    the second record overwrote the first, both chains assembled on it, the shell opened and the retry blamed "the room, the sense, a split" (vR5x C3-carry z2: chains 3 /
    4 the reversed duplicates of 2 / 1, 26 free edges). skin-wires refuses it when it writes the file (R5f); a fillets.json written before that rule, or by hand, on the
    same network reaches the build"""
    by_ = {}
    for i_, f_ in enumerate(fils_ or []):
        try: k_ = int(f_["line"])
        except (KeyError, TypeError, ValueError): continue
        lg_ = f_.get("leg"); whole_ = f_.get("chain") is not None or lg_ is None or not str(lg_).strip().lstrip("-").isdigit()
        by_.setdefault(k_, []).append(("*" if whole_ else int(str(lg_).strip()), ("chain %s" % f_["chain"]) if f_.get("chain") is not None else ("entry %d%s" % (i_, "" if whole_ else " (leg %s)" % lg_))))
    out_ = []
    for k_, L_ in sorted(by_.items()):
        hit_ = sorted(set(d_ for a_ in range(len(L_)) for b_ in range(a_ + 1, len(L_)) if (L_[a_][0] == "*" or L_[b_][0] == "*" or L_[a_][0] == L_[b_][0]) for d_ in (L_[a_][1], L_[b_][1])))
        if hit_: out_.append((k_, hit_))
    return out_
def _dup_text(d_):
    return "; ".join("line %d in %s" % (k_, " and ".join(h_)) for k_, h_ in d_)
if GUIDES: say("ADDED LINES: %d inside %d face(s) - each face's surface passes through them" % (sum(len(v) for v in GUIDES.values()), len(GUIDES)))
FILLET_LINES = set(int(x) for x in os.environ.get("FILLET_LINES", "").replace(";", ",").split(",") if x.strip().lstrip("-").isdigit())
FIL_MERGE = {}
FIL_NOT_MADE = {}
FIL_HOLD = {}
BLEND_FACES = {}    # ORIGINAL
ORIG_FIL = {}       # ORIGINAL
ORIG_FIL_SRC = {}   # NOT VALID
CREASE_MIN_DEG = float(os.environ.get("CREASE_MIN_DEG", "8") or 8)
CHAIN_MODE = (os.environ.get("CHAIN_MODE", "corner") or "corner").strip().lower()
if CHAIN_MODE != "corner": K._fail("FAIL: CHAIN_MODE=%s - the chain blend has one route, the rolling-ball corner (CHAIN_MODE=corner; \"caps\" was retired 2026-10-16: 20-23 free edges on the agent's b23 copy, the two blends overlapping on the common face at a concave junction - the kit's development record 31bp fix 5)" % CHAIN_MODE)
FIL_TAPER = os.environ.get("FIL_TAPER", "1") != "0"
CONTACT_MERGE_MAX = float(os.environ.get("CONTACT_MERGE_MAX", "2.5") or 2.5)      # corner edge
TAPER_X = float(os.environ.get("TAPER_X", "3") or 3); TAPER_MIN = float(os.environ.get("TAPER_MIN", "1.0") or 1.0)
THIN_FIL = float(os.environ.get("THIN_MM", "0.3") or 0.3)   # skin-build
FIL_SMOOTH_MM = float(os.environ.get("FIL_SMOOTH_MM", "1.5") or 1.5)
CREASE_TURN_MAX = float(os.environ.get("CREASE_TURN_MAX", "45") or 45)
RIBBON_MM = float(os.environ.get("RIBBON_MM", "0.3") or 0)
RIBBON_STEP = float(os.environ.get("RIBBON_STEP", "1.0") or 1.0)
TWIN_BETA_TOL = 10.0; TWIN_T_TOL = 0.15
_CEN_ALL = None
def _mirror_ids(ids_):
    """31bq R7W (M3): the original face at the mirror image of each id's triangles' centroid (its twin across the card's plane); [] without a face index or a plane"""
    global _CEN_ALL
    out_ = []
    if FID is None or MP is None: return out_
    if _CEN_ALL is None: _CEN_ALL = cKDTree(Vu[F].mean(1))
    for b_ in ids_ or []:
        T_ = np.nonzero(FID == int(b_))[0]
        if not len(T_): continue
        R_ = K.reflect(Vu[F[T_]].mean(1).mean(0)[None, :], MP[0], MP[1])[0]; _d_, j_ = _CEN_ALL.query(R_)
        if int(FID[int(j_)]) != int(b_): out_.append(int(FID[int(j_)]))
    return sorted(set(out_))
def _twin_cause(bur_, mbur_, faces_):
    """31bq R7W (M3): why a twin reads another crease than its master - its "buried" ids against the faces beside its line, and the MIRROR TWINS of its master's ids"""
    try:
        if FID is None: return "the mesh beside its line is not its master's mirror (regions.npz carries no face index to say more)"
        own_ = set(int(x_) for f__ in faces_ for x_ in np.unique(FID[pid == f__]))
        bits_ = []
        if bur_ and not (set(int(x_) for x_ in bur_) & own_): bits_.append("its \"buried\" %s lie on NONE of its faces %s" % (sorted(bur_), list(faces_)))
        tw_ = sorted(set(_mirror_ids(mbur_ or bur_)) & own_)
        if tw_: bits_.append("the MIRROR TWINS %s of the%s buried ids %s lie beside this line - name them in this entry's \"buried\" (skin-wires' kit mirror copies the master's ids; the kit does not mirror original-face ids)" % (tw_, " master's" if mbur_ else "", sorted(mbur_ or bur_)))
        return "; ".join(bits_) or "its buried ids and its master's do not explain it - look at both creases"
    except Exception as ex_tc: return "(the cause could not be read: %s)" % str(ex_tc)[:80]
BURIED_MIN = float(os.environ.get("BURIED_MIN", "0.3") or 0.3); BURIED_REACH = float(os.environ.get("BURIED_REACH", "2.0") or 2.0)
def _face_tri_normals(f):
    T_ = F[pid == f]; n_ = np.cross(Vu[T_[:, 1]] - Vu[T_[:, 0]], Vu[T_[:, 2]] - Vu[T_[:, 0]]); a_ = np.linalg.norm(n_, axis=1); ok_ = a_ > 1e-9
    return Vu[T_[ok_]].mean(1), n_[ok_] / a_[ok_][:, None]
def _edge_pts(e_, step=0.3):
    return np.vstack([samples(x_, step) for x_ in _flat_e([e_])])
def _master_fl(mo_, leg_=None, J0_=None, J1_=None):
    """31bq PP (B05 (2) / B41 (h)): the master line's blend record - FIL_MERGE is keyed by the line for a whole line and by len(ALL_E) for a LEG, so a legged
    twin never found its legged master: the master's records are found by their line, a leg among them by its place (the leg whose ends reflect onto this one's)"""
    if mo_ is None: return None
    try:
        recs_ = [fl_ for fl_ in FIL_MERGE.values() if int(fl_.get("chain", -1)) == int(mo_)]
        if not recs_: return None
        if leg_ is None or len(recs_) == 1: return next((fl_ for fl_ in recs_ if fl_.get("leg") is None), recs_[0])
        if MP is not None and J0_ is not None and J1_ is not None:
            R_ = K.reflect(np.array([J0_, J1_], float), MP[0], MP[1])
            return min(recs_, key=lambda fl_: min(float(np.linalg.norm(np.asarray(fl_["J"][0], float) - R_[0]) + np.linalg.norm(np.asarray(fl_["J"][1], float) - R_[1])), float(np.linalg.norm(np.asarray(fl_["J"][0], float) - R_[1]) + np.linalg.norm(np.asarray(fl_["J"][1], float) - R_[0]))))
        return next((fl_ for fl_ in recs_ if fl_.get("leg") == leg_), recs_[0])
    except Exception: return None
def _fillet_lines(f_):
    k = int(f_["line"]); r = float(f_["r"]); p_, q_ = [int(x) for x in CH[k]["pair"]]
    if kind[p_] == "cap" or kind[q_] == "cap":
        raise RuntimeError("a fillet by lines does not touch a cap (the body's own section face): line %d is between %d (%s) and %d (%s)" % (k, p_, kind[p_], q_, kind[q_]))
    # ORIGINAL
    leg_ = f_.get("leg"); cr_e = NE[k]
    BUR_ = set(int(x) for x in (f_.get("buried") or []) if str(x).lstrip("-").isdigit()); SRCF = {}; SRCF_SHARE = {}; BUR_SHARE = {}
    if leg_ is not None:
        pcs_l = ALL_E[k] if isinstance(ALL_E[k], list) else None
        if not pcs_l: raise RuntimeError("line %d is ONE piece - a fillet PER LEG needs a split (or a decided line) ending ON the crease, which makes the corner a junction and cuts the line into legs; this line is not cut (drop \"leg\", or end a split on the corner)" % k)
        if not (0 <= int(leg_) < len(pcs_l)): raise RuntimeError("line %d has %d leg(s) (the pieces between its junctions and the split end(s) on it) - leg %s does not exist" % (k, len(pcs_l), leg_))
        cr_e = pcs_l[int(leg_)]
    S_ = samples(cr_e, 0.3); J0, J1 = S_[0], S_[-1]
    # corner edge
    # corner edge
    _EXT = {int(e__): float(c__["extend"]) for e__, c__ in (f_.get("chain_c") or {}).items() if c__.get("extend")}
    core_ = np.ones(len(S_), bool)
    if _EXT and len(S_) >= 2:
        T0_ = S_[1] - S_[0]; T0_ = T0_ / max(np.linalg.norm(T0_), 1e-9); T1_ = S_[-1] - S_[-2]; T1_ = T1_ / max(np.linalg.norm(T1_), 1e-9)
        pre_ = [S_[0] - T0_ * s_ for s_ in np.arange(0.3, _EXT.get(0, 0.0) + 0.15, 0.3)][::-1] if _EXT.get(0, 0.0) > 0 else []
        post_ = [S_[-1] + T1_ * s_ for s_ in np.arange(0.3, _EXT.get(1, 0.0) + 0.15, 0.3)] if _EXT.get(1, 0.0) > 0 else []
        core_ = np.concatenate([np.zeros(len(pre_), bool), core_, np.zeros(len(post_), bool)])
        S_ = np.vstack([np.array(pre_, float).reshape(-1, 3), S_, np.array(post_, float).reshape(-1, 3)])
    _CUTB = {int(e__): float(c__["cutback"]) for e__, c__ in (f_.get("chain_c") or {}).items() if c__.get("cutback")}
    if _CUTB and len(S_) >= 4:
        for e__, cb__ in sorted(_CUTB.items()):
            if cb__ <= 1e-6: continue
            _cs = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(S_, axis=0), axis=1))]); _from = _cs if e__ == 0 else (_cs[-1] - _cs); _keep = _from > cb__ + 1e-9
            if int(_keep.sum()) < 3: raise RuntimeError("line %s: the vertex ball's station lies %.2f mm from its end %d and leaves no crease to sweep (%.2f mm long) - the ball is as long as the crease: a smaller R, or no fillet on the corner edge" % (k if leg_ is None else "%d leg %s" % (k, leg_), cb__, e__, _cs[-1]))
            _i1 = int(np.argmax(_keep)) if e__ == 0 else int(len(S_) - 1 - np.argmax(_keep[::-1]))
            _j0 = _i1 - 1 if e__ == 0 else _i1 + 1; _seg = S_[_i1] - S_[_j0]; _P = S_[_i1] - _seg / max(float(np.linalg.norm(_seg)), 1e-12) * float(_from[_i1] - cb__)
            if e__ == 0: S_ = np.vstack([_P[None, :], S_[_i1:]]); core_ = np.concatenate([[True], core_[_i1:]])
            else: S_ = np.vstack([S_[:_i1 + 1], _P[None, :]]); core_ = np.concatenate([core_[:_i1 + 1], [True]])
    _jv_ = [np.array([v.X, v.Y, v.Z]) for v in (NE[k].Vertexes[0], NE[k].Vertexes[-1])]
    SPLIT_END = [bool(min(np.linalg.norm(J - jv) for jv in _jv_) > 1e-3) for J in (J0, J1)]
    # corner edge
    CHAIN_END = [bool(x_) for x_ in (f_.get("chain_ends") or [False, False])]; CHAIN_A = f_.get("chain_common"); CHAIN_C = f_.get("chain_c") or {}
    FREED = set(int(x_) for x_ in (f_.get("freed") or []))      # corner edge
    CHAIN_LINES = set(int(x_) for x_ in (f_.get("chain_lines") or []))
    TAPER_RUN = {int(k__): float(v__) for k__, v__ in (f_.get("taper_run") or {}).items()}
    NO_TAPER = [bool(x_) for x_ in (f_.get("no_taper") or [False, False])]
    if any(CHAIN_END): SPLIT_END = [bool(SPLIT_END[e_] and not CHAIN_END[e_]) for e_ in (0, 1)]
    L_ = float(np.linalg.norm(J1 - J0))
    T_ = np.gradient(S_, axis=0); T_ /= np.maximum(np.linalg.norm(T_, axis=1), 1e-9)[:, None]
    _w = max(1, int(1.5 / 0.3)); _tn = np.diff(S_, axis=0); _tn /= np.maximum(np.linalg.norm(_tn, axis=1), 1e-9)[:, None]
    if len(_tn) >= 3:
        _st = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", _tn[:-1], _tn[1:]), -1.0, 1.0)))
        if len(_tn) > _w: _turn = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", _tn[:-_w], _tn[_w:]), -1.0, 1.0)))
        else: _turn = np.array([float(np.degrees(np.arccos(np.clip(float(_tn[0] @ _tn[-1]), -1.0, 1.0))))])
        _i = int(np.argmax(_turn)); _kink = float(_st.max()) if len(_st) else 0.0; _med = float(np.median(_st)) if len(_st) else 0.0
        if float(_turn[_i]) > CREASE_TURN_MAX and _kink > max(3.0 * _med, 0.5 * float(_turn[_i])):
            raise RuntimeError("line %d has a CORNER inside it: its tangent turns %.0f deg within 1.5 mm at %s (CREASE_TURN_MAX %g) - a fillet by lines sweeps ONE smooth crease, and round a corner the inner face's offset line crosses itself and the blend folds (the kernel's fillet fails there for the same reason). EITHER make the corner a junction - end a split or a decided line there, so the line is cut into legs - and decide the fillet PER LEG: the same _fillets entry with \"leg\": \"all\" (each leg its own smooth crease, the blend tapering to nothing at the corner, which stays a point) - OR drop the fillet on this line. The kit measures; it does not choose"
                               % (k, float(_turn[_i]), np.round(S_[min(_i + _w // 2, len(S_) - 1)], 1).tolist(), CREASE_TURN_MAX))
    NF = {}; NL = {}; FO = {}
    def _local_normals(f):
        n_f, n_loc, _inf9 = K.local_face_normals(Vu, F, pid, f, S_)
        if n_loc is None: raise RuntimeError("face %d has no voxel triangles" % f)
        if _inf9.get("excluded"): say("   fillet line %s: face %d is thin or wraps beside the crease - %d of its nearest mesh triangles face the other way and are left out of its normal (fix 9: the sheet at the crease decides)" % (k if leg_ is None else "%d leg %s" % (k, leg_), f, _inf9["excluded"]))
        # 31bp fix 11: A BURIED FACE
        if BUR_ and FID is not None and f not in SRCF:
            try:
                Tf_ = np.nonzero(pid == f)[0]
                if len(Tf_):
                    Cf_ = Vu[F[Tf_]].mean(1); _d1, _j1 = K.knn(Cf_, S_, 1); _j1 = np.asarray(_j1, int).reshape(-1); _d1 = np.asarray(_d1, float).reshape(-1)
                    near_ = _d1 < 2.5; fb_ = np.isin(FID[Tf_[_j1]], list(BUR_)) & near_
                    share_ = float(fb_.sum()) / max(1, int(near_.sum())) if near_.any() else 0.0
                    BUR_SHARE[f] = share_
                    if share_ >= BURIED_MIN:
                        # 31bp fix 11b: THE HOST'S SURFACE IS ONE OF ITS OWN UNBURIED ORIGINAL FACES  recorded
                        # recorded
                        try: _nopt_ = set(int(r__["face"]) for r__ in json.load(open(os.path.join(SK, "points_faces.json"), encoding="utf-8")) if not int(r__.get("on") or 0))
                        except Exception: _nopt_ = set()
                        fidn_ = FID[Tf_[_j1]]; cands_ = {}
                        for x_ in np.unique(fidn_[near_]):
                            if int(x_) >= 0 and int(x_) not in BUR_ and int(x_) not in _nopt_: cands_[int(x_)] = int(((fidn_ == x_) & near_).sum())
                        for x_ in np.unique(FID[Tf_]):
                            if int(x_) >= 0 and int(x_) not in BUR_ and int(x_) not in cands_ and int(x_) not in _nopt_: cands_[int(x_)] = 0
                        _drp4 = sorted(int(x_) for x_ in np.unique(FID[Tf_]) if int(x_) >= 0 and int(x_) not in BUR_ and int(x_) in _nopt_)
                        if _drp4: say("   fillet line %s: original face(s) %s under face %d got NO point (the points dropped them) - not a source surface for the host (31br D4; the agent's d9 laid the offset on the dropped slot wall 2356, 3.3 mm off the built face)" % (k if leg_ is None else "%d leg %s" % (k, leg_), _drp4, f))
                        pj_ = PJ[f].get("face") if PJ[f].get("face") is not None else PJ[f].get("face_src")
                        order_ = sorted(cands_, key=lambda c_: -cands_[c_])
                        if pj_ is not None and int(pj_) in cands_: order_ = [int(pj_)] + [c_ for c_ in order_ if c_ != int(pj_)]
                        if not order_: raise RuntimeError("line %s buries %s beside face %d, and face %d has no unburied original face of its own to stand for the mesh (its recorded source %s is buried): fold the buried face into a neighbour that has a surface there" % (k if leg_ is None else "%d leg %s" % (k, leg_), sorted(BUR_), f, f, pj_))
                        tried_ = []; src_ = None
                        for c_ in order_:
                            S_o = BF[int(c_)].Surface; prj_ = []; n_s = []
                            for s_ in S_:
                                uu_, vv_ = S_o.parameter(V3(*s_)); pt_ = S_o.value(uu_, vv_); prj_.append([pt_.x, pt_.y, pt_.z]); nn_ = S_o.normal(uu_, vv_); v_ = np.array([nn_.x, nn_.y, nn_.z]); n_s.append(v_ / max(np.linalg.norm(v_), 1e-9))
                            prj_ = np.array(prj_); n_s = np.array(n_s); d_reach = float(np.median(np.linalg.norm(prj_ - S_, axis=1))); tried_.append((int(c_), d_reach))
                            if d_reach <= BURIED_REACH: src_ = int(c_); break
                        if src_ is None:
                            raise RuntimeError("line %s buries %s beside face %d, but face %d's own unburied original face %d does not reach the crease (%.2f mm from it; every candidate: %s - the median mm from the crease; over BURIED_REACH %g): there is nothing of face %d to blend to there - fold the buried face into the neighbour whose surface reaches the line, or draw the line where the surface is" % (k if leg_ is None else "%d leg %s" % (k, leg_), sorted(BUR_), f, f, tried_[0][0], tried_[0][1], ", ".join("%d: %.2f" % t__ for t__ in tried_), BURIED_REACH, f))
                        if pj_ is not None and int(pj_) in BUR_: say("   fillet line %s: face %d's recorded source %d is itself a BURIED face - its own unburied original %d stands for it (fix 11b)" % (k if leg_ is None else "%d leg %s" % (k, leg_), f, int(pj_), src_))
                        # cannot be read
                        try:
                            if str(BF[int(src_)].Orientation) == "Reversed": n_s = -n_s
                            _nref_bf = True
                        except Exception: _nref_bf = False
                        own_ = Tf_[~np.isin(FID[Tf_], list(BUR_))]
                        if len(own_):
                            try:
                                Co_ = Vu[F[own_]].mean(1); no_ = np.cross(Vu[F[own_][:, 1]] - Vu[F[own_][:, 0]], Vu[F[own_][:, 2]] - Vu[F[own_][:, 0]]); ao_ = np.linalg.norm(no_, axis=1); ok_ = ao_ > 1e-9
                                Co_ = Co_[ok_]; no_ = no_[ok_] / ao_[ok_][:, None]
                                _do, _jo = K.knn(Co_, S_, int(min(8, len(Co_)))); _jo = np.asarray(_jo, int).reshape(len(S_), -1)
                                nref_ = no_[_jo].mean(1); nref_ /= np.maximum(np.linalg.norm(nref_, axis=1), 1e-9)[:, None]
                                flip_ = np.einsum("ij,ij->i", n_s, nref_) < 0
                                if not _nref_bf: n_s[flip_] = -n_s[flip_]
                                elif float(flip_.mean()) > 0.5: say("   fillet line %s: face %d's source surface %d - its orientation's outward normal and the face's own unburied triangles disagree on %.0f %% of the samples (the orientation kept - a cross-check, 31bq B05 (c))" % (k if leg_ is None else "%d leg %s" % (k, leg_), f, int(src_), 100.0 * float(flip_.mean())))
                            except Exception: pass
                        SRCF[f] = int(src_); SRCF_SHARE[f] = share_
                        say("   fillet line %s: the mesh beside the crease on face %d is the BURIED face(s) %s's (%.0f %% of the samples) - face %d's own source surface %d stands for it there (%.2f mm from the line): its normals, its offset and its side from the surface, the sense from the two faces' material directions (fix 11)" % (
                            k if leg_ is None else "%d leg %s" % (k, leg_), f, sorted(BUR_), 100 * share_, f, int(src_), d_reach))
                        n_f = n_s.mean(0); n_f /= max(np.linalg.norm(n_f), 1e-9)
                        return n_f, n_s
            except RuntimeError: raise
            except Exception as ex_b:
                say("   fillet line %s: the buried-face reading on face %d failed (%s) - the layout mesh stands" % (k if leg_ is None else "%d leg %s" % (k, leg_), f, str(ex_b)[:100]))
        # ORIGINAL
        if kind[f] == "orig" and (PJ[f].get("face") is not None):
            try:
                S_o = BF[int(PJ[f]["face"])].Surface; n_s = []
                for i_, s_ in enumerate(S_):
                    uu_, vv_ = S_o.parameter(V3(*s_)); nn_ = S_o.normal(uu_, vv_); v_ = np.array([nn_.x, nn_.y, nn_.z]); v_ /= max(np.linalg.norm(v_), 1e-9)
                    if float(v_ @ n_loc[i_]) < 0: v_ = -v_
                    n_s.append(v_)
                n_s = np.array(n_s); _dev = float(np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", n_s, n_loc), -1.0, 1.0))).max())
                if _dev > 5.0: say("   fillet line %s: face %d is an original face - its own surface's normals taken along the crease (the layout mesh's were up to %.0f deg off there)" % (k if leg_ is None else "%d leg %s" % (k, leg_), f, _dev))
                n_f = n_s.mean(0); n_f /= max(np.linalg.norm(n_f), 1e-9)
                return n_f, n_s
            except Exception as ex_o:
                say("   fillet line %s: face %d's own surface normals could not be taken (%s) - the layout mesh's stand" % (k if leg_ is None else "%d leg %s" % (k, leg_), f, str(ex_o)[:80]))
        if FIL_SMOOTH_MM > 0 and len(S_) > 4:
            from scipy.ndimage import gaussian_filter1d as _gf
            _ds = float(np.median(np.linalg.norm(np.diff(S_, axis=0), axis=1))) or 0.3
            n_loc = np.stack([_gf(n_loc[:, c_], max(0.5, FIL_SMOOTH_MM / _ds), mode="nearest") for c_ in range(3)], 1)
            n_loc /= np.maximum(np.linalg.norm(n_loc, axis=1), 1e-9)[:, None]
        return n_f, n_loc
    for f in (p_, q_): NF[f], NL[f] = _local_normals(f)
    if BUR_ and FID is None and not globals().get("_SAID_NOFID"):
        globals()["_SAID_NOFID"] = True; say("   fillet line %s: \"buried\" %s given but regions.npz carries no face index (fid) - the mesh stands as it is; run skin-regions again on this source" % (k if leg_ is None else "%d leg %s" % (k, leg_), sorted(BUR_)))
    if BUR_ and not SRCF and FID is not None and any(np.isin(FID[pid == f__], list(BUR_)).any() for f__ in (p_, q_)):
        say("   fillet line %s: \"buried\" %s matched nothing beside this line (the buried faces' share of the samples: %s; BURIED_MIN %g%s) - the layout mesh stands: check the ids, or the line" % (
            k if leg_ is None else "%d leg %s" % (k, leg_), sorted(BUR_), ", ".join("face %d %.0f %%" % (f__, 100 * s__) for f__, s__ in sorted(BUR_SHARE.items())) or "no sample read", BURIED_MIN, "" if FID is not None else "; no face index in regions.npz"))
    beta_ = np.degrees(np.arccos(np.clip(np.einsum("ij,ij->i", NL[p_], NL[q_]), -1, 1)))
    try:
        _cj = json.load(open(os.path.join(SK, "fillet_creases.json"), encoding="utf-8"))
        if _cj.get("network_frame_md5") == K.md5(os.path.join(SK, "network_frame.brep")) and str(k) in (_cj.get("beta_built_deg") or {}):
            _bb = float(_cj["beta_built_deg"][str(k)])
            if _bb < CREASE_MIN_DEG: raise RuntimeError("line %d is NO CREASE AS BUILT: faces %d and %d meet at %.0f deg on the built piece (the layout's mesh has %.0f deg; under CREASE_MIN_DEG %g) - the surfaces the ladder built are tangent there, nothing to round; decide the border as a crease (a split, a different surface beside it), or drop the fillet entry" % (k, p_, q_, _bb, float(np.median(beta_)), CREASE_MIN_DEG))
    except RuntimeError: raise
    except Exception: pass
    if float(np.median(beta_)) < CREASE_MIN_DEG:
        raise RuntimeError("line %d is NO CREASE: faces %d and %d meet at %.0f deg (under CREASE_MIN_DEG %g) - there is nothing to round; drop the fillet entry, or decide the line that IS the corner" % (k, p_, q_, float(np.median(beta_)), CREASE_MIN_DEG))
    t_ = r * np.tan(np.radians(np.clip(beta_, 0.0, 170.0)) / 2.0)
    t_mid = float(np.median(t_))
    need_x = 2.5 * (1.0 - 0.5 * sum(1 for x_ in (0, 1) if CHAIN_END[x_] or NO_TAPER[x_]))
    if need_x > 0 and L_ < need_x * t_mid:
        r_cap = round(r * (L_ / need_x) / max(t_mid, 1e-6), 3)
        say("   fillet line %d: R %g needs t %.2f mm of each face (beta %.0f deg) - more than the line's %.1f mm / %g: R capped to %.3f (a fillet by lines needs %g t of line for its run-out(s))" % (k, r, t_mid, float(np.median(beta_)), L_, need_x, r_cap, need_x))
        r = r_cap; f_ = dict(f_, r=r); t_ = r * np.tan(np.radians(np.clip(beta_, 0.0, 170.0)) / 2.0); t_mid = float(np.median(t_))
    def _border_at(f, J):
        best_ = None
        for kk in pch.get(f, []):
            if kk == k: continue
            for pe_ in _flat_e([ALL_E[kk]]):
                for v_ in (pe_.Vertexes[0], pe_.Vertexes[-1]):
                    dJ = np.linalg.norm(np.array([v_.X, v_.Y, v_.Z]) - J)
                    if dJ < 0.05 and (best_ is None or dJ < best_[0]): best_ = (dJ, kk, pe_)
        if best_ is None: raise RuntimeError("no border line of face %d leaves the junction at the end of line %d" % (f, k))
        return best_[1], best_[2]
    for f in sorted((p_, q_), key=lambda x_: 1 if x_ in SRCF else 0):
        n_loc = NL[f]
        D_ = np.cross(n_loc, T_); D_ /= np.maximum(np.linalg.norm(D_, axis=1), 1e-9)[:, None]
        dref_ = []
        for e_j, J in enumerate((J0, J1)):
            if SPLIT_END[e_j] or CHAIN_END[e_j] or str(e_j) in CHAIN_C or e_j in FREED: continue      # corner edge
            try:
                kk, pe_ = _border_at(f, J); Pe_ = samples(pe_, 0.05); far_ = Pe_[-1] if np.linalg.norm(Pe_[0] - J) < np.linalg.norm(Pe_[-1] - J) else Pe_[0]
                tJ2_ = T_[0] if J is J0 else T_[-1]; v_ = (far_ - J) - ((far_ - J) @ tJ2_) * tJ2_
                if np.linalg.norm(v_) > 1e-6: dref_.append(v_ / np.linalg.norm(v_))
            except Exception: pass
        m_ = len(S_) // 2
        try: _sd9, _nd9 = K.crease_side(Vu, F, pid, f, (q_ if f == p_ else p_), S_, D_)
        except Exception: _sd9, _nd9 = None, 0
        if f in SRCF: _sd9, _nd9 = None, 0
        _topo9 = (_sd9 is not None and abs(_sd9) >= 0.5)
        _vote9 = None; _dref9 = None
        try:
            Cf_, _Nf = _face_tri_normals(f)
            if f in SRCF and FID is not None:
                _Tb = F[pid == f]; _fb = FID[pid == f]; _ob = ~np.isin(_fb, list(BUR_)); _Tb = _Tb[_ob]
                _nb = np.cross(Vu[_Tb[:, 1]] - Vu[_Tb[:, 0]], Vu[_Tb[:, 2]] - Vu[_Tb[:, 0]]); _ab = np.linalg.norm(_nb, axis=1)
                if (_ab > 1e-9).sum() >= 3: Cf_ = Vu[_Tb[_ab > 1e-9]].mean(1)
            kdf_ = cKDTree(Cf_); kq_ = int(min(12, len(Cf_)))
            dq_, jq_ = kdf_.query(S_, k=kq_, workers=-1); dq_ = np.atleast_2d(dq_).reshape(len(S_), -1); jq_ = np.atleast_2d(jq_).reshape(len(S_), -1)
            vote_ = 0.0; nvote_ = 0
            for i_ in range(len(S_)):
                m2_ = (dq_[i_] < 3.0) & (dq_[i_] > 0.3)
                if m2_.any():
                    w_ = (Cf_[jq_[i_][m2_]] - S_[i_]) @ D_[i_]; vote_ += float(np.sign(w_).sum()); nvote_ += int(m2_.sum())
            if nvote_ >= 6 and abs(vote_) >= 0.5 * nvote_: _vote9 = (vote_ < 0)
            if f in SRCF: _vote9 = None
            if f in SRCF and FID is not None:
                try:
                    _Tbur = F[(pid == f) & np.isin(FID, list(BUR_))]
                    if len(_Tbur):
                        _Cb = Vu[_Tbur].mean(1); _mk = len(S_) // 2; _dvb = _Cb - S_[_mk]; _ddb = np.linalg.norm(_dvb, axis=1); _nb = _ddb < 3.0
                        if _nb.sum() >= 3:
                            _scb = float(np.mean(np.sign(_dvb[_nb] @ D_[_mk])))
                            if abs(_scb) >= 0.3:
                                _vote9 = (_scb > 0)
                                say("   fillet line %s: face %d's side AWAY FROM the buried face's %d triangles beside the crease (%+.2f; they are the blended body's own material side) (fix 11 / 31bq K)" % (k if leg_ is None else "%d leg %s" % (k, leg_), f, int(_nb.sum()), _scb))
                except Exception: pass
            if f in SRCF and _vote9 is None and len(Cf_) >= 3:
                _m5 = len(S_) // 2; _dv5 = Cf_ - S_[_m5]; _dd5 = np.linalg.norm(_dv5, axis=1); _w5 = 1.0 / (_dd5 + 0.5); _sc5 = float((np.sign(_dv5 @ D_[_m5]) * _w5).sum() / max(float(_w5.sum()), 1e-9))
                if abs(_sc5) >= 0.3:
                    _vote9 = (_sc5 < 0)
                    say("   fillet line %s: face %d's side from its %d unburied triangles (%+.2f, distance-weighted; the near mesh is the buried face's - fix 11 / 31bq B05)" % (k if leg_ is None else "%d leg %s" % (k, leg_), f, len(Cf_), _sc5))
            if dref_: _dref9 = (float(np.mean([d_r @ D_[m_] for d_r in dref_])) < 0)
        except Exception:
            if dref_:
                try: _dref9 = (float(np.mean([d_r @ D_[m_] for d_r in dref_])) < 0)
                except Exception: _dref9 = None
        if _topo9:
            _flip9 = bool(_sd9 < 0)
            _dis = [nm_ for nm_, v_ in (("the centroid vote", _vote9), ("the borders leaving the junctions", _dref9)) if v_ is not None and v_ != _flip9]
            if _dis or (_vote9 is None and os.environ.get("FIL_DBG") == "1"):
                say("   fillet line %s: face %d's side at the crease decided by the mesh's own triangles there (%d shared edge(s), %+.2f)%s" % (k if leg_ is None else "%d leg %s" % (k, leg_), f, _nd9, _sd9,
                    (" - %s would have put the offset on the OTHER side (fix 9b)" % " and ".join(_dis)) if _dis else (" - the centroid vote was undecided (%+.0f of %d)" % (vote_, nvote_) if _vote9 is None and nvote_ else "")))
            if _flip9: D_ = -D_
        elif _vote9 is not None:
            if _vote9: D_ = -D_
        elif _dref9: D_ = -D_
        if f in SRCF:
            _oth = q_ if f == p_ else p_
            if _oth in FO and _oth not in SRCF:
                try:
                    _so = float(np.mean(np.einsum("ij,ij->i", FO[_oth]["D"], NL[f]))); _sh = float(np.mean(np.einsum("ij,ij->i", D_, NL[_oth])))
                    if abs(_so) >= 0.3 and abs(_sh) >= 0.05 and _so * _sh < 0:
                        D_ = -D_
                        say("   fillet line %s: face %d's side turned to AGREE with face %d's own reading of the crease (%+.2f against %+.2f) - a crease has one sense; the buried-face rule / the votes had put the offset on the other side (31bq K)" % (k if leg_ is None else "%d leg %s" % (k, leg_), f, _oth, _so, _sh))
                except Exception: pass
        if kind[f] == "orig" and PJ[f].get("face") is not None and f not in SRCF:
            # ORIGINAL
            try:
                _Fo16 = BF[int(PJ[f]["face"])]; _So16 = _Fo16.Surface; _eps16 = max(0.2, 0.5 * float(t_[m_])); _ins16 = []
                for _sg16 in (1.0, -1.0):
                    _Px16 = S_[m_] + _sg16 * _eps16 * D_[m_]; _uu16, _vv16 = _So16.parameter(V3(*_Px16))
                    _ins16.append(bool(_Fo16.isPartOfDomain(_uu16, _vv16)) and float((_So16.value(_uu16, _vv16) - V3(*_Px16)).Length) < 0.5)
                if _ins16[1] and not _ins16[0]:
                    D_ = -D_
                    say("   fillet line %s: face %d's side at the crease set by its OWN B-rep face %d - the point %.2f mm on the offset's side lies outside it and the other side inside: the mesh / border reading had laid the offset BEYOND the crease (31bq R7W W2, F.16: a face's corner at a junction can be reflex - the border leaving it then lies on the other side)" % (k if leg_ is None else "%d leg %s" % (k, leg_), f, int(PJ[f]["face"]), _eps16))
                elif os.environ.get("FIL_DBG") == "1" and _ins16[0] == _ins16[1]: say("   fillet line %s: face %d's own B-rep face %d does not decide the side (both sides %s at %.2f mm) - the mesh reading stands (F.16)" % (k if leg_ is None else "%d leg %s" % (k, leg_), f, int(PJ[f]["face"]), "inside" if _ins16[0] else "outside", _eps16))
            except Exception as _exF16:
                if os.environ.get("FIL_DBG") == "1": say("   fillet line %s: face %d's own B-rep face could not be read for the side (%s) - the mesh reading stands (F.16)" % (k if leg_ is None else "%d leg %s" % (k, leg_), f, str(_exF16)[:80]))
        O_ = S_ + t_[:, None] * D_
        if (kind[f] == "orig" and PJ[f].get("face") is not None) or f in SRCF:
            try:
                S_o = BF[int(SRCF.get(f, PJ[f].get("face")))].Surface; prj_ = []
                for x_ in O_:
                    uu_, vv_ = S_o.parameter(V3(*x_)); pt_ = S_o.value(uu_, vv_); prj_.append([pt_.x, pt_.y, pt_.z])
                prj_ = np.array(prj_); say("   fillet line %d: the offset line on face %d laid on its %s surface %d (moved by %.3f mm at most)" % (k, f, "source" if f in SRCF else "original", int(SRCF.get(f, PJ[f].get("face"))), float(np.linalg.norm(prj_ - O_, axis=1).max()))); O_ = prj_
            except Exception as ex_o:
                raise RuntimeError("the offset line on original face %d could not be laid on its surface: %s" % (f, str(ex_o)[:80]))
        FO[f] = {"D": D_, "O": O_, "n_loc": n_loc}
    b_ = NL[p_] + NL[q_]; b_ /= np.maximum(np.linalg.norm(b_, axis=1), 1e-9)[:, None]
    beta = float(np.median(beta_))
    sag_ = r * (1.0 / np.maximum(np.cos(np.radians(beta_ / 2)), 0.2) - 1.0); sag = float(np.median(sag_))
    m_ = len(S_) // 2
    _sp = float(np.mean(np.einsum("ij,ij->i", FO[p_]["D"], NL[q_]))); _sq = float(np.mean(np.einsum("ij,ij->i", FO[q_]["D"], NL[p_]))); _sense = _sp + _sq
    def _turn_to_sense(convex_, whose_):
        """31bq HH (B05 (a)) / PP (B05 (3)(4)): the face whose own reading contradicts the sense taken has its offset on the wrong side - its D turned and its
        offset re-laid on its surface; a turn that fails is UNDONE (its D put back) and said"""
        for f__, s__ in ((p_, _sp), (q_, _sq)):
            if (s__ < 0) != (not convex_): continue
            _D0 = FO[f__]["D"].copy(); _O0 = FO[f__]["O"].copy()
            try:
                FO[f__]["D"] = -FO[f__]["D"]; _O2 = S_ + t_[:, None] * FO[f__]["D"]
                if (kind[f__] == "orig" and PJ[f__].get("face") is not None) or f__ in SRCF:
                    _Su = BF[int(SRCF.get(f__, PJ[f__].get("face")))].Surface; _pr2 = []
                    for x_ in _O2:
                        _uu2, _vv2 = _Su.parameter(V3(*x_)); _q2 = _Su.value(_uu2, _vv2); _pr2.append([_q2.x, _q2.y, _q2.z])
                    _O2 = np.array(_pr2)
                FO[f__]["O"] = _O2
                say("   fillet line %s: face %d's side TURNED to %s sense (its own reading %+.2f contradicted it) - the offset re-laid on its surface (31bq B05 (a))" % (k if leg_ is None else "%d leg %s" % (k, leg_), f__, whose_, s__))
            except Exception as _e5:
                FO[f__]["D"] = _D0; FO[f__]["O"] = _O0
                say("   fillet line %s: face %d's side could not be turned to %s sense (%s) - left as it was (31bq PP, B05 (4))" % (k if leg_ is None else "%d leg %s" % (k, leg_), f__, whose_, str(_e5)[:80]))
    _msc, _mne = K.crease_sense(Vu, F, pid, p_, q_, S_)
    if SRCF: _msc_m = _msc; _msc = None
    if _msc is not None and abs(_msc) >= 0.05: convex = _msc < 0; _how_s = "the mesh dihedral %.2f over %d edge(s)" % (_msc, _mne)
    elif SRCF and _sp * _sq > 0: convex = _sense < 0; _how_s = "both faces' sides from the source surface(s) %s (%.2f / %.2f; the mesh dihedral %s is the buried face's - fix 11)" % (sorted(set(SRCF.values())), _sp, _sq, "n/a" if _msc_m is None else "%.2f" % _msc_m)
    elif _sp * _sq > 0: convex = _sense < 0; _how_s = "both faces' sides (%.2f / %.2f; no mesh border within 0.5 mm of the line%s)" % (_sp, _sq, "" if _msc is None else ", its dihedral %.2f undecided" % _msc)
    else:
        _mo0 = f_.get("mirror_of"); _mfl0 = _master_fl(_mo0, leg_, J0, J1)
        if _mfl0 is not None and _mfl0.get("convex") is not None:
            convex = bool(_mfl0["convex"]); _how_s = "its master line %s's sense (the twin's own sides disagree: %.2f / %.2f - 31bq B05)" % (_mo0, _sp, _sq)
            _turn_to_sense(convex, "the master's")
        else: raise RuntimeError("line %d: CONVEX OR CONCAVE NOT DECIDED - the mesh holds %s between faces %d and %d along the drawn line, and the two faces' own sides disagree (%.2f / %.2f): the line lies off the mesh border or the corner is not one crease; decide the line on the border (or trace it), or drop the fillet"
                           % (k, ("no shared edge within 0.5 mm" if _msc is None else "a dihedral of %.2f (undecided) over %d edge(s)" % (_msc, _mne)), p_, q_, _sp, _sq))
    _mo = f_.get("mirror_of"); _mfl = _master_fl(_mo, leg_, J0, J1)
    if _mfl is not None and _mfl.get("convex") is not None and bool(_mfl.get("convex")) != bool(convex):
        _nmt_ = k if leg_ is None else "%d leg %s" % (k, leg_); _bm_ = float(_mfl.get("beta") or 0.0); _tm_ = float(_mfl.get("t") or 0.0)
        if abs(float(beta) - _bm_) > TWIN_BETA_TOL or abs(float(t_mid) - _tm_) > max(TWIN_T_TOL, 0.25 * _tm_):
            raise RuntimeError("line %s: ITS OWN SENSE IS DECIDED %s (%s) and contradicts its master line %s's %s - and its crease is NOT its master's mirror: %.0f deg / t %.2f mm against the master's %.0f deg / t %.2f mm (alike within %g deg / %g mm): the twin reads another crease beside its line than its master does - %s; the kit does not build a twin on its master's sense across another crease (31bq R7W, M3)"
                               % (_nmt_, "convex" if convex else "concave", _how_s, _mo, "convex" if _mfl["convex"] else "concave", float(beta), float(t_mid), _bm_, _tm_, TWIN_BETA_TOL, TWIN_T_TOL, _twin_cause(sorted(BUR_), _mfl.get("buried"), (p_, q_))))
        say("   fillet line %s: its sense reads %s (%.2f) while its master line %s reads %s - the master's sense is taken (a twin is its mirror: %.0f deg / t %.2f against the master's %.0f / %.2f)" % (k if leg_ is None else "%d leg %s" % (k, leg_), "convex" if convex else "concave", _sense, _mo, "convex" if _mfl["convex"] else "concave", float(beta), float(t_mid), _bm_, _tm_))
        convex = bool(_mfl["convex"]); _turn_to_sense(convex, "the master's")
    G_ = S_ + ((-sag_ if convex else sag_)[:, None]) * b_
    NARC = 9
    def _arc_row(A_, G_pt, B_):
        try:
            arc_ = Part.Arc(V3(*A_), V3(*G_pt), V3(*B_)).toShape()
            return np.array([[q.x, q.y, q.z] for q in arc_.discretize(Number=NARC)])
        except Exception:
            return np.linspace(np.asarray(A_, float), np.asarray(B_, float), NARC)
    def _sweep(G_s):
        rows = [_arc_row(FO[p_]["O"][i], G_s[i], FO[q_]["O"][i]) for i in range(len(S_))]
        if len(rows) < 4: raise RuntimeError("the crease is too short for a blend (%d arcs)" % len(rows))
        bs = Part.BSplineSurface(); bs.interpolate([[V3(*x) for x in row] for row in rows])
        u0, u1, v0, v1 = bs.bounds()
        isoc_ = {p_: bs.vIso(v0), q_: bs.vIso(v1)}; isoE_ = {f: c_.toShape() for f, c_ in isoc_.items()}
        isoU_ = {}; isoP_ = {}
        for f, c_ in isoc_.items():
            n_ = int(max(200, min(6000, c_.length() / 0.02 + 1))); isoU_[f] = np.linspace(u0, u1, n_); isoP_[f] = np.array([[q.x, q.y, q.z] for q in (c_.value(float(u)) for u in isoU_[f])])
        return rows, bs, (u0, u1, v0, v1), isoc_, isoE_, isoU_, isoP_
    CHAIN_SNAP = {}; NOREACH = {}; _SAID_NR = set()      # corner edge
    _cum = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(S_, axis=0), axis=1))])
    rows, bs, (u0, u1, v0, v1), isoc_, isoE_, isoU_, isoP_ = _sweep(G_)
    MEET = {p_: [None, None], q_: [None, None]}; UEND = {p_: [u0, u1], q_: [u0, u1]}; PEND = {p_: [FO[p_]["O"][0], FO[p_]["O"][-1]], q_: [FO[q_]["O"][0], FO[q_]["O"][-1]]}
    MEET_TOL = 0.15
    def _meet_pass():
        """where each offset line meets the border leaving the junction (within the sweep): cut there; a chain end on the side face meets the CORNER
        EDGE the same way (cut-cap: the end pole on it) - returns the chain ends whose offset does not reach it, with the shift that would"""
        short_ = {}
        for f in (p_, q_):
            MEET[f] = [None, None]; UEND[f] = [u0, u1]; PEND[f] = [FO[f]["O"][0], FO[f]["O"][-1]]
            for e_, J in enumerate((J0, J1)):
                if SPLIT_END[e_]: continue
                if CHAIN_END[e_]:
                    # corner edge
                    if f == CHAIN_A or str(e_) not in CHAIN_C or CHAIN_C[str(e_)].get("vertex"): continue
                    cc_ = CHAIN_C[str(e_)]; cedge_ = cc_["edge"]
                    if cc_.get("target") is not None:
                        tg_ = np.asarray(cc_["target"], float); dT_ = float(np.linalg.norm(tg_ - np.asarray(PEND[f][e_], float)))
                        MEET[f][e_] = {"chain": cc_.get("chain"), "split_face": cc_.get("split_face"), "piece_mid": cc_.get("piece_mid"), "at": tg_, "u": (u0, u1)[e_], "J": J, "piece": cedge_, "corner": True, "cut": False}
                        if dT_ > 1e-4: short_[(f, e_)] = tg_ - np.asarray(PEND[f][e_], float)
                        continue
                    try: dC_, ptsC_, _i = cedge_.distToShape(isoE_[f]); E_ = np.array([ptsC_[0][0].x, ptsC_[0][0].y, ptsC_[0][0].z])
                    except Exception: dC_, E_ = 9.0, np.asarray(PEND[f][e_], float)
                    dEnd_ = float(np.linalg.norm(E_ - np.asarray(PEND[f][e_], float)))
                    if dC_ <= MEET_TOL and np.linalg.norm(E_ - J) >= THIN_FIL:
                        uE_ = float(isoU_[f][int(np.argmin(np.linalg.norm(isoP_[f] - E_, axis=1)))])
                        cut_ = abs(uE_ - (u0, u1)[e_]) > 1e-6 and dEnd_ > 0.02
                        MEET[f][e_] = {"chain": cc_.get("chain"), "split_face": cc_.get("split_face"), "piece_mid": cc_.get("piece_mid"), "at": E_, "u": (uE_ if cut_ else (u0, u1)[e_]), "J": J, "piece": cedge_, "corner": True, "cut": cut_}
                        if cut_: UEND[f][e_] = uE_; PEND[f][e_] = E_
                        if os.environ.get("FIL_DBG") == "1": say("   fillet line %s: chain end %d on face %d - the offset line MEETS the corner edge %s %.2f mm before its end: the blend %s there" % (k if leg_ is None else "%d leg %s" % (k, leg_), e_, f, ("chain %s" % cc_.get("chain")) if cc_.get("chain") is not None else "(a split of face %s)" % cc_.get("split_face"), dEnd_, "cut" if cut_ else "ends"))
                    else:
                        try: dQ_, ptsQ_, _i = cedge_.distToShape(Part.Vertex(V3(*PEND[f][e_]))); Q2_ = np.array([ptsQ_[0][0].x, ptsQ_[0][0].y, ptsQ_[0][0].z])
                        except Exception: Q2_ = np.asarray(PEND[f][e_], float)
                        # corner edge
                        _ax_nr = np.asarray(cc_.get("axis") or [0.0, 0.0, 0.0], float); _Taway = T_[0] if e_ == 0 else -T_[-1]; _Dend = FO[f]["D"][0 if e_ == 0 else -1]
                        _dotD = float(_ax_nr @ _Dend) if np.linalg.norm(_ax_nr) > 1e-9 else 0.0; _gapJ = float(np.linalg.norm(Q2_ - J))
                        _angc = float(np.degrees(np.arctan2(_dotD, float(_ax_nr @ _Taway)))) % 360.0 if np.linalg.norm(_ax_nr) > 1e-9 else float("nan")
                        if _dotD < -0.2 or _gapJ < THIN_FIL:
                            NOREACH[int(e_)] = {"mm": round(float(np.linalg.norm(np.asarray(PEND[f][e_], float) - J)), 3), "deg": (None if np.isnan(_angc) else round(_angc, 1)), "face": int(f), "gap": round(_gapJ, 3), "dot": round(_dotD, 3)}
                            MEET[f][e_] = {"chain": cc_.get("chain"), "split_face": cc_.get("split_face"), "piece_mid": cc_.get("piece_mid"), "at": np.asarray(PEND[f][e_], float), "u": (u0, u1)[e_], "J": J, "piece": cedge_, "corner": True, "cut": False, "noreach": True}
                            if (f, e_) not in _SAID_NR:
                                _SAID_NR.add((f, e_))
                                say("   fillet line %s: chain end %d - the offset line on face %d CANNOT REACH the corner edge %s: the side face's corner at the junction is REFLEX - the corner edge leaves the junction at %s deg from the crease measured through the offset's side (axis . offset %+.2f; its nearest point to the offset's end is the junction itself, %.2f mm off) - the wall the ball leans on turns away past the junction; NOT turned onto the edge (the ramp had pinched the blend to nothing there and folded its surface); the end stands as swept, the chain assembly gives the junction up (31bq R7W W2)" % (
                                    k if leg_ is None else "%d leg %s" % (k, leg_), e_, f, ("chain %s" % cc_.get("chain")) if cc_.get("chain") is not None else "(a split of face %s)" % cc_.get("split_face"), "?" if np.isnan(_angc) else "%.0f" % _angc, _dotD, _gapJ))
                            continue
                        short_[(f, e_)] = Q2_ - np.asarray(PEND[f][e_], float)
                        MEET[f][e_] = {"chain": cc_.get("chain"), "split_face": cc_.get("split_face"), "piece_mid": cc_.get("piece_mid"), "at": Q2_, "u": (u0, u1)[e_], "J": J, "piece": cedge_, "corner": True, "cut": False}
                    continue
                try: kk, pe_ = _border_at(f, J)
                except Exception as ex_b: raise RuntimeError(str(ex_b))
                if kk >= len(CH): raise RuntimeError("the border line of face %d at the end of line %d is a wall edge - a fillet there would cut the body's own face (L114)" % (f, k))
                _mate_ = (f == CHAIN_A and kk in CHAIN_LINES and kk != k and str(e_) in CHAIN_C)
                if _mate_ and not any(int(v_.get("chain", -1)) == int(kk) and any(float(np.linalg.norm(np.asarray(Jv_, float) - J)) < 0.05 for Jv_ in (v_.get("J") or [])) for v_ in FIL_MERGE.values()):
                    if os.environ.get("FIL_DBG") == "1": say("   fillet line %s: on face %d the border leaving the junction %s is chain-mate %d's crease, but no made member of it ends there (dropped or failed) - a sharp border, met as a free end's (31bq R7W W2, R7Wj d)" % (k if leg_ is None else "%d leg %s" % (k, leg_), f, np.round(J, 1).tolist(), kk))
                    _mate_ = False
                if _mate_:
                    if os.environ.get("FIL_DBG") == "1": say("   fillet line %s: on face %d the border leaving the junction %s is chain-mate %d's crease - no border to cut (its blend's strip replaces it): the end tapers there (31bq R7W W2)" % (k if leg_ is None else "%d leg %s" % (k, leg_), f, np.round(J, 1).tolist(), kk))
                    continue
                d_, pts_, _i = pe_.distToShape(isoE_[f])
                if os.environ.get("FIL_DBG") == "1": say("   fillet line %d: on face %d the offset line %s the border %d leaving the junction %s (nearest %.3f mm%s)" % (k, f, "MEETS" if d_ <= MEET_TOL else "does not meet", kk, np.round(J, 1).tolist(), d_, (", %.2f mm from the junction" % np.linalg.norm(np.array([pts_[0][0].x, pts_[0][0].y, pts_[0][0].z]) - J)) if d_ <= MEET_TOL else ""))
                if d_ <= MEET_TOL:
                    E_ = np.array([pts_[0][0].x, pts_[0][0].y, pts_[0][0].z])
                    if np.linalg.norm(E_ - J) < THIN_FIL:
                        continue
                    uE_ = float(isoU_[f][int(np.argmin(np.linalg.norm(isoP_[f] - E_, axis=1)))])
                    MEET[f][e_] = {"chain": kk, "at": E_, "u": uE_, "J": J, "piece": pe_}; UEND[f][e_] = uE_; PEND[f][e_] = E_
        return short_
    short_rec = {}
    short_ = _meet_pass()
    if short_:
        # corner edge
        # corner edge
        # corner edge
        for (f, e_), sh_ in short_.items():
            if np.linalg.norm(sh_) < 1e-4: continue
            if (MEET[f][e_] or {}).get("corner") and str(e_) in CHAIN_C and CHAIN_C[str(e_)].get("target") is not None: continue
            short_rec[int(e_)] = max(short_rec.get(int(e_), 0.0), float(np.linalg.norm(sh_)))
            if _EXT.get(int(e_)): say("   fillet line %s: the sweep extended %.2f mm past the junction at end %d still falls %.2f mm short of the corner edge - the offset line is turned onto it about its far end on top (the ramp)" % (k if leg_ is None else "%d leg %s" % (k, leg_), _EXT[int(e_)], int(e_), float(np.linalg.norm(sh_))))
        # does not reach  corner edge
        for (f, e_), sh_ in short_.items():
            if np.linalg.norm(sh_) < 1e-4: continue
            # over the  corner edge
            Lr_ = float(_cum[-1]); dist_ = (_cum[-1] - _cum) if e_ == 1 else _cum
            w_ = np.clip(1.0 - dist_ / max(Lr_, 1e-6), 0.0, 1.0)
            FO[f]["O"] = FO[f]["O"] + w_[:, None] * sh_[None, :]; CHAIN_SNAP[(f, e_)] = (float(np.linalg.norm(sh_)), None)
            if os.environ.get("FIL_DBG") == "1": say("   fillet line %s: chain end %d - the offset line on face %d does not reach the corner edge (%.2f mm short): the offset line turned onto it about its far end (a linear ramp over the %.1f mm crease)" % (k if leg_ is None else "%d leg %s" % (k, leg_), e_, f, np.linalg.norm(sh_), Lr_))
        rows, bs, (u0, u1, v0, v1), isoc_, isoE_, isoU_, isoP_ = _sweep(G_)
        _meet_pass()
    # over the
    TAPER_ENDS = [e_ for e_ in (0, 1) if not CHAIN_END[e_] and not NO_TAPER[e_] and (SPLIT_END[e_] or (FIL_TAPER and (MEET[p_][e_] is None or MEET[q_][e_] is None)))]
    if any(NO_TAPER) and os.environ.get("FIL_DBG") == "1": say("   fillet line %s: shared junction(s) %s - swept at full R to it and CAPPED there (no taper): %s" % (k if leg_ is None else "%d leg %s" % (k, leg_), [e_ for e_ in (0, 1) if NO_TAPER[e_]], "; ".join("end %d: face %d %s" % (e_, f, ("cut-cap at its border %s" % MEET[f][e_]["chain"]) if MEET[f][e_] else "arc-cap, an end line to the junction") for e_ in (0, 1) if NO_TAPER[e_] for f in (p_, q_))))
    run_out_ = max(TAPER_X * t_mid, TAPER_MIN); w_t = np.ones(len(S_)); _ro_e = {int(e__): max(run_out_, TAPER_RUN.get(int(e__), 0.0)) for e__ in TAPER_ENDS}
    if TAPER_ENDS:
        w_t = (np.minimum.reduce([K.taper_weights(S_, _ro_e[int(e__)], ends=(int(e__),)) for e__ in TAPER_ENDS]) if any(abs(_ro_e[int(e__)] - run_out_) > 1e-9 for e__ in TAPER_ENDS) else K.taper_weights(S_, run_out_, ends=tuple(TAPER_ENDS))); w_s = np.maximum(w_t, 0.003)
        for f in (p_, q_):
            O_t = S_ + w_s[:, None] * (FO[f]["O"] - S_)
            if (kind[f] == "orig" and PJ[f].get("face") is not None) or f in SRCF:
                try:
                    S_o = BF[int(SRCF.get(f, PJ[f].get("face")))].Surface; prj_ = []
                    for i_, x_ in enumerate(O_t):
                        uu_, vv_ = S_o.parameter(V3(*x_)); pt_ = S_o.value(uu_, vv_); prj_.append([pt_.x, pt_.y, pt_.z])
                    O_t = np.array(prj_)
                except Exception: pass
            FO[f]["O"] = O_t
        G_ = S_ + w_s[:, None] * (G_ - S_); t_ = t_ * w_t
        rows, bs, (u0, u1, v0, v1), isoc_, isoE_, isoU_, isoP_ = _sweep(G_)
        for e_ in TAPER_ENDS:
            J = (J0, J1)[e_]; iu_ = 1 if e_ == 0 else bs.NbUPoles
            for jv_ in range(1, bs.NbVPoles + 1): bs.setPole(iu_, jv_, V3(*J))
        isoc_ = {p_: bs.vIso(v0), q_: bs.vIso(v1)}; isoE_ = {f: c_.toShape() for f, c_ in isoc_.items()}
        try: _meet_pass()
        except Exception as ex_mp: say("   fillet line %s: the meets could not be found again on the tapered surface (%s) - the untapered ends stand" % (k if leg_ is None else "%d leg %s" % (k, leg_), str(ex_mp)[:100]))
        for e_ in TAPER_ENDS:
            J = (J0, J1)[e_]
            for f in (p_, q_): MEET[f][e_] = None; UEND[f][e_] = (u0, u1)[e_]; PEND[f][e_] = np.asarray(J, float)
        say("   fillet line %s: the blend TAPERS to the junction at end(s) %s over %.1f mm (the radius to nothing there - no cap, the neighbours' borders uncut)%s%s"
            % (("%d leg %d" % (k, int(leg_))) if leg_ is not None else str(k), TAPER_ENDS, run_out_, (" - the crease (%.1f mm) is shorter than two run-outs: the full R is never reached (%.0f %% at most)" % (L_, 100 * float(w_t.max()))) if float(w_t.max()) < 0.999 else "",
               (" - end(s) %s are the split end on the crease: the corner stays a point" % [e_ for e_ in (0, 1) if SPLIT_END[e_]]) if any(SPLIT_END) else ""))
    if TAPER_ENDS and any(_ro_e[int(e__)] > run_out_ + 1e-9 for e__ in TAPER_ENDS):
        say("   fillet line %s: the taper at end(s) %s runs out over %s mm - from where the room ends, not the kit's %.1f (31bq R7W W2; L141: where the room ends, the radius ends with it)" % (k if leg_ is None else "%d leg %s" % (k, leg_), [int(e__) for e__ in TAPER_ENDS if _ro_e[int(e__)] > run_out_ + 1e-9], " / ".join("%.2f" % _ro_e[int(e__)] for e__ in TAPER_ENDS if _ro_e[int(e__)] > run_out_ + 1e-9), run_out_))
    for f in (p_, q_):
        if UEND[f][1] <= UEND[f][0] + 1e-6: raise RuntimeError("the offset line on face %d meets its end borders in the wrong order along the crease - the borders cross the strip (the face is narrower than t along the crease)" % f)
    # over the
    for f in (p_, q_):
        D_ = FO[f]["D"]; O_ = FO[f]["O"]
        cutk_ = {m_["chain"] for m_ in MEET[f] if m_ is not None and m_.get("chain") is not None}
        in_ = (((np.linalg.norm(S_ - J0, axis=1) > t_) & (np.linalg.norm(S_ - J1, axis=1) > t_)) if not f_.get("ends_too") else np.ones(len(S_), bool)) & core_; S_in = S_[in_] if in_.any() else S_      # ends_too
        Dn_ = D_[in_] if in_.any() else D_; tin_ = t_[in_] if in_.any() else t_; On_ = O_[in_] if in_.any() else O_; bin_ = beta_[in_] if in_.any() else beta_
        thn_ = (THIN_FIL * w_t)[in_] if in_.any() else THIN_FIL * w_t
        lam_ = np.linspace(0.0, 1.0, 7)[None, :, None]
        segs_ = (S_in[:, None, :] + lam_ * (On_ - S_in)[:, None, :]).reshape(-1, 3)
        worst_ = None; cross_ = None
        for kk in pch.get(f, []):
            if kk == k or kk in cutk_ or ALL_E[kk] is None: continue
            B_ = np.vstack([samples(x_, 0.2) for x_ in _flat_e([ALL_E[kk]])])
            touches_end_ = float(min(np.linalg.norm(B_ - J0, axis=1).min(), np.linalg.norm(B_ - J1, axis=1).min())) < 0.05
            dsb_ = np.linalg.norm(segs_[:, None, :] - B_[None, :, :], axis=2).min(1).reshape(len(S_in), -1)
            i_, l_ = np.unravel_index(int(np.argmin(dsb_ - thn_[:, None])), dsb_.shape); dmin_ = float(dsb_[i_, l_])
            if dmin_ < float(thn_[i_]) and not (touches_end_ and l_ == 0):
                jb_ = int(np.argmin(np.linalg.norm(B_ - S_in[i_], axis=1))); w_ = float(max(0.0, (B_[jb_] - S_in[i_]) @ Dn_[i_]))
                if cross_ is None or dmin_ < cross_[0]: cross_ = (dmin_, kk, S_in[i_], w_, float(tin_[i_]), float(bin_[i_]))
            if not touches_end_:
                dqi_ = np.linalg.norm(On_[:, None, :] - B_[None, :, :], axis=2).min(1); iq_ = int(np.argmin(dqi_ - thn_)); dq_ = float(dqi_[iq_])
                if dq_ < float(thn_[iq_]) and (worst_ is None or dq_ < worst_[0]): worst_ = (dq_, kk)
        if cross_ is not None:
            kk = cross_[1]; what_ = ("a wall edge of the edit region" if kk >= len(CH) else "its border %d (faces %s)" % (kk, CH[kk]["pair"]))
            r_fit = max(0.0, (cross_[3] - THIN_FIL) / max(np.tan(np.radians(min(cross_[5], 170.0)) / 2.0), 1e-6))
            _e_nr = _NoRoom("A FILLET NEEDS ROOM - R %g does not fit on face %d: a fillet of radius R touches each face t = R tan(beta/2) from the crease (beta the angle between the faces' normals; 90 deg -> t = R; here beta %.0f deg -> t = %.2f mm) and needs t + the print tolerance (%.2f) of face beside the crease; face %d has %.2f mm there before %s (at %s). EITHER make room - move that border (a hole's rim, a neighbour's border) or fill the gap so the face is at least %.2f mm wide beside the crease, as the design intends - OR lower R to %.2f at most. The kit measures; it does not choose"
                               % (r, f, cross_[5], cross_[4], THIN_FIL, f, cross_[3], what_, np.round(cross_[2], 1).tolist(), cross_[4] + THIN_FIL, r_fit)); _e_nr.at = np.asarray(cross_[2], float); raise _e_nr
        if worst_ is not None:
            kk = worst_[1]; what_ = ("a wall edge of the edit region" if kk >= len(CH) else "its border %d (faces %s)" % (kk, CH[kk]["pair"]))
            _e_nr = _NoRoom("A FILLET NEEDS ROOM - R %g does not fit on face %d: a fillet of radius R touches each face t = R tan(beta/2) from the crease (here t = %.2f mm) and needs t + the print tolerance (%.2f) of face beside the crease; its offset line runs within %.2f mm of %s. EITHER make room - move that border or fill the gap, as the design intends - OR lower R. The kit measures; it does not choose"
                               % (r, f, float(np.median(t_)), THIN_FIL, worst_[0], what_)); _e_nr.at = None; raise _e_nr
    if f_.get("check_only"): return {"width_ok": True}
    def _fit(P, A_, B_):
        cv_ = Part.BSplineCurve(); cv_.approximate(Points=[V3(*x) for x in P], DegMin=3, DegMax=3, Tolerance=1e-3, Continuity="C2")
        cv_.setPole(1, V3(*A_)); cv_.setPole(cv_.NbPoles, V3(*B_)); return cv_.toShape()
    def _iso_pts(f, vv, ua, ub):
        n_ = max(8, int((ub - ua) * len(S_) * 1.5) + 1)
        return np.array([[q.x, q.y, q.z] for q in (bs.value(float(u), float(vv)) for u in np.linspace(ua, ub, n_))])
    EOFF = {}
    for f, vv in ((p_, v0), (q_, v1)):
        if all(m_ is None or (m_.get("corner") and not m_.get("cut")) for m_ in MEET[f]): EOFF[f] = isoE_[f]
        else: EOFF[f] = _fit(_iso_pts(f, vv, UEND[f][0], UEND[f][1]), PEND[f][0], PEND[f][1])
    ENDC = []; ELS = {p_: [None, None], q_: [None, None]}; CAPS = [None, None]
    for e_, J in enumerate((J0, J1)):
        if e_ in TAPER_ENDS: ENDC.append(None); continue
        # corner edge
        _uncut = lambda m_: m_ is None or (m_.get("corner") and not m_.get("cut"))
        if _uncut(MEET[p_][e_]) and _uncut(MEET[q_][e_]): ca_ = bs.uIso((u0, u1)[e_])
        else:
            ua, ub = UEND[p_][e_], UEND[q_][e_]; n_ = 24
            P = np.array([[q.x, q.y, q.z] for q in (bs.value(float(ua + (ub - ua) * s_), float(v0 + (v1 - v0) * s_)) for s_ in np.linspace(0, 1, n_))])
            ca_ = Part.BSplineCurve(); ca_.approximate(Points=[V3(*x) for x in P], DegMin=3, DegMax=3, Tolerance=1e-3, Continuity="C2")
            ca_.setPole(1, V3(*PEND[p_][e_])); ca_.setPole(ca_.NbPoles, V3(*PEND[q_][e_]))
        ENDC.append(ca_.toShape())
        if CHAIN_END[e_]: continue
        cs_ = Part.BSplineSurface()
        cs_.buildFromPolesMultsKnots([[V3(*J)] * ca_.NbPoles, list(ca_.getPoles())], [2, 2], list(ca_.getMultiplicities()), [0.0, 1.0], list(ca_.getKnots()), False, False, 1, ca_.Degree)
        CAPS[e_] = cs_
        for f in (p_, q_):
            if MEET[f][e_] is None: ELS[f][e_] = Part.LineSegment(V3(*J), V3(*PEND[f][e_])).toShape()
    out = {p_: (EOFF[p_], [dict(face=p_, what="chain", chain=m_["chain"], at=[float(x) for x in m_["at"]], fillet=k) for m_ in MEET[p_] if m_ is not None and not m_.get("corner")], int(bs.NbUPoles), []),
           q_: (EOFF[q_], [dict(face=q_, what="chain", chain=m_["chain"], at=[float(x) for x in m_["at"]], fillet=k) for m_ in MEET[q_] if m_ is not None and not m_.get("corner")], int(bs.NbUPoles), [])}
    anc_ = {f: {tuple(np.round(J, 3)): PEND[f][e_] for e_, J in enumerate((J0, J1))} for f in (p_, q_)}
    return {"p": p_, "q": q_, "r": r, "lines": out, "guide": G_, "why": f_.get("why", ""), "convex": bool(convex), "chain": k, "extended": _EXT, "short": short_rec, "noreach": {int(k__): dict(v__) for k__, v__ in NOREACH.items()}, "buried": sorted(BUR_), "src_surface": dict(SRCF), "leg": (None if leg_ is None else int(leg_)), "name": (("%d leg %d" % (k, int(leg_))) if leg_ is not None else str(k)), "J": (J0, J1), "split_end": SPLIT_END, "sense": round(_sense, 3), "sense_how": _how_s, "mesh_sense": (None if _msc is None else round(_msc, 3)), "beta": round(float(beta), 1), "sag": round(float(sag), 3), "t": round(t_mid, 3),
            "surf": bs, "arcs": [(ENDC[0], J0), (ENDC[1], J1)], "caps": CAPS, "ends": ELS, "meet": MEET, "anchor": anc_[q_], "anchor_p": anc_[p_], "rows": len(rows), "npoles": (int(bs.NbUPoles), int(bs.NbVPoles)),
            "endkind": ["taper" if e_ in TAPER_ENDS else ("chain" if CHAIN_END[e_] else ("arc-cap" if (MEET[p_][e_] is None and MEET[q_][e_] is None) else "cut-cap")) for e_ in (0, 1)],
            "chain_end": CHAIN_END, "S": S_, "NL": {p_: NL[p_], q_: NL[q_]}, "T": T_, "bounds": (u0, u1, v0, v1), "PEND": {p_: [np.asarray(x_, float) for x_ in PEND[p_]], q_: [np.asarray(x_, float) for x_ in PEND[q_]]}, "ENDC": ENDC,
            "vertex_end": [bool((CHAIN_C.get(str(e_)) or CHAIN_C.get(e_) or {}).get("vertex")) for e_ in (0, 1)]}
def _leg_entries(f_):
    """31bp: the entries a _fillets record stands for - itself, or one per leg ("leg": "all" = every piece of the cut chain; <n> = that piece)"""
    k = int(f_["line"]); lg_ = f_.get("leg")
    if lg_ is None: return [f_]
    pcs_ = ALL_E[k] if (0 <= k < len(ALL_E) and isinstance(ALL_E[k], list)) else []
    if str(lg_).strip().lower() == "all": return [dict(f_, leg=i_) for i_ in range(len(pcs_))] or [dict(f_, leg=0)]
    return [dict(f_, leg=int(lg_))]
CHAINS = {}
def _crease_edge(f_):
    k_ = int(f_["line"]); lg_ = f_.get("leg")
    return ALL_E[k_][int(lg_)] if (lg_ is not None and isinstance(ALL_E[k_], list)) else NE[k_]
def _vpt(v): return np.array([v.X, v.Y, v.Z], float) if hasattr(v, "X") else np.array([v.x, v.y, v.z], float)
def _vx_id(fa__, fb__, J__):
    """31bq R7W merge-B26 (B26's latent seam, measure-B26's merge consequence 2): a VERTEX JUNCTION by its IDENTITY - its two members' names and its point -
    never their indices in the chain's fls list: the B04 (3) re-settle REBUILDS fls when it drops a member left with an OPEN end, and an index key written by
    the vertex pass then names another pair or none (the ball's junction fell to the corner as before - its members already cut back to the ball's station, c
    already swept from it, no sphere triangle)"""
    return (tuple(sorted((str(fa__.get("name")), str(fb__.get("name"))))), tuple(np.round(np.asarray(J__, float), 2)))
def _noreach_at(fx_, ex_):
    """31bq R7W W2 (R7Wj): the member's NOREACH record at end ex_ (the side offset cannot reach the corner edge there - the side face's corner at the junction is reflex),
    whichever key form the record holds; None otherwise"""
    nr_ = fx_.get("noreach") or {}
    v_ = nr_.get(int(ex_)) if nr_.get(int(ex_)) is not None else nr_.get(str(ex_))
    return v_
def _corner_edge_at(f, J, k_self):
    """31bp: the corner edge c leaving the junction J on face f - a border chain of f other than the crease (its piece ending at J), else a split of f ending
    there (a leg's apex: the split that cut the line); returns (kind, ref, edge) or None"""
    for kk in pch.get(f, []):
        if kk == k_self: continue
        for pe_ in _flat_e([ALL_E[kk]]):
            for v_ in (pe_.Vertexes[0], pe_.Vertexes[-1]):
                if np.linalg.norm(_vpt(v_) - J) < 0.05: return ("chain", kk, pe_)
    for sp_ in SPLITS.get(f, []):
        for se_ in _split_edges(sp_[1]):
            for v_ in (se_.Vertexes[0], se_.Vertexes[-1]):
                if np.linalg.norm(_vpt(v_) - J) < 0.05: return ("split", f, se_)
    return None
# >>> 31ca R5 F1 THE NO CORNER DECISION

def _nocorner_at(k_, kp_, turn_, kind_, sok_, turn_max_):
    """31ca (R5 F1): what the chain does at the junction of members k_ | kp_ - 'nocorner' (a far-side face boundary the crease runs through under the kit's corner definition: the chain is
    refused, 31bx K35), 'sharp_ok' (the same junction with EITHER member accepted sharp - never swept, 31bx X76: its chain-mates taper to the junction, no corner form is needed: the test
    is skipped, said) or None (a corner, or a split's apex - the agent's junction, L157)"""
    if kind_ != "chain" or not (turn_ < turn_max_): return None
    return "sharp_ok" if (int(k_) in sok_ or int(kp_) in sok_) else "nocorner"
# <<< 31ca R5 F1 THE NO CORNER DECISION
def _chain_members(record=True):
    """31bq QQ: record=False builds the entries only (no CHAINS entry, nothing printed) - the kernel stage's room check asks for a member's chain context.
    31bp: every fillet record as the entries the lines pass builds: single lines and legs as before; a chain's lines (and the legs of a line a split
    cut) ordered along the path, each told its chain ends (the junction it shares with the next member), the common face A, and per shared junction
    the corner edge c and the ball's contact Q0 on it (the same point for both members)"""
    out = []; by_ = {}
    for f0_ in FILLETS:
        if f0_.get("chain") is None: out += [(e_, None) for e_ in _leg_entries(f0_)]
        else: by_.setdefault(int(f0_["chain"]), []).append(f0_)
    for cid, ents in sorted(by_.items()):
        mem = []
        for e_ in sorted(ents, key=lambda x_: int(x_.get("pos", 0))):
            k_ = int(e_["line"]); mem += _leg_entries(dict(e_, leg="all") if isinstance(ALL_E[k_], list) else dict(e_))
        for m_ in mem:
            ce_ = _crease_edge(m_); m_["_ends"] = [_vpt(ce_.Vertexes[0]), _vpt(ce_.Vertexes[-1])]; m_["_edge"] = ce_
        common = set(int(x) for x in CH[int(mem[0]["line"])]["pair"])
        for m_ in mem[1:]: common &= set(int(x) for x in CH[int(m_["line"])]["pair"])
        if len(common) != 1:
            if record: say("FILLET CHAIN %d: its lines %s do not all border ONE face (%s) - a chain runs round a foot on one face; its lines are made as single blends" % (cid, [int(m_["line"]) for m_ in mem], sorted(common)))
            out += [(dict(m_, chain=None), None) for m_ in mem]; continue
        A = common.pop(); juncs = []; _nocorner = []
        _sok_nc = set(int(f_["line"]) for f_ in FILLETS if f_.get("sharp_ok") and str(f_.get("line", "")).lstrip("-").isdigit()) | set(int(m_["line"]) for m_ in mem if m_.get("sharp_ok")); _nc_said = []      
        for i_, m_ in enumerate(mem):
            ce = [False, False]; cc = {}
            for e_ in (0, 1):
                J = m_["_ends"][e_]; partner = None
                for j_, o_ in enumerate(mem):
                    if j_ == i_: continue
                    for x_ in (0, 1):
                        if np.linalg.norm(J - o_["_ends"][x_]) < 0.05: partner = (j_, x_)
                if partner is None: continue
                ce[e_] = True
                k_ = int(m_["line"]); side_ = [int(x) for x in CH[k_]["pair"] if int(x) != A]
                if not side_: continue
                corner_ = _corner_edge_at(side_[0], J, k_)
                if corner_ is None:
                    (say if record else (lambda *a__: None))("FILLET CHAIN %d: at the junction %s of lines %d and %d no corner edge leaves it on face %d - the two blends taper there as before" % (cid, np.round(J, 1).tolist(), k_, int(mem[partner[0]]["line"]), side_[0])); ce[e_] = False; continue
                kind_c, ref_c, pe_c = corner_
                Pc_ = samples(pe_c, 0.1); i0_ = int(np.argmin(np.linalg.norm(Pc_ - J, axis=1))); i1_ = min(len(Pc_) - 1, i0_ + 10) if i0_ < len(Pc_) // 2 else max(0, i0_ - 10)
                ax_ = Pc_[i1_] - Pc_[i0_]; ax_ /= max(np.linalg.norm(ax_), 1e-9)
                
                try:
                    _Pm = samples(m_["_edge"], 0.3); _tm = (_Pm[1] - _Pm[0]) if np.linalg.norm(_Pm[0] - J) < np.linalg.norm(_Pm[-1] - J) else (_Pm[-2] - _Pm[-1])
                    _Pp = samples(mem[partner[0]]["_edge"], 0.3); _tp = (_Pp[1] - _Pp[0]) if np.linalg.norm(_Pp[0] - J) < np.linalg.norm(_Pp[-1] - J) else (_Pp[-2] - _Pp[-1])
                    _turnJ = 180.0 - float(np.degrees(np.arccos(np.clip(float(_tm @ _tp) / max(np.linalg.norm(_tm) * np.linalg.norm(_tp), 1e-12), -1.0, 1.0))))
                except Exception: _turnJ = 180.0
                cc[str(e_)] = {"chain": (ref_c if kind_c == "chain" else None), "split_face": (ref_c if kind_c == "split" else None), "piece_mid": [float(x) for x in _vpt(pe_c.valueAt(0.5 * (pe_c.FirstParameter + pe_c.LastParameter)))], "axis": [float(x) for x in ax_], "edge": pe_c, "turn_deg": round(_turnJ, 1)}
                juncs.append({"J": [float(x) for x in J], "m": i_, "e": e_, "partner": partner, "axis": cc[str(e_)]["axis"], "side": side_[0], "turn_deg": cc[str(e_)]["turn_deg"]})
                _nc_ = _nocorner_at(k_, int(mem[partner[0]]["line"]), _turnJ, kind_c, _sok_nc, CREASE_TURN_MAX)      
                if record and _nc_ == "sharp_ok" and not any(t_ == (min(k_, int(mem[partner[0]]["line"])), max(k_, int(mem[partner[0]]["line"]))) for t_ in _nc_said):
                    _nc_said.append((min(k_, int(mem[partner[0]]["line"])), max(k_, int(mem[partner[0]]["line"]))))
                    say("FILLET CHAIN %d: the junction %s of lines %d | %d is no corner (the crease turns %.1f deg through the far side's face boundary) - a member there stands SHARP by your sharp_ok, so no corner form is needed: its chain-mates taper to it (31ca R5 F1; 31bx X76)" % (cid, np.round(J, 1).tolist(), k_, int(mem[partner[0]]["line"]), _turnJ))
                if record and _nc_ == "nocorner":      
                    try: _pside = int(next(x for x in CH[int(mem[partner[0]]["line"])]["pair"] if int(x) != A))
                    except Exception: _pside = -1
                    if not any(t_[0] == int(mem[partner[0]]["line"]) and t_[1] == k_ for t_ in _nocorner): _nocorner.append((k_, int(mem[partner[0]]["line"]), [round(float(x), 1) for x in J], float(_turnJ), int(side_[0]), _pside))
            m_["chain_ends"] = ce; m_["chain_common"] = A; m_["chain_c"] = cc; m_["chain_lines"] = sorted({int(x_["line"]) for x_ in mem})      
            out.append((m_, cid))
        if record and _nocorner:      
            K._fail("FAIL: fillet chain %d: %d junction(s) are NO CORNER - the crease runs through a face boundary on the far side turning under CREASE_TURN_MAX %g (the kit's corner definition): %s. A blend runs along ONE crease between corners: put those far-side faces in ONE feature (FEATURES - skin-features, then the layout, the network and the wires again) so the crease is one line and one blend, or accept the member that lies between the no-corner junctions sharp (\"sharp_ok\": [<line>] on the chain's entry) - its chain-mates taper to those junctions (31ca R5 F1). No corner form is built at such a junction (31bx K35: the one built there left a sliver no surface spans)"
                    % (cid, len(_nocorner), CREASE_TURN_MAX, "; ".join("lines %d | %d at %s turn %.1f deg (the far side's faces %d | %d)" % t_ for t_ in _nocorner)))
        if record: CHAINS[cid] = {"A": A, "members": mem, "keys": [], "junctions": juncs}
        if record: say("FILLET CHAIN %d (31bp): %d member(s) round face %d - %s; %d shared junction(s) get a corner patch (the crease turns %s deg at them, per member end - 31bx K35)" % (cid, len(mem), A, [("%d leg %s" % (int(m_["line"]), m_["leg"])) if m_.get("leg") is not None else str(int(m_["line"])) for m_ in mem], len({tuple(np.round(j_["J"], 2)) for j_ in juncs}), ", ".join("%.1f" % float(j_.get("turn_deg", 180.0)) for j_ in juncs) or "-"))
    return out

_KIT_SPLIT_RE = re.compile(r"\((?:fillet chain \d+, members? (?P<m>[^,)]+), by lines|fillet chain (?P<c>\d+) by lines|fillet R [\d.]+ on line (?P<l>\d+)(?: leg \d+)? by lines), from \[")
def _span_advice(why_):
    """31bq B44: the way out named by the failure - a split is advised only when the face's SHAPE failed; a failure that IS a split (its ends on no piece) or a
    fillet strip names that instead (fill4e: 'a split ... has its ends on no piece of the face ... split it with a wire')"""
    w_ = str(why_)
    if not _KIT_SPLIT_RE.search(w_):
        
        w_ = re.sub(r"a split \(.*?, from \[[^\]]*\] to \[[^\]]*\]\)", "a split (...)", w_, flags=re.S); w_ = re.sub(r"the split '[^']*'", "the split '...'", w_)
    if _KIT_SPLIT_RE.search(w_): return "a split the KIT made for a blend's strip has its ends on no piece of this face - that member's own offset line ends off the face's pieces: lower R on that member, or decide the line's end there (a junction); not a wire of yours (31bq B44; NN: tested before the generic split text, which its text also holds)"
    if "runs along a bridge" in w_: return "the split runs along a bridge of the hole (both its ends on the bridges' shared vertices): end it off those vertices, or drop it (31bq PP, B44 (3))"
    if "has its ends on no piece" in w_ or "are not both on one piece" in w_: return "the split named above does not fit the face's pieces: end it on a border vertex of THIS face (a junction or a split end), or drop it - another split will not help"
    if "strip" in w_ and "fillet" in w_: return "the fillet's strip is the failure - the split's end on its crease or the room beside it: move the split's end off the crease, lower R on that line, or drop the entry"
    if "folds" in w_ or "wraps" in w_ or "takes its loop" in w_ or "does not take its loop" in w_ or "sharpest corner" in w_: return "split it with a wire (skin-wires: a line of role split) where the fold or the sharp corner is"
    return "split it with a wire (skin-wires: a line of role split), or change the lines that bound it"
def _members_safe():
    try: return _chain_members()
    except Exception as ex_m:
        import traceback as _tb; _fr = _tb.extract_tb(sys.exc_info()[2])[-1]
        say("FILLET CHAINS: the chain pre-pass failed - %s (%s line %d); every fillet entry is made as a single blend" % (str(ex_m)[:300], os.path.basename(_fr.filename), _fr.lineno))
        return [(e_, None) for f0_ in FILLETS for e_ in _leg_entries(dict(f0_, leg=("all" if (isinstance(ALL_E[int(f0_["line"])], list) and f0_.get("chain") is not None) else f0_.get("leg"))))]
_CHK_MEM = None
def _check_members(line_k, leg_=None):
    """31bq QQ (HANDOVER 7 (b), fill18): the entries the width rule is asked about when the kernel's fillet failed on a CHAIN member - the member with its chain
    context (its shared junctions chain ends, the corner edge there the chain's contact: the lines pass measures it so); [] for a line in no chain"""
    global _CHK_MEM
    if _CHK_MEM is None:
        try: _CHK_MEM = [(m_, c_) for m_, c_ in _chain_members(record=False) if c_ is not None]
        except Exception as ex_cm:
            _CHK_MEM = []; say("   the chain context for the room check could not be built (%s) - a chain member's room is measured as a single line" % str(ex_cm)[:120])
    return [m_ for m_, c_ in _CHK_MEM if int(m_["line"]) == int(line_k) and (leg_ is None or m_.get("leg") is None or int(m_.get("leg")) == int(leg_))]
class _Uncut(RuntimeError):
    """31bq B01: a border a strip needs cut was not - raised, never printed as FAIL (the runner reads any FAIL line as the step's refusal)"""
class _NoRoom(RuntimeError):
    """31bq R7W W2 (R7Wj c): the width rule's refusal (A FILLET NEEDS ROOM) - .at is the crease sample where the room ends (None when the offset line alone ran too close to a border)"""
def _frags(kk, J, _nm="?"):
    """the piece(s) of border kk that touch junction J after the cut"""
    pcs_ = _flat_e([ALL_E[kk]]); got_ = []
    if len(pcs_) < 2: raise _Uncut("fillet line %s: the border %d was not cut at the strip's end - the offset line would end inside an uncut border" % (_nm, kk))      
    for pe_ in pcs_:
        P0_ = np.array([pe_.Vertexes[0].X, pe_.Vertexes[0].Y, pe_.Vertexes[0].Z]); P1_ = np.array([pe_.Vertexes[-1].X, pe_.Vertexes[-1].Y, pe_.Vertexes[-1].Z])
        if min(np.linalg.norm(P0_ - J), np.linalg.norm(P1_ - J)) < 0.05: got_.append(pe_)
    return got_
def _member_strips(fl, key_, _nm):
    """the strips of ONE blend on its two faces: [end line], the offset line (its pieces), [end line] - cut out of an original face, a split of a changed one"""
    J_ends = [np.asarray(fl["J"][0], float), np.asarray(fl["J"][1], float)]
    for f in (fl["p"], fl["q"]):
        chain_ = [x_ for x_ in ([fl["ends"][f][0]] + list(_flat_e([fl["lines"][f][0]])) + [fl["ends"][f][1]]) if x_ is not None]       
        frag_ = [pe_ for e_ in (0, 1) if fl["meet"][f][e_] is not None and fl["meet"][f][e_].get("chain") is not None for pe_ in _frags(int(fl["meet"][f][e_]["chain"]), J_ends[e_], _nm)]
        if kind[f] == "orig":
            strip_ = list(_flat_e([ALL_E[key_]])) + frag_; FIL_HOLD[(key_, f)] = strip_ + chain_      
            ORIG_FIL.setdefault(f, {"drop": [], "add": []}); ORIG_FIL[f]["drop"] += strip_; ORIG_FIL[f]["add"] += chain_
            ORIG_FIL_SRC.setdefault(f, []).extend(("the strip of fillet line %s" % _nm, x_) for x_ in chain_)      
            say("   fillet line %s: original face %d keeps its surface, trimmed by the offset line (%d edge(s) out, %d in)" % (_nm, f, len(strip_), len(chain_)))
        else:
            SPLITS.setdefault(f, []).append(({"role": "split", "kind": "CUBIC", "why": "fillet R %g on line %s by lines" % (fl["r"], _nm), "fillet": key_}, chain_ if len(chain_) > 1 else chain_[0]))
def _side_edges(fl, f, e_):
    """a blend end's edge(s) on face f from the junction to the offset end: the end line, or the cut fragment(s) of the border it met"""
    if fl["ends"][f][e_] is not None: return [fl["ends"][f][e_]]
    m_ = fl["meet"][f][e_]; J_ = np.asarray(fl["J"][e_], float); got_ = []
    if m_ is None or m_.get("chain") is None: return []
    for pe_ in _flat_e([ALL_E[int(m_["chain"])]]):
        P0_ = _vpt(pe_.Vertexes[0]); P1_ = _vpt(pe_.Vertexes[-1])
        if min(np.linalg.norm(P0_ - J_), np.linalg.norm(P1_ - J_)) < 0.05 and min(np.linalg.norm(P0_ - m_["at"]), np.linalg.norm(P1_ - m_["at"])) < 0.05: got_.append(pe_)
    return got_
def _apply_cuts(fl):
    """the borders a member's offset lines met are cut there (ALL_E)"""
    for f, (e_, cuts_, npol, whole_) in fl["lines"].items():
        for c_ in cuts_:
            if c_.get("chain") is None: continue
            kk = int(c_["chain"]); e0 = ALL_E[kk]
            if e0 is None: continue
            out_ = []; pcs_ = (e0 if isinstance(e0, list) else [e0]); _dd_ = []
            for pe_ in pcs_:      
                try: _dd_.append(float(pe_.distToShape(Part.Vertex(V3(*c_["at"])))[0]))
                except Exception: _dd_.append(9e9)
            _ib_ = int(np.argmin(_dd_)) if _dd_ else -1
            if _ib_ >= 0 and _dd_[_ib_] > 0.05: say("   fillet line %s: border %d stays UNCUT where the offset line meets it - the meet is %.2f mm from it (31bq B20 (3))" % (fl.get("name", "?"), kk, _dd_[_ib_]))
            for _jp_, pe_ in enumerate(pcs_):
                if _jp_ != _ib_ or _dd_[_ib_] > 0.05: out_.append(pe_); continue
                try:
                    prm_ = _prm_on(pe_, V3(*c_["at"])); lo_, hi_ = sorted((pe_.FirstParameter, pe_.LastParameter))
                    if not (lo_ < prm_ < hi_): out_.append(pe_); continue
                    w_ = pe_.split([prm_]); sub_ = [x_ for x_ in w_.Edges if x_.Length > 1e-4]; out_.extend(sub_ if len(sub_) == 2 else [pe_])
                except Exception as _exc3: out_.append(pe_); say("   fillet line %s: border %d could not be cut at the meet (%s)" % (fl.get("name", "?"), kk, str(_exc3)[:60]))
            ALL_E[kk] = out_ if len(out_) > 1 else out_[0]
if FIT == "span" and FILLET_LINES and FILLETS:
    _dups0 = _dup_entries(FILLETS)
    if _dups0: K._fail("FAIL: THE LINES PASS IS REFUSED before any sweep - skin\\fillets.json decides a crease in two entries: %s - one blend per crease (line, leg): decide each once and run skin-wires again (it refuses a line decided twice when it writes the file; this file was written before that rule, or by hand) (31bq R7W, M4)" % _dup_text(_dups0))
    _mem_all = list(_members_safe())
    _mem_all.sort(key=lambda fc_: (0 if fc_[0].get("mirror_of") is None else 1))
    
    _VERTEX_C = {}; _VERTEX_J = {}; _VX_SIDE = {}
    try:
        _singles = {int(f0_["line"]): f0_ for f0_ in FILLETS if f0_.get("chain") is None and f0_.get("leg") is None and str(f0_.get("line", "")).lstrip("-").isdigit()}
        for _cid0, _ch0 in CHAINS.items():
            _rc0 = sorted({round(float(m0_.get("r", 0)), 4) for m0_ in _ch0["members"]})
            for _j0 in _ch0.get("junctions", []):
                _m0 = _ch0["members"][_j0["m"]]; _c0 = (_m0.get("chain_c") or {}).get(str(_j0["e"])) or {}; _kc0 = _c0.get("chain")
                if _kc0 is None or int(_kc0) not in _singles: continue
                _e0 = _singles[int(_kc0)]
                if len(_rc0) == 1 and abs(float(_e0.get("r", 0)) - _rc0[0]) <= 0.01 * max(_rc0[0], 1e-9):
                    if int(_kc0) not in _VERTEX_C: _VERTEX_C[int(_kc0)] = {"cid": _cid0, "J": np.asarray(_j0["J"], float), "entry": _e0, "done": False,
                                                                          "members": sorted({int(_m0["line"])} | ({int(_ch0["members"][_j0["partner"][0]]["line"])} if _j0.get("partner") else set()))}      # 31br D1 (c)
                else: say("FILLET CHAIN %d: the corner edge %d at %s has its own fillet (R %s) but not the chain's R (%s) - no vertex ball there (the radii must match); it is made as a single blend and the corner is the mitre (31bq R7v)" % (_cid0, int(_kc0), np.round(_j0["J"], 1).tolist(), _e0.get("r"), _rc0))
    except Exception as _exv: say("the vertex-blend pre-pass failed (%s) - every fillet is made as before" % str(_exv)[:120]); _VERTEX_C = {}
    if _VERTEX_C: say("VERTEX BLENDS (31bq R7v, B26): %d corner edge(s) with a fillet of the chain's R - held for the chain assembly (the ball's station decides where each sweep stops): %s" % (len(_VERTEX_C), {int(k_): "chain %s" % v_["cid"] for k_, v_ in _VERTEX_C.items()}))
    for f_, _cid in _mem_all:      
        k = int(f_["line"])
        if k not in FILLET_LINES: continue
        _nm = ("%d leg %s" % (k, f_["leg"])) if f_.get("leg") is not None else str(k)
        if f_.get("sharp_ok"):      # recorded
            say("FILLET BY LINES on line %s: stands SHARP by your \"sharp_ok\" - never swept (31bx X76); its chain-mates end at its junctions as at an unmade member (the taper)" % _nm)
            FIL_NOT_MADE.setdefault(k, "stands SHARP by your sharp_ok (31bx X76) - not swept")
            if _cid is not None: CHAINS[_cid].setdefault("failed", []).append(f_)
            continue
        if _cid is None and k in _VERTEX_C and not f_.get("_vertex_pass"): continue      # corner edge
        try:
            fl = _fillet_lines(f_)
        except Exception as ex:
            if "NOT DECIDED" in str(ex) and f_.get("mirror_of") is None and not f_.get("_retry_g") and any(x_[0].get("mirror_of") is not None and int(x_[0]["mirror_of"]) == k for x_ in _mem_all):
                
                say("FILLET BY LINES on line %s: CONVEX OR CONCAVE NOT DECIDED as the master - tried again after its twin, taking the twin's sense if the twin decides (31bq B41 (g))" % _nm)
                _mem_all.append((dict(f_, _retry_g=True), _cid)); continue
            if f_.get("_retry_g"):      
                _tw_ = next((fl2_ for fl2_ in FIL_MERGE.values() if fl2_.get("convex") is not None and any(x_[0].get("mirror_of") is not None and int(x_[0]["mirror_of"]) == k and int(x_[0]["line"]) == int(fl2_.get("chain", -9)) for x_ in _mem_all)), None)
                if _tw_ is not None and "NOT DECIDED" in str(ex):
                    try:
                        fl = _fillet_lines(dict(f_, mirror_of=int(_tw_["chain"])))
                        say("   fillet line %s: the master takes its twin %s's sense (%s) - 31bq B41 (g)" % (_nm, _tw_["chain"], "convex" if fl["convex"] else "concave"))
                        if _cid is not None:      
                            for _m8 in CHAINS.get(_cid, {}).get("members", []):
                                if int(_m8["line"]) == k and _m8.get("leg") == f_.get("leg"): _m8["mirror_of"] = int(_tw_["chain"])
                        ex = None
                    except Exception as ex2: ex = ex2
            if ex is not None:
                import traceback as _tb; _fr = _tb.extract_tb(sys.exc_info()[2])[-1]
                say("FILLET BY LINES on line %s: not made - %s (%s line %d)" % (_nm, str(ex)[:1500], os.path.basename(_fr.filename), _fr.lineno))
                FIL_NOT_MADE.setdefault(k, str(ex)[:300])
                if _cid is not None: CHAINS[_cid].setdefault("failed", []).append(f_)      
                continue
        if fl.get("leg") is not None:      
            key_ = len(ALL_E); ALL_E.append(ALL_E[k][int(fl["leg"])])
        else: key_ = k
        fl["key"] = key_; fl["cid"] = _cid
        if _cid is not None: CHAINS[_cid]["keys"].append(key_)
        J_ends = [np.asarray(fl["J"][0], float), np.asarray(fl["J"][1], float)]
        _apply_cuts(fl)
        FIL_MERGE[key_] = fl
        say("FILLET BY LINES on line %s (R %g, faces %d | %d, %s crease by %s - %.0f deg between the normals, tangent distance t %.2f mm onto each face, sagitta %.2f): the blend is an arc of R swept along the crease (%d arcs -> one %d x %d-pole surface); its ends: %s"
            % (_nm, fl["r"], fl["p"], fl["q"], "convex" if fl["convex"] else "concave", fl.get("sense_how", "?"), fl["beta"], fl["t"], fl["sag"], fl["rows"], fl["npoles"][0], fl["npoles"][1],
               ", ".join("%s (%s)" % (fl["endkind"][e_], ("the split end on the crease - the corner stays a point" if fl["split_end"][e_] else "; ".join("face %d %s" % (f, (("its offset line to the corner edge %s" % ("chain %d" % fl["meet"][f][e_]["chain"] if fl["meet"][f][e_].get("chain") is not None else "(a split of face %s)" % fl["meet"][f][e_].get("split_face"))) if fl["meet"][f][e_].get("corner") else "cut at its border %d" % fl["meet"][f][e_]["chain"]) if fl["meet"][f][e_] else "an end line to the junction") for f in (fl["p"], fl["q"])))) for e_ in (0, 1))))
        if _cid is None:
            try: _member_strips(fl, key_, _nm)
            except _Uncut as ex_u:      
                FIL_MERGE.pop(key_, None); FIL_NOT_MADE.setdefault(k, str(ex_u)[:300]); say("FILLET BY LINES on line %s: not made - %s (sk_build.py %s)" % (_nm, str(ex_u), "the strip's border")); continue
def _sweep_declined(kk_, V_):
    """31br D1 (2026-10-29; d2: four corner edges left sharp): a corner edge's fillet HELD for a vertex ball that the junction test DECLINED is swept as a SINGLE blend at its decided R, here and
    now - before this chain's strips are built, as every single blend is swept before the chains (the flag `single` had been set on four paths and nothing read it). The corner is the mitre."""
    if V_.get("done") or V_.get("swept_single") or int(kk_) in FIL_MERGE or int(kk_) not in FILLET_LINES: return
    if not V_.get("_final"):      # 31br D1 (c)
        # _VERTEX_C
        V_["single"] = True; V_["declined"] = True; return
    V_["swept_single"] = True; f_ = dict(V_["entry"]); f_["_vertex_pass"] = True; _nm = str(int(kk_))
    try:
        
        # corner edge  kit measure
        _fillet_lines(dict(f_, check_only=True, ends_too=True))
    except _NoRoom as ex_w:
        _wy = "NOT made as a single blend after the declined ball - at the junction its side face is a WEDGE with no room for it: %s - lower R on it or make room (the chain member on that face says the same); the corner stays sharp (31br D1 (b))" % str(ex_w)[:400]
        FIL_NOT_MADE.setdefault(int(kk_), _wy); say("FILLET BY LINES on line %s: %s" % (_nm, _wy)); return
    except Exception as ex_w2:
        say("   the corner edge %s's width check at the junction could not run (%s) - the single blend is tried" % (_nm, str(ex_w2)[:120]))
    try:
        fl = _fillet_lines(f_)
    except Exception as ex:
        import traceback as _tb; _fr = _tb.extract_tb(sys.exc_info()[2])[-1]
        say("FILLET BY LINES on line %s: not made as the single blend after the declined ball - %s (%s line %d)" % (_nm, str(ex)[:1500], os.path.basename(_fr.filename), _fr.lineno)); FIL_NOT_MADE.setdefault(int(kk_), str(ex)[:300]); return
    key_ = int(kk_); fl["key"] = key_; fl["cid"] = None
    _apply_cuts(fl); FIL_MERGE[key_] = fl
    say("FILLET BY LINES on line %s (R %g, faces %d | %d, %s crease): the corner edge's fillet is made as a SINGLE blend at its decided R after the vertex ball was declined - the corner is the mitre, as for a corner edge of another R (31br D1)"
        % (_nm, fl["r"], fl["p"], fl["q"], "convex" if fl["convex"] else "concave"))
    try: _member_strips(fl, key_, _nm)
    except _Uncut as ex_u:
        FIL_MERGE.pop(key_, None); FIL_NOT_MADE.setdefault(int(kk_), str(ex_u)[:300]); say("FILLET BY LINES on line %s: not made - %s (sk_build.py %s)" % (_nm, str(ex_u), "the strip's border"))


def _ribbon_ok(S_plain, S_rib, kind_r, n_=7):
    """31bp fix 8: the fill through the tangent ribbon against the plain fill of the same piece - taken only when it is a NURBS fill whose bounding box
    grows by no more than max(2 mm, 3 x RIBBON_MM) and whose surface lies within max(1 mm, 3 x RIBBON_MM) of the plain one at n_ x n_ sample points;
    returns (ok, why)"""
    try:
        if kind_r != "nurbs": return False, "the fill through the ribbon is a %s, not a NURBS fill" % kind_r
        grow_ = max(2.0, 3.0 * RIBBON_MM); near_ = max(1.0, 3.0 * RIBBON_MM)
        fp_ = Part.Face(S_plain); fr_ = Part.Face(S_rib); bp_, br_ = fp_.BoundBox, fr_.BoundBox
        over_ = max(bp_.XMin - br_.XMin, br_.XMax - bp_.XMax, bp_.YMin - br_.YMin, br_.YMax - bp_.YMax, bp_.ZMin - br_.ZMin, br_.ZMax - bp_.ZMax)
        if over_ > grow_: return False, "it left the plain fill's envelope by %.1f mm (allowed %.1f)" % (over_, grow_)
        u0_, u1_, v0_, v1_ = S_rib.bounds(); worst_ = 0.0
        for iu_ in range(n_):
            for iv_ in range(n_):
                q_ = S_rib.value(u0_ + (u1_ - u0_) * (iu_ + 0.5) / n_, v0_ + (v1_ - v0_) * (iv_ + 0.5) / n_)
                worst_ = max(worst_, float(fp_.distToShape(Part.Vertex(q_))[0]))
                if worst_ > near_: return False, "it stands %.2f mm off the plain fill (allowed %.2f)" % (worst_, near_)
        return True, "within %.2f mm of the plain fill, its envelope grown %.2f mm" % (worst_, max(0.0, over_))
    except Exception as ex_k:
        return False, "the acceptance could not be measured: %s" % str(ex_k)[:80]
RIBBONS = {}      
if FIT == "span" and FIL_MERGE and RIBBON_MM > 0:
    for k_f, fl in FIL_MERGE.items():
        try:
            bs_ = fl["surf"]; G_ = np.asarray(fl["guide"], float)
            for f in (fl["p"], fl["q"]):
                if kind[f] != "changed": continue
                oe_ = _flat_e([fl["lines"][f][0]]); pts_ = []
                for pe_ in oe_:
                    n_ = max(2, int(pe_.Length / RIBBON_STEP) + 1); lo_, hi_ = pe_.FirstParameter, pe_.LastParameter
                    for i_ in range(n_ + 1):
                        u_ = lo_ + (hi_ - lo_) * (i_ + 0.5) / (n_ + 1)
                        q_ = pe_.valueAt(u_); tq_ = pe_.tangentAt(u_); p_ = np.array([q_.x, q_.y, q_.z]); T_ = np.array([tq_.x, tq_.y, tq_.z]); T_ /= max(np.linalg.norm(T_), 1e-9)
                        try:
                            uu_, vv_ = bs_.parameter(q_); nb_ = bs_.normal(uu_, vv_); nB_ = np.array([nb_.x, nb_.y, nb_.z])
                        except Exception: continue
                        if np.linalg.norm(nB_) < 0.5: continue           
                        c_ = np.cross(nB_, T_); nc_ = np.linalg.norm(c_)
                        if nc_ < 0.3: continue
                        c_ /= nc_
                        g_ = G_[int(np.argmin(np.linalg.norm(G_ - p_, axis=1)))]
                        if float(c_ @ (p_ - g_)) < 0: c_ = -c_             
                        pts_.append(p_ + RIBBON_MM * c_)
                if len(pts_) >= 2: RIBBONS.setdefault(f, []).append((np.array(pts_), oe_))
        except Exception as ex_r: say("   ribbon of fillet %s: not laid (%s)" % (fl.get("name", k_f), str(ex_r)[:80]))
    if RIBBONS: say("TANGENT RIBBONS (31bp): %d row(s) of points %.2f mm inside %d changed face(s) beside a blend, on the blend's tangent plane - the fill runs out of the blend tangent" % (sum(len(v) for v in RIBBONS.values()), RIBBON_MM, len(RIBBONS)))
# THE CHAIN ASSEMBLY
# corner edge
# corner edge

for _cid, _ch in CHAINS.items():      
    for f_h in _ch.get("failed", []):
        for Jh in f_h.get("_ends", []):
            for m_ in _ch["members"]:
                if m_ is f_h or not m_.get("chain_ends"): continue
                for e_ in (0, 1):
                    if m_["chain_ends"][e_] and np.linalg.norm(np.asarray(m_["_ends"][e_]) - np.asarray(Jh)) < 0.05:
                        m_["chain_ends"][e_] = False
                        key_h = next((k_ for k_, fl_ in FIL_MERGE.items() if fl_.get("cid") == _cid and fl_.get("name") == (("%d leg %s" % (int(m_["line"]), m_["leg"])) if m_.get("leg") is not None else str(int(m_["line"])))), None)
                        if key_h is None: continue
                        try:
                            fl_h = _fillet_lines(m_); fl_h["key"] = key_h; fl_h["cid"] = _cid; _apply_cuts(fl_h); FIL_MERGE[key_h] = fl_h
                            say("   fillet chain %d: member %s swept again with its end at %s FREE (the taper) - its neighbour %s there was not made" % (_cid, fl_h.get("name"), np.round(Jh, 1).tolist(), ("%d leg %s" % (int(f_h["line"]), f_h["leg"])) if f_h.get("leg") is not None else str(int(f_h["line"]))))
                        except Exception as ex_h:
                            say("   fillet chain %d: member %s could not be swept again with a free end at %s - %s; it stands as first swept (an OPEN end)" % (_cid, m_.get("line"), np.round(Jh, 1).tolist(), str(ex_h)[:1500]))
PIVOTS = []        
_BAL_KEYS = ("balloon_mm", "balloon_note", "balloon_unmeasured", "balloon_tess")
_SPANC_BAL = {}
def _span_corner(eds_, name_, fallback_=None, rim_tol=None):
    """a corner face spanned by the kit's own ladder through its edges (NURBS fill -> Coons -> plate, the rim checked - within rim_tol when given); the
    given fallback surface when the ladder refuses; returns (surface, how). 31bq R5g (round 5's C6, B17 (1)): the ladder's rise record is left in _SPANC_BAL for
    the caller's record (a corner face's rise had reached no record and no summary), and its progress is said"""
    global _SPANC_BAL
    _SPANC_BAL = {}
    try:
        kind_c, payload_c, info_c = SP.span_face(SP.edge_polys(list(eds_)), [], CORNER_DEG, SPAN_STEP, vox_normals=None, progress=(lambda m_: say("   %s: %s" % (name_, m_))), nurbs=None, rim_tol=rim_tol)
        _SPANC_BAL = {k_: info_c.get(k_) for k_ in _BAL_KEYS if info_c.get(k_) is not None}
        return SP.surface_of(kind_c, payload_c), "%s (%s)" % (kind_c, str(info_c.get("how", ""))[:60])
    except Exception as ex_c:
        say("   %s: the span ladder refused its %d edge(s) - %s; %s" % (name_, len(eds_), str(ex_c)[:100], "the Coons blend through them stands" if fallback_ is not None else "NO face"))
        return fallback_, "coons blend (the ladder refused)"
_CUT_WHY = {}      # did not happen
def _cut_chain_at(kk, at_, tol=0.05):
    """chain kk cut at the point: the piece the point lies on (the kernel's nearest point, distToShape) split at that parameter; a point within tol of
    a piece's end is that end (True, nothing to cut); False when no piece passes within tol - the reason kept in _CUT_WHY"""
    e0 = ALL_E[kk]
    if e0 is None: _CUT_WHY[kk] = "no edge"; return False
    pcs_ = e0 if isinstance(e0, list) else [e0]; best_ = None
    for i_, pe_ in enumerate(pcs_):
        try:
            d_, pts_, inf_ = pe_.distToShape(Part.Vertex(V3(*at_)))
            if best_ is None or d_ < best_[0]: best_ = (float(d_), i_, pe_, inf_)
        except Exception: continue
    if best_ is None or best_[0] > tol:
        _CUT_WHY[kk] = "no piece of it passes within %.2f mm of the point (nearest %.3f mm)" % (tol, best_[0] if best_ else 9.0); return False
    d_, i_, pe_, inf_ = best_
    try:
        prm_ = None
        for rec_ in inf_:
            if rec_[0] == "Edge": prm_ = float(rec_[2]); break
        if prm_ is None: prm_ = float(pe_.Curve.parameter(V3(*at_)))
        lo_, hi_ = sorted((pe_.FirstParameter, pe_.LastParameter))
        if min(np.linalg.norm(_vpt(v_) - np.asarray(at_, float)) for v_ in (pe_.Vertexes[0], pe_.Vertexes[-1])) <= tol: return True      
        if not (lo_ < prm_ < hi_): _CUT_WHY[kk] = "the nearest point's parameter %.4f is outside the piece (%.4f..%.4f)" % (prm_, lo_, hi_); return False
        w_ = pe_.split([prm_]); sub_ = [x_ for x_ in w_.Edges if x_.Length > 1e-4]
        if len(sub_) != 2: _CUT_WHY[kk] = "the split gave %d piece(s)" % len(sub_); return False
        out_ = list(pcs_[:i_]) + sub_ + list(pcs_[i_ + 1:]); ALL_E[kk] = out_ if len(out_) > 1 else out_[0]; return True
    except Exception as ex_c:
        _CUT_WHY[kk] = "the split raised %s" % str(ex_c)[:60]; return False
def _cut_split_at(sf_, pm_, at_, tol=0.05):
    """a split of face sf_ cut at the point: the piece of ANY split of the face nearest the point (within tol) is split there (the kernel's nearest
    point); a point within tol of a piece's end is that end already (True). pm_ (the piece's midpoint when the corner was found) is a hint only"""
    at_ = np.asarray(at_, float); best_ = None
    for si2_, sp2_ in enumerate(SPLITS.get(int(sf_), [])):
        for pi2_, pe_ in enumerate(_split_edges(sp2_[1])):
            try: d_, pts_, inf_ = pe_.distToShape(Part.Vertex(V3(*at_)))
            except Exception: continue
            if best_ is None or d_ < best_[0]: best_ = (float(d_), si2_, pi2_, pe_, inf_)
    if best_ is None or best_[0] > tol: return False
    d_, si2_, pi2_, pe_, inf_ = best_
    if min(np.linalg.norm(_vpt(v_) - at_) for v_ in (pe_.Vertexes[0], pe_.Vertexes[-1])) <= tol: return True
    try:
        prm_ = next((float(r_[2]) for r_ in inf_ if r_[0] == "Edge"), None)
        if prm_ is None: prm_ = float(pe_.Curve.parameter(V3(*at_)))
        lo_, hi_ = sorted((pe_.FirstParameter, pe_.LastParameter))
        if not (lo_ < prm_ < hi_): return False
        w_ = pe_.split([prm_]); sub_ = [x_ for x_ in w_.Edges if x_.Length > 1e-4]
        if len(sub_) != 2: return False
        pcs2_ = _split_edges(SPLITS[int(sf_)][si2_][1]); new2_ = list(pcs2_[:pi2_]) + sub_ + list(pcs2_[pi2_ + 1:])
        SPLITS[int(sf_)][si2_] = (SPLITS[int(sf_)][si2_][0], new2_); return True
    except Exception: return False
def _pieces_to(kk, J, Qp, tol=0.05):
    """the pieces of chain kk from the junction J up to the point Qp (a vertex of its pieces), in order; [] when Qp is at J"""
    pcs_ = _flat_e([ALL_E[kk]]); out_ = []; cur_ = np.asarray(J, float); used_ = set()
    for _ in range(len(pcs_)):
        if np.linalg.norm(cur_ - np.asarray(Qp, float)) < tol: break
        nxt_ = None
        for pe_ in pcs_:
            if pe_.hashCode() in used_: continue
            v0_, v1_ = _vpt(pe_.Vertexes[0]), _vpt(pe_.Vertexes[-1])
            if np.linalg.norm(v0_ - cur_) < tol: nxt_ = (pe_, v1_); break
            if np.linalg.norm(v1_ - cur_) < tol: nxt_ = (pe_, v0_); break
        if nxt_ is None: break
        out_.append(nxt_[0]); used_.add(nxt_[0].hashCode()); cur_ = nxt_[1]
    return out_
def _cut_chain_once(kk, at_, tol=0.05):
    """the chain cut at the point unless a piece already ends there; True when a vertex is there afterwards"""
    for pe_ in _flat_e([ALL_E[kk]]):
        for v_ in (pe_.Vertexes[0], pe_.Vertexes[-1]):
            if np.linalg.norm(_vpt(v_) - np.asarray(at_, float)) < tol: return True
    return _cut_chain_at(kk, at_)
def _crease_path(pa_, pb_, kks_, cut=True, tol=0.05, only=None):
    """31bq QQ (B04 (2)): the crease pieces of the lines kks_ from pa_ to pb_, in order - a point inside a piece cut into its line first (both faces keep sharing
    the pieces; cut=False takes whole pieces only), each piece by the kernel's distance within its OWN bounds (Curve.parameter on a straight crease had taken any
    collinear point beyond the edge), the path through the pieces' shared vertices (a hole of several ADJACENT members: one crease after the next); [] when none"""
    pa_ = np.asarray(pa_, float); pb_ = np.asarray(pb_, float)
    if float(np.linalg.norm(pa_ - pb_)) < 1e-6: return []
    if cut:
        for P_ in (pa_, pb_):
            for kk in kks_:
                if not (0 <= kk < len(ALL_E)) or ALL_E[kk] is None: continue
                try:
                    if min(float(pe_.distToShape(Part.Vertex(V3(*P_)))[0]) for pe_ in _flat_e([ALL_E[kk]])) <= tol: _cut_chain_once(kk, P_, tol)
                except Exception: pass
    pcs_ = [pe_ for kk in kks_ if 0 <= kk < len(ALL_E) and ALL_E[kk] is not None for pe_ in _flat_e([ALL_E[kk]]) if pe_.Length > 1e-6]
    if only:      
        def _on_(pe_):
            try: m_ = pe_.valueAt(0.5 * (pe_.FirstParameter + pe_.LastParameter)); return any(float(o_.distToShape(Part.Vertex(m_))[0]) <= tol for o_ in only)
            except Exception: return False
        pcs_ = [pe_ for pe_ in pcs_ if _on_(pe_)]
    nodes_ = []
    def _node(P_):
        for i_, Q_ in enumerate(nodes_):
            if float(np.linalg.norm(Q_ - P_)) < tol: return i_
        nodes_.append(np.asarray(P_, float)); return len(nodes_) - 1
    adj_ = {}
    for j_, pe_ in enumerate(pcs_):
        a_ = _node(_vpt(pe_.Vertexes[0])); b_ = _node(_vpt(pe_.Vertexes[-1]))
        if a_ == b_: continue
        adj_.setdefault(a_, []).append((b_, j_)); adj_.setdefault(b_, []).append((a_, j_))
    s_ = next((i_ for i_, Q_ in enumerate(nodes_) if float(np.linalg.norm(Q_ - pa_)) < tol), None); g_ = next((i_ for i_, Q_ in enumerate(nodes_) if float(np.linalg.norm(Q_ - pb_)) < tol), None)
    if s_ is None or g_ is None: return []
    prev_ = {s_: None}; queue_ = [s_]
    while queue_:
        u_ = queue_.pop(0)
        if u_ == g_: break
        for v_, j_ in adj_.get(u_, []):
            if v_ not in prev_: prev_[v_] = (u_, j_); queue_.append(v_)
    if g_ not in prev_: return []
    path_ = []; v_ = g_
    while prev_[v_] is not None:
        u_, j_ = prev_[v_]; path_.append(pcs_[j_]); v_ = u_
    return path_[::-1]
def _seg_off_face(e_, f_):
    """31bq R6 / R7W (B04 (3)): how far an edge runs from face f_ - (against the face's OWN source-mesh triangles, its trimmed region; against a kept face's original
    surface, a second reading) in mm; a reading that cannot be taken is None - NOT MEASURED, never read as 0 (the R6 form read a kept face's UNTRIMMED surface: a
    chord across a hole or a reflex corner of a planar face read 0.000 and was laid)"""
    try:
        n_ = max(9, int(e_.Length / 0.5) + 1); P_ = [e_.valueAt(e_.FirstParameter + (e_.LastParameter - e_.FirstParameter) * t_) for t_ in np.linspace(0.0, 1.0, n_)]
    except Exception: return None, None
    dm_ = ds_ = None
    try:
        T_ = F[pid == f_]
        if len(T_):
            _q_, d_ = K.closest_on_mesh(np.array([[q_.x, q_.y, q_.z] for q_ in P_]), Vu, T_); dm_ = float(np.max(d_))
            if not getattr(K, "CLOSEST_LAST", {}).get("exact", True) and dm_ > THIN_FIL: dm_ = None      # over the
    except Exception: dm_ = None
    try:
        if kind[f_] == "orig" and PJ[f_].get("face") is not None:
            S_ = BF[int(PJ[f_]["face"])].Surface; ds_ = float(max((S_.value(*S_.parameter(q_)) - q_).Length for q_ in P_))
    except Exception: ds_ = None
    return dm_, ds_
def _set_line(fl_, f, edge_):
    fl_["lines"][f] = (edge_,) + tuple(fl_["lines"][f][1:])
def _nearest_on(edges_, X_):
    """the point of the edges nearest X and the edge it is on"""
    best_ = None
    for pe_ in edges_:
        d_, pts_, _i = pe_.distToShape(Part.Vertex(V3(*X_)))
        if best_ is None or d_ < best_[0]: best_ = (d_, np.array([pts_[0][0].x, pts_[0][0].y, pts_[0][0].z]), pe_)
    return best_
def _end_vertex(edges_, near_):
    """the end vertex of the edges nearest the point near_ (the exact point a shared edge must start from)"""
    vs_ = [_vpt(v_) for e_ in edges_ for v_ in (e_.Vertexes[0], e_.Vertexes[-1])]
    return vs_[int(np.argmin([np.linalg.norm(v_ - np.asarray(near_, float)) for v_ in vs_]))]
def _cut_line_at(fl_, f, X_, away_from, snap_to=None):
    """the member's offset line on face f cut at X (a point ON it), the piece towards away_from dropped, the kept piece's cut end re-fitted onto
    snap_to when given; returns the kept pieces"""
    pcs_ = _flat_e([fl_["lines"][f][0]]); new_ = []; cut_ = False; X_ = np.asarray(X_, float)
    at_end_ = [i_ for i_, pe_ in enumerate(pcs_) if min(np.linalg.norm(_vpt(v_) - X_) for v_ in (pe_.Vertexes[0], pe_.Vertexes[-1])) <= 0.05]
    if at_end_:
        
        if snap_to is not None and np.linalg.norm(np.asarray(snap_to, float) - X_) > 1e-7:
            new_ = [VX.refit_end(pe_, _end_vertex([pe_], X_), snap_to) if i_ in at_end_ else pe_ for i_, pe_ in enumerate(pcs_)]
            _set_line(fl_, f, new_ if len(new_) > 1 else new_[0]); return new_
        return pcs_
    for pe_ in pcs_:
        try:
            prm_ = pe_.Curve.parameter(V3(*X_)); lo_, hi_ = sorted((pe_.FirstParameter, pe_.LastParameter))
            if lo_ + 1e-6 < prm_ < hi_ - 1e-6 and pe_.valueAt(prm_).distanceToPoint(V3(*X_)) <= 0.05:
                w_ = pe_.split([prm_]); sub_ = [x_ for x_ in w_.Edges if x_.Length > 1e-4]
                keep_ = [s_ for s_ in sub_ if min(np.linalg.norm(_vpt(v_) - away_from) for v_ in (s_.Vertexes[0], s_.Vertexes[-1])) > 0.05]
                if keep_ and snap_to is not None and np.linalg.norm(np.asarray(snap_to, float) - X_) > 1e-7:
                    keep_ = [VX.refit_end(k_, _end_vertex([k_], X_), snap_to) if min(np.linalg.norm(_vpt(v_) - X_) for v_ in (k_.Vertexes[0], k_.Vertexes[-1])) < 0.05 else k_ for k_ in keep_]
                if keep_: new_ += keep_; cut_ = True; continue
        except Exception: pass
        new_.append(pe_)
    if not cut_: say("   fillet chain: member %s's offset line on face %d was NOT cut at X %s (no piece passes within 0.05 mm of it: nearest %.3f mm) - the strip may cross itself there" % (fl_.get("name"), f, np.round(X_, 2).tolist(), min(pe_.distToShape(Part.Vertex(V3(*X_)))[0] for pe_ in pcs_)))
    _set_line(fl_, f, new_ if len(new_) > 1 else new_[0]); return new_
for _cid, _ch in CHAINS.items():
    try:
        A = _ch["A"]; fls = [FIL_MERGE[k_] for k_ in _ch["keys"] if k_ in FIL_MERGE]
        if len(fls) < 2: say("FILLET CHAIN %d: only %d of its %d members were made - no corner patch; the members stand as single blends" % (_cid, len(fls), len(_ch["members"])))
        # THE EXTEND PASS, before anything else
        # corner edge
        # corner edge
        
        _seen_x = set()
        for ia_ in range(len(fls)):
            for ea_ in (0, 1):
                fa = fls[ia_]
                if not fa["chain_end"][ea_]: continue
                Ja = np.asarray(fa["J"][ea_], float); hit = None
                for ib_ in range(len(fls)):
                    if ib_ == ia_: continue
                    for eb_ in (0, 1):
                        if fls[ib_]["chain_end"][eb_] and np.linalg.norm(np.asarray(fls[ib_]["J"][eb_], float) - Ja) < 0.05: hit = (ib_, eb_)
                if hit is None or (min(ia_, hit[0]), max(ia_, hit[0]), tuple(np.round(Ja, 2))) in _seen_x: continue
                _seen_x.add((min(ia_, hit[0]), max(ia_, hit[0]), tuple(np.round(Ja, 2)))); ib_, eb_ = hit; fb = fls[ib_]
                if bool(fa["convex"]) != bool(fb["convex"]): continue      
                try:
                    sa_ = VX.spine(fa["S"], fa["NL"][fa["p"]], fa["NL"][fa["q"]], fa["r"], fa["convex"]); sb_ = VX.spine(fb["S"], fb["NL"][fb["p"]], fb["NL"][fb["q"]], fb["r"], fb["convex"])
                    meet_x = bool(VX.vertex_ball(sa_, sb_, tol=max(1e-3, 0.1 * float(min(fa["r"], fb["r"]))))["meet"])
                    if not meet_x:      
                        for x1_ in _flat_e([fa["lines"][A][0]]):
                            for x2_ in _flat_e([fb["lines"][A][0]]):
                                try: d_x, p_x, _i = x1_.distToShape(x2_)
                                except Exception: continue
                                if d_x <= 0.05 and p_x:
                                    px_ = np.array([p_x[0][0].x, p_x[0][0].y, p_x[0][0].z])
                                    if min(np.linalg.norm(px_ - _vpt(v_)) for e_ in (x1_, x2_) for v_ in (e_.Vertexes[0], e_.Vertexes[-1])) > 0.1: meet_x = True
                except Exception: continue
                if not meet_x: continue
                
                for fx_, ex_, ix_ in ((fa, ea_, ia_), (fb, eb_, ib_)):
                    sh_x = float((fx_.get("short") or {}).get(ex_) or (fx_.get("short") or {}).get(str(ex_)) or 0.0)
                    if sh_x <= 1e-4 or (fx_.get("extended") or {}).get(ex_): continue
                    mx_ = next((m2 for m2 in _ch["members"] if (("%d leg %s" % (int(m2["line"]), m2["leg"])) if m2.get("leg") is not None else str(int(m2["line"]))) == fx_.get("name")), None)
                    if mx_ is None or str(ex_) not in (mx_.get("chain_c") or {}): continue
                    mx_["chain_c"][str(ex_)]["extend"] = float(min(sh_x * 1.25 + 0.1, 3.0 * max(float(fx_.get("t") or 0.5), 0.5)))
                    try:
                        fl2_ = _fillet_lines(mx_); fl2_["key"] = fx_["key"]; fl2_["cid"] = _cid; _apply_cuts(fl2_); FIL_MERGE[fx_["key"]] = fl2_; fls[ix_] = fl2_
                        say("   fillet chain %d: junction %s is CONCAVE and member %s's side offset fell %.2f mm short of the corner edge there - its sweep EXTENDED %.2f mm past the junction and laid again (fix 9f: the ball rolls on until it touches the next wall; at a convex junction it pivots and never rolls past)" % (_cid, np.round(Ja, 1).tolist(), fx_.get("name"), sh_x, mx_["chain_c"][str(ex_)]["extend"]))
                    except Exception as ex_e:
                        mx_["chain_c"][str(ex_)].pop("extend", None); say("   fillet chain %d: member %s could not be swept extended at %s (%s) - it stands as swept (the ramp)" % (_cid, fx_.get("name"), np.round(Ja, 1).tolist(), str(ex_e)[:1500]))
        # 31bq R7v (B26): THE VERTEX PASS  corner edge
        
        # corner edge
        _nm_of0 = lambda m__: ("%d leg %s" % (int(m__["line"]), m__["leg"])) if m__.get("leg") is not None else str(int(m__["line"]))
        def _turn_at(Ja_):
            """31bx K35: the crease's turn at the junction - the chain's junction record, by the point (180 when none); said with the contacts so a reader sees the kink a short member bridges"""
            try:
                tj_ = [float(j_.get("turn_deg", 180.0)) for j_ in (_ch.get("junctions") or []) if "turn_deg" in j_ and np.linalg.norm(np.asarray(j_["J"], float) - np.asarray(Ja_, float)) < 0.05]
                return float(min(tj_)) if tj_ else 180.0
            except Exception: return 180.0
        _seen_v = set()
        for _vpass_, ia_ in [(p__, i__) for p__ in (0, 1) for i__ in range(len(fls))]:      
            for ea_ in (0, 1):
                fa = fls[ia_]
                if not fa["chain_end"][ea_]: continue
                Ja = np.asarray(fa["J"][ea_], float); hit = None
                for ib_ in range(len(fls)):
                    if ib_ == ia_: continue
                    for eb_ in (0, 1):
                        if fls[ib_]["chain_end"][eb_] and np.linalg.norm(np.asarray(fls[ib_]["J"][eb_], float) - Ja) < 0.05: hit = (ib_, eb_)
                _jk = None if hit is None else (min(ia_, hit[0]), max(ia_, hit[0]), tuple(np.round(Ja, 2)))
                if hit is None or _jk in _seen_v: continue
                ib_, eb_ = hit; fb = fls[ib_]
                # mirror_of
                _twin_ = any(m_.get("mirror_of") is not None for m_ in _ch["members"] if _nm_of0(m_) in (fa.get("name"), fb.get("name")))
                if (_vpass_ == 0) == bool(_twin_): continue
                _seen_v.add(_jk)
                def _mkey(fx_):
                    """the member's MASTER line: the line its entry mirrors, else its own (a leg of one line is the other leg's mirror)"""
                    m__ = next((m_ for m_ in _ch["members"] if _nm_of0(m_) == fx_.get("name")), {}) or {}
                    return int(m__["mirror_of"]) if m__.get("mirror_of") is not None else int(m__.get("line", -1))
                mm_a = next((m_ for m_ in _ch["members"] if _nm_of0(m_) == fa.get("name")), None); cc_v = ((mm_a or {}).get("chain_c") or {}).get(str(ea_)) or {}; kk_v = cc_v.get("chain")
                if kk_v is None or int(kk_v) not in _VERTEX_C: continue
                V_ = _VERTEX_C[int(kk_v)]
                try:
                    if int(kk_v) not in FILLET_LINES: say("   fillet chain %d: junction %s - the corner edge %d's fillet is not in this lines pass: no vertex ball; the corner as before (31bq R7v)" % (_cid, np.round(Ja, 1).tolist(), int(kk_v))); continue
                    if fa["convex"] or fb["convex"]: say("   fillet chain %d: junction %s - the vertex ball needs two CONCAVE blends (%s is %s, %s is %s): the corner edge %d's fillet - it was held for the ball: it is NOT made by lines and stays as this pass leaves it (sharp), the corner as before (31bq R7v; R7W merge-B26: this line had said 'made as a single blend', and nothing swept it)" % (_cid, np.round(Ja, 1).tolist(), fa.get("name"), "convex" if fa["convex"] else "concave", fb.get("name"), "convex" if fb["convex"] else "concave", int(kk_v))); V_["single"] = True; _sweep_declined(int(kk_v), V_); continue
                    sa_ = VX.spine(fa["S"], fa["NL"][fa["p"]], fa["NL"][fa["q"]], fa["r"], fa["convex"]); sb_ = VX.spine(fb["S"], fb["NL"][fb["p"]], fb["NL"][fb["q"]], fb["r"], fb["convex"])
                    vb_v = VX.vertex_ball(sa_, sb_, tol=max(1e-3, 0.1 * float(min(fa["r"], fb["r"]))))
                    if not vb_v["meet"]: say("   fillet chain %d: junction %s - the two spines do not meet (gap %.2f mm): no vertex ball; the corner edge %d's fillet - it was held for the ball: it is NOT made by lines and stays as this pass leaves it (sharp), the corner as before (31bq R7v; R7W merge-B26: this line had said 'made as a single blend', and nothing swept it)" % (_cid, np.round(Ja, 1).tolist(), vb_v["gap"], int(kk_v))); V_["single"] = True; _sweep_declined(int(kk_v), V_); continue
                    C_v = np.asarray(vb_v["C"], float); R_v = float(fa["r"])
                    def _cutback_of(fx_, ex_, frac_):
                        S__ = np.asarray(fx_["S"], float); cs__ = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(S__, axis=0), axis=1))])
                        i__ = int(min(max(int(frac_), 0), len(S__) - 2)); L__ = cs__[i__] + (float(frac_) - i__) * (cs__[i__ + 1] - cs__[i__])
                        iJ__ = int(np.argmin(np.linalg.norm(S__ - np.asarray(fx_["J"][ex_], float), axis=1))); return abs(L__ - cs__[iJ__])
                    cb_a = _cutback_of(fa, ea_, vb_v["ia"]); cb_b = _cutback_of(fb, eb_, vb_v["ib"])
                    
                    P_v = fa["q"] if fa["p"] == A else fa["p"]; Q_v = fb["q"] if fb["p"] == A else fb["p"]
                    pq_c = [int(x) for x in CH[int(kk_v)]["pair"]]
                    if set(pq_c) != {int(P_v), int(Q_v)}: say("   fillet chain %d: junction %s - the corner edge %d borders faces %s, not the two side faces %s: no vertex ball there (31bq R7v)" % (_cid, np.round(Ja, 1).tolist(), int(kk_v), pq_c, [P_v, Q_v])); V_["single"] = True; _sweep_declined(int(kk_v), V_); continue
                    S_c = np.vstack([samples(x_, 0.3) for x_ in _flat_e([ALL_E[int(kk_v)]])])
                    if np.linalg.norm(S_c[0] - Ja) > np.linalg.norm(S_c[-1] - Ja): S_c = S_c[::-1]
                    _, nP_ = K.local_face_normals(Vu, F, pid, int(P_v), S_c)[:2]; _, nQ_ = K.local_face_normals(Vu, F, pid, int(Q_v), S_c)[:2]
                    if nP_ is None or nQ_ is None: raise RuntimeError("no mesh normals along the corner edge")
                    sp_c = VX.spine(S_c, nP_, nQ_, R_v, convex=False); d_c = np.linalg.norm(sp_c - C_v, axis=1); ic_ = int(np.argmin(d_c))
                    
                    # stations
                    
                    _cA = sp_c[:-1]; _cD = sp_c[1:] - _cA; _cL2 = np.maximum(np.einsum("ij,ij->i", _cD, _cD), 1e-18)
                    _ct = np.clip(np.einsum("ij,ij->i", C_v[None, :] - _cA, _cD) / _cL2, 0.0, 1.0); _cF = _cA + _ct[:, None] * _cD; _cdf = np.linalg.norm(_cF - C_v, axis=1)
                    _if = int(np.argmin(_cdf)); d_foot = float(_cdf[_if])
                    if d_foot > 0.35: say("   fillet chain %d: junction %s - the corner edge %d's spine passes %.2f mm from the vertex ball's centre (over 0.35): the three creases do not share one ball there; the corner edge's fillet - it was held for the ball: it is NOT made by lines and stays as this pass leaves it (sharp), the corner as before (31bq R7v; R7W merge-B26: this line had said 'made as a single blend', and nothing swept it)" % (_cid, np.round(Ja, 1).tolist(), int(kk_v), d_foot)); V_["single"] = True; _sweep_declined(int(kk_v), V_); continue
                    cs_c = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(S_c, axis=0), axis=1))]); cb_c_sample = float(cs_c[ic_])
                    cb_c = float(cs_c[_if] + float(_ct[_if]) * (cs_c[_if + 1] - cs_c[_if]))
                    say("   fillet chain %d: junction %s - c %d's station is the continuous foot of the ball's centre on c's spine: %.3f mm up the edge (the nearest SAMPLE read %.3f; one sample step %.3f mm; the spine %.3f mm from the centre at the foot) - 31bq R7v4" % (_cid, np.round(Ja, 1).tolist(), int(kk_v), cb_c, cb_c_sample, float(np.median(np.diff(cs_c))) if len(cs_c) > 1 else 0.0, d_foot))
                    # THE TWIN JUNCTION TAKES ITS MASTER'S BALL
                    # stations
                    _mst_ = None
                    if _twin_ and MP is not None:
                        _Jr_ = K.reflect(np.asarray([Ja], float), MP[0], MP[1])[0]
                        _mst_ = next((v__ for v__ in _VERTEX_C.values() if v__.get("done") and v__.get("cid") == _cid and v__.get("lines_cb") and v__.get("Ja") is not None and np.linalg.norm(np.asarray(v__["Ja"], float) - _Jr_) < 0.1), None)
                        if _mst_ is None: say("   fillet chain %d: junction %s is a twin but no made ball stands at its mirror %s - it reads its own ball (31bq R7v3)" % (_cid, np.round(Ja, 1).tolist(), np.round(_Jr_, 1).tolist()))
                    if _mst_ is not None:
                        if _mkey(fa) not in _mst_["lines_cb"] or _mkey(fb) not in _mst_["lines_cb"]: raise RuntimeError("the twin's members %s / %s (master lines %s / %s) are not the master ball's %s" % (fa.get("name"), fb.get("name"), _mkey(fa), _mkey(fb), sorted(_mst_["lines_cb"])))
                        _own_ = (np.asarray(C_v, float).copy(), cb_a, cb_b, cb_c)
                        cb_a = float(_mst_["lines_cb"][_mkey(fa)]); cb_b = float(_mst_["lines_cb"][_mkey(fb)]); cb_c = float(_mst_["cb"][2])
                        C_v = K.reflect(np.asarray([_mst_["C"]], float), MP[0], MP[1])[0]; V_["master"] = _mst_; V_["mkeys"] = (_mkey(fa), _mkey(fb))
                        say("   fillet chain %d: junction %s takes THE MIRROR OF junction %s's ball (31bq R7v3): centre %s (its own mesh read %s, %.3f mm away), stations %.2f / %.2f mm and c's %.2f (its own %.2f / %.2f / %.2f)" % (
                            _cid, np.round(Ja, 1).tolist(), np.round(_mst_["Ja"], 1).tolist(), np.round(C_v, 3).tolist(), np.round(_own_[0], 3).tolist(), float(np.linalg.norm(C_v - _own_[0])), cb_a, cb_b, cb_c, _own_[1], _own_[2], _own_[3]))
                    # stations
                    for fx_, ex_, ix_, cb_ in ((fa, ea_, ia_, cb_a), (fb, eb_, ib_, cb_b)):
                        mx_ = next((m_ for m_ in _ch["members"] if _nm_of0(m_) == fx_.get("name")), None)
                        if mx_ is None or str(ex_) not in (mx_.get("chain_c") or {}): raise RuntimeError("member %s's junction record is missing" % fx_.get("name"))
                        mx_["chain_c"][str(ex_)].update({"vertex": True, "cutback": float(cb_)}); mx_["chain_c"][str(ex_)].pop("target", None); _ext6_ = mx_["chain_c"][str(ex_)].pop("extend", None); V_.setdefault("ext6", []).append(float(_ext6_ or 0.0))      
                        fl2_ = _fillet_lines(mx_); fl2_["key"] = fx_["key"]; fl2_["cid"] = _cid; fl2_.setdefault("vertex_end", [False, False])[ex_] = True; _apply_cuts(fl2_); FIL_MERGE[fx_["key"]] = fl2_; fls[ix_] = fl2_
                    fa = fls[ia_]; fb = fls[ib_]
                    
                    ec_v = 0; e_c = dict(V_["entry"]); e_c["chain_ends"] = [True, False]; e_c["chain_common"] = None; e_c["chain_c"] = {"0": {"vertex": True, "cutback": cb_c}}; e_c["_vertex_pass"] = True
                    _cv0 = _flat_e([ALL_E[int(kk_v)]]); _v0 = np.array([_cv0[0].Vertexes[0].X, _cv0[0].Vertexes[0].Y, _cv0[0].Vertexes[0].Z])
                    if np.linalg.norm(_v0 - Ja) > np.linalg.norm(np.array([_cv0[-1].Vertexes[-1].X, _cv0[-1].Vertexes[-1].Y, _cv0[-1].Vertexes[-1].Z]) - Ja): ec_v = 1; e_c["chain_ends"] = [False, True]; e_c["chain_c"] = {"1": {"vertex": True, "cutback": cb_c}}
                    fl_c = _fillet_lines(e_c); fl_c["key"] = int(kk_v); fl_c["cid"] = None; fl_c.setdefault("vertex_end", [False, False])[ec_v] = True; _apply_cuts(fl_c); FIL_MERGE[int(kk_v)] = fl_c
                    V_.update({"done": True, "fl": fl_c, "ec": ec_v, "C": C_v, "R": R_v, "P": int(P_v), "Q": int(Q_v), "cb": (cb_a, cb_b, cb_c)}); _VERTEX_J[_vx_id(fa, fb, Ja)] = int(kk_v)
                    V_.update({"Ja": np.asarray(Ja, float), "names": (fa.get("name"), fb.get("name")), "ea": int(ea_), "eb": int(eb_), "lines_cb": {_mkey(fa): cb_a, _mkey(fb): cb_b}, "kname": {_mkey(fa): fa.get("name"), _mkey(fb): fb.get("name")}})      
                    say("   fillet chain %d: junction %s is a VERTEX BALL (31bq R7v, B26) - %s, %s and the corner edge %d's own fillet (R %g) meet in one ball centred at %s: the sweeps stop %.2f / %.2f mm before the junction and c's starts %.2f mm up it (the ball's stations; c's spine %.3f mm from the centre); the sphere triangle through their three end arcs closes the corner - no mitre, the extension past the junction dropped (%.2f / %.2f mm - 31bq R7v6a)" % (
                        _cid, np.round(Ja, 1).tolist(), fa.get("name"), fb.get("name"), int(kk_v), R_v, np.round(C_v, 2).tolist(), cb_a, cb_b, cb_c, d_foot, (list(V_.get("ext6") or []) + [0.0, 0.0])[0], (list(V_.get("ext6") or []) + [0.0, 0.0])[1]))      
                    say("FILLET BY LINES on line %d (R %g, faces %d | %d, concave crease - the CORNER EDGE of fillet chain %d's junction %s): swept from the vertex ball's station (%.2f mm up the edge) to its other end; its lower end arc is the ball's circle between the two side faces' contacts" % (int(kk_v), R_v, int(P_v), int(Q_v), _cid, np.round(Ja, 1).tolist(), cb_c))
                except Exception as ex_v:
                    import traceback as _tbv; _frv = _tbv.extract_tb(sys.exc_info()[2])[-1]
                    say("   fillet chain %d: the vertex ball at %s could not be made - %s (%s line %d): the corner edge %d's fillet - it was held for the ball: it is NOT made by lines and stays as this pass leaves it (sharp), the corner as before (31bq R7v; R7W merge-B26: this line had said 'made as a single blend', and nothing swept it)" % (_cid, np.round(Ja, 1).tolist(), str(ex_v)[:400], os.path.basename(_frv.filename), _frv.lineno, int(kk_v))); V_["single"] = True; _sweep_declined(int(kk_v), V_)
        # THE CONTACTS PASS:  corner edge  corner edge
        
        _seen_c = set()
        for ia_ in range(len(fls)):
            for ea_ in (0, 1):
                fa = fls[ia_]
                if not fa["chain_end"][ea_]: continue
                Ja = np.asarray(fa["J"][ea_], float); hit = None
                for ib_ in range(len(fls)):
                    if ib_ == ia_: continue
                    for eb_ in (0, 1):
                        if fls[ib_]["chain_end"][eb_] and np.linalg.norm(np.asarray(fls[ib_]["J"][eb_], float) - Ja) < 0.05: hit = (ib_, eb_)
                if hit is None or (min(ia_, hit[0]), max(ia_, hit[0]), tuple(np.round(Ja, 2))) in _seen_c: continue
                _seen_c.add((min(ia_, hit[0]), max(ia_, hit[0]), tuple(np.round(Ja, 2)))); ib_, eb_ = hit; fb = fls[ib_]
                if _vx_id(fa, fb, Ja) in _VERTEX_J: continue      
                if _noreach_at(fa, ea_) is not None or _noreach_at(fb, eb_) is not None: continue      # corner edge
                P_ = fa["q"] if fa["p"] == A else fa["p"]; Q_ = fb["q"] if fb["p"] == A else fb["p"]
                if bool(fa["convex"]) != bool(fb["convex"]): continue      
                say("   fillet chain %d: junction %s - the crease turns %.1f deg there; blends %s (t %.2f) and %s (t %.2f) (31bx K35)" % (_cid, np.round(Ja, 1).tolist(), _turn_at(Ja), fa.get("name"), float(fa.get("t") or 0.0), fb.get("name"), float(fb.get("t") or 0.0)))
                try:
                    Qa0_ = np.asarray(fa["PEND"][P_][ea_], float); Qb0_ = np.asarray(fb["PEND"][Q_][eb_], float); d0_ = float(np.linalg.norm(Qa0_ - Qb0_))
                    if not (0.05 < d0_ <= CONTACT_MERGE_MAX):      
                        if d0_ > CONTACT_MERGE_MAX: say("   fillet chain %d: junction %s - the two contacts on the corner edge are %.2f mm apart, over CONTACT_MERGE_MAX %g: they stand as two (at a CONVEX junction the pivot patch spans them by design; at a CONCAVE one a sliver is left between the mitre edges - raise the lever, or lower the wider member's R)" % (_cid, np.round(Ja, 1).tolist(), d0_, CONTACT_MERGE_MAX))
                        continue
                    ma0_ = fa["meet"][P_][ea_] or {}; mb0_ = fb["meet"][Q_][eb_] or {}
                    # corner edge
                    # corner edge
                    
                    _ta, _tb = float(fa.get("t") or 0.0), float(fb.get("t") or 0.0)      # corner edge  corner edge
                    if abs(_ta - _tb) < 0.05: _ta, _tb = float(np.linalg.norm(Qa0_ - Ja)), float(np.linalg.norm(Qb0_ - Ja))      
                    mi_, em_, anchor_pt, an_ = (ib_, eb_, Qa0_, fa) if _ta >= _tb else (ia_, ea_, Qb0_, fb)
                    fm_ = fls[mi_]; mm_ = next((m_ for m_ in _ch["members"] if (("%d leg %s" % (int(m_["line"]), m_["leg"])) if m_.get("leg") is not None else str(int(m_["line"]))) == fm_.get("name")), None)
                    if mm_ is None or str(em_) not in (mm_.get("chain_c") or {}): continue
                    mm_["chain_c"][str(em_)]["target"] = [float(x) for x in anchor_pt]
                    fl2_ = _fillet_lines(mm_); fl2_["key"] = fm_["key"]; fl2_["cid"] = _cid; _apply_cuts(fl2_); FIL_MERGE[fm_["key"]] = fl2_; fls[mi_] = fl2_
                    say("   fillet chain %d: junction %s - the two contacts on the corner edge were %.2f mm apart (within CONTACT_MERGE_MAX %g): member %s swept again onto %s's contact (one contact)" % (_cid, np.round(Ja, 1).tolist(), d0_, CONTACT_MERGE_MAX, fl2_.get("name"), an_.get("name")))
                except Exception as ex_t:
                    say("   fillet chain %d: the second sweep onto one contact failed - %s; the two contacts stand" % (_cid, str(ex_t)[:1500]))
        def _give_up(i_, e_, cap=True):
            """a member's chain end freed: swept again with the TAPER there - or, when the taper does not fit (the width rule: the side face a wedge narrower
            than t beside the junction), with the kit's CAP at that end (31bl: the blend cut where its offset meets the border, an end line where it does
            not, a cap) - in place; the junction's corner is not made. The member's end is found by geometry (the junction), not by the record's index.
            31bq R7W W2 (R7Wj c): between the taper and the cap THE TAPER FROM WHERE THE ROOM ENDS - the run-out lengthened to the crease sample the width rule
            named (max(1.5 d, d + TAPER_MIN), at most half the crease; L141: where the room ends, the radius ends with it); cap=False at a reflex-corner junction - a
            cap's end line on the common face collides with the chain-mate's tapered strip (w2e: face 2 invalid, the cap faces crossing themselves); a member whose
            tapers both fail has an OPEN end (B04 (3): dropped after the settle), its room line and the way out recorded in _open_why"""
            f0_ = fls[i_]; Je_ = np.asarray(f0_["J"][e_], float)
            try:
                m_ = next((m2 for m2 in _ch["members"] if (("%d leg %s" % (int(m2["line"]), m2["leg"])) if m2.get("leg") is not None else str(int(m2["line"]))) == f0_.get("name")), None)
                if m_ is None: return
                em_ = int(np.argmin([np.linalg.norm(np.asarray(x_, float) - Je_) for x_ in m_["_ends"]]))
                m_["chain_ends"] = list(m_.get("chain_ends") or [False, False]); m_["chain_ends"][em_] = False; m_["freed"] = sorted(set(int(x_) for x_ in (m_.get("freed") or [])) | {int(em_)})      
                if str(em_) in (m_.get("chain_c") or {}): m_["chain_c"][str(em_)].pop("target", None)
            except Exception as ex_g0:
                say("   fillet chain %d: member %s's end at %s could not be freed (%s) - it stands as swept" % (_cid, f0_.get("name"), np.round(Je_, 1).tolist(), str(ex_g0)[:120])); return
            why_ = {}
            for form_ in (("taper", "taper-long", "cap") if cap else ("taper", "taper-long")):
                try:
                    if form_ == "taper-long":
                        _dat = why_.get("_noroom_mm")
                        if _dat is None: continue      
                        try: _Lm = float(m_["_edge"].Length)
                        except Exception: _Lm = 2.0 * (float(_dat) + TAPER_MIN)
                        m_["taper_run"] = dict(m_.get("taper_run") or {}); m_["taper_run"][em_] = float(min(max(1.5 * float(_dat), float(_dat) + TAPER_MIN), 0.5 * _Lm))
                    if form_ == "cap": m_.pop("taper_run", None); m_["no_taper"] = list(m_.get("no_taper") or [False, False]); m_["no_taper"][em_] = True
                    fl2_ = _fillet_lines(m_); fl2_["key"] = f0_["key"]; fl2_["cid"] = _cid; _apply_cuts(fl2_); FIL_MERGE[f0_["key"]] = fl2_; fls[i_] = fl2_
                    if form_ == "taper-long": say("   fillet chain %d: member %s's freed end at %s TAPERS FROM WHERE THE ROOM ENDS - its run-out %.2f mm (the kit's %.2f was short of it: %s) (31bq R7W W2; L141: where the room ends, the radius ends with it)" % (_cid, fl2_.get("name"), np.round(Je_, 1).tolist(), float(m_["taper_run"][em_]), max(TAPER_X * float(fl2_.get("t") or 0.0), TAPER_MIN), str(why_.get("taper", "?"))[:400]))
                    if form_ == "cap": say("   fillet chain %d: member %s's freed end at %s takes the CAP (the blend cut where its offset meets the border, an end line where it does not) - the taper did not fit there: %s" % (_cid, fl2_.get("name"), np.round(Je_, 1).tolist(), why_.get("taper", "?")))
                    return
                except _NoRoom as ex_g:
                    why_[form_] = str(ex_g)[:1500]
                    if getattr(ex_g, "at", None) is not None and "_noroom_mm" not in why_: why_["_noroom_mm"] = float(np.linalg.norm(np.asarray(ex_g.at, float) - Je_))      
                except Exception as ex_g:
                    why_[form_] = str(ex_g)[:1500]
            if cap: _wo_ = "neither the taper (%s)%s nor the cap (%s)" % (why_.get("taper", "?"), (" nor the taper from where the room ends - %.2f mm from the junction (%s)" % (why_["_noroom_mm"], why_.get("taper-long", "?"))) if "taper-long" in why_ else "", why_.get("cap", "?"))
            else: _wo_ = "its R does not fit the side face beside the junction (this end was FREED because its chain-mate at the junction was not made or the two offsets do not meet there - the FILLET CHAIN lines above say which; a smaller R can free an end a larger R met in a corner form, and the taper then needs its own room - 31bx R5 F3) - the taper: %s%s; a CAP is not tried at a reflex-corner junction (its end line on the common face would collide with the chain-mate's tapered strip - w2e). THE WAY OUT: lower R on this line (the room line names the R that fits), or redraw its border so the side face has room beside the crease at the junction" % (why_.get("taper", "?"), ("; the taper from where the room ends (%.2f mm from the junction): %s" % (why_["_noroom_mm"], why_.get("taper-long", "?"))) if "taper-long" in why_ else "")
            _open_why[f0_.get("key")] = _wo_
            say("   fillet chain %d: member %s could not be swept again with its end at %s freed - %s: an OPEN end - the strips will NOT close there, %s (31bq R6 / R7W, B04 (3))" % (_cid, f0_.get("name"), np.round(Je_, 1).tolist(), _wo_, "so the member is dropped after this settle pass" if _pass == "settle" else "and in the build pass it stands with that end open (no settle follows)"))
            if _pass == "settle": _open_.add(f0_.get("key"))
        done_ = set(); arcs_A = {}; cfrag_ = {}; cseg_ = {}
        _open_ = set()
        _open_why = {}      
        _passes_ = ["settle", "build"]; _ip_ = 0
        while _ip_ < len(_passes_):      
          _pass = _passes_[_ip_]; _ip_ += 1
          done_ = set()
          for ia_ in range(len(fls)):
            for ea_ in (0, 1):
                fa = fls[ia_]
                if not fa["chain_end"][ea_]: continue
                Ja = np.asarray(fa["J"][ea_], float); hit = None
                for ib_, fb in enumerate(fls):
                    if ib_ == ia_: continue
                    for eb_ in (0, 1):
                        if fb["chain_end"][eb_] and np.linalg.norm(np.asarray(fb["J"][eb_], float) - Ja) < 0.05: hit = (ib_, eb_)
                if _pass == "settle" and fa.get("key") in _open_: continue
                if hit is not None and _pass == "settle" and fls[hit[0]].get("key") in _open_: continue      
                if hit is None:
                    say("FILLET CHAIN %d: member %s's end at %s meets no made member there - swept again with that end free (the taper)" % (_cid, fa.get("name"), np.round(Ja, 1).tolist())); _give_up(ia_, ea_); continue
                if (min(ia_, hit[0]), max(ia_, hit[0]), tuple(np.round(Ja, 2))) in done_: continue
                done_.add((min(ia_, hit[0]), max(ia_, hit[0]), tuple(np.round(Ja, 2)))); ib_, eb_ = hit; fb = fls[ib_]
                P_ = fa["q"] if fa["p"] == A else fa["p"]; Q_ = fb["q"] if fb["p"] == A else fb["p"]
                _vxk = _vx_id(fa, fb, Ja)
                
                if _vxk in _VERTEX_J:
                    
                    # recorded
                    if _pass == "settle": continue
                    try:
                        V_ = _VERTEX_C[_VERTEX_J[_vxk]]; fl_c = V_["fl"]; ec_ = int(V_["ec"]); C_v = np.asarray(V_["C"], float); R_v = float(V_["R"]); kk_v = int(_VERTEX_J[_vxk])
                        def _snap_end(fl_, f_, e_, X_):
                            """the offset line of fl_ on face f_ at end e_ re-fitted onto X_ (its end nearest the recorded end), the record's end moved"""
                            old_ = np.asarray(fl_["PEND"][f_][e_], float); pcs_ = _flat_e([fl_["lines"][f_][0]])
                            j_ = int(np.argmin([min(np.linalg.norm(_vpt(v_) - old_) for v_ in (e__.Vertexes[0], e__.Vertexes[-1])) for e__ in pcs_]))
                            pcs_[j_] = VX.refit_end(pcs_[j_], _end_vertex([pcs_[j_]], old_), X_); _set_line(fl_, f_, pcs_ if len(pcs_) > 1 else pcs_[0]); fl_["PEND"][f_][e_] = np.asarray(X_, float)
                        
                        Oa_A = np.asarray(fa["PEND"][A][ea_], float); Ob_A = np.asarray(fb["PEND"][A][eb_], float); X_A = 0.5 * (Oa_A + Ob_A)
                        if kind[A] == "orig" and PJ[A].get("face") is not None:
                            try: _SA = BF[int(PJ[A]["face"])].Surface; _ua, _va = _SA.parameter(V3(*X_A)); X_A = _vpt(_SA.value(_ua, _va))
                            except Exception: pass
                        def _master_contacts(V__):
                            """31bq R7v3: a twin junction's three contacts - its master's (the members' offset ends' midpoints there, as the master's own pass snaps
                            them), reflected in the mirror plane; None for a master"""
                            M__ = V__.get("master")
                            if M__ is None or MP is None: return None
                            ma_ = next((f__ for f__ in fls if f__.get("name") == M__["names"][0]), None); mb_ = next((f__ for f__ in fls if f__.get("name") == M__["names"][1]), None); mc_ = M__["fl"]
                            if ma_ is None or mb_ is None: return None
                            mA_ = 0.5 * (np.asarray(ma_["PEND"][A][M__["ea"]], float) + np.asarray(mb_["PEND"][A][M__["eb"]], float))
                            def _side(mx__, ex__):
                                f__ = mx__["q"] if mx__["p"] == A else mx__["p"]
                                return 0.5 * (np.asarray(mx__["PEND"][f__][ex__], float) + np.asarray(mc_["PEND"][f__][int(M__["ec"])], float))
                            sid_ = {M__["names"][0]: _side(ma_, M__["ea"]), M__["names"][1]: _side(mb_, M__["eb"])}
                            R__ = lambda x__: K.reflect(np.asarray([x__], float), MP[0], MP[1])[0]
                            return R__(mA_), R__(sid_[M__["kname"][V__["mkeys"][0]]]), R__(sid_[M__["kname"][V__["mkeys"][1]]])
                        _MX_ = _master_contacts(V_)
                        if _MX_ is not None: _dA_ = float(np.linalg.norm(_MX_[0] - X_A)); X_A = _MX_[0]
                        # THE CONTACT ON THE COMMON FACE IS THE TWO OFFSETS' OWN CROSSING
                        
                        _XC_ = None; _Xm5_ = 0.5 * (Oa_A + Ob_A)
                        try:
                            for x1_ in _flat_e([fa["lines"][A][0]]):
                                for x2_ in _flat_e([fb["lines"][A][0]]):
                                    _xc = VX.cross_point(x1_, x2_, 0.6)
                                    if _xc is not None and (_XC_ is None or float(np.linalg.norm(np.asarray(_xc, float) - _Xm5_)) < float(np.linalg.norm(_XC_ - _Xm5_))): _XC_ = np.asarray(_xc, float)
                        except Exception as _exc5:
                            _XC_ = None; say("   fillet chain %d: VERTEX BALL at %s - the offsets' crossing on face %d could not be read (%s) - the midpoint contact stands (31bq R7v5)" % (_cid, np.round(Ja, 1).tolist(), A, str(_exc5)[:60]))
                        if _XC_ is not None and float(np.linalg.norm(_XC_ - _Xm5_)) <= 0.6:
                            _tw5_ = bool(_MX_ is not None and float(np.linalg.norm(_XC_ - X_A)) <= 0.05); _Xt5_ = np.asarray(X_A if _tw5_ else _XC_, float)
                            _dxa5, _Xa5, _e5 = _nearest_on(_flat_e([fa["lines"][A][0]]), _Xt5_); _dxb5, _Xb5, _e5 = _nearest_on(_flat_e([fb["lines"][A][0]]), _Xt5_)
                            _cut_line_at(fa, A, _Xa5, Oa_A); _cut_line_at(fb, A, _Xb5, Ob_A); X_A = _Xt5_
                            say("   fillet chain %d: VERTEX BALL at %s - on face %d the two members' offsets CROSS %.3f mm from their ends' midpoint (the ends %.3f mm apart): the contact is their crossing%s, both lines CUT there (%.3f / %.3f mm from it on each; the overshoots past it dropped - no bow-tie at the contact; 31bq R7v5)" % (
                                _cid, np.round(Ja, 1).tolist(), A, float(np.linalg.norm(_XC_ - _Xm5_)), float(np.linalg.norm(Oa_A - Ob_A)), (" (the master's reflected point, %.3f mm from the own crossing)" % float(np.linalg.norm(_XC_ - X_A))) if _tw5_ else "", _dxa5, _dxb5))
                        else: say("   fillet chain %d: VERTEX BALL at %s - on face %d the two members' offsets do not cross within 0.6 mm of their ends' midpoint (the ends %.3f mm apart%s): the contact is the midpoint, both ends moved onto it (31bq R7v5)" % (_cid, np.round(Ja, 1).tolist(), A, float(np.linalg.norm(Oa_A - Ob_A)), ("; the nearest crossing %.2f mm away" % float(np.linalg.norm(_XC_ - _Xm5_))) if _XC_ is not None else ""))
                        gA_ = float(np.linalg.norm(Oa_A - Ob_A)); _snap_end(fa, A, ea_, X_A); _snap_end(fb, A, eb_, X_A)
                        
                        Pf_ = fa["q"] if fa["p"] == A else fa["p"]; Qf_ = fb["q"] if fb["p"] == A else fb["p"]
                        X_P = 0.5 * (np.asarray(fa["PEND"][Pf_][ea_], float) + np.asarray(fl_c["PEND"][Pf_][ec_], float)); gP_ = float(np.linalg.norm(np.asarray(fa["PEND"][Pf_][ea_], float) - np.asarray(fl_c["PEND"][Pf_][ec_], float)))
                        X_Q = 0.5 * (np.asarray(fb["PEND"][Qf_][eb_], float) + np.asarray(fl_c["PEND"][Qf_][ec_], float)); gQ_ = float(np.linalg.norm(np.asarray(fb["PEND"][Qf_][eb_], float) - np.asarray(fl_c["PEND"][Qf_][ec_], float)))
                        if _MX_ is not None:      
                            say("   fillet chain %d: VERTEX BALL at %s - the twin's three contacts are the master's REFLECTED (moved %.3f / %.3f / %.3f mm from its own midpoints on faces %d / %d / %d) - 31bq R7v3" % (_cid, np.round(Ja, 1).tolist(), _dA_, float(np.linalg.norm(_MX_[1] - X_P)), float(np.linalg.norm(_MX_[2] - X_Q)), A, Pf_, Qf_))
                            X_P, X_Q = _MX_[1], _MX_[2]
                        _snap_end(fa, Pf_, ea_, X_P); _snap_end(fl_c, Pf_, ec_, X_P); _snap_end(fb, Qf_, eb_, X_Q); _snap_end(fl_c, Qf_, ec_, X_Q)
                        
                        arc_a = VX.refit_end(VX.refit_end(fa["ENDC"][ea_], Oa_A, X_A), np.asarray(fa["PEND"][Pf_][ea_], float) if False else X_P, X_P)
                        arc_a = fa["ENDC"][ea_]
                        for _old, _new in ((Oa_A, X_A),): arc_a = VX.refit_end(arc_a, _old, _new)
                        arc_a = VX.refit_end(arc_a, _end_vertex([arc_a], X_P) if False else [_vpt(v_) for v_ in arc_a.Vertexes if np.linalg.norm(_vpt(v_) - X_A) > 1e-6][0], X_P)
                        arc_b = fb["ENDC"][eb_]; arc_b = VX.refit_end(arc_b, Ob_A, X_A); arc_b = VX.refit_end(arc_b, [_vpt(v_) for v_ in arc_b.Vertexes if np.linalg.norm(_vpt(v_) - X_A) > 1e-6][0], X_Q)
                        arc_c = fl_c["ENDC"][ec_]; _vc = [_vpt(v_) for v_ in arc_c.Vertexes]
                        _cP = min(_vc, key=lambda v_: np.linalg.norm(v_ - X_P)); _cQ = [v_ for v_ in _vc if np.linalg.norm(v_ - _cP) > 1e-9][0]
                        arc_c = VX.refit_end(VX.refit_end(arc_c, _cP, X_P), _cQ, X_Q)
                        fa["ENDC"][ea_] = arc_a; fa["arcs"][ea_] = (arc_a, Ja); fb["ENDC"][eb_] = arc_b; fb["arcs"][eb_] = (arc_b, Ja); fl_c["ENDC"][ec_] = arc_c; fl_c["arcs"][ec_] = (arc_c, Ja)
                        surf_s = VX.sphere_fan(arc_a, arc_b, arc_c, X_A, C_v, R_v)
                        # THE TRIANGLE'S EDGES ARE THE FAN'S OWN BOUNDARY ISOS
                        
                        _iso6_ = None; _iso6_how_ = "the refit arcs (no iso held)"
                        try:
                            u0_, u1_, v0_, v1_ = surf_s.bounds()
                            def _fits6_(e_, A1_, A2_):
                                q0_, q1_ = _vpt(e_.Vertexes[0]), _vpt(e_.Vertexes[-1]); A1_ = np.asarray(A1_, float); A2_ = np.asarray(A2_, float)
                                return min(max(np.linalg.norm(q0_ - A1_), np.linalg.norm(q1_ - A2_)), max(np.linalg.norm(q0_ - A2_), np.linalg.norm(q1_ - A1_))) <= 1e-3
                            for _how6_, _trip6_ in (("uIso(u0) / uIso(u1) / vIso(v1)", (surf_s.uIso(u0_).toShape(), surf_s.uIso(u1_).toShape(), surf_s.vIso(v1_).toShape())),
                                                    ("vIso(v0) / vIso(v1) / uIso(u1) - the roles swapped", (surf_s.vIso(v0_).toShape(), surf_s.vIso(v1_).toShape(), surf_s.uIso(u1_).toShape()))):
                                if _fits6_(_trip6_[0], X_A, X_P) and _fits6_(_trip6_[1], X_A, X_Q) and _fits6_(_trip6_[2], X_P, X_Q): _iso6_ = _trip6_; _iso6_how_ = "the fan's own boundary isos, %s" % _how6_; break
                            if _iso6_ is None: say("   fillet chain %d: VERTEX BALL at %s - the fan's boundary isos do not end on the three contacts within 1e-3 mm (either role): the refit arcs stay the triangle's edges (31bq R7v6b)" % (_cid, np.round(Ja, 1).tolist()))
                        except Exception as ex6_: say("   fillet chain %d: VERTEX BALL at %s - the fan's isos could not be taken (%s): the refit arcs stay (31bq R7v6b)" % (_cid, np.round(Ja, 1).tolist(), str(ex6_)[:120])); _iso6_ = None
                        if _iso6_ is not None:
                            arc_a, arc_b, arc_c = _iso6_
                            fa["ENDC"][ea_] = arc_a; fa["arcs"][ea_] = (arc_a, Ja); fb["ENDC"][eb_] = arc_b; fb["arcs"][eb_] = (arc_b, Ja); fl_c["ENDC"][ec_] = arc_c; fl_c["arcs"][ec_] = (arc_c, Ja)
                        rec_s = {"span": "sphere", "sub": "FS", "corners": "the vertex ball of blends %s, %s and the corner edge %d's: the spherical triangle through their three end arcs (R %g about %s)" % (fa.get("name"), fb.get("name"), kk_v, R_v, np.round(C_v, 2).tolist()), "guides": 0, "fillet": fa["key"], "guide_after": 0.0, "nurbs_why": None, "folds": 0}
                        PIVOTS.append((A, surf_s, [arc_a, arc_b, arc_c], rec_s))
                        
                        for fx_, fside_, ex_ in ((fa, Pf_, ea_), (fb, Qf_, eb_)):
                            _VX_SIDE[(fx_["key"], int(fside_))] = {"c_key": kk_v, "c_off": list(_flat_e([fl_c["lines"][int(fside_)][0]])), "c_top_end": ([fl_c["ends"][int(fside_)][1 - ec_]] if fl_c["ends"][int(fside_)][1 - ec_] is not None else []), "c_top_meet": fl_c["meet"][int(fside_)][1 - ec_], "c_J_top": np.asarray(fl_c["J"][1 - ec_], float), "c_crease": list(_flat_e([ALL_E[kk_v]]))}
                        say("   fillet chain %d: VERTEX BALL at %s - the sphere triangle placed (its three contacts: on face %d the two offsets met %.3f mm apart, on face %d %.3f, on face %d %.3f - each snapped to one point; its three edges %s - 31bq R7v6b); the side faces' strips run along the member's offset to the contact and up the corner edge's blend (one split each)" % (_cid, np.round(Ja, 1).tolist(), A, gA_, Pf_, gP_, Qf_, gQ_, _iso6_how_))
                    except Exception as ex_s:
                        import traceback as _tbs; _frs = _tbs.extract_tb(sys.exc_info()[2])[-1]
                        say("   fillet chain %d: the sphere triangle at %s could not be made - %s (%s line %d): the three blends stand as swept with OPEN ends there" % (_cid, np.round(Ja, 1).tolist(), str(ex_s)[:400], os.path.basename(_frs.filename), _frs.lineno))
                    continue
                if bool(fa["convex"]) != bool(fb["convex"]):
                    
                    if _pass == "settle":
                        say("   fillet chain %d: junction %s - %s (a %s crease) meets %s (a %s one): the crease's SENSE changes there - a fillet meeting a round is no rolling-ball corner; the chain ENDS at that junction and both blends taper to it (the point stays sharp)" % (
                            _cid, np.round(Ja, 1).tolist(), fa.get("name"), "convex" if fa["convex"] else "concave", fb.get("name"), "convex" if fb["convex"] else "concave"))
                        _give_up(ia_, ea_); _give_up(ib_, eb_)
                    continue
                _nra = _noreach_at(fa, ea_); _nrb = _noreach_at(fb, eb_)
                if _nra is not None or _nrb is not None:
                    
                    # corner edge
                    
                    if _pass == "settle":
                        _ccn = None
                        for m_ in _ch["members"]:
                            for e_s, c_s in (m_.get("chain_c") or {}).items():
                                if np.linalg.norm(np.asarray(m_["_ends"][int(e_s)]) - Ja) < 0.05: _ccn = c_s
                        _kcn = (_ccn or {}).get("chain"); _wf, _wm, _wd = ((P_, fa, _nra) if _nra is not None else (Q_, fb, _nrb))
                        say("   fillet chain %d: junction %s - member %s's side offset on face %d CANNOT REACH the corner edge %s: the side face's corner at the junction is REFLEX (the corner edge leaves the junction at %s deg from the crease measured through the offset's side; the offset's end %.2f mm from the junction) - the wall the ball leans on turns away past the junction, so NO rolling-ball corner exists there: not the mitre (the offsets diverge) and not the vertex ball (three faces with a reflex one share no ball); the chain ENDS at that junction - %s and %s taper to it, the point stays sharp (L145's family). THE WAY OUT is a layout / lines decision: redraw the border so face %d's corner at the junction is a wedge the offset crosses (t = %.2f mm beside the crease), or end the chain there on purpose (31bq R7W W2: the ramp onto the junction had pinched both blends to nothing - the 56 legs' faces ICOS / SelfIntersect on every live piece)" % (
                            _cid, np.round(Ja, 1).tolist(), _wm.get("name"), int(_wf), ("chain %s" % _kcn) if _kcn is not None else "(a split)", ("%.0f" % _wd["deg"]) if _wd.get("deg") is not None else "?", float(_wd.get("mm") or 0.0), fa.get("name"), fb.get("name"), int(_wf), float(_wm.get("t") or 0.0)))
                        _give_up(ia_, ea_, cap=False); _give_up(ib_, eb_, cap=False)      
                    continue
                sa_ = VX.spine(fa["S"], fa["NL"][fa["p"]], fa["NL"][fa["q"]], fa["r"], fa["convex"]); sb_ = VX.spine(fb["S"], fb["NL"][fb["p"]], fb["NL"][fb["q"]], fb["r"], fb["convex"])
                vb_ = VX.vertex_ball(sa_, sb_, tol=max(1e-3, 0.1 * float(min(fa["r"], fb["r"]))))
                
                Oa_ = _end_vertex(_flat_e([fa["lines"][A][0]]), fa["PEND"][A][ea_]); Ob_ = _end_vertex(_flat_e([fb["lines"][A][0]]), fb["PEND"][A][eb_])
                if not vb_["meet"]:
                    
                    xg_ = None
                    for x1_ in _flat_e([fa["lines"][A][0]]):
                        for x2_ in _flat_e([fb["lines"][A][0]]):
                            try: d_x, p_x, _i = x1_.distToShape(x2_)
                            except Exception: continue
                            if d_x <= 0.05 and p_x:
                                px_ = np.array([p_x[0][0].x, p_x[0][0].y, p_x[0][0].z])
                                if min(np.linalg.norm(px_ - _vpt(v_)) for e_ in (x1_, x2_) for v_ in (e_.Vertexes[0], e_.Vertexes[-1])) > 0.1: xg_ = px_
                    if xg_ is not None:
                        if _pass == "build": say("   fillet chain %d: junction %s - the spines' test read CONVEX (%.2f mm apart at the junction stations) but the two offset lines on face %d CROSS at %s, %.2f / %.2f mm before their ends: the corner is CONCAVE by the common face's own geometry (the mitre)" % (
                            _cid, np.round(Ja, 1).tolist(), vb_["gap"], A, np.round(xg_, 2).tolist(), float(np.linalg.norm(xg_ - Oa_)), float(np.linalg.norm(xg_ - Ob_))))
                        vb_ = dict(vb_, meet=True, gap=0.0, la=vb_["len_a"], lb=0.0)
                Qa_ = _end_vertex(_flat_e([fa["lines"][P_][0]]), fa["PEND"][P_][ea_]); Qb_ = _end_vertex(_flat_e([fb["lines"][Q_][0]]), fb["PEND"][Q_][eb_]); dq_ = float(np.linalg.norm(Qa_ - Qb_)); Q0_ = 0.5 * (Qa_ + Qb_)
                cc_ = None
                for m_ in _ch["members"]:
                    for e_s, c_s in (m_.get("chain_c") or {}).items():
                        if np.linalg.norm(np.asarray(m_["_ends"][int(e_s)]) - Ja) < 0.05: cc_ = c_s
                if cc_ is None: say("FILLET CHAIN %d: no corner edge on record at %s - no corner patch there" % (_cid, np.round(Ja, 1).tolist())); continue
                ax_ = np.asarray(cc_["axis"], float)
                
                kk_c = cc_.get("chain"); cpcs_ = _flat_e([ALL_E[int(kk_c)]]) if kk_c is not None else [cc_["edge"]]
                dqa_, Qa2_, _e = _nearest_on(cpcs_, Qa_); dqb_, Qb2_, _e = _nearest_on(cpcs_, Qb_); dab_ = float(np.linalg.norm(Qa2_ - Qb2_)); cmid_ = None
                if _pass == "settle" and not vb_["meet"] and dab_ <= 0.3 and dqa_ <= 1e-3 and float(np.linalg.norm(Oa_ - Ob_)) < THIN_FIL and not any((fx_.get("mitre_x") or {}).get(ex_) for fx_, ex_ in ((fa, ea_), (fb, eb_))):
                    
                    _u7 = Oa_ - Ja; _u7 -= (_u7 @ ax_) * ax_; _w7 = Ob_ - Ja; _w7 -= (_w7 @ ax_) * ax_
                    _ang7 = abs(float(np.degrees(np.arctan2(float(ax_ @ np.cross(_u7, _w7)), float(_u7 @ _w7)))))
                    _t7 = max(float(fa.get("t") or 0.5), float(fb.get("t") or 0.5)); _ext7 = float(min(1.5, max(0.6, 2.5 * _t7 * np.tan(np.radians(min(_ang7, 60.0)) / 2.0) + 0.3)))
                    if _ang7 <= 45.0:
                        _new7 = []
                        try:
                            for fx_, ex_, ix_ in ((fa, ea_, ia_), (fb, eb_, ib_)):
                                mx_ = next((m2 for m2 in _ch["members"] if (("%d leg %s" % (int(m2["line"]), m2["leg"])) if m2.get("leg") is not None else str(int(m2["line"]))) == fx_.get("name")), None)
                                if mx_ is None or str(ex_) not in (mx_.get("chain_c") or {}): raise RuntimeError("member %s has no corner record at the junction" % fx_.get("name"))
                                old7_ = dict(mx_["chain_c"][str(ex_)]); mx_["chain_c"][str(ex_)]["extend"] = _ext7
                                try: fl7_ = _fillet_lines(mx_)
                                except Exception:
                                    mx_["chain_c"][str(ex_)] = old7_; raise
                                _new7.append((mx_, ex_, ix_, fx_, fl7_, old7_))
                            for mx_, ex_, ix_, fx_, fl7_, old7_ in _new7:
                                fl7_["key"] = fx_["key"]; fl7_["cid"] = _cid; fl7_.setdefault("mitre_x", {})[ex_] = True; _apply_cuts(fl7_); FIL_MERGE[fx_["key"]] = fl7_; fls[ix_] = fl7_
                            say("   fillet chain %d: CONVEX corner at %s turns %.0f deg with ONE contact and a floor of %.2f mm - under the print tolerance (THIN_MM %g): no corner face; %s and %s swept ON %.2f mm past the junction so their offsets on face %d cross - the corner is MITRED by their own surfaces' intersection (31bq R7W, A5: ZZ (4)'s one-arc merge left an edge off both blends)" % (_cid, np.round(Ja, 1).tolist(), _ang7, float(np.linalg.norm(Oa_ - Ob_)), THIN_FIL, fa.get("name"), fb.get("name"), _ext7, A))
                            continue
                        except Exception as ex7_:
                            for mx_, ex_, ix_, fx_, fl7_, old7_ in _new7: mx_["chain_c"][str(ex_)] = old7_
                            say("   fillet chain %d: the sub-tolerance convex corner at %s could not be swept on to a mitre (%s) - the rotation patch is made there" % (_cid, np.round(Ja, 1).tolist(), str(ex7_)[:300]))
                if dab_ <= 0.3 and dab_ > 1e-6:
                    
                    try:
                        ln_ = _flat_e([fb["lines"][Q_][0]]); j_ = int(np.argmin([min(np.linalg.norm(_vpt(v_) - Qb_) for v_ in (e_.Vertexes[0], e_.Vertexes[-1])) for e_ in ln_]))
                        ln_[j_] = VX.refit_end(ln_[j_], Qb_, Qa2_); _set_line(fb, Q_, ln_ if len(ln_) > 1 else ln_[0])
                        if fb["ENDC"][eb_] is not None: fb["ENDC"][eb_] = VX.refit_end(fb["ENDC"][eb_], Qb_, Qa2_); fb["arcs"][eb_] = (fb["ENDC"][eb_], fb["arcs"][eb_][1])
                        fb["PEND"][Q_][eb_] = Qa2_; Qb_ = Qa2_; Qb2_ = Qa2_; dab_ = 0.0
                    except Exception as ex_r: say("   fillet chain %d: the second contact could not be moved onto the first (%s)" % (_cid, str(ex_r)[:80]))
                if kk_c is not None and dab_ > 0.3:
                    cut_ok = _cut_chain_once(int(kk_c), Qa2_) and _cut_chain_once(int(kk_c), Qb2_)
                    if not cut_ok:
                        say("   fillet chain %d: junction %s - the corner edge (chain %d) could not be cut at the contacts %s / %s (%s): the corner is GIVEN UP - %s and %s end there with the taper" % (_cid, np.round(Ja, 1).tolist(), int(kk_c), np.round(Qa2_, 2).tolist(), np.round(Qb2_, 2).tolist(), _CUT_WHY.get(int(kk_c), "?"), fa.get("name"), fb.get("name")))
                        _give_up(ia_, ea_); _give_up(ib_, eb_); continue
                    la_, lb_ = np.linalg.norm(Qa2_ - Ja), np.linalg.norm(Qb2_ - Ja); lowQ_, highQ_ = (Qa2_, Qb2_) if la_ <= lb_ else (Qb2_, Qa2_)
                    low_pcs = _pieces_to(int(kk_c), Ja, lowQ_); high_pcs = _pieces_to(int(kk_c), Ja, highQ_)
                    mid_pcs = [x_ for x_ in high_pcs if not any(x_.isSame(y_) for y_ in low_pcs)]
                    cmid_ = mid_pcs
                    cfrag_[(fa["key"], ea_)] = low_pcs if la_ <= lb_ else high_pcs; cfrag_[(fb["key"], eb_)] = high_pcs if la_ <= lb_ else low_pcs
                    Q0_ = 0.5 * (Qa2_ + Qb2_); dc_ = 0.5 * dab_
                else:
                    Q0_ = 0.5 * (Qa2_ + Qb2_)
                    try:
                        dc_, pts_c, _i = (cpcs_[0] if len(cpcs_) == 1 else Part.makeCompound(cpcs_)).distToShape(Part.Vertex(V3(*Q0_))); Q0_ = np.array([pts_c[0][0].x, pts_c[0][0].y, pts_c[0][0].z])
                    except Exception: dc_ = 0.0
                    at_J_ = float(np.linalg.norm(Q0_ - Ja)) <= 0.05      
                    cut_ok = True if at_J_ else (_cut_chain_once(int(kk_c), Q0_) if kk_c is not None else _cut_split_at(cc_["split_face"], cc_["piece_mid"], Q0_))
                    if kk_c is not None:
                        if at_J_: fr_ = []
                        else:
                            try: fr_ = _frags(int(kk_c), Ja, "%s / %s" % (fa.get("name"), fb.get("name")))
                            except (_Uncut, SystemExit, Exception): fr_ = None
                        if fr_ is None or not cut_ok:
                            say("   fillet chain %d: junction %s - the corner edge (chain %d) could not be cut at the contact %s (%s): the corner is GIVEN UP - %s and %s end there with the taper" % (_cid, np.round(Ja, 1).tolist(), int(kk_c), np.round(Q0_, 2).tolist(), _CUT_WHY.get(int(kk_c), "the piece touching the junction was not found after the cut"), fa.get("name"), fb.get("name")))
                            _give_up(ia_, ea_); _give_up(ib_, eb_); continue
                        cfrag_[(fa["key"], ea_)] = fr_; cfrag_[(fb["key"], eb_)] = fr_
                    Qa2_ = Qb2_ = Q0_
                sga_ = VX.seg(Qa_, Qa2_, 1e-3); sgb_ = VX.seg(Qb2_, Qb_, 1e-3); cseg_[(fa["key"], ea_)] = sga_; cseg_[(fb["key"], eb_)] = sgb_
                apex_ = [Qa_, Qa2_, Qb2_, Qb_]
                if _pass == "settle": continue
                say("   fillet chain %d: junction %s - %s and %s: the ball centres' loci come %.2f mm close%s; the two offset ends %.2f mm apart, on the corner edge %.2f / %.2f mm from it, their contacts %.2f mm apart along it (%s)%s" % (
                    _cid, np.round(Ja, 1).tolist(), fa.get("name"), fb.get("name"), vb_["gap"], " at the junction stations (CONVEX)" if not vb_["meet"] else " %.2f / %.2f mm before it (CONCAVE)" % (vb_["len_a"] - vb_["la"], vb_["lb"]),
                    dq_, dqa_, dqb_, dab_, ("c cut at both - the piece between them (%d) is the corner's apex edge" % len(cmid_)) if cmid_ else ("c cut once at %s" % np.round(Q0_, 2).tolist() if cut_ok else "c NOT cut (no piece of it passes within 0.05 mm)"),
                    "" if (sga_ is None and sgb_ is None) else " - the side faces close to the corner edge by %.2f / %.2f mm edges" % (0 if sga_ is None else sga_.Length, 0 if sgb_ is None else sgb_.Length)))
                if not vb_["meet"]:
                    enda_, endb_ = fa["ENDC"][ea_], fb["ENDC"][eb_]
                    if enda_ is None or endb_ is None: say("FILLET CHAIN %d: a member has no end arc at %s - no patch" % (_cid, np.round(Ja, 1).tolist())); continue
                    _u = Oa_ - Ja; _u -= (_u @ ax_) * ax_; _w = Ob_ - Ja; _w -= (_w @ ax_) * ax_; ang_ = float(np.degrees(np.arctan2(float(ax_ @ np.cross(_u, _w)), float(_u @ _w)))); gap_ = 0.0
                    if abs(ang_) < 1.0 and dq_ < 0.02:
                        say("   fillet chain %d: the corner turns %.1f deg only - no patch, the two end arcs coincide" % (_cid, ang_)); continue
                    topP_ = ([sga_] if sga_ is not None else []) + list(cmid_ or []) + ([sgb_] if sgb_ is not None else [])
                    if not topP_ and float(np.linalg.norm(Oa_ - Ob_)) < THIN_FIL:
                        
                        say("   fillet chain %d: CONVEX corner at %s turns %.0f deg with ONE contact and a floor of %.2f mm (under THIN_MM %g) - NOT mitred (the blends swept on did not cross on face %d): the rotation patch is made (31bq R7W)" % (_cid, np.round(Ja, 1).tolist(), abs(ang_), float(np.linalg.norm(Oa_ - Ob_)), THIN_FIL, A))
                    _bal_p = {}      
                    try:
                        _Sorig = BF[int(PJ[A]["face"])].Surface if (kind[A] == "orig" and PJ[A].get("face") is not None) else None      
                        _apx = None      # corner edge  corner edge
                        if topP_:
                            try: _apx = [x_ for x_ in VX._boundary_pts(list(topP_), Qa_, max(9, int(sum(e__.Length for e__ in topP_) / 0.1) + 1))]      
                            except Exception as _ex_ap: _apx = None; say("   fillet chain %d: the corner patch's apex path could not be read off its %d edge(s) (%s) - the straight blend stands there" % (_cid, len(topP_), str(_ex_ap)[:80]))
                        surf_, _ang2, arc_ = VX.pivot_patch_bounded(enda_, endb_, Ja, ax_, Oa_, Ob_, apex_path=_apx, floor_on=_Sorig); how_p = "the rolling ball's rotation about the corner edge (G1 to both blends); its floor the rotation's own trace%s%s" % (" laid on the original surface" if _Sorig is not None else "", "; its apex on the corner edge between the two contacts" if _apx else "")
                    except Exception as ex_pv:
                        say("   fillet chain %d: the rotation patch at %s failed (%s) - the span ladder through its edges instead (a facet: no tangent)" % (_cid, np.round(Ja, 1).tolist(), str(ex_pv)[:80]))
                        arc_ = VX.corner_arc(Ja, Oa_, Ob_, ax_)
                        surf_, how_p = _span_corner([x_ for x_ in ([enda_, sga_] + list(cmid_ or []) + [sgb_, endb_, arc_]) if x_ is not None], "fillet chain %d: the convex corner patch at %s" % (_cid, np.round(Ja, 1).tolist()), VX.coons_patch(enda_, endb_, arc_, topP_ if topP_ else Qa2_)); _bal_p = dict(_SPANC_BAL)
                    if surf_ is None: continue
                    eds_p = [x_ for x_ in ([enda_, sga_] + list(cmid_ or []) + [sgb_, endb_, arc_]) if x_ is not None]
                    rec_p = {"span": "pivot", "sub": "FC", "corners": "the corner of blends %s and %s: the rolling ball pivoting %.0f deg about the corner edge - the patch between the two end arcs%s" % (fa.get("name"), fb.get("name"), abs(ang_), (" (the pure revolve of one arc would miss the other by %.2f mm; the offset ends %.2f mm apart)" % (gap_, dq_)) if (gap_ > 0.02 or dq_ > 0.02) else ""), "guides": 0, "fillet": fa["key"], "guide_after": 0.0, "nurbs_why": None, "folds": 0}
                    rec_p.update(_bal_p)      
                    if os.environ.get("FIL_DBG") == "1":
                        try:
                            _fe = [_vpt(arc_.Vertexes[0]), _vpt(arc_.Vertexes[-1])]; _ae = [_vpt(enda_.Vertexes[0]), _vpt(enda_.Vertexes[-1])]; _be = [_vpt(endb_.Vertexes[0]), _vpt(endb_.Vertexes[-1])]
                            say("   fillet chain %d: corner at %s - the floor's ends sit %.3f / %.3f mm from the offset ends; the end arcs' feet %.3f / %.3f mm from them" % (
                                _cid, np.round(Ja, 1).tolist(), min(np.linalg.norm(x_ - Oa_) for x_ in _fe), min(np.linalg.norm(x_ - Ob_) for x_ in _fe), min(np.linalg.norm(x_ - Oa_) for x_ in _ae), min(np.linalg.norm(x_ - Ob_) for x_ in _be)))
                        except Exception: pass
                    _nat_ = None
                    if not topP_:
                        
                        try:
                            _Fn = Part.Face(surf_)
                            if _Fn.isValid():
                                try: _Fn.check(True); _nok = True
                                except Exception: _nok = False
                                if _nok:
                                    _ed = [e_ for e_ in _Fn.Edges if e_.Length > 1e-6]
                                    def _match(e0_):
                                        m0_ = e0_.valueAt(0.5 * (e0_.FirstParameter + e0_.LastParameter))
                                        return min(_ed, key=lambda e_: abs(e_.Length - e0_.Length) + (e_.valueAt(0.5 * (e_.FirstParameter + e_.LastParameter)) - m0_).Length)
                                    _ma, _mb, _mf = _match(enda_), _match(endb_), _match(arc_)
                                    _off = max(float(x_.distToShape(Part.Vertex(y_.valueAt(y_.FirstParameter + (y_.LastParameter - y_.FirstParameter) * q_ / 10.0)))[0]) for x_, y_ in ((_ma, enda_), (_mb, endb_), (_mf, arc_)) for q_ in range(11))
                                    if len({_ma.hashCode(), _mb.hashCode(), _mf.hashCode()}) == 3 and _off <= 1e-3: _nat_ = (_Fn, _ma, _mb, _mf, _off)
                                    else: say("   fillet chain %d: the apex patch at %s - the rotation patch's own edges do not match its three edges (%.4f mm off) - the ladder spans it" % (_cid, np.round(Ja, 1).tolist(), _off))
                                else: say("   fillet chain %d: the apex patch at %s - the rotation patch's own face fails check(True) - the ladder spans it" % (_cid, np.round(Ja, 1).tolist()))
                        except Exception as ex_nn: say("   fillet chain %d: the apex patch at %s - the rotation patch's own face could not be made (%s) - the ladder spans it" % (_cid, np.round(Ja, 1).tolist(), str(ex_nn)[:80]))
                    if _nat_ is not None:
                        _Fn, _ma, _mb, _mf, _off = _nat_
                        fa["ENDC"][ea_] = _ma; fa["arcs"][ea_] = (_ma, Ja); fb["ENDC"][eb_] = _mb; fb["arcs"][eb_] = (_mb, Ja); enda_, endb_, arc_ = _ma, _mb, _mf
                        rec_p["ready"] = _Fn; rec_p["sub"] = "FV"; eds_p = [_ma, _mb, _mf]; rec_p["corners"] += " - the rotation patch's own face, its edges the blends' end arcs and the floor (%.5f mm from the swept arcs), the apex a point (31bq ZZ (2))" % _off
                    elif not topP_:
                        
                        surf_f, how_f = _span_corner([enda_, endb_, arc_], "fillet chain %d: the apex patch at %s" % (_cid, np.round(Ja, 1).tolist()), None)
                        if surf_f is not None:
                            surf_ = surf_f; eds_p = [enda_, endb_, arc_]; rec_p["corners"] += " - spanned through its three edges (%s), the apex a point" % how_f; rec_p.update(_SPANC_BAL)      
                        else:
                            try: rec_p["ready"] = Part.Face(surf_); rec_p["sub"] = "FV"
                            except Exception as ex_nf: say("   fillet chain %d: the apex patch's natural face failed (%s) - built from its edges" % (_cid, str(ex_nf)[:80]))
                    PIVOTS.append((A, surf_, eds_p, rec_p))
                    arcs_A[(fa["key"], ea_)] = arc_; arcs_A[(fb["key"], eb_)] = arc_
                    say("   fillet chain %d: CONVEX corner - the patch turns %.0f deg about the corner edge, %d edges (one arc's revolve would miss the other by %.2f mm); face %d's border there is the arc about the junction (%.2f mm)" % (_cid, abs(ang_), len(eds_p), gap_, A, arc_.Length))
                else:
                    X_ = None
                    for x1_ in _flat_e([fa["lines"][A][0]]):
                        for x2_ in _flat_e([fb["lines"][A][0]]):
                            X_ = X_ if X_ is not None else VX.cross_point(x1_, x2_, 0.6)
                    if X_ is None:
                        say("   fillet chain %d: CONCAVE corner at %s but the two offset lines on face %d do not cross within 0.6 mm - no mitre; both blends run to the junction as swept" % (_cid, np.round(Ja, 1).tolist(), A)); continue
                    dxa_, Xa_, _e = _nearest_on(_flat_e([fa["lines"][A][0]]), X_); dxb_, Xb_, _e = _nearest_on(_flat_e([fb["lines"][A][0]]), X_); dx_ = float(np.linalg.norm(Xa_ - Xb_))
                    if max(float(dxa_), float(dxb_)) > 0.05: say("   fillet chain %d: the mitre's X %s lies %.2f / %.2f mm off blends %s / %s's offset lines on face %d (beyond an end: the sweep did not reach it - the extend pass carries a member past a concave junction to X since 31bx K35; this corner may not close)" % (_cid, np.round(X_, 2).tolist(), float(dxa_), float(dxb_), fa.get("name"), fb.get("name"), A))
                    snap_ = dx_ <= 0.3      
                    Xm_ = Xa_ if snap_ else 0.5 * (Xa_ + Xb_)
                    one_ = None; how_one_ = "their surfaces' own intersection"
                    if snap_ and dab_ <= 0.05:
                        one_ = VX.true_mitre(Part.Face(fa["surf"]), Part.Face(fb["surf"]), Xa_, Qa2_)      
                    if one_ is not None: ma_ = mb_ = one_
                    else:
                        ma_ = VX.mitre_edge(Part.Face(fa["surf"]), Xm_, Qa_, Qb_, Xa_, Qa_); mb_ = VX.mitre_edge(Part.Face(fb["surf"]), Xm_, Qa_, Qb_, Xa_ if snap_ else Xb_, Qb_)
                        if snap_ and dab_ <= 0.05 and ma_ is not None:
                            # planar mitre
                            try:
                                _sx = Part.Face(fa["surf"]).section(Part.Face(fb["surf"])); _se = [e_ for e_ in _sx.Edges if e_.Length > 1e-6]
                                say("   fillet chain %d: the two blend surfaces' own intersection did not reach X and the contact (%d section edge(s); nearest %.2f / %.2f mm) - both blends take blend %s's planar mitre" % (_cid, len(_se), min([e_.distToShape(Part.Vertex(V3(*Xa_)))[0] for e_ in _se] + [9]), min([e_.distToShape(Part.Vertex(V3(*Qa2_)))[0] for e_ in _se] + [9]), fa.get("name")))
                            except Exception: pass
                            mb_ = ma_; one_ = ma_; how_one_ = "blend %s's planar mitre (their surfaces' own intersection stopped short of X or the contact)" % fa.get("name")
                            try:      # planar mitre
                                _qm = [ma_.valueAt(ma_.FirstParameter + (ma_.LastParameter - ma_.FirstParameter) * q_ / 20.0) for q_ in range(21)]
                                _gm = max(float(Part.Face(fb["surf"]).distToShape(Part.Vertex(p_))[0]) for p_ in _qm); how_one_ += " - blend %s lies %.2f mm from it%s" % (fb.get("name"), _gm, " (OVER the 0.30 mm print tolerance: that edge is off its face by as much - a defect of this corner, not a cosmetic)" if _gm > 0.30 else "")
                            except Exception: pass
                            try:      # planar mitre
                                _Fa2, _Fb2 = Part.Face(fa["surf"]), Part.Face(fb["surf"]); _cm = VX.true_mitre(_Fa2, _Fb2, Xa_, Qa2_, ok_gap=None)
                                if _cm is not None:
                                    _gc = VX.mitre_gap(_cm, (_Fa2, _Fb2)); _gp = VX.mitre_gap(ma_, (_Fa2, _Fb2))
                                    if _gc < _gp - 0.01:
                                        ma_ = mb_ = one_ = _cm; how_one_ = "their surfaces' own intersection CARRIED where the kernel's section gave out, %.2f mm from the blends at worst (blend %s's planar mitre lay %.2f from them; where the two blends only touch at the contact no curve lies on both)" % (_gc, fa.get("name"), _gp)
                            except Exception as _exm: say("   fillet chain %d: the carried mitre could not be compared with the planar one (%s)" % (_cid, str(_exm)[:80]))
                    if ma_ is None or mb_ is None:
                        say("   fillet chain %d: CONCAVE corner at %s - the mitre plane through X and the offset ends misses blend %s; left as swept" % (_cid, np.round(Ja, 1).tolist(), fa.get("name") if ma_ is None else fb.get("name"))); continue
                    _cut_line_at(fa, A, Xa_, Oa_); _cut_line_at(fb, A, Xb_, Ob_, snap_to=(Xa_ if snap_ else None))
                    if snap_: Xb_ = Xa_
                    sgx_ = VX.seg(Xa_, Xb_) if not snap_ else None
                    fa["ENDC"][ea_] = ma_; fa["arcs"][ea_] = (ma_, Ja); fa["PEND"][A][ea_] = Xa_; fa.setdefault("mitred", [False, False])[ea_] = True
                    fb["ENDC"][eb_] = mb_; fb["arcs"][eb_] = (mb_, Ja); fb["PEND"][A][eb_] = Xb_; fb.setdefault("mitred", [False, False])[eb_] = True
                    arcs_A[(fa["key"], ea_)] = sgx_; arcs_A[(fb["key"], eb_)] = sgx_
                    eds_s = [] if one_ is not None else [x_ for x_ in ([ma_, sga_] + list(cmid_ or []) + [sgb_, mb_, sgx_]) if x_ is not None]
                    if len(eds_s) >= 3:
                        topS_ = ([sga_] if sga_ is not None else []) + list(cmid_ or []) + ([sgb_] if sgb_ is not None else [])
                        slv_, how_s = _span_corner(eds_s, "fillet chain %d: the concave sliver at %s" % (_cid, np.round(Ja, 1).tolist()), VX.coons_patch(ma_, mb_, (sgx_ if sgx_ is not None else Xa_), topS_ if topS_ else Qa2_))
                        if slv_ is not None: PIVOTS.append((A, slv_, eds_s, dict(_SPANC_BAL, **{"span": "mitre", "sub": "FM", "corners": "the concave corner of blends %s and %s: the sliver between their two mitre edges (the offset ends %.2f mm apart on the side faces, the crossings %.2f mm apart on face %d)" % (fa.get("name"), fb.get("name"), dq_, dx_, A), "guides": 0, "fillet": fa["key"], "guide_after": 0.0, "nurbs_why": None, "folds": 0})))
                    say("   fillet chain %d: CONCAVE corner - %s" % (_cid, ("the two blends share ONE mitre: %s from X %s (face %d) to the contact, %.2f mm" % (how_one_, np.round(Xa_, 2).tolist(), A, ma_.Length)) if one_ is not None else ("the two blends mitred by the plane through X %s (face %d) and the offset ends: edges of %.2f / %.2f mm%s" % (np.round(Xa_, 2).tolist(), A, ma_.Length, mb_.Length, (" with a %d-edge sliver between them" % len(eds_s)) if len(eds_s) >= 3 else " - one mitre"))))
          if _pass == "settle" and _open_:
              # A MEMBER LEFT WITH AN OPEN END IS NOT MADE
              # corner edge
              
              _drop_ = [x_ for x_ in fls if x_.get("key") in _open_]
              for fx_ in _drop_:
                  FIL_MERGE.pop(fx_.get("key"), None)
                  if fx_.get("key") in _ch["keys"]: _ch["keys"].remove(fx_.get("key"))
                  mx_ = next((m2 for m2 in _ch["members"] if (("%d leg %s" % (int(m2["line"]), m2["leg"])) if m2.get("leg") is not None else str(int(m2["line"]))) == fx_.get("name")), None)
                  if mx_ is not None:
                      _ch.setdefault("failed", []).append(mx_)
                      for Jx_ in (mx_.get("_ends") or []):      
                          for m2 in _ch["members"]:
                              if m2 is mx_: continue
                              for e2_, J2_ in enumerate(m2.get("_ends") or []):
                                  if float(np.linalg.norm(np.asarray(J2_, float) - np.asarray(Jx_, float))) < 0.05 and str(e2_) in (m2.get("chain_c") or {}): m2["chain_c"][str(e2_)].pop("extend", None)
                  _owhy_ = _open_why.get(fx_.get("key"), "its freed end fits neither the taper nor the cap")
                  FIL_NOT_MADE.setdefault(int(fx_.get("chain", -1)), "an OPEN end in fillet chain %d (%s)" % (_cid, _owhy_[:600]))      
                  say("FILLET BY LINES on line %s: not made - an OPEN end in fillet chain %d (%s): its strips would not close on faces %d / %d, so the member is dropped and the chain's hole grows by it; its crease stays sharp, its neighbours' ends there are freed (31bq R6 / R7W, B04 (3))" % (fx_.get("name"), _cid, _owhy_, fx_["p"], fx_["q"]))
              fls = [x_ for x_ in fls if x_.get("key") not in _open_]; _open_.clear()
              _passes_.insert(_ip_, "settle")
        if not fls:      
            say("FILLET CHAIN %d: no member is made - face %d keeps its whole border there, every crease of the chain stays sharp" % (_cid, A)); continue
        # THE STRIPS
        order_ = []; left_ = list(range(len(fls))); nsub_ = 0; _subof = []
        
        _nm_of = lambda m__: ("%d leg %s" % (int(m__["line"]), m__["leg"])) if m__.get("leg") is not None else str(int(m__["line"]))
        _made_nm0 = set(str(fl_.get("name")) for fl_ in fls)
        def _shared_end(J_, own_):
            J_ = np.asarray(J_, float)
            return any(float(np.linalg.norm(np.asarray(x__, float) - J_)) < 0.05 for m__ in _ch["members"] if _nm_of(m__) != own_ for x__ in (m__.get("_ends") or []))
        def _far_side(J_):
            cur_ = np.asarray(J_, float); seen_ = set()
            for _ in range(len(_ch["members"])):
                nxt_ = None
                for m__ in _ch["members"]:
                    if _nm_of(m__) in _made_nm0 or id(m__) in seen_: continue
                    E__ = [np.asarray(x__, float) for x__ in (m__.get("_ends") or [])]
                    if len(E__) != 2: continue
                    for a__ in (0, 1):
                        if float(np.linalg.norm(E__[a__] - cur_)) < 0.05: nxt_ = (m__, E__[1 - a__])
                    if nxt_ is not None: break
                if nxt_ is None: break
                seen_.add(id(nxt_[0])); cur_ = nxt_[1]
            return cur_
        _lastJ = None
        while left_:
            _free = [(i_, e_) for i_ in left_ for e_ in (0, 1) if not fls[i_]["chain_end"][e_]]
            if _lastJ is not None and _free:
                _tgt = _far_side(_lastJ); start_, e_in = min(_free, key=lambda ie_: float(np.linalg.norm(np.asarray(fls[ie_[0]]["J"][ie_[1]], float) - _tgt)))
            elif _free:
                _outer_ = [ie_ for ie_ in _free if not _shared_end(fls[ie_[0]]["J"][ie_[1]], str(fls[ie_[0]].get("name")))]
                if _outer_: start_, e_in = _outer_[0]
                else:
                    
                    _hole_ = [ie_ for ie_ in _free if any(float(np.linalg.norm(np.asarray(x__, float) - np.asarray(fls[ie_[0]]["J"][ie_[1]], float))) < 0.05 for m__ in _ch["members"] if _nm_of(m__) not in _made_nm0 for x__ in (m__.get("_ends") or []))]
                    start_, e_in = (_hole_ or _free)[0]
                    if _hole_: say("   fillet chain %d: a closed chain - the strip starts at the hole (member %s's end at %s): the hole at its wrap keeps the missing member's crease as face %d's own border (31bq R7W)" % (_cid, fls[start_].get("name"), np.round(np.asarray(fls[start_]["J"][e_in], float), 1).tolist(), A))
            else: start_ = left_[0]; e_in = 0 if not fls[start_]["chain_end"][0] else 1
            cur_ = start_; nsub_ += 1
            while cur_ is not None and cur_ in left_:
                left_.remove(cur_); fl_ = fls[cur_]; e_out = 1 - e_in; order_.append((cur_, e_in, e_out)); _subof.append(nsub_)
                Jo = np.asarray(fl_["J"][e_out], float); nxt_ = None; _lastJ = Jo
                for j_ in left_:
                    for x_ in (0, 1):
                        if np.linalg.norm(np.asarray(fls[j_]["J"][x_], float) - Jo) < 0.05: nxt_ = (j_, x_)
                if nxt_ is None: break
                cur_, e_in = nxt_
        if nsub_ > 1: say("   fillet chain %d: %d sub-chains (a hole where a member was not made - the ends beside it taper)" % (_cid, nsub_))
        strip_A = []; dropA_ = []; _sub_rng = []      
        for _oi, (i_, e_in, e_out) in enumerate(order_):
            fl_ = fls[i_]; _n0 = len(strip_A)
            if fl_["ends"][A][e_in] is not None and not fl_["chain_end"][e_in]: strip_A.append(fl_["ends"][A][e_in])
            strip_A += _flat_e([fl_["lines"][A][0]])
            if fl_["ends"][A][e_out] is not None and not fl_["chain_end"][e_out]: strip_A.append(fl_["ends"][A][e_out])
            arc_ = arcs_A.get((fl_["key"], e_out))
            if arc_ is not None: strip_A.append(arc_)
            if not _sub_rng or _sub_rng[-1][4] != _subof[_oi]: _sub_rng.append([_n0, len(strip_A) - 1, (i_, e_in), (i_, e_out), _subof[_oi]])
            else: _sub_rng[-1][1] = len(strip_A) - 1; _sub_rng[-1][3] = (i_, e_out)
            dropA_ += list(_flat_e([ALL_E[fl_["key"]]]))
            for e_ in (0, 1):
                m_ = fl_["meet"][A][e_]
                if not fl_["chain_end"][e_] and m_ is not None and m_.get("chain") is not None:
                    try: dropA_ += _frags(int(m_["chain"]), np.asarray(fl_["J"][e_], float), fl_.get("name", "?"))
                    except (_Uncut, SystemExit): say("   fillet chain %d: member %s's free end - the border %d was not cut; its fragment stays" % (_cid, fl_.get("name"), int(m_["chain"])))
        # THE HOLE'S OWN TWO POINTS
        
        def _term_A(i__, e__):
            fl__ = fls[i__]
            if fl__["ends"][A][e__] is not None and not fl__["chain_end"][e__]: return np.asarray(fl__["J"][e__], float)
            return np.asarray(fl__["PEND"][A][e__], float)      
        def _snap_v(e__, P__):
            vs__ = [_vpt(v_) for v_ in (e__.Vertexes[0], e__.Vertexes[-1])]; d__ = [float(np.linalg.norm(v_ - P__)) for v_ in vs__]; j__ = int(np.argmin(d__))
            return vs__[j__], d__[j__]
        _bnd = {}      
        for s_ in range(len(_sub_rng) - 1):
            a_, b_ = _sub_rng[s_], _sub_rng[s_ + 1]
            try:
                pa0_, da0_ = _snap_v(strip_A[a_[1]], _term_A(*a_[3])); pb0_, db0_ = _snap_v(strip_A[b_[0]], _term_A(*b_[2]))
                _bnd[a_[1]] = (pa0_, pb0_, da0_, db0_, fls[a_[3][0]].get("name"), fls[b_[2][0]].get("name"))
            except Exception as ex_bd: say("   fillet chain %d: the walk's boundary %d could not be read (%s) - that gap is measured by the nearest vertex pair (31bq R7W)" % (_cid, s_, str(ex_bd)[:80]))
        gaps_ = []
        for i_ in range(len(strip_A) - 1):
            if i_ in _bnd: g_ = float(np.linalg.norm(_bnd[i_][0] - _bnd[i_][1]))      
            else:
                e1_, e2_ = strip_A[i_], strip_A[i_ + 1]
                v1_ = [_vpt(v_) for v_ in (e1_.Vertexes[0], e1_.Vertexes[-1])]; v2_ = [_vpt(v_) for v_ in (e2_.Vertexes[0], e2_.Vertexes[-1])]
                g_ = min(np.linalg.norm(a_ - b_) for a_ in v1_ for b_ in v2_)
            if g_ > 0.01: gaps_.append((i_, round(float(g_), 3)))
        if gaps_:
            
            _made_nm = set(str(fl_.get("name")) for fl_ in fls)
            _miss_lines = sorted(set(int(m__["line"]) for m__ in _ch["members"] if ((("%d leg %s" % (int(m__["line"]), m__["leg"])) if m__.get("leg") is not None else str(int(m__["line"]))) not in _made_nm)))
            _miss_edges = [m__["_edge"] for m__ in _ch["members"] if _nm_of(m__) not in _made_nm and m__.get("_edge") is not None]      
            def _off_miss(P__):
                try: return min(float(x__.distToShape(Part.Vertex(V3(*P__)))[0]) for x__ in _miss_edges)
                except Exception: return 9e9
            _filled = []; _unclosed = []; _refused = []      
            for (_gi, _gmm) in sorted(gaps_, reverse=True):
                e1_, e2_ = strip_A[_gi], strip_A[_gi + 1]
                if _gi in _bnd:
                    
                    pa_, pb_ = _bnd[_gi][0], _bnd[_gi][1]; _oa, _ob = _off_miss(pa_), _off_miss(pb_)
                    if _oa <= 0.05 and _ob <= 0.05:
                        path_ = _crease_path(pa_, pb_, _miss_lines, only=_miss_edges) or _crease_path(pa_, pb_, _miss_lines, cut=False, only=_miss_edges)
                        if path_:
                            strip_A[_gi + 1:_gi + 1] = path_; dropA_ += [x_ for x_ in path_ if not any(x_.isSame(y_) for y_ in dropA_)]      
                            _filled.append((_gi, round(float(_gmm), 2), "%d crease piece(s), %.2f mm, between the walk's own ends (after %s, before %s)" % (len(path_), sum(x_.Length for x_ in path_), _bnd[_gi][4], _bnd[_gi][5])))
                            continue
                        _refused.append((_gi, round(float(_gmm), 2), "no path of the missing member(s) %s's crease pieces joins the walk's ends (after %s, before %s)" % (_miss_lines, _bnd[_gi][4], _bnd[_gi][5])))
                    else: _refused.append((_gi, round(float(_gmm), 2), "the walk's ends (after %s, before %s) lie %.2f / %.2f mm off the missing member(s) %s's crease" % (_bnd[_gi][4], _bnd[_gi][5], _oa, _ob, _miss_lines)))
                    continue
                v1_ = [_vpt(v_) for v_ in (e1_.Vertexes[0], e1_.Vertexes[-1])]; v2_ = [_vpt(v_) for v_ in (e2_.Vertexes[0], e2_.Vertexes[-1])]
                pa_, pb_ = min(((a_, b_) for a_ in v1_ for b_ in v2_), key=lambda ab_: np.linalg.norm(ab_[0] - ab_[1]))

                path_ = _crease_path(pa_, pb_, _miss_lines, only=_miss_edges) or _crease_path(pa_, pb_, _miss_lines, cut=False, only=_miss_edges)      
                if path_:
                    strip_A[_gi + 1:_gi + 1] = path_; dropA_ += [x_ for x_ in path_ if not any(x_.isSame(y_) for y_ in dropA_)]      
                    _filled.append((_gi, round(float(_gmm), 2), "%d crease piece(s), %.2f mm" % (len(path_), sum(x_.Length for x_ in path_))))
                else:      
                    try:
                        seg_ = Part.LineSegment(V3(*pa_), V3(*pb_)).toShape(); _offg_, _offs_ = _seg_off_face(seg_, A)
                        if _offg_ is None: _unclosed.append((_gi, round(float(_gmm), 2), "NOT MEASURED"))
                        elif _offg_ > THIN_FIL: _unclosed.append((_gi, round(float(_gmm), 2), round(float(_offg_), 2)))
                        else: strip_A.insert(_gi + 1, seg_); _filled.append((_gi, round(float(_gmm), 2), "a straight end line %.2f, on the face within %.3f mm of its own mesh%s" % (seg_.Length, _offg_, "" if _offs_ is None else " (%.3f mm of its surface)" % _offs_)))
                    except Exception: pass
            if _filled: say("   fillet chain %d: face %d's strip had gap(s) %s where a member is missing or stands with an open end - closed by the missing member's own crease piece, else a straight end line on the face (index, gap mm, piece): %s - the crease stays sharp there (31bq B04)" % (_cid, A, gaps_, _filled))
            if _refused: say("   fillet chain %d: face %d's strip gap(s) at a HOLE NOT closed (index, gap mm, why): %s - a hole between two sub-chains is closed only by the missing member(s)' own crease between the walk's own two ends; nothing is drawn across the face there (31bq R7W, M2)" % (_cid, A, _refused))
            if _unclosed: say("   fillet chain %d: face %d's strip gap(s) NOT closed (index, gap mm, how far a straight line would leave the face - against its own mesh): %s - no missing member's crease spans them and a straight line between their ends is no border of face %d (over the print tolerance %g, or NOT MEASURED): no edge is handed to a face it does not lie on; the strip stays open there - a member beside it stands with an OPEN end (31bq R6 / R7W, B04 (3))" % (_cid, A, _unclosed, A, THIN_FIL))
            if not _filled and not _unclosed and not _refused: say("   fillet chain %d: face %d's strip is NOT end to end - gap(s) %s between consecutive edges (index, mm) of %s" % (_cid, A, gaps_, [round(x_.Length, 2) for x_ in strip_A]))
        if os.environ.get("FIL_DBG") == "1":
            try: Part.makeCompound(strip_A).exportBrep(os.path.join(SK, "fillet_chain_%d_strip.brep" % _cid))
            except Exception: pass
        if kind[A] == "orig":
            ORIG_FIL.setdefault(A, {"drop": [], "add": []}); ORIG_FIL[A]["drop"] += dropA_; ORIG_FIL[A]["add"] += strip_A
            ORIG_FIL_SRC.setdefault(A, []).extend(("fillet chain %d's common strip" % _cid, x_) for x_ in strip_A)      
            for fl_ in fls: FIL_HOLD[(fl_["key"], A)] = dropA_ + strip_A
            say("   fillet chain %d: original face %d keeps its surface, trimmed by the chain's offset lines and corner arcs (%d edge(s) out, %d in)" % (_cid, A, len(dropA_), len(strip_A)))
        else:
            SPLITS.setdefault(A, []).append(({"role": "split", "kind": "CUBIC", "why": "fillet chain %d by lines" % _cid, "fillet": fls[0]["key"], "chain_keys": [fl_["key"] for fl_ in fls]}, strip_A))
        side_strips = []      
        for fl_ in fls:
            f = fl_["q"] if fl_["p"] == A else fl_["p"]
            chain_ = []
            if fl_["ends"][f][0] is not None and not fl_["chain_end"][0]: chain_.append(fl_["ends"][f][0])
            if fl_["chain_end"][0] and cseg_.get((fl_["key"], 0)) is not None: chain_.append(cseg_[(fl_["key"], 0)])
            chain_ += list(_flat_e([fl_["lines"][f][0]]))
            if fl_["ends"][f][1] is not None and not fl_["chain_end"][1]: chain_.append(fl_["ends"][f][1])
            if fl_["chain_end"][1] and cseg_.get((fl_["key"], 1)) is not None: chain_.append(cseg_[(fl_["key"], 1)])
            frag_ = []
            for e_ in (0, 1):
                m_ = fl_["meet"][f][e_]
                if fl_["chain_end"][e_]: frag_ += cfrag_.get((fl_["key"], e_), [])
                elif m_ is not None and m_.get("chain") is not None:
                    try: frag_ += _frags(int(m_["chain"]), np.asarray(fl_["J"][e_], float), fl_.get("name", "?"))
                    except (_Uncut, SystemExit): say("   fillet chain %d: member %s's free end on face %d - the border %d was not cut; its fragment stays" % (_cid, fl_.get("name"), f, int(m_["chain"])))
            _vs = _VX_SIDE.get((fl_["key"], int(f)))      # corner edge
            if _vs is not None:
                chain_ = list(chain_) + list(_vs["c_off"]) + list(_vs["c_top_end"])
                mt_ = _vs.get("c_top_meet")
                if mt_ is not None and mt_.get("chain") is not None:
                    try: frag_ += _frags(int(mt_["chain"]), _vs["c_J_top"], "%d (the corner edge's blend)" % _vs["c_key"])
                    except (_Uncut, SystemExit): say("   fillet chain %d: the corner edge %d's blend's top end on face %d - the border %d was not cut; its fragment stays" % (_cid, _vs["c_key"], f, int(mt_["chain"])))
                fl_["_vx_crease"] = list(_vs["c_crease"]); fl_["_vx_ckey"] = _vs["c_key"]
                say("   fillet chain %d: face %d's strip is the L of member %s's offset and the corner edge %d's blend's (%d edge(s)) - 31bq R7v" % (_cid, f, fl_.get("name"), _vs["c_key"], len(chain_)))
            side_strips.append((f, fl_, chain_, frag_))
        
        def _ends_of(ch_):
            vs_ = [_vpt(v_) for e_ in ch_ for v_ in (e_.Vertexes[0], e_.Vertexes[-1])]
            return [v_ for v_ in vs_ if sum(1 for w_ in vs_ if np.linalg.norm(v_ - w_) < 0.05) == 1]
        
        groups_ = [(f, [fl_], list(chain_), list(frag_)) for f, fl_, chain_, frag_ in side_strips]
        for f, mems_, chain_, frag_ in groups_:
            if kind[f] == "orig":
                fl_ = mems_[0]
                strip_ = list(_flat_e([ALL_E[fl_["key"]]])) + frag_ + list(fl_.get("_vx_crease") or []); FIL_HOLD[(fl_["key"], f)] = strip_ + chain_      # corner edge
                if fl_.get("_vx_ckey") is not None: FIL_HOLD[(int(fl_["_vx_ckey"]), f)] = strip_ + chain_
                ORIG_FIL.setdefault(f, {"drop": [], "add": []}); ORIG_FIL[f]["drop"] += strip_; ORIG_FIL[f]["add"] += chain_
                ORIG_FIL_SRC.setdefault(f, []).extend(("fillet chain %d member %s's strip" % (_cid, fl_.get("name")), x_) for x_ in chain_)      
                say("   fillet chain %d: original face %d keeps its surface, trimmed by member %s's offset line (%d edge(s) out, %d in)" % (_cid, f, fl_.get("name"), len(strip_), len(chain_)))
            else:
                names_ = " + ".join(str(m_.get("name")) for m_ in mems_)
                if len(mems_) > 1: say("   fillet chain %d: members %s share an end on face %d - their strips one split chain of %d edge(s)" % (_cid, names_, f, len(chain_)))
                SPLITS.setdefault(f, []).append(({"role": "split", "kind": "CUBIC", "why": "fillet chain %d, member%s %s, by lines" % (_cid, "s" if len(mems_) > 1 else "", names_), "fillet": mems_[0]["key"], "chain_keys": [m_["key"] for m_ in mems_]}, chain_ if len(chain_) > 1 else chain_[0]))
        say("FILLET CHAIN %d: %d member(s) assembled round face %d - %d corner face(s), the face's strip one chain of %d edge(s)" % (_cid, len(fls), A, sum(1 for h_, _s, _e, _r in PIVOTS if h_ == A), len(strip_A)))
        try: say("   fillet chain %d: the members' strip ends on face %d (31bq R7W): %s" % (_cid, A, "; ".join("%s %s %s" % (fl_.get("name"), np.round(_term_A(i_, 0), 3).tolist(), np.round(_term_A(i_, 1), 3).tolist()) for i_, fl_ in enumerate(fls))))      
        except Exception: pass
    except Exception as ex_c:
        import traceback as _tb; _fr = _tb.extract_tb(sys.exc_info()[2])[-1]
        say("FILLET CHAIN %d: the corners could not be made - %s (%s line %d); its members stand as single blends with their ends as swept" % (_cid, str(ex_c)[:300], os.path.basename(_fr.filename), _fr.lineno))
for _kv9, _V9 in sorted((globals().get("_VERTEX_C") or {}).items()):      # corner edge  recorded
    if _V9.get("done") or int(_kv9) not in FILLET_LINES or int(_kv9) in FIL_MERGE: continue      
    # 31br D1 (c)
    # corner edge
    
    _sd9 = globals().get("_sweep_declined"); _made9 = set()
    for _fl9 in (FIL_MERGE or {}).values():
        try: _made9.add(int((_fl9 or {}).get("chain")))
        except (TypeError, ValueError): pass
    _nm9 = sorted(int(m__) for m__ in (_V9.get("members") or []) if int(m__) not in _made9)
    if _nm9:
        _w9c = "NOT made as a single blend: the chain member(s) %s at its junction %s were NOT made (%s) - a blend on the corner edge beside a sharp member's crease cuts the side face to a wedge no rung spans; the corner edge stays sharp with them (lower R there or make room, then both are made) (31br D1 (c))" % (
            _nm9, np.round(np.asarray(_V9.get("J"), float), 1).tolist(), "; ".join("%d: %s" % (m__, str(FIL_NOT_MADE.get(m__, "not swept"))[:120]) for m__ in _nm9))
        FIL_NOT_MADE.setdefault(int(_kv9), _w9c); say("   the corner edge %d's fillet: %s" % (int(_kv9), _w9c)); continue
    if _sd9:
        _V9["_final"] = True; _sd9(int(_kv9), _V9)
    if int(_kv9) in FIL_MERGE or int(_kv9) in FIL_NOT_MADE: continue
    _w9 = "held for the vertex ball of fillet chain %s at %s, which %s - not made by lines; the corner edge stays sharp in this pass" % (_V9.get("cid"), np.round(np.asarray(_V9.get("J"), float), 1).tolist(), "was declined (the line above says why)" if _V9.get("single") else "no vertex pass reached (a member at that junction was not made, or the chain's corners failed)")
    FIL_NOT_MADE.setdefault(int(_kv9), _w9); say("   the corner edge %d's fillet: %s (31bq R7W merge-B26)" % (int(_kv9), _w9))
if PLANE and FIT != "span":
    for pi in chg:
        vt = np.unique(F[pid == pi].ravel())
        if len(vt) < 6: continue
        flat, p95_, max_, c0, e1, e2, n0 = K.is_flat(Vu[vt], PLANE_P95, PLANE_MAX)
        if not flat: continue
        a1 = (Vu[vt] - c0) @ e1; a2 = (Vu[vt] - c0) @ e2; m_ = 3.0
        cn = [[c0 + (a1.min() - m_) * e1 + (a2.min() - m_) * e2, c0 + (a1.min() - m_) * e1 + (a2.max() + m_) * e2],
              [c0 + (a1.max() + m_) * e1 + (a2.min() - m_) * e2, c0 + (a1.max() + m_) * e1 + (a2.max() + m_) * e2]]
        pb = Part.BSplineSurface(); pb.buildFromPolesMultsKnots([[V3(*cn[i][j]) for j in range(2)] for i in range(2)], [2, 2], [2, 2], [0.0, 1.0], [0.0, 1.0], False, False, 1, 1)
        PAT[pi] = _Surf(pb); nplane += 1
        recs[pi] = {"plane": True, "plane_p95": round(p95_, 4), "plane_max": round(max_, 4)}
        say("FLAT face %d: its voxel lies on a plane (p95 %.3f, max %.3f mm) - the face is that plane" % (pi, p95_, max_))
if FIT == "span":
    say("FACE LADDER (31aw): %d face(s) kept on the original surface (the layout's rung 1); %d SPANNED BY THEIR EDGES and the lines added inside them (a planar boundary = a plane) - no fit to the voxel"
        % (sum(1 for k in kind if k == "orig"), len(chg)))
else:
    say("FACE LADDER: %d face(s) kept on the original surface (the layout's rung 1), %d flat (rung 2), %d to be fitted (rung 3: LAM %g, CTRL_MM %g%s)"
        % (sum(1 for k in kind if k == "orig"), nplane, len(chg) - nplane, LAM, CTRL_MM, ", SYMFIT across %s" % MIRROR_S if (MP is not None and SYMFIT) else ""))
def order_loops(eds, tol=1e-3):
    def P_(v): return np.array([v.X, v.Y, v.Z])
    left = list(eds); loops = []
    while left:
        out = [left.pop(0)]; head = P_(out[0].Vertexes[0]); tail = P_(out[0].Vertexes[-1])
        while left and np.linalg.norm(tail - head) > tol or (left and len(out) == 1):
            best = None
            for k, e in enumerate(left):
                a, b = P_(e.Vertexes[0]), P_(e.Vertexes[-1])
                for d, rev in ((np.linalg.norm(a - tail), False), (np.linalg.norm(b - tail), True)):
                    if best is None or d < best[0]: best = (d, k, rev)
            if best[0] > tol: break
            e = left.pop(best[1]); out.append(e.reversed() if best[2] else e); tail = P_(e.Vertexes[0]) if best[2] else P_(e.Vertexes[-1])
        loops.append(out)
    return loops
HOLE_EDGES = {}      
def _wire_closed(L):
    """an ordered loop of edges closes (the kernel's own test, with its tolerances; the loop ends met within 1e-3 mm by order_loops)"""
    try: return bool(Part.Wire(list(L)).isClosed())
    except Exception: return False
def _edge_origin(e_, i_):
    """31bq PP (B20 (1)): where an edge of face i came from - its own border chain, a FOREIGN chain's piece (with that chain's faces), a fillet strip's edge
    handed to it (ORIG_FIL_SRC), or nothing the build knows (the NOT VALID line had printed "chain None" for the very edge it had to name)"""
    k_ = _chain_of(e_, i_)
    if k_ is not None: return "chain %d" % k_
    try:
        m_ = e_.valueAt(0.5 * (e_.FirstParameter + e_.LastParameter))
        _same = lambda x_: x_.isSame(e_) or (x_.valueAt(0.5 * (x_.FirstParameter + x_.LastParameter)) - m_).Length <= 1e-3
        for src_, x_ in ORIG_FIL_SRC.get(i_, []):
            if _same(x_): return "an edge of %s, handed to this face" % src_
        
        _p3 = [e_.valueAt(e_.FirstParameter + (e_.LastParameter - e_.FirstParameter) * t_) for t_ in (0.25, 0.5, 0.75)]
        for _tab3, _nm3 in ((SPLITS, "split"), (GUIDES, "added line")):
            for g3_, se3_ in _tab3.get(i_, []):
                for x_ in _split_edges(se3_):
                    try:
                        if max(float(x_.distToShape(Part.Vertex(q_))[0]) for q_ in _p3) <= 1e-3: return "the %s '%s' of this face%s" % (_nm3, str(g3_.get("why", ""))[:60], (" (the kit's, for fillet %s)" % g3_.get("fillet")) if g3_.get("fillet") is not None else "")
                    except Exception: continue
        for kk_ in range(len(ALL_E)):
            if ALL_E[kk_] is not None and any(_same(x_) for x_ in _flat_e([ALL_E[kk_]])):
                return "a FOREIGN edge - a piece of chain %d (faces %s), not a border of this face" % (kk_, CH[kk_]["pair"] if kk_ < len(CH) else "a wall edge")
    except Exception: pass
    return "an edge of no chain and no recorded strip"
def _chain_of(e_, i_):
    """the chain whose edge is e_ (a face's edge after the face was made is a new object: matched by its mid point, within 1e-3 mm)"""
    try:
        m_ = e_.valueAt(0.5 * (e_.FirstParameter + e_.LastParameter))
        for k_ in pch.get(i_, []):
            for x_ in _flat_e([ALL_E[k_]]):
                if (x_.valueAt(0.5 * (x_.FirstParameter + x_.LastParameter)) - m_).Length <= 1e-3 or x_.isSame(e_): return k_
    except Exception: pass
    return None
def _clip_guides(gp_, polys_, pi_):
    """31br D2 (2026-10-29; the agent's d3: a guide ending on a decided fillet's crease was handed WHOLE to its face in the LINES pass - its points inside the strip pulled the fill into the blend: 6 free edges,
    then a 0.36 mm self-intersection): in the lines pass a guide is CLIPPED to the face's loop of THIS pass - the loop's points fitted with a plane, the guide's points outside the loop's polygon in it
    dropped (the end that lay inside a fillet strip ends at the last point inside); a guide left with one point is dropped; said. The sharp pass's guides lie on the face by construction (no clip)"""
    if not os.environ.get("FILLET_LINES") or not gp_ or not polys_: return gp_
    
    _cre_ = []
    try:
        for _flc in (FIL_MERGE or {}).values():
            if int(_flc.get("p", -1)) == int(pi_) or int(_flc.get("q", -1)) == int(pi_):
                _kc_ = int(_flc.get("chain")); _ec_ = ALL_E[_kc_] if 0 <= _kc_ < len(ALL_E) else None
                if _ec_ is None: continue
                _cre_.append((np.vstack([samples(x_, 0.3) for x_ in _flat_e([_ec_])]), 2.5 * float(_flc.get("r", 0.0)) + 0.30))
    except Exception: _cre_ = []
    if not _cre_: return gp_
    try:
        Lp_ = np.vstack([np.asarray(P_, float) for P_ in polys_]); c_ = Lp_.mean(0); _, _, vh_ = np.linalg.svd(Lp_ - c_, full_matrices=False); e1_, e2_ = vh_[0], vh_[1]
        poly2_ = np.stack([(Lp_ - c_) @ e1_, (Lp_ - c_) @ e2_], 1); out_ = []
        for gi_, G_ in enumerate(gp_):
            G_ = np.asarray(G_, float); ins_ = SP._inside((G_ - c_) @ e1_, (G_ - c_) @ e2_, poly2_)
            _near_ = np.zeros(len(G_), bool)
            for _Pc, _reach in _cre_: _near_ |= np.linalg.norm(G_[:, None, :] - _Pc[None, :, :], axis=2).min(1) <= _reach
            ins_ = ins_ | ~_near_      
            if ins_.all(): out_.append(G_); continue
            keep_ = G_[ins_]
            if len(keep_) >= 2: out_.append(keep_)
            say("face %d: added line %d clipped to the face's loop of this pass - %d of %d points lay outside it (inside a fillet strip): %s (31br D2)" % (pi_, gi_, int((~ins_).sum()), len(G_), ("%d points kept" % len(keep_)) if len(keep_) >= 2 else "dropped (one point left)"))
        return out_
    except Exception as ex_: say("face %d: the guides could not be clipped to the loop (%s) - handed whole" % (pi_, str(ex_)[:80])); return gp_
# crumpled

# skin-wires

_A3_TWIN, _A3_MASTER, _A3_RIM = {}, set(), {}
if FIT == "span" and MP is not None and TWIN_MIRROR:
    _cen3 = {}
    for p3 in chg:
        T3 = F[pid == p3]
        if len(T3): _cen3[p3] = Vu[T3].mean(1).mean(0)
    _A3_TWIN, _A3_MASTER = SP.twin_pairs(_cen3, MP[0], MP[1], TWIN_CEN_MM)
    if _A3_TWIN:
        chg = sorted(chg, key=lambda p3: (0 if (p3 not in _A3_TWIN or p3 in _A3_MASTER) else 1, p3))
        say("TWINS (31br A3): %d changed face pair(s) across %s - the master (+ side) spanned first, the twin takes the master's surface REFLECTED onto its own loop: %s; %d changed face(s) span the plane or have no twin"
            % (len(_A3_MASTER), MIRROR_S, ", ".join("%d -> %d" % (m3, _A3_TWIN[m3]) for m3 in sorted(_A3_MASTER)), len(chg) - 2 * len(_A3_MASTER)))
elif FIT == "span" and MP is not None:
    say("TWINS (31br A3): TWIN_MIRROR=0 - every changed face is spanned apart; twins may come out unalike (the agent's d19b)")
def _a3_reflect(S_):
    """the surface mirrored in the card's plane (Shape.mirror on the face made of it; its Surface is the mirrored geometry with the location applied)"""
    f_ = S_.toShape() if hasattr(S_, "toShape") else Part.Face(S_)
    f_ = f_.mirror(V3(*(MP[0] * MP[1])), V3(*MP[0]))
    return f_.Faces[0].Surface if f_.Faces else f_.Surface
def _a3_rim(S_, polys_):
    """how far the surface sits from the loop's points (the rim) - sk_span's own measure"""
    rim_ = np.vstack([np.asarray(P_, float)[::max(1, len(P_) // 40)] for P_ in polys_])
    return float(SP._dev(S_, rim_))
def _a3_side(P_):
    return float(K.mirror_side(np.asarray(P_, float)[None, :], MP[0], MP[1])[0])
def _a3_mirror_surface(pi_, polys_, mid_, subs_now=None):
    """(kind, surface, info) for a twin piece / face from its master's built surface, or None with the reason said. Two masters: (1) the twin FACE's master across the plane
    (the whole face, or the piece whose reflected midpoint is mid_); (2) on a face that SPANS the plane and is split (the agent's belly: the keel-line split on x 0, pieces E / F
    and the flares A / D), the - side piece's master is the + side piece of the SAME face already built in this run (subs_now), matched by its reflected midpoint"""
    m_ = _A3_TWIN.get(pi_)
    if m_ is None and mid_ is not None and subs_now is not None and MP is not None and _a3_side(mid_) < -0.3:
        best_ = None
        for S_s, eds_s, inf_s in subs_now:
            try: c_s = np.vstack(SP.edge_polys(eds_s)).mean(0)
            except Exception: continue
            if _a3_side(c_s) < 0.3 or inf_s.get("mirror_of_sub") is not None: continue      
            d_ = float(np.linalg.norm(K.reflect(c_s[None, :], MP[0], MP[1])[0] - np.asarray(mid_, float)))
            if best_ is None or d_ < best_[0]: best_ = (d_, S_s, inf_s)
        if best_ is None or best_[0] > TWIN_CEN_MM: return None      
        S_m, inf_m = best_[1].bs, best_[2]; kind_m = inf_m.get("span"); sub_m = inf_m.get("sub"); rim_m = _A3_RIM.get((pi_, sub_m)); m_ = pi_
        if kind_m in (None, "plane"): return None
        try: S_t = _a3_reflect(S_m)
        except Exception as ex_: say("   face %d: piece %s's surface could not be reflected (%s) - this piece is spanned on its own (31br A3)" % (pi_, sub_m, str(ex_)[:80])); return None
        try: rim_t = _a3_rim(S_t, polys_)
        except Exception: rim_t = 9e9
        allow_ = max(float(rim_m if rim_m is not None else SP.NURBS_RIM), SP.NURBS_RIM) + TWIN_RIM_PLUS
        if rim_t > allow_:
            say("   face %d: its own + side piece %s's surface reflected misses this - side piece's rim by %.3f mm (the + piece held %s; allowed %.3f): spanned on its own (31br A3)" % (pi_, sub_m, rim_t, ("%.3f" % rim_m) if rim_m is not None else "?", allow_)); return None
        info_ = {"how": "the MIRROR of this face's own + side piece %s's %s surface (31br A3): rim on this piece's own edges %.3f mm (the + piece's %s)" % (sub_m, kind_m, rim_t, ("%.3f" % rim_m) if rim_m is not None else "?"),
                 "guides": 0, "nu": getattr(S_t, "NbUPoles", 0), "nv": getattr(S_t, "NbVPoles", 0), "folds": 0, "mirror_of_face": pi_, "mirror_of_sub": sub_m, "rim_mm": round(rim_t, 4), "nurbs": (kind_m == "nurbs")}
        return kind_m, S_t, info_
    if m_ is None or pi_ in _A3_MASTER or m_ not in PAT: return None
    if recs.get(m_, {}).get("fail"):
        say("   face %d: its master face %d FAILED to span - this twin is spanned on its own (31br A3)" % (pi_, m_)); return None
    src_ = PAT[m_]; kind_m = None; S_m = None; sub_m = None
    if isinstance(src_, list):
        if mid_ is None: return None
        best_ = None
        for S_s, eds_s, inf_s in src_:
            try: c_s = np.vstack(SP.edge_polys(eds_s)).mean(0)
            except Exception: continue
            d_ = float(np.linalg.norm(K.reflect(c_s[None, :], MP[0], MP[1])[0] - np.asarray(mid_, float)))
            if best_ is None or d_ < best_[0]: best_ = (d_, S_s, inf_s)
        if best_ is None or best_[0] > TWIN_CEN_MM:
            say("   face %d: no piece of its master face %d reflects onto this piece (nearest %.2f mm) - spanned on its own (31br A3)" % (pi_, m_, best_[0] if best_ else 9e9)); return None
        S_m, inf_m = best_[1].bs, best_[2]; kind_m = inf_m.get("span"); sub_m = inf_m.get("sub"); rim_m = _A3_RIM.get((m_, sub_m))
    else:
        if mid_ is not None: return None      
        S_m = src_.bs; kind_m = recs.get(m_, {}).get("span"); rim_m = _A3_RIM.get(m_)
    if S_m is None or kind_m in (None, "plane"): return None      
    try: S_t = _a3_reflect(S_m)
    except Exception as ex_: say("   face %d: its master's surface could not be reflected (%s) - spanned on its own (31br A3)" % (pi_, str(ex_)[:80])); return None
    try: rim_t = _a3_rim(S_t, polys_)
    except Exception: rim_t = 9e9
    allow_ = max(float(rim_m if rim_m is not None else SP.NURBS_RIM), SP.NURBS_RIM) + TWIN_RIM_PLUS
    if rim_t > allow_:
        say("   face %d: its master face %d%s's surface reflected misses THIS face's own rim by %.3f mm (the master held its own within %s; allowed %.3f) - the two loops are not mirrors here (the body's own wall edges?): spanned on its own (31br A3)"
            % (pi_, m_, (" piece %s" % sub_m) if sub_m else "", rim_t, ("%.3f" % rim_m) if rim_m is not None else "?", allow_)); return None
    info_ = {"how": "the MIRROR of master face %d%s's %s surface (31br A3): rim on this face's own edges %.3f mm (the master's %s)" % (m_, (" piece %s" % sub_m) if sub_m else "", kind_m, rim_t, ("%.3f" % rim_m) if rim_m is not None else "?"),
             "guides": 0, "nu": getattr(S_t, "NbUPoles", 0), "nv": getattr(S_t, "NbVPoles", 0), "folds": 0, "mirror_of_face": m_, "mirror_of_sub": sub_m, "rim_mm": round(rim_t, 4), "nurbs": (kind_m == "nurbs")}
    return kind_m, S_t, info_
nspan = nplane2 = 0
for pi in chg:
    if pi in PAT: continue          
    t1 = time.time()
    if FIT == "span":
        
        try:
            eds_ = _flat_e([ALL_E[k] for k in pch.get(pi, [])])
            if pi in ORIG_FIL: eds_ = [e_ for e_ in eds_ if not any(e_.isSame(x_) for x_ in ORIG_FIL[pi]["drop"])] + list(ORIG_FIL[pi]["add"])      
            if not eds_: raise RuntimeError("no edges")
            
            _loops = sorted(order_loops(eds_), key=lambda L: -Part.makeCompound(L).BoundBox.DiagonalLength)
            _holes = [L for L in _loops[1:] if _wire_closed(L)]
            _opens = [L for L in _loops[1:] if not _wire_closed(L)]
            if _opens:      # the agent's b6
                _own_ = {}
                for L_ in _opens:
                    for e__ in L_:
                        _who = [kk__ for kk__ in pch.get(pi, []) if ALL_E[kk__] is not None and any(e__.isSame(x__) for x__ in _flat_e([ALL_E[kk__]]))]
                        if not _who:      
                            try: _who2 = [kk__ for kk__ in range(len(ALL_E)) if ALL_E[kk__] is not None and any(e__.isSame(x__) or (x__.valueAt(0.5 * (x__.FirstParameter + x__.LastParameter)) - e__.valueAt(0.5 * (e__.FirstParameter + e__.LastParameter))).Length <= 1e-3 for x__ in _flat_e([ALL_E[kk__]]))]
                            except Exception: _who2 = []
                            _own_[e__.hashCode()] = ("a FOREIGN edge: a piece of chain %s (faces %s) - a neighbour's border or split handed to this face" % (_who2, [CH[x__]["pair"] for x__ in _who2 if x__ < len(CH)])) if _who2 else "no border at all (a split's or a fillet strip's edge handed to this face - the lines pass's)"
                        else: _own_[e__.hashCode()] = "border %s" % _who
                say("face %d: %d loop(s) beyond its outer one do NOT close - their edges: %s - a split or a fillet strip of a neighbour reached into this face's border; the face spans its outer loop, look at those edges (31bq B20)"
                    % (pi, len(_opens), "; ".join("%.2f mm from %s" % (e__.Length, _own_.get(e__.hashCode(), "?")) for L_ in _opens for e__ in L_[:4])))
            if len(_loops) > 1:
                say("face %d: %d loop(s) - the outer (%d edges) is spanned, %d hole(s) (%s edges) kept for the face stage, their rims as added lines" % (pi, len(_loops), len(_loops[0]), len(_holes), [len(L) for L in _holes]))
                HOLE_EDGES[pi] = [e_ for L in _holes for e_ in L]; eds_ = list(_loops[0])
            polys_ = SP.edge_polys(eds_)
            gpolys_ = _clip_guides([np.array([[q.x, q.y, q.z] for q in ge.discretize(Number=max(6, int(ge.Length / 0.5) + 1))]) for _g, ge in GUIDES.get(pi, [])], polys_, pi)      
            gpolys_ += [np.array([[q.x, q.y, q.z] for q in he.discretize(Number=max(6, int(he.Length / 0.5) + 1))]) for he in HOLE_EDGES.get(pi, [])]
            _vt = F[pid == pi]; _vn = np.cross(Vu[_vt[:, 1]] - Vu[_vt[:, 0]], Vu[_vt[:, 2]] - Vu[_vt[:, 0]]); _va = np.linalg.norm(_vn, axis=1); _vn = _vn[_va > 1e-9] / _va[_va > 1e-9][:, None]
            if gpolys_ or len(_loops) > 1:      
                say("face %d: spanning %d edge(s) + %d added line(s) (%s) - NURBS fill first, then Coons, then plate" % (pi, len(eds_), len(gpolys_), "with %d hole(s)" % len(_holes) if len(_loops) > 1 else "no hole"))
            if SPLITS.get(pi):
                
                # skin-wires
                
                def _bridge_pieces(outer_x, holes_x, splits_x):
                    """31bl (the agent's b15: 'a split's ends are not both on one piece of the face' - the hole was held back for the face stage, so a split
                    could not end on its rim): a split with one end on the outer loop and the other on a hole's rim is a BRIDGE. n >= 2 bridges to
                    one hole cut the face into n simple pieces: outer arc + bridge + the hole arc on that side + bridge, the hole consumed (one per
                    corner of the hole keeps every piece a band). Returns (pieces or None, the remaining splits, the holes consumed). One bridge
                    alone is refused with the count; two bridges on one hole vertex are refused by name."""
                    pol_o = SP.edge_polys(outer_x); loop_o, st_o, ord_o = SP.order_loop(pol_o); eo = [outer_x[k0] for k0, rv in ord_o]; Vo = loop_o[st_o]
                    hl = []
                    for H_ in holes_x:
                        pol_h = SP.edge_polys(H_); loop_h, st_h, ord_h = SP.order_loop(pol_h); hl.append(([H_[k0] for k0, rv in ord_h], loop_h[st_h], loop_h))
                    def _where(P_):
                        d_o = np.linalg.norm(Vo - P_, axis=1); jo = int(np.argmin(d_o))
                        if d_o[jo] <= 0.05: return ("outer", jo)
                        for hi_, (heo, Vh, _l) in enumerate(hl):
                            d_h = np.linalg.norm(Vh - P_, axis=1); jh = int(np.argmin(d_h))
                            if d_h[jh] <= 0.05: return ("hole", hi_, jh)
                        return None
                    bridges = {}; rest = []
                    for sp_ in splits_x:
                        se_ = sp_[1]; E0, E1 = _split_ends(se_)
                        w0, w1 = _where(E0), _where(E1)
                        if w0 and w1 and {w0[0], w1[0]} == {"outer", "hole"}:
                            wo, wh = (w0, w1) if w0[0] == "outer" else (w1, w0)
                            bridges.setdefault(wh[1], []).append((wo[1], wh[2], se_, sp_))
                        else: rest.append(sp_)
                    if not bridges: return None, splits_x, []
                    for hi_ in list(bridges):      
                        seen_ = {}; 
                        for b_ in bridges[hi_]: seen_.setdefault((b_[0], b_[1]), b_)
                        bridges[hi_] = list(seen_.values())
                    for hi_, bl in bridges.items():
                        if len(bl) < 2: raise RuntimeError("a split into the hole of this face needs at least TWO bridges (n bridges make n simple pieces, the hole consumed; four, one per corner, keep every piece a simple band) - %d found" % len(bl))
                    if len(bridges) > 1: raise RuntimeError("bridges into %d different holes of one face - one hole at a time" % len(bridges))
                    hi_, bl = next(iter(bridges.items())); heo, Vh, loop_h = hl[hi_]; n_o = len(eo); n_h = len(heo)
                    bl = sorted(bl, key=lambda b_: b_[0])
                    
                    _hs = [b_[1] for b_ in bl]
                    if len(bl) >= 3:
                        _alike = (sum((_hs[(q_ + 1) % len(bl)] - _hs[q_]) % n_h for q_ in range(len(bl))) == n_h)
                    else:
                        _nw = lambda L_: np.cross(np.asarray(L_), np.roll(np.asarray(L_), -1, 0)).sum(0)
                        _ref = _vn.mean(0) if len(_vn) else np.array([0.0, 0.0, 1.0])
                        _alike = (float(_nw(loop_o) @ _ref) * float(_nw(loop_h) @ _ref)) > 0
                    def _arc(seq, a_, b_, n_): return [seq[(a_ + t_) % n_] for t_ in range(((b_ - a_) % n_) or n_)] if a_ != b_ else []
                    def _mid(E_): return np.vstack(SP.edge_polys(E_)).mean(0) if E_ else None
                    pieces_b = []; _hu_ = []
                    for q_ in range(len(bl)):
                        (ja_, ha_, ba_, _sa), (jb_, hb_, bb_, _sb) = bl[q_], bl[(q_ + 1) % len(bl)]
                        if ja_ == jb_ and len(bl) > 1: raise RuntimeError("two bridges into the hole start on the same border vertex %s - one bridge per border vertex" % np.round(Vo[ja_], 2).tolist())
                        outA = _arc(eo, ja_, jb_, n_o)
                        hX = _arc(heo, hb_, ha_, n_h); hY = _arc(heo, ha_, hb_, n_h)
                        hA = hY if _alike else hX                                      
                        pieces_b.append(outA + _split_edges(bb_) + hA + _split_edges(ba_)); _hu_.extend(hA)
                    if sorted(map(id, _hu_)) != sorted(map(id, heo)):      
                        raise RuntimeError("the %d bridges end on %d distinct hole vertex(es) %s - the hole is not cut through (its %d edges go %d times into the pieces' borders): the bridges must end on at least two different corners of the rim and must not cross"
                                           % (len(bl), len(set(_hs)), sorted(set(_hs)), n_h, len(_hu_)))
                    say("face %d: a hole BRIDGED by %d split(s) - %d pieces (%s edges; the hole's %d edges are now borders)" % (pi, len(bl), len(pieces_b), " + ".join(str(len(x_)) for x_ in pieces_b), n_h))
                    return pieces_b, rest, [hi_]
                def _ends_on(eds_y, sp_):
                    vs_ = np.array([[v.X, v.Y, v.Z] for e_ in eds_y for v in e_.Vertexes])
                    return all(np.linalg.norm(vs_ - E_, axis=1).min() <= 0.05 for E_ in _split_ends(sp_[1]))
                _cut_applied = set()
                def _cut(eds_x, splits_x, deferred=()):
                    """the face's loop cut by its splits, one at a time: the first split with both ends on the loop's vertices makes two pieces; the
                    rest go to the piece that holds both their ends. 31bo: a split whose ends are not yet on one piece (its end sits on another
                    fillet's offset line, a border only after THAT strip is cut away - the agent's b20 keel split between the two keel-root strips) is
                    DEFERRED to both branches and applied where it fits; the caller refuses any split never applied (_cut_applied)."""
                    if not splits_x: return [eds_x]
                    pol_x = SP.edge_polys(eds_x); loop_, starts_, order_ = SP.order_loop(pol_x); eo_ = [eds_x[k0] for k0, rv in order_]
                    for si_, (gs_, se_) in enumerate(splits_x):
                        ends_ = np.array(_split_ends(se_))
                        d_ = [np.linalg.norm(loop_[starts_] - x_, axis=1) for x_ in ends_]; js_ = [int(np.argmin(x_)) for x_ in d_]
                        if max(d_[0][js_[0]], d_[1][js_[1]]) <= 0.05 and js_[0] != js_[1]: break
                    else:
                        if all(id(sp_) in deferred for sp_ in splits_x): return [eds_x]
                        raise RuntimeError("a split (%s, from %s to %s): its ends (%.2f / %.2f mm from the nearest border vertices) are not both on one piece of the face" % (_wtxt(gs_), np.round(ends_[0], 2).tolist(), np.round(ends_[1], 2).tolist(), d_[0][js_[0]], d_[1][js_[1]]))      
                    _cut_applied.add(id(splits_x[si_]))
                    j1, j2 = sorted(js_); n_ = len(order_)
                    subA = [eo_[k] for k in range(j1, j2)] + _split_edges(se_); subB = [eo_[k] for k in list(range(j2, n_)) + list(range(0, j1))] + _split_edges(se_)
                    rest_ = [x_ for q_, x_ in enumerate(splits_x) if q_ != si_]
                    def _holds(eds_y, sp_):
                        vs_ = np.array([[v.X, v.Y, v.Z] for e_ in eds_y for v in e_.Vertexes])
                        return all(np.linalg.norm(vs_ - E_, axis=1).min() <= 0.05 for E_ in _split_ends(sp_[1]))
                    rA = [x_ for x_ in rest_ if _holds(subA, x_)]; rB = [x_ for x_ in rest_ if _holds(subB, x_) and x_ not in rA]
                    rX = [x_ for x_ in rest_ if x_ not in rA and x_ not in rB]
                    dX = set(deferred) | {id(x_) for x_ in rX}
                    return _cut(subA, rA + rX, dX) + _cut(subB, rB + rX, dX)
                def _cut_all(eds_x, splits_x):
                    _cut_applied.clear(); out_ = _cut(eds_x, list(splits_x))
                    miss_ = [sp_ for sp_ in splits_x if id(sp_) not in _cut_applied]
                    if miss_:
                        _e0, _e1 = _split_ends(miss_[0][1])
                        raise RuntimeError("a split (%s, from %s to %s) has its ends on no piece of the face - on no border vertex within 0.05 mm, or on two different pieces"
                                           % (_wtxt(miss_[0][0]), np.round(_e0, 2).tolist(), np.round(_e1, 2).tolist()))
                    return out_
                
                _fil_anchor = {}
                for k_f, fl_ in FIL_MERGE.items():
                    if pi not in (fl_["p"], fl_["q"]): continue
                    for Jk_, at_ in (fl_["anchor"] if pi == fl_["q"] else fl_["anchor_p"]).items(): _fil_anchor[Jk_] = (np.asarray(at_, float), k_f)
                def _reend(se_, which_, at_):
                    P_ = np.array([[q.x, q.y, q.z] for q in se_.discretize(Number=max(12, int(se_.Length / 0.05) + 1))])
                    if which_ == 1: P_ = P_[::-1]
                    if isinstance(se_.Curve, Part.Line) or isinstance(se_.Curve, Part.LineSegment): return Part.LineSegment(V3(*at_), V3(*P_[-1])).toShape()
                    s_ = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P_, axis=0), axis=1))]); s_ = s_ / max(s_[-1], 1e-9)
                    Q_ = P_ + (1.0 - s_)[:, None] * (np.asarray(at_) - P_[0])[None, :]
                    cv_ = Part.BSplineCurve(); cv_.approximate(Points=[V3(*x) for x in Q_], DegMin=3, DegMax=3, Tolerance=1e-3, Continuity="C2")
                    cv_.setPole(1, V3(*Q_[0])); cv_.setPole(cv_.NbPoles, V3(*Q_[-1])); return cv_.toShape()
                
                _fil_cr = {}
                for k_f, fl_ in FIL_MERGE.items():
                    if pi in (fl_["p"], fl_["q"]): _fil_cr[k_f] = (np.vstack([samples(x_, 0.05) for x_ in _flat_e([ALL_E[k_f]])]), fl_)
                def _on_crease(E_):
                    for k_f, (Pc_, fl_) in _fil_cr.items():
                        if np.linalg.norm(Pc_ - E_, axis=1).min() < 0.05: return k_f, fl_
                    return None
                def _to_strip(E_, k_f, fl_):
                    """the nearest point of this face's offset line of fillet k_f, the offset edge cut there"""
                    pcs_ = _flat_e([fl_["lines"][pi][0]]); best_ = None
                    for pe_ in pcs_:
                        d_, pts_, _i = pe_.distToShape(Part.Vertex(V3(*E_)))
                        if best_ is None or d_ < best_[0]: best_ = (d_, pe_, np.array([pts_[0][0].x, pts_[0][0].y, pts_[0][0].z]))
                    d_, pe_, Q_ = best_
                    try:
                        prm_ = pe_.Curve.parameter(V3(*Q_)); lo_, hi_ = sorted((pe_.FirstParameter, pe_.LastParameter))
                        if lo_ + 1e-6 < prm_ < hi_ - 1e-6:
                            w_ = pe_.split([prm_]); sub_ = [x_ for x_ in w_.Edges if x_.Length > 1e-4]
                            if len(sub_) == 2:
                                new_ = [x_ for x_ in pcs_ if not x_.isSame(pe_)] + sub_
                                fl_["lines"][pi] = (new_,) + tuple(fl_["lines"][pi][1:])
                                for si2_, sp2_ in enumerate(SPLITS[pi]):
                                    if sp2_[0].get("fillet") == k_f: SPLITS[pi][si2_] = (sp2_[0], [x_ for x_ in _split_edges(sp2_[1]) if not x_.isSame(pe_)] + sub_)
                                if pi in ORIG_FIL: ORIG_FIL[pi]["add"] = [x_ for x_ in ORIG_FIL[pi]["add"] if not x_.isSame(pe_)] + sub_; ORIG_FIL_SRC.setdefault(pi, []).extend(("the strip of fillet %d (cut at a split's end)" % k_f, x_) for x_ in sub_)      
                    except Exception as ex_c:
                        say("   face %d: the offset line of fillet %d could not be cut at the split's end (%s) - the split ends at its nearest point" % (pi, k_f, str(ex_c)[:60]))
                    return Q_
                if _fil_anchor or _fil_cr:
                    _moved = []
                    for si_, sp_ in enumerate(SPLITS[pi]):
                        se_ = sp_[1]
                        if isinstance(se_, (list, tuple)) or sp_[0].get("fillet") is not None: continue      
                        E0, E1 = _split_ends(se_)
                        h0 = [Jk for Jk in _fil_anchor if np.linalg.norm(E0 - np.array(Jk)) < 0.05]; h1 = [Jk for Jk in _fil_anchor if np.linalg.norm(E1 - np.array(Jk)) < 0.05]
                        if h0 and h1: raise RuntimeError("the split '%s' runs from one fillet crease junction to another - it would cross the fillet's strip; end it elsewhere" % sp_[0].get("why", "")[:50])
                        if h0 or h1:
                            Jk = (h0 or h1)[0]; at_, k_f = _fil_anchor[Jk]; se_ = _reend(se_, 0 if h0 else 1, at_); SPLITS[pi][si_] = (sp_[0], se_)
                            _moved.append("'%s' by %.2f mm (a crease junction)" % (sp_[0].get("why", "")[:30], float(np.linalg.norm(np.array(Jk) - at_))))
                        for which_, E_ in ((0, E0), (1, E1)):
                            if (which_ == 0 and h0) or (which_ == 1 and h1): continue
                            oc_ = _on_crease(E_)
                            if oc_ is None: continue
                            k_f, fl_ = oc_; at_ = _to_strip(E_, k_f, fl_); se_ = _reend(se_, which_, at_); SPLITS[pi][si_] = (sp_[0], se_)
                            _moved.append("'%s' by %.2f mm (on the crease of fillet %d, to its strip's border)" % (sp_[0].get("why", "")[:30], float(np.linalg.norm(np.asarray(E_) - at_)), k_f))
                    if _moved: say("face %d: %d split end(s) on a fillet's crease moved to the strip's border (the curve kept): %s" % (pi, len(_moved), "; ".join(_moved)))
                _hole_loops = [L for L in _loops[1:] if _wire_closed(L)] if len(_loops) > 1 else []
                _bp, _rest, _used = _bridge_pieces(eds_, _hole_loops, list(SPLITS[pi]))
                if _bp is not None:
                    HOLE_EDGES[pi] = [e_ for hi_, L in enumerate(_hole_loops) if hi_ not in _used for e_ in L]

                    gpolys_ = _clip_guides([np.array([[q.x, q.y, q.z] for q in ge.discretize(Number=max(6, int(ge.Length / 0.5) + 1))]) for _g, ge in GUIDES.get(pi, [])], polys_, pi)      
                    gpolys_ += [np.array([[q.x, q.y, q.z] for q in he.discretize(Number=max(6, int(he.Length / 0.5) + 1))]) for he in HOLE_EDGES.get(pi, [])]
                    for s_ in _rest:      
                        own_ = [q_ for q_, pc_ in enumerate(_bp) if _ends_on(pc_, s_)]
                        if len(own_) != 1:
                            _e0, _e1 = _split_ends(s_[1])
                            raise RuntimeError("after the bridges a split (%s, from %s to %s) %s - end it on one piece, or start a bridge at its end"
                                               % (_wtxt(s_[0]), np.round(_e0, 2).tolist(), np.round(_e1, 2).tolist(),
                                                  "has its ends on different pieces of the bridged face, or off every border vertex by more than 0.05 mm (it crosses a bridge)" if not own_ else "has both ends on the shared vertices of pieces %s (it runs along a bridge)" % [chr(65 + q_) for q_ in own_]))
                    pieces_ = [pc_ for piece_ in _bp for pc_ in _cut_all(piece_, [s_ for s_ in _rest if _ends_on(piece_, s_)])]
                else:
                    pieces_ = _cut_all(eds_, list(SPLITS[pi]))
                subs_ = []
                if FIL_MERGE:     
                    held_ = []
                    for eds_s in pieces_:
                        for k_f, fl in FIL_MERGE.items():
                            if pi in (fl["p"], fl["q"]) and any(any(x_.isSame(y_) for y_ in _flat_e([ALL_E[k_f]])) for x_ in eds_s):
                                FIL_HOLD[(k_f, pi)] = eds_s; held_.append(id(eds_s))
                                if fl.get("cid") is not None and pi == CHAINS.get(fl["cid"], {}).get("A"):      
                                    for k2_ in CHAINS[fl["cid"]]["keys"]: FIL_HOLD[(k2_, pi)] = eds_s
                                
                                # corner edge
                                
                                for (_vxk_, _vxf_), _vxs_ in (globals().get("_VX_SIDE") or {}).items():
                                    if int(_vxf_) == int(pi) and int(k_f) in (int(_vxk_), int(_vxs_["c_key"])): FIL_HOLD[(int(_vxk_), pi)] = eds_s; FIL_HOLD[(int(_vxs_["c_key"]), pi)] = eds_s
                                break
                    pieces_ = [x for x in pieces_ if id(x) not in held_]
                _ord3 = list(range(len(pieces_)))
                if TWIN_MIRROR and MP is not None and FIT == "span" and len(pieces_) > 1:      
                    try: _ord3 = sorted(_ord3, key=lambda q3: (0 if _a3_side(np.vstack(SP.edge_polys(pieces_[q3])).mean(0)) >= -0.3 else 1, q3))
                    except Exception: _ord3 = list(range(len(pieces_)))
                for si_ in _ord3:
                    eds_s = pieces_[si_]
                    pol_s = SP.edge_polys(eds_s); mid_s = np.vstack(pol_s).mean(0)
                    if os.environ.get("FIL_DBG") == "1":      
                        _bb_d = Part.makeCompound(list(eds_s)).BoundBox
                        say("   face %d piece %s: %d edges, lengths %s, box x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f - spanning" % (pi, chr(65 + si_), len(eds_s), [round(x_.Length, 2) for x_ in eds_s], _bb_d.XMin, _bb_d.XMax, _bb_d.YMin, _bb_d.YMax, _bb_d.ZMin, _bb_d.ZMax))
                        try: Part.makeCompound(list(eds_s)).exportBrep(os.path.join(SK, "piece_%d_%s.brep" % (pi, chr(65 + si_))))
                        except Exception: pass
                    gp_s = [g for g in gpolys_ if min(np.linalg.norm(np.vstack(SP.edge_polys(o_)).mean(0) - g.mean(0)) for o_ in pieces_) >= np.linalg.norm(mid_s - g.mean(0)) - 1e-9]
                    rib_s = [rp_ for rp_, roe_ in RIBBONS.get(pi, []) if any(any(e_.isSame(x_) for x_ in roe_) for e_ in eds_s)]      
                    try:
                        _prog = lambda m_, pi_=pi, si__=si_: say("   face %d piece %s: %s ..." % (pi_, chr(65 + si__), m_))
                        _m3 = _a3_mirror_surface(pi, pol_s, mid_s, subs_) if (TWIN_MIRROR and MP is not None and FIT == "span") else None      
                        if _m3 is not None:
                            kind_s, payload_s, info_s = _m3; rib_s = []      
                            say("   face %d piece %s: %s" % (pi, chr(65 + si_), info_s["how"]))
                        else:
                            kind_s, payload_s, info_s = SP.span_face(pol_s, gp_s, CORNER_DEG, SPAN_STEP, vox_normals=_vn, progress=_prog, **_nurbs_args(pi))
                        if rib_s:
                            # ACCEPTED
                            
                            try:
                                kind_r, payload_r, info_r = SP.span_face(pol_s, gp_s + rib_s, CORNER_DEG, SPAN_STEP, vox_normals=_vn, progress=None, **_nurbs_args(pi))
                                ok_r, why_r = _ribbon_ok(SP.surface_of(kind_s, payload_s), SP.surface_of(kind_r, payload_r), kind_r)
                            except Exception as ex_rb:
                                ok_r, why_r = False, "the fill through the ribbon failed: %s" % str(ex_rb)[:80]
                            if ok_r:
                                kind_s, payload_s, info_s = kind_r, payload_r, dict(info_r, ribbon=why_r); gp_s = gp_s + rib_s
                                say("   face %d piece %s: the tangent ribbon TAKEN - the fill runs out of the blend tangent (%s)" % (pi, chr(65 + si_), why_r))
                            else:
                                say("   face %d piece %s: the tangent ribbon REFUSED - %s; the plain fill stands (a ridge beside the blend may remain there)" % (pi, chr(65 + si_), why_r))
                    except Exception as ex_s:
                        
                        _ch_s = sorted(set(k_ for k_ in pch.get(pi, []) for e_ in _flat_e([ALL_E[k_]]) if any(e_.isSame(x_) for x_ in eds_s)))
                        _bb_s = Part.makeCompound(list(eds_s)).BoundBox
                        raise RuntimeError("piece %s of %d (chains %s, %d edges, %d added line(s); x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f): %s - the pieces before it: %s"
                                           % (chr(65 + si_), len(pieces_), _ch_s, len(eds_s), len(gp_s), _bb_s.XMin, _bb_s.XMax, _bb_s.YMin, _bb_s.YMax, _bb_s.ZMin, _bb_s.ZMax, str(ex_s)[:120],
                                              ", ".join("%s %s" % (x[2]["sub"], x[2]["span"]) for x in subs_) or "none"))
                    try: _A3_RIM[(pi, chr(65 + si_))] = _a3_rim(SP.surface_of(kind_s, payload_s), pol_s)      
                    except Exception: pass
                    subs_.append((_Surf(SP.surface_of(kind_s, payload_s)), eds_s, {"span": kind_s, "sub": chr(65 + si_), "corners": info_s.get("how"), "guides": len(gp_s), "mirror_of_face": info_s.get("mirror_of_face"), "mirror_of_sub": info_s.get("mirror_of_sub"),
                                                                                  "nurbs_why": (None if kind_s == "nurbs" else str(info_s.get("nurbs", ""))[:160]), "folds": info_s.get("folds"),
                                                                                  "balloon_mm": info_s.get("balloon_mm"), "balloon_note": info_s.get("balloon_note"), "balloon_unmeasured": info_s.get("balloon_unmeasured"), "balloon_tess": info_s.get("balloon_tess")}))      # recorded
                subs_.sort(key=lambda x3: x3[2]["sub"])      
                PAT[pi] = subs_; recs[pi] = {"span": "split", "subs": [x[2] for x in subs_], "why": "; ".join(g_.get("why", "") for g_, _e in SPLITS[pi])}; nspan += 1
                say("face %d: SPLIT into %d by %d line(s) - %s (%s)" % (pi, len(subs_), len(SPLITS[pi]), ", ".join("%s %s" % (x[2]["sub"], x[2]["span"]) for x in subs_), recs[pi]["why"][:80]))
                for x in subs_:      
                    if x[2].get("nurbs_why"): say("   piece %s is %s: NURBS %s" % (x[2]["sub"], x[2]["span"], x[2]["nurbs_why"]))
                continue
            _m3 = _a3_mirror_surface(pi, polys_, None) if (_A3_TWIN and pi in _A3_TWIN and pi not in _A3_MASTER) else None      
            if _m3 is not None: kind_, payload_, info_ = _m3
            else: kind_, payload_, info_ = SP.span_face(polys_, gpolys_, CORNER_DEG, SPAN_STEP, vox_normals=_vn, progress=lambda m_, pi_=pi: say("   face %d: %s ..." % (pi_, m_)), **_nurbs_args(pi))
            try: _A3_RIM[pi] = _a3_rim(SP.surface_of(kind_, payload_), polys_)      
            except Exception: pass
            if kind_ == "plane":
                PAT[pi] = _Surf(SP.surface_of(kind_, payload_))
                recs[pi] = {"span": "plane", "plane": True, "secs": round(time.time() - t1, 2)}; nplane2 += 1
                say("face %d: PLANE - its %d edges lie in one plane" % (pi, len(eds_)))
            else:
                if info_["guides"] and (info_.get("guide_after") or 0) > SP.GUIDE_TOL:
                    say("face %d: an added line stays %.2f mm off the surface (the pull reached %.2f -> %.2f) - the fallback: make that line a SPLIT (skin-wires role split)" % (pi, info_["guide_after"], info_["guide_before"], info_["guide_after"]))
                PAT[pi] = _Surf(SP.surface_of(kind_, payload_))
                recs[pi] = {"span": kind_, "corners": info_["how"], "nu": info_["nu"], "nv": info_["nv"], "guides": info_["guides"], "folds": info_.get("folds", 0), "secs": round(time.time() - t1, 2), "mirror_of_face": info_.get("mirror_of_face"),
                            "nurbs_why": (None if kind_ == "nurbs" else info_.get("nurbs")), "balloon_mm": info_.get("balloon_mm"), "balloon_note": info_.get("balloon_note"), "balloon_unmeasured": info_.get("balloon_unmeasured"), "balloon_tess": info_.get("balloon_tess")}      # not taken
                if kind_ == "plate": recs[pi].update({"coons": info_.get("coons"), "fit_max_mm": info_.get("fit_max_mm"), "turn_p95_deg": info_.get("turn_p95_deg")})
                if info_["guides"]: recs[pi].update({"guide_before_mm": info_.get("guide_before"), "guide_after_mm": info_.get("guide_after")})
                nspan += 1
                if info_.get("mirror_of_face") is not None: say("face %d: %s (%.1fs)" % (pi, info_["how"], time.time() - t1))
                else: say("face %d: %s its %d edge(s) (%s; %dx%d poles)%s (%.1fs)" % (pi, {"coons": "spanned (Coons) by", "nurbs": "a NURBS fill through"}.get(kind_, "a PLATE through"), len(eds_), info_["how"], info_["nu"], info_["nv"],
                    (" + %d added line(s) inside it" % info_["guides"]) if info_["guides"] else "", time.time() - t1) + (("; NURBS: %s" % info_.get("nurbs")) if kind_ != "nurbs" and info_.get("nurbs") else ""))
        except Exception as ex:
            recs[pi] = {"fail": str(ex)[:1500], "secs": round(time.time() - t1, 2)}; say("face %d: SPAN FAILED - %s - %s" % (pi, str(ex)[:1500], _span_advice(str(ex)))); _a6_say(pi)      
        continue
    try:
        pt = Patch(pi)
        bxyz = np.vstack([samples(ALL_E[k]) for k in pch.get(pi, [])]) if pch.get(pi) else np.zeros((0, 3))
        buv, bd = pt.locate(bxyz) if len(bxyz) else (np.zeros((0, 2)), np.zeros(0))
        info = pt.fit(buv, bxyz); info["locate_max"] = round(float(bd.max()), 4) if len(bd) else 0
        if os.environ.get("FITDBG", "0") == "1" and info["edge_max"] > 0.1:
            n0 = 0
            for k in pch.get(pi, []):
                m_ = len(samples(ALL_E[k])); sl = slice(n0, n0 + m_); n0 += m_
                q_ = np.array([[x.x, x.y, x.z] for x in (pt.bs.value(float(a), float(b)) for a, b in buv[sl])])
                dfit = np.linalg.norm(q_ - bxyz[sl], axis=1)
                if os.environ.get("FITDBG_P") and str(pi) in os.environ["FITDBG_P"].split() and dfit.max() > 0.05:
                    w_ = int(np.argmax(dfit)); P_ = bxyz[sl][w_]
                    _, nn_ = pt.kd.query(P_, k=3); tri_ = pt.T[nn_[0]]; gl_ = pt.vids[tri_]
                    
                    tf_ = np.nonzero((np.sort(F, 1) == np.sort(gl_)).all(1))[0]
                    say("         worst point of edge %d: located uv %s on a triangle of face %s (own face %d); surface there misses by %.3f; uv of its neighbours on the edge %s" % (
                        k, np.round(buv[sl][w_], 4).tolist(), [int(pid[x]) for x in tf_], pi, dfit[w_], np.round(buv[sl][max(0, w_ - 2):w_ + 3], 4).tolist()))
                    hi_ = np.argsort(-dfit)[:5]; say("         5 worst along the edge at sample indices %s of %d, misses %s, off the voxel %s" % (hi_.tolist(), m_, np.round(dfit[hi_], 3).tolist(), np.round(bd[sl][hi_], 3).tolist()))
                if dfit.max() > 0.05:
                    say("      patch %d edge %d (%s, %.2f mm): off the voxel max %.3f (uv clamped at the patch rim: %d of %d); the surface misses it by max %.3f" % (
                        pi, k, ("body edge" if k >= len(CH) else CH[k]["type"] + " " + str(CH[k]["pair"])), ALL_E[k].Length, bd[sl].max(),
                        int(((buv[sl] <= 1e-6) | (buv[sl] >= 1 - 1e-6)).any(1).sum()), m_, dfit.max()))
        PAT[pi] = pt; recs[pi] = info
        if SHOW_NUMBERS:
            say("changed patch %d: %d edges, map flips %d, control %s; mesh dev p50 %.3f p95 %.3f max %.2f; boundary dev p95 %.4f max %.4f; edge points off the mesh max %.3f (%.0fs)"
                % (pi, len(pch.get(pi, [])), info["flips"], info["ctrl"], info["vox_p50"], info["vox_p95"], info["vox_max"], info["edge_p95"], info["edge_max"], info["locate_max"], time.time() - t1))
        else:
            say("changed patch %d: fitted (%d edges, control %s%s)" % (pi, len(pch.get(pi, [])), info["ctrl"], ", symmetric" if info.get("symfit") else ""))
    except Exception as ex:
        recs[pi] = {"fail": str(ex)[:120]}; say("changed patch %d: FIT FAILED %s" % (pi, str(ex)[:120]))

try:
    SLOW_X = float(os.environ.get("SLOW_X", "3") or 3); SLOW_MIN_S = float(os.environ.get("SLOW_MIN_S", "30") or 30)
    _ckp = os.path.join(SK, "SPAN_CLOCK.json")
    try: _ck = json.load(open(_ckp, encoding="utf-8"))
    except (OSError, ValueError): _ck = {}
    _now = {}
    for pi_, r_ in recs.items():
        if r_.get("secs") is None: continue
        _rg = r_.get("span") or ("failed" if r_.get("fail") else "?"); _now.setdefault(_rg, []).append((float(r_["secs"]), pi_))
    _lines = []; _slow = []
    for _rg, _ls in sorted(_now.items()):
        _past = [float(x) for x in _ck.get(_rg, [])]; _typ = float(np.median(_past + [s_ for s_, _ in _ls]))
        _lines.append("%s %.1f s typical over %d face(s)" % (_rg, _typ, len(_past) + len(_ls)))
        for s_, pi_ in _ls:
            if s_ > SLOW_MIN_S and s_ > SLOW_X * _typ: _slow.append((pi_, _rg, s_, _typ))
        _ck[_rg] = (_past + [round(s_, 2) for s_, _ in _ls])[-200:]
    json.dump(_ck, open(_ckp, "w", encoding="utf-8"), indent=0)
    if _lines: say("SPAN TIMES (no time bound; the job's running record skin\\SPAN_CLOCK.json): %s" % "; ".join(_lines))
    for pi_, _rg, s_, _typ in _slow:
        say("face %d: SLOW - %.0f s for a %s face against %.1f s typical on this job (over SLOW_X %g): recommended - a SPLIT line across it or fewer added lines; it is not cut short" % (pi_, s_, _rg, _typ, SLOW_X))
except Exception as _exc: say("the span-time record failed: %s" % str(_exc)[:80])
for k_f, fl in FIL_MERGE.items():
    A_ = FIL_HOLD.get((k_f, fl["p"])); B_ = FIL_HOLD.get((k_f, fl["q"])); _nmf = fl.get("name", str(k_f))      
    say("fillet line %s: strips held on face %d (%s) and face %d (%s)" % (_nmf, fl["p"], "yes" if A_ is not None else "NO", fl["q"], "yes" if B_ is not None else "NO"))
    if A_ is None or B_ is None:
        say("FILLET BY LINES on line %s: the strip was not found on face %s - the faces stay as split" % (_nmf, fl["p"] if A_ is None else fl["q"])); continue
    eds_m = _flat_e([fl["lines"][fl["p"]][0], fl["arcs"][1][0], fl["lines"][fl["q"]][0], fl["arcs"][0][0]])      
    if os.environ.get("FIL_DBG") == "1":
        try:
            Part.makeCompound(list(eds_m) + [x_ for f in (fl["p"], fl["q"]) for x_ in fl["ends"][f] if x_ is not None]).exportBrep(os.path.join(SK, "fillet_%d_strip.brep" % k_f)); Part.makeCompound(_flat_e([ALL_E[k_f]])).exportBrep(os.path.join(SK, "fillet_%d_crease.brep" % k_f))
            Part.Face(fl["surf"]).exportBrep(os.path.join(SK, "fillet_%d_surf.brep" % k_f))      
            say("   blend of line %s: 4 edges, lengths %s; %d arcs, %d x %d poles; ends %s" % (_nmf, [round(x_.Length, 2) for x_ in eds_m], fl["rows"], fl["npoles"][0], fl["npoles"][1], fl["endkind"]))
        except Exception as ex_: say("   strip dbg: %s" % str(ex_)[:120])
    try:
        bs_m = fl["surf"]
        host = fl["q"] if isinstance(PAT.get(fl["q"]), list) else (fl["p"] if isinstance(PAT.get(fl["p"]), list) else None)
        def _put(surf_, eds_, rec_):
            global host
            if host is not None: PAT[host].append((_Surf(surf_), eds_, rec_)); recs[host].setdefault("subs", []).append(rec_)
            else: BLEND_FACES.setdefault(fl["p"], []).append((_Surf(surf_), eds_, rec_)); recs.setdefault(fl["p"], {}).setdefault("subs", []).append(rec_)
        
        _cutcorner = any((m_ or {}).get("corner") and (m_ or {}).get("cut") for f_ in (fl["p"], fl["q"]) for m_ in fl["meet"][f_])      # corner edge
        _natural = all(x_ in ("taper", "chain", "arc-cap") for x_ in fl["endkind"]) and not any(fl.get("mitred", [False, False])) and not any(fl.get("merged_end", [False, False])) and not any(fl.get("vertex_end", [False, False])) and not _cutcorner      
        rec_m = {"span": "sweep", "sub": ("F*" if _natural else "F"), "corners": "an arc of R %g swept along the crease: %d arcs interpolated into one %d x %d-pole surface" % (fl["r"], fl["rows"], fl["npoles"][0], fl["npoles"][1]),
                 "guides": 1, "fillet": k_f, "guide_after": 0.0, "nurbs_why": None, "folds": 0}
        J_ends_ = [np.asarray(fl["J"][0], float), np.asarray(fl["J"][1], float)]      
        def _side(f, e_):
            if fl["ends"][f][e_] is not None: return [fl["ends"][f][e_]]
            m_ = fl["meet"][f][e_]; J_ = J_ends_[e_]; got_ = []
            for pe_ in _flat_e([ALL_E[int(m_["chain"])]]):
                P0_ = np.array([pe_.Vertexes[0].X, pe_.Vertexes[0].Y, pe_.Vertexes[0].Z]); P1_ = np.array([pe_.Vertexes[-1].X, pe_.Vertexes[-1].Y, pe_.Vertexes[-1].Z])
                if min(np.linalg.norm(P0_ - J_), np.linalg.norm(P1_ - J_)) < 0.05 and min(np.linalg.norm(P0_ - m_["at"]), np.linalg.norm(P1_ - m_["at"])) < 0.05: got_.append(pe_)
            if not got_: raise RuntimeError("the cut fragment of border %d at the junction %s was not found for the cap" % (m_["chain"], np.round(J_, 1).tolist()))
            return got_
        caps_ = [(cs_, _side(fl["p"], e_), [fl["arcs"][e_][0]], _side(fl["q"], e_)) for e_, cs_ in enumerate(fl["caps"]) if cs_ is not None]      
        _put(bs_m, eds_m, rec_m)
        for e_, (cs_, sp_c, arc_c, sq_c) in enumerate(caps_):
            ce_ = sp_c + arc_c + sq_c
            
            mis_ = 0.0
            try:
                _cf = Part.Face(cs_)
                mis_ = max(float(_cf.distToShape(Part.Vertex(V3(*q_)))[0]) for e_c in ce_ for q_ in samples(e_c, 0.3))
            except Exception: mis_ = 0.0
            if mis_ > 0.02:
                _Jc = np.asarray(fl["J"][e_], float); _fb = None
                try: _fb = VX.coons_patch(sp_c if len(sp_c) > 1 else sp_c[0], sq_c if len(sq_c) > 1 else sq_c[0], arc_c[0], _Jc)
                except Exception as ex_cc: say("   fillet line %s: the cap's Coons through its edges failed (%s)" % (_nmf, str(ex_cc)[:80]))
                surf_c, how_c = _span_corner(list(ce_), "fillet line %s: the cap at end %d" % (_nmf, e_), _fb, rim_tol=0.02)
                if surf_c is not None:
                    _put(surf_c, ce_, dict(_SPANC_BAL, **{"span": "cap-span", "sub": "F%d" % e_, "corners": "the cap at the crease's junction: spanned through its %d edges (%s) - the cone missed its curved border by %.3f mm" % (len(ce_), how_c, mis_), "guides": 0, "fillet": k_f, "guide_after": 0.0, "nurbs_why": None, "folds": 0}))
                    say("   fillet line %s: the cap at end %d is spanned through its edges - the cone missed its curved border by %.3f mm" % (_nmf, e_, mis_)); continue
            _put(cs_, ce_, {"span": "cone", "sub": "F%d" % e_, "corners": "the cap at the crease's junction: a cone from the junction to the blend's end curve", "guides": 0, "fillet": k_f, "guide_after": 0.0, "nurbs_why": None, "folds": 0})
        say("FILLET BY LINES on line %s: the blend face is the arc of R %g swept along the crease (%d x %d poles; ends %s) - the crease is gone" % (_nmf, fl["r"], fl["npoles"][0], fl["npoles"][1], " / ".join(fl["endkind"])))
    except Exception as ex:
        say("FILLET BY LINES on line %s FAILED: %s - the strips stay as two faces on their crease" % (_nmf, str(ex)[:120]))
        for f, E_ in ((fl["p"], A_), (fl["q"], B_)):
            if f in ORIG_FIL and not isinstance(PAT.get(f), list):
                ORIG_FIL.pop(f, None); say("   face %d (original) keeps its full border - its strip is not cut out (the crease stays sharp)" % f); continue
            try:
                k_s, pl_s, in_s = SP.span_face(SP.edge_polys(E_), [], CORNER_DEG, SPAN_STEP, progress=lambda m_, f_=f: say("   face %d's strip: %s ..." % (f_, m_)))
                PAT[f].append((_Surf(SP.surface_of(k_s, pl_s)), E_, {"span": k_s, "sub": "S", "corners": in_s.get("how"), "guides": 0}))
            except Exception as ex2: say("   face %d's strip: %s" % (f, str(ex2)[:80]))
for host_, surf_, eds_, rec_ in PIVOTS:      
    if isinstance(PAT.get(host_), list): PAT[host_].append((_Surf(surf_), eds_, rec_)); recs[host_].setdefault("subs", []).append(rec_)
    else: BLEND_FACES.setdefault(host_, []).append((_Surf(surf_), eds_, rec_)); recs.setdefault(host_, {}).setdefault("subs", []).append(rec_)
if PIVOTS: say("CORNER PATCHES (31bp): %d placed" % len(PIVOTS))
if FIT == "span": say("SPANNED: %d face(s) through their edges, %d plane(s), %d failed" % (nspan, nplane2, sum(1 for pi in chg if "fail" in recs.get(pi, {}))))

if KEEP_NET:
    EDGES = list(ALL_E); erec = [{"chain": k, "how": ("body edge" if k >= len(CH) else "network edge") + (" (cut by a split)" if isinstance(ALL_E[k], list) else "")} for k in range(len(ALL_E))]
    say("KEEP_NET: the %d network edges are used unchanged; changed faces are built on their pinned fits" % len(NE))
if not KEEP_NET:
    JN = JP.copy(); jmoved = []
    jpat = [set(j["patches"]) for j in NJ["junctions"]]
    JUV = {}
    for j in range(len(JP)):
        cs = sorted(p for p in jpat[j] if p in PAT and isinstance(PAT[p], Patch))      
        if not cs: continue
        pt = PAT[cs[0]]; uv, d = pt.locate(JP[j]); q = pt.bs.value(float(uv[0, 0]), float(uv[0, 1]))
        JN[j] = (q.x, q.y, q.z); JUV[(cs[0], j)] = uv[0]; jmoved.append(float(np.linalg.norm(JN[j] - JP[j])))
    say("junctions moved onto a changed surface: %d, by p50 %.4f max %.4f mm" % (len(jmoved), np.median(jmoved) if jmoved else 0, max(jmoved) if jmoved else 0))
    
    EDGES = [None] * len(CH); erec = []
    for k, c in enumerate(CH):
        p, q = c["pair"]; ja, jb = c["junctions"]; closed = c["closed"]
        host = min([x for x in (p, q) if x in PAT and isinstance(PAT[x], Patch)], default=None)
        S = samples(NE[k], 0.5)
        try:
            if host is not None:
                pt = PAT[host]; uv, _ = pt.locate(S)
                if not closed:
                    if ja is not None: uv[0] = JUV.get((host, ja), pt.locate(JN[ja])[0][0])
                    if jb is not None: uv[-1] = JUV.get((host, jb), pt.locate(JN[jb])[0][0])
                keep = [0]
                for i in range(1, len(uv)):
                    if np.linalg.norm(uv[i] - uv[keep[-1]]) > 1e-7: keep.append(i)
                if not closed and keep[-1] != len(uv) - 1: keep[-1] = len(uv) - 1
                uv = uv[keep]
                c2 = Part.Geom2d.BSplineCurve2d()
                if closed: c2.interpolate([Base.Vector2d(*x) for x in uv[:-1]], PeriodicFlag=True)
                elif len(uv) == 2:
                    mid = 0.5 * (uv[0] + uv[1]); c2.interpolate([Base.Vector2d(*uv[0]), Base.Vector2d(*mid), Base.Vector2d(*uv[1])])
                else: c2.interpolate([Base.Vector2d(*x) for x in uv])
                e = c2.toShape(pt.bs, c2.FirstParameter, c2.LastParameter); how = "on changed surface %d" % host
            else:
                if not closed:
                    if ja is not None: S[0] = JN[ja]
                    if jb is not None: S[-1] = JN[jb]
                moved = (ja is not None and np.linalg.norm(JN[ja] - JP[ja]) > 1e-9) or (jb is not None and np.linalg.norm(JN[jb] - JP[jb]) > 1e-9)
                if moved:
                    kp = [0]
                    for i in range(1, len(S)):
                        if np.linalg.norm(S[i] - S[kp[-1]]) > 1e-5: kp.append(i)
                    if kp[-1] != len(S) - 1: kp[-1] = len(S) - 1
                    S = S[kp]
                    if len(S) == 2: cv = Part.LineSegment(V3(*S[0]), V3(*S[1])).toBSpline()
                    else: cv = Part.BSplineCurve(); cv.interpolate([V3(*x) for x in S])
                    e = cv.toShape(); how = "re-ended"
                else: e = NE[k]; how = "network edge"
            EDGES[k] = e; erec.append({"chain": k, "how": how})
        except Exception as ex:
            erec.append({"chain": k, "fail": str(ex)[:100]}); say("edge %d (%s): FAILED %s" % (k, c["type"], str(ex)[:100]))
    say("edges: %d built, %d failed" % (sum(1 for e in EDGES if e is not None), sum(1 for e in EDGES if e is None)))

faces = []; frec = []
_todo_faces = []
for i, p in enumerate(PJ):
    ks = pch.get(i, []); eds = _flat_e([EDGES[k] for k in ks])
    if i in ORIG_FIL:         
        eds = [e_ for e_ in eds if not any(e_.isSame(x_) for x_ in ORIG_FIL[i]["drop"])] + list(ORIG_FIL[i]["add"])
    if isinstance(PAT.get(i), list):        
        for S_sub, eds_sub, inf_sub in PAT[i]:
            if inf_sub.get("ready") is not None: _todo_faces.append((i, p, eds_sub, inf_sub["ready"], "FV", inf_sub.get("fillet"))); continue      
            _he = HOLE_EDGES.get(i, [])
            if _he:      
                _bb = Part.makeCompound(list(eds_sub)).BoundBox; _hc = Part.makeCompound(list(_he)).BoundBox.Center
                if _bb.isInside(_hc): eds_sub = list(eds_sub) + list(_he)
            _todo_faces.append((i, p, eds_sub, S_sub.bs, inf_sub["sub"], inf_sub.get("fillet")))
    else: _todo_faces.append((i, p, eds, None, None, None))
    for S_sub, eds_sub, inf_sub in BLEND_FACES.get(i, []):
        if inf_sub.get("ready") is not None: _todo_faces.append((i, p, eds_sub, inf_sub["ready"], "FV", inf_sub.get("fillet"))); continue      
        _todo_faces.append((i, p, eds_sub, S_sub.bs, inf_sub["sub"], inf_sub.get("fillet")))
def _not_borders(i_, eds_):
    """31bq R6 / R7W (the instrument of B20 - OPEN: the split handover B20 records is not reproduced on this route, its cause untraced): THE FACE STAGE'S BORDER CHECK - every edge a face (or a piece of a
    split face) is given must be a border of it: a piece of one of its own chains or wall edges, or its own split / a strip a step recorded for it (ORIG_FIL / SPLITS: the
    kit's fillet strips, B04's gap closers); on an ORIGINAL face a recorded edge must also lie on the face within the print tolerance (THIN_MM) - measured against its own
    mesh (_seg_off_face); an edge that is a FOREIGN chain's piece, an added line, an edge no step recorded, or a recorded edge off the face is NOT a border - named with its
    origin, its length, its distance, its place and its loop (the B03 retry's fill7j / 7k / 8: a 23.2 mm straight line of fillet chain 2's strip crossed the original vane
    underside 5.8 mm off it - "chain None"); a recorded edge whose distance cannot be read is named NOT MEASURED. The loops in the face stage's own order (the outer, the
    largest box, first). Returns (the findings, the loops: [(closed, [(length, origin)...])])"""
    out_ = []
    try: loops_ = sorted(order_loops(list(eds_)), key=lambda L__: -Part.makeCompound(list(L__)).BoundBox.DiagonalLength)
    except Exception: loops_ = [list(eds_)]
    lps_ = []
    for li_, L_ in enumerate(loops_):
        cl_ = _wire_closed(L_); lst_ = []
        for e_ in L_:
            try:
                if e_.Length < 1e-6: continue
                org_ = _edge_origin(e_, i_)
            except Exception: continue
            lst_.append((round(float(e_.Length), 2), org_))
            rec_ = org_.endswith(", handed to this face") or org_.startswith("the split ")      # recorded
            own_ = org_.startswith("chain ") or rec_
            off_ = _seg_off_face(e_, i_)[0] if (rec_ and kind[i_] == "orig") else None
            unm_ = bool(rec_ and kind[i_] == "orig" and off_ is None)
            if own_ and not unm_ and (off_ is None or off_ <= THIN_FIL): continue
            try: m_ = e_.valueAt(0.5 * (e_.FirstParameter + e_.LastParameter)); mid_ = [round(m_.x, 2), round(m_.y, 2), round(m_.z, 2)]
            except Exception: mid_ = None
            out_.append({"len": round(float(e_.Length), 3), "origin": org_, "off_mm": (None if off_ is None else round(float(off_), 3)), "unmeasured": unm_, "mid": mid_, "loop": li_, "loop_closed": bool(cl_)})
        lps_.append((bool(cl_), lst_))
    return out_, lps_
NOT_BORDER = []      
# ---- 31bq R7W WIRE-CLEAN

# 0 cracks

# ONE CURVE in both faces

# over the
# WIRE_CLEAN_TOL
WC_RECORD = None      # wire_clean
try:
    import sk_clean as _CL
    _WC_TOL = float(os.environ.get("WIRE_CLEAN_TOL", str(_CL.TOL)) or 0); _WC_DRY = os.environ.get("WIRE_CLEAN_DRY", "0") == "1"
    if _WC_TOL > 0 and _todo_faces:
        
        _wf = list(_todo_faces); _wc_src = {}; _wc_frozen = set(); _wc_fz_edges = []
        if FRAME:
            for _kb in BODY_E:
                try: _wc_fz_edges.extend(_flat_e([ALL_E[_kb]]))
                except Exception: pass
        for _tw in _wf:
            if (_tw[4] if len(_tw) > 4 else None) in ("FV", "F*"): _wc_fz_edges.extend(list(_tw[2]))
        for x_ in _wc_fz_edges:
            try: _wc_frozen.add(x_.hashCode())
            except Exception: pass
        _wc_fpts = []
        for x_ in _wc_fz_edges:
            try: _wc_fpts.extend([_CL.ends(x_)[0], _CL.ends(x_)[1]])
            except Exception: pass
        _wc_fpts = np.asarray(_wc_fpts, float).reshape(-1, 3)
        def _wc_tuple(t_, eds_): return (t_[0], t_[1], list(eds_)) + tuple(t_[3:])
        def _wc_name(t_): return "%d%s" % (t_[0], (t_[4] if (len(t_) > 4 and t_[4]) else ""))
        def _wc_closed(L_, tol_):
            """31bq R7Wn4 (C3): closed WITHIN THE CONSTRUCTION TOLERANCE - the kernel's own isClosed (1e-3 and its tolerances) had skipped every gapped loop silently, so a GAP
            under 0.02 never reached the pass; returns (closed, the widest junction gap)"""
            try:
                E_ = _CL.order(list(L_)); g_ = [float(np.linalg.norm(_CL.ends(E_[(k_ + 1) % len(E_)])[0] - _CL.ends(E_[k_])[1])) for k_ in range(len(E_))]
                return bool(max(g_) <= tol_), float(max(g_))
            except Exception: return False, float("nan")
        _wc_moves = 0; _wc_faces = 0; _wc_lines = []; _wc_hand = 0; _wc_void = 0; _wc_lost = 0; _wc_frz = 0; _wc_copies = 0; _wc_skip = []; _wc_vx = 0; _wc_micro = []; _wc_dry = {"gap": 0, "short": 0, "graze": 0, "near": 0, "double_graze_loops": 0, "loops": 0}
        _wc_read = 0; _wc_notread = 0; _wc_neck = 0      
        def _wc_take(t_, new_eds, old_eds):
            """31bq R7Wn4b (test-R7Wn4 D7): the pass-made edges of a face into the sources (B20's instrument) and, under 0.1 mm, into the micro record WITH the face's sub and name - the
            gate matches a TooSmallEdge face by patch AND sub (28 and 29F had both read 'patch 29'; a match by patch alone named another edge of the patch)"""
            _p_ = t_[0]; _s_ = (t_[4] if (len(t_) > 4 and t_[4]) else None)
            for x_ in new_eds:
                if any(x_.isSame(y_) for y_ in old_eds): continue
                _wc_src.setdefault(_p_, []).append(("the wire-clean pass (31bq R7W)", x_))
                try:
                    if x_.Length < 0.1: _mq_ = x_.valueAt(0.5 * (x_.FirstParameter + x_.LastParameter)); _wc_micro.append({"patch": int(_p_), "sub": _s_, "face": _wc_name(t_), "len": round(float(x_.Length), 4), "mid": [round(float(_mq_.x), 3), round(float(_mq_.y), 3), round(float(_mq_.z), 3)]})
                except Exception: pass
        for _ti in range(len(_wf)):
            _tw = _wf[_ti]; _iw, _pw, _edsw = _tw[0], _tw[1], list(_tw[2]); _subw = _tw[4] if len(_tw) > 4 else None
            if _pw.get("kind") == "cap": _wc_notread += 1; continue
            if _subw in ("FV", "F*"): _wc_notread += 1; continue      
            try:
                if len(_edsw) < 3: _wc_skip.append("%s (%d edge(s))" % (_wc_name(_tw), len(_edsw))); continue
                _lpw = sorted(order_loops(list(_edsw), tol=_WC_TOL), key=lambda L_: -Part.makeCompound(list(L_)).BoundBox.DiagonalLength); _outw = _lpw[0]      
                _cl_, _gm_ = _wc_closed(_outw, _WC_TOL)
                if not _cl_: _wc_skip.append("%s (its outer loop is open by %.3f mm - over the construction tolerance, not the pass's to close)" % (_wc_name(_tw), _gm_)); continue
                _wc_read += 1
                
                # micro_edges
                # recorded
                for _se in [e_ for L2_ in _lpw[1:] for e_ in L2_ if e_.Length < _WC_TOL]:
                    _sa, _sb = _CL.ends(_se); _put = None
                    for _k2 in range(len(_outw)):
                        _pe = _CL.ends(_outw[_k2])[1]; _ne = _CL.ends(_outw[(_k2 + 1) % len(_outw)])[0]
                        if min(float(np.linalg.norm(_pe - _sa)), float(np.linalg.norm(_pe - _sb))) <= _WC_TOL and min(float(np.linalg.norm(_ne - _sa)), float(np.linalg.norm(_ne - _sb))) <= _WC_TOL: _put = _k2 + 1; break
                    if _put is None: continue
                    _outw = list(_outw[:_put]) + [_CL._orient(_se, _CL.ends(_outw[_put - 1])[1])] + list(_outw[_put:])
                    _lpw = [_outw] + [[e_ for e_ in L2_ if not e_.isSame(_se)] for L2_ in _lpw[1:]]; _lpw = [L2_ for L2_ in _lpw if L2_]
                    _wc_lines.append("face %d%s wire-clean: a %.4f mm edge the loop walk had left out (the loop closed within the tolerance before it) is put back at its junction (31bq R7Wn4b)" % (_iw, _subw or "", _se.Length))
                _frz_ = set(_wc_frozen) | {e_.hashCode() for e_ in _outw if any(_CL.same_edge(e_, y_) for y_ in _wc_fz_edges)}
                if _WC_DRY:      
                    _fs_ = _CL.find_slivers(_outw, tol=_WC_TOL); _wc_dry["loops"] += 1
                    for f_ in _fs_: _wc_dry[f_["kind"]] = _wc_dry.get(f_["kind"], 0) + 1
                    if sum(1 for f_ in _fs_ if f_["kind"] == "graze") >= 2: _wc_dry["double_graze_loops"] += 1
                    if _fs_: _wc_lines.append("face %d%s dry: %s" % (_iw, _subw or "", "; ".join("%s %s" % (f_["kind"], {k_: (round(v_, 4) if isinstance(v_, float) else v_) for k_, v_ in f_.items() if k_ != "kind"}) for f_ in _fs_[:6])))
                    continue
                _E2, _mvw, _how, _rpw = _CL.clean_loop(_outw, tol=_WC_TOL, say=lambda s_: _wc_lines.append("face %d%s %s" % (_iw, _subw or "", s_.strip())), frozen=_frz_)
            except Exception as _exw:
                say("   wire-clean: face %d%s could not be cleaned (%s) - its loop stands" % (_iw, _subw or "", str(_exw)[:80])); continue
            try:      
                _Jn = np.asarray([_CL.ends(e_)[0] for e_ in _E2], float); _nk = None
                for _a2 in range(len(_Jn)):
                    for _b2 in range(_a2 + 2, len(_Jn)):
                        if (_a2 == 0 and _b2 == len(_Jn) - 1): continue
                        if float(np.linalg.norm(_Jn[_a2] - _Jn[_b2])) < _WC_TOL: _nk = (_a2, _b2, float(np.linalg.norm(_Jn[_a2] - _Jn[_b2]))); break
                    if _nk: break
                if _nk:
                    _wc_neck += 1; say("   wire-clean: face %d%s - after the clean two junctions %.4f mm apart are NOT consecutive (junctions %d / %d): a NECK under the construction tolerance the pass cannot decide - its loop stands as built (31bq R7Wn4b, D4)" % (_iw, _subw or "", _nk[2], _nk[0], _nk[1])); continue
            except Exception: pass
            _wc_frz += len([m_ for m_ in _mvw if m_.get("kind") == "frozen"])
            for m_ in _mvw:
                if m_.get("kind") == "graze-failed": say("   wire-clean: face %d%s - a graze could not be cut (%s)" % (_iw, _subw or "", m_.get("why")))
                if m_.get("kind") == "short-skipped": say("   wire-clean: face %d%s - a %.4f mm edge was NOT dropped: %s" % (_iw, _subw or "", float(m_.get("len") or 0.0), m_.get("why")))
            if not _rpw: continue
            
            _vmv = [(np.asarray(a_, float), np.asarray(b_, float)) for m_ in _mvw for a_, b_ in (m_.get("vmoves") or [])]
            if _vmv and len(_wc_fpts) and any(float(np.linalg.norm(_wc_fpts - a_, axis=1).min()) <= _WC_TOL for a_, b_ in _vmv):
                say("   wire-clean: face %d%s - a vertex move would reach a frozen edge's end (the body's own, or a ready face's) - its loop stands as built" % (_iw, _subw or "")); continue
            _wc_faces += 1; _wc_moves += len([m_ for m_ in _mvw if m_.get("kind") in ("gap", "short", "graze")])
            _origs = {e_.hashCode(): e_ for e_ in _outw if e_.hashCode() in _rpw}      # ORIGINAL
            _inner = [e_ for e_ in _edsw if not any(e_.isSame(x_) for x_ in _outw)]
            _wf[_ti] = _wc_tuple(_tw, list(_E2) + _inner)
            _wc_take(_tw, _E2, _outw)      
            _handed = set()
            for _tj in range(len(_wf)):      
                if _tj == _ti: continue
                _tt = _wf[_tj]
                if _tt[1].get("kind") == "cap" or (_tt[4] if len(_tt) > 4 else None) in ("FV", "F*"): continue
                _edsj = list(_tt[2]); _hit = {}
                for _ej, e_ in enumerate(_edsj):
                    for _oh, _oe in _origs.items():
                        if _CL.same_edge(e_, _oe): _hit.setdefault(_oh, []).append(_ej); break
                _new = []; _chg = bool(_hit)
                for _ej, e_ in enumerate(_edsj):
                    _oh = next((k_ for k_, v_ in _hit.items() if _ej in v_), None)
                    if _oh is None:
                        _e2 = e_
                        for a_, b_ in _vmv:      
                            try:
                                if _e2.hashCode() in _wc_frozen: break
                                _ea, _eb = _CL.ends(_e2)
                                if np.linalg.norm(_ea - a_) <= _WC_TOL and np.linalg.norm(_ea - b_) > 1e-9: _e2 = _CL._orient(_CL.reend(_e2, _ea, b_), b_); _wc_vx += 1
                                elif np.linalg.norm(_eb - a_) <= _WC_TOL and np.linalg.norm(_eb - b_) > 1e-9: _e2 = _CL._orient_end(_CL.reend(_e2, _eb, b_), b_); _wc_vx += 1
                            except Exception: pass
                        if _e2 is not e_: _chg = True
                        _new.append(_e2); continue
                    if not e_.isSame(_origs[_oh]): _wc_copies += 1
                    _new.extend(_rpw[_oh]["others"])
                for _h in _how:      
                    _oa, _ob, _b1 = _h.get("cut_orig"), _h.get("split_orig"), _h["edge"]
                    if _oa not in _hit: continue
                    if _ob in _hit:      
                        _new = [x_ for x_ in _new if not x_.isSame(_b1)]; _wc_void += 1; _handed.add(id(_h)); _chg = True
                        say("   wire-clean: the %.3f mm border piece between the old vertex and the cut edge's new end is NOBODY'S - face %s holds both edges of the sliver (the two faces met along both): it takes the cut edge and the split edge's far piece, the sliver closes" % (_b1.Length, _wc_name(_tt)))
                    elif not any(x_.isSame(_b1) for x_ in _new):
                        _new.append(_b1); _wc_hand += 1; _handed.add(id(_h)); _chg = True
                        say("   wire-clean: the %.3f mm border piece between the old vertex and the cut edge's new end handed to face %s (it reaches the vertex along it)" % (_b1.Length, _wc_name(_tt)))
                    else: _handed.add(id(_h))
                if not _chg: continue
                _wf[_tj] = _wc_tuple(_tt, _new)
                _wc_take(_tt, _new, _edsj)      
            for _h in _how:
                if id(_h) not in _handed: _wc_lost += 1; say("   wire-clean: no face across the cut edge was found for the %.3f mm border piece (no other loop holds that edge, as the object or as a copy) - left out" % _h["edge"].Length)
        for _l in _wc_lines[:40]: say(_l)      
        if _wc_skip: say("   wire-clean: %d loop(s) NOT cleaned - %s%s" % (len(_wc_skip), "; ".join(_wc_skip[:12]), " ..." if len(_wc_skip) > 12 else ""))
        if _WC_DRY:
            say("WIRE-CLEAN DRY RUN (31bq R7Wn4): %d loop(s) read, nothing moved - %d gap(s), %d short edge(s), %d graze(s) (%d loop(s) with two or more), %d near stretch(es)" % (_wc_dry["loops"], _wc_dry["gap"], _wc_dry["short"], _wc_dry["graze"], _wc_dry["double_graze_loops"], _wc_dry["near"]))
        else:
            say("WIRE-CLEAN (31bq R7W): %d loop(s) of %d read cleaned at the construction tolerance %g mm (%d faces in all - %d caps / ready faces not read, %d loop(s) skipped, %d neck(s) left) - %d move(s); %d border piece(s) handed across, %d nobody's (the sliver between two faces), %d left out; %d copies of a changed edge made one object; %d edge(s) of other faces re-ended onto a moved vertex; %d move(s) skipped on a frozen edge (the body's own or a ready face's); %d pass-made edge(s) under 0.1 mm (solid_c.json wire_clean)%s" % (
                _wc_faces, _wc_read, _WC_TOL, len(_wf), _wc_notread, len(_wc_skip), _wc_neck, _wc_moves, _wc_hand, _wc_void, _wc_lost, _wc_copies, _wc_vx, _wc_frz, len(_wc_micro), "" if _wc_faces else " (nothing to clean)"))
            _todo_faces[:] = _wf      
            for _fi, _lst in _wc_src.items(): ORIG_FIL_SRC.setdefault(_fi, []).extend(_lst)
        WC_RECORD = {"tol": _WC_TOL, "dry": (_wc_dry if _WC_DRY else None), "loops_read": _wc_read, "not_read": _wc_notread, "necks": _wc_neck, "loops_cleaned": _wc_faces, "moves": _wc_moves, "handed": _wc_hand, "nobodys": _wc_void, "left_out": _wc_lost, "copies": _wc_copies, "vertex_reends": _wc_vx, "frozen_skips": _wc_frz, "skipped": _wc_skip[:40], "micro_edges": _wc_micro}
except Exception as _exwc:
    import traceback as _tbw; _frw = _tbw.extract_tb(sys.exc_info()[2])[-1]
    say("WIRE-CLEAN (31bq R7W): the pass failed (%s, %s line %d) - every loop stands as built (31bq R7Wn4: nothing was committed)" % (str(_exwc)[:120], os.path.basename(_frw.filename), _frw.lineno))
    WC_RECORD = {"failed": "%s (%s line %d)" % (str(_exwc)[:120], os.path.basename(_frw.filename), _frw.lineno)}
def _loop_area_and_corner(eds_):
    """a piece's loop: its own area (the fan triangulation about its centroid) and its sharpest corner (deg, point) - the reference a repaired face is
    measured against, and the place a split line goes when the fill could not follow"""
    try:
        polys_ = SP.edge_polys(list(eds_)); loop_, starts_, order_ = SP.order_loop(polys_); L_ = np.asarray(loop_, float); c_ = L_.mean(0)
        area_ = 0.5 * float(np.sum(np.linalg.norm(np.cross(L_ - c_, np.roll(L_, -1, 0) - c_), axis=1)))
        worst_ = (180.0, None)
        for s_ in starts_:
            a_ = L_[s_] - L_[s_ - 1]; b_ = L_[(s_ + 1) % len(L_)] - L_[s_]
            ang_ = 180.0 - float(np.degrees(np.arccos(np.clip(a_ @ b_ / max(np.linalg.norm(a_) * np.linalg.norm(b_), 1e-12), -1, 1))))      
            if ang_ < worst_[0]: worst_ = (ang_, L_[s_])
        return area_, worst_
    except Exception:
        return None, (None, None)
for i, p, eds, S_given, sub_, fk_ in _todo_faces:
    rec = {"patch": i, "kind": kind[i], "edges": len(eds), "_in": {e_.hashCode() for e_ in eds}}          # skin-wires
    if sub_ is not None: rec["sub"] = sub_
    if fk_ is not None and fk_ in FIL_MERGE:      
        rec["fillet_line"] = int(FIL_MERGE[fk_]["chain"]); rec["fillet_name"] = str(FIL_MERGE[fk_].get("name", FIL_MERGE[fk_]["chain"]))
    if FRAME and p["kind"] == "cap":
        fc = BFc[CAPB[i]]
        rec.update({"valid": bool(fc.isValid()), "how": "the body's own section face %d" % CAPB[i], "area": round(fc.Area, 3), "patch_area": p["area_mm2"], "tol": round(max(e.Tolerance for e in fc.Edges), 4), "wires": len(fc.Wires), "closed": True})
        faces.append(fc); frec.append(rec); continue
    if sub_ == "FV" and S_given is not None:
        # corner edge
        try:
            fc = S_given if S_given.ShapeType == "Face" else Part.Face(S_given)
            rec.update({"valid": bool(fc.isValid()), "how": "a ready face (the corner patch / the mitred blend)", "area": round(fc.Area, 3), "patch_area": p["area_mm2"], "tol": round(max([e.Tolerance for e in fc.Edges] + [0.0]), 4), "wires": len(fc.Wires), "closed": True, "holes": 0})
            if fc.isValid() and fc.Area > 1e-6: faces.append(fc); frec.append(rec); continue
            rec["fail"] = "the ready face: valid %s, area %.4f" % (fc.isValid(), fc.Area); frec.append(rec); say("patch %d%s: the ready face is %s" % (i, sub_, rec["fail"])); continue
        except Exception as ex:
            rec["fail"] = "ready face: %s" % str(ex)[:60]; frec.append(rec); say("patch %d%s: %s" % (i, sub_, rec["fail"])); continue
    if sub_ == "F*" and S_given is not None:
        
        try:
            fc = Part.Face(S_given)
            rec.update({"valid": bool(fc.isValid()), "how": "the blend surface with its natural bounds (tapered to the junction at both ends)", "area": round(fc.Area, 3), "patch_area": p["area_mm2"],
                        "tol": round(max(e.Tolerance for e in fc.Edges), 4), "wires": 1, "closed": True, "holes": 0})
            if fc.isValid() and fc.Area > 1e-6: faces.append(fc); frec.append(rec); continue
            rec["fail"] = "the natural-bounds blend face: valid %s, area %.4f" % (fc.isValid(), fc.Area); frec.append(rec); say("patch %d%s: the blend face with its natural bounds is %s" % (i, sub_, rec["fail"])); continue
        except Exception as ex:
            rec["fail"] = "natural face: %s" % str(ex)[:60]; frec.append(rec); say("patch %d%s: %s" % (i, sub_, rec["fail"])); continue
    try:
        wires = sorted([Part.Wire(g) for g in (order_loops(eds) if FRAME else Part.sortEdges(eds))], key=lambda w: -w.BoundBox.DiagonalLength)
    except Exception as ex:
        rec["fail"] = "wire: %s" % str(ex)[:60]; frec.append(rec); say("patch %d: WIRE FAILED %s" % (i, str(ex)[:60])); continue
    if not wires:
        rec["fail"] = "no edges"; frec.append(rec); say("patch %d (%s): NO EDGES (%.2f mm2)" % (i, p["kind"], p["area_mm2"])); continue
    rec["wires"] = len(wires); rec["closed"] = bool(wires[0].isClosed())
    
    inner = [w_ for w_ in wires[1:] if w_.isClosed()] if (HOLES and len(wires) > 1) else []
    rec["holes"] = len(inner)
    if S_given is not None: S = S_given
    elif p["kind"] == "cap": n, c0 = walls[p["wall"]]; S = Part.Plane(V3(*(n * c0)), V3(*n))
    elif kind[i] == "orig": S = BF[p["face"]].Surface
    elif i in PAT: S = PAT[i].bs
    else: rec["fail"] = "no surface - the span failed: %s" % str(recs.get(i, {}).get("fail", "?"))[:160]; frec.append(rec); continue
    if sub_ is None or (len(str(sub_)) == 1 and str(sub_) not in ("F", "S")):      
        try:
            _nb_, _lp_ = _not_borders(i, eds); _op_ = [(li_, l_) for li_, (c_, l_) in enumerate(_lp_) if not c_]
            if _nb_:
                rec["not_borders"] = _nb_; NOT_BORDER.append((i, sub_, _nb_))
                say("patch %3d%s %-7s NOT A BORDER - given %d edge(s) that are NOT a border of it: %s - the step named handed each over (31bq R6 / R7W: the instrument of B20)" % (
                    i, ("" if sub_ is None else sub_), p["kind"], len(_nb_), "; ".join("%.2f mm, %s%s, at %s (%s)" % (x_["len"], x_["origin"], (" - its distance NOT MEASURED" if x_.get("unmeasured") else ((", %.2f mm off the face's own mesh" % x_["off_mm"]) if x_.get("off_mm") is not None else "")), x_["mid"],
                        ("in the OUTER loop - the face is made WITH it" if x_["loop"] == 0 else "loop %d of %d%s - the face is made from its outer loop" % (x_["loop"], len(_lp_), "" if x_["loop_closed"] else ", OPEN"))) for x_ in _nb_[:6])))
            if _op_ and len(_lp_) > 1:
                rec["loops_open"] = [li_ for li_, l_ in _op_]
                say("patch %3d%s %-7s %d of its %d loop(s) do NOT close - %s (31bq R6 / R7W: the instrument of B20)" % (i, ("" if sub_ is None else sub_), p["kind"], len(_op_), len(_lp_), "; ".join("loop %d%s: %s" % (li_, " (the OUTER)" if li_ == 0 else "", ", ".join("%.2f mm %s" % (a_, b_) for a_, b_ in l_[:6]) + (" and %d more" % (len(l_) - 6) if len(l_) > 6 else "")) for li_, l_ in _op_[:4])))
        except Exception as _exnb: say("patch %d%s: the border check could not run (%s) - NOT TAKEN (31bq R6 / R7W)" % (i, ("" if sub_ is None else sub_), str(_exnb)[:100]))
    def mkface(S_, w_, inner_=None):
        if inner_:
            
            try:
                f_ = Part.Face(S_, w_); f_.cutHoles(list(inner_))
                if not f_.isValid() or len(f_.Wires) != 1 + len(inner_): raise ValueError("cutHoles: valid %s, %d wires" % (f_.isValid(), len(f_.Wires)))
            except Exception:
                f_ = Part.Face(S_, [w_] + list(inner_))
        else:
            f_ = Part.Face(S_, w_)
        if EDGE_FIX:
            sfe = Part.ShapeFix.Edge()
            for e in f_.Edges:
                for fn in (lambda: sfe.fixAddPCurve(e, f_, False, 1e-4), lambda: sfe.fixReversed2d(e, f_), lambda: sfe.fixSameParameter(e)):
                    try: fn()
                    except Exception: pass
        return f_
    try:
        fc = None; v0 = None
        tries_ = [("as built", S, wires[0], inner), ("wire reversed", S, wires[0].reversed(), inner)]
        if inner: tries_ += [("inner wires reversed", S, wires[0], [w_.reversed() for w_ in inner]), ("all reversed", S, wires[0].reversed(), [w_.reversed() for w_ in inner])]
        for nm_, S_, w_, in_ in tries_:
            try: cand = mkface(S_, w_, in_)
            except Exception: continue
            if v0 is None: v0 = cand.isValid()
            if cand.isValid() and cand.Area > 0: fc = cand; rec["how"] = nm_; break
            if fc is None or (cand.Area > 0 and fc.Area <= 0): fc = cand; rec["how"] = nm_ + " (not valid)"
        if fc is None: raise RuntimeError("no face from the wire")
        if not fc.isValid():
            # NOT VALID
            
            try:
                fc2 = fc.copy(); fc2.fix(1e-4, 1e-6, 1.0)
                
                _la, (_ca, _cp) = _loop_area_and_corner(eds) if sub_ is not None else (None, (None, None))
                _ref = _la if (sub_ is not None and _la) else (fc.Area if (sub_ is not None and fc.Area > 1e-6) else p["area_mm2"])
                def _keeps_loop(f2_):
                    """every edge the piece was given is still in the repaired face: the length within 2 %, the midpoint within 0.1 mm"""
                    try:
                        for e0_ in eds:
                            if e0_.Length < 1e-6: continue
                            m0_ = e0_.valueAt(0.5 * (e0_.FirstParameter + e0_.LastParameter))
                            if not any(abs(e1_.Length - e0_.Length) <= 0.02 * e0_.Length + 1e-3 and (e1_.valueAt(0.5 * (e1_.FirstParameter + e1_.LastParameter)) - m0_).Length <= 0.1 for e1_ in f2_.Edges): return e0_
                        return None
                    except Exception: return None
                _lost = _keeps_loop(fc2) if fc2.isValid() else None
                if fc2.isValid() and abs(fc2.Area - _ref) <= 0.25 * _ref + 0.5 and _lost is None: fc = fc2; rec["how"] = (rec.get("how") or "").replace(" (not valid)", "") + " + repaired"
                else:
                    rec["repair"] = "valid %s, area %.2f against the loop's %.2f%s" % (fc2.isValid(), fc2.Area, _ref, (" - the repair lost / trimmed a %.2f mm edge of the loop" % _lost.Length) if _lost is not None else "")
                    if sub_ is not None and _la:
                        rec["fail"] = "the surface does not take its loop (as built invalid; its repair %s) - %s%s" % (("trimmed the loop's %.2f mm edge" % _lost.Length) if _lost is not None else (("is invalid too: %s (%.1f mm2 against the loop's %.1f); as built: %s" % (_kchk(fc2), fc2.Area, _la, _kchk(fc))) if not fc2.isValid() else ("is the wrong region: %.1f mm2 against the loop's %.1f" % (fc2.Area, _la))), ("the kit-made junction piece's form is the kit's (the contacts' merge, the mitre - 31bq N), not a wire of yours" if str(sub_).startswith("F") else "split it with a wire where the fold or the sharp corner is"), (" (the loop's sharpest corner %.0f deg at %s)" % (_ca, np.round(_cp, 1).tolist())) if _ca is not None else "")
                        say("face %d piece %s%s: SPAN FAILED - %s" % (i, sub_, (" (fillet of line %s)" % rec["fillet_name"]) if rec.get("fillet_name") else "", rec["fail"])); _a6_say(i); frec.append(rec); continue      
            except Exception as ex2:
                rec["repair"] = "raised %s" % str(ex2)[:60]
        rec.update({"valid": bool(fc.isValid()), "valid_before_fix": bool(v0), "area": round(fc.Area, 3), "patch_area": p["area_mm2"], "tol": round(max(e.Tolerance for e in fc.Edges), 4)})
        if not fc.isValid():
            
            try:
                fc.check(True); _why = "the kernel's check passes - the face is unorientable as built"
            except Exception as exc:
                _why = "; ".join(sorted(set(l_.strip() for l_ in str(exc).splitlines() if l_.strip() and "BOP" not in l_)))[:160] or str(exc)[:120]
            _worst = (0.0, None)
            for e_ in fc.Edges:
                try:
                    _pts = [e_.valueAt(e_.FirstParameter + (e_.LastParameter - e_.FirstParameter) * t_) for t_ in np.linspace(0, 1, 15)]
                    _d = max((S.value(*S.parameter(q_)) - q_).Length for q_ in _pts)
                    _k = _chain_of(e_, i)
                    if _d > _worst[0]: _worst = (_d, _k)
                except Exception:
                    pass
            rec["why"] = _why; rec["worst_edge_mm"] = round(_worst[0], 3); rec["worst_chain"] = _worst[1]
            try:
                def _gap_e(e_):      
                    try: return max(((S.value(*S.parameter(q_)) - q_).Length for q_ in [e_.valueAt(e_.FirstParameter + (e_.LastParameter - e_.FirstParameter) * t_) for t_ in np.linspace(0, 1, 15)]), default=0.0)
                    except Exception: return -1.0
                _we_ = max(fc.Edges, key=_gap_e)
                rec["worst_origin"] = _edge_origin(_we_, i)
            except Exception: rec["worst_origin"] = "chain %s" % _worst[1]
            _self = "self-intersect" in _why.lower()
            if _self and i in PAT and p["kind"] != "orig":
                
                rec["fail"] = "its border crosses itself on the %s surface (the surface folds under it; worst edge %.3f mm off, chain %s)" % (recs.get(i, {}).get("span", "fitted"), _worst[0], _worst[1])
                say("face %d: SPAN FAILED - %s - %s" % (i, rec["fail"], _span_advice(str(rec["fail"])))); _a6_say(i); del rec["valid"]      
                frec.append(rec); continue
        if abs(fc.Area) < 0.01 and len(fc.Edges) <= 2:
            rec["fail"] = "degenerate (area %.4f, %d edges) - left out" % (fc.Area, len(fc.Edges)); del rec["valid"]
        else: faces.append(fc)
    except Exception as ex: rec["fail"] = "face: %s" % str(ex)[:80]
    frec.append(rec)
    if "fail" in rec or not rec.get("valid") or rec.get("wires", 1) > 1 or (SHOW_NUMBERS and (rec.get("tol", 0) > 0.1 or abs(rec.get("area", 0) - p["area_mm2"]) > 0.25 * p["area_mm2"] + 0.5)):
        if SHOW_NUMBERS:
            say("patch %3d %-7s wires %s closed %s -> %s" % (i, p["kind"], rec.get("wires"), rec.get("closed"), ("valid %s area %.2f (layout patch %.2f) tol %.3f" % (rec["valid"], rec["area"], p["area_mm2"], rec["tol"])) if "valid" in rec else rec.get("fail")))
        else:
            say("patch %3d%s %-7s %s" % (i, ("" if sub_ is None else sub_) + ((" (fillet of line %s)" % rec["fillet_name"]) if rec.get("fillet_name") else ""), p["kind"], (("NOT VALID - %s; worst border edge %.3f mm off its surface (%s); repair: %s - look at it (skin-look draws it yellow)"
                                                       % (rec.get("why", "?"), rec.get("worst_edge_mm", 0), rec.get("worst_origin", "chain %s" % rec.get("worst_chain")), rec.get("repair", "none"))) if "valid" in rec and not rec["valid"] else
                                                       ("%d wires" % rec.get("wires", 1)) if rec.get("wires", 1) > 1 else rec.get("fail", ""))))
for r_ in frec:
    if r_.get("wires", 1) > 1: say("   multi-loop patch %d (%s): %d wires%s" % (r_["patch"], r_["kind"], r_["wires"], (" - %d hole(s) kept" % r_["holes"]) if r_.get("holes") else " - the outer loop only (HOLES=0 or the inner loops are not closed)"))

MDv = K.MeshDist(Vu, F, k=12)
for f_, r_ in zip(faces, [r for r in frec if "valid" in r]):
    if not r_.get("valid") or not os.environ.get("VOXCHECK", "0") == "1": continue      
    try:
        Vt, Tt = f_.tessellate(0.2); Vt = np.array([[q.x, q.y, q.z] for q in Vt]); Tt = np.array(Tt)
        Cq = Vt[Tt].mean(axis=1) if len(Tt) else np.zeros((0, 3))
        if len(Cq) > 1500: Cq = Cq[np.random.RandomState(0).choice(len(Cq), 1500, replace=False)]
        dd = MDv(Cq) if len(Cq) else np.zeros(1)
        r_["vox_p95"] = round(float(np.percentile(dd, 95)), 3); r_["vox_max"] = round(float(dd.max()), 3)
    except Exception: pass
say("faces measured against the source mesh" if os.environ.get("VOXCHECK", "0") == "1" else ("faces: no voxel measurement (VOXCHECK off; the source mesh is the original) - the pictures judge the shape" if K.brep_source() else "faces: not measured against the voxel piece (VOXCHECK off) - the pictures judge the shape"))      
bad = sorted([r for r in frec if r.get("vox_max", 0) > 0.5], key=lambda r: -r["vox_max"])
if SHOW_NUMBERS and os.environ.get("VOXCHECK", "0") == "1": say("faces straying more than 0.5 mm from the source mesh: %d - %s" % (len(bad), ", ".join("p%d %.2f/%.2f" % (r["patch"], r["vox_p95"], r["vox_max"]) for r in bad[:15])))
try:      # recorded
    _bal_ = [(int(pi_), r_.get("balloon_mm")) for pi_, r_ in recs.items() if isinstance(r_, dict) and r_.get("balloon_note")]
    _bal_ += [(int(pi_), s_.get("balloon_mm")) for pi_, r_ in recs.items() if isinstance(r_, dict) for s_ in (r_.get("subs") or []) if isinstance(s_, dict) and s_.get("balloon_note")]
    if _bal_: say("NURBS FILLS THAT RISE past their border's height range (build_c.json balloon_mm / balloon_note; not refused - judge them in the look): %s%s" % (", ".join("face %d %.1f mm" % (a_, float(b_ or 0)) for a_, b_ in _bal_[:12]), (" and %d more" % (len(_bal_) - 12)) if len(_bal_) > 12 else ""))
    _un_ = [(int(pi_), r_.get("balloon_unmeasured")) for pi_, r_ in recs.items() if isinstance(r_, dict) and r_.get("balloon_unmeasured")]      # recorded
    _un_ += [(int(pi_), s_.get("balloon_unmeasured")) for pi_, r_ in recs.items() if isinstance(r_, dict) for s_ in (r_.get("subs") or []) if isinstance(s_, dict) and s_.get("balloon_unmeasured")]
    if _un_: say("SURFACES WHOSE RISE WAS NOT MEASURED (not judged - the look decides): %s%s" % ("; ".join("face %d (%s)" % (a_, str(b_)[:60]) for a_, b_ in _un_[:12]), (" and %d more" % (len(_un_) - 12)) if len(_un_) > 12 else ""))
    _tg_ = [int(pi_) for pi_, r_ in recs.items() if isinstance(r_, dict) and (r_.get("balloon_tess") or any(isinstance(s_, dict) and s_.get("balloon_tess") for s_ in (r_.get("subs") or [])))]      
    if _tg_: say("SURFACES WHOSE RISE WAS MEASURED ON THE 25 x 25 GRID ONLY (their tessellation failed or gave no point - a horn between the samples is not seen): face(s) %s" % sorted(set(_tg_))[:12])
except Exception: pass
nb = len(faces); nfail = sum(1 for r in frec if "fail" in r)
say("FACES: %d built (%d valid), %d failed; multi-loop patches %d; max tolerance %.3f" % (nb, sum(1 for r in frec if r.get("valid")), nfail,
    sum(1 for r in frec if r.get("wires", 1) > 1), max([r.get("tol", 0) for r in frec] + [0])))
if NOT_BORDER: say("NOT A BORDER: %d face(s) were given an edge that is no border of them - %s (build_c.json faces[].not_borders; 31bq R6 / R7W: the instrument of B20)" % (len(NOT_BORDER), "; ".join("patch %d%s: %s" % (a_, ("" if b_ is None else b_), ", ".join("%.2f mm %s%s" % (x_["len"], x_["origin"][:70], (" NOT MEASURED" if x_.get("unmeasured") else ((" %.2f mm off" % x_["off_mm"]) if x_.get("off_mm") is not None else ""))) for x_ in c_[:3])) for a_, b_, c_ in NOT_BORDER[:8])))
for r_ in frec: r_.pop("_in", None)
json.dump({"changed": {str(k): v for k, v in recs.items()}, "faces": frec, "edges": erec}, open(os.path.join(SK, "build_c.json"), "w"), indent=0, default=lambda o_: "<%s>" % type(o_).__name__)

def _rung(r):
    if re.match(r"^F(?:S|C|M|V|\d)", str(r.get("sub") or "")) or r.get("fillet_name"): return "fillet"          
    if r["kind"] in ("cap", "orig"): return r["kind"]
    rr = recs.get(r["patch"], {})
    if rr.get("plane"): return "flat"
    sp_ = rr.get("span")
    if sp_ == "split":
        sub_ = r.get("sub"); subrec = next((x_ for x_ in rr.get("subs", []) if x_.get("sub") == sub_), {})
        if subrec.get("fillet") is not None: return "fillet"      
        sp_ = subrec.get("span", "coons")
    if sp_ == "plane": return "flat"
    if sp_ == "coons": return "span"
    if sp_ == "nurbs": return "nurbs"
    if sp_ == "plate": return "plate"
    return "fit"                           
BUILT = [(np.array([f_.CenterOfMass.x, f_.CenterOfMass.y, f_.CenterOfMass.z]), float(f_.Area), r_) for f_, r_ in zip(faces, [r for r in frec if "valid" in r])]
Part.makeCompound(faces).exportBrep(os.path.join(SK, "faces_c.brep"))
if os.environ.get("FIL_DBG") == "1":
    
    try:
        _fv = [r_ for r_ in frec if "valid" in r_]
        _own = {}      
        for _i, _f in enumerate(faces):
            for _e in _f.Edges:
                if _e.Length < 1e-6: continue
                _own.setdefault(_e.hashCode(), []).append((_i, _e))
        _single = [(h_, v_[0]) for h_, v_ in _own.items() if len(v_) == 1]
        _rep = []
        for a_ in range(len(_single)):
            ha_, (ia_, ea_) = _single[a_]
            for b_ in range(a_ + 1, len(_single)):
                hb_, (ib_, eb_) = _single[b_]
                if ia_ == ib_ or abs(ea_.Length - eb_.Length) > 1e-3: continue
                ma_ = ea_.valueAt(0.5 * (ea_.FirstParameter + ea_.LastParameter)); mb_ = eb_.valueAt(0.5 * (eb_.FirstParameter + eb_.LastParameter))
                if (ma_ - mb_).Length > 1e-3: continue
                ra_ = _fv[ia_] if ia_ < len(_fv) else {}; rb_ = _fv[ib_] if ib_ < len(_fv) else {}
                given_ = "the same object was given to both (the face builder copied it in face %s)" % ("%s%s" % (rb_.get("patch"), rb_.get("sub", "")) if ha_ in rb_.get("_in", set()) else ("%s%s" % (ra_.get("patch"), ra_.get("sub", "")) if hb_ in ra_.get("_in", set()) else "?")) if (ha_ in rb_.get("_in", set()) or hb_ in ra_.get("_in", set())) else "two objects were given (the step that made the edges holds two copies)"
                _rep.append("%.2f mm at %s: faces %s%s (%s, tol %s) | %s%s (%s, tol %s) - %s" % (ea_.Length, [round(ma_.x, 1), round(ma_.y, 1), round(ma_.z, 1)], ra_.get("patch"), ra_.get("sub", ""), str(ra_.get("how", ""))[:28], ra_.get("tol"), rb_.get("patch"), rb_.get("sub", ""), str(rb_.get("how", ""))[:28], rb_.get("tol"), given_))
        _UNSHARED = _rep      
        if _rep: say("UNSHARED COPIES (31bp, FIL_DBG): %d edge(s) two faces hold as two copies of one curve (named below only if the shell does not close)" % len(_rep))
    except Exception as _exs: say("the sharing report failed: %s" % str(_exs)[:120])
if os.environ.get("FILLET_LINES"):      
    try:
        Part.makeCompound(faces).exportBrep(os.path.join(SK, "faces_lines_c.brep"))
        json.dump([{k_: r_.get(k_) for k_ in ("patch", "sub", "how", "valid", "area", "edges", "fail", "tol")} for r_ in frec if "valid" in r_], open(os.path.join(SK, "faces_lines_c.json"), "w"), indent=0)
    except Exception as _exd: say("faces_lines_c dump: %s" % str(_exd)[:80])
# skin-wires

# recorded

if os.environ.get("SKIN_PREFLIGHT") == "1":
    try:
        _pf_faces = {}
        for pi_ in chg:
            r_ = recs.get(pi_) or {}
            _pf_faces[str(int(pi_))] = {"span": ("plane" if r_.get("plane") else r_.get("span")), "fail": (str(r_.get("fail"))[:700] if r_.get("fail") else None), "guides": r_.get("guides"), "balloon_note": r_.get("balloon_note"), "secs": r_.get("secs"), "at_the_wall": A6_SAID.get(int(pi_))}      
        _pf_sf = sorted(int(pi_) for pi_ in chg if "fail" in (recs.get(pi_) or {}))
        
        _pf_pcs = [{"patch": r_.get("patch"), "sub": r_.get("sub"), "fail": str(r_.get("fail"))[:300]} for r_ in frec if r_.get("fail")]
        for p__ in _pf_pcs:
            try: _pp = int(p__["patch"])
            except (TypeError, ValueError): continue
            if _pp not in _pf_sf: _pf_sf.append(_pp)
            if str(_pp) in _pf_faces and not _pf_faces[str(_pp)].get("fail"): _pf_faces[str(_pp)]["fail"] = ("piece %s: " % p__["sub"] if p__.get("sub") else "") + p__["fail"]
        _pf_sf = sorted(set(_pf_sf))
        _pf_nfail_stage = sum(1 for r_ in frec if r_.get("fail"))
        if _pf_nfail_stage != len(_pf_pcs): say("PREVIEW: the face stage counts %d failure(s) and the record %d - a kit fault in the record; the verdict takes the larger" % (_pf_nfail_stage, len(_pf_pcs)))
        _pf_inv = [{"patch": r_.get("patch"), "sub": r_.get("sub")} for r_ in frec if "valid" in r_ and not r_.get("valid") and not r_.get("fail")]
        def _pf_line(k__):      
            try:
                _m__ = re.match(r"\s*(-?\d+)", str(k__[0] if isinstance(k__, (tuple, list)) else k__))
                return int(_m__.group(1)) if _m__ else None
            except Exception: return None
        _pf_made = set()      
        for k__, v__ in FIL_MERGE.items():
            try: _pf_made.add(int((v__ or {}).get("chain")) if (v__ or {}).get("chain") is not None else _pf_line(k__))
            except (TypeError, ValueError): _pf_made.add(_pf_line(k__))
        _pf_lines = {}; _sok_pf = set(int(f_["line"]) for f_ in FILLETS if f_.get("sharp_ok") and str(f_.get("line", "")).lstrip("-").isdigit())      
        for k_ in sorted(FILLET_LINES):
            if k_ in _pf_made:
                _fl = next((v__ for k__, v__ in FIL_MERGE.items() if str((v__ or {}).get("chain")) == str(k_) or _pf_line(k__) == k_), {})
                _pf_lines[str(k_)] = {"made": True, "ends": [str(x__) for x__ in (_fl.get("endkind") or [])], "r": _fl.get("r")}
            else:
                _pf_lines[str(k_)] = {"made": False, "sharp_ok": bool(k_ in _sok_pf), "why": str(FIL_NOT_MADE.get(k_, "not swept (its chain's corners failed, or a hole beside it)"))[:500]}      
        _pf = {"network_frame_md5": K.md5(os.path.join(SK, "network_frame.brep")), "tag": os.environ.get("TAG") or os.environ.get("LK_TAG"), "when": time.strftime("%Y-%m-%d %H:%M:%S"), "lines_pass": bool(FILLET_LINES),
               "faces": _pf_faces, "span_failed": _pf_sf, "pieces_failed": _pf_pcs, "faces_invalid": _pf_inv, "lines": _pf_lines, "not_made": sorted(int(k__) for k__, v__ in _pf_lines.items() if not v__["made"] and not v__.get("sharp_ok")), "sharp_ok": sorted(int(k__) for k__, v__ in _pf_lines.items() if v__.get("sharp_ok")),
               "made": sorted(int(k__) for k__, v__ in _pf_lines.items() if v__["made"]),
               "levers": {k__: os.environ.get(k__) for k__ in ("NURBS_RIM", "NURBS_WALL_RIM", "CORNER_DEG", "SPAN_STEP", "PLATE_BALLOON_MM", "PLATE_BALLOON_FRAC", "TAPER_X", "THIN_MM", "FIL_SMOOTH_MM", "CTRL_MM", "LAM") if os.environ.get(k__)}}
        json.dump(_pf, open(os.path.join(SK, "preflight.json"), "w", encoding="utf-8"), indent=1, default=str)
        say("PREVIEW (31br G1 / G2): %d changed face(s) spanned, %d FAILED%s; %d face-stage piece(s) failed%s; fillets: %d of %d decided made%s - skin\\preflight.json; nothing sewn (the preview ends here)"
            % (len(chg) - len(_pf_sf), len(_pf_sf), (" (faces %s)" % _pf_sf) if _pf_sf else "", len(_pf_pcs), (" (%s)" % ", ".join("%s%s" % (p__["patch"], p__["sub"] or "") for p__ in _pf_pcs[:6])) if _pf_pcs else "",
               len(_pf["made"]), len(_pf_lines), ((", NOT made: %s" % _pf["not_made"]) if _pf["not_made"] else "") + ((", %d standing SHARP by your sharp_ok: %s" % (len(_pf["sharp_ok"]), _pf["sharp_ok"])) if _pf.get("sharp_ok") else "")))
    except Exception as _expf:
        import traceback as _tbpf; _frpf = _tbpf.extract_tb(sys.exc_info()[2])[-1]
        say("PREVIEW (31br G1 / G2): the record could not be written - %s (%s line %d)" % (str(_expf)[:200], os.path.basename(_frpf.filename), _frpf.lineno))
    print("DONE", flush=True); raise SystemExit(0)
# ---- 5. shell, solid
faces = [x for f in faces for x in (f.Faces if f.ShapeType != "Face" else [f])]
try:
    with busy("Part.Shell of %d faces" % len(faces), 900): sh = Part.Shell(faces)
    say("Part.Shell: closed %s" % sh.isClosed())
except Exception as ex: say("Part.Shell threw: %s" % str(ex)[:80]); sh = None
if sh is None or not sh.isClosed():
    cp = Part.Compound(faces); t1 = time.time()
    with busy("sewShape of %d faces" % len(faces), 1200): cp.sewShape()
    shells = cp.Shells; say("sewShape: %d shell(s), closed %s (%.0fs)" % (len(shells), [s_.isClosed() for s_ in shells], time.time() - t1))
    if shells: sh = max(shells, key=lambda s_: len(s_.Faces))
def _edge_uses(sh_):
    """31bq PP (B16 (f)): every edge's USES over the shell's faces - a SEAM (an edge a periodic face holds twice: a cylinder's, a sphere's) counts twice for its
    face; f.Edges lists it once, and the count read every seam as a FREE edge (a valid cylinder failed 'a sliver face is missing'; a lines pass with a periodic
    blend face would drop a sound blend for it)"""
    m_ = {}
    for f_ in sh_.Faces:
        for e_ in f_.Edges:
            if e_.Length < 1e-6: continue           
            try: s_ = bool(e_.isSeam(f_))
            except Exception: s_ = False
            m_[e_.hashCode()] = m_.get(e_.hashCode(), 0) + (2 if s_ else 1)
    return m_
emap = _edge_uses(sh)
free = sum(1 for v in emap.values() if v == 1)
say("shell: %d faces, closed %s, free edges %d" % (len(sh.Faces), sh.isClosed(), free))

fpat = [r_["patch"] for r_ in frec if "valid" in r_]
cent = np.array([[f_.CenterOfMass.x, f_.CenterOfMass.y, f_.CenterOfMass.z] for f_ in faces])
def _mesh_props(f_, dev=0.02):
    """31bq R7W (A5): a face's centre and area from its OWN tessellation (a copy) - the kernel's Area / CenterOfMass are integrals over the face's pcurves and
    read garbage on a corrupt face (qq6's face 37: -1.8e18 mm2); (None, None) when it cannot be meshed"""
    try:
        V_, T_ = f_.copy().tessellate(dev); V_ = np.array([[q.x, q.y, q.z] for q in V_], float); T_ = np.array(T_, int).reshape(-1, 3)
        if not len(T_): return None, None
        a_ = 0.5 * np.linalg.norm(np.cross(V_[T_[:, 1]] - V_[T_[:, 0]], V_[T_[:, 2]] - V_[T_[:, 0]]), axis=1); A_ = float(a_.sum())
        if A_ <= 0: return None, None
        return (V_[T_].mean(1) * a_[:, None]).sum(0) / A_, A_
    except Exception: return None, None
def _kprops(f_):
    """the kernel's own centre and area of a face - (None, None) when they are not numbers (a corrupt face's integrals)"""
    try:
        c_ = f_.CenterOfMass; a_ = float(f_.Area); c_ = np.array([c_.x, c_.y, c_.z], float)
        return (c_, a_) if (np.all(np.isfinite(c_)) and np.isfinite(a_) and a_ > 0) else (None, None)
    except Exception: return None, None
_BK = [_kprops(f_) for f_ in faces]
def _same_built(f_):
    """31bq R7W (A5): the built face a shell face IS - its kernel centre within 1e-3 mm and its area within 1e-4 of it (the shell keeps a face it does not sew;
    FreeCAD 1.1's Part.Shell hands back new objects either way: identity is no test - vc1's sharp pass); None for a face its sewing rebuilt or whose integrals
    are garbage"""
    c_, a_ = _kprops(f_)
    if c_ is None: return None
    best_ = None
    for i_, (cb_, ab_) in enumerate(_BK):
        if cb_ is None: continue
        d_ = float(np.linalg.norm(cb_ - c_))
        if d_ <= 1e-3 and abs(ab_ - a_) <= 1e-4 * max(ab_, 1.0) and (best_ is None or d_ < best_[0]): best_ = (d_, i_)
    return None if best_ is None else best_[1]
_SH_IDX = [_same_built(f_) for f_ in sh.Faces]      
_in_sh = set(i for i in _SH_IDX if i is not None)
lost_i = [i for i in range(len(faces)) if i not in _in_sh]
lost = [fpat[i] for i in lost_i]
_fv0 = [r_ for r_ in frec if "valid" in r_]
say("faces not in the shell: patches %s%s" % (lost, "" if not lost_i else " - matched to no built face BY POSITION (the kernel's centre / area of the shell's face moved past 1e-3 mm / 1e-4 of the built face's, or its integrals are no numbers - the corrupt case; each is named by its own mesh below and FACE SANITY reads it): %s" % "; ".join("patch %s%s (%s, %.3f mm2 as built)" % (_fv0[i].get("patch"), _fv0[i].get("sub") or "", str(_fv0[i].get("how", ""))[:40], float(faces[i].Area)) for i in lost_i[:8])))
FREE = []
_fv = [r_ for r_ in frec if "valid" in r_]      
for f_ in sh.Faces:
    _fi = _same_built(f_); _fi = -1 if _fi is None else _fi      
    if _fi < 0:
        _mc8, _ma8 = _mesh_props(f_); _fi = int(np.argmin(np.linalg.norm(cent - _mc8, axis=1))) if (len(cent) and _mc8 is not None) else -1
    _own = ("patch %s%s" % (_fv[_fi].get("patch"), _fv[_fi].get("sub", ""))) if 0 <= _fi < len(_fv) else "?"      
    for e in f_.Edges:
        if e.Length >= 1e-6 and emap.get(e.hashCode()) == 1:
            m = e.valueAt(0.5 * (e.FirstParameter + e.LastParameter))
            dists = [(min(x_.distToShape(Part.Vertex(m))[0] for x_ in _flat_e([EDGES[k]])), k) for k in range(len(CH)) if EDGES[k] is not None]
            d0, k0 = min(dists)
            FREE.append({"chain": k0, "pair": CH[k0]["pair"], "type": CH[k0]["type"], "len": round(e.Length, 3), "dist": round(d0, 4), "mid": [round(m.x, 2), round(m.y, 2), round(m.z, 2)], "owner": _own})
for fr in FREE: say("   free edge %.3f mm on chain %d %s pair %s (%.4f from it) - owned by %s, mid %s" % (fr["len"], fr["chain"], fr["type"], fr["pair"], fr["dist"], fr["owner"], fr["mid"]))
if FREE and os.environ.get("FIL_DBG") == "1":
    try:
        _near = [l_ for l_ in (globals().get("_UNSHARED") or []) if any(abs(float(l_.split(" mm at ")[0]) - fr["len"]) < 0.5 and str([round(x, 1) for x in fr["mid"]]) in l_ for fr in FREE)]
        if _near:
            say("UNSHARED COPIES at the free edges (%d of %d):" % (len(_near), len(globals().get("_UNSHARED") or [])))
            for _l in _near[:20]: say("   " + _l)
    except Exception: pass
json.dump({"free": FREE, "lost": lost}, open(os.path.join(SK, "free_edges.json"), "w"), indent=1)
sh.exportBrep(os.path.join(SK, "shell_c.brep"))
fe = [e for f_ in sh.Faces for e in f_.Edges if e.Length >= 1e-6 and emap.get(e.hashCode()) == 1]
if fe: Part.makeCompound(fe).exportBrep(os.path.join(SK, "free_c.brep"))
res = {"faces": len(sh.Faces), "closed": bool(sh.isClosed()), "free_edges": free}
if os.environ.get("SAMEPARAM", "1") == "1":
    try:
        sh2 = sh.copy(); r_ = Part.ShapeFix.sameParameter(sh2, True, 1e-5)
        emap2 = _edge_uses(sh2)      
        say("sameParameter on the shell: %s; max edge tolerance %.4f; free edges after %d" % (r_, max(e.Tolerance for e in sh2.Edges), sum(1 for v in emap2.values() if v == 1)))
        if sh2.isClosed(): sh = sh2
    except Exception as ex: say("sameParameter failed: %s" % str(ex)[:100])

# recorded
if sh.isClosed():
    _emf_ = _edge_uses(sh); _sl_ = []
    for _fi_, _ff_ in enumerate(sh.Faces):
        for _ee_ in _ff_.Edges:
            if _ee_.Length >= 1e-6 and _emf_.get(_ee_.hashCode(), 0) == 1:
                _m_ = _ee_.valueAt(0.5 * (_ee_.FirstParameter + _ee_.LastParameter)); _sl_.append((_fi_, round(_ee_.Length, 3), [round(_m_.x, 2), round(_m_.y, 2), round(_m_.z, 2)]))
    res["slit_edges"] = _sl_
    if _sl_: say("SLIT: %d edge(s) held on BOTH sides by one face (not a seam) - a split or a strip edge that ends inside its face, the face not divided there: %s - the shell is closed and the solid stands; look at those faces (31bq B16)" % (len(_sl_), "; ".join("shell face %d, %.2f mm at %s" % s_ for s_ in _sl_[:6])))
if sh.isClosed():
    so = Part.Solid(sh)
    if so.Volume < 0: so.reverse()
    res.update({"valid": bool(so.isValid()), "volume": round(so.Volume, 1)})
    say("SOLID: valid %s, %d faces, volume %.1f" % (so.isValid(), len(so.Faces), so.Volume))
    
    OFF_TOL = float(os.environ.get("OFF_TOL", "0.02"))
    def _edge_gaps(so_):
        """31bq R5g (round 5's C7, B07 remaining 3): the edges' gaps on a solid - (tolerances raised, the largest projection gap, the largest pcurve gap, the edges NOT
        measured, the pcurves NOT measured); run on the sewn solid and again on the solid the kernel's fillets made (the record had held the sharp solid's gaps while the
        filleted one was written). 31bq R7W (M12, the C-gates review's finding 10): an edge whose sampling raised, a pcurve the kernel did not give or that raised, and the
        edges of a face whose surface could not be read are COUNTED - a maximum over a subset is no clearance (the gate's use of the count is the gate's)"""
        nraised = 0; worst_off = 0.0; worst_pc = 0.0; un_e = 0; un_p = 0
        try:      
            for f_ in so_.Faces:
                try: S_ = f_.Surface; E_f = list(f_.Edges)
                except Exception:
                    try: n__ = len(f_.Edges)
                    except Exception: n__ = 1
                    un_e += n__; un_p += n__; continue
                for e_ in E_f:
                    try:
                        P_ = [e_.valueAt(e_.FirstParameter + (e_.LastParameter - e_.FirstParameter) * t / 40.0) for t in range(41)]
                        dv_ = max(S_.value(*S_.parameter(x_)).distanceToPoint(x_) for x_ in P_)
                    except Exception: un_e += 1; un_p += 1; continue
                    worst_off = max(worst_off, dv_); _pg_e = 0.0      
                    try:      # recorded
                        _pc_ = f_.curveOnSurface(e_)
                        if _pc_:
                            _c2_, _a2_, _b2_ = _pc_[0], float(_pc_[1]), float(_pc_[2])
                            for _tt_ in np.linspace(_a2_, _b2_, 121):
                                _uv_ = _c2_.value(float(_tt_)); _pg_e = max(_pg_e, float((S_.value(_uv_.x, _uv_.y) - e_.valueAt(float(_tt_))).Length))
                            worst_pc = max(worst_pc, _pg_e)
                        else: un_p += 1
                    except Exception: un_p += 1
                    _gap_e = max(dv_, _pg_e)
                    want_ = _gap_e * 2.0 + 2e-5             
                    if want_ > e_.Tolerance and _gap_e <= OFF_TOL:
                        e_.fixTolerance(want_); nraised += 1
        except Exception as ex_:
            un_e += 1; un_p += 1; say("edge tolerances: %s - the measurement stopped there: the edges after it are NOT measured (counted; 31bq R7W)" % str(ex_)[:80])
        return nraised, worst_off, worst_pc, un_e, un_p
    with busy("edge gaps on %d faces" % len(so.Faces), 900): nraised, worst_off, worst_pc, _une, _unp = _edge_gaps(so)      
    if nraised: say("edge tolerances set to their measured gap on %d edge(s) (up to OFF_TOL %g); the largest gap of any edge from its face: %.4f mm" % (nraised, OFF_TOL, worst_off))
    res["edge_off_max"] = round(max(worst_off, worst_pc), 4); res["edge_proj_gap_max"] = round(worst_off, 4); res["pcurve_gap_max"] = round(worst_pc, 4)      
    res["edge_gaps_unmeasured"] = int(_une + _unp); res["edge_gaps_unmeasured_detail"] = {"edges": int(_une), "pcurves": int(_unp)}      # recorded
    if _une or _unp: say("edge gaps: %d edge(s) and %d pcurve(s) could NOT be measured - the largest gaps above are over the rest only (unmeasured is not clear: solid_c.json edge_gaps_unmeasured - 31bq R7W)" % (_une, _unp))
    if worst_pc > worst_off + 1e-3: say("edge gaps: the 3-D curves lie up to %.3f mm from their PCURVES on the faces (the projection reads %.3f) - the gap the BOP check's curve-on-surface test sees (31bq PP)" % (worst_pc, worst_off))
    # fillets.json
    
    nfil = 0; res["fillets"] = []; fil_failed = []; CREASE_BUILT = {}
    _sok_k = sorted(set(int(f_["line"]) for f_ in FILLETS if f_.get("sharp_ok") and str(f_.get("line", "")).lstrip("-").isdigit()))      
    if FILLETS and not so.isValid():
        # skin-build

        _done_ = {int(fl_["chain"]) for fl_ in FIL_MERGE.values()}
        _fl = [int(f_["line"]) for f_ in FILLETS if str(f_.get("line", "")).lstrip("-").isdigit() and int(f_["line"]) not in _done_ and not f_.get("sharp_ok")]      
        for _k in _sok_k: res["fillets"].append({"line": _k, "ok": False, "how": "sharp_ok", "why": "stands SHARP by your sharp_ok - not tried by the kernel, not swept by lines (31bx X76)"})
        fil_failed = list(_fl); FIL_RERUN = sorted(set(list(FILLET_LINES) + fil_failed + _sok_k)) if (fil_failed and FIT == "span" and os.environ.get("FILLET_RERUN", "1") == "1") else []
        for _k in _fl: res["fillets"].append({"line": _k, "ok": False, "why": "the solid is not valid - the kernel fillet was not tried"})
        say("FILLETS: %d decided fillet(s) NOT tried by the kernel - the solid is not valid (check(True) names the faces)%s"
            % (len(_fl), (" - the lines pass follows for %s" % FIL_RERUN) if FIL_RERUN else (" - no lines pass (FILLET_RERUN=0 or FIT != span): those edges stay sharp" if _fl else "")))
    if FILLETS and so.isValid():
        _done_ = {int(fl_["chain"]) for fl_ in FIL_MERGE.values()}      
        _dropped_env = set(int(x) for x in os.environ.get("FILLET_DROPPED", "").split(",") if x.strip().lstrip("-").isdigit())
        for f_ in FILLETS:
            if f_.get("sharp_ok"):      
                res["fillets"].append({"line": f_.get("line"), "r": f_.get("r"), "ok": False, "how": "sharp_ok", "why": "stands SHARP by your sharp_ok - not tried by the kernel, not swept by lines (31bx X76)"}); continue
            if int(f_["line"]) in _dropped_env:      
                res["fillets"].append({"line": int(f_["line"]), "r": float(f_["r"]), "ok": False, "why": "left out of this lines pass (the retry without it) - stands sharp"}); continue
            if int(f_["line"]) in _done_:
                res["fillets"].append({"line": int(f_["line"]), "r": float(f_["r"]), "ok": True, "how": "lines", "leg": f_.get("leg")}); continue
            _kcall_ = False      # makeFillet
            try:
                k_ = int(f_["line"]); r_ = float(f_["r"]); e0s_ = _flat_e([EDGES[k_]]) if k_ < len(EDGES) else []
                if f_.get("leg") is not None and isinstance(EDGES[k_], list) and str(f_["leg"]).strip().lower() != "all" and 0 <= int(f_["leg"]) < len(EDGES[k_]):
                    e0s_ = [EDGES[k_][int(f_["leg"])]]      
                if not e0s_: raise RuntimeError("line %d is not an edge of the piece" % k_)
                _ends = np.array([[e0s_[0].Vertexes[0].X, e0s_[0].Vertexes[0].Y, e0s_[0].Vertexes[0].Z], [e0s_[-1].Vertexes[-1].X, e0s_[-1].Vertexes[-1].Y, e0s_[-1].Vertexes[-1].Z]])
                if K.wall_dist(_ends).min() < 0.05:
                    raise RuntimeError("line %d ends on a wall of the edit region - a fillet there would change the body's own section face (the caps are exact; L97); the fillet must already be in the body outside, or the line ends inside" % k_)
                sel_ = []
                for e0_ in e0s_:
                    m_ = e0_.valueAt(0.5 * (e0_.FirstParameter + e0_.LastParameter)); pv_ = Part.Vertex(m_)
                    cand_ = sorted(((e_.distToShape(pv_)[0], i_) for i_, e_ in enumerate(so.Edges) if abs(e_.Length - e0_.Length) < max(0.05, 0.02 * e0_.Length)), key=lambda t: t[0])
                    if not cand_ or cand_[0][0] > 0.05: raise RuntimeError("line %d not found on the solid (nearest %.3f mm)" % (k_, cand_[0][0] if cand_ else 99))
                    sel_.append(so.Edges[cand_[0][1]])
                
                # fillet_creases.json
                try:
                    _em = sel_[len(sel_) // 2]; _mp = _em.valueAt(0.5 * (_em.FirstParameter + _em.LastParameter)); _fa = [f__ for f__ in so.Faces if any(e__.isSame(_em) for e__ in f__.Edges)]
                    if len(_fa) == 2:
                        
                        _nn = []
                        for f__ in _fa:
                            try:
                                _cm = f__.CenterOfMass; _dir = V3(_cm.x - _mp.x, _cm.y - _mp.y, _cm.z - _mp.z); _dir = _dir * (0.3 / max(_dir.Length, 1e-9))
                                _qn = f__.distToShape(Part.Vertex(_mp + _dir))[1][0][0]
                            except Exception: _qn = _mp
                            _u, _v = f__.Surface.parameter(_qn); _n1 = f__.normalAt(_u, _v)
                            try:
                                if so.isInside(_qn + _n1 * 0.05, 1e-6, True): _n1 = _n1 * (-1.0)
                            except Exception: pass
                            _nn.append(_n1)
                        _bb = float(np.degrees(np.arccos(max(-1.0, min(1.0, _nn[0].dot(_nn[1])))))); CREASE_BUILT[k_] = round(_bb, 1)
                        say("   fillet line %d: the crease AS BUILT is %.0f deg between the two faces' OUTWARD normals at its middle (the layout's mesh: see the room line)" % (k_, _bb))
                        if _bb < CREASE_MIN_DEG:
                            raise RuntimeError("NO CREASE AS BUILT: the two faces meet at %.0f deg at line %d (under CREASE_MIN_DEG %g) - the surfaces the ladder built are tangent there, nothing to round; if that corner is meant to be sharp and then rounded, decide the border as a crease (a split, a different surface beside it) - else drop the fillet entry" % (_bb, k_, CREASE_MIN_DEG))
                except RuntimeError: raise
                except Exception as _exc: say("   fillet line %d: the crease as built could not be measured (%s)" % (k_, str(_exc)[:60]))
                
                _ck_cid = _kernel_chain_of(f_)
                if _ck_cid is not None:
                    raise RuntimeError("skipped - a member of fillet chain %s - the chain is one blend with corners, made by the lines pass (31bq R7W chain-kernel)" % _ck_cid)
                
                # ORIGINAL
                try:
                    _rg = {}      
                    for r__ in frec:
                        if "patch" in r__ and not str(r__.get("sub", "")).startswith("F"):
                            try: _rg.setdefault(int(r__["patch"]), set()).add(str(_rung(r__)))
                            except Exception: pass
                    _pq = [int(x__) for x__ in CH[k_]["pair"]] if (isinstance(k_, int) and k_ < len(CH)) else []
                    if _pq and all(_rg.get(f__) and _rg[f__] <= {"nurbs", "coons", "plate", "span", "fit", "fitted"} for f__ in _pq):
                        raise RuntimeError("skipped - both faces are fills (%s): the kernel's fillet fails on NURBS fills at every radius (31bm); the lines pass makes it" % ", ".join("%d %s" % (f__, "/".join(sorted(_rg.get(f__) or []))) for f__ in _pq))
                except NameError: pass
                _kcall_ = True
                with busy("makeFillet on line %s" % k_, 600): so2_ = so.makeFillet(r_, sel_)
                # makeFillet
                if so2_.ShapeType != "Solid" and len(so2_.Solids) == 1 and not so2_.Solids[0].isNull(): so2_ = so2_.Solids[0]
                if not so2_.isValid() or so2_.ShapeType != "Solid" or abs(so2_.Volume) < 0.5 * abs(so.Volume):
                    raise RuntimeError("the fillet made an invalid or empty solid (valid %s, a %s, volume %.0f against %.0f)" % (so2_.isValid(), so2_.ShapeType, abs(so2_.Volume), abs(so.Volume)))
                so = so2_; nfil += 1; res["fillets"].append({"line": k_, "r": r_, "ok": True})
                say("FILLET: line %d rounded at R %g (%s) - %d faces now" % (k_, r_, f_.get("why", ""), len(so.Faces)))
            except Exception as ex_:
                
                why_w = ""; room_ok_ = False; _room_chain_ = None
                try:
                    if _kcall_ and str(f_.get("line", "")).lstrip("-").isdigit() and int(f_["line"]) < len(CH) and FIT == "span":
                        # corner edge
                        _leg_q = None if (f_.get("leg") is None or str(f_["leg"]).strip().lower() == "all") else int(f_["leg"])
                        _cm_ = _check_members(int(f_["line"]), _leg_q) if f_.get("chain") is not None else []
                        for _e_ in (_cm_ or [dict({"line": int(f_["line"]), "r": float(f_["r"])}, **({"leg": _leg_q} if _leg_q is not None else {}))]):
                            _fillet_lines(dict(_e_, check_only=True))
                        room_ok_ = True; _room_chain_ = f_.get("chain") if _cm_ else None
                except RuntimeError as exw_:
                    why_w = (" - AND " + str(exw_)) if ("does not fit" in str(exw_) or "NO CREASE" in str(exw_)) else ""      
                except Exception: why_w = ""
                res["fillets"].append({"line": f_.get("line"), "r": f_.get("r"), "ok": False, "why": (str(ex_)[:300] + why_w)[:1500]})
                _skipped_ = str(ex_).startswith("skipped")      
                say("FILLET by the kernel %s on line %s at R %s: %s%s" % ("SKIPPED" if _skipped_ else ("FAILED" if _kcall_ else "NOT TRIED"), f_.get("line"), f_.get("r"), str(ex_)[:300], "" if (_skipped_ or not _kcall_) else (why_w if why_w else ((" (the room beside the crease is enough for this R%s - the kernel's own failure on these surfaces; the lines pass follows)" % ((" - measured as fillet chain %s's member, its shared junctions the chain's corners" % _room_chain_) if _room_chain_ is not None else "")) if room_ok_ else ""))))      # NO CREASE
                if str(f_.get("line", "")).lstrip("-").isdigit() and "ends on a wall" not in str(ex_) and "NO CREASE" not in str(ex_): fil_failed.append(int(f_["line"]))      
        if nfil: res.update({"valid": bool(so.isValid()), "volume": round(so.Volume, 1), "faces": len(so.Faces)}); say("SOLID after %d fillet(s): valid %s, %d faces, volume %.1f" % (nfil, so.isValid(), len(so.Faces), so.Volume))
        try: json.dump({"network_frame_md5": K.md5(os.path.join(SK, "network_frame.brep")), "beta_built_deg": {str(k__): v__ for k__, v__ in CREASE_BUILT.items()}}, open(os.path.join(SK, "fillet_creases.json"), "w", encoding="utf-8"), indent=1)      
        except Exception: pass
        FIL_RERUN = sorted(set(list(FILLET_LINES) + fil_failed + _sok_k)) if (fil_failed and FIT == "span" and os.environ.get("FILLET_RERUN", "1") == "1") else []
    if nfil:      # 31bq R5g
        with busy("edge gaps on %d faces (after the kernel's fillets)" % len(so.Faces), 900): _nr2, _wo2, _wp2, _une2, _unp2 = _edge_gaps(so)      
        res["edge_off_max"] = round(max(_wo2, _wp2), 4); res["edge_proj_gap_max"] = round(_wo2, 4); res["pcurve_gap_max"] = round(_wp2, 4)
        res["edge_gaps_unmeasured"] = int(_une2 + _unp2); res["edge_gaps_unmeasured_detail"] = {"edges": int(_une2), "pcurves": int(_unp2)}
        if _une2 or _unp2: say("edge gaps after the kernel's fillets: %d edge(s) and %d pcurve(s) could NOT be measured (31bq R7W)" % (_une2, _unp2))
        say("edge gaps on the solid after the kernel's %d fillet(s): the largest %.4f mm (projection %.4f, pcurve %.4f); %d tolerance(s) set to their gap (31bq R5g)" % (nfil, max(_wo2, _wp2), _wo2, _wp2, _nr2))
    try:
        with busy("check(True) on the solid", 900): so.check(True)
        res["check"] = "OK"; say("check(True): OK")
    except Exception as ex: res["check"] = str(ex)[:400]; res["check_selfintersect"] = ("SelfIntersect" in str(ex)); say("check(True): %s" % str(ex)[:400])

    res["self_intersections"] = []; res["si_searched"] = False
    _SO_SAME = (nfil == 0 and len(so.Faces) == len(_SH_IDX))      
    _SO_MP = {}
    def _so_mesh(k__):
        k__ = int(k__)
        if k__ not in _SO_MP: _SO_MP[k__] = _mesh_props(so.Faces[k__])
        return _SO_MP[k__]
    def _built_of(k__):
        """31bq R7W (A5): solid face k's built record (BUILT, the faces given to the shell) - by position through the shell when no kernel fillet changed the
        solid, else (and for a face the shell's sewing rebuilt) by its own MESH's centre and area against the built faces'; None when no built face is it (a
        face the kernel's fillets made or changed). The kernel's centre + area key had named qq6's corrupt blend face 37 'patch 1, cap'"""
        k__ = int(k__)
        if _SO_SAME and _SH_IDX[k__] is not None: return _SH_IDX[k__]
        c__, a__ = _so_mesh(k__)
        if c__ is None or not BUILT: return None
        j__ = min(range(len(BUILT)), key=lambda j: float(np.linalg.norm(BUILT[j][0] - c__)) + abs(BUILT[j][1] - a__) / max(BUILT[j][1], 1.0))
        if float(np.linalg.norm(BUILT[j__][0] - c__)) > 0.5 or abs(BUILT[j__][1] - a__) > 0.1 * max(BUILT[j__][1], 1.0): return None
        return j__
    def _face_name(k__):      
        try:
            j__ = _built_of(k__)
            if j__ is None: return "%d (a face the fillets made or changed)" % int(k__)
            r__ = BUILT[j__][2]; return "%d (patch %s%s, %s%s)" % (int(k__), r__.get("patch"), r__.get("sub") or "", _rung(r__), (" of line %s" % r__.get("fillet_name")) if r__.get("fillet_name") is not None else "")      
        except Exception: return str(k__)
    res["si_names"] = {}
    if res.get("check_selfintersect") or "SelfIntersect" in str(res.get("check", "")) or len(so.Faces) <= 400:      
        try:
            _fs = so.Faces; _eh = [set(e_.hashCode() for e_ in f_.Edges) for f_ in _fs]; _si = []; _skipped_pairs = 0
            _FMESH = {}; _si_border = []
            
            # confirmed
            _SI_DEFL = 0.015; _SI_BAND = 2.0 * _SI_DEFL; _SEAM_TOL = 0.02; _RMESH = {}; _si_faces = {}; _si_kcut = [0, 0, 0]; _RLOST = {}; _si_inc = {}
            _SI_LOST_REACH = 0.5
            _nbr = [set(j__ for j__ in range(len(_fs)) if j__ != i__ and (_eh[i__] & _eh[j__])) for i__ in range(len(_fs))]      
            def _fmesh(f__):
                """31bq PP (B16 (c) 2): a face's OWN mesh for the depth walk - a COPY tessellated at 0.015 mm (the piece's faces keep no new triangulation: a
                picture mesh must never reuse a per-face one - K-MESH-CRACKS), its triangles' normals, its BORDER edges (used once), a centroid tree; 31bq R7W: the
                border's vertices and each one's border neighbours (A7 / A8) and the face itself (A8: the kernel's word on a walking point)"""
                h__ = f__.hashCode()
                if h__ in _FMESH: return _FMESH[h__]
                out__ = None
                try:
                    pts__, tri__ = f__.copy().tessellate(_SI_DEFL)
                    V__ = np.array([[q.x, q.y, q.z] for q in pts__], float); T__ = np.array(tri__, int).reshape(-1, 3)
                    if len(T__):
                        E__ = np.sort(np.concatenate([T__[:, [0, 1]], T__[:, [1, 2]], T__[:, [2, 0]]]), axis=1); Eu__, cnt__ = np.unique(E__, axis=0, return_counts=True)
                        C__ = V__[T__].mean(1); Rt__ = np.linalg.norm(V__[T__] - C__[:, None, :], axis=2).max(1)
                        N__ = np.cross(V__[T__[:, 1]] - V__[T__[:, 0]], V__[T__[:, 2]] - V__[T__[:, 0]]); N__ /= np.maximum(np.linalg.norm(N__, axis=1), 1e-12)[:, None]
                        Be__ = Eu__[cnt__ == 1]; badj__ = {}
                        for a__, b__ in Be__.tolist(): badj__.setdefault(int(a__), []).append(int(b__)); badj__.setdefault(int(b__), []).append(int(a__))
                        out__ = {"V": V__, "T": T__, "N": N__, "C": C__, "Rt": Rt__, "Rmax": float(Rt__.max()), "kd": cKDTree(C__), "border": set(map(tuple, Be__.tolist())),
                                 "bverts": set(badj__), "badj": badj__, "size": float(np.linalg.norm(V__.max(0) - V__.min(0))), "face": f__, "lo": V__.min(0), "hi": V__.max(0)}      
                except Exception: out__ = None
                _FMESH[h__] = out__; return out__
            def _foot1(M__, p__):
                """the nearest point of mesh M to p (exact over the triangles that can hold it), its distance, the triangle, and whether it is a TRUE FOOT -
                inside a triangle, or on an edge the mesh shares; a point beyond the face lands on its BORDER (a snapped projection: NN's walk read 12.5 mm for a
                0.2 mm-deep strip whose surface the face covers whole). 31bq R7W (A7, the A2 review): a foot AT A VERTEX (two weights zero) is a true foot only when
                that vertex is not on the border - a point beyond a border vertex reached through a fan triangle whose own two edges there are interior had been one
                (a way ran on past the other face's corner: 6.42 mm for a 0.108 mm way in 480 of 720 fan orders); an edge foot tests that edge"""
                kd__ = M__["kd"]; V__ = M__["V"]; T__ = M__["T"]; C__ = M__["C"]; Rt__ = M__["Rt"]
                _d0, _j0 = kd__.query(p__); cand__ = np.asarray(kd__.query_ball_point(p__, float(_d0) + M__["Rmax"]), int)
                if len(cand__) > 1: cand__ = cand__[np.linalg.norm(C__[cand__] - p__, axis=1) - Rt__[cand__] <= float(_d0) + 1e-9]
                if not len(cand__): cand__ = np.array([int(_j0)])
                Q__ = K._closest_pt_tri(p__[None, :], V__[T__[cand__, 0]], V__[T__[cand__, 1]], V__[T__[cand__, 2]]); D__ = np.linalg.norm(Q__ - p__[None, :], axis=1)
                k__ = int(np.argmin(D__)); t__ = int(cand__[k__]); q__ = Q__[k__]; d__ = float(D__[k__])
                a__, b__, c__ = V__[T__[t__, 0]], V__[T__[t__, 1]], V__[T__[t__, 2]]
                v0 = b__ - a__; v1 = c__ - a__; v2 = q__ - a__; d00 = float(v0 @ v0); d01 = float(v0 @ v1); d11 = float(v1 @ v1); d20 = float(v2 @ v0); d21 = float(v2 @ v1); den = d00 * d11 - d01 * d01
                if abs(den) < 1e-30: return q__, d__, t__, False
                wb = (d11 * d20 - d01 * d21) / den; wc = (d00 * d21 - d01 * d20) / den; wa = 1.0 - wb - wc; tri = T__[t__]; on_ = []
                if wa < 1e-7: on_.append(tuple(sorted((int(tri[1]), int(tri[2])))))
                if wb < 1e-7: on_.append(tuple(sorted((int(tri[0]), int(tri[2])))))
                if wc < 1e-7: on_.append(tuple(sorted((int(tri[0]), int(tri[1])))))
                if d__ < 1e-5: return q__, d__, t__, True
                if len(on_) >= 2:      
                    _vx = [int(tri[k_]) for k_, w_ in ((0, wa), (1, wb), (2, wc)) if w_ >= 1e-7]
                    return q__, d__, t__, (len(_vx) == 1 and _vx[0] not in M__["bverts"])
                return q__, d__, t__, not any(e_ in M__["border"] for e_ in on_)
            def _near_mesh(M__, p__, tol__):
                """31bq R7W (A8): whether mesh M comes within tol of the point p (point-to-triangle over the triangles that can reach it)"""
                cand__ = np.asarray(M__["kd"].query_ball_point(p__, tol__ + M__["Rmax"]), int)
                if not len(cand__): return False
                Q__ = K._closest_pt_tri(p__[None, :], M__["V"][M__["T"][cand__, 0]], M__["V"][M__["T"][cand__, 1]], M__["V"][M__["T"][cand__, 2]])
                return bool(float(np.linalg.norm(Q__ - p__[None, :], axis=1).min()) <= tol__)
            def _on_seam(MU__, k__, q__, t__):
                """31bq R7W (A8): a foot on member k's BORDER is a foot of the union only INSIDE a seam - every border edge of k it touches (the one it lies on; both
                at a border vertex) has both its ends on another member within _SEAM_TOL. At a seam's END (the union's own corner) it is no foot - the P-depth-narrow
                review's NIT: the R6 patch's seam rule (the foot within 0.02 of another member) had let a point past the union's corner in as a snapped projection"""
                Mk__ = MU__["mem"][k__]; tri__ = Mk__["T"][t__]; V__ = Mk__["V"]
                a__, b__, c__ = V__[tri__[0]], V__[tri__[1]], V__[tri__[2]]
                v0 = b__ - a__; v1 = c__ - a__; v2 = q__ - a__; d00 = float(v0 @ v0); d01 = float(v0 @ v1); d11 = float(v1 @ v1); d20 = float(v2 @ v0); d21 = float(v2 @ v1); den = d00 * d11 - d01 * d01
                if abs(den) < 1e-30: return False
                wb = (d11 * d20 - d01 * d21) / den; wc = (d00 * d21 - d01 * d20) / den; W3__ = (1.0 - wb - wc, wb, wc); zs__ = [k_ for k_ in range(3) if W3__[k_] < 1e-7]
                if len(zs__) == 2:      
                    v__ = int(tri__[[k_ for k_ in range(3) if k_ not in zs__][0]])
                    if v__ not in Mk__["badj"]: return False
                    eds__ = [(v__, u__) for u__ in Mk__["badj"][v__]]
                elif len(zs__) == 1:      
                    e__ = tuple(sorted((int(tri__[(zs__[0] + 1) % 3]), int(tri__[(zs__[0] + 2) % 3]))))
                    if e__ not in Mk__["border"]: return False
                    eds__ = [e__]
                else: return False
                oth__ = [M2__ for k2__, M2__ in enumerate(MU__["mem"]) if k2__ != k__]
                for e__ in eds__:
                    for vv__ in e__:
                        if not any(_near_mesh(M2__, V__[vv__], _SEAM_TOL) for M2__ in oth__ if _boxd(M2__, V__[vv__]) <= _SEAM_TOL): return False      
                return True
            def _foot(M__, p__):
                """the foot on a reference: one face's own mesh (_foot1), or a UNION (_rmesh, 31bq R7W A8) - each member's own foot, the nearest (a true one first among
                equals); a foot on a member's border inside a seam with another member is a true foot of the union (_on_seam). The triangle index is into the
                union's stacked normals"""
                if M__.get("mem") is None: return _foot1(M__, p__)
                
                bd__ = np.linalg.norm(np.maximum(np.maximum(M__["lo"] - p__, p__ - M__["hi"]), 0.0), axis=1); rs__ = {}; dmin__ = np.inf
                for k_ in np.argsort(bd__, kind="stable"):
                    if float(bd__[k_]) > dmin__ + 1e-7: break
                    rs__[int(k_)] = _foot1(M__["mem"][int(k_)], p__); dmin__ = min(dmin__, rs__[int(k_)][1])
                ks__ = sorted(rs__, key=lambda k_: (rs__[k_][1] > dmin__ + 1e-7, not rs__[k_][3], rs__[k_][1], k_))
                k__ = ks__[0]; q__, d__, t__, tf__ = rs__[k__]
                if not tf__: tf__ = _on_seam(M__, k__, q__, t__)
                return q__, d__, int(M__["toff"][k__] + t__), tf__
            def _rkey(r__, w__):
                """31bq R7W: the reference union's members - r and r's neighbours, less w. fix-depth-F3F4 (F.4): THE WHOLE SURFACE BEYOND r - every face reachable from r
                through shared edges without passing through w (r's neighbours ONE ring away had ended a walk on the union's own border: on a valid fin whose bottom lies two or
                three rings from its wall the floor's arm ran on along the chamfer past the far wall and read 0.421 for a 0.30 mm poke, 0.352 for 0.25 - false FAILs;
                R7W/fix-depth-F3F4/out/f4_rings_ctrl.txt / f4_rings3_ctrl.txt; under a floor of narrow strips one ring read 0.079 for 0.341 - out/f4_strips.txt). The
                queries prune by the members' boxes (exact), so the far faces cost nothing but their mesh"""
                seen__ = {int(r__)}; front__ = [int(r__)]
                blk__ = {int(w__)} | set(int(n__) for n__ in _nbr[w__] if n__ != r__ and n__ not in _nbr[r__])      
                while front__:
                    nxt__ = []
                    for f__ in front__:
                        for n__ in _nbr[f__]:
                            if n__ not in blk__ and n__ not in seen__: seen__.add(int(n__)); nxt__.append(int(n__))
                    front__ = nxt__
                return tuple([int(r__)] + sorted(x__ for x__ in seen__ if x__ != int(r__)))
            def _boxd(M__, p__):
                """fix-depth-F3F4 (F.4): the distance from p to mesh M's box - a lower bound of its distance to the mesh"""
                return float(np.linalg.norm(np.maximum(np.maximum(M__["lo"] - p__, p__ - M__["hi"]), 0.0)))
            def _far_from(m__, w__):
                """fix-depth-F3F4 (F.4): True when face m's B-rep box lies farther than _SI_LOST_REACH from face w's (a B-rep box may over-report - the bound only errs toward near)"""
                try:
                    a__ = _fs[m__].BoundBox; b__ = _fs[w__].BoundBox
                    g__ = [max(0.0, a__.XMin - b__.XMax, b__.XMin - a__.XMax), max(0.0, a__.YMin - b__.YMax, b__.YMin - a__.YMax), max(0.0, a__.ZMin - b__.ZMax, b__.ZMin - a__.ZMax)]
                    if float(np.linalg.norm(g__)) > _SI_LOST_REACH: return True
                    return float(_fs[m__].distToShape(_fs[w__])[0]) > _SI_LOST_REACH      
                except Exception: return False
            def _rmesh(r__, w__):
                """31bq R7W (A8 - round 5's #17, the open list's item 2 redone): THE SURFACE BEYOND A NARROW FACE - the reference a walk on face w is measured against:
                face r's own mesh and its NEIGHBOURS' (a shared edge in the solid), less w alone - a neighbour can only shorten a way (its border foot is no foot, or
                the side turns at a concave edge), never lengthen one past the solid's surface. A crossing through a narrow face (a blend strip 1.5-3 mm wide) is
                followed under the faces beyond that face's border instead of ending there at about half its width. Each member keeps its own mesh; r's own mesh
                when no neighbour is left. fix-depth-F3F4 (F.4) - the words: the members are _rkey's - the WHOLE surface beyond r, every face reachable from it
                without passing through w (one ring ended a walk on the union's own border); a member with no mesh counts LOST only near w (_far_from)"""
                key__ = _rkey(r__, w__); mem__ = list(key__)
                if key__ in _RMESH: return _RMESH[key__]
                M0__ = _fmesh(_fs[mem__[0]]); Ms__ = []; fs__ = []; _lost__ = 0
                if M0__ is not None:
                    for m__ in mem__:
                        M__ = M0__ if m__ == mem__[0] else _fmesh(_fs[m__])
                        if M__ is None:
                            if not _far_from(m__, w__): _si_kcut[2] += 1; _lost__ += 1      
                            continue
                        Ms__.append(M__); fs__.append(m__)
                if not Ms__: out__ = None
                elif len(Ms__) == 1: out__ = Ms__[0]
                else: out__ = {"mem": Ms__, "faces": fs__, "toff": np.cumsum([0] + [len(M__["T"]) for M__ in Ms__[:-1]]), "N": np.vstack([M__["N"] for M__ in Ms__]),
                               "lo": np.array([M__["lo"] for M__ in Ms__]), "hi": np.array([M__["hi"] for M__ in Ms__])}      
                _RMESH[key__] = out__; _RLOST[key__] = _lost__; return out__
            def _dom_foot(f__, p__):
                """31bq R7W (2nd round, the verifier's change 1): the point's ORTHOGONAL foot on the face's own surface (Surface.parameter / value, normalAt - the
                face's orientation) and whether it lies inside the face's TRIMMED domain (isPartOfDomain: its pcurves) - (True / False, the distance), or (None, None)
                when the kernel cannot answer. The support type of distToShape is NOT the test: next to an edge of large tolerance it says Edge where the pcurve domain
                still holds the foot (crafted: a 0.412 mm crossing cut back to 0.280, a false PASS; the agent's b16 13 x 15 cut to 0.098 against its 0.244 truth)"""
                try:
                    S__ = f__.Surface; u__, v__ = S__.parameter(V3(float(p__[0]), float(p__[1]), float(p__[2]))); q__ = S__.value(u__, v__)
                    qq__ = np.array([q__.x, q__.y, q__.z], float); d__ = float(np.linalg.norm(p__ - qq__)); n__ = f__.normalAt(u__, v__); nn__ = np.array([n__.x, n__.y, n__.z], float)
                    s__ = abs(float((p__ - qq__) @ nn__)) / max(float(np.linalg.norm(nn__)), 1e-12)
                    return bool((d__ < 1e-4 or s__ >= 0.995 * d__) and f__.isPartOfDomain(u__, v__)), d__
                except Exception: return None, None
            def _kernel_on(MR__, p__):
                """31bq R7W (A8; 2nd round): the KERNEL's word on a walking point against the reference - for the one or two members nearest by mesh, the point's
                orthogonal foot on the member's own surface INSIDE its trimmed domain (_dom_foot) -> (True, its distance); none inside, but the two members' nearest
                points (distToShape) both on an EDGE at one point (a seam inside the union) -> (True, d); else (False, d): the point is past the reference (a fold or
                a stretch of the mesh beyond the face's pcurve domain). Any member the kernel cannot answer for -> (None, None): the mesh's reading stands"""
                Ms__ = MR__["mem"] if MR__.get("mem") is not None else [MR__]
                if len(Ms__) > 2:      
                    bd__ = np.linalg.norm(np.maximum(np.maximum(MR__["lo"] - p__, p__ - MR__["hi"]), 0.0), axis=1); dd__ = {}
                    for k_ in np.argsort(bd__, kind="stable"):
                        if len(dd__) >= 2 and float(bd__[k_]) > sorted(dd__.values())[1]: break
                        dd__[int(k_)] = _foot1(Ms__[int(k_)], p__)[1]
                    Ms__ = [Ms__[k_] for k_ in sorted(dd__, key=lambda k_: (dd__[k_], k_))[:2]]
                ans__ = []
                for M__ in Ms__:
                    f__ = M__.get("face")
                    if f__ is None: return None, None
                    _si_kcut[1] += 1; ok__, d__ = _dom_foot(f__, p__)
                    if ok__ is None: return None, None
                    if ok__: return True, d__
                    ans__.append((f__, d__))
                if len(ans__) > 1:
                    try:
                        got__ = []
                        for f__, _d in ans__:
                            d__, pt__, inf__ = f__.distToShape(Part.Vertex(float(p__[0]), float(p__[1]), float(p__[2])))
                            got__.append((float(d__), str(inf__[0][0]), np.array([pt__[0][0].x, pt__[0][0].y, pt__[0][0].z], float)))
                        got__.sort(key=lambda x__: x__[0])
                        if got__[0][1] == "Edge" and got__[1][1] == "Edge" and (got__[1][0] - got__[0][0]) <= _SEAM_TOL and float(np.linalg.norm(got__[1][2] - got__[0][2])) <= _SEAM_TOL: return True, got__[0][0]
                    except Exception: pass
                return False, min(d__ for _f, d__ in ans__)
            def _walk(MW, MR, s0, d0, cap):
                """walk on face W from s0 along d0 - re-anchored on W's mesh at every step, the step growing 1.6x and halving at each end (W's border, or where the
                point no longer projects onto R as a true foot: the end found within 5 um) - and return the largest distance of W's points from R on the way.
                31bq R5a (round 5's C4, NEW #16): SIGNED by R's own triangle normal - the way ENDS where it crosses R again (a scrape that dips under R and comes back
                out reads its dip, never the separation beyond the second crossing). 31bq R7W (A6, the A2 review): the side - and a crossing back - only PAST
                _SI_BAND, the two 0.015 mm meshes' own disagreement (at 2e-4 mm the tessellation's noise took the side on the first step, the real side then read as
                a crossing back and the way ended at 0.002 mm: a deep crossing at 5-12 deg read 0.000 in 9 of 72 crafted draws). R7W (A8): R may be a union
                (_rmesh); the way's largest reading is confirmed by the KERNEL (_kernel_on) - a stretch the kernel puts past the reference is cut back to the last
                confirmed step (the confirmed stretch a prefix of the way) and the exit refined by six halvings. Returns (the distance, the side the way went to:
                +1 / -1, 0 when it never left the band, the steps taken)"""
                p = np.asarray(s0, float).copy(); dirn = np.asarray(d0, float).copy(); w = 0.0; h = 0.05; e = 0.0; hmax = max(0.5, 0.05 * cap); sg_ = 0; ns_ = 0; hist_ = []
                for _it in range(600):
                    if w >= cap or h < 0.005: break
                    q, dq, tq, okq = _foot(MW, p + dirn * h)
                    if not okq: h *= 0.5; continue
                    st = q - p; L = float(np.linalg.norm(st))
                    if L < 1e-7: h *= 0.5; continue
                    qr, dr, tr, okr = _foot(MR, q)
                    if not okr: h *= 0.5; continue
                    sd_ = 1 if float((q - qr) @ MR["N"][tr]) > 0 else -1
                    if dr > _SI_BAND:      
                        if sg_ == 0: sg_ = sd_
                        elif sd_ != sg_: break
                    dirn = st / L; p = q; w += L; e = max(e, dr); h = min(h * 1.6, hmax); ns_ += 1; hist_.append((dr, q, sd_))
                if hist_ and e > _SI_BAND:
                    im_ = int(np.argmax([x_[0] for x_ in hist_]))
                    if _kernel_on(MR, hist_[im_][1])[0] is False:      # confirmed
                        _si_kcut[0] += 1; lo_, hi_ = -1, im_
                        while hi_ - lo_ > 1:
                            mid_ = (lo_ + hi_) // 2
                            if _kernel_on(MR, hist_[mid_][1])[0] is not False: lo_ = mid_
                            else: hi_ = mid_
                        e = max([x_[0] for x_ in hist_[:lo_ + 1]] or [0.0]); sg_ = next((x_[2] for x_ in hist_[:lo_ + 1] if x_[0] > _SI_BAND), 0)
                        a_ = hist_[lo_][1] if lo_ >= 0 else np.asarray(s0, float); b_ = hist_[hi_][1]
                        for _r in range(6):      # confirmed  confirmed
                            m_, dm_, tm_, okm_ = _foot(MW, 0.5 * (a_ + b_))
                            if not okm_: break
                            ok_, dk_ = _kernel_on(MR, m_)
                            if ok_ is not False:
                                a_ = m_
                                if dk_ is not None: e = max(e, dk_)
                            else: b_ = m_
                return e, sg_, ns_
            def _si_depth(fa__, fb__, eds__, ia__=None, ib__=None):
                """31bq NN / PP (B16 (c)): a crossing's penetration DEPTH, measured ALONG its section on the two faces' own meshes. From up to 16 points of the
                counted section edges, each face is walked away from the section both ways (in its own surface, re-anchored on its mesh, the step growing and
                halving at each end so the end is found exactly - no fixed steps, no 25 mm cap) while the walking point still projects onto the other face as a
                TRUE FOOT; each way's extent is its largest distance from the other face. A face reads the SMALLER of its two ways (a crossing's wrong side is
                its short side; at a convex corner the overshoot is the short side, the face's own extent the long one; a face whose two ways stay on one side of
                the other reads 0 - a touch, R5a), the depth the largest over the samples. A coincident overlap reads ~0; None when nothing was measured.
                31bq R7W (A8 - round 5's #17, the open list's item 2): each face is walked against the OTHER face AND THE SURFACE BEYOND IT (_rmesh, when the two
                faces' indices in the solid are given) and a pair reads the LARGER of its two faces - the smaller had let a crossing through a NARROW face pass: a
                face through a blend strip under 0.6 mm wide read at most half the strip's width and passed 0.30 (its deep arm ended at the strip's border).
                Returns (the depth, every walk took 0 steps, [face a's reading, face b's reading]).
                (NN's walk: fixed 0.1-25 mm steps read 0.49 as 0.25 and capped a 0.35 crossing at 0.22; it read convex 0.02-0.2 mm lips as 7.87 and a snapped
                projection as 12.5 - VERIFY_NN_2026-10-19.txt.)"""
                MA = _fmesh(fa__); MB = _fmesh(fb__)
                if MA is None or MB is None: return None, False, None
                _u = ia__ is not None and ib__ is not None
                RA = (_rmesh(ia__, ib__) if _u else None) or MA; RB = (_rmesh(ib__, ia__) if _u else None) or MB      
                _fbest = [None, None]
                
                # not taken
                _inc = [bool(_u and _RLOST.get(_rkey(ib__, ia__), 0)), bool(_u and _RLOST.get(_rkey(ia__, ib__), 0))]      
                if any(_inc): _si_inc["%d x %d" % (ia__, ib__)] = [_RLOST.get(_rkey(ib__, ia__), 0), _RLOST.get(_rkey(ia__, ib__), 0)]
                _tot = sum(e_.Length for e_ in eds__) or 1.0; _ns_all = [max(1, int(round(16 * e_.Length / _tot))) for e_ in eds__]
                while sum(_ns_all) > 16 and max(_ns_all) > 1: _ns_all = [max(1, n_ // 2) for n_ in _ns_all]
                _best = None; _steps = [0]
                for e_, _ns in zip(eds__, _ns_all):
                    for _t in np.linspace(e_.FirstParameter, e_.LastParameter, _ns + 2)[1:-1]:
                        try: _s0 = e_.valueAt(float(_t)); _te = e_.tangentAt(float(_t))
                        except Exception: continue
                        s0 = np.array([_s0.x, _s0.y, _s0.z]); te = np.array([_te.x, _te.y, _te.z]); te /= max(float(np.linalg.norm(te)), 1e-12)
                        m_ = []
                        for fw_, (MW, MR) in enumerate(((MA, RB), (MB, RA))):
                            q0, d0_, t0, ok0 = _foot(MW, s0)
                            dd = np.cross(MW["N"][t0], te); n_ = float(np.linalg.norm(dd))
                            if n_ < 1e-9: continue
                            dd /= n_; cap = max(1.0, MW["size"])
                            (ea_, sa_, na_), (eb_, sb_, nb_) = _walk(MW, MR, q0, dd, cap), _walk(MW, MR, q0, -dd, cap); _steps[0] += na_ + nb_
                            r_ = 0.0 if (sa_ != 0 and sa_ == sb_) else min(ea_, eb_)      
                            m_.append((fw_, r_)); _fbest[fw_] = r_ if _fbest[fw_] is None else max(_fbest[fw_], r_)
                        if not m_: continue
                        _dep = max([r__ for f__, r__ in m_ if not _inc[f__]] + [min(r__ for f__, r__ in m_)]); _best = _dep if _best is None else max(_best, _dep)
                return _best, (_steps[0] == 0 and _best is not None), _fbest      
            def _bf_txt(t_):
                """31bq R7W: a measured pair's two faces' readings, for the say line"""
                r__ = _si_faces.get("%d x %d" % (t_[0], t_[1]))
                if not r__ or None in r__: return ""
                return " - face %d %.2f / face %d %.2f, each against the other and the surface beyond it" % (t_[0], r__[0], t_[1], r__[1])
            with busy("self-intersection search over %d face pair(s)" % (len(_fs) * (len(_fs) - 1) // 2), 900):      
                for i_ in range(len(_fs)):
                    for j_ in range(i_ + 1, len(_fs)):
                        if not _fs[i_].BoundBox.intersect(_fs[j_].BoundBox): continue
                        _shared = [e_ for e_ in _fs[i_].Edges if e_.hashCode() in _eh[j_]]      
                        try:
                            if _fs[i_].distToShape(_fs[j_])[0] > 1e-3: continue
                            _sx = _fs[i_].section(_fs[j_]); _L = 0.0; _sxe = []
                            for e_ in _sx.Edges:
                                if _shared:
                                    _mid = e_.valueAt(0.5 * (e_.FirstParameter + e_.LastParameter))
                                    if min(Part.Vertex(_mid).distToShape(se_)[0] for se_ in _shared) < 0.02: continue
                                _L += e_.Length; _sxe.append(e_)
                        except Exception: _skipped_pairs += 1; continue      
                        if _L > 0.05:
                            try: _dep, _z0, _fr = _si_depth(_fs[i_], _fs[j_], _sxe or list(_sx.Edges), i_, j_)      
                            except Exception: _dep, _z0, _fr = None, False, None
                            if _fr is not None: _si_faces["%d x %d" % (i_, j_)] = [None if x__ is None else round(float(x__), 3) for x__ in _fr]
                            if _z0: _si_border.append([i_, j_])
                            _si.append([i_, j_, round(float(_L), 2), (round(float(_dep), 3) if _dep is not None else None)])      # UNMEASURED
            res["self_intersections"] = _si; res["si_unmeasured_pairs"] = _skipped_pairs; res["si_searched"] = True; res["si_border_touch"] = _si_border
            res["si_depth_by_face"] = _si_faces; res["si_depth_kernel"] = {"cut_back": _si_kcut[0], "calls": _si_kcut[1], "unmeshed_neighbours": _si_kcut[2]}; res["si_depth_incomplete"] = _si_inc      
            if _si_inc: say("   %d crossing pair(s) where a face's reference lost a neighbour with no mesh (the surface beyond it incomplete) - that face's reading is not taken as the larger, the smaller-face rule stands for it: %s (pair: [face a's lost, face b's lost]) (31bq R7W)" % (len(_si_inc), _si_inc))
            if _skipped_pairs: say("   %d face pair(s) with overlapping boxes could not be measured for a crossing (the kernel's distance or section raised) - unmeasured, not clear (31bq B16)" % _skipped_pairs)
            if _si:
                res["si_names"] = {str(k__): _face_name(k__) for t_ in _si[:12] for k__ in t_[:2]}
                say("THE SOLID SELF-INTERSECTS: %s - a face runs THROUGH its neighbour (a plate or a fill left its border's envelope, a blend's arc, a junction piece); the sew carries it: split that face with a wire or decide its lines there (skin-look's face numbers)" % ", ".join("faces %s x %s (%.1f mm along, %s%s)" % (_face_name(t_[0]), _face_name(t_[1]), t_[2], (("%.2f mm deep%s" % (t_[3], _bf_txt(t_))) if (len(t_) > 3 and t_[3] is not None) else "the depth UNMEASURED - NOT CLEARED where check(True) says SelfIntersect, noted where it does not (R7W A9)"), " - the faces MEET ALONG A BORDER, no overlap (every walk took 0 steps - 31bq R5a)" if [t_[0], t_[1]] in _si_border else (" - a COINCIDENT overlap, no penetration" if (len(t_) > 3 and t_[3] is not None and t_[3] < 0.05 and t_[2] > 0.3) else "")) for t_ in _si[:8]))
            elif "SelfIntersect" in str(res.get("check", "")): say("check(True) says SelfIntersect but no two faces cut each other along more than 0.05 mm (an edge or a vertex touch)")
            else: say("no two faces of the solid cut each other along more than 0.05 mm (every pair measured, neighbours included - 31bq B16)")
        except Exception as _exs: say("the self-intersection search failed: %s" % str(_exs)[:80])
    # FACE SANITY - every face of the solid read against
    
    FS_TOL = float(os.environ.get("FACE_SANITY_TOL", "0.05") or 0.05)
    _fs_bad = []; _fs_unm = []; _fs_mis = []; vol_mesh = None; vol_k = float(so.Volume)      # recorded
    with busy("FACE SANITY over %d faces" % len(so.Faces), 600):
        for k_, f_ in enumerate(so.Faces):
            try: a_k = float(f_.Area)
            except Exception: a_k = float("nan")
            c_k, m_k = _so_mesh(k_); j_k = _built_of(k_); b_k = (float(BUILT[j_k][1]) if j_k is not None else None)
            why_ = []
            if not np.isfinite(a_k) or a_k <= 0: why_.append("its kernel area reads %.4g mm2" % a_k)
            elif m_k is not None and abs(a_k - m_k) > FS_TOL * m_k + 0.05: _fs_mis.append((k_, a_k, m_k))      
            if _SO_SAME and b_k is not None and np.isfinite(a_k) and abs(a_k - b_k) > FS_TOL * b_k + 0.05: why_.append("%.4g mm2 against %.3f as built" % (a_k, b_k))
            if m_k is None: _fs_unm.append(k_)      # NOT TAKEN  recorded  recorded
            if why_: _fs_bad.append({"face": k_, "name": _face_name(k_), "area": (round(a_k, 4) if np.isfinite(a_k) else None), "mesh_area": (round(m_k, 4) if m_k is not None else None), "built_area": (round(b_k, 4) if b_k is not None else None), "why": "; ".join(why_), "rebuilt_by_sew": bool(_SO_SAME and _SH_IDX[k_] is None)})
        def _mesh_vol(d__):
            Vm_, Tm_ = so.copy().tessellate(d__); Vm_ = np.array([[q.x, q.y, q.z] for q in Vm_], float); Tm_ = np.array(Tm_, int).reshape(-1, 3)
            return abs(float(np.einsum("ij,ij->i", Vm_[Tm_[:, 0]], np.cross(Vm_[Tm_[:, 1]], Vm_[Tm_[:, 2]])).sum() / 6.0))
        try: vol_mesh = _mesh_vol(0.01)
        except Exception: vol_mesh = None
    _area_m = float(sum(m_ for m_ in (_so_mesh(k_)[1] for k_ in range(len(so.Faces))) if m_ is not None))
    _vtol = 0.75 * _area_m * 0.01 + 5.0      
    _vbad = bool(vol_mesh is not None and abs(abs(vol_k) - vol_mesh) > _vtol)
    _vsharp = None
    if os.environ.get("FILLET_LINES"):
        try: _vsharp = float(json.load(open(os.path.join(SK, "solid_c.json.sharp"), encoding="utf-8")).get("volume"))
        except Exception: _vsharp = None
    res["face_sanity"] = {"bad": _fs_bad[:20], "n_bad": len(_fs_bad), "unmeshed_not_taken": [int(x_) for x_ in _fs_unm], "mismatch_noted": [{"face": int(a_), "name": _face_name(a_), "area": round(float(b_), 4), "mesh_area": round(float(c_), 4)} for a_, b_, c_ in _fs_mis[:20]], "volume_kernel": round(vol_k, 2), "volume_mesh": (round(vol_mesh, 2) if vol_mesh is not None else None), "volume_bad": _vbad, "volume_tol": round(_vtol, 1), "volume_sharp_pass": _vsharp, "tol": FS_TOL}
    say("FACE SANITY (31bq R7W): %d of %d face(s) off their own mesh or their built record%s; the solid's kernel volume %.1f against its own mesh's at 0.01 mm %s%s%s" % (
        len(_fs_bad), len(so.Faces), ((" - " + "; ".join("face %s: %s" % (b_["name"], b_["why"]) for b_ in _fs_bad[:6])) if _fs_bad else "") + ((" - face(s) %s give NO triangle at 0.02 mm: their area NOT TAKEN (not judged)" % ", ".join(_face_name(x_) for x_ in _fs_unm[:6])) if _fs_unm else "") + ((" - face(s) %s: the kernel area off the face's own mesh's by over %g (kernel / mesh mm2; NOTED, not judged - 31bq R7Wo, the pictures decide)" % (", ".join("%s %.3f / %.3f" % (_face_name(a_), b_, c_) for a_, b_, c_ in _fs_mis[:6]), FS_TOL)) if _fs_mis else ""), vol_k, ("%.1f" % vol_mesh) if vol_mesh is not None else "UNMEASURED",
        (" - THEY DISAGREE beyond the mesh's own chord error (%.0f mm3): Part.Volume is no ruler on this piece" % _vtol) if _vbad else " (within the mesh's chord error, %.0f mm3)" % _vtol, (" (the sharp pass %.1f: %+.1f mm3 - the blends and the faces they re-span; said, not judged)" % (_vsharp, vol_k - _vsharp)) if _vsharp is not None else ""))
    so.exportBrep(os.path.join(SK, "piece_skin.brep"))
    pf_ = []
    for k_, f_ in enumerate(so.Faces):
        j_ = _built_of(k_)      
        r_ = BUILT[j_][2] if j_ is not None else {"patch": -1, "kind": "fillet" if nfil else "?"}
        try:      # recorded
            _tv = np.array([[q.x, q.y, q.z] for q in f_.tessellate(0.1)[0]]); _bb = [_tv[:, 0].min(), _tv[:, 0].max(), _tv[:, 1].min(), _tv[:, 1].max(), _tv[:, 2].min(), _tv[:, 2].max()]
        except Exception:
            _b = f_.BoundBox; _bb = [_b.XMin, _b.XMax, _b.YMin, _b.YMax, _b.ZMin, _b.ZMax]
        pf_.append({"face": k_, "patch": int(r_.get("patch", -1)), "rung": _rung(r_) if j_ is not None else ("fillet" if nfil else "?"), "area_mm2": round(float(f_.Area), 3), "mesh_area_mm2": (round(float(_so_mesh(k_)[1]), 3) if _so_mesh(k_)[1] is not None else None),
                    "sub": (r_.get("sub") if j_ is not None else None), "fillet_name": (r_.get("fillet_name") if j_ is not None else None),      
                    "bbox": [round(float(v), 3) for v in _bb]})
    
    if res.get("check") != "OK":
        badf = []
        with busy("check(True) on %d faces one by one" % len(so.Faces), 900):      
            for k_, f_ in enumerate(so.Faces):
                try:
                    f_.check(True)
                except Exception as ex_:
                    w_ = str(ex_)
                    
                    what_ = ("its border crosses itself" if "SelfIntersect" in w_ else "an edge is off its surface" if ("CurveOnSurface" in w_ or "SameParameter" in w_) else
                             ("a too-small edge (BOP): the body's own %.2f mm section edge - the wall's junk, not this build's (the caps are the body's faces verbatim, L114)" % min([e_.Length for e_ in f_.Edges] + [9.0]) if pf_[k_]["rung"] == "cap" else "a too-small edge (BOP): an edge %.2f mm long with its tolerance raised to its gap" % min([e_.Length for e_ in f_.Edges] + [9.0])) if "TooSmallEdge" in w_ else
                             ("not valid as built (no BOP error named; its edges' tolerance up to %.3f mm)" % max([e_.Tolerance for e_ in f_.Edges] + [0.0])) if not f_.isValid() else
                             (("BOP: " + "; ".join(sorted(set(l_.split("BOPAlgo")[-1].strip(" _:") for l_ in w_.splitlines() if "BOPAlgo" in l_)))[:80]) if "BOPAlgo" in w_ else
                              "not valid (the check raised: %s)" % (w_.strip().splitlines() or ["?"])[0][:60]))
                    badf.append({"face": k_, "patch": pf_[k_]["patch"], "rung": pf_[k_]["rung"], "what": what_, "check": w_[:300], "valid": bool(f_.isValid()), "sub": pf_[k_].get("sub"), "fillet_name": pf_[k_].get("fillet_name")})      
                    pf_[k_]["check"] = what_
        res["check_faces"] = badf
        res["si_self_faces"] = [b_["face"] for b_ in badf if "SelfIntersect" in str(b_.get("check", ""))]      
        if badf:
            say("check(True) FAILS on %d face(s): %s - skin-look's frames carry these numbers; their lines / points are the fix"
                % (len(badf), ", ".join("face %d (patch %d%s, %s%s: %s)" % (b_["face"], b_["patch"], b_.get("sub") or "", b_["rung"], (" of line %s" % b_["fillet_name"]) if b_.get("fillet_name") else "", b_["what"]) for b_ in badf[:12])))
        else:
            say("check(True) fails on the solid as a whole - no single face fails its own check")
    json.dump({"piece_md5": K.md5(os.path.join(SK, "piece_skin.brep")), "faces": pf_}, open(os.path.join(SK, "piece_faces.json"), "w"), indent=0)
    say("piece faces by rung: %s" % {k: sum(1 for x in pf_ if x["rung"] == k) for k in ("cap", "orig", "flat", "nurbs", "span", "plate", "fit", "fillet")})
if FRAME and sh.isClosed():
    
    pl_ = [f for f in so.Faces if isinstance(f.Surface, Part.Plane)]
    dc = []
    for b_, B_ in enumerate(BFc):
        dd_ = min((f.CenterOfMass - B_.CenterOfMass).Length + abs(f.Area - B_.Area) for f in pl_); dc.append(dd_)
    de = []
    so_e = so.Edges
    for k, (q_, b_, i_) in BODY_E.items():
        e0 = BFc[b_].Edges[i_]; P0 = [e0.valueAt(e0.FirstParameter + (e0.LastParameter - e0.FirstParameter) * t / 10.0) for t in range(11)]
        tolF = max(1e-6, FRAME_TOL); cand = [e for e in so_e if abs(e.Length - e0.Length) < tolF and (e.CenterOfMass - e0.CenterOfMass).Length < tolF]   
        de.append(min([max(e.distToShape(Part.Vertex(x))[0] for x in P0) for e in cand], default=99.0))
    res["frame_caps_max_dev"] = round(max(dc), 9); res["frame_edges_max_dev"] = round(max(de), 9); res["frame_edges_missing"] = sum(1 for x in de if x > FRAME_TOL); res["frame_tol"] = FRAME_TOL
    if SHOW_NUMBERS:
        say("FRAME CHECK: the %d caps against the body's section faces - worst centre+area difference %.2e; the %d body edges the skin faces own - worst %.2e mm, %d not within FRAME_TOL %.3g mm"
            % (len(BFc), max(dc), len(de), max(de), res["frame_edges_missing"], FRAME_TOL))
    else:
        say("FRAME CHECK: the %d caps %s the body's own section faces; %d of the %d body edges the skin faces own are the body's (within FRAME_TOL)"
            % (len(BFc), "ARE" if max(dc) <= 1e-6 else "are NOT", len(de) - res["frame_edges_missing"], len(de)))
try:
    _ct = Part.Shape(); _ct.importBrep(os.path.join(RUN, "content.brep")); res["content_faces"] = len(_ct.Faces)
except Exception: pass
try: res["piece_md5"] = K.md5(os.path.join(SK, "piece_skin.brep")) if (sh.isClosed() and os.path.isfile(os.path.join(SK, "piece_skin.brep"))) else None      
except Exception: res["piece_md5"] = None
res["wire_clean"] = globals().get("WC_RECORD")      
json.dump(res, open(os.path.join(SK, "solid_c.json"), "w"), indent=1)

if not res.get("closed"): K._fail("FAIL: the skin's shell did not close - %d free edge(s) (skin\\free_c.brep; `kit rebuild skin-look` draws them red)" % res.get("free_edges", -1))
if not res.get("valid"):
    _inv_ = [b_ for b_ in (res.get("check_faces") or []) if b_.get("valid") is False]      
    K._fail("FAIL: the closed shell did not make a valid solid%s" % ((" - the face(s) not valid themselves: %s" % ", ".join("face %d (patch %d%s, %s%s)" % (b_["face"], b_["patch"], b_.get("sub") or "", b_["rung"], (" of line %s" % b_["fillet_name"]) if b_.get("fillet_name") else "") for b_ in _inv_[:12])) if _inv_ else " - no face of it is invalid by itself (check(True) above names what fails)"))
if FRAME and (res.get("frame_caps_max_dev", 1.0) > 1e-6 or res.get("frame_edges_missing", 1) > 0):
    K._fail("FAIL: THE FRAME CHECK - the piece's caps are not the body's own section faces (worst %.2e) or %d body edge(s) a skin face owns are not in the piece within FRAME_TOL %.3g mm: the reinsert faces come first and exact (the client 2026-10-06)" % (res.get("frame_caps_max_dev", -1), res.get("frame_edges_missing", -1), FRAME_TOL))
_fsr = res.get("face_sanity") or {}
if _fsr.get("n_bad") or _fsr.get("volume_bad"):
    K._fail("FAIL: FACE SANITY - %s%s: the kernel's area / volume integrals are no ruler on this piece (a face the shell's sewing rebuilt, or an edge off the faces that hold it) - skin\\solid_c.json face_sanity; skin-look draws the faces (31bq R7W, A5)" % (
        "; ".join("face %s: %s%s" % (b_["name"], b_["why"], " (rebuilt by the shell's sewing)" if b_.get("rebuilt_by_sew") else "") for b_ in (_fsr.get("bad") or [])[:6]) or "every face reads right",
        (" - the solid's kernel volume %.1f against its own mesh's %.1f" % (_fsr.get("volume_kernel"), _fsr.get("volume_mesh"))) if _fsr.get("volume_bad") else ""))
_FSUF = ""      
if os.environ.get("FILLET_LINES") and FILLETS:
    try:
        _drp_ = set(int(x) for x in os.environ.get("FILLET_DROPPED", "").split(",") if x.strip().lstrip("-").isdigit())
        _fr_ = list(res.get("fillets") or []); _no_ = [r_ for r_ in _fr_ if not r_.get("ok")]
        def _why_sharp(r_):
            try: k_ = int(r_.get("line"))
            except (TypeError, ValueError): k_ = None
            if k_ in _drp_: return "left out by the retry"
            if k_ in FIL_NOT_MADE: return FIL_NOT_MADE[k_][:120] if "sharp_ok" in FIL_NOT_MADE[k_] else ("not made by lines: %s" % FIL_NOT_MADE[k_][:120])      
            return str(r_.get("why", "?"))[:80]
        if _no_: _FSUF = " - fillets: %d of %d decided made, %d standing SHARP: %s (31bq R7W)" % (len(_fr_) - len(_no_), len(_fr_), len(_no_), "; ".join("line %s%s (%s)" % (r_.get("line"), (" leg %s" % r_["leg"]) if r_.get("leg") is not None else "", _why_sharp(r_)) for r_ in _no_[:8]) + (" and %d more" % (len(_no_) - 8) if len(_no_) > 8 else ""))
    except Exception as _exfs: _FSUF = " - fillets: the made / sharp count could not be read (%s)" % str(_exfs)[:60]
_chk = "check(True) OK" if res.get("check") == "OK" else ("check(True) FAILS on %d face(s): %s%s" % (len(res.get("check_faces", [])), ", ".join("%d (%s)" % (b_["face"], b_["rung"]) for b_ in res.get("check_faces", [])[:12]), (" and %d more (skin\\solid_c.json check_faces names them all)" % (len(res.get("check_faces", [])) - 12)) if len(res.get("check_faces", [])) > 12 else "")
                                                       if res.get("check_faces") else "check(True) FAILS on the solid as a whole")   
if res.get("self_intersections"):      # SELF-INTERSECTS
    SI_TOUCH_MM = 0.05
    _sxT_ = [x_ for x_ in res["self_intersections"] if (len(x_) > 3 and x_[3] is not None and float(x_[3]) <= SI_TOUCH_MM) or [x_[0], x_[1]] in (res.get("si_border_touch") or [])]
    _sxX_ = [x_ for x_ in res["self_intersections"] if x_ not in _sxT_]
    if _sxX_: _chk += "; THE SOLID SELF-INTERSECTS: %s" % ", ".join("faces %d x %d (%s)" % (x_[0], x_[1], ("%.2f mm deep" % x_[3]) if (len(x_) > 3 and x_[3] is not None) else ("%.2f mm along, the depth UNMEASURED" % x_[2])) for x_ in _sxX_[:6])
    if _sxT_: _chk += "; %d face pair(s) TOUCH (%.2f mm deep at most - a border touch or a coincident overlap, no crossing: skin\\solid_c.json self_intersections)" % (len(_sxT_), max([float(x_[3]) for x_ in _sxT_ if len(x_) > 3 and x_[3] is not None] + [0.0]))

# UNMEASURED
# NOT CLEARED
# noted, not judged

_si_all = list(res.get("self_intersections") or []); _si_meas = lambda x_: len(x_) > 3 and x_[3] is not None
_si_big = [x_ for x_ in _si_all if _si_meas(x_) and not (float(x_[3]) <= 0.30)]      
_si_unm = [x_ for x_ in _si_all if not _si_meas(x_)]; _si_sx = bool(res.get("check_selfintersect") or "SelfIntersect" in str(res.get("check", ""))); _si_why = []
if _si_big: _si_why.append("beyond the 0.30 mm print tolerance: %s - a face runs through its neighbour (a plate or a fill left its border's envelope, or a blend's arc): split that face with a wire where they cross, or a smaller R on the blend beside it (31bq B16)" % ", ".join("faces %s x %s %.2f mm deep (%.2f along)" % ((res.get("si_names") or {}).get(str(x_[0]), x_[0]), (res.get("si_names") or {}).get(str(x_[1]), x_[1]), float(x_[3]), float(x_[2])) for x_ in _si_big[:6]))
if _si_unm and _si_sx: _si_why.append("NOT CLEARED - %d crossing(s) of UNMEASURED depth and the build's own check(True) says SelfIntersect: nothing measured them under the 0.30 mm print tolerance (a short crossing can be deep): %s - the reinsert's BOP gate and kit check refuse the same record; build again (a face whose own mesh could not be made, or a walk that raised, leaves its crossing unmeasured) (31bq R6a / R7a / R7W A9)" % (len(_si_unm), ", ".join("faces %d x %d (%.2f mm along)" % (x_[0], x_[1], float(x_[2])) for x_ in _si_unm[:6])))
elif _si_unm: say("SELF-INTERSECTION NOTE: %d crossing(s) whose depth is UNMEASURED - the build's check(True) does not say SelfIntersect, so they are noted, not judged (as kit check notes them): %s (31bq R7W A9)" % (len(_si_unm), ", ".join("faces %d x %d (%.2f mm along)" % (x_[0], x_[1], float(x_[2])) for x_ in _si_unm[:6])))
if _si_why: K._fail("FAIL: THE SOLID SELF-INTERSECTS %s" % " - AND ".join(_si_why))
_PASS_LINE = ("SKIN BUILD PASS: %d faces in the piece (the edit region's content had %s), a valid solid, %s; %s" % (res["faces"], res.get("content_faces", "?"), "the frame exact" if FRAME else "NO FRAME (caps not the body's)", _chk)) + globals().get("_FSUF", ""); print(_PASS_LINE, flush=True)      
# 31ax: a fillet the kernel failed is made by DRAWN LINES

if "FIL_RERUN" in dir() and FIL_RERUN:
    import subprocess, shutil as _sh
    _dups_p = _dup_entries(FILLETS)
    if _dups_p:      
        print("FILLET BY LINES: the lines pass is REFUSED before any sweep - skin\\fillets.json decides a crease in two entries: %s - one blend per crease (line, leg): decide each once and run skin-wires again (it refuses a line decided twice when it writes the file); the piece above stands (31bq R7W, M4)" % _dup_text(_dups_p), flush=True)
        print(_PASS_LINE + "   (the sharp piece stands - 31bq B01)", flush=True); print("DONE", flush=True); raise SystemExit(0)
    _keep = ("piece_skin.brep", "piece_faces.json", "solid_c.json", "build_c.json", "faces_c.brep", "shell_c.brep"); _keep_ = _keep
    for _f in _keep:
        try: _sh.copy2(os.path.join(SK, _f), os.path.join(SK, _f + ".sharp"))
        except OSError: pass
    say("FILLET by the kernel failed on line(s) %s - the piece above is kept aside; built AGAIN with those fillets drawn by lines (two offset lines a radius from the crease, the strip between them one blend face through the arc's sagitta):" % FIL_RERUN)
    def _lines_child(lines_):
        """31bq B01 / B03: the lines pass as a child with THESE lines; its output re-said by the parent (a "FAIL:" of the lines pass becomes "LINES PASS - FAIL:"
        so the runner - kit.py _judge_output reads any line starting "FAIL:" as the step's refusal, rc 1 - does not refuse a build whose sharp piece stands); the
        child's lines are kept for the retry's reading. 31bq R7W (M9, A3 finding 9): a child that exits 0 WITHOUT its own SKIN BUILD PASS line gave no verdict - rc 1, no
        lines pass (the .sharp copies had been deleted and the parent's PASS line had described a piece no longer on disk)"""
        env_ = dict(os.environ); env_["FILLET_LINES"] = ",".join(str(x) for x in lines_); env_["FILLET_RERUN"] = "0"
        env_["FILLET_DROPPED"] = ",".join(str(x) for x in FIL_RERUN if x not in set(lines_))      
        sys.stdout.flush(); kept_ = []
        _pr = subprocess.Popen([sys.executable, os.path.abspath(__file__)], env=env_, cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace", bufsize=1)
        for _ln in _pr.stdout:
            _ln = _ln.rstrip("\n"); kept_.append(_ln)
            if _ln.startswith("FAIL:"): _ln = "LINES PASS - FAIL:" + _ln[5:]
            elif re.match(r"^\s*\d+s\s+FAIL:", _ln): _ln = re.sub(r"FAIL:", "LINES PASS - FAIL:", _ln, count=1)
            elif _ln.startswith("Traceback (most recent call last)"): _ln = "LINES PASS - the child's traceback follows (the parent stands):"      
            elif _ln.startswith("Exception while processing file"): _ln = "LINES PASS - the child's exception: " + _ln.split(":", 1)[-1].strip()
            print(_ln, flush=True)
        rc__ = _pr.wait()
        if rc__ == 0 and any(l__.startswith("Traceback (most recent call last)") or l__.startswith("Exception while processing file") for l__ in kept_): rc__ = 1
        if rc__ == 0 and not any(l__.startswith("SKIN BUILD PASS") for l__ in kept_):      
            rc__ = 1; kept_.append("(no verdict: the lines child exited 0 without its SKIN BUILD PASS line - 31bq R7W)"); print("LINES PASS - the child exited 0 WITHOUT its SKIN BUILD PASS line: no verdict, no lines pass (31bq R7W)", flush=True)
        return rc__, kept_
    _BLAME_NOTE = []      
    def _blame(lines_, out_):
        """the members the child's own record blames for an open shell, in two sets: DIRECT (a member not made, not re-swept, a split of its that failed a face's span)
        and the FREE EDGES' chains (a looser sign: a free edge beside a sound blend names it too - 31bq B03 (2): the first form dropped a sound line for that).
        31bq R7W (M9, A3 finding 4): a chain's COMMON-FACE strip whose split failed blames the member(s) whose strip END lies at the split's failing end (the child's
        "strip ends" line), the whole chain only when no member's end matches - said; (M1): a blend face's own SPAN FAILED (a piece F*, "fillet of line N") blames its line"""
        direct_, free_ = set(), set(); chains_, cmem_, cend_ = {}, {}, {}
        for _ln in out_:
            for _m in re.finditer(r"free edge [\d.]+ mm on chain (\d+)", _ln): free_.add(int(_m.group(1)))
            
            for _m in re.finditer(r"FILLET BY LINES on line (\d+)[^:]*: not made", _ln): direct_.add(int(_m.group(1)))
            for _m in re.finditer(r"member (\d+)(?: leg \d+)? could not be swept again", _ln): direct_.add(int(_m.group(1)))
            if "SPAN FAILED" in _ln:
                for _m in re.finditer(r"piece F\w*\s+\(fillet of line (\d+)", _ln): direct_.add(int(_m.group(1)))      
                for _m in _KIT_SPLIT_RE.finditer(_ln):
                    if _m.group("m"):
                        for _n in re.findall(r"(?:^|\+)\s*(\d+)", _m.group("m")): direct_.add(int(_n))
                    elif _m.group("c"):
                        _tl = _ln[_m.end() - 1:]; _pp = re.match(r"\[\s*([-\d.e]+),\s*([-\d.e]+),\s*([-\d.e]+)\]\s*to\s*\[\s*([-\d.e]+),\s*([-\d.e]+),\s*([-\d.e]+)\]", _tl)
                        _dd = re.search(r"its ends \(([\d.]+) / ([\d.]+) mm", _tl[:400])
                        _fe = []
                        if _pp:
                            _P = [np.array([float(_pp.group(1)), float(_pp.group(2)), float(_pp.group(3))]), np.array([float(_pp.group(4)), float(_pp.group(5)), float(_pp.group(6))])]
                            _fe = [P__ for P__, d__ in zip(_P, ([float(_dd.group(1)), float(_dd.group(2))] if _dd else [1.0, 1.0])) if d__ > 0.05] or _P
                        chains_.setdefault(int(_m.group("c")), []).extend(_fe)
                    elif _m.group("l"): direct_.add(int(_m.group("l")))
            _mc = re.search(r"FILLET CHAIN (\d+) \(31bp\): \d+ member\(s\) round face \d+ - (\[[^\]]*\])", _ln)
            if _mc: cmem_[int(_mc.group(1))] = [int(x_) for x_ in re.findall(r"'(\d+)", _mc.group(2))]
            _me = re.search(r"fillet chain (\d+): the members' strip ends on face \d+ \(31bq R7W\): (.*)$", _ln)
            if _me: cend_[int(_me.group(1))] = [(int(_x.group(1)), np.array([float(v_) for v_ in _x.group(2).split(",")]), np.array([float(v_) for v_ in _x.group(3).split(",")])) for _x in re.finditer(r"(\d+)(?: leg \d+)? \[([^\]]*)\] \[([^\]]*)\]", _me.group(2))]
        for c_, fe_ in chains_.items():
            hit_ = sorted(set(k_ for k_, a_, b_ in cend_.get(c_, []) for P__ in fe_ if min(float(np.linalg.norm(a_ - P__)), float(np.linalg.norm(b_ - P__))) <= 0.05))
            if hit_: direct_.update(hit_); _BLAME_NOTE.append("chain %d's common-face strip: the member(s) %s whose strip end lies at the split's failing end" % (c_, hit_))
            else: direct_.update(cmem_.get(c_, [])); _BLAME_NOTE.append("chain %d's common-face strip: no member's strip end lies at the split's failing end - the whole chain" % c_)
        L_ = set(lines_)
        return sorted(b_ for b_ in direct_ if b_ in L_), sorted(b_ for b_ in free_ if b_ in L_ and b_ not in direct_)
    rc_, out_ = _lines_child(FIL_RERUN)
    if rc_ != 0:
        try:      
            _sf2 = [l__ for l__ in out_ if "SPAN FAILED" in l__]; _nm2 = [l__ for l__ in out_ if re.search(r"FILLET BY LINES on line \d+[^:]*: (not made|NOT made)", l__)]
            _dir2, _free2 = _blame(FIL_RERUN, out_)
            print("LINES PASS - FAILED, FIRST THE THREE THINGS (31br I2):", flush=True)
            print("  (a) faces that failed to span: %s" % ("; ".join(re.sub(r"^\s*\d+s\s+", "", l__)[:260] for l__ in _sf2[:4]) or ("none - the shell opened elsewhere (the free edges' chains: %s)" % _free2)), flush=True)
            print("  (b) members not made%s: %s" % ((" - the retry drops %s" % _dir2) if _dir2 else "", "; ".join(re.sub(r"^\s*\d+s\s+", "", l__)[:200] for l__ in _nm2[:4]) or "none"), flush=True)
            print("  (c) the one change: %s" % ("split the failed piece where its surface turns, or give the turning part to the neighbour it faces like (the SPAN FAILED line names the piece and its added lines)" if _sf2 else
                                               ("lower R or make room at the members named (their room lines say where), or accept them sharp (\"sharp_ok\": true)" if _nm2 else "look at the free edges (skin-look draws them red) - the retry below says what it drops")), flush=True)
        except Exception: pass
        
        def _nfree(out__):
            """31bq R7W (M9, A3 finding 3): the child's OWN count - its FAIL line ('did not close - N free edge(s)'), else its shell line, else the sameParameter line (that one
            is printed only with SAMEPARAM=1 and when sameParameter does not raise: with SAMEPARAM=0 the 'no better' stop never fired and every message read '?')"""
            _n = _ns = _nsp = None
            for _ln in out__:
                _m = re.search(r"shell did not close - (\d+) free edge", _ln)
                if _m: _n = int(_m.group(1))
                _m = re.search(r"shell: \d+ faces, closed \w+, free edges (\d+)", _ln)
                if _m: _ns = int(_m.group(1))
                _m = re.search(r"free edges after (\d+)", _ln)
                if _m: _nsp = int(_m.group(1))
            return _n if _n is not None else (_ns if _ns is not None else _nsp)
        def _class(out__, rc__=None):
            for _ln in out__:      
                if "FAIL: THE SOLID SELF-INTERSECTS" in _ln: return "closed the shell but the solid SELF-INTERSECTS (the line above names the faces)"
                if "FAIL: the closed shell did not make a valid solid" in _ln: return "closed the shell but the solid is NOT VALID (the line above names its faces not valid themselves) - 31bq R5b (C5 NEW #6)"
                if ("FAIL: THE FRAME" in _ln) or ("FRAME CHECK" in _ln and "FAIL" in _ln): return "closed the shell but failed THE FRAME CHECK (the line above)"
                if "FAIL: FACE SANITY" in _ln: return "closed the shell but FAILED FACE SANITY (a face whose kernel area / volume integrals are no ruler - the line above names it and its blend line; 31bq R7W A5)"
                if "FAIL: THE LINES PASS IS REFUSED before any sweep" in _ln: return "was REFUSED before any sweep - the design decides a crease twice (the line above; 31bq R7W M4)"
                if _ln.startswith("Traceback (most recent call last)") or _ln.startswith("Exception while processing file"): return "CRASHED (the child's exception above - a kit defect, not a blend's)"
            if any(l_.startswith("(no verdict:") for l_ in out__): return "gave NO VERDICT - the child exited 0 without its SKIN BUILD PASS line (a kit defect, not a blend's; 31bq R7W)"
            if rc__ not in (None, 0) and not any(l_.startswith("FAIL:") for l_ in out__):      
                return "CRASHED (exit code %s with no FAIL line - a crash of the child, a kit defect, not a blend's)" % rc__
            return None
        def _class_lines(out__, lines_):
            """31bq R7W (M1, A3 findings 1 / 2 / 6): the blend lines the class's OWN failure line names - the crossing's (FAIL: THE SOLID SELF-INTERSECTS ...: 'faces a (patch ..,
            fillet of line N) x ...') or the invalid solid's faces (FAIL: ... 'the face(s) not valid themselves: ... fillet of line N') - never another cause's (the KK clause
            had let a crossing through to ANY direct cause: a member not made, and the retry said 'the blend(s) the solid's crossing names' for a line it did not name)"""
            got_ = set()
            for _ln in out__:
                if _ln.startswith("FAIL: THE SOLID SELF-INTERSECTS") or _ln.startswith("FAIL: the closed shell did not make a valid solid") or _ln.startswith("FAIL: FACE SANITY"):      
                    for _m in re.finditer(r"fillet of line (\d+)", _ln): got_.add(int(_m.group(1)))
            return sorted(x_ for x_ in got_ if x_ in set(lines_))
        _dropped = []; _out_cur = out_; _best = (_nfree(out_) if _class(out_, rc_) is None else None); _keep_lines = list(FIL_RERUN)
        for _stage in range(3):      
            if rc_ == 0: break
            _pre = "the pass" if not _dropped else ("the retry without %s" % _dropped)
            _cl = _class(_out_cur, rc_); del _BLAME_NOTE[:]
            if _cl:
                _cls_own = ("SELF-INTERSECTS" in _cl or "NOT VALID" in _cl or "FACE SANITY" in _cl)
                _set = [x for x in (_class_lines(_out_cur, _keep_lines) if _cls_own else []) if x not in _dropped]
                if not _set:
                    print("FILLET BY LINES: %s %s - %s: no retry by blame; the sharp piece stands (31bq B03 (4) / R7W)" % (_pre, _cl, "its failure line names no blend of this pass" if _cls_own else "dropping members cannot mend that"), flush=True); break
                _what = _cl.split(" (")[0]; _why = "the blend(s) named by %s" % ("the solid's crossing" if "SELF-INTERSECTS" in _cl else ("the FACE SANITY failure" if "FACE SANITY" in _cl else "the invalid solid's own invalid faces"))
            else:
                _direct, _free = _blame(_keep_lines, _out_cur)
                _set = [x for x in (_direct or _free) if x not in _dropped]; _what = "left the shell open"
                _why = ("the members not made, not re-swept, or whose split failed a face" if _direct else "the chains the free edges lie on") + (("; " + "; ".join(_BLAME_NOTE)) if _BLAME_NOTE else "")
                if not _set:
                    _chs = sorted(set(int(_m.group(1)) for _ln in _out_cur for _m in re.finditer(r"free edge [\d.]+ mm on chain (\d+)", _ln)))
                    _nc = _nfree(_out_cur)
                    print("FILLET BY LINES: the shell is still open (%s free edge(s)) on chain(s) %s - none is a fillet line of this pass: not a blend's failure to drop (a junction's end form, a split, a face - the free-edge lines above name the place); no further retry" % ("?" if _nc is None else _nc, _chs), flush=True); break
            _drop2 = sorted(set(_dropped) | set(_set))
            if len(_drop2) >= len(FIL_RERUN):
                print("FILLET BY LINES: %s %s - the record blames EVERY line of the pass (%s): no retry; the sharp piece stands (31bq R7W)" % (_pre, _what, _drop2), flush=True); break
            _dropped = _drop2; _keep_lines = [x for x in FIL_RERUN if x not in _dropped]
            print("FILLET BY LINES: %s %s - RETRIED WITHOUT line(s) %s (%s); the %d other line(s) %s are built again (31bq B03)" % (_pre, _what, _dropped, _why, len(_keep_lines), _keep_lines), flush=True)
            for _f in _keep_:
                try: _sh.copy2(os.path.join(SK, _f + ".sharp"), os.path.join(SK, _f))
                except OSError: pass
            _cl_prev = _cl
            rc_, _out_cur = _lines_child(_keep_lines); _n2 = _nfree(_out_cur)
            if rc_ == 0: print("FILLET BY LINES: the retry PASSED - line(s) %s stand sharp (their failure above is theirs to fix: the room, the sense, a split, the crossing); the other blends are made (the SKIN BUILD PASS line above names them)" % _dropped, flush=True); break
            if _cl_prev is not None and _class(_out_cur, rc_) is None and _n2 is not None: _best = _n2      # no better than the 0 before
            if _cl_prev is None and _class(_out_cur, rc_) is None:      
                print("FILLET BY LINES: the retry without %s did not close the shell either (%s free edge(s)%s)" % (_dropped, "?" if _n2 is None else _n2,
                      "" if (_best is None or _n2 is None) else (" - fewer than the %d before" % _best if _n2 < _best else " - no better than the %d before: no further retry" % _best)), flush=True)
                if _best is not None and _n2 is not None and _n2 >= _best: break
                if _n2 is not None: _best = _n2
    if rc_ != 0:
        for _f in _keep:
            try: os.replace(os.path.join(SK, _f + ".sharp"), os.path.join(SK, _f))
            except OSError: pass
        print("FILLET BY LINES FAILED on line(s) %s (the pass above) - the piece WITHOUT the fillet stands (its edge sharp): the first SKIN BUILD PASS line is the result; decide a smaller radius, a different line, or no fillet" % FIL_RERUN, flush=True)
        try: print(_PASS_LINE + "   (the sharp piece stands - 31bq B01)", flush=True)      
        except NameError: pass
        print("DONE", flush=True); raise SystemExit(0)
    for _f in _keep:
        try: os.remove(os.path.join(SK, _f + ".sharp"))
        except OSError: pass
    raise SystemExit(0)
print("DONE", flush=True)

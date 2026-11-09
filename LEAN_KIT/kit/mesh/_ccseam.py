# MESH_JOB
# MESH_JOB
# recorded
import numpy as np
from scipy.spatial import cKDTree


def _weld(V, T, tol):
    key = np.round(np.asarray(V, float) / max(tol, 1e-12)).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inv = np.asarray(inv).reshape(-1)
    order = np.argsort(first)
    pos = np.empty(len(first), int); pos[order] = np.arange(len(first))
    inv = pos[inv]
    Vw = np.asarray(V, float)[first][order]
    Tw = inv[np.asarray(T, int)]
    Tw = Tw[(Tw[:, 0] != Tw[:, 1]) & (Tw[:, 1] != Tw[:, 2]) & (Tw[:, 0] != Tw[:, 2])]
    return Vw, Tw


def _edges(T):
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    s = np.sort(e, 1)
    u, c = np.unique(s, axis=0, return_counts=True)
    return u, c


def health(V, T):
    u, c = _edges(T)
    return int((c == 1).sum()), int((c > 2).sum())


def _loops(T):
    """boundary edges -> loops, each an ORDERED vertex list (vertices of degree 2 on the rim)"""
    u, c = _edges(T)
    rim = u[c == 1]
    adj = {}
    for a, b in rim:
        adj.setdefault(int(a), []).append(int(b)); adj.setdefault(int(b), []).append(int(a))
    seen, loops, bad = set(), [], 0
    for s in list(adj):
        if s in seen:
            continue
        if len(adj[s]) != 2:
            seen.add(s); bad += 1
            continue
        loop, prev, cur = [s], None, s
        seen.add(s)
        while True:
            nx = [v for v in adj[cur] if v != prev]
            if not nx:
                break
            nxt = nx[0] if len(adj[cur]) == 2 else None
            if nxt is None or nxt == s:
                break
            if nxt in seen:
                break
            loop.append(nxt); seen.add(nxt); prev, cur = cur, nxt
        loops.append(loop)
    return loops, rim, bad


def _insert(V, T, loop, pts, tol):
    """Project each of pts onto the closed polyline `loop` (vertex indices into V) and insert it, splitting the
    rim edge's triangle into a fan. Returns V, T, partner (vertex index per point, -1 if beyond tol), dist."""
    V = np.asarray(V, float)
    L = np.asarray(loop, int)
    A = V[L]; B = V[np.roll(L, -1)]
    AB = B - A
    L2 = np.maximum((AB * AB).sum(1), 1e-30)
    tri_of = {}
    for ti, t in enumerate(T):
        for j in range(3):
            a, b = int(t[j]), int(t[(j + 1) % 3])
            tri_of[(min(a, b), max(a, b))] = ti
    Ln = np.roll(L, -1)
    real = np.array([(min(int(a), int(b)), max(int(a), int(b))) in tri_of for a, b in zip(L, Ln)])
    L2 = np.where(real, L2, 1e-30)
    mid = np.where(real[:, None], 0.5 * (A + B), 1e9)
    k = min(12, len(L))
    _, cand = cKDTree(mid).query(pts, k=k)
    cand = np.asarray(cand).reshape(len(pts), -1)
    best_e = np.zeros(len(pts), int); best_w = np.zeros(len(pts)); best_d = np.full(len(pts), np.inf)
    for col in range(cand.shape[1]):
        e = cand[:, col]
        w = np.clip(((pts - A[e]) * AB[e]).sum(1) / L2[e], 0.0, 1.0)
        q = A[e] + AB[e] * w[:, None]
        d = np.linalg.norm(pts - q, axis=1)
        d[~real[e]] = np.inf
        better = d < best_d
        best_e[better] = e[better]; best_w[better] = w[better]; best_d[better] = d[better]
    partner = -np.ones(len(pts), int)
    newV = []
    nV0 = len(V)
    groups = {}
    for i in range(len(pts)):
        if best_d[i] > tol:
            continue
        e = int(best_e[i]); w = float(best_w[i])
        a, b = int(L[e]), int(L[(e + 1) % len(L)])
        ln = np.sqrt(L2[e])
        if w * ln < 1e-6:
            partner[i] = a
        elif (1 - w) * ln < 1e-6:
            partner[i] = b
        else:
            groups.setdefault(e, []).append((w, i))
    T = [list(map(int, t)) for t in T]
    for e, lst in groups.items():
        a, b = int(L[e]), int(L[(e + 1) % len(L)])
        ti = tri_of.get((min(a, b), max(a, b)))
        if ti is None:
            continue
        t = T[ti]
        j = [q for q in range(3) if {t[q], t[(q + 1) % 3]} == {a, b}]
        if not j:
            continue
        j = j[0]
        x, y, c = t[j], t[(j + 1) % 3], t[(j + 2) % 3]
        lst.sort()
        if x != a:
            lst = [(1 - w, i) for w, i in lst][::-1]
        chain = [x]
        P0, P1 = V[x], V[y]
        lastw = -1.0
        for w, i in lst:
            if w - lastw < 1e-9 and len(chain) > 1:
                partner[i] = chain[-1]
                continue
            idx = nV0 + len(newV)
            newV.append(P0 + (P1 - P0) * w)
            chain.append(idx); partner[i] = idx; lastw = w
        chain.append(y)
        T[ti] = [chain[0], chain[1], c]
        for q in range(1, len(chain) - 1):
            T.append([chain[q], chain[q + 1], c])
            for u_, v_ in ((chain[q], chain[q + 1]), (chain[q + 1], c), (c, chain[q])):
                tri_of[(min(u_, v_), max(u_, v_))] = len(T) - 1
    if newV:
        V = np.vstack([V, np.asarray(newV, float)])
    return V, np.asarray(T, int), partner, best_d


def _poly(V, loop):
    P = V[np.asarray(loop, int)]
    Q = np.roll(P, -1, 0)
    seg = np.linalg.norm(Q - P, axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    return P, Q, seg, cum


def _project_param(P, Q, seg, cum, pts, k=12):
    """nearest point on a closed polyline -> (arc parameter, distance)"""
    AB = Q - P; L2 = np.maximum(seg ** 2, 1e-30)
    mid = 0.5 * (P + Q)
    _, cand = cKDTree(mid).query(pts, k=min(k, len(P)))
    cand = np.asarray(cand).reshape(len(pts), -1)
    bs = np.zeros(len(pts)); bd = np.full(len(pts), np.inf)
    for col in range(cand.shape[1]):
        e = cand[:, col]
        w = np.clip(((pts - P[e]) * AB[e]).sum(1) / L2[e], 0.0, 1.0)
        d = np.linalg.norm(pts - (P[e] + AB[e] * w[:, None]), axis=1)
        b = d < bd
        bd[b] = d[b]; bs[b] = cum[e][b] + w[b] * seg[e][b]
    return bs, bd


def _at_param(P, Q, seg, cum, sp):
    per = cum[-1]
    sp = np.mod(sp, per)
    e = np.clip(np.searchsorted(cum, sp, side="right") - 1, 0, len(P) - 1)
    w = np.where(seg[e] > 0, (sp - cum[e]) / np.maximum(seg[e], 1e-30), 0.0)
    w = np.clip(w, 0.0, 1.0)
    return e, w, P[e] + (Q[e] - P[e]) * w[:, None]


def _split_edges(V, T, loop, jobs):
    """jobs: list of (edge index in loop, w, job id). Fan-split each rim edge at all its points, in order.
    Returns V, T, partner dict job id -> vertex index."""
    V = np.asarray(V, float)
    L = np.asarray(loop, int)
    tri_of = {}
    for ti, t in enumerate(T):
        for j in range(3):
            a, b = int(t[j]), int(t[(j + 1) % 3])
            tri_of[(min(a, b), max(a, b))] = ti
    partner = {}
    groups = {}
    for e, w, jid in jobs:
        a, b = int(L[e]), int(L[(e + 1) % len(L)])
        ln = float(np.linalg.norm(V[b] - V[a]))
        if w * ln < 1e-6:
            partner[jid] = a
        elif (1 - w) * ln < 1e-6:
            partner[jid] = b
        else:
            groups.setdefault(int(e), []).append((float(w), jid))
    T = [list(map(int, t)) for t in T]
    newV = []; nV0 = len(V); failed = 0
    for e, lst in groups.items():
        a, b = int(L[e]), int(L[(e + 1) % len(L)])
        ti = tri_of.get((min(a, b), max(a, b)))
        if ti is None:
            failed += len(lst); continue
        t = T[ti]
        j = [q for q in range(3) if {t[q], t[(q + 1) % 3]} == {a, b}]
        if not j:
            failed += len(lst); continue
        j = j[0]
        x, y, c = t[j], t[(j + 1) % 3], t[(j + 2) % 3]
        lst.sort()
        if x != a:
            lst = [(1 - w, i) for w, i in lst][::-1]
        chain = [x]; P0, P1 = V[x], V[y]; lastw = -1.0
        for w, i in lst:
            if w - lastw < 1e-9 and len(chain) > 1:
                partner[i] = chain[-1]; continue
            idx = nV0 + len(newV); newV.append(P0 + (P1 - P0) * w)
            chain.append(idx); partner[i] = idx; lastw = w
        chain.append(y)
        T[ti] = [chain[0], chain[1], c]
        for q in range(1, len(chain) - 1):
            T.append([chain[q], chain[q + 1], c])
            for u_, v_ in ((chain[q], chain[q + 1]), (chain[q + 1], c), (c, chain[q])):
                tri_of[(min(u_, v_), max(u_, v_))] = len(T) - 1
    if newV:
        V = np.vstack([V, np.asarray(newV, float)])
    return V, np.asarray(T, int), partner, failed



def _track_param(P, Q, seg, cum, pts, t_start, tol):
    """Arc parameter of each point of an ORDERED run of points on a closed polyline, found by WALKING: each point is
    looked for only a little way ahead of the last one (2026-09-23). A global nearest-point projection jumps between
    the two strands of a hairpin - the rim loop running up one side of a thin edge and back down the other, 0.5 mm
    apart - and the monotone clamp then holds every later point back: R4's pillar seam refused 23 points at up to
    0.54 mm although each was within 0.106 mm of the body loop. Falls back to the global projection when nothing
    within the window is near (the loop was left), so a real gap still shows as a gap."""
    per = cum[-1]; n = len(P)
    AB = Q - P; L2 = np.maximum(seg ** 2, 1e-30)
    S = np.concatenate([cum[:-1] + k * per for k in (-1, 0, 1, 2)])
    SI = np.tile(np.arange(n), 4)
    tg, _ = _project_param(P, Q, seg, cum, pts)
    out = np.empty(len(pts)); t = float(t_start)
    for i in range(len(pts)):
        p = pts[i]
        step = float(np.linalg.norm(p - pts[i - 1])) if i else 0.0
        lo = t - 0.25; hi = t + 3.0 * step + 4.0 * tol + 0.5
        j0 = max(int(np.searchsorted(S, lo, side="right")) - 1, 0); j1 = min(int(np.searchsorted(S, hi, side="right")), len(S) - 1)
        js = np.arange(j0, j1 + 1); e = SI[js]
        w = np.clip(((p - P[e]) * AB[e]).sum(1) / L2[e], 0.0, 1.0)
        d = np.linalg.norm(p - (P[e] + AB[e] * w[:, None]), axis=1)
        k = int(np.argmin(d))
        if d[k] <= 3.0 * tol:
            cand = S[js[k]] + w[k] * seg[e[k]]
        else:
            cand = tg[i] + per * np.round((t - tg[i]) / per)
            if cand < t - 0.25:
                cand += per
        t = max(t, float(cand))
        out[i] = t
    return out


FAR_POINTS = []


def _pair_loops_monotone(VA, TA, la, VB, TB, lb, tol):
    """ONE monotone correspondence along the loop, so both insertions keep the same ORDER. Orthogonal
    projection each way let neighbours 0.03 mm apart swap sides where the surfaces are 0.15 mm apart, and every
    swap left a hole (172 open edges on bay V2-V3). Here B's vertices are placed on A by their projection
    parameter made NON-DECREASING along B, and A's vertices are placed on B through the inverse of that same
    map. Returns VA, TA, VB, TB, pairs [(a_vertex, b_vertex)], worst gap, count beyond tol."""
    PA, QA, sA, cA = _poly(VA, la)
    perA = cA[-1]
    lb = list(lb)
    PB0 = VB[np.asarray(lb, int)]
    t, _ = _project_param(PA, QA, sA, cA, PB0)
    dt = np.diff(np.unwrap(t * 2 * np.pi / perA)) * perA / (2 * np.pi)
    if np.median(dt) < 0:
        lb = lb[::-1]; PB0 = PB0[::-1]; t = t[::-1]
    j0 = int(np.argmin(np.minimum(t, perA - t)))
    lb = lb[j0:] + lb[:j0]; PB0 = VB[np.asarray(lb, int)]; t = np.concatenate([t[j0:], t[:j0]])
    tu = np.unwrap(t * 2 * np.pi / perA) * perA / (2 * np.pi)
    if tu[0] > perA / 2:
        tu = tu - perA
    tm = _track_param(PA, QA, sA, cA, PB0, float(tu[0]), tol)
    PBp, QBp, sB, cB = _poly(VB, lb)
    perB = cB[-1]
    u = cB[:-1]
    tt = np.concatenate([tm - perA, tm, tm + perA]); uu = np.concatenate([u - perB, u, u + perB])
    sAv = cA[:-1]
    ok = np.concatenate([[True], np.diff(tt) > 0])
    uA = np.interp(sAv, tt[ok], uu[ok])
    eB, wB, posB = _at_param(PBp, QBp, sB, cB, uA)
    eA, wA, posA = _at_param(PA, QA, sA, cA, tm)
    dA = np.linalg.norm(PB0 - posA, axis=1); dB = np.linalg.norm(VA[np.asarray(la, int)] - posB, axis=1)
    worst = float(max(dA.max(), dB.max()))
    far = int((dA > tol).sum() + (dB > tol).sum())
    FAR_POINTS.extend([("patch", PB0[i].round(2).tolist(), round(float(dA[i]), 3)) for i in np.where(dA > tol)[0]])
    FAR_POINTS.extend([("body", VA[la[i]].round(2).tolist(), round(float(dB[i]), 3)) for i in np.where(dB > tol)[0]])
    VA, TA, pA, fA = _split_edges(VA, TA, la, [(int(eA[j]), float(wA[j]), j) for j in range(len(lb))])
    VB, TB, pB, fB = _split_edges(VB, TB, lb, [(int(eB[i]), float(wB[i]), i) for i in range(len(la))])
    pairs = [(int(pA[j]), int(lb[j])) for j in range(len(lb)) if j in pA]
    pairs += [(int(la[i]), int(pB[i])) for i in range(len(la)) if i in pB]
    return VA, TA, VB, TB, pairs, worst, far + fA + fB


def seam_merge(VA, TA, VB, TB, tol=0.15, assign=None, say=print, onto=None, tiny="cap", micro="best"):
    """Join mesh A (the body with a hole) and mesh B (the patch) along their matching rim loops.
    Returns (V, T, report); V is None when refused, with report['error'] saying why.
    onto=None merges each point with its partner at their midpoint (the mesh route); onto="A" puts every merged
    point AT the A side (the burrito's keep-and-weld, 2026-10-01: A is the body's exact triangles, B the
    marching-cubes patch whose rim is rounded 0.15-0.30 at a sharp edge - the midpoint would halve that step,
    the A side removes it)."""
    VA, TA = _weld(VA, TA, 1e-7); VB, TB = _weld(VB, TB, 1e-7)
    def _cn(V_, T_):
        a_, b_, c_ = V_[T_[:, 0]], V_[T_[:, 1]], V_[T_[:, 2]]
        n_ = np.cross(b_ - a_, c_ - a_); n_ /= np.linalg.norm(n_, axis=1)[:, None] + 1e-30
        return (a_ + b_ + c_) / 3.0, n_
    cA_, nA_ = _cn(VA, TA); cB_, nB_ = _cn(VB, TB)
    uB_, kB_ = _edges(TB)
    rimv = np.unique(uB_[kB_ == 1])
    nearB = np.isin(TB, rimv).any(1)
    dd_, ii_ = cKDTree(cA_).query(cB_[nearB])
    m_ = dd_ < 0.3
    agree = float((np.einsum("ij,ij->i", nB_[nearB][m_], nA_[ii_[m_]]) > 0).mean()) if m_.any() else 1.0
    flipped = agree < 0.5
    if flipped:
        TB = TB[:, ::-1].copy()
    hA, hB = health(VA, TA), health(VB, TB)
    LA, _, badA = _loops(TA); LB, _, badB = _loops(TB)
    LA = [l for l in LA if len(l) >= 3]; LB = [l for l in LB if len(l) >= 3]
    rep = {"loopsA": len(LA), "loopsB": len(LB), "branchA": badA, "branchB": badB,
           "facing_agreement_near_rim": round(agree, 3), "patch_flipped": bool(flipped),
           "open_in": hA[0] + hB[0], "nonmanifold_in": hA[1] + hB[1]}
    IA = [(VA[l].mean(0), float(np.ptp(VA[l], 0).max())) for l in LA]
    IB = [(VB[l].mean(0), float(np.ptp(VB[l], 0).max())) for l in LB]
    cost = np.array([[np.linalg.norm(a[0] - b[0]) + 0.25 * abs(a[1] - b[1]) for b in IB] for a in IA]) if IA and IB else np.zeros((len(IA), len(IB)))
    # side by side
    if IA and IB:
        _tA = [cKDTree(VA[l]) for l in LA]
        for i_ in range(len(IA)):
            for j_ in range(len(IB)):
                if cost[i_, j_] <= 0.5 * max(IA[i_][1], IB[j_][1]) + tol:
                    cost[i_, j_] = float(np.percentile(_tA[i_].query(VB[LB[j_]])[0], 90))
    cap = np.array([[0.5 * max(a[1], b[1]) + tol for b in IB] for a in IA]) if IA and IB else np.zeros((len(IA), len(IB)))
    pairs = assign(cost, cap) if (assign is not None and cost.size) else []
    good = []
    for a, b in pairs:
        d = cKDTree(VB[LB[b]]).query(VA[LA[a]])[0]
        if np.percentile(d, 90) <= 3 * tol:
            good.append((a, b))
    pairs = good
    usedA = {a for a, _ in pairs}; usedB = {b for _, b in pairs}
    oA = [a for a in range(len(LA)) if a not in usedA]; oB = [b for b in range(len(LB)) if b not in usedB]
    mism = []
    for a in oA:
        ta = cKDTree(VA[LA[a]])
        for b in oB:
            if ta.query(VB[LB[b]])[0].min() <= 3.0:
                mism.append((a, b))
    rep["loops_paired"] = len(pairs)
    # open edges
    _orphB = [(len(LB[b]), [round(float(v), 1) for v in VB[LB[b]].mean(0)]) for b in oB if not any(b == bb for _a, bb in mism)]
    rep["patch_loops_unpaired"] = _orphB
    # UNPAIRED
    _cap_lim = 1.0
    _tiny = [b for b in oB if not any(b == bb for _a, bb in mism) and float(np.ptp(VB[LB[b]], 0).max()) < _cap_lim]
    if _tiny and tiny == "collapse":
        _col = np.arange(len(VB))
        for b in _tiny:
            lp = np.asarray(LB[b], int); c_ = VB[lp].mean(0); VB[lp[0]] = c_; _col[lp[1:]] = lp[0]
        TB = _col[TB]; TB = TB[(TB[:, 0] != TB[:, 1]) & (TB[:, 1] != TB[:, 2]) & (TB[:, 0] != TB[:, 2])]
        VB, TB = _weld(VB, TB, 1e-9)
        rep["patch_loops_collapsed"] = [len(LB[b]) for b in _tiny]
        _orphB = [o for o in _orphB if not any(o[0] == n_ for n_ in rep["patch_loops_collapsed"])]
        hB = health(VB, TB)
        rep["open_in"] = hA[0] + hB[0]; rep["nonmanifold_in"] = hA[1] + hB[1]
        # collapsed
        LB2, _, _ = _loops(TB); LB2 = [l for l in LB2 if len(l) >= 3]
        _tB2 = [cKDTree(VB[l]) for l in LB2]
        _re = []
        for a, b in pairs:
            _d = [(float(np.percentile(_tB2[j].query(VA[LA[a]])[0], 90)), j) for j in range(len(LB2))]
            _re.append((a, min(_d)[1]))
        pairs = _re; LB = LB2; _tiny = []
    if _tiny:
        _add = []
        for b in _tiny:
            lp = LB[b]
            ci = len(VB) + len(_add); _add.append(VB[lp].mean(0))
            e_ = set(); tri_dir = {}
            for t in TB:
                for j in range(3):
                    tri_dir[(int(t[j]), int(t[(j + 1) % 3]))] = True
            capt = []
            for q_ in range(len(lp)):
                u_, v_ = int(lp[q_]), int(lp[(q_ + 1) % len(lp)])
                capt.append([v_, u_, ci] if (u_, v_) in tri_dir else [u_, v_, ci])
            TB = np.vstack([TB, np.asarray(capt, int)])
        VB = np.vstack([VB, np.asarray(_add)])
        rep["patch_loops_capped"] = [(len(LB[b]), [round(float(v), 1) for v in VB[LB[b]].mean(0)]) for b in _tiny]
        _orphB = [o for o in _orphB if not any(o[1] == c[1] for c in rep["patch_loops_capped"])]
        hB = health(VB, TB)
        rep["open_in"] = hA[0] + hB[0]; rep["nonmanifold_in"] = hA[1] + hB[1]
    if _orphB:
        rep["error"] = ("%d loop(s) of the NEW surface have no body partner - each would be left as a hole: %s. The core "
                        "wall crosses the new surface where the body has no matching edge (a thin feature, a crack)."
                        % (len(_orphB), _orphB[:6]))
        return None, None, rep
    rep["loops_unrelated"] = len(oA) + len(oB) - len({a for a, _ in mism}) - len({b for _, b in mism})
    if mism:
        rep["error"] = ("DIFFERENT TOPOLOGY at the boundary: %d unmatched loop pair(s) within 3 mm of each other "
                        "(sizes %s) - the wall passes through a feature one build has and the other does not"
                        % (len(mism), [(len(LA[a]), len(LB[b])) for a, b in mism][:6]))
        return None, None, rep
    if not pairs:
        rep["error"] = "no loop pairs - the boundary does not cross both meshes"
        return None, None, rep
    worst = 0.0
    far = 0
    merge_pairs = []
    for a, b in pairs:
        VA, TA, VB, TB, pp, wst, fr = _pair_loops_monotone(VA, TA, LA[a], VB, TB, LB[b], tol)
        merge_pairs += pp; worst = max(worst, wst); far += fr
    rep["worst_mm"] = worst; rep["beyond_tol"] = far
    if far:
        rep["far_points"] = FAR_POINTS[:40]
        rep["error"] = ("%d rim point(s) have no partner within %.3f mm on the other side's loop; first ones (side, where, gap): %s"
                        % (far, tol, FAR_POINTS[:8]))
        return None, None, rep
    nA = len(VA)
    V = np.vstack([VA, VB]); T = np.vstack([TA, TB + nA])
    parent = np.arange(len(V))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for ia, ib in merge_pairs:
        ra, rb = find(ia), find(ib + nA)
        if ra != rb:
            parent[rb] = ra
    root = np.array([find(i) for i in range(len(V))])
    sums = np.zeros_like(V); cnt = np.zeros(len(V))
    np.add.at(sums, root, V); np.add.at(cnt, root, 1)
    V2 = sums / np.maximum(cnt, 1)[:, None]
    if onto == "A":
        isA = np.arange(len(V)) < nA
        sA = np.zeros_like(V); cA = np.zeros(len(V)); np.add.at(sA, root[isA], V[isA]); np.add.at(cA, root[isA], 1)
        V2 = np.where(cA[:, None] > 0, sA / np.maximum(cA, 1)[:, None], V2)
    moved = np.linalg.norm(V - V2[root], axis=1)
    rep["largest_move_mm"] = float(moved.max())
    T2 = root[T]
    T2 = T2[(T2[:, 0] != T2[:, 1]) & (T2[:, 1] != T2[:, 2]) & (T2[:, 0] != T2[:, 2])]
    # collapsed
    # over the
    _grp = np.bincount(root, minlength=len(V2))
    _at_seam = (_grp[T2] > 1).any(1)
    key = np.sort(T2, 1)
    u, inv, c = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    _dup = c[np.asarray(inv).reshape(-1)] > 1
    T2 = T2[~(_dup & _at_seam)]
    _fins = 0
    for _it in range(3):
        _ev = np.vstack([T2[:, [0, 1]], T2[:, [1, 2]], T2[:, [2, 0]]]); _ks = np.sort(_ev, 1)
        _u, _inv, _c = np.unique(_ks, axis=0, return_inverse=True, return_counts=True); _inv = _inv.ravel()
        _nm = np.nonzero(_c > 2)[0]
        if not len(_nm):
            break
        _P = V2[T2]; _n = np.cross(_P[:, 1] - _P[:, 0], _P[:, 2] - _P[:, 0])
        _n /= np.linalg.norm(_n, axis=1)[:, None] + 1e-30
        _drop = set()
        _tri_of_e = {}
        for _j, _k in enumerate(_inv):
            if _c[_k] > 2:
                _tri_of_e.setdefault(_k, []).append(_j % len(T2))
        for _k, _ts in _tri_of_e.items():
            if not (_grp[_u[_k]] > 1).any():
                continue
            for _a in range(len(_ts)):
                for _b in range(_a + 1, len(_ts)):
                    if float(_n[_ts[_a]] @ _n[_ts[_b]]) < -0.3:
                        _drop.update((_ts[_a], _ts[_b]))
        if not _drop:
            break
        _fins += len(_drop)
        T2 = T2[np.setdiff1d(np.arange(len(T2)), list(_drop))]
    rep["fin_triangles_removed"] = _fins
    seam_v = np.zeros(len(V2), bool)
    grp = np.bincount(root, minlength=len(V2))
    seam_v[grp > 1] = True
    ev = np.vstack([T2[:, [0, 1]], T2[:, [1, 2]], T2[:, [2, 0]]])
    ks = np.sort(ev, 1)
    uk, ik, ck = np.unique(ks, axis=0, return_inverse=True, return_counts=True)
    bnd = ev[ck[np.asarray(ik).reshape(-1)] == 1]          # boundary edges
    dirn = {}
    adj = {}
    for a_, b_ in bnd:
        a_, b_ = int(a_), int(b_)
        dirn[(min(a_, b_), max(a_, b_))] = (a_, b_)
        adj.setdefault(a_, set()).add(b_); adj.setdefault(b_, set()).add(a_)
    holes = []
    seenv = set()
    for a0 in list(adj):
        if a0 in seenv:
            continue
        comp, stack = [], [a0]
        while stack:
            x = stack.pop()
            if x in seenv:
                continue
            seenv.add(x); comp.append(x); stack.extend(adj[x] - seenv)
        # boundary edges
        # boundary edges
        if len(comp) < 3 or len(comp) > 30 or any(len(adj[x]) % 2 for x in comp) or not any(seam_v[x] for x in comp):
            continue
        P = V2[comp]
        if np.ptp(P, 0).max() > 0.5:
            continue
        holes.append(comp)
    capped = len(holes)
    if holes and micro == "open":
        # open edges
        rep["micro_holes_open"] = [(len(c), [round(float(v), 2) for v in V2[c].mean(0)]) for c in holes]
        rep["micro_hole_method"] = "open (left for the repair's fill: %d hole(s), %d edges)" % (len(holes), sum(len(c) for c in holes))
        holes = []; capped = 0
    if holes:
        caps, extraV = [], []
        for comp in holes:
            ci = len(V2) + len(extraV); extraV.append(V2[comp].mean(0))
            cs = set(comp); done = set()
            for x in comp:
                for y in adj[x]:
                    k = (min(x, y), max(x, y))
                    if k in done:
                        continue
                    done.add(k)
                    u_, v_ = dirn[k]
                    caps.append([v_, u_, ci])
        Vc = np.vstack([V2, np.asarray(extraV)]); Tc = np.vstack([T2, np.asarray(caps, int)])
        rm = np.arange(len(V2)); Vk = V2.copy()
        for comp in holes:
            Vk[comp[0]] = V2[comp].mean(0); rm[comp] = comp[0]
        Tk = rm[T2]
        Tk = Tk[(Tk[:, 0] != Tk[:, 1]) & (Tk[:, 1] != Tk[:, 2]) & (Tk[:, 0] != Tk[:, 2])]
        hc, hk = health(Vc, Tc), health(Vk, Tk)
        if (hk[1], hk[0]) < (hc[1], hc[0]):
            V2, T2 = Vk, Tk; rep["micro_hole_method"] = "collapse (open %d, non-manifold %d; cap would give %d, %d)" % (hk + hc)
        else:
            V2, T2 = Vc, Tc; rep["micro_hole_method"] = "cap (open %d, non-manifold %d; collapse would give %d, %d)" % (hc + hk)
    rep["micro_holes_capped"] = capped
    used = np.unique(T2)
    remap = -np.ones(len(V2), int); remap[used] = np.arange(len(used))
    V2 = V2[used]; T2 = remap[T2]
    o, nm = health(V2, T2)
    rep["open_out"] = o; rep["nonmanifold_out"] = nm
    _de = np.vstack([T2[:, [0, 1]], T2[:, [1, 2]], T2[:, [2, 0]]])
    _ud, _cd = np.unique(_de, axis=0, return_counts=True)
    rep["same_direction_edges_out"] = int((_cd > 1).sum())
    seam_edges = sum(len(LA[a]) + len(LB[b]) for a, b in pairs)
    rep["seam_open"] = int(o - (rep["open_in"] - seam_edges))
    rep["_V"], rep["_T"] = V2, T2
    _ue, _ce = _edges(T2)
    _nmE = _ue[_ce > 2]
    rep["nonmanifold_at"] = [[round(float(v), 2) for v in V2[e].mean(0)] for e in _nmE[:60]]
    if rep["seam_open"] > 0 or nm > rep["nonmanifold_in"]:
        rep["error"] = ("the seam did NOT close: %d open edge(s) beyond the inputs' own, non-manifold %d (inputs %d)"
                        % (rep["seam_open"], nm, rep["nonmanifold_in"]))
        return None, None, rep
    return V2, T2, rep

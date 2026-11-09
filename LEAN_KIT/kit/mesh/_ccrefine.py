# MESH_JOB
import os, sys, json, hashlib, time
import numpy as np
sys.path.insert(0, os.environ["KIT_HOME"])
import Part, MeshPart


def say(*a):
    print(*a, flush=True)


t0 = time.time()
DEV = float(os.environ.get("CC_DEV", "0.08"))
if os.environ["CC_BODY"].lower().endswith(".stl"):
    import kitlib_render as _KR
    _Vs, _Ts = _KR.read_stl(os.environ["CC_BODY"])
    V, T, _, _ = _KR._weld(np.asarray(_Vs, float), np.asarray(_Ts, np.int64), [], 1e-6)
    T = np.asarray(T, np.int64)
    say("body read from MESH %s: %d points, %d triangles (a crop base; the body itself is never the operand)"
        % (os.path.basename(os.environ["CC_BODY"]), len(V), len(T)))
    _side = os.path.splitext(os.environ["CC_BODY"])[0] + ".crop.json"
    _CAP_PLANES = []
    if os.path.isfile(_side):
        try:
            _gb = json.load(open(_side, encoding="utf-8"))["grown_box"]
            _CAP_PLANES = [((_gb[0], 0, 0), (1, 0, 0)), ((_gb[1], 0, 0), (-1, 0, 0)), ((0, _gb[2], 0), (0, 1, 0)),
                           ((0, _gb[3], 0), (0, -1, 0)), ((0, 0, _gb[4]), (0, 0, 1)), ((0, 0, _gb[5]), (0, 0, -1))]
            say("  a kit crop: its caps on the six walls are left unrefined")
        except (OSError, ValueError, KeyError):
            _CAP_PLANES = []
else:
    _CAP_PLANES = []
    sh = Part.Shape(); sh.importBrep(os.environ["CC_BODY"])
    m = MeshPart.meshFromShape(Shape=sh, LinearDeflection=DEV, AngularDeflection=0.4, Relative=False)
    m.removeDuplicatedPoints()
    V = np.asarray(m.Topology[0], float); T = np.asarray(m.Topology[1], np.int64)
    say("body meshed with meshFromShape (dev %.2f): %d points, %d triangles" % (DEV, len(V), len(T)))
if os.environ.get("CC_EXTENT", "").strip():
    _ext = [float(t) for t in os.environ["CC_EXTENT"].split()]
elif os.environ["CC_BODY"].lower().endswith(".stl"):
    _ext = None
    say("  no CC_EXTENT: the flap pass is skipped (an STL/crop base carries none of meshFromShape's flaps)")
else:
    say("FAIL: CC_EXTENT \"x0 x1 y0 y1 z0 z1\" (the body of record's extent) is not set; kit mesh fills it from the atlas"); raise SystemExit(2)
_mg = float(os.environ.get("CC_SPIKE_MARGIN", "0.5"))
if _ext is not None:
    _lo = np.array(_ext[0::2]) - _mg; _hi = np.array(_ext[1::2]) + _mg
    _out = ~np.all((V[T] >= _lo).all(2) & (V[T] <= _hi).all(2), axis=1)
    if _out.any():
        T = T[~_out]
        say("  spike flaps dropped before refinement: %d triangle(s) with a vertex outside the body's extent + %.1f mm" % (int(_out.sum()), _mg))
CORES = [[float(t) for t in c.split()] for c in os.environ.get("CC_CORES", "").split(";") if c.strip()]
from scipy.spatial import cKDTree
BLOBS = []
for bp in [t for t in os.environ.get("CC_BLOBS", "").split(";") if t.strip()]:
    z_ = np.load(bp.strip())
    BLOBS.append((cKDTree(np.asarray(z_["E"], float)), (np.asarray(z_["Mi"], float) if "Mi" in z_.files else float(z_["M"])), bp.strip()))
say("cores: %d analytic, %d edit-zone" % (len(CORES), len(BLOBS)))
L = float(os.environ.get("CC_REFINE_L", "0.3"))
TAG = os.environ.get("LK_TAG", "")


def f_all(P):
    """per point, the product over cores is not needed - an edge is marked if it crosses ANY core wall"""
    out = []
    for c in CORES:
        cen = np.asarray(c[:3]); rad = np.asarray(c[3:6]); rnd = c[6] if len(c) > 6 else 0.0
        if rnd > 0:
            out.append((np.abs((P - cen) / rad) ** (2.0 / rnd)).sum(-1) - 1.0)
        else:
            out.append((((P - cen) / rad) ** 2).sum(-1) - 1.0)
    for tr_, m_, _p in BLOBS:
        if np.ndim(m_) == 0:
            out.append(tr_.query(P)[0] - m_)
        else:
            _dk, _ik = tr_.query(P, k=16)
            out.append((_dk - m_[_ik]).min(1))
    return np.stack(out, 0)


def vol(V_, T_):
    a, b, c = V_[T_[:, 0]], V_[T_[:, 1]], V_[T_[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)


import traceback
try:
    v0 = vol(V, T)
    T_in = T.copy()
    Fc = None
    for it in range(60):
        E = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], 0)
        Es = np.sort(E, 1)
        U, inv = np.unique(Es, axis=0, return_inverse=True)
        inv = inv.ravel()
        nT = len(T)
        TE = inv.reshape(3, nT).T
        if Fc is None:
            Fc = f_all(V)
        elif Fc.shape[1] < len(V):
            Fc = np.concatenate([Fc, f_all(V[Fc.shape[1]:])], 1)
        F = Fc
        cross = ((F[:, U[:, 0]] * F[:, U[:, 1]]) < 0).any(0)
        ln = np.linalg.norm(V[U[:, 0]] - V[U[:, 1]], axis=1)
        mark = cross & (ln > L)
        tl = ln[TE]
        LE = np.argmax(tl, axis=1)
        LEid = TE[np.arange(nT), LE]
        if BLOBS:
            Fb = F[len(CORES):]
            near_t = (np.abs(Fb[:, T]).min(2) < tl.max(1)[None, :]).any(0) & (tl.max(1) > L)
            if _CAP_PLANES:
                _onw = np.zeros(len(T), bool)
                for _p0, _n in _CAP_PLANES:
                    _onw |= (np.abs((V[T] - np.asarray(_p0, float)) @ np.asarray(_n, float)) <= 1e-6).all(1)
                near_t &= ~_onw
            mark[LEid[near_t]] = True
        if not mark.any():
            break
        while True:
            has = mark[TE].any(1)
            add = has & ~mark[LEid]
            if not add.any():
                break
            mark[LEid[add]] = True
        mid_idx = -np.ones(len(U), np.int64)
        mid_idx[mark] = len(V) + np.arange(mark.sum())
        V = np.vstack([V, 0.5 * (V[U[mark, 0]] + V[U[mark, 1]])])
        M = mid_idx[TE]
        has = (M >= 0).any(1)
        out = [T[~has]]
        for k in range(3):
            s_ = has & (LE == k)
            if not s_.any():
                continue
            q0, q1, q2 = T[s_, k], T[s_, (k + 1) % 3], T[s_, (k + 2) % 3]
            m0, m1, m2 = M[s_, k], M[s_, (k + 1) % 3], M[s_, (k + 2) % 3]
            a1 = m1 >= 0; a2 = m2 >= 0
            out += [np.stack([q0[~a2], m0[~a2], q2[~a2]], 1),
                    np.stack([q0[a2], m0[a2], m2[a2]], 1), np.stack([m0[a2], q2[a2], m2[a2]], 1),
                    np.stack([m0[~a1], q1[~a1], q2[~a1]], 1),
                    np.stack([m0[a1], q1[a1], m1[a1]], 1), np.stack([m0[a1], m1[a1], q2[a1]], 1)]
        T = np.concatenate(out, 0)
        say("  pass %2d: split %6d edges (crossing a core wall, or closing the longest-edge rule) -> %d triangles"
            % (it + 1, int(mark.sum()), len(T)))
    v1 = vol(V, T)
    # open edges
    def open_count(T_):
        e = np.sort(np.concatenate([T_[:, [0, 1]], T_[:, [1, 2]], T_[:, [2, 0]]], 0), 1)
        _, c = np.unique(e, axis=0, return_counts=True)
        return int((c == 1).sum()), int((c > 2).sum())
    say("volume before %.3f  after %.3f mm3 (difference %.2e - midpoints lie on their triangles)" % (v0, v1, v1 - v0))
    say("open / non-manifold edges: before %d / %d, after refinement %d / %d (a split open edge counts twice)"
        % (open_count(T_in) + open_count(T)))
    _E = np.unique(np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], 0), 1), axis=0)
    _F = Fc if (Fc is not None and Fc.shape[1] == len(V)) else f_all(V)
    if _F.shape[1] < len(V):
        _F = np.concatenate([_F, f_all(V[_F.shape[1]:])], 1)
    _x = ((_F[:, _E[:, 0]] * _F[:, _E[:, 1]]) < 0).any(0)
    _l = np.linalg.norm(V[_E[_x, 0]] - V[_E[_x, 1]], axis=1)
    say("edges crossing a core wall: %d, longest %.2f mm, p99 %.2f, over %.2f: %d" % (_x.sum(), _l.max(), np.percentile(_l, 99), L, (_l > L).sum()))
    OUT = os.environ["CC_OUT"]
    import struct
    # collapsed
    tri32 = V[T].astype(np.float32).astype(np.float64)
    q = np.round(tri32.reshape(-1, 3) / 1e-6).astype(np.int64)
    uq, iq = np.unique(q, axis=0, return_inverse=True)
    Tq = iq.reshape(-1, 3)
    good = (Tq[:, 0] != Tq[:, 1]) & (Tq[:, 1] != Tq[:, 2]) & (Tq[:, 0] != Tq[:, 2])
    say("zero-area / collapsed triangles dropped: %d" % int((~good).sum()))
    T = T[good]
    tri = V[T].astype(np.float32)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); ln_ = np.linalg.norm(n, axis=1); ln_[ln_ == 0] = 1
    rec = np.zeros(len(tri), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    rec["n"] = (n / ln_[:, None]).astype(np.float32); rec["v"] = tri.reshape(-1, 9)
    with open(OUT, "wb") as fh:
        fh.write(b"the agent refined base".ljust(80, b" ")); fh.write(struct.pack("<I", len(tri))); fh.write(rec.tobytes())
    h = hashlib.md5(open(OUT, "rb").read()).hexdigest()
    json.dump({"md5": h, "from": os.environ["CC_BODY"], "kind": "refined base (geometry unchanged)",
               "cores": CORES, "blobs": [b[2] for b in BLOBS], "refine_l": L, "tag": TAG, "triangles": int(len(T)),
               "note": "the model of record's mesh with edges crossing each weld core wall split at their midpoints - "
                       "an UNEDITED body, a valid base for every weld of the round while this md5 matches"},
              open(OUT + ".base.json", "w"), indent=1)
    say("wrote %s (%d triangles, md5 %s) in %.0f s" % (OUT, len(T), h[:8], time.time() - t0))
    say("DONE")
except Exception:
    say(traceback.format_exc())
    raise

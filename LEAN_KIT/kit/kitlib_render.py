"""rlib - small numpy renderer + section tools for headless FreeCAD work (no GUI).
Runs under freecadcmd's python (numpy 1.26, PIL 12).  Defines only.
"""
import os, json, math
for _v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np

# PROJECT_FACTS section 6
F = np.array([0.0, -1.0, 0.0])
L = np.array([1.0, 0.0, 0.0])
U = np.array([0.0, 0.0, 1.0])
try:
    _env_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "env.json")
    _env_fr = ((json.load(open(_env_p, encoding="utf-8")) or {}).get("frame") or None) if os.path.isfile(_env_p) else None
    if _env_fr:
        _fv = [np.array([float(x) for x in _env_fr[k]]) for k in ("forward", "left", "up")]
        if any(len(v) != 3 or float(np.linalg.norm(v)) < 1e-9 for v in _fv): raise ValueError("each of forward / left / up is three numbers, not all zero")
        F, L, U = [v / float(np.linalg.norm(v)) for v in _fv]
except Exception as _e_fr:      # cannot be read
    import sys as _sys; _sys.stderr.write("kitlib_render: env.json 'frame' not taken (%s) - the document's axes stand\n" % str(_e_fr)[:120])
# 31by: the frame block ends here


CAP_COLOUR = (0.72, 0.74, 0.78)


def _n(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def look(fwd=0.0, left=0.0, up=0.0):
    """camera LOOK direction in vehicle words: look(fwd=-1) stands ahead looking aft (shows the front)."""
    return _n(fwd * F + left * L + up * U)


def tess_shape(shape, dev=0.1, faces=None, ang=None):
    """returns V (n,3), T (m,3), FID (m,) face index per triangle.

    ang (31bl): an ANGULAR deflection in radians as well as the linear one - MeshPart.meshFromShape per face. MEASURED on a 57-face piece
    (the reviewer's probe, 2026-10-12): Part.tessellate(0.05) = 144,684 triangles = MeshPart(0.05, 0.1 rad) exactly - the kernel's plain
    tessellation already carries 0.1 rad; ang 0.25 -> 52,529 (a third), ang 0.05 -> 375,358. So ang is a way to go FINER than the plain
    tessellation (ang < 0.1), never a free smoothing. MeshPart writes its triangulation into the faces: a later f.tessellate(x) on the same
    shape returns that mesh whatever x. None = the linear deflection only (every caller before 31bl).

    `faces` may be Face OBJECTS or INTEGER INDICES into shape.Faces — indices are resolved
    rather than refused, because an int index is exactly determined and every caller that
    passed one meant that face.

    WHY THIS IS NOT A BARE `except: continue` ANY MORE. Live session, 2026-09-09: *"tess_shape
    wants face objects, not indices. Hand it indices and it returns an empty tessellation, and
    every number downstream is a clean answer from an empty set. It cost me one run and only
    announced itself because I print the triangle count."*
    That is the exact failure class this kit exists to stop — not a wrong answer that looks
    wrong, but a wrong answer that looks RIGHT. An empty selection is now an exception, because
    there is no measurement it can honestly support: no volume, no area, no clearance. A caller
    that genuinely wants "nothing selected" can test the selection itself and not call this.
    """
    all_faces = shape.Faces
    if faces is None:
        fl = all_faces
    else:
        fl = []
        for k, f in enumerate(faces):
            if isinstance(f, (int, np.integer)):
                if not (0 <= int(f) < len(all_faces)):
                    raise IndexError(
                        "tess_shape: face index %d is out of range — this shape has %d faces."
                        % (int(f), len(all_faces)))
                fl.append(all_faces[int(f)])
            elif hasattr(f, "tessellate"):
                fl.append(f)
            else:
                raise TypeError(
                    "tess_shape: faces[%d] is %s, which is neither a Face nor an index.\n"
                    "  Pass shape.Faces objects, or ints indexing them." % (k, type(f).__name__))
    Vs, Ts, Fs, off, failed = [], [], [], 0, []
    for i, f in enumerate(fl):
        try:
            if ang:
                try:
                    import MeshPart
                    _m = MeshPart.meshFromShape(Shape=f, LinearDeflection=float(dev), AngularDeflection=float(ang), Relative=False)
                    tv, tt = _m.Topology
                except Exception:
                    tv, tt = f.tessellate(dev)          # MeshPart
            else:
                tv, tt = f.tessellate(dev)
        except Exception as exc:
            failed.append("%d (%s)" % (i, exc.__class__.__name__))
            continue
        if not tt:
            continue
        Vs.append(np.array([[p.x, p.y, p.z] for p in tv]))
        Ts.append(np.array(tt, int) + off)
        Fs.append(np.full(len(tt), i, np.int64))
        off += len(tv)
    if not Vs:
        raise ValueError(
            "tess_shape produced ZERO triangles from %d face(s)%s.\n"
            "  Nothing downstream of this can be measured, so it refuses here rather than "
            "returning\n  an empty set that every later number would quietly agree with.\n"
            "  Usual causes: an empty face selection, a deflection too coarse for the feature, "
            "or a\n  shape that carries no faces at all."
            % (len(fl), (" — %d failed to tessellate: %s" % (len(failed), ", ".join(failed[:6])))
               if failed else ""))
    return np.vstack(Vs), np.vstack(Ts), np.concatenate(Fs)


def save_tess(path, V, T, FID):
    np.savez_compressed(path, V=V, T=T, FID=FID)


def load_tess(path):
    z = np.load(path)
    return z["V"], z["T"], z["FID"]



def save_tess_cache(path, V, T, FID, source, dev, quality=None):
    """The tessellation plus ITS PROVENANCE. A cache without provenance is L9 waiting to happen. 31bn: plus the mesh's QUALITY (piece_mesh's
    verdict - the frames drawn from it are stamped by it)."""
    import json as _j
    np.savez_compressed(
        path, V=np.asarray(V, np.float32), T=np.asarray(T, np.int32), FID=np.asarray(FID),
        dev=float(dev), source=str(source),
        source_mtime=float(os.path.getmtime(source)) if os.path.exists(source) else 0.0,
        written=float(__import__("time").time()), quality=_j.dumps(quality or {}))


def load_tess_cache(path, allow_stale=False):
    """(V, T, FID, meta) - and it REFUSES a cache older than the shape it was made from.

    L9 IS WHY THIS GUARD IS IN THE CACHE AND NOT IN THE CALLER. A piece was once overlaid against a
    reference mesh from a different card, two hours and one card out of date, and the comparison
    looked entirely plausible and meant nothing. Caching makes that mistake cheaper to commit, so
    the guard has to live where the mistake would be made.
    """
    z = np.load(path, allow_pickle=False)
    meta = {k: (z[k].item() if z[k].shape == () else z[k]) for k in ("dev", "source", "source_mtime", "written") if k in z.files}
    if "quality" in z.files:
        import json as _j
        try: meta["quality"] = _j.loads(str(z["quality"].item() if z["quality"].shape == () else z["quality"])) or None
        except Exception: meta["quality"] = None
    src = str(meta.get("source", ""))
    if not allow_stale and src and os.path.exists(src):
        if os.path.getmtime(src) > float(meta.get("written", 0)) + 1.0:
            raise SystemExit(
                "TESS CACHE IS STALE: %s was written %s, and its source %s changed since.\n"
                "  Re-run the cache step. An overlay against a stale reference looks plausible and "
                "means nothing (L9)."
                % (os.path.basename(path), __import__("time").strftime(
                    "%H:%M:%S", __import__("time").localtime(float(meta.get("written", 0)))), src))
    V, T = z["V"], z["T"]
    if len(T) == 0:
        raise SystemExit(
            "TESS CACHE IS EMPTY: %s holds 0 triangles. The shape tessellated to nothing.\n"
            "  That is a RESULT, not a detail - report it and stop. An empty tessellation is what "
            "made a 192-byte result file carry a fresh timestamp and look like a product (L13)."
            % os.path.basename(path))
    return V, T, z["FID"], meta


# DIFFERENT
def orbit_sweep(n_orbit=24, rings=(-25.0, 20.0)):
    """[(name, (dx,dy,dz))] - the full review sweep. Deterministic; the names are stable."""
    out = []
    per = max(1, n_orbit // len(rings))
    for el in rings:
        e = math.radians(el)
        for i in range(per):
            a = math.radians(360.0 * i / per)
            out.append(("orb%s_%03d" % ("lo" if el < 0 else "hi", int(round(math.degrees(a)))),
                        (math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))))
    out += [("ortho_front", (0, 1, 0)), ("ortho_back", (0, -1, 0)),
            ("ortho_left", (1, 0, 0)), ("ortho_right", (-1, 0, 0)),
            ("ortho_top", (0, 0, -1)), ("ortho_bottom", (0, 0, 1)),
            ("iso_fl", (0.577, 0.577, -0.577)), ("iso_br", (-0.577, -0.577, -0.577))]
    return out


def shard_frames(frames, shards):
    """Split by CONTIGUOUS ARC, never round-robin.

    A reviewer handed every sixth frame sees a scatter of unrelated angles; one handed a contiguous
    sweep sees MOTION, and a defect that appears, rotates and disappears is a different and much
    easier thing to spot than the same defect in one still. Coverage is identical either way - this
    is about what a human or an agent can actually read.
    """
    n, k = len(frames), max(1, int(shards))
    return [frames[i * n // k:(i + 1) * n // k] for i in range(k)]


def div_volume(V, T):
    P = V[T]
    return float(np.einsum("ij,ij->i", P[:, 0], np.cross(P[:, 1], P[:, 2])).sum() / 6.0)


def tri_normals(V, T):
    P = V[T]
    n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    a = np.linalg.norm(n, axis=1)
    a[a == 0] = 1.0
    return n / a[:, None]


def basis(d):
    """Camera frame for a look direction. Returns (forward, right, up) in world axes.

    THE STRAIGHT-DOWN VIEW USED TO COME OUT BACKWARDS. For d = (0,0,-1) — the "top" view — the
    old `upref = (0,-1,0)` gave right = (-1,0,0), so **image-x ran the wrong way**: something at
    the left-hand end of the part drew at the right-hand end of the picture, with +y pointing
    down as well. A test orchestrator caught it on 2026-09-09 only because its two features were
    asymmetric; on a centred feature there is no clue at all.

    That is the R1 failure with the evidence itself lying — a feature built on the wrong side
    renders as a perfect picture, and the whole method rests on the orchestrator believing what
    it sees. So the degenerate case now picks upref = (0,+1,0), giving right = +x and up = +y,
    which is how anyone reads a plan view.

    Looking UP from underneath keeps upref = (0,-1,0): from below, +y genuinely IS reversed
    relative to the top view, and pretending otherwise would be a different lie. The caption
    written by `axes_label()` says which is which on every frame, so no view has to be
    remembered.
    """
    d = _n(d)
    upref = np.array([0.0, 0.0, 1.0])
    if abs(np.dot(d, upref)) > 0.95:
        upref = np.array([0.0, 1.0, 0.0]) if d[2] < 0 else np.array([0.0, -1.0, 0.0])
    r = _n(np.cross(d, upref))
    u = _n(np.cross(r, d))
    return d, r, u


def axes_label(r3, u3):
    """'+x right, +y up' for the frame — so a view never has to be remembered or guessed.

    An orbit view with no axis on it cannot be checked against a card that says "the slot is at
    the LEFT-HAND end". This is one string and it makes every frame self-describing.
    """
    def nm(v):
        i = int(np.argmax(np.abs(v)))
        return "%s%s" % ("+" if v[i] > 0 else "-", "xyz"[i])
    return "%s right, %s up" % (nm(np.asarray(r3, float)), nm(np.asarray(u3, float)))


def cut_mesh(V, T, C, p0, n, tol=1e-7, cap=True):
    """A REAL CUT: triangles are SPLIT on the plane and the exposed face is CAPPED. Returns
    (V, T, C, (loops_closed, loops_open)) - and, with cap=False, a fifth element: the closed loops
    (lists of vertex indices) for the caller to fill itself. `render()` uses that: it fills the cap in
    IMAGE space with the even-odd rule, which is exact for a ring, a vane row or any concave outline.

    THE CENTROID FAN IS GONE FROM THE PICTURE (2026-09-24). Until then the cap of each closed loop was a
    fan from the loop's centroid - "correct for a convex section outline, approximate for a concave one".
    A real section is almost never convex: a part cut is a thin ring with vanes and pockets, and a fan
    from the ring's centroid paints triangles straight across the hollow, over the vanes, out through
    the pockets. Those are the "shards / triangles that are not real" the client kept seeing in sectioned
    renders and that every doc told agents to disbelieve. With cap=True (a caller that wants cap
    TRIANGLES) each closed loop is ear-clipped on its own plane instead - exact for any simple outline;
    a loop that lies inside another (a hole) is NOT triangulated, and the outer loop's triangles cover it,
    which a volume caller must know: use the loops and the even-odd rule for a number.

    WHY THIS REPLACED A CENTROID FILTER (2026-09-21). The old `clip` dropped a triangle when its
    CENTROID fell on the far side. That is not a cut, it is a filter, and it produces a ragged
    boundary made of whole triangles that reads in the frame as an edge of the part. the client, on such a
    picture: *"It looks like a cross section that is making edits on a boundary line that isn't
    really there."* Three separate pictures had to be disproved for them before the cause was found,
    and the kit itself was captioning the filter as a "section".

    After the split the boundary IS the plane, so nothing false is drawn. The cap is a fan from each
    closed loop's centroid: correct for a convex section outline, approximate for a concave one, and
    stated here rather than discovered. **Loops that do not close are COUNTED AND RETURNED** - on a
    body carrying boundary edges of its own (R31: 3,306 after welding) a cut cannot close everywhere,
    and a caller that reports "section" without saying so is making the same claim this function
    exists to stop. Caption the frame with both numbers.
    """
    V = np.asarray(V, float); T = np.asarray(T, int); C = np.asarray(C, float)
    if len(T) == 0:
        return V, T, C, (0, 0)
    if C.ndim == 1:
        C = np.tile(C, (len(T), 1))
    d = (V - p0) @ n
    dt = d[T]
    inside = dt <= 0
    n_in = inside.sum(1)
    keep_whole = n_in == 3
    straddle = (n_in == 1) | (n_in == 2)
    Vo = [V]
    To = [T[keep_whole]]
    Co = [C[keep_whole]]
    segs = []
    extra_v, extra_t, extra_c = [], [], len(V)
    nv = len(V)
    for ti in np.where(straddle)[0]:
        tri = T[ti]
        poly = []
        cut = []
        for a in range(3):
            i, j = tri[a], tri[(a + 1) % 3]
            di, dj = d[i], d[j]
            if di <= 0:
                poly.append(("v", i))
            if (di <= 0) != (dj <= 0):
                w = di / (di - dj)
                p = V[i] + w * (V[j] - V[i])
                poly.append(("p", len(extra_v) + nv))
                cut.append(len(extra_v) + nv)
                extra_v.append(p)
        if len(poly) < 3:
            continue
        idx = [k for _, k in poly]
        for a in range(1, len(idx) - 1):
            extra_t.append((idx[0], idx[a], idx[a + 1]))
            Co.append(C[ti][None, :])
        if len(cut) == 2:
            segs.append(tuple(cut))
    if extra_v:
        Vo.append(np.asarray(extra_v, float))
    if extra_t:
        To.append(np.asarray(extra_t, int))
    Vall = np.vstack(Vo)
    Tall = np.vstack([t for t in To if len(t)]) if any(len(t) for t in To) else np.zeros((0, 3), int)
    Call = np.vstack([c for c in Co if len(c)]) if any(len(c) for c in Co) else np.zeros((0, 3), float)

    closed = opened = 0
    loops_out = []
    if segs:
        q = np.round(Vall[nv:], 6) if len(Vall) > nv else np.zeros((0, 3))
        canon = {}
        rep = {}
        for k in range(len(q)):
            t = tuple(q[k])
            canon.setdefault(t, nv + k)
            rep[nv + k] = canon[t]
        segs = [(rep.get(a, a), rep.get(b, b)) for a, b in segs]
        segs = [(a, b) for a, b in segs if a != b]
        key = {}
        for a, b in segs:
            key.setdefault(a, []).append(b)
            key.setdefault(b, []).append(a)
        seen = set()
        cap_t, cap_c = [], []
        col = np.array(CAP_COLOUR)
        for start in list(key):
            if start in seen:
                continue
            loop, cur, prev = [start], start, None
            seen.add(start)
            while True:
                nxt = [q for q in key.get(cur, []) if q != prev]
                nxt = [q for q in nxt if q not in seen or q == start]
                if not nxt:
                    opened += 1
                    loop = None
                    break
                prev, cur = cur, nxt[0]
                if cur == start:
                    closed += 1
                    break
                seen.add(cur)
                loop.append(cur)
                if len(loop) > 200000:
                    opened += 1
                    loop = None
                    break
            if not loop or len(loop) < 3:
                continue
            pts = Vall[loop]
            _nl = np.zeros(3)
            for a in range(len(pts)):
                p, q = pts[a], pts[(a + 1) % len(pts)]
                _nl += np.cross(p, q)
            if _nl @ n < 0:
                loop = loop[::-1]
                pts = Vall[loop]
            loops_out.append(list(loop))
        if cap and loops_out:
            r2, u2 = _plane_basis(n)
            P2 = [(Vall[lp] - p0) @ np.column_stack([r2, u2]) for lp in loops_out]
            for k, lp in enumerate(loops_out):
                depth = sum(1 for j, q in enumerate(P2) if j != k and _point_in_poly(P2[k][0], q))
                if depth % 2 == 1:
                    continue
                for a, b, c in _ear_clip(P2[k]):
                    cap_t.append((lp[a], lp[b], lp[c])); cap_c.append(col)
        if cap_t:
            Tall = np.vstack([Tall, np.asarray(cap_t, int)])
            Call = np.vstack([Call, np.asarray(cap_c, float)])
    if cap:
        return Vall, Tall, Call, (closed, opened)
    return Vall, Tall, Call, (closed, opened), loops_out


def _plane_basis(n):
    """two unit vectors spanning the plane with normal n (right-handed with n)."""
    n = _n(n)
    a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    r = _n(np.cross(n, a)); u = np.cross(n, r)
    return r, u


def _point_in_poly(p, poly):
    """even-odd point-in-polygon in 2-D (poly: (k,2))."""
    x, y = p
    xs, ys = poly[:, 0], poly[:, 1]
    xj, yj = np.roll(xs, 1), np.roll(ys, 1)
    cond = (ys > y) != (yj > y)
    with np.errstate(divide="ignore", invalid="ignore"):
        xint = xj + (y - yj) * (xs - xj) / (ys - yj)
    return bool(np.count_nonzero(cond & (x < xint)) % 2)


def _ear_clip(P):
    """triangles (index triples into P) of a simple 2-D polygon, by ear clipping. Reflex checks are
    vectorised, so a 2,000-vertex loop is well under a second. A degenerate polygon yields nothing."""
    P = np.asarray(P, float)
    m = len(P)
    if m < 3:
        return []
    area2 = float(np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]))
    idx = list(range(m)) if area2 > 0 else list(range(m))[::-1]
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 4 * m:
        guard += 1
        found = False
        k = len(idx)
        for a in range(k):
            i0, i1, i2 = idx[a - 1], idx[a], idx[(a + 1) % k]
            p0, p1, p2 = P[i0], P[i1], P[i2]
            cross = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])
            if cross <= 1e-12:
                continue
            others = np.array([j for j in idx if j not in (i0, i1, i2)])
            if len(others):
                Q = P[others]
                d0 = (p1[0] - p0[0]) * (Q[:, 1] - p0[1]) - (p1[1] - p0[1]) * (Q[:, 0] - p0[0])
                d1 = (p2[0] - p1[0]) * (Q[:, 1] - p1[1]) - (p2[1] - p1[1]) * (Q[:, 0] - p1[0])
                d2 = (p0[0] - p2[0]) * (Q[:, 1] - p2[1]) - (p0[1] - p2[1]) * (Q[:, 0] - p2[0])
                # open edges
                sc = max(float(np.abs(p1 - p0).max()), float(np.abs(p2 - p1).max()), float(np.abs(p0 - p2).max()), 1e-12)
                tol = 1e-9 * sc * sc; tolc = 1e-9 * sc
                on_or_in = (d0 >= -tol) & (d1 >= -tol) & (d2 >= -tol)
                coinc = (np.abs(Q - p0).max(1) <= tolc) | (np.abs(Q - p1).max(1) <= tolc) | (np.abs(Q - p2).max(1) <= tolc)
                if np.any(on_or_in & ~coinc):
                    continue
            tris.append((i0, i1, i2)); idx.pop(a); found = True
            break
        if not found:
            break
    if len(idx) == 3:
        tris.append((idx[0], idx[1], idx[2]))
    return tris


def _project_root(path):
    """the project folder (the one holding .claude) above a file, or None"""
    try:
        import leangate as _G; _sr = _G.records_root("")
        if _sr:
            os.makedirs(os.path.join(_sr, ".claude"), exist_ok=True); return _sr
        r = os.path.dirname(os.path.abspath(path)); _home = os.path.normcase(os.path.abspath(os.path.expanduser("~")))
        while r and os.path.dirname(r) != r:
            if os.path.normcase(r) == _home or os.path.isdir(os.path.join(r, ".claude", "projects")): return None
            if os.path.isdir(os.path.join(r, ".claude")): return r
            r = os.path.dirname(r)
    except Exception:
        pass
    return None


def index_frame(path, box, d=None, title="", quality=None):
    """31am - LOOK BEFORE YOU MEASURE (the client, 2026-10-06: "the agent must be pushed to render review if a measurement is about to be
    taken in the next step ... it must be gated to be properly targeted at the measurement subject in question"). Every picture says
    what it frames, so the guard can tell a picture AT a measurement's subject from one that is not: {png, box (x0 x1 y0 y1 z0 z1 of
    the framed region), view, title} appended to <project>\\.claude\\frames.jsonl. Never raises - a picture is never lost to its index."""
    try:
        import time as _t
        root = _project_root(path)
        if not root: return
        b = [float(v) for v in box]
        rec = {"png": os.path.abspath(path), "png_n": os.path.normcase(os.path.abspath(path)).replace("\\", "/"), "box": [round(v, 3) for v in b],
               "view": [round(float(v), 4) for v in d] if d is not None else None, "title": str(title or "")[:160], "when": _t.time(),
               "quality": (dict(quality) if isinstance(quality, dict) else None), "defective": bool(isinstance(quality, dict) and quality.get("defective"))}
        p = os.path.join(root, ".claude", "frames.jsonl")
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        if os.path.getsize(p) > 5_000_000:
            with open(p, encoding="utf-8", errors="replace") as fh:
                keep = fh.readlines()[-4000:]
            with open(p, "w", encoding="utf-8") as fh:
                fh.writelines(keep)
    except Exception:
        pass


PIC_W = int(os.environ.get("PIC_W", "1000") or 1000)


def box_cover(zbuf, box, d3, r3, u3, x0, y1, mmpx, W, H, cap_mask=None):
    """31bv K32 (the tester TB2's F2): THE BOX'S FOOTPRINT AND ITS COVER, PER PIXEL BY THE VIEW RAY - a pixel is in the footprint when its orthographic ray (from the
    frame plane, along d3) HITS the box (the slab test on the three axis pairs), DRAWN when the depth buffer holds a surface there, COVERED when that surface lies
    nearer than the ray's ENTRY into the box at that pixel. The first form took the footprint as the box's bounding rectangle on the frame and 'nearer' against the
    box's one nearest corner, the rectangle's empty background in the denominator: a box poking out of the body (the cutter's 8 mm box, 4.7 mm of it air above
    the plate) read 84000 covered of 201075 - under the half - and MISS where every drawn pixel of its footprint was the wall in front of it. Returns
    (box_px, box_drawn_px, occluded_px); the callers judge OCCLUDED on the DRAWN footprint."""
    sx0, sx1, sy0, sy1, sz0, sz1 = [float(v) for v in box]
    r3 = np.asarray(r3, float); u3 = np.asarray(u3, float); d3 = np.asarray(d3, float)
    _cb = np.array([[cx_, cy_, cz_] for cx_ in (sx0, sx1) for cy_ in (sy0, sy1) for cz_ in (sz0, sz1)], float)
    _bxp = (_cb @ r3 - x0) / mmpx; _byp = (y1 - _cb @ u3) / mmpx
    _c0, _c1 = max(0, int(np.floor(_bxp.min()))), min(int(W) - 1, int(np.ceil(_bxp.max()))); _r0, _r1 = max(0, int(np.floor(_byp.min()))), min(int(H) - 1, int(np.ceil(_byp.max())))
    if _c1 < _c0 or _r1 < _r0:
        return 0, 0, 0
    _jj, _ii = np.mgrid[_r0:_r1 + 1, _c0:_c1 + 1]; _jj = _jj.ravel(); _ii = _ii.ravel()
    _P0 = (x0 + (_ii + 0.5) * mmpx)[:, None] * r3[None, :] + (y1 - (_jj + 0.5) * mmpx)[:, None] * u3[None, :]
    _lo = np.array([sx0, sy0, sz0]); _hi = np.array([sx1, sy1, sz1])
    _tmin = np.full(len(_P0), -np.inf); _tmax = np.full(len(_P0), np.inf); _hit = np.ones(len(_P0), bool)
    for _k in range(3):
        if abs(d3[_k]) < 1e-12:
            _hit &= (_P0[:, _k] >= _lo[_k] - 1e-9) & (_P0[:, _k] <= _hi[_k] + 1e-9)
        else:
            _t1 = (_lo[_k] - _P0[:, _k]) / d3[_k]; _t2 = (_hi[_k] - _P0[:, _k]) / d3[_k]
            _tmin = np.maximum(_tmin, np.minimum(_t1, _t2)); _tmax = np.minimum(_tmax, np.maximum(_t1, _t2))
    _hit &= _tmax >= _tmin - 1e-9
    _z = np.asarray(zbuf)[_jj, _ii]; _drawn = _hit & np.isfinite(_z)
    _cov = _drawn & (_z < _tmin - 1e-6)
    if cap_mask is not None:
        try: _cov |= _drawn & np.asarray(cap_mask, bool)[_jj, _ii]
        except Exception: pass
    return int(_hit.sum()), int(_drawn.sum()), int(_cov.sum())


def render(path, parts, d, W=1400, pad=5.0, bg=(0.13, 0.14, 0.17), focus=None, light=None,
           title=None, clip=None, H=None, scale_bar=True, edges=True, subject_box=None, stats=None):
    """parts: list of (name, V, T, C) with C = (m,3) rgb per triangle in 0..1, or a single rgb.
    d: look direction (camera looks ALONG d).  focus: (k,3) points defining the framed window
    (default: all vertices).  clip: optional (point, normal): triangles whose centroid has
    (c-point).n > 0 are dropped (cutaway).  Writes png. Returns mm/px.

    subject_box: ((x0,x1),(y0,y1),(z0,z1)) — the region the frame is FOR. With it, `stats` (a
    dict the caller passes) is filled with what the frame actually shows: `drawn_px` (pixels
    with geometry), `subject_px` (pixels whose own surface point - by the depth buffer - lies inside the box; 31bu TK6 F2 - the owning triangle's centroid before, blind to a big triangle), `box_px` / `occluded_px` (the box's footprint on the frame and the pixels of it covered by nearer surface - 31bv K32: a view that cannot see the box is OCCLUDED, reported, not failed),
    and `shows` (the xyz extent of the triangles that are visible). Ported from an earlier kit's
    `zbuf.zrender_owned` ownermap / subject-pixel manifest: the client, 2026-09-10, on the R18 survey —
    "renders are not targeting well — ABC_tipP_6_bottom, ABC_tipP_7_back do not include the
    section in question at all". A frame is framed on the box but the body can OCCLUDE it; the
    only way to know is to count who owns the pixels."""
    W = int(min(int(W), PIC_W)) if PIC_W > 0 else int(W)
    from PIL import Image, ImageDraw
    d3, r3, u3 = basis(d)
    Vs, Ts, Cs = [], [], []
    cap_loops = []
    off = 0
    for nm, V, T, C in parts:
        V = np.asarray(V, float); T = np.asarray(T, int)
        if len(T) == 0:
            continue
        C = np.asarray(C, float)
        if C.ndim == 1:
            C = np.tile(C, (len(T), 1))
        if clip is not None:
            p0, nn = np.asarray(clip[0], float), _n(clip[1])
            V, T, C, _cap, _loops = cut_mesh(V, T, C, p0, nn, cap=False)
            _capcol = np.array(CAP_COLOUR)
            for lp in _loops:
                cap_loops.append((V[lp], _capcol))
            if stats is not None:
                s = stats.setdefault("cut", {"closed": 0, "open": 0})
                s["closed"] += _cap[0]; s["open"] += _cap[1]
        Vs.append(V); Ts.append(T + off); Cs.append(C); off += len(V)
    if not Vs:
        if focus is None:
            raise ValueError("render: no triangle to draw and no focus to frame")
        Vs = [np.zeros((0, 3))]; Ts = [np.zeros((0, 3), int)]; Cs = [np.zeros((0, 3))]
        title = ("%s   [NOTHING OF THE SHAPE FALLS IN THIS WINDOW]" % title) if title else "NOTHING OF THE SHAPE FALLS IN THIS WINDOW"
    V = np.vstack(Vs); T = np.vstack(Ts); C = np.vstack(Cs)
    foc = V if focus is None else np.asarray(focus, float)
    fx = foc @ r3; fy = foc @ u3
    x0, x1 = fx.min() - pad, fx.max() + pad
    y0, y1 = fy.min() - pad, fy.max() + pad
    mmpx = (x1 - x0) / W
    if H is None:
        H = int(math.ceil((y1 - y0) / mmpx))
    else:
        cy = 0.5 * (y0 + y1); y0 = cy - 0.5 * H * mmpx; y1 = cy + 0.5 * H * mmpx
    X = (V @ r3 - x0) / mmpx
    Y = (y1 - V @ u3) / mmpx
    Z = V @ d3
    P = V[T]
    n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1; n = n / ln[:, None]
    if light is None:
        light = _n(-d3 + 0.5 * u3 + 0.35 * r3)
    elif isinstance(light, str):
        light = _n(-0.35 * d3 + 0.7 * u3 + 0.6 * r3) if light == "grazing" else _n(-d3 + 0.5 * u3 + 0.35 * r3)
    vn = np.zeros_like(V)
    np.add.at(vn, T[:, 0], n * ln[:, None]); np.add.at(vn, T[:, 1], n * ln[:, None]); np.add.at(vn, T[:, 2], n * ln[:, None])
    vl = np.linalg.norm(vn, axis=1); vl[vl == 0] = 1; vn = vn / vl[:, None]
    cn = vn[T]
    agree = np.einsum("mkj,mj->mk", cn, n) >= 0.866
    cn = np.where(agree[:, :, None], cn, n[:, None, :])
    zbuf = np.full((H, W), np.inf)
    img = np.empty((H, W, 3)); img[:] = bg
    nbuf = np.zeros((H, W, 3))
    own = np.full((H, W), -1, dtype=np.int64)
    if len(C):
        _cu, cid_t = np.unique(np.round(C, 3), axis=0, return_inverse=True)
        cid_t = cid_t.reshape(-1)
    else:
        cid_t = np.zeros(0, dtype=np.int64)
    cbuf = np.full((H, W), -1, dtype=np.int64)
    tx = X[T]; ty = Y[T]; tz = Z[T]
    xmin = np.floor(tx.min(1)).astype(int); xmax = np.ceil(tx.max(1)).astype(int)
    ymin = np.floor(ty.min(1)).astype(int); ymax = np.ceil(ty.max(1)).astype(int)
    onscreen = (xmax >= 0) & (xmin < W) & (ymax >= 0) & (ymin < H)
    idx = np.nonzero(onscreen)[0]
    for i in idx:
        ax, bx, cx = tx[i]; ay, by, cy = ty[i]
        det = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)
        if abs(det) < 1e-12:
            continue
        xa = max(xmin[i], 0); xb = min(xmax[i], W - 1)
        ya = max(ymin[i], 0); yb = min(ymax[i], H - 1)
        if xb < xa or yb < ya:
            continue
        gx = np.arange(xa, xb + 1) + 0.5
        gy = np.arange(ya, yb + 1) + 0.5
        px, py = np.meshgrid(gx, gy)
        w0 = ((bx - px) * (cy - py) - (cx - px) * (by - py)) / det
        w1 = ((cx - px) * (ay - py) - (ax - px) * (cy - py)) / det
        w2 = 1.0 - w0 - w1
        eps = -1e-3
        m = (w0 >= eps) & (w1 >= eps) & (w2 >= eps)
        if not m.any():
            cxp = int((ax + bx + cx) / 3); cyp = int((ay + by + cy) / 3)
            if 0 <= cxp < W and 0 <= cyp < H:
                zc = tz[i].mean()
                if zc < zbuf[cyp, cxp]:
                    sh = 0.35 + 0.65 * abs(float(n[i] @ light))
                    zbuf[cyp, cxp] = zc; img[cyp, cxp] = C[i] * sh; nbuf[cyp, cxp] = n[i]; own[cyp, cxp] = i
                    cbuf[cyp, cxp] = cid_t[i]
            continue
        zz = w0 * tz[i, 0] + w1 * tz[i, 1] + w2 * tz[i, 2]
        sub = zbuf[ya:yb + 1, xa:xb + 1]
        upd = m & (zz < sub)
        if not upd.any():
            continue
        sub[upd] = zz[upd]
        npx = (w0[..., None] * cn[i, 0] + w1[..., None] * cn[i, 1] + w2[..., None] * cn[i, 2])
        nl2 = np.linalg.norm(npx, axis=-1); nl2[nl2 == 0] = 1; npx = npx / nl2[..., None]
        sh = 0.35 + 0.65 * np.abs(npx @ light)
        img[ya:yb + 1, xa:xb + 1][upd] = (C[i][None, :] * sh[upd][:, None])
        nbuf[ya:yb + 1, xa:xb + 1][upd] = npx[upd]
        own[ya:yb + 1, xa:xb + 1][upd] = i
        cbuf[ya:yb + 1, xa:xb + 1][upd] = cid_t[i]
    if cap_loops and clip is not None:
        p0, nn = np.asarray(clip[0], float), _n(clip[1])
        dn = float(d3 @ nn)
        if abs(dn) > 1e-6:
            mask = np.zeros((H, W), bool)
            for pts, _cc in cap_loops:
                lx = (pts @ r3 - x0) / mmpx; ly = (y1 - pts @ u3) / mmpx
                mimg = Image.new("1", (W, H), 0)
                ImageDraw.Draw(mimg).polygon(list(zip(lx.tolist(), ly.tolist())), fill=1)
                mask ^= np.array(mimg, dtype=bool)
            if mask.any():
                yy, xx = np.nonzero(mask)
                wx = x0 + (xx + 0.5) * mmpx; wy = y1 - (yy + 0.5) * mmpx
                zc = (float(p0 @ nn) - wx * float(r3 @ nn) - wy * float(u3 @ nn)) / dn
                upd = zc < zbuf[yy, xx]
                sh = 0.35 + 0.65 * abs(float(nn @ light))
                capcol = cap_loops[0][1] * sh
                zbuf[yy[upd], xx[upd]] = zc[upd]
                img[yy[upd], xx[upd]] = capcol
                nbuf[yy[upd], xx[upd]] = nn
                own[yy[upd], xx[upd]] = -2
                cbuf[yy[upd], xx[upd]] = -2
    if stats is not None:
        vis = own[own >= 0]
        stats["drawn_px"] = int(len(vis))
        stats["own"] = own
        stats["tri_index"] = T
        stats["mmpx"] = float(mmpx)
        if subject_box is not None and len(vis):
            (sx0, sx1), (sy0, sy1), (sz0, sz1) = subject_box
            cen = P.mean(axis=1)
            inbox = ((cen[:, 0] >= sx0) & (cen[:, 0] <= sx1) & (cen[:, 1] >= sy0) & (cen[:, 1] <= sy1)
                     & (cen[:, 2] >= sz0) & (cen[:, 2] <= sz1))
            stats["subject_tris"] = int(inbox.sum())
            _jj, _ii = np.nonzero(np.isfinite(zbuf) & (own >= 0))
            _Pw = ((x0 + (_ii + 0.5) * mmpx)[:, None] * r3[None, :] + (y1 - (_jj + 0.5) * mmpx)[:, None] * u3[None, :] + zbuf[_jj, _ii][:, None] * d3[None, :])
            _tol = 0.05
            _pin = ((_Pw[:, 0] >= sx0 - _tol) & (_Pw[:, 0] <= sx1 + _tol) & (_Pw[:, 1] >= sy0 - _tol) & (_Pw[:, 1] <= sy1 + _tol) & (_Pw[:, 2] >= sz0 - _tol) & (_Pw[:, 2] <= sz1 + _tol))
            stats["subject_px"] = int(_pin.sum())
            stats["box_px"], stats["box_drawn_px"], stats["occluded_px"] = box_cover(zbuf, (sx0, sx1, sy0, sy1, sz0, sz1), d3, r3, u3, x0, y1, mmpx, W, H, cap_mask=(own == -2))
            seen = V[T[np.unique(vis)]].reshape(-1, 3)
            stats["shows"] = [[float(v) for v in seen.min(0)], [float(v) for v in seen.max(0)]]
        elif subject_box is not None:
            stats["subject_tris"] = 0; stats["subject_px"] = 0; stats["shows"] = None
            try:
                (sx0, sx1), (sy0, sy1), (sz0, sz1) = subject_box
                stats["box_px"], stats["box_drawn_px"], stats["occluded_px"] = box_cover(zbuf, (sx0, sx1, sy0, sy1, sz0, sz1), d3, r3, u3, x0, y1, mmpx, W, H, cap_mask=(own == -2))
            except Exception:
                stats["box_px"] = stats["box_drawn_px"] = stats["occluded_px"] = 0
    if edges:
        dot_x = (nbuf[:, 1:] * nbuf[:, :-1]).sum(-1); dot_y = (nbuf[1:, :] * nbuf[:-1, :]).sum(-1)
        fin_x = np.isfinite(zbuf[:, 1:]) & np.isfinite(zbuf[:, :-1]); fin_y = np.isfinite(zbuf[1:, :]) & np.isfinite(zbuf[:-1, :])
        with np.errstate(invalid="ignore"):
            jump_x = fin_x & (np.abs(zbuf[:, 1:] - zbuf[:, :-1]) > 1.5 * mmpx * 4); jump_y = fin_y & (np.abs(zbuf[1:, :] - zbuf[:-1, :]) > 1.5 * mmpx * 4)
        ex = (fin_x & (np.abs(dot_x) < 0.85)) | jump_x; ey = (fin_y & (np.abs(dot_y) < 0.85)) | jump_y
        line = np.zeros((H, W), bool); line[:, 1:] |= ex; line[1:, :] |= ey
        sil_x = np.isfinite(zbuf[:, 1:]) != np.isfinite(zbuf[:, :-1]); sil_y = np.isfinite(zbuf[1:, :]) != np.isfinite(zbuf[:-1, :])
        line[:, 1:] |= sil_x; line[1:, :] |= sil_y
        img[line] = img[line] * 0.35
        pb_x = fin_x & (cbuf[:, 1:] != cbuf[:, :-1]); pb_y = fin_y & (cbuf[1:, :] != cbuf[:-1, :])
        pb = np.zeros((H, W), bool); pb[:, 1:] |= pb_x; pb[1:, :] |= pb_y
        pb &= ~line
        img[pb] = img[pb] * 0.6
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    dr = ImageDraw.Draw(im)
    if title:
        # boundary edges
        _s = (stats or {}).get("cut") or {}
        if _s:
            _o, _c = int(_s.get("open", 0)), int(_s.get("closed", 0))
            title = "%s   [CUT %d capped, %d OPEN%s]" % (
                title.replace("   [CUT - capped]", ""), _c, _o,
                " - THE CUT FACE IS NOT SOLID, do not read thickness off it" if _o else "")
        dr.rectangle([0, 0, W, 18], fill=(0, 0, 0))
        dr.text((4, 3), "%s   [%s]" % (title, axes_label(r3, u3)), fill=(255, 255, 80))
    if scale_bar:
        _wmm = W * mmpx; _L = next((x_ for x_ in (100.0, 50.0, 20.0, 10.0, 5.0, 2.0, 1.0, 0.5) if x_ <= 0.4 * _wmm), 0.5)
        bar = _L / mmpx
        dr.line([10, H - 12, 10 + bar, H - 12], fill=(255, 255, 255), width=3)
        dr.text((12, H - 28), "%g mm  (%.2f mm/px)" % (_L, mmpx), fill=(255, 255, 255))
    im.save(path)
    index_frame(path, [foc[:, 0].min(), foc[:, 0].max(), foc[:, 1].min(), foc[:, 1].max(), foc[:, 2].min(), foc[:, 2].max()], d3, title)
    return mmpx


def section_segs(V, T, axis, c):
    """segments of the triangle mesh cut by plane axis=c. returns (k,2,3) array. 31bp fix 7: vectorised - the loop form (_section_segs_loop) took
    ~300 s over 16 stations of two 1.46 M-triangle meshes and the silence watchdog killed review-body; the same points, the same dedupe."""
    P = np.asarray(V, float)[np.asarray(T, int)]
    a = P[:, :, axis] - c
    s = np.sign(a)
    cross = ~((s[:, 0] == s[:, 1]) & (s[:, 1] == s[:, 2]))
    P = P[cross]; a = a[cross]
    if not len(P): return np.zeros((0, 2, 3))
    pts = np.zeros((len(P), 3, 3)); ok = np.zeros((len(P), 3), bool)
    for e_, (i, j) in enumerate(((0, 1), (1, 2), (2, 0))):
        ai, aj = a[:, i], a[:, j]
        m_ = (((ai < 0) != (aj < 0)) | (ai == 0) | (aj == 0)) & (ai != aj)
        den = np.where(ai != aj, ai - aj, 1.0); tt = ai / den
        m_ &= (tt >= 0.0) & (tt <= 1.0)
        pts[:, e_] = P[:, i] + tt[:, None] * (P[:, j] - P[:, i]); ok[:, e_] = m_
    n_ok = ok.sum(axis=1); keep = n_ok >= 2
    pts = pts[keep]; ok = ok[keep]; n_ok = n_ok[keep]
    if not len(pts): return np.zeros((0, 2, 3))
    order = np.argsort(~ok, axis=1, kind="stable")
    p0 = np.take_along_axis(pts, order[:, 0][:, None, None].repeat(3, 2), axis=1)[:, 0]
    p1 = np.take_along_axis(pts, order[:, 1][:, None, None].repeat(3, 2), axis=1)[:, 0]
    p2 = np.take_along_axis(pts, order[:, 2][:, None, None].repeat(3, 2), axis=1)[:, 0]
    three = n_ok == 3
    if three.any():
        d01 = np.linalg.norm(p0 - p1, axis=1)
        p1 = np.where((three & (d01 < 1e-9))[:, None], p2, p1)
    return np.stack([p0, p1], axis=1)


def _section_segs_loop(V, T, axis, c):
    """the loop form of section_segs (kept for the test: the vectorised one gives the same segments)"""
    P = V[T]
    a = P[:, :, axis] - c
    s = np.sign(a)
    cross = ~((s[:, 0] == s[:, 1]) & (s[:, 1] == s[:, 2]))
    P = P[cross]; a = a[cross]
    segs = []
    for tri, av in zip(P, a):
        pts = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            ai, aj = av[i], av[j]
            if (ai < 0) != (aj < 0) or ai == 0 or aj == 0:
                if ai == aj:
                    continue
                t = ai / (ai - aj)
                if 0.0 <= t <= 1.0:
                    pts.append(tri[i] + t * (tri[j] - tri[i]))
        if len(pts) >= 2:
            if len(pts) == 3:
                d01 = np.linalg.norm(pts[0] - pts[1]); d12 = np.linalg.norm(pts[1] - pts[2])
                d02 = np.linalg.norm(pts[0] - pts[2])
                if d01 < 1e-9: pts = [pts[0], pts[2]]
                elif d12 < 1e-9 or d02 < 1e-9: pts = [pts[0], pts[1]]
                else: pts = [pts[0], pts[1]]
            segs.append((pts[0], pts[1]))
    return np.array(segs) if segs else np.zeros((0, 2, 3))


def draw_section(path, segsets, axis, title, W=1400, pad=4.0, window=None, grid=10.0, polys=None,
                 hlines=None, vlines=None, texts=None):
    """segsets: list of (segs(k,2,3), rgb255, width). axis = the cut axis; the two other axes are
    drawn (u = first remaining, v = second remaining, v up).  window: ((u0,u1),(v0,v1)).
    polys: list of (pts(n,2) in (u,v), rgb255) outlines drawn on top."""
    from PIL import Image, ImageDraw
    ax_u, ax_v = [a for a in (0, 1, 2) if a != axis]
    allp = np.vstack([s.reshape(-1, 3) for s, _, _ in segsets if len(s)]) if any(len(s) for s, _, _ in segsets) else np.zeros((1, 3))
    if window is None:
        u0, u1 = allp[:, ax_u].min() - pad, allp[:, ax_u].max() + pad
        v0, v1 = allp[:, ax_v].min() - pad, allp[:, ax_v].max() + pad
    else:
        (u0, u1), (v0, v1) = window
    sc = W / (u1 - u0)
    H = int(math.ceil((v1 - v0) * sc)) + 24
    im = Image.new("RGB", (W, H), (20, 20, 24))
    dr = ImageDraw.Draw(im)

    def tp(u, v):
        return ((u - u0) * sc, (v1 - v) * sc + 24)
    if grid:
        g = math.ceil(u0 / grid) * grid
        while g <= u1:
            x, _ = tp(g, 0); dr.line([x, 24, x, H], fill=(45, 45, 52)); g += grid
        g = math.ceil(v0 / grid) * grid
        while g <= v1:
            _, y = tp(0, g); dr.line([0, y, W, y], fill=(45, 45, 52)); g += grid
    for segs, rgb, wd in segsets:
        for a, b in segs:
            dr.line([tp(a[ax_u], a[ax_v]), tp(b[ax_u], b[ax_v])], fill=rgb, width=wd)
    for h in (hlines or []):
        v, rgb = h; _, y = tp(0, v); dr.line([0, y, W, y], fill=rgb, width=1)
    for vv in (vlines or []):
        u, rgb = vv; x, _ = tp(u, 0); dr.line([x, 24, x, H], fill=rgb, width=1)
    for pts, rgb in (polys or []):
        pts = np.asarray(pts, float)
        pp = [tp(p[0], p[1]) for p in pts] + [tp(pts[0][0], pts[0][1])]
        dr.line(pp, fill=rgb, width=2)
    for t in (texts or []):
        u, v, s, rgb = t; dr.text(tp(u, v), s, fill=rgb)
    names = "xyz"
    dr.rectangle([0, 0, W, 22], fill=(0, 0, 0))
    dr.text((4, 4), "%s   [%s horizontal, %s up]  %.3f mm/px  grid %g" % (title, names[ax_u], names[ax_v], 1 / sc, grid), fill=(255, 255, 80))
    im.save(path)
    return 1 / sc


def match_segs(A, B, ax_u, ax_v, tol=0.1, n=5):
    """31bp fix 7b: which segments of A lie on the section B - every one of n sample points along the segment within tol of some segment of B, in the
    station's (u, v) plane; a boolean per segment of A. Exact point-to-segment distances, vectorised in blocks (a few hundred segments a station).
    Used by review-body's stations: a line both bodies share is drawn ONCE in its own colour (a 1 px new line on a 3 px old one read as either)."""
    A = np.asarray(A, float); B = np.asarray(B, float)
    if not len(A): return np.zeros(0, bool)
    if not len(B): return np.zeros(len(A), bool)
    tt = np.linspace(0.0, 1.0, n)[None, :, None]
    P = (A[:, None, 0, :] * (1.0 - tt) + A[:, None, 1, :] * tt)[:, :, [ax_u, ax_v]].reshape(-1, 2)
    S0 = B[:, 0, [ax_u, ax_v]]; D = B[:, 1, [ax_u, ax_v]] - S0; L2 = np.maximum((D * D).sum(1), 1e-18)
    best = np.full(len(P), np.inf)
    for i0 in range(0, len(P), 1000):
        Pi = P[i0:i0 + 1000]
        w = Pi[:, None, :] - S0[None, :, :]
        s = np.clip((w * D[None, :, :]).sum(2) / L2[None, :], 0.0, 1.0)
        best[i0:i0 + 1000] = np.linalg.norm(w - s[:, :, None] * D[None, :, :], axis=2).min(1)
    return (best.reshape(len(A), n) <= tol).all(1)


class ZRays(object):
    """cast +z / -z rays through a triangle mesh; returns hits sorted by z."""
    def __init__(self, V, T, cell=4.0):
        self.V = V; self.T = T
        P = V[T]
        self.P = P
        self.mn = P[:, :, :2].min(1); self.mx = P[:, :, :2].max(1)
        self.cell = cell
        self.o = self.mn.min(0) - 1e-6
        ij0 = np.floor((self.mn - self.o) / cell).astype(int)
        ij1 = np.floor((self.mx - self.o) / cell).astype(int)
        self.grid = {}
        for t in range(len(T)):
            for i in range(ij0[t, 0], ij1[t, 0] + 1):
                for j in range(ij0[t, 1], ij1[t, 1] + 1):
                    self.grid.setdefault((i, j), []).append(t)

    def hits(self, x, y):
        """all z where the vertical line (x,y) crosses the mesh, with triangle ids, ascending z."""
        i = int(np.floor((x - self.o[0]) / self.cell)); j = int(np.floor((y - self.o[1]) / self.cell))
        cand = self.grid.get((i, j))
        if not cand:
            return np.zeros(0), np.zeros(0, int)
        cand = np.array(cand)
        P = self.P[cand]
        ax, ay = P[:, 0, 0], P[:, 0, 1]; bx, by = P[:, 1, 0], P[:, 1, 1]; cx, cy = P[:, 2, 0], P[:, 2, 1]
        det = (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)
        ok = np.abs(det) > 1e-12
        det[~ok] = 1
        w0 = ((bx - x) * (cy - y) - (cx - x) * (by - y)) / det
        w1 = ((cx - x) * (ay - y) - (ax - x) * (cy - y)) / det
        w2 = 1 - w0 - w1
        m = ok & (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
        if not m.any():
            return np.zeros(0), np.zeros(0, int)
        z = w0[m] * P[m, 0, 2] + w1[m] * P[m, 1, 2] + w2[m] * P[m, 2, 2]
        o = np.argsort(z)
        return z[o], cand[m][o]

    def first_above(self, x, y, z0, gap=0.05):
        z, t = self.hits(x, y)
        m = z > z0 + gap
        if not m.any():
            return None, None
        return float(z[m][0]), int(t[m][0])

    def solid_runs(self, x, y):
        """pairs (z_enter, z_exit) assuming a closed mesh: consecutive crossings."""
        z, t = self.hits(x, y)
        zz = []
        for v in z:
            if zz and abs(v - zz[-1]) < 1e-6:
                continue
            zz.append(v)
        runs = [(zz[i], zz[i + 1]) for i in range(0, len(zz) - 1, 2)]
        return runs


def fill_mask(segs, ax_u, ax_v, u0, v1, sc, W, H, yoff=0):
    """even-odd scanline fill of closed section loops -> boolean mask (H,W)."""
    mask = np.zeros((H, W), bool)
    if len(segs) == 0:
        return mask
    A = segs[:, 0]; B = segs[:, 1]
    au = (A[:, ax_u] - u0) * sc; av = (v1 - A[:, ax_v]) * sc + yoff
    bu = (B[:, ax_u] - u0) * sc; bv = (v1 - B[:, ax_v]) * sc + yoff
    for row in range(H):
        y = row + 0.5
        m = ((av <= y) & (bv > y)) | ((bv <= y) & (av > y))
        if not m.any():
            continue
        t = (y - av[m]) / (bv[m] - av[m])
        xs = np.sort(au[m] + t * (bu[m] - au[m]))
        for k in range(0, len(xs) - 1, 2):
            a = int(max(0, np.floor(xs[k]))); b = int(min(W - 1, np.ceil(xs[k + 1])))
            if b >= a:
                mask[row, a:b + 1] = True
    return mask


def draw_section_filled(path, fills, segsets, axis, title, W=1400, pad=4.0, window=None, grid=10.0,
                        polys=None, hlines=None, vlines=None, texts=None, flip_u=False):
    """fills: list of (segs, rgb255) painted solid (even-odd); segsets outlines on top."""
    from PIL import Image, ImageDraw
    ax_u, ax_v = [a for a in (0, 1, 2) if a != axis]
    src = [s for s, _ in fills] + [s for s, _, _ in segsets]
    allp = np.vstack([s.reshape(-1, 3) for s in src if len(s)])
    if window is None:
        u0, u1 = allp[:, ax_u].min() - pad, allp[:, ax_u].max() + pad
        v0, v1 = allp[:, ax_v].min() - pad, allp[:, ax_v].max() + pad
    else:
        (u0, u1), (v0, v1) = window
    sc = W / (u1 - u0)
    H = int(math.ceil((v1 - v0) * sc))
    img = np.zeros((H + 24, W, 3), np.uint8); img[:] = (20, 20, 24)
    for segs, rgb in fills:
        mk = fill_mask(segs, ax_u, ax_v, u0, v1, sc, W, H)
        img[24:][mk] = rgb
    if flip_u:
        img = img[:, ::-1]
    im = Image.fromarray(img); dr = ImageDraw.Draw(im)

    def tp(u, v):
        x = (u - u0) * sc
        if flip_u: x = W - x
        return (x, (v1 - v) * sc + 24)
    if grid:
        g = math.ceil(u0 / grid) * grid
        while g <= u1:
            x, _ = tp(g, 0); dr.line([x, 24, x, H + 24], fill=(60, 60, 70)); dr.text((x + 2, 26), "%g" % g, fill=(150, 150, 160)); g += grid
        g = math.ceil(v0 / grid) * grid
        while g <= v1:
            _, y = tp(0, g); dr.line([0, y, W, y], fill=(60, 60, 70)); dr.text((2, y + 1), "%g" % g, fill=(150, 150, 160)); g += grid
    for segs, rgb, wd in segsets:
        for a, b in segs:
            dr.line([tp(a[ax_u], a[ax_v]), tp(b[ax_u], b[ax_v])], fill=rgb, width=wd)
    for h in (hlines or []):
        v, rgb = h; _, y = tp(0, v); dr.line([0, y, W, y], fill=rgb, width=1)
    for vv in (vlines or []):
        u, rgb = vv; x, _ = tp(u, 0); dr.line([x, 24, x, H + 24], fill=rgb, width=1)
    for pts, rgb in (polys or []):
        pts = np.asarray(pts, float)
        pp = [tp(p[0], p[1]) for p in pts] + [tp(pts[0][0], pts[0][1])]
        dr.line(pp, fill=rgb, width=2)
    for t in (texts or []):
        u, v, s, rgb = t; dr.text(tp(u, v), s, fill=rgb)
    names = "xyz"
    dr.rectangle([0, 0, W, 22], fill=(0, 0, 0))
    dr.text((4, 4), "%s   [%s horizontal%s, %s up]  %.3f mm/px  grid %g" % (title, names[ax_u], " (flipped)" if flip_u else "", names[ax_v], 1 / sc, grid), fill=(255, 255, 80))
    im.save(path)
    return 1 / sc


def point_tri_dist(P, V, T, cell=None):
    """Exact distance from each point in P to the nearest triangle of (V, T). numpy only.

    WHY EXACT AND NOT NEAREST-VERTEX. A stitch is judged on whether two SURFACES agree along a band.
    Nearest-vertex distance overstates that wherever one side is coarsely tessellated — a flat patch
    with metre-long triangles has vertices far from a point that lies exactly on it — so a band that
    is in perfect agreement can be refused for being coarse. That would push the orchestrator towards
    the dense, busy part of the model, which is the opposite of the advice.

    Triangles are bucketed into a uniform grid by their bounding boxes and each point is tested
    against the triangles of its own cell, widening the ring until the best distance found is smaller
    than the ring's own lower bound. Points are expected to be a band, not a whole body.
    """
    P = np.asarray(P, float).reshape(-1, 3)
    V = np.asarray(V, float); T = np.asarray(T, int)
    if len(P) == 0 or len(T) == 0:
        return np.zeros(len(P))
    lo = V[T].min(axis=1); hi = V[T].max(axis=1)
    if cell is None:
        cell = max(float(np.median(hi - lo).max()), 1e-6) * 2.0
    org = np.minimum(lo.min(0), P.min(0)) - cell
    buckets = {}
    i0 = np.floor((lo - org) / cell).astype(int); i1 = np.floor((hi - org) / cell).astype(int)
    for t in range(len(T)):
        for a in range(i0[t, 0], i1[t, 0] + 1):
            for b in range(i0[t, 1], i1[t, 1] + 1):
                for c in range(i0[t, 2], i1[t, 2] + 1):
                    buckets.setdefault((a, b, c), []).append(t)
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]

    def _d(p, idx):
        a, b, c = A[idx], B[idx], C[idx]
        ab, ac, ap = b - a, c - a, p - a
        d1 = (ab * ap).sum(1); d2 = (ac * ap).sum(1)
        bp = p - b; d3 = (ab * bp).sum(1); d4 = (ac * bp).sum(1)
        cp = p - c; d5 = (ab * cp).sum(1); d6 = (ac * cp).sum(1)
        vc = d1 * d4 - d3 * d2; vb = d5 * d2 - d1 * d6; va = d3 * d6 - d5 * d4
        den = va + vb + vc
        den = np.where(np.abs(den) < 1e-30, 1e-30, den)
        v = vb / den; w = vc / den
        m = (d1 <= 0) & (d2 <= 0); v = np.where(m, 0.0, v); w = np.where(m, 0.0, w)
        m = (d3 >= 0) & (d4 <= d3); v = np.where(m, 1.0, v); w = np.where(m, 0.0, w)
        m = (d6 >= 0) & (d5 <= d6); v = np.where(m, 0.0, v); w = np.where(m, 1.0, w)
        m = (vc <= 0) & (d1 >= 0) & (d3 <= 0)
        v = np.where(m, np.clip(d1 / np.where(d1 - d3 == 0, 1e-30, d1 - d3), 0, 1), v); w = np.where(m, 0.0, w)
        m = (vb <= 0) & (d2 >= 0) & (d6 <= 0)
        w = np.where(m, np.clip(d2 / np.where(d2 - d6 == 0, 1e-30, d2 - d6), 0, 1), w); v = np.where(m, 0.0, v)
        m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0)
        t2 = np.clip((d4 - d3) / np.where((d4 - d3) + (d5 - d6) == 0, 1e-30, (d4 - d3) + (d5 - d6)), 0, 1)
        v = np.where(m, 1.0 - t2, v); w = np.where(m, t2, w)
        q = a + v[:, None] * ab + w[:, None] * ac
        return np.linalg.norm(p - q, axis=1)

    out = np.full(len(P), np.inf)
    keys = np.floor((P - org) / cell).astype(int)
    for i in range(len(P)):
        best, r = np.inf, 0
        while True:
            idx = []
            k = keys[i]
            for a in range(k[0] - r, k[0] + r + 1):
                for b in range(k[1] - r, k[1] + r + 1):
                    for c in range(k[2] - r, k[2] + r + 1):
                        if r == 0 or max(abs(a - k[0]), abs(b - k[1]), abs(c - k[2])) == r:
                            idx.extend(buckets.get((a, b, c), ()))
            if idx:
                best = min(best, float(_d(P[i], np.asarray(idx, int)).min()))
            if best <= r * cell or r > 64:
                break
            r += 1
        out[i] = best
    return out

def read_stl(path):
    with open(path, "rb") as fh:
        head = fh.read(84)
        if len(head) < 84:
            raise SystemExit("%s is too short to be an STL" % path)
        n = int(np.frombuffer(head[80:84], "<u4")[0])
        body = fh.read()
    if n and len(body) >= n * 50:
        rec = np.frombuffer(body[:n * 50], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)),
                                                           ("a", "<u2")]), count=n)
        V = rec["v"].reshape(-1, 3).astype(np.float32)
        T = np.arange(len(V), dtype=np.int32).reshape(-1, 3)
        return V, T
    txt = open(path, "r", errors="replace").read()
    pts = [tuple(float(x) for x in ln.split()[1:4])
           for ln in txt.splitlines() if ln.strip().lower().startswith("vertex")]
    if not pts or len(pts) % 3:
        raise SystemExit("%s is neither a readable binary nor ASCII STL" % path)
    V = np.asarray(pts, np.float32)
    return V, np.arange(len(V), dtype=np.int32).reshape(-1, 3)


def load_mesh_parts(paths):
    """one or more STLs, concatenated into a single (V, T). Vertices are NOT welded: the cache is for
    rendering, and welding here would change what the picture is of."""
    Vs, Ts, off = [], [], 0
    for p in paths:
        V, T = read_stl(p)
        Vs.append(V)
        Ts.append(T + off)
        off += len(V)
    return np.vstack(Vs), np.vstack(Ts)


def slab_samples(V, T, axis, lo, hi, box=None):
    """Points ON THE SURFACE inside an axis-aligned slab, whatever the tessellation density.

    WHY NOT JUST THE VERTICES IN THE SLAB. A seam band is thin by rule — at most a few tenths of a
    millimetre — and a coarsely tessellated patch can pass straight through one without putting a
    single VERTEX in it. Sampling vertices would then report "nothing here" for a surface that is
    plainly there, and the thinner the band the more often it happens. That is the same class of
    error as measuring a surface by its nearest vertex: an artefact of how the mesh was cut up,
    reported as a fact about the part.

    So each triangle that reaches the slab is CLIPPED to it (a convex polygon, Sutherland–Hodgman
    against the two half-spaces and, if `box` is given, against its other four faces) and the
    polygon's corners and centroid are the samples. Curvature is irrelevant: a slab meets a curved
    surface in a curved ribbon and the clip follows it. The only surface this returns nothing for is
    one that does not enter the slab at all.
    """
    V = np.asarray(V, float); T = np.asarray(T, int)
    ax = int(axis)
    planes = [(ax, 1.0, float(lo)), (ax, -1.0, -float(hi))]
    if box is not None:
        for k in range(3):
            if k == ax:
                continue
            planes += [(k, 1.0, float(box[2 * k])), (k, -1.0, -float(box[2 * k + 1]))]
    lo3 = np.array([box[0], box[2], box[4]], float) if box is not None else None
    hi3 = np.array([box[1], box[3], box[5]], float) if box is not None else None
    tl = V[T].min(axis=1); th = V[T].max(axis=1)
    cand = (th[:, ax] >= lo) & (tl[:, ax] <= hi)
    if box is not None:
        cand &= np.all(th >= lo3, axis=1) & np.all(tl <= hi3, axis=1)
    out = []
    for t in np.nonzero(cand)[0]:
        poly = [V[T[t, 0]], V[T[t, 1]], V[T[t, 2]]]
        for k, sgn, off in planes:
            if not poly:
                break
            nxt = []
            n = len(poly)
            for i in range(n):
                a, b = poly[i], poly[(i + 1) % n]
                da, db = sgn * a[k] - off, sgn * b[k] - off
                if da >= 0:
                    nxt.append(a)
                if (da > 0) != (db > 0) and (da - db) != 0:
                    nxt.append(a + (b - a) * (da / (da - db)))
            poly = nxt
        if len(poly) >= 2:
            P = np.asarray(poly, float)
            out.append(P)
            out.append(P.mean(axis=0)[None, :])
    if not out:
        return np.zeros((0, 3))
    return np.unique(np.round(np.vstack(out), 9), axis=0)


def split_at_plane(V, T, p0, n, keep=+1.0, eps=1e-9):
    """Keep the part of (V, T) on one side of a plane. Returns (V2, T2, rim) — rim is the list of
    edges (index pairs into V2) created ON the plane, each used by exactly one kept triangle.

    Straddling triangles are CLIPPED, not dropped and not kept whole: the polygon on the kept side
    is fan-triangulated and the two new points become a rim edge. Nothing on the kept side moves.
    """
    V = np.asarray(V, float); T = np.asarray(T, int)
    p0 = np.asarray(p0, float); n = _n(n) * (1.0 if keep >= 0 else -1.0)
    d = (V - p0) @ n
    out_V = [V]
    new_V = []
    out_T = []
    rim = []
    base = len(V)

    def _pt(p):
        new_V.append(p)
        return base + len(new_V) - 1

    for t in T:
        dd = d[t]
        if np.all(dd >= -eps):
            out_T.append(list(t)); continue
        if np.all(dd <= eps):
            continue
        poly, cut = [], []
        for i in range(3):
            a, b = t[i], t[(i + 1) % 3]
            da, db = dd[i], dd[(i + 1) % 3]
            if da >= -eps:
                poly.append(int(a))
            if (da > eps and db < -eps) or (da < -eps and db > eps):
                w = da / (da - db)
                q = V[a] + (V[b] - V[a]) * w
                k = _pt(q)
                poly.append(k); cut.append(k)
        if len(poly) < 3:
            continue
        for i in range(1, len(poly) - 1):
            out_T.append([poly[0], poly[i], poly[i + 1]])
        if len(cut) == 2:
            rim.append((cut[0], cut[1]))
    if new_V:
        out_V.append(np.asarray(new_V, float))
    V2 = np.vstack(out_V)
    T2 = np.asarray(out_T, int).reshape(-1, 3)
    rim = []
    if len(T2):
        e = np.vstack([T2[:, [0, 1]], T2[:, [1, 2]], T2[:, [2, 0]]])
        es = np.sort(e, axis=1)
        uniq, cnt = np.unique(es, axis=0, return_counts=True)
        on = np.abs((V2 - p0) @ n) <= 1e-6 * max(1.0, float(np.abs(V2).max()))
        for (a, b), c in zip(uniq, cnt):
            if c == 1 and on[a] and on[b]:
                rim.append((int(a), int(b)))
    return V2, T2, rim


def _weld(V, T, rim, tol):
    """Merge coincident vertices (within tol) and re-index T and rim. Returns (V, T, rim, remap)."""
    key = np.round(np.asarray(V, float) / max(tol, 1e-12)).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    inv = np.asarray(inv).reshape(-1)
    Vw = np.asarray(V, float)[first]
    order = np.argsort(first)
    pos = np.empty(len(first), int); pos[order] = np.arange(len(first))
    inv = pos[inv]
    Vw = Vw[order]
    Tw = inv[np.asarray(T, int)]
    Tw = Tw[(Tw[:, 0] != Tw[:, 1]) & (Tw[:, 1] != Tw[:, 2]) & (Tw[:, 0] != Tw[:, 2])]
    rw = [(int(inv[a]), int(inv[b])) for a, b in rim]
    rw = [e for e in rw if e[0] != e[1]]
    return Vw, Tw, rw, inv


def _refine_rim(V, T, rim, jobs, tol, skip=None):
    """Insert each point of `pts` into the rim edge it lies on, splitting that edge's triangle.

    THIS IS THE STEP, AND THE ONE THAT IS EASY TO GET WRONG. The seam's vertices are NOT free to
    move: they ARE this mesh's boundary, and the other side will be stitched to them by identity.
    So a point is added by SPLITTING an existing rim edge at the point's own projection — the new
    vertex is shared with the triangle that owned the edge, and no edge is orphaned. Resampling the
    loop to a common spacing does the arithmetically similar thing and multiplies open edges by an
    order of magnitude, because new points coincide with nothing (measured, 2026-09-21).
    """
    V = list(np.asarray(V, float)); T = [list(t) for t in np.asarray(T, int)]
    rim = [tuple(e) for e in rim]
    owner = {}
    for ti, t in enumerate(T):
        for i in range(3):
            owner[(t[i], t[(i + 1) % 3])] = ti
            owner[(t[(i + 1) % 3], t[i])] = ti
    for p, allowed in jobs:
        p = np.asarray(p, float)
        best, bi, bw = None, -1, 0.0
        for k in (allowed if allowed is not None else range(len(rim))):
            if k >= len(rim):
                continue
            a, b = rim[k]
            A, B = V[a], V[b]
            ab = B - A
            L2 = float(ab @ ab)
            if L2 <= 0:
                continue
            w = float(np.clip((p - A) @ ab / L2, 0.0, 1.0))
            q = A + ab * w
            dq = float(np.linalg.norm(p - q))
            if best is None or dq < best:
                best, bi, bw = dq, k, w
        if bi < 0 or best is None or best > tol:
            continue
        a, b = rim[bi]
        A, B = V[a], V[b]
        q = A + (B - A) * bw
        if min(np.linalg.norm(q - A), np.linalg.norm(q - B)) <= (tol * 0.5 if skip is None else skip):
            continue
        ti = owner.get((a, b))
        if ti is None:
            continue
        m = len(V); V.append(q)
        t = T[ti]
        i = t.index(a) if a in t else None
        if i is None or b not in t:
            continue
        j = t.index(b); c = [x for x in t if x != a and x != b]
        if not c:
            continue
        c = c[0]
        T[ti] = [a, m, c] if (t.index(b) - t.index(a)) % 3 == 1 else [m, a, c]
        T.append([m, b, c] if (t.index(b) - t.index(a)) % 3 == 1 else [b, m, c])
        for e in ((a, m), (m, a), (m, b), (b, m), (a, c), (c, a), (m, c), (c, m), (b, c), (c, b)):
            owner.setdefault(e, ti)
        owner[(m, b)] = owner[(b, m)] = len(T) - 1
        rim[bi] = (a, m); rim.append((m, b))
        if allowed is not None:
            allowed.append(len(rim) - 1)
    return np.asarray(V, float), np.asarray(T, int).reshape(-1, 3), rim


def stitch_on_plane(VA, TA, VB, TB, p0, n, tol=0.15):
    """ROUTE C on a PLANE - the degenerate case of `stitch_on_field`, kept as a named shorthand.

    ONE IMPLEMENTATION, NOT TWO. The plane version was written first and the field version generalised
    it; leaving both as separate code meant a fix to one silently missed the other, which is how the
    seam-closure check ended up in one of them and not the other. It delegates.
    """
    return stitch_on_field(VA, TA, VB, TB, sd_plane(p0, n), tol=tol)


def mesh_health(V, T):
    """(boundary_edges, non_manifold_edges) on the WELDED mesh. The two numbers a seam is read by."""
    T = np.asarray(T, int)
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    e = np.sort(e, axis=1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    return int((cnt == 1).sum()), int((cnt > 2).sum())


def write_stl(path, V, T):
    """Binary STL. The counterpart of read_stl, and the only writer the kit needs."""
    import struct
    V = np.asarray(V, float); T = np.asarray(T, int)
    P = V[T]
    n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1.0
    n = n / ln[:, None]
    with open(path, "wb") as fh:
        fh.write(b"\0" * 80)
        fh.write(struct.pack("<I", len(T)))
        rec = np.zeros(len(T), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
        rec["n"] = n.astype("<f4"); rec["v"] = P.astype("<f4")
        fh.write(rec.tobytes())


def sd_plane(p0, n):
    """Signed distance to a plane. Negative on the -n side."""
    p0 = np.asarray(p0, float); n = _n(n)
    return lambda P: (np.asarray(P, float).reshape(-1, 3) - p0) @ n


def sd_box(bx):
    """EXACT signed distance to an axis-aligned box. Negative INSIDE.

    The box is the boundary an orchestrator actually wants: "A inside this, B outside", with the
    seam running round the box including ITS CORNERS. A plane cannot express that.
    """
    lo = np.array([bx[0], bx[2], bx[4]], float)
    hi = np.array([bx[1], bx[3], bx[5]], float)
    c = 0.5 * (lo + hi); h = 0.5 * (hi - lo)

    def f(P):
        q = np.abs(np.asarray(P, float).reshape(-1, 3) - c) - h
        outside = np.linalg.norm(np.maximum(q, 0.0), axis=1)
        inside = np.minimum(q.max(axis=1), 0.0)
        return outside + inside
    return f


def _cross(fn, A, B, iters=60):
    """The point on segment A-B where fn changes sign, by BISECTION.

    Linear interpolation of the field is exact for a plane and WRONG for anything with a crease -
    a box corner, a fillet radius, any distance field - and wrong quietly, by a fraction of the
    edge. Bisection converges on the real crossing for ANY continuous field, which is what lets the
    boundary be a shape instead of a plane.
    """
    a, b = np.asarray(A, float), np.asarray(B, float)
    fa = float(fn(a[None, :])[0])
    for _ in range(iters):
        m = 0.5 * (a + b)
        fm = float(fn(m[None, :])[0])
        if (fm < 0) == (fa < 0):
            a, fa = m, fm
        else:
            b = m
    return 0.5 * (a + b)


def split_at_field(V, T, fn, keep_negative=True, eps=1e-9, max_split=7):
    """Keep the part of (V, T) where `fn` has the kept sign. Returns (V2, T2, rim).

    GEOMETRICALLY INDEPENDENT: `fn` is any continuous scalar field over space, so the boundary can
    be a plane, a box with corners, a cylinder, or a distance field taken from another surface. The
    only thing the splitter needs is the sign and a bisection.

    A triangle whose EDGE crosses the boundary more than once - a corner clipping a long triangle,
    say - cannot be cut by one straight line, so it is SUBDIVIDED at its longest edge and its parts
    re-tried, up to `max_split` levels. What cannot be resolved is REPORTED, never silently cut
    wrong: the count comes back in the rim as an "unresolved" tally on the function's attribute.
    """
    V = np.asarray(V, float); T = np.asarray(T, int)
    sgn = -1.0 if keep_negative else 1.0
    verts = [V]
    newV = []
    base = len(V)
    out_T = []
    unresolved = 0

    def _pt(p):
        newV.append(p)
        return base + len(newV) - 1

    def _f(pts):
        return sgn * np.asarray(fn(np.asarray(pts, float).reshape(-1, 3)), float)

    def _pos(i):
        return V[i] if i < base else newV[i - base]

    work = [tuple(int(x) for x in t) for t in T]
    depth = {}
    while work:
        t = work.pop()
        P = np.array([_pos(t[0]), _pos(t[1]), _pos(t[2])], float)
        d = _f(P)
        if np.all(d >= -eps):
            out_T.append(list(t)); continue
        if np.all(d <= eps):
            continue
        cuts = {}
        bad = False
        for i in range(3):
            a, b = t[i], t[(i + 1) % 3]
            Pa, Pb = _pos(a), _pos(b)
            ts = np.linspace(0.0, 1.0, 17)
            s = _f(Pa[None, :] + (Pb - Pa)[None, :] * ts[:, None])
            flips = int(np.sum((s[:-1] < 0) != (s[1:] < 0)))
            if flips > 1:
                bad = True; break
            if flips == 1:
                cuts[i] = _cross(lambda X: sgn * np.asarray(fn(X), float), Pa, Pb)
        # open edges
        if not bad and len(cuts) == 2:
            q = list(cuts.values())
            chord = 0.5 * (q[0] + q[1])
            scale = max(float(np.max(np.linalg.norm(P - P[[1, 2, 0]], axis=1))), 1e-12)
            if abs(float(_f(chord[None, :])[0])) > 0.02 * scale:
                bad = True
        if bad or len(cuts) != 2:
            dep = depth.get(t, 0)
            if dep >= max_split:
                unresolved += 1
                if np.sum(d >= -eps) >= 2:
                    out_T.append(list(t))
                continue
            L = [float(np.linalg.norm(P[(i + 1) % 3] - P[i])) for i in range(3)]
            i = int(np.argmax(L)); a, b, c = t[i], t[(i + 1) % 3], t[(i + 2) % 3]
            m = _pt(0.5 * (_pos(a) + _pos(b)))
            for nt in ((a, m, c), (m, b, c)):
                depth[nt] = dep + 1
                work.append(nt)
            continue
        poly = []
        for i in range(3):
            a = t[i]
            if d[i] >= -eps:
                poly.append(int(a))
            if i in cuts:
                poly.append(_pt(cuts[i]))
        if len(poly) < 3:
            continue
        for i in range(1, len(poly) - 1):
            out_T.append([poly[0], poly[i], poly[i + 1]])
    if newV:
        verts.append(np.asarray(newV, float))
    V2 = np.vstack(verts)
    T2 = np.asarray(out_T, int).reshape(-1, 3)
    # open edges
    # boundary edges  recorded
    own = set()
    # boundary edges
    Vin, Tin, _o, _i = _weld(np.asarray(V, float), np.asarray(T, int), [], 1e-6)
    if len(Tin):
        ei = np.sort(np.vstack([Tin[:, [0, 1]], Tin[:, [1, 2]], Tin[:, [2, 0]]]), axis=1)
        ui, ci = np.unique(ei, axis=0, return_counts=True)
        for (a, b) in ui[ci == 1]:
            pa = tuple(np.round(Vin[a], 6)); pb = tuple(np.round(Vin[b], 6))
            own.add((pa, pb) if pa <= pb else (pb, pa))
    rim = []
    if len(T2):
        e = np.vstack([T2[:, [0, 1]], T2[:, [1, 2]], T2[:, [2, 0]]])
        uniq, cnt = np.unique(np.sort(e, axis=1), axis=0, return_counts=True)
        fv = np.abs(np.asarray(fn(V2), float))
        scale = max(1.0, float(np.abs(V2).max()))
        on = fv <= 1e-6 * scale
        for (a, b), c in zip(uniq, cnt):
            if c != 1 or not (on[a] and on[b]):
                continue
            pa = tuple(np.round(V2[a], 6)); pb = tuple(np.round(V2[b], 6))
            if ((pa, pb) if pa <= pb else (pb, pa)) in own:
                continue
            rim.append((int(a), int(b)))
    return V2, T2, rim, unresolved


def rim_loops(rim):
    """Split a rim (a list of edges) into its separate LOOPS, each a connected vertex set.

    THIS IS THE DIFFERENCE BETWEEN A TEST PART AND A REAL ONE. On a cylinder a boundary crosses the
    surface in ONE loop, and a rim can then be treated as a bag of points. On a part with ribs, vanes
    and openings the same boundary crosses it in MANY loops - measured on this part: one build's
    rim came out in 10 loops and the other's in 8 - and a bag-of-points match then pairs a vertex on
    a small loop in one build with a point on a different FEATURE in the other, which is how a rim
    mismatch of tens of millimetres appears on two surfaces that agree to a few hundredths. Loops are
    matched to LOOPS, or the stitch refuses and says how many had no partner.
    """
    adj = {}
    for a, b in rim:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    seen, out = set(), []
    for start in adj:
        if start in seen:
            continue
        comp, stack = [], [start]
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u); comp.append(u)
            for v in adj[u]:
                if v not in seen:
                    stack.append(v)
        if len(comp) >= 2:
            out.append(comp)
    return out


def _assign(cost, cap):
    """Minimum-cost one-to-one assignment (Hungarian), with pairs over `cap` left unassigned.

    GREEDY IS NOT GOOD ENOUGH HERE and the failure is silent. Taking the cheapest pair first lets an
    early match steal the only sensible partner of a later loop, which then reports as "no partner"
    and stops the stitch - measured on a real part, 11 of 14 loops paired greedily where an
    optimal assignment pairs more, and four of the three "unmatched" loops had a partner that was
    simply taken first. A loop count is small (tens), so the exact algorithm is free.
    """
    C = np.array(cost, float)
    n, m = C.shape
    k = max(n, m)
    BIG = float(C[np.isfinite(C)].max() if np.isfinite(C).any() else 1.0) * 10.0 + 1.0
    P = np.full((k, k), BIG)
    P[:n, :m] = np.where(C <= cap, C, BIG)
    u = np.zeros(k + 1); v = np.zeros(k + 1); p = np.zeros(k + 1, int); way = np.zeros(k + 1, int)
    for i in range(1, k + 1):
        p[0] = i; j0 = 0
        minv = np.full(k + 1, np.inf); used = np.zeros(k + 1, bool)
        while True:
            used[j0] = True; i0 = p[j0]; delta = np.inf; j1 = 0
            for j in range(1, k + 1):
                if used[j]:
                    continue
                cur = P[i0 - 1, j - 1] - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j] = cur; way[j] = j0
                if minv[j] < delta:
                    delta = minv[j]; j1 = j
            for j in range(k + 1):
                if used[j]:
                    u[p[j]] += delta; v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]; p[j0] = p[j1]; j0 = j1
            if j0 == 0:
                break
    out = []
    for j in range(1, k + 1):
        i = p[j] - 1; jj = j - 1
        if 0 <= i < n and jj < m and C[i, jj] <= cap[i, jj]:
            out.append((i, jj))
    return out


def stitch_on_field(VA, TA, VB, TB, fn, tol=0.15):
    """ROUTE C on ANY boundary. A's surface where `fn` < 0, B's where `fn` > 0, joined into one mesh.

    LOOP BY LOOP, never as a bag of points - `rim_loops` says why that is the whole difference
    between a test cylinder and a part with ribs on it.
    """
    VA2, TA2, rimA, uA = split_at_field(VA, TA, fn, keep_negative=True)
    VB2, TB2, rimB, uB = split_at_field(VB, TB, fn, keep_negative=False)
    VA2, TA2, rimA, _ = _weld(VA2, TA2, rimA, tol * 1e-3)
    VB2, TB2, rimB, _ = _weld(VB2, TB2, rimB, tol * 1e-3)
    V, T, rep2 = weld_rims(VA2, TA2, rimA, VB2, TB2, rimB, tol=tol, uA=uA, uB=uB,
                           health_in=(VA, TA, VB, TB))
    return V, T, rep2


def weld_rims(VA2, TA2, rimA, VB2, TB2, rimB, tol=0.15, uA=0, uB=0, health_in=None,
              require_all_paired=True):
    """JOIN TWO ALREADY-OPEN MESHES ALONG THEIR RIMS, by refinement and identity. No zipper.

    THIS IS THE LEVER ROUTE A'S RATIO GATE DOES NOT HAVE. That gate says "keep the two loops' point
    counts within about 3:1 or the zip will fan", and nothing in the weld can change a point count:
    the decimator runs with `BoundaryVertexDeletionOff` and the smoother with `BoundarySmoothingOff`,
    both on purpose, so the rim survives untouched. The only lever that moved a count was a RESAMPLE,
    which multiplies open edges by an order of magnitude because the seam vertices are not free to
    move - they ARE the two boundaries, stitched by exact vertex identity, so new points coincide
    with nothing and orphan every original edge.

    **Refinement is the lever.** Each side's rim is refined IN THE MESH by the other side's points:
    every added vertex SPLITS an existing rim edge and is shared with the triangle that owned it, so
    nothing is orphaned and the counts come to correspond. The two rims are then welded one-to-one,
    meeting in the middle. **The seam costs NO ribbon triangles at all**, so the ratio it was gated on
    stops mattering: measured across rims of 192 and 24 edges, an 8:1 fan case, the sparse rim refined
    to 192 and the seam contributed 0 boundary and 0 non-manifold edges.

    Route C calls this after splitting two builds at a field. Route A calls it on the body-with-a-hole
    and the patch it means to put in the hole. Same operation, one implementation.
    """
    LA, LB = rim_loops(rimA), rim_loops(rimB)
    _speck = [("A", len(c)) for c in LA if len(c) < 3] + [("B", len(c)) for c in LB if len(c) < 3]
    LA = [c for c in LA if len(c) >= 3]; LB = [c for c in LB if len(c) >= 3]
    rep = {"rimA_edges0": len(rimA), "rimB_edges0": len(rimB),
           "triA": int(len(TA2)), "triB": int(len(TB2)),
           "loopsA": len(LA), "loopsB": len(LB), "unresolved": int(uA + uB),
           "specks_ignored": len(_speck), "speck_sizes": [n for _s, n in _speck]}
    if not rimA or not rimB:
        rep["error"] = "one side has no rim on this boundary - the boundary does not cross both meshes"
        return None, None, rep

    def _info(V, L):
        out = []
        for c in L:
            P = V[np.asarray(c, int)]
            out.append((P.mean(axis=0), float(np.ptp(P, axis=0).max()), len(c)))
        return out
    IA, IB = _info(VA2, LA), _info(VB2, LB)
    cost = np.zeros((len(LA), len(LB)))
    for a in range(len(LA)):
        for b in range(len(LB)):
            cost[a, b] = (float(np.linalg.norm(IA[a][0] - IB[b][0]))
                          + 0.25 * abs(IA[a][1] - IB[b][1]))
    cap = np.zeros_like(cost)
    for a in range(len(LA)):
        for b in range(len(LB)):
            cap[a, b] = 0.5 * max(IA[a][1], IB[b][1]) + tol
    pairs = _assign(cost, cap)
    usedA = {a for a, _b in pairs}; usedB = {b for _a, b in pairs}
    rep["loops_paired"] = len(pairs)
    # UNPAIRED
    # open edges
    _orph_A = [a for a in range(len(LA)) if a not in usedA]
    _orph_B = [b for b in range(len(LB)) if b not in usedB]
    near_A, near_B = [], []
    for a in _orph_A:
        for b in _orph_B:
            if float(np.linalg.norm(IA[a][0] - IB[b][0])) <= cap[a, b] * 3.0:
                near_A.append(a); near_B.append(b)
    near_A = sorted(set(near_A)); near_B = sorted(set(near_B))
    far_A = [a for a in _orph_A if a not in near_A]
    far_B = [b for b in _orph_B if b not in near_B]
    rep["loops_unrelated"] = len(far_A) + len(far_B)
    rep["loops_mismatched"] = len(near_A) + len(near_B)
    lost = ([len(LA[a]) for a in (_orph_A if require_all_paired else near_A)]
            + [len(LB[b]) for b in (_orph_B if require_all_paired else near_B)])
    if lost:
        rep["error"] = (
            "the two builds cross this boundary with DIFFERENT TOPOLOGY: %d loop(s) on one side, %d "
            "on the other, %d of them with no partner (%s vertices). That is not a tessellation "
            "difference and no vertex matching repairs it - the boundary passes through a feature one "
            "build has and the other does not, or one that decimation moved. Move the boundary onto "
            "surface both builds cross the same way."
            % (len(LA), len(LB), len(lost), ", ".join(str(n) for n in sorted(lost, reverse=True)[:8])))
        return None, None, rep

    eidxA, eidxB = {}, {}
    for k, e in enumerate(rimA):
        eidxA.setdefault(e[0], []).append(k); eidxA.setdefault(e[1], []).append(k)
    for k, e in enumerate(rimB):
        eidxB.setdefault(e[0], []).append(k); eidxB.setdefault(e[1], []).append(k)
    jobsA, jobsB = [], []
    _eaAll, _ebAll = [], []
    for a, b in pairs:
        ea = sorted({k for v in LA[a] for k in eidxA.get(v, ())})
        eb = sorted({k for v in LB[b] for k in eidxB.get(v, ())})
        _eaAll.append(ea); _ebAll.append(eb)
        for v in LB[b]:
            jobsA.append((VB2[v], ea))
        for v in LA[a]:
            jobsB.append((VA2[v], eb))
    VA2, TA2, rimA = _refine_rim(VA2, TA2, rimA, jobsA, tol, skip=tol * 0.02)
    VB2, TB2, rimB = _refine_rim(VB2, TB2, rimB, jobsB, tol, skip=tol * 0.02)
    rep["rimA_edges"] = len(rimA); rep["rimB_edges"] = len(rimB)

    _payA = {i for ea in _eaAll for k in ea if k < len(rimA) for i in rimA[k]}
    _payB = {i for eb in _ebAll for k in eb if k < len(rimB) for i in rimB[k]}
    idxA = sorted(_payA or {i for e in rimA for i in e})
    idxB = sorted(_payB or {i for e in rimB for i in e})
    PA, PB = VA2[idxA], VB2[idxB]
    dm = np.linalg.norm(PB[:, None, :] - PA[None, :, :], axis=2)
    order = np.dstack(np.unravel_index(np.argsort(dm, axis=None), dm.shape))[0]
    pb = np.full(len(PB), -1, int); usedAv = np.zeros(len(PA), bool)
    for bi, ai in order:
        if dm[bi, ai] > tol:
            break
        if pb[bi] < 0 and not usedAv[ai]:
            pb[bi] = ai; usedAv[ai] = True
    rep["unpaired_B"] = int((pb < 0).sum()); rep["unpaired_A"] = int((~usedAv).sum())
    ok = pb >= 0
    rep["worst_mm"] = float(dm[np.nonzero(ok)[0], pb[ok]].max()) if ok.any() else 0.0
    if rep["unpaired_A"] or rep["unpaired_B"]:
        rep["error"] = ("%d + %d rim vertices are further than the %.4f mm ceiling from any partner, "
                        "so the seam would stay open there"
                        % (rep["unpaired_A"], rep["unpaired_B"], tol))
        return None, None, rep
    mid = 0.5 * (PB[ok] + PA[pb[ok]])
    VA2 = VA2.copy(); VB2 = VB2.copy()
    VA2[np.asarray(idxA, int)[pb[ok]]] = mid
    VB2[np.asarray(idxB, int)[ok]] = mid
    V = np.vstack([VA2, VB2])
    T = np.vstack([TA2, TB2 + len(VA2)])
    V, T, _r, _ = _weld(V, T, [], max(tol * 1e-3, 1e-9))
    rep["tri"] = int(len(T)); rep["vert"] = int(len(V))
    b, nm = mesh_health(V, T)
    _hA, _hB = (health_in[:2], health_in[2:]) if health_in else ((VA2, TA2), (VB2, TB2))
    hA = mesh_health(*_weld(np.asarray(_hA[0], float), np.asarray(_hA[1], int), [], 1e-6)[:2])
    hB = mesh_health(*_weld(np.asarray(_hB[0], float), np.asarray(_hB[1], int), [], 1e-6)[:2])
    rep["boundary_in"] = int(hA[0] + hB[0]); rep["boundary_out"] = int(b)
    rep["nonmanifold_out"] = int(nm)
    rep["seam_open"] = int(b - max(hA[0], hB[0]))
    if rep["unresolved"] or rep["seam_open"] > 0 or nm > max(hA[1], hB[1]):
        rep["error"] = (
            "the seam did NOT close: %d open edge(s) and %d non-manifold beyond the inputs', and %d "
            "triangle(s) the boundary could not be cut across cleanly. A boundary with a CREASE the "
            "seam must turn - a box CORNER - is the known case; a plane, a sphere, or a box whose "
            "rings never meet, close to zero." % (rep["seam_open"], nm, rep["unresolved"]))
        return None, None, rep
    return V, T, rep


def lump_select(labels, n_lab, voxel_mm3, keep=None, min_vol=0.0, suspect=True, centres=None):
    """Choose connected components of a voxel mask. ONE selector, called by the ADD half AND the REM half.

    the agent, 2026-09-22, after a removal mask came out as 2,099 components of dust: *"The lump-selection
    machinery (`CC_KEEP`, `CC_MINVOL`) exists only on the ADD side, and REM needs it more."* It does,
    and the reason is structural rather than incidental: **REM is not the inverse of ADD.** A `close`
    fills concave voids as a few connected blobs, so the ADD mask is naturally a handful of lumps. An
    `open` shaves a thin skin off every convex feature in the box at once, so the REM mask is
    naturally thousands of specks. The half that arrives as dust is exactly the half that cannot be
    used without selection.

    `keep` is a list of 1-based component ranks by volume (the largest is 1), or None for all.
    `min_vol` drops components under that many mm3. Returns (mask_of_kept, table) where the table is
    one dict per component with rank, volume, voxel count and centre - the same shape `frozen_suspect`
    takes, so a regular array of lumps can be flagged before any of them is placed.
    """
    import numpy as np
    lab = np.asarray(labels)
    cnt = np.bincount(lab.ravel(), minlength=n_lab + 1)
    cnt[0] = 0
    order = np.argsort(-cnt)
    table = []
    for rank, c in enumerate([c for c in order if cnt[c] > 0], start=1):
        row = {"rank": rank, "label": int(c), "voxels": int(cnt[c]),
               "vol": float(cnt[c] * voxel_mm3)}
        if centres is not None:
            row["centre"] = tuple(float(v) for v in centres[c])
        table.append(row)
    chosen = []
    for row in table:
        if row["vol"] < float(min_vol):
            row["dropped"] = "under min_vol"
            continue
        if keep and row["rank"] not in set(int(k) for k in keep):
            row["dropped"] = "not in keep"
            continue
        chosen.append(row["label"])
        row["kept"] = True
    mask = np.isin(lab, chosen) if chosen else np.zeros(lab.shape, bool)
    if suspect and centres is not None and len(table) >= 3:
        try:
            import leangate as _G
            flagged = set(_G.frozen_suspect([r for r in table if "centre" in r]))
            for i, r in enumerate(table):
                if i in flagged:
                    r["suspect"] = "one of N near-identical lumps at constant pitch - a DESIGNED array?"
        except Exception:
            pass
    return mask, table


def scan_occupancy(V, T, g0, n, h, axis):
    """Occupancy of a regular grid by ray WINDING along `axis`: one ray per grid column, every triangle
    it crosses counted +1/-1 by the triangle's facing along the ray, and a cell is solid where the running
    count is non-zero. Pure numpy. Rays run the WHOLE mesh along `axis` (triangles are selected by the
    grid's footprint in the other two axes only), so a ray never starts inside the part.

    A crack in the mesh - two faces tessellated separately, a sliver of air between them - lets a ray pass
    without a hit, and every cell after it along that ray is then wrong. That is a STREAK along one axis,
    which is why this is only ever used through `inside_vote`."""
    V = np.asarray(V, float); T = np.asarray(T, int)
    g0 = np.asarray(g0, float); n = [int(v) for v in n]
    a = int(axis); b, c = [k for k in range(3) if k != a]
    A_, B_, C_ = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    lo = np.minimum(np.minimum(A_, B_), C_); hi = np.maximum(np.maximum(A_, B_), C_)
    g1b = g0[b] + (n[b] - 1) * h; g1c = g0[c] + (n[c] - 1) * h
    sel = (hi[:, b] >= g0[b]) & (lo[:, b] <= g1b) & (hi[:, c] >= g0[c]) & (lo[:, c] <= g1c)
    A_, B_, C_, lo, hi = A_[sel], B_[sel], C_[sel], lo[sel], hi[sel]
    nrm = np.cross(B_ - A_, C_ - A_)
    sg = np.sign(nrm[:, a])
    e1b, e1c = B_[:, b] - A_[:, b], B_[:, c] - A_[:, c]
    e2b, e2c = C_[:, b] - A_[:, b], C_[:, c] - A_[:, c]
    den = e1b * e2c - e2b * e1c
    ib0 = np.maximum(0, np.ceil((lo[:, b] - g0[b]) / h - 1e-9)).astype(int)
    ib1 = np.minimum(n[b] - 1, np.floor((hi[:, b] - g0[b]) / h + 1e-9)).astype(int)
    ic0 = np.maximum(0, np.ceil((lo[:, c] - g0[c]) / h - 1e-9)).astype(int)
    ic1 = np.minimum(n[c] - 1, np.floor((hi[:, c] - g0[c]) / h + 1e-9)).astype(int)
    cols, poss, sgns = [], [], []
    jb, jc = h * 1.41421356e-4, h * 1.73205081e-4
    for t in np.where((np.abs(den) > 1e-14) & (ib1 >= ib0) & (ic1 >= ic0))[0]:
        ib = np.arange(ib0[t], ib1[t] + 1); ic = np.arange(ic0[t], ic1[t] + 1)
        PB, PC = np.meshgrid(g0[b] + ib * h + jb, g0[c] + ic * h + jc, indexing="ij")
        wb, wc = PB - A_[t, b], PC - A_[t, c]
        u = (wb * e2c[t] - e2b[t] * wc) / den[t]
        v = (e1b[t] * wc - wb * e1c[t]) / den[t]
        m = (u >= 0.0) & (v >= 0.0) & (u + v <= 1.0)
        if not m.any():
            continue
        pa = A_[t, a] + u[m] * (B_[t, a] - A_[t, a]) + v[m] * (C_[t, a] - A_[t, a])
        IB, IC = np.meshgrid(ib, ic, indexing="ij")
        cols.append(IB[m] * n[c] + IC[m]); poss.append(pa); sgns.append(np.full(pa.shape, sg[t]))
    occ = np.zeros((n[b] * n[c], n[a] + 1), np.int32)
    if cols:
        col = np.concatenate(cols); pos = np.concatenate(poss); sgn = np.concatenate(sgns)
        o = np.lexsort((pos, col)); col, pos, sgn = col[o], pos[o], sgn[o]
        run = np.cumsum(sgn)
        start = np.r_[True, col[1:] != col[:-1]]
        base = np.maximum.accumulate(np.where(start, np.arange(len(col)), 0))
        run = run - np.where(base > 0, np.cumsum(sgn)[np.maximum(base - 1, 0)], 0) * (base > 0)
        same_next = np.r_[col[1:] == col[:-1], False]
        k = np.where(same_next & (run != 0))[0]
        ka = np.ceil((pos[k] - g0[a]) / h - 1e-9).astype(int)
        kb = np.floor((pos[k + 1] - g0[a]) / h + 1e-9).astype(int)
        ka = np.clip(ka, 0, n[a]); kb = np.clip(kb, -1, n[a] - 1)
        ok = kb >= ka
        np.add.at(occ, (col[k][ok], ka[ok]), 1)
        np.add.at(occ, (col[k][ok], kb[ok] + 1), -1)
    occ = np.cumsum(occ, axis=1)[:, :n[a]] > 0
    occ = occ.reshape(n[b], n[c], n[a])
    order = [0, 0, 0]
    order[b], order[c], order[a] = 0, 1, 2
    return np.transpose(occ, order)


def points_inside(P, V, T):
    """Inside/outside for SCATTERED points: ray WINDING along x, y and z, majority of three. The rays are
    nudged off the grid by a fixed irrational offset, for the reason `scan_occupancy` gives (a ray through
    a shared edge counts twice). Only triangles whose footprint meets the query points' footprint in the
    two other axes can cross a ray, so each axis looks at that column of the mesh and nothing else.
    Returns a bool array, True = inside. A mesh with holes is judged by the majority: a hole streaks one
    direction, the other two outvote it."""
    P = np.asarray(P, float).reshape(-1, 3); V = np.asarray(V, float); T = np.asarray(T, int)
    votes = np.zeros(len(P), int)
    if not len(P) or not len(T):
        return votes.astype(bool)
    A_, B_, C_ = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    lo = np.minimum(np.minimum(A_, B_), C_); hi = np.maximum(np.maximum(A_, B_), C_)
    for a in range(3):
        b, c = [k for k in range(3) if k != a]
        jb, jc = 1.41421356e-5, 1.73205081e-5
        pb, pc = P[:, b] + jb, P[:, c] + jc
        sel = ((hi[:, b] >= pb.min()) & (lo[:, b] <= pb.max()) & (hi[:, c] >= pc.min()) & (lo[:, c] <= pc.max()))
        idx = np.where(sel)[0]
        if not len(idx):
            continue
        ext = np.maximum(hi[idx][:, [b, c]] - lo[idx][:, [b, c]], 1e-9)
        cell = max(float(np.median(ext)) * 2.0, 1e-3)
        org = np.array([min(lo[idx, b].min(), pb.min()), min(lo[idx, c].min(), pc.min())]) - cell
        i0 = np.floor((lo[idx][:, [b, c]] - org) / cell).astype(np.int64)
        i1 = np.floor((hi[idx][:, [b, c]] - org) / cell).astype(np.int64)
        span = (i1 - i0 + 1)
        cnt = span[:, 0] * span[:, 1]
        tri = np.repeat(idx, cnt)
        k = np.concatenate([np.arange(n_) for n_ in cnt]) if len(cnt) else np.zeros(0, int)
        rep_span = np.repeat(span[:, 1], cnt)
        kb = np.repeat(i0[:, 0], cnt) + k // rep_span
        kc = np.repeat(i0[:, 1], cnt) + k % rep_span
        key = kb * 1000003 + kc
        o = np.argsort(key, kind="stable"); key, tri = key[o], tri[o]
        uk, first = np.unique(key, return_index=True)
        last = np.r_[first[1:], len(key)]
        qk = (np.floor((pb - org[0]) / cell).astype(np.int64) * 1000003
              + np.floor((pc - org[1]) / cell).astype(np.int64))
        pos = np.searchsorted(uk, qk)
        for i in range(len(P)):
            j = pos[i]
            if j >= len(uk) or uk[j] != qk[i]:
                continue
            t = tri[first[j]:last[j]]
            e1b, e1c = B_[t, b] - A_[t, b], B_[t, c] - A_[t, c]
            e2b, e2c = C_[t, b] - A_[t, b], C_[t, c] - A_[t, c]
            den = e1b * e2c - e2b * e1c
            ok = np.abs(den) > 1e-14
            den = np.where(ok, den, 1.0)
            wb, wc = pb[i] - A_[t, b], pc[i] - A_[t, c]
            u = (wb * e2c - e2b * wc) / den
            v = (e1b * wc - wb * e1c) / den
            m = ok & (u >= 0.0) & (v >= 0.0) & (u + v <= 1.0)
            if not m.any():
                continue
            tm = t[m]
            pa = A_[tm, a] + u[m] * (B_[tm, a] - A_[tm, a]) + v[m] * (C_[tm, a] - A_[tm, a])
            na = (B_[tm, b] - A_[tm, b]) * (C_[tm, c] - A_[tm, c]) - (B_[tm, c] - A_[tm, c]) * (C_[tm, b] - A_[tm, b])
            ahead = pa > P[i, a]
            if int(np.sign(na[ahead]).sum()) != 0:
                votes[i] += 1
    return votes >= 2


def inside_vote(V, T, g0, n, h):
    """Majority of three ray directions (x, y, z): a cell is solid when at least two of the three
    winding counts say so. A crack streaks ONE direction's rays; the other two outvote it.

    Written for `_ccextract`, 2026-09-22 (the agent's diagnosis, jobs\\DIAG_V2V3\\FINDINGS.md): the extract took the
    field's sign from the nearest triangle's facing on a body meshed face by face - 68,943 crack points - and
    near V3 and V4 it called open air solid up to 7.7 mm deep, which is the lumps. Six tilted rays by majority
    agreed with the truth at every tested point, including all 204 where the nearest-triangle sign was wrong.
    Returns (vote, [occ_x, occ_y, occ_z])."""
    occ = [scan_occupancy(V, T, g0, n, h, ax) for ax in range(3)]
    s = occ[0].astype(np.int8) + occ[1].astype(np.int8) + occ[2].astype(np.int8)
    return s >= 2, occ


def cluster_points(P, link):
    """Group points: two points are joined when they lie within `link` of each other. numpy + a small
    union-find over grid cells of size `link`; returns a label per point."""
    P = np.asarray(P, float)
    n = len(P)
    parent = np.arange(n)

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    if n == 0:
        return parent
    key = np.floor(P / link).astype(np.int64)
    cells = {}
    for i, k in enumerate(map(tuple, key)):
        cells.setdefault(k, []).append(i)
    offs = [(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)]
    for k, idx in cells.items():
        idx = np.asarray(idx)
        for o in offs:
            k2 = (k[0] + o[0], k[1] + o[1], k[2] + o[2])
            if k2 < k or k2 not in cells:
                continue
            j = np.asarray(cells[k2])
            d = np.linalg.norm(P[idx][:, None, :] - P[j][None, :, :], axis=2)
            ii, jj = np.nonzero(d <= link)
            for a_, b_ in zip(idx[ii], j[jj]):
                ra, rb = find(a_), find(b_)
                if ra != rb:
                    parent[max(ra, rb)] = min(ra, rb)
    return np.array([find(i) for i in range(n)])


def inside_consistency(V, T, h=0.25, pad=0.5, link=None):
    """WHERE A CLOSED MESH'S INSIDE DEPENDS ON THE RAY DIRECTION (31aj, R4 run 16's crown pit). A mesh can be `solid True
    nonmanifold False selfint 0` and still carry a buried one-layer sheet (or its fan-filled twin): every ray along one axis
    that crosses it counts one crossing too many, and a parity / single-axis inside test calls the material beyond it AIR -
    the blend then builds that air column as surface (a 4.2 mm pit through the crown top). The three axes' winding
    occupancies are compared with their majority vote on a grid of h over the mesh; the voxels where any axis disagrees are
    grouped (`cluster_points`). A clean closed mesh gives none (the rays are jittered off the grid, scan_occupancy).
    Returns a list of {"n": voxels, "at": centre, "lo": .., "hi": .., "axes": "xyz" letters that disagree}, the largest first."""
    V = np.asarray(V, float); T = np.asarray(T, int)
    if not len(T):
        return []
    lo = V.min(0) - pad + h * np.array([0.37, 0.29, 0.43]); hi = V.max(0) + pad
    n = (np.ceil((hi - lo) / h).astype(int) + 1).tolist()
    vote, occ = inside_vote(V, T, lo, n, h)
    dis = (occ[0] != vote) | (occ[1] != vote) | (occ[2] != vote)
    if not dis.any():
        return []
    I = np.argwhere(dis); P = lo + I * h
    lab = cluster_points(P, link or 1.5 * h)
    out = []
    for g in np.unique(lab):
        m = lab == g; Q = P[m]; J = I[m]
        ax = "".join("xyz"[a] for a in range(3) if (occ[a][J[:, 0], J[:, 1], J[:, 2]] != vote[J[:, 0], J[:, 1], J[:, 2]]).any())
        out.append({"n": int(m.sum()), "at": [round(float(v), 2) for v in Q.mean(0)], "lo": [round(float(v), 2) for v in Q.min(0)],
                    "hi": [round(float(v), 2) for v in Q.max(0)], "axes": ax})
    return sorted(out, key=lambda c: -c["n"])


def internal_triangles(V, T, eps=0.05, link=0.6):
    """THE TRIANGLES WITH MATERIAL ON BOTH SIDES (31aj, R4 run 16's crown pit): each triangle's centroid stepped eps along its
    own normal both ways and tested by `points_inside` (3-axis winding vote); both inside = the triangle is not a boundary of
    the solid - a buried sheet, its fan-filled twin, a fold, or one wall of a slit thinner than 2*eps. Measured on R4 run 16's
    base (tags\\s4k30c\\arr_base.stl, 20,780 triangles, 4 s): the crown-underside recess's sheet, 2 triangles / 3.5 mm2 at
    z 87.2 - the sheet a single-axis parity test read as a 4.2 mm air column (the pit). Returns (mask over T, clusters) - each
    cluster {"n", "area_mm2", "at", "lo", "hi"}, the largest area first."""
    V = np.asarray(V, float); T = np.asarray(T, int)
    if not len(T):
        return np.zeros(0, bool), []
    A_, B_, C_ = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    Nn = np.cross(B_ - A_, C_ - A_); ar = 0.5 * np.linalg.norm(Nn, axis=1); ok = ar > 1e-10
    Nn[ok] /= (2.0 * ar[ok])[:, None]; Ct = (A_ + B_ + C_) / 3.0
    mask = np.zeros(len(T), bool)
    if ok.any():
        up = points_inside(Ct[ok] + eps * Nn[ok], V, T); dn = points_inside(Ct[ok] - eps * Nn[ok], V, T)
        mask[np.nonzero(ok)[0][up & dn]] = True
    idx = np.nonzero(mask)[0]; out = []
    if len(idx):
        lab = cluster_points(Ct[idx], link)
        for g in np.unique(lab):
            m = lab == g; P = Ct[idx][m]
            out.append({"n": int(m.sum()), "area_mm2": round(float(ar[idx][m].sum()), 4), "at": [round(float(v), 2) for v in P.mean(0)],
                        "lo": [round(float(v), 2) for v in P.min(0)], "hi": [round(float(v), 2) for v in P.max(0)]})
    return mask, sorted(out, key=lambda c: -c["area_mm2"])

import numpy as np


def choose_offsets(lo, cell, S, N, ax_deg=20.0, clear=0.3, k=40, extra=(0.0, 0.0, 0.0)):
    """The grid origin g0 (3,) whose planes along each axis stay off the skins near-parallel to them.
    lo: the window's low corner; S (n,3) the original's surface samples, N (n,3) their unit normals.
    For each axis the k candidate offsets are scored by the number of samples whose normal is within ax_deg of that axis
    (a skin the plane would run along) and that lie within `clear` mm of a grid plane; the fewest wins, ties by the largest
    clearance. `extra` (KEEP_OFFSET, mm) shifts the chosen grid by hand after an orbit review - the plane positions move,
    the grid still covers the window (the origin is kept at or below lo). Returns (g0, report) - report per axis:
    {"near_parallel": n, "within_clear": count, "clearance": mm, "offset_extra": mm}."""
    lo = np.asarray(lo, float); S = np.asarray(S, float).reshape(-1, 3); N = np.asarray(N, float).reshape(-1, 3)
    cs = np.cos(np.radians(ax_deg)); g0 = np.zeros(3); rep = []
    for ax in range(3):
        m = np.abs(N[:, ax]) >= cs if len(N) else np.zeros(0, bool)
        co = S[m, ax] if len(S) else np.zeros(0)
        best = None
        for j in range(k):
            off = (j + 0.5) / float(k) * cell; o = lo[ax] - cell + off
            if len(co):
                fr = (co - o) / cell; d = np.abs(fr - np.round(fr)) * cell
                cnt = int((d < clear).sum()); cl = float(d.min())
            else:
                cnt = 0; cl = cell
            key = (cnt, -cl)
            if best is None or key < best[0]: best = (key, o, cnt, cl)
        o = best[1] + float(extra[ax])
        while o > lo[ax] + 1e-9: o -= cell
        while o < lo[ax] - cell - 1e-9: o += cell
        g0[ax] = o
        rep.append({"near_parallel": int(m.sum()) if len(N) else 0, "within_clear": int(best[2]), "clearance": round(float(best[3]), 3), "offset_extra": float(extra[ax])})
    return g0, rep


def bin_index(X, g0, cell, nb):
    return np.clip(np.floor((np.asarray(X, float) - g0) / cell).astype(int), 0, np.asarray(nb) - 1)


def boundary_widths(rebuild, forced, g0, cell, S, N, d, slab=0.3, sin_min=0.05):
    """The seam width a cut would leave on every face between a rebuilt bin and a kept (not forced) one.
    rebuild, forced: bool (nx,ny,nz); S (n,3) the original's VISIBLE samples, N their normals, d (n,) each one's distance
    to the new surface. For a sample within `slab` of a grid plane whose two neighbouring bins along that axis are one
    rebuilt and one kept-and-free, the estimate is d / max(sin(a), sin_min), a = the angle between the surface and the
    plane (sin a = sqrt(1 - n_ax^2)). Returns a list of dicts, one per such face with samples, the widest first:
    {"kept": (i,j,k), "rebuilt": (i,j,k), "axis": ax, "width": mm, "n": samples, "at": [x,y,z] of the widest sample}."""
    rebuild = np.asarray(rebuild, bool); forced = np.asarray(forced, bool); nb = np.array(rebuild.shape)
    S = np.asarray(S, float).reshape(-1, 3); N = np.asarray(N, float).reshape(-1, 3); d = np.asarray(d, float).reshape(-1)
    out = {}
    if not len(S): return []
    B = bin_index(S, g0, cell, nb)
    for ax in range(3):
        u = (S[:, ax] - g0[ax]) / cell; p = np.round(u).astype(int)
        near = (np.abs(u - p) * cell <= slab) & (p >= 1) & (p <= nb[ax] - 1)
        if not near.any(): continue
        idx = np.nonzero(near)[0]
        lo_b = B[idx].copy(); lo_b[:, ax] = p[idx] - 1
        hi_b = B[idx].copy(); hi_b[:, ax] = p[idx]
        r_lo = rebuild[lo_b[:, 0], lo_b[:, 1], lo_b[:, 2]]; r_hi = rebuild[hi_b[:, 0], hi_b[:, 1], hi_b[:, 2]]
        f_lo = forced[lo_b[:, 0], lo_b[:, 1], lo_b[:, 2]]; f_hi = forced[hi_b[:, 0], hi_b[:, 1], hi_b[:, 2]]
        a = r_lo & ~r_hi & ~f_hi
        b = r_hi & ~r_lo & ~f_lo
        sn = np.sqrt(np.clip(1.0 - N[idx, ax] ** 2, 0.0, 1.0))
        w = d[idx] / np.maximum(sn, sin_min)
        for sel, kept, reb in ((a, hi_b, lo_b), (b, lo_b, hi_b)):
            for q in np.nonzero(sel)[0]:
                key = (tuple(int(v) for v in kept[q]), ax)
                e = out.get(key)
                if e is None:
                    out[key] = e = {"kept": key[0], "rebuilt": tuple(int(v) for v in reb[q]), "axis": ax, "width": 0.0, "n": 0, "at": None}
                e["n"] += 1
                if w[q] > e["width"]: e["width"] = float(w[q]); e["at"] = [float(v) for v in S[idx[q]]]
    return sorted(out.values(), key=lambda e: -e["width"])


def grow(rebuild, forced, faces, seam_max):
    """Mark every kept-and-free bin behind a face estimated over seam_max as rebuilt. Returns (new rebuild, bins grown)."""
    r = np.asarray(rebuild, bool).copy(); n = 0
    for e in faces:
        if e["width"] <= seam_max: continue
        i, j, k = e["kept"]
        if forced[i, j, k] or r[i, j, k]: continue
        r[i, j, k] = True; n += 1
    return r, n


def clusters(points, cell=6.0, top=4):
    """points (n,3) grouped on a cell-mm grid, the most populous first: [(count, centre (3,), lo (3,), hi (3,))]"""
    P = np.asarray(points, float).reshape(-1, 3)
    if not len(P): return []
    k = np.floor(P / cell).astype(int)
    uk, inv, cnt = np.unique(k, axis=0, return_inverse=True, return_counts=True); inv = np.asarray(inv).reshape(-1)
    out = []
    for j in np.argsort(-cnt)[:top]:
        Q = P[inv == j]; out.append((int(cnt[j]), Q.mean(0), Q.min(0), Q.max(0)))
    return out

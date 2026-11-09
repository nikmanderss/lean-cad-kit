# MESH_JOB
import os, sys, time, json, struct
import numpy as np

MESH = os.environ["PC_MESH"]; OUT = os.environ["PC_OUT"]
THIN = float(os.environ.get("PC_THIN", "0.8")); WALL = float(os.environ.get("PC_WALL", "1.2"))
SAMPLE = int(os.environ.get("PC_SAMPLE", "400000")); MAXT = float(os.environ.get("PC_MAXT", "40.0"))
CL = float(os.environ.get("PC_CLUSTER", "4.0")); OFF = 0.02
t0 = time.time()


def say(*a):
    print(*a, flush=True)


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    if len(b) < 84 + n * 50:
        raise SystemExit("FAIL: %s is not a binary STL with %d facets" % (p, n))
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


tri = read_stl(MESH)
q = np.round(tri.reshape(-1, 3) / 1e-6).astype(np.int64)
u_, inv = np.unique(q, axis=0, return_inverse=True)
V = u_ * 1e-6; T = inv.reshape(-1, 3)
T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
P = V[T]; ctr = P.mean(1)
N = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); area = 0.5 * np.linalg.norm(N, axis=1); N = N / (2 * area[:, None] + 1e-30)
say("mesh %s: %d triangles, %d points (%.0f s)" % (os.path.basename(MESH), len(T), len(V), time.time() - t0))
step = max(1, len(T) // SAMPLE)
idx = np.arange(0, len(T), step)
cs = 2.0
lo3 = V.min(0) - MAXT - 1.0
dims = np.maximum(((V.max(0) + MAXT + 1.0 - lo3) / cs).astype(np.int64) + 1, 1)


def cid(ix, iy, iz):
    return (ix * dims[1] + iy) * dims[2] + iz


i0 = np.clip(((P.min(1) - lo3) / cs).astype(np.int64), 0, dims - 1); i1 = np.clip(((P.max(1) - lo3) / cs).astype(np.int64), 0, dims - 1)
cnt = np.prod(i1 - i0 + 1, axis=1)
owner = np.repeat(np.arange(len(T)), cnt)
first = np.cumsum(cnt) - cnt
loc = np.arange(cnt.sum()) - np.repeat(first, cnt)
nx = (i1 - i0 + 1)[owner]
lx = loc % nx[:, 0]; ly = (loc // nx[:, 0]) % nx[:, 1]; lz = loc // (nx[:, 0] * nx[:, 1])
tri_cells = cid(i0[owner, 0] + lx, i0[owner, 1] + ly, i0[owner, 2] + lz)
o = np.argsort(tri_cells, kind="stable"); tri_cells = tri_cells[o]; tri_owner = owner[o]
del owner, loc, nx, lx, ly, lz, o
d = -N[idx]; org = ctr[idx]
ns_ = int(np.ceil(MAXT / (cs * 0.5))) + 1
ts = np.linspace(0.0, MAXT, ns_)
pts = org[:, None, :] + d[:, None, :] * ts[None, :, None]
ic = np.clip(((pts - lo3) / cs).astype(np.int64), 0, dims - 1)
rc = cid(ic[..., 0], ic[..., 1], ic[..., 2])
del pts, ic
rc_sorted = np.sort(rc, axis=1)
keep = np.ones_like(rc_sorted, bool); keep[:, 1:] = rc_sorted[:, 1:] != rc_sorted[:, :-1]
ray_cells = rc_sorted[keep]; ray_owner = np.repeat(np.arange(len(idx)), keep.sum(1))
del rc, rc_sorted, keep
say("grid %s cells of %g mm: %d triangle entries, %d ray entries for %d rays (%.0f s)" % (tuple(int(x) for x in dims), cs, len(tri_cells), len(ray_cells), len(idx), time.time() - t0))
lo_i = np.searchsorted(tri_cells, ray_cells, side="left"); hi_i = np.searchsorted(tri_cells, ray_cells, side="right")
npair = hi_i - lo_i
total = int(npair.sum()); say("%d candidate pairs (%.0f s)" % (total, time.time() - t0))
best_t = np.full(len(idx), np.inf); best_ag = np.zeros(len(idx))
CH = 1500000; start = 0; done = 0; last = 0
while start < len(ray_cells):
    acc = np.cumsum(npair[start:])
    stop = start + int(np.searchsorted(acc, CH)) + 1
    sel = np.arange(start, min(stop, len(ray_cells)))
    c_ = npair[sel]
    if c_.sum():
        ri = np.repeat(ray_owner[sel], c_)
        fst = np.repeat(lo_i[sel], c_)
        offs = np.arange(c_.sum()) - np.repeat(np.cumsum(c_) - c_, c_)
        tj = tri_owner[fst + offs]
        m = tj != idx[ri]
        ri = ri[m]; tj = tj[m]
        v0 = P[tj, 0]; e1 = P[tj, 1] - v0; e2 = P[tj, 2] - v0
        dd = d[ri]
        pv = np.cross(dd, e2); det = np.einsum("ij,ij->i", e1, pv)
        ok = np.abs(det) > 1e-12
        inv_det = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tv = org[ri] - v0
        u = np.einsum("ij,ij->i", tv, pv) * inv_det
        qv = np.cross(tv, e1)
        v = np.einsum("ij,ij->i", dd, qv) * inv_det
        t = np.einsum("ij,ij->i", e2, qv) * inv_det
        ag = np.einsum("ij,ij->i", N[tj], dd)
        hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > OFF) & (t < MAXT) & (np.abs(ag) > 0.5)
        if hit.any():
            ri = ri[hit]; t = t[hit]; ag = ag[hit]
            np.minimum.at(best_t, ri, t)
            mm = t <= best_t[ri] + 1e-12
            best_ag[ri[mm]] = ag[mm]
        done += int(c_.sum())
    start = stop
    if done - last >= 50000000 or start >= len(ray_cells):
        say("  %d of %d pairs (%.0f s)" % (done, total, time.time() - t0)); last = done
measured = np.isfinite(best_t) & (best_ag > 0.5)
inverted = np.isfinite(best_t) & (best_ag < -0.5)
n_no = int((~np.isfinite(best_t)).sum()); n_inv = int(inverted.sum())
th = np.full(len(T), np.nan); th[idx[measured]] = best_t[measured]
t = best_t[measured]; ar = area[idx[measured]] * step
say("rays %d: %d with no exit within %g mm (thicker than that, or a hole), %d began outside (mis-oriented normals), %d walls measured (%.0f s)"
    % (len(idx), n_no, MAXT, n_inv, len(t), time.time() - t0))
res = {"mesh": MESH, "triangles": int(len(T)), "rays": int(len(idx)), "step": int(step), "measured": int(len(t)), "no_exit": n_no,
       "inverted": n_inv, "thin_floor": THIN, "wall_floor": WALL}
if len(t):
    edges = sorted(set([0.0, 0.5, THIN, WALL, 1.5, 2.0, 3.0, 1e9]))
    hist = []
    say("WALL THICKNESS (floors: thinnest part %.1f, walls %.1f mm)" % (THIN, WALL))
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (t >= lo) & (t < hi)
        hist.append({"from": lo, "to": (hi if hi < 1e8 else None), "rays": int(m.sum()), "pct": round(100.0 * m.sum() / len(t), 2), "mm2": round(float(ar[m].sum()), 1)})
        say("   %4.1f to %6s mm : %8d rays  %6.2f pct  %9.1f mm2 of surface" % (lo, ("%.1f" % hi) if hi < 1e8 else "inf", m.sum(), 100.0 * m.sum() / len(t), ar[m].sum()))
    res["hist"] = hist
    res.update({"min": round(float(t.min()), 3), "p01": round(float(np.percentile(t, 1)), 3), "median": round(float(np.median(t)), 3),
                "mm2_under_thin": round(float(ar[t < THIN].sum()), 1), "mm2_under_wall": round(float(ar[t < WALL].sum()), 1),
                "pct_under_thin": round(100.0 * float((t < THIN).mean()), 3), "pct_under_wall": round(100.0 * float((t < WALL).mean()), 3)})
    say("   min %.3f  p1 %.3f  median %.3f mm;  under %.1f: %.1f mm2 (%.2f pct);  under %.1f: %.1f mm2 (%.2f pct)"
        % (res["min"], res["p01"], res["median"], THIN, res["mm2_under_thin"], res["pct_under_thin"], WALL, res["mm2_under_wall"], res["pct_under_wall"]))
    thin_i = idx[measured][t < WALL]
    rows = []
    if len(thin_i):
        cell = np.floor(ctr[thin_i] / CL).astype(np.int64)
        keys, kinv = np.unique(cell, axis=0, return_inverse=True); kinv = kinv.ravel()
        kd = {tuple(k): i for i, k in enumerate(keys)}
        lab = np.arange(len(keys))
        for _ in range(len(keys)):
            changed = False
            for i, k in enumerate(keys):
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            j = kd.get((k[0] + dx, k[1] + dy, k[2] + dz))
                            if j is not None and lab[j] < lab[i]:
                                lab[i] = lab[j]; changed = True
            if not changed:
                break
        for g in np.unique(lab):
            ii = thin_i[lab[kinv] == g]; tt = th[ii]; cc = ctr[ii]
            lo, hi = cc.min(0), cc.max(0)
            k = int(np.argmin(tt))
            rows.append({"rays": int(len(ii)), "min": round(float(tt.min()), 3), "median": round(float(np.median(tt)), 3),
                         "mm2": round(float(area[ii].sum() * step), 1),
                         "box": [round(float(v), 1) for v in (lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])],
                         "centre": [round(float(v), 1) for v in 0.5 * (lo + hi)],
                         "min_at": [round(float(v), 2) for v in cc[k]],
                         "median_at": [round(float(v), 2) for v in cc[int(np.argsort(tt)[len(tt) // 2])]]})
        rows.sort(key=lambda x: -x["mm2"])
    res["clusters"] = rows[:60]; res["n_clusters"] = len(rows)
    say("THIN PLACES (under %.1f mm), clustered at %g mm - a cluster is a wall, a fin or a lamina; a stray is an edge:" % (WALL, CL))
    for r_ in rows[:25]:
        say("   %7.1f mm2  %5d rays  min %.2f  median %.2f mm  box x %7.1f..%7.1f  y %7.1f..%7.1f  z %6.1f..%6.1f"
            % ((r_["mm2"], r_["rays"], r_["min"], r_["median"]) + tuple(r_["box"])))
    say("   %d cluster(s) in all" % len(rows))
np.savez_compressed(os.path.join(OUT, "walls.npz"), thickness=th.astype(np.float32), step=step)
json.dump(res, open(os.path.join(OUT, "walls.json"), "w", encoding="utf-8"), indent=1)
say("%.0f s" % (time.time() - t0)); say("DONE")

"""kitlib_burrito - SHELVED as a chain (the client 2026-11-03): the first voxel burrito's library, its chain reached only through t_burrito.py (shelved too) - the live route is `kit rebuild`, the skin route. Its B.union(pieces) stays the sanctioned piece-to-piece union the raw-fuse refusals name (31bs T7 F2).
THE BURRITO, second build (the client, the project R18, 2026-09-10).  Import ONLY under freecadcmd.

WHAT IT IS, in the client's words: "a better, smarter, more capable, voxel mesh operation on a brep. Picking
the window it operates in is the only thing I should have to care about. The agent should figure out
how many sections are needed and where to cut clean lines vs. hammer out features on the model."
It is for ANY feature: whatever lies inside the window is re-expressed as clean, smooth, printable
material - gaps bridged, laminae welded, shards and punch-through gone, enclosed voids filled.

WHAT THE FIRST BUILD GOT WRONG (its own 17:45 report, and the client's rulings on it):
  - it cleaned every section on its own, so the outline STEPPED along the stack ("not wanted");
  - it filled each slice even-odd, so overlapping solids read as holes ("this is trash");
  - its window was a box, its two end caps mated and its other four walls did not;
  - it stacked polylines into ruled faces: faceted, and self-crossing when dense (the fuse then
    "manufactured" volume that scaled with the face count).

HOW THIS ONE WORKS
  1. FOOTPRINT, not a box.  Any polygon in the plane across the rays (a rectangle is the simple
     case) and a v-range along them.  Everything in footprint x [v0, v1] is replaced.  A MARGIN
     around it is sampled too, for context and for the mating.
  2. SAMPLE.  One ray per grid column (`spacing`) through the kit's own tessellation.  Crossings
     are paired by NONZERO WINDING from the triangle normals: overlapping solids and punch-through
     read as material, laminae as nothing.  Parity is the fallback for a ray whose winding does
     not close (a hole in the shell), and those rays are counted.
  3. CLEAN IN 3-D on the voxel grid, once for the whole region: CLOSE (`bridge`) welds gaps and
     laminae in every direction at once; ENCLOSED VOIDS - air the outside cannot reach - are
     FILLED (a print has no use for a bubble; the client); OPEN (`shave`) removes shards and tabs thinner
     than 2*shave; a MAJORITY vote (`majority`) rounds what is left.  Nothing is decided per slice.
  4. SHEETS and LAYERS.  The cleaned material is split into 3-D connected components (sheets); a
     loose one under `island_min` mm3 is a shard and goes.  Each sheet is read as LAYERS - the
     k-th material interval from the top in every column - so an undercut is two layers, never a
     filled gap.  Every layer has a top and a bottom height field.
  5. CLEAN LINES vs HAMMERED FEATURES.  The fields are smoothed with a crease-preserving average:
     neighbours further than `crease` away in height do not mix, so a real step stays a step (a
     clean line) and everything smaller flows together.  A crease-bounded patch smaller than
     `feature_min` mm2 is a feature to hammer: it is dissolved and its height re-interpolated from
     around it.  The agent draws no lines; it sets the two thresholds and reads the map picture.
  6. MATING on every wall.  Within `band` of the footprint edge the fields blend to the body's
     OWN raw skin and reach it exactly at the wall.  A wall column whose cleaned layer has no raw
     counterpart is a MISMATCH, printed with its place, so the wall can be moved to sound skin.
  7. BUILD (mode='build').  Per layer, per crease-bounded panel: ONE fitted B-spline sheet
     (degree 3, approximated to `fit_tol`), trimmed by the panel's outline tube - R41's "6x11
     combo", the construction the ledger says worked.  The solid under a top sheet and the solid
     over a bottom sheet are intersected; layers and sheets are fused into the piece; the body
     has the footprint prism cut out and the piece fused in.  The MANUFACTURED volume
     (result - cut - piece) is printed and the build REFUSED beyond `fuse_tol`.
  mode='probe' does 1-6, writes the pictures and burrito_plan.json, builds nothing.

WHAT IT CANNOT DO (say so on the card): the fields are height fields along the rays.  A face
steeper than atan(crease / spacing) becomes a vertical riser at a crease.  A drafted skirt face
seen by z rays is such a face: give the skirt its own pass with rays across it (`rays='y'`).
"""
import os, sys, math, json, time
import numpy as np
import Part
import FreeCAD as App
V = App.Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kitlib as K
import kitlib_render as R

_AXIS = {"x": 0, "y": 1, "z": 2}
_NAMES = "xyz"
LAST = {}


def frame(P):
    """(ax_c, ax_u, ax_v): the rays run along ax_v; the plan axes follow in CYCLIC order so that the
    local (c, u, v) frame is a proper rotation of xyz (z rays: c=x u=y; x rays: c=y u=z; y rays: c=z u=x)."""
    ax_v = _AXIS[str(P.get("rays", "z")).lower()]
    return (ax_v + 1) % 3, (ax_v + 2) % 3, ax_v

def _spin(P):
    """SPIN (degrees about world z, the client 2026-09-11: "burrito would work well on the skirt corners
    inside and out"): a corner wall runs at an angle to every axis, so the rays are turned to meet
    it - the body is rotated by -spin before the ray frame, the piece and region rotated back by
    +spin.  Rays 'x' with spin 45 look at a wall that faces halfway between -x and -y."""
    return float(P.get("spin", 0.0) or 0.0)

def _rot_pts(Vv, deg):
    """rotate (n,3) world points by deg about z"""
    if abs(deg) < 1e-9:
        return Vv
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    out = Vv.copy(); out[:, 0] = c * Vv[:, 0] - s * Vv[:, 1]; out[:, 1] = s * Vv[:, 0] + c * Vv[:, 1]
    return out

def _to_world(shape, ax_c, ax_u, ax_v, spin=0.0):
    if (ax_c, ax_u, ax_v) != (0, 1, 2):
        m = [0.0] * 16; m[15] = 1.0
        m[ax_c * 4 + 0] = 1.0; m[ax_u * 4 + 1] = 1.0; m[ax_v * 4 + 2] = 1.0
        s = shape.copy(); s.transformShape(App.Matrix(*m)); shape = s
    if abs(spin) > 1e-9:
        s = shape.copy(); s.rotate(V(0, 0, 0), V(0, 0, 1), spin); shape = s
    return shape

def footprint_poly(P):
    fp = P.get("footprint")
    if fp:
        pts = [(float(a), float(b)) for a, b in fp]
        if len(pts) >= 2 and abs(pts[0][0] - pts[-1][0]) < 1e-9 and abs(pts[0][1] - pts[-1][1]) < 1e-9:
            pts = pts[:-1]
        if len(pts) < 3:
            K.fail("burrito: footprint needs at least 3 (c, u) points")
    else:
        c0, c1, u0, u1 = float(P["c0"]), float(P["c1"]), float(P["u0"]), float(P["u1"])
        if not (c1 > c0 and u1 > u0):
            K.fail("burrito: c1>c0 and u1>u0 are required when no footprint polygon is given")
        pts = [(c0, u0), (c1, u0), (c1, u1), (c0, u1)]
    return np.array(pts, float)

def poly_sdist(poly, C, U):
    """signed distance of the grid points (C, U) to the footprint polygon: > 0 inside.  Also the index
    of the nearest polygon edge (the 'wall') for every point."""
    n = len(poly)
    d = np.full(C.shape, np.inf); edge = np.zeros(C.shape, int); inside = np.zeros(C.shape, bool)
    for i in range(n):
        ax, ay = poly[i]; bx, by = poly[(i + 1) % n]
        vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy
        if L2 < 1e-18:
            continue
        t = np.clip(((C - ax) * vx + (U - ay) * vy) / L2, 0.0, 1.0)
        di = np.hypot(C - (ax + t * vx), U - (ay + t * vy))
        closer = di < d
        d = np.where(closer, di, d); edge = np.where(closer, i, edge)
        cond = (ay > U) != (by > U)
        xint = ax + (U - ay) * vx / np.where(np.abs(vy) < 1e-18, 1e-18, vy)
        inside ^= cond & (C < xint)
    return np.where(inside, d, -d), edge


def sample_grid(Vr, T, cs, us, v0, mmpv, Hv):
    """RAW occupancy (S, K, Hv) from one +v ray per column.  Vr is the tessellation in the local
    (c, u, v) frame.  Each crossing carries the sign of its triangle's v-normal: -1 the ray ENTERS
    the solid, +1 it leaves; material where the running count is not zero.  Two closed solids that
    overlap count 2 inside the overlap - material, which is what a slicer would print and what the
    even-odd fill of the first build got wrong.  Returns (grid, columns hit, parity fallbacks)."""
    S, Kn = len(cs), len(us)
    G = np.zeros((S, Kn, Hv), bool)
    nz = R.tri_normals(Vr, T)[:, 2]
    Z = R.ZRays(Vr, T, cell=2.0)
    n_hit = 0; n_par = 0
    for i, c in enumerate(cs):
        for j, u in enumerate(us):
            z, t = Z.hits(float(c) + 0.0131, float(u) + 0.0071)
            if len(z) == 0:
                continue
            n_hit += 1
            sg = np.where(nz[t] < 0, 1, -1)
            w = np.cumsum(sg)
            if w[-1] == 0 and len(z) >= 2:
                inside = w[:-1] != 0
                a = z[:-1][inside]; b = z[1:][inside]
            else:
                n_par += 1
                zz = [z[0]]
                for zv in z[1:]:
                    if zv - zz[-1] > 1e-6:
                        zz.append(zv)
                zz = np.array(zz[:len(zz) // 2 * 2])
                a = zz[0::2]; b = zz[1::2]
            if len(a) == 0:
                continue
            i0 = np.ceil((a - v0) / mmpv - 0.5).astype(int); i1 = np.floor((b - v0) / mmpv - 0.5).astype(int)
            for lo, hi in zip(i0, i1):
                lo = max(int(lo), 0); hi = min(int(hi), Hv - 1)
                if hi >= lo:
                    G[i, j, lo:hi + 1] = True
    return G, n_hit, n_par


def _shift_or(m, axis, r, mode):
    if r <= 0:
        return m
    pad = [(0, 0)] * 3; pad[axis] = (r, r)
    P = np.pad(m, pad, mode=mode) if mode == "edge" else np.pad(m, pad, mode="constant", constant_values=False)
    out = m.copy(); n = m.shape[axis]
    for k in range(-r, r + 1):
        if k == 0:
            continue
        sl = [slice(None)] * 3; sl[axis] = slice(r + k, r + k + n)
        out |= P[tuple(sl)]
    return out

def dilate(m, rc, ru, rv, mode="edge"):
    """box dilation, separable: gaps up to 2r wide in each direction weld shut.  'edge' = material
    at the grid boundary continues beyond it (a skin crossing the window does)."""
    out = m
    for ax, r in ((0, rc), (1, ru), (2, rv)):
        out = _shift_or(out, ax, r, mode)
    return out

def erode(m, rc, ru, rv, mode="edge"):
    return ~dilate(~m, rc, ru, rv, mode)

def majority(m, rc, ru, rv):
    """majority vote over a (2rc+1)(2ru+1)(2rv+1) box: rounds pits and bumps smaller than the box
    without moving a wall or a step (a median, on a binary grid)."""
    if rc <= 0 and ru <= 0 and rv <= 0:
        return m
    cnt = m.astype(np.int16); tot = 1
    for ax, r in ((0, rc), (1, ru), (2, rv)):
        if r <= 0:
            continue
        pad = [(0, 0)] * 3; pad[ax] = (r, r)
        P = np.pad(cnt, pad, mode="edge"); acc = cnt.copy(); n = cnt.shape[ax]
        for k in range(-r, r + 1):
            if k == 0:
                continue
            sl = [slice(None)] * 3; sl[ax] = slice(r + k, r + k + n)
            acc += P[tuple(sl)]
        cnt = acc; tot *= 2 * r + 1
    return cnt * 2 > tot

def _dil6(m):
    out = m.copy()
    out[1:] |= m[:-1]; out[:-1] |= m[1:]
    out[:, 1:] |= m[:, :-1]; out[:, :-1] |= m[:, 1:]
    out[:, :, 1:] |= m[:, :, :-1]; out[:, :, :-1] |= m[:, :, 1:]
    return out

def reachable_air(G, max_iter=600):
    """air cells the outside can reach (6-connected) from any face of the grid.  Straight lines of
    sight from the six faces seed it (that is nearly all of it); pockets and undercuts are reached
    by propagation.  Returns (reach, iterations, converged)."""
    air = ~G
    reach = np.zeros_like(air)
    for ax in (0, 1, 2):
        reach |= ~np.logical_or.accumulate(G, axis=ax)
        reach |= ~np.flip(np.logical_or.accumulate(np.flip(G, ax), axis=ax), ax)
    reach &= air
    for it in range(max_iter):
        new = _dil6(reach) & air
        if not (new & ~reach).any():
            return reach, it, True
        reach |= new
    return reach, max_iter, False

def fill_unreachable(G, rc, ru, rv):
    """FILL BY ACCESSIBILITY: air that a ball of half-sizes (rc, ru, rv) cells cannot reach from the
    outside becomes material.  The ball's centre may only sit where it clears the material (the air
    eroded by the ball); those centre cells are flood-filled from the grid boundary; the ball swept
    over the reachable centres is the reachable air; the rest is filled.  So a crack, and a cavity
    behind a thin opening, weld at a SMALL ball, while a through-slot wider than the ball stays open
    however deep it runs.  The isotropic closing this replaces welded the rib's 1.5 mm design slot
    to the crown face wherever it narrowed below `bridge` and left it open elsewhere - 17 mm steps
    at every transition, the striped walls of the first build (the client, 2026-09-10).
    Returns (grid, cells filled, converged)."""
    if rc <= 0 and ru <= 0 and rv <= 0:
        return G, 0, True
    centres = ~dilate(G, rc, ru, rv)
    reach, it, ok = reachable_air(~centres)
    if not ok:
        return G, 0, False
    swept = dilate(reach, rc, ru, rv, mode="constant")    # over the
    fill = ~G & ~swept
    return G | fill, int(fill.sum()), True

def fill_voids(G, label):
    reach, it, ok = reachable_air(G)
    if not ok:
        print("BURRITO %s: void search did not converge in %d passes - unreached air is LEFT AS AIR (nothing filled blindly); "
              "raise mmpv or shrink the window" % (label, it), flush=True)
        return G, 0
    void = ~G & ~reach
    n = int(void.sum())
    return G | void, n


def column_runs(G):
    """every material interval of every column as arrays: (i, j, start_cell, end_cell) with end exclusive."""
    S, Kn, Hv = G.shape
    z = np.zeros((S, Kn, 1), np.int8)
    d = np.diff(np.concatenate([z, G.astype(np.int8), z], axis=2), axis=2)
    si, sj, sk = np.nonzero(d == 1); ei, ej, ek = np.nonzero(d == -1)
    return si, sj, sk, ek

class _UF(object):
    def __init__(self, n):
        self.p = list(range(n))
    def find(self, i):
        p = self.p
        while p[i] != i:
            p[i] = p[p[i]]; i = p[i]
        return i
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra

def sheets_from_runs(S, Kn, ri, rj, rs, re_):
    """3-D components of the runs (a run touches a run in a 4-neighbour column when their v-ranges
    overlap).  Returns comp id per run."""
    N = len(ri)
    cols = {}
    for n in range(N):
        cols.setdefault((int(ri[n]), int(rj[n])), []).append(n)
    uf = _UF(N)
    for (i, j), runs in cols.items():
        for nb in ((i + 1, j), (i, j + 1)):
            other = cols.get(nb)
            if not other:
                continue
            for a in runs:
                sa, ea = rs[a], re_[a]
                for b in other:
                    if sa < re_[b] and rs[b] < ea:
                        uf.union(a, b)
    root = np.array([uf.find(n) for n in range(N)])
    _, comp = np.unique(root, return_inverse=True)
    return comp, cols


def bilateral(H, w, crease, sp=1.0):
    """THE SMOOTHING PASS, slope-aware.  Each column's local slope is taken first (the gentler of its
    two one-sided differences on each axis, so never across a step); every neighbour in the
    (2w+1)^2 window is judged against that local PLANE, and the residuals of those within `crease`
    of it are averaged (triangular weights) and added back.  So a steep flank smooths exactly like a
    flat skin - the first build's smoother compared neighbours to the centre HEIGHT, found every
    neighbour on a rib flank further than `crease` away, and smoothed nothing there (the client, 2026-09-10:
    'missing a very much needed smoothing pass') - while a real step still mixes nothing across."""
    valid = ~np.isnan(H)
    if w <= 0:
        return H.copy()
    S, Kn = H.shape
    with np.errstate(invalid="ignore"):
        H1 = np.pad(H, 1, mode="constant", constant_values=np.nan)
        def pick(f, b):
            f = np.where(np.isnan(f), np.inf, f); b = np.where(np.isnan(b), np.inf, b)
            g = np.where(np.abs(f) <= np.abs(b), f, b)
            return np.where(np.isinf(g), 0.0, g) / sp
        gc = pick(H1[2:, 1:-1] - H, H - H1[:-2, 1:-1])
        gu = pick(H1[1:-1, 2:] - H, H - H1[1:-1, :-2])
        Hp = np.pad(H, w, mode="constant", constant_values=np.nan)
        acc = np.zeros(H.shape); wt = np.zeros(H.shape)
        for dc in range(-w, w + 1):
            for du in range(-w, w + 1):
                g = float((w + 1 - abs(dc)) * (w + 1 - abs(du)))
                N = Hp[w + dc:w + dc + S, w + du:w + du + Kn]
                r = N - (H + (dc * gc + du * gu) * sp)
                ok = ~np.isnan(r) & (np.abs(r) <= crease)
                acc += np.where(ok, r * g, 0.0); wt += np.where(ok, g, 0.0)
    out = np.where(wt > 0, H + acc / np.where(wt > 0, wt, 1.0), np.nan)
    out[~valid] = np.nan
    return out

def _label(valid, cut_c, cut_u):
    """4-connected components of the valid cells joined by UNCUT edges; labels 0..P-1, -1 invalid."""
    S, Kn = valid.shape
    ok_c = ~cut_c & valid[1:] & valid[:-1]
    ok_u = ~cut_u & valid[:, 1:] & valid[:, :-1]
    lab = np.arange(S * Kn).reshape(S, Kn)
    for _ in range(20000):
        n = lab.copy()
        m = np.minimum(n[1:], n[:-1])
        n[1:] = np.where(ok_c, np.minimum(n[1:], m), n[1:]); n[:-1] = np.where(ok_c, np.minimum(n[:-1], m), n[:-1])
        m = np.minimum(n[:, 1:], n[:, :-1])
        n[:, 1:] = np.where(ok_u, np.minimum(n[:, 1:], m), n[:, 1:]); n[:, :-1] = np.where(ok_u, np.minimum(n[:, :-1], m), n[:, :-1])
        if np.array_equal(n, lab):
            break
        lab = n
    lab = np.where(valid, lab, -1)
    ids = np.unique(lab[valid])
    out = np.full(valid.shape, -1, int)
    for k, v in enumerate(ids):
        out[lab == v] = k
    return out

def extend_creases(lab, cut_c, cut_u):
    """A crease that ENDS inside a panel leaves that panel with a step through it — a block whose
    top ramps smoothly into the skin further on (the arrowhead ridge on the crown: R18 probe
    17:45, 'top panels 1' with a 3 mm step in the section).  One fitted sheet cannot carry a step;
    it smears or rings.  So a loose crease end is extended STRAIGHT ON, in its own direction,
    until it meets the panel's edge or another crease: the two sides become two panels, and the
    riser between them tapers to nothing where the surfaces merge — the block's wall, as a B-rep
    would draw it.  Returns (cut_c, cut_u, cells extended)."""
    S, Kn = lab.shape
    cut_c = cut_c.copy(); cut_u = cut_u.copy()
    wc = cut_c | (lab[1:] != lab[:-1]); wu = cut_u | (lab[:, 1:] != lab[:, :-1])
    deg = np.zeros((S + 1, Kn + 1), int)
    I, J = np.nonzero(wc); np.add.at(deg, (I + 1, J), 1); np.add.at(deg, (I + 1, J + 1), 1)
    I, J = np.nonzero(wu); np.add.at(deg, (I, J + 1), 1); np.add.at(deg, (I + 1, J + 1), 1)
    deg[0, :] += 2; deg[-1, :] += 2; deg[:, 0] += 2; deg[:, -1] += 2
    same_c = (lab[1:] == lab[:-1]) & (lab[:-1] >= 0); same_u = (lab[:, 1:] == lab[:, :-1]) & (lab[:, :-1] >= 0)
    n_ext = 0
    I, J = np.nonzero(cut_c & same_c)
    for i, j in zip(I.tolist(), J.tolist()):
        for corner, dj in (((i + 1, j), -1), ((i + 1, j + 1), 1)):
            if deg[corner] != 1:
                continue
            jj = j + dj
            while 0 <= jj < Kn and not cut_c[i, jj] and same_c[i, jj]:
                cut_c[i, jj] = True; n_ext += 1
                far = (i + 1, jj + 1) if dj > 0 else (i + 1, jj)
                if deg[far] >= 1:
                    break
                jj += dj
    I, J = np.nonzero(cut_u & same_u)
    for i, j in zip(I.tolist(), J.tolist()):
        for corner, di in (((i, j + 1), -1), ((i + 1, j + 1), 1)):
            if deg[corner] != 1:
                continue
            ii = i + di
            while 0 <= ii < S and not cut_u[ii, j] and same_u[ii, j]:
                cut_u[ii, j] = True; n_ext += 1
                far = (ii + 1, j + 1) if di > 0 else (ii, j + 1)
                if deg[far] >= 1:
                    break
                ii += di
    return cut_c, cut_u, n_ext

def _shift0(a, axis, k):
    """`a` shifted by k cells along `axis` (a[i] <- a[i-k]), zeros where nothing shifts in."""
    if k == 0:
        return a
    out = np.zeros_like(a)
    src = [slice(None)] * 2; dst = [slice(None)] * 2
    if k > 0:
        src[axis] = slice(0, a.shape[axis] - k); dst[axis] = slice(k, None)
    else:
        src[axis] = slice(-k, None); dst[axis] = slice(0, a.shape[axis] + k)
    out[tuple(dst)] = a[tuple(src)]
    return out

def _step_edges(H, crease, ratio, axis, span_cells=4, cliff=6.0):
    """edges along `axis` that are STEPS: a jump over `crease` that STANDS OUT from the jumps either
    side of it (more than `ratio` times the larger neighbour).  A slope steep to the rays - a rib
    flank at 0.6..3 mm per column - has the same jump at every column: no edge stands out, no cut,
    one continuous surface.  The first build cut every jump over `crease` and turned the whole
    underside into 17 terraces with vertical walls between (the client, 2026-09-10: 'extremely wrong in
    result ... did not work in 3D').

    A FACETED slope is a ramp too.  The tessellation of a drafted wall puts the whole drop of each
    facet at the facet's edge: jumps 4, 0, 0, 4, 0, 0 at 0.5 mm columns - every 4 stands out from
    its flat neighbours and was cut (probe 12:10: five parallel 1 mm creases 1.5 mm apart down
    each rib wall, three across the vane underside, 20 bottom panels).  So a jump is NOT a step
    when a jump of the SAME SIGN and comparable size (at least a/ratio) lies within `span_cells`
    along the ray... that is the next tread of the same ramp.  A real cliff has no such companion;
    a slot's two walls are opposite in sign and both stay steps.

    The companion is searched in TWO DIMENSIONS: 2..span cells further along `axis` (1 cell is
    dead by construction - the step test already required the adjacent jump to be under a/ratio;
    the orchestrator's control run, 13:05) and up to `span` cells sideways.  A swept or tapered
    rib end puts each facet edge on a different row, so a one-row search saw every tread alone
    and cut all five (13:05: `step_span` removed 2 mm of 372).  Sideways offset 0 with along-
    axis offset 0 is the jump itself and is never a companion; the crease's own continuation
    (along-axis offset 0, sideways offset +-1) is excluded by requiring an along-axis offset.

    AND THE COMPANION MUST BE THE NEXT TREAD, NOT THE SAME CLIFF SEEN DIAGONALLY.  A cliff that
    runs diagonally across the grid is a chain of equal same-sign jumps offset (1,1), (2,2)... -
    exactly what the 2-D search took for a staircase, so it deleted every diagonal crease and left
    fragments that the extension rule then ran to the footprint edge (build 14:25: crease 910 ->
    2248 mm, extension x3.6, 45 bottom panels).  Two treads of a ramp stand at DIFFERENT levels
    (the second starts where the first ended); two cells of one cliff share the same two levels.
    So a companion must also have its lower level shifted from this jump's by more than `crease`.

    AND A JUMP OVER `cliff` IS A CUT WHATEVER ITS NEIGHBOURS SAY.  Build 5 (2026-09-11 14:15, the
    fields dumped and every panel checked for jumps between its OWN cells): top panel 9 (5,689
    cells) carried an 18.5 mm jump inside it at seven cells, bottom panel 1 a 23 mm one at sixteen -
    the rib wall's crease line had gaps where the ratio and ramp rules let a cell through, the two
    sides of the wall became ONE panel, and every fitter (tolerance, interpolation, quadric) rang
    by tens of millimetres on it.  A jump of `cliff` mm between two 0.5 mm columns is a wall at 85
    degrees or more; no facet of a drafted wall in this model reaches it (those are 4 mm)."""
    with np.errstate(invalid="ignore"):
        d = np.diff(H, axis=axis)
        lo = np.minimum(H[1:], H[:-1]) if axis == 0 else np.minimum(H[:, 1:], H[:, :-1])
    dn = np.nan_to_num(d, nan=0.0)
    a = np.abs(dn); sg = np.sign(dn)
    lo = np.nan_to_num(lo, nan=0.0)
    pad = [(0, 0), (0, 0)]; pad[axis] = (1, 1)
    ap = np.pad(a, pad, mode="constant", constant_values=0.0)
    n = a.shape[axis]
    sl_prev = [slice(None)] * 2; sl_prev[axis] = slice(0, n)
    sl_next = [slice(None)] * 2; sl_next[axis] = slice(2, n + 2)
    neighbour = np.maximum(ap[tuple(sl_prev)], ap[tuple(sl_next)])
    step = (a > crease) & (a > ratio * neighbour) & ~np.isnan(d)
    ramp = np.zeros(a.shape, bool)
    other = 1 - axis; span = int(span_cells)
    for k in range(-span, span + 1):
        if abs(k) < 2:
            continue
        ak = _shift0(a, axis, k); sk = _shift0(sg, axis, k); lk = _shift0(lo, axis, k)
        for m in range(-span, span + 1):
            a2 = _shift0(ak, other, m); s2 = _shift0(sk, other, m); lo2 = _shift0(lk, other, m)
            ramp |= (s2 == sg) & (a2 > 0) & (a2 >= a / ratio) & (np.abs(lo2 - lo) > crease)
    return (step & ~ramp) | ((a > float(cliff)) & ~np.isnan(d))

def label_panels(H, crease, ratio=2.5, span_cells=4, hard=False, cliff=6.0):
    """panels of a height field: the valid cells, split along every STEP (a jump over `crease` that
    stands out from its neighbours by `ratio`), with loose crease ends extended so no panel carries
    a step inside it.  Returns (labels 0..P-1 or -1, cut_c (S-1,K), cut_u (S,K-1), cells extended)
    and, with hard=True, three more: the labels BEFORE extension - the panels bounded by real
    creases only, which is the size that decides whether something is a feature - and the two
    cut arrays before extension (the primary creases; the map draws the rest in another colour)."""
    valid = ~np.isnan(H)
    cut_c = _step_edges(H, crease, ratio, 0, span_cells, cliff) & valid[1:] & valid[:-1]
    cut_u = _step_edges(H, crease, ratio, 1, span_cells, cliff) & valid[:, 1:] & valid[:, :-1]
    lab = _label(valid, cut_c, cut_u)
    lab_hard = lab; cut_c0 = cut_c; cut_u0 = cut_u
    cut_c, cut_u, n_ext = extend_creases(lab, cut_c, cut_u)
    if n_ext:
        lab = _label(valid, cut_c, cut_u)
    if hard:
        return lab, cut_c, cut_u, n_ext, lab_hard, cut_c0, cut_u0
    return lab, cut_c, cut_u, n_ext

def inpaint(H, holes, max_iter=None):
    """fill the `holes` cells from their valid neighbours (Jacobi relaxation: a smooth, harmonic
    patch); cells that are NaN and not holes stay NaN and are not used."""
    out = H.copy(); out[holes] = np.nan
    fixed = ~np.isnan(out)
    if not fixed.any() or not holes.any():
        return H.copy()
    if max_iter is None:
        max_iter = int(max(80, 3 * max(H.shape)))
    cur = out.copy()
    with np.errstate(invalid="ignore"):
        for it in range(max_iter):
            P = np.pad(cur, 1, mode="constant", constant_values=np.nan)
            nb = np.stack([P[:-2, 1:-1], P[2:, 1:-1], P[1:-1, :-2], P[1:-1, 2:]])
            cnt = (~np.isnan(nb)).sum(0)
            mean = np.where(cnt > 0, np.nansum(nb, axis=0) / np.where(cnt > 0, cnt, 1), np.nan)
            new = np.where(fixed, out, np.where(holes, mean, np.nan))
            if it > 10 and not np.isnan(new[holes]).any():
                diff = np.abs(new - cur); diff = diff[~np.isnan(diff)]
                if not len(diff) or diff.max() < 2e-4:
                    cur = new; break
            cur = new
    return cur

def fill_all(H):
    """every NaN filled: nearest values propagate, then relax.  For the fit grid of a panel."""
    return inpaint(H, np.isnan(H), max_iter=int(max(120, 3 * max(H.shape))))


def trace_cells(mask):
    """boundary loops of a cell set on the corner lattice (cell (i,j) owns corners (i,j)..(i+1,j+1)),
    directed with the cells on the LEFT: outer loops anticlockwise, holes clockwise."""
    P = np.pad(mask, 1, mode="constant", constant_values=False)
    m = P[1:-1, 1:-1]
    lo_u = m & ~P[1:-1, :-2]; hi_c = m & ~P[2:, 1:-1]; hi_u = m & ~P[1:-1, 2:]; lo_c = m & ~P[:-2, 1:-1]
    nxt = {}
    def add(sel, di0, dj0, di1, dj1):
        I, J = np.nonzero(sel)
        for i, j in zip(I.tolist(), J.tolist()):
            nxt.setdefault((i + di0, j + dj0), []).append((i + di1, j + dj1))
    add(lo_u, 0, 0, 1, 0); add(hi_c, 1, 0, 1, 1); add(hi_u, 1, 1, 0, 1); add(lo_c, 0, 1, 0, 0)
    loops = []
    while nxt:
        start = next(iter(nxt)); loop = [start]; cur = start
        while True:
            outs = nxt.get(cur)
            if not outs:
                break
            n = outs.pop()
            if not outs:
                del nxt[cur]
            if n == start:
                break
            loop.append(n); cur = n
        if len(loop) >= 4:
            loops.append(np.array(loop, float))
    return loops

def _dp(pts, tol):
    n = len(pts); keep = np.zeros(n, bool); keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        A = pts[a]; B = pts[b]; d = B - A; L = math.hypot(d[0], d[1]); seg = pts[a + 1:b]
        dist = np.hypot(seg[:, 0] - A[0], seg[:, 1] - A[1]) if L < 1e-12 else \
            np.abs((seg[:, 0] - A[0]) * d[1] - (seg[:, 1] - A[1]) * d[0]) / L
        k = int(np.argmax(dist))
        if dist[k] > tol:
            keep[a + 1 + k] = True; stack.append((a, a + 1 + k)); stack.append((a + 1 + k, b))
    return keep

def simplify_loop(pts, tol):
    """Douglas-Peucker on a closed loop: a diagonal staircase of cells becomes the straight line it
    is sampling (tol just over cell/sqrt2); a designed corner survives."""
    n = len(pts)
    if n <= 4:
        return pts
    k = int(np.argmax(np.hypot(pts[:, 0] - pts[0, 0], pts[:, 1] - pts[0, 1])))
    chain = np.vstack([pts, pts[:1]]); keep = np.zeros(n + 1, bool)
    keep[:k + 1] |= _dp(chain[:k + 1], tol); keep[k:] |= _dp(chain[k:], tol)
    out = chain[:-1][keep[:-1]]
    return out if len(out) >= 3 else pts

def chaikin(pts, passes=2):
    """corner-cutting on a closed loop: a cell-edge staircase becomes a smooth curve within ~cell/8 of
    it, a designed 90-degree corner is rounded by ~0.2 cells.  The first build's panel joints were
    0.5 mm STAIRS along every crease and silhouette (orchestrator's piece renders, 2026-09-10 18:15) -
    exactly the faceting the client rejects."""
    P = np.asarray(pts, float)
    for _ in range(int(passes)):
        Q = np.roll(P, -1, axis=0)
        R2 = np.empty((2 * len(P), 2)); R2[0::2] = 0.75 * P + 0.25 * Q; R2[1::2] = 0.25 * P + 0.75 * Q
        P = R2
    return P

def _area2(L):
    x, y = L[:, 0], L[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def run(body, P):
    """the burrito.  mode='probe' returns None after the pictures and burrito_plan.json;
    mode='build' returns (piece_solids_world, region_world, plan)."""
    t0 = time.time()
    ax_c, ax_u, ax_v = frame(P)
    nc, nu, nv = _NAMES[ax_c], _NAMES[ax_u], _NAMES[ax_v]
    build = str(P.get("mode", "probe")).lower() == "build"
    if build and not str(P.get("sections_approved", "") or "").strip():
        # recorded
        K.fail("burrito: mode='build' needs sections_approved='<the client, when, which sections>' in PARAMS - the client approves the "
               "probe's sections before any build. Run the probe, put its sections in front of the client, then record their word here.")
    poly = footprint_poly(P)
    v0 = float(P["v0"]); v1 = float(P["v1"])
    sp = float(P.get("spacing", 0.5)); mmpv = float(P.get("mmpv", 0.1)); margin = float(P.get("margin", 2.0))
    if not (v1 > v0 and sp > 0 and mmpv > 0):
        K.fail("burrito: v1>v0, spacing>0, mmpv>0 are required")
    Hv = int(math.ceil((v1 - v0) / mmpv - 1e-9)); v1e = v0 + Hv * mmpv
    out_dir = P.get("out_dir", "."); os.makedirs(out_dir, exist_ok=True)
    cmin, cmax = poly[:, 0].min(), poly[:, 0].max(); umin, umax = poly[:, 1].min(), poly[:, 1].max()
    def _grid(lo, hi):
        n = int(math.ceil((hi - lo) / sp - 1e-9)) + 1; n += (n + 1) % 2
        return 0.5 * (lo + hi) + (np.arange(n) - (n - 1) / 2.0) * sp
    cs = _grid(cmin - margin, cmax + margin); us = _grid(umin - margin, umax + margin)
    S, Kn = len(cs), len(us)
    C, U = np.meshgrid(cs, us, indexing="ij")
    sd, wall = poly_sdist(poly, C, U)
    in_fp = sd >= 0
    ncell = S * Kn * Hv
    print("BURRITO rays along %s: footprint %d points %s %.2f..%.2f %s %.2f..%.2f (+%g margin), %s %.2f..%.2f | grid %d x %d columns at %.2f, "
          "%d cells along %s at %.3f -> %.1f M cells | %d columns inside the footprint (%.1f mm2)"
          % (nv, len(poly), nc, cmin, cmax, nu, umin, umax, margin, nv, v0, v1e, S, Kn, sp, Hv, nv, mmpv, ncell / 1e6,
             int(in_fp.sum()), in_fp.sum() * sp * sp), flush=True)
    if ncell > 60e6:
        print("BURRITO NOTE: %.0f M cells is heavy (each cleaning pass copies the grid several times); raise mmpv or spacing if this runs out of memory" % (ncell / 1e6), flush=True)
    if abs(v1e - v1) > 1e-6:
        print("BURRITO NOTE: v1 rounded up to %.3f so the cells divide the range; the region cut uses %.3f" % (v1e, v1e), flush=True)

    Vv, T, _ = K.tess(body, 0.05)
    spin = _spin(P)
    if abs(spin) > 1e-9:
        Vv = _rot_pts(Vv, -spin)
        print("BURRITO spin %.1f deg about z: the rays meet a wall turned by that angle; footprint and v-range are in the SPUN frame" % spin, flush=True)
    Vr = Vv[:, [ax_c, ax_u, ax_v]]
    Pt = Vr[T]
    keep = ((Pt[:, :, 0].max(1) >= cs[0] - 0.5) & (Pt[:, :, 0].min(1) <= cs[-1] + 0.5) &
            (Pt[:, :, 1].max(1) >= us[0] - 0.5) & (Pt[:, :, 1].min(1) <= us[-1] + 0.5))
    T = T[keep]
    if len(T) == 0:
        K.fail("burrito: no triangle of the body lies under the footprint - check rays/footprint/c,u ranges")
    t1 = time.time()
    G_raw, n_hit, n_par = sample_grid(Vr, T, cs, us, v0, mmpv, Hv)
    cellv = sp * sp * mmpv
    print("BURRITO sampled %d columns (%d hit material, %d fell back to parity because the winding did not close) "
          "in %.0f s; %d triangles in reach (tess %.0f s); raw material %.0f mm3, %.0f inside the footprint"
          % (S * Kn, n_hit, n_par, time.time() - t1, len(T), t1 - t0, G_raw.sum() * cellv, G_raw[in_fp].sum() * cellv), flush=True)
    if n_hit == 0:
        K.fail("burrito: no column hit material - the footprint is not on the part")

    bridge = float(P.get("bridge", 2.5)); shave = float(P.get("shave", 0.3)); maj = float(P.get("majority", 0.5))
    rb_cu = int(bridge / 2.0 / sp + 1e-9); rb_v = int(round(bridge / 2.0 / mmpv))
    rs_cu = int(shave / sp + 1e-9); rs_v = int(round(shave / mmpv))
    rm_cu = int(maj / sp + 1e-9); rm_v = int(round(maj / mmpv))
    t2 = time.time()
    bridge_mode = str(P.get("bridge_mode", "ball")).lower()
    if bridge_mode == "close":
        G1 = erode(dilate(G_raw, rb_cu, rb_cu, rb_v), rb_cu, rb_cu, rb_v)
        n_bridged = int(G1.sum() - G_raw.sum())
    else:
        G1, n_bridged, ok_b = fill_unreachable(G_raw, rb_cu, rb_cu, rb_v)
        if not ok_b:
            print("BURRITO bridge: the ball search did not converge - nothing welded; raise mmpv or shrink the window", flush=True)
    G1, n_void1 = fill_voids(G1, "after bridging")
    G2 = dilate(erode(G1, rs_cu, rs_cu, rs_v), rs_cu, rs_cu, rs_v)
    n_shaved = int(G1.sum() - G2.sum())
    G3 = majority(G2, rm_cu, rm_cu, rm_v)
    n_maj = int(G3.sum() - G2.sum())
    G3, n_void2 = fill_voids(G3, "after shaving")
    print("BURRITO cleaned in 3-D in %.0f s: bridge %g %s (%d/%d cells) welded %+.1f mm3 | enclosed voids filled %+.1f mm3 | "
          "shave %g (%d/%d cells) removed %.1f mm3 | majority %g (%d/%d cells) %+.1f mm3 | voids after shaving %+.1f mm3"
          % (time.time() - t2, bridge, "by ball (air a ball of that diameter cannot reach is filled)" if bridge_mode != "close" else "by closing",
             rb_cu, rb_v, n_bridged * cellv, n_void1 * cellv, shave, rs_cu, rs_v, n_shaved * cellv,
             maj, rm_cu, rm_v, n_maj * cellv, n_void2 * cellv), flush=True)

    ri, rj, rs, re_ = column_runs(G3)
    if len(ri) == 0:
        K.fail("burrito: nothing is left after cleaning - shave is above the designed walls, or the footprint is in air")
    comp, cols = sheets_from_runs(S, Kn, ri, rj, rs, re_)
    n_comp = int(comp.max()) + 1
    vol = np.bincount(comp, weights=(re_ - rs) * cellv, minlength=n_comp)
    island_min = float(P.get("island_min", 2.0))
    order = np.argsort(-vol); rank = np.empty(n_comp, int); rank[order] = np.arange(n_comp)
    sheet = rank[comp]
    keep_sheet = vol[order] >= island_min
    n_drop = int((~keep_sheet).sum()); v_drop = float(vol[order][~keep_sheet].sum())
    G_fin = G3.copy()
    for n in np.nonzero(~keep_sheet[sheet])[0]:
        G_fin[ri[n], rj[n], rs[n]:re_[n]] = False
    live = keep_sheet[sheet]
    print("BURRITO sheets: %d connected pieces of material; %d kept, %d dropped as loose islands under %g mm3 (%.1f mm3 in all%s)"
          % (n_comp, int(keep_sheet.sum()), n_drop, island_min, v_drop,
             ("; largest dropped %.2f" % vol[order][~keep_sheet].max()) if n_drop else ""), flush=True)

    qi, qj, qs, qe = column_runs(G_raw)
    raw_cols = {}
    for n in range(len(qi)):
        raw_cols.setdefault((int(qi[n]), int(qj[n])), []).append((int(qs[n]), int(qe[n])))

    fields = {}
    per_col = {}
    for n in np.nonzero(live)[0]:
        per_col.setdefault((int(ri[n]), int(rj[n])), []).append((int(sheet[n]), int(rs[n]), int(re_[n])))
    def _field(key):
        if key not in fields:
            fields[key] = {"top": np.full((S, Kn), np.nan), "bot": np.full((S, Kn), np.nan),
                           "rawtop": np.full((S, Kn), np.nan), "rawbot": np.full((S, Kn), np.nan)}
        return fields[key]
    for (i, j), runs in per_col.items():
        by_sheet = {}
        for sh, s_, e_ in runs:
            by_sheet.setdefault(sh, []).append((s_, e_))
        rr = raw_cols.get((i, j), [])
        for sh, lst in by_sheet.items():
            lst.sort(key=lambda t: -t[0])
            for L, (s_, e_) in enumerate(lst):
                F = _field((sh, L))
                F["top"][i, j] = v0 + e_ * mmpv; F["bot"][i, j] = v0 + s_ * mmpv
                ov = [(a, b) for a, b in rr if a < e_ and s_ < b]
                if ov:
                    F["rawtop"][i, j] = v0 + max(b for a, b in ov) * mmpv
                    F["rawbot"][i, j] = v0 + min(a for a, b in ov) * mmpv
    keys = sorted(fields.keys())
    print("BURRITO layers: %s" % ", ".join("sheet %d layer %d: %d columns" % (sh, L, int((~np.isnan(fields[(sh, L)]["top"])).sum())) for sh, L in keys), flush=True)

    smooth = float(P.get("smooth", 2.0)); crease = float(P.get("crease", 1.0)); step_ratio = float(P.get("step_ratio", 2.5))
    step_span_cells = max(1, int(round(float(P.get("step_span", 2.0)) / sp)))
    cliff = float(P.get("cliff", 6.0))
    feature_min = float(P.get("feature_min", 6.0)); band = float(P.get("band", 2.0))
    w_cells = int(round(smooth / sp))
    wgt = np.clip(sd / max(band, 1e-9), 0.0, 1.0)
    ring = in_fp & (sd < sp)
    plan = {"sheets": [], "mismatch": {}, "creases_mm": 0.0, "creases_extended_mm": 0.0, "features_dissolved": 0, "features_area": 0.0}
    n_mis_total = 0; mis_cells = np.zeros((S, Kn), bool); dissolved_all = np.zeros((S, Kn), bool)
    n_sliver = 0; v_sliver = 0.0
    for key in keys:
        F = fields[key]
        valid = ~np.isnan(F["top"])
        comp = _label(valid, np.zeros((S - 1, Kn), bool), np.zeros((S, Kn - 1), bool))
        if comp.max() >= 1:
            area = np.bincount(comp[comp >= 0], minlength=int(comp.max()) + 1) * sp * sp
            small = np.isin(comp, np.nonzero(area < feature_min)[0]) & valid
            if small.any() and small.sum() < valid.sum():
                n_sliver += int(small.sum()); v_sliver += float(np.nansum((F["top"] - F["bot"])[small]) * sp * sp)
                for nm in ("top", "bot", "rawtop", "rawbot"):
                    F[nm][small] = np.nan
        for side in ("top", "bot"):
            H = F[side]; raw = F["raw" + side]
            Hs = bilateral(H, w_cells, crease, sp)
            mis = ~np.isnan(H) & np.isnan(raw)
            Hb = np.where(np.isnan(raw), Hs, wgt * Hs + (1.0 - wgt) * raw)
            dissolved = np.zeros(H.shape, bool); n_diss = 0
            for _round in range(3):
                lab, cut_c, cut_u, _, lab_hard, _c0, _u0 = label_panels(Hb, crease, step_ratio, step_span_cells, hard=True, cliff=float("inf"))
                nP = int(lab.max()) + 1
                if nP <= 1:
                    break
                nH = int(lab_hard.max()) + 1
                area_h = np.bincount(lab_hard[lab_hard >= 0], minlength=nH) * sp * sp
                small_ids = np.nonzero(area_h < feature_min)[0]
                small = np.isin(lab_hard, small_ids) & (lab_hard >= 0)
                if not small.any() or small.sum() == (lab >= 0).sum():
                    break
                Hn = inpaint(Hb, small)
                still = small & np.isnan(Hn)
                Hn[still] = Hb[still]
                dissolved |= small & ~still; n_diss += len(small_ids)
                Hb = Hn
            lab, cut_c, cut_u, n_ext, _lh, cut_c0, cut_u0 = label_panels(Hb, crease, step_ratio, step_span_cells, hard=True, cliff=cliff)
            F[side + "_final"] = Hb; F[side + "_panels"] = lab; F[side + "_cut"] = (cut_c, cut_u)
            F[side + "_cut0"] = (cut_c0, cut_u0)
            F[side + "_dissolved"] = dissolved
            if side == "top":
                n_mis = int((mis & ring).sum()); n_mis_total += n_mis; mis_cells |= mis & ring
            dissolved_all |= dissolved
            plan["creases_mm"] += float((cut_c.sum() + cut_u.sum()) * sp)
            plan["creases_extended_mm"] = plan.get("creases_extended_mm", 0.0) + float(n_ext * sp)
            plan["features_dissolved"] += n_diss
            plan["features_area"] += float(dissolved.sum() * sp * sp)
        sh, L = key
        tp = F["top_final"]; bt = F["bot_final"]; ok = ~np.isnan(tp) & ~np.isnan(bt)
        t_min = max(3.0 * float(P.get("fit_tol", 0.2)), mmpv, 0.1)
        with np.errstate(invalid="ignore"):
            crossed = ok & ((tp - bt) < t_min)
        if crossed.any():
            mid = 0.5 * (tp[crossed] + bt[crossed])
            tp[crossed] = mid + 0.5 * t_min; bt[crossed] = mid - 0.5 * t_min
            print("BURRITO sheet %d layer %d: top and bottom crossed in %d columns after smoothing - held %.2f apart there" % (sh, L, int(crossed.sum()), t_min), flush=True)
        thin = float(np.nanmin(tp - bt)) if ok.any() else float("nan")
        devs = {}
        for side in ("top", "bot"):
            Hf = F[side + "_final"]; raw = F["raw" + side]
            with np.errstate(invalid="ignore"):
                d = np.abs(Hf - raw)
            m = in_fp & ~np.isnan(d)
            new = int((in_fp & ~np.isnan(Hf) & np.isnan(raw)).sum())
            if m.any():
                dm = np.where(m, d, -1.0); k = int(np.argmax(dm)); i_, j_ = np.unravel_index(k, d.shape)
                devs[side] = {"max": float(d[i_, j_]), "at": [float(cs[i_]), float(us[j_])], "p99": float(np.percentile(d[m], 99)),
                              "mean": float(d[m].mean()), "columns": int(m.sum()), "new_material_columns": new}
                print("BURRITO deviation sheet %d layer %d %s: |final - raw| max %.2f at (%s %.1f, %s %.1f), p99 %.2f, mean %.3f over %d columns; "
                      "%d columns carry material where the raw had none (welded / filled)"
                      % (sh, L, side, devs[side]["max"], nc, cs[i_], nu, us[j_], devs[side]["p99"], devs[side]["mean"], int(m.sum()), new), flush=True)
            else:
                devs[side] = {"columns": 0, "new_material_columns": new}
        plan["sheets"].append({"sheet": sh, "layer": L, "columns": int(ok.sum()), "columns_in_footprint": int((ok & in_fp).sum()),
                               "volume_grid": float(np.nansum((tp - bt)[ok & in_fp]) * sp * sp),
                               "panels_top": int(F["top_panels"].max()) + 1, "panels_bot": int(F["bot_panels"].max()) + 1,
                               "thinnest": thin, "deviation": devs})
        print("BURRITO sheet %d layer %d: %d columns (%d in the footprint), %.0f mm3, top panels %d, bottom panels %d, thinnest %.2f, "
              "wall mismatches %d" % (sh, L, plan["sheets"][-1]["columns"], plan["sheets"][-1]["columns_in_footprint"],
                                      plan["sheets"][-1]["volume_grid"], plan["sheets"][-1]["panels_top"], plan["sheets"][-1]["panels_bot"], thin,
                                      int(((~np.isnan(F["top"]) & np.isnan(F["rawtop"])) & ring).sum())), flush=True)

    for e in range(len(poly)):
        sel = ring & (wall == e); n_ring = int(sel.sum()); n_mis = int((sel & mis_cells).sum())
        a, b = poly[e], poly[(e + 1) % len(poly)]
        where = ""
        if n_mis:
            I, J = np.nonzero(sel & mis_cells)
            where = " at %s %.1f..%.1f %s %.1f..%.1f" % (nc, cs[I].min(), cs[I].max(), nu, us[J].min(), us[J].max())
        plan["mismatch"]["wall_%d" % e] = {"from": [float(a[0]), float(a[1])], "to": [float(b[0]), float(b[1])], "columns": n_ring, "mismatch": n_mis}
        print("BURRITO wall %d (%s %.1f,%s %.1f)->(%s %.1f,%s %.1f): %d edge columns, %d cannot mate (cleaned layer with no raw skin there)%s%s"
              % (e, nc, a[0], nu, a[1], nc, b[0], nu, b[1], n_ring, n_mis, where,
                 "  <- move this wall into sound skin, or accept a step there" if n_mis else ""), flush=True)

    v_raw_fp = float(G_raw[in_fp].sum() * cellv); v_fin_fp = float(G_fin[in_fp].sum() * cellv)
    v_field = sum(s_["volume_grid"] for s_ in plan["sheets"])
    print("BURRITO decisions: %d sheet-layers | crease lines %.0f mm (jumps over %g), of which %.0f mm extended so no panel carries a step | "
          "features hammered %d (%.1f mm2 under %g mm2) | isolated slivers dropped %d columns (%.1f mm3) | band %g on %d edge columns, %d mismatches | smooth %g (%d cells)"
          % (len(keys), plan["creases_mm"], crease, plan.get("creases_extended_mm", 0.0), plan["features_dissolved"], plan["features_area"],
             feature_min, n_sliver, v_sliver, band, int(ring.sum()), n_mis_total, smooth, w_cells), flush=True)
    plan["slivers_dropped"] = {"columns": n_sliver, "mm3": v_sliver}
    print("BURRITO volume: raw in the footprint %.0f mm3 -> cleaned %.0f -> smoothed fields %.0f; expect the body to change by about %+.0f mm3 "
          "(bound: footprint x height, %.0f)" % (v_raw_fp, v_fin_fp, v_field, v_field - v_raw_fp, in_fp.sum() * sp * sp * (v1e - v0)), flush=True)

    try:
        zones = pass2_zones(fields, keys, in_fp, G_raw, G_fin, cs, us, sp, mmpv,
                            float(P.get("pass2_change_min", 0.3)), float(P.get("pass2_margin", 2.0)), float(P.get("pass2_min_area", 4.0)))
        z_area = sum(abs(_area2(z)) for z in zones)
        plan["pass2_footprints"] = [z.tolist() for z in zones]
        print("BURRITO pass 2 (shelved): %d zone(s) of change over %.0f mm2 (%.0f%% of the footprint) would be re-burritoed with the body kept elsewhere; "
              "polygons in burrito_plan.json pass2_footprints, cyan on the map" % (len(zones), z_area, 100.0 * z_area / max(in_fp.sum() * sp * sp, 1e-9)), flush=True)
    except Exception as e:
        zones = []; print("BURRITO pass 2 zones not computed (%s: %s)" % (type(e).__name__, e), flush=True)
    plan.update({"rays": nv, "c": nc, "u": nu, "footprint": poly.tolist(), "v0": v0, "v1": v1e, "spacing": sp, "mmpv": mmpv,
                 "grid": [S, Kn, Hv], "columns_hit": n_hit, "parity_fallbacks": n_par,
                 "raw_mm3": v_raw_fp, "cleaned_mm3": v_fin_fp, "fields_mm3": v_field, "expected_change": v_field - v_raw_fp,
                 "bridged_mm3": n_bridged * cellv, "voids_mm3": (n_void1 + n_void2) * cellv, "shaved_mm3": n_shaved * cellv,
                 "islands_dropped": n_drop, "islands_mm3": v_drop, "mismatches": n_mis_total,
                 "params": {k_: (v_ if isinstance(v_, (int, float, str, bool)) else str(v_)) for k_, v_ in P.items()}})
    with open(os.path.join(out_dir, "burrito_plan.json"), "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=1)

    LAST.clear(); LAST.update(dict(fields=fields, keys=keys, in_fp=in_fp, sd=sd, G_raw=G_raw, G_fin=G_fin, cs=cs, us=us,
                                   sp=sp, mmpv=mmpv, v0=v0, v1=v1e, poly=poly, plan=plan, frame=(ax_c, ax_u, ax_v)))
    try:
        _pictures(P, out_dir, cs, us, v0, v1e, sp, mmpv, G_raw, G_fin, fields, keys, in_fp, sd, poly, mis_cells, dissolved_all, nc, nu, nv, zones)
    except Exception as e:
        import traceback
        print("BURRITO pictures NOT written (%s: %s) - the numbers above still stand" % (type(e).__name__, e), flush=True)
        traceback.print_exc()
    print("BURRITO probe done in %.0f s" % (time.time() - t0), flush=True)
    if str(P.get("mode", "probe")).lower() != "build":
        return None
    return _build(P, cs, us, v0, v1e, sp, poly, fields, keys, in_fp, sd, ax_c, ax_u, ax_v, plan)


def _ramp(x):
    """0..1 -> RGB: blue - cyan - green - yellow - red"""
    x = np.clip(np.nan_to_num(x, nan=0.0), 0, 1)
    r = np.clip(np.minimum(4 * x - 1.5, -4 * x + 4.5), 0, 1)
    g = np.clip(np.minimum(4 * x + 0.5, -4 * x + 3.5), 0, 1)
    b = np.clip(np.minimum(4 * x + 1.5, -4 * x + 2.5), 0, 1)
    return (np.stack([r, g, b], -1) * 255).astype(np.uint8)

def _pictures(P, out_dir, cs, us, v0, v1, sp, mmpv, G_raw, G_fin, fields, keys, in_fp, sd, poly, mis, dissolved, nc, nu, nv, zones=()):
    from PIL import Image, ImageDraw
    S, Kn, Hv = G_raw.shape
    every = float(P.get("sheet_every", 10.0) or 0)
    px = int(max(2, min(10, 1400 // max(S, 1))))
    for key in keys:
        F = fields[key]
        panels = []
        for side in ("top", "bot"):
            H = F[side + "_final"]; valid = ~np.isnan(H)
            lo, hi = (np.nanmin(H), np.nanmax(H)) if valid.any() else (0, 1)
            img = _ramp((H - lo) / max(hi - lo, 1e-9))
            img[~valid] = (28, 28, 34)
            img[~in_fp & valid] = (img[~in_fp & valid] * 0.45).astype(np.uint8)
            img[dissolved & valid] = (250, 230, 60)
            img[mis] = (255, 0, 255)
            big = np.repeat(np.repeat(img, px, axis=0), px, axis=1)
            big = big.transpose(1, 0, 2)[::-1]
            im = Image.fromarray(np.ascontiguousarray(big)); dr = ImageDraw.Draw(im)
            W, Hh = im.size
            def tp(c, u):
                return ((c - cs[0] + sp / 2) / sp * px, Hh - (u - us[0] + sp / 2) / sp * px)
            cut_c, cut_u = F[side + "_cut"]
            cut_c0, cut_u0 = F.get(side + "_cut0", (cut_c, cut_u))
            for cc, cu, col in (((cut_c & ~cut_c0), (cut_u & ~cut_u0), (255, 150, 30)), (cut_c0, cut_u0, (255, 40, 40))):
                I, J = np.nonzero(cc)
                for i, j in zip(I.tolist(), J.tolist()):
                    x = (i + 1) * px; y0 = Hh - j * px; y1 = Hh - (j + 1) * px
                    dr.line([x, y0, x, y1], fill=col, width=2)
                I, J = np.nonzero(cu)
                for i, j in zip(I.tolist(), J.tolist()):
                    y = Hh - (j + 1) * px; x0 = i * px; x1 = (i + 1) * px
                    dr.line([x0, y, x1, y], fill=col, width=2)
            pp = [tp(c, u) for c, u in poly] + [tp(poly[0][0], poly[0][1])]
            dr.line(pp, fill=(255, 255, 255), width=2)
            for z in zones:
                zz = [tp(c, u) for c, u in z] + [tp(z[0][0], z[0][1])]
                dr.line(zz, fill=(0, 255, 255), width=1)
            dr.text((4, 4), "%s   %s %.1f..%.1f (right)  %s %.1f..%.1f (up)   height %.2f..%.2f" % (side.upper(), nc, cs[0], cs[-1], nu, us[0], us[-1], lo, hi), fill=(255, 255, 255))
            panels.append(im)
        Wt = max(p.size[0] for p in panels); Ht = sum(p.size[1] for p in panels) + 40
        sheet_im = Image.new("RGB", (Wt, Ht), (20, 20, 24)); y = 40
        for p in panels:
            sheet_im.paste(p, (0, y)); y += p.size[1]
        ImageDraw.Draw(sheet_im).text((4, 4), "burrito map  sheet %d layer %d   colour = height along %s | red = crease (clean line) | orange = crease extended to the panel edge | yellow = feature hammered | magenta = wall mismatch | white = footprint | cyan = pass-2 zone (shelved) | dim = margin"
                                      % (key[0], key[1], nv), fill=(255, 255, 80))
        sheet_im.save(os.path.join(out_dir, "burrito_map_S%d_L%d.png" % key))
    # stations  stations
    def section(kind, idx):
        if kind == "c":
            raw = G_raw[idx]; fin = G_fin[idx]; xs = us; xn = nu; cval = cs[idx]; inside = in_fp[idx]
        else:
            raw = G_raw[:, idx]; fin = G_fin[:, idx]; xs = cs; xn = nc; cval = us[idx]; inside = in_fp[:, idx]
        n = len(xs)
        img = np.zeros((Hv, n, 3), np.uint8); img[:] = (20, 20, 24)
        rt = raw.T; ft = fin.T
        img[rt & ft] = (120, 120, 132); img[ft & ~rt] = (255, 140, 0); img[rt & ~ft] = (70, 120, 255)
        img[:, ~inside] = (img[:, ~inside] * 0.45).astype(np.uint8)
        img = img[::-1]
        Wpx = 1400; scale = Wpx / (n * sp); Hpx = int(math.ceil((v1 - v0) * scale))
        im = Image.fromarray(np.ascontiguousarray(img)).resize((Wpx, max(Hpx, 1)), Image.NEAREST)
        canvas = Image.new("RGB", (Wpx, Hpx + 24), (0, 0, 0)); canvas.paste(im, (0, 24)); dr = ImageDraw.Draw(canvas)
        def tp(x, v):
            return ((x - xs[0] + sp / 2) * scale, 24 + (v1 - v) * scale)
        for key in keys:
            F = fields[key]
            for side in ("top", "bot"):
                H = F[side + "_final"]; line = H[idx] if kind == "c" else H[:, idx]
                pts = []
                for x, v in zip(xs, line):
                    if np.isnan(v):
                        if len(pts) > 1:
                            dr.line(pts, fill=(60, 230, 120), width=2)
                        pts = []
                    else:
                        pts.append(tp(x, v))
                if len(pts) > 1:
                    dr.line(pts, fill=(60, 230, 120), width=2)
        d = np.diff(inside.astype(np.int8))
        for k in np.nonzero(d != 0)[0]:
            x, _ = tp(xs[k] + sp / 2, 0); dr.line([x, 24, x, Hpx + 24], fill=(255, 255, 255), width=1)
        g = 5.0; gx = math.ceil(xs[0] / g) * g
        while gx <= xs[-1]:
            x, _ = tp(gx, 0); dr.line([x, 24, x, Hpx + 24], fill=(60, 60, 70)); dr.text((x + 2, 26), "%g" % gx, fill=(150, 150, 160)); gx += g
        gv = math.ceil(v0 / g) * g
        while gv <= v1:
            _, y = tp(0, gv); dr.line([0, y, Wpx, y], fill=(60, 60, 70)); dr.text((2, y + 1), "%g" % gv, fill=(150, 150, 160)); gv += g
        dr.text((4, 4), "burrito %s = %.2f   [%s horizontal, %s up]  %.3f mm/px   grey kept | orange added | blue removed | green final surfaces | white footprint edge | dim = outside the footprint, untouched"
                % (kind_name(kind), cval, xn, nv, 1 / scale), fill=(255, 255, 80))
        canvas.save(os.path.join(out_dir, "burrito_%s%.1f.png" % (kind_name(kind), cval)))
    def kind_name(kind):
        return nc if kind == "c" else nu
    n_pic = 0
    if every > 0:
        for kind, arr, lo, hi in (("c", cs, poly[:, 0].min(), poly[:, 0].max()), ("u", us, poly[:, 1].min(), poly[:, 1].max())):
            val = lo
            while val <= hi + 1e-9:
                idx = int(np.argmin(np.abs(arr - val))); section(kind, idx); n_pic += 1; val += every
    print("BURRITO pictures: %d maps (burrito_map_S*_L*.png) and %d sections (burrito_%s*.png, burrito_%s*.png) in %s"
          % (len(keys), n_pic, nc, nu, out_dir), flush=True)


def _approx(pts, tol):
    s = Part.BSplineSurface()
    last = None
    for kw in (dict(Points=pts, DegMin=3, DegMax=5, Continuity="C2", Tolerance=tol),
               dict(Points=pts, DegMin=3, DegMax=5, Continuity=4, Tolerance=tol),
               dict(Points=pts, DegMin=3, DegMax=5, Tolerance=tol)):
        try:
            s.approximate(**kw); return s
        except Exception as e:
            last = e
    raise RuntimeError("approximate: %s" % last)

def _quadric_sheet(I, J, H, cs, us, i0, i1, j0, j1):
    """least-squares QUADRIC (1, c, u, c2, cu, u2 on centred, scaled axes) through a panel's own
    cells, sampled on an 8x8 grid over the panel's box and interpolated as ONE B-spline sheet.
    The fallback when the approximator follows noise: it cannot oscillate, so two such sheets
    over a thin layer do not cross.  Returns (face, max |quadric - field| over the cells)."""
    c = cs[I].astype(float); u = us[J].astype(float); h = H[I, J].astype(float)
    cm, um = c.mean(), u.mean(); sc = max(float(c.std()), 1e-6); su = max(float(u.std()), 1e-6)
    x = (c - cm) / sc; y = (u - um) / su
    A = np.column_stack([np.ones(len(x)), x, y, x * x, x * y, y * y])
    coef, _, _, _ = np.linalg.lstsq(A, h, rcond=None)
    dev = float(np.abs(A @ coef - h).max())
    def f(c_, u_):
        x_ = (c_ - cm) / sc; y_ = (u_ - um) / su
        return coef[0] + coef[1] * x_ + coef[2] * y_ + coef[3] * x_ * x_ + coef[4] * x_ * y_ + coef[5] * y_ * y_
    gc = np.linspace(float(cs[i0]), float(cs[i1]), 8); gu = np.linspace(float(us[j0]), float(us[j1]), 8)
    pts = [[V(float(c_), float(u_), float(f(c_, u_))) for u_ in gu] for c_ in gc]
    s = Part.BSplineSurface(); s.interpolate(pts)
    return s.toShape(), dev

def fit_sheet(cs, us, H, tol, step_cells, mode="interp"):
    """one B-spline sheet through the height field H over (cs, us), no NaN allowed.
    mode 'interp' (the default since build 4, 2026-09-11 14:05): a degree-3 C2 INTERPOLATION through
    every fit_step of the field.  Bounded by construction - a cubic through samples overshoots by a
    fraction of the local jump, never by a room.  The tolerance-driven approximation ('approx', the
    old path) inserted knots until it met 0.2 mm on a 70-degree groove and RANG: top panel 9 of
    build 3 spanned z 41..137 on data 70..96, the untrimmed sheet self-intersected, and that was the
    whole piece-assembly failure ("Error in Face: BOPAlgo SelfIntersect" on the two slabs under it).
    Returns (face, tolerance used - 0.0 for the interpolation)."""
    ii = list(range(0, len(cs), max(1, step_cells))); jj = list(range(0, len(us), max(1, step_cells)))
    if ii[-1] != len(cs) - 1: ii.append(len(cs) - 1)
    if jj[-1] != len(us) - 1: jj.append(len(us) - 1)
    if len(ii) < 4 or len(jj) < 4:
        ii = list(range(len(cs))); jj = list(range(len(us)))
    pts = [[V(float(cs[i]), float(us[j]), float(H[i, j])) for j in jj] for i in ii]
    if mode == "interp":
        s = Part.BSplineSurface(); s.interpolate(pts)
        return s.toShape(), 0.0
    t = tol; last = None
    for _ in range(4):
        try:
            return _approx(pts, t).toShape(), t
        except Exception as e:
            last = e; t *= 2.0
    raise RuntimeError("burrito: sheet fit failed up to tolerance %.2f (%s)" % (t / 2, last))

def _pole_range(sh):
    """z range of a B-spline face's poles - where the sheet CAN go; the data range says where it should."""
    try:
        P_ = sh.Surface.getPoles()
        zs = [p.z for row in P_ for p in row]
        return min(zs), max(zs)
    except Exception:
        b = sh.BoundBox
        return b.ZMin, b.ZMax

def _trim(face, tube, name=""):
    try:
        r = face.common(tube); fl = [f for f in r.Faces if f.Area > 1e-6]
        if fl:
            return fl
    except Exception as e:
        print("burrito: %s face.common(tube) raised %s - slicing instead" % (name, e), flush=True)
    import BOPTools.SplitAPI as SA
    # no region
    try:
        pieces = SA.slice(face, [tube], "Split").Faces
    except Exception as e:
        print("burrito: %s slice of the sheet by its region raised %s - the sheet trims to nothing there" % (name, e), flush=True)
        return []
    return [f for f in pieces if tube.isInside(f.CenterOfMass, 1e-4, True)]

def reach_short(u, pieces, slack=1.0):
    """How far a union falls short of where its own inputs reached, per axis - [] when it reaches.

    A POSITIONAL check, because a volume check cannot see a small piece vanish. Measured 2026-09-17
    (the R21 session, `job_h_sections.py`, lifted here on its request): `union` dropped a 1413.5 mm3
    vane from a 5271.8 mm3 running union on two of five sections, returned ONE VALID SOLID and named
    nothing - 6560.9 > 0.95 x 5271.8, so a piece under 5 % of the union is invisible to the collapse
    guard. One comparison per axis found it; it has caught four real drops and raised no false positive.

    BoundBox over-reports on un-tessellated NURBS (L36), by tens of mm on these shapes. It is the
    right instrument HERE and only here, because both sides are BoundBoxes of the same kind of surface
    so the over-report cancels, and `slack` absorbs what does not. Never reuse these numbers as extents.
    """
    ext = [None] * 6
    for sh in pieces:
        if sh is None:
            continue
        b = sh.BoundBox
        v = [b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax]
        for k in range(3):
            ext[k] = v[k] if ext[k] is None else min(ext[k], v[k])
            ext[k + 3] = v[k + 3] if ext[k + 3] is None else max(ext[k + 3], v[k + 3])
    if ext[0] is None or u is None:
        return []
    bo = u.BoundBox
    got = [bo.XMin, bo.YMin, bo.ZMin, bo.XMax, bo.YMax, bo.ZMax]
    short = []
    for k, nm in enumerate("xyz"):
        if got[k] > ext[k] + slack:
            short.append("%s starts %.2f short of %.2f" % (nm, got[k], ext[k]))
        if got[k + 3] < ext[k + 3] - slack:
            short.append("%s stops %.2f short of %.2f" % (nm, got[k + 3], ext[k + 3]))
    return short


def shared(a, b, box=None, n=(9, 18, 18), tol=1e-7, budget_points=12000):
    """DO TWO SOLIDS SHARE MATERIAL, AND WHERE - by sampled `isInside`, never by `common()`.

    `shape.common()` returned 0.0000 mm3 on two solids sharing 100 of 245 sampled points (the R21
    session, 2026-09-17, a section's vane and blended core) and a cause was written down as fact for
    an hour on that number. Booleans lie on these shapes - cut, fuse, and now common - which is why
    the signed sampled distance is the project's instrument of record. A `common()` of zero is a
    claim to check, never a finding to act on. This is the check, lifted from `job_h_bandprobe.py`.

    Samples an (nx, ny, nz) grid over `box` (x0,x1,y0,y1,z0,z1; default: a's BoundBox), keeps the
    points inside `a`, asks `b` about each. Returns a dict: `in_a`, `shared`, `frac`, `box` (the
    extents of the shared points, or None), `points` (the shared points, for a z profile). SIZE IT:
    `isInside` on a NURBS solid runs at about 70 points per second here, so a grid over
    `budget_points` (12,000 = about three minutes, the step cap) is refused with the number rather
    than killed at the cap.
    """
    nx, ny, nz = n
    if nx * ny * nz > budget_points:
        raise ValueError("shared(): %d points at ~70 isInside/s is over the %d-point budget (about three "
                         "minutes); coarsen the grid or narrow the box" % (nx * ny * nz, budget_points))
    if box is None:
        bb = a.BoundBox
        box = (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax)
    xs = np.linspace(box[0], box[1], nx); ys = np.linspace(box[2], box[3], ny); zs = np.linspace(box[4], box[5], nz)
    inside_a = []
    for x in xs:
        for y in ys:
            for z in zs:
                if a.isInside(V(float(x), float(y), float(z)), tol, True):
                    inside_a.append((float(x), float(y), float(z)))
    hit = [p for p in inside_a if b.isInside(V(*p), tol, True)]
    out = {"in_a": len(inside_a), "shared": len(hit), "frac": (len(hit) / float(len(inside_a))) if inside_a else 0.0,
           "box": None, "points": hit}
    if hit:
        H = np.asarray(hit, float)
        out["box"] = (float(H[:, 0].min()), float(H[:, 0].max()), float(H[:, 1].min()), float(H[:, 1].max()),
                      float(H[:, 2].min()), float(H[:, 2].max()))
    print("burrito shared: %d of %d sampled points inside A are also inside B (%.1f %%)%s"
          % (out["shared"], out["in_a"], 100.0 * out["frac"],
             ("  spanning x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % out["box"]) if out["box"] else ""), flush=True)
    return out


def _union_in_order(order, pieces, tol, collapse):
    """The pairwise loop over `pieces` in the given index order. (shape, failed) with ORIGINAL indices."""
    failed = []
    u = None
    for i in order:
        nxt = pieces[i]
        if u is None:
            u = nxt
            continue
        try:
            cand = u.fuse(nxt) if tol <= 0 else u.fuse(nxt, tol)
        except Exception as e:
            failed.append((i, "raised %s" % str(e)[:80])); continue
        if cand is None or not getattr(cand, "Solids", None) or not cand.isValid():
            failed.append((i, "null or invalid")); continue
        if cand.Volume < collapse * max(u.Volume, nxt.Volume):
            failed.append((i, "volume collapsed to %.1f from %.1f + %.1f" % (cand.Volume, u.Volume, nxt.Volume))); continue
        u = cand
    return u, failed


def union(pieces, tol=0.0, label="", collapse=0.95, reach=True, reorder=True, slack=1.0):
    """THE PIECE-TO-PIECE UNION, pairwise, with a check at every step - L40's remedy as a library
    function, so a project script never needs a raw `.fuse(` of its own (the guard refuses one).

    Returns (shape, failed): `shape` is the union of every piece that joined (None if nothing did),
    `failed` is [(index, why)] for each piece that would not - named, never swallowed. A single
    multiFuse over N pieces answers yes or Null and cannot say which pair broke it (the project FAILURES
    row 52, 2026-09-17: three strips, all ten boundaries measured at 1.50 mm of overlap, one Null).
    The checks at each step: the kernel raised; the result is None / has no solid / is not valid;
    or its volume fell below `collapse` x the larger input - L47 records the kernel dropping solids
    under load and reporting a plausible number.

    THE RESULT DEPENDS ON THE ORDER, and until 2026-09-17 this said nothing about it (the R21 session,
    third batch item 1). Three pieces L, C, R where the two vanes L and R share nothing with each other
    and both overlap the core: L-C-R asks the kernel for the same hard join twice and drops R - one
    valid solid, plausible volume, 12.50 mm short in x; L-R-C fuses the two disjoint pieces into a cheap
    intermediate first and joins the core to both at once, and holds. So: the given order is tried
    first (it is the caller's intent and right four times in five); if a piece failed or the result
    falls short of where its inputs reached (`reach_short`, the positional check that a volume check
    cannot replace), the other orders are tried, up to five pieces (120 orders). The order used is
    printed when it is not the given one. `reorder=False` / `reach=False` switch either off.

    A result that still falls short after every order carries a synthetic entry `(-1, "reach: ...")`
    in `failed`, so a caller that only checks `failed` cannot mistake a drop for a success. The caller
    decides what a failure means: for the S5 piece a piece left out is the build failing (say FAIL:
    and stop); for a pre-union of strips it is the strip to look at (L39: overlap it). Run
    `reach_short` again yourself after any `removeSplitter` - a refine that drops a solid must not
    get through either.
    """
    live = [i for i, s in enumerate(pieces) if s is not None and getattr(s, "Volume", 0.0) > 1e-9]
    empty = [(i, "empty") for i, s in enumerate(pieces) if i not in live]
    if not live:
        return None, empty
    lp = [pieces[i] for i in live]
    given = tuple(live)
    orders = [given]
    if reorder and 1 < len(live) <= 5:
        import itertools as _it
        orders += [p for p in _it.permutations(given) if p != given]
    best = None
    tried = []
    for order in orders:
        u, failed = _union_in_order(order, pieces, tol, collapse)
        short = reach_short(u, lp, slack) if (reach and u is not None and hasattr(u, "BoundBox")) else []
        score = (len(failed), len(short))
        if best is None or score < best[0]:
            best = (score, order, u, failed, short)
        if not failed and not short:
            break
        tried.append((order, failed, short))
    score, order, u, failed, short = best
    failed = list(empty) + list(failed)
    if short:
        failed.append((-1, "reach: " + "; ".join(short)))
    if order != given and not (failed and any(i >= 0 for i, _ in failed)) and not short:
        print("burrito union%s: the given order lost a piece; unioned as %s instead (%d order(s) tried)"
              % ((" " + label) if label else "", "-".join("#%d" % i for i in order), len(tried) + 1), flush=True)
    if failed:
        print("burrito union%s: %d piece(s) would not join and are NOT in the result: %s"
              % ((" " + label) if label else "", len(failed), "; ".join("#%d (%s)" % f for f in failed)), flush=True)
    return u, failed


def _fuse_all(sols):
    sols = [s for s in sols if s is not None and s.Volume > 1e-9]
    if not sols:
        return None
    if len(sols) == 1:
        return sols[0]
    res = sols[0].fuse(sols[1:])
    try:
        if res is None or not res.Solids or not res.isValid():
            _u, _failed = union(sols, label="(diagnosing the multi-fuse)")
            if _failed:
                print("burrito: the multi-fuse of %d pieces failed; pairwise, the piece(s) that would not join: %s"
                      % (len(sols), "; ".join("#%d (%s)" % f for f in _failed)), flush=True)
            elif _u is not None:
                print("burrito: the multi-fuse of %d pieces failed but every pairwise step joined - the failure is in the "
                      "kernel's multi-argument fuse, not in a piece (L47)" % len(sols), flush=True)
    except Exception:
        pass
    return res

def _smooth_wire(mm, zf, closed, sp):
    """A LINE, NOT A STAIRCASE (the client 2026-09-11 14:33: "There should be lines getting drawn not steps
    everywhere. No part of a finished burrito has steps unless they were originally there").
    The cell-edge polyline is corner-cut twice (a rounded staircase within cell/8 of the cells,
    which are within half a cell of the surface they sample).  Its CORNERS - turns over 45 degrees
    on the polyline thinned at one cell, two within two cells counting once - stay exactly where
    they are; between corners the dense polyline becomes one cubic B-spline APPROXIMATED at 0.8
    cell (above the ripple: a straight run comes out straight, a curve smooth), or one LINE when
    its points stand under a cell off the chord.  Tested 2026-09-11 14:50 on the 0.5 grid: a
    rotated 40 x 20 rectangle, a 30 mm disc, a stadium and a ring all reproduce their cells' area
    to 0.3 % and extrude to the right volume.  (One closed approximation across a sharp corner
    makes a hairpin there: the side face of the prism came out 14 % too large and its volume 16 %
    - that is why corners split the fit.  An interpolation through thinned points bows a
    rectangle's sides out by 9 mm: never interpolate a thinned outline.)  Returns a Wire; the
    thinned polygon if anything about the spline wire is not right, so nothing is ever dropped."""
    P = np.asarray(mm, float)
    n0 = len(P)
    if (closed and n0 < 4) or (not closed and n0 < 2):
        pts0 = [V(float(c), float(u), zf) for c, u in P]
        return Part.makePolygon(pts0 + [pts0[0]]) if closed else Part.makePolygon(pts0)
    dense = chaikin(P, 2) if closed else chaikin_open(P, 2)
    thin = simplify_loop(dense, 1.0 * sp) if closed else dense[_dp(dense, 1.0 * sp)]
    tpts = [V(float(c), float(u), zf) for c, u in thin]
    poly = Part.makePolygon(tpts + [tpts[0]]) if closed else Part.makePolygon(tpts)
    if (closed and len(thin) < 4) or (not closed and len(thin) < 2):
        return poly
    prev = np.roll(thin, 1, axis=0); nxt = np.roll(thin, -1, axis=0)
    d1 = thin - prev; d2 = nxt - thin
    turn = np.degrees(np.abs(np.arctan2(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0], d1[:, 0] * d2[:, 0] + d1[:, 1] * d2[:, 1])))
    corner = turn > 45.0
    if not closed:
        corner[0] = corner[-1] = True
    ci = [int(k) for k in np.nonzero(corner)[0]]
    merged = []
    for k in ci:
        if merged and np.hypot(*(thin[k] - thin[merged[-1]])) < 2.0 * sp:
            continue
        merged.append(k)
    if closed and len(merged) > 1 and np.hypot(*(thin[merged[0]] - thin[merged[-1]])) < 2.0 * sp:
        merged.pop()
    def nearest(q):
        return int(np.argmin(np.hypot(dense[:, 0] - q[0], dense[:, 1] - q[1])))
    try:
        if closed and not merged:
            pts = [V(float(c), float(u), zf) for c, u in np.vstack([dense, dense[:1]])]
            c = Part.BSplineCurve(); c.approximate(Points=pts, DegMin=3, DegMax=3, Tolerance=0.8 * sp, Continuity="C1")
            e = c.toShape(); gap = e.Vertexes[0].Point.distanceToPoint(e.Vertexes[-1].Point)
            w = Part.Wire([e, Part.makeLine(e.Vertexes[-1].Point, e.Vertexes[0].Point)]) if gap > 1e-6 else Part.Wire(e)
        else:
            if closed:
                k0 = nearest(thin[merged[0]])
                dense = np.roll(dense, -k0, axis=0)
                cuts = sorted(set(nearest(thin[k]) for k in merged)); cuts = [0] + [k for k in cuts if k > 0] + [len(dense)]
                pieces = [np.vstack([dense[a:b], dense[b:b + 1] if b < len(dense) else dense[:1]]) for a, b in zip(cuts[:-1], cuts[1:])]
            else:
                cuts = sorted(set(nearest(thin[k]) for k in merged)); cuts = [0] + [k for k in cuts if 0 < k < len(dense) - 1] + [len(dense) - 1]
                pieces = [dense[a:b + 1] for a, b in zip(cuts[:-1], cuts[1:])]
            edges = []
            for piece in pieces:
                if len(piece) < 2:
                    continue
                A = piece[0]; Bp = piece[-1]; dd = Bp - A; L = math.hypot(*dd)
                if L < 1e-9:
                    continue
                sag = float(np.abs((piece[1:-1, 0] - A[0]) * dd[1] - (piece[1:-1, 1] - A[1]) * dd[0]).max() / L) if len(piece) > 2 else 0.0
                pa = V(float(A[0]), float(A[1]), zf); pb = V(float(Bp[0]), float(Bp[1]), zf)
                if len(piece) < 4 or sag <= 1.0 * sp:
                    edges.append(Part.makeLine(pa, pb))
                else:
                    c = Part.BSplineCurve(); c.approximate(Points=[V(float(x), float(y), zf) for x, y in piece], DegMin=3, DegMax=3, Tolerance=0.8 * sp, Continuity="C1")
                    edges.append(c.toShape())
            w = Part.Wire(edges)
        if not (w.isValid() and w.isClosed() == closed):
            return poly
        if closed:
            f = Part.Face(w); a_poly = abs(_area2(dense))
            if not f.isValid() or abs(f.Area - a_poly) > 0.03 * max(a_poly, 1e-9):
                return poly
            t = f.extrude(V(0, 0, 1.0))
            if abs(t.Volume - f.Area) > 0.03 * max(f.Area, 1e-9):
                return poly
        return w
    except Exception:
        return poly

def loops_to_face(loops, zf, sp=None):
    ws = []
    for L in loops:
        if sp is not None:
            w = _smooth_wire(L, zf, True, sp)
        else:
            pts = [V(float(c), float(u), zf) for c, u in L]
            w = Part.makePolygon(pts + [pts[0]])
        ws.append((abs(_area2(np.asarray(L, float))), w))
    ws.sort(key=lambda t: -t[0])
    outer = ws[0][1]
    if len(ws) == 1:
        return Part.Face(outer)
    try:
        f = Part.Face([outer] + [w for _, w in ws[1:]])
        if f.isValid() and f.Area > 0:
            return f
    except Exception:
        pass
    f = Part.Face(outer)
    for _, w in ws[1:]:
        f = f.cut(Part.Face(w))
    return f

def _panel_tube(cells, cs, us, sp, zf, zlen, overlap, fp_tube, name="", passes=2):
    loops = trace_cells(cells)
    if not loops:
        return None
    raw = [np.column_stack([cs[0] - sp / 2 + L[:, 0] * sp, us[0] - sp / 2 + L[:, 1] * sp]) for L in loops]
    mm = raw
    face = loops_to_face(mm, zf, sp)
    try:
        bad = (not face.isValid()) or face.Area <= 1e-9
    except Exception:
        bad = True
    if bad:
        print("burrito: panel %s outline is invalid after smoothing (%d loops, %d points) - using the unsmoothed cell outline" % (name, len(mm), sum(len(L) for L in mm)), flush=True)
        face = loops_to_face(raw, zf)
    if overlap > 0:
        grown = None; last = ""
        for join in (0, 2, 1):
            try:
                off = face.makeOffset2D(overlap, join, False, False, False)
                if off.Area > face.Area:
                    grown = off; break
            except Exception as e:
                last = str(e)[:80]
        if grown is not None:
            face = grown
        else:
            print("burrito: panel %s offset failed (%s) - this panel's walls will be coincident with its neighbours'" % (name, last), flush=True)
    tube = face.extrude(V(0, 0, zlen))
    return tube.common(fp_tube)

def chaikin_open(pts, passes=2):
    """corner-cutting on an OPEN polyline: the two ends stay where they are."""
    P = np.asarray(pts, float)
    for _ in range(int(passes)):
        if len(P) < 3:
            return P
        A = P[:-1]; B = P[1:]
        Q = np.empty((2 * len(A), 2)); Q[0::2] = 0.75 * A + 0.25 * B; Q[1::2] = 0.25 * A + 0.75 * B
        P = np.vstack([P[:1], Q, P[-1:]])
    return P

def crease_sheets(cut_c, cut_u, cs, us, sp, zf, zlen, ext=4.0):
    """THE SHARED BOUNDARY.  Every crease edge of a layer (top and bottom cuts together) is chained on
    the corner lattice, each chain is smoothed once (Chaikin, ends fixed) and thinned, its two ends
    pushed 1 mm on so it clears the tube wall, and it becomes ONE vertical ruled sheet.  The layer's
    tube is split by these sheets, so the two panels either side of a crease are cut by the SAME
    surface - the first build traced and smoothed each panel's outline on its own, and the two
    boundaries were two different curves: gaps at one overlap, self-intersection at another, and
    no value that fixed both (orchestrator, 2026-09-10 18:45).  Returns (sheets, chains_mm)."""
    adj = {}
    def add(a, b):
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    I, J = np.nonzero(cut_c)
    for i, j in zip(I.tolist(), J.tolist()):
        add((i + 1, j), (i + 1, j + 1))
    I, J = np.nonzero(cut_u)
    for i, j in zip(I.tolist(), J.tolist()):
        add((i, j + 1), (i + 1, j + 1))
    used = set(); chains = []
    def walk(a, b):
        chain = [a, b]; used.add((a, b)); used.add((b, a))
        while len(adj[b]) == 2:
            nxt = adj[b][0] if adj[b][0] != a else adj[b][1]
            if (b, nxt) in used:
                break
            used.add((b, nxt)); used.add((nxt, b)); chain.append(nxt); a, b = b, nxt
        return chain
    for corner in list(adj.keys()):
        if len(adj[corner]) != 2:
            for nb in adj[corner]:
                if (corner, nb) not in used:
                    chains.append(walk(corner, nb))
    for corner in list(adj.keys()):
        for nb in adj[corner]:
            if (corner, nb) not in used:
                chains.append(walk(corner, nb))
    sheets = []; chains_mm = []
    for ch in chains:
        L = np.array(ch, float)
        mm = np.column_stack([cs[0] - sp / 2 + L[:, 0] * sp, us[0] - sp / 2 + L[:, 1] * sp])
        closed = len(mm) > 3 and np.allclose(mm[0], mm[-1])
        if closed:
            wire = _smooth_wire(mm[:-1], zf, True, sp)
            mm = np.array([[v.X, v.Y] for v in wire.Vertexes], float) if len(wire.Vertexes) > 2 else mm
        else:
            sm = chaikin_open(mm, 1)
            sm = sm[_dp(sm, 0.5 * sp)] if len(sm) > 2 else sm
            # over the
            def _end_dir(P_, at_end):
                q = P_[::-1] if at_end else P_
                k = 1
                while k < len(q) - 1 and np.hypot(*(q[0] - q[k])) < 3.0:
                    k += 1
                d_ = q[0] - q[k]; n_ = np.hypot(*d_)
                return d_ / n_ if n_ > 1e-9 else None
            d0 = _end_dir(sm, False); d1 = _end_dir(sm, True)
            if d0 is not None: sm = np.vstack([sm[0] + d0 * float(ext), sm])
            if d1 is not None: sm = np.vstack([sm, sm[-1] + d1 * float(ext)])
            wire = _smooth_wire(sm, zf, False, sp)
            mm = sm
        sheet = wire.extrude(V(0, 0, zlen))
        sheets.append(sheet); chains_mm.append(mm)
    return sheets, chains_mm

def _expand_plan(reg, delta, zf, zlen):
    """the region's plan footprint grown by `delta` all round and re-extruded: the region solids of a
    layer then OVERLAP their neighbours by 2*delta instead of sharing a wall exactly.  the client, 2026-09-11
    15:40, on the assembly failing for the fifth time on coincident walls: "must share walls exactly -
    they don't have to in my eyes so what's the workaround for the system?" - this is it.  A fuse of
    solids that overlap is the case OCC handles; a fuse of solids that touch along a wall is the case
    it does not (the kit's own 0.5 mm overlap rule, METHOD.md 3.4).  At a crease the higher region
    reaches delta past the step - a shelf half a cell wide.  Returns the grown tube, or `reg` itself
    if the footprint cannot be read or grown - and SAYS SO on the log (build 16, 15:48: every tube
    came back ungrown because makeOffset2D with the intersection join (2) returns a null result on
    these B-spline outlines, and the silent fallback hid it; the pair diagnosis found common = 0
    between the tubes.  The arc join (0) grows every one of them - jobs\\BURRITO\\
    job_expand_test.py, status_expand_test.json)."""
    if delta <= 0:
        return reg
    why = ""
    try:
        zc = zf + 0.5 * zlen
        wires = [w for w in reg.slice(V(0, 0, 1), zc) if w.isClosed()]
        if not wires:
            why = "no closed outline at mid-height"
            raise ValueError(why)
        faces = []
        for w in wires:
            try:
                fc = Part.Face(w)
                if fc.isValid() and fc.Area > 1e-6:
                    faces.append(fc)
            except Exception:
                pass
        if not faces:
            why = "outline made no face"
            raise ValueError(why)
        faces.sort(key=lambda f_: -f_.Area)
        face = faces[0]
        for f_ in faces[1:]:
            face = face.cut(f_) if face.isInside(f_.CenterOfMass, 1e-6, True) else face.fuse(f_)
        if len(face.Faces) != 1:
            face = max(face.Faces, key=lambda f_: f_.Area)
        off = None
        for join in (0, 2, 1):
            try:
                cand = face.makeOffset2D(float(delta), join, False, False, False)
                if cand.Area > face.Area:
                    off = cand; break
            except Exception as e:
                why = "makeOffset2D join %d: %s" % (join, str(e)[:60])
        if off is None:
            raise ValueError(why or "no offset grew the outline")
        off.translate(V(0, 0, zf - zc))
        tube = off.extrude(V(0, 0, zlen))
        if not (tube.isValid() and tube.Volume > reg.Volume):
            why = "grown tube invalid or not larger"
            raise ValueError(why)
        return tube
    except Exception as e:
        print("  tube NOT grown by %.2f mm (%s) - it will share walls with its neighbours" % (delta, why or str(e)[:80]), flush=True)
        return reg

def _region_cells(region, cs, us, sp, zmid):
    """bool mask (S, K) of the grid cells whose centre lies inside the split region (isInside on
    the cells of the region's plan bounding box).  Computed ONCE per region: the panel votes and
    the empty-slab diagnostics all read it."""
    b = region.BoundBox
    I = np.nonzero((cs >= b.XMin - sp) & (cs <= b.XMax + sp))[0]; J = np.nonzero((us >= b.YMin - sp) & (us <= b.YMax + sp))[0]
    m = np.zeros((len(cs), len(us)), bool)
    for i in I:
        for j in J:
            if region.isInside(V(float(cs[i]), float(us[j]), zmid), 1e-6, True):
                m[i, j] = True
    return m

def _mode_of(lab, mask):
    """the commonest panel label among the masked cells, and its count; (-1, 0) if none."""
    v = lab[mask & (lab >= 0)]
    if v.size == 0:
        return -1, 0
    ids, cnt = np.unique(v, return_counts=True)
    k = int(np.argmax(cnt))
    return int(ids[k]), int(cnt[k])

def _mode_label(lab, region, cs, us, sp, zmid):
    """the panel label a split region belongs to (kept for callers outside the build loop)."""
    return _mode_of(lab, _region_cells(region, cs, us, sp, zmid))

def _build(P, cs, us, v0, v1, sp, poly, fields, keys, in_fp, sd, ax_c, ax_u, ax_v, plan):
    t0 = time.time()
    print("BURRITO build: sections approved by %s" % P.get("sections_approved"), flush=True)
    mmpv = float(P.get("mmpv", 0.1))
    fit_tol = float(P.get("fit_tol", 0.2)); step_cells = max(1, int(round(float(P.get("fit_step", 1.0)) / sp)))
    small_panel = int(P.get("small_panel", 64))
    fit_mode = str(P.get("fit_mode", "interp") or "interp").lower()
    overlap = float(P.get("panel_overlap") or 0.5)
    assembly = str(P.get("assembly", "tubes") or "tubes").lower()
    t_min_build = max(3.0 * fit_tol, mmpv, 0.1)
    if fit_tol < 2.0 * mmpv:
        print("BURRITO WARNING: fit_tol %.2f is under 2 x mmpv (%.2f) - the fitter will follow the voxel staircase; set fit_tol >= %.2f" % (fit_tol, 2 * mmpv, 2 * mmpv), flush=True)
    zf = v0 - 1.0; zlen = (v1 - v0) + 2.0; D = zlen + 1.0; zmid = 0.5 * (v0 + v1)
    fp_face = Part.Face(Part.makePolygon([V(float(c), float(u), zf) for c, u in poly] + [V(float(poly[0][0]), float(poly[0][1]), zf)]))
    fp_tube = fp_face.extrude(V(0, 0, zlen))
    region = Part.Face(Part.makePolygon([V(float(c), float(u), v0) for c, u in poly] + [V(float(poly[0][0]), float(poly[0][1]), v0)])).extrude(V(0, 0, v1 - v0))
    S, Kn = len(cs), len(us)
    pieces = []; n_regions = 0; n_sheets_fit = 0
    for key in keys:
        F = fields[key]
        valid = ~np.isnan(F["top_final"]) & ~np.isnan(F["bot_final"])
        if not (valid & (sd > -sp)).any():
            continue
        edge_min = float(P.get("edge_min", 0.3)); passes = 3
        if edge_min > 0:
            with np.errstate(invalid="ignore"):
                thick_ok = valid & ((F["top_final"] - F["bot_final"]) >= edge_min)
            if thick_ok.sum() >= 0.5 * valid.sum():
                m3 = np.pad(thick_ok, 1, mode="constant", constant_values=False).astype(np.int8)
                votes = sum(m3[1 + a:1 + a + S, 1 + b:1 + b + Kn] for a in (-1, 0, 1) for b in (-1, 0, 1))
                voted = (votes >= 5) & valid
                if voted.sum() >= 0.75 * thick_ok.sum():
                    valid = voted
                else:
                    valid = thick_ok
                    print("BURRITO layer sheet %d layer %d: 3x3 vote would keep only %d of %d thick columns - vote skipped, this layer is too thin for it" % (key[0], key[1], int(voted.sum()), int(thick_ok.sum())), flush=True)
                print("BURRITO layer sheet %d layer %d: outline drawn at thickness >= %.2f, 3x3 vote (%d of %d columns kept)" % (key[0], key[1], edge_min, int(valid.sum()), int((~np.isnan(F["top_final"])).sum())), flush=True)
        else:
            passes = 2
            print("BURRITO layer sheet %d layer %d: edge_min 0 - raw column outline, Chaikin x2 (control)" % key, flush=True)
        tube = _panel_tube(valid, cs, us, sp, zf, zlen, 0.0, fp_tube, "sheet %d layer %d" % key, passes=passes)
        if tube is None or tube.Volume < 1e-9:
            print("burrito: sheet %d layer %d: no tube - skipped" % key, flush=True); continue
        # recorded
        tc_c, tc_u = F["top_cut"]; bc_c, bc_u = F["bot_cut"]
        tp0 = F["top_panels"]; bp0 = F["bot_panels"]
        pair_map = np.where(valid & (tp0 >= 0) & (bp0 >= 0), tp0 * 100003 + bp0, -1)
        for _fill in range(6):
            hole = valid & (pair_map < 0)
            if not hole.any():
                break
            cand = np.full(pair_map.shape, -1)
            for sh_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb_ = np.roll(pair_map, sh_, axis=(0, 1))
                cand = np.where((cand < 0) & (nb_ >= 0), nb_, cand)
            pair_map = np.where(hole & (cand >= 0), cand, pair_map)
        pc_c = valid[1:] & valid[:-1] & (pair_map[1:] >= 0) & (pair_map[:-1] >= 0) & (pair_map[1:] != pair_map[:-1])
        pc_u = valid[:, 1:] & valid[:, :-1] & (pair_map[:, 1:] >= 0) & (pair_map[:, :-1] >= 0) & (pair_map[:, 1:] != pair_map[:, :-1])
        print("BURRITO layer sheet %d layer %d: cut edges %d (top) + %d (bottom); pair-change edges %d -> the sheets" % (key[0], key[1], int(tc_c.sum() + tc_u.sum()), int(bc_c.sum() + bc_u.sum()), int(pc_c.sum() + pc_u.sum())), flush=True)
        sheets, chains = crease_sheets(pc_c, pc_u, cs, us, sp, zf, zlen)
        if sheets and assembly != "tubes":
            import BOPTools.SplitAPI as SA
            try:
                pieces_of_tube = [s_ for s_ in SA.slice(tube, sheets, "Split").Solids if s_.Volume > 1e-6]
            except Exception as e:
                print("burrito: sheet %d layer %d: splitting the tube by %d crease sheets raised %s - building the layer unsplit" % (key[0], key[1], len(sheets), e), flush=True)
                pieces_of_tube = [s_ for s_ in tube.Solids] or [tube]
        else:
            pieces_of_tube = [s_ for s_ in tube.Solids] or [tube]
        print("BURRITO layer sheet %d layer %d: tube %.0f mm3, %d crease chains (%.0f mm) -> %d plan regions"
              % (key[0], key[1], tube.Volume, len(sheets), sum(float(np.hypot(*np.diff(c_, axis=0).T).sum()) for c_ in chains if len(c_) > 1), len(pieces_of_tube)), flush=True)
        fitted = {}
        def sheet_for(side, p):
            if (side, p) in fitted:
                return fitted[(side, p)]
            H = F[side + "_final"]; lab = F[side + "_panels"]; cells = lab == p
            I, J = np.nonzero(cells)
            i0, i1 = max(0, I.min() - 2), min(S - 1, I.max() + 2); j0, j1 = max(0, J.min() - 2), min(Kn - 1, J.max() + 2)
            if int(cells.sum()) < small_panel:
                A = np.column_stack([np.ones(len(I)), cs[I], us[J]]); coef, _, _, _ = np.linalg.lstsq(A, H[I, J], rcond=None)
                c0_, c1_, u0_, u1_ = cs[i0], cs[i1], us[j0], us[j1]
                pl = lambda c_, u_: V(float(c_), float(u_), float(coef[0] + coef[1] * c_ + coef[2] * u_))
                sh = Part.Face(Part.makePolygon([pl(c0_, u0_), pl(c1_, u0_), pl(c1_, u1_), pl(c0_, u1_), pl(c0_, u0_)]))
                print("  sheet %d layer %d %s panel %d: %d cells -> a PLANE (under small_panel %d)" % (key[0], key[1], side, p, int(cells.sum()), small_panel), flush=True)
                fitted[(side, p)] = sh
                return sh
            Hp = fill_all(np.where(cells, H, np.nan)[i0:i1 + 1, j0:j1 + 1])
            if np.isnan(Hp).any():
                Hp = np.where(np.isnan(Hp), np.nanmean(Hp), Hp)
            # ACCEPTED
            ncell = int(cells.sum()); t_try = fit_tol
            if fit_mode == "interp":
                dlo, dhi = float(np.nanmin(H[I, J])), float(np.nanmax(H[I, J])); slack = max(3.0, 0.5 * (dhi - dlo))
                try:
                    sh, used_tol = fit_sheet(cs[i0:i1 + 1], us[j0:j1 + 1], Hp, t_try, step_cells, "interp")
                    npoles = sh.Surface.NbUPoles * sh.Surface.NbVPoles
                    plo, phi = _pole_range(sh)
                    rang = (plo < dlo - slack) or (phi > dhi + slack)
                    why = "" if not rang else "poles reach z %.1f..%.1f on data %.1f..%.1f" % (plo, phi, dlo, dhi)
                except Exception as e_:
                    sh = None; npoles = -1; rang = True; why = "interpolation raised %s" % e_
                if rang:
                    sh, dev = _quadric_sheet(I, J, H, cs, us, i0, i1, j0, j1)
                    print("  sheet %d layer %d %s panel %d: %d cells, interpolation REJECTED (%s) -> a QUADRIC through its cells (max dev %.2f)"
                          % (key[0], key[1], side, p, ncell, why, dev), flush=True)
                else:
                    print("  sheet %d layer %d %s panel %d: %d cells, interpolated through every %d cells, %d poles, sheet z %.1f..%.1f on data %.1f..%.1f"
                          % (key[0], key[1], side, p, ncell, step_cells, npoles, plo, phi, dlo, dhi), flush=True)
                fitted[(side, p)] = sh
                return sh
            for _k in range(3):
                sh, used_tol = fit_sheet(cs[i0:i1 + 1], us[j0:j1 + 1], Hp, t_try, step_cells, "approx")
                npoles = (sh.Surface.NbUPoles * sh.Surface.NbVPoles) if hasattr(sh, "Surface") else -1
                if npoles <= ncell or _k == 2:
                    break
                t_try *= 2.0
            if npoles > ncell:
                sh, dev = _quadric_sheet(I, J, H, cs, us, i0, i1, j0, j1)
                print("  sheet %d layer %d %s panel %d: %d cells, the fitter followed noise up to tol %.2f (%d poles) -> a QUADRIC through its cells (max dev %.2f)"
                      % (key[0], key[1], side, p, ncell, used_tol, npoles, dev), flush=True)
                fitted[(side, p)] = sh
                return sh
            print("  sheet %d layer %d %s panel %d: %d cells, fit tol %.2f%s, %d poles"
                  % (key[0], key[1], side, p, ncell, used_tol,
                     ("  (WARNING: doubled from %.2f)" % fit_tol) if used_tol > fit_tol else "", npoles), flush=True)
            fitted[(side, p)] = sh
            return sh
        def slab_for(reg, rv, pt, pb, tag):
            """the slab of ONE region under ONE top panel and over ONE bottom panel: cuts first (the
            common of two extrusions fails silently on a thin skin - build 20:30: two regions with
            fields 1.1 mm apart came back empty from the common and held 2,850 mm3 by the cuts),
            the common as the second construction.  Returns (solids, why) - solids empty on failure."""
            top_faces = _trim(sheet_for("top", pt), reg, "%s top panel %d" % (tag, pt))
            bot_faces = _trim(sheet_for("bot", pb), reg, "%s bottom panel %d" % (tag, pb))
            if not top_faces or not bot_faces:
                return [], "a sheet trims to nothing inside it"
            top_air = _fuse_all([f.extrude(V(0, 0, D)) for f in top_faces]); bot_air = _fuse_all([f.extrude(V(0, 0, -D)) for f in bot_faces])
            if top_air is None or bot_air is None:
                return [], "an extrusion has no volume"
            got = []
            try:
                slab = reg.common(region)
                slab = slab.cut(top_air).cut(bot_air)
                got = [s_ for s_ in slab.Solids if s_.Volume > 1e-6]
            except Exception as e:
                print("  %s: the slab by cuts raised [%s]" % (tag, e), flush=True); got = []
            how = "cuts"
            if not got:
                try:
                    above = _fuse_all([f.extrude(V(0, 0, -D)) for f in top_faces]); below = _fuse_all([f.extrude(V(0, 0, D)) for f in bot_faces])
                    if above is not None and below is not None:
                        slab = above.common(below).common(reg).common(region)
                        got = [s_ for s_ in slab.Solids if s_.Volume > 1e-6]
                        how = "common"
                except Exception as e:
                    print("  %s: the slab by common raised [%s]" % (tag, e), flush=True); got = []
            if got and rv == rv and sum(s_.Volume for s_ in got) > 1.05 * rv + 1.0:
                return [], "slab %.1f mm3 EXCEEDS its tube %.1f - an assembly fault" % (sum(s_.Volume for s_ in got), rv)
            if not got:
                return [], "empty slab - the sheets cross here"
            return got, how
        sols = []; n_skipped = 0
        if assembly == "tubes":
            comp = _label(valid & (pair_map >= 0), (pair_map[1:] != pair_map[:-1]), (pair_map[:, 1:] != pair_map[:, :-1]))
            ncomp = int(comp.max()) + 1
            sizes = np.bincount(comp[comp >= 0], minlength=ncomp) if ncomp > 0 else np.zeros(0, int)
            order = np.argsort(-sizes)
            print("BURRITO layer sheet %d layer %d: %d panel-pair components (largest %s cells); tubes grown by %.2f mm" % (key[0], key[1], ncomp, sizes[order[:6]].tolist(), overlap), flush=True)
            n_regions_layer = 0
            for r in order.tolist():
                m_ = comp == r
                n_ = int(m_.sum())
                if n_ < 4:
                    n_skipped += 1; continue
                I_, J_ = np.nonzero(m_)
                pt = int(tp0[I_[0], J_[0]]); pb = int(bp0[I_[0], J_[0]])
                if pt < 0 or pb < 0:
                    pid = int(pair_map[I_[0], J_[0]]); pt, pb = pid // 100003, pid % 100003
                stage = "tube"
                try:
                    tube_c = _panel_tube(m_, cs, us, sp, zf, zlen, 0.0, fp_tube, "component %d (top %d, bottom %d)" % (r, pt, pb), passes=2)
                    if tube_c is None or tube_c.Volume < 1e-6:
                        print("  component %d (top %d, bottom %d, %d cells): no tube - skipped" % (r, pt, pb, n_), flush=True); n_skipped += 1; continue
                    tube_x = _expand_plan(tube_c, overlap, zf, zlen)
                    stage = "slab"
                    got, why = slab_for(tube_x, float(tube_x.Volume), pt, pb, "component %d" % r)
                    if not got:
                        print("  component %d (top %d, bottom %d, %d cells): %s - skipped" % (r, pt, pb, n_, why), flush=True); n_skipped += 1; continue
                    print("  component %d (top %d, bottom %d, %d cells): %s -> %.1f mm3" % (r, pt, pb, n_, why, sum(s_.Volume for s_ in got)), flush=True)
                    sols += got; n_regions += 1; n_regions_layer += 1
                except Exception as e:
                    print("  component %d (top %d, bottom %d): %s raised [%s] - skipped" % (r, pt, pb, stage, e), flush=True); n_skipped += 1
            pieces_of_tube = []
        for r, reg in enumerate(pieces_of_tube):
            try:
                rv = float(reg.Volume)
            except Exception:
                rv = float("nan")
            print("  region %d/%d of sheet %d layer %d: tube %.1f mm3" % (r, len(pieces_of_tube), key[0], key[1], rv), flush=True)
            stage = "panel labels"
            try:
                rmask = _region_cells(reg, cs, us, sp, zmid)
                tp_ = F["top_panels"]; bp_ = F["bot_panels"]
                lab_ok = rmask & (tp_ >= 0) & (bp_ >= 0)
                if not lab_ok.any():
                    print("  region %d of sheet %d layer %d: %.0f mm3 tube, no panel under it - skipped" % (r, key[0], key[1], rv), flush=True)
                    n_skipped += 1; continue
                # over the
                pairs = {}
                I_, J_ = np.nonzero(lab_ok)
                for i_, j_ in zip(I_.tolist(), J_.tolist()):
                    pairs[(int(tp_[i_, j_]), int(bp_[i_, j_]))] = pairs.get((int(tp_[i_, j_]), int(bp_[i_, j_])), 0) + 1
                big = sorted([(n_, pq) for pq, n_ in pairs.items() if n_ >= 4], reverse=True)
                total = sum(pairs.values())
                if not big:
                    big = [max((n_, pq) for pq, n_ in pairs.items())]
                got_all = []; why_all = []
                if len(big) == 1 or big[0][0] >= 0.97 * total:
                    pt, pb = big[0][1]
                    stage = "slab (top panel %d, bottom panel %d)" % (pt, pb)
                    reg_x = _expand_plan(reg, overlap, zf, zlen)
                    got, why = slab_for(reg_x, float(reg_x.Volume), pt, pb, "region %d" % r)
                    got_all = got; why_all.append("(top %d, bottom %d): %s" % (pt, pb, why))
                else:
                    print("  region %d spans %d panel pairs %s - split by a dividing sheet" % (r, len(big), [(pq, n_) for n_, pq in big]), flush=True)
                    stage = "dividing sheet"
                    if not plan.get("_sheets_saved_%d_%d" % key):
                        try:
                            _od = os.path.dirname(P.get("piece_name") or P.get("out_dir") or ".")
                            K.save(Part.makeCompound(sheets), os.path.join(_od, "sheets_L%d_%d.brep" % key)); K.save(tube, os.path.join(_od, "tube_L%d_%d.brep" % key))
                            plan["_sheets_saved_%d_%d" % key] = True
                            print("  layer's %d crease sheets and its tube saved beside the job" % len(sheets), flush=True)
                        except Exception as _e:
                            print("  could not save the sheets (%s)" % _e, flush=True)
                    pair_id = np.where(lab_ok & rmask, tp_ * 100003 + bp_, -1)
                    for _fill in range(6):
                        hole = rmask & (pair_id < 0)
                        if not hole.any():
                            break
                        cand = np.full(pair_id.shape, -1)
                        for sh_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            nb_ = np.roll(pair_id, sh_, axis=(0, 1))
                            cand = np.where((cand < 0) & (nb_ >= 0), nb_, cand)
                        pair_id = np.where(hole & (cand >= 0), cand, pair_id)
                    dc = rmask[1:] & rmask[:-1] & (pair_id[1:] >= 0) & (pair_id[:-1] >= 0) & (pair_id[1:] != pair_id[:-1])
                    du = rmask[:, 1:] & rmask[:, :-1] & (pair_id[:, 1:] >= 0) & (pair_id[:, :-1] >= 0) & (pair_id[:, 1:] != pair_id[:, :-1])
                    print("  region %d: %d dividing edges" % (r, int(dc.sum() + du.sum())), flush=True)
                    subs = []
                    for ext_ in (4.0, 12.0):
                        div_sheets, _dch = crease_sheets(dc, du, cs, us, sp, zf, zlen, ext=ext_)
                        if not div_sheets:
                            break
                        try:
                            import BOPTools.SplitAPI as SA
                            subs = [s_ for s_ in SA.slice(reg, div_sheets, "Split").Solids if s_.Volume > 1e-6]
                        except Exception as e:
                            why_all.append("dividing slice raised %s" % e); subs = []
                        if len(subs) >= 2:
                            break
                        print("  region %d: the dividing sheet (ends %.0f mm past the walls) did not split it - %s" % (r, ext_, "retrying longer" if ext_ < 12.0 else "giving up"), flush=True)
                        try:
                            _od = os.path.dirname(P.get("piece_name") or P.get("out_dir") or ".")
                            K.save(reg, os.path.join(_od, "region_%d_unsplit.brep" % r)); K.save(Part.makeCompound(div_sheets), os.path.join(_od, "divider_%d.brep" % r))
                            print("  region %d and its %d dividing sheet(s) saved beside the job for looking at (chains: %s points)" % (r, len(div_sheets), [len(c_) for c_ in _dch]), flush=True)
                        except Exception as _e:
                            print("  region %d: could not save the unsplit region (%s)" % (r, _e), flush=True)
                    if len(subs) < 2:
                        why_all.append("could not be divided into its %d pairs - SKIPPED rather than built under one pair" % len(big))
                        print("  region %d of sheet %d layer %d: %s" % (r, key[0], key[1], "; ".join(why_all)), flush=True)
                        n_skipped += 1; continue
                    for k_, sub in enumerate(subs):
                        sm_ = _region_cells(sub, cs, us, sp, zmid) & lab_ok
                        if not sm_.any():
                            why_all.append("piece %d (%.1f mm3): no cells - dropped" % (k_, sub.Volume)); continue
                        cnt_ = {}
                        for i_, j_ in zip(*np.nonzero(sm_)):
                            pq_ = (int(tp_[i_, j_]), int(bp_[i_, j_])); cnt_[pq_] = cnt_.get(pq_, 0) + 1
                        (pt, pb), n_ = max(cnt_.items(), key=lambda t: t[1])
                        stage = "slab (top panel %d, bottom panel %d) in piece %d" % (pt, pb, k_)
                        sub_x = _expand_plan(sub, overlap, zf, zlen)
                        got, why = slab_for(sub_x, float(sub_x.Volume), pt, pb, "region %d piece %d (%d,%d)" % (r, k_, pt, pb))
                        got_all += got; why_all.append("piece %d (top %d, bottom %d, %d cells): %s %.1f mm3" % (k_, pt, pb, n_, why, sum(s_.Volume for s_ in got)))
                if not got_all:
                    print("  region %d of sheet %d layer %d: %s - skipped" % (r, key[0], key[1], "; ".join(why_all)), flush=True)
                    n_skipped += 1; continue
                print("  region %d of sheet %d layer %d: %s -> %.1f mm3" % (r, key[0], key[1], "; ".join(why_all), sum(s_.Volume for s_ in got_all)), flush=True)
                got = got_all
            except Exception as e:
                print("  region %d of sheet %d layer %d: %s raised [%s] - skipped" % (r, key[0], key[1], stage, e), flush=True)
                n_skipped += 1; continue
            sols += got; n_regions += 1
        if n_skipped:
            print("BURRITO layer sheet %d layer %d: %d of %d regions SKIPPED - the piece has that much missing; read the region lines" % (key[0], key[1], n_skipped, len(pieces_of_tube)), flush=True)
        n_sheets_fit += len(fitted)
        vg = [s_ for s_ in plan["sheets"] if s_["sheet"] == key[0] and s_["layer"] == key[1]]
        vg = float(vg[0]["volume_grid"]) if vg else 0.0
        vs = float(sum(s_.Volume for s_ in sols))
        pct = (100.0 * (vs - vg) / vg) if vg else 0.0
        print("BURRITO layer sheet %d layer %d SUMMARY: %d region solid(s), %d fitted sheets, volume %.1f vs grid %.1f (%+.1f mm3, %+.1f pct), faces %d, %.0f s"
              % (key[0], key[1], len(sols), len(fitted), vs, vg, vs - vg, pct, sum(len(s_.Faces) for s_ in sols), time.time() - t0), flush=True)
        if not sols:
            K.fail("burrito: sheet %d layer %d produced no solid - nothing to fuse; read the region lines above" % key)
        if vg > 0 and abs(vs - vg) > max(3.0, 0.08 * vg):
            print("BURRITO NOTE: that layer is %.0f%% off its own grid volume - look at it before trusting the fuse" % (100.0 * abs(vs - vg) / vg), flush=True)
        if vg > 0 and vs > vg + max(50.0, 0.30 * vg):
            print("BURRITO NOTE: the region solids sum to %.0f mm3 against a grid of %.0f - with panel_overlap %.2f the overlaps are counted twice here; the fused piece is what the rays judge" % (vs, vg, overlap), flush=True)
        if vg > 0 and (vg - vs) > max(50.0, 0.20 * vg):
            try:
                _keep = os.path.join(os.path.dirname(P.get("piece_name") or P.get("out_dir") or "."), "layers_REFUSED.brep")
                K.save(Part.makeCompound(pieces + sols), _keep)
                print("BURRITO layers built so far saved to %s" % _keep, flush=True)
            except Exception as _e:
                print("BURRITO could not save the layers (%s)" % _e, flush=True)
            K.fail("burrito: sheet %d layer %d built %.0f mm3 against a grid of %.0f (%+.0f%%) - a failed layer; read its region lines (SKIPPED, EXCEEDS, empty slab) before building again" % (key[0], key[1], vs, vg, 100.0 * (vs - vg) / vg))
        pieces += sols
    if not pieces:
        K.fail("burrito: nothing was built")
    crumbs = [s_ for s_ in pieces if s_.Volume < 0.5]
    if crumbs:
        print("BURRITO piece: %d crumb solid(s) under 0.5 mm3 dropped (%.2f mm3 in all)" % (len(crumbs), sum(s_.Volume for s_ in crumbs)), flush=True)
        pieces = [s_ for s_ in pieces if s_.Volume >= 0.5]
    try:
        piece = _fuse_all(pieces)
    except Exception as e:
        print("burrito: fusing the %d region solids into one piece raised [%s] - the piece goes to the body as a compound" % (len(pieces), e), flush=True)
        piece = None
    if piece is None or len(piece.Solids) == 0 or piece.Volume < 0.5 * sum(s_.Volume for s_ in pieces):
        print("burrito: fusing the %d region solids lost volume (%.0f of %.0f) - the piece goes to the body as a compound" % (len(pieces), piece.Volume if piece is not None else 0, sum(s_.Volume for s_ in pieces)), flush=True)
        try:
            piece = Part.makeCompound(pieces)
        except Exception as e:
            K.fail("burrito: the region solids cannot even be gathered into a compound (%s) - one of them is a null shape; read the region lines" % e)
    try:
        ok, msg = K.bop_ok(piece)
    except Exception as e:
        ok, msg = False, "self-intersection check raised %s" % e
    print("BURRITO piece: %d region solids, %d fitted sheets -> %d solid(s), %d faces, volume %.1f, self-intersection check %s%s  (%.0f s)"
          % (n_regions, n_sheets_fit, len(piece.Solids), len(piece.Faces), piece.Volume, "clean" if ok else "FAILED", "" if ok else " (%s)" % msg, time.time() - t0), flush=True)
    try:
        inside = piece.common(region).Volume
        print("BURRITO piece inside its region: %.1f of %.1f mm3 (%.2f%% outside)" % (inside, piece.Volume, 100.0 * max(piece.Volume - inside, 0.0) / max(piece.Volume, 1e-9)), flush=True)
    except Exception as e:
        print("BURRITO piece containment test raised %s" % e, flush=True)
    if not ok:
        out_dir = os.path.dirname(P.get("piece_name") or P.get("out_dir") or ".")
        try:
            K.save(piece, os.path.join(out_dir, "piece_REFUSED.brep")); K.save(Part.makeCompound(pieces), os.path.join(out_dir, "regions_REFUSED.brep"))
            print("BURRITO piece and its region solids saved to %s (piece_REFUSED.brep, regions_REFUSED.brep)" % out_dir, flush=True)
        except Exception as _e:
            print("BURRITO could not save the refused piece (%s)" % _e, flush=True)
        bad = []
        for k_, s_ in enumerate(pieces):
            try:
                ok_, msg_ = K.bop_ok(s_)
            except Exception as e_:
                ok_, msg_ = False, "check raised %s" % e_
            if not ok_:
                c_ = s_.BoundBox.Center
                bad.append((k_, s_, msg_, (round(c_.x, 1), round(c_.y, 1), round(c_.z, 1))))
        vbad = sum(s_.Volume for _, s_, _, _ in bad)
        print("BURRITO piece self-intersection: %d of %d region solids fail alone (%.1f mm3): %s"
              % (len(bad), len(pieces), vbad, [(k_, round(s_.Volume, 1), c_, m_[:50]) for k_, s_, m_, c_ in bad]), flush=True)
        if not bad:
            piece = Part.makeCompound(pieces)
            print("BURRITO every region solid is clean alone - the fuse made the bad face; the %d region solids go to the body as a COMPOUND" % len(pieces), flush=True)
            ok, msg = True, ""
        elif vbad <= 0.01 * piece.Volume:
            drop = {b[0] for b in bad}
            keep_ = [s_ for k_, s_ in enumerate(pieces) if k_ not in drop]
            print("BURRITO DROPPED %d region solid(s), %.1f mm3 (%.2f%% of the piece) - re-fusing the other %d" % (len(bad), vbad, 100.0 * vbad / max(piece.Volume, 1e-9), len(keep_)), flush=True)
            try:
                piece = _fuse_all(keep_); ok, msg = K.bop_ok(piece)
            except Exception as e_:
                ok, msg = False, "re-fuse raised %s" % e_
            print("BURRITO piece after the drop: %d solid(s), %d faces, volume %.1f, self-intersection check %s%s" % (len(piece.Solids), len(piece.Faces), piece.Volume, "clean" if ok else "FAILED", "" if ok else " (%s)" % msg), flush=True)
        if not ok:
            K.fail("burrito: the piece self-intersects (%s) - an assembly fault, not a lever: read the region lines above for an empty slab or a skipped region, and look at piece_REFUSED.brep / regions_REFUSED.brep beside the job" % msg)
    return _to_world(piece, ax_c, ax_u, ax_v, _spin(P)), _to_world(region, ax_c, ax_u, ax_v, _spin(P)), plan

def pass2_zones(fields, keys, in_fp, G_raw, G_fin, cs, us, sp, mmpv, change_min, margin, min_area):
    """WHERE A SECOND PASS WOULD GO.  the client: "a secondary pass that includes taking the best of both
    worlds from the original geometry and this edit."  Pass 1 is the detector: a column changed if
    any of its final surfaces moved more than `change_min` from the raw body, or if the cleaning
    added or removed more than `change_min` of material through it.  Changed columns grown by
    `margin` and traced become the sub-footprints; everything outside them keeps the body's own
    geometry.  Returns a list of (n,2) polygons in (c,u) mm, each at least `min_area` mm2."""
    S, Kn = in_fp.shape
    changed = np.zeros((S, Kn), bool)
    with np.errstate(invalid="ignore"):
        for key in keys:
            F = fields[key]
            for side in ("top", "bot"):
                d = np.abs(F[side + "_final"] - F["raw" + side])
                changed |= np.nan_to_num(d, nan=0.0) > change_min
                changed |= ~np.isnan(F[side + "_final"]) & np.isnan(F["raw" + side])
    thick = np.abs(G_fin.sum(axis=2).astype(float) - G_raw.sum(axis=2).astype(float)) * mmpv
    changed |= thick > change_min
    changed &= in_fp
    r = int(margin / sp + 1e-9)
    if r > 0:
        P2 = np.pad(changed, r, mode="constant", constant_values=False); grown = changed.copy()
        for dc in range(-r, r + 1):
            for du in range(-r, r + 1):
                if dc * dc + du * du <= r * r:
                    grown |= P2[r + dc:r + dc + S, r + du:r + du + Kn]
        changed = grown & in_fp
    comp = _label(changed, np.zeros((S - 1, Kn), bool), np.zeros((S, Kn - 1), bool))
    zones = []
    for k in range(int(comp.max()) + 1):
        cells = comp == k
        if cells.sum() * sp * sp < min_area:
            continue
        loops = trace_cells(cells)
        if not loops:
            continue
        L = max(loops, key=lambda l_: abs(_area2(l_)))
        mm = np.column_stack([cs[0] - sp / 2 + L[:, 0] * sp, us[0] - sp / 2 + L[:, 1] * sp])
        zones.append(simplify_loop(chaikin(mm, 2), 0.125 * sp) if len(mm) >= 4 else mm)
    return zones

def run_pass2(body, P):
    """SHELVED.  Pass 2 = pass 1's probe on the full footprint to find the zones of change, then the
    whole method (probe + build + replace) inside each zone in turn, the body carried forward, so
    the original geometry survives everywhere pass 1 found nothing to change.  Pass 1 stays runnable
    standalone (mode='probe' / 'build') — the client: "I would still want to keep the option to run this
    first pass standalone."  Returns the final body."""
    P1 = dict(P); P1["mode"] = "probe"
    run(body, P1)
    plan_path = os.path.join(P.get("out_dir", "."), "burrito_plan.json")
    with open(plan_path, encoding="utf-8") as fh:
        zones = json.load(fh).get("pass2_footprints", [])
    if not zones:
        print("BURRITO pass 2: no zone of change found - nothing to do", flush=True); return body
    print("BURRITO pass 2: %d zone(s); each is its own footprint, built and fused in turn" % len(zones), flush=True)
    for k, z in enumerate(zones):
        Pk = dict(P); Pk["mode"] = "build"; Pk["footprint"] = [tuple(p) for p in z]
        Pk["out_dir"] = os.path.join(P.get("out_dir", "."), "pass2_zone%02d" % k); os.makedirs(Pk["out_dir"], exist_ok=True)
        Pk["piece_name"] = os.path.join(Pk["out_dir"], "piece_zone%02d.brep" % k)
        print("BURRITO pass 2 zone %d of %d: %d-point footprint, %.0f mm2" % (k + 1, len(zones), len(z), abs(_area2(np.array(z, float)))), flush=True)
        out = run(body, Pk)
        if out is None:
            continue
        piece, region, plan = out
        K.save(piece, Pk["piece_name"])
        body = replace(body, piece, region, P.get("fuse_tol"), Pk, plan)
    return body

def ray_volume(shape, P):
    """material inside the footprint between v0..v1, by the SAME rays the probe used: overlapping
    shells count once, a lost void counts as the air it is - the measure a slicer would make.
    Returns (mm3 inside the footprint, columns that fell back to parity)."""
    ax_c, ax_u, ax_v = frame(P); poly = footprint_poly(P)
    v0 = float(P["v0"]); v1 = float(P["v1"]); sp = float(P.get("spacing", 0.5)); mmpv = float(P.get("mmpv", 0.1))
    Hv = int(math.ceil((v1 - v0) / mmpv - 1e-9))
    Vv, T, _ = K.tess(shape, 0.05)
    Vv = _rot_pts(Vv, -_spin(P))
    Vr = Vv[:, [ax_c, ax_u, ax_v]]
    cs = np.arange(poly[:, 0].min(), poly[:, 0].max() + sp * 0.5, sp); us = np.arange(poly[:, 1].min(), poly[:, 1].max() + sp * 0.5, sp)
    C, U = np.meshgrid(cs, us, indexing="ij"); sd, _ = poly_sdist(poly, C, U); in_fp = sd >= 0
    Pt = Vr[T]
    keep = ((Pt[:, :, 0].max(1) >= cs[0] - 0.5) & (Pt[:, :, 0].min(1) <= cs[-1] + 0.5) &
            (Pt[:, :, 1].max(1) >= us[0] - 0.5) & (Pt[:, :, 1].min(1) <= us[-1] + 0.5))
    T = T[keep]
    if len(T) == 0:
        return 0.0, 0
    G, n_hit, n_par = sample_grid(Vr, T, cs, us, v0, mmpv, Hv)
    return float(G[in_fp].sum() * sp * sp * mmpv), n_par

def replace(body, piece, region, fuse_tol=None, P=None, plan=None):
    """cut the footprint prism out and fuse the piece in.  The MANUFACTURED volume - what the fuse
    added beyond cut + piece - is the first build's disqualifying defect (+385 / +1865 mm3): it is
    printed, and the result is REFUSED beyond fuse_tol (default max(3 mm3, 2 % of the piece)).
    WHICH MEASURE DECIDES (2026-09-10 18:10, first v2 build): the kernel said +1789 on a 136 x 50
    footprint, the same ~1800 the first build's 9 x 15 box produced - a number that does not scale
    with the piece is the BODY's bookkeeping (an overlap counted twice, a void lost), not the fuse.
    So when P and plan are given the result is re-measured by the probe's own rays: the cut body
    must hold ~nothing inside the footprint, the result must hold what the fields said.  The rays
    decide; the kernel figure is printed, and a kernel-only discrepancy is a WARNING for kit check.
    A refused result is saved as result_REFUSED.brep so it can be looked at, never discarded."""
    t = time.time(); v0 = body.Volume
    cutr = body.cut(region)
    print("BOOKKEEPING cut region: vol %.0f (%+.0f) solids %d faces %d  %.0fs (all solids kept for the fuse)"
          % (cutr.Volume, cutr.Volume - v0, len(cutr.Solids), len(cutr.Faces), time.time() - t), flush=True)
    fz = float((P or {}).get("fuse_fuzzy", 0.0) or 0.0)
    res = cutr.fuse(piece, fz) if fz > 0 else cutr.fuse(piece)
    expect = cutr.Volume + piece.Volume; man = res.Volume - expect
    if fuse_tol is None:
        fuse_tol = max(3.0, 0.02 * piece.Volume)
    print("BURRITO fuse (kernel): cut %.1f + piece %.1f = expected %.1f; result %.1f; MANUFACTURED %+.2f mm3 (tolerance %.2f)"
          % (cutr.Volume, piece.Volume, expect, res.Volume, man, fuse_tol), flush=True)
    final = K._after(res, v0, "burrito", t)
    refuse = None
    if len(res.Solids) > 1 and abs(final.Volume - cutr.Volume) < 0.5 * piece.Volume:
        refuse = "the piece did not merge with the body (the fuse returned %d solids and the largest is the cut body)" % len(res.Solids)
    if refuse is None and P is not None and plan is not None:
        try:
            t2 = time.time()
            v_cut, np_cut = ray_volume(cutr, P); v_pc, np_pc = ray_volume(piece, P); v_res, n_par = ray_volume(final, P)
            v_fields = float(plan.get("fields_mm3", 0.0)); v_raw = float(plan.get("raw_mm3", 0.0))
            n_cols = int(plan.get("columns_hit", 0) or 0)
            print("BURRITO fuse (rays, overlaps counted once): the cut body holds %.0f mm3 inside the footprint (0 = the cut took everything, %d parity fallbacks); "
                  "the piece alone holds %.0f (%d fallbacks); the result holds %.0f, the fields said %.0f (%+.0f), the raw body had %.0f; "
                  "%d parity fallbacks on the result  %.0f s"
                  % (v_cut, np_cut, v_pc, np_pc, v_res, v_fields, v_res - v_fields, v_raw, n_par, time.time() - t2), flush=True)
            if n_par > max(50, 0.02 * max(n_cols, 1)) and n_par > 10 * max(np_pc, np_cut, 1):
                refuse = ("the fused result's skin is inconsistent inside the footprint - %d rays could not close (piece %d, cut body %d): "
                          "the fuse with the body broke face orientation; the volumes are not to be read. The piece is sound" % (n_par, np_pc, np_cut))
            elif v_cut > fuse_tol:
                refuse = "the cut left %.0f mm3 inside the footprint - the region prism did not take everything (a second shell in the body?)" % v_cut
            elif abs(v_res - v_fields) > fuse_tol:
                refuse = "the result holds %.0f mm3 inside the footprint where the fields said %.0f (%+.0f)" % (v_res, v_fields, v_res - v_fields)
            elif abs(man) > fuse_tol:
                print("BURRITO WARNING: the kernel's volume is %+.1f mm3 beyond cut + piece while the rays see the material the fields "
                      "asked for. That is the BODY's bookkeeping (an overlap counted twice or a void lost), not new material - "
                      "kit check must read solids / valid on the result before any apply, and say so on the card." % man, flush=True)
        except Exception as e:
            print("BURRITO fuse: ray re-measure failed (%s: %s) - falling back to the kernel figure" % (type(e).__name__, e), flush=True)
            refuse = ("the fuse manufactured %+.1f mm3 (kernel; rays unavailable)" % man) if abs(man) > fuse_tol else None
    elif abs(man) > fuse_tol:
        refuse = "the fuse manufactured %+.1f mm3 (kernel)" % man
    if refuse:
        out = os.path.join(os.path.dirname(str((P or {}).get("piece_name", "") or "")) or ".", "result_REFUSED.brep")
        try:
            K.save(res, out); print("BURRITO refused result saved as %s (every solid the fuse returned; for looking at, not for applying)" % out, flush=True)
        except Exception as e:
            print("BURRITO refused result could NOT be saved (%s: %s)" % (type(e).__name__, e), flush=True)
        K.fail("burrito: %s - do not apply. Look at the piece alone (kit look on the piece brep) and at %s" % (refuse, out))
    return final

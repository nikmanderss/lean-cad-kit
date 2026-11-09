"""kit_union.py - `kit union`: A DRAWN SOLID UNIONED INTO A CROP, DIRECTLY (2026-09-24; the join rewritten the same night).

the client, 2026-09-24: "Seems like there would be a faster way to put a large flat surface into a mesh and fill up to a wall"
- and, on the answer: "Yes, refine kit union. I believe it's a needed feature." The voxel route (kit mesh extract with
CC_UNION_STL) does this through a field, minutes per piece and a re-meshed box; this does it in seconds and touches
only the triangles the solid meets.

    kit union <crop.stl> --solid <solid.stl> [--solid <more.stl>] --out <out.stl> [--refine 0] [--cut]

--cut (2026-09-24, the client: "Clean up the 5.3mm groove with a cut"): the DIFFERENCE crop minus tool, by the same arrangement -
the body's faces outside the tool and the tool's faces INSIDE the body, turned over. Same checks; the result's volume
must lie between the crop's minus the tool's and the crop's.

THE P3 LOSS, AND WHY EVERY SELF-CHECK PASSED (2026-09-24, fixed the same night). `rail_P3_crop` + `rail_P_3` came out
at crop - 5677 mm3 (and crop - 7068 with the solid lifted 0.2 mm) with parity conflicts 0, bad pairs 0, closed. The
classification was right - on z rays nothing of crop u solid was missing - but the faces kept were WOUND wrongly
(windings -3/-2/+1 over 2135 mm3 of the rays). THE SOLID WAS NOT ORIENTED. `_rail_solid.py`
sweeps a profile and ear-clips two caps; for the P side the profile runs the other way round, its sides came out wound
INWARD while the caps (checked by their own normals) faced out, and the sweep's sign test - the signed volume of that
mixed mesh - read +6601 mm3 because the big cap stood 146 mm from the origin (about the solid's own centre the same mesh
reads -2879; its true volume is 5044, what rail M reads). This file's input check was "closed (each edge used twice) and
signed volume > 0", which such a mesh passes: 86 edges (the two cap rims) were run the SAME way by both their triangles.
The union kept the solid's faces as they came, so the result carried 2473 edges wound against their neighbours and its
signed volume was garbage - still closed, still manifold. THE CHECKS NOW: (1) every input is tested for ORIENTATION
(each edge run once each way); a solid that is not oriented, or oriented inward, is re-wound - breadth-first over its
edges, then each shell outward (a shell nested inside an odd number of the others is a cavity and is wound in) - and
the log says so loudly, because the drawing that made it is wrong; (2) the result may carry no edge wound against its
neighbour beyond the crop's own; (3) THE RESULT'S VOLUME must lie between the crop's and the crop's + the solid's (a
union can neither lose material nor add more than the solid holds; --cut: between the crop's - the tool's and the
crop's; measured about the world origin AND about the solid's centre, which agree for an oriented result - the P3
failure read -5677 about the one and +939 about the other). A result failing (2) or (3) under every shift is REFUSED
and written as <out>_REFUSED.stl, never as <out>. After the fix: rail_P3_crop + rail_P_3 (re-wound, 5043.2 mm3) ->
45 458.9 mm3 (+3422.7), open 0 / nm 0 / wound-against 0, on 130 k z rays equal to crop u solid (0 rays differ; the
0.043 mm of odd winding is the crop's own fold, 0.0431 in the crop), `kit splice` into base_after_rail_P2 seam +0; the
old failure replayed with the re-wind switched off is REFUSED. --cut on rail_M1_crop: boxes through the plate (-1047.4
mm3), tilted (-1460.8), floor 50 um under the plate top (-26.1), into the wall (-807.9) - each closed, ray-exact
against crop - tool.

THE CUT CURVE IS COMPUTED ONCE AND SHARED BY BOTH MESHES. The first version cut each mesh on the other's inside/outside
field separately and then tried to join the two rims: the body's rim came out as the 3 closed loops it should be, the
solid's in 7 pieces wherever a solid face grazes the body within the rework mesh's ~0.2 mm voxel roughness (the fillet's
foot at the wall, the ramp) or crosses the plate/wall crease, and nothing that pairs two independently sampled rims can
close that - near a tangency the two samplings differ in TOPOLOGY, not in position (`weld_rims` refused on the loops; a
proximity pairing at 0.4 mm left 232 + 205 vertices unpaired, 653 open edges). So the union is now an ARRANGEMENT:

  1. every body triangle x solid triangle whose boxes meet (and whose planes both straddle) is tested EXACTLY: which
     edges of each pierce the other (orientation predicates in float64 with an error bound; the few within the bound
     are redone in integer arithmetic on the inputs' binary values). Each piercing is ONE vertex, keyed by
     (edge, face), shared by every triangle on that edge;
  2. two triangles that meet share one segment between two such piercings (exactly two - anything else is counted as
     an error), and that one segment is put into both triangles: the body's cut rim and the solid's ARE the same
     polyline, vertex for vertex, by construction. No pairing, no tolerance;
  3. inside each cut triangle the segments form chains from edge to edge; they cut it into faces (a chord diagram,
     traced combinatorially - no angle sorting), each face is inside or outside the other mesh (from its corners,
     flipped across every chain), and the faces outside are ear-clipped. A closed loop inside ONE triangle (the body's
     roughness poking through a big solid face, a solid corner through a big body face) is broken first: that triangle
     is split at a point inside the loop and the arrangement is run again;
  4. every other triangle is kept or dropped whole by its corners. Corner classes come from PARITY along the mesh's
     own edges (each piercing flips it), from body vertices outside the solid's box (certainly outside) and, for the
     solid, a winding vote of ~25 of its vertices against the whole crop - exact where a ray test beside a grazing
     face is not.
The solid is moved by a generic ~1e-4 mm first, so no body vertex lies exactly on a solid face and no piercing lands on
a vertex (the rework mesh has vertices on round-number planes; so do drawn solids - without the shift a flat case gave
3849 degenerate predicates and 2448 open edges). The result is (body outside the solid) + (solid outside the body),
joined by vertex identity along the shared curve, and it is CHECKED after a float32 round trip - what `kit splice`
reads: open and non-manifold edges must equal the crop's own, or the run is repeated with another shift (a float32
collision of two curve vertices) and then reported NOT closed with the open loops' boxes. A closed CAVITY the union
creates (a drawn face spanning a pocket of the body) is reported with its volume and box - MJF traps powder in it.

Measured 2026-09-24 on the rail (rail_M1_crop 164 k triangles + rail_M_1f 3952): 2.3 s, one pass, 0 exact fallbacks,
0 open / 0 non-manifold (the crop's own: 0 / 0), +3525 mm3; on 523 k z-rays the union equals crop u solid to 0.0005 mm
and winds 0/1 only; `kit splice` into R31_reworked: seam +0 open edges. Also closed and ray-exact: the P rail, the
17 k-triangle rail, a rail sunk 0.45 mm, boxes flat on / 5 um into / tilted across the plate top and across the wall,
and synthetic rough heightfields under 12-triangle boxes (55-259 loops split, both ways round).

The solid must be CLOSED (checked; refused otherwise) and should be wound OUTWARD (checked by orientation, not by the
sign of a volume; re-wound when it is not); one that does not reach the body's surface is refused. Faces of
the solid may touch or graze the body anywhere; exact coplanar contact is resolved by the shift (the solid's face ends
up 1e-4 mm on one side), so keep designed contact faces 0.1 mm into the body when they are meant to merge. `--refine L`
splits the solid's edges longer than L first (not needed for the join any more; default 0). numpy (+ scipy for the
cavity count when present); no kernel.
"""
import os, sys, time, json, collections
for _v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitlib_render as R

SHIFTS = [np.array([0.4412, 0.6397, 0.6293]) * 1.0e-4,
          np.array([-0.5813, 0.2944, 0.7584]) * 1.7e-4,
          np.array([0.3301, -0.7127, 0.6189]) * 2.3e-4]
_EPS_O3D = 1e-13


def load(path):
    """an STL, index-welded like the splice welds it (1e-6 keys) - first-occurrence coordinates kept EXACTLY"""
    V, T = R.read_stl(path)
    V, T, _, _ = R._weld(np.asarray(V, float), np.asarray(T, int), [], 1e-6)
    return V, T


def closed_outward(V, T):
    """(signed volume, open-or-nonmanifold edge count)"""
    P = V[T]
    vol = float((np.cross(P[:, 1], P[:, 2]) * P[:, 0]).sum() / 6.0)
    e = np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    return vol, int((cnt != 2).sum())


def _edges(T):
    """unique undirected edges (sorted vertex pairs) and each triangle's three edge ids (edge k runs T[k] -> T[k+1])"""
    e = np.stack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], axis=1).reshape(-1, 2)
    u, inv = np.unique(np.sort(e, axis=1), axis=0, return_inverse=True)
    return u, np.asarray(inv).reshape(-1, 3)


def wound_against(T):
    """edges that BOTH their triangles run the same way. A closed mesh is ORIENTED only when there are none - and only
    then is its signed volume its volume: `closed_outward` counts each edge's triangles, not their directions, and a
    mesh with its sides wound in and its caps out passes it with a volume that depends on where the origin is (P3)."""
    T = np.asarray(T, np.int64)
    d = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    u, inv = np.unique(np.sort(d, axis=1), axis=0, return_inverse=True)
    inv = np.asarray(inv).reshape(-1)
    nt = np.bincount(inv, minlength=len(u))
    nf = np.bincount(inv, weights=(d[:, 0] < d[:, 1]).astype(float), minlength=len(u))
    return int(((nt == 2) & (nf != 1)).sum())


def signed_volume_about(V, T, o):
    P = np.asarray(V, float)[np.asarray(T, np.int64)] - np.asarray(o, float)
    return float((np.cross(P[:, 1], P[:, 2]) * P[:, 0]).sum() / 6.0)


def orient_outward(V, T):
    """a CLOSED manifold mesh re-wound: consistently across every edge (breadth-first over the triangles), then each
    shell outward - a shell nested inside an odd number of the others is a cavity and is wound inward. Returns
    (T, triangles turned over, shells). Raises on an open or non-orientable mesh."""
    T0 = np.asarray(T, np.int64); T = T0.copy(); n = len(T)
    d = np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
    tri = np.tile(np.arange(n), 3)
    u, inv = np.unique(np.sort(d, axis=1), axis=0, return_inverse=True)
    inv = np.asarray(inv).reshape(-1)
    if (np.bincount(inv, minlength=len(u)) != 2).any():
        raise RuntimeError("the mesh is not closed and manifold - it cannot be oriented")
    o = np.argsort(inv, kind="stable"); h1, h2 = o[0::2], o[1::2]
    E = np.stack([tri[h1], tri[h2]], 1)
    par = (d[h1, 0] == d[h2, 0]).astype(np.int64)
    flip, comp, nc, conf = _two_colour(n, E, par, np.full(n, -1, np.int64))
    if conf:
        raise RuntimeError("the mesh is not orientable (%d edges contradict every winding)" % conf)
    T[flip == 1] = T[flip == 1][:, ::-1]
    parts = [np.where(comp == k)[0] for k in range(nc)]
    for k, tk in enumerate(parts):
        vol = signed_volume_about(V, T[tk], np.asarray(V, float)[np.unique(T[tk])].mean(0))
        depth = 0
        if 1 < nc <= 50:
            p = np.asarray(V, float)[T[tk[0], 0]]
            depth = sum(int(_inside_brute(p, np.asarray(V, float), T[tj])[0]) for j, tj in enumerate(parts) if j != k)
        if (vol < 0) != (depth % 2 == 1):
            T[tk] = T[tk][:, ::-1]
    changed = int((~np.all(T == T0, axis=1)).sum())
    return T, changed, nc


def shells(V, T):
    """the mesh's connected pieces: [(triangles, signed volume, box lo, box hi)], largest first. A piece with a
    NEGATIVE volume is a closed cavity (an inward-facing shell inside the part)."""
    n = len(V)
    e = np.vstack([T[:, [0, 1]], T[:, [1, 2]]])
    try:
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import connected_components
        _nc, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    except ImportError:
        lab = np.arange(n)
        while True:
            old = lab.copy()
            np.minimum.at(lab, e[:, 0], lab[e[:, 1]]); np.minimum.at(lab, e[:, 1], lab[e[:, 0]])
            lab = lab[lab]
            if np.array_equal(lab, old):
                break
    tl = lab[T[:, 0]]
    out = []
    for k in np.unique(tl):
        Tk = T[tl == k]
        vol, _b = closed_outward(V, Tk)
        P = V[np.unique(Tk)]
        out.append((int(len(Tk)), vol, P.min(0), P.max(0)))
    out.sort(key=lambda r: -abs(r[1]))
    return out


def open_loops(V, T):
    """the open edges of an index-welded mesh as loops (connected pieces), each with its vertex count and box"""
    e = np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1)
    u, c = np.unique(e, axis=0, return_counts=True)
    bad = u[c != 2]
    out = []
    for comp in R.rim_loops([tuple(x) for x in bad]):
        P = V[np.asarray(comp)]
        out.append((len(comp), P.min(0), P.max(0)))
    return out


def _o3d_float(A, B, C, D):
    """det[B-A, C-A, D-A] per row and its error bound"""
    e = B - A; f = C - A; g = D - A
    m0 = f[:, 1] * g[:, 2]; m1 = f[:, 2] * g[:, 1]; m2 = f[:, 2] * g[:, 0]
    m3 = f[:, 0] * g[:, 2]; m4 = f[:, 0] * g[:, 1]; m5 = f[:, 1] * g[:, 0]
    det = e[:, 0] * (m0 - m1) + e[:, 1] * (m2 - m3) + e[:, 2] * (m4 - m5)
    bnd = _EPS_O3D * (np.abs(e[:, 0]) * (np.abs(m0) + np.abs(m1)) + np.abs(e[:, 1]) * (np.abs(m2) + np.abs(m3))
                      + np.abs(e[:, 2]) * (np.abs(m4) + np.abs(m5)))
    return det, bnd


def _o3d_exact(a, b, c, d):
    q = [float(x).as_integer_ratio() for x in (a[0], a[1], a[2], b[0], b[1], b[2], c[0], c[1], c[2], d[0], d[1], d[2])]
    D = max(den for _n, den in q)
    ax, ay, az, bx, by, bz, cx, cy, cz, dx, dy, dz = [n * (D // den) for n, den in q]
    ex, ey, ez = bx - ax, by - ay, bz - az
    fx, fy, fz = cx - ax, cy - ay, cz - az
    gx, gy, gz = dx - ax, dy - ay, dz - az
    det = ex * (fy * gz - fz * gy) + ey * (fz * gx - fx * gz) + ez * (fx * gy - fy * gx)
    return (det > 0) - (det < 0)


def orient3d(A, B, C, D, st):
    """EXACT sign of det[B-A, C-A, D-A] per row (+1: D on the side (B-A)x(C-A) points to), and the float value"""
    det, bnd = _o3d_float(A, B, C, D)
    s = np.sign(det).astype(np.int64)
    unsure = np.where(np.abs(det) <= bnd)[0]
    for i in unsure:
        s[i] = _o3d_exact(A[i], B[i], C[i], D[i])
    st["exact"] = st.get("exact", 0) + len(unsure)
    return s, det


def _pierce(Pa, Pb, F0, F1, F2, st):
    """edge a-b against triangle F0 F1 F2, rows paired: (hit, t along a->b, degenerate). A hit needs a and b STRICTLY on
    opposite sides of the plane and the line through the triangle's interior (the three edge orientations alike)."""
    sa, da = orient3d(F0, F1, F2, Pa, st)
    sb, db = orient3d(F0, F1, F2, Pb, st)
    deg = (sa == 0) != (sb == 0)
    cand = np.where(sa * sb < 0)[0]
    hit = np.zeros(len(Pa), bool)
    if len(cand):
        a, b = Pa[cand], Pb[cand]
        s0 = orient3d(a, b, F0[cand], F1[cand], st)[0]
        s1 = orient3d(a, b, F1[cand], F2[cand], st)[0]
        s2 = orient3d(a, b, F2[cand], F0[cand], st)[0]
        hit[cand] = ((s0 > 0) & (s1 > 0) & (s2 > 0)) | ((s0 < 0) & (s1 < 0) & (s2 < 0))
        deg[cand] |= (s0 == 0) | (s1 == 0) | (s2 == 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(hit, da / np.where(da - db == 0, 1.0, da - db), 0.0)
    return hit, np.clip(t, 0.0, 1.0), deg


def _box_pairs(loA, hiA, loB, hiB):
    """every (i, j) with box A_i meeting box B_j: B's boxes filed in a grid, A's looked up in it"""
    extA = (hiA - loA).max(1); extB = (hiB - loB).max(1)
    cell = max(float(np.median(extA)), float(np.median(extB)), 0.05)
    org = np.minimum(loA.min(0), loB.min(0)) - cell
    n = np.ceil((np.maximum(hiA.max(0), hiB.max(0)) - org) / cell).astype(np.int64) + 2

    def cells(lo, hi):
        i0 = np.floor((lo - org) / cell).astype(np.int64); i1 = np.floor((hi - org) / cell).astype(np.int64)
        span = i1 - i0 + 1; cnt = span.prod(1)
        own = np.repeat(np.arange(len(lo)), cnt)
        k = np.arange(int(cnt.sum())) - np.repeat(np.cumsum(cnt) - cnt, cnt)
        s1 = np.repeat(span[:, 1], cnt); s2 = np.repeat(span[:, 2], cnt)
        ia = np.repeat(i0[:, 0], cnt) + k // (s1 * s2)
        ib = np.repeat(i0[:, 1], cnt) + (k // s2) % s1
        ic = np.repeat(i0[:, 2], cnt) + k % s2
        return own, (ia * n[1] + ib) * n[2] + ic
    ownB, keyB = cells(loB, hiB)
    o = np.argsort(keyB, kind="stable"); keyB = keyB[o]; ownB = ownB[o]
    ownA, keyA = cells(loA, hiA)
    first = np.searchsorted(keyB, keyA, "left"); cnt = np.searchsorted(keyB, keyA, "right") - first
    ia = np.repeat(ownA, cnt)
    k = np.arange(int(cnt.sum())) - np.repeat(np.cumsum(cnt) - cnt, cnt)
    jb = ownB[np.repeat(first, cnt) + k]
    key = np.unique(ia.astype(np.int64) * len(loB) + jb)
    i = key // len(loB); j = key % len(loB)
    ok = np.all(hiA[i] >= loB[j], 1) & np.all(loA[i] <= hiB[j], 1)
    return i[ok], j[ok]


def _straddle(F0, F1, F2, P0, P1, P2):
    """False where all three points are CERTAINLY on one side of the plane F0 F1 F2 (float, with the error bound)"""
    pos = np.ones(len(F0), bool); neg = np.ones(len(F0), bool)
    for P in (P0, P1, P2):
        d, b = _o3d_float(F0, F1, F2, P)
        pos &= d > b; neg &= d < -b
    return ~(pos | neg)


def _two_colour(nv, E, par, seed):
    """inside/outside by PARITY over a mesh's edges: seed[v] in {0, 1} fixes a vertex (-1 free); crossing an edge flips
    the class when the edge's parity is 1. Multi-source BFS from the seeds, then each unseeded component from its first
    vertex (class 0, a RELATIVE labelling - the caller fixes its sign). Returns (cls, comp, n_comp, conflicts)."""
    E = np.asarray(E, np.int64); par = np.asarray(par, np.int64) & 1
    src = np.r_[E[:, 0], E[:, 1]]; dst = np.r_[E[:, 1], E[:, 0]]; pp = np.r_[par, par]
    o = np.argsort(src, kind="stable")
    dst = dst[o].tolist(); pp = pp[o].tolist()
    st = np.searchsorted(src[o], np.arange(nv + 1)).tolist()
    cls = [-1] * nv; comp = [-1] * nv
    dq = collections.deque()
    for v in np.where(np.asarray(seed) >= 0)[0].tolist():
        cls[v] = int(seed[v]); dq.append(v)

    def run():
        while dq:
            u = dq.popleft(); cu = cls[u]; ku = comp[u]
            for k in range(st[u], st[u + 1]):
                w = dst[k]
                if cls[w] < 0:
                    cls[w] = cu ^ pp[k]; comp[w] = ku; dq.append(w)
    run()
    has = np.zeros(nv, bool); has[E.ravel()] = True
    ncomp = 0
    for v in np.where(has)[0].tolist():
        if cls[v] < 0:
            cls[v] = 0; comp[v] = ncomp; ncomp += 1; dq.append(v); run()
    cls = np.asarray(cls, np.int64); comp = np.asarray(comp, np.int64)
    lab = (cls[E[:, 0]] >= 0) & (cls[E[:, 1]] >= 0)
    conflicts = int(((cls[E[lab, 0]] ^ cls[E[lab, 1]]) != par[lab]).sum())
    return cls, comp, ncomp, conflicts


def _inside_brute(P, V, T):
    """winding along x, y and z, majority of three, for a FEW points against EVERY triangle (no grid, no clipping)"""
    P = np.asarray(P, float).reshape(-1, 3)
    A = V[T[:, 0]]; B = V[T[:, 1]]; C = V[T[:, 2]]
    lo = np.minimum(np.minimum(A, B), C); hi = np.maximum(np.maximum(A, B), C)
    jit = (1.41421356e-5, 1.73205081e-5, 1.1180339887e-5)
    out = np.zeros(len(P), bool)
    for i, p in enumerate(P):
        votes = 0
        for ax in range(3):
            b_, c_ = [k for k in range(3) if k != ax]
            pb = p[b_] + jit[b_]; pc = p[c_] + jit[c_]
            m = np.where((lo[:, b_] <= pb) & (hi[:, b_] >= pb) & (lo[:, c_] <= pc) & (hi[:, c_] >= pc) & (hi[:, ax] > p[ax]))[0]
            if not len(m):
                continue
            a = A[m]; e1 = B[m] - a; e2 = C[m] - a
            den = e1[:, b_] * e2[:, c_] - e2[:, b_] * e1[:, c_]
            ok = den != 0
            dd = np.where(ok, den, 1.0)
            wb = pb - a[:, b_]; wc = pc - a[:, c_]
            u = (wb * e2[:, c_] - e2[:, b_] * wc) / dd
            v = (e1[:, b_] * wc - wb * e1[:, c_]) / dd
            hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1)
            pa = a[:, ax] + u * e1[:, ax] + v * e2[:, ax]
            if int(np.sign(den[hit & (pa > p[ax])]).sum()) != 0:
                votes += 1
        out[i] = votes >= 2
    return out


def _basis(P0, P1, P2):
    e1 = P1 - P0; n = np.cross(e1, P2 - P0); l1 = float(np.linalg.norm(e1)); ln = float(np.linalg.norm(n))
    if l1 == 0 or ln == 0:
        return np.array([1.0, 0, 0]), np.array([0, 1.0, 0])
    e1 = e1 / l1
    return e1, np.cross(n / ln, e1)


def _ear(ids, xy):
    """triangles of a simple polygon given in the winding that must be kept. NEVER FAILS: when no clean ear exists (a
    near-degenerate sliver face) the most convex corner is clipped anyway, so every polygon edge is still used exactly
    once - the seam's closure does not depend on the geometry being well conditioned."""
    ids = list(ids); n = len(ids)
    if n < 3:
        return []
    if n == 3:
        return [tuple(ids)]
    xy = np.asarray(xy, float)
    span = float(np.ptp(xy, axis=0).max()) or 1.0
    tol = 1e-12 * span * span; tolc = 1e-12 * span
    idx = list(range(n)); out = []; ptr = 0
    while len(idx) > 3:
        k = len(idx); I = np.asarray(idx)
        Q = xy[I]; A = np.roll(Q, 1, axis=0); C = np.roll(Q, -1, axis=0)
        cr = (Q[:, 0] - A[:, 0]) * (C[:, 1] - A[:, 1]) - (Q[:, 1] - A[:, 1]) * (C[:, 0] - A[:, 0])
        pick = -1
        for s in range(k):
            a = (ptr + s) % k
            if cr[a] <= tol:
                continue
            p0, p1, p2 = A[a], Q[a], C[a]
            d0 = (p1[0] - p0[0]) * (Q[:, 1] - p0[1]) - (p1[1] - p0[1]) * (Q[:, 0] - p0[0])
            d1 = (p2[0] - p1[0]) * (Q[:, 1] - p1[1]) - (p2[1] - p1[1]) * (Q[:, 0] - p1[0])
            d2 = (p0[0] - p2[0]) * (Q[:, 1] - p2[1]) - (p0[1] - p2[1]) * (Q[:, 0] - p2[0])
            blk = (d0 >= -tol) & (d1 >= -tol) & (d2 >= -tol)
            blk[[(a - 1) % k, a, (a + 1) % k]] = False
            blk &= ~((np.abs(Q - p0).max(1) <= tolc) | (np.abs(Q - p1).max(1) <= tolc) | (np.abs(Q - p2).max(1) <= tolc))
            if not blk.any():
                pick = a; break
        if pick < 0:
            pick = int(np.argmax(cr))
        out.append((ids[idx[(pick - 1) % k]], ids[idx[pick]], ids[idx[(pick + 1) % k]]))
        idx.pop(pick); ptr = pick % (k - 1)
    out.append((ids[idx[0]], ids[idx[1]], ids[idx[2]]))
    return out


def _tri_faces(c, ccls, elist, segs, Vall, keep=0, turn=False):
    """ONE cut triangle. c: its 3 corner ids (in its winding), ccls: their classes (0 outside the other mesh);
    elist[k]: the piercing ids on edge c[k] -> c[k+1], in that order; segs: its curve segments (id pairs).
    Returns ("ok", triangles of the faces of class `keep` - 0 outside, 1 inside the other mesh - turned over when
    `turn`), ("loops", [closed loops of inner ids]) or ("err", why)."""
    bset = set(x for L in elist for x in L)
    adj = {}
    for a, b in segs:
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    for v, nb in adj.items():
        if len(nb) != (1 if v in bset else 2):
            return "err", "a %s node of degree %d" % ("edge" if v in bset else "inner", len(nb))
    if any(x not in adj for x in bset):
        return "err", "an edge node with no segment"
    chains, at, seen = [], {}, set()
    for L in elist:
        for s in L:
            if s in seen:
                continue
            ch = [s]; seen.add(s); prev, cur = s, adj[s][0]; g = 0
            while cur not in bset:
                ch.append(cur); seen.add(cur)
                n0, n1 = adj[cur]
                prev, cur = cur, (n1 if n0 == prev else n0)
                g += 1
                if g > len(adj) + 2:
                    return "err", "a chain that does not end"
            ch.append(cur); seen.add(cur)
            if cur == s:
                return "err", "a chain back to its start"
            at[ch[0]] = (len(chains), False); at[ch[-1]] = (len(chains), True); chains.append(ch)
    loops = []
    for v in adj:
        if v in seen:
            continue
        lp = [v]; seen.add(v); prev, cur = v, adj[v][0]; g = 0
        while cur != v:
            lp.append(cur); seen.add(cur)
            n0, n1 = adj[cur]
            prev, cur = cur, (n1 if n0 == prev else n0)
            g += 1
            if g > len(adj) + 2:
                return "err", "a loop that does not close"
        loops.append(lp)
    if loops:
        return "loops", loops
    seq = [c[0]] + list(elist[0]) + [c[1]] + list(elist[1]) + [c[2]] + list(elist[2])
    M = len(seq); pos = {v: i for i, v in enumerate(seq)}
    iv = sorted((min(pos[ch[0]], pos[ch[-1]]), max(pos[ch[0]], pos[ch[-1]])) for ch in chains)
    for i in range(len(iv)):
        for j in range(i + 1, len(iv)):
            if iv[i][0] < iv[j][0] < iv[i][1] < iv[j][1]:
                return "err", "two chains cross"
    used = [False] * M; faces = []
    for s0 in range(M):
        if used[s0]:
            continue
        poly, uses, i, g = [], [], s0, 0
        while True:
            used[i] = True; poly.append(seq[i])
            j = (i + 1) % M
            if seq[j] in at:
                ci, rev = at[seq[j]]
                ch = chains[ci][::-1] if rev else chains[ci]
                poly.extend(ch[:-1]); uses.append(ci)
                j = pos[ch[-1]]
            i = j
            if i == s0:
                break
            g += 1
            if g > M + 2:
                return "err", "a face that does not close"
        faces.append((poly, uses))
    corner = {c[0]: ccls[0], c[1]: ccls[1], c[2]: ccls[2]}
    fcls = []
    for poly, _u in faces:
        cs = {corner[x] for x in poly if x in corner}
        if len(cs) > 1:
            return "err", "corners of one face disagree"
        fcls.append(cs.pop() if cs else -1)
    sides = {}
    for fi, (_p, uses) in enumerate(faces):
        for ci in uses:
            sides.setdefault(ci, []).append(fi)
    if any(len(fs) != 2 for fs in sides.values()):
        return "err", "a chain not between two faces"
    changed = True
    while changed:
        changed = False
        for f1, f2 in sides.values():
            if fcls[f1] >= 0 and fcls[f2] < 0:
                fcls[f2] = 1 - fcls[f1]; changed = True
            elif fcls[f2] >= 0 and fcls[f1] < 0:
                fcls[f1] = 1 - fcls[f2]; changed = True
            elif fcls[f1] >= 0 and fcls[f1] == fcls[f2]:
                return "err", "both sides of a chain alike"
    if min(fcls) < 0:
        return "err", "a face with no class"
    P0 = Vall[c[0]]; e1, e2 = _basis(P0, Vall[c[1]], Vall[c[2]])
    tris = []
    for (poly, _u), fc in zip(faces, fcls):
        if fc != keep:
            continue
        if len(poly) == 3:
            tris.append(tuple(poly)); continue
        Q = Vall[np.asarray(poly)] - P0
        tris.extend(_ear(poly, np.c_[Q @ e1, Q @ e2]))
    if turn:
        tris = [(a, d, b) for a, b, d in tris]
    return "ok", tris


def _loop_point(loop, c, Vall):
    """a point strictly inside a closed loop lying in triangle c: the centroid of the loop's largest ear"""
    P0 = Vall[c[0]]; e1, e2 = _basis(P0, Vall[c[1]], Vall[c[2]])
    Q = Vall[np.asarray(loop)] - P0; xy = np.c_[Q @ e1, Q @ e2]
    a2 = float(np.sum(xy[:, 0] * np.roll(xy[:, 1], -1) - np.roll(xy[:, 0], -1) * xy[:, 1]))
    order = list(range(len(loop))) if a2 >= 0 else list(range(len(loop)))[::-1]
    tr = _ear(order, xy[order])
    ar = [abs((xy[b][0] - xy[a][0]) * (xy[d][1] - xy[a][1]) - (xy[b][1] - xy[a][1]) * (xy[d][0] - xy[a][0])) for a, b, d in tr]
    a, b, d = tr[int(np.argmax(ar))]
    m = (xy[a] + xy[b] + xy[d]) / 3.0
    return P0 + m[0] * e1 + m[1] * e2


def _split_tris(V, T, req):
    """each requested triangle split at its points (1 -> 3 per point, into the sub-triangle holding it); winding kept"""
    V = np.asarray(V, float); T = np.asarray(T, int)
    newV, newT = [], []
    drop = np.zeros(len(T), bool)
    for t, pts in req.items():
        c = [int(x) for x in T[t]]
        P0 = V[c[0]]; e1, e2 = _basis(P0, V[c[1]], V[c[2]])
        xy = {v: np.array([(V[v] - P0) @ e1, (V[v] - P0) @ e2]) for v in c}
        sub = [tuple(c)]
        for p in pts:
            vid = len(V) + len(newV); newV.append(np.asarray(p, float))
            q = np.array([(p - P0) @ e1, (p - P0) @ e2]); xy[vid] = q
            best, bi = -np.inf, 0
            for si, (a, b, d) in enumerate(sub):
                A_, B_, C_ = xy[a], xy[b], xy[d]
                den = (B_[0] - A_[0]) * (C_[1] - A_[1]) - (B_[1] - A_[1]) * (C_[0] - A_[0])
                if den == 0:
                    continue
                l1 = ((q[0] - A_[0]) * (C_[1] - A_[1]) - (q[1] - A_[1]) * (C_[0] - A_[0])) / den
                l2 = ((B_[0] - A_[0]) * (q[1] - A_[1]) - (B_[1] - A_[1]) * (q[0] - A_[0])) / den
                m = min(1.0 - l1 - l2, l1, l2)
                if m > best:
                    best, bi = m, si
            a, b, d = sub.pop(bi)
            sub += [(a, b, vid), (b, d, vid), (d, a, vid)]
        drop[t] = True; newT.extend(sub)
    return np.vstack([V, np.asarray(newV, float).reshape(-1, 3)]), np.vstack([T[~drop], np.asarray(newT, int).reshape(-1, 3)])


def _arrange(VB, TB, VS, TS, say, cut=False):
    """one pass: (V, T, report) when every cut triangle resolved, else the split requests for the loops found.
    The body keeps its faces outside the solid; the solid keeps its faces outside the body (union) or, for a cut,
    its faces INSIDE the body, turned over."""
    t0 = time.time(); st = {}; rep = {}
    keepS = 1 if cut else 0
    lo = VS.min(0) - 1e-3; hi = VS.max(0) + 1e-3
    PB = VB[TB]; blo = PB.min(1); bhi = PB.max(1)
    near = np.where(np.all(bhi >= lo, 1) & np.all(blo <= hi, 1))[0]
    TBn = TB[near]
    PS = VS[TS]; slo = PS.min(1); shi = PS.max(1)
    if len(near):
        ib, js = _box_pairs(blo[near] - 1e-9, bhi[near] + 1e-9, slo - 1e-9, shi + 1e-9)
    else:
        ib, js = np.zeros(0, np.int64), np.zeros(0, np.int64)
    n_box = len(ib)
    B0, B1, B2 = VB[TBn[ib, 0]], VB[TBn[ib, 1]], VB[TBn[ib, 2]]
    S0, S1, S2 = VS[TS[js, 0]], VS[TS[js, 1]], VS[TS[js, 2]]
    ok = _straddle(S0, S1, S2, B0, B1, B2) & _straddle(B0, B1, B2, S0, S1, S2)
    ib, js = ib[ok], js[ok]
    EB, eidB = _edges(TBn); ES, eidS = _edges(TS)
    nS, nBn = len(TS), len(TBn)
    cb = np.unique(np.concatenate([eidB[ib, k].astype(np.int64) * nS + js for k in range(3)])) if len(ib) else np.zeros(0, np.int64)
    cbe, cbf = cb // nS, cb % nS
    hB, tB, dB = _pierce(VB[EB[cbe, 0]], VB[EB[cbe, 1]], VS[TS[cbf, 0]], VS[TS[cbf, 1]], VS[TS[cbf, 2]], st)
    cs = np.unique(np.concatenate([eidS[js, k].astype(np.int64) * nBn + ib for k in range(3)])) if len(ib) else np.zeros(0, np.int64)
    cse, csf = cs // nBn, cs % nBn
    hS, tS, dS = _pierce(VS[ES[cse, 0]], VS[ES[cse, 1]], VB[TBn[csf, 0]], VB[TBn[csf, 1]], VB[TBn[csf, 2]], st)
    rep.update({"near_body_triangles": int(nBn), "box_pairs": int(n_box), "straddling_pairs": int(len(ib)),
                "body_edge_piercings": int(hB.sum()), "solid_edge_piercings": int(hS.sum()),
                "exact_predicates": int(st.get("exact", 0)), "degenerate": int(dB.sum() + dS.sum())})
    nVB, nVS = len(VB), len(VS); off = nVB + nVS
    nodeB = np.full(len(cb), -1, np.int64); nodeB[hB] = off + np.arange(int(hB.sum()))
    nodeS = np.full(len(cs), -1, np.int64); nodeS[hS] = off + int(hB.sum()) + np.arange(int(hS.sum()))
    a_, b_ = EB[cbe[hB], 0], EB[cbe[hB], 1]
    XB = VB[a_] + tB[hB, None] * (VB[b_] - VB[a_])
    a2, b2 = ES[cse[hS], 0], ES[cse[hS], 1]
    XS = VS[a2] + tS[hS, None] * (VS[b2] - VS[a2])
    Vall = np.vstack([VB, VS, XB, XS])
    kb = [np.searchsorted(cb, eidB[ib, k].astype(np.int64) * nS + js) for k in range(3)]
    ks = [np.searchsorted(cs, eidS[js, k].astype(np.int64) * nBn + ib) for k in range(3)]
    nodes = np.stack([nodeB[kb[0]], nodeB[kb[1]], nodeB[kb[2]], nodeS[ks[0]], nodeS[ks[1]], nodeS[ks[2]]], 1) if len(ib) else np.zeros((0, 6), np.int64)
    cnt = (nodes >= 0).sum(1)
    rep["pairs_not_0_or_2"] = int(((cnt != 0) & (cnt != 2)).sum())
    two = np.where(cnt == 2)[0]
    srt = np.sort(nodes[two], axis=1)[:, -2:]
    segB, segS = {}, {}
    for r, (u, v) in zip(two.tolist(), srt.tolist()):
        segB.setdefault(int(ib[r]), []).append((u, v)); segS.setdefault(int(js[r]), []).append((u, v))
    rep["segments"] = int(len(two))
    edB, edS = {}, {}
    o = np.lexsort((tB[hB], cbe[hB]))
    for e_, n_ in zip(cbe[hB][o].tolist(), nodeB[hB][o].tolist()):
        edB.setdefault(e_, []).append(n_)
    o = np.lexsort((tS[hS], cse[hS]))
    for e_, n_ in zip(cse[hS][o].tolist(), nodeS[hS][o].tolist()):
        edS.setdefault(e_, []).append(n_)
    parB = np.zeros(len(EB), np.int64); np.add.at(parB, cbe[hB], 1)
    seedB = np.full(nVB, -1, np.int64)
    vn = np.unique(TBn)
    outb = np.any((VB[vn] < lo) | (VB[vn] > hi), axis=1)
    seedB[vn[outb]] = 0
    clsB, compB, ncB, confB = _two_colour(nVB, EB, parB, seedB)
    for k in range(ncB):
        vk = np.where(compB == k)[0]
        if _inside_brute(VB[vk[:1]], VS, TS)[0]:
            clsB[vk] ^= 1
    parS = np.zeros(len(ES), np.int64); np.add.at(parS, cse[hS], 1)
    clsS, compS, ncS, confS = _two_colour(nVS, ES, parS, np.full(nVS, -1, np.int64))
    agree = []
    rng = np.random.RandomState(7)
    for k in range(ncS):
        vk = np.where(compS == k)[0]
        smp = vk if len(vk) <= 25 else rng.choice(vk, 25, replace=False)
        w = _inside_brute(VS[smp], VB, TB).astype(np.int64)
        n_eq = int((w == clsS[smp]).sum())
        if n_eq * 2 < len(smp):
            clsS[vk] ^= 1; n_eq = len(smp) - n_eq
        agree.append("%d/%d" % (n_eq, len(smp)))
    rep.update({"parity_conflicts": int(confB + confS), "solid_winding_agreement": agree,
                "solid_vertices_inside_body": int((clsS == 1).sum())})
    out, splitB, splitS, errs = [], {}, {}, collections.Counter()
    err_boxes = []
    for i, sg in segB.items():
        c = [int(x) for x in TBn[i]]
        el = []
        for k in range(3):
            e = int(eidB[i, k]); L = edB.get(e, [])
            el.append(L if c[k] == EB[e, 0] else L[::-1])
        kind, res = _tri_faces(c, [int(clsB[x]) for x in c], el, sg, Vall)
        if kind == "ok":
            out.extend(res)
        elif kind == "loops":
            splitB[int(near[i])] = [_loop_point(lp, c, Vall) for lp in res]
        else:
            errs["body: " + res] += 1; err_boxes.append(Vall[c].mean(0))
    for j, sg in segS.items():
        cS = [int(x) for x in TS[j]]; c = [x + nVB for x in cS]
        el = []
        for k in range(3):
            e = int(eidS[j, k]); L = edS.get(e, [])
            el.append(L if cS[k] == ES[e, 0] else L[::-1])
        kind, res = _tri_faces(c, [int(clsS[x]) for x in cS], el, sg, Vall, keep=keepS, turn=cut)
        if kind == "ok":
            out.extend(res)
        elif kind == "loops":
            splitS[j] = [_loop_point(lp, c, Vall) for lp in res]
        else:
            errs["solid: " + res] += 1; err_boxes.append(Vall[c].mean(0))
    rep.update({"cut_body_triangles": len(segB), "cut_solid_triangles": len(segS),
                "loops_split": sum(len(v) for v in splitB.values()) + sum(len(v) for v in splitS.values()),
                "triangle_errors": dict(errs)})
    if splitB or splitS:
        return None, None, rep, splitB, splitS
    far = np.ones(len(TB), bool); far[near] = False
    keepT = [TB[far]]
    whole = np.ones(nBn, bool); whole[list(segB.keys())] = False
    cc = clsB[TBn[whole]]
    mixed = int((cc.min(1) != cc.max(1)).sum())
    keepT.append(TBn[whole][cc.max(1) == 0])
    wholeS = np.ones(nS, bool); wholeS[list(segS.keys())] = False
    cc = clsS[TS[wholeS]]
    mixed += int((cc.min(1) != cc.max(1)).sum())
    if cut:
        keepT.append(TS[wholeS][cc.min(1) == 1][:, ::-1] + nVB)
    else:
        keepT.append(TS[wholeS][cc.max(1) == 0] + nVB)
    if out:
        keepT.append(np.asarray(out, np.int64))
    T = np.vstack(keepT)
    rep["uncut_triangles_with_mixed_corners"] = mixed
    used = np.unique(T)
    remap = np.full(len(Vall), -1, np.int64); remap[used] = np.arange(len(used))
    V = Vall[used]; T = remap[T]
    rep["err_centres"] = [[round(float(x), 2) for x in p] for p in err_boxes[:20]]
    rep["secs"] = round(time.time() - t0, 1)
    return V, T, rep, None, None


def union_mesh(VB, TB, VS, TS, shift, say=print, cut=False):
    """body (VB, TB) u solid (VS, TS) - or, `cut`, body minus solid - the solid shifted by `shift`; loops inside one
    triangle split and re-run"""
    VS = np.asarray(VS, float) + shift
    split_total = 0
    for rnd in range(6):
        V, T, rep, sB, sS = _arrange(VB, TB, VS, TS, say, cut=cut)
        say("  pass %d: %s" % (rnd + 1, json.dumps({k: v for k, v in rep.items() if k != "err_centres"})))
        if not rep["segments"]:
            where = "inside" if rep["solid_vertices_inside_body"] else "outside"
            if cut:
                raise RuntimeError("the tool does not cross the body's surface (it is wholly %s the crop) - %s"
                                   % (where, "cutting it would seal a closed void in the part" if where == "inside" else "nothing to cut"))
            raise RuntimeError("the solid does not cross the body's surface (it is wholly %s the crop) - nothing to unite" % where)
        split_total += rep["loops_split"]
        if V is not None:
            rep.update({"arrangement_passes": rnd + 1, "loops_split_total": split_total})
            return V, T, rep
        if sB:
            VB, TB = _split_tris(VB, TB, sB)
        if sS:
            VS, TS = _split_tris(VS, TS, sS)
    raise RuntimeError("closed loops inside single triangles did not resolve in 6 passes")


def refine_long_edges(V, T, L):
    """split every edge longer than L (midpoint), repeatedly, so a coarse solid follows a curved cut"""
    V = list(map(tuple, V)); T = [tuple(t) for t in T]
    for _ in range(12):
        Va = np.asarray(V, float); Ta = np.asarray(T, int)
        e = Va[Ta[:, [1, 2, 0]]] - Va[Ta]
        ln = np.linalg.norm(e, axis=2)
        if ln.max() <= L:
            break
        mid = {}
        newT = []
        for t, l in zip(T, ln):
            i = int(np.argmax(l))
            if l[i] <= L:
                newT.append(t); continue
            a, b, c = t[i], t[(i + 1) % 3], t[(i + 2) % 3]
            key = (min(a, b), max(a, b))
            if key not in mid:
                V.append(tuple(0.5 * (Va[a] + Va[b]))); mid[key] = len(V) - 1
            m = mid[key]
            newT.append((a, m, c)); newT.append((m, b, c))
        T = newT
        Va = np.asarray(V, float); Ta = np.asarray(T, int)
        for _pass in range(3):
            changed = False
            e_all = np.sort(np.concatenate([Ta[:, [0, 1]], Ta[:, [1, 2]], Ta[:, [2, 0]]]), axis=1)
            ue, cnt = np.unique(e_all, axis=0, return_counts=True)
            single = ue[cnt == 1]
            if not len(single):
                break
            sv = set(map(tuple, single))
            outT = []
            for t in Ta:
                done = False
                for i in range(3):
                    a, b = t[i], t[(i + 1) % 3]; c = t[(i + 2) % 3]
                    key = (min(a, b), max(a, b))
                    if key in mid and ((min(a, mid[key]), max(a, mid[key])) in sv or (min(b, mid[key]), max(b, mid[key])) in sv):
                        m = mid[key]; outT.append((a, m, c)); outT.append((m, b, c)); done = True; changed = True; break
                if not done:
                    outT.append(tuple(t))
            Ta = np.asarray(outT, int); T = [tuple(t) for t in Ta]
            if not changed:
                break
    return np.asarray(V, float), np.asarray(T, int)


def _roundtrip(V, T):
    """what the splice will read: float32 coordinates, welded at 1e-6"""
    V32 = np.asarray(V, float).astype(np.float32).astype(float)
    Vw, Tw, _, _ = R._weld(V32, np.asarray(T, int), [], 1e-6)
    return Vw, Tw


def _window(v_in, vs, cut):
    """the volume change a correct result lies in (mm3): 0..+solid for a union (it can neither lose material nor add
    more than the solid holds), -tool..0 for a cut; each end widened by the float32 round trip's allowance `tol`.
    Returns (low, high, tol)."""
    tol = max(0.05, 1e-6 * (abs(v_in) + abs(vs)))
    return ((-vs - tol, tol) if cut else (-tol, vs + tol)) + (tol,)


def union(crop_path, solid_paths, out_path, refine=0.0, say=print, cut=False):
    t0 = time.time()
    what, verb = ("tool", "cut") if cut else ("solid", "union")
    VB, TB = load(crop_path)
    h0 = R.mesh_health(VB, TB); v0, _ = closed_outward(VB, TB); w0 = wound_against(TB)
    say("crop %s: %d triangles, %.1f mm3, open edges %d, non-manifold %d, edges wound against their neighbour %d"
        % (os.path.basename(crop_path), len(TB), v0, h0[0], h0[1], w0))
    if w0:
        say("WARNING: the crop is not oriented (%d edges run the same way by both their triangles) - the result may carry"
            " no more than these" % w0)
    sh0 = shells(VB, TB)
    reps, refusal = [], None
    for sp in solid_paths:
        VS, TS = load(sp)
        vol, bad = closed_outward(VS, TS)
        if bad:
            raise RuntimeError("%s is not closed (%d open or non-manifold edges) - a %s must be one closed solid" % (sp, bad, what))
        wa = wound_against(TS); rewound = 0
        if wa or vol <= 0:
            vc = signed_volume_about(VS, TS, 0.5 * (VS.min(0) + VS.max(0)))
            TS, rewound, nsh = orient_outward(VS, TS)
            vol2, _ = closed_outward(VS, TS)
            say("WARNING: %s is NOT WOUND OUTWARD - %s, so its signed volume is not its volume (%.1f mm3 about the origin,"
                " %.1f about its own centre). Re-wound here: %d of %d triangles turned over, %d shell(s) outward -> %.1f mm3."
                " The drawing that wrote it has a winding bug - fix it at the source."
                % (os.path.basename(sp), ("%d edges are run the SAME way by both their triangles (a sweep's sides wound"
                                          " against its caps?)" % wa) if wa else "it is wound inward throughout",
                   vol, vc, rewound, len(TS), nsh, vol2))
            vol = vol2
            if vol <= 0:
                raise RuntimeError("%s: no outward winding found (%.1f mm3 after re-winding)" % (sp, vol))
        if refine and refine > 0:
            VS, TS = refine_long_edges(VS, TS, refine)
            VS, TS, _, _ = R._weld(VS, TS, [], 1e-9)
        say("%s %s: %d triangles, %.1f mm3" % (what, os.path.basename(sp), len(TS), vol))
        hin = R.mesh_health(VB, TB); win = wound_against(TB)
        ctr = 0.5 * (VS.min(0) + VS.max(0))
        vin0 = signed_volume_about(VB, TB, np.zeros(3)); vinc = signed_volume_about(VB, TB, ctr)
        lo_ok, hi_ok, tol = _window(vin0, vol, cut)
        result = None
        for k, sh in enumerate(SHIFTS):
            V, T, rep = union_mesh(VB, TB, VS, TS, sh, say, cut=cut)
            Vw, Tw = _roundtrip(V, T)
            h = R.mesh_health(Vw, Tw); wr = wound_against(Tw)
            dv = signed_volume_about(Vw, Tw, np.zeros(3)) - vin0
            dvc = signed_volume_about(Vw, Tw, ctr) - vinc
            vol_ok = bool(lo_ok <= dv <= hi_ok and lo_ok <= dvc <= hi_ok)
            if abs(dv - dvc) > tol:
                say("    the volume change reads %+.2f mm3 about the origin but %+.2f about the solid's centre - the result"
                    " is not oriented" % (dv, dvc))
            rep.update({"shift_mm": [float(x) for x in sh], "open_edges": int(h[0]), "nonmanifold_edges": int(h[1]),
                        "wound_against_edges": int(wr), "float32_merged_vertices": int(len(V) - len(Vw)),
                        "solid_volume_mm3": round(vol, 3), "solid_rewound_triangles": int(rewound),
                        "volume_change_mm3": round(dv, 3), "volume_change_about_solid_mm3": round(dvc, 3),
                        "volume_window_mm3": [round(lo_ok, 3), round(hi_ok, 3)], "volume_ok": vol_ok})
            say("  %s with %s (shift %d): %d triangles, open edges %d, non-manifold %d, wound against %d (the crop's own:"
                " %d, %d, %d), %d vertices merged by float32; volume %+.2f mm3 (a correct %s: %+.2f..%+.2f)%s"
                % (verb, os.path.basename(sp), k + 1, len(Tw), h[0], h[1], wr, hin[0], hin[1], win, len(V) - len(Vw),
                   dv, verb, lo_ok, hi_ok, "" if vol_ok else "  <- OUTSIDE"))
            bad = max(0, h[0] - hin[0]) + max(0, h[1] - hin[1])
            score = (int(not vol_ok) + int(wr > win), bad, sum(rep["triangle_errors"].values()) + rep["pairs_not_0_or_2"])
            if result is None or score < result[3]:
                result = (Vw, Tw, rep, score)
            if score == (0, 0, 0):
                break
            for n_, lo_, hi_ in open_loops(Vw, Tw)[:12]:
                say("    open: %d vertices, box x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (n_, lo_[0], hi_[0], lo_[1], hi_[1], lo_[2], hi_[2]))
        VB, TB, rep, score = result
        rep["solid"] = os.path.abspath(sp); reps.append(rep)
        if score[0]:
            why = []
            if not rep["volume_ok"]:
                why.append("the %s changed the crop's volume by %+.2f mm3 (%+.2f about the solid's centre) - a correct %s"
                           " changes it by %+.2f..%+.2f" % (verb, rep["volume_change_mm3"], rep["volume_change_about_solid_mm3"],
                                                           verb, rep["volume_window_mm3"][0], rep["volume_window_mm3"][1]))
            if rep["wound_against_edges"] > win:
                why.append("the result carries %d edges wound against their neighbour (the crop's own: %d)" % (rep["wound_against_edges"], win))
            refusal = ("%s with %s, under every shift: %s - faces were kept on the wrong side (an input that is not one"
                       " closed, oriented, non-self-intersecting solid?)" % (verb, os.path.basename(sp), "; ".join(why)))
            break
    if refusal:
        ref = os.path.splitext(out_path)[0] + "_REFUSED.stl"
        R.write_stl(ref, VB, TB)
        raise RuntimeError("%s. Written as %s for looking at; %s is NOT written." % (refusal, ref, out_path))
    R.write_stl(out_path, VB, TB)
    Vr, Tr = load(out_path)
    h = R.mesh_health(Vr, Tr); vol, _ = closed_outward(Vr, Tr); wr = wound_against(Tr)
    say("wrote %s: %d triangles, %.1f mm3 (crop %.1f, %+.1f), open edges %d, non-manifold %d, wound against %d (the crop's"
        " own: %d, %d, %d) - %.1f s" % (out_path, len(Tr), vol, v0, vol - v0, h[0], h[1], wr, h0[0], h0[1], w0, time.time() - t0))
    sh1 = shells(Vr, Tr)
    cav0 = [s for s in sh0 if s[1] < 0]
    cav = [s for s in sh1 if s[1] < 0]
    new_cav = [s for s in cav if not any(abs(s[1] - c[1]) < 1e-3 and np.abs(s[2] - c[2]).max() < 1e-3
                                         and np.abs(s[3] - c[3]).max() < 1e-3 for c in cav0)]
    for nt, cv, lo_, hi_ in new_cav:
        say("WARNING: the %s ENCLOSED a cavity of %.2f mm3 (%d triangles), box x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f -"
            " a drawn face spans a pocket of the body; MJF traps powder in it (reach the face below the pocket's floor,"
            " or fill the pocket with another solid)" % (verb, -cv, nt, lo_[0], hi_[0], lo_[1], hi_[1], lo_[2], hi_[2]))
    pos0 = [s for s in sh0 if s[1] > 0]; pos1 = [s for s in sh1 if s[1] > 0]
    loose = sorted(pos1, key=lambda r: r[1])[:max(0, len(pos1) - len(pos0))]
    for nt, pv, lo_, hi_ in loose:
        say("WARNING: the %s left a LOOSE PIECE of %.2f mm3 (%d triangles), box x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f -"
            " it is not joined to the part" % (verb, pv, nt, lo_[0], hi_[0], lo_[1], hi_[1], lo_[2], hi_[2]))
    return {"out": out_path, "mode": verb, "triangles": int(len(Tr)), "volume_mm3": vol, "crop_volume_mm3": v0,
            "added_mm3": vol - v0, "open_edges": int(h[0]), "nonmanifold_edges": int(h[1]), "wound_against_edges": int(wr),
            "crop_open_edges": int(h0[0]), "crop_nonmanifold_edges": int(h0[1]), "crop_wound_against_edges": int(w0),
            "bad_edges": int(max(0, h[0] - h0[0]) + max(0, h[1] - h0[1])),
            "cavities_crop": len(cav0), "cavities_out": len(cav),
            "new_cavities": [{"mm3": round(-cv, 3), "triangles": nt, "box": [round(float(x), 2) for x in (lo_[0], hi_[0], lo_[1], hi_[1], lo_[2], hi_[2])]}
                             for nt, cv, lo_, hi_ in new_cav],
            "loose_pieces": [{"mm3": round(pv, 3), "triangles": nt, "box": [round(float(x), 2) for x in (lo_[0], hi_[0], lo_[1], hi_[1], lo_[2], hi_[2])]}
                             for nt, pv, lo_, hi_ in loose],
            "passes": reps}


def cmd(args, kit):
    r"""kit union <crop.stl> --solid <solid.stl> [--solid ...] --out <out.stl> [--refine 0] [--cut]
              [--baseline <the same box cropped from the PRE-EDIT body.stl>]

    --baseline replays the operation on the pre-edit crop and prints how much ORIGINAL material the cut takes (a cut
    meant to trim added material reads ~0; the ramp cut that dug into the chamfer would have read -70); the replay is
    written as <out>.baseline.stl. <out>.union.json records the md5 of the crop, each solid and the output.

    A drawn, closed solid unioned into a crop of the body - or, with --cut, cut out of it: the two meshes' intersection
    curve is computed once (exact triangle-pair tests, one shared vertex per edge/face piercing), inserted into both,
    and the body's faces outside the solid are kept with the solid's faces outside the body (union) or inside it,
    turned over (cut) - seconds. A solid that is not wound outward (an edge run the same way by both its triangles, or
    inward throughout) is re-wound and the log says so. Checked after a float32 round trip: open, non-manifold and
    wound-against edges must equal the crop's own, and the volume must change by 0..+solid (union) or -tool..0 (cut) -
    else REFUSED, written as <out>_REFUSED.stl. Then `kit splice` the result back with the crop's sidecar."""
    cut = "--cut" in args
    args = [t for t in args if t != "--cut"]
    a = kit._kv(args)
    src = a["_"][0] if a["_"] else ""
    solids = kit._all(args, "--solid")
    out = a.get("--out", "")
    baseline = a.get("--baseline", "")
    if not src or not solids or not out or baseline is True:
        print(cmd.__doc__); return 2
    for p in [src] + solids + ([baseline] if baseline else []):
        if not os.path.isfile(p):
            print("kit union: no such file: %s" % p); return 2
    try:
        rep = union(src, solids, out, refine=float(a.get("--refine", 0.0)), say=lambda *x: print(" ".join(str(y) for y in x), flush=True), cut=cut)
    except RuntimeError as e:
        print("kit union REFUSED: %s" % e); return 2
    # ORIGINAL
    # ORIGINAL
    base_rep = None
    if baseline:
        bout = os.path.splitext(out)[0] + ".baseline.stl"
        try:
            base_rep = union(baseline, solids, bout, refine=float(a.get("--refine", 0.0)), say=lambda *x: None, cut=cut)
            print("baseline %s: the %s changes the ORIGINAL (pre-edit) surface by %+.2f mm3 (this crop: %+.2f) -> %s"
                  % (os.path.basename(baseline), rep["mode"], base_rep["added_mm3"], rep["added_mm3"], bout))
            if cut and base_rep["added_mm3"] < -0.5:
                print("WARNING: the cut takes %.2f mm3 OF THE ORIGINAL PART, not only of what was added. If it was meant to"
                      " trim added material only, its floor sits under the original surface - follow the original"
                      " (floor = max(design plane, original + 0.03 mm)) and cut again." % -base_rep["added_mm3"])
        except RuntimeError as e:
            print("baseline %s: the %s could not be replayed on it (%s) - no original-material figure" % (os.path.basename(baseline), rep["mode"], str(e)[:160]))
    md5 = {"crop": kit_md5(src), "solids": [kit_md5(s) for s in solids], "out": kit_md5(out)}
    with open(os.path.splitext(out)[0] + ".union.json", "w", encoding="utf-8") as fh:
        json.dump(dict(rep, crop=os.path.abspath(src), solids=[os.path.abspath(s) for s in solids], md5=md5,
                       baseline=(os.path.abspath(baseline) if baseline else None),
                       baseline_change_mm3=(round(base_rep["added_mm3"], 3) if base_rep else None),
                       when=time.strftime("%Y-%m-%d %H:%M:%S")), fh, indent=1)
    if rep["bad_edges"]:
        print("kit union: the result is NOT closed (%d open/non-manifold edges beyond the crop's own) - look at it before splicing" % rep["bad_edges"]); return 1
    print("  Next      : kit splice %s --crop %s --out <body2.stl>   (then LOOK: kit render of the spliced mesh, boxed on the addition, every frame opened)"
          % (out, os.path.splitext(src)[0] + ".crop.json" if os.path.isfile(os.path.splitext(src)[0] + ".crop.json") else "<the crop's .crop.json>"))
    return 0


def kit_md5(path):
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    class _K:
        @staticmethod
        def _kv(args):
            d = {"_": []}; i = 0
            while i < len(args):
                if args[i].startswith("--") and i + 1 < len(args) and not args[i + 1].startswith("--"):
                    d[args[i]] = args[i + 1]; i += 2
                elif args[i].startswith("--"):
                    d[args[i]] = True; i += 1
                else:
                    d["_"].append(args[i]); i += 1
            return d

        @staticmethod
        def _all(args, name):
            return [args[i + 1] for i, t in enumerate(args) if t == name and i + 1 < len(args)]
    sys.exit(cmd(sys.argv[1:], _K))

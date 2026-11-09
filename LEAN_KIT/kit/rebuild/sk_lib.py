# REBUILD_region.json  kit rebuild
# over the
import os, json, time, hashlib, glob, numpy as np
from PIL import Image, ImageDraw, ImageFont

RUN = os.environ.get("RUN") or os.getcwd()
SK = os.path.join(RUN, "skin")
EDGEMAP = os.path.join(SK, "edgemap")
OUT = os.environ.get("OUT_DIR") or os.path.join(SK, "review")
for _d in (SK, EDGEMAP, OUT):
    try: os.makedirs(_d, exist_ok=True)
    except OSError: pass
BODY = os.environ.get("BODY", "")
STL = os.environ.get("STL") or os.path.join(RUN, "piece.stl")
TAG = os.environ.get("LK_TAG", "")


def _fail(m):
    print(m if str(m).startswith("FAIL") else "FAIL: " + str(m), flush=True); raise SystemExit(1)


def _load_window():
    """the edit region the region step recorded: the box and the extra cut planes (point, OUTWARD normal)"""
    try:
        rec = json.load(open(os.path.join(RUN, "REBUILD_region.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return None, []
    w = rec.get("window")
    win = tuple(float(v) for v in w) if w and len(w) == 6 else None
    planes = []
    for p in rec.get("planes") or []:
        c = np.array(p[:3], float); n = np.array(p[3:6], float); n = n / max(np.linalg.norm(n), 1e-12)
        planes.append((c, n))
    return win, planes


WIN, PLANES = _load_window()
if WIN is None:
    WIN = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
WALLS = [(np.array(n, float), float(c)) for n, c in (((1, 0, 0), WIN[0]), ((-1, 0, 0), -WIN[1]), ((0, 1, 0), WIN[2]), ((0, -1, 0), -WIN[3]),
                                                       ((0, 0, 1), WIN[4]), ((0, 0, -1), -WIN[5]))]
WALLS += [(-n, float(-(n @ c))) for c, n in PLANES]
RAKE_P, RAKE_N = (PLANES[0] if PLANES else (np.zeros(3), np.array([0.0, 0.0, 1.0])))
BG = (0.13, 0.14, 0.17); VOX = (0.80, 0.62, 0.42); ALPHA = 0.20


def need_window():
    if WIN == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0):
        _fail("FAIL: no edit region - REBUILD_region.json is missing from %s; `kit rebuild region` writes it" % RUN)


def inwin(P, m=0.0):
    P = np.asarray(P, float)
    return np.all(np.stack([P @ n - c for n, c in WALLS], axis=1) >= -m, axis=1)


def wall_dist(P):
    """distance of each point to the nearest edit region wall (the six box planes and every cut plane), inside the edit region"""
    P = np.asarray(P, float)
    return np.stack([P @ n - c for n, c in WALLS], axis=1).min(axis=1)


def wall_of(P):
    """(the wall index, the worst distance) of the wall the points P lie on"""
    P = np.asarray(P, float)
    d = [np.abs(P @ n - c).max() for n, c in WALLS]
    return int(np.argmin(d)), float(min(d))


def font(sz):
    for nm in ("arialbd.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try: return ImageFont.truetype(nm, sz)
        except Exception: pass
    return ImageFont.load_default()
F16, F22 = font(16), font(22)


def corners(b):
    return np.array([[x, y, z] for x in (b[0], b[1]) for y in (b[2], b[3]) for z in (b[4], b[5])], float)


def render_transparent(R, V, T, d, foc, W, pad, C=None):
    """every layer accumulated per pixel (weighted-average transparency); C = per-triangle colour (0..1) or None"""
    d3, r3, u3 = R.basis(d)
    fx = foc @ r3; fy = foc @ u3
    x0, x1 = fx.min() - pad, fx.max() + pad; y0, y1 = fy.min() - pad, fy.max() + pad
    mmpx = (x1 - x0) / W; H = int(np.ceil((y1 - y0) / mmpx))
    X = (V @ r3 - x0) / mmpx; Y = (y1 - V @ u3) / mmpx
    P = V[T]; n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1; n = n / ln[:, None]
    light = -d3 + 0.5 * u3 + 0.35 * r3; light = light / np.linalg.norm(light)
    sh = 0.30 + 0.70 * np.abs(n @ light)
    Ct = np.tile(np.array(VOX), (len(T), 1)) if C is None else np.asarray(C, float)
    acc = np.zeros((H, W, 3)); wsum = np.zeros((H, W)); trans = np.ones((H, W))
    XT = X[T]; YT = Y[T]
    xa_ = np.clip(np.floor(XT.min(axis=1)).astype(int), 0, W - 1); xb_ = np.clip(np.ceil(XT.max(axis=1)).astype(int), 0, W - 1)
    ya_ = np.clip(np.floor(YT.min(axis=1)).astype(int), 0, H - 1); yb_ = np.clip(np.ceil(YT.max(axis=1)).astype(int), 0, H - 1)
    for i in range(len(T)):
        xa, xb, ya, yb = xa_[i], xb_[i], ya_[i], yb_[i]
        (x1_, x2_, x3_), (y1_, y2_, y3_) = XT[i], YT[i]
        den = (y2_ - y3_) * (x1_ - x3_) + (x3_ - x2_) * (y1_ - y3_)
        if abs(den) < 1e-12: continue
        gx = np.arange(xa, xb + 1)[None, :] + 0.5; gy = np.arange(ya, yb + 1)[:, None] + 0.5
        w0 = ((y2_ - y3_) * (gx - x3_) + (x3_ - x2_) * (gy - y3_)) / den
        w1 = ((y3_ - y1_) * (gx - x3_) + (x1_ - x3_) * (gy - y3_)) / den
        ins = (w0 >= 0) & (w1 >= 0) & (1.0 - w0 - w1 >= 0)
        if not ins.any(): continue
        sa = acc[ya:yb + 1, xa:xb + 1]; sw = wsum[ya:yb + 1, xa:xb + 1]; st_ = trans[ya:yb + 1, xa:xb + 1]
        sa[ins] += Ct[i] * sh[i] * ALPHA; sw[ins] += ALPHA; st_[ins] *= (1.0 - ALPHA)
    hit = wsum > 0
    mean = np.zeros_like(acc); mean[hit] = acc[hit] / wsum[hit][:, None]
    cov = (1.0 - trans)[..., None]
    img = mean * cov + np.array(BG)[None, None, :] * (1.0 - cov)
    edge = np.zeros((H, W), bool); edge[:, 1:] |= hit[:, 1:] != hit[:, :-1]; edge[1:, :] |= hit[1:, :] != hit[:-1, :]
    img[edge] = np.array(VOX) * 0.9
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)), mmpx, x0, y1, r3, u3


def _unit(v):
    v = np.asarray(v, float); return v / max(np.linalg.norm(v), 1e-12)


def close_ups(n=4, pad=3.0):
    """close-up views at the edit region's CHANGED regions (skin\\regions.json, written by skin-regions), the largest first, each seen
    from outside the edit region's middle toward it (from above when it lies level with the middle). A section's hand-placed close-ups
    (the slot mouth, the crown lip, the keel) came from its pictures; on another edit region the changes decide where to look."""
    try:
        regs = json.load(open(os.path.join(SK, "regions.json"), encoding="utf-8")).get("regions", [])
    except (OSError, ValueError):
        return []
    regs = [r for r in regs if r.get("status") == "remake" and r.get("bbox")]
    regs.sort(key=lambda r: -float(r.get("area_mm2", 0)))
    wc = np.array([(WIN[0] + WIN[1]) / 2, (WIN[2] + WIN[3]) / 2, (WIN[4] + WIN[5]) / 2])
    out = []
    for k, r in enumerate(regs[:n]):
        b = r["bbox"]; fb = (b[0] - pad, b[3] + pad, b[1] - pad, b[4] + pad, b[2] - pad, b[5] + pad)
        rc = np.array(r.get("centre") or [(b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2], float)
        d = -_unit(rc - wc) if np.linalg.norm(rc - wc) > 1e-6 else np.array([0.0, 0.0, -1.0])
        if abs(d[2]) < 0.3: d = _unit(d + np.array([0.0, 0.0, -0.6]))
        out.append(("close_R%d" % r.get("id", k), tuple(d), fb, 1300, "close-up: changed region R%d (%.0f mm2)" % (r.get("id", k), float(r.get("area_mm2", 0)))))
    return out


# PICS=full
PICS = (os.environ.get("PICS", "full") or "full").strip().lower()
if PICS not in ("quick", "full"):
    PICS = "full"
QUICK_VIEWS = ("orbit_045", "orbit_135", "orbit_225", "orbit_315", "below_135", "below_315")


def spot_close_ups(n=2, pad=3.0):
    """31av: the quick set's close-ups - the places the last layout / piece redos named (skin\\RESTART.json: the spots with tries or locked),
    newest first, each seen from outside the edit region's middle toward it"""
    try:
        st = json.load(open(os.path.join(SK, "RESTART.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return []
    sps = [s for s in st.get("spots", []) if s.get("box") and len(s["box"]) == 6 and (s.get("tries") or s.get("locked"))]
    sps.sort(key=lambda s: max([str(t.get("when", "")) for t in s.get("tries", [])] + [str(s.get("locked_at") or "")]), reverse=True)
    wc = np.array([(WIN[0] + WIN[1]) / 2, (WIN[2] + WIN[3]) / 2, (WIN[4] + WIN[5]) / 2])
    out = []
    for s in sps[:n]:
        b = [float(v) for v in s["box"]]; fb = (b[0] - pad, b[1] + pad, b[2] - pad, b[3] + pad, b[4] - pad, b[5] + pad)
        rc = np.array([(b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2])
        d = -_unit(rc - wc) if np.linalg.norm(rc - wc) > 1e-6 else np.array([0.0, 0.0, -1.0])
        if abs(d[2]) < 0.3: d = _unit(d + np.array([0.0, 0.0, -0.6]))
        out.append(("spot%d" % int(s.get("id", 0)), tuple(d), fb, 1300, "close-up: spot %d - where the last redo pointed" % int(s.get("id", 0))))
    return out


def views(close=True, below=False, pics=None):
    """8 orbit views from 30 deg above, straight down, straight up - over the whole edit region; with below=True (31an: the whole piece
    from below and behind - the client 2026-10-07, after R4 skin 1's crumpled underside was seen only by the final sweep) 4 more orbit views
    from 30 deg BELOW; then the close-ups at the changed regions. 31av: pics (default PICS) "quick" = four orbits above, two below
    (whatever `below` says - the underside is always looked at) and the close-ups where the last redo pointed."""
    mode = (pics or PICS)
    full = tuple(WIN)
    out = []
    for az in range(0, 360, 45):
        a = np.radians(az); el = np.radians(30.0)
        out.append(("orbit_%03d" % az, (-np.cos(el) * np.sin(a), np.cos(el) * np.cos(a), -np.sin(el)), full, 1400, "orbit %d deg, 30 deg up" % az))
    if below or mode == "quick":
        for az in (45, 135, 225, 315):
            a = np.radians(az); el = np.radians(-30.0)
            out.append(("below_%03d" % az, (-np.cos(el) * np.sin(a), np.cos(el) * np.cos(a), -np.sin(el)), full, 1400, "orbit %d deg, from 30 deg BELOW" % az))
    out += [("top", (0, 0, -1), full, 1400, "straight down"), ("bottom", (0, 0, 1), full, 1400, "straight up")]
    if mode == "quick":
        out = [v for v in out if v[0] in QUICK_VIEWS]
        if close:
            out += spot_close_ups()
        return out
    if close:
        out += close_ups()
    return out


# skin-labels  skin-mirror  skin-build
def mirror_plane(s):
    """(n unit (3,), c) of the plane named by s, or None for an empty s; ValueError for a malformed one"""
    s = (s or "").replace(",", " ").split()
    if not s:
        return None
    if len(s) == 2 and s[0].lower() in ("x", "y", "z"):
        n = np.zeros(3); n["xyz".index(s[0].lower())] = 1.0
        return n, float(s[1])
    if len(s) == 4:
        n = np.array([float(v) for v in s[:3]]); L = float(np.linalg.norm(n))
        if L < 1e-9: raise ValueError("the plane's normal is zero")
        return n / L, float(s[3]) / L
    raise ValueError("MIRROR is \"<axis> <offset>\" (x 0) or \"nx ny nz c\", not %r" % " ".join(s))


def reflect(P, n, c):
    P = np.asarray(P, float); return P - 2.0 * ((P @ n) - c)[..., None] * n


def reflect_dir(N, n):
    N = np.asarray(N, float); return N - 2.0 * (N @ n)[..., None] * n


def face_area_normals(V, T, fid, nf):
    """31at: each face's AREA-WEIGHTED normal - the sum of its triangles' area normals (|sum| = the area for a flat face, less as the face
    turns; ~0 for a closed tube) - and its area, from a tessellation (V, T, fid = the face of each triangle). A face with no triangle: zeros."""
    V = np.asarray(V, float); T = np.asarray(T); fid = np.asarray(fid)
    P = V[T]; cr = 0.5 * np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    NS = np.zeros((nf, 3)); AR = np.zeros(nf)
    np.add.at(NS, fid, cr); np.add.at(AR, fid, np.linalg.norm(cr, axis=1))
    return NS, AR


def mirror_pairs(C, A, N, S, n, c, tol=1.5, area_frac=0.35):
    """THE MIRROR CHECK's pairing (sk_mirror 31al; here since 31at so it is tested without a kernel). Every face is matched with the face
    whose centre is its centre's mirror (within tol mm, or a quarter of its size if larger), of like area (within area_frac, or 3 mm2) and
    whose direction is its own mirrored (dot > 0.7) - a face with no direction (N zero: its normals cancel) is held to centre and area only;
    the cheapest match first; a face on the plane may pair with itself. Returns (pairs [(i, j)], unpaired [i], mate {i: j})."""
    C = np.asarray(C, float); A = np.asarray(A, float); N = np.asarray(N, float); S = np.asarray(S, float)
    Rc = reflect(C, n, c); Rn = reflect_dir(N, n)
    cand = []
    for i in range(len(C)):
        tol_i = max(tol, 0.25 * S[i])
        for j in range(i, len(C)):
            dc = float(np.linalg.norm(Rc[i] - C[j]))
            if dc > tol_i: continue
            da = abs(A[i] - A[j]); okA = da <= max(area_frac * max(A[i], A[j]), 3.0)
            dn = float(Rn[i] @ N[j]); okN = dn > 0.7 or np.linalg.norm(N[i]) < 0.5 or np.linalg.norm(N[j]) < 0.5
            if okA and okN: cand.append((dc / tol_i + da / max(A[i], A[j], 1e-9), i, j, dc, da))
    cand.sort()
    mate = {}
    for cost, i, j, dc, da in cand:
        if i in mate or j in mate: continue
        mate[i] = j; mate[j] = i
    pairs = sorted({tuple(sorted((i, j))) for i, j in mate.items()})
    unp = [i for i in range(len(C)) if i not in mate]
    return pairs, unp, mate


def mirror_side(P, n, c):
    """signed distance of the points from the plane (+ on the side the normal points to)"""
    return np.asarray(P, float) @ n - c


def window_symmetric(n, c, tol=0.5):
    """(ok, why): the edit region - its box and every extra cut plane - is its own mirror across the plane. A mirror layout needs both
    sides of the edit inside one edit region; an edit region that is not symmetric about MIRROR has slave triangles with no master to copy."""
    if WIN == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0):
        return False, "no edit region recorded"
    box = corners(WIN)
    if float(np.abs(mirror_side(box, n, c)).max()) < 1e-9 or not (mirror_side(box, n, c).min() < 0 < mirror_side(box, n, c).max()):
        return False, "the plane does not cross the edit region (both sides of a symmetric edit must be inside it)"
    rb = reflect(box, n, c)
    lo, hi = np.array([WIN[0], WIN[2], WIN[4]]), np.array([WIN[1], WIN[3], WIN[5]])
    if not (np.all(rb.min(0) >= lo - tol) and np.all(rb.max(0) <= hi + tol) and np.all(rb.min(0) <= lo + tol) and np.all(rb.max(0) >= hi - tol)):
        return False, "the edit region box is not its own mirror (reflected it spans %s .. %s, the box is %s .. %s)" % (
            np.round(rb.min(0), 2).tolist(), np.round(rb.max(0), 2).tolist(), lo.tolist(), hi.tolist())
    for pc, pn in PLANES:
        q, qn = reflect(pc, n, c), reflect_dir(pn, n)
        if not any(abs(float((q - pc2) @ pn2)) < tol and float(qn @ pn2) > 0.999 for pc2, pn2 in PLANES):
            return False, "the cut plane through %s (normal %s) has no mirror partner among the card's PLANES" % (np.round(pc, 2).tolist(), np.round(pn, 3).tolist())
    return True, "the edit region and its %d cut plane(s) are their own mirror" % len(PLANES)


def mirror_decision():
    """the card's symmetry decision recorded at skin-labels (skin\\MIRROR_DECISION.json): the MIRROR string, "" = not symmetric,
    None = no decision recorded yet"""
    try:
        return str(json.load(open(os.path.join(SK, "MIRROR_DECISION.json"), encoding="utf-8")).get("plane", "")).strip()
    except (OSError, ValueError):
        return None


def tri_adjacency(F):
    """(ta, tb, Es_shared): the triangle pairs that share an edge"""
    E_ = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); Es = np.sort(E_, 1); tri = np.tile(np.arange(len(F)), 3)
    o = np.lexsort((Es[:, 1], Es[:, 0])); Es = Es[o]; tri = tri[o]; same = np.all(Es[1:] == Es[:-1], axis=1)
    return tri[:-1][same], tri[1:][same]


def face_twins(cent, area, n, c, tol_mm=0.5, area_tol=0.10):
    """31bf: the mirror twin of every body face in the edit region - the face whose centroid is the reflection of its own (within tol_mm) and whose
    area is within area_tol; a twin must be mutual. cent / area: {face: xyz} / {face: mm2}. Returns {face: twin} (a face spanning the plane is
    its own twin when its centroid lies on the plane)."""
    faces = sorted(cent); C = np.array([cent[f] for f in faces], float); A = np.array([area[f] for f in faces], float)
    Q = reflect(C, n, c); out = {}
    for i, f in enumerate(faces):
        d = np.linalg.norm(C - Q[i][None, :], axis=1)
        ok = (d <= tol_mm) & (np.abs(A - A[i]) <= area_tol * np.maximum(A, A[i]))
        if not ok.any(): continue
        j = int(np.argmin(np.where(ok, d, np.inf))); out[f] = faces[j]
    return {f: t for f, t in out.items() if out.get(t) == f}


def mirror_layout_faces(Cn, Nn, At, F, fid, pid, iscap, n, c, master="auto", band=0.3, twin_of=None, vote_mm=2.0, say=print):
    """31bf - THE LAYOUT MIRRORED FACE BY FACE (a B-rep source; the agent's b4: the triangle mirror of a bigger slit wall on the -x side left an island
    of one face inside another and broke a border into three chains - the plate top / spine flank open at the frame). The master side keeps its
    patches. A slave face is labelled by its RAW PIECES (the connected components of one original face with one skin-labels patch - its mesh
    pieces and its wrap halves), never by the triangle, so no island can open inside a face and a face in two pieces (the b4 test's 1783:
    2 + 20 triangles) is mirrored piece by piece. A slave face WITH a master twin: each piece takes the patch most of its triangles' mirror
    points land in AMONG THE TWIN'S OWN like-facing triangles (+ MIRROR_OFF) - one patch when the twin is one patch, the twin's own split when
    it is not (a piece splits per triangle only when no patch holds two thirds of it). A slave face with NO twin (the model is not face-for-face
    symmetric there: the agent's bigger -x slit wall 1154 against 1101, the b4 test's 536 against 518): the WHOLE face takes the master patch most of
    its mirrored triangles land in (area-weighted; a triangle farther than vote_mm from every like-facing master triangle has no vote) - no
    border cut inside it. A patch that is ITS OWN MIRROR (skin beyond band on both sides: a face spanning the plane and whatever was absorbed
    into it) is taken as itself - only where the piece touches it on the slave side (an island with a master label would read as a twin pair
    later); the piece of a plane-centred face lying wholly on the slave side is mirrored against the face's master-side piece (the b4 test's
    1104, one piece per side, never paired). A face no rule reaches is absorbed by the slave neighbour with the longest border (the neighbour's
    label along that border), in rounds; one nothing reaches keeps its own patch. Then every mirrored label is ONE slave component: a stray
    voted / absorbed piece joins the neighbour it touches most (what skin-features' twin re-pairing and the mirror check assume). numpy only.
    Returns (new labels, info - Python ints and floats)."""
    fid = np.asarray(fid, np.int64); pid = np.asarray(pid, np.int64); iscap = np.asarray(iscap, bool)
    Cn = np.asarray(Cn, float); Nn = np.asarray(Nn, float); At = np.asarray(At, float); nF = len(F)
    s = mirror_side(Cn, n, c); nc = ~iscap
    faces = sorted(int(x) for x in np.unique(fid[(fid >= 0) & nc]))
    side_f = {}
    for f in faces:
        d = float(np.mean(s[(fid == f) & nc])); side_f[f] = 1 if d > band else (-1 if d < -band else 0)
    plus = sum(1 for f in faces if side_f[f] > 0); minus = sum(1 for f in faces if side_f[f] < 0); cross = [f for f in faces if side_f[f] == 0]
    if master == "auto":
        master = "+" if plus <= minus else "-"
        say("mirror: MASTER auto - %d faces on the + side, %d on the - side -> %s (the side with FEWER faces: less junk to mirror away)" % (plus, minus, master))
    sgn = 1 if master == "+" else -1
    twin_of = twin_of or {}
    ss = s * sgn
    own_pids = set(int(x) for x in np.unique(pid[(ss > band) & nc])) & set(int(x) for x in np.unique(pid[(ss < -band) & nc]))
    mface = np.zeros(nF, bool); sface = np.zeros(nF, bool)
    for f in faces:
        if side_f[f] == sgn: mface |= (fid == f)
        elif side_f[f] == -sgn: sface |= (fid == f)
    mface &= nc; sface &= nc
    master_pids = set(int(x) for x in np.unique(pid[mface])) | own_pids
    slave_only = set(int(x) for x in np.unique(pid[sface])) - master_pids
    ta, tb = tri_adjacency(F)
    key = np.where(fid >= 0, fid * (int(pid.max()) + 2) + pid, -1 - np.arange(nF))
    piece = label_components(key, ta, tb, nF)
    cand = np.zeros(nF, bool)
    for f in faces:
        if side_f[f] in (sgn, 0): cand |= (fid == f)
    cand &= nc & (ss >= 0.0)
    mi_all = np.nonzero(cand)[0]
    new = pid.astype(np.int64).copy(); done = {}; no_twin = []; placed = np.zeros(nF, bool); votes = []
    slave = [f for f in faces if side_f[f] == -sgn]

    def _nearest(ti, mi):
        """for the slave triangles ti: the triangle among mi nearest their mirror point - a like-facing one (reflected normal . normal > 0.3)
        when any of the 12 nearest is; (index into mi, like-facing found, its distance)"""
        q = reflect(Cn[ti], n, c); nq = reflect_dir(Nn[ti], n)
        k = int(min(12, len(mi)))
        dk, ik = knn(Cn[mi], q, k)
        dk = np.asarray(dk, float); ik = np.asarray(ik, np.int64)
        if dk.ndim == 1: dk = dk[:, None]; ik = ik[:, None]
        ok = np.einsum("ij,ikj->ik", nq, Nn[mi][ik]) > 0.3
        first = np.where(ok.any(1), ok.argmax(1), 0)
        r = np.arange(len(ik)); return ik[r, first], ok.any(1), dk[r, first]

    def _touches(ti, P):
        """the triangles ti share a mesh edge with a slave-side skin triangle of raw patch P"""
        inT = np.zeros(nF, bool); inT[ti] = True
        other = (pid == P) & nc & (ss < 0.0) & ~inT
        return bool(((inT[ta] & other[tb]) | (inT[tb] & other[ta])).any())

    def _label(ti, P):
        """the label a slave piece takes for the master patch P: P itself when P is its own mirror and the piece touches it; P + MIRROR_OFF
        otherwise; None when P is its own mirror but out of reach, or lives on slave faces only"""
        if P in slave_only: return None
        if P in own_pids: return P if _touches(ti, P) else None
        return P + MIRROR_OFF

    def _place(f, ti, mi, whole, any_facing, kind):
        """label the slave triangles ti of face f by the vote over their nearest among mi: whole = one patch for all of ti, else piece by
        piece. any_facing: a twin's own triangles count even when none faces alike; else only like-facing within vote_mm. Returns placed?"""
        j, okf, dist = _nearest(ti, mi)
        if any_facing: okf = np.ones(len(ti), bool)
        else: okf &= (dist <= vote_mm)
        if not okf.any(): return False
        P_ = pid[mi][j]
        groups = [np.ones(len(ti), bool)] if whole else [piece[ti] == pc for pc in np.unique(piece[ti])]
        lab = np.full(len(ti), -1, np.int64); shares = []
        for g in groups:
            gv = g & okf
            if not gv.any(): continue
            vote = {}
            for p_, a_ in zip(P_[gv].tolist(), At[ti][gv].tolist()): vote[p_] = vote.get(p_, 0.0) + a_
            tot = sum(vote.values()); P, aP = max(vote.items(), key=lambda kv: (kv[1], -kv[0]))
            if whole or aP >= (2.0 / 3.0) * tot:
                L = _label(ti[g], P)
                if L is None: continue
                lab[g] = L; shares.append((P, aP / max(tot, 1e-12), float(np.median(dist[gv]))))
            else:
                for q_ in np.nonzero(g)[0]:
                    L = _label(ti[q_:q_ + 1], int(P_[q_])) if okf[q_] else None
                    if L is not None: lab[q_] = L
                shares.append((P, aP / max(tot, 1e-12), float(np.median(dist[gv]))))
        got = lab >= 0
        if not got.any(): return False
        if not got.all():
            vals, cnt = np.unique(lab[got], return_counts=True); lab[~got] = vals[cnt.argmax()]
        new[ti] = lab; placed[ti] = True
        votes.append([kind, int(f), int(shares[0][0]), round(float(min(x[1] for x in shares)), 3), round(float(max(x[2] for x in shares)), 3)])
        return True

    nvote = 0
    for f in slave:
        ti = np.nonzero((fid == f) & nc)[0]
        if not len(ti): continue
        t = twin_of.get(f)
        if t is not None and side_f.get(t) == sgn:
            mi = np.nonzero((fid == t) & nc)[0]
            if len(mi) and _place(f, ti, mi, whole=False, any_facing=True, kind="twin"):
                done[f] = ("twin", int(t)); continue
        no_twin.append(f)
        if len(mi_all) and _place(f, ti, mi_all, whole=True, any_facing=False, kind="vote"):
            done[f] = ("vote", int(new[ti][0])); nvote += 1
    nhalf = 0
    for f in cross:
        tf = np.nonzero((fid == f) & nc)[0]
        if not len(tf): continue
        pcs = np.unique(piece[tf]); lo = [pc for pc in pcs if ss[tf][piece[tf] == pc].max() <= band]
        mi = tf[ss[tf] > 0.0]
        if not lo or not len(mi): continue
        for pc in lo:
            ti = tf[piece[tf] == pc]
            if _place(f, ti, mi, whole=True, any_facing=True, kind="half"): nhalf += 1
    fa, fb = fid[ta], fid[tb]; nb = {}
    for x, y in zip(fa.tolist(), fb.tolist()):
        if x == y or x < 0 or y < 0: continue
        nb.setdefault(x, {}); nb[x][y] = nb[x].get(y, 0) + 1
        nb.setdefault(y, {}); nb[y][x] = nb[y].get(x, 0) + 1

    def _border_label(f, g):
        m1 = (fa == f) & (fb == g); m2 = (fa == g) & (fb == f)
        labs = np.concatenate([new[tb[m1]], new[ta[m2]]]); labs = labs[labs >= 0]
        if not len(labs): labs = new[(fid == g) & nc]
        vals, cnt = np.unique(labs, return_counts=True); return int(vals[cnt.argmax()])
    nab = 0
    for _round in range(len(slave) + 1):
        add = {}
        for f in slave:
            if f in done: continue
            cands = [(cnt, -g) for g, cnt in nb.get(f, {}).items() if g in done]
            if cands:
                cnt, g = max(cands); add[f] = -g
        if not add: break
        for f, g in add.items():
            ti = np.nonzero((fid == f) & nc)[0]; new[ti] = _border_label(f, g); done[f] = ("border", g); nab += 1
    own = [f for f in slave if f not in done]
    ndet = 0; split = []
    for _ in range(10):
        cc = label_components(new, ta, tb, nF); moved = 0; comps = {}
        for ci in np.unique(cc[(new >= MIRROR_OFF) & nc]):
            m = (cc == ci) & nc; L = int(new[m][0])
            isA = any(done.get(int(f_), ("",))[0] == "twin" for f_ in np.unique(fid[m]).tolist())
            comps.setdefault(L, []).append((int(ci), float(At[m].sum()), isA))
        split = []
        for L, cs in comps.items():
            if len(cs) < 2: continue
            keep = set(ci for ci, a_, isA in cs if isA) or {max(cs, key=lambda x: x[1])[0]}
            for ci, a_, isA in cs:
                if ci in keep: continue
                m = (cc == ci) & nc; cnt = {}
                for x, y in ((ta, tb), (tb, ta)):
                    m2 = m[x] & ~m[y] & nc[y] & (ss[y] < 0.0) & (new[y] != L)
                    for v in new[y[m2]].tolist(): cnt[v] = cnt.get(v, 0) + 1
                if cnt: new[m] = max(cnt.items(), key=lambda kv: (kv[1], -kv[0]))[0]; moved += 1; ndet += 1
                else: split.append(int(L))
        if not moved: break
    info = {"master": master, "plus": int(plus), "minus": int(minus), "cross": [int(x) for x in cross], "own_patches": sorted(int(x) for x in own_pids),
            "slave_faces": len(slave), "twins": sum(1 for v in done.values() if v[0] == "twin"), "voted": int(nvote),
            "votes": votes, "halves": int(nhalf), "absorbed": int(nab), "detached": int(ndet), "split": sorted(set(split)),
            "own": [int(x) for x in own], "no_twin": [int(x) for x in no_twin], "vote_mm": float(vote_mm)}
    return new, info


def label_components(lab, ta, tb, nF):
    """the connected pieces of each label (triangles sharing an edge and a label); scipy under freecadcmd, numpy otherwise (the selftest)"""
    m = lab[ta] == lab[tb]
    try:
        import scipy.sparse as _sp
        from scipy.sparse.csgraph import connected_components as _cc
        A = _sp.coo_matrix((np.ones(int(m.sum())), (ta[m], tb[m])), shape=(nF, nF))
        return _cc(A, directed=False)[1]
    except ImportError:
        a_, b_ = ta[m], tb[m]; c = np.arange(nF)
        while True:
            lo = np.minimum(c[a_], c[b_]); old = c.copy()
            np.minimum.at(c, a_, lo); np.minimum.at(c, b_, lo); c = c[c]
            if np.array_equal(c, old): break
        return np.unique(c, return_inverse=True)[1]


def knn(P, Q, k):
    """the k nearest of P to each of Q: (distances, indices) - scipy's cKDTree under freecadcmd, a chunked brute force otherwise"""
    P = np.asarray(P, float); Q = np.asarray(Q, float); k = int(min(k, len(P)))
    try:
        from scipy.spatial import cKDTree
        return cKDTree(P).query(Q, k=k, workers=-1)
    except ImportError:
        dd = np.empty((len(Q), k)); ii = np.empty((len(Q), k), int)
        for s0 in range(0, len(Q), 256):
            D = np.linalg.norm(Q[s0:s0 + 256, None, :] - P[None, :, :], axis=2)
            j = np.argsort(D, axis=1)[:, :k]; ii[s0:s0 + 256] = j; dd[s0:s0 + 256] = np.take_along_axis(D, j, 1)
        return (dd[:, 0], ii[:, 0]) if k == 1 else (dd, ii)


MIRROR_OFF = 1000000


def mirror_layout(Cn, Nn, At, F, pid, iscap, n, c, master="auto", band=0.3, cross_min=1.0, a_noise=0.5, frag=5.0, say=print):
    """THE LAYOUT MADE ON ONE SIDE AND MIRRORED (the agent's job_skin_mirror_labels.py v2-v5, R4 skin 1, 2026-10-06 - the rungs that made the
    layout mirror-check PASS; generic: any plane, any edit region that is its own mirror). numpy only.
    Cn, Nn, At: triangle centroids, unit normals, areas; F: triangles; pid: the face label of each triangle; iscap: the wall triangles
    (they keep their labels - skin-rim re-derives the caps from the body). The MASTER side ("+", "-", or "auto" = the side whose layout
    has more faces: a face missing on one side is the defect this exists to stop) keeps its faces; every slave triangle takes the face
    of the nearest LIKE-FACING master triangle at its mirror point (v3: a thin plate's other skin is often nearer); a face that truly
    spans the plane (triangles beyond `band` on both sides) stays ONE face across it (v2), unless it meets the plane only through a sliver
    under `cross_min` mm2 (v5: then it is a mirrored pair); a slave triangle with no like-facing master near its mirror point is filled
    from its smooth neighbours (v4); specks under `a_noise` mm2 join a neighbour, a face left in pieces keeps its largest and pieces
    under `frag` mm2 join the neighbour they touch most (v2).
    Returns (new labels, info): a twin's label is its master's + MIRROR_OFF; info has the master side, the faces across the plane, the
    mirror distances."""
    s = mirror_side(Cn, n, c)
    nc = ~iscap
    if master == "auto":
        plus = len(np.unique(pid[(s > band) & nc])); minus = len(np.unique(pid[(s < -band) & nc]))
        master = "+" if plus > minus else "-"
        say("mirror: MASTER auto - %d faces on the + side, %d on the - side -> %s (the side with more faces keeps them)" % (plus, minus, master))
    sgn = 1.0 if master == "+" else -1.0
    mst = (s * sgn >= 0.0); slv = ~mst
    mm = mst & nc; sl = slv & nc
    if not mm.any() or not sl.any():
        raise ValueError("one side of the plane holds no skin - the plane does not split this layout")
    q = reflect(Cn[sl], n, c); nq = reflect_dir(Nn[sl], n); Nm = Nn[mm]
    k = min(12, int(mm.sum()))
    dk, ik = knn(Cn[mm], q, k)
    if k == 1: dk = np.asarray(dk)[:, None]; ik = np.asarray(ik)[:, None]
    ok = np.einsum("ij,ikj->ik", nq, Nm[ik]) > 0.3
    first = np.where(ok.any(1), ok.argmax(1), 0)
    ix = ik[np.arange(len(ik)), first]; d = dk[np.arange(len(dk)), first]
    srcp = pid[mm][ix]
    pos = set(int(x) for x in np.unique(pid[(s > band) & nc])); neg = set(int(x) for x in np.unique(pid[(s < -band) & nc]))
    cross = pos & neg
    bandA = {}
    for t in np.nonzero((np.abs(s) < band) & nc)[0]: bandA[int(pid[t])] = bandA.get(int(pid[t]), 0.0) + float(At[t])
    thin = sorted(l for l in cross if bandA.get(l, 0.0) < cross_min)
    cross = cross - set(thin)
    new = pid.astype(np.int64).copy()
    new[np.nonzero(sl)[0]] = np.where(np.isin(srcp, list(cross)), srcp, srcp + MIRROR_OFF)
    ta, tb = tri_adjacency(F)
    smooth = (Nn[ta] * Nn[tb]).sum(1) > 0.5
    bad = np.nonzero(sl)[0][~ok.any(1)]; new[bad] = -1
    for _ in range(200):
        un = new < 0
        if not un.any(): break
        cand = {}
        for x, y in ((ta[smooth], tb[smooth]), (tb[smooth], ta[smooth])):
            m2 = un[x] & ~un[y]
            for tx, ly in zip(x[m2], new[y[m2]]): cand.setdefault(int(tx), {}); cand[int(tx)][int(ly)] = cand[int(tx)].get(int(ly), 0) + 1
        if not cand: break
        for tx, dd in cand.items(): new[tx] = max(dd.items(), key=lambda kv: kv[1])[0]
    left = new < 0
    if left.any(): new[left] = pid[left]
    for _ in range(20):
        cc = label_components(new, ta, tb, len(F)); ar = np.bincount(cc, weights=At); small = np.nonzero(ar < a_noise)[0]
        if not len(small): break
        smk = np.isin(cc, small); cr = cc[ta] != cc[tb]; best = {}
        for x, y in ((ta[cr], tb[cr]), (tb[cr], ta[cr])):
            m2 = smk[x] & ~smk[y] & ~iscap[y]
            for cx, ly in zip(cc[x[m2]], new[y[m2]]): best.setdefault(int(cx), {}); best[int(cx)][int(ly)] = best[int(cx)].get(int(ly), 0) + 1
        if not best: break
        for cx, dd in best.items():
            mk = (cc == cx) & ~iscap
            new[mk] = max(dd.items(), key=lambda kv: kv[1])[0]
    for _ in range(10):
        cc = label_components(new, ta, tb, len(F)); ar = np.bincount(cc, weights=At); moved = 0
        lab_of = {}
        for cx in np.unique(cc): lab_of[int(cx)] = int(new[np.nonzero(cc == cx)[0][0]])
        by = {}
        for cx, l_ in lab_of.items(): by.setdefault(l_, []).append(cx)
        for l_, cs in by.items():
            if len(cs) < 2: continue
            keep = max(cs, key=lambda x: ar[x])
            for cx in cs:
                if cx == keep or ar[cx] >= frag: continue
                mk = cc == cx
                if iscap[mk].any(): continue
                cnt = {}
                for x, y in ((ta, tb), (tb, ta)):
                    m2 = mk[x] & ~mk[y] & ~iscap[y]
                    for v in new[y[m2]]:
                        if int(v) != l_: cnt[int(v)] = cnt.get(int(v), 0) + 1
                if cnt: new[mk] = max(cnt, key=cnt.get); moved += 1
        if not moved: break
    info = {"master": master, "cross": sorted(int(x) for x in cross), "thin_pairs": thin, "slave_tris": int(sl.sum()),
            "no_like_facing": int(len(bad)), "mirror_d_p50": float(np.median(d)) if len(d) else 0.0,
            "mirror_d_p95": float(np.percentile(d, 95)) if len(d) else 0.0, "mirror_d_max": float(d.max()) if len(d) else 0.0}
    return new, info


def orig_rung(patches, pt_patch, pf, pon, frac=0.9, nmin=3):
    """THE FIRST RUNG OF THE FACE LADDER (the client 2026-10-07: "original to flat face to smoothed fit"): a face whose points (the ~1000 of
    skin-points) lie ON one original face - at least `nmin` of them, at least `frac` of its points, none OFF - IS that original face's
    surface (kind "orig", face = it); every face that has ON points gets face_src = the original face most of them lie on (skin-rim's
    wall-edge owners use it). the agent's job_skin_mirror_labels.py v6 (R4 skin 1). patches: dicts with "patch" and "kind"; pt_patch: the face
    of each point; pf: the original face each point projects to (-1 none); pon: ON. Returns the number made orig."""
    norig = 0
    for rec in patches:
        if rec.get("kind") == "cap": continue
        mk = pt_patch == rec["patch"]; n_ = int(mk.sum()); rec["points"] = n_
        if not n_: continue
        fs, cnt = np.unique(pf[mk & pon], return_counts=True)
        if len(fs):
            top = int(fs[np.argmax(cnt)]); ntop = int(cnt.max()); rec["face_src"] = top
            if ntop >= nmin and ntop >= frac * n_ and not (mk & ~pon).any():
                rec["kind"] = "orig"; rec["face"] = top; norig += 1
    return norig


def same_kind_groups(patches):
    """a face and its mirror twin are the same kind: orig only when both qualify (the agent v9's rule). Returns the number demoted."""
    grp = {}; n = 0
    for rec in patches:
        if rec.get("kind") == "cap" or rec.get("grp") is None: continue
        grp.setdefault(rec["grp"], []).append(rec)
    for rs in grp.values():
        if len(rs) > 1 and any(r["kind"] != "orig" for r in rs):
            for r in rs:
                if r["kind"] == "orig": r["kind"] = "changed"; r.pop("face", None); r["not_orig"] = "its mirror twin is not on an original surface"; n += 1
    return n


def is_flat(P, p95=0.08, pmax=0.25):
    """(flat?, p95, max, centre, the plane's in-plane axes e1 e2, normal): the points lie on one plane within p95 at the 95th
    percentile and pmax at worst - the second rung of the face ladder (the agent's plane rung, R4 skin 1 skB3c)"""
    P = np.asarray(P, float); c0 = P.mean(0)
    _, _, vh = np.linalg.svd(P - c0, full_matrices=False)
    dpl = np.abs((P - c0) @ vh[2])
    a, b = float(np.percentile(dpl, 95)), float(dpl.max())
    return (a <= p95 and b <= pmax), a, b, c0, vh[0], vh[1], vh[2]


def iso_dirs(n, e1, e2, tilt_deg=54.7):
    """THE TWO ISO VIEWS OF ONE FACE (the client 2026-10-07: "not straight at it, that hides ripples/lumps. Two iso views instead of one
    straight on"): the camera at two corners of the face's own frame - (n + e1 + e2) and (n - e1 + e2), 55 deg off the normal - looking
    at it; n the face's outward normal, e1/e2 its main in-face directions. 31bl: tilt_deg - a face in a concave corner (a fillet in a
    58 deg V) is hidden by its own neighbours at 55 deg; skin-look lowers the tilt until the camera's line of sight is clear."""
    n = _unit(n); e1 = _unit(e1 - (e1 @ n) * n); e2 = _unit(np.cross(n, e1))
    a_ = np.radians(float(tilt_deg)); c_, s_ = np.cos(a_), np.sin(a_)
    return [tuple(-_unit(c_ * n + s_ * _unit(e1 + e2))), tuple(-_unit(c_ * n + s_ * _unit(-e1 + e2)))]


def _closest_pt_tri(p, a, b, c):
    """the closest point of triangle (a, b, c) to p, vectorised over any leading shape (Ericson, Real-Time Collision Detection 5.1.5)"""
    ab = b - a; ac = c - a; ap = p - a
    d1 = np.einsum("...i,...i->...", ab, ap); d2 = np.einsum("...i,...i->...", ac, ap)
    bp = p - b; d3 = np.einsum("...i,...i->...", ab, bp); d4 = np.einsum("...i,...i->...", ac, bp)
    cp = p - c; d5 = np.einsum("...i,...i->...", ab, cp); d6 = np.einsum("...i,...i->...", ac, cp)
    vc = d1 * d4 - d3 * d2; vb = d5 * d2 - d1 * d6; va = d3 * d6 - d5 * d4
    den = va + vb + vc; den = np.where(np.abs(den) < 1e-30, 1e-30, den); v = vb / den; w = vc / den
    out = a + ab * v[..., None] + ac * w[..., None]
    e1 = d1 - d3; e1 = np.where(np.abs(e1) < 1e-30, 1e-30, e1); m = (vc <= 0) & (d1 >= 0) & (d3 <= 0); out = np.where(m[..., None], a + ab * (d1 / e1)[..., None], out)
    e2 = d2 - d6; e2 = np.where(np.abs(e2) < 1e-30, 1e-30, e2); m = (vb <= 0) & (d2 >= 0) & (d6 <= 0); out = np.where(m[..., None], a + ac * (d2 / e2)[..., None], out)
    e3 = (d4 - d3) + (d5 - d6); e3 = np.where(np.abs(e3) < 1e-30, 1e-30, e3); m = (va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0); out = np.where(m[..., None], b + (c - b) * ((d4 - d3) / e3)[..., None], out)
    m = (d1 <= 0) & (d2 <= 0); out = np.where(m[..., None], a, out)
    m = (d3 >= 0) & (d4 <= d3); out = np.where(m[..., None], b, out)
    m = (d6 >= 0) & (d5 <= d6); out = np.where(m[..., None], c, out)
    return out


_INC = {}; _CRT = {}
CLOSEST_LAST = {"exact": True, "why": "", "n": 0}
CLOSEST_NOT_EXACT = []
_CM_ELEMS = 400000
def _arr_sig(a):
    """31bq R7f: an array's CONTENT as a cache key (its shape, dtype and the md5 of its bytes) - the id + end-row sums of R5i (3) hit a stale cache on a mesh moved in place or
    reordered in its middle (rv_edge 2 / 3)"""
    a = np.asarray(a)
    try: return (tuple(a.shape), str(a.dtype), hashlib.md5(np.ascontiguousarray(a).tobytes()).hexdigest())
    except Exception: return (tuple(a.shape), str(a.dtype), id(a))
def closest_on_mesh(P, V, F, tree=None, k=12, return_tri=False):
    """31bq B19: the nearest point ON the mesh (point-to-triangle over the k nearest triangles by centroid) for each of P, and its distance. The vertex
    KD-tree the trace and the old deviation line used reads half an edge length on a straight border (a recorded process failure). Returns (Q, d) - and the
    triangle of each nearest point with return_tri (31bq R5f). 31bq R7f: EXACT or SAID - CLOSEST_LAST carries the call's exactness; a failure of the fast exact
    pass falls to the slow exact form; a failure of that too leaves the nearest-64 UPPER BOUND and says so (the pass had sat in a bare except: rv_com)."""
    _ck = (_arr_sig(V), _arr_sig(F))
    P = np.asarray(P, float).reshape(-1, 3); V = np.asarray(V, float); F = np.asarray(F, int)
    CLOSEST_LAST.clear(); CLOSEST_LAST.update({"exact": True, "why": "", "n": int(len(P))})
    if not len(P) or not len(F): return (P.copy(), np.zeros(len(P)), np.full(len(P), -1, int)) if return_tri else (P.copy(), np.zeros(len(P)))
    _crt = _CRT.get(_ck)
    if _crt is None:
        C = V[F].mean(1); _crt = (C, np.linalg.norm(V[F] - C[:, None, :], axis=2).max(1)); _CRT.clear(); _CRT[_ck] = _crt
    C, Rt = _crt
    from scipy.spatial import cKDTree
    if tree is None: tree = cKDTree(C)
    kk = int(min(max(k, 24), len(C))); _, J = tree.query(P, k=kk); J = np.asarray(J).reshape(len(P), -1)
    try:
        inc = _INC.get(_ck)
        if inc is None:
            fl = F.ravel(); order = np.argsort(fl, kind="stable"); tri_of = np.repeat(np.arange(len(F)), 3)[order]; starts = np.searchsorted(fl[order], np.arange(len(V) + 1))
            inc = (cKDTree(V), tri_of, starts); _INC.clear(); _INC[_ck] = inc
        vt, tri_of, starts = inc; _, JV = vt.query(P, k=int(min(6, len(V)))); JV = np.asarray(JV).reshape(len(P), -1)
        extra = [np.unique(np.concatenate([tri_of[starts[v]:starts[v + 1]] for v in row])) if len(row) else np.zeros(0, int) for row in JV]
        m = max((len(e) for e in extra), default=0)
        if m:
            Ex = np.repeat(J[:, :1], m, axis=1)
            for i_, e in enumerate(extra): Ex[i_, :len(e)] = e
            J = np.concatenate([J, Ex], axis=1)
    except Exception: pass
    A = V[F[J][:, :, 0]]; B = V[F[J][:, :, 1]]; Cc = V[F[J][:, :, 2]]
    Q = _closest_pt_tri(P[:, None, :], A, B, Cc)
    D = np.linalg.norm(Q - P[:, None, :], axis=2); i = np.argmin(D, axis=1); r = np.arange(len(P))
    Qb = Q[r, i].copy(); Db = D[r, i].copy(); Tb = J[r, i].copy()
    _why = ""
    try:
        # over the
        R99 = float(np.percentile(Rt, 99)) if len(Rt) else 0.0; big = np.nonzero(Rt > R99)[0]
        if len(big):
            rows = max(1, int(_CM_ELEMS // max(len(big), 1)))
            Ab, Bb, Cb = V[F[big, 0]][None, :, :], V[F[big, 1]][None, :, :], V[F[big, 2]][None, :, :]
            for s0 in range(0, len(P), rows):
                Ps = P[s0:s0 + rows]; rr = np.arange(len(Ps))
                Qg = _closest_pt_tri(Ps[:, None, :], Ab, Bb, Cb); Dg = np.linalg.norm(Qg - Ps[:, None, :], axis=2); jg = np.argmin(Dg, axis=1)
                m_ = Dg[rr, jg] < Db[s0:s0 + rows]; ix_ = np.nonzero(m_)[0]
                Db[s0 + ix_] = Dg[rr, jg][ix_]; Qb[s0 + ix_] = Qg[rr, jg][ix_]; Tb[s0 + ix_] = big[jg[ix_]]
        kq = int(min(64, len(C))); dq_, jq_ = tree.query(P, k=kq); dq_ = np.asarray(dq_, float).reshape(len(P), -1); jq_ = np.asarray(jq_, int).reshape(len(P), -1)
        for s0 in range(0, len(P), 1000):
            J2 = jq_[s0:s0 + 1000]; Ps = P[s0:s0 + 1000]; rr = np.arange(len(Ps))
            Q2 = _closest_pt_tri(Ps[:, None, :], V[F[J2][:, :, 0]], V[F[J2][:, :, 1]], V[F[J2][:, :, 2]]); D2 = np.linalg.norm(Q2 - Ps[:, None, :], axis=2); j2 = np.argmin(D2, axis=1)
            m_ = D2[rr, j2] < Db[s0:s0 + 1000]; ix_ = np.nonzero(m_)[0]
            Db[s0 + ix_] = D2[rr, j2][ix_]; Qb[s0 + ix_] = Q2[rr, j2][ix_]; Tb[s0 + ix_] = J2[rr, j2][ix_]
        _need = np.nonzero((dq_[:, -1] - R99 <= Db + 1e-12) if kq < len(C) else np.zeros(len(P), bool))[0]
        for i_ in _need:
            cand = np.asarray(tree.query_ball_point(P[i_], float(Db[i_]) + R99), int)
            if not len(cand): continue
            cand = cand[np.linalg.norm(C[cand] - P[i_], axis=1) - Rt[cand] <= Db[i_] + 1e-12]
            if not len(cand): continue
            Qi = _closest_pt_tri(P[i_][None, :], V[F[cand, 0]], V[F[cand, 1]], V[F[cand, 2]]); Di = np.linalg.norm(Qi - P[i_][None, :], axis=1); j_ = int(np.argmin(Di))
            if Di[j_] < Db[i_]: Db[i_] = Di[j_]; Qb[i_] = Qi[j_]; Tb[i_] = cand[j_]
    except Exception as _ex1:
        _why = "the fast exact pass: %s: %s" % (type(_ex1).__name__, str(_ex1)[:100])
        try:
            Rmax = float(Rt.max()) if len(Rt) else 0.0
            for i_ in range(len(P)):
                cand = np.asarray(tree.query_ball_point(P[i_], float(Db[i_]) + Rmax), int)
                if not len(cand): continue
                cand = cand[np.linalg.norm(C[cand] - P[i_], axis=1) - Rt[cand] <= Db[i_] + 1e-12]
                if not len(cand): continue
                Qi = _closest_pt_tri(P[i_][None, :], V[F[cand, 0]], V[F[cand, 1]], V[F[cand, 2]]); Di = np.linalg.norm(Qi - P[i_][None, :], axis=1); j_ = int(np.argmin(Di))
                if Di[j_] < Db[i_]: Db[i_] = Di[j_]; Qb[i_] = Qi[j_]; Tb[i_] = cand[j_]
            CLOSEST_LAST["slow"] = _why; _why = ""
        except Exception as _ex2:
            _why += "; the slow exact pass too: %s: %s" % (type(_ex2).__name__, str(_ex2)[:100])
    if _why:
        CLOSEST_LAST.update({"exact": False, "why": _why}); CLOSEST_NOT_EXACT.append(_why)
    return (Qb, Db, Tb) if return_tri else (Qb, Db)


def mesh_plane_section(V, T, n, c, eps=1e-6):
    """31bq OO (B19 (a)): the segments where the triangles T cross the plane n . x = c - (m, 2, 3). A trace on the mirror plane follows its face's section by
    the plane (its ridge): the nearest surface point of a V ridge lies on a flank, off the plane (x -1.19 on fill13's keel split). 31bq R7f (B2's NIT): a vertex
    ON the plane (|s| <= eps) is a point of the section from EITHER side (the s > 0 test had counted it as the - side: an edge lying in the plane came back from a +
    triangle only - rv_edge 4), a triangle lying in the plane gives its three edges, a zero-length segment is dropped"""
    V = np.asarray(V, float); T = np.asarray(T, int).reshape(-1, 3); n = np.asarray(n, float)
    if not len(T): return np.zeros((0, 2, 3))
    P = V[T]; s = P @ n - float(c); on = np.abs(s) <= eps; pts = []; msk = []
    for a in (0, 1, 2):
        pts.append(P[:, a]); msk.append(on[:, a])
    for a, b in ((0, 1), (1, 2), (2, 0)):
        m_ = ((s[:, a] > 0) != (s[:, b] > 0)) & ~on[:, a] & ~on[:, b]; den = s[:, a] - s[:, b]; tt = np.where(m_, s[:, a] / np.where(np.abs(den) < 1e-300, 1.0, den), 0.0)
        pts.append(P[:, a] + tt[:, None] * (P[:, b] - P[:, a])); msk.append(m_)
    pts = np.stack(pts, 1); msk = np.stack(msk, 1); cnt = msk.sum(1); out = []
    two = cnt == 2
    if two.any(): out.append(pts[two][msk[two]].reshape(-1, 2, 3))
    three = cnt == 3
    if three.any():
        Q3 = pts[three][msk[three]].reshape(-1, 3, 3); out.append(np.concatenate([Q3[:, [0, 1]], Q3[:, [1, 2]], Q3[:, [2, 0]]], 0))
    if not out: return np.zeros((0, 2, 3))
    seg = np.concatenate(out, 0)
    return seg[np.linalg.norm(seg[:, 1] - seg[:, 0], axis=1) > eps]


def nearest_on_segments(P, segs):
    """for each of P the nearest point on the segments (m, 2, 3) and its distance - (Q, d)"""
    P = np.asarray(P, float).reshape(-1, 3); segs = np.asarray(segs, float).reshape(-1, 2, 3)
    if not len(segs): return P.copy(), np.full(len(P), np.inf)
    a = segs[:, 0]; ab = segs[:, 1] - a; L2 = np.maximum((ab * ab).sum(1), 1e-18); Q = np.zeros_like(P); d = np.zeros(len(P)); step = max(1, 2_000_000 // len(segs))
    for s0 in range(0, len(P), step):
        Pi = P[s0:s0 + step]; tt = np.clip(((Pi[:, None, :] - a[None]) * ab[None]).sum(2) / L2[None], 0.0, 1.0); X = a[None] + tt[:, :, None] * ab[None]
        D = np.linalg.norm(X - Pi[:, None, :], axis=2); j = np.argmin(D, axis=1); r = np.arange(len(Pi)); Q[s0:s0 + step] = X[r, j]; d[s0:s0 + step] = D[r, j]
    return Q, d


def polyline_samples(P, step=0.1):
    """31bo fix 3c: points along the polyline P every `step` (its vertices included) - a measurement against a mesh border is a measurement against
    the border's SEGMENTS, not its vertices: on a coarse source one straight mesh edge can be 13.78 mm long, and a curve lying exactly on it read
    6.89 mm "off the mesh" by the nearest-vertex distance (b13's chains 50 / 116 / 68)"""
    P = np.asarray(P, float)
    if len(P) < 2: return P.copy()
    out = [P[0]]
    for a, b in zip(P[:-1], P[1:]):
        L = float(np.linalg.norm(b - a)); n = max(1, int(np.ceil(L / max(step, 1e-9))))
        for i in range(1, n + 1): out.append(a + (b - a) * (i / n))
    return np.array(out)
def crease_sense(Vu, F, pid, p, q, S, near=0.5):
    """the SENSE of the crease between layout faces p and q along the drawn line S (n, 3): +1 an inside corner (concave - each face rises into the
    other's air), -1 an outside corner (convex), from the mesh's own shared edges within `near` mm of the line: for each mesh edge (u, v) held by a
    triangle of p and a triangle of q, sign(det[v - u, w_p - u, w_q - u]) (w_p / w_q the triangles' far vertices) times the angle between the two
    triangles' normals, weighted by the edge's length; the sum over the edges' weighted angles. The same number from either face order and under a
    reflection of an outward-wound mesh. Returns (score in [-1, 1] or None, the number of shared edges found). (31bo: a one-face centroid probe
    read a twin pair opposite - the twin's p was the coarse face.)"""
    Vu = np.asarray(Vu, float); F = np.asarray(F, int); pid = np.asarray(pid)
    tp = np.nonzero(pid == p)[0]; tq = np.nonzero(pid == q)[0]
    if not len(tp) or not len(tq): return None, 0
    def dir_edges(tris):
        E = {}
        for ti in tris:
            a, b, c = (int(x) for x in F[ti])
            for u, v, w in ((a, b, c), (b, c, a), (c, a, b)): E[(u, v)] = w
        return E
    Ep = dir_edges(tp); Eq = dir_edges(tq)
    S = np.asarray(S, float).reshape(-1, 3)
    from scipy.spatial import cKDTree
    kd = cKDTree(S) if len(S) else None
    num = 0.0; den = 0.0; n_e = 0
    for (u, v), wp in Ep.items():
        wq = Eq.get((v, u))
        if wq is None: continue
        m = 0.5 * (Vu[u] + Vu[v])
        if kd is not None and kd.query(m)[0] > near: continue
        e = Vu[v] - Vu[u]; L = float(np.linalg.norm(e))
        if L < 1e-9: continue
        n1 = np.cross(e, Vu[wp] - Vu[u]); n2 = np.cross(Vu[u] - Vu[v], Vu[wq] - Vu[v])
        a1 = np.linalg.norm(n1); a2 = np.linalg.norm(n2)
        if a1 < 1e-12 or a2 < 1e-12: continue
        ang = float(np.arccos(np.clip((n1 / a1) @ (n2 / a2), -1.0, 1.0)))
        sgn = float(np.sign(np.linalg.det(np.stack([e, Vu[wp] - Vu[u], Vu[wq] - Vu[u]]))))
        num += L * sgn * ang; den += L * ang; n_e += 1
    if n_e == 0 or den <= 1e-12: return None, 0
    return float(num / den), n_e


def local_face_normals(Vu, F, pid, f, S, k=8, reach=2.5, sheet_dot=0.5):
    """31bp fix 9 - A FACE'S NORMAL AT A CREASE IS ITS OWN SHEET'S THERE. For each point of S the triangle of layout face f nearest BY TRUE DISTANCE
    (tri_dist, among the k nearest centroids) sets the sheet; of the k nearest within `reach` mm only those facing with it (normal . its normal >
    sheet_dot) are averaged - the others (the far side of a thin or wrapping face) are left out and counted. The plain k-mean mixed both sides of
    the agent's b27b stem chamfer 1722 (its far side 1-2 mm away faces the other way): beta between the two faces read 58 deg where the outward normals are
    122 apart, so t = 0.84 for 2.7, the sagitta 0.22 for 1.6, and the swept arc was a 248 deg loop of R 0.5 standing 61 deg off both faces (the 77 / 56
    pinch). The normals are the mesh's own winding (outward on a consistently wound source). Returns (n_face (3,) - the mean of the per-sample
    normals -, n_loc (n, 3), info {"excluded": the other-sheet triangles left out over all samples, "nearest_mm": the farthest nearest triangle});
    (None, None, info) when the face has no triangle."""
    Vu = np.asarray(Vu, float); F = np.asarray(F, int); pid = np.asarray(pid); S = np.asarray(S, float).reshape(-1, 3)
    T_ = F[pid == f]
    if not len(T_) or not len(S): return None, None, {"excluded": 0, "nearest_mm": None}
    n_ = np.cross(Vu[T_[:, 1]] - Vu[T_[:, 0]], Vu[T_[:, 2]] - Vu[T_[:, 0]]); a_ = np.linalg.norm(n_, axis=1); ok_ = a_ > 1e-9
    T_ = T_[ok_]; C_ = Vu[T_].mean(1); N_ = n_[ok_] / a_[ok_][:, None]
    if not len(C_): return None, None, {"excluded": 0, "nearest_mm": None}
    kk = int(min(max(k, 1), len(C_))); dk, jk = knn(C_, S, kk); dk = np.asarray(dk, float).reshape(len(S), -1); jk = np.asarray(jk, int).reshape(len(S), -1)
    n_loc = np.zeros((len(S), 3)); excl = 0
    for i in range(len(S)):
        J = jk[i]; A = Vu[T_[J, 0]]; B = Vu[T_[J, 1]]; Cc = Vu[T_[J, 2]]
        dt = tri_dist(np.repeat(S[i][None, :], len(J), 0), A, B, Cc)
        ref = N_[J[int(np.argmin(dt))]]
        near = dk[i] < reach; same = near & ((N_[J] @ ref) > sheet_dot)
        excl += int((near & ~same).sum())
        v = N_[J[same]].mean(0) if same.any() else ref
        nv = float(np.linalg.norm(v)); n_loc[i] = v / nv if nv > 1e-9 else ref
    n_f = n_loc.mean(0); n_f = n_f / max(float(np.linalg.norm(n_f)), 1e-9)
    return n_f, n_loc, {"excluded": int(excl), "nearest_mm": float(dk[:, 0].max())}


def crease_side(Vu, F, pid, f, other, S, D, near=0.5):
    """31bp fix 9b - THE SIDE OF A FACE AT ITS CREASE FROM THE MESH'S OWN TOPOLOGY: for each mesh edge held by a triangle of layout face f and one of
    `other` within `near` mm of the line S (n, 3), the f-triangle's far vertex lies on f's side by construction; its sign against D (the offset direction
    proposed at the nearest sample, (n, 3)) is summed. Returns (score in [-1, 1] or None, the shared edges found): > 0 keeps D, < 0 flips it. (the agent's
    b27b 77 / 56: the chamfer 1722 wraps past the crease, its centroid vote was +46 of 178 - undecided - and the fallback took the far end of a 10 mm
    curving border on the wrong side: the offset went 0.84 mm beyond the crease instead of onto the face and the swept arc looped 248 deg.)"""
    Vu = np.asarray(Vu, float); F = np.asarray(F, int); pid = np.asarray(pid); S = np.asarray(S, float).reshape(-1, 3); D = np.asarray(D, float).reshape(-1, 3)
    tf = np.nonzero(pid == f)[0]; to = np.nonzero(pid == other)[0]
    if not len(tf) or not len(to) or not len(S) or len(D) != len(S): return None, 0
    def dir_edges(tris):
        E = {}
        for ti in tris:
            a, b, c = (int(x) for x in F[ti])
            for u, v, w in ((a, b, c), (b, c, a), (c, a, b)): E[(u, v)] = w
        return E
    Ef = dir_edges(tf); Eo = dir_edges(to)
    mids = []; ws = []
    for (u, v), wf in Ef.items():
        if (v, u) not in Eo: continue
        mids.append(0.5 * (Vu[u] + Vu[v])); ws.append(Vu[wf])
    if not mids: return None, 0
    mids = np.array(mids); ws = np.array(ws)
    d_, i_ = knn(S, mids, 1); d_ = np.asarray(d_, float).reshape(-1); i_ = np.asarray(i_, int).reshape(-1)
    keep = d_ <= near
    if not keep.any(): return None, 0
    sg = np.sign(np.einsum("ij,ij->i", ws[keep] - mids[keep], D[i_[keep]]))
    sg = sg[sg != 0]
    if not len(sg): return None, int(keep.sum())
    return float(sg.mean()), int(len(sg))


def taper_weights(S, run_out, ends=(0, 1)):
    """31bm - A BLEND WHOSE RADIUS SHRINKS TO NOTHING AT THE JUNCTION: per sample of the crease S (ordered end to end), a weight 0 at each tapered
    end rising to 1 over run_out mm of arc length (a smoothstep), 1 elsewhere; the fillet's t, sagitta and offset scale by it, so the offset lines
    come back to the junction and the blend face is a lens - no cap, no cut of the neighbours' borders. A crease shorter than two run-outs never
    reaches the full radius (the caller says so)."""
    S = np.asarray(S, float); s = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(S, axis=0), axis=1))]); ro = max(float(run_out), 1e-9)
    def _w(x): x = np.clip(x / ro, 0.0, 1.0); return x * x * (3.0 - 2.0 * x)
    w = np.ones(len(S))
    if 0 in ends: w = w * _w(s)
    if 1 in ends: w = w * _w(s[-1] - s)
    return w


def iso_dirs4(n, e1, e2, tilt_deg=54.7):
    """THE FOUR ISO DIRECTIONS OF ONE FACE - the camera at each corner of the face's own frame (+-e1 +-e2), tilt_deg off the normal n,
    looking at it. 31bl: skin-look scores each by visible_fraction() and keeps the two that SEE the face - a face in a concave corner is
    hidden from some corners by its own neighbours. iso_dirs() is the first two of these."""
    n = _unit(n); e1 = _unit(e1 - (e1 @ n) * n); e2 = _unit(np.cross(n, e1))
    a_ = np.radians(float(tilt_deg)); c_, s_ = np.cos(a_), np.sin(a_)
    return [tuple(-_unit(c_ * n + s_ * _unit(sx * e1 + sy * e2))) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]


def visible_fraction(V, T, own, P, d):
    """31bl (the client 2026-10-12: "Your rendering a bottom feature from the top and can't actually see anything"): the fraction of the sample
    points P (points ON the face whose triangles are `own`, a bool mask over T) that a camera looking along d SEES - the ray from the point
    toward the camera meets no OTHER triangle of the mesh (the face's own triangles are not in its way). numpy only: a screen-box cut, then
    Moller-Trumbore per sample; 1.0 when nothing can block. A line-of-sight probe at a few points along one ray missed what lay further out."""
    d3 = _unit(np.asarray(d, float)); P = np.asarray(P, float).reshape(-1, 3)
    Tn = np.asarray(T)[~np.asarray(own, bool)]
    if len(P) == 0 or len(Tn) == 0: return 1.0
    a_ = np.array([1.0, 0.0, 0.0]) if abs(d3[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    r3 = _unit(np.cross(d3, a_)); u3 = np.cross(r3, d3)
    Vt = np.asarray(V, float)[Tn]
    px, py = P @ r3, P @ u3; tx, ty = Vt @ r3, Vt @ u3
    m = (tx.max(1) >= px.min()) & (tx.min(1) <= px.max()) & (ty.max(1) >= py.min()) & (ty.min(1) <= py.max())
    Vt = Vt[m]
    if len(Vt) == 0: return 1.0
    D = -d3; E1 = Vt[:, 1] - Vt[:, 0]; E2 = Vt[:, 2] - Vt[:, 0]; H = np.cross(D, E2); det = (E1 * H).sum(1)
    ok = np.abs(det) > 1e-12; E1, E2, H, V0, inv = E1[ok], E2[ok], H[ok], Vt[ok, 0], 1.0 / det[ok]
    if len(V0) == 0: return 1.0
    seen = 0
    for p_ in P:
        S = p_ - V0; u = (S * H).sum(1) * inv; Q = np.cross(S, E1); v = (Q @ D) * inv; tt = (E2 * Q).sum(1) * inv
        if not np.any((u >= 0) & (u <= 1) & (v >= 0) & (u + v <= 1) & (tt > 1e-3)): seen += 1
    return seen / float(len(P))


def first_blocker(V, T, own, P, d, fid):
    """31bl: for the sample points P of a face seen along d, the face (fid per triangle) of the FIRST triangle each ray toward the camera meets
    and how far away it lies - (the commonest blocking face, the median distance) over the rays that meet one; (None, None) when none does.
    A face no corner sees from either side is covered by another within a millimetre: a slit of air or a pocket the piece encloses."""
    d3 = _unit(np.asarray(d, float)); P = np.asarray(P, float).reshape(-1, 3); own = np.asarray(own, bool)
    idx = np.nonzero(~own)[0]; Tn = np.asarray(T)[idx]
    if len(P) == 0 or len(Tn) == 0: return None, None
    Vt = np.asarray(V, float)[Tn]; D = -d3
    E1 = Vt[:, 1] - Vt[:, 0]; E2 = Vt[:, 2] - Vt[:, 0]; H = np.cross(D, E2); det = (E1 * H).sum(1); ok = np.abs(det) > 1e-12
    E1, E2, H, V0, inv, idx = E1[ok], E2[ok], H[ok], Vt[ok, 0], 1.0 / det[ok], idx[ok]
    hits = []
    for p_ in P:
        S = p_ - V0; u = (S * H).sum(1) * inv; Q = np.cross(S, E1); v = (Q @ D) * inv; tt = (E2 * Q).sum(1) * inv
        m = (u >= 0) & (u <= 1) & (v >= 0) & (u + v <= 1) & (tt > 1e-3)
        if m.any():
            k_ = np.nonzero(m)[0][np.argmin(tt[m])]; hits.append((int(np.asarray(fid)[idx[k_]]), float(tt[k_])))
    if not hits: return None, None
    fs_ = [h_[0] for h_ in hits]; f_ = max(set(fs_), key=fs_.count)
    return f_, float(np.median([h_[1] for h_ in hits if h_[0] == f_]))


def wall_views(cap_faces, cap_wall, pad=3.0):
    """one view per edit region wall that holds body section faces (the caps), looking at it from outside, a little from above:
    the box round that wall's caps grown `pad` mm. cap_faces = Part faces (wall_caps.brep), cap_wall = the wall index of each."""
    out = []
    for w in sorted(set(cap_wall)):
        fs = [f for f, cw in zip(cap_faces, cap_wall) if cw == w]
        if not fs: continue
        bb = fs[0].BoundBox
        for f in fs[1:]: bb.add(f.BoundBox)
        n_in, _ = WALLS[w]
        d = _unit(-(-n_in) + np.array([0.0, 0.0, -0.3]))
        fb = (bb.XMin - pad, bb.XMax + pad, bb.YMin - pad, bb.YMax + pad, bb.ZMin - pad, bb.ZMax + pad)
        out.append(("wall%d" % w, tuple(d), fb, 1500, "edit region wall %d from outside (its %d body section face(s))" % (w, len(fs))))
    return out


_PICS_REC = {}; _PICS_DEL = set()
def _pics_path(): return os.path.join(OUT, ".pictures.json")
def _pics_load():
    global _PICS_REC
    if not _PICS_REC:
        try: _PICS_REC = json.load(open(_pics_path(), encoding="utf-8"))
        except (OSError, ValueError): _PICS_REC = {}
    return _PICS_REC
def _pics_save():
    try:      # over the
        try: disk = json.load(open(_pics_path(), encoding="utf-8"))
        except (OSError, ValueError): disk = {}
        if not isinstance(disk, dict): disk = {}
        for k_ in _PICS_DEL: disk.pop(k_, None)
        disk.update(_PICS_REC)
        with open(_pics_path(), "w", encoding="utf-8") as fh: json.dump(disk, fh, indent=0)
    except OSError: pass
_VIEWV = []; _STEPV = []
def _view_version():
    """31bq OO (B40 (4)): the renderers' own source in every picture's key - a changed view never reads an old frame back as a HIT. 31bq R7f: sk_lib's WHOLE file
    (the hand list of nine functions missed rasterize, vertex_normals, mesh_quality, _gap_to_segments - the code they call; B2's finding)"""
    if not _VIEWV:
        try:
            _f = os.path.abspath(__file__); _f = _f[:-1] if _f.lower().endswith(".pyc") else _f
            _VIEWV.append(md5(_f)[:8] if os.path.isfile(_f) else "nosrc")
        except Exception: _VIEWV.append("nosrc")
    return _VIEWV[0]
def _step_file():
    """31bq R7f: the DRAWING STEP's own file - the OUTERMOST frame of the call stack that runs from a file. FreeCADCmd <step>.py runs the step through a COPY of
    __main__'s dict (Interpreter.runFile local=true): sys.modules['__main__'] never carries its __file__, so R5i's key held the constant 'none:__main__' under the kit's
    own launcher and a changed draw block read every old frame back as a HIT (B2's rv_launch). Then __main__'s __file__ (runpy), then sys.argv's script; None when
    nothing names a file."""
    import sys as _sys
    here = os.path.abspath(__file__); here = here[:-1] if here.lower().endswith(".pyc") else here
    found = None
    try:
        f_ = _sys._getframe(1)
        while f_ is not None:
            fn_ = f_.f_code.co_filename
            try:
                if fn_ and not fn_.startswith("<") and os.path.isfile(fn_) and os.path.abspath(fn_) != here: found = os.path.abspath(fn_)
            except Exception: pass
            f_ = f_.f_back
    except Exception: pass
    if found: return found
    for c_ in (getattr(_sys.modules.get("__main__"), "__file__", None), (_sys.argv[-1] if getattr(_sys, "argv", None) else None)):
        try:
            if c_ and os.path.isfile(c_) and str(c_).lower().endswith((".py", ".fcmacro")): return os.path.abspath(c_)
        except Exception: pass
    return None
def pic_key(*paths, **extra):
    """the key of a picture: the md5 of each named file's bytes + the extras (PICS, a mode) + the renderers' version"""
    h = hashlib.md5(); h.update(_view_version().encode())
    if not _STEPV:
        import sys as _sys
        try:
            _sf = _step_file(); _STEPV.append(("step:%s:%s" % (os.path.basename(_sf), md5(_sf))) if _sf else ("none:step:%r" % time.time()))
        except Exception: _STEPV.append("unread:step:%r" % time.time())
        try:
            _f = getattr(_sys.modules.get("kitlib_render"), "__file__", None)
            _STEPV.append(md5(_f) if (_f and os.path.isfile(_f)) else "none:kitlib_render")
        except Exception: _STEPV.append("unread:kitlib_render")
    for _v in _STEPV: h.update(_v.encode())
    for p_ in paths:
        if p_ and os.path.isfile(p_):
            h.update(os.path.basename(p_).encode()); h.update(md5(p_).encode())
        else:
            h.update(("missing:%s" % os.path.basename(str(p_))).encode())
    for k_ in sorted(extra): h.update(("%s=%s" % (k_, extra[k_])).encode())
    return h.hexdigest()
PIC_HITS = []; PIC_MISSES = []
def pic_hit(path, key, count=True):
    """True when the frame on disk was drawn from this key (it stays; nothing is drawn)"""
    rec = _pics_load().get(os.path.basename(path))
    hit = bool(key) and os.path.isfile(path) and isinstance(rec, dict) and rec.get("key") == key
    if hit and count and path not in PIC_HITS and path not in PIC_MISSES: PIC_HITS.append(path)
    return hit
def pic_mark(path, key):
    if not key: return
    _pics_load()[os.path.basename(path)] = {"key": key, "when": time.strftime("%Y-%m-%d %H:%M:%S")}; _pics_save()
    if path not in PIC_MISSES: PIC_MISSES.append(path)
def clear_frames(prefix, key=None, also=()):
    """remove this prefix's frames that are not HITs of the key - nor of a key in `also` (31bq B18 R7W: skin-look's vanished frames carry their own key, the
    records they draw, and the look's other frames are not redrawn when only those change) (none of an earlier artefact's frames is left beside this run's - L119)"""
    n = 0
    for f_ in os.listdir(OUT):
        if f_.startswith(prefix) and f_.endswith(".png"):
            p_ = os.path.join(OUT, f_)
            if key and pic_hit(p_, key): continue
            if any(k_ and pic_hit(p_, k_, count=False) for k_ in also): continue
            try: os.remove(p_); n += 1
            except OSError: pass
            _pics_load().pop(f_, None); _PICS_DEL.add(f_)
    _pics_save(); return n
def pic_report(what=""):
    """one line: how many frames this run drew and how many it found unchanged"""
    _nk = (" - the picture key carries NO step source (no file on the call stack names the drawing step): every frame of this run is drawn as a MISS (31bq R7f)") if (_STEPV and not str(_STEPV[0]).startswith("step:")) else ""
    return "pictures%s: %d drawn (MISS), %d unchanged (HIT - drawn from the same inputs before)%s" % ((" " + what) if what else "", len(PIC_MISSES), len(PIC_HITS), _nk)


_SRCQ = {}
def source_quality(VP, TP):
    """31bq B40: the quality of the SOURCE mesh the pre-build frames draw (the content's own conforming tessellation, closed) - judged once per mesh, carried
    in every such frame's record (frames.jsonl 'quality') so the layout / points / wires verdicts rest on a judged picture too; a defective source stamps them"""
    try:
        key = (int(len(VP)), int(len(TP)), round(float(np.asarray(VP, float)[:64].sum()), 3))
        if key not in _SRCQ:
            q = mesh_quality(np.asarray(VP, float), np.asarray(TP, int), np.zeros(len(TP), int), True)
            _SRCQ[key] = {"tris": int(len(TP)), "how": "the source mesh (the content tessellated once by skin-source)", "open_edges": q.get("open_edges"), "seams": q.get("seams"), "cracks": q.get("cracks"),
                          "gap_max_mm": q.get("gap_max_mm"), "defective": bool(q.get("cracks")), "why": ("%d crack(s) in the source mesh (gap up to %.3f mm)" % (q.get("cracks") or 0, q.get("gap_max_mm") or 0.0)) if q.get("cracks") else ""}
        return _SRCQ[key]
    except Exception as ex:
        return {"tris": int(len(TP)) if TP is not None else 0, "how": "the source mesh", "defective": False, "why": "", "note": "quality not measured: %s" % str(ex)[:60]}


def _clip_mask(VP, TP, gb):
    """31bq B40: the triangles a frame draws - every triangle that REACHES the grown box. 31bq OO (B40 (6)): by the triangle's own box against the frame's (a vertex /
    centroid test dropped a large triangle crossing the box with no vertex inside). 31bq R7f (B2's NIT): that box overlap is the PREFILTER and the separating-axis
    triangle / box test decides - a large slanted facet beside the region whose own box overlapped the frame's was drawn into opaque frames with no point inside (rv_edge 5)"""
    VP = np.asarray(VP, float); TP = np.asarray(TP, int).reshape(-1, 3)
    if not len(TP): return np.zeros(0, bool)
    Pt = VP[TP]; lo = Pt.min(axis=1); hi = Pt.max(axis=1)
    m = (hi[:, 0] >= gb[0]) & (lo[:, 0] <= gb[1]) & (hi[:, 1] >= gb[2]) & (lo[:, 1] <= gb[3]) & (hi[:, 2] >= gb[4]) & (lo[:, 2] <= gb[5])
    idx = np.nonzero(m)[0]
    if not len(idx): return m
    cb = np.array([(gb[0] + gb[1]) / 2.0, (gb[2] + gb[3]) / 2.0, (gb[4] + gb[5]) / 2.0]); hb = np.array([(gb[1] - gb[0]) / 2.0, (gb[3] - gb[2]) / 2.0, (gb[5] - gb[4]) / 2.0]) + 1e-9
    Q = Pt[idx] - cb[None, None, :]; E = np.stack([Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 1], Q[:, 0] - Q[:, 2]], 1)
    nrm = np.cross(E[:, 0], E[:, 1]); ok = np.abs((nrm * Q[:, 0]).sum(1)) <= (hb[None, :] * np.abs(nrm)).sum(1)
    for j in range(3):
        u = np.zeros(3); u[j] = 1.0
        for i in range(3):
            ax = np.cross(E[:, i], u[None, :]); p = np.einsum("kvj,kj->kv", Q, ax); rad = (hb[None, :] * np.abs(ax)).sum(1)
            ok &= ~((p.min(1) > rad) | (p.max(1) < -rad))
    m[idx[~ok]] = False
    return m


def stamp_png(path, q, y0=40):
    """31bq B40 (LL): the RENDER DEFECTIVE band drawn onto a SAVED frame (the layout and label frames are drawn by kitlib_render, not by this module's view)"""
    if not (isinstance(q, dict) and q.get("defective")): return False
    try:
        from PIL import Image, ImageDraw
        im = Image.open(path).convert("RGB"); od = ImageDraw.Draw(im); _stamp_if_defective(im, od, q, y0); im.save(path); return True
    except Exception: return False


def _stamp_if_defective(out, od, q, y0):
    """a red band across the frame when its mesh is defective (the piece view's rule, now on the pre-build frames too)"""
    if not (isinstance(q, dict) and q.get("defective")): return
    try:
        od.rectangle([0, y0, out.width, y0 + 26], fill=(170, 20, 20)); od.text((8, y0 + 4), ("RENDER DEFECTIVE - NO EVIDENCE: %s" % q.get("why", ""))[:160], fill=(255, 255, 255), font=F16)
    except Exception: pass


def _title_bars(dr, im, title, axes):
    """31bx (R5 F5 / R6 F11): the title wrapped to the frame's width - one black bar per line (a long title had run off the right edge of the LAYOUT / SP12 / WIRE frames)"""
    txt = "%s   [%s]" % (title, axes); words = str(txt).split(" "); lines_ = []; cur = ""
    for w_ in words:
        t_ = (cur + " " + w_).strip()
        if not cur or dr.textbbox((0, 0), t_)[2] <= im.width - 8: cur = t_
        else: lines_.append(cur); cur = w_
    if cur: lines_.append(cur)
    dr.rectangle([0, 0, im.width, 18 * max(1, len(lines_))], fill=(0, 0, 0))
    for i_, l_ in enumerate(lines_): dr.text((4, 2 + 18 * i_), l_, fill=(255, 255, 80))
    return len(lines_)


def view(R, out_path, VP, TP, d, fbox, W, title, head, lines, draw=None, C=None, legend=(), key=None):
    if key and pic_hit(out_path, key): return "HIT"
    foc = corners(fbox); pad = 1.0
    gb = (fbox[0] - 4, fbox[1] + 4, fbox[2] - 4, fbox[3] + 4, fbox[4] - 4, fbox[5] + 4)
    m = _clip_mask(VP, TP, gb); _q = source_quality(VP, TP)
    im, mmpx, x0, y1, r3, u3 = render_transparent(R, VP, TP[m], d, foc, W, pad, None if C is None else C[m])
    dr = ImageDraw.Draw(im)
    proj = lambda P: [tuple(v) for v in np.stack([(np.asarray(P) @ r3 - x0) / mmpx, (y1 - np.asarray(P) @ u3) / mmpx], axis=1)]
    if draw: draw(dr, proj)
    _title_bars(dr, im, title, R.axes_label(r3, u3))
    bar = 10.0 / mmpx; dr.line([10, im.height - 12, 10 + bar, im.height - 12], fill=(255, 255, 255), width=3)
    dr.text((12, im.height - 30), "10 mm  (%.3f mm/px)" % mmpx, fill=(255, 255, 255))
    out = Image.new("RGB", (im.width, im.height + 40 + 26 * 3 + 24 * len(lines) + 10), (16, 16, 20))
    od = ImageDraw.Draw(out); od.text((10, 8), head, fill=(255, 235, 120), font=F22); out.paste(im, (0, 40))
    y = im.height + 46; x = 10
    for colr, t in legend:
        tw = od.textbbox((0, 0), t, font=F16)[2]
        if x + 30 + tw > out.width - 10: y += 26; x = 10
        od.rectangle([x, y + 3, x + 22, y + 19], fill=colr); od.text((x + 30, y + 2), t, fill=(235, 235, 235), font=F16); x += 44 + tw
    y += 30
    for ln in lines:
        od.text((10, y), ln, fill=(235, 235, 235), font=F16); y += 24
    _stamp_if_defective(out, od, _q, 40)
    out.save(out_path)
    if hasattr(R, "index_frame"): R.index_frame(out_path, fbox, d, head, quality=_q)
    if key: pic_mark(out_path, key)
    return "MISS"


OCC_TOL = 0.40


def _wrap(od, text, font, width):
    """the words of `text` in lines that fit `width` pixels (textbbox); never an empty list"""
    words = str(text).split(" "); lines = []; cur = ""
    for w_ in words:
        t_ = (cur + " " + w_).strip()
        if not cur or od.textbbox((0, 0), t_, font=font)[2] <= width: cur = t_
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines or [""]


def vertex_normals(V, T, L, crease_deg=30.0):
    """31bn fix 4 - SMOOTH SHADING FROM THE SURFACE: one normal per (vertex, face L) - the area-weighted mean of the face's triangles at that
    vertex, so a crease BETWEEN faces stays sharp and a face's own smoothness shows instead of its facets (the reviewers read flat facets as
    crumple). A corner whose mean turns more than crease_deg from its own triangle (a fold inside one face the mesh cannot smooth) keeps the
    flat normal. Returns (len(T), 3, 3): the normal at each corner of each triangle."""
    V = np.asarray(V, float); T = np.asarray(T, int); L = np.asarray(L).astype(np.int64)
    if len(T) == 0: return np.zeros((0, 3, 3))
    P = V[T]; fn = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    key = T.ravel().astype(np.int64) * (int(L.max()) + 2) + np.repeat(L + 1, 3)
    u, inv = np.unique(key, return_inverse=True); inv = inv.reshape(-1)
    acc = np.zeros((len(u), 3)); np.add.at(acc, inv, np.repeat(fn, 3, axis=0))
    acc /= np.maximum(np.linalg.norm(acc, axis=1), 1e-12)[:, None]
    N = acc[inv].reshape(len(T), 3, 3)
    fnu = fn / np.maximum(np.linalg.norm(fn, axis=1), 1e-12)[:, None]
    flat = (N * fnu[:, None, :]).sum(2) < np.cos(np.radians(float(crease_deg)))
    N[flat] = np.broadcast_to(fnu[:, None, :], N.shape)[flat]
    return N


def rasterize(X, Y, Z, T, W, H, max_frag=1_500_000):
    """31bn fix 4 - A TRUE Z-BUFFER (the painter's order by mean depth painted hidden faces over visible ones: a planar face's few large triangles
    sort by their centre). Every triangle's pixels (its screen box, the centre of each pixel inside it by barycentric coordinates), its depth
    interpolated there; the NEAREST triangle per pixel wins. numpy only: the triangles grouped by the size of their screen box (most are a
    pixel or two), each group tested against its grid at once. Returns ID (H, W; -1 = background), ZB (the depth), BW (H, W, 3: the winning
    triangle's barycentric weights - for the smooth normals)."""
    T = np.asarray(T, int); n = len(T)
    ID = np.full((H, W), -1, np.int64); ZB = np.full((H, W), np.inf); BW = np.zeros((H, W, 3))
    if n == 0: return ID, ZB, BW
    XT, YT, ZT = np.asarray(X, float)[T], np.asarray(Y, float)[T], np.asarray(Z, float)[T]
    den = (YT[:, 1] - YT[:, 2]) * (XT[:, 0] - XT[:, 2]) + (XT[:, 2] - XT[:, 1]) * (YT[:, 0] - YT[:, 2])
    xmin = np.clip(np.floor(XT.min(1)), 0, W - 1).astype(int); xmax = np.clip(np.ceil(XT.max(1)), 0, W - 1).astype(int)
    ymin = np.clip(np.floor(YT.min(1)), 0, H - 1).astype(int); ymax = np.clip(np.ceil(YT.max(1)), 0, H - 1).astype(int)
    live = (np.abs(den) > 1e-12) & (XT.max(1) >= 0) & (XT.min(1) <= W - 1) & (YT.max(1) >= 0) & (YT.min(1) <= H - 1)
    size = np.maximum(xmax - xmin, ymax - ymin) + 1
    frags = []; Kb = 1
    while Kb <= 8192:
        sel = np.nonzero(live & (size <= Kb) & (size > Kb // 2))[0]
        if len(sel):
            ox, oy = np.meshgrid(np.arange(Kb), np.arange(Kb)); ox = ox.ravel(); oy = oy.ravel()
            step = max(1, max_frag // (Kb * Kb))
            for s0 in range(0, len(sel), step):
                idx = sel[s0:s0 + step]
                px = xmin[idx][:, None] + ox[None, :]; py = ymin[idx][:, None] + oy[None, :]
                ok = (px <= xmax[idx][:, None]) & (py <= ymax[idx][:, None])
                cx = px + 0.5; cy = py + 0.5; dn = den[idx][:, None]; x2 = XT[idx, 2][:, None]; y2 = YT[idx, 2][:, None]
                l0 = ((YT[idx, 1] - YT[idx, 2])[:, None] * (cx - x2) + (XT[idx, 2] - XT[idx, 1])[:, None] * (cy - y2)) / dn
                l1 = ((YT[idx, 2] - YT[idx, 0])[:, None] * (cx - x2) + (XT[idx, 0] - XT[idx, 2])[:, None] * (cy - y2)) / dn
                l2 = 1.0 - l0 - l1
                ok &= (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
                if not ok.any(): continue
                tri = np.broadcast_to(idx[:, None], ok.shape)[ok]
                z = (l0 * ZT[idx, 0][:, None] + l1 * ZT[idx, 1][:, None] + l2 * ZT[idx, 2][:, None])[ok]
                frags.append(((py[ok] * W + px[ok]).astype(np.int64), z, tri, l0[ok], l1[ok]))
        Kb *= 2
    if not frags: return ID, ZB, BW
    pix = np.concatenate([f[0] for f in frags]); z = np.concatenate([f[1] for f in frags]); tri = np.concatenate([f[2] for f in frags])
    l0 = np.concatenate([f[3] for f in frags]); l1 = np.concatenate([f[4] for f in frags])
    order = np.lexsort((z, pix)); ps = pix[order]; first = np.ones(len(ps), bool); first[1:] = ps[1:] != ps[:-1]; w_ = order[first]
    ID.reshape(-1)[pix[w_]] = tri[w_]; ZB.reshape(-1)[pix[w_]] = z[w_]
    B2 = BW.reshape(-1, 3); B2[pix[w_], 0] = l0[w_]; B2[pix[w_], 1] = l1[w_]; B2[pix[w_], 2] = 1.0 - l0[w_] - l1[w_]
    return ID, ZB, BW


def render_opaque(R, V, T, C, L, d, fbox, W, pad=1.0, light=None, smooth=True):
    """z-buffered opaque render: the image and the camera (with the depth buffer). C: per-triangle colour (0..1), L: per-triangle face (the tint's
    face; the smooth normals are averaged within it and never across it). smooth=False: flat per-triangle shading."""
    d3, r3, u3 = R.basis(d); d3 = np.asarray(d3, float); r3 = np.asarray(r3, float); u3 = np.asarray(u3, float)
    foc = corners(fbox); fx = foc @ r3; fy = foc @ u3
    x0, x1 = fx.min() - pad, fx.max() + pad; y0, y1 = fy.min() - pad, fy.max() + pad
    mmpx = (x1 - x0) / W; H = int(np.ceil((y1 - y0) / mmpx))
    V = np.asarray(V, float); T = np.asarray(T, int)
    X = (V @ r3 - x0) / mmpx; Y = (y1 - V @ u3) / mmpx; Z = V @ d3
    ID, zbuf, BW = rasterize(X, Y, Z, T, W, H)
    valid = ID >= 0; ids = ID[valid]
    light = (-0.35 * d3 + 0.7 * u3 + 0.6 * r3) if light == "grazing" else (-d3 + 0.5 * u3 + 0.35 * r3); light = light / np.linalg.norm(light)
    P = V[T]; fn = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); fnu = fn / np.maximum(np.linalg.norm(fn, axis=1), 1e-12)[:, None]
    if smooth and len(T):
        N3 = vertex_normals(V, T, L)
        nn = (N3[ids] * BW[valid][:, :, None]).sum(1); nn /= np.maximum(np.linalg.norm(nn, axis=1), 1e-12)[:, None]
    else: nn = fnu[ids]
    sh = 0.35 + 0.65 * np.abs(nn @ light)
    img = np.tile(np.array(BG, float), (H, W, 1)); img[valid] = np.asarray(C, float)[ids] * sh[:, None]
    fo = np.full((H, W), -1); fo[valid] = np.asarray(L)[ids]
    edge = np.zeros((H, W), bool); edge[:, 1:] |= fo[:, 1:] != fo[:, :-1]; edge[1:, :] |= fo[1:, :] != fo[:-1, :]
    img[edge] = img[edge] * 0.45
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)), dict(d3=d3, r3=r3, u3=u3, x0=x0, y1=y1, mmpx=mmpx, zbuf=zbuf, fo=fo, H=H, W=W, id=ID)


def draw_occluded(dr, cam, P, col, width, tol=None, faces=(), show_hidden=True):
    """each segment of the polyline P: visible (on / in front of the surface) full, hidden faint and dotted (show_hidden=False: not drawn at all).
    Returns (visible, hidden). tol: cam['tol'] (the piece view: 2 x PIC_DEV + the piece's largest edge tolerance) else OCC_TOL.
    faces: the layout faces the line belongs to (a border's two, an added line's one) - where the surface in view IS one of them the line is
    ON it and drawn full whatever its depth (a decided line runs under the mesh's lumps; the mesh is sloppy, the line is not)."""
    P = np.asarray(P, float)
    x = (P @ cam["r3"] - cam["x0"]) / cam["mmpx"]; y = (cam["y1"] - P @ cam["u3"]) / cam["mmpx"]; z = P @ cam["d3"]
    zb = cam["zbuf"]; H, Wd = cam["H"], cam["W"]; tol = max(float(cam.get("tol", OCC_TOL)) if tol is None else float(tol), 2.0 * cam["mmpx"])
    xi = np.clip(np.round(x).astype(int), 0, Wd - 1); yi = np.clip(np.round(y).astype(int), 0, H - 1)
    zz = np.full(len(P), -np.inf); anyf = np.zeros(len(P), bool); own = np.zeros(len(P), bool)
    fo = cam.get("fo"); fset = set(int(f) for f in (faces or ()))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            yy = np.clip(yi + dy, 0, H - 1); xx = np.clip(xi + dx, 0, Wd - 1)
            zn = zb[yy, xx]; f_ = np.isfinite(zn)
            zz = np.where(f_, np.maximum(zz, zn), zz); anyf |= f_
            if fo is not None and fset:
                own |= np.isin(fo[yy, xx], list(fset))
    vis = ~anyf | (z <= zz + tol) | own
    dim = tuple(int(c * 0.40 + 35) for c in col); nv = nh = 0
    for k in range(len(P) - 1):
        a = (float(x[k]), float(y[k])); b = (float(x[k + 1]), float(y[k + 1]))
        if vis[k] and vis[k + 1]:
            dr.line([a, b], fill=col, width=width); nv += 1
        else:
            nh += 1
            if show_hidden and (k // 4) % 2 == 0: dr.line([a, b], fill=dim, width=1)
    return nv, nh



# MeshPart
PIC_DEV = float(os.environ.get("PIC_DEV", "0.02") or 0.02)
PIC_ANG = float(os.environ.get("PIC_ANG", "0.05") or 0.05)
PIC_DEV_MAX, PIC_ANG_MAX = 0.05, 0.10


def _gap_to_segments(M, A, B, skip):
    """the distance from each point M[i] to the nearest segment A[j]-B[j] with j not in skip[i] (a row of segment indices; -1 = none) (numpy, chunked)"""
    M = np.asarray(M, float); A = np.asarray(A, float); B = np.asarray(B, float); out = np.full(len(M), np.inf); skip = np.asarray(skip, int).reshape(len(M), -1)
    if len(M) == 0 or len(A) == 0: return out
    AB = B - A; L2 = np.maximum((AB * AB).sum(1), 1e-18); step = max(1, 2_000_000 // len(A))
    for s in range(0, len(M), step):
        Mi = M[s:s + step]; sk = skip[s:s + step]
        tt = np.clip(((Mi[:, None, :] - A[None, :, :]) * AB[None, :, :]).sum(2) / L2[None, :], 0.0, 1.0)
        D = np.linalg.norm(Mi[:, None, :] - (A[None, :, :] + tt[:, :, None] * AB[None, :, :]), axis=2)
        rows = np.repeat(np.arange(len(Mi)), sk.shape[1]); cols = sk.ravel(); ok = cols >= 0
        D[rows[ok], cols[ok]] = np.inf
        out[s:s + step] = D.min(1)
    return out


def mesh_quality(V, T, FID, closed, ang=None, tol=None, expected=None, judge_open=True, expected_planes=None):
    """the quality of a picture's mesh. The OPEN edges (one triangle holds them) are sorted: EXPECTED - within tol of `expected` (points on the
    B-rep edges that bound what was meshed: an open shell's rim, a face subset's border); SEAMS - closed by another open edge within tol (MeshPart's
    T-junctions and split vertices, 1e-4..1e-3 mm apart: geometrically closed, invisible); CRACKS - open by more than tol (a visible tear: the
    per-face tessellation's seams). tol = PIC_DEV (the precision the mesh promises). judge_open=False (a mesh file with an unknown rim): the open
    edges are counted, none is a crack. expected_planes [(point, normal)]: an open edge with BOTH ends on one of them is expected (a mesh cut on a
    plane: the body round the edit region). facet_p99 / facet_max = the angle between neighbouring triangles' normals INSIDE one face (information:
    a crease inside a face is real; the coarseness is judged against the SURFACE by mesh_vs_surface). DEFECTIVE when there are cracks."""
    V = np.asarray(V, float); T = np.asarray(T, int); FID = np.asarray(FID); ang = PIC_ANG if ang is None else float(ang); tol = PIC_DEV if tol is None else float(tol)
    q = {"tris": int(len(T)), "dev_mm": None, "ang_rad": round(ang, 4), "closed": bool(closed), "open_edges": 0, "expected_open": 0, "seams": 0, "cracks": 0, "gap_tol_mm": tol,
         "gap_max_mm": 0.0, "crack_pts": [], "facet_p99_deg": 0.0, "facet_max_deg": 0.0, "defective": False, "why": ""}
    if len(T) == 0: q.update({"defective": True, "why": "an empty mesh"}); return q
    E = np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), axis=1)
    Eu, inv, cnt = np.unique(E, axis=0, return_inverse=True, return_counts=True); inv = inv.reshape(-1)
    op_i = np.nonzero(cnt == 1)[0]; op = Eu[op_i]; q["open_edges"] = int(len(op)); q["sliver_open"] = 0
    tri_e = inv.reshape(3, len(T)).T
    n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]); A2 = np.linalg.norm(n, axis=1); n /= np.maximum(A2, 1e-12)[:, None]
    if len(op):
        A = V[op[:, 0]]; B = V[op[:, 1]]; M = 0.5 * (A + B); exp_ = np.zeros(len(op), bool)
        own_ = np.full(len(Eu), -1); own_[tri_e.ravel()] = np.repeat(np.arange(len(T)), 3)
        Lmax_ = np.maximum.reduce([np.linalg.norm(V[T[:, 1]] - V[T[:, 0]], axis=1), np.linalg.norm(V[T[:, 2]] - V[T[:, 1]], axis=1), np.linalg.norm(V[T[:, 0]] - V[T[:, 2]], axis=1)])
        sliv_ = (A2[own_[op_i]] / np.maximum(Lmax_[own_[op_i]], 1e-12)) <= tol
        q["sliver_open"] = int(sliv_.sum()); exp_ |= sliv_
        if expected is not None and len(expected):
            X_ = np.asarray(expected, float); step = max(1, 2_000_000 // len(X_))
            for s in range(0, len(M), step):
                exp_[s:s + step] = np.linalg.norm(M[s:s + step, None, :] - X_[None, :, :], axis=2).min(1) <= tol + 0.06
        for pl_ in (expected_planes or ()):
            p0_ = np.asarray(pl_[0], float); n0_ = np.asarray(pl_[1], float); n0_ = n0_ / max(np.linalg.norm(n0_), 1e-12)
            exp_ |= (np.abs((A - p0_) @ n0_) <= tol + 1e-6) & (np.abs((B - p0_) @ n0_) <= tol + 1e-6)
        q["expected_open"] = int(exp_.sum()); rest = np.nonzero(~exp_)[0]
        if len(rest) and judge_open:
            cand = np.nonzero(cnt != 2)[0]; pos = np.full(len(Eu), -1); pos[cand] = np.arange(len(cand))
            owner = np.full(len(Eu), -1); owner[tri_e.ravel()] = np.repeat(np.arange(len(T)), 3)
            skip = pos[tri_e[owner[op_i[rest]]]]
            gaps = _gap_to_segments(M[rest], V[Eu[cand, 0]], V[Eu[cand, 1]], skip)
            q["seams"] = int((gaps <= tol).sum()); q["cracks"] = int((gaps > tol).sum()); q["gap_max_mm"] = round(float(np.minimum(gaps, 99.0).max()), 4)
            q["crack_pts"] = [[round(float(v), 3) for v in m_] for m_ in M[rest][gaps > tol][:2000]]
            q["crack_faces"] = sorted(int(f_) for f_ in set(FID[owner[op_i[rest]][gaps > tol]].tolist()))
        elif len(rest): q["seams"] = int(len(rest))
    order = np.argsort(tri_e.ravel(), kind="stable"); eid = tri_e.ravel()[order]; tid = np.repeat(np.arange(len(T)), 3)[order]
    same = eid[1:] == eid[:-1]; a_ = tid[:-1][same]; b_ = tid[1:][same]
    m_ = (FID[a_] == FID[b_]) & (A2[a_] > 2e-6) & (A2[b_] > 2e-6)
    if m_.any():
        dots = np.abs((n[a_[m_]] * n[b_[m_]]).sum(1)); angs = np.degrees(np.arccos(np.clip(dots, -1, 1)))
        q["facet_p99_deg"] = round(float(np.percentile(angs, 99)), 2); q["facet_max_deg"] = round(float(angs.max()), 2)
    why = []
    if q["cracks"]: why.append("%d crack edge(s) between faces open by more than %g mm (a torn seam; the widest %.3f mm)" % (q["cracks"], tol, q["gap_max_mm"]))
    q["defective"] = bool(why); q["why"] = "; ".join(why)
    return q



def mesh_vs_surface(shape, V, T, FID, faces=None, n=3000, seed=11):
    """31bn - ACCURATE TO THE GEOMETRY (the client): n triangles drawn by area; each centroid against its face's own SURFACE - the distance (the realized
    linear deflection) and the angle between the triangle's normal and the surface's there (the realized angular deflection); p99 of both.
    Returns {dev_p99_mm, dev_max_mm, nang_p99_deg, nang_max_deg, sampled}."""
    V = np.asarray(V, float); T = np.asarray(T, int); FID = np.asarray(FID, int)
    none = {"dev_p99_mm": None, "dev_max_mm": None, "nang_p99_deg": None, "nang_max_deg": None, "sampled": 0}
    if len(T) == 0: return none
    P = V[T]; nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); A2 = np.linalg.norm(nrm, axis=1); ok = A2 > 2e-6
    if not ok.any(): return none
    rs = np.random.RandomState(seed); w = np.where(ok, A2, 0.0); w = w / w.sum(); idx = rs.choice(len(T), size=min(n, int(ok.sum())), replace=False, p=w)
    C = P[idx].mean(1); N = nrm[idx] / A2[idx][:, None]; fl = shape.Faces if faces is None else [shape.Faces[int(i)] for i in faces]
    devs = []; angs = []; wts = []
    import FreeCAD as _F
    for c_, n_, f_, i_ in zip(C, N, FID[idx], idx):
        try:
            S = fl[int(f_)].Surface; u_, v_ = S.parameter(_F.Vector(*c_)); q_ = S.value(u_, v_); ns = S.normal(u_, v_)
            devs.append(q_.distanceToPoint(_F.Vector(*c_))); angs.append(np.degrees(np.arccos(min(1.0, abs(ns.x * n_[0] + ns.y * n_[1] + ns.z * n_[2]))))); wts.append(float(A2[i_]))
        except Exception: continue
    if not devs: return none
    devs = np.array(devs); angs = np.array(angs); wts = np.array(wts)
    def _wp(v_, w_, pct):
        o_ = np.argsort(v_); cw = np.cumsum(w_[o_]); return float(v_[o_][min(int(np.searchsorted(cw, pct / 100.0 * cw[-1])), len(o_) - 1)])
    return {"dev_p99_mm": round(_wp(devs, wts, 99), 4), "dev_max_mm": round(float(devs.max()), 4), "nang_p99_deg": round(_wp(angs, wts, 99), 2),
            "nang_max_deg": round(float(angs.max()), 2), "sampled": int(len(devs)), "by": "area-weighted percentiles"}


def _rule_version():
    """the mesh cache is keyed by the RULES' own source - a changed rule never reads an old verdict back (fix 4: a hand-bumped 'q4' did)"""
    import hashlib as _h, inspect as _i
    try: src = "".join(_i.getsource(f_) for f_ in (mesh_quality, mesh_vs_surface, _gap_to_segments, piece_mesh))
    except Exception: src = "nosrc"
    return _h.md5(src.encode("utf-8", "replace")).hexdigest()[:8]


def _expected_boundary(shape, faces, step=0.1, skip=()):
    """points on the B-rep edges that bound what is meshed - the edges held by fewer than two of the meshed faces (an open shell's rim, the border
    of a face subset; fix 5d: a DEGENERATE face - no area, or one the mesher gave no triangle - does not count as meshed: the model of record carries a
    0.00 mm2 planar face whose wire runs out and back along the same edges, and its neighbour's mesh edge there has no partner to meet); an open mesh
    edge there is expected, not a crack"""
    fl = shape.Faces if faces is None else [shape.Faces[int(i)] for i in faces]
    cnt = {}; keep = {}; skip = set(int(s_) for s_ in skip)
    for i_, f_ in enumerate(fl):
        try: dead = i_ in skip or f_.Area < 1e-4
        except Exception: dead = i_ in skip
        for e_ in f_.Edges:
            h_ = e_.hashCode(); cnt[h_] = cnt.get(h_, 0) + (0 if dead else 1); keep[h_] = e_
    pts = []
    for h_, e_ in keep.items():
        if cnt[h_] >= 2 or e_.Length < 1e-6: continue
        try: pts.extend([[p_.x, p_.y, p_.z] for p_ in e_.discretize(Number=max(2, int(e_.Length / step) + 1))])
        except Exception: continue
    return np.array(pts, float).reshape(-1, 3)


def piece_mesh(path, shape=None, faces=None, dev=None, ang=None, cache_dir=None, say=None):
    """THE ONE MESH of a B-rep for pictures: MeshPart on the whole shape (Segments = the face of every triangle), conforming across faces, cached
    beside the pictures by the file's md5, the deflections and the rules' version. faces = a subset (indices): the mesh of a compound of those
    faces, FID in that list's index space (an invalid face left out cannot crash the mesher in-process); None = every face, FID = shape.Faces
    indices. Returns V, T, FID, quality ('cached' True when read back). The per-face tessellation is the fallback when MeshPart refuses - its
    cracks then make the frames DEFECTIVE, which is the truth about them."""
    import hashlib as _h
    dev = PIC_DEV if dev is None else float(dev); ang = PIC_ANG if ang is None else float(ang)
    isf = bool(path and os.path.isfile(path))
    key = _h.md5(("%s|%s|%s|%s|%s" % (md5(path) if isf else "nofile", dev, ang, ",".join(str(int(f)) for f in faces) if faces is not None else "all", _rule_version())).encode()).hexdigest()[:16]
    cdir = cache_dir or OUT; cp = os.path.join(cdir, ".mesh_%s.npz" % key)
    if isf and os.path.isfile(cp):
        try:
            z = np.load(cp, allow_pickle=True); q = json.loads(str(z["quality"])); q["cached"] = True
            return z["V"], z["T"], z["FID"], q
        except Exception: pass
    import Part
    if shape is None: shape = Part.Shape(); shape.importBrep(path)
    if faces is not None: sub = Part.makeCompound([shape.Faces[int(i)] for i in faces]); nf = len(faces)
    else: sub = shape; nf = len(shape.Faces)
    closed = bool(faces is None and shape.Solids and all(s_.isClosed() for s_ in shape.Shells))
    V = T = FID = None; how = "MeshPart whole shape"; unassigned = 0
    try:
        import MeshPart
        m = MeshPart.meshFromShape(Shape=sub, LinearDeflection=dev, AngularDeflection=ang, Relative=False, Segments=True)
        V = np.array([[p_.x, p_.y, p_.z] for p_ in m.Points], float); T = np.array([[f_.PointIndices[0], f_.PointIndices[1], f_.PointIndices[2]] for f_ in m.Facets], int).reshape(-1, 3)
        FID = np.full(len(T), -1, np.int64)
        for i_ in range(m.countSegments()): FID[np.asarray(m.getSegment(i_), int)] = i_
        unassigned = int((FID < 0).sum())
        if m.countSegments() != nf or unassigned: how += " (%d segments for %d faces; %d triangles unassigned)" % (m.countSegments(), nf, unassigned)
    except Exception as ex:
        V = T = FID = None; how = "per-face tessellation (MeshPart refused: %s)" % str(ex)[:60]
    if V is None:
        import kitlib_render as R_
        V_, T_, F_ = R_.tess_shape(sub, dev, ang=ang); V = np.asarray(V_, float); T = np.asarray(T_, int); FID = np.asarray(F_, np.int64)
    # MeshPart
    # open edges
    phantom = []
    try:
        fl_ = shape.Faces if faces is None else [shape.Faces[int(i)] for i in faces]
        P_ = V[T]; At = 0.5 * np.linalg.norm(np.cross(P_[:, 1] - P_[:, 0], P_[:, 2] - P_[:, 0]), axis=1); Asum = np.bincount(np.maximum(FID, 0), weights=At, minlength=nf)
        for i_, f_ in enumerate(fl_):
            try: af = float(f_.Area)
            except Exception: continue
            if Asum[i_] > 3.0 * af + 0.5: phantom.append(i_)
        if phantom:
            keep = ~np.isin(FID, phantom); T = T[keep]; FID = FID[keep]
            how += " (%d phantom face(s) dropped: the mesher drew area where the B-rep has none)" % len(phantom)
    except Exception as _exp: how += " (the phantom check failed: %s)" % str(_exp)[:40]
    try:      # open edges
        _nm = np.bincount(np.maximum(FID, 0), minlength=nf) if len(FID) else np.zeros(nf, int)
        expected = _expected_boundary(shape, faces, skip=list(np.nonzero(_nm == 0)[0]) + phantom)
    except Exception: expected = None
    q = mesh_quality(V, T, np.maximum(FID, 0), closed, ang, tol=dev, expected=expected)
    if q.get("cracks") and q.get("crack_faces") and V is not None:
        try:
            import kitlib_render as R_
            fl_ = shape.Faces if faces is None else [shape.Faces[int(i)] for i in faces]
            keep = np.ones(len(T), bool); Vn = [V]; Tn = []; Fn = []; off = len(V); done_ = []
            for fi_ in q["crack_faces"]:
                if fi_ < 0 or fi_ >= len(fl_): continue
                V2, T2, _ = R_.tess_shape(fl_[fi_], dev, ang=ang); V2 = np.asarray(V2, float); T2 = np.asarray(T2, int).reshape(-1, 3)
                if len(T2) == 0: continue
                keep &= FID != fi_; Vn.append(V2); Tn.append(T2 + off); Fn.append(np.full(len(T2), fi_, np.int64)); off += len(V2); done_.append(fi_)
            if done_:
                V = np.vstack(Vn); T = np.vstack([T[keep]] + Tn); FID = np.concatenate([FID[keep]] + Fn)
                q2 = mesh_quality(V, T, np.maximum(FID, 0), closed, ang, tol=dev, expected=expected)
                how += " (%d face(s) re-meshed one by one where the mesher left %d gap(s): %d left)" % (len(done_), q["cracks"], q2["cracks"]); q = q2
        except Exception as _exr: how += " (the re-mesh of the gapped faces failed: %s)" % str(_exr)[:50]
    # recorded
    unmeshed = []; ubox = []
    try:
        fl_ = shape.Faces if faces is None else [shape.Faces[int(i)] for i in faces]
        _cnt = np.bincount(np.maximum(np.asarray(FID, np.int64), 0), minlength=nf) if len(FID) else np.zeros(nf, int)
        for i_, f_ in enumerate(fl_):
            if i_ < len(_cnt) and _cnt[i_] > 0: continue
            try: af_ = abs(float(f_.Area))
            except Exception: af_ = float("inf")
            if not af_ >= 1e-4: continue
            es_ = list(f_.Edges); bb_ = es_[0].BoundBox if es_ else f_.BoundBox
            for e_ in es_[1:]: bb_.add(e_.BoundBox)
            unmeshed.append(int(faces[i_]) if faces is not None else int(i_)); ubox.append([round(float(v_), 3) for v_ in (bb_.XMin, bb_.XMax, bb_.YMin, bb_.YMax, bb_.ZMin, bb_.ZMax)])
    except Exception as _exu: how += " (the unmeshed-face check failed: %s)" % str(_exu)[:50]
    q.update({"dev_mm": dev, "how": how, "cached": False})
    crack_why = q["why"]; why = []
    if unassigned: why.append("%d triangle(s) belong to no face (the mesher's segments do not match the faces)" % unassigned)
    if dev > PIC_DEV_MAX or ang > PIC_ANG_MAX: why.append("the mesh is coarser than a piece picture may be (%g mm / %g rad asked; at most %g mm / %g rad)" % (dev, ang, PIC_DEV_MAX, PIC_ANG_MAX))
    try:
        q.update(mesh_vs_surface(shape, V, T, np.maximum(FID, 0), faces))
        try: q["edge_tol_max"] = round(float(max([e_.Tolerance for e_ in shape.Edges] + [0.0])), 4)
        except Exception: q["edge_tol_max"] = 0.0
        dev_lim = max(2.0 * dev, q["edge_tol_max"])
        if q.get("dev_p99_mm") is not None and q["dev_p99_mm"] > dev_lim: why.append("the mesh stands %.3f mm off its surfaces (p99) against %.3f allowed (twice the %g asked, or the piece's own largest edge tolerance %.3f)" % (q["dev_p99_mm"], dev_lim, dev, q["edge_tol_max"]))
        if q.get("nang_p99_deg") is not None and q["nang_p99_deg"] > 2.0 * np.degrees(ang): why.append("the facets lean %.1f deg off the surface normal (p99) against the %.1f asked - too coarse" % (q["nang_p99_deg"], np.degrees(ang)))
    except Exception as _exq: q["surface_check"] = "failed: %s" % str(_exq)[:60]
    q["defective_mesh"] = bool(why); q["why_mesh"] = "; ".join(why)
    q["defective"] = bool(why) or bool(q["cracks"]); q["why"] = "; ".join(why + ([crack_why] if crack_why else []))
    q["unmeshed_faces"] = unmeshed; q["unmeshed_boxes"] = ubox
    if unmeshed: q["defective"] = True; q["why"] = "; ".join(x_ for x_ in (q["why"], "face(s) %s of the piece have NO triangles in the mesh (the mesher gave them none) - each a HOLE in every frame that frames it" % unmeshed) if x_)
    if isf:
        try:
            os.makedirs(cdir, exist_ok=True); np.savez_compressed(cp, V=V, T=T, FID=FID, quality=json.dumps(q))
            old = sorted((os.path.getmtime(f_), f_) for f_ in glob.glob(os.path.join(cdir, ".mesh_*.npz")) if os.path.abspath(f_) != os.path.abspath(cp))
            for _, f_ in old[:-2]: os.remove(f_)
        except Exception: pass
    if say: say("piece mesh: %d triangles (%s, %g mm / %g rad); against the surfaces: %s mm off (p99), facets %s deg off the normal (p99); open edges %d (%d expected at the rim, %d seams closed within %g mm, %d cracks)%s"
                % (len(T), how, dev, ang, q.get("dev_p99_mm"), q.get("nang_p99_deg"), q["open_edges"], q["expected_open"], q["seams"], dev, q["cracks"], (" - RENDER DEFECTIVE: " + q["why"]) if q["defective"] else ""))
    return V, T, FID, q



def quality_line(q):
    """the one sentence under every piece picture: the record's own numbers (the reviewers compared the frame with PIECE_LOOK and found two)"""
    if not isinstance(q, dict): return "mesh: not measured"
    surf = ("against its surfaces %.3f mm off, facets %.2f deg off the normal (p99)" % (q["dev_p99_mm"], q["nang_p99_deg"])) if q.get("dev_p99_mm") is not None else "surfaces not measured (a mesh file)"
    op = q.get("open_edges", 0) or 0; cr = q.get("cracks", 0) or 0
    cif = q.get("cracks_in_frame")
    crs = ("%d cracks (%s)" % (cr, ("%d in this frame" % cif) if cif else "none in this frame")) if (cr and cif is not None) else ("%d cracks" % cr)
    oe = ("open edges %d: %d at the rim, %d seams closed within %g mm, %s" % (op, q.get("expected_open", 0) or 0, q.get("seams", 0) or 0, q.get("gap_tol_mm", 0) or 0, crs)) if (op or cr) else "open edges 0"
    return "mesh: %d triangles at %g mm / %g rad; %s; %s" % (q.get("tris", 0) or 0, q.get("dev_mm") or 0, q.get("ang_rad") or 0, surf, oe)


def scale_bar_mm(mmpx, W):
    """the scale bar's length: 10 mm, or 5 / 2 / 1 when 10 mm would run off the frame (a close-up at 0.009 mm/px: 1111 px of a 900 px frame)"""
    for L in (10.0, 5.0, 2.0, 1.0):
        if L / max(float(mmpx), 1e-9) <= 0.4 * float(W): return L
    return 1.0


def frame_quality(q, fbox, pad=1.0):
    """the FRAME's verdict from the mesh's: the mesh's own defects (deviation, lean, coarseness, unassigned triangles) stamp every frame; a crack
    stamps the frames whose box holds it (grown pad mm) - the rest say how many lie elsewhere"""
    if not isinstance(q, dict): return q
    fq = dict(q); pts = np.asarray(q.get("crack_pts") or [], float).reshape(-1, 3)
    lo = np.array([fbox[0], fbox[2], fbox[4]], float) - pad; hi = np.array([fbox[1], fbox[3], fbox[5]], float) + pad
    inf_ = int(np.all((pts >= lo) & (pts <= hi), axis=1).sum()) if len(pts) else 0
    fq["cracks_in_frame"] = inf_; fq["crack_pts_in_frame"] = pts[np.all((pts >= lo) & (pts <= hi), axis=1)].tolist() if len(pts) else []; fq.pop("crack_pts", None)
    why = [w_ for w_ in [q.get("why_mesh", "")] if w_]
    if inf_: why.append("%d crack edge(s) open by more than %g mm in this frame, ringed red (a torn seam; the widest in the mesh %.3f mm)" % (inf_, q.get("gap_tol_mm", 0) or 0, q.get("gap_max_mm", 0) or 0))
    hit_ = [f_ for f_, b_ in zip(q.get("unmeshed_faces") or [], q.get("unmeshed_boxes") or []) if all(b_[2 * k_] <= hi[k_] and b_[2 * k_ + 1] >= lo[k_] for k_ in range(3))]
    fq["unmeshed_in_frame"] = hit_
    if hit_: why.append("face(s) %s of the piece have NO triangles in the mesh - each a HOLE in this frame (the mesher gave them none)" % hit_)
    fq["defective"] = bool(why); fq["why"] = "; ".join(why)
    return fq


def view_piece(R, out_path, V, T, FID, C, d, fbox, W, title, head, lines, polylines=(), legend=(), key=None, quality=None, light=None, draw=None, stats=None, subject_box=None, cap_tris=None):
    """THE PIECE VIEW: the mesh opaque with a true z-buffer, smooth-shaded from the surface normals within each face (creases stay), each triangle
    its colour C (per face tint, grey for the rest), the polylines [(P, colour, width, faces[, show_hidden])] depth-tested (full where seen, faint
    dotted behind the part - or not drawn), the box framed; every caption line WRAPPED to the frame; the mesh's quality STAMPED on the frame and
    in its record (frames.jsonl). quality is REQUIRED (a frame with no mesh verdict is no piece view). Returns 'HIT' when the cache has it."""
    if key and pic_hit(out_path, key): return "HIT"
    if not isinstance(quality, dict): raise ValueError("view_piece: quality is required - every piece picture carries its mesh's verdict (piece_mesh / mesh_quality)")
    quality = frame_quality(quality, fbox)
    try: W = int(min(int(W), R.PIC_W)) if int(getattr(R, "PIC_W", 0) or 0) > 0 else int(W)
    except Exception: pass
    C = np.asarray(C, float)
    if C.ndim == 1: C = np.tile(C, (len(T), 1))
    im, cam = render_opaque(R, V, T, C, FID, d, fbox, W, light=light)
    cam["tol"] = max(2.0 * PIC_DEV + float(quality.get("edge_tol_max") or 0.0), 2.0 * cam["mmpx"])
    if isinstance(stats, dict):
        _id = cam.get("id"); stats["mmpx"] = float(cam["mmpx"]); stats["drawn_px"] = int((_id >= 0).sum()) if _id is not None else 0; stats["own"] = _id
        if subject_box is not None and _id is not None and len(T):
            (sx0, sx1), (sy0, sy1), (sz0, sz1) = subject_box
            _zb = cam["zbuf"]
            _capm = None      # over the
            try:
                if cap_tris is not None and len(cap_tris) == len(T): _capm = (_id >= 0) & np.asarray(cap_tris, bool)[np.maximum(_id, 0)]
            except Exception: _capm = None
            _jj, _ii = np.nonzero(np.isfinite(_zb) & (_id >= 0) & (~_capm if _capm is not None else True))
            _Pw = ((cam["x0"] + (_ii + 0.5) * cam["mmpx"])[:, None] * cam["r3"][None, :] + (cam["y1"] - (_jj + 0.5) * cam["mmpx"])[:, None] * cam["u3"][None, :] + _zb[_jj, _ii][:, None] * cam["d3"][None, :])
            _tl = 0.05
            stats["subject_px"] = int(((_Pw[:, 0] >= sx0 - _tl) & (_Pw[:, 0] <= sx1 + _tl) & (_Pw[:, 1] >= sy0 - _tl) & (_Pw[:, 1] <= sy1 + _tl) & (_Pw[:, 2] >= sz0 - _tl) & (_Pw[:, 2] <= sz1 + _tl)).sum())
            _cb = np.array([[cx_, cy_, cz_] for cx_ in (sx0, sx1) for cy_ in (sy0, sy1) for cz_ in (sz0, sz1)], float)
            stats["box_px"], stats["box_drawn_px"], stats["occluded_px"] = R.box_cover(_zb, (sx0, sx1, sy0, sy1, sz0, sz1), cam["d3"], cam["r3"], cam["u3"], cam["x0"], cam["y1"], cam["mmpx"], cam["W"], cam["H"], cap_mask=_capm)
    dr = ImageDraw.Draw(im)
    for pl in polylines:
        P_, col, wd = pl[0], pl[1], pl[2]; fc_ = pl[3] if len(pl) > 3 else (); shh = bool(pl[4]) if len(pl) > 4 else True
        if len(P_) >= 2: draw_occluded(dr, cam, P_, col, wd, faces=fc_, show_hidden=shh)
    proj = lambda P: [tuple(v) for v in np.stack([(np.asarray(P) @ cam["r3"] - cam["x0"]) / cam["mmpx"], (cam["y1"] - np.asarray(P) @ cam["u3"]) / cam["mmpx"]], axis=1)]
    if draw: draw(dr, proj)
    mmpx, r3, u3 = cam["mmpx"], cam["r3"], cam["u3"]
    for c_ in quality.get("crack_pts_in_frame") or []:
        (xx_, yy_), = proj([c_]); dr.ellipse([xx_ - 9, yy_ - 9, xx_ + 9, yy_ + 9], outline=(255, 40, 40), width=3)
    _title_bars(dr, im, title, R.axes_label(r3, u3))
    Lb = scale_bar_mm(mmpx, im.width); bar = Lb / mmpx; dr.line([10, im.height - 12, 10 + bar, im.height - 12], fill=(255, 255, 255), width=3)
    dr.text((12, im.height - 30), "%g mm  (%.3f mm/px)" % (Lb, mmpx), fill=(255, 255, 255))
    q = quality; od0 = ImageDraw.Draw(Image.new("RGB", (8, 8))); wmax = im.width - 20
    heads = _wrap(od0, head, F22, wmax); qlines = _wrap(od0, quality_line(q), F16, wmax)
    stamps = _wrap(od0, "RENDER DEFECTIVE - NO EVIDENCE: %s" % q.get("why", ""), F16, wmax) if q.get("defective") else []
    body = [l_ for ln in lines for l_ in _wrap(od0, ln, F16, wmax)]
    leg_rows = 0
    if legend:
        x = 10; leg_rows = 1
        for colr, t_ in legend:
            tw = od0.textbbox((0, 0), t_, font=F16)[2]
            if x + 30 + tw > im.width - 10 and x > 10: leg_rows += 1; x = 10
            x += 44 + tw
    out = Image.new("RGB", (im.width, 12 + 28 * len(heads) + (6 + 22 * len(stamps) + 4 if stamps else 0) + im.height + 6 + 26 * leg_rows + 22 * (len(body) + len(qlines)) + 12), (16, 16, 20))
    od = ImageDraw.Draw(out); y = 8
    for h_ in heads: od.text((10, y), h_, fill=(255, 235, 120), font=F22); y += 28
    y += 4
    if stamps:
        od.rectangle([0, y, out.width, y + 6 + 22 * len(stamps)], fill=(150, 20, 20))
        for s_ in stamps: od.text((10, y + 3), s_, fill=(255, 255, 255), font=F16); y += 22
        y += 10
    out.paste(im, (0, y)); y += im.height + 6; x = 10
    for colr, t_ in legend:
        tw = od.textbbox((0, 0), t_, font=F16)[2]
        if x + 30 + tw > out.width - 10 and x > 10: y += 26; x = 10
        od.rectangle([x, y + 3, x + 22, y + 19], fill=colr); od.text((x + 30, y + 2), t_, fill=(235, 235, 235), font=F16); x += 44 + tw
    if legend: y += 26
    for ln in body: od.text((10, y), ln, fill=(235, 235, 235), font=F16); y += 22
    for ln in qlines: od.text((10, y), ln, fill=(150, 150, 160), font=F16); y += 22
    out.save(out_path)
    if hasattr(R, "index_frame"): R.index_frame(out_path, fbox, d, head, quality=q)
    if key: pic_mark(out_path, key)
    return "MISS"



def merge_quality(qs):
    """one verdict for a frame drawn from several meshes: the sums (triangles, open edges, seams, cracks), the worst deviations, every crack's place,
    DEFECTIVE when any part is; the deflections the first part's"""
    qs = [q for q in qs if isinstance(q, dict)]
    if not qs: return None
    def mx(k):
        v = [q.get(k) for q in qs if q.get(k) is not None]; return max(v) if v else None
    def sm(k): return int(sum(int(q.get(k) or 0) for q in qs))
    why_m = "; ".join(w for w in (q.get("why_mesh", "") for q in qs) if w); why = "; ".join(w for w in (q.get("why", "") for q in qs) if w)
    return {"tris": sm("tris"), "dev_mm": qs[0].get("dev_mm"), "ang_rad": qs[0].get("ang_rad"), "gap_tol_mm": qs[0].get("gap_tol_mm"), "parts": len(qs),
            "how": " + ".join(str(q.get("how", "?")) for q in qs), "closed": all(bool(q.get("closed")) for q in qs),
            "open_edges": sm("open_edges"), "expected_open": sm("expected_open"), "seams": sm("seams"), "cracks": sm("cracks"), "gap_max_mm": mx("gap_max_mm") or 0.0,
            "crack_pts": [p_ for q in qs for p_ in (q.get("crack_pts") or [])], "dev_p99_mm": mx("dev_p99_mm"), "dev_max_mm": mx("dev_max_mm"), "nang_p99_deg": mx("nang_p99_deg"),
            "nang_max_deg": mx("nang_max_deg"), "edge_tol_max": mx("edge_tol_max") or 0.0, "facet_p99_deg": mx("facet_p99_deg") or 0.0, "facet_max_deg": mx("facet_max_deg") or 0.0,
            "defective_mesh": any(bool(q.get("defective_mesh")) for q in qs), "why_mesh": why_m, "defective": any(bool(q.get("defective")) for q in qs), "why": why,
            "cached": all(bool(q.get("cached")) for q in qs),
            "unmeshed_faces": [f_ for q in qs for f_ in (q.get("unmeshed_faces") or [])], "unmeshed_boxes": [b_ for q in qs for b_ in (q.get("unmeshed_boxes") or [])]}


def view_meshes(R, out_path, meshes, d, fbox, W, title, head, lines, polylines=(), legend=(), key=None, light=None, clip=None, draw=None, stats=None, subject_box=None):
    """THE PIECE VIEW of several meshes at once (the real model: the body round the region, the content, the seam faces; a trial body).
    meshes: [(V, T, FID, quality, C[, bias])] - each from piece_mesh (its quality the part's verdict), C one rgb (3,) or one per triangle (len(T), 3);
    bias: mm the part is moved TOWARD the camera (fix 5e: an overlay whose skin coincides with another part's - the seam faces on the body they lie on,
    the content against the body round it - wins the depth fight; along the view direction nothing moves on the screen); clip: (point, normal) - a real
    capped cut (kit review's cut-away). The parts' faces are kept apart (the tints' borders, the smooth normals), their qualities merged, one
    view_piece call. Returns 'HIT' / 'MISS'."""
    if key and pic_hit(out_path, key): return "HIT"
    Vs, Ts, Fs, Cs, qs = [], [], [], [], []; nv = 0; nf = 0; caps_ = []
    d3_ = np.asarray(R.basis(d)[0], float); d3_ = d3_ / max(np.linalg.norm(d3_), 1e-12)
    for part in meshes:
        V_, T_, F_, q_, C_ = part[:5]; bias = float(part[5]) if len(part) > 5 else 0.0
        V_ = np.asarray(V_, float); T_ = np.asarray(T_, int).reshape(-1, 3); F_ = np.maximum(np.asarray(F_, int).reshape(-1), 0)
        if bias: V_ = V_ - bias * d3_[None, :]
        C_ = np.asarray(C_, float); C_ = np.tile(C_, (len(T_), 1)) if C_.ndim == 1 else C_
        if clip is not None and len(T_):
            p_, n_ = np.asarray(clip[0], float), np.asarray(clip[1], float)
            Vc, Tc, Cc, lp = R.cut_mesh(V_, T_, C_, p_, n_)
            _, _, Fc, _ = R.cut_mesh(V_, T_, np.repeat(F_[:, None], 3, 1).astype(float), p_, n_)
            capc = np.asarray(getattr(R, "CAP_COLOUR", (0.0, 0.0, 0.0)), float); nfp = (int(F_.max()) + 1) if len(F_) else 0
            is_cap = np.all(np.abs(np.asarray(Fc, float) - capc[None, :]) < 1e-9, axis=1) if len(Fc) else np.zeros(0, bool)
            F_ = np.where(is_cap, nfp, np.round(np.asarray(Fc, float)[:, 0]).astype(int)) if len(Fc) else np.zeros(0, int)
            V_, T_, C_ = np.asarray(Vc, float), np.asarray(Tc, int).reshape(-1, 3), np.asarray(Cc, float)
            if isinstance(stats, dict): stats["cut"] = {"closed": int(lp[0]) + int((stats.get("cut") or {}).get("closed", 0)), "open": int(lp[1]) + int((stats.get("cut") or {}).get("open", 0))}
            caps_.append(np.asarray(is_cap, bool) if len(Fc) else np.zeros(len(T_), bool))
        else:
            caps_.append(np.zeros(len(T_), bool))
        Vs.append(V_); Ts.append(T_ + nv); Fs.append(F_ + nf); Cs.append(C_); qs.append(q_)
        nv += len(V_); nf += (int(F_.max()) + 1) if len(F_) else 0
    V = np.vstack(Vs) if Vs else np.zeros((0, 3)); T = np.vstack(Ts) if Ts else np.zeros((0, 3), int); FID = np.concatenate(Fs) if Fs else np.zeros(0, int)
    C = np.vstack(Cs) if Cs else np.zeros((0, 3)); q = merge_quality(qs) or {"tris": 0, "defective": True, "why": "no mesh", "why_mesh": "no mesh", "defective_mesh": True}
    return view_piece(R, out_path, V, T, FID, C, d, fbox, W, title, head, lines, polylines=polylines, legend=legend, key=key, quality=q, light=light, draw=draw, stats=stats, subject_box=subject_box, cap_tris=(np.concatenate(caps_) if caps_ else None))


def mesh_outside_region(R, V, T, FID, halfspaces):
    """the part of a mesh OUTSIDE a convex region (the intersection of half-spaces [(point, normal)]: inside = (v - point) . normal <= 0 for every one),
    cut EXACTLY on the planes (R.cut_mesh splits the straddling triangles; the face ids ride through as a colour): for each plane the pieces beyond it
    go to the outside, what is left goes on to the next plane; what survives every plane is the inside and is dropped. Returns V, T, FID.
    (fix 5f: a whole-triangle trim left a ragged rim and see-through gaps between the body round the edit region and the content.)"""
    V = np.asarray(V, float); T = np.asarray(T, int).reshape(-1, 3); FID = np.asarray(FID, int).reshape(-1)
    Vo, To, Fo = [], [], []; nv = 0
    for p0, n in halfspaces:
        if len(T) == 0: break
        p0 = np.asarray(p0, float); n = np.asarray(n, float); n = n / max(np.linalg.norm(n), 1e-12)
        Cf = np.repeat(FID[:, None], 3, 1).astype(float)
        Vb, Tb, Fb, _ = R.cut_mesh(V, T, Cf, p0, -n, cap=False)[:4]
        if len(Tb): Vo.append(np.asarray(Vb, float)); To.append(np.asarray(Tb, int).reshape(-1, 3) + nv); Fo.append(np.round(np.asarray(Fb, float)[:, 0]).astype(int)); nv += len(Vb)
        Vi, Ti, Fi, _ = R.cut_mesh(V, T, Cf, p0, n, cap=False)[:4]
        V = np.asarray(Vi, float); T = np.asarray(Ti, int).reshape(-1, 3); FID = np.round(np.asarray(Fi, float)[:, 0]).astype(int) if len(Ti) else np.zeros(0, int)
    if not To: return np.zeros((0, 3)), np.zeros((0, 3), int), np.zeros(0, int)
    V = np.vstack(Vo); T = np.vstack(To); FID = np.concatenate(Fo)
    # collapsed
    _, first, inv = np.unique(np.round(V, 7), axis=0, return_index=True, return_inverse=True)
    V = V[np.sort(first)]; remap = np.empty(len(first), int); remap[np.argsort(first)] = np.arange(len(first)); T = remap[inv.reshape(-1)[T]]
    ok_ = (T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 2] != T[:, 0])
    return V, T[ok_], FID[ok_]

def cut_quality(q_src, V_src, T_src, V_cut, T_cut, FID_cut, planes, tol=None):
    """the quality of a mesh DRAWN as a cut of a judged source mesh (mesh_outside_region: the body round the edit region). The source's verdict stands
    for its surfaces (deviation, lean, its own cracks); the cut's OWN open edges are judged: EXPECTED on a cut plane (both ends within tol of it) or on
    the source's own open rim, the rest by the gap rule - so a ragged trim (whole triangles dropped) is a CRACK of the drawn mesh and stamps the frames;
    an exact cut leaves none. (fix 5g: the region cuts' quality line read clean on b20t7's torn rim because it measured the uncut meshes.)"""
    tol = PIC_DEV if tol is None else float(tol)
    V_src = np.asarray(V_src, float); T_src = np.asarray(T_src, int).reshape(-1, 3)
    E = np.sort(np.concatenate([T_src[:, [0, 1]], T_src[:, [1, 2]], T_src[:, [2, 0]]]), axis=1)
    Eu, cnt = np.unique(E, axis=0, return_counts=True); op = Eu[cnt == 1]
    pts = []
    for a_, b_ in (zip(V_src[op[:, 0]], V_src[op[:, 1]]) if len(op) else ()):
        k_ = max(2, int(np.ceil(np.linalg.norm(b_ - a_) / 0.1)) + 1); pts.append(a_[None, :] + (b_ - a_)[None, :] * np.linspace(0.0, 1.0, k_)[:, None])
    X_ = np.vstack(pts) if pts else None
    qc = mesh_quality(V_cut, T_cut, FID_cut, False, ang=q_src.get("ang_rad"), tol=tol, expected=X_, expected_planes=list(planes))
    q = dict(q_src); q["how"] = "%s, cut on the walls" % q_src.get("how", "?"); q["closed"] = False; q["tris"] = int(len(np.asarray(T_cut).reshape(-1, 3)))
    q["open_edges"] = qc["open_edges"]; q["expected_open"] = qc["expected_open"]; q["seams"] = int(q_src.get("seams") or 0) + int(qc["seams"])
    q["cracks"] = int(q_src.get("cracks") or 0) + int(qc["cracks"]); q["gap_max_mm"] = max(float(q_src.get("gap_max_mm") or 0.0), float(qc["gap_max_mm"]))
    q["crack_pts"] = list(q_src.get("crack_pts") or []) + list(qc["crack_pts"]); q["cut_cracks"] = int(qc["cracks"])
    if qc["cracks"]:
        w_ = "%d open edge(s) of the DRAWN cut lie neither on a wall plane nor on the source's rim - a ragged trim (the widest gap %.3f mm)" % (qc["cracks"], qc["gap_max_mm"])
        q["why"] = "; ".join(x for x in (q_src.get("why", ""), w_) if x); q["defective"] = True
    return q


def fbox_of(P, pad=0.0):
    """the framed box of a point set (the old renderer framed on `focus` points; the piece view frames on a box)"""
    P = np.asarray(P, float).reshape(-1, 3); lo = P.min(0) - pad; hi = P.max(0) + pad
    return (float(lo[0]), float(hi[0]), float(lo[1]), float(hi[1]), float(lo[2]), float(hi[2]))

def view_occluded(R, out_path, VP, TP, LAB, d, fbox, W, title, head, lines, polylines, legend=(), key=None, draw=None):
    """a WIRE frame with hidden lines hidden: the mesh opaque (each layout face LAB its own tint), the polylines [(P, colour, width)] depth-tested;
    draw(dr, proj) draws on top without a depth test (junction dots, labels). Returns 'HIT' when the cache has it."""
    if key and pic_hit(out_path, key): return "HIT"
    try: W = int(min(int(W), R.PIC_W)) if int(getattr(R, "PIC_W", 0) or 0) > 0 else int(W)
    except Exception: pass
    gb = (fbox[0] - 4, fbox[1] + 4, fbox[2] - 4, fbox[3] + 4, fbox[4] - 4, fbox[5] + 4)
    m = _clip_mask(VP, TP, gb); _q = source_quality(VP, TP)
    LAB = np.asarray(LAB); PAL = np.array(PALETTE, float)
    C = PAL[np.mod(LAB[m], len(PAL))] * 0.75 + 0.25 * np.array(VOX, float)
    im, cam = render_opaque(R, VP, TP[m], C, LAB[m], d, fbox, W)
    dr = ImageDraw.Draw(im); nv = nh = 0
    for pl in polylines:
        P_, col, wd = pl[0], pl[1], pl[2]; fc_ = pl[3] if len(pl) > 3 else ()
        a_, b_ = draw_occluded(dr, cam, P_, col, wd, faces=fc_); nv += a_; nh += b_
    proj = lambda P: [tuple(v) for v in np.stack([(np.asarray(P) @ cam["r3"] - cam["x0"]) / cam["mmpx"], (cam["y1"] - np.asarray(P) @ cam["u3"]) / cam["mmpx"]], axis=1)]
    if draw: draw(dr, proj)
    mmpx, r3, u3 = cam["mmpx"], cam["r3"], cam["u3"]
    _title_bars(dr, im, title, R.axes_label(r3, u3))
    bar = 10.0 / mmpx; dr.line([10, im.height - 12, 10 + bar, im.height - 12], fill=(255, 255, 255), width=3)
    dr.text((12, im.height - 30), "10 mm  (%.3f mm/px)" % mmpx, fill=(255, 255, 255))
    lines = list(lines) + ["segments drawn: %d visible (full colour), %d hidden behind the part (faint dotted)" % (nv, nh)]
    out = Image.new("RGB", (im.width, im.height + 40 + 26 * 3 + 24 * len(lines) + 10), (16, 16, 20))
    od = ImageDraw.Draw(out); od.text((10, 8), head, fill=(255, 235, 120), font=F22); out.paste(im, (0, 40))
    y = im.height + 46; x = 10
    for colr, t in legend:
        tw = od.textbbox((0, 0), t, font=F16)[2]
        if x + 30 + tw > out.width - 10: y += 26; x = 10
        od.rectangle([x, y + 3, x + 22, y + 19], fill=colr); od.text((x + 30, y + 2), t, fill=(235, 235, 235), font=F16); x += 44 + tw
    y += 30
    for ln in lines:
        od.text((10, y), ln, fill=(235, 235, 235), font=F16); y += 24
    _stamp_if_defective(out, od, _q, 40)
    out.save(out_path)
    if hasattr(R, "index_frame"): R.index_frame(out_path, fbox, d, head, quality=_q)
    if key: pic_mark(out_path, key)
    return "MISS"


def weld(V, T, q=1e-5):
    """unwelded STL triangles -> unique vertices and faces"""
    key = np.round(V[T].reshape(-1, 3) / q).astype(np.int64)
    u, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    Vu = np.zeros((len(u), 3)); np.add.at(Vu, inv, V[T].reshape(-1, 3)); cnt = np.bincount(inv, minlength=len(u))
    Vu /= cnt[:, None]
    return Vu, inv.reshape(-1, 3)


def orig_mesh(R, Part=None):
    """the ORIGINAL's material in the edit region as a mesh: content_base.stl when the job has one (a section's), else the content
    (content.brep, written by the region step) tessellated at 0.01 mm"""
    p = os.path.join(RUN, "content_base.stl")
    if os.path.isfile(p):
        V, T = R.read_stl(p); return np.asarray(V, float), np.asarray(T), p
    if Part is None: import Part
    s = Part.Shape(); s.importBrep(os.path.join(RUN, "content.brep"))
    V, T, _ = R.tess_shape(s, 0.01)
    return np.asarray(V, float), np.asarray(T), os.path.join(RUN, "content.brep")


def brep_source(stl=None):
    """31bb: True when the STL the skin steps run on is the job's own SOURCE MESH (skin-source: the original content tessellated - no voxel):
    REBUILD_source.json's source_md5 is its md5. The voxel field is shelved (the client 2026-10-08); this is the skin route's normal case now."""
    p = stl or STL
    try:
        rec = json.load(open(os.path.join(RUN, "REBUILD_source.json"), encoding="utf-8"))
        return bool(rec.get("source_md5")) and os.path.isfile(p) and md5(p) == rec["source_md5"]
    except (OSError, ValueError):
        return False


def source_fid(n_tri):
    """31bb: the ORIGINAL FACE INDEX of every triangle of source.stl (skin-source's source_fid.npz, aligned with the STL's triangle order - the weld
    keeps it), or None when the record is not this mesh's"""
    try:
        Z = np.load(os.path.join(RUN, "source_fid.npz")); fid = np.asarray(Z["fid"], np.int64)
    except (OSError, ValueError, KeyError):
        return None
    return fid if len(fid) == n_tri else None


def fid_labels(fid, seeded, ta, tb, dih_ok, Cn=None, own_base=-30000):
    """31bb - THE LAYOUT FROM THE FACE INDEX (a B-rep source; the client 2026-10-08: the junctions are in the B-rep). tl[t] = fid[t] for a triangle of an
    original face that has a point (seeded = kept, as it is). A face with NO point (the agent's pick: no point = not kept) is absorbed WHOLE by
    the kept neighbour it shares the longest border with (counted in shared mesh edges), in rounds, so a face behind an absorbed face follows
    it - smooth borders first, then (31bd) across a crease: no point means not kept, whatever the angle; every border of the layout stays a
    B-rep edge and every junction a B-rep vertex. A face nothing kept touches becomes a face of its own, one per connected group (own_base - k).
    Returns (tl, n_absorbed_triangles, n_own)."""
    from scipy.sparse import coo_matrix as _coo
    from scipy.sparse.csgraph import connected_components as _cc
    fid = np.asarray(fid, np.int64); n = len(fid)
    faces = [int(f) for f in np.unique(fid)]; sset = set(int(x) for x in seeded)
    lab_f = {f: (f if f in sset else -1) for f in faces}
    ok = np.asarray(dih_ok, bool); ta = np.asarray(ta); tb = np.asarray(tb)
    def _nbmap(a_, b_):
        fa, fb = fid[a_], fid[b_]; cross = fa != fb; nb = {}
        for x, y in zip(fa[cross].tolist(), fb[cross].tolist()):
            nb.setdefault(x, {}); nb[x][y] = nb[x].get(y, 0) + 1
            nb.setdefault(y, {}); nb[y][x] = nb[y].get(x, 0) + 1
        return nb
    def _absorb(nb):
        for _round in range(len(faces) + 1):
            new = {}
            for f in faces:
                if lab_f[f] != -1: continue
                cands = [(c, -g) for g, c in nb.get(f, {}).items() if lab_f[g] >= 0]
                if cands:
                    c_, g_ = max(cands); new[f] = lab_f[-g_]
            if not new: break
            lab_f.update(new)
    _absorb(_nbmap(ta[ok], tb[ok]))
    if any(lab_f[f] == -1 for f in faces): _absorb(_nbmap(ta, tb))
    left = [f for f in faces if lab_f[f] == -1]; n_own = 0
    if left:
        idx = {f: i for i, f in enumerate(left)}; nb = _nbmap(ta, tb)
        pairs = [(idx[x], idx[y]) for x in left for y in nb.get(x, {}) if y in idx]
        G = _coo((np.ones(len(pairs)), ([p[0] for p in pairs], [p[1] for p in pairs])), shape=(len(left), len(left))) if pairs else _coo((len(left), len(left)))
        _nc, lc_ = _cc(G, directed=False)
        for f in left: lab_f[f] = own_base - int(lc_[idx[f]])
        n_own = int(len(np.unique(lc_)))
    tl = np.array([lab_f[int(f)] for f in fid], np.int64)
    nabs = int(sum(1 for t in range(n) if lab_f[int(fid[t])] >= 0 and lab_f[int(fid[t])] != int(fid[t])))
    return tl, nabs, n_own


def repair_twins(PJ, live, absorbed, remap, newp, say=print):
    """31be - THE TWINS AFTER THE MERGES, FROM THE RAW LAYOUT'S grp PAIRS (the agent, 2026-10-08: 31bd paired them from `mirror_of`, which skin-labels
    wrote in its PRE-renumbering numbers - unrelated faces were grouped in threes, one with a wall cap; 34 clean pairs became 14-17).
    A twin pair in the raw layout = two non-cap patches sharing a grp. A survivor's members are itself and what it absorbed; its twin is the
    survivor holding its members' raw twins. A grp that already pairs two live faces is never touched; a pair is made only when the twin
    survivor is free (not in a clean pair with someone else); no grp ever gets a third member. Returns (repaired, asymmetric, bad_groups)."""
    grp0 = {}
    for q in PJ:
        if q.get("kind") == "cap" or q.get("grp") is None: continue
        grp0.setdefault(q["grp"], []).append(int(q["patch"]))
    twin0 = {}
    for g, ps in grp0.items():
        if len(ps) == 2: twin0[ps[0]] = ps[1]; twin0[ps[1]] = ps[0]
    members = {p: set([p]) | set(absorbed.get(p, [])) for p in live}
    holder = {x: p for p in live for x in members[p]}
    def live_grp():
        d = {}
        for p in live:
            r = newp[remap[p]]
            if r.get("kind") == "cap" or r.get("grp") is None: continue
            d.setdefault(r["grp"], []).append(p)
        return d
    repaired = 0; asym = []
    for p in sorted(live):
        rp = newp[remap[p]]
        if rp.get("kind") == "cap": continue
        lg = live_grp(); g = rp.get("grp")
        if g is not None and len(lg.get(g, [])) == 2: continue
        tw = {twin0[x] for x in members[p] if x in twin0}
        if not tw: continue
        holders = {holder[x] for x in tw if x in holder and holder[x] != p}
        if len(holders) != 1:
            if len(holders) > 1: asym.append((remap[p], sorted(remap[h] for h in holders)))
            continue
        s_ = next(iter(holders)); rs = newp[remap[s_]]
        gs = rs.get("grp")
        if gs is not None and len(lg.get(gs, [])) == 2 and p not in lg[gs]:
            asym.append((remap[p], [remap[s_]])); continue
        master, twin = (p, s_) if PJ[p].get("mirror_of") is None else (s_, p)
        rm, rt = newp[remap[master]], newp[remap[twin]]
        g_ = rm.get("grp") if rm.get("grp") is not None else rm.get("label")
        rm["grp"] = g_; rm.pop("mirror_of", None); rt["grp"] = g_; rt["mirror_of"] = remap[master]
        repaired += 1
    lg = live_grp(); bad = {g: [remap[x] for x in ps] for g, ps in lg.items() if len(ps) > 2}
    return repaired, asym, bad


def frozen_surfaces(Part=None):
    """every frozen region's surface (keep_frozen.json, written by the runner from the atlas) as one compound, or None"""
    try:
        rows = json.load(open(os.path.join(RUN, "keep_frozen.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if Part is None: import Part
    shapes = []
    for r in rows:
        sp = r.get("surface") or ""
        if sp and os.path.isfile(sp):
            s = Part.Shape(); s.importBrep(sp); shapes.append(s)
    return Part.makeCompound(shapes) if shapes else None


PALETTE = [(0.95, 0.30, 0.85), (0.30, 0.85, 0.95), (0.95, 0.85, 0.25), (0.45, 0.95, 0.40), (0.95, 0.50, 0.25), (0.55, 0.55, 1.00),
           (1.00, 0.45, 0.55), (0.70, 1.00, 0.85), (0.85, 0.65, 1.00), (1.00, 0.75, 0.55), (0.40, 0.75, 0.55), (0.80, 0.80, 0.40)]

def _seg_dist(P, A, B):
    AB = B - A; t = np.clip(np.einsum("...j,...j->...", P - A, AB) / np.maximum(np.einsum("...j,...j->...", AB, AB), 1e-30), 0, 1)
    return np.linalg.norm(P - (A + t[..., None] * AB), axis=-1)
def tri_dist(P, A, B, C):
    """exact distance from P (...,3) to triangles (A,B,C) (...,3)"""
    n = np.cross(B - A, C - A); nn = np.linalg.norm(n, axis=-1); n = n / np.maximum(nn, 1e-30)[..., None]
    dpl = np.einsum("...j,...j->...", P - A, n); Q = P - dpl[..., None] * n
    def side(X, Y): return np.einsum("...j,...j->...", np.cross(Y - X, Q - X), n)
    inside = (side(A, B) >= 0) & (side(B, C) >= 0) & (side(C, A) >= 0)
    de = np.minimum(np.minimum(_seg_dist(P, A, B), _seg_dist(P, B, C)), _seg_dist(P, C, A))
    return np.where(inside & (nn > 1e-20), np.abs(dpl), de)
class MeshDist(object):
    def __init__(self, V, T, k=12):
        from scipy.spatial import cKDTree
        self.V = np.asarray(V, float); self.T = np.asarray(T); self.k = k
        self.kd = cKDTree(self.V[self.T].mean(axis=1))
    def __call__(self, P, chunk=100000):
        P = np.asarray(P, float); out = np.zeros(len(P))
        for i0 in range(0, len(P), chunk):
            kk = min(self.k, len(self.T)); Pc = P[i0:i0 + chunk]; _, nn = self.kd.query(Pc, k=kk, workers=-1)
            if kk == 1: nn = nn[:, None]
            Tn = self.T[nn]; A = self.V[Tn[..., 0]]; B = self.V[Tn[..., 1]]; C = self.V[Tn[..., 2]]
            out[i0:i0 + chunk] = tri_dist(Pc[:, None, :], A, B, C).min(axis=1)
        return out


# ORIGINAL
VANISH_MM = 0.5
VANISH_MM2 = 2.0
VANISH_CAP = 1.0
VANISH_LINK = 1.0
VANISH_FRAMES = 6
VANISH_PAIRS = 150000


def dist_capped(P, V, T, cap=VANISH_CAP, need_over=VANISH_MM, k=16, chunk=VANISH_PAIRS):
    """31bq B18: the distance of each point P to the mesh (V, T). The k-nearest-centroid bound everywhere (the true distance is no larger); EXACT where that
    bound is over `need_over` and the distance at most `cap` - every triangle whose centroid lies within min(bound, cap) + the p99 triangle radius is tried,
    and every larger triangle within cap + its own radius; beyond `cap` the value is at least `cap`. Returns (d, the triangle of the nearest point found,
    side: +1 the point lies on the side that triangle's normal points to - OUTSIDE an outward-wound mesh -, -1 the other side, 0 on it). numpy + scipy.
    R7W: kept APART from closest_on_mesh (exact everywhere): on the B18 samples of the fill piece (44 490 points, 471 568 triangles) closest_on_mesh took 91 s
    (its over-p99 pass tries 4 716 large triangles for every point) and this 6 s, the 0.5 mm classification identical on every point and the distance equal
    inside the cap (probe_cost); the exact pass runs in chunks of `chunk` pairs and of 200 points (100 large triangles) (the R6 form peaked at 705 MB there); no exception is
    swallowed - a failure reaches the caller (skin-look says the measure NOT TAKEN, a kit fault)."""
    from scipy.spatial import cKDTree
    P = np.asarray(P, float).reshape(-1, 3); V = np.asarray(V, float); T = np.asarray(T, int).reshape(-1, 3); n = len(P)
    d = np.full(n, np.inf); tri = np.full(n, -1, np.int64); Q = P.copy()
    if not n or not len(T): return d, tri, np.zeros(n, int)
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]; Cen = (A + B + C) / 3.0
    Rt = np.sqrt(np.max(np.stack([((X_ - Cen) ** 2).sum(1) for X_ in (A, B, C)], 1), 1))
    tree = cKDTree(Cen); kk = int(min(max(int(k), 1), len(T)))
    _, J = tree.query(P, k=kk); J = np.asarray(J, np.int64).reshape(n, -1)
    rows_ = max(1, int(chunk) // kk)
    for s0 in range(0, n, rows_):
        Jc = J[s0:s0 + rows_]; Pc = P[s0:s0 + rows_]; r_ = np.arange(len(Pc))
        Qc = _closest_pt_tri(Pc[:, None, :], A[Jc], B[Jc], C[Jc]); Dc = np.linalg.norm(Qc - Pc[:, None, :], axis=2); i_ = np.argmin(Dc, axis=1)
        d[s0:s0 + rows_] = Dc[r_, i_]; tri[s0:s0 + rows_] = Jc[r_, i_]; Q[s0:s0 + rows_] = Qc[r_, i_]
    def _take(p_, t_):      # over the
        for s0 in range(0, len(p_), int(chunk)):
            pp = p_[s0:s0 + int(chunk)]; tt = t_[s0:s0 + int(chunk)]
            if not len(pp): continue
            Qp = _closest_pt_tri(P[pp], A[tt], B[tt], C[tt]); Dp = np.linalg.norm(Qp - P[pp], axis=1)
            o_ = np.lexsort((Dp, pp)); ps_ = pp[o_]; fst = np.ones(len(ps_), bool); fst[1:] = ps_[1:] != ps_[:-1]; w_ = o_[fst]
            m_ = Dp[w_] < d[pp[w_]]; ix_ = pp[w_][m_]
            d[ix_] = Dp[w_][m_]; tri[ix_] = tt[w_][m_]; Q[ix_] = Qp[w_][m_]
    need = np.nonzero(d > float(need_over))[0]
    if len(need):
        R99 = float(np.percentile(Rt, 99)); big = np.nonzero(Rt > R99)[0]
        r0 = np.minimum(d[need], float(cap)) + R99
        for c0 in range(0, len(need), 200):
            nd_ = need[c0:c0 + 200]
            Ls = tree.query_ball_point(P[nd_], r=r0[c0:c0 + 200]); ln_ = np.array([len(x_) for x_ in Ls], np.int64)
            if ln_.sum(): _take(np.repeat(nd_, ln_), np.concatenate([np.asarray(x_, np.int64) for x_ in Ls]))
            del Ls
        if len(big):
            ptree = cKDTree(P[need])
            for c0 in range(0, len(big), 100):
                bg_ = big[c0:c0 + 100]
                Lb = ptree.query_ball_point(Cen[bg_], r=Rt[bg_] + float(cap)); lb_ = np.array([len(x_) for x_ in Lb], np.int64)
                if lb_.sum(): _take(need[np.concatenate([np.asarray(x_, np.int64) for x_ in Lb])], np.repeat(bg_, lb_))
    N = np.cross(B - A, C - A); N = N / np.maximum(np.linalg.norm(N, axis=1), 1e-30)[:, None]
    s_ = np.einsum("ij,ij->i", P - Q, N[np.maximum(tri, 0)])
    return d, tri, np.where(d < 1e-9, 0, np.sign(s_)).astype(int)


def faces_against_piece(Vs, Fs, fid, V, T, seed=3, per_mm2=5.0, nmin=160, nmax=4000, mm=VANISH_MM, cap=VANISH_CAP):
    """31bq B18: every ORIGINAL face of the source mesh (Vs, Fs; fid = the original face of each triangle - a negative id, a wall cap, is left out) against
    the piece's own mesh (V, T, outward-wound): area-drawn samples (per_mm2 a mm2, at least nmin and at most nmax a face), each one's distance by dist_capped.
    Returns ({face: {"area", "off_mm2" (the area lying over `mm` from the piece), "removed_mm2" (off and OUTSIDE the piece: the original stood proud of it -
    material taken away), "filled_mm2" (off and INSIDE it: material added), "max_mm" (None: over `cap`), "n"}}, (S, the face of each sample, its weight mm2,
    d, its nearest piece triangle, its side, its SOURCE triangle - R7W: the layout face a sample lies on is its own triangle's)) - ({}, None) when there is
    nothing to measure."""
    Vs = np.asarray(Vs, float); Fs = np.asarray(Fs, int).reshape(-1, 3); fid = np.asarray(fid, np.int64)
    Pt = Vs[Fs]; At = 0.5 * np.linalg.norm(np.cross(Pt[:, 1] - Pt[:, 0], Pt[:, 2] - Pt[:, 0]), axis=1)
    rs = np.random.RandomState(int(seed)); S = []; SF = []; SW = []; ST_ = []
    for f in sorted(int(x_) for x_ in np.unique(fid[fid >= 0])):
        ti = np.nonzero(fid == f)[0]; ti = ti[At[ti] > 0]
        if not len(ti): continue
        af = float(At[ti].sum()); nn = int(min(nmax, max(nmin, np.ceil(af * per_mm2))))
        pk = rs.choice(ti, size=nn, replace=True, p=At[ti] / af); r1 = np.sqrt(rs.rand(nn)); r2 = rs.rand(nn)
        S.append((1 - r1)[:, None] * Pt[pk, 0] + (r1 * (1 - r2))[:, None] * Pt[pk, 1] + (r1 * r2)[:, None] * Pt[pk, 2]); SF.append(np.full(nn, f, np.int64)); SW.append(np.full(nn, af / nn)); ST_.append(pk.astype(np.int64))
    if not S: return {}, None
    S = np.vstack(S); SF = np.concatenate(SF); SW = np.concatenate(SW); ST_ = np.concatenate(ST_)
    d, tri, side = dist_capped(S, V, T, cap=cap, need_over=mm)
    out = {}
    for f in np.unique(SF):
        m_ = SF == f; w_ = SW[m_]; dd = d[m_]; off = dd > mm; sd = side[m_]
        out[int(f)] = {"area": round(float(w_.sum()), 3), "off_mm2": round(float(w_[off].sum()), 3), "removed_mm2": round(float(w_[off & (sd > 0)].sum()), 3),
                       "filled_mm2": round(float(w_[off & (sd < 0)].sum()), 3), "max_mm": (round(float(dd.max()), 3) if float(dd.max()) <= cap else None), "n": int(m_.sum())}
    return out, (S, SF, SW, d, tri, side, ST_)


def off_regions(S, W, off, link=VANISH_LINK):
    """31bq B18 (R7W, the skeptic's finding 1): the samples OFF the piece in CONNECTED REGIONS - two off samples closer than `link` mm are one region, whatever
    original face each lies on (a feature that leaves as several small faces is one region; the two lens pads of a symmetric edit are two). Returns (lab: the
    region of each sample, -1 for a sample on the piece; areas: each region's off area, mm2 - the sum of its samples' weights). numpy + scipy."""
    from scipy.spatial import cKDTree
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    S = np.asarray(S, float).reshape(-1, 3); W = np.asarray(W, float); off = np.asarray(off, bool)
    lab = np.full(len(S), -1, np.int64); idx = np.nonzero(off)[0]
    if not len(idx): return lab, np.zeros(0)
    pr = cKDTree(S[idx]).query_pairs(r=float(link), output_type="ndarray")
    G = coo_matrix((np.ones(len(pr)), (pr[:, 0], pr[:, 1])), shape=(len(idx), len(idx)))
    nc, l_ = connected_components(G, directed=False); lab[idx] = l_
    return lab, np.bincount(l_, weights=W[idx], minlength=nc)


def drop_boxes(PT):
    """31bq B18 (R7W, the skeptic's finding 7 - the reasoned box's path had never run): the PTS_DROP boxes of a points record (points1000.json) with their
    reasons, [(box [x0 x1 y0 y1 z0 z1], why or None)] - the reason after "|" in the lever (31bq B22's form, as sk_points._boxes reads it), else lever_whys'
    entry of the same box, else None (a box written before B22 carries none)."""
    PT = PT if isinstance(PT, dict) else {}; out = []
    whys = [w_ for w_ in ((PT.get("lever_whys") or {}).get("PTS_DROP") or []) if isinstance(w_, dict)]
    for part_ in str((PT.get("levers") or {}).get("PTS_DROP") or "").split(";"):
        nums_, _, why_ = part_.partition("|"); v_ = nums_.replace(",", " ").split()
        if len(v_) < 6: continue
        try: b_ = [float(x_) for x_ in v_[:6]]
        except ValueError: continue
        w_ = why_.strip() or None
        if w_ is None:
            for e_ in whys:
                bb_ = e_.get("box") or []
                if len(bb_) >= 6 and np.allclose(np.asarray(bb_[:6], float), np.asarray(b_, float), atol=1e-6): w_ = str(e_.get("why") or "").strip() or None; break
        out.append((b_, w_))
    return out


def crease_t(r, Vs, Fs, pid, pair, crease, near=1.0):
    """31bq B18 (R7W): the strip a decided blend of radius r makes beside its crease - t = r tan(beta / 2) (L141), beta the angle between the two layout faces'
    outward normals on the source mesh (Vs, Fs; pid = the layout face of each triangle), area-weighted over their triangles with a corner within `near` mm of the crease
    polyline. Returns (t, beta) - (r, None) when a side has no triangle there; t at most 4 r (beta 152 deg)."""
    Vs = np.asarray(Vs, float); Fs = np.asarray(Fs, int).reshape(-1, 3); pid = np.asarray(pid); cr = np.asarray(crease, float).reshape(-1, 3)
    if len(cr) < 2: return float(r), None
    segs = np.stack([cr[:-1], cr[1:]], 1); ns = []
    for p_ in pair:
        ti = np.nonzero(pid == int(p_))[0]
        if not len(ti): return float(r), None
        Pt = Vs[Fs[ti]]; _, dd = nearest_on_segments(Pt.reshape(-1, 3), segs); ti = ti[dd.reshape(-1, 3).min(1) <= near]
        if not len(ti): return float(r), None
        Pn = Vs[Fs[ti]]; nv = np.cross(Pn[:, 1] - Pn[:, 0], Pn[:, 2] - Pn[:, 0]).sum(0)
        if np.linalg.norm(nv) < 1e-12: return float(r), None
        ns.append(nv / np.linalg.norm(nv))
    beta = float(np.degrees(np.arccos(np.clip(ns[0] @ ns[1], -1.0, 1.0))))
    return float(min(4.0 * r, r * np.tan(np.radians(min(beta, 179.0)) / 2.0))), round(beta, 1)


def blend_tie(S, S_patch, S_fil, blends, margin=VANISH_MM):
    """31bq B18 (R7W, the skeptic's finding 2 - the 'blend' class read no record: the nearest fillet face cleared a pad): which samples a DECIDED blend accounts
    for - a sample whose nearest piece face is a blend (S_fil), whose own layout face (S_patch) is one of the two faces of a decided fillet line, and that lies
    in that blend's strip: within t + margin of the line's crease. blends: [{"line", "pair": (p, q), "crease": (n, 3), "t"}] - fillets.json of THIS wireframe,
    the crease the decided line as drawn (network_frame.brep). Returns the line of each sample (-1: no decided blend accounts for it; the nearest crease wins)."""
    S = np.asarray(S, float).reshape(-1, 3); S_patch = np.asarray(S_patch); S_fil = np.asarray(S_fil, bool)
    out = np.full(len(S), -1, np.int64); best = np.full(len(S), np.inf)
    for b_ in blends or ():
        cr = np.asarray(b_.get("crease"), float).reshape(-1, 3)
        if len(cr) < 2: continue
        m_ = S_fil & np.isin(S_patch, [int(x_) for x_ in b_["pair"]])
        if not m_.any(): continue
        ix = np.nonzero(m_)[0]; _, dd = nearest_on_segments(S[ix], np.stack([cr[:-1], cr[1:]], 1))
        ok = (dd <= float(b_["t"]) + float(margin)) & (dd < best[ix])
        out[ix[ok]] = int(b_["line"]); best[ix[ok]] = dd[ok]
    return out


VANISH_BY_RECORD = ("dropped", "buried", "blend")
def classify_parts(parts, rec):
    """31bq B18 (R7W): each PART - an original face's off samples inside one region - gets its CLASS, what the record says about it, tried in this order:
       dropped    - the face got no point and most of the part lies in a PTS_DROP box WITH its reason (part["drop"] = (box no., why))     BY A RECORD
       buried     - a decided blend's chain names the face "buried" (rec["buried_of"][f] = [lines])                                  that removes
       blend      - most of the part lies in a DECIDED blend's strip on its own layout face (part["blend"] = (share, [lines]))         it there
       unreasoned - most of the part lies in a PTS_DROP box with NO reason (31bq B22: no decision anyone can check)                 NAMED - the
       absorbed   - the face got no point (rec["no_points"]): the grid stepped over it and its neighbour took it                     pictures decide
       feature    - the feature map merged it with other kept faces (rec["merged"][f]) and that face was re-spanned (rec["feat_of"][f])
       own        - its own layout face was re-spanned through its wires (rec["respanned"][f])
       lost       - NOT ACCOUNTED FOR: its layout face has no face in the piece (rec["in_piece"][f] False), or keeps an original surface and still misses it
    parts: [{"face", "region", "off_mm2", "drop": (box no., why or None) | None, "blend": (share, [lines], {line: t})}] - "cls" and "why" set in place; returned."""
    g_ = lambda k_, f_, dflt=None: (rec.get(k_) or {}).get(f_, dflt)
    nop = set(int(x_) for x_ in (rec.get("no_points") or ()))
    for r_ in parts:
        f = int(r_["face"]); dr_ = r_.get("drop"); bl_ = r_.get("blend") or (0.0, [], {})
        if f in nop and dr_ is not None and dr_[1] and float(r_.get("removed_mm2") or 0.0) > max(float(r_.get("filled_mm2") or 0.0), 0.5 * VANISH_MM2):
            r_["cls"] = "removed"; r_["why"] = "MATERIAL REMOVED - %.1f mm2 of this original face stands OUTSIDE the piece (filled %.1f mm2) under PTS_DROP box %s (%s): a drop box excuses filling (a slot closed), never removal - name the removal on the card as intended, or keep the face / its points (31br G3)" % (
                float(r_.get("removed_mm2") or 0.0), float(r_.get("filled_mm2") or 0.0), dr_[0], str(dr_[1])[:120])
        elif f in nop and dr_ is not None and dr_[1]:
            r_["cls"] = "dropped"; r_["why"] = "dropped by PTS_DROP box %s - its reason: %s" % (dr_[0], dr_[1])
        elif g_("buried_of", f):
            r_["cls"] = "buried"; r_["why"] = "buried by the blend of line(s) %s (the chain's \"buried\" list)" % sorted(set(int(x_) for x_ in g_("buried_of", f)))
        elif float(bl_[0] or 0.0) >= 0.5:
            r_["cls"] = "blend"; r_["why"] = "under the DECIDED blend of line(s) %s: %.0f %% of it lies in that blend's strip (t %s mm + %.1f) beside the line's crease on its own layout face, nearest a blend face of the piece%s" % (
                sorted(bl_[1]), 100.0 * float(bl_[0]), "/".join("%.2f" % float(t_) for t_ in (bl_[2] or {}).values() if t_ is not None) or "?", VANISH_MM,
                (" - the other %.1f mm2 lies BEYOND any decided blend's strip: no record accounts for it (R7W)" % (float(r_["off_mm2"]) * (1.0 - float(bl_[0])))) if float(bl_[0]) < 1.0 - 1e-9 else "")
        elif dr_ is not None:
            r_["cls"] = "unreasoned"; r_["why"] = "inside PTS_DROP box %s, which carries NO REASON (31bq B22: a box without its reason is no decision anyone can check) - give the box its reason (\"x0 x1 y0 y1 z0 z1 | why\") or keep the face (PTS_BOX)" % dr_[0]
        elif f in nop:
            r_["cls"] = "absorbed"; r_["why"] = "it got NO POINT - the grid stepped over it and its neighbour took it (a PTS_BOX keeps it; a PTS_DROP with its reason drops it on purpose)"
        elif not g_("in_piece", f, True):
            r_["cls"] = "lost"; r_["why"] = "NOT ACCOUNTED FOR - its layout face has no face in the piece"
        elif g_("merged", f) and g_("respanned", f):
            fe_ = g_("feat_of", f); fw_ = (rec.get("feat_why") or {}).get(fe_) if fe_ else None
            r_["cls"] = "feature"; r_["feature"] = fe_; r_["why"] = "the feature map merged it into %s with other kept faces and skin-build re-spanned that face%s" % (
                ("feature " + fe_) if fe_ else "one face", (" - the map's reason: " + fw_) if fw_ else " - the map gives no reason for it")
        elif g_("respanned", f):
            r_["cls"] = "own"; r_["why"] = "its own layout face was re-spanned through its wires (its LINES / the face ladder) and the original's shape is not kept there"
        else:
            r_["cls"] = "lost"; r_["why"] = "NOT ACCOUNTED FOR - its layout face keeps an original surface in the piece and still misses it"
    return parts


def name_regions(parts, areas, mm2=VANISH_MM2):
    """31bq B18 (R7W, the skeptic's finding 1): THE THRESHOLD PER REGION - a region with mm2 or more of off area LEFT the piece; it is NAMED when mm2 or more of
    that area is in parts no record accounts for (a feature that leaves as several small faces sums there; a blend part's area BEYOND its strip counts), else it stands by its records. Returns {region:
    {"off_mm2", "named_mm2", "named"}} for every region of mm2 or more."""
    out = {}
    for r_, a_ in enumerate(np.asarray(areas, float)):
        if a_ < mm2: continue
        nm_ = sum(float(p_["off_mm2"]) * ((1.0 - float((p_.get("blend") or (0.0,))[0] or 0.0)) if p_.get("cls") == "blend" else (0.0 if p_.get("cls") in VANISH_BY_RECORD else 1.0))
                  for p_ in parts if int(p_["region"]) == r_)
        out[r_] = {"off_mm2": round(float(a_), 3), "named_mm2": round(nm_, 3), "named": nm_ >= mm2}
    return out


def _clip_uv(segs, au, av, window):
    """the segments (m, 2, 3) cut to the window ((u0, u1), (v0, v1)) in their (au, av) coordinates - Liang-Barsky, vectorised; the pieces inside kept"""
    segs = np.asarray(segs, float).reshape(-1, 2, 3)
    if not len(segs): return segs
    (u0, u1), (v0, v1) = window; a = segs[:, 0]; b = segs[:, 1]; dl = b - a
    t0 = np.zeros(len(segs)); t1 = np.ones(len(segs)); ok = np.ones(len(segs), bool)
    for ax_, lo_, hi_ in ((au, u0, u1), (av, v0, v1)):
        p_ = dl[:, ax_]; q0 = a[:, ax_] - lo_; q1 = hi_ - a[:, ax_]
        for pp_, qq_ in ((-p_, q0), (p_, q1)):
            par = np.abs(pp_) < 1e-15; ok &= ~(par & (qq_ < 0))
            r_ = np.where(par, 0.0, qq_ / np.where(par, 1.0, pp_))
            ent = ~par & (pp_ < 0); ext = ~par & (pp_ > 0)
            t0 = np.where(ent, np.maximum(t0, r_), t0); t1 = np.where(ext, np.minimum(t1, r_), t1)
    ok &= t0 <= t1
    return np.stack([a[ok] + t0[ok, None] * dl[ok], a[ok] + t1[ok, None] * dl[ok]], 1)


def section_frame(R, out_path, old, new, axis, c, window, tol, head, lines, quality=None, W=900):
    """31bq B18 (R7W, the skeptic's finding 4 - a FILLED loss is invisible in a 3-D frame: the original lies inside the piece): the region cut by the plane
    axis = c AS THE STATION FRAMES DRAW IT (rb_review_body, L146) - both meshes' sections cut to the window ((u0, u1), (v0, v1)), a segment lying on the other's
    section within tol drawn ONCE green, the rest YELLOW (the original only) / BLUE (the piece only), 3 px; the head and the lines over and under it, the
    meshes' quality line, a RENDER DEFECTIVE band when the quality says so, the frame's record (index_frame). old / new: (V, T). Returns {"both", "old_only",
    "new_only"} - the segment counts."""
    au, av = [a_ for a_ in (0, 1, 2) if a_ != axis]
    cut_ = lambda VT_: _clip_uv(R.section_segs(np.asarray(VT_[0], float), np.asarray(VT_[1], int), axis, float(c)), au, av, window)
    sa = cut_(old); sb = cut_(new)
    ma = R.match_segs(sa, sb, au, av, tol); mb = R.match_segs(sb, sa, au, av, tol)
    both = sb[mb] if len(sb) else sb; oo = sa[~ma] if len(sa) else sa; no = sb[~mb] if len(sb) else sb
    wu = float(window[0][1] - window[0][0]); grid = 1.0 if wu <= 15 else (2.0 if wu <= 40 else 5.0)
    R.draw_section(out_path, [(both, (90, 210, 110), 2), (oo, (255, 215, 60), 3), (no, (80, 200, 255), 3)], axis,
                   "%s = %.2f   GREEN: both within %.2f mm   YELLOW: the original only   BLUE: the piece only" % ("xyz"[axis], float(c), float(tol)), W=W, window=window, grid=grid)
    fb_ = [0.0] * 6; fb_[2 * au], fb_[2 * au + 1] = window[0]; fb_[2 * av], fb_[2 * av + 1] = window[1]; fb_[2 * axis], fb_[2 * axis + 1] = float(c) - 1.0, float(c) + 1.0
    q = frame_quality(quality, tuple(fb_)) if isinstance(quality, dict) else {}
    im = Image.open(out_path).convert("RGB"); od0 = ImageDraw.Draw(Image.new("RGB", (8, 8))); wmax = im.width - 20
    heads = _wrap(od0, head, F22, wmax); body = [l_ for ln in lines if ln for l_ in _wrap(od0, ln, F16, wmax)]; qlines = _wrap(od0, quality_line(q) if q else "mesh: not measured", F16, wmax)
    stamps = _wrap(od0, "RENDER DEFECTIVE - NO EVIDENCE: %s" % q.get("why", ""), F16, wmax) if q.get("defective") else []
    out = Image.new("RGB", (im.width, 12 + 28 * len(heads) + (6 + 22 * len(stamps) + 4 if stamps else 0) + im.height + 6 + 22 * (len(body) + len(qlines)) + 12), (16, 16, 20))
    od = ImageDraw.Draw(out); y = 8
    for h_ in heads: od.text((10, y), h_, fill=(255, 235, 120), font=F22); y += 28
    y += 4
    if stamps:
        od.rectangle([0, y, out.width, y + 6 + 22 * len(stamps)], fill=(150, 20, 20))
        for s_ in stamps: od.text((10, y + 3), s_, fill=(255, 255, 255), font=F16); y += 22
        y += 10
    out.paste(im, (0, y)); y += im.height + 6
    for ln in body: od.text((10, y), ln, fill=(235, 235, 235), font=F16); y += 22
    for ln in qlines: od.text((10, y), ln, fill=(150, 150, 160), font=F16); y += 22
    out.save(out_path)
    if hasattr(R, "index_frame"):
        dn_ = [0.0, 0.0, 0.0]; dn_[axis] = -1.0
        R.index_frame(out_path, fb_, dn_, head, quality=q)
    return {"both": int(len(both)), "old_only": int(len(oo)), "new_only": int(len(no))}


def md5(path):
    import hashlib
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


RULE_31BH = ("THE ORIGINAL IS THE STARTING REFERENCE, NOT A CONSTRAINT - you are editing this part: any border can be redrawn or moved (LINES / RAILS), a face split "
             "by a line (role split), faces joined (FEATURES), a strip folded into its neighbour; nothing holds the wireframe to the original's face boundaries. "
             "THE ONE EXCEPTION IS THE FRAME: where the skin meets the body (the edit region's walls) every face ends EXACTLY on the body's own section faces, "
             "edges and vertices - skin-frame refuses an open face.")


def _border_note():
    """31bd: the caption's truth depends on the source - on a B-rep source the master side's borders ARE the model's edges"""
    try:
        if brep_source():
            return ("BORDERS here START as the model's own edges on the MASTER side (a B-rep source) and follow the mesh (saw-tooth) on the mirrored side until",
                    "skin-wires mirrors the master's lines onto it (WIRE_*). " + RULE_31BH)
    except Exception:
        pass
    return ("BORDERS here are the VOXEL's triangles grouped by face - their saw-tooth is the voxel, not the model's edge;",
            "the model's edges are the lines skin-wires draws (WIRE_*). " + RULE_31BH)
class _BorderNote(tuple):
    """BORDER_NOTE reads as a tuple; the text is decided at the first use (brep_source needs RUN / STL, set before any picture is drawn)"""
    def __new__(cls): return super().__new__(cls, ())
    def __iter__(self): return iter(_border_note())
    def __len__(self): return len(_border_note())
    def __getitem__(self, i): return _border_note()[i]
BORDER_NOTE = _BorderNote()
# over the
VIEW_OF_STEP = {
    "SP7d (skin-points)": "overlay - the source mesh transparent, every point on its face",
    "SP8 / LAYOUT / SP12 / FEAT (skin-labels, skin-rim, skin-features)": "label - the layout face by face",
    "SP4 (skin-network)": "overlay - the network's lines over the transparent mesh (NET_PICS)",
    "WIRE / CORNERS (skin-wires)": "occluded - the wireframe with hidden lines hidden (WIRE_OCC=0 draws the overlay form, said on the frame)",
    "MIRROR (skin-mirror)": "model - the layout or the piece opaque, pairs tinted",
    "SKIN_look whole and close-ups (skin-look)": "THE PIECE VIEW (31bn) - ONE conforming mesh of the whole piece (MeshPart, PIC_DEV 0.02 mm / PIC_ANG 0.05 rad, cached by md5), opaque, z-buffered, smooth-shaded from the surface normals within each face (creases stay), per-face tint, every frame stamped with the mesh's quality; a DEFECTIVE frame (cracks, coarse facets) is no evidence",
    "SKIN_look face iso (skin-look full)": "THE PIECE VIEW framed on the face's box, the face tinted, its neighbours grey, side light, its border depth-tested; the two corners of the face's frame that SEE it (visible_fraction >= LOOK_VIS, the iso tilt first, a lower tilt only when no wider one sees it - the title says); never a cut of the mesh",
    "SKIN_look free-edge clusters (skin-look)": "THE PIECE VIEW framed on the cluster, the free edges red (depth-tested)",
    "SKIN_look vanished (skin-look, 31bq B18)": "per NAMED REGION (R7W) two frames: its SECTION, as the station frames draw it (the source mesh = the original and the piece mesh cut on one axis plane through the region, a line on both within VANISH_MM GREEN, the original only YELLOW, the piece only BLUE - a filled loss shows there) and THE PIECE VIEW of the piece (grey) with the original's off surface of the region's named faces YELLOW (depth-tested where it stands proud; GHOSTED - drawn over the piece - where it lies inside it), its borders magenta; their own picture key (the records they draw)",
    "look_at (kit tool, the look-before-measure picture)": "THE PIECE VIEW of the whole shape framed on the box - the faces touching the box in their tints, the rest grey, the box outlined yellow and depth-tested; never a clipped set of triangles, never see-through",
    "review_body / TRIAL (reinsert, review-body)": "model - the real body (kit review's renderer)",
}
BORDER_COL = (150, 220, 255)


def carry_lines(prev, cur, max_mm=3.0):
    """31av: THE LINE DECISIONS CARRIED TO A NEW NUMBERING (the agent's job_skin_lines_remap.py, R4 skin 2: a re-split renumbered every chain and 60-70
    reasoned decisions were lost each time; the client 2026-10-07: "Yes keep what is correct"). prev: [{"chain", "sig": [feature, feature], "mid": xyz,
    "dec": {...} or None}] - the last skin-wires run's chains and the decision each was drawn with; cur: [{"chain", "sig", "mid"}] - this run's.
    A current chain takes the decision of the previous chain between the SAME two features whose middle is nearest its own, within max_mm
    (the agent's MATCH_MM 3.0). Returns ({"<chain>": decision}, [(chain, why) - the chains left to decide, those on a cap left out])."""
    out = {}; todo = []
    P = [p for p in prev if p.get("dec") and p.get("sig") and p.get("mid") is not None]
    for c in cur:
        sc = sorted(str(x) for x in (c.get("sig") or []))
        best = None
        for p in P:
            if sorted(str(x) for x in p["sig"]) != sc: continue
            d = float(np.linalg.norm(np.asarray(c["mid"], float) - np.asarray(p["mid"], float)))
            if best is None or d < best[0]: best = (d, p)
        if best is not None and best[0] <= max_mm:
            dec = dict(best[1]["dec"]); why = str(dec.get("why", ""))
            k_ = why.find(" [carried from chain")
            dec["why"] = (why[:k_] if k_ >= 0 else why) + " [carried from chain %s]" % best[1]["chain"]
            out[str(c["chain"])] = dec
        elif "CAP" not in sc:
            todo.append((c["chain"], "no earlier line between %s within %g mm%s" % ("+".join(sc), max_mm, (" (nearest %.1f mm: chain %s)" % (best[0], best[1]["chain"])) if best else "")))
    return out, todo


def write_look(kind, frames, artefact, extra=None):
    """the record a judge reads: which frames show which artefact (its md5) - `kit rebuild judge --what <kind>` refuses a verdict on
    frames of an earlier artefact (31ai's rule, now for the skin's layout and piece)"""
    rec = {"kind": kind, "frames": [os.path.basename(f) for f in frames], "artefact": os.path.relpath(artefact, RUN), "md5": md5(artefact), "tag": TAG,
           "pics": PICS}
    if extra: rec.update(extra)
    if kind != "skin" and "frame_info" not in rec:
        try:
            _q = (list(_SRCQ.values()) or [None])[-1]
            if isinstance(_q, dict):
                rec["frame_info"] = {os.path.basename(f): {"quality": dict(_q)} for f in frames}; rec["mesh_quality"] = dict(_q)
        except Exception: pass
    fn = {"layout": "LAYOUT_LOOK.json", "skin": "PIECE_LOOK.json", "points": "POINTS_LOOK.json",
          "wires": "WIRES_LOOK.json"}[kind]                                                         # skin-wires
    with open(os.path.join(OUT, fn), "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1)
    return os.path.join(OUT, fn)

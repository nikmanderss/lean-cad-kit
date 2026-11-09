# kit rebuild
# content.brep
import os, sys, time, math, json, Part, FreeCAD
def _fail(m): print(m if str(m).startswith("FAIL") else "FAIL: " + str(m), flush=True); raise SystemExit(1)
import BOPTools.SplitAPI as SA
V = FreeCAD.Vector; T0 = time.time()
RUN = os.environ.get("RUN") or _fail("RUN not set: the job folder"); os.makedirs(RUN, exist_ok=True)
BUDGET = float(os.environ.get("BUDGET", "140"))
STATE_P = os.path.join(RUN, "state.json")
STATE = json.load(open(STATE_P)) if os.path.exists(STATE_P) else {}
def save_state(): json.dump(STATE, open(STATE_P, "w"))
def elapsed(): return time.time() - T0
SRC = os.environ.get("SRC") or _fail("SRC not set: the region's content brep (rb_region writes content.brep)")
S = Part.Shape(); S.importBrep(SRC)
big = max(S.Solids, key=lambda x: x.Volume); F = big.Faces
A_SMALL = float(os.environ.get("A_SMALL", "1.0")); FLAT = float(os.environ.get("FLAT", "0.25")); TOL = float(os.environ.get("TOL", "0.5")); PLANE_TOL = float(os.environ.get("PLANE_TOL", "0.05"))
DEPTH = 100.0; OUT = 0.0; OVERLAP = 1.0; SMOOTH = 0.05; M = 60.0; EXT = 80.0; STEP = float(os.environ.get("STEP", "1.0")); TOL_CAP = 0.1
bb = big.BoundBox
WIN = [float(t) for t in (os.environ.get("WIN") or _fail("WIN not set: 'x0 x1 y0 y1 z0 z1' of the region box")).split()]
PROTECT_P = [[float(v) for v in b.split()] for b in os.environ.get("PROTECT", "").split(";") if b.strip()]
if any(len(b) != 6 for b in PROTECT_P): _fail("FAIL: PROTECT box needs six numbers x0 x1 y0 y1 z0 z1")
PROTECT_FACES = os.environ.get("PROTECT_FACES", "0") == "1"
def meets_protect(b, grow=0.0):
    """does the BoundBox b meet any PROTECT box (grown by `grow` mm)"""
    for pb in PROTECT_P:
        if b.XMax >= pb[0] - grow and b.XMin <= pb[1] + grow and b.YMax >= pb[2] - grow and b.YMin <= pb[3] + grow and b.ZMax >= pb[4] - grow and b.ZMin <= pb[5] + grow: return True
    return False
win = Part.makeBox(WIN[1] - WIN[0], WIN[3] - WIN[2], WIN[5] - WIN[4], V(WIN[0], WIN[2], WIN[4]))
def in_win(p, m=0.01):
    return WIN[0] - m <= p.x <= WIN[1] + m and WIN[2] - m <= p.y <= WIN[3] + m and WIN[4] - m <= p.z <= WIN[5] + m
print("piece: %d faces, %.1f mm3, bbox x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f; window %s" % (len(F), big.Volume, bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax, WIN), flush=True)

def face_data(f):
    u0, u1, v0, v1 = f.ParameterRange; pts = []
    for a in range(1, 6):
        for b in range(1, 6):
            u = u0 + (u1 - u0) * a / 6.0; v = v0 + (v1 - v0) * b / 6.0
            try:
                if f.isPartOfDomain(u, v): pts.append((f.valueAt(u, v), f.normalAt(u, v)))
            except Exception: pass
    for e in f.Edges:
        m = e.valueAt(0.5 * (e.FirstParameter + e.LastParameter))
        try:
            u, v = f.Surface.parameter(m); pts.append((f.valueAt(u, v), f.normalAt(u, v)))
        except Exception: pass
    try:
        u, v = f.Surface.parameter(f.CenterOfMass); pts.append((f.valueAt(u, v), f.normalAt(u, v)))
    except Exception: pass
    c = f.CenterOfMass
    try: n = f.normalAt(*f.Surface.parameter(c))
    except Exception: n = f.normalAt(0.5, 0.5)
    vxs = [vx for vx in f.Vertexes if in_win(vx.Point, 0.5)] or list(f.Vertexes)
    dev = max(abs((vx.Point - c).dot(n)) for vx in vxs) if vxs else 0.0
    try:
        u, v = f.Surface.parameter(c); sgn = 1.0 if f.Surface.normal(u, v).dot(f.normalAt(u, v)) > 0 else -1.0
    except Exception: sgn = 1.0
    kind = type(f.Surface).__name__
    return {"pts": pts, "wpts": [pn for pn in pts if in_win(pn[0])], "c": c, "n": n, "dev": dev, "sgn": sgn, "kind": kind,
            "area": f.Area, "plane": kind == "Plane" or dev <= PLANE_TOL or (f.Area < A_SMALL and dev <= FLAT), "ext": set()}
D = [face_data(f) for f in F]
T_MIN = float(os.environ.get("T_MIN", "1.2")); V_MIN = float(os.environ.get("V_MIN", "50.0"))
def thin_behind(p, n):
    for t in (0.3, 0.6, 0.9, 1.2):
        if t > T_MIN: break
        if not big.isInside(p - n * t, 1e-6, True): return True
    return False
if "skin" in STATE:
    SKIN = {int(k): v for k, v in STATE["skin"].items()}
else:
    SKIN = {int(k): v for k, v in STATE.get("skin_partial", {}).items()}
    for i in range(len(F)):
        if D[i]["area"] < A_SMALL or not D[i]["wpts"] or i in SKIN: continue
        if PROTECT_FACES and meets_protect(F[i].BoundBox, 0.3): SKIN[i] = []; continue
        SKIN[i] = [j for j, (p, n) in enumerate(D[i]["wpts"]) if thin_behind(p, n)]
        STATE["skin_partial"] = {str(k): v for k, v in SKIN.items()}
        if elapsed() > 140: save_state(); print("skin scan PAUSED at face %d - run again" % (i + 1), flush=True); raise SystemExit(0)
    STATE["skin"] = {str(k): v for k, v in SKIN.items()}; STATE.pop("skin_partial", None); save_state()
    print("  (skin scan took %.0fs)" % elapsed(), flush=True)
for i, js in SKIN.items():
    if js:
        keep = [pn for j, pn in enumerate(D[i]["wpts"]) if j not in set(js)]
        D[i]["skin"] = len(js); D[i]["wpts"] = keep
print("  skin samples dropped: " + " ".join("f%d:%d/%d" % (i + 1, D[i].get("skin", 0), len(D[i]["wpts"]) + D[i].get("skin", 0)) for i in sorted(SKIN) if D[i].get("skin")), flush=True)
def on_window_wall(i):
    c = D[i]["c"]; n = D[i]["n"]
    for ax, lo, hi in ((0, WIN[0], WIN[1]), (1, WIN[2], WIN[3]), (2, WIN[4], WIN[5])):
        if abs(abs(n[ax]) - 1.0) < 0.01 and min(abs(c[ax] - lo), abs(c[ax] - hi)) < 0.05: return True
    return False
WALL = set(i for i in range(len(F)) if on_window_wall(i))
def surf_key(i):
    f = F[i]; k = D[i]["kind"]
    if k == "Plane":
        n = D[i]["n"]; d = D[i]["c"].dot(n)
        return ("Plane", round(n.x, 2), round(n.y, 2), round(n.z, 2), round(d, 1))
    try:
        b = Part.Face(f.Surface).BoundBox
        return (k, round(b.XMin, 1), round(b.XMax, 1), round(b.YMin, 1), round(b.YMax, 1), round(b.ZMin, 1), round(b.ZMax, 1))
    except Exception: return (k, i)
SAME = {}
def design_face(i):
    """a face the arrangement may take as a design surface: at least A_SMALL, not a window wall - or (PROTECT_FACES, 31af) any face
    meeting a PROTECT box whatever its size: the card says the void is designed, so its faces are"""
    if i in WALL: return False
    if D[i]["area"] >= A_SMALL: return True
    return PROTECT_FACES and D[i]["area"] > 1e-4 and meets_protect(F[i].BoundBox, 0.3)
for i in range(len(F)):
    if design_face(i): SAME.setdefault(surf_key(i), []).append(i)
for i in range(len(F)): D[i]["plane_own"] = D[i]["plane"]
REP = {}
for k, fs in SAME.items():
    r = max(fs, key=lambda i: D[i]["area"])
    grp_plane = all(D[i]["plane"] for i in fs)
    for i in fs: REP[i] = r; D[i]["plane"] = grp_plane
GAP = float(os.environ.get("GAP", "3.0")); GAP_FRAC = 0.5
def gap_pairs():
    """faces that look at another design face across an empty gap of at most GAP mm (most of their samples):
    facing normals, the other's surface within GAP along the normal, the projection inside the other's trimmed
    face, and the midpoint outside the solid. Returns the set of such faces."""
    idx = [i for i in range(len(F)) if design_face(i) and D[i]["wpts"]]
    out = set()
    for a in idx:
        na = D[a]["n"]; hits = 0; n_pts = len(D[a]["wpts"])
        for b in idx:
            if b == a or na.dot(D[b]["n"]) > -0.7: continue
            cnt = 0
            for p, n in D[a]["wpts"]:
                try: sg = signed(b, p)
                except Exception: continue
                if not (0.05 <= sg <= GAP): continue
                q = p - n * 0.0 + D[b]["n"] * 0.0
                try:
                    dd = F[b].distToShape(Part.Vertex(p))[0]
                except Exception: continue
                if dd > abs(sg) + 0.3: continue
                mid = p + n * (abs(sg) * 0.5)
                if not big.isInside(mid, 1e-6, True): cnt += 1
            if cnt > 0: GAPLOG.append((a, b, cnt, n_pts))
            hits = max(hits, cnt)
        if hits >= GAP_FRAC * n_pts: out.add(a)
    return out
print("  same surface: " + "; ".join(" ".join("f%d" % (i + 1) for i in fs) for fs in SAME.values() if len(fs) > 1), flush=True)
print("  window walls: %s;  planar: %s" % (" ".join("f%d" % (i + 1) for i in sorted(WALL)),
      " ".join("f%d" % (i + 1) for i in range(len(F)) if D[i]["plane"] and D[i]["kind"] != "Plane" and D[i]["area"] >= A_SMALL)), flush=True)

def signed(i, p):
    """signed distance of p from face i's extended surface; + = outside the material of i"""
    d = D[i]
    if d["plane"]: return (p - d["c"]).dot(d["n"])
    s = F[i].Surface; u, v = s.parameter(p); q = s.value(u, v); n = s.normal(u, v) * d["sgn"]
    return (p - q).dot(n)
def side_ok(i, faces, side):
    """side +1: every sample of `faces` on the material side of i (<= TOL); -1: every sample outside i (>= -TOL)"""
    vals = [side * signed(i, p) for g in faces for p, n in D[g]["wpts"]]
    return ((max(vals) <= TOL) if vals else True), (max(vals) if vals else 0.0)
def ext_faces(i, L=EXT):
    """the face's own surface over its natural range + four tangent skirts + four corner quads (G1 continuation,
    L mm past every boundary) - so that no prism side wall can sit on a neighbouring design face"""
    f = F[i]; s = f.Surface; k = D[i]["kind"]; u0, u1, v0, v1 = f.ParameterRange
    if D[i]["plane"]: return [Part.Face(Part.Plane(D[i]["c"], D[i]["n"]).toShape(-300, 300, -300, 300))]
    if k in ("Cylinder", "Cone"): return [Part.Face(s.toShape(0.0, 2 * math.pi, v0 - M, v1 + M))]
    if k == "SurfaceOfExtrusion":
        bc = s.BasisCurve; return [Part.Face(s.toShape(bc.FirstParameter, bc.LastParameter, v0 - M, v1 + M))]
    if k == "SurfaceOfRevolution":
        bc = s.BasisCurve; return [Part.Face(s.toShape(0.0, 2 * math.pi, bc.FirstParameter, bc.LastParameter))]
    if k not in ("BSplineSurface", "BezierSurface"): return [Part.Face(s.toShape(u0 - M, u1 + M, v0 - M, v1 + M))]
    U0, U1, V0, V1 = s.bounds(); um = 0.5 * (U0 + U1); vm = 0.5 * (V0 + V1)
    base = Part.Face(s)
    eU0 = s.uIso(U0).toShape(V0, V1); eU1 = s.uIso(U1).toShape(V0, V1); eV0 = s.vIso(V0).toShape(U0, U1); eV1 = s.vIso(V1).toShape(U0, U1)
    tU0 = s.tangent(U0, vm)[0] * (-L); tU1 = s.tangent(U1, vm)[0] * L; tV0 = s.tangent(um, V0)[1] * (-L); tV1 = s.tangent(um, V1)[1] * L
    faces = [base, eU0.extrude(tU0), eU1.extrude(tU1), eV0.extrude(tV0), eV1.extrude(tV1)]
    for (u, v), tu, tv in (((U0, V0), tU0, tV0), ((U0, V1), tU0, tV1), ((U1, V0), tU1, tV0), ((U1, V1), tU1, tV1)):
        P = s.value(u, v); faces.append(Part.Face(Part.makePolygon([P, P + tu, P + tu + tv, P + tv, P])))
    return faces
SHELLS = {}
def bound_shell(i, side):
    key = (i, side)
    if key not in SHELLS:
        faces = ext_faces(i)
        if side < 0: faces = [f.translated(D[i]["n"] * (-OVERLAP)) for f in faces]
        sh = Part.Shell(faces)
        try: sh.sewShape()
        except Exception: pass
        SHELLS[key] = sh
    return SHELLS[key]
def inner_point(s_):
    c = s_.CenterOfMass
    if s_.isInside(c, 1e-6, True): return c
    for fc in s_.Faces[:6]:
        try:
            q = fc.CenterOfMass; u, v = fc.Surface.parameter(q); q = fc.valueAt(u, v); n = fc.normalAt(u, v)
            if s_.isInside(q - n * 0.2, 1e-6, True): return q - n * 0.2
        except Exception: pass
    return c
def side_of(s_, i):
    """which side of bound i the piece s_ lies on: the sign of the farthest face-inner-point's signed distance"""
    best = None
    for fc in s_.Faces:
        try:
            q = fc.CenterOfMass; u, v = fc.Surface.parameter(q); q = fc.valueAt(u, v); n = fc.normalAt(u, v)
            sg = signed(i, q - n * 0.2)
        except Exception: continue
        if best is None or abs(sg) > abs(best): best = sg
    return best if best is not None else signed(i, s_.CenterOfMass)
def cut_by(sol, i, side):
    """the part of sol on the material side of bound i (side +1) or outside it, OVERLAP deep (side -1)"""
    pieces = SA.slice(sol, [bound_shell(i, side)], "Split", 1e-5)
    keep = []
    for s_ in pieces.Solids:
        sg = side_of(s_, i)
        if (side > 0 and sg <= 0.0) or (side < 0 and sg >= -OVERLAP): keep.append(s_)
    if not keep: return None
    out = keep[0]
    for k in keep[1:]: out = out.fuse(k)
    return out
def hs(i, side):
    raise RuntimeError("hs() retired: use cut_by")
def short_at(i, p):
    """which natural boundary of face i's surface the point p lies beyond/at ('u0','u1','v0','v1') or None"""
    if D[i]["plane"]: return None
    s = F[i].Surface
    try: U0, U1, V0, V1 = s.bounds()
    except Exception: return None
    try: u, v = s.parameter(p)
    except Exception: return None
    eu = 0.02 * (U1 - U0); ev = 0.02 * (V1 - V0)
    if u <= U0 + eu: return "u0"
    if u >= U1 - eu: return "u1"
    if v <= V0 + ev: return "v0"
    if v >= V1 - ev: return "v1"
    return None

SAME_TOL = float(os.environ.get("SAME_TOL", "0.15")); SAME_SPLIT = []
def _pts_of(i):
    pts = [p for p, n in D[i]["pts"] if in_win(p, 0.5)] + [vx.Point for vx in F[i].Vertexes if in_win(vx.Point, 0.5)]
    return pts or ([p for p, n in D[i]["pts"]] + [vx.Point for vx in F[i].Vertexes])
def _dev_to(r, i):
    try:
        vals = [abs(signed(r, p)) for p in _pts_of(i)]
        return max(vals) if vals else 0.0
    except Exception: return float("inf")
if SAME_TOL > 0:
    for i in range(len(F)): D[i]["plane"] = D[i]["plane_own"]
    for key, fs in list(SAME.items()):
        if len(fs) < 2: continue
        r = max(fs, key=lambda i: D[i]["area"]); stay = [r]; leave = []
        for i in fs:
            if i == r: continue
            dv = _dev_to(r, i)
            if dv <= SAME_TOL: stay.append(i)
            else: leave.append(i); SAME_SPLIT.append((i, r, dv))
        if not leave: continue
        SAME[key] = stay; groups = []
        for i in sorted(leave, key=lambda j: -D[j]["area"]):
            for g in groups:
                if _dev_to(g[0], i) <= SAME_TOL: g.append(i); break
            else: groups.append([i])
        for gi, g in enumerate(groups): SAME[tuple(key) + ("split", gi)] = g
    REP = {}
    for k, fs in SAME.items():
        r = max(fs, key=lambda i: D[i]["area"]); grp_plane = all(D[i]["plane_own"] for i in fs)
        for i in fs: REP[i] = r; D[i]["plane"] = grp_plane
    print("  same-surface groups MEASURED (SAME_TOL %.2f): %s" % (SAME_TOL, ("%d member(s) left their group - " % len(SAME_SPLIT)) + " ".join("f%d(%.2f off f%d)" % (i + 1, dv, r + 1) for i, r, dv in SAME_SPLIT[:40]) if SAME_SPLIT else "every member lies within it"), flush=True)
GAPLOG = []
if "gapw" in STATE: GAPW = set(STATE["gapw"])
else:
    if elapsed() > 100: save_state(); print("gap walls deferred - run again", flush=True); raise SystemExit(0)
    GAPW = gap_pairs()
    STATE["gapw"] = sorted(GAPW); save_state(); print("  (gap walls took %.0fs)" % elapsed(), flush=True)
    print("  gap pairs seen: " + "; ".join("f%d>f%d %d/%d" % (a + 1, b + 1, c, n) for a, b, c, n in GAPLOG if c >= 0.2 * n), flush=True)
print("  gap walls (never bounds): %s" % " ".join("f%d" % (i + 1) for i in sorted(GAPW)), flush=True)

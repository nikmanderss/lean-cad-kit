"""kitlib - the CAD helpers every template uses. Import ONLY under freecadcmd. Everything here is a primitive a
CAD engineer would use: sketch outlines on planes, extrude, connect two outlines with straight sides, revolve,
cylinders, boxes, fuse/cut with bookkeeping. Nothing experimental.
"""
import os, sys, time, math
import numpy as np
import Part
import FreeCAD as App
V = App.Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kitlib_render as R

class MeshShape(object):
    """an STL stood in for a shape (2026-09-25): `kit render <mesh.stl>` had always been in the usage line and had never
    worked - `load` fed the file to importBrep and the tessellator refused with ZERO triangles (found the moment a
    survey of the client's list was tried on the rework mesh). Carries V, T and a Volume; `tess` hands it back as is."""
    def __init__(self, path):
        V, T = R.read_stl(str(path))
        self.V = np.asarray(V, float); self.T = np.asarray(T, int); self.path = str(path)
        self.Volume = float(R.div_volume(self.V, self.T))
        self.Faces = []


def load(path):
    if not os.path.isfile(str(path)): raise FileNotFoundError("kitlib.load: no such file %s (the folder: %s) - a missing shape had read as 'ZERO triangles' or '[shape is invalid]' downstream (31bu, T8 F4)" % (path, os.getcwd()))
    if str(path).lower().endswith(".stl"):
        return MeshShape(path)
    s = Part.Shape(); s.importBrep(str(path)); return s
def save(shape, path):
    import os
    path = str(path); tmp = path + ".writing"
    shape.exportBrep(tmp)
    try:
        os.replace(tmp, path)
    except OSError:
        if os.path.exists(path) and os.stat(path).st_nlink > 1:
            os.remove(tmp)
            raise RuntimeError("save: %s is hard-linked (%d names) and cannot be replaced; write a new name" % (path, os.stat(path).st_nlink))
        shape.exportBrep(path); os.remove(tmp)
    return path
def tess(shape, dev=0.05):
    if isinstance(shape, MeshShape):
        return shape.V, shape.T, np.full(len(shape.T), -1, int)
    Vv, T, F = R.tess_shape(shape, dev); return Vv.astype(float), T, F
def volumes(shape, dev=0.05):
    Vv, T, _ = tess(shape, dev); return float(shape.Volume), float(R.div_volume(Vv, T))
def thickness_map(Vv, T, box, step=1.0, axis=2):
    """Material depth along `axis` over a grid on the other two axes.

    axis: 2 = rays down z (the original and the default), 1 = along y, 0 = along x.
    box: ((x0,x1),(y0,y1)) for the z case, or the full ((x0,x1),(y0,y1),(z0,z1)) for any axis.

    WHY THE AXIS ARGUMENT EXISTS. This cast z rays ONLY, and `kit check` used it as its
    punch-through test. So a hole bored straight down was caught and **a wall bored through
    SIDEWAYS was invisible** — a test orchestrator punched a 24 x 16 slot clean through an
    upstand on 2026-09-09 and the check reported `opened 0`. METHOD.md 5 promises "no new opening
    where the card said no punch-through"; that promise held for vertical holes and nothing else.

    Implemented by ROTATING THE GEOMETRY rather than writing three ray casters: swap the axis of
    interest into z, reuse the one caster that is already trusted, and the answer means the same
    thing on every axis. One instrument, three uses — the alternative is three instruments that
    will disagree with each other eventually.
    """
    Vv = np.asarray(Vv, float)
    if axis == 2:
        Vr, bx = Vv, box
    else:
        order = {0: (1, 2, 0), 1: (2, 0, 1)}[axis]
        Vr = Vv[:, list(order)]
        b3 = box if len(box) == 3 else (box[0], box[1], (Vv[:, 2].min(), Vv[:, 2].max()))
        bx = (b3[order[0]], b3[order[1]])
    if len(bx) == 3:
        bx = (bx[0], bx[1])
    Z = R.ZRays(Vr, T, 2.0)
    xs = np.arange(bx[0][0], bx[0][1] + 1e-6, step); ys = np.arange(bx[1][0], bx[1][1] + 1e-6, step)
    H = np.zeros((len(ys), len(xs)), np.float32)
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            z, _ = Z.hits(x + 0.013, y + 0.007); z = np.sort(z)
            if len(z) >= 2:
                z = z[:len(z) // 2 * 2]; H[j, i] = (z[1::2] - z[0::2]).sum()
    return xs, ys, H
def bop_ok(shape):
    try:
        shape.check(True); return True, ""
    except Exception as e:
        lines = sorted(set(l.strip() for l in str(e).split("\n")[1:] if l.strip()))
        return False, " | ".join(lines)[:300]
def fail(msg):
    """Stop the script with a message that SURVIVES freecadcmd. A bare `raise SystemExit(text)`
    exits 1 and prints NOTHING there (FreeCAD turns SystemExit into its own exception and drops
    the text): the first burrito probe died with an empty log that way (R18 2026-09-10 13:12)."""
    print("FAIL: " + str(msg), flush=True)
    raise SystemExit(1)


# recorded
# translated
# METHOD.md
class _Need(object):
    """The value of a slot nobody has filled. False in a boolean test, so a template that reads one
    before `need()` runs takes the empty branch rather than doing arithmetic on it."""
    __slots__ = ()

    def __repr__(self):
        return "<from the card>"

    def __bool__(self):
        return False
    __nonzero__ = __bool__


NEED = _Need()


def need(P):
    """Refuse, naming EVERY unfilled slot at once. One pass, not one refusal per run.

    Nested dicts, lists and tuples are walked, so `find=dict(normal=K.NEED)` is found and named as
    `find.normal`. Call it immediately after `P = PARAMS`, before anything reads a value.
    """
    miss = []

    def walk(node, path):
        if isinstance(node, dict):
            items = node.items()
        elif isinstance(node, (list, tuple)):
            items = enumerate(node)
        else:
            return
        for k, v in items:
            here = ("%s.%s" % (path, k)) if path else str(k)
            if isinstance(v, _Need):
                miss.append(here)
            else:
                walk(v, here)

    walk(P, "")
    if miss:
        fail("PARAMS is not filled - %d slot(s) still belong to the card:\n       %s\n"
             "  Every one of these is a number the CARD owns. Do not invent one: if it is not on\n"
             "  your card, write the question in RESULT.md and stop (CONTRACT.md)."
             % (len(miss), "\n       ".join(miss)))

def sig(path):
    """Content hash of a file, 16 hex. Missing file -> ''."""
    import hashlib
    try:
        with open(str(path), "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()[:16]
    except Exception:
        return ""
def card_sig(d):
    """Signature of the numbers a verdict was given about. Pass only the entries that CHANGE THE
    SHAPE - not output paths, not tolerances that cannot move a surface. Over-signing makes every
    verdict stale on a cosmetic edit and trains agents to re-review without looking."""
    import hashlib, json as _json
    return hashlib.sha256(_json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:16]
def _verdict_file(out_dir, step):
    return os.path.join(str(out_dir), "verdict_%s.json" % str(step))
def verdict_read(out_dir, step):
    import json as _json
    try:
        with open(_verdict_file(out_dir, step), encoding="utf-8") as fh:
            d = _json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}
def verdict_write(out_dir, step, artefact, cardsig, who, saw, call="pass"):
    """Record that `who` opened the pictures of `artefact` and what they saw. `kit verdict` calls
    this; a job never calls it about its own output."""
    import json as _json
    d = {"verdict": str(call).strip().lower(), "by": str(who), "when": time.strftime("%Y-%m-%d %H:%M:%S"),
         "saw": str(saw), "artefact": str(artefact), "artefact_sig": sig(artefact), "card": str(cardsig)}
    p = _verdict_file(out_dir, step)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        _json.dump(d, fh, indent=1)
    return d
def verdict_require(out_dir, step, artefact, cardsig, what, how):
    """Refuse unless a PASS verdict on disk is about THIS artefact and THIS card, and was given
    AFTER the artefact was written. `what` names the thing in the refusal; `how` is the one command
    that produces the pictures. Returns the verdict."""
    v = verdict_read(out_dir, step)
    if not v:
        fail("%s REFUSED - no recorded orbit verdict for %s.\n"
             "  the client's ruling stands: the orbit is the acceptance and the numbers are indicators.\n"
             "  L2: the piece with the best numbers of six was a solid brick.\n"
             "  Do this, in this order:\n"
             "    1. %s\n"
             "    2. OPEN EVERY FRAME. Not the contact sheet - the frames.\n"
             "    3. kit verdict %s --artefact \"%s\"%s --pass|--fail --by <you> --saw \"<one line per frame>\"\n"
             "  There is no skip hatch and asking for one is not a route." % (what, what, how, step, artefact, (" --card %s" % cardsig) if cardsig else ""))
    now = sig(artefact)
    if not now:
        fail("%s REFUSED - %s does not exist, so no verdict can be about it." % (what, artefact))
    if v.get("artefact_sig") and v["artefact_sig"] != now:
        fail("%s REFUSED - the verdict for %s is STALE: %s has changed since it was given.\n"
             "  A verdict records that somebody looked at a PARTICULAR shape. This is a different one.\n"
             "  Re-render and give a new verdict: %s" % (what, step, artefact, how))
    if (v.get("verdict") or "").strip().lower() != "pass":
        fail("%s REFUSED - the recorded verdict for %s is %r, not pass.\n"
             "  Fix what you saw, rebuild, look again. Do not re-run hoping for a different gate."
             % (what, step, v.get("verdict")))
    # recorded
    if cardsig and not v.get("card"):
        fail("%s REFUSED - the verdict for %s names NO card signature.\n"
             "  Then it is a verdict about a file, not about the numbers that produced it: the card\n"
             "  could change underneath it and this would still pass.\n"
             "  The job prints its signature. Record the verdict with it:\n"
             "      kit verdict %s --artefact \"%s\" --card %s --pass --by <you> --saw \"...\"\n"
             "  %s" % (what, step, step, artefact, cardsig, how))
    if v.get("card") and cardsig and v["card"] != cardsig:
        fail("%s REFUSED - the card has changed since the verdict for %s was given.\n"
             "  The numbers that decide the shape are not the ones that were looked at.\n"
             "      verdict card : %s\n"
             "      this card    : %s\n"
             "  Re-render and give a new verdict: %s" % (what, step, v["card"], cardsig, how))
    try:
        t_art = os.path.getmtime(str(artefact)); t_ver = os.path.getmtime(_verdict_file(out_dir, step))
        if t_art > t_ver + 1.0:
            fail("%s REFUSED - %s is NEWER than the verdict for %s (%.0f s newer).\n"
                 "  It was rebuilt after it was reviewed, so the verdict is about a shape that is no\n"
                 "  longer on disk. A matching hash is not enough on its own; this check is the one\n"
                 "  that needs no cooperation from any other job.\n"
                 "  Re-render and give a new verdict: %s" % (what, artefact, step, t_art - t_ver, how))
    except OSError:
        pass
    print("[gate] %s: verdict PASS for %s by %s (%s)" % (what, step, v.get("by") or "?", v.get("when") or "?"), flush=True)
    return v

def save_if_changed(shape, path):
    """31bu (TK2 F2): save the shape only when its bytes differ from the file on disk - a re-run that builds the SAME shape leaves the file's time alone, so a verdict given on it stands
    (verdict_require refuses an artefact newer than its verdict; t_cutter saved the cutter and the result on every run BEFORE their gates, so a gate could never pass: the cutter type had
    never reached a RESULT through kit run). Returns True when the file was written."""
    import os, hashlib
    path = str(path); tmp = path + ".writing"
    shape.exportBrep(tmp)
    try:
        if os.path.isfile(path):
            with open(tmp, "rb") as a_, open(path, "rb") as b_:
                _same = hashlib.md5(a_.read()).hexdigest() == hashlib.md5(b_.read()).hexdigest()
            if _same:
                os.remove(tmp); return False
    except OSError:
        pass
    try:
        os.replace(tmp, path)
    except OSError:
        shape.exportBrep(path)
        try: os.remove(tmp)
        except OSError: pass
    return True

_AX = {"+x": V(1, 0, 0), "-x": V(-1, 0, 0), "+y": V(0, 1, 0), "-y": V(0, -1, 0), "+z": V(0, 0, 1), "-z": V(0, 0, -1)}
def plane(origin, normal, udir):
    """a sketch plane: origin (x,y,z), normal ('+z' or a vector = the extrude direction for +depth), udir = the
    outline's local u axis ('+x' or a vector). Returns (O, N, U, W) unit vectors."""
    O = V(*origin); N = _AX[normal] if isinstance(normal, str) else V(*normal); N.normalize()
    U = _AX[udir] if isinstance(udir, str) else V(*udir); U = U - N * U.dot(N); U.normalize(); Wv = N.cross(U)
    return O, N, U, Wv
def to3d(pl, u, v):
    O, N, U, Wv = pl; return O + U * u + Wv * v

def rect(w, h, cx=0.0, cy=0.0):
    """rectangle outline in plane coordinates, centred at (cx,cy): list of (u,v)"""
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
def polygon(pts):
    return list(pts)

def wire_from_outline(pl, outline, radius=0.0):
    """closed wire from an outline (list of (u,v)) on plane pl; radius > 0 rounds every corner with a drawn arc
    (a rounded rectangle when the outline is a rectangle)."""
    P = [to3d(pl, u, v) for u, v in outline]; n = len(P)
    if radius <= 0:
        return Part.makePolygon(P + [P[0]])
    edges = []
    for i in range(n):
        p0, p1, p2 = P[i - 1], P[i], P[(i + 1) % n]
        d0 = (p0 - p1); d0.normalize(); d2 = (p2 - p1); d2.normalize()
        ang = math.acos(max(-1, min(1, d0.dot(d2)))); t = radius / math.tan(ang / 2)
        a = p1 + d0 * t; b = p1 + d2 * t
        bis = (d0 + d2); bis.normalize(); c = p1 + bis * (radius / math.sin(ang / 2))
        mid = c + (p1 - c) * ((radius) / (p1 - c).Length)
        edges.append(("pt", a, b, mid))
    wires = []
    for i in range(n):
        a_prev, b_prev, m_prev = edges[i - 1][1], edges[i - 1][2], edges[i - 1][3]
        a, b, m = edges[i][1], edges[i][2], edges[i][3]
        wires.append(Part.LineSegment(b_prev, a).toShape())
        wires.append(Part.Arc(a, m, b).toShape())
    return Part.Wire(Part.__sortEdges__(wires))

def circle_wire(pl, d, cu=0.0, cv=0.0):
    O, N, U, Wv = pl; c = to3d(pl, cu, cv)
    return Part.Wire(Part.Circle(c, N, d / 2.0).toShape())

def extrude(pl, wire, depth):
    """closed wire on plane pl -> solid, extruded by depth along the plane normal (negative = the other way)."""
    O, N, U, Wv = pl; f = Part.Face(wire); s = f.extrude(N * depth)
    if s.Volume < 0: s.reverse()
    return s
def connect(plA, outlineA, plB, outlineB, radius=0.0):
    """two outlines with the same vertex count -> solid with straight ruled sides + the two caps.
    radius > 0: both outlines get drawn corner arcs and the sides are ruled between matching edges."""
    if len(outlineA) != len(outlineB): fail("connect: the two outlines must have the same number of vertices")
    wa = wire_from_outline(plA, outlineA, radius); wb = wire_from_outline(plB, outlineB, radius)
    if len(wa.Edges) != len(wb.Edges): fail("connect: the two outlines have a different edge count after drawing (%d vs %d)" % (len(wa.Edges), len(wb.Edges)))
    sides = Part.makeRuledSurface(wa, wb)
    faces = list(sides.Faces) + [Part.Face(wa), Part.Face(wb)]
    sh = Part.makeShell(faces)
    if not sh.isClosed():
        fail("connect: the %d side faces and 2 caps do not close into a shell - check that the outlines are in the SAME vertex order (a reversed outline makes a twisted piece)" % len(sides.Faces))
    sol = Part.makeSolid(sh)
    if sol.Volume < 0: sol.reverse()
    ok, msg = bop_ok(sol)
    if not ok: fail("connect: the piece self-intersects (%s) - check vertex order / planes" % msg)
    n_pl = sum(1 for f in sides.Faces if f.Surface.__class__.__name__ == "Plane")
    print("CONNECT: %d side faces (%d planar, %d ruled) + 2 caps, %d vertices per outline, vol %.1f" % (len(sides.Faces), n_pl, len(sides.Faces) - n_pl, len(outlineA), sol.Volume), flush=True)
    return sol
def revolve(pl, wire, axis_point, axis_dir, angle=360.0):
    f = Part.Face(wire); s = f.revolve(V(*axis_point), V(*axis_dir), angle)
    if s.Volume < 0: s.reverse()
    return s
def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))
def cylinder(p0, axis, d, length):
    a = _AX[axis] if isinstance(axis, str) else V(*axis); a.normalize()
    return Part.makeCylinder(d / 2.0, length, V(*p0), a)
def mirror_x(shape): return shape.mirror(V(0, 0, 0), V(1, 0, 0))
def mirror_y(shape): return shape.mirror(V(0, 0, 0), V(0, 1, 0))
def translate(shape, dx, dy, dz):
    s = shape.copy(); s.translate(V(dx, dy, dz)); return s
def rotate(shape, axis, deg, about=(0.0, 0.0, 0.0)):
    """31br B5 (2026-10-30): the shape turned by deg about the axis through `about` - its LOCATION changes, as translate's does; the geometry is untouched"""
    s = shape.copy(); s.rotate(V(*about), V(*axis), float(deg)); return s
def place(shape, dx=0.0, dy=0.0, dz=0.0, rot_axis=(0.0, 0.0, 1.0), rot_deg=0.0, rot_about=(0.0, 0.0, 0.0)):
    """31br B5: rotate FIRST (about the point), then translate - FreeCAD's Placement order; the form t_move and kit place share"""
    s = rotate(shape, rot_axis, rot_deg, rot_about) if float(rot_deg) else shape.copy()
    s.translate(V(dx, dy, dz)); return s

def fuse(body, adds, label="", keep_all=None):
    """keep_all (31bw B4): None = by the base - a COMPOUND base (several solids) keeps every solid of the result, a one-solid base keeps the largest (an edit never makes a second
    body); True keeps every solid whatever the base (a pattern's disjoint copies); False keeps the largest."""
    t = time.time(); v0 = body.Volume; n0 = len(body.Solids)
    res = body.fuse(adds if isinstance(adds, list) else [adds])
    return _after(res, v0, "fuse " + label, t, keep_all=(n0 > 1) if keep_all is None else bool(keep_all), n0=n0)
def cut(body, cutters, label="", keep_all=None):
    t = time.time(); v0 = body.Volume; n0 = len(body.Solids); cl = cutters if isinstance(cutters, list) else [cutters]
    if n0 > 1:      # a compound is cut SOLID BY SOLID
        res = Part.makeCompound([x_ for s_ in body.Solids for x_ in s_.cut(cl).Solids])
    else:
        res = body.cut(cl)
    return _after(res, v0, "cut " + label, t, keep_all=(n0 > 1) if keep_all is None else bool(keep_all), n0=n0)
def _after(res, v0, label, t, keep_all=False, n0=1):
    """31bw B4 (the parts project's FAILURES 10-29 / 10-30: 'every kit boolean keeps only the largest solid of a multi-solid result' - a board compound lost its connector when its
    substrate was drilled, a pattern of 36 receptacles kept one): the largest-solid rule belongs to a ONE-solid base, where a second body is an edit's defect; a COMPOUND base keeps
    every solid of the result, the census said; a caller that makes several bodies on purpose (a pattern) says keep_all=True."""
    n = len(res.Solids)
    print("BOOKKEEPING %s: vol %.0f (%+.0f) valid %s solids %d faces %d  %.0fs" % (label, res.Volume, res.Volume - v0, res.isValid(), n, len(res.Faces), time.time() - t), flush=True)
    if n > 1 and keep_all:
        sv = sorted((s.Volume for s in res.Solids), reverse=True)
        print("   every solid KEPT (the base held %d solid(s); 31bw B4): %d in the result, the largest %.0f mm3, the smallest %.1f%s" % (n0, n, sv[0], sv[-1], (", %d under 1 mm3" % sum(1 for v_ in sv if v_ < 1.0)) if any(v_ < 1.0 for v_ in sv) else ""), flush=True)
        if n0 > 1 and n != n0: print("   the solid count changed %d -> %d (a cut that removes whole solids, or a fuse that joins touching ones - say which in the record)" % (n0, n), flush=True)
        return res
    if n > 1:
        for s_ in sorted(res.Solids, key=lambda s: -s.Volume)[1:6]:
            b = s_.BoundBox
            print("   dropped solid vol %.0f at x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f" % (s_.Volume, b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax), flush=True)
        res = max(res.Solids, key=lambda s: s.Volume)
        print("   -> ONE solid kept (the largest, %.0f mm3): THE FILE holds 1 solid - vol %.0f (%+.0f against the base), valid %s, faces %d; the BOOKKEEPING line above is the kernel's result BEFORE this rule, and the card's Expected is judged on the file (31bw)" % (res.Volume, res.Volume, res.Volume - v0, res.isValid(), len(res.Faces)), flush=True)
    return res
def region(body, bx, margin=0.0):
    (x0, x1), (y0, y1), (z0, z1) = bx
    return body.common(box(x0 - margin, x1 + margin, y0 - margin, y1 + margin, z0 - margin, z1 + margin))

STD_VIEWS = [("front-above-left", (-0.5, 0.7, -0.5)), ("rear-above-right", (0.55, -0.6, -0.55)), ("below-front", (-0.4, 0.6, 0.7)),
             ("side-right", (-1.0, 0.0, -0.15)), ("top", (0.0, 0.0, -1.0)), ("front", (0.0, 1.0, 0.0))]
ALL_VIEWS = STD_VIEWS + [("bottom", (0.0, 0.0, 1.0)), ("back", (0.0, -1.0, 0.0)), ("side-left", (1.0, 0.0, -0.15))]
def look(shape, out_dir, name, focus_box=None, views="std", W=1000, highlight=None, light=None, whole=True):
    """highlight: 1-based face numbers (the client's numbering) painted orange on the shaded frames — the
    R18 brief asked for "the three faces highlighted" and the kit had no way (friction log 09:42).
    light: None = the standard head-on light; "grazing" = low, from the side, so a flat flank shows
    its undulations instead of washing out (friction log 09:52, the two side elevations)."""
    os.makedirs(out_dir, exist_ok=True)
    Vv, T, F = tess(shape, 0.05); paths = []
    if focus_box is not None:
        (x0, x1), (y0, y1), (z0, z1) = focus_box
        # DIFFERENT
        foc = np.array([[x_, y_, z_] for x_ in (x0, x1) for y_ in (y0, y1) for z_ in (z0, z1)], float)
    else: foc = None
    vl = list(ALL_VIEWS if views == "all" else STD_VIEWS)
    if focus_box is not None:
        bx = Vv.min(0); bX = Vv.max(0); ext = np.maximum(bX - bx, 1e-6); bc = 0.5 * (bx + bX)
        fc = np.array([0.5 * (x0 + x1), 0.5 * (y0 + y1), 0.5 * (z0 + z1)])
        side_views = {(0, -1): ("side-left", (1.0, 0.0, -0.15)), (0, 1): ("side-right", (-1.0, 0.0, -0.15)),
                      (1, -1): ("front", (0.0, 1.0, 0.0)), (1, 1): ("back", (0.0, -1.0, 0.0)),
                      (2, -1): ("bottom", (0.0, 0.0, 1.0)), (2, 1): ("top", (0.0, 0.0, -1.0))}
        have = {lab for lab, _ in vl}
        for ax in range(3):
            off = (fc[ax] - bc[ax]) / ext[ax]
            if abs(off) > 0.25:
                lab, dv = side_views[(ax, -1 if off < 0 else 1)]
                if lab not in have:
                    vl.append((lab, dv)); have.add(lab)
    grey = np.tile(np.array([0.72, 0.74, 0.78]), (len(T), 1))
    if highlight:
        hl = np.isin(np.asarray(F), np.array([int(i) - 1 for i in highlight]))
        grey[hl] = (1.0, 0.45, 0.10)
        print("LOOK highlight: faces %s -> %d triangles painted orange%s"
              % (list(highlight), int(hl.sum()), "" if hl.any() else "  ** NONE FOUND: check the numbers (1-based) **"))
        if foc is None and hl.any():
            foc = Vv[np.unique(T[hl])]
    manifest = {}; rows = []
    _t0 = time.time()
    for k, (lab, dv) in enumerate(vl):
        d = np.array(dv, float); d /= np.linalg.norm(d)
        p = os.path.join(out_dir, "%s_%d_%s.png" % (name, k, lab))
        st = {}
        Tv = T
        if foc is not None:
            _d3, _r3, _u3 = R.basis(d)
            _fx = foc @ _r3; _fy = foc @ _u3
            _wx0, _wx1, _wy0, _wy1 = _fx.min() - 5.0, _fx.max() + 5.0, _fy.min() - 5.0, _fy.max() + 5.0
            _px = Vv @ _r3; _py = Vv @ _u3
            _tx = _px[T]; _ty = _py[T]
            _in = (_tx.max(1) >= _wx0) & (_tx.min(1) <= _wx1) & (_ty.max(1) >= _wy0) & (_ty.min(1) <= _wy1)
            Tv = T[_in]
        R.render(p, [("s", Vv, Tv, grey if Tv is T else grey[_in])], d, W=W, focus=foc, title="%s  view %s%s" % (name, lab, "  [grazing light]" if light == "grazing" else ""), light=light, subject_box=focus_box, stats=st)
        print("LOOK frame %d/%d %s  %d of %d triangles in the window  %.0f s" % (k + 1, len(vl), lab, len(Tv), len(T), time.time() - _t0), flush=True)
        if focus_box is None:
            paths.append(p); continue
        spx = int(st.get("subject_px", 0)); _dpx0 = int(st.get("drawn_px") or 0); dpx = max(1, _dpx0)
        sh = st.get("shows")
        ext = ("shows x %.0f..%.0f y %.0f..%.0f z %.0f..%.0f" % (sh[0][0], sh[1][0], sh[0][1], sh[1][1], sh[0][2], sh[1][2])) if sh else "shows nothing"
        manifest[os.path.basename(p)] = {"view": lab, "subject_px": spx, "drawn_px": _dpx0, "mmpx": st.get("mmpx"), "shows": sh, "box_px": st.get("box_px"), "box_drawn_px": st.get("box_drawn_px"), "occluded_px": st.get("occluded_px")}
        rows.append((p, lab, spx, dpx, ext))
    if rows:
        best = max(r[2] for r in rows) or 1
        for p, lab, spx, dpx, ext in rows:
            share = 100.0 * spx / best
            m = manifest[os.path.basename(p)]; m["of_best_pct"] = round(share, 1)
            if spx == 0 or share < 5.0:
                off = os.path.join(out_dir, "_offtarget"); os.makedirs(off, exist_ok=True)
                q = os.path.join(off, os.path.basename(p)); os.replace(p, q); m["moved_to"] = q
                _den = m.get("box_drawn_px") if m.get("box_drawn_px") is not None else m.get("box_px")
                if _den and (m.get("occluded_px") or 0) >= 0.5 * _den:
                    m["occluded"] = True
                    print("LOOK OCCLUDED %-26s the box lies behind the body's surface in this view (%d of %d of its drawn footprint covered) -> _offtarget\\ - reported, not a miss of the camera; the views that see it count  [%s]" % (os.path.basename(p), m["occluded_px"], _den, ext), flush=True)
                else:
                    print("LOOK MISS  %-28s subject %6d px = %4.1f%% of the best view -> _offtarget\\  [%s]" % (os.path.basename(p), spx, share, ext), flush=True)
                continue
            tag = "LOOK POOR " if share < 20.0 else "LOOK      "
            print("%s %-28s subject %6d px (%4.1f%% of drawn, %4.1f%% of the best view)  [%s]%s" % (tag, os.path.basename(p), spx, 100.0 * spx / dpx, share, ext, "  ** mostly hidden from this view **" if share < 20.0 else ""), flush=True)
            paths.append(p)
        import json as _json
        with open(os.path.join(out_dir, "%s_manifest.json" % name), "w", encoding="utf-8") as fh:
            _json.dump(manifest, fh, indent=1)
        miss = [k for k, v in manifest.items() if v.get("moved_to")]
        if miss:
            print("LOOK %d of %d views do not show the subject; they are in _offtarget\\ with their real extent in %s_manifest.json - reusable, not rubbish." % (len(miss), len(rows), name), flush=True)
    if whole:
        d = np.array(vl[0][1], float); d /= np.linalg.norm(d)
        p = os.path.join(out_dir, "%s_whole.png" % name); R.render(p, [("s", Vv, T, grey)], d, W=W, focus=None, title="%s  whole part" % name, light=light); paths.append(p)
    import colorsys
    nF = int(F.max()) + 1
    if nF <= 0:
        return paths
    hues = (np.arange(nF) * 0.61803) % 1.0
    C = np.array([colorsys.hsv_to_rgb(h, 0.55, 0.92) for h in hues])[F]
    d = np.array(vl[0][1], float); d /= np.linalg.norm(d)
    p = os.path.join(out_dir, "%s_rainbow.png" % name); R.render(p, [("s", Vv, T, C)], d, W=W, focus=foc, title="%s  one colour per face (%d faces)" % (name, nF)); paths.append(p)
    return paths


def say(*a):
    """Print, flushed. `print` alone loses its output when freecadcmd dies mid-step."""
    print(*[str(x) for x in a], flush=True)


def warn(msg):
    """A caution the card must carry into the run. It does NOT stop the script - a warn that stops
    is a fail wearing the wrong name, and CONTRACT rule 0 is about exactly that confusion."""
    for i, line in enumerate(str(msg).split("\n")):
        print(("WARN: " if i == 0 else "      ") + line, flush=True)


def frozen_or_fail(box, what="this box"):
    """Say which frozen regions `box` takes in. One line in a template. NO LONGER A REFUSAL (2026-09-22).

    the client: *"The vanes are locked but have to be allowed into edits. The point of them being frozen is they
    need to be recreated at the end of edits. The same would be true for any frozen sections that need
    to be included in a selection area."* So a selection BOX may include a frozen region; what may not
    happen is a LUMP chosen inside one - that fills a designed feature, and the recreation would undo it
    (`kit frozen check` on the lump still refuses). The rest of the old docstring stands:

    The registry lives with the PROJECT (`claude_code/FROZEN_REGIONS.json`) because the boxes are
    part-specific; the refusal lives here because the rule is not. Nothing measurable tells a
    construction gap from a designed aperture - a fill built over a flank slot array passed every
    gate in this kit and would have filled a designed vent array - so the answer is recorded once,
    by whoever knows the design, and enforced after.
    """
    import os as _os
    import sys as _sys
    _here = _os.path.dirname(_os.path.abspath(__file__))
    if _here not in _sys.path:
        _sys.path.insert(0, _here)
    try:
        import leangate as _G
    except Exception as _e:
        warn("frozen-region check unavailable (%s) - the box was NOT tested against the registry." % _e)
        return
    root = _os.environ.get("KIT_PROJECT") or _os.getcwd()
    for _ in range(4):
        if _os.path.isdir(_os.path.join(root, "claude_code")):
            break
        root = _os.path.dirname(root)
    hits = _G.frozen_hits(root, box)
    if hits:
        warn("%s takes in FROZEN region(s): %s. Allowed in a selection (the client, 2026-09-22) - choose NO lump\n"
             "  inside them (`kit frozen check <lump box>` refuses one); they are put back at the end of edits."
             % (what, ", ".join(h.get("name", "?") for h in hits)))


_NORMAL_FLIP = None
def _normal_calibrate():
    """Whether Face.normalAt on a 'Reversed' face already points OUTWARD (orientation-aware) - measured once per process on a 10 mm box whose outside is known, as
    kit measure's crease instrument measures it every run. The by-normal selectors (kit measure faces --normal, t_cutter's C1) had flipped every Reversed face BY HAND on
    top of it: on a valid box '+z' selected the top AND the bottom face and the cutter was drawn at the bottom (31bs T6 F2, R02)."""
    global _NORMAL_FLIP
    if _NORMAL_FLIP is not None: return _NORMAL_FLIP
    try:
        cal = Part.makeBox(10, 10, 10); cc = cal.CenterOfMass; flip = False
        for f in cal.Faces:
            if str(f.Orientation) == "Reversed":
                u, v = f.Surface.parameter(f.CenterOfMass); n = f.normalAt(u, v); n.normalize()
                flip = n.dot(f.CenterOfMass - cc) < 0; break
        _NORMAL_FLIP = bool(flip)
    except Exception:
        _NORMAL_FLIP = False
    return _NORMAL_FLIP


def outward_normal(f, u, v):
    """the face's OUTWARD unit normal at (u, v) as a FreeCAD Vector, or None - normalAt with the CALIBRATED flip for a Reversed face, never a hand flip on top of it (31bu)"""
    try:
        n = f.normalAt(u, v)
    except Exception:
        return None
    L = n.Length
    if L < 1e-12: return None
    n = n * (1.0 / L)
    if _normal_calibrate() and str(f.Orientation) == "Reversed": n = n * -1.0
    return n

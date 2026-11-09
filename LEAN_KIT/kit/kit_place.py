r"""kit_place.py - `kit place`: a body or a mesh PLACED (moved and turned) in the project's frame, recorded (31br B5, 2026-10-30).

the client, 2026-10-30, on a fixture project: "Initial CAD setup also needs better mapping to the agent for how to place and rotate parts. It couldn't
find that first go either." The agent's own review of every .py of the kit was right: `translate`, `mirror_x`, `mirror_y` were the kit's only moves -
nothing turned a brep or a mesh, `kit deliver` copied every template object's Placement verbatim, and the three PCBA-frame boards waited in their
export frame.

WHAT THE KERNEL DOES WITH A PLACEMENT ON RELOAD - measured first (a probe of four files, FreeCAD 1.1.3), because the two object
kinds differ and a guess here ships a part in the wrong place:
  Part::Feature : the .brp's OWN LOCATION wins. A Placement written in Document.xml over an identity brep is reset to identity on reload (P2 - the
                  kit's --target swap of a GUI-placed body LOSES the placement); a located brep under an identity XML Placement comes back placed (P3).
                  So a placed body is written BOTH ways, agreeing: the brep carries the location, the XML says the same (P4).
  Mesh::Feature : the XML Placement wins - it is applied ONCE to the kernel on reload (M2); the .bms stays unplaced. So a placed mesh is the mesh's
                  own kernel + the Placement property; a mesh FILE (.stl) carries no location - `kit place` on an .stl bakes the points.

THE PLACEMENT: rotate by `deg` about `axis` through the point `about` (the body's own origin unless given), THEN translate - FreeCAD's own order
(Placement(base, rotation, center)). A body that already carries a location keeps it: the new placement is composed ON TOP of it (pl * old).

  kit place <in.brep|in.stl> --out <out.brep|out.stl> [--translate dx dy dz] [--rotate "ax ay az deg"] [--about px py pz]
            [--why "<the frame this puts the part into>"] [--bake]
      the placed file written (a .brep carries the placement as its LOCATION; --bake writes it into the geometry, identity location; an .stl is
      always baked), the volume and the bounding boxes before / after printed, the placement RECORDED in claude_code\PLACEMENTS.json (keyed by
      the output's path under the project: from, translate, rotate, about, the Placement's base / axis / angle / quaternion, why, when).
  The same placement rides `kit deliver --add-body "...|place=dx,dy,dz,ax,ay,az,deg[,px,py,pz]"` and `--mesh "...|place=..."` (the JSON forms:
  "place": {"translate": [..], "rotate": [ax, ay, az, deg], "about": [..]}), and `t_move`'s rot_axis / rot_deg / rot_about PARAMS in a job.
"""
import os, sys, json, math, time

PLACEMENTS = os.path.join("claude_code", "PLACEMENTS.json")


# pure python
def _norm(v):
    n = math.sqrt(sum(float(x) * float(x) for x in v))
    if n < 1e-12:
        raise ValueError("the rotation axis is the zero vector")
    return tuple(float(x) / n for x in v)


def _rot(axis, deg, v):
    """v rotated by deg about the unit axis (Rodrigues)"""
    k = axis; t = math.radians(deg); c, s = math.cos(t), math.sin(t)
    kv = (k[1] * v[2] - k[2] * v[1], k[2] * v[0] - k[0] * v[2], k[0] * v[1] - k[1] * v[0])
    kd = k[0] * v[0] + k[1] * v[1] + k[2] * v[2]
    return tuple(v[i] * c + kv[i] * s + k[i] * kd * (1.0 - c) for i in range(3))


def placement(translate=(0, 0, 0), rotate=None, about=(0, 0, 0)):
    """the placement as numbers: {base, axis, angle_deg, q (x, y, z, w), translate, rotate, about}. rotate = (ax, ay, az, deg) or None."""
    t = tuple(float(x) for x in (translate or (0, 0, 0)))
    p = tuple(float(x) for x in (about or (0, 0, 0)))
    if len(t) != 3 or len(p) != 3:
        raise ValueError("--translate and --about take three numbers")
    if rotate is None or (len(rotate) == 4 and abs(float(rotate[3])) < 1e-12):
        axis, deg = (0.0, 0.0, 1.0), 0.0
    else:
        if len(rotate) != 4:
            raise ValueError("--rotate takes four numbers: ax ay az deg")
        axis, deg = _norm(rotate[:3]), float(rotate[3])
    rp = _rot(axis, deg, p)
    base = tuple(t[i] + p[i] - rp[i] for i in range(3))
    h = math.radians(deg) / 2.0; s = math.sin(h)
    q = (axis[0] * s, axis[1] * s, axis[2] * s, math.cos(h))
    return {"base": base, "axis": axis, "angle_deg": deg, "q": q, "translate": t, "rotate": (list(axis) + [deg]) if deg else None, "about": p}


def is_identity(pl, tol=1e-9):
    return all(abs(x) < tol for x in pl["base"]) and abs(pl["angle_deg"]) < tol


def xml_placement(pl):
    """the <PropertyPlacement .../> element FreeCAD writes (Px Py Pz, the quaternion Q0..Q3 = x y z w, the angle A in radians and its axis O)"""
    b, q, ax = pl["base"], pl["q"], pl["axis"]
    f = lambda x: "%.16f" % x
    return ('<PropertyPlacement Px="%s" Py="%s" Pz="%s" Q0="%s" Q1="%s" Q2="%s" Q3="%s" A="%s" Ox="%s" Oy="%s" Oz="%s"/>'
            % (f(b[0]), f(b[1]), f(b[2]), f(q[0]), f(q[1]), f(q[2]), f(q[3]), f(math.radians(pl["angle_deg"])), f(ax[0]), f(ax[1]), f(ax[2])))


IDENTITY_XML = xml_placement(placement())


def parse_xml_placement(txt):
    """the numbers of one <PropertyPlacement .../> element -> a placement dict (the quaternion read; A / O ignored), or None"""
    import re
    m = re.search(r'<PropertyPlacement\s+([^/]*)/>', txt or "")
    if not m:
        return None
    a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
    try:
        base = (float(a["Px"]), float(a["Py"]), float(a["Pz"]))
        q = (float(a["Q0"]), float(a["Q1"]), float(a["Q2"]), float(a["Q3"]))
    except (KeyError, ValueError):
        return None
    w = max(-1.0, min(1.0, q[3])); ang = 2.0 * math.degrees(math.acos(w)); s = math.sqrt(max(0.0, 1.0 - w * w))
    axis = (q[0] / s, q[1] / s, q[2] / s) if s > 1e-9 else (0.0, 0.0, 1.0)
    if ang > 180.0:
        ang -= 360.0
    return {"base": base, "axis": axis, "angle_deg": ang, "q": q, "translate": base, "rotate": (list(axis) + [ang]) if abs(ang) > 1e-9 else None, "about": (0.0, 0.0, 0.0)}


def parse_place_field(s):
    """`place=dx,dy,dz,ax,ay,az,deg[,px,py,pz]` (a --mesh / --add-body spec's last field) -> placement; a bad field raises ValueError by name"""
    s = (s or "").strip()
    if s.lower().startswith("place="):
        s = s[6:]
    try:
        v = [float(x) for x in s.split(",") if x.strip() != ""]
    except ValueError:
        raise ValueError("place= takes numbers: dx,dy,dz,ax,ay,az,deg[,px,py,pz] - got %r" % s)
    if len(v) == 3:
        return placement(v, None, (0, 0, 0))
    if len(v) == 7:
        return placement(v[:3], v[3:7], (0, 0, 0))
    if len(v) == 10:
        return placement(v[:3], v[3:7], v[7:10])
    raise ValueError("place= takes 3 (dx,dy,dz), 7 (+ ax,ay,az,deg) or 10 (+ px,py,pz) numbers - got %d in %r" % (len(v), s))


def parse_place_json(d):
    """{"translate": [..], "rotate": [ax, ay, az, deg], "about": [..]} -> placement (None / {} -> None)"""
    if not d:
        return None
    if not isinstance(d, dict):
        raise ValueError("\"place\" is an object {\"translate\": [dx, dy, dz], \"rotate\": [ax, ay, az, deg], \"about\": [px, py, pz]} - got %r" % (d,))
    return placement(d.get("translate") or (0, 0, 0), d.get("rotate"), d.get("about") or (0, 0, 0))


def describe(pl):
    if is_identity(pl):
        return "identity (no move, no turn)"
    s = "translate (%.3f, %.3f, %.3f)" % tuple(pl["translate"])
    if pl["angle_deg"]:
        s = "rotate %.2f deg about (%.3f, %.3f, %.3f)%s, then %s" % (pl["angle_deg"], pl["axis"][0], pl["axis"][1], pl["axis"][2],
                                                                    (" through (%.3f, %.3f, %.3f)" % tuple(pl["about"])) if any(pl["about"]) else "", s)
    return s + " -> Placement base (%.3f, %.3f, %.3f)" % tuple(pl["base"])


def _kernel():
    import FreeCAD as App
    src, out = os.environ["CC_PLACE_IN"], os.environ["CC_PLACE_OUT"]
    pl = json.loads(os.environ["CC_PLACE_PL"]); bake = os.environ.get("CC_PLACE_BAKE", "0") == "1"
    fpl = App.Placement(App.Vector(*pl["base"]), App.Rotation(App.Vector(*pl["axis"]), pl["angle_deg"]))
    t0 = time.time()
    if src.lower().endswith(".stl"):
        import Mesh
        m = Mesh.Mesh(src); bb0 = m.BoundBox; v0 = m.Volume if m.isSolid() else float("nan")
        m.transformGeometry(fpl.toMatrix()); bb = m.BoundBox
        m.write(out)
        print("PLACED mesh %s: %d facets, baked (a mesh file carries no location); bbox x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f  (was x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f)  %.0f s"
              % (os.path.basename(out), m.CountFacets, bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax, bb0.XMin, bb0.XMax, bb0.YMin, bb0.YMax, bb0.ZMin, bb0.ZMax, time.time() - t0), flush=True)
        print("RESULT " + json.dumps({"kind": "mesh", "facets": m.CountFacets, "bbox": [bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax], "bbox_before": [bb0.XMin, bb0.XMax, bb0.YMin, bb0.YMax, bb0.ZMin, bb0.ZMax], "baked": True}), flush=True)
        return 0
    import Part
    s = Part.Shape(); s.importBrep(src)
    bb0 = s.BoundBox; v0 = s.Volume; old = s.Placement
    if bake:
        if not old.isIdentity():
            s.Placement = App.Placement()
            s = s.transformGeometry(fpl.multiply(old).toMatrix())
        else:
            s = s.transformGeometry(fpl.toMatrix())
    else:
        s.Placement = fpl.multiply(old)
    bb = s.BoundBox; v1 = s.Volume
    tmp = out + ".writing"; s.exportBrep(tmp); os.replace(tmp, out)
    chk = Part.Shape(); chk.importBrep(out); cp = chk.Placement
    print("PLACED body %s: vol %.1f (was %.1f, %+.4f); %d solid(s) %d faces; Placement base (%.3f, %.3f, %.3f) axis (%.3f, %.3f, %.3f) angle %.2f deg%s%s; bbox x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f  (was x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f)  %.0f s"
          % (os.path.basename(out), v1, v0, v1 - v0, len(s.Solids), len(s.Faces), cp.Base.x, cp.Base.y, cp.Base.z, cp.Rotation.Axis.x, cp.Rotation.Axis.y, cp.Rotation.Axis.z, math.degrees(cp.Rotation.Angle),
             " (baked into the geometry)" if bake else " (the brep's location)", "" if old.isIdentity() else " - composed on the file's own location", bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax, bb0.XMin, bb0.XMax, bb0.YMin, bb0.YMax, bb0.ZMin, bb0.ZMax, time.time() - t0), flush=True)
    print("RESULT " + json.dumps({"kind": "body", "volume": v1, "volume_before": v0, "solids": len(s.Solids), "faces": len(s.Faces), "valid": bool(s.isValid()),
                                  "bbox": [bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax], "bbox_before": [bb0.XMin, bb0.XMax, bb0.YMin, bb0.YMax, bb0.ZMin, bb0.ZMax],
                                  "location_before": None if old.isIdentity() else [old.Base.x, old.Base.y, old.Base.z, old.Rotation.Axis.x, old.Rotation.Axis.y, old.Rotation.Axis.z, math.degrees(old.Rotation.Angle)],
                                  "placement_in_file": [cp.Base.x, cp.Base.y, cp.Base.z, cp.Rotation.Axis.x, cp.Rotation.Axis.y, cp.Rotation.Axis.z, math.degrees(cp.Rotation.Angle)], "baked": bake}), flush=True)
    return 0


def run_kernel(kit, src, out, pl, bake=False, log=None, cap=900):
    """the kernel step from a kit command: (rc, the RESULT dict or None). `kit` is the kit module (sh, freecad)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("LK_")}
    env.update({"CC_PLACE_IN": src, "CC_PLACE_OUT": out, "CC_PLACE_PL": json.dumps(pl), "CC_PLACE_BAKE": "1" if bake else "0",
                "KIT_HOME": os.path.dirname(os.path.abspath(__file__)), "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    rc, txt = kit.sh([kit.freecad(), os.path.abspath(__file__)], cap, log=log, env=env, cwd=os.path.dirname(os.path.abspath(out)) or None, outputs=(out,))
    res = None
    for ln in (txt or "").splitlines():
        if ln.startswith("RESULT "):
            try: res = json.loads(ln[7:])
            except ValueError: res = None
    if rc != 0 or not os.path.isfile(out):
        return (rc or 2), res
    return 0, res


LOCK_WAIT_S = 30.0
LOCK_STALE_S = 60.0


class _Lock(object):
    """31bs K26 (2026-11-03): one writer at a time on PLACEMENTS.json - a lock FILE beside it (O_CREAT | O_EXCL is atomic on NTFS and POSIX alike), waited for up to
    LOCK_WAIT_S, a lock older than LOCK_STALE_S taken over (its owner is dead). The second project agent measured six agents placing at once: a read under another process's
    write came back invalid, record() started from an EMPTY map and one write replaced the whole frame map with one entry."""
    def __init__(self, path):
        self.path = path + ".lock"; self.fd = None; self.took_over = False
    def __enter__(self):
        t0 = time.time()
        while True:
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, ("%d %s" % (os.getpid(), time.strftime("%Y-%m-%d %H:%M:%S"))).encode("utf-8"))
                return self
            except (FileExistsError, PermissionError):
                try:
                    if time.time() - os.path.getmtime(self.path) > LOCK_STALE_S:
                        os.remove(self.path); self.took_over = True; continue
                except OSError:
                    pass
                if time.time() - t0 > LOCK_WAIT_S:
                    raise OSError("the frame map is locked by another writer (%s, %.0f s) - the placement is NOT recorded; run kit place again" % (self.path, time.time() - t0))
                time.sleep(0.05)
    def __exit__(self, *a):
        try:
            if self.fd is not None: os.close(self.fd)
        finally:
            try: os.remove(self.path)
            except OSError: pass
        return False


def _read_map(p):
    """the frame map on disk, or {} when there is none; an EXISTING file that is not a JSON object is REFUSED (never an empty map written over it) - 31bs K26"""
    if not os.path.isfile(p):
        return {}
    try:
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError) as e:
        raise OSError("%s does not read as JSON (%s: %s) - the frame map is NOT overwritten; fix or move the file (its .tmp.* neighbours hold the last writers' copies)" % (p, type(e).__name__, str(e)[:80]))
    if not isinstance(d, dict):
        raise OSError("%s is not a JSON object - the frame map is NOT overwritten" % p)
    return d


def record(root, out, entry):
    """claude_code\\PLACEMENTS.json under the records root: {<out path relative to the project>: entry} - the project's frame map, one row per placed file.
    31bs K26: under a lock, read and re-written through a per-process temporary name; an unreadable existing map refuses the write (OSError, said by the caller)."""
    import leangate as _LG
    rr = _LG.records_root(root)
    p = os.path.join(rr, PLACEMENTS)
    try:
        key = os.path.relpath(os.path.abspath(out), os.path.abspath(root)).replace("\\", "/")
    except ValueError:
        key = os.path.abspath(out).replace("\\", "/")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with _Lock(p) as lk:
        d = _read_map(p)
        d[key] = entry
        tmp = "%s.tmp.%d" % (p, os.getpid())
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=1)
        for _try in range(40):
            try:
                os.replace(tmp, p); break
            except OSError:
                if _try == 39:
                    try: os.remove(tmp)
                    except OSError: pass
                    raise
                time.sleep(0.05)
        if lk.took_over:
            print("kit place: a stale lock on the frame map (over %.0f s old, its writer gone) was taken over" % LOCK_STALE_S)
    return p, key


def cmd(args, kit):
    r"""kit place <in.brep|in.stl> --out <out.brep|out.stl> [--translate dx dy dz] [--rotate "ax ay az deg"] [--about px py pz]
              [--why "<the frame this puts the part into>"] [--bake]

    THE PLACEMENT (31br B5): rotate by deg about the axis through `about` (the file's origin unless given), THEN translate - FreeCAD's own
    order. A .brep is written with the placement as its LOCATION (what FreeCAD reads back as the object's Placement; `--bake` writes it into
    the geometry instead - identity location); an .stl is always baked (a mesh file carries no location). A file that already carries a
    location keeps it - the new placement is composed on top. The volume never changes; the bounding boxes before and after are printed.
    RECORDED in claude_code\PLACEMENTS.json (the project's frame map): from, translate, rotate, about, the Placement, why, when.
    A placed brep is delivered as it is (`kit deliver --add-body "name|label|<out.brep>|1|r,g,b|group"`); a placement may also ride the
    spec itself (`|place=dx,dy,dz,ax,ay,az,deg`) and `t_move`'s rot_axis / rot_deg / rot_about PARAMS in a job.
    """
    if not args or args[0].startswith("-"):
        print(cmd.__doc__); return 2
    src = args[0]
    if not os.path.isfile(src):
        print("kit place: no such file %s" % src); return 2
    ext = os.path.splitext(src)[1].lower()
    if ext not in (".brep", ".stl"):
        print("kit place: the input is a .brep or an .stl (got %s) - a STEP / FCStd source is exported to brep first (ask the client; the kit reads brep and stl)" % ext); return 2
    out = kit._opt(args, "--out", "")
    if not out:
        print("kit place: --out <the placed file> is required (never the input itself - the frame map records where each copy came from)"); return 2
    if os.path.splitext(out)[1].lower() != ext:
        print("kit place: --out keeps the input's kind (%s in, %s out)" % (ext, os.path.splitext(out)[1].lower())); return 2
    if os.path.abspath(out).lower() == os.path.abspath(src).lower():
        print("kit place: --out is the input itself - write the placed copy beside it"); return 2
    def _three(flag):
        """the three numbers after `flag` (`--translate -44.15 65.14 96.20`: a negative number is a value, never an option)"""
        if flag not in args:
            return [0.0, 0.0, 0.0]
        i = args.index(flag); vals = args[i + 1:i + 4]
        if len(vals) != 3:
            raise ValueError("%s takes three numbers (dx dy dz), got %r" % (flag, vals))
        try:
            return [float(x) for x in vals]
        except ValueError:
            raise ValueError("%s takes three numbers (dx dy dz), got %r" % (flag, vals))
    try:
        tr = _three("--translate"); ab = _three("--about")
        rot = None
        if "--rotate" in args:
            rv = kit._opt(args, "--rotate", "")
            parts = [float(x) for x in rv.replace(",", " ").split()]
            if len(parts) != 4:
                print("kit place: --rotate takes \"ax ay az deg\" (four numbers in one quoted argument), got %r" % rv); return 2
            rot = parts
        pl = placement(tr, rot, ab)
    except ValueError as e:
        print("kit place: %s" % e); return 2
    if is_identity(pl):
        print("kit place: nothing to do - no --translate and no --rotate (or a 0 deg turn). Give the move."); return 2
    why = (kit._opt(args, "--why", "") or "").strip()
    bake = kit._flag(args, "--bake") or ext == ".stl"
    print("kit place: %s -> %s\n  placement: %s\n  written as: %s%s" % (src, out, describe(pl), "the geometry itself (baked, identity location)" if bake else "the brep's LOCATION (FreeCAD reads it back as the object's Placement)",
                                                                       ("\n  why      : " + why) if why else "\n  why      : (none given - say the frame this puts the part into with --why; the frame map records it)"))
    log = os.path.splitext(os.path.abspath(out))[0] + ".place_log.txt"
    t0 = time.time()
    rc, res = run_kernel(kit, os.path.abspath(src), os.path.abspath(out), pl, bake=bake, log=log, cap=900)
    if rc != 0:
        print("kit place: the kernel step FAILED (rc %s) - %s; nothing recorded" % (rc, log)); return 2
    if res and res.get("kind") == "body" and abs(float(res.get("volume", 0)) - float(res.get("volume_before", 0))) > 1e-6 * max(1.0, abs(float(res.get("volume_before", 0)))):
        print("kit place: the VOLUME CHANGED (%.3f -> %.3f) - a placement moves, it never reshapes; the output stands for your look but is NOT recorded" % (res.get("volume_before"), res.get("volume"))); return 2
    entry = {"from": os.path.abspath(src), "translate": list(pl["translate"]), "rotate": pl["rotate"], "about": list(pl["about"]),
             "placement": {"base": list(pl["base"]), "axis": list(pl["axis"]), "angle_deg": pl["angle_deg"], "quaternion_xyzw": list(pl["q"])},
             "baked": bake, "why": why, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "result": res, "seconds": round(time.time() - t0, 1)}
    try: entry["md5"] = __import__("hashlib").md5(open(os.path.abspath(out), "rb").read()).hexdigest()
    except OSError: pass
    try:
        p, key = record(kit.ROOT, out, entry)
        print("kit place: RECORDED %s -> %s" % (key, p))
    except OSError as e:
        print("kit place: the placement was NOT recorded (%s) - the file stands, the frame map does not know it" % e); return 2
    print("kit place: DONE in %.0f s. Deliver it: kit deliver <REV> --template <FCStd> --add-body \"<name>|<label>|%s|1|r,g,b|<group>\" (the brep's location is its placement)" % (time.time() - t0, out))
    return 0


if os.environ.get("CC_PLACE_IN") and os.environ.get("CC_PLACE_OUT"):
    sys.exit(_kernel())

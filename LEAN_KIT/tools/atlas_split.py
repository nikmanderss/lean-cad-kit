# KIT INSTRUMENT `atlas_split` - cut a body's SKIN into named regions for the atlas: faces that cross a region
# boundary are CUT on it, every piece is kept somewhere, and the area must add back up to the body's.
# Run: kit tool atlas_split --job <JOB> --set ATLAS_SHAPE=<body.brep> --set ATLAS_REGIONS=<spec.json> ...
# Inputs: ATLAS_SHAPE (the body brep)  ATLAS_REGIONS (the region spec, below)  ATLAS_OUTDIR (default: the job folder)
#         ATLAS_CACHE (per-face tessellation npz V/T/FID; built and kept if absent)  ATLAS_DEV (0.05)
#         ATLAS_RADIAL "x y" (the axis the in/out surface tests measure from; only needed if a region uses them)
# What is generic about it, and why each part is there:
#
# * A FACE IS NOT A REGION. On a real body a few long faces carry half the surface (155 of 4,765 faces spanned
#   more than 100 mm and held 51 % of the area), so "the faces whose centroid is in box B" is wrong for half the
#   part. Ownership is decided per TRIANGLE (a triangle is small enough not to span a boundary), and a face
#   whose triangles land in more than one region is CUT against the regions' boxes, most specific first.
# * NOTHING IS DROPPED. A region set that does not tile space drops whatever falls between its boxes - 15 % of
#   one body's surface, once, and nothing said so. So the LAST region is a catch-all (one is appended if the
#   spec does not end in one), and the run REFUSES unless assigned + discarded-sliver area = the body's area and
#   every original face contributes a piece.
# * THE SPEC. {name: {"rgb": [r,g,b], "boxes": [[x0,x1,y0,y1,z0,z1], ...], "faces": [body face numbers, 1-based],
#   "surface": up|down|flat|upish|downish|lowest|in|out, "minarea": mm2, "maxarea": mm2, "note": "..."}},
#   most specific FIRST. A region may be a box list, a face list, or both. "catch_all": true marks the last one.
# * THE OUTPUT. One brep compound per region, manifest.json (pieces, area, the body face each piece came from),
#   facemap.json ({region: {piece number: body face}} - what `kit atlas faces --facemap` reads to turn a pick on
#   the map back into a body face), triowner.npz (per-triangle ownership, for a render that shows the predicates),
#   status_atlas_split.json.
import os, sys, json, time
import numpy as np
sys.path.insert(0, os.environ["KIT_HOME"])
import kitlib as K
import FreeCAD as App
import Part


def say(*a):
    print(*a, flush=True)


T0 = time.time()
SHAPE = os.environ["ATLAS_SHAPE"]
SPEC = os.environ["ATLAS_REGIONS"]
D = os.environ.get("ATLAS_OUTDIR") or os.getcwd()
os.makedirs(D, exist_ok=True)
FLOOR = 0.05
sh = Part.Shape()
sh.importBrep(SHAPE)
faces = sh.Faces
NF = len(faces)
say("body: %d faces" % NF)

_cache = os.environ.get("ATLAS_CACHE") or os.path.join(D, "tess_cache.npz")
if os.path.exists(_cache):
    z = np.load(_cache)
    V, T, FID = z["V"], z["T"], z["FID"]
    say("tessellation from %s" % _cache)
else:
    V, T, FID = K.tess(sh, float(os.environ.get("ATLAS_DEV", "0.05")))
    np.savez_compressed(_cache, V=V, T=T, FID=FID)
    say("tessellated and kept: %s" % _cache)
if int(FID.max()) + 1 != NF:
    say("REFUSED: the tessellation has %d faces and the body %d - a cache from another model" % (int(FID.max()) + 1, NF))
    raise SystemExit(2)
P = V[T]
tri_a = 0.5 * np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1)
tri_c = P.mean(1)
tri_n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
tri_n = tri_n / np.maximum(np.linalg.norm(tri_n, axis=1), 1e-12)[:, None]

REG = json.load(open(SPEC, encoding="utf-8"))
NAMES = list(REG.keys())
if not NAMES:
    say("REFUSED: the spec names no region"); raise SystemExit(2)
lo_, hi_ = P.reshape(-1, 3).min(0) - 1.0, P.reshape(-1, 3).max(0) + 1.0
_covers = any(b[0] <= lo_[0] and b[1] >= hi_[0] and b[2] <= lo_[1] and b[3] >= hi_[1] and b[4] <= lo_[2] and b[5] >= hi_[2]
              for b in REG[NAMES[-1]].get("boxes", []))
if _covers and not REG[NAMES[-1]].get("surface"):
    REG[NAMES[-1]]["catch_all"] = True
if not REG[NAMES[-1]].get("catch_all"):
    REG["_REMAINDER"] = {"rgb": [205, 205, 210], "boxes": [[lo_[0], hi_[0], lo_[1], hi_[1], lo_[2], hi_[2]]],
                         "catch_all": True, "note": "surface no named region claimed"}
    NAMES.append("_REMAINDER")
    say("the spec does not end in a catch-all - `_REMAINDER` appended, so nothing can be dropped")
LAST = NAMES[-1]
say("regions: %d" % len(NAMES))

RADIAL = [float(t) for t in os.environ.get("ATLAS_RADIAL", "").split()] if os.environ.get("ATLAS_RADIAL") else None
if any(REG[n].get("surface") in ("in", "out") for n in NAMES) and not RADIAL:
    say("REFUSED: a region uses the in/out surface test, which measures from an axis - set ATLAS_RADIAL \"x y\"")
    raise SystemExit(2)


def in_box(c, b):
    return ((c[:, 0] >= b[0]) & (c[:, 0] <= b[1]) & (c[:, 1] >= b[2]) & (c[:, 1] <= b[3])
            & (c[:, 2] >= b[4]) & (c[:, 2] <= b[5]))


owner = np.full(len(T), -1, np.int32)
if RADIAL:
    _r = np.stack([tri_c[:, 0] - RADIAL[0], tri_c[:, 1] - RADIAL[1]], 1)
    _r /= np.maximum(np.linalg.norm(_r, axis=1), 1e-12)[:, None]
    radial = tri_n[:, 0] * _r[:, 0] + tri_n[:, 1] * _r[:, 1]
else:
    radial = np.zeros(len(T))
LOWTOL = float(os.environ.get("ATLAS_LOWTOL", "2.5")); _g = float(os.environ.get("ATLAS_LOWCELL", "3.0"))
_ix = np.floor(tri_c[:, 0] / _g).astype(np.int64); _iy = np.floor(tri_c[:, 1] / _g).astype(np.int64)
_cell = (_ix - _ix.min()) * (int(_iy.max() - _iy.min()) + 2) + (_iy - _iy.min())
_lowest = np.full(int(_cell.max()) + 1, np.inf)
np.minimum.at(_lowest, _cell, tri_c[:, 2])
LOWEST = tri_c[:, 2] <= _lowest[_cell] + LOWTOL
SURF = {"in": radial < -0.25, "out": radial > 0.25, "down": tri_n[:, 2] < -0.70, "up": tri_n[:, 2] > 0.70,
        "flat": np.abs(tri_n[:, 2]) > 0.70, "lowest": LOWEST & (tri_n[:, 2] < -0.70),
        "downish": tri_n[:, 2] < -0.25, "upish": tri_n[:, 2] > 0.25}
_fa = np.zeros(NF); np.add.at(_fa, FID, tri_a)
for i, nm in enumerate(NAMES):
    spec = REG[nm]
    if spec.get("surface") and spec["surface"] not in SURF:
        say("REFUSED: region %s asks for surface %r; known: %s" % (nm, spec["surface"], ", ".join(sorted(SURF))))
        raise SystemExit(2)
    m = np.zeros(len(T), bool)
    if spec.get("faces"):
        m |= np.isin(FID, np.array(spec["faces"], int) - 1)
    for b in spec.get("boxes", []):
        m |= in_box(tri_c, b)
    if spec.get("surface"):
        m &= SURF[spec["surface"]]
    if spec.get("maxarea"):
        m &= _fa[FID] <= float(spec["maxarea"])
    if spec.get("minarea"):
        m &= _fa[FID] >= float(spec["minarea"])
    took = m & (owner == -1)
    owner[took] = i
    say("  %-30s %8d tri  %10.0f mm2" % (nm, int(took.sum()), tri_a[took].sum()))

share = np.zeros((NF, len(NAMES) + 1))
np.add.at(share, (FID, owner + 1), tri_a)
tot = share.sum(1)
best = share.argmax(1)
clean = (tot - share.max(1)) <= 0.5
say("faces wholly inside one region: %d of %d    faces that CROSS a boundary: %d" % (int(clean.sum()), NF, int((~clean).sum())))

BOXSOLID = {}


def boxes_of(nm):
    if nm not in BOXSOLID:
        BOXSOLID[nm] = [Part.makeBox(b[1] - b[0], b[3] - b[2], b[5] - b[4], App.Vector(b[0], b[2], b[4]))
                        for b in REG[nm].get("boxes", [])]
    return BOXSOLID[nm]


def surf_ok(want, g):
    try:
        u = g.Surface.parameter(g.CenterOfMass)
        nv = g.normalAt(u[0], u[1])
        cm = g.CenterOfMass
        rad = 0.0
        if RADIAL:
            rx, ry = cm.x - RADIAL[0], cm.y - RADIAL[1]
            rl = (rx * rx + ry * ry) ** 0.5 or 1.0
            rad = (nv.x * rx + nv.y * ry) / rl
        return {"in": rad < -0.25, "out": rad > 0.25, "down": nv.z < -0.70, "up": nv.z > 0.70,
                "flat": abs(nv.z) > 0.70, "lowest": nv.z < -0.70, "downish": nv.z < -0.25,
                "upish": nv.z > 0.25}[want]
    except Exception:
        return True


out = {nm: [] for nm in NAMES}
origin = {nm: [] for nm in NAMES}
ncut = nfail = nwhole = nfallback = 0
dropped = 0.0
for f in range(NF):
    if tot[f] <= 0:
        continue
    if clean[f]:
        nm = LAST if best[f] == 0 else NAMES[best[f] - 1]
        out[nm].append(faces[f]); origin[nm].append(f + 1); nwhole += 1
        continue
    cols = [c for c in np.argsort(-share[f]) if share[f][c] > 0.5 and c != 0]
    cols = [c for c in cols if REG[NAMES[c - 1]].get("boxes")] + [c for c in cols if not REG[NAMES[c - 1]].get("boxes")]
    cols = [c for c in cols if NAMES[c - 1] != LAST]
    rem = [faces[f]]
    _before = sum(len(v) for v in out.values())
    for c in cols:
        nm = NAMES[c - 1]
        if not rem:
            break
        bxs = boxes_of(nm)
        if not bxs:
            if (f + 1) in set(REG[nm].get("faces", [])):
                got = [g for g in rem if g.Area > FLOOR]
                dropped += sum(g.Area for g in rem if g.Area <= FLOOR)
                rem = []
                out[nm].extend(got); origin[nm].extend([f + 1] * len(got)); ncut += len(got)
            continue
        got, nxtrem = [], []
        for g in rem:
            for bx in bxs:
                try:
                    for h in g.common(bx).Faces:
                        if h.Area > FLOOR:
                            got.append(h)
                        else:
                            dropped += h.Area
                except Exception:
                    nfail += 1
            cur = [g]
            for bx in bxs:
                step = []
                for h in cur:
                    try:
                        for k in h.cut(bx).Faces:
                            if k.Area > FLOOR:
                                step.append(k)
                            else:
                                dropped += k.Area
                    except Exception:
                        step.append(h)
                cur = step
            nxtrem += cur
        rem = nxtrem
        spec = REG[nm]
        want, amax, amin = spec.get("surface"), spec.get("maxarea"), spec.get("minarea")
        if got and (want or amax or amin):
            keepg = []
            for gg in got:
                if (amax and faces[f].Area > float(amax)) or (amin and faces[f].Area < float(amin)) \
                        or (want and not surf_ok(want, gg)):
                    rem.append(gg)
                    continue
                keepg.append(gg)
            got = keepg
        out[nm].extend(got); origin[nm].extend([f + 1] * len(got)); ncut += len(got)
    for g in rem:                                   # no region
        if g.Area > FLOOR:
            out[LAST].append(g); origin[LAST].append(f + 1)
        else:
            dropped += g.Area
    if sum(len(v) for v in out.values()) == _before:
        nm = LAST if best[f] == 0 else NAMES[best[f] - 1]
        out[nm].append(faces[f]); origin[nm].append(f + 1); nfallback += 1

say("kept whole: %d faces    cut into: %d pieces    boolean failures: %d    placed whole after a failed cut: %d"
    % (nwhole, ncut, nfail, nfallback))
man, fmap = {}, {}
for nm, fs in out.items():
    if not fs:
        say("  %-30s EMPTY" % nm)
        continue
    p = os.path.join(D, "%s.brep" % nm)
    Part.Compound(fs).exportBrep(p)
    man[nm] = {"brep": p, "rgb": REG[nm].get("rgb", [205, 205, 210]), "pieces": len(fs),
               "area": float(sum(g.Area for g in fs)), "from_faces": origin[nm], "note": REG[nm].get("note", "")}
    fmap[nm] = {str(i + 1): int(fid) for i, fid in enumerate(origin[nm])}
    say("  %-30s %5d piece(s)  %10.0f mm2" % (nm, len(fs), man[nm]["area"]))
np.savez_compressed(os.path.join(D, "triowner.npz"), owner=owner, names=np.array(NAMES, dtype=object),
                    rgb=np.array([REG[n].get("rgb", [205, 205, 210]) for n in NAMES], int))
json.dump(man, open(os.path.join(D, "manifest.json"), "w", encoding="utf-8"), indent=1)
json.dump(fmap, open(os.path.join(D, "facemap.json"), "w", encoding="utf-8"), indent=1)

_seen = set()
for _ids in origin.values():
    _seen.update(_ids)
lost = [i + 1 for i in range(NF) if (i + 1) not in _seen and tot[i] > 0]
body = float(sum(g.Area for g in faces))
assigned = float(sum(v["area"] for v in man.values()))
gap = body - assigned - dropped
tolg = max(FLOOR * ncut, 1.0)
ok = (abs(gap) <= tolg) and not lost
say("")
say("AREA: body %.1f mm2 = assigned %.1f + slivers under %.2f mm2 %.1f  (unaccounted %.1f, allowed %.1f)"
    % (body, assigned, FLOOR, dropped, gap, tolg))
if lost:
    say("*** %d ORIGINAL FACE(S) CONTRIBUTED NOTHING: %s" % (len(lost), " ".join("Face%d" % i for i in lost[:40])))
json.dump({"state": "done" if ok else "REFUSED", "body_mm2": round(body, 1), "assigned_mm2": round(assigned, 1),
           "slivers_mm2": round(dropped, 2), "unaccounted_mm2": round(gap, 2), "lost_faces": lost[:200],
           "regions": len(man), "pieces_cut": ncut, "boolean_failures": nfail, "seconds": round(time.time() - T0, 1)},
          open(os.path.join(D, "status_atlas_split.json"), "w", encoding="utf-8"), indent=1)
say("%.0f s" % (time.time() - T0))
if not ok:
    say("REFUSED: the split does not account for the body's surface - a region set that loses surface is not a map.")
    raise SystemExit(2)
say("DONE - every face placed, area conserved")

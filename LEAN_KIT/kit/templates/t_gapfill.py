# t_gapfill - THE GAP FILL: the air between two neighbouring surfaces becomes material, touching every
# neighbour BY CONSTRUCTION. Fill PARAMS only.
#
# The method (proven on the R14 body through the direct FreeCAD route, 2026-09-11: the web under
# Face1569, then both skirt-to-part channels, 7,417 / 10,076 / 10,284 mm3, each 1 valid solid):
#   1. a SLAB box covers the gap and reaches INTO the neighbouring material on every side that must be
#      touched (the box's far walls sit inside walls, never in air, wherever contact is wanted);
#   2. the AIR in the slab is `slab.cut(body)`; it comes out as several pieces (the gap, the air outboard
#      of a wall, air above a web...); the fill is the piece that contains the PROBE point, a point you
#      know is in the gap - never chosen by bounding box (a B-spline body's boxes lie);
#   3. `body.fuse(fill)`: the fill's faces are the body's own faces where they meet, so there is nothing
#      to mismatch; the slab's own planar walls become the fill's free faces (its bottom, its ends).
# What it is for: a slit or channel between two parts of one body (skirt to part, web to wall), a
# flush floor between a ledge and a wall, a strengthening web. What it is NOT for: smoothing a surface
# (that is the burrito), or a fill whose free face must curve (make the slab's free wall follow the
# neighbour by choosing its plane; a curved free face needs a second construction).
# Rules it carries: the bottom/ends of the slab follow the NEIGHBOUR'S surface (the client: "all of those fixes
# do not follow a specific z"); frozen regions stay outside the slab; measure after: solids, valid,
# volume delta against the fill's own volume (the kernel's volume is +-1e-4 on this body: a 2 %
# discrepancy on a 7,000 mm3 fill is noise, a 20 % one is a lost piece).
import os, sys; sys.path.insert(0, os.environ.get("KIT_HOME", os.path.dirname(os.path.abspath(__file__)))); import kitlib as K, Part
from FreeCAD import Vector as V
PARAMS = dict(
    base=K.NEED,                      # ABSOLUTE path: the body (the model of record or a region.brep holding the whole slab + neighbours)
    slab=K.NEED,                      # x0 x1 y0 y1 z0 z1 of the slab: reaches INTO every wall to be touched; its free walls sit where the fill should end
    probe=K.NEED,                     # a point certainly inside the GAP (mid-gap, mid-height), OR a list of such points: every air piece holding one becomes part of the fill (a rib can divide the gap into pieces - the front pocket did, 2026-09-11, and a single probe at x 0 sat exactly on it)
    min_piece=K.NEED,                 # air pieces under this volume (mm3) are ignored when picking
    mouths=K.NEED,                    # the slab walls the fill MAY reach (its free faces): any of x0 x1 y0 y1 z0 z1, or "any" for the old behaviour. The fill touching any OTHER wall means the probe sat in air that is open to the outside there - the front-corner slabs of 2026-09-11 13:20 took two 3,780 mm3 blocks of EXTERIOR air standing proud of the skirt; a probe point cannot tell a pocket from the outdoors, the walls can
    fuse_fuzzy=K.NEED,                # fuzzy tolerance for the fuse; 0 = plain (plain sufficed three times)
    expect_fill=None,                 # optional: the fill volume you expect (mm3); the run FAILS if the air piece is off by more than 30 %
    out_dir=".",                      # ABSOLUTE job folder
    piece_name="fill_gap.brep",       # ABSOLUTE path: the fill alone (for looking at it)
    result_name="result.brep",        # ABSOLUTE path: the fused result
)
P = PARAMS
K.need(P)
body = K.load(P["base"])
v0 = body.Volume
x0, x1, y0, y1, z0, z1 = P["slab"]
slab = K.box(x0, x1, y0, y1, z0, z1)
air = slab.cut(body)
pieces = [s for s in air.Solids if s.Volume > float(P.get("min_piece", 5.0))]
print("GAPFILL air in the slab: %d piece(s) over %.0f mm3: %s" % (len(pieces), float(P.get("min_piece", 5.0)), [round(s.Volume) for s in pieces]), flush=True)
probes = P["probe"] if isinstance(P["probe"][0], (list, tuple)) else [P["probe"]]
probes = [V(*p) for p in probes]
hits = {i: [k for k, pr in enumerate(probes) if s.isInside(pr, 1e-6, True)] for i, s in enumerate(pieces)}
print("GAPFILL probe hits per piece: %s" % {i: v for i, v in hits.items()}, flush=True)
gap = [pieces[i] for i, v in hits.items() if v]
if not gap:
    K.fail("gapfill: no air piece contains any probe point - the probes are in material, or the slab does not reach the gap; move one of them")
fill = gap[0] if len(gap) == 1 else gap[0].fuse(gap[1:])
print("GAPFILL fill: %.1f mm3, %d faces, valid %s" % (fill.Volume, len(fill.Faces), fill.isValid()), flush=True)
mouths = P.get("mouths")
if mouths is None: K.fail("gapfill: PARAMS has no `mouths` - name the slab walls the fill may reach (a list of x0 x1 y0 y1 z0 z1), or 'any' on purpose (the exterior-air check off) (31bx R2 F2)")
if mouths != "any":
    # the fill may reach the slab only at its mouths. Tight box (optimalBoundingBox): the plain BoundBox of
    # a B-spline-faced piece is loose by millimetres and would touch every wall.
    ob = fill.optimalBoundingBox(True, False); eps = 0.05
    touched = [w for w, hit in (("x0", ob.XMin < x0 + eps), ("x1", ob.XMax > x1 - eps), ("y0", ob.YMin < y0 + eps),
                                ("y1", ob.YMax > y1 - eps), ("z0", ob.ZMin < z0 + eps), ("z1", ob.ZMax > z1 - eps)) if hit]
    print("GAPFILL the fill reaches the slab's walls %s; allowed mouths %s" % (touched, list(mouths)), flush=True)
    bad = [w for w in touched if w not in mouths]
    if bad:
        K.fail("gapfill: the fill reaches the slab wall(s) %s, which are not mouths - that air is open to the outside there (the "
               "slab pokes out of the body, or the probe sits in exterior air); shrink the slab to the neighbours or move the probe" % bad)
if P.get("expect_fill"):
    e = float(P["expect_fill"])
    if abs(fill.Volume - e) > 0.3 * e:
        K.fail("gapfill: the fill is %.0f mm3 against an expected %.0f - the slab or the probe picked the wrong air" % (fill.Volume, e))
K.save(fill, P["piece_name"])
fz = float(P.get("fuse_fuzzy", 0.0) or 0.0)
res = body.fuse([fill], fz) if fz > 0 else body.fuse(fill)
res = K._after(res, v0, "gapfill fuse", __import__("time").time(), keep_all=len(body.Solids) > 1, n0=len(body.Solids))      # 31bw B4: a compound base keeps its solids
print("GAPFILL result: %d solid(s), valid %s, faces %d (body %d), volume %+.1f against the fill's %.1f (%+.1f)"
      % (len(res.Solids), res.isValid(), len(res.Faces), len(body.Faces), res.Volume - v0, fill.Volume, res.Volume - v0 - fill.Volume), flush=True)
if (len(res.Solids) != 1 and len(body.Solids) == 1) or not res.isValid():      # 31bw B4
    K.fail("gapfill: the fuse did not give one valid solid - read the lines above; try fuse_fuzzy=0.02 once, then look at the fill alone")
K.save(res, P["result_name"])
print("GAPFILL saved %s" % P["result_name"], flush=True)

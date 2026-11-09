# t_sketch_extrude - a closed outline on a plane, extruded to a depth; ADD (fuse) or CUT. Fill PARAMS only.
import os, sys; sys.path.insert(0, os.environ.get("KIT_HOME", os.path.dirname(os.path.abspath(__file__)))); import kitlib as K
PARAMS = dict(
    # OUTPUT NAMES (31bs K4 / K20, 2026-11-03): a RELATIVE name lands in the JOB FOLDER - kit run runs this script there; an ABSOLUTE path is the safest (the card lint's ABS PATHS slot)
    base=K.NEED,                    # ABSOLUTE path to the body copy; "" builds the piece alone (the very first block)
    plane_origin=K.NEED,            # a point on the sketch plane (x, y, z) from the job card
    plane_normal=K.NEED,            # extrude direction for positive depth: '+x' '-x' '+y' '-y' '+z' '-z' or (nx, ny, nz)
    plane_udir=K.NEED,              # the outline's local u axis in space ('+x' etc. or a vector)
    outline=K.NEED,                 # 'rect' | 'circle' | 'polygon'
    rect_w=None, rect_h=None,       # for 'rect' (u-width, v-height), centred at (cu, cv); required only then
    circle_d=None,                  # for 'circle'; required only then
    polygon=None,                   # for 'polygon' - (u, v) points in order, closed automatically; required only then
    cu=K.NEED, cv=K.NEED,           # centre offset in plane coordinates
    corner_radius=K.NEED,           # > 0 rounds every corner of a rect/polygon with a drawn arc
    extra_rects=[],                 # optional more rectangles on the SAME plane, same depth/op: list of (w, h, cu, cv)
    extra_circles=[],               # optional more circles on the SAME plane: list of (d, cu, cv)
    depth=K.NEED,                   # extrude length along plane_normal (negative = opposite direction)
    op=K.NEED,                      # 'add' = fuse into base, 'cut' = cut from base, 'piece' = only bank the piece
    piece_name="piece_extrude.brep",
    result_name="result.brep",
)
P = PARAMS
K.need(P)
# THE THREE OUTLINE VARIANTS ARE MUTUALLY EXCLUSIVE, so only the chosen one is required. Marking
# all three K.NEED would refuse a rect card for not carrying a circle diameter - a check that
# breaks a correct edit, which is worse than no check (the client, 2026-09-16).
_want = {"rect": ("rect_w", "rect_h"), "circle": ("circle_d",), "polygon": ("polygon",)}
for _k in _want.get(P["outline"], ()):
    if P.get(_k) is None: K.fail("outline is %r, so PARAMS.%s is required and is empty." % (P["outline"], _k))
pl = K.plane(P["plane_origin"], P["plane_normal"], P["plane_udir"])
if P["outline"] == "rect": w = K.wire_from_outline(pl, K.rect(P["rect_w"], P["rect_h"], P["cu"], P["cv"]), P["corner_radius"])
elif P["outline"] == "circle": w = K.circle_wire(pl, P["circle_d"], P["cu"], P["cv"])
elif P["outline"] == "polygon": w = K.wire_from_outline(pl, [(u + P["cu"], v + P["cv"]) for u, v in P["polygon"]], P["corner_radius"])
else: K.fail("outline must be rect | circle | polygon")
piece = K.extrude(pl, w, P["depth"])
for (w2, h2, cu2, cv2) in P.get("extra_rects", []):
    piece = piece.fuse(K.extrude(pl, K.wire_from_outline(pl, K.rect(w2, h2, cu2, cv2), P["corner_radius"]), P["depth"]))
for (d2, cu2, cv2) in P.get("extra_circles", []):
    piece = piece.fuse(K.extrude(pl, K.circle_wire(pl, d2, cu2, cv2), P["depth"]))
ok, msg = K.bop_ok(piece)
if not ok: K.fail("piece self-intersects: " + msg)
b = piece.BoundBox
print("PIECE %s: vol %.0f faces %d bbox x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (P["piece_name"], piece.Volume, len(piece.Faces), b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax), flush=True)
K.save(piece, P["piece_name"])
if P["op"] == "piece" or not P["base"]:
    K.save(piece, P["result_name"]); print("BOOKKEEPING piece only: vol %.0f valid %s solids 1 faces %d" % (piece.Volume, piece.isValid(), len(piece.Faces)))
else:
    body = K.load(P["base"])
    body = K.fuse(body, piece, "extrude") if P["op"] == "add" else K.cut(body, piece, "extrude")
    K.save(body, P["result_name"]); print("RESULT -> %s" % P["result_name"])

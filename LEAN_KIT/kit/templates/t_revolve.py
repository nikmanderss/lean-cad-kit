# t_revolve - a closed outline in a plane that contains the axis, revolved about that axis; ADD / CUT / piece. Fill PARAMS only.
import os, sys; sys.path.insert(0, os.environ.get("KIT_HOME", os.path.dirname(os.path.abspath(__file__)))); import kitlib as K
PARAMS = dict(
    # OUTPUT NAMES (31bs K4 / K20, 2026-11-03): a RELATIVE name lands in the JOB FOLDER - kit run runs this script there; an ABSOLUTE path is the safest (the card lint's ABS PATHS slot)
    base=K.NEED,                       # ABSOLUTE path
    plane=dict(origin=K.NEED, normal=K.NEED, udir=K.NEED),        # the sketch plane; it must CONTAIN the axis
    outline=K.NEED,                    # (u, v) points in the sketch plane - u along udir, v along normal x udir (kitlib.plane: v is the direction the outline rises in; 31bx R1 D8); closed automatically; must not cross the axis
    axis_point=K.NEED,                 # a point on the revolve axis (3-D)
    axis_dir=K.NEED,                   # the axis direction (3-D)
    angle=K.NEED,
    op=K.NEED,                         # 'add' | 'cut' | 'piece'
    piece_name="piece_revolve.brep",
    result_name="result.brep",
)
P = PARAMS
K.need(P)
pl = K.plane(**P["plane"]); w = K.wire_from_outline(pl, P["outline"], 0.0)
piece = K.revolve(pl, w, P["axis_point"], P["axis_dir"], P["angle"])
ok, msg = K.bop_ok(piece)
if not ok: K.fail("piece self-intersects: " + msg)
b = piece.BoundBox
print("PIECE %s: vol %.0f faces %d bbox x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (P["piece_name"], piece.Volume, len(piece.Faces), b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax), flush=True)
K.save(piece, P["piece_name"])
if P["op"] == "piece" or not P["base"]:
    K.save(piece, P["result_name"]); print("BOOKKEEPING piece only: vol %.0f valid %s solids 1 faces %d" % (piece.Volume, piece.isValid(), len(piece.Faces)))
else:
    body = K.load(P["base"])
    body = K.fuse(body, piece, "revolve") if P["op"] == "add" else K.cut(body, piece, "revolve")
    K.save(body, P["result_name"]); print("RESULT -> %s" % P["result_name"])

# t_sketch_connect - two closed outlines on two planes joined by straight sides; ADD or CUT. Fill PARAMS only.
import os, sys; sys.path.insert(0, os.environ.get("KIT_HOME", os.path.dirname(os.path.abspath(__file__)))); import kitlib as K
PARAMS = dict(
    # OUTPUT NAMES (31bs K4 / K20, 2026-11-03): a RELATIVE name lands in the JOB FOLDER - kit run runs this script there; an ABSOLUTE path is the safest (the card lint's ABS PATHS slot)
    base=K.NEED,                                                   # ABSOLUTE path
    planeA=dict(origin=K.NEED, normal=K.NEED, udir=K.NEED),        # outline A lives here
    outlineA=K.NEED,                                               # (u, v) points, same count and order as outlineB
    planeB=dict(origin=K.NEED, normal=K.NEED, udir=K.NEED),
    outlineB=K.NEED,
    corner_radius=K.NEED,             # > 0 rounds every corner of BOTH outlines with drawn arcs (same radius)
    op=K.NEED,                        # 'add' | 'cut' | 'piece'
    piece_name="piece_connect.brep",
    result_name="result.brep",
)
P = PARAMS
K.need(P)
plA = K.plane(**P["planeA"]); plB = K.plane(**P["planeB"])
piece = K.connect(plA, P["outlineA"], plB, P["outlineB"], P.get("corner_radius", 0.0))
b = piece.BoundBox
print("PIECE %s: vol %.0f faces %d bbox x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (P["piece_name"], piece.Volume, len(piece.Faces), b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax), flush=True)
K.save(piece, P["piece_name"])
if P["op"] == "piece" or not P["base"]:
    K.save(piece, P["result_name"]); print("BOOKKEEPING piece only: vol %.0f valid %s solids 1 faces %d" % (piece.Volume, piece.isValid(), len(piece.Faces)))
else:
    body = K.load(P["base"])
    body = K.fuse(body, piece, "connect") if P["op"] == "add" else K.cut(body, piece, "connect")
    K.save(body, P["result_name"]); print("RESULT -> %s" % P["result_name"])

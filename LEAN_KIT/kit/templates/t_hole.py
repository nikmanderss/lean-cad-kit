# t_hole - a round bore (a counterbore when cbore_d > 0) from a start point along an axis, CUT. Fill PARAMS only.
import os, sys; sys.path.insert(0, os.environ.get("KIT_HOME", os.path.dirname(os.path.abspath(__file__)))); import kitlib as K
PARAMS = dict(
    # OUTPUT NAMES (31bs K4 / K20, 2026-11-03): a RELATIVE name lands in the JOB FOLDER - kit run runs this script there; an ABSOLUTE path is the safest (the card lint's ABS PATHS slot)
    base=K.NEED,                         # ABSOLUTE path
    holes=[                              # one entry per hole; all cut in one step
        dict(start=K.NEED,               # a point 2 mm OUTSIDE the face the hole enters (in air)
             axis=K.NEED,                # direction the hole goes into the material
             d=K.NEED,                   # bore diameter
             depth=K.NEED,               # length from start (so 2 mm air + 8 mm bore); for a through hole: past the far face + 2
             cbore_d=K.NEED, cbore_depth=K.NEED),  # the counterbore from the same start: cbore_d 0 and cbore_depth 0 = none (both REQUIRED, 0 is the answer - 31bx R1 D9)
    ],
    piece_name="piece_holes.brep",
    result_name="result.brep",
)
P = PARAMS
K.need(P)
cutters = []
for h in P["holes"]:
    c = K.cylinder(h["start"], h["axis"], h["d"], h["depth"]); cutters.append(c)
    if h.get("cbore_d", 0) > 0: cutters.append(K.cylinder(h["start"], h["axis"], h["cbore_d"], h["cbore_depth"]))
piece = cutters[0] if len(cutters) == 1 else cutters[0].fuse(cutters[1:])
K.save(piece, P["piece_name"])
print("PIECE %s: %d cylinders, vol %.0f" % (P["piece_name"], len(cutters), piece.Volume), flush=True)
body = K.load(P["base"]); body = K.cut(body, cutters, "holes"); K.save(body, P["result_name"]); print("RESULT -> %s" % P["result_name"])

# t_move - move a finished part by a fixed offset, and - 31br B5 (2026-10-30) - turn it first when the card says so. No shape change, only position. Fill PARAMS only.
import os, sys; sys.path.insert(0, os.environ.get("KIT_HOME", os.path.dirname(os.path.abspath(__file__)))); import kitlib as K
PARAMS = dict(
    # OUTPUT NAMES (31bs K4 / K20, 2026-11-03): a RELATIVE name lands in the JOB FOLDER - kit run runs this script there; an ABSOLUTE path is the safest (the card lint's ABS PATHS slot)
    base=K.NEED,                        # ABSOLUTE path to the part to move
    dx=K.NEED, dy=K.NEED, dz=K.NEED,    # the offset, mm. 0.0 is a legitimate answer; it is not a default
    rot_axis=(0.0, 0.0, 1.0),           # 31br B5: the turn's axis (ax, ay, az) ...
    rot_deg=0.0,                        # ... and its angle in degrees (0.0 = no turn); the turn comes FIRST, then the offset (FreeCAD's Placement order)
    rot_about=(0.0, 0.0, 0.0),          # ... through this point (the part's origin by default)
    result_name="result.brep",
)
P = PARAMS
K.need(P)
b = K.load(P["base"]); bb0 = b.BoundBox
r = K.place(b, P["dx"], P["dy"], P["dz"], P["rot_axis"], P["rot_deg"], P["rot_about"])
bb = r.BoundBox
print("PIECE %s: vol %.0f faces %d bbox x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (P["result_name"], r.Volume, len(r.Faces), bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax), flush=True)
print("BOOKKEEPING move: vol %.0f (%+.0f) valid %s solids %d faces %d   was x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f%s" % (
    r.Volume, r.Volume - b.Volume, r.isValid(), len(r.Solids), len(r.Faces), bb0.XMin, bb0.XMax, bb0.YMin, bb0.YMax, bb0.ZMin, bb0.ZMax,
    ("   turned %.2f deg about (%.3f, %.3f, %.3f) through (%.2f, %.2f, %.2f), then moved" % (P["rot_deg"], *P["rot_axis"], *P["rot_about"])) if float(P["rot_deg"]) else "   (no turn)"), flush=True)
K.save(r, P["result_name"])

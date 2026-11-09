# t_shell - hollow a plain solid (<= 12 faces) leaving the faces named by direction open; wall thickness inward. Fill PARAMS only.
import os, sys; sys.path.insert(0, os.environ.get("KIT_HOME", os.path.dirname(os.path.abspath(__file__)))); import kitlib as K
PARAMS = dict(
    # OUTPUT NAMES (31bs K4 / K20, 2026-11-03): a RELATIVE name lands in the JOB FOLDER - kit run runs this script there; an ABSOLUTE path is the safest (the card lint's ABS PATHS slot)
    base=K.NEED,                  # ABSOLUTE path
    open_faces=K.NEED,            # faces whose outward normal points this way are removed (the open side): a LIST like ['+z'] (a bare '+z' is taken as one face) of '+z' '-z' '+x' '-x' '+y' '-y'
    wall=K.NEED,                  # inward wall thickness, mm
    result_name="result.brep",
)
P = PARAMS
K.need(P)
if isinstance(P["open_faces"], str): P["open_faces"] = [P["open_faces"]]      # 31bx (R1 F6): a bare '+z' had been read per character and died on '+'
body = K.load(P["base"])
if len(body.Faces) > 12: K.fail("shell: %d faces - only plain solids (<= 12 faces) may be shelled; cut the interior as a pocket instead" % len(body.Faces))
sel = []
for f in body.Faces:
    u0, u1, v0, v1 = f.ParameterRange; n = f.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
    for d in P["open_faces"]:
        a = K._AX[d]
        if n.dot(a) > 0.95: sel.append(f)
if not sel: K.fail("shell: no face matched open_faces %s" % P["open_faces"])
res = body.makeThickness(sel, -abs(P["wall"]), 1e-4)
print("BOOKKEEPING shell: vol %.0f (%+.0f) valid %s solids %d faces %d" % (res.Volume, res.Volume - body.Volume, res.isValid(), len(res.Solids), len(res.Faces)), flush=True)
K.save(res, P["result_name"]); print("RESULT -> %s" % P["result_name"])

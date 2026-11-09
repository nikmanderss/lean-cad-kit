# t_edge_round - round selected edges of a PRIMITIVE piece (<= 12 faces) before it is fused. Fill PARAMS only.
import os, sys; sys.path.insert(0, os.environ.get("KIT_HOME", os.path.dirname(os.path.abspath(__file__)))); import kitlib as K
PARAMS = dict(
    # OUTPUT NAMES (31bs K4 / K20, 2026-11-03): a RELATIVE name lands in the JOB FOLDER - kit run runs this script there; an ABSOLUTE path is the safest (the card lint's ABS PATHS slot)
    piece=K.NEED,                     # ABSOLUTE path to a fresh box / extruded outline / cylinder
    radius=K.NEED,
    select=K.NEED,                    # 'vertical' = edges parallel to z; 'all'; 'top' = edges lying in the top face; 'bottom'
    result_name="piece_rounded.brep",
)
P = PARAMS
K.need(P)
p = K.load(P["piece"])
if len(p.Faces) > 12: K.fail("edge_round: %d faces - only primitive pieces (<= 12 faces) may be filleted" % len(p.Faces))
bb = p.BoundBox; edges = []
for e in p.Edges:
    v0, v1 = e.Vertexes[0].Point, e.Vertexes[-1].Point; dz = abs(v1.z - v0.z); dxy = ((v1.x - v0.x) ** 2 + (v1.y - v0.y) ** 2) ** 0.5
    if P["select"] == "all": edges.append(e)
    elif P["select"] == "vertical" and dz > 1e-6 and dxy < 1e-6: edges.append(e)
    elif P["select"] == "top" and abs(v0.z - bb.ZMax) < 1e-6 and abs(v1.z - bb.ZMax) < 1e-6: edges.append(e)
    elif P["select"] == "bottom" and abs(v0.z - bb.ZMin) < 1e-6 and abs(v1.z - bb.ZMin) < 1e-6: edges.append(e)
if not edges: K.fail("edge_round: no edges matched '%s'" % P["select"])
r = p.makeFillet(P["radius"], edges)   # t_edge_round is the one template allowed to call this
if not r.isValid(): K.fail("edge_round: fillet result invalid - draw the round into the sketch outline instead")
K.save(r, P["result_name"]); print("BOOKKEEPING edge_round: vol %.0f (%+.0f) valid %s solids %d faces %d" % (r.Volume, r.Volume - p.Volume, r.isValid(), len(r.Solids), len(r.Faces)))

# t_mirror_pattern - copies of a banked piece (mirror across x=0 / y=0 and/or translations), all fused or cut in ONE step (disjoint copies stay separate solids - 31bw B4).
import os, sys; sys.path.insert(0, os.environ.get("KIT_HOME", os.path.dirname(os.path.abspath(__file__)))); import kitlib as K
PARAMS = dict(
    # OUTPUT NAMES (31bs K4 / K20, 2026-11-03): a RELATIVE name lands in the JOB FOLDER - kit run runs this script there; an ABSOLUTE path is the safest (the card lint's ABS PATHS slot)
    base=K.NEED,                      # ABSOLUTE path
    piece=K.NEED,                     # ABSOLUTE path to the banked piece to copy (the original is NOT applied again unless include_original)
    include_original=K.NEED,
    mirror_x=K.NEED,                  # add the copy mirrored across the plane x = 0
    mirror_y=K.NEED,                  # add the copy mirrored across the plane y = 0
    translations=[],                  # extra copies: list of (dx, dy, dz)
    op=K.NEED,                        # 'add' | 'cut'
    result_name="result.brep",
)
P = PARAMS
K.need(P)
p0 = K.load(P["piece"]); copies = [p0] if P["include_original"] else []
if P["mirror_x"]: copies.append(K.mirror_x(p0))
if P["mirror_y"]: copies.append(K.mirror_y(p0))
if P["mirror_x"] and P["mirror_y"]: copies.append(K.mirror_y(K.mirror_x(p0)))
for d in P["translations"]: copies.append(K.translate(p0, *d))
print("PATTERN: %d copies" % len(copies), flush=True)
body = K.load(P["base"])
# 31bw B4: a pattern's copies are PARTS ON PURPOSE - an added copy that touches nothing stays its own solid (the result a compound; a pattern of 36 receptacles had collapsed to one); a cut follows the base's rule
body = K.fuse(body, copies, "pattern", keep_all=True) if P["op"] == "add" else K.cut(body, copies, "pattern")
K.save(body, P["result_name"]); print("RESULT -> %s" % P["result_name"])

# t_split - divide the body at a plane into two banked parts (e.g. base / cover). Fill PARAMS only.
import os, sys; sys.path.insert(0, os.environ.get("KIT_HOME", os.path.dirname(os.path.abspath(__file__)))); import kitlib as K
PARAMS = dict(
    # OUTPUT NAMES (31bs K4 / K20, 2026-11-03): a RELATIVE name lands in the JOB FOLDER - kit run runs this script there; an ABSOLUTE path is the safest (the card lint's ABS PATHS slot)
    base=K.NEED,              # ABSOLUTE path
    axis=K.NEED,              # 'x' | 'y' | 'z' - the plane is axis = value
    value=K.NEED,             # where the plane sits. A plane exactly on an existing face cuts one
                              # side only (a recorded lesson) - offset by a micron
    name_below="part_base.brep",   # the part on the negative side of the plane
    name_above="part_cover.brep",  # the part on the positive side
)
P = PARAMS
K.need(P)
body = K.load(P["base"]); bb = body.BoundBox; big = 1000.0
# 31bs K23 (2026-11-03; the second project FAILURES 10-30 15:56 / 11-02 14:21): ONLY the chosen axis's two boxes are built. The dict literals of K.box(...) calls built all three axes' boxes
# with the plane value, and a value outside the body's range on an UNCHOSEN axis (any part placed away from the origin) made Part.makeBox raise 'length / height of box too
# small'. The six numbers of each axis are tuples here (nothing built); a value outside the chosen axis's own range is refused by name - one side would be empty.
ax = str(P["axis"]).lower(); v = float(P["value"])
if ax not in ("x", "y", "z"): K.fail("split: axis is 'x', 'y' or 'z' (got %r)" % (P["axis"],))
lo_ax, hi_ax = {"x": (bb.XMin, bb.XMax), "y": (bb.YMin, bb.YMax), "z": (bb.ZMin, bb.ZMax)}[ax]
if not (lo_ax < v < hi_ax):
    K.fail("split: the plane %s = %.3f lies outside the body's %s range %.3f..%.3f - one side of the split would be empty (31bs K23)" % (ax, v, ax, lo_ax, hi_ax))
LO = {"x": (bb.XMin - 1, v, bb.YMin - 1, bb.YMax + 1, bb.ZMin - 1, bb.ZMax + 1),
      "y": (bb.XMin - 1, bb.XMax + 1, bb.YMin - 1, v, bb.ZMin - 1, bb.ZMax + 1),
      "z": (bb.XMin - 1, bb.XMax + 1, bb.YMin - 1, bb.YMax + 1, bb.ZMin - 1, v)}[ax]
HI = {"x": (v, bb.XMax + 1, bb.YMin - 1, bb.YMax + 1, bb.ZMin - 1, bb.ZMax + 1),
      "y": (bb.XMin - 1, bb.XMax + 1, v, bb.YMax + 1, bb.ZMin - 1, bb.ZMax + 1),
      "z": (bb.XMin - 1, bb.XMax + 1, bb.YMin - 1, bb.YMax + 1, v, bb.ZMax + 1)}[ax]
lo = K.box(*LO); hi = K.box(*HI)      # the two boxes of the chosen axis - the only makeBox calls of this template
n0 = len(body.Solids)      # 31bw B4: a COMPOUND base keeps every solid on each side (a board assembly split at its plane); a one-solid base keeps the largest per side, as before
if n0 > 1:      # 31bw B4 (the tester TB6's F1): a compound is split SOLID BY SOLID - the kernel's common of a WHOLE compound whose solids overlap (two of a board's solids overlapped its substrate by 0.37 mm3) had dropped the substrate and nine more solids from BOTH sides
    a = K.Part.makeCompound([x_ for s_ in body.Solids for x_ in s_.common(lo).Solids]); b = K.Part.makeCompound([x_ for s_ in body.Solids for x_ in s_.common(hi).Solids])
else:
    a = body.common(lo); b = body.common(hi)
_sum = a.Volume + b.Volume
print("SPLIT sum %.0f vs body %.0f" % (_sum, body.Volume))
if abs(_sum - body.Volume) > max(0.5, 1e-3 * body.Volume):      # 31bw B4 (TB6 F1): a split that does not add up is a FAILURE, not a report (a 5,976 mm3 loss had passed with rc 0 - CONTRACT rule 0); nothing is banked
    K.fail("split: the two sides hold %.1f mm3 against the body's %.1f - %+.1f mm3 lost or doubled by the cut (a solid the kernel dropped, or one counted on both sides beyond the plane's tolerance); nothing banked" % (_sum, body.Volume, _sum - body.Volume))
for s, nm in ((a, P["name_below"]), (b, P["name_above"])):
    if len(s.Solids) > 1 and n0 == 1: s = max(s.Solids, key=lambda q: q.Volume)
    elif len(s.Solids) > 1: print("   %s: every solid KEPT on this side (the base held %d; 31bw B4): %d solid(s)" % (nm, n0, len(s.Solids)), flush=True)
    K.save(s, nm); print("BOOKKEEPING split %s: vol %.0f valid %s solids %d faces %d" % (nm, s.Volume, s.isValid(), len(s.Solids), len(s.Faces)), flush=True)

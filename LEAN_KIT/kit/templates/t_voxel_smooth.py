# t_voxel_smooth - ONE named region cleaned by DELTA SOLIDS, delivered as a MESH. Fill PARAMS only.
#
# THIS TEMPLATE DOES NOT RUN THE EDIT. It is a CARD CHECKER and a COMMAND PRINTER, and that is
# deliberate: `voxel_smooth` is orchestrator tier, its five steps are separate gated runs, and three
# of them (V2's lump choice, V3's placement, V4's review) require a human-or-orchestrator judgement
# between them that no single script can make on its own. A template that ran all five would be a
# way of skipping those judgements without noticing.
#
# What it does do is refuse a card that cannot succeed, BEFORE any of the expensive steps: a missing
# route decision, a defect class this type does not treat, a removal carded as an addition. Every one
# of those has cost a live session. (A box that takes in a frozen region was refused here until the client,
# 2026-09-22: frozen sections may be in a selection area; they are recreated at the end of edits.)
#
#   python kit.py run t_voxel_smooth.py        (after `kit howto voxel_smooth` copies it here)
import os, sys; sys.path.insert(0, os.environ.get("KIT_HOME", os.path.dirname(os.path.abspath(__file__))))
import kitlib as K

PARAMS = dict(
    # ---- what and where -------------------------------------------------------------------------
    body=K.NEED,              # ABSOLUTE path to the mesh the edit is placed into (.stl) - NOT the B-rep
    base=K.NEED,              # ABSOLUTE path to the UNTOUCHED mesh of the same document; the control
    box=K.NEED,               # (x0, x1, y0, y1, z0, z1) round ONE feature. Cost is the box, accuracy is the cell
    feature=K.NEED,           # what this region IS, in the project's own words ("the rib-to-vane junction")

    # ---- the one question this type asks before anything else ------------------------------------
    defect_class=K.NEED,      # 'concave_junction'  - the ONLY class this type treats
                              # anything else names it and this template refuses: 'step' 'shelf'
                              # 'ridge' 'tab' 'crown' 'shard' -> those are `cutter` or the B-rep

    # ---- V3's route, decided HERE and not at V4 ---------------------------------------------------
    route=K.NEED,             # 'A' rebuild+weld  - a true blend; re-tessellates, the baseline moves
                              # 'B' drop-in       - bit-identical body; leaves a RIM, structurally
                              # 'C' combine       - A's surface inside a boundary, B's outside
                              # C is the route when A and B both fail the SAME feature (the client 2026-09-22)
    acceptance=K.NEED,        # 'blend' | 'rim_tolerated' - the thing `route` must be chosen FROM

    # ---- the field (V2) ---------------------------------------------------------------------------
    h=K.NEED,                 # cell size mm. The step budget, not a taste
    r_close=K.NEED,           # fills concave voids; this is what finds the defect
    r_open=K.NEED,            # shaves convex features; the REM half comes from here
    sigma=K.NEED,             # blur, mm
    g_min=K.NEED,             # trims the feather where the two surfaces nearly coincide
    t_bury=K.NEED,            # burial INTO parent material; the overlap rule, in a field
    add_open=0.0,             # LAST RESORT. It erodes the ADD mask and a fillet's feather is thinner
                              # than the erosion - separate with the BOX and the LUMP CHOICE first
    keep=None,                # ADD lump ranks to keep, largest = 1. None = V2 stops and makes you look
    min_vol=1.0,              # drop ADD lumps under this (mm3)
    do_rem=False,             # the removal half. It arrives as thousands of specks, not a few lumps
    keep_rem=None,            # REM lump ranks - REM needs the choice MORE than ADD does
    min_vol_rem=None,         # defaults to min_vol

    # ---- the review (V4) --------------------------------------------------------------------------
    lead=K.NEED,              # the frames YOU have decided matter, comma separated. There is no default
    reference=None,           # an APPROVED build to put in the frame beside this one, if one exists
    headline_mm3=None,        # the reference's own volume, if there is one: a build materially under it
                              # is a report, not a ship
)

P = PARAMS
K.need(P)

# ---------------------------------------------------------------------------------------------
# THE DEFECT CLASS. Three independent measured cases, 2026-09-22: this type treats a CONCAVE
# JUNCTION THAT WANTS A FILLET and nothing else. The tell when it is aimed at the wrong class is a
# FRAGMENTARY ADD mask - one row gave 6-12 open edges over 9-14 disconnected regions at every
# feather from 0 to 0.40 mm, because the field was trying to add slivers AROUND a tab.
_REMOVALS = ("step", "shelf", "ridge", "tab", "crown", "shard")
if P["defect_class"] in _REMOVALS:
    K.fail("defect_class is %r, which is a REMOVAL or a convex feature. `voxel_smooth` can only ADD:\n"
           "  its ADD half fills concave voids, and a %s has nothing to fill. Card it to `cutter`\n"
           "  (measure the part, DRAW the tool, sweep, cut once) or to the B-rep.\n"
           "  If you believe it is genuinely a concave junction, say so as 'concave_junction' and the\n"
           "  fragmentary-mask test at V2 will settle it."
           % (P["defect_class"], P["defect_class"]))
if P["defect_class"] != "concave_junction":
    K.fail("defect_class must be 'concave_junction' (the only class this type treats) or one of %s,\n"
           "  which this template refuses and sends to `cutter`." % ", ".join(_REMOVALS))

# THE ROUTE IS CHOSEN FROM THE ACCEPTANCE, at V1. Discovering it at V4 cost four generations of
# tuning on a live part: the drop-in cannot produce a tangent blend at any cell size with any lever,
# because its tool stops at a voxel mask boundary and that rim carries a one-cell step and a
# facet-density discontinuity. A tangent blend has neither.
if P["acceptance"] not in ("blend", "rim_tolerated"):
    K.fail("acceptance must be 'blend' or 'rim_tolerated' - it is what `route` is chosen FROM.")
if P["acceptance"] == "blend" and P["route"] == "B":
    K.fail("acceptance is 'blend' and route is B. The drop-in CANNOT produce a tangent blend - not at\n"
           "  any cell size, not with any mask lever; the rim is structural. Route A gives the blend,\n"
           "  route C gives the blend AND the identity outside the edit.")
if P["route"] not in ("A", "B", "C"):
    K.fail("route must be 'A' (rebuild+weld), 'B' (drop-in) or 'C' (combine).")
if P["route"] == "A":
    K.warn("route A, as of 2026-09-22 (the agent's diagnosis): the extract's sign is voted and its reinsertion\n"
           "  gate judges only surface the edit did not touch; place the core with `kit coreplace` (a\n"
           "  refusal is the patch's defect); weld onto ONE unchanged base (_ccweld refuses a chained one);\n"
           "  the join is kit seamweld (_ccweld's default) - the 3:1 zipper-ratio gate is retired. Nine gates:\n"
           "  EDIT_TYPES.md voxel_smooth, route A.")

# THE BOX. Containment, not intersection. A frozen region INSIDE it is said, not refused (the client, 2026-09-22:
# frozen sections may be in a selection area and are recreated at the end of edits); a LUMP chosen inside
# one is refused at V1 by `kit frozen check`, because nothing measurable tells a gap from an aperture.
box = [float(v) for v in P["box"]]
if len(box) != 6:
    K.fail("box is (x0, x1, y0, y1, z0, z1) - six numbers.")
if any(box[2 * i] >= box[2 * i + 1] for i in range(3)):
    K.fail("box is empty or inverted in at least one axis.")
K.frozen_or_fail(box, "this card's box")

# THE LEAD FRAMES. There is no default set, on purpose: the kit cannot tell which cameras see into
# your box, and a body-wide default reads as a choice. Three of five defaults came back `cannot` on
# an under-spine feature, and the sweep was released by the two that happened to see something.
_lead = [t.strip() for t in str(P["lead"]).replace(",", " ").split() if t.strip()]
if len(_lead) < 2:
    K.fail("lead needs at least two frames YOU have decided show this feature. One camera cannot tell\n"
           "  a shape fault from a camera fault, and `kit review --sweep` refuses a single lead.")

if P["route"] == "C" and not P.get("reference"):
    K.warn("route C combines two builds. Name the approved one as `reference` so the review compares\n"
           "  new against APPROVED - a comparison with the untouched body cannot show a regression.")
if P.get("headline_mm3") and float(P["headline_mm3"]) <= 0:
    K.fail("headline_mm3 is the REFERENCE build's own volume, not a target to beat.")

# ---------------------------------------------------------------------------------------------
# The card passes. Print the five steps with this card's numbers in them, in order, and stop.
_b = " ".join("%g" % v for v in box)
K.say("")
K.say("CARD ACCEPTED: %s, a %s, route %s, acceptance %s" %
      (P["feature"], P["defect_class"], P["route"], P["acceptance"]))
K.say("")
K.say("V0  INVENTORY - how many of them are there, before you commit to one box")
K.say("    kit inventory %s --axis <a> --box %s --measure <b>" % (P["body"], _b))
K.say("")
K.say("V1  SELECT - the faces this box meets, and the faces the tool will come within 0.1 mm of")
K.say("    kit frozen check %s" % _b)
K.say("    kit reach %s --box %s --base %s" % (P["body"], _b, P["base"]))
K.say("")
K.say("V2  TOOLS - the field, then the LUMP CHOICE, which is a LOOKING step")
K.say("    h %g  close %g  open %g  sigma %g  g_min %g  t_bury %g  add_open %g  min_vol %g"
      % (P["h"], P["r_close"], P["r_open"], P["sigma"], P["g_min"], P["t_bury"],
         P["add_open"], P["min_vol"]))
K.say("    keep %s%s" % (P["keep"] if P["keep"] else "NOT SET - V2 stops and makes you open the frames",
                         ("   rem: keep %s min_vol %s" % (P["keep_rem"], P["min_vol_rem"]))
                         if P["do_rem"] else "   rem: OFF"))
if P["add_open"] and float(P["add_open"]) > 0:
    K.say("    NOTE add_open is %g. It is the LAST resort: it erodes the ADD mask and a fillet's own"
          % float(P["add_open"]))
    K.say("         feather is thinner than the erosion. Separate with the box and the lumps first.")
K.say("")
K.say("V3  PLACE - route %s" % P["route"])
if P["route"] == "C":
    K.say("    kit stitchband <A.stl> <B.stl> --band <a slab on the boundary you chose>")
    K.say("    kit stitch     <A.stl> <B.stl> --box <the boundary> --out <result.stl>")
else:
    K.say("    the project's own placement step for route %s; check the tool's WINDING before it goes"
          % P["route"])
K.say("")
K.say("V4  PROVE - and the first question is whether anything you can SEE changed")
K.say("    render the result with LK_OWNERMAP=1, then:")
K.say("    kit visible <result.stl> --tool <tool.stl> --frames <review dir>")
K.say("    kit review <before> <result.stl> --out <dir> --box %s --lead %s" % (_b, ",".join(_lead)))
K.say("    kit review --judge <dir> ... ; kit review --sweep <dir> ; kit review --done <dir>")
K.say("    kit accept <job> --review <dir>        (it will not accept without a COMPLETE review)")
if P.get("headline_mm3"):
    K.say("    the reference is %g mm3. A build materially under it is a report, not a ship."
          % float(P["headline_mm3"]))
K.say("")
K.say("This template CHECKS the card and prints the steps. It does not run them: three of the five")
K.say("need a judgement between them, and a template that ran all five would skip those quietly.")

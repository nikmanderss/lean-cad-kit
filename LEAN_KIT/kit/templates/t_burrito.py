# t_burrito - THE BURRITO (second build): everything inside a footprint x v-range is re-expressed as clean, smooth, printable material. Fill PARAMS only.
import os, sys; sys.path.insert(0, os.environ.get("KIT_HOME", os.path.dirname(os.path.abspath(__file__)))); import kitlib as K, kitlib_burrito as B, Part
PARAMS = dict(
    # EXEMPT FROM `K.need` - ON PURPOSE, AND IT IS THE ONLY TEMPLATE THAT IS. Every other template's
    # card slots are `K.NEED` and refuse until the card fills them (kitlib `need`, 2026-09-16, the client's
    # ruling). These levers are TUNED CONSTANTS whose owner is `BURRITO_STEPS.md`, with a live round
    # attached, and stripping them blind is the failure the client named: *"a wrongly applied check will
    # confuse an agent and utterly break editing."* The lever census decides it.
    #
    # THIS NOTE LIVES INSIDE THE DICT FOR A REASON. `kit run`'s copy rule compares a worker script
    # to its template byte-for-byte OUTSIDE the PARAMS block. A comment placed ABOVE this line on
    # 2026-09-16 changed the body, and every burrito worker script on disk - 63 of them, in the
    # live round - would have been refused at its next `kit run`. Caught by checking, the same day.
    base="region.brep",               # the body: the model of record, or a region.brep that holds the WHOLE footprint plus margin
    rays="z",                         # the columns run along this axis; the plan axes follow cyclically: z -> (c=x, u=y), x -> (c=y, u=z), y -> (c=z, u=x)
    spin=0.0,                         # degrees about world z applied BEFORE the rays (the client 2026-09-11: the skirt corners): rays 'x' with spin 45 meet a corner wall facing between -x and -y. Footprint, v-range, maps and sections are all in the spun frame; the piece comes back in world
    footprint=None,                   # ANY polygon in the plan, as [(c,u), (c,u), ...]; None = the rectangle c0..c1 x u0..u1 below
    c0=-150.0, c1=150.0,              # rectangle only: the footprint's extent along c
    u0=-215.0, u1=-190.0,             # rectangle only: ... and along u
    v0=60.0, v1=95.0,                 # the range along the rays that is REPLACED; put both in air when you can (nothing to mate there)
    spacing=0.5,                      # grid cell across the plan (mm) - every column is a sample plane in both directions
    mmpv=0.1,                         # cell along the rays (mm)
    margin=2.0,                       # sampled beyond the footprint, for context and for the mating (mm)
    bridge=1.2,                       # WELD BY ACCESSIBILITY: air that a ball of this diameter cannot reach from outside is filled - cracks, laminae and cavities behind a thin opening weld at a SMALL ball; a designed slot or channel WIDER than the ball stays open however deep. Set it UNDER the narrowest designed slot in the footprint
    bridge_mode="ball",               # 'ball' (above) or 'close' = the old isotropic closing, which also filled any slot narrower than bridge
    shave=0.3,                        # OPEN in 3-D: shards, tabs and walls thinner than 2*shave vanish (mm); under half the thinnest DESIGNED wall
    majority=0.5,                     # majority vote over this radius (mm) on the voxel grid: rounds pits/bumps smaller than it. KEEP UNDER HALF THE THINNEST DESIGNED WALL - it erases anything thinner than its window (a 2 mm vane at 1.5 is gone)
    island_min=2.0,                   # a piece of material not connected to anything else, under this volume (mm3), is a shard: dropped
    smooth=2.0,                       # THE SMOOTHING PASS: radius (mm) of the slope-aware average on every surface - a steep flank smooths like a flat skin, a step does not mix
    crease=1.0,                       # a height jump over this (mm) between neighbouring columns is a CLEAN LINE: kept sharp, never smoothed across
    step_ratio=2.5,                   # ... and it is built as a STEP (vertical riser) only if it stands out from the jumps either side by this ratio; a steep slope has equal jumps everywhere and stays one smooth surface
    step_span=2.0,                    # ... and NOT a step if a same-sign jump of comparable size lies within this distance (mm), along the ray or sideways: a faceted slope's treads are one ramp, not creases. A slot's two walls are opposite in sign and stay steps. Inert under 2 cells (the adjacent cell is already judged by step_ratio)
    cliff=6.0,                        # ... but a jump over THIS (mm) between two columns is a cut whatever its neighbours say: a wall at 85 degrees or more. Build 5 (2026-09-11): the rib wall's crease line had gaps, both sides of the wall became one panel with an 18-23 mm jump inside it, and every fitter rang by tens of mm. Keep it above the biggest facet of a drafted wall (4 mm here)
    feature_min=6.0,                  # a crease-bounded patch under this plan area (mm2) is a feature to HAMMER: dissolved and re-interpolated. Judged on the panels the REAL creases make, never on the fragments the extension cuts leave
    band=2.0,                         # within this distance of the footprint edge the surfaces blend to the body's own skin (mm), reaching it at the wall
    fit_tol=0.2,                      # build: each panel's B-spline sheet approximates its field to this (mm). MUST be >= 2 x mmpv: the fields are quantised at mmpv and a tolerance at that floor makes the fitter follow the voxel staircase (38313 poles, empty layer - 2026-09-10)
    fit_step=1.0,                     # build: the sheet is fitted through every fit_step mm of the field
    fit_mode="interp",                # build: 'interp' = a degree-3 interpolation through those samples, bounded by construction (default since 2026-09-11: the tolerance-driven 'approx' rang to z 41..137 on a 70-degree groove with data 70..96 and self-intersected - the piece-assembly failure). 'approx' = the old ladder, a control. A sheet whose poles leave the panel's data range by more than max(3 mm, half the range) is rejected for a least-squares quadric
    edge_min=0.3,                     # build: a layer's outline is drawn where it is at least this thick (mm, the print class) + a 3x3 vote + Chaikin x3 - no 0.5 mm stairs on a feather edge. 0 = the raw column mask (the 08:15 silhouette), a control
    small_panel=64,                   # build: a panel under this many cells is fitted as a least-squares PLANE, not a B-spline. 0 = every panel a B-spline, a control
    panel_overlap=0.0,                # unused since the shared-wall assembly (every crease is ONE cutting sheet; neighbours share it exactly); kept so old cards still parse
    fuse_tol=None,                    # build: the fuse may not manufacture more than this (mm3); None = max(3, 2 % of the piece)
    fuse_fuzzy=0.0,                   # build: fuzzy tolerance for the fuse with the body (mm); 0 = exact. Try 0.02 when the fused result's rays cannot close while the piece's do
    sheet_every=10.0,                 # pictures: a section every this many mm along c AND along u, plus one map per sheet-layer
    mode="probe",                     # 'probe' = grid, decisions, pictures, plan; nothing built.  'build' = the edit.  'pass2' = SHELVED (the client 2026-09-10): pass 1 as the detector, then the method inside each zone of change only, the body kept elsewhere
    pass2_change_min=0.3,             # pass 2 (shelved): a column changed if a surface moved more than this, or the cleaning added/removed more than this through it (mm)
    pass2_margin=2.0,                 # pass 2 (shelved): the zones of change are grown by this before they become footprints (mm)
    pass2_min_area=4.0,               # pass 2 (shelved): a zone under this plan area is left alone (mm2)
    sections_approved="",             # build refuses while this is empty: the client approves the probe's sections first (their ruling 2026-09-10); write who, when, which
    out_dir=".",                      # where burrito_plan.json and the pictures go
    piece_name="piece_burrito.brep",
    result_name="result.brep",
)
P = PARAMS
body = K.load(P["base"])
if str(P.get("mode", "probe")).lower() == "pass2":
    # SHELVED (the client): runs only when a card says mode='pass2' on their word. Pass 1 standalone is unchanged.
    body = B.run_pass2(body, P)
    K.save(body, P["result_name"]); print("RESULT -> %s" % P["result_name"], flush=True)
else:
    out = B.run(body, P)
    if out is None:
        print("BURRITO PROBE ONLY - nothing built. Open the maps and the sections, read the decisions / wall / volume lines, write the card, then mode='build'.", flush=True)
    else:
        piece, region, plan = out
        b = piece.BoundBox
        print("PIECE %s: vol %.0f faces %d bbox x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (P["piece_name"], piece.Volume, len(piece.Faces), b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax), flush=True)
        K.save(piece, P["piece_name"])
        body = B.replace(body, piece, region, P.get("fuse_tol"), P, plan)
        K.save(body, P["result_name"]); print("RESULT -> %s" % P["result_name"], flush=True)

r"""kit_rebuild.py - `kit rebuild <step>`: THE BURRITO'S RUNNER (the rebuild chain, BURRITO_STEPS.md, 2026-09-28).

The chain: everything inside a WINDOW of the body of record is re-decided from the body's own surfaces
(the arrangement), blended and opened as continuous signed-distance fields (the blend), finished as a mesh,
reviewed, optionally decimated, made a B-rep, measured against the original so that ONLY THE BINS IT CHANGED are
replaced (keep: the clean faces, the PROTECT voids and the frozen faces stay the body's own), and put back by the
EXACT-PLANE JOIN (both sides cut by the same solid; the reinsert). Eleven scripts in `LEAN_KIT\\kit\\rebuild\\`, run
from THERE (nothing copied into the job), one freecadcmd process each, through the kit's `sh()` (the cap, the kill
on silence, `.KILLED` markers on declared outputs).

    kit rebuild <step> --job <name> --tag <T> [--set K=V ...] [--plan] [--bg] [--whole-body "<why>"] [--supersede "<why>"  (skin-labels: a kit update re-makes the judged layout)]
    kit rebuild --help                    every step, its script, its CARD levers and the defaults it takes

What every run gets: an environment EMPTY of every lever of the chain (nothing inherited from the shell - a
`$env:STL` left by an earlier line is not an input), the step's DEFAULTS from the job folder (each printed with
"default" beside it), the run's `--set`s, KIT_HOME; a CARD lever the step reads that the run does not set is
REFUSED by name (WIN and PLANES for the region, R for the blend, REDUCTION for the decimation, STEP for the
reinsert - an empty value is a decision too: `--set PLANES=`); the whole-body gate on every STL input; the wall
clock from the project's WALL_CLOCKS.md row for the script (the sample is added after every run); the env
record `env_<step>_<T>.json` and the log `log_<step>_<T>.txt` in the job folder; the atlas gate before the
reinsert's STEP 3 (new B-rep geometry needs its region: `kit atlas assign <job> --to <region>`); the session
gate (an orchestrator command; `--plan` and `--help` are reading, not editing).

31al (2026-10-06) - THE SKIN ROUTE IS THE BURRITO NOW. the client: "There is a new burrito process and it works. The old process gets ~1/2
shelved and the new process needs gates/hooks/setup so it can be tested on new windows." The front half is the REGION step and skin-source (the voxel field - arrange .. review - is SHELVED
since 31ba, refused without SHELVED_OK; 31bx R6 F11); then the reinsert faces FIRST
(reinsert STEP=1 writes wall_caps.brep, the body's own section faces); then the skin remade as a low-face-count B-rep from the voxel
and the ORIGINAL's faces (skin-regions, skin-edges, skin-points, skin-labels, skin-rim + the layout judged, skin-mirror on a symmetric
edit, skin-network, skin-frame, skin-build with the frame check, skin-look + the piece judged); then reinsert STEP 2-4 by the SEW on
those caps (JOIN=sew, REGION=none - no boolean). SHELVED (refused without --set SHELVED_OK="<why>"): decimate, fillholes, finish,
brep, keep and the exact-plane fuse (JOIN=fuse) - the triangle piece's back half (1.5k faces against the edit region's 142).

31an (2026-10-07) - the client's answers on R4 skin 1 (stopped "time's up": three hours, 14 rungs on one 3 mm corner, the crumpled underside seen
only by the final sweep): "Remember the process worked as I had it, it was only missing focus on simplifying the geometry instead of
following the voxel improvements so closely"; "it is just direction to the agent and its sub agents that need refinement".
  * THE FACE LADDER: original surface (skin-labels' rung 1 + skin-rim's owner check) -> flat (skin-build PLANE) -> smoothed fit (LAM 0.5
    suggested). No extruded walls, no filled faces.
  * THE MIRRORED LAYOUT, generic: MIRROR is skin-labels' CARD lever (any plane "x 0" / "nx ny nz c"); the later steps take the decision.
  * THE RESTART, PER SPOT: three failed tries at one place lock every step after skin-points until the points INSIDE that place are
    picked again (skin-points keeps every other point; PTS_BOX / PTS_DROP there, read off its wireframe + transparent voxel close-ups)
    and judged: `judge --what points`. A move/redo names its places (--face / --spot); a place a later verdict does not name passed.
  * THE SECOND REVIEWER BEFORE THE AGENT'S `ok` ON A PIECE: `kit rebuild second --what skin --assign` / `--shard k --result <json>`;
    its defects come back ranked largest first. skin-look shows the whole piece from every side and every fitted face in two iso views.
  * SUGGESTIONS, NOT REQUIREMENTS: the runner's values are printed as "suggested"; only LEVER_RANGE refuses a value.
  * THE BUILD LOG: one row per run / judgement in <job>\BUILD_LOG.md; a STATE line at every savepoint.

31ar (2026-10-07) - the client: "There is an issue of waste with the way renders are being created ... Sometimes building the model and getting
true renders is the right answer"; "mirror checks should pass before creating a real model".
  * THE TRIAL: reinsert --set TRIAL="<why>" on STEP 2, 3, 4 sews an UNACCEPTED piece into the body as a look at the real model (its
    mirror check first on a symmetric edit); the body is body_trial.brep - not body_new.brep until its ACCEPTANCE (31aw: `judge --what trial --verdict ok` promotes it) - and review-body reviews it
    (TRIAL_LOOK.json); `judge --what trial` records redo / move, or ok on the two reviewers' frames (over blockers only with the client's recorded --ruling).
  * skin-look LOOK_MODE quick (suggested: the whole piece, 8 frames) for the inner loop; full (every fitted face in two iso views) once,
    for the second reviewer (`second` refuses a quick look). sk_build prints no deviations (SHOW_NUMBERS=1 to see them).

31as (2026-10-07) - the client: "Feature map and wireframe: - should be CAD generic kit steps. They work correctly for the process and adjusting them makes
step 4 complete correctly, they do not rely on a step 4 finish to make it into the kit." the agent's R4 skin 2 job scripts are kit steps:
  * skin-features (after skin-labels): THE FEATURE MAP - FEATURES (the agent's {feature: [original face ids]}, from FEAT_labels_*) makes the faces
    the features; small smooth faces join. skin-rim refuses a layout that has not been through it.
  * skin-wires (after skin-frame): THE WIREFRAME DECIDED - LINES (each chain's kind, with its reason) and RAILS (straight feature edges between
    the reinsert faces' corners, CORNERS_*); symmetric; WIRE_* labelled from the finished curve. skin-build refuses until `judge --what wires` is ok.

31av (2026-10-07) - the client's answers on the agent's loop (six section-wide re-splits, the restart never fired) and the render study:
  * THE LAYOUT LOCK: the first layout judged ok fixes skin-labels' / skin-features' / skin-rim's section-wide levers (skin\\LAYOUT_LOCK.json) - a face
    then changes through its points, its lines through LINES / RAILS (the client: "Yes to changing it through points").
  * LAYOUT ROUNDS: ROUNDS_MAX (5, 31bk) layout redos without a skin-build that passes lock every place they named - back to the points there.
  * 31bk: a layout / piece judged ok is ALSO overturned by a later step that FAILED or was KILLED on it (BUILD_LOG): the upstream step then runs
    by itself (no strike; a layout round). A re-run with neither a picture nor a failure on the record is a refusal the first time, a strike after.
  * PICS quick in the loop (about 8 frames a step), the full set before a layout / wireframe ok; every step keeps its pictures.
  * The judge's --frame is a picture in the job's own folder (jobs\\<J>\\skin\\review\\); `kit rebuild save` / `restore`: a build's whole state.
  * After a mirror check that passes, the next step is named (the trial for a piece).
"""
import os, sys, json, time, re, subprocess, shutil

STEPS = [
    ("region",      "rb_region.py",      "the edit region's content, walls and record (read its two warnings)", ("WIN", "PLANES"), {}),
    # voxel step is now getting skipped
    ("arrange",     "rb_arrange.py",     "SHELVED 2026-10-08 (the voxel field; --set SHELVED_OK=\"<why>\"): stage A: split by the design surfaces + classify (resumable: run again until 'STAGE A done')", (), {"STAGE": "A"}),
    ("arrange-m",   "rb_arrange.py",     "SHELVED 2026-10-08 (the voxel field): stage M: the material decision -> arr_base_raw.stl (99-101 % of the content) + the face census", (), {"STAGE": "M"}),
    ("arrange-f",   "rb_repair.py",      "SHELVED 2026-10-08 (the voxel field): the arrangement's mesh finish: arr_base_raw.stl -> arr_base.stl (FINAL solid True nonmanifold False selfint 0, or it refuses)", (), {}),
    ("blend",       "rb_blend.py",       "SHELVED 2026-10-08 (the voxel field): the closing R / R_SMALL, the opening, walls kept CLIP_OUT past the planes -> blend.stl", ("R",), {}),
    ("repair",      "rb_repair.py",      "SHELVED 2026-10-08 (the voxel field): mesh finish -> piece.stl (solid True, selfint 0)", (), {}),
    ("review",      "rb_review.py",      "SHELVED 2026-10-08 (the voxel field): the piece: 8 views, 5 close-ups, station overlays vs the content -> review\\ (OPEN EVERY PICTURE)", (), {}),
    ("skin-source",  "sk_source.py",     "SKIN 0 (31ba - THE VOXEL FIELD IS SHELVED, the client 2026-10-08): the edit region's ORIGINAL content tessellated -> source.stl, the mesh the skin steps lay the points, the layout, the frame and the network on; the geometry is corrected in the WIREFRAME", (), {}),
    ("skin-regions", "sk_regions.py",    "SKIN 1: the mesh record for the skin steps (skin\\regions.npz) - on a B-rep source (31bb) with the original face of every triangle, no regions, no pictures; on a voxel: the changed regions, clipped WALL_CLIP 1.5 off the walls", (), {}),
    ("skin-edges",  "sk_edges.py",       "SKIN 2: the original's edges classified from the B-rep and measured against the voxel -> skin\\edgemap\\ (open its pictures)", (), {}),
    ("skin-points", "sk_points.py",      "SKIN 3: THE PICK OF WHAT IS KEPT - ~NPTS points of the mesh, each given to the original face it lies on; a face with no point is absorbed by its neighbours (NPTS, PTS_BOX, PTS_DROP, FRAME_PTS) -> skin\\points1000.json", (), {}),
    ("skin-labels", "sk_labels.py",      "SKIN 4: the final faces decided by the points (a flood from the ON points, crisp original edges as barriers, no bands); MIRROR = the card's symmetry decision (a symmetric edit: the layout made on one side and mirrored); the face ladder's rung 1 (kind orig) -> skin\\patches_labels.*", ("MIRROR",), {}),
    ("skin-features", "sk_features.py", "SKIN 4b (31as): THE FEATURE MAP - the faces made the features (FEATURES = the agent's json {feature: [original face ids]}, written from FEAT_labels_*: \"A spine, A vane, a support\"), small smooth faces joined -> skin\\patches_labels.* rewritten, FEAT_*", (), {}),
    ("skin-rim",    "sk_rim.py",         "SKIN 5: THE EXACT FRAME - the body's own wall faces own the rim -> skin\\patches.* + LAYOUT_LOOK.json (OPEN EVERY FRAME; `kit rebuild judge --what layout`)", (), {}),
    ("skin-mirror", "sk_mirror.py",      "the MIRROR CHECK (a symmetric edit): WHAT=layout after skin-rim, WHAT=piece after skin-build -> skin\\mirror_<what>.json + pictures (MIRROR: the card's decision at skin-labels)", ("WHAT",), {}),
    ("skin-network", "sk_network.py",    "SKIN 6: the edge network on the judged layout - one edge per border, built once, shared -> skin\\network.*", (), {}),
    ("skin-frame",  "sk_frame.py",       "SKIN 7: the frame map - wall junctions on the body's vertices, the wall chains = the body's own edges -> skin\\network_frame.brep, frame.json", (), {}),
    ("skin-wires",  "sk_wires.py",       "SKIN 7b (31as): THE WIREFRAME DECIDED - every border ONE simple curve: LINES (each chain's kind with a reason), RAILS (straight feature edges between the reinsert faces' corners), symmetric, labelled from the finished curve -> skin\\network_frame.brep rewritten, WIRE_* (OPEN EVERY FRAME; `kit rebuild judge --what wires`). THE ORIGINAL IS THE STARTING REFERENCE, NOT A CONSTRAINT: any border can be redrawn, moved, split (role split) or added (role guide); faces joined by FEATURES - nothing holds the wireframe to the original's face boundaries, EXCEPT THE FRAME: at the edit region's walls every face ends exactly on the body's own section faces, edges and vertices (31bh)", (), {}),
    ("skin-build",  "sk_build.py",       "SKIN 8: THE FACE LADDER (original surface -> flat -> smoothed fit), shell -> solid, THE FRAME CHECK -> skin\\piece_skin.brep, piece_faces.json", (), {}),
    ("skin-look",   "sk_look.py",        "SKIN 9: the piece's render review - the whole piece from every side (below too) + TWO ISO VIEWS of every fitted face, side-lit -> skin\\review\\SKIN_look_* (the SECOND REVIEWER first: `kit rebuild second`; then `kit rebuild judge --what skin`)", (), {}),
    ("reinsert",    "rb_reinsert.py",    "STEP=1 local box + THE WALL CAPS (run it before the skin steps) | 2 JOIN=sew: the skin piece on the body\'s own caps (no boolean; JOIN=fuse is SHELVED) | 3 the ring sew -> body_new.brep | 4 CHECK PASS/FAIL (seam, PROTECT, shells)", ("STEP",), {}),
    ("review-body", "rb_review_body.py", "the new body whole, at the region, old-vs-new stations -> review_body\\ (OPEN EVERY PICTURE)", (), {}),
    # recorded
    ("decimate",    "rb_decimate.py",    "SHELVED 2026-10-06 (--set SHELVED_OK=\"<why>\"): quadric decimation -> piece_dec.stl (required: ~4.5k faces is the join's ceiling; 0.99 = ~1.5k faces on a section)", ("REDUCTION",), {}),
    ("fillholes",   "rb_fillholes.py",   "SHELVED 2026-10-06 (--set SHELVED_OK=\"<why>\"): the holes a decimation can leave -> piece_dec_f.stl", (), {}),
    ("finish",      "rb_repair.py",      "SHELVED 2026-10-06 (--set SHELVED_OK=\"<why>\"): mesh finish after the decimation -> piece_final.stl", (), {}),
    ("brep",        "rb_brep.py",        "SHELVED 2026-10-06 (--set SHELVED_OK=\"<why>\"): mesh -> B-rep, one solid per component -> piece.brep", (), {}),
    ("keep",        "rb_keep.py",        "SHELVED 2026-10-06 (--set SHELVED_OK=\"<why>\"): KEEP WHAT IS CLEAN: the bins the piece changed -> keep_region.brep; PROTECT and frozen bins kept; the cuts checked and drawn (keep\\keep_cuts_*.png: judge them - `kit rebuild judge`)", (), {}),
]
# content.brep
FILES = {"content": "content.brep", "window": "window_solid.brep", "walls": "walls.json", "arr": "arr_base.stl", "arr_raw": "arr_base_raw.stl",
         "blend": "blend.stl", "piece": "piece.stl", "dec": "piece_dec.stl", "decf": "piece_dec_f.stl",
         "final": "piece_final.stl", "brep": "piece.brep", "keep": "keep_region.brep", "frozen": "keep_frozen.json", "body_new": "body_new.brep", "region_rec": "REBUILD_region.json",
         "wall_caps": "wall_caps.brep", "skin_piece": os.path.join("skin", "piece_skin.brep"), "patches": os.path.join("skin", "patches.json"),
         "source": "source.stl"}   # skin-source
SHELVED = ("decimate", "fillholes", "finish", "brep", "keep",
           "arrange", "arrange-m", "arrange-f", "blend", "repair", "review")   # voxel step is now getting skipped
VOXEL = ("arrange", "arrange-m", "arrange-f", "blend", "repair", "review")
SKIN = ("skin-source", "skin-regions", "skin-edges", "skin-points", "skin-labels", "skin-features", "skin-rim", "skin-mirror", "skin-network", "skin-frame", "skin-wires", "skin-build", "skin-look")
LEVERS = ("BODY", "RUN", "WIN", "PLANES", "SRC", "STAGE", "BUDGET", "A_SMALL", "LEVEL", "LEVEL_DEG", "LEVEL0", "LEVEL0_DEG",
          "DUP_FRAC", "GAP", "SPIKE_V", "V_SLIVER", "T_MIN", "V_MIN", "PLANE_TOL", "FLAT", "TOL", "FUZZ", "DEV", "WELD", "NMAX", "SPLIT", "CLIP_TOOLS", "TOOL_ALLOW", "SLIT", "KEEP_TINY_A", "KEEP_TINY_B", "REPAIR_ROUNDS",
          "PROTECT_GAP", "GAP_V", "LEVEL_WALL", "LEVEL_VERTS", "PROTECT_FACES", "REFINE_ZONES", "REFINE_FRAC", "REFINE_MAX",
          "STL", "OUT", "R", "H", "W", "E", "WALLS", "CLIP_OUT", "R_SMALL", "V_BIG", "OPEN", "SNAP", "EDGE_DEG", "FLAT_DEG",
          "POLISH", "POLISH2", "HOLD_W", "SAMP", "DUMP", "CLIP_BOX", "SLIV", "SLIV_A", "ORIG", "TAG", "OUT_DIR", "STATIONS_X",
          "STATIONS_Y", "REDUCTION", "DECIM", "DECERR", "BAND", "ACCUM", "VOLPRES", "DEC_SNAPBACK", "KEEP_RIMSNAP", "KEEP_RELAX_RINGS", "KEEP_RELAX_ITER", "KEEP_OPEN_OK", "KEEP_MICRO", "CLOSE_ROUNDS", "WALL_ZONE", "POLISH_PB", "POLISH_NM", "MIN_MM3", "PIECE", "G", "SHRINK", "SHRINK_LADDER", "MIN_KEEP", "SEWTOL", "SHRUNK_MAX", "STEP", "NEW", "PINCH", "PROTECT", "PROTECT_W", "IN_CONTENT", "JOIN", "FUZZY", "SEW_MATCH",
          "KEEP_TOL", "KEEP_CELL", "KEEP_SAMP", "KEEP_DEV", "FROZEN", "FROZEN_TOL", "KEEP_OFFSET", "KEEP_GROW", "KEEP_CLEAR", "SAME_TOL", "SPIKE_DENSE", "MANIFOLD_FIX", "GRID_MIRROR_X",
          "INSIDE", "ZONES", "ZONE_W", "FLAT_TRIM", "INTERNAL_FIX", "INTERNAL_DROP", "INTERNAL_MAX", "INTERNAL_GATE", "FRAC_BOX", "TOOL_VOLCHECK", "WINDOW", "SURF_MAX", "REGION", "BOP_OK", "SEAM_MAX", "PROTECT_TOL", "GRAZE_OK", "FEAT", "FEAT_REACH", "FEAT_DEPTH", "KEEP", "KEEP_M", "KEEP_TOL", "KEEP_L", "KEEP_VMIN", "KEEP_NM", "KEEP_JOIN", "LK_TAG",
          "T_HI", "T_LO", "A_MIN", "WALL_MM", "WALL_CLIP", "EDGE_PHASE", "TANGENT_DEG", "TINY_MM", "NPTS", "ON_MM", "SUFFIX",
          "A_NOISE", "OPEN_MM", "ISLAND_MM2", "WRAP_STRENGTH", "CREASE_DEG", "BAR_MM", "SMOOTH_R", "SMOOTH_IT", "NO_BANDS", "RIM_MM", "REACH_MM",
          "JMERGE", "SMOOTH_MM", "STEP_MM", "KEEP_NET", "EDGE_FIX", "RINGS", "CTRL_MM", "W_EDGE", "LAM", "NEAR_MM", "LAM_MODE", "RING_W", "FRAME",
          "VOXCHECK", "SAMEPARAM", "FITDBG", "FITDBG_P", "SHAPE", "LOOK_PREFIX", "MIRROR", "WHAT", "MIRROR_TOL", "MIRROR_AREA", "SHELVED_OK", "PREFLIGHT", "TRACE_TUBE_MM", "ADD_VIA_TOL",
          "PTS_BOX", "PTS_DROP", "FRAME_PTS", "FRAME_PTS_MM", "MASTER", "CROSS_MIN_MM2", "FRAG_MM2", "ORIG_FRAC", "ORIG_MIN",
          "PLANE", "PLANE_P95", "PLANE_MAX", "SYMFIT", "FRAME_TOL", "LOOK_MIN_MM2", "KEEP_POINTS",
          "TRIAL", "LOOK_MODE", "FACES", "LOOK_FULL_OK", "SHOW_NUMBERS",
          "FEATURES", "MAX_AREA", "TINY", "SMOOTH_DEG", "MAX_SPREAD", "UNITE", "MIN_BORDER", "UNITE_MM", "UNITE_DEG", "STRIP_HALF", "FEAT_LABELS",
          "LINES", "RAILS", "TOL_LINE", "TOL_ARC", "TOL_CUBIC", "TOL_SMOOTH", "MAX_POLES", "GROW", "GROW_MAX", "CROSS_MM", "END_MM", "WALL_CLEAR",
          "EASE_MM", "SYM_WIRES", "END_BLEND", "WIRE_PICS", "WIRE_LABELS", "CORNER_PICS",
          "PICS", "CARRY_MM", "ON_TOL",
          "FIT", "CORNER_DEG", "SPAN_STEP", "OFF_TOL", "ADD", "FILLETS", "ADD_SNAP", "NET_PICS", "DESIGN",
          "PIC_W", "FILLET_LINES", "FILLET_RERUN", "FIL_DBG",
          "THIN_MM", "JMOVE_MAX", "LOOK_ANG", "LOOK_TOL_MAX", "LOOK_VIS", "ABSORB_MM2", "ABSORB_FRAC", "SLOW_X", "SLOW_MIN_S", "CREASE_MIN_DEG", "FIL_TAPER", "TAPER_X", "TAPER_MIN", "FIL_SMOOTH_MM", "CREASE_TURN_MAX", "CONTACT_MERGE_MAX", "NURBS_LOOSE_RIM", "BURIED_MIN", "BURIED_REACH", "LINE_OFF_MAX", "PLATE_BALLOON_MM", "PLATE_BALLOON_FRAC", "LOOK_HIDDEN", "RIBBON_MM", "RIBBON_STEP", "PIC_DEV", "PIC_ANG", "SEC_TOL",
          "HOLES", "VERT_TOL", "TWIN_MM", "TWIN_AREA", "VOTE_MM", "MAP_TOL", "CARRY_FIT", "SELF_MM",
          "TESS", "ANG", "MIN_A", "NURBS", "NURBS_RIM", "NURBS_WALL_RIM", "NURBS_TOL", "NURBS_STEP", "NURBS_MAXSEG", "NURBS_MAXDEG", "NURBS_SKIP", "WIRE_OCC",
          "WIRE_CLEAN_TOL",
          "HAIRPIN_DEG", "HAIRPIN_MM")
# over the
# recorded
DEFAULTS = {
    "arrange":   {"A_SMALL": "1", "LEVEL": "0.8", "LEVEL_DEG": "12", "BUDGET": "140"},
    "arrange-m": {"A_SMALL": "1", "LEVEL": "0.8", "LEVEL_DEG": "12"},
    "arrange-f": {"PINCH": "0.6", "INTERNAL_DROP": "1", "INTERNAL_MAX": "0.5"},
    "blend":     {"H": "0.2", "CLIP_OUT": "0.1", "OPEN": "0", "POLISH": "30", "KEEP": "1", "KEEP_JOIN": "merge", "KEEP_TOL": "0.8", "KEEP_MICRO": "open", "KEEP_OPEN_OK": "60"},
    "brep":      {"MIN_MM3": "0.5"},
    "keep":      {"KEEP_TOL": "0.1", "KEEP_CELL": "3", "FROZEN_TOL": "0.15", "KEEP_GROW": "3"},
    "reinsert":  {"G": "3", "SHRINK": "2", "CLIP_OUT": "0.1", "SEAM_MAX": "0.15", "PROTECT_TOL": "2", "JOIN": "sew"},
    "skin-points": {"FRAME_PTS": "1", "PICS": "quick"},
    "skin-labels": {"OPEN_MM": "1.0", "PICS": "quick"},
    "skin-features": {"PICS": "quick"}, "skin-rim": {"PICS": "quick"}, "skin-network": {"PICS": "quick"}, "skin-wires": {"PICS": "quick"},
    "skin-build":  {"FRAME": "1", "KEEP_NET": "1", "EDGE_FIX": "1", "W_EDGE": "400", "CTRL_MM": "1.0", "LAM": "0.5", "VOXCHECK": "0", "FRAME_TOL": "0.02", "PLANE": "1"},
}
# recorded
LEVER_RANGE = {
    "SEAM_MAX":  (0.0, 0.15, "the client 2026-09-21: a step where new meets old is at most 0.15 mm - lowered, never raised"),
    "SEC_TOL":   (0.0, 0.15, "31bp fix 7b: a station line both bodies share within SEC_TOL is drawn as unchanged - never over the seam ceiling"),
    "FRAME_TOL": (0.0, 0.15, "a wall edge off the body's by more than the 0.15 mm seam ceiling is a seam step (the client 2026-09-21)"),
    "NPTS":      (100, 5000, "projecting 59k voxel vertices ran past 720 s (SP7b); 1000 points took 18 s - 5000 is ~90 s"),
    "LAM":       (0.0, 1e6, "the fairness is not negative"),
    "CTRL_MM":   (0.05, 50.0, "a control spacing under 0.05 mm is finer than the voxel itself"),
    "PIC_DEV":   (0.001, 0.05, "31bn: a piece picture coarser than 0.05 mm (a sixth of the print tolerance) is no evidence of the geometry (the client: accurate to the geometry)"),
    "PIC_ANG":   (0.005, 0.10, "31bn: a piece picture with facets more than 5.7 deg apart is no evidence of a curved face"),
}
NEEDS_FC = re.compile(r"^\s*(?:from\s+(?:FreeCAD|FreeCADGui|Part|MeshPart|Mesh|vtk)\b|import\s+[^\n#]*\b(?:FreeCAD|FreeCADGui|Part|MeshPart|Mesh|vtk)\b)", re.M)


def _dir(kit):
    return os.path.join(kit.HERE, "rebuild")


def _window_of(folder):
    """the edit region the region step recorded (REBUILD_region.json), as the 'x0 x1 y0 y1 z0 z1' string, or None"""
    try:
        rec = json.load(open(os.path.join(folder, FILES["region_rec"]), encoding="utf-8"))
        w = rec.get("window")
        if w and len(w) == 6:
            return " ".join("%g" % float(v) for v in w)
    except (OSError, ValueError, TypeError):
        pass
    return None


def _protect_of(folder, first="blend"):
    """the card's PROTECT boxes as the lever string - from the record named `first` ("blend": what the piece was built with;
    "region": what the card gave the region step, 31ai P19 - so a fresh edit region's first split honours them), else from the other;
    None when neither record holds them"""
    order = ("REBUILD_blend.json", "REBUILD_region.json") if first == "blend" else ("REBUILD_region.json", "REBUILD_blend.json")
    for fn in order:
        try:
            pr = json.load(open(os.path.join(folder, fn), encoding="utf-8")).get("protect")
        except (OSError, ValueError, TypeError):
            continue
        if pr:
            return ";".join(" ".join("%g" % float(v) for v in b) for b in pr)
    return None


def write_frozen(kit, folder, say=print):
    """keep_frozen.json: the atlas's FROZEN regions whose box meets the edit region (REBUILD_region.json), with the surface file
    the atlas recorded for each and whether the client allowed burying it (buried_ok). `kit rebuild keep` and the region step's
    pre-flight read it; rb_keep keeps every bin where the piece would cut into one of these faces, or bury one without
    buried_ok. Returns the list written (empty when the project has no atlas, or no frozen region meets the edit region)."""
    out = os.path.join(folder, FILES["frozen"]); rows = []
    try:
        rec = json.load(open(os.path.join(folder, FILES["region_rec"]), encoding="utf-8")); w = [float(v) for v in rec.get("window")]
    except (OSError, ValueError, TypeError):
        w = None
    try:
        ad = kit.G.atlas_load(kit.ROOT) or {}
    except Exception:
        ad = {}
    for name, r in (ad.get("regions") or {}).items():
        if str(r.get("edit_status", "")).upper() != "FROZEN": continue
        b = r.get("box")
        if w and b and len(b) == 6 and not (b[0] <= w[1] + 1 and b[1] >= w[0] - 1 and b[2] <= w[3] + 1 and b[3] >= w[2] - 1 and b[4] <= w[5] + 1 and b[5] >= w[4] - 1): continue
        sf = r.get("surface_file") or ""
        sp = sf if os.path.isabs(sf) else os.path.join(kit.ROOT, sf.replace("\\", os.sep).replace("/", os.sep))
        rt = r.get("recreate_tol") or {}
        rows.append({"name": name, "surface": sp, "surface_exists": os.path.isfile(sp), "buried_ok": bool(r.get("buried_ok")), "box": b,
                     "tol": (float(rt.get("mm")) if isinstance(rt, dict) and rt.get("mm") else None)})
    try:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=1)
    except OSError as e:
        say("  keep_frozen.json: NOT written (%s)" % e)
    return rows


def _mirror_decision(folder):
    """the card's symmetry decision recorded at skin-labels (skin\\MIRROR_DECISION.json): the plane, "" = not symmetric, None = none recorded"""
    try:
        return str(json.load(open(os.path.join(folder, "skin", "MIRROR_DECISION.json"), encoding="utf-8")).get("plane", "")).strip()
    except (OSError, ValueError):
        return None


def step_defaults(step, folder, model_of_record):
    """the inputs and outputs a step takes from the job folder when the run does not set them: {lever: value}"""
    P = lambda k: os.path.join(folder, FILES[k])
    d = {"RUN": folder}
    win = _window_of(folder)
    if step == "region":
        d["BODY"] = model_of_record or ""
    elif step in ("arrange", "arrange-m"):
        d["SRC"] = P("content")
        if win: d["WIN"] = win
        pr = _protect_of(folder, "region")
        if pr: d["PROTECT"] = pr
    elif step == "blend":
        # content_base.stl
        # content_base.stl
        base = P("arr") if os.path.isfile(P("arr")) else (os.path.join(folder, "content_base.stl") if os.path.isfile(os.path.join(folder, "content_base.stl")) else P("arr"))
        d.update({"STL": base, "OUT": P("blend"), "WALLS": P("walls")})
        if win: d["WIN"] = win
        pr = _protect_of(folder, "region")
        if pr: d["PROTECT"] = pr
    elif step == "arrange-f":
        d.update({"STL": P("arr_raw"), "OUT": P("arr")})
    elif step == "repair":
        d.update({"STL": P("blend"), "OUT": P("piece")})
        try:
            if int(json.load(open(os.path.join(folder, "REBUILD_blend.json"), encoding="utf-8")).get("KEEP", 0)) == 1:
                d.update({"SLIV": "0.03", "SLIV_A": "0.005"})
        except (OSError, ValueError, TypeError):
            pass
    elif step == "review":
        d.update({"STL": P("piece"), "ORIG": P("content"), "TAG": "piece"})
        if win: d["WIN"] = win
    elif step == "decimate":
        d.update({"STL": P("piece"), "OUT": P("dec")})
    elif step == "fillholes":
        d.update({"STL": P("dec"), "OUT": P("decf")})
    elif step == "finish":
        d.update({"STL": P("decf"), "OUT": P("final")})
    elif step == "brep":
        d.update({"STL": P("final") if os.path.isfile(P("final")) else P("piece"), "OUT": P("brep")})
    elif step == "keep":
        d.update({"PIECE": P("brep"), "ORIG": P("content"), "WINDOW": P("window"), "FROZEN": P("frozen")})
        pr = _protect_of(folder)
        if pr is not None: d["PROTECT"] = pr
    elif step == "reinsert":
        d.update({"BODY": model_of_record or "", "PIECE": P("skin_piece") if os.path.isfile(P("skin_piece")) else P("brep"), "WALLS": P("walls"), "REGION": "none"})
        pr = _protect_of(folder)
        if pr is not None: d["PROTECT"] = pr
    elif step in SKIN:
        d.update({"STL": P("source") if (os.path.isfile(P("source")) or not os.path.isfile(P("piece"))) else P("piece"), "BODY": model_of_record or ""})
        if step == "skin-source": d.pop("STL", None)
        dec = _mirror_decision(folder)
        if step in ("skin-mirror", "skin-network", "skin-build") and dec is not None:
            d["MIRROR"] = dec          # skin-labels
    elif step == "review-body":
        d.update({"BODY": model_of_record or "", "NEW": P("body_new"), "TAG": "body"})
        # the last STEP 2 was a TRIAL
        if os.path.isfile(os.path.join(folder, "TRIAL.json")) and os.path.isfile(os.path.join(folder, "body_trial.brep")):
            d.update({"NEW": os.path.join(folder, "body_trial.brep"), "TAG": "trial"})
        if win: d["WIN"] = win
    d.update(DEFAULTS.get(step, {}))
    return d


def step_outputs(step, env):
    """the files this step declares (renamed .KILLED if the runner kills it)"""
    out = []
    if env.get("OUT"): out.append(env["OUT"])
    run = env.get("RUN", "")
    if step == "region": out += [os.path.join(run, FILES[k]) for k in ("content", "window", "walls", "region_rec")]
    if step == "region" and env.get("KIT_HOME") is None: pass
    if step == "arrange-m": out += [os.path.join(run, FILES["arr_raw"]), os.path.join(run, "REBUILD_arrangement.json")]
    if step == "keep": out += [os.path.join(run, FILES["keep"]), os.path.join(run, "REBUILD_keep.json")]
    if step == "reinsert" and env.get("STEP") == "3": out += [os.path.join(run, FILES["body_new"]), os.path.join(run, "REBUILD_reinsert.json")]
    sk = lambda *n: os.path.join(run, "skin", *n)
    out += {"skin-regions": [sk("regions.npz"), sk("regions.json")], "skin-edges": [sk("edgemap", "edge_classes.json"), sk("edgemap", "edge_measure.json")],
            "skin-points": [sk("points1000.json")], "skin-labels": [sk("patches_labels.npz"), sk("patches_labels.json")],
            "skin-rim": [sk("patches.npz"), sk("patches.json"), sk("frame_owner.json")], "skin-network": [sk("network.brep"), sk("network.json")],
            "skin-frame": [sk("network_frame.brep"), sk("frame.json")],
            # skin-rim  skin-build
            "skin-features": [sk("patches_labels.npz"), sk("patches_labels.json")],
            "skin-wires": [sk("network_frame.brep"), sk("wire_simplify.json"), sk("corners.json"), sk("wires_demote.json"), sk("LINES_carried.json"), sk("preflight.json")],
            "skin-build": [sk("piece_skin.brep"), sk("solid_c.json")]}.get(step, [])
    if step == "reinsert" and env.get("STEP") == "1": out += [os.path.join(run, FILES["wall_caps"])]
    return [p for p in out if p]


def _help(say):
    say(__doc__)
    say("steps (in order - the skin route (31ba, the voxel field shelved): region, skin-source, reinsert STEP=1 (the caps FIRST), skin-regions .. skin-look, reinsert STEP=2-4,")
    say("review-body; the SHELVED steps last, refused without --set SHELVED_OK=\"<why>\"):")
    for k, scr, what, card, fixed in STEPS:
        say("  %-12s %-19s %s%s" % (k, scr, what, ("   CARD: " + ", ".join(card)) if card else ""))
    say("\nevery step takes RUN = the job folder and its inputs from the previous step's outputs (printed as `suggested` - 31an: suggestions, not requirements);")
    say("  kit rebuild judge --job J --what region|keep|layout|wires|skin|points|trial --verdict ok|move|redo --note \"...\" [--face n | --spot box]   the verdict on a look")
    say("  kit rebuild second --job J --what skin [--assign] | --shard k --result <json>               the second reviewer (before a skin verdict)")
    say("  kit rebuild save --job J --tag T    /    kit rebuild restore --job J --tag T                 31av: a build's whole state (layout, wires, piece, their")
    say("      verdicts) - every skin-build that passes saves it; save is for a build made outside the runner; restore puts one back (the live state kept first)")
    say("BODY defaults to the session's model of record. `--set K=V` overrides any of them. BURRITO_STEPS.md has the lever table.")


RECORDS = ("REBUILD_region.json", "REBUILD_arrangement.json", "REBUILD_blend.json", "REBUILD_mesh.json",
           "REBUILD_decimate.json", "REBUILD_brep.json", "REBUILD_keep.json", "REBUILD_reinsert.json", "REBUILD_check.json",
           "REBUILD_source.json")      # skin-source


def _tstr(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def _rec_time(path, rec):
    """R7W fix-built-from: a record's time as (epoch, how) - its own "when" (skin-source writes one), else its file's mtime; (None, why) when neither"""
    w_ = rec.get("when") if isinstance(rec, dict) else None
    if w_:
        try:
            return time.mktime(time.strptime(str(w_).strip()[:19], "%Y-%m-%d %H:%M:%S")), "its own when"
        except (ValueError, OverflowError, TypeError):
            pass
    try:
        return os.path.getmtime(path), "its file's mtime"
    except OSError as e_:
        return None, "no time (%s)" % e_


def _skin_read(folder, *rel):
    """R7W fix-built-from: (the record, None) or (None, why) - a skin record that is absent, unreadable or JSON but no object is SAID, never raised"""
    p_ = os.path.join(folder, *rel); nm_ = "\\".join(rel)
    if not os.path.isfile(p_):
        return None, "%s absent" % nm_
    try:
        with open(p_, encoding="utf-8") as fh_:
            v_ = json.load(fh_)
    except (OSError, ValueError) as e_:
        return None, "%s unreadable (%s)" % (nm_, str(e_)[:80])
    if not isinstance(v_, dict):
        return None, "%s is JSON but not an object (a %s)" % (nm_, type(v_).__name__)
    return v_, None


def _n_of(x):
    """a count: the length of a list / dict, a number as it is, None as None"""
    return len(x) if isinstance(x, (list, tuple, dict)) else x


def _skin_built_from(folder, steps, left_out, left_rule):
    r"""R7W fix-built-from (the plan's F.15 design question; verify-fix-small's field list): WHAT A SKIN PIECE WAS BUILT FROM - read from the job's own
    records (the root's REBUILD_*.json as merged, skin\*.json, skin\review\PIECE_LOOK.json, TRIAL.json, review_body\*.json). The old summary (design
    surfaces, cells, the blend's R / OPEN, the decimation, brep faces, the keep) is the SHELVED voxel chain's: on the agent's accepted b27b it named cells
    9937, blend R 3.0, piece_faces 1796 - records of 10-05 / 10-06 under the 68-face skin piece of 10-16 (L119: no file of an earlier build is read as
    this one's). Every section reads its own files under try / except: a record absent or unreadable is said in the section as "absent", never a crash."""
    S = {"route": "skin"}
    src = steps.get("source") if isinstance(steps.get("source"), dict) else {}
    ctx = {"piece_md5": None}

    def sect(name, fn):
        try:
            S[name] = fn()
        except Exception as e_:      # kit accept
            S[name] = {"absent": "%s could not be read as expected (%s: %s)" % (name, type(e_).__name__, str(e_)[:120])}

    def _region():
        reg_ = steps.get("region")
        if not isinstance(reg_, dict):
            return {"absent": "REBUILD_region.json absent" if reg_ is None else "REBUILD_region.json is not an object"}
        rk_ = ("body", "window", "planes", "walls", "content_mm3", "protect", "grazing_faces", "design_faces_in_planes")
        out_ = {k_: reg_.get(k_) for k_ in rk_}
        out_["not_in_record"] = [k_ for k_ in rk_ if k_ not in reg_]
        cuts_, why_ = _skin_read(folder, "review", "CUTS_REGION.json")
        cm_ = (cuts_ or {}).get("content_md5")
        out_["content_md5_of_cuts"] = cm_ or ("not compared - %s" % (why_ or "review\\CUTS_REGION.json carries no content_md5"))
        out_["same_content_as_source"] = (cm_ == src.get("content_md5")) if (cm_ and src.get("content_md5")) else None
        return out_

    def _source():
        if not src:
            return {"absent": "REBUILD_source.json is not an object"}
        return {k_: src.get(k_) for k_ in ("content_md5", "source_md5", "faces", "triangles", "body_faces_mapped", "unmapped_faces", "when", "tag")}

    def _points():
        pj_, why_ = _skin_read(folder, "skin", "points1000.json")
        if pj_ is None:
            return {"absent": why_}
        return {"NPTS": pj_.get("NPTS"), "kept": _n_of(pj_.get("kept")), "no_points": _n_of(pj_.get("no_points")), "levers": pj_.get("levers"),
                "lever_whys": pj_.get("lever_whys") if "lever_whys" in pj_ else "absent - points1000.json written before 31bq B22 (no box carried its reason)",
                "frame_faces": _n_of(pj_.get("frame_faces")), "frame_faces_no_point": pj_.get("frame_faces_no_point")}

    def _features():
        fj_, why_ = _skin_read(folder, "skin", "features.json")
        if fj_ is None:
            return {"absent": why_}
        mem_ = {str(k_): _n_of(v_) for k_, v_ in fj_.items() if not str(k_).startswith("_")}
        return {"features": len(mem_), "members": mem_,
                "_why": fj_.get("_why") if "_why" in fj_ else "absent - features.json written before 31bq B22 (no feature carried its reason)"}

    def _layout():
        out_ = {}
        pj_, why_ = _skin_read(folder, "skin", "patches.json")
        if pj_ is None:
            out_["faces_by_kind"] = {"absent": why_}
        else:
            kc_ = {}
            for p_ in pj_.get("patches") or []:
                k_ = str(p_.get("kind")) if isinstance(p_, dict) else "?"
                kc_[k_] = kc_.get(k_, 0) + 1
            out_["faces"] = sum(kc_.values()); out_["faces_by_kind"] = kc_
        lk_, why_ = _skin_read(folder, "skin", "LAYOUT_LOCK.json")
        out_["lock"] = {"absent": why_} if lk_ is None else {k_: lk_.get(k_) for k_ in ("when", "tag", "levers", "not_on_record", "backfilled") if k_ in lk_}
        md_, why_ = _skin_read(folder, "skin", "MIRROR_DECISION.json")
        out_["mirror_plane"] = {"absent": why_} if md_ is None else md_.get("plane")
        return out_

    def _wires():
        out_ = {}
        ws_, why_ = _skin_read(folder, "skin", "wire_simplify.json")
        if ws_ is None:
            out_["wire_simplify"] = {"absent": why_}
        else:
            c_ = ws_.get("counts") or {}; g_ = {"LINE": 0, "ARC": 0, "CUBIC": 0, "MULTI": 0}
            for k_, v_ in c_.items():
                kk_ = "MULTI" if str(k_).upper().startswith("MULTI") else str(k_).upper()
                g_[kk_] = g_.get(kk_, 0) + int(v_ or 0)
            out_["skin_edges"] = ws_.get("skin_edges"); out_["counts"] = g_; out_["counts_raw"] = c_
            out_["decided"] = sum(1 for r_ in (ws_.get("chains") or []) if isinstance(r_, dict) and r_.get("decided"))
            out_["lines_file"] = os.path.basename(str(ws_.get("lines")).replace("\\", "/")) if ws_.get("lines") else None
        gj_, why_ = _skin_read(folder, "skin", "guides.json")
        if gj_ is None:
            out_["add"] = {"absent": why_ + " (skin-wires removes it when no line is added)"}
        else:
            r_ = {}
            for x_ in gj_.get("guides") or []:
                k_ = str(x_.get("role")) if isinstance(x_, dict) else "?"
                r_[k_] = r_.get(k_, 0) + 1
            out_["add"] = r_
        fj_, why_ = _skin_read(folder, "skin", "fillets.json")
        if fj_ is None:
            out_["fillets"] = {"absent": why_}
        else:
            out_["fillets"] = [{"line": x_.get("line"), "r": x_.get("r"), "chain": x_.get("chain"), "buried": x_.get("buried")} for x_ in (fj_.get("fillets") or []) if isinstance(x_, dict)]
            out_["room_levers"] = fj_.get("room_levers") if "room_levers" in fj_ else "not recorded - fillets.json written by a skin-wires before 31bq R7W (M8)"
        return out_

    def _piece():
        out_ = {}
        sc_, why_ = _skin_read(folder, "skin", "solid_c.json")
        pf_, whyf_ = _skin_read(folder, "skin", "piece_faces.json")
        keys_ = ("faces", "volume", "valid", "closed", "free_edges", "edge_off_max", "pcurve_gap_max", "self_intersections", "si_self_faces", "edge_gaps_unmeasured",
                 "si_depth_incomplete", "face_sanity", "check_faces")
        if sc_ is None:
            out_["solid"] = {"absent": why_}
        else:
            for k_ in keys_[:11]:
                out_[k_] = sc_.get(k_)
            fs_ = sc_.get("face_sanity")
            out_["face_sanity"] = {"n_bad": fs_.get("n_bad"), "mismatch_noted": _n_of(fs_.get("mismatch_noted")), "volume_mesh": fs_.get("volume_mesh")} if isinstance(fs_, dict) else None
            out_["check_faces"] = _n_of(sc_.get("check_faces"))
            if "wire_clean" in sc_:
                out_["wire_clean"] = sc_.get("wire_clean")
            out_["not_in_record"] = [k_ for k_ in keys_ if k_ not in sc_]
        pp_ = os.path.join(folder, FILES["skin_piece"]); pm_ = None; how_ = "none on record"
        if os.path.isfile(pp_):
            try:
                pm_, how_ = _md5(pp_), "skin\\piece_skin.brep"
            except OSError as e_:
                how_ = "skin\\piece_skin.brep unreadable (%s)" % str(e_)[:60]
        if pm_ is None:
            for nm_, r_ in (("skin\\solid_c.json", sc_), ("skin\\piece_faces.json", pf_)):
                if r_ and r_.get("piece_md5"):
                    pm_, how_ = r_.get("piece_md5"), "%s (the piece file absent)" % nm_; break
        out_["piece_md5"] = pm_; out_["piece_md5_from"] = how_; ctx["piece_md5"] = pm_
        oth_ = [nm_ for nm_, r_ in (("skin\\solid_c.json", sc_), ("skin\\piece_faces.json", pf_)) if r_ and r_.get("piece_md5") and pm_ and r_.get("piece_md5") != pm_]
        if oth_:
            out_["records_of_another_piece"] = oth_
        if pf_ is None:
            out_["rungs"] = {"absent": whyf_}
        else:
            ru_ = {}
            for f_ in pf_.get("faces") or []:
                k_ = str(f_.get("rung")) if isinstance(f_, dict) else "?"
                ru_[k_] = ru_.get(k_, 0) + 1
            out_["rungs"] = ru_
        return out_

    def _look():
        lk_, why_ = _skin_read(folder, "skin", "review", "PIECE_LOOK.json")
        pm_ = ctx["piece_md5"]
        if lk_ is None:
            return "no look of this piece (%s)" % why_
        if not pm_ or lk_.get("md5") != pm_:
            return "no look of this piece - skin\\review\\PIECE_LOOK.json (tag %s) is of piece %s, this piece is %s" % (lk_.get("tag"), str(lk_.get("md5"))[:8], str(pm_)[:8])
        mq_ = lk_.get("mesh_quality"); of_ = lk_.get("original_faces")
        if isinstance(of_, dict):
            nm_ = [g_ for g_ in (of_.get("named") or []) if isinstance(g_, dict)]
            ofo_ = {"measure": "TAKEN" if of_.get("taken") else ("does not apply" if of_.get("applies") is False else "NOT TAKEN"),
                    "named": len(nm_), "named_mm2": [g_.get("named_mm2", g_.get("off_mm2")) for g_ in nm_]}
            if not of_.get("taken"):
                ofo_["why"] = of_.get("why")
        else:
            ofo_ = "NOT TAKEN - the look's record carries no measure of the original's faces (drawn before 31bq B18)"
        return {"mode": lk_.get("mode"), "frames": _n_of(lk_.get("frames")), "tag": lk_.get("tag"),
                "mesh_quality": {"defective": mq_.get("defective"), "cracks": mq_.get("cracks")} if isinstance(mq_, dict) else "absent - a look drawn before THE PIECE VIEW (31bn)",
                "original_faces": ofo_}

    def _trial():
        tj_, why_ = _skin_read(folder, "TRIAL.json"); pm_ = ctx["piece_md5"]
        out_ = {"absent": why_} if tj_ is None else {"done": tj_.get("done"), "accepted": bool(tj_.get("accepted")), "accepted_when": tj_.get("accepted_when"),
                                                     "check": tj_.get("check"), "piece_md5": tj_.get("piece_md5"),
                                                     "same_piece": (tj_.get("piece_md5") == pm_) if (tj_.get("piece_md5") and pm_) else None}
        bm_ = (tj_ or {}).get("body_md5") or (tj_ or {}).get("trial_body_md5")
        sj_, why2_ = _skin_read(folder, "review_body", "SECOND_trial.json")
        if sj_ is None:
            out_["second"] = {"absent": why2_}
        else:
            out_["second"] = {"shards": {str(k_): {"verdict": str(v_.get("verdict", "")).strip().lower(),
                                                   "blockers": sum(1 for d_ in (v_.get("defects") or []) if isinstance(d_, dict) and str(d_.get("severity", "")).strip().lower() == "blocker")}
                                         for k_, v_ in (sj_.get("results") or {}).items() if isinstance(v_, dict)},
                              "of_this_trial": (sj_.get("md5") == bm_) if (bm_ and sj_.get("md5")) else None}
        jj_, why3_ = _skin_read(folder, "review_body", "TRIAL_JUDGED.json")
        out_["judged"] = {"absent": why3_} if jj_ is None else {"verdict": jj_.get("verdict"), "when": jj_.get("when"), "ruling": jj_.get("ruling"),
                                                                "blockers_overruled": _n_of(jj_.get("blockers_overruled")) or 0}
        return out_

    def _gone(fn):
        return ("left out - older than the source (built_from.records_left_out)" if any(x_.get("record") == fn for x_ in left_out) else "%s absent" % fn)

    def _reinsert():
        rei_ = steps.get("reinsert")
        if not isinstance(rei_, dict):
            return {"absent": _gone("REBUILD_reinsert.json")}
        out_ = {k_: rei_.get(k_) for k_ in ("G", "SHRINK", "join", "region", "region_mm3", "expected_mm3", "got_mm3", "seam_widest_mm", "faces", "valid", "mesh_volume_mm3", "dropped_mm3") if k_ in rei_}
        out_["bop_ok"] = rei_.get("bop_ok"); out_["piece_md5"] = rei_.get("piece_md5")
        out_["protect_source"] = rei_.get("protect_source") if "protect_source" in rei_ else "not in REBUILD_reinsert.json - STEP 4 records it (built_from.check.protect_source)"
        out_["not_in_record"] = [k_ for k_ in ("bop_ok", "piece_md5") if k_ not in rei_]
        return out_

    def _check():
        chk_ = steps.get("check")
        if not isinstance(chk_, dict):
            return {"absent": _gone("REBUILD_check.json")}
        ck_ = ("verdict", "refused", "protect", "protect_source", "seam")
        return dict({k_: chk_.get(k_) for k_ in ck_}, not_in_record=[k_ for k_ in ck_ if k_ not in chk_])

    for nm_, fn_ in (("region", _region), ("source", _source), ("points", _points), ("features", _features), ("layout", _layout), ("wires", _wires),
                     ("piece", _piece), ("look", _look), ("trial", _trial), ("reinsert", _reinsert), ("check", _check)):
        sect(nm_, fn_)
    S["tags"] = sorted(set(str(s_.get("tag")) for s_ in steps.values() if isinstance(s_, dict) and s_.get("tag")))
    S["records_left_out"] = list(left_out)
    S["records_left_out_rule"] = left_rule
    return S


def _skin_line(job, S):
    """the dossier's "built from" line of the skin form (R7W fix-built-from)"""
    def g(*ks):
        v_ = S
        for k_ in ks:
            v_ = v_.get(k_) if isinstance(v_, dict) else None
        return "?" if v_ is None or isinstance(v_, dict) else v_
    fl_ = (S.get("wires") or {}).get("fillets") if isinstance(S.get("wires"), dict) else None
    tr_ = S.get("trial") if isinstance(S.get("trial"), dict) else {}
    line = ("built from (skin route): job %s, source %s (%s faces, %s triangles) inside edit region %s; %s faces kept by %s points, %s features; "
            "%s wires (%s decided, %s fillets); the piece %s faces, %s mm3, valid %s, edge gap %s; trial %s; check %s"
            % (job, str(g("source", "content_md5"))[:8], g("source", "faces"), g("source", "triangles"), g("region", "window"), g("points", "kept"), g("points", "NPTS"),
               g("features", "features"), g("wires", "skin_edges"), g("wires", "decided"), len(fl_) if isinstance(fl_, list) else "?", g("piece", "faces"), g("piece", "volume"),
               g("piece", "valid"), g("piece", "edge_off_max"), ("accepted %s" % tr_.get("accepted_when")) if tr_.get("accepted") else "not accepted", g("check", "verdict")))
    if S.get("records_left_out"):
        line += "; %d record(s) older than the source left out (%s)" % (len(S["records_left_out"]), ", ".join("%s %s" % (x_.get("record"), x_.get("tag")) for x_ in S["records_left_out"]))
    return line


def merge_record(kit, job, region=None, say=print):
    """THE REBUILD RECORD - what the accepted piece was BUILT FROM, merged from the chain's per-step REBUILD_*.json into
    ONE `REBUILD.json` in the job folder and, when the region's dossier exists, into `claude_code\\dossier\\<region>\\
    REBUILD.json` with a "built from" line in the dossier's index. Written by `kit accept` (the client, 2026-09-25: the record
    is written on acceptance only, and maintained like the dossier) and by `kit rebuild record --job J` to redo it.
    R7W fix-built-from: when the skin route ran (REBUILD_source.json among the steps) built_from is THE SKIN FORM (_skin_built_from) and every
    REBUILD_*.json OLDER than the source (its own when, else its file's mtime - the voxel era of a restarted job) is LEFT OUT of the steps and named;
    a job without REBUILD_source.json keeps the old (voxel) form.
    Returns (ok, message)."""
    folder = os.path.join(kit.ROOT, "claude_code", "jobs", job)
    steps = {}
    for fn in RECORDS:
        p = os.path.join(folder, fn)
        if os.path.isfile(p):
            try:
                steps[fn[len("REBUILD_"):-len(".json")]] = json.load(open(p, encoding="utf-8"))
            except (OSError, ValueError) as e:
                return False, "%s could not be read (%s)" % (fn, e)
    if not steps:
        return False, "no REBUILD_*.json in %s - nothing of the rebuild chain ran in this job" % folder
    skin_ = "source" in steps
    left_out = []; left_rule = None
    if skin_:
        # REBUILD_source.json
        # REBUILD_region.json
        st_t, st_how = _rec_time(os.path.join(folder, "REBUILD_source.json"), steps["source"])
        left_rule = {"source_when": _tstr(st_t) if st_t is not None else None, "by": st_how,
                     "kept_whatever_its_date": "REBUILD_region.json - the edit region the source was cut from (skin-source tessellates the region's content.brep)"}
        if st_t is not None:
            for fn in RECORDS:
                k_ = fn[len("REBUILD_"):-len(".json")]
                if k_ in ("source", "region") or k_ not in steps:
                    continue
                t_, how_ = _rec_time(os.path.join(folder, fn), steps[k_])
                if t_ is not None and t_ < st_t:
                    left_out.append({"record": fn, "tag": steps[k_].get("tag") if isinstance(steps[k_], dict) else None, "when": _tstr(t_), "by": how_})
                    steps.pop(k_)
        summary = _skin_built_from(folder, steps, left_out, left_rule)
        _rg = summary.get("region") if isinstance(summary.get("region"), dict) else {}
        _pc = summary.get("piece") if isinstance(summary.get("piece"), dict) else {}
        _tr = summary.get("trial") if isinstance(summary.get("trial"), dict) else {}
        msg0 = ("REBUILD.json written in the job: %d step record(s) (%s); built from (skin route): source %s of %s, edit region %s; the piece %s faces, %s mm3, valid %s; trial %s"
                % (len(steps), ", ".join(sorted(steps)), str((summary.get("source") or {}).get("content_md5") or "?")[:8],
                   os.path.basename(str(_rg.get("body"))), _rg.get("window"), _pc.get("faces", "?"), _pc.get("volume", "?"), _pc.get("valid", "?"),
                   ("accepted %s" % _tr.get("accepted_when")) if _tr.get("accepted") else "not accepted"))
        if left_out:
            msg0 += ("; %d record(s) OLDER than the source (%s, %s) LEFT OUT of the steps, named in built_from.records_left_out: %s"
                     % (len(left_out), left_rule["source_when"], st_how, ", ".join("%s (%s, %s)" % (x_["record"], x_.get("tag"), x_["when"]) for x_ in left_out)))
    else:
        reg = steps.get("region", {}); arr = steps.get("arrangement", {}); rei = steps.get("reinsert", {}); bl = steps.get("blend", {})
        ds = arr.get("design_surfaces") or []
        summary = {
            "body": reg.get("body") or rei.get("body"), "window": reg.get("window"), "planes": reg.get("planes"), "walls": reg.get("walls"),
            "content_mm3": reg.get("content_mm3"), "grazing_faces": reg.get("grazing_faces"), "design_faces_in_planes": reg.get("design_faces_in_planes"),
            "design_surfaces_used": len(ds), "surfaces": [{"face": d.get("face"), "kind": d.get("kind"), "area_mm2": d.get("area_mm2"),
                                                           "merged_into_it": d.get("merged_into_it")} for d in ds],
            "cells": arr.get("cells"), "volume_mm3": arr.get("volume_mm3"),
            "blend": {"R": (bl.get("levers") or {}).get("R"), "R_SMALL": (bl.get("levers") or {}).get("R_SMALL"), "OPEN": (bl.get("levers") or {}).get("OPEN"),
                      "added_mm3_full": bl.get("added_mm3_full"), "added_mm3_faded": bl.get("added_mm3_faded")},
            "decimation": (steps.get("decimate") or {}).get("reduction"), "piece_faces": (steps.get("brep") or {}).get("faces"),
            "keep": {k: (steps.get("keep") or {}).get(k) for k in ("rebuilt", "forced_kept", "orig_surface_kept_exact", "region_mm3", "seam_step_mm") if k in (steps.get("keep") or {})},
            "reinsert": {k: rei.get(k) for k in ("G", "SHRINK", "join", "region", "region_mm3", "expected_mm3", "got_mm3", "seam_widest_mm", "faces", "valid", "mesh_volume_mm3", "dropped_mm3") if k in rei},
            "check": {k: (steps.get("check") or {}).get(k) for k in ("verdict", "refused") if k in (steps.get("check") or {})},
            "tags": sorted(set(str(s.get("tag")) for s in steps.values() if s.get("tag"))),
        }
        summary["route"] = "voxel"      # REBUILD_source.json
        msg0 = ("REBUILD.json written in the job: %d step record(s) (%s); built from %d design surface(s) of %s, edit region %s"
                % (len(steps), ", ".join(sorted(steps)), len(ds), os.path.basename(str(summary["body"])), summary["window"]))
    rec = {"job": job, "region": region, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "built_from": summary, "steps": steps}
    out = os.path.join(folder, "REBUILD.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1)
    msg = [msg0]
    try:
        import kit_dossier as D
        idx = D.load(kit.ROOT) or {}
    except Exception:
        idx = {}
    if region and region in idx:
        e = idx[region]; d = os.path.join(kit.ROOT, e["dir"]); os.makedirs(d, exist_ok=True)
        dp = os.path.join(d, "REBUILD.json")
        hist = []
        if os.path.isfile(dp):
            try:
                old = json.load(open(dp, encoding="utf-8")); hist = old.get("history", []) + [{k: old.get(k) for k in ("job", "when", "built_from")}]
            except (OSError, ValueError):
                hist = []
        rec2 = dict(rec); rec2["history"] = hist
        with open(dp, "w", encoding="utf-8") as fh:
            json.dump(rec2, fh, indent=1)
        if skin_:
            line = _skin_line(job, summary)
        else:
            line = ("built from: job %s, %d design surfaces of %s inside edit region %s, %d cells kept (%s dropped as spikes, %s gaps filled), "
                    "blend R %s / OPEN %s (+%s mm3), piece %s faces, reinsert SHRINK %s CLIP_OUT %s -> %s faces, valid %s"
                    % (job, len(ds), os.path.basename(str(summary["body"])), summary["window"], (arr.get("cells") or {}).get("kept", 0),
                       (arr.get("cells") or {}).get("spikes_dropped", "?"), (arr.get("cells") or {}).get("gap_cells_filled", "?"),
                       summary["blend"]["R"], summary["blend"]["OPEN"], summary["blend"]["added_mm3_faded"], summary["piece_faces"],
                       summary["reinsert"].get("SHRINK"), summary["reinsert"].get("CLIP_OUT"), summary["reinsert"].get("faces"), summary["reinsert"].get("valid")))
        try:
            D.add(kit.ROOT, region, "kit accept %s (rebuild record)" % job, line)
        except Exception as e:
            msg.append("the dossier index line was not added (%s)" % e)
        msg.append("dossier %s: REBUILD.json written (%d earlier record(s) kept in history) and the built-from line filed" % (region, len(hist)))
    elif region:
        msg.append("no dossier named %r (kit dossier list) - the record stays in the job; `kit rebuild record --job %s --region <dossier>` files it later" % (region, job))
    else:
        msg.append("no region named - the record stays in the job; `kit atlas assign %s --to <region>` then `kit rebuild record --job %s --region <dossier>` files it" % (job, job))
    return True, "\n  ".join(msg)


def on_accept(job, kit):
    """called by `kit accept <job>` after the apply gate passed: the merge, into the region the atlas assigned the job to"""
    region = None
    try:
        a = kit.G.atlas_assignment(kit.ROOT, job)
        region = (a.get("region") or a.get("to")) if isinstance(a, dict) else (str(a) if a else None)      # no region
    except Exception:
        region = None
    ok, msg = merge_record(kit, job, region)
    print(("kit accept: rebuild record - " if ok else "kit accept: no rebuild record (") + msg + ("" if ok else ")"))
    return ok


JUDGED = {"region": ("review", "CUTS_REGION.json", "REGION_CUTS_JUDGED.json", "content.brep", "content_md5"),
          "keep": ("keep", "CUTS.json", "KEEP_CUTS_JUDGED.json", "keep_region.brep", "region_md5"),
          # skin-rim
          "layout": (os.path.join("skin", "review"), "LAYOUT_LOOK.json", "LAYOUT_JUDGED.json", os.path.join("skin", "patches.json"), "md5"),
          "skin": (os.path.join("skin", "review"), "PIECE_LOOK.json", "PIECE_JUDGED.json", os.path.join("skin", "piece_skin.brep"), "md5"),
          # over the
          "points": (os.path.join("skin", "review"), "POINTS_LOOK.json", "POINTS_JUDGED.json", os.path.join("skin", "points1000.json"), "md5"),
          # promote_trial
          "trial": ("review_body", "TRIAL_LOOK.json", "TRIAL_JUDGED.json", "body_trial.brep", "md5"),
          # skin-wires  over the  skin-build
          "wires": (os.path.join("skin", "review"), "WIRES_LOOK.json", "WIRES_JUDGED.json", os.path.join("skin", "network_frame.brep"), "md5"),
          "look": (os.path.join("skin", "review"), "PIECE_LOOK.json", "LOOK_JUDGED.json", os.path.join("skin", "piece_skin.brep"), "md5")}


def _md5(path):
    import hashlib
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def cuts_verdict(folder, what):
    """(ok, message): is there a verdict 'ok' on the cuts of the CURRENT artefact"""
    sub, cuts_fn, judged_fn, art_fn, _ = JUDGED[what]
    art = os.path.join(folder, art_fn); jp = os.path.join(folder, sub, judged_fn)
    if not os.path.isfile(art):
        return False, "%s is missing" % art_fn
    try:
        j = json.load(open(jp, encoding="utf-8"))
    except (OSError, ValueError):
        return False, "no verdict on the %s's frames (%s\\%s)" % (what, sub, judged_fn)
    if j.get("md5") != _md5(art):
        return False, "the verdict in %s\\%s is for an earlier %s - the cuts changed since; look at the new orbit" % (sub, judged_fn, art_fn)
    if j.get("verdict") != "ok":
        return False, "the %s was judged %r (%s) - fix it and run the step again" % (what, j.get("verdict"), j.get("note", ""))
    return True, "the %s judged ok %s (%s)" % (what, j.get("when", ""), j.get("note", "")[:80])


def _mirror_ok(folder, what, plane):
    """(ok, message): skin\\mirror_<what>.json passed, for this plane, on the CURRENT layout / piece (its md5)"""
    rp = os.path.join(folder, "skin", "mirror_%s.json" % what)
    art = os.path.join(folder, FILES["patches"] if what == "layout" else FILES["skin_piece"])
    try:
        r = json.load(open(rp, encoding="utf-8"))
    except (OSError, ValueError):
        return False, "no mirror check of the %s (skin\\mirror_%s.json)" % (what, what)
    if " ".join(str(r.get("plane", "")).split()).lower() != " ".join(plane.split()).lower():
        return False, "the mirror check of the %s was made across %r, not %r" % (what, r.get("plane"), plane)
    if not os.path.isfile(art) or r.get("md5") != _md5(art):
        return False, "the mirror check of the %s is for an earlier one - the %s changed since" % (what, what)
    if not r.get("pass"):
        return False, "the mirror check of the %s FAILED: %d face(s) with no partner" % (what, len(r.get("unpaired") or []))
    return True, "the %s mirror-checked across %s: %d pairs, none unpaired" % (what, plane, len(r.get("pairs") or []))


# BACK TO THE POINTS THERE
TRIES_MAX = 3
SPOT_MARGIN = 1.0
AFTER_POINTS = ("skin-labels", "skin-features", "skin-rim", "skin-mirror", "skin-network", "skin-frame", "skin-wires", "skin-build", "skin-look")
ROOM_LEVERS = ("TAPER_X", "TAPER_MIN", "FIL_TAPER", "THIN_MM", "CREASE_MIN_DEG", "BURIED_MIN", "BURIED_REACH", "FIL_SMOOTH_MM")


def _restart_path(folder):
    return os.path.join(folder, "skin", "RESTART.json")


def restart_state(folder):
    try:
        st = json.load(open(_restart_path(folder), encoding="utf-8"))
        st.setdefault("spots", []); return st
    except (OSError, ValueError):
        return {"spots": []}


def _restart_save(folder, st):
    os.makedirs(os.path.dirname(_restart_path(folder)), exist_ok=True)
    with open(_restart_path(folder), "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=1)


def _touch(a, b, m=SPOT_MARGIN):
    return all(a[2 * k] - m <= b[2 * k + 1] and b[2 * k] - m <= a[2 * k + 1] for k in range(3))


def _same_spot(a, b, g=0.5):
    """one place: the smaller box lies at least half inside the larger (each grown 0.5 mm so a flat face has a thickness). Neighbouring
    faces' boxes only touch at their border - they stay separate spots (the client: only the places that failed are picked again)"""
    a = [a[0] - g, a[1] + g, a[2] - g, a[3] + g, a[4] - g, a[5] + g]; b = [b[0] - g, b[1] + g, b[2] - g, b[3] + g, b[4] - g, b[5] + g]
    inter = 1.0
    for k in range(3):
        w = min(a[2 * k + 1], b[2 * k + 1]) - max(a[2 * k], b[2 * k])
        if w <= 0: return False
        inter *= w
    va = (a[1] - a[0]) * (a[3] - a[2]) * (a[5] - a[4]); vb = (b[1] - b[0]) * (b[3] - b[2]) * (b[5] - b[4])
    return inter >= 0.5 * min(va, vb)


def _box(b):
    b = [float(v) for v in b]
    return [min(b[0], b[1]), max(b[0], b[1]), min(b[2], b[3]), max(b[2], b[3]), min(b[4], b[5]), max(b[4], b[5])]


def parse_boxes(s_):
    out = []
    for part in str(s_ or "").split(";"):
        v = part.replace(",", " ").split()
        if not v: continue
        if len(v) != 6: raise ValueError("a spot is six numbers \"x0 x1 y0 y1 z0 z1\", not %r" % part.strip())
        out.append(_box(v))
    return out


def _points_inside(folder, box):
    """a digest of the points (and the faces they were given) inside the box - what a re-pick must change"""
    import hashlib
    try:
        P = json.load(open(os.path.join(folder, "skin", "points1000.json"), encoding="utf-8")).get("points") or []
    except (OSError, ValueError):
        return None
    sel = sorted((round(float(q[0]), 3), round(float(q[1]), 3), round(float(q[2]), 3), int(q[3])) for q in P
                 if box[0] <= q[0] <= box[1] and box[2] <= q[1] <= box[3] and box[4] <= q[2] <= box[5])
    return hashlib.md5(json.dumps(sel).encode()).hexdigest() + ":%d" % len(sel)


def _spot_candidates(folder, box):
    """31br G4c: the number of source-triangle CENTROIDS inside the box. The points step picks ONLY centroids (skin-points: the grid, PTS_BOX), so a spot with none has
    nothing to pick (the agent's d13 spots 5 / 9: 4 mm boxes on a free edge of the built piece over a flat face's large triangles - 0 inside; the kit had locked them as points
    spots and no lever could ever change their points). None when the mesh cannot be read (the old rule then stands)."""
    try:
        import numpy as _np
        Z = _np.load(os.path.join(folder, "skin", "regions.npz")); C = Z["Vu"][Z["F"]].mean(axis=1); b = _box(box)
        return int(((C[:, 0] >= b[0]) & (C[:, 0] <= b[1]) & (C[:, 1] >= b[2]) & (C[:, 1] <= b[3]) & (C[:, 2] >= b[4]) & (C[:, 2] <= b[5])).sum())
    except Exception:
        return None


def release_void_spots(folder, say=print):
    """31br G4c: a LOCKED spot whose box holds no source centroid is NOT a points spot - nothing can be picked there, its lock could never clear, and the cause of its
    tries was never the points (the lines or the build; a span failure is a wires try - G4b). Released with the reason, kept in the history; returns the ids released."""
    st = restart_state(folder); freed = []
    for sp in st["spots"]:
        if not sp.get("locked"): continue
        if _spot_candidates(folder, sp["box"]) == 0:
            st.setdefault("history", []).append({"spot": sp["id"], "box": sp["box"], "tries": sp["tries"], "released": time.strftime("%Y-%m-%d %H:%M:%S"),
                                                 "why": "no source-triangle centroid inside the box - nothing to pick there; not a points spot (31br G4c)"})
            sp["locked"] = False; sp["tries"] = []; sp["void"] = True; freed.append(sp["id"])
    if freed:
        st["spots"] = [sp for sp in st["spots"] if sp["tries"] or sp.get("locked")]
        _restart_save(folder, st)
        say("  RESTART : spot(s) %s RELEASED (31br G4c) - no source-triangle centroid lies inside the box, so there is no point to pick there and the lock could never clear;\n"
            "            the failed tries at a spot with nothing to pick were the LINES' or the build's (a span failure is a wires try - G4b), never the points'. No points are owed there." % freed)
    return freed


KIT_FAULT_LINES = (r"does not close end to end", r"NOT VALID", r"WIRE FAILED", r"no face from the wire", r"crosses itself on the",
                   r"NO EDGES", r"no surface", r"Traceback")


def build_kit_faults(out):
    """31bg (the agent's b5 item 4: "the tries counter counts kit failures" - two builds that failed on invalid rung-1 faces and a boundary gap put a
    try on 30 spots; a third would have locked them for a points re-pick that was not the cause): the lines of a skin-build's output that
    are the KIT's failure, not the shape's. A build with any of them is not a try at the free-edge spots."""
    hits = []
    lines_ = out.splitlines() if isinstance(out, str) else (out or [])
    for ln in lines_:
        s_ = str(ln)
        if any(re.search(p_, s_) for p_ in KIT_FAULT_LINES): hits.append(s_.strip()[:140])
    return hits


def kit_fault_faces(lines):
    """31bh (the client: "The point of pushing the agent back to picking new points is to edit the wireframe in such a way that it gets closer to
    successful"): the layout faces the kit lines name ("face 16: ...", "patch  16 ...") - only the free-edge spots at THOSE faces are not counted;
    a spot at a face the agent's own wireframe left folded still counts, in the same build."""
    out = set()
    for ln in lines or []:
        m = re.search(r"\b(?:face|patch)\s+(\d+)", str(ln))
        if m: out.add(int(m.group(1)))
    return out


def record_try(folder, what, artefact_md5, why, boxes, say=print):
    """failed tries at the spots `boxes` (one artefact counts once per spot); three at a spot lock it. Returns the state."""
    st = restart_state(folder)
    if not boxes:
        say("  TRIES   : %s failed but named no place - not counted; the next look names it (judge ... --face <n> | --spot <box>)" % what)
        return st
    for b in boxes:
        b = _box(b)
        hit = [sp for sp in st["spots"] if _same_spot(sp["box"], b)]
        if hit:
            sp = hit[0]
            for o in hit[1:]:
                sp["box"] = [min(sp["box"][0], o["box"][0]), max(sp["box"][1], o["box"][1]), min(sp["box"][2], o["box"][2]), max(sp["box"][3], o["box"][3]),
                             min(sp["box"][4], o["box"][4]), max(sp["box"][5], o["box"][5])]
                sp["tries"] += [t for t in o["tries"] if t["md5"] not in {x["md5"] for x in sp["tries"]}]
                sp["locked"] = sp.get("locked") or o.get("locked"); st["spots"].remove(o)
            sp["box"] = [min(sp["box"][0], b[0]), max(sp["box"][1], b[1]), min(sp["box"][2], b[2]), max(sp["box"][3], b[3]), min(sp["box"][4], b[4]), max(sp["box"][5], b[5])]
        else:
            sp = {"id": max([x["id"] for x in st["spots"]] + [0]) + 1, "box": b, "tries": [], "locked": False}; st["spots"].append(sp)
        if artefact_md5 and any(t["md5"] == artefact_md5 for t in sp["tries"]):
            continue
        sp["tries"].append({"what": what, "md5": artefact_md5, "why": str(why)[:240], "when": time.strftime("%Y-%m-%d %H:%M:%S")})
        if len(sp["tries"]) >= TRIES_MAX and not sp.get("locked") and _spot_candidates(folder, sp["box"]) == 0:
            sp["void"] = True
            say("  TRIES   : spot %d %s - %d failed tries but NO source-triangle centroid inside its box: nothing to pick there, so it is NOT a points spot and is not locked (31br G4c);\n"
                "            the cause is in the lines or the build (the FAIL / SPAN FAILED lines above - a span failure is a wires try, G4b)" % (sp["id"], [round(v, 1) for v in sp["box"]], len(sp["tries"])))
        elif len(sp["tries"]) >= TRIES_MAX and not sp.get("locked"):
            sp["locked"] = True; sp["locked_at"] = time.strftime("%Y-%m-%d %H:%M:%S"); sp["points_at_lock"] = _points_inside(folder, sp["box"])
            say("\n" + "!" * 100 + "\nTHREE FAILED TRIES AT SPOT %d %s - BACK TO THE POINTS THERE, NOW (the client 2026-10-07). Only this spot is re-picked; every point\n"
                "  outside it is kept as it is (\"if 80%% of the point selections were correct it should not be forced to repick those\"):\n"
                "    1. open the SP7d_* close-ups of spot %d (the original's wireframe over the transparent voxel, each point on its face; red = OFF,\n"
                "       magenta = a reinsert-face edge whose face got no point) and decide which points must build which faces THERE;\n"
                "    2. kit rebuild skin-points --job <J> --tag <T> [--set \"PTS_BOX=<inside the spot> [mm] | <why>\"] [--set \"PTS_DROP=<inside the spot> | <why>\"]\n"
                "    3. open every frame POINTS_LOOK.json lists, then kit rebuild judge --job <J> --what points --verdict ok --note \"<which points build which faces there>\"\n"
                "  The tries: %s\n" % (sp["id"], [round(v, 2) for v in sp["box"]], sp["id"], "; ".join("%s: %s" % (t["what"], t["why"][:70]) for t in sp["tries"][-TRIES_MAX:])) + "!" * 100)
        elif not sp.get("locked"):
            say("  TRIES   : spot %d %s - %d of %d failed tries (%s); at %d its points are picked again" % (sp["id"], [round(v, 1) for v in sp["box"]], len(sp["tries"]), TRIES_MAX, what, TRIES_MAX))
    _restart_save(folder, st)
    return st


def spots_passed(folder, failing_boxes, artefact_md5, say=print):
    """a judgement of an artefact: every unlocked spot it does not name passed - its count starts again (the tries are CONSECUTIVE)"""
    st = restart_state(folder); n = 0
    for sp in st["spots"]:
        if sp.get("locked") or not sp["tries"]: continue
        if any(_same_spot(sp["box"], _box(b)) for b in (failing_boxes or [])): continue
        if any(t["md5"] == artefact_md5 for t in sp["tries"]): continue
        st.setdefault("history", []).append({"spot": sp["id"], "box": sp["box"], "tries": sp["tries"], "passed": time.strftime("%Y-%m-%d %H:%M:%S")})
        sp["tries"] = []; n += 1
    st["spots"] = [sp for sp in st["spots"] if sp["tries"] or sp.get("locked")]
    _restart_save(folder, st)
    if n: say("  TRIES   : %d spot(s) not named this time passed - their counts start again" % n)
    return n


def wires_try_faces(out):
    """31br G4b: {layout face: its SPAN FAILED line} for every face whose failed piece carries the agent's added lines ('face 4: SPAN FAILED - piece A of 2 (chains [...], 4 edges, 3 added line(s); ...)') -
    the wires' failure, not the points' (the kit's own remedy line says 'split it with a wire'); 31br G4b (2): the try's record carries that line, not the shell's FAIL line"""
    faces = {}
    for ln in (out.splitlines() if isinstance(out, str) else (out or [])):
        m = re.search(r"face\s+(\d+): SPAN FAILED - piece \S+ of \d+ \(chains \[[^\]]*\], \d+ edges?, (\d+) added line", str(ln))
        if m and int(m.group(2)) > 0: faces.setdefault(int(m.group(1)), re.sub(r"^\s*\d+s\s+", "", str(ln)).strip()[:400])
    return faces


def _box_at_faces(folder, box, faces):
    """31br G4b: is this free-edge spot on one of the faces (its box overlaps the face's patch box, skin\\patches.json)"""
    try:
        PJ = json.load(open(os.path.join(folder, "skin", "patches.json"), encoding="utf-8")).get("patches") or []
    except (OSError, ValueError):
        return False
    for f in faces:
        if f < 0 or f >= len(PJ): continue
        bb = PJ[f].get("box") or PJ[f].get("bbox")
        if not bb or len(bb) != 6: continue
        if box[0] <= bb[1] + 0.5 and box[1] >= bb[0] - 0.5 and box[2] <= bb[3] + 0.5 and box[3] >= bb[2] - 0.5 and box[4] <= bb[5] + 0.5 and box[5] >= bb[4] - 0.5: return True
    return False


def _face_lines_sig(folder, face):
    """31br G4b (3): the signature of the agent's ADDED LINES on this layout face (skin\\guides.json: role / kind / ends / via / trace / why) and of the DECISIONS on its borders
    (wire_simplify.json's chains whose pair holds the face) - the lock at that face releases when it CHANGES, not when skin-wires merely ran again (a tester agent's E2, 2026-10-29)"""
    sig = []
    try:
        G = json.load(open(os.path.join(folder, "skin", "guides.json"), encoding="utf-8")); G = G if isinstance(G, list) else (G.get("entries") or G.get("guides") or [])
        for e in G:
            if isinstance(e, dict) and str(e.get("face")) == str(int(face)):
                sig.append(["add", e.get("role"), e.get("kind"), e.get("ends"), e.get("via"), e.get("trace"), str(e.get("why", ""))[:200]])
    except (OSError, ValueError, TypeError, AttributeError): pass
    try:
        W = json.load(open(os.path.join(folder, "skin", "wire_simplify.json"), encoding="utf-8"))
        for c in (W.get("chains") or []):
            if isinstance(c, dict) and int(face) in [int(x) for x in (c.get("pair") or []) if str(x).lstrip("-").isdigit()] and c.get("decided"):
                sig.append(["chain", c.get("chain"), c.get("rung"), c.get("decided")])
    except (OSError, ValueError, TypeError, AttributeError): pass
    import hashlib
    return hashlib.md5(json.dumps(sig, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12] if sig else "none"


def _network_md5(folder):
    try: return str(json.load(open(os.path.join(folder, "skin", "wire_simplify.json"), encoding="utf-8")).get("network_md5") or "")
    except (OSError, ValueError, TypeError, AttributeError): return ""


def record_wires_try(folder, faces, tag, why, say=print):
    """31br G4b: a failed try of the WIRES at these faces (RESTART.json 'wires': {face: {tries, locked_at, lines_sig, network_md5}}); three at one face lock skin-build until the lines AT THAT FACE change
    (or the preview spans it, or the network changes - wires_refusal); `faces` is {face: its SPAN FAILED line} (G4b (2)) or a list (`why` for all)"""
    st = restart_state(folder); W = st.setdefault("wires", {})
    fl = dict(faces) if isinstance(faces, dict) else {int(f): why for f in faces}
    for f, why_f in sorted(fl.items()):
        e = W.setdefault(str(int(f)), {"tries": []})
        if any(t.get("tag") == tag for t in e["tries"]): continue
        e["tries"].append({"tag": tag, "why": str(why_f or why)[:400], "when": time.strftime("%Y-%m-%d %H:%M:%S")})
        if len(e["tries"]) >= TRIES_MAX:
            e["locked_at"] = time.time(); e["lines_sig"] = _face_lines_sig(folder, f); e["network_md5"] = _network_md5(folder)
            say("\n" + "!" * 100 + "\nTHREE FAILED WIRES TRIES AT FACE %d (31br G4b) - its added lines made a piece the kit could not span three times (%s). The next skin-build is REFUSED until\n"
                "  skin-wires runs again with the lines at face %d CHANGED (split where the surface turns, or give the turning part to the neighbour it faces like) and its PREVIEW spans the face;\n"
                "  the kit's SPAN FAILED lines above name the piece and the remedy. The points there are not the cause and are not re-picked.\n" % (int(f), "; ".join(t["tag"] for t in e["tries"][-TRIES_MAX:]), int(f)) + "!" * 100)
        else:
            say("  TRIES   : face %d - %d of %d failed WIRES tries (the piece's added lines; 31br G4b); at %d skin-build waits for skin-wires with the lines at that face changed" % (int(f), len(e["tries"]), TRIES_MAX, TRIES_MAX))
    _restart_save(folder, st)
    return st


def wires_refusal(folder, step):
    """31br G4b: None, or the refusal of skin-build while a face holds three failed wires tries and nothing at that face changed since. The lock RELEASES when skin-wires ran again (wire_simplify.json
    newer than the lock) AND one of: the lines at that face changed (guides.json's entries on it, its borders' decisions - G4b (3)), the network changed (a new layout: the face numbers are another
    layout's), the PREVIEW of that wires run spans the face (skin\\preflight.json, 31br G1), or the lock predates the signature; a wires run with the face's lines unchanged keeps the lock and says so"""
    if step != "skin-build": return None
    W = (restart_state(folder).get("wires") or {}); lk = {f: e for f, e in W.items() if e.get("locked_at")}
    if not lk: return None
    try: t_w = os.path.getmtime(os.path.join(folder, "skin", "wire_simplify.json"))
    except OSError: t_w = 0
    try: PF = json.load(open(os.path.join(folder, "skin", "preflight.json"), encoding="utf-8")); t_pf = os.path.getmtime(os.path.join(folder, "skin", "preflight.json"))
    except (OSError, ValueError): PF, t_pf = {}, 0
    net_now = _network_md5(folder); still = {}; freed = {}
    for f, e in lk.items():
        la = float(e["locked_at"])
        if t_w <= la: still[f] = (e, "skin-wires has not run since the lock"); continue
        sig_now = _face_lines_sig(folder, f)
        if e.get("lines_sig") is not None and sig_now != e.get("lines_sig"): freed[f] = "the lines at face %s changed (its added lines / its borders' decisions)" % f; continue
        if e.get("network_md5") and net_now and net_now != e.get("network_md5"): freed[f] = "the network changed (a new layout - face %s is another face now)" % f; continue
        if isinstance(PF, dict) and t_pf > la and PF.get("taken") and int(f) not in [int(x) for x in (PF.get("span_failed") or [])] and str(f) in (PF.get("faces") or {}): freed[f] = "the preview of the new wires run spans face %s" % f; continue
        if e.get("lines_sig") is None: freed[f] = "skin-wires ran again (a lock recorded before 31br G4b (3) holds no signature)"; continue
        still[f] = (e, "skin-wires ran again at %s but the lines at face %s are UNCHANGED (its added lines and its borders' decisions - guides.json / wire_simplify.json) and the preview did not span it" % (time.strftime("%H:%M:%S", time.localtime(t_w)), f))
    if freed:
        st = restart_state(folder)
        for f, why in freed.items(): st["wires"][f] = {"tries": [], "released": time.strftime("%Y-%m-%d %H:%M:%S"), "released_why": why, "was": lk[f]["tries"]}
        _restart_save(folder, st)
    if not still: return None
    return ("kit rebuild REFUSED: THREE FAILED WIRES TRIES AT FACE(S) %s (31br G4b) - the pieces its added lines make could not be spanned three times (%s). %s. Run skin-wires again with the\n"
            "  lines at that face CHANGED (split where the surface turns; give the turning part to the neighbour it faces like), read its PREVIEW VERDICT, judge the wires, then build."
            % (", ".join(sorted(still)), "; ".join("face %s: %s" % (f, " / ".join(t["tag"] for t in e["tries"][-TRIES_MAX:])) for f, (e, _w) in still.items()), "; ".join(w for _e, w in still.values())))


# skin-layout
STEP_OWN_WORDS = ("judge", "second", "restore", "reinsert", "review-body", "region", "skin-layout", "skin-lines")
def _route_rows(home=None):
    """THE SKIN ROUTE table's rows of BURRITO_STEPS.md as cell lists [#, command, what, writes] (the ** and ` marks dropped from the command)"""
    try:
        bs = open(os.path.join(home or os.path.dirname(os.path.abspath(__file__)), "..", "BURRITO_STEPS.md"), encoding="utf-8", errors="replace").read()
    except OSError: return []
    i0 = bs.find("## THE SKIN ROUTE"); i1 = bs.find("# HOW IT ACTUALLY RUNS", i0 if i0 >= 0 else 0); out = []
    for l in bs[i0:i1 if i1 > i0 else None].splitlines():
        if not l.startswith("| ") or l.startswith("| #") or l.startswith("|---"): continue
        c = re.split(r"\s\|\s", l.strip().strip("|").strip())
        if len(c) >= 3: out.append([c[0], re.sub(r"\*\*|`", "", c[1]).strip()] + c[2:])
    return out
def step_names(home=None):
    """31ca (R7 D4): every name step_page answers - the pages, the route table's commands, their short forms, the steps' own words"""
    n = set(step_pages_list(home)) | set(STEP_OWN_WORDS)
    for c in _route_rows(home):
        m = re.match(r"(?:kit rebuild\s+)?([a-z][a-z-]*)", c[1])
        if m: n.add(m.group(1))
    n |= {x[5:] for x in n if x.startswith("skin-")}
    return sorted(n)
def _step_alias(step, home=None):
    """31ca (R7 D4): a short name to its step - points -> skin-points, layout -> skin-layout; the steps' own words and a full name as they are"""
    st = (step or "").strip()
    if not st or st.startswith("skin-") or st in STEP_OWN_WORDS: return st
    if "skin-" + st in step_names(home): return "skin-" + st
    return st
def step_page(step, home=None):
    """31br I1 (2026-10-29; the client: 'when an agent moves to make certain steps only then is the pre built process mapped out to them'): the step's ONE PAGE from kit\\rebuild\\STEP_PAGES.md - what to
    look at, what to decide, the levers, what each gate catches, the known limits - printed when the step runs and by `kit howto burrito --step <step>`; nothing is added to the read-in"""
    step = _step_alias(step, home)
    if not step: return ""
    try:
        p = os.path.join(home or os.path.dirname(os.path.abspath(__file__)), "rebuild", "STEP_PAGES.md")
        txt = open(p, encoding="utf-8", errors="replace").read()
        m = re.search(r"^## %s[ \t]*\n.*?(?=^## |\Z)" % re.escape(step), txt, re.M | re.S)
        if m: return "  page    : THE %s PAGE (kit howto burrito --step %s)\n" % (step.upper(), step) + "\n".join("  page    : " + l for l in m.group(0).rstrip().splitlines()[1:])
    except OSError: return ""
    try:
        import textwrap as _tw
        bs = open(os.path.join(home or os.path.dirname(os.path.abspath(__file__)), "..", "BURRITO_STEPS.md"), encoding="utf-8", errors="replace").read()
        i0 = bs.find("## THE SKIN ROUTE"); i1 = bs.find("# HOW IT ACTUALLY RUNS", i0 if i0 >= 0 else 0)
        rows = [l for l in bs[i0:i1 if i1 > i0 else None].splitlines() if l.startswith("| ") and not l.startswith("| #") and not l.startswith("|---")]
        out = []; n_ = 0
        for l in rows:
            cells = re.split(r"\s\|\s", l.strip().strip("|").strip())
            if len(cells) < 3: continue
            cmd = re.sub(r"\*\*|`", "", cells[1]).strip()
            if not (re.match(r"^%s(\s|$|\b)" % re.escape(step), cmd) or (step == "judge" and cmd.startswith("judge --what"))): continue
            n_ += 1; out.append("  page    : THE %s ROW %d (BURRITO_STEPS.md, THE SKIN ROUTE - no page of its own): %s" % (step.upper(), n_, cmd))
            body_ = " ".join(cells[2:]); lines_ = _tw.wrap(body_, 190)
            for chunk in lines_[:12]: out.append("  page    :   " + chunk)
            if len(lines_) > 12: out.append("  page    :   (... the rest of this row: BURRITO_STEPS.md, THE SKIN ROUTE)")
        if out: return "\n".join(out)
        _rr = _route_rows(home); _w = re.compile(r"(?<![\w-])%s(?![\w-])" % re.escape(step))
        for _ci in (1, 2):
            for c_ in _rr:
                if _w.search(re.sub(r"\*\*|`", "", c_[_ci])):
                    out = ["  page    : THE %s STEP - no page of its own - the route table's row: | %s | %s |" % (step.upper(), c_[0], c_[1][:160])]
                    lines_ = _tw.wrap(" ".join(c_[2:]), 190)
                    for chunk in lines_[:12]: out.append("  page    :   " + chunk)
                    if len(lines_) > 12: out.append("  page    :   (... the rest of this row: BURRITO_STEPS.md, THE SKIN ROUTE)")
                    return "\n".join(out)
        return ""
    except OSError: return ""


def step_pages_list(home=None):
    try: return re.findall(r"^## (\S+)", open(os.path.join(home or os.path.dirname(os.path.abspath(__file__)), "rebuild", "STEP_PAGES.md"), encoding="utf-8", errors="replace").read(), re.M)
    except OSError: return []


def restart_refusal(folder, step, say=print):
    """None, or the refusal for a step taken while a spot's restart is owed"""
    release_void_spots(folder, say)      # nothing to pick  released
    lk = [sp for sp in restart_state(folder)["spots"] if sp.get("locked")]
    if not lk:
        return None
    return ("kit rebuild REFUSED: THE POINTS ARE OWED AT %d SPOT(S) - three failed tries there (the client 2026-10-07: three tries, then straight back to the points,\n"
            "  and only where they failed). `%s` waits until the points INSIDE these boxes are picked again and judged:\n%s\n"
            "  kit rebuild skin-points (it keeps every point outside these spots; PTS_BOX / PTS_DROP inside them, read off their SP7d close-ups), open\n"
            "  every frame POINTS_LOOK.json lists, then kit rebuild judge --what points --verdict ok --note \"<which points build which faces there>\""
            % (len(lk), step, "\n".join("    spot %d %s: %s" % (sp["id"], [round(v, 2) for v in sp["box"]], "; ".join("%s (%s)" % (t["what"], t["why"][:50]) for t in sp["tries"][-TRIES_MAX:])) for sp in lk)))


def points_judged(folder, say=print):
    """a points verdict ok: each locked spot whose points were picked again is unlocked; one whose points are the same stays locked; one with nothing to pick is released (31br G4c)"""
    _void = release_void_spots(folder, say)
    st = restart_state(folder); freed, same = [], []
    for sp in st["spots"]:
        if not sp.get("locked"): continue
        now = _points_inside(folder, sp["box"])
        if now is not None and now != sp.get("points_at_lock"):
            st.setdefault("history", []).append({"spot": sp["id"], "box": sp["box"], "tries": sp["tries"], "unlocked": time.strftime("%Y-%m-%d %H:%M:%S")})
            sp["locked"] = False; sp["tries"] = []; freed.append(sp["id"])
        else:
            same.append(sp["id"])
    st["spots"] = [sp for sp in st["spots"] if sp["tries"] or sp.get("locked")]
    _restart_save(folder, st)
    if same and not freed:
        return False, "the points INSIDE spot(s) %s are the SAME as when their tries ran out - pick them again there (PTS_BOX / PTS_DROP inside the box)" % same
    _vs = ("spot(s) %s RELEASED - nothing to pick inside them (31br G4c)" % _void) if _void else ""
    if freed: return True, _vs + ("; " if _vs else "") + "spot(s) %s picked again - unlocked%s" % (freed, ("; spot(s) %s still the same - still locked" % same) if same else "")
    return True, _vs or "no spot was locked"


def spot_boxes(folder, what, faces=None, spots=None):
    """the boxes a judgement names: --spot boxes as given; --face numbers as the face's box (a layout's from skin\\patches.json, a piece's from
    skin\\piece_faces.json) grown 1 mm"""
    out = list(parse_boxes(spots)) if spots else []
    for f in [x for x in str(faces or "").replace(",", " ").split() if x.strip()]:
        try:
            if what == "layout":
                recs = json.load(open(os.path.join(folder, FILES["patches"]), encoding="utf-8"))["patches"]
                r = next(r for r in recs if int(r["patch"]) == int(f))
            else:
                recs = json.load(open(os.path.join(folder, "skin", "piece_faces.json"), encoding="utf-8"))["faces"]
                r = next(r for r in recs if int(r["face"]) == int(f))
            b = r.get("bbox")
            if not b: raise KeyError("no bbox")
            out.append([b[0] - 1, b[1] + 1, b[2] - 1, b[3] + 1, b[4] - 1, b[5] + 1])
        except (OSError, ValueError, KeyError, StopIteration):
            raise ValueError("face %s has no box on record (%s) - give the place as --spot \"x0 x1 y0 y1 z0 z1\"" % (f, "skin\\patches.json" if what == "layout" else "skin\\piece_faces.json"))
    return out


# DIFFERENT
# skin-build
ROUNDS_MAX = 5


def record_round(folder, md5_, boxes, note, say=print):
    st = restart_state(folder); rd = st.setdefault("rounds", [])
    if any(r.get("md5") == md5_ for r in rd):
        return st
    rd.append({"md5": md5_, "boxes": [_box(b) for b in boxes], "note": str(note)[:200], "when": time.strftime("%Y-%m-%d %H:%M:%S")})
    if len(rd) < ROUNDS_MAX:
        _restart_save(folder, st)
        say("  ROUNDS  : layout round %d of %d without a build that passes - at %d every place the rounds named goes back to the points" % (len(rd), ROUNDS_MAX, ROUNDS_MAX))
        return st
    now = time.strftime("%Y-%m-%d %H:%M:%S"); named = []
    for r in rd:
        for b in r["boxes"]:
            hit = [sp for sp in st["spots"] if _same_spot(sp["box"], b)]
            if hit:
                sp = hit[0]; sp["box"] = [min(sp["box"][0], b[0]), max(sp["box"][1], b[1]), min(sp["box"][2], b[2]), max(sp["box"][3], b[3]), min(sp["box"][4], b[4]), max(sp["box"][5], b[5])]
            else:
                sp = {"id": max([x["id"] for x in st["spots"]] + [0]) + 1, "box": list(b), "tries": [], "locked": False}; st["spots"].append(sp)
            if not any(t.get("md5") == r["md5"] for t in sp["tries"]):
                sp["tries"].append({"what": "layout round", "md5": r["md5"], "why": r["note"], "when": r["when"]})
            if not sp.get("locked"):
                sp["locked"] = True; sp["locked_at"] = now; sp["points_at_lock"] = _points_inside(folder, sp["box"])
            named.append(sp["id"])
    st.setdefault("history", []).append({"rounds": rd, "locked": sorted(set(named)), "when": now})
    st["rounds"] = []
    _restart_save(folder, st)
    say("\n" + "!" * 100 + "\n" + str(ROUNDS_MAX) + " LAYOUT ROUNDS WITHOUT A BUILD THAT PASSES - BACK TO THE POINTS at spot(s) %s, NOW (the client 2026-10-07: \"It decided to split a section\n"
        "  instead of going back to point picking and then it looped in infinite failure\"). Every other point is kept; at those places:\n"
        "    1. open the SP7d_* close-ups (the original's wireframe over the transparent voxel, each point on its face) and decide which points build which faces there;\n"
        "    2. kit rebuild skin-points --job <J> --tag <T> [--set \"PTS_BOX=<inside the spot> [mm] | <why>\"] [--set \"PTS_DROP=<inside the spot> | <why>\"]\n"
        "    3. open every frame POINTS_LOOK.json lists, then kit rebuild judge --job <J> --what points --verdict ok --note \"<which points build which faces there>\"\n"
        "  The rounds: %s\n" % (sorted(set(named)), "; ".join(r["note"][:70] for r in rd)) + "!" * 100)
    return st


def restart_on_new_source(folder, say=print):
    """31bc - A NEW SOURCE MESH IS A RESTART (the client 2026-10-08: "you are restarting the edit. ignore the locks. nothing is good yet"; the agent's items 2a-c: skin-labels
    on the new B-rep source was refused as an undo of the voxel-era layout ok, the voxel-era LAYOUT_LOCK still pinned the levers, RESTART.json still held
    the voxel trials' tries). When skin-source writes a source.stl whose md5 is not the one the records were made on: every standing ok (layout, wires,
    look, skin, points, trial) is SUPERSEDED (the record kept, its verdict "superseded"), LAYOUT_LOCK.json and RESTART.json are set aside (renamed with the
    time), the layout rounds start again, and the new source's md5 is written into RESTART.json so a re-run of skin-source on the same content changes
    nothing. Returns the number of records superseded, or -1 when the source is unchanged."""
    try:
        src = json.load(open(os.path.join(folder, "REBUILD_source.json"), encoding="utf-8")).get("source_md5")
    except (OSError, ValueError):
        return -1
    if not src: return -1
    st = restart_state(folder)
    if st.get("source_md5") == src: return -1
    stamp = time.strftime("%H%M%S"); n = 0
    for w_, (sub, _c, judged_fn, _a, _k) in JUDGED.items():
        if w_ in ("region", "keep"): continue      # content.brep
        jp = os.path.join(folder, sub, judged_fn)
        if not os.path.isfile(jp): continue
        try:
            j = json.load(open(jp, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if j.get("verdict") in ("superseded",): continue
        j = dict(j, verdict="superseded", superseded=time.strftime("%Y-%m-%d %H:%M:%S"), note=(j.get("note") or "") + " [superseded: a new source mesh %s - the restart]" % src[:8])
        with open(jp, "w", encoding="utf-8") as fh: json.dump(j, fh, indent=1)
        n += 1
    for fn in ("LAYOUT_LOCK.json", "RESTART.json"):
        fp = os.path.join(folder, "skin", fn)
        if os.path.isfile(fp):
            try: os.replace(fp, os.path.join(folder, "skin", fn.replace(".json", "_superseded_%s.json" % stamp)))
            except OSError: pass
    try: rounds_reset(folder, lambda *a, **k: None)
    except Exception: pass
    st = {"spots": [], "source_md5": src, "restarted": time.strftime("%Y-%m-%d %H:%M:%S")}
    _restart_save(folder, st)
    say("  RESTART : a NEW source mesh (%s) - %d standing verdict(s) superseded, the layout lock and the tries set aside (skin\\*_superseded_%s.json), the layout\n"
        "            rounds start again. The first layout judged ok on this source sets a new lock. (the client 2026-10-08: \"you are restarting the edit. ignore the locks.\")"
        % (src[:8], n, stamp))
    return n


def supersede_for_kit_update(folder, why, say=print):
    """31bf - A KIT UPDATE RE-MAKES THE LAYOUT: `kit rebuild skin-labels --supersede "<why>"`. The standing oks of the layout and everything built
    on it (wires, the piece's look / skin, the trial) are SUPERSEDED the way 31bc's new-source restart supersedes them (the record kept, its
    verdict "superseded", the reason in its note) - no strike (the layout is not undone on a number: the kit that made it changed) and no
    layout round; the lock, the tries and the points' ok stay (the levers and the points are not what changed). The kit maintainer's 31bf test:
    the real job's b4 layout was judged ok at rounds 2 of 3 - a redo verdict on a kit defect would have been the third round and sent the agent back to
    the points. Returns the number of records superseded."""
    n = 0; names = []
    for w_, (sub, _c, judged_fn, _a, _k) in JUDGED.items():
        if w_ in ("region", "keep", "points"): continue
        jp = os.path.join(folder, sub, judged_fn)
        if not os.path.isfile(jp): continue
        try:
            j = json.load(open(jp, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if j.get("verdict") != "ok": continue
        j = dict(j, verdict="superseded", superseded=time.strftime("%Y-%m-%d %H:%M:%S"), note=(j.get("note") or "") + " [superseded: a kit update or the client's word on the design - %s]" % str(why)[:160])
        with open(jp, "w", encoding="utf-8") as fh: json.dump(j, fh, indent=1)
        n += 1; names.append(w_)
    say("  SUPERSEDE: a kit update or the client's word on the design (%s) - %d standing verdict(s) superseded (%s; the records kept); no strike, no layout round; the lock, the tries and\n"
        "            the points' ok stay. The layout is judged again on its new pictures. (31br A2: a decision from outside the pictures - the client's instruction, recorded here verbatim - re-makes a judged layout as a kit update does.)" % (str(why)[:120], n, ", ".join(names) or "none"))
    return n


def rounds_reset(folder, say=print):
    st = restart_state(folder)
    if st.get("rounds"):
        n = len(st["rounds"]); st["rounds"] = []; _restart_save(folder, st)
        say("  ROUNDS  : a build passed - the %d layout round(s) before it start again" % n)


# skin-labels
# skin-features  skin-rim  recorded
# skin-wires
# FEATURES
# skin-features
# left FREE
# live layout
LOCKED_LEVERS = {
    "skin-labels": ("A_NOISE", "BAND", "BAR_MM", "CREASE_DEG", "CROSS_MIN_MM2", "FRAG_MM2", "ISLAND_MM2", "MASTER", "MIRROR", "NO_BANDS", "ON_MM",
                    "OPEN_MM", "ORIG_FRAC", "ORIG_MIN", "SMOOTH_IT", "SMOOTH_R", "WRAP_STRENGTH", "ABSORB_MM2", "ABSORB_FRAC"),
    "skin-features": ("MAX_AREA", "MAX_SPREAD", "MIN_BORDER", "SMOOTH_DEG", "STRIP_HALF", "TINY", "UNITE", "UNITE_DEG", "UNITE_MM", "THIN_MM"),
    "skin-rim": ("REACH_MM", "RIM_MM")}
_LAYOUT_FILE = {"skin-labels": ("patches_labels_raw.json", "patches_labels.json"), "skin-features": ("patches_labels.json", "patches_labels.json"),
                "skin-rim": ("patches.json", "patches.json")}


def _lock_path(folder):
    return os.path.join(folder, "skin", "LAYOUT_LOCK.json")


def layout_lock(folder):
    try:
        return json.load(open(_lock_path(folder), encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _layout_env(folder, step):
    """the env record of the run that made this step's LIVE layout file (its tag's copy has the live file's md5), or (None, None)"""
    live_n, tag_n = _LAYOUT_FILE[step]; live = os.path.join(folder, "skin", live_n)
    if not os.path.isfile(live):
        return None, None
    m = _md5(live); recs = []
    for fn in os.listdir(folder):
        if fn.startswith("env_%s_" % step) and fn.endswith(".json"):
            try:
                recs.append(dict(json.load(open(os.path.join(folder, fn), encoding="utf-8")), _file=fn))
            except (OSError, ValueError, TypeError):
                pass
    recs = sorted(recs, key=lambda r: str(r.get("_when", "")), reverse=True)
    for r in recs:
        tp = os.path.join(folder, "tags", str(r.get("_tag", "")), tag_n)
        if os.path.isfile(tp) and _md5(tp) == m:
            return r["_file"], r
    # NOT on record  skin-labels  live layout
    if recs:
        r = dict(recs[0]); r["_by_time"] = True
        return r["_file"], r
    return None, None


def write_layout_lock(folder, tag, say=print):
    """at the FIRST layout judged ok: the section-wide levers it was made with, per step; a step whose run is not on record is said, not guessed"""
    if layout_lock(folder):
        return None
    rec = {"when": time.strftime("%Y-%m-%d %H:%M:%S"), "tag": tag, "levers": {}, "from": {}, "not_on_record": []}
    for step, levs in LOCKED_LEVERS.items():
        fn, r = _layout_env(folder, step)
        if r is None:
            rec["not_on_record"].append(step); continue
        rec["from"][step] = fn + (" (by time: the newest run of the step - no tag copy matched the live file)" if r.get("_by_time") else "")
        rec["levers"][step] = {k: (None if r.get(k) is None else str(r.get(k))) for k in levs}
    os.makedirs(os.path.dirname(_lock_path(folder)), exist_ok=True)
    with open(_lock_path(folder), "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1)
    say("  LOCKED  : the layout's section-wide settings are fixed from this first ok (skin\\LAYOUT_LOCK.json: %s) - from now a face changes through its\n"
        "            own points (skin-points PTS_BOX / PTS_DROP), its lines through skin-wires LINES / RAILS%s"
        % ("; ".join("%s %s" % (s, ", ".join("%s=%s" % (k, v) for k, v in sorted(d.items()) if v is not None) or "its own defaults") for s, d in rec["levers"].items()),
           ("; NOT on record (made outside the runner, or before 31av) - not locked: %s" % ", ".join(rec["not_on_record"])) if rec["not_on_record"] else ""))
    return rec


def lock_backfill(folder, lk, step, say=print, write=True):
    """R7W tester-findings (T3 3.4 case 3): the levers of LOCKED_LEVERS[step] the lock `lk` holds no key for (a lever that joined the table after the lock was
    written - THIN_MM at 31bq R7c) are BACKFILLED from the env record of the run that made the LIVE layout (_layout_env: the tag copy with the live file's md5,
    else the newest run on record - said which), with a note in the lock (`backfilled`), and the lock is written (write=False on --plan: said, not written);
    no run of the step on record -> said by name and left free. Returns [(lever, value, source)] backfilled; `lk` is updated in place."""
    levs = (lk.get("levers") or {}).get(step) if isinstance(lk, dict) else None
    if not isinstance(levs, dict): return []
    miss = [k for k in LOCKED_LEVERS.get(step, ()) if k not in levs]
    if not miss: return []
    fn, r = _layout_env(folder, step)
    if r is None:
        say("  LOCK    : %s %s locked since this job's lock was written (%s, tag %s) - NO run of %s on record made the live layout: left FREE, not locked (R7W tester-findings)"
            % (step, ", ".join(miss), lk.get("when"), lk.get("tag"), step))
        return []
    src = fn + (" (by time: the newest run of the step on record - no tag copy matched the live layout file)" if r.get("_by_time") else " (the run that made the live layout: its tag copy has the live file's md5)")
    done = []
    for k in miss:
        v = None if r.get(k) is None else str(r.get(k)); levs[k] = v; done.append((k, v, src))
    now_ = time.strftime("%Y-%m-%d %H:%M:%S")
    lk.setdefault("backfilled", []).extend({"step": step, "lever": k, "value": v, "from": src, "when": now_,
                                            "why": "the lock (%s) was written before %s joined LOCKED_LEVERS - taken from the run that made the live layout (R7W tester-findings)" % (lk.get("when"), k)} for k, v, _s in done)
    say("  LOCK    : BACKFILLED %s %s from %s - the lock (%s, tag %s) was written before %s joined the locked levers (31bq R7c); locked from now as the others%s"
        % (step, ", ".join("%s=%s" % (k, "the script's own value (not set)" if v is None else v) for k, v, _s in done), src, lk.get("when"), lk.get("tag"),
           "it" if len(done) == 1 else "they", "" if write else " (--plan: the lock is NOT written)"))
    if write:
        try:
            with open(_lock_path(folder), "w", encoding="utf-8") as fh: json.dump(lk, fh, indent=1)
        except OSError as e_:
            say("  LOCK    : the backfilled lock was NOT written (%s) - this run takes the values; the next one backfills again" % e_)
    return done


def _same_val(a, b):
    if a is None or b is None:
        return a is None and b is None
    try:
        return abs(float(a) - float(b)) <= 1e-12 * max(1.0, abs(float(a)))
    except (TypeError, ValueError):
        return " ".join(str(a).replace(",", " ").lower().split()) == " ".join(str(b).replace(",", " ").lower().split())


def room_levers_check(folder, env):
    """31bq R7W (M8 - THE OPEN LIST v2, D1 1 / B1 8): THE ROOM LEVERS ARE ONE DECISION. skin-wires records the levers its room line estimated with
    (skin\\fillets.json "room_levers": each lever's value as read and the default the wires and the build share when it is unset); a skin-build whose own
    levers differ would build to another rule than the one the agent judged the wires' 'it fits' / 'lower R' lines on (the wires had taken the PREVIOUS
    build's levers - R5e / R7c - and nothing on the build side compared them). Returns (ok, line): ok False = refuse (the line names every lever that
    differs, both values); ok None = NOT TAKEN (no record - said, never a pass and never a refusal); ok True = they agree (or no fillet is decided)"""
    p_ = os.path.join(folder, "skin", "fillets.json")
    if not os.path.isfile(p_): return True, ""
    try:
        fj_ = json.load(open(p_, encoding="utf-8"))
    except (OSError, ValueError) as ex_:
        return None, "the wires' room levers NOT TAKEN - skin\\fillets.json could not be read (%s)" % str(ex_)[:60]
    if not (fj_.get("fillets") or []): return True, ""
    rl_ = fj_.get("room_levers")
    if not isinstance(rl_, dict) or not rl_:
        return None, ("the wires' room levers NOT TAKEN - skin\\fillets.json (tag %s) was written by a skin-wires before 31bq R7W and records none: its room "
                      "lines may have estimated with other levers than this build's - skin-wires again records them" % fj_.get("tag"))
    bad_ = []; same_ = []; unrec_ = []
    for k_ in ROOM_LEVERS:
        r_ = rl_.get(k_)
        if not isinstance(r_, dict): unrec_.append(k_); continue
        mine_ = str(env.get(k_) or "").strip() or str(r_.get("default", "")).strip()
        theirs_ = str(r_.get("value", "")).strip()
        (same_ if _same_val(mine_, theirs_) else bad_).append((k_, theirs_, mine_))
    if bad_:
        return False, ("THE ROOM LEVERS DIFFER - the wires' room line (skin-wires tag %s, skin\\fillets.json) estimated with %s where this build runs %s: its 'it fits' / "
                       "'lower R' lines are not this build's. EITHER skin-wires again with the build's levers (--set %s - the lines are not touched, the room is "
                       "estimated again) OR this build with the wires' (--set %s). (31bq R7W, D1 / B1: the room levers are one decision)"
                       % (fj_.get("tag"), ", ".join("%s %s" % (k_, a_) for k_, a_, b_ in bad_), ", ".join("%s %s" % (k_, b_) for k_, a_, b_ in bad_),
                          " ".join("%s=%s" % (k_, b_) for k_, a_, b_ in bad_), " ".join("%s=%s" % (k_, a_) for k_, a_, b_ in bad_)))
    return True, ("the build's room levers agree with the wires' room line (skin-wires tag %s: %s)%s"
                  % (fj_.get("tag"), ", ".join("%s %s" % (k_, a_) for k_, a_, b_ in same_), ("; not on its record: %s" % ", ".join(unrec_)) if unrec_ else ""))


# over the  skin-build
# kit rebuild
# kit rebuild
STATE_FILES = ("points1000.json", "points_faces.json", "patches_labels.npz", "patches_labels.json", "patches_labels_raw.npz", "patches_labels_raw.json",
               "features.json", "MIRROR_DECISION.json", "patches.npz", "patches.json", "frame_owner.json", "mirror_layout.json", "network.brep",
               "network.json", "network_frame.brep", "network_frame_raw.brep", "frame.json", "wire_simplify.json", "corners.json", "LINES_carried.json",
               "wires_demote.json", "piece_skin.brep", "piece_faces.json", "solid_c.json", "build_c.json", "mirror_piece.json",
               "review/LAYOUT_JUDGED.json", "review/WIRES_JUDGED.json", "review/POINTS_JUDGED.json", "review/PIECE_JUDGED.json", "review/SECOND_skin.json",
               "review/LAYOUT_LOOK.json", "review/WIRES_LOOK.json", "review/PIECE_LOOK.json", "review/POINTS_LOOK.json", "review/LOOK_JUDGED.json", "review/FACES_LOOKED.json",
               "preflight.json", "guides.json", "guides.brep", "fillets.json")
LOOK_RECORDS = ("review/LAYOUT_LOOK.json", "review/WIRES_LOOK.json", "review/PIECE_LOOK.json", "review/POINTS_LOOK.json")
FRAME_MAX = 8 * 1024 * 1024


def _look_frames(folder, rel):
    """31br A2: the frame files a *_LOOK.json lists, as (state key, path) - the record's own folder (skin\\review; a look_at frame under look\\)"""
    p = os.path.join(folder, "skin", *rel.split("/"))
    try: rec = json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError): return []
    out = []
    for f in (rec.get("frames") or []) if isinstance(rec, dict) else []:
        f = str(f).replace("\\", "/").lstrip("/")
        if not f.lower().endswith(".png") or ".." in f: continue
        out.append(("review/" + f, os.path.join(folder, "skin", "review", *f.split("/"))))
    return out


def save_state(folder, tag, say=print, quiet=False):
    sk = os.path.join(folder, "skin"); store = os.path.join(folder, "tags", "_states"); files = {}
    os.makedirs(store, exist_ok=True)
    for rel in STATE_FILES:
        p = os.path.join(sk, *rel.split("/"))
        if not os.path.isfile(p): continue
        nm = _md5(p) + os.path.splitext(p)[1]; dst = os.path.join(store, nm)
        if not os.path.isfile(dst): shutil.copy2(p, dst)
        files[rel] = nm
    big = []
    for rel in LOOK_RECORDS:
        if rel not in files: continue
        for key, fp in _look_frames(folder, rel):
            if key in files or not os.path.isfile(fp): continue
            if os.path.getsize(fp) > FRAME_MAX: big.append(key); continue
            nm = _md5(fp) + os.path.splitext(fp)[1]; dst = os.path.join(store, nm)
            if not os.path.isfile(dst): shutil.copy2(fp, dst)
            files[key] = nm
    if big and not quiet: say("  STATE   : %d frame(s) over %d MB not kept in the state: %s" % (len(big), FRAME_MAX // (1024 * 1024), ", ".join(big[:4])))
    td = os.path.join(folder, "tags", tag); os.makedirs(td, exist_ok=True)
    pp = os.path.join(sk, "piece_skin.brep")
    with open(os.path.join(td, "STATE.json"), "w", encoding="utf-8") as fh:
        json.dump({"tag": tag, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "piece_md5": _md5(pp) if os.path.isfile(pp) else None, "files": files}, fh, indent=1)
    if not quiet:
        say("  STATE   : the build's whole state (%d files: points, layout, feature map, wires, piece, their verdicts) kept as tags\\%s\\STATE.json - "
            "`kit rebuild restore --job <J> --tag %s` puts it back" % (len(files), tag, tag))
    return files


def save_cmd(args, kit, say=print):
    """kit rebuild save --job <J> --tag <T>   the live skin state kept as tags\\<T>\\STATE.json (a build made outside the runner)"""
    job = kit._opt(args, "--job"); tag = kit._opt(args, "--tag")
    if not job or not tag or not re.match(r"^[A-Za-z0-9_-]+$", tag):
        say(save_cmd.__doc__); return 2
    folder = os.path.join(kit.ROOT, "claude_code", "jobs", job)
    if not os.path.isdir(os.path.join(folder, "skin")):
        say("kit rebuild save REFUSED: %s has no skin\\ folder - nothing to save" % folder); return 2
    files = save_state(folder, tag, say)
    log_row(folder, tag, "save", {}, "the skin state kept (%d files)" % len(files), 0)
    return 0


def restore_cmd(args, kit, say=print):
    """kit rebuild restore --job <J> --tag <T> [--release-spots "<why>"]   put a build's whole state back (tags\\<T>\\STATE.json); the live state is kept first;
    --release-spots releases the points spots a LATER build locked, into RESTART.json's history with your reason (31bw K34: a return to an older state on purpose)"""
    job = kit._opt(args, "--job"); tag = kit._opt(args, "--tag")
    if not job or not tag:
        say(restore_cmd.__doc__); return 2
    folder = os.path.join(kit.ROOT, "claude_code", "jobs", job); sk = os.path.join(folder, "skin")
    try:
        rec = json.load(open(os.path.join(folder, "tags", tag, "STATE.json"), encoding="utf-8"))
    except (OSError, ValueError):
        say("kit rebuild restore REFUSED: no saved state for tag %s (tags\\%s\\STATE.json) - every skin-build that passes saves one since 31av;\n"
            "  a build made outside the runner: `kit rebuild save --job %s --tag <its tag>` right after it" % (tag, tag, job)); return 2
    lk = [sp["id"] for sp in restart_state(folder)["spots"] if sp.get("locked")]
    if lk:
        _rel = (kit._opt(args, "--release-spots") or "").strip()      # 31bw K34  released
        if len(_rel) < 12:
            say("kit rebuild restore REFUSED: the points are owed at spot(s) %s (the restart) - a restore would bring back the points being replaced there.\n"
                "  Pick them first (skin-points, then judge --what points) - or, to go back to a state OLDER than these locks on purpose, `--release-spots \"<why>\"` (twelve characters at least):\n"
                "  the locks are released into RESTART.json's history with your reason, and the restore goes on (31bw K34)." % lk); return 2
        st_ = restart_state(folder)
        for sp in st_["spots"]:
            if sp.get("locked"):
                st_.setdefault("history", []).append({"spot": sp["id"], "box": sp.get("box"), "tries": sp.get("tries"), "released": time.strftime("%Y-%m-%d %H:%M:%S"),
                                                      "why": "restore --tag %s on the agent's word: %s (31bw K34)" % (tag, _rel)})
                sp["locked"] = False; sp["tries"] = []
        st_["spots"] = [sp for sp in st_["spots"] if sp.get("tries") or sp.get("locked")]
        _restart_save(folder, st_)
        say("  RESTART : spot(s) %s RELEASED on your word for this restore (31bw K34) - %s; their tries are in RESTART.json's history" % (lk, _rel))
    store = os.path.join(folder, "tags", "_states")
    miss = [rel for rel, nm in rec["files"].items() if not os.path.isfile(os.path.join(store, nm))]
    if miss:
        say("kit rebuild restore REFUSED: the saved state is incomplete - missing from tags\\_states\\: %s" % ", ".join(miss[:6])); return 2
    stamp = "_live_" + time.strftime("%Y%m%d_%H%M%S")
    save_state(folder, stamp, say, quiet=True)
    put = rm = 0
    live_frames = {k_ for rel in LOOK_RECORDS for k_, _p in _look_frames(folder, rel)}
    for rel in STATE_FILES:
        live = os.path.join(sk, *rel.split("/"))
        if rel in rec["files"]:
            os.makedirs(os.path.dirname(live), exist_ok=True); shutil.copy2(os.path.join(store, rec["files"][rel]), live); put += 1
        elif os.path.isfile(live):
            os.remove(live); rm += 1
    fput = 0
    for key, nm in rec["files"].items():
        if not (key.startswith("review/") and key.lower().endswith(".png")): continue
        live = os.path.join(sk, *key.split("/")); os.makedirs(os.path.dirname(live), exist_ok=True); shutil.copy2(os.path.join(store, nm), live); fput += 1; live_frames.discard(key)
    frm = 0
    for key in sorted(live_frames):
        try: os.remove(os.path.join(sk, *key.split("/"))); frm += 1
        except OSError: pass
    old_state = not any(k_ in rec["files"] for k_ in LOOK_RECORDS)
    vd = [n.split("/")[-1].replace("_JUDGED.json", "").lower() for n in rec["files"] if n.startswith("review/") and n.endswith("_JUDGED.json")]
    log_row(folder, tag, "restore", {}, "the state of %s put back (%d files; %d removed); the live state kept as tags\\%s" % (tag, put, rm, stamp), 0)
    say("kit rebuild restore: the build state of %s (%s) is back - %d file(s) and %d frame(s); %d live file(s) and %d frame(s) that state did not have removed (they are in the live state kept below).\n"
        "  The live state before it is kept as tags\\%s (restore that to undo this). The verdicts it carried came back with their artefacts: %s.\n"
        "  %s"
        % (tag, rec.get("when"), put, fput, rm, frm, stamp, ", ".join(vd) or "none",
           ("THIS STATE WAS SAVED BEFORE 31br A2 - it carries no look record, so the live ones (another build's) are removed: a REDO / MOVE of a restored layout or piece is judged on a picture you have opened\n"
            "  (judge --verdict redo --frame <png> --face <n>), an OK waits for the step's look again; the client's word on the design re-makes a judged layout: skin-rim --supersede \"<the client's words>\"" if old_state else
            "Its look records and their frames are back with it (31br A2) - judge them as they stand; a REDO / MOVE of a restored layout or piece is judged on a picture you have opened; the client's word on the design\n"
            "  re-makes a judged layout: skin-rim --supersede \"<the client's words>\"")))
    return 0


def log_row(folder, tag, step, setsd, line, rc, secs=None):
    p = os.path.join(folder, "BUILD_LOG.md")
    try:
        new = not os.path.isfile(p)
        with open(p, "a", encoding="utf-8") as fh:
            if new:
                fh.write("# BUILD LOG - one row per `kit rebuild` run / judgement, written by the runner (kit 31an). Paste the rows into the report.\n\n"
                         "| when | tag | step | levers set (the rest: suggested) | the line | rc | s |\n|---|---|---|---|---|---|---|\n")
            lv = ", ".join("%s=%s" % (k, (v if len(v) < 40 else v[:37] + "...")) for k, v in sorted(setsd.items()) if k not in ("LK_TAG",))
            fh.write("| %s | %s | %s | %s | %s | %s | %s |\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), tag, step, lv.replace("|", "/") or "-",
                     (line or "-").replace("|", "/")[:220], rc, ("%.0f" % secs) if secs is not None else "-"))
    except OSError:
        pass


_KEYLINE = re.compile(r"^(?:\s*\d+s\s+)?(FAIL:.*|SKIN BUILD PASS.*|MIRROR CHECK PASS.*|CHECK (?:PASS|FAIL).*|FACES: .*|FINAL FACES: .*|FACE LADDER.*|MIRRORED LAYOUT.*|"
                      r"regions: .*|wall_caps\.brep: .*|projected in .*|frame faces .*|STEP \d.*->.*|.*-> PASS.*|POINTS_LOOK.json.*|LAYOUT_LOOK.json.*|PIECE_LOOK.json.*|"
                      r"ADDED LINES: .*|LINES AGAINST THE PART: .*|FRAME: .*|wall junctions placed .*|network \d+ edges, .*|patches \d+ \(.*|WIRES_LOOK.json.*|LAYOUT_LOOK.json.*|source\.stl.*|SOURCE: .*|selected points measured.*|STATIONS.*|review-body: .*|TRIAL_LOOK.json.*|SECOND .*|CUTS_REGION.json.*|region .* mm3; content .*|SOURCE -> .*|edges built \d+.*|FRAME v2: .*)$")


def key_line(out):
    """the step's verdict line: its FAIL, else the last of its result lines"""
    lines = [l.strip() for l in (out or "").splitlines() if l.strip()]
    for l in lines:
        if l.startswith("FAIL:"): return l
    hits = [_KEYLINE.match(l).group(1) for l in lines if _KEYLINE.match(l)]
    if hits:
        _pri = [h for h in hits if h.startswith("LINES AGAINST THE PART")]      # skin-wires
        return _pri[-1] if (_pri and hits[-1].startswith("ADDED LINES")) else hits[-1]
    _banner = re.compile(r"^(FreeCAD \d|FreeCAD is free and open-source|(?:\(c\)|\u00a9)\s*\d{4}|\d{4}-\d{4} FreeCAD contributors|Copyright|This program is free software|This library is free software|Licence|License|See the GNU|FreeCAD comes with|You should have received)", re.I)
    _kb = next((getattr(m_, "_FC_BANNER") for m_ in (sys.modules.get("kit"), sys.modules.get("__main__")) if getattr(m_, "_FC_BANNER", None) is not None), None)
    rest = [l for l in lines if not _banner.match(l) and not (_kb is not None and _kb.match(l)) and l != "DONE"]
    return rest[-1] if rest else ""


def savepoint(kit, job, tag, what):
    """a STATE line at a savepoint (a judged-ok layout / piece / points, a STEP 4 CHECK PASS) - the tag key survives a compaction"""
    try:
        kit.cmd_state(["--note", "SAVEPOINT %s: %s (job %s) - the BUILD_LOG row is the detail" % (tag, what, job), "--tags", "%s=current" % tag])
    except SystemExit:
        pass
    except Exception:
        pass


# THE SECOND REVIEW
# crumpled
# recorded
# kit rebuild
SECOND_BRIEF = """WHAT TO LOOK FOR - a SKIN LOOK of the burrito's remade piece (the client's words): the finished section is "one big curve meeting other curves
or flat areas cleanly"; "the simplest surface spanning clean edges"; "nearly everything is still far too lumpy" was the failure. Each face has its
own tint (no edges drawn); in a FACE frame the subject face is tinted and its neighbours grey. For every frame report: a LUMP, RIPPLE, CRUMPLE, DIMPLE,
FOLD or PINCH on a face; a WAVY or saw-toothed border between faces; a face that is not ONE simple surface; a hole, a slit or a red (free) edge; a
yellow (invalid) face; on a symmetric edit, two sides that differ. Add to each defect "face" (the number
in the frame's title when it names one) and "size": large (a face or more), medium (a patch of a face), small (a spot). Every frame is THE PIECE VIEW
(31bn): one conforming mesh of the whole piece (its quality line at the bottom: triangles, mm off the surfaces, degrees off the normal, cracks) - a
surface is shaded smoothly from its own normals (a crease between faces stays sharp); a soft lengthwise shading band on a long face is its real
ripple as built, not a defect of the picture; a frame carrying a red RENDER DEFECTIVE band is NO EVIDENCE: list it under poor_frames and report
nothing from it."""

TRIAL_BRIEF = """WHAT TO LOOK FOR - the REAL MODEL: the burrito's remade piece sewn into the body (a TRIAL). The frames are review-body's: the whole body,
the edit region close up from every side (above and below), and the OLD-vs-NEW station sections through the seams on one camera. the client's words: the
finished section is "one big curve meeting other curves or flat areas cleanly"; "fits back into model perfectly"; "symmetric where the design is";
no "lumpy / wavy / crumpled" feature in the delivery. Judge the SHAPE in the body: (1) the seam - does the new section meet the old on every
wall without a step, a lip or a gap (the stations show it)? In the station frames GREEN is a section line both bodies share (unchanged within the seam ceiling, 0.15 mm),
YELLOW is the OLD body only (removed), BLUE is the NEW body only (added): a seam step is a yellow and a blue line running apart where one green line should
be; inside the edit region yellow-and-blue is the edit itself - judge the blue shape; outside the region every line should be green, and a yellow or blue
one there is a defect. (2) each feature - a spine, a vane, a support - one simple surface, where the old one was,
the right size; (3) the two sides alike on a symmetric edit; (4) nothing missing, nothing extra (a bulge, a pit, a fin where none was); (5) the
designed openings still open. A defect names the FRAME, the PLACE (which feature, which side) and its SIZE (large / medium / small); a BLOCKER is a
wrong shape, a missing feature, a visible seam step. Return the JSON the brief below the skin look asks for (frames_opened, verdict, defects,
poor_frames). the client decides the acceptance from the pictures; you say what they show."""


SECOND_SCHEMA = """THE RESULT, exactly this JSON (31bp - a result off it is REFUSED): {"frames_opened": [<every frame path of the shard>], "verdict": "pass" | "fail",
  "defects": [{"frame": "<file>", "what": "<what is wrong>", "where": "<which feature, which side>", "face": <the number in the frame's title, when one>,
  "size": "large" | "medium" | "small", "severity": "blocker" | "flaw" | "note"}], "poor_frames": [<frames stamped RENDER DEFECTIVE, reported from not at all>]}
  - "fail" with no blocker still counts as a blocker; "redo", "ok", "blocker": true and the like are not the schema."""
def _second_check(r):
    """31bp: the reviewer's JSON against the schema - the reason it is refused, or None"""
    if not isinstance(r, dict): return "not a JSON object"
    v = str(r.get("verdict", "")).strip().lower()
    if v not in ("pass", "fail"): return "verdict %r is not \"pass\" | \"fail\"" % r.get("verdict")
    for i, d in enumerate(r.get("defects") or []):
        if not isinstance(d, dict): return "defect %d is not an object" % i
        if str(d.get("severity", "")).strip().lower() not in ("blocker", "flaw", "note"): return "defect %d (%s) carries no \"severity\" of blocker | flaw | note (got %r)" % (i, str(d.get("what", ""))[:40], d.get("severity"))
        if not str(d.get("frame", "")).strip() or not str(d.get("what", "")).strip(): return "defect %d names no \"frame\" or \"what\"" % i
    return None
def _second_path(folder, what="skin"):
    return os.path.join(folder, "review_body", "SECOND_trial.json") if what == "trial" else os.path.join(folder, "skin", "review", "SECOND_skin.json")


def _shards(frames, n):
    n = max(1, min(n, len(frames))); k, r = divmod(len(frames), n); out = []; i = 0
    for j in range(n):
        m = k + (1 if j < r else 0); out.append(frames[i:i + m]); i += m
    return out


def second(args, kit, say=print):
    """kit rebuild second --job <J> --what skin [--assign] [--shards 6]   the shards' frame lists + the reviewer's brief (31ar: --brief is kit.py's own filter)
    kit rebuild second --job <J> --what skin --shard <k> --result <file.json | 'json'>   one cad-reviewer's returned JSON, recorded"""
    job = kit._opt(args, "--job"); what = kit._opt(args, "--what") or "skin"
    if not job or what not in ("skin", "trial"):
        say(second.__doc__); return 2
    folder = os.path.join(kit.ROOT, "claude_code", "jobs", job)
    ref = restart_refusal(folder, "second")
    if ref: say(ref); return 2
    # stations
    if what == "trial":
        lk_p = os.path.join(folder, "review_body", "TRIAL_LOOK.json"); art = os.path.join(folder, "body_trial.brep"); rev = os.path.join(folder, "review_body"); nsh0 = 2
    else:
        lk_p = os.path.join(folder, "skin", "review", "PIECE_LOOK.json"); art = os.path.join(folder, FILES["skin_piece"]); rev = os.path.join(folder, "skin", "review"); nsh0 = 6
    try:
        lk = json.load(open(lk_p, encoding="utf-8"))
    except (OSError, ValueError):
        say("kit rebuild second REFUSED: %s is missing - `kit rebuild %s` first" % (os.path.relpath(lk_p, folder), "review-body (on the trial's body)" if what == "trial" else "skin-look")); return 2
    if not os.path.isfile(art) or lk.get("md5") != _md5(art):
        say("kit rebuild second REFUSED: the look is of an earlier %s - `kit rebuild %s` on the current one" % ("trial body" if what == "trial" else "piece", "review-body" if what == "trial" else "skin-look")); return 2
    if what == "trial":
        try: _tjs = json.load(open(os.path.join(folder, "TRIAL.json"), encoding="utf-8")) if os.path.isfile(os.path.join(folder, "TRIAL.json")) else {}
        except (OSError, ValueError): _tjs = {}
        if not _tjs.get("done") or not _check_passed(_tjs):
            say("kit rebuild second REFUSED: the trial's STEP 4 %s (%s) - a trial that failed its own check is not reviewed: fix the piece (the REFUSED lines of STEP 4 name the seam, the PROTECT box or the void) and run the trial again" % ("did not finish" if not _tjs.get("done") else "was not CHECK PASS", str(_tjs.get("check", ""))[:100])); return 2
    frames = list(lk.get("frames") or []); m = lk["md5"]
    sp = _second_path(folder, what)
    try:
        st = json.load(open(sp, encoding="utf-8"))
    except (OSError, ValueError):
        st = {}
    if st.get("md5") != m:
        nsh = int(kit._opt(args, "--shards", nsh0) or nsh0)
        st = {"md5": m, "frames": frames, "assigned": {str(i): g for i, g in enumerate(_shards(frames, nsh))}, "results": {}, "opened": time.strftime("%Y-%m-%d %H:%M:%S")}
    if "--assign" in args or "--brief" in args or (kit._opt(args, "--shard") is None and kit._opt(args, "--result") is None):
        if what == "skin" and lk.get("mode") in ("quick", "faces"):
            say("kit rebuild second REFUSED: the piece's look is the %s one - the second reviewer reviews the FULL look:\n" % ("QUICK (whole piece only)" if lk.get("mode") == "quick" else "TARGETED (FACES=%s; 31br L1)" % lk.get("faces_looked")) +
                "  kit rebuild skin-look --job %s --tag <T> --set LOOK_MODE=full   (every fitted face in two iso views), then this again" % job); return 2
        nsh = int(kit._opt(args, "--shards", len(st["assigned"])) or len(st["assigned"]))
        if nsh != len(st["assigned"]) and not st["results"]:
            st["assigned"] = {str(i): g for i, g in enumerate(_shards(frames, nsh))}
        with open(sp, "w", encoding="utf-8") as fh: json.dump(st, fh, indent=1)
        say("THE SECOND REVIEW of the %s (%d frames, %d shards) - launch ALL the shards at once, one `cad-reviewer` sub-agent each, BEFORE you" % ("REAL MODEL (the trial)" if what == "trial" else "piece", len(frames), len(st["assigned"])))
        say("judge it yourself. Give each: its frame paths (absolute, below), edit_region = the edit region's box, frozen = its frozen regions, its shard")
        say("number, and this brief:\n\n" + (SECOND_BRIEF if what == "skin" else TRIAL_BRIEF) + "\n\n" + SECOND_SCHEMA + "\n")
        for k, g in sorted(st["assigned"].items(), key=lambda kv: int(kv[0])):
            say("  shard %s (%d frames):" % (k, len(g)))
            for f in g: say("    %s" % os.path.join(rev, f))
        say("\nThen record each shard's returned JSON (a file or the text):  kit rebuild second --job %s --what %s --shard <k> --result <it>" % (job, what))
        log_row(folder, "-", "second --assign", {}, "%d frames in %d shards" % (len(frames), len(st["assigned"])), 0)
        return 0
    k = kit._opt(args, "--shard"); res = kit._opt(args, "--result")
    if k is None or res is None or str(k) not in st["assigned"]:
        say("kit rebuild second: --shard <k> (one of %s) --result <file.json | json text>   (run `kit rebuild second --job <J> --what skin --assign` first)" % ", ".join(sorted(st["assigned"], key=int))); return 2
    try:
        r = json.load(open(res, encoding="utf-8")) if os.path.isfile(res) else json.loads(res)
    except (OSError, ValueError) as e:
        say("kit rebuild second REFUSED: the result is not the reviewer's JSON (%s)" % e); return 2
    _why = _second_check(r)
    if _why:
        say("kit rebuild second REFUSED: shard %s's result is off the schema - %s. Nothing recorded. %s" % (k, _why, SECOND_SCHEMA)); return 2
    want = set(st["assigned"][str(k)]); got = set()
    for x in (r.get("frames_opened") or []):
        bx = os.path.basename(str(x)); got.add(bx if bx.lower().endswith(".png") else bx + ".png")
    miss = sorted(want - got)
    if miss:
        say("kit rebuild second REFUSED: shard %s did not open %d of its %d frames (%s) - a shard that skips frames has not reviewed; re-run it" % (k, len(miss), len(want), ", ".join(miss[:6]))); return 2
    st["results"][str(k)] = {"verdict": str(r.get("verdict", "")).strip().lower(), "defects": r.get("defects") or [], "poor": r.get("poor_frames") or [], "when": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(sp, "w", encoding="utf-8") as fh: json.dump(st, fh, indent=1)
    done = len(st["results"]); tot = len(st["assigned"])
    say("kit rebuild second: shard %s recorded (%s, %d defect(s)) - %d of %d shards in" % (k, st["results"][str(k)]["verdict"], len(st["results"][str(k)]["defects"]), done, tot))
    log_row(folder, "-", "second shard %s" % k, {}, "%s, %d defect(s)" % (st["results"][str(k)]["verdict"], len(st["results"][str(k)]["defects"])), 0)
    if done == tot:
        ok, msg, ranked = second_verdict(folder, art, what)
        say(msg)
        if what == "trial" and ok: say("  -> the real model passed its two reviewers: open every frame yourself, then kit rebuild judge --job %s --what trial --verdict ok --note \"...\" - the trial becomes THE model (no rebuild, no reinsert)" % job)
        if not ok and ranked is not None:
            bx = []
            for d in ranked:
                if d.get("severity") != "blocker" or d.get("face") in (None, "", "?"): continue
                try:
                    bx += spot_boxes(folder, "skin", faces=str(d.get("face")))
                except ValueError:
                    pass
            record_try(folder, "second review", m, "the second reviewer: " + (ranked[0].get("what", "") if ranked else ""), bx, say)
    return 0


_SIZE = {"large": 3, "medium": 2, "small": 1}


def second_verdict(folder, art, what="skin"):
    """(complete and no blocker, the message, the defects ranked largest first - or None when incomplete)"""
    try:
        st = json.load(open(_second_path(folder, what), encoding="utf-8"))
    except (OSError, ValueError):
        return False, "no second review of the %s (kit rebuild second --what %s --assign)" % ("trial" if what == "trial" else "piece", what), None
    if not os.path.isfile(art):
        return False, "%s is missing - nothing to review%s" % (os.path.basename(art), " or accept" if what == "trial" else ""), None
    if st.get("md5") != _md5(art):
        return False, "the second review is of an earlier %s - `kit rebuild second --what %s --assign` on this one" % ("trial body" if what == "trial" else "piece", what), None
    miss = [k for k in st["assigned"] if k not in st["results"]]
    if miss:
        return False, "the second review is not complete: shard(s) %s not recorded" % ", ".join(sorted(miss, key=int)), None
    try:
        info = json.load(open(os.path.join(folder, "skin", "review", "PIECE_LOOK.json"), encoding="utf-8")).get("frame_info") or {}
    except (OSError, ValueError):
        info = {}
    defects = []
    for k, r in st["results"].items():
        for d in r["defects"]:
            fr = str(d.get("frame", "")); fr = fr if fr.endswith(".png") else fr + ".png"
            fi = info.get(fr) or {}
            d2 = dict(d); d2["severity"] = str(d.get("severity", "")).strip().lower(); d2["shard"] = k; d2["face_area_mm2"] = fi.get("area_mm2"); d2["rank"] = (_SIZE.get(str(d.get("size", "")).strip().lower(), 0), float(fi.get("area_mm2") or 0.0), 1 if d2["severity"] == "blocker" else 0)
            defects.append(d2)
    defects.sort(key=lambda d: d["rank"], reverse=True)
    _sev = lambda d_: str((d_ or {}).get("severity", "")).strip().lower()
    blockers = [d for d in defects if _sev(d) == "blocker"] + [None for r in st["results"].values() if str(r.get("verdict", "")).strip().lower() == "fail" and not any(_sev(dd) == "blocker" for dd in r["defects"])]
    lines = ["THE SECOND REVIEW of the %s: %d shard(s), %d defect(s), %d blocker(s)%s - largest first:" % ("REAL MODEL (the trial)" if what == "trial" else "piece", len(st["results"]), len(defects), len(blockers), (" (%d of them a shard's 'fail' verdict naming no blocker)" % sum(1 for b in blockers if b is None)) if any(b is None for b in blockers) else "")]
    for d in defects[:15]:
        lines.append("   %-7s %-7s face %-5s %-8s %s - %s" % (d.get("severity", "?"), d.get("size", "?"), d.get("face", "?"), ("%.0f mm2" % d["face_area_mm2"]) if d.get("face_area_mm2") else "", d.get("frame", "?"), str(d.get("what", ""))[:110]))
    ok = not blockers
    lines.append("  -> %s" % (("no blocker: your own verdict next (open every frame; `kit rebuild judge --what %s`)" % what) if ok else
                              "FAIL: the %s is not ok - fix the LARGEST defect first (its face, its points, its line), then build and look again" % ("real model" if what == "trial" else "piece")))
    return ok, "\n".join(lines), defects


# skin-labels  skin-rim
# skin-build
# silly dum dum
OK_GUARDS = {"skin-labels": "layout", "skin-features": "layout",      # 31bx (R6 F9): the feature map re-makes the layout - over a judged ok it is refused like skin-labels / skin-rim (it had re-made it silently and skin-rim
             "skin-rim": "layout", "skin-build": "skin"}


def _lookgate(kit):
    try:
        hd = os.path.join(os.path.dirname(kit.HERE), "hooks")
        if hd not in sys.path: sys.path.insert(0, hd)
        import lookgate
        return lookgate
    except Exception:
        return None


def standing_ok(folder, what):
    """the judged-ok record of the CURRENT artefact (its md5 matches), or None"""
    sub, _cuts, judged_fn, art_fn, _k = JUDGED[what]
    art = os.path.join(folder, art_fn)
    try:
        j = json.load(open(os.path.join(folder, sub, judged_fn), encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if j.get("verdict") == "ok" and os.path.isfile(art) and j.get("md5") == _md5(art):
        return j
    return None


# skin-wires
DOWNSTREAM = {"layout": ("skin-network", "skin-frame", "skin-wires", "skin-build", "skin-look", "skin-mirror WHAT=piece"),
              "skin": ("reinsert", "skin-mirror WHAT=piece", "second")}


def downstream_failure_since(folder, what, okj):
    """the first BUILD_LOG row after the ok of a step downstream of `what` that failed or was killed: {when, tag, step, line, rc} or None"""
    p = os.path.join(folder, "BUILD_LOG.md"); since = str(okj.get("when") or "")
    try:
        rows = open(p, encoding="utf-8").read().splitlines()
    except OSError:
        return None
    for ln in rows:
        if not ln.startswith("| 20"): continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 6: continue
        when, tag, step, _lv, line, rc = cells[0], cells[1], cells[2], cells[3], cells[4], cells[5]
        if when <= since: continue
        if not any(step.startswith(d_) for d_ in DOWNSTREAM.get(what, ())): continue
        if rc.strip() in ("0", "2", "-"): continue
        return {"when": when, "tag": tag, "step": step, "line": line, "rc": rc}
    if what == "layout":      # skin-features
        pf = os.path.join(folder, "skin", "preflight.json")
        try:
            j = json.load(open(pf, encoding="utf-8")); pw = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(pf)))
            if str(j.get("verdict", "")).lower() == "fail" and pw > since:
                return {"when": pw, "tag": str(j.get("tag") or ""), "step": "skin-wires (the preview)", "rc": "preview",
                        "line": "PREVIEW VERDICT - THE BUILD WOULD FAIL: faces %s, pieces %s, built NOT VALID %s" % (j.get("span_failed"), j.get("pieces_failed"), [f_.get("patch") if isinstance(f_, dict) else f_ for f_ in (j.get("faces_invalid") or [])])}
        except (OSError, ValueError):
            pass
    return None


def supersede_after_failure(folder, what, okj, fail, say=print):
    """the ok (and the wires' ok, for a layout) marked superseded with the failure as the reason; a layout round recorded; the line said"""
    why = "%s %s %s (rc %s): %s" % (fail["step"], fail["tag"], "KILLED" if fail["rc"].strip() == "137" else "FAILED", fail["rc"], fail["line"][:120])
    n = 0
    for w_ in ((what, "wires") if what == "layout" else (what,)):
        sub, _c, judged_fn, _a, _k = JUDGED[w_]; jp = os.path.join(folder, sub, judged_fn)
        try:
            j = json.load(open(jp, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if j.get("verdict") != "ok": continue
        j = dict(j, verdict="superseded", superseded=time.strftime("%Y-%m-%d %H:%M:%S"), note=(j.get("note") or "") + " [superseded: a later step failed on it - %s]" % why)
        with open(jp, "w", encoding="utf-8") as fh: json.dump(j, fh, indent=1)
        n += 1
    say("  OVERTURNED: the %s judged ok at %s is overturned by a later step's failure - %s - so this step runs (31bk; %d verdict(s) superseded, the"
        " records kept). It is a layout round: open the new layout's pictures and judge them." % (what, okj.get("when"), why, n))
    try:
        record_round(folder, okj.get("md5") or "?", [], "redo after a downstream failure: " + why, say)
    except Exception:
        pass
    return n


def _refused_bump(folder, what, md5_):
    """31bk: how many times a re-run over THIS judged ok (by md5) has been refused - the first is a refusal, the next a strike"""
    st = restart_state(folder); d = st.setdefault("refused_ok", {}); key = "%s:%s" % (what, md5_ or "?")
    d[key] = int(d.get(key, 0)) + 1; _restart_save(folder, st); return d[key]


def _ok_time(j):
    try:
        return time.mktime(time.strptime(j.get("when", ""), "%Y-%m-%d %H:%M:%S"))
    except (ValueError, TypeError):
        return 0.0


def _undo_strike(kit, what_txt, cmdline, say):
    LG = _lookgate(kit)
    if LG is None:
        return ""
    sent = LG.strike(kit.ROOT, "undo", what_txt, cmdline)
    return ("\n\n" + LG.owed_message(LG._dd_load(kit.ROOT))) if sent else ""


def design_best(folder, say=print, why=""):
    r"""31aw (the client 2026-10-08: "two copies, not unlimited. Best so far and working"): skin\DESIGN.json -> skin\DESIGN_best.json when the design just
    built a passing piece or an accepted trial; `--set DESIGN=best` reads it back"""
    d = os.path.join(folder, "skin", "DESIGN.json"); b = os.path.join(folder, "skin", "DESIGN_best.json")
    if not os.path.isfile(d): return
    try:
        shutil.copy2(d, b); say("  design  : skin\\DESIGN.json kept as DESIGN_best.json (%s) - `--set DESIGN=best` restores it" % why)
    except OSError:
        pass


def _check_passed(tj):
    """31bq R7c (D1 on RR B10): the trial's STEP 4 verdict read from the CHECK line's HEAD (a substring "PASS" test had been the gate; rb_reinsert prints
    "CHECK PASS: ..." / "CHECK FAIL: ..." as its last line and exits rc 0 either way)"""
    if tj.get("check_pass") is not None: return bool(tj.get("check_pass"))
    return str(tj.get("check", "")).strip().startswith("CHECK PASS")


def _trial_promotable(folder, kit, job):
    """31bq RR (B10 (1)): can the trial become THE MODEL - checked BEFORE the verdict is written (promote_trial's refusals came after it and left an "ok" on
    record): its body, its STEP 4 CHECK PASS, and the atlas gate's OWN condition (a real STEP 3 asks the same: new B-rep geometry needs its region) - the NOTE
    promote_trial printed tested the assignment alone (it fired with no atlas, on a DRAFT-only atlas and on a tag assignment, and blocked nothing)"""
    bt_ = os.path.join(folder, "body_trial.brep"); tj_p_ = os.path.join(folder, "TRIAL.json")
    if not os.path.isfile(bt_): return False, "body_trial.brep is missing - nothing to accept"
    try: tj_ = json.load(open(tj_p_, encoding="utf-8")) if os.path.isfile(tj_p_) else {}
    except (OSError, ValueError): tj_ = {}
    if not tj_.get("done"): return False, "the trial's STEP 4 did not finish (TRIAL.json) - a trial is accepted whole: STEP 2, 3 and 4 with CHECK PASS"
    if not _check_passed(tj_): return False, "the trial's STEP 4 was not CHECK PASS (%s) - not reviewable, not acceptable: fix the piece and run the trial again" % str(tj_.get("check", ""))[:80]
    try:
        G_ = kit.G
        if G_.atlas_needs_assignment(kit.ROOT) and not (G_.atlas_assignment(kit.ROOT, job) or (tj_.get("tag") and G_.atlas_assignment(kit.ROOT, str(tj_.get("tag"))))):
            return False, ("the trial becomes THE MODEL (body_new.brep) and the atlas does not say which region it belongs to - the gate a real STEP 3 holds (31bq B10):\n"
                           "  kit atlas assign %s --to <existing region>\n  kit atlas assign %s --new <name> --what \"<its physical definition>\"   (then announce it to the client)" % (job, job))
    except AttributeError: pass
    _sic = os.path.join(folder, "skin", "solid_c.json"); _pp = os.path.join(folder, FILES["skin_piece"]); _no = []
    if os.path.isfile(_pp):
        try: _sj = json.load(open(_sic, encoding="utf-8")) or {}
        except (OSError, ValueError) as _e: _sj = None; _no.append("the build's record skin\\solid_c.json is missing or unreadable (%s) - the piece's self-intersection is not judged, which is no pass" % str(_e)[:60])
        if _sj is not None and not isinstance(_sj, dict):      # unreadable
            _no.append("the build's record skin\\solid_c.json is JSON but not an object (a %s) - it cannot be read, which is no pass (kit check refuses it the same way)" % type(_sj).__name__); _sj = None
        if _sj is not None:
            _pm = _md5(_pp)
            if _sj.get("piece_md5") != _pm or (tj_.get("piece_md5") and tj_.get("piece_md5") != _pm):
                _no.append("the build's record is not THIS piece's (record %s, TRIAL.json %s, the piece %s)" % (str(_sj.get("piece_md5"))[:8], str(tj_.get("piece_md5"))[:8], _pm[:8]))
            _sis = bool(_sj.get("check_selfintersect") or "SelfIntersect" in str(_sj.get("check", "")))
            _sf = list(_sj.get("si_self_faces") or [])
            if not _sf and "si_self_faces" not in _sj:
                _sf = [b_.get("face") for b_ in (_sj.get("check_faces") or []) if isinstance(b_, dict) and "SelfIntersect" in str(b_.get("check", ""))]
            if _sf and _sis: _no.append("%d face(s) of the piece cross THEMSELVES %s (the build's check(True) says SelfIntersect; a fold is no cosmetic)" % (len(_sf), _sf[:12]))
            _deep = []; _unm = []
            for x_ in (_sj.get("self_intersections") or []):
                try: d_ = x_[3] if len(x_) > 3 else None
                except TypeError: d_ = None
                if d_ is None: _unm.append(x_)
                else:
                    try:
                        if not (float(d_) <= 0.30): _deep.append(x_)
                    except (TypeError, ValueError): _deep.append(x_)
            if _deep: _no.append("%d crossing(s) deeper than the 0.30 mm print tolerance (%s)" % (len(_deep), ", ".join("%s x %s" % (x_[0], x_[1]) for x_ in _deep[:6])))
            if _unm and _sis: _no.append("%d crossing(s) of UNMEASURED depth under a check(True) that says SelfIntersect (%s)" % (len(_unm), ", ".join("%s x %s" % (x_[0], x_[1]) for x_ in _unm[:6])))
            try: _up = int(_sj.get("si_unmeasured_pairs") or 0)
            except (TypeError, ValueError): _up = 1
            if _up and _sis: _no.append("%d face pair(s) never measured for a crossing under a check(True) that says SelfIntersect" % _up)
            if ("si_searched" in _sj) and not _sj.get("si_searched") and _sis: _no.append("the build's crossing search did not complete under a check(True) that says SelfIntersect")
            # NOT READ
            # recorded  promote_trial
            _bok = None
            try:
                _rtj = json.load(open(os.path.join(folder, "REBUILD_reinsert_trial.json"), encoding="utf-8"))
                _bok = _rtj.get("bop_ok") if isinstance(_rtj, dict) else None
            except (OSError, ValueError): _bok = None
            if "edge_gaps_unmeasured" in _sj:
                try: _egu = 1 if isinstance(_sj.get("edge_gaps_unmeasured"), bool) else int(float(_sj.get("edge_gaps_unmeasured")))
                except (TypeError, ValueError, OverflowError): _egu = 1
                if _egu and not _bok: _no.append("%d edge gap(s) of the piece were NOT MEASURED by skin-build (edge_gaps_unmeasured) and the trial's reinsert recorded no BOP_OK - kit check refuses the same record" % _egu)
            _graw = _sj.get("edge_off_max")
            try: _gap = None if isinstance(_graw, bool) else float(_graw)
            except (TypeError, ValueError): _gap = None
            if _gap is not None and _gap != _gap: _gap = None
            if _gap is None and not _bok: _no.append("the piece's edge gap was NOT READ (skin\\solid_c.json %s) and the trial's reinsert recorded no BOP_OK - kit check refuses the same record" % ("holds no edge_off_max" if "edge_off_max" not in _sj else "gives edge_off_max as %r" % (_graw,)))
            elif _gap is not None and _gap > 0.02 and not _bok: _no.append("the piece's edges are up to %.3f mm off their faces (over the client's 0.02 mm) and the trial's reinsert recorded no BOP_OK" % _gap)
    if _no:
        return False, ("the trial would become THE MODEL and kit check would refuse it - an accepted trial is never rebuilt or re-sewn, so it is refused HERE (31bq R7W D9):\n    %s\n"
                       "  The way back: fix the piece where it is named (its lines / points), `kit rebuild skin-build` again, look, mirror, then a new trial from STEP 2."
                       % "\n    ".join(_no))
    return True, ""


def promote_trial(folder, rec, say=print):
    r"""31aw: THE TRIAL ACCEPTED (the client 2026-10-08: "If a trial passes, do not rebuild it, do not reinsert it"): body_trial.brep -> body_new.brep, its
    reinsert / check records the real ones, TRIAL.json accepted (a real STEP 2 / 3 / 4 and a skin-build of the same piece are refused), the piece
    judged ok on the trial's frames, review_body\ marked a COMPLETE review (kit check --review reads it)"""
    bt = os.path.join(folder, "body_trial.brep"); bn = os.path.join(folder, FILES["body_new"]); tj_p = os.path.join(folder, "TRIAL.json")
    if not os.path.isfile(bt): return False, "body_trial.brep is missing - nothing to accept"
    try:
        tj = json.load(open(tj_p, encoding="utf-8")) if os.path.isfile(tj_p) else {}
    except (OSError, ValueError):
        tj = {}
    if not tj.get("done"): return False, "the trial's STEP 4 did not finish (TRIAL.json) - a trial is accepted whole: STEP 2, 3 and 4 with CHECK PASS"
    if not _check_passed(tj): return False, "the trial's STEP 4 was not CHECK PASS (%s)" % str(tj.get("check", ""))[:80]
    _done_ = []      # recorded
    try:
        _bef = os.path.join(folder, "body_new_before_trial.brep")
        if os.path.isfile(bn): os.replace(bn, _bef); _done_.append((_bef, bn))
        os.replace(bt, bn); _done_.append((bn, bt))
        for a_, b_ in (("REBUILD_reinsert_trial.json", "REBUILD_reinsert.json"), ("REBUILD_check_trial.json", "REBUILD_check.json")):
            if os.path.isfile(os.path.join(folder, a_)): shutil.copy2(os.path.join(folder, a_), os.path.join(folder, b_))
        tj.update({"accepted": True, "accepted_when": rec.get("when"), "accepted_note": rec.get("note"), "body_md5": _md5(bn)})
        with open(tj_p, "w", encoding="utf-8") as fh: json.dump(tj, fh, indent=1)
    except OSError as ex:
        for a_, b_ in reversed(_done_):
            try: os.replace(a_, b_)
            except OSError: pass
        return False, "the trial's files could not be renamed (%s) - %d rename(s) undone, the trial stands as it was" % (ex, len(_done_))
    # skin-build
    try:
        pp = os.path.join(folder, FILES["skin_piece"]); s_, _c, jf_, _a, _k = JUDGED["skin"]
        with open(os.path.join(folder, s_, jf_), "w", encoding="utf-8") as fh:
            json.dump({"what": "skin", "verdict": "ok", "note": "accepted through its TRIAL in the real model: " + str(rec.get("note", ""))[:200], "md5": _md5(pp) if os.path.isfile(pp) else None,
                       "frames": rec.get("frames"), "when": rec.get("when"), "tag": rec.get("tag"), "by": "trial"}, fh, indent=1)
    except OSError:
        pass
    try:
        rvd = os.path.join(folder, "review_body"); st = {}
        try: st = json.load(open(os.path.join(rvd, "review_state.json"), encoding="utf-8")) or {}
        except (OSError, ValueError): st = {}
        st.update({"state": "COMPLETE", "counts": {"frames": len(rec.get("frames") or []), "pass": len(rec.get("frames") or []), "cannot": 0},
                   "by": "kit rebuild judge --what trial ok (31aw)", "when": rec.get("when"), "model": FILES["body_new"], "md5": tj["body_md5"]})
        with open(os.path.join(rvd, "review_state.json"), "w", encoding="utf-8") as fh: json.dump(st, fh, indent=1)
    except OSError:
        pass
    design_best(folder, say, "the accepted trial")
    _atl = ""
    return True, ("ACCEPTED: the trial IS the model - body_trial.brep is now body_new.brep (md5 %s), its reinsert / check records the real ones, the piece judged ok.\n"
                  "  Do not rebuild it, do not reinsert it (the client 2026-10-08) - a skin-build or a STEP 2 of this piece is refused. Next: kit review (before / after, one\n"
                  "  camera) -> kit check --wide-box -> kit look -> kit accept on body_new.brep; kit deliver on the client's word." % tj["body_md5"][:8] + _atl)


def judge(args, kit, say=print):
    """kit rebuild judge --job <J> --what region|keep|layout|wires|skin|points|trial --verdict ok|move|redo --note <what the frames show, in words>
    [--face <n>[,<n>...] | --spot "x0 x1 y0 y1 z0 z1[; ...]"]   (a layout / skin / trial move or redo names every place that failed)
    [--frame <png>]   (31aq: overturning a layout / piece judged ok needs the picture that shows it wrong)"""
    job = kit._opt(args, "--job"); what = kit._opt(args, "--what"); verdict = (kit._opt(args, "--verdict") or "").strip().lower(); note = kit._opt(args, "--note") or ""
    if not job or what not in JUDGED or verdict not in ("ok", "move", "redo"):
        say("kit rebuild judge --job <J> --what region|keep|layout|wires|look|skin|points|trial --verdict ok|move|redo --note \"<what the frames show>\"\n"
            "  look (after skin-look, BEFORE skin-mirror WHAT=piece or a trial - 31az): every frame of PIECE_LOOK.json opened; ok = the piece is right\n"
            "  in every frame; redo = what is wrong and where (--face / --spot) - then fix the lines or the points THERE and build again; nothing moves\n"
            "  forward on a piece the pictures show wrong\n"
            "  wires (after skin-wires): ok = every line where that feature's edge is, one straight line, arc or single curve, symmetric; redo = which\n"
            "  chain and why - decide it again in LINES / RAILS and run skin-wires again\n"
            "  trial (after review-body of a TRIAL reinsert): ok = THE ACCEPTANCE after its two reviewers (31aw: the trial's body is promoted, nothing\n"
            "  rebuilt); when the reviewers found blockers, ok only on the client's recorded word: --ruling \"<the client's words>\" --note \"<each blocker and why it\n"
            "  stands under the ruling>\" (L134: their judgement, not their agreement); redo / move = what the REAL model shows, and where (--face / --spot)\n"
            "  layout (after skin-rim) / skin (after skin-look): ok = every face one simple surface with clean borders, both sides alike on a\n"
            "  symmetric edit, nothing missing; redo = name the face and what is wrong, fix the layout / the build and look again. A skin verdict\n"
            "  waits for the SECOND REVIEWER (kit rebuild second); a move/redo NAMES every place that failed (--face <n>,... | --spot \"x0 x1 y0 y1 z0 z1\")\n"
            "  - a failed TRY at that spot; three at one spot send you back to the points THERE (31an). points: which points build which faces.\n"
            "  the verdict on the ORBIT OF THE CUTS (review\\region_cuts_*.png after the region; keep\\keep_cuts_*.png after the keep):\n"
            "  ok = every red cut crosses skins and lands in air or thick clean material; move = a cut runs along a skin, through a thin\n"
            "  lip or rib, or through the feature being fixed - then move it (WIN / PLANES; KEEP_OFFSET / KEEP_CELL) and run the step again"); return 2
    folder = os.path.join(kit.ROOT, "claude_code", "jobs", job)
    sub, cuts_fn, judged_fn, art_fn, md5key = JUDGED[what]
    _ruling = None; _overruled = []; _ruling_line = None
    if what == "trial" and verdict == "ok":
        art_t = os.path.join(folder, "body_trial.brep")
        try: _tja = json.load(open(os.path.join(folder, "TRIAL.json"), encoding="utf-8")) if os.path.isfile(os.path.join(folder, "TRIAL.json")) else {}
        except (OSError, ValueError): _tja = {}
        if _tja.get("accepted"):
            say("kit rebuild judge REFUSED: this trial was ACCEPTED at %s - it IS the model (body_new.brep, md5 %s); nothing is judged again. A different piece is a new trial from STEP 2 (the client 2026-10-08: do not rebuild it, do not reinsert it)." % (_tja.get("accepted_when"), str(_tja.get("body_md5", ""))[:8])); return 2
        ok2, msg2, ranked2 = second_verdict(folder, art_t, "trial")
        if ranked2 is None:
            say("kit rebuild judge REFUSED: a trial is accepted only after its TWO reviewers (the real model's frames): %s.\n"
                "  kit rebuild second --job %s --what trial --assign (one cad-reviewer per shard), record each shard, then judge ok." % (msg2, job)); return 2
        okp0_, whyp0_ = _trial_promotable(folder, kit, job)      # recorded  recorded
        if not okp0_: say("kit rebuild judge REFUSED: %s" % whyp0_); return 2
        if not ok2:
            # over the  recorded
            ruling_ = (kit._opt(args, "--ruling") or "").strip()
            blk_ = [d for d in ranked2 if str(d.get("severity", "")).strip().lower() == "blocker"]
            try:
                for k_s, r_s in sorted(((json.load(open(_second_path(folder, "trial"), encoding="utf-8")) or {}).get("results") or {}).items()):
                    if str(r_s.get("verdict", "")).strip().lower() == "fail" and not any(str((dd_ or {}).get("severity", "")).strip().lower() == "blocker" for dd_ in (r_s.get("defects") or [])):
                        blk_.append({"frame": None, "what": "shard %s failed naming no blocker" % k_s, "where": "", "size": None})
            except (OSError, ValueError, AttributeError, TypeError): pass
            if len(ruling_) < 20 or len(note.strip()) < 60:
                say("kit rebuild judge REFUSED: a trial is accepted only after its TWO reviewers (the real model's frames): the reviewers found blockers:\n%s\n"
                    "  the client's judgement outranks the reviewers (L134): an ok over their %d blocker(s) carries their RULING, recorded - --ruling \"<the client's words, 20+ characters>\"\n"
                    "  --note \"<each blocker and why it stands under the ruling, 60+ characters>\"; or fix what they found and review again." % (msg2, len(blk_))); return 2
            _ruling = ruling_; _overruled = [{"frame": d.get("frame"), "what": str(d.get("what", ""))[:200], "where": str(d.get("where", ""))[:120], "size": d.get("size")} for d in blk_]
            say(msg2); _ruling_line = "  RULING  : the %d blocker(s) are overruled on the client's word, recorded with the verdict - %s" % (len(blk_), ruling_)      # recorded
        else:
            say(msg2)
    if what in ("layout", "skin", "trial", "look"):
        ref = restart_refusal(folder, "judge --what %s" % what)
        if ref: say(ref); return 2
    cp = os.path.join(folder, sub, cuts_fn); art = os.path.join(folder, art_fn)
    # recorded
    # skin-rim
    _ovr = verdict in ("move", "redo") and bool((kit._opt(args, "--frame") or "").strip()); _frs = None
    try:
        cuts = json.load(open(cp, encoding="utf-8"))
    except (OSError, ValueError):
        if not _ovr: say("kit rebuild judge REFUSED: %s\\%s is missing - the %s step writes the frames to judge; run it (it is not a picture you can judge unseen)" % (sub, cuts_fn, what)); return 2
        cuts = {}; _frs = "missing"
    frames = [f for f in cuts.get("frames", []) if os.path.isfile(os.path.join(folder, sub, f))]
    if not frames and not _ovr:
        say("kit rebuild judge REFUSED: the frames are not on disk (%s) - run the %s step again" % (", ".join(cuts.get("frames", [])) or "none listed", what)); return 2
    if not os.path.isfile(art):
        say("kit rebuild judge REFUSED: %s is missing" % art_fn); return 2
    m = _md5(art)
    if cuts.get(md5key) and cuts.get(md5key) != m:
        if not _ovr: say("kit rebuild judge REFUSED: the frames show an earlier %s (the step ran again since) - run the step to render the current one" % art_fn); return 2
        _frs = "stale"
    if _frs: say("  frames  : the %s's frames record is %s (%s) - this %s stands on the picture you cite (--frame), as 31br A2 allows; an OK would not" % (what, _frs, ("%s\\%s is for an earlier %s" % (sub, cuts_fn, art_fn)) if _frs == "stale" else ("%s\\%s is not on disk" % (sub, cuts_fn)), verdict.upper()))
    if len(note.strip()) < 25:
        say("kit rebuild judge REFUSED: --note says in words what the %d frames show - at least a sentence" % len(frames)); return 2
    # RENDER DEFECTIVE
    _defs = [f_ for f_, i_ in (cuts.get("frame_info") or {}).items() if isinstance(i_, dict) and isinstance(i_.get("quality"), dict) and i_["quality"].get("defective")]
    if _defs:
        say("kit rebuild judge REFUSED: %d of the %d frames are stamped RENDER DEFECTIVE (%s%s) - %s. A defective picture is no evidence: make the mesh right\n"
            "  (the step's PIC_DEV / PIC_ANG, or an invalid face left out) and run the step again; no verdict on these."
            % (len(_defs), len(frames), ", ".join(_defs[:4]), "..." if len(_defs) > 4 else "", ((cuts.get("frame_info") or {}).get(_defs[0], {}).get("quality") or {}).get("why", ""))); return 2
    _mq = cuts.get("mesh_quality")
    if what in ("look", "skin") and not _frs:
        if not isinstance(_mq, dict):
            say("kit rebuild judge REFUSED: this look has no mesh record - it was drawn before THE PIECE VIEW (31bn) or by another renderer, and is no evidence: run `kit rebuild skin-look` again and judge those frames"); return 2
    _lap = cuts.get("lines_against_part")
    if what == "wires" and verdict == "ok" and (not isinstance(_lap, dict) or not _lap.get("taken")):      # NOT TAKEN
        say("kit rebuild judge REFUSED: the wires' measurement against the part was NOT TAKEN (%s) - a check that did not run is no pass: run skin-wires again and judge the frames of a run that measured its lines"
            % (str(_lap.get("why", "?"))[:120] if isinstance(_lap, dict) else "this wires record carries no measurement at all - drawn by a kit that did not measure its lines (before 31bq OO)")); return 2
    _pf = cuts.get("preflight")      # skin-wires
    if what == "wires" and verdict == "ok":
        if not isinstance(_pf, dict) or not _pf.get("taken"):
            say("kit rebuild judge REFUSED: the wires' PREVIEW (the build's own ladder on this wireframe - 31br G1 / G2) was NOT TAKEN (%s): run skin-wires again (PREFLIGHT=1, the suggestion) and judge the frames of a run that carries it"
                % (str(_pf.get("why", "?"))[:200] if isinstance(_pf, dict) else "this wires record carries no preview - drawn by a kit before 31br, or by a skin-wires with PREFLIGHT=0")); return 2
        _bad = (list(_pf.get("span_failed") or []), list(_pf.get("pieces_failed") or []), list(_pf.get("not_made_unaccepted") or []), list(_pf.get("faces_invalid") or []))
        if any(_bad):
            say("kit rebuild judge REFUSED: the PREVIEW says skin-build would FAIL on this wireframe (31br G1 / G2)%s%s%s%s - the PREVIEW VERDICT lines of the wires run say where and how: change the lines there and run skin-wires again; a fillet you accept sharp carries \"sharp_ok\": true on its entry"
                % ((" - faces that cannot be spanned: %s" % _bad[0]) if _bad[0] else "", (" - kit-made pieces that fail the face stage: %s" % ", ".join("%s%s" % (p_.get("patch"), p_.get("sub") or "") for p_ in _bad[1][:6])) if _bad[1] else "", (" - fillet lines NOT made: %s" % _bad[2]) if _bad[2] else "",
                   (" - faces built but NOT VALID (skin-build fails on them): %s" % ", ".join("%s%s" % (p_.get("patch"), p_.get("sub") or "") for p_ in _bad[3][:6])) if _bad[3] else "")); return 2
    if note and re.search(r"\b(cannot|can't|can not|could not|couldn't|unable to) be (built|made|blended|spanned|filled|rounded)\b|\bkit (cannot|can't|could not)\b|\bunbuildable\b|\bnot buildable\b", note, re.I) \
            and not re.search(r"\b(tag|build|run|try|tried)\b\s*[:=#]?\s*[A-Za-z]*\d[A-Za-z0-9_-]*|\b[a-z]{1,4}\d{1,3}[a-z]?[a-z0-9]{0,4}\b", note):
        say("kit rebuild judge REFUSED: the note states a LIMIT ('cannot be built') with no build behind it - a limitation is stated only with the TAG of the build that tried it (FAILURES 2026-10-26: three spots called unbuildable without one try): name the tag, or try it first (31br I3)"); return 2
    _of = cuts.get("original_faces")
    if what in ("look", "skin") and verdict == "ok" and not (isinstance(_of, dict) and (_of.get("taken") or _of.get("applies") is False)):
        say("kit rebuild judge REFUSED: the look's measure of the ORIGINAL'S FACES AGAINST THE PIECE was NOT TAKEN (%s) - a check that did not run is no pass (31bq B18): an original feature that left the piece\n"
            "  is named only by a look that measured it - run kit rebuild skin-look again (a kit fault named there is the kit maintainer's) and judge the frames of a look that measured" % (
            str(_of.get("why", "?"))[:200] if isinstance(_of, dict) else "this look record carries no such measure - drawn by a kit before 31bq B18")); return 2
    if isinstance(_mq, dict) and _mq.get("defective"):
        say("kit rebuild judge REFUSED: the %s's mesh is stamped RENDER DEFECTIVE (%s) - every frame of it is NO EVIDENCE: make the mesh right (PIC_DEV / PIC_ANG, an invalid face left out) and run the step again" % (what, _mq.get("why", ""))); return 2
    if what == "look" or (verdict == "ok" and what in ("region", "layout", "wires", "skin", "trial")):
        LG_ = _lookgate(kit); unopened = []
        import leangate as _LGr; lj_ = os.path.join(_LGr.records_root(kit.ROOT), ".claude", "looks.jsonl")
        if LG_ is not None and not os.path.isfile(lj_):
            unopened = list(frames)
        elif LG_ is not None:
            try:
                seen = {}
                for r in LG_._tail(lj_, 6000):
                    k_ = r.get("png_n") or LG_._norm(r.get("png", "")); seen[k_] = max(seen.get(k_, 0.0), float(r.get("opened", 0)))
                for f in frames:
                    fp = os.path.join(folder, sub, f); k_ = LG_._norm(fp)
                    try: mt = os.path.getmtime(fp)
                    except OSError: mt = 0.0
                    if seen.get(k_, 0.0) < mt - 1.0: unopened.append(f)
            except Exception:
                unopened = []
        if unopened:
            say("kit rebuild judge REFUSED: %d of the %d frames were never opened since they were drawn (%s%s). Open every one (the Read tool), say what\n"
                "  each shows, then judge. (31az, the client 2026-10-08: the agent moved on with geometry its own pictures showed wrong; 31bw K31: every what)"
                % (len(unopened), len(frames), ", ".join(unopened[:6]), "..." if len(unopened) > 6 else "")); return 2
    if what == "look" and verdict == "ok" and str(cuts.get("mode") or "") == "faces":
        say("kit rebuild judge REFUSED: this look is a TARGETED one (FACES=%s) - a redo / move may be judged on it, an ok may not: the piece's own verdict is the QUICK look's\n"
            "  (kit rebuild skin-look --job %s --tag <T>), every frame opened (31br L1)." % (cuts.get("faces_looked"), job)); return 2
    if verdict == "ok" and what in ("layout", "wires") and str(cuts.get("pics", "full")) == "quick":
        st_ = "skin-rim" if what == "layout" else "skin-wires"
        say("kit rebuild judge REFUSED: these %d frames are the QUICK set - an ok is judged on the FULL set, once:\n"
            "  kit rebuild %s --job %s --tag <T> --set PICS=full   (the same inputs; every view), open every frame, then judge ok.\n"
            "  A redo / move may be judged on the quick set." % (len(frames), st_, job)); return 2
    if what in ("layout", "skin") and verdict in ("move", "redo"):
        okj = standing_ok(folder, what)
        if okj:
            fr_ = kit._opt(args, "--frame") or ""
            LG = _lookgate(kit); opened = 0.0
            pic_dir = os.path.abspath(os.path.join(folder, sub))
            fr_p = os.path.abspath(fr_ if os.path.isabs(fr_) else os.path.join(folder, sub, fr_)) if fr_ else ""
            try:
                in_dir = bool(fr_p) and os.path.isfile(fr_p) and os.path.normcase(os.path.commonpath([pic_dir, fr_p])) == os.path.normcase(pic_dir)
            except ValueError:
                in_dir = False
            if LG is not None and in_dir and getattr(LG, "frame_defective", lambda *a_: False)(kit.ROOT, fr_p):
                say("kit rebuild judge REFUSED: %s is stamped RENDER DEFECTIVE - a torn or coarse picture overturns nothing; render it again (the piece view) and cite that one" % fr_); return 2
            if LG is not None and in_dir:
                key = LG._norm(fr_p)
                opened = max([float(r.get("opened", 0)) for r in LG._tail(os.path.join(__import__("leangate").records_root(kit.ROOT), ".claude", "looks.jsonl"), 3000)
                              if r.get("png_n") == key or LG._norm(r.get("png", "")) == key] + [0.0])
            if fr_ and not os.path.isfile(fr_p):
                say("kit rebuild judge REFUSED: no such picture: %s (looked for %s). Cite the frame by its name in %s\\ (a look_at picture as look\\<name>.png); the %s judged ok STANDS until a picture that exists is cited." % (fr_, fr_p, os.path.join(folder, sub), what)); return 2
            if fr_ and in_dir and opened > 0.0 and len(note.strip()) < 40:
                say("kit rebuild judge REFUSED: --note says in words what the picture shows - 40+ characters (a %s judged ok is overturned by a picture AND the words for it; the ok stands, no strike)" % what); return 2
            if fr_ and not in_dir:      # never opened
                say("kit rebuild judge REFUSED - THE PICTURE MUST BE THE JOB'S: %s is not a picture in %s\\ - cite the frame by its name there (a look_at picture as look\\<name>.png; `kit tool look_at --job %s` puts its pictures there); the %s judged ok STANDS" % (fr_, os.path.join(folder, sub), job, what)); return 2
            if not fr_ or opened <= 0.0:      # never opened
                tail = _undo_strike(kit, "a %s judged ok at %s, overturned %s" % (what, okj.get("when"), "with no picture" if not fr_ else "on a picture never opened"),
                                    " ".join(["kit rebuild judge"] + list(args)), say)
                folder_line = ""
                say("kit rebuild judge REFUSED: the %s was judged OK on its pictures at %s - it STANDS. A number does not overturn a picture (the client 2026-10-07:\n"
                    "  \"makes a measurement that it arbitrarily decides is a bad measurement with no reasoning as to why, and then undoes correct work. It has\n"
                    "  to stop\"). To overturn it: open a picture that SHOWS what is wrong (opened - at any time, 31bi - and inside the job's picture folder), then\n"
                    "  kit rebuild judge --job %s --what %s --verdict redo --frame <that picture> --note \"<what the picture shows, 40+ characters>\" --face <n>%s%s"
                    % (what, okj.get("when"), job, what, folder_line, tail)); return 2
    boxes = []
    if what in ("layout", "skin", "trial", "look") and verdict in ("move", "redo"):
        try:
            boxes = spot_boxes(folder, "skin" if what in ("trial", "look") else what, kit._opt(args, "--face"), kit._opt(args, "--spot"))
        except ValueError as ex:
            say("kit rebuild judge REFUSED: %s" % ex); return 2
        if not boxes:
            say("kit rebuild judge REFUSED: name every place that failed - --face <n>[,<n>...] (the %s's face numbers%s) or --spot \"x0 x1 y0 y1 z0 z1[; ...]\".\n"
                "  The tries are counted per spot, and only a spot that fails three times has its points picked again (the client 2026-10-07)."
                % (what, " in skin\\patches.json" if what == "layout" else " in the frames' titles / skin\\piece_faces.json")); return 2
    # THE SECOND REVIEW
    if what == "skin":
        ok2, msg2, ranked2 = second_verdict(folder, art)
        if ranked2 is None and verdict in ("redo", "move"):      # recorded
            say("  second  : no second review of the piece yet - a %s needs none (31br L1; the places you name count a try there); an OK needs the complete review free of blockers" % verdict.upper()); msg2 = None
        elif verdict == "ok" and (ranked2 is None or not ok2):
            say("kit rebuild judge REFUSED: %s.\n  The second reviewer judges the piece BEFORE you do: kit rebuild second --job %s --what skin --assign (one cad-reviewer per shard),\n"
                "  record each shard's result, then judge." % (msg2 if "\n" not in msg2 else "the second reviewer found blockers:\n" + msg2, job)); return 2
        if msg2: say(msg2)
    if what == "points":
        if verdict == "ok":
            okp, whyp = points_judged(folder, say)
            if not okp:
                say("kit rebuild judge REFUSED: %s" % whyp); return 2
            say("  restart : %s" % whyp)
            if "picked again" in whyp:
                for w_ in ("layout", "skin"):
                    okj = standing_ok(folder, w_)
                    if okj:
                        s_, _c, jf_, _a, _k = JUDGED[w_]; okj = dict(okj, verdict="superseded", superseded=time.strftime("%Y-%m-%d %H:%M:%S"),
                                                                    note=(okj.get("note") or "") + " [superseded: the points were picked again at a restart]")
                        with open(os.path.join(folder, s_, jf_), "w", encoding="utf-8") as fh: json.dump(okj, fh, indent=1)
                        say("  restart : the %s's ok (on the old points) is superseded - its steps run again" % w_)
    if what == "trial" and verdict == "ok":
        okp0_, whyp0_ = _trial_promotable(folder, kit, job)
        if not okp0_: say("kit rebuild judge REFUSED: %s" % whyp0_); return 2
    rec = {"what": what, "verdict": verdict, "note": note.strip(), "md5": m, "frames": frames, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "tag": cuts.get("tag")}
    if _frs: rec["frames_record"] = _frs; rec["frame_cited"] = (kit._opt(args, "--frame") or "").strip()
    if _ruling: rec["ruling"] = _ruling; rec["blockers_overruled"] = _overruled      # over the
    msgp = ""
    if what == "trial" and verdict == "ok":
        okp, msgp = promote_trial(folder, rec, say)
        if not okp:
            say("kit rebuild judge REFUSED: %s - nothing recorded (the verdict is written only once the trial's files are in place)" % msgp); return 2
    with open(os.path.join(folder, sub, judged_fn), "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1)
    if _ruling_line: say(_ruling_line)      # recorded  recorded
    if msgp: say(msgp)
    say("kit rebuild judge: the %s judged %s on %d frame(s) - recorded in %s\\%s%s" % (what, verdict.upper(), len(frames), sub, judged_fn,
        "" if verdict == "ok" else "; the next step refuses until a new look is judged ok"))
    log_row(folder, cuts.get("tag") or "-", "judge %s" % what, {}, "%s%s: %s" % (verdict.upper(), (" ON THE CLIENT'S RULING (%d blocker(s) overruled: %s)" % (len(_overruled), _ruling[:80])) if _ruling else "", note.strip()[:160]), 0)
    _nxj = {("region", "ok"): "kit rebuild skin-source --job %s --tag <T> (the skin steps' mesh) -> reinsert --set STEP=1 (THE REINSERT FACES FIRST) -> skin-regions -> skin-edges -> skin-points",
            ("region", "redo"): "move the walls (WIN / PLANES) where the frames showed the fault and run kit rebuild region --job %s again",
            ("layout", "ok"): "a symmetric edit: kit rebuild skin-mirror --job %s --tag <T> --set WHAT=layout; then skin-network -> skin-frame -> skin-wires (kit rebuild skin-lines runs the three)",
            ("layout", "redo"): "the points (PTS_BOX / PTS_DROP) or the FEATURES at the places you named, then skin-labels / skin-features / skin-rim again on job %s (a layout round)",
            ("wires", "ok"): "kit rebuild skin-build --job %s --tag <T>",
            ("wires", "redo"): "the LINES / _add / _fillets at the places you named, then kit rebuild skin-wires --job %s again (the preview decides)",
            ("points", "ok"): "kit rebuild skin-labels --job %s --tag <T> --set \"MIRROR=...\" (the chain from the labels on, on the new points)",
            ("look", "ok"): "a symmetric edit: kit rebuild skin-mirror --job %s --tag <T> --set WHAT=piece; then the TRIAL: reinsert --set STEP=2 --set TRIAL=\"<why>\" -> 3 -> 4 -> review-body -> second --what trial --assign -> judge --what trial",
            ("skin", "ok"): "the TRIAL: kit rebuild reinsert --job %s --tag <T> --set STEP=2 --set TRIAL=\"<why>\" -> 3 -> 4 -> review-body",
            ("trial", "ok"): "kit review (before / after) -> kit check ... --wide-box -> kit look -> kit accept -> kit apply --job %s (the accepted body into the bank)",
            ("trial", "redo"): "fix the lines or the points of job %s at the places you named, build again, look, then a new trial (a redo feeds the restart)"}.get((what, "ok" if verdict == "ok" else "redo"))
    if _nxj: say("  next    : %s" % (_nxj % job))
    if what in ("layout", "skin", "trial", "look"):
        spots_passed(folder, boxes, m, say)
    if verdict in ("move", "redo") and what in ("layout", "skin", "trial", "look"):
        record_try(folder, "skin" if what == "look" else what, m, note.strip(), boxes, say)
        if what == "look":
            say("  next    : the piece is WRONG where you said - fix its lines (skin-wires: LINES / _add) or its points THERE and build again; no mirror\n"
                "            check, no trial, no measurement of this piece (the client 2026-10-08: rework the edit, do not move to the next step)")
        if what == "layout":
            record_round(folder, m, boxes, note.strip(), say)
    if verdict == "ok" and what == "layout":
        write_layout_lock(folder, cuts.get("tag") or "?", say)
    if verdict == "ok" and what in ("layout", "skin", "points", "wires"):
        savepoint(kit, job, cuts.get("tag") or "?", "the %s judged ok - %s" % (what, note.strip()[:120]))
    return 0


_REFUSED = []


def _say_rec(*a, **k):
    """print, remembering a runner refusal's first line (31bq R7W D1: the refusals become BUILD_LOG rows)"""
    print(*a, **k)
    s_ = " ".join(str(x) for x in a).strip().split("\n", 1)[0]
    if "REFUSED" in s_: _REFUSED.append(s_)


def cmd(args, kit):
    """the runner; 31bq R7W route-end D1: a step the runner itself refused (rc 2, a REFUSED line) is a BUILD_LOG row with rc 2 - the log had shown a trial
    STEP 3 straight after a failed mirror check, the refused STEP 2 between them on no record (downstream_failure_since skips rc 2: no ok is overturned)"""
    del _REFUSED[:]
    rc = _cmd(args, kit)
    try:
        if rc == 2 and _REFUSED and args and args[0] not in ("judge", "second", "record", "save", "restore", "skin-layout", "skin-lines") and "--plan" not in args:
            job_ = kit._opt(args, "--job"); folder_ = os.path.join(kit.ROOT, "claude_code", "jobs", job_ or "")
            if job_ and os.path.isdir(folder_):
                sets_ = dict(kv.split("=", 1) for kv in kit._all(args, "--set") if "=" in kv)
                st_ = args[0] + ((" STEP=%s" % sets_.get("STEP")) if args[0] == "reinsert" and sets_.get("STEP") else "") + ((" WHAT=%s" % sets_.get("WHAT")) if args[0] == "skin-mirror" and sets_.get("WHAT") else "")
                log_row(folder_, kit._opt(args, "--tag") or "-", st_, sets_, _REFUSED[-1], 2)
    except Exception:
        pass
    return rc


def _cmd(args, kit):
    say = _say_rec
    G = kit.G
    RB = _dir(kit)
    if not args or args[0] in ("-h", "--help"):
        _help(say); return 2
    if args[0] == "judge":
        return judge(args[1:], kit, say)
    if args[0] == "second":
        return second(args[1:], kit, say)
    if args[0] == "record":
        job = kit._opt(args, "--job")
        if not job:
            say("kit rebuild record --job <name> [--region <dossier name>]   merge the job's REBUILD_*.json into REBUILD.json (and the dossier's)"); return 2
        ok, msg = merge_record(kit, job, kit._opt(args, "--region"), say)
        say(("kit rebuild record: " if ok else "kit rebuild record REFUSED: ") + msg); return 0 if ok else 2
    if args[0] == "save":
        return save_cmd(args[1:], kit, say)
    if args[0] == "restore":
        return restore_cmd(args[1:], kit, say)
    step = args[0]; rest = args[1:]
    # skin-layout  skin-rim  skin-mirror
    # skin-network  skin-frame  skin-wires
    if step in ("skin-layout", "skin-lines"):
        job_ = kit._opt(rest, "--job"); folder_ = os.path.join(kit.ROOT, "claude_code", "jobs", job_ or "")
        chain = [("skin-rim", [])] if step == "skin-layout" else [("skin-network", ["--set", "NET_PICS=0"]), ("skin-frame", []), ("skin-wires", [])]
        if step == "skin-layout" and job_ and _mirror_decision(folder_): chain.append(("skin-mirror", ["--set", "WHAT=layout"]))
        say("kit rebuild %s: %s" % (step, " -> ".join(k for k, _ in chain)))
        for k_, extra_ in chain:
            rc_ = cmd([k_] + list(rest) + extra_, kit)
            if rc_: say("kit rebuild %s: stopped at %s (rc %s)" % (step, k_, rc_)); return rc_
        return 0
    table = {k: (scr, what, card, fixed) for k, scr, what, card, fixed in STEPS}
    if step not in table:
        say("kit rebuild: %r is not a step: %s" % (step, ", ".join(k for k, _, _, _, _ in STEPS))); return 2
    script, what, card, fixed = table[step]
    path = os.path.join(RB, script)
    if not os.path.isfile(path):
        say("kit rebuild: %s is missing from the kit (%s)" % (script, RB)); return 2
    plan = "--plan" in rest
    job = kit._opt(rest, "--job")
    if not job:
        say("kit rebuild: --job <name> names the job folder under claude_code\\jobs\\ (kit newjob <name> makes it)"); return 2
    folder = os.path.join(kit.ROOT, "claude_code", "jobs", job)
    if not os.path.isdir(folder):
        say("kit rebuild: no job folder %s - `kit newjob %s` makes it (and links the model of record in as region.brep)" % (folder, job)); return 2
    sets = {}
    for kv in kit._all(rest, "--set"):
        if "=" not in kv:
            say("kit rebuild: --set takes KEY=VALUE, not %r" % kv); return 2
        k, v = kv.split("=", 1); sets[k.strip()] = v
    # "_fillets"
    # FEATURES
    # skin-build
    try:
        dsel = str(sets.pop("DESIGN", "")).strip().lower()
        dpath = os.path.join(folder, "skin", "DESIGN_best.json" if dsel == "best" else "DESIGN.json")
        if os.path.isfile(dpath) and step in ("skin-points", "skin-features", "skin-wires"):
            dj = json.load(open(dpath, encoding="utf-8")) or {}
            parts = {"skin-features": [("features", "FEATURES")], "skin-wires": [("lines", "LINES"), ("rails", "RAILS")], "skin-points": []}[step]
            for sec, lever in parts:
                if lever in sets or sec not in dj: continue
                fp_ = os.path.join(folder, "skin", "DESIGN_%s.json" % sec)
                with open(fp_, "w", encoding="utf-8") as fh: json.dump(dj[sec], fh, indent=1)
                sets[lever] = fp_; say("  design  : %s from %s (%s)" % (lever, os.path.basename(dpath), sec))
            if step == "skin-points":
                for lever in ("PTS_BOX", "PTS_DROP"):
                    if lever not in sets and (dj.get("points") or {}).get(lever): sets[lever] = str(dj["points"][lever]); say("  design  : %s from %s" % (lever, os.path.basename(dpath)))
    except (OSError, ValueError, TypeError) as ex_:
        say("  design  : skin\\DESIGN.json not read (%s)" % str(ex_)[:60])
    # FEATURES  resolved against
    # FEATURES
    for k_ in list(sets):
        v_ = str(sets[k_]).strip()
        if k_ in ("FEATURES", "LINES", "RAILS", "STL", "BODY", "NEW", "PIECE", "SHAPE") and v_ and not os.path.isabs(v_) and ("\\" in v_ or "/" in v_ or v_.lower().endswith((".json", ".brep", ".stl"))):
            _cands = [os.path.join(os.getcwd(), v_), os.path.join(kit.ROOT, v_), os.path.join(kit.ROOT, "claude_code", v_), os.path.join(folder, v_), os.path.join(folder, "skin", v_)]
            _hit = next((c_ for c_ in _cands if os.path.isfile(c_)), None)
            if _hit: sets[k_] = os.path.abspath(_hit); say("  lever   : %s=%s resolved to %s (a relative path is read from the folder the command ran in, then the project root, claude_code\\, the job folder, its skin\\ - 31bx R6 F6)" % (k_, v_, sets[k_]))
            else: say("kit rebuild REFUSED: --set %s=%s names no file in any of the places a relative path is read from: %s (31bx R6 F6)" % (k_, v_, "; ".join(_cands))); return 2
    unknown = [k for k in sets if k not in LEVERS]
    if unknown:
        say("kit rebuild: --set names a lever NO script of the chain reads: %s (a lever nothing reads is a silent skip)" % ", ".join(unknown)); return 2
    for k, v in sets.items():
        if k in LEVER_RANGE:
            lo_, hi_, why_ = LEVER_RANGE[k]
            try:
                fv = float(v)
            except ValueError:
                say("kit rebuild REFUSED: %s=%r is not a number" % (k, v)); return 2
            if not (lo_ <= fv <= hi_):
                say("kit rebuild REFUSED: %s=%s is outside %g..%g - %s" % (k, v, lo_, hi_, why_)); return 2
    tag = kit._opt(rest, "--tag") or sets.get("LK_TAG")
    if not tag:
        say("kit rebuild: no tag. --tag <T> names the log, the env record and every REBUILD_*.json of this run."); return 2
    if not re.match(r"^[A-Za-z0-9_-]+$", tag):
        say("kit rebuild: the tag is letters, digits, _ or - (it names files): %r" % tag); return 2
    tj_p = os.path.join(folder, "TRIAL.json"); bn_p = os.path.join(folder, FILES["body_new"]); bt_p = os.path.join(folder, "body_trial.brep")
    _tja0 = {}      # ACCEPTED
    if not plan and os.path.isfile(tj_p) and os.path.isfile(bn_p):
        try: _tja0 = json.load(open(tj_p, encoding="utf-8")) or {}
        except (OSError, ValueError): _tja0 = {}
    if not plan and os.path.isfile(tj_p) and os.path.isfile(bn_p) and not _tja0.get("accepted") and not (_tja0.get("body_md5") and _md5(bn_p) == _tja0.get("body_md5")):
        try:
            os.replace(bn_p, bt_p)
            say("  TRIAL   : body_new.brep was a trial's body (a trial STEP 4 that did not finish) - renamed body_trial.brep: a trial's body is never body_new.brep")
        except OSError:
            pass
    # ACCEPTED
    if not plan and os.path.isfile(tj_p) and ((step == "reinsert" and str(sets.get("STEP", "")) in ("2", "3", "4")) or step == "skin-build"):
        try: tj_ = json.load(open(tj_p, encoding="utf-8"))
        except (OSError, ValueError): tj_ = {}
        if tj_.get("accepted"):
            pp_ = os.path.join(folder, FILES["skin_piece"]); same_ = os.path.isfile(pp_) and tj_.get("piece_md5") == _md5(pp_)
            if step == "reinsert" or same_:
                say("kit rebuild REFUSED: the TRIAL of this piece was ACCEPTED at %s - it IS the model (body_new.brep). the client 2026-10-08: \"If a trial passes, do not\n"
                    "  rebuild it, do not reinsert it.\" Next: kit review -> kit check -> kit look -> kit accept on body_new.brep. A different piece (new points or lines)\n"
                    "  is a new job over the applied model (BURRITO_STEPS: going back into a done edit)." % tj_.get("accepted_when")); return 2
    try:
        sess = G.session(kit.ROOT) or {}
    except Exception:
        sess = {}
    mor = sess.get("model_of_record") or ""
    env = {k: v for k, v in os.environ.items() if not (k.startswith(kit.LEVER_PREFIXES) or k in LEVERS)}
    env["KIT_HOME"] = kit.HERE; env["PYTHONUTF8"] = "1"; env["PYTHONIOENCODING"] = "utf-8"; env["PYTHONUNBUFFERED"] = "1"
    if (os.environ.get("KIT_SCRATCH_ROOT") or "").strip(): env["KIT_SCRATCH_ROOT"] = os.environ["KIT_SCRATCH_ROOT"]
    defaults = step_defaults(step, folder, mor)
    used_default = {}
    for k, v in defaults.items():
        if k not in sets and v != "":
            env[k] = v; used_default[k] = v
    from_build_ = {}
    if step == "skin-wires":      # skin-build
        try:
            _eb = sorted([dict(json.load(open(os.path.join(folder, f_), encoding="utf-8")), _file=f_) for f_ in os.listdir(folder) if f_.startswith("env_skin-build_") and f_.endswith(".json")], key=lambda r_: str(r_.get("_when", "")), reverse=True)
            _lp = os.path.join(folder, "skin", "piece_skin.brep"); _lm = _md5(_lp) if os.path.isfile(_lp) else None; _how = "the newest skin-build on record (no tag copy of the live piece matched)"
            for r_ in _eb:
                tp_ = os.path.join(folder, "tags", str(r_.get("_tag", "")), "piece_skin.brep")
                if _lm and os.path.isfile(tp_) and _md5(tp_) == _lm: _eb = [r_] + [x_ for x_ in _eb if x_ is not r_]; _how = "the skin-build that made the live piece (tag %s)" % r_.get("_tag"); break
            if _eb:
                for k_ in ROOM_LEVERS:
                    if k_ not in sets and str(_eb[0].get(k_) or "").strip(): env[k_] = str(_eb[0][k_]); used_default[k_] = env[k_]; from_build_[k_] = _eb[0]["_file"]
                if from_build_: say("  build   : %s from %s (%s) - the room line estimates with the build's own levers (31bq R5e / R7c); a build run with other --set values will disagree with this estimate" % (", ".join("%s=%s" % (k_, env[k_]) for k_ in sorted(from_build_)), _how, _eb[0]["_file"]))
        except (OSError, ValueError, TypeError) as _exb: say("  build   : the last skin-build's levers not read (%s) - the room line uses the script's defaults" % str(_exb)[:60])
        # skin-build
        # skin-build  over the
        try:
            _pbe = dict(step_defaults("skin-build", folder, mor))
            _ebl = locals().get("_eb") or []
            if _ebl: _pbe.update({k_: str(v_) for k_, v_ in _ebl[0].items() if k_ in LEVERS and k_ not in ("BODY", "RUN", "STL", "TAG") and str(v_).strip() != ""})
            env["PREFLIGHT_BUILD_ENV"] = json.dumps({k_: str(v_) for k_, v_ in _pbe.items() if str(v_).strip() != ""})
        except Exception as _expb: say("  preview : the build's levers for the preview child could not be gathered (%s) - the child takes the card's proven set" % str(_expb)[:60])
    for k, v in fixed.items():
        env[k] = v
    env.update(sets); env["LK_TAG"] = tag
    missing = [k for k in card if k not in sets]
    if step == "reinsert" and "STEP" in sets and sets["STEP"] not in ("1", "2", "3", "4"):
        say("kit rebuild: STEP is 1, 2, 3 or 4 (--set STEP=n), not %r" % sets["STEP"]); return 2
    if missing:
        say("kit rebuild REFUSED: %s reads %d CARD lever(s) this run does not set: %s\n"
            "  A CARD lever is a number the edit region decides - --set %s (an empty value is a decision too: --set PLANES=)."
            % (step, len(missing), ", ".join(missing), " ".join("%s=..." % m for m in missing)))
        return 2
    locked_keys = set()
    lk_ = layout_lock(folder) if step in LOCKED_LEVERS else None
    if lk_ and step in (lk_.get("levers") or {}):
        lock_backfill(folder, lk_, step, say, write=not plan)
        bad_ = []
        for k, v in lk_["levers"][step].items():
            if k in sets:
                if not _same_val(sets[k], v): bad_.append((k, sets[k], v))
            else:
                if v is None:
                    env.pop(k, None); used_default.pop(k, None)
                else:
                    env[k] = v
                locked_keys.add(k)
        if bad_:
            say("kit rebuild REFUSED: the layout's section-wide settings were fixed when its first layout was judged ok (%s, tag %s - skin\\LAYOUT_LOCK.json):\n%s\n"
                "  the client 2026-10-07: \"Yes to changing it through points, it should still be able to have the lines that build it tweaked without selecting new\n"
                "  points.\" A face changes through its own points (kit rebuild skin-points: PTS_BOX / PTS_DROP), its lines through skin-wires LINES / RAILS.\n"
                "  Drop these --set (the locked values are taken) or give the locked value."
                % (lk_.get("when"), lk_.get("tag"), "\n".join("    %s=%s - locked at %s" % (k, s_, "the script's own value (not set)" if v is None else v) for k, s_, v in bad_)))
            return 2
    # recorded
    if (step in SHELVED or (step == "reinsert" and str(env.get("JOIN", "")).strip().lower() == "fuse")) and not str(sets.get("SHELVED_OK", "")).strip():
        if step in VOXEL:
            say("kit rebuild REFUSED: %s is SHELVED (2026-10-08, the client: \"the entire voxel step is now getting skipped. shelve it in the kit, as it may be used\n"
                "  another time. Instead of voxel the wireframe redraw will handle all geometry corrections\"). The skin route runs on the original's own mesh:\n"
                "  kit rebuild skin-source (content.brep -> source.stl), reinsert --set STEP=1, then skin-regions .. skin-wires - the lines are where the\n"
                "  geometry is corrected (LINES / RAILS / _add, decided from the pictures) - then skin-build (NURBS first).\n"
                "  --set SHELVED_OK=\"<why>\" runs the voxel step anyway and records the reason." % step); return 2
        say("kit rebuild REFUSED: %s is SHELVED (2026-10-06, the client: \"There is a new burrito process and it works. The old process gets ~1/2 shelved\").\n"
            "  The triangle piece's back half (decimate, fillholes, finish, brep, keep, the exact-plane fuse) made 1.5k faces against the\n"
            "  edit region's 142; the SKIN ROUTE replaces it: reinsert --set STEP=1, then skin-regions .. skin-look, then reinsert --set STEP=2 (JOIN=sew).\n"
            "  --set SHELVED_OK=\"<why>\" runs it anyway and records the reason." % (step if step != "reinsert" else "reinsert JOIN=fuse")); return 2
    makers = {FILES["content"]: "region", FILES["walls"]: "region", FILES["arr_raw"]: "arrange-m", FILES["arr"]: "arrange-f", FILES["blend"]: "blend", FILES["piece"]: "repair",
              FILES["dec"]: "decimate", FILES["decf"]: "fillholes", FILES["final"]: "finish", FILES["brep"]: "brep", FILES["keep"]: "keep", FILES["body_new"]: "reinsert (STEP=3)",
              "piece_skin.brep": "skin-build", FILES["wall_caps"]: "reinsert (STEP=1)", FILES["source"]: "skin-source"}
    for k in ("SRC", "STL", "WALLS", "ORIG", "PIECE", "NEW", "BODY", "WINDOW", "REGION"):
        v = env.get(k)
        if k == "REGION" and v and v.lower() in ("none", "-", "window"): continue
        if k == "PIECE" and step == "reinsert" and str(env.get("STEP")) == "1": continue
        if v and not os.path.isfile(v) and not plan:
            mk = makers.get(os.path.basename(v))
            say("kit rebuild REFUSED: %s = %s does not exist%s" % (k, v, (" - `kit rebuild %s` makes it" % mk) if mk else ("" if k != "BODY" else " - no session model of record; --set BODY=<the .brep of record>")))
            return 2
    if step in ("arrange", "arrange-m", "blend", "review", "review-body") and not env.get("WIN"):
        say("kit rebuild REFUSED: no WIN - the region step records it in %s; run `kit rebuild region` first or --set WIN=\"x0 x1 y0 y1 z0 z1\"" % FILES["region_rec"]); return 2
    if step == "blend" and str(env.get("KEEP", "0")) == "1" and os.path.basename(str(env.get("STL", ""))) != FILES["arr"]:
        say("kit rebuild REFUSED: KEEP=1 needs the arrangement's FINISHED base (%s from `kit rebuild arrange-f`); STL is %s - L105: keep-and-weld keeps the base, so the base must be the clean one" % (FILES["arr"], os.path.basename(str(env.get("STL", ""))) or "unset")); return 2
    if step == "arrange" and not plan and str(env.get("SPLIT", "seq")) != "more" and not os.path.isfile(os.path.join(folder, "cells.brep")):
        okj, why = cuts_verdict(folder, "region")
        if not okj:
            say("kit rebuild REFUSED: %s.\n  Open every frame of review\\region_cuts_*.png (the edit region's walls in red on the body), then\n"
                "  kit rebuild judge --job %s --what region --verdict ok --note \"<where the walls cut, across what>\"   (move: WIN / PLANES, region again)" % (why, job)); return 2
        say("  cuts    : %s" % why)
    if step == "reinsert" and str(env.get("STEP")) in ("1", "2") and not plan and os.path.basename(str(env.get("REGION", ""))) == FILES["keep"]:
        okj, why = cuts_verdict(folder, "keep")
        if not okj:
            say("kit rebuild REFUSED: %s.\n  Open every frame of keep\\keep_cuts_*.png (the cuts in red: where kept meets rebuilt), then\n"
                "  kit rebuild judge --job %s --what keep --verdict ok --note \"<where the cuts run, across what>\"   (move: KEEP_OFFSET / KEEP_CELL, keep again)" % (why, job)); return 2
        say("  cuts    : %s" % why)
    # THE CUTS ARE JUDGED BEFORE THE SKIN ROUTE  kit rebuild
    # skin-source  skin-source  content.brep
    if not plan and (step == "skin-source" or (step == "reinsert" and str(env.get("STEP")) == "1")):
        okr_, whyr_ = cuts_verdict(folder, "region")
        if not okr_:
            say("kit rebuild REFUSED: %s.\n  THE CUTS ARE JUDGED BEFORE THE SKIN ROUTE: open every frame of review\\region_cuts_*.png and review\\region_fit_*.png, then\n"
                "  kit rebuild judge --job %s --what region --verdict ok --note \"<where the walls cut, across what>\"   (move: WIN / PLANES, region again) (31bq R7W D10)" % (whyr_, job)); return 2
        say("  cuts    : %s" % whyr_)
    # REINSERT FACES COME FIRST
    if step in SKIN and step != "skin-source" and not plan and not os.path.isfile(os.path.join(folder, FILES["wall_caps"])):
        say("kit rebuild REFUSED: wall_caps.brep is missing - THE REINSERT FACES COME FIRST (the client 2026-10-06: \"Step 1 is get the perfect reinsert\n"
            "  faces. Literally the very first thing to do.\"). The body's own section faces on the edit region walls are the skin's caps, and every\n"
            "  skin face ends on their edges:\n  kit rebuild reinsert --job %s --tag <T> --set STEP=1" % job); return 2
    # --supersede  skin-labels
    why_sup = kit._opt(rest, "--supersede")
    if step in ("skin-labels", "skin-rim") and not plan and str(why_sup or "").strip():      # skin-rim
        supersede_for_kit_update(folder, why_sup, say)
    elif why_sup is not None and not plan:
        say("kit rebuild REFUSED: --supersede is skin-labels' or skin-rim's (the layout is re-made from there); on %s it means nothing" % step); return 2
    # kit rebuild
    if step in OK_GUARDS and not plan:
        okj = standing_ok(folder, OK_GUARDS[step])
        if okj and step == "skin-features":
            def _nfm(d):
                if isinstance(d, dict): return {str(k_): _nfm(v_) for k_, v_ in d.items()}
                if isinstance(d, (list, tuple)): return sorted(str(x_) for x_ in d)
                return str(d)
            try:
                _fv = str(sets.get("FEATURES") or "").strip(); _cur = os.path.join(folder, "skin", "features.json")
                _new = json.load(open(_fv, encoding="utf-8")) if _fv and os.path.isfile(_fv) else None
                _old = json.load(open(_cur, encoding="utf-8")) if os.path.isfile(_cur) else None
                _same = (_new is None and _old is None) or (_new is not None and _old is not None and _nfm(_new) == _nfm(_old))
            except Exception:
                _same = False
            if _same: say("  features: the same map as the judged layout's (skin\\features.json) - a re-run changes nothing of it; allowed (31bx R6 F9)"); okj = None
        if okj:
            what_ = OK_GUARDS[step]
            fail_ = downstream_failure_since(folder, what_, okj)
            if fail_:
                supersede_after_failure(folder, what_, okj, fail_, say)
            else:
                n_ref = _refused_bump(folder, what_, okj.get("md5"))
                tail = _undo_strike(kit, "re-running %s over a %s judged ok at %s, after the refusal that named the two ways" % (step, what_, okj.get("when")),
                                    " ".join(["kit rebuild", step] + list(rest)), say) if n_ref >= 2 else ""
                say("kit rebuild REFUSED: %s would replace the %s that was judged OK on its pictures at %s (\"%s\"). It STANDS. THE TWO WAYS TO RE-MAKE IT (31bk):\n"
                    "  (1) a picture you have opened shows it wrong: kit rebuild judge --job %s --what %s --verdict redo --frame <it> --note \"<what it shows>\" --face <n>;\n"
                    "  (2) a later step (%s) FAILED or was KILLED on it (the BUILD_LOG) - then this step runs by itself, as a layout round.\n"
                    "  Neither is on the record now. A measurement alone is not a reason (the client 2026-10-07: \"It has to stop.\").%s%s"
                    % (step, what_, okj.get("when"), (okj.get("note") or "")[:80], job, what_, ", ".join(DOWNSTREAM.get(what_, ())),
                       "" if n_ref >= 2 else " This is the first refusal against this ok; the next attempt against it is a strike.", tail)); return 2
    if not plan and step == "skin-points": release_void_spots(folder, say)      # nothing to pick  released
    if not plan and (step in AFTER_POINTS or (step == "reinsert" and str(env.get("STEP")) in ("2", "3", "4") and os.path.basename(str(env.get("PIECE", ""))) == "piece_skin.brep")):
        ref = restart_refusal(folder, step, say) or wires_refusal(folder, step)
        if ref: say(ref); return 2
    # skin-labels
    if step in ("skin-mirror", "skin-network", "skin-build") and not plan:
        dec = _mirror_decision(folder); norm = lambda x: " ".join(str(x or "").replace(",", " ").lower().split())
        if dec is None and step == "skin-network" and "MIRROR" not in sets:
            say("kit rebuild REFUSED: no symmetry decision on record (skin\\MIRROR_DECISION.json - skin-labels writes it since 31an). Re-run skin-labels with\n"
                "  --set \"MIRROR=x 0\" (or --set MIRROR= for an edit that is not symmetric), or give it here: --set \"MIRROR=...\"" ); return 2
        if dec is not None and "MIRROR" in sets and norm(sets["MIRROR"]) != norm(dec):
            say("kit rebuild REFUSED: MIRROR=%r differs from the card's decision at skin-labels (%r). The layout was made %s; re-run skin-labels with the\n"
                "  plane you mean (the layout changes with it)." % (sets["MIRROR"], dec, ("mirrored across " + dec) if dec else "as not symmetric")); return 2
    if step == "skin-mirror" and not plan and str(env.get("WHAT", sets.get("WHAT", ""))).strip().lower() == "piece":
        okl, whyl = cuts_verdict(folder, "look")
        if not okl:
            say("kit rebuild REFUSED: %s.\n  THE LOOK FIRST (31az): kit rebuild skin-look --job %s --tag <T>; open EVERY frame of skin\\review\\PIECE_LOOK.json; then\n"
                "  kit rebuild judge --job %s --what look --verdict ok --note \"<what every frame shows>\" - or redo --face <n> and fix the piece THERE.\n"
                "  The mirror check of a piece the pictures show wrong is pointless (the client 2026-10-08: rework the edit, do not move to the next step)." % (whyl, job, job)); return 2
        say("  look    : %s" % whyl)
    if step == "skin-network" and not plan:
        okj, why = cuts_verdict(folder, "layout")
        if not okj:
            say("kit rebuild REFUSED: %s.\n  Open every frame skin-rim listed (skin\\review\\LAYOUT_LOOK.json: the layout's LAYOUT_* from every side and the rim's SP12_*), then\n"
                "  kit rebuild judge --job %s --what layout --verdict ok --note \"<the faces you see, the borders, anything missing or one-sided>\"" % (why, job)); return 2
        say("  layout  : %s" % why)
        plane = str(env.get("MIRROR", "")).strip()
        if _mirror_decision(folder) is None:
            try:
                with open(os.path.join(folder, "skin", "MIRROR_DECISION.json"), "w", encoding="utf-8") as fh:
                    json.dump({"plane": plane, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "tag": tag, "step": "skin-network"}, fh)
            except OSError:
                pass
        if plane:
            okm, whym = _mirror_ok(folder, "layout", plane)
            if not okm:
                say("kit rebuild REFUSED: the edit is symmetric about %s (MIRROR) and %s.\n  kit rebuild skin-mirror --job %s --tag <T> --set WHAT=layout --set \"MIRROR=%s\"   (the client 2026-10-06: a face with no partner on the other side is a defect)" % (plane, whym, job, plane)); return 2
            say("  mirror  : %s" % whym)
        else:
            say("  mirror  : MIRROR is empty - the card's decision that this edit is not symmetric (no mirror check)")
    # THE FEATURE MAP
    # skin-rim  skin-features  skin-labels
    if step == "skin-rim" and not plan:
        try:
            mine_ = "merge_smooth" in json.load(open(os.path.join(folder, "skin", "patches_labels.json"), encoding="utf-8"))
        except (OSError, ValueError):
            mine_ = False
        if not mine_:
            say("kit rebuild REFUSED: skin-labels' layout has not been through THE FEATURE MAP since it was made - every original face that got a point is\n"
                "  still its own face. kit rebuild skin-features --job %s --tag <T>: open FEAT_labels_* (each original face's id), name each one's FEATURE\n"
                "  (the client: \"A spine, A vane, a support\"), write {\"feature\": [ids]} and run it again with --set FEATURES=<that json>; then skin-rim" % job); return 2
    # skin-wires
    if step == "skin-build" and not plan:
        okl_, whyl_ = room_levers_check(folder, env)
        if okl_ is False:
            say("kit rebuild REFUSED: %s" % whyl_); return 2
        if whyl_: say("  room    : %s" % whyl_)
    if step == "skin-build" and not plan:
        okw, whyw = cuts_verdict(folder, "wires")
        if not okw:
            say("kit rebuild REFUSED: %s.\n  THE WIREFRAME comes before the faces: kit rebuild skin-wires --job %s --tag <T> [--set LINES=<json>] [--set RAILS=<json>]; open every\n"
                "  WIRE_* frame (skin\\review\\WIRES_LOOK.json: each line, its chain number, what it IS), then\n"
                "  kit rebuild judge --job %s --what wires --verdict ok --note \"<the lines you see - each where its feature's edge is, one simple curve>\"" % (whyw, job, job)); return 2
        say("  wires   : %s" % whyw)
    # mirror checks should pass before creating a real model
    # body_trial.brep
    # kit rebuild  body_trial.brep
    trial = bool(str(sets.get("TRIAL", "")).strip()) and step == "reinsert"
    st_ = str(env.get("STEP"))
    if step == "reinsert" and not plan and st_ in ("3", "4"):
        tj = {}
        if os.path.isfile(tj_p):
            try:
                tj = json.load(open(tj_p, encoding="utf-8"))
            except (OSError, ValueError):
                tj = {"why": "?"}
        if not trial and os.path.isfile(tj_p):
            say("kit rebuild REFUSED: the last STEP 2 was a TRIAL (%s, %s) - a real STEP 3 / 4 does not continue it: what a trial sewed becomes body_new.brep only by\n"
                "  its ACCEPTANCE (31aw: two reviewers, then judge --what trial --verdict ok). Finish the trial with --set TRIAL=\"%s\" on STEP 3 and 4, or start the\n"
                "  REAL reinsert at STEP 2 without TRIAL (the piece judged after the second reviewer, mirror-checked)." % (tj.get("when"), tj.get("why"), tj.get("why", "<why>"))); return 2
        if trial and not os.path.isfile(tj_p):
            say("kit rebuild REFUSED: TRIAL on STEP %s continues a trial that STEP 2 started - the last STEP 2 was not a trial. Start the trial there:\n"
                "  kit rebuild reinsert --job %s --tag <T> --set STEP=2 --set TRIAL=\"<why>\"" % (st_, job)); return 2
        if trial:
            _pp1 = str(env.get("PIECE", "")); _pm1 = _md5(_pp1) if os.path.isfile(_pp1) else None; _no1 = []
            if not tj.get("run_id"): _no1.append("TRIAL.json carries no STEP 2 run id (a trial of an older kit)")
            if not tj.get("step2_ok"): _no1.append("its STEP 2 did not finish (refused, failed or never run - TRIAL.json %s, %s)" % (tj.get("when"), str(tj.get("why", ""))[:60]))
            if not tj.get("piece_md5") or tj.get("piece_md5") != _pm1: _no1.append("it is the trial of another piece (TRIAL.json piece_md5 %s; %s now %s)" % (str(tj.get("piece_md5"))[:8], os.path.basename(_pp1), str(_pm1)[:8]))
            if _no1:
                say("kit rebuild REFUSED: TRIAL STEP %s continues the trial STEP 2 that sewed THIS piece, and there is none: %s.\n"
                    "  Start the trial at STEP 2: kit rebuild reinsert --job %s --tag <T> --set STEP=2 --set TRIAL=\"<why>\" (31bq R7W D1)" % (st_, "; ".join(_no1), job)); return 2
        if trial and "--bg" in rest:
            say("kit rebuild REFUSED: a TRIAL's STEP %s runs in the foreground - its body is renamed body_trial.brep when the step ends" % st_); return 2
    if trial and not plan and st_ == "2" and os.path.basename(str(env.get("PIECE", ""))) == "piece_skin.brep":
        okl, whyl = cuts_verdict(folder, "look")
        if not okl:
            say("kit rebuild REFUSED: %s.\n  THE LOOK FIRST (31az): kit rebuild skin-look --job %s --tag <T>; open EVERY frame of skin\\review\\PIECE_LOOK.json; then\n"
                "  kit rebuild judge --job %s --what look --verdict ok --note \"<what every frame shows>\" - or redo --face <n> and fix the piece THERE first.\n"
                "  A trial of a piece the pictures show wrong is not run (the client 2026-10-08)." % (whyl, job, job)); return 2
        say("  look    : %s" % whyl)
        # mirror checks should pass before creating a real model
        plane_ = _mirror_decision(folder) or ""
        if plane_:
            okm, whym = _mirror_ok(folder, "piece", plane_)
            if not okm:
                say("kit rebuild REFUSED: the edit is symmetric about %s and %s - a trial model of a piece that is not symmetric is pointless (the client 2026-10-07:\n"
                    "  \"mirror checks should pass before creating a real model\"). kit rebuild skin-mirror --job %s --tag <T> --set WHAT=piece; fix the\n"
                    "  piece (its points, its lines) until it passes, then the trial." % (plane_, whym, job)); return 2
            say("  mirror  : %s" % whym)
    if trial and st_ == "2":
        say("  TRIAL   : a look at the real model (%s) - the piece's verdict (the second reviewer) is not asked for yet; the body is body_trial.brep" % sets["TRIAL"])
    if step == "reinsert" and str(env.get("STEP")) == "2" and not plan and not trial and os.path.basename(str(env.get("PIECE", ""))) == "piece_skin.brep":
        okj, why = cuts_verdict(folder, "skin")
        if not okj:
            say("kit rebuild REFUSED: %s.\n  kit rebuild skin-look --job %s --tag <T>; open every frame (skin\\review\\PIECE_LOOK.json), then\n"
                "  kit rebuild judge --job %s --what skin --verdict ok --note \"<the faces, the borders, any lump, fold or missing face>\"" % (why, job, job)); return 2
        say("  piece   : %s" % why)
        try:
            plane = (json.load(open(os.path.join(folder, "skin", "MIRROR_DECISION.json"), encoding="utf-8")).get("plane") or "").strip()
        except (OSError, ValueError):
            plane = ""
        if plane:
            okm, whym = _mirror_ok(folder, "piece", plane)
            if not okm:
                say("kit rebuild REFUSED: the edit is symmetric about %s and %s.\n  kit rebuild skin-mirror --job %s --tag <T> --set WHAT=piece --set \"MIRROR=%s\"" % (plane, whym, job, plane)); return 2
            say("  mirror  : %s" % whym)
    if step in ("keep", "skin-edges") and not plan:
        rows = write_frozen(kit, folder, say)
        if rows:
            say("  frozen  : %s" % ", ".join("%s%s%s" % (r["name"], " (buried_ok)" if r["buried_ok"] else "", "" if r["surface_exists"] else " [surface file MISSING]") for r in rows))
        else:
            say("  frozen  : none (no atlas, or no FROZEN region meets the edit region)")
    # recorded
    whole = []
    try:
        import kit_crop as KC
        ext = None
        try:
            ad = G.atlas_load(kit.ROOT) or {}
            be = (ad.get("body_extent") or {}).get("box")
            if be and len(be) == 6:
                ext = ([float(be[0]), float(be[2]), float(be[4])], [float(be[1]), float(be[3]), float(be[5])])
        except Exception:
            ext = None
        for k in ("STL", "SRC"):
            v = env.get(k, "")
            if v.lower().endswith(".stl") and os.path.isfile(v):
                big, why = KC.body_sized(v, ext)
                if big: whole.append((k, os.path.basename(v), why))
    except ImportError:
        pass
    why_wb = kit._opt(rest, "--whole-body")
    if whole and not why_wb:
        say("kit rebuild REFUSED: %s is the WHOLE BODY (%s). The chain's unit of work is a WINDOW: cut it with `kit rebuild region`\n"
            "  and run every step on the edit region's files. If there is genuinely no other way, --whole-body \"<why>\" runs it and records the reason."
            % (", ".join(k for k, _, _ in whole), "; ".join("%s: %s" % (b, w) for _, b, w in whole)))
        return 2
    if step == "reinsert" and env.get("STEP") == "3" and not plan and not (env.get("TRIAL") or "").strip():      # no region
        try:
            if G.atlas_needs_assignment(kit.ROOT) and not (G.atlas_assignment(kit.ROOT, job) or G.atlas_assignment(kit.ROOT, tag)):
                say("kit rebuild REFUSED: STEP 3 writes new B-rep geometry and the atlas does not say which region it belongs to.\n"
                    "  kit atlas assign %s --to <existing region>\n"
                    "  kit atlas assign %s --new <name> --what \"<its physical definition>\"   (then announce it to the client)" % (job, job))
                return 2
        except AttributeError:
            pass
    needs_fc = True
    runner = kit.freecad()
    cmdline = [runner, path]
    say("kit rebuild: %s -> %s   (%s)" % (step, script, what))
    say("  job     : %s" % folder)
    say("  tag     : %s" % tag)
    _pg = step_page(step)
    if _pg: say(_pg)
    say("  runs under: %s (every step: one interpreter, FreeCAD's numpy/scipy/vtk)" % os.path.basename(runner))
    shown = [k for k in LEVERS if k in env and k != "LK_TAG"]
    for k in shown:
        src = "set      " if k in sets else ("fixed    " if k in fixed else ("locked   " if k in locked_keys else ("build    " if k in from_build_ else "suggested")))      # skin-build
        say("    %s %-11s = %s%s" % (src, k, env[k],      # 31bx (R1 F2)
                                   ("   (suggested %s)" % DEFAULTS.get(step, {})[k]) if (k in sets and k in DEFAULTS.get(step, {}) and DEFAULTS[step][k] != sets[k]) else ""))
    if whole and why_wb:
        say("  WHOLE BODY: %s - run on the recorded exception: %s" % (", ".join(k for k, _, _ in whole), why_wb))
    rec = {"_step": step, "_script": script, "_when": time.strftime("%Y-%m-%d %H:%M:%S"), "_job": job, "_tag": tag,
           "_sources": {k: ("--set" if k in sets else ("fixed" if k in fixed else ("locked" if k in locked_keys else (("skin-build " + from_build_[k]) if k in from_build_ else "suggested")))) for k in shown}}
    rec.update({k: env[k] for k in shown})
    if why_wb: rec["_whole_body_because"] = why_wb
    envfile = os.path.join(folder, "env_%s_%s.json" % (step, tag))
    if not plan:
        try:
            with open(envfile, "w", encoding="utf-8") as fh:
                json.dump(rec, fh, indent=1)
            say("  env file: %s" % os.path.basename(envfile))
        except OSError as e:
            say("  env file: NOT written (%s)" % e)
    W = kit._wallclock()
    # kit rebuild  kit rebuild
    row = "kit rebuild %s" % step + ((" STEP=%s" % env.get("STEP")) if step == "reinsert" else "")
    # skin-build
    if step == "skin-look": row += " LOOK_MODE=%s" % ("faces" if str(env.get("FACES") or "").strip() else ((env.get("LOOK_MODE") or "quick").strip().lower() or "quick"))
    elif step == "skin-wires": row += " PREFLIGHT=%s" % ("1" if str(env.get("PREFLIGHT", "1")) == "1" else "0")
    elif step == "skin-build":
        try: _nf9 = len((json.load(open(os.path.join(folder, "skin", "fillets.json"), encoding="utf-8")) or {}).get("fillets") or [])
        except (OSError, ValueError, TypeError, AttributeError): _nf9 = 0
        row += " LINES=%d" % (1 if (_nf9 and str(env.get("FILLET_RERUN", "1")) == "1") else 0)
    budget_min, why = (W.budget_for(row, "Bash", kit.ROOT) if W else (4.0, "no wall clock module"))
    cap = max(int(budget_min * 60 * 2), 360)
    say("  budget  : %.1f min (%s); cap %d s - a step that declares itself busy (a long kernel call) is waited for up to its own allowance, said in the heartbeat; the hard ceiling is 3x the cap of UNDECLARED time (31bw K33)" % (budget_min, why, cap))
    if plan:
        say("  --plan: nothing was run."); return 0
    log = os.path.join(folder, "log_%s_%s.txt" % (step, tag))
    outs = step_outputs(step, env)
    try:
        import shutil as _sh
        free_gb = _sh.disk_usage(folder).free / 1e9
        need = float(kit.ENV.get("min_free_gb", 0.8))
        if step == "reinsert" and env.get("BODY") and os.path.isfile(env["BODY"]):
            need = max(need, 4.0 * os.path.getsize(env["BODY"]) / 1e9)
        if free_gb < need:
            say("kit rebuild REFUSED: %.2f GB free on the job's disk, this step needs %.2f GB (env.json min_free_gb, or 4x the body for the reinsert).\n"
                "  Free space first - old jobs' _local.bin/_rest.bin/_local_res.bin and body_new.brep are the usual weight." % (free_gb, need))
            return 2
    except Exception:
        pass
    # recorded
    _rid = None
    if step == "reinsert" and st_ == "2": _rid = "%s-%s" % (tag, time.strftime("%Y%m%d-%H%M%S")); env["LK_RUN_ID"] = _rid
    elif step == "reinsert" and st_ in ("3", "4") and trial and not plan: env["LK_RUN_ID"] = str(tj.get("run_id") or "")
    # body_trial.brep
    if trial and st_ == "2":
        pp_ = os.path.join(folder, FILES["skin_piece"])
        try:
            with open(tj_p, "w", encoding="utf-8") as fh:
                json.dump({"why": sets["TRIAL"], "when": time.strftime("%Y-%m-%d %H:%M:%S"), "tag": tag, "piece_md5": _md5(pp_) if os.path.isfile(pp_) else None, "done": False, "run_id": _rid, "step2_ok": False}, fh, indent=1)
        except OSError:
            pass
        if os.path.isfile(bn_p):
            try:
                os.replace(bn_p, os.path.join(folder, "body_new_before_trial.brep"))
                say("  TRIAL   : the real body_new.brep is kept aside as body_new_before_trial.brep (the trial's STEP 3 would overwrite it)")
            except OSError:
                pass
    if trial and st_ == "4" and os.path.isfile(bt_p):
        try:
            os.replace(bt_p, bn_p)
        except OSError:
            pass
    if "--bg" in rest:
        name = "rebuild_%s_%s" % (step, tag)
        with open(log, "w", encoding="utf-8") as fh:
            p = subprocess.Popen(cmdline, cwd=folder, env=env, stdout=fh, stderr=subprocess.STDOUT,
                                 creationflags=(0x08000000 if os.name == "nt" else 0))
            if hasattr(kit, "pin_process"):
                kit.pin_process(p)
        if W:
            W.watch_add(kit.ROOT, name, budget_min, "kit rebuild %s (%s)" % (step, script), owner=G.current_conversation(kit.ROOT) or "", pid=p.pid)
        say("  started in the background, pid %d, log %s\n  ON THE CLOCK as %s - `kit collected %s` when it is read (L14); `--kill` ends it by pid." % (p.pid, log, name, name))
        return 0
    before = time.time()
    rc, out = kit.sh(cmdline, cap, log, env, cwd=folder, outputs=outs)
    took = time.time() - before
    rc = kit._judge_output(out, rc, log, "kit rebuild")
    typical = (W.table_budgets(kit.ROOT).get(row) if W else None)
    flag = "   RED FLAG - %.1fx the typical %.0f s (the client: 1.5x needs evaluating)" % (took / typical, typical) if typical and took > 1.5 * typical else ""
    if step == "skin-wires" and flag:
        try:
            _pfp = os.path.join(folder, "skin", "preflight.json")
            if os.path.isfile(_pfp) and os.path.getmtime(_pfp) >= before - 1.0:
                _pfj = json.load(open(_pfp, encoding="utf-8")) or {}
                flag += " - of which the PREVIEW child %.0f s on %d decided line(s) and %d changed face(s) of THIS layout (the mode row's typical lumps every layout)" % (float(_pfj.get("secs") or 0), len(_pfj.get("lines") or []), len(_pfj.get("faces") or []))
        except Exception: pass
    if str(rc) in ("3221225477", "-1073741819"): flag += " - FreeCADCmd CRASHED in-process (access violation 0xC0000005): a shape the kernel could not handle (a face with a large edge tolerance, an invalid solid) - the step's inputs, not its code; the log's last line names what it was doing"
    say("kit rebuild: rc %s, %.0f s%s, log %s" % (rc, took, flag, log))
    # body_trial.brep
    def _mv(a_, b_):
        try:
            if os.path.isfile(os.path.join(folder, a_)): os.replace(os.path.join(folder, a_), os.path.join(folder, b_))
            return True
        except OSError as ex_:      # body_trial.brep
            say("  RENAME FAILED: %s -> %s (%s) - the trial's files are NOT where the next step reads them; free the target (a read-only link?) and run the step again" % (a_, b_, ex_))
            return False
    if trial and st_ == "2":
        try:
            tj = json.load(open(tj_p, encoding="utf-8")); tj.update({"step2_ok": rc == 0, "step2_when": time.strftime("%Y-%m-%d %H:%M:%S")})
            with open(tj_p, "w", encoding="utf-8") as fh: json.dump(tj, fh, indent=1)
        except (OSError, ValueError):
            pass
    if trial and st_ == "3" and rc == 0:
        _ok3a = _mv(FILES["body_new"], "body_trial.brep"); _ok3b = _mv("REBUILD_reinsert.json", "REBUILD_reinsert_trial.json")
        if _ok3a and _ok3b: say("  TRIAL   : the body is body_trial.brep - next: kit rebuild reinsert --job %s --tag %s --set STEP=4 --set TRIAL=\"%s\"" % (job, tag, sets["TRIAL"]))
        else: rc = 1; say("  TRIAL   : STEP 3 ran but its files could NOT be renamed into the trial's place (above) - rc 1: NOT the next step; free the target and run STEP 3 again (31bq R7Wr)")
    if trial and st_ == "4":
        _mv(FILES["body_new"], "body_trial.brep"); _mv("REBUILD_check.json", "REBUILD_check_trial.json")
        _kl4 = key_line(out); _cp4 = rc == 0 and _kl4.strip().startswith("CHECK PASS")
        try:
            tj = json.load(open(tj_p, encoding="utf-8")); tj.update({"done": rc == 0, "check_pass": _cp4, "finished": time.strftime("%Y-%m-%d %H:%M:%S"), "check": _kl4, "trial_body_md5": (_md5(bt_p) if os.path.isfile(bt_p) else None)})
            with open(tj_p, "w", encoding="utf-8") as fh: json.dump(tj, fh, indent=1)
        except (OSError, ValueError):
            pass
        if _cp4:
            say("  TRIAL   : the body is body_trial.brep (a look until its acceptance). Next: kit rebuild review-body --job %s --tag %s (it reviews the trial's body) - open\n"
                "            every frame; wrong: kit rebuild judge --job %s --what trial --verdict redo --spot \"<box>\" | --face <n> --note \"...\"; right: THE ACCEPTANCE (31aw) -\n"
                "            kit rebuild second --job %s --what trial --assign (two cad-reviewers, each shard recorded), then kit rebuild judge --job %s --what trial --verdict ok\n"
                "            --note \"...\" (the trial becomes body_new.brep - nothing rebuilt or re-sewn)"
                % (job, tag, job, job, job))
        else:
            _ref4 = [l_.strip() for l_ in (out or "").splitlines() if l_.strip().startswith("REFUSED:")]
            say("  TRIAL   : the trial FAILED its own check (%s)%s - it is NOT reviewable and NOT acceptable (`second --what trial` and `judge --what trial --verdict ok` refuse it):\n"
                "            fix the piece where the REFUSED line(s) point (the seam, the PROTECT box, the void - its points, its lines) and run the trial again from STEP 2"
                % (_kl4[:100] or ("rc %s" % rc), (":\n            " + "\n            ".join(_ref4[:4])) if _ref4 else ""))
    if step == "reinsert" and st_ == "2" and not trial and rc == 0 and os.path.isfile(tj_p):
        try:
            os.remove(tj_p)
            say("  TRIAL   : a REAL reinsert has started - the trial is over (body_trial.brep stays only as the trial's picture source)")
        except OSError:
            pass
    if step == "review-body" and rc == 0 and os.path.basename(str(env.get("NEW", ""))) == "body_trial.brep":
        try:
            rvd = os.path.join(folder, "review_body"); od = env.get("OUT_DIR")
            if od and os.path.normcase(os.path.abspath(od)) != os.path.normcase(os.path.abspath(rvd)):
                say("  TRIAL   : the frames went to OUT_DIR %s - a trial is judged on review_body\\ (TRIAL_LOOK.json): run review-body again without OUT_DIR" % od)
            else:
                frs = sorted(f for f in os.listdir(rvd) if f.lower().endswith(".png") and os.path.getmtime(os.path.join(rvd, f)) >= before - 1)
                _rec = {"kind": "trial", "frames": frs, "md5": _md5(os.path.join(folder, "body_trial.brep")), "tag": tag}
                try:      # REVIEW_BODY_quality.json
                    _qj = json.load(open(os.path.join(rvd, "REVIEW_BODY_quality.json"), encoding="utf-8"))
                    _rec["frame_info"] = {f_: {"quality": q_} for f_, q_ in (_qj.get("frames") or {}).items() if f_ in frs}; _rec["mesh_quality"] = _qj.get("mesh_quality")
                except (OSError, ValueError): pass
                with open(os.path.join(rvd, "TRIAL_LOOK.json"), "w", encoding="utf-8") as fh:
                    json.dump(_rec, fh, indent=1)
                say("  TRIAL   : review_body\\TRIAL_LOOK.json lists the %d frames of the trial body - open every one, then kit rebuild judge --what trial ..." % len(frs))
        except OSError:
            pass
    kl = key_line(out)
    log_row(folder, tag, step + ((" STEP=%s" % env.get("STEP")) if step == "reinsert" else "") + ((" WHAT=%s" % env.get("WHAT")) if step == "skin-mirror" else ""), sets, kl, rc, took)
    try:
        skin_piece = os.path.basename(str(env.get("PIECE", ""))) == "piece_skin.brep"
        if step == "skin-build" and rc != 0:
            bx = []; _kf = build_kit_faults(out); _kff = kit_fault_faces(_kf); _skipped = 0; _outside = 0; _out_mids = []
            try:
                _w = [float(x) for x in (_window_of(folder) or "").split()]; _w = _w if len(_w) == 6 else None
            except Exception:
                _w = None
            try:
                for fr_ in (json.load(open(os.path.join(folder, "skin", "free_edges.json"), encoding="utf-8")).get("free") or []):
                    if os.path.getmtime(os.path.join(folder, "skin", "free_edges.json")) < before - 1: break
                    mid = fr_.get("mid")
                    if not mid: continue
                    if _kff and any(int(p_) in _kff for p_ in (fr_.get("pair") or [])): _skipped += 1; continue
                    if _w:
                        _mg = 5.0
                        if not (_w[0] - _mg <= mid[0] <= _w[1] + _mg and _w[2] - _mg <= mid[1] <= _w[3] + _mg and _w[4] - _mg <= mid[2] <= _w[5] + _mg):
                            _outside += 1; _out_mids.append([round(float(v), 1) for v in mid]); continue
                    bx.append([mid[0] - 2, mid[0] + 2, mid[1] - 2, mid[1] + 2, mid[2] - 2, mid[2] + 2])
            except (OSError, ValueError):
                pass
            if _outside: say("  TRIES   : %d free-edge spot(s) outside the edit region not counted (a broken shell's coordinates, 31bl): at %s" % (_outside, _out_mids[:6]))
            if _kf:
                say("  TRIES   : %d free-edge spot(s) at the kit-fault faces %s not counted (the build failed on a kit line: %s)%s"
                    % (_skipped, sorted(_kff), " | ".join(_kf[:2]), "; the %d spot(s) at the agent's own failures count" % len(bx) if bx else "; nothing else to count"))
            _wf = wires_try_faces(out)
            if _wf:
                record_wires_try(folder, _wf, tag, kl, say)
                bx = [b_ for b_ in bx if not _box_at_faces(folder, b_, _wf)]
            if bx or (not _kf and not _wf):
                record_try(folder, "skin-build", "build:" + tag, kl, bx, say)
        elif step == "skin-source" and rc == 0:
            restart_on_new_source(folder, say)
        elif step == "skin-build" and rc == 0:
            rounds_reset(folder, say)
            save_state(folder, tag, say)              # kit rebuild
            design_best(folder, say, "a passing skin-build (%s)" % tag)
        elif step == "skin-mirror" and rc != 0:
            what_ = str(env.get("WHAT", "")).lower()
            artp = os.path.join(folder, FILES["patches"] if what_ == "layout" else FILES["skin_piece"])
            bx = []
            try:
                for u_ in (json.load(open(os.path.join(folder, "skin", "mirror_%s.json" % what_), encoding="utf-8")).get("unpaired") or []):
                    c_ = u_.get("centre"); h_ = max(1.5, 0.5 * float(u_.get("area_mm2") or 0) ** 0.5 + 1.0)
                    if c_: bx.append([c_[0] - h_, c_[0] + h_, c_[1] - h_, c_[1] + h_, c_[2] - h_, c_[2] + h_])
            except (OSError, ValueError, TypeError):
                pass
            record_try(folder, "mirror %s" % env.get("WHAT"), _md5(artp) if os.path.isfile(artp) else "mirror:" + tag, kl, bx, say)
        elif step == "reinsert" and skin_piece and str(env.get("STEP")) in ("2", "4"):
            pp = os.path.join(folder, FILES["skin_piece"])
            if (rc != 0 or "CHECK FAIL" in out) and not trial:
                record_try(folder, "reinsert STEP %s" % env.get("STEP"), _md5(pp) if os.path.isfile(pp) else "reinsert:" + tag, kl, [], say)
            elif str(env.get("STEP")) == "4" and "CHECK PASS" in out and not trial:
                savepoint(kit, job, tag, "reinsert STEP 4 " + kl[:140])
    except Exception as _ex:
        say("  (the try / savepoint record could not be written: %s)" % str(_ex)[:80])
    if rc != 0:
        for o in outs:
            try:
                if os.path.isfile(o) and os.path.getmtime(o) >= before - 1:
                    os.replace(o, o + ".FAILED"); say("  output  : %s written by the failed step - renamed .FAILED, not a result" % os.path.basename(o))
            except OSError:
                pass
    # not on disk
    if rc == 0:
        tdir = os.path.join(folder, "tags", tag); kept = []
        for o in outs:
            try:
                if os.path.isfile(o) and os.path.getmtime(o) >= before - 1 and os.path.getsize(o) <= 60 * 1024 * 1024:
                    os.makedirs(tdir, exist_ok=True); shutil.copy2(o, os.path.join(tdir, os.path.basename(o))); kept.append(os.path.basename(o))
            except OSError:
                pass
        if kept: say("  kept    : %s -> tags\\%s\\ (the tag's own copy; the job's live file is still %s)" % (", ".join(kept), tag, ", ".join(kept)))
    if step == "region" and rc == 0:
        rows = write_frozen(kit, folder, say)
        say("  frozen regions meeting the edit region: %s" % (", ".join("%s%s" % (r["name"], " (buried_ok)" if r["buried_ok"] else "") for r in rows) if rows else "none on record"))
        say("  PROTECT: the card's designed OPENINGS go to the region (--set PROTECT=...): the arrangement, the blend, the keep and STEP 4 read them from its record (31ai) - a box round an opening only, never round enclosed air (L111)")
    if rc == 0 and took >= 1 and os.path.isdir(os.path.join(kit.ROOT, "claude_code")):
        try:
            kit.cmd_clock(["add", row, "%.0f" % took, "--note", "kit rebuild %s" % step])
        except SystemExit:
            pass
        except Exception:
            pass
    tail = {"region": "read the WARNING lines (a grazing skin, a design face in a plane); OPEN EVERY FRAME of review\\region_cuts_*.png (the content alone, its section faces red = the cuts) and review\\region_fit_*.png, then `kit rebuild judge --what region` before the skin route",
            "arrange": "'STAGE A done' -> `kit rebuild arrange-m`; '... run again' -> the same line again",
            "arrange-m": "the `internal faces` line (31aj), the `as solid:` line (99-101 % of the content), THE BASE CENSUS and the `census cells` line; then `kit rebuild arrange-f`",
            "arrange-f": "`internal triangles dropped` and `inside check` (31aj); the FINAL mesh line must say solid True nonmanifold False selfint 0 (the base KEEP builds on); then `kit rebuild blend --set R=3`",
            "blend": "`the base's inside check` and `inside (3-axis winding vote)` (31aj), any `zone` lines; the RESULT line: health (0, 0) or small; then `kit rebuild repair`",
            "repair": "the FINAL mesh line must say solid True nonmanifold False selfint 0; then `kit rebuild review`",
            "review": "OPEN EVERY PICTURE in review\\ at full size; a defect stops the chain here; then THE CAPS FIRST: `kit rebuild reinsert --set STEP=1`, then `kit rebuild skin-regions` (31al)",
            "decimate": "the two-way deviation (p99 under 0.1 mm); then `kit rebuild fillholes`, then `kit rebuild finish`",
            "fillholes": "then `kit rebuild finish`",
            "finish": "the FINAL mesh line; then `kit rebuild brep`",
            "brep": "the `piece:` line: all valid True; more than one solid is normal (L89); then `kit rebuild keep`",
            "keep": "OPEN EVERY FRAME of keep\\keep_cuts_*.png (grey kept, orange rebuilt, green forced, RED the cuts); read the CUTS and FORCED KEPT lines; `kit rebuild judge --what keep`; then `kit rebuild reinsert --set STEP=1`",
            "reinsert": "STEP 1 (before the skin steps: wall_caps.brep) -> the skin route -> STEP 2 (JOIN=sew: the piece judged and, on a symmetric edit, mirror-checked; check(True) failing needs BOP_OK=\"<why>\", recorded) -> 3 -> 4: CHECK PASS or CHECK FAIL (the seam, PROTECT, shells). A TRIAL (--set TRIAL=\"<why>\" on STEP 2, 3 and 4) sews a piece not yet accepted - mirror-checked first - in as a LOOK: body_trial.brep, then review-body",
            "review-body": "OPEN EVERY PICTURE in review_body\\; a TRIAL's body: wrong - `kit rebuild judge --what trial --verdict redo|move --spot/--face` (what the REAL model shows); right - `kit rebuild second --what trial --assign` (two reviewers), then `kit rebuild judge --what trial --verdict ok` (THE ACCEPTANCE, 31aw); a real body: kit review / kit check / kit look / kit accept on body_new.brep",
            "skin-regions": "on a B-rep source (the normal case): the mesh record only, no pictures - then `kit rebuild skin-edges`; on a voxel: OPEN skin\\review\\SP1_* (the changed regions)",
            "skin-edges": "OPEN skin\\review\\edgemap\\1_*: the original's edges by class (crease, smooth, frozen, sliver) and the corners - then `kit rebuild skin-points`",
            "skin-points": "OPEN skin\\review\\SP7d_*: every dot on its original face (a face with NO dot is absorbed - PTS_BOX keeps it), MAGENTA = a reinsert-face edge whose face got no point - then `kit rebuild skin-labels --set \"MIRROR=<plane or empty>\"` (after the restart: `kit rebuild judge --what points` first)",
            "skin-labels": "the MIRRORED LAYOUT and FACE LADDER rung 1 lines; OPEN skin\\review\\SP8_*: the faces - then THE FEATURE MAP: `kit rebuild skin-features`",
            "skin-features": "OPEN FEAT_labels_* (each original face's id; 1121' = its mirror) and FEAT_features_* (the features, named); no FEATURES yet: name each face's FEATURE (\"A spine, A vane, a support\"), write {\"feature\": [ids]}, run again with --set FEATURES=<json> - then `kit rebuild skin-rim`",
            "skin-rim": "OPEN every frame LAYOUT_LOOK.json lists (LAYOUT_* from every side, SP12_* at the walls); `kit rebuild judge --what layout`; a symmetric edit: `kit rebuild skin-mirror --set WHAT=layout`; then `kit rebuild skin-network` (MIRROR comes from skin-labels' decision)",
            "skin-mirror": "the UNPAIRED lines (a face with no partner is a defect - fix the layout or the piece); MIRROR_<what>_*.png",
            "skin-network": "the junction / edge counts and any FAILED edge; OPEN skin\\review\\SP4_* - then `kit rebuild skin-frame`",
            "skin-frame": "every wall junction on a body vertex, no open face - then THE WIREFRAME: `kit rebuild skin-wires` (its WIRE_* number every chain, CORNERS_* every corner of the reinsert faces: decide LINES / RAILS from them, each with its reason)",
            "skin-wires": "OPEN every WIRE_* frame (WIRES_LOOK.json): each line where its feature's edge is, straight / one arc / one cubic, both sides alike; magenta = not one simple curve (its faces' points); `kit rebuild judge --what wires` - then `kit rebuild skin-build`. The original is the STARTING REFERENCE, not a constraint: redraw, move, split or add any line you decide - except at the frame, where every face ends exactly on the body's own walls (31bh)",
            "skin-build": "the FACE LADDER line (orig / flat / fit), SKIN BUILD PASS (closed, valid, the frame within FRAME_TOL) and the face count against the edit region's content; check(True) said - then `kit rebuild skin-look`",
            "skin-look": "QUICK look (the inner loop): open every frame - wrong: fix the LINE or the points the pictures point at, build, look again (no probe, no side render between); judge it - kit rebuild judge --what look --verdict ok|redo|move (every frame opened; the mirror check and the trial refuse without an ok - 31bx R6 F11); looks right (ok): see it in the REAL model - a symmetric edit `kit rebuild skin-mirror --set WHAT=piece` first, then a TRIAL (`kit rebuild reinsert --set STEP=2 --set TRIAL=\"<why>\"` -> 3 -> 4 -> review-body; two reviewers, then judge --what trial --verdict ok - THE ACCEPTANCE, 31aw) - or go formal. FORMAL, once: `kit rebuild skin-look --set LOOK_MODE=full` -> THE SECOND REVIEWER (`kit rebuild second --what skin --assign`, one cad-reviewer per shard, all at once; record each result; fix the largest defect first) -> OPEN EVERY FRAME yourself and `kit rebuild judge --what skin` -> skin-mirror WHAT=piece -> `kit rebuild reinsert --set STEP=2` (BOP_OK=\"<why>\" if check(True) failed)"}
    nxt = tail.get(step, "")
    if step == "skin-build" and rc == 0:
        try:
            _scj = json.load(open(os.path.join(folder, "skin", "solid_c.json"), encoding="utf-8")); _cfl = [c_ for c_ in (_scj.get("check_faces") or []) if isinstance(c_, dict) and c_.get("face") is not None]
        except (OSError, ValueError): _cfl = []
        if _cfl:
            _ids = sorted({int(c_["face"]) for c_ in _cfl}); _caps = sorted({int(c_["face"]) for c_ in _cfl if str(c_.get("kind")) == "cap"})
            nxt = ("check(True) FAILS on face(s) %s%s - THE CHECK FACES FIRST (31br L1, the client 2026-10-29: 'wouldn't it make sense to only render those spots as a check first?'): `kit rebuild skin-look --job %s --tag <T> --set FACES=%s`\n"
                   "            (their two iso views each, seconds) - open them: a real defect -> `kit rebuild judge --what look --verdict redo --frame <png> --face <n> --note ...` (no second review needed) and fix the lines / the points THERE, build again;\n"
            "            a tolerance-level flag or the body's own cap face -> say so in the note. The FULL look and the second review REFUSE until every flagged face has its targeted look (LOOK_FULL_OK=\"<why>\" overrides). Then: %s"
                   % (_ids, (" (cap faces %s are the body's own section faces)" % _caps) if _caps else "", job, ",".join(str(x_) for x_ in _ids), nxt))
    if step == "skin-mirror" and rc == 0:
        nxt = (("PASS - the piece is its own mirror. NEXT: see it in the REAL model, as a TRIAL (the client: \"Sometimes building the model and getting true renders is\n"
                "            the right answer\"): kit rebuild reinsert --job %s --tag <T> --set STEP=2 --set TRIAL=\"<why>\" -> STEP=3 -> STEP=4 (the same TRIAL) -> review-body.\n"
                "            Once the real model is right: kit rebuild second --what trial --assign (two reviewers) -> judge --what trial --verdict ok - THE ACCEPTANCE (31aw: nothing rebuilt)" % job)
               if str(env.get("WHAT", "")).lower() == "piece" else
               "PASS - every face has its mirror partner. NEXT: kit rebuild skin-network --job %s --tag <T>" % job)
    if step == "skin-features" and rc == 0 and str(env.get("FEATURES") or "").strip():      # no FEATURES
        nxt = "the FEATURE MAP applied (FEATURES=%s); OPEN FEAT_features_* (the features, named) - a face wrongly joined or split: fix the json and run again; then `kit rebuild skin-rim`" % env.get("FEATURES")
    if step == "skin-network" and str(env.get("NET_PICS", "")).strip() == "0":
        nxt = "the junction / edge counts and any FAILED edge (no pictures - NET_PICS=0) - then `kit rebuild skin-frame`"
    if step in ("skin-rim", "skin-wires") and rc == 0 and str(env.get("PICS", "quick")).strip().lower() != "full":
        nxt += " - THIS RUN DREW THE QUICK SET: an OK is judged on the FULL set, run once with --set PICS=full (a redo may be judged on the quick set; 31av)"
    if rc == 0: say("  next    : %s" % nxt)
    else: say("  next    : the step did not finish (rc %s) - fix what its REFUSED / FAIL line above names, then run it again" % rc)
    return rc

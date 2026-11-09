# EDIT TYPES — the catalogue. One directional card per type: what it is for, who runs it, the sequence, the numbers.
# `kit route "<the request in words>"` names the type and prints its sequence; `kit howto <type>` prints the card and
# copies its template into the job folder (--job, or run from inside one); `kit card <card.md>` prints that type's traps and only those. A feature that fits no type is
# split into features that do, or asked about. Workers never combine types in one script.
# (Rewritten 2026-09-24 as a catalogue: the history and evidence behind each card live in BURRITO_STEPS.md,
# VOXEL_SMOOTH_STEPS.md and KERNEL_LESSONS.md — a card says what to do, not what it cost.)

## GENERAL — printed with every card
- ONE job card (the numbers) and THIS card (the recipe). Nothing else is read; not the ledger, not the other cards.
- Copy the template, fill `PARAMS` only. A value missing from the card: write RESULT.md with the question and stop.
- Run only through `kit run`; render only through `kit render`; open every picture; one line each: HIT / MISS / POOR.
- LOOK BEFORE YOU MEASURE (31am, the client 2026-10-06): the guard refuses a measurement until a picture AT its subject was opened -
  name the subject (`# MEASURES: x0 x1 y0 y1 z0 z1 - <what>`), `kit tool look_at --job <J> --set "BOX=..."`, open it, then measure.
- The script builds the PIECE (banked as piece_*.brep) and fuses/cuts it into the REGION copy (result.brep). The
  orchestrator applies the piece to the model of record; a worker never touches the bank.
- Overlap: a piece that joins material goes >= 0.5 mm INTO it; a face that must not touch stands >= 2 mm clear.
  Never flush, never 0.1 mm off.
- Punch-through is forbidden; the card gives the far limit ("stops N mm short of ..."). PARAMS that would exceed it
  are not run - write RESULT.md.
- Expected faces per feature are small (each card says). Many more faces = wrong; report, do not apply.
- Every card carries `Row:` (the criteria row: a letter, an R<n> of the client's list, or `none - the client <date>: '<their
  words>'`), `Class:` (shape | seal), `Region:` (the atlas feature, in words), `Dossier:` (where the numbers came from,
  or `none - <why>`), `Top face:` (what the piece's top must BE). A slot that does not apply says so; a slot that is
  absent is refused by `kit card`, and `kit job` refuses a card that did not pass. Scaffold with `kit newcard`, never
  copy the last card. The phrase -> row map is the PROJECT'S (its PROJECT_FACTS.md), never this file's.
- Every sequence below starts with `kit newjob <JOB>` (the folder and the read-only region.brep), and its `kit check`
  and `kit accept` name the job's render review (`--review <dir>`); `kit atlas assign <JOB> --to <region>` comes before
  `kit apply`. The sequences name the steps; the flags are in `kit --help`.
  `kit run` runs the worker's script IN ITS OWN FOLDER (31bs K4): a template's relative output name lands in the job folder; an absolute one is unchanged.

## SYMPTOMS — characterise before you card (printed by `kit route`; the section decides shape vs seal)
SHAPE = the outside changes (an airflow surface, a transition, a step removed, a blend). SEAL = only the construction
changes (weld, fill under a lip, lamination, void, shard, punch-through). Shape first, seal LAST - `kit job` refuses a
seal card unless the client named it. Generic phrases: "punch through / watertight / seams / shards / one solid" ->
seal, last; "not smooth / fingernail / step" -> take the section first.

| the section shows | it is | class | type | NOT |
|---|---|---|---|---|
| a blade / fin / boss ending in a flat face in air above the surface it should meet ("stops dead", "shelf", "tab") | an unfinished transition | shape | `sketch_extrude` ADD of its own cross-section, continued until buried below; `sketch_connect` fan if the straight one reads too hard | `voxel_smooth` (it only ADDS); a weld under its edge |
| a shallow dent in a SOUND, thick, curved skin | a surface defect | shape | `sketch_connect` BEDSHEET off the skin's own profiles | a flat-topped extrusion at any tilt |
| a thin flap over air; two laminae; a 0.01 mm wall; four ray hits where there should be two | a construction defect in the skin | seal | WINDOW PANE (`sketch_extrude` cut + `sketch_connect` pane); the `burrito` when it "happens all over" | a bedsheet laid on the flap |
| a thin lip / notch / undercut with a wedge of air under it, outer surface fine | a construction defect | seal | fill (buried extrude) or the burrito's bridge | carding it against a shaping row |
| spikes, wedges, slivers on or through a surface; faces under 0.30 mm2; a needle wall | shards / punch-through | seal | the burrito's shave, or `sketch_extrude` cut of each | smoothing them as if they were shape |
| a step or shelf between two surfaces that should be one (reversal > 0.5 mm, a riser in section) | a shape defect | shape | `sketch_connect` between the two surfaces' own profiles | filling the corner with a box |
| a designed angle change, smooth on both sides, no riser | not a defect | - | nothing; say so with the section named | "sharpening" it |
| a narrow flat land where a strip must sit (a rim) | a dimension | shape | `sketch_extrude` ADD inboard, section before/after | a whole-rim campaign |
| a whole feature that should not be there: a plate, a shelf, a web, a boss, a stub | material to remove | shape | `cutter` - measure the part, DRAW the tool, cut once | a cutter built from the feature's own faces |
| a concave junction / crack between two sheets that wants a fillet, on a part whose deliverable is a MESH | rough construction | seal | `voxel_smooth` (ADD only) | any step, ridge, tab or shard (removals) |
| a gap between two of the body's own surfaces that should be material | air to fill | seal | `gapfill` - the slab's free walls ARE the fill's faces | extruding one face toward the other |
| a hollow skin found by rays (four hits) where nobody flagged it | a construction defect, new finding | seal | report it, row J | fixing it inside a shaping job |
| a DRAWN feature to add - a rail, a slab, a boss, a pad, a drawn notch fill - on a part whose deliverable is a MESH | a designed addition | shape | `mesh_union` (`kit crop` -> `kit union` -> `kit splice`) | `voxel_smooth` with `CC_UNION_STL` (~15 min a piece, a million triangles for four flat faces) |

## sketch_extrude — a closed flat outline on a plane, given depth (add or cut)
When: blocks, pads, walls, ribs, pockets, recesses, slots, rectangular/rounded holes, the box body itself.
Route: block pad wall rib pocket recess slot fill extrude boss round-boss cylindrical plate land
Tier: haiku - two first-try cards (J01A piece, J01B tilted-plane cut).
Sequence: kit atlas find -> dossier (section at the plane, the far limit) -> kit newcard -> kit card -> kit job ->
  run (worker or you) -> kit review (after frames on the box) -> kit check -> kit look -> kit accept -> kit apply.
Recipe: outline = rectangle / rounded rectangle (radius drawn in) / circle / polygon-with-arcs, in the plane's own 2-D
  coordinates; plane = one of the six axis planes at an offset, or a named body face; extrude `depth` along the normal
  (sign = direction); ADD -> fuse, CUT -> cut. Start 0.5 mm inside material for a fuse; 2 mm out in air for a cut.
DO: keep corner radii in the outline; state depth as a number from the card; one outline per script.
DO NOT: extrude to "the next face" by guessing; cut past the far limit; fillet afterwards; fill or patch a CURVED skin
  with this type - a flat top stands proud on one side and leaves a step on the other (fingernail test, 0.15 mm catches):
  that is `sketch_connect`, the BEDSHEET.
Expect faces: box +5, rounded rectangle +9, circle +2..3, polygon +N+1.
Template: t_sketch_extrude.py

## sketch_connect — two closed outlines on two planes joined by straight sides (wedge, taper, angled face, bedsheet, pane)
When: an angled face, a taper from one section to another, a transition block, a trapezoidal loop body, a chamfer-like
  transition; a patch ON a curved skin (the BEDSHEET); the pane that closes a cut window IN a curved skin (WINDOW PANE).
Route: angled taper wedge transition bedsheet pane patch skin dent smooth-between two-surfaces chamfer
Tier: haiku - J04 rounded pocket with a tilted ceiling, first try.
Sequence: as sketch_extrude; the profiles come from the kit (`kit measure ... section --profile --dossier`), never from a
  picture.
Recipe: outline A on plane A, outline B on plane B (same vertex count, same order); each pair of corresponding edges is
  one ruled face; the outlines cap it. ADD -> fuse, CUT -> cut. Planes may be parallel or not; they must not cross
  inside the piece.
THE BEDSHEET (a shallow dent in a SOUND, thick skin): section the sound skin at the two ends of the defect; draw each
  profile as a polyline lying ON the skin (chords with sagitta under 0.10), closed 0.5 mm down into sound material;
  connect them. The top is the skin by construction. If the skin's curvature ACROSS the patch exceeds a 0.10 sagitta
  over the span, split into two connects. Pass: one continuous outline in a section across the patch; nothing past 5 deg
  at the boundaries; zero faces under 0.30 mm2.
THE WINDOW PANE (a defect IN a curved skin - pit, shard fan, flap over a void, lamination): (1) bound the defect in plan,
  2 mm of SOUND skin beyond it on every side (`section --box` finds the extent); (2) CUT the window: `sketch_extrude`
  op=cut, rect outline on a plane above the skin, through everything flawed, stopping 2 mm clear of sound material
  below (the far limit, measured); (3) PROFILES from the kit on the UNCUT body at y0 and y1 (`kit measure <brep> section
  y <y0> --box ... --profile --step 1`), material intervals top-down, the first is (outer, inner); (4) PANE: outline A on
  the plane y=y0 (normal +y, udir +x): the OUTER line x0->x1, down the x1 wall, the INNER line back (the printed inner
  points where the skin was sound, a drawn line at the neighbours' thickness across the flaw), up the x0 wall; outline
  B at y1 likewise, same count and order; connect. The pane's caps ARE the cut's y-faces and its ends ARE the cut's
  x-walls: coplanar planar joins. (5) skin curving along y by more than a 0.10 sagitta: three stations, two panes.
  Pass: continuous outline in a section across each cut plane; nothing past 5 deg at the four boundaries; zero faces
  under 0.30 mm2 in the box; `kit check` in the box.
DO: same vertex count and order on both outlines (the template checks); keep both outlines convex or nearly so.
DO NOT: more than two outlines (a loft - forbidden); twist B relative to A; card "a polygon with ONE arc" -
  `corner_radius` rounds EVERY corner of BOTH outlines with ONE radius; draw an arc as N chords whose sagitta
  r(1-cos(a/2N)) is under 0.30 and state N on the card.
Expect faces: N sides + 2 (rounded: 2N + 2).
Template: t_sketch_connect.py

## hole — a round bore, optional counterbore/countersink, from a named face to a depth (cut)
When: insert bores, through-bolts, clearance holes, countersunk screws.
Route: hole bore drill insert counterbore countersink through-bolt clearance
Tier: haiku - T01 with a `kit facts insert` lookup, first try.
Sequence: as sketch_extrude; the insert size comes from `kit facts insert` (the project's own numbers, never this file).
Recipe: cylinder(s) along the stated axis starting 2 mm above the face, to the stated depth (or 2 mm past the far face
  for a through hole); counterbore = second, larger cylinder to its own depth; CUT.
DO: check the card's wall-to-edge number and report it back. A TILTED bore needs a lead-in of 2 + r x tan(tilt) on each
  side - the card gives it.
DO NOT: tap threads; bore where the card gives no boss/thickness; exceed the far limit.
Expect faces: +1 (through) .. +3 (blind with counterbore).
Template: t_hole.py

## gapfill — the air between neighbouring surfaces becomes material, touching every neighbour BY CONSTRUCTION
When: a slit or channel between two parts of one body (skirt to part, web to wall); a flush floor between a ledge and
  a wall; a web brought down to a neighbour; any "fill this gap" where the neighbours' own surfaces bound the fill.
Route: gap fill channel slit web-to-wall flush-floor bring-down close-the-gap
Tier: haiku from a filled card; the ORCHESTRATOR writes the slab and the probe point from sections (>= 3 stations).
Sequence: kit atlas find -> dossier (3+ sections across the gap) -> kit newcard (slab walls on the NEIGHBOUR's
  surfaces; the probe point in the gap) -> kit card -> kit job -> run -> kit review -> kit check -> kit look ->
  kit accept -> kit apply.
Recipe: a SLAB box over the gap reaching INTO every wall the fill must touch (>= 0.5 mm) and whose free walls sit exactly
  where the fill should end; the AIR in the slab = `slab.cut(body)`; the fill = the air piece containing the PROBE
  point; `body.fuse(fill)`. The fill's faces are the body's own where they meet.
DO: read the gap in sections at >= 3 stations (neighbours flare, step and lean); put the slab's free walls on the
  NEIGHBOUR's surface, never at a chosen z; name a frozen region inside the slab on `Region:` (recreated at the end of
  edits); count the air pieces and their volumes before fusing.
DO NOT: pick the piece by bounding box (a B-spline body's boxes lie); extrude a face along its normal to reach a
  neighbour; fill a channel that carries airflow without the client's word.
Expect: faces = body minus the buried ones plus the slab's free faces; volume within 1-3 % of the fill's own
  (20 % off = a wrong piece).
Template: t_gapfill.py

## cutter — remove a whole feature by DRAWING an independent tool from a measured, faired table (cut)
When: a feature that should not be there at all - a thin plate on a vane, a shelf, a web, a boss, a stub. Not for
  smoothing (burrito), not for a pocket with drawn walls (sketch_extrude cut), not for filling air (gapfill).
Route: remove delete cut-off shelf stub boss-remove web-remove plate-remove take-off get-rid
Tier: opus worker (`cad-worker-opus`) from a filled card - C2, C4 and C5 are judgement calls on pictures.
Sequence: kit atlas find -> `kit measure faces --normal ... --tol-deg` (the angles go on the card) -> dossier
  (stations) -> kit newcard -> kit card -> kit job -> run (the template runs C0-C10 in order and refuses to skip) ->
  GATE A (cutter alone + in place, 2 frames, verdict) -> cut -> GATE B (result alone + what was removed, 2 frames,
  verdict) -> kit check (a removal that leaves no material where the feature stood is an opening to kit check: --breakout ok, the card saying the
  feature goes) -> kit look -> kit accept -> kit apply.
Recipe: C0 why a cut and not a deletion (one line, boilerplate refused) · C1 find the feature's faces BY NORMAL
  (never by index - numbering differs between FCStd, brep and revision) · C2 classify by orientation (a face pointing
  INTO material has air behind it and cannot carry a floor) · C3 measure a table from the TESSELLATED faces (never
  `BoundBox`) · C4 symmetrise -> smooth -> OFFSET, never clamp · C5 declare where the cut ENDS, from the part
  (`boundary: "face_edge"` is refused) · C6 one cutter solid from ruled segments between drawn stations · GATE A · C7 cut
  once · C8 clean leftovers with boxes (each a listed sketch_extrude cut) · C9 verify · GATE B · C10 RESULT.
Verification (one block): removed volume vs `expect.volume_mm3` (required); thin-wall column count before/after;
  the boundary station by station (stub / knife edge / island); solids and slivers; surface area (a cut that ends with
  MORE area is wrong); conservation residual kept + removed - source; re-validate (count solids and volume first -
  `isValid()` is True on an empty shape).
DO NOT: build the cutter from `face.OuterWire` / a face extrusion / `makeOffsetShape` on the feature (the guard refuses
  it in a script that cuts and saves); measure with `BoundBox`; clamp the faired table; carry numbers from one cut to
  the next; change more than one lever per retry; overlay the gate frames.
On failure the template writes RESULT.md and stops with a RETRY BLOCK (lever, direction, failed check). Stopping is a
  valid outcome; dropping scope is not.
Expect faces: a few per station segment plus the caps - tens, not thousands. kit check's face figure (the card's `faces about +N`) counts the FLOOR's strip faces -
  one per station interval (a 6 mm boss removed at step 0.5: +41 against its own -2 - the result is kept uncleaned when the whole-body cleanup would change a face far from the cut, 31ca R2 F1) - never the feature's own face change (31bz R2 D1).
Template: t_cutter.py (kit run allows its own removeSplitter - the seams of its OWN swept tool - in an unmodified copy, nowhere else; 31bs K25)

## mirror_pattern — copy an existing banked piece across a plane or along a spacing, then fuse/cut all copies
When: bolt patterns, symmetric bosses, the two loops, both sides of anything.
Route: mirror pattern both-sides symmetric array repeat other-side
Tier: haiku - T02 three mirrored bores, first try.
Sequence: as sketch_extrude, on a piece already banked.
Recipe: load piece_*.brep, mirror across x = 0 and / or y = 0 (mirror_x / mirror_y - the template's two mirrors; no z mirror, no offset plane: place the piece so the plane is x = 0 or
  y = 0 first, or build the copy at its place) and / or translate by the spacing N times; apply all copies in ONE fuse/cut. kit check on a pattern whose copies' box is over 25x the
  change: `--wide-box "<why>"` (31bx R2 D6 / D7).
DO NOT: rebuild the piece from numbers (the copy is the banked solid); mirror onto a body that is not symmetric there -
  section the far side first.
Expect faces: copies x piece faces. Expect solids: an added copy that touches nothing stays its own solid - the result a compound of the base's solids plus the free copies
  (31bw B4; a pattern of 36 receptacles had collapsed to one) - the card's Expected line states `solids N` (the base's + the free copies), which kit check judges; a cut on a
  compound base keeps every solid of it.
Template: t_mirror_pattern.py

## split — divide the body at a plane into two parts and bank both (base / cover)
When: the base/cover split; any two-part print.
Route: split cover base two-part parting-plane halves
Sequence: as sketch_extrude (card -> kit job -> kit run -> kit review -> kit check -> kit look -> kit accept -> kit apply), both halves banked. kit check on a split: a split OPENS the body by design -
  `--breakout ok "a split"` - and its box is the whole body - `--wide-box "a split"` (31bx R2 D5 / D7).
Tier: haiku - J02, first try.
Recipe: `common` with a half-space box on each side of the plane; bank part_A.brep and part_B.brep. Lips/rebates are
  separate sketch_extrude features afterwards.
Expect: two solids, each valid; the volumes add up to the original (a compound base: every solid on each side kept - 31bw B4; a one-solid base keeps the largest per side).
Template: t_split.py

## edge_round — a round on the edges of a PRIMITIVE piece before it is fused (never on the assembled body)
When: a softened outer box edge, a rounded loop. Only on a fresh box/cylinder/prism piece with <= 12 faces.
Route: round-edge edge-round round-off edge fillet-piece soften corner-round rounded
Sequence: as sketch_extrude, on a PRIMITIVE piece before it is fused (never on the assembled body).
Tier: haiku - T05 four vertical edges r3 on a box piece, first try.
Recipe: `makeFillet(r, edges)` on the piece, checked valid; if it fails once, the round goes into the sketch outline
  instead (rounded rectangle) and this card is not used for that edge. kit check on a round: the change is small against its box (a round on a circular edge: 392x) -
  `--wide-box "a round on the piece's edge"`; the rounded piece (piece_rounded.brep) then goes into the body like any piece: `kit apply <bank> <piece_rounded.brep> fuse <next bank> --job <J>` (31bx R1 D7).
DO NOT: fillet a body after any fuse/cut; chain fillets.
Expect faces: + edges filleted.
Template: t_edge_round.py

## revolve — a closed outline revolved about an axis (round bosses with steps, ring lips, round loop cross-sections)
When: a stepped round boss, a lip ring, a bar-loop with round section.
Route: revolve ring lip stepped-boss turned lathe
Sequence: as sketch_extrude; the profile from the kit's own sections (`kit measure ... section --profile --dossier`).
Tier: haiku, provisional - no test card has run; the first run is the test (record it).
Recipe: outline (u, v) in a plane containing the axis - u along the plane's udir, v along normal x udir (kitlib.plane; v is the direction the outline rises in - 31bx R1 D8) - revolved 360
  (or the card's angle); ADD/CUT.
DO NOT: revolve an outline that crosses the axis.
Expect faces: outline edges count.
Template: t_revolve.py

## shell — hollow a plain box-like solid from one open face with a wall thickness
When: turning the blank outer body into the box (open at the split plane) - once, early, on a simple solid only.
Route: shell hollow wall-thickness open-face
Sequence: as sketch_extrude; the wall thickness and the open face measured first (dossier).
Tier: haiku, provisional - no test card has run; the first run is the test (record it).
Recipe: `makeThickness` on the solid with the open face(s) named by direction, thickness inward. Stop if the solid has
  more than ~12 faces (then the interior is a `sketch_extrude` cut).
DO NOT: shell a body that already has holes, bosses or an angled face.
Expect faces: about double.
Template: t_shell.py

## move — a finished part moved and TURNED to a new position (no shape change)
When: the whole part has to sit somewhere else - moved, or turned about an axis and moved (a board exported in its own frame placed into the
  fixture's frame: the client 2026-10-30, 31br B5). Position only.
Route: move translate reposition relocate rotate turn place placement orient pose align frame
Sequence: as sketch_extrude (card -> job -> run -> review -> check -> look -> accept -> apply); a placement alone is `kit place` (recorded in PLACEMENTS.json), no job. kit check on a move:
  the part's old footprint is vacated by design - `--breakout ok "the move vacates its footprint"` (31bx R1 F7).
Tier: haiku.
Recipe: `t_move` takes the part, a dx/dy/dz and - 31br B5 - an optional turn: rot_axis (ax, ay, az), rot_deg, rot_about (the point the axis passes through;
  the part's origin by default); the turn comes FIRST, then the move (FreeCAD's Placement order). The bookkeeping line prints the old and the new bounding
  box; the volume must not change by a single cubic millimetre - if it does, something other than a move happened. OUTSIDE A JOB - a bank body or an
  export to place once, recorded: `kit place <in.brep|in.stl> --out <out> [--translate dx dy dz] [--rotate "ax ay az deg"] [--about px py pz] --why "<the
  frame>"` writes the placed copy (a brep carries the placement as its LOCATION - what FreeCAD reads back as the object's Placement; an .stl is baked) and
  records it in `claude_code\PLACEMENTS.json`, the project's frame map; the same placement rides a delivery spec (`kit deliver --add-body
  "...|place=dx,dy,dz,ax,ay,az,deg"`, `--mesh "...|place=..."`), and a `--target` swap keeps the template body's own Placement. The kit has NO other turn:
  mirror_pattern's two mirrors compose to a 180 deg turn about z at most; nothing in the mesh steps or the atlas moves geometry.
Template: t_move.py

## region_look — no edit: render a region for the orchestrator (before/after, appearance)
Route: look render show show-me picture view corner appearance
Sequence: kit newjob <J> -> kit newcard <J> --type region_look --write jobs\<J>\CARD.md -> kit card -> kit job <J> --type region_look --card <the card> (registers the look so `kit look <J>`
  records it - 31bx R2 F9) -> kit render <brep> --out jobs\<J>\look --box <the card's box> --job <J> -> open every frame -> kit look <J> --code <frame>=<CODE> ... --says "..." ->
  kit cancel <J> --why "a look, not an edit" (no run, no check, no apply).
Tier: haiku.
Recipe: `kit render` on the given brep with the card's views; one line per picture.
Template: (none)

## burrito — everything inside a window is re-decided from the body's own surfaces, blended, and put back as a B-rep (the rebuild chain; rewritten 2026-09-28)
When: ANY feature whose construction is wrong and whose shape is not dimensionally critical - punch-through along a
  rib seam, laminated skin, shards, needle walls, spikes, overlaps that never fused, gaps that should be material (a sliver of air the surfaces span across once the small faces round it are absorbed -
  NOT a slot between two features: that is a gapfill job after the burrito, FAILURES 2026-10-29 17:01; 31bx R6 D3), a
  corner - one feature or a whole section. Deliverable: the body of record with the window's content replaced
  (`body_new.brep`), one valid solid. The client's words: "start with a messy/sloppy/hole filled/sharp edged/etc brep
  and end with a cleaned version of that, that ... fits back into model perfectly" - what it must PRODUCE is the list at
  the head of BURRITO_STEPS.md (the client's requirements, listed 2026-10-05): B-rep in and out; the junk gone (gaps, enclosed
  pockets, spikes - removed by the rebuild itself); simple and smooth; very few faces (at or under the original section's -
  the finishing pass); seams <= 0.15; designed openings open; frozen regions recreated; symmetric where designed; printable;
  judged by pictures; CAD-generic.
Route: burrito smooth generically rebuild section reexpress clean-up rib-seam laminated re-draw spikes gaps arrangement blend
Tier: ORCHESTRATOR - no worker. The chain's scripts are in `LEAN_KIT\kit\rebuild\` (the skin route's sk_*.py; rb_*.py for region / reinsert / review-body and the shelved voxel field), run from the kit one step at a time
  through `kit rebuild <step> --job <J> --tag <T> [--set KEY=VALUE ...]` (one freecadcmd process each, the clock, the env
  record, the inputs taken from the job and printed as `default`; a CARD lever not set is refused; `--plan` shows a run).
Sequence (31al, 2026-10-06 - THE SKIN ROUTE; the client: "There is a new burrito process and it works. The old process gets ~1/2 shelved"):
  kit atlas find -> kit frozen check -> kit newjob / newcard --type burrito / job (the card) -> kit atlas assign <job> --to <region>
  -> rebuild region --set PROTECT= (read its GRAZING / DESIGN-FACE warnings) -> OPEN EVERY FRAME of review\region_cuts_*.png (the content alone, its
  section faces red = the cuts; 31bn fix 5g) and region_fit_*.png (in the body) and `kit rebuild judge --what region`
  **(31ba, the client 2026-10-08: "the entire voxel step is now getting skipped. shelve it" - THE VOXEL FIELD arrange / arrange-m / arrange-f / blend / repair / review IS SHELVED, refused without SHELVED_OK; 31bq B48: it is no longer in this sequence) - after the region
  step: `kit rebuild skin-source` (content.brep -> source.stl + the original face of every triangle, the skin steps' STL, made once); the layout is the
  B-rep's own faces (31bb: borders = B-rep edges, junctions = B-rep vertices), what is KEPT is the pick (skin-points) and the wireframe's; the geometry is
  corrected in the WIREFRAME.**
  -> THE REINSERT FACES FIRST: rebuild reinsert --set STEP=1 (wall_caps.brep - the client: "Step 1 is get the perfect reinsert faces")
  -> THE SKIN: skin-regions -> skin-edges -> skin-points (OPEN SP7d_*: the original's wireframe on the source mesh, every point on its face;
  PTS_BOX / PTS_DROP / FRAME_PTS pick them; 31bq: every box with its reason - `x0 x1 y0 y1 z0 z1 [spacing] | why`, refused without) -> skin-labels --set "MIRROR=x 0" (the card's symmetry decision; empty = not symmetric; a
  symmetric layout is made on one side and mirrored; the face ladder's rung 1) -> skin-features (THE FEATURE MAP, 31as: open FEAT_labels_*,
  name each original face's feature - "A spine, A vane, a support" - and run it again with --set FEATURES=<json> (31bq: with `"_why": {feature: reason}` for every feature, refused without); skin-rim refuses without it) -> skin-rim -> OPEN EVERY FRAME (LAYOUT_LOOK.json: LAYOUT_*
  from every side, SP12_*) and `kit rebuild judge --what layout` (31av: an ok on the FULL set - PICS=full once, the loop runs PICS quick; the FIRST ok
  LOCKS the layout's section-wide levers - after it a face changes through its points, its lines through LINES / RAILS; five layout redos (ROUNDS_MAX) without a
  skin-build that passes send every place they named back to the points) -> a symmetric edit: skin-mirror --set WHAT=layout -> skin-network
  (refused without the layout judged and mirror-checked) -> skin-frame -> skin-wires. **31aw: `kit rebuild skin-layout` = skin-rim + skin-mirror WHAT=layout and
  `kit rebuild skin-lines` = skin-network + skin-frame + skin-wires (the client: "2 commands, 3 picture sets"); a frame drawn from the same inputs before is a HIT, not
  drawn again; in the LINES json "_add": GUIDE lines inside a face (its surface passes through them - depth / curvature) and SPLIT lines (the face made two -
  the fallback, and a face that wraps), "_fillets" (the kernel rounds the line after the solid; A FILLET NEEDS ROOM (31bl): t = R tan(beta/2) + the print tolerance of face beside the crease on each side, else make room - move the border / fill the gap - or lower R; the kit measures and says it at the wires and at the build, never chooses; the kernel first, the lines blend behind it - which TAPERS to the junction where its offset line meets no border (31bm; no cap, no cut); the crease measured AS BUILT, a tangent border refused as no crease; a failure said; the client 2026-10-13: no mesh route for blends); a split is a wire,
  never a re-split of the layout.** skin-wires (THE WIREFRAME, 31as: from its WIRE_* (every chain
  numbered) and CORNERS_* (every corner of the reinsert faces, c<n>) decide LINES - each chain straight, one arc or one cubic, with its reason - and
  RAILS - straight feature edges between corners - and run it again; 31av: LINES' numbers are the last WIRE_* pictures' - after a re-split skin-wires
  CARRIES the decisions to the new numbers, skin\LINES_carried.json, and lists only the new lines TO DECIDE) -> OPEN EVERY WIRE_* frame and `kit rebuild judge --what wires` -> skin-build (THE FACE LADDER, 31aw - THE FACE THROUGH ITS EDGES: original surface -> a plane -> the Coons patch of the face's four sides (the
  border exact) -> a PLATE through its edges when the patch folds -> refused when it wraps: split it with a wire; nothing of the voxel in a surface; every face loop cleaned at the 0.02 mm construction tolerance before the face is built (31bq R7W wire-clean pass: a gap joined, a short edge dropped,
  a graze cut back - said per move; L153);
  SKIN BUILD PASS: closed, valid, the frame within FRAME_TOL; the faces failing check(True) named (a corner inside a side = a C0 line, sound for the sew);
  the build's whole state saved - `kit rebuild restore --tag <T>` puts it back WITH its look records and their frames (31br A2; a REDO of a restored layout / piece is judged on an opened picture; `skin-rim --supersede "<the client's words>"` re-makes a judged layout on their word); the design file's best copy) -> skin-look,
  QUICK (8 frames: wrong -> fix the line or the points it shows and build again - no probe or side render between) - **31bn: every piece picture
  (skin-look, look_at, the mirror) is THE PIECE VIEW: one conforming mesh of the whole piece (PIC_DEV 0.02 / PIC_ANG 0.05), opaque, a tint per face, lines
  depth-tested, the mesh judged against its surfaces before it is drawn; a frame with a red RENDER DEFECTIVE band is NO EVIDENCE - the judge and the look gate
  refuse it; make the mesh right and draw again**
  -> right: the REAL model as a TRIAL (31ar, the client: "Sometimes building the model and getting true renders is the right answer"): a symmetric
  edit skin-mirror --set WHAT=piece FIRST (the client: "mirror checks should pass before creating a real model"), then rebuild reinsert --set STEP=2
  / 3 / 4 --set TRIAL="<why>" -> review-body (it reviews body_trial.brep) -> `kit rebuild judge --what trial --verdict redo|move --spot|--face`
  (a trial FILE for the client only when the client asks - `kit deliver <REV> --trial "<the client's words>"`, 31av) - **31az: the quick look is JUDGED first (`kit rebuild judge
  --what look`, every frame opened; redo names the place) - skin-mirror WHAT=piece and the trial refuse without it; the face ladder is NURBS FIRST (the
  plate fill through the wires, rim 0.10; Coons / plate only when the fill cannot hold its rim); the WIRE_* frames hide hidden lines; a traced line follows
  the ORIGINAL (31bb: kept geometry)** -> **31aw: THE TRIAL IS THE ACCEPTANCE** (the client: "If a
  trial passes, do not rebuild it, do not reinsert it. Yes to orbit, 2 reviewers"): `kit rebuild second --what trial --assign` -> TWO cad-reviewers over
  review-body's frames of the real model (the orbit, the close-ups, the old-vs-new stations), each result recorded (`--shard k --result <file>`) ->
  OPEN EVERY FRAME yourself (the stations: GREEN = both bodies, YELLOW = old only, BLUE = new only - 31bp fix 7b) -> `kit rebuild judge --what trial --verdict ok` (over the reviewers' blockers only with the client's recorded `--ruling` and a `--note` disposing of each; L134) -> PROMOTED: body_trial.brep IS body_new.brep, the piece judged ok,
  review_body\ a COMPLETE review; a skin-build or a STEP 2 of that piece is refused after it -> kit review (before/after, one camera) -> kit check
  --wide-box "the edit region is the change" -> the card's After render -> kit look -> kit accept -> kit apply --job <job> (31bq R7W route-end D3: the burrito's accepted body_new.brep copied into the bank under the next REV and promoted - kit accept first; a second apply and a promote of a jobs\ file are refused) / kit deliver on the client's word. (The
  72-frame full look, `second --what skin` and the real STEP 2-4 are no longer on the path; they still run for a piece judged without a trial.) SHELVED (refused without --set SHELVED_OK="<why>"): decimate, fillholes, finish, brep, keep, JOIN=fuse.
  Going back into a done edit: before apply, re-run any step on the job's files; after apply, a new job over the same place against
  the new model of record (BURRITO_STEPS, THE SKIN ROUTE). THE RESTART, PER SPOT (31an, the client 2026-10-07): a move/redo names every place that
  failed (`--face <n>` / `--spot <box>`); three consecutive failed tries at one place lock it, and skin-points then keeps every other point
  and picks again only there; `kit rebuild judge --what points` unlocks it (L120). No lever ladders for a failing area - the points and the
  face ladder fix it (the client: "Let the process fix it"). Every run and judgement is a row of <job>\BUILD_LOG.md (paste them into the report).
The CARD levers: `WIN`, `PLANES` (walls in air or thick clean material, never grazing a skin - the region step REFUSES a
  grazing wall, `GRAZE_OK="<why>"` overrides - never in a design face), `R` (3), `PROTECT` (a box round each DESIGNED
  OPENING R must not fill - what counts as a designed opening is the PROJECT'S ruling (PROJECT_FACTS section 6, its NEWEST line; 31br D13) - holding the opening's air ONLY:
  enclosed air is junk and is filled (the client 2026-10-05; L111); a fresh job sets it on the REGION step (31ai: the region's record; arrange / arrange-m / blend are shelved - 31bq B48),
  reinsert reads it from there and STEP 4 measures the boxes' material),
  `REDUCTION` (0.99), `--tag`, `KEEP` (1 = keep-and-weld: the base's own triangles kept exact outside the junction cores,
  the marching-cubes surface only inside them, joined by the MERGE with its micro-holes left open for the repair - L104;
  it needs the ARRANGEMENT's base, never the content's raw tessellation - L105; with it OPEN 0, KEEP_JOIN merge, KEEP_TOL
  0.8, KEEP_MICRO open, KEEP_OPEN_OK 60 - the proven set, runs 14-15, set on every blend line until the kit pass makes them
  the defaults); with a reason on the card: `ZONES` (31aj: the defect each zone targets, from the piece review's pictures - the client 2026-10-05:
  "targeting smoothing operations in those areas"), `GAP_V` / `SPIKE_V` (a section: 1 / 0 since run 16 - the manifold fix closes the corner), `KEEP_CELL` (3; 2 failed STEP 2
  by a degenerate shell on a section), `KEEP_OFFSET` (the grid moved by hand after the orbit of the cuts), `BOP_OK`, `FROZEN_TOL` (0.15; a NON-CRITICAL frozen region - the vanes - is
  recreated within the 0.30 print tolerance: 0.31 on a section, requirement 7; the delivery gate `kit atlas recreated`
  still holds 0.15 until the kit pass). `SEAM_MAX` is 0.15 mm - the client's ceiling (2026-09-21), lowered
  only. Every other lever VALUE is a suggestion (the client 2026-10-07: "default settings should be suggestions only, not requirements") - the
  agent picks by the pictures and the runner records it; only LEVER_RANGE refuses (L124). The method's STEPS are fixed - never changed
  mid-round (the client, 2026-09-30: strongly recommended not to change the method; log the failures).
DO NOT: put a wall through the feature being fixed or along a skin (the region step refuses a grazing wall); run any step
  on a body-sized input (the window is the unit; the reinsert never fuses on the body - box + the ring sew); lay a piece's
  skin on the body's skin (the band of 2026-09-28 - L99: the piece meets the body on exact planes only); offer a piece
  that fails check(True) to any boolean (L100); loosen SEAM_MAX, KEEP_TOL or PROTECT_TOL to pass a gate - a seam over
  0.15 mm or a changed PROTECT box is the PIECE's defect (a resample's rounding - L104; the blend's OPEN / PROTECT fade / a wall) and is fixed there;
  use fixSelfIntersections on the mesh (L86); accept a STEP 4 CHECK FAIL or a review whose pictures you have not opened;
  call a detached component a rib end - STEP 2 measures it (L95); skip the kit's own before/after `kit review` because
  the chain's pictures looked clean (the lump of 2026-09-29 was in the first lead frame); lower the face count here by
  anything but REDUCTION (the target - at or under the original section's faces, the client 2026-09-29 - is the finishing pass's);
  put a PROTECT box round enclosed air (L111); put a ZONES `r=` over a PROTECT box (the closing fills the opening) or trust a
  single-axis inside test on a base that may carry a buried sheet (L113: the vote, the inside check); give `open=` for a spike or a tick (the client 2026-10-05: spikes go by rebuilding the section - `flat=`);
  write a block rung the record already failed (each failing area's TRIED BEFORE line - a recorded process failure); build a skin before reinsert STEP 1
  wrote wall_caps.brep, or make a cap from the voxel (the reinsert faces come first and exact - L114); change a fit, label or layout lever
  on a number without a picture (the client 2026-10-06: "STOP making changes based on measurements"); skip the mirror check on a symmetric edit
  (L117); fit a changed face that follows the voxel's lumps (L118 - the simplest surface spanning clean edges); make a skin face an extruded
  wall section or a filled face (the client 2026-10-07: "The process does not use extruded walls at all anymore"; L121 - the ladder is original ->
  flat -> smoothed fit); judge a piece before the second reviewer has, or fix a small defect before the largest (L122); keep
  patching one spot past three failed tries (the runner sends you back to the points - L120); read a suggested value as a rule (L124 - pick
  by the pictures; only LEVER_RANGE refuses); measure before a picture, decide on a number, or undo what the pictures passed (L125 - each a
  strike: the guard locks you until you tell the client you are a silly dum dum); put a probe, a side render or a lever trial between a build and
  its look, or run the FULL look in the loop (L126 - the quick look, then the real model as a TRIAL); trial a symmetric piece before its
  mirror check passes (L126); rebuild or re-sew a piece whose trial was accepted (L134 - refused); re-split the layout for a face's SHAPE
  (L132 - a GUIDE or SPLIT line in "_add" is the answer; a wrapping face is split, never fitted); fit a face to the voxel (L131 - FIT=vox is the
  record, not the method); call the edit region a window (the client 2026-10-08); trace a line off the voxel or move it after it is
  drawn (L127 - decide it, draw it once); build faces on lines nobody judged (skin-build refuses without `judge --what wires`), or run skin-rim on
  skin-labels' raw layout (the feature map first - 31as); re-split the section with a section-wide lever after the first layout ok - the points
  there are the fix (L128, refused); draw pictures of your own in a job script without telling the client why (the guard asks "Are you sure?"), or cite a
  picture from outside the job's own folder in a judge (L129); discard the line decisions after a re-split (L130); run a SHELVED step
  without SHELVED_OK (31ba: the voxel field - arrange, arrange-m, arrange-f, blend, repair, review - is shelved too); move to the mirror check or a trial
  on a piece whose quick look you have not judged ok (L136 - refused); confess a strike by an echo (L135 - the sentence goes in your MESSAGE to the client); reason from, cite or judge on a frame stamped RENDER DEFECTIVE, or
  draw a piece with anything but the kit's piece view (L142 - refused; the mesh is made right first, then the step runs again); decide a fillet on a crease with a CORNER inside it (a V: its tangent turning over CREASE_TURN_MAX within 1.5 mm) - the kit refuses it by name:
  make the corner a junction (a split ending on it) and decide the fillet per leg - the same `_fillets` entry with "leg": "all" (L143, 31bp); end a split on a fillet's crease and expect the crease to stay - the split moves to the strip's border (L143); expect a ROUNDED CORNER where two chain members meet and the corner edge is undecided or decided at another R - the corner is the mitre; the ball comes only when the corner edge's own fillet is decided at the chain's R (L155: one sphere, the sweeps stop at its stations, the sphere triangle closes it; the kit says 'not the chain's R - no vertex ball' by name); put a convex edge (a round between two original faces) in a fillet CHAIN of wall-foot creases and expect a corner there - the chain ENDS where the crease's sense changes, both blends taper to that junction, said by name (L145; leave the round out of the chain or decide it alone); expect a corner where the side face's corner at a chain junction is REFLEX (the corner edge leaves the junction past 180 deg from the crease) - no rolling-ball corner exists there: the chain ENDS, both blends taper, a member whose side face is a sliver narrower than t + 0.30 beside the junction is NOT made and its room line says so (L154: redraw the border so the side face has a wedge the offset crosses, end the chain there on purpose, or lower R); decide a fillet chain across a junction that is no corner (the crease runs through a far-side face boundary turning under CREASE_TURN_MAX) - the build refuses it by name: make the far side ONE feature so the crease is one line and one blend, or accept the member that lies between the no-corner junctions sharp (`"sharp_ok": [<line>]` on the chain's entry) - its chain-mates taper to those junctions (31bx K35; 31ca R5 F1); decide a LINE / ARC / CUBIC or an `_add` line that leaves the part by more than LINE_OFF_MAX 0.5 mm (31bq B19 - skin-wires measures every one against the source and refuses by name; decide an ARC / CUBIC, via points, or trace - a trace interpolates the surface's points); expect a symmetric edit's twin faces to come out alike from two independent spans (31br A3: the build spans the master and REFLECTS its surface onto the twin - TWIN_MIRROR 1; a twin spanned on its own is said, with why); expect two blends of unequal width to meet in a flat sliver at a kink - the kit merges their contacts within CONTACT_MERGE_MAX 2.5 mm on the wider one (31bq N / U), over it the junction keeps two and says so; give a piece failing check(True) on cosmetics only BOP_OK - the BOP gate passes the caps' own edges, the wire-clean pass's own cut-back pieces under 0.1 mm (the client 2026-10-23), edge tolerances and edge gaps under 0.02 mm and self-touches under the 0.30 mm print tolerance by itself (31bq B07 / R7d, the client's Q2; a C0 line or a wider tolerance needs BOP_OK with its reason); blend a crease whose mesh beside it is a face the design BURIES (a vane's end face in a slit under the crown, put into the crown's feature) without naming it - `"buried": [ids]` on the chain entry makes the host's own unburied original surface stand for the mesh there (fix 11, L149; BURIED_MIN / BURIED_REACH); read a station frame's colours as "old" and "new" - GREEN is a line both bodies share, YELLOW old only, BLUE new only (L146); accept a trial over the reviewers' blockers without the client's recorded ruling (`judge --what trial --verdict ok --ruling "<the client's words>" --note "<each blocker disposed>"`; L134); judge a look ok without saying, for every named region (SKIN_look_vanished_NN and its _section frame), whether the original's shape it shows YELLOW left the piece by design or is a feature lost - the look NAMES every connected region 2 mm2 or more of which lies over 0.5 mm from the piece and that no PTS_DROP box WITH its reason, burial or decided blend removes (31bq B18: the vane-1 lens pads of b27b / c1 left with nothing flagging them); expect a PTS_DROP box without its reason to clear a face - it is named (31bq B22);
  judge an orbit of the cuts you have not opened frame by frame, or go on past
  a cut that runs along a skin or inside a thin lip (L112 - move it); trust the chain's own review frames on a window that is not a section (they
  are placed from a section's centred window, BURRITO_REVIEW F11 - the kit's `kit review --box <the window + 3 mm>` is bound
  to the card's box: PI P-R31-01; never a centroid selector, P23; a focus box has eight corners, P25); use the sheet fitter
  as the converter (L88); change the method's steps
  or scripts mid-round (log the failure, write the inbox block); judge a wireframe ok on a record whose PREVIEW is missing or failed (31br G1 / G2: skin-wires runs the build's own
  ladder and blends on the decided lines and names the face that cannot be spanned and the fillet not made BEFORE the build; `"sharp_ok": true | [lines]` on a `_fillets` entry accepts
  lines left sharp on purpose; true covers each line's kit-mirrored twin too and a list names the master side's numbers - 31bs K29; the line is never swept and stays in its chain, its chain-mates taper to its junctions - 31bx X76); fit one cubic through more than two via points and expect it to pass them (31br D6: measured, refused over ADD_VIA_TOL 0.3 - `"poles": 5..8` or fewer
  points); ask for more poles than points on an added line ("poles": 8 with 5 via points - the agent's d19: the fit is underdetermined and the curve swings 13.7 mm between the points it passes; refused at the read, 31br D5b: poles <= via + 2, more shape = more via points on the surface); end a GUIDE on a decided fillet's crease and expect the fill through it (31br D2: the lines pass clips the guide to the strip's reach, said - a SPLIT where the shape needs
  it); expect a corner edge's blend at a declined vertex ball while a chain member at its junction was NOT made (31br D1: it stays sharp with the reason); charge a face's SPAN failure
  on your own added lines to the points (31br G4b: it is a WIRES try - three at one face lock the build until the lines there change); try to re-pick a restart spot whose box holds
  no source centroid (31br G4c: nothing to pick there - the kit releases such a spot itself and says so; if a lock stands that no lever can clear, that is a kit defect to report, never a dead end to work round); state a limit of the kit in a judge note without
  the build tag that showed it (31br I3, refused); expect a SPLIT ending at the APEX of a hairpin border to round the corner off (the agent's d14 / d19: one smooth curve through the hairpin, the lip piece failed its loop) - since 31bw A5b the wires draw that chain PER LEG at the split's decided end (the apex kept, said as DRAWN PER LEG, rung V(...)); the preview still decides whether the thin lip spans - if it fails, end the split where a corner survives, or fold the hairpin's face into the feature so the border becomes wall edges (d19b); make a split piece own a wall segment whose body surface faces the other way from the piece (31bu A6, the agent's d16-d18: the jog step at the x 24 wall faces fore, the closing piece aft - a 180 deg flip, 50 min) - a piece faces ONE way AT THE WALL too; a face that owns wall edges and fails to span says the facing at every wall stretch beside its inboard facing; read look_at's old 'in view' share as visibility (31br D11: the subject is the faces centred in the box, the share per face from the
  z-buffer; SECTION="y -110" for an inner region); run the FULL look or the second review on a piece whose check(True) faces you have not looked at (31br L1: `skin-look --set FACES=<ids>` first -
  seconds; a REDO / MOVE on an opened frame needs no second review; the full look refuses while a flagged face has no look; a face the targeted look cannot draw - not valid, over LOOK_TOL_MAX - is said UNSEEN and is no look: draw it with LOOK_TOL_MAX raised, or LOOK_FULL_OK - 31bs K28).
Expect faces: at or under the original section's count (requirement 4) - the build row says the piece's count against the content's (one measured section: 49 skin + 7 section
  faces against ~135-142). Give the Bash tool `timeout: 900000` for the reinsert's STEP 2.
Status: the passes and where the round stands are in the kit's development record (31ax); the live state is the project's STATE_NOW.
Long form: `kit howto burrito --step <step>` prints the step's ONE PAGE (31br I1, `kit\rebuild\STEP_PAGES.md`; the runner prints it when the step runs); `LEAN_KIT\BURRITO_STEPS.md` - THE SKIN ROUTE (the table, row by row; HOW IT ACTUALLY RUNS below it is the shelved voxel field), then the levers, the
  clocks, the record (REBUILD_*.json per step; merged into REBUILD.json and the region's dossier by kit accept), L2/
  L11-L14/L21/L22/L26/L27/L81-L113 before the first window; `kit lessons` prints the index; the RECOMMENDATIONS FOR THE
  FINISHING PASS at its end. (the round's status lines moved to the kit's development record, 31ax.)
  A DESIGNED OPENING: the project's ruling decides (PROJECT_FACTS section 6, the newest line on it; 31br D13) - a
  PROTECT box only round an opening the facts rule open, never round enclosed air beside it (the client
  2026-10-05; L111).
Recipe: a step with a counterpart in another route starts from that route's proven numbers (THE KEEP RECIPE in
  BURRITO_STEPS; the mesh route's `kit\mesh\LEVERS_CENSUS.md`, the project's `RECIPE_*.json`); a project session tests several
  items, one lever per build (the client 2026-10-02).
31br levers (suggested): PREFLIGHT 1 (the wires step's preview of the build; 0 skips it, said and refused at the judge), ADD_VIA_TOL 0.3, TRACE_TUBE_MM 2, CARRY (drop refuses a
  same-network LINES file that drops the last run's decisions).
Template: none - the chain's scripts are `kit\rebuild\sk_*.py` (the skin route) and `rb_*.py` (region, reinsert, review-body; the shelved voxel field), run from the kit by `kit rebuild` (31bq B48).

## voxel_smooth — one named region cleaned in the MESH by delta solids: only the material that changes is built
TREATS ONE DEFECT CLASS: a concave junction (or crack between two sheets) that wants a fillet, on a part whose
  deliverable is a PRINT MESH - a concave gap under 2 x CC_CLOSE. The ADD half fills concave voids; it does NOT treat a
  step, shelf, ridge, tab, crown, shard, fin, lip, facet or convex block (those are DRAWN: `mesh_union`, union and
  `--cut`; the B-rep's `cutter` for a B-rep round). The tell when aimed wrong: a FRAGMENTARY ADD mask. The card states
  the defect's class first; a box that comes from a survey list is drawn over the item's frame before it runs (2026-09-25:
  an unattended chain of nine such boxes spliced 0 of 4 attempted pieces - (e)'s box sat 46 mm from the notch).
Route: voxel mesh-smooth junction fillet-in-mesh crack weld-in-mesh print-mesh localized-smooth
Tier: ORCHESTRATOR until the levers are dialled in on a family of regions; then a lower tier per family, on the
  client's word ("get one finished first, have me approve, then do the rest").
Sequence: (V0-V4; `kit howto voxel_smooth --long` prints the long form) V0 INVENTORY (`kit inventory` - how many,
  where; never a triangle-density scan) -> V1 SELECT one box round ONE feature, tight; `kit frozen check`; NAME THE
  ROUTE from the acceptance (tangent blend -> A; visible rim tolerated -> B; blend AND identity outside -> C) ->
  V2 TOOLS (signed distance field, close/open/blur, ADD = state test, lumps labelled and CHOSEN one by one; bury by
  field; render the tools and open every frame before choosing) -> V3 PLACE in the mesh (A, THE CROP FLOW through
  `kit mesh <step>` - the route's scripts are the kit's, `kit\mesh\`: `kit crop` the base round the box -> `extract` ->
  `core` -> `refine` and `weld` ON THE CROP (seammerge, ONE unchanged base) -> the gates on the crop -> `kit mesh final`
  = one `kit splice` of every welded crop; the body is never a step's operand, `kit mesh` refuses a body-sized STL;
  B: drop in; C: `kit stitchband` then `kit stitch`) ->
  V4 PROVE (`kit visible` - did the tool change what can be SEEN; census as an equality count; +0/+0 mesh-health
  delta vs a control built the same way; spike gate; wall thickness against the process) -> `kit review` (L22 order,
  fail-fast leads on the box) -> a second independent render review -> deliver (`kit deliver --mesh`).
Levers (all CARD levers - a step that leaves one at a code default is refused): `box` `dev` `h` `r_close` `r_open`
  `sigma` `g_min` `t_bury` `add_open` `min_vol` `keep` `decimate`; route A's `CC_*` levers are classed in
  `kit\mesh\LEVERS_CENSUS.md` (120: CARD / CONSTANT / DEAD) and `kit mesh` refuses a CARD lever left unset - a project
  keeps its recipe's values in an EXAMPLE env file passed with `--env`, never in a wrapper, never in code.
  `CC_UNION_STL` (closed STLs unioned into the field before cleaning, which fillets them in) takes a DRAWN solid
  through this route - the slow way for a drawn shape (~15 min a 50 mm piece, a million triangles for four flat
  faces): a drawn addition is `mesh_union` (`kit union`, seconds); this route is for BLENDING (a junction, a notch,
  a film).
DO: run `kit reach` for any census (never a centroid selector); render with `LK_OWNERMAP=1` and turn what you SEE
  into triangle ids with `kit pick`; report mm3 ADDED and REMOVED separately; every buried vertex >= 0.45 mm inside
  material after decimation; the frozen registry checked before any lump is chosen; a regular array of lumps at
  constant pitch is SUSPECT (a designed feature as often as a defect).
DO NOT: crop geometry to frame a picture (zoom the camera); judge a colour boundary as geometry; take a mesh-health
  number as absolute; run the REMOVAL half until it has a keeper mask; chase a number with no requirement behind it;
  let a tool face land flush on a body face; resample a loop; mesh-boolean or B-rep-boolean the tool (both measured
  and rejected).
Expect: ADD and REM each one closed shell per lump, 0 boundary edges, inside the box; the result's welded boundary and
  non-manifold counts UNCHANGED from the control; volume added = the tool's closed volume.
Long form: `LEAN_KIT\VOXEL_SMOOTH_STEPS.md` (the procedure, the field construction and its traps, the three
  routes and their gates, the review rules, the environment). Its status: the crop -> edit -> splice flow is in the kit (`kit crop`,
  `kit mesh <step>`, `kit splice`; the whole body is never re-processed - a cropped piece is); the recipe levers are LEVERS_CENSUS.md's recipe column.
Template: t_voxel_smooth.py - it CHECKS the card and PRINTS the route's commands; it runs no edit itself (the CC_* levers of the steps are the second lever set, set in the --env json)

> **KEEP, DON'T REBUILD (L63):** a feature whose faces are intact in the brep is not re-fitted and not measured; the
> piece is the body kept between the feature's own surfaces (`Part.Face(face.Surface)`, swept, intersected, common'd
> with the body), so its faces are the original's and no seam exists. In the burrito this is `kit rebuild keep` (L102):
> the chain's piece is measured against the original and only the bins it changed are replaced. For any other edit the
> agent decides card vs keep from one section picture and the face list, and says which in STATE_NOW.

## mesh_union — a DRAWN closed solid added to or cut from a print MESH: crop, union [--cut], splice (a rail, a slab, a boss, a fill, a flush cut, a re-surfaced strip)
When: THE DEFAULT for anything that can be DRAWN on a part whose deliverable is a MESH (the print STL; the B-rep is not
  edited for the order): a rail, a slab, a boss, a pad, a notch fill, a flush cut, a fin or lip taken off, a step or a
  crease RE-SURFACED (= a union that covers the strip, then a cut with a drawn floor that follows the original). The
  R33-R35 round (2026-09-25) did every one of the client's a-e items and both slivers this way, 1-9 s a union and 41-170 s an
  apply on the 3.2 M-triangle body, where the voxel route could not touch a convex block, a fin, a facet or a step.
  `voxel_smooth` is for ONE class only: a CONCAVE junction under 2 x CC_CLOSE that wants a blend.
Route: union mesh-union mesh stl print-mesh print-stl print-file block-on-mesh pocket-in-mesh rail-on-mesh slab-on-mesh boss-on-mesh addition-to-mesh drawn-solid notch-fill flush-cut
  re-surface fill-a-notch cut-flush shave trim mesh-finishing appearance-fix
Tier: ORCHESTRATOR - no worker; numpy, no kernel, seconds. `kit newcard <J> --type mesh_union` scaffolds the card and
  prints the type's traps (leangate TYPE_TRAPS, 2026-09-25); `kit union --cut` is the same arrangement as a DIFFERENCE
  (the solid's inside removed - the ramp cut on the heatsink-plate rails, 2026-09-25).
Sequence: kit atlas find -> kit frozen check <the solid's box> -> DRAW the solid (any closed, outward-wound STL; a
  swept-profile script in the job folder is fine) -> kit crop <base.stl> --box <the solid's box> --margin 6 ->
  kit union <crop.stl> --solid <solid.stl> --out <union.stl> -> kit splice <union.stl> --crop <crop>.crop.json ->
  LOOK at it (`kit render` of the spliced mesh, boxed on the addition, every frame opened) -> at the end of the
  round's edits: printfile / printcheck / `kit deliver --mesh` (PRINT_READINESS.md).
Recipe: the intersection curve is computed ONCE (exact triangle-pair tests, one shared vertex per piercing) and put
  into both meshes, so the two rims are one polyline by construction; each mesh's part outside the other is kept and
  only the triangles the solid meets are touched - not the VTK mesh boolean `voxel_smooth` rejects. Checked after a
  float32 round trip: open and non-manifold edges must equal the crop's own, or it exits 1 with the open loops' boxes
  (look before splicing). `kit splice` refuses an edit that reached the crop wall - widen the box.
DO: MEASURE IN 3-D BEFORE DRAWING - fit planes to the ring of surface round the defect (rms 0.06-0.15 mm on the rework
  mesh; P and M agree to 0.003), section at several stations, and compare to the model of record so a designed pocket
  is not "fixed" (the wedge "spike" was a 0.16-0.33 mm step; the "notch" was designed). THE DRAWING RULES, SCOPED
  (2026-09-25, lessons D15 - the generic ones cost four tuning passes inside a 2.4 mm wall): bias OUTWARD only the faces
  of the NEW exterior, 0.02-0.08 mm off the measured plane; overlap at least 0.5 mm INTO existing material with every
  face meant to merge; the "2 mm clear" rule applies to faces left IN AIR, and a buried face is judged by the frozen /
  opening invariants instead; draw at a measured plane +- the bias, never at a round number (a face on a round-number
  plane grazes the body's own vertices and is refused or leaves 0.006-0.049 mm voids); sweep along a curved edge (a
  height-field fill cannot follow one); a cutter's FLOOR FOLLOWS THE ORIGINAL SURFACE (floor = max(design plane,
  original + 0.03), sampled on the pre-edit mesh) and `--baseline <pre-edit crop>` proves it takes ~0 original
  material (the three numbers, each for its purpose: >= 0.5 mm INTO material where the solid JOINS it; >= 0.3 mm clear in or out where a face must NOT touch the body - the card's trap; 0.1 mm sunk where a face is meant to end FLUSH). Sink a face that is meant to end FLUSH 0.1 mm into the body (exact coplanar contact is settled by a 1e-4 mm
  shift, to one side or the other); read the CAVITY warning - a drawn face spanning a pocket of the body encloses it
  and MJF traps powder there (reach below the pocket's floor, or fill the pocket with a second solid - the drawing's
  call); several solids in one crop go in one call (`--solid` repeated); separate places are separate crops, spliced in
  ONE pass (`kit splice --pieces`); trial on a crop of the CURRENT base (path + md5), hand back a pieces file (box,
  margin, solids, expected dV), apply exactly as trialled, and check the assembly clearance to a mating part (the
  cover) as well as the frozen regions - a slab in the cover seat passed every frozen gate and filled a third of a
  bore. The builder script asserts closed + oriented before writing (a reversed cap, an inward tool, 76 vertices
  outside the body were each caught there in seconds).
DO NOT: take a drawn shape through the voxel route (`kit mesh extract` + `CC_UNION_STL`) - it works, at ~15 min a 50 mm
  piece and a million triangles for four flat faces (marching cubes never knows a face is flat); union into the whole
  body (the crop is the operand); hand it a solid that is open, wound inward or does not cross the body's surface
  (each refused); tune past two iterations that miss a threshold (redesign the target or show the client the grazing render -
  (c) went through seven attempts and ~500 agent-minutes chasing a 3 deg kink below anything visible at their scale);
  splice a piece on a STATUS line before its check has returned; design on a private base carrying unapplied pieces
  (name ONE base by path and md5 in the design and the check brief).
Expect: open / non-manifold edges = the crop's own; the added mm3 printed, `<out>.union.json` beside the result (with the
  md5 of the crop, each solid and the output - a checker reproduces the run byte for byte from it); the splice's seam +0
  open edges (tens of them are a rim that did not meet - render the seam before the next piece). Measured: a 4 k-triangle
  rail into a 164 k-triangle crop, ~2 s; `--cut --baseline` replays the cut on the pre-edit crop and prints the ORIGINAL
  material it takes (the ramp cut that dug a 1 mm step into the chamfer would have read -70 mm3 there).
Long form: `kit union --help`, then the top block of `kit\kit_union.py` (the method, what it refuses, what it warns of).
Template: (none) - three kit commands; the solid is the orchestrator's own drawing.

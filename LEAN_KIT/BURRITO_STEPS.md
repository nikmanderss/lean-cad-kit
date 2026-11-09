# THE BURRITO — the rebuild chain (rewritten 2026-09-28; replaces the S3–S7 sheet-fitting chain)

**What it does, in the client's words:** *"start with a messy/sloppy/hole filled/sharp edged/etc brep and end with a cleaned
version of that, that is low face count, fits back into model perfectly."* The process is CAD-generic; mirroring is an
option, never a requirement (the client, 2026-09-13 / 09-25).

## WHAT IT MUST PRODUCE — the client's requirements (listed to them 2026-10-05, on their word: "follow the requirement of what the process is to produce")

Every decision in the chain - a lever, a gate, a tolerance - is judged against this list; a question to the client that the list
answers is not asked.

1. **B-rep in, B-rep out** - never a mesh in the delivered model (2026-09-29: *"brep at start and end"*); one valid solid.
2. **The junk gone** - gaps and holes filled; enclosed pockets filled (2026-10-05: *"enclosed pockets are not wanted"*);
   spikes, shards, tabs and folds gone - removed by the rebuild itself, the section re-made from the body's own design
   surfaces, not by a separate spike rule (2026-10-05: *"nothing explicitly removes them, they are removed by rebuilding bad
   sections"*); nothing under the 0.30 mm print tolerance (2026-08-21: *"No shards under print tolerances"*).
3. **Simple and smooth** - *"one big curve meeting other curves or flat areas cleanly"* (2026-08-21); smooth transitions, the
   air directed properly, printable features (2026-09-10).
4. **Very few faces** - *"the final section you edit is to have VERY few faces. Less than the original brep section that was
   removed or very close to it at the least"* (2026-09-29); reached by the finishing pass (NOT WIRED 1) - this chain ends at
   every triangle a face.
5. **Fits back perfectly** - a step where new meets old at most 0.15 mm, lowered never raised (2026-09-21, the fingernail test).
6. **Designed openings stay open** - what counts as one is the PROJECT's ruling (PROJECT_FACTS section 6, its newest line - the project names
   them: its windows, a slot array; a ruling can change and the newest line stands); a PROTECT box holds the
   OPENING only, never enclosed air (L111; 31bs T7 F10).
7. **Frozen regions recreated** at the end of the edits (2026-09-22): a NON-CRITICAL one (the vanes, the windows) within the
   0.30 print tolerance - *"nothing is critical below it"* - its roots / edges buried where the client allowed it; a critical one
   (cover seat, the bays, the mounts, QC) at the atlas gate's 0.15 as today.
8. **Symmetric where the design is** - *"the section you reinsert should be symmetric"* (2026-09-29).
9. **Printable on MJF PA12** - the print rules (the project `PA12_MJF_Rules_EVALUATED.md`): walls, no sealed void, deviation
   outward on critical faces.
10. **Judged by pictures** - before and after on one camera, every frame opened; numbers point, pictures decide (L2).
11. **Runs without the client, on any geometry** - a fixed method the agent runs and tests, failures logged; CAD-generic; no lofts
    (2026-09-19); no fallback to an older piece (2026-09-29).

## THE SKIN ROUTE (kit 31al, 2026-10-06) — THE BURRITO AS IT RUNS NOW

**The unit of work is the EDIT REGION** (the client, 2026-10-08: *"stop calling it a window that makes no sense"*) - the box plus its cut planes that the
region step records. Older text in this file still says "window"; it means the edit region, never the part's frozen WINDOWS. Every runner
and script message says edit region since 31aw.

the client, 2026-10-06, on the first remade skin sewn back into the body: *"one face is missing entirely and nearly everything is still far
too lumpy but otherwise I would call that a success"*; then *"There is a new burrito process and it works. The old process gets ~1/2
shelved and the new process needs gates/hooks/setup so it can be tested on new edit regions."* the agent's run:
a section remade as 49 skin
faces + the body's 7 section faces against the ~135-142 the window held - one closed valid solid, sewn in with NO boolean: STEP 4
CHECK PASS, seam 0 faces, PROTECT unchanged, no voids. The scripts are the agent's (jobs\REBUILD_JOB), in the kit as `kit\rebuild\sk_*.py`
with only the paths and a section's numbers made the job's (selftest_skin: the walls and distances equal the agent's to 1e-14).

| # | `kit rebuild ...` | what | writes |
|---|---|---|---|
| 0 | region | the edit region: its box, the cut planes, the walls, content.brep (the original's material inside it), the cut pictures judged (31bn fix 5: the pre-flight and the orbit of the cuts are THE PIECE VIEW - the body round the region and the content each one conforming mesh, judged, the frames stamped when the mesh fails or shows a crack, CUTS_REGION.json carrying every frame's quality; the judge refuses a stamped set. Fix 5g / 5h: `region_cuts_*` are the CONTENT ALONE with its faces in a wall plane RED - the body's section on that wall is the cut itself, and no correct picture of body and content together can show it - ONE frame FACE-ON to each wall (the camera on the body's side looking in; only that wall's section red, the other walls' dull) plus two isos for the crossing angles (the body covers it from outside, the content from inside: the old frames' red was the artefacts' gaps); `region_fit_*` (two) show the content in its place in the body, cut exactly on the walls, and the drawn cut body carries its own verdict - a ragged trim is a crack of the picture) | content.brep, walls.json |
| 0b | **skin-source** (31ba / 31bb / 31bc: A NEW SOURCE IS A RESTART - every standing verdict superseded, LAYOUT_LOCK and RESTART.json set aside, the rounds reset; a re-run on the same content changes nothing) | **THE VOXEL FIELD IS SHELVED** (the client 2026-10-08: *"the entire voxel step is now getting skipped. shelve it in the kit, as it may be used another time. Instead of voxel the wireframe redraw will handle all geometry corrections"*): the mesh every skin step lays its points, layout, frame and network on is the ORIGINAL content itself, tessellated ONCE (MeshPart, TESS 0.05 mm / ANG 5 deg, one segment per face -> the original face of every triangle, mapped to the BODY's face indices; remade only when content.brep changes) -> source.stl + source_fid.npz. The B-rep's faces are the START: what is KEPT is the agent's pick (row 3: a face with no point is absorbed; row 14b: a line left alone keeps its faces, a redrawn one re-spans them, a traced one follows the original); the only lock is the frame (the reinsert faces exact). arrange / arrange-m / arrange-f / blend / repair / review refuse without SHELVED_OK | source.stl, source_fid.npz, REBUILD_source.json |
| 7 | reinsert --set STEP=1 | **THE REINSERT FACES FIRST**: the local box and the body's own section faces on the window walls; reads no piece | wall_caps.brep |
| 8 | skin-regions | on a B-REP SOURCE (31bb): writes the mesh record the skin steps read (skin\regions.npz: the welded mesh + the original face of every triangle), no regions, no pictures (the client: "I do not need the pictures anyway"). On a voxel (SHELVED_OK): the changed regions of the voxel vs the original, clipped WALL_CLIP off the walls | skin\regions.* |
| 9 | skin-edges | the original's edges classified from the B-rep (frozen / convex / concave / smooth / tiny), then measured against the voxel | skin\edgemap\* |
| 10 | skin-points | **THE PICK OF WHAT IS KEPT (31bb, on a B-rep source):** ~NPTS points of the mesh (1000 suggested - a starting value, not a rule; 100-5000), each given to the original face it lies on (within ON_MM 0.10); an original face with NO point is absorbed by its neighbour in skin-labels - the grid drops the junk, PTS_BOX keeps a small face, PTS_DROP drops one. (On a voxel: a point on no original face is OFF, the fix.) **31an: the agent PICKS points** - PTS_BOX / PTS_DROP boxes, FRAME_PTS (points beside every reinsert-face edge; a frame face still without a point is ringed magenta); the frames include the views from below. **31av:** PICS quick (suggested) in the loop - about 8 frames, never none. **31bq B22 (the client 2026-10-19): every PTS_BOX / PTS_DROP box carries ITS REASON - `x0 x1 y0 y1 z0 z1 [spacing] | why` - refused without one (a deliberate drop with no recorded reason was undone by a later session and the build went invalid; the reasons go to points1000.json lever_whys)** **31br G4c (2026-10-29, the agent's d13): A SPOT WITH NOTHING TO PICK IS NOT A POINTS SPOT - the points are source-triangle CENTROIDS (the grid, PTS_BOX), so a restart spot whose box holds none can never have its points changed: such a spot is never locked (its three tries were the lines' or the build's - a span failure is a wires try, G4b) and a standing lock on one is RELEASED, said, at every gated step, at `judge --what points` and before this step runs (spots 5 / 9 of JOB3: 4 mm boxes on a free edge of the built piece over a flat face's large triangles, 0 centroids inside - every step after the points had been refused for good).** | skin\points1000.json, points_faces.json, POINTS_LOOK.json |
| 11 | skin-labels --set "MIRROR=x 0" (or empty) | THE FACES DECIDED BY THE POINTS. **On a B-rep source (31bb): every triangle labelled by its ORIGINAL FACE (skin-source's index) - a face with a point keeps its own triangles, so every border STARTS as a B-rep edge and every junction as a B-rep vertex (the client: "the border junctions are in the brep") - THE STARTING REFERENCE, NOT A CONSTRAINT (31bh): skin-features joins faces and skin-wires redraws, moves, splits or adds any border you decide - except at the FRAME, where every face ends exactly on the body's own section faces, edges and vertices; a face with no point is absorbed WHOLE by the kept neighbour it shares the longest border with, never across a crease (CREASE_DEG); an unseeded area closed off by creases is a face of its own (its face_src = the original face most of it lies on, for FEATURES); no flood, no border walk, no opening / island / noise merge, NO HOLE CUT (31bc: a face pierced by a stem keeps its hole - skin-build makes it with its inner wires); every kept face is kind orig whatever its point count.** On a voxel: a flood from the ON points, crisp original edges and creases as barriers, no bands, holed faces cut, wrapping faces split. **31an:** MIRROR is the CARD's symmetry decision (recorded; later steps take it) - a symmetric edit's layout is made on ONE side and mirrored (any plane); then THE FACE LADDER's rung 1: a face the points put on one original face keeps that surface (kind orig). **31av: its section-wide levers (OPEN_MM, BAND, ...) are LOCKED at the first layout judged ok** - after that a face changes through its points, its lines through LINES / RAILS | skin\patches_labels.*, MIRROR_DECISION.json |
| 11b | skin-features [--set FEATURES=<json>] (31as) | **THE FEATURE MAP** (the client: *"a good addition to the process"*; *"should be CAD generic kit steps"*): run it once without FEATURES - FEAT_labels_* write every original face's id on the layout (1121' = the mirror of 1121) - then name each face's FEATURE in {"feature": [ids]} (*"A spine, A vane, a support"*) and run it again; one face per feature per side, twins never merged across the plane (a V keeps its crease), small smooth faces joined (MAX_AREA, SMOOTH_DEG) - a section: 54 -> 32 skin faces. skin-rim refuses a layout that has not been through it. **31bq B22: the map carries `"_why": {"<feature>": "<why these faces are one feature>"}` for every feature, refused without; features.json keeps it** | skin\patches_labels.* (rewritten; skin-labels' kept as patches_labels_raw.*), features.json, FEAT_* |
| 12 | skin-rim | THE EXACT FRAME: each body cap edge owned by the skin face built from the original face it bounds; the voxel's rim relabelled by a constrained flood. **31an:** an orig face owning another original face's wall edge is fitted instead (with its twin); the layout drawn HERE from every side (LAYOUT_*) - never an earlier layout's frames; **31av:** its layout pictures say their borders are the VOXEL's triangles, not the model's edges | skin\patches.*, LAYOUT_LOOK.json |
| - | judge --what layout | every frame opened (LAYOUT_* from above, below and close; the rim's SP12_*) - the verdict on THIS layout. **31av:** an ok on the FULL set (skin-rim --set PICS=full once; a redo may be judged on the quick set); the FIRST ok locks the layout's section-wide levers (skin\LAYOUT_LOCK.json); THREE layout redos without a skin-build that passes send every place they named back to the points | skin\LAYOUT_LOCK.json |
| - | skin-mirror --set WHAT=layout | a symmetric edit: every face paired with its mirror (the plane from skin-labels' decision); a face with no partner FAILS; **31av:** a PASS names the next step (skin-network; for a piece: the TRIAL) | skin\mirror_layout.json |
| 13 | skin-network | one edge per border, built once, shared; REFUSED without the layout judged and (a symmetric edit) mirror-checked. 31bo: an original surface is projected onto only where it REACHES the border (the median distance of the raw border's segments within JMOVE_MAX; both reach = their intersection, one = that surface, none = the mesh border - said by name, recorded as far_faces); every chain's record carries its deviation from its own mesh border (measured along the border's segments), the worst said ("OFF THE MESH") | skin\network.* |
| 14 | skin-frame | the wall junctions on the body's vertices; the wall chains are the body's own edges | skin\network_frame.brep |
| 12+ | **`kit rebuild skin-layout`** (31aw) = skin-rim + skin-mirror WHAT=layout on a symmetric edit; **`kit rebuild skin-lines`** = skin-network (no pictures) + skin-frame + skin-wires | the client: *"2 commands, 3 picture sets"* - the layout's (LAYOUT_* / SP12_*), the mirror's (MIRROR_layout_*), the wires' (WIRE_*). **HIT / MISS:** a frame drawn from the same inputs before is a HIT and stays (`pictures: N drawn (MISS), M unchanged (HIT)`) | skin\review\.pictures.json |
| 14b | skin-wires [--set LINES=<json>] [--set RAILS=<json>] (31as) | **THE WIREFRAME DECIDED** (31bh, the client: "You can put the wireframe wherever you want. You simply have the original as a starting reference" - the original's faces and edges are the START; any border can be redrawn, moved, split by a line or added, faces joined by FEATURES, a strip folded into its neighbour; nothing holds you to the original's face boundaries - EXCEPT THE FRAME: at the edit region's walls every face ends exactly on the body's own section faces, edges and vertices, and skin-frame refuses an open face) (31az: the WIRE_* frames are drawn with HIDDEN LINES HIDDEN - the mesh opaque, each layout face its own tint, every line depth-tested: full where it is on / in front of the surface, faint dotted where it is behind the part; the agent's job_wire_occluded.py - the client: *"The hidden lines is valuable for your understand and should be maintained in the kit"*; WIRE_OCC=0 draws the old transparent form. `"trace": true` is DRAWN AGAIN (31bb): a traced line takes the SOURCE mesh's depth, and the source is the ORIGINAL - the original's own surface inside the face, geometry the agent wants kept (the client on the agent's traced vane-underside guides: "it's good they were traced that was geometry that was wanted to be kept")) (the client: *"a good addition to the process"*): WIRE_* number every chain and CORNERS_* every corner of the reinsert faces (c<n>); the agent decides LINES - each chain straight, one arc or one cubic, with its reason (*"about 50 wires, they should all follow a single curve or be straight"*) - and RAILS - a straight feature edge between two corners or junctions; the junctions made symmetric first; twins exact mirrors; nothing moves a line after it is drawn (no lay-back onto the voxel); the WIRE_* frames labelled by the FINISHED curve (LINE / ARC / CUBIC; MULTI magenta) - a section: 64 edges, 43 straight, 19-21 arcs. **31av:** the numbers in LINES are those on the LAST WIRE_* pictures; after a re-split the decisions are CARRIED to the new numbers (the same two features, the nearest middle within CARRY_MM 3) - skin\LINES_carried.json, only the new lines listed TO DECIDE; a decided line on an original face is ONE cubic span on it (ON_TOL 0.01), else that face (and its twin) leaves its original surface for the next rung - said, skin\wires_demote.json | network_frame.brep rewritten (skin-frame's kept as network_frame_raw.brep), wire_simplify.json, corners.json, WIRE_*, CORNERS_*, WIRES_LOOK.json; **31aw: ADDED LINES in the LINES json - `"_add"`: a GUIDE (the face's surface passes through it: the client's cross curves for depth; "trace": true takes the voxel's depth as one cubic) or a SPLIT (the face made two surfaces sharing the line - the fallback, and a face that wraps; its ends on the border, the border line cut there; never inside a wall edge), mirrored to the twin; `"_fillets"`: a line rounded by the kernel after the solid, or - when the kernel fails - BY LINES (31ax, the client: "If fillets fail then they will be made by the added drawn wireframe line"): two offset lines a radius from the crease, the strip between them one blend face through the arc's sagitta, the crease gone; the sharp piece stands if that fails too (31bl - A FILLET NEEDS ROOM, the CAD-generic rule, said in the same words where the fillet is DECIDED (skin-wires: a room line per decided fillet, before the judge) and where it is MADE (skin-build: the width rule, and the kernel's failure line): a fillet of radius R touches each face t = R tan(beta/2) from the crease (beta the angle between the faces' normals; 90 deg -> t = R) and needs t + the print tolerance (THIN_MM) of face beside the crease; where another border - a hole's rim, a neighbour's border, a wall edge - is nearer, EITHER make room (move that border or fill the gap, as the design intends) OR lower R; the kit measures and says both, it never chooses. The kernel's fillet is tried first at the decided R; the lines blend behind it is the arc of R swept along the crease, a NURBS surface with a cap at each junction, an ORIGINAL face allowed on either side. A split never ends inside a wall edge - refused at the wires with the corners to end on; a split ending at the APEX of a HAIRPIN in the raw border (the border turns over HAIRPIN_DEG 120 within HAIRPIN_MM 1 there - a V lip, a wedge tip: one smooth curve rounds the apex off and the end snaps onto it) is SAID at the READ with the corners / junctions to end on and the fold-in way out, before the simplify and the preview run, and the preview's verdict names it for a face it fails (31bu A5; since 31bw A5b the chain is DRAWN PER LEG at that end - each leg its own curve, the apex kept as a corner of the border, the split's end on it: L157; the agent's d14 / d19 - a thin lip fails, the agent's d15 riser at a 173 deg apex built: the preview decides); 31bm: where the offset line meets no border leaving the junction the blend TAPERS to the junction - the radius to nothing over TAPER_X x t (at least TAPER_MIN), no cap, no cut, the junction point itself sharp; the crease is measured AS BUILT at the kernel stage and a border whose built faces are tangent (under CREASE_MIN_DEG) is NO CREASE - refused by name; the kernel's fillet fails on NURBS fills at every radius (measured on b20, single or grouped) - the lines blend is the route there; the client 2026-10-13: NO MESH ROUTE for blends - the voxel closing stays shelved); 31bo: the crease's SENSE (convex / concave) is the mesh's own dihedral along the border, the same from either side and under a reflection; the offset lines are SMOOTH (the mesh normals filtered along the crease over FIL_SMOOTH_MM); a crease with a CORNER inside it (its tangent turning over CREASE_TURN_MAX within 1.5 mm - a V) is refused by name: make the corner a junction and decide the fillet per leg; a split ending anywhere on a fillet's crease moves to the strip's border; 31bp: a V IS decided PER LEG - end a split (or a decided line) on the corner, and the same `_fillets` entry with "leg": "all" (or a leg number) blends each piece of the line between its junctions and the split ends on it as its own crease, tapering to nothing at the corner, which stays a point; 31bp fix 6b: a chain is one blend between members of ONE sense - where a concave crease meets a convex edge (a round between two original faces) the chain ENDS, both blends taper to that junction (or take the cap), said by name (L145); 31bp fix 11: a chain entry may name original faces the blend BURIES - `"buried": [ids]` (the vane's end face in a sub-millimetre slit under the crown, put into the crown's feature so the lip is the vane | crown border): where the mesh beside the crease on a face is a buried face's (BURIED_MIN of the samples), the face's own UNBURIED original surface stands for the mesh - normals, offset, side, the sense from the material directions - said by name; refused when no unburied surface of the host reaches (BURIED_REACH); never the merged face's recorded source when that is the buried face itself (L149); 31bq: the wires' rules of the open-bugs campaign are L152 (lines measured against the part, the room line - its ends and its NORMALS as the build's -, the buried faces, the twins, the carry, the trace) -> skin\guides.brep / guides.json / fillets.json, drawn orange / white in WIRE_*; **31br (2026-10-29) THE PREVIEW - G1 / G2:** right after its records skin-wires runs sk_build as a CHILD (SKIN_PREFLIGHT=1, FILLET_LINES = every decided line, the BUILD's own levers - the runner hands PREFLIGHT_BUILD_ENV = step_defaults(skin-build) + the live piece's build record, the direct form the job's newest env_skin-build record): every changed face spanned by the ladder, every decided fillet swept and its strips cut, the face stage run, then it ENDS before the shell and writes skin\preflight.json (faces: span kind / fail; lines: made / not made and why; the kit-made pieces that failed); the step says PREVIEW VERDICT - PASS, or THE BUILD WOULD FAIL naming the face that cannot be spanned, the kit-made piece that fails, the fillet NOT made (unless the `_fillets` entry carries `"sharp_ok": true | [lines]` - those stand sharp, accepted, said; 31bs K29: true covers the entry's line(s) AND their kit-mirrored twins, a list names the master side's numbers and a twin is accepted with its master - decided where each record is built and carried with the lines, never re-keyed by line number); `judge --what wires --verdict ok` REFUSES a record whose preview is missing or failed; PREFLIGHT=0 skips it, said and refused at the judge (the agent's d12: face 4's two-facing belly piece named at the wires in 72 s where three 7-minute chains had found it; the cost +72-163 s on the wires step, its own clock row PREFLIGHT=1). THE WIRES' OWN CHECKS: an `_add` cubic through more than two via points is MEASURED against them and refused over ADD_VIA_TOL 0.3 mm (`"poles": 5..8` on the entry lets a longer spline pass them, never more poles than points - the via points + the two ends - or the fit is underdetermined and swings between the points it passes: the agent's d19 "poles": 8 with 5 via points swung 13.7 mm, refused at the read since 31br D5b; the agent's real 7-point guide reads 0.13); a trace follows its face within TRACE_TUBE_MM 2 SIDEWAYS of the line's own plane (the agent's d3 guide had wandered 3.18 mm round its face) - the DEPTH stays the agent's `"span"` decision (the 10-22 ruling), and `"span": "face"` interpolates straight across the whole face (the closed slot under the keel: 18 mm, 0.00 off the chord, no face list); a one-member `"lines"` is taken as `"line"` and every `_add` / `_fillets` SHAPE is checked in the first second (D5); a same-network LINES file that drops the last run's decisions CARRIES them, said (D8; CARRY=drop refuses the carry). THE RESTART RULE ATTRIBUTES THE TRY (G4b): a SPAN FAILED piece that carries the agent's added lines is a WIRES try at that face (RESTART.json `wires`, never a points spot); three at one face lock skin-build until the lines AT THAT FACE change (guides.json's entries on it + its borders' decisions - a signature kept at the lock), the network changes, or a newer preview spans the face; a wires run with the face unchanged keeps the lock, said. |
| - | judge --what wires | **31as:** every WIRE_* frame opened - each line where its feature's edge is, one simple curve, both sides alike (the client: *"The only way to decide if a measurement is bad is to first render review what lines you have drawn"*); skin-build refuses without it, and again after any change to network_frame.brep; **31av:** an ok on the FULL set (skin-wires --set PICS=full); **31br:** REFUSED when the record's PREVIEW is missing or failed (G1 / G2 above) - a wireframe the build cannot span is not judged ok; a judge note that states a limit of the kit without the build tag that showed it is refused (I3) | skin\review\WIRES_JUDGED.json, skin\preflight.json |
| 15 | skin-build | **THE FACE LADDER (31aw - THE FACE THROUGH ITS EDGES; 31az: NURBS FIRST - the client 2026-10-08: "After the wireframe the surface creation is defaulting to Coons. It should prioritize using NURBS. Those work much better in most cases"):** the original's surface (rung 1, from the layout) -> four or more edges in one plane = a PLANE -> **the NURBS fill** (the agent's job_skin_build_nurbs.py: OCC's plate fill through points every NURBS_STEP 1.0 mm on every edge and added line, approximated to ONE B-spline; a ladder of starts - the mean plane, then the Coons / plate of the edges as the start, enlarged 1.1 / 1.3, then edge points every 0.3 mm; the first fill that holds its rim within NURBS_RIM 0.10 - the agent's sn6 - and does not fold wins; a face that owns a wall edge within NURBS_WALL_RIM 0.02, or the frame check breaks; NURBS_SKIP names faces that keep the Coons - a long spine top waved as a fill) -> the Coons patch of the face's four sides as one B-spline surface, the border exact (a corner inside a side leaves a C0 line, said by check(True), sound for the sew) -> a face whose Coons patch folds (a concave outline) = a PLATE, the smoothest height field over its own plane through its edges and added lines, trimmed -> a face that folds and turns past 80 deg is REFUSED: split it with a wire. Added GUIDE lines pull the surface through them; SPLIT lines make the face two; FILLETS by the kernel on the sewn solid, else by lines (31ax: a second pass of the build with FILLET_LINES - the strip beside the crease one face; a failure keeps the sharp piece, said) (31bl: a hole in a split face is BRIDGED - n split lines from the outer loop to the rim make n NURBS pieces; a kept face that absorbed more than a sliver of other original faces is CHANGED and spanned (ABSORB_MM2 / ABSORB_FRAC); every spanned face's seconds logged (skin\SPAN_CLOCK.json), a face far over its rung's typical SAID, no time bound; the solid's self-intersecting face pair named; skin-look's face frames from the corners that SEE the face (LOOK_VIS), a face seen from nowhere said - a slit of air or an enclosed pocket). Nothing of the voxel is in a surface. shell -> solid; THE FRAME CHECK within FRAME_TOL (0.02 suggested, 0.15 max). The faces failing check(True) NAMED; a passing build saves its whole state (`kit rebuild restore --tag <T>`; 31br A2: with every look record and the frames it lists, so a restored verdict comes back with the pictures it was judged on; a REDO / MOVE of a restored layout or piece is judged on an opened picture whatever the frames record; `skin-rim --supersede "<the client's words>"` re-makes a judged layout on their word) and the design file's best copy. **31bq: the build FAILS on a self-intersection over the 0.30 mm print tolerance (B16) and refuses a PLATE that balloons past its border's own height range (B17; PLATE_BALLOON_MM 2 / PLATE_BALLOON_FRAC 0.15); R7W build-depth / F.4 (R7Wd 10-22, R7Wy 10-23): THE DEPTH OF A CROSSING is read on the faces' own meshes - a face through a NARROW face is read on the larger face against the surface beyond the narrow one (the connected component of the mesh without that face and its OWN neighbours - a face's own neighbours cut its arms near its own border and read a 0.42 mm penetration as 0.25; verify-fix-depth), the members' boxes pruning the search exactly, a member the mesh lost within 0.5 mm (the kernel's distance, never the box alone) said; the kernel confirms a foot inside the member's pcurve domain; an unmeasured depth is never cleared by its length at any of the three gates; a lines pass that leaves the shell open is said as `LINES PASS - FAIL`, the sharp piece stands with rc 0 (B01) after ONE retry without the members the record blames (B03); a hole in a chain is closed by the missing member's own crease (B04); the kernel's fillet is not tried between two fills (B55); the long kernel calls declare themselves busy to the runner's watchdog (B02); an open extra loop of a face names the foreign edges (B20); 31bq (2): the lines pass RETRIES by blame only an OPEN shell, from the LATEST pass's record - a self-intersection, a frame failure or a crash is said as such, the sharp piece stands and its SKIN BUILD PASS line is the verdict (B03 / B01); two members' contacts on a corner edge within CONTACT_MERGE_MAX 2.5 mm are made ONE on the wider member's contact, the narrower swept again outward (the 26 deg sliver that no rung spans is gone - N / U); the blend over a BURIED face has its host's offset AWAY from the buried triangles and a crease ONE sense (the buried host agrees with the other face's own reading - K (2)); a NURBS fill's rise past its border's height range is said, the plate's refused (B17); the span declares itself busy (B02); 31bq R7W A4 / A10 (10-22): THE NURBS LADDER RANKS A FILL BY ITS INTERIOR TOO - every try that holds its rim has its RISE past its border's own height range measured on the FACE (inside the fill's own rim range, not the enlarged margin), and a try rising over the 0.30 mm print tolerance loses to a flatter one whose rim misses by no more than the TRADE RIM (the caller's: a wall face trades up to NURBS_RIM 0.10 only when NURBS_WALL_RIM was loosened over its 0.02; the fillet caps and every caller that hands none keep their own rim) - said as THE INTERIOR RANKED and recorded (the vane plate's 6.7 mm / ~1670 mm3 balloon of every fill build since fill15, named and refused for the first time by the live kit on 10-22: 13736.8 -> 12065.1 mm3); the PLATE balloon samples every pole's GREVILLE point and each knot span's centre too (a spike of the surface's own basis between the 25 x 25 grid's samples had passed at 22-52 % of its height); THE WIRE-CLEAN PASS (31bq R7W R7Wn, 10-23 - the client 10-22: "some form of rounding that would make sense to apply to everything to avoid the tessellation issue"): EVERY FACE LOOP IS CLEANED AT THE CONSTRUCTION TOLERANCE (sk_clean.TOL 0.02 mm - the client's Q2 bound, the kernel's sewing scale; never the 0.30 print tolerance, a design bound) BEFORE THE FACE IS BUILT - a GAP under it between consecutive edges joined, a SHORT edge dropped, a GRAZE (an edge's end stretch running along its loop neighbour over a run >= 0.02, told from a corner by the GROWTH LAW of the distance from the shared vertex) cut back to its foot on the neighbour, the neighbour split there and its piece handed to the face across the cut edge; every other loop holding a changed edge - the object or a copy of the curve - takes the pieces it is now; a body (wall) edge is never touched (L114); every move said with its number, WIRE_CLEAN_TOL=0 turns it off (B26 v9's torn left junction: c's tapered offset 0.0004 mm outside the border it ends on for 0.03 mm - the piece view's 10 cracks to 0 on the vertex copy, L153)** **31br (2026-10-29):** D1 (c) a corner edge's fillet HELD for a vertex ball the junction test declines is swept as a SINGLE blend decided at the chain's END and only when every member at its junction was MADE - else it stays sharp WITH THE REASON (a member not made leaves its crease sharp on the side face, and a blend on the corner edge beside it cuts that face to a wedge no rung spans: qq d1b, both passes failed; d1d = the control byte for byte); D2 the lines pass CLIPS a face's guides to its loop of this pass, only on a face holding a fillet in this pass and only the points within 2.5 R + 0.30 of that crease and outside the loop (a polygon test alone misread a 47 mm curved face and lost 29.4 mm3 on a face with no fillet: d1c); D4 a face the points dropped is no source surface for a buried host, said; D3 every sk_*.py re-runs itself under runpy inside a try so a crash's TRACEBACK reaches the log (FreeCADCmd prints the message alone); I2 after a failed lines pass THREE THINGS FIRST - the faces that failed to span and why, the members dropped, the one recommended change; the SKIN_PREFLIGHT child (row 14b) is this step ended before the shell. **31br L1 (the client 2026-10-29: 'wouldn't it make sense to only render those 4 spots as a check first?'): THE CHECK FACES FIRST - when check(True) names faces, the step's NEXT line names them and sends the agent to `skin-look --set FACES=<ids>` (their two iso views each, seconds) before any full look: a real defect -> `judge --what look --verdict redo --face <n>` (no second review needed) and the lines / points THERE; a tolerance-level flag or the body's own cap face -> said in the note.** | skin\piece_skin.brep, piece_faces.json (rungs cap / orig / flat / span / plate / fillet), tags\<T>\STATE.json, DESIGN_best.json |
| - | judge --what look (31az) | **THE LOOK VERDICT** (the client 2026-10-08: the agent "moving to next steps when it knows the results are incorrect rather than reworking the edit - tried to move to mirror check with bad geometry"): every frame of PIECE_LOOK.json OPENED (the look gate's record); a frame stamped RENDER DEFECTIVE refuses any verdict (31bn - make the mesh right and draw it again); then ok = the piece is right in every frame; redo = what is wrong and where (--face / --spot: a try there) - fix the lines or the points THERE and build again. skin-mirror WHAT=piece and a TRIAL refuse without a look ok on THIS piece (md5). **31bq B18 (R7W):** an ok (look or skin) is REFUSED when the look's measure of the original's faces against the piece was NOT TAKEN, or the record carries none (a look drawn before B18) - a check that did not run is no pass (R5j's rule); a voxel source, where it does not apply, is said | skin\review\LOOK_JUDGED.json |
| 16 | skin-look | **31ar: LOOK_MODE quick (suggested) in the loop** - the whole piece, 8 iso frames from above and below; **full once**, for the second reviewer: + the close-ups normal and grazing and every FITTED face in TWO ISO VIEWS under a side light (31an); no edge overlay. **31bn: THE PIECE VIEW - the one render method of every piece picture (the client 2026-10-13: "The render creation method must be controlled. Instructions are not good enough. Only good renders allow for good work ... Lowest compute that includes all functionality/features of the best renders ... The renders must be accurate to the geometry"):** ONE conforming mesh of the whole piece (MeshPart on the solid, Segments=True; PIC_DEV 0.02 mm / PIC_ANG 0.05 rad, made once per piece and cached. The per-face tessellation every picture used before left 6130 open edges on the closed 59-face b20i piece - measured by their gap in fix 4, 6108 are closed within 0.02 mm and 22 open by up to 0.024: the torn look the agent and the client saw was look_at's centroid clip and the painter's-order renderer, not the seams), drawn opaque through a TRUE z-buffer (fix 4: the painter's order by mean depth had painted hidden faces over visible ones), smooth-shaded from the surface's own normals within each face (a crease between faces stays sharp; flat facets read as crumple to every reviewer), a tint per face, every line depth-tested; the mesh is JUDGED against the surfaces it stands for before it is drawn (CRACKS = open mesh edges wider than PIC_DEV - MeshPart's own T-junctions and split vertices, closed within a thousandth of a millimetre, are SEAMS and the rim of an open shell or a face subset is EXPECTED; 3000 area-drawn triangles against their own face's surface - the p99 distance against twice PIC_DEV or the piece's largest edge tolerance, the p99 facet lean against twice PIC_ANG) and a frame whose mesh fails carries a red band **RENDER DEFECTIVE - NO EVIDENCE** with the reason; its record (frames.jsonl, PIECE_LOOK.json) says defective; `judge` refuses a verdict on a set that holds one and a `--frame` that is one, the look gate does not count it as a look. The free edges a look draws are the PIECE'S OWN (an edge one face holds), never a side file (fix 4: a failed later build's free_c.brep was drawn over the restored, closed b20i), and their close-up's camera is chosen to SEE them. The same view draws `kit tool look_at` (the whole shape, the faces at the box tinted, the box depth-tested, the camera the one of eight that sees most of the subject - the share in the title; an STL the same way) and the mirror pictures. A frame is named by its VIEW (SKIN_look_orbit_045.png, SKIN_look_face008_iso1.png): the quick look's frames are the same files as the full look's. The quick look 12 frames ~26 s, the full look 82 frames ~130 s. **31bq B18: THE ORIGINAL'S FACES AGAINST THE PIECE** (an original feature had left the piece with nothing flagging it - the agent's b27b / c1: the vane-1 lens pads, merged into the vane top by the feature map and re-spanned away; only the trial's station frame showed them): every look samples every original face of the content (the source mesh, 5 samples a mm2) against the piece's own mesh (sk_lib.dist_capped - exact to 1 mm, its pairs in bounded chunks), gathers the samples over VANISH_MM 0.5 mm from the piece into connected REGIONS (VANISH_LINK 1 mm: a feature that leaves as several small faces is one region, the two lens pads of a symmetric edit are two) and NAMES every region with VANISH_MM2 2 mm2 or more of off area that no record accounts for - a PTS_DROP box WITH its reason (31bq B22; a box with none is NAMED), a chain's "buried" list and a DECIDED blend's strip (fillets.json of this wireframe: the sample on one of the line's two layout faces, within t + 0.5 mm of its crease as drawn, nearest a blend face of the piece) account for it; the pick's absorption (no point), a feature-map merge re-spanned (its `_why` quoted), its own re-span and nothing (NOT ACCOUNTED FOR) are NAMED, each original face there with what the record says; VANISH_FRAMES 6 named regions at most get two frames of THIS look each - SKIN_look_vanished_NN_section (a section through the region as the station frames draw it: GREEN the original and the piece together within 0.5 mm, YELLOW the original only, BLUE the piece only - a filled loss shows there) and SKIN_look_vanished_NN (the piece view, the original's off surface YELLOW - ghosted over the piece where it lies inside it - its borders magenta), keyed by the records they draw (a skin-wires re-run redraws them, not the look's other frames); a region under 2 mm2 is said as partly off, a feature of the map with no face in the piece is named; a look that cannot measure says NOT TAKEN (a kit fault named as one) and `judge --what look` refuses its ok. The look's verdict says, for each named region, the design or a feature lost (a lost one: its points, its feature or its lines). Measured (31bq R7W): the block 39.2 s on the first quick look of the agent's fill piece (471 568-triangle mesh, 10 frames of 5 named regions drawn; the whole look 34 frames), 10.7 s when every frame is a HIT, 34.0 s when the 10 vanished frames are redrawn (a fillets.json rewrite); 9-14 s with no frame drawn (b27b / c1 / fill replays). **31br D11 / G3-lean:** `kit tool look_at`'s SUBJECT is the faces CENTRED in the box (the faces merely touching it are context), the share in view said PER FACE from the z-buffer (a hidden face named with the way out - the agent's keel box had read 90-95 % in view with the keel behind the vane plate: 12 %, face 23 0 %), `SECTION="x|y|z v"` cuts the camera's half away and shows the inside (the cut's ragged edge is the mesh's triangles, said on the frame); the look's vanished-region classes: a PTS_DROP box excuses FILLING (closing a slot), never REMOVAL - a region of the original removed by the piece is named `removed` (the agent's d8 / d9 had planed the keel off under a drop-box reason). The step's ONE PAGE (kit\rebuild\STEP_PAGES.md) is printed when a step runs and by `kit howto burrito --step <step>` (I1). **31br L1: `FACES=<ids>` is THE TARGETED LOOK - only those faces' two iso views (any kind, any size), the look recorded as mode `faces` with the faces looked at for this piece (skin\review\FACES_LOOKED.json, by piece md5); an ok is never judged on it (redo / move only - the quick look is the piece's own verdict), `second --what skin` refuses it as it refuses a quick look; `LOOK_MODE=full` is REFUSED while the build's check(True) names faces of this piece that no targeted look has shown (the way out said; LOOK_FULL_OK="<why>" overrides, recorded).** **31bs K28: a FACES id the look cannot draw - not valid, an edge tolerance over LOOK_TOL_MAX, or no triangle of it in the piece mesh - is SAID (UNSEEN, with the reason) and is NOT recorded as looked at (PIECE_LOOK.json faces_unseen); the full look stays shut on it until a targeted look draws it (LOOK_TOL_MAX raised) or LOOK_FULL_OK (a closed band - a hole's cylinder - is drawn along its axis, 31bt) - a face nobody saw is never a looked-at face.** | skin\review\SKIN_look_*, PIECE_LOOK.json (per frame: quality; original_faces - 31bq B18: TAKEN / NOT TAKEN, the named regions), skin\review\ORIGINAL_FACES.json (every original face's area off the piece, every part's class), skin\review\.mesh_<md5>.npz |
| - | reinsert --set STEP=2 / 3 / 4 --set TRIAL="<why>"; review-body; judge --what trial | **31ar: THE TRIAL - the built piece seen in the REAL model before it is accepted** (the client: *"Sometimes building the model and getting true renders is the right answer"*): its MIRROR CHECK first on a symmetric edit (the client: *"mirror checks should pass before creating a real model"*), the second reviewer not yet; the body is body_trial.brep - body_new.brep only by its ACCEPTANCE (below), never applied or delivered as a trial; review-body reviews it; `judge --what trial` redo / move naming the place (a try there), or ok after its two reviewers (the acceptance). **31av:** 31bq B10 / RR: a TRIAL's STEP 3 needs no atlas assignment; its ACCEPTANCE refuses without one (`kit atlas assign <job> --to <region>` before `judge --what trial --verdict ok`); a trial FILE for the client only when the client asks: `kit deliver <REV> --trial "<the client's words>" --target <body> --model <job>\body_trial.brep` -> Deliverables\<REV>\review\<REV>_<name>_TRIAL.FCStd, never a delivery | body_trial.brep, review_body\TRIAL_LOOK.json **31aw: THE TRIAL IS THE ACCEPTANCE** (the client: *"If a trial passes, do not rebuild it, do not reinsert it. Yes to orbit, 2 reviewers"*): `second --what trial --assign` -> TWO cad-reviewers over the real model's frames (the orbit, the close-ups, the old-vs-new stations; 31bp: the brief prints the result's schema, and a shard result off it - a verdict that is not pass | fail, a defect with no severity of blocker | flaw | note - is refused by name) -> `judge --what trial --verdict ok` (31bp fix 7b: when the reviewers found blockers, only with the client's recorded word - `--ruling "<the client's words>" --note "<each blocker and why it stands>"`, the ruling and the overruled blockers in TRIAL_JUDGED.json and the BUILD_LOG row; L134: their judgement, not their agreement) -> PROMOTED: body_trial.brep is body_new.brep, the piece judged ok, review_body\ a COMPLETE review; a skin-build or STEP 2 of that piece refused after it; then kit review / check / look / accept | body_trial.brep -> body_new.brep, TRIAL.json accepted, review_body\SECOND_trial.json |
| - | skin-look --set LOOK_MODE=full; second --what skin --assign; one cad-reviewer per shard; second --shard k --result <json> | **31an: THE SECOND REVIEWER BEFORE THE AGENT, EVERY TIME** - on the FULL look (31ar: it refuses a quick one; `--assign` because kit.py strips `--brief`); defects ranked largest first; a blocker refuses `ok`. **31br L1 (the client 2026-10-29: 'Why are you running a full review ... if you know it has issues?'): the second review gates an OK only - a REDO / MOVE of the piece judged on an opened frame is recorded without it and counts its tries; the full look itself waits for the targeted look of the check(True) faces (row 16).** | skin\review\SECOND_skin.json |
| - | judge --what skin; skin-mirror --set WHAT=piece | the piece looked at (and mirror-checked) - STEP 2 refuses without both | |
| 17 | reinsert --set STEP=2 / 3 / 4 | JOIN=sew on the caps (the default; no boolean); a piece failing check(True) needs BOP_OK="<why>" (recorded; 31bq B07 / R7d, the client's Q2 2026-10-19: cosmetics only - the caps' own body edges (TooSmallEdge on cap faces, and - the client 2026-10-23, R7Wn5 - on a face holding a WIRE-CLEAN PASS-MADE edge under 0.1 mm: the cut-back's border piece, its geometry moved under the construction tolerance, matched by patch / sub and the edge's own length), edge and vertex tolerances and edge gaps UNDER 0.02 mm, self-touches under the 0.30 mm print tolerance - pass without it; a C0 line inside a Coons face is not in their list (BOP_OK with its reason until the client rules); the kernel's real check(True) words are parsed, an unparsed kind is never a cosmetic); STEP 4 CHECK PASS. After a TRIAL, a real STEP 3 / 4 refuses until a real STEP 2 has run (what a trial sewed becomes body_new.brep only by its acceptance) | body_new.brep |
| 18 | review-body; kit review / check / look / accept | as for any B-rep result. 31bn fix 5: review-body's frames (the trial or new body whole and at the region; the stations drawn from the same conforming meshes), the seam frames of STEP 4 and kit review's orbits (the tessellation cache = the one conforming mesh with its quality; the arcs through the piece view, the capped cut kept) are THE PIECE VIEW - judged, stamped, their records (REVIEW_BODY_quality.json -> TRIAL_LOOK.json; the review's cache) carrying the verdict; `judge --what trial` refuses a stamped set. 31bp: the stations cut the WHOLE mesh of each body and clip the segments to the region's window (a centroid clip of the triangles drew an old floor line with no new partner where the kernel's sections were identical); 31bp fix 7b: a station line both bodies share is drawn ONCE in GREEN (within the seam ceiling SEC_TOL 0.15), the differences YELLOW (old only) / BLUE (new only), the segments cut at the window, the counts per station recorded (STATIONS_<tag>.json) - a 1 px new line on a 3 px old one had been read as either colour by every reader (L146). 31bq: kit check's face budget is the EDIT REGION's (B08; R7W: every face CLASSED by where its triangles lie - INSIDE the region (the job's window + planes), ON A WALL, WALL-ADJACENT (the boxes, the reinsert's local box, the region) or FAR; the budget judges INSIDE; a FAR face that changed FAILS by name - nothing may change there; the walls' splits are reported and bounded by WALL_GROW_X x the base's faces at the region (kit check --wall-grow-x, suggested 4); a --box apart from the local box is a region of its own); a column counts as opened only when the 0.02 mm mesh of the faces near the box agrees (B09); a self-intersection over 0.30 mm in the build's own record fails the check (B16); kit accept REPORTS the volume change by the local ruler - the kernel's and the meshes' piece-minus-content with their spread - and the pictures decide (B21, the client 2026-10-19: "change reported, picture decides"); the reinsert's BOP gate passes a piece whose check(True) failures are cosmetics only - the caps' own body edges, the wire-clean pass's own cut-back pieces under 0.1 mm (the client 2026-10-23, R7Wn5), edge tolerances and edge gaps under 0.02 mm, self-touches under the 0.30 mm print tolerance (the client's Q2) - without BOP_OK (B07 / R7d; the kernel's real words parsed, an unparsed kind never cosmetic); kit check FAILS a piece whose faces cross themselves or whose face pairs went unmeasured under a check(True) that says SelfIntersect, and an edge gap over 0.02 with no BOP_OK recorded (R7d); a judge's missing --frame is 'no such picture', never a strike (B12). THE BURRITO APPLY (31bq R7W route-end D3, 10-23 - a METHOD ADDITION): `kit apply --job <J>` applies a job whose RESULT IS THE WHOLE BODY - the accepted body_new.brep is COPIED into claude_code\bank\<next REV>_BODY_MASTER.brep (md5-checked; never a fuse, never a piece) and PROMOTED as the model of record (the promotion recorded with the job; a STATE_NOW block, never a root STATE.md); the gate is kit accept's (checked, looked, the card's tripwire) and `kit accept` comes first (the COMPLETE review, the rebuild record into the dossier); a second apply of the same job, `kit promote` of a jobs\ file no applied job stands behind, and a real `kit deliver` of a job file or of a promoted non-bank file are REFUSED; a trial file (`kit deliver --trial`: the trial's body that passed its own STEP 4, no atlas objects, `_TRIAL.delivery.json`) spends no REV. A trial's STEP 3 / 4 continue the STEP 2 that sewed THIS piece (run id + piece md5 in TRIAL.json and _reinsert_state.json; refused by name otherwise); an accepted trial's body_new.brep is never renamed by a later step; the trial acceptance applies kit check's skin-record rules first (faces crossing themselves, an unmeasured depth / pair / gap, a record that is no object); skin-source and STEP 1 need the region's verdict ok, which a new source's RESTART keeps; every runner refusal is a BUILD_LOG row with rc 2 | |

**the client's rulings for this route (2026-10-06), and what each became in the kit:**
- *"Step 1 is get the perfect reinsert faces. Literally the very first thing to do."* - every skin step refuses until reinsert STEP 1
  wrote wall_caps.brep; skin-build FAILS unless its caps are those faces and every body edge a skin face owns is in it unchanged; STEP
  2's sew matches the caps both ways (L114).
- The points decide the final faces; the voxel is correct but sloppy, the original incorrect but fairly clean; the off points are the
  fix; the faces that get no point blend away; *"kill the bands"*; only the reinsert faces are exact (L116).
- *"STOP making changes based on measurements"*, *"render reviews are how you understand the model"*; the working view is the original's
  REAL wireframe over the voxel drawn TRANSPARENT (*"you are making it up"*) - the layout and the piece are judged on their frames before
  the next step (`kit rebuild judge --what layout | skin`; refused on the frames of an earlier artefact).
- Frozen is a recommendation, not a hard rule, in this process.
- *"for this edit ... it should also have a mirror check ... since it is symmetric"* - MIRROR is the card's decision at skin-network (L117).
- The changed faces are to be the SIMPLEST surface spanning clean edges (*"nearly everything is still far too lumpy"*): the route's open
  item - the agent's next pass; the build's levers for it are CTRL_MM (control spacing; 1.0 mm in the piece that went in) and LAM (fairness; 0.005) (L118).
  *(31an, 2026-10-07: the ladder is now the kit's - original surface -> flat -> smoothed fit, LAM 0.5 suggested; L121.)*

**Going back into a done edit (the client, 2026-10-06: "Will the burrito process be able to go back into an edit that has already been done and
tweak thing slightly if the outcome wasn't quite right?").** Before it is applied: any step re-runs on the job's own files (every
passing step's outputs are kept under `tags\<T>\`; a re-run layout or piece needs a new look - the judge refuses old frames). After it
is applied: a new job over the same place against the new model of record - its content IS the remade skin, which the route treats as
it treats any original (fewer, cleaner faces for the points to land on). The one risk: a fitted face that fails check(True) went in
under BOP_OK, and the next STEP 1 cuts the body with a box (a boolean) - near such a face it may fail (L100); a skin whose faces pass
check(True) is the reliable one to come back to.

**The passes that made this route (31an .. 31aw, their client rulings and measurements) and where each round stood are in the kit's development record** (31ax: history out of the method); the rules they produced are the table above and L114 onward.

# HOW IT ACTUALLY RUNS — THE SHELVED VOXEL CHAIN

The rebuild chain's first form ran on a VOXEL FIELD. Its voxel steps (arrange, arrange-m, arrange-f, blend, repair, review) and its back half (decimate,
fillholes, finish, brep, keep and the exact-plane fuse `JOIN=fuse`) are SHELVED: THE SKIN ROUTE above replaced them, and `kit rebuild` refuses every
shelved step without `--set SHELVED_OK="<why>"`. The steps stay in the kit (`kit\rebuild\rb_*.py`) so a later pass can bring one back on a recorded
reason; `kit rebuild <step> --plan` prints a step's inputs and lever defaults. The lessons L1-L113 below were learned on that chain; the rules from
them that still hold follow, and THE SKIN ROUTE's rows restate them where they apply. One of them belongs to every route: a PROTECT box (set on the
region step) holds a DESIGNED OPENING only - what counts as one is the project's ruling, PROJECT_FACTS section 6, its newest line - and never
enclosed air, which is junk and is filled (L111).

# THE RULES THAT CARRY OVER FROM THE OLD CHAIN (their lessons keep their numbers below)

Every kernel call on a body-sized shape goes out of process, one per call, through the runner (L11, L47); crop before
measuring; `check(True)` is not a gate on anything body-sized; a step can write an empty or partial result and then die
(L13, L32) — the artefact and its FINAL line are the evidence, never the exit code; a background task you stop reading
is not a task you stopped (L14); the review order is after-frames alone, judged, an overlay only to confirm coincidence
(L22, L26), and a frame that cannot see the feature gets a clip plane, never deleted (L27); a single-height section is
not a continuity check (L29); walls land in air or in the thickest clean material, never at the thinnest place (L21);
read the acceptance table, do not invent criteria (L24); audit the clocks at 1.5× (L30); no number the method
produces can detect a wrong-shaped piece — only the pictures can (L2).

# THE LESSONS — one index (`kit lessons`; `--near` before writing a new one)

Numbers are permanent. A lesson marked *retired* belonged to the S3–S7 chain (rays, cards, sheets, stitch, MARGIN);
its full text is in the kit's development record. `kit lessons` prints the next free number. (L114-L130, the skin route, are filed first below.) (L104–L113 are filed above L103: written out of order on 2026-10-01/05.)


## L114. THE REINSERT FACES COME FIRST: A PIECE THAT GOES BACK BY A SEW IS BUILT ON THE BODY'S OWN SECTION FACES FROM ITS FIRST BUILD (2026-10-06).
the agent's skin builds SP3-SP9 made their wall caps from the voxel (triangles within 0.15 mm of a wall plane); the probe SP10 showed 4 of the
11 caps were voxel corner artefacts with no body face behind them and 7 wall junctions 0.1-2.6 mm off the body's vertices - and sp9n's
self-intersecting face was a cap the voxel made. the client: *"Step 1 is get the perfect reinsert faces. Literally the very first thing to
do."* The restart on `wall_caps.brep` (the 7 body faces; each of their 74 edges owned by the skin face of the original face it bounds,
or a box corner two caps share) closed the shell WITHOUT sewing and went in with seam 0. The rule, generic: whatever a piece must meet
exactly is built FIRST and every later step builds on it; a check that it is there runs on every build, never at the join.

## L115. A SLOPPY ORIGINAL CANNOT BE TRIMMED: ITS FACES DO NOT MEET - LAY THE SKIN OUT ON THE VOXEL AND BORROW THE ORIGINAL'S SURFACES (2026-10-06).
SP2 laid the changed regions' outlines on the original faces as exact edges: every region had crossings that could not be made - faces
0.10-0.14 mm apart with no edge between them (the slits the voxel closed), faces touching with no shared edge. The original's topology
is the junk the burrito removes; its surfaces are good. The skin's faces are the voxel's patches; a patch that lies on an original face
keeps that face's surface.

## L116. THE POINTS DECIDE THE FACES - NOT LABELS, NOT WHOLE FACES, NOT EVERY VERTEX (2026-10-06).
Voxel labels (nearest sample + smoothing + sliver merges) gave ragged borders off the original's edges (SP3-SP7: "you picked
incorrectly for points that build faces"); whole original faces were too coarse (SP5: 113 of 135 "changed" - a fillet band drags in
the big faces beside it); projecting all 59k vertices ran past 720 s. About 1000 points, each given to the face it lies on (SP7d, 18 s),
decide which faces stay; the flood from them, with the crisp original edges as barriers, makes the layout (SP8). (the client, 2026-10-07: the 1000 was a
SUGGESTION - "the agent attempted to use over 40k points and I simply wanted that pulled down to something reasonable": NPTS is the agent's,
1000 to start, held to 100-5000 by LEVER_RANGE; the file is named points1000.json whatever the count.) the client: *"about 1000
points would be more than enough to confirm simple face edits"*.

## L117. A SYMMETRIC EDIT IS MIRROR-CHECKED: LAYOUTS MADE SIDE BY SIDE ON AN ASYMMETRIC VOXEL DIVERGE (2026-10-06).
Face4600 - the strip between the crown top and the slot mouth on one side - had no partner on the other: the layout ran on each side
independently, on a voxel whose sloppiness is not symmetric, and absorbed the strip into its neighbours there. the client: a mirror check, of the
layout before any face is fitted and of the piece after. `kit rebuild skin-mirror`; the card's MIRROR at skin-network. 31at (2026-10-07): a face's
direction in the PIECE check is its area-weighted normal, as in the layout check - the normal where the surface is nearest the centre of
mass came from one arm of a U spanning the plane (R4 skin 2 sk5a face 12) and refused a face that is its own mirror.

## L118. THE SIMPLIFYING STEP: A CHANGED FACE IS THE SIMPLEST SURFACE SPANNING CLEAN EDGES, NOT A FIT THAT FOLLOWS THE VOXEL (2026-10-06).
The changed faces were least-squares B-splines at ~1 mm control spacing with light fairness, their edges from the voxel's label
borders: they followed the voxel's sloppiness - the client, *"nearly everything is still far too lumpy"*. The fit is judged by the grazing-light
pictures (skin-look), never by a misfit number (the client: *"STOP making changes based on measurements"*); planes, cylinders and the original's
own surfaces where a face reads as one. Open: the agent's next pass.

## L119. NO FILE OF AN EARLIER BUILD IS READ AS THIS ONE'S (2026-10-06).
A stale `free_c.brep` drew false free edges over a closed piece; the morning's seam frames stayed in review_body\ after a STEP 4 with no
seam; the job's "copy patches.* to patches_sp8.* the first time" made a re-run labels step invisible to the rim. Every skin step now
clears or names its own outputs (skin-build removes the old piece and shell first; skin-look ignores an older free_c.brep; STEP 4 with
no seam face removes the old seam pictures; skin-labels writes patches_labels.*, skin-rim always reads them).

## L120. THREE FAILED TRIES AT ONE SPOT SEND THE AGENT BACK TO THE POINTS THERE - SUCCESS LIES IN PICKING THE RIGHT POINTS (2026-10-07).
R4 skin 1 spent 14 layout rungs (v8-v16, ~80 min) on one 3 mm corner, each patching the last; the corner's own original face had got no point
at the 2.8 mm grid, so the layout had no face for it and the rim gave its wall edge to the neighbours. the client: *"Yes to 3 tries, but I want the agent
to be immediately forced into going back to the start of point selection off of the wireframe + voxel transparent overlay because everything
about success lies is picking the right points to build faces off of."* and *"Unlock should be per spot, if 80% of the point selections were
correct it should not be forced to repick those, only the ones that failed."* The runner counts failed tries PER SPOT - a box where an artefact
failed: the faces a move/redo names (`judge ... --face <n>` / `--spot <box>`, refused without one), the second reviewer's blocker faces, a
mirror check's unpaired faces, a failed build's open edges; a box at least half inside another is the same spot; each artefact counts once per
spot; a spot a later verdict does not name passed and starts again. Three consecutive at one spot lock it: every step after skin-points is
refused until skin-points - which KEEPS every point outside the locked spots - picks again inside them (PTS_BOX / PTS_DROP held inside them,
two iso close-ups of each on the wireframe + transparent voxel) and `kit rebuild judge --what points` sees the points there changed. FRAME_PTS
asks for every original face the reinsert faces' edges meet. Generic: when one place keeps failing, its faces are wrong, and the faces are the
points; the places that work keep theirs.
*(31br G4c addendum, 2026-10-29: the agent's d13 - the d10-d12 builds had failed at ONE face's span (the agent's own split piece facing two ways - a wires failure, charged at the
points before 31br G4b) and the free-edge spots they left were locked; two of them, 4 mm boxes on a free edge over a flat face's large triangles, held NO source-triangle
centroid, and the points step picks only centroids - so no lever could change their points, `judge --what points` could never unlock them and every later step was refused
for good (the agent: 'a kit dead end'). The rule: a points spot needs a point to pick; a spot with none is not a points spot - never locked, and a standing lock on one released with
the reason wherever the lock is read. Generic: a lock whose release condition cannot be met by any action of the agent is a defect of the lock, not a task for the agent -
the kit checks that the way out exists where it makes the lock.)*

## L121. THE FACE LADDER: THE ORIGINAL'S SURFACE, THEN FLAT, THEN A SMOOTHED FIT - NEVER A FIT THAT FOLLOWS THE VOXEL (2026-10-07).
the client: *"the process ... was only missing focus on simplifying the geometry instead of following the voxel improvements so closely"*; *"original to
flat face to smoothed fit makes sense"*. Rung 1 (the layout, skin-labels / skin-rim): a face whose points all lie on one original face IS that
face (kind orig; skin-rim fits it instead if it would own another original face's wall edge). Rung 2 (skin-build PLANE): a changed face whose voxel
is flat is a bounded plane (the agent skB3c: 9 planes, 60/60 faces valid). Rung 3: the rest fitted with strong fairness - LAM 0.5 (skB2q-u: 59/59
faces valid where LAM 0.005 folded) - the voxel a weak guide. Measured and dropped: coarse control grids (CTRL_MM 2.5 / 4: edges missed by up
to 2 mm), filled faces (makeFilledFace: edges missed by 1-46 mm; access violations with an initial surface), and the extruded wall section
the agent used for the keel end (the client: *"The process does not use extruded walls at all anymore"* - the walls are the body's own faces, the rest comes
from points). Open: R4 skin 1's crumpled fitted faces (the aft plate, the wing-root pockets) - their points and their borders.

## L122. THE WHOLE PIECE FROM EVERY SIDE, TWO ISO VIEWS PER FITTED FACE, THE SECOND REVIEWER BEFORE THE AGENT - LARGEST DEFECT FIRST (2026-10-07).
R4 skin 1's piece passed skin-look (views from above, grazing close-ups at the changed REGIONS) and its six lead frames; six cad-reviewers then
failed all 26 sweep frames - crumpled faces under the spine's aft end, seen from below. The 862 mm2 aft plate face had been flagged at 18:03, made
valid at 18:46 and never looked at from below; the next 80 minutes went to a 3 mm corner the piece mirror gate had named. skin-look now draws the
whole piece from above AND below and every fitted face in two iso views under a side light (the client: *"not straight at it, that hides
ripples/lumps"*); `kit rebuild second` shards the frames for one cad-reviewer each and the agent's verdict on a piece waits for them, every
time; their defects come back ranked by size and the largest is fixed first.
*(31br L1 addendum, 2026-10-29: 'before the agent' means before the agent's OK. the agent's d13 build printed check(True) failures on 9 faces and the kit's next line sent it to the 74-frame full look and
the two reviewers (the client: 'Why are you running a full review to get ready to insert into the model if you know it has issues?'); then a REDO on the two real defects was refused for want of that
review. Now the check(True) faces get a TARGETED look first (`skin-look FACES=<ids>`, seconds), a REDO / MOVE on an opened frame is recorded without the second review, the full look is refused
while a flagged face has no look, and an OK still needs the complete review free of blockers. Generic: an expensive review is spent on a piece the cheap checks have passed, never on one they
have already failed; the cheapest frame that shows the known defect is the one to judge it on.)*

## L123. A SYMMETRIC EDIT'S LAYOUT IS MADE ON ONE SIDE AND MIRRORED - ACROSS ANY PLANE, IN A WINDOW THAT IS ITS OWN MIRROR (2026-10-07).
R4 skin 1 B1: OPEN_MM 0.6 made the two sides diverge more (7 unpaired); the agent's mirrored layout (v2-v5: the plane splits the sides, a face that
truly spans it stays one, a sliver crossing makes a pair, a slave triangle takes the like-facing master at its mirror point) passed the mirror
check; v9 gave each twin the mirror of its master's original face. In the kit (sk_lib.mirror_layout) with MIRROR "x 0" or "nx ny nz c", the
master side the one with more faces (a missing face is the defect), refused on a window that is not its own mirror. Not ported: the wrap split
(v8 - it dragged the keel's seam), the exact relabel (v14 - specks), the straddle carve and KEEP_ORIG (v10, v16 - hand-picked face numbers),
the crease snap and same-face merges (v12, v13 - moved nothing).

## L124. A LEVER'S VALUE IS A SUGGESTION; ONLY A KNOWN-WRONG RANGE REFUSES (2026-10-07).
the client: *"default settings should be suggestions only, not requirements. Possibly a min/max enforcement rule at most."* The runner prints its
values as `suggested` and takes any other the agent sets (printed beside the suggestion, recorded in the env file); LEVER_RANGE refuses only
SEAM_MAX / FRAME_TOL over 0.15 (the client's seam ceiling), NPTS outside 100-5000, a negative LAM, a CTRL_MM under 0.05. A hard-coded tolerance that
refused good builds (skin-build's 1e-6 frame check: five edges 0.008-0.015 mm off sewed with seam 0) became a lever with a suggestion.

## L125. A NUMBER NEVER OVERTURNS A PICTURE - AND REACHING FOR ONE FIRST IS A STRIKE (2026-10-07).
the client, with the agent live: *"the agent is editing and ALWAYS jumps to measurements before renders. Find a way to punish it"*; *"It consistently gets to a good
result off of renders + changes, makes a measurement that it arbitrarily decides is a bad measurement with no reasoning as to why, and then
undoes correct work. It has to stop."* The guard (hooks\lookgate.py) makes three things strikes - a measurement with no picture of its
subject, a lever build right after a measurement with no picture since, an attempt to undo a layout or piece judged ok on its pictures
(kit_rebuild: skin-labels / skin-rim / skin-build refuse to overwrite a standing ok; a redo of it needs --frame, a picture opened after the
ok and after the last measurement that shows what is wrong). A strike goes on claude_code\DUMDUM.md and locks the session until the agent
says "I'm a silly dum dum" to the client; a measurement then needs more pictures (the penance) and always a # SAW and a # WHY. Generic: the
pictures decide; a number may be asked for, with its reason, only to answer what a picture cannot.

## L126. BUILD IT AND LOOK AT THE REAL THING - A CHEAP LOOK IN THE LOOP, THE FULL LOOK ONCE, THE REAL MODEL BEFORE THE ACCEPTANCE (2026-10-07).
R4 skin 2: the ~40-face piece built in ~10 s; skin-look's full look took 290 s for 72 frames and ran on pieces wrong in its first frame; between a
build and its look the agent ran face probes, wire probes, section tools, four lever trials chosen from printed tolerances and a surface-sampling render -
checks on invented intermediates, none cheaper than building and looking; and the reinsert's gates (the second reviewer, then the mirror) made the
real model in the body the last thing anyone saw. the client: *"Sometimes building the model and getting true renders is the right answer"*; *"mirror
checks should pass before creating a real model"*. The runner now: skin-look QUICK (8 frames) in the loop and FULL once for the second reviewer;
`reinsert --set TRIAL="<why>"` sews a piece not yet accepted into the body as a look (its mirror check first) - body_trial.brep, never body_new.brep,
its STEP 3 / 4 refused to a real run, `judge --what trial` redo / move only; sk_build prints no deviations. Generic: the cheapest true picture of
the real artefact beats any picture or number of an intermediate; spend the expensive look once, when the cheap ones say it is right.

## L127. THE WIREFRAME IS DECIDED, NOT TRACED: FEATURES FIRST, A REASON FOR EVERY LINE, LABELS FROM THE FINISHED CURVE (2026-10-07).
R4 skin 2: 54 skin faces (one per original face that got a point) became 32 when the agent named each original face's feature from numbered
pictures (spine, vane, support - the client: *"Think SIMPLE"*); the network, 155 edges for 57 faces in skin 1 (skB4c), was 64 for 32 (sk3j: 43 straight,
21 arcs, none multi-span) once every line's kind was decided with a reason and straight feature edges were railed between the reinsert faces' corners; the client: *"The wireframe simplifying is looking
good"*, then *"the wire frame labelling and simplifying priority was a good addition to the process"*. Two failures on the way: a line laid back
onto the voxel after it was simplified (ON_VOX - "that follow the voxel's original design lines IS WRONG"), and frames coloured by the rung chosen
FIRST while later steps bent the curve (teal "straight" lines drawn bent - the client caught it). Rules: decide the line, then draw it once; nothing moves
it after (a junction moves before); a picture's legend is computed from what it draws (L119 one level down). In the kit (31as - the client: "they do not
rely on a step 4 finish to make it into the kit"): skin-features (after skin-labels) and skin-wires (after skin-frame), the wires judged before
skin-build; generic - the master side and the rails follow skin-labels' mirror decision on any plane, or none.

## L128. A RE-SPLIT IS NOT A FIX: THE LAYOUT'S SECTION-WIDE SETTINGS ARE FIXED AT ITS FIRST OK, AND THREE ROUNDS SEND YOU BACK TO THE POINTS (2026-10-07).
R4 skin 2, 15:07-16:29: four layout redos, each at a different place (the keel end, the fin's front edge, the fore end's loops, the fore plate top),
each answered by a section-wide lever (BAND, OPEN_MM) that fixed one place and moved faces elsewhere - six re-splits, ~70 min, no piece. The per-spot
restart (L120) counts tries at ONE place, so it never fired. the client: *"It decided to split a section instead of going back to point picking and then it
looped in infinite failure"*; *"Yes to changing it through points, it should still be able to have the lines that build it tweaked without selecting
new points"*. The kit: the first layout judged ok locks skin-labels' / skin-features' / skin-rim's section-wide levers (skin\LAYOUT_LOCK.json - read
from the run that made the live layout, by md5; a step not on record is said, never guessed); five layout redos (ROUNDS_MAX, 31bk; was three) without a skin-build that passes lock
every place they named. Generic: a setting that changes the whole section is decided once; after that the places are fixed where they are.

## L129. FEWER PICTURES IN THE LOOP, NEVER NONE - AND EVERY PICTURE FROM THE KIT (2026-10-07).
One re-split was ~11.5 min, ~85 % pictures (skin-rim 165 s, skin-labels 160, skin-wires 96 ...). the client: *"Yes to less picture but no to having any single
step without them if it has them today. That is the part of the process that stops the measurement hallucinations."* PICS=quick (the runner's
suggestion in the loop): four orbits above, two below, close-ups where the last redo pointed; the full set once before a layout or a wireframe is judged
ok. The render study found the shredded colours were the drawing, not the model - the layout views colour the voxel triangle by triangle, look_at
coloured its subject the same way, job scripts sampled untrimmed surfaces. the client: *"How renders get generated needs to be locked down, same idea as how the
targeting is"*; *"only refuse unless it is announced in the chat session why it has to be different ... 'Are you sure?'"*. The kit: a job script's own
pictures are refused until announced to the client, then "Are you sure?", then allowed; look_at draws one colour and outlines the subject's box; every layout
picture says its borders are the voxel's; the judge's pictures are the job's own (jobs\<J>\skin\review\).

## L130. A DECISION SURVIVES A RENUMBERING, AND A DECIDED LINE IS NOT BENT TO KEEP A SURFACE (2026-10-07).
LINES was keyed by chain number and skin-network renumbers every chain when a face changes - 60-70 reasoned decisions lost per re-split (the agent's
job_skin_lines_remap.py carried them by hand). And a decided line bordering a kept-original face was re-laid onto that surface with unlimited poles
(pw4: 11-30 poles, magenta; sk8a: short ones crossed and fell back to the raw border - three faces with self-intersecting wires). the client: *"Yes keep what is
correct"*; *"Yes to keep original faces when it makes sense to"*. The kit: the numbers in LINES are the last WIRE_* pictures'; after a re-split each new
chain takes the decision of the old one between the same two features, nearest middle within 3 mm (skin\LINES_carried.json), and only new lines are
listed; a decided line on an original face is refitted as ONE cubic span on it - kept within ON_TOL, else the face (and its twin) leaves its original
surface for the next rung, and the step says which and why. Generic: the agent's reasoning is the asset; the kit never discards it or distorts it.

## L131. A CHANGED FACE IS THE SURFACE ITS EDGES SPAN - A SAMPLED GRID RINGS, THE SIDES AS THE BORDER DO NOT (2026-10-08).
Every defect of the trial tr5b4 was in a fitted face (26 of the piece's 34 skin faces were 70x70-pole fits to the voxel, 0 flat). the client: *"No to voxel
smoothing"*; *"More lines should be added as needed to give the face the required shape"*. The face is now spanned by its decided edges the way CAD draws
one: a plane when the edges allow it, else the Coons patch of its four sides. The first form interpolated a sampled Coons grid with a C2 surface: a corner
or a joint inside a side rang through the interpolation - edges 0.1-0.44 mm off their faces on every face with a kink inside a side, 27 faces failing,
the solid invalid; a 4-edge face was exact. The B-spline Coons patch (the two ruled surfaces minus the bilinear one on one knot grid) has the sides AS its
border: every face within 0.004 mm of its edges. Two more traps on the way: `join` concatenates PARAMETER ranges (a 2 mm piece after a 14 mm one owned
half the side and sheared the strip into a fold - the pieces are scaled to arc length first), and a concave outline folds any Coons patch - that face is a
PLATE (the smoothest height field over its own plane, trimmed by its wire); one that folds and wraps past 80 deg is split with a wire. The voxel decides
the points and the lines; nothing of it is in a surface. Generic: build a face from its edges exactly, never from a sampled copy of them.

## L132. DEPTH, SPLITS AND FILLETS ARE WIRE DECISIONS, NOT LAYOUT CHANGES (2026-10-08).
the client's sketch: a quad with three cross curves and a centre line - *"More lines should be added as needed"*; *"If splitting faces is needed add a wire to the
wireframe"*; *"Merge smooth preferred with fallback to stitch"*. A GUIDE line inside a face pulls its surface through it (merge smooth); a line the surface
cannot reach becomes a SPLIT (stitch): the face is two surfaces sharing it. A split ends on the face's border and cuts the border line there for BOTH faces -
never inside a wall edge (the caps are the body's, L114): the keel end (the trial's lump: one face wrapping 90 deg) became three faces, side / tip strip /
side, by two LINE wires. A FILLET is a line the kernel rounds on the sewn solid - measured on a section's B-spline faces it mostly fails (R 1.5 / 0.8 / 0.4
invalid on the support's foot; one short line valid at R 0.4) and a failure leaves the edge sharp, said. the agent's six re-splits of 10-07 were all answers to
shapes a wire now gives. Generic: the layout decides WHICH faces; the wires decide their shape - a face that needs a different shape gets a line, not a
re-split.

## L133. TWO COMMANDS, THREE PICTURE SETS - AND A PICTURE DRAWN FROM THE SAME INPUTS IS NOT DRAWN AGAIN (2026-10-08).
the client: *"After mirror there should be a picture set. So 2 commands, 3 picture sets. If pictures have been taken of the starting area then no need to repeat
taking those images - confirm with hit/miss picture type."* `kit rebuild skin-layout` (rim + mirror) and `kit rebuild skin-lines` (network + frame + wires);
every frame carries the md5 of what it draws (`.pictures.json`): a HIT stays, a MISS is drawn - skin-rim on an unchanged layout 62 s -> 13 s. The 10-07
day spent ~115 min in picture steps against 3 min of builds; most of those pictures showed what the last ones had. Generic: a picture is a function of
its inputs - key it by them.

## L134. THE TRIAL IS THE ACCEPTANCE: THE REAL MODEL, TWO REVIEWERS, THEN NOTHING IS REBUILT OR RE-SEWN (2026-10-08).
31ar made the trial a look that could never accept; the formal path (the 72-frame full look, the second reviewer on the piece, the mirror, a REAL STEP 2-4)
would have rebuilt what the trial had already sewn. the client: *"If a trial passes, do not rebuild it, do not reinsert it. Yes to orbit, 2 reviewers on a
sectioned model for before and after. yes to real model"*; *"passing criteria is my judgement not if they agree"*. Two cad-reviewers read review-body's
frames of the real model (the orbit, the region close-ups, the old-vs-new stations); the agent opens every frame; `judge --what trial ok` promotes the
trial's body by rename - the piece is judged ok by that, review_body\ is the COMPLETE review, and a skin-build or STEP 2 of the same piece is refused.
the client decides from the pictures. Generic: when the cheapest true picture is of the real artefact, the acceptance is made on it, and the artefact is kept as
it was judged.

## L135. THE CONFESSION IS SAID WHERE the client READS - THE AGENT'S MESSAGE, NEVER A TOOL CALL (2026-10-08).
31aq took an `echo "I'm a silly dum dum ..."` as the confession and 31au showed strikes as the hook's systemMessage; on the client's machine neither
reached them - strike 7 (12:38:29) was "confessed" by an echo ten seconds later and the client saw nothing ("The kit is not live reporting that it's a
dum dum"). The one channel the client reads is the agent's message text. The guard now reads the session transcript (the hook input's transcript_path)
at every tool call while a strike is owed and unlocks only when an assistant TEXT block written after the strike holds the sentence with that
strike's number; an echo is refused as NOT SAID; no transcript readable -> the echo stands (fail-open). Generic: a control that must reach the
human is checked where the human looks, not where the agent is convenient.

## L136. NOTHING MOVES FORWARD ON A PIECE ITS OWN PICTURES SHOW WRONG - THE LOOK IS JUDGED, EVERY FRAME OPENED (2026-10-08).
the agent built sn5 / sn6, ran the quick look, and went on to the mirror check and a trial with the pictures showing the pocket wrong (the client: "moving to
next steps when it knows the results are incorrect rather than reworking the edit"). The runner now wants `judge --what look` on the quick look's
frames - every one opened (the look gate's record), ok or redo with the place - before skin-mirror WHAT=piece or a trial; a redo is a try at
that spot and sends the agent to the lines / the points there. Generic: a step's own pictures are a gate on the next step, not a courtesy.

## L137. THE FACE IS A NURBS FILL THROUGH ITS WIRES FIRST; THE WIRES ARE DECIDED, NEVER TRACED (2026-10-08).
the agent's NURBS prototype (job_skin_build_nurbs.py, sn1-sn7): a plate fill through points on every edge and added line, approximated to one B-spline,
does not overshoot the way the height-field plate did (sk12a's towers and horns gone in sn6) and is only as good as what holds the inside of the
face - guides TRACED on the voxel put the voxel's lumps into the vane undersides (sn6 wavy). the client: "prioritize using NURBS. Those work much better in
most cases"; "the wireframe should NOT follow the voxel. That process step is now defined as skipped". The kit: NURBS first in the ladder (rim
0.10 as sn6; 0.02 on a face that owns a wall edge - sn3 / sn5 broke the frame check; NURBS_SKIP for a face the pictures show wavy as a fill),
Coons / plate only when the fill cannot hold its rim. (31az refused "trace": true; 31bb draws it again - with the voxel shelved a trace follows
the ORIGINAL, which is kept geometry: the client, "it's good they were traced that was geometry that was wanted to be kept".) Generic: the surface is the
smoothest thing through DECIDED curves; a curve traced on the design surface is decided, a curve traced on a measurement of it is not.

## L138. THE VOXEL FIELD IS SHELVED - THE SKIN ROUTE STARTS FROM THE B-REP'S OWN FACES; THE PICK AND THE WIREFRAME DO THE REST (2026-10-08).
the client: "the entire voxel step is now getting skipped. shelve it in the kit, as it may be used another time. Instead of voxel the wireframe redraw
will handle all geometry corrections." Six steps (arrange, arrange-m, arrange-f, blend, repair, review) refuse without SHELVED_OK. `kit rebuild
skin-source` tessellates the edit region's content ONCE (MeshPart 0.05 mm / 5 deg, one segment per face: the original face of every triangle,
mapped to the body's face indices - a section: 142 faces, 135 on body faces + 7 walls, 18,834 triangles, 20 s) into source.stl, the mesh every
skin step reads until content.brep changes. the kit maintainer's first cut (31ba) ran the voxel-era flood on that mesh; the client: "tessellation here doesn't seem
necessary ... The border junctions are in the brep". 31bb: the layout comes from the face index - a face with a point keeps its own triangles
(every border a B-rep edge, every junction a B-rep vertex), a face with no point is absorbed whole by its neighbour (skin-points is the pick of
what is kept: NPTS / PTS_BOX / PTS_DROP / FRAME_PTS), the wireframe is where the geometry is corrected (a line left alone keeps its faces exactly;
a redrawn line re-spans them, NURBS first; a traced line follows the original; a moved junction is a rail or a coordinate end), the frame is the
only lock. skin-regions writes the mesh record only (no pictures - the client does not need them); skin-edges compares nothing. NOT YET RUN AS A CHAIN
(the agent's restart of a section is the test). Generic: the carrier of a layout is the design's own faces; a mesh is only the picture and the pick.

## L139. A B-REP FACE KEEPS ITS HOLES; A NEW SOURCE IS A RESTART; A CONFESSION ENDS THE TURN (2026-10-08, the agent's restart of a section).
the agent's first run on the B-rep source (31bb) found four things in an hour, all caught by the kit's own gates or by the client: (1) the voxel-era HOLE CUT
split the fore vane underside - one connected B-rep face pierced by the stems - into ~40 layout faces (the client: "I don't think those features in the
vane are real ... see if your process is bugged"); the cut was for flood faces round an island; a B-rep face keeps its holes and skin-build makes
it with its inner wires. (2) skin-labels on the new source was refused as an undo of the VOXEL layout's ok and struck; the voxel LAYOUT_LOCK
still pinned the levers; RESTART.json still held the voxel trials' tries - a new source mesh now supersedes every verdict, lock and try (the client:
"ignore the locks. nothing is good yet"). (3) the confession written mid-turn unlocked nothing: the desktop app writes message text to the
transcript at the turn's END - the agent writes the sentence and ends the turn; the Stop hook lifts the lock; and the transcript is walked
backwards to the strike (a 400 KB tail missed a sentence behind two picture Reads). (4) points on big flat faces read OFF because their face's
samples were not among the 24 nearest centroids - on a B-rep source a point's face is its source triangle's. Generic: every gate that keyed on
"the voxel" had to be asked again on the B-rep; the records of one route are not the next route's truth.

## L140. A CHAIN IS ITS OWN TWIN ONLY WHEN ITS MIRROR LIES ON IT; A DESIGN CARRIED TO A NEW LAYOUT IS CHECKED, NOT TRUSTED (2026-10-08, the agent's b2).
On the first wires of the B-rep layout every WIRE frame showed ~20 mm circles across the spine top: a face whose mirror twin had been absorbed
into another survivor in skin-features had no twin, so the mirror step took its border as "its own twin" and averaged it with its mirror image -
pulled from x 7.75 onto the plane. The same run crashed on RAILS written for the voxel layout's corner numbers (two corners now one point),
applied 38 chain decisions carried by position to chains they did not fit (carried arcs became circles), and tried to put `_add` guides on the
old layout's face numbers. Now: own-twin only when the mirror image is within SELF_MM of the chain, else ONE-SIDED and said; twins re-paired
from the merged sets; a rail with one point refused; a carried LINE / ARC further than CARRY_FIT from its chain goes TO DECIDE; `_add` /
`_fillets` of another numbering go TO DECIDE. Generic: a record keyed by numbers (corners, chains, faces) is only as good as the numbering it
was written on; crossing a re-layout, every carried item is checked against the new geometry or handed back to the agent.

## L141. A FILLET NEEDS ROOM - THE KERNEL AND THE LINES FAIL FOR THE SAME REASON, AND THE ROOM IS MADE BY FILLING THE GAP FIRST; A FACE FRAME IS A VIEW THAT SEES THE FACE (2026-10-12/13, kit 31bl).
the agent's b15: six builds could not round the vane-to-spine crease (the kernel StdFail at R 2-3; the fillet by lines folded the holed spine underside). Measured on
a scratch copy: the crease runs 1.5 mm from the slot hole's rim, and a fillet of radius R reaches t = R tan(beta / 2) onto each face (beta the angle between the
faces' normals; 90 deg -> t = R, this 135 deg crease -> t = 2.4 R) - R 2 wanted 4.8 mm of face where 1.5 mm existed. At the R that fits (0.45) the kernel's
fillet MADE a valid solid and the kit had refused its own result (a compound round the one solid read as "not a solid"); the lines route, rebuilt as an arc of
R swept along the crease into one NURBS surface with a cap at each junction, makes the same blend. R33's success had no fillet at all: the voxel closing (R 3)
FILLED the vane-root gaps and the hole, and the faces were fitted over the filled shape - the room came first. The look that could not show the blend (the client:
"rendering a bottom feature from the top") was fixed by scoring the face frame's camera corners by the share of the face they SEE; a face no corner sees from
either side is covered by another within a millimetre - a slit of air or an enclosed pocket, which is what requirement 2 says to fill. Generic: before a blend
is asked for, the width beside the crease decides the radius (the kit names it); a gap or a hole beside a root is filled or moved first, then the blend fits by
any route; the acceptance test of a kernel result reads the result it got, not the type it expected; and a picture of a face is one the camera can see it in.

*(31bm addendum, 2026-10-13: the agent's ten builds asked for blends whose creases END where a short border leaves the junction - the kernel's ball had nowhere to run
out, the lines' caps folded the neighbour. Measured on b20: the kernel fails on NURBS fills at EVERY radius, single or grouped with the end borders; so the
lines blend now TAPERS to the junction (R to nothing over 3 t) where its offset line meets no border - a lens, no cap, no cut - and the junction point stays
sharp. And the crease is measured AS BUILT: two NURBS fills met at 25 deg where the original had a 90 deg wall - the fillet the agent asked for had almost no corner
to round. Generic: a blend is defined on the surfaces the ladder BUILT, not on the original's; where the room ends, the radius ends with it.)*

## L142. ONE MESH, ONE VIEW, EVERY FRAME JUDGED BEFORE IT IS DRAWN - A DEFECTIVE PICTURE IS NO EVIDENCE (2026-10-13/15, kit 31bn).
the agent's b18-b20 blend work was reasoned from torn and faceted frames (look_at: translucent overlapping sheets, a saw-tooth edge along the spine side;
skin-look: coarse facets on NURBS faces read as lumps), the second time in two days, with CONTRACT's render rule in front of it; the client: "Why are render views
tessellated and torn again? ... you are missing gates and hooks and can't be trusted to create renders correctly", then "gate/hook whatever has to be
done. The render creation method must be controlled. Instructions are not good enough. Only good renders allow for good work." Measured: every piece
picture tessellated the solid FACE BY FACE (Part.tessellate per face) - on the closed 59-face piece that leaves 6130 edges where two faces' meshes do not
share their points (measured by the gap in fix 4: 6108 closed within 0.02 mm, 22 open by up to 0.024 mm), look_at clipped triangles by centroid into one
translucent colour (the shards and the see-through sheets), and the painter's-order renderer painted hidden faces over visible ones; MeshPart on the WHOLE
shape with Segments=True leaves no open edge on the piece (393 k triangles at 0.02 mm / 0.05 rad; on the 4765-face model of record 251 closed T-junction
seams and 4 real gaps along one wall) and the reworked renderer - a true z-buffer, smooth shading from the surface normals within each face - draws it in
2-3 s a frame against 10 s for the old one. The kit now has ONE render method for a piece - the piece view: the one conforming mesh, made once and cached, drawn
opaque with a tint per face and depth-tested lines; and the mesh is judged BEFORE it is drawn - cracks between faces, the realized deflections of its
triangles against the surfaces they stand for - and a mesh that fails stamps every frame with a red RENDER DEFECTIVE band, a crack stamps the frames whose box holds it (the model of record's region.brep
meshes with 251 closed seams and 4 real gaps of 0.6-1.1 mm along one wall: a look at the vane root 40 mm away is sound, a look framed on that wall is not),
the record says so, and the judge and the look gate refuse it; the judge also refuses a look with no mesh record at all (one drawn before the piece view). Fix 4 (an Opus review of all 90 frames and the code,
2026-10-15): a true z-buffer in place of the painter's order (hidden faces had been painted over visible ones), smooth shading from the surface normals within each face
(flat facets read as crumple), the crack rule by the gap (MeshPart leaves T-junction seams 1e-4..1e-3 mm apart on a valid solid - look_at on the model of record had
been stamped DEFECTIVE on 255 of them), the free edges from the piece itself with a camera that sees them, every caption wrapped to the frame. The one real finding on the way: a facet statistic cannot tell a coarse mesh from a true crease inside a face (a Coons C0 line, a
tapered blend's rows) - the defect is measured against the SURFACE, never against the mesh itself; and the spine top really ripples 0.3 deg a sample
(a 174 x 2-pole B-spline) - a fine conforming mesh shows the geometry, a coarse one hides it. Generic: a picture that is evidence is made one way, from
a mesh that is proved to stand for the geometry it draws; the proof is on the frame and in its record, and a gate reads the record - an instruction to
"say so and re-render" is not a control (a recorded process failure).

*(fix 5g addendum, 2026-10-15: a face two bodies share is seen in no correct picture of both - the body's section on an edit region's wall is covered from outside by the body and from inside by the content, so the red cut faces the region orbit promised since 31ai were only ever visible through the old renderer's gaps and painter's-order errors. The cut is shown where it is visible by construction: on the content alone, its section faces red. And a picture derived from a judged mesh by a drawing operation (a trim, a cut) is judged AGAIN as drawn - sk_lib.cut_quality: an open edge on no cut plane and not on the source's rim is a crack of the picture; the uncut meshes' clean line had passed b20t7's ragged rim.)*

## L143. A BLEND IS DECIDED FROM THE MESH IT SITS ON, SWEPT ALONG ONE SMOOTH CREASE, AND A SURFACE IS PROJECTED ONTO ONLY WHERE IT REACHES (2026-10-15, kit 31bo).
the agent's b20 lines blend read a mirror pair opposite (116 concave, its twin 30 convex: the -x blend into the material, the shell open) because the sense came from
ONE face's eight nearest triangle centroids against the other's normal - and the pair is sorted by face id, so the twin's probe face was the coarse 1092 mm2
spine face whose centroids lie millimetres from the crease. The sense is now the mesh's own signed dihedral along the shared border (the same from either face
and under a reflection), with the two faces' material directions as the fallback and a refusal by name when neither decides. Two more things the keel-root
fillet taught: the offset lines were WAVY (0.36 mm second differences; every offset point inherited the jump of the per-sample mesh normals - smoothed along
the crease over FIL_SMOOTH_MM, the neighbours' fills hold their rims again) and a V-SHAPED crease cannot be swept (round its corner the inner face's offset
line crosses itself and the blend folds; the kernel's fillet fails there for the same reason) - a corner inside a crease, its tangent turning over
CREASE_TURN_MAX within 1.5 mm, refuses the fillet with the corner named: make it a junction (a split or a line ending there) and decide the fillet per leg.
And a split that ends anywhere on a fillet's crease (the agent's keel split at the apex) moves to the strip's border, the offset line cut there, the piece cutter
waiting for the piece that holds both its ends. On the wires (the agent's b13): a face that had absorbed a strip did not REACH its new border on its own surface,
and projecting the border onto both surfaces slid it along the surface's domain edge into a hairpin; now each original surface is asked whether it reaches
the border (the median distance of the raw border's segments within JMOVE_MAX) and only those that do are projected onto; the "original edge" path only
when the border's points lie on that edge (its midpoint alone had decided), and in every branch a point the surface or the edge does not reach within
JMOVE_MAX stays on the layout's border, said (a mixed border - half on the shared edge, half along an absorbed strip - is moved where it is on the edge and
left where it is not); and every chain's deviation from its own mesh border is on record - measured
against the border's SEGMENTS, not its vertices: the first form read a chain lying exactly on one 13.78 mm mesh edge as 6.89 mm off, and a fix was written
on that reading before the probe (a recorded process failure). Generic: a construction that reads geometry from a mesh reads it the same from every side, a
sweep follows one smooth curve, a projection is a decision the target must deserve - said where it is refused - and a new instrument's first surprising
reading is checked against the thing itself before anything is built on it.

*(31bp addendum, 2026-10-15: the corner refusal's way out - "make the corner a junction and decide the fillet per leg" - was a sentence, not a kit function: a `_fillets` entry
named a chain and the lines pass swept the WHOLE network chain whatever splits had cut it (the agent's b21: the keel split ends at 54's apex, the line is cut there, and the
two legs had no name). Now "leg": "all" | <n> on the entry: each piece between the line's junctions and the split ends on it is swept as its own crease, the blend
tapering to nothing at the split end, each leg held and merged under its own key. Generic: when the kit tells the agent a way out, the way out is a kit function with
a name in the record, or the refusal is a dead end dressed as advice.)*

*(31bp addendum 2, 2026-10-16: THE CHAIN BLEND. A foot blended by several lines was several lenses - every blend by lines tapered to a point at each junction (the agent's
b23: scalloped feet, both reviewers REDO). A `_fillets` entry may be a CHAIN: `{"lines": [k1, k2, ...], "r": R, "why"}` - the lines round the foot in path order,
consecutive lines sharing a junction (refused by name when they do not; a member's single entry dropped and said); a line cut by a split ending on it is taken as its
legs inside the chain. skin-build sweeps every member at full R to the junction it shares with the next (no taper, no cap), ends its side offset ON the corner edge
(cut where it meets it, turned onto it where it falls short - about its far end, a linear ramp), brings the two members of a junction to ONE contact (the one short of
the edge swept again onto the other's), cuts the corner edge there, and makes the corner as the rolling ball does (sk_vertex; prototyped against the kernel's own fillet
in the kit's development record): CONVEX - the ball pivots about the corner edge: the patch is arc a's rotation blended (smoothstep) into arc b's,
G1 to both blends, its floor the rotation's own trace on the common face; CONCAVE - the two blends mitred along one curve (the surfaces' own intersection, else the
first's planar mitre for both) - a G0 crease from X up the corner edge, the kernel's answer too; only a blend of the corner edge itself removes it (not in the kit).
A hole in the chain (a member not made) frees its neighbours' ends - they taper - and the chain stands as sub-chains. The length cap counts only the run-outs a member
still has. Measured on the agent's b23 copy (25 builds): a closed valid solid once each keel half carried the ONE split the build named (the repair gate: a piece measured
against its own loop, the face and its sharpest corner said); the corner patches 10 deg mean off their blends at the 81 deg corners, 20-26 at the apex (the eased
ends' ramp, the cut-cap's slant - the exact rolling-and-sliding corner for unequal t is the next item). The cone-caps route (full R and caps at every junction) was
measured at 20-23 free edges on the same copy - two blends overlap on the common face at a concave junction - and is RETIRED (L144). Generic: a round of a foot is
ONE blend with corners, not a list of blends - the kit takes the round as the agent decides it and makes the corners itself; a failing route is diagnosed to its
step and fixed, never routed around.)*

*(31bp addendum 3, 2026-10-16 12:5x: the agent's b26 ran the fore and vane-2 chains too and the corner route met three more defects at their junctions, each measured on a copy and fixed
(the kit's development record): a corner edge the cut could not find by its parameter (now the kernel's nearest point; an uncuttable corner is GIVEN UP, never a hard
FAIL; a contact at the junction needs no cut; the junction loop settles every contact and give-up before any corner is built); THE SENSE CHANGE - a convex edge
between two original faces inside a chain of concave creases, where the chain now ENDS (L145); the small geometry of the ends - the concave cut snaps a piece's end
onto the one X, the apex patch with one contact and the caps are spanned THROUGH their shared edges (a cone cannot hold a curved border fragment; a natural-bounds
face's iso edges were never the neighbours' curves), the meets are found again on the TAPERED surface (on a crease shorter than two run-outs the other end's row is
scaled too). The three-chain copy of the agent's b26 then closed (f9: 87 faces, valid, 12131.3 mm3, max edge tolerance 0.25) with the fore and vane-2 feet as sub-chains
pointed at each sense change. The keel-half split named above is the aft chain's alone: with the vane-2 chain live (51 blended) the keel halves' loops change and
span without it. On the agent's job this round: the aft chain (b27b, PASS, trial CHECK PASS); the fore and vane-2 feet stay b23's lenses - the convex edges 48 / 91 / 51
in those chains are the agent's layout call (L145).)* *(31bq R7W W2, 2026-10-23: THE REFLEX-CORNER JUNCTION - where the side face's corner at a chain junction is reflex (the corner edge leaves the junction
past 180 deg from the crease through the offset's side) the chain ENDS there as at a sense change: both blends taper to the junction, a member whose side face has no room beside it is dropped with its room
line, the way out a layout / lines decision said by name; a freed end tapers from where the room ends before it takes a cap; a face's side of the crease is its own B-rep's (L154).)*

## L113. A VALID SOLID CAN HAVE AN INSIDE THAT DEPENDS ON THE RAY - JUDGE INSIDE BY THE WINDING VOTE, AND DROP WHAT HAS MATERIAL ON BOTH SIDES (2026-10-05).
the client, on R4 run 16's piece: *"A pit about 4 mm deep through the crown top - can't exist on a valid solid. How did this happen? It's the only
thing stopping the kit from being able to iterate to success."* It was a valid solid with a wrong shape, made by three links that each
trusted the one before (the agent's proof, a round report): (1) stage M took the outer shell by face identity, and the
crown-underside recess's top face - shared by two kept cells whose copies the sequential split had cut differently - matched on neither
side and stayed in as a buried sheet (z 87.2); (2) arrange-f's gate is topological (`solid True nonmanifold False selfint 0`) and its fan
fill closed the sheet's rim into a zero-volume pocket; (3) the blend's inside test was z-ray PARITY, whose `solid_runs` merges coincident
crossings - three crossings (85.46 / 87.23 / 91.40) paired as material then AIR, and the closing and the marching cubes built that air as a
4.2 mm pit. Measured on the job's base (numpy, read-only): 893 voxels the parity calls air are material by the 3-axis winding vote, exactly
the pit; 64 triangles of the raw base have material on both sides (the sheet 3.5 + 2.6 + 0.9 mm2, and 24 small places). The rules,
generic: (a) an inside test on a mesh that may carry a buried sheet, a fold or a crack is the WINDING number, along three axes, by
majority - never one axis's parity (`INSIDE=vote`); (b) a face or triangle with material on both sides is not a surface - dropped where it
is made (stage M `INTERNAL_FIX`, by geometry) and where it is meshed (arrange-f `INTERNAL_DROP`); (c) a topological gate is not a gate on
the inside: arrange-f also refuses a base whose inside check finds a buried sheet over 0.5 mm2. A single-axis test is fine only on a mesh
proven to have one consistent inside - which is the thing being made here.

## L112. THE CUTS ARE JUDGED BY AN ORBIT BEFORE THE WORK CONTINUES - BY AN AGENT WHO KNOWS WHAT A GOOD CUT IS (2026-10-05).
the client, 2026-10-05, on the keep's grid: *"the cuts should be render reviewed by an orbit pass before continuing work. That, plus an agent
understanding the process would fix placing walls where they shouldn't go."* Run 15's last seam faces (0.25 / 0.22 / 0.19) were a
keep plane laid flat inside a 1 mm lip - visible in one picture, found by three runs of numbers. Every cut the chain makes (the
window's walls, the keep's bin planes) is now drawn in red on the body in an 8-view orbit, and the next step refuses until an agent
has opened every frame and recorded the verdict on that artefact (`kit rebuild judge`; a re-run makes new cuts and needs a new
look; no override). What a good cut is: it CROSSES every skin it meets steeply, lands in thick clean material or in air, never runs
along a skin or inside a thin lip or rib, never through the feature being fixed, never across a fillet; seen from both sides the
surface is the same. A bad one is MOVED (WIN / PLANES; KEEP_OFFSET / KEEP_CELL) and the step run again. The kit's own checks (the
grazing refusal, the keep's placement and cut estimate) make the agent's job smaller; they never replace the look.

## L111. A PROTECT BOX HOLDS AN OPENING, NEVER ENCLOSED AIR - DRAW IT ON THE OPENING AND CHECK WHAT AIR IS INSIDE IT (2026-10-05).
the client, 2026-10-05: *"enclosed pockets are not wanted"*. Measured the same day (numpy, read-only, on REBUILD_JOB's content and on
R35_PRINT, the client's design-goal reference): each of a section's two PROTECT boxes held ~153 mm³ of the original's air; R35 keeps
~28 mm³ of it open (the slot's aft mouth) and fills ~125 mm³ - the gap between the vane's plate and the hat, forward of the mouth:
the enclosed hat pocket R35 fills at every station (MEASUREMENTS 2026-09-29), which a 2026-09-29 reading had already called
construction junk. The chain's base kept all of it, because a PROTECT box is kept exactly - in the arrangement (no gap fill), the
blend (no closing) and the keep (cut out of the region). So runs 13-15's slot-floor work (1.05 -> 0.012 mm) held a pocket the
requirements say must go: the boxes had been drawn on 2026-09-30 round "the two pockets under the hat's tongue" as the section
slot. The rule, generic: a PROTECT box is drawn on the designed OPENING only - the air open to the outside in the design reference
and in the pictures - and before a box goes on a card, the air inside it is checked against the reference: what the reference
fills is junk and stays out of the box.

## L110. THE ARRANGEMENT IS JUDGED AT THE ARRANGEMENT, AND ITS DECISION IS BLIND BELOW CELL SCALE (2026-10-02, R4 run 14).
Run 14's first piece on the PROTECT base reached STEP 4 (0.475, then 0.444 with the window-corner spikes kept), and the keep's new
BASE-vs-ORIGINAL lines put every remaining seam face on the BASE: 1.046 / 1.044 inside both slot boxes, 0.689 at the floor under the
keel's end, 0.400 on the forward plane (that one cured by SPIKE_V 1). Measured on the job's own files (numpy z-rays, read-only):
inside the slot at x +-3.4, y -119.4 the original has air from z 81.59 to 83.73 and the base has material up to 82.89 - cells.json
names the cell: a 13 mm3 AIR cell (fraction 0.00) with 49 mm2 of surface, 2V/A 0.53 mm, FILLED by the GAP rule as "a thin gap
between two material faces", because the 31ad PROTECT exemption tested the cell's CENTRE OF MASS (below the box floor at z 81) and the
cell straddles the box face. At the keel's end the base's 60 mm3 cell is "material, fraction 1.00 at 5 points" and its aft corner is
air in the original: the two end faces f75 / f84 were merged as duplicates of their planes f29 / f27 (within 0.5 at the 25 interior
samples) and the merged plane stands 0.69 off at the floor's corner, where no sample was. Three rules, generic: (1) a test of
"inside a box" on a CELL is by the cell's extent, never its centroid; (2) where a plane crosses it STEP 4 measures the base, so a
merge there is bounded by the SEAM ceiling, not the lasagna tolerance, and the merge test includes the corners; (3) a cell's
material fraction by 5 points cannot see a sub-cell feature - a mixed cell in a measured zone is re-split by the original's own
faces (REFINE_ZONES), and a changed tool set is applied incrementally (SPLIT=more), never by a 40-min re-split. And the
instrument: THE BASE CENSUS in stage M - run 14 read the base's deviation off the keep, eight steps and ~15 min later; the
arrangement prints it now, 3 minutes after the split, with the cell and the rule named at every place over 0.15 (the attribution).

## L109. THE AUDIT OF EVERY BORROWED MESH-ROUTE FUNCTION, SETTING BY SETTING (2026-10-02) - and what it measured.
the client, R4 run 12: "Have you actually checked that you got everything this time?" - the answer is this table, taken once against
`kit\mesh` (RECIPE_EXTRACT/WELD.json = the proven numbers) instead of one finding per poke. SAME: core margin 1.5 / fade off the
caps; the base refine at the wall (0.3); tiny-loop handling; the pinch before the join; the clean base (L105). MISMATCH: (1) the MC
grid 0.2 one-level vs 0.18 + 0.09 fine (H 0.15/0.12 tested run 11: did not help the seam); (2) THE RIM SNAP - CC_SNAP 0.25 walks
every patch vertex within 0.25 onto the kept surface, the burrito snaps planar faces only at 0.03 and skips sharp edges, so the MC
rim sits 0.36-1.09 off the base at a sharp-edge crossing and the zipper bridges it (the root of L108's strip; `KEEP_RIMSNAP`, 31ad);
(3) the join tolerance - seammerge at a 0.15 ceiling vs a strip accepted to 2 x KEEP_TOL (L108); (4) the polish - PassBand 0.05 /
NonManifoldSmoothingOff on the patch vs 0.1 / smoothed on the whole MC piece (`POLISH_PB` / `POLISH_NM` levers, 31ad; FeatureAngle is
inert with FeatureEdgeSmoothingOff - not a mismatch); (5) THE DECIMATION OPERAND - the mesh route decimates the PATCH only, before
the weld, boundary vertices kept, and never the body; the burrito decimates the WHOLE joined piece after the join, the kept-exact
base included - MEASURED on run 12's piece (numpy, read-only): inside both PROTECT boxes the undecimated KEEP piece equals arr_base to
0.02 mm (KEEP holds the base; the keep's "the blend strays 1.06 mm" line is not the blend) and the quadric 0.99 moves those exact
triangles up to 0.338 / 0.272 mm - BUT R4 run 13 CLEARED THE DECIMATOR as the seam's cause: a 0.97 quadric piece within 0.05 mm of
the undecimated one wherever STEP 4 measures listed the SAME six faces at the same widths (slot-box floors 0.439/0.340, the forward
cut plane 0.380/0.308, the floor 0.376) - the seams are the BASE's (the arrangement's) section against the original on the window
walls and the box faces; the keep's `BASE vs ORIGINAL at wall k / PROTECT box k` lines (31ae) measure that directly. `BAND` (31ad)
never reached STEP 4: DecimatePro on the open interior did not keep its rim vertex for vertex (open 136-202 after re-attach) -
a dead end on this piece; the quadric at 0.97 (4.3k faces, STEP 2 80 s) is the decimation; 0.95 (7.2k) is over the fuse's budget;
(6) the decimator - DecimatePro vertex-subset (exact, edges kept) vs the quadric (new positions, chamfers), with DecimatePro's
(0, 99) + volume gain on this closed piece unsolved (the step now names where); (7) the cap's units - bbox fraction, in the mesh
route's own `SetMaximumError(0.02)` too (hidden by its small crops; the comment says mm and is wrong - the value is proven, the
comment is not). Not a mismatch: the post-weld repair is a different tool set (nmfix/needle/spikes vs the FreeCAD finish), proven on
run 11. The audit's first rule: a borrowed function is audited against its route's recipe as a TABLE before the first run, never
found one defect at a time; the table lives here and in the KEEP RECIPE.

## L108. THE KEEP SEAM BORROWED THE MESH ROUTE'S WELD AND DECIMATE BUT NOT THEIR TOLERANCES - "the function, not the discipline". And a diagnostic / a repair pass must END.
R4 run 10 (2026-10-02, measured by the 31z placement line): the KEEP blend passed (health (0, 0), 175k triangles) and the
repair could not close it - **96 of 105 self-intersecting pairs were AT THE SEAM (< 0.5 mm from the body rim the zipper
paired), 0 elsewhere**; the base and piece were clean on their own. The crossings are the zipper's strip FOLDING THROUGH a
neighbour where it bridges a wide rim gap - the gap exists because the piece is raw marching cubes at h 0.2 (which rounds a
sharp convex edge 0.15-0.30 mm and is not snapped to the edge) and the zipper accepts a strip up to 2 x KEEP_TOL (1.6 mm at
run 8). The proven mesh route (`kit\mesh`, 27 welded pieces) welds a cleaned, decimated patch on a 0.09 grid and never
bridges a gap over its match tolerance (0.12-0.25); a far rim point is cured by MOVING THE WALL or a finer grid, never a
strip. Same weld family (`_ccseam`), the tolerance 3-6x looser and the grid 2x coarser. The second instance, same shape: the
decimation was plain `vtkQuadricDecimation` (chamfers the kept edges, 538 -> 790 samples cut > 0.15) where the mesh route's
own `vtkDecimatePro` (BoundaryVertexDeletionOff, PreserveTopologyOn, error cap) keeps them - made the default in 31aa and
REVERTED in 31ac (DecimatePro on this whole-section piece: a bbox-relative cap and health (0, 99); the quadric is the default,
the band of 31ad keeps the base undecimated where STEP 4 measures). The generic rule: when a step borrows a proven route's FUNCTION, it borrows its TOLERANCES and its grid too,
or it re-earns every failure the route already paid off. And `rb_repair`, found the same run: a collapse that maps w->u with
no walk-to-root chained a >=3-cycle that `mapping[mapping]` never resolved (356 s silent, watchdog-killed) - a diagnostic or
a repair loop that can run unbounded must walk to a root (as `_slit_pass` does) AND declare itself; a "revert" that snapshots
AFTER it has already moved the vertices does not revert; and a fan fill that can leave a non-manifold edge needs a
`removeNonManifolds` after it (run 10 ended `solid False nonmanifold True selfint 0`, one step short). All three fixed (31aa).

**L1. The ray range must START AND END IN AIR. This is the first check, not a detail.**
*Retired with the S3–S7 chain (2026-09-28): the rebuild chain has no rays. Its equivalent is the region step's two wall
warnings — a wall lands in clean material, never through the feature being fixed.*

## L2. No number this method produces can detect a wrong-shaped piece. Only the orbit can.
Still the first law. Volume within 2 %, one valid solid and CHECK PASS were all true of pieces the client rejected on sight.
The piece review (step 6) and the body review (step 10) are opened picture by picture at full size before anything is
handed over; a status line is never a verdict.

## L3. Choose the card's walls by MEASURING the seam, never by round numbers.
*Retired (corrected by L21, which stands).*

## L4. A panel spanning two disconnected surfaces cannot be fitted, and more poles will not help.
*Retired with the sheet fitter.*

## L5. `LK_LAYERS` defaults to `L0_0`, and S7 DELETES everything not in the piece.
*Retired with S7. Its descendant: the reinsert puts the region's leftover solids back unchanged (step 1, step 9).*

## L6. `smooth` is the lever that fixes a failing BOP check on the piece — try it before any surgery.
*Retired with S5.*

## L7. Ray direction is a design decision and is worth measuring BOTH ways — at the PROBE.
*Retired: no rays.*

## L8. Regions that collapse to `no tube` are a real loss, and growing the margin does not save them.
*Retired: no tubes.*

## L9. Verify the reference mesh is the one you just built.
*Retired as written; the rule survives as the tag: every output of a run carries `--tag T`, and the record names it.*

## L10. A large curved wall is not a burrito card in ANY ray direction. Size the card to the DEFECT.
*Retired as written. The window is still sized to the defect — a whole flank in one window is a whole flank of
arrangement cells and a whole flank of blend grid.*

## L11. Every step of this process takes at most ~3 minutes. Longer means locked up, not working.
Stands, and the runner enforces it: an unnamed step is capped at 360 s. The one step that outgrows it is the reinsert's
fuse as the piece's face count rises (CLOCKS) — a measured clock row raises its budget; a hung step never does.

## L12. DO NOT CHAIN CARDS. Fuse every piece onto the SAME original body, never onto the last result.
Restated for the rebuild: the chain never fuses on the body at all (a local box and a sew), so windows CAN follow one
another into the current body of record — each accepted first, and two windows whose local boxes overlap are one
window. What is still forbidden is a piece fused onto an unaccepted result.

## L13. S7 can write an EMPTY result and then crash before telling you.
Stands for every step: freecadcmd exits 0 on a script exception. The evidence is the artefact (size, the FINAL / RESULT /
CHECK line in the log), never the exit code; the runner renames a killed step's declared outputs `.KILLED`.

## L14. A background task you stop reading is not a task you stopped. Kill it.
Stands. `kit burrito ... --bg` registers the pid; `kit collected <name>` when read, `--kill` to end it.

## L15. An invalid fuse has a number of bad faces, and it is usually one. Census before you treat.
*Retired with S7 (the whole-body fuse). The reinsert's STEP 4 is the census now: faces on each plane and offset.*

## L16. You cannot repair a fuse-made invalid face afterwards. All four repairs are measured no-ops.
*Retired as written; the rule survives as L81 — the union is made transversal BEFORE it is made, never repaired after.*

## L17. The fuzzy fuse is the fix, it costs 20× the plain fuse, and that cost is not a lock-up.
*Retired and reversed: the client, 2026-09-28 — "too expensive for both compute and time. This is not a fix or something I would
want to use." No fuzzy operation anywhere in the rebuild chain (the generalFuse FUZZ 1e-5 is a tolerance, not a fuzzy fuse).*

## L18. "Manufactured volume" is not a gate when the piece's own two rulers disagree.
Stands as L85: the mesh volume is the ruler; `Part.Volume` is 11,000 mm³ off on this body.

## L19. Two cards that abut cannot be combined by chaining, by multi-fuse, or by a fuzzy join.
*Retired with cards. Its descendant: overlapping local boxes are one window (L12).*

## L20. The fuzz treats a card cut against a seam. It is not an improvement. Ladder it, from zero.
*Retired: no fuzz.*

## L21. CHOOSE A CARD'S WALL BY THICKNESS, NOT BY MINIMUM SEAM AREA. THIS CORRECTS L3.
Stands for the window's walls: land a wall in AIR where possible, otherwise in the thickest clean material; the
minimum-seam wall finds the thinnest place in the body, which is the worst place to cut. The region step now measures
what the old rule could not: a grazing skin and a design face in the plane.

## L22. THE REVIEW ORDER: AFTER FRAMES ALONE, JUDGED. BEFORE FRAMES ONLY IF THAT JUDGEMENT NEEDS THEM. AN OVERLAY LAST, AND ONLY IF BOTH SAY IT WOULD HELP.
the client, 2026-09-17: *"It should tell agents to only take after frames... then before frames if needed."* The piece review
renders the result alone; the station overlays are the LAST instrument, for one question only — do the two coincide
where they should. An overlay render of before and after cannot show where the piece changed as a shape; a section
can (L70's picture at a stated scale, plus numbers).

## L23. Do not merge abutting cards into one, and do not mix card widths in one fuse.
*Retired with cards.*

## L24. READ THE ACCEPTANCE TABLE. DO NOT INVENT CRITERIA.
Stands. `PROJECT_SUCCESS_CRITERIA.md` is the table; a window's card carries its `Row:`; the six criteria at the top of
this file are the client's words, not a substitute for the row.

## L25. The review fan-out disagrees on purpose — the orchestrator opening flagged frames IS the merge.
Stands for any fan-out review; the chain's own reviews are one reviewer opening every frame.

## L26. AN OVERLAY CANNOT SHOW A SHAPE OR AN EDIT. BEFORE LAUNCHING A JOB, SAY WHAT ITS OUTPUT WILL SHOW.
the client, 2026-09-14: *"YOU CAN'T OVERLAY THE ORBIT OR YOU DON'T SEE THE EDIT."* An overlay render of before and after shows
coincidence and nothing else; the default frame is the RESULT ALONE. Say before a review what its pictures will show,
and open them for that.

## L27. A FRAME THAT CANNOT SEE THE CARD IS A GATED FAILURE. NEVER DELETE IT — GIVE IT A CLIP PLANE.
Stands. The piece review's close-ups exist for this; an underside that a view cannot reach is a z-section, not a
deleted frame.

## L28. The method is "close base shape, then iterate mesh edits to converge" — and nobody writes that down.
*Retired as written: the arrangement IS the base shape and it is exact, so there is no convergence loop. What remains
of it: one measured change per defect, re-run, re-review — never a second run with nothing changed.*

## L29. A SINGLE-HEIGHT SECTION IS NOT A CONTINUITY CHECK. THE ORBIT CAUGHT WHAT IT MISSED.
Stands. Stations are chosen through every feature the window holds (the lines above give nine in y and five in x for a section), and the orbit views are opened regardless of what the stations say.

## L30. AUDIT FOR DRIFTING PROCESSES ON A SCHEDULE, NOT WHEN SOMETHING FEELS SLOW.
Stands: 1.5× the measured typical is the red flag (the client, 2026-09-14); `kit clock add` after every step of a new chain.

## L31. `MARGIN` LETS A BAD PANEL'S SHEET OVERLAP A GOOD ONE. RAISING IT TO FORCE ONE SOLID IS A TRAP.
*Retired with the sheets — raising MARGIN to get one solid bought it with a 1.4 mm ridge. Its descendant: never buy one
solid with a lever; more than one solid in the piece is normal and the reinsert attaches them (L89).*

## L32. A FUSE RESULT'S `isValid()` IS NOT A GATE: IT RETURNS TRUE ON AN EMPTY SHAPE.
Stands: every step's line prints the volume and the count beside `valid`; STEP 3 refuses more than one solid.

## L33. Fuzzy fuse is not a repair on this body. The seam is, and `OUTER` is its lever.
*Retired (no fuzz; the seam's levers are CLIP_OUT and SHRINK, L81/L82).*

## L34. A DRIVER SCRIPT THAT HARDCODES A LEVER SILENTLY OVERRIDES EVERY DOCUMENTED DEFAULT.
Stands: every lever of the chain is an environment variable with its default in the table above and in the script's
header; the runner's env file records what the run actually saw.

## L35. READ WHAT S5 RETURNED, NOT WHAT THE DRIVER PRINTED.
Stands in spirit: the record is the REBUILD_*.json and the artefact, not the chat.

## L36. `Shape.BoundBox` ON UN-TESSELLATED NURBS IS A LIE, AND IT WILL MAKE YOU BLAME THE KERNEL.
Stands (a section's region solid reports x ±65 for a ±24 window). Bounds are read off a tessellation or the mesh.

## L37. A height map cannot see a lean, and this part leans.
*Retired with the height-map probe; the arrangement classifies by volume fraction, not by height.*

## L38. Split the card at a wall, not across it. The x-split is what fixes stepped panels.
*Retired with panels.*

## L39. Abutting strips do not fuse. Overlap them.
Stands as L81, one level up: nothing coplanar is ever fused; every union overlaps by CLIP_OUT.

## L40. Pre-union the pieces before fusing into the body.
*Retired: the reinsert fuses the piece solids and the leftovers into the LOCAL crop in one call, never into the body.*

## L41. Recover a polygon's edges from the curves that made it, never by splitting it in half.
*Retired with the sheet fitter.*

## L42. Tune per piece, not per job.
Stands: the CARD levers (window, planes, R, REDUCTION) are the window's; the rest are the method's.

## L43. S3 reports layers that are not in the footprint. Handing them to S5 IS "no tube".
*Retired.*

## L44. Measure in the window you are building in. A height map has no window.
Stands: every instrument of the chain is windowed — the region, the arrangement, the blend grid, the reinsert's box,
the STEP 4 census (L90).

## L45. The ball weld closes a taper here, not a slot, and chasing it produces blades.
*Retired.*

## L46. RETRACTED 2026-09-16. It contradicted L22 and L26 and caused a third overlaid orbit.
Kept retracted; the number stays taken.

## L47. THE KERNEL'S FINAL FUSE IS NOT DETERMINISTIC UNDER LOAD, AND IT FAILS QUIETLY.
Stands, and is why the chain has no whole-body fuse: the sew is deterministic and 24 s.

## L48. A waiter that polls for a sentinel file hangs forever when the file never comes.
Stands: the runner's declared outputs and `.KILLED` markers; wait on an artefact with a bounded wait, never on a name.

## L49. When the method has a proven run on this geometry, reproduce that configuration first.
Stands: the lines above ARE a section's proven run; a new window starts from them and changes the CARD levers only.

## L50. At a tall wall, L38 and L39 cannot both be obeyed. Measurement says straddle the wall.
*Retired with panels.*

## L51. One card per feature, on that feature's own axis. And the build stage only supports z.
*Retired: the blend has no axis; the arrangement has no rays.*

## L52. AN INSTRUMENT BUILT FROM BOUNDING EXTENTS GIVES A CONFIDENT FALSE ANSWER AT A CURVED OR OBLIQUE INTERFACE.
Stands (with L36): the region's "touches the box face" test reads a face's real bounds; anything at a raked plane is
measured by distance to the plane, not by a box.

## L53. A card boundary belongs inside material, where the two pieces cross — not on a wall they share.
*Retired as written; the rule is L81/L82 now: the boundary is a transversal overlap band, never a shared face.*

## L54. A layer index is a ray-order accident, not a feature. Track the skin instead.
*Retired.*

## L55. The S6 loop is measured, not tuned: WHERE the sheets miss, by how much, and one op that applies it.
*Retired with S6; the station overlays with numbers survive as the piece review.*

## L56. When two pieces must share a band, `offset` one of them.
*Retired.*

## L57. A smooth feature that spans several sections gets one card.
Stands as a window rule: a feature that crosses a wall is cut by it; put the wall where the feature is not.

## L58. A card's footprint ends where its roof falls off.
*Retired.*

## L59. Where a z-column runs on into another feature, the dive is real material. Decide what it is before touching it.
Stands as the arrangement's rule: the material decision is made by the original's own volume fraction, cell by cell,
never by a column.

## L60. MIRROR THE FEATURE WHOSE SYMMETRY IS DESIGN, AND NEVER A PIECE THAT MATES TO AN ASYMMETRIC BODY.
Stands. Mirroring is an option (the client, 2026-09-13), and the blend's grid is centred so a symmetric window comes out
symmetric on its own (median asymmetry 0.001 mm); nothing in the chain mirrors.

## L61. One card, one skin.
*Retired.*

## L62. THE BODY FUSE IS NOT A RESULT UNTIL `isValid()`; AND THE UNION IS NOT A RESULT WHILE `failed` IS NOT EMPTY.
Stands for the local fuse and the sew: STEP 2 and STEP 3 print valid, solids, faces, volume; STEP 4 is the census.

## L63. CUT ONLY WHAT IS JUNK; WHAT IS CLEAN COMES BACK AS ITS OWN FACES.
Stands, and since 2026-09-30 the chain obeys it (L102): `kit rebuild keep` finds the bins the piece changed and the
reinsert replaces those alone; every clean face, the PROTECT voids and the frozen faces come back as the body's own.

## L64. Withdrawn in place (2026-09-19, the client's rule of 17:40).
Number kept.

## L65. Withdrawn in place (2026-09-19, with L64).
Number kept.

## L66. THE STATIONS INSTRUMENT HAS THREE WAYS TO LIE.
Stands: a station picture is a section at a stated scale with its mm/px in the caption (the review writes it), and a
station with nothing in it is skipped and said so, never drawn empty.

## L67. The card describes its shell only.
*Retired with the `shell` op.*

## L68. ASSEMBLY: PLAIN JOINS, ONE PLAIN FUSE.
Stands, sharpened: one local fuse, one sew, nothing else.

## L69. MEASURE ONLY WHEN THE RULES HAVE FAILED, AND SAY SO.
Stands (the client, 2026-09-19 02:20).

## L70. THE REVIEW IS A SECTION PICTURE AT A STATED SCALE, PLUS THREE NUMBERS.
Stands (the client: "pixel level accurate"): the station overlays carry their scale; the numbers are the volumes, the wall
sections and STEP 4's areas.

## L71. A piece meets the body on planes it shares — plane cut, plane-bottomed slab, box fill.
*Retired as written and corrected by L81: a shared plane is exactly what does not fuse; the piece meets the body across
an overlap band.*

## L72. A SHEET OVERLAPS THE PLANE IT MEETS; IT NEVER RESTS ON IT. ONE SHELL AFTER EVERY FUSE.
Stands and is now the reinsert's construction (CLIP_OUT past every wall).

## L73. THE GRID IS CENTRED, THE WALL IS ON THE FACE, THE OUTLINE SNAPS TO THE WALL.
Stands (with L84): the blend grid is centred on x = 0 and offset off every face; the caps stay on their planes.

## L74. A SMALL FUSE IS GATED IN A WINDOW, NOT ON THE BODY'S VOLUME.
Stands: STEP 4 counts inside the local box only (L90); the mesh volume of the whole body is recorded, not gated.

## L75. A non-symmetric region: one card per side, each from its own rays, no mirror, the twins compared afterwards.
*Retired as written; nothing mirrors (L60).*

## L76. A raked plate is described across its thickness, never by columns down through it.
*Retired with columns; the arrangement decides by volume fraction.*

## L77. A void is filled by its own shape, and the fill is gated on shells.
Stands as the arrangement's gap fill (thin cells between two material faces) and the blend's closing (gaps filled).

## L78. A fill's box planes are checked against the body, and a void behind a chamfer is bounded by the chamfer itself.
Stands as the region step's wall checks.

## L79. A VOXEL FILL IS BUILT ADD-ONLY; A FLAT FACE RE-EXTRACTED COMES BACK HALF A VOXEL INSIDE ITSELF.
Stands, and is why the blend is continuous fields with a snap back onto the planar base (L83): a flat face of the
arrangement comes back exactly, not half a voxel in.

## L80. A HELD FACE THAT RUNS INTO THE DEFECT BECOMES A FIN — hold the design, bridge the defect.
Stands: the arrangement holds the design surfaces and drops the fins (spikes, slivers); the opening removes what is
left thinner than the print rule.

## L81. A FUSE ACROSS A COPLANAR CONTACT DOES NOT MERGE — EVERY UNION IS MADE TRANSVERSAL BEFORE IT IS MADE.
Measured 2026-09-28: a piece cut flush with the walls and fused into the body left its cap faces as slits (84 and
382 mm²), and no repair afterwards removes them (L16). So the blend keeps the piece CLIP_OUT (0.1 mm) past every wall
plane, the reinsert cuts the region SHRINK (3 mm) inside every wall so the body keeps a band, the leftovers' plane
faces are extruded CLIP_OUT, and every union crosses the other shape. STEP 4 proves it: nothing on the plane itself.

## L82. A WALL GRAZING A SKIN LEAVES A WEDGE NO MESH CARRIES — SHRINK THE REGION AND MOVE THE PLANE.
A plane within ~10–20° of a skin leaves a sub-voxel wedge between the two that the arrangement drops and the opening
removes; with the region cut flush that wedge was 176 mm² of exposed cut face. SHRINK 3 keeps the body's own material
there; what remains is a 2.6 mm² step 3 mm deep on a section's front plane, reported by STEP 4. The region step warns
of the graze before anything is built; the cure is a plane that crosses the skin, not one that follows it.

## L83. SNAP ONLY ONTO PLANAR BASE TRIANGLES — SNAPPING ONTO A TESSELLATED CURVED SKIN PRINTS ITS FACET EDGES.
The dark dashes on the crown were the base tessellation's facet edges pulled into the blend by the snap; FLAT_DEG
decides what is planar enough, EDGE_DEG keeps the snap off sharp edges, and a snap that would fold a triangle is refused.
Curved faces get the gentle POLISH2 instead — and a sinc polish over curved faces WITHOUT holding the base made 377
self-intersections, so everything within SNAP of the base is held.

## L84. A PLANAR FACE EXACTLY ON A GRID PLANE MAKES DEGENERATE MARCHING-CUBES TRIANGLES — OFFSET THE GRID.
Open and non-manifold edges and five components at x = 4.5, all on one planar face that sat on a grid plane; the grid
is offset by 0.37/0.29/0.43 h and the defects are gone. Any voxel instrument on this body carries the offset.

## L85. `Part.Volume` IS NOT A RULER ON THIS BODY; THE MESH VOLUME IS.
11,000 mm³ apart on the body before anything is done to it (L18 measured the same on a piece). Every record in the
chain carries the mesh volume; `Part.Volume` is printed with the words "not a ruler here" beside it.

## L86. `Mesh.fixSelfIntersections` DESTROYS VOLUME — NEVER; COLLAPSE THE SLIVERS AND LET `removeNonManifolds` + `fillupHoles` FINISH.
7502 → 6684 mm³ on the section-4 blend. The finish that works: sliver collapse with the link condition and a
normal-flip check, self-intersecting pairs collapsed with a manifold revert, then removeDuplicatedPoints,
removeNonManifolds, fillupHoles, collapseFacets — 256,118 facets, solid, 0 self-intersections, volume kept.

## L87. NEAR-DUPLICATE SLOPPY SURFACES MAKE A LASAGNA OF CELLS — MERGE THE SMALL FACE INTO THE BIG ONE, NEVER TWO BIG ONES, NEVER A FACE ON THE BOUNDARY.
the client's rail-foot lumps were 0.2–0.5 mm cells between surfaces 3–10° apart. LEVEL 0.8 / 12° on every pair cured them and
thinned the vane wing 0.5 mm at the wall (two big faces merged); the rule that holds both: the relaxed merge only for a
face under DUP_FRAC of its neighbour's area and never for one that reaches the window boundary; the strict merge
(0.5 mm / 5°) for everything else; the opening takes the rest.

## L88. THE SHEET FITTER IS A 2.5-D REPRESENTATION — NOT THE MESH → B-REP CONVERTER, AND NOT THE FINISHING PASS EITHER.
On the arrangement's own clean mesh the S3/S5 chain gave valid 45–63-face pieces that washed out designed features,
dropped the wings at the walls, missed the walls and lost ~10 % of the volume. A B-rep of every triangle is the
conversion that keeps the shape (the client: "do it like burrito 1 sounds stupid" — it is; it is also what is right until the
finishing pass), and the face count comes down once, on everything, when the client says (2026-09-28).

## L89. A DETACHED COMPONENT OF THE PIECE IS NOT A RIB END UNTIL IT IS MEASURED — **CORRECTED 2026-09-29 BY L95.**
As first written (2026-09-28): "a section's two small solids (30 and 7 mm³) are rib ends cut by the x walls; the
reinsert attaches them". They were not. They were arrangement cells at the front raked wall with a third of their
volume OUTSIDE R31's skin, and fused in they stood 0.6 mm proud of the vane wing's underside — a lump the sandbox's own
review passed because this lesson had named the pieces before anyone measured them, and the kit's before/after review on
the client's machine caught in its first lead frame. What survives: `rb_brep` makes one solid per component on purpose (one shell
of three was invalid), STEP 3 must still report ONE solid, and anything under MIN_KEEP left floating is dropped and
printed. What replaces the claim: the measurement in L95.

## L90. THE BODY HAS ITS OWN FACES ON A WALL PLANE ELSEWHERE — COUNT SEAM FACES INSIDE THE LOCAL BOX ONLY.
STEP 4 first refused a clean reinsert: 59 faces / 166 mm² on z = 60, all of them R31's own, none inside the window.
The census counts faces whose centre is inside the local box, subtracts the old body's own faces on that plane there,
and judges the rest.

## L91. THE PIECE'S SKINS ARE THE BODY'S OWN TO 0.03 mm, SO THE BAND IS A STRIP OF NEARLY COINCIDENT SURFACES — THE FUSE FAILS QUIETLY THERE, AND A SHORTER BAND FAILS LESS. LADDER SHRINK; GATE EVERY RUNG ON VOLUME.
2026-09-28, a section, the same window twice: the first piece (1,790 faces) fused at SHRINK 3 in 62 s; the second
(1,784 faces, one pinch merged, otherwise the same to 0.1 mm) returned ONE far solid of 2,388 mm³ at SHRINK 3 — the
18,663 mm³ main solid silently gone, the kernel's rc 0, `isValid()` True (L32, L47). The main solid alone with the
piece returned EMPTY in 33 s; the reversed order ran past 150 s; a fuzzy fuse at 0.01 gave four solids, three of them
empty; `generalFuse` succeeded (51 cells, 37 of them under 0.01 mm³ — the slivers of the band) but no shell could be
closed from them. SHRINK 2, 1, 0.5 and 0.3 all fused the same piece in 41–52 s. The band is where the arrangement's
faceted skins (DEV 0.03 mm) lie on the body's exact ones, and every millimetre of it is more near-coincident
intersection for the BOP to get wrong. So STEP 2 walks `SHRINK_LADDER` (2, 1, 0.5, 0.3), gates each result — a union
is never smaller than the crop it started from, must be valid, and has no more solids than the crop — records the rung
that passed, and STEP 4 measures the exposed shrunk cut at that rung. A run that fails every rung says so and stops.

## L92. A PINCH — A MICRO-SLIT OF TWO OPEN EDGES AND ONE NON-MANIFOLD EDGE UNDER 0.05 mm — IS MERGED, NOT FILLED.
The blend's polish holds every vertex within HOLD_W of a wall; a vertex just outside that band folded against its held
neighbours at (18.8, −130.9, 89.8) and left 0.004 and 0.018 mm open edges with one edge shared three times. FreeCAD's
`fillupHoles` cannot close a slit that short and `removeNonManifolds` only runs when it sees a non-manifold, so the first
run through the runner shipped `solid False`. The finish now merges the endpoints of every open or non-manifold edge
under PINCH (0.05 mm) before the FreeCAD pass, keeps the merge only if the health count drops, and fills any remaining
open loop whether or not a non-manifold is beside it: (2, 1) → (0, 0), solid True.

## L93. `kitlib.fuse` KEEPS ONLY THE LARGEST SOLID — NEVER USE IT WHERE THE RESULT IS SEVERAL.
The local crop of the body holds every solid inside the box (a section: the main 18,663 mm³ and a far 2,388 mm³ one,
both body material). `kitlib.fuse` prints the others as "dropped solid" and returns the largest; run through it, the
reinsert would have sewn the body back without the 2,388 mm³ solid and STEP 4 would have said PASS. `rb_reinsert`
fuses raw on purpose (`kit rebuild` is its runner; `kit burrito`'s raw-fuse refusal is right for the S7 door and wrong
here), and the volume gate of L91 is what would catch a dropped solid.

## L94. numpy 2.0.0 RETURNS A 2-D INVERSE FROM `np.unique(axis=0, return_inverse=True)` — FLATTEN IT, AND RUN EVERY STEP UNDER ONE INTERPRETER.
the agent's round, 2026-09-29: the one step the runner started under the machine's plain Python (fillholes, no kernel import)
died in `write_stl` with `could not broadcast (1785,1,3) into (1785,3)` — numpy 2.0.0's inverse is (n, 1), fixed in
2.0.1, and `T = inv[T]` had grown a third axis. Every `np.unique(... return_inverse=True)` in the chain now ends in
`inv.reshape(-1)`, and the runner starts every step under freecadcmd (FreeCAD's own numpy ran the other nine steps),
so the machine's site-packages never touch the chain again. And the crashed step had left an 84-byte STL the next step
took as its default input (L13 in a new place): a failed step's declared outputs are renamed `.FAILED`.

## L95. A DETACHED COMPONENT OF THE PIECE GOES BACK IN ONLY IF ITS MATERIAL IS THE ORIGINAL'S — MEASURE THE FRACTION INSIDE THE CONTENT.
The lump of L89, measured: 64 % and 66 % of the two components lay inside R31's content; the rest was material the
original never had, decided by 5×5×5 fractions in cells beside a grazing wall. STEP 2 now tests every detached solid
against the content (`IN_CONTENT` 0.9): under it, dropped and said (`component 30.32 mm3: only 64 % inside the original
- DROPPED`), recorded in `_reinsert_state.json` and REBUILD_reinsert.json; over it, kept — a rib end that really crosses
a wall is inside the original by construction. The main solid is exempt: its added material IS the blend. the agent's trial
had cured the same lump with `MIN_MM3 40` — a size threshold, which would also drop a real rib end; the measurement is
the rule. The sandbox re-run: dropped both, body 6,582 faces, CHECK PASS, lips 0.78 mm² — the agent's numbers exactly.

## L96. THE KIT'S GATES HAVE THEIR OWN LINES, AND A REBUILD MUST SAY THREE OF THEM: --wide-box, THE CARD'S OWN LINE FOR kit look, kit review ON ONE CAMERA.
`kit check` refuses the window box by its 25× rule (163,944 mm³ of box against a 142 mm³ net change) — for a rebuild the
change is the whole window re-expressed, so `--wide-box "the window is the change: <content mm3> re-expressed"` goes on
the record. `kit look` reads only stamped frames, and the chain's `review\` and `review_body\` are not — the card's
`After:` line (`kit render ... --box <window + 3> --job <name>`, 80 s) runs first. And the chain's own pictures are
the piece and the seams; the kit's `kit review`, old body and new body on ONE camera, is what found the lump — both
reviews, every frame, always. The `kit job` line: `--type burrito --card <CARD.md> --tier orchestrator --wall-min 30`,
with `Region:` on the card (an approved atlas refuses a job without it).

## L97. A FITTED PIECE GOES BACK IN BY A SEW ON THE BODY'S OWN SECTION FACES, NEVER BY A FUSE — AND A PIECE THAT FAILS `check(True)` BREAKS EVERY BOOLEAN.
the agent's finishing pass, 2026-09-29: B53 (66 fitted faces, `isValid()` True, 0.4 % of the volume) fused into the crop on
no rung; measured here: plain fuse hung past 150 s at SHRINK 0 and 2; fuzzy 0.02 threw `Null shape`; fuzzy 0.05 hung;
`generalFuse` at 0.05 hung; `piece.common(crop)` returned EMPTY; clipping the piece flush at the walls made it
invalid. Its faces fail `check(True)` (InvalidCurveOnSurface / SelfIntersect, the agent's item 18) — pcurves a boolean cannot
work with, whatever the tolerance. The join that needs no boolean: cut the body exactly at the walls, give the piece
the body's own section faces as its caps (`wall_caps.brep` from STEP 1, their edges shared by the faces beside them),
match the caps, drop both copies, sew the rest (`JOIN=sew`). Sewing joins only EXACTLY coincident edges in FreeCAD
1.1.3 (`sewShape` ignores its tolerance, the agent's item 13) — which is exactly what copied faces give. The rest of the piece
may be any approximation: only the cap edges must be exact. Measured with the content as the piece: 4 s, to 0.4 mm³.

## L98. THE FUSE GATE COMPARES WITH CROP + PIECES − THE BAND − THE OVERHANG, NEVER WITH THE CROP ALONE.
the agent's B45 and B47 "passed" STEP 2 at SHRINK 0.5 while losing 1,500–2,100 mm³; STEP 3 caught them. The old gate asked
only that the union be no smaller than the crop. Now: expected = crop + every piece − the pieces' volume inside the
band (a planar cut of the pieces by band = window − shrunk window) − the pieces' volume past the walls (piece − window),
within max(1 % of the piece, 2 mm³); a section's good fuse sits +12.6 on a 74.8 tolerance. Both measures are planar
cuts of the PIECES alone, so a piece that breaks a boolean cannot pass by them.

## L99. THE BAND WAS THE FAILURE: TWO DESCRIPTIONS OF ONE SKIN ON TOP OF EACH OTHER. THE PIECE MEETS THE BODY ON EXACT PLANES ONLY.
2026-09-30, measured on a section with the same 1,784-face mesh piece (check(True) OK). The band construction — the body cut
SHRINK inside every wall, the piece overlapping that band to CLIP_OUT past the walls — lays the piece's skin 0–0.03 mm
over the body's own along the whole band (K-COINCIDENT); the kernel's union then fails QUIETLY: at SHRINK 3 one solid of
2,388 mm³ came back and the 18,627 mm³ main solid was gone (L91); the shorter rungs fused by luck, which is all the ladder
ever bought. The same piece and leftovers TRIMMED by the same shrunk solid (`piece ∩ shr`: the only contact is coplanar
planar faces of one plane, both from one BOP tool in one process) fused within +0.8 mm³ of the exact expectation at
SHRINK 3, +3.3 at 1, +7.6 at 0. So STEP 2 cuts the body and the piece by ONE region solid and fuses the trimmed pieces in
one at a time; the volume gate is exact (max(0.1 %, 2 mm³)); SHRINK survives only as where the plane is when no keep
region exists. Why "reinserts worked before without marked edges": the old S7 cut the un-grown footprint and trimmed the
piece 0.5 mm wider (OUTER) — a short band — and L33 records its one invalid face at the seam; luck with good odds, not a
method. L81's "a coplanar contact does not merge" was a piece clipped by VTK at the plane against a kernel-cut face —
nearly, not exactly, coplanar; cut by the same kernel tool the contact is exact and the fuse merges it.

## L100. A PIECE THAT FAILS `check(True)` BREAKS EVERY BOOLEAN IN EVERY CONSTRUCTION — IT IS REFUSED BEFORE ONE IS TRIED.
the agent's B47 (66 fitted faces, edge tolerance 0.08 mm, isValid True) fails the BOP check with 56 InvalidCurveOnSurface and
8 SelfIntersect; trimmed exactly like the mesh piece it still lost the main solid. B53 the same (plus two C0 edges, tol 0.6);
S16 (114 faces, tol 2.49) 104 SelfIntersect / 74 ICOS. STEP 2 now runs `check(True)` on every piece solid first (0.5–1 s on
a 1.7–3 k-face mesh piece; 134 s on S16 — an invalid piece is slow to judge) and refuses by name with the kinds and counts;
`BOP_OK="<why>"` goes on anyway and is recorded. K-BOPGATE said this on 2026-09-16; the chain had not applied it. A fitted
piece is right when its edges lie on its faces (edge tolerance under 0.01 mm), no wire crosses itself and no edge is C0 —
the finishing pass's own gate, build by build, not the reinsert's.

## L101. `sewShape()` IN FreeCAD 1.1.3 JOINS IDENTICAL EDGES ONLY; AND A SEW OF EVERY FACE RE-FIXES THE FUSED INTERIOR — SEW THE RING.
A 1e-5 mm gap stays open at every tolerance passed (the docstring is `sewShape()`: the argument reaches nothing). So a
JOIN=sew piece needs caps that ARE the body's section faces (wall_caps.brep), edge for edge (L97), and nothing is ever
"sewn within 0.01". And STEP 3's sew of rest + the local result's EVERY face flipped four of the fused result's faces (a
13 mm² seam face among them) and gave a valid shell inside an invalid solid, 1,947 mm³ short by Part.Volume — the sew's
own repairs on edges the fuse had left tolerant. Sewing only the faces with an edge IN a box plane (154 of 7,059) keeps
every interior face and edge object as the fuse made them: valid, closed, the mesh ruler agreeing within 3 mm³.

## L102. KEEP WHAT IS CLEAN: ONLY THE BINS THE PIECE CHANGED ARE REPLACED; PROTECT VOIDS ARE CUT OUT EXACTLY; A FROZEN FACE THE PIECE CUTS INTO STAYS.
the client, 2026-09-30: "clean faces, the frozen vanes and the section slot go back exactly as they are, and only the wrong parts get
touched" — "do it". `kit rebuild keep`: the window binned (KEEP_CELL), a bin CHANGED by a surface sample further than
KEEP_TOL from the other surface or by material flipping away from both; the rest KEPT. Measured on a section's symmetric
window: 55 % of the visible surface kept exactly, the slot pair's material 234 → 234 mm³ (S16's sewn refit: −10 / −17 %,
refused). Three things the first run taught: (a) a PROTECT box forced bin by bin keeps the piece's fill OUTSIDE the box
behind in the kept bins — a 2 mm step along every box edge; cut the box out of the region exactly and the piece runs to the
box face, where the blend's own fade starts (0.17–0.30 mm there); (b) a frozen face inside the body's own material on both
sides is a lamination, not a surface — 8–11 % of the samples on this part — and is not judged; (c) a region component the
original fills completely is left alone: the piece has a VOID inside the body there (four 0.6–3.9 mm³ cells the
arrangement dropped at the x walls) and cutting and re-fusing it made four enclosed voids. What remains honest: a forced
bin beside a rebuilt one is a step the seam shows (a section: the blend's OPEN trimmed the vane root by up to 1 mm;
STEP 4 refuses at 0.52 mm) — the cure is the piece, never a looser keep.

## L107. PAIR THE RIMS FIRST; COLLAPSE ONLY WHAT HAS NO PARTNER - A COLLAPSE BEFORE PAIRING ORPHANS THE OTHER SIDE.
R4 run 7 (2026-10-02, the agent's finding from the join's own record): the zipper collapsed every piece rim loop under 1 mm to a
point BEFORE pairing - a grid-artefact rule - so where the core wall crossed a real 0.9 mm feature (the mirrored slit pair
under the slot boxes), the piece's two 40-45-point loops vanished and their exact body loops were left without a partner;
the join refused, and no KEEP lever could reach it (KEEP_TOL inert, KEEP_M only moved which loops were hit). The order is
the mesh route's (`_ccseam`: pair, then treat only the unpaired): pair the loops as they are, collapse an orphan only when
it is small on its own evidence (a piece loop under 1 mm, a body loop under 0.5 mm - a speck of the base's mesh, like the
3-point 0.02 mm loop that refused the default build), and refuse on the rest by name. The same run gave the arrangement
its first watertight base: the raw mesh's hairline slits (microns wide, 0.2-0.5 mm long) close under a pinch of 0.6 mm
(0.05 and 0.2 do not) - and a SLIT pass that merges by the slit's width, not its length, is the cleaner cure (31w).

## L106. A LONG SILENT KERNEL CALL IS DECLARED, NOT GUESSED AT: THE STEP SAYS WHAT IT IS DOING AND FOR HOW LONG, AND THE RUNNER WAITS THAT LONG - AND THE ARRANGEMENT'S SHELL CLOSES ONLY AFTER THE CHAIN'S OWN MESH FINISH.
Two findings of R4 run 5 (2026-10-01). (1) The runner kills a step that has printed nothing for the silence window (half
the cap, 10–180 s) - right for a stuck step, wrong for one generalFuse of a curved tool on 6,000 cells (186 s, silent by
nature: no print is possible inside an OCC call). the client, 2026-10-02: "Gate the heartbeat in if tasks run long and are
silent." So every long silent call in the chain is DECLARED (`kit\rebuild\_busy.py`: `with busy("the split by f22 on 6387
cells", TOOL_ALLOW):` writes {what, since, allow_s} to the file the runner names in KIT_BUSY and removes it after), and
`kit.py sh()` reads the declaration when its cap fires: while it holds, silence is not evidence - the runner prints its own
heartbeat line and waits; a call past its own allowance is killed with the allowance named (selftest_busy: seven cases). 31bq R6 / R7W
(B02 (b)): every declared call writes its interval to the runner's ledger (<log>.busy.done) when it ends; the hard ceiling (3x the cap) counts
only the time no declaration held, and silence is counted from the end of the last declared call, never across it (a real skin-build whose
declared sew and re-sew carried it past 3x its cap was killed on the ceiling while printing - R7W's CONTROL run at cap 70: 392 s, after its SKIN BUILD PASS line; the fixed kit's run at that cap died on silence in the undeclared _edge_gaps (M12), so the pair is not clean - verify-controls, 2026-10-22).
The declaration is a bound the step knows, never a blank cheque; a step that cannot say how long it may take does not
declare and is judged as before. Declared so far: the arrangement's splits, stage M's shell / unify / tessellation, the
reinsert's STEP 1 split, STEP 2 cut and fuses, STEP 3 ring sew. (2) The sequential split's cells share their faces (no face
on more than two cells) and the shell built from them is closed in topology - and its tessellation carried 30 open and 8
non-manifold edges in chains 1–7 mm long, the far side ~0.5 mm away, mirrored at the crown's side edges where the 47 tools
cross as a lasagna of thin strips: sliver faces the tessellator gives nothing or next to nothing. A base with those holes
is no base for KEEP (L105). The cure is not a lever on the split: stage M writes the RAW mesh and names the faces (the
face census), and `kit rebuild arrange-f` - the piece's own mesh finish on the arrangement's shell - closes the sub-mm
slivers and REFUSES what it cannot close. The gate is the finish's FINAL line, as for the piece.

## L105. KEEP-AND-WELD KEEPS THE BASE'S JUNK TOO: IT NEEDS THE ARRANGEMENT'S ONE-SHELL BASE, NEVER THE RAW CONTENT TESSELLATION.
R4 run 4 (2026-10-01) and the sandbox runs k8-k18 after it: with the join closed and manifold (the zipper), the repair still
ended `solid False` / 6-19 self-intersecting pairs. Measured on the base itself (`content_base.stl`, the fallback when the
arrangement's GeneralFuse fails): 17 self-intersecting facet pairs (the x- slot pocket's laminated wall, two sheets 0.1 mm
apart), 1,531 triangles INSIDE the material by more than h/2 (the vane shells running through the spine, 1,255 mm2, up to
3.8 mm deep), 1,180 triangles in air (flaps, sub-grid slivers). The full resample never showed them (a level set has no
inner sheets); the exact base returns them to the piece. Making the junk into cores fragments the piece (41 components,
dozens of unpaired loops - the junk runs to the window walls); a centroid-to-plane lamination test flags every curved
face's neighbours (7,001). The clean base is the ARRANGEMENT's (`arr_base.stl`: the kept cells' outer shell by face
identity, watertight) - and the arrangement is what failed on this window (47 tools against the ~30-tool fuse). So the
order of work is the chain's own: make the arrangement run (sequential single-tool splits, 31s; or split the window),
THEN keep-and-weld. The base's own self-intersections are checked before the field (`KEEP=1` prints them) and become
cores; a base with inner sheets is not a base for KEEP.

## L104. A RESAMPLE ROUNDS EVERY SHARP EDGE BY THE GRID; KEEP THE BASE'S OWN TRIANGLES AND RE-EXTRACT ONLY WHERE THE MATERIAL CHANGED.
R4 runs 1-3 of the loop (2026-10-01) failed STEP 4 three times at the same places - the rib-to-vane star (0.513 / 0.439 /
0.490 mm) and the slot-box faces (0.336) - with every CARD lever moved. Measured: a marching-cubes resample of the whole
window at h 0.2 cuts every sharp convex edge of the base by 0.15-0.30 mm (raw MC p90 0.131, max 0.281 on a section's
vanes; the grid field itself loses the tip of a 29° wedge by ~0.1; the quadric decimation adds up to 0.15 more); the
keep's FROZEN rule (0.15) then forces the vane-edge bins kept INSIDE the fillet, and the slot mouths' rounding shows at
the PROTECT faces. No blend lever reaches it - it is the resample. Two cures were built the same day: (a) a feature-edge
RESTORE that pulls the MC vertices onto the base's sharp edges afterwards (`_feat.py`) - it reaches the edges (0 samples
over 0.15 with the edge sweep) but the moves pierce their neighbours (75-522 self-intersections, the repair leaves the
mesh `solid False`); a dual-contouring prototype was worse (477 self-intersections, 44 non-manifold). (b) **KEEP-AND-WELD**,
the mesh route's own principle (`kit\mesh\_ccweld.py`, the client 2026-09-19: keep the body's original triangles, stitch where
the two agree): the base's triangles kept exactly outside the cores, the MC surface only inside them, the rims joined
by the kit's seam merge onto the base - measured (k6): sharp-edge samples cut over 0.15 fall from 422 to 93, all inside
the junction cores, max 0.254; the PROTECT voids and the caps are the base's own. (b) is the route (`KEEP=1`); (a) is
off and kept as the record. Three things the first runs taught: a changed component under 1 mm³ is not a core (a
one-node fill made a tangent ball whose rim the two meshes cut differently); every fade starts KEEP_M + 1 mm off its
wall (with the fade starting at the wall, both join refusals sat within 1 mm of a window wall: a thin slit on the aft
cap cut differently by the two meshes, a pinched fillet foot at the fore wall); a margin of 0.8 mm leaves open edges at
the seam (the rims run too close to the fillet feet) - 1.5 holds.

## L103. A STEP SCRIPT NEVER DIES ON A PRINT: WINDOWS FREECADCMD'S STDOUT IS cp1252 AND IGNORES PYTHONIOENCODING.
R4 run 1 of the burrito loop (the agent, 2026-10-01): reinsert STEP 2 crashed nine seconds in - `'charmap' codec can't encode
character '\u2212'` - on a say() that printed "local - region" with a Unicode minus. The runner (`kit_rebuild.py`) had set
PYTHONUTF8=1 and PYTHONIOENCODING=utf-8 for the child; freecadcmd's embedded interpreter on Windows ignores both and
hands the script a cp1252 TextIOWrapper. The fix is in the script, not the environment: every `rb_*.py` flips its own
streams on import (`sys.stdout.reconfigure(encoding="utf-8", errors="replace")`, the three-line prefix after the imports),
and selftest_leangates [30] proves the prefix under a cp1252 stdout. The two non-ASCII prints are ASCII now, but the
prefix is the rule - a status line must never be able to end a step. (Same class as T01: an exception swallowed by
freecadcmd exits 0; a print that raises exits 3 with the job's inputs intact - run 1 resumed at STEP 2.)

# RECOMMENDATIONS FOR THE FINISHING PASS (the agent) — STARTING POINTS, TO ITERATE AND TEST; NOT GATES (the client, 2026-09-30)

the client's words on these: "This should be recommendations to the agent to start. It needs iteration and test." And: "It should
be strongly recommended to agent to not change the method. failures should be logged." So:

* **DO NOT CHANGE THE METHOD MID-ROUND.** The chain's steps, their order and their levers' defaults are the kit's; a round
  runs them as they are and changes CARD levers only (WIN, PLANES, R, PROTECT, REDUCTION, and SEAM_MAX / KEEP_CELL /
  BOP_OK with a reason on the card). A step that cannot be made to work is a `kit failure --what --why --fix --signature
  --caught self` row and an inbox block to the kit maintainer (`kit inbox --append <file> --from "the agent <round>"`), never a
  rewritten script in the job folder. Round 3b ran 22 builds of a changing method; the kit saw none of them.
* **LOG EVERY FAILURE** the same way, build by build, with the number that exposed it. A failure nobody logged is a failure
  the next round repeats.
* The finishing pass (a low-face B-rep of the window, the client's goal) starts from these, each to be iterated and measured:
  1. **Edges are drawn on the KEPT faces, in their own parameter space.** An edge that bounds a kept design face lies ON that
     face by construction (its (u, v) curve), never fitted in 3-D and projected after - the agent's edges were 0.1-1 mm off their
     faces (B3/B4) and the big faces would not mesh.
  2. **The blends are the only new surfaces, each fitted THROUGH the fixed edges** it shares with its two neighbours (the
     boundary samples pinned, weight on the shared edges, B14/B16's lesson); where FreeCAD's own fillet succeeds on the
     kept edge, use it instead of a fit.
  3. **Every face is checked on its own and KEPT once it passes** (valid, meshes, `check(True)` clean on the face, within
     tolerance of the guide); the next build redoes only the failures, so the count of good faces only rises. A whole-window
     rebuild per lever is what made 22 builds (A12).
  4. **A failing face goes through a fixed repair list**, in order, and the list ends in a SPLIT: a looped edge trimmed, a
     sliver merged into its neighbour, a poor fit split in two along its long axis (B9/B10/B13). Splitting always ends with
     faces small enough to fit; a failure the list does not name is a stop-and-report, not a new lever.
  5. **Render 1-2 views after EVERY build before measuring anything** (the client's ruling, A1) and run `kit rebuild reinsert
     --set STEP=2` on the piece the moment it closes: the BOP gate (L100) and the PROTECT/seam census (STEP 4) are the
     cheapest judges of a fitted piece there are.
  6. The piece's caps are the body's own (`wall_caps.brep`, L97), copied, not refitted; and so is every PROTECT face the
     piece touches (A14).

A `kit rebuild keep` run on the chain's mesh piece shows the finishing pass WHERE the new surfaces are needed: only the
rebuilt bins carry new geometry; everything grey in `keep\` is kept as it is.

## L144. A KIT ROUTE THAT FAILS ON THE REAL BODY IS A DEFECT - DIAGNOSED TO ITS STEP AND FIXED, NEVER ROUTED AROUND; A WRONG TOOL IS RETIRED WITH ITS REASON HERE (2026-10-16).
the client, on the kit maintainer switching the chain blend from the rolling-ball corner patches to the older cone caps after the patches left the shell open:
*"if there's something wrong with the kit you should be fixing it. If it wasn't the right thing to use then generic instructions to future agents
should be updated. Failures are not to be ignored."* The switch had been offered under the client's own priority that morning (a successful build over
geometry believed exactly right) with a cause stated from memory ("the kit's face machinery with sub-mm edges") that no measurement had shown.
The measurement, once made (the UNSHARED COPIES report in sk_build, FIL_DBG=1: every edge two faces hold as two copies of one curve, both owners
named, and whether they were given one edge object or two), named two causes in the corner route itself - sub-mm closing edges at the corner-edge
contacts, and corner surfaces interpolated near their edges rather than through them (tolerances 1.4-8.8 mm, the face repair rewriting the
neighbours' wires) - and both were fixed at the source the same hour. The rule, for every agent: (1) a route that fails on the agent's job is diagnosed
to the STEP that made the failure, with an instrument that names it, before any other route is offered; (2) a priority on throughput orders the
work - the smallest fix that closes the shell first - it never decides whether a defect is fixed or recorded; (3) a route found to be the wrong
tool is retired here, in the card and in KERNEL_LESSONS with the measurement that retired it, so no later agent re-learns it; (4) a sentence to the client
or the agent that names a cause carries the measurement that showed it (a recorded process failure).

## L145. A FILLET CHAIN IS ONE BLEND BETWEEN MEMBERS OF ONE SENSE - WHERE A FILLET MEETS A ROUND THE CHAIN ENDS, AND THE KIT SAYS SO BY NAME (2026-10-16, kit 31bp fix 6b).
On the copy of the agent's b26 state the fore and vane-2 chains' common faces came out invalid ("self-intersecting wire", 31 free edges): their strips CROSSED
THEMSELVES at the junctions 37 | 48, 48 | 56, 35 | 51 and 51 | 97. Measured on the dumped strips: line 48 (and 91, 51, each in two legs) is a CONVEX 90 deg
edge between two ORIGINAL faces - a round - inside a chain of concave wall-foot creases. At such a junction the rolling ball changes sides: the two spines
never meet (the kit's convex / concave test read "convex", the ball centres 3 mm apart at the junction stations) while the two offset lines on the common
face converge and cross (the concave sign on that face) - the kit laid a corner arc across crossing lines. There is no rolling-ball corner where a fillet
meets a round; the kit now ENDS the chain there - both blends taper to that junction (or take the cap form where the taper does not fit: the round's side
face is a wedge narrower than t beside the junction, 31bl's cut-cap with an end line) - says it by name ("37 (a concave crease) meets 48 leg 1 (a convex
one): the crease's SENSE changes there - a fillet meeting a round is no rolling-ball corner; the chain ENDS at that junction"), skips the junction in the
contacts pass, and the foot stands as sub-chains with a point at each sense change. The agent's layout decision follows: a round between two original
faces is not part of a wall-foot fillet - leave it out of the chain (or decide it as its own round) if the foot is to read as one band. A second guard rides
with it: a convex reading of the spines yields to the two offset lines CROSSING on the common face before their ends (the mitre) - two blends of unequal t
can put the spines' crossing beyond a short leg's end. Generic: the sense of the crease decides which side the ball is on; a corner is made only between two
blends whose balls are on the same side, and a construction that assumes otherwise shows itself first in the common face's strip (a crossing or a gap) -
the strip is checked end to end and said before the face is built.

## L146. A BEFORE / AFTER OVERLAY NEEDS A COLOUR FOR "THE SAME" - A THIN NEW LINE ON A THICK OLD ONE IS READ AS EITHER (2026-10-16, kit 31bp fix 7b).
the agent's b27b trial: both cad-reviewers called blockers on the station frames at y -92 / -100 / -154, far below the region ("a whole flat plane moved ~12 mm",
"yellow only", "blue at another z with three notches"), and the kit maintainer had itself read the same frames as "continuous" the evening before (31bp fix 2).
Measured: the two bodies are IDENTICAL there - the kernel's sections 0 of 2298 points differ at y -154, 0 of 1914 at y -100; the picture meshes give the same
segments; and down a pixel column every such line is yellow-blue-yellow - the 3 px old line with the 1 px new line on it; a redraw from the identical data
reproduces the frames. The picture was right and illegible: a coincident line had no colour of its own, so each reader saw one colour or the other by the
viewer's resampling, and a 1 px line that lands on an exact pixel row vanishes at another scale. The station frames now encode "the same" explicitly - a
segment of one body lying on the other's section within the seam ceiling (SEC_TOL 0.15 mm, a lever never over 0.15; kitlib_render.match_segs) is drawn ONCE
in GREEN; only the differences are drawn, YELLOW old only / BLUE new only, 3 px each; the segments are cut at the review window (a long chord of a curved
face running to the body's far side differs between two meshes by its sagitta - false slivers 40 mm from the seam); the counts per station are printed and
recorded (STATIONS_<tag>.json: on b27b y -92 and y -154 100 % green, y -118 the edit itself); the trial brief gives the reviewers the key. Generic: an overlay
that asks "did this change?" draws the answer, not two layers for the reader to subtract; and a picture's legibility is judged by the reader it is for, at the
scale that reader sees it, never by the author who knows what is there. The same family as L142 (a picture that is evidence is made one way, proved).

## L147. A CONTROL THAT RAN ON THE WRONG NUMBER FOR SEVENTEEN DAYS: THE RUNNER'S BUDGET NEVER READ ITS OWN CLOCK ROWS, AND A SILENT LOOP WAS KILLED FOR IT (2026-10-16, kit 31bp fix 7).
the agent's review-body was KILLED at the cap (361 s, "silence - nothing printed for 313 s") on the b27b trial. Two defects under one symptom: the station cut
(kitlib_render.section_segs) looped in Python over every crossing triangle - 16 stations of two 1.46 M-triangle meshes, ~300 s, nothing printed - and the
runner's budget read "3.0 min (an unnamed step)": hooks\wallclock.table_budgets took only rows named `<script>.py`, so the rows the runner itself writes
after every run since 2026-09-29 (`kit rebuild review-body` 188 s typical over 16 samples, `kit rebuild skin-build`, `kit rebuild reinsert STEP=2` ...)
were never read, and EVERY kit rebuild step ran on the same 360 s cap whatever its clock said - the budget line printed on every run and nobody read "an
unnamed step" as the defect it was (a recorded process failure). Fixed: the cut vectorised (the
same segments on 17 of 17 test cases; 16 stations in 7.6 s against 6.2 s for ONE by the loop) with a line per station; the command rows read (review-body
budget 282 s, cap 564 s); the cap floored at the 360 s every step had, so a longer typical raises a cap and nothing lowers one. Generic: a budget's source
is checked by reading the budget line it prints - "unnamed" on a step whose row exists is a parser that cannot see the row; a long loop prints its progress
(L106: a long silent call declares itself or is judged on silence); and a kill at the cap names both the loop and the cap's source.

## L148. THE SIDE OF A BLEND'S OFFSET IS THE MESH'S OWN TOPOLOGY AT THE CREASE - A VOTE OF A FACE'S CENTROIDS IS UNDECIDED ON A FACE THAT WRAPS, AND A BORDER'S FAR END IS NO SIDE (2026-10-16, kit 31bp fix 9b).
the agent's b23 / b27b: the 77 / 56 blends (the vane-1 underside 1095 | the stem chamfer 1722, a 58 deg crease, R 1.5) stood 66 deg off both neighbours along
their whole edge and touched the vane underside (a 0.1 mm self-intersection). Measured on the copy: the blend's cross-section was a 248 deg loop of R 0.5
(chord 0.815 mm, sagitta 0.78) where the kit's own numbers - beta 58, t 0.84, sagitta 0.22 - describe a shallow arc of chord 1.48; the chamfer-side offset
line lay 0.835 mm off the original 1722 and 0.71 off 1095 - laid 0.84 mm BEYOND the crease instead of onto the face (the vane-side offset exactly on 1095).
The side had been a vote of the face's triangle centroids 0.3-3 mm from the crease: on 1722, which wraps past the crease (and which skin-wires had demoted
to a fill, so no projection onto its surface corrected the point), the vote was +46 of 178 - under the 50 % rule - and the fallback, the far end of a border
leaving the junction (10.4 mm away, curving), chose the wrong side. The side is now read where it is certain: each mesh edge the two faces share within 0.5
mm of the line has the face's far vertex on the face's side by construction (sk_lib.crease_side); the vote and the borders stand behind it and a
disagreement is said. On the way a wrong instrument (a probe's outward reference taken beside the looping blend read the crease as 122 deg) cost a fix
built on it - fix 9, the sheet-aware normals and the as-built angle between OUTWARD normals, kept as a guard (a recorded process failure). Generic: a
construction's side or sign is taken from the structure that defines it (the mesh's winding at the shared edge), never from a statistic over a
neighbourhood that can straddle it; and a fallback that reaches far from the place it decides for is no fallback.

*(fixes 9c-9g addendum, 2026-10-16 17:4x: THE CHAIN'S SHORT MEMBERS. the agent's stem-foot chain [56, 74, 77] - the nose 74 a 1.6 mm arc between two 17 deg bends, its side offset 0.4 mm
short of the corner edge at each end - did not close on the copy: fix 5's remedy for a short offset (the offset line turned about its far end) tilted the 1.6 mm member 17 deg,
the mitres missed it and the common face opened. The rolling ball's own answer: it rolls ON past a junction only where it runs into the next wall - a CONCAVE corner - so a member
short of the corner edge there is swept past the junction by the shortfall (the samples continued along the crease; not the width rule's) and laid again: the offset meets the
corner edge within the sweep and is cut there, the two surfaces overlap for the true mitre. At a CONVEX corner the ball pivots at the junction and is never extended (the 54
apex, a rounded V: extended legs ran into each other - a 6 mm mitre at 1.08 mm tolerance); a contact TARGET is turned onto, not extended toward; the decision is made in the
chain assembly's own first pass from the corner's sense (the first sweeps' spines and the crossing guard), BEFORE the contacts pass (which had already turned 74 onto its
neighbours' contacts and emptied its record); and a corner inside a crease is a KINK - the turn held by one or two steps - never a smooth arc however tight (the nose sweeps,
the keel V is refused). A turn gate at the junction (fix 9e) was measured unable to tell a rounded V from a bend and withdrawn. c2y: the agent's four chains close - 75 faces, valid,
tolerance 0.29, the stem foot one band with two true mitres 1.70 / 1.71 mm, its blends 1.3-2.8 deg off their neighbours. Generic: where a construction must continue past a
junction, the geometry that says so is the junction's own sense (concave: into the next wall; convex: pivot), decided where every member is known, and never a local statistic
of one member; a remedy that distorts a member in proportion to its shortness (a tilt, a ramp) is replaced by one that adds length.)*

## L149. A GAP IS FILLED BY BURYING THE FACE THAT MAKES IT - THE HOST'S OWN UNBURIED SURFACE STANDS FOR THE MESH AT THE CREASE, AND THE DESIGN NAMES WHAT IS BURIED (2026-10-16, kit 31bp fix 11).
the agent's c1 trial: the fore and vane-2 feet notched where the lip edges 48 / 91 / 51 stayed sharp. Measured on the original: the notch is the VANE'S OWN END FACE
(1734 / 1736, 1792 / 1794: 5 mm2, normal up) in a sub-millimetre slit under the crown underside - the lip convex, the grooves wedges of air, the three surfaces
not meeting at a point. No layout move fills it by itself: absorbing the end faces by points let the network lay the vane | crown border on the untrimmed
surfaces' intersection 2-3 mm outside both faces, and a bare FEATURES fold is a fill through the end face's own edges, which reproduces it. The kit maintainer
called it a new kit form ("the blend across a slit") and the finished model "not reachable tonight"; the client: "that is what drawing the lines and filling in a face
is for. No reason that idea can't be made to work ... Get the kit to select the right points, draw the lines, make the faces". The route in the process's own
terms: the end faces go INTO the crown's feature (the crown split fore / mid / aft so each piece is small), the lip is the vane | crown border, each foot is one
concave chain, and the chain entry NAMES the buried faces ("buried": [ids]) - the kit then reads the host face's geometry at the crease from the host's own
UNBURIED original surface instead of the mesh (whose triangles there are the end face's, facing the other way): its normals signed by the host's unburied
triangles, the offset projected onto it, the side from those triangles, the sense from the two faces' material directions (the mesh dihedral along the lip is
the buried face's and reads convex). Two measured corrections on the way: a merged face's recorded source is the feature master's original face and on one
side that was the buried face itself (the +x pieces got the roof, the -x pieces the end face - the master's order) - the host's surface is one of its OWN
unburied original faces, those nearest the crease first; and the candidates are counted per crease SAMPLE, as the share is. On the copy of the agent's c1 the lips
blend as concave 44 / 39 deg strips to the roof (the +x pair in fill4c; the -x pair once the source was the roof). Generic: a gap or slit the design wants
filled is filled by burying the face that makes it under the blend across it - the design says which face (a name in the record, never a guess from the mesh),
the host's own surface stands for the mesh where the mesh is the buried face's, and a merged face's "source" is checked against the buried list before it
is trusted. What the kit still cannot do here is a room problem, not a form: where the host's neighbour comes to a sharp wedge at the chain's junction (the
spine flank's end: 0.63 mm for t 1.11) the member's R does not fit - the point / border there or the radius is the agent's call, as the room rule says.

## L150. THE BLEND OVER A BURIED FACE LANDS AWAY FROM IT, A CREASE HAS ONE SENSE, AND TWO BLENDS OF UNEQUAL WIDTH MEET ON THE WIDER ONE'S CONTACT (2026-10-19, kit 31bq fixes K (2), N, U).
The fill of the feet (L149) left the -x lips NOT DECIDED (sides 0.62 / -0.65 against the +x twins' 0.62 / 0.65), and the first repair - "the host's offset points toward
the buried triangles" (fix K) - made every lip undecided: it flipped the +x hosts that fill4e had right. Measured on the copy: the buried face is the blended body's own
END (the vane's), on that body's MATERIAL side of the crease in the host's tangent plane, and the blend lands on the AIR side - the host's offset points AWAY from the
buried triangles (fill7f: all four lips concave 44 / 39 deg blends by the roof). Behind it the rule a crease cannot break: ONE sense - a buried host, with no topology
at the crease and only indirect votes, is read after the other face and takes the side that agrees with that face's own reading when it is clear; a twin whose sides
disagree takes its master's sense before any refusal. Then the junction of two blends of unequal t (the lip 0.53 against the chamfer 1.1, a 154 deg kink): their
contacts on the corner edge sat 1.67 mm apart, the contacts pass merged only up to 1.0, and a 26 deg planar SLIVER was left between the mitre edges that no rung spans -
the merge limit is a lever (CONTACT_MERGE_MAX 2.5) and the ANCHOR is the contact farther from the junction, the wider member's: the narrower one is swept again
OUTWARD onto it (the transition a variable-width fillet has); anchoring on the member that had met the corner edge pulled the wider blend's end inward and its wire
crossed itself (fill7j / 7k: "Self-intersecting wire; Unorientable shape"). Measured on the copy (fill9, 2026-10-19 12:35): the lines pass closed the shell with every blend for the first time on the fill route - 76 faces, 0 free edges, all 17 members made, the lips swept onto the chamfer's contacts; the solid then self-intersects 0.9 mm at one face pair (B16's gate holds it) - the next item. Generic: a sign rule is checked against the case that already worked before it ships
(the +x lips were the control and were flipped); a construction's fallback that moves a strip toward its own crease can cross its wire - move the narrower one outward;
and where two blends of unequal width meet at a kink, the wider one's contact is the junction.

## L151. A STAGED RETRY READS THE LATEST RECORD AND KNOWS WHAT KIND OF FAILURE IT SAW; AN INSTRUMENT SAYS WHAT IT MEASURED; A HELPER IS DEFINED ABOVE ITS CALLER (2026-10-19, kit 31bq B03 / B36 / B07, P0).
Three instruments of the lines pass lied in the same day. (1) The retry: its second stage carried the FIRST pass's free-edge chains and dropped two sound blends
(30 / 116) for a free edge on a chain that was no fillet line; it took every non-zero rc as "the shell did not close" when the retry had CLOSED the shell and the
solid's self-intersection gate had failed it - every blend lost, the message wrong; and its kept-lines list was bound to the name of the sharp FILES tuple, so after
every failed retry the restore raised TypeError and the step ended in a Traceback with the sharp piece NOT put back (fill7c-7e). Now each stage re-blames from the
latest record, a self-intersection / frame failure / crash is said as such with no retry by blame, a dropped member stays sharp in the retry child's kernel try too, and
the standing SKIN BUILD PASS line is printed last - the verdict the runner reads. (2) The wires' room line refused EVERY chain member (34 refusals, 0 'it fits') on its
own neighbour's border converging at the junction, while the build found the room: the room is now measured the build's way - along the offset direction on the face,
a border leaving the line's own junction held only against the offset point. (3) The BOP gate's parser matched CamelCase kinds the kernel never writes; FreeCAD 1.1's
check(True) says "Error in Face: BOPAlgo SelfIntersect", "Self-intersecting wire", "Unorientable shape", "No error" (a reversed-face solid) and nothing at all on an open
shell (probe_check_strings.txt) - the kinds fell through, {} <= cosmetics passed anything; a line no kind matches is now its own kind, never empty. And one of the
kit maintainer's own: a helper placed below the module-level loop that calls it ("name '_prm_on' is not defined") made every split fall back to the line's vertex for three
builds (fill7g-7i) - the sharp pass lost face 18 and the first reading was "the balloon test broke the sharp pass". Generic: a retry acts on the record of the pass it
retries, names the class of failure it saw, and leaves the artefact it promised; a refusal that fires on every case is the instrument's shape, not the geometry's (L143,
a recorded process failure); a parser of another program's words is probed on that program's real output before it gates anything; an edit script's anchor is unique at
its indentation, and a helper stands above its first caller - checked by the run, not by the compile.

## L152. THE WIRES' RULES OF THE OPEN-BUGS CAMPAIGN (2026-10-19, kit 31bq) - moved here from row 14b of THE SKIN ROUTE (B58: the row read as a table again).
31bq: EVERY DECIDED AND ADDED LINE IS MEASURED AGAINST THE PART - point-to-triangle on the source mesh, refused by name over LINE_OFF_MAX 0.5 mm (a straight chord across a curved border builds a face the part does not have; a trace follows the nearest surface point) (B19); the room line's governing samples clear of the ends by the UNTAPERED t, a chain member untapered, per leg where a split ends on the line, the buried faces' mesh not read (B36-B38); 31bq (2): the room is measured the BUILD's way - the width along the offset direction on the face, a border leaving the line's own junction held only against the offset point (fill7eb: every chain member refused on its neighbour's converging border while the build found the room); R7W (M7): each END of a room line decided as the build decides it - a CHAIN END (the next member's, or this line's other leg where a split cut it, with a corner edge on the side face) never tapered and its corner edge cut at the contact; a SPLIT END tapered; a free end MET on a face where the UNTAPERED offset passes within MEET_TOL 0.15 of the border leaving it (that border cut, not measured) and tapered unless BOTH faces meet (the PP form tapered every free end and tested its meet on the tapered offset: a junction met on both faces read 'lower R' where the build fits); each face's end decision in fillets.json (room ends); a trace INTERPOLATES its surface points (one cubic span had smoothed the keel's x-0 ridge away, 2.98 mm off) and a trace still off the part is said; a self-mirror chain's minus-side members take their plus-side twins as masters; an unmatched "buried" is said (B42); a line on the mirror plane is its own twin (B41); the `_add` / `_fillets` of a LINES file written for the LAST run's numbering are CARRIED - a fillet line by its two features and middle, an added line by its drawn ends onto the face that holds them now, the rest TO DECIDE (B06)
*(Decided at the close of the campaign: a traced line still over LINE_OFF_MAX is SAID, never refused - a trace follows its face's own surface where there is one and spans a
gap (a region the points dropped, the closed slot under the keel) straight; a NURBS fill's rise past its border's height range is said and recorded (balloon_note), never
refused - the look decides it (the client: pictures decide) - and since R7W A4 (10-22) the ladder RANKS by it: a try rising over the 0.30 mm print tolerance loses to a flatter one within the trade rim (THE INTERIOR RANKED; the vane plate's ~1670 mm3 balloon refused on the live kit); the room line is the wires' ESTIMATE and says so - the build's width rule on the built strip decides; R7W fix-wires-normals (10-23, R7Wz): the room line reads its NORMALS as the build does - a changed (or demoted) face's sheet smoothed along the line over FIL_SMOOTH_MM (a room lever now, carried from the live piece's build and gated with the others), an original face its own surface's normals however far it lies (no reach test, as the build; a JMOVE_MAX fallback the fixer wrote was REMOVED by its verifier - 22.5 deg off the build where it fired, and the build never reads that lever), the side still the wires' own vote (right 66 / 66 on the real records; the build's crease_side at a reflex border is F.16) - measured 35 / 35 verdicts and 54 / 56 meets on the two real jobs (the 2 the build's own wrong side), 29 / 114's width the build's 0.63 mm where M7 alone read 0.77 (the raw per-sample normals had read the changed face 25.6-28.4 deg off the build's at a sample - beta 83 / t 1.32 against 69 / 1.03).)*

## L153. A SLIVER UNDER THE CONSTRUCTION TOLERANCE IS REMOVED AT THE CONSTRUCTION TOLERANCE, BEFORE THE FACE IS BUILT - THE WIRE-CLEAN PASS; A CORNER IS TOLD FROM A GRAZE BY THE GROWTH LAW (2026-10-22/23, kit 31bq R7W R7Wn).
B26's v9 (the first SKIN BUILD PASS with both vertex balls) came back with the LEFT junction's frames stamped RENDER DEFECTIVE - 10 cracks up to 1.64 mm along c 52's upper
end - and the right junction clean. The render gate was right (L142: a torn mesh is no evidence): the mesher tore the face on a 0.0003 mm sliver - c's tapered offset reaches
the upper junction ALONG the border it ends on, 0.0002-0.0004 mm outside it for its first 0.03 mm, then opens away; the sliver was on BOTH sides (0.034 / 0.032 mm; faces 22 / 25
both 'Self-intersecting wire'), torn on one by the two sides' micron differences - the mesher's coin toss, not an asymmetry of the edit. the client: "Is there some form of rounding that
would make sense to apply to everything to avoid the tessellation issue? The kit has the print tolerance guidance but this is a more specific case that's root cause shows up
elsewhere." The rule, generic: a loop's geometry under the CONSTRUCTION tolerance (0.02 mm - the client's Q2 bound for edge and vertex tolerances and gaps, the kernel's sewing scale;
the 0.30 print tolerance is a DESIGN bound and never a construction one) is junk the face builder and the mesher cannot resolve, and it is removed at that scale BEFORE the face
is built, never patched in the mesh or the picture after: a GAP between consecutive edges is joined, a SHORT edge dropped, a GRAZE cut back to its foot on the neighbour and the
neighbour split there - every move said with its number, no geometry over the tolerance moved. Three instruments were tried for the graze and two lied: a band-run rule
flagged every 90 deg corner (the first 0.02 mm sample lies 0.02 off at a right angle); a band-median rule missed the real tangent departure (the run's tail lifts the median);
THE GROWTH LAW tells them apart - at a corner the distance from the shared vertex grows LINEARLY (median half the max, the first quarter a quarter of it), a tangent graze
departs quadratically or later (the v9 case: 0.0004 mm for 0.03 mm, 0.0012 at 0.05, 0.025 at 0.12 - median a tenth of the max, the first quarter inside the coincidence band
tol / 10). Measured on the vertex copy: the pass found the graze on exactly the torn face and its mirror, cut both back 0.018-0.019 mm, and the kit's own piece mesh went from 10
cracks to 0 (v10; v11 / v12 byte-identical), the solid valid, the frame exact. Three lessons rode with it: (1) THE RECORD IS KEYED BY THE LOOP'S OWN EDGE OBJECTS - the
pass's first form walked the loop through Part.Wire(...).OrderedEdges, which hands back COPIES of every edge but the first (new hashCodes, not isSame), so its record of
what changed never matched the caller's loop: no face across ever took the pieces, and on the real edit the cut face's new edges stood against the neighbours' untouched
originals - the shell opened and a blend was lost (R7Wn's red after-merge, 10-23; R7Wn3: a nearest-end walk over the input objects - Part.__sortEdges__ keeps them but drops a
gapped edge - and the record resolved by isSame); the match by GEOMETRY (the same object OR the same curve: length and midpoint within 1e-3, the 31bp sharing report's test)
stands behind it for a face that holds a copy; (2) the body's own wall edges are FROZEN - the frame is exact (L114), and a clean that re-ended or split one would break the frame
check; (3) a red after-merge is FIXED FORWARD, never answered by reverting approved work (the client 10-23: 'Most of those edits you are reversing were already approved. You are not
handling the failure correctly' - L144 / a recorded process failure one more time: the defect is diagnosed to its step with an instrument - here two hash probes - and fixed). Generic: a tolerance
names the scale at which geometry is cleaned, and the cleaning happens at the source (the loop) at that scale - a picture gate that refuses the torn result is doing its job
and points at the loop; a corner and a graze are told apart by how the distance GROWS, never by a single distance; and a rule written for a shared object is checked against
the artefact - whether the kernel handed back the object or a copy - before it ships.
*(R7Wn4b / R7Wn5 addendum, 2026-10-23: the pass's own product, ruled on. The cut-back leaves a border piece under 0.1 mm (0.0612 mm on qq, handed to face 28 and held by the split's piece 29F) that the kernel flags TooSmallEdge on two NON-cap faces; the client (11:2x, the plan's G4): "a" - such a pass-made edge, its geometry moved under the 0.02 construction tolerance and paired by the sew, is a COSMETIC like the caps' own edges: the reinsert gate clears its TooSmallEdge, named as the pass's, no BOP_OK owed - matched by the face's patch AND sub (the record carries both since R7Wn4b) and by the edge's own length within 0.01 where check(True)'s text says one, never by the patch alone (an Opus tester of the batch, test-R7Wn4: a match by patch had named another edge of the patch). The same tester found seven defects of the batch before it merged - a short edge the loop walk left out and stranded, a seam short edge handed as two copies, a census counting one graze twice, a neck closed into an invalid face, three messages - each fixed in R7Wn4b and pinned; none fires on the real pieces (qq: 0 SHORT, 0 GAP, one graze; B26: three single grazes, 0 cracks). Generic: a tolerance pass's own residue is ruled on by name - what it may leave and what the gate makes of it - and a gate's match is as specific as the record allows.)*

## L154. A CHAIN ENDS WHERE THE SIDE FACE'S CORNER AT THE JUNCTION IS REFLEX - NO ROLLING-BALL CORNER EXISTS THERE; A FREED END TAPERS FROM WHERE THE ROOM ENDS OR IS NOT MADE; A FACE'S SIDE OF A CREASE IS ITS OWN B-REP'S, NEVER A BORDER'S FAR POINT AT A REFLEX CORNER (2026-10-23, kit 31bq R7W W2).
On every live qq piece the two blends of the keel crease 56 failed check(True) ICOS + SelfIntersect at their junctions with 36 / 91 (M10). The cause, measured on the work copy W2 (probe_j56e / f, the frames
by the kit's visibility rule): at the junction the keel face 18's own sheet spans 0..261 deg from the crease and the corner edge c 50 leaves at 271 deg - the side face's corner at the junction is REFLEX. The
wall the ball would lean on turns away past the junction: member 56's side offset never meets c, and the kit RAMPED the whole offset onto the junction point, then pulled 36's end onto that contact too - both
blends zero-wide at the point, their surfaces folded. No rolling-ball corner exists there: not the mitre (the offsets diverge), not the vertex ball (three faces with a reflex one share no ball - c's spine 1.77
mm from the centre by the kit's own test). THE RULE: such a chain end is NOREACH - recorded with the angle, said once, not ramped; the chain ENDS at that junction as at a sense change (L145): both members
taper to it, the point stays sharp, and the kit says the way out by name (redraw the border so the side face has a wedge the offset crosses, or end the chain there on purpose). A freed end is swept again
down a LADDER: the taper; the taper FROM WHERE THE ROOM ENDS (the width rule names the crease sample where the side face runs out of room - the run-out lengthened to it; L141: where the room ends, the radius
ends with it); the cap - never at a reflex junction (its end line on the common face lands inside the chain-mate's tapered strip); a member that fits no taper is NOT MADE, dropped with its room line and the
way out (36 / 91 here: faces 19 / 17 are slivers of 0.00 mm beside the crease - lower R or make room). A freed end never cuts a MADE chain-mate's crease on the common face (the strip replaces it); a dropped
mate's crease is a sharp border met as a free end's. AND THE SIDE (F.16): a face's side of the crease was the mesh topology, then the centroid vote, then the far point of the border leaving the junction -
true only where the face's corner there is convex; at a reflex corner that border lies on the OTHER side (w2g1: the freed end of 114 took the dropped mate's crease as the reference, laid face 2's offset into
the wedge that is faces 3 / 17, and face 2 ran under the whole blend - a 0.32 mm 'self-intersection' that is the sagitta). An end that is or was a chain end gives no border reference, and an ORIGINAL face's
own B-rep decides its side outright (a point half t on the offset's side inside its trimmed domain, the other side outside; else the offset is turned and said). Measured: qq 71 faces valid at the first lines
pass, 15 of 17 made, the 56 legs clean points at the junctions (frames judged); the B26 job 75 faces, both vertex balls. Generic: a junction form is decided by the faces' own geometry at the point (convex /
reflex, the room beside the crease), never by a ramp that bends a line onto a point it cannot reach; where a form does not exist the kit says so and ends the chain; a reference taken from a neighbour's far
point is a guess that a reflex corner inverts - the face's own trimmed domain is the fact.

## L155. THE VERTEX BALL: THREE CONCAVE BLENDS OF ONE RADIUS MEET IN ONE SPHERE - THE SWEEPS STOP AT THE BALL'S STATIONS, THE CORNER IS THE SPHERE TRIANGLE THROUGH THEIR END ARCS; A CORNER EDGE WITHOUT THE CHAIN'S R IS A SINGLE BLEND AND THE MITRE, SAID (2026-10-23, kit 31bq R7v / B26, merged with the R7W W2 stack).
Where two members of a concave fillet chain meet on their common face and the CORNER EDGE leaving that junction carries its own fillet of the chain's R (fillets.json: the corner
edge's line decided at R), the three blends are ONE rolling ball: a sphere of R tangent to the three faces, its centre on all three offsets. The kit (sk_vertex: spine,
vertex_ball, sphere_fan; sk_build's vertex pass) finds the ball from the two members' spines and c's, STOPS each sweep at the ball's station (the members cut back, c's blend
started up the edge - fix 9f's extension past the junction is dropped at the vertex re-sweep: measured from the extended end the members had stopped 0.75 mm late, the ends 0.42
mm apart, a bow-tie), snaps the three shared contacts onto one point each (on the common face the two members' offsets' OWN CROSSING, both cut there - never a midpoint bent
beyond where the pcurves cross, which the tessellator reads as a 2-D bow-tie - R7v5; on the side faces a member's and c's), and closes the corner with the SPHERE TRIANGLE
through the three end arcs, its edges the fan's own boundary isos held by the neighbours (R7v6b: a loop whose sharpest corner is 10 deg is refused by the surface fitter - the
fan's isos are the edges). The side faces' strips become one L-shaped split each (the member's offset to the contact, then c's offset up the edge). A twin junction's contacts
are the master's REFLECTED (R7v3: the mirror plane, not a second measurement - the two balls came out 0.42 mm apart from two samplings). The first SKIN BUILD PASS with both
balls: 79 faces, valid (v9); the stack as merged: the B26 job 75 faces, valid, both balls, 17 of 19 blends (W2 w2b26h). What is NOT a ball: a corner edge whose fillet has
another R than the chain's (said - 'not the chain's R: no vertex ball there; it is made as a single blend and the corner is the mitre'); a junction where the side face's corner
is REFLEX (L154 - three faces with a reflex one share no ball; the chain ends there); a corner edge that ends on a WALL edge (L114: a fillet there would cut the body's own
face - refused by name). STILL OPEN, named by measure-B26: the ball's seams read 9-16 deg where the fan's boundary rows sit 0.016-0.033 mm off the sphere on the three arcs
(the interior rows are on it; the arcs put on the ball bring the boundary error to 0.0 deg median) and the blends' stations sit 0.05-0.12 mm off the ball's centre plane (2-3.5
deg more) - the next lever at the ball, with the frames judged. Generic: three blends of one radius meeting at a concave point have exactly one corner surface, the sphere; the
sweeps stop where the sphere says, the contacts are the curves' own crossings, the corner's edges are the surface's own boundary - and the twin is the master mirrored, not
measured again.

## L156. THE WIRES STEP PREVIEWS THE BUILD, AND A FAILED TRY IS CHARGED TO THE STEP THAT MADE IT (2026-10-29, kit 31br - the agent's REBUILD_JOB3, 13 builds).
the agent's restart of a section on the merged kit: nine single-change builds on a layout whose narrow underside strips were visible in its first layout frames; d8's feature merge
REMOVED THE KEEL and the look excused it (a PTS_DROP reason read as 'closing a slot'); d10-d12 failed at one face's SPAN in the sharp pass after 7-minute chains (one split
piece facing two ways - the agent had written the 140 deg normal turn down while planning and built anyway); d13: the 3-tries rule charged those wires failures to the POINTS and
skin-points crashed on a one-triangle spot. the client: *"the burrito process is close to working but it still fails to hit correct edits on the first try. Constant loops of creating
edits that shred themselves or balloon out of control are not acceptable"*; the gates approved on the proposal of 10-29: G1 the span preview, G2 the blend preflight, G4 the
restart rule, G3 lean. The kit now: (1) THE PREVIEW - skin-wires runs the build's own ladder and blend code as a child on the decided wireframe (SKIN_PREFLIGHT=1, the build's
levers) and ends before the shell: a face that cannot be spanned, a kit-made junction piece that fails, a fillet NOT made is named AT THE WIRES (the agent's d12 belly piece in 72 s),
and the wires judge refuses a missing or failed preview; `"sharp_ok"` on an entry accepts lines left sharp on purpose (qq: 36 / 91, the room) - never swept, kept in its chain so its chain-mates taper to its junctions (31bx X76). (2) THE TRY IS THE STEP'S: a SPAN
FAILED piece carrying added lines is a WIRES try at that face - three lock skin-build until the lines at that face change, the network changes or a preview spans it; a points
spot is charged only where the points were the cause. (3) The corner edge's single blend at a declined vertex ball is decided at the chain's end, only when its junction's
members were made - else sharp with the reason (a sweep beside an unmade member cut the roof slivers to wedges: PLATE BALLOONS 74 mm). (4) The guide clip, the via-point
measure (ADD_VIA_TOL), the sideways trace tube (TRACE_TUBE_MM; the depth is the agent's `"span"`), `"span": "face"`, look_at's subject by the z-buffer with a SECTION, the
vanished classes' `removed`, one page per step at the step. MEASURED on copies (the kit's development record): pvg2 (the agent's d12 layout) THE BUILD WOULD FAIL face 4 in 72 s;
pv3 (qq) PASS 25 faces / 15 fillets, 36 / 91 accepted sharp; d1d (qq, the full build) SKIN BUILD PASS at the first lines pass, 71 faces, 12309.0 mm3, the piece = the control
6d1c30a0 byte for byte; d6b refused a 7-point cubic 1.62 mm off its via points where the agent's real guide reads 0.13; d10c the keel trace 0.00 off its chord across 18 mm; the
preview's cost 72-163 s. Generic: a step that can run the next step's own measure cheaply runs it before the agent commits to a 7-minute build - the kit's own code, never a
re-implementation; a failed try is charged to the decision that made it (lines or points), never to the nearest spot; a decision the kit declines (a ball, a blend) is never
left silently as it stands - it is re-decided where every input is known (the chain's end) or left with its reason.
*(31br A3 addendum, 2026-10-30 - the agent's twin faces built unalike (d19b: the -x belly half a crumpled Coons patch, its +x twin a clean NURBS fill; the second review 'two sides differ'): the fill is not reflection-equivariant, so two mirrored loops spanned apart are a coin toss per side. The build now spans the MASTER (the + side) first and gives the twin its master's surface REFLECTED in the card's plane, laid on the twin's own loop (the wires exact mirrors, the wall edges the body's own - the frame exact), accepted when it holds the twin's rim no worse than the master held its own; a split face's pieces matched by their reflected midpoints; a twin whose master failed or whose rim comes out worse is spanned itself, said; TWIN_MIRROR=0 spans apart. Generic: on a symmetric edit the two sides are ONE decision made once and reflected - never two independent runs of a fitter that cannot promise the same answer twice.)*
*(31br A2 addendum, 2026-10-30 - the agent's restore deadlock: `kit rebuild restore --tag d15` put the layout and its ok back but not its LOOK record, which stayed the later build's; the judge's md5 check refused a REDO on an opened picture before its overturn
branch, and skin-rim was refused by the restored ok - no way out but undoing the restore (the agent did). Now a state carries every look record with the frames it lists (a verdict travels with the pictures it was judged on; L119 both ways: the later
build's frames go with its own saved state), a REDO / MOVE stands on the opened picture it cites whatever the frames record (an OK never does), and `--supersede "<why>"` on skin-rim re-makes a judged layout on the client's word (a decision from outside
the pictures), as it did on skin-labels for a kit update. Generic: a saved state is the whole evidence of a verdict, not the verdict alone; a gate that guards an acceptance never blocks a condemnation made on the evidence the rule asks for; and
the human's decision is a recorded way to re-make judged work, beside a defect and a failure.)*

## L157. A JUNCTION THE AGENT DECIDES IS A JUNCTION FOR EVERY STEP THAT DRAWS THROUGH IT - A CHAIN IS SIMPLIFIED PER LEG AT A SPLIT'S DECIDED END (2026-11-05, kit 31bw A5b; the agent's d14 / d19).
the agent ended two split lines at the TIP of a V-shaped border (the lid's wedge tip) - a decision that the tip is a junction. The wires step drew that border as ONE smooth curve (its rule: every chain
one line, arc or cubic), the curve rounded the tip off, the split's ends snapped 0.4-1.4 mm onto the rounded curve and the lip piece got an 11 deg sliver no surface spans; the preview failed it
70 s later. 31bu said the hairpin at the read and left the chain as it was (a refusal had false-tripped on the agent's d15 riser, a split 0.17 mm from a 173 deg apex, which builds). The rule now: where
a split's DECIDED end lies at a hairpin apex of the raw border (HAIRPIN_DEG within HAIRPIN_MM, the read's check), the chain is drawn PER LEG - each leg its own line, arc or cubic by the same
ladder (the open-chain fit of simplify_chain, extracted as _fit_open and called per leg), the legs joined at the apex into one edge with a corner (rung V(LINE+ARC); the record carries legs and
apex; the WIRE frame draws it pale cyan) - so the split's end lands on the kept apex and the build cuts the border there into two simple legs; a symmetric twin is redrawn per leg too, and an end
found only after the chains were drawn (a carried entry) is said for the next run. Generic: a decision the agent makes about the wireframe's topology (this point is a junction) binds every
later drawing step; a step that smooths it away has overruled the agent silently (L156: nothing the kit declines is left silently), and the geometry - not a refusal - decides whether the piece
between the legs spans.

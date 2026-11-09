# VOXEL_SMOOTH — HOW IT ACTUALLY RUNS

The long form of the `voxel_smooth` edit type (`kit howto voxel_smooth` prints the card; this file is the
procedure), the way `BURRITO_STEPS.md` is the long form of the burrito. **Nothing here is about one part.**
A project's own regions, face numbers and boxes belong in that project's round folder, never here.

## THE ROUTE IS IN THE KIT, AND ITS UNIT OF WORK IS A CROP (2026-09-24)

**The scripts live in `LEAN_KIT\kit\mesh\` — one copy — and run through `kit mesh <step>`** (`kit mesh --help`
lists the 22 steps and the gate tools). They grew in one project's job folders and ran through the burrito's runner;
the client, 2026-09-24: *"mesh editing should not be in the burrito."* What `kit mesh` gives every run: an environment
empty of inherited levers; `--env <file>` (a project's EXAMPLE CASE, named as such) then `--set`; the CC_ lever
census (`kit\mesh\LEVERS_CENSUS.md` — a CARD lever the run leaves unset is REFUSED by name, so a code default is never
the answer); `CC_WORK` = the job's `work\` folder, where every artefact, status file (`status_<step><TAG>.json`) and
log goes; `CC_EXTENT` / `CC_ATLAS` / `CC_ATLAS_MANIFEST` filled from the project's atlas (`kit atlas extent` records
the body's tight extent with the brep's md5 — run it once per model of record); the wall clock (`--row <name>` for a
step that needs its own row); a MACHINE SLOT for the heavy steps (extract, weld, gates: at most `mesh_slots` at
once, PID-owned, a dead owner's slot freed, never one under 60 s — `kit mesh slots`); and the whole-body gate.

**Route A, per piece, in this order — the body is never the operand of a step** (the client: *"the whole body being
processed multiple times ... is extremely wasteful"*):

    kit crop <base.stl> --box "<extract box>" --margin 6 --out work\<zone>\<name>_crop.stl      (numpy, ~1 s)
    kit mesh extract --job <J> --tag <T>  --env <RECIPE_EXTRACT.json> --set CC_SHAPE=<brep> --set "CC_BOX=..." ...
    kit mesh core    --job <J> --tag <T>  --set CC_BASE=<crop.stl> --set CC_PATCH=... --set CC_OUT=<blob.npz> ...
    kit mesh refine  --job <J> --tag <T>R --set CC_BODY=<crop.stl> --set CC_BLOBS=<blob.npz> --set CC_DEV=0.08 --set CC_OUT=<cbase.stl>
    kit mesh weld    --job <J> --tag <T>W --env <RECIPE_WELD.json> --set CC_BODY=<cbase.stl> --set CC_PATCH=... --set CC_CORE_BLOB=... --set CC_OUT=<cweld.stl>
    (the recipe json = the CC_* levers of the step as `{"CC_X": "value"}` - kit\mesh\LEVERS_CENSUS.md's `recipe` column lists each with its value; the core's own levers CC_SEL / CC_PNG and the weld's
    CC_PASSBAND / CC_SMOOTH stand behind the `...` above; no recipe file ships - a lever missing from the env is refused by name, which tells you the list; 31bx R4 D2)
    A COARSE SOURCE MESH shows a toothed rim at the core wall: the route was built on print-quality meshes (triangles at the recipe's 0.08 mm dev); on a CAD export with 8 mm
    triangles the weld's rim meets the base refined to 0.29 mm edges (CC_REFINE_L 0.3) and reads as a 0.09-0.22 mm saw-tooth with a 0.012-0.015 mm step and sliver triangles
    under 1e-4 mm2 inside the core (measured 2026-11-05 on a 60 x 40 x 10 box with a fin). Smaller CC_REFINE_L refines the base finer at the wall - finer teeth, not none (measured 2026-11-06
    on that box: CC_REFINE_L 0.1 -> 4082 wall edges against 1551, the teeth finer and still there, slivers under 1e-4 mm2 1161 -> 3656); `kit printfile` does not make a coarse
    source fine - its --dev 0.05 is a deflection, so a planar CAD export keeps its 8 mm triangles (the measured case was such a file). The splice's T-junctions at the crop wall are closed exactly (31bx) - a splice adds no open edge.
    (the per-piece gates on <crop.stl> against <cweld.stl>, with the same boxes)
    ... every piece the same; then ONE pass:
    kit mesh collect --job <J> --tag F -- work\final_manifest.json          (GOOD + reviewed pieces; weld + crop per piece)
    kit mesh final   --job <J> --tag F --set CC_BASE=<base.stl> -- work\final_manifest.json
        = kit splice --pieces (every welded crop into the base, the target cut fresh at each box and checked against the
          unedited crop, caps dropped, rims matched point for point) + the agent's repairs (spikes, needles, pinches, specks)
    kit mesh gates   --job <J> --tag F --set CC_RESULT=... --set CC_BASE=... --set CC_MANIFEST=... --set CC_OUT=...

Proved on R31's B45t (2026-09-24): crop 1 s, refine 2 s (13 s whole-body), weld 11 s; the same seam numbers as the
whole-body weld to four decimals (0.0872 / 0.0465 mm); every new triangle of the whole-body weld present in the
crop-flow result; outside the box the base's own triangles by index. The extract keeps the brep and its fine grid
(493 s measured; its time is the 87 M-cell grid, not the body). The margin must clear the extract pad (3) and the
weld's near-core margin (2): 6 mm. Put the walls through material or air, never along a face.

**Boxes, and a designed solid through the field (2026-09-24, a drawn rail added with `CC_UNION_STL`).** One box per
~50 mm of feature (a 145 mm box made a 2.7 M-triangle patch). The EDIT box 5 mm inside the extract box (the cleaning
reaches ~2.5 mm past it, and the core refuses an edit within 1.8 mm of a wall); the edit box ABOVE designed bores
(their roofs would be cleaned) and the box floor BELOW them (a wall through a bore); the box's outboard wall 1.8 mm past
where the addition meets the wall (the core's need); `CC_MATCHTOL 0.25` where a box wall crosses sharp exterior edges;
the gate box = the extract box (a gate box inside it on ALL six walls has no wall samples and is a FAIL; a one-wall
inset keeps five walls measured, which is what `_ccextract.py`'s CC_GATE_BOX was written for - but it is a DIAGNOSTIC,
never the fix: **a refusal at a wall is fixed by moving that wall, not by narrowing where the gate measures**; a
hand-written replica of the gate said PASS at 0.113 and the kit's own gate refused the same patch at 0.165 - use only
the kit's gate for a go decision). Pieces run in sequence, each
on the previous splice (MESH MODE: `CC_SHAPE` may be a crop STL, keepers and frozen regions from `CC_REGION_MESHES`).

**Where a box wall may NOT go, and what a refusal at one means (the R33-R35 round, 2026-09-25).** Before placing a
wall, check the project's recorded cracks and films (`MEASUREMENTS.md`; `kit atlas find` for the frozen regions): a
sub-cell crack or a ~0.25 mm film crossing a wall reads as a 0.4 mm reproduction miss at that wall - the RIGHT refusal,
and the fix is a few mm of wall, either way. The gate now prints, per zone, the over-tolerance samples PER WALL, the 3 mm
clusters with their boxes, and names the wall ("the misses sit on the x-min wall"); the status JSON holds the worst 50
with coordinates (`gate.where`). **A core refusal names ONE side ("within 1.4 mm of the x-min cap"): widen THAT side by
the shortfall + 0.5 mm, never every side** - growing all six by 3 mm moved three good walls onto a known crack and cost
36 min of extracts with nothing spliced. **A refused extract is deterministic: a runner never retries an identical
one.** **A frozen surface inside the edit box is closed by the field like anything else** (the cover seat's blind
bolt bore and 11 mm of gasket groove were the largest discarded regions of every chain-F status JSON, and the weld
would have plugged the bore): keep a bore or a groove OUT of the edit box, or hold it with `CC_KEEP_REGIONS`; the
extract now names, per discarded region, the nearest frozen region and its distance, and warns under 1 mm. Every
voxel piece states the defect's CLASS first (concave junction under 2 x `CC_CLOSE` - this route; a convex edge, a
ridge, a facet, a step, a fin, a lip - a drawn solid, `mesh_union`), and its box is drawn over the item's frame before
it runs.
The session stays open while a pipeline runs — `kit close` refuses its next `kit mesh` step. **And a DRAWN shape — a
rail, a slab, a boss, a drawn notch fill — does not belong on this route: `kit crop` → `kit union` → `kit splice`,
exact, in seconds** (EDIT_TYPES `mesh_union`; an exact arrangement, not the VTK boolean step V3 rejects). Through the
field it takes ~15 min a 50 mm piece and comes out a million triangles for four flat faces, because marching cubes
never knows a face is flat. This route is for BLENDING — a sloppy junction, a notch, a film.

**Route A2 — GROW AND UNION (built 2026-09-25; NOT YET RUN — the kit's development record. Nothing below is measured).** the client,
2026-09-24: *"take a copy of every other rework section. Grow it and smooth it and then union it back into the part for
a speedy cleanup of the remaining areas."* For ADD-ONLY smoothing where the core / weld gates bounce or speed matters —
no core, no refine, no weld:

    kit crop <base.stl> --box "<extract box>" --margin 6 --out work\<name>_crop.stl
    kit mesh extract --job <J> --tag <T> --env <RECIPE_EXTRACT.json> --set CC_SHAPE=<crop.stl> --set "CC_BOX=<extract box>"
         --set "CC_EDITBOX=..." --set "CC_GATE_BOX=<extract box>" --set CC_ADDONLY=1 --set CC_GROW=0.25 --set CC_GROW_SHRINK=0.15
         (+ the piece's usual levers) --set CC_OUT_STL=work\<name>_copy.stl
    kit union work\<name>_crop.stl --solid work\<name>_copy.stl --out work\<name>_union.stl
    kit splice work\<name>_union.stl --crop work\<name>_crop.crop.json --out <base2.stl> --into <base.stl>

With `CC_GROW` > 0 the extract moves the cleaned surface OUT `CC_GROW` x the edit weight (walls x edit box x frozen x
keepers, held on both sides, x lid) and IN `CC_GROW_SHRINK` x (1 - it): strictly outside the body in the edit zone,
strictly inside it at the walls and under every held surface, crossing it once where the weight is
SHRINK / (GROW + SHRINK) — a copy that coincides with the body is unioned as hair-thin slivers. The reinsertion gate is
report-only (per zone: how far the body stands outside the copy, and where the copy pokes through), SNAP is skipped,
and `<copy>.extract.json` says GROWN: never weld a grown copy. By construction the edit zone comes out `CC_GROW` proud,
stepping down to the body across the edit-box ramp, and every opening inside the edit zone narrows by 2 x `CC_GROW` —
keep bores and slots out of the edit box, or freeze them. After the union, look for ONE clean skin where the copy
crosses the body; a sliver patchwork there means the crossing is too shallow (raise `CC_GROW_SHRINK`).

Written 2026-09-21 from the SOLIDBOOL and SIDESTEP designs and from running all four steps on a real body.
Every number quoted is from that run and is named as an example, not as a constant.

---

## WHAT THIS METHOD HAS PROVEN, AND WHAT IT HAS NOT — read this before carding one

**Proven:** the placement and the exactness. The body's triangles come back bit-identical, the extents of
the selection are unchanged as an identity, and the whole thing runs in seconds where a boolean route did
not complete at all.

**Proven, and it is not this method's:** the BLEND. The build a user has accepted on this family of
features was made by **route A, rebuild-and-weld**, which is a working route and is not superseded by
anything here. Its one defect — a saw-tooth seam — is diagnosed and its gates are written (V3). What it
does not give you is the identity outside the edit.

**DISPROVEN: ROUTE B, THE DROP-IN, CANNOT PRODUCE A TANGENT BLEND.** Not at any cell size, not with any
mask lever. The appearance target is a continuous swept blend — reviewers reached independently for
*funnel* and *saddle* — leaving both parent faces TANGENTIALLY, with no visible start, no proud rim, no
terracing. The drop-in build put beside it was read as a bead. An earlier version of this file said the
causes were known and addressed below. **They are not, and that correction is the most expensive thing on
this page.** The rim is structural — V3 gives the mechanism. Four generations of tuning changed the
bead's size and smoothness and never its character, and the decisive test (a mask boundary sitting on the
TRUE tangent line, `add_open 0`) left the seam intact and flooded membranes down the vane faces for it.

**So NAME THE ROUTE AT V1, from the acceptance.** Blend → A. Identity outside the edit, rim acceptable →
B. Both → C, which combines them on a boundary the orchestrator chooses. **AND C IS THE ROUTE WHEN A AND B
BOTH FAIL THE SAME FEATURE** (the client, 2026-09-22) — that is what it is for, not a footnote. On the case that
settled it, A gave a true blend and 1,868 open+non-manifold against the body's 185 (unprintable) while B
gave +0 and a bead three independent reviewers failed: neither is shippable alone, and C takes the blend
from one and the identity from the other. The tool is the same in all
three; the gates are not, and finding that out at V4 is what cost four generations of tuning. What this
method contributes to EVERY route is the lump choice (V2): the only mechanism on disk that can spare an
opening while filling a notch beside it.

## THE SHAPE OF IT, IN ONE PARAGRAPH

Build ONLY the material that changes, as its own closed mesh, and drop it into the body's tessellation.
The body is never clipped, re-meshed or re-indexed, so "the extents of the selection are unchanged" is an
IDENTITY proved by an equality count, not a tolerance defended by a measurement. The deliverable is an
STL; the B-rep stays the model of record and is not edited. Four steps, two of them gated by a render
review. It is the burrito's region thinking with the fitter — the expensive, fragile half — removed,
because a print mesh does not need one.

---

## V0 — INVENTORY, before there is a box

    kit inventory <mesh.stl> --axis y --box x0 x1 y0 y1 z0 z1 --measure z [--step 0.5] [--min-pitch 5]

**How many of them are there and where?** Nothing in a dossier answers that, and every project so far
has had an orchestrator guess a repeating feature's count off a render. On 2026-09-22 that guess had
survived two sessions: what the record called two junctions were the LEFT AND RIGHT SIDES OF ONE
feature, so the previous round had edited one, not two, and three remained rather than "some".

**A triangle-density scan finds the EDIT, not the geometry.** This type leaves far more triangles
where it touched, so a density histogram returned exactly one feature — the one already done — and hid
the rest completely. The density-independent measure is how far material REACHES along another axis at
each station. A constant pitch is reported, and flagged: **a regular array is a designed feature as
often as it is a repeated defect** — check it against `kit frozen list` before carding any of them.

## V1 — SELECT

One box round ONE feature. **Cost is set by the box, accuracy by the cell**, so a tight box is nearly free
accuracy. Containment, not intersection, defines the area: a face is in it only if its optimal bounding
box lies wholly inside. (An intersection test pulls in every large skin that merely passes through.)

**The frozen-surface question, and how this type narrows it.** It cannot MOVE a frozen face because it
cannot move any face, and V4's census settles that over the whole body — so the usual "frozen faces
byte-identical in a before/after census of each frozen box" is discharged by construction, for every box —
for route B. Route A re-tessellates its core: a frozen face inside it is RECREATED at the end of edits (the client,
2026-09-22), measured back with `kit atlas recreated`, and delivery refuses until it is.
What remains is the other direction: **does the new material LAND ON something it must not touch?** No
census catches that. So list the faces the selection meets, and again the faces the TOOL comes within a
tenth of a millimetre of once V2 has built it. The second list is the short one and every face on it is a
question to answer before placing. Fusing TO locked geometry is allowed; changing it is not.

---

## V2 — TOOLS

    raw   the body's true signed distance over the box   (vtkImplicitPolyDataDistance + vtkSampleFunction)
    cln   raw, morphologically closed / opened / blurred  - the smoothed body
    dS    cln RE-SIGNED from its own occupancy by EDT      - see the trap below
    gain  raw - dS          > 0 where material is ADDED, < 0 where REMOVED

    ADD = {dS < 0} and {raw > 0} and {gain >= g_min}      REM = the mirror
    F_add = max( dS, -(raw + t_bury), D_confine )         F_rem = max( -dS, raw - t_bury, D_confine )

**Never derive the field from binary occupancy** — occupancy gives a voxel staircase. **And never take
`gain` off the grey-morphology field:** grey closing of a DISTANCE field moves the value in air wherever
the structuring ball reaches, including where the zero set does not move at all. Re-sign from the cleaned
occupancy first, or the mask comes out an order of magnitude too big and its lumps span the whole box.

**The state test, not the gain test, is what "added" means.** Air before and solid after. A point that is
still air can sit closer to the new surface than to the old one and pass a gain threshold; `g_min` is
there to trim the feather where the two surfaces nearly coincide, not to define the addition.

**Bury the tool INTO parent material by `t_bury`** so no tool face is ever coincident with a body face —
the overlap rule, in a field. **Bury it with the FIELD term, never a binary dilation**: the dilation's
staircase shows on the tool. And **dilate the confinement mask by more than the burial** before taking the
distance to it, or the confinement and the burial fight, the confinement wins, and the tool comes out with
no overlap at all — the coincident-face case every rule forbids. The symptom is a tool whose volume is
SMALLER than the mask it came from.

**THE LUMPS ARE THE POINT.** Label the ADD mask into connected components and choose them one by one. A
box says WHERE to rebuild; it cannot say WHAT to fix, and two features a few millimetres apart — one to
fill, one to leave open — are filled alike by any isotropic close. As lumps they are different objects.
Separation by radius and separation by height were both measured to fail; separation by connectivity does
not need a lever.

**SEPARATE WITH THE BOX AND THE LUMP CHOICE. `add_open` IS THE LAST RESORT, NOT THE FIRST LEVER.**

This is the correction that cost a rejected delivery, and it is the opposite of what a first reading
suggests. `add_open` opens the ADD MASK ITSELF and deletes everything thinner than twice its radius — and
**a fillet's own feather IS thinner than that.** Erode it and the tool is cut off short of tangency, the
cut becomes a visible closed seam, and the result is a BEAD sitting in the corner instead of a blend.
Twelve independent reviewers over 64 frames reached for that word unprompted, on a tool whose outer face
was a rolling-ball fillet **tangent by construction** — the fillet was never the problem, the erosion was.
Measured on one region: nearly half the addition was lost to the opening meant to separate it.

**A tight box is FREE here, and that is what changed.** Under rebuild-and-reinsert, shrinking the box made
the weld harder — the band got squeezed, the walls sat inside material, and the clip crossed several
pieces so the loops stopped corresponding. **`voxel_smooth` has no weld, because the body is never
clipped**, so the only cost of a box is cells and the only cost of cells is seconds. Tightening one
region's box by about a third in each direction cut the grid to under half the cells, brought a finer cell
inside the step budget, and **returned the same lump to within about a per cent**. So: **size the box for the
FEATURE, choose the lumps, and spend the saving on the cell.** An unwanted feature is excluded by not
being in the box, or by not being a kept lump — both free, neither touching the tool's shape.

Use `add_open` only when a wanted and an unwanted feature are genuinely connected inside the smallest box
that holds the work, and then expect to pay for it: `add_grow` dilates the KEPT lumps back into the
pre-open mask and restores some of the feather — measured, about a third of what the opening took — but it
 is a repair on a lever that is better not pulled. If the log says *sheets under N mm thick are gone*, read it as **the
feather went too**.

**Gates:** every tool closed (0 boundary + non-manifold), inside the selection, finite. **And a gate
REFUSES or it is renamed a report** — a step that states its own failure and then writes its artefact
anyway is worse than no gate, because everything downstream reads the artefact as the verdict.

**Census with `kit reach`, never with a centroid.** A triangle that spans out of a region has its
centroid OUTSIDE it — that is what spanning means — so the one defect a user can see is excluded from
every count by construction. A 151.8 mm blade stayed out of a 2,966-triangle census at every threshold
for exactly this reason. Select on ANY VERTEX in the box and rank by reach, with the control taken from
the SAME document: a foreign base turned an unambiguous 6.77 mm into a mushy 11.32 mm.

**Render with `LK_OWNERMAP=1` and use `kit pick`.** A frame that cannot name its own triangles is
not an instrument. Naming a defect by PIXELS and getting the exact triangles back removes the step
where the subject of a picture is inferred — which was the single root cause of three separate
mis-attributions in one session, each of them the wrong subject measured confidently.

**The extent gate measures the EXPOSED surface, never the bounding box.** The tool is deliberately buried
in parent material, and buried material cannot change the selection's extents — the extents are a property
of the outer surface. A bbox cannot tell burial from protrusion, and on 2026-09-21 that refused a live
build for 0.30 mm of overhang everyone assumed was burial. Test the points where the body's own field is
positive: those are the exposed ones, and only they count. **Make the refusal carry its evidence** — how
far past the wall, how far outside the body, and the test's own resolution — because a refusal that cannot
be checked gets argued with instead of acted on. When the same run was re-tested properly the overhang
turned out to be real material standing 1.3–1.7 mm outside the body: the gate had been right and unable to
say so. A tool whose EXPOSED surface reaches past a wall is a SELECTION fault — widen the box; never trim
it silently and never move the number.

---

## V2b — SMOOTH THE TOOL. This step is free here and was forbidden under the old method.

Marching cubes terraces: the tool's exposed face carries steps of one cell, and they are
plain in an unpainted frame. Halving the cell is not the route — 0.06 mm is of order 100 M cells even on
a tight box.

**Smooth the TOOL instead, and note why that is allowed.** Under rebuild-and-reinsert, mesh smoothing
moved the BODY's geometry, so it had to be fought with boundary pinning and it still left whiskers along
the seam. Here the tool is a SEPARATE CLOSED SHELL and the body's triangles are never touched: the census
identity is a property of the PLACEMENT, not of the tool's shape. So the tool can be smoothed freely.
Exactly two things can go wrong and both are checked, not trusted:

* **the shell opening** — boundary and non-manifold counts before and after;
* **the burial shrinking below the overlap rule** — re-measure the buried depth after smoothing, because
  a smoother pulls the buried face toward the exposed one.

The tool is closed, so there is no boundary to preserve and boundary smoothing is irrelevant. Leave
FEATURE-EDGE smoothing OFF: the tool's own sharp arrises, where it meets parent material, must not be
rounded away into the burial.

## V3 — PLACE, IN THE MESH

**THREE ROUTES END THE SAME TOOL, AND ALL THREE ARE GATED. NONE SUPERSEDES ANOTHER.**
V2 builds the tool once. What differs is how it is ENDED.

* **A — REBUILD AND WELD.** Re-express the region's surface from the field and weld it back: classify the
  body's triangles against the tool's implicit (all three vertices outside → keep bit-for-bit; all three
  inside → drop; clip ONLY the straddlers, in their own parent triangle's plane), clip the tool to the
  outside of the body, and insert each tool rim point into the body's clip-generated rim edge so both
  sides index one vertex sequence. **This is the route that produced the build a user accepted.** It gives a true blend and one connected region,
  and pays by re-tessellating the region, so the baseline moves and mesh health goes up. It ran for a
  long time with NO gates, which is why its one defect reached a delivery — that is an argument for
  gating it, not for replacing it. Its five gates are below.
* **B — DROP IN.** Lay the tool on as a second closed shell. Seconds, and the body is bit-identical
  everywhere. It leaves a rim, structurally (next block). Gated already.
* **C — COMBINE.** Take the edited surface from A and everything else from B, joined on a boundary the
  **ORCHESTRATOR names**. Gated by `kit stitchband` and made by `kit stitch`; both exist.

**Run A and B off one tool.** Their frames are directly comparable because the tool is shared, so the
only variable between them is the ending — which is the one thing worth looking at, and the reason to
run both rather than pick one. Route C then needs no third build; it has its two inputs already.

**WHY ROUTE C's BOUNDARY IS THE ORCHESTRATOR'S CHOICE AND THE KIT WILL NOT MAKE IT.** A stitch is easy
exactly where the two builds already agree: put the boundary out on quiet surface clear of the edit and
the two rims are nearly coincident, so the join is a short zip between matching geometry. Put it through
the edit and you are stitching across a shape change, which is the hard case and the one that shows.
Only a judgement about the PART knows where that quiet surface is. So the kit measures the choice
instead of making it:

    kit stitchband <A.stl> <B.stl> --band x0 x1 y0 y1 z0 z1 [--tol 0.15] [--anyway "<why>"]

**0.15 mm IS A CEILING, NOT A DEFAULT** (the client, 2026-09-21): a seam to other geometry does not ship over it.
`--tol` below it is honoured; `--tol` above it is refused; **`--anyway` does not reach it** — an override
that can raise a ceiling is not a ceiling. `--anyway` covers the zipper ratio and the choice of band,
which are judgements. The deviation is not.

**THE BAND IS A SLAB, and it goes on ANY geometry.** Give a box at most **0.30 mm thick in ONE of x, y
or z** — whichever suits the seam — and as long as you like in the other two. Nothing here assumes the
surface is flat: a slab meets a curved surface in a curved ribbon and the sampling follows it, through
fillets, round ribs, across holes. **Samples are taken ON the surface**, by clipping each triangle to the
slab, not from the mesh's vertices — so a coarse patch that puts no vertex inside a 0.3 mm band is still
measured, and a surface is never reported absent because of how it happened to be cut up. A box thick in
all three directions is refused: it averages the agreement over material that is not the join, and a step
at the join disappears into it.

It reports the worst deviation and the sample-count ratio, refuses a band one build's surface does not
enter, and does not judge the stitch: render it, put the band in the frame, name it in the caption, judge
that frame on its own.

**ROUTE A, AS OF the agent'S DIAGNOSIS (2026-09-22, the project `jobs\DIAG_V2V3\FINDINGS.md`; its junctions are named V2–V4, which are not this page's steps).** Junction V2 welded and
junctions V3/V4 did not because the extract's inside/outside flipped near the body mesh's cracks and built 6–12 mm lumps in open
air, the core cut them, and junction V3 was welded onto a base that already carried junction V2's weld. No lever was at fault. The
card's nine gates are in `EDIT_TYPES.md` (voxel_smooth, route A); what each one IS in the code:
1. **Sign by vote** — `_ccextract` corrects the nearest-triangle sign by three axis ray-winding counts wherever
   the sample is further than `CC_SIGNFAR` cells from the surface; `sign_check` in the status file.
2. **Reinsertion gate refuses, on surface the edit did not touch** — zone model `CC_EDITED_EPS` (0.02 mm).
3. **Fragment and open-edge count on the patch, BEFORE anything is welded.** More than one piece, or any open
   edge, and the mask is too TIGHT — the opposite of the intuition. No generic percentage threshold.
4. **Core by rule — the EDIT ZONE measured both ways (`kit mesh core`, `_blobcore.py`), grown `CC_M` 1.5 mm.** Edit =
   patch points more than `CC_TOL` off the body; REFUSED within 1.8 mm of the capped wall or where a disagreement sits
   under the wall; `kit mesh grow` / `pair` / `island` grow it over far points, narrow it between neighbours, take short
   rim loops in. (`kit coreplace`'s ellipsoid measured only material the edit adds and refused on the real part - the agent 2.18.)
5. **One unchanged base** — `_ccweld` refuses a chained body (L12); a `kit crop` of the base, or its refined crop, IS
   an unchanged base (provenance by md5); `CC_CHAIN_OK` records the client's exception.
6. **The join is seammerge (`CC_JOIN=seammerge`, `_ccseam.py` in the kit, a CARD lever)** — loop-to-loop matching with
   explicit ordered partners, each rim refined by the other's points, welded by identity, no ribbon, the 0.15 mm ceiling
   per pair, a patch loop with no body partner is a hole and refuses; 3-4 s. (`kit seamweld` / `weld_rims`, the older
   verb, could not close refined rims - the agent 2.19.) **The old gate 2 (rim counts within 3:1) is RETIRED** — junction V2
   welded clean at 20:1 and 50:1. `CC_JOIN=zipper` + `CC_ZIPPER_WHY` = comparison only.
7. **Never resample a loop** — see the trap below.
8. **The reach mask is driven by the LUMP CHOICE, not the box.**
9. **The seam to other geometry does not ship over 0.15 mm** — `kit stitchband <welded result> <the original
   body> --band <a slab on the seam>`. The ceiling may be reduced, never raised.

`kit seamweld <a.stl> <b.stl> --out <r.stl>` is the same join as a verb, for halves `_ccweld` dumps with
`CC_DUMP_PARTS`. Measured on route A's own shape at 8:1: the sparse rim refined 96 → 432 edges and the seam
contributed 0 boundary and 0 non-manifold edges; on the real part it runs in 1–23 s and names the loops it
refuses. The body's own open ends are left alone: an orphan loop is a mismatch only when the other side has an
orphan near it.

**`CC_KEEP_REM` / `CC_MINVOL_REM` — THE REMOVAL HALF GETS THE SAME LUMP CHOICE AS THE ADD HALF, and needs
it more.** The asymmetry is structural: a `close` fills concave voids as a few connected blobs, so ADD
arrives as a handful of lumps; an `open` shaves a thin skin off every convex feature in the box at once, so
REM arrives as thousands of specks — 2,099 components of dust on one measured region. The half that arrives
as dust is exactly the half that cannot be used without selection. Past a couple of hundred components with
no ranks named, the step says so: **that is not a cutter, and a named feature that has to come off is a
`cutter` job, not a morphological one.**

**AND A FAILURE ON ONE TOOL MUST NOT SUPPRESS THE OTHER.** ADD and REM are independent products of one
field. A run with a perfectly good removal mask produced NO FILE because an unrelated ADD lump was clipped
by the box wall. Record the failure, build the other tool, exit non-zero at the end.

**Route C's gates are A's 6, 7 and 9 — the same join, the same ceiling, the same command — plus:** the census still
holds OUTSIDE the band, to the vertex, because that is what route C is for; and the band is in the review
frame, named in the caption, judged as a frame of its own.

**AND THE STITCH ITSELF IS WRITTEN:**

    kit stitch <a.stl> <b.stl> --plane z5.0 --out <result.stl> [--tol 0.15]

A's surface on the plus side of the plane, B's on the minus side, one mesh out. **It REFINES, it does
not ZIP** — and that is the whole difference. Each side's rim is refined in the mesh by the other side's
points: every added vertex SPLITS an existing rim edge and is shared with the triangle that owned it, so
nothing is orphaned. The two rims are then welded, meeting in the middle. **The seam costs no ribbon
triangles at all**, which is exactly the defect a zipper leaves. Measured across rims of 192 and 24 edges
— 8:1, the fan case — the sparse rim refined to 192 and the seam contributed **0 boundary edges and 0
non-manifold**, with a worst vertex movement of 0.0856 mm. A rim pair further apart than `--tol` is a
REFUSAL, not a stretch, and `--tol` cannot exceed the ceiling.

**THE RIM IS LOOPS.** A boundary crosses a cylinder in one loop and a real part in many; loops are matched
to LOOPS by optimal assignment, and a loop with no partner stops the stitch and is named. A bag-of-points
match pairs across FEATURES and hides the problem. The mesh's own pre-existing open edges - a production
body has hundreds - are excluded from the rim, computed on the welded input.

**WHAT A REFUSAL USUALLY MEANS ON A REAL PART, measured 2026-09-21.** The approved build of a junction
against its own base body matched nine loops a side exactly and refused on ONE spare: a 0.2 mm edge lying
on the edited build's surface and 9.3 mm from the base body's. A census of that region explained it - 8,665
triangles with an aspect ratio over 20, longest edge 151.8 mm, 1,652 of them bridging more than a
millimetre clear of the part. That is the ZIPPER FAN the retired zipper made and route A's seamweld join now prevents,
in a build made before those gates existed. **So a route C refusal is usually a verdict on its INPUT.**
Read the loop that failed before touching the boundary.

**One caveat to card honestly:** the plane is a PLANE. A boundary that has to follow something other than
a flat cut needs the same operation applied to several planes in turn, which composes but has not been
run. And this has been proven on synthetic bodies, not yet on a real part.

**WHY THE DROP-IN CAN NEVER BLEND — the mechanism, measured 2026-09-21.** The tool's outer face is the
closed field's own surface, a correct rolling-ball fillet; that was never the fault. But the tool has to
STOP, and where it stops is the edge of a voxel mask. So at the rim there is ALWAYS (1) **a step of order
one cell**, because a mask boundary cannot land between cells, and (2) **a facet-density discontinuity**,
because the tool's skin and the body's skin were tessellated by different processes at different densities.
A tangent blend has neither. Twelve independent reviewers over 64 frames, none told what the others said,
all reached for "bead"; one named the mechanism unprompted — an abrupt jump in facet density at a sharp
line is the signature of a separately-tessellated add-on, where a tangent blend keeps a comparable facet
size and shows no such line. **No lever reaches this.** Do not spend a generation of tuning re-finding it.

**THE WELD TIER'S OWN SEAM — every link diagnosed, the last one unwritten.**
* **A patch that comes back in FRAGMENTS means the mask is too TIGHT**, which is the opposite of the
  intuition. A dozen-odd pieces with open edges everywhere at a narrow reach; widening the reach and
  softening its ramp gave 0 boundary edges, CLOSED, one region, and cut the welded health delta by most of
  itself. Read the
  FRAGMENT COUNT and the OPEN-EDGE COUNT the extract prints. **There is no generic percentage** — the
  "5–19 pct of cells open" note is one region's write-up and must not be promoted to a threshold.
* **A zipper FANS between loops of very different point counts, and the fan IS the seam** — measured at
  better than 20:1, ~23 long thin triangles off every sparse vertex. That is why the zipper is retired and the
  join is `kit seamweld`; the 3:1 ratio that used to gate it never separated good from bad (junction V2 was 20:1 and 50:1).
* **Resampling either loop to fix the ratio is a trap that looks like it works.** The ratio goes to about
  1:1 and the ribbon loses two thirds of its triangles — and **open edges go up by more than an order of
  magnitude**, because the seam vertices are not free to move: they ARE the two boundaries and the ribbon is
  stitched by exact vertex identity, so new points coincide with nothing and every original boundary edge is
  orphaned. Refine the SPARSE side in the mesh —
  the rim-point insertion above — and never resample.
* **Ruled out by test, each leaving the seam byte-identical:** the loop-pairing tolerance (6.0 and 14.0),
  the patch decimation (0.90 and 0.55), the extract's cross-fade band (4 → 7 halved the patch's open edges,
  7 → 11 changed nothing at all), and the patch's own closure.

**THE TOOL'S WINDING IS A REFUSAL, NOT A SILENT REPAIR.** Marching cubes on a max-of-implicits can emit it
INWARD, and a slicer reads an inward shell as a VOID — it would mill the new material out of the part.
Watertight, manifold, single-region and a clean census all pass on an inverted shell, so no other gate sees
it. It has fired on 5 of 5 placements on one body, which is an argument for fixing the step that emits it,
not for flipping it quietly: a silent flip means nobody learns, and a shell that is inverted ON PURPOSE (a
void) gets corrupted without a word. Refuse by default, with two named overrides that each say what they
did — one that corrects it, one that ships it as-is — so neither can happen by accident. Same family as
the spike gate: a gate that does not look at the quantity cannot see the fault in it.

**Two routes that are NOT the answer, both measured:**
* A **mesh boolean** (`vtkBooleanOperationPolyDataFilter`) on a local crop plus the tool: a thousand-odd
  boundary edges added, **a dozen connected regions where the body had one**, a fifth of the new material
  lost, and vertices missing from the untouched remainder. Three seconds, wrong four ways. **And "the crop
  was too small" is disproved, not untested:** MORE remainder coordinates were lost at a wider margin than
  at a narrow one. The filter re-triangulates whatever it touches.
* A **B-rep boolean** (cut + fuse through the kit's own replace): did not complete in a 174 s call even
  for a 2,562-face piece, and crashed the interpreter on the full tool. Its manufactured-volume gate also
  assumes an ABUTTING piece and misreads a deliberate overlap. Solidifying a decimated tool gives a shell
  that is CLOSED but INVALID, and deleting its degenerate triangles OPENS it — that is not the repair.

---

## V4 — PROVE AND DELIVER

**The census is an equality count over the WHOLE body** — every vertex bit-identical, reported as N of N
with a hash. Anything short of N of N is a defect, not a tolerance, because this method never clips the
body.

**Every mesh-health number is a DELTA against a control built the same way, read on the WELDED mesh.** A
per-face tessellation is a soup — around a third of its vertices are duplicates and its raw boundary count
measures the tessellator, not the part. Expect +0 boundary and +0 non-manifold.

**The spike gate is not optional:** every result vertex inside the body's own bounding box and finite.

**WALL THICKNESS AGAINST THE PROCESS — the gate a print deliverable actually needs.** A feature is a
print problem when it is thinner than the process can form, and that is a number, not a judgement from a
picture. Fire a ray from just under each triangle's centroid along the inward normal and measure where it
leaves the solid again: that is the local wall thickness. Report the distribution against the process
minimum from the project's own print rules — and **count needle triangles separately**, because a needle
is a meshing artefact and a thin wall is geometry, and their fixes are unrelated: one is re-meshed away,
the other has to be made thicker. A tool that adds material can still leave a blade at its rim.

**THREE FRAMES ANSWER THREE DIFFERENT QUESTIONS. Do not substitute one for another.**

| the question | the frame |
|---|---|
| is the shape right, does it read as a sweep or as a lump stuck on | the orbit sweep, uncut, camera-framed |
| **how BIG is it — radius, tangency, how much bridges the corner** | a **section ACROSS the run of the feature**, viewed down the slab normal, drawn as filled material with a closed outline and a mm grid |
| what is going on under a skin that hides the feature | a **3-D cutaway**: one named plane, split and capped, loop counts in the caption |

The second is the one that gets skipped, and skipping it is how a build gets accepted at 0.04 mm/px where
a 1 mm and a 3 mm bead are the same handful of pixels. **Radius lives in a section and nowhere else.** A
`CANNOT-JUDGE` on an orbit frame is not a defeat — it is the gate telling you to go and cut the section.
And the section is drawn against the APPROVED build, never the untouched body: a comparison with the
original cannot show a regression against something already accepted.

**Say plainly what "one part" means.** One FILE and one mesh object: yes, from the drop-in tier. One
connected watertight shell: no — and on a body whose own welded tessellation already carries thousands of
boundary edges, welding the tool would not deliver one either. A slicer unions overlapping shells, and the
burial is what gives it the overlap to resolve. If a single watertight solid is ever required, that is a
whole-body mesh repair as a separate final pass, and it rebuilds every triangle — so the census identity
is forfeited by design, which is acceptable only because the B-rep stays the model of record.

---

## THE REVIEW, WHICH IS THE ACCEPTANCE

Gated at the choice of lumps and at delivery, through the review gate. `run` does not mean skip.

**It runs FAIL-FAST, in two phases** (`kit review`, 2026-09-21). Phase 1 is the LEAD frames — the views
you have already decided matter, on the card's box — and each is judged on its own:

    kit review <before> <after> --out <dir> --box x0,x1,y0,y1,z0,z1 [--lead f1,f2]
    kit review --judge <dir> --frame <name> --verdict pass|fail|cannot --note "what you saw"
    kit review --sweep <dir>

A `fail` ABORTS: the sweep is never rendered, because 26 more frames of a build already known to be wrong
buy nothing. **Diagnosing that failure with extra views is UNGATED** — capture whatever the fix needs.
A `cannot` is not a pass; it means the frame could not settle it, and if every lead frame comes back
`cannot` the review is VOID, which is a different refusal from a failure and must never be reported as
one. A `fail` or `cannot` without a note is refused: a verdict with no observation is not a review.
A build on its way to being accepted is still seen from every angle — the sweep is not skipped, only
withheld from a build that has already failed.

**The review reads a MESH as well as a B-rep** (`after=<tool.stl>`, and `a.stl+b.stl` concatenates), so a
drop-in tool is reviewable BEFORE it is placed. A review dir that already holds frames is refused —
frames carry no tag and would overwrite the evidence behind an earlier verdict.

**NAME THE LEADS. The kit's default set is body-wide and knows nothing about your box** — on an
under-spine feature 3 of 5 defaults came back `cannot`, the sweep was released by the two that happened to
see something, and twelve reviewers then failed the build on sight. So `--sweep` now REFUSES when half or
more of the leads returned `cannot`, and says whether the set was the default or your own. Half the leads
blind is evidence about the frames, not about the build. Lead with the views you have already decided
matter; `--lead-ok` overrides and is recorded.

**A CUT FRAME ON A BODY LIKE THIS IS NOT SOLID, AND THE CAPTION NOW SAYS SO IN THE PICTURE.** Measured at
one plane of a production body, most loops stayed OPEN. A body carrying thousands of boundary edges cannot close
most of its section loops, so a cut face is not material and **wall thickness must never be read off one**.
The caption carries both counts and the warning where the reviewer is looking, not in a JSON field.

* **Never crop geometry to frame a picture.** Frame with the CAMERA. A bounding-box crop makes the whole
  silhouette an artificial boundary and paint on the cut faces reads as an edit stopping at an edge that
  is not there.
* A cross-section is allowed and useful, but it is **ONE named plane placed clear of the subject**, and
  the caption says so. A feature under a skin is invisible from outside and from straight below.
* **A colour boundary is paint, not geometry** — one colour per triangle, so a classification boundary
  zig-zags and reads like a torn edge.
* **Open every frame and write the verdict after looking.** A caption that explains away a discrepancy is
  not a review. If the render does not show what you expect, the render is the finding.
* **When a reference build exists, it goes IN THE FRAME.** Once something has been approved, new-against-
  ORIGINAL cannot show a regression against it. The pair is OLD against NEW.
* **GATE THE HEADLINE QUANTITY AGAINST THE REFERENCE.** A build that makes HALF as much of the exact thing
  being made as the approved one did is a report, not a ship — whatever the frames look like. That ratio
  printed in the log of the build that was rejected and was read past. The reference figure itself lives in
  the round's brief, never here. **A match between two builds is only evidence
  when you know which one is the reference** — agreement with the weaker one reads as confirmation and is
  the defect itself.
* **DO NOT CHRISTEN A FEATURE.** If the record names it, use the record's name exactly; if it does not,
  describe it by position and dimension and say you do not know its name. An invented name gets reasoned
  from as though it were a fact, and one reached a project's standing FACTS file through `kit close
  --fact`, where it is inherited by every agent afterwards with that file's authority.
* **Before writing a renderer, run the kit's review. If it cannot read your input, make it able to read
  your input.** A session went into four bespoke renderers because the review only read B-reps and the
  result was a mesh; the review then answered in twelve minutes what they had not in hours, and found two
  things they had missed.

---

## THE REMOVAL HALF NEEDS A KEEPER MASK BEFORE IT IS USED

Measured on the worked example: REM came out not as knife edges and tabs but as **ribbons running the full
length of every sharp arris in the box** — the open and blur shaving each one, 153 components. Cutting it
would have rounded surfaces the brief had frozen. No number said so; the picture did. Run the addition
half alone until the removal half is masked to keep clear of the surfaces that must survive.

---

## ENVIRONMENT

VTK is the dependency, and the FreeCAD install on Windows ships it. **Only a trimmed Linux container**
(a kit maintainer's sandbox) may lack it — that setup script's first stage deletes `vtkmodules`. Restoring it
from the AppImage takes a fraction of a second:
`<FreeCAD>.AppImage --appimage-extract 'usr/lib/python3.11/site-packages/vtkmodules/*'` from the
extraction root. `Part.makeShapeFromMesh` is in `Part`, not `MeshPart`, so the type does not depend on the
module a trim removes first.

# KERNEL LESSONS — what the OCC kernel actually does, proven by runs, in a form any CAD edit can use

the client, 2026-09-11, on an orchestrator's line *"I reason about OCC from evidence, not recall"*: **there
is to be one working document, constantly updated, of lessons learned in a generic format so it
can be applied to all CAD edits.** This is it. It is installed into every project's `claude_code\`.

**The rules of this file.** One row per kernel behaviour. A row is written the day a run PROVES
the behaviour — a claim without a run is not a lesson and does not go in. Each row is generic
(no project names in the rule itself; the evidence column may name the run). The orchestrator
appends a row itself, with its Write tool, the moment a build or a check teaches it something the
table does not already say — it does not wait for the auditor. the kit maintainer merges the project copy
into the master `LEAN_KIT\KERNEL_LESSONS.md` at every round boundary. **Read it before
the first build or apply of a session, and whenever a run dies inside the kernel.**

Columns: **WHAT the kernel does** · **EVIDENCE** (date, run, the numbers) · **THE CHECK that
catches it** · **THE CONSTRUCTION that avoids it**.

## Booleans

| what the kernel does | evidence | the check | the construction |
|---|---|---|---|
| A boolean's failure is usually SILENT: `common`/`cut`/`fuse` return a shape with 0 solids (or the input unchanged) instead of raising. | R18 2026-09-11 build 15:20: `above.common(below)` of two healthy fitted sheets came back with 0 solids in three regions ("empty slab"); no exception. | After EVERY boolean, count `.Solids` (or `.Faces`) and compare the volume to what was expected; an empty result is a finding, never a pass. | Build the same solid a second way when the first is empty (a slab as `region − air above − air below` when `above ∩ below` is empty); bound every intermediate by the exact region it is meant for. |
| When a boolean DOES raise, under FreeCADCmd it is a bare string (`Null shape`, `BRep_API: command not done`) with NO traceback and no stage name. | R18 2026-09-11 builds 13:35 and 14:40: `[Null shape]` after eleven successful panel fits, then again after three clean layer summaries; the log pointed at the wrong stage both times. | The last printed line is NOT where it died unless every kernel stage prints its name BEFORE it runs. | Print the stage before each kernel call; wrap each unit of work (a region, a layer) in try/except that names the stage and skips the unit; never let one unit's failure kill the run without a name. |
| `fuse` with nearly coincident faces (0.1 mm off, or flush) MANUFACTURES or loses volume and reports success. | R18 2026-09-10: ruled-polyline piece +385 / +1865 mm³; 2026-09-11 08:15: fitted piece +1789 / +3072 mm³ "manufactured", and the result's tessellation lost orientation (parity fallbacks 2 → 2039). Sections 2026-09-11 15:20: no volume actually missing — a hairline seam left unhealed. | Measure the result by an INDEPENDENT method (rays through the tessellation), not by the kernel's own volume; count parity fallbacks before and after; section across the seam. | Overlap 0.5 mm INTO material, never flush, never 0.1 mm off; consider a fuzzy fuse (`fuse_fuzzy`) across a seam; keep the number of fuses down (assemble region solids that share EXACT walls, then fuse once). |
| A face `common` a solid can come back with NO faces (no exception) and a `SplitAPI.slice` of that face by the solid can then RAISE `Null shape`. | R18 2026-09-11 13:35: `_trim` fell through from an empty `common` to the slice and died bare. | Count faces after the common; treat "trims to nothing" as an outcome to report. | Wrap the slice; an empty trim skips the unit with its name, it is not fatal. |
| `SplitAPI.slice` of one solid by N cutting sheets is the most fragile and the slowest step and scales badly with N. | R18 2026-09-11: 47 → 83 sheets doubled the plan regions (23 → 53) and the fragments each needed their own booleans; 425 s → 1034 s builds. | Count the cutting sheets before slicing; a jump in that count is a defect upstream (crease detection), not a build parameter. | Fewer, longer cuts: merge fragments upstream; never split what does not need splitting. |
| `makeOffset2D` fails on a concave polyline with small features and on self-touching loops. | R18 2026-09-10 18:15: panel offsets failed on outlines with one-cell necks. | Catch it and NAME the panel; check `isValid()` and `.Area` of any face built from a traced outline. | Smooth outlines with corner-cutting (Chaikin) then thin them (Douglas–Peucker) rather than offsetting; fall back to the unsmoothed outline when the smoothed face is invalid. |
| `Part.Face([outer, holes])` can return an invalid face without raising. | R18 2026-09-10 17:00 (burrito v2 `loops_to_face`). | `f.isValid() and f.Area > 0` before use. | Fall back to `Face(outer)` with each hole cut. |

## Surfaces and fitting

| what the kernel does | evidence | the check | the construction |
|---|---|---|---|
| `GeomAPI_PointsToBSplineSurface` tolerance is a TARGET, not a guarantee: the fit stops when degree/continuity limits are hit and returns a surface that may miss the points by more. | R18 2026-09-11 15:20: sheets fitted at tol 0.20 to fields held 0.60 apart still crossed. | Compare the fitted sheet to its field (max deviation) — do not trust the tolerance argument; hold two fitted surfaces apart by at least 3 × the tolerance. | A clearance of 3 × tol between fields that will be fitted separately. |
| C2 continuity cannot be reached at degree 3 across pieces; the fit fails outright ("Surface not done") at every tolerance. | R18 2026-09-10 18:04: every tolerance failed with DegMax 3. | The error text "Surface not done" at ALL tolerances = a degree/continuity conflict, not a tolerance problem. | DegMax ≥ 5 for C2; cap DegMax (8 rang: 5265 poles). |
| A tolerance at the data's quantisation floor makes the fitter follow the noise: poles explode, the surface rings and swings outside its data. | R18 2026-09-10 18:45: tol 0.05 on 0.1 mm-quantised fields → 38,313 poles, an empty layer; 2026-09-11 14:25: 765 poles over 329 cells inverted a slab. | Poles vs points: a sheet with more poles than data points is not a surface. | tol ≥ 2 × the data's quantisation; double the tolerance until poles < points; tiny patches as least-squares PLANES. |
| A fitted surface is only valid over its data; its extrusion reaches wherever its box does. | R18 2026-09-11 14:25: layer 1 built 238,994 mm³ against a 1,425 mm³ grid — the whole footprint prism. | A region solid's volume against the tube it was built for: over 100 % is an escape, not a result. | Clip every slab by its OWN exact region (the tube slice), not only by the outer window. |

## Validity, tessellation, measurement

| what the kernel does | evidence | the check | the construction |
|---|---|---|---|
| `isValid()` True, 1 solid, 1 shell — and the tessellation still carries thousands of open edges: validity is topological, not watertight. | R14 body 2026-09-09: valid, yet 7037 open edges at 1e-4 weld and 4590 at 0.8 mm (real cracks); vertex tolerance 0.90. | Open-edge census of the tessellation at the print resolution; vertex AND edge tolerance maxima. | Weld/heal only closes tolerance near-misses; real cracks need material (a fill) — a valid solid can still be unprintable. |
| Face numbering is 1-based in the GUI and 0-based in Python; a number read off the screen is one higher than the index. | the client's picks (faces 337/338/342, 2644, 1569) are GUI numbers. | Render the named faces highlighted and confirm before acting on a number. | Convert once at the boundary; carry both in the card. |
| A rectangular window's origin shift of 0.1 mm changed a measurement by 12× — the kernel is not the instrument. | R18 2026-09-10 17:45 (burrito v1). | Measure by rays on a fixed grid, count parity fallbacks, and repeat with a shifted grid: a real number is stable. | Numbers come from the probe's own rays, kernel volumes are a cross-check. |
| A slope steep to the sampling direction reads as a staircase in any height-field method; a faceted (tessellated) slope bunches its drop at facet edges; a diagonal cliff is a chain of equal jumps. | R18 2026-09-10 18:15 (17 terraces); 2026-09-11 12:10 (facet creases); 14:25 (diagonal creases deleted). | Crease count and length per probe; primary vs extended; a jump in either between runs is a rule defect. | A step is a jump that stands out from its neighbours AND has no same-sign companion at a shifted level within a span; sample surfaces steep to the rays with a different ray direction. |
| Reading `.Volume` (or any property) of a degenerate/null shape can itself raise. | R18 2026-09-11 build 14:40 (piece assembly). | — | Guard property reads in diagnostics with try/except so the diagnostic cannot be the thing that dies. |

## K-GUI — `freecadcmd` SILENTLY DELETES EVERY COLOUR IN THE DOCUMENT

*Merged from `the project\claude_code\KERNEL_LESSONS.md` 2026-09-16 (R21). The user, repeatedly:
"you have reverted to grey many times and it's a standing bug."*

**What the kernel does.** `freecadcmd` is the console binary. It has no GUI, so App objects have **no
ViewObject** — colour, appearance, transparency, line width, display mode and visibility do not exist in
that process. When it saves, FreeCAD writes an `.FCStd` with **no `GuiDocument.xml` at all**, and that
file is the only place those properties live. No care inside a console script can fix it: the information
is not in the process. Opening a coloured template and re-saving destroys the colours every time.

**Evidence.** Same part, four deliveries: the GUI-made file carried `GuiDocument.xml` at 120,385 bytes;
two files written by a console delivery script had it **absent**; the zip-swap route had it present at
117,041 bytes.

**The construction — edit the zip, never open the document.** An `.FCStd` is a zip. Replace the one entry
holding the body's brep; edit `Document.xml` as **text** to relabel it, drop the stale `ElementMap="…"`,
and remove any dead object (its `<Object/>` line, its `<ObjectData>` block, its `<Dep>`/`<Link>` entries
and the two `Count=` attributes); remove the matching `<ViewProvider>` from `GuiDocument.xml` and
decrement `ViewProviderData Count`; copy every other entry byte for byte.

**In FreeCAD 1.1 colour is NOT `ShapeColor`/`DiffuseColor`.** It is `ShapeAppearance`, an
`App::PropertyMaterialList` stored as its **own zip entry** (`ShapeAppearance`, `ShapeAppearance1`, …)
and referenced **by name, not by position** — so removing one ViewProvider orphans only that object's
entry and leaves every other colour resolving.

**Free second win:** the console route re-serialised the brep to **378 MB**; the zip swap produced
**52.9 MB** from the same body.

**The check:** `zipfile.ZipFile(doc).namelist()` must contain `GuiDocument.xml`. It does not, the model is
grey and it is not deliverable. `kit deliverycheck <file.FCStd>` runs this and the two below.

## K-VIS — "it opens on the wrong thing" is VISIBILITY, and it lives in TWO files

*Merged from the project 2026-09-16 (R21).*

`Visibility` exists **twice**: as an `App::PropertyBool` in `Document.xml` and as a ViewObject property in
`GuiDocument.xml`. **The viewer obeys the GUI one.** Set both, in text, in the zip — the console binary
can set neither (K-GUI).

Measured: a template opened showing only the coloured assembly because the print body's GUI `Visibility`
was `false` and every assembly part's was `true` — correct while a now-deleted mesh was the visible body,
wrong the moment it went. **A delivery gate checks three things, not one:** `GuiDocument.xml` present;
every `MaterialList file=` reference resolves to an entry; the print body visible.

## K-FILETABLE — an ORPHANED zip entry makes the WHOLE document render grey, silently

*Merged from the project 2026-09-16 (R21).*

FreeCAD registers every `file="X"` it meets while parsing `Document.xml` and `GuiDocument.xml`, then reads
the zip against that registration. **The reference list and the payload entries must agree exactly.** An
entry with no reference — or a reference with no entry — breaks the mapping and **every** object falls back
to the default material. No error, no warning: it comes out grey.

That is what greyed one delivery: removing a dead object's `<ViewProvider>` de-registered its
`ShapeAppearance_PRINT` entry, which was left in the zip. Every byte of colour was present and correct,
and none of it was used.

```
refs    = file="…" in Document.xml + GuiDocument.xml
payload = zip entries - {Document.xml, GuiDocument.xml}
orphan  = payload - refs      # must be empty
missing = refs - payload      # must be empty
```

Measured: clean template 111 refs / 111 entries; the broken delivery one orphan; the fixed one 109 / 109.
**Verifying that the bytes are present is not verifying that they are used. Check the invariant, not the
ingredients.** In the kit as `kit deliverycheck`.

## K-MIRROR — do not mirror a cutter onto an asymmetric body

*Merged from the project 2026-09-16 (R21).*

Mirroring a +x cutter onto −x to force left/right symmetry removed the far side **only in patches**: the
stock was not symmetric there — a facet sat at 48.37…50.67 on one side and −47.09…−49.31 on the other,
1.3 mm out — so the mirrored tool did not meet the shelf it was aimed at. **Build every side from its own
face; symmetry of the RESULT is not obtained by symmetry of the TOOL when the stock is asymmetric.**

Two instrument lessons came with it. The reason mirroring was reached for at all was that the native build
appeared to be failing — and the thing reporting failure was `body.common(piece)`, **which returned
0.00 mm³ all session for solids that cut perfectly well. Never gate on `common`.** Gate on the piece's own
volume and solid count, and on the final removed volume. Nor on `BoundBox`, which reported x max 81.33 for
a piece the box clipped at 79.42 (L36).


## K-PREUNION — a pre-union whose VOLUME COMES OUT NEGATIVE is an inverted solid, and every fuse after it is nonsense

*Merged from the project 2026-09-16 (R21).*

**2026-09-16, assembling fifteen strips into one piece.** `job_assemble.py` pre-unions the pieces before the single
body fuse (L40 — 14 small solids fused one at a time into a 4451-face body ran 8+ minutes against 50 s
for the same job with 5). The pre-union reported:

```
pre-union: one piece would not join (fuse shrank or nulled) - it will be fused separately   [x3]
pre-union: 3 solid(s) -22804.4 mm3, 3 piece(s) held back
```

**A negative volume.** `Shape.Volume` sums SIGNED volumes over the solids in a compound, so an inside-out
solid subtracts. Three pieces then refused to join the blob at all — which is the same defect showing up
as a failed boolean rather than as a sign.

This is the same family as the recorded trap that `Shape.Volume` returns a magnitude for a single
inside-out solid, which passes `isValid()`, `isClosed()` and `check(True)` and then makes `cut()` ADD
material. Here the compound makes it visible because the signs cancel.

**The gate:** after any pre-union or fuse of several solids, assert the result's volume is **positive and
at least the largest input's**. A "fuse shrank or nulled" message on more than one piece is not bad luck;
it is the orientation of one of them. Fix the orientation (or drop and rebuild that piece) before fusing
into the body — grinding the body fuse against a negative blob is pure waste, and its own fallback chain
(exact → refine → per-solid → fuzzy) will try all four before failing.

*Merged from a project's copy on 2026-09-24 (R22–R31 rounds). Evidence names the runs; the rules are generic. `kit lessons --near "<what
you are about to do>"` finds the rows below by their words.*

## K-COINCIDENT — two fits of the SAME skin over a shared band are coincident, and the fuse DROPS one silently

Two independent least-squares fits of one skin land on top of each other (p50 gap under 0.05 mm across the band).
Every union order and every tolerance returned a "valid" solid with ONE piece's volume — the other was gone,
`isValid()` True, `common()` 0.00 mm³. OCC answers a zero-gap seam in a curved skin with a lie, not a failure.
**The fix is geometric, not a fuse option:** move one skin off the other in the band (an `offset` of 0.5 mm, buried
into the neighbour). A ramped offset is zero AT the box edge, so where a planar end wall stands on the box edge the
skins are coincident again — carry the offset past the wall. **The gate:** before unioning two band pieces, probe the
gap (p50 under 0.05 mm over most of the band = it will drop a piece); after the union assert volume ≥ largest input +
something. **Third form:** a card's sheet that re-describes another piece's faces (a bottom sheet following a plate's
top and sides) puts faces ON the other piece's walls: `common()` 0.0, `isInside` says overlap, the exact fuse gives two
solids or hangs. A card describes ONLY its own feature (bottom = top − T); what hangs under it is another piece's.
**Fourth form:** `piece.cut(piece.mirror())` returns the WHOLE piece when mirrored walls coincide with the originals,
and a false small number when they nearly do — symmetry is measured on section outlines (discretised at 0.02 mm,
mirrored, nearest-point distance), never by a boolean.

**Fifth form, and the construction that ends it (2026-09-30, the burrito's reinsert on a section):** a piece whose skin
reproduces the body's own to 0-0.03 mm, OVERLAPPING the body over a band of SHRINK mm, is two descriptions of one skin
on top of each other; the union lost the 18,627 mm³ main solid at SHRINK 3 and fused at shorter bands by luck. **Cut both
operands by the SAME tool solid in the same process and fuse the trimmed pieces: the only contact is exactly coplanar
planar faces of one plane, and the kernel merges that** (within +0.8 mm³ at every band length, −0.07 / −0.26 mm³ on the
real keep regions). A coplanar contact made by two different operations (a VTK clip against a kernel cut, L81) is NOT
exact and leaves slits; the same kernel tool on both sides is. One tool solid at a time, largest first (one BOP with
every tool as an argument took 2.7 GB on 2,242 faces); every component of a many-solid region cut separately.

## K-SEW — `sewShape()` joins identical edges only (1.1.3: its tolerance reaches nothing); a global sew re-fixes a fused interior

A 1e-5 mm gap stays open at every tolerance passed (the docstring is `sewShape()`). Faces copied from the body sew; faces
near the body do not. **And a sew of EVERY face of a shape that came out of a fuse re-fixes the fuse's tolerant edges:**
on a section it flipped four of the fused result's faces (a 13 mm² one among them) — a closed, valid SHELL inside an
INVALID solid, 1,947 mm³ short by Part.Volume, `check()` reporting "No error". Sew only the faces with an edge on the
seam you are closing (the ring at the local box: 154 of 7,059 faces) and `Part.Shell` the rest as they are: valid, closed,
the mesh ruler agreeing within 3 mm³.

## K-RAYS-NOT-BOP — material inside a box is measured on the tessellation by rays, never by `common` on a suspect solid

`solid.common(box).Volume` read 0.0 of 233.7 mm³ on a body sewn from a BOP-invalid fitted piece (S16) — the same lie
K-MIRROR recorded for an edit that was there. A ray-winding count on the tessellation (three axes, majority) read the
truth (234.6 → 171.2 mm³: the slot had changed). Every gate on "how much material is in this box" uses the rays.

## K-BOXREACH / K-BBOX — `BoundBox` of a B-spline shape is its control polygon; a reach check reads vertices

A piece's BoundBox reached 1.8 mm below its lowest vertex — the control polygon of a bottom sheet bulging below the
surface it controls — and a reach check reported the union "short" when it was complete. A ±26 mm crop reported
x ±65 by BoundBox; `optimalBoundingBox()` gave ±11.25 exactly. **A reach or extent check compares vertices, a
tessellation, or the optimal box — never `BoundBox` — on anything with a B-spline face.**

## K-2DBOOL — a planar section boolean can fail silently: excess AND missing both equal to the section

At one station in 33, `build.cut(orig)` and `orig.cut(build)` both returned ≈ the whole section area when the two
sections overlapped almost entirely — the face from the sliced wires self-overlapped where a union seam runs through
it. A lone station where excess ≈ missing ≈ the whole area is the boolean, not the part; the neighbours are the
measurement.

## K-VALIDFUSE / K-BOPGATE — the right volume with an invalid solid; `isValid()` is not the gate, `check(True)` is

Plates overlapping a body's fins by 1.5 mm fused to volume = cut + piece − overlap and `isValid()` False (exact and
refine), a Null on fuzzy 0.01, eight negative-volume solids on fuzzy 0.05. Drop-in plates read `isValid()` True and
`check(True)` "BOPAlgo SelfIntersect"; fused, they came back invalid with a gain LARGER than the plate — impossible for
a correct boolean, the tell of a broken operand. **Every PIECE passes `check(True)` before it is offered to a fuse; a
result whose gain exceeds the piece's volume is rejected whatever `isValid()` says.** (2026-09-30: the burrito's reinsert
runs it on every piece solid and refuses by name - the agent's B47 / B53 / S16, fitted pieces with 56-104 SelfIntersect /
InvalidCurveOnSurface faces, lost the main solid in every construction; `check(True)` on a 1.7-3 k-face mesh piece is
under 1 s, on an invalid 114-face fitted piece 134 s.) On a 4,800-face body `check(True)`
runs past 170 s — check pieces and regions, never the body. And `shape.Solids` are fresh wrappers on every call: a
`for s in shape.Solids` compared with `is` against a solid from a second call never matches (a crumb filter kept the
main solid twice and doubled the body). Index into ONE list.

## K-C0EDGE — an approximation sheet with too many poles leaves a C0 edge the BOP check refuses

A least-squares sheet rejected at every pole spacing, then an approximation at 0.30 that built a piece with
`BOPAlgo GeomAbs_C0` on an edge — twice. A looser approximation (0.6: 405 poles instead of thrashing to 1,377) was
clean. **A C0 edge is the kernel's verdict on a sheet with too many poles for its data: loosen the approximation, do
not tighten it.**

## K-FUZZYBODY / K-NULLSHAPE — a fuzzy fuse into the body is a global edit; pieces go into the body one at a time

`body.fuse(piece, 0.01)` on a 111 MB body: a 731.5 mm³ plate gained 2,115.4 mm³, and the next plate's exact fuse then
gained 54 of its 732 — the fuzzy tolerance is applied to every face pair in the body. **Fuzzy is for small pieces joined
to each other, never for the body.** A crown + ten plates joined into one valid solid then made `body.fuse(union)` raise
"Null shape" for unions of 691–1,195 faces in both operand orders and at fuzzy 0.001, while the same pieces fused one
at a time went exact and valid (20–27 s each): a union carries the fuzzy joins' faces into the body's BOP. **Pieces go
into the body ONE AT A TIME, exact, each gated (K-BOPGATE), the body saved atomically at the end** — a kill mid-write
truncated the only copy once (23 MB of 111).

## K-LOCALBOOL — split the region out, assemble, put it back: check the split sums, always

`body.common(box)` + `body.cut(box)` lost 3,988 mm³ (region + rest ≠ body) on a body with its own junk near the box
faces. **Do not trust a split whose two parts do not sum to the whole within 1 mm³ — the check is one subtraction.**

## K-SLIVER / K-TRAP — a sheet that RESTS on a plane leaves an enclosed void; sealing a slit traps every pocket behind it

A fitted bottom clipped at a plane (87.495–87.505 over a rib) fused onto that plane's face became a second SHELL of
0.17 mm³ — a closed cavity no section shows, that MJF prints as trapped powder. Near-coincident is a face of its own.
**A sheet never meets a plane, it OVERLAPS it** — cut the body past the sheet's extreme over solid columns. A slit fill
that was the ONLY opening of pockets behind a wall fused clean by every count and had TWO shells: the pockets were now
enclosed voids. **The check is free and belongs in every assembly: after every fuse `len(main.Shells) == 1`** (0 s). Each
inner shell IS the trapped pocket's solid — `Part.Solid(shell)` (reverse if negative), fuse it in, report it, and gate
the window again expecting air + pockets.

## K-GRAZE / K-RAYS-LIE — a ray that lies IN a face counts no material; near fitted sheets every ray classifier disagrees

A grid column exactly on a planar face (planes at multiples of the spacing are the common case) reads air, the traced
outline ends a column short, and the built wall stands 0.3–0.4 mm inside the block. **The cure is not a finer grid:
put the footprint wall ON the face and snap the outline to it.** Near fitted-sheet faces x-rays, z-rays, `isInside` on
two crop sizes and a 0.1 mm box `common` all disagreed with nothing out of tolerance. **When two probes disagree, do
not take a third ray — cut a section (`Part.slice`, 8 s) or a BOP and read that.**

## K-VOLBOOK — the body's `Volume` is not a gate for a small fuse; gate a WINDOW round the fill

A 224 mm³ notch box (98.8 mm³ of it air) moved the body's Volume by 161 mm³ — the body's own junk shells make `Volume`
a bookkeeping figure. **The gate that works is local:** material inside a window box round the fill must grow by
exactly the box's air; material outside it must not change at all (two `common()`/`cut()` on the body, ~30 s). Window
pad ≥ 8 mm: a 3 mm pad put the window's planes through B-spline faces and read −2.4 mm³ for a fuse that changed
nothing outside.

## K-BOXPLANE — every planar face a fill got from its BOX is checked against the body before the fuse

A fill = box − body − floor carries faces from the body (exact), the floor (built flush) and the BOX's planes. A box
plane is right only where the body is solid just beyond it; where the body is air beyond it the box cut through a
void the fill does not close — a flat face standing in a cavity, a 0.02–1.5 mm gap to the real wall, K-SLIVER on the
next fuse. **Sample a 0.5 mm grid on every planar fill face lying on a box plane, 0.05 mm beyond it, and print the
fraction in air** before every fuse; "the gate passed" does not see a flat face standing in air.

## K-ZIPORDER — FreeCAD reads an FCStd as ONE STREAM: a payload written before the XML that names it is never read

A delivery built by zip surgery passed every file-table gate (36 references, 36 entries, counts consistent) and still
opened its meshes in the default colour: their `ShapeAppearance_*` payloads were written BEFORE `GuiDocument.xml`.
FreeCAD registers each `file="X"` while parsing an XML file and takes the entries that FOLLOW; a payload already past
is skipped silently. **Payloads referenced from Document.xml go after Document.xml; payloads referenced from
GuiDocument.xml go after GuiDocument.xml** (the order FreeCAD's own GUI writes). The table gate cannot see this; a GUI
load that reads the view properties back can. `kit deliver` writes in that order. Same day: a headless `saveAs` of a
coloured map kept every `mat_*` reference and dropped all 15 entries — HOW_TO_DELIVER fault 2 arriving by fault 1.

## K-MESHFLAPS / K-NONMANIFOLD — a body's tessellation carries flaps; `removeNonManifolds` trades a pinch for a hole

`meshFromShape` of the body gave the same triangle count run to run and spike flaps up to 113 mm outside the part that
CHANGED run to run (the "before" volume ranged 1,311,699–1,319,562 mm³). **Drop flaps (triangles outside the B-rep's
extent + 0.5 mm) before any refine or compare; when a model of record is promoted, write ONE canonical tessellation
with its md5 and use it everywhere.** FreeCAD `removeNonManifolds` took open edges 167 → 356 and added 4,900 mm³ —
split vertices instead. The voxel extract writes its patch wound INWARD; a slicer reads an inward shell as a void —
check the winding, refuse, never flip silently.

## K-SORTEDGES - `Part.sortEdges` drops edges at vertices that carry a tolerance; order a face's edges end to end yourself

*the agent's skin build, 2026-10-06 (R4 SP13).* The body's section faces (`wall_caps.brep`) carry vertex tolerances up to 6e-5 mm. A skin face
whose boundary used those body edges came out OPEN after `Part.sortEdges` + `Part.Wire` (two faces) - the sort dropped edges whose ends
met within the vertices' tolerance but not exactly. **The construction:** order the edges end to end yourself (nearest free endpoint,
within the vertex tolerances), build the wire from that order and check it is closed; never trust `sortEdges` on edges copied from
another shape. `kit\rebuild\sk_build.py` carries the ordering.

## K-FILLET-ROOM - `makeFillet` fails (`StdFail_NotDone`) when the fillet has no room on a face, and returns a COMPOUND round the solid when it succeeds

*the kit maintainer, 2026-10-12/13 (kit 31bl, the project b15).* Six builds could not round a vane-to-spine crease: `BRep_API: command not done` at
R 2-3, and the agent's note blamed the piece's check(True) failures. Measured on the sharp piece: a fillet of radius R touches each face t = R tan(beta/2)
from the crease (beta the angle between the faces' normals: 90 deg -> t = R; a 135 deg crease -> t = 2.4 R); the face beside this crease was 1.52 mm
wide before the next border (a hole's rim) and R 2 wanted 4.8 mm - the kernel's fillet surface ran off the face, so it failed. At the R that fits
(0.45) `makeFillet` succeeded at once and `fixTolerance` / `fix` / `removeSplitter` changed nothing either way; the check(True) statuses (a cap's
TooSmallEdge = the body's own 0.1 mm section edge; edges 0.003-0.09 mm off their surfaces) did not matter. **The construction:** measure the room
beside the crease on each face before asking for a fillet (t + the print tolerance of face), and say both ways out - make room (move the border /
fill the gap) or lower R; the kernel is then tried first, the lines blend behind it (`kit\rebuild\sk_build.py`, `sk_wires.py`). **The result:** a
successful `makeFillet` on a Solid hands back a Compound holding the one Solid - read `.Solids`, never `.ShapeType == "Solid"`: the kit refused its own
valid fillet for an hour on that test.
**Addendum (31bm, 2026-10-13, the agent's b20):** on a piece whose faces beside the crease are NURBS FILLS (GeomPlate approximated to B-splines) `makeFillet`
fails at EVERY radius - 2, 1, 0.5, 0.1 - alone, as a group of all the creases in one call, and as a group with every short border leaving their end
junctions; `makeFillet(r1, r2, edges)` (a taper) returns a shape with valid False and a negative volume delta. The kernel's rolling ball needs clean
analytic or original surfaces (b15: it worked against an ORIGINAL face). **The measurement to make first:** the angle between the two built faces'
normals at the edge's middle ON THE SOLID - two fills can meet near tangent (25 deg) where the original had a 90 deg wall; a fillet asked there has
almost no corner to round. The kit's fillet by lines (the arc of R swept along the crease, tapered to the junctions) is the blend on such faces.

**Addendum (31bo, 2026-10-15):** (1) the sense of a crease (convex / concave) read from ONE face's mesh centroids against the other's normal depends on
which face is asked - on a coarse face the nearest centroids lie millimetres from the crease; read it from the shared mesh edges' signed dihedral
(sign(det[v-u, w_p-u, w_q-u]) by edge length), the same from either side and under a reflection. (2) A swept blend's offset points inherit every jump of the
per-sample mesh normals (0.36 mm second differences on a 32 mm crease) and the neighbouring NURBS fills then miss the rim; filter the normals along the
crease first. (3) A V-shaped crease cannot be swept with one blend - the inner face's offset line crosses itself at the corner and the surface folds;
`makeFillet` fails there for the same reason. (4) Projecting a border onto a B-spline surface whose own extent ends short of it (`Surface.parameter` /
`value` on the untrimmed surface) slides the points along the surface's domain edge - a hairpin twice the chord's length with a residual of 0 at the
spots it slid to; ask first whether the surface reaches the border (the median distance of the border's raw segments). (5) A distance to a MESH BORDER is
a distance to its segments: on a B-rep tessellation one straight mesh edge can be 13.78 mm long, and the nearest-vertex distance reads half of that at
the middle of a curve lying exactly on it. (6) A border can be MIXED - half on a shared B-rep edge, half along an absorbed strip - so the test that
decides a surface (the median) and the rule that moves a point (a per-point limit) are two different things; both are needed.

## K-MESH-CRACKS - a solid tessellated FACE BY FACE is a torn mesh; `MeshPart.meshFromShape(solid, Segments=True)` on the WHOLE shape is conforming but for T-junction seams; a crack is an open edge WIDER than the deflection, and a mesh is judged against the SURFACE, never against itself

*the kit maintainer, 2026-10-13 (kit 31bn, the project b20i).* Every piece picture had called `Face.tessellate` per face (`kitlib_render.tess_shape`) and
welded the pieces: on a closed, valid 59-face B-spline solid the meshes of two neighbouring faces do not share their boundary points, so the welded mesh had
6130 open edges - measured by their gap (fix 4), 6108 closed within 0.02 mm and 22 open by up to 0.024 mm: the torn seams, see-through slits and shards the agent
and the client saw were look_at's centroid clip and a painter's-order renderer (hidden faces painted over visible ones), on a solid that is sound. `MeshPart.meshFromShape(shape,
LinearDeflection=0.02, AngularDeflection=0.05, Relative=False, Segments=True)` on the whole solid gives ONE conforming mesh (393 k triangles, 5 s) and its segments give the face of every triangle - but NOT with zero open edges: on a
valid closed B-rep MeshPart leaves T-junctions and split vertices along some face borders (region.brep, 4765 faces: 255 open edges, 1e-4 to 1e-3 mm apart -
geometrically closed, invisible). An open edge is a CRACK only when it is open by more than the deflection asked (its midpoint farther than that from every
other open edge); under it, a SEAM. Four of region.brep's 255 are real gaps of 0.6-1.1 mm along one wall (MeshPart's own failure there) - a crack stamps the
frames whose box holds it, not every frame of the mesh. **Judging the mesh:** a facet-angle statistic (the angle between neighbouring
triangles' normals) cannot tell a coarse mesh from a real C0 line inside a face (a Coons corner, a tapered blend's rows) - 88 deg facets on a sound mesh; the
measurement that works is the REALIZED deflection against the surface each triangle stands for: `Surface.parameter(centroid)` -> `value` / `normal`, the
distance and the normal lean, p99 over a few thousand area-drawn triangles (b20i: 0.057 mm, 3.75 deg at 0.02 / 0.05 asked - the sew's edges sit up to
0.29 mm off their surfaces, so the bound is max(2 x the deflection asked, the piece's largest edge tolerance)). And a long 2-pole B-spline really ripples
(the spine top: 0.3 deg a sample, 745 sign changes of its normal's second difference) - a fine mesh is faithful to that, a coarse one smooths it away;
the picture must show the geometry as built. (`kit\rebuild\sk_lib.py`: piece_mesh / mesh_quality / mesh_vs_surface / view_piece.)
**Addendum (31bn fix 5, 2026-10-15):** (1) `MeshPart.meshFromShape` and `Face.tessellate` both make a 6.8 mm2 SHEET of a planar face whose area is 0.00006 mm2
(R31's model of record: a face whose wire runs out and back along the same two edges) - a PHANTOM where the B-rep has nothing; its rows have no partner
and read as 1 mm "cracks". Drop the triangles of a face whose mesh area exceeds three times its B-rep area + 0.5 mm2 (one such face on R31; its 81 specks under
0.001 mm2 mesh as specks and are left alone) and count its edges, with those of faces the mesher gave no triangle, as an expected boundary. (4) Two
shapes drawn in one frame fight for depth where their skins coincide (the content against the body round the region, the seam faces on the body): the
overlay is moved a fraction of a millimetre toward the camera along the view direction - nothing moves on the screen, the overlay wins. (2) The realized deflection and lean are judged BY AREA, never by count:
a small part's 3000 area-drawn samples reach the mesher's boundary slivers (0.002-0.03 mm2, near perpendicular - its rows bridging a sewn edge's tolerance
band), 53 of which read "41 deg off the normal" on two faces 99.9 % of whose area is within 3 deg. (3) An open edge of a triangle whose height is under
the deflection is a sliver's, nothing to see.
(4, fix 5g) `kitlib_render.cut_mesh` gives every split triangle its own cut points (no weld): a mesh cut on a plane carries one duplicate vertex per
split triangle along the cut - weld before counting its open edges (a 4x4x2 box cut on two planes: 72 vertices for 32 triangles, 40 "open" interior edges).
And a face two solids share - the body's section on an edit region's wall - is seen in no correct picture of both (covered from outside by the body, from
inside by the content); draw the cut on the piece whose face it is, alone, and judge a picture derived from a judged mesh by a trim or a cut AGAIN as drawn.

## K-FACE-COPIES - every face skin-build makes holds its OWN copies of its edges; the shell closes by the sew pairing identical curves, and a face repair that rewrites a wire breaks the pairing (2026-10-16, kit 31bp fix 5).
The UNSHARED COPIES report (sk_build, FIL_DBG=1) showed 121 edges held as two copies of one curve in a pass that CLOSES: `Part.Face(S, wire)` + the
EDGE_FIX pcurves leave no shared TEdge between neighbours, and `Part.Shell(faces)` / `sewShape` pair them by geometry. So (1) two faces that should
share an edge must be GIVEN the same curve to within the sew's tolerance - a 0.04 mm length difference between the copies (an edge re-fitted in one
face only) is a free edge; (2) a face whose surface misses its wire (a fill 0.4 mm off its rim, a corner surface interpolated near its edges) carries
that as an inflated edge tolerance (1.4-8.8 mm seen) and ShapeFix's repair of it REWRITES the wire - trims a corner, drops a sub-mm edge - and the
neighbours no longer match; (3) the repair gate therefore measures a repaired piece against its own LOOP (the fan area and every edge within 2 % /
0.1 mm), never against the invalid face as built - a repair of the wrong region is a span failure (the face named with the loop's sharpest corner);
(4) sub-millimetre edges (0.04-0.3 mm closing segments, contact pieces) invite exactly this: a construction that needs them is wrong - one contact per
junction, lines that cross within 0.3 mm are one point; (5) a corner surface must contain its boundary edges (the rotation's own trace is its floor
edge, not a three-point arc near it) and keep the blends' tangent by construction (the smoothstep blend of the two rotations - a linear blend of two
unequal arcs put their difference into the tangent, 41 deg). (6) (31bp fix 6b-6d) a face made with its NATURAL bounds (`Part.Face(surface)`) holds the
surface's own boundary isos as its edges - never the curves you interpolated beside them through the same points (two interpolations differ by their
parametrization: 1.605 against 1.610 mm in length, unpaired by the sew), and never the neighbours' edge objects; a face that must share edges is built
THROUGH the shared edge objects (the span ladder through them), and a surface degenerate at a corner (one pole column collapsed) is the last resort. (7) a
cone from a point to a curve (`buildFromPolesMultsKnots` with one collapsed row) holds only STRAIGHT side edges - a curved cut fragment of a border lies
0.1 mm off it and the face is invalid; such a cap is spanned through its edges (a 0.02 mm rim) or is the exact Coons of its three edges and the apex. (8)
after any re-sweep of a surface (a taper, an ease) every record taken from the previous surface - offset end points, meet parameters - is stale: re-derive
them on the final surface (a crease shorter than two run-outs scales the OTHER end's row too: 0.073 mm between an end curve's pole and the surface's corner).

## K-C0-DIST - `distToShape` misreads a point's distance to a B-spline edge with a C0 corner (a V joined at its apex) by up to 0.47 mm; measure against the edge's dense samples (2026-11-05, kit 31bw TB7c F3).
On the agent's d19 wires the testers read the kit-mirrored twin of the V chain 65 as 0.46 mm off its master's mirror - `edge.distToShape(Part.Vertex(p))` for every sample of the twin. The
true figure, by the nearest of the mirrored master's own samples at 0.01 mm (`cKDTree`), was 0.148; the same instrument read the master's own cubic leg 0.468 off the V edge that
HOLDS it exactly (the first span's seven poles are the leg's exact degree elevation - `BSplineCurve.join` and `increaseDegree` are exact at the pole level), and a plain two-line
polyline 0.099 off its own first line. BRepExtrema's extremum search returns a wrong local answer near the C0 knot of a degree-6 curve. Generic: a distance to a curve with a corner
(any V the A5b per-leg draw makes, any joined B-spline) is measured against the curve's dense samples, never by `distToShape`; `distToShape` stays for faces and solids.

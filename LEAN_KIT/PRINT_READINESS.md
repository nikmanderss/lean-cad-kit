# PRINT READINESS — how a part is judged ready for a print shop, and the file that goes (2026-09-24)

the client, after the R31 orderability review: *"if you have generic checks or a process written for how to review a part to
be ready to print at the end of the review that would be helpful / wanted for future agents."* This is that process.
It is run at the END of a round, after the last edit is reviewed, and again before an order is placed. Two commands do
the mechanical part; the agent's job is the pictures and the shop's rules.

## The two commands

    kit printfile  <delivered mesh.stl | body.brep> --out Deliverables\<REV>\model\<REV>_PRINT.stl --rules <shop>
    kit printcheck Deliverables\<REV>\model\<REV>_PRINT.stl --rules <shop> [--bores <spec.json>]

`<shop>` is a key of `kit\print_rules.json` (`jlc_mjf_pa12`, `jlc_9000he`, ...). **Re-read the shop's page and update the
rules file's `read` date before an order** — limits change without notice. Both commands run with no session open (they
read; they edit nothing of record). printfile writes its report beside its STL; printcheck writes `PRINTCHECK.md` into `claude_code\jobs\PRINTCHECK_<stem>_<rules>\` (one folder per rule set; each command also makes a job folder of that name).

**`kit printfile`** makes the file the shop will see. It never moves geometry except by decimation, and that only over
the size limit: weld exact duplicates → drop bubbles and fragments (every shell but the largest) → open every air film
(two parallel surfaces facing each other within `--film` mm: a lamina, a slit, a crack — both walls go, the body closes
over it) → the kit's nmfix (pinches split, no face lost) → drop what that cut loose → fill every boundary loop (ear
clipping in the surface's plane; FreeCAD's fill for the rest) → decimate to the limit → binary STL + `<name>_PRINTFILE.md`.
Exit 1 when the file is still not one closed shell — then the report's counts say where, and the agent looks.

**`kit printcheck`** judges a file (or a B-rep, tessellated at 0.05 mm) against the shop: size vs build volume, file size,
watertightness (0 open, 0 non-manifold, 1 shell), the B-rep's own health if given one, a ray-cast wall census against the
shop's floors with every thin place clustered and named by atlas region, filled 2-D sections through every cluster of
5 mm² or more, and the bores against a spec file. Verdict `ORDERABLE` / `ORDERABLE with questions` / `NOT ORDERABLE` with
the number behind each row and the kit action that clears it, in `PRINTCHECK.md`.

## The review, in order — nothing is skipped

1. **The delivered model of the round is the input.** the client, 2026-09-24: *"the mesh exported as an stl is what goes to the
   print house ... Step and brep don't matter and don't need to be changed at this point."* When the round delivered a mesh,
   the mesh is the print file's source; the B-rep is not edited for the order. When the round delivered a B-rep, the B-rep
   is tessellated by `kit printfile` and the STL is what is judged — the shop never sees a B-rep, and a STEP of a body
   with 0.3 mm edge tolerances re-imports as loose faces (R31: 353 MB, 0 solids). Never send STEP.
2. **`kit printfile`, read its report.** Every film it opened is a defect the round left (the R31 intake-lip films: a
   0.2–0.3 mm air gap 0.35 mm under the lip's underside, 450 mm² a side); every fragment it dropped is a bubble or a
   sliver. If a film is where a designed gap should be, the gap was under `--film` and that is the design's problem.
3. **`kit printcheck`, then OPEN EVERY SECTION PICTURE.** The census cannot tell a thin wall from a thin skin over an air
   film; the filled section can (one band = a wall, two bands with a dark hairline = a lamina). the client: the pictures are the
   acceptance. A wall under the shop's floor is a design change (thicken); a lamina is a `printfile --film` matter.
4. **Bores and inserts against the SHOP's insert spec, never against an old ruling.** R31's Ø3.6 × 7 and Ø5.9 × 7 were
   called a regression against a 2026-09-05 ruling; they were the print shop's Type 5 and Type 8 insert holes exactly, changed on
   purpose, and the client had to say so. The bore spec file names the insert type for every hole; the shop's insert page is the
   source; a difference from an older ruling is a question, not a finding. **`kit printcheck --bores <spec>` measures
   them ON THE MESH too** (2026-09-25; before that a mesh printed no bore row and no warning, and a drawn slab that
   filled a third of cover bore C4 passed every gate): a spec that measures nothing is a FAIL row, never a silent pass.
   A bore off spec on a mesh means something drawn covered its mouth - `kit union`'s cavity and frozen reports say what.
5. **Frozen regions, reported** — `kit atlas recreated <region> --result <print file> --baseline <the pre-edit mesh>
   --where` for every frozen region a piece's box touched, and its counts go with the delivery. **On a mesh round this
   is an INDICATOR the agent judges, not a gate** (the client, 2026-09-25: enforcement is for B-rep and burrito edits only; a
   mesh delivery owes nothing to `deliverycheck`). On a mesh-route project every frozen region already misses on the
   untouched rework mesh (7, 5 and 6 cells on three of them on R32), so the baseline is what tells new damage from old;
   `--where` prints the clusters. The result is cropped to the region's box first (the heatsink took 10-12 min against
   the whole 3.2 M-triangle result). The always-FAIL thin-wall row of printcheck is the same kind of thing: the
   agent's judgement against the previous revision, not a waiver (the client, 2026-09-25).
6. **The shop's process, written for the client** in `Deliverables\<REV>\review\ORDER_NOTES.md` (the agent writes `review\`; `model\` is the kit's - the guard refuses a hand-written file there): for SLA, which faces must be built
   facing up (seats, gasket lands, pads — supports leave nubs where they touch and the shop cannot reach inside ducting);
   for MJF, that slits under ~2.5 mm keep powder; for both, one part per file, mm, the tolerance band at the part's size
   (the larger of the shop's ±mm and ±%: at 340 mm, ±1.4 mm MJF, ±1.0 mm SLA) against every clearance the design relies on.
7. **Deliver — the usual FreeCAD model, not a bare STL, IN THE PREVIOUS DELIVERY'S STRUCTURE** (the client, 2026-09-24: *"I don't
   just want an stl I want the full freecad model delivery as per usual"*; on the first two R32 builds: *"The entire
   colored atlas should be in an unexpanded, hidden part"* and *"Look at R26 delivery structure and update that with the
   4 models"*): ONE command, `kit deliver <REV> --name PRINT --template <the previous delivery .FCStd> --mesh-file
   <specs.json>` (or `--mesh "<print mesh>|<label>|<stl>|1|r,g,b|G1_PRINT;<source mesh>|...|0|r,g,b|G5_SOURCE;<model-of-record
   mesh>|...|0|...|G5_SOURCE"` - a label may not contain `;` or `|`; the JSON form takes any label)
   `--group "G5_SOURCE|5  SOURCE MESHES (hidden) ..." --atlas-group "G6_ATLAS_v6|6  REGION ATLAS ..." --map <the client's approved
   map .FCStd> --drop <the template's body object> --review <the COMPLETE orbit-review dir>`. **`--review` is the
   default of this template; `--no-review "<the client's words>"` is a recorded exception in their quoted words, and the delivery
   after an unreviewed one runs the full review** (2026-09-25: this line carried `--no-review` baked in, R31 and R32
   shipped with no orbit review, and the first full review - on R34 - found a roof-ridge tear that had been in R32 all
   along). The template's G1_PRINT (shown, expanded),
   G2_ASSEMBLY (coloured, hidden), G3_REFERENCE (hidden) and G4_MARKERS (hidden) come across byte for byte with every part
   and colour; the print mesh goes INTO G1_PRINT beside the cover, the sources into their own hidden collapsed group, the
   atlas's region objects into ONE hidden collapsed group (tick it to paint); nothing sits loose at the top level; the
   old body object is dropped; the command runs `kit deliverycheck` itself. A headless open (`FreeCAD.openDocument`,
   list top-level objects and each group's members) confirms the tree. (`kit mesh meshdoc` + `kit mesh zip` was the
   first recipe and is superseded; `HOW_TO_DELIVER_A_COLOURED_MODEL.md` has the why.) Beside it: the STL (the upload
   file), `<name>_PRINTFILE.md`, `PRINTCHECK.md` (both shops if both are planned), the section pictures under
   `Deliverables\<REV>\review\printcheck_<shop>\`, `ORDER_NOTES.md` and a `README.md` naming each file (both in `review\` - the agent's folder). **The source STL
   (the edited mesh before films closed and decimation) stays in the job's work folder (`claude_code\jobs\<J>\work\`) - only `kit printfile --out` / `kit deliver` write into `model\`, never the source beside the print file** - the client took
   the 163 MB source in `model\` for the print file and reported it over 100 MB (2026-09-25). **The README is written
   from the measured results after the model exists**; a skeleton written ahead of the work claimed edits that were
   never made and sat in a guard-protected deliverable for hours; a README with `{{` placeholders reached
   Deliverables once - `grep` it before the copy. A project's order record (`claude_code\ORDER_PREP.md`: item, test that
   closes it, STATE) is the agents' record (the client does not read .md); it is rewritten in place, never appended to.
8. **Checks once, at the end** (the client, 2026-09-24 late: *"save checks for the end of all edits so they can be done once on a
   hopefully finished model. I want all of them done together"*): when a round of edits precedes the order, none of
   steps 1-7 runs per edit - the edited base is finished first, then printfile, printcheck (both shops, `--bores`), the
   frozen regions (step 5), the review and the delivery run ONCE on it. **A dry end pass on the candidate base while
   the last pieces run** (printfile + printcheck into a job folder) finds the finish-stage defects 2 h before shipping
   (2026-09-25: `--bores` silent, cover bore C4 at 2.58 mm, the gutter slabs in the cover seat) - promote its outputs
   by base md5 instead of re-running them. **The runner that does this never checks or delivers an INCOMPLETE chain**
   (the project's first one did, and copied an unfinished 163 MB base into Deliverables): it stops and says which pieces
   are missing. Its return codes are read (printcheck, deliver); `--recreate-waived` and `--no-review` are not baked into
   it. **Between revisions the census is compared, not re-read**: re-decimating the whole mesh moves single-sample
   thin-wall clusters in untouched regions (a 10 mm² "new" cluster at the client's circled corner was census noise), so report
   the thin-wall clusters as NEW / GONE / CHANGED against the previous revision's printcheck (a `kit printcheck --baseline` is owed) and flag only the new ones.

## What the shop does with the file (so the report answers it before the shop asks)

Upload → automatic check (dimensions against the build volume, wall thickness against a floor, thinnest part, weight) →
a manual engineer review of hours → confirm → pay. The shop's repair closes small holes and unions overlapping shells on
its own; it does not fill a crack that opens to the outside, and it reads a lamina as a thin wall — which is why
`printfile` closes films and `printcheck` sections them. **MJF**: no supports; unfused powder is the support; the part is
unpacked and blasted; open ducting empties, slits keep powder. **SLA**: supports on every down-facing surface at the
chosen orientation, removed by hand, nubs sanded where reachable. Neither process resolves a feature under ~0.3 mm; a
wall under the shop's floor prints fragile or not at all.

## Lessons this process carries (each cost a wrong statement to the client on 2026-09-24)

* A wall census must accept the face the ray LEAVES material through (normal along the ray). Accepting the face that
  "looks back" reads wall + duct, flags only thin skins over cavities, and misses a real thin fin. `_pc_walls.py` header.
* Do not re-orient a valid tessellation's normals with VTK's AutoOrientNormals: on a mesh with open edges it flipped
  14,000 triangles. The STL's own winding is the truth for a mesh the kit wrote.
* Bubbles and pockets are dropped BEFORE films are looked for; a wedge-shaped pocket's apex reads as a film otherwise.
* A partial triangulation of a hole is worse than none: it leaves the loop open and reports it filled. Only m − 2
  triangles close an m-gon. A long thin loop that bends in space (the mouth of a film at a corner, a crack along a
  fillet's edge) does not ear-clip in any plane; the minimum-area triangulation in 3-D closes it.
* A film is not just its two walls: the thin bands that close it at its mouth and its ends (the free end of the sheet,
  the end faces of a slit) go with the walls, or they stay as flaps and every cap over the mouth duplicates one of them
  (126 non-manifold edges on the first test). A cap that duplicates an existing triangle IS a flap: both go, refill.
* A film's other wall must be PARALLEL (normal agreement under −0.9), not merely facing: the bottom strip of a V-groove
  and the apex of a wedge-shaped pocket face each other too, and eating them changes designed geometry.
* A hole's rim is walked UNDIRECTED: one rim triangle wound the other way makes a directed walk fail silently and the
  hole stays open; the cap's winding is settled afterwards against the mesh's own directed open edges, by majority.
  Pinched edges (three or more triangles) are cut out and refilled like any hole; so are junction vertices.
* On a 2.6 M-triangle mesh VTK's per-ray intersection costs milliseconds a ray whatever the tree; a short ray (the film
  test) is a grid join in numpy, seconds for the whole mesh. Long rays (the wall census) keep VTK with a deep tree and
  a sample, never every triangle.
* Machine hygiene, because the pass runs for minutes: one launch per job (a marker file; a timed-out launch call may
  still have run), P-core affinity and above-normal priority on a hybrid CPU (kit.py's `sh()` does it from `env.json`'s affinity_notes), no
  `wmic`, no waiting inside FreeCAD's executor.

# PROJECT START - a project that designs FROM PARTS (no model of record yet)

The kit's method assumes one model of record - a body in `claude_code\bank\` edited region by region and promoted. A project that starts from purchased
parts and a given assembly has none yet; the first session of such a project met these frictions (2026-10-29 / 30) and this page is their answer.
`kit open` prints the steps while the bank is empty.

## 1. The first body
- A brep or an stl the client exported goes into `claude_code\bank\`; `kit newjob <J> --from <that brep>` starts a job on it (the kit reads .brep and .stl
  only - a STEP or an FCStd is exported to one of those by the client; the kit never runs FreeCAD outside its commands).
- A body of your own design, with no client brep at all: `kit newjob <J> --first "<why - the client's words>"` (no base, no region.brep), then a `sketch_extrude`
  card with `Base: none - the first body` and `Row: none - the client <date>: '<the client's words>'` (the lint's form for a job outside the criteria table), `kit job`, `kit run`
  with `base=""` and `op='piece'` - the piece alone (the very first block); every later block is a job on the previous result (`kit newjob --from`).
- HOW A FIRST BODY ENDS: nothing checks a body against no base (`kit review` / `check` / `accept` / `apply` are an edit's gates). Render it (`kit render <result>
  --box ...`) and look; copy the result into `claude_code\bank\` (`R01_<NAME>.brep`); `kit promote <project>\claude_code\bank\R01_<NAME>.brep --note "..."` (a path
  written from the project root resolves from any folder); then `kit cancel <J> --why "the first body - promoted from the bank"` takes the job off the books (the
  stop hook otherwise lists it as open). `kit promote` ends the atlas deferral in its record (4).
- `kit apply` / `kit promote` mean "this body is the model of record"; a project with several bodies keeps each in its own job and delivers them together (3).

## 2. The FreeCAD document - from the kit's template
`templates\BLANK_MODEL.FCStd` is a GUI-saved document that carries nothing of any project: the groups `G1_PRINT` (shown) / `G2_ASSEMBLY` / `G3_REFERENCE` /
`G4_MARKERS` / `G5_SOURCE` (hidden), the two marker blocks (`MARKER_BOX`, `MARKER_PYRAMID` - the marker-block route's blocks), a `PLACEHOLDER_BODY` in
G1_PRINT, and the NAMED COLOURS as four simple shapes in the hidden group `G0_PALETTE` (`templates\BLANK_MODEL.md` says which colour is which). The first delivery:

    kit deliver R01 --template "<the kit>\templates\BLANK_MODEL.FCStd" --target PLACEHOLDER_BODY --model <the first brep> --no-review "the first body - nothing to review against" --add-body "name|label|<brep>|1|r,g,b|G2_ASSEMBLY" ...

`--target PLACEHOLDER_BODY` swaps the first body in (the placeholder takes the swapped body's own name; `--label` names another); every further body is an
`--add-body` spec into a group (a `place=` turns and moves it; a shown body added into a group the template keeps hidden shows the group too, said); the output is
the next delivery's `--template`. `kit deliverycheck` runs itself; the client's look in the GUI is the acceptance.

## 3. Placing and turning parts
Every export sits in its own frame. `kit place <brep> --out <placed.brep> --translate dx dy dz --rotate "ax ay az deg" [--about px py pz] --why "..."` writes the
placed brep (the placement in the brep's own location - what FreeCAD reads back) and records it in `claude_code\PLACEMENTS.json`, the project's frame map; a
`place=` field on an `--add-body` / `--mesh` spec does the same at the delivery; `t_move` turns too (`rot_axis` / `rot_deg` / `rot_about`).

## 4. The atlas and the dossier - after the model has made worthwhile progress
A new project has nothing to map. `kit atlas defer --until "<the client's words>"` records that: the stop hook's atlas question is silent, a card's `Region:`
reads `no atlas yet (deferred: ...)`, a delivery owes no `--no-atlas`. The question returns at the first promoted model of record (`kit promote` ends it in its own
record - `kit atlas status` says how it ended; `kit atlas defer --until` again defers it anew on the client's word) or `kit atlas defer --lift`; `kit atlas init`
starts the atlas and ends the deferral.

## 5. An assembly - several solids, edited as they are (31bw)
An assembly (a compound of several solids) is edited as it is since 31bw: every kit boolean keeps every solid of a compound base (a one-solid base keeps the largest, as
before - an edit never makes a second body), `t_split` keeps every solid on each side (solid by solid - the kernel's whole-compound common drops overlapping solids), a pattern's added copies stay separate solids, `kit check` judges
the result's solid count against the count the edit intends (a job that makes or removes whole bodies on purpose states `solids N` on its card's Expected line; else one body stays one
and a compound keeps its own count),
and `kit tool extract --job <J> --set "BOX=x0 x1 y0 y1 z0 z1" [--set TRIM=1|0]` copies a region of an assembly out with its census (the solids wholly inside kept whole, the
ones the box cuts trimmed to it, the rest left out) for the next job (`kit newjob --from <the extract>`); the skin route still edits one solid - its region step says so.

## What is still the client's today
Still the client's: STEP / FCStd import (the client exports breps), a survey mode for measuring purchased parts, and the render budget for very large meshes - the plan's
open items; until then: ask for breps and render large parts one at a time.

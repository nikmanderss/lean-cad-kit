# METHOD — how a project builds CAD with agents (plain English)

Written 2026-09-06 and **used on more than one project since** — where an example names a part or a
feature, it is an illustration from the part it was learned on, not a fact about yours. The METHOD transfers; the numbers do not. This is the conceptual approach;
`EDIT_TYPES.md` is the catalogue of allowed edits; the project's own `CLAUDE.md` is the entry point an
orchestrator reads. This file changes only at milestones, not every round.


## BEFORE YOU ASK THE CLIENT ANYTHING: the record has probably answered it

**An interpretation menu is the anti-pattern.** The project that taught this wrote it down:
*"if two readings produce the SAME geometry, there is no question - pick and build. A question is only
earned when two readings produce DIFFERENT geometry, both plausible under the ranked goals - and then it
ships with renders of both."* And: *"The orchestrator owes ONE playback line - the acceptance test it
derived - and builds unless the client vetoes it."*

**What that rules out - and the opposite failure, both on 2026-09-22.** An agent with the whole project
folder mounted asked the client which end of a part was the front, on a job months old. That question
should not have been asked. It then answered it itself - WRONG: it took the newest line in the facts
file that stated an orientation, an agent's own derivation written that morning, over four older sources
that agreed with each other, one of them carrying the client's own correction. Four correctly named
regions were renamed backwards and a "correction" was sent to the agent that had named them right.
**Not asking is only half the rule. The record has to be WEIGHED, not grabbed.**

So, before a question is written:

1. **Who said it outranks when it was said.** The client's own words and corrections first; measurements
   the client confirmed next; **an agent's derivation is a claim to check, however recent and wherever it
   is filed.** A facts file holds both kinds - read the heading a line sits under before quoting it as a
   ruling.
2. **Count the independent sources.** What the whole record uses - the boxes the acceptance table was
   surveyed with, the job folders' own names for things, the frame the renders were taken in - is settled
   by agreement. One line contradicting all of them is the thing to check, not the answer.
3. **When sources disagree, that disagreement IS the finding.** Resolve it by the higher-authority source,
   then write the correction beside the wrong line so nobody re-derives from it.
4. **The acceptance table and the rounds that measured it.** The table names the feature; the survey and
   job boxes from the round it was written in show where each row was measured.
5. **The part itself**, as corroboration and never as the primary source: a render is how the wrong
   reading gets confidence.

A question to the client is earned only when sources of EQUAL authority disagree and the readings build
different geometry - and it goes with a picture of each.

**And when you do ask: words, dimensions and a picture - never coordinates.** *"Coordinates mean nothing
to me. Ask with words/dimensions/pictures."* A question written in raw numbers puts the translation work
on the person who already knows the answer.

## 1. The idea in one paragraph

A CAD engineer builds a part as a short list of simple features, each drawn as a flat shape on a
known plane and then given depth: a rectangle extruded into a block, a circle cut into a hole, two
outlines joined by straight sides into a wedge. They never sculpt; they never fit a surface through a
cloud of points; they never ask the computer to "smooth this". This project builds the part exactly
that way. Every feature is a **job card** that names the edit type, the flat shape (with its
numbers), the plane it sits on, the depth or the second shape it connects to, and whether it adds
or removes material. A low-tier agent fills a fixed script template with those numbers and runs it.
It cannot invent a method, cannot measure, cannot choose a number. The orchestrator (Opus or Fable)
owns every number, every measurement and every acceptance.

## 2. Who does what

**The orchestrator** (Opus / Fable, in Claude Code)
- Holds the design intent, the part's facts (the project's fact file: `PROJECT_FACTS.md`, or `FACTS.md` - `kit facts` reads either) and the model of record.
- Decides the feature order and writes one job card per feature (`claude_code\jobs\<JOB>\CARD.md` - `kit newcard <job> --type <t> --write <path>` scaffolds it - without --write it only prints it; `kit card` lints it - 31bs T7 F12).
- Takes every measurement itself (sections, ray tables, bounding boxes, clearances) BEFORE the card is
  written, and puts the resulting numbers on the card. A worker never measures.
- After the worker hands back: runs `kit check` (the instrument), opens the pictures, accepts or
  re-briefs. Applies the accepted piece to the model of record itself (`kit apply`).
- Asks the client when intent is unclear. Never guesses a dimension that matters.

**The worker** (the lowest tier that can do the job — found by test, see §7)
- Reads ONE job card and ONE edit-type card. Nothing else.
- Copies the edit type's template, fills the `PARAMS` block with the card's numbers, runs it through
  `kit run` (pinned FreeCAD, hard timeout, log).
- The script builds the feature as its own small solid (the **piece**), banks it as a `.brep`, then
  fuses or cuts it into a **region copy** of the body so the result can be looked at.
- Renders the standard pictures with `kit render` (6 views + the close-ups the card asks for), OPENS
  them, and writes one line per picture: HIT (the feature is visible, what it looks like) or MISS.
- Hands back `RESULT.md`: the PARAMS used, the run's bookkeeping lines (one solid / valid / volume
  change), the picture lines, and any question. If a number is missing or the template cannot express
  the card, it writes the question in `RESULT.md` and stops. It never changes the method.

## 3. How an edit is conceived (the shape-extents rule)

Every feature follows the same four steps, and the job card is written in these words:

1. **Where does it go?** The orchestrator names the plane the flat shape sits on (a named face of the
   body, or a plane at a stated offset from one) and the area on it, from its own render/section.
2. **Draw the shape there.** A closed flat outline: rectangle, rounded rectangle, circle, slot, or a
   polygon with straight sides and drawn arcs. Rounded corners are drawn INTO the outline (never
   filleted afterwards on a built body).
3. **Give it depth, or connect it.** Either extrude the outline a stated distance along the plane's
   normal (add or cut), or draw a second outline on a second plane and connect the two with straight
   sides (a wedge, a taper, an angled face). Straight vectors or drawn curves only; no lofts through
   many sections, no fitted surfaces.
4. **Fill the material in / take it out.** The piece is fused into the body (or cut from it). The piece
   is always built to overlap the existing material by at least 0.5 mm where it joins, and to stand at
   least 2 mm clear in air where it must not touch — never flush, never 0.1 mm away (that is where the
   kernel fails silently).

**Punch-through is forbidden; entering is allowed.** A piece may go INTO an existing feature (the
fuse merges it cleanly); it may never come out the other side of a wall or through a face it was not
meant to reach. The job card therefore states the piece's far limit as a number ("stops 3 mm short of
the inner floor"), and the orchestrator has measured that number before writing it.

**No shard fields, no face explosions.** Every feature adds a handful of faces (a box: 5; a hole: 1–3;
a wedge: 5–6). If a run reports more than the card's expected face count, the result is wrong and is
not applied. Anything that "smooths" by adding thousands of faces is outside this method.

## 4. What is allowed and what is not

Allowed operations: box, cylinder, extruded closed sketch (with arcs), ruled connection between two
closed sketches on two planes, revolve of a closed sketch, fuse, cut, common with a box, mirror across a
named plane, linear pattern of a piece, shell (hollow) of a plain box only, rounds drawn into sketches.

Not allowed in a worker script: fillet/chamfer operators on a built body, lofts through more than two
sections, surface fitting/approximation, `removeSplitter`, defeaturing, mesh operations, fuzzy booleans,
any measuring call (`distToShape`, `section` for numbers, ray casting for numbers), any edit outside the
job's region box. The kit refuses these by scanning the script before it runs (`kit run`), and the
Claude-Code hook refuses the shell command before the kit sees it.

## 5. Gates (why nothing silently goes wrong)

> **Updated 2026-09-09 — the gates below are now CODE, and there are six more that judge the
> ORCHESTRATOR.** `kit exam` / `kit open` / `kit card` / `kit job` / `kit look` / `kit accept`,
> in `kit\leangate.py`, with `CONTRACT.md` pushed at every session start by a SessionStart
> warden. They were aimed at the orchestrator deliberately: every non-clean result in
> the first project's test log was a CARD defect the worker caught, and an earlier kit's experience is that
> heavy machinery on the worker buys compliance rather than correctness (2,039 stamped review
> images, 96 % satisfied, and a round still aimed at the wrong faces).

- `kit run` is the only way FreeCAD executes. It checks free disk first, pins the binary, applies the
  170 s cap, tees a log, scans the script for forbidden calls, and prints a bookkeeping line after every
  boolean (volume change, solids, valid, faces). A script that has no such line did not do anything.
- `kit render` writes the standard pictures; the hand-back refuses if they are missing.
- `kit check` (orchestrator only) is the instrument: valid, one solid, kernel + tessellation volume
  agree, face count within the card's window, nothing changed outside the region box, and no new
  opening where the card said "no punch-through" (thickness map before/after).
- Claude-Code hooks (`LEAN_KIT\hooks\`, wired by each project's `.claude\settings.json`): a worker's Bash is refused if it runs FreeCAD outside `kit run`,
  writes outside its job folder, or calls a measurement command; a worker cannot finish while
  `RESULT.md` lacks the run's bookkeeping line and the picture lines.

## 6. What the orchestrator does with the numbers

The orchestrator measures with its own tools (the same kit, `kit measure`, which workers cannot call):
sections at named stations, ray tables, bounding boxes of named faces, clearance between two solids.
Results go on the job card as plain numbers at the tolerance-class resolution (0.30 critical, 0.10 seal,
1.5 working band elsewhere) — no long decimals. A card that needs a number the orchestrator does not
have is not written until the number is measured.

**A MEASUREMENT IS ANY NUMBER YOU WILL ACT ON** — not only what a `kit measure` subcommand prints. A
face area from your own script, a bolt position read off a face table, a sill height from a section: if
a card, a region or a decision rests on it, it is a measurement, and it goes into the region's dossier
once — `kit dossier add <name> --what --value --source` files it without a kernel call. the client, 2026-09-22:
*"There should be no re-measuring - that's the point of the dossier."* One session took several hundred
numbers with its own scripts and filed none, because the only road in re-measured. Take a dossier only
when an edit needs its numbers; never re-take one just because it lapsed.

## 7. Tiers, effort, and how the line is found

- Tiers are model sizes: haiku (smallest) < sonnet < opus. Each job type is first tried on haiku with
  a fully specified card. If haiku fills the template correctly and the check passes twice on two
  different cards of that type, that type is "haiku-grade". If it fails on the same card twice, sonnet
  is tried, and so on. The result is recorded per edit type in `EDIT_TYPES.md` (the "tier" line) and
  the test evidence stays in the job folders (RESULT.md) and in `FAILURES.md`.
- Effort: yes, it can be dictated. In Claude Code an agent definition carries a `model:` and an effort
  setting in its frontmatter; the orchestrator can also say in the brief "think briefly / do not
  deliberate". Whether it matters for CAD is being tested: the hypothesis is that with a complete card
  the work is clerical (copy numbers, run, look), so LOW effort should be enough for haiku-grade types
  and effort only matters when the card is incomplete — which is the orchestrator's fault, not the
  worker's. Test cases record tier AND effort.
- Orchestration itself stays with Opus/Fable. Test orchestrators may be launched to read the docs and
  propose a card, to see whether the docs re-read correctly; their proposals are not merged into the
  design without the client.

## 7b. What keeps a worker on task (measured on the first 15 launches, 2026-09-06)

Fifteen haiku launches at low effort, fifteen correct behaviours, ~50k tokens and ~1 minute each. Nothing in that
came from long rule lists; it came from five things:
1. **A complete card.** Every PARAMS value spelled out, absolute paths, the base file already in the folder, and
   EXPECTED numbers the orchestrator actually computed (plan area × height, face counts). The two times a number was
   wrong on a card, the worker flagged it; it never "fixed" it.
2. **One edit type per card, one template per type.** The worker's whole job is filling a PARAMS block. It cannot
   pick a method because there is nothing to pick.
3. **"Ask and stop" as the only branch.** A missing number (T03) produced a question and no run; a card that the
   template refused (T04) produced one failed run and a report, not a workaround. The rule is short and it holds.
4. **The template validates before the kernel does.** Mismatched outlines, self-intersecting pieces, forbidden calls,
   too many faces for a fillet — all refused with a one-line reason the worker can paste. Cheapest gate there is.
5. **Pictures are mandatory and the orchestrator looks anyway.** Haiku's picture descriptions are sometimes invented
   (a "sloped top" on a flat part); the pictures themselves are what the orchestrator judges. The renderer draws
   crease lines so a hole reads even square-on.

The do-not list for workers is six lines long (GENERAL card in `EDIT_TYPES.md`) and has not needed a seventh.

## 8. What was learned on the part that this method keeps

- Render first; a picture answers most of what an instrument would be built for.
- Build pieces from the body's own geometry where possible (its faces, its sections), never from
  numbers typed from memory — but on a part built feature by feature, the body's geometry IS the
  numbers on the cards, so this collapses into "read the number from the card, which was read from the
  body".
- One boolean per step, bookkeeping after each, bank every piece.
- Never coincident faces; overlap 0.5 into material or 2 out into air.
- A clean-looking result that was not looked at from the owner's angle is not a result.

## 9. Session-1 close notes (2026-09-06) — for the next revision of §3/§7
- 36 launches, all haiku/low. One worker deviation (C3: hand-wrote a script from the howto printout instead of the copied template) →
  `kit run` now refuses any script that is not a template copy. Every other mismatch was the orchestrator's EXPECTED number.
- Card-writing rules that earned their place: expected volume = area × (depth − air lead-in); "about" for face counts (cylinder seams
  split unpredictably); a tilted bore's lead-in = 2 + r·tan(tilt); a piece's far limit is measured on the NEIGHBOUR it might reach
  (the v2 loop flange left 0.5 mm over the bore — found by the fit check, not by the worker); fit-check against the scan after every
  feature that touches it.
- Delivery is orchestrator work (`kit deliver`); a worker template for it is not worth writing.

## 10. The orientation lesson (2026-09-06, R1 review) — a card rule, not a worker failure
R1's sloped face was built high on the viewer's side, so the screen looked away from the viewer. Every worker did exactly what its card
said; every check passed; the fit checks passed. The card carried only numbers ("front edge 40, back edge 94.8") and no statement of
what the feature was FOR. **New card rule: any feature with a direction — a slope, a window, a heatsink wall, a clamp — states its
purpose in one plain sentence next to the numbers ("the face looks up and BACK at the viewer"), and the orchestrator's own accept step
checks the picture against that sentence, not against the numbers it just wrote.** A number can only be checked against itself.

## 11. The region atlas — what the part's regions ARE, stored once (2026-09-22)
A card names the region it edits (`Region:`), and only a region the client confirmed. A region is a FEATURE the
client would name ("the skirt"), not a breakdown; which part of it goes in words on the card. How one is defined,
in the order that was bought by rejected maps:
1. **State what it IS first** — what mates to it, which way its surface faces, what it does. Not a box.
2. **Look from the side that can physically show it** (a down-facing seal from below, a bore along its axis).
   If the view cannot show it, the reading does not count.
3. **Write it as SPACE + SURFACE DIRECTION + AREA LIMITS**, and CUT faces on the boundary: a few long faces carry
   half of a real body's surface, so "the faces whose centre is in the box" is wrong for half the part.
4. **Render it alone and judge it; the client confirms it.** A number is supporting evidence.
The tools (`kit tool --help` on each): `atlas_split` cuts the body's skin by a region spec and REFUSES unless the
area adds back up; `atlas_features` regroups the split into the client's features; `atlas_colour` writes the
coloured review model, its legend and its facemap. The client clicks faces in that model and pastes FreeCAD's
selection lines; `kit atlas faces <file> --region <r> --facemap <map>_facemap.json` turns them into body faces.
`kit atlas set <r> --definition CLIENT --said "<the client's words>"` is the only way a region becomes citable.
**The gates that keep it true.** Once CAD exists and there is no atlas, the Stop hook asks at the end of every turn
whether now is the time to make one. A B-rep edit (`kit apply`, burrito S7) is refused until its new geometry is
assigned: `kit atlas assign <job> --to <region>`, or `--new <name> --what "..."` announced to the client. A FROZEN
region may sit inside a selection; it is recreated at the end of edits and `kit atlas recreated` measures it back
(material CUT from it refuses; material laid OVER it refuses unless the client allowed blends onto it).

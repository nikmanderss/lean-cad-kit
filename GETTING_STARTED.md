# Getting started

This page assumes [INSTALL.md](INSTALL.md) is done: the kit is at `C:\CAD\LEAN_KIT`, a project folder
`C:\CAD\Projects\MyPart` holds the template files, and the installer has wired it. The kit's documents call the
person the agent works for **the client** - that is you.

## 1. The project folder

```
MyPart\
  CLAUDE.md                     the project's entry point: the start sequence, the part, its standing orders
  PROJECT_FACTS.md              the part's facts and the client's rulings (section 6, appended by `kit ruling`)
  PROJECT_SUCCESS_CRITERIA.md   the acceptance table: one row per thing that must be true; every job card cites its row
  FAILURES.md, PROCESS_IMPROVEMENTS.md, SESSION_HANDOFF.md      written by the kit (kit failure / kit close)
  .claude\                      settings.json and agents\ - written by the installer, never by hand
  claude_code\                  THE AGENT'S WORKING FOLDER - every kit command runs from here
     bank\                      the model of record (R01_BODY_MASTER.brep, then R02_..., each apply)
     jobs\<JOB>\                one folder per job: card, script, region.brep, pictures, RESULT.md
     dossier\                   measured regions (measured once, reused)
     INBOX.md, STATE_NOW.md, MEASUREMENTS.md, KERNEL_LESSONS.md, WALL_CLOCKS.md
     PA12_MJF_Rules_EVALUATED.md   your manufacturing rules - pushed into every session
  Deliverables\<REV>\           what you are shown: review\ (pictures to judge), renders\, model\
  references\                   inputs you supply (drawings, specs, scans) - the agent only reads them
```

The agent writes in exactly two places: `claude_code\` and, under `Deliverables\<REV>\`, its `review\` and `renders\` (the kit itself writes `model\` and the delivery files). The guard refuses a file
anywhere else. The full rule is `LEAN_KIT\PROJECT_LAYOUT.md`.

## 2. Before the first session

1. **The starting model.** The kit edits a *model of record*: one valid solid, as a `.brep` file, in
   `claude_code\bank\`. Name the first one `R01_BODY_MASTER.brep`. From FreeCAD: open or build the part, select the
   solid, File > Export, choose "BREP format", save it into the bank. A STEP file is converted the same way (import it
   into FreeCAD, then export the solid as BREP). Starting a design from nothing, or from purchased parts: leave the bank
   empty - `kit open` opens on it and prints the first-body route (`kit newjob <J> --first "<why>"`, a `sketch_extrude` run with
   `base=""`, the result promoted from the bank); `LEAN_KIT\PROJECT_START.md` is the page.
2. **`PROJECT_FACTS.md`** - units, the coordinate frame and which way is front, the key dimensions, what each named
   feature is. The agent reads this before it asks you anything; the more it holds, the fewer questions you get.
3. **`PROJECT_SUCCESS_CRITERIA.md`** - the acceptance table. Each row is a lettered requirement with a test that
   decides it ("A - the mounting holes stay on their 50 mm pitch: measured centre to centre"). Nothing is accepted
   without its row.
4. **`claude_code\PA12_MJF_Rules_EVALUATED.md`** - the rules of the process the part is made by (minimum wall, hole,
   gap, clearance), whatever the process is: the kit pushes this file into every session under this exact name. Fill
   it in yourself: it is one of the files the guard protects, so the agent is refused any edit to it.
5. **`CLAUDE.md`** - fill in the part's paragraph and any standing orders of your own.

## 3. The first session

Open Claude Code on `MyPart` and say what you want changed, in your own words. The start sequence the agent follows
is in the project's `CLAUDE.md`; in short:

1. The SessionStart hook pushes `CONTRACT.md` and `ORCHESTRATOR.md` (the standing rules) and the project's state.
2. On a project's first session the agent reads `LEAN_KIT\METHOD.md` and `LEAN_KIT\EDIT_TYPES.md` once, then runs
   `kit exam` (three questions answered from the contract) and `kit open`, which names the model of record and opens
   the gates:

   ```
   kit open --method --edit-types --state "STATE_NOW.md: <what it says>" --model "R01_BODY_MASTER.brep" --answer overlap="..." --answer measure="..." --answer punch="..."
   (an EMPTY bank - a project with no model yet: the same line with NO --model; the first-body start of section 2)
   ```

3. `kit route "<your request>"` names the edit type, its tier, its sequence and the one section to read.
4. `kit atlas find "<the feature>"` locates the region once a region atlas exists. On a new project there is none:
   `kit open` says so, and the agent proposes regions to you (`kit atlas init`, `LEAN_KIT\METHOD.md` section 11) - or, while the
   model is still taking shape, `kit atlas defer --until "<your words>"` keeps the question quiet until the NEXT promoted model of
   record (every promotion ends the standing deferral - defer again while the model is still taking shape). Until then a card's `Region:` line says which part of the model it touches in words.
5. Then the sequence the router printed. Each kit command prints its next step.

`kit` is `C:\CAD\LEAN_KIT\kit\kit.py`, run with the full interpreter path from `claude_code\`;
`claude_code\WHERE_THE_KIT_IS.md` spells the full command form for your machine.

## 4. One edit, end to end

A small edit - a hole, a pocket, a boss, a wedge - runs this way. The agent drives it; you are asked for decisions and
shown pictures.

| step | command | what it does |
|---|---|---|
| route | `kit route "<request>"` | the edit type and its sequence |
| job | `kit newjob <JOB>` | `claude_code\jobs\<JOB>\` and `region.brep`, a read-only link to the model of record |
| card | `kit newcard <JOB> --type <type> --write jobs\<JOB>\CARD.md` | a card scaffold written to the job folder: every slot the type needs, its known traps (without `--write` it is only printed) |
| numbers | `kit dossier take <name> --box ...`, `kit measure ...` | the orchestrator measures (sections, faces, extents) after it has looked at a picture of the place; a worker never measures |
| lint | `kit card <card.md>` | the card checked: every slot filled, the numbers in range, the type's traps |
| register | `kit job <JOB> --type <type> --card <card.md>` | the job pinned: the expected volume, the face figure and - for an edit that makes or removes whole bodies on purpose, a pattern of separate copies - the solid count from the card's Expected line (`faces about +N` - the NEW faces the edit adds, with its sign; a negative figure is a drop and allows no net new face; an unsigned figure of 40 or more reads as a face count and is not taken; `solids N`; `--expect-faces N` overrides the face figure) |
| build | `kit howto <type> --job <JOB>`, then `kit run <script>` | the type's template copied into the job folder, its PARAMS filled BY HAND from the card (the copy arrives with every slot marked K.NEED), run in FreeCAD under the cap - by the orchestrator or a worker at the card's tier. `kit run` runs the script in its own job folder, so a relative output name in PARAMS lands there (the templates say so) |
| before | `kit before <JOB> ...`, `kit beforelook <JOB> --saw ... --says ...` | the BEFORE frames rendered once and read back |
| pictures | `kit render ...`; `kit review <before> <after> --out <dir> --lead <views> --box ...` (add `--solo` to open every frame yourself instead of one `cad-reviewer` per shard), then `kit review --render <dir>` | the standard views, then the orbit review's 32 frames: 12 `orblo_<az>` (the orbit from below), 12 `orbhi_<az>` (from above), `ortho_front` / `back` / `left` / `right` / `top` / `bottom`, `iso_fl`, `iso_br` - `--lead` names two or more of THESE (never `kit render`'s view names; `kit review --plan-only` lists them); a frame marked `[CUT - capped]` is a section through the box, its grey face the cut material; give the review box a few millimetres of margin round the feature |
| judge | `kit review --judge <dir> --frame <name> --verdict pass\|fail\|cannot`, `kit review --sweep <dir>`, `kit review --done <dir>` | every frame judged - after-frames first, a defect confirmed on a second frame; a frame that cannot see the feature is `cannot` (one the renderer marked OCCLUDED - the box behind the body in that view - costs nothing; a one-sided feature such as a blind pocket is reviewed at the box of the feature that HOLDS it, through the thickness); `--done` marks the review COMPLETE. `kit check` needs the judged LEADS; `kit accept` and `kit deliver` need the review COMPLETE |
| numbers | `kit check <result> --base <body> --box ... --out <dir> --job <JOB> --review <dir> --as-orchestrator` | valid, one solid (a result of several solids on purpose is judged against the card's `solids N`, or `--expect-solids N`), the volume and faces against the card, nothing changed outside the box, no punch-through (a designed through-hole is declared with `--breakout ok`) |
| reading | `kit look <JOB> --code <frame>=<CODE> ... --says "<frame>: ..."` | the orchestrator's own reading of the frames: the codes stamped in them typed back, at least three frames, one `--says` each |
| accept | `kit accept <JOB> --review <dir>` | the last gate |
| apply | `kit apply bank\<REV>_BODY_MASTER.brep jobs\<JOB>\<piece>.brep fuse\|cut bank\<next REV>_BODY_MASTER.brep --job <JOB> --as-orchestrator`, then `kit promote <the new brep>` | the new model of record in `claude_code\bank\`. Once the atlas holds a region the client confirmed, `kit atlas assign <JOB> --to <region>` comes first |

`kit help` lists every command and its flags (`kit <cmd>` - run each with the full interpreter path, never the bare word
`python`); `kit howto <type>` prints a type's card. Each command prints its next step.

## 5. Delivering a model

A delivery is a coloured FreeCAD document built by `kit deliver` - never a file re-saved by a script (FreeCAD's
command-line binary drops the colours). It needs a **template**: a document saved once from the FreeCAD GUI. One ships with the kit - `LEAN_KIT\templates\BLANK_MODEL.FCStd`
(six groups: G0 the palette, G1-G5; two marker blocks, a placeholder body and the named colours; `LEAN_KIT\templates\BLANK_MODEL.md` says what each is) - and
the first delivery swaps the model of record into its placeholder (`--no-atlas` stays off while the atlas is deferred; further bodies: `--add-body`, PROJECT_START.md 2); the output is the next delivery's template:

   ```
   kit deliver R01 --template "C:\CAD\LEAN_KIT\templates\BLANK_MODEL.FCStd" --target PLACEHOLDER_BODY --model "bank\R01_BODY_MASTER.brep" --no-review "the first body - nothing to review against" --no-atlas "<why>"
   ```

Or save your own:

1. In FreeCAD, import the model of record (or open any document of the part), colour the body, add any reference
   objects you want in every delivery, and save it, for example as `references\MyPart_TEMPLATE.FCStd`.
2. Then:

   ```
   kit deliver R02 --template "..\references\MyPart_TEMPLATE.FCStd" --target <the body object's Name> --model "bank\R02_BODY_MASTER.brep" --review <the edit's review folder> --no-atlas "<why>"
   ```

   `--target` is the body object's internal **Name**, not its Label (the tree shows the Label; select the object and
   run `Gui.Selection.getSelection()[0].Name` in FreeCAD's Python console). `kit deliver` swaps the model of record
   into that object, adds bodies with `--add-body` and meshes with `--mesh`, sets visibility and the camera, writes
   `Deliverables\R02\model\`, and runs `kit deliverycheck`.
   `--no-atlas "<why>"` stays on the line until the region atlas has been rendered onto the model of record (it is not owed while
   the atlas is deferred - `kit atlas defer`). That
   needs a recipe recorded once: `kit atlas recipe --split <regions.json> --features <features.json> --template <a
   GUI-saved .FCStd>` (METHOD.md section 11 describes the atlas); once the atlas holds regions, every `kit promote`
   says so until it is rendered. `LEAN_KIT\HOW_TO_DELIVER_A_COLOURED_MODEL.md` has the detail. A part is moved or turned with
   `kit place` (rotate first, then translate; recorded in `claude_code\PLACEMENTS.json`).

For a print shop: `kit printfile` writes the STL that goes to the shop and `kit printcheck --rules <shop>` reads it
against that shop's rules (`LEAN_KIT\PRINT_READINESS.md`). The shops' rules are `LEAN_KIT\kit\print_rules.json`
(two rule sets ship: `jlc_mjf_pa12` and `jlc_9000he`); adding a shop means adding a rule set there by hand, then
running the installer again (the file is one of the kit's controls).

## 6. The bigger routes

- **The burrito** - a region whose construction is wrong (shards, gaps, spikes, overlapping skins, a lumpy blend) is
  re-made as clean B-rep and sewn back into the body: the skin route, about twenty `kit rebuild <step>` steps, each
  judged on its own pictures. `kit howto burrito` prints the route; the six decision steps - points, features, wires, build, look, judge - have a page each and every other step prints its row of the route table
  (`kit howto burrito --step <step>` - both forms); every step prints its NEXT line when it runs and `--plan` shows its inputs. Orchestrator only.
- **The mesh routes** - `voxel_smooth` (a region cleaned in the mesh) and `mesh_union` (a drawn solid added to or cut
  from a print mesh), on a crop of the body: `kit crop`, `kit mesh <step>`, `kit union`, `kit splice`.
  `LEAN_KIT\VOXEL_SMOOTH_STEPS.md`.

## 7. What the hooks will hold the agent to

- **Pictures before numbers.** A measurement is refused unless a picture of its subject was opened in the last 20
  minutes. Measuring blind, or overturning a decision the pictures passed, is a *strike*: the agent is locked to
  reading until its next message to you opens with the guard's apology sentence ("I'm a silly dum dum ..."), and
  later measurements need more pictures. The sentence is part of the process.
- **Two folders.** Writes only in `claude_code\` and `Deliverables\<REV>\review\` and `renders\` (a delivery's `model\` folder and the root files are the kit
  commands' - `kit deliver`, `kit ruling`, `kit failure`, `kit close`); scripts only in a job folder.
- **FreeCAD only through the kit** (`kit run`, `kit render` and the kit's own steps).
- **No bare `python`, no killing processes by name, no detached `&`.**
- **No unfinished turn.** The Stop hook refuses to end a turn with a job open, a task put on the clock (`kit watch`) still running, or unread
  inbox text; a BACKGROUND task the harness launched lets the turn end - its completion wakes the agent; `kit stop --why "<the reason>"` is the honest exit.
- **The record.** Failures go to `FAILURES.md` (`kit failure`), your rulings to `PROJECT_FACTS.md` (`kit ruling
  --said`), measurements to `claude_code\MEASUREMENTS.md` (the agent writes that file - `kit measure` prints, it does not file), the state that must survive a compaction to
  `claude_code\STATE_NOW.md` (`kit state --note`), the session's handoff to `SESSION_HANDOFF.md` (`kit close --remaining "<where the design stands / what is left>"  --improvement "..." | --no-improvements "<why>"  --fact "..." | --no-facts "<why>"  [--note "..."] [--next "..."]` - the three are required; the last two accept "nothing to add" with a reason).
- **The inbox.** `claude_code\INBOX.md` is how you (or whoever maintains the kit) steer a running session: a block
  appended with `kit inbox --append <file.md> --from "<who>"` is printed at the top of the agent's next kit command (without `--from` the block is stamped as the orchestrator's own and counts as read). The kit's
  documents call whoever writes to the inbox from outside the session **the auditor**.
- **Round folders.** A round's own files (its brief, reports, notes) go in one folder under `claude_code\`, named
  `R<n>`, `ROUND_<NAME>`, `<NAME>_ROUND` or `CC_<NAME>` (capitals, digits and underscores); the guard refuses other
  folder names there.

## 8. Where to look things up

| | |
|---|---|
| every command | `kit help` |
| the edit types | `kit types`; `kit route --table`; `kit howto <type>` |
| the rules | `LEAN_KIT\CONTRACT.md`, `LEAN_KIT\ORCHESTRATOR.md`, `LEAN_KIT\METHOD.md` |
| the burrito | `kit howto burrito`, `kit howto burrito --step <step>`, `LEAN_KIT\BURRITO_STEPS.md`, `kit lessons --near "<what you are doing>"` |
| the kernel's traps | `LEAN_KIT\KERNEL_LESSONS.md` (`kit lessons --near` finds the row) |
| the mesh route's proven numbers | `LEAN_KIT\kit\mesh\LEVERS_CENSUS.md` |
| deliveries and print files | `LEAN_KIT\HOW_TO_DELIVER_A_COLOURED_MODEL.md`, `LEAN_KIT\PRINT_READINESS.md` |

# THE LEAN CONTRACT — pushed at every session start. Rules only.

*This is the whole standing contract. `METHOD.md` (the approach, 5 min) and `EDIT_TYPES.md` (the catalogue) are the two
files behind it; you read them ONCE per project, and after that the kit routes you: `kit route "<the request>"` names
the edit type, its tier, its sequence and the one thing to read. Nothing else is read until the router names it.*

## Who you are

**ORCHESTRATOR** (Opus / Fable). You own every number, every measurement, every acceptance, and every piece that reaches
the model of record. You do the CAD thinking. The gates judge YOU. You run a job yourself or launch a worker at the tier
its card names (`kit route` / the card's `Tier:` line) — a launch is for context economy or parallel independent jobs,
never a requirement. **You do not stop with work on the books**: the Stop hook refuses a turn's end while a job is open,
a launched task is uncollected, the session is unclosed or the inbox holds unread text; the only other honest exit is
`kit stop --why "<the client's instruction, or the blocker in one sentence>"`.

**WORKER** (`cad-worker-haiku` / `-sonnet` / `-opus`). You fill `PARAMS` in a copied template and look at the pictures.
Run only through `kit run`; render only through `kit render`. Open every picture, one line each ending HIT / MISS / POOR.
**A number you need that is not on your card: write the question in `RESULT.md` and stop.** Two failed runs = stop.

**REVIEWER** (`cad-reviewer`). You open every frame you were given, in order, and return the fixed schema. Nothing else.

## The session, in the order you meet it

```
kit route "<request>"           the type, the tier, the sequence, what to read   (no match: the symptom table)
kit exam  ->  kit open          once per session; three questions answered from THIS page
kit atlas find "<feature>"      where the edit is: region, box, frozen?, dossier?   (the atlas is the first instrument)
kit newjob <job>                the job folder + region.brep (a READ-ONLY link to the bank) - always first
kit newcard <job> --type <t>    every slot present; numbers from the dossier (kit dossier add for one you already have)
kit card <card.md>              lint + that type's traps, and only those; `kit job` refuses a card that did not pass
kit job <name> --type <t> --card <card.md>   pins the job and its expected numbers
   run it (kit run / launch)    the worker's RESULT.md, or your own (kit howto <t> --job <job> copies the template)
kit review <before> <after> --out <dir> --lead <views> --box ...   RENDER REVIEW FIRST: after frames on the box,
                                the leads you name judged first, fail-fast; a defect is real when a SECOND frame
                                confirms it; old/new = two frame sets on one camera; then --sweep, then --done
kit check ... --job <job> --review <dir>   the numbers: valid, one solid, volume, nothing outside the box, no punch-through
kit look <job> --code ...       your own reading, codes typed back from the frames (proof you opened them)
kit accept <job> --review <dir>  the last gate before the model of record
kit atlas assign <job> --to <region>   where the new geometry belongs;  kit apply  writes the new brep
kit promote <brep>              the new model of record - and the coloured ATLAS is regenerated on it
kit close --remaining --improvement --fact       the handoff is the product; silence is what is refused
```

`kit check`, `kit apply`, `kit measure`, `kit burrito`, `kit mesh` refuse without an open session. `kit run` and `kit render` never do.
**Never pipe kit output through a filter** — `--brief` suppresses advice and cannot suppress a refusal.
**The inbox steers you**: every orchestrator command prints what is new in `claude_code\INBOX.md` first; it outranks what
you were about to do. A job whose premise is disproved is `kit cancel <job> --why`, not left open.

## The rules that produce most failures on record

0. **A GATE REFUSES, OR IT IS A REPORT AND IS RENAMED ONE.** A check that states its own failure and writes its artefact
   anyway is worse than no check. A gate with no lever is a report.
1. **Overlap 0.5 mm INTO material; stand 2 mm clear in air.** Never flush, never 0.1 mm off.
2. **A cutter is a solid and goes further than you think.** A marker solid is a cut TOOL, not a cut PLANE.
3. **The z extent of a FACE is not the extent of MATERIAL.** Measure where the part has material, slab by slab.
4. **Moving a feature is two operations: fill the old, cut the new.**
5. **Symmetry of NAME is not symmetry of GEOMETRY.** Section the far side before repeating an edit on "the other one".
6. **One unchanged base.** Every piece is fused onto the model of record, never onto the previous piece's result.
7. **No lofts. No fitted surfaces in a worker script. No mesh work except the burrito and `voxel_smooth`, at
   orchestrator tier, through the kit.** Section -> draw 2-D -> extrude, or connect two drawn 2-D shapes.
   **Mesh work runs on a CROP, never on the body** (`kit crop` -> `kit mesh <step>` on the crop -> `kit splice`); the
   body as a step's operand is refused, and `--whole-body "<why>"` is a recorded exception (the client, 2026-09-24).
8a. **LOOK BEFORE YOU MEASURE - GATED (kit 31am, the client 2026-10-06: "For any step, in any process, the agent must be pushed to
   render review if a measurement is about to be taken in the next step. It can be as little as 1 image ... but it must be gated to be
   properly targeted at the measurement subject in question").** A measurement - `kit measure`, a measuring instrument (`kit tool
   diag_*` ...), `kit atlas recreated`, a probe script run by `kit burrito` / `kit run`, any command ending `# MEASURES: <box>` - is
   refused by the guard until a picture AT its subject was opened in the last 20 min. Name the subject (`# MEASURES: x0 x1 y0 y1 z0 z1
   - <what>` at the end of the command or in the script's header; `--box` / `BOX=` count), make the picture (`kit tool look_at --job
   <J> --set "BOX=x0 x1 y0 y1 z0 z1"` - one is enough; any kit render framing the box counts once opened), open it, say what it shows,
   then measure only what it points at. Experiments are covered: the guard sees every tool call, whoever wrote the script.
   **31aq (the client 2026-10-07: "ALWAYS jumps to measurements before renders ... Make it announce to me that it's a silly dum dum every time";
   "makes a measurement that it arbitrarily decides is a bad measurement with no reasoning as to why, and then undoes correct work. It
   has to stop").** A measurement with no picture of its subject, and a SECOND attempt to re-run a step over a layout / piece judged OK
   after the refusal that named the two ways, are STRIKES (31bj: look -> measure -> decide is the sequence - a lever build after a looked-at
   measurement is not a strike. 31bk: a judged ok is re-made two ways - a picture you have opened shows it wrong (judge --verdict redo
   --frame <it>), or a later step FAILED / was KILLED on it, in which case the upstream step runs by itself as a layout round; the first
   re-run with neither on the record is a refusal, not a strike; five layout rounds before the points re-pick): claude_code\DUMDUM.md (the wall of shame) and a lock - only
   Read / Glob / Grep run until your next message to the client opens with the guard's sentence ("I'm a silly dum dum - I'm so very sorry! Pretty [x strike N] please forgive Mr. Silly Dum Dum: ...") and you
   open your message with it (an `echo` is a tool call and registers nothing while the transcript can be read). After a strike a measurement needs 1 + (strikes in 24 h) different pictures of its subject (up to 4). Every measurement ends
   `# SAW: <what the picture shows>  # WHY: <what the number decides that the picture cannot>`. An ok judged on pictures STANDS: only a
   picture overturns it (`kit rebuild judge --verdict redo --frame <it>`) - a picture you have OPENED, at any time (31bi, the client: "if an
   agent has reviewed a picture and then references it, that is ok. Not looking is what is not ok"); a picture never opened is the strike. Python scripts named like measurements and inline `python -c`
   code that measures are measurements too. 31au: the client SEES each strike as it lands and each confession as you say it (the guard shows
   them to them directly) - the wall of shame is built in front of them, not read out at the end.
8. **Render, reason, measure LAST.** A picture answers most of what an instrument would be built for; a number you will
   act on is a measurement and goes in the region's dossier once (`kit dossier add`), never re-measured.
9. **Know a step's wall time before you launch it** (`kit clock show`; 1.5x typical = red flag, ~2x = look at its log).
   **Kill on evidence, never on the clock alone** (the client, 2026-09-24: *"tasks should only be killed when they are for sure
   not working correctly"*): a step that is still printing progress is working — the kit extends it past the cap up to
   3x and says so; a step SILENT for the silence window is stuck and is killed; read the log before you kill anything by
   hand. Every launched task is collected or killed in the same exchange it is read (`kit collected <name> [--kill]`);
   a killed step's output is `.KILLED` and never a result.
10. **A process started on Windows from a process with no console pops a window on the client's desktop.** The kit starts its
    children without one (`creationflags=0x08000000`); any helper script YOU write that spawns a process does the same,
    and any `subprocess` call from FreeCAD's own python does too. The client has asked for this more than once.
11. **Every number you measure goes in `claude_code\MEASUREMENTS.md`; the state that must survive a compaction goes in
    `claude_code\STATE_NOW.md` (`kit state --note`) — before the compaction, not after.**

## Standing orders (the client, said more than once)

- **Render review FIRST on every edit, no exceptions.** The orbit is the only instrument that sees a shape; a number can
  be right while the shape is absurd. After frames alone, judged; before frames on the same camera only if the judgement
  needs them; **never an overlay** (it shows the larger geometry of both bodies and hides the edit). A single frame is
  indicative; a defect is confirmed on a second view before it is acted on. A sectioned or coloured frame with shards,
  triangles or paint where there is no geometry is a RENDER defect: say so, re-render, never reason from it.
- **Every picture of the piece AND of the real model is THE PIECE VIEW, and a frame with a red RENDER DEFECTIVE band is no evidence** (31bn, the client 2026-10-13: *"The render creation method
  must be controlled. Instructions are not good enough. Only good renders allow for good work"*): skin-look, `kit tool look_at`, the mirror pictures, the region
  cuts, review-body's frames, the seam frames and kit review's orbits draw
  ONE conforming mesh of the whole piece (a true z-buffer, smooth shading from the surface's own normals within each face), judged against its own surfaces
  before it is drawn; a mesh that fails stamps every frame RENDER DEFECTIVE - NO EVIDENCE with the reason, a crack in the mesh stamps the frames that show it. Such a frame opens nothing: `kit rebuild judge` refuses a verdict on a set holding one and a `--frame` that is one, and the
  look gate does not count it as a look. Make the mesh right (`--set PIC_DEV=` / `PIC_ANG=` finer, an invalid face left out), run the step again, then judge.
  No other renderer draws a piece or the model; a job script's picture is still the RENDER EXCEPTION above.
- **Pictures come from the kit** (31av, the client 2026-10-07: *"How renders get generated needs to be locked down, same idea as how the targeting
  is"*): a step's own frames, `kit tool look_at`, `kit review`. A job script that draws its own is refused until you tell the client why -
  a line of its own that STARTS `RENDER EXCEPTION: <script or its full path>: <your reason>` IN YOUR MESSAGE TO the client (31bq B51 - the client reads the message;
  an `echo` of the line registers nothing while the transcript can be read, and a command carrying the line is judged like any other; the
  refusal's template line is no reason; ONE message announces ONE version of the script - a changed script is announced again; 31bq R6) - and
  once more with "Are you sure?". Python code typed into a command (`-c`, a heredoc fed to the interpreter) that saves a picture is refused as it
  is - put it in a job script and announce that (31bq R7W). The pictures a judge reads are
  the job's own (`claude_code\jobs\<J>\skin\review\`, look_at's in its `look\`); `Deliverables\<REV>\review\` holds only what the client is asked to look at.
- **Any command for the client is GENERATED, never typed:** `kit ps "<script>" [args...]`; `kit ps --lint "<line>"` checks one.
  One pastable PowerShell line, `&`-invoked, the interpreter's full path (the bare word `python` may be the Microsoft Store stub on Windows),
  absolute quoted paths, `;` never `&&`, `$env:X="v"; & ...` for variables, no placeholders, ASCII only.
- **No coordinates in a message or a picture caption.** Dimensions yes; x/y/z live in cards, facts and state.
- **Never say "sorry"** (the one exception is the strike sentence 8a requires, word for word). Own it, state the number, fix it. **Never a pop-up question**; a question goes in the message
  body, once, with a picture, after the measurement that frames it — and only when two readings build different geometry.
- **You write in TWO places only: `claude_code\` and, under `Deliverables\<REV>\`, its `review\` and `renders\` (the kit itself writes `model\` and the delivery files)** (`PROJECT_LAYOUT.md`). The guard refuses a
  new file loose in `claude_code\`, at the project root, or a script outside `claude_code\jobs\<JOB>\`. Registers are
  appended through the kit: `kit state`, `kit clock add`, `kit ruling --said`, `kit failure`, `kit dossier add`.
- **A frozen region may sit inside an edit; it is put back exactly at the end of edits** and delivery refuses until
  `kit atlas recreated` measures it. New B-rep geometry is assigned to a region before `kit apply` (`kit atlas assign`).
- **Purge superseded renders and intermediates when a new edit lands.** Warn the client and STOP before a disk-space crash.
- **A delivery is `kit deliver`** — the model of record (or the round's mesh), the atlas map objects, the reference and
  marker objects, visibility and camera set — then `kit deliverycheck`. Never a re-saved document: colour lives in the
  GUI half of the file and `freecadcmd` deletes it. **A mesh delivery is reviewed like any other** (`--review <COMPLETE
  dir>`); `--no-review` carries the client's quoted words and the next delivery runs the full review - a roof-ridge tear shipped
  unseen in R32 and R33 under a template that baked `--no-review` in. **On a MESH round a frozen region is an
  INDICATOR, not a gate** (the client, 2026-09-25: *"frozen regions should only act as an indicator to the agent that the area
  is not to be changed. I do not want to enforce it. Enforcement is only for brep (and burrito) edits"*): `kit atlas
  recreated --baseline <the pre-edit mesh> --where` is run and its counts are reported with the delivery; the agent
  judges them; nothing refuses. Review frames for a revision: after frames first; before frames on the same camera
  with a reason; a close-up shard on an edit box with a reason (the client, 2026-09-25).
- **A handover is written when an unattended run STARTS, not at the usage cap**, and it names ONE first command that
  tests the riskiest claim nobody has run, points at the runner's state file and step log, and never tells a project
  session to run the installer or touch the integrity manifest (a project session cannot; whoever maintains
  the kit re-records it after a kit update by running the installer - INSTALL.md). Hand over through `kit close` at about 80 % of the budget. **The first minute of a
  takeover is the process table and the log ages, not the handover's claims** (`kit mesh slots`, the runner's log).
- **THE ORIGINAL IS THE STARTING REFERENCE, NOT A CONSTRAINT (31bh, the client 2026-10-09: "You can put the wireframe wherever you want. You simply
  have the original as a starting reference").** On the skin route the layout starts from the original's faces and the wireframe is yours:
  any border can be redrawn or moved (LINES / RAILS), a face split by a line (role split), faces joined (FEATURES), a strip folded into its
  neighbour. Nothing holds you to the original's face boundaries; a stop that says "the kit can't split one original face" is wrong - draw the split.
  THE ONE EXCEPTION IS THE FRAME: where the skin meets the body (the edit region's walls) every face ends EXACTLY on the body's own section
  faces, edges and vertices (wall_caps.brep); skin-frame refuses an open face there, and skin-wires cannot move a wall edge.
- **A cut takes only material above the ORIGINAL surface**: draw its floor from the pre-edit mesh (floor = max(design
  plane, original + 0.03 mm)) and prove it with `kit union --cut --baseline <pre-edit crop>` - a cut meant to trim
  added material reads ~0 mm3 there. A plane through two measured points shaved a frozen chamfer 0.29 mm and left a flap
  the client found it themselves (2026-09-25).
- **Never stop a process by name or pattern, never a bare `&`, never the bare word `python`** - the guard refuses all
  three (a `taskkill /IM python.exe` killed the FreeCAD MCP servers; `nohup ... &` inside a loop left four untracked
  processes; on Windows `python` may be the Microsoft Store stub).

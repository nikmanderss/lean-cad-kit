# ORCHESTRATOR — how to be right about geometry (pushed with CONTRACT.md; rules and facts, not history)

## 1. The three that would have prevented almost everything

1. **Orbit-render every part before delivery and OPEN every picture** — twelve views, then close-ups of what you edited.
   A number can be right while the shape is absurd (two 64 mm fins stood through three deliveries with every check green).
2. **After a boolean, measure what changed OUTSIDE the region you meant to change.** A cutter is a solid; it does not stop
   where your intention stops. `kit check` sweeps a 3 mm collar round the box; `--whole` sweeps the footprint on the client's word.
3. **Ask only when an instruction has two readings that build DIFFERENT geometry** — once, with a picture of each, after
   the measurement that frames the choice. The record has usually answered it: the client's own words and corrections
   first, measurements the client confirmed next, an agent's derivation last, however recent. When sources disagree, that
   disagreement is the finding; resolve by authority and write the correction beside the wrong line.

## 2. Geometry facts that have each cost a round

- **A marker solid is a cut TOOL, not a cut PLANE** (9.2 mm3 intended, 900 mm3 removed through the aft flank).
- **The z extent of a FACE is not the extent of MATERIAL.** Measure material in the footprint slab by slab before a fill.
- **Moving a feature is two operations: fill the old, cut the new.**
- **"Solids: 1" does not mean attached.** Measure the contact area (a 0.5 mm slab through the joint plane / 0.5); a joint
  carrying a bolt is tens of mm2, not single digits.
- **Write the constraint as an inequality before you draw.** No solution in the shape you want = the shape is wrong.
- **Wall thickness: measure it.** A 4.0 bore down a 10x10 post leaves exactly 3.0. List every clearance.
- **Symmetry of NAME is not symmetry of GEOMETRY.** Section the far side and look.
- **Booleans on heavy bodies lie sometimes**; where a boolean and a probe disagree, trust the probe and a render.
  `BoundBox` on spline faces is the untrimmed surface's box — never quote it as a feature extent.
- **Coincident faces break booleans.** A cut plane exactly on an existing face removes one side only; offset by a micron.
- **Face numbers from the client are 1-based**: `Face527` is `Shape.Faces[526]`.
- **`isValid()` is True on an empty shape**; count solids and volume first. A fuse can MANUFACTURE volume at a
  near-coincident seam and report success (`KERNEL_LESSONS.md` — read the row for the operation you are about to run:
  `kit lessons --near "<what you are doing>"`).

## 3. Measuring — how much is enough

**RENDER -> REASON -> MEASURE LAST** (the client: *"No rays. You should know what cross section you are looking at from renders
and be able to reason from that what it is first. Only measure as a LAST resort."*) The order: the boxed frames and the
dossier's sections -> say what the shape IS, in words, and what would prove you wrong -> the dossier's numbers to
confirm -> a card. A bare `kit measure` is the last resort; the instrument CLOSES at the fourth bare section / rays / dihedral / faces measurement since the last card (three run; a card, a dossier or `kit failure` reopens it).

- **Tolerance classes 0.30 critical, 0.10 seal, 1.5 working band.** Report at class resolution; `kit card` warns on more.
- **Never take a picture of the same thing twice.** The survey's frames of a box ARE the before-set (`kit before <job>
  --frames <survey dir>`); a fresh render is owed only for something a measurement found that no frame shows.
- **Before building an instrument:** can a render answer this? which `PARAMS` field does the number fill? If you cannot
  name the field you are exploring — say so and time-box it. **When the kit lacks the command you need, say so
  (`kit failure`) — do not write a script beside the kit.** 85 bespoke scripts and 4,412 lines is the record of that.
- **Sections check a PROFILE; renders check a SURFACE.** A defect along the section axis is invisible in any number of
  sections and obvious in one isometric. Take both.
- **Quote a BOUND before an INTEGRAL**, and every number in a caption is computed by the run that drew the frame.
- **A rainbow render proves face BOUNDARIES; a size census proves face AREAS.** Intersect them before claiming they agree.
- **MEASURE ONCE — the dossier.** A region is measured once (`kit dossier take <name> --box ...`: sections, profiles,
  face census, boxed frames, one kernel call) and every card on it is written from those numbers; a number you already
  have goes in with `kit dossier add`. `kit job` refuses a card on a STALE dossier (its box was applied to). Take one
  when an edit needs its numbers; never re-take one because it lapsed. `kit dossier list` is UNCHECKED before `kit open`.
- **The self-intersection test (`kit check --bop --because "..."`) walks every face pair and needs a reason.**

## 4. Running the work

- **The one who writes the card runs it**, or launches a worker at the card's tier. A launch pays for CONTEXT (~50k tokens
  per job stays out of yours) and for PARALLELISM when features are independent; a chain of dependent features is run
  in order, about 3 minutes per feature, and is not contorted into a batch. Do not launch a one-line change, or anything
  you cannot state a far limit for without measuring first.
- **The wall clock.** Know the number before you launch (`kit clock show`; `WALL_CLOCKS.md` is the table and the hook
  reads it). Over 1.5x typical: find the cause. Over ~2x: stuck — cancel and restructure. Never wait on a file without
  checking the job writes it. Every launched task is collected or killed in the same exchange it is read; a foreground
  bounded wait beats a background wrapper. Before any hand-off, kill what is running (`kit collected <name> --kill`,
  `tasklist /FI "IMAGENAME eq freecadcmd.exe"` for orphans — by PID, never by pattern). The PostToolUse hook watches
  your own launches; `kit watch <name> --expect <min> --pid <N>` puts on the clock what it cannot see.
- **The orbit review runs in parallel** (`kit review <before> <after> --out <dir> --box ... --lead <views> --shards 6`): one kernel step
  (tessellate, once, alone), then numpy frames six-up, then one `cad-reviewer` per contiguous ARC (a sweep shows
  motion; a defect that appears, rotates and disappears is easier to see). Nothing renders or opens fewer frames — the
  speed removes the excuse for skipping it. A shard that returns `pass` without listing every frame has not reviewed;
  one dead shard fails the review; purge superseded renders from the folder before you start. Then YOU open the
  flagged frames plus the after top view and one iso, and supply the verdict — it is yours and is not delegated.
- **A review of an edited region** (the client: *"pixel level accurate to tolerances"*) adds the section picture (planar sections
  of the original under the build, mm axes), the cover-from-above numbers, and `kit render` close-ups of every edited
  region at a stated mm/px. A `CANNOT-JUDGE` on an orbit frame means go and cut the section.
- **Waiting is not a tool call** (the R33-R35 round, 2026-09-25: 244 of 312 tool-minutes were foreground `until ...;
  sleep` loops; the client's questions sat unanswered up to 10 min at a time and the client killed tasks; a promise to stop did not hold
  seven minutes). The guard now refuses a foreground loop with `sleep`, or a `sleep` of 60 s or more. Launch with
  `run_in_background` (its completion wakes you), or arm a Monitor on the log's VERDICT line (`PIECE`, `STOPPED`, `rc`,
  `DONE`), and every stage before the end of a Monitor pipeline is line-buffered (`grep --line-buffered`, `awk` with
  `fflush`; a `| cut` at the end block-buffers and delivered nothing for 30 min). Never a Monitor on an agent's progress
  lines - read its `STATUS.txt` on demand. Then END THE TURN with a 3-6 line status; the stop guard lets a turn end when
  launched tasks are all that is on the books (`kit stop --until <ids>` covers a stop that also leaves a job open). An
  unprompted one-line status to the client every 30 min of long work.
- **One item per agent, capped, with a status line per step** (2026-09-25: single agents with a 30-45 min cap, a
  narrow defect list and a `STATUS.txt` line per step finished in 11-31 min; the open-ended six-designer workflows ran
  159-167 min on their slowest item alone). The brief states the RULE, not the form (*no wall under 0.8 mm; a working
  channel*), allows "nothing to do", requires CHECK / RETURN lists and a "not fixed, and why" section, gives coordinates
  or says "unknown", names the base by path AND md5, and demands a best-so-far file the moment a trial passes. Measure in
  3-D before drawing (fit planes to the ring round the defect; section at several stations; compare to the model of
  record to tell designed shape from defect). Workflows are for read-only fan-out (takeover readers, review shards).
- **A checker per spliced plan, and never a splice on a STATUS line.** The checker asks "is this the client's place?" first
  (back-project their mark through the render camera; a picture titled R32 was painted on the B-rep test mesh and the
  fill went 10 mm from their circle), re-measures with its own instruments, is capped at 15-20 min and returns a verdict,
  numbered defects with coordinates and a trial-run fix. A piece whose last independent check FAILED goes in only after
  a fresh check of the fixed files - or ships marked "not accepted" with its failing numbers in the README. Apply only
  after the verdict, never on a STATUS.txt line while the agent is still rendering.
- **A runner never checks or delivers an incomplete chain, and only judgement-free steps run unattended** (union,
  splice, printfile, printcheck; a voxel piece that a gate refuses needs a judgement no script can make). A README is
  written from measured results after the model exists, never as a skeleton ahead of it; the source STL stays in the job's work folder
  (`claude_code\jobs\<J>\work\` - only `kit printfile --out` / `kit deliver` write into `model\`), never beside the print file (the client took the 163 MB source for the print file).
- **An agent's reading of the client's words is a READING, not a ruling**: `kit ruling --reading "<it>" --of "<the client's words>"`
  files it under READINGS, NOT RULINGS; `kit ruling --said` refuses text that reads like one. A ruling is their words.

## 5. The record's verdict on this role

Of 165 jobs run under this method on the first project, workers rendered honestly on 153; the acceptance instrument was
run on 3, and 85 bespoke orchestration scripts were written instead. `kit accept` now refuses an apply that was never
checked and never looked at. The lesson that carries: the failures are the orchestrator's arithmetic and the
orchestrator's shortcuts — 41 % of hand-backs flagged a card defect — and every one of them is caught by a complete
card, a render opened, and a number read off the dossier rather than remembered.

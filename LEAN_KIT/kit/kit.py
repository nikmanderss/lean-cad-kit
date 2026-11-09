#!/usr/bin/env python3
r"""kit.py - the one command for CAD work on a lean-kit project (it serves whichever project you run it from).
`kit <cmd>` below is the form the project pushes (`& "<the interpreter>" "<LEAN_KIT>\kit\kit.py" <cmd>` in PowerShell - never the bare word python: the guard refuses it on Windows; 31bs K8).
Plain python; every geometric step runs in a freecadcmd subprocess with a hard timeout (a hung kernel
call ends the subprocess, never the caller).

WORKER commands
  kit facts <word> [<word>...]         one-line facts that mention the words (PROJECT_FACTS.md; FACTS.md where a project already has one)
  kit templates [--orphans]            every worker copy vs its template; run before AND after editing a template body
  kit levers [<job folder>] [--env f]  every env-var lever the folder's scripts read, its default, and whether it is set
  kit levers --census | --check         the lever census (LEVERS_CENSUS.md): CARD / CONSTANT / DEAD, filled by the agent; CARD levers must be set every run
  kit lessons [--near "<text>"]        the burrito lessons indexed (number, title, gaps, collisions); --near: what a new one would sit beside
  kit paths [<file.md> ...]            every backticked path the entry points name, resolved; the dead ones listed (default: the project's CLAUDE.md)
  kit priorart <job folder>            the scripts already in a job folder, ranked (ruling first, families collapsed) - name the one you apply before writing a new one
  kit burrito <step|script> --tag T    run one step of the burrito chain through the kit (orchestrator tier); --plan to see, --bg to detach
  kit rebuild <step> --job J --tag T   run one step of THE BURRITO (the skin route, kit\rebuild\): region, skin-source, reinsert, skin-regions / skin-edges / skin-points / skin-labels / skin-features / skin-rim / skin-mirror / skin-network / skin-frame / skin-wires / skin-build / skin-look, judge, second, restore, review-body (the voxel field's arrange / blend / repair / decimate / fillholes / finish / brep are SHELVED); --plan, --bg
  kit stop --why "..." [--until <bg-ids,...>|tasks]                 record a reasoned stop; the Stop hook refuses to idle with work open otherwise
  kit route "<the request in words>"   the edit type, its tier, its sequence, what to read (--table: the map)
  kit howto <edit_type> [--long]       the edit-type card (+ its template copied as w_<type>.py into a job folder: --job <J>, or run from inside one) (--long: its long form; burrito --step <step>: one step's page)
  kit run <script.py>                  run a FreeCAD script under the guard (forbidden-call scan, cap, log)
  kit render <shape.brep> --out <dir> [--box x0 x1 y0 y1 z0 z1] [--views std|all] [--name N] [--job <J>]
                                    [--faces 337,338,342] [--light grazing] [--whole]
                                                 the standard pictures (no numbers). --faces paints
                                                 the client's named faces (1-based) orange and frames them;
                                                 --light grazing lights a flat flank from the side;
                                                 a boxed render skips the whole-part frame unless --whole.
ORCHESTRATOR commands  -- EVERY one of these carries --as-orchestrator at the end. The PreToolUse
                     guard refuses check / apply / measure without that token (a worker must never
                     run them); the kit strips it, so it is harmless on the rest.
  kit check <result.brep> --base <base.brep> --box x0 x1 y0 y1 z0 z1 --out <dir> [--expect +|-|0] [--faces N] [--expect-solids N] [--breakout ok] [--wide-box "<why>"] [--whole] [--bop --because "<why>"] --job <name> --review <dir> --as-orchestrator
                     --job is what marks the job CHECKED. Without it `kit accept` still refuses. --review names the
                     job's render review (its LEAD frames judged) - RENDER REVIEW FIRST, the numbers after.
                     The box is the CHANGE's box plus a small margin: a box 25x the change is refused.
  kit apply <body.brep> <piece.brep> fuse|cut <out.brep> --job <name> --as-orchestrator
                     refused until `kit atlas assign <job> --to <region>` names where the new geometry belongs.
  kit measure <shape.brep> bbox | section x|y|z <c> [--out png] [--box x0 x1 y0 y1 z0 z1] [--grid G] [--profile --step S] | faces ... | rays ... | dihedral ...  [--dossier <name>]   (kit measure --help: every form)
                     | rays z <x> <y>  |  rays z 0 0 --grid x0 x1 y0 y1 [--step S]   (many rays, one call)
                     | faces [--min A] [--max A] [--box x0 x1 y0 y1 z0 z1] [--only 337,338,342]
                             [--normal 0,0,-1 [--tol-deg 10]]     (10 is the default; it is MEASURED)
                     | export [--dev D]
                     | dihedral --box x0 x1 y0 y1 z0 z1 [--min-len L] [--worst N] [--control]
                     `faces --box` censuses the faces in a region; `faces --only` lists named faces;
                     `faces --normal` finds a FEATURE by the direction its faces point - the only
                     selector that survives a revision, and how the `cutter` type finds its target
                     (the client's 1-based numbers) with their areas and extents.
                     `section --box` ZOOMS the frame to the box (the two axes not cut); without it
                     the whole body is drawn at ~0.3 mm/px, which cannot show a 0.30 mm feature.
                     `dihedral` is the crease instrument: shared edges in the box, worst fold first;
                     its sign convention is calibrated on a box at every run and `--control` proves it.
                     `rays` casts DOWN Z at (x, y) and reports the runs of material it passes
                     through. It is z-only; the synopsis used to say `rays x|y|z` and the usage
                     string said `rays z x y`, which contradicted each other in one file.
  kit types                            list the edit types

GATE commands (orchestrator; see leangate.py for why each exists)
  kit exam                             the three session questions
  kit open --method --edit-types --state "<file>: <what it says>" --model "<path to the .brep, not a description>"
                     --answer overlap="..." --answer measure="..." --answer punch="..."
  kit newjob <name> [--from <brep>] [--first "<why>"]    job folder + region.brep from the model of record (--first: the very first body, no base)
  kit newcard <job> --type <edit_type> [--title ...] [--base ...] [--out ...] [--write <path>]
                     a card scaffold with every required slot + that type's traps
  kit before <job> [--box x0 x1 y0 y1 z0 z1] [--frames <dir> [--prefix <name>]]
                     YOU render the BEFORE frames once and put them on the card. The worker
                     opens those and renders only the AFTER frames, from the same box.
                     --frames REUSES frames that already exist (the survey's) instead of
                     rendering the same thing again: copied into the job, stamped, gate satisfied.
                     A fresh render is owed only for something a measurement found that no frame
                     shows (the client, 2026-09-10).
  kit beforelook <job> --saw <frame>=<CODE> [--saw ...] --says "..." [--says ...]
                     YOUR reading of the BEFORE frames: the codes stamped in them, typed back,
                     and one honest line per frame. RENDER FIRST is this pair: `before` renders
                     and stamps, `beforelook` proves you opened them, and `launched` REFUSES
                     until both are done. (It was missing from this list on 2026-09-10 and an
                     orchestrator concluded it did not exist.)
  kit cancel <job> --why "<the premise that failed>"
                     retire a job whose premise is disproved: off the wall clock, out of the
                     handoff's "pick these up first", kept in the register as CANCELLED.
  kit inbox [--wait <seconds>] [--append <file.md> [--from "<who>"]]
                     instructions from the auditor / the client arrive in claude_code\INBOX.md. Every
                     orchestrator command prints what is new there, once, marked *** INBOX ***.
                     --wait blocks until something arrives (give the Bash tool a longer timeout).
                     --append posts YOUR block from a file, verbatim, under a stamped heading:
                     never `cat >>` or a heredoc (quoting ate a block and a \r ate a path).
                     --from names a writer who is not the orchestrator: the block stays UNREAD.
  kit dossier take <name> --box x0 x1 y0 y1 z0 z1 [--axis x|y|z] [--stations 3] [--step 1]
                     MEASURE ONCE: sections + profiles + faces census + boxed frames of one region
                     in one kernel call, kept under claude_code\dossier\<name>. `dossier list`,
                     `dossier show <name>` (the numbers, no kernel), `dossier refresh <name>`.
                     Any `kit measure ... --dossier <name>` files itself into it; `kit before <job>
                     --dossier <name>` reuses its frames; `kit apply` marks touched dossiers STALE.
                     Cards carry `Dossier:`; `kit job` refuses a missing or stale one.
  kit repath --from "<old root>" --to "<new root>" [--apply]
                     After the tree MOVES. Rewrites a stale absolute root inside this project's
                     LIVE STATE only - the dossier, the session, the registers, card files,
                     WINNING_ENV. It never touches a RECORD (status_*, GATE_*, burrito_plan, look
                     manifests, logs, _archive): a path in those is what actually happened, and
                     rewriting it falsifies evidence. Dry run unless --apply.
  kit stitch <a.stl> <b.stl> (--box x0 x1 y0 y1 z0 z1 | --plane z=5.0) --out <r.stl> [--tol 0.15]
                     ROUTE C: one mesh from two - A inside the boundary, B outside, joined along it.
                     THE BOUNDARY IS A FIELD, not a plane: box, plane, sphere, cylinder or a distance
                     field, found by bisection. It REFINES each rim with the other's points and welds
                     one-to-one; no zip, so no ribbon triangles. A boundary whose seam must turn a
                     CORNER does not close and is REFUSED, not shipped. Ceiling 0.15 mm.
  kit coreplace <patch.stl> <body.stl> --box x0 x1 y0 y1 z0 z1 --at x y z [--neighbours "y y ..."]
                     ROUTE A's WELD CORE, BY RULE: every patch point over 0.10 mm off the body is edit;
                     the core is its extent plus 1.5 mm, REFUSED if it reaches another departure or a
                     neighbouring feature. Prints CC_CORE_CEN / CC_CORE_RAD. A refusal is the patch's defect.
  kit seamweld <a.stl> <b.stl> --out <r.stl> [--tol 0.15]
                     THE JOIN, route A: two open meshes welded rim to rim by refinement, no ribbon.
  kit tool [<name> --job <JOB> --set KEY=VALUE ...]
                     the kit's INSTRUMENTS (LEAN_KIT\tools\): loops a weld left, true sections, the field's
                     sign vs ray parity, open edges, gate misses. Output lands in the named job's folder.
  kit stitchband <a.stl> <b.stl> --band x0 x1 y0 y1 z0 z1 [--tol 0.15] [--anyway "<why>"]
                     THE SEAM GATE, for voxel_smooth routes A and C. Two meshes, one thin band, one
                     question: do they agree across it, to 0.15 mm? That is a CEILING - --tol may lower it,
                     nothing raises it, --anyway does not reach it. The band is a SLAB, at most 0.30 mm thick
                     in ONE of x/y/z and any length in the other two; it works on curved geometry and samples
                     the SURFACE, not the vertices. The kit never picks the band - that is your judgement.
  kit review <before.brep> <after.brep> --out <dir> --lead <view,view,...> [--shards 6] [--tag _X]
                     [--box x0,x1,y0,y1,z0,z1] [--dev 0.1] [--plan-only] [--solo] [--mode after|before]
                     [--section auto|none|z64|y-192+]   (a feature on a WALL or under a skin: cut the body at the
                     plane and orbit the remainder; `auto` = drop material under the box for cameras looking up)
                     --lead is REQUIRED: the views you already decided matter for this box (judged first, fail-fast).
                     The box here is comma-separated (one token); every other command takes six space-separated
                     numbers - two spellings, one kit, and both are accepted by --box everywhere (2026-09-24).
                     Then: review --judge <dir> --frame <name> --verdict pass|fail|cannot [--confirms|--clears|--about <frame>]
                     review --sweep <dir> ; review --done <dir>   (COMPLETE is what check/accept/deliverycheck ask for)
                     review --render <dir> [--leads]   (31an) every shard rendered at once and waited for - the one-line parallel form; --leads the lead frames alone, first (31bw)
                     THE PARALLEL ORBIT REVIEW. Runs the one kernel step (tessellate both bodies,
                     ONCE, ALONE) and prints the N shard commands + the review fan-out. ~10 min
                     -> ~3 min at six-up with IDENTICAL coverage: the kernel is ~1 min of it and
                     everything after it is numpy. NOTHING renders or opens fewer frames.
                     DEFAULT is one `cad-reviewer` sub-agent per shard; `--solo` prints the
                     you-open-them-all version. Both are valid; only the reader changes.
  kit ps "<full path to a script>" [args...]
  kit ps --lint "<the line you were about to give the client>"
                     NEVER TYPE A COMMAND FOR the client - generate it. One pastable PowerShell line:
                     starts with `&` (without it PowerShell PRINTS a quoted path instead of
                     running it), names the interpreter in full (the bare word `python` here is
                     the Microsoft Store stub), absolute quoted paths, `;` never `&&`, no
                     placeholders. The whole rule is in CONTRACT.md. `--lint` checks one.
  kit launched <job>                   start this job's wall clock at spawn
  kit watch <name> [--expect <min>] [--what "..."] [--pid <N>]
  kit verdict <step> --artefact <file> --pass|--fail --by <who> --saw "<one line per frame>"
                     record that somebody OPENED THE PICTURES. Gated jobs refuse until this exists,
                     is about the artefact ON DISK, and was written AFTER it. A job never calls it
                     about its own output.
  kit deliver <REV> --template <gui-saved.FCStd> --target <body object> [--model <brep>] [--camera iso|top|...] [--review <dir> | --no-review "<why>"]
                     THE DELIVERY RECIPE: model of record + atlas map objects + the template's assembly, reference
                     and marker objects, visibility and camera set, by zip surgery; then deliverycheck. Refused
                     while the atlas map is behind the bank (kit atlas render) unless --no-atlas "<the client's reason>".
                     --add-body "name|label|path.brep|shown|r,g,b|group[|place=dx,dy,dz,ax,ay,az,deg]" (several) adds Part::Feature bodies into a group
                     (31br B2 - a new project's first bodies, a fixture's parts); a `place=` on a body or a --mesh spec, and the template body's own
                     Placement at a --target swap, are written the way FreeCAD reads them back (31br B5). The atlas map is NOT a body carrier.
  kit place <in.brep|in.stl> --out <out> [--translate dx dy dz] [--rotate "ax ay az deg"] [--about px py pz] [--why "..."] [--bake]
                     a body or mesh MOVED AND TURNED in the project's frame (rotate first, then translate), recorded in claude_code\PLACEMENTS.json -
                     the project's frame map (31br B5); then `kit deliver --add-body` ships it. In a job: t_move's rot_axis / rot_deg / rot_about.
  kit deliverycheck <file.FCStd> (--review <dir> | --no-review "<why>") [--body <Object>] [--expect-colour <Object>=#rrggbb]
                     the three faults that each ship a GREY model, checked in one second. R19 and
                     R20 both shipped grey. See LEAN_KIT\HOW_TO_DELIVER_A_COLOURED_MODEL.md.
  kit collected <name> [--kill]
                     THE WALL CLOCK for work that is NOT a job. Background Bash and Task launches
                     are registered by the PostToolUse hook on their own; this is for anything
                     else whose clock nobody is holding. `collected` when you have its answer or
                     have killed it - L14: a background task you stop reading is not a task you
                     stopped, and `kit close` refuses while one is open.
  kit promote <brep> [--note "..."] [--no-atlas "<why>"]    advance the model of record + a STATE_NOW.md block
  kit close --remaining "<where the design stands / what is left>"
                     (--improvement "..." | --no-improvements "<why none>")
                     (--fact "..."        | --no-facts "<why none>")
                     [--note "..."] [--next "..."]
                     END OF SESSION. Writes SESSION_HANDOFF.md from the registers, appends the
                     improvements to PROCESS_IMPROVEMENTS.md and the facts to PROJECT_FACTS.md (FACTS.md where a project already has one). All
                     three are REQUIRED; two accept "nothing to add" with a reason. Silence is
                     what is refused, because silence and forgetting look identical later.
  kit card <card.md> [--type <edit_type>]     lint a card BEFORE launching a worker
  kit job <name> --type <edit_type> [--card <path>] [--tier haiku]
                     [--expect-vol N] [--expect-faces N]
  kit look <job> --code <pic>=<CODE> --code ... --says "..." --says "..."
                     YOUR reading. The CODES are stamped in each frame and nowhere else
  kit accept <job> --review <dir> [--check <CHECK.json>]     the gate before apply (pre-flight;
                     `kit apply --job <name>` runs the same gate on the path that does the work); --review must be COMPLETE
  kit newjob <name> [--from <brep>] [--first "<why>"]    the job folder + region.brep (a READ-ONLY hard link to the bank);
                     ALWAYS the first step of a job - newcard, card and job follow
  kit failure --what ... --why ... --fix ... --signature ... [--job <name>] [--caught gate|user|self]
  kit status                           session + jobs
  kit state --note "..." [--tags "..."] | --show     STATE_NOW.md: a dated block at the top (what survives a compaction)
  kit clock add|runaway <script.py> <seconds> [--note|--why "..."] | show    WALL_CLOCKS.md: one sample, typical re-taken
  kit ruling --said "<the client's words>" [--about "..."] | --reading "<an agent's reading>" --of "<the client's words>"  the rulings section of PROJECT_FACTS.md, dated, in the client's words
  kit atlas <init|status|defer|set|assign|faces|recreated|import|render|find|extent|recipe|axis|behind ...>   the region atlas (kit atlas --help; defer --until "<words>" | --lift: a new project's atlas comes AFTER its model - 31bv B1);
                     `extent` records the model of record's tight extent (a kernel call) - the mesh route's spike gates read it
  kit mesh <step> --job <J> --tag <T> [--env FILE] [--set K=V ...] [--plan] [--bg] [-- args]
                     THE MESH ROUTE'S RUNNER (route A of voxel_smooth): the scripts are the kit's own (kit\mesh\), the CC_
                     lever census refuses a CARD lever left unset, status files go to the job's work\ per tag, the heavy
                     steps take a machine slot (kit mesh slots), a body-sized STL input is refused (the crop flow).
  kit crop <body.stl> --box x0 x1 y0 y1 z0 z1 [--margin 3] --out <crop.stl>    the route's unit of work: a
                     capped crop of the body round the box (numpy, seconds) + its .crop.json
  kit splice <edited_crop.stl> --crop <crop.json> --out <body2.stl> [--into <body.stl>] | --pieces <list.json>
  kit union <crop.stl> --solid <solid.stl> [--solid ...] --out <out.stl>   a DRAWN closed solid unioned into the crop
                                                       exactly (seconds; the cut curve shared by both meshes), then `kit splice` it
                     the edited crop(s) back into the body in ONE pass: fresh cut checked against the unedited crop,
                     caps dropped, rims matched point for point, joined by identity; outside the boxes the body by index
  kit printfile <mesh.stl|body.brep> --out <file.stl> --rules <shop> [--film 0.35] [--max-mb N]
                     THE FILE THAT GOES TO THE PRINT SHOP: weld, drop bubbles/fragments, open every air film and close
                     the body over it, nmfix, fill every hole, decimate to the shop's limit; <name>_PRINTFILE.md beside it
  kit printcheck <file.stl|body.brep> --rules <shop> [--bores <spec.json>] [--out <dir>] [--step]
                     is it ready for that shop: size, file size, watertight, wall census against the shop's floors with
                     every thin place sectioned and named by region, bores vs spec; PRINTCHECK.md. See PRINT_READINESS.md
  kit frozen <list|add|check ...>       the frozen-region registry (kit frozen --help)
  kit inventory <mesh> --axis a --box ... --measure b     how many of a repeating feature there are, and where
  kit reach <mesh> --box ... --base <before>            census by how far triangles REACH (never by centroid)
  kit pick <frames> ...                 pixels in a review frame -> the triangle ids they show (with LK_OWNERMAP=1)
  kit visible <result.stl> --tool <tool.stl> --frames <dir>   did the tool change what can be SEEN (pixels owned)
"""
import os, sys, json, time, subprocess, shutil, re
for _v in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_MASTER = os.path.dirname(HERE)
ENV = json.load(open(os.path.join(HERE, "env.json")))


def _resolve_project():
    r"""Which PROJECT is this command for? Resolved from the CWD, not from the kit's location.

    THE CHANGE the client ORDERED, 2026-09-14: *"I don't want the kit running on it's own copy of the
    lean kit. Ever. It should be forced to run off of the controls in the lean_kit folder and it
    should not be able to edit anything that controls it's processes."*

    This line used to be `ROOT = os.path.dirname(os.path.dirname(HERE))` — the project was
    wherever the kit file happened to sit, which only works if every project has its OWN COPY of
    the kit. It did, and they had drifted: on 2026-09-14 there were THREE copies of this file
    (the master and two projects' copies), one of them with two modules the other lacked, and the installer's answer had been to back the difference up and report it
    rather than prevent it.

    An earlier kit settled this years of rounds ago and its installer says why in one line:
    *"Copies are forbidden, because a copy is exactly how a part drifted stale and cost a
    session: two versions of the same thing, one of them silently out of date, and nothing to say
    which."*

    So the kit is now ONE copy, in LEAN_KIT, run directly. The project is found the same way
    `guard.py` and `session_start.py` find it — walking up from the working directory to a
    `.claude\` folder — so a script, a gate and a hook can never disagree about which project they
    are in.

    It REFUSES rather than guesses, and it refuses hardest when the answer is the kit itself: a
    session whose ROOT is LEAN_KIT would write its registers into the master and treat the kit
    as its own project, which is precisely the thing being stopped.
    """
    cand = os.environ.get("KIT_PROJECT"); _walked = False
    if cand and os.path.isdir(cand):
        r = os.path.abspath(cand)
    else:
        r = os.path.abspath(os.getcwd()); _walked = True
        while r and not os.path.isdir(os.path.join(r, ".claude")) and os.path.dirname(r) != r:
            r = os.path.dirname(r)
        if not os.path.isdir(os.path.join(r, ".claude")):
            r = os.path.dirname(os.path.dirname(HERE))
    _homes = {os.path.normcase(os.path.abspath(h_)) for h_ in (os.path.expanduser("~"), os.environ.get("USERPROFILE") or "") if h_}
    if os.path.normcase(r) in _homes:
        sys.exit("kit: REFUSED - the project resolved to your HOME folder (%s): its .claude\\ is Claude Code's own, never a project's.\n"
                 "  cd into the project folder first (the one holding claude_code\\ and .claude\\), or set KIT_PROJECT to it; a new project comes from\n"
                 "  the kit's project_template\\ and install_lean_hooks.py --project <its folder> (INSTALL.md)." % r)
    if _walked and os.path.isdir(os.path.join(r, ".claude")) and not os.path.isdir(os.path.join(r, "claude_code")):
        sys.exit("kit: REFUSED - %s holds a .claude\\ but no claude_code\\ - not a kit project; run from inside a project, or set KIT_PROJECT" % r)
    n = os.path.normcase(r)
    low = r.replace("\\", "/").lower().rstrip("/") + "/"
    if n == os.path.normcase(KIT_MASTER) or n.startswith(os.path.normcase(KIT_MASTER) + os.sep) \
            or "/lean_kit/" in low:
        _kit_rule = n == os.path.normcase(KIT_MASTER) or n.startswith(os.path.normcase(KIT_MASTER) + os.sep)
        sys.exit(
            ("kit: REFUSED — the project resolved to the KIT, not a project.\n" if _kit_rule else
             "kit: REFUSED — the project resolved to a folder under LEAN_KIT (the NAME rule: a path holding \\LEAN_KIT\\ is the kit's tree, never a\n"
             "  project - a copy of the kit, a scratch project in a pass folder; reach a scratch project through a path outside LEAN_KIT).\n") +
            "    kit      : %s\n"
            "    resolved : %s\n"
            "  The kit is not a project. It holds no jobs, no bank and no session, and a command\n"
            "  that thinks otherwise would write this session's registers into the master and\n"
            "  treat the controls as its own working files (the client, 2026-09-14).\n"
            "  cd into the project folder first, or set KIT_PROJECT to it." % (KIT_MASTER, r))
    return r


ROOT = _resolve_project()

FORBIDDEN = [
    (r"\bmakeLoft\b|\bmakePipeShell\b|\bBSplineSurface\b|\bapproximate\s*\(|\binterpolate\s*\(", "lofts / fitted surfaces are not allowed (METHOD.md 4)"),
    (r"\bremoveSplitter\b|\bdefeaturing\b|\bfixTolerance\b|\bShapeFix\b", "kernel repair/defeature calls are not allowed"),
    (r"\bMesh\b|\bMeshPart\b", "mesh operations are not allowed in a worker script"),
    (r"\bdistToShape\b|\bsection\s*\(|\bproximity\b", "measuring calls are the orchestrator's; a worker only renders"),
    (r"\.fuse\s*\([^)]*,\s*0\.\d|\.cut\s*\([^)]*,\s*0\.\d", "fuzzy booleans are not allowed"),
]
WORKER_FILLET_OK = "t_edge_round"   # makeFillet

LEVER_PREFIXES = ("CC_", "LK_", "KIT_", "SB_", "FINE_")
SECRET_PAT = re.compile(r"TOKEN|SECRET|PASSW|CREDENTIAL|API_KEY|APIKEY|AUTH|COOKIE|PRIVATE|OAUTH|BEARER", re.I)
ENV_NEVER = ("PATH", "PYTHONPATH", "PYTHONHOME", "LD_LIBRARY_PATH", "HOME", "TEMP", "TMP", "USERPROFILE",
             "SYSTEMROOT", "COMPUTERNAME", "USERNAME", "PROCESSOR_ARCHITECTURE")


def _lever_env(env, folder, seen=()):
    """The subset of `env` that is a LEVER for the scripts in `folder`: read by one of them (by name,
    off the code) or carrying a lever prefix. Secrets are redacted by NAME, never written."""
    read_by_scripts = set()
    try:
        import leangate as _G
        rows, _ = _G.levers(folder, "", None)
        read_by_scripts = {r[0] for r in rows}
    except Exception:
        pass
    out = {}
    for k, v in sorted(env.items()):
        if k in seen or k.startswith("_") or k in ENV_NEVER:
            continue
        if not (k.startswith(LEVER_PREFIXES) or k in read_by_scripts):
            continue
        out[k] = "<redacted>" if SECRET_PAT.search(k) else v
    return out


def scrub_env_files(folder, write=True):
    """One-off: strip every secret-named or non-lever key out of the `_inherited` block of every
    env*.json under `folder` (recursively). Returns (files_seen, files_changed, keys_removed)."""
    seen = changed = removed = 0
    for dp, _dn, fn in os.walk(folder):
        for f in fn:
            if not (f.startswith("env") and f.endswith(".json")):
                continue
            p = os.path.join(dp, f)
            try:
                rec = json.load(open(p, encoding="utf-8"))
            except (OSError, ValueError):
                continue
            seen += 1
            inh = rec.get("_inherited")
            if not isinstance(inh, dict):
                continue
            keep = {}
            for k, v in inh.items():
                if SECRET_PAT.search(k) or not k.startswith(LEVER_PREFIXES):
                    removed += 1; continue
                keep[k] = v
            if keep != inh:
                changed += 1
                if write:
                    rec["_inherited"] = keep
                    tmp = p + ".tmp"
                    with open(tmp, "w", encoding="utf-8") as fh:
                        json.dump(rec, fh, indent=1)
                    os.replace(tmp, p)
    return seen, changed, removed

def freecad():
    import glob as _glob
    if os.environ.get("KIT_FREECAD") and os.path.exists(os.environ["KIT_FREECAD"]):
        return os.environ["KIT_FREECAD"]
    for c in ENV["freecadcmd_candidates"]:
        for hit in (sorted(_glob.glob(c)) if any(ch in c for ch in "*?[") else [c]):
            if os.path.exists(hit): return hit
    sys.exit("kit: no freecadcmd found in env.json candidates: %s" % ENV["freecadcmd_candidates"])

def _emit(line):
    """Print one line of subprocess output without letting the CONSOLE kill a measurement.

    the project CRASH.log, 2026-09-09, three of the session's six kit crashes: `kit measure faces`
    and `kit run` died inside this print with `OSError: [Errno 22] Invalid argument`, and
    `kit facts` died with `UnicodeEncodeError: 'charmap' codec can't encode '\\u2265'` — the
    Windows console/pipe refusing a character or a write, with FreeCAD's answer already in hand.
    A print is never the reason a gate loses its result: fall back to raw UTF-8 bytes, and if the
    stream will not take those either, keep going — the line is still in the log.
    """
    try:
        print(line, end="", flush=True)
    except (OSError, UnicodeEncodeError, ValueError):
        try:
            sys.stdout.buffer.write(line.encode("utf-8", "replace")); sys.stdout.buffer.flush()
        except Exception:
            pass


_FC_BANNER = re.compile(r"^(FreeCAD \d[\w.]*, Libs:|(?:\(c\)|\u00a9|copyright)\s*\d{4}\s*\S\s*\d{4}\s+FreeCAD contributors|"
                        r"FreeCAD is free and open-source software licensed under the terms of LGPL)", re.I)
_FC_PROGRESS = re.compile(r"\(\s*\d{1,3}\s*%\)")


def _fc_noise(line):
    """FreeCAD's three-line banner, a blank line, or a bare progress tick ("Meshing (45%)") - nothing
    else. A percentage beside any other number, or beside a loud word, is a RESULT and is shown."""
    s = line.strip()
    if not s or _FC_BANNER.match(s):
        return True
    if _FC_PROGRESS.search(s):
        rest = _FC_PROGRESS.sub("", s)
        return not re.search(r"\d", rest) and not re.search(r"FAIL|REFUS|ERROR|WARN|Traceback", rest, re.I)
    return False


KILLED_RC = 137


def _win_procs():
    """[(pid, parent pid, command line)] of every process on the machine (Windows, CIM), or [] when it cannot be read"""
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                            "Get-CimInstance Win32_Process | ForEach-Object { '{0}|{1}|{2}' -f $_.ProcessId, $_.ParentProcessId, $_.CommandLine }"],
                           capture_output=True, text=True, timeout=30, creationflags=0x08000000)
        out = []
        for ln in r.stdout.splitlines():
            parts = ln.split("|", 2)
            if len(parts) == 3 and parts[0].strip().isdigit():
                out.append((int(parts[0]), int(parts[1] or 0), parts[2]))
        return out
    except Exception:
        return []


def _alive(pid):
    try:
        if os.name == "nt":
            r = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH", "/FO", "CSV"], capture_output=True, text=True, timeout=15, creationflags=0x08000000)
            return ('"%d"' % pid) in r.stdout
        os.kill(pid, 0); return True
    except Exception:
        return False


def _kill_targets(p, cmd=None, by_name=True):
    """31bs K2a (2026-11-03; the 11-02 review K2a): the pids _kill_tree ends - the step's own tree (the children of p, six levels down) and, ONLY WITH by_name, every other
    process whose command line names the step's script. The sweep is 31an's belt for `kit burrito`'s one FreeCADCmd that outlived its parent; reused by `kit review --render`
    it ended the SIBLING SHARDS (all run job_render_arc.py) and any other review on the machine at the first shard's cap - those shards read rc 1 with their status files
    'running'. sh()'s watchdog keeps the sweep (one script per call); the render passes by_name=False."""
    targets = {p.pid: "the step"}
    script = None
    for a_ in (cmd or []):
        if str(a_).lower().endswith(".py"): script = os.path.basename(str(a_)).lower()
    if os.name == "nt":
        procs = _win_procs()
        kids = {p.pid}
        for _ in range(6):
            new = {pid for pid, ppid, _c in procs if ppid in kids and pid not in kids}
            if not new: break
            kids |= new
        for pid, ppid, c in procs:
            if pid in kids or (by_name and script and script in (c or "").lower() and pid != os.getpid()):
                targets[pid] = (c or "")[:160]
    return targets


def _kill_tree(p, cmd=None, by_name=True):
    """Kill the child AND everything it spawned, AND CONFIRM THEY ARE GONE. `p.kill()` reaches only the direct child: on Windows a
    freecadcmd started by a driver survived its parent's death and fought the next session for the same body (ORCHESTRATOR.md 4b,
    the frozen machine of 2026-09-10; the agent 2026-09-24, 2.14). 31an (a project run of 2026-10-06): `kit burrito` KILLED a step at 360 s
    and its FreeCADCmd kept running - found by tasklist ten minutes later and stopped by hand. So the kill is now checked: the tree
    (and any process whose command line names the step's script) is listed before the kill, killed, then each pid is looked for again,
    killed once more by pid, and a survivor is RETURNED (the caller prints it loudly and writes it into the .KILLED marker).
    Returns the list of (pid, command line) still alive afterwards - empty is the only good answer. 31bs K2a: by_name=False kills the tree alone (the render's shards).
    31bt: by_name is False while a job holds the tree (sh(), the shards) - the job ends every member; the sweep is the belt where Windows refused the job."""
    targets = _kill_targets(p, cmd, by_name)
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=20, creationflags=0x08000000)
        else:
            import signal
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            except Exception:
                p.kill()
    except Exception:
        pass
    try: p.kill()
    except Exception: pass
    try: p.wait(timeout=5)
    except Exception: pass
    left = []
    for pid, what in targets.items():
        if pid == p.pid and p.poll() is not None: continue
        if not _alive(pid): continue
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20, creationflags=0x08000000)
            else:
                os.kill(pid, 9)
        except Exception:
            pass
        time.sleep(0.5)
        if _alive(pid): left.append((pid, what))
    return left


def pin_process(p):
    """Pin a subprocess the kit started to env.json's `affinity_mask` and raise it to `priority` (Windows only).
    A HYBRID CPU CAN PUT BACKGROUND WORK ON ITS SLOW CORES: on a CPU with performance and efficiency cores, a kernel
    step started from FreeCAD has been measured at a third of its speed on the efficiency cores (a 40 s step took over
    six minutes). Pinning it to the performance cores (env.json `affinity_mask`) and above-normal priority puts it back
    at full speed. Skipped when the mask names CPUs the machine does not have, when
    the key is blank, and on every error - never a reason to fail a step."""
    if os.name != "nt":
        return
    try:
        mask = ENV.get("affinity_mask")
        pr = (ENV.get("priority") or "").lower()
        import ctypes
        k32 = ctypes.windll.kernel32
        h = int(p._handle)
        if mask:
            m = int(str(mask), 16) if str(mask).lower().startswith("0x") else int(mask)
            n = os.cpu_count() or 1
            if m and m < (1 << n):
                k32.SetProcessAffinityMask(h, ctypes.c_size_t(m))
        if pr in ("above_normal", "high"):
            k32.SetPriorityClass(h, 0x00008000 if pr == "above_normal" else 0x00000080)
    except Exception:
        pass


def _job_new():
    """31bt (the client's ruling on T6 F7, 2026-11-05): a Windows JOB OBJECT with kill-on-close for a kernel subprocess - the OS ends every process of the step's tree when the job is
    terminated (the watchdog's kill) or when the runner's handle closes (the end of sh(), a runner that dies), re-parented or not: 31an's orphaned FreeCADCmd. While a job holds,
    the by-name sweep of OTHER processes (the 31an belt, which reached another project's run of the same sk_*.py) is not run. None off Windows or on any error (the sweep then
    stands as before). No name tag needed - a job knows its processes by membership, never by name."""
    if os.name != "nt":
        return None
    try:
        import ctypes, ctypes.wintypes as wt
        k32 = ctypes.windll.kernel32
        k32.CreateJobObjectW.restype = ctypes.c_void_p; k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wt.LPCWSTR]
        k32.SetInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, wt.DWORD]
        class _BL(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64), ("LimitFlags", wt.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wt.DWORD), ("Affinity", ctypes.c_size_t), ("PriorityClass", wt.DWORD), ("SchedulingClass", wt.DWORD)]
        class _IO(ctypes.Structure):
            _fields_ = [(n_, ctypes.c_uint64) for n_ in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount", "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]
        class _EL(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", _BL), ("IoInfo", _IO), ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]
        h = k32.CreateJobObjectW(None, None)
        if not h:
            return None
        info = _EL(); info.BasicLimitInformation.LimitFlags = 0x2000
        if not k32.SetInformationJobObject(h, 9, ctypes.byref(info), ctypes.sizeof(info)):
            k32.CloseHandle(h); return None
        return h
    except Exception:
        return None


def _job_assign(h, p):
    """the subprocess p (a Popen) into the job h - True when Windows took it (a process already in a job that forbids nesting is refused: the sweep then stands)"""
    try:
        import ctypes
        k32 = ctypes.windll.kernel32; k32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        return bool(h) and bool(k32.AssignProcessToJobObject(h, ctypes.c_void_p(int(p._handle))))
    except Exception:
        return False


def _job_kill(h):
    """every process of the job, at once"""
    try:
        import ctypes, ctypes.wintypes as wt
        k32 = ctypes.windll.kernel32; k32.TerminateJobObject.argtypes = [ctypes.c_void_p, wt.UINT]
        if h: k32.TerminateJobObject(h, 1)
    except Exception:
        pass


def _job_close(h):
    """the handle closed - kill-on-close ends whatever the step left running"""
    try:
        import ctypes
        k32 = ctypes.windll.kernel32; k32.CloseHandle.argtypes = [ctypes.c_void_p]
        if h: k32.CloseHandle(h)
    except Exception:
        pass


def sh(cmd, timeout, log=None, env=None, cwd=None, outputs=()):
    """Run one kernel subprocess under the cap. Returns (rc, output).

    A KILLED STEP CANNOT READ AS SUCCESS (2026-09-24). A refine killed at its cap returned the wrapper's
    0 and 27 pieces were welded onto a base that was never written (the agent's handoff, 2.2). So a kill now:
    returns KILLED_RC, writes `<log>.KILLED` beside the log (why: budget or silence, how long), and
    renames every declared output that appeared during the run to `<out>.KILLED` so nothing downstream
    can open it as a result. `outputs` are the paths the caller knows the step declares (CC_OUT...).
    Children run unbuffered (PYTHONUNBUFFERED) so a log is never 0 bytes for an hour of work.
    """
    t = time.time(); out = []
    last_line = {"t": t}
    env = dict(env) if env is not None else dict(os.environ)
    env.setdefault("PYTHONUNBUFFERED", "1")
    import threading
    killed = {"v": False, "why": "", "extended": 0}
    hard = float(timeout) * 3.0
    silence_max = min(float(timeout), max(min(float(timeout) / 2.0, 180.0), 10.0))   # over the
    # skin-build  recorded
    busy_path = (str(log) + ".busy") if log else None
    if busy_path:
        env["KIT_BUSY"] = busy_path
        for _bp in (busy_path, busy_path + ".done"):
            try: os.remove(_bp)
            except OSError: pass
    def _busy_now():
        if not busy_path or not os.path.exists(busy_path): return None
        try:
            with open(busy_path, "r", encoding="utf-8") as fh: d = json.load(fh)
            since = float(d.get("since", 0.0)); allow = float(d.get("allow_s", 0.0)); run = time.time() - since
            if since >= t - 1.0 and run < allow: return (str(d.get("what", "a kernel call")), run, allow)
        except Exception: pass
        return None

    def _declared(now=None):
        """31bq R6 (B02 (b)): (seconds of THIS run spent inside declared calls, the end of the latest CLOSED one) - the closed calls
        from the ledger _busy writes (<busy>.done), the open one from the busy file; each capped at its own allowance, overlaps counted
        once. An open call past its allowance moves no silence clock: it is judged on silence as before (the declaration is a bound)"""
        now = now or time.time(); iv = []; end_ = 0.0
        if not busy_path: return 0.0, 0.0
        try:
            with open(busy_path + ".done", "r", encoding="utf-8") as fh:
                for ln_ in fh:
                    try:
                        d_ = json.loads(ln_); s_ = float(d_.get("since") or 0.0); e_ = float(d_.get("end") or s_); a_ = float(d_.get("allow_s") or 0.0)
                    except (ValueError, TypeError, AttributeError): continue
                    if s_ >= t - 1.0 and e_ > s_:
                        iv.append((s_, min(e_, s_ + a_) if a_ > 0 else e_)); end_ = max(end_, iv[-1][1])
        except OSError: pass
        try:
            if os.path.exists(busy_path):
                with open(busy_path, "r", encoding="utf-8") as fh: d_ = json.load(fh)
                s_ = float(d_.get("since") or 0.0); a_ = float(d_.get("allow_s") or 0.0)
                if s_ >= t - 1.0 and now > s_: iv.append((s_, min(now, s_ + a_) if a_ > 0 else now))
        except Exception: pass
        tot_, cur_ = 0.0, None
        for s_, e_ in sorted(iv):
            if cur_ and s_ <= cur_[1]: cur_[1] = max(cur_[1], e_)
            else:
                if cur_: tot_ += cur_[1] - cur_[0]
                cur_ = [s_, e_]
        if cur_: tot_ += cur_[1] - cur_[0]
        return tot_, end_

    def _kill():
        # ON THE CLOCK
        elapsed = time.time() - t; dec_s, dec_end = _declared()
        quiet = time.time() - max(last_line["t"], dec_end)
        undecl = elapsed - dec_s
        b = _busy_now()
        if b is not None:
            what, run, allow = b
            killed["extended"] += 1
            msg = ("\nkit: heartbeat - the step declares itself busy: %s (%.0f s of the %.0f s it allowed itself; silent %.0f s) - "
                   "waiting, not killing.\n" % (what, run, allow, quiet))
            out.append(msg); _emit(msg)
            nxt = threading.Timer(max(10.0, min(60.0, allow - run + 1.0)), _kill); nxt.daemon = True; nxt.start()
            watch["t"] = nxt
            return
        if undecl < hard - 1.0 and quiet < silence_max:
            killed["extended"] += 1; ext_ = min(float(timeout), max(10.0, hard - undecl))
            _pr = ("still printing (last line %.0f s ago)" % quiet) if last_line["t"] > t else ("nothing printed yet - %.0f s quiet, under the silence window of %.0f s" % (quiet, silence_max))
            msg = ("\nkit: at the cap (%d s) but %s - EXTENDED by %d s "
                   "(extension %d); hard ceiling %d s of UNDECLARED time: %.0f s so far, %.0f s inside the step's declared calls not counted. "
                   "Read the log if you doubt it.\n"
                   % (timeout, _pr, ext_, killed["extended"], hard, undecl, dec_s))
            out.append(msg); _emit(msg)
            nxt = threading.Timer(ext_, _kill); nxt.daemon = True; nxt.start()
            watch["t"] = nxt
            return
        killed["v"] = True
        killed["why"] = ("silence - nothing printed for %.0f s%s" % (quiet, " after the step's last declared call ended" if dec_end > last_line["t"] else "")) if quiet >= silence_max else \
                        ("hard ceiling %d s of undeclared time reached while still printing (last line %.0f s ago; %.0f s of the %.0f s inside declared calls, not counted)" % (hard, quiet, dec_s, elapsed))
        if busy_path and os.path.exists(busy_path):
            try:
                with open(busy_path, "r", encoding="utf-8") as fh: d = json.load(fh)
                killed["why"] += "; the step's declared call '%s' ran past its own allowance of %.0f s" % (d.get("what"), float(d.get("allow_s", 0)))
            except Exception: pass
        if job["ok"]: _job_kill(job["h"])
        killed["left"] = _kill_tree(p, cmd, by_name=not job["ok"])
    p = None
    watch = {"t": None}; job = {"h": None, "ok": False}
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             encoding="utf-8", errors="replace", env=env, cwd=cwd,
                             start_new_session=(os.name != "nt"),
                             creationflags=(0x08000000 if os.name == "nt" else 0))
        pin_process(p)
        job["h"] = _job_new(); job["ok"] = bool(job["h"]) and _job_assign(job["h"], p)
        if job["h"] and not job["ok"]: _job_close(job["h"]); job["h"] = None
        watchdog = threading.Timer(float(timeout), _kill); watchdog.daemon = True; watchdog.start()
        watch["t"] = watchdog
        for line in p.stdout:
            # FAIL: 12 samples (5.1 %)
            out.append(line); last_line["t"] = time.time()
            if not _fc_noise(line):
                _emit(line)
        p.wait(timeout=5); rc = p.returncode
        try:
            watch["t"].cancel()
        except Exception:
            pass
    except subprocess.TimeoutExpired:
        if job["ok"]: _job_kill(job["h"])
        killed["left"] = _kill_tree(p, cmd, by_name=not job["ok"]); rc = KILLED_RC; killed["v"] = True; killed["why"] = "no exit after its output closed"
        out.append("kit: killed (no exit)\n")
    if killed["v"]:
        took = time.time() - t
        why = killed["why"] or "the cap"
        rc = KILLED_RC
        msg = "\nkit: KILLED at %d s (cap %d s), cause: %s. rc %d. Its output is NOT a result.\n" % (took, timeout, why, rc)
        out.append(msg); _emit(msg)
        _left = killed.get("left") or []
        if _left:
            msg2 = ("kit: !!! THE KILL DID NOT END EVERYTHING - STILL RUNNING: %s. Stop it before ANY other kernel step (two kernel jobs on one body "
                    "froze the machine, 2026-09-10): %s\n" % ("; ".join("pid %d (%s)" % (a_, w_) for a_, w_ in _left),
                                                          " ; ".join("taskkill /F /PID %d" % a_ for a_, _w in _left)))
            out.append(msg2); _emit(msg2)
        else:
            msg2 = "kit: the killed step's process tree is confirmed gone.\n"
            out.append(msg2); _emit(msg2)
        marker = (log + ".KILLED") if log else None
        try:
            if marker:
                with open(marker, "w", encoding="utf-8") as fh:
                    fh.write("%s  killed at %.0f s (cap %d)  cause: %s\ncmd: %s\nstill running after the kill: %s\n"
                             % (time.strftime("%Y-%m-%d %H:%M:%S"), took, timeout, why, " ".join(map(str, cmd)),
                                ", ".join("pid %d" % a_ for a_, _w in (killed.get("left") or [])) or "none (confirmed)"))
        except OSError:
            pass
        for o in outputs or ():
            try:
                if o and os.path.exists(o) and os.path.getmtime(o) >= t - 1:
                    os.replace(o, o + ".KILLED")
                    out.append("kit: renamed %s -> %s.KILLED (written by a killed step)\n" % (os.path.basename(o), os.path.basename(o)))
                    _emit(out[-1])
            except OSError:
                pass
    if job["h"]: _job_close(job["h"]); job["h"] = None
    if busy_path:
        for _bp in (busy_path, busy_path + ".done"):
            try: os.remove(_bp)
            except OSError: pass
    if log:
        with open(log, "a", encoding="utf-8", errors="replace") as f: f.write("== %s  %s\n%s\n" % (time.strftime("%H:%M:%S"), " ".join(map(str, cmd)), "".join(out)))
    return rc, "".join(out)

def preflight():
    try:
        st = shutil.disk_usage(ENV.get("scratch", "/tmp")); free_gb = st.free / 1e9
        if free_gb < ENV["min_free_gb"]: sys.exit("kit: only %.1f GB free (< %.1f). Delete intermediates first." % (free_gb, ENV["min_free_gb"]))
    except FileNotFoundError: pass

def _body(text):
    """Everything except the PARAMS dict — that is the only part a worker may change. ONE owner:
    `scan()` refuses on it and `kit templates` reports on it, and they must agree."""
    m = re.search(r"^PARAMS\s*=\s*dict\(.*?^\)\s*$", text, re.S | re.M)
    return (text[:m.start()] + text[m.end():]) if m else text


def cmd_levers(args):
    r"""kit levers [<job folder>] [--env <settings.json>] [--prefix LK_] [--unset] [--census | --check]

    Every environment-variable lever the scripts in a folder read, which scripts read it, and its
    hardcoded default - out of the code, so it cannot be stale. `--env` marks the ones a settings file
    actually sets; `--unset` lists only the ones running on a default. Default folder: the newest
    job under claude_code\jobs\; default --env: WINNING_ENV.json in it, if there is one.

    `--census` writes (or merges into) LEVERS_CENSUS.md in the folder: one row per lever with a `class`
    column for the agent to fill - CARD (a number a card decides; must be set every run), CONSTANT (an
    algorithm constant; the code default is the value), DEAD (read only outside the chain). `--check`
    says what is unclassified and which CARD levers the env file does not set. Once classified,
    `kit burrito` refuses a step whose CARD levers are not set for the run (the client, 2026-09-17: defaults
    cannot be passed to an agent; a file that pre-sets variables is an example case, not the process).

    `--scrub-env [--dry]` strips every non-lever and every secret-named key out of the `_inherited`
    block of every env*.json under the folder (recursively). One-off, for env files written before
    2026-09-24, when the record captured the whole session environment (a session token among it).
    """
    jobs = os.path.join(ROOT, "claude_code", "jobs")
    folder = next((a for a in args if not a.startswith("--") and os.path.isdir(a)), None)
    if not folder:
        cands = [os.path.join(jobs, d) for d in os.listdir(jobs)] if os.path.isdir(jobs) else []
        cands = [c for c in cands if os.path.isdir(c)]
        folder = max(cands, key=os.path.getmtime) if cands else jobs
    if "--scrub-env" in args:
        seen, changed, removed = scrub_env_files(folder, write="--dry" not in args)
        print("[levers] env files under %s: %d seen, %d %s, %d non-lever/secret key(s) %s"
              % (folder, seen, changed, "would change" if "--dry" in args else "rewritten",
                 removed, "found" if "--dry" in args else "removed"))
        return 0
    env = _opt(args, "--env")
    if not env and os.path.isfile(os.path.join(folder, "WINNING_ENV.json")):
        env = os.path.join(folder, "WINNING_ENV.json")
    if "--census" in args:
        chain = [scr for _, scr, _ in BURRITO_STEPS] + ["lk_spawn.py", "job_gates.py", "lk_review.py"]
        n, uncls, new = G.census_write(folder, chain, env, _opt(args, "--prefix", "LK_") or "LK_")
        print("[levers] %s: %d lever(s), %d new row(s), %d still to classify (CARD / CONSTANT / DEAD)."
              % (os.path.join(folder, G.LEVERS_CENSUS), n, new, uncls))
        print("[levers] Fill the `class` column, one lever at a time; a `?` is the census proposing, not deciding.")
        print("[levers] When it is done, `kit burrito` refuses a step whose CARD levers are not set for the run.")
        return 0
    if "--check" in args:
        keys = set()
        if env and os.path.isfile(env):
            try:
                keys = set(json.load(open(env, encoding="utf-8")))
            except (OSError, ValueError):
                keys = set()
        uncls, missing, has = G.census_check(folder, keys)
        if not has:
            print("[levers] no %s in %s - run `kit levers --census` first." % (G.LEVERS_CENSUS, os.path.basename(folder)))
            return 2
        c = G.census_read(folder)
        card = sorted(n for n, v in c.items() if v["class"] == "CARD")
        print("[levers] census: %d lever(s); %d classified, %d to classify; %d CARD, %d CONSTANT, %d DEAD"
              % (len(c), len(c) - len(uncls), len(uncls), len(card),
                 sum(1 for v in c.values() if v["class"] == "CONSTANT"), sum(1 for v in c.values() if v["class"] == "DEAD")))
        if uncls:
            print("[levers]   to classify: %s" % ", ".join(uncls[:40]) + (" ..." if len(uncls) > 40 else ""))
        if card:
            print("[levers]   CARD levers %s%s: %s" % ("set by " if env else "", os.path.basename(env) if env else "(no env file)",
                                                       ", ".join(n for n in card if n in keys) or "-"))
            if missing:
                print("[levers]   CARD levers NOT set by it - every run must set these: %s" % ", ".join(missing))
        return 1 if uncls else 0
    return G.levers_report(folder, _opt(args, "--prefix", "LK_") or "LK_", env, "--unset" in args)


def _kernel_near(path, text, top=5):
    """[(score, heading, first body lines)] of the KERNEL_LESSONS.md sections (## K-... and the table rows) that share
    the text's distinctive words."""
    try:
        src = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return []
    words = set(w for w in re.findall(r"[a-z][a-z0-9_]{3,}", text.lower())) - G.STOP_WORDS
    if not words:
        return []
    out = []
    parts = re.split(r"(?m)^(?=## )", src)
    for part in parts:
        lines = [l for l in part.splitlines() if l.strip()]
        if not lines:
            continue
        head = lines[0].lstrip("# ").strip()
        if not head.startswith("K-") and not lines[0].startswith("## "):
            continue
        low = part.lower()
        score = sum(1 for w in words if w in low)
        if head.startswith("K-") and score >= max(2, len(words) // 4):
            out.append((score, head, [l for l in lines[1:] if not l.startswith("|")][:3]))
        elif not head.startswith("K-"):
            for l in lines[1:]:
                if l.startswith("|") and not l.startswith("|---") and not l.startswith("| what"):
                    cells = [c.strip() for c in l.strip("|").split("|")]
                    rl = l.lower()
                    s = sum(1 for w in words if w in rl)
                    if s >= max(2, len(words) // 4) and cells:
                        out.append((s, "%s: %s" % (head[:24], cells[0][:90]), cells[1:4]))
    out.sort(key=lambda r: -r[0])
    return out[:top]


def cmd_lessons(args):
    r"""kit lessons [--near "<the lesson you are about to write, or the operation you are about to run>"] [--all]

    The burrito lessons, indexed out of LEAN_KIT\BURRITO_STEPS.md: every number and title,
    in one list, so a gap or a collision is visible without reading the file (L28-L31 were "missing" for a
    day because two files each numbered their own). `--near` prints the lessons that share a new lesson's
    distinctive words - read those before writing it; L46 contradicted L22 and L26 and its author could not
    see it. A nudge, never a refusal (the client, 2026-09-17).
    """
    master = os.path.join(os.path.dirname(HERE), "BURRITO_STEPS.md")
    kernel = os.path.join(os.path.dirname(HERE), "KERNEL_LESSONS.md")
    near = _opt(args, "--near")
    if near:
        hits = G.lessons_near(master, near)
        khits = _kernel_near(kernel, near)
        if not hits and not khits:
            print("kit lessons: nothing in %s or %s shares this text's words. Write it; give it the next free number (kit lessons)."
                  % (os.path.basename(master), os.path.basename(kernel)))
            return 0
        if hits:
            print("BURRITO LESSONS THAT SHARE THIS TEXT'S WORDS - read them before you write; if the new one CORRECTS one, say so in its title (as L21 does for L3):")
            for score, n, title in hits:
                print("  L%-3d %s" % (n, title[:110]))
        if khits:
            print("KERNEL LESSONS THAT SHARE THIS TEXT'S WORDS (KERNEL_LESSONS.md - the rows for the operation at hand):")
            for score, head, body in khits:
                print("  %s" % head[:118])
                for ln in body[:3]:
                    print("      %s" % ln[:116])
        return 0
    ls = G.lessons(master)
    if not ls:
        print("kit lessons: no lessons found in %s" % master); return 2
    nums = sorted(n for n, _, _ in ls)
    print("THE BURRITO LESSONS - %d, L%d to L%d, all in %s" % (len(nums), nums[0], nums[-1], os.path.basename(master)))
    for n, title, _ in sorted(ls):
        print("  L%-3d %s" % (n, title[:110]))
    gaps = [i for i in range(nums[0], nums[-1] + 1) if i not in nums]
    dups = sorted(set(n for n in nums if nums.count(n) > 1))
    if gaps:
        print("  GAP: L%s never written or lost - say which in the file" % ", L".join(map(str, gaps)))
    if dups:
        print("  COLLISION: L%s used twice - two lessons, one number" % ", L".join(map(str, dups)))
    print("  next free number: L%d" % (nums[-1] + 1))
    return 0


def cmd_paths(args):
    """kit paths [<file.md> ...]

    Every backticked path a document names, resolved; the ones that do not exist are listed. Default:
    the project's CLAUDE.md - the file a session obeys before it can check anything. A report, never a refusal.
    """
    master = os.path.dirname(HERE)
    files = [a for a in args if not a.startswith("--")] or [
        os.path.join(ROOT, "CLAUDE.md")]
    roots = [ROOT, os.path.dirname(master), master, os.path.dirname(ROOT)]
    bad = 0
    for f in files:
        if not os.path.isfile(f):
            print("kit paths: no such file %s" % f); bad += 1; continue
        dead = G.dead_paths(f, roots)
        print("%s: %d path(s) named, %d not found" % (f, len(set(m.group(1) for m in G.PATH_TOKEN.finditer(open(f, encoding='utf-8', errors='replace').read()) if G._path_like(m.group(1)))), len(dead)))
        for tok, tried in dead:
            print("   NOT FOUND  %s" % tok)
        bad += len(dead)
    if bad:
        print("kit paths: a path an entry point names and cannot resolve is the first thing a session obeys. Fix the document or archive the file it names.")
    return 1 if bad else 0



SEAM_CEILING_MM = 0.15
PRINT_TOL_MM = 0.30
SEAM_BAND_MAX_MM = 0.30


def cmd_stitchband(args):
    """kit stitchband <a.stl> <b.stl> --band x0 x1 y0 y1 z0 z1 [--tol 0.15] [--anyway "<why>"]

    THE SEAM GATE. Two meshes, one thin band, one question: do they agree across it, to 0.15 mm?

    It serves both places a seam is made:
      * **ROUTE A** - <welded result> against <the original body>, band on the seam where the rebuilt
        patch meets untouched geometry. Route A re-tessellates its region, so this is the gate that
        says the shape did not MOVE where it was not meant to.
      * **ROUTE C** - <build A> against <build B>, band on the boundary the ORCHESTRATOR chose to
        stitch on. The kit never picks that boundary: a stitch is cheap exactly where the two builds
        already agree, and only a judgement about the part knows where that is.

    **0.15 mm IS A CEILING, NOT A DEFAULT.** `--tol` below it is honoured; `--tol` above it is
    refused, and `--anyway` does not reach it either - an override that can raise a ceiling is not a
    ceiling. The sample-count ratio is REPORTED only: the 3:1 zipper-ratio gate was retired on
    2026-09-22 (it never separated good from bad; the join is `kit seamweld`, which refines). So
    `--anyway` now reaches nothing - it is recorded, and the deviation stays the gate.

    **THE BAND IS A SLAB and it works on ANY geometry.** Give a box that is at most 0.30 mm thick in
    ONE of x, y or z - whichever suits the seam - and as long as you like in the other two. Nothing
    here assumes the surface is flat: a slab meets a curved surface in a curved ribbon and the
    sampling follows it, through fillets, round ribs, across holes. Samples are taken ON the surface
    by clipping triangles to the slab, not from the mesh's vertices, so a coarse patch that puts no
    vertex inside a 0.3 mm band is still measured.
    """
    a = _kv(args)
    pos = a["_"]
    if len(pos) < 2 or "--band" not in args:
        print(cmd_stitchband.__doc__); return 2
    A_path, B_path = pos[0], pos[1]
    for q in (A_path, B_path):
        for part in [r for r in str(q).split("+") if r.strip()]:
            if not os.path.exists(part):
                print("kit stitchband: no such file: %s" % part); return 2
    i = args.index("--band")
    try:
        bx = [float(v) for v in args[i + 1:i + 7]]
        assert len(bx) == 6
    except Exception:
        print("kit stitchband: --band needs six numbers: x0 x1 y0 y1 z0 z1"); return 2
    bx = [min(bx[0], bx[1]), max(bx[0], bx[1]), min(bx[2], bx[3]), max(bx[2], bx[3]),
          min(bx[4], bx[5]), max(bx[4], bx[5])]
    ext = [bx[1] - bx[0], bx[3] - bx[2], bx[5] - bx[4]]
    ax = int(min(range(3), key=lambda k: ext[k]))
    if ext[ax] > SEAM_BAND_MAX_MM + 1e-9:
        print("kit stitchband REFUSED: this band is %.3f x %.3f x %.3f mm - it is not a band, it is a box."
              % tuple(ext))
        print("  A seam band is THIN IN ONE DIRECTION: at most %.2f mm in x, y OR z - whichever suits the"
              % SEAM_BAND_MAX_MM)
        print("  seam - and as long as you like in the other two. Your thinnest direction is %s at %.3f mm."
              % ("xyz"[ax], ext[ax]))
        print("  Measuring a VOLUME instead of a seam averages the agreement over material that is not the")
        print("  join, and a step at the join disappears into it.")
        return 2
    tol = float(a.get("--tol", SEAM_CEILING_MM))
    if tol > SEAM_CEILING_MM + 1e-12:
        print("kit stitchband REFUSED: --tol %.4f is above the %.2f mm ceiling." % (tol, SEAM_CEILING_MM))
        print("  The ceiling can be REDUCED, never raised. the client, 2026-09-21: a seam to other geometry does")
        print("  not ship over %.2f mm, and no flag on this command changes that." % SEAM_CEILING_MM)
        return 2
    sys.path.insert(0, HERE)
    import numpy as np
    import kitlib_render as R
    try:
        VA, TA = R.load_mesh_parts([q for q in A_path.split("+") if q.strip()])
        VB, TB = R.load_mesh_parts([q for q in B_path.split("+") if q.strip()])
    except SystemExit as exc:
        print("kit stitchband: %s" % exc)
        print("  Both inputs must be STL: this compares two BUILDS, and a build of this type is a mesh.")
        return 2
    VA = np.asarray(VA, float); VB = np.asarray(VB, float)
    PA = R.slab_samples(VA, TA, ax, bx[2 * ax], bx[2 * ax + 1], box=bx)
    PB = R.slab_samples(VB, TB, ax, bx[2 * ax], bx[2 * ax + 1], box=bx)
    print("kit stitchband: band is a slab %.3f mm thick in %s, %.1f x %.1f mm across"
          % (ext[ax], "xyz"[ax], *[e for k, e in enumerate(ext) if k != ax]))
    print("  A %-28s %d surface samples in the band" % (os.path.basename(A_path), len(PA)))
    print("  B %-28s %d surface samples in the band" % (os.path.basename(B_path), len(PB)))
    if len(PA) == 0 or len(PB) == 0:
        print("\nkit stitchband REFUSED: one build's surface does NOT enter this band.")
        print("  Samples are taken on the surface, not at its vertices, so this is not a tessellation")
        print("  artefact - the band is simply not on that build's skin. Move it onto surface both")
        print("  builds carry.")
        return 2
    dA = R.point_tri_dist(PA, VB, TB)
    dB = R.point_tri_dist(PB, VA, TA)
    d = np.concatenate([dA, dB])
    worst = float(d.max())
    ratio = max(len(PA), len(PB)) / float(max(1, min(len(PA), len(PB))))
    print("\n  deviation across the band   min %.4f  median %.4f  MAX %.4f mm   (limit %.4f, ceiling %.2f)"
          % (float(d.min()), float(np.median(d)), worst, tol, SEAM_CEILING_MM))
    print("  sample-count ratio          %.1f : 1" % ratio)
    why = a.get("--anyway", "")
    fan = False
    if ratio > 3.0:
        print("  (past 3:1 - a zipper would fan here; the join is kit seamweld, which refines, so this is")
        print("   reported, not gated. Never resample either loop.)")
    if worst > tol:
        print("\nkit stitchband REFUSED: the seam deviates %.4f mm, over the %.4f mm limit." % (worst, tol))
        print("  This is the one refusal --anyway does not reach. A seam to other geometry does not ship")
        print("  over %.2f mm; --tol may lower that, nothing raises it." % SEAM_CEILING_MM)
        print("  Route A: the rebuilt surface has MOVED where it was not meant to - widen the cross-fade")
        print("  or check the patch is not fragmented. Route C: move the band onto quiet surface clear of")
        print("  the edit, where the two builds are the same shape.")
        return 2
    if why:
        print("\n  --anyway is recorded but reaches nothing: the ratio gate it overrode is retired and the")
        print("  deviation cannot be overridden. (%s)" % why)
    print("\nkit stitchband PASS: the seam deviates at most %.4f mm, inside %.4f." % (worst, tol))
    print("  This gate does not judge the stitch. Render it, put the band in the frame, name it in the")
    print("  caption, and judge that frame on its own.")
    return 0



def cmd_stitch(args):
    """kit stitch <a.stl> <b.stl> (--box x0 x1 y0 y1 z0 z1 | --plane z=5.0) --out <r.stl> [--tol 0.15]

    ROUTE C, MADE. One mesh out of two: A's surface INSIDE the boundary, B's outside, joined along it.

    **THE BOUNDARY IS A FIELD, NOT A PLANE.** The splitter takes any continuous scalar function over
    space and finds its zero set by BISECTION, so the boundary can be a plane, a BOX with corners, a
    sphere, a cylinder, or a distance field taken from another surface. Two are wired to flags:

        --box x0 x1 y0 y1 z0 z1     A inside the box, B outside. The natural one: it is the same
                                    vocabulary as every other box in the kit, and it wraps an edit.
        --plane z=5.0               A on the minus side of the named axis value, B on the plus side.
                                    Axis is x, y or z; the value is a model coordinate.

    **What is proven and what is not, measured 2026-09-21.** A SMOOTH boundary of any shape closes the
    seam to zero extra boundary edges and zero non-manifold - plane, sphere, and a box whose seam comes
    out as separate smooth rings were all exact. A boundary with a CREASE THE SEAM MUST TURN - a box
    CORNER, where two seam directions meet - does NOT close, and is REFUSED rather than shipped: the
    command measures the result's open edges against the inputs' own and stops if the seam is open.
    So: wrap an edit with a box whose faces cut clear of each other, or use a plane or a rounded
    boundary, and the corner case will tell you rather than leak.

    **It REFINES, it does not ZIP.** Each side's rim is refined IN THE MESH by the other side's points
    - every added vertex splits an existing rim edge and is shared with the triangle that owned it -
    and the two rims are then welded one-to-one, meeting in the middle. The seam costs NO ribbon
    triangles. A zipper between rims of different point counts fans long thin triangles off every
    vertex of the sparse side, and that fan IS the saw-tooth seam; resampling a loop to fix the ratio
    multiplies open edges, because resampled points coincide with nothing (both measured).

    The 0.15 mm ceiling applies: no rim vertex moves further than `--tol` to meet its partner, `--tol`
    may only be lowered, and a rim pair further apart is a REFUSAL, not a stretch.
    """
    a = _kv(args)
    pos = a["_"]
    has_box = "--box" in args
    has_plane = "--plane" in args
    if len(pos) < 2 or "--out" not in args or has_box == has_plane:
        print(cmd_stitch.__doc__); return 2
    A_path, B_path = pos[0], pos[1]
    for q in (A_path, B_path):
        if not os.path.exists(q):
            print("kit stitch: no such file: %s" % q); return 2
    tol = float(a.get("--tol", SEAM_CEILING_MM))
    if tol > SEAM_CEILING_MM + 1e-12:
        print("kit stitch REFUSED: --tol %.4f is above the %.2f mm ceiling, which may only be reduced."
              % (tol, SEAM_CEILING_MM))
        return 2
    sys.path.insert(0, HERE)
    import numpy as np
    import kitlib_render as R
    if has_box:
        i2 = args.index("--box")
        try:
            bx = [float(v) for v in args[i2 + 1:i2 + 7]]
            assert len(bx) == 6
        except Exception:
            print("kit stitch: --box needs six numbers: x0 x1 y0 y1 z0 z1"); return 2
        bx = [min(bx[0], bx[1]), max(bx[0], bx[1]), min(bx[2], bx[3]), max(bx[2], bx[3]),
              min(bx[4], bx[5]), max(bx[4], bx[5])]
        fn = R.sd_box(bx)
        where = "A inside the named box, B outside it"
    else:
        spec = str(a.get("--plane", "")).strip().lower().replace("=", "")
        if not spec or spec[0] not in "xyz":
            print("kit stitch: --plane is an axis and a value, e.g. --plane z=5.0"); return 2
        try:
            val = float(spec[1:])
        except ValueError:
            print("kit stitch: --plane is an axis and a value, e.g. --plane z=5.0"); return 2
        ax = "xyz".index(spec[0])
        p0 = [0.0, 0.0, 0.0]; p0[ax] = val
        nn = [0.0, 0.0, 0.0]; nn[ax] = 1.0
        fn = R.sd_plane(p0, nn)
        where = "A on the minus-%s side, B on the plus-%s side" % ("xyz"[ax], "xyz"[ax])
    out = a["--out"]
    try:
        VA, TA = R.load_mesh_parts([q for q in A_path.split("+") if q.strip()])
        VB, TB = R.load_mesh_parts([q for q in B_path.split("+") if q.strip()])
    except SystemExit as exc:
        print("kit stitch: %s" % exc); return 2
    if has_box:
        _fh = G.frozen_hits(ROOT, bx)
        if _fh:
            print("kit stitch: the boundary takes in FROZEN region(s): %s - A's surface replaces them here; they are"
                  " put back at the end of edits." % ", ".join(h.get("name", "?") for h in _fh))
    print("kit stitch: %s   (%s / %s)" % (where, os.path.basename(A_path), os.path.basename(B_path)))
    V, T, rep = R.stitch_on_field(VA, TA, VB, TB, fn, tol=tol)
    print("  A kept %d triangles, rim %d edges   B kept %d triangles, rim %d -> %d edges (refined)"
          % (rep.get("triA", 0), rep.get("rimA_edges0", 0), rep.get("triB", 0),
             rep.get("rimB_edges0", 0), rep.get("rimB_edges", rep.get("rimB_edges0", 0))))
    if V is None:
        print("\nkit stitch REFUSED: %s" % rep.get("error", "the stitch could not be made"))
        if "ceiling" in str(rep.get("error", "")):
            print("  `kit stitchband` on the same boundary answers the same question: move it onto")
            print("  quiet surface clear of the edit, where the two builds are the same shape.")
        if "CREASE" in str(rep.get("error", "")) or "paired" in str(rep.get("error", "")):
            print("  This is the KNOWN limit and it is refusing, not leaking: a boundary whose seam has")
            print("  to turn a corner. Use a boundary whose seam comes out smooth - a plane, or a box")
            print("  whose faces cut the surface in separate rings that never meet.")
        return 2
    print("\n  worst rim vertex moved  %.4f mm   (ceiling %.2f, limit %.4f)"
          % (rep["worst_mm"], SEAM_CEILING_MM, tol))
    print("  boundary edges          %d in, %d out - the SEAM contributed %d"
          % (rep["boundary_in"], rep["boundary_out"], rep["seam_open"]))
    print("  non-manifold edges      %d out" % rep["nonmanifold_out"])
    print("  result                  %d triangles, %d vertices" % (rep["tri"], rep["vert"]))
    R.write_stl(out, V, T)
    print("\n  written: %s" % out)
    print("  This is geometry, not a verdict. Review it, with the seam in the frame and named in the")
    print("  caption: `kit review <before> %s --out <dir> --lead ...`" % out)
    return 0



def cmd_frozen(args):
    """kit frozen list | add <name> x0 x1 y0 y1 z0 z1 --why "<the client's words>" | check x0 x1 y0 y1 z0 z1 | drop <name>

    THE FROZEN-REGION REGISTRY. Boxes the client has said are not to be touched, recorded once and enforced.

    the agent, 2026-09-22, on a fill it had built over a flank slot array: *"closed tool, 0 exposed vertices,
    +0 open edges, body bit-identical"* - every gate in the kit passed, and the tool would have put
    material into a DESIGNED vent array. What caught it was painting the tool and asking a reviewer
    whether the openings were construction gaps or apertures, and the reviewer's reasoning was that
    the row is METRONOMIC: *"construction gaps from a voxel process are irregular in width and
    position frame to frame."*

    **No measurement distinguishes a construction gap from a designed aperture.** That is why this is
    a registry and not a detector: the answer is recorded by whoever knows the design, once, and every
    later tool is gated against it rather than judged by eye. A project's frozen list in prose - this
    one has had one for weeks - cannot refuse anything.

    `--why` is required on `add` and should be the client's own words. A region with no reason is a region
    nobody can later argue with.

    `check` is for a LUMP (voxel_smooth V2): a lump inside a frozen region is refused, because it fills a
    designed feature that is recreated at the end of edits anyway. A selection BOX may include a frozen
    region (the client, 2026-09-22) - the template and `kit stitch` say so and carry on.
    """
    a = _kv(args)
    sub = (a["_"][0] if a["_"] else "list").lower()
    regs = G.frozen_load(ROOT)
    if sub == "list":
        if not regs:
            print("kit frozen: NO REGIONS RECORDED for this project.")
            print("  Every gate in the kit measures the tool. None of them knows what the part is FOR.")
            print("  Record the boxes the client has frozen:  kit frozen add <name> x0 x1 y0 y1 z0 z1 --why \"...\"")
            return 0
        print("kit frozen: %d region(s) recorded" % len(regs))
        for r in regs:
            b = r.get("box", [])
            print("  %-22s  %s" % (r.get("name", "?"),
                                   " ".join("%g" % v for v in b) if b else "no box"))
            print("      %s   (recorded %s by %s)" % (r.get("why", "no reason recorded"),
                                                      r.get("when", "?"), r.get("who", "?")))
        return 0
    if sub == "add":
        rest = a["_"][1:]
        if len(rest) < 7:
            print(cmd_frozen.__doc__); return 2
        name = rest[0]
        try:
            box = [float(v) for v in rest[1:7]]
        except ValueError:
            print("kit frozen add: the six box numbers must be numbers"); return 2
        why = _opt(args, "--why", "")
        if not why.strip():
            print("kit frozen add REFUSED: --why is required, in the client's own words where you have them.")
            print("  A frozen region with no reason recorded is one nobody can argue with later, and")
            print("  the first agent who finds it inconvenient will assume it was a guess.")
            return 2
        regs = [r for r in regs if r.get("name") != name]
        regs.append({"name": name, "box": box, "why": why, "when": G._now(),
                     "who": _opt(args, "--who", "orchestrator")})
        G.frozen_save(ROOT, regs)
        print("kit frozen: recorded %r over %s" % (name, " ".join("%g" % v for v in box)))
        print("  Every `kit job`, `kit apply` and `kit stitch` box is now tested against it.")
        return 0
    if sub == "drop":
        rest = a["_"][1:]
        if not rest:
            print(cmd_frozen.__doc__); return 2
        if not _opt(args, "--why", "").strip():
            print("kit frozen drop REFUSED: --why is required. Unfreezing is the client's call, not a tidy-up.")
            return 2
        keep = [r for r in regs if r.get("name") != rest[0]]
        if len(keep) == len(regs):
            print("kit frozen drop: no region named %r" % rest[0]); return 2
        G.frozen_save(ROOT, keep)
        print("kit frozen: dropped %r - %s" % (rest[0], _opt(args, "--why", "")))
        return 0
    if sub == "check":
        rest = a["_"][1:]
        if len(rest) < 6:
            print(cmd_frozen.__doc__); return 2
        box = [float(v) for v in rest[:6]]
        ok, msg = G.frozen_refuse(ROOT, box, "the box given", _opt(args, "--allow-frozen", ""))
        if ok:
            print("kit frozen check: clear%s" % ((" - " + msg) if msg else ""))
            return 0
        print("kit frozen check REFUSED:\n%s" % msg)
        return 2
    print(cmd_frozen.__doc__)
    return 2




def _frame_mmpx(frames):
    """{frame name: mm per pixel} from whatever the review wrote beside its frames."""
    import json as _js
    out = {}
    for f in sorted(os.listdir(frames)):
        if not (f.startswith("status_") and f.endswith(".json")):
            continue
        try:
            d = _js.load(open(os.path.join(frames, f), encoding="utf-8"))
        except Exception:
            continue
        for w in d.get("written", []) or []:
            if w.get("frame") and w.get("mm_per_px"):
                out[w["frame"]] = float(w["mm_per_px"])
    return out


def cmd_visible(args):
    """kit visible <result.stl> --tool <tool.stl> --frames <dir> [--min-px 200] [--anyway "<why>"]

    DID THE TOOL CHANGE WHAT YOU CAN SEE? Counted in PIXELS, in the review's own frames.

    the agent, 2026-09-22, on row I: a clean, gated, symmetric tool - closure, extents, +0 open edges, body
    bit-identical - that came out **~99 pct BURIED, only two tips exposed.** Every gate passed and the
    part did not change. *"A gate suite that cannot tell 'correct' from 'did nothing' is not
    finished."* It was caught by PAINTING the tool and looking.

    **AND THE GEOMETRIC VERSION OF THIS GATE DID NOT WORK.** Three measures were tried on the agent's own
    tools, a no-op against a tool that changed the part:

        new material by volume (the field's own figure) : 35.7 pct vs 37.6 pct
        exposed area by a point-in-body test            : 28.2 pct vs 23.8 pct  - the no-op read HIGHER
        an escaping-normal-ray test                     :  2.2 pct vs  2.9 pct

    None of them separates the case. The reason is that the tool fills an INTERNAL void: its material
    genuinely is not body material, so every geometric test calls it exposed. **The no-op is not
    detectable from the tool and the body alone.** It is a question about what a camera can see, so it
    is answered where the cameras are - the ownermap.

    Render the RESULT with `LK_OWNERMAP=1`, then: this counts the pixels the TOOL's triangles own
    across those frames. A tool that changed nothing owns almost none.
    """
    a = _kv(args)
    pos = a["_"]
    frames = a.get("--frames", "")
    tool = a.get("--tool", "")
    if not pos or not tool or not frames:
        print(cmd_visible.__doc__); return 2
    res = pos[0]
    for q in (res, tool):
        if not os.path.exists(q):
            print("kit visible: no such file: %s" % q); return 2
    if not os.path.isdir(frames):
        print("kit visible: --frames is the review directory holding the frames and their _own.npy")
        return 2
    sys.path.insert(0, HERE)
    import numpy as np
    import kitlib_render as R
    owns = sorted(f for f in os.listdir(frames) if f.endswith("_own.npy"))
    if not owns:
        print("kit visible REFUSED: no `_own.npy` in %s." % frames)
        print("  Re-render with LK_OWNERMAP=1. Without the ownermap a frame cannot say which")
        print("  triangles it drew, and this question has no other honest answer - the geometric")
        print("  versions of it were measured and none of them separates a no-op from a real edit.")
        return 2
    VR, TR = R.load_mesh_parts([q for q in res.split("+") if q.strip()])
    VT, TT = R.load_mesh_parts([q for q in tool.split("+") if q.strip()])
    key = lambda V, T: np.round(np.asarray(V, float)[np.asarray(T, int)].mean(axis=1), 4)
    kt = {tuple(k) for k in key(VT, TT)}
    kr = key(VR, TR)
    mine = np.array([tuple(k) in kt for k in kr], bool)
    print("kit visible: %s painted in %d frame(s) of %s"
          % (os.path.basename(tool), len(owns), os.path.basename(frames.rstrip(os.sep))))
    print("  the tool is %d of the result's %d triangles" % (int(mine.sum()), len(TR)))
    if not mine.any():
        print("\nkit visible REFUSED: none of the tool's triangles is in this result.")
        print("  Either the result is not the placement of this tool, or the placement moved them.")
        return 2
    mm = _frame_mmpx(frames)
    dirs = dict(R.orbit_sweep())
    Pt = np.asarray(VT, float)[np.asarray(TT, int)]
    ntri = np.cross(Pt[:, 1] - Pt[:, 0], Pt[:, 2] - Pt[:, 0])
    atri = 0.5 * np.linalg.norm(ntri, axis=1)
    L = np.linalg.norm(ntri, axis=1); L[L == 0] = 1.0
    ntri = ntri / L[:, None]
    tot_px = 0; own_px = 0; pred_px = 0.0; per = []
    for f in owns:
        nm = f[:-8]
        o = np.load(os.path.join(frames, f))
        drawn = o >= 0
        hit = drawn & mine[np.clip(o, 0, len(mine) - 1)]
        d = dirs.get(nm)
        mmpx = mm.get(nm)
        pr = float("nan")
        if d is not None and mmpx:
            face = (ntri @ np.asarray(d, float)) < 0.0
            pr = float((atri[face] * np.abs(ntri[face] @ np.asarray(d, float))).sum() / (mmpx * mmpx))
            pred_px += pr
        per.append((nm, int(hit.sum()), int(drawn.sum()), pr))
        own_px += int(hit.sum()); tot_px += int(drawn.sum())
    for nm, h, dpx, pr in sorted(per, key=lambda r: -r[1])[:8]:
        print("    %-18s %8d px owned   predicted %10s   (%d px drawn)"
              % (nm, h, ("%.0f" % pr) if pr == pr else "unknown", dpx))
    print("\n  TOTAL %d pixel(s) owned across %d frame(s)" % (own_px, len(owns)))
    if pred_px > 0:
        print("  PREDICTED %.0f px if nothing hid it   ->   visible fraction %.4f"
              % (pred_px, own_px / pred_px))
    else:
        print("  PREDICTED: unknown - no mm/px recorded for these frames, so only the raw count is")
        print("  available. Re-render through `kit review`, which writes it, to get the fraction.")
    why = a.get("--anyway", "")
    if pred_px > 0 and pred_px < 1.0:
        print("\nkit visible REFUSED: these frames predict %.2f px of the tool - they do not LOOK at it."
              % pred_px)
        print("  That is a LEAD SET fault, not a verdict on the build. Re-aim the cameras and re-run.")
        return 2
    thr = float(a.get("--min-ratio", 0.0)) * pred_px if pred_px > 0 else float(a.get("--min-px", 1))
    if own_px <= thr:
        print("\nkit visible %s: the tool owns %d pixel(s) where %s were predicted."
              % ("OVERRIDDEN" if why else "REFUSED", own_px,
                 ("%.0f" % pred_px) if pred_px > 0 else "some"))
        print("  This is the SILENT NO-OP. Every other gate passes it - it is closed, it is inside its")
        print("  box, it adds no open edges and the body stays bit-identical - because almost nothing")
        print("  happened where anyone can see. Usual cause: the concavity the field found is INTERNAL,")
        print("  so the feature you meant to fix is not a concave void and this type does not treat it.")
        print("  If the frames simply do not look at it, that is a LEAD SET fault - re-aim and re-run.")
        if not why:
            print('  --anyway "<reason>" records the override; a deliberate internal fill is a real case.')
            return 2
        print("  OVERRIDE RECORDED: %s" % why)
    else:
        print("\nkit visible PASS: the tool is visible in the frames the review is judged on%s."
              % ((", %.1f pct of what these cameras could show" % (100.0 * own_px / pred_px))
                 if pred_px > 0 else ""))
    print("  The count says HOW MUCH is visible, never whether it is RIGHT. Open the frames.")
    return 0


def _inside_count(P, V, T):
    """Ray crossings from each point of P through the mesh (V, T). Even = outside, odd = inside.

    NOT WHAT `kit visible` USES ANY MORE, and the reason is worth keeping with the code. An
    inside/outside test cannot detect a tool that fills an INTERNAL void: the material is genuinely
    not body material, so the test correctly calls it outside, and a silent no-op reads as exposed.
    Measured on two real tools, a no-op against one that changed the part: 28.2 pct against 23.8 pct,
    the no-op HIGHER. The primitive is correct and tested; the question it was asked was the wrong one.

    THE RAY IS TILTED ON PURPOSE. Along an axis it lands exactly on the shared diagonal of any
    axis-aligned quad, gets counted once in each of the two triangles, and reports an interior point
    as OUTSIDE - on a part built from boxes that is not an edge case, it is the common case. The
    origin inside a plain cube read 2 crossings. A tilt small enough to keep the broadphase cheap and
    large enough to miss every shared edge fixes it; the broadphase is widened by the tilt's own
    drift across the model so it stays conservative.
    """
    import numpy as np
    P = np.asarray(P, float); V = np.asarray(V, float); T = np.asarray(T, int)
    if len(T) == 0 or len(P) == 0:
        return np.zeros(len(P), int)
    dirv = np.array([1.0, 0.0037151, 0.0091733])
    dirv = dirv / np.linalg.norm(dirv)
    span = float(V[:, 0].max() - V[:, 0].min()) + 1.0
    drift = span * (abs(dirv[1]) + abs(dirv[2])) + 1e-6
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    lo = np.minimum(np.minimum(A, B), C); hi = np.maximum(np.maximum(A, B), C)
    e1 = B - A; e2 = C - A
    pv = np.cross(dirv, e2)
    det = (e1 * pv).sum(1)
    live = np.abs(det) > 1e-12
    inv = np.zeros(len(det)); inv[live] = 1.0 / det[live]
    out = np.zeros(len(P), int)
    for i, p in enumerate(P):
        m = (live & (hi[:, 0] >= p[0])
             & (hi[:, 1] >= p[1] - drift) & (lo[:, 1] <= p[1] + drift)
             & (hi[:, 2] >= p[2] - drift) & (lo[:, 2] <= p[2] + drift))
        if not m.any():
            continue
        tv = p - A[m]
        u = (tv * pv[m]).sum(1) * inv[m]
        ok = (u >= 0) & (u <= 1)
        if not ok.any():
            continue
        qv = np.cross(tv, e1[m])
        v = (dirv * qv).sum(1) * inv[m]
        ok &= (v >= 0) & (u + v <= 1)
        if not ok.any():
            continue
        t = (e2[m] * qv).sum(1) * inv[m]
        out[i] = int(((t > 1e-9) & ok).sum())
    return out


def cmd_reach(args):
    """kit reach <mesh.stl> --box x0 x1 y0 y1 z0 z1 [--base <control.stl>] [--min-reach 5.0] [--out <npz>]

    TRIANGLES THAT REACH OUT OF A REGION. The selector a census has to use, and the one it usually does not.

    the agent, 2026-09-22: *"THE BUG IN EVERY CENSUS I WROTE THIS SESSION: they select triangles whose CENTROID
    is in the box. A triangle that spans out of the region has its centroid OUTSIDE it - that is what
    spanning means - so the one defect the client can see was excluded from every count I ever showed them."*
    The blade the client circled was a single triangle with a 151.8 mm edge whose centroid sat 60 mm outside the
    junction box, and it never appeared in a 2,966-triangle census at any threshold, because of one word
    in a mask.

    So: select on ANY VERTEX in the box, and rank by how far the triangle REACHES beyond it.

    **Give it a `--base` control, and take the control from the SAME DOCUMENT as the subject.** A part
    has long context triangles of its own and the number is meaningless without them; a FOREIGN base
    (sharing 42.8 pct of its vertices, in the case that taught this) gave a mushy worst-reach of
    11.32 mm where the document's own before-mesh gave 6.77 mm and made the answer unambiguous.
    """
    a = _kv(args)
    pos = a["_"]
    if not pos or "--box" not in args:
        print(cmd_reach.__doc__); return 2
    mesh = pos[0]
    if not os.path.exists(mesh):
        print("kit reach: no such file: %s" % mesh); return 2
    i = args.index("--box")
    try:
        bx = [float(v) for v in args[i + 1:i + 7]]
        assert len(bx) == 6
    except Exception:
        print("kit reach: --box needs six numbers: x0 x1 y0 y1 z0 z1"); return 2
    bx = [min(bx[0], bx[1]), max(bx[0], bx[1]), min(bx[2], bx[3]), max(bx[2], bx[3]),
          min(bx[4], bx[5]), max(bx[4], bx[5])]
    sys.path.insert(0, HERE)
    import numpy as np
    import kitlib_render as R

    def _reach(path):
        V, T = R.load_mesh_parts([q for q in path.split("+") if q.strip()])
        V = np.asarray(V, float); T = np.asarray(T, int)
        lo = np.array(bx[0::2]); hi = np.array(bx[1::2])
        P = V[T]
        inbox = np.all((P >= lo) & (P <= hi), axis=2)
        sel = inbox.any(axis=1)
        if not sel.any():
            return T[:0], np.zeros(0), np.zeros(0)
        Q = P[sel]
        out = np.maximum(lo - Q, 0.0) + np.maximum(Q - hi, 0.0)
        reach = np.linalg.norm(out, axis=2).max(axis=1)
        edge = np.linalg.norm(Q[:, [1, 2, 0]] - Q, axis=2).max(axis=1)
        return np.nonzero(sel)[0], reach, edge

    idx, reach, edge = _reach(mesh)
    print("kit reach: %s" % os.path.basename(mesh))
    print("  triangles with ANY VERTEX in the box: %d" % len(idx))
    if len(idx) == 0:
        print("  nothing selected - the box does not touch this mesh.")
        return 2
    print("  reach beyond the box   median %.3f  p99 %.2f  MAX %.2f mm" %
          (float(np.median(reach)), float(np.percentile(reach, 99)), float(reach.max())))
    print("  longest edge           median %.3f  p99 %.2f  MAX %.2f mm" %
          (float(np.median(edge)), float(np.percentile(edge, 99)), float(edge.max())))
    base = a.get("--base", "")
    if base and os.path.exists(base):
        bidx, breach, bedge = _reach(base)
        print("  CONTROL %s: %d triangles, reach MAX %.2f mm, longest edge MAX %.2f mm"
              % (os.path.basename(base), len(bidx),
                 float(breach.max()) if len(bidx) else 0.0, float(bedge.max()) if len(bidx) else 0.0))
        print("  DELTA                  reach %+.2f mm, longest edge %+.2f mm"
              % (float(reach.max()) - (float(breach.max()) if len(bidx) else 0.0),
                 float(edge.max()) - (float(bedge.max()) if len(bidx) else 0.0)))
    elif base:
        print("  CONTROL %s: NOT FOUND - reported without one, which makes the numbers hard to read."
              % base)
    else:
        print("  NO CONTROL GIVEN. A part has long context triangles of its own; without a control from")
        print("  the SAME document these numbers say little. --base <the before-mesh of this document>.")
    mr = float(a.get("--min-reach", 5.0))
    bad = np.nonzero(reach >= mr)[0]
    print("\n  reaching %g mm or more: %d triangle(s)" % (mr, len(bad)))
    for k in bad[np.argsort(-reach[bad])][:10]:
        print("     triangle %-8d reach %8.2f mm   longest edge %8.2f mm" % (idx[k], reach[k], edge[k]))
    out = a.get("--out", "")
    if out:
        np.savez_compressed(out, fin=idx[bad], reach=reach[bad], edge=edge[bad], box=np.array(bx))
        print("  written: %s  (feed it to a paint step as the highlight set)" % out)
    return 2 if len(bad) else 0



def cmd_pick(args):
    """kit pick <mesh.stl> --own <frame_own.npy> (--rect x0 y0 x1 y1 | --seg x0 y0 x1 y1 halfwidth) [--out <npz>]

    TURN PIXELS INTO TRIANGLE IDS. The other half of the ownermap, and the end of inferring a subject.

    the agent, 2026-09-22: *"Until now the next step was always 'guess which triangles those are and go measure
    something', and that guess is the single root cause of every mis-attribution this session: the
    zipper fan, the decimation, the displaced vertices. All three were me inferring the subject of a
    picture instead of reading it."*

    So name the defect by PIXELS - a rectangle round it, or a stroke down it - and get the exact
    triangles back, with their area, longest edge and aspect ratio. Then measure THOSE. Render with
    `LK_OWNERMAP=1` to get the `_own.npy` beside each frame.
    """
    a = _kv(args)
    pos = a["_"]
    own_p = a.get("--own", "")
    if not pos or not own_p:
        print(cmd_pick.__doc__); return 2
    for q in (pos[0], own_p):
        if not os.path.exists(q):
            print("kit pick: no such file: %s" % q); return 2
    sys.path.insert(0, HERE)
    import numpy as np
    import kitlib_render as R
    own = np.load(own_p)
    V, T = R.load_mesh_parts([q for q in pos[0].split("+") if q.strip()])
    V = np.asarray(V, float); T = np.asarray(T, int)
    H, W = own.shape
    yy, xx = np.mgrid[0:H, 0:W]
    if "--rect" in args:
        i = args.index("--rect")
        x0, y0, x1, y1 = [float(v) for v in args[i + 1:i + 5]]
        m = (xx >= min(x0, x1)) & (xx <= max(x0, x1)) & (yy >= min(y0, y1)) & (yy <= max(y0, y1))
        what = "rect"
    elif "--seg" in args:
        i = args.index("--seg")
        x0, y0, x1, y1, hw = [float(v) for v in args[i + 1:i + 6]]
        dx, dy = x1 - x0, y1 - y0
        L2 = max(dx * dx + dy * dy, 1e-9)
        t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / L2, 0.0, 1.0)
        m = ((xx - (x0 + t * dx)) ** 2 + (yy - (y0 + t * dy)) ** 2) <= hw * hw
        what = "stroke"
    else:
        print(cmd_pick.__doc__); return 2
    ids = np.unique(own[m & (own >= 0)])
    print("kit pick: %s over %d pixel(s) -> %d triangle(s)" % (what, int(m.sum()), len(ids)))
    if len(ids) == 0:
        print("  nothing there. The %s covers background only - check it against the frame." % what)
        return 2
    P = V[T[ids]]
    area = 0.5 * np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1)
    edge = np.linalg.norm(P[:, [1, 2, 0]] - P, axis=2).max(axis=1)
    ar = np.where(area > 1e-12, edge ** 2 / (4.0 * np.sqrt(3.0) * np.maximum(area, 1e-12)), np.inf)
    print("  area        median %.4f  MIN %.6f mm2" % (float(np.median(area)), float(area.min())))
    print("  longest edge median %.3f  MAX %.2f mm" % (float(np.median(edge)), float(edge.max())))
    fin = np.isfinite(ar)
    print("  aspect ratio median %.2f  worst %s  (1 = equilateral)"
          % (float(np.median(ar[fin])) if fin.any() else float("nan"),
             ("%.0f" % ar[fin].max()) if fin.any() else "degenerate"))
    order = np.argsort(-edge)[:8]
    for k in order:
        print("     triangle %-8d edge %8.2f mm   area %10.5f mm2   aspect %s"
              % (ids[k], edge[k], area[k], ("%.0f" % ar[k]) if np.isfinite(ar[k]) else "inf"))
    out = a.get("--out", "")
    if out:
        np.savez_compressed(out, fin=ids, area=area, edge=edge)
        print("  written: %s  (this is the highlight set - paint it and look again)" % out)
    return 0



def cmd_inventory(args):
    """kit inventory <mesh.stl> --axis x|y|z --box x0 x1 y0 y1 z0 z1 --measure x|y|z [--step 0.5] [--min-pitch 5]

    HOW MANY OF THEM ARE THERE, AND WHERE? Enumerate a repeating feature before a round is planned.

    the agent, 2026-09-22: *"There was no way to answer 'how many junctions are there and where?' ... every
    project so far has had an orchestrator guess the count off a render instead."* On this part the
    guess had survived two sessions and was wrong in a way that mattered: what the record called
    "junctions 1 and 2" were the LEFT AND RIGHT SIDES OF ONE vane. The previous round had edited one
    vane, not two, and three remained rather than "some".

    **And the obvious measure is the wrong one.** A triangle-count histogram finds the EDIT, not the
    geometry - `voxel_smooth` leaves far more triangles where it touched, so a density scan returned
    ONE feature: the one already done, with the other three hidden completely. The density-independent
    measure is how far material REACHES along `--measure` at each station along `--axis`. That found
    four vanes at a clean pitch in one run.
    """
    a = _kv(args)
    pos = a["_"]
    if not pos or "--box" not in args or not a.get("--axis") or not a.get("--measure"):
        print(cmd_inventory.__doc__); return 2
    if not os.path.exists(pos[0]):
        print("kit inventory: no such file: %s" % pos[0]); return 2
    ax = "xyz".find(str(a.get("--axis", "")).strip().lower()[:1])
    mx = "xyz".find(str(a.get("--measure", "")).strip().lower()[:1])
    if ax < 0 or mx < 0 or ax == mx:
        print("kit inventory: --axis and --measure are each x, y or z, and they differ."); return 2
    i = args.index("--box")
    try:
        bx = [float(v) for v in args[i + 1:i + 7]]
        assert len(bx) == 6
    except Exception:
        print("kit inventory: --box needs six numbers: x0 x1 y0 y1 z0 z1"); return 2
    sys.path.insert(0, HERE)
    import numpy as np
    import kitlib_render as R
    V, T = R.load_mesh_parts([q for q in pos[0].split("+") if q.strip()])
    V = np.asarray(V, float)
    lo = np.array(bx[0::2]); hi = np.array(bx[1::2])
    m = np.all((V >= lo) & (V <= hi), axis=1)
    P = V[m]
    if len(P) < 8:
        print("kit inventory: only %d vertices in that box - nothing to enumerate." % len(P)); return 2
    step = float(a.get("--step", 0.5))
    a0, a1 = bx[2 * ax], bx[2 * ax + 1]
    nb = max(4, int(round((a1 - a0) / step)))
    edges = np.linspace(a0, a1, nb + 1)
    which = np.clip(np.searchsorted(edges, P[:, ax]) - 1, 0, nb - 1)
    prof = np.full(nb, np.nan)
    for k in range(nb):
        q = P[which == k]
        if len(q):
            prof[k] = float(q[:, mx].min())
    good = np.isfinite(prof)
    if good.sum() < 4:
        print("kit inventory: the box is too sparse along %s to profile." % "xyz"[ax]); return 2
    centres = 0.5 * (edges[:-1] + edges[1:])
    v = np.where(good, prof, np.nanmax(prof[good]))
    minp = float(a.get("--min-pitch", 5.0))
    span = max(1, int(round(minp / step / 2)))
    peaks = []
    for k in range(span, nb - span):
        w = v[k - span:k + span + 1]
        if v[k] <= w.min() + 1e-9 and (v[k] < np.nanmedian(v) - 1e-9):
            if not peaks or centres[k] - centres[peaks[-1]] >= minp:
                peaks.append(k)
            elif v[k] < v[peaks[-1]]:
                peaks[-1] = k
    print("kit inventory: %s over %s, reach measured along %s"
          % (os.path.basename(pos[0]), "xyz"[ax], "xyz"[mx]))
    print("  %d vertices in the box, profiled in %d stations of %g mm" % (len(P), nb, step))
    if not peaks:
        print("  NO REPEATING FEATURE FOUND. Either the box holds one feature or none, or the reach")
        print("  profile is flat along this axis - try --measure on a different axis.")
        return 0
    cs = [float(centres[k]) for k in peaks]
    print("  %d feature(s) at %s = %s" % (len(cs), "xyz"[ax], ", ".join("%.1f" % c for c in cs)))
    if len(cs) > 1:
        gaps = [b - a2 for a2, b in zip(cs, cs[1:])]
        mg = sum(gaps) / len(gaps)
        print("  pitch: %s   mean %.2f mm, worst deviation %.2f mm"
              % (", ".join("%.2f" % g for g in gaps), mg, max(abs(g - mg) for g in gaps)))
        if max(abs(g - mg) for g in gaps) <= 0.15 * mg:
            print("  REGULAR. A constant pitch is a designed array as often as it is a repeated defect -")
            print("  check it against `kit frozen list` before carding any of them.")
    return 0



def cmd_coreplace(args):
    """kit coreplace <patch.stl> <body.stl> --box x0 x1 y0 y1 z0 z1 --at x y z [--neighbours "c c ..."]
                     [--axis y] [--tol 0.10] [--margin 1.5] [--link 1.2] [--max-pts 25000] [--out core.json]

    PLACE A WELD CORE BY A RULE, NOT BY COPYING A NUMBER THAT ONCE WORKED. the agent's diagnosis, 2026-09-22
    (the project jobs\\DIAG_V2V3\\FINDINGS.md, test 4): the core must ENCLOSE the whole edit and put its wall only
    on surface the edit did not touch - `kit seamweld` refused the accepted V2 seam because the edit reached
    the core wall, and its refusal names this rule. So:
      * every patch point more than --tol off the body is EDIT; points are grouped by connectivity (--link);
      * the edit to enclose is the group(s) holding --at (or the nearest one); the core is its extent plus
        --margin, as an axis-aligned ellipsoid;
      * the core is REFUSED if it would reach ANOTHER departure group, or a neighbouring feature station
        (`kit inventory`'s list, along --axis) - a wall there cannot sit on untouched surface.
    Without being told V2's numbers it placed a clean core on V2; on V3 and V4 it refused, correctly, because
    of the lumps the extract's sign error built (fixed in `_ccextract` the same day).
    --box IS THE EXTRACT BOX. The patch closes itself with caps in the air margin outside it, and a wider box
    reads those caps as departures (measured on V2: 5 groups in a box 2 mm wider, 2 in the extract box - and
    the 2 reproduce the diagnosis' core, radii 15.3 / 9.7 / 8.5).
    Prints the CC_CORE_CEN / CC_CORE_RAD lines for the weld. Exit 2 when refused."""
    import numpy as np
    a = _kv(args)
    pos = [t for t in a["_"] if not _isnum(t)]
    if len(pos) < 2 or "--box" not in args or "--at" not in args:
        print(cmd_coreplace.__doc__); return 2
    try:
        i = args.index("--box"); box = [float(v) for v in args[i + 1:i + 7]]
        i = args.index("--at"); at = np.array([float(v) for v in args[i + 1:i + 4]])
        assert len(box) == 6 and len(at) == 3
    except Exception:
        print("kit coreplace: --box needs six numbers and --at three"); return 2
    import kitlib_render as R
    tol = float(a.get("--tol", 0.10)); marg = float(a.get("--margin", 1.5))
    link = float(a.get("--link", 1.2)); maxp = int(a.get("--max-pts", 25000))
    ax = "xyz".find((a.get("--axis", "y") or "y")[:1])
    nbs = [float(v) for v in (a.get("--neighbours", "") or "").replace(",", " ").split()]
    PV, PT = R.read_stl(pos[0]); BV, BT = R.read_stl(pos[1])
    PV = np.asarray(PV, float); BV = np.asarray(BV, float); BT = np.asarray(BT, int)
    lo_b = BV[BT].min(1); hi_b = BV[BT].max(1)
    near = ((hi_b[:, 0] >= box[0] - 3) & (lo_b[:, 0] <= box[1] + 3) & (hi_b[:, 1] >= box[2] - 3)
            & (lo_b[:, 1] <= box[3] + 3) & (hi_b[:, 2] >= box[4] - 3) & (lo_b[:, 2] <= box[5] + 3))
    BT = BT[near]
    inner = ((PV[:, 0] > box[0] + 0.5) & (PV[:, 0] < box[1] - 0.5) & (PV[:, 1] > box[2] + 0.5)
             & (PV[:, 1] < box[3] - 0.5) & (PV[:, 2] > box[4] + 0.5) & (PV[:, 2] < box[5] - 0.5))
    P = PV[inner]
    if len(P) > maxp:
        P = P[np.linspace(0, len(P) - 1, maxp).astype(int)]
    if not len(P) or not len(BT):
        print("kit coreplace: no patch points or no body surface inside the box"); return 2
    d = R.point_tri_dist(P, BV, BT)
    off = d > tol
    Q, dq = P[off], d[off]
    print("patch points examined %d; off the body by more than %.2f mm: %d (%.1f pct)"
          % (len(P), tol, int(off.sum()), 100.0 * off.mean()))
    if not len(Q):
        print("the patch reproduces the body everywhere in the box - there is no edit to enclose"); return 2
    lab = R.cluster_points(Q, link)
    groups = []
    for k in np.unique(lab):
        m = lab == k
        if m.sum() < 5:
            continue
        groups.append({"pts": int(m.sum()), "min": Q[m].min(0), "max": Q[m].max(0),
                       "off": float(dq[m].max()), "mask": m})
    groups.sort(key=lambda g: -g["pts"])
    print("%d departure group(s):" % len(groups))
    for i, g in enumerate(groups):
        print("   %d: %5d pts, off up to %5.2f mm, %.1f x %.1f x %.1f mm"
              % (i, g["pts"], g["off"], *(g["max"] - g["min"])))
    hold = [g for g in groups if np.all(at >= g["min"] - 2.0) and np.all(at <= g["max"] + 2.0)]
    if not hold:
        hold = [min(groups, key=lambda g: float(np.linalg.norm(Q[g["mask"]] - at, axis=1).min()))]
    lo = np.min([g["min"] for g in hold], 0); hi = np.max([g["max"] for g in hold], 0)
    cen = (lo + hi) / 2.0; rad = np.maximum((hi - lo) / 2.0 + marg, 1.0)
    clash = []
    for i, g in enumerate(groups):
        if any(g is h for h in hold):
            continue
        if ((((Q[g["mask"]] - cen) / rad) ** 2).sum(1) <= 1.0).any():
            clash.append("departure group %d (%d pts, off up to %.1f mm) reaches inside the core" % (i, g["pts"], g["off"]))
    for c in nbs:
        if abs(c - cen[ax]) < rad[ax]:
            clash.append("the neighbouring feature at %s %.1f lies inside the core" % ("xyz"[ax], c))
    print("RULE CORE: edit extent plus %.1f mm margin" % marg)
    print("  CC_CORE_CEN=%.2f %.2f %.2f" % tuple(cen))
    print("  CC_CORE_RAD=%.2f %.2f %.2f" % tuple(rad))
    rec = {"core_cen": [round(float(v), 3) for v in cen], "core_rad": [round(float(v), 3) for v in rad],
           "clash": clash, "groups": [{"pts": g["pts"], "off_mm": round(g["off"], 3),
                                       "min": [round(float(v), 2) for v in g["min"]],
                                       "max": [round(float(v), 2) for v in g["max"]]} for g in groups]}
    if a.get("--out"):
        import json as _js
        _js.dump(rec, open(a["--out"], "w"), indent=1)
    if clash:
        print("REFUSED: the rule cannot place a clean core -")
        for c in clash:
            print("   * " + c)
        print("  A core wall there would cut material the body does not have, or another edit, and the cut is a")
        print("  loop with nothing to join. Fix the patch (a departure away from the edit is an extract defect),")
        print("  or split the edit - do not hand-pick a core round it.")
        return 2
    print("the core encloses the whole edit and reaches nothing else")
    return 0


def cmd_seamweld(args):
    """kit seamweld <a.stl> <b.stl> --out <result.stl> [--tol 0.15]

    ROUTE A'S MISSING LEVER. Join two ALREADY-OPEN meshes along their rims, by refinement and
    identity. No zipper, so no ribbon and no fan.

    Route A's gate 2 says *"keep the two loops' point counts within about 3:1 or the zip will fan"* -
    and nothing in the weld could change a point count. The decimator runs with
    `BoundaryVertexDeletionOff` and the smoother with `BoundarySmoothingOff`, both on purpose, so the
    rim survives untouched; the only lever that moved a count was a RESAMPLE, which multiplies open
    edges by an order of magnitude because the seam vertices are not free to move. **A gate whose only
    lever is forbidden by the next gate is a report wearing a gate's clothes** (CONTRACT rule 0). This
    is the lever.

    Each side's rim is refined IN THE MESH by the other side's points - every added vertex splits an
    existing rim edge and is shared with the triangle that owned it - and the rims are then welded
    one-to-one. Measured across rims of 192 and 24 edges, an 8:1 fan case: the sparse rim refined to
    192 and the seam contributed 0 boundary and 0 non-manifold edges.

    `a` is the body with the hole in it, `b` is the patch that goes in the hole - or the other way
    round; it does not matter. Loops are matched to LOOPS, and a loop with no partner REFUSES rather
    than leaving the seam open there.
    """
    a = _kv(args)
    pos = a["_"]
    if len(pos) < 2 or "--out" not in args:
        print(cmd_seamweld.__doc__); return 2
    for q in pos[:2]:
        if not os.path.exists(q):
            print("kit seamweld: no such file: %s" % q); return 2
    tol = float(a.get("--tol", SEAM_CEILING_MM))
    if tol > SEAM_CEILING_MM + 1e-12:
        print("kit seamweld REFUSED: --tol %.4f is above the %.2f mm ceiling, which may only be reduced."
              % (tol, SEAM_CEILING_MM))
        return 2
    sys.path.insert(0, HERE)
    import numpy as np
    import kitlib_render as R
    VA, TA = R.load_mesh_parts([q for q in pos[0].split("+") if q.strip()])
    VB, TB = R.load_mesh_parts([q for q in pos[1].split("+") if q.strip()])
    VA, TA, _r, _ = R._weld(np.asarray(VA, float), np.asarray(TA, int), [], tol * 1e-3)
    VB, TB, _r, _ = R._weld(np.asarray(VB, float), np.asarray(TB, int), [], tol * 1e-3)

    def _rim(V, T):
        e = np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]])
        u, c = np.unique(np.sort(e, axis=1), axis=0, return_counts=True)
        return [(int(x), int(y)) for x, y in u[c == 1]]
    rimA, rimB = _rim(VA, TA), _rim(VB, TB)
    print("kit seamweld: %s (%d tri, rim %d edges) + %s (%d tri, rim %d edges)"
          % (os.path.basename(pos[0]), len(TA), len(rimA),
             os.path.basename(pos[1]), len(TB), len(rimB)))
    if not rimA or not rimB:
        print("\nkit seamweld REFUSED: one of these meshes is CLOSED - it has no rim to weld to.")
        print("  This joins two OPEN meshes: the body with a hole in it, and the patch for the hole.")
        print("  A closed tool laid over a closed body is route B, the drop-in, and needs no weld.")
        return 2
    # open edges
    V, T, rep = R.weld_rims(VA, TA, rimA, VB, TB, rimB, tol=tol, require_all_paired=False)
    print("  loops: %d and %d, %s paired%s" % (
        rep.get("loopsA", 0), rep.get("loopsB", 0), rep.get("loops_paired", 0),
        ("   (%d unrelated boundary loop(s) left alone - the part's own open edges)"
         % rep["loops_unrelated"]) if rep.get("loops_unrelated") else ""))
    if rep.get("specks_ignored"):
        print("  %d degenerate speck(s) set aside - a loop under 3 vertices bounds no area (sizes %s); left in the mesh as they were"
              % (rep["specks_ignored"], rep.get("speck_sizes")))
    if V is None:
        print("\nkit seamweld REFUSED: %s" % rep.get("error", "the weld could not be made"))
        return 2
    print("  rim refined: %d -> %d edges on one side, %d -> %d on the other"
          % (rep["rimA_edges0"], rep["rimA_edges"], rep["rimB_edges0"], rep["rimB_edges"]))
    print("  worst rim vertex moved  %.4f mm   (ceiling %.2f)" % (rep["worst_mm"], SEAM_CEILING_MM))
    _left = len(rimA) + len(rimB) - (rep["rimA_edges"] - rep["rimA_edges0"]) \
        - (rep["rimB_edges"] - rep["rimB_edges0"])
    _expect = rep["boundary_out"]
    print("  boundary edges          %d in (both meshes), %d out" % (rep["boundary_in"], _expect))
    print("                          the paired rims are consumed; what remains is each mesh's own")
    print("                          open edges, which this weld is not responsible for.")
    print("  non-manifold edges      %d out" % rep["nonmanifold_out"])
    if rep["nonmanifold_out"] > 0:
        print("                          ^ ABOVE ZERO. The seam did not close cleanly - look before welding.")
    print("  result                  %d triangles, %d vertices" % (rep["tri"], rep["vert"]))
    R.write_stl(a["--out"], V, T)
    print("\n  written: %s" % a["--out"])
    print("  No ribbon triangles were made. The ratio gate 2 measures does not apply to this join;")
    print("  what matters is that every loop found a partner, and the count above says it did.")
    return 0



def cmd_atlas(args):
    """kit atlas init | status | add <name> ... | set <name> --definition DRAFT|RENDERED|CLIENT [--frame <png>] [--said "<words>"] | --edit <state> | --surface-file <stl> | stale <box>
             | cite <name> | faces <file> | recreated <name> --result <mesh> | assign <job> --to <r>|--new <r> | defer --until "<the client's words>" [--lift]  (31bv B1: a new project's atlas comes AFTER its model)

    THE REGION ATLAS. What the part's named pieces ARE, stored once, versioned with the model, and
    gated so it cannot go stale quietly.

    the client, 2026-09-22: *"projects will need to create and maintain an atlas as they work through CAD
    edits. It will need gating to force the updates so things don't become stale and it stays
    accurate."* The failure it comes out of, in the agent's words answering the client's question *"do you decide
    that fact new every time?"* - **yes**, on a part eleven revisions in. Three consecutive scripts in
    one session each re-derived every boundary from nothing; the acceptance table named its regions in
    prose with no coordinates for any of them. Every card was then written against a box invented that
    afternoon, the edit landed where that guess pointed, and it was read as a geometry problem and the
    box re-tuned - for weeks.

    **A BOX IS NOT A DEFINITION.** Three things are, and each was bought by a rejected delivery:
      * SURFACE DIRECTION - a sealing face is the DOWN-facing plane; the up-facing band 4 mm above it
        is a shelf, and a box holds both.
      * CONNECTIVITY BY SHARED VERTEX - bolt counterbores can lie in the same plane facing the same
        way, and only connectivity separates them. **Not by centroid:** a 150 mm rail's centroid sits
        75 mm from the corner it touches, so one closed ring came back as 46 "clusters".
      * AREA LIMITS - a blade face is 490-1800 mm2; the seam debris welded to it is 10-60.

    And a face list is not a region either: on one real body **155 of 4,765 faces span more than
    100 mm and carry 51.4 pct of the surface**, so "the faces whose centroid is in box B" is wrong for
    half the part however good the box is. The atlas tool has to CUT a crossing face on the boundary.

    THE GATES, as wired 2026-09-22 - the day the client approved the first atlas, and not before (*"wire atlas
    gates after defining the atlas and getting it approved by me"*). A project with no atlas, or none
    confirmed, is told and nothing refuses. Once a region is at CLIENT:
      * `kit job` refuses a card with no `Region:` and a region not at CLIENT; it warns on one edited since
        its map was taken;
      * FROZEN means RECREATED, not untouchable (the client, 2026-09-22: *"The vanes are locked but have to be
        allowed into edits. The point of them being frozen is they need to be recreated at the end of
        edits."*). A frozen region may be in a selection; once a job that named it applies, it is
        RECREATE OWED, `kit atlas recreated <region> --result <mesh>` measures it back against its
        original, and `kit deliverycheck` refuses while one is owed;
      * `kit apply` records the job's regions as EDITED - the map predates the model; the definition
        stays citable. `kit atlas stale <box>` still stales by space, by hand.
    NOT gated yet, because it has not been run: how a region's map is re-taken after an edit.
    """
    a = _kv(args)
    sub = (a["_"][0] if a["_"] else "status").lower()
    doc = G.atlas_load(ROOT)

    if sub == "init":
        if doc:
            print("kit atlas: an atlas already exists (%d region(s))." % len(doc.get("regions", {})))
            return 0
        G.atlas_save(ROOT, {"model": _opt(args, "--model", ""), "regions": {},
                            "created": G._now()})
        print("kit atlas: created %s" % os.path.join("claude_code", G.ATLAS_FILE))
        try:
            if os.path.exists(G.atlas_defer_path(ROOT)): os.remove(G.atlas_defer_path(ROOT)); print("  (the deferral recorded by `kit atlas defer` is lifted - the atlas exists now)")
        except OSError: pass
        print("  Now inventory the part before carding anything. `kit inventory` enumerates a")
        print("  repeating feature; `kit atlas add` records what each one IS.")
        return 0

    if sub == "defer":
        if _flag(args, "--lift"):
            _dp = G.atlas_defer_path(ROOT)
            if os.path.exists(_dp):
                os.remove(_dp); print("kit atlas: the deferral LIFTED - the atlas question returns at the next turn's end; `kit atlas init` starts the atlas"); return 0
            print("kit atlas: no deferral is recorded"); return 0
        _until = (_opt(args, "--until", "") or "").strip()
        if len(_until) < 12:
            print("kit atlas defer REFUSED: --until \"<the client's words - what must exist before the atlas is worth making>\" (twelve characters at least); `kit atlas defer --lift` ends it"); return 2
        if doc:
            print("kit atlas defer: an atlas already exists (%d region(s)) - nothing to defer; `kit deliver --no-atlas \"<why>\"` is the way past its gates" % len(doc.get("regions", {}))); return 2
        _old = G.atlas_deferred(ROOT) or {}
        if _old.get("ended"): print("  (the earlier deferral of %s had ENDED by %s - a new one starts now)" % (_old.get("when"), (_old.get("ended") or {}).get("how")))
        _rec = {"until": _until, "when": G._now(), "by": "the client's word (kit atlas defer --until)"}
        os.makedirs(os.path.join(ROOT, "claude_code"), exist_ok=True)
        with open(G.atlas_defer_path(ROOT), "w", encoding="utf-8") as fh:
            json.dump(_rec, fh, indent=1)
        print("kit atlas: DEFERRED until \"%s\" (%s) - the stop hook's atlas question is silent, a card's Region: reads 'no atlas yet (deferred)', a delivery owes no --no-atlas;\n"
              "  it returns at the next promoted model of record (the first, on a new project) or `kit atlas defer --lift`; `kit atlas init` starts the atlas and ends the deferral (31bv B1)" % (_until, _rec["when"]))
        return 0
    if not doc:
        _dfr = G.atlas_deferred(ROOT)
        if _dfr:
            print("kit atlas: DEFERRED since %s until \"%s\" (31bv B1) - no atlas yet, on the client's word: `kit atlas init` starts one, `kit atlas defer --lift` ends the deferral%s"
                  % (_dfr.get("when"), _dfr.get("until"), _defer_end_clause(_dfr)))
            return 0
        print("kit atlas: THIS PROJECT HAS NO ATLAS.")
        print("  Nothing records what this part's named regions ARE, so every card is written against")
        print("  a box invented that day and the edit lands where that guess pointed. On the part that")
        print("  taught this, three scripts in ONE session each re-derived every boundary from nothing.")
        print("    kit atlas init")
        return 2

    regs = doc.setdefault("regions", {})

    if sub == "status":
        if not regs:
            print("kit atlas: 0 regions. An empty atlas is the starting point, not the finish.")
            return 0
        by_def, by_edit = {}, {}
        for r in regs.values():
            by_def[r.get("definition_status", "DRAFT")] = by_def.get(r.get("definition_status", "DRAFT"), 0) + 1
            by_edit[r.get("edit_status", "OPEN")] = by_edit.get(r.get("edit_status", "OPEN"), 0) + 1
        print("kit atlas: %d region(s)   definition %s   edit %s"
              % (len(regs),
                 " ".join("%s=%d" % kv for kv in sorted(by_def.items())),
                 " ".join("%s=%d" % kv for kv in sorted(by_edit.items()))))
        cit = [n for n, r in regs.items() if r.get("definition_status") == "CLIENT"]
        print("  CITABLE BY A CARD (definition CLIENT): %s" % (", ".join(sorted(cit)) if cit else "NONE"))
        stale = [n for n, r in regs.items() if r.get("definition_status") == "STALE"]
        if stale:
            print("  STALE - an edit touched their space, re-look before citing: %s" % ", ".join(sorted(stale)))
        run = G.atlas_running(ROOT)
        if run:
            print("  edit RUNNING: %s" % ", ".join(sorted(run)))
        owe = G.atlas_recreate_owed(ROOT)
        if owe:
            print("  RECREATE OWED - frozen regions an applied edit reached; delivery refuses until each is measured back:")
            for n in sorted(owe):
                print("    %-24s by %s   -> kit atlas recreated %s --result <final mesh>" % (n, ", ".join(owe[n]), n))
        edt = [n for n, r in regs.items() if r.get("edited_by")]
        if edt:
            print("  EDITED since their map was taken (definition still the client; face list and pieces predate the model):")
            for n in sorted(edt):
                e = regs[n]["edited_by"][-1]
                print("    %-24s by %s, %s" % (n, e.get("job", "?"), e.get("when", "")))
        if _opt(args, "--long", "") or "--long" in args:
            for n in sorted(regs):
                r = regs[n]
                print("\n  %-28s %s / %s" % (n, r.get("definition_status", "DRAFT"),
                                              r.get("edit_status", "OPEN")))
                print("      %s" % r.get("what_it_is", "NO PHYSICAL DEFINITION RECORDED"))
                if r.get("box"):
                    print("      space   %s" % " ".join("%g" % v for v in r["box"]))
                for k in ("surface", "connectivity", "area_limits", "evidence"):
                    if r.get(k):
                        print("      %-8s%s" % (k[:7] + " ", r[k]))
        return 0

    if sub == "add":
        rest = a["_"][1:]
        if not rest:
            print(cmd_atlas.__doc__); return 2
        name = rest[0]
        what = _opt(args, "--what", "")
        if not what.strip():
            print("kit atlas add REFUSED: --what is required - the region's PHYSICAL definition in one")
            print("  sentence. What mates to it, which way its surface faces, what it does. A name and")
            print("  a box with no statement of what the thing IS is how a shelf got called a seat.")
            return 2
        box = None
        if "--box" in args:
            i = args.index("--box")
            try:
                box = [float(v) for v in args[i + 1:i + 7]]
                assert len(box) == 6
            except Exception:
                print("kit atlas add: --box needs six numbers"); return 2
        surf = _opt(args, "--surface", "")
        if not surf:
            print("kit atlas add: NOTE - no --surface given. A box holds both a down-facing sealing")
            print("  face and the up-facing shelf above it; only the surface direction separates them.")
        conflict = G.atlas_axis_conflict(name, box, doc.get("axis"))
        if conflict:
            # recorded
            print("kit atlas add: WARNING - %s" % conflict)
            print("  Recorded anyway. Check the name AND the recorded axis (`kit atlas axis`) - one of")
            print("  them is wrong, and on 2026-09-22 it was the axis.")
        regs[name] = {"what_it_is": what, "box": box, "surface": surf,
                      "connectivity": _opt(args, "--connectivity", ""),
                      "area_limits": _opt(args, "--area", ""),
                      "faces": regs.get(name, {}).get("faces", []),
                      "evidence": _opt(args, "--evidence", ""),
                      "definition_status": "DRAFT", "edit_status": _opt(args, "--edit", "OPEN"),
                      "model": doc.get("model", ""), "when": G._now()}
        G.atlas_save(ROOT, doc)
        print("kit atlas: %r recorded at definition DRAFT." % name)
        print("  DRAFT is not citable. Render it ALONE from the side that can physically show it,")
        print("  judge that frame, then `kit atlas set %s --definition RENDERED --frame <that frame>`; the client's confirmation (--definition CLIENT --said \"<the client's words>\")" % name)
        print("  raises it to CLIENT, which is the only status a card may cite.")
        return 0

    if sub == "set":
        rest = a["_"][1:]
        if not rest or rest[0] not in regs:
            print("kit atlas set <name> --definition DRAFT|RENDERED|CLIENT [--frame <the frame judged - RENDERED needs it>] [--said \"<the client's words - the client needs them>\"]  --edit %s" % "|".join(G.ATLAS_EDIT))
            return 2
        r = regs[rest[0]]
        d = _opt(args, "--definition", "")
        e = _opt(args, "--edit", "")
        if d:
            if d not in G.ATLAS_DEF:
                print("kit atlas set: --definition is one of %s" % ", ".join(G.ATLAS_DEF)); return 2
            if d == "CLIENT" and not _opt(args, "--said", ""):
                print("kit atlas set REFUSED: raising a definition to CLIENT needs --said \"<the client's words, or")
                print("  the FaceN correction the client sent>\". That status means the client confirmed this")
                print("  boundary; an agent cannot award it on its own judgement.")
                return 2
            if d == "RENDERED" and not _opt(args, "--frame", ""):
                print("kit atlas set REFUSED: RENDERED means somebody OPENED a frame of this region")
                print("  alone and judged it. Name it: --frame <path>.")
                return 2
            r["definition_status"] = d
            if _opt(args, "--said", ""):
                r["client_said"] = _opt(args, "--said", "")
            if _opt(args, "--frame", ""):
                r["evidence"] = _opt(args, "--frame", "")
            r.pop("stale_why", None); r.pop("stale_when", None)
        if e:
            if e not in G.ATLAS_EDIT:
                print("kit atlas set: --edit is one of %s" % ", ".join(G.ATLAS_EDIT)); return 2
            r["edit_status"] = e
        if _opt(args, "--surface-file", ""):
            r["surface_file"] = _opt(args, "--surface-file", "")
        if _opt(args, "--recreate-tol", ""):
            # recorded
            try:
                rt = float(_opt(args, "--recreate-tol", ""))
            except ValueError:
                print("kit atlas set: --recreate-tol takes millimetres"); return 2
            if rt <= 0 or rt > PRINT_TOL_MM + 1e-12:
                print("kit atlas set REFUSED: --recreate-tol %.3f - a frozen region comes back within the print tolerance (%.2f mm) at most" % (rt, PRINT_TOL_MM)); return 2
            if not _opt(args, "--said", ""):
                print("kit atlas set REFUSED: --recreate-tol needs --said \"<the client's words, or the client's requirement it rests on>\" - a region's class is the client's"); return 2
            r["recreate_tol"] = {"mm": rt, "said": _opt(args, "--said", ""), "when": G._now()}
        if "--buried-ok" in args:
            if not _opt(args, "--said", ""):
                print("kit atlas set REFUSED: --buried-ok needs --said \"<the client's words>\" - whether a frozen region"
                      " may be blended onto is their call."); return 2
            r["buried_ok"] = {"said": _opt(args, "--said", ""), "when": G._now()}
        r["when"] = G._now()
        G.atlas_save(ROOT, doc)
        print("kit atlas: %s is now %s / %s" % (rest[0], r.get("definition_status"), r.get("edit_status")))
        return 0

    if sub == "stale":
        rest = a["_"][1:]
        try:
            box = [float(v) for v in rest[:6]]
            assert len(box) == 6
        except Exception:
            print("kit atlas stale x0 x1 y0 y1 z0 z1 [--why \"...\"]"); return 2
        hit = G.atlas_mark_stale(ROOT, box, _opt(args, "--why", ""))
        print("kit atlas: %d region(s) marked STALE%s" % (len(hit), (": " + ", ".join(hit)) if hit else ""))
        return 0

    if sub == "recreated":
        return _atlas_recreated(args, doc, regs)

    if sub == "assign":
        rest = a["_"][1:]
        to, new = _opt(args, "--to", ""), _opt(args, "--new", "")
        if not rest or bool(to) == bool(new):
            print("kit atlas assign <job or burrito tag> --to <existing region>")
            print("kit atlas assign <job or burrito tag> --new <name> --what \"<its physical definition>\"")
            print("  Exactly one of the two. A new section is created at DRAFT and must be announced to the client.")
            return 2
        key = rest[0]
        _bx = None
        try:
            _j = G.job(ROOT, key) or {}
            if _j.get("box"):
                _bx = [float(v) for v in str(_j["box"]).split()]
        except Exception:
            pass
        ok, msg = G.atlas_assign(ROOT, key, region=to or None, new=new or None, what=_opt(args, "--what", ""), box=_bx)
        if not ok:
            print("kit atlas assign REFUSED: %s" % msg); return 2
        if new:
            print("kit atlas: NEW SECTION %r created at DRAFT for %s's geometry." % (new, key))
            print("  ANNOUNCE IT TO the client IN THE CHAT: \"%s creates a new section, %s: %s\"" % (key, new, _opt(args, "--what", "")))
        else:
            print("kit atlas: %s's new geometry is assigned to %s." % (key, to))
        return 0

    if sub == "cite":
        rest = a["_"][1:]
        ok, msg = G.atlas_citable(ROOT, rest[0] if rest else "")
        print("kit atlas cite: %s" % msg)
        return 0 if ok else 2

    if sub == "find":
        words = re.findall(r"[a-z0-9_]+", " ".join(a["_"][1:]).lower())
        if not words:
            print("kit atlas find <words describing the feature>   -> the region(s), box, frozen?, citable?, dossier?")
            return 2
        hits = []
        for n, r in regs.items():
            text = (" ".join([n, r.get("what_it_is", ""), r.get("surface", ""), r.get("connectivity", ""),
                              " ".join(r.get("aliases", []) if isinstance(r.get("aliases"), list) else [])])).lower()
            nm = n.lower().replace("_", " ")
            score = 0
            for w in words:
                if w == nm or w in nm.split() or w.rstrip("s") == nm or w.rstrip("s") in nm.split():
                    score += 3
                elif w in text or w.rstrip("s") in text:
                    score += 1
            if score:
                hits.append((score, n, r))
        if not hits:
            print("kit atlas find: no region matches %r. The %d regions are: %s\n  A feature no region names is a"
                  " NEW region (kit atlas add <name> --what \"...\"), announced to the client before it is carded."
                  % (" ".join(words), len(regs), ", ".join(sorted(regs))))
            return 1
        hits.sort(key=lambda h: (-h[0], h[1]))
        try:
            dossiers = D.list_defined(ROOT) if hasattr(D, "list_defined") else []
        except Exception:
            dossiers = []
        for score, n, r in hits[:4]:
            box = r.get("box")
            print("%s  [%s / %s]%s" % (n, r.get("definition_status", "DRAFT"), r.get("edit_status", "OPEN"),
                                       "   CITABLE" if r.get("definition_status") == "CLIENT" else "   NOT citable - the client has not confirmed it"))
            print("    what : %s" % (r.get("what_it_is", "") or "(no physical definition recorded)"))
            if box:
                print("    box  : %s   (%s x %s x %s mm)" % (" ".join("%g" % v for v in box),
                      "%g" % (box[1] - box[0]), "%g" % (box[3] - box[2]), "%g" % (box[5] - box[4])))
            if r.get("edit_status") == "FROZEN":
                print("    FROZEN: it may sit inside a selection; it is put back exactly at the end of edits and delivery"
                      " refuses until `kit atlas recreated %s` measures it%s." % (n, " (buried allowed)" if r.get("buried_ok") else ""))
            if r.get("edited_by"):
                e = r["edited_by"][-1]
                print("    edited since its map: by %s, %s" % (e.get("job", "?"), e.get("when", "")))
            if box and dossiers:
                ov = [d for d in dossiers if d.get("box") and all(d["box"][2 * k] <= box[2 * k + 1] and d["box"][2 * k + 1] >= box[2 * k] for k in range(3))]
                print("    dossier: %s" % (", ".join("%s (%s)" % (d["name"], d.get("state", "?")) for d in ov) if ov else "none covers this box - kit dossier take <name> --box ... when an edit needs its numbers"))
            if r.get("surface_file"):
                print("    surface: %s" % r["surface_file"])
        if len(hits) > 4:
            print("  (+%d more: %s)" % (len(hits) - 4, ", ".join(h[1] for h in hits[4:])))
        return 0

    if sub == "render":
        return _atlas_render(args, doc, regs)

    if sub == "recipe":
        rec = doc.get("recipe") or {}
        given = {k: _opt(args, "--" + k, "") for k in ("split", "features", "template", "moves")}
        if not any(given.values()):
            if rec:
                print("kit atlas recipe: %s" % json.dumps(rec, indent=1))
            else:
                print("kit atlas recipe --split <regions spec .json> --features <features .json> --template <gui-saved .FCStd> [--moves <moves .json>]")
                print("  the files that produced the approved map; `kit atlas render` re-runs them on the model of record.")
            return 0
        for k, v in given.items():
            if v:
                p = v if os.path.isabs(v) else os.path.join(ROOT, v)
                if not os.path.isfile(p):
                    print("kit atlas recipe REFUSED: --%s names a file that does not exist: %s" % (k, p)); return 2
                rec[k] = v
        doc["recipe"] = rec
        G.atlas_save(ROOT, doc)
        print("kit atlas recipe: recorded %s" % ", ".join("%s=%s" % (k, rec[k]) for k in rec))
        return 0

    if sub == "behind":
        b, msg = atlas_behind(doc)
        print("kit atlas behind: %s%s" % ("YES - " if b else "no - ", msg))
        return 1 if b else 0

    if sub == "extent":
        model = _opt(args, "--model") or _model_of_record()
        if not model or not os.path.isfile(model):
            print("kit atlas extent: no model of record (--model <brep>)"); return 2
        cur = doc.get("body_extent") or {}
        md5 = _md5(model)
        if cur.get("md5") == md5 and "--force" not in args:
            print("kit atlas extent: %s   (%s, unchanged)" % (" ".join("%g" % v for v in cur["box"]), os.path.basename(model))); return 0
        _scr = os.path.join(G.store(ROOT), "scratch"); os.makedirs(_scr, exist_ok=True)
        _res = os.path.join(_scr, "atlas_extent.json")
        if os.path.exists(_res):
            os.remove(_res)
        code = ("import Part, json\nsh = Part.Shape(); sh.importBrep(%r)\n"
                "try:\n    bb = sh.optimalBoundingBox()\nexcept Exception:\n    bb = sh.BoundBox\n"
                "json.dump({'box': [bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax], 'faces': len(sh.Faces)}, open(%r, 'w'))\n"
                "print('EXTENT %%.4f %%.4f %%.4f %%.4f %%.4f %%.4f' %% (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))\n"
                "print('BOOKKEEPING extent')\n" % (model, _res))
        rc = _fc(code, os.path.join(ROOT, "claude_code"), "atlas_extent")
        if rc != 0 or not os.path.isfile(_res):
            print("kit atlas extent FAILED (rc %s) - no result written" % rc); return 2
        box = [float(t) for t in json.load(open(_res, encoding="utf-8"))["box"]]
        doc["body_extent"] = {"box": box, "model": os.path.relpath(model, ROOT) if model.startswith(ROOT) else model,
                              "md5": md5, "when": G._now()}
        G.atlas_save(ROOT, doc)
        print("kit atlas extent: %s   (%s, recorded)" % (" ".join("%g" % v for v in box), os.path.basename(model)))
        return 0

    if sub == "faces":
        return _atlas_faces(args, doc, regs)

    if sub == "import":
        return cmd_atlas_import(args, doc)

    if sub == "axis":
        rest = a["_"][1:]
        if len(rest) < 3:
            print("kit atlas axis <x|y|z> <front coordinate> <aft coordinate> --said \"<where it was settled>\"")
            print("  Records which end of the part is the FRONT, once, so a region can never again be")
            print("  NAMED for one end while its box sits at the other. Four did, in one delivered map.")
            cur = doc.get("axis")
            if cur:
                print("  currently: %s front %.1f, aft %.1f   (%s)"
                      % (cur.get("axis"), cur.get("front"), cur.get("aft"), cur.get("said", "")))
            return 2
        if not _opt(args, "--said", ""):
            print("kit atlas axis REFUSED: --said is required - WHERE this was settled. An orientation")
            print("  taken from an assembly is a fact; one taken from a render is a guess, and the next")
            print("  agent cannot tell them apart unless you say which it was.")
            return 2
        doc["axis"] = {"axis": rest[0].lower()[:1], "front": float(rest[1]), "aft": float(rest[2]),
                       "said": _opt(args, "--said", ""), "when": G._now()}
        bad = [G.atlas_axis_conflict(n, r.get("box"), doc["axis"]) for n, r in regs.items()]
        bad = [b for b in bad if b]
        G.atlas_save(ROOT, doc)
        print("kit atlas: axis recorded - %s, front %.1f, aft %.1f"
              % (doc["axis"]["axis"], doc["axis"]["front"], doc["axis"]["aft"]))
        if bad:
            print("\n  %d EXISTING region(s) are named for the wrong end:" % len(bad))
            for b in bad:
                print("    " + b)
            print("  A name is the only thing most readers ever see of a region. Rename them.")
        return 0

    print(cmd_atlas.__doc__)
    return 2


def _atlas_recreated(args, doc, regs):
    """kit atlas recreated <region> --result <final mesh.stl> [--original <region surface.stl>] [--tol 0.15]
                                   [--baseline <the mesh BEFORE the edits.stl>] [--where]

    --baseline: the same samples on the pre-edit mesh; a count that did not RISE above the baseline's passes (a
    mesh-route project's frozen regions already miss on the untouched rework mesh - 7, 5 and 6 cells on three of them ... -
    and without the baseline the gate cannot pass and cannot tell new damage from old). --where: the off samples'
    places, CUT and BURIED, as 3 mm clusters with boxes (flags go AFTER the region name). The result is cropped to
    the region's box + 5 mm before the ray tests (heatsink: 10-12 min -> ~1 min).

    A FROZEN REGION IS RECREATED AT THE END OF EDITS, and this is the measurement that says it was. the client,
    2026-09-22: *"The vanes are locked but have to be allowed into edits. The point of them being frozen
    is they need to be recreated at the end of edits."* Samples are taken ON the region's original
    surface (its vertices and triangle centres) and each is measured to the nearest triangle of the
    result. The worst must be inside --tol, a ceiling of 0.15 mm that may only be lowered. PASS clears
    the region's RECREATE OWED; a miss refuses and changes nothing. How the region was recreated is the
    job's business - this checks that it was. A region with a recorded RECREATE CLASS (kit atlas set <r>
    --recreate-tol <mm> --said ..., at most the 0.30 print tolerance - 31ai) is held to that instead of 0.15."""
    a = _kv(args)
    rest = a["_"][1:]
    if not rest or rest[0] not in regs:
        print(_atlas_recreated.__doc__); return 2
    name = rest[0]; r = regs[name]
    res = a.get("--result", "")
    orig = a.get("--original", "") or r.get("surface_file", "")
    if orig and not os.path.isabs(orig):
        orig = os.path.join(ROOT, orig)
    if not res or not os.path.exists(res):
        print("kit atlas recreated: --result <the final mesh, STL> is required and must exist."); return 2
    if not orig or not os.path.exists(orig):
        print("kit atlas recreated: no original surface for %r. --original <its surface as STL>, or record it once:" % name)
        print("  kit atlas set %s --surface-file <path>" % name); return 2
    if not orig.lower().endswith(".stl"):
        print("kit atlas recreated: the original %s is not an STL. Export it first (`kit measure <brep> export`)," % orig)
        print("  then pass --original <the .stl>."); return 2
    _rt = r.get("recreate_tol") or {}
    ceiling = float(_rt["mm"]) if isinstance(_rt, dict) and _rt.get("mm") else SEAM_CEILING_MM
    tol = float(a.get("--tol", ceiling))
    if tol > ceiling + 1e-12:
        print("kit atlas recreated REFUSED: --tol %.3f is above %s's %.2f mm ceiling, which may only be lowered%s."
              % (tol, name, ceiling, (" (its recreate class: %s)" % _rt.get("said", "")) if ceiling != SEAM_CEILING_MM else "")); return 2
    if ceiling != SEAM_CEILING_MM:
        print("  %s's recreate class: within %.2f mm (%s)" % (name, ceiling, _rt.get("said", "")))
    import numpy as np
    sys.path.insert(0, HERE)
    import kitlib_render as R
    OV, OT = R.read_stl(orig)
    OV = np.asarray(OV, float); OT = np.asarray(OT, int)
    P = np.vstack([OV, OV[OT].mean(1)])
    maxp = int(a.get("--max-pts", 20000))
    if len(P) > maxp:
        P = P[np.linspace(0, len(P) - 1, maxp).astype(int)]
    Ct = OV[OT].mean(1)
    Nt = np.cross(OV[OT[:, 1]] - OV[OT[:, 0]], OV[OT[:, 2]] - OV[OT[:, 0]])
    _ln = np.linalg.norm(Nt, axis=1); _ok = _ln > 1e-12
    Ct, Nt = Ct[_ok], Nt[_ok] / _ln[_ok][:, None]
    _pick = np.linspace(0, len(Ct) - 1, min(len(Ct), 3000)).astype(int) if len(Ct) else np.zeros(0, int)
    Cs, Ns = Ct[_pick], Nt[_pick]
    import kit_crop as KC
    box = [float(OV[:, 0].min()), float(OV[:, 0].max()), float(OV[:, 1].min()), float(OV[:, 1].max()),
           float(OV[:, 2].min()), float(OV[:, 2].max())]

    def _load_cropped(path):
        V_, T_ = R.read_stl(path)
        V_ = np.asarray(V_, float); T_ = np.asarray(T_, int)
        if len(T_) > 200000:
            try:
                cV_, cT_, _, _, _, _ = KC.crop(V_, T_, box, margin=5.0)
                if len(cT_):
                    return cV_, cT_, len(T_)
            except Exception as e:
                print("  (the crop of %s to the region's box failed - %s - measuring against the whole mesh)"
                      % (os.path.basename(path), str(e)[:120]))
        return V_, T_, len(T_)

    def _measure(V_, T_):
        """(d, off, n_cut, n_bur, cut_pts, bur_pts, n_on, covered, bare) of the region's samples against one mesh."""
        h = 2.0
        keys = {tuple(k) for k in np.floor(P / h).astype(int)}
        near = set()
        for k in keys:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        near.add((k[0] + dx, k[1] + dy, k[2] + dz))
        ck = np.floor(V_[T_].mean(1) / h).astype(int)
        keep = np.array([tuple(k) in near for k in ck], bool)
        if not keep.any():
            return None
        d_ = R.point_tri_dist(P, V_, T_[keep])
        # DIFFERENT
        off_ = d_ > tol
        n_cut_ = n_bur_ = 0
        cut_pts = np.zeros((0, 3)); bur_pts = np.zeros((0, 3))
        n_on = covered = bare = 0
        # over the
        if len(Cs):
            _dc = R.point_tri_dist(Cs, V_, T_[keep])
            _on = _dc <= tol
            if _on.any():
                eps = 2.0 * tol
                _a = R.points_inside(Cs[_on] + eps * Ns[_on], V_, T_)
                _b = R.points_inside(Cs[_on] - eps * Ns[_on], V_, T_)
                _sc = len(Ct) / float(len(_pick))
                n_on = int(_on.sum()); covered = int((_a & _b).sum()); bare = int((~_a & ~_b).sum())
                n_bur_ += int(round(covered * _sc)); n_cut_ += int(round(bare * _sc))
                cut_pts = np.vstack([cut_pts, Cs[_on][~_a & ~_b]]); bur_pts = np.vstack([bur_pts, Cs[_on][_a & _b]])
        if off_.any():
            Q = P[off_]
            pick = np.linspace(0, len(Q) - 1, min(len(Q), 5000)).astype(int)
            ins = R.points_inside(Q[pick], V_, T_)
            scale = len(Q) / float(len(pick))
            n_bur_ += int(round(ins.sum() * scale)); n_cut_ += int(round((~ins).sum() * scale))
            cut_pts = np.vstack([cut_pts, Q[pick][~ins]]); bur_pts = np.vstack([bur_pts, Q[pick][ins]])
        return d_, off_, n_cut_, n_bur_, cut_pts, bur_pts, n_on, covered, bare

    def _clusters(X, cell=3.0, top=8):
        """the off samples grouped on a 3 mm grid, largest first: [(count, box)]"""
        if not len(X):
            return []
        k = np.floor(X / cell).astype(int)
        uk, inv, cnt = np.unique(k, axis=0, return_inverse=True, return_counts=True)
        inv = np.asarray(inv).reshape(-1)
        out = []
        for j in np.argsort(-cnt)[:top]:
            Xi = X[inv == j]
            out.append((int(cnt[j]), [round(float(v), 1) for v in np.concatenate([Xi.min(0), Xi.max(0)])[[0, 3, 1, 4, 2, 5]]]))
        return out

    RV, RT, n_res = _load_cropped(res)
    m = _measure(RV, RT)
    if m is None:
        print("kit atlas recreated REFUSED: the result has NO surface where %s's original is - it is not there at all." % name)
        return 2
    d, off, n_cut, n_bur, cut_pts, bur_pts, n_on, covered, bare = m
    worst = float(d.max()); p99 = float(np.percentile(d, 99))
    print("kit atlas recreated: %s - %d samples on its original surface against %s%s"
          % (name, len(P), os.path.basename(res), (" (cropped to the region's box + 5 mm: %d of %d triangles)" % (len(RT), n_res)) if len(RT) != n_res else ""))
    print("  distance to the result   median %.3f  p99 %.3f  worst %.3f mm   (limit %.2f)"
          % (float(np.median(d)), p99, worst, tol))
    if n_on:
        print("  on the result's surface: %d triangle(s) checked both sides - covered %d, bare %d" % (n_on, covered, bare))
    if off.any():
        print("  off the result by more than %.2f mm: %d sample(s)" % (tol, int(off.sum())))
    print("  CUT (material gone) %d, BURIED (under added material) %d   (both counts include the covered/bare triangles)" % (n_cut, n_bur))
    where = "--where" in args
    if where:
        for label, X in (("CUT", cut_pts), ("BURIED", bur_pts)):
            for n_, b_ in _clusters(X):
                print("    %-6s %5d sample(s)  box x %g..%g y %g..%g z %g..%g" % (label, n_, *b_))
    base_path = a.get("--baseline", "")
    b_cut = b_bur = None
    if base_path:
        if not os.path.exists(base_path):
            print("kit atlas recreated: --baseline %s does not exist." % base_path); return 2
        BV, BT, n_b = _load_cropped(base_path)
        mb = _measure(BV, BT)
        if mb is None:
            print("kit atlas recreated: the baseline has no surface where %s's original is - not a baseline of this part." % name); return 2
        b_cut, b_bur = mb[2], mb[3]
        print("  baseline %s: CUT %d, BURIED %d  ->  the result's counts must not RISE above these"
              % (os.path.basename(base_path), b_cut, b_bur))
        if where:
            for label, X in (("CUT", mb[4]), ("BURIED", mb[5])):
                for n_, b_ in _clusters(X):
                    print("    baseline %-6s %5d sample(s)  box x %g..%g y %g..%g z %g..%g" % (label, n_, *b_))
    cut_bad = n_cut > (b_cut if b_cut is not None else 0)
    bur_bad = n_bur > (b_bur if b_bur is not None else 0) and not r.get("buried_ok")
    if cut_bad:
        print("\nkit atlas recreated REFUSED: %d sample(s) of %s's original surface lost their material%s - the frozen"
              " region was cut into or rounded, and was not recreated there. Nothing was recorded.%s"
              % (n_cut, name, (" (baseline %d)" % b_cut) if b_cut is not None else "",
                 "" if where else "  Run it again with --where for the places."))
        return 2
    if bur_bad:
        print("\nkit atlas recreated REFUSED: %d sample(s) of %s's original surface are BURIED under added material%s."
              % (n_bur, name, (" (baseline %d)" % b_bur) if b_bur is not None else ""))
        print("  If that is an intended blend onto this frozen region (a round at its root), the client records it once:")
        print("      kit atlas set %s --buried-ok --said \"<the client's words>\"" % name)
        print("  Otherwise it is a bead on a frozen feature. Nothing was recorded.%s" % ("" if where else "  --where prints the places."))
        return 2
    owed = [e.get("job", "?") for e in r.get("recreate_owed", [])]
    r["recreated"] = {"when": G._now(), "result": os.path.abspath(res), "original": orig, "worst_mm": round(worst, 4),
                      "p99_mm": round(p99, 4), "tol_mm": tol, "cut": n_cut, "buried": n_bur, "cleared": owed,
                      "baseline": (os.path.abspath(base_path) if base_path else None),
                      "baseline_cut": b_cut, "baseline_buried": b_bur}
    r["recreate_owed"] = []
    G.atlas_save(ROOT, doc)
    print("  PASS - %s is its original to within %.2f mm%s%s.%s" % (name, tol,
          (", except %d sample(s) buried under a blend the client allowed" % n_bur) if (n_bur and r.get("buried_ok")) else "",
          (" - no count rose above the baseline's (CUT %d, BURIED %d)" % (b_cut, b_bur)) if b_cut is not None else "",
          (" RECREATE OWED cleared (%s)." % ", ".join(owed)) if owed else ""))
    return 0


def _atlas_faces(args, doc, regs):
    """kit atlas faces <file|-> --region <name> [--facemap <map facemap>|--body] [--mode set|add|remove]
                                               — the client's own FreeCAD clicks, straight into a region.

    Corrections come back as lines pasted out of FreeCAD's selection view:

        Gui.Selection.addSelection('R31_MAP','ED_H_aft_exit_ceiling','Face412',1.2,-3.4,5.6)

    THAT IS THE MOST AUTHORITATIVE INPUT THIS PROJECT GETS and there was no verb for it. the client, on a
    region that had swallowed half the underside: *"flat skirt bottom has way too much in it. Should
    be just [four faces]."* With this it is a one-line correction; without it, it is another guess.
    """
    a = _kv(args)
    name = a.get("--region", "")
    if not name or name not in regs:
        print("kit atlas faces <file|-> --region <an existing region>")
        print("  regions: %s" % ", ".join(sorted(regs)) if regs else "  (none)")
        return 2
    src = a["_"][1] if len(a["_"]) > 1 else "-"
    try:
        txt = sys.stdin.read() if src == "-" else open(src, encoding="utf-8", errors="replace").read()
    except OSError as e:
        print("kit atlas faces: %s" % e); return 2
    import re as _re
    hits = _re.findall(r"""addSelection\s*\(\s*['"]([^'"]*)['"]\s*,\s*['"]([^'"]*)['"]\s*,\s*['"]\s*Face(\d+)""",
                       txt)
    if not hits:
        hits = [("", "", m) for m in _re.findall(r"\bFace(\d+)\b", txt)]
    if not hits:
        print("kit atlas faces: nothing that looks like a FreeCAD selection in that input.")
        print("  Paste the lines FreeCAD's selection view prints, or any text carrying FaceN.")
        return 2
    objs = sorted({h[1] for h in hits if h[1]})
    # translated
    fmap = a.get("--facemap", "")
    if objs and not fmap and "--body" not in args:
        print("kit atlas faces REFUSED: these picks name object(s) %s. On a region map a FaceN is LOCAL to its"
              % ", ".join(objs))
        print("  object. Give the map's facemap (--facemap <map>_facemap.json|.md) to translate them to body faces,")
        print("  or --body if they were picked on the body itself.")
        return 2
    if fmap:
        _fm = _read_facemap(fmap)
        if not _fm:
            print("kit atlas faces: nothing readable in the facemap %s" % fmap); return 2
        faces_, bad_ = set(), []
        for _doc, _obj, _n in hits:
            _orig = (_fm.get(_obj) or {}).get(int(_n))
            if _orig is None:
                bad_.append("%s.Face%s" % (_obj or "?", _n))
            else:
                faces_.add(int(_orig))
        if bad_:
            print("kit atlas faces REFUSED: %d pick(s) are not in the facemap: %s" % (len(bad_), ", ".join(bad_[:10])))
            return 2
        faces = sorted(faces_)
        print("kit atlas faces: %d pick(s) translated through %s to %d body face(s)" % (len(hits), os.path.basename(fmap), len(faces)))
    else:
        faces = sorted({int(h[2]) for h in hits})
    mode = (a.get("--mode", "set") or "set").lower()
    was = list(regs[name].get("faces", []))
    if mode == "add":
        new = sorted(set(was) | set(faces))
    elif mode == "remove":
        new = sorted(set(was) - set(faces))
    else:
        new = faces
    regs[name]["faces"] = new
    # FROM the client
    regs[name]["faces_from"] = {"objects": objs, "when": G._now(), "mode": mode,
                                "source": src if src != "-" else "pasted"}
    if regs[name].get("definition_status") == "CLIENT" and mode != "set":
        regs[name]["definition_status"] = "DRAFT"
        print("  NOTE: this region was at CLIENT and its face list just changed, so it drops to DRAFT.")
    G.atlas_save(ROOT, doc)
    print("kit atlas faces: %s  %s %d face(s) -> %d in the region"
          % (name, {"set": "set to", "add": "added", "remove": "removed"}[mode], len(faces), len(new)))
    if objs:
        print("  from object(s): %s" % ", ".join(objs))
    print("  Face numbers are NOT stable across a fuse. This list is valid for the model the atlas")
    print("  names (%s); re-take it after any apply." % (doc.get("model") or "UNRECORDED - set one"))
    return 0



def _read_facemap(path):
    """{object: {local face: original body face}} from a region map's facemap - the .json the map tools
    write, or the markdown table (`## <object>` then `F<local> =<original>` pairs)."""
    try:
        txt = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return {}
    if path.lower().endswith(".json"):
        try:
            d = json.loads(txt)
            return {o: {int(k): int(v) for k, v in m.items()} for o, m in d.items()}
        except Exception:
            return {}
    out, cur = {}, None
    for ln in txt.splitlines():
        m = re.match(r"^##\s+(\S+)", ln)
        if m:
            cur = m.group(1); out.setdefault(cur, {}); continue
        if cur:
            for k, v in re.findall(r"\bF(\d+)\s*=\s*(\d+)", ln):
                out[cur][int(k)] = int(v)
    return {o: m for o, m in out.items() if m}


def cmd_atlas_import(args, doc):
    """kit atlas import <regions.json> [--model <name>] [--replace]

    Bring a region set in from the tool that built it — a coloured review document, a splitter's
    manifest, anything that can emit the list. Each entry: `name`, `area`, `faces`, `box`,
    `mean_normal`, and the two statuses if it has them.

    **STATUSES DO NOT SURVIVE AN IMPORT UNCHALLENGED.** A definition that arrived at `CLIENT` from a
    file is accepted as `CLIENT` only if the file carries the words the client said; otherwise it lands
    at `RENDERED` at best. A status is a claim about who looked at something, and importing one is
    not looking at it.
    """
    a = _kv(args)
    src = a["_"][1] if len(a["_"]) > 1 else ""
    if not src or not os.path.exists(src):
        print(cmd_atlas_import.__doc__); return 2
    import json as _js
    try:
        rows = _js.load(open(src, encoding="utf-8"))
    except Exception as e:
        print("kit atlas import: %s is not readable JSON (%s)" % (src, e)); return 2
    if isinstance(rows, dict):
        rows = rows.get("regions") or list(rows.values())
    regs = doc.setdefault("regions", {})
    if a.get("--model"):
        doc["model"] = a["--model"]
    added = kept = downgraded = 0
    for r in rows:
        if not isinstance(r, dict) or not r.get("name"):
            continue
        name = r["name"]
        dfn = str(r.get("definition", "DRAFT")).upper().replace("CLIENT_OK", "CLIENT")
        if dfn == "CLIENT" and not r.get("client_said"):
            dfn = "RENDERED" if r.get("evidence") else "DRAFT"
            downgraded += 1
        if dfn not in G.ATLAS_DEF:
            dfn = "DRAFT"
        edt = str(r.get("edit", "OPEN")).upper()
        if edt not in G.ATLAS_EDIT:
            edt = "OPEN"
        if name in regs and "--replace" not in args:
            kept += 1
            continue
        regs[name] = {"what_it_is": r.get("what_it_is", r.get("label", "")),
                      "box": r.get("box"), "surface": r.get("surface", ""),
                      "mean_normal": r.get("mean_normal"),
                      "connectivity": r.get("connectivity", ""),
                      "area_limits": r.get("area_limits", ""),
                      "area": r.get("area"), "n_faces": r.get("faces"),
                      "faces": r.get("face_list", []),
                      "evidence": r.get("evidence", "imported from " + os.path.basename(src)),
                      "definition_status": dfn, "edit_status": edt,
                      "model": doc.get("model", ""), "when": G._now()}
        if r.get("client_said") or r.get("said"):
            regs[name]["client_said"] = r.get("client_said") or r.get("said")
        added += 1
    G.atlas_save(ROOT, doc)
    print("kit atlas import: %d region(s) from %s" % (added, os.path.basename(src)))
    if kept:
        print("  %d left alone because they already exist (--replace overwrites)" % kept)
    if downgraded:
        print("  %d arrived claiming definition CLIENT with no record of what the client SAID, and were" % downgraded)
        print("  NOT accepted at CLIENT. A status is a claim about who looked at something; importing one")
        print("  is not looking at it. Raise them with `kit atlas set <name> --definition CLIENT --said \"...\"`.")
    tot = sum(float(r.get("area") or 0) for r in regs.values())
    print("  total area over all regions: %.1f mm2" % tot)
    print("  **CHECK THIS AGAINST THE BODY'S OWN AREA.** A partition that does not conserve area has")
    print("  silently dropped surface, and counting FACES will not show it: every face can contribute")
    print("  a piece while 15 pct of the area goes nowhere.")
    return 0


def cmd_priorart(args):
    r"""kit priorart <job folder name>

    The scripts that already exist for a job folder, ranked: the one whose header carries the client's ruling
    first, then job_ before w_, version families collapsed - so the authoritative script is seen
    without reading the folder. `kit job <name> --type ...` prints the same when it CREATES a job;
    this is the verb for a folder that already exists (`jobs\BURRITO` holds over 250 scripts).
    the project FAILURES row 49: CLAUDE.md sent a session to `kit job <name>` for this and it was refused.
    Name the script you are applying, or say why not, before you write a new one.
    """
    if not args or args[0].startswith("-"):
        print(cmd_priorart.__doc__); return 2
    d = os.path.join(ROOT, "claude_code", "jobs", args[0])
    if not os.path.isdir(d):
        print("kit priorart: no such job folder %s" % d); return 2
    G.prior_art(ROOT, args[0])
    return 0


BURRITO_STEPS = [                    # HOW IT ACTUALLY RUNS
    ("s3",     "job_fields_dump.py",       "the probe -> fields_<tag>.npz. Read raw/bound: >25 %% is a block fill (L1)"),
    ("s3g",    "job_s3_sections.py",       "before/after section pictures - the client reviews these"),
    ("s4",     "job_mesh_burrito.py",      "the reference mesh -> piece_mesh.brep. NEVER carries an edit"),
    ("s5",     "job_features_burrito.py",  "the B-spline piece -> piece_features<tag>.brep"),
    ("audit",  "job_piece_audit.py",       "one table for N candidate pieces"),
    ("review", "job_compare_pics.py",      "THE REVIEW - orthos + orbit; open EVERY frame (L2)"),
    ("s7",     "job_s7_replace.py",        "cut the card prism, fuse the piece; job_gates.py refuses without a verdict"),
    ("s7r",    "job_s7_crop.py",           "crop before/after to the card so the orbit shows the SEAM"),
]


def cmd_burrito(args):
    """kit burrito <step | script.py> [--job NAME] [--env FILE] [--set KEY=VALUE ...] [--tag T] [--plan] [--bg]

    THE ORCHESTRATOR'S RUNNER FOR THE BURRITO CHAIN. the client, 2026-09-17: *"Workflow is claude code
    launched with Opus. It launches other agents but runs burrito itself. Make that happen and don't
    leave dangling paths."*

    WHY A SECOND RUNNER. The burrito is not a template job. It is a chain of project scripts
    (`BURRITO_STEPS` above), each run as its own freecadcmd process and driven by `LK_*`
    environment variables. `kit run` is the WORKER's runner: it refuses any script that is not a
    byte-copy of a template and any script that calls Mesh, B-spline fitting, section() or a fuzzy
    boolean - the worker rules of METHOD.md 4. The burrito chain does all of those on purpose, at
    orchestrator tier (EDIT_TYPES.md: no worker), so until 2026-09-17 it ran through the project's
    own `lk_spawn.py` and passed through NO kit gate: no lever check, no wall-clock budget, no
    FAIL: echo, and a driver that fanned out fifteen probes ran on the hook's 15-minute default.

    WHAT THIS DOES, in order, and it refuses only what cannot work:
      1. resolves the step to its script in the job folder (or takes any job_*.py path there);
      2. builds the environment: the job's settings file (--env, default WINNING_ENV.json), then
         every --set KEY=VALUE, then KIT_HOME. A --set naming a lever NO script in the folder reads
         is refused - a typo in a lever name is the silent-skip class one level up;
      3. requires LK_TAG (--tag): without it two runs overwrite each other's status, brep and
         log, and a comparison is never possible again;
      4. prints the levers THIS script reads and which are set vs running on a default (kit levers),
         and at s3 the burrito's card-time traps, because this is where the burrito's card is chosen;
      5. takes the budget from the project's living WALL_CLOCKS.md (1.5x typical), else the hook's
         snapshot, and runs BLOCKING with a cap of 2x that - a step past 2x its expectation is
         stuck, not working hard (L11), and a blocking run can never be left uncollected (L14);
      6. reads the OUTPUT for failure the way kit run does (freecadcmd exits 0 on a thrown script;
         a `FAIL:` line is a refusal), names the status file the step wrote, and flags a run over
         1.5x typical as the client's red flag.
    --plan prints all of it and runs nothing. --bg registers the step on the wall clock and runs it
    detached for the genuinely parallel case (a driver fanning out strips); collect it.
    """
    if not args or args[0] in ("-h", "--help"):
        print(cmd_burrito.__doc__)
        print("steps:")
        for k, scr, what in BURRITO_STEPS:
            print("  %-7s %-26s %s" % (k, scr, what))
        return 2
    plan = "--plan" in args
    job = _opt(args, "--job")
    jobs = os.path.join(ROOT, "claude_code", "jobs")
    if job:
        folder = os.path.join(jobs, job)
    else:
        cands = [os.path.join(jobs, d) for d in os.listdir(jobs)] if os.path.isdir(jobs) else []
        cands = [c for c in cands if os.path.isdir(c) and os.path.isfile(os.path.join(c, "WINNING_ENV.json"))]
        folder = max(cands, key=os.path.getmtime) if cands else None
    if not folder or not os.path.isdir(folder):
        sys.exit("kit burrito: no job folder. Name it: --job <name> (a folder under claude_code\\jobs\\ that holds the chain).")
    step = args[0]
    steps = {k: (scr, what) for k, scr, what in BURRITO_STEPS}
    if step in steps:
        script, what = steps[step]
    elif step.endswith(".py"):
        script, what = os.path.basename(step), "a script of this job folder"
    else:
        sys.exit("kit burrito: %r is not a step (%s) and not a .py script." % (step, ", ".join(k for k, _, _ in BURRITO_STEPS)))
    path = os.path.join(folder, script)
    if not os.path.isfile(path):
        sys.exit("kit burrito: %s is not in %s. The chain's scripts live in the job folder; nothing is copied."
                 % (script, folder))
    # recorded
    if script not in {scr for _, scr, _ in BURRITO_STEPS}:
        try:
            _src = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            _src = ""
        _m = re.search(r"(?<![\w.])(?!K\.|B\.|kitlib\.|kitlib_burrito\.)\w+\.fuse\s*\(", _src)
        if _m:
            sys.exit("kit burrito REFUSED: %s performs a raw fuse (%s) and is not the chain's S7.\n"
                     "  A script that fuses is a script that routes around the orbit gate. Piece-to-piece: use\n"
                     "  `B.union(pieces)` (kitlib_burrito - pairwise, checked, names the piece that will not join).\n"
                     "  Piece-into-body: the chain's s7 (`kit burrito s7`), which refuses without an orbit verdict.\n"
                     "  If you believe this refusal is wrong, that is a finding: kit failure ... Do not reword the script."
                     % (script, _m.group(0)[:40]))

    inherited = sorted(k for k in os.environ if k.startswith("LK_"))
    env = {k: v for k, v in os.environ.items() if not k.startswith("LK_")}
    env["KIT_HOME"] = HERE
    env["PYTHONUTF8"] = "1"; env["PYTHONIOENCODING"] = "utf-8"
    envfile = _opt(args, "--env") or (os.path.join(folder, "WINNING_ENV.json")
                                       if os.path.isfile(os.path.join(folder, "WINNING_ENV.json")) else None)
    from_file = {}
    if envfile:
        try:
            from_file = {k: str(v) for k, v in json.load(open(envfile, encoding="utf-8")).items()}
        except (OSError, ValueError) as e:
            sys.exit("kit burrito: cannot read %s (%s)" % (envfile, e))
        env.update(from_file)
    sets = {}
    for kv in _all(args, "--set"):
        if "=" not in kv:
            sys.exit("kit burrito: --set takes KEY=VALUE, not %r" % kv)
        k, v = kv.split("=", 1); sets[k.strip()] = v
    tag = _opt(args, "--tag") or sets.get("LK_TAG") or from_file.get("LK_TAG")
    if not tag:
        sys.exit("kit burrito: no LK_TAG. Give --tag <T>: it suffixes the status file, the brep and the log,\n"
                 "  so two runs never overwrite each other and a comparison is always possible (BURRITO_STEPS.md).")
    sets["LK_TAG"] = tag
    env.update(sets)

    rows, _ = G.levers(folder, "LK_", envfile)
    known = {r[0]: r for r in rows}
    unknown = [k for k in sets if k.startswith("LK_") and k not in known]
    if unknown:
        sys.exit("kit burrito: --set names a lever NO script in %s reads: %s.\n"
                 "  A lever nothing reads is a silent skip one level up. `kit levers %s` lists the %d that exist."
                 % (os.path.basename(folder), ", ".join(unknown), os.path.basename(folder), len(known)))
    mine = [r for r in rows if script in r[1]]
    print("kit burrito: %s -> %s   (%s)" % (step, script, what))
    print("  job     : %s" % folder)
    print("  settings: %s%s" % (envfile or "(none)", " + %d --set" % len(sets) if sets else ""))
    if envfile and os.path.basename(envfile).upper().startswith("WINNING"):
        print("  EXAMPLE CASE: %s reproduced ONE accepted piece. It is not the process and its numbers are not\n"
              "  this card's - every CARD lever is this card's decision (kit levers --check names them)."
              % os.path.basename(envfile))
    uncls, missing, has_census = G.census_check(folder, set(from_file) | set(sets), script)
    if has_census:
        if missing:
            sys.exit("kit burrito REFUSED: %s reads %d CARD lever(s) this run does not set: %s\n"
                     "  A CARD lever is a number the card decides. Set each one - in the run's env file or --set KEY=VALUE -\n"
                     "  or reclassify it in %s with a note saying why the default is right for every card."
                     % (script, len(missing), ", ".join(missing), G.LEVERS_CENSUS))
        if uncls:
            print("  census  : %d lever(s) this script reads are not yet classified in %s: %s"
                  % (len(uncls), G.LEVERS_CENSUS, ", ".join(uncls[:12]) + (" ..." if len(uncls) > 12 else "")))
    if step == "s7" and G.atlas_needs_assignment(ROOT) and not G.atlas_assignment(ROOT, tag):
        sys.exit("kit burrito REFUSED: S7 fuses new B-rep geometry and the atlas does not say which section it belongs to.\n"
                 "  kit atlas assign %s --to <existing region>\n"
                 "  kit atlas assign %s --new <name> --what \"<its physical definition>\"   (then announce it to the client)"
                 % (tag, tag))
    if step == "s3":
        _fine = G.fine_gate(folder, env, _all(args, "--fine"), tag)
        if _fine.get("refused"):
            sys.exit("kit burrito REFUSED (fine measurement): %s" % _fine["refused"])
        if _fine.get("announce"):
            print("  FINE    : ANNOUNCE THIS LINE IN THE CHAT BEFORE GOING ON (no reply is needed; the record is the point):")
            print("            " + _fine["announce"])
    print("  tag     : %s" % tag)
    if inherited:
        print("  dropped : %d LK_* from the shell, NOT passed to the step: %s" % (len(inherited), ", ".join(inherited[:10]) + (" ..." if len(inherited) > 10 else "")))
    try:
        # recorded
        _named = sorted(set(from_file) | set(sets))
        _rec = {"_step": step, "_script": script, "_when": time.strftime("%Y-%m-%d %H:%M:%S"), "_settings_file": envfile,
                "_sources": {k: ("--set" if k in sets else "file") for k in _named}}
        _rec.update({k: env[k] for k in _named if k in env})
        _seen = set(_rec)
        _rec["_inherited"] = _lever_env(env, folder, _seen)
        with open(os.path.join(folder, "env%s.json" % tag), "w", encoding="utf-8") as _fh:
            json.dump(_rec, _fh, indent=1)
        print("  env file: env%s.json (%d lever(s) set + %d inherited, and where each came from)"
              % (tag, len(_named), len(_rec.get("_inherited", {}))))
    except OSError as _e:
        print("  env file: NOT written (%s)" % _e)
    print("  levers this script reads: %d - %d set, %d on a hardcoded default%s"
          % (len(mine), sum(1 for r in mine if r[3] or r[0] in sets),
             sum(1 for r in mine if not (r[3] or r[0] in sets)),
             "" if mine else " (none found by name in the script; the folder's are listed by `kit levers`)"))
    for r in mine:
        src = "set " if (r[3] or r[0] in sets) else "    "
        print("    %s%-22s %s" % (src, r[0], ("= " + env.get(r[0], "")) if (r[3] or r[0] in sets) else ("default " + (r[2] or "-"))))
    foreign = [k for k in sets if k.startswith("LK_") and k in known and script not in known[k][1]]
    if foreign:
        print("  note: --set %s is read by other scripts in the folder, not by %s" % (", ".join(foreign), script))
    if step == "s3":
        print("  traps for the burrito card (kit card prints these for template types; the burrito's card is the env):")
        for t in G.TYPE_TRAPS.get("burrito", [])[:3]:
            print("    * " + t[:150])
    if step == "s5":
        _prev = os.path.join(folder, "status_features%s.json" % tag)
        if os.path.isfile(_prev) and not (env.get("LK_EDITS") or "").strip() and not (env.get("LK_MESH_OPS") or "").strip():
            print("  S6      : this is a RE-RUN of tag %s with NO rework edit (LK_EDITS and LK_MESH_OPS both empty).\n"
                  "            S3->S5 makes a CLOSE base shape; S6 - one local edit per defect, re-run, re-review -\n"
                  "            is where the shape is finished (L28). If the last build was wrong in one place, the\n"
                  "            next lever is --set LK_EDITS=... or --set LK_MESH_OPS=..., not another S5." % tag)

    W = _wallclock()
    budget_min, why = (W.budget_for(script, "Bash", ROOT) if W else (4.0, "no wall clock module"))
    cap = max(int(budget_min * 60 * 2), 60)
    print("  budget  : %.1f min (%s); cap %d s" % (budget_min, why, cap))
    if plan:
        print("  --plan: nothing was run.")
        return 0

    log = os.path.join(folder, "log_%s_%s.txt" % (os.path.splitext(script)[0], tag))
    # recorded
    try:
        import kit_crop as _KC
        _ext = None
        try:
            _ad = G.atlas_load(ROOT) or {}
            _bx = [r.get("box") for r in (_ad.get("regions") or {}).values() if r.get("box") and len(r["box"]) == 6]
            if _bx:
                _bx = [[float(v) for v in b] for b in _bx]
                _ext = ([min(b[0] for b in _bx), min(b[2] for b in _bx), min(b[4] for b in _bx)],
                        [max(b[1] for b in _bx), max(b[3] for b in _bx), max(b[5] for b in _bx)])
        except Exception:
            _ext = None
        _whole = []
        for _k, _v in env.items():
            if not (_k.startswith(LEVER_PREFIXES) and isinstance(_v, str) and _v.strip().lower().endswith(".stl")):
                continue
            if "OUT" in _k:
                continue
            _p = _v.strip() if os.path.isabs(_v.strip()) else os.path.join(folder, _v.strip())
            if not os.path.isfile(_p):
                continue
            _big, _bwhy = _KC.body_sized(_p, _ext)
            if _big:
                _whole.append((_k, os.path.basename(_p), _bwhy))
        _why = _opt(args, "--whole-body")
        if _whole and not _why:
            sys.exit("kit burrito REFUSED: %s is the WHOLE BODY (%s) and this step would process all of it.\n"
                     "  The mesh route's unit of work is a CROP: cut the box first and run every step on the crop -\n"
                     "    kit crop <body.stl> --box x0 x1 y0 y1 z0 z1 --margin 6 --out <job>\\<name>_crop.stl\n"
                     "  then --set %s=<name>_crop.stl, and `kit splice` puts the edited crop back (once, for every piece).\n"
                     "  If there is genuinely no other way, --whole-body \"<why>\" runs it and records the reason."
                     % (", ".join(k for k, _, _ in _whole), "; ".join("%s: %s" % (b, w) for _, b, w in _whole), _whole[0][0]))
        if _whole and _why:
            print("  WHOLE BODY: %s - run on the client's exception: %s" % (", ".join(k for k, _, _ in _whole), _why))
            try:
                _ef = os.path.join(folder, "env%s.json" % tag)
                _ej = json.load(open(_ef, encoding="utf-8")); _ej["_whole_body_because"] = _why
                json.dump(_ej, open(_ef, "w", encoding="utf-8"), indent=1)
            except (OSError, ValueError):
                pass
    except SystemExit:
        raise
    except Exception:
        pass
    if "--bg" in args:
        name = "%s_%s" % (step, tag)
        env.setdefault("PYTHONUNBUFFERED", "1")
        with open(log, "w", encoding="utf-8") as fh:
            flags = 0x08000000 if os.name == "nt" else 0
            pid = subprocess.Popen([freecad(), path], cwd=folder, env=env, stdout=fh,
                                   stderr=subprocess.STDOUT, creationflags=flags).pid
        if W:   # kit collected
            W.watch_add(ROOT, name, budget_min, "kit burrito %s (%s)" % (step, script),
                        owner=G.current_conversation(ROOT) or "", pid=pid)
        print("  started in the background, pid %d, log %s\n  ON THE CLOCK as %s - `kit collected %s` when it is read (L14); `--kill` ends it by pid."
              % (pid, log, name, name))
        return 0

    before = time.time()
    _outs = []
    for _k, _v in env.items():
        if _k.startswith(LEVER_PREFIXES) and "OUT" in _k and isinstance(_v, str) \
                and re.search(r"\.(stl|brep|npz|json|fcstd|step|stp|obj|ply|png)$", _v.strip(), re.I):
            _outs.append(_v.strip() if os.path.isabs(_v.strip()) else os.path.join(folder, _v.strip()))
    rc, out = sh([freecad(), path], cap, log, env, cwd=folder, outputs=_outs)
    took = time.time() - before
    rc = _judge_output(out, rc, log, "kit burrito")
    newest = None
    try:
        cands = [f for f in os.listdir(folder) if f.startswith("status") and f.endswith(".json")
                 and tag in f and os.path.getmtime(os.path.join(folder, f)) >= before]
        newest = max(cands, key=lambda f: os.path.getmtime(os.path.join(folder, f))) if cands else None
        if rc == KILLED_RC and newest:
            os.replace(os.path.join(folder, newest), os.path.join(folder, newest + ".KILLED"))
            print("  status  : %s was written by the killed step - renamed %s.KILLED, not a result" % (newest, newest))
            newest = None
    except OSError:
        pass
    typical = (W.table_budgets(ROOT).get(script) if W else None)
    flag = ""
    if typical and took > 1.5 * typical:
        flag = "   RED FLAG - %.1fx the typical %.0f s (the client: 1.5x needs evaluating)" % (took / typical, typical)
    print("kit burrito: rc %s, %.0f s%s, log %s" % (rc, took, flag, log))
    print("  status  : %s" % (newest or "no status file written by this step - wait on its artefact, never on a status name"))
    try:
        if W and hasattr(W, "state_behind"):
            n_new, sfolder, has_state = W.state_behind(ROOT)
            if n_new >= getattr(W, "STATE_EVERY", 25):
                print("  STATE   : %d new artefacts in %s since %s - write claude_code\\STATE_NOW.md now (the tag key first,"
                      % (n_new, os.path.basename(sfolder), "STATE_NOW.md was written" if has_state else "the session opened"))
                print("            then the build, the live lead, what is settled, the next actions), then carry on.")
    except Exception:
        pass
    # kit accept  MEASUREMENTS.md
    # kit accept
    try:
        G.ledger_behind(ROOT, os.path.basename(folder))
    except Exception:
        pass
    return rc


TOOLS_DIR = os.path.join(os.path.dirname(HERE), "tools")


def _md5(path):
    import hashlib
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve_project_path(p):
    """31bv (the tester TB1's F4): A RELATIVE PATH IS TRIED AGAINST THE CWD, THEN THE PROJECT ROOT, THEN claude_code\\ - the pages write paths from the project root
    (`claude_code\\bank\\<brep>`) and every kit command runs from claude_code\\ (PROJECT_LAYOUT), so `kit promote claude_code\\bank\\x.brep` run from claude_code\\ had read
    'no such file' while `kit newjob --from` resolved the same spelling against the root. The first spelling that is a FILE wins; an absolute path, or one that
    resolves nowhere, comes back as given (made absolute) so the caller's own refusal names it."""
    p = str(p or "").strip()
    if not p:
        return ""
    if os.path.isabs(p):
        return p
    for cand in (os.path.abspath(p), os.path.join(ROOT, p), os.path.join(ROOT, "claude_code", p)):
        if os.path.isfile(cand):
            return cand
    return os.path.abspath(p)


def _model_of_record():
    """the session's model of record, or the newest .brep in claude_code\\bank, or ''."""
    try:
        m = (G.session(ROOT) or {}).get("model_of_record")
        if m and os.path.isfile(m):
            return m
    except Exception:
        pass
    bank = os.path.join(ROOT, "claude_code", "bank")
    try:
        c = [os.path.join(bank, f) for f in os.listdir(bank) if f.lower().endswith(".brep")]
        return max(c, key=os.path.getmtime) if c else ""
    except OSError:
        return ""


def _newest_rev():
    d = os.path.join(ROOT, "Deliverables")
    try:
        revs = [f for f in os.listdir(d) if re.fullmatch(r"R\d+", f)]
        return max(revs, key=lambda r: int(r[1:])) if revs else "R1"
    except OSError:
        return "R1"


def _atlas_render(args, doc, regs):
    r"""kit atlas render [--model <brep>] [--rev R32] [--out <file.FCStd>] [--plan]
    kit atlas recipe --split <regions.json> --features <features.json> --template <gui-saved.FCStd> [--moves <moves.json>]

    THE ATLAS IS MAINTAINED ON THE LATEST BREP, AT ALL TIMES (the client, 2026-09-24). This regenerates the coloured
    region map on the model of record with the recipe that produced the approved one - the split spec, the
    feature regrouping and the client's moves - through the three kit instruments (atlas_split ->
    atlas_features -> atlas_colour), and records the model's md5 the map was made on. `kit promote` runs it;
    `kit deliver` refuses while the map is behind the bank. A recipe is recorded ONCE (`kit atlas recipe`).
    The face numbers a spec names may not carry across a revision; the run says which regions use them.
    """
    rec = doc.get("recipe") or {}
    template = rec.get("template", "")
    if template and not os.path.isabs(template):
        template = os.path.join(ROOT, template)
    if not template or not os.path.isfile(template):
        print("kit atlas render: no GUI-saved template recorded (the colour step copies a view-provider block from one).\n"
              "  kit atlas recipe --template <a GUI-saved .FCStd>   (the approved map itself, or the last delivery)")
        return 2
    model = _opt(args, "--model", "") or _model_of_record()
    if not model or not os.path.isfile(model):
        print("kit atlas render: no model of record found (--model <brep>, or open the session)."); return 2
    rev = _opt(args, "--rev", "") or _newest_rev()
    out = _opt(args, "--out", "") or os.path.join(ROOT, "Deliverables", rev, "model", "%s_REGION_MAP.FCStd" % rev)
    jobdir = os.path.join(ROOT, "claude_code", "jobs", "ATLAS"); os.makedirs(jobdir, exist_ok=True)
    plan = "--plan" in args
    if "--recipe" in args:
        if not rec.get("split") or not rec.get("features"):
            print("kit atlas render --recipe: no split/features recorded (kit atlas recipe --split ... --features ...)."); return 2
        split_dir = os.path.join(jobdir, "split"); os.makedirs(split_dir, exist_ok=True)
        feat_dir = os.path.join(jobdir, "features"); os.makedirs(feat_dir, exist_ok=True)
        for k in ("split", "features", "moves"):
            p = rec.get(k)
            if p and not os.path.isabs(p):
                p = os.path.join(ROOT, p)
            if p and not os.path.isfile(p):
                print("kit atlas render: the recipe's %s is missing: %s" % (k, p)); return 2
            if p:
                rec[k] = p
        try:
            spec = json.load(open(rec["split"], encoding="utf-8"))
            uses_faces = [n for n, r in spec.items() if r.get("faces")]
            if uses_faces:
                print("kit atlas render: NOTE - %d region(s) in the split spec are defined by FACE NUMBERS (%s). Face numbers"
                      " may not carry across a revision; check those regions in the rendered map." % (len(uses_faces), ", ".join(uses_faces[:6])))
        except (OSError, ValueError):
            pass
        steps = [
            ("atlas_split", ["--set", "ATLAS_SHAPE=%s" % model, "--set", "ATLAS_REGIONS=%s" % rec["split"],
                             "--set", "ATLAS_OUTDIR=%s" % split_dir]),
            ("atlas_features", ["--set", "ATLAS_SPLIT=%s" % split_dir, "--set", "ATLAS_FEATURES=%s" % rec["features"],
                                "--set", "ATLAS_OUTDIR=%s" % feat_dir] + (["--set", "ATLAS_MOVES=%s" % rec["moves"]] if rec.get("moves") else [])),
        ]
        man_dir = feat_dir
    else:
        tr_dir = os.path.join(jobdir, "transfer"); os.makedirs(tr_dir, exist_ok=True)
        atlas_json = os.path.join(ROOT, "claude_code", G.ATLAS_FILE)
        steps = [("atlas_transfer", ["--set", "ATLAS_SHAPE=%s" % model, "--set", "ATLAS_JSON=%s" % atlas_json,
                                     "--set", "ATLAS_OUTDIR=%s" % tr_dir])]
        man_dir = tr_dir
    steps.append(("atlas_colour", ["--set", "ATLAS_MANIFEST=%s" % os.path.join(man_dir, "manifest.json"),
                                   "--set", "ATLAS_REGIONS=%s" % os.path.join(man_dir, "regions.json"),
                                   "--set", "ATLAS_TEMPLATE=%s" % template, "--set", "ATLAS_OUT=%s" % out]))
    print("kit atlas render: model %s\n  map -> %s" % (model, out))
    for nm, sets in steps:
        print("  step %s" % nm)
        rc = cmd_tool([nm, "--job", "ATLAS", "--tag", "map"] + sets + (["--plan"] if plan else []))
        if rc:
            print("kit atlas render FAILED at %s (rc %s). The atlas is NOT rendered on this model; the old map stands and\n"
                  "  `kit deliver` will say so." % (nm, rc))
            return rc or 2
    if plan:
        print("  --plan: nothing was run."); return 0
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rep = {}
    try:
        rep = json.load(open(os.path.join(man_dir, "transfer.json"), encoding="utf-8"))
    except (OSError, ValueError):
        pass
    doc["rendered"] = {"model": model, "md5": _md5(model), "out": out, "when": G._now(), "rev": rev,
                       "new_faces": rep.get("new_faces", []), "mixed": len(rep.get("mixed", []))}
    doc["model"] = os.path.basename(out)
    G.atlas_save(ROOT, doc)
    if rep.get("new_faces"):
        print("kit atlas render: %d face(s) are NEW SURFACE (no approved region has them) - they are in the map as `_NEW_SURFACE`;\n"
              "  assign them: kit atlas assign <job> --to <region> | --new <name> --what \"...\"" % len(rep["new_faces"]))
    print("kit atlas render: DONE - %s on %s (md5 %s). Check it: kit deliverycheck \"%s\"" % (out, os.path.basename(model), doc["rendered"]["md5"][:8], out))
    return 0


def atlas_behind(doc):
    """(behind?, message): is the coloured map older than the model of record?"""
    if not doc:
        return False, "no atlas"
    model = _model_of_record()
    if not model:
        return False, "no model of record"
    r = doc.get("rendered") or {}
    if not r.get("md5"):
        return True, "the atlas has never been rendered by the kit on a model of record (kit atlas render)"
    try:
        cur = _md5(model)
    except OSError:
        return False, "model unreadable"
    if cur != r["md5"]:
        return True, ("the atlas map %s was made on %s (md5 %s); the model of record is now %s (md5 %s) - kit atlas render"
                      % (os.path.basename(r.get("out", "?")), os.path.basename(r.get("model", "?")), r["md5"][:8],
                         os.path.basename(model), cur[:8]))
    return False, "the atlas map matches the model of record (md5 %s)" % cur[:8]


def _tool_head(path, n=None):
    """the instrument's comment header - its own documentation"""
    out = []
    try:
        for l in open(path, encoding="utf-8", errors="replace"):
            if not l.startswith("#"):
                break
            out.append(l[2:].rstrip() if l.startswith("# ") else l[1:].rstrip())
            if n and len(out) >= n:
                break
    except OSError:
        pass
    return out


def cmd_tool(args):
    r"""kit tool                                           list the instruments
    kit tool <name> --help                              what it answers and what it reads
    kit tool <name> --job <JOB> [--set KEY=VALUE ...] [--tag T] [--plan]

    AN INSTRUMENT IS NOT A JOB STEP. the agent's diagnosis, 2026-09-22: eight instruments written to answer one
    question - what is each unmatched loop, a true section through body and patch, does the field call
    air solid - lived in jobs\BURRITO\, the burrito's own folder, runnable only as "a script of
    this job folder" and findable only by the agent that wrote them. They are the kit's now, in ONE
    place (LEAN_KIT\tools\), and each run's output lands in the job whose question it answers.

    Runs the instrument under freecadcmd with the job folder as its working directory; the shell's
    LK_* levers are dropped, KIT_HOME is set, CC_OUTDIR defaults to the job folder, and a --set the
    instrument never reads is refused (a typo is a silent skip). A raw fuse is refused outright: an
    instrument measures, it never edits. The run's environment is written to env_tool_<name>_<TAG>.json
    and its log to log_tool_<name>_<TAG>.txt, in the job folder. Budget from WALL_CLOCKS.md, cap 2x.
    """
    names = sorted(f[:-3] for f in os.listdir(TOOLS_DIR) if f.endswith(".py")) if os.path.isdir(TOOLS_DIR) else []
    if args and args[0] in ("--help", "-h"):
        print(cmd_tool.__doc__); return 0
    if not args or args[0] in ("--list", "-l"):
        print("kit tool: %d instrument(s) in %s" % (len(names), TOOLS_DIR))
        for nm in names:
            h = _tool_head(os.path.join(TOOLS_DIR, nm + ".py"), 1)
            print("  %-18s %s" % (nm, (h[0].split(" - ", 1)[-1] if h else "")[:100]))
        print("  kit tool <name> --help  for what one reads.")
        return 0
    nm = os.path.basename(args[0])
    nm = nm[:-3] if nm.endswith(".py") else nm
    nm = nm.lstrip("_")
    path = os.path.join(TOOLS_DIR, nm + ".py")
    if not os.path.isfile(path):
        print("kit tool: no instrument %r. There are: %s" % (nm, ", ".join(names) or "(none)")); return 2
    if "--help" in args or "-h" in args:
        print("\n".join(_tool_head(path))); return 0
    src = open(path, encoding="utf-8", errors="replace").read()
    if re.search(r"(?<![\w.])\w+\.fuse\s*\(", src):
        print("kit tool REFUSED: %s fuses. An instrument measures; a script that edits is a job step." % nm)
        return 2
    job = _opt(args, "--job")
    if not job:
        print("kit tool: name the job whose question this answers - --job <name> (a folder under claude_code\\jobs\\).")
        print("  Its output lands there, beside the work it is evidence for.")
        return 2
    folder = os.path.join(ROOT, "claude_code", "jobs", job)
    if not os.path.isdir(folder):
        print("kit tool: no job folder %s. `kit newjob` makes one; an instrument does not." % folder); return 2
    env = {k: v for k, v in os.environ.items() if not k.startswith("LK_")}
    env["KIT_HOME"] = HERE
    env["PYTHONUTF8"] = "1"; env["PYTHONIOENCODING"] = "utf-8"
    env["KIT_CALLER_CWD"] = os.getcwd()
    sets = {}
    for kv in _all(args, "--set"):
        if "=" not in kv:
            print("kit tool: --set takes KEY=VALUE, not %r" % kv); return 2
        k, v = kv.split("=", 1); sets[k.strip()] = v
    unread = [k for k in sets if k not in src]
    if unread:
        print("kit tool REFUSED: %s never reads %s. A lever nothing reads is a silent skip." % (nm, ", ".join(unread)))
        return 2
    if "CC_OUTDIR" in src and "CC_OUTDIR" not in sets:
        sets["CC_OUTDIR"] = folder
    env.update(sets)
    tag = _opt(args, "--tag") or time.strftime("%H%M%S")
    print("kit tool: %s  (job %s, tag %s)" % (nm, job, tag))
    for k in sorted(sets):
        print("  set %-16s = %s" % (k, sets[k]))
    W = _wallclock()
    budget_min, why = (W.budget_for(nm + ".py", "Bash", ROOT) if W else (4.0, "no wall clock module"))
    cap = max(int(budget_min * 60 * 2), 60)
    print("  budget  : %.1f min (%s); cap %d s" % (budget_min, why, cap))
    try:
        with open(os.path.join(folder, "env_tool_%s_%s.json" % (nm, tag)), "w", encoding="utf-8") as fh:
            json.dump({"_tool": nm, "_when": time.strftime("%Y-%m-%d %H:%M:%S"), **sets}, fh, indent=1)
    except OSError as e:
        print("  env file: NOT written (%s)" % e)
    if "--plan" in args:
        print("  --plan: nothing was run."); return 0
    log = os.path.join(folder, "log_tool_%s_%s.txt" % (nm, tag))
    t0 = time.time()
    rc, out = sh([freecad(), path], cap, log, env, cwd=folder)
    rc = _judge_output(out, rc, log, "kit tool")
    print("kit tool: rc %s, %.0f s, log %s" % (rc, time.time() - t0, log))
    return rc


def cmd_stop(args):
    r"""kit stop --why "<the client's instruction to stop, or the blocker in one sentence>" [--until <bg-ids,...>|tasks]

    Records a REASONED stop. The Stop hook (`hooks\stop_guard.py`) refuses to let the orchestrator
    end its turn while work is on the books - an open job, a task on the clock, an unclosed session,
    unread inbox text - and this is the one honest way past it that is not finishing the work. The
    reason is appended to the inbox, so the client reads why the work stopped in the agent's own words, and
    the hook honours it once. the client, 2026-09-17: continue working while there is work left and no stop
    has been approved; no clock, no scheduled task.
    """
    why = (_opt(args, "--why") or "").strip()
    if len(why) < 30:
        print("kit stop REFUSED: --why needs a real reason (30+ characters) - the client's instruction to stop, quoted,\n"
              "  or the blocker in one sentence. A stop with no reason is what the guard exists to prevent.")
        return 2
    until = (_opt(args, "--until") or "").strip()
    rec = {"why": why, "when": G._now()}
    if until:
        rec["until"] = "tasks" if until.lower() == "tasks" else [t.strip() for t in until.split(",") if t.strip()]
    G._write(ROOT, "STOP_OK.json", rec)
    try:
        G.inbox_append(ROOT, "STOP RECORDED - " + why + ((" (holds while %s run)" % until) if until else ""), who="THE ORCHESTRATOR")
    except Exception:
        pass
    print("kit stop: recorded. %s; the reason is in the inbox for the client."
          % ("Every stop is allowed while the named tasks are on the clock" if until else "The next stop is allowed once"))
    try:
        sys.path.insert(0, os.path.join(KIT_MASTER, "hooks"))
        import wallclock as _W
        left = [n for n, _m, _e, _o, _w in _W.watch_open(ROOT)]
        if left:
            print("  still on the clock, and still yours to collect or kill: %s" % ", ".join(left))
    except Exception:
        pass
    return 0


def cmd_templates(args):
    """kit templates            every worker copy in this project, and whether its body still matches a template

    WHY. `kit run` refuses a worker script whose body differs from every template - the rule that
    keeps a haiku worker to filling PARAMS. The other edge of that rule: **editing a template's body
    orphans every worker copy on disk, silently, until each one is next run.** On 2026-09-16 a
    seven-line comment added ABOVE the PARAMS block of `t_burrito.py` - by the maintenance pass, in
    the act of writing that it was leaving the burrito alone - would have refused all 63 burrito
    worker scripts in the live round at their next `kit run`. Caught by checking, not by luck.

    So: run this BEFORE and AFTER touching a template body. A comment that has to live in a
    template goes INSIDE the PARAMS block, which the body-match ignores.
    """
    tdir = os.path.join(HERE, "templates")
    bodies = {}
    for t in sorted(os.listdir(tdir)):
        if t.startswith("t_") and t.endswith(".py"):
            bodies[t] = _body(open(os.path.join(tdir, t), encoding="utf-8", errors="replace").read())
    jobs = os.path.join(ROOT, "claude_code")
    rows, orphans = [], 0
    for dp, dn, fn in os.walk(jobs):
        if any(x in dp for x in ("_archive", "_replaced_by", "_kit_before", "__pycache__")):
            continue
        for f in sorted(fn):
            if not (f.startswith("w_") and f.endswith(".py")):
                continue
            p = os.path.join(dp, f)
            try:
                w = _body(open(p, encoding="utf-8", errors="replace").read())
            except OSError:
                continue
            hit = next((t for t, b in bodies.items() if b == w), None)
            if not hit:
                orphans += 1
            rows.append((os.path.relpath(p, jobs), hit or "NO TEMPLATE MATCHES"))
    if not rows:
        print("kit templates: no worker copies (w_*.py) under claude_code"); return 0
    for rel, hit in rows:
        if "--orphans" in args and hit != "NO TEMPLATE MATCHES":
            continue
        print("  %-64s %s" % (rel, hit))
    print("\nkit templates: %d worker copies, %d orphaned" % (len(rows), orphans))
    if orphans:
        print("  An orphan is refused at its next `kit run`. If the TEMPLATE changed, take a fresh copy with\n"
              "  `kit howto <type>` and move the PARAMS block across; if the WORKER changed the body, that is\n"
              "  the C3 deviation and the refusal is correct.")
    return 1 if orphans else 0


# removeSplitter
TEMPLATE_CALL_OK = {"t_cutter": (r"\bremoveSplitter\b",)}
# kit rebuild
SHELVED_TEMPLATES = {"t_burrito": "the first voxel burrito (2026-09-10, kitlib_burrito) - SHELVED by the client 2026-11-03; the live route is `kit rebuild` (THE SKIN ROUTE, the burrito card: Template none)"}


def _template_of(src, base):
    """(the template name a script is an unmodified copy of - PARAMS aside -, {template: body} for the hint), or (None, bodies); a _kit_ script is the kit's own"""
    if base.startswith("_kit_"):
        return "_kit_", {}
    tdir = os.path.join(HERE, "templates")
    if not os.path.isdir(tdir):
        return None, {}
    want = _body(src); bodies = {}
    for t in sorted(os.listdir(tdir)):
        if t.startswith("t_") and t.endswith(".py"):
            try:
                bodies[t] = _body(open(os.path.join(tdir, t), encoding="utf-8", errors="replace").read())
            except OSError:
                continue
            if bodies[t] == want:
                return t[:-3], bodies
    return None, bodies


def scan(script):
    src = open(script, encoding="utf-8", errors="replace").read()
    base = os.path.basename(script)
    tmpl, bodies = _template_of(src, base)
    if tmpl in SHELVED_TEMPLATES and not os.environ.get("SHELVED_OK", "").strip():
        sys.exit("kit run REFUSED: %s is a copy of %s.py - %s. SHELVED_OK=\"<why>\" in the environment runs it on the client's word - say their words in your message (31bs T6 F5: nothing logs it)." % (base, tmpl, SHELVED_TEMPLATES[tmpl]))
    for rx, why in FORBIDDEN:
        for m in re.finditer(rx, src):
            if tmpl and any(re.fullmatch(ok_, m.group(0)) for ok_ in TEMPLATE_CALL_OK.get(tmpl, ())):
                continue
            sys.exit("kit run REFUSED: '%s' in %s - %s" % (m.group(0), base, why))
    if re.search(r"\bmakeFillet\b|\bmakeChamfer\b", src) and WORKER_FILLET_OK not in src:
        sys.exit("kit run REFUSED: makeFillet/makeChamfer outside the edge_round template (EDIT_TYPES.md edge_round)")

    # METHOD.md
    # METHOD.md
    # does not exist
    if tmpl is not None:
        return
    if not os.path.isdir(os.path.join(HERE, "templates")):
        return
    want = _body(src)
    import difflib
    hint = ""
    if bodies:
        best = max(bodies, key=lambda t: difflib.SequenceMatcher(None, bodies[t], want).ratio())
        diff = [l for l in difflib.unified_diff(bodies[best].splitlines(), want.splitlines(), "template " + best, base, lineterm="", n=0)
                if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))][:8]
        hint = ("\n  Closest template: %s. First differences outside PARAMS (- template, + your script):\n    %s\n"
                "  If the TEMPLATE changed since your copy (a kit update), take a fresh copy and move your\n"
                "  PARAMS block into it." % (best, "\n    ".join(diff) if diff else "(same lines, different bytes: line endings or whitespace)"))
    sys.exit(
        "kit run REFUSED: %s is not an unmodified copy of an edit-type template.\n"
        "  A worker fills the PARAMS block and changes NOTHING else - that is the whole contract,\n"
        "  and it is what makes a haiku worker safe (METHOD.md 9; worker C3 hand-wrote a script\n"
        "  from the howto printout and this refusal is the fix).\n"
        "  Get a clean copy:  kit howto <edit_type>\n"
        "  If the template genuinely cannot express your card, do NOT edit it: write the question\n"
        "  in RESULT.md and stop. That is the correct move and it is cheap.%s" % (base, hint))

def cmd_run(args, internal=False):
    preflight(); script = args[0]
    if not os.path.exists(script): sys.exit("kit run: no such script " + script)
    scan(script)
    cap = int(os.environ.get("KIT_TIMEOUT", ENV["timeout_s"]))
    if os.path.splitext(os.path.basename(script))[0] in ("_kit_check", "_kit_dossier") and "KIT_TIMEOUT" not in os.environ:
        cap = int(ENV.get("timeout_check_s", 900))
    log = os.path.join(os.path.dirname(os.path.abspath(script)), "kit_run.log")
    env = dict(os.environ); env["KIT_HOME"] = HERE
    env["PYTHONUTF8"] = "1"; env["PYTHONIOENCODING"] = "utf-8"
    # kit measure
    t = time.time(); rc, out = sh([freecad(), os.path.abspath(script)] + args[1:], cap, log, env, cwd=(None if internal else os.path.dirname(os.path.abspath(script))))
    rc = _judge_output(out, rc, log, "kit run")
    if not internal and "BOOKKEEPING" not in out and rc == 0:
        print("kit run: WARNING - no BOOKKEEPING line was printed; the script did not complete a boolean step.")
    print("kit run%s: rc %s, %.0f s, log %s" % (" (the kit's own macro - the command's verdict follows; 31bs T8 F9b)" if internal else "", rc, time.time() - t, log)); return rc

def _judge_output(out, rc, log, who):
    """The exit code is NOT evidence under freecadcmd; the OUTPUT is. ONE reader for `kit run` and
    `kit burrito`, so the two runners cannot disagree about what a failure looks like."""
    bad = [m for m in ("Exception while processing file", "Traceback (most recent call last)")
           if m in out]
    if bad and rc == 0:
        rc = 3
        print("%s: THE SCRIPT FAILED although the interpreter exited 0 - %s.\n"
              "  freecadcmd does not propagate a script exception, so the exit code is not "
              "evidence here.\n  The reason is in the log: %s" % (who, bad[0], log))
    for _l in out.splitlines():
        if _l.startswith("FAIL:"):
            print("%s: the script REFUSED - %s" % (who, _l[5:].strip())); rc = rc or 1
    return rc


def _fc(code, workdir, name):
    _wd = os.path.abspath(workdir)
    _jobs = os.path.abspath(os.path.join(ROOT, "claude_code", "jobs"))
    _doss = os.path.abspath(os.path.join(ROOT, "claude_code", "dossier"))
    if not (_wd.startswith(_jobs + os.sep) or _wd.startswith(_doss + os.sep)):
        workdir = os.path.join(G.store(ROOT), "scratch"); os.makedirs(workdir, exist_ok=True)
    tmp = os.path.join(workdir, "_kit_%s.FCMacro" % name)
    with open(tmp, "w", encoding="utf-8") as _fh:
        _fh.write(code)
    _FC_LAST["log"] = os.path.join(workdir, "kit_run.log"); _FC_LAST["macro"] = tmp
    return cmd_run([tmp], internal=True)


_FC_LAST = {}      # kit measure

def cmd_render(args):
    whole_flag = "--whole" in args; args = [t for t in args if t != "--whole"]
    a = _kv(args)
    if not a["_"] or not a.get("--out"):
        print("kit render <shape.brep|mesh.stl> --out <dir> [--box x0 x1 y0 y1 z0 z1] [--views std|all] "
              "[--name <prefix>] [--job <name>] [--faces 1,2,3] [--light grazing] [--whole]")
        return 2
    shape = a["_"][0]; out = a["--out"]; os.makedirs(out, exist_ok=True)
    bx = a.get("--box"); name = a.get("--name", "look"); views = a.get("--views", "std")
    # recorded
    if not bx and a.get("--job"):
        try:
            _jb = G.job(ROOT, a["--job"]) or {}
            if _jb.get("box"):
                bx = str(_jb["box"])
                print("[leangate] render: using job %s's recorded box (%s)" % (a["--job"], bx))
        except Exception:
            pass
    hl = None
    if a.get("--faces"):
        hl = sorted(set(int(t) for t in re.split(r"[,\s]+", str(a["--faces"]).strip()) if t))
    lt = a.get("--light")
    if lt is not None and lt not in ("std", "grazing"):
        sys.exit("kit render: --light is std or grazing")
    code = ("import sys; sys.path.insert(0, %r); import kitlib as K\n"
            "s = K.load(%r); bx = %r; bx3 = None if bx is None else tuple((bx[i], bx[i+1]) for i in (0,2,4))\n"
            "paths = K.look(s, %r, %r, focus_box=bx3, views=%r, highlight=%r, light=%r, whole=%r)\n"
            "print('RENDER wrote %%d pictures:' %% len(paths)); [print('   ', p) for p in paths]\n") % (HERE, shape, None if bx is None else list(map(float, bx.split())), out, name, views, hl, None if lt in (None, "std") else lt, bool(bx is None or whole_flag))
    rc = _fc(code, out, "render")
    jb = a.get("--job")
    if rc == 0 and jb:
        stamp_codes(out, jb, name, boxed=bool(bx))
    return rc


def stamp_codes(out_dir, job, prefix, boxed=None):
    """Burn a random code into each frame's header band; record only its salted hash.

    The plaintext lives in exactly one place — the pixels. That is what makes `kit look` able to
    tell an opened picture from a plausible sentence about one. See leangate's PROOF OF OPENING
    note for why a specificity check alone cannot do it.

    Also records whether a frame is essentially EMPTY. A view whose subject is out of frame draws
    almost nothing, and no amount of honest reading can extract a finding from it — so that is
    measured here, off the pixels, rather than left to the reader to notice.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as _np
    except Exception as exc:
        print("*** PROOF-OF-OPENING FAILED *** could not stamp codes: %s\n"
              "  `kit beforelook` / `kit look` will REFUSE until the frames carry codes. One line:\n"
              "      & \"%s\" -m pip install pillow\n"
              "  then re-run this render." % (exc, sys.executable))
        return False
    pics = sorted(os.path.join(out_dir, f) for f in os.listdir(out_dir)
                  if f.lower().endswith(".png") and f.startswith(prefix))
    if not pics:
        return
    salt = os.urandom(8).hex()
    items = []
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 34)
    except Exception:
        font = ImageFont.load_default()
    for p in pics:
        c = G.new_code()
        im = Image.open(p).convert("RGB")
        w, _h = im.size
        dr = ImageDraw.Draw(im)
        band = 46
        new = Image.new("RGB", (w, im.size[1] + band), (0, 0, 0))
        new.paste(im, (0, band))
        dr = ImageDraw.Draw(new)
        dr.rectangle([0, 0, w, band], fill=(0, 0, 0))
        dr.text((10, 4), "LOOK CODE  %s" % " ".join(c), fill=(255, 235, 60), font=font)
        new.save(p)
        arr = _np.asarray(Image.open(p).convert("RGB"))[band:]
        bg = _np.array([33, 36, 43])
        blank = bool((_np.abs(arr.astype(int) - bg).sum(-1) < 24).mean() > 0.985)
        items.append({"image": p, "hash": G._kdf(c, salt), "blank": blank, "boxed": boxed})
        del c
    G.codes_record(ROOT, job, items, salt)
    n_blank = sum(1 for it in items if it["blank"])
    print("[leangate] %d frame(s) stamped with a LOOK CODE for job %s%s."
          % (len(items), job, (" — %d look EMPTY" % n_blank) if n_blank else ""))
    print("[leangate]   Open them, read the code in the top band, and pass at least %d back:"
          % G.MIN_CODES)
    if str(job).endswith("::before"):
        print("[leangate]     kit beforelook %s --saw %s=<CODE> --saw ... --says \"...\"" % (str(job)[:-8], os.path.basename(items[0]["image"])))
    else:
        print("[leangate]     kit look %s --code %s=<CODE> --code ... --says \"...\""
              % (job, os.path.basename(items[0]["image"])))
    return True

BOX_SLACK = 25.0


def gate_box_size(allbox, job, waived):
    """Refuse a permitted-change box that exempts far more material than the feature can explain.

    the client asked whether the one-box problem should be fixed with prose or a gate. Prose cannot do
    it: the box looks reasonable while you are typing it, and the consequence — material silently
    exempted from the "nothing changed outside" test — is invisible in the output. Nothing in the
    result says how much you licensed yourself to change.

    So it is arithmetic. The card already states the expected volume change; the box has a
    volume. If the box is more than BOX_SLACK times the change it is meant to contain, it is
    exempting material the feature cannot account for, and the honest fix is one box per feature
    rather than one box spanning them. That is exactly the bolt-pair case a test orchestrator
    hit: two 6.6 bores needing 1,232 mm3, inside a box of 31,000.

    Overridable with --wide-box "<why>", because a genuinely large feature exists. What is
    refused is doing it silently.
    """
    if not job:
        return
    j = G.job(ROOT, job) or {}
    exp = j.get("expect_vol")
    if exp is None:
        return
    vol = sum(abs((b[1] - b[0]) * (b[3] - b[2]) * (b[5] - b[4])) for b in allbox)
    if abs(exp) < 1e-9 or vol <= BOX_SLACK * abs(exp):
        return
    if str(waived or "").strip():
        print("[leangate] wide box accepted on your word: %s" % waived)
        return
    ratio = vol / abs(exp)
    print("\n" + "=" * 78)
    print("CHECK REFUSED - the permitted-change box is %.0fx the change it should contain."
          % ratio)
    print("=" * 78)
    print("  box volume        %.0f mm3   (%d box%s)" % (vol, len(allbox),
                                                         "" if len(allbox) == 1 else "es"))
    print("  card expects      %.0f mm3" % exp)
    print("")
    print("  THE BOX IS THE PERMITTED-CHANGE REGION, NOT THE INSPECTED ONE. Everything inside it")
    print("  is exempt from the 'nothing changed outside' test, so a bigger box does not inspect")
    print("  more - it CHECKS LESS, and nothing in the result says so.")
    print("")
    print("  If this is two features far apart, give one box EACH - --box may be repeated, and")
    print("  the material between them is then inspected instead of exempted:")
    print("      kit check ... --box <feature 1> --box <feature 2> --job %s" % job)
    print("  If the feature really is this big, say so and it is on the record:")
    print("      --wide-box \"<why the feature spans this much>\"")
    print("=" * 78)
    sys.exit(2)


# no em dash inside a macro string
def cmd_check(args):
    whole_flag = "--whole" in args; bop_flag = "--bop" in args
    args = [t for t in args if t not in ("--whole", "--bop")]
    because = _opt(args, "--because")
    if bop_flag and not (because or "").strip():
        print("kit check REFUSED: --bop needs --because \"<the reason this body must be tested for "
              "self-intersection now>\".\n  The test walks every face pair (minutes on this body); "
              "with a reason it is approved, without one it is waste (the client, 2026-09-10).")
        return 2
    if because:
        _i = args.index("--because"); args = args[:_i] + args[_i + 2:]
    a = _kv(args)
    if not a["_"] or not (a.get("--base") or "").strip() or not (a.get("--out") or "").strip() or not (a.get("--boxes") or a.get("--box")):      # KeyError
        print("kit check REFUSED: it takes <result.brep> --base <the body BEFORE the edit> --box x0 x1 y0 y1 z0 z1 --out <dir> --job <name> (the usage: kit check --help)."
              + ("" if (a.get("--base") or "").strip() or not a["_"] else
                 "\n  A FIRST BODY has no base and is not checked against one (PROJECT_START.md 1; 31bv B1): look at it (kit render <result> --box ...), copy it into claude_code\\bank\\,\n"
                 "  `kit promote` it, and `kit cancel <job> --why \"the first body - promoted from the bank\"` takes its job off the books."))
        return 2
    res = a["_"][0]; base = a["--base"]; out = a["--out"]
    allbox = [list(map(float, b.split())) for b in a.get("--boxes") or [a["--box"]]]
    bx = allbox[0]
    if len(allbox) > 1: print("[leangate] %d permitted boxes - the material BETWEEN them is inspected, not exempted." % len(allbox))
    gate_box_size(allbox, a.get("--job"), a.get("--wide-box"))
    expect = a.get("--expect", "?"); name = a.get("--name", "check"); os.makedirs(out, exist_ok=True)
    faces = a.get("--max-new-faces", a.get("--faces"))
    _jb = a.get("--job")
    # RENDER REVIEW FIRST
    # confirmed
    # kit accept
    if _jb:
        _rvd = a.get("--review", "")
        if not _rvd:
            _prev = (G.job(ROOT, _jb) or {}).get("review_dir")
            _rvd = _prev or ""
        _rst = _rv_load(_rvd) if _rvd else None
        if not _rst:
            sys.exit("kit check REFUSED: no render review named for job %s. RENDER REVIEW FIRST - the numbers come after\n"
                     "  the pictures. Render the after frames on the job's box, judge the lead frames, then check:\n"
                     "     kit review <before.brep> <result.brep> --out <dir> --box <the job box> --lead <views>\n"
                     "     kit review --render <dir> --leads                                              (the lead frames alone; 31bw)\n"
                     "     kit review --judge <dir> --frame <lead> --verdict pass|fail|cannot --note \"...\"   (each lead)\n"
                     "     kit check ... --job %s --review <dir>" % (_jb, _jb))
        if _rst.get("state") == "ABORTED":
            sys.exit("kit check REFUSED: the render review %s ABORTED on a confirmed defect. A check on a build already\n"
                     "  known to be wrong is wasted compute - fix the build and review again." % _rvd)
        if _rst.get("state") == "VOID":
            sys.exit("kit check REFUSED: the render review %s is VOID (every lead came back `cannot`) - re-aim the\n"
                     "  cameras and review again before measuring anything." % _rvd)
        _lead = _rst.get("lead", []); _v = _rst.get("verdicts", {})
        _unjudged = [f for f in _lead if f not in _v]
        _open_s = [k for k, x in (_rst.get("suspects") or {}).items() if not x.get("confirmed_by") and not x.get("cleared_by")]
        if _unjudged or _open_s:
            sys.exit("kit check REFUSED: the render review %s has %d lead frame(s) unjudged%s. Judge them first - the\n"
                     "  pictures decide whether the numbers are worth taking."
                     % (_rvd, len(_unjudged), (" and %d suspect(s) unconfirmed" % len(_open_s)) if _open_s else ""))
        G.job_mark(ROOT, _jb, "review_dir", _rvd)
        print("[leangate] render review %s: leads judged (%s) - the numbers may be taken." % (_rvd, _rst.get("state")))
    if faces is None and _jb:
        _j = G.job(ROOT, _jb) or {}
        if _j.get("expect_faces") is not None:
            faces = _j["expect_faces"]
            print("[leangate] max NEW faces = %s, from job %s's expect_faces." % (faces, _jb))
        elif _j.get("expect_faces_unsigned") is not None:      # not taken
            print("[leangate] the card's face figure %s was NOT taken as the growth allowance (no sign, 40 or more - it reads as a face COUNT): write `faces about +N` for the N NEW faces (`kit card`, `kit job %s` alone) or pass --max-new-faces N; the growth check runs at 40 below (31bw)" % (_j["expect_faces_unsigned"], _jb))
    if faces is None:
        faces = 40
        print("[leangate] NOTE: no --max-new-faces and no expect_faces on the job, so the "
              "face-explosion\n[leangate]   check is effectively OFF (allowing 40 new faces). "
              "It is a GROWTH allowance,\n[leangate]   not a face count - a rectangular pocket "
              "adds 5.")
    faces = int(faces)
    if faces < 0:
        print("[leangate] the face figure %d is a DROP (the edit removes faces): the growth ceiling is 0 - no net new face inside the region; the drop's size is not checked by count, the volume tripwire and the pictures judge the cut (31bw)" % faces); faces = 0
    solids_exp = a.get("--expect-solids")
    if solids_exp is None and _jb:
        _js9 = G.job(ROOT, _jb) or {}
        if _js9.get("expect_solids") is not None:
            solids_exp = _js9["expect_solids"]; print("[leangate] expected solids = %s, from job %s's card (Expected: ... solids N)." % (solids_exp, _jb))
    solids_exp = int(solids_exp) if solids_exp is not None else None
    _wgx = a.get("--wall-grow-x", os.environ.get("WALL_GROW_X"))
    try: wallx = float(_wgx) if _wgx not in (None, "", True) else 4.0
    except ValueError:
        print("kit check REFUSED: --wall-grow-x needs a number (got %r)" % (_wgx,)); return 2
    if wallx < 0:
        print("kit check REFUSED: --wall-grow-x is a multiple of the base's faces at the region, never negative (got %g)" % wallx); return 2
    print("[leangate] WALL_GROW_X = %g (%s): the faces on or beside the edit region's walls may grow by at most %g x (base INSIDE + base WALL-ADJACENT) - the walls' splits; more fails (31bq B08 C2)" % (wallx, "suggested" if _wgx in (None, "", True) else "set", wallx))
    code = r'''
import sys, os, json, hashlib, time as _tm; sys.path.insert(0, %(here)r); import kitlib as K, numpy as np
_t0 = _tm.time()
res = K.load(%(res)r); ALLBOX = %(allbox)r; bx = ALLBOX[0]
box3 = ((bx[0],bx[1]),(bx[2],bx[3]),(bx[4],bx[5]))
rep = {"result": %(res)r, "base": %(base)r, "box": bx, "boxes": ALLBOX, "expect": %(expect)r}
rep["valid"] = bool(res.isValid()); rep["solids"] = len(res.Solids); rep["faces"] = len(res.Faces)
print("CHECK step: result loaded, valid %%s, %%.0f s" %% (rep["valid"], _tm.time() - _t0), flush=True)
# THE BASE IS LOADED ONCE PER MODEL OF RECORD, EVER. Its face count, kernel volume, bounding box
# and tessellation are recorded under the PROJECT's claude_code\jobs\_tess_cache by the file's hash
# the first time a check sees it; every later check on the same base loads ONE body, not two (the client,
# 2026-09-10: cheaper checks). The result is tessellated once (about 7 s on this body).
# THE PROJECT'S FOLDER, NOT THE KIT'S. This was `<kit>\..\jobs\_tess_cache`, which was the project's
# folder only while the kit was a copy inside each project; since the 2026-09-14 unification it was
# LEAN_KIT\jobs\_tess_cache - the kit writing project data into the master, past every
# guard (a subprocess). Found 2026-09-17: a 5.9 MB npz from 09-14 sitting in the master.
# 31bq B08 (check-faces, R7W): AND NEVER AGAIN FOR THE FACES. The face classes below read this record's own 0.05 mm mesh (every face's triangles: FID) - the count
# had loaded the whole base B-rep again on every check (K.load + the kernel's CenterOfMass of 4765 faces: 10-11 s of a 55-63 s check on R31). The record now carries
# (1) the MESHER that made it (FreeCAD + OCC: the far faces are matched mesh to mesh, and one mesher makes an unchanged face's mesh identically - measured 0.0 mm
# on 4603 far faces of fill15's body; a record without the stamp or made by another mesher is re-meshed ONCE), (2) the kernel's centre and area of every face the mesh
# holds no triangle of (R31: 2 faces), (3) the volume ruler's 0.025 mm base mesh volume, the first time a check needs it.
_bj_path = None
def _rec_save(pj_, j_):      # the record written whole or not at all
    _tmp = pj_ + ".writing"
    with open(_tmp, "w", encoding="utf-8") as fh_: json.dump(j_, fh_)
    os.replace(_tmp, pj_)
def _mesher():
    try: return "FreeCAD %%s / OCC %%s" %% (".".join(str(x_) for x_ in K.App.Version()[:4]), getattr(K.Part, "OCC_VERSION", "?"))
    except Exception as _em: return "unknown (%%s)" %% str(_em)[:40]
def _no_mesh_faces(shape_, fid_):      # {face index: [cx, cy, cz, area]}: the kernel's centre and area of every face the 0.05 mm mesh holds no triangle of
    _has = set(int(i_) for i_ in np.unique(np.asarray(fid_))) if len(fid_) else set(); out_ = {}
    for i_, f_ in enumerate(getattr(shape_, "Faces", None) or []):
        if i_ in _has: continue
        try:
            c_ = f_.CenterOfMass; out_[str(i_)] = [float(c_.x), float(c_.y), float(c_.z), float(f_.Area)]
        except Exception:
            try:
                b_ = f_.BoundBox; out_[str(i_)] = [(b_.XMin + b_.XMax) / 2.0, (b_.YMin + b_.YMax) / 2.0, (b_.ZMin + b_.ZMax) / 2.0, 0.0]
            except Exception: out_[str(i_)] = None
    return out_
def _base_cached(path):
    global _bj_path
    h = hashlib.md5(open(path, "rb").read()).hexdigest()
    d = os.path.join(%(root)r, "claude_code", "jobs", "_tess_cache"); os.makedirs(d, exist_ok=True)
    pn, pj = os.path.join(d, h + ".npz"), os.path.join(d, h + ".json"); _bj_path = pj; _why = ""
    if os.path.exists(pn) and os.path.exists(pj):
        z = np.load(pn); j = json.load(open(pj, encoding="utf-8"))
        if j.get("mesher") == _mesher() and "faces_no_mesh" in j and "solids" in j:      # 31bx V10: a record older than 31bw B4 has no solid count - re-made, never read as one solid
            print("CHECK step: base from cache (%%s: %%d faces, vol %%.0f)" %% (os.path.basename(path), j["faces"], j["vol_kernel"]), flush=True)
            return z["V"], z["T"], z["FID"], j
        z.close()      # 31bq B08 (check-faces) edit 3: the record is re-made below - an npz np.load holds open cannot be replaced on Windows ([WinError 5])
        _why = (" - the record has no solid count (made before 31bw B4)" if "solids" not in j else ((" - the record was made by %%s, this check runs %%s" %% (j.get("mesher"), _mesher())) if j.get("mesher") else " - the record predates the face classes (no mesher stamp, no faces with no triangle)"))
    b = K.load(path); Vx, Tx, Fx = K.tess(b); bb = b.BoundBox
    j = {"faces": len(b.Faces), "solids": len(b.Solids), "vol_kernel": float(b.Volume),
         "bbox": [bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax], "mesher": _mesher(), "faces_no_mesh": _no_mesh_faces(b, Fx)}
    try:
        np.savez_compressed(pn + ".writing.npz", V=Vx, T=Tx, FID=Fx); os.replace(pn + ".writing.npz", pn); _rec_save(pj, j)
    except Exception as _e:
        _bj_path = None      # 31bq B08 C3: the record was not written whole - nothing later stamps the json onto an npz it does not match
        try:
            if os.path.exists(pn + ".writing.npz"): os.remove(pn + ".writing.npz")
        except OSError: pass
        print("CHECK note: base not cached (%%s) - the record is left as it was" %% _e, flush=True)
    print("CHECK step: base loaded and cached%%s, %%.0f s" %% (_why, _tm.time() - _t0), flush=True)
    return Vx, Tx, Fx, j
Vb, Tb, Fb, _bj = _base_cached(%(base)r); rep["faces_base"] = _bj["faces"]; rep["solids_base"] = int(_bj.get("solids", 1) or 1)      # 31bw B4 (a record without a count is re-made - 31bx V10)
V, T, F = K.tess(res)
# 31bq B08 (check-faces, R7W): THE FACE BUDGET IS THE EDIT REGION'S, AND NOTHING FAR FROM IT MAY CHANGE - requirement 4 of BURRITO_STEPS' head (very few faces,
# at or under the original section's count) judged INSIDE the edit region; a sew joins the piece on the body's own section faces at the walls, so the only change
# expected outside it is the walls' splits of the body's own faces. Every face of the base (its cached 0.05 mm mesh record - the base B-rep is NOT loaded for this)
# and of the result (its own 0.05 mm mesh, made above) is CLASSED by where its TRIANGLES lie (the separating-axis test of each triangle against each convex region -
# exact; a vertex or centroid sample missed a big planar triangle crossing a box: R31's 100 mm faces carry two), the grace g 0.5 mm, against
#   THE EDIT REGION - the job's REBUILD_region.json (its window cut by its planes: the walls the piece is sewn on) when the job records one, else every --box; and
#   THE PERMITTED REGION - every --box, the edit region, and the reinsert's LOCAL BOX (_localbox.brep: STEP 1 cut the body there as well - the region's box + G; its
#   splits lie 3 mm outside the region: b27b with the agent's own box had 68 of them beyond the box, all reading far without it):
#     INSIDE        a triangle reaches more than g into the edit region - the edited section's faces: THE BUDGET judges these alone;
#     ON A WALL     every vertex within g of the edit region and none more than g inside - a cap / a section face lying on a wall: said, not counted;
#     WALL-ADJACENT in or touching the permitted region within g - a body face a wall cut (the region's walls, the local box's): its growth is the walls' splits,
#                   expected, said with the count;
#     FAR           more than g outside the permitted region everywhere - NOTHING may change there: a far face the base does not hold (its mesh centroid within
#                   _FFAR_C mm, its area within _FFAR_A) or a far face of the base gone FAILS by name.
# The count it replaces (a face's CENTRE in a box + 0.5 mm, round 4's B08): a pure box-wall split read +1 inside (the inside fragment of a face whose centre lay
# outside) and failed a 0 budget; nothing outside the boxes was judged (a 5-face pocket and 40 splits far from the box passed); a card box with a margin counted the
# body's own wall splits in it as the piece's (fill15: base 137 -> 161 inside the window + 3 mm while the piece has half the content's faces).
_FG, _FFAR_C, _FFAR_A = 0.5, 1e-4, 1e-6
_FCLS = ("INSIDE", "ON A WALL", "WALL-ADJACENT", "FAR", "UNCLASSED")
def _fhs(b_):      # a box as half-spaces: a point on each wall and its OUTWARD normal
    return (np.array([[b_[0], 0, 0], [b_[1], 0, 0], [0, b_[2], 0], [0, b_[3], 0], [0, 0, b_[4]], [0, 0, b_[5]]], float),
            np.array([[-1, 0, 0], [1, 0, 0], [0, -1, 0], [0, 1, 0], [0, 0, -1], [0, 0, 1]], float))
def _fpoly(P0, N, off):      # the convex region {p: n.p <= n.p0 - off} (off > 0 shrinks it, < 0 grows it): its vertices, face normals, edge directions, box - None when empty or flat
    P0 = np.asarray(P0, float); N = np.asarray(N, float); N = N / np.linalg.norm(N, axis=1)[:, None]
    b = np.einsum("ij,ij->i", P0, N) - off; m = len(N); vs = []
    for i in range(m):
        for j in range(i + 1, m):
            for k in range(j + 1, m):
                A3 = N[[i, j, k]]
                if abs(np.linalg.det(A3)) < 1e-9: continue
                p = np.linalg.solve(A3, b[[i, j, k]])
                if np.all(N @ p <= b + 1e-7): vs.append(p)
    if len(vs) < 4: return None
    Vp = np.unique(np.round(np.array(vs), 7), axis=0); act = np.abs(Vp @ N.T - b[None, :]) < 1e-5
    if np.linalg.matrix_rank(Vp - Vp[0]) < 3: return None
    FN = N[act.sum(axis=0) >= 3]; E = []
    for a in range(len(Vp)):
        for c in range(a + 1, len(Vp)):
            if (act[a] & act[c]).sum() >= 2:
                d = Vp[c] - Vp[a]; L = float(np.linalg.norm(d))
                if L > 1e-9:
                    d = d / L
                    if not any(abs(abs(float(d @ e)) - 1.0) < 1e-9 for e in E): E.append(d)
    return Vp, FN, np.array(E, float).reshape(-1, 3), np.r_[Vp.min(axis=0), Vp.max(axis=0)]
def _fhit(T3, polys):      # T3 (n, 3, 3) triangles -> (n,) bool: the triangle meets one of the convex polytopes (the separating-axis test - exact, a touch counts)
    hit = np.zeros(len(T3), bool)
    if not len(T3): return hit
    tmin = T3.min(axis=1); tmax = T3.max(axis=1)
    for pol in polys:
        if pol is None: continue
        Vp, FN, E, bb = pol
        cand = np.flatnonzero(~hit & np.all(tmax >= bb[:3] - 1e-9, axis=1) & np.all(tmin <= bb[3:] + 1e-9, axis=1))
        if not len(cand): continue
        Tc = T3[cand]; e0 = Tc[:, 1] - Tc[:, 0]; e1 = Tc[:, 2] - Tc[:, 1]; e2 = Tc[:, 0] - Tc[:, 2]; ok = np.ones(len(cand), bool)
        def sep(ax):
            tp = np.einsum("nij,nj->ni", Tc, ax); pp = ax @ Vp.T; nz = np.einsum("ij,ij->i", ax, ax) > 1e-18
            return nz & ((tp.max(axis=1) < pp.min(axis=1) - 1e-9) | (tp.min(axis=1) > pp.max(axis=1) + 1e-9))
        for fn in FN: ok &= ~sep(np.broadcast_to(fn, e0.shape))
        ok &= ~sep(np.cross(e0, -e2))
        for ed in E:
            for te in (e0, e1, e2): ok &= ~sep(np.cross(np.broadcast_to(ed, te.shape), te))
        hit[cand[ok]] = True
    return hit
def _fdepth(Pts, regs):      # > 0 inside the union of the convex regions (P0, N); < 0 outside it (minus the largest wall violation - a lower bound of the distance)
    Pts = np.asarray(Pts, float).reshape(-1, 3); best = np.full(len(Pts), -np.inf)
    for k0 in range(0, len(Pts), 200000):
        Q = Pts[k0:k0 + 200000]; bq = np.full(len(Q), -np.inf)
        for P0, N in regs:
            N = np.asarray(N, float); N = N / np.linalg.norm(N, axis=1)[:, None]
            bq = np.maximum(bq, (np.einsum("ij,ij->i", np.asarray(P0, float), N)[None, :] - Q @ N.T).min(axis=1))
        best[k0:k0 + 200000] = bq
    return best
def _fclasses(Vx, Tx, Fx, nf, nomesh, ereg, preg, g):      # every face's class (an index into _FCLS), centroid and area - its mesh's; the kernel's for a face the mesh holds no triangle of
    Vx = np.asarray(Vx, float); Tx = np.asarray(Tx, np.int64); Fx = np.asarray(Fx, np.int64)
    if len(Fx) > 1 and np.any(np.diff(Fx) < 0):
        o = np.argsort(Fx, kind="stable"); Tx, Fx = Tx[o], Fx[o]
    pin = [_fpoly(P0, N, g) for P0, N in ereg]; pout = [_fpoly(P0, N, -g) for P0, N in preg]
    nt = np.bincount(Fx, minlength=nf)[:nf]; T3 = Vx[Tx]
    f_in = np.bincount(Fx[_fhit(T3, pin)], minlength=nf)[:nf] > 0      # a triangle reaches more than g into the edit region
    f_pr = np.bincount(Fx[_fhit(T3, pout)], minlength=nf)[:nf] > 0      # a triangle meets the permitted region grown by g
    dmin = _fdepth(Vx, ereg)[Tx].min(axis=1); f_dmin = np.full(nf, -np.inf)
    if len(Fx):
        st = np.flatnonzero(np.r_[True, Fx[1:] != Fx[:-1]]); f_dmin[Fx[st]] = np.minimum.reduceat(dmin, st)      # every vertex within g outside the edit region (convex: the triangles too)
    A = 0.5 * np.linalg.norm(np.cross(T3[:, 1] - T3[:, 0], T3[:, 2] - T3[:, 0]), axis=1); cg = T3.mean(axis=1)
    area = np.bincount(Fx, A, minlength=nf)[:nf]
    cen = np.vstack([np.bincount(Fx, A * cg[:, k], minlength=nf)[:nf] for k in range(3)]).T
    cm = np.vstack([np.bincount(Fx, cg[:, k], minlength=nf)[:nf] for k in range(3)]).T
    with np.errstate(invalid="ignore", divide="ignore"):
        cen = np.where((area > 0)[:, None], cen / np.where(area > 0, area, 1.0)[:, None], cm / np.maximum(nt, 1)[:, None])
    cls = np.where(f_in, 0, np.where(f_dmin >= -g, 1, np.where(f_pr, 2, 3)))
    nm = np.flatnonzero(nt == 0)
    for i in nm:
        q = (nomesh or {}).get(str(int(i)))
        if q:
            P_ = np.array([q[:3]], float); e = float(_fdepth(P_, ereg)[0]); pr = float(_fdepth(P_, preg)[0])
            cls[i] = 0 if e > g else (1 if abs(e) <= g else (2 if pr >= -g else 3)); cen[i] = q[:3]; area[i] = float(q[3]) if len(q) > 3 else 0.0
        else:
            cls[i] = 4; cen[i] = np.nan
    return cls, cen, area, [int(i) for i in nm]
def _far_match(cb, cenb, arb, cr, cenr, arr, tol_c, tol_a):      # the FAR faces of the result matched one to one to the base's: centroid within tol_c mm, area within tol_a (relative)
    ib = np.flatnonzero(cb == 3); ir = np.flatnonzero(cr == 3); Cb = cenb[ib]; Ab = arb[ib]
    o = np.argsort(Cb[:, 0], kind="stable"); xs = Cb[o, 0]; used = np.zeros(len(ib), bool); new = []; wc = 0.0; wa = 0.0
    for i in ir:
        c = cenr[i]; a = float(arr[i]); hit = -1
        if np.all(np.isfinite(c)):
            for j in o[np.searchsorted(xs, c[0] - tol_c):np.searchsorted(xs, c[0] + tol_c, side="right")]:
                if used[j]: continue
                dc = float(np.linalg.norm(Cb[j] - c)); da = abs(float(Ab[j]) - a) / max(float(Ab[j]), a, 1e-12)
                if dc <= tol_c and da <= tol_a:
                    hit = j; wc = max(wc, dc); wa = max(wa, da); break
        if hit < 0: new.append(int(i))
        else: used[hit] = True
    return int(len(ib)), int(len(ir)), new, [int(ib[j]) for j in np.flatnonzero(~used)], wc, wa
def _fapart(boxes, ref):      # 31bq B08 C1: the --boxes that do not meet ref (the job's local box, else its window) - each is an edit region of its own
    return [b_ for b_ in boxes if (b_[1] < ref[0] or b_[0] > ref[1] or b_[3] < ref[2] or b_[2] > ref[3] or b_[5] < ref[4] or b_[4] > ref[5])]
def _fwall_limit(nb, nr, k):      # 31bq B08 C2: the growth of WALL-ADJACENT + ON A WALL (nb / nr: the counts in _FCLS order) against k x (base INSIDE + base WALL-ADJACENT)
    g_ = (nr[1] + nr[2]) - (nb[1] + nb[2]); lim_ = float(k) * (nb[0] + nb[2]); return g_, lim_, g_ > lim_
_t0 = _tm.time(); rep["face_classes"] = None
try:
    _ereg = []; _preg = [_fhs(b_) for b_ in ALLBOX]; _ereg_how = "the %%d --box(es) of the check" %% len(ALLBOX); _preg_how = ""
    _jdr = %(jobdir)r; _rj = os.path.join(_jdr, "REBUILD_region.json") if _jdr else ""
    if _rj and os.path.isfile(_rj):
        _rr = json.load(open(_rj, encoding="utf-8")) or {}; _w = [float(x_) for x_ in (_rr.get("window") or [])]
        if len(_w) == 6:
            _P0, _N = _fhs(_w); _pl = [[float(v_) for v_ in x_] for x_ in (_rr.get("planes") or []) if len(x_) == 6]
            if _pl: _P0 = np.vstack([_P0, np.array([x_[:3] for x_ in _pl], float)]); _N = np.vstack([_N, np.array([x_[3:] for x_ in _pl], float)])
            _ereg = [(_P0, _N)]; _ereg_how = "the job's EDIT REGION (REBUILD_region.json: the window %%s cut by %%d plane(s) - the walls the piece is sewn on)" %% (_w, len(_pl))
            _lb = os.path.join(_jdr, "_localbox.brep")
            if os.path.isfile(_lb):
                _lbb = K.load(_lb).BoundBox; _lbx = [_lbb.XMin, _lbb.XMax, _lbb.YMin, _lbb.YMax, _lbb.ZMin, _lbb.ZMax]; _preg.append(_fhs(_lbx))
                _preg_how = ", the reinsert's local box %%s" %% [round(v_, 2) for v_ in _lbx]
            else: _preg_how = " (the job holds no _localbox.brep: no local box in it - a split of the reinsert's local box beyond the --box(es) would read FAR)"
            _ref = _lbx if os.path.isfile(_lb) else _w; _apart = _fapart(ALLBOX, _ref)      # 31bq B08 C1 (V5: two pockets with --boxes A B on a job whose region is A passed - B's faces were judged by nothing)
            if _apart:
                _ereg += [_fhs(b_) for b_ in _apart]; _ereg_how += " + %%d --box(es) apart from the job's %%s (each an edit region of its own: %%s)" %% (len(_apart), "local box" if os.path.isfile(_lb) else "window", [list(b_) for b_ in _apart[:4]])
    if not _ereg: _ereg = [_fhs(b_) for b_ in ALLBOX]
    _preg = _preg + _ereg
    _nfr = len(res.Faces); _nfb = int(_bj.get("faces") or 0)
    if not _nfr or not _nfb: raise ValueError("a mesh base or result - no B-rep faces to class")
    _hasr = set(int(x_) for x_ in np.unique(np.asarray(F))); _nm_r = {}
    for i_ in range(_nfr):
        if i_ in _hasr: continue
        try: c_ = res.Faces[i_].CenterOfMass; _nm_r[str(i_)] = [float(c_.x), float(c_.y), float(c_.z), float(res.Faces[i_].Area)]
        except Exception: _nm_r[str(i_)] = None
    _cb, _cenb, _arb, _nmb = _fclasses(Vb, Tb, Fb, _nfb, _bj.get("faces_no_mesh") or {}, _ereg, _preg, _FG)
    _cr, _cenr, _arr, _nmr = _fclasses(V, T, F, _nfr, _nm_r, _ereg, _preg, _FG)
    _nb = [int((_cb == k_).sum()) for k_ in range(5)]; _nr = [int((_cr == k_).sum()) for k_ in range(5)]
    _fb0, _fr0, _fnew, _fgone, _fwc, _fwa = _far_match(_cb, _cenb, _arb, _cr, _cenr, _arr, _FFAR_C, _FFAR_A)
    _fat = lambda ids_, C_: [[round(float(v_), 2) for v_ in C_[i_]] for i_ in ids_[:6]]
    rep["face_classes"] = {"edit_region": _ereg_how, "permitted": "the --box(es)%%s and the edit region" %% _preg_how, "grace_mm": _FG,
                           "how": "a face's triangles against each convex region by the separating-axis test (its 0.05 mm mesh; the kernel's centre for a face the mesh holds no triangle of)",
                           "base": dict(zip(_FCLS, _nb)), "new": dict(zip(_FCLS, _nr)),
                           "far": {"base": _fb0, "new": _fr0, "changed": len(_fnew) + len(_fgone), "n_new_or_moved": len(_fnew), "new_or_moved": _fnew[:40], "new_or_moved_at": _fat(_fnew, _cenr),
                                   "n_gone": len(_fgone), "gone": _fgone[:40], "gone_at": _fat(_fgone, _cenb),
                                   "match": {"centroid_mm": _FFAR_C, "area_rel": _FFAR_A, "matched_worst_centroid_mm": _fwc, "matched_worst_area_rel": _fwa}},
                           "no_triangle": {"base": _nmb[:20], "new": _nmr[:20]}}
    rep["faces_in_box"], rep["faces_in_box_base"] = _nr[0], _nb[0]      # the keys the readers know - the INSIDE class now (was a face's centre in a box + 0.5 mm)
    rep["faces_on_wall"], rep["faces_on_wall_base"] = _nr[1], _nb[1]
    rep["faces_wall_adjacent"], rep["faces_wall_adjacent_base"] = _nr[2], _nb[2]
    rep["faces_far"], rep["faces_far_base"], rep["faces_far_changed"] = _nr[3], _nb[3], len(_fnew) + len(_fgone)
    _wg, _wl, _wo = _fwall_limit(_nb, _nr, %(wallx)r)      # 31bq B08 C2 (V3: eight 0.9 mm slivers beside a wall at budget 0 read "the walls' splits" and passed)
    rep["face_classes"]["walls_growth"] = {"growth": _wg, "limit": _wl, "WALL_GROW_X": %(wallx)r, "over": bool(_wo)}
    print("CHECK step: the faces by where they lie (g %%.1f mm; the base from its cached mesh record - no B-rep loaded) against %%s, the permitted region the --box(es)%%s:"
          " INSIDE %%d -> %%d (the budget judges these); ON A WALL %%d -> %%d (caps / section faces on the walls - said, not counted); WALL-ADJACENT %%d -> %%d (%%+d: the walls' splits"
          " of the body's own faces - expected - its growth with ON A WALL's at most %%g = WALL_GROW_X %%g x (base INSIDE + base WALL-ADJACENT)); FAR %%d -> %%d (%%d changed - nothing may change there)%%s; the whole body %%d -> %%d; %%.1f s"
          %% (_FG, _ereg_how, _preg_how, _nb[0], _nr[0], _nb[1], _nr[1], _nb[2], _nr[2], _nr[2] - _nb[2], _wl, %(wallx)r, _nb[3], _nr[3], len(_fnew) + len(_fgone),
             ("; UNCLASSED %%d -> %%d (no triangle and no kernel centre)" %% (_nb[4], _nr[4])) if (_nb[4] or _nr[4]) else "", _nfb, _nfr, _tm.time() - _t0), flush=True)
except Exception as _e:
    rep["face_classes"] = None; rep["face_classes_not_taken"] = str(_e)[:200]
    print("CHECK note: the faces by where they lie were NOT TAKEN (%%s) - the whole body's growth is judged against the budget instead" %% str(_e)[:120], flush=True)
def _near_box3(f_, g_=2.0):
    try:
        b_ = f_.BoundBox
        return any(not (b_.XMax < _b[0] - g_ or b_.XMin > _b[1] + g_ or b_.YMax < _b[2] - g_ or b_.YMin > _b[3] + g_ or b_.ZMax < _b[4] - g_ or b_.ZMin > _b[5] + g_) for _b in ALLBOX)
    except Exception: return False
# 31bq B09: the opening test's 0.02 mm mesh of the faces near the box; B08 (check-faces): made only when a column OPENED (it decides nothing otherwise) - the base B-rep
# is loaded for it then, never for the face count
_fine = None; _fine_tried = False
def _fine_mesh():
    global _fine, _fine_tried
    if _fine_tried: return _fine
    _fine_tried = True
    try:
        import Part as _Part
        _t1 = _tm.time(); _bsh = K.load(%(base)r)
        _fn = [f_ for f_ in res.Faces if _near_box3(f_)]; _fb = [f_ for f_ in _bsh.Faces if _near_box3(f_)]
        if _fn and _fb:
            _V2, _T2, _ = K.tess(_Part.makeCompound(_fn), dev=0.02); _Vb2, _Tb2, _ = K.tess(_Part.makeCompound(_fb), dev=0.02); _fine = (_V2, _T2, _Vb2, _Tb2)
            print("CHECK step: a column opened - the faces near the box meshed again at 0.02 mm for the opening test (%%d / %%d faces, %%d / %%d triangles; the base B-rep loaded for it, %%.0f s)" %% (len(_fn), len(_fb), len(_T2), len(_Tb2), _tm.time() - _t1), flush=True)
        del _bsh, _fb
    except Exception as _e:
        print("CHECK note: no fine mesh for the opening test (%%s) - the 0.05 mm caster alone decides" %% str(_e)[:120], flush=True)
    return _fine
kv, tv = float(res.Volume), float(K.R.div_volume(V, T)); kvb, tvb = float(_bj["vol_kernel"]), float(K.R.div_volume(Vb, Tb))
rep["vol_kernel"] = kv; rep["vol_tess"] = tv; rep["dvol_kernel"] = kv - kvb; rep["dvol_tess"] = tv - tvb
print("CHECK step: tessellated, dvol kernel %%+.0f tess %%+.0f, %%.0f s" %% (kv - kvb, tv - tvb, _tm.time() - _t0), flush=True)
# 31bp fix 7d: THE LOCAL RULER - a job whose change is a PIECE put in for the region's CONTENT (the burrito's skin route: content.brep, skin\\piece_skin.brep)
# has its volume change measured as the two small solids' difference, where the kernel's volume is a ruler (cross-checked by each solid's own mesh); the
# whole-body mesh delta carries the litre's own tessellation spread (tens of mm3 outside the region) and cannot resolve a change to a few percent
rep["dvol_local"] = None
try:
    _jd = %(jobdir)r
    _pc, _pp = (os.path.join(_jd, "content.brep"), os.path.join(_jd, "skin", "piece_skin.brep")) if _jd else ("", "")
    if _jd and os.path.isfile(_pc) and os.path.isfile(_pp):
        rep["skin_piece"] = True      # 31bq SS (B21 (3)): a skin edit - accept REPORTS its volume change whatever ruler took it (set before the ruler, so its failure keeps it)
        _c = K.load(_pc); _p = K.load(_pp)
        _ck, _cm = K.volumes(_c); _pk, _pm = K.volumes(_p)
        _ok_c = abs(_ck - _cm) <= max(5.0, 0.005 * abs(_cm)); _ok_p = abs(_pk - _pm) <= max(5.0, 0.005 * abs(_pm))
        _dlk, _dlm = (_pk - _ck), (_pm - _cm); _dl = _dlk if (_ok_c and _ok_p) else _dlm
        # 31bp fix 7d (2): both local deltas and their SPREAD on record - the ruler's own resolution on this artefact (the kernel's volume of a solid with
        # self-touches and raised edge tolerances against its mesh: 41 mm3 on b27b's piece); accept's tolerance is never tighter than it
        rep["dvol_local"] = float(_dl); rep["dvol_local_kernel"] = float(_dlk); rep["dvol_local_mesh"] = float(_dlm); rep["dvol_local_spread"] = float(abs(_dlk - _dlm))
        rep["dvol_local_how"] = {"content_kernel": _ck, "content_mesh": _cm, "piece_kernel": _pk, "piece_mesh": _pm, "by": "the kernel (its volumes agree with the meshes)" if (_ok_c and _ok_p) else "the meshes (the kernel's volume of a small solid disagreed with its mesh)"}
        print("CHECK step: the change by the LOCAL ruler - the piece (%%.1f mm3) against the region's content (%%.1f): %%+.1f by %%s (the kernel says %%+.1f, the meshes %%+.1f - the ruler's own spread %%.0f mm3); the whole-body meshes say %%+.0f and carry the body's own tessellation spread" %% (_pk, _ck, _dl, rep["dvol_local_how"]["by"], _dlk, _dlm, abs(_dlk - _dlm), tv - tvb), flush=True)
        del _c, _p
except Exception as _el:
    rep["dvol_local_failed"] = str(_el)[:200]      # 31bq SS (B21 (3)): on record for accept
    print("CHECK note: the local ruler was not taken (%%s)" %% str(_el)[:80], flush=True)
# THE KERNEL'S SELF-INTERSECTION TEST (shape.check(True), BOPCheck over every face pair - minutes
# on 4013 faces) RUNS ONLY WHEN ASKED FOR WITH A REASON: `kit check --bop --because "..."`.
# the client, 2026-09-10: "Claude can request to run it and then be auto approved as long as it has
# reason for it. I just don't want it running wastefully."
_collar = %(collar)r
if %(bop)r:
    ok, msg = K.bop_ok(res); rep["bop_because"] = %(because)r
    print("CHECK step: BOP self-intersection test, whole body (because: %%s): %%s, %%.0f s" %% (%(because)r, "ok" if ok else "FAIL", _tm.time() - _t0), flush=True)
else:
    ok, msg = True, "not run (kit check --bop --because \"<why>\" runs it)"
rep["bop_ok"] = ok; rep["bop_msg"] = msg
step = 1.0
xs, ys, H = K.thickness_map(V, T, (box3[0], box3[1]), step); _, _, Hb = K.thickness_map(Vb, Tb, (box3[0], box3[1]), step)
rep["map_max_gain"] = float((H-Hb).max()); rep["map_max_loss"] = float((H-Hb).min())
# NEW OPENINGS (punch-through): columns that had material and now have none - ON ALL THREE AXES.
# thickness_map used to cast z rays only, so a wall bored through SIDEWAYS reported `opened 0`.
opened = 0; rep["columns_opened_by_axis"] = {}
for _ax in (0, 1, 2):
    try:
        _, _, _Ha = K.thickness_map(V, T, box3, step, axis=_ax)
        _, _, _Hba = K.thickness_map(Vb, Tb, box3, step, axis=_ax)
        _open = (_Hba > 0.5) & (_Ha < 0.05)
        if _open.any():      # 31bq the agent (B09 (3)): an opened column is CONFIRMED by four more casts at quarter-step offsets on the WHOLE mesh - a caster's miss between two triangles of a thin wall opens one cast, a real bore opens all
            try:
                _conf = _open.copy(); _ax2 = [a__ for a__ in (0, 1, 2) if a__ != _ax]
                for _dx, _dy in ((0.25, 0.0), (-0.25, 0.0), (0.0, 0.25), (0.0, -0.25)):
                    _b2 = [list(b__) for b__ in box3]; _b2[_ax2[0]] = [_b2[_ax2[0]][0] + _dx, _b2[_ax2[0]][1] + _dx]; _b2[_ax2[1]] = [_b2[_ax2[1]][0] + _dy, _b2[_ax2[1]][1] + _dy]
                    _, _, _Ha3 = K.thickness_map(V, T, tuple(tuple(b__) for b__ in _b2), step, axis=_ax); _, _, _Hba3 = K.thickness_map(Vb, Tb, tuple(tuple(b__) for b__ in _b2), step, axis=_ax)
                    _o3 = (_Hba3 > 0.5) & (_Ha3 < 0.05)
                    if _o3.shape == _conf.shape: _conf = _conf & _o3
                if (_open & ~_conf).any():
                    rep.setdefault("axis_notes", {})["xyz"[_ax] + "_rays"] = "%%d of the %%d opened column(s) read open in ONE cast only (the caster's miss on a thin wall) - not counted; %%d confirmed by five casts" %% (int((_open & ~_conf).sum()), int(_open.sum()), int(_conf.sum()))
                    print("CHECK note: %%s" %% rep["axis_notes"]["xyz"[_ax] + "_rays"], flush=True)
                _open = _conf
            except Exception as _e3: rep.setdefault("axis_notes", {})["xyz"[_ax] + "_rays"] = "offset casts: %%s" %% str(_e3)[:80]
        if _open.any() and _fine_mesh() is not None:      # 31bq B09: a column counts as opened only when the 0.02 mm mesh of the faces near the box agrees; B08 (check-faces): that mesh made only when a column opened
            try:
                _, _, _Ha2 = K.thickness_map(_fine[0], _fine[1], box3, step, axis=_ax); _, _, _Hba2 = K.thickness_map(_fine[2], _fine[3], box3, step, axis=_ax)
                _open2 = (_Hba2 > 0.5) & (_Ha2 < 0.05)
                if _open2.shape == _open.shape and (_open & ~_open2).any():      # 31bq Z (B09 (2)): the fine mesh of the faces NEAR the box is partial - a NOTE on the opened columns, never an AND that can hide a real bore
                    rep.setdefault("axis_notes", {})["xyz"[_ax] + "_fine"] = "%%d of the %%d opened column(s) are closed on the 0.02 mm mesh of the faces near the box (a thin wall the 0.05 mm caster misses?) - the coarse verdict stands; --breakout ok with that measurement when the picture shows a wall" %% (int((_open & ~_open2).sum()), int(_open.sum()))
                    print("CHECK note: %%s" %% rep["axis_notes"]["xyz"[_ax] + "_fine"], flush=True)
            except Exception as _e2: rep.setdefault("axis_notes", {})["xyz"[_ax]] = "fine mesh: %%s" %% str(_e2)[:80]
        _n = int(_open.sum())
    except Exception as _e:
        _n = 0; rep.setdefault("axis_errors", {})["xyz"[_ax]] = str(_e)[:120]
    rep["columns_opened_by_axis"]["xyz"[_ax]] = _n; opened += _n
rep["columns_opened"] = opened
# THE OUTSIDE-THE-BOX SWEEP IS A COLLAR, NOT THE WHOLE PART. the client, 2026-09-10: the whole-footprint
# sweep at 3 mm (10,000 rays over two bodies on every job) had never caught anything and was a
# third of the check's cost. A 3 mm collar at 0.5 mm spacing around every permitted box is where
# an escaped piece lands; the whole-body sweep is `kit check --whole`, run once at `kit close`.
if %(whole)r:
    _bb = _bj["bbox"]; xo = np.arange(_bb[0], _bb[1], 3.0); yo = np.arange(_bb[2], _bb[3], 3.0)
else:
    xo = np.concatenate([np.arange(_b[0] - _collar, _b[1] + _collar + 1e-9, 0.5) for _b in ALLBOX])
    yo = np.concatenate([np.arange(_b[2] - _collar, _b[3] + _collar + 1e-9, 0.5) for _b in ALLBOX])
Z1 = K.R.ZRays(V, T, 2.0); Z0 = K.R.ZRays(Vb, Tb, 2.0); worst = 0.0; where = None
def th(Z, x, y):
    z, _ = Z.hits(x + 0.013, y + 0.007); z = np.sort(z)
    if len(z) < 2: return 0.0
    z = z[:len(z) // 2 * 2]; return float((z[1::2] - z[0::2]).sum())
# EVERY permitted box, not just one. THE BOX IS THE PERMITTED-CHANGE REGION, NOT THE INSPECTED
# ONE: this loop skips points inside it, so a bigger box EXEMPTS more material from the
# "nothing changed outside" test. A test orchestrator, 2026-09-09, on a pair of bolt bores:
# "I had to use a box 87 long to span two 6.6 bores, putting 80 of must-not-change material
# INSIDE the unchecked region. The most standard feature in CAD is the one this instrument checks
# worst." With --box given twice, the two bores get one small box each and the slab between them
# is inspected again.
def _exempt(x, y):
    for _b in ALLBOX:
        if _b[0] <= x <= _b[1] and _b[2] <= y <= _b[3]: return True
    return False
for x in xo:
    for y in yo:
        if _exempt(x, y): continue
        d = abs(th(Z1, x, y) - th(Z0, x, y))
        if d > worst: worst, where = d, (float(x), float(y))
rep["outside_box_max_change_mm"] = worst; rep["outside_box_where"] = where
print("CHECK step: maps and the outside-box sweep done (worst %%.2f mm), %%.0f s; rendering" %% (worst, _tm.time() - _t0), flush=True)
fails = []
if not rep["valid"]: fails.append("invalid shape")
_SOLX = %(solids_exp)r      # 31bw (TB6c F2): bound to a name ONCE - the literal form `187 if 187 is not None` had FreeCAD's Python print a SyntaxWarning twice per check
rep["solids_expected"] = _SOLX if _SOLX is not None else rep["solids_base"]      # 31bw B4 (TB6 F4 / F5): the count the edit INTENDS (the card's `Expected: ... solids N` / --expect-solids), else the base's own - one stays one, a compound keeps its count
if rep["solids"] == 0: fails.append("no solid in the result")
elif rep["solids"] != rep["solids_expected"]:
    fails.append("%%d solids where %%d were expected (%%s) - an edit never changes the body count by accident: a pattern of separate copies, a cut that removes whole solids or a fuse that joins touching ones STATES its count on the card (`Expected: ... solids N`) or by --expect-solids N; a compound base whose cache record predates 31bw reads as one solid - delete claude_code\\jobs\\_tess_cache\\<its md5>.json and check again"
                 %% (rep["solids"], rep["solids_expected"], ("the card's figure" if _SOLX is not None else ("the base is one solid" if rep["solids_base"] == 1 else "the base's own %%d" %% rep["solids_base"]))))
if not ok: fails.append("BOP check: " + msg[:100])
# 31bp fix 7c: WHICH RULER LIES - when the kernel's delta and the mesh's disagree, a THIRD measurement decides: both bodies meshed again at half the
# deflection. The two meshes' deltas agreeing while the kernel's stands apart = Part.Volume is no ruler on this body (a sewn body's tolerance edges and
# touching faces make it wander; reinsert measures by the mesh for the same reason): the mesh delta is the measurement, the disagreement a NOTE on
# record. The two meshes disagreeing with each other too = the FAIL stands and names both. (The base's own kernel-to-mesh gap is no calibration: every
# healthy body has one - the tessellation's error, thousands of mm3 on a litre - and it cancels between base and new.)
_tol_v = max(50.0, 0.05 * abs(rep["dvol_tess"]))
if abs(rep["dvol_kernel"] - rep["dvol_tess"]) > _tol_v:
    _dt2 = None
    try:
        print("CHECK step: the kernel's and the mesh's volume deltas disagree (%%+.0f vs %%+.0f) - both bodies meshed again at half the deflection to see which ruler lies ..." %% (rep["dvol_kernel"], rep["dvol_tess"]), flush=True)
        _V2, _T2, _ = K.R.tess_shape(res, dev=0.025)
        _vbh = _bj.get("vol_tess_0.025")      # 31bq B08 (check-faces): the base's 0.025 mm mesh volume joins its cache record the first time a check needs it - the base B-rep is not loaded again for it (10.4-10.8 s on R31)
        if _vbh is None:
            _b2 = K.load(%(base)r); _Vb2, _Tb2, _ = K.R.tess_shape(_b2, dev=0.025); _vbh = float(K.R.div_volume(np.asarray(_Vb2, float), np.asarray(_Tb2, int))); del _b2, _Vb2, _Tb2
            _bj["vol_tess_0.025"] = _vbh
            try:
                if _bj_path: _rec_save(_bj_path, _bj)      # 31bq B08 C3: never onto a record whose npz this check could not write
            except Exception as _es: print("CHECK note: the base's 0.025 mm mesh volume was not cached (%%s)" %% str(_es)[:80], flush=True)
        else: print("CHECK step: the base's 0.025 mm mesh volume from its cache record (%%.1f mm3) - the base B-rep not loaded for it" %% float(_vbh), flush=True)
        _dt2 = float(K.R.div_volume(np.asarray(_V2, float), np.asarray(_T2, int))) - float(_vbh)
        del _V2, _T2
    except Exception as _e2:
        print("CHECK note: the second mesh failed (%%s)" %% str(_e2)[:80], flush=True)
    rep["volume_ruler"] = {"dvol_kernel": rep["dvol_kernel"], "dvol_tess": rep["dvol_tess"], "dvol_tess_half_deflection": _dt2}
    if _dt2 is not None and abs(_dt2 - rep["dvol_tess"]) <= max(100.0, 0.10 * abs(rep["dvol_tess"])):
        rep["volume_note"] = ("Part.Volume is not a ruler on this body: the two meshes agree on the change (%%+.0f at 0.05 mm, %%+.0f at 0.025 mm) and the kernel stands apart (%%+.0f) - "
                              "the mesh delta is the measurement; the kernel's is not counted (a sewn body's tolerance edges and touching faces make Part.Volume wander)") %% (rep["dvol_tess"], _dt2, rep["dvol_kernel"])
        print("CHECK note: " + rep["volume_note"], flush=True)
    else:
        fails.append("kernel and tessellation volumes disagree: %%+.0f vs %%+.0f%%s" %% (rep["dvol_kernel"], rep["dvol_tess"], (" - and the two meshes disagree with each other too (%%+.0f at half the deflection): the tessellation is not to be trusted here either" %% _dt2) if _dt2 is not None else " (the second mesh could not be made)"))
if %(expect)r == "+" and rep["dvol_tess"] <= 0: fails.append("expected material ADDED, volume did not grow")
if %(expect)r == "-" and rep["dvol_tess"] >= 0: fails.append("expected material REMOVED, volume did not shrink")
if rep.get("face_classes"):      # 31bq B08 (check-faces): the budget judges the INSIDE class alone (requirement 4); a FAR face changed fails by name; the walls' splits and the faces on the walls are said above
    _fcl = rep["face_classes"]; _gin = _fcl["new"]["INSIDE"] - _fcl["base"]["INSIDE"]
    if _gin > %(faces)d: fails.append("face count INSIDE the edit region grew by %%d (card allows %%d; inside %%d -> %%d) - the walls' splits (WALL-ADJACENT %%+d), the faces on the walls (%%d -> %%d) and the whole body (%%+d) are not in it (31bq B08)"
                                      %% (_gin, %(faces)d, _fcl["base"]["INSIDE"], _fcl["new"]["INSIDE"], _fcl["new"]["WALL-ADJACENT"] - _fcl["base"]["WALL-ADJACENT"], _fcl["base"]["ON A WALL"], _fcl["new"]["ON A WALL"], rep["faces"] - rep["faces_base"]))
    _fwg = _fcl.get("walls_growth") or {}
    if _fwg.get("over"): fails.append("the faces on or beside the edit region's walls grew by %%d (WALL-ADJACENT %%d -> %%d, ON A WALL %%d -> %%d) - over WALL_GROW_X %%g x (base INSIDE %%d + base WALL-ADJACENT %%d) = %%g: a wall's split leaves a few fragments of each face it cuts; more is growth in the band beside the walls that the budget does not judge (31bq B08 C2; kit check --wall-grow-x <k> sets the lever)"
                                      %% (_fwg["growth"], _fcl["base"]["WALL-ADJACENT"], _fcl["new"]["WALL-ADJACENT"], _fcl["base"]["ON A WALL"], _fcl["new"]["ON A WALL"], _fwg["WALL_GROW_X"], _fcl["base"]["INSIDE"], _fcl["base"]["WALL-ADJACENT"], _fwg["limit"]))
    _ffr = _fcl["far"]
    if _ffr["changed"]: fails.append("%%d face(s) changed far from every edit region box - nothing may change there: the far faces %%d -> %%d; %%d not in the base (new or moved: faces %%s at %%s), %%d of the base's gone (base faces %%s at %%s) - matched by the mesh centroid within %%g mm and the area within %%g (31bq B08)"
                                     %% (_ffr["changed"], _ffr["base"], _ffr["new"], _ffr["n_new_or_moved"], _ffr["new_or_moved"][:6], _ffr["new_or_moved_at"][:3], _ffr["n_gone"], _ffr["gone"][:6], _ffr["gone_at"][:3], _FFAR_C, _FFAR_A))
elif rep["faces"] - rep["faces_base"] > %(faces)d: fails.append("face count grew by %%d (card allows %%d) - the whole body's growth: the faces by where they lie were NOT TAKEN (%%s)" %% (rep["faces"] - rep["faces_base"], %(faces)d, rep.get("face_classes_not_taken", "?")))
# 31bq B16: a self-intersection the build itself recorded (skin\solid_c.json: faces a x b, the section's length) over the 0.30 mm print tolerance fails the check
try:
    _sic = %(sic)r
    if _sic and os.path.isfile(_sic):
        try:
            _sjj = json.load(open(_sic, encoding="utf-8"))
            if not isinstance(_sjj, dict): raise ValueError("it is JSON but not an object: a %%s" %% type(_sjj).__name__)      # R7W tester-findings (T4 C 8 / C11): a list, a number or null is no record - a list had died in .get() under the outer except (a note and a PASS), [] / null had read as {}
        except (OSError, ValueError) as _erd:      # 31bq R7d (C 8): a record that EXISTS and cannot be read is no clear - it had been a note and a PASS
            fails.append("skin-build's self-intersection record (skin\\solid_c.json) exists and cannot be read (%%s) - the piece's self-intersection is not judged, which is no pass: build again (31bq R7d)" %% str(_erd)[:80]); raise
        _si = []
        for x_ in (_sjj.get("self_intersections") or []):      # 31bq R7d (C 8): each entry parsed by itself - a bad entry is counted as DEEP, never dropped with the whole list
            try: _si.append((int(x_[0]), int(x_[1]), float(x_[2]), (float(x_[3]) if (len(x_) > 3 and x_[3] is not None) else None)))
            except (TypeError, ValueError, IndexError): _si.append((x_[0] if len(x_) > 0 else -1, x_[1] if len(x_) > 1 else -1, float("nan"), float("nan")))      # 31bq Z: [a, b, length, depth]; NN: a None depth is UNMEASURED
        rep["self_intersections"] = _si
        _other_piece = False      # 31bq R5d (round 5's C7, NEW #30): the record is tied to the piece in the body FIRST - another piece's record judges nothing of this one (its crossings and its faces had been printed as the body's piece)
        try:      # 31bq PP: the record tied to the piece that went INTO the body (REBUILD_reinsert.json piece_md5; else skin\piece_skin.brep) - a stale record was judged as the current one
            import hashlib as _hlj
            _pmj = _sjj.get("piece_md5"); _rij = os.path.join(os.path.dirname(os.path.dirname(_sic)), "REBUILD_reinsert.json")
            _pin = (json.load(open(_rij, encoding="utf-8")) or {}).get("piece_md5") if os.path.isfile(_rij) else None
            if not _pin:
                _pfj = os.path.join(os.path.dirname(_sic), "piece_skin.brep"); _pin = _hlj.md5(open(_pfj, "rb").read()).hexdigest() if os.path.isfile(_pfj) else None
            if _pmj and _pin and _pmj != _pin:
                fails.append("skin-build's self-intersection record is ANOTHER piece's (its piece_md5 %%s; the piece in the body %%s) - the piece is not judged by it: build again, or restore the build that made it (31bq PP)" %% (str(_pmj)[:8], str(_pin)[:8])); _other_piece = True
            elif not _pmj: print("CHECK note: skin-build's record names no piece (no piece_md5 - an older build): it is judged as this piece's unchecked (31bq PP)", flush=True)
        except Exception as _epm: print("CHECK note: the record's piece could not be compared (%%s)" %% str(_epm)[:60], flush=True)
        if not _other_piece:
            _sis0 = bool(_sjj.get("check_selfintersect") or "SelfIntersect" in str(_sjj.get("check", "")))      # 31bq R6a (B07 rem 2): the build's own check(True) called a crossing
            _dd = lambda x_: ("the record's entry is NO NUMBER (%%s) - counted as deep" %% (str(x_)[:40],)) if (x_[3] is not None and x_[3] != x_[3]) else (("%%.2f mm deep, %%.2f mm along" %% (x_[3], x_[2])) if x_[3] is not None else ("the depth UNMEASURED, %%.2f mm along%%s" %% (x_[2], " - the build's check(True) says SelfIntersect: not cleared" if _sis0 else "")))      # 31bq PP: an unmeasured depth is said as such ("depth not recorded deep" before); R7d (3): a non-number entry said in words
            _big = [x_ for x_ in _si if not ((x_[3] if x_[3] is not None else (float("nan") if _sis0 else -1.0)) <= 0.30)]      # 31bq PP: a non-number is never shallow; R6a: an unmeasured depth under a check(True) that says SelfIntersect is no pass; R7d (C 5): without SelfIntersect an unmeasured depth is NOTED whatever its length (it had been judged by its length, against R6a's own record)
            _bm = [x_ for x_ in _big if x_[3] is not None]; _bu = [x_ for x_ in _big if x_[3] is None]      # 31bq R7a (verify-R6 on R6a): the MEASURED crossings over the tolerance apart from the UNMEASURED - one text had called both "beyond the print tolerance" (fill15's two unmeasured 0.14 mm crossings read 0.00 mm deep in the current build)
            if _bm: fails.append("the piece SELF-INTERSECTS beyond the print tolerance (0.30 mm): %%s - a face runs through its neighbour (skin-build's record)" %% ", ".join("faces %%d x %%d (%%s)" %% (x_[0], x_[1], _dd(x_)) for x_ in _bm[:6]))
            if _bu: fails.append("%%d crossing(s) of the piece have an UNMEASURED depth and the build's own check(True) says SelfIntersect - NOT CLEARED: nothing measured them under the 0.30 mm print tolerance (a short crossing can be deep); %%s - the build could not measure them, or its record predates the depth measurement: skin-build again with the current kit measures every crossing's depth, and a depth it reads under 0.30 mm clears (31bq R6a / R7a)" %% (len(_bu), ", ".join("faces %%d x %%d (%%.2f mm along)" %% (x_[0], x_[1], x_[2]) for x_ in _bu[:6])))
            else:
                _sm = [x_ for x_ in _si if x_[3] is not None]; _su = [x_ for x_ in _si if x_[3] is None]      # 31bq R5d (B16 (e)): an unmeasured depth is listed apart - it is judged by its length, not measured under the tolerance
                if _sm: print("CHECK note: %%d self-touch(es) / coincident overlap(s) under the print tolerance in the piece (%%s)" %% (len(_sm), ", ".join("%%d x %%d %%s" %% (x_[0], x_[1], _dd(x_)) for x_ in _sm[:6])), flush=True)
                if _su: print("CHECK note: %%d crossing(s) whose depth is UNMEASURED - the build's check(True) does not say SelfIntersect, so they are noted, not judged: %%s (31bq R6a)" %% (len(_su), ", ".join("%%d x %%d %%.2f mm along" %% (x_[0], x_[1], x_[2]) for x_ in _su[:6])), flush=True)
            _sisj = _sjj.get("check_selfintersect") or "SelfIntersect" in str(_sjj.get("check", ""))
            try: _unmp_ = int(_sjj.get("si_unmeasured_pairs") or 0)
            except (TypeError, ValueError): _unmp_ = 1
            if _unmp_ and _sisj: fails.append("%%d face pair(s) of the piece could not be measured for a crossing and the build's own check(True) says SelfIntersect - NOT CLEARED (the reinsert gate refuses the same record; 31bq R7d)" %% _unmp_)      # 31bq R7d (C 3): the same rule as the gate
            elif _unmp_: print("CHECK note: %%d face pair(s) of the piece could not be measured for a crossing (skin-build's record) - unmeasured, not clear" %% _unmp_, flush=True)      # 31bq NN (B16 (b))
            if ("si_searched" in _sjj) and not _sjj.get("si_searched") and _sisj: fails.append("check(True) says SelfIntersect and skin-build's crossing search did not complete - the crossing is not measured (31bq NN)")
            elif ("si_searched" in _sjj) and not _sjj.get("si_searched"): print("CHECK note: skin-build's crossing search did not complete - the piece's self-intersection is unmeasured, not clear (31bq PP)", flush=True)
            elif "si_searched" not in _sjj and "self_intersections" in _sjj: print("CHECK note: skin-build's record predates the crossing search's completion flag (an older build) - its crossing list is read as it stands (31bq R5d)", flush=True)
            if "self_intersections" not in _sjj: print("CHECK note: skin-build's record holds no crossing list (an older build) - the piece's self-intersection is NOT judged here (31bq PP)", flush=True)
            _sfj = list(_sjj.get("si_self_faces") or []); _sfj_how = "their own check(True) says SelfIntersect"
            if not _sfj and "si_self_faces" not in _sjj:      # 31bq R5d (B16 (e)): an older record - the faces its own check_faces marks SelfIntersect
                _sfj = [b_.get("face") for b_ in (_sjj.get("check_faces") or []) if "SelfIntersect" in str(b_.get("check", ""))]; _sfj_how = "the record's check_faces marks SelfIntersect - an older record with no si_self_faces"
            if _sfj and _sisj: fails.append("%%d face(s) of the piece cross THEMSELVES (%%s; no depth is measured for a fold) - a fold is no cosmetic and BOP_OK at the reinsert is no ruling on the geometry: %%s%%s (31bq R7d; the reinsert gate refuses the same record)" %% (len(_sfj), _sfj_how, _sfj[:12], (" +%%d more" %% (len(_sfj) - 12)) if len(_sfj) > 12 else ""))      # 31bq R7d (C 3): a FAIL, as at the gate
            elif _sfj: print("CHECK note: %%d face(s) of the piece cross THEMSELVES (%%s; no depth is measured for them): %%s%%s (31bq PP)" %% (len(_sfj), _sfj_how, _sfj[:12], (" +%%d more" %% (len(_sfj) - 12)) if len(_sfj) > 12 else ""), flush=True)      # 31bq R5d (NEW #25): the list whole (it was cut at 8 with no word)
            # 31bq R7d (C 3): THE PIECE'S OWN EDGE GAP (the build's edge_off_max, the pcurve's gap included) against the client's 0.02 - unless the body's reinsert recorded a BOP_OK, said with its reason.
            # R7W tester-findings (T4 C 3 - C9 / C10): a gap the record does not give as a number (absent - a build before NN's measured gap -, null, text, NaN, a bool) is
            # NOT READ, and a gap not read is NOT CLEARED: a FAIL unless the reinsert recorded a BOP_OK (then a note with its reason, as above) - it had been
            # `except (TypeError, ValueError): pass`, a PASS with no word, where the reinsert gate reads the same record as no cosmetic
            _bopok_j = None
            try:
                _rij_g = os.path.join(os.path.dirname(os.path.dirname(_sic)), "REBUILD_reinsert.json")
                _rrj_g = json.load(open(_rij_g, encoding="utf-8")) if os.path.isfile(_rij_g) else None
                _bopok_j = _rrj_g.get("bop_ok") if isinstance(_rrj_g, dict) else None
            except (OSError, ValueError): _bopok_j = None
            # R7W tester-findings (6) (C-10, M12): the edges / pcurves skin-build could NOT measure (edge_gaps_unmeasured) - edge_off_max is then over the rest only: the
            # gaps are UNMEASURED, NOT CLEARED (R7a / R7d's shape) - a FAIL unless the reinsert recorded a BOP_OK (then a note with its reason); no key = an older build, said
            if "edge_gaps_unmeasured" in _sjj:
                _egu_raw = _sjj.get("edge_gaps_unmeasured")
                try: _egu_j = 1 if isinstance(_egu_raw, bool) else int(float(_egu_raw))
                except (TypeError, ValueError, OverflowError): _egu_j = 1      # a count that is no number: unmeasured, never 0
                rep["edge_gaps_unmeasured"] = _egu_j
                if _egu_j and _bopok_j: print("CHECK note: %%d edge gap(s) of the piece were NOT MEASURED by skin-build (edge_gaps_unmeasured %%s) - it went in under BOP_OK: %%s (R7W tester-findings (6))" %% (_egu_j, str(_sjj.get("edge_gaps_unmeasured_detail") or _egu_raw)[:80], str(_bopok_j)[:160]), flush=True)
                elif _egu_j: fails.append("%%d edge gap(s) of the piece were NOT MEASURED by skin-build (edge_gaps_unmeasured %%s; its edge_off_max is over the rest only) - NOT CLEARED under the client's 0.02 mm bound, and no BOP_OK recorded by the reinsert for it (the reinsert gate refuses the same record; R7W tester-findings (6))" %% (_egu_j, str(_sjj.get("edge_gaps_unmeasured_detail") or _egu_raw)[:80]))
            elif "edge_off_max" in _sjj: print("CHECK note: skin-build's record predates the unmeasured-gap count (no edge_gaps_unmeasured - an older build): its edge_off_max is read as it stands (R7W tester-findings (6))", flush=True)
            _gap_raw = _sjj.get("edge_off_max")
            try: _gap_j = None if isinstance(_gap_raw, bool) else float(_gap_raw)
            except (TypeError, ValueError): _gap_j = None
            if _gap_j is not None and _gap_j != _gap_j: _gap_j = None      # NaN
            if _gap_j is None:
                _gap_what = "holds no edge_off_max (a build before the measured gap - 31bq NN)" if "edge_off_max" not in _sjj else ("gives edge_off_max as %%s - no number" %% repr(_gap_raw)[:40])
                rep["edge_gap_not_read"] = _gap_what
                if _bopok_j: print("CHECK note: the piece's edge gap was NOT READ (skin-build's record %%s) - it went in under BOP_OK: %%s (R7W tester-findings)" %% (_gap_what, str(_bopok_j)[:160]), flush=True)
                else: fails.append("the piece's edge gap was NOT READ - skin-build's record %%s: NOT CLEARED under the client's 0.02 mm bound (Q2, 2026-10-19), and no BOP_OK recorded by the reinsert for it (the reinsert gate reads the same record as no cosmetic) - skin-build again with the current kit records the gap (R7W tester-findings; 31bq R7d: a record that cannot be read is no clear)" %% _gap_what)
            elif _gap_j > 0.02 and _bopok_j: print("CHECK note: the piece's edges are up to %%.3f mm off their faces (skin-build's edge_off_max; the client's Q2 bound 0.02) - it went in under BOP_OK: %%s (31bq R7d)" %% (_gap_j, str(_bopok_j)[:160]), flush=True)
            elif _gap_j > 0.02: fails.append("the piece's edges are up to %%.3f mm off their faces (skin-build's edge_off_max, the pcurve's gap included) - over the client's 0.02 mm bound (Q2, 2026-10-19) and no BOP_OK recorded by the reinsert for it (31bq R7d)" %% _gap_j)
    elif _sic and os.path.isdir(os.path.dirname(_sic)): print("CHECK note: the job's skin folder holds no solid_c.json - skin-build's self-intersection record is NOT judged here (a missing or renamed record - 31bq NN (B16 (e)))", flush=True)
except Exception as _e: print("CHECK note: the build's self-intersection record was not read (%%s)" %% str(_e)[:80], flush=True)
if worst > 0.3: fails.append("material changed OUTSIDE the box: %%.1f mm at %%s" %% (worst, where))

# PUNCH-THROUGH IS CHECKED ESPECIALLY ON CUTS. It used to be skipped whenever --expect was "-",
# which is what EVERY cut declares - so the one check METHOD.md 5 promises against a new opening
# was off for exactly the operation that can make one. A test orchestrator, 2026-09-09: F2 printed
# `opened 74` and passed without comment.
#
# The card is what says whether breakout is allowed, so --breakout is what turns it off:
#   (absent)          no new opening may appear. The default, and the safe direction.
#   --breakout ok     this feature is MEANT to go through; report the count and pass.
# Probed on all three axes, not just z (see kitlib.thickness_map): F1 punched a 24x16 slot clean
# through a wall sideways and the z-only map reported `opened 0`.
if opened > 0 and %(breakout)r != "ok":
    fails.append("%%d column(s) lost ALL material - a NEW OPENING. If the card says no punch-through this is the failure it names; if the feature is MEANT to go through, say so: --breakout ok" %% opened)
elif opened > 0:
    print("   note: %%d column(s) opened; --breakout ok was given (the card says this feature goes through)." %% opened)
rep["fails"] = fails; rep["PASS"] = (len(fails) == 0)
# NO RENDERS HERE: the card's After line already made the boxed look this job is judged on; a
# second set of seven frames was a minute of the check for a picture nobody opened.
rep["pictures"] = []
json.dump(rep, open(%(out)r + "/CHECK.json", "w"), indent=1)
print("CHECK %%s | valid %%s solids %%d (expected %%d, base %%d) faces %%d (base %%d) | dvol kernel %%+.0f tess %%+.0f | opened %%d | outside-box change %%.2f mm | bop %%s | %%.0f s" %% ("PASS" if rep["PASS"] else "FAIL", rep["valid"], rep["solids"], rep["solids_expected"], rep["solids_base"], rep["faces"], rep["faces_base"], rep["dvol_kernel"], rep["dvol_tess"], opened, worst, "ok" if %(bop)r and ok else ("FAIL" if %(bop)r else "not run"), _tm.time() - _t0))
for f in fails: print("   FAIL:", f)
''' % {"sic": (os.path.join(ROOT, "claude_code", "jobs", str(_jb), "skin", "solid_c.json") if _jb else ""), "here": HERE, "root": ROOT, "res": res, "base": base, "bx": bx, "expect": expect, "out": out, "name": name, "solids_exp": solids_exp, "faces": faces, "breakout": a.get("--breakout", "no"), "allbox": allbox,
       "jobdir": (os.path.join(ROOT, "claude_code", "jobs", _jb) if _jb else ""),
       "whole": bool(whole_flag), "collar": float(a.get("--collar", 3.0)), "bop": bool(bop_flag), "because": because or "", "wallx": wallx}
    rc = _fc(code, out, "check")
    # kit accept
    # kit accept
    jb = _opt(args, "--job")
    try:
        if rc == 0 and not (json.load(open(os.path.join(out, "CHECK.json"), encoding="utf-8")) or {}).get("PASS"):
            rc = 2
    except Exception:
        pass
    if jb:
        try:
            rep = json.load(open(os.path.join(out, "CHECK.json"), encoding="utf-8"))
            if rep.get("PASS"):
                G.job_mark(ROOT, jb, "checked", time.strftime("%Y-%m-%d %H:%M:%S"))
                G.job_mark(ROOT, jb, "check_json", os.path.join(out, "CHECK.json"))
                print("[leangate] job %s marked CHECKED. Next: kit look %s --code <frame>=<CODE> ... --says \"...\" (the card's After frames read back), then kit accept %s --review <dir> (31bx R1 D10)." % (jb, jb, jb))
            else:
                print("[leangate] job %s NOT marked checked: the check FAILED. Fix the piece, "
                      "do not re-run\n[leangate]   the check hoping for a different answer." % jb)
                try:
                    if str((G.job(ROOT, jb) or {}).get("edit_type", "")).lower() == "move" and any("NEW OPENING" in str(f_) for f_ in (rep.get("fails") or [])):
                        print("[leangate]   this job is a MOVE: the footprint the part vacated reads as a new opening - run the check again with --breakout ok \"the move vacates its footprint\" (31bx R1 F7)")
                except Exception:
                    pass
        except Exception as exc:
            print("[leangate] could not record the check for job %r (%s). `kit accept` will "
                  "refuse\n[leangate]   until it can see one." % (jb, exc))
    else:
        print("[leangate] NOTE: no --job given, so nothing was recorded and `kit accept` will "
              "still refuse.\n[leangate]   Re-run as: kit check ... --job <name> --as-orchestrator")
    return rc

def _next_rev():
    """31bq R7W D3: the revision after the newest one this project knows - a bank file R<n>_..., a Deliverables R<n> folder (the project's and the
    scratch root's), the model of record's own name"""
    ns = []
    for d_ in (os.path.join(ROOT, "claude_code", "bank"), os.path.join(ROOT, "Deliverables"),
               os.path.join(G.records_root(ROOT), "Deliverables")):
        try:
            for f_ in os.listdir(d_):
                m_ = re.match(r"^R(\d+)(?:_|$)", f_)
                if m_ and (os.path.basename(d_) != "Deliverables" or os.path.isdir(os.path.join(d_, f_, "model"))): ns.append(int(m_.group(1)))
        except OSError:
            pass
    m_ = re.match(r"^R(\d+)_", os.path.basename(str((G.session(ROOT) or {}).get("model_of_record") or "")))
    if m_: ns.append(int(m_.group(1)))
    return "R%d" % ((max(ns) if ns else 0) + 1)


def _apply_body(args, jb):
    """31bq R7W route-end D3: THE BURRITO APPLY. kit apply --job <J> [--rev R<n>] [--no-atlas "<why>"]
    A job whose result is the WHOLE body (the burrito: <job>\\body_new.brep beside REBUILD_reinsert.json - the reinsert sewed the piece into the body of
    record; a trial's body is body_new.brep only by its acceptance) is applied by COPYING that body into the bank under the next revision's name - never
    by a fuse (a whole body fused into the old one brings back what the edit removed; a piece fused in is the boolean the skin route forbids, L100).
    The gate is the one every apply passes (gate_apply: registered, checked, looked, the card's tripwire); then the atlas assignment, the job marked
    applied, the dossiers and the edited atlas regions marked, and the bank file PROMOTED as the model of record (recorded as applied by the job)."""
    jd = os.path.join(ROOT, "claude_code", "jobs", jb); bn = os.path.join(jd, "body_new.brep")
    if not os.path.isfile(bn) or not os.path.isfile(os.path.join(jd, "REBUILD_reinsert.json")):
        print("kit apply REFUSED: --job %s alone applies a job whose RESULT IS THE WHOLE BODY (the burrito: body_new.brep beside REBUILD_reinsert.json) -\n"
              "  %s has %s. A piece is applied with: kit apply <body.brep> <piece.brep> fuse|cut <out.brep> --job <name>"
              % (jb, jd, "no body_new.brep" if not os.path.isfile(bn) else "no REBUILD_reinsert.json")); return 2
    try:
        tj_ = json.load(open(os.path.join(jd, "TRIAL.json"), encoding="utf-8")) if os.path.isfile(os.path.join(jd, "TRIAL.json")) else {}
    except (OSError, ValueError):
        tj_ = {"accepted": False}
    if tj_ and not tj_.get("accepted"):
        print("kit apply REFUSED: %s\\body_new.brep sits beside a TRIAL that was not accepted (TRIAL.json) - a trial's body becomes body_new.brep only by its\n"
              "  acceptance (kit rebuild judge --what trial --verdict ok after its two reviewers)." % jb); return 2
    _j0 = G.job(ROOT, jb) or {}
    if _j0.get("applied_to"):
        print("kit apply REFUSED: job %s was APPLIED already - to %s (at %s). A second apply would bank the same body again under the next revision;\n"
              "  a different result is a new job (kit newjob) over the model of record." % (jb, _j0.get("applied_to"), _j0.get("applied"))); return 2
    if _j0 and not _j0.get("applied"):
        print("kit apply REFUSED: job %s was not ACCEPTED - kit accept %s --review <its COMPLETE review: an accepted trial's review_body\\> first (the same gate,\n"
              "  the review it names, the rebuild record into the dossier); the card's order: kit check -> kit look -> kit accept -> kit apply." % (jb, jb)); return 2
    G.gate_apply(ROOT, jb, _opt(args, "--check"))
    if G.atlas_needs_assignment(ROOT) and not G.atlas_assignment(ROOT, jb):
        print("kit apply REFUSED: job %s adds B-rep geometry and the atlas does not say which section it belongs to.\n  kit atlas assign %s --to <existing region>" % (jb, jb))
        return 2
    rev = (_opt(args, "--rev", "") or _next_rev()).strip()
    if not re.match(r"^R\d+$", rev):
        print("kit apply REFUSED: --rev is R<n> (R32), not %r" % rev); return 2
    bank = os.path.join(ROOT, "claude_code", "bank"); os.makedirs(bank, exist_ok=True)
    dst = os.path.join(bank, "%s_BODY_MASTER.brep" % rev)
    if os.path.exists(dst):
        print("kit apply REFUSED: %s already exists - the bank never overwrites a model; --rev <the next free R<n>>" % dst); return 2
    tmp = dst + ".tmp"
    shutil.copyfile(bn, tmp)
    if _md5(tmp) != _md5(bn):
        os.remove(tmp); print("kit apply REFUSED: the copy into the bank does not match body_new.brep - nothing applied"); return 2
    os.replace(tmp, dst)
    G.job_mark(ROOT, jb, "applied_to", os.path.abspath(dst))
    print("[leangate] %s APPLIED: %s\\body_new.brep -> %s (a copy, md5 %s - the burrito's result is the whole body; nothing fused)" % (jb, jb, dst, _md5(dst)[:8]))
    try:
        _j = G.job(ROOT, jb) or {}
        if _j.get("box"):
            D.mark_stale(ROOT, jb, _j["box"])
        _rn = [r_ for r_ in (_j.get("regions") or "").split(",") if r_]
        if _rn:
            _hit = G.atlas_mark_edited(ROOT, _rn, jb, os.path.abspath(dst))
            if _hit:
                print("[atlas] edited: %s - their maps (face lists, pieces) predate this apply; `kit atlas status`." % ", ".join(_hit))
            _owe = sorted(G.atlas_recreate_owed(ROOT))
            if _owe:
                print("[atlas] RECREATE OWED before delivery (frozen regions an edit reached): %s" % ", ".join(_owe))
    except Exception as _e:
        print("[atlas / dossier] could not record the edited regions (%s)." % _e)
    pa = [dst, "--note", "kit apply --job %s (the burrito's body_new.brep)" % jb, "--applied-by", jb]
    if _opt(args, "--no-atlas", ""):
        pa += ["--no-atlas", _opt(args, "--no-atlas")]
    return cmd_promote(pa)


def cmd_apply(args):
    # kit accept
    # kit accept
    pos = [t for t in args if not t.startswith("-")]
    _ov = set(v_ for v_ in (_opt(args, k_) for k_ in ("--job", "--rev", "--check", "--no-atlas", "--note")) if v_)
    if _opt(args, "--job") and not [t for t in pos if t not in _ov]:
        return _apply_body(args, _opt(args, "--job"))
    if len(pos) < 4:
        print("kit apply <body.brep> <piece.brep> fuse|cut <out.brep> --job <name>\n"
              "kit apply --job <name> [--rev R<n>] [--no-atlas \"<why>\"]   a job whose result is the WHOLE body (the burrito's body_new.brep)")
        return 2
    body, piece, op, out = pos[:4]
    jb = _opt(args, "--job")
    if not jb:
        print("kit apply REFUSED: --job <name> is required.\n"
              "  This is the last step before the model of record, and the gate that stands in "
              "front of it\n  needs to know WHICH job it is judging - whether it was checked, "
              "whether you looked at it,\n  and what its card expected. Without that there is "
              "nothing to check against.\n"
              "  If the job is not registered:  kit job <name> --type <edit_type> --card <path>")
        return 2
    G.gate_apply(ROOT, jb, _opt(args, "--check"))
    scratch = os.path.join(G.store(ROOT), "scratch")
    os.makedirs(scratch, exist_ok=True)
    code = ("import sys; sys.path.insert(0, %r); import kitlib as K\n"
            "b = K.load(%r); p = K.load(%r)\n"
            "r = K.fuse(b, p, 'piece') if %r == 'fuse' else K.cut(b, p, 'piece')\n"
            "K.save(r, %r); print('applied -> %%s' %% %r)\n") % (HERE, body, piece, op, out, out)
    if G.atlas_needs_assignment(ROOT) and not G.atlas_assignment(ROOT, jb):
        print("kit apply REFUSED: job %s adds B-rep geometry and the atlas does not say which section it belongs to." % jb)
        print("  kit atlas assign %s --to <existing region>" % jb)
        print("  kit atlas assign %s --new <name> --what \"<its physical definition>\"   (then announce it to the client)" % jb)
        print("  the client, 2026-09-22: all new geometry goes to an existing section, or a new section is announced.")
        return 2
    rc = _fc(code, scratch, "apply")
    if rc == 0:
        G.job_mark(ROOT, jb, "applied_to", os.path.abspath(out))
        print("[leangate] %s applied. If this is the new model of record, record it:\n"
              "[leangate]     kit promote %s" % (jb, out))
        try:
            _j = G.job(ROOT, jb) or {}
            if _j.get("box"):
                D.mark_stale(ROOT, jb, _j["box"])
        except Exception as _e:
            print("[dossier] could not mark dossiers stale (%s) - run `kit dossier list` and judge by box." % _e)
        # confirmed  recorded
        try:
            _j = G.job(ROOT, jb) or {}
            _rn = [r_ for r_ in (_j.get("regions") or "").split(",") if r_]
            if _rn:
                _hit = G.atlas_mark_edited(ROOT, _rn, jb, os.path.abspath(out))
                if _hit:
                    print("[atlas] edited: %s - their maps (face lists, pieces) predate this apply; `kit atlas status`."
                          % ", ".join(_hit))
                _owe = sorted(G.atlas_recreate_owed(ROOT))
                if _owe:
                    print("[atlas] RECREATE OWED before delivery (frozen regions an edit reached): %s\n"
                          "        `kit atlas recreated <region> --result <final mesh>` when the edits are done." % ", ".join(_owe))
        except Exception as _e:
            print("[atlas] could not record the edited regions (%s)." % _e)
    return rc

_MEASURE_USAGE = ("kit measure <shape.brep> bbox | faces [--min A] [--max A] [--box ...] [--only n,n] "
                  "[--normal x,y,z [--tol-deg N]] | export [--dev D] | "
                  "section x|y|z c [--out png] [--box x0 x1 y0 y1 z0 z1] [--grid G] [--profile --step S] | rays z x y [--grid ...] | "
                  "dihedral --box x0 x1 y0 y1 z0 z1 [--min-len L] [--worst N] [--control]   [--dossier <name>] --as-orchestrator\n"
                  "  <shape.brep> is ANY brep - the model of record, a job's result.brep, a result_REFUSED.brep, a piece.")


def cmd_measure(args):
    control = "--control" in args; profile_flag = "--profile" in args
    args = [t for t in args if t not in ("--control", "--profile")]
    dossier = None
    if "--dossier" in args:
        _i = args.index("--dossier")
        if _i + 1 < len(args):
            dossier = args[_i + 1]
        args = args[:_i] + args[_i + 2:]
    a = _kv(args)
    # kit measure  kit measure
    if "--help" in args or "-h" in args or len(a["_"]) < 2:
        print(_MEASURE_USAGE)
        return 2
    shape = a["_"][0]; what = a["_"][1]; rest = a["_"][2:]
    if not os.path.isfile(shape):
        print("kit measure: no such shape file: %s\n%s" % (shape, _MEASURE_USAGE))
        return 2
    if True:
        if what == "rays" and not dossier:
            print("kit measure REFUSED: rays run only into a dossier - add --dossier <name> (kit dossier list),\n"
                  "  or read the dossier's profiles first: kit dossier show <name>. the client: \"No rays. You should\n"
                  "  know what cross section you are looking at from renders ... Only measure as a LAST resort.\"")
            return 2
        if not dossier and what in ("section", "rays", "dihedral", "faces"):
            try:
                _since = int((G._read(G._p(ROOT, G.MEASURES), {}) or {}).get("since_card", 0))
            except Exception:
                _since = 0
            if os.environ.get("KIT_MEASURE_SHUT") == "1":
                print("kit measure REFUSED: %d bare measurements since the last card. The instrument is closed\n"
                      "  until one of: the card is linted (kit card <card> - kit newcard alone does not reopen it), the measurement is filed\n"
                      "  into a dossier (--dossier <name>), or `kit failure --what \"what the render could not answer\" --why ... --fix ... --signature ...`\n"
                      "  (all four fields). The dossier for this region probably already holds the number: kit dossier show <name>."
                      % _since)
                return 2
    code = "import sys; sys.path.insert(0, %r); import kitlib as K, numpy as np\ns = K.load(%r)\n" % (HERE, shape)
    if what == "bbox":
        code += "b = s.BoundBox; print('MEASURE bbox x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f  faces %d  vol %.0f' % (b.XMin,b.XMax,b.YMin,b.YMax,b.ZMin,b.ZMax,len(s.Faces),s.Volume))\n"
    elif what == "faces":
        mn = float(a.get("--min", "0")); mx = float(a.get("--max", "1e30"))
        _bx = a.get("--box"); _box = None
        if _bx:
            _box = [float(t) for t in str(_bx).split()]
            if len(_box) != 6:
                sys.exit("kit measure faces: --box needs SIX numbers x0 x1 y0 y1 z0 z1")
        _only = None
        if a.get("--only"):
            _only = sorted(set(int(t) for t in re.split(r"[,\s]+", str(a["--only"]).strip()) if t))
        _nrm = None
        if a.get("--normal"):
            _nrm = [float(t) for t in re.split(r"[,\s]+", str(a["--normal"]).strip()) if t]
            if len(_nrm) != 3:
                sys.exit("kit measure faces: --normal needs THREE numbers, e.g. --normal 0,0,-1")
            _ln = (_nrm[0] ** 2 + _nrm[1] ** 2 + _nrm[2] ** 2) ** 0.5
            if _ln < 1e-9:
                sys.exit("kit measure faces: --normal is a zero vector")
            _nrm = [c / _ln for c in _nrm]
        # none of the
        _tol = float(a.get("--tol-deg", "10"))
        _census = (
            "_box = __BOX__; _only = __ONLY__; _nrm = __NRM__; _tol = __TOL__\n"
            "def _face_angles(f):\n"
            "    \"\"\"(angle at the midpoint, worst angle over a 3x3 sample), in degrees, against _nrm.\n"
            "    Orientation applied. Returns (None, None) when the normal cannot be taken.\"\"\"\n"
            "    try:\n"
            "        u0, u1, v0_, v1_ = f.ParameterRange\n"
            "    except Exception:\n"
            "        return (None, None)\n"
            "    def _ang(u, v):      # 31bu (T6 F2): the OUTWARD normal, calibrated once (kitlib.outward_normal) - the hand flip on a Reversed face had inverted every one of them\n"
            "        n = K.outward_normal(f, u, v)\n"
            "        if n is None: return None\n"
            "        d = n.x*_nrm[0] + n.y*_nrm[1] + n.z*_nrm[2]\n"
            "        return float(np.degrees(np.arccos(max(-1.0, min(1.0, d)))))\n"
            "    mid = _ang(0.5*(u0+u1), 0.5*(v0_+v1_))\n"
            "    _all = [x for x in (_ang(u0 + (u1-u0)*fu, v0_ + (v1_-v0_)*fv)\n"
            "                        for fu in (0.05, 0.5, 0.95) for fv in (0.05, 0.5, 0.95)) if x is not None]\n"
            "    return (mid, max(_all) if _all else None)\n"
            "def _in(i, f):\n"
            "    if _only is not None and (i + 1) not in _only: return False\n"
            "    if _box is not None:\n"
            "        bb = f.BoundBox\n"
            "        if not (bb.XMax >= _box[0] and bb.XMin <= _box[1] and bb.YMax >= _box[2] and bb.YMin <= _box[3]\n"
            "                and bb.ZMax >= _box[4] and bb.ZMin <= _box[5]): return False\n"
            "    if _nrm is not None:\n"
            "        mid, _w = _face_angles(f)\n"
            "        if mid is None or mid > _tol: return False\n"
            "    return True\n"
            "_idx = [i for i, f in enumerate(s.Faces) if _in(i, f)]\n"
            "_ar = np.array([s.Faces[i].Area for i in _idx]) if _idx else np.zeros(0)\n"
            "_scope = ('in box ' + str(_box)) if _box is not None else ('faces ' + str(_only)) if _only is not None else 'whole body'\n"
            "if _nrm is not None: _scope += '  normal %s within %.1f deg' % (_nrm, _tol)\n"
            "print('CENSUS %s: %d faces (body has %d)  total area %.1f mm2' % (_scope, len(_ar), len(s.Faces), _ar.sum()))\n"
            "if _only is not None and len(_idx) != len(_only):\n"
            "    print('CENSUS WARNING: %d of the %d requested face numbers do not exist on this body (faces run 1..%d)' % (len(_only) - len(_idx), len(_only), len(s.Faces)))\n"
            "if not len(_ar): print('CENSUS ABORT: the selection holds NO faces - an empty set proves nothing (T68). Check the box / numbers.')\n"
            "for _t in (0.05, 0.30, 1.00, 5.00):\n"
            "    _m = _ar < _t\n"
            "    print('CENSUS   under %5.2f mm2: %5d faces (%6.2f pct)  their area %9.3f mm2'\n"
            "          % (_t, _m.sum(), 100.0*_m.sum()/max(1,len(_ar)), _ar[_m].sum()))\n"
            "_n = 0\n"
            "for i in _idx:\n"
            "    f = s.Faces[i]; bb=f.BoundBox; n=f.Surface.__class__.__name__\n"
            "    if __MN__ <= f.Area <= __MX__:\n"
            "        _n += 1\n"
            "        _ang = ''\n"
            "        if _nrm is not None:\n"
            "            _m, _w = _face_angles(f)\n"
            "            _ang = '  n %5.1f deg (worst %5.1f)' % (_m if _m is not None else -1.0, _w if _w is not None else -1.0)\n"
            "        print('Face%d %-10s A=%10.4f x %7.2f..%7.2f y %7.2f..%7.2f z %7.2f..%7.2f%s'\n"
            "              % (i+1,n[:10],f.Area,bb.XMin,bb.XMax,bb.YMin,bb.YMax,bb.ZMin,bb.ZMax,_ang))\n"
            "print('CENSUS listed %d face(s) with area in [%g, %g]' % (_n, __MN__, __MX__))\n"
            "if _nrm is not None and _idx:\n"
            "    _str = [i for i in _idx if (_face_angles(s.Faces[i])[1] or 0.0) > _tol]\n"
            "    if _str:\n"
            "        print('CENSUS WARNING: %d selected face(s) CURVE OUT of the %.1f deg tolerance '\n"
            "              '(kept on their midpoint): %s' % (len(_str), _tol, [i+1 for i in _str][:20]))\n"
            "        print('CENSUS   a face that straddles the boundary is partly in the feature and partly not.')\n"
            "        print('CENSUS   Decide it yourself - tighten --tol-deg, or split the selection by --box.')\n")
        code += (_census.replace("__MN__", repr(mn)).replace("__MX__", repr(mx))
                 .replace("__BOX__", repr(_box)).replace("__ONLY__", repr(_only))
                 .replace("__NRM__", repr(_nrm)).replace("__TOL__", repr(_tol)))
    elif what == "export":
        # open edges
        # open edges
        dev = float(a.get("--dev", "0.02"))
        _exp = (
            "print('EXPORT shape valid=%s  solids=%d  shells=%d  faces=%d  vol=%.1f'\n"
            "      % (s.isValid(), len(s.Solids), len(s.Shells), len(s.Faces), s.Volume))\n"
            "_et = np.array([e.Tolerance for e in s.Edges]); _vt = np.array([v.Tolerance for v in s.Vertexes])\n"
            "print('EXPORT edge tolerance  max %.6f  over 1e-4: %d of %d   vertex tol max %.6f'\n"
            "      % (_et.max(), int((_et > 1e-4).sum()), len(_et), _vt.max()))\n"
            "V,T,F = K.tess(s, __DEV__)\n"
            "print('EXPORT tessellation dev=__DEV__: %d vertices, %d triangles' % (len(V), len(T)))\n"
            "if len(T) == 0:\n"
            "    print('EXPORT ABORT: the tessellation is EMPTY - every result below would be a')\n"
            "    print('EXPORT ABORT: clean answer from an empty set. Nothing is proved.')\n"
            "else:\n"
            "    for _w in (1e-4, 1e-3, 1e-2, 5e-2, 1e-1, 2e-1, 4e-1, 8e-1):\n"
            "        _q = np.round(V / _w).astype(np.int64)\n"
            "        _u, _inv = np.unique(_q, axis=0, return_inverse=True)\n"
            "        _inv = np.asarray(_inv).reshape(-1)   # numpy 2.0 axis-unique shape\n"
            "        _t = _inv[T]\n"
            "        _e = np.concatenate([_t[:, [0,1]], _t[:, [1,2]], _t[:, [2,0]]], axis=0)\n"
            "        _e = np.sort(_e, axis=1)\n"
            "        _ue, _cnt = np.unique(_e, axis=0, return_counts=True)\n"
            "        _open = int((_cnt == 1).sum()); _nm = int((_cnt > 2).sum())\n"
            "        print('EXPORT   weld %6.4f mm: %7d welded verts  %7d edges  OPEN %5d  NON-MANIFOLD %4d  %s'\n"
            "              % (_w, len(_u), len(_ue), _open, _nm,\n"
            "                 'WATERTIGHT' if (_open == 0 and _nm == 0) else 'not watertight'))\n"
            "        if _w == 1e-3:\n"
            "            _ue2, _inv2, _cnt2 = np.unique(_e, axis=0, return_inverse=True, return_counts=True)\n"
            "            _inv2 = np.asarray(_inv2).reshape(-1)\n"
            "            _tri = np.tile(np.arange(len(T)), 3)\n"
            "            _ot = _tri[_cnt2[_inv2] == 1]\n"
            "            _of = np.asarray(F)[_ot]\n"
            "            _fc2 = np.bincount(_of, minlength=len(s.Faces))\n"
            "            _hit = np.nonzero(_fc2)[0]\n"
            "            print('EXPORT open edges touch %d of %d faces' % (len(_hit), len(s.Faces)))\n"
            "            if len(_hit):\n"
            "                _fa = np.array([s.Faces[i].Area for i in _hit])\n"
            "                print('EXPORT   those faces total %.1f mm2; %d of them are under 1 mm2'\n"
            "                      % (_fa.sum(), int((_fa < 1.0).sum())))\n"
            "                _ord = np.argsort(-_fc2[_hit])[:20]\n"
            "                print('EXPORT   worst 20 faces (Face#, open edges, area mm2, surface):')\n"
            "                for _k in _ord:\n"
            "                    _i = _hit[_k]; _f = s.Faces[_i]\n"
            "                    print('EXPORT     Face%-5d %5d open  A=%9.3f  %s'\n"
            "                          % (_i+1, _fc2[_i], _f.Area, _f.Surface.__class__.__name__[:18]))\n"
            "                _top = np.sort(_fc2[_hit])[::-1]\n"
            "                print('EXPORT   worst 20 faces hold %d of %d open-edge uses; worst 100 hold %d'\n"
            "                      % (_top[:20].sum(), _top.sum(), _top[:100].sum()))\n"
            "            _bad = _ue[_cnt == 1]\n"
            "            if len(_bad):\n"
            "                _mid = 0.5 * (_u[_bad[:, 0]] + _u[_bad[:, 1]]) * _w\n"
            "                print('EXPORT open-edge extent  x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f'\n"
            "                      % (_mid[:,0].min(), _mid[:,0].max(), _mid[:,1].min(),\n"
            "                         _mid[:,1].max(), _mid[:,2].min(), _mid[:,2].max()))\n"
            "                _b = np.floor(_mid / 25.0).astype(int)\n"
            "                _ub, _cb = np.unique(_b, axis=0, return_counts=True)\n"
            "                _o = np.argsort(-_cb)[:14]\n"
            "                print('EXPORT open edges by 25 mm cell, worst first '\n"
            "                      '(cell corner x y z, then the count):')\n"
            "                for _k in _o:\n"
            "                    print('EXPORT   cell %7.0f %7.0f %7.0f : %5d open edges'\n"
            "                          % (_ub[_k][0]*25, _ub[_k][1]*25, _ub[_k][2]*25, _cb[_k]))\n"
            "                print('EXPORT   those 14 cells hold %d of %d open edges'\n"
            "                      % (_cb[_o].sum(), _open))\n")
        code += _exp.replace("__DEV__", repr(dev))
    elif what == "section":
        ax = {"x": 0, "y": 1, "z": 2}[rest[0]]; c = float(rest[1])
        out = a.get("--out", "")
        if not out:
            _stem = "section_%s%g%s.png" % (rest[0], c, ("_" + str(a.get("--name"))) if a.get("--name") else "")
            if a.get("--dossier"):
                out = os.path.join(ROOT, "claude_code", "dossier", str(a.get("--dossier")), _stem)
            elif a.get("--job"):
                out = os.path.join(ROOT, "claude_code", "jobs", str(a.get("--job")), _stem)
            else:
                out = os.path.join(G.store(ROOT), "scratch", _stem)
                print("[kit] no --dossier / --job / --out: the picture goes to the kit's scratch (%s) - a measurement worth\n"
                      "      keeping is filed with --dossier <name>" % out)
            os.makedirs(os.path.dirname(out), exist_ok=True)
        bx = a.get("--box"); win = None
        if bx:
            v6 = [float(t) for t in str(bx).split()]
            if len(v6) != 6:
                sys.exit("kit measure section: --box needs SIX numbers x0 x1 y0 y1 z0 z1")
            au, av = [i for i in (0, 1, 2) if i != ax]
            win = ((v6[2 * au], v6[2 * au + 1]), (v6[2 * av], v6[2 * av + 1]))
        grid = float(a.get("--grid", "10" if win is None else "1"))
        prof = profile_flag
        pstep = float(a.get("--step", "1.0"))
        _prof = ""
        if prof and win is not None:
            _prof = (
                "_au, _av = [i for i in (0,1,2) if i != __AX__]\n"
                "_A = segs[:, 0, :]; _B = segs[:, 1, :]\n"
                "print('PROFILE section __AXN__=__C__, u = axis %d, v = axis %d, u %g..%g step %g: material intervals top-down (outer, inner) per station' % (_au, _av, _win[0][0], _win[0][1], __PSTEP__))\n"
                "_u = _win[0][0]\n"
                "while _u <= _win[0][1] + 1e-9:\n"
                "    _lo = np.minimum(_A[:, _au], _B[:, _au]); _hi = np.maximum(_A[:, _au], _B[:, _au])\n"
                "    _m = (_lo <= _u) & (_hi > _u) & (_hi - _lo > 1e-9)\n"
                "    _t = (_u - _A[_m, _au]) / (_B[_m, _au] - _A[_m, _au])\n"
                "    _v = np.sort(_A[_m, _av] + _t * (_B[_m, _av] - _A[_m, _av]))[::-1]\n"
                "    _pp = []\n"
                "    for _i in range(0, len(_v) - 1, 2):\n"
                "        _hi, _lo = _v[_i], _v[_i + 1]\n"
                "        if _hi < _win[1][0] or _lo > _win[1][1]: continue\n"
                "        _pp.append('[%.2f%s %.2f%s]' % (min(_hi, _win[1][1]), '+' if _hi > _win[1][1] else '', max(_lo, _win[1][0]), '+' if _lo < _win[1][0] else ''))\n"
                "    print('PROFILE u %8.2f : %s' % (_u, ' '.join(_pp) if _pp else 'MISS'))\n"
                "    _u += __PSTEP__\n").replace("__PSTEP__", repr(pstep))
        _sec = (
            "V,T,F = K.tess(s); segs = K.R.section_segs(V,T,__AX__,__C__)\n"
            "_win = __WIN__\n" + _prof +
            "if _win: print('MEASURE section window u %g..%g  v %g..%g  -> %.3f mm/px (grid __GRID__)'\n"
            "               % (_win[0][0], _win[0][1], _win[1][0], _win[1][1], (_win[0][1]-_win[0][0])/1200.0))\n"
            "K.R.draw_section_filled(__OUT__, [(segs,(150,150,160))], [(segs,(240,240,240),1)], __AX__, 'section __AXN__ = __C__', W=1200, grid=__GRID__, window=_win)\n"
            "P = segs.reshape(-1,3); print('MEASURE section __AXN__=__C__: %d segments, extent ' % len(segs), np.round(P.min(0),2), np.round(P.max(0),2), '->', __OUT__)\n")
        code += (_sec.replace("__AXN__", rest[0]).replace("__AX__", repr(ax)).replace("__C__", repr(c))
                 .replace("__OUT__", repr(out)).replace("__WIN__", repr(win)).replace("__GRID__", repr(grid)))
    elif what == "rays":
        grid = a.get("--grid")
        if grid:
            g = [float(t) for t in str(grid).split()]
            if len(g) != 4:
                sys.exit("kit measure rays --grid needs FOUR numbers x0 x1 y0 y1 (and --step S, default 1)")
            step = float(a.get("--step", "1"))
            code += ("V,T,F = K.tess(s); Z = K.R.ZRays(V,T,2.0)\n"
                     "_xs = np.arange(%r, %r + 1e-9, %r); _ys = np.arange(%r, %r + 1e-9, %r)\n"
                     "print('MEASURE z-ray grid x %%g..%%g y %%g..%%g step %%g: %%d rays (hits are z values, bottom to top; a gap between pairs is air)' %% (_xs[0], _xs[-1], _ys[0], _ys[-1], %r, len(_xs) * len(_ys)))\n"
                     "for _y in _ys:\n"
                     "    for _x in _xs:\n"
                     "        z,_ = Z.hits(_x+0.013, _y+0.007); z = np.sort(z)\n"
                     "        print('  x %%7.2f y %%8.2f : %%s' %% (_x, _y, ' '.join('%%.2f' %% v for v in z) if len(z) else 'MISS'))\n"
                     ) % (g[0], g[1], step, g[2], g[3], step, step)
        else:
            if len(rest) < 3 or rest[0].lower() != "z" or not (_isnum(rest[1]) and _isnum(rest[2])):
                sys.exit("kit measure <brep> rays z <x> <y>        one ray, cast DOWN z at (x, y)\n"
                         "kit measure <brep> rays z 0 0 --grid x0 x1 y0 y1 [--step S]   a grid of them\n"
                         "  (got: rays %s)" % " ".join(rest))
            ax = rest[0]; c1 = float(rest[1]); c2 = float(rest[2])
            code += ("V,T,F = K.tess(s); Z = K.R.ZRays(V,T,2.0)\n"
                     "z,_ = Z.hits(%f+0.013, %f+0.007); z=np.sort(z); print('MEASURE z-ray at x=%g y=%g: hits', np.round(z,2))\n") % (c1, c2, c1, c2)
    elif what == "dihedral":
        box = a.get("--box")
        if not box and not control:
            sys.exit("kit measure <brep> dihedral --box x0 x1 y0 y1 z0 z1 [--min-len L] [--worst N] [--control]")
        minlen = float(a.get("--min-len", "0.3")); worst = int(a.get("--worst", "30"))
        samples = int(a.get("--samples", "11"))
        _dih = (
            "import math, Part, FreeCAD as _App\n"
            "def _raw(f, p):\n"
            "    u, v = f.Surface.parameter(p); n = f.normalAt(u, v); n.normalize(); return n\n"
            "_cal = Part.makeBox(10, 10, 10); _cc = _cal.CenterOfMass; _FLIP = None\n"
            "for _f in _cal.Faces:\n"
            "    if _f.Orientation == 'Reversed':\n"
            "        _FLIP = _raw(_f, _f.CenterOfMass).dot(_f.CenterOfMass - _cc) < 0; break\n"
            "if _FLIP is None:\n"
            "    _FLIP = False; print('DIHEDRAL sign: the calibration box has NO Reversed face - convention UNVERIFIED, no flip applied')\n"
            "else:\n"
            "    print('DIHEDRAL sign: Face.normalAt on a Reversed face points %s -> reversed faces are %s'\n"
            "          % ('INWARD' if _FLIP else 'OUTWARD (already orientation-aware)', 'flipped' if _FLIP else 'NOT flipped'))\n"
            "def _onorm(f, p):\n"
            "    n = _raw(f, p)\n"
            "    if _FLIP and f.Orientation == 'Reversed': n = n * -1.0\n"
            "    return n\n"
            "def _census(sh, box, minlen, label):\n"
            "    if box:\n"
            "        x0,x1,y0,y1,z0,z1 = box\n"
            "        sel = [i for i, f in enumerate(sh.Faces) if f.BoundBox.XMax >= x0 and f.BoundBox.XMin <= x1\n"
            "               and f.BoundBox.YMax >= y0 and f.BoundBox.YMin <= y1 and f.BoundBox.ZMax >= z0 and f.BoundBox.ZMin <= z1]\n"
            "    else:\n"
            "        sel = list(range(len(sh.Faces)))\n"
            "    print('DIHEDRAL %s: %d faces in box - about %.0f s at 11 samples per edge (cap 170 s)%s' % (label, len(sel), 0.1 * len(sel) * __SAMPLES__ / 11.0,\n"
            "          '' if len(sel) < 400 else '  ** TOO BIG FOR ONE CALL: split the box, or --samples 3 **'), flush=True)\n"
            "    key2f, key2e = {}, {}\n"
            "    for i in sel:\n"
            "        for e in sh.Faces[i].Edges:\n"
            "            m = e.CenterOfMass; k = (round(m.x,3), round(m.y,3), round(m.z,3), round(e.Length,3))\n"
            "            key2f.setdefault(k, []).append(i); key2e.setdefault(k, e)\n"
            "    rows = []\n"
            "    for k, fs in key2f.items():\n"
            "        fs = sorted(set(fs))\n"
            "        if len(fs) != 2 or k[3] < minlen: continue\n"
            "        fa, fb, ed = sh.Faces[fs[0]], sh.Faces[fs[1]], key2e[k]\n"
            "        p0, p1 = ed.ParameterRange; angs = []\n"
            "        for q in range(1, __SAMPLES__ + 1):\n"
            "            p = ed.valueAt(p0 + (p1 - p0) * q / (__SAMPLES__ + 1.0))\n"
            "            try: na, nb = _onorm(fa, p), _onorm(fb, p)\n"
            "            except Exception: continue\n"
            "            angs.append(math.degrees(math.acos(max(-1.0, min(1.0, na.dot(nb))))))\n"
            "        if angs: rows.append((max(angs), sum(angs)/len(angs), fs[0]+1, fs[1]+1, k[3], k[2]))\n"
            "    rows.sort(reverse=True)\n"
            "    n160 = sum(1 for r in rows if r[0] > 160.0); n175 = sum(1 for r in rows if r[0] > 175.0)\n"
            "    n45 = sum(1 for r in rows if r[0] > 45.0); n5 = sum(1 for r in rows if r[0] > 5.0)\n"
            "    print('DIHEDRAL %s: %d faces in box, %d shared edges >= %.1f mm measured' % (label, len(sel), len(rows), minlen))\n"
            "    if not rows:\n"
            "        print('DIHEDRAL ABORT: NO shared edges measured - an empty set proves nothing (T68). Check the box.')\n"
            "        return rows\n"
            "    print('DIHEDRAL   FOLDS  past 175 deg: %3d   past 160 deg: %3d   |  past 45: %d   past 5: %d   tangent(<=5): %d'\n"
            "          % (n175, n160, n45, n5, len(rows) - n5))\n"
            "    print('DIHEDRAL   worst %.2f deg between Face%d and Face%d (len %.2f at z %.2f)' % (rows[0][0], rows[0][2], rows[0][3], rows[0][4], rows[0][5]))\n"
            "    return rows\n").replace("__SAMPLES__", repr(max(1, samples)))
        if control:
            _dih += (
                "_bx = Part.makeBox(10, 10, 10); _r = _census(_bx, None, 1.0, 'CONTROL box')\n"
                "_ok1 = len(_r) == 12 and all(abs(r[0] - 90.0) < 0.01 for r in _r)\n"
                "_c = Part.makeCylinder(5, 10).fuse(Part.makeCylinder(5, 10, _App.Vector(0,0,10)))\n"
                "_r2 = _census(_c, None, 1.0, 'CONTROL fused cylinders')\n"
                "_ok2 = any(r[0] < 0.01 for r in _r2) and any(abs(r[0] - 90.0) < 0.01 for r in _r2)\n"
                "_in = [i + 1 for i, _f in enumerate(_bx.Faces) if _onorm(_f, _f.CenterOfMass).dot(_f.CenterOfMass - _bx.CenterOfMass) <= 0]\n"
                "_ok3 = not _in\n"
                "print('DIHEDRAL CONTROL %s: box 12 edges at 90.00 -> %s; cylinder seam 0.00 and ends 90.00 -> %s; all 6 box normals outward -> %s%s'\n"
                "      % ('PASSED' if (_ok1 and _ok2 and _ok3) else 'FAILED', _ok1, _ok2, _ok3, '' if _ok3 else ' (INWARD on faces %s)' % _in))\n"
                "if not (_ok1 and _ok2 and _ok3): raise SystemExit('DIHEDRAL CONTROL FAILED - do not believe any reading from this instrument')\n")
        if box:
            vals = [float(t) for t in str(box).split()] if " " in str(box) else [float(t) for t in rest[:6]]
            if len(vals) != 6:
                sys.exit("kit measure dihedral: --box needs SIX numbers x0 x1 y0 y1 z0 z1")
            _dih += (
                "_rows = _census(s, %r, %r, 'box')\n"
                "for _r in _rows[:%d]:\n"
                "    print('DIHEDRAL   %%7.2f deg max  %%6.2f mean   Face%%-5d | Face%%-5d  len %%6.2f  z %%6.2f' %% _r)\n"
                "if len(_rows) > %d: print('DIHEDRAL   ... %%d more, all below %%.2f deg' %% (len(_rows) - %d, _rows[%d][0]))\n"
                % (tuple(vals), minlen, worst, worst, worst, worst))
        code += _dih
    else:
        sys.exit(_MEASURE_USAGE)
    rc = _fc(code, os.getcwd(), "measure")
    if dossier:
        txt = ""
        try:
            with open(_FC_LAST.get("log") or os.path.join(os.getcwd(), "kit_run.log"), encoding="utf-8", errors="replace") as _fh:
                _all = _fh.read()
            txt = _all[_all.rfind("\n== "):] if "\n== " in _all else _all
        except OSError:
            pass
        png = a.get("--out") if what == "section" else None
        D.add(ROOT, dossier, "kit measure " + " ".join(args), txt, png)
    return rc

def _facts_path(root):
    """The project's fact file. another project calls it FACTS.md; the part has always called it
    PROJECT_FACTS.md - 52 kB, including the section 6 standing-rulings log. The kit hard-coded
    another project's name, so `kit facts` died with FileNotFoundError on the part: the one command a
    worker is given for looking up a project number, unavailable on this project.

    Prefer whichever file exists, FACTS.md first so another project is bit-unchanged. Do NOT "fix" this by
    creating a second FACTS.md beside an existing PROJECT_FACTS.md - a number restated in two
    files is a number that will disagree with itself, which is the defect the hole card already
    records. an earlier improvement (P23)."""
    for n in ("FACTS.md", "PROJECT_FACTS.md"):
        p = os.path.join(root, n)
        if os.path.exists(p):
            return p
    return os.path.join(root, "FACTS.md")


def cmd_facts(args):
    kws = [k.lower() for k in args]
    lines = [l.rstrip() for l in open(_facts_path(ROOT), encoding="utf-8") if l.strip() and not l.startswith("#")]
    hits = [l for l in lines if all(k in l.lower() for k in kws)] if kws else lines[:40]
    for l in hits[:40]: print(l)
    if not hits: print("no fact mentions %s - ask the orchestrator; do not guess" % kws)

NOT_A_TYPE = ("GENERAL", "SYMPTOMS")


def _catalogue():
    """[(type, one-line, card text)] off EDIT_TYPES.md - the one owner of the catalogue."""
    txt = open(os.path.join(HERE, "..", "EDIT_TYPES.md"), encoding="utf-8").read()
    out = []
    for m in re.finditer(r"^## (\S+) — (.*?)$(.*?)(?=^## |\Z)", txt, re.M | re.S):
        if m.group(1) not in NOT_A_TYPE:
            out.append((m.group(1), m.group(2).strip(), m.group(0)))
    return out


def _card_field(card, name):
    m = re.search(r"^%s:\s*(.+?)(?=^\S[^\n]*:|\Z)" % re.escape(name), card, re.M | re.S)
    return " ".join(m.group(1).split()) if m else ""


def cmd_types(args):
    for t, one, _ in _catalogue():
        print("%-18s %s" % (t, one))


def cmd_route(args):
    r"""kit route "<the request, in the client's words>"      -> the edit type, its tier, the sequence, what to read
    kit route --table                                        the whole map, one line per type

    THE MAP FROM A REQUEST TO A PATH (2026-09-24). The client's process: "an Opus orchestrator ... figures out what
    types of working methods are needed, then is given limited (mapped) instructions that ensure success from the
    kit. This way wasteful read-in on methods that are not going to be used for the current edit is avoided."
    The words are matched against each card's `Route:` line in EDIT_TYPES.md (the one owner); the sequence and
    the tier are that card's. No match: the SYMPTOMS table prints - classify from a section, then route again.
    """
    cat = _catalogue()
    if not args or args[0] in ("--table",):
        print("%-16s %-26s %s" % ("type", "tier", "route words"))
        for t, one, card in cat:
            tier = _card_field(card, "Tier").split(" - ")[0].split(" (")[0]
            print("%-16s %-26s %s" % (t, tier, _card_field(card, "Route")))
        print("\nkit route \"<request>\" picks one; kit howto <type> prints its card; kit card <card.md> its traps.")
        return 0
    req = " ".join(args).lower()
    words = set(re.findall(r"[a-z][a-z0-9-]+", req))
    words |= {x[:-1] for x in list(words) if len(x) > 4 and x.endswith("s") and not x.endswith("ss")}
    scored = []
    for t, one, card in cat:
        rw = [w.lower() for w in _card_field(card, "Route").split()]
        def _hit(w):
            """2 = the word itself was said; 1 = a stem of it was (smooth / smoothing); 0 = no."""
            if w in words:
                return 2
            parts = [x for x in w.split("-") if len(x) >= 3]
            if len(parts) >= 2 and all(x in words for x in parts):
                return 2
            return 1 if (len(w) >= 6 and any(len(x) >= 6 and x[:6] == w[:6] for x in words)) else 0
        hits = {w: _hit(w) for w in rw}
        hits = {w: s for w, s in hits.items() if s}
        if t.lower() in words:
            hits[t] = 3
        if hits:
            scored.append((sum(hits.values()), t, one, card, sorted(hits)))
    if not scored:
        txt = open(os.path.join(HERE, "..", "EDIT_TYPES.md"), encoding="utf-8").read()
        m = re.search(r"^## SYMPTOMS — .*?(?=^## |\Z)", txt, re.M | re.S)
        print("kit route: no edit type's route words match %r.\n" % req)
        print("Classify from a SECTION first (the table decides shape vs seal), then `kit route` again with the row's words:\n")
        print(m.group(0).rstrip() if m else "(no SYMPTOMS section in EDIT_TYPES.md)")
        return 1
    scored.sort(key=lambda r: (-r[0], r[1]))
    best = scored[0]
    print("ROUTE: %s -> %s   (%s)" % (req[:70], best[1], best[2]))
    print("  matched : %s" % ", ".join(best[4]))
    if len(scored) > 1 and scored[1][0] >= max(1, best[0] - 1):
        print("  also    : %s - if the section says the feature is that, route to it instead"
              % ", ".join("%s (%s)" % (r[1], ", ".join(r[4])) for r in scored[1:3]))
    print("  tier    : %s" % _card_field(best[3], "Tier"))
    seq = _card_field(best[3], "Sequence")
    if seq:
        print("  sequence: %s" % seq)
    lf = _card_field(best[3], "Long form")
    print("  read    : kit howto %s%s" % (best[1], ("   then " + lf.split(" - ")[0].split(" (")[0]) if lf else ""))
    print("  traps   : kit card <card.md>   (that type's traps print there, and only there)")
    return 0


def cmd_howto(args):
    if not args or args[0].startswith("-"):
        cmd_types(args)
        print("\nkit howto <type> prints that type's card.")
        return 0
    cls = args[0]; txt = open(os.path.join(HERE, "..", "EDIT_TYPES.md"), encoding="utf-8").read()
    if cls in NOT_A_TYPE: sys.exit("'%s' is a section of the catalogue, not an edit type. `kit route` prints it." % cls)
    if cls == "burrito" and "--step" in args:
        import kit_rebuild as _krp
        _st = _opt(args, "--step") or ""; _pg = _krp.step_page(_st, HERE)
        print(_pg if _pg else "no page for step %r - the names it takes: %s (a short name is its skin step's: points = skin-points; 31ca R7 D4)" % (_st, ", ".join(_krp.step_names(HERE)))); return 0
    m = re.search(r"^## %s — .*?(?=^## |\Z)" % re.escape(cls), txt, re.M | re.S)
    if not m: sys.exit("no edit type '%s'. Run: kit types" % cls)
    g = re.search(r"^## GENERAL — .*?(?=^## |\Z)", txt, re.M | re.S)
    print(g.group(0).rstrip()); print(); print(m.group(0).rstrip())
    if "--long" in args:
        lf = _card_field(m.group(0), "Long form")
        fn = re.search(r"([A-Z_]+\.md)", lf or "")
        if fn and os.path.exists(os.path.join(HERE, "..", fn.group(1))):
            lt = open(os.path.join(HERE, "..", fn.group(1)), encoding="utf-8", errors="replace").read()
            if cls == "burrito":
                i = lt.find("## THE SKIN ROUTE"); j = lt.find("# HOW IT ACTUALLY RUNS", i if i >= 0 else 0)
                print("\n" + (lt[i:j] if i >= 0 and j > i else lt[:6000]).rstrip())
                print("\n(the old chain's front half - HOW IT ACTUALLY RUNS, steps 0-6, the voxel field - is SHELVED since 2026-10-08 (31ba): refused without SHELVED_OK; read it in BURRITO_STEPS.md only for a shelved step)")
                print("\n(the lessons: kit lessons; a lesson's text: kit lessons --near \"<its title>\")")
            else:
                j = lt.find("## THE REVIEW")
                print("\n" + (lt[:j] if j > 0 else lt).rstrip())
        else:
            print("\n(no long form for %s)" % cls)
    if cls == "burrito":
        if "--long" not in args:
            bs = os.path.join(HERE, "..", "BURRITO_STEPS.md")
            try:
                txt = open(bs, encoding="utf-8", errors="replace").read()
                i = txt.index("## THE SKIN ROUTE"); j = txt.index("\n# HOW IT ACTUALLY RUNS", i)
                print(); print(txt[i:j].rstrip())
            except (OSError, ValueError):
                print("\nBURRITO_STEPS.md's THE SKIN ROUTE block could not be read: %s" % bs)
        print("\nno template copied - the burrito runs as a chain of kit steps: kit rebuild <step> --job <J> --tag <T> (the route row by row: kit howto burrito --long)")
        return
    tpl = os.path.join(HERE, "templates", "t_%s.py" % cls)
    if os.path.exists(tpl):
        _job = _opt(args, "--job", "")
        _cwd = os.path.abspath(os.getcwd())
        _jobs = os.path.abspath(os.path.join(ROOT, "claude_code", "jobs"))
        if _job:
            _dd = os.path.join(_jobs, _job)
            if not os.path.isdir(_dd):
                print("\nkit howto: no job folder %s - `kit newjob %s` makes one; the template is not copied." % (_dd, _job)); return 2
        elif _cwd.startswith(_jobs + os.sep):
            _dd = _cwd
        else:
            print("\ntemplate NOT copied: you are not in a job folder. `kit howto %s --job <JOB>` copies it into\n"
                  "  claude_code\\jobs\\<JOB>\\ (a worker standing in its job folder needs no flag)." % cls)
            return 0
        dst = os.path.join(_dd, "w_%s.py" % cls)
        if not os.path.exists(dst): shutil.copy(tpl, dst); print("\ntemplate copied to %s - fill PARAMS at the top, then: kit run \"%s\"" % (dst, dst))
        else: print("\ntemplate already at %s" % dst)

def _isnum(t):
    try: float(t); return True
    except ValueError: return False
def _kv(args):
    a = {"_": []}; i = 0; args = [t for t in args if t != "--as-orchestrator"]
    while i < len(args):
        if args[i] == "--box":
            i += 1
            _one = str(args[i]).replace(",", " ").split() if i < len(args) and not args[i].startswith("--") else []
            if len(_one) > 1 and all(_isnum(t) for t in _one):
                vals = _one; i += 1
            else:
                vals = []
                while i < len(args) and _isnum(args[i]) and len(vals) < 6:
                    vals.append(args[i]); i += 1
            if len(vals) not in (0, 6):
                sys.exit("kit: --box needs SIX numbers (x0 x1 y0 y1 z0 z1); got %d: %s"
                         % (len(vals), " ".join(vals)))
            a.setdefault("--boxes", []).append(" ".join(vals))
            a["--box"] = " ".join(vals)
        elif args[i] == "--grid":
            i += 1
            if i < len(args) and not args[i].startswith("--") and \
                    len(str(args[i]).split()) > 1 and all(_isnum(t) for t in args[i].split()):
                vals = args[i].split(); i += 1
            else:
                vals = []
                while i < len(args) and _isnum(args[i]) and len(vals) < 4:
                    vals.append(args[i]); i += 1
            if len(vals) not in (1, 4):
                sys.exit("kit: --grid takes ONE number (section: grid spacing, mm) or FOUR (rays: "
                         "x0 x1 y0 y1); got %d: %s" % (len(vals), " ".join(vals)))
            a["--grid"] = " ".join(vals)
        elif args[i] in ("--help", "-h"):
            # kit measure
            # FAILURES.md
            a["--help"] = True; i += 1
        elif args[i].startswith("--"):
            if i + 1 >= len(args) or args[i + 1].startswith("--"):
                a[args[i]] = True; i += 1
            else:
                a[args[i]] = args[i + 1]; i += 2
        else: a["_"].append(args[i]); i += 1
    return a

import leangate as G
import kit_dossier as D


def _opt(args, name, default=None):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) \
        else default


def _all(args, name):
    return [args[i + 1] for i, t in enumerate(args) if t == name and i + 1 < len(args)]


def _flag(args, name):
    return name in args


def cmd_exam(args):
    print("THE THREE SESSION QUESTIONS. Each is answered from CONTRACT.md (pushed at session start; rules 1 and 8, the worker's obligation)\n"
          "and, for the punch-through question, METHOD.md 3 - the FAR LIMIT on the card (31bx R6 D2). METHOD.md and EDIT_TYPES.md are read ONCE per project and declared with --method\n"
          "--edit-types; after that `kit route` names the one card you need.\n")
    for q in G.exam_questions():
        print("  [%s]  %s\n" % (q["id"], q["q"]))
    print("Then, ONE line:\n\n    " + G.OPEN_EXAMPLE)
    return 0


def _defer_end_clause(d):
    """31bv (TB1 F3): how a deferral ended, from its own record (kit promote writes it) - '' while it stands"""
    e = (d or {}).get("ended") or {}
    if e:
        return " - ENDED %s by %s: the atlas question is back (`kit atlas init`, or `kit atlas defer --until` again on the client's word)" % (e.get("when"), e.get("how"))
    return "" if G.atlas_defer_active(ROOT) else " - a model of record was PROMOTED since: the atlas question is back"


def _start_message():
    """31bv B1 (the second project project's start - friction F1 / F5 / F10; the client 10-30): THE BANK IS EMPTY - what a project that designs from parts does first. Printed by `kit open`, the
    SessionStart push and `kit newjob` without a model; PROJECT_START.md is the page."""
    _tpl = os.path.join(os.path.dirname(HERE), "templates", "BLANK_MODEL.FCStd"); _bank = os.path.join(ROOT, "claude_code", "bank", "<its brep>")
    return ("THE BANK IS EMPTY - a project that designs from parts starts here (the page: LEAN_KIT\\PROJECT_START.md):\n"
            "  1. THE FIRST BODY: `kit newjob <J> --from <a brep the client exported>` (a brep or an stl in claude_code\\bank\\ is the model of record once promoted), or\n"
            "     `kit newjob <J> --first \"<why>\"` + a sketch_extrude job with base=\"\" (the piece alone - the very first block; the card's Base: none - the first body, Row: none - the client <date>: '<the client's words>').\n"
            "     The kit reads .brep / .stl; a STEP or FCStd is exported to one by the client. HOW A FIRST BODY ENDS (nothing checks a body against no base - kit review / check / accept are an edit's):\n"
            "     kit render the result and look; copy it into claude_code\\bank\\; `kit promote \"%s\"`; then `kit cancel <J> --why \"the first body - promoted from the bank\"`.\n"
            "  2. THE FREECAD DOCUMENT starts from the kit's template - the groups, the marker blocks and the named colours are in it (templates\\BLANK_MODEL.md):\n"
            "     kit deliver R01 --template \"%s\" --target PLACEHOLDER_BODY --model <the PROMOTED first brep> --no-review \"the first body - nothing to review against\" --add-body \"name|label|<brep>|1|r,g,b|G2_ASSEMBLY\" ...\n"
            "     (the placeholder takes the body's own name; before a promotion: --drop PLACEHOLDER_BODY and every body an --add-body spec; a shown body into a hidden template group shows the group)\n"
            "  3. A PART IS PLACED AND TURNED by `kit place <brep> --out <placed.brep> --translate dx dy dz --rotate \"ax ay az deg\" [--about px py pz] --why \"...\"` - the project's\n"
            "     frame map is claude_code\\PLACEMENTS.json; a `place=` on an --add-body spec does the same at the delivery.\n"
            "  4. THE ATLAS AND THE DOSSIER COME AFTER the model is initialised and has made worthwhile progress - not now: `kit atlas defer --until \"<the client's words>\"` keeps\n"
            "     the atlas question quiet until the first promoted model of record (or `--lift`); a card's Region: then reads 'no atlas yet (deferred)' and a delivery owes no --no-atlas." % (_bank, _tpl))


def cmd_open(args):
    answers = {}
    for a in _all(args, "--answer"):
        if "=" in a:
            k, v = a.split("=", 1)
            answers[k.strip().lower()] = v
    G.session_open(ROOT, _flag(args, "--method"), _flag(args, "--edit-types"),
                   _opt(args, "--state", ""), answers, _opt(args, "--model", ""),
                   _opt(args, "--notes", ""))
    try:
        D.session_prompt(ROOT)
    except Exception:
        pass
    try:
        _atl = G.atlas_load(ROOT)
        if not _atl:
            _dfr = G.atlas_deferred(ROOT)
            if _dfr: print("ATLAS: DEFERRED until \"%s\" (%s; 31bv B1) - the question is quiet until the first promoted model of record or `kit atlas defer --lift`%s" % (_dfr.get("until"), _dfr.get("when"), _defer_end_clause(_dfr)))
            elif not ((G.session(ROOT) or {}).get("model_of_record") or ""): print("ATLAS: none yet - the bank is empty: the atlas comes AFTER the model has made worthwhile progress (`kit atlas defer --until \"<the client's words>\"` keeps the question quiet meanwhile; PROJECT_START.md 4; 31bv B1)")
            else: print("ATLAS: none. Nothing records what this part's regions ARE - `kit atlas init` (the regions proposed to the client, METHOD.md 11), or `kit atlas defer --until \"<the client's words>\"` while the model is still taking shape (the question returns at the next promotion; 31bx R1 D2).")
        else:
            _rg = _atl.get("regions", {})
            _ad = sorted(n for n, r in _rg.items() if r.get("definition_status") == "CLIENT")
            _fz = sorted(n for n in _ad if _rg[n].get("edit_status") == "FROZEN")
            _ed = sorted(n for n, r in _rg.items() if r.get("edited_by"))
            print("ATLAS: %d region(s), %d confirmed by the client (model %s). A card names its Region: from these."
                  % (len(_rg), len(_ad), _atl.get("model", "?")))
            print("  FROZEN (may be in a selection; recreated at the end of edits): %s" % (", ".join(_fz) or "none"))
            if _ed:
                print("  edited since their map was taken: %s" % ", ".join(_ed))
            _ow = G.atlas_recreate_owed(ROOT)
            if _ow:
                print("  RECREATE OWED before delivery: %s" % ", ".join(sorted(_ow)))
    except Exception:
        pass
    try:
        _bk = os.path.join(ROOT, "claude_code", "bank")
        _has = any(f.lower().endswith((".brep", ".stl", ".step", ".stp", ".fcstd")) for f in (os.listdir(_bk) if os.path.isdir(_bk) else []))
        if not _has and not (G.session(ROOT) or {}).get("model_of_record"):
            print(_start_message())
    except Exception:
        pass
    return 0


def cmd_card(args):
    if not args or str(args[0]).startswith("--"):
        print("usage: kit card <card.md> [--type <edit_type>] [--warn-only]     lint a card BEFORE launching a worker"); return 2
    G.card_lint(ROOT, args[0], _opt(args, "--type"),
                strict=not _flag(args, "--warn-only"))
    return 0


def _region_gate(card, txt):
    """None = refused (printed); [] = no approved atlas, nothing to check; [names] = the card's regions."""
    atl = G.atlas_load(ROOT) or {}
    regs = atl.get("regions", {})
    ok_names = sorted(n for n, r in regs.items() if r.get("definition_status") == "CLIENT")
    if not ok_names:
        return []
    editable = ok_names
    if txt is None:
        print("kit job REFUSED: this project has an approved atlas, so a job names its card (--card) and the")
        print("  card names the region(s) in its selection (Region:). Regions the client confirmed: %s"
              % ", ".join(editable))
        return None
    m = re.search(r"^\s*region\s*[:=]\s*(.*)$", txt, re.I | re.M)
    line = (m.group(1).strip() if m else "")
    if not line or line.startswith("<"):
        print("kit job REFUSED: the card has no Region: - name every atlas region in the job's selection, then say")
        print("  in words which part of it (\"Region: ribcage, vanes - the round under the second vane\").")
        print("  Regions the client confirmed: %s" % ", ".join(editable))
        print("  A card with no region is written against a box invented that day - the failure the atlas is for.")
        return None
    head = re.split(r"\s+[-\u2013\u2014]\s+|\(|:", line, 1)[0]
    names = [t.strip(" `*'\"") for t in re.split(r",|;|\+|\band\b", head) if t.strip(" `*'\"")]
    bad = []
    for n in names:
        if n not in regs:
            bad.append("%r is not a region of this part's atlas" % n)
            continue
        ok, msg = G.atlas_citable(ROOT, n)
        if not ok:
            bad.append(msg)
    if bad:
        print("kit job REFUSED on the card's Region: %s" % line)
        for b in bad:
            print("   * " + b)
        print("  Regions the client confirmed: %s" % ", ".join(editable))
        return None
    for n in names:
        r = regs[n]
        if r.get("edit_status") == "FROZEN":
            print("kit job: %r is FROZEN - allowed in the selection; it is RECREATED at the end of edits. Once this"
                  " job applies,\n  delivery refuses until `kit atlas recreated %s --result <final mesh>` measures it"
                  " back against its original." % (n, n))
        if r.get("edited_by"):
            print("kit job: WARNING - %r was edited after its map was taken (%s). The atlas still says what it"
                  " IS; its face list and pieces are from before - re-take the map before trusting them."
                  % (n, ", ".join(e.get("job", "?") for e in r["edited_by"][-3:])))
    print("kit job: region(s) %s - confirmed by the client." % ", ".join(names))
    return names


def cmd_job(args):
    ev, ef, wm = _opt(args, "--expect-vol"), _opt(args, "--expect-faces"), _opt(args, "--wall-min")
    if not args or args[0].startswith("-"):
        print("kit job <name> --type <edit_type> --card <path> [--tier haiku|sonnet|opus] [--expect-vol N] [--expect-faces N] [--wall-min N] [--box \"x0 x1 y0 y1 z0 z1\"]\n"
              "  kit job <name>   alone re-reads the record's card after an edit (kit card <path> first - the lint is the gate)")
        return 2
    _jr7 = G.job(ROOT, args[0]) or {}
    _ty7 = _opt(args, "--type") or _jr7.get("edit_type") or ""
    _cd7 = _opt(args, "--card") or _jr7.get("card")
    _tr7 = _opt(args, "--tier") or _jr7.get("tier") or ""
    if not _tr7:
        try:
            _ct7 = open(_cd7, encoding="utf-8", errors="replace").read() if _cd7 and os.path.exists(_cd7) else ""
            _mt7 = re.search(r"^\s*Tier\s*:\s*(.+?)\s*$", _ct7, re.I | re.M); _tr7 = (_mt7.group(1).strip() if _mt7 else "") or _tier_for(_ty7)
        except Exception:
            _tr7 = _tier_for(_ty7)
        _tr7 = (re.split(r"\s*[-(;:,]\s*|\s+from\s+|\s+worker\b", str(_tr7))[0].strip().rstrip(".") or "haiku")[:40]
    if _jr7 and (not _opt(args, "--type") or not _opt(args, "--card")):
        print("[leangate] kit job %s: %s from the job's own record (31bw)" % (args[0], ", ".join(x_ for x_ in (("type %s" % _ty7) if not _opt(args, "--type") else "", ("card %s" % _cd7) if not _opt(args, "--card") else "", ("tier %s" % _tr7) if not _opt(args, "--tier") else "") if x_)))
    elif not _jr7 and not _opt(args, "--type"):
        print("kit job REFUSED: %s has no record yet - name its type and its card: kit job %s --type <edit_type> --card <path>  (kit newjob / kit newcard / kit card first)" % (args[0], args[0])); return 2
    card = _cd7      # 31bw (TB6b F1)
    if card and os.path.exists(card):
        with open(card, encoding="utf-8", errors="replace") as _fh:
            _txt = _fh.read()
        _m = re.search(r"^\s*class\s*[:=]\s*(shape|seal)", _txt, re.I | re.M)
        if _m and _m.group(1).lower() == "seal" and "--allow-seal" not in args:
            print("kit job REFUSED: the card is CLASS seal — it changes construction, not shape.\n"
                  "  the client's order (2026-09-10): shape first, seal LAST. an early corner job was a buried weld\n"
                  "  carded as rows D/I. If the client named THIS seal job now, re-run with --allow-seal and\n"
                  "  quote them in the friction log; otherwise it waits for row J.")
            return 2
        _m = re.search(r"^\s*dossier\s*[:=]\s*(\S+)", _txt, re.I | re.M)
        if _m and _m.group(1).lower() not in ("none", "n/a", "-", "<"):
            _stt, _de = D.status(ROOT, _m.group(1))
            if _stt == "missing":
                print("kit job REFUSED: the card names dossier %r and there is no such dossier.\n"
                      "  kit dossier list — or take it: kit dossier take %s --box <the job box>"
                      % (_m.group(1), _m.group(1)))
                return 2
            if _stt == "stale":
                print("kit job REFUSED: dossier %r is STALE (job %s changed that box after it was taken).\n"
                      "  kit dossier refresh %s, then re-read its numbers into the card."
                      % (_m.group(1), _de["stale"].get("by"), _m.group(1)))
                return 2
            if _stt == "defined":
                print("kit job REFUSED: dossier %r is DEFINED but not measured — kit dossier take %s, then write\n"
                      "  the card from its numbers." % (_m.group(1), _m.group(1)))
                return 2
            if _stt == "partial":
                print("kit job REFUSED: dossier %r is PARTIAL — a take started and did not finish, so its files\n"
                      "  are not a measurement. kit dossier take %s --force, then write the card from its numbers."
                      % (_m.group(1), _m.group(1)))
                return 2
    # confirmed
    _regions = _region_gate(card, _txt if (card and os.path.exists(card)) else None)
    if _regions is None:
        return 2
    G.job_open(ROOT, args[0], _ty7, _cd7,
               _tr7,
               float(ev) if ev is not None else None,
               int(ef) if ef is not None else None,
               int(wm) if wm is not None else None)
    if _regions:
        G.job_mark(ROOT, args[0], "regions", ",".join(_regions))
    bx = _opt(args, "--box")
    if bx:
        G.job_mark(ROOT, args[0], "box", bx)
    G.prior_art(ROOT, args[0])
    try:      # every command prints its next step - this one had none
        _nx7 = {"burrito": "kit atlas assign %s --to <region> (once an atlas holds a region) -> kit rebuild region --job %s --tag <T> --set WIN=... (the card's levers; `kit howto burrito` is the route)" % (args[0], args[0]),
                "region_look": "kit render <brep> --out jobs\\%s\\look --box <the card's box> --job %s, then open every frame (a look, not an edit)" % (args[0], args[0])}.get(_ty7)
        print("  next    : %s" % (_nx7 or ("kit howto %s --job %s (the template copied into the job folder - its PARAMS filled from the card by hand), kit before %s ..., then kit run jobs\\%s\\w_%s.py" % (_ty7, args[0], args[0], args[0], _ty7))))
    except Exception:
        pass
    return 0


def cmd_look(args):
    if not args or str(args[0]).startswith("--"):
        print('usage: kit look <job> --says "<one line per picture>" [--says ...] [--picture <png>] [--code <pic>=<CODE>]     the orchestrator\'s own look'); return 2
    codes = {}
    for c in _all(args, "--code"):
        if "=" in c:
            k, v = c.split("=", 1)
            codes[k.strip()] = v.strip()
    G.orchestrator_look(ROOT, args[0], _all(args, "--says"), _all(args, "--picture"), codes)
    return 0


def cmd_accept(args):
    """kit accept <job> --review <dir> [--check ...]

    ACCEPTANCE NAMES ITS REVIEW. A job is not accepted because its numbers are good; it is accepted
    because somebody looked at it from every angle and said so, and that claim has exactly one
    source - a review directory stamped COMPLETE by `kit review --done`.

    On 2026-09-21 a delivery was described as *"render reviewed properly this time"* on five lead
    frames, three of which came back `cannot`, with the sweep never run and no frame ever given to a
    reviewer. Nothing in the kit contradicted it, because nothing in the kit was ever shown the
    review. Now the review is an argument to this command and is checked, not described.
    """
    if not args or args[0].startswith("-"):
        print(cmd_accept.__doc__)
        return 2
    rv = _opt(args, "--review", "")
    ok, msg = _rv_complete(rv)
    if not ok:
        print("kit accept REFUSED: %s" % msg)
        print("  `kit accept <job> --review <dir>`, and the dir must be COMPLETE - every frame the")
        print("  review rendered judged, none failed, fewer than half `cannot`. Judging the LEAD")
        print("  frames is phase 1 of 3 and is not a review; it exists to stop a bad build early.")
        print("  If this job genuinely needs no render review, say so to the client in the message body and")
        print("  let them answer. Do not route round this.")
        return 2
    print("kit accept: %s" % msg)
    G.ledger_behind(ROOT, args[0])
    G.gate_apply(ROOT, args[0], _opt(args, "--check"))
    try:
        _jf = os.path.join(ROOT, "claude_code", "jobs", args[0])
        if os.path.isdir(_jf) and any(f.startswith("REBUILD_") and f.endswith(".json") for f in os.listdir(_jf)):
            __import__("kit_rebuild").on_accept(args[0], sys.modules[__name__])
    except Exception as _e:
        print("kit accept: the rebuild record was NOT merged (%s) - `kit rebuild record --job %s` does it" % (_e, args[0]))
    return 0


def cmd_failure(args):
    # does not exist  recorded
    _c = (_opt(args, "--caught", "") or "").strip().lower()
    if _c and _c not in ("gate", "user", "self"):
        print("kit failure: --caught is gate | user | self  (who stopped it). Got %r." % _c)
        return 2
    if not _c:
        print("kit failure: NOTE - no --caught given, recorded as 'unknown'. It is gate | user | self, and\n"
              "  it is the only field that says whether the machinery caught this or a person did.")
    fields = {k: (_opt(args, "--" + k) or "") for k in ("what", "why", "fix", "signature")}
    for k in fields:
        f = _opt(args, "--from-" + k)
        if f:
            if not os.path.isfile(f):
                sys.exit("kit failure: --from-%s names a file that does not exist: %s" % (k, f))
            fields[k] = open(f, encoding="utf-8", errors="replace").read().strip()
    G.record_failure(ROOT, fields["what"], fields["why"], fields["fix"], fields["signature"], _opt(args, "--job", ""), _c)
    print("  stored: what %d, why %d, fix %d, signature %d characters%s"
          % (len(fields["what"]), len(fields["why"]), len(fields["fix"]), len(fields["signature"]),
             " - a backtick is in the text: if bash ran it, words are missing (use --from-what <file> etc.)" if any("`" in v for v in fields.values()) else ""))
    return 0


# WALL_CLOCKS.md
STATE_NOW = os.path.join("claude_code", "STATE_NOW.md")
WALL_CLOCKS = os.path.join("claude_code", "WALL_CLOCKS.md")


def _text_of(args, flag, file_flag="--from"):
    """The text after `flag`, or the contents of the file after `--from` (a backtick inside a
    --improvement argument was run by bash on 2026-09-22 and words went missing; a file cannot be)."""
    f = _opt(args, file_flag)
    if f:
        if not os.path.isfile(f):
            sys.exit("kit: --from names a file that does not exist: %s" % f)
        return open(f, encoding="utf-8", errors="replace").read().strip()
    t = _opt(args, flag, "")
    if t and "`" in t:
        print("kit: NOTE - a backtick in the text; if bash ran it, words are missing. Use --from <file> for prose with backticks.")
    return (t or "").strip()


def cmd_state(args):
    r"""kit state --note "<what changed>" [--tags "<tag>=<current|superseded|sweep|poisoned>, ..."] [--from <file>]
    kit state --show

    THE STATE THAT SURVIVES A COMPACTION, appended at the TOP of claude_code\STATE_NOW.md as a dated
    block (newest first, the way the file is read). `--tags` writes the tag key lines the block must
    open with. `--show` prints the newest block. The wall clock nudges when the job folder has outrun
    the file; this is the one-line way to answer it - no script, no re-reading.
    """
    p = os.path.join(G.records_root(ROOT), STATE_NOW)
    if "--show" in args or not args:
        if not os.path.isfile(p):
            print("kit state: no %s yet. `kit state --note \"...\"` starts it." % STATE_NOW); return 0
        txt = open(p, encoding="utf-8", errors="replace").read()
        blocks = re.split(r"(?m)^(?=# >>> UPDATE )", txt)
        print((blocks[1] if len(blocks) > 1 and not blocks[0].strip() else blocks[0]).rstrip()[:3000]); return 0
    note = _text_of(args, "--note")
    if not note:
        sys.exit("kit state: --note \"<what changed, what is settled, the next action>\" is required (or --from <file>).")
    tags = (_opt(args, "--tags", "") or "").strip()
    head = "# >>> UPDATE %s" % time.strftime("%Y-%m-%d %H:%M")
    lines = [head]
    if tags:
        lines.append("* TAGS: " + tags)
    for ln in note.splitlines():
        lines.append(("* " + ln) if ln.strip() and not ln.lstrip().startswith(("*", "-")) else ln)
    block = "\n".join(lines) + "\n\n"
    old = open(p, encoding="utf-8", errors="replace").read() if os.path.isfile(p) else ""
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(block + old)
    os.replace(tmp, p)
    print("kit state: written at the top of %s\n%s" % (STATE_NOW, block.rstrip()))
    return 0


def cmd_clock(args):
    r"""kit clock add <script.py> <seconds> [--note "..."]      one sample into claude_code\WALL_CLOCKS.md
    kit clock runaway <script.py> <seconds> --why "..."       a defect sample, kept OUT of the typical
    kit clock show [<script.py>]

    THE LIVING TABLE the wall-clock hook reads its budgets from (1.5x the typical = the red flag).
    `add` appends the sample to the script's row and re-takes the typical as the median of its
    samples; a script with no row gets one. `runaway` goes to the RUNAWAYS table (the client, 2026-09-14:
    "do not include jobs that have runaway issues"). Nothing else in the file is touched.
    """
    p = os.path.join(G.records_root(ROOT), WALL_CLOCKS)
    if not args or args[0] in ("show",):
        if not os.path.isfile(p):
            print("kit clock: no %s yet." % WALL_CLOCKS); return 0
        want = args[1] if len(args) > 1 else None
        for ln in open(p, encoding="utf-8", errors="replace"):
            if ln.startswith("| `") and (not want or want in ln):
                print(ln.rstrip()[:160])
        return 0
    verb = args[0]
    if verb not in ("add", "runaway") or len(args) < 3:
        sys.exit("kit clock add|runaway <script.py> <seconds> [--note|--why \"...\"]")
    script, secs = args[1], args[2]
    try:
        secs = float(secs)
    except ValueError:
        sys.exit("kit clock: <seconds> must be a number, got %r" % secs)
    note = _opt(args, "--note", "") or _opt(args, "--why", "") or ""
    if verb == "runaway" and not note:
        sys.exit("kit clock runaway: --why \"<the cause>\" is required - a runaway without its cause is noise.")
    if not os.path.isfile(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("# TYPICAL WALL CLOCKS PER JOB - a living table (kit clock add / runaway)\n\n## The table\n\n"
                     "| job | typical | samples (s) | red flag at 1.5x | notes |\n|---|---|---|---|---|\n\n"
                     "## RUNAWAYS - excluded from the averages, kept so the shape is recognisable\n\n"
                     "| job | ran | typical | why |\n|---|---|---|---|\n")
    lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
    key = "| `%s`" % script
    if verb == "add":
        cut = next((i for i, l in enumerate(lines) if l.strip().upper().startswith("## RUNAWAY")), len(lines))
        idx = next((i for i in range(cut) if lines[i].startswith(key)), None)
        if idx is None:
            hdr = next((i for i in range(cut) if lines[i].startswith("|---")), None)
            if hdr is None:
                block = ["", "## The table", "", "| job | typical | samples (s) | red flag at 1.5x | notes |", "|---|---|---|---|---|"]
                lines[cut:cut] = block
                cut += len(block)
                hdr = cut - 1
            end = hdr + 1
            while end < cut and lines[end].startswith("|"):
                end += 1
            row = "| `%s` | **%.0f s** | %.0f | **%.0f s** | %s |" % (script, secs, secs, secs * 1.5, note)
            lines.insert(end, row)
            print("kit clock: new row - %s" % row)
        else:
            cells = [c.strip() for c in lines[idx].strip().strip("|").split("|")]
            nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", cells[2])] if len(cells) > 2 else []
            nums.append(secs)
            nums_sorted = sorted(nums); n = len(nums_sorted)
            typ = nums_sorted[n // 2] if n % 2 else (nums_sorted[n // 2 - 1] + nums_sorted[n // 2]) / 2.0
            cells[1] = "**%.0f s**" % typ
            cells[2] = ", ".join("%g" % x for x in nums)
            if len(cells) > 3:
                cells[3] = "**%.0f s**" % (typ * 1.5)
            if note and len(cells) > 4 and note not in cells[4]:
                cells[4] = (cells[4] + "; " if cells[4] else "") + note
            lines[idx] = "| " + " | ".join(cells) + " |"
            print("kit clock: %s typical now %.0f s over %d samples (red flag %.0f s)" % (script, typ, n, typ * 1.5))
    else:
        cut = next((i for i, l in enumerate(lines) if l.strip().upper().startswith("## RUNAWAY")), None)
        if cut is None:
            lines += ["", "## RUNAWAYS - excluded from the averages, kept so the shape is recognisable", "",
                      "| job | ran | typical | why |", "|---|---|---|---|"]
            cut = len(lines) - 5
        end = cut + 1
        while end < len(lines) and not lines[end].startswith("|---"):
            end += 1
        end += 1
        while end < len(lines) and lines[end].startswith("|"):
            end += 1
        typical = ""
        for l in lines[:cut]:
            if l.startswith(key):
                m = re.search(r"\*\*(\d+(?:\.\d+)?) s\*\*", l); typical = (m.group(1) + " s") if m else ""
        row = "| `%s` | **%.0f s, killed/runaway** | %s | %s |" % (script, secs, typical or "-", note)
        lines.insert(end, row)
        print("kit clock: runaway recorded - %s" % row)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    os.replace(tmp, p)
    return 0


def cmd_ruling(args):
    r"""kit ruling --said "<the client's words, verbatim>" [--about "<what it settles>"] [--from <file>]
    kit ruling --reading "<the agent's reading>" --of "<the client's words it reads>" [--about "..."]
    kit ruling --find "<words>"

    THE CLIENT'S STANDING RULINGS go in ONE place: the rulings section of the project's facts file (§6 of
    PROJECT_FACTS.md, or FACTS.md), dated, in the client's words. This inserts at the END of that section - not
    at the end of the file, where a 2026-09-24 ruling landed among auto-written "Measured" blocks and
    was invisible to `kit facts`. The section is found by its heading (RULING in the title).

    --reading (2026-09-25, lessons D17): an AGENT'S READING of the client's words is not a ruling. One went into §6 on
    2026-09-25 dated like a ruling ("item (e) ... read (the agent, FIN_E) as the rectangular cut-back"), and METHOD.md
    already records what that costs - a later agent took an agent's derivation for the client's fact and got the part's
    orientation wrong. A reading goes to its own section, "READINGS, NOT RULINGS", with the words it reads, and
    stands until the client vetoes it. --said refuses text that reads like a reading ("read as", "interpreted", "I take
    this to mean") - quote them, or file it as --reading.
    --find prints the ruling lines (and readings) that carry the words, with their line numbers.
    """
    fp = os.path.join(ROOT, "FACTS.md")
    if not os.path.exists(fp) and os.path.exists(os.path.join(ROOT, "PROJECT_FACTS.md")):
        fp = os.path.join(ROOT, "PROJECT_FACTS.md")
    if not os.path.isfile(fp):
        sys.exit("kit ruling: no FACTS.md / PROJECT_FACTS.md at the project root.")
    txt = open(fp, encoding="utf-8", errors="replace").read()
    nl = "\r\n" if "\r\n" in txt else "\n"
    lines = txt.split(nl)
    heads = [i for i, l in enumerate(lines) if re.match(r"^##\s", l)]
    find = _opt(args, "--find", "")
    if find:
        words = [w.lower() for w in find.split() if w.strip()]
        rsec = [i for i in heads if re.search(r"RULING|READINGS", lines[i], re.I)]
        hits = 0
        for si in rsec:
            nxt = next((i for i in heads if i > si), len(lines))
            for i in range(si + 1, nxt):
                if lines[i].strip().startswith("*") and all(w in lines[i].lower() for w in words):
                    print("%s:%d  %s" % (os.path.basename(fp), i + 1, lines[i].strip()[:220])); hits += 1
        if not hits:
            print("kit ruling --find: no ruling or reading carries all of: %s" % " ".join(words))
        return 0
    reading = _text_of(args, "--reading")
    said = _text_of(args, "--said") if not reading else (_opt(args, "--of", "") or "").strip()
    about = (_opt(args, "--about", "") or "").strip()
    if reading:
        if not said:
            sys.exit("kit ruling --reading: --of \"<the client's words this reads>\" is required - a reading of nothing is a decision.")
        entry = ("* **%s%s - READING (an agent's, stands until the client vetoes it):** %s   *(of the client's words: \"%s\")*"
                 % (time.strftime("%Y-%m-%d"), (", " + about) if about else "", reading.replace(nl, " ").strip(), said.replace(nl, " ").strip()))
        sec = next((i for i in heads if re.search(r"READINGS, NOT RULINGS", lines[i], re.I)), None)
        new_head = "## READINGS, NOT RULINGS - an agent's reading of the client's words (kit ruling --reading); each stands until the client vetoes it"
    else:
        if not said:
            sys.exit("kit ruling: --said \"<the client's words>\" is required (or --from <file>).")
        if re.search(r"\b(read (as|by)|interpret(ed|ation)|i take (this|it) to mean|my reading)\b|\(the agent,|the kit maintainer read", said, re.I):
            sys.exit("kit ruling REFUSED: --said must be the client's words verbatim; this reads like an agent's reading of them"
                     " (\"read as\", \"interpreted\" ...). File it with `kit ruling --reading \"<your reading>\" --of \"<the client's words>\"`.")
        entry = "* **%s%s:** *\"%s\"*" % (time.strftime("%Y-%m-%d"), (", " + about) if about else "", said.replace(nl, " ").strip())
        sec = next((i for i in heads if re.search(r"RULING", lines[i], re.I) and not re.search(r"READINGS, NOT RULINGS", lines[i], re.I)), None)
        new_head = "## THE CLIENT'S STANDING RULINGS - CUMULATIVE LOG (append every new ruling HERE, dated)"
    if sec is None:
        lines += ["", new_head, "", entry]
        print("kit ruling: no %s section found - one was added at the end of %s" % ("readings" if reading else "rulings", os.path.basename(fp)))
    else:
        nxt = next((i for i in heads if i > sec), len(lines))
        end = nxt
        while end > sec + 1 and not lines[end - 1].strip():
            end -= 1
        lines.insert(end, entry)
        print("kit ruling: inserted at the end of `%s` (line %d of %s)" % (lines[sec].strip()[:60], end + 1, os.path.basename(fp)))
    tmp = fp + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(nl.join(lines))
    os.replace(tmp, fp)
    print("  " + entry[:200])
    print("  stored %d characters%s" % (len(entry), " - a backtick is in the text: if bash ran it, words are missing (use --from <file>)" if "`" in entry else ""))
    return 0


def cmd_status(args):
    ok, msg = guard_is_alive()
    print("guard: %s" % (msg if ok else "NOT RUNNING — " + msg))
    G.status(ROOT)
    _W = _wallclock()
    if _W:
        _t = _W.report(ROOT, latch=False)
        if _t:
            print(_t)
    try:
        import os as _os, sys as _sys
        for _c in (_os.path.join(ROOT, ".claude", "hooks"),
                   _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                                 "hooks")):
            if _os.path.exists(_os.path.join(_c, "liveness.py")):
                _sys.path.insert(0, _c)
                import liveness as _L
                _lines = _L.report(ROOT)
                print("\n".join(_lines) if _lines
                      else "watchers: all %d declared are beating." % len(_L.WATCHERS))
                break
    except Exception:
        pass
    try:
        D.session_prompt(ROOT)
    except Exception:
        pass
    return 0


def cmd_inbox(args):
    """ORCHESTRATOR: show what is new in claude_code/INBOX.md, --wait N seconds for it, or
    --append <file.md> [--from "<who>"] to post a block VERBATIM (no shell quoting).

    --from names a writer who is NOT the inbox's reader - the kit maintainer from LEAN_KIT, an auditor. Its
    block stays UNREAD until the orchestrator's next look. Without --from the block is the
    orchestrator's own and is pre-read. Until 2026-09-22 there was no --from, so every block
    the kit maintainer posted through this command was marked read the moment it landed (the same defect as
    the project FAILURES row 48, through the front door)."""
    ap = _opt(args, "--append")
    if ap is not None:
        if not os.path.exists(ap):
            print("kit inbox --append: no such file %s" % ap); return 2
        who = (_opt(args, "--from") or "").strip() or G.READER
        txt = open(ap, encoding="utf-8", errors="replace").read()
        n = G.inbox_append(ROOT, txt, who=who)
        print("INBOX: appended %d characters from %s under a stamped '# FROM %s' heading%s." % (
            n, ap, who, "" if who == G.READER else " - UNREAD until the orchestrator's next look"))
        return 0
    w = _opt(args, "--wait")
    if w is not None:
        print("INBOX: waiting up to %s s for new instructions in %s ..." % (w, G.INBOX_FILE), flush=True)
        G.inbox_wait(ROOT, float(w))
        return 0
    if not G.inbox_banner(ROOT):
        print("INBOX: nothing new in %s." % G.INBOX_FILE)
    return 0


def cmd_cancel(args):
    """ORCHESTRATOR: retire a job whose premise is disproved (leangate.job_cancel, the project P29)."""
    if not args or args[0].startswith("-"):
        print("kit cancel <job> --why \"<the premise that failed, one line>\"")
        return 2
    G.job_cancel(ROOT, args[0], _opt(args, "--why", ""))
    return 0


def cmd_close(args):
    _W = _wallclock()
    if _W:
        # transcript  kit close
        try:
            _gone = _W.auto_collect(ROOT, os.environ.get("CLAUDE_TRANSCRIPT_PATH"))
            if _gone:
                print("[wallclock] collected by their own signals: %s" % ", ".join("%s (%s)" % g for g in _gone))
        except Exception:
            pass
        _open = _W.watch_open(ROOT)
        if _open:
            G.refuse("close", [
                "%d launched task(s) are still on the clock:\n%s"
                % (len(_open), "\n".join("        %-22s %5.0f min   %s" % (n, m, w or "")
                                         for n, m, _e, _o, w in _open))],
                "L14: a background task you stop reading is not a task you stopped. Read it or "
                "kill it,\n  then `kit collected <name>` — and check for orphaned kernel "
                "processes while you are there:\n      tasklist /FI \"IMAGENAME eq "
                "freecadcmd.exe\"\n  One left running outlives this session and fights the next "
                "one for the same body.")
    G.loose_docs(ROOT)
    try:
        _owe = G.atlas_recreate_owed(ROOT)
        if _owe:
            print("[atlas] RECREATE OWED at hand-off (frozen regions an edit reached): %s - say so in --remaining."
                  % ", ".join("%s (%s)" % (n, ", ".join(j)) for n, j in sorted(_owe.items())))
    except Exception:
        pass
    G.close(ROOT, _opt(args, "--note", ""), _opt(args, "--next", ""),
            improvements=_all(args, "--improvement"), facts=_all(args, "--fact"),
            remaining=_opt(args, "--remaining", ""),
            no_improvements=_opt(args, "--no-improvements", ""),
            no_facts=_opt(args, "--no-facts", ""))
    _rotate_registers()
    return 0


def _rotate_registers(keep_state_blocks=8, inbox_keep_lines=200, inbox_min_lines=600):
    """THE REGISTERS ARE ROTATED AT CLOSE, THE CURRENT STATE KEPT (the client, 2026-09-25: "yes but keep the most current
    state"; lessons F4: STATE_NOW had 600 lines and INBOX 10,771, a reader needed 26 min to surface a known cause).
    STATE_NOW.md keeps its newest `keep_state_blocks` blocks (the ones the next session reads); the older blocks go to
    claude_code\\_archive\\STATE_NOW_<date>.md. INBOX.md is rotated only when everything in it has been read: its
    older lines go to _archive\\INBOX_<date>.md, the last `inbox_keep_lines` stay, and the read mark is re-set so
    nothing reads as new. Never raises; a rotation that fails is reported and skipped."""
    arch = os.path.join(G.records_root(ROOT), "claude_code", "_archive")
    stamp = time.strftime("%Y-%m-%d")
    try:
        p = os.path.join(G.records_root(ROOT), STATE_NOW)
        if os.path.isfile(p):
            txt = open(p, encoding="utf-8", errors="replace").read()
            blocks = [b for b in re.split(r"(?m)^(?=# >>> UPDATE )", txt) if b.strip()]
            if len(blocks) > keep_state_blocks:
                os.makedirs(arch, exist_ok=True)
                old = blocks[keep_state_blocks:]
                with open(os.path.join(arch, "STATE_NOW_%s.md" % stamp), "a", encoding="utf-8") as fh:
                    fh.write("\n".join(b.rstrip() for b in old) + "\n")
                tmp = p + ".tmp"
                with open(tmp, "w", encoding="utf-8", newline="") as fh:
                    fh.write("".join(blocks[:keep_state_blocks]))
                os.replace(tmp, p)
                print("[close] STATE_NOW.md: %d older block(s) -> _archive\\STATE_NOW_%s.md; the newest %d stay"
                      % (len(old), stamp, keep_state_blocks))
    except Exception as e:
        print("[close] STATE_NOW.md not rotated: %s" % str(e)[:120])
    try:
        p = G._inbox_path(ROOT)
        if os.path.isfile(p):
            new, _total = G.inbox_new(ROOT)
            lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
            if not new.strip() and len(lines) > inbox_min_lines:
                os.makedirs(arch, exist_ok=True)
                with open(os.path.join(arch, "INBOX_%s.md" % stamp), "a", encoding="utf-8") as fh:
                    fh.write("\n".join(lines[:-inbox_keep_lines]) + "\n")
                tmp = p + ".tmp"
                body = "# INBOX (rotated %s at kit close - the older entries are in claude_code\\_archive\\INBOX_%s.md)\n\n" % (stamp, stamp) \
                    + "\n".join(lines[-inbox_keep_lines:])
                with open(tmp, "w", encoding="utf-8", newline="") as fh:
                    fh.write(body)
                os.replace(tmp, p)
                G.inbox_mark(ROOT, len(body))
                print("[close] INBOX.md: %d line(s) -> _archive\\INBOX_%s.md; the last %d stay, all read"
                      % (len(lines) - inbox_keep_lines, stamp, inbox_keep_lines))
            elif new.strip():
                print("[close] INBOX.md not rotated: it holds unread text (kit inbox)")
    except Exception as e:
        print("[close] INBOX.md not rotated: %s" % str(e)[:120])


def cmd_launched(args):
    if not args or args[0].startswith("-"):
        print("kit launched <job>    start this job's wall clock, when the worker is spawned")
        return 2
    G.job_launched(ROOT, args[0])
    return 0


def _wallclock():
    """The wall-clock warden module, or None. Never raises and never blocks a kit command.

    It lives in `.claude\\hooks\\` because it is a hook first; these two commands are the manual
    half of the same register, for work the hook cannot see by itself.
    """
    import os as _os
    import sys as _sys
    for cand in (_os.path.join(ROOT, ".claude", "hooks"),
                 _os.path.join(_os.path.dirname(_os.path.dirname(
                     _os.path.abspath(__file__))), "hooks")):
        if _os.path.exists(_os.path.join(cand, "wallclock.py")):
            try:
                _sys.path.insert(0, cand)
                import wallclock
                return wallclock
            except Exception:
                return None
    return None


def cmd_repath(args):
    r"""Rewrite a moved root inside the project's LIVE STATE — and nowhere else.

        kit repath --from "C:\Users\user\Documents\Claude\Projects" --to "C:\CAD\Projects"
        kit repath --from "<old>" --to "<new>" --apply

    Dry run by default: it prints every file and line it would change and writes nothing.

    WHY THIS EXISTS. On 2026-09-14 the whole tree moved from
    `C:\Users\user\Documents\Claude\Projects\` to `C:\CAD\Projects\`, and absolute paths written
    into files went stale in three separate waves - the hooks, then the job scripts, then the state
    files (`WINNING_ENV.json` pointed at a fields `.npz` that no longer existed; the dossier pointed
    at every one of its own PNGs). Each wave was found by someone tripping over it.

    THE DISTINCTION THIS COMMAND IS BUILT AROUND, and it is the reason it is not a bulk
    search-and-replace:

      * **LIVE STATE** is read by the NEXT run - the dossier, the session, the registers, a card
        file, a settings bundle like `WINNING_ENV.json`. A stale path here is a fault and must be
        fixed.
      * **A RECORD** is what HAPPENED - `status_*.json`, `GATE_*.json`, `burrito_plan.json`, a look
        manifest, a log. **A C: path in a record is correct history.** Rewriting one is falsifying
        evidence, and this project's gates exist to keep evidence honest. So records are excluded by
        name, and the exclusion is listed below where it can be argued with.

    It handles both spellings because JSON escapes its separators: a file may hold `C:\Users\...`
    or `C:\\Users\\...`, and a survey that greps for only one of them under-reports - which is
    exactly how the dossier was missed on the first pass.
    """
    old = _opt(args, "--from", "")
    new = _opt(args, "--to", "")
    if not old or not new:
        print(cmd_repath.__doc__)
        return 2
    apply_ = "--apply" in args

    LIVE = ("claude_code/dossier/*.json", "claude_code/dossier/*/*.json",
            "claude_code/jobs/*/WINNING_ENV.json", "claude_code/jobs/*/cards_*.json",
            "claude_code/jobs/*/w_*.py", "claude_code/jobs/*/job_*.py",
            "claude_code/jobs/*/*.py", "claude_code/*.json",
            ".claude/_leangates/SESSION*.json", ".claude/_leangates/JOBS.json",
            ".claude/_leangates/MEASURES.json", ".claude/_leangates/LOOKS.json",
            ".claude/_leangates/CODES.json")
    SKIP = ("status_", "gate_s5", "gate_", "burrito_plan", "look_manifest", "_archive",
            "_to delete", "_replaced_by_", "_kit_before_install", "__pycache__", "_stale_")

    import glob as _g
    # nothing to do
    pairs, seen = [], set()
    for a, b in ((old, new),
                 (old.replace("\\", "\\\\"), new.replace("\\", "\\\\")),
                 (old.replace("\\", "/"), new.replace("\\", "/"))):
        if a not in seen:
            seen.add(a)
            pairs.append((a, b))

    hits, changed = 0, 0
    for pat in LIVE:
        for p in sorted(_g.glob(os.path.join(ROOT, pat.replace("/", os.sep)))):
            low = p.replace("\\", "/").lower()
            if any(s in low for s in SKIP):
                continue
            try:
                with open(p, encoding="utf-8") as fh:
                    txt = fh.read()
            except Exception:
                continue
            n = sum(txt.count(a) for a, _ in pairs)
            if not n:
                continue
            hits += n
            print("  %-4d %s" % (n, os.path.relpath(p, ROOT)))
            if apply_:
                for a, b in pairs:
                    txt = txt.replace(a, b)
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(txt)
                changed += 1

    if not hits:
        print("kit repath: nothing in this project's LIVE STATE names %s" % old)
        return 0
    print("\n%d occurrence(s) in %s." % (hits, "%d file(s) REWRITTEN" % changed if apply_
                                        else "the files above — nothing written"))
    if not apply_:
        print("  Re-run with --apply to write them.")
    print("  RECORDS were not touched and must not be: a %s path in a status file, a gate file or"
          % old.split(os.sep)[0])
    print("  a log is what actually happened, and rewriting it would falsify the evidence this")
    print("  project's gates exist to keep honest.")
    return 0


_RV_STATE = "review_state.json"


def _rv_load(d):
    import json as _j
    p = os.path.join(d, _RV_STATE)
    if not os.path.exists(p):
        return None
    try:
        return _j.load(open(p, encoding="utf-8"))
    except Exception:
        return None


def _rv_save(d, st):
    import json as _j
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, _RV_STATE), "w", encoding="utf-8") as fh:
        _j.dump(st, fh, indent=1)


def _rv_png(d, name):
    """31bt (TJ2 F3): the picture a frame name stands for - <name>.png in the review folder or a folder under it (a confirm set, _offtarget); None when no such picture exists"""
    try:
        for root_, dirs_, files_ in os.walk(d):
            if name + ".png" in files_: return os.path.join(root_, name + ".png")
    except OSError:
        pass
    return None


def cmd_review_judge(args):
    """kit review --judge <dir> --frame <name> --verdict pass|fail|cannot [--note "..."] [--confirms <frame> | --clears <frame>]
    A `fail` on ONE frame is a SUSPECT; a second, different frame judged `fail --confirms <it>` aborts the review;
    `pass --clears <it>` records it as shading/perspective. The sweep and --done refuse with a suspect open."""
    d = _opt(args, "--judge")
    st = _rv_load(d)
    if not st:
        print("kit review --judge: no review in %s (run kit review first)" % d)
        return 2
    fr = _opt(args, "--frame", "")
    vd = (_opt(args, "--verdict", "") or "").strip().lower()
    if vd not in ("pass", "fail", "cannot") or not fr:
        print("kit review --judge <dir> --frame <name> --verdict pass|fail|cannot [--note \"...\"]")
        return 2
    note = _opt(args, "--note", "")
    if vd != "pass" and not note.strip():
        print("kit review: a `%s` needs --note saying WHAT you saw. A verdict with no observation is "
              "not a review." % vd)
        return 2
    if not _rv_png(d, fr):
        print("kit review --judge REFUSED: no picture %s.png in %s or a folder under it - a verdict needs the frame on disk (31bt). The review's frames: %s" % (fr, d, ", ".join(st.get("frames") or [])[:400])); return 2
    verdicts = st.setdefault("verdicts", {})
    suspects = st.setdefault("suspects", {})          # confirmed
    confirms = (_opt(args, "--confirms", "") or "").strip()
    clears = (_opt(args, "--clears", "") or "").strip()
    _rj = (_opt(args, "--rejudge", "") or "").strip()      # released  recorded
    if st.get("state") in ("sweep", "COMPLETE") and fr in st.get("lead", []) and fr in verdicts and verdicts[fr].get("verdict") in ("pass", "fail", "cannot") and verdicts[fr].get("verdict") != vd and not _rj:
        print("kit review --judge REFUSED: %s is a LEAD frame judged %s before the sweep was released on it; a changed verdict after the release re-opens what the sweep stood on - say why: --rejudge \"<why>\" (recorded) (31bx R1 F9)" % (fr, verdicts[fr].get("verdict"))); return 2
    if vd == "fail" and not confirms:
        suspects[fr] = {"note": note, "at": G._now()}
        verdicts[fr] = {"verdict": "suspect", "note": note, "at": G._now()}
        _rv_save(d, st)
        box = st.get("box") or ""
        print("kit review: SUSPECT at %s - %s" % (fr, note))
        print("  One frame is indicative, not proof. Render or open a SECOND view of the same spot from a different\n"
              "  camera (a section across it, or a frame 30-60 deg round the orbit) and judge THAT frame:\n"
              "     kit review --judge %s --frame <second> --verdict fail --confirms %s --note \"...\"   -> ABORTS\n"
              "     kit review --judge %s --frame <second> --verdict pass --clears %s   -> it was shading/perspective\n"
              "     kit review --judge %s --frame <second> --verdict cannot --about %s --note \"...\"  -> still unsure: take another\n"
              "  A fresh view: kit render <after.brep> --out %s\\confirm%s --views std   (then judge its frames)."
              % (d, fr, d, fr, d, fr, d, (" --box " + box) if box else ""))
        return 0
    if vd == "fail" and confirms:
        if confirms not in suspects or suspects[confirms].get("confirmed_by") or suspects[confirms].get("cleared_by"):
            print("kit review: --confirms %s names no open suspect. Suspects open: %s"
                  % (confirms, ", ".join(k for k, v in suspects.items() if not v.get("confirmed_by") and not v.get("cleared_by")) or "none"))
            return 2
        if confirms == fr:
            print("kit review: the confirming frame must be a DIFFERENT frame from the suspect (%s)." % fr)
            return 2
        suspects[confirms]["confirmed_by"] = fr
        verdicts[fr] = {"verdict": "fail", "note": note, "at": G._now(), "confirms": confirms}
        verdicts[confirms]["verdict"] = "fail"
        st["state"] = "ABORTED"
        _rv_save(d, st)
        print("kit review: ABORTED - %s confirmed by %s.\n  %s\n  %s" % (confirms, fr, suspects[confirms]["note"], note))
        print("  The sweep does NOT run. This review cannot be cited as a pass - the state file says so.")
        print("  Fix the build. Extra views to diagnose it are ungated: render what you need.")
        return 3
    about = (_opt(args, "--about", "") or "").strip()
    if about:
        if about not in suspects or suspects[about].get("confirmed_by") or suspects[about].get("cleared_by"):
            print("kit review: --about %s names no open suspect." % about)
            return 2
        suspects[about].setdefault("looked", []).append({"frame": fr, "verdict": vd, "note": note, "at": G._now()})
        if vd == "cannot":
            verdicts[fr] = {"verdict": vd, "note": note, "at": G._now(), "about": about}
            _rv_save(d, st)
            print("kit review: %s could not settle suspect %s (%d view(s) so far: %s). Take another view - a section\n"
                  "  across it, or a frame further round the orbit; the suspect stays open until one confirms or clears it."
                  % (fr, about, len(suspects[about]["looked"]), ", ".join(x["frame"] for x in suspects[about]["looked"])))
            return 0
    if clears:
        if clears not in suspects or suspects[clears].get("confirmed_by"):
            print("kit review: --clears %s names no open suspect." % clears)
            return 2
        if clears == fr:
            print("kit review: the clearing frame must be a DIFFERENT frame from the suspect (%s)." % fr)
            return 2
        suspects[clears]["cleared_by"] = fr
        verdicts[clears] = {"verdict": "cleared", "note": suspects[clears]["note"] + " -> not real (%s: %s)" % (fr, note or "clean"),
                            "at": G._now()}
        print("kit review: suspect %s CLEARED by %s (shading / perspective). Say so in the report." % (clears, fr))
    verdicts[fr] = dict({"verdict": vd, "note": note, "at": G._now()}, **({"rejudged": _rj, "was": verdicts.get(fr, {}).get("verdict")} if _rj else {}))
    _rv_save(d, st)
    lead = st.get("lead", [])
    done = [f for f in lead if f in st.get("verdicts", {})]
    if fr in lead: print("kit review: %s = %s  (%d of %d lead frames judged)" % (fr, vd, len(done), len(lead)))
    else:
        _sw = [f for f in st.get("frames", []) if f not in lead]; _swd = [f for f in _sw if f in st.get("verdicts", {})]
        print("kit review: %s = %s  (a sweep frame; %d of %d sweep frames judged, the %d lead frame(s) done)" % (fr, vd, len(_swd), len(_sw), len(done)))
    return 0


def cmd_review_sweep(args):
    """kit review --sweep <dir> — refuses until the LEAD frames are judged and none failed."""
    d = _opt(args, "--sweep")
    st = _rv_load(d)
    if not st:
        print("kit review --sweep: no review in %s" % d)
        return 2
    if st.get("state") == "ABORTED":
        print("kit review --sweep REFUSED: this review ABORTED on a failed lead frame. A sweep now would "
              "spend\n  26 frames on a build already known to be wrong. Fix it and start a new review dir.")
        return 2
    lead = st.get("lead", [])
    v = st.get("verdicts", {})
    open_susp = [k for k, x in (st.get("suspects") or {}).items() if not x.get("confirmed_by") and not x.get("cleared_by")]
    if open_susp:
        print("kit review --sweep REFUSED: %d suspect frame(s) neither confirmed nor cleared by a second view: %s"
              % (len(open_susp), ", ".join(open_susp)))
        print("  Judge a second view: --verdict fail --confirms <frame>  or  --verdict pass --clears <frame>.")
        return 2
    missing = [f for f in lead if f not in v]
    if missing:
        print("kit review --sweep REFUSED: %d lead frame(s) not judged: %s" % (len(missing), ", ".join(missing)))
        print("  These are the views you said matter. Open them and judge each one:")
        print("    kit review --judge %s --frame <name> --verdict pass|fail|cannot --note \"...\"" % d)
        return 2
    if lead and all(v[f]["verdict"] == "cannot" for f in lead):
        st["state"] = "VOID"
        _rv_save(d, st)
        print("kit review: VOID - every lead frame came back `cannot`. Nothing was shown, so nothing was")
        print("  judged. This is NOT a failure of the build and must not be reported as one: it is a")
        print("  failure of the frames. Re-aim them (or raise the resolution) and review again.")
        return 2
    # released
    ncannot = sum(1 for f in lead if v[f]["verdict"] == "cannot")
    if lead and ncannot * 2 >= len(lead) and "--lead-ok" not in args:
        print("kit review --sweep REFUSED: %d of %d lead frames came back `cannot`." % (ncannot, len(lead)))
        print("  You named these frames as the ones that matter, so half of them showing nothing is")
        print("  evidence about the FRAMES, not about the build.")
        print("  Half the views you led with showed nothing, so the passes among them are a thin basis")
        print("  for spending the sweep. Name the frames that actually show this feature and review again:")
        print("  A one-sided feature (a blind pocket): review the box of the feature that HOLDS it, through the body's thickness - a camera")
        print("  from the far side then sees the subject (31bt K3; the client 2026-11-05). The subject is the box's pixels, never the item alone.")
        print("    kit review <before> <after> --out <NEW dir> --box ... --lead ortho_bottom,orbhi_180,...")
        print("  Frame names: the 24 orbit frames are orblo_XXX / orbhi_XXX by azimuth, plus ortho_front,")
        print("  ortho_back, ortho_left, ortho_right, ortho_top, ortho_bottom, iso_fl, iso_br.")
        print("  --lead-ok overrides, and says in the record that you looked and led with these anyway.")
        return 2
    st["state"] = "sweep"
    _rv_save(d, st)
    print("kit review: lead frames all judged, none failed. The sweep is released.")
    print("  Render the sweep: kit review --render %s (every shard; the judged leads are kept as judged), then judge those frames the same way." % d)
    print("  THIS IS NOT YET A REVIEW. %d of %d frames still carry no verdict. Nothing may be called"
          % (len(st.get("frames", [])) - len(st.get("verdicts", {})), len(st.get("frames", []))))
    print("  reviewed, delivered or accepted until `kit review --done %s` stamps it COMPLETE." % d)
    return 0



def cmd_review_done(args):
    """kit review --done <dir> — the ONLY thing that turns a review into a REVIEW. Nothing else may claim it.

    THE HOLE THIS CLOSES, and it was used on 2026-09-21. The two-phase review was built so a bad
    build could be stopped after five frames instead of thirty-two. Phase 1 alone then became a
    shortcut: an agent judged five leads, three came back `cannot`, it never ran `--sweep`, never
    rendered the other twenty-seven, never gave a frame to a reviewer, and delivered the model
    describing it as *"render reviewed properly this time - all five opened, all five judged"*. Every
    word of that was true and the model was not reviewed. Fail-fast is permission to stop EARLY on a
    FAILURE; it was never permission to stop on a pass.

    So the claim now has one source. This command refuses unless:
      * the leads were judged and the sweep was RELEASED (`--sweep` run, not skipped);
      * EVERY frame the review rendered carries a verdict - not the leads, all of them;
      * none is a `fail`;
      * fewer than half are `cannot` - a review mostly unable to see its subject is not a review;
      * every `fail` or `cannot` carries a note, which the judge command already enforces.
    Only then is the dir stamped COMPLETE, and only a COMPLETE dir satisfies `kit accept` and
    `kit deliverycheck`. An agent that has not run this has nothing to cite.
    """
    d = _opt(args, "--done")
    st = _rv_load(d)
    if not st:
        print("kit review --done: no review in %s" % d)
        return 2
    if st.get("state") in ("ABORTED", "VOID"):
        print("kit review --done REFUSED: this review is %s. It is not evidence and cannot be "
              "completed." % st.get("state"))
        return 2
    _osusp = [k for k, x in (st.get("suspects") or {}).items() if not x.get("confirmed_by") and not x.get("cleared_by")]
    if _osusp:
        print("kit review --done REFUSED: suspect frame(s) never confirmed or cleared by a second view: %s" % ", ".join(_osusp))
        return 2
    if st.get("state") != "sweep":
        print("kit review --done REFUSED: the sweep has not been released (state %r)." % st.get("state"))
        print("  Judge the lead frames, then `kit review --sweep %s`, then render and judge the rest." % d)
        print("  PHASE 1 IS NOT A REVIEW. Stopping after the leads is allowed on a FAILURE and on")
        print("  nothing else - a build that passes its leads still gets seen from every angle.")
        return 2
    frames = list(st.get("frames") or [])
    v = st.get("verdicts", {})
    missing = [f for f in frames if f not in v]
    if missing:
        print("kit review --done REFUSED: %d of %d frames carry no verdict." % (len(missing), len(frames)))
        print("  Unjudged: %s%s" % (", ".join(missing[:12]), " ..." if len(missing) > 12 else ""))
        print("  Every frame the review rendered is opened and judged, or the review is a sample and")
        print("  says so. `kit review --judge %s --frame <name> --verdict pass|fail|cannot --note \"...\"`" % d)
        return 2
    _nopng = [f for f in frames if not _rv_png(d, f)]
    if _nopng:
        print("kit review --done REFUSED: %d frame(s) of the plan have no picture on disk: %s%s - a killed or failed shard; render them (kit review --render %s) before the review can be complete" % (len(_nopng), ", ".join(_nopng[:12]), " ..." if len(_nopng) > 12 else "", d)); return 2
    fails = [f for f in frames if v[f]["verdict"] == "fail"]
    cannots = [f for f in frames if v[f]["verdict"] == "cannot"]
    if fails:
        print("kit review --done REFUSED: %d frame(s) FAILED: %s" % (len(fails), ", ".join(fails[:8])))
        print("  A review with a failure in it is a finding, not an acceptance. Fix the build.")
        return 2
    _occf = set()
    try:
        _odir = (st.get("render") or {}).get("out") or d
        for _sf in os.listdir(_odir):
            if _sf.startswith("status_arc") and _sf.endswith(".json"):
                _sjd = json.load(open(os.path.join(_odir, _sf), encoding="utf-8")) or {}
                _occf |= set(((_sjd.get("gates") or {}).get("occluded")) or [])
    except Exception:
        _occf = set()
    _cann_j = [f for f in cannots if f not in _occf]; _seeing = [f for f in frames if not (f in _occf and f in cannots)]
    if frames and len(_cann_j) * 2 >= max(1, len(_seeing)):
        print("kit review --done REFUSED: %d of %d frames came back `cannot`%s." % (len(_cann_j), len(_seeing), (" (the %d OCCLUDED frame(s) left out of this rule)" % len(_occf & set(cannots))) if (_occf & set(cannots)) else ""))
        print("  A review that mostly could not see its subject is evidence about the CAMERAS. Re-aim")
        print("  them and review again; do not report this as a pass. A one-sided feature (a blind pocket, a step in a top face): review the box of the")
        print("  feature that HOLDS it, through the body's thickness - a camera from the far side then sees the subject (31bt K3; the client 2026-11-05); a frame whose")
        print("  box the body covers in that view is OCCLUDED by the renderer and is judged `cannot` without penalty (31bv K32; 31bx R1 F5).")
        return 2
    st["state"] = "COMPLETE"
    st["completed"] = G._now()
    st["counts"] = {"frames": len(frames), "pass": len(frames) - len(cannots), "cannot": len(cannots), "occluded": len(_occf & set(cannots))}
    _rv_save(d, st)
    print("kit review COMPLETE: %d frames, %d judged pass, %d cannot%s, 0 fail." % (
        len(frames), len(frames) - len(cannots), len(cannots), (" (%d of them OCCLUDED - the box behind the body in that view, expected)" % len(_occf & set(cannots))) if (_occf & set(cannots)) else ""))
    print("  before: %s\n  after : %s" % (st.get("before"), st.get("after")))
    print("  Cite this directory. `kit accept` and `kit deliverycheck` will ask for it by name.")
    return 0


def _rv_complete(d):
    """(ok, message) — is `d` a COMPLETE review? The one test every acceptance path shares."""
    if not d:
        return False, "no review directory named (--review <dir> for an edit that was reviewed; --no-review \"<why>\" for a body nothing was reviewed against - a project's FIRST body, PROJECT_START.md; 31bx R7 D1)"
    st = _rv_load(d)
    if not st:
        return False, "no review in %s" % d
    if st.get("state") != "COMPLETE":
        return False, ("the review in %s is %r, not COMPLETE - run `kit review --done %s`"
                       % (d, st.get("state"), d))
    c = st.get("counts", {})
    return True, ("review COMPLETE: %s frames, %s cannot, 0 fail  (%s)"
                  % (c.get("frames", "?"), c.get("cannot", "?"), d))


def cmd_review_render(args):
    """kit review --render <dir> [--leads] - render EVERY shard of a planned review at once (31an), wait for all, report each; `--leads` renders the lead frames alone as one shard (31bw).

    The shards are numpy-only (job_render_arc.py never imports Part and never opens a .brep), so N of them together is safe - the
    one-kernel-job rule is about the tessellation cache (step 1), which must exist first. a project run of 2026-10-06: six shards
    ran one after another in 4.9 min because there was no runnable parallel form under the guard."""
    d = _opt(args, "--render")
    st = _rv_load(d)
    spec = (st or {}).get("render")
    if not spec:
        print("kit review --render: no planned review with shard specs in %s (plan it with `kit review <before> <after> --out %s ...` first)" % (d, d))
        return 2
    for c in (spec["ca"], spec["cb"]):
        if not os.path.isfile(c):
            print("kit review --render REFUSED: the tessellation cache %s is missing - step 1 (job_tess_cache.py, the kernel, alone) first" % c)
            return 2
    py = ENV.get("python") if ENV.get("python") and os.path.isfile(str(ENV.get("python"))) else sys.executable
    script = os.path.join(HERE, "job_render_arc.py")
    procs = []; _jobs = {}
    t0 = time.time()
    _groups = list(spec["groups"]); _leads_only = "--leads" in args
    if _leads_only:
        _ld = [str(x_) for x_ in (st.get("lead") or [])]
        _lf = [[n_, d_] for _k_, grp_ in _groups for n_, d_ in grp_ if n_ in _ld]
        if not _lf: print("kit review --render --leads: the review in %s names no lead frame among its shards (lead: %s)" % (d, ", ".join(_ld) or "none")); return 2
        _groups = [["lead", _lf]]; print("kit review --render --leads: the %d lead frame(s) alone (%s) as one shard - the sweep's shards after --sweep" % (len(_lf), ", ".join(n_ for n_, _d_ in _lf)))
    _vd = st.get("verdicts") or {}; _kept = []
    if not _leads_only and _vd:
        _g2 = []
        for k, grp in _groups:
            _keep = [[n_, d_] for n_, d_ in grp if not (n_ in _vd and _rv_png(d, n_))]; _kept += [n_ for n_, d_ in grp if n_ in _vd and _rv_png(d, n_)]
            if _keep: _g2.append([k, _keep])
            else: print("  shard %s: every frame of it is judged already - not drawn again (31bw)" % k)
        _groups = _g2
        if _kept: print("kit review --render: %d judged frame(s) kept as judged, not drawn again (31bw): %s" % (len(_kept), ", ".join(_kept)))
        if not _groups: print("kit review --render: every planned frame is judged - nothing to draw; `kit review --done %s` closes the review" % d); return 0
    for k, grp in _groups:
        env = dict(os.environ, KIT_HOME=HERE, LK_CACHE_A=spec["ca"], LK_CACHE_B=spec["cb"], LK_OUT=spec["out"], LK_SHARD=str(k),
                   LK_BOX=spec.get("box") or "", LK_MODE=spec.get("mode") or "after", LK_SECTION=spec.get("section") or "auto",
                   LK_FRAMES=json.dumps(grp), PYTHONUNBUFFERED="1")
        lg = open(os.path.join(spec["out"], "log_arc%s.txt" % k), "w", encoding="utf-8")
        pr = subprocess.Popen([py, script], stdout=lg, stderr=subprocess.STDOUT, env=env, cwd=spec["out"],
                              creationflags=(0x08000000 if os.name == "nt" else 0))
        pin_process(pr); _jb = _job_new(); _jobs[k] = _jb if (_jb and _job_assign(_jb, pr)) else None
        if _jb and _jobs[k] is None: _job_close(_jb)
        procs.append((k, pr, lg, len(grp)))
    print("kit review --render: %d shard(s) started together (%s) - waiting for all" % (len(procs), ", ".join("shard %s: %d frames, pid %d" % (k, n, pr.pid) for k, pr, _l, n in procs)))
    cap0 = float(ENV.get("timeout_check_s", 900)); _nmax = max([n_ for _k_, _p_, _l_, n_ in procs] or [1])
    cap = max(cap0, 300.0 * _nmax)
    if cap > cap0: print("  the shards' cap: %d s (%d frames in the largest shard at 300 s each; timeout_check_s is %d)" % (cap, _nmax, cap0))
    bad = []
    for k, pr, lg, n in procs:
        try:
            rc = pr.wait(timeout=max(5.0, cap - (time.time() - t0)))
        except subprocess.TimeoutExpired:
            if _jobs.get(k): _job_kill(_jobs[k])
            left = _kill_tree(pr, [py, script], by_name=False); rc = KILLED_RC
            print("  shard %s KILLED at the cap (%d s)%s" % (k, cap, ("; STILL RUNNING: %s" % left) if left else ""))
        lg.close()
        if _jobs.get(k): _job_close(_jobs[k]); _jobs[k] = None
        made = len([f for f in os.listdir(spec["out"]) if f.endswith(".png")])
        print("  shard %s: rc %s, %d frame(s) asked" % (k, rc, n))
        try:
            _sjo = json.load(open(os.path.join(spec["out"], "status_arc%s.json" % k), encoding="utf-8")) or {}
            _occ = ((_sjo.get("gates") or {}).get("occluded")) or []
            if _occ: print("    %d frame(s) OCCLUDED - the box lies behind the body's surface in that view; judged on the frames that see it (31bv K32): %s" % (len(_occ), ", ".join(_occ)))
        except Exception: pass
        if rc != 0: bad.append(k)
    print("kit review --render: %.0f s for all shards; %d PNG(s) in %s%s" % (time.time() - t0, len([f for f in os.listdir(spec["out"]) if f.endswith(".png")]), spec["out"],
          ("; FAILED shard(s) %s - their logs log_arc<k>.txt" % bad) if bad else ""))
    for k_ in bad:
        try: _sj = json.load(open(os.path.join(spec["out"], "status_arc%s.json" % k_), encoding="utf-8")) or {}
        except Exception: _sj = {}
        print("  shard %s: %s - %s" % (k_, _sj.get("state", "no status file"), (_sj.get("error") or "killed at the cap (no error recorded)")[:200]))
    print(("  Next: open each lead and judge it (kit review --judge %s --frame <lead> --verdict pass|fail|cannot --note ...); a fail ABORTS; then --sweep and `kit review --render %s` for every shard (31bw)" % (d, d))
          if _leads_only else ("  Next: open and judge every remaining frame - one cad-reviewer per shard (kit review --judge %s --frame <name> --verdict pass|fail|cannot --note ...), then `kit review --done %s` (the leads are judged and the sweep released; 31bw)" % (d, d))
          if st.get("state") == "sweep" else "  Next: judge the LEAD frames (kit review --judge ...), then --sweep, then one cad-reviewer per shard on the rest, then --done.")
    return 1 if bad else 0


def cmd_review_prune(args):
    """kit review --prune <dir> — clear superseded review dirs; never the approved baseline."""
    import shutil as _sh
    root = _opt(args, "--prune")
    if not os.path.isdir(root):
        print("kit review --prune: %s is not a directory" % root)
        return 2
    kept, gone = [], []
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        if not os.path.isdir(d):
            continue
        st = _rv_load(d) or {}
        if st.get("approved"):
            kept.append((name, "APPROVED BASELINE - never pruned"))
            continue
        if st.get("state") in ("ABORTED", "VOID"):
            gone.append((name, st.get("state")))
        elif not st:
            kept.append((name, "no review state - not ours to delete, look at it"))
        else:
            kept.append((name, st.get("state", "?")))
    for name, why in gone:
        _sh.rmtree(os.path.join(root, name), ignore_errors=True)
        print("  pruned %-28s (%s - its frames were never evidence)" % (name, why))
    for name, why in kept:
        print("  kept   %-28s (%s)" % (name, why))
    if not gone:
        print("  nothing to prune.")
    return 0


def cmd_review(args):
    r"""ORCHESTRATOR: plan a PARALLEL orbit review. Prints the commands; runs the kernel step itself.

        kit review <before.brep> <after.brep> --out <dir> --lead <view,view,...> [--shards 6] [--tag _B21]
                             [--box x0,x1,y0,y1,z0,z1] [--dev 0.1] [--plan-only] [--solo]
                             [--mode after|before]           (no overlay: two frame sets on one camera - L22)

    BOTH WAYS TO REVIEW ARE AVAILABLE AND THE FAN-OUT IS THE DEFAULT (the client, 2026-09-14).
    The frames are PNGs on disk either way, so `--solo` changes only who opens them - you, instead
    of one sub-agent per shard. **It never changes how many get opened.** Solo is right for a
    handful of frames, a re-look at one arc, or when sub-agents are not available; the fan-out is
    the default because an agent reading 32 large images spends its context on pictures and has
    none left for the job, and because six independent observers beat one tired one.

    WHY THIS EXISTS. Measured on the R19 body, 2026-09-14: a 29-frame review took **over nine
    minutes**, and only about ONE of those was kernel work. The rest was numpy projection and pixel
    classification, serial for no reason. ~10 min -> ~3 min at six-up, with IDENTICAL coverage.

    **SUPERSEDED 2026-09-21 - read both, the second is current.** the client, 2026-09-13: *"you should be
    gated to never be allowed to bypass full orbit reviews. I don't care if you think it's wasteful
    it's absolutely not."* the client, 2026-09-21: *"I do not want gating to force all images each time (up
    to 32 for some methods) ... as soon as a failure comes in that is meaningful the review process
    should get stopped."* Both are about the same thing - never skipping the looking - and the newer
    one adds that a build already known to be broken must not go on costing frames. So: the LEAD
    frames are judged first, a `fail` on one aborts, and the sweep is released only when they are
    clean. A build on its way to being accepted is still seen from every angle.

    The shape of it:
      1. `job_tess_cache.py` — the ONLY kernel step. Runs once, ALONE (two kernel jobs on one body
         froze the machine, 2026-09-10). This command runs it for you.
      2. `job_render_arc.py` x N — numpy only, no `Part`, no `.brep`. Safe six-up.
      3. one `cad-reviewer` sub-agent per shard, each opening ITS WHOLE ARC.
      4. you open only what was flagged, plus a baseline, and supply the one verdict
         `lk_review.gate()` refuses to return without.
    """
    import json as _json
    if _opt(args, "--judge", ""):
        return cmd_review_judge(args)
    if _opt(args, "--sweep", ""):
        return cmd_review_sweep(args)
    if _opt(args, "--done", ""):
        return cmd_review_done(args)
    if _opt(args, "--prune", ""):
        return cmd_review_prune(args)
    if _opt(args, "--render", ""):
        return cmd_review_render(args)
    if len(args) < 2 or args[0].startswith("-"):
        print(cmd_review.__doc__)
        return 2
    mode = (_opt(args, "--mode", "after") or "after").lower()
    # --mode before
    if mode == "overlay":
        print("kit review REFUSED: --mode overlay no longer exists. Old/new is two frame sets on the same camera:\n"
              "  kit review <before> <after> --out <dir>\\after  --mode after   (judged first)\n"
              "  kit review <before> <after> --out <dir>\\before --mode before  (only if the judgement needs it)\n"
              "  An overlay shows the larger geometry of both bodies and hides the edit (the client, 2026-09-17 and 2026-09-24).")
        return 2
    if mode not in ("after", "before"):
        print("kit review: --mode is after | before (default after)")
        return 2
    before, after = args[0], args[1]
    out = _opt(args, "--out", os.path.join(ROOT, "claude_code", "review"))
    before, after, out = os.path.abspath(before), os.path.abspath(after), os.path.abspath(out)
    shards = max(1, int(_opt(args, "--shards", 6)))
    tag = _opt(args, "--tag", "")
    box = _opt(args, "--box", "")
    if box and "," not in box:
        _i = args.index("--box") + 1
        _vals = []
        while _i < len(args) and _isnum(args[_i]) and len(_vals) < 6:
            _vals.append(args[_i]); _i += 1
        if len(_vals) == 6:
            box = ",".join(_vals)
        elif len(box.split()) == 6:
            box = ",".join(box.split())
    dev = _opt(args, "--dev", "0.1")
    for p in (before, after):
        for part in [q for q in str(p).split("+") if q.strip()]:
            if not os.path.exists(part):
                print("kit review: no such file: %s%s" % (part, ("   (from %s)" % p) if "+" in str(p) else ""))
                return 2
    if os.path.isdir(out) and any(f.lower().endswith(".png") for f in os.listdir(out)) \
            and "--resume" not in args:
        print("kit review REFUSED: %s already holds frames.\n"
              "  Frames carry no tag, so this run would overwrite them and destroy the evidence behind\n"
              "  whatever verdict they support. Give this review its own --out dir, or --resume to add\n"
              "  to the one that is there. `kit review --prune <parent>` clears aborted and void ones." % out)
        return 2
    if "--plan-only" not in args: os.makedirs(out, exist_ok=True)

    sys.path.insert(0, HERE)
    import kitlib_render as R
    frames = R.orbit_sweep()
    groups = R.shard_frames(frames, shards)

    lead = [t.strip() for t in (_opt(args, "--lead", "") or "").split(",") if t.strip()]
    lead_from = "named"
    bad = [t for t in lead if t not in [n for n, _d in frames]]
    if bad:
        print("kit review: --lead names %d frame(s) that do not exist: %s" % (len(bad), ", ".join(bad)))
        print("  Frames are orblo_XXX / orbhi_XXX by azimuth (24), plus ortho_front, ortho_back,")
        print("  ortho_left, ortho_right, ortho_top, ortho_bottom, iso_fl, iso_br.")
        return 2
    if not lead:
        # came back `cannot`
        # released
        print("kit review REFUSED: --lead is required. Name the frames YOU have decided matter.")
        print("  The kit has no default and will not guess which cameras see into your box; that is")
        print("  the orchestrator's judgement and it is the first thing the review rests on.")
        print("    --lead ortho_bottom,orbhi_180,iso_br        (comma-separated, 2 or more)")
        print("  Frames: orblo_XXX / orbhi_XXX by azimuth (24 of them), ortho_front, ortho_back,")
        print("  ortho_left, ortho_right, ortho_top, ortho_bottom, iso_fl, iso_br.")
        print("  A feature under a skin or inside a cavity is read from the side the CAMERA stands,")
        print("  not the side the feature faces. If you cannot say which frames show it, render a")
        print("  `kit render --views all` survey first and look - that is ungated.")
        return 2
    if len(lead) < 2:
        print("kit review REFUSED: one lead frame is not a lead SET. A single camera cannot")
        print("  distinguish a shape fault from a camera fault, and `cannot` on it voids the review.")
        return 2
    st0 = {"state": "lead", "before": before, "after": after, "box": box, "mode": mode,
           "lead": lead, "lead_from": lead_from, "verdicts": {}, "opened": G._now(),
           "frames": [n for n, _d in frames]}
    print("PHASE 1 OF 3. Judging the leads is not a review and cannot be reported as one: it exists")
    print("  to stop a BAD build after %d frames instead of %d. A build that PASSES its leads is"
          % (len(lead), len(frames)))
    print("  still seen from every angle. --sweep releases the rest; --done stamps it COMPLETE.")
    if "--plan-only" in args: print("  (--plan-only: nothing is written - no review_state.json, no cache; the plan above is the whole output)")
    else: _rv_save(out, st0)

    solo = "--solo" in args
    section = (_opt(args, "--section", "auto") or "auto").lower()
    print("kit review: %d frames over %d shard(s), by contiguous arc.  Frames: %s.  Review: %s"
          % (len(frames), shards,
             {"after": "THE RESULT ALONE", "before": "the start body alone"}[mode],
             "SOLO (you open them all)" if solo else "SUB-AGENTS, one per shard (default)"))
    print("  before %s\n  after  %s\n  out    %s" % (before, after, out))
    if not box:
        print("\n  NOTE: no --box, so frames are not scored for whether they SHOW the edit.")
        print("        Pass --box x0,x1,y0,y1,z0,z1 (the card's region) and each frame gets a")
        print("        subject-pixel fraction and an ok/thin/POOR mark the reviewer must honour.")
    print("\nSTEP 1 - the kernel, ONCE and ALONE (never two kernel jobs on one body):")
    print("  $env:LK_SHAPES=\"before=%s;after=%s\"; $env:LK_OUT=\"%s\"; "
          "$env:LK_DEV=\"%s\"; $env:LK_TAG=\"%s\"" % (before, after, out, dev, tag))
    print("  " + G.psline(os.path.join(HERE, "job_tess_cache.py"), py=freecad()))
    ca = os.path.join(out, "tess_before%s.npz" % tag)
    cb = os.path.join(out, "tess_after%s.npz" % tag)

    print("\nSTEP 2 - the shards. Launch ALL of them, then wait with waitlib.wait_all():")
    for k, grp in enumerate(groups):
        if not grp:
            continue
        spec = _json.dumps([[n, list(d)] for n, d in grp])
        print("  # shard %d: %d frames, %s .. %s" % (k, len(grp), grp[0][0], grp[-1][0]))
        print("  $env:LK_CACHE_A=\"%s\"; $env:LK_CACHE_B=\"%s\"; $env:LK_OUT=\"%s\"; "
              "$env:LK_SHARD=\"%d\"; $env:LK_BOX=\"%s\"; $env:LK_MODE=\"%s\"; "
              "$env:LK_SECTION=\"%s\"; $env:LK_FRAMES='%s'"
              % (ca, cb, out, k, box, mode, section, spec))
        print("  " + G.psline(os.path.join(HERE, "job_render_arc.py")))
    print("\n  Wait on the TAGGED status files - status_arc<k>.json - never an untagged one, and")
    print("  with waitlib, which checks the PID. A waiter that does not check liveness is not a")
    print("  waiter: ten minutes went into polling a dead process on 2026-09-14.")
    # bare `&`
    st0["render"] = {"ca": ca, "cb": cb, "out": out, "box": box, "mode": mode, "section": section,
                     "groups": [[k, [[n, list(d)] for n, d in grp]] for k, grp in enumerate(groups) if grp]}
    if "--plan-only" not in args: _rv_save(out, st0)
    print("\n  OR ALL AT ONCE, ONE LINE (31an): kit review --render %s   (every shard together, waited for; after step 1's caches exist)" % out)
    print("  THE LEADS FIRST: kit review --render %s --leads   (the lead frames alone, one shard - judged before the sweep is spent; 31bw)" % out)

    if solo:
        print("\nSTEP 3 - SOLO (--solo). YOU open all %d frames yourself, in shard order, one at a"
              % len(frames))
        print("  time. Same frames, same coverage, no sub-agents - it is the fan-out that is")
        print("  optional, never the looking. Expect this to cost you most of a context on")
        print("  pictures, which is the reason the fan-out is the default.")
        print("  Right when: a handful of frames, a re-look at one arc, or sub-agents unavailable.")
        print("\nSTEP 4 - write the verdict and supply the single agent_verdict.")
    else:
        print("\nSTEP 3 - DEFAULT: one `cad-reviewer` sub-agent PER SHARD, each opening its WHOLE arc.")
        print("  Give each: its frame list, the edit region, the frozen list. It returns the fixed")
        print("  schema in agents\\cad-reviewer.md. A shard that returns a pass without listing every")
        print("  frame it was given HAS NOT DONE THE REVIEW - reject it and re-run it.")
        print("  ONE DEAD SHARD FAILS THE REVIEW. A gap in the sweep is not '5 of 6 passed'.")
        print("  (`--solo` prints the do-it-yourself version of this step instead.)")
        print("\nSTEP 4 - you open only the flagged frames plus the AFTER top view and one iso as a")
        print("  baseline (never an overlay - L22), merge the verdicts, and supply the single agent_verdict.")
    print("\n" + "=" * 78)
    print("PHASE 1 - THE LEAD FRAMES. These, judged, BEFORE the sweep above is spent:")
    print("  %s" % ", ".join(lead))
    print("  Rendered alone first: kit review --render %s --leads   (one shard of the %d lead frame(s), after step 1; the full --render after --sweep; 31bw)" % (out, len(lead)))
    print("  For each one: open it, then")
    print("    kit review --judge %s --frame <name> --verdict pass|fail|cannot --note \"...\"" % out)
    print("  A `fail` ABORTS the review then and there - the client, 2026-09-21: \"as soon as a failure comes in")
    print("  that is meaningful the review process should get stopped.\" The remaining frames are not")
    print("  rendered, and diagnosing the failure with extra views is UNGATED.")
    print("  A `cannot` is not a pass: the frame could not settle it. All-cannot voids the review.")
    print("\nPHASE 2 - release the sweep, which refuses until phase 1 is clean:")
    print("    kit review --sweep %s" % out)
    print("=" * 78)
    print("\nBEFORE ANY OF IT: purge superseded renders. `kit review --prune <parent-dir>` removes the")
    print("  aborted and void ones and never the approved baseline. An accusation of damage on 2026-09-14")
    print("  turned out to be failed piece renders left lying in a shared folder.")

    if "--plan-only" in args:
        return 0
    print("\nRunning step 1 now (kernel, alone)...")
    env = dict(os.environ, LK_SHAPES="before=%s;after=%s" % (before, after),
               LK_OUT=out, LK_DEV=str(dev), LK_TAG=tag, KIT_HOME=HERE)
    _rlog = os.path.join(out, "log_tess_cache_%s.txt" % (tag or "x"))
    rc, _ = sh([freecad(), os.path.join(HERE, "job_tess_cache.py")], int(ENV.get("timeout_check_s", 900)), _rlog, env, cwd=out)
    if rc != 0 or not (os.path.isfile(ca) and os.path.isfile(cb)):
        print("\nSTEP 1 FAILED (rc %s): the caches are not both there (before %s, after %s) - read %s; no shard can run on this review" % (rc, "ok" if os.path.isfile(ca) else "MISSING", "ok" if os.path.isfile(cb) else "MISSING", _rlog)); return 2
    print("\nstep 1 exit %s. Caches:\n  %s\n  %s" % (rc, ca, cb))
    return 0


def cmd_ps(args):
    """Print ONE pastable PowerShell line for the client. Never type one by hand.

        kit ps "<script.py>" [args...]        the line, formatted
        kit ps --lint "<the line you were about to give them>"

    the client, 2026-09-14: *"You are not instructing me correctly for powershell commands."* It is their
    most-repeated correction, the rule had been prose in CONTRACT.md since 2026-09-09, and agents
    kept getting it wrong — because the rule was missing the two things that actually break the
    line (the `&` call operator, and that the bare word `python` is the Store stub here), and
    because the routing documents contradicted it by example.

    This is the P10 fix applied to a command instead of a camera: **formatted, never transcribed.**
    """
    if not args:
        print(cmd_ps.__doc__)
        return 2
    if args[0] == "--lint":
        line = " ".join(args[1:])
        bad = G.pslint(line)
        if not bad:
            print("[ps] that line is fine to give the client.")
            return 0
        print("[ps] DO NOT GIVE THE CLIENT THAT LINE — %d fault(s):" % len(bad))
        for what, fix in bad:
            print("  - it %s" % what)
            print("      %s" % fix)
        print("\n  `kit ps \"<script>\" [args...]` builds a correct one for you.")
        return 2
    print(G.psline(args[0], *args[1:]))
    return 0


def cmd_watch(args):
    """Put a launched thing on the clock BY HAND, when the hook cannot see it for itself.

    BURRITO_LESSONS L14, the client 2026-09-13: *"you had a two hour task running. Clearly you aren't
    monitoring correctly."* A wrapper launched to wait for one ~40 s probe was alive two hours
    later; the answer had come by another route and nobody killed it. Nothing warned, because a
    silent wait looks exactly like a silent success.

    The PostToolUse hook registers background Bash and Task launches automatically — this is for
    everything else: a scheduled watchdog, a driver started in another window, a kernel process
    somebody else spawned. Anything whose clock nobody else is holding.
    """
    W = _wallclock()
    if not W:
        print("kit watch: the wall-clock warden is not installed in this project. Give the client:\n"
              "  " + G.psline(os.path.join(KIT_MASTER, "install_lean_hooks.py"),
                              "--project", ROOT))
        return 2
    if not args or args[0].startswith("-"):
        print("kit watch <name> [--expect <minutes>] [--what \"<what it is>\"] [--pid <N>]\n"
              "kit collected <name> [--kill]   when you have its answer, or to end it by its pid tree")
        return 2
    try:
        exp = float(_opt(args, "--expect", 5))
    except (TypeError, ValueError):
        print("kit watch: --expect takes the expected MINUTES as a number (got %r); say what it is with --what \"...\"" % (_opt(args, "--expect", 5),)); return 2
    owner = G.current_conversation(ROOT) or ""
    pid = _opt(args, "--pid")
    W.watch_add(ROOT, args[0], exp, _opt(args, "--what", ""), owner=owner, pid=pid)
    print("[wallclock] watching %s, expected under %.0f min%s. `kit collected %s` closes it."
          % (args[0], exp, (", pid %s" % pid) if pid else "", args[0]))
    return 0


def cmd_deliverycheck(args):
    """kit deliverycheck <file.FCStd> (--review <dir> | --no-review "<why>") [--expect-colour <Object>=<#rrggbb> ...] [--body <Object>]

    THE THREE FAULTS THAT EACH PRODUCE A GREY MODEL, CHECKED. They look identical on screen and
    fixing one does not fix the others - `HOW_TO_DELIVER_A_COLOURED_MODEL.md` has the evidence.
    R19 and R20 both shipped grey.

    Pure zip + text. No FreeCAD, so it runs anywhere and in under a second.

    IT CHECKS THAT THE COLOURS ARE WIRED UP, NOT THAT THE BYTES ARE PRESENT. Verifying the
    ingredients is not verifying the dish; that mistake was made twice on this model.

    A PASS HERE IS NOT ACCEPTANCE. The only proof the colour actually paints is a GUI screenshot of
    the client's own session - the headless tools cannot render one. This catches the faults that are
    invisible until the client opens the file.
    """
    import zipfile
    import xml.etree.ElementTree as ET
    # none of the
    _rv = _opt(args, "--review", "")
    _ok, _msg = _rv_complete(_rv)
    if not _ok and _opt(args, "--no-review", ""):
        print("kit deliverycheck: no COMPLETE review (%s) - NO-REVIEW RECORDED: %s" % (_msg, _opt(args, "--no-review", "")))
    elif not _ok:
        print("kit deliverycheck REFUSED: %s" % _msg)
        print("  `kit deliverycheck <file> --review <dir>`. The dir must be COMPLETE: every frame the")
        print("  review rendered judged, none failed, fewer than half `cannot`. Phase 1 - the lead")
        print("  frames - is not a review and may not be delivered on.")
        print("  --no-review \"<why the client agreed this needs none>\" records the exception in the open.")
        if not _opt(args, "--no-review", ""):
            return 2
        print("  NO-REVIEW RECORDED: %s" % _opt(args, "--no-review", ""))
    else:
        print("kit deliverycheck: %s" % _msg)
    _owe = G.atlas_recreate_owed(ROOT)
    if _owe and _opt(args, "--recreate-waived", ""):
        print("kit deliverycheck: frozen region(s) an edit reached are not measured back (%s) - RECREATE WAIVED: %s" % (", ".join(sorted(_owe)), _opt(args, "--recreate-waived", "")))
        _owe = None
    if _owe:
        print("kit deliverycheck REFUSED: frozen region(s) an edit reached have not been measured back: %s"
              % ", ".join(sorted(_owe)))
        print("  kit atlas recreated <region> --result <the final mesh>   for each. --recreate-waived \"<the client's words>\"")
        print("  records their exception in the open.")
        if not _opt(args, "--recreate-waived", ""):
            return 2
        print("  RECREATE WAIVED: %s" % _opt(args, "--recreate-waived", ""))
    path = str(args[0]).strip().strip('"') if args and not args[0].startswith("--") else ""
    if not path or not os.path.exists(path):
        print(cmd_deliverycheck.__doc__)
        print("\nkit deliverycheck: give it an existing .FCStd")
        return 2
    _rev_dir = os.path.dirname(os.path.dirname(os.path.abspath(path))) if os.path.basename(os.path.dirname(os.path.abspath(path))).lower() == "model" \
        else os.path.dirname(os.path.abspath(path))
    for _rd in {_rev_dir, os.path.dirname(os.path.abspath(path))}:
        _rp = os.path.join(_rd, "README.md")
        if os.path.isfile(_rp):
            try:
                _rt = open(_rp, encoding="utf-8", errors="replace").read()
            except OSError:
                _rt = ""
            _ph = [m_.group(0) for m_ in re.finditer(r"\{\{[^}]*\}\}|\bTBD\b|<fill[^>]*>|\bTODO\b", _rt)]
            if _ph:
                print("kit deliverycheck REFUSED: %s holds %d placeholder(s) - %s. A README is written from the measured results"
                      " after the model exists; fill it before the delivery." % (_rp, len(_ph), ", ".join(_ph[:5])))
                return 2
    want = {}
    for i, t in enumerate(args):
        if t == "--expect-colour" and i + 1 < len(args) and "=" in args[i + 1]:
            k, v = args[i + 1].split("=", 1)
            want[k.strip()] = v.strip().lower().lstrip("#")
    bodyname = _opt(args, "--body")
    fails, notes = [], []
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        # GuiDocument
        if "GuiDocument.xml" not in names:
            fails.append("NO GuiDocument.xml. This file was saved by `freecadcmd`, which has no GUI "
                         "and therefore no ViewObjects, so colour/visibility do not exist in it. "
                         "Rebuild it by swapping the shape inside the zip; never open and re-save.")
            print("DELIVERYCHECK FAIL\n  - " + fails[0])
            return 2
        doc = z.read("Document.xml").decode("utf-8", "replace")
        gui = z.read("GuiDocument.xml").decode("utf-8", "replace")
    refs = set(re.findall(r'file="([^"]+)"', doc)) | set(re.findall(r'file="([^"]+)"', gui))
    payload = names - {"Document.xml", "GuiDocument.xml", "thumbnails/Thumbnail.png"}      # thumbnail
    orphan, missing = sorted(payload - refs), sorted(refs - payload)
    print("DELIVERYCHECK %s\n  file table: %d reference(s), %d payload entr(ies)"
          % (os.path.basename(path), len(refs), len(payload)))
    if orphan:
        fails.append("%d ORPHAN zip entr(ies) - referenced by nothing: %s" % (len(orphan), orphan[:8]))
    if missing:
        fails.append("%d MISSING entr(ies) - referenced and absent: %s" % (len(missing), missing[:8]))
    # GuiDocument
    try:
        root = ET.fromstring(gui)
    except Exception as e:
        fails.append("GuiDocument.xml does not parse: %s" % str(e)[:120])
        root = None
    colours, bad_counts, vis = {}, [], {}
    if root is not None:
        for vp in root.iter("ViewProvider"):
            nm = vp.get("name") or "?"
            props = vp.find("Properties")
            if props is None:
                continue
            for p in props.findall("Property"):
                if p.get("name") == "Visibility":
                    b = p.find("Bool")
                    if b is not None:
                        vis[nm] = str(b.get("value")).lower() in ("true", "1")
            declared = props.get("Count")
            actual = len(props.findall("Property"))
            if declared is not None and str(declared).isdigit() and int(declared) != actual:
                bad_counts.append("%s says %s, has %d" % (nm, declared, actual))
            for p in props.findall("Property"):
                if p.get("name") == "ShapeColor":
                    c = p.find("PropertyColor")
                    if c is not None and (c.get("value") or "").isdigit():
                        v = int(c.get("value"))
                        colours[nm] = "%02x%02x%02x" % ((v >> 24) & 255, (v >> 16) & 255, (v >> 8) & 255)
    if bad_counts:
        fails.append("Properties Count disagrees with the children on %d ViewProvider(s): %s"
                     % (len(bad_counts), bad_counts[:6]))
    for label, xml, cnt_pat, blk_pat in (("Objects", doc, r'<Objects Count="(\d+)"', r'<Object type="[^"]+" name="'),
                                        ("ObjectData", doc, r'<ObjectData Count="(\d+)"', r'<Object name="'),
                                        ("ViewProviderData", gui, r'<ViewProviderData Count="(\d+)"', r'<ViewProvider name="')):
        m = re.search(cnt_pat, xml)
        if not m:
            fails.append("no <%s Count=...> in the document" % label)
            continue
        declared, present = int(m.group(1)), len(re.findall(blk_pat, xml))
        if declared != present:
            fails.append("%s Count=%d but %d blocks are present: FreeCAD will load %d and DROP the rest "
                         "(the last one written is the delivered body)" % (label, declared, present, declared))
    print("  top-level counts: Objects/ObjectData/ViewProviderData checked against their blocks")
    print("  ShapeColor: %d object(s) carry one" % len(colours))
    if not colours:
        fails.append("NO object carries a ShapeColor. In FreeCAD 1.1 the App-level PropertyMaterial "
                     "(the Default card) wins over a stored ShapeAppearance, so every part renders "
                     "Default grey even though the colours are in the file. Write ShapeColor.")
    for k, v in sorted(want.items()):
        got = colours.get(k)
        if got is None:
            fails.append("%s has no ShapeColor (expected #%s)" % (k, v))
        elif got != v:
            fails.append("%s is #%s, expected #%s" % (k, got, v))
    vis_doc = {}
    try:
        droot = ET.fromstring(doc)
        for ob in droot.iter("Object"):
            nm = ob.get("name")
            props = ob.find("Properties")
            if nm is None or props is None:
                continue
            for p in props.findall("Property"):
                if p.get("name") == "Visibility":
                    b = p.find("Bool")
                    if b is not None:
                        vis_doc[nm] = str(b.get("value")).lower() in ("true", "1")
    except Exception as e:
        fails.append("Document.xml does not parse: %s" % str(e)[:120])
    if bodyname:
        for where, table in (("GuiDocument.xml", vis), ("Document.xml", vis_doc)):
            if bodyname not in table:
                fails.append("%s carries NO Visibility property in %s. The object is either absent "
                             "or unreadable; either way the delivery cannot be verified. Known "
                             "objects there: %s" % (bodyname, where, sorted(table)[:10]))
            elif not table[bodyname]:
                fails.append("%s is HIDDEN in %s. The GUI one is what the viewer obeys; set BOTH. "
                             "A hidden print body opens as an empty document; hiding the assembly "
                             "instead opens as a grey one." % (bodyname, where))
        if bodyname in vis and bodyname in vis_doc and vis[bodyname] != vis_doc[bodyname]:
            fails.append("%s's Visibility DISAGREES between the two files (Gui=%s, Doc=%s). They are "
                         "two separate settings and both must be set." % (bodyname, vis[bodyname],
                                                                          vis_doc[bodyname]))
    for n in notes:
        print("  note: " + n)
    if fails:
        print("DELIVERYCHECK FAIL - %d fault(s):" % len(fails))
        for f in fails:
            print("  - " + f)
        print("  See LEAN_KIT\\HOW_TO_DELIVER_A_COLOURED_MODEL.md. All three faults look identical\n"
              "  on screen and fixing one does not fix the others.")
        return 2
    print("DELIVERYCHECK PASS - the colours are WIRED UP, not merely present.\n"
          "  This is not acceptance: open it in the GUI and look. Only a screenshot of the client's own\n"
          "  session proves the colour paints.")
    return 0


def cmd_verdict(args):
    """kit verdict <step> --artefact <file> [--out <dir>] --pass|--fail --by <who> --saw "<text>"

    RECORD THAT SOMEBODY OPENED THE PICTURES. A gated job refuses until this exists, is about the
    artefact ON DISK, and was written AFTER it.

    THE JOB NEVER CALLS THIS ABOUT ITS OWN OUTPUT. That is the whole point: a script that can
    certify itself certifies nothing. the client, 2026-09-13: *"you should be gated to never be allowed to
    bypass full orbit reviews. I don't care if you think it's wasteful it's absolutely not."*

    `--saw` is not optional and not decoration. One line per frame, in your own words, describing
    what is IN the picture. It is the only part of the record a later reader can use to tell a look
    from a click - and the whole reason the gate exists is L2, the piece with the best numbers of
    six that turned out to be a solid brick.
    """
    step = str((args[0] if args and not args[0].startswith("--") else _opt(args, "--step")) or "").strip()
    art = str(_opt(args, "--artefact") or "").strip().strip('"')
    out = str(_opt(args, "--out") or (os.path.dirname(art) or ".")).strip().strip('"')
    who = str(_opt(args, "--by") or "").strip()
    saw = str(_opt(args, "--saw") or "").strip()
    card = str(_opt(args, "--card") or "").strip()
    call = "fail" if "--fail" in args else ("pass" if "--pass" in args else "")
    miss = [n for n, v in (("<step>", step), ("--artefact", art), ("--by", who),
                           ("--saw", saw), ("--pass/--fail", call)) if not v]
    if miss:
        print(cmd_verdict.__doc__)
        print("\nkit verdict: missing %s" % ", ".join(miss))
        return 2
    if not os.path.exists(art):
        print("kit verdict: %s does not exist, so no verdict can be about it." % art)
        return 2
    if len(saw) < 25:
        print("kit verdict: --saw is %d characters. Write what you SAW, one line per frame.\n"
              "  A verdict with nothing in it is a click, and the gate exists because numbers\n"
              "  cannot separate a blanket from a brick (L2)." % len(saw))
        return 2
    p, d = _verdict_write_plain(out, step, art, who, saw, call, card)
    print("kit verdict: %s recorded for %s (%s) by %s\n  artefact %s  sha %s\n  saw: %s"
          % (call.upper(), step, os.path.basename(art), who, art, d["artefact_sig"], saw))
    if not card:
        print("  WARNING: no --card signature, so a job that signs its card WILL REFUSE this\n"
              "        verdict. That is deliberate: without it, this would be a verdict about a\n"
              "        FILE rather than about the numbers that produced it, and the card could\n"
              "        change underneath it. The job prints its signature - re-run with --card <sig>.")
    print("  written %s" % p)
    return 0


def _verdict_write_plain(out, step, art, who, saw, call, cardsig=""):
    import hashlib
    try:
        with open(art, "rb") as fh:
            sig = hashlib.sha256(fh.read()).hexdigest()[:16]
    except Exception:
        sig = ""
    d = {"verdict": call, "by": who, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "saw": saw,
         "artefact": art, "artefact_sig": sig, "card": cardsig}
    os.makedirs(out or ".", exist_ok=True)
    p = os.path.join(out or ".", "verdict_%s.json" % step)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1)
    os.replace(tmp, p)
    return p, d


def cmd_collected(args):
    W = _wallclock()
    if not W:
        print("kit collected: the wall-clock warden is not installed in this project.")
        return 2
    if not args or args[0].startswith("-"):
        print("kit collected <name> [--kill]   the task is read (and, with --kill, ended by its recorded pid TREE);\n"
              "                                take it off the clock. Never stop a process by a command-line\n"
              "                                pattern - that killed another agent's kernel on 2026-09-24.")
        return 2
    if "--kill" in args:
        pid = W.watch_pid(ROOT, args[0]) if hasattr(W, "watch_pid") else None
        if not pid:
            print("[wallclock] %s has no pid recorded - it was registered without one (`kit watch <name> --pid <N>`\n"
                  "            or a hook launch that returned no pid). Nothing was killed; find the pid yourself\n"
                  "            from the task's own log and end THAT tree only." % args[0])
            return 2
        class _P: pass
        _p = _P(); _p.pid = int(pid); _p.kill = lambda: None
        _kill_tree(_p)
        print("[wallclock] %s: pid tree %d ended." % (args[0], int(pid)))
    if W.watch_clear(ROOT, args[0]):
        print("[wallclock] %s collected." % args[0])
    else:
        print("[wallclock] %s was not being watched. `kit status` lists what is." % args[0])
    return 0


def cmd_before(args):
    """ORCHESTRATOR: render the BEFORE frames for a job and hand them to the worker.

    the client, 2026-09-09: *"Where possible the orchestrator should take renders and pass them to the
    agent with whatever information is relevant for edits. That way the render is only generated
    once and by the one who understands the change."*

    This is the same lesson an earlier kit paid for as an earlier improvement (P10), arriving in the
    lean kit by a different door. There, three workers were handed a survey's NUMBERS and
    CONCLUSIONS but no pictures and no renderer, so all three wrote their own — ~490 lines of
    near-identical scaffolding and 97 renders of one region in one round. Worse, the camera
    directions were TRANSCRIBED rather than shared, so one worker's first camera differed from
    another's by two swapped digits. A camera that differs by a typed digit is a different
    camera, and before-against-after quietly stops being like-for-like.

    Here the shape of the waste is different but the cure is the same. The orchestrator has
    already loaded the body and already knows the region — it measured it to write the card. So
    it renders the BEFORE frames once, from the standard views, focused on the job's box, and the
    card names them. The worker opens those, does its edit, and renders the AFTER frames with the
    same `kit render` call on the same box — so the pair is comparable by construction and nobody
    re-derives a picture that already exists.

    The worker still looks at its OWN after-frames and writes its own HIT/MISS lines. That does
    not change: looking at somebody else's picture is not looking at yours.
    """
    if not args or args[0].startswith("-"):
        print("kit before <job> [--box x0 x1 y0 y1 z0 z1] [--from <brep>]")
        return 2
    name = args[0]
    s = G._require_session(ROOT, "before")
    j = G.job(ROOT, name)
    if not j:
        if os.path.isdir(os.path.join(ROOT, "claude_code", "jobs", name)):
            j = G.job_stub(ROOT, name)
        else:
            print("kit before: no job folder for %r. Run:   kit newjob %s   (then before, "
                  "beforelook, card, job)" % (name, name))
            return 2
    src = _opt(args, "--from") or j.get("region") or s.get("model_of_record")
    if src and not os.path.isabs(src):
        for cand in (os.path.join(ROOT, "claude_code", "bank", src), os.path.join(ROOT, "model", "bank", src), os.path.join(ROOT, src)):
            if os.path.exists(cand):
                src = cand
                break
    if not src or not os.path.exists(src):
        jobdir = os.path.join(ROOT, "claude_code", "jobs", name)
        region = os.path.join(jobdir, "region.brep")
        if os.path.isfile(region):
            print("kit before: the job folder is fine — %s exists — but the base file this "
                  "command was\n  pointed at does not:\n      %s\n"
                  "  That path came from --from, or from the session's model of record, and it "
                  "does not\n  resolve. Check it:   kit status\n"
                  "  If the model of record is wrong, re-open the session with a real path:\n"
                  "      kit open --method --edit-types --state \"...\" --model \"%s\" "
                  "--answer overlap=\"...\" --answer measure=\"...\" --answer punch=\"...\"\n"
                  "  Or render this job's own region directly:\n"
                  "      kit before %s --from \"%s\"" % (region, src, region, name, region))
        else:
            print("kit before: no base file (%s), and %s has no region.brep.\n"
                  "  Run:   kit newjob %s" % (src, jobdir, name))
        return 2
    box = None
    if "--box" in args:
        i = args.index("--box")
        vals = []
        for t in args[i + 1: i + 7]:
            try:
                float(t)
            except ValueError:
                break
            vals.append(t)
        if len(vals) != 6:
            print("kit before: --box needs SIX numbers (x0 x1 y0 y1 z0 z1); got %d: %s"
                  % (len(vals), " ".join(vals) or "(none)"))
            return 2
        box = " ".join(vals)
    box = box or j.get("box")
    if box and len(str(box).split()) != 6:
        print("kit before: the box recorded on job %r is malformed (%r). Re-run with an explicit"
              "\n  --box x0 x1 y0 y1 z0 z1." % (name, box))
        return 2
    out = os.path.join(ROOT, "claude_code", "jobs", name, "before")
    frames = _opt(args, "--frames")
    _dn = _opt(args, "--dossier")
    if _dn:
        _stt, _de = D.status(ROOT, _dn)
        if not _de:
            print("kit before: no dossier %r. kit dossier list" % _dn); return 2
        if _stt == "stale":
            print("kit before: dossier %r is STALE (by %s) — kit dossier refresh %s first." % (_dn, _de["stale"].get("by"), _dn)); return 2
        frames = os.path.join(ROOT, _de["dir"]); args = list(args) + ["--prefix", _dn + "_"]
        if not box:
            box = " ".join("%g" % v for v in _de["box"])
    if frames:
        pref = _opt(args, "--prefix", "") or ""
        try:
            src_pngs = sorted(f for f in os.listdir(frames)
                              if f.lower().endswith(".png") and f.startswith(pref))
        except OSError:
            src_pngs = []
        if not src_pngs:
            print("kit before: no PNG frames in %s%s" % (frames, (" starting with %r" % pref) if pref else ""))
            return 2
        os.makedirs(out, exist_ok=True)
        for f in src_pngs:
            shutil.copyfile(os.path.join(frames, f), os.path.join(out, "before_" + f))
        print("[leangate] %d existing frame(s) reused from %s — no re-render." % (len(src_pngs), frames))
        rc = 0
    else:
        a = [src, "--out", out, "--name", "before"]
        if box:
            a += ["--box", box]
        rc = cmd_render(a)
    try:
        pics = sorted(f for f in os.listdir(out) if f.endswith(".png"))
    except OSError:
        pics = []
    if rc != 0 or not pics:
        print("\nkit before REFUSED: the render produced %d picture(s).\n"
              "  Nothing has been recorded on job %r — a BEFORE set that does not exist must not\n"
              "  end up named on a card. Fix the render first:\n"
              "      kit render %s --out %s --name before%s\n"
              "  and read its output. `kit run` can return 0 on a script that drew nothing."
              % (len(pics), name, src, out, (" --box " + box) if box else ""))
        return 2
    if box:
        G.job_mark(ROOT, name, "box", box)
    if True:
        if stamp_codes(out, G.before_key(name), "before") is False:
            print("\nkit before REFUSED: the frames exist but could not be stamped, so the "
                  "render-first gate\n  has nothing to check. Fix the cause printed above and "
                  "re-run `kit before %s`." % name)
            return 2
        G.job_mark(ROOT, name, "before_dir", out)
        print("\n[leangate] BEFORE FRAMES for %s — %d picture(s) in\n[leangate]   %s"
              % (name, len(pics), out))
        print("[leangate] NOW OPEN THEM AND SAY WHAT IS THERE — this is the render-first gate,")
        print("[leangate] and `kit launched` refuses until it is satisfied:")
        print("[leangate]     kit beforelook %s --saw <frame>=<CODE> --saw ... --says \"...\"" % name)
        print("[leangate] PUT THESE ON THE CARD. The worker opens them, edits, then renders the")
        print("[leangate] AFTER frames with the SAME box, so the pair is comparable by "
              "construction:")
        print("[leangate]     kit render <result.brep> --out <job>/after --name look%s"
              % ((" --box " + box) if box else ""))
        print("[leangate] Do NOT retype a view direction into the card — both sides call the "
              "same renderer.")
    return rc


def cmd_beforelook(args):
    """ORCHESTRATOR: type back the codes from the BEFORE frames and say what is there.

    the client, 2026-09-09: *"Make sure there is a render first requirement for the orchestrator."*
    This is that requirement's proof half. `kit before` renders and stamps; this opens.
    """
    if not args or args[0].startswith("-"):
        print("kit beforelook <job> --saw <frame>=<CODE> [--saw ...] --says \"...\" [--says ...]")
        return 2
    name = args[0]
    codes, says = {}, []
    i = 1
    while i < len(args):
        if args[i] == "--saw" and i + 1 < len(args) and "=" in args[i + 1]:
            k, v = args[i + 1].split("=", 1)
            codes[k] = v
            i += 2
        elif args[i] == "--says" and i + 1 < len(args):
            says.append(args[i + 1])
            i += 2
        else:
            i += 1
    G.before_look(ROOT, name, says, codes)
    return 0


def cmd_newjob(args):
    """Make the job folder and copy the model of record in as region.brep.

    A test orchestrator, 2026-09-09: "`kit newjob` — make the folder and copy the model of record
    in as region.brep. I did it with mkdir and cp. **The lint demands a base file that no command
    produces.**" That last sentence is the whole justification: a rule that requires something no
    command creates is a rule that trains people to work outside the kit.
    """
    if not args or args[0].startswith("-"):
        print("kit newjob <name> [--from <brep>]   (default --from = the session's model of record)\n"
              "kit newjob <name> --mesh <base.stl> [--box \"x0 x1 y0 y1 z0 z1\"]   a MESH job: the base is recorded, no region.brep\n"
              "kit newjob <name> --first \"<why>\"   the project's FIRST BODY (no model of record, no client brep): no base, no region.brep - a sketch_extrude with base=\"\" (31bv B1)")
        return 2
    name = args[0]
    s = G._require_session(ROOT, "newjob")
    # recorded
    mesh_base = _opt(args, "--mesh")
    if mesh_base:
        if not os.path.isfile(mesh_base) or not mesh_base.lower().endswith(".stl"):
            print("kit newjob: --mesh names an STL that must exist: %s" % mesh_base); return 2
        d = os.path.join(ROOT, "claude_code", "jobs", name)
        os.makedirs(d, exist_ok=True)
        import hashlib as _hl
        _h = _hl.md5()
        with open(mesh_base, "rb") as _fh:
            for _ch in iter(lambda: _fh.read(1 << 20), b""):
                _h.update(_ch)
        rec = {"job": name, "kind": "mesh", "base": os.path.abspath(mesh_base), "base_md5": _h.hexdigest(),
               "box": _opt(args, "--box", ""), "when": G._now(), "note": "a mesh job: work on a crop (kit crop), union/splice back; no region.brep"}
        json.dump(rec, open(os.path.join(d, "JOB.json"), "w", encoding="utf-8"), indent=1)
        print("[leangate] job folder %s (MESH job)" % d)
        print("[leangate]   base %s  md5 %s%s" % (rec["base"], rec["base_md5"], ("  box %s" % rec["box"]) if rec["box"] else ""))
        print("[leangate]   Next: kit newcard %s --type mesh_union --write %s   then kit crop <base> --box ... --margin 6" % (name, os.path.join(d, "card.md")))
        return 0
    _first = (_opt(args, "--first", "") or "").strip()
    if _flag(args, "--first") and len(_first) < 12:
        print("kit newjob: --first \"<why this is the project's first body - the client's words>\" (twelve characters at least)"); return 2
    if _first:
        if s.get("model_of_record"):
            print("kit newjob: --first is for a project with NO model of record; this session has one (%s) - `kit newjob %s` starts a job on it" % (s.get("model_of_record"), name)); return 2
        d = os.path.join(ROOT, "claude_code", "jobs", name); os.makedirs(d, exist_ok=True)
        json.dump({"job": name, "kind": "first", "base": "", "why": _first, "when": G._now(),
                   "note": "the project's first body: a sketch_extrude with base=\"\" (the piece alone) - no region.brep and nothing to check against; look at the result (kit render), copy it into claude_code\\bank\\, kit promote it, kit cancel this job (PROJECT_START.md 1)"},
                  open(os.path.join(d, "JOB.json"), "w", encoding="utf-8"), indent=1)
        print("[leangate] job folder %s (THE FIRST BODY - no base: %s)" % (d, _first))
        print("[leangate]   Next: kit newcard %s --type sketch_extrude --write %s   (Base: none - the first body; Row: none - the client <date>: '<the client's words>')," % (name, os.path.join(d, "CARD.md")))
        print("[leangate]         kit job, kit run with base=\"\" and op='piece'; then kit render the result, copy it into claude_code\\bank\\, kit promote it,")
        print("[leangate]         and kit cancel %s --why \"the first body - promoted from the bank (31bv B1)\" takes the job off the books (nothing checks a body against no base)" % name)
        return 0
    src = _opt(args, "--from") or s.get("model_of_record")
    if not src:
        print("kit newjob: no --from and the session has no model of record. THE FIRST BODY of a project (31bv B1): `kit newjob <J> --from <a brep the client exported>`,\n"
              "  or `kit newjob <J> --first \"<why>\"` - a sketch_extrude job with base=\"\" (the piece alone, no region.brep) - LEAN_KIT\\PROJECT_START.md; `kit open` prints the steps.")
        return 2
    if not os.path.isabs(src):
        for cand in (os.path.join(ROOT, "claude_code", "bank", src), os.path.join(ROOT, "model", "bank", src), os.path.join(ROOT, src)):
            if os.path.exists(cand):
                src = cand
                break
    if not os.path.exists(src):
        print("kit newjob: no such base file: %s" % src)
        return 2
    d = os.path.join(ROOT, "claude_code", "jobs", name)
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, "region.brep")
    # over the
    if os.path.exists(dst):
        try:
            import stat as _st
            os.chmod(dst, _st.S_IWRITE | _st.S_IREAD)
        except OSError:
            pass
        os.remove(dst)
    how = "linked to"
    # body_trial.brep
    _bank_ = os.path.normcase(os.path.join(ROOT, "claude_code", "bank")) + os.sep
    if not os.path.normcase(os.path.abspath(src)).startswith(_bank_):
        shutil.copyfile(src, dst); how = "copied from (not a bank file - only the bank's model is hard-linked and made read-only; 31bq R7W D11)"
    else:
        try:
            os.link(src, dst)
        except OSError as e:
            shutil.copyfile(src, dst); how = "copied from (no hard link: %s)" % e
    try:
        import stat as _stat
        os.chmod(dst, _stat.S_IREAD)
        if how == "linked to":
            os.chmod(src, _stat.S_IREAD)
    except OSError:
        pass
    print("[leangate] job folder %s" % d)
    print("[leangate]   region.brep %s %s  (READ-ONLY%s; write results to result.brep)" % (how, src, ": it shares the bank's bytes" if how == "linked to" else ""))
    try:      # kit tool extract
        json.dump({"job": name, "kind": "brep", "base": os.path.abspath(src), "how": how.split(" (")[0], "when": G._now()}, open(os.path.join(d, "JOB.json"), "w", encoding="utf-8"), indent=1)
    except OSError as _exj: print("[leangate]   (JOB.json not written: %s)" % _exj)
    print("[leangate]   Next: kit newcard %s --type <t> --write %s"
          % (name, os.path.join(d, "CARD.md")))
    return 0


def _strip_prefix(p):
    r"""31bq R7W W2 (fres F2 / F4, 2026-10-23): a Windows extended-length or device prefix taken off a name that has a drive or a share behind it - \\?\C:\x -> C:\x,
    \\.\C:\x -> C:\x, \\?\UNC\srv\sh\x -> \\srv\sh\x. A \\?\Volume{GUID}\ or \\?\GLOBALROOT name is returned as given (its drive form is its REAL path - _real_path)."""
    p = str(p or "")
    if p.startswith("\\\\?\\UNC\\"):
        return "\\\\" + p[8:]
    if p[:4] in ("\\\\?\\", "\\\\.\\") and len(p) > 5 and p[5] == ":":
        return p[4:]
    return p


def _real_path(p):
    r"""fix-route-end-seen (verify-route-end's seen (4), 2026-10-23): the file a path NAMES. os.path.realpath resolves a junction, a symlink and an 8.3 short
    name (abspath only folds '..' and the slashes, normcase the case). Compare two of these by os.path.normcase. A path that cannot be resolved is its abspath.
    31bq R7W W2 (fres F4): realpath FIRST on the name as given, the prefix off the RESULT - stripped first, a \\?\Volume{GUID}\ or \\?\GLOBALROOT\Device\ name
    had come out under the CWD (the verifier's S18 / S19); realpath on the name as given gives \\?\C:\..., which _strip_prefix then settles."""
    p = str(p or "")
    try:
        r = os.path.realpath(p)
    except (OSError, ValueError):
        r = os.path.abspath(p)
    return _strip_prefix(r)


def _file_id(p):
    """31bq R7W W2 (fres F1 / F3 / F5): a file's identity (st_dev, st_ino) - None when it cannot be read or the volume gives no index (st_ino 0)"""
    try:
        st = os.stat(str(p or ""))
    except (OSError, ValueError):
        return None
    return (st.st_dev, st.st_ino) if st.st_ino else None


def _same_file(a, b):
    """31bq R7W W2 (fres F1 / F3 / F5): two names of ONE file - by the real path (normcase), else by the file identity (a hard link; a UNC alias of the local
    drive, which realpath cannot join back to its folder)"""
    a = str(a or ""); b = str(b or "")
    if not a or not b:
        return False
    if os.path.normcase(_real_path(a)) == os.path.normcase(_real_path(b)):
        return True
    ia = _file_id(a)
    return ia is not None and ia == _file_id(b)


def _in_folder(p, folder):
    """31bq R7W W2 (fres F1 / F5): p names a file UNDER folder - its real path under the folder's real path, or one of the name's parent folders IS the folder
    by identity (the UNC alias / a `net use` drive: the verifier's S15-S17; about a dozen stats up the tree)"""
    rp = os.path.normcase(_real_path(p)); rf = os.path.normcase(_real_path(folder)).rstrip(os.sep) + os.sep
    if rp.startswith(rf):
        return True
    fid = _file_id(folder)
    if fid is None:
        return False
    d = os.path.dirname(_strip_prefix(os.path.abspath(str(p or "")))); n = 0
    while d and n < 48:
        if _file_id(d) == fid:
            return True
        up = os.path.dirname(d)
        if up == d:
            break
        d = up; n += 1
    return False


def _jobs_file(p):
    """31bq R7W W2 (fres F3 / F5): (True, what it is) when p names a file of the project's jobs folder - under it by its real path or by a parent's identity, or
    a HARD LINK of one (st_nlink > 1 and its identity found in the jobs walk - 42,906 files in 0.37 s on the project, walked only for a multi-link name) that is not a
    bank file's identity (`kit newjob` hard-links the bank's master into every job as region.brep - the bank master has nlink 15 and is no jobs file). A file whose
    real path is in the bank is no jobs file. (False, "") otherwise."""
    jobs = os.path.join(ROOT, "claude_code", "jobs"); bank = os.path.join(ROOT, "claude_code", "bank"); given = _strip_prefix(os.path.abspath(str(p or "")))
    if _in_folder(p, bank):
        return False, ""
    if _in_folder(p, jobs):
        rp = _real_path(p)
        if os.path.normcase(rp) == os.path.normcase(given) and os.path.normcase(rp).startswith(os.path.normcase(_real_path(jobs)).rstrip(os.sep) + os.sep):
            return True, "a file in a job folder"
        return True, "a file in a job folder - by its REAL path %s, in the project's jobs folder %s (the name given resolves there)" % (rp, _real_path(jobs))
    try:
        st = os.stat(str(p or ""))
    except (OSError, ValueError):
        return False, ""
    if st.st_nlink > 1 and st.st_ino:
        me = (st.st_dev, st.st_ino)
        bank_ids = set(x for x in (_file_id(os.path.join(bank, f)) for f in (os.listdir(bank) if os.path.isdir(bank) else [])) if x)
        if me in bank_ids:
            return False, ""
        for dp, dn, fn in os.walk(jobs):
            for f in fn:
                q = os.path.join(dp, f)
                if _file_id(q) == me:
                    return True, "a HARD LINK of %s (the same file by its identity - st_dev, st_ino)" % os.path.relpath(q, ROOT)
    return False, ""


def _rel_for_record(p):
    r"""31bq R7W W2 (fres F2): a path as the records write it - relative to ROOT with forward slashes; across mounts (os.path.relpath raises ValueError: the \\?\
    prefix, another drive, the project reached through a junction on another drive) the absolute, prefix-free name. Computed BEFORE the session write."""
    p = _strip_prefix(str(p or ""))
    try:
        return os.path.relpath(p, ROOT).replace("\\", "/")
    except ValueError:
        return p.replace("\\", "/")


def _record_name(p):
    r"""31bq R7W W2 (fres F2): the model of record is written without an extended-length / device prefix (\\?\C:\x -> C:\x, \\?\UNC\srv\sh\x -> \\srv\sh\x); a
    \\?\Volume{GUID}\ or \\?\GLOBALROOT name as its real path; otherwise the name as given (the REAL path in general would put a project reached through a
    junction on another drive under the wrong root)"""
    s = _strip_prefix(str(p or ""))
    return _real_path(s) if (s.startswith("\\\\?\\") or s.startswith("\\\\.\\")) else s


def cmd_promote(args):
    """Advance the model of record, and say so in STATE.md.

    Same run: "Nothing advances the model of record. After applying both features the gate still
    printed `model of record: .../blockbox_r0.brep`. **Had I fed J04 the original block by
    mistake, the gate would have passed it identically and silently dropped the pocket.**"
    That is a whole feature lost with every check green, which is the failure class this kit
    exists for.
    """
    if not args or args[0].startswith("-"):
        print("kit promote <brep> [--note \"...\"]")
        return 2
    new = _resolve_project_path(args[0])
    if not new or not os.path.isfile(new):
        print("kit promote: no such file: %r (the model of record is a FILE - an empty path or a folder is none; a relative path is tried against the cwd, the project root and claude_code\\ - 31bv)" % (args[0],))
        return 2
    s = G._require_session(ROOT, "promote")
    # recorded
    # HARD LINK of
    _jf, _jwhy = _jobs_file(new)
    if _jf:
        _behind = [n_ for n_, j_ in (G._read(G._p(ROOT, G.JOBS), {}) or {}).items() if isinstance(j_, dict) and j_.get("applied_to")
                   and _same_file(j_["applied_to"], new)]
        if not _behind:
            print("kit promote REFUSED: %s is %s, and no applied job stands behind it (no job's `kit apply` wrote it).\n"
                  "  A job's result becomes the model of record through the apply gate: kit accept <job> --review <dir>, then\n"
                  "  kit apply --job <job>   (a burrito: its body_new.brep is copied into claude_code\\bank\\ and promoted)\n"
                  "  kit apply <body> <piece> fuse|cut <out> --job <job>   (a piece) (31bq R7W D3)" % (new, _jwhy))
            return 2
    # did not happen
    new = _record_name(new); old = s.get("model_of_record"); _rel_new = _rel_for_record(new); _rel_old = _rel_for_record(old) if old else "none"
    s["model_of_record"] = new
    s.setdefault("promotions", []).append(
        {"from": old, "to": new, "when": time.strftime("%Y-%m-%d %H:%M:%S"),
         "note": _opt(args, "--note", ""), "job": _opt(args, "--applied-by", "") or None})
    G._write(ROOT, G.SESSION, s)
    print("[leangate] MODEL OF RECORD: %s\n[leangate]            was: %s" % (new, old or "none"))
    try:      # kit close
        if G.atlas_defer_end(ROOT, "the promotion of %s (%s)" % (_rel_new, time.strftime("%Y-%m-%d %H:%M"))):
            print("[leangate] the atlas deferral ENDS with this promotion (31bv B1): the atlas question is back at the turn's end - `kit atlas init` starts the atlas,\n"
                  "[leangate]   `kit atlas defer --until \"<the client's words>\"` defers it again on the client's word")
    except Exception as _ed:
        print("[leangate] the atlas deferral was NOT ended (%s) - `kit atlas defer --lift`" % _ed)
    # Model of record
    st = os.path.join(ROOT, "STATE.md")
    rel = _rel_new
    note = _opt(args, "--note", "")
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = "- %s  model of record -> `%s`%s\n" % (stamp, rel, ("  — " + note) if note else "")
    try:
        cmd_state(["--note", "MODEL OF RECORD -> %s (was %s)%s" % (rel, _rel_old, ("  - " + note) if note else ""),
                   "--tags", "model=%s" % os.path.basename(new)])
    except SystemExit:
        pass
    except Exception as _es:
        print("[leangate] the promotion was NOT written to STATE_NOW.md (%s)" % _es)
    try:
        if not os.path.exists(st):
            raise FileNotFoundError("no STATE.md at the project root - not created (31bq R7W D13)")
        txt = open(st, encoding="utf-8").read()
        txt, n = re.subn(r"(?im)^(\s*(?:\*\*)?Model of record(?:\*\*)?\s*[:=]).*$",
                         lambda m: "%s `%s`   (updated %s)" % (m.group(1), rel, stamp), txt,
                         count=1)
        if not n:
            txt = txt.rstrip() + "\n\n**Model of record:** `%s`   (updated %s)\n" % (rel, stamp)
        txt = re.sub(r"(?im)^.*nothing (?:else )?has been built.*$",
                     "_(superseded: features have been applied — see the promotion log below.)_",
                     txt)
        if "## Promotions" not in txt:
            txt = txt.rstrip() + "\n\n## Promotions\n\n"
        txt = txt.rstrip() + "\n" + line
        with open(st, "w", encoding="utf-8") as fh:
            fh.write(txt)
        print("[leangate] STATE.md header rewritten and promotion logged.")
    except FileNotFoundError:
        pass
    except OSError as exc:
        print("[leangate] could NOT write STATE.md (%s). It is guard-protected — create "
              ".claude/unlock,\n[leangate]   fix the 'Model of record' line to `%s`, add this "
              "line, and delete the unlock:\n%s" % (exc, rel, line))
    # recorded
    _doc = G.atlas_load(ROOT)
    if _doc and _doc.get("regions"):
        if _opt(args, "--no-atlas", ""):
            _doc["render_skipped"] = {"why": _opt(args, "--no-atlas"), "when": G._now(), "model": new}
            G.atlas_save(ROOT, _doc)
            print("[leangate] atlas NOT re-rendered on the promoted model: %s. `kit deliver` will ask for it." % _opt(args, "--no-atlas"))
        else:
            print("[leangate] re-rendering the atlas on the promoted model (kit atlas render) ...")
            try:
                _rc = _atlas_render(["--model", new], _doc, _doc.get("regions", {}))
            except SystemExit as _e:
                _rc = getattr(_e, "code", 2)
            if _rc:
                print("[leangate] the atlas could not be re-rendered (rc %s). The promotion stands; the map is BEHIND the\n"
                      "[leangate]   model of record and `kit deliver` refuses until `kit atlas render` succeeds or a reason is given." % _rc)
    return 0


CARD_TEMPLATE = """# CARD {job} — {title}

Edit type: {etype}

Row: <ONE letter A-L from the project's <PROJECT>_SUCCESS_CRITERIA.md (PROJECT_SUCCESS_CRITERIA.md on the part), an R<n> of the client's
  work list, or `none - the client <date>: '<the client's words>'` - the row this job satisfies, with its pass test in your own words (the lint accepts
  exactly these forms). No row names it = it is not a job; ask, or `kit failure`.>

Region: <EVERY atlas region in the job's selection, by name (`kit atlas status`), then in words which
  part: "ribcage, vanes - the round under the second vane". Only regions the client confirmed. A FROZEN one may
  be in the selection and is RECREATED at the end of edits - delivery refuses until it is measured back.>

Class: <shape | seal. SHAPE changes what the outside of the part looks like — an airflow surface,
  a transition, a step removed, a blend. SEAL changes only the construction — a weld, a fill
  under a lip, a lamination, a void, a shard, a punch-through. the client 2026-09-10: shape first, seal
  LAST; `kit job` refuses a seal card unless the client named it (--allow-seal). An early corner job was a
  buried weld carded as rows D/I. Decide this from the SYMPTOM → CLASS table in EDIT_TYPES.md.>

Dossier: <the dossier this card's numbers came from (`kit dossier list`; read them with
  `kit dossier show <name>`, never from a fresh kernel call), or "none — <why no measurement is
  needed>". A missing or STALE dossier refuses `kit job`.>

Purpose: <ONE PLAIN SENTENCE saying what this feature is FOR — not what it is.
  "the face looks up and BACK at the viewer", "the pocket clears the connector shroud so the
  cable leaves facing down". You check the finished PICTURE against this sentence, not against
  the numbers you wrote: a number can only be checked against itself. METHOD.md 10 — R1's
  screen faced away from the viewer while every number was right and every check passed.>

Base: {base}
Out:  {out}

Top face: <WHAT THE PIECE'S TOP HAS TO BE, answered BEFORE any number below is written: "a plane"
  (then extrude), or "a piece of the existing skin" (then sketch_connect off the skin's own
  section points — the bedsheet — never an extrusion at any tilt). An early fill job chose
  the edit type from the shape of the HOLE instead of the shape of the SURFACE; ten
  ray stations, a fitted plane and a bound were careful arithmetic in service of the wrong
  shape, and the client rejected it on sight — a fingernail catches on 0.15 mm (an early fill job, 2026-09-10).>

PARAMS:
{params}

Expected: volume change about <N> mm3; faces about +<N>
  <COMPUTE these, do not guess. The face figure is the GROWTH - the NEW faces the edit adds, WITH ITS SIGN (+5 for a rectangular pocket, -N for a cut that removes
  faces; a drop allows no net new face) - never the body's total: an unsigned figure of 40 or more is not taken (31bw). Add 'solids N' to the line only when the edit makes or removes whole bodies on purpose (a pattern of separate copies: the base's + the free copies;
  an assembly losing or joining solids; 31bw B4) - else leave it out: one body stays one, a compound keeps its own count, and kit check judges the count. Volume = plan area x (depth - the air lead-in) — counting the
  lead-in as removed is the commonest card arithmetic error on this project's record. Say
  "about" for faces: cylinder seams split unpredictably.
  This is the tripwire. `kit accept` refuses an apply that misses it by more than 5 %.>

Far limit: <stops N mm short of <the neighbour it might reach> — no punch-through.
  MEASURED on the neighbour, not assumed. The worker cannot check this.>

Box: <x0 x1 y0 y1 z0 z1 — the job's region box: `kit check` judges inside it, and the BEFORE
  and AFTER frames are both rendered from it, so the pair is comparable by construction.>

After: {py} {kit} render <result.brep> --out {out}after --name look --box <the Box above> --job {job}
  <THE WORKER RUNS EXACTLY THIS LINE after its edit, and nothing else for pictures. Without the
  box the after-set is the whole body at 0.35 mm/px and a 4 mm feature is eleven pixels —
  an early fill job (2026-09-10), the first under this method, shipped exactly that.>

Tier: {tier}
"""


def _tier_for(etype):
    """The tier, READ OFF `EDIT_TYPES.md`, which is where it is decided.

    It was the literal `haiku (low effort)` on every card until 2026-09-16 - a second copy of a
    fact whose owner is the catalogue (the kit's rule 0), and WRONG for three of the
    twelve types: `cutter` is `cad-worker-opus` from a filled card, `gapfill` needs the
    orchestrator to write the slab and the probe, and `region_look` has no worker at all. A
    scaffold that prints the wrong tier is a scaffold that launches the wrong agent.
    """
    try:
        txt = open(os.path.join(HERE, "..", "EDIT_TYPES.md"), encoding="utf-8").read()
        sec = re.search(r"^## %s — .*?(?=^## |\Z)" % re.escape(etype), txt, re.M | re.S)
        if sec:
            m = re.search(r"^Tier:\s*(.+?)\s*$", sec.group(0), re.M)
            if m:
                return m.group(1).strip()
    except OSError:
        pass
    return "read EDIT_TYPES.md § %s - no Tier line found there" % etype

_STARTER = {
    "voxel_smooth": (
        "  body: <ABSOLUTE path to the mesh the edit goes into (.stl), NOT the B-rep>\n"
        "  base: <ABSOLUTE path to the UNTOUCHED mesh of the SAME document - the control>\n"
        "  box: <x0 x1 y0 y1 z0 z1 round ONE feature>\n"
        "  feature: <what this region IS, in the project's own words>\n"
        "  defect_class: concave_junction        # the only class this type treats\n"
        "  acceptance: <blend | rim_tolerated>   # route is chosen FROM this\n"
        "  route: <A rebuild+weld | B drop-in | C combine>\n"
        "  h: <cell mm>   r_close: <mm>   r_open: <mm>   sigma: <mm>\n"
        "  g_min: <mm>    t_bury: <mm>    add_open: 0.0   min_vol: <mm3>\n"
        "  keep: <ADD lump ranks, largest = 1 - leave empty and V2 stops so you look>\n"
        "  do_rem: <no | yes>   keep_rem: <REM lump ranks>   min_vol_rem: <mm3>\n"
        "  lead: <two or more frame names YOU decided show this feature>\n"
        "  reference: <the APPROVED build to put in the frame beside it, if one exists>\n"
        "  headline_mm3: <the reference's own volume - a build materially under it is a report>"
    ),
    "sketch_extrude": "  base=<ABSOLUTE path to region.brep>\n"
                      "  outline=rect            # rect | circle | polygon\n"
                      "  rect_w=<W>  rect_h=<H>  cu=0.0  cv=0.0\n"
                      "  circle_d=<D>            # only for outline=circle\n"
                      "  polygon=[(u,v), ...]    # only for outline=polygon\n"
                      "  plane_origin=(<x>, <y>, <z>)  plane_normal=<+z>  plane_udir=<+x>\n"
                      "  corner_radius=0.0\n"
                      "  extra_rects=[]  extra_circles=[]\n"
                      "  depth=<D>  op=<add|cut|piece>\n"
                      "  piece_name=<ABSOLUTE path to piece_*.brep>\n"
                      "  result_name=<ABSOLUTE path to result.brep>",
    "hole": "  base=<ABSOLUTE path to region.brep>\n"
            "  holes=[dict(start=(<x>, <y>, <z>),   # a point 2 mm OUTSIDE the face the hole enters (in air)\n"
            "              axis=(<dx>, <dy>, <dz>),  # the direction INTO the material\n"
            "              d=<diameter>, depth=<from start: 2 mm air + the bore; a through hole: past the far face + 2>,\n"
            "              cbore_d=<diameter, 0 = no counterbore>, cbore_depth=<mm, 0 = none>),   # one dict per hole - all cut in one step (31bs T1 F3: 0, never None)\n"
            "         ...]\n"
            "  piece_name=<ABSOLUTE path to piece_holes.brep>  result_name=<ABSOLUTE path to result.brep>\n"
            "  <a tilted bore's lead-in = 2 + r*tan(tilt)>   (31bs W31: these ARE t_hole's PARAMS - the old hint named d / depth / axis / origin, which it has not)",
    "cutter": "  base=<ABSOLUTE path to region.brep>   out_dir=<ABSOLUTE job folder>\n"
              "  why_not_delete=<one line, in your own words - boilerplate is refused>\n"
              "  find=normal=(<x>,<y>,<z>)  tol_deg=<MEASURED, from kit measure faces --normal>\n"
              "        within=(<x0>,<x1>,<y0>,<y1>,<z0>,<z1>)\n"
              "  along=<x|y|z>  cross=<x|y|z>  step=<mm>  cross_samples=<N>\n"
              "  symmetrise=<cross value, or None>  smooth_mm=<mm>  offset_mm=<mm, > the smoothing deviation>\n"
              "  boundary=type=<stations|full>  value=(<lo>,<hi>)\n"
              "  sweep=dir=<+1|-1>  dist_mm=<mm>   cleanup_boxes=<[(x0,x1,y0,y1,z0,z1), ...]>\n"
              "  cross_margin_mm=0.30   # each station's cross extent widened both ways (a round feature's extreme points lie ON the sampled faces: a tool bounded exactly by them leaves zero-volume needles - 31bx R2 F1)\n"
              "  expect=volume_mm3=<REQUIRED>  vol_tol=<fraction, e.g. 0.05>  area_growth_max=<fraction, e.g. 0.02>  thinwall_mm=<the PROCESS minimum for this part>  sliver_mm3=<mm3, e.g. 1.0>  boundary_step_max=<mm, e.g. 0.3>\n",
    "sketch_connect": "  base=<ABSOLUTE path to region.brep>\n"
                      "  planeA=dict(origin=(<x>, <y>, <z>), normal=(<nx>, <ny>, <nz>), udir=(<ux>, <uy>, <uz>))   # outline A lives here\n"
                      "  outlineA=[(u, v), ...]          # the SAME vertex count and order as outlineB\n"
                      "  planeB=dict(origin=..., normal=..., udir=...)\n"
                      "  outlineB=[(u, v), ...]\n"
                      "  corner_radius=<0 or r: > 0 rounds every corner of BOTH outlines>  op=<add|cut|piece>\n"
                      "  piece_name=<ABSOLUTE path to piece_connect.brep>  result_name=<ABSOLUTE path to result.brep>   (31bs W31: t_sketch_connect's own keys)",
    "burrito": "  WIN=<x0 x1 y0 y1 z0 z1: the EDIT REGION's box; every wall in air or thick clean material, never through the feature being fixed, never along a skin (the region step refuses a grazing wall)>\n"
               "  PLANES=<cx cy cz nx ny nz; ...: extra cut planes, outward normals - or empty (an empty value is a decision too); never grazing a skin, never in a design face>\n"
               "  PROTECT=<x0 x1 y0 y1 z0 z1; ...: a box round each designed OPENING only - what is a designed opening is the PROJECT'S ruling (PROJECT_FACTS section 6, its NEWEST line on it; 31br D13), never round enclosed air (L111); set on the REGION step - or empty>\n"
               "  MIRROR=<\"x 0\" | \"nx ny nz c\" | empty: the card's symmetry decision, made ONCE at skin-labels - a symmetric layout is made on one side and mirrored>\n"
               "  tag=<the run's --tag: names every log, env record and REBUILD_*.json>\n"
               "  every other lever VALUE is a suggestion (the client 2026-10-07) - picked by the pictures, recorded; only LEVER_RANGE refuses (SEAM_MAX 0.15 mm is the client's ceiling, lowered only)\n"
               "  THE SKIN ROUTE (the card's Sequence, EDIT_TYPES.md): kit atlas assign <job> --to <region> -> kit rebuild region --set WIN= --set PLANES= --set PROTECT= -> OPEN every\n"
               "    region_cuts_* / region_fit_* frame, kit rebuild judge --what region -> skin-source -> reinsert --set STEP=1 (THE REINSERT FACES FIRST) -> skin-regions -> skin-edges ->\n"
               "    skin-points (PTS_BOX / PTS_DROP with | why) -> skin-labels --set \"MIRROR=...\" -> skin-features (FEATURES with _why) -> skin-layout, judge --what layout ->\n"
               "    skin-lines (LINES / RAILS / _add / _fillets, each with its why), judge --what wires -> skin-build (NURBS first) -> skin-look, judge --what look -> skin-mirror\n"
               "    --set WHAT=piece -> reinsert --set STEP=2 / 3 / 4 --set TRIAL=\"<why>\" -> review-body -> kit rebuild second --what trial --assign (two cad-reviewers) ->\n"
               "    kit rebuild judge --what trial --verdict ok (THE ACCEPTANCE - never rebuilt or re-sewn after)\n"
               "  then the kit's gate: kit review (before/after, one camera, every frame) -> kit check ... --wide-box \"the edit region is the change\" -> the After line -> kit look ->\n"
               "    kit accept -> kit apply --job <job> (the body copied into the bank, promoted) / kit deliver - on the client's word\n"
               "  SHELVED (refused without --set SHELVED_OK=\"<why>\"): the voxel field (arrange .. review), decimate, fillholes, finish, brep, keep, JOIN=fuse",
    "gapfill": "  base=<ABSOLUTE path to region.brep>\n"
               "  slab=(x0, x1, y0, y1, z0, z1)  <the box over the gap: INTO every wall to be touched; its free walls where the fill ends>\n"
               "  probe=(x, y, z)  <a point certainly inside the gap - picks the air piece>\n"
               "  mouths=[\"z1\"]  <the slab walls the fill MAY reach - a LIST of x0 x1 y0 y1 z0 z1 (the fill touching any OTHER wall means the probe sat in exterior air: refused); \"any\" on purpose switches that check off (31bx R2 F2)>\n"
               "  min_piece=5  fuse_fuzzy=0  expect_fill=<mm3 you expect, or None>\n"
               "  out_dir=<ABSOLUTE job folder>  piece_name=<ABSOLUTE fill_gap.brep>  result_name=<ABSOLUTE result.brep>",
    "mesh_union": (
        "  body: <ABSOLUTE path to the mesh the solid goes into (.stl) - the base of the chain, never the body B-rep>\n"
        "  solid: <ABSOLUTE path to the DRAWN closed solid (.stl) - authored in the B-rep world or swept in numpy;\n"
        "          wound outward, checked about its own centre; no face grazing the body (>= 0.3 mm in or out)>\n"
        "  op: <union | cut>                    # cut = kit union --cut (the solid's inside removed)\n"
        "  box: <x0 x1 y0 y1 z0 z1 - the crop box: holds the WHOLE solid with 6 mm to spare; kit crop --margin 6>\n"
        "  expect_mm3: <the solid's own volume, less what already lies inside the body - kit union prints the delta>\n"
        "  cavities: <none expected | which pocket the solid spans and what happens to it>\n"
        "  frozen: <kit atlas find - which frozen regions the box touches; the solid never crosses one>\n"
        "  sequence: kit crop -> kit union [--cut] -> kit splice --into <body> ; read 'seam adds +N'\n"
        "  after: <the crop rendered with jobs\\...\\look\\_look_crop.py or kit render on the crop - never the body>"
    ),
    "mirror_pattern": "  base=<ABSOLUTE path to region.brep>  piece=<ABSOLUTE path to the banked piece to copy>\n"
                      "  include_original=<True|False>  mirror_x=<True|False>  mirror_y=<True|False>  translations=[(dx, dy, dz), ...]\n"
                      "  op=<add|cut>  result_name=<ABSOLUTE path to result.brep>   (31bs W31: t_mirror_pattern's own keys - there is no plane= key)",
    "split": "  base=<ABSOLUTE path>  axis=<x|y|z>  value=<14.0005 - a micron off any existing face; inside the body's range on that axis>\n"
             "  name_below=<ABSOLUTE path to part_base.brep>  name_above=<ABSOLUTE path to part_cover.brep>   (31bs W31: t_split's own keys - axis / value, not plane / c)",
    "edge_round": "  piece=<ABSOLUTE path to a fresh box / extruded outline / cylinder>  radius=<r>\n"
                  "  select=<vertical | all | top | bottom>  result_name=<ABSOLUTE path to piece_rounded.brep>   (31bs W31: t_edge_round's own keys - select, not edges)",
    "revolve": "  base=<ABSOLUTE path to region.brep>  plane=dict(origin=(<x>, <y>, <z>), normal=(...), udir=(...))   # the sketch plane; it must CONTAIN the axis\n"
               "  outline=[(u, v), ...]   # closed automatically; must not cross the axis\n"
               "  axis_point=(<x>, <y>, <z>)  axis_dir=(<dx>, <dy>, <dz>)  angle=<deg>  op=<add|cut|piece>\n"
               "  piece_name=<ABSOLUTE path to piece_revolve.brep>  result_name=<ABSOLUTE path to result.brep>   (31bs W31: t_revolve's own keys)",
    "shell": "  base=<ABSOLUTE path>  open_faces=[\"+z\"]   # a LIST of \"+z\" \"-z\" \"+x\" \"-x\" \"+y\" \"-y\": the faces whose outward normal points this way are removed (31bs T8 F8: a bare \"+z\" is read per character)\n"
             "  wall=<mm, inward>  result_name=<ABSOLUTE path to result.brep>   (31bs W31: t_shell's own keys - wall / open_faces, not thickness / open_face)",
    "move": "  base=<ABSOLUTE path to the part to move>  dx=<0.0> dy=<0.0> dz=<0.0>   # 0.0 is an answer, not a default\n"
            "  rot_axis=(<ax>, <ay>, <az>)  rot_deg=<0.0 = no turn; the turn comes FIRST, then the offset>  rot_about=(<px>, <py>, <pz>)\n"
            "  result_name=<ABSOLUTE path to result.brep>   (31bs W31: t_move's own keys; the turn since 31br B5)",
    "region_look": "  box=<x0 x1 y0 y1 z0 z1>",
}


def cmd_newcard(args):
    """Scaffold a card with every required slot present and marked <...>.

    WHY THIS EXISTS. Measured on the 165 jobs already on disk: worker wall time is a median of
    152 s, while the ORCHESTRATOR gap between jobs has a p90 of 35 minutes. Card-writing is the
    bottleneck, not the worker — and the orchestrator felt it too, because it wrote a 39 KB
    `gen_cards.py` of its own rather than keep writing cards by hand. A scaffold that starts
    with every slot the lint requires is cheaper than either.
    """
    etype = _opt(args, "--type", "")
    if etype not in G.TYPE_TRAPS:
        print("kit newcard <job> --type <edit_type> [--title ...] [--base ...] [--out ...] [--write <path>]   (without --write the scaffold is printed, not written)")
        print("  types: %s" % ", ".join(G.TYPES))
        return 2
    job = args[0] if args and not args[0].startswith("-") else "J00"
    out_dir = _opt(args, "--out", os.path.join(ROOT, "claude_code", "jobs", job) + os.sep)
    _jrec = {}      # no region
    try:
        _jp = os.path.join(ROOT, "claude_code", "jobs", job, "JOB.json"); _jrec = json.load(open(_jp, encoding="utf-8")) if os.path.isfile(_jp) else {}
    except Exception:
        _jrec = {}
    _first_job = (_jrec or {}).get("kind") == "first"
    _params = _STARTER.get(etype, "  <fill from the template's PARAMS block>")
    if _first_job:
        _params = _params.replace("base=<ABSOLUTE path to region.brep>", 'base=""                  # the first body - the piece alone, no base (kit newjob --first; 31bv B1)')
    txt = CARD_TEMPLATE.format(
        job=job, title=_opt(args, "--title", "<what this feature is>"), etype=etype,
        base=_opt(args, "--base", ("none - the first body (no base: kit newjob --first; 31bv B1)" if _first_job else os.path.join(ROOT, "claude_code", "jobs", job, "region.brep"))),
        out=out_dir,
        params=_params,
        tier=_tier_for(etype),
        py='"%s"' % (ENV.get("python") or sys.executable),
        kit='"%s"' % os.path.join(HERE, "kit.py"))
    _dfr = G.atlas_defer_active(ROOT)
    if _dfr:
        txt = re.sub(r"Region: <EVERY atlas region.*?measured back\.>", "Region: no atlas yet (deferred: %s) - the job's place in the part, in words: ..." % str(_dfr.get("until", "")).replace("<", "(").replace(">", ")"), txt, count=1, flags=re.S)
    dest = _opt(args, "--write")
    if dest:
        _dd = os.path.dirname(os.path.abspath(dest)); _jobs = os.path.normcase(os.path.join(ROOT, "claude_code", "jobs"))
        if os.path.normcase(_dd).startswith(_jobs + os.sep) and not os.path.isdir(_dd):
            print("kit newcard REFUSED: %s is a job folder that does not exist yet - `kit newjob %s` first (the folder and its read-only region.brep - none for a --first job), then the card" % (_dd, os.path.basename(_dd))); return 2
        os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
        open(dest, "w", encoding="utf-8", newline="\n").write(txt)
        print("[leangate] card scaffold written: %s" % dest)
    else:
        print(txt)
    traps = G.TYPE_TRAPS.get(etype) or []
    if traps:
        print("\n[leangate] traps for %r — read these while you fill the numbers:" % etype)
        for t in traps:
            print("[leangate]   * %s" % t)
    print("\n[leangate] Every <...> must be replaced. `kit card <path>` refuses a card with a required slot "
          "missing or a <...> left in\n[leangate] Row / Class / Top face (a second instead of a launch); in the other "
          "slots it cannot tell a <...> from a value -\n[leangate] those are yours (31bs T7 F6).")
    return 0


GUARD_MAX_AGE_S = 900


def guard_is_alive(root=None):
    """(ok, message) — has the PreToolUse guard actually run recently?

    WHY kit.py ASKS THIS. The guard is the only thing standing between a worker and FreeCAD
    outside `kit run`, `kit check` without --as-orchestrator, and writes into the model bank.
    It is wired in .claude/settings.json, and a hook whose command cannot launch DOES NOT FAIL
    LOUDLY — it sits there looking installed while every rule in METHOD.md 5 that says "the hook
    refuses it" quietly becomes advice.

    That is not hypothetical. The shipped settings.json named `python3`, and the client's Python is a
    python.org 3.12 install: on Windows that provides `python.exe` and the `py` launcher and no
    `python3.exe` whatsoever. So the guard had never run, and nothing anywhere said so.

    A hook cannot report its own absence. This can: guard.py touches .claude/.guard_alive on
    every invocation, and the Bash call that reaches kit.py went through PreToolUse moments ago —
    so a stale or missing heartbeat means the guard did not fire for THIS call.
    """
    root = root or ROOT
    hb = os.path.join(root, ".claude", ".guard_alive")
    if not os.path.exists(hb):
        return False, ("no .claude/.guard_alive — the PreToolUse guard has never run in this "
                       "project.")
    age = time.time() - os.path.getmtime(hb)
    if age > GUARD_MAX_AGE_S:
        return False, ("the guard's last heartbeat is %d minutes old; this call did not go "
                       "through it." % int(age // 60))
    return True, "guard alive (%ds ago)" % int(age)


def warn_if_unguarded():
    """Say the guard is not running — ONCE per session, and diagnose it correctly.

    IT USED TO PRINT ~15 LINES ON EVERY ORCHESTRATOR COMMAND. A test orchestrator piped nearly
    every command through `grep -v` to suppress it, and that cost it an exit code: it recorded
    `kit look`'s refusal as exiting 0 when it exits 2, and only caught the error by re-testing
    with PIPESTATUS. Its verdict: **"A noisy banner trains you to filter, and filtering hides
    refusals."** That is the same failure an earlier kit paid for at P17, where a worker's filter
    tore a trap banner into fragments that then read as measurement output.

    The diagnosis was also wrong. It said "fix the install", and the install was fine — the hooks
    simply cannot fire outside Claude Code. Prescribing a reinstall that changes nothing is how a
    warning gets classified as noise, and once classified it is filtered for good.
    """
    ok, msg = guard_is_alive()
    if ok:
        return
    flag = os.path.join(G.store(ROOT), ".unguarded_said")
    try:
        if os.path.exists(flag) and (time.time() - os.path.getmtime(flag)) < 6 * 3600:
            sys.stderr.write("[kit] (the PreToolUse guard is not running in this shell - said in full once per 6 h, last at %s; `kit status` says why)\n"
                             % time.strftime("%H:%M", time.localtime(os.path.getmtime(flag))))
            return
        os.makedirs(os.path.dirname(flag), exist_ok=True)
        open(flag, "w").close()
    except OSError:
        pass
    inside_cc = bool(os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("CLAUDE_SESSION_ID"))
    sys.stderr.write(
        "\n" + "!" * 78 + "\n"
        "THE PRETOOLUSE GUARD IS NOT RUNNING - %s\n" % msg +
        "\n"
        "Nothing is enforcing METHOD.md 5 right now: a worker could run FreeCAD outside\n"
        "`kit run`, call check/apply/measure without --as-orchestrator, or write into the bank.\n"
        "\n" +
        ("The hooks are wired but have not fired. If you are NOT running inside Claude Code -\n"
         "a harness, a plain shell - that is expected and there is nothing to fix; the gates in\n"
         "kit.py still apply.\n"
         "\n"
         "INSIDE Claude Code the commonest cause is THE FOLDER IT HAS OPEN. Claude Code reads\n"
         ".claude\\settings.json and .claude\\agents\\ from its project root. Pointed at a PARENT\n"
         "folder holding several projects, it finds neither, and NOTHING SAYS SO: the hooks never\n"
         "fire, and cad-worker-haiku / sonnet / opus are not loaded either, so workers run as\n"
         "generic agents instead of at their tested tiers. Happened 2026-09-09; hence this note.\n"
         "\n"
         "THE PROJECT ROOT MUST BE THIS FOLDER, not its parent:\n"
         "    " + ROOT + "\n"
         "  * in the Claude desktop app: change the folder the project is open on;\n"
         "  * in a terminal: restart Claude Code from inside that folder.\n"
         "(In the desktop app there is no working directory to change: reopen the project folder there.)\n"
         "\n"
         "If the root is already right, the install is broken. Check it:\n"
         if not inside_cc else
         "You appear to BE inside Claude Code. Two causes, in order of likelihood:\n"
         "  1. Its project root is a PARENT folder, so it never found .claude\\ at all. The root\n"
         "     must be:  " + ROOT + "\n"
         "     In the desktop app, change the folder the project is open on. In a terminal,\n"
         "     restart from inside that folder.\n"
         "     (The same cause stops cad-worker-haiku / sonnet / opus being loaded, so workers\n"
         "     run as generic agents rather than at their tested tiers - and nothing says so.)\n"
         "  2. The install is broken. Check it:\n") +
        "    & \"%s\" \"%s\" --project \"%s\" --status\n"
        % (sys.executable, installer_path(), ROOT) +
        "On Windows the interpreter must be a real path or `py` - NOT `python3`, which\n"
        "python.org does not install on Windows at all.\n"
        "\nSaid once per session. Do not filter kit output to hide it: a filter that removes a\n"
        "banner removes refusals too, and that has already cost this project a misread exit code.\n"
        + "!" * 78 + "\n\n")


def root_hint():
    return ROOT


def installer_path():
    """Where install_lean_hooks.py ACTUALLY is, so the command printed can be pasted.

    A path that is merely plausible is the thing being avoided here. The kit is deployed as a
    COPY inside the project (`<project>\\claude_code\\kit\\`), while the installer lives in the
    master `LEAN_KIT\\` — so deriving it from this file's own location gives a path that does not
    exist, which is worse than a placeholder because it looks right.
    """
    import glob as _glob
    here_up = os.path.dirname(HERE)
    for cand in (os.path.join(here_up, "install_lean_hooks.py"),
                 os.path.join(os.path.dirname(here_up), "LEAN_KIT", "install_lean_hooks.py")):
        for hit in (sorted(_glob.glob(cand)) if "*" in cand else [cand]):
            if os.path.exists(hit):
                return hit
    # does not exist
    return os.path.join(here_up, "install_lean_hooks.py")


_BRIEF_LOUD = ("REFUSED", "FAILED", "WARNING", "!!!", "***", "FAIL", "NOT ", "not made", "OFF THE MESH", "does not fit", "GIVEN UP", "SELF-INTERSECT", "BALLOON", "DEFECTIVE",
               "still open", "no better", "HIDDEN FROM", "TO DECIDE", "refused", "Traceback", "RISES", "cannot", "failed", "error:", "KILLED", "COINCIDENT",
               "capped", "no mirrored", "missing", "UNCUT", "NO corner face", "MEET ALONG", "VOLUME", "GATE PASSED")
_BRIEF_LOUD_CI = ("unmeasured", "not clear", "could not be measured", "no patch comes from", "get no face", "could not hold", "not closed", "error", "exception",
                  "invalid", "warning", "slit", "could not", "disagree", "not read", "out of range", "wrong chain")
_BRIEF_LOUD_RE = re.compile(r"\bIN \d+ PIECES\b")
def _brief_keep(s):
    noisy = s.lstrip().startswith("[leangate]") or s.lstrip().startswith("[kit]") or bool(re.match(r"^\s*\d+s\s{4,}\S", s))
    sl = s.lower()
    loud = any(w in s for w in _BRIEF_LOUD) or any(w in sl for w in _BRIEF_LOUD_CI) or bool(_BRIEF_LOUD_RE.search(s))
    return loud or not noisy


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if len(sys.argv) < 2: print(__doc__); sys.exit(0)
    c = sys.argv[1]; args = [t for t in sys.argv[2:] if t != "--as-orchestrator"]
    if c in ("--help", "-h", "help") and not args:
        print(__doc__); sys.exit(0)
    if c == "help":
        c, args = args[0], ["--help"]

    if "--brief" in args:
        args = [t for t in args if t != "--brief"]
        import builtins as _b
        _real_print = _b.print

        def _brief_print(*a, **k):
            s = " ".join(str(x) for x in a)
            if _brief_keep(s):
                _real_print(*a, **k)
        _b.print = _brief_print
    fn = {"run": cmd_run, "render": cmd_render, "check": cmd_check, "apply": cmd_apply, "templates": cmd_templates, "levers": cmd_levers, "lessons": cmd_lessons, "paths": cmd_paths, "priorart": cmd_priorart, "frozen": cmd_frozen, "visible": cmd_visible, "reach": cmd_reach, "pick": cmd_pick, "inventory": cmd_inventory, "seamweld": cmd_seamweld, "coreplace": cmd_coreplace, "tool": cmd_tool, "atlas": cmd_atlas, "stitchband": cmd_stitchband, "stitch": cmd_stitch, "burrito": cmd_burrito, "stop": cmd_stop,
          "measure": cmd_measure, "facts": cmd_facts, "types": cmd_types, "howto": cmd_howto,
          "state": cmd_state, "clock": cmd_clock, "ruling": cmd_ruling, "route": cmd_route,
          "exam": cmd_exam, "open": cmd_open, "card": cmd_card, "job": cmd_job,
          "look": cmd_look, "accept": cmd_accept, "failure": cmd_failure,
          "newcard": cmd_newcard, "newjob": cmd_newjob, "promote": cmd_promote,
          "before": cmd_before, "beforelook": cmd_beforelook, "close": cmd_close, "launched": cmd_launched,
          "status": cmd_status, "cancel": cmd_cancel, "inbox": cmd_inbox,
          "watch": cmd_watch, "collected": cmd_collected, "ps": cmd_ps, "review": cmd_review,
          "repath": cmd_repath, "verdict": cmd_verdict, "deliverycheck": cmd_deliverycheck,
          "dossier": lambda a_: D.cmd(a_, sys.modules[__name__]),
          "deliver": lambda a_: __import__("kit_deliver").cmd(a_, sys.modules[__name__]),
          "crop": lambda a_: __import__("kit_crop").cmd_crop(a_, sys.modules[__name__]),
          "splice": lambda a_: __import__("kit_crop").cmd_splice(a_, sys.modules[__name__]),
          "union": lambda a_: __import__("kit_union").cmd(a_, sys.modules[__name__]),
          "mesh": lambda a_: __import__("kit_mesh").cmd(a_, sys.modules[__name__]),
          "rebuild": lambda a_: __import__("kit_rebuild").cmd(a_, sys.modules[__name__]),
          "printcheck": lambda a_: __import__("kit_print").cmd_printcheck(a_, sys.modules[__name__]),
          "place": lambda a_: __import__("kit_place").cmd(a_, sys.modules[__name__]),      # recorded
          "printfile": lambda a_: __import__("kit_print").cmd_printfile(a_, sys.modules[__name__])}.get(c)
    if fn is None: print(__doc__); sys.exit(2)
    if c in ("crop", "splice") and (not args or any(t in ("--help", "-h") for t in args)):
        _kc = __import__("kit_crop")
        print((_kc.cmd_crop if c == "crop" else _kc.cmd_splice).__doc__); sys.exit(0)
    if c in ("printcheck", "printfile") and (not args or any(t in ("--help", "-h") for t in args)):
        _kp = __import__("kit_print")
        print(_kp.__doc__ if c == "printcheck" else _kp.cmd_printfile.__doc__); sys.exit(0)
    if c == "mesh" and (not args or any(t in ("--help", "-h") for t in args)):
        sys.exit(__import__("kit_mesh").cmd(["--help"], sys.modules[__name__]))
    if c == "rebuild" and (not args or any(t in ("--help", "-h") for t in args)):
        sys.exit(__import__("kit_rebuild").cmd(["--help"], sys.modules[__name__]))
    # kit measure
    # FAILURES.md
    if c == "deliver" and any(t in ("--help", "-h") for t in args):
        print(__import__("kit_deliver").cmd.__doc__); sys.exit(0)
    if c == "union" and any(t in ("--help", "-h") for t in args):
        print(__import__("kit_union").cmd.__doc__); sys.exit(0)

    if any(t in ("--help", "-h") for t in args) and c not in ("burrito", "repath", "review",
                                                             "verdict", "dossier", "tool", "deliver", "union",      # 31bx (R7 F1 / F2)
                                                             "crop", "splice", "mesh", "rebuild", "printcheck", "printfile"):
        lines = []; _on = False
        for l in (__doc__ or "").splitlines():      # kit measure
            if re.search(r"^\s*(?:python\s+)?kit(?:\.py)?\s+%s\b" % re.escape(c), l): lines.append(l); _on = True
            elif _on and re.match(r"^\s{10,}\S", l): lines.append(l)      # kit close
            else: _on = False
        print("\n".join(lines) if lines else "kit %s" % c)
        if getattr(fn, "__doc__", None):
            print(); print(fn.__doc__.strip("\n"))
        sys.exit(0)
    if c in ("run", "render", "check", "apply", "measure", "burrito", "mesh", "rebuild"):
        warn_if_unguarded()
    if c not in ("run", "render", "facts", "howto", "types", "inbox", "route",
                 "templates", "paths", "levers", "lessons", "priorart", "ps",
                 "atlas", "dossier", "tool", "frozen", "inventory", "coreplace", "seamweld",
                 "stitchband", "stitch", "crop", "splice", "union", "printcheck", "printfile") and not os.environ.get("KIT_NO_INBOX"):
        try:
            G.inbox_banner(ROOT)
        except Exception:
            pass
    if c in ("check", "apply", "measure", "burrito") or \
            (c == "mesh" and args and args[0] not in ("gate", "slots") and "--plan" not in args) or \
            (c == "rebuild" and args and "--plan" not in args):
        try:
            G._require_session(ROOT, c)
        except G.Refused as e:
            print(str(e)); sys.exit(2)
    def _measure_shut(args):
        """31bu (TK2 F5): True when kit measure will REFUSE this bare measurement (the instrument closed after three since the last card) - it is then not counted (the count had run on: 13, 14, 15 while refused)"""
        try: _shut = int((G._read(G._p(ROOT, G.MEASURES), {}) or {}).get("since_card", 0)) >= 3 and any(a_ in ("section", "rays", "dihedral", "faces") for a_ in args[:3])
        except Exception: _shut = False
        if _shut: os.environ["KIT_MEASURE_SHUT"] = "1"
        return _shut
    if c == "measure" and "--dossier" not in args and not _measure_shut(args):
        try:
            _n, _msg = G.measure_tick(ROOT, " ".join(args[:3]))
            if _msg:
                print(_msg)
        except Exception:
            pass
    _t_cmd = time.time()

    def _clock_self(rc_):
        if c in ("crop", "splice", "union", "printfile", "printcheck", "render", "look", "atlas", "review", "mesh", "deliver") \
                and os.path.isdir(os.path.join(ROOT, "claude_code")):
            _secs = time.time() - _t_cmd
            if _secs >= 20:
                try:
                    _sub = (" " + args[0]) if c in ("atlas", "mesh") and args and not args[0].startswith("-") else ""
                    cmd_clock(["add", "kit %s%s" % (c, _sub), "%.0f" % _secs, "--note", "self-clocked%s" % (" (rc %s)" % rc_ if rc_ else "")])
                except SystemExit:
                    pass
                except Exception:
                    pass
    try:
        _rc = fn(args) or 0
        _clock_self(_rc)
        sys.exit(_rc)
    except G.Refused as e:
        print(str(e)); sys.exit(2)
    except KeyboardInterrupt:
        print("\nkit: interrupted. Nothing was left half-written — every register is written to "
              "a temp file\n  and renamed, so the worst case is that this command did not "
              "happen.")
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        try:
            d = G.store(ROOT)
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, "CRASH.log")
            with open(p, "a", encoding="utf-8") as fh:
                fh.write("\n%s  kit %s\n%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"),
                                                 " ".join(sys.argv[1:]), tb))
        except Exception:
            p = "(could not be written)"
        print("\n" + "=" * 78)
        print("THE KIT ITSELF FAILED — this is a DEFECT IN THE KIT, not something you did wrong.")
        print("=" * 78)
        print("  command : kit %s" % " ".join(sys.argv[1:])[:150])
        print("  error   : %s: %s" % (type(e).__name__, str(e)[:200]))
        print("  detail  : %s" % p)
        print("")
        print("  DO NOT try to fix the kit and DO NOT work around it. Record it and tell the client:")
        print("      kit failure --what \"kit %s crashed\" --why \"%s\" \\"
              % (c, type(e).__name__))
        print("          --fix \"reported, not worked around\" --signature \"<what you saw>\"")
        print("  Everything the kit writes is written to a temp file and renamed, so no register")
        print("  is half-written. The safe assumption is that this command did not happen.")
        print("=" * 78)
        sys.exit(2)

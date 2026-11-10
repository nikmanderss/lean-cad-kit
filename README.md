# Lean CAD Kit

A process kit that lets **Claude Code** make controlled, reviewable edits to **FreeCAD** solid models.

**New to the kit? Read [LEAN_KIT_USER_GUIDE_2026-11-06.docx](LEAN_KIT_USER_GUIDE_2026-11-06.docx) first** - the user guide (Word). The pages below are the reference.

The kit treats CAD the way a careful engineer does: every change is a small, named feature drawn as a flat
shape on a known plane and given depth, built as its own piece, checked, looked at, and only then fused into
the model of record. Claude Code runs the work; the kit supplies the method, the commands and the gates that
keep an agent from guessing, skipping the pictures, or editing outside its project.

## Why this kit

Most AI CAD tools either generate a new part from a text prompt or hand back a mesh (STL) that has to be
cleaned up and rebuilt before it is any use for engineering. This kit works the other way round:

- **It edits the model you already have.** Your part stays the model of record. Each change is a small,
  named feature added to it, not a fresh guess at the whole part.
- **The result stays a true B-rep solid.** Edits are flat sketches on known planes given depth (extrude,
  revolve, cut, fuse, round), so the model keeps exact faces, edges and dimensions that you can keep
  working on in FreeCAD, export to STEP, machine or print. The mesh routes are separate, named edit types,
  and the burrito route rebuilds a messy region back into clean B-rep.
- **Every change is checked before it lands.** `kit check` confirms the piece is valid and still one
  solid, the kernel and tessellation volumes agree, the face count is in range, nothing changed outside the
  edit's region box, and no wall was punched through where the job card said it must not be.
- **Pictures come before numbers.** Every result is rendered and reviewed as an orbit of frames by
  reviewer agents and the orchestrator, and the hooks refuse a measurement taken before its subject has
  been looked at.
- **The agent cannot quietly go off-script.** Claude Code hooks refuse FreeCAD runs outside the kit,
  writes outside the project, and ending a turn with work still open. Every number on a job card is
  measured, not guessed.
- **Every edit leaves a trail.** Job folders, cards, renders, review frames and a handoff at session close
  show what changed, why and with which numbers, so the next session picks up where this one stopped.
- **Lean on context, hence the name.** A session never reads the whole kit. The contract is pushed in at
  session start, and `kit route` maps the request to its edit type and the few pages that step needs, so the
  agent reads only what matters for the job in hand. Reading the full kit every session would fill the context
  window and push the session into compaction almost every other message.

## What is in it

| | |
|---|---|
| **The method** | `LEAN_KIT\METHOD.md` (the approach), `LEAN_KIT\CONTRACT.md` (the standing rules, pushed into every session), `LEAN_KIT\ORCHESTRATOR.md` (how to be right about geometry), `LEAN_KIT\PROJECT_LAYOUT.md` (where every file goes) |
| **The edit catalogue** | `LEAN_KIT\EDIT_TYPES.md`: sketch extrude, sketch connect (wedges, tapers), hole, gap fill, cutter, mirror / pattern, split, edge round, revolve, shell, move / place, region look, the **burrito** (a messy region rebuilt as clean B-rep) and the mesh routes (`voxel_smooth`, `mesh_union`) |
| **The kit command** | `LEAN_KIT\kit\kit.py` - one command for every step: routing a request, job folders, cards, running FreeCAD headless under a hard timeout, renders, orbit reviews, checks, acceptance, applying to the model of record, coloured FreeCAD deliveries, print-file preparation |
| **The hooks** | `LEAN_KIT\hooks\` - Claude Code hooks that push the contract at session start, refuse unsafe tool calls (FreeCAD outside the kit, writes outside the project, a measurement before a picture of its subject), keep wall clocks on long steps, and refuse to end a turn with work open |
| **The agents** | `LEAN_KIT\agents\` - worker definitions (`cad-worker-haiku`, `-sonnet`, `-opus`) and the orbit reviewer (`cad-reviewer`), copied into each project by the installer |
| **The installer** | `LEAN_KIT\install_lean_hooks.py` - wires the hooks into one project (`--project`), and after an update of the kit re-wires every project it has wired on the machine (`--all`); the kit itself is never copied into a project |
| **A project template** | `project_template\` - the project's own `CLAUDE.md`, facts file, acceptance table and print-rules file, to copy into a new project folder |
| **A FreeCAD template** | `LEAN_KIT\templates\BLANK_MODEL.FCStd` - a blank document saved from the FreeCAD GUI (the groups, two marker blocks, a placeholder body, the named colours) that the first delivery starts from; `LEAN_KIT\templates\BLANK_MODEL.md` says what is in it |
| **The test suites** | `LEAN_KIT\_run_selftests.py` runs the kit's 28 self-test suites (they need no project and no model of your own) |

## Requirements

| | version this release was tested with |
|---|---|
| Windows | Windows 11 (Windows 10 should work; Linux and macOS are untested) |
| FreeCAD | 1.1 (1.0 is on the search path) - <https://www.freecad.org/downloads.php> |
| Python | 3.12, 64-bit, from python.org - <https://www.python.org/downloads/windows/> - with `numpy`, `scipy`, `pillow`, `matplotlib` |
| Claude Code | the desktop app or the CLI, signed in to an account that can run an Opus- or Fable-class model (the orchestrator) and Haiku / Sonnet (workers) - <https://claude.com/claude-code> |
| Disk | a few GB free on the drive that holds your projects (renders, meshes and body copies add up) |

## Quick start

1. Install Python, the four packages, FreeCAD and Claude Code - **[INSTALL.md](INSTALL.md)**.
2. Put the `LEAN_KIT` folder somewhere permanent, for example `C:\CAD\LEAN_KIT`.
3. Make a project folder outside it (for example `C:\CAD\Projects\MyPart`) and copy the contents of
   `project_template\` into it.
4. Run the installer once for that project, with the full path of your Python:

   ```powershell
   & "C:\Users\<you>\AppData\Local\Programs\Python\Python312\python.exe" "C:\CAD\LEAN_KIT\install_lean_hooks.py" --project "C:\CAD\Projects\MyPart"
   ```

5. Put the starting model (one solid, exported from FreeCAD as `.brep`) in `MyPart\claude_code\bank\` - or leave the bank empty: a project that
   starts from nothing, or from purchased parts, opens on an empty bank and `kit open` prints the first-body route (`LEAN_KIT\PROJECT_START.md`).
6. Open a Claude Code session **in the project folder** (restart it if it was already open - hooks load at
   session start) and describe the change you want. The kit's start sequence is in the project's `CLAUDE.md`
   and in **[GETTING_STARTED.md](GETTING_STARTED.md)**.

## How a session runs, in one paragraph

The session opens with the contract pushed by the SessionStart hook. The orchestrator (an Opus- or Fable-class model)
runs `kit route "<your request>"` to get the edit type and its sequence, finds the region, opens a job folder
(`kit newjob`), writes a job card with every number measured and stated (`kit newcard`, `kit card`), runs the
template itself or hands it to a worker agent at the card's tier (`kit run`, `kit render`), reviews the result
in pictures first (`kit review`, an orbit of frames read by `cad-reviewer` agents and by the orchestrator),
then checks the numbers (`kit check`), records its own reading (`kit look`), accepts (`kit accept`) and applies
the piece to the model of record (`kit apply`, `kit promote`). Deliveries are coloured FreeCAD documents built
by `kit deliver` and checked by `kit deliverycheck`. The session ends with `kit close`, which writes the
handoff for the next one.

## Read next

- **[LEAN_KIT_USER_GUIDE_2026-11-06.docx](LEAN_KIT_USER_GUIDE_2026-11-06.docx) - start here**: the whole kit for the person who runs it - what it is, installing it, starting a project, how to talk to the
  agent and what it will ask you, what every edit type and route does, the gates and why, where files land, the limits, and a one-page cheat sheet.
- [2026-10-30 - Full Section Rework - How It Works - Rev A.pptx](2026-10-30%20-%20Full%20Section%20Rework%20-%20How%20It%20Works%20-%20Rev%20A.pptx) - a slide deck (PowerPoint): one section of a real part rebuilt by the burrito's skin route, step by step, with the kit's own
  pictures. It shows the route as it ran on 2026-10-30; where it and the method pages differ, the method pages are the reference.
- [INSTALL.md](INSTALL.md) - installing everything, wiring a project, checking it works, updating the kit.
- [GETTING_STARTED.md](GETTING_STARTED.md) - the project folder, the first session, the first edit, delivery.
- [RELEASE_NOTES.md](RELEASE_NOTES.md) - what this release is, what is known to be limited.

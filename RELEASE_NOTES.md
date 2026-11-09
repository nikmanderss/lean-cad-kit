# Release notes

## Lean CAD Kit - built 2026-11-09

The kit as it runs today: the method, the edit catalogue, the `kit` command, the Claude Code hooks, the agent definitions, the
installer, a project template, a blank FreeCAD document template and the self-test suites. This folder is BUILT from the
maintainer's working kit at every change, so its text is the kit's own at the build date above.

### Tested with

Windows 11, FreeCAD 1.1, Python 3.12 (numpy, scipy, pillow, matplotlib), Claude Code. All 28 self-test suites pass on this
build, the installer has been run on clean projects, and the routes have been run end to end on scratch projects by test
agents working from these pages.

### Known limitations

| | |
|---|---|
| **Platform** | Built and tested on Windows only. Linux and macOS are untested (INSTALL.md section 10). |
| **Importing** | There is no `kit import`: convert STEP and FreeCAD documents to `.brep` in FreeCAD (GETTING_STARTED.md section 2). A project may start with an empty bank (`LEAN_KIT\PROJECT_START.md`). |
| **Very large meshes** | A body of millions of triangles (a dense vendor model) can outlast a render's silence cap or the review's cap. Render such bodies one at a time, in their own job folder, and give the review box a margin round the feature. |
| **A feature inside a closed solid** | Seen from a side whose view is covered by nearer surface, a review frame reads OCCLUDED; the review passes on the frames that see the box. |
| **The shelved voxel chain** | The burrito's first form (a voxel field) is shelved; its steps are refused without `--set SHELVED_OK="<why>"`. The skin route is how a region is rebuilt. |
| **Hooks need a project session** | The hooks act only in a Claude Code session opened on the project folder. Outside one (a plain shell, a harness), the gates inside `kit.py` still apply and the kit says the guard is not running. |
| **One control manifest per machine** | The installer records the kit's controls in `%USERPROFILE%\.claude\leankit_manifest.json`; after updating the kit, run `install_lean_hooks.py --all` once (INSTALL.md section 8). |

### About the text you will read

- **The code is published without its inline commentary**, except the edit-type templates (their PARAMS field guide)
  and the tools' header comments (`kit tool <name> --help`). Docstrings and every message the kit prints are kept.
- **Rule tags, and the core pages' examples.** The pages (CONTRACT, ORCHESTRATOR, METHOD, PROJECT_LAYOUT, PRINT_READINESS, EDIT_TYPES, STEP_PAGES, the installer's and the kit's own messages) name the parts, jobs and revisions of the project the kit was built on (a vane, a spine, a keel, R18, J01A, d19 ...) where a rule was learned - an example that illustrates the rule, never a requirement of your part. Many rules carry the tag of the kit revision that introduced them (`31br G4c`, `31bq B22`). They are
  kept so a rule can be traced; they need no other document.
- **The client's rulings.** Where a rule came from the design owner's decision, the text quotes it with its date
  ("the client, 2026-10-07: ..."). In your project, *the client* is you, and your rulings go in `PROJECT_FACTS.md`
  section 6 (`kit ruling --said`).
- **Worked examples.** The lessons (`BURRITO_STEPS.md` L1-L157, `KERNEL_LESSONS.md`) were learned on the parts the kit
  was developed on, and their examples use those parts' feature names (vanes, a spine, a keel, a crown, a belly, a
  skirt) and revision labels (R10-R39). They illustrate a rule; they are not requirements of your part.
- **The process-failure sentence.** When an agent measures before it has looked, or overturns what the pictures
  passed, the guard makes it open its next message with a fixed apology sentence. That is deliberate.

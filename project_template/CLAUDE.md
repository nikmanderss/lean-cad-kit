# CLAUDE.md — <PROJECT NAME>

**The kit is `<KIT FOLDER>\LEAN_KIT`, one copy for every project** — `claude_code\WHERE_THE_KIT_IS.md` carries the
generated command lines for this machine. **Run every kit command from `claude_code\`.** The kit and its documents are
never copied into this project.

## Start — in this order, and nothing else is read until the router names it

1. **`CONTRACT.md`, `ORCHESTRATOR.md` and this project's state arrive on their own** — the SessionStart hook pushes them
   before your first prompt. Read them; there is no larger document behind them.
2. **First session on this project only:** `LEAN_KIT\METHOD.md` (the approach) and `LEAN_KIT\EDIT_TYPES.md` (the
   catalogue), once. Then `kit exam` and `kit open` (the three questions are answered from the contract page).
3. **`kit route "<the client's request, in the client's words>"`** — the edit type, its tier, its sequence, and the one
   long-form section to read if the type has one (`kit howto <type> --long` prints it). No match: the symptom table
   prints; classify from a section, route again.
4. **`kit atlas find "<the feature>"`** — the region, its box, whether it is frozen, whether a dossier exists. With no
   atlas yet, propose the regions to the client (`kit atlas init`; METHOD.md section 11) and name the region in words
   on each card meanwhile.
5. **The row.** `PROJECT_SUCCESS_CRITERIA.md` is the acceptance table; nothing is accepted without its row, and a card
   carries `Row:`.
6. Then the sequence the router printed. A dossier is measured once and reused (`kit dossier list` after `kit open`);
   a number you already have goes in with `kit dossier add`.

**Do NOT read at start:** `claude_code\INBOX.md` in full (the kit prints what is new), `KERNEL_LESSONS.md` in full
(`kit lessons --near "<what you are about to do>"` prints the rows for it), `BURRITO_STEPS.md` or
`VOXEL_SMOOTH_STEPS.md` cover to cover (the router prints the section), anything in `_archive\`.

**If a `HANDOVER_*.md` newer than `SESSION_HANDOFF.md` exists in `claude_code\`, the session before you did not close
properly:** read it, then end YOUR session with `kit close`.

## The project

<One paragraph: what the part is, what it does, how it is made (process, material), what it mates to.>

**Model of record: `claude_code\bank\R01_BODY_MASTER.brep`** — `kit open` names the current one and
`SESSION_HANDOFF.md` repeats it; they win over this line if they differ.

**Frozen — recreated at the end of edits:** <the features no edit may change, e.g. the mounting faces, the sealing
surface>. A frozen region may sit inside an edit's selection; it is put back exactly, and delivery refuses until
`kit atlas recreated` measures it.

**B-rep for every WORKER job** — section → draw 2-D → extrude, or connect two drawn 2-D shapes; `kit run` refuses the
rest. The orchestrator-tier exceptions are the burrito (`kit rebuild`) and the mesh routes (`kit mesh`). No lofts.

## Where things go (the full rule: `LEAN_KIT\PROJECT_LAYOUT.md` — the guard refuses a file in the wrong place)

| what | where |
|---|---|
| the client's rulings | `kit ruling --said "<the client's words>"` → `PROJECT_FACTS.md` section 6, dated |
| the state that survives a compaction | `kit state --note "..." --tags "..."` → `claude_code\STATE_NOW.md` |
| every number you measure | `claude_code\MEASUREMENTS.md` (what, measured on what, valid for what) + the region's dossier |
| a step's wall time | `kit clock add <script> <seconds>` → `claude_code\WALL_CLOCKS.md` (the hook reads it) |
| a process failure | `kit failure --what --why --fix --signature --caught gate\|user\|self` → `FAILURES.md` (append-only) |
| friction and its fix | `kit close --improvement "..."` → `PROCESS_IMPROVEMENTS.md` |
| a picture the client is asked to look at | `Deliverables\<REV>\review\` — self-explanatory from its caption |
| every other render | `Deliverables\<REV>\renders\<job or subject>\` |
| the delivered model | `Deliverables\<REV>\model\` via `kit deliver`, on the client's word only |
| the model of record | `claude_code\bank\` (`kit apply` writes there; `kit promote` advances it) |
| a job | `claude_code\jobs\<name>\` — card, script, region.brep, pictures, RESULT.md |
| a round's brief, report, audit | `claude_code\<ROUND>\`, named `R<n>`, `ROUND_<NAME>`, `<NAME>_ROUND` or `CC_<NAME>` (the guard refuses other names) — the folder moves to `_archive\` when the round closes |
| a block for the client or the kit's maintainer | `kit inbox --append <file.md>` |
| inputs the client supplied | `references\` — read, never write |
| anything superseded | `_archive\` — never read at start, never written by you |

## Project-specific standing orders (the generic ones are in CONTRACT.md)

- <Any rule of this project's own: units, naming, which end is front, review cameras the client wants, ...>

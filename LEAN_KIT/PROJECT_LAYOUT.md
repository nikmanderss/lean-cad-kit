# PROJECT LAYOUT — where every file goes, and the two folders an agent may write in

the client, 2026-09-11: *"I am tired of trying to hunt down items to review. … It should only produce
work in two folders. The one it's working in and Deliverables."* This is the standard for every
project on the lean kit. It is not gated; it is a standing order, and a file in the wrong place is
a defect to report and fix like any other.

## The rule

**An agent writes in exactly two places:**

1. **`claude_code\`** — its working folder. The inbox, `jobs\`, `bank\`,
   `dossier\`, its logs, its scratch. Run every kit command FROM this folder so the kit's scratch
   files (`_kit_*.py`, `kit_run.log`) land here and not in the project root. The kit and its documents
   are NOT here: they run from `LEAN_KIT\` (`claude_code\WHERE_THE_KIT_IS.md`).
2. **`Deliverables\<REV>\`** — what the client looks at, by revision. Nothing else. (The agent writes its `review\` and `renders\`; the kit writes `model\` and the delivery files - the guard holds the rest.)

Nothing is ever written to the project root, to `references\`, or to `_archive\` by an agent.

## The tree

```
<PROJECT>\
  CLAUDE.md                     start here (the read order), nothing else to read at start
  PROJECT_SUCCESS_CRITERIA.md  the acceptance table for the round
  PROJECT_FACTS.md              numbers and the client's rulings (`kit facts <keyword>`)
  PROCESS_IMPROVEMENTS.md       friction and its fix, accumulating
  SESSION_HANDOFF.md            written by `kit close`; SESSION_DEFAULTS.md
  FAILURES.md                   written by `kit failure` (root-anchored, whatever folder you run from)
  .claude\                      settings.json (points the hooks at LEAN_KIT\hooks\) and agents\
                                (the installer's; never by hand)
  claude_code\                  THE AGENT'S WORKING FOLDER
     WHERE_THE_KIT_IS.md        generated: the kit and its documents run from LEAN_KIT\
     KERNEL_LESSONS.md          what the kernel does, proven by runs — the agent APPENDS to it
     INBOX.md                   the channel with the auditor; blocks via `kit inbox --append`
     bank\                      THE MODEL OF RECORD and its predecessors (`kit apply` writes here)
     dossier\                   measured regions
     jobs\<JOB>\                one folder per job: card, script, region.brep, RESULT.md, the
                                probe's own pictures, before/after frames. Cancelled or superseded
                                jobs are moved to `_archive\jobs\` by the client's restructure, never
                                left to pile up.
     <ROUND>\                  a round's briefs, reports, friction log - named R<n>, ROUND_<NAME>, <NAME>_ROUND or CC_<NAME>;
                                never loose in claude_code\ (the guard refuses a loose one)
  Deliverables\
     <REV>\review\              EVERY picture the client is asked to look at, this revision, self-
                                explanatory from its caption; sub-folders by subject are fine
     <REV>\renders\             every other render of the revision (surveys, piece looks, result
                                looks) — stamped by job or subject, never a fresh `look2\` per re-render
     <REV>\model\               the delivered FCStd / STEP / STL / brep of the revision
     _archive\_r<NN>\           earlier revisions, same shape
  references\                   inputs the client supplied or approved: BOM, wiring, design spec, the
                                assembly guide and its sources, print-process rules, the design
                                guide, the ledger, a reference model of the surroundings. READ-ONLY for agents.
  _archive\                     everything superseded: old state files, old review sets, retired
                                kits' state, cancelled jobs, root leftovers. Never read at start.
```

`<REV>` is the round's revision (`R18`). A new round makes `Deliverables\R19\review\` on its
first picture; it does not add to the previous one.

## What goes where, decided at the moment of writing

A project that starts FROM PARTS (no model of record yet - a fixture designed round purchased parts): `PROJECT_START.md` is its first page (the first body, the
FreeCAD document from `templates\BLANK_MODEL.FCStd`, placing and turning, the atlas deferred until the model has made progress - 31bv B1).

| the agent is about to write… | it goes to |
|---|---|
| a card, a script, a job's RESULT.md, a probe's sections and maps, before/after frames | `claude_code\jobs\<JOB>\` |
| a picture a kit step makes for its OWN judge — the skin route's frames, `kit tool look_at`'s looks, the body's review (31av: the client, *"Deliverables review or claude code review? I think this is where the agents are getting confused"*) | the job: `claude_code\jobs\<JOB>\skin\review\` (look_at: its `look\` sub-folder), `jobs\<JOB>\review_body\` — `kit rebuild judge` reads them there and nowhere else |
| a picture the client is asked to review (the card names it, the block names it) | `Deliverables\<REV>\review\` — ONLY what the client looks at (a judge never reads it); copy or move it there when it becomes review material |
| any other render (survey, `kit look` on a piece, a result look) | `Deliverables\<REV>\renders\<JOB or subject>\` |
| a new model of record (`kit apply`) | `claude_code\bank\` |
| the revision's deliverable model (at delivery, on the client's word) | `Deliverables\<REV>\model\` |
| a report, a friction log, a brief | `claude_code\<ROUND>\` (a round folder - the guard refuses one loose in `claude_code\`) |
| a block for the auditor | `kit inbox --append <file>` |
| a ruling the client gave | `PROJECT_FACTS.md` (the one root file an agent appends to) |
| **a number you measured** | **`claude_code\MEASUREMENTS.md` — one row: what it is, what it was measured ON, and what it is valid FOR.** See below; this row was missing and the ledger lapsed for four days |
| **the state that must survive a chat compaction** — the TAG KEY first (every tag in the job folder: current / superseded / sweep / poisoned), the current build and its verdict, the live lead with its numbers, what is settled, the next actions in order | **`claude_code\STATE_NOW.md`** — one file, rewritten in place, never a dated copy. A session that is compacted rather than closed leaves no handoff; this is what the next one picks up. The wall-clock warden nudges when the job folder has gained 25 artefacts since it was written (2026-09-17). `kit close` at the end is still the handoff |
| anything else | it does not go anywhere — ask in the inbox |

## Purge, do not pile

When a new edit lands, the renders it supersedes are moved under `Deliverables\<REV>\renders\` (or
deleted if they were never review material) and the job's stale probe pictures are cleared by the
kit's own re-run. Five identical 119 MB `region.brep` copies across cancelled jobs is the state
this rule exists to prevent: a cancelled job's folder is archived whole, at once.

## EVERY NUMBER YOU MEASURE GOES IN THE LEDGER (2026-09-16)

**`claude_code\MEASUREMENTS.md`.** One row per measurement: what it is, what it was measured **on**
(the body, the revision, the box) and what it is valid **for**. It is named here so a session cannot
invent a second one. *(the project's was `LK_MEASUREMENTS.md` until 2026-09-17; it is `MEASUREMENTS.md` now, and the kit knows one name — it says "rename it" if it meets the old one.)*

**Why it is a row in this table.** the client, 2026-09-15: *"have you been adding all of your measurements to
the dossier? If not make sure that you record the instruction is missing for the lean_kit agent."*
It was missing. The ledger was created on their order on 2026-09-11 and its last row was dated
2026-09-11, while **four days of work re-measured the same body** into per-job `status*.json`, `.npz`
and PNG files — and the vane rake, the shelf thickness and the body volume were each **taken twice**,
because the second step had no way to know the first had done it. It lapsed because it was nobody's
step: `kit check`, `kit look` and `kit accept` all gate the PICTURES, and nothing gated the NUMBERS.

**The card's `Dossier:` slot asks where a number came FROM. This asks whether what you measured got
written DOWN.** They are the two halves and neither implies the other.

`kit accept` compares the ledger's timestamp with the newest `status*.json` in the job folder and
says so when the ledger is behind. **It does not refuse** — a refusal at the last gate before the
model of record would strand a session holding work it cannot hand back.

*A measured region's pictures and sections are the dossier's half (`kit dossier take`), and that half
is already gated: applying a job marks the dossiers its box touches STALE, and `kit job` refuses a
card written on a stale one. Nothing there needs building.*

## ONE OF EACH DOCUMENT — the rule that stops the pile-up (2026-09-16)

the client: *"make sure things are organized appropriately and future agents are instructed so this file
runaway doesn't happen again."* Measured the day it was written: one project's `claude_code\` held
**six** `HANDOVER_*.md`, four round reports and briefs from a round that had closed, two merge
requests and two loose `.ps1` scripts — and its `CLAUDE.md` named one handover by filename, which
was no longer the newest. **A reader cannot tell which of six is current, and the newest is not
always the right answer.**

**There is ONE of each of these, always, and its name never carries a date or a round:**

| one file | what it is | who writes it |
|---|---|---|
| `SESSION_HANDOFF.md` | where the work stands, at the project root | `kit close` |
| `FAILURES.md` | process failures, at the project root — append-only; a `RESOLVED: row N` row closes row N | `kit failure` writes; `LEAN_KIT\failures_review.py` reviews and closes (whoever maintains the kit — the kit never reads it back) |
| `PROCESS_IMPROVEMENTS.md` | friction and its fix | the session, appending |
| `KERNEL_LESSONS.md` | what the kernel does, in `claude_code\` | the session, appending a row |
| `INBOX.md` | the channel with the auditor | `kit inbox` |

**Append to the one that exists. Never start `HANDOVER_<date>.md`, `NOTES_v2.md` or
`REPORT_round3.md` beside it** — that is the drift this rule exists to stop, and a second
tracking file needs the client's yes.

**A round's own files live in `claude_code\<ROUND>\`** — its brief, its reports, its audit, its
friction log — and **the whole folder moves to `_archive\` when the round closes**, in one act, the
same way a cancelled job's folder does. Nothing a closed round produced stays loose in
`claude_code\`.

**A round's folder has one of four names** (the guard's rule, stated here since 31bs K15): `R<NN>\` (a revision round), `CC_<NAME>\`,
`ROUND_<NAME>\` or `<NAME>_ROUND\` - upper case, digits and underscores. The kit's own folders beside them: `jobs\<JOB>\` (a job's files), `dossier\`, `bank\` (the kit
writes it), `_archive\`, `_to_delete\` and `scratch\`; a new file in any other folder of `claude_code\` is refused (31bs T7 F16).

**Scripts are not documents.** A one-off `.ps1` or `.py` written to fix something belongs in the job
folder it served, or in `_archive\` once it has run. If it is worth keeping, it is a `kit` command
and the kit maintainer adds it to the kit — *"When the kit lacks the command you need, say so (`kit failure`) — do not
write a script beside the kit"* (`ORCHESTRATOR.md` §3).

`kit close` counts the loose documents in `claude_code\` and names them when the pile grows. It does
not refuse — a refusal at close would strand a session that has work to hand back.

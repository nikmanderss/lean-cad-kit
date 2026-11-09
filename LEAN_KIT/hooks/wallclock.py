#!/usr/bin/env python3
"""wallclock.py - THE WALL-CLOCK WARDEN. PostToolUse hook, plus a small CLI the kit calls.

WHY THIS EXISTS, AND WHY THE CLOCK THAT WAS ALREADY HERE DID NOT CATCH ANYTHING.

the client, 2026-09-14: *"There should be a wall clock monitor gate/hook/warden - not sure which but
whatever it is, it's not working."* The client is right, and the reason is worth stating exactly, because
the machinery was all present and none of it could have fired.

`leangate.wall_status()` has been the kit's wall clock since 2026-09-09. It is correct code. It
failed on all three of the ways a monitor can fail at once:

  1. **IT IS PULL-ONLY.** It is printed in exactly one place - inside `status()`, i.e. when
     somebody types `kit status`. An agent that has stopped watching the clock is, by definition,
     an agent that is not typing `kit status`. The one failure the clock exists to catch is the
     one that stops it being read. L14, 2026-09-13: *"a silent wait looks exactly like a silent
     success."*

  2. **ITS DOMAIN IS JOBS, AND THE STALLS WERE STEPS.** It reports registered jobs - opened with
     `kit job`, started with `kit launched`. The R19 burrito run's two stalls were neither: a
     sweep driver that spent **441 s per combo on ~40 s of real work** (six combos, 44 minutes),
     and a background wrapper left alive for **two hours** after its answer had been read
     elsewhere. Both were raw Bash. A diligent `kit status` would have printed nothing about
     either. This is P08's shape again - *a detector whose search domain is not the thing it is
     meant to detect measures its domain.*

  3. **ITS BUDGET IS 30x THE REAL STEP.** `WALL_MIN_DEFAULT = 15` minutes. `BURRITO_STEPS.md`'s
     own runbook has said since 2026-09-13 that S3 takes ~13 s, S4 ~20 s, S5 ~25 s, S7 ~20 s and
     an orbit render ~2 min, and L11 states the rule: *"Every step in this process took at most
     3 minutes... If they can't report back with some form of progress then cancel and
     restructure your instructions."* **The expectations were written in a document and the clock
     was written in code, and nothing joined them.** A 15-minute budget cannot notice a 30-second
     step taking seven minutes.

  And a fourth, which is a choice rather than a defect but belongs in the same paragraph:
  `wall_status()` is deliberately *"Reported, never refused"*. That is right for KILLING a worker
  - a gate that killed one mid-write would lose the RESULT.md that says why it was stuck. It is
  wrong for BEING READ. So this warden never kills anything and never blocks work; it spends one
  refused tool call to put the finding in front of the agent, and the very next call goes through.

WHAT THIS FILE DOES, IN ONE LINE EACH:

  * `guard.py` (PreToolUse) stamps the start of every tool call into `WALLCLOCK.json`.
  * this file (PostToolUse, matcher `Bash|Task|Agent` - 31bs K7: the sub-agent tool is named Agent) reads that stamp, so the duration it measures is
    **the tool's own wall time** - not the gap between calls, which also contains the model's
    thinking and any wait for the client, and would cry wolf on both.
  * a step over its budget, a background task nobody collected, or a registered job past its
    budget is written to stderr with `exit(2)`, which is how a PostToolUse hook hands text to the
    agent. Nothing is blocked: the tool has already run.
  * each finding speaks ONCE, then stays quiet for 10 minutes or until the overrun doubles. P17's
    lesson: *"a wall that is right the first time and noise every time after"* trains agents to
    filter, and a filter eventually removes the line that mattered.

WHAT IS NOT PROVEN AND MUST BE TESTED LIVE (the kit maintainer, 2026-09-14 - flagged to the client, not hidden):

  * That a PostToolUse hook's `exit 2` stderr reaches the agent on this Claude Code build. Every
    other part of this file is ordinary Python and is covered by `selftest_wallclock.py`; that one
    is a property of the harness and can only be observed in a real session. **Test 1 in
    the kit's development record.**
  * The automatic registration of background work reads `tool_input.run_in_background` and the
    shell id out of `tool_response`. Those field names are the harness's, not the kit's, and this
    file has never seen a real one. Every read is defensive and a miss costs nothing but a missing
    finding. **Test 2 in the kit's development record.**

SAFETY. This file can never be the reason work stops. Every path is inside one try/except that
exits 0. `LEANKIT_WALLCLOCK=off` in the environment disables it entirely. It writes one small JSON
file and reads no CAD.
"""

import json
import os
import re
import sys
for _s_ in (sys.stdout, sys.stderr):      # transcript
    try: _s_.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
import time

STATE_DIR = os.path.join(".claude", "_leangates")
STATE = "WALLCLOCK.json"

# WALL_CLOCKS.md
# WALL_CLOCKS.md
# WALL_CLOCKS.md
# PER FRAME
STEP_BUDGETS = [
    (r"job_fields_dump",                       0.33, "S3 probe, typical 13 s (8 samples)"),
    (r"job_mesh_burrito",                      0.50, "S4 reference mesh, measured ~20 s"),
    (r"job_features_burrito",                  2.13, "S5 piece, typical 85 s (11 samples)"),
    (r"job_s7_crop",                           0.38, "S7 crop, typical 15 s"),
    (r"job_s7_replace",                        1.60, "S7 cut+fuse, typical 64 s full fuse "
                                                     "(a gate refusal is 20 s, not a failure)"),
    (r"job_assemble",                          4.00, "pre-union then one fuse; fuse cost scales "
                                                     "with FACE COUNT, not card area"),
    (r"job_fuzzladder",                       10.00, "a fuzzy fuse; L17 says poll to ~9 min "
                                                     "before calling it stuck. A rung returning "
                                                     "NULL is FAST, not slow (L32)"),
    (r"job_repair",                            0.68, "face census, typical 27 s on 4530 faces"),
    (r"job_piece_audit|job_brepstat",          0.33, "a read-only brep stat, typical 13 s"),
    (r"job_sect_compare",                      0.58, "3-4 stations, typical 23 s. WRITES NO "
                                                     "STATUS FILE - wait on the PNG count"),
    (r"job_compare_pics",                      8.00, "DIVERGING, see the note above. Budget "
                                                     "~15 s PER FRAME and count PNGs"),
    (r"job_render_arc|job_beforeafter",        3.00, "a sharded orbit render"),
    (r"kit\.py\s+render\b.*--box",             1.25, "boxed / piece render, typical 50 s"),
    (r"kit\.py\s+render\b",                    2.10, "whole-body render, typical 83 s"),
    (r"kit\.py\s+review\b",                    2.25, "review step 1, the tess cache - the ONLY "
                                                     "kernel step of a review, typical 90 s"),
    (r"kit\.py\s+dossier\b",                   3.20, "dossier take, typical 127 s"),
    (r"kit\.py\s+measure\s+faces\b",           0.08, "faces --only, typical 3 s"),
    (r"kit\.py\s+measure\s+section\b",         0.25, "one station, typical 8-9 s"),
    (r"kit\.py\s+measure\b",                   1.00, "a kit measure"),
    (r"kit\.py\s+check\b",                    16.00, "kit check, whose own cap is 900 s (P43)"),
    (r"kit\.py\s+run\b",                       4.00, "a kit run"),
    (r"cad-reviewer",                          3.20, "a cad-reviewer worker, typical 105 s at 5 "
                                                     "frames / 125 s at 10"),
]
DEFAULT_STEP_MIN = 3.0
DEFAULT_WATCH_MIN = 5.0
QUIET_S = 600
LOUDER = 2.0



def find_root(start):
    r = start
    while r and not os.path.exists(os.path.join(r, ".claude")) and os.path.dirname(r) != r:
        r = os.path.dirname(r)
    return r


def _path(root):
    return os.path.join((os.environ.get("KIT_SCRATCH_ROOT") or "").strip() or root, STATE_DIR, STATE)


def load(root):
    try:
        with open(_path(root), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def save(root, d):
    """Best effort. A clock that raises is worse than a clock that misses a tick."""
    if not root or not os.path.isdir(root):
        return False
    try:
        os.makedirs(os.path.dirname(_path(root)), exist_ok=True)
        tmp = _path(root) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=1)
        os.replace(tmp, _path(root))
        return True
    except Exception:
        return False


def stamp_start(root, tool, what):
    """Called by guard.py on PreToolUse. The ONLY thing that makes the duration below honest.

    Without it the best available measurement is the gap between two tool calls, which contains
    the model's thinking and any wait for the client - so it reports a long lunch as a stuck step, and a
    warden that cries wolf is a warden that gets filtered (P17).
    """
    d = load(root)
    d["pre"] = {"t": time.time(), "tool": str(tool or ""), "what": str(what or "")[:160]}
    return save(root, d)



def watch_add(root, name, expect_min=None, what="", kind="background", owner="", pid=None):
    """Register launched work. `owner` is the session/agent that launched it (2026-09-24: the
    register used to be one list per project and every sub-agent was nagged about every other
    agent's tasks - the agent's handoff, 2.5); `pid` lets `kit stop <name>` kill the right tree."""
    d = load(root)
    w = d.setdefault("watch", {})
    if name in w:
        w[name]["t"] = time.time()
        if owner: w[name]["owner"] = owner
        if pid: w[name]["pid"] = int(pid)
    else:
        w[name] = {"t": time.time(), "expect": float(expect_min or DEFAULT_WATCH_MIN),
                   "what": str(what or "")[:200], "kind": kind, "owner": str(owner or ""),
                   "pid": int(pid) if pid else None}
    save(root, d)
    return w[name]


def watch_clear(root, name):
    d = load(root)
    gone = (d.get("watch") or {}).pop(name, None)
    if gone is not None:
        save(root, d)
    return gone


def watch_open(root, owner=None):
    """[(name, minutes, expect, over?, what)] for everything launched and not collected.

    With `owner` given, ONLY that owner's entries (and legacy entries with no owner recorded) - a
    reviewer sub-agent is not told to collect the orchestrator's driver, and the orchestrator is
    not told to collect a reviewer's probe. `watch_foreign(root, owner)` counts the rest."""
    now, out = time.time(), []
    for n, w in sorted((load(root).get("watch") or {}).items()):
        if owner is not None and (w.get("owner") or "") not in ("", str(owner)):
            continue
        try:
            mins = (now - float(w["t"])) / 60.0
        except (TypeError, ValueError, KeyError):
            continue
        exp = float(w.get("expect") or DEFAULT_WATCH_MIN)
        out.append((n, round(mins, 1), exp, mins > exp, w.get("what", "")))
    return out


def watch_foreign(root, owner):
    """How many open entries belong to OTHER owners (one line of context, never a finding)."""
    return sum(1 for w in (load(root).get("watch") or {}).values()
               if (w.get("owner") or "") not in ("", str(owner or "")))


def watch_pid(root, name):
    w = (load(root).get("watch") or {}).get(name) or {}
    return w.get("pid")



TABLE = os.path.join("claude_code", "WALL_CLOCKS.md")
TABLE_ROW = re.compile(r"^\|\s*`([^`]+\.py)`[^|]*\|\s*\*\*~?\s*(\d+(?:\.\d+)?)\s*s\*\*", re.M)


def table_budgets(root):
    r"""{script filename: typical seconds} read off the PROJECT'S OWN living table.

    the client, 2026-09-14: *"log for future agents in this session what typical wall clocks are per job.
    Update the average as you go and do not include jobs that have runaway issues."* And: *"any
    clock that runs 1.5x what a typical job runs is a red flag."* The project's
    `claude_code\WALL_CLOCKS.md` is where that averaging happens, and until 2026-09-17 this hook
    carried a hand-copied SNAPSHOT of it in `STEP_BUDGETS` - the table moved and the hook's numbers
    did not. The table is the owner (README rule 0); the snapshot is the fallback for scripts the
    table has never timed.

    ONLY THE TYPICAL TABLE IS READ. The file also holds a RUNAWAYS table (*"excluded from the
    averages, kept so the shape is recognisable"*), and a first draft of this parser took the
    largest figure it could find - 488 s for a step whose typical is 85 s - which is precisely the
    number the client said to exclude. So: a table is read only if its header row's second column is
    `typical`, and a row only if its typical cell is a plain `**N s**` (a `PER FRAME` or a dash
    falls through to the snapshot). Two rows for one script take the larger typical - a budget is
    a ceiling, and the S7 "refused at a gate" row is shorter than the full fuse.
    """
    out = {}
    if not root:
        return out
    p = os.path.join(root, TABLE)
    if not os.path.isfile(p):
        return out
    try:
        lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
    except OSError:
        return out
    in_typical = False
    for line in lines:
        t = line.strip()
        if not t.startswith("|"):
            in_typical = False
            continue
        cells = [c.strip() for c in t.strip("|").split("|")]
        if len(cells) >= 2 and cells[1].lower() == "typical" and cells[0].lower() in ("job", "step", "script"):
            in_typical = True
            continue
        if not in_typical or t.startswith("|---") or set(t) <= set("|-: "):
            continue
        # kit rebuild
        # kit rebuild  kit rebuild
        m = re.match(r"`([^`]+\.py)`", cells[0]) or re.match(r"`(kit\s+[^`]+)`\s*$", cells[0])
        if not m:
            continue
        v = re.match(r"^\*\*~?\s*(\d+(?:\.\d+)?)\s*s\*\*$", cells[1])
        if not v:
            continue
        name, secs = m.group(1).strip(), float(v.group(1))
        out[name] = max(out.get(name, 0.0), secs)
    return out


def budget_for(cmd, tool=None, root=None):
    c = str(cmd or "")
    table = table_budgets(root)
    # kit rebuild  kit rebuild
    _m = re.search(r"""kit(?:\.py)?["']?\s+([A-Za-z][\w-]*)\s+([A-Za-z][\w.:-]*)""", c)
    if _m:
        _cands = ["kit %s %s" % (_m.group(1), _m.group(2)), "kit %s" % _m.group(1)]     # kit rebuild
        _st = re.search(r"STEP=(\d+)", c)
        if _st:
            _cands.insert(0, _cands[0] + " STEP=" + _st.group(1))
        _md = re.search(r"\b(LOOK_MODE=\w+|LINES=[01])\b", c)      # kit rebuild  LOOK_MODE=full
        if _md and not _st: _cands.insert(0, _cands[0] + " " + (("LOOK_MODE=" + _md.group(1).split("=", 1)[1].lower()) if _md.group(1).startswith("LOOK_MODE") else _md.group(1)))
        for _n in _cands:
            # mode rows  kit rebuild  skin-build  kit rebuild  LOOK_MODE=full
            _fam = [table[x_] for x_ in table if x_ == _n or x_.startswith(_n + " ")]
            if _fam:
                _t = max(_fam)
                return max(_t * 1.5 / 60.0, 0.05), "typical %.0f s in claude_code\\WALL_CLOCKS.md (row %s%s), red flag at 1.5x" % (_t, _n, " and its mode rows" if len(_fam) > 1 else "")
    # kit rebuild
    # kit rebuild
    for name, secs in table.items():
        if name in c and re.search(re.escape(name) + r"(?![\w.-])", c):
            return max(secs * 1.5 / 60.0, 0.05), "typical %.0f s in claude_code\\WALL_CLOCKS.md, red flag at 1.5x" % secs
    # WALL_CLOCKS.md
    for pat, mins, what in STEP_BUDGETS:
        if re.search(pat, c, re.I):
            return mins, what
    if str(tool or "") in ("Task", "Agent"):      # transcript
        return 15.0, "a launched worker; measured median 152 s, p90 452 s (ORCHESTRATOR.md 4a)"
    return DEFAULT_STEP_MIN, "an unnamed step (L11: every step in this process is under 3 min)"


def _jobs_over(root):
    """leangate's own job clock, if leangate can be found. Optional by design: this warden must
    work in a project whose kit has moved, and it must never block on an import."""
    for cand in (os.path.join(root, "claude_code", "kit"),
                 os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kit"),
                 os.path.join(root, "kit")):
        if os.path.exists(os.path.join(cand, "leangate.py")):
            try:
                sys.path.insert(0, cand)
                import leangate
                return [r for r in leangate.wall_status(root) if r[3]]
            except Exception:
                return []
    return []


def findings(root, tool=None, cmd=None, dur_min=None, owner=None, subagent=False):
    """[(key, ratio, text)] - everything the agent should be told right now.

    `owner` scopes the watch list to this session/agent; `subagent=True` means the call came from a
    launched sub-agent (a reviewer, a worker): it hears about its OWN step's duration and nothing
    else - the job clocks, the state nudge and the orchestrator's launched tasks are the
    orchestrator's business (the agent's handoff 2.5: read-only reviewer sessions were stopped by a
    blocking "JOB M2A IS 19961 MIN PAST ITS BUDGET" about a job parked two weeks earlier)."""
    out = []

    if dur_min is not None and str(tool or "") in ("Bash", "Task", "Agent"):
        budget, what = budget_for(cmd, tool, root)
        if dur_min > budget:
            out.append((
                "step:%s" % re.sub(r"\W+", "_", str(cmd or "")[:60]),
                dur_min / budget,
                "THAT STEP TOOK %.1f MINUTES against a %.0f min budget (%s).\n"
                "      %s\n"
                "\n"
                "  BURRITO_LESSONS L11, the client 2026-09-13: \"Every step in this process took at most 3\n"
                "  minutes. All 3 agents are probably locked up currently. If they can't report back\n"
                "  with some form of progress then cancel and restructure your instructions.\"\n"
                "  A step past about 2x its expectation is STUCK, not working hard. The usual cause\n"
                "  is a wait on a file the job never writes - `job_fields_dump.py` writes no status\n"
                "  file at all, and a poll loop against a filename that is never created is\n"
                "  indistinguishable from slow work. That one cost 441 s per combo for ~40 s of work.\n"
                "\n"
                "  Do one of these before running it again, and say which:\n"
                "    - check the job's own log for what it actually produced, and wait on THAT file;\n"
                "    - cancel and restructure, per the client's instruction above;\n"
                "    - or say in one line why this step is legitimately long, and carry on."
                % (dur_min, budget, what, str(cmd or "")[:160])))

    if subagent:
        return out

    for name, mins, exp, over, what in watch_open(root, owner):
        if not over:
            continue
        out.append((
            "watch:%s" % name,
            mins / max(exp, 0.1),
            "A LAUNCHED TASK HAS BEEN OPEN %.0f MIN AND NOBODY HAS COLLECTED IT: %s\n"
            "      %s\n"
            "\n"
            "  BURRITO_LESSONS L14, the client 2026-09-13: \"you had a two hour task running. Clearly you\n"
            "  aren't monitoring correctly.\" A wrapper launched for one ~40 s probe was still alive\n"
            "  two hours later because the answer had arrived by another route and nobody killed it.\n"
            "  Nothing warned, because a silent wait looks exactly like a silent success.\n"
            "\n"
            "  Every launched task is killed or collected IN THE SAME EXCHANGE IT IS READ:\n"
            "      kit collected %s        once you have its answer or have killed it\n"
            "  If it is still genuinely working, say so and give it a longer expectation:\n"
            "      kit watch %s --expect <minutes>"
            % (mins, name, what or "(no description recorded)", name, name)))

    for n, mins, budget, _over in _jobs_over(root):
        out.append((
            "job:%s" % n,
            mins / max(budget, 0.1),
            "JOB %s IS %.0f MIN PAST ITS %d MIN BUDGET.\n"
            "  A lean job past its budget is not working hard, it is stuck, and the usual cause is\n"
            "  a card it cannot satisfy. Read its RESULT.md; if there is none, ask it for one\n"
            "  before killing it." % (n, mins - budget, budget)))

    try:
        n_new, folder, has_state = state_behind(root)
        if n_new >= STATE_EVERY:
            out.append((
                "state:%s" % os.path.basename(folder),
                n_new / float(STATE_EVERY),
                "%d NEW ARTEFACTS IN %s SINCE %s.\n"
                "  A session that is COMPACTED rather than closed leaves no handoff, and the thing\n"
                "  compaction destroys first is what the run tags mean. Write claude_code\\STATE_NOW.md\n"
                "  now, in this order: the tag key (every tag in the folder, one line each: current /\n"
                "  superseded / sweep / poisoned), the current build and its verdict, the live lead with\n"
                "  its numbers, what is settled, the next actions in order. Then carry on. `kit close`\n"
                "  at the end is still the handoff; this is what survives a compaction before it."
                % (n_new, os.path.basename(folder),
                   "claude_code\\STATE_NOW.md was written" if has_state else "the session opened (no STATE_NOW.md yet)")))
    except Exception:
        pass

    return out


STATE_FILE = os.path.join("claude_code", "STATE_NOW.md")
STATE_EVERY = 25


def state_behind(root):
    """(new artefacts, the job folder, whether a state file exists). Counts files in the NEWEST job
    folder written after STATE_NOW.md (or after the session opened when there is none). Job
    folders only - the tag key is theirs; registers and logs under claude_code\\ do not count."""
    sp = os.path.join(root, STATE_FILE)
    has_state = os.path.isfile(sp)
    ref = os.path.getmtime(sp) if has_state else None
    if ref is None:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kit"))
            import leangate as _G
            s = _G.session(root)
            ref = float((s or {}).get("started") or 0.0)
        except Exception:
            ref = 0.0
        if not ref:
            return 0, "", has_state
    jobs = os.path.join(root, "claude_code", "jobs")
    if not os.path.isdir(jobs):
        return 0, "", has_state
    # NEW ARTEFACTS
    folders = [os.path.join(jobs, d) for d in os.listdir(jobs) if os.path.isdir(os.path.join(jobs, d)) and not d.lower().endswith("_chnf") and not os.path.isfile(os.path.join(jobs, d, ".setup_side"))]
    if not folders:
        return 0, "", has_state
    folder = max(folders, key=os.path.getmtime)
    n = 0
    for f in os.listdir(folder):
        p = os.path.join(folder, f)
        if os.path.isfile(p) and not f.startswith("log_") and os.path.getmtime(p) > ref:
            n += 1
    return n, folder, has_state


def _due(root, keys_ratios):
    """Which findings may speak. Latched, so a standing condition is not a banner (P17)."""
    d, now, due = load(root), time.time(), []
    said = d.setdefault("said", {})
    for key, ratio in keys_ratios:
        prev = said.get(key) or {}
        try:
            age = now - float(prev.get("t", 0))
            before = float(prev.get("ratio", 0))
        except (TypeError, ValueError):
            age, before = 1e9, 0.0
        if age > QUIET_S or ratio >= before * LOUDER:
            said[key] = {"t": now, "ratio": ratio}
            due.append(key)
    if due:
        save(root, d)
    return set(due)


def report(root, tool=None, cmd=None, dur_min=None, latch=True, owner=None, subagent=False):
    """The text to show, or "". `latch=False` for `kit status`, which is a deliberate look."""
    fs = findings(root, tool, cmd, dur_min, owner=owner, subagent=subagent)
    if not fs:
        return ""
    if latch:
        ok = _due(root, [(k, r) for k, r, _ in fs])
        fs = [f for f in fs if f[0] in ok]
    if not fs:
        return ""
    text = "\n\n".join("[wallclock] " + t for _, _, t in fs)
    if owner is not None:
        n = watch_foreign(root, owner)
        if n:
            text += "\n[wallclock] (%d launched task(s) belong to other agents of this project and are not yours to collect)" % n
    return text



_BG_NAME = re.compile(r"[^A-Za-z0-9_.-]+")
_STOP_TOOLS = ("KillShell", "KillBash", "TaskStop", "StopTask", "KillTask")
_ID_IN_TEXT = re.compile(r"(?:(?:shell|task|agent|background)[ _]?(?:id|ID)|\bID)[\"':\s]+([A-Za-z0-9_.-]{3,40})")
_DONE_WORDS = re.compile(r"\b(completed|complete|finished|failed|killed|cancelled|canceled|exited|stopped|done)\b", re.I)


def _id_in_text(text):
    """The harness's task id out of the text it returns at launch ('Command running in background with ID: xxx')."""
    m = _ID_IN_TEXT.search(str(text or ""))
    return m.group(1) if m else ""


def _pid_alive(pid):
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return None
    try:
        if os.name == "nt":
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if not h:
                return False
            code = ctypes.c_ulong()
            ok = ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
            ctypes.windll.kernel32.CloseHandle(h)
            return bool(ok) and code.value == 259
        os.kill(pid, 0)
        return True
    except OSError:
        return False
    except Exception:
        return None


def auto_collect(root, transcript_path=None):
    """Collect finished watches without a hand (2026-09-25, lessons K6 / W2 / #7: `kit close` refused until 35 stale
    watches - some 202 min old, all long finished - were collected by hand, and every launch needed `kit watch`).
    Two signals, both the harness's own: a watch whose recorded PID has exited (the kit's `--bg` launches), and a watch
    whose harness id appears in the transcript's tail beside a completion word (the task notification the harness
    writes when a background command ends). Returns the names collected."""
    d = load(root)
    w = d.get("watch") or {}
    if not w:
        return []
    tail = ""
    if transcript_path and os.path.isfile(str(transcript_path)):
        try:
            with open(transcript_path, "rb") as fh:
                fh.seek(0, 2); n = fh.tell(); fh.seek(max(0, n - 200000))
                tail = fh.read().decode("utf-8", "replace")
        except OSError:
            tail = ""
    gone = []
    for name, ent in list(w.items()):
        pid = ent.get("pid")
        if pid and _pid_alive(pid) is False:
            gone.append((name, "pid %s has exited" % pid)); continue
        sid = name[3:] if name.startswith("bg-") else ""
        if sid and len(sid) >= 3 and tail and not sid.isdigit():
            for line in tail.splitlines():
                if sid in line and _DONE_WORDS.search(line) and ("notification" in line.lower() or "background" in line.lower()
                                                                  or "task" in line.lower() or "shell" in line.lower()):
                    gone.append((name, "the harness reported it %s" % _DONE_WORDS.search(line).group(1).lower())); break
    for name, why in gone:
        w.pop(name, None)
    if gone:
        d["watch"] = w
        d.setdefault("collected_auto", []).append({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "items": gone})
        d["collected_auto"] = d["collected_auto"][-20:]
        save(root, d)
    return gone


def caller(data):
    """(owner, is_subagent) off the hook payload. The owner is the session id, extended by the
    agent id when the harness gives one, so an orchestrator and its sub-agents keep separate clocks.
    UNVERIFIED field names (the harness's, not the kit's): `session_id`, `agent_id`, `agent_type`,
    `parent_session_id`, `subagent`. Every read is defensive; a miss means one shared clock, which is
    what there was before."""
    sid = str(data.get("session_id") or "")
    aid = str(data.get("agent_id") or data.get("agent_type") or data.get("subagent_id") or "")
    sub = bool(aid or data.get("parent_session_id") or data.get("subagent") or data.get("is_subagent"))
    owner = (sid + ("/" + aid if aid else "")) or ""
    return owner, sub


def _auto_register(root, tool, inp, resp, owner=""):
    """Register work that outlives the tool call, WITHOUT the agent having to remember.

    L14 is a rule about a thing agents forget, so a rule that depends on remembering is the one
    shape of fix that cannot work. UNVERIFIED against a real harness payload - see the module
    docstring. Every read is defensive; a miss costs a missing finding and nothing else.
    """
    try:
        # foreground
        bg = bool(inp.get("run_in_background") or inp.get("background"))
        if tool in ("Bash", "Task", "Agent") and bg:
            sid = ""
            pid = None
            if isinstance(resp, dict):
                sid = str(resp.get("shellId") or resp.get("shell_id") or resp.get("taskId")
                          or resp.get("task_id") or resp.get("agentId") or resp.get("id") or "")
                pid = resp.get("pid") or resp.get("processId")
                if not sid:
                    # none of the
                    sid = _id_in_text(" ".join(str(v) for v in resp.values() if isinstance(v, (str, int))))
            elif isinstance(resp, str):
                sid = _id_in_text(resp)
            if sid:      # 31br D12 (b)
                name = "bg-" + _BG_NAME.sub("-", sid)[:24]
                watch_add(root, name, DEFAULT_WATCH_MIN,
                          str(inp.get("command") or inp.get("description") or "")[:200], "background",
                          owner=owner, pid=pid)
        elif tool in _STOP_TOOLS:
            sid = str(inp.get("shell_id") or inp.get("shellId") or inp.get("task_id") or inp.get("taskId") or "")
            watch_clear(root, "bg-" + _BG_NAME.sub("-", sid)[:24])
    except Exception:
        pass


def main():
    if str(os.environ.get("LEANKIT_WALLCLOCK", "")).lower() in ("off", "0", "no"):
        return 0
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0                      # unreadable
    tool = data.get("tool_name", "")
    inp = data.get("tool_input", {}) or {}
    resp = data.get("tool_response", {})
    root = find_root(data.get("cwd") or os.getcwd())
    if not root:
        return 0

    cmd = inp.get("command") or inp.get("description") or ""
    owner, subagent = caller(data)
    _auto_register(root, tool, inp, resp, owner=owner)
    try:
        auto_collect(root, data.get("transcript_path"))
    except Exception:
        pass

    d = load(root)
    pre = d.get("pre") or {}
    dur = None
    try:
        if pre.get("tool") == tool:
            dur = (time.time() - float(pre["t"])) / 60.0
    except (TypeError, ValueError, KeyError):
        dur = None
    d["pre"] = {}
    save(root, d)

    text = report(root, tool, cmd, dur, owner=owner or None, subagent=subagent)
    if text:
        sys.stderr.write(text + "\n")
        return 2
    return 0


def cli(argv):
    """`kit watch` / `kit collected` / `kit status` reach the register through these."""
    root = find_root(os.getcwd())
    if not argv:
        print(report(root, latch=False) or "[wallclock] nothing open and nothing overdue.")
        return 0
    if argv[0] == "--report":
        print(report(root, latch=False) or "[wallclock] nothing open and nothing overdue.")
        return 0
    if argv[0] == "--watch" and len(argv) > 1:
        exp = float(argv[argv.index("--expect") + 1]) if "--expect" in argv else DEFAULT_WATCH_MIN
        what = argv[argv.index("--what") + 1] if "--what" in argv else ""
        pid = argv[argv.index("--pid") + 1] if "--pid" in argv else None
        owner = ""
        try:
            with open(os.path.join(root, ".claude", ".conversation"), encoding="utf-8") as fh:
                owner = fh.read().strip()
        except Exception:
            owner = ""
        watch_add(root, argv[1], exp, what, owner=owner, pid=pid)
        print("[wallclock] watching %s, expected under %.0f min%s." % (argv[1], exp, (", pid %s" % pid) if pid else ""))
        return 0
    if argv[0] == "--collected" and len(argv) > 1:
        if watch_clear(root, argv[1]):
            print("[wallclock] %s collected." % argv[1])
        else:
            print("[wallclock] %s was not being watched." % argv[1])
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    # sys.exit(0)
    _root = find_root(os.getcwd())
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import liveness as _L
    except Exception:
        _L = None
    if _L is None:
        try:
            sys.exit(cli(sys.argv[1:]) if len(sys.argv) > 1 else main())
        except Exception:
            sys.exit(0)
    elif len(sys.argv) > 1:
        sys.exit(_L.guarded(_root, "wallclock", cli, sys.argv[1:]))
    else:
        sys.exit(_L.guarded(_root, "wallclock", main))

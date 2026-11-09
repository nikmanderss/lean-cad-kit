#!/usr/bin/env python3
"""selftest_wallclock.py - every case is a failure already on this project's record.

    python selftest_wallclock.py

Runs in a temporary folder. No FreeCAD, no project, no network. It covers everything in
`wallclock.py` EXCEPT the one thing only a live session can answer - whether a PostToolUse hook's
`exit 2` stderr reaches the agent on this Claude Code build. That is Test 1 in the kit's development record and
it is flagged to the client rather than assumed.

The kit's rule for a selftest : *"32 cases. Run it after changing
a gate; every case is a failure already on this project's record."* These nine are R19's.
"""

import os
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wallclock as W

FAILED = []


def check(name, got, want):
    ok = (got == want)
    print("  %-4s %s" % ("ok" if ok else "FAIL", name))
    if not ok:
        print("        got  %r" % (got,))
        print("        want %r" % (want,))
        FAILED.append(name)


def fresh():
    root = tempfile.mkdtemp(prefix="wallclock_test_")
    os.makedirs(os.path.join(root, ".claude", "_leangates"), exist_ok=True)
    return root


def fired(text, needle):
    return bool(text) and needle.lower() in text.lower()


def run():
    print("selftest_wallclock")

    # job_fields_dump.py
    root = fresh()
    t = W.report(root, "Bash", "python job_fields_dump.py --tag B21", 441 / 60.0)
    check("441 s S3 step fires", fired(t, "THAT STEP TOOK"), True)
    check("...and names L11", fired(t, "L11"), True)
    check("...without any JOBS.json", os.path.exists(os.path.join(root, "JOBS.json")), False)

    root = fresh()
    check("15 s S3 step is silent",
          W.report(root, "Bash", "python job_fields_dump.py --tag B21", 15 / 60.0), "")
    check("40 s S3 step fires - 3x its 13 s typical",
          fired(W.report(fresh(), "Bash", "python job_fields_dump.py --tag B21", 40 / 60.0),
                "THAT STEP TOOK"), True)

    root = fresh()
    check("kit check at 12 min is silent",
          W.report(root, "Bash", 'python kit.py check result.brep --as-orchestrator', 12.0), "")
    check("kit check at 20 min fires",
          fired(W.report(fresh(), "Bash",
                         'python kit.py check result.brep --as-orchestrator', 20.0),
                "THAT STEP TOOK"), True)

    root = fresh()
    W.watch_add(root, "bg-br18dsrmp", 5.0, "until [ -f fields.npz ]; do sleep 5; done")
    d = W.load(root)
    d["watch"]["bg-br18dsrmp"]["t"] = time.time() - 120 * 60
    W.save(root, d)
    t = W.report(root)
    check("2 h background wrapper fires", fired(t, "NOBODY HAS COLLECTED IT"), True)
    check("...and names L14", fired(t, "L14"), True)
    check("collected clears it", bool(W.watch_clear(root, "bg-br18dsrmp")), True)
    check("...and it then stays quiet", W.report(root, latch=False), "")

    root = fresh()
    a = W.report(root, "Bash", "python job_s7_replace.py", 10.0)
    b = W.report(root, "Bash", "python job_s7_replace.py", 10.0)
    check("a finding speaks once", (bool(a), b), (True, ""))

    c = W.report(root, "Bash", "python job_s7_replace.py", 25.0)
    check("...and again when the overrun doubles", bool(c), True)

    root = fresh()
    W.stamp_start(root, "Bash", "python job_fields_dump.py")
    pre = W.load(root).get("pre") or {}
    check("guard stamps the start", pre.get("tool"), "Bash")
    check("...and the stamp carries what ran", "job_fields_dump.py" in pre.get("what", ""), True)

    root = fresh()
    check("an unnamed 9 min step fires",
          fired(W.report(root, "Bash", "python some_new_driver.py", 9.0), "THAT STEP TOOK"), True)
    check("an unnamed 4 min step fires - L11's rule is 3 min",
          fired(W.report(fresh(), "Bash", "python some_new_driver.py", 4.0), "THAT STEP TOOK"), True)
    check("an unnamed 2 min step is silent",
          W.report(fresh(), "Bash", "python some_new_driver.py", 2.0), "")

    check("a 9 min worker is silent", W.report(fresh(), "Task", "fill the vane card", 9.0), "")
    check("a 40 min worker fires",
          fired(W.report(fresh(), "Task", "fill the vane card", 40.0), "THAT STEP TOOK"), True)
    # WALL_CLOCKS.md
    check("a 2 min cad-reviewer is silent",
          W.report(fresh(), "Task", "cad-reviewer: 5 frames of the vane", 2.0), "")
    check("an 8 min cad-reviewer fires, though a generic worker would not",
          fired(W.report(fresh(), "Task", "cad-reviewer: 5 frames of the vane", 8.0),
                "THAT STEP TOOK"), True)
    check("...and a generic worker at the same 8 min is still silent",
          W.report(fresh(), "Task", "fill the vane card", 8.0), "")
    root = fresh()
    W._auto_register(root, "Task", {"subagent_type": "cad-worker-haiku"}, {})
    check("a finished Task is not put on the watch register", W.watch_open(root), [])

    print("\n[scope] launched tasks belong to the agent that launched them")
    root = fresh()
    W._auto_register(root, "Bash", {"command": "orchestrator driver", "run_in_background": True},
                     {"shellId": "orch1", "pid": 4242}, owner="S/orch")
    W._auto_register(root, "Bash", {"command": "reviewer probe", "run_in_background": True},
                     {"shellId": "rev1"}, owner="S/rev")
    check("two owners, two entries", sorted(n for n, *_ in W.watch_open(root)), ["bg-orch1", "bg-rev1"])
    check("the orchestrator sees only its own", [n for n, *_ in W.watch_open(root, "S/orch")], ["bg-orch1"])
    check("the reviewer sees only its own", [n for n, *_ in W.watch_open(root, "S/rev")], ["bg-rev1"])
    check("the pid is recorded for --kill", W.watch_pid(root, "bg-orch1"), 4242)
    check("a foreign count is one line of context", W.watch_foreign(root, "S/orch"), 1)
    W.watch_add(root, "legacy", 5.0, "an entry written before owners existed")
    check("a legacy entry with no owner is everyone's", "legacy" in [n for n, *_ in W.watch_open(root, "S/rev")], True)
    W._auto_register(root, "TaskStop", {"task_id": "orch1"}, {})
    check("TaskStop clears the entry", "bg-orch1" in [n for n, *_ in W.watch_open(root)], False)
    W.watch_add(root, "bg-late", 0.01, "x", owner="S/orch"); time.sleep(1.0)
    check("a sub-agent is not told to collect another agent's overdue task",
          fired(W.report(root, "Bash", "x", None, owner="S/rev", subagent=True), "NOBODY HAS COLLECTED"), False)
    check("...while the owner is", fired(W.report(root, "Bash", "x", None, owner="S/orch"), "NOBODY HAS COLLECTED"), True)
    check("the payload's session and agent ids make the owner",
          W.caller({"session_id": "S", "agent_id": "a7"}), ("S/a7", True))
    check("...and a plain session is the orchestrator", W.caller({"session_id": "S"}), ("S", False))

    # kit close
    print("\n[collect] the harness id out of the launch text; auto-collect on the pid or the completion notice")
    root = fresh()
    W._auto_register(root, "Bash", {"command": "long probe", "run_in_background": True},
                     {"stdout": "Command running in background with ID: b4fipbr92", "stderr": ""}, owner="S")
    check("a background Bash is registered under the harness id in its response text",
          [n for n, *_ in W.watch_open(root)], ["bg-b4fipbr92"])
    W._auto_register(root, "Bash", {"command": "second", "run_in_background": True},
                     "Command running in background with ID: boex5nqui", owner="S")
    check("...from a plain-string response too", "bg-boex5nqui" in [n for n, *_ in W.watch_open(root)], True)
    tp = os.path.join(root, "transcript.jsonl")
    with open(tp, "w", encoding="utf-8") as fh:
        fh.write('{"type":"user","message":{"content":"<task-notification><task-id>b4fipbr92</task-id><status>completed</status></task-notification>"}}\n')
    gone = W.auto_collect(root, tp)
    check("the harness's completion notice in the transcript collects that watch", [g[0] for g in gone], ["bg-b4fipbr92"])
    check("...and the other stays open", [n for n, *_ in W.watch_open(root)], ["bg-boex5nqui"])
    W.watch_add(root, "bg-deadpid", 5.0, "a kit --bg launch", owner="S", pid=2147483000)
    gone = W.auto_collect(root, None)
    check("a watch whose pid has exited collects itself", [g[0] for g in gone], ["bg-deadpid"])
    check("...the live one stays", [n for n, *_ in W.watch_open(root)], ["bg-boex5nqui"])

    # none of the
    root = fresh()
    with open(W._path(root), "w", encoding="utf-8") as fh:
        fh.write("{ not json at all")
    check("corrupt state reads as empty", W.load(root), {})
    _cwd = os.getcwd(); _scratch = tempfile.mkdtemp(prefix="wallclock_cwd_"); os.chdir(_scratch)
    try:
        W.report(root, "Bash", "x", 99.0)
        W.watch_add(root, "n", 1.0, "x")
        W.report("", "Bash", "x", 99.0)
        W.save("/does/not/exist/anywhere", {"x": 1})
        raised = False
    except Exception as exc:
        raised = repr(exc)
    finally:
        os.chdir(_cwd)
    check("...and nothing raises on it", raised, False)
    check("...and an empty root writes NOTHING into the current folder",
          os.path.exists(os.path.join(_scratch, ".claude")), False)
    shutil.rmtree(_scratch, ignore_errors=True)

    # WALL_CLOCKS.md
    print("\n[table] the living WALL_CLOCKS.md is read - typical table only, runaways excluded")
    troot = fresh()
    os.makedirs(os.path.join(troot, "claude_code"), exist_ok=True)
    with open(os.path.join(troot, "claude_code", "WALL_CLOCKS.md"), "w", encoding="utf-8") as fh:
        fh.write("# TYPICAL WALL CLOCKS\n\n## The table\n\n"
                 "| job | typical | samples (s) | red flag at 1.5x | notes |\n|---|---|---|---|---|\n"
                 "| `job_alpha.py` (S3) | **20 s** | 19, 20, 21 | **30 s** | tight |\n"
                 "| `job_beta.py` full | **60 s** | 60 | **90 s** | |\n"
                 "| `job_beta.py` refused at a gate | **12 s** | 12 | **18 s** | shorter |\n"
                 "| `job_pics.py` | **~15 s PER FRAME** | 79, 450 | - | useless |\n\n"
                 "## RUNAWAYS - excluded from the averages\n\n"
                 "| job | ran | typical | why |\n|---|---|---|---|\n"
                 "| `job_alpha.py` POLE=2 | **488 s** | 20 s | 24x for nothing |\n")
    tb = W.table_budgets(troot)
    check("a typical row is read", tb.get("job_alpha.py"), 20.0)
    check("two rows for one script take the LARGER typical", tb.get("job_beta.py"), 60.0)
    check("a PER FRAME typical is skipped", "job_pics.py" in tb, False)
    check("the RUNAWAYS table is NOT read - 488 s stays out", tb.get("job_alpha.py") < 100, True)
    b, why = W.budget_for("python job_alpha.py", "Bash", troot)
    check("the budget is 1.5x the table's typical, in minutes", round(b, 3), 0.5)
    check("...and says where it came from", "WALL_CLOCKS.md" in why, True)
    b2, why2 = W.budget_for("python job_pics.py", "Bash", troot)
    check("a script the table cannot budget falls through to the snapshot", "PER FRAME" in why2 or b2 > 0, True)
    check("no project root -> the snapshot as before", W.budget_for("python job_fields_dump.py", "Bash")[0], 0.33)
    shutil.rmtree(troot, ignore_errors=True)

    print("\n[state] STATE_NOW.md behind the job folder - a nudge, latched, silent once it is written")
    sroot = fresh()
    jf = os.path.join(sroot, "claude_code", "jobs", "BUR")
    os.makedirs(jf, exist_ok=True)
    os.makedirs(os.path.join(sroot, ".claude"), exist_ok=True)
    st = os.path.join(sroot, "claude_code", "STATE_NOW.md")
    with open(st, "w", encoding="utf-8") as fh:
        fh.write("# state\n")
    os.utime(st, (1000, 1000))
    for i in range(W.STATE_EVERY - 1):
        with open(os.path.join(jf, "piece_features_T%d.brep" % i), "w") as fh:
            fh.write("x")
    n, folder, has = W.state_behind(sroot)
    check("%d artefacts after the state file are counted, log_ files are not" % (W.STATE_EVERY - 1), (n, has), (W.STATE_EVERY - 1, True))
    with open(os.path.join(jf, "log_job_x_T1.txt"), "w") as fh:
        fh.write("log")
    check("...a log file does not count", W.state_behind(sroot)[0], W.STATE_EVERY - 1)
    check("one under the threshold is silent", "NEW ARTEFACTS" in (W.report(sroot, latch=False) or ""), False)
    with open(os.path.join(jf, "status_features_T99.json"), "w") as fh:
        fh.write("{}")
    t = W.report(sroot, latch=False) or ""
    check("at the threshold the nudge speaks, naming STATE_NOW.md and the tag key", fired(t, "NEW ARTEFACTS") and fired(t, "tag key"), True)
    with open(st, "w", encoding="utf-8") as fh:
        fh.write("# state, rewritten now\n")
    check("writing STATE_NOW.md resets the count to 0", W.state_behind(sroot)[0], 0)
    check("...and the nudge is silent again", "NEW ARTEFACTS" in (W.report(sroot, latch=False) or ""), False)
    os.remove(st)
    check("no state file and no session -> nothing to count against, silent", W.state_behind(sroot)[0], 0)
    shutil.rmtree(sroot, ignore_errors=True)

    # transcript
    check("31bs K7: a 40 min Agent step speaks (the launched-worker budget)", fired(W.report(fresh(), "Agent", "fill the vane card", 40.0), "THAT STEP TOOK"), True)
    check("31bs K7: a 9 min Agent step is silent", W.report(fresh(), "Agent", "fill the vane card", 9.0), "")
    _r7 = fresh(); W._auto_register(_r7, "Agent", {"run_in_background": True, "description": "a reviewer shard"}, {"agentId": "a7a73eac4292"})
    check("31bs K7: a BACKGROUND Agent launch registers its watch under the harness id", [n for n, *_ in W.watch_open(_r7)], ["bg-a7a73eac4292"])
    _r7b = fresh(); W._auto_register(_r7b, "Agent", {"description": "a worker"}, {"agentId": "zzz"})
    check("31bs K7: a FOREGROUND Agent (finished when PostToolUse fires) registers nothing", W.watch_open(_r7b), [])
    shutil.rmtree(root, ignore_errors=True)
    print("")
    if FAILED:
        print("%d FAILED: %s" % (len(FAILED), ", ".join(FAILED)))
        return 1
    print("all cases pass.")
    print("NOT COVERED HERE, and it needs a live session: that a PostToolUse hook's exit-2 stderr")
    print("reaches the agent. See the kit's development record, 2026-09-14, Test 1.")
    return 0


if __name__ == "__main__":
    sys.exit(run())

#!/usr/bin/env python3
r"""selftest_liveness.py — every case is a silent death this project has actually had.

    & "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" "C:\CAD\LEAN_KIT\hooks\selftest_liveness.py"

No FreeCAD, no project, no network. Runs in a temp folder.

**The case that carries the design is #1: a watcher that never launched.** Every other case here
could be caught by reading a beat file. That one cannot — there is no file to read — and it is the
exact shape of 2026-09-09, when both hooks were wired to a `python3` that does not exist on Windows
and neither had ever run while settings.json looked perfectly installed. It is caught only because
`WATCHERS` declares what should have been there.
"""

import json
import os
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import liveness as L

FAILED = []
ONE = {"w": {"every": "every call", "stale_min": 30, "why": "..."}}
OPT = {"w": {"every": "every call", "stale_min": 30, "why": "...", "optional": True}}


def check(name, got, want):
    ok = (got == want)
    print("  %-4s %s" % ("ok" if ok else "FAIL", name))
    if not ok:
        print("        got  %r" % (got,))
        print("        want %r" % (want,))
        FAILED.append(name)


def fresh():
    r = tempfile.mkdtemp(prefix="liveness_test_")
    os.makedirs(os.path.join(r, ".claude"), exist_ok=True)
    return r


def sev(root, name, expect=None):
    return [s for s, n, _ in L.check(root, expect) if n == name]


def age(root, name, minutes):
    """Backdate a beat. Editing the file is the point: `beat()` always stamps now."""
    d = L._read(root, name)
    d["t"] = time.time() - minutes * 60
    with open(L._path(root, name), "w", encoding="utf-8") as fh:
        json.dump(d, fh)


def boom():
    raise ValueError("the thing that actually went wrong")


def run():
    print("selftest_liveness")

    root = fresh()
    check("a watcher that never ran is DEAD", sev(root, "w", ONE), ["DEAD"])
    check("...an optional one is not", sev(root, "w", OPT), [])
    check("...and the report says so", "HAS NEVER RUN" in "\n".join(L.report(root, ONE)), True)

    # sys.exit(0)
    root = fresh()
    check("a crashing watcher does NOT raise", L.guarded(root, "w", boom), 0)
    check("...it is recorded as CRASHED", sev(root, "w", ONE), ["CRASHED"])
    check("...and the exception is kept",
          "the thing that actually went wrong" in L._read(root, "w").get("last_error", ""), True)

    root = fresh()
    check("a refusal returns its code", L.guarded(root, "w", lambda: sys.exit(2)), 2)
    check("...and is NOT a crash", sev(root, "w", ONE), [])

    root = fresh()
    L.beat(root, "w", "start")
    check("a start just now is not yet a crash", sev(root, "w", ONE), [])
    age(root, "w", 20)
    check("a start 20 min old IS a crash", sev(root, "w", ONE), ["CRASHED"])

    root = fresh()
    L.guarded(root, "w", lambda: 0)
    check("a fresh clean run is silent", sev(root, "w", ONE), [])
    age(root, "w", 120)
    check("...two hours later, with NO other watcher having run since, it is NOT stale (nobody worked)", sev(root, "w", ONE), [])
    TWO = dict(ONE, v={"every": "every call", "stale_min": 30, "why": "..."})
    L.guarded(root, "v", lambda: 0)
    check("...but once another watcher has beaten since, it IS STALE", sev(root, "w", TWO), ["STALE"])
    root = fresh()
    PC = {"guard": {"every": "every Bash tool call", "stale_min": 30, "why": "..."}, "session_start": {"every": "session open", "stale_min": 1440, "why": "..."}}
    L.guarded(root, "guard", lambda: 0); age(root, "guard", 36)
    L.guarded(root, "session_start", lambda: 0)
    check("31bc: a session-open beat 36 min after the guard's last call does NOT make the guard STALE", sev(root, "guard", PC), [])
    PC2 = dict(PC, wallclock={"every": "every Bash and Task tool call", "stale_min": 60, "why": "..."})
    L.guarded(root, "wallclock", lambda: 0)
    check("31bc: ...but a per-call watcher beating 36 min after the guard does", sev(root, "guard", PC2), ["STALE"])
    check("31be: at session open (at_start) a per-call watcher is never STALE - nothing has called it yet", [s for s, _n, _l in L.check(root, PC2, at_start=True) if _n == "guard"], [])

    # FLAPPING
    root = fresh()
    for _ in range(10):
        L.guarded(root, "w", lambda: 0)
    for _ in range(4):
        L.guarded(root, "w", boom)
    check("failing 4 of 14 runs is FLAPPING", "FLAPPING" in sev(root, "w", ONE), True)

    # sys.exit(0)
    root = fresh()
    blocker = os.path.join(root, "not-a-directory")
    with open(blocker, "w", encoding="utf-8") as fh:
        fh.write("x")
    bad_root = os.path.join(blocker, "under-a-file")
    try:
        wrote = L.beat(bad_root, "w")
        L.check(bad_root, ONE)
        L.report("", ONE)
        raised = False
    except Exception as exc:
        wrote, raised = None, repr(exc)
    check("nothing raises on an unwritable root", raised, False)
    check("a failed beat reports False, it does not throw", wrote, False)

    PCZ = {"guard": {"every": "every Bash tool call", "stale_min": 30, "why": "..."}, "wallclock": {"every": "every Bash and Task tool call", "stale_min": 60, "why": "..."}}
    root = fresh(); L.guarded(root, "guard", lambda: 0)
    check("31bz: a per-call watcher never run (not at start) is NOT YET", sev(root, "wallclock", PCZ), ["NOT YET"])
    rz = L.report(root, PCZ)
    check("31bz: ...the report is one line - no banner, no 'stop'", (len(rz) == 1 and "have not run yet" in rz[0] and "If the GUARD is the dead one, stop" not in rz[0] and "A WATCHER IS NOT REPORTING" not in rz[0]), True)
    L.guarded(root, "wallclock", lambda: 0); age(root, "guard", 45)
    rz = "\n".join(L.report(root, PCZ))
    check("31bz: a STALE guard -> the banner AND its 'stop' line", ("A WATCHER IS NOT REPORTING" in rz and "If the GUARD is the dead one, stop" in rz), True)
    root2 = fresh(); L.guarded(root2, "guard", lambda: 0); L.guarded(root2, "wallclock", lambda: 0); age(root2, "wallclock", 90)
    rz = "\n".join(L.report(root2, PCZ))
    check("31bz: a STALE wallclock with a live guard -> the banner, no 'stop'", ("A WATCHER IS NOT REPORTING" in rz and "If the GUARD is the dead one, stop" not in rz), True)
    shutil.rmtree(root, ignore_errors=True); shutil.rmtree(root2, ignore_errors=True)

    root = fresh()
    check("report() returns lines, never a refusal", isinstance(L.report(root), list), True)

    shutil.rmtree(root, ignore_errors=True)
    print("")
    if FAILED:
        print("%d FAILED: %s" % (len(FAILED), ", ".join(FAILED)))
        return 1
    print("all cases pass.")
    print("NOT COVERED, and it cannot be: if the interpreter cannot launch at all, no code here")
    print("runs. That case is caught by the DECLARED list in WATCHERS and by nothing else.")
    return 0


if __name__ == "__main__":
    sys.exit(run())

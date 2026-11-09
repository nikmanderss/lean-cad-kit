#!/usr/bin/env python3
r"""liveness.py — a watcher that dies must not look like a watcher with nothing to say.

the client, 2026-09-14: *"polling/watching/clocks all need to have a liveness check to make sure crashes
aren't gone without reporting."* And, on the one decision this left open: **"Dead guards report."**
So nothing here refuses anything, ever. It reports.

THE DEFECT. Every warden in this folder ends the same way:

    except Exception:
        sys.exit(0)

That is deliberate and the reasoning is right — *the warden must never be the reason work stops*.
But it buys that with silence: **a wallclock that crashes on its first call and a wallclock with
nothing to report produce the identical observable — nothing.** The one thing that would tell you is
the thing it swallows.

Four instances on this project's record, all the same shape:

| when | what died quietly | how it was found |
|---|---|---|
| 2026-09-09 | both hooks, wired to a `python3` that python.org does not install on Windows | by reading settings.json, days later |
| 2026-09-10 | `kit check`, killed by its own 170 s cap every time (P43) | the round wrote it up as a fact of life and re-ran it unchanged |
| 2026-09-10 | the proof-of-opening gate — no Pillow, so nothing was stamped and the gate passed on nothing for an hour (P37) | the client noticed the frames had no codes |
| 2026-09-13 | a sweep driver waiting on a file no job writes: 441 s per combo (L11) | the client asked why three agents were quiet |

`guard.py` is the only one with an answer, and only because it was paid for once: it writes
`.claude\.guard_alive` on every invocation *before any decision*, and `kit.py` refuses FreeCAD unless
that stamp is fresh. Its own comment is the principle this generalises: **"Nothing inside a hook can
report that the hook never ran. But the thing that DOES run can check."**

TWO PARTS, AND THE SECOND IS THE ONE THAT IS EASY TO LEAVE OUT.

  * **A beat per watcher** — `start`, then `ok`, or `error` with the exception. A `start` with no
    `ok` is a crash mid-run, which no exception handler can report because the process is gone.
  * **A DECLARED list of what must beat.** A watcher that never launched writes nothing at all, so
    its absence is invisible *unless something says it should have been there*. `WATCHERS` is that
    something. Same lesson as P08 (a detector whose search domain is wrong measures its domain) and
    as the duplicate-detector whose stale search path reported "no duplicates" exactly as loudly as
    a correct one.

WHERE IT IS READ: `session_start.py`, once per session, and `kit status` on demand. **Deliberately
not a new hook** — a new hook is one more thing that can die silently, and answering "who watches the
watcher" with "another watcher" is how this class of defect breeds.

WHAT IT CANNOT DO: if the interpreter cannot launch at all — the 2026-09-09 case — no code here
runs and nothing is recorded. **That case is caught by the DECLARED list and by nothing else**, which
is why the list is not decoration.
"""

import json
import os
import time

DIR = os.path.join(".claude", "_leangates", "_alive")

WATCHERS = {
    "guard": {
        "every": "every Bash / Write / Edit / Read tool call",
        "stale_min": 30,
        "why": "nothing is enforcing METHOD.md 5 — FreeCAD can run outside `kit run`, orchestrator "
               "commands are ungated, and the model bank is writable",
    },
    "wallclock": {
        "every": "every Bash and Task tool call",
        "stale_min": 60,
        "why": "no step is timed and no launched task is collected; a stuck step and a working one "
               "look identical again (L11, L14)",
    },
    "session_start": {
        "every": "session open",
        "stale_min": 1440,
        "why": "the contract, the CAD thinking and the manufacturing rules never arrived — the "
               "session is running on whatever it remembers",
    },
    "integrity": {
        "every": "session open",
        "stale_min": 1440,
        "why": "nothing is checking whether the controls themselves changed",
    },
    "handback": {
        "every": "each worker hand-back",
        "stale_min": None,
        "optional": True,
        "why": "a worker can finish with no RESULT.md at all",
    },
    "inbox_watch": {
        "every": "5-10 min, from a scheduled task",
        "stale_min": 30,
        "optional": True,
        "external": True,
        "why": "the orchestrator's questions are reaching nobody; the client found this by typing into its "
               "window (2026-09-10, five stalls)",
    },
}

MID_RUN_MIN = 5.0


def _path(root, name):
    return os.path.join((os.environ.get("KIT_SCRATCH_ROOT") or "").strip() or root, DIR, "%s.json" % name)


def _read(root, name):
    try:
        with open(_path(root, name), encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def beat(root, name, phase="ok", note=""):
    """Record that `name` reached this point. `phase`: "start" | "ok" | "error".

    COUNTERS, NOT JUST A TIMESTAMP. A warden that fails one call in five is the hardest kind to
    catch — it works when you test it. `runs` and `errors` accumulate so that is visible as a ratio
    rather than as a coincidence.
    """
    try:
        d = _read(root, name)
        d["name"] = name
        d["t"] = time.time()
        d["phase"] = phase
        d["pid"] = os.getpid()
        if note:
            d["note"] = str(note)[:400]
        if phase == "start":
            d["runs"] = int(d.get("runs", 0)) + 1
        elif phase == "error":
            d["errors"] = int(d.get("errors", 0)) + 1
            d["last_error"] = str(note)[:400]
            d["last_error_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        os.makedirs(os.path.dirname(_path(root, name)), exist_ok=True)
        tmp = _path(root, name) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=1)
        os.replace(tmp, _path(root, name))
        return True
    except Exception:
        return False


def guarded(root, name, fn, *a, **kw):
    """Run `fn` as watcher `name`, recording start, finish and any crash. Returns fn's exit code.

    This replaces each watcher's bare `try / except Exception: sys.exit(0)`. **It keeps the
    guarantee that made that line right — no exception ever escapes, so the warden still cannot be
    the reason work stops — and removes the silence it was bought with.**

    SystemExit IS NOT A CRASH. `guard.py` refuses by `sys.exit(2)`, which is a BaseException; a
    refusal is the guard working. Recording it as an error would make every correct refusal look
    like a fault, and a warden that cries wolf gets filtered within a day (P17).
    """
    beat(root, name, "start")
    try:
        rc = fn(*a, **kw)
        beat(root, name, "ok", "" if not rc else "exit %s" % rc)
        return rc or 0
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 0
        beat(root, name, "ok", "exit %s (refusal or deliberate stop)" % code)
        return code
    except BaseException as e:
        beat(root, name, "error", "%s: %s" % (type(e).__name__, e))
        return 0


def check(root, expect=None, at_start=False):
    """[(severity, name, line)] — "DEAD", "CRASHED", "STALE" or "FLAPPING". at_start (31be): the session-open banner - a per-call watcher has
    not been asked for anything yet, so it is never STALE there (the agent, 2026-10-08: "the wall-clock watcher silent for 143 minutes" at session start
    was the previous session's picture-reading stretch, where the guard beats on every Read and the clock only on Bash / Task)."""
    out, now = [], time.time()
    beats = {}
    for name in (expect or WATCHERS):
        d = _read(root, name)
        if d and d.get("t"):
            beats[name] = float(d.get("t", 0))
    latest = max(beats.values()) if beats else now
    percall = {n for n, sp in (expect or WATCHERS).items() if "tool call" in str(sp.get("every", ""))}
    latest_pc = max([beats[n] for n in percall if n in beats] or [latest])
    for name, spec in sorted((expect or WATCHERS).items()):
        d = _read(root, name)
        if not d:
            if not spec.get("optional"):
                if name in percall:
                    out.append(("NOT YET", name, "%s has not run yet in this project - it starts with your first tool call (a new project, or a hook that has not fired yet; nothing is wrong)" % name))
                else:
                    out.append(("DEAD", name,
                                "%s HAS NEVER RUN in this project. %s" % (name, spec["why"])))
            continue
        age = ((latest_pc if name in percall else latest) - float(d.get("t", 0))) / 60.0
        age_wall = (now - float(d.get("t", 0))) / 60.0
        if d.get("phase") == "error":
            out.append(("CRASHED", name,
                        "%s crashed %s: %s" % (name, d.get("last_error_at", "?"),
                                               d.get("last_error", "?"))))
        elif d.get("phase") == "start" and age_wall > MID_RUN_MIN:
            out.append(("CRASHED", name,
                        "%s started %.0f min ago and never finished — it died mid-run, so no "
                        "exception handler of its own could report it." % (name, age_wall)))
        elif spec.get("stale_min") and age > spec["stale_min"] and not (at_start and name in percall):
            out.append(("STALE", name,
                        "%s last ran %.0f min ago, and other watchers have beaten %.0f min since it - a session ran and it"
                        " did not; it should run %s. %s" % (name, age_wall, age, spec["every"], spec["why"])))
        runs, errs = int(d.get("runs", 0)), int(d.get("errors", 0))
        if errs > 2 and runs and errs > 0.2 * runs:
            out.append(("FLAPPING", name,
                        "%s has failed %d of %d runs — it works often enough to look healthy. "
                        "Last: %s" % (name, errs, runs, d.get("last_error", "?"))))
    return out


def report(root, expect=None, at_start=False):
    """The lines to print. Empty when everything that should be beating is. at_start: the session-open banner (per-call watchers not judged stale).

    IT REPORTS AND NEVER REFUSES (the client, 2026-09-14: "Dead guards report"). A watcher that blocks work
    when another watcher stops is a second failure stacked on the first, and the guard already has
    the one refusal that matters — `kit.py` will not touch FreeCAD on a stale `.guard_alive`.
    """
    findings = check(root, expect, at_start=at_start)
    if not findings:
        return []
    soft = [f for f in findings if f[0] == "NOT YET"]; hard = [f for f in findings if f[0] != "NOT YET"]
    if not hard:
        return ["[liveness] the per-call watcher(s) %s have not run yet in this project - they start with your first tool call; nothing is wrong at a new project's first session." % ", ".join(n for _s, n, _l in soft)]
    out = ["!" * 78,
           "A WATCHER IS NOT REPORTING. This is the failure that hides every other one.", ""]
    for sev, _n, line in hard:
        out.append("    %-9s %s" % (sev, line))
    if soft:
        out.append("    %-9s %s" % ("NOT YET", "%s: not run yet in this project (it starts with the first tool call) - nothing is wrong with these" % ", ".join(n for _s, n, _l in soft)))
    out += ["",
            "A crashed watcher and a quiet one produce the same observable — nothing — which is why",
            "a MISSING beat is itself a finding here.",
            "Say what is dead, in the message body, and do not clear it by deleting the beat file."]
    if any(n == "guard" for _s, n, _l in hard):
        out.append("If the GUARD is the dead one, stop: the round is not valid unguarded.")
    out.append("!" * 78)
    return out


def main(argv=None):
    root = os.getcwd()
    while root and not os.path.isdir(os.path.join(root, ".claude")) \
            and os.path.dirname(root) != root:
        root = os.path.dirname(root)
    lines = report(root)
    if lines:
        print("\n".join(lines))
        return 1
    print("[liveness] every declared watcher is beating.")
    for name in sorted(WATCHERS):
        d = _read(root, name)
        if d:
            print("    %-14s %5.0f min ago   runs %s  errors %s"
                  % (name, (time.time() - float(d.get("t", 0))) / 60.0,
                     d.get("runs", "?"), d.get("errors", 0)))
        elif not WATCHERS[name].get("optional"):
            print("    %-14s NEVER RUN" % name)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))

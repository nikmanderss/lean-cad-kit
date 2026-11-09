#!/usr/bin/env python3
r"""waitlib.py — A WAITER THAT DOES NOT CHECK LIVENESS IS NOT A WAITER.

R19 orchestrator, 2026-09-14: ten minutes were spent polling a job whose worker had **already
died**. The status file said `running` forever, because nothing was alive to change it. the client spotted
it before the tooling did:

> *"Does 'Wait for the multi-card fuse' mean that you are running the task there ... It sounds like
> the latter but I see nothing else running"* — and the client was right. The process was gone.

**A status file records intent, not existence.** `{"state": "running"}` means "the last thing that
wrote this file expected to keep going", which is exactly as true of a job that finished a
microsecond later, a job that crashed, and a job the OS killed. The only thing that answers *is it
still running* is the process table.

Three failures this closes, all from the same week:

1. **The dead poll above** — a wait with no liveness check runs to its full timeout on a corpse.
2. **The untagged status file** — `job_compare_pics.py` writes `status_compare.json` with no tag, so
   a waiter read a PREVIOUS run's terminal state and reported TIMEOUT on a job that was working
   perfectly. `wait_job()` therefore requires the tagged path and refuses an obviously shared name.
3. **The silent timeout** (L11) — a wait that gives up quietly turns a bug into "the kernel is slow
   today". Every return here says which of the four things happened and why.

Nothing in this file raises. It reports.
"""

import json
import os
import time

SHARED_NAMES = ("status_compare.json", "status.json", "status_run.json")


def alive(pid):
    """Is this PID a live process? None when we cannot tell (never guess 'yes')."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return None
    if pid <= 0:
        return None
    if os.name == "nt":
        import subprocess
        try:
            r = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"],
                               capture_output=True, text=True, timeout=20)
            return str(pid) in (r.stdout or "")
        except Exception:
            return None
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return None


def read_status(path):
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def wait_job(status_path, timeout_s=300, poll_s=2.0, expect_min_s=0.0, say=print):
    """Wait for a job to finish. Returns (outcome, status_dict, seconds).

    outcome is one of:
      "done"    — the job wrote a terminal state
      "failed"  — likewise, and it says it failed
      "dead"    — **its process is gone and the file still says running.** This is the one a
                  status-only waiter cannot see, and it is why this function exists
      "timeout" — still alive, still working, and it outlasted the budget: a REPORT, not a verdict
      "nofile"  — nothing ever wrote the file (check the job actually writes this name — L11 rule 2)

    `expect_min_s` is the step's expected wall time. Exceeding it by more than ~2x is L11's
    definition of stuck; the message says so rather than leaving it to be noticed.
    """
    base = os.path.basename(str(status_path))
    if base in SHARED_NAMES:
        say("[wait] REFUSED: %r is an untagged status file. Two runs share it, and a waiter then "
            "reads the PREVIOUS run's terminal state - that reported TIMEOUT on a healthy job on "
            "2026-09-14. Give the job a LK_TAG and wait on the tagged name." % base)
        return "nofile", {}, 0.0

    t0 = time.time()
    seen_pid, last_size = None, -1
    while True:
        st = read_status(status_path)
        if st:
            seen_pid = st.get("pid", seen_pid)
            state = str(st.get("state", "")).lower()
            if state in ("done", "ok", "finished"):
                return "done", st, time.time() - t0
            if state in ("failed", "error", "refused"):
                say("[wait] %s FAILED: %s" % (base, str(st.get("error", ""))[:200]))
                return "failed", st, time.time() - t0
            if seen_pid and alive(seen_pid) is False:
                say("[wait] %s says 'running' and PID %s IS GONE after %.0f s.\n"
                    "       The process died without writing a terminal state - a crash, a kill, or "
                    "the machine.\n"
                    "       Do NOT keep waiting and do NOT treat any output already on disk as a "
                    "product: read the log, then re-run." % (base, seen_pid, time.time() - t0))
                return "dead", st, time.time() - t0
        elif time.time() - t0 > min(30.0, timeout_s):
            say("[wait] %s has not appeared after %.0f s. Check the job actually WRITES this name - "
                "`job_fields_dump.py` wrote no status file at all and every wait on it ran to its "
                "full timeout." % (base, time.time() - t0))

        el = time.time() - t0
        if expect_min_s and el > 2.0 * expect_min_s and int(el) % 60 < poll_s:
            say("[wait] %s has run %.0f s against an expectation of %.0f s. Over about 2x is STUCK, "
                "not working hard (L11) - decide, do not drift." % (base, el, expect_min_s))
        if el > timeout_s:
            live = alive(seen_pid) if seen_pid else None
            say("[wait] TIMEOUT after %.0f s waiting for %s (pid %s is %s)."
                % (el, base, seen_pid,
                   {True: "ALIVE - it is still working", False: "GONE", None: "unknown"}[live]))
            return "timeout", read_status(status_path), el
        time.sleep(poll_s)


def wait_all(status_paths, timeout_s=600, poll_s=2.0, say=print):
    """Wait for a fan-out. Returns {path: (outcome, status, secs)} and reports the first bad one.

    ONE DEAD SHARD FAILS THE REVIEW. A parallel orbit review whose shard 4 died has a hole in its
    coverage, and a hole in coverage is the thing the client gated against - it is not "5 of 6 passed".
    """
    out, t0 = {}, time.time()
    for p in status_paths:
        left = max(10.0, timeout_s - (time.time() - t0))
        out[p] = wait_job(p, timeout_s=left, poll_s=poll_s, say=say)
    bad = {p: v for p, v in out.items() if v[0] != "done"}
    if bad:
        say("[wait] %d of %d shard(s) did NOT finish cleanly: %s"
            % (len(bad), len(out), ", ".join(sorted(os.path.basename(p) for p in bad))))
        say("       The review is INCOMPLETE. Re-render the missing shard before anyone reviews "
            "anything - a sweep with a gap in it is not a full orbit.")
    return out

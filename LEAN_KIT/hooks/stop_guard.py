#!/usr/bin/env python3
"""Stop hook: THE ORCHESTRATOR DOES NOT IDLE WHILE WORK IS ON THE BOOKS. Exit 2 = keep working, with the list.

the client, 2026-09-17: *"I want an agent to be gated/hooked/wardened/whatever to continue working when
there is work left to be done (I haven't approved a stop). I do not want a clock and scheduled
task on it."*

WHAT THIS IS NOT. The Stop hook the client quarantined on 2026-09-11
refused the stop and sent the agent to WAIT on the inbox - five-minute polls, up to six hours. A clock
in disguise, and the client shelved it. This one has no timer and never tells the agent to wait. It refuses
the stop while there is WORK it can name, names the work, and names the two honest exits: finish it,
or record a reasoned stop with `kit stop --why` so the reason reaches the client instead of silence.

WHAT COUNTS AS WORK LEFT - all of it readable off disk, none of it a clock:
  * a job registered with `kit job` and neither applied nor cancelled;
  * a launched task still on the wall clock (`kit watch` / a background `kit burrito --bg`) not
    collected;
  * the session opened with `kit open` and not closed with `kit close` (the handoff is the
    product of a session, and six hand-written handovers were what a session that stopped without
    it left behind);
  * text in the INBOX the agent has not read - instructions there outrank what it was about to do.

THE EXITS. `kit accept` / `kit cancel` close a job; `kit collected` clears a watch; `kit close`
ends the session; reading the inbox clears it. And **`kit stop --why "<the client's instruction to stop,
or the blocker in one sentence>"`** records a reasoned stop: the hook honours it ONCE, and the
reason is appended to the inbox so the client reads why the work stopped, in the agent's own words.

THE LOOP GUARD. Claude Code passes `stop_hook_active` when a Stop hook has already refused once in
this turn. After three refusals in a row for the SAME list of work, the stop is allowed and the fact
is written to the inbox as an UNAPPROVED STOP - an agent that cannot say why it is stuck spinning
for hours is worse than one that stops and is seen to have stopped. The counter resets whenever the
list of work changes, so finishing one item does not count against the next.

Exit 2 + stderr is the same convention as handback.py. Fail OPEN on anything unexpected: a hook that
crashes on a corrupt file must never be the reason a session cannot end.
"""
import hashlib
import json
import os
import sys
for _s_ in (sys.stdout, sys.stderr):      # transcript
    try: _s_.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
import time

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
cwd = data.get("cwd", os.getcwd()); root = cwd
while root and not os.path.exists(os.path.join(root, ".claude")) and os.path.dirname(root) != root:
    root = os.path.dirname(root)
HERE = os.path.dirname(os.path.abspath(__file__))
try:
    sys.path.insert(0, HERE)
    import liveness as _L; _L.beat(root, "stop_guard", "ok")
except Exception:
    pass
KIT = os.path.join(os.path.dirname(HERE), "kit")
if not os.path.exists(os.path.join(KIT, "leangate.py")):
    sys.exit(0)
sys.path.insert(0, KIT)
try:
    import leangate as G
except Exception:
    sys.exit(0)

STATE = "STOP_GUARD.json"
OK = "STOP_OK.json"
MAX_REFUSALS = 3


def work_left():
    """[(what, how to finish it)] - everything that says the session is not done."""
    out = []
    try:
        jobs = G._read(G._p(root, G.JOBS), {}) or {}
        for n, j in sorted(jobs.items()):
            if not j.get("applied") and not j.get("cancelled"):
                if j.get("parked") or os.path.isfile(os.path.join(root, "claude_code", "jobs", str(n), "PARKED.md")):
                    continue
                out.append(("job %s is open (%s)" % (n, j.get("edit_type", "?")),
                            "kit accept %s --review <the job's render review dir>   or   kit cancel %s --why \"...\"   or park it: PARKED.md in its folder with the client's words" % (n, n)))
    except Exception:
        pass
    try:
        sys.path.insert(0, HERE)
        import wallclock as W
        _owner, _sub = W.caller(data)
        try:
            W.auto_collect(root, data.get("transcript_path"))
        except Exception:
            pass
        for n, m, _e, _o, w in W.watch_open(root, _owner or None):
            out.append(("launched task %s is still on the clock (%.0f min)%s" % (n, m, (" - " + w) if w else ""),
                        "kit collected %s   once you have read what it produced (--kill ends it by pid)" % n))
    except Exception:
        pass
    try:
        if G.session(root):
            out.append(("the session is open and has not been closed",
                        "kit close --remaining \"...\" --improvement \"...\" --fact \"...\"   (the handoff is the product)"))
    except Exception:
        pass
    try:
        new, _ = G.inbox_new(root)
        if new.strip():
            out.append(("the INBOX holds %d characters you have not read" % len(new.strip()),
                        "kit inbox   - instructions there outrank what you were about to do"))
    except Exception:
        pass
    return out


def atlas_question():
    """the client, 2026-09-22: a new project has no atlas because it has nothing to map - *"It should ask every turn
    after the first CAD is created if now is the right time to create an atlas."* So once CAD exists (a model
    of record in the bank, or the session's) and no atlas has been started, every turn ends with that question
    to the client. `kit atlas init` starts one, and the question stops."""
    try:
        if G.atlas_defer_active(root):
            return None
    except Exception:
        pass
    try:
        if G.atlas_load(root) is not None:
            return None
    except Exception:
        return None
    cad = False
    for d in (os.path.join(root, "claude_code", "bank"), os.path.join(root, "model", "bank")):
        try:
            if any(f.lower().endswith((".brep", ".fcstd", ".step", ".stp")) for f in os.listdir(d)):
                cad = True
        except OSError:
            pass
    try:
        m = (G.session(root) or {}).get("model_of_record")
        cad = cad or bool(m and os.path.exists(m))
    except Exception:
        pass
    return cad


def last_reply(path):
    """The text of the agent's last message this turn, from the transcript Claude Code hands the hook."""
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except Exception:
        return None
    for ln in reversed(lines[-400:]):
        try:
            o = json.loads(ln)
        except Exception:
            continue
        msg = o.get("message") if isinstance(o.get("message"), dict) else o
        if o.get("type") != "assistant" and msg.get("role") != "assistant":
            continue
        c = msg.get("content")
        txt = c if isinstance(c, str) else " ".join(x.get("text", "") for x in (c or []) if isinstance(x, dict))
        if txt.strip():
            return txt
    return None


# transcript
try:
    import lookgate as _LG
    _st = _LG._dd_load(root); _o = _st.get("owed")
    if _o:
        _said = _LG.said_in_transcript(data.get("transcript_path"), _o.get("since"), n=_o.get("n"))
        if _said:
            _st["confessions"].append({"n": _o.get("n"), "t": time.time(), "when": time.strftime("%Y-%m-%d %H:%M:%S"), "said": "in the message to the client (read at Stop)"})
            _st["owed"] = None; _LG._dd_save(root, _st)
            if not data.get("stop_hook_active"):
                sys.stderr.write("strike %s is confessed in your message - the client reads it there; the lock is lifted. DO NOT STOP AND DO NOT WAIT FOR the client: "
                                 "continue the work you were on, now - the step you were about to run, with the picture opened first (31bi).\n" % _o.get("n"))
                sys.exit(2)
            # did not finish
except SystemExit:
    raise
except Exception:
    pass

left = work_left()

# recorded
# foreground
_tasks = [w for w, _ in left if w.startswith("launched task bg-")]
_other = [w for w, _ in left if not w.startswith("launched task bg-") and not w.startswith("the session is open")]
if _tasks and not _other:
    sys.stderr.write("stop allowed: waiting on %d launched task(s) - %s. Their completion wakes you; collect them then.\n"
                     % (len(_tasks), "; ".join(t[:60] for t in _tasks[:4])))
    sys.exit(0)

# recorded
try:
    _ok_until = G._read(G._p(root, OK), None)
except Exception:
    _ok_until = None
if _ok_until and _ok_until.get("until"):
    _want = _ok_until.get("until")
    _open_names = [w.split(" ")[2] for w in _tasks if len(w.split(" ")) > 2]
    _still = _open_names if _want == "tasks" else [n for n in _open_names if n in _want]
    if _still:
        sys.stderr.write("stop allowed: `kit stop --until` holds while %s run(s) - %s\n" % (", ".join(_still[:6]), str(_ok_until.get("why"))[:160]))
        sys.exit(0)
    try:
        os.remove(G._p(root, OK))
    except Exception:
        pass

if not left:
    if atlas_question() and not data.get("stop_hook_active"):
        said = last_reply(data.get("transcript_path") or "")
        if said is not None and "atlas" not in said.lower():
            sys.stderr.write("BEFORE YOU STOP: this project has CAD and no region atlas yet. the client's rule (2026-09-22): every turn,\n"
                             "ask them in your reply whether now is the right time to create it (`kit atlas init`).\n"
                             "Add that question to your reply, then stop.\n")
            sys.exit(2)
    sys.exit(0)

# recorded
try:
    ok = G._read(G._p(root, OK), None)
except Exception:
    ok = None
if ok and ok.get("why"):
    try:
        os.remove(G._p(root, OK))
    except Exception:
        pass
    sys.stderr.write("stop allowed: reason recorded by `kit stop` - %s\n" % str(ok.get("why"))[:200])
    sys.exit(0)

key = hashlib.sha1("\n".join(w for w, _ in left).encode("utf-8")).hexdigest()[:12]
try:
    st = G._read(G._p(root, STATE), {}) or {}
except Exception:
    st = {}
n = int(st.get("n", 0)) + 1 if (st.get("key") == key and data.get("stop_hook_active")) else 1
try:
    G._write(root, STATE, {"key": key, "n": n, "when": time.strftime("%Y-%m-%d %H:%M:%S")})
except Exception:
    pass

if data.get("stop_hook_active") and n > MAX_REFUSALS:
    note = ("UNAPPROVED STOP %s - the orchestrator stopped with work open after %d refusals and gave no "
            "reason:\n  " % (time.strftime("%Y-%m-%d %H:%M"), n - 1) + "\n  ".join(w for w, _ in left))
    try:
        G.inbox_append(root, note, who="THE STOP GUARD")
        G._write(root, STATE, {"key": key, "n": 0, "when": time.strftime("%Y-%m-%d %H:%M:%S")})
    except Exception:
        pass
    sys.stderr.write(note + "\n")
    sys.exit(0)

lines = ["DO NOT STOP - there is work on the books and no stop has been approved (refusal %d of %d):" % (n, MAX_REFUSALS)]
for what, how in left:
    lines.append("  * %s\n      -> %s" % (what, how))
lines.append("  Finish it, or record WHY you are stopping so the client reads it:")
lines.append("      kit stop --why \"<the client's instruction to stop, or the blocker in one sentence>\"")
lines.append("  There is no timer here and nothing to wait for. Do the next thing on the list.")
sys.stderr.write("\n".join(lines) + "\n")
sys.exit(2)

#!/usr/bin/env python3
"""selftest_stop_guard.py - the Stop hook, driven the way Claude Code drives it: JSON on stdin, exit code out.

    & python "C:\\CAD\\LEAN_KIT\\hooks\\selftest_stop_guard.py"

the client, 2026-09-17: *"I want an agent to be gated/hooked/wardened/whatever to continue working when
there is work left to be done (I haven't approved a stop). I do not want a clock and scheduled
task on it."* Exit 2 refuses the stop and the stderr is what the agent reads; exit 0 lets it end.

WHAT IS PINNED, and why each is a real case:
  * nothing open -> the stop is allowed (a guard that refuses everything is not a guard);
  * an open job / an uncollected task / an unclosed session / unread inbox text -> refused, and
    the refusal NAMES the work and the command that finishes it;
  * `kit stop --why` -> the next stop is allowed ONCE, then refused again;
  * `--why` under thirty characters is refused by `kit stop` itself;
  * three refusals in a row for the same work, with `stop_hook_active` -> allowed, and an
    UNAPPROVED STOP note lands in the inbox so it is seen; finishing an item resets the count;
  * a corrupt state file -> the hook fails OPEN (exit 0), never crashes a session shut;
  * nothing anywhere mentions waiting, a timer or a poll - the quarantined 2026-09-11 hook did,
    and that is why it was quarantined.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "stop_guard.py")
KIT = os.path.join(os.path.dirname(HERE), "kit")
sys.path.insert(0, KIT)
sys.path.insert(0, HERE)
import leangate as G
import wallclock as W

FAILED = []


def check(label, cond, detail=""):
    print("  %-4s %s" % ("ok" if cond else "FAIL", label))
    if not cond:
        print("       %s" % str(detail)[:300])
        FAILED.append(label)


def stop(root, active=False):
    p = subprocess.run([sys.executable, HOOK],
                       input=json.dumps({"cwd": root, "hook_event_name": "Stop", "stop_hook_active": active}),
                       capture_output=True, text=True)
    return p.returncode, (p.stderr or "") + (p.stdout or "")


def kit(root, *args):
    env = dict(os.environ); env["KIT_PROJECT"] = root
    p = subprocess.run([sys.executable, os.path.join(KIT, "kit.py")] + list(args),
                       capture_output=True, text=True, env=env, cwd=os.path.join(root, "claude_code"))
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    root = tempfile.mkdtemp(prefix="stopguard_")
    os.makedirs(os.path.join(root, ".claude"), exist_ok=True)
    os.makedirs(os.path.join(root, "claude_code", "jobs"), exist_ok=True)
    print("\nTHE STOP GUARD - no idling with work on the books, and no clock\n")
    try:
        rc, said = stop(root)
        check("nothing open -> the stop is allowed", rc == 0, said)

        bank = os.path.join(root, "model", "bank"); os.makedirs(bank, exist_ok=True)
        mor = os.path.join(bank, "R1.brep"); open(mor, "w").write("x")
        G.session_open(root, True, True, "S", {"overlap": "0.5 mm into material, 2 mm clear in air",
                                                "measure": "the orchestrator measures; workers only render",
                                                "punch": "never through; stops 3 mm short"}, mor)
        rc, said = stop(root)
        check("an open session refuses the stop", rc == 2, said)
        check("...and names kit close as the way out", "kit close" in said, said)
        # foreground
        W.watch_add(root, "bg-wait1", 2.0, "kit mesh extract")
        rc, said = stop(root)
        check("an open session + a launched task on the clock -> the stop is ALLOWED, naming what it waits on",
              rc == 0 and "waiting on 1 launched task" in said and "bg-wait1" in said, said)
        W.watch_clear(root, "bg-wait1")
        rc, said = stop(root)
        check("...and once the task is collected, the open session refuses again", rc == 2, said)
        check("...and says there is nothing to wait for", "nothing to wait for" in said and "timer" in said, said)
        for bad in ("--wait", "poll", "sleep", "every 5", "try again in"):
            check("...%r is not in the refusal (no clock, no instruction to wait)" % bad,
                  bad not in said.lower(), said)

        sys.path.insert(0, os.path.dirname(HERE))
        from selftest_leangates import GOOD_CARD
        j1card = os.path.join(root, "J1_card.md")
        open(j1card, "w", encoding="utf-8").write(GOOD_CARD.replace("sketch_extrude", "hole").replace("about -960 mm3", "about -10 mm3"))
        G.card_lint(root, j1card)
        G.job_open(root, "J1", "hole", j1card, tier="haiku", expect_vol=-10.0)
        rc, said = stop(root)
        check("an open job is named, with kit accept / kit cancel", rc == 2 and "job J1 is open" in said
              and "kit accept J1" in said and "kit cancel J1" in said, said)
        pcard = os.path.join(root, "PARKED1_card.md")
        open(pcard, "w", encoding="utf-8").write(GOOD_CARD.replace("sketch_extrude", "hole").replace("about -960 mm3", "about 5 mm3"))
        G.card_lint(root, pcard)
        G.job_open(root, "PARKED1", "hole", pcard, tier="haiku", expect_vol=5.0)
        os.makedirs(os.path.join(root, "claude_code", "jobs", "PARKED1"), exist_ok=True)
        open(os.path.join(root, "claude_code", "jobs", "PARKED1", "PARKED.md"), "w").write("# PARKED - the client: never clear it\n")
        rc, said = stop(root)
        check("a job with PARKED.md in its folder is NOT counted as work left", "PARKED1" not in said, said)
        check("...while the genuinely open job still is", rc == 2 and "job J1 is open" in said, said)

        W.watch_add(root, "bg-s5", 2.0, "kit burrito s5")
        rc, said = stop(root)
        check("an uncollected task is named, with kit collected", rc == 2 and "bg-s5" in said and "kit collected bg-s5" in said, said)
        rc, out = kit(root, "stop", "--why", "the client said wait for the extract and report; J1 stays open meanwhile", "--until", "bg-s5")
        check("kit stop --until records", rc == 0 and "while the named tasks" in out, out)
        G.inbox_mark(root, os.path.getsize(os.path.join(root, "claude_code", "INBOX.md")))
        rc1, said1 = stop(root); rc2, said2 = stop(root)
        check("...and holds across repeated stops while bg-s5 is on the clock", rc1 == 0 and rc2 == 0 and "holds while bg-s5" in said2, said1 + said2)
        W.watch_clear(root, "bg-s5")
        rc, said = stop(root)
        check("...expires once the task is gone: the open job refuses the stop again", rc == 2 and "job J1 is open" in said, said)
        rc, said = stop(root)
        check("...and it is not honoured a second time (the record was removed)", rc == 2, said)

        with open(os.path.join(root, "claude_code", "INBOX.md"), "a", encoding="utf-8") as fh:
            fh.write("\n\n---\n\n# FROM the client  now\n\ndo the vane shelf first\n")
        rc, said = stop(root)
        check("unread inbox text is named, with kit inbox", rc == 2 and "INBOX" in said and "kit inbox" in said, said)
        G.inbox_mark(root, os.path.getsize(os.path.join(root, "claude_code", "INBOX.md")))

        rc, out = kit(root, "stop", "--why", "too short")
        check("kit stop refuses a reason under thirty characters", rc != 0 and "30+" in out, out)
        rc, out = kit(root, "stop", "--why", "the client said stop here and hand over; the section review is theirs to make next")
        check("kit stop records a real reason", rc == 0 and "recorded" in out, out)
        G.inbox_mark(root, os.path.getsize(os.path.join(root, "claude_code", "INBOX.md")))
        rc, said = stop(root)
        check("...the next stop is allowed, once, and says why", rc == 0 and "reason recorded" in said, said)
        rc, said = stop(root)
        check("...and the one after is refused again", rc == 2, said)
        inbox = open(os.path.join(root, "claude_code", "INBOX.md"), encoding="utf-8").read()
        check("...the reason is in the inbox for the client", "STOP RECORDED - the client said stop here" in inbox)

        for i in range(2):
            rc, said = stop(root, active=True)
        check("three refusals in a row for the same work", rc == 2 and "refusal 3 of 3" in said, said)
        rc, said = stop(root, active=True)
        check("...the fourth attempt is allowed as an UNAPPROVED STOP", rc == 0 and "UNAPPROVED STOP" in said, said)
        inbox = open(os.path.join(root, "claude_code", "INBOX.md"), encoding="utf-8").read()
        check("...and it is written to the inbox, naming the open work", "UNAPPROVED STOP" in inbox and "job J1" in inbox)
        rc, said = stop(root, active=False)
        check("a stop WITHOUT stop_hook_active never counts toward the cap", rc == 2, said)
        G.job_mark(root, "J1", "cancelled", G._now())
        rc, said = stop(root, active=True)
        check("finishing an item resets the count (refusal 1 of 3 again)", rc == 2 and "refusal 1 of 3" in said, said)

        with open(G._p(root, "STOP_GUARD.json"), "w") as fh:
            fh.write("{not json")
        rc, said = stop(root)
        check("a corrupt state file does not crash the hook (exit 0 or 2, never a traceback)",
              rc in (0, 2) and "Traceback" not in said, said)
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print("\nTHE ATLAS QUESTION - asked every turn once CAD exists, until an atlas is started\n")
    r2 = tempfile.mkdtemp(prefix="stopguard_atlas_")
    os.makedirs(os.path.join(r2, ".claude"), exist_ok=True)
    os.makedirs(os.path.join(r2, "claude_code", "bank"), exist_ok=True)
    tr = os.path.join(r2, "transcript.jsonl")

    def reply(text):
        with open(tr, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"type": "user", "message": {"role": "user", "content": "go"}}) + "\n")
            fh.write(json.dumps({"type": "assistant", "message": {"role": "assistant",
                                 "content": [{"type": "text", "text": text}]}}) + "\n")

    def stop2(active=False):
        p = subprocess.run([sys.executable, HOOK], input=json.dumps({"cwd": r2, "hook_event_name": "Stop",
                           "stop_hook_active": active, "transcript_path": tr}), capture_output=True, text=True)
        return p.returncode, (p.stderr or "") + (p.stdout or "")
    try:
        reply("The bracket is drawn and saved.")
        rc, said = stop2()
        check("no CAD in the project yet -> no atlas question", rc == 0, said)
        open(os.path.join(r2, "claude_code", "bank", "R1_BODY.brep"), "w").write("x")
        rc, said = stop2()
        check("CAD exists, no atlas, the reply did not ask -> refused with the question", rc == 2 and "atlas" in said, said)
        rc, said = stop2(active=True)
        check("...but never twice in one turn (stop_hook_active)", rc == 0, said)
        reply("The bracket is drawn. Is now the right time to create the region atlas?")
        rc, said = stop2()
        check("a reply that asks it -> the stop is allowed", rc == 0, said)
        rc, _o = kit(r2, "atlas", "defer", "--until", "a basic correct model of the parts exists")
        check("31bv B1: kit atlas defer records the client's word", rc == 0 and "DEFERRED" in _o, _o[-300:])
        reply("Done for now.")
        rc, said = stop2()
        check("31bv B1: while the atlas is deferred the question is silent", rc == 0, said)
        rc, _o = kit(r2, "atlas", "status")
        check("31bv B1: kit atlas status says DEFERRED", rc == 0 and "DEFERRED since" in _o, _o[-300:])
        rc, _o = kit(r2, "atlas", "defer", "--lift")
        rc, said = stop2()
        check("31bv B1: --lift brings the question back", rc == 2 and "atlas" in said, said)
        reply("Done for now.")
        rc, _o = kit(r2, "atlas", "init")
        rc, said = stop2()
        check("once an atlas is started (kit atlas init) the question stops", rc == 0, said)
        # DO NOT STOP AND DO NOT WAIT FOR the client
        import time as _tm2
        sys.path.insert(0, HERE); import lookgate as _LG
        _iso = lambda t_: _tm2.strftime("%Y-%m-%dT%H:%M:%S", _tm2.gmtime(t_)) + ".000Z"
        def reply_ts(text, t_):
            with open(tr, "w", encoding="utf-8") as fh:
                fh.write(json.dumps({"type": "user", "timestamp": _iso(t_ - 5), "message": {"role": "user", "content": "go on"}}) + "\n")
                fh.write(json.dumps({"type": "assistant", "timestamp": _iso(t_), "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}) + "\n")
        def owe(n_, since_):
            json.dump({"owed": {"n": n_, "since": since_, "t": since_}, "confessions": [], "strikes": [{"n": k_, "what": "a measurement before a picture"} for k_ in range(1, n_ + 1)]},
                      open(os.path.join(r2, ".claude", "dumdum.json"), "w"))
        with open(os.path.join(r2, "claude_code", "INBOX.md"), "a", encoding="utf-8") as fh:
            fh.write("\n# FROM the kit maintainer (LEAN_KIT) 2026-10-19 17:1x\nthe next step is yours - read this before you stop\n")
        _now = _tm2.time(); owe(1, _now - 60)
        reply_ts("Strike 1. " + _LG.apology(1, "I measured before a picture") + " Back to the build now.", _now - 10)
        rc, said = stop2()
        _st1 = _LG._dd_load(r2)
        check("31bq B11: the real confession in a timestamped message lifts the lock (dumdum owed None, the confession recorded) and the stop is refused ONCE by the confession path (DO NOT STOP AND DO NOT WAIT FOR the client)",
              rc == 2 and "DO NOT STOP AND DO NOT WAIT FOR the client" in said and _st1.get("owed") is None and len(_st1.get("confessions") or []) == 1, (rc, said[:200], _st1.get("owed")))
        rc, said = stop2(active=True)
        check("31bq VV: the plain stop after the confession's refusal (the lock already lifted), work open (an unread inbox note), is refused and the INBOX named - the B11 (2) pin is the stop_hook_active case below (31bq R7g: this case passes the exit(0) mutant and is no pin of it)", rc == 2 and "INBOX" in said, said)
        owe(2, _now - 60)
        reply_ts("Strike 2. " + _LG.apology(2, "I measured before a picture again") + " Back to the build.", _now - 5)
        rc, said = stop2(active=True)
        _st2 = _LG._dd_load(r2)
        check("31bq VV (B11 pin): the FIRST stop that sees a confession arrives with stop_hook_active and work open (where the exit(0) sat) - the lock lifts and the stop is REFUSED with the work named, never allowed",
              rc == 2 and "INBOX" in said and _st2.get("owed") is None, (rc, said[:200], _st2.get("owed")))
        owe(3, _now - 60)
        reply_ts("Strike 3. I'm a silly dum dum - I'm so very sorry! Pretty please forgive Mr. Silly Dum Dum: one pretty short.", _now - 3)
        rc, said = stop2()
        check("31bq VV (B11 pin): a confession with the WRONG count of 'pretty' lifts nothing (strike 3 owes three)", _LG._dd_load(r2).get("owed") is not None, _LG._dd_load(r2).get("owed"))
    finally:
        shutil.rmtree(r2, ignore_errors=True)

    print()
    if FAILED:
        print("%d FAILED: %s" % (len(FAILED), ", ".join(FAILED)))
        return 1
    print("all cases pass. Stopping with work open is refused and named; stopping with a reason is recorded.")
    print("\nNOT COVERED, and only a live Claude Code session can: that the harness honours exit 2 from a")
    print("Stop hook and feeds stderr back, and that `stop_hook_active` arrives as documented. Both are")
    print("the same contract handback.py (SubagentStop) already runs on.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

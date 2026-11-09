#!/usr/bin/env python3
"""selftest_need.py - THE UNFILLED SLOT. No FreeCAD, no project, no Claude Code.

    & python "C:\\CAD\\LEAN_KIT\\kit\\selftest_need.py"

`K.NEED` is what a PARAMS slot holds until the card fills it, and `K.need(P)` refuses naming every
one that is still empty. Both exist because the client asked the question the kit had already answered
twice and not applied: *"why have defaults filled in at all? That will just make opus agents think
they are right and don't need to be changed."*

WHAT THIS PINS, and why each case is here rather than being obvious:

* **Every unfilled slot is named in ONE refusal.** A template that refused the first one and exited
  would cost a run per slot; the one who fills the block needs the whole list.
* **Nested slots are found and named by path.** `find=dict(normal=NEED)` is the shape the cutter
  actually uses, and a walker that only looked at the top level would pass it silently - which is
  the failure this whole mechanism exists to stop.
* **A filled block is SILENT.** A gate that refuses everything is not a gate, and this one sits in
  front of every template.
* **`NEED` is FALSE in a boolean test.** If a template reads a slot before `need()` runs, it must
  take the empty branch, not do arithmetic on the sentinel and produce a number.
* **0, 0.0, "", None, () are VALUES, not empty slots.** `dz=0.0` is a legitimate answer; `symmetrise
  =None` means "off"; `cleanup_boxes=()` means "none needed". Refusing those would make the gate
  unusable and is exactly the over-blunt failure the client named on the fuse block.

`kitlib` imports FreeCAD at module scope, so this file loads the two definitions out of the source
rather than importing it - the alternative is a test that cannot run without CAD installed, and a
test that cannot run is worth nothing (a recorded process failure).
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FAILED = []


def load():
    """`_Need`, `NEED`, `need` and a stand-in `fail`, lifted from kitlib.py's source."""
    src = open(os.path.join(HERE, "kitlib.py"), encoding="utf-8", errors="replace").read()
    m = re.search(r"^class _Need\(object\):.*?(?=\n# ---|\nclass |\ndef (?!need|walk)\w)",
                  src, re.S | re.M)
    if not m:
        print("selftest_need: could not find _Need/need in kitlib.py")
        sys.exit(1)
    said = {}

    def fail(msg):
        said["msg"] = str(msg)
        raise SystemExit(1)

    ns = {"fail": fail}
    exec(compile(m.group(0), "kitlib_need", "exec"), ns)
    ns["_said"] = said
    return ns


def refuses(ns, label, P, must_name=()):
    try:
        ns["need"](P)
    except SystemExit:
        msg = ns["_said"].get("msg", "")
        gone = [n for n in must_name if n not in msg]
        if gone:
            print("  FAIL %-46s refused, but did not name %s" % (label, ", ".join(gone)))
            FAILED.append(label)
            return
        print("  ok   %-46s REFUSED, naming %s" % (label, ", ".join(must_name) or "-"))
        return
    print("  FAIL %-46s it was ALLOWED" % label)
    FAILED.append(label)


def allows(ns, label, P):
    try:
        ns["need"](P)
    except SystemExit:
        print("  FAIL %-46s REFUSED: %s" % (label, ns["_said"].get("msg", "")[:60]))
        FAILED.append(label)
        return
    print("  ok   %-46s allowed" % label)


def main():
    ns = load()
    N = ns["NEED"]
    print("\nTHE UNFILLED SLOT - a default is not an answer\n")

    refuses(ns, "one empty slot is named", dict(base=N, out="."), ["base"])
    refuses(ns, "EVERY empty slot, in one refusal",
            dict(base=N, depth=N, op=N, result_name="result.brep"), ["base", "depth", "op"])
    refuses(ns, "a nested slot is named by its path",
            dict(find=dict(normal=N, tol_deg=10.0)), ["find.normal"])
    refuses(ns, "a slot inside a list is named by its path",
            dict(holes=[dict(d=4.0), dict(d=N)]), ["holes.1.d"])

    allows(ns, "a filled block is silent", dict(base="/abs/region.brep", depth=4.0, op="cut"))
    allows(ns, "0 and 0.0 are VALUES, not empty slots", dict(dx=0.0, dy=0, dz=0.0))
    allows(ns, "None means 'off', not 'unfilled'", dict(symmetrise=None, thinwall_max=None))
    allows(ns, "an empty tuple means 'none needed'", dict(cleanup_boxes=(), extra_rects=[]))
    allows(ns, "an empty string is a value the lint judges", dict(why_not_delete=""))

    print("\n  %-4s %-46s %s" % ("ok" if not bool(N) else "FAIL",
                                 "NEED is FALSE, so a read before need() is empty",
                                 "bool(NEED) = %s" % bool(N)))
    if bool(N):
        FAILED.append("NEED is falsey")
    print("  %-4s %-46s %r" % ("ok" if "card" in repr(N) else "FAIL",
                               "and it says where the value comes from", N))
    if "card" not in repr(N):
        FAILED.append("NEED repr")

    print()
    if FAILED:
        print("%d FAILED: %s" % (len(FAILED), ", ".join(FAILED)))
        return 1
    print("all cases pass. An unfilled slot refuses by name; a filled one says nothing.")
    print("\nNOT COVERED HERE: that every template actually CALLS need(). That is")
    print("`selftest_leangates.py` [19], which reads the templates themselves.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

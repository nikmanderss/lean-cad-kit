#!/usr/bin/env python3
"""selftest_verdict.py - THE ORBIT GATE'S OWN TESTS. Run it with plain python; no FreeCAD needed.

WHY THIS FILE EXISTS. The gate mechanism was lifted into `kitlib` on 2026-09-16 so that every
template could use one implementation instead of each job carrying its own. The very first ad-hoc
run of it found a hole that had been in the original too:

    if v.get("card") and cardsig and v["card"] != cardsig:

A verdict recorded WITHOUT a card signature has an empty `card`, so that condition is false and the
verdict satisfies EVERY card that is ever put to it. The binding could be opted out of by leaving
one flag off `kit verdict`. That is the `_rebuild.py` shape again - a gate that can be skipped by
not using it is decoration - and the client's ruling is that the orbit gate is never bypassable: *"you
should be gated to never be allowed to bypass full orbit reviews. I don't care if you think it's
wasteful it's absolutely not."*

It was caught by writing the test, and by nothing else. So the test lives here now.

THE FOUR THINGS A VERDICT MUST BIND, each with a case below:
  1. THAT SOMEBODY LOOKED       - no verdict, or a `fail` verdict, refuses
  2. WHICH SHAPE they looked at - the artefact's content hash
  3. WHICH NUMBERS produced it  - the card signature, and a verdict naming NO card is refused
  4. THAT THEY LOOKED AT THIS ONE - the artefact must be OLDER than the verdict. This is the check
     that does the real work: it needs no cooperation from any other job, because a file written
     after somebody looked is a file nobody has looked at.
"""
import os
import sys
import time
import types

for _n in ("Part", "kitlib_render"):
    sys.modules.setdefault(_n, types.ModuleType(_n))
_fc = types.ModuleType("FreeCAD")
_fc.Vector = lambda *a, **k: None
sys.modules.setdefault("FreeCAD", _fc)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitlib as K

FAILED = []


def check(label, got, want):
    ok = got == want
    print("  %-4s %s" % ("ok" if ok else "FAIL", label))
    if not ok:
        print("        got  %r\n        want %r" % (got, want))
        FAILED.append(label)


def refuses(fn):
    """'' if it passed through, else the first line of the refusal."""
    try:
        fn()
        return ""
    except SystemExit as e:
        return str(e).split("\n")[0]


def main():
    import tempfile
    root = tempfile.mkdtemp(prefix="verdict_")
    art = os.path.join(root, "piece.brep")
    with open(art, "w") as fh:
        fh.write("pretend brep bytes\n")
    CARD = K.card_sig({"base": "b.brep", "smooth_mm": 2.5})
    OTHER = K.card_sig({"base": "b.brep", "smooth_mm": 3.0})
    K.fail = lambda m: (_ for _ in ()).throw(SystemExit(m))
    G = lambda step, card=CARD: refuses(
        lambda: K.verdict_require(root, step, art, card, "THE CUT", "kit review ..."))

    print("\n[1] NOBODY LOOKED")
    check("no verdict at all refuses", "no recorded orbit verdict" in G("s1"), True)
    K.verdict_write(root, "s2", art, CARD, "CLIENT", "frame 2 shows a step at the outboard third", "fail")
    check("a FAIL verdict refuses", "is 'fail', not pass" in G("s2"), True)

    print("\n[2] A GOOD VERDICT PASSES - a gate that refuses everything is not a gate")
    K.verdict_write(root, "s3", art, CARD, "CLIENT", "three frames, the step is gone, no island", "pass")
    check("pass + right card + right hash + older artefact", G("s3"), "")

    print("\n[3] WHICH NUMBERS - the hole that was found by writing this file")
    K.verdict_write(root, "s4", art, "", "CLIENT", "three frames, all clean, nothing standing", "pass")
    check("a verdict naming NO card is REFUSED", "names NO card signature" in G("s4"), True)
    K.verdict_write(root, "s5", art, OTHER, "CLIENT", "three frames, all clean, nothing standing", "pass")
    check("a verdict for a DIFFERENT card is refused", "the card has changed" in G("s5"), True)
    check("...and a job that signs no card still accepts it", G("s5", card=""), "")

    print("\n[4] WHICH SHAPE")
    K.verdict_write(root, "s6", art, CARD, "CLIENT", "three frames, all clean, nothing standing", "pass")
    with open(art, "a") as fh:
        fh.write("different bytes\n")
    check("changed content refuses", "is STALE" in G("s6"), True)

    print("\n[5] THAT THEY LOOKED AT THIS ONE - the check that needs no cooperation")
    K.verdict_write(root, "s7", art, CARD, "CLIENT", "three frames, all clean, nothing standing", "pass")
    time.sleep(1.1)
    os.utime(art, None)
    check("artefact NEWER than its verdict refuses, though the hash still matches",
          "is NEWER than the verdict" in G("s7"), True)

    print("\n[6] A MISSING ARTEFACT IS NOT A PASS")
    K.verdict_write(root, "s8", art, CARD, "CLIENT", "three frames, all clean, nothing standing", "pass")
    os.remove(art)
    check("a verdict about a file that is gone refuses", "does not exist" in G("s8"), True)

    print()
    if FAILED:
        print("%d FAILED: %s" % (len(FAILED), ", ".join(FAILED)))
        return 1
    print("all cases pass. The gate binds who looked, at which shape, built from which numbers,")
    print("and whether the shape has moved since.")
    print("\nNOT COVERED, and it cannot be here: whether the agent actually OPENED the frames.")
    print("Nothing on disk can prove that. `--saw` is the only witness, which is why a verdict")
    print("with fewer than 25 characters in it is refused by `kit verdict` rather than recorded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

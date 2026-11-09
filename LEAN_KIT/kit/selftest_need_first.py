#!/usr/bin/env python3
"""selftest_need_first.py - AN UNFILLED TEMPLATE REFUSES BEFORE IT TOUCHES THE KERNEL.

    & python "C:\\CAD\\LEAN_KIT\\kit\\selftest_need_first.py"

WHAT THIS CLOSES. `selftest_need.py` proves `K.need()` finds the empty slots. It does not prove the
thing that actually matters on the day: that a worker who runs an UNFILLED template gets the slot
list rather than a traceback out of the middle of `K.plane()`. the client, 2026-09-16: *"close the other
point before handover."*

HOW, WITHOUT FreeCAD. The kit's machine has the kernel; a maintenance sandbox does not. So this
executes **the real template files** with `FreeCAD`, `Part` and `kitlib_render` replaced by stubs,
and then **replaces every kernel-touching function in the real `kitlib` with one that raises**. If a
template reaches `K.load`, `K.plane`, `K.box`, `K.tess` or any other of them before refusing, this
file fails and names it.

WHAT IT STILL DOES NOT PROVE, and only the binary can: that `freecadcmd` prints what a script prints
before `SystemExit`. That is why `K.fail` prints FIRST and raises second (its own docstring: a bare
`raise SystemExit(text)` prints NOTHING under freecadcmd - the first burrito probe died with an empty
log that way), and why `kit run` scans the OUTPUT for a `FAIL:` line and sets its own exit code from
it rather than trusting the interpreter's. Both halves are checked below on the text this produces.
"""
import io
import re as _re
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(HERE, "templates")
EXEMPT = {"burrito"}
FAILED = []


def _stub_freecad():
    """Enough of FreeCAD/Part for `import kitlib` to succeed. Nothing here computes geometry."""
    class _Vec(object):
        def __init__(self, *a):
            self.x, self.y, self.z = (list(a) + [0, 0, 0])[:3]

    fc = types.ModuleType("FreeCAD")
    fc.Vector = _Vec
    fc.ActiveDocument = None
    fc.newDocument = lambda *a, **k: None
    fc.Base = types.SimpleNamespace(Vector=_Vec)
    part = types.ModuleType("Part")
    for n in ("Shape", "Solid", "Face", "Wire", "Edge", "Compound", "makePolygon",
              "makeBox", "makeCylinder", "LineSegment", "Arc", "BSplineCurve"):
        setattr(part, n, type(n, (object,), {"__init__": lambda self, *a, **k: None}))
    part.show = lambda *a, **k: None
    rend = types.ModuleType("kitlib_render")
    sys.modules.setdefault("FreeCAD", fc)
    sys.modules.setdefault("Part", part)
    sys.modules.setdefault("kitlib_render", rend)


def _arm(K):
    """Every kitlib entry point that reaches the kernel raises instead. Returns the tripwire list."""
    tripped = []
    names = [n for n in dir(K)
             if not n.startswith("_") and callable(getattr(K, n))
             and n not in ("fail", "need", "NEED")]

    def mk(n):
        def boom(*a, **k):
            tripped.append(n)
            raise AssertionError("K.%s() was called BEFORE the refusal" % n)
        return boom

    for n in names:
        try:
            setattr(K, n, mk(n))
        except (AttributeError, TypeError):
            pass
    return tripped


def run_one(name, K):
    """(outcome, text). Executes templates/t_<name>.py with PARAMS exactly as it ships."""
    path = os.path.join(TPL, "t_%s.py" % name)
    src = open(path, encoding="utf-8", errors="replace").read()
    tripped = _arm(K)
    out = io.StringIO()
    keep = sys.stdout
    sys.stdout = out
    try:
        exec(compile(src, path, "exec"), {"__name__": "__main__", "__file__": path})
    except SystemExit as e:
        return ("refused", out.getvalue(), int(e.code or 0), tripped)
    except AssertionError as e:
        return ("kernel", out.getvalue(), str(e), tripped)
    except Exception as e:
        return ("died", out.getvalue(), "%s: %s" % (type(e).__name__, str(e)[:120]), tripped)
    finally:
        sys.stdout = keep
    return ("ran", out.getvalue(), 0, tripped)


def main():
    _stub_freecad()
    sys.path.insert(0, HERE)
    try:
        import kitlib as K
    except Exception as e:
        print("selftest_need_first: could not import kitlib even with stubs (%s)" % e)
        return 1

    names = sorted(f[2:-3] for f in os.listdir(TPL)
                   if f.startswith("t_") and f.endswith(".py") and f[2:-3] not in EXEMPT)

    print("\nTHE HARNESS ITSELF\n")
    real = K.need.__code__.co_filename.endswith("kitlib.py")
    print("  %-4s `need` under test is the real one (%s)"
          % ("ok" if real else "FAIL", os.path.basename(K.need.__code__.co_filename)))
    if not real:
        FAILED.append("real need")
    _before = K.load
    _arm(K)
    armed = K.load is not _before
    try:
        K.load("x.brep")
        fires = False
    except AssertionError:
        fires = True
    except Exception:
        fires = False
    print("  %-4s the kernel tripwire is installed and FIRES when called"
          % ("ok" if (armed and fires) else "FAIL"))
    if not (armed and fires):
        FAILED.append("tripwire")

    print("\nAN UNFILLED TEMPLATE REFUSES BEFORE IT TOUCHES THE KERNEL\n")
    for n in names:
        outcome, text, detail, tripped = run_one(n, K)
        first = (text.strip().split("\n") or [""])[0][:64]
        src = open(os.path.join(TPL, "t_%s.py" % n), encoding="utf-8", errors="replace").read()
        blk = _re.search(r"^PARAMS\s*=\s*dict\(.*?^\)\s*$", src, _re.S | _re.M)
        declared = blk.group(0).count("K.NEED") if blk else -1
        said = _re.search(r"(\d+) slot\(s\)", text)
        counted = int(said.group(1)) if said else -1
        if outcome == "refused" and text.startswith("FAIL: PARAMS is not filled") \
                and counted == declared:
            print("  ok   %-20s refused, code %s, no kernel call, named %d of %d slots"
                  % ("t_" + n, detail, counted, declared))
        elif outcome == "refused" and counted != declared:
            print("  FAIL %-20s refused but named %d slots; the file declares %d K.NEED"
                  % ("t_" + n, counted, declared))
            FAILED.append("t_" + n)
        elif outcome == "refused" and text.startswith("FAIL: PARAMS is not filled"):
            print("  ok   %-20s refused, code %s, no kernel call" % ("t_" + n, detail))
        elif outcome == "kernel":
            print("  FAIL %-20s %s" % ("t_" + n, detail))
            FAILED.append("t_" + n)
        elif outcome == "refused":
            print("  FAIL %-20s exited %s but said %r, not the slot list"
                  % ("t_" + n, detail, first))
            FAILED.append("t_" + n)
        else:
            print("  FAIL %-20s %s (%s)" % ("t_" + n, outcome, detail))
            FAILED.append("t_" + n)

    print("\nTHE CONTROL - fill the slots and it stops refusing\n")
    for n in ("hole", "move", "split", "shell"):
        p = os.path.join(TPL, "t_%s.py" % n)
        if not os.path.exists(p):
            continue
        filled = open(p, encoding="utf-8", errors="replace").read().replace("K.NEED", "1.0")
        out = io.StringIO()
        keep = sys.stdout
        sys.stdout = out
        got = "ran to the end without touching the kernel"
        try:
            exec(compile(filled, p, "exec"), {"__name__": "__main__", "__file__": p})
        except AssertionError as e:
            got = str(e)
        except SystemExit:
            got = "STILL REFUSED: %s" % out.getvalue().strip().split("\n")[0][:50]
        except Exception as e:
            got = "%s: %s" % (type(e).__name__, str(e)[:60])
        finally:
            sys.stdout = keep
        ok = "was called BEFORE the refusal" in got
        print("  %-4s %-20s %s" % ("ok" if ok else "FAIL", "t_" + n, got))
        if not ok:
            FAILED.append("control t_" + n)

    print("\nAND THE REFUSAL SURVIVES A CONSOLE THAT DROPS SystemExit TEXT\n")
    _, text, code, _ = run_one(names[0], K)
    said = text.startswith("FAIL: ")
    print("  %-4s the reason is PRINTED, not carried on SystemExit" % ("ok" if said else "FAIL"))
    if not said:
        FAILED.append("printed")
    print("  %-4s ...and the exit code is 1" % ("ok" if code == 1 else "FAIL"))
    if code != 1:
        FAILED.append("exit 1")
    seen = [l for l in text.splitlines() if l.startswith("FAIL:")]
    print("  %-4s ...and `kit run` finds it by the `FAIL:` prefix it scans for"
          % ("ok" if seen else "FAIL"))
    if not seen:
        FAILED.append("FAIL: prefix")
    print("\n       the line it will echo:  kit run: the script REFUSED - %s"
          % (seen[0][6:].strip() if seen else "?"))

    print()
    if FAILED:
        print("%d FAILED: %s" % (len(FAILED), ", ".join(FAILED)))
        return 1
    print("all %d templates refuse on an unfilled block, before any kernel call." % len(names))
    print("\nNOT COVERED, and only the FreeCAD binary can show it: that `freecadcmd` flushes a")
    print("script's stdout before it dies. `K.fail` prints before raising for that reason, and")
    print("`kit run` sets its own exit code from the printed line rather than the interpreter's.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

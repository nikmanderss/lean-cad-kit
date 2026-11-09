#!/usr/bin/env python3
r"""selftest_psline.py — every case is a line that was actually handed to the client.

    & "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" "C:\CAD\LEAN_KIT\kit\selftest_psline.py"

the client, 2026-09-14: *"You are not instructing me correctly for powershell commands. Update whatever
needs to be so that doesn't happen again."* It is their most-repeated correction. It had been written
down as prose in `CONTRACT.md` since 2026-09-09 and agents kept getting it wrong anyway, so the
rule is now code — `leangate.psline()` generates the line and `leangate.pslint()` judges one — and
this is what keeps them honest.

**The case that matters is the last one: everything `psline()` produces passes `pslint()`.** A
generator whose own output fails its own checker would be worse than no generator, because it
would carry authority.

Needs no FreeCAD, no project and no network.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leangate as G

FAILED = []
PY = r"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe"
SCRIPT = r"C:\CAD\LEAN_KIT\hooks\selftest_wallclock.py"
PROJ = r"C:\CAD\Projects\MYPART"


def check(name, got, want):
    ok = (got == want)
    print("  %-4s %s" % ("ok" if ok else "FAIL", name))
    if not ok:
        print("        got  %r" % (got,))
        print("        want %r" % (want,))
        FAILED.append(name)


def faults(line):
    return sorted(w for w, _ in G.pslint(line))


def has(line, needle):
    return any(needle in w for w in faults(line))


def run():
    print("selftest_psline")
    G.PS_PY = PY

    bad = 'python "%s"' % SCRIPT
    check("bare `python` is caught", has(bad, "bare word `python`"), True)

    check("a quoted path with no `&` is caught",
          has('"%s" "%s"' % (PY, SCRIPT), "no `&`"), True)
    check("...and the same line WITH `&` is clean",
          faults('& "%s" "%s"' % (PY, SCRIPT)), [])

    routing = 'python LEAN_KIT\\install_lean_hooks.py --project "<the project folder>"'
    check("the routing document's own line has 3 faults", len(faults(routing)) >= 3, True)
    check("...bare python", has(routing, "bare word `python`"), True)
    check("...placeholder", has(routing, "placeholder"), True)
    check("...no absolute path", has(routing, "no absolute path"), True)

    check("a relative filename is caught", has("py install_hooks.py", "no absolute path"), True)

    check("a `^` continuation is caught", has('python "%s" ^' % SCRIPT, "ends with `^`"), True)
    check("a `\\` continuation is caught", has('& "%s" \\' % PY, "ends with `\\`"), True)
    check("a backtick continuation is caught", has('& "%s" `' % PY, "ends with a backtick"), True)

    check("`&&` is caught", has('cd "%s" && py x.py' % PROJ, "uses `&&`"), True)
    check("`;` is the right separator",
          faults('cd "%s"; & "%s" "%s"' % (PROJ, PY, SCRIPT)), [])

    check("a bash env prefix is caught",
          has('LK_P="crease=2.0" & "%s" "%s"' % (PY, SCRIPT),
              "environment variable the bash way"), True)

    check("%VAR% is caught", has('& "%s" "%%USERPROFILE%%\\x.py"' % PY, "%VAR%"), True)

    check("two lines are caught", has('& "%s" a\n& "%s" b' % (PY, PY), "more than one line"), True)

    for args in (
            (SCRIPT,),
            (SCRIPT, "--project", PROJ),
            (SCRIPT, "--project", PROJ, "--status"),
            (SCRIPT, "--says", "the seam is closed and the ridge is blended"),
            (SCRIPT, "--note", "a value with 'quotes' in it"),
    ):
        line = G.psline(*args, py=PY)
        check("psline%s passes its own lint" % (args[1:] or "",), faults(line), [])
    line = G.psline(SCRIPT, "status", py=PY, cwd=PROJ)
    check("psline(cwd=) passes its own lint", faults(line), [])
    check("psline(cwd=) uses `;` and not `&&`", "&&" in line, False)
    check("psline starts with the call operator", line.split(";")[1].strip()[0], "&")
    check("psline never emits the bare word python",
          G.psline(SCRIPT, py=PY).startswith("& \""), True)

    ps1 = G.psline(r"Q:\Some Folder\tidy.ps1")
    check("a .ps1 is called directly, with no interpreter",
          "python" not in ps1.lower() and ps1.startswith('& "'), True)
    check("...and it is still clean by psline's own checker", faults(ps1), [])
    ps1b = G.psline(r"Q:\Some Folder\tidy.ps1", "--go", cwd=r"Q:\Some Folder")
    check("args and cwd still work on a .ps1",
          ps1b.startswith('cd "Q:\\Some Folder"; & "') and ps1b.endswith("--go"), True)
    check("a .py still gets the interpreter's full path",
          ".exe" in G.psline(SCRIPT).lower(), True)

    check("...and the same line on the current root is clean",
          faults('& "%s" "%s"' % (PY, SCRIPT)), [])

    print("")
    if FAILED:
        print("%d FAILED: %s" % (len(FAILED), ", ".join(FAILED)))
        return 1
    print("all cases pass. Generate lines with `kit ps`; never type one.")
    return 0


if __name__ == "__main__":
    sys.exit(run())

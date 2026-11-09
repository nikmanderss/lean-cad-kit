#!/usr/bin/env python3
"""selftest_burrito.py - `kit burrito`, the orchestrator's runner for the chain, driven end to end.

    & python "C:\\CAD\\LEAN_KIT\\kit\\selftest_burrito.py"

No FreeCAD: KIT_FREECAD points the runner at this Python, and the "job scripts" are three-line
Python files that behave the way the real chain does at the boundary the kit can see - they read
LK_* variables, write a status_<tag>.json, print a FAIL: line, or take too long. Everything else
(the levers census, the budget from WALL_CLOCKS.md, the tag rule, the refusal on a lever nothing
reads, the FAIL: echo, the red flag) is the real code path, through the real command line.

WHY THIS FILE EXISTS. The burrito ran outside every kit gate until 2026-09-17 because the kit's only
runner was the WORKER's, and the chain breaks every worker rule on purpose. `kit burrito` is the
orchestrator's runner. A runner nobody has driven is the dead-guard class (a recorded process failure).
"""
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, "kit.py")
sys.path.insert(0, HERE)
import leangate as G

FAILED = []


def check(label, cond, detail=""):
    print("  %-4s %s" % ("ok" if cond else "FAIL", label))
    if not cond:
        print("       %s" % str(detail)[:300])
        FAILED.append(label)


def kit(root, *args, extra_env=None):
    env = dict(os.environ)
    env["KIT_PROJECT"] = root
    env["KIT_FREECAD"] = sys.executable
    if extra_env:
        env.update(extra_env)
    p = subprocess.run([sys.executable, KIT] + list(args), capture_output=True, text=True, env=env,
                       cwd=os.path.join(root, "claude_code"))
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    root = tempfile.mkdtemp(prefix="burrito_")
    os.makedirs(os.path.join(root, ".claude"), exist_ok=True)
    cc = os.path.join(root, "claude_code")
    job = os.path.join(cc, "jobs", "BUR")
    os.makedirs(job, exist_ok=True)
    bank = os.path.join(root, "model", "bank")
    os.makedirs(bank, exist_ok=True)
    mor = os.path.join(bank, "R1.brep")
    open(mor, "w", encoding="utf-8").write("stub")
    G.session_open(root, True, True, "STATE.md: R1 is the model of record",
                   {"overlap": "0.5 mm into material, 2 mm clear in air",
                    "measure": "the orchestrator measures; workers only render",
                    "punch": "never through the far side; the card states the far limit, e.g. stops 3 mm short"},
                   mor)

    open(os.path.join(job, "job_fields_dump.py"), "w", encoding="utf-8").write(
        'import os, json\n'
        'tag = os.environ.get("LK_TAG", "")\n'
        'alpha = float(os.environ.get("LK_ALPHA", "0.5"))\n'
        'beta = os.environ.get("LK_BETA", "x")\n'
        'print("probe raw 100 bound 1000")\n'
        'json.dump({"tag": tag, "alpha": alpha, "beta": beta}, open("status_probe%s.json" % tag, "w"))\n')
    open(os.path.join(job, "job_bad.py"), "w", encoding="utf-8").write(
        'import os\nold = os.environ.get("LK_OLDKNOB", "3")\nprint("FAIL: the card is not filled")\nraise SystemExit(1)\n')
    open(os.path.join(job, "job_slow.py"), "w", encoding="utf-8").write(
        'import os, time\nprint(os.environ.get("LK_TAG"))\ntime.sleep(2.5)\n')
    with open(os.path.join(job, "WINNING_ENV.json"), "w", encoding="utf-8") as fh:
        json.dump({"LK_ALPHA": "2.0", "LK_UNREAD": "1"}, fh)
    with open(os.path.join(cc, "WALL_CLOCKS.md"), "w", encoding="utf-8") as fh:
        fh.write("# TYPICAL\n\n## The table\n\n| job | typical | samples (s) | red flag at 1.5x | notes |\n"
                 "|---|---|---|---|---|\n| `job_fields_dump.py` | **1 s** | 1 | **2 s** | |\n"
                 "| `job_slow.py` | **1 s** | 1 | **2 s** | |\n")

    print("\nKIT BURRITO - the orchestrator's runner, end to end\n")

    rc, out = kit(root, "burrito", "--help")
    check("--help lists the chain's steps", "s3" in out and "job_fields_dump.py" in out and "s7r" in out, out[-300:])

    rc, out = kit(root, "burrito", "s3", "--job", "BUR")
    check("no --tag is REFUSED, with the reason", rc != 0 and "LK_TAG" in out, out[-300:])

    rc, out = kit(root, "burrito", "s3", "--job", "BUR", "--tag", "T1", "--set", "LK_NOPE=1")
    check("--set naming a lever nothing reads is REFUSED", rc != 0 and "LK_NOPE" in out and "reads" in out, out[-300:])

    rc, out = kit(root, "burrito", "s3", "--job", "BUR", "--tag", "T1", "--plan")
    check("--plan exits 0 and runs nothing", rc == 0 and "nothing was run" in out and not os.path.exists(os.path.join(job, "status_probeT1.json")), out[-400:])
    check("...it names the levers this script reads, set and defaulted",
          "LK_ALPHA" in out and "LK_BETA" in out and "default" in out, out[-600:])
    check("...the budget comes from the living WALL_CLOCKS.md", "WALL_CLOCKS.md" in out, out[-400:])
    check("...and s3 prints the burrito's card-time traps", "THE WALLS ARE THE CARD" in out, out[-800:])

    rc, out = kit(root, "burrito", "s3", "--job", "BUR", "--tag", "T1", "--set", "LK_BETA=y")
    st = os.path.join(job, "status_probeT1.json")
    check("a real step runs to rc 0 through the real command line", rc == 0, out[-400:])
    check("...the settings file, --set and --tag all reached the script",
          os.path.exists(st) and json.load(open(st)) == {"tag": "T1", "alpha": 2.0, "beta": "y"},
          (open(st).read() if os.path.exists(st) else "no status file"))
    check("...and the status file it wrote is named", "status_probeT1.json" in out, out[-300:])
    check("...the log is in the job folder, tagged", os.path.exists(os.path.join(job, "log_job_fields_dump_T1.txt")))

    rc, out = kit(root, "burrito", "job_bad.py", "--job", "BUR", "--tag", "T2")
    check("a FAIL: line is echoed as a refusal and the rc is non-zero", rc != 0 and "REFUSED" in out and "card is not filled" in out, out[-300:])

    rc, out = kit(root, "burrito", "job_slow.py", "--job", "BUR", "--tag", "T3")
    check("a step over 1.5x its typical is flagged, not hidden", "RED FLAG" in out, out[-300:])

    rc, out = kit(root, "burrito", "s3", "--job", "BUR", "--tag", "T4", "--bg")
    time.sleep(1.5)
    check("--bg starts it detached and puts it ON THE CLOCK", rc == 0 and "ON THE CLOCK" in out and "kit collected" in out, out[-300:])
    check("...and the detached step still ran", os.path.exists(os.path.join(job, "status_probeT4.json")))

    rc, out = kit(root, "burrito", "s9", "--job", "BUR", "--tag", "T5")
    check("an unknown step is refused by name", rc != 0 and "not a step" in out, out[-200:])

    # raw fuse
    open(os.path.join(job, "job_h_fuseparts.py"), "w", encoding="utf-8").write('import Part\nu = a.fuse(b)\nprint("fused")\n')
    rc, out = kit(root, "burrito", "job_h_fuseparts.py", "--job", "BUR", "--tag", "T5", "--plan")
    check("a non-chain script with a raw fuse is REFUSED before it runs, naming B.union and s7",
          rc != 0 and "raw fuse" in out and "B.union" in out and "s7" in out, out[-300:])
    open(os.path.join(job, "job_h_union.py"), "w", encoding="utf-8").write('import kitlib_burrito as B\nu, failed = B.union(shapes)\n')
    rc, out = kit(root, "burrito", "job_h_union.py", "--job", "BUR", "--tag", "T5", "--plan")
    check("...the same script through B.union is allowed", rc == 0 and "nothing was run" in out, out[-300:])
    open(os.path.join(job, "job_s7_replace.py"), "w", encoding="utf-8").write('import Part\nres = body.fuse(piece)\n')
    rc, out = kit(root, "burrito", "s7", "--job", "BUR", "--tag", "T5", "--plan")
    check("...and the chain's own S7, which fuses by design, is not refused for it", rc == 0 and "raw fuse" not in out, out[-300:])

    open(os.path.join(job, "job_features_burrito.py"), "w", encoding="utf-8").write(
        'import os\nedits = os.environ.get("LK_EDITS", "")\nops = os.environ.get("LK_MESH_OPS", "")\nprint("built")\n')
    rc, out = kit(root, "burrito", "s5", "--job", "BUR", "--tag", "T8", "--plan")
    check("a FIRST S5 for a tag says nothing about S6", rc == 0 and "RE-RUN" not in out, out[-300:])
    open(os.path.join(job, "status_featuresT8.json"), "w", encoding="utf-8").write('{"state": "done"}')
    rc, out = kit(root, "burrito", "s5", "--job", "BUR", "--tag", "T8", "--plan")
    check("an S5 RE-RUN with no LK_EDITS / LK_MESH_OPS is named as a rebuild, not a rework (L28)",
          rc == 0 and "RE-RUN" in out and "L28" in out, out[-400:])
    rc, out = kit(root, "burrito", "s5", "--job", "BUR", "--tag", "T8", "--plan", "--set", "LK_EDITS=L0_0@blend:1,2,3,4")
    check("...and with a rework edit set it is not", rc == 0 and "RE-RUN" not in out, out[-300:])

    rc, out = kit(root, "burrito", "s3", "--job", "BUR", "--tag", "T6", "--plan")
    check("before any census: the EXAMPLE CASE banner prints for WINNING_ENV.json and nothing is refused",
          rc == 0 and "EXAMPLE CASE" in out and "census" not in out, out[-400:])
    rc, out = kit(root, "levers", job, "--census")
    cen = os.path.join(job, "LEVERS_CENSUS.md")
    check("kit levers --census writes LEVERS_CENSUS.md with one row per lever", rc == 0 and os.path.exists(cen)
          and "| `LK_ALPHA` |" in open(cen, encoding="utf-8").read() and "| `LK_BETA` |" in open(cen, encoding="utf-8").read(), out[-300:])
    txt = open(cen, encoding="utf-8").read()
    check("...the example file's keys are marked, a lever it does not set is not", "| yes | " in txt.split("LK_ALPHA")[1].split("\n")[0]
          and "| no | " in txt.split("LK_BETA")[1].split("\n")[0], txt[-400:])
    _row = txt.split("`LK_OLDKNOB`")[1].split("\n")[0]
    check("...a lever read by no chain script (job_bad.py's LK_OLDKNOB) is marked 'in chain: no' with its reader named, class left BLANK - the census proposes nothing",
          "| no | no |  |" in _row and "read only outside the chain (job_bad.py)" in _row, _row)
    rc, out = kit(root, "levers", job, "--check")
    check("--check before classifying exits 1 and lists what is to classify", rc == 1 and "to classify" in out, out[-300:])
    rc, out = kit(root, "burrito", "s3", "--job", "BUR", "--tag", "T6", "--plan")
    check("an unclassified census PRINTS what is unclassified for this step and does not refuse",
          rc == 0 and "not yet classified" in out and "LK_BETA" in out, out[-400:])
    txt = txt.replace("| `LK_ALPHA` |", "| `LK_ALPHA` |").replace("| yes |  |", "| yes | CARD |", 1)
    lines = []
    for l in txt.splitlines(True):
        if l.startswith("| `LK_BETA` |"):
            c = l.split("|"); c[6] = " CARD "; c[7] = " the smoothing this card wants "; l = "|".join(c)
        elif l.startswith("| `LK_ALPHA` |"):
            c = l.split("|"); c[6] = " CARD "; l = "|".join(c)
        elif l.startswith("| `LK_TAG` |"):
            c = l.split("|"); c[6] = " CONSTANT "; c[7] = " the run's own tag, set by kit burrito "; l = "|".join(c)
        elif l.startswith("| `LK_OLDKNOB` |"):
            c = l.split("|"); c[6] = " DEAD "; l = "|".join(c)
        elif l.startswith("| `LK_EDITS` |") or l.startswith("| `LK_MESH_OPS` |"):
            # to classify
            c = l.split("|"); c[6] = " CARD "; c[7] = " the rework this card wants; empty is a rebuild (L28) "; l = "|".join(c)
        lines.append(l)
    open(cen, "w", encoding="utf-8").write("".join(lines))
    rc, out = kit(root, "levers", job, "--check")
    check("--check after classifying exits 0 and names the CARD lever the example does not set (BETA)",
          rc == 0 and "NOT set by it" in out and "LK_BETA" in out and "to classify:" not in out, out[-400:])
    rc, out = kit(root, "burrito", "s3", "--job", "BUR", "--tag", "T7", "--plan")
    check("a CARD lever the run does not set is REFUSED by name", rc != 0 and "REFUSED" in out and "LK_BETA" in out and "CARD" in out, out[-400:])
    rc, out = kit(root, "burrito", "s3", "--job", "BUR", "--tag", "T7", "--plan", "--set", "LK_BETA=z")
    check("...and --set of that lever lets the step run", rc == 0 and "nothing was run" in out, out[-300:])
    open(os.path.join(job, "job_fields_dump.py"), "a", encoding="utf-8").write('gamma = os.environ.get("LK_GAMMA", "7")\n')
    rc, out = kit(root, "levers", job, "--census")
    txt = open(cen, encoding="utf-8").read()
    check("re-running --census keeps every class given and adds the new lever unclassified",
          "| CARD |" in txt.split("LK_BETA")[1].split("\n")[0] and "the smoothing this card wants" in txt
          and "| `LK_GAMMA` |" in txt and "1 new row" in out, out[-300:])

    print("\nB.union - the piece-to-piece union names the piece that will not join\n")
    import types
    for _m in ("FreeCAD", "Part", "kitlib_render"):
        _mod = types.ModuleType(_m)
        if _m == "FreeCAD":
            _mod.Vector = lambda *a: a
        sys.modules.setdefault(_m, _mod)
    import kitlib_burrito as B

    class Shape(object):
        """A fake solid: a volume, a validity, a badness that fails a fuse in EITHER position (the
        kernel does not care which side a broken piece is on), and no BoundBox - so `reach` is off."""
        def __init__(self, vol, valid=True, name="s", bad=False):
            self.Volume = vol; self._valid = valid; self.name = name; self.bad = bad
        @property
        def Solids(self):
            return [self] if self.Volume > 0 else []
        def isValid(self):
            return self._valid
        def fuse(self, other, tol=None):
            bad = getattr(other, "bad", False) or getattr(self, "bad", False)
            if bad == "null":
                return None
            if bad == "raise":
                raise RuntimeError("BOPAlgo failed")
            if bad == "collapse":
                return Shape(1.0, name=self.name + "+" + other.name)
            if bad == "invalid":
                return Shape(self.Volume + other.Volume, valid=False)
            return Shape(self.Volume + other.Volume, name=self.name + "+" + other.name)

    u, failed = B.union([Shape(10, name="a"), Shape(20, name="b"), Shape(30, name="c")])
    check("three good pieces join into one, nothing failed", u is not None and u.Volume == 60 and failed == [], (u and u.Volume, failed))
    u, failed = B.union([Shape(10, name="a"), Shape(20, name="b", bad="null"), Shape(30, name="c")])
    check("a piece the kernel returns Null for is NAMED by index and the others still join (no order saves it)",
          u is not None and u.Volume == 40 and failed == [(1, "null or invalid")], (u and u.Volume, failed))
    u, failed = B.union([Shape(10, name="a"), Shape(20, name="b", bad="collapse")])
    check("a fuse whose volume collapses is refused as a join and says the numbers",
          u.Volume == 10 and len(failed) == 1 and "collapsed" in failed[0][1], failed)
    u, failed = B.union([Shape(10, name="a"), Shape(20, name="b", bad="raise"), None, Shape(0, name="z")])
    check("a raise, a None and an empty shape are each named, not swallowed",
          u.Volume == 10 and sorted(i for i, _ in failed) == [1, 2, 3] and any("raised" in w for _, w in failed), failed)
    u, failed = B.union([])
    check("nothing to join -> (None, [])", u is None and failed == [])

    import io, contextlib
    class BB(object):
        def __init__(self, x0, x1):
            self.XMin, self.XMax, self.YMin, self.YMax, self.ZMin, self.ZMax = x0, x1, 0.0, 10.0, 0.0, 10.0

    class Boxed(Shape):
        def __init__(self, vol, x0, x1, name="s", cut_by_vane=False):
            Shape.__init__(self, vol, name=name)
            self.x0, self.x1, self.cut_by_vane = x0, x1, cut_by_vane
        @property
        def BoundBox(self):
            return BB(self.x0, self.x1)
        def fuse(self, other, tol=None):
            # UNCHANGED
            if self.cut_by_vane and "vane" in other.name:
                return Boxed(self.Volume, self.x0, self.x1, name=self.name, cut_by_vane=True)
            r = Boxed(self.Volume + other.Volume, min(self.x0, other.x0), max(self.x1, other.x1),
                      name=self.name + "+" + other.name)
            r.cut_by_vane = ("core" in self.name or "core" in other.name) and ("vane" in self.name or "vane" in other.name)
            return r

    L = Boxed(1400, -27.0, -10.0, name="vaneL"); C = Boxed(4000, -11.5, 11.5, name="core"); R = Boxed(1400, 10.0, 27.0, name="vaneR")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        u, failed = B.union([L, C, R], label="a section")
    check("L-C-R would drop the right vane; union finds the order that reaches everywhere",
          u is not None and failed == [] and u.Volume == 6800 and u.BoundBox.XMax == 27.0, (u and u.Volume, failed, buf.getvalue()[-200:]))
    check("...and SAYS the given order lost a piece and which order was used", "given order lost a piece" in buf.getvalue(), buf.getvalue()[-200:])
    with contextlib.redirect_stdout(buf):
        u, failed = B.union([L, C, R], reorder=False)
    check("with reorder off, the drop is still CAUGHT by the reach check, not passed as a success",
          any(i == -1 and "reach:" in w and "x stops" in w for i, w in failed), failed)
    check("...and reach_short names the axis and the numbers", B.reach_short(u, [L, C, R]) == ["x stops 11.50 short of 27.00"], B.reach_short(u, [L, C, R]))
    check("reach_short is [] when the union reaches", B.reach_short(Boxed(1, -27.0, 27.0), [L, C, R]) == [])
    six = [Boxed(10, float(i), float(i) + 2, name="p%d" % i) for i in range(6)]
    with contextlib.redirect_stdout(buf):
        u, failed = B.union(six)
    check("six pieces: no permutation search (cap is five), the given order is used", u is not None and u.Volume == 60 and failed == [])

    class Solid(Boxed):
        def isInside(self, p, tol, on):
            return self.x0 <= p[0] <= self.x1 and 0.0 <= p[1] <= 10.0 and 0.0 <= p[2] <= 10.0
    vane = Solid(1400, -27.0, -10.0, name="vane"); core = Solid(4000, -11.5, 11.5, name="core"); far = Solid(1, 40.0, 50.0, name="far")
    with contextlib.redirect_stdout(buf):
        r = B.shared(vane, core)
    check("shared() counts the sampled points inside both and boxes them",
          r["in_a"] == 9 * 18 * 18 and r["shared"] == 18 * 18 and r["box"] is not None and abs(r["box"][0] + 10.0) < 1e-9, {k: v for k, v in r.items() if k != "points"})
    with contextlib.redirect_stdout(buf):
        r = B.shared(vane, far)
    check("...and says none when there are none", r["shared"] == 0 and r["box"] is None and r["frac"] == 0.0)
    try:
        B.shared(vane, core, n=(30, 30, 30)); over = False
    except ValueError as e:
        over = "27000 points" in str(e) and "budget" in str(e)
    check("a grid over the 12,000-point budget is refused with the number, not killed at the cap", over)
    class Multi(Shape):
        def fuse(self, others, tol=None):
            if isinstance(others, list):
                if any(getattr(o, "bad", False) for o in others):
                    return None
                return Shape(self.Volume + sum(o.Volume for o in others))
            return Shape.fuse(self, others, tol)
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = B._fuse_all([Multi(10, name="a"), Shape(20, name="b", bad="null"), Shape(30, name="c")])
    check("_fuse_all still returns the multi-fuse's (Null) result - the build's behaviour is unchanged", r is None)
    check("...but it now says WHICH piece would not join", "#1 (null or invalid)" in buf.getvalue(), buf.getvalue()[-300:])
    with contextlib.redirect_stdout(buf):
        r = B._fuse_all([Multi(10, name="a"), Shape(20, name="b"), Shape(30, name="c")])
    check("a multi-fuse that succeeds is returned as before, with no diagnostic", r is not None and r.Volume == 60)

    rc, out = kit(root, "howto", "burrito")
    check("kit howto burrito prints HOW IT ACTUALLY RUNS and copies NO template",
          rc == 0 and "HOW IT ACTUALLY RUNS" in out and "no template copied" in out
          and not os.path.exists(os.path.join(cc, "w_burrito.py")), out[-300:])

    print()
    if FAILED:
        print("%d FAILED: %s" % (len(FAILED), ", ".join(FAILED)))
        return 1
    print("all cases pass. The chain now has a runner that passes through the kit.")
    print("\nNOT COVERED, and only the binary can: that freecadcmd honours the environment and the cwd the")
    print("way this Python did. The real chain's own scripts already read KIT_HOME and LK_* this way.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

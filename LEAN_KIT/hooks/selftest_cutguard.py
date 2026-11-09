#!/usr/bin/env python3
"""selftest_cutguard.py - THE CUT-JOB RULES, DRIVEN THE WAY THE HARNESS DRIVES THEM.

Run it with the kit's interpreter (the full path to python.exe; the bare word is not it on Windows) from anywhere. No FreeCAD, no Claude Code, no project:

    & python "C:\\CAD\\LEAN_KIT\\hooks\\selftest_cutguard.py"

WHY IT RUNS `guard.py` AS A SUBPROCESS INSTEAD OF IMPORTING IT. `guard.py` is a script: it reads a
JSON payload from stdin at module level and signals its verdict with an EXIT CODE (2 = deny). There
is no function to call. Importing it would prove nothing about the thing that actually runs, and on
2026-09-16 the thing that actually runs turned out to be a file that did not parse - for two days,
in total silence, because a hook that dies at parse time exits non-zero with a traceback and that is
not exit code 2. **So this drives the real file, over stdin, and reads the real exit code.**

WHAT IT PINS. The cut rules refuse a METHOD, never an operation. the client, on the first over-blunt fuse
block: *"that breaks a lot of edits. That needs to be fixed."* A cut is never refused on its own -
every cross-section, profile and sectioned orbit frame is a cut. The distinguisher is THE SAVE: a
script that cuts a loaded body **and writes the result out** is a material-removal job; one that
cuts in order to LOOK discards it.

The four cases below are the ones the client flagged as needing a live test when the `cutter` type was
specified. They were written on 2026-09-16 and the sandbox died before they could run, so they are
recorded here rather than left in a scratch folder.

**IF A CASE FAILS BECAUSE THE RULE IS TOO BLUNT, NARROW `_is_cut_job` - NEVER LOOSEN WHAT THE RULES
SAY.** A refusal you believe is wrong is a `kit failure` finding, not an edit.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(HERE, "guard.py")
FAILED = []

CASES = [
    ("a_cutter_from_a_face", True, """
import kitlib as K
body = K.load("b.brep")
w = body.Faces[1239].OuterWire          # the cutter's outline taken from the part's own face
tool = w.extrude(FreeCAD.Vector(0, 0, 25))
res = body.cut(tool)
K.save(res, "result.brep")
"""),
    ("b_cross_section_only", False, """
import kitlib as K
body = K.load("b.brep")
slab = K.box(-100, 100, -100, 100, 40, 41)
sect = body.cut(slab)                   # cuts in order to LOOK, and never saves
print(len(sect.Faces), sect.Faces[0].OuterWire)
"""),
    ("c_boundbox_as_a_measurement", True, """
import kitlib as K
body = K.load("b.brep")
bb = body.BoundBox                      # measuring with a box that lies on NURBS
tool = K.box(bb.XMin, bb.XMax, -10, 10, 0, 25)
res = body.cut(tool)
res.exportBrep("result.brep")
"""),
    ("d_a_properly_drawn_cut", False, """
import kitlib as K
body = K.load("b.brep")
segs = [K.connect(a, b, c, d) for a, b, c, d in stations]   # drawn from a measured table
tool = segs[0]
for s in segs[1:]:
    tool = K.fuse(tool, s)
res = K.cut(body, [tool], "cutter")
K.save(res, "result.brep")
"""),
    ("e_boundbox_to_select_only", False, """
import kitlib as K
body = K.load("b.brep")
for i, f in enumerate(body.Faces):
    bb = f.BoundBox                     # selecting, not measuring; nothing is saved
    if bb.ZMin > 40:
        print(i + 1, f.Area)
"""),
]


def _run(payload):
    p = subprocess.run([sys.executable, GUARD], input=json.dumps(payload),
                       capture_output=True, text=True)
    said = (p.stderr or p.stdout or "").strip().split("\n")
    return p.returncode, (said[0][:96] if said and said[0] else "")


def ask(root, src, name):
    """(exit code, first line of what it said). Exit 2 is a refusal."""
    return _run({"tool_name": "Write", "cwd": root,
                 "tool_input": {"file_path": os.path.join(root, "claude_code", "jobs", "J0", name), "content": src}})


_BARE_PY = re.compile(r"(^|[;&|(\s])python3?(?=\s)")


def ask_bash(root, command):
    """The guard's Bash branch, driven the way the harness drives it. The cases below spell the interpreter as the
    bare word `python` for brevity; since 2026-09-25 the guard refuses that word on Windows (it is the Microsoft
    Store stub on the client's machine - lessons F3, hooks\\selftest_guard.py has that case), so the bare word is replaced by
    this interpreter's full path before the command is judged - every case here tests some OTHER rule."""
    command = _BARE_PY.sub(lambda m: m.group(1) + '"' + sys.executable + '"', command)
    return _run({"tool_name": "Bash", "cwd": root, "tool_input": {"command": command}})


def ask_edit(root, name, old, new):
    """The same question asked the way an Edit asks it. `_body` is `new_string` - THE CHANGED TEXT
    ONLY, never the whole file - so an edit that touches no banned spelling is not a cut job at all,
    however the file around it reads. This is the difference between the real workflow and the way
    the synthetic cases above are posed, and on 2026-09-16 the kit maintainer reported an alarm having tested
    only the latter."""
    return _run({"tool_name": "Edit", "cwd": root,
                 "tool_input": {"file_path": os.path.join(root, "claude_code", "jobs", "J0", name),
                                "old_string": old, "new_string": new}})


def main():
    if not os.path.exists(GUARD):
        print("selftest_cutguard: no guard.py beside this file (%s)" % GUARD)
        return 1
    root = tempfile.mkdtemp(prefix="cutguard_")
    os.makedirs(os.path.join(root, ".claude"), exist_ok=True)
    os.makedirs(os.path.join(root, "claude_code", "jobs", "J0"), exist_ok=True)
    try:
        print("\nTHE CUT-JOB RULES - refusing a METHOD, never an operation\n")
        for name, must_refuse, src in CASES:
            code, said = ask(root, src, name + ".py")
            refused = code == 2
            ok = refused == must_refuse
            print("  %-4s %-30s %s" % ("ok" if ok else "FAIL", name,
                                       "REFUSED" if refused else "allowed"))
            if refused:
                print("       %s" % said)
            if not ok:
                print("       EXPECTED %s" % ("a refusal" if must_refuse else "it to be allowed"))
                FAILED.append(name)

        # kit howto <type>
        # METHOD.md  recorded
        print("\nTHE SANCTIONED ROUTE - `kit howto` copies, the agent fills PARAMS\n")
        tpl = os.path.join(os.path.dirname(HERE), "kit", "templates", "t_cutter.py")
        if os.path.exists(tpl):
            with open(tpl, encoding="utf-8", errors="replace") as fh:
                body = fh.read()
            shutil.copy(tpl, os.path.join(root, "claude_code", "jobs", "J0", "w_cutter.py"))
            print("  ok   %-30s %s" % ("howto copies the template",
                                       "no tool call, so no hook - on disk unread"))
            filled = ('PARAMS = dict(\n'
                      '    base="/abs/region.brep",\n'
                      '    out_dir="/abs/jobs/CUT1",\n'
                      '    why_not_delete="the plate is fused to the vane; deleting leaves it open",\n'
                      '    find=dict(normal=(0, 0, -1), tol_deg=10.0, within=(15, 45, -2, 16, 5, 30)),\n'
                      ')')
            for name, must_refuse, how in (
                    ("filling PARAMS with an Edit", False, "edit"),
                    ("HAND-TYPING the template", True, "write")):
                if how == "edit":
                    code, said = ask_edit(root, "w_cutter.py", "PARAMS = dict(", filled)
                else:
                    code, said = ask(root, body, "w_cutter.py")
                refused = code == 2
                ok = refused == must_refuse
                print("  %-4s %-30s %s" % ("ok" if ok else "FAIL", name,
                                           "REFUSED" if refused else "allowed"))
                if not ok:
                    print("       EXPECTED %s" % ("a refusal" if must_refuse else "it to be allowed"))
                    FAILED.append(name)
        else:
            print("  (skipped - no t_cutter.py beside this kit)")

        print("\nFILTERING THE KIT'S OUTPUT - every shell's spelling\n")
        _PY = r'"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe"'
        _K = r'"C:\CAD\LEAN_KIT\kit\kit.py"'
        for label, must_refuse, cmd in (
                ("| Select-String  (PowerShell)", True, "& %s %s status | Select-String FAIL"),
                ("| sls            (its alias)", True, "& %s %s status | sls FAIL"),
                ("| Select-Object  (its head)", True, "& %s %s status | Select-Object -First 20"),
                ("| more", True, "& %s %s status | more"),
                ("| head           (bash)", True, "& %s %s status | head -5"),
                ("| findstr        (cmd)", True, "& %s %s status | findstr FAIL"),
                ("--brief, the sanctioned quiet mode", False, "& %s %s status --brief"),
                ("--brief WITH a filter (refused since 2026-09-17)", True,
                 "& %s %s status --brief | Select-String FAIL"),
                ("| tee log | tail   (the filter is the SECOND pipe)", True,
                 "& %s %s burrito s5 --tag T | tee claude_code/jobs/J0/run.log | tail -20"),
                ("| sed -n           (a line-selector)", True, "& %s %s burrito s5 --tag T | sed -n '1,40p'"),
                ("| grep -v          (an inverse match)", True, "& %s %s burrito s5 --tag T 2>&1 | grep -v leangate"),
                ("| Out-Null         (swallows everything)", True, "& %s %s burrito s5 --tag T | Out-Null"),
                ("| Where-Object     (PowerShell line filter)", True, "& %s %s status | Where-Object { $_ -match 'FAIL' }"),
                ("| tee alone        (passes everything through)", False, "& %s %s burrito s5 --tag T | tee claude_code/jobs/J0/run.log"),
                ("a pipe in a LATER command is not the kit's output", False,
                 "& %s %s status; git log | head -3"),
                ("a pipe INSIDE a quoted argument is prose (L246)", False,
                 "& %s %s failure --what \"the grep | head issue\" --why x --fix y --signature z")):
            code, said = ask_bash(root, cmd % (_PY, _K))
            refused = code == 2
            ok = refused == must_refuse
            print("  %-4s %-38s %s" % ("ok" if ok else "FAIL", label,
                                       "REFUSED" if refused else "allowed"))
            if not ok:
                FAILED.append(label)
        for label, cmd in (("a non-kit command piped", "git status | head -5"),
                           ("reading a file with head", "head -5 claude_code/INBOX.md"),
                           ("grep on the kit's SOURCE piped to head", "grep -n 'def cmd_' %s kitlib_render.py | head -20" % _K),
                           ("a sed expression is not a path", "sed -i 's/old/new/g' claude_code/jobs/J1/CARD.md"),
                           ("timeout on the kit itself", "timeout 600 %s %s status --as-orchestrator" % (_PY, _K))):
            code, said = ask_bash(root, cmd)
            ok = code != 2
            print("  %-4s %-38s %s" % ("ok" if ok else "FAIL", label,
                                       "allowed" if ok else "REFUSED - too blunt"))
            if not ok:
                print("       said=%s" % said)
                FAILED.append(label)

        print("\nWHERE A NEW FILE LANDS - PROJECT_LAYOUT.md, gated\n")
        _cc = os.path.join(root, "claude_code"); os.makedirs(os.path.join(_cc, "jobs", "J1", "work"), exist_ok=True)
        os.makedirs(os.path.join(_cc, "CC_FINISH"), exist_ok=True)
        os.makedirs(os.path.join(root, "Deliverables", "R31", "review"), exist_ok=True)
        with open(os.path.join(_cc, "STATE_NOW.md"), "w") as _fh: _fh.write("# state\n")
        with open(os.path.join(root, "PROJECT_FACTS.md"), "w") as _fh: _fh.write("# facts\n")

        def ask_write(path, src="x\n", tool="Write"):
            if tool == "Write":
                return _run({"tool_name": "Write", "cwd": root, "tool_input": {"file_path": path, "content": src}})
            return _run({"tool_name": "Edit", "cwd": root, "tool_input": {"file_path": path, "old_string": "a", "new_string": src}})
        for label, path, must_refuse in (
                ("a NEW note loose in claude_code\\", os.path.join(_cc, "NOTES_FOR_KIT.md"), True),
                ("a NEW handover loose in claude_code\\", os.path.join(_cc, "HANDOVER_2026-09-24.md"), True),
                ("a NEW file at the project root", os.path.join(root, "EveryTime_I_Didnt_Listen.md"), True),
                ("a NEW script loose in claude_code\\", os.path.join(_cc, "_state_upd.py"), True),
                ("a NEW script in a round folder", os.path.join(_cc, "CC_FINISH", "probe.py"), True),
                ("a NEW file in an unnamed folder", os.path.join(_cc, "notes", "x.md"), True),
                ("a job's script                     (allowed)", os.path.join(_cc, "jobs", "J1", "job_probe.py"), False),
                ("a job's file at depth              (allowed)", os.path.join(_cc, "jobs", "J1", "work", "REVIEW.md"), False),
                ("a round's brief                    (allowed)", os.path.join(_cc, "CC_FINISH", "BRIEF.md"), False),
                ("the first STATE_NOW.md             (allowed)", os.path.join(_cc, "STATE_NOW.md"), False),
                ("a register that does not exist yet (allowed)", os.path.join(_cc, "MEASUREMENTS.md"), False),
                ("an EXISTING root file by hand (refused - 31bz R3 F2)", os.path.join(root, "PROJECT_FACTS.md"), True),
                ("a new PROJECT_FACTS.md in a new project (allowed)", os.path.join(root, "SESSION_DEFAULTS.md"), False),
                ("a picture for the client                   (allowed)", os.path.join(root, "Deliverables", "R31", "review", "a.png"), False),
                ("a dossier file                     (allowed)", os.path.join(_cc, "dossier", "spine", "sections.json"), False)):
            rc, said = ask_write(path)
            refused = rc == 2
            ok = refused == must_refuse
            print("  %-4s %-56s %s" % ("ok" if ok else "FAIL", label, "REFUSED" if refused else "allowed"))
            if not ok:
                print("       rc=%s said=%s" % (rc, said))
                FAILED.append("placement: " + label)
        rc, said = ask_write(os.path.join(_cc, "STATE_NOW.md"), "more", "Edit")
        ok = rc != 2
        print("  %-4s %-56s %s" % ("ok" if ok else "FAIL", "an Edit is never judged by placement", "allowed" if ok else "REFUSED"))
        if not ok: FAILED.append("placement: edit")
        for label, cmd, must_refuse in (
                ("a heredoc to a new loose note", "cat > claude_code/CC_TWO_METHODS.md << 'EOF'\nhello\nEOF", True),
                ("a redirect into a job folder      (allowed)", "echo hi > claude_code/jobs/J1/log.txt", False),
                ("an append to an existing register (allowed)", "echo row >> claude_code/STATE_NOW.md", False),
                ("tee to a new root file", "python x.py | tee IM_A_DUMMY.md", True)):
            rc, said = _run({"tool_name": "Bash", "cwd": root, "tool_input": {"command": cmd}})
            refused = rc == 2
            ok = refused == must_refuse
            print("  %-4s %-56s %s" % ("ok" if ok else "FAIL", label, "REFUSED" if refused else "allowed"))
            if not ok:
                print("       rc=%s said=%s" % (rc, said))
                FAILED.append("placement(bash): " + label)

        print("\nLAUNCHER PREFIXES, KILLS BY PATTERN, BARE BACKGROUNDS\n")
        for label, must_refuse, cmd in (
                ("timeout 600 FreeCAD.exe            (a launcher prefix)", True,
                 "timeout 600 \"C:/Program Files/FreeCAD 1.1/bin/FreeCAD.exe\" _guiload.py"),
                ("nice -n 10 freecadcmd", True, "nice -n 10 freecadcmd job.py"),
                ("VAR=1 timeout 10 freecadcmd", True, "CC_X=1 timeout -k 5 10 freecadcmd job.py"),
                ("pkill -f", True, "pkill -f '_ccthin.py'"),
                ("taskkill /IM", True, "taskkill /F /IM freecadcmd.exe"),
                ("Get-Process | Stop-Process", True,
                 "Get-Process freecadcmd | Where-Object { $_.CommandLine -match 'thin' } | Stop-Process -Force"),
                ("Stop-Process -Name", True, "Stop-Process -Name freecadcmd -Force"),
                ("kill by pid                        (allowed)", False, "kill 12345"),
                ("taskkill /PID                      (allowed)", False, "taskkill /T /F /PID 12345"),
                ("a bare trailing &", True, "python3 long_probe.py > probe.log 2>&1 &"),
                ("a chain with &&                    (allowed)", False, "ls && echo done"),
                ("2>&1 redirect                      (allowed)", False, "python3 x.py > claude_code/jobs/J0/x.log 2>&1"),
                ("prose mentioning pkill in a quoted arg (allowed)", False,
                 "%s %s failure --what \"agent used pkill -f\" --why x --fix y --signature z" % (_PY, _K))):
            code, said = ask_bash(root, cmd)
            refused = code == 2
            ok = refused == must_refuse
            print("  %-4s %-56s %s" % ("ok" if ok else "FAIL", label, "REFUSED" if refused else "allowed"))
            if not ok:
                print("       rc=%s said=%s" % (code, said))
                FAILED.append(label)

        # does not exist
        # resolved against
        print("\nTHE INLINE ONE-LINER'S PATHS - refuse the escape, allow the work\n")
        for label, must_refuse, cmd in (
                ("'\\n'.join to a relative file", False,
                 r"""python -c "import io; io.open('out.txt','w').write('\n'.join(['a']))" """),
                ("'\\t'.join, printing only", False,
                 r"""python -c "print('\t'.join(['a','b']))" """),
                ("a nested relative write", False,
                 r"""python -c "open('sub/dir/notes.txt','w').write('x')" """),
                ("relative, windows separators", False,
                 r"""python -c "open(r'jobs\J1\r.brep','w').write('x')" """),
                ("a read, with no write intent", False,
                 r"""python -c "print(open('x.txt').read())" """),
                ("2>/dev/null", False, r"""python -c "print(1)" 2>/dev/null"""),
                ("..\\.. escaping the project", True,
                 r"""python -c "open(r'..\..\x.txt','w').write('x')" """),
                ("..\\\\..\\\\ - a raw string's doubled separators", True,
                 r"""python -c "open(r'..\\..\\x.txt','w').write('x')" """),
                ("../../ escaping the project", True,
                 r"""python -c "open('../../x.txt','w').write('x')" """),
                ("an absolute path outside", True,
                 r"""python -c "open(r'C:\Windows\evil.txt','w').write('x')" """),
                ("/etc/passwd", True, r"""python -c "open('/etc/passwd','w').write('x')" """),
                ("the kit's own guard", True,
                 r"""python -c "open(r'C:\CAD\LEAN_KIT\hooks\guard.py','w').write('x')" """)):
            code, _said = ask_bash(root, cmd)
            refused = code == 2
            ok = refused == must_refuse
            print("  %-4s %-44s %s" % ("ok" if ok else "FAIL", label,
                                       "REFUSED" if refused else "allowed"))
            if not ok:
                FAILED.append("inline path: " + label)

        print("\nTHE SHELL WRITE - the content rules apply to a .py written from Bash, by any spelling\n")
        jobs = os.path.join(root, "claude_code", "jobs")
        jq = (lambda f_: '"%s/%s"' % (jobs, f_) if " " in jobs else "%s/%s" % (jobs, f_))
        cases = [
            ("a heredoc that writes a raw fuse into a .py",
             "cat > %s <<'EOF'\nimport Part\nu = a.fuse(b)\nEOF" % jq("job_h_fuseparts.py"), True),
            ("a python -c one-liner that appends a raw fuse to a .py",
             "python -c \"open(r'%s/job_h_fuseparts.py','a').write('    cand = u.fuse(nxt)\\n')\"" % jobs, True),
            ("a python - heredoc that opens a .py for writing and writes a raw fuse",
             "python - <<'PY'\np=r'%s/job_x.py'\ns=open(p).read().replace('# fuse here','    u = u.fuse(nxt, TOL)')\nopen(p,'w').write(s)\nPY" % jobs, True),
            ("sed -i that lands a raw fuse in a .py",
             "sed -i 's/# fuse here/u = u.fuse(nxt)/' %s" % jq("job_x.py"), True),
            ("PowerShell Set-Content of a raw fuse into a .py",
             "Set-Content -Path '%s/job_x.py' -Value 'r = a.fuse(b)'" % jobs, True),
            ("the SAME heredoc writing B.union (the kit's checked pairwise union) is fine",
             "cat > %s <<'EOF'\nimport kitlib_burrito as B\nu, failed = B.union(shapes)\nEOF" % jq("job_h_fuseparts.py"), False),
            ("a heredoc writing K.fuse (the kit's bookkept fuse) is fine",
             "cat > %s <<'EOF'\nimport kitlib as K\nres = K.fuse(body, piece)\nEOF" % jq("job_ok.py"), False),
            ("a report that QUOTES a raw fuse and writes nothing is prose (L246)",
             "python kit.py failure --what \"job_h_fuseparts.py:58 has u.fuse( and was run\" --why x --fix y --signature z", False),
            ("grep for a raw fuse is reading, not writing",
             "grep -n 'u.fuse(' %s" % jq("job_h_fuseparts.py"), False),
            ("a raw fuse written into a .md (a note, not a script) is not a script",
             "cat >> %s <<'EOF'\nthe old code did u.fuse(nxt) here\nEOF" % jq("../claude_code/NOTES.md"), False),
        ]
        for label, cmd, must_refuse in cases:
            rc, said = ask_bash(root, cmd)
            refused = rc == 2
            ok = refused == must_refuse and (not refused or "FUSE" in said.upper())
            print("  %-4s %-78s %s" % ("ok" if ok else "FAIL", label, "REFUSED" if refused else "allowed"))
            if not ok:
                print("       rc=%s said=%s" % (rc, said))
                FAILED.append("shell write: " + label)

        # PRIOR ART
        print("\nTHE PRIOR-ART GATE - a new job script in a crowded folder names what it applies\n")
        big = os.path.join(root, "claude_code", "jobs", "BIG")
        os.makedirs(big, exist_ok=True)
        for i in range(20):
            open(os.path.join(big, "job_old%02d.py" % i), "w").write("# old\n")
        small = os.path.join(root, "claude_code", "jobs", "SMALL")
        os.makedirs(small, exist_ok=True)
        for i in range(3):
            open(os.path.join(small, "job_s%d.py" % i), "w").write("# old\n")

        def ask_write(path, src, tool="Write"):
            payload = {"tool_name": tool, "cwd": root, "tool_input": {"file_path": path, "content": src}}
            if tool == "Edit":
                payload["tool_input"] = {"file_path": path, "old_string": "x", "new_string": src}
            return _run(payload)

        pa_cases = [
            ("a new job_*.py naming none of the twenty", os.path.join(big, "job_new.py"),
             "# LK - the three-card split\nimport os\nprint(1)\n", "Write", True),
            ("...the same naming job_old03.py in its header", os.path.join(big, "job_new.py"),
             "# LK - applies job_old03.py's generation, split out so kit burrito runs it\nimport os\n", "Write", False),
            ("...the same saying PRIOR ART", os.path.join(big, "job_new.py"),
             "# PRIOR ART: none of the twenty does this; see RESULT.md\nimport os\n", "Write", False),
            ("...the same saying no prior art", os.path.join(big, "job_new.py"),
             "# no prior art - a new subject\nimport os\n", "Write", False),
            ("a new job_*.py in a folder of three", os.path.join(small, "job_new.py"),
             "# LK - fresh\nimport os\n", "Write", False),
            ("an Edit to an existing script is not gated", os.path.join(big, "job_old01.py"),
             "print(2)\n", "Edit", False),
            ("a helper that is not job_*.py is not gated", os.path.join(big, "lk_helper.py"),
             "import os\n", "Write", False),
        ]
        for label, path, src, tool, must_refuse in pa_cases:
            rc, said = ask_write(path, src, tool)
            refused = rc == 2
            ok = refused == must_refuse and (not refused or "PRIOR ART" in said.upper() or "NAMES NONE" in said.upper())
            print("  %-4s %-78s %s" % ("ok" if ok else "FAIL", label, "REFUSED" if refused else "allowed"))
            if not ok:
                print("       rc=%s said=%s" % (rc, said))
                FAILED.append("prior art: " + label)

        print("\nTHE REAL SCRIPTS, if this kit sits beside the part project\n")
        proj = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                            "My Projects", "MYPART", "claude_code", "jobs", "BURRITO")
        real = [("job_facecut.py", True), ("job_platecut.py", True),
                ("job_sect_compare.py", False), ("job_s7_crop.py", False)]
        seen = 0
        for fn, must_refuse in real:
            p = os.path.join(proj, fn)
            if not os.path.exists(p):
                continue
            seen += 1
            with open(p, encoding="utf-8", errors="replace") as fh:
                code, said = ask(root, fh.read(), fn)
            refused = code == 2
            ok = refused == must_refuse
            print("  %-4s %-30s %s" % ("ok" if ok else "FAIL", fn,
                                       "REFUSED" if refused else "allowed"))
            if not ok:
                FAILED.append(fn)
        if not seen:
            print("  (skipped - the project is not beside this kit; the synthetic cases above")
            print("   cover the same rules and are the ones that must pass)")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print()
    if FAILED:
        print("%d FAILED: %s" % (len(FAILED), ", ".join(FAILED)))
        print("\nIf a refusal here is too blunt, narrow `_is_cut_job` in guard.py.")
        print("Do NOT weaken what the rules say, and do not reword a script to get past one.")
        return 1
    print("all cases pass. The method is refused; the instrument is not.")
    print("\nNOT COVERED, and only a live session can show it: that a PreToolUse hook's exit-2")
    print("stderr reaches the agent rather than being swallowed. See the kit's development record 2026-09-14.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

import os, re, sys, json, shutil, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import guard as g

FAILED = []


def check(label, cond, detail=""):
    print("  %-4s %s" % ("ok" if cond else "FAIL", label))
    if not cond:
        print("       %s" % str(detail)[:500])
        FAILED.append(label)


PYX = '"%s"' % sys.executable
_BARE_PY = re.compile(r"(^|[;&|(\s])python3?(?=\s)")


def run(root, command, cwd=None, background=False):
    command = _BARE_PY.sub(lambda m: m.group(1) + PYX, command)
    inp = {"command": command}
    if background:
        inp["run_in_background"] = True
    j = json.dumps({"tool_name": "Bash", "tool_input": inp, "cwd": cwd or root})
    p = subprocess.run([sys.executable, os.path.join(HERE, "guard.py")], input=j, capture_output=True, text=True, cwd=root)
    return p.returncode, (p.stderr or "") + (p.stdout or "")


def main():
    try:
        tmp = tempfile.mkdtemp(prefix="kitguard_", dir=os.path.expanduser("~"))
    except OSError:
        tmp = tempfile.mkdtemp(prefix="kitguard_")
    root = os.path.join(tmp, "proj")
    for d in (".claude", "claude_code/jobs/J1", "claude_code/CC_ROUND", "Deliverables/R35/model"):
        os.makedirs(os.path.join(root, d), exist_ok=True)
    open(os.path.join(root, "Deliverables", "R35", "README.md"), "w").write("x")
    open(os.path.join(root, "claude_code", "jobs", "J1", "notes.md"), "w").write("x")
    J1 = os.path.join(root, "claude_code", "jobs", "J1")
    try:
        print("\nGUARD - the 2026-09-25 rules\n")
        print("[1] A RELATIVE TARGET AFTER `cd` IS JUDGED AGAINST THAT DIRECTORY (K1)")
        rc, out = run(root, 'cd "%s" && echo hi > chain_FP_run1.txt' % J1)
        check("cd <job folder> && echo > rel.txt is ALLOWED (it lands in the job folder)", rc == 0, out[-400:])
        rc, out = run(root, "echo hi > chain_FP_run1.txt", cwd=os.path.join(root, "claude_code"))
        check("...while the same relative redirect from claude_code\\ itself is still refused as loose", rc == 2 and "LOOSE" in out, out[-300:])
        rc, out = run(root, 'cd "%s" && python3 -c "print(1)" > log.txt' % os.path.join(root, "claude_code", "CC_ROUND"))
        check("cd <round folder> && ... > log.txt is allowed", rc == 0, out[-300:])

        print("\n[2] sed -i JUDGES ITS FILE OPERANDS, NEVER THE EXPRESSION (K2)")
        rc, out = run(root, 'sed -i "s/old/new/g" "%s"' % os.path.join(J1, "notes.md"))
        check("sed -i s/a/b/ <file in a job> is allowed", rc == 0, out[-400:])
        check("_sed_operands drops the expression and options", g._sed_operands(["sed", "-i", "s/a/b/g", "x.md", "y.md"]) == ["x.md", "y.md"]
              and g._sed_operands(["sed", "-i", "-e", "s/a/b/", "z.md"]) == ["z.md"], g._sed_operands(["sed", "-i", "s/a/b/g", "x.md"]))
        rc, out = run(root, 'sed -i "s/a/b/" "%s"' % os.path.join(root, "Deliverables", "R35", "README.md"))
        check("...and sed -i on a protected file is still refused", rc == 2 and "protected path" in out, out[-300:])

        print("\n[3] SHELL VARIABLES IN A TARGET (K2)")
        rc, out = run(root, 'D="%s"; echo 1 > $D/out.txt' % J1)
        check("a variable assigned in the same command is expanded and judged (allowed here)", rc == 0, out[-400:])
        rc, out = run(root, "echo 1 > $D/out.txt")
        check("an unresolved $VAR in a write target is refused WITH THE RULE, not as an unnamed folder",
              rc == 2 and "SHELL VARIABLE" in out and "unnamed folder" not in out, out[-400:])
        rc, out = run(root, 'OUT="%s"; echo 1 > $OUT' % os.path.join(tmp, "elsewhere.txt"))
        check("...and a variable that resolves OUTSIDE the project is refused as outside", rc == 2 and "OUTSIDE THE PROJECT" in out, out[-300:])

        print("\n[4] A BARE `&` ANYWHERE, AND A KILL BY NAME (K3)")
        for c in ("(python3 x.py &) ; echo", "nohup python3 x.py & cd ..", "for i in 1 2; do python3 s.py $i & done", "python3 x.py &"):
            rc, out = run(root, c)
            check("refused: %s" % c, rc == 2 and "bare `&`" in out, out[-200:])
        for c in ("python3 x.py 2>&1 | tee %s" % os.path.join(J1, "log.txt"), "a && b", "a || b", "python3 x.py >&2", 'echo "a & b"'):
            rc, out = run(root, c)
            check("allowed: %s" % c, rc == 0, out[-200:])
        for c in ("taskkill /F /IM python.exe", "taskkill //F //IM python.exe", "pkill python", "killall FreeCADCmd", "Stop-Process -Name python"):
            rc, out = run(root, c)
            check("kill by name refused: %s" % c, rc == 2 and "NAME" in out, out[-200:])
        rc, out = run(root, "taskkill /T /F /PID 1234")
        check("a kill by pid is allowed", rc == 0, out[-200:])

        print("\n[5] THE FILTER RULE EXEMPTS INFORMATIONAL KIT CALLS (K4)")
        kp = os.path.join(root, "kit.py"); kpr = kp
        if " " in kp: kp = '"%s"' % kp
        for c in ("python3 %s exam | head -20" % kp, "python3 %s atlas --help | sed -n 1,5p" % kp,
                  "python3 %s help crop | head" % kp, "python3 %s howto cutter | head -40" % kp):
            rc, out = run(root, c)
            check("allowed: %s" % c.split("kit.py ")[-1], rc == 0, out[-300:])
        rc, out = run(root, "python3 %s status | grep FAIL" % kp)
        check("...but `kit status | grep` stays refused (its output carries the wardens' state)", rc == 2 and "filter" in out, out[-300:])
        rc, out = run(root, "python3 %s check J1 --as-orchestrator | grep -v banner" % kp)
        check("...while filtering a GATED command's output is still refused", rc == 2 and "filter" in out, out[-300:])

        print("\n[6] A FOREGROUND WAIT IS REFUSED; run_in_background IS THE WAY (T1)")
        for c in ("until grep -q DONE log.txt; do sleep 15; done", "while true; do sleep 5; done", "sleep 120", "for i in 1 2 3; do sleep 30; done"):
            rc, out = run(root, c)
            check("refused: %s" % c, rc == 2 and "WAIT in the foreground" in out, out[-200:])
        rc, out = run(root, "until grep -q DONE log.txt; do sleep 15; done", background=True)
        check("...the same loop with run_in_background is allowed", rc == 0, out[-300:])
        rc, out = run(root, "sleep 5; python3 x.py")
        check("a short sleep is allowed", rc == 0, out[-300:])
        rc, out = run(root, "timeout 300 python3 x.py")
        check("a `timeout` prefix is not a sleep", rc == 0, out[-300:])

        print("\n[7] THE UNLOCK IN THE SAME COMMAND, RELATIVE OR ABSOLUTE (K22)")
        draft = os.path.join(J1, "README_draft.md"); open(draft, "w").write("d")
        prot = os.path.join(root, "Deliverables", "R35", "README.md")
        rc, out = run(root, 'echo 1 > .claude/unlock && cp "%s" "%s" && rm .claude/unlock' % (draft, prot))
        check("relative unlock -> write -> rm, from the project root, is allowed", rc == 0, out[-400:])
        rc, out = run(root, 'echo 1 > "%s" && cp "%s" "%s" && rm "%s"' % (os.path.join(root, ".claude", "unlock"), draft, prot, os.path.join(root, ".claude", "unlock")))
        check("absolute unlock -> write -> rm is allowed too", rc == 0, out[-400:])
        rc, out = run(root, 'echo 1 > .claude/unlock && cp "%s" "%s" && rm .claude/unlock' % (draft, prot), cwd=os.path.join(root, "claude_code"))
        check("...from claude_code\\ the relative unlock lands in claude_code\\.claude\\ - refused (the write stays protected)", rc == 2, out[-400:])
        rc, out = run(root, 'echo 1 > .claude/unlock && cp "%s" "%s"' % (draft, prot))
        check("an unlock that is never removed is refused", rc == 2 and "never removes it" in out, out[-300:])
        rc, out = run(root, 'cp "%s" "%s"' % (draft, prot))
        check("the protected write alone is still refused", rc == 2 and "protected path" in out, out[-300:])

        print("\n[9] THE KIT NAMED THROUGH THE ENVIRONMENT, A SUBSTITUTION OR AN UNRESOLVED VARIABLE (31bq R6b, B50 rest)")
        os.environ["KIT_R6B_T"] = kpr
        try:
            for c in ("python3 $KIT_R6B_T rebuild skin-build --job X | tail -5", "python3 ${KIT_R6B_T} status | grep FAIL",
                      "python3 $(cygpath -w %s) rebuild skin-wires --job X | tail" % kp, 'python3 "$(cygpath -w \'%s\')" ruling --find x | head' % kpr,
                      "python3 `cygpath -w %s` inbox | tail" % kp, "python3 $KIT_R6B_T run job.py | tail"):
                rc, out = run(root, c)
                check("refused: %s" % c.replace(kp, "<kit.py>"), rc == 2 and "filter" in out, out[-300:])
            rc, out = run(root, "python3 $(cygpath -w %s) rebuild skin-wires --job X | tail" % kp)
            _fx = next((l for l in out.splitlines() if "THE CORRECTED COMMAND" in l), "")
            check("...the corrected command of the substitution form is the literal kit path, no `$(`, balanced quotes", "$(" not in _fx and "kit.py" in _fx and _fx.count('"') % 2 == 0 and "--brief" in _fx, _fx)
            for c in ("python3 $UNSET_R6B_X myarg | tail", "python3 $UNSET_R6B_X run | tail", "python3 $(cygpath -w x.py) rebuild | tail",
                      "python3 $KIT_R6B_T exam | head", "echo $UNSET_R6B_KIT rebuild | tail",
                      "python3 $UNSET_R6B_KIT ruling --find nothing | tail", "$PY $UNSET_R6B_KIT rebuild skin-build | tail -3",
                      "T=/q/x/tool.py; python3 $T check --all | tail -3"):
                rc, out = run(root, c)
                check("allowed: %s" % c, rc == 0, out[-300:])
        finally:
            os.environ.pop("KIT_R6B_T", None)

        print("\n[10] THE KIT INSIDE A SHELL COMPOUND OR A CAPTURE (31bq R7b - verify-R6's replay of 4037 real the agent commands: the real 2026-10-01 form passed both guards)")
        for c in ("for i in 1 2; do python3 %s rebuild skin-build --job X | tail -5; done" % kp,
                  "if true; then python3 %s status | grep FAIL; fi" % kp,
                  "{ python3 %s inbox | tail; }" % kp,
                  "( python3 %s inbox | tail )" % kp,
                  "out=$(python3 %s rebuild arrange --job X 2>&1); rc=$?; echo \"$out\" | grep -v '^  job '" % kp,
                  "for i in 1 2 3; do out=$(python3 %s rebuild arrange --job X 2>&1); rc=$?; echo \"$out\" | grep -v '^  job '; echo \"rc=$rc\"; done" % kp,
                  "out=$(python3 %s status); grep -q DEAD <<< \"$out\" && echo dead" % kp,
                  "if python3 %s check J1 --as-orchestrator | grep -q FAIL; then echo bad; fi" % kp,
                  "for i in 1 2; do python3 %s status; done | tail -3" % kp,
                  "{ python3 %s inbox; } | grep -v banner" % kp):
            rc, out = run(root, c)
            check("refused: %s" % c.replace(kp, "<kit.py>"), rc == 2 and "filter" in out, out[-300:])
        rc, out = run(root, "out=$(python3 %s rebuild arrange --job X 2>&1); echo \"$out\" | grep -v '^  job '" % kp)
        check("...the capture's refusal names the variable and gives the kit call as THE CORRECTED COMMAND with --brief", "CAPTURED into $out" in out and "rebuild arrange --job X" in out and "--brief" in out, out[-500:])
        for c in ("for f in a b; do grep -n kit.py \"$f\" | head; done",
                  "out=$(ls); echo \"$out\" | grep x",
                  "out=$(python3 %s exam); echo \"$out\" | head -20" % kp,
                  "out=$(python3 %s status); echo \"$out\"" % kp,
                  "out=$(python3 %s status); echo \"$out\" | tee %s" % (kp, os.path.join(J1, "status.log")),
                  "for i in 1 2; do python3 %s status; done" % kp,
                  "( cd \"%s\" && echo hi > chain_R7b_x.txt )" % J1,
                  "(cd \"%s\" && echo hi > chain_R7b_y.txt)" % J1):
            rc, out = run(root, c)
            check("allowed: %s" % c.replace(kp, "<kit.py>"), rc == 0, out[-300:])
        print("\n[11] EVERY KIT CALL OF THE LINE IS JUDGED (31br D12 (e) - the agent's JOB3: `kit inbox --append ... && kit inbox --brief | head -3` ran)")
        for c in ("python3 %s inbox --append --from X --text hi && python3 %s inbox --brief 2>&1 | head -3" % (kp, kp),
                  "python3 %s status; python3 %s rebuild skin-build --job X | tail -5" % (kp, kp),
                  "python3 %s exam && python3 %s check J1 --as-orchestrator | grep FAIL" % (kp, kp)):
            rc, out = run(root, c)
            check("refused (the second call's filter): %s" % c.replace(kp, "<kit.py>"), rc == 2 and "filter" in out, out[-300:])
        for c in ("python3 %s inbox --append --from X --text hi && python3 %s inbox --brief" % (kp, kp),
                  "python3 %s exam | head -5 && python3 %s howto burrito | head -20" % (kp, kp)):
            rc, out = run(root, c)
            check("allowed (no filter on a kit call, or reference calls only): %s" % c.replace(kp, "<kit.py>"), rc == 0, out[-300:])
        for c in ("python3 %s status |& tail -5" % kp, "python3 %s inbox | (head -5)" % kp, "python3 %s inbox | { head -5; }" % kp,
                  "tail -3 <(python3 %s status)" % kp, "grep -q FAIL <(python3 %s check J1 --as-orchestrator) && echo bad" % kp,
                  "python3 -X utf8 %s rebuild skin-build --job X | tail" % kp, "python3 -W ignore %s status | grep DEAD" % kp):
            rc, out = run(root, c)
            check("refused: %s" % c.replace(kp, "<kit.py>"), rc == 2 and "filter" in out, out[-300:])
        for c in ("for i in 1 2; do python3 %s tool look_at --job X --set BOX=1; done | grep -v DONE" % kp,
                  "tail -3 <(python3 %s exam)" % kp, "out=$(python3 %s howto burrito); echo \"$out\" | head" % kp):
            rc, out = run(root, c)
            check("allowed: %s" % c.replace(kp, "<kit.py>"), rc == 0, out[-300:])
        rc, out = run(root, "for i in 1 2; do python3 %s rebuild skin-build --job X 2>&1 | tail -5; done" % kp)
        _fx = next((l for l in out.splitlines() if "THE CORRECTED COMMAND" in l), "")
        check("...the corrected command of a loop body starts with the interpreter (no `do`) and puts --brief before the redirection", _fx.split(":", 1)[-1].strip().split()[:1] != ["do"] and "--brief 2>&1" in _fx, _fx)
        _bash = shutil.which("bash")
        if _bash:
            _bad = []
            for c in ("for i in 1 2; do python3 %s rebuild skin-build --job X 2>&1 | tail -5; done" % kp, "python3 $(cygpath -w %s) rebuild skin-wires --job X | tail" % kp,
                      "out=$(python3 %s rebuild arrange --job X 2>&1); echo \"$out\" | grep -v x" % kp, "python3 %s rebuild skin-build --job X | tail -5" % kp):
                rc, out = run(root, c); _fx = next((l for l in out.splitlines() if "THE CORRECTED COMMAND" in l), "").split(":", 1)[-1].strip()
                _p = subprocess.run([_bash, "-n", "-c", _fx], capture_output=True, text=True)
                if _p.returncode != 0: _bad.append((c[:60], _fx[:120], _p.stderr.strip()[:80]))
            check("every corrected command parses under `bash -n` (D2: the (b) form had an unbalanced paren)", not _bad, _bad)
        rc, out = run(root, "for i in 1; do FreeCADCmd x.py; done")
        check("a FreeCAD launch inside a loop body is refused (the keyword is no shield)", rc == 2 and "FreeCAD runs only" in out, out[-300:])
        rc, out = run(root, 'for i in 1; do rm -rf "%s"; done' % os.path.join(tmp, "elsewhere"))
        check("a delete outside the project inside a loop body is refused", rc == 2 and "OUTSIDE THE PROJECT" in out, out[-300:])
        check("_strip_prefix drops the shell keywords and a glued paren", g._strip_prefix(["do", "python", "x.py"]) == ["python", "x.py"] and g._strip_prefix(["(cd", "dir"]) == ["cd", "dir"]
              and g._strip_prefix(["{", "timeout", "60", "X=1", "cmdx"]) == ["cmdx"] and g._strip_prefix(["then", "!", "grep", "x"]) == ["grep", "x"], g._strip_prefix(["{", "timeout", "60", "X=1", "cmdx"]))

        print("\n[11] 31bz - a RELATIVE write into the bank / a delivery's model\\ (R3 F11), an EXISTING file outside the two places (R3 F2), the quoted kit.py form (R7 F7)")
        CCb = os.path.join(root, "claude_code"); os.makedirs(os.path.join(CCb, "bank"), exist_ok=True); open(os.path.join(root, "CLAUDE.md"), "w").write("x")
        os.makedirs(os.path.join(root, "references"), exist_ok=True); open(os.path.join(root, "references", "spec.txt"), "w").write("x")
        for c_, cw_ in (("cp jobs/J1/notes.md bank/R09_BODY_MASTER.brep", CCb), ("echo x > ./bank/R09_BODY_MASTER.brep", CCb), ("cd claude_code && cp jobs/J1/notes.md bank/R09.brep", root),
                        ("echo x > Deliverables/R35/model/R35.FCStd", root)):
            rc, out = run(root, c_, cwd=cw_)
            check("31bz R3 F11: refused - %s (from %s)" % (c_, os.path.basename(cw_)), rc == 2 and "protected path" in out, out[-300:])
        for c_ in ("echo x > ../CLAUDE.md", "echo x >> ../references/spec.txt"):
            rc, out = run(root, c_, cwd=CCb)
            check("31bz R3 F2: refused - %s (an EXISTING file outside claude_code\\ / review\\ / renders\\)" % c_, rc == 2 and "AN EXISTING FILE OUTSIDE THE TWO PLACES" in out, out[-300:])
        for tl_ in ("Write", "Edit"):
            _ti = {"file_path": os.path.join(root, "CLAUDE.md"), "content": "x"} if tl_ == "Write" else {"file_path": os.path.join(root, "CLAUDE.md"), "old_string": "x", "new_string": "y"}
            p_ = subprocess.run([sys.executable, os.path.join(HERE, "guard.py")], input=json.dumps({"tool_name": tl_, "tool_input": _ti, "cwd": CCb}), capture_output=True, text=True, cwd=root)
            check("31bz R3 F2: the %s tool on the root's CLAUDE.md is refused" % tl_, p_.returncode == 2 and "AN EXISTING FILE OUTSIDE" in (p_.stderr + p_.stdout), (p_.stderr + p_.stdout)[-300:])
        rc, out = run(root, "echo x >> jobs/J1/notes.md", cwd=CCb)
        check("31bz R3 F2: an existing file in a job folder is still writable", rc == 0, out[-300:])
        rc, out = run(root, "echo 1 > .claude/unlock && echo x > CLAUDE.md && rm .claude/unlock", cwd=root)
        check("31bz R3 F2: the orchestrator's one-command unlock still edits the root file", rc == 0, out[-300:])
        _kq = os.path.join(root, "LK", "kit", "kit.py")
        for c_ in ('"%s" "%s" check r.brep --base b.brep' % (sys.executable, _kq), '& "%s" "%s" apply --job J1' % (sys.executable, _kq)):
            rc, out = run(root, c_, cwd=CCb)
            check("31bz R7 F7: the QUOTED kit.py form without --as-orchestrator is refused (%s)" % c_.split()[-3], rc == 2 and "orchestrator commands" in out, out[-300:])
        rc, out = run(root, '"%s" "%s" render b.brep --out jobs/J1/r' % (sys.executable, _kq), cwd=CCb)
        check("31bz R7 F7: ...and a quoted render (a worker's command) passes", rc == 0, out[-300:])

        print("\n[7b] A QUOTED .py TARGET WITH A SPACE (31cb H-F1, the route harness)")
        _sp = os.path.join(J1, "a b"); os.makedirs(_sp, exist_ok=True)
        rc, out = run(root, 'cat > "%s" <<\'EOF\'\nimport Part\nu = a.fuse(b)\nEOF' % os.path.join(_sp, "job_hf1.py"))
        check("a heredoc writing a raw fuse into a QUOTED .py path holding a space is REFUSED (the content rule ran)", rc == 2 and "RAW FUSE" in out, out[-300:])
        rc, out = run(root, 'echo "u = a.fuse(b)" >> "%s"' % os.path.join(_sp, "job_hf1b.py"))
        check("...and an append to such a path the same", rc == 2 and "RAW FUSE" in out, out[-300:])
        check("_PY_WRITE reads a quoted target with a space (> and tee)", bool(g._PY_WRITE.search('cat > "C:\\x y\\j.py" <<EOF')) and bool(g._PY_WRITE.search('python3 a.py | tee "C:\\x y\\j.py"')))

        print("\n[8] HELPERS")
        _os_name = g.os.name
        try:
            g.os.name = "nt"
            check("_drive turns a Git-Bash path into the Windows spelling (on Windows)", g._drive("/c/CAD/Projects/x.txt") == "C:/CAD/Projects/x.txt", g._drive("/c/CAD/Projects/x.txt"))
            check("...and leaves an ordinary rooted path alone", g._drive("/tmp/x") == "/tmp/x", g._drive("/tmp/x"))
            check("bare `python` is named as the Store stub on Windows", g.bare_python("python x.py") == "python", g.bare_python("python x.py"))
            check("...a full interpreter path is not", g.bare_python(r'"C:\Users\a\python.exe" x.py') is None)
        finally:
            g.os.name = _os_name
        check("_kit_info_call: exam / --help / howto are reference output", all(g._kit_info_call(x) for x in ("exam", "atlas --help", "howto cutter", "help crop")))
        check("...check / apply / mesh / status are not", not any(g._kit_info_call(x) for x in ("check J1", "apply J1", "mesh extract --job X", "status --brief")))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if FAILED:
        print("\n%d FAILED:" % len(FAILED))
        for f in FAILED:
            print("  - %s" % f)
        sys.exit(1)
    print("\nall cases pass. NOT COVERED, and only a live Claude Code session can show it: that the harness passes\n"
          "run_in_background in tool_input the way the docs say, and that a hook's exit-2 stderr reaches the agent.")


if __name__ == "__main__":
    main()

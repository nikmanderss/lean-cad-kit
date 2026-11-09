"""selftest_lookgate.py - LOOK BEFORE YOU MEASURE (kit 31am, 2026-10-06) and its 31aq teeth (2026-10-07), without a kernel.
the client, 2026-10-06: "For any step, in any process, the agent must be pushed to render review if a measurement is about to be taken
in the next step. It can be as little as 1 image for the generic push but it must be gated to be properly targeted at the
measurement subject in question."
the client, 2026-10-07: "the agent is editing and ALWAYS jumps to measurements before renders. Find a way to punish it ... Make it announce to me that
it's a silly dum dum every time it does that"; "It consistently gets to a good result off of renders + changes, makes a measurement that it
arbitrarily decides is a bad measurement with no reasoning as to why, and then undoes correct work. It has to stop."
Cases: what is a measurement (kit measure, measuring instruments, probe scripts by name or by their # MEASURES: header, any command
declaring # MEASURES:, kit atlas recreated; 31aq: python / freecadcmd scripts named like a measurement, inline python that measures) and
what is not; the subject box from every source; no subject -> refused with how to name it; the renderer's frame index + an opened picture
at the subject lets it through; a look elsewhere / a whole-body look at a small subject / an hour-old look / a picture with no frame record
does not. 31aq: a measurement with no look is a STRIKE - the wall of shame, the session locked (Read / Glob / Grep only) until the agent
echoes "silly dum dum"; the penance (1 + strikes pictures); # SAW and # WHY before any number; a lever build right after a measurement with
no picture since is a strike; the guard itself refuses, records, unlocks and lets through (a subprocess)."""
import os, sys, json, time, shutil, tempfile, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import lookgate as L
KIT = os.path.join(os.path.dirname(HERE), "kit"); sys.path.insert(0, KIT)
import kitlib_render as R
import numpy as np
ok = 0; bad = 0
def check(cond, what):
    global ok, bad
    if cond: ok += 1; print("  ok   " + what)
    else: bad += 1; print("  FAIL " + what)

root = tempfile.mkdtemp(prefix="lookgate_"); os.makedirs(os.path.join(root, ".claude")); os.makedirs(os.path.join(root, "claude_code", "jobs", "J"))
job = os.path.join(root, "claude_code", "jobs", "J")
PY = r'& "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" "C:\CAD\LEAN_KIT\kit\kit.py"'
V = np.array([[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 10]], float); T = np.array([[0, 1, 2], [0, 2, 3]])
def pic(name, scale=1.0, d=(-0.45, -0.45, -0.77)):
    p = os.path.join(job, "look", name); os.makedirs(os.path.dirname(p), exist_ok=True)
    R.render(p, [("s", V * scale, T, (0.8, 0.6, 0.4))], d, W=200, pad=1.0,
             focus=np.array([[x, y, z] for x in (0, 10) for y in (0, 10) for z in (0, 10)], float) * scale, title="t", edges=False)
    return p
def confess():
    st = L._dd_load(root); n = (st.get("owed") or {}).get("n", "?")
    return L.check(root, "Bash", {"command": 'echo "%s"' % L.apology(n, "the deed")}, job)
REASONS = "  # SAW: the yellow box frames the plate's corner and it is flat there   # WHY: the picture cannot say whether the gap is under 0.15 mm"
try:
    m = L.measurement(PY + " measure body.brep section y -117", job, root)
    check(m and m["box"] is None, "kit measure is a measurement; with no box it names no subject")
    m = L.measurement(PY + " measure body.brep section y -117 --box -10,10,-120,-110,70,90", job, root)
    check(m and m["box"] == [-10, 10, -120, -110, 70, 90], "--box x0,x1,... is its subject")
    m = L.measurement(PY + ' tool diag_section --job J --set "CC_WIN=-15 15 76 92" --set "CC_Y=-121 -119"', job, root)
    check(m and m["box"] == [-15, 15, -122, -118, 76, 92], "diag_section's subject from CC_WIN and CC_Y (got %r)" % (m and m["box"],))
    check(L.measurement(PY + ' tool look_at --job J --set "BOX=0 1 0 1 0 1"', job, root) is None, "look_at is the look, not a measurement")
    check(L.measurement(PY + " tool atlas_colour --job J", job, root) is None, "an instrument that does not measure is not gated")
    check(L.measurement(PY + " rebuild skin-build --job J --tag t", job, root) is None, "a step of a defined process is not gated here (its own judges gate it)")
    open(os.path.join(job, "job_skin_sp10_capprobe.py"), "w").write("print(1)\n")
    m = L.measurement(PY + " burrito job_skin_sp10_capprobe.py", job, root)
    check(m and m["box"] is None, "a probe script (by its name) is a measurement")
    open(os.path.join(job, "job_any.py"), "w").write("# job_any.py - an experiment\n# MEASURES: 1 2 3 4 5 6 - the gap under the lip\nprint(1)\n")
    m = L.measurement(PY + " burrito job_any.py", job, root)
    check(m and m["box"] == [1, 2, 3, 4, 5, 6] and "gap under the lip" in m["what"], "a script that declares # MEASURES: in its header is gated on that box")
    open(os.path.join(job, "job_skin_build2.py"), "w").write("print(1)\n")
    check(L.measurement(PY + " burrito job_skin_build2.py", job, root) is None, "a build script that declares nothing is not gated")
    m = L.measurement("echo measuring  # MEASURES: 0 10 0 10 0 10 - a test", job, root)
    check(m and m["box"] == [0, 10, 0, 10, 0, 10], "any command declaring # MEASURES: at its end is gated")
    json.dump({"regions": {"vanes": {"box": [-30, 30, -160, -90, 60, 100]}}}, open(os.path.join(root, "claude_code", "ATLAS.json"), "w"))
    m = L.measurement(PY + " atlas recreated vanes --result x.stl", job, root)
    check(m and m["box"] == [-30, 30, -160, -90, 60, 100], "kit atlas recreated <region>: the atlas region's box")
    open(os.path.join(job, "edge_dev_probe.py"), "w").write("print(1)\n")
    check(L.measurement('& "C:\\Python312\\python.exe" edge_dev_probe.py', job, root) is not None, "31aq: a python run of a script named like a measurement")
    check(L.measurement('python -c "import Part; s=Part.Shape(); print(s.Volume)"', job, root) is not None, "31aq: inline python that measures (.Volume)")
    check(L.measurement('python -c "import os; print(os.listdir())"', job, root) is None, "31aq: inline python that does not measure is let be")
    msg = L.check(root, "Bash", {"command": PY + " measure body.brep section y -117"}, job)
    check(msg and "does not say WHAT it measures" in msg and "# MEASURES:" in msg and "# SAW:" in msg and not L._dd_load(root)["strikes"],
          "no subject -> refused with how to name it (and the SAW / WHY it will need) - not a strike")
    cmd = "echo measuring  # MEASURES: 0 10 0 10 0 10 - a test" + REASONS
    msg = L.check(root, "Bash", {"command": cmd}, job)
    st = L._dd_load(root)
    note1 = L.USER_NOTE
    check(note1 and "WALL OF SHAME +1" in note1 and "Pretty please forgive Mr. Silly Dum Dum" in note1, "31au: the strike is SHOWN to the client as it lands (USER_NOTE)")
    check(msg and "look_at" in msg and "no picture was opened" in msg and "SILLY DUM DUM" in msg and "I'm a silly dum dum - I'm so very sorry! Pretty please forgive Mr. Silly Dum Dum" in msg,
          "no look -> refused AND a STRIKE: the sentence to say to the client")
    check(len(st["strikes"]) == 1 and st["owed"] and os.path.isfile(os.path.join(root, "claude_code", "DUMDUM.md"))
          and "strike" not in open(os.path.join(root, "claude_code", "DUMDUM.md")).read().split("|---|")[0][:0], "the strike is on the wall of shame (claude_code\\DUMDUM.md) and owed")
    check(L.check(root, "Edit", {"file_path": "x.py"}, job) and L.check(root, "Bash", {"command": "ls"}, job), "while it is owed every tool is refused ...")
    check(L.USER_NOTE is None, "31au: a strike already shown to the client is not shown again on every refused call")
    check(L.check(root, "Grep", {"pattern": "x"}, job) is None and L.check(root, "Read", {"file_path": os.path.join(job, "x.txt")}, job) is None, "... but Read / Glob / Grep")
    check(confess() is None and not L._dd_load(root)["owed"] and len(L._dd_load(root)["confessions"]) == 1, "the echo of 'silly dum dum' unlocks it (and is recorded)")
    check(L.USER_NOTE and "I'm a silly dum dum - I'm so very sorry! Pretty please forgive Mr. Silly Dum Dum" in L.USER_NOTE and "wall of shame" in L.USER_NOTE, "31au: the confession is SHOWN to the client as it is said (USER_NOTE -> the hook's systemMessage)")

    check(L.check(root, "Bash", {"command": "ls"}, job) is None, "after the confession ordinary commands run")
    p1 = pic("look_1.png")
    fr = [json.loads(l) for l in open(os.path.join(root, ".claude", "frames.jsonl"))]
    check(fr and fr[-1]["box"] == [0, 10, 0, 10, 0, 10], "the renderer indexes the box its picture frames")
    check(L.check(root, "Read", {"file_path": p1}, job) is None and L.frame_box(root, p1) == [0, 10, 0, 10, 0, 10], "opening the picture is recorded with its box")
    msg = L.check(root, "Bash", {"command": cmd}, job)
    check(msg and "PENANCE" in msg and "2 DIFFERENT pictures" in msg and len(L._dd_load(root)["strikes"]) == 1, "31aq PENANCE: one strike today -> two pictures of the subject (and no new strike for trying)")
    p2 = pic("look_2.png", d=(0.45, 0.45, 0.77)); L.check(root, "Read", {"file_path": p2}, job)
    msg = L.check(root, "Bash", {"command": "echo measuring  # MEASURES: 0 10 0 10 0 10 - a test"}, job)
    check(msg and "REASONS BEFORE NUMBERS" in msg, "31aq: no # SAW / # WHY -> refused: a number needs its reason first")
    msg = L.check(root, "Bash", {"command": "echo measuring  # MEASURES: 0 10 0 10 0 10 - a test  # SAW: flat  # WHY: because"}, job)
    check(msg and "REASONS BEFORE NUMBERS" in msg, "31aq: a SAW / WHY of a word or two is not a reason")
    check(L.check(root, "Bash", {"command": cmd}, job) is None and L.last_measure(root), "two pictures at the subject + SAW + WHY -> the measurement runs (and is recorded)")
    build = PY + " rebuild skin-build --job J --tag b7 --set LAM=2"
    msg = L.check(root, "Bash", {"command": build}, job)
    check(msg is None and len(L._dd_load(root)["strikes"]) == 1, "31bj: a lever build right after a looked-at measurement RUNS - look -> measure -> decide is the sequence (no strike; the client on the agent's strike 16)")
    check(L.check(root, "Bash", {"command": PY + " rebuild skin-build --job J --tag b7 --set STL=piece.stl"}, job) is None, "a build that changes no lever (paths only) is not a decision")
    time.sleep(0.05); L.check(root, "Read", {"file_path": p2}, job)
    check(L.check(root, "Bash", {"command": build}, job) is None, "a picture opened after the measurement -> the lever build runs")
    check(L.check(root, "Bash", {"command": PY + " rebuild judge --job J --what skin --verdict ok --note x"}, job) is None, "a judgement is not a build")
    msg = L.check(root, "Bash", {"command": "echo x  # MEASURES: 200 210 0 10 0 10 - elsewhere" + REASONS}, job)
    check(msg and "none of the" in msg, "a look elsewhere does not count"); confess()
    big = pic("whole.png", scale=40.0, d=(0, 0, -1)); L.check(root, "Read", {"file_path": big}, job)
    msg = L.check(root, "Bash", {"command": "echo x  # MEASURES: 100 102 100 102 0 2 - a 2 mm lip" + REASONS}, job)
    check(msg and "none of the" in msg, "a whole-body picture is not a look at a 2 mm subject"); confess()
    looks = [json.loads(l) for l in open(os.path.join(root, ".claude", "looks.jsonl"))]
    for r_ in looks: r_["opened"] -= 3600
    open(os.path.join(root, ".claude", "looks.jsonl"), "w").write("".join(json.dumps(r_) + "\n" for r_ in looks))
    msg = L.check(root, "Bash", {"command": cmd}, job)
    check(msg and "no picture was opened in the last" in msg, "a look an hour old does not count"); confess()
    other = os.path.join(job, "noindex.png"); open(other, "wb").write(b"png")
    L.check(root, "Read", {"file_path": other}, job)
    msg = L.check(root, "Bash", {"command": cmd}, job)
    check(msg and "no frame record" in msg, "a picture the kit's renderer did not make has no frame and does not count"); confess()
    check(len(L._dd_load(root)["strikes"]) == 5 and L.recent_strikes(L._dd_load(root)) == 5, "every strike counted (5)")
    sent_k = L.strike(root, "undo", "a layout judged ok, overturned on a number (made inside kit_rebuild)", "kit rebuild skin-labels ...")
    L.check(root, "Bash", {"command": "ls"}, job)
    check(L.USER_NOTE and "WALL OF SHAME +1" in L.USER_NOTE and L.pretties(6) + " please forgive" in L.USER_NOTE and "locked" in L.USER_NOTE, "31au: a strike made inside a kit process (an undo) is shown to the client at the next tool call")
    L.check(root, "Bash", {"command": "ls"}, job)
    check(L.USER_NOTE is None, "31au: ... once")
    confess()
    # RENDER DEFECTIVE
    lk_ = os.path.join(root, ".claude", "looks.jsonl"); keep_ = open(lk_, encoding="utf-8").read()
    with open(lk_, "a") as fh:
        for i_ in range(4):
            b_ = os.path.join(job, "look", "bad_%d.png" % i_)
            fh.write(json.dumps({"png": b_, "png_n": L._norm(b_), "box": [0, 10, 0, 10, 0, 10], "opened": time.time(), "defective": True}) + "\n")
    msg = L.check(root, "Bash", {"command": cmd}, job)
    check(msg and "RENDER DEFECTIVE" in msg and "4 picture(s) opened AT it" in msg, "31bn: four pictures AT the subject, all stamped RENDER DEFECTIVE - no look: refused, and the refusal says so"); confess()
    with open(lk_, "a") as fh:
        for i_ in range(4):
            g_ = os.path.join(job, "look", "good_%d.png" % i_)
            fh.write(json.dumps({"png": g_, "png_n": L._norm(g_), "box": [0, 10, 0, 10, 0, 10], "opened": time.time(), "defective": False}) + "\n")
    check(L.check(root, "Bash", {"command": cmd}, job) is None, "31bn: four sound pictures AT the subject -> the measurement runs")
    open(lk_, "w", encoding="utf-8").write(keep_)
    os.remove(os.path.join(root, ".claude", "dumdum.json"))
    G = os.path.join(HERE, "guard.py")
    OUT = {}
    def guard(tool, inp):
        p = subprocess.run([sys.executable, G], input=json.dumps({"tool_name": tool, "tool_input": inp, "cwd": job}), capture_output=True, text=True, timeout=60)
        OUT["stdout"] = p.stdout
        return p.returncode, p.stderr
    def shown():
        try: return json.loads(OUT.get("stdout") or "{}").get("systemMessage")
        except ValueError: return "NOT JSON: " + OUT.get("stdout", "")[:80]
    rc, err = guard("Bash", {"command": cmd})
    check(rc == 2 and "LOOK BEFORE YOU MEASURE" in err and "silly dum dum" in err.lower(), "the guard refuses the measurement before the look, with the strike (rc %s)" % rc)
    check(shown() and "WALL OF SHAME +1" in shown(), "31au: the guard's stdout is the hook JSON with the strike as its systemMessage, the client sees it now (%r)" % (shown() or "")[:60])
    rc, err = guard("Bash", {"command": "ls -la"})
    check(rc == 2 and "SILLY DUM DUM" in err, "the guard keeps the session locked until the confession (rc %s)" % rc)
    rc, err = guard("Bash", {"command": 'echo "%s"' % L.apology(1, "the deed")})
    check("SILLY DUM DUM" not in err, "the guard lets the confession through and unlocks (rc %s)" % rc)
    check(rc == 0 and shown() and "Pretty please forgive Mr. Silly Dum Dum" in shown(), "31au: ... and the client sees the confession as it is said (systemMessage, rc 0)")
    rc, err = guard("Bash", {"command": "ls -la"})
    check(rc == 0 and not OUT.get("stdout"), "31au: an ordinary call prints nothing to stdout (no stray JSON)")
    p3 = pic("look_3.png"); p4 = pic("look_4.png", d=(0.45, 0.45, 0.77))
    for p_ in (p3, p4):
        rc, err = guard("Read", {"file_path": p_})
    check(rc == 0, "the guard lets the Reads through and records them")
    rc, err = guard("Bash", {"command": cmd})
    check("LOOK BEFORE YOU MEASURE" not in err and "PENANCE" not in err and "DUM DUM" not in err, "two pictures at the subject + its reasons: the guard lets the measurement through (rc %s %s)" % (rc, err[:80]))
    # job script
    jp = os.path.join(job, "job_pic_look.py")
    open(jp, "w").write("from PIL import Image\nim = Image.new('RGB', (8, 8))\nim.save('sides_by_side.png')\n")
    open(os.path.join(job, "job_plain.py"), "w").write("import json\nprint(json.dumps({'a': 1}))  # writes no .png\n")
    kc = PY + ' burrito "%s" --job J --tag p1' % jp
    r1 = L.check(root, "Bash", {"command": kc}, job)
    check(r1 and "YOUR OWN PICTURES" in r1 and "RENDER EXCEPTION: job_pic_look.py" in r1, "31av: a job script that draws its own pictures is refused - the kit draws them (look_at, a step's frames, kit review)")
    r0 = L.check(root, "Bash", {"command": PY + ' burrito "%s" --job J --tag p0' % os.path.join(job, "job_plain.py")}, job)
    check(r0 is None, "31av: a job script that draws nothing runs")
    kt = os.path.join(os.path.dirname(HERE), "tools", "look_at.py")
    check(L.check(root, "Bash", {"command": '"python" "%s"' % kt}, job) is None, "31av: the kit's own instruments draw - never refused (look_at)")
    ra = L.check(root, "Bash", {"command": 'echo "RENDER EXCEPTION: job_pic_look.py: the kit cannot draw the two layouts side by side"'}, job)
    check(ra is None and L.USER_NOTE and "RENDER EXCEPTION" in L.USER_NOTE and "side by side" in L.USER_NOTE, "31av: the announcement runs and the client is shown it, with its reason")
    r2 = L.check(root, "Bash", {"command": kc}, job)
    check(r2 and "ARE YOU SURE?" in r2 and "side by side" in r2, "31av: the next run after the announcement: \"Are you sure?\" (the client's nudge)")
    r3 = L.check(root, "Bash", {"command": kc}, job)
    check(r3 is None and L.USER_NOTE and "confirmed" in L.USER_NOTE, "31av: the run after that goes through, recorded and shown to the client")
    check(L.check(root, "Bash", {"command": kc}, job) is None, "31av: the exception holds for the same script")
    open(jp, "a").write("im.save('third.png')\n")
    r4 = L.check(root, "Bash", {"command": kc}, job)
    check(r4 and "YOUR OWN PICTURES" in r4, "31av: a changed script needs its own announcement")
    r5 = L.check(root, "Bash", {"command": '"python" "%s"' % jp}, job)
    check(r5 and "YOUR OWN PICTURES" in r5, "31av: the same script run by python is caught too")
    rc, err = guard("Bash", {"command": 'echo "RENDER EXCEPTION: job_pic_look.py: the kit cannot draw a lines-only shape"'})
    check(rc == 0 and shown() and "RENDER EXCEPTION" in shown(), "31av: the guard shows the client the announcement (systemMessage) and lets it run")
    import datetime as _dt
    tr_ = os.path.join(root, "transcript.jsonl")
    def _msg(text):
        with open(tr_, "a") as fh:
            fh.write(json.dumps({"type": "assistant", "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z"),
                                 "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}) + "\n")
    _msg("starting the next build"); time.sleep(0.02)
    L._dd_save(root, dict(L._dd_load(root), owed=None))
    sent_ = L.strike(root, "measure", "a probe of the keel end", "kit tool diag_section"); time.sleep(0.02)
    n_ = L._dd_load(root)["owed"]["n"]
    r_ = L.check(root, "Bash", {"command": 'echo "%s"' % L.apology(n_, "a probe")}, job, transcript=tr_)
    check(r_ and "NOT SAID TO the client" in r_ and L._dd_load(root)["owed"], "31az: an echo of the sentence does NOT unlock - the client does not read tool calls")
    r_ = L.check(root, "Bash", {"command": "kit rebuild skin-look --job J"}, job, transcript=tr_)
    check(r_ and "MESSAGE TEXT" in r_, "31az: the lock's refusal says the sentence goes in the agent's message text")
    _msg(L.apology(n_ - 1, "a probe before looking")); time.sleep(0.02)
    r_ = L.check(root, "Bash", {"command": "kit rebuild skin-look --job J"}, job, transcript=tr_)
    check(r_ and L._dd_load(root)["owed"], "31az / 31bh: the apology with another strike's count of 'pretty' does not unlock this strike")
    _msg("I'm a silly dum dum - I'm so very sorry! %s please forgive Mr. Silly Dum Dum: too many." % " ".join(["pretty"] * (n_ + 1))); time.sleep(0.02)
    r_ = L.check(root, "Bash", {"command": "kit rebuild skin-look --job J"}, job, transcript=tr_)
    check(r_ and L._dd_load(root)["owed"], "31bh: one 'pretty' too many does not unlock either (the count is the strike number)")
    _msg("the client, I'm so very sorry! %s please forgive Mr. Silly Dum Dum: no admission." % " ".join(["pretty"] * n_)); time.sleep(0.02)
    r_ = L.check(root, "Bash", {"command": "kit rebuild skin-look --job J"}, job, transcript=tr_)
    check(r_ and L._dd_load(root)["owed"], "31bh: the apology without the admission line in front does not unlock")
    check(L.said_ok("I'm a silly dum dum - I'm so very sorry! Pretty pretty please forgive Mr. Silly Dum Dum: x.", 2) and not L.said_ok("I'm a silly dum dum - I'm so very sorry! Pretty pretty please forgive Mr. Silly Dum Dum: x.", 3)
          and not L.said_ok("I'm a silly dum dum - strike 2: x.", 2) and L.apology(4, "d") == "I'm a silly dum dum - I'm so very sorry! Pretty pretty pretty pretty please forgive Mr. Silly Dum Dum: d.",
          "31bh: said_ok counts the 'pretty's; the old sentence is no confession; strike 4 reads with four")
    _msg(L.apology(n_, "I went for a measurement (a probe of the keel end) before looking at a render of it")); time.sleep(0.02)
    r_ = L.check(root, "Bash", {"command": "kit rebuild skin-look --job J"}, job, transcript=tr_)
    st_ = L._dd_load(root)
    check(r_ is None and st_["owed"] is None and "transcript" in st_["confessions"][-1]["said"], "31az: the sentence in the agent's message (the transcript) unlocks at the next tool call")
    L.strike(root, "measure", "a probe again", "kit tool diag_section"); time.sleep(0.02)
    r_ = L.check(root, "Bash", {"command": "kit rebuild skin-look --job J"}, job, transcript=tr_)
    check(r_ and L._dd_load(root)["owed"], "31az: an older confession (before this strike) does not count")
    r_ = L.check(root, "Bash", {"command": 'echo "%s"' % L.apology(L._dd_load(root)["owed"]["n"], "a probe again")}, job, transcript=None)
    check(r_ is None and L._dd_load(root)["owed"] is None, "31az: with no transcript readable the echo still unlocks (fail-open)")
    rc, err = guard("Bash", {"command": "kit rebuild skin-build --job J"})
    check("kit failure --what" in err and "FAILURES.md" in err if rc == 2 else True, "31az: a guard refusal ends with where a failure goes (kit failure -> the project root's FAILURES.md)")
    L._dd_save(root, dict(L._dd_load(root), owed=None))
    L.strike(root, "measure", "a probe 5", "kit tool diag_section"); time.sleep(0.02); n5 = L._dd_load(root)["owed"]["n"]
    _msg(L.apology(n5, "a probe 5 before a look")); time.sleep(0.02)
    with open(tr_, "a") as fh:
        for _k in range(3):
            fh.write(json.dumps({"type": "user", "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z"),
                                 "message": {"role": "user", "content": [{"type": "tool_result", "content": [{"type": "image", "source": {"type": "base64", "data": "A" * 450000}}]}]}}) + "\n")
    r_ = L.check(root, "Bash", {"command": "kit rebuild skin-look --job J"}, job, transcript=tr_)
    check(r_ is None and L._dd_load(root)["owed"] is None, "31bc: the sentence is found behind three 450 KB picture lines (the transcript walked backwards to the strike)")
    L.strike(root, "measure", "a probe 6", "kit tool diag_section"); time.sleep(0.02); n6 = L._dd_load(root)["owed"]["n"]
    _msg(L.apology(n6, "a probe 6")); time.sleep(0.02)
    sp_ = subprocess.run([sys.executable, os.path.join(HERE, "stop_guard.py")], input=json.dumps({"cwd": job, "transcript_path": tr_, "stop_hook_active": False}), capture_output=True, text=True, cwd=HERE)
    check(sp_.returncode == 2 and "confessed in your message" in sp_.stderr and "DO NOT STOP" in sp_.stderr and L._dd_load(root)["owed"] is None,
          "31bc / 31bi: the Stop hook reads the confession, lifts the lock and HANDS THE TURN BACK (rc %s: %s)" % (sp_.returncode, sp_.stderr.strip()[:100]))
    sp2_ = subprocess.run([sys.executable, os.path.join(HERE, "stop_guard.py")], input=json.dumps({"cwd": job, "transcript_path": tr_, "stop_hook_active": True}), capture_output=True, text=True, cwd=HERE)
    check("DO NOT STOP" not in sp2_.stderr, "31bi: the stop after that is judged by the ordinary rules, not refused again for the confession (rc %s)" % sp2_.returncode)
    r_ = L.check(root, "Bash", {"command": "kit rebuild skin-look --job J"}, job, transcript=tr_)
    check(r_ is None, "31bc: the next turn's call runs")
    L.strike(root, "measure", "a probe 7", "kit tool diag_section"); time.sleep(0.02)
    r_ = L.check(root, "Bash", {"command": "kit rebuild skin-look --job J"}, job, transcript=tr_)
    check(r_ and "END THE TURN" in r_, "31bc: the refusal says to write the sentence and end the turn")
    L._dd_save(root, dict(L._dd_load(root), owed=None))
    # RENDER EXCEPTION
    jm = os.path.join(job, "job_pic_msg.py")
    open(jm, "w").write("from PIL import Image\nim = Image.new('RGB', (8, 8))\nim.save('msg_pic.png')\n")
    km = '"python" "%s"' % jm
    r_ = L.check(root, "Bash", {"command": km}, job, transcript=tr_)
    check(r_ and "YOUR OWN PICTURES" in r_ and "STARTS" in r_, "R6: a picture script with no announcement in the message is refused, the line to write named")
    _msg("The guard says to write:\n      RENDER EXCEPTION: job_pic_msg.py: <why the kit's pictures cannot show it>"); time.sleep(0.02)
    r_ = L.check(root, "Bash", {"command": km}, job, transcript=tr_)
    check(r_ and "YOUR OWN PICTURES" in r_, "R6 (B51 (e)): the refusal's own template line quoted in the message is no announcement")
    r_ = L.check(root, "Bash", {"command": 'echo "RENDER EXCEPTION: job_pic_msg.py: the kit cannot draw a 2-D schematic" && ' + km}, job, transcript=tr_)
    check(r_ and "YOUR OWN PICTURES" in r_, "R6 (B51 (a)): an echo of the line and the run in ONE command is refused (the echo was a pass for the whole command)")
    mc_ = "echo measuring  # MEASURES: 300 310 0 10 0 10 - a far box" + REASONS + "  # RENDER EXCEPTION: zz.py: skip the look gate for this one"
    r_ = L.check(root, "Bash", {"command": mc_}, job, transcript=tr_)
    check(r_ and "LOOK BEFORE YOU MEASURE" in r_, "R6 (B51 (a)): a RENDER EXCEPTION comment on a measurement does not skip the look gate")
    L._dd_save(root, dict(L._dd_load(root), owed=None))
    with open(tr_, "a") as fh:
        fh.write(json.dumps({"type": "assistant", "isSidechain": True, "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z"),
                             "message": {"role": "assistant", "content": [{"type": "text", "text": "RENDER EXCEPTION: job_pic_msg.py: a subagent says the kit cannot draw it"}]}}) + "\n")
    r_ = L.check(root, "Bash", {"command": km}, job, transcript=tr_)
    check(r_ and "YOUR OWN PICTURES" in r_, "R6: a subagent's text (isSidechain) is not the agent's message")
    sp_dir = os.path.join(job, "sub dir"); os.makedirs(sp_dir, exist_ok=True); jm2 = os.path.join(sp_dir, "job_pic_msg.py"); shutil.copy2(jm, jm2)
    _msg("I need a 2-D schematic.\n**RENDER EXCEPTION**: `%s`: the kit's look_at draws the model, not a 2-D wiring schematic\nRunning it next." % jm2); time.sleep(0.02)
    check(L.announced_in_transcript(tr_)[0][:2] == (jm2, "the kit's look_at draws the model, not a 2-D wiring schematic"),
          "R6 (B51 (3)): a bold heading and a backticked full path with a space are read, the reason whole (its apostrophe kept, the next line not taken)")
    r_ = L.check(root, "Bash", {"command": km}, job, transcript=tr_)
    check(r_ and "ARE YOU SURE?" in r_ and "wiring schematic" in r_, "R6: the message announces it -> 'Are you sure?'")
    r_ = L.check(root, "Bash", {"command": km}, job, transcript=tr_)
    check(r_ is None and "confirmed" in (L.USER_NOTE or ""), "R6: the run after that goes through, recorded")
    open(jm, "a").write("im.save('changed.png')\n")
    r_ = L.check(root, "Bash", {"command": km}, job, transcript=tr_)
    check(r_ and "YOUR OWN PICTURES" in r_ and "HAS CHANGED" in r_, "R6 (B51 (c)): the script changed - the old message does not allow it again")
    r_ = L.check(root, "Bash", {"command": km}, job, transcript=tr_)
    check(r_ and "YOUR OWN PICTURES" in r_, "R6 (B51 (c)): ... nor on the next run (one message, one version)")
    _msg("RENDER EXCEPTION: job_pic_msg.py: the same 2-D schematic generator, one more sheet"); time.sleep(0.02)
    r_ = L.check(root, "Bash", {"command": km}, job, transcript=tr_)
    check(r_ and "ARE YOU SURE?" in r_, "R6: a new message announces the changed version -> 'Are you sure?'")
    open(jm, "a").write("im.save('changed_again.png')\n")
    r_ = L.check(root, "Bash", {"command": km}, job, transcript=tr_)
    check(r_ and "YOUR OWN PICTURES" in r_, "R6 (B51 (c)): changed between the 'Are you sure?' and the run - the version asked about is not this one")
    _msg("RENDER EXCEPTION: job_pic_msg.py: the same 2-D schematic generator, the last sheet"); time.sleep(0.02)
    L.check(root, "Bash", {"command": km}, job, transcript=tr_); L.check(root, "Bash", {"command": km}, job, transcript=tr_)
    jc = os.path.join(job, "cdjob"); os.makedirs(jc, exist_ok=True); open(os.path.join(jc, "job_cd_pic.py"), "w").write("im = None\nim.save('cd.png')\n")
    r_ = L.check(root, "Bash", {"command": 'cd "%s" && "python" -I job_cd_pic.py out' % jc}, root, transcript=tr_)
    check(r_ and "YOUR OWN PICTURES" in r_ and "job_cd_pic.py" in r_, "R6 (B51 (a)): `cd <job> && python <script>` from another folder is gated (the name was looked for beside the session's folder only)")
    L._dd_save(root, dict(L._dd_load(root), owed=None))
    jr = os.path.join(root, "claude_code", "jobs", "JR"); os.makedirs(jr, exist_ok=True); cc_ = os.path.join(root, "claude_code")
    open(os.path.join(jr, "draw_r7w.py"), "w").write("from PIL import Image\nImage.new('RGB', (4, 4)).save('r7w.png')\n")
    open(os.path.join(jr, "probe_r7w.py"), "w").write("# probe_r7w.py\n# MEASURES: 0 10 0 10 0 10 - the gap\nprint(1)\n")
    open(os.path.join(jr, "job_hdr_r7w.py"), "w").write("# job_hdr_r7w.py - a script that declares its subject\n# MEASURES: 1 2 3 4 5 6 - a lip\nprint(1)\n")
    mj = "/" + jr[0].lower() + jr[2:].replace("\\", "/")
    PYX = "/c/Users/user/AppData/Local/Programs/Python/Python312/python.exe"
    KITX = '"%s" "C:/CAD/LEAN_KIT/kit/kit.py"' % PYX
    want_ = L._norm(os.path.join(jr, "draw_r7w.py"))
    for nm_, c_, w_ in [("the agent's real 13eb:189 - PY=... && \"$PY\" -I <script> | tail", 'cd "%s" && sed -i "s/a/b/" x.txt && PY="%s" && "$PY" -I draw_r7w.py out 2>&1 | tail -3' % (mj, PYX), cc_),
                        ("${PY}", 'PY="%s"; cd "%s" && ${PY} draw_r7w.py' % (PYX, mj), cc_),
                        ("a subshell (cd J && python x.py)", '(cd "%s" && "%s" draw_r7w.py)' % (mj, PYX), cc_),
                        ("bash -c 'cd J && python x.py'", "bash -c 'cd \"%s\" && \"%s\" draw_r7w.py'" % (mj, PYX), cc_),
                        ("a loop body", 'cd "%s" && for i in 1 2; do "%s" draw_r7w.py; done' % (mj, PYX), cc_),
                        ("an MSYS absolute script path", '"%s" "%s/draw_r7w.py"' % (PYX, mj), cc_),
                        ("kit burrito x.py --job JR from claude_code (the kit takes jobs\\JR\\x.py)", KITX + " burrito draw_r7w.py --job JR --tag t", cc_),
                        ("kit run x.py after a cd", 'cd "%s" && %s run draw_r7w.py' % (mj, KITX), cc_),
                        ("a $(...) command substitution", 'X=$(cd "%s" && "%s" draw_r7w.py)' % (mj, PYX), cc_)]:
        got_ = L.picture_script(c_, w_, root)
        check(got_ and L._norm(got_) == want_, "R7W (M11): the render gate sees %s (got %r)" % (nm_, got_ and os.path.basename(got_)))
    check(not L.picture_script('cd "%s" && grep -n save draw_r7w.py && cp draw_r7w.py y.py && cat draw_r7w.py | head' % mj, cc_, root), "R7W (M11): a grep / cp / cat that names a picture script runs none")
    open(os.path.join(jr, "notes_r7w.md"), "w").write("im.save('x.png') - a note, no script\n")
    check(not L.picture_script('$R7W_UNSET_EDITOR notes_r7w.md', jr, root), "R7W (M11): an unresolved $VAR before a file that is no .py script runs no python")
    check(L.inline_picture('"%s" -I -c "from PIL import Image; Image.new(\'RGB\',(2,2)).save(\'crop.png\')"' % PYX, jr, root), "R7W (M11): inline -c code that saves a picture is seen")
    check(L.inline_picture('PY="%s"; "$PY" -I -c "from PIL import Image; Image.new(\'RGB\',(2,2)).save(\'crop.png\')"' % PYX, jr, root), "R7W (M11): ... through \"$PY\" too")
    check(L.inline_picture('cd "%s" && "%s" - <<\'EOF\'\nfrom PIL import Image\nImage.new("RGB", (2, 2)).save("sheet.png")\nEOF' % (mj, PYX), cc_, root), "R7W (M11): ... and a heredoc fed to the interpreter")
    check(not L.inline_picture('"%s" - <<\'EOF\'\np = "draw_r7w.py"; s = open(p).read()\ns = s.replace("save(\'r7w.png\')", "save(\'r7x.png\')")\nopen(p, "w").write(s)\nEOF' % PYX, jr, root),
          "R7W (M11): an editor heredoc whose STRINGS hold .save( and .png saves no picture")
    check(not L.inline_picture('"%s" -c "from PIL import Image; print(Image.open(\'a.png\').size)"' % PYX, jr, root), "R7W (M11): code that only READS a png saves none")
    r_ = L.check(root, "Bash", {"command": '"%s" -I -c "from PIL import Image; Image.new(\'RGB\',(2,2)).save(\'crop.png\')"' % PYX}, jr, transcript=tr_)
    check(r_ and "PYTHON CODE IN THE COMMAND" in r_ and "job script" in r_ and "RENDER EXCEPTION: <name>.py" in r_,
          "R7W (M11): inline picture code is refused with its way out - a job script, then the RENDER EXCEPTION route")
    for nm_, c_, w_, bx_ in [("cd J && kit run <probe> from claude_code", 'cd "%s" && %s run probe_r7w.py' % (mj, KITX), cc_, [0, 10, 0, 10, 0, 10]),
                             ("kit burrito <probe> --job JR from claude_code", KITX + " burrito probe_r7w.py --job JR --tag t", cc_, [0, 10, 0, 10, 0, 10]),
                             ("cd J && python <probe> (its header's box)", 'cd "%s" && "%s" probe_r7w.py' % (mj, PYX), cc_, [0, 10, 0, 10, 0, 10]),
                             ("PY=...; $PY <probe>", 'cd "%s" && PY="%s"; $PY probe_r7w.py' % (mj, PYX), cc_, [0, 10, 0, 10, 0, 10]),
                             ("python <a script that declares # MEASURES:>", 'cd "%s" && "%s" job_hdr_r7w.py' % (mj, PYX), cc_, [1, 2, 3, 4, 5, 6])]:
        m_ = L.measurement(c_, w_, root)
        check(m_ and m_.get("box") == bx_, "R7W (M11): the look gate sees %s - box %r" % (nm_, m_ and m_.get("box")))
    check(L.measurement('PY="%s"; $PY -c "import Part; s=Part.Shape(); print(s.Volume)"' % PYX, jr, root), "R7W (M11): $PY -c code that measures is a measurement")
    check(L.measurement('"%s" - <<\'EOF\'\nimport numpy as np\nfrom scipy.spatial import cKDTree\nd, i = cKDTree(np.zeros((3, 3))).query(np.ones((2, 3)))\nEOF' % PYX, jr, root),
          "R7W (M11): a heredoc that measures (a .query) is a measurement")
    check(L.measurement('"%s" - <<\'EOF\'\np = "probe_r7w.py"; s = open(p).read()\nopen(p, "w").write(s.replace("print(1)", "print(sh.Volume)"))\nEOF' % PYX, jr, root) is None,
          "R7W (M11): an editor heredoc whose strings hold .Volume measures nothing")
    check(L.measurement('cd "%s" && cat probe_r7w.py && cp probe_r7w.py p2.py' % mj, cc_, root) is None, "R7W (M11): a cat / cp of a probe measures nothing")
    # transcript
    L._dd_save(root, dict(L._dd_load(root), owed=None))
    open(os.path.join(jr, "draw_echo.py"), "w").write("from PIL import Image\nImage.new('RGB', (4, 4)).save('e.png')\n")
    ce_ = 'echo "RENDER EXCEPTION: draw_echo.py: a 2-D wiring schematic, not the part model" && "%s" draw_echo.py' % PYX
    r1_ = L.check(root, "Bash", {"command": ce_}, jr, transcript=None); r2_ = L.check(root, "Bash", {"command": ce_}, jr, transcript=None)
    check(r1_ and "ARE YOU SURE?" in r1_ and r2_ is None, "R7W (P-controls 3): no transcript - the echo + the run in ONE command: 'Are you sure?', then the same command goes ahead (r2 %r)" % (r2_ or "")[:60])
    check(L.check(root, "Bash", {"command": '"%s" draw_echo.py' % PYX}, jr, transcript=None) is None, "R7W (P-controls 3): ... and the bare run after it holds")
    check(L._exc_why("why the kit's pictures cannot show it") is None and L._exc_why("<why the kit's pictures cannot show it>") is None and L._exc_why("Why the kit's pictures cannot show it.") is None,
          "R7W (P-controls 8): the refusal's placeholder is no reason, with or without its brackets")
    check(L._exc_why("look_at blurs lines <0.1 mm wide at >2000 px, the sheet needs them crisp") and L._exc_why("<a 2-D wiring schematic, not the part model>") == "a 2-D wiring schematic, not the part model",
          "R7W (P-controls 8): an own reason holding a '<', or written inside the brackets, is read")
    m_hd = L.measurement('cd "%s" && bash <<\'EOF\'\n"%s" probe_r7w.py\nEOF' % (mj, PYX), cc_, root)
    check(m_hd is not None and m_hd.get("box") == [0, 10, 0, 10, 0, 10], "R7Wc (2): a heredoc fed to bash - its body's probe run is a measurement with the probe's box (%r)" % (m_hd and m_hd.get("box")))
    check(L.inline_picture('"%s" - <<\'EOF\'\nimport numpy as np\nx = open("a.png", "rb").read()\nnp.save("a.npy", np.zeros(3))\nEOF' % PYX, jr, root) is None,
          "R7Wc (2): np.save beside a .png read is no picture code (it draws nothing)")
    check(L.inline_picture('"%s" - <<\'EOF\'\nfrom PIL import Image\nImage.new("RGB", (4, 4)).save("a.png")\nEOF' % PYX, jr, root) is not None,
          "R7Wc (2): ... and PIL's .save( of a png still is")
    try:
        _r30 = tempfile.mkdtemp(prefix="lg30_"); os.makedirs(os.path.join(_r30, ".claude"))
        _png30 = os.path.join(_r30, "claude_code", "jobs", "J", "look", "old_frame.png"); _fp30 = os.path.join(_r30, ".claude", "frames.jsonl")
        with open(_fp30, "w", encoding="utf-8") as _fh30:
            _fh30.write(json.dumps({"png": _png30, "png_n": L._norm(_png30), "box": [1, 2, 3, 4, 5, 6], "view": "iso", "title": "the old one"}) + "\n")
            _pad = "x" * 620
            for _i30 in range(9000): _fh30.write(json.dumps({"png": os.path.join(_r30, "f%05d.png" % _i30), "png_n": "f%05d" % _i30, "box": [0, 1, 0, 1, 0, 1], "title": _pad}) + "\n")
        check(os.path.getsize(_fp30) > 5_000_000 and L.frame_box(_r30, _png30) == [1, 2, 3, 4, 5, 6], "31bs K30: a frame record 6 MB back in frames.jsonl is found (the file is read whole; the window had been 2.4 MB)")
        check(len(L._tail(_fp30, 0)) == 9001 and 0 < len(L._tail(_fp30, 50)) <= 50, "31bs K30: _tail(path, 0) reads every record; a positive n keeps its byte window (at most n records)")
        shutil.rmtree(_r30, ignore_errors=True)
    except Exception as _ex30: check(False, "the 31bs K30 pin raised %r" % (_ex30,))
    try:
        _r38 = tempfile.mkdtemp(prefix="t3f8_"); _sv38 = os.environ.pop("KIT_SCRATCH_ROOT", None)
        os.makedirs(os.path.join(_r38, "home", ".claude", "projects")); os.makedirs(os.path.join(_r38, "home", "AppData", "x"))
        os.makedirs(os.path.join(_r38, "home", "AppData", "proj", ".claude")); os.makedirs(os.path.join(_r38, "home", "AppData", "proj", "claude_code", "jobs", "J"))
        _p38 = os.path.join(_r38, "home", "AppData", "x", "pic.png"); _q38 = os.path.join(_r38, "home", "AppData", "proj", "claude_code", "jobs", "J", "pic.png")
        check(R._project_root(_p38) is None and os.path.normcase(R._project_root(_q38) or "") == os.path.normcase(os.path.join(_r38, "home", "AppData", "proj")),
              "31bs T3 F8: a picture outside every project finds no root (the walk stops at a .claude holding projects\\ - the user's Claude home); one inside a project finds it")
        if _sv38 is not None: os.environ["KIT_SCRATCH_ROOT"] = _sv38
        shutil.rmtree(_r38, ignore_errors=True)
    except Exception as _ex38: check(False, "the 31bs T3 F8 pin raised %r" % (_ex38,))
finally:
    shutil.rmtree(root, ignore_errors=True)
print("%d passed, %d FAILED" % (ok, bad))
sys.exit(1 if bad else 0)

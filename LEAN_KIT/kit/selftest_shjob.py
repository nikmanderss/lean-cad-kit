import os, sys, time, re, tempfile, textwrap, subprocess, types
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
if not os.environ.get("KIT_PROJECT"):
    _sp = os.path.join(tempfile.gettempdir(), "_kit_selftest_shjob_proj"); os.makedirs(os.path.join(_sp, "claude_code"), exist_ok=True); os.makedirs(os.path.join(_sp, ".claude", "_leangates"), exist_ok=True)
    os.environ["KIT_PROJECT"] = _sp
os.environ.setdefault("KIT_NO_INBOX", "1")
import kit
PASS, FAIL = [], []
def check(cond, what):
    (PASS if cond else FAIL).append(what); print("  %s  %s" % ("ok  " if cond else "FAIL", what), flush=True)
tmp = tempfile.mkdtemp(prefix="shjob_")
child = os.path.join(tmp, "_shjob_child.py")
open(child, "w", encoding="utf-8").write(textwrap.dedent('''
    import os, sys, time, subprocess
    # a DETACHED grandchild (its own console-less process, a new process group) that would outlive its parent - the 31an orphan's shape
    flags = (0x00000008 | 0x00000200 | 0x08000000) if os.name == "nt" else 0
    g = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], creationflags=flags, close_fds=True)
    print("GRANDCHILD %d" % g.pid, flush=True)
    if sys.argv[1] == "exit": sys.exit(0)        # the step leaves at once; the grandchild stays - the job's close must end it
    time.sleep(120)                               # 'hang': silent past the cap - the watchdog kills it
'''))
NT = os.name == "nt"
_flags = 0x08000000 if NT else 0
def gpid_of(out):
    m = re.search(r"GRANDCHILD (\d+)", out or ""); return int(m.group(1)) if m else None
def reap(pid):
    if pid and kit._alive(pid):
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)] if NT else ["kill", "-9", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    if NT:
        h = kit._job_new(); check(bool(h), "a job object is made on Windows (kill-on-close)"); kit._job_close(h)
    rc, out = kit.sh([sys.executable, child, "exit"], 30, log=os.path.join(tmp, "c1.log"))
    g1 = gpid_of(out); time.sleep(0.6)
    check(rc == 0 and g1 is not None and (not NT or not kit._alive(g1)), "1. a grandchild left by a step that exited is dead when sh() returns (kill-on-close; rc %s, grandchild %s alive=%s)" % (rc, g1, kit._alive(g1) if g1 else None))
    reap(g1)
    rc, out = kit.sh([sys.executable, child, "hang"], 3, log=os.path.join(tmp, "c2.log"))
    g2 = gpid_of(out); time.sleep(0.6)
    check(rc == kit.KILLED_RC and g2 is not None and (not NT or not kit._alive(g2)), "2. a hung step is KILLED at its cap and its detached grandchild dies with it (rc %s, grandchild %s alive=%s)" % (rc, g2, kit._alive(g2) if g2 else None))
    check("confirmed gone" in out, "2. ... and the kill is confirmed gone")
    reap(g2)
    sib = subprocess.Popen([sys.executable, child, "hang"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=_flags)
    sg = gpid_of(sib.stdout.readline())
    rc, out = kit.sh([sys.executable, child, "hang"], 3, log=os.path.join(tmp, "c3.log"))
    g3 = gpid_of(out); time.sleep(0.6)
    check(sib.poll() is None and (sg is None or kit._alive(sg)), "3. a sibling running the SAME script name (and its own grandchild) survives another step's kill (no by-name sweep while the job holds)")
    check(rc == kit.KILLED_RC and (not NT or not kit._alive(g3)), "3. ... while the killed step's own grandchild is gone")
    reap(sib.pid); reap(sg); reap(g3)
    if NT:
        kit._win_procs = lambda: [(100, 1, "python _shjob_child.py a"), (101, 1, "python _shjob_child.py b"), (102, 100, "grandchild of 100")]
        t_on = set(kit._kill_targets(types.SimpleNamespace(pid=100), [sys.executable, child], by_name=True)); t_off = set(kit._kill_targets(types.SimpleNamespace(pid=100), [sys.executable, child], by_name=False))
        check(t_off == {100, 102} and t_on == {100, 101, 102}, "4. the belt (no job): by_name reaches the sibling that shares the script name; with a job the tree alone (%s / %s)" % (sorted(t_off), sorted(t_on)))
    ks = open(os.path.join(HERE, "kit.py"), encoding="utf-8").read()
    check('killed["left"] = _kill_tree(p, cmd, by_name=not job["ok"])' in ks and 'if job["h"]: _job_close(job["h"]); job["h"] = None' in ks and "_jobs[k] = _jb if (_jb and _job_assign(_jb, pr)) else None" in ks,
          "5. sh() kills by job and sweeps by name only without one; the job is closed at sh()'s end; the review's shards get a job each")
finally:
    import shutil; shutil.rmtree(tmp, ignore_errors=True)
print("selftest_shjob: %d passed, %d FAILED" % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)

import subprocess, sys, os, time, glob
K = os.path.dirname(os.path.abspath(__file__)); py = sys.executable
args = sys.argv[1:]
out_dir = None
if "--out" in args:
    i = args.index("--out"); out_dir = args[i + 1]; args = args[:i] + args[i + 2:]
suites = sorted(glob.glob(os.path.join(K, "selftest_*.py")) + glob.glob(os.path.join(K, "kit", "selftest_*.py"))
                + glob.glob(os.path.join(K, "hooks", "selftest_*.py")))
if args:
    suites = [s for s in suites if os.path.basename(s) in args]
env = dict(os.environ); env.update({"KIT_HOME": os.path.join(K, "kit"), "PYTHONPATH": os.path.join(K, "kit"), "PYTHONUTF8": "1"})
env.pop("KIT_NO_INBOX", None)
flags = {"creationflags": 0x08000000} if os.name == "nt" else {}
t0 = time.time(); bad = []; lines = []


def say(s):
    print(s, flush=True); lines.append(s)


for s in suites:
    t = time.time()
    p = subprocess.run([py, "-W", "ignore", s], cwd=os.path.dirname(s), env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=1800, **flags)
    tail = [l for l in (p.stdout + p.stderr).splitlines() if l.strip()][-3:]
    say("%-32s rc %-3s %5.0f s | %s" % (os.path.basename(s), p.returncode, time.time() - t, " / ".join(x[:100] for x in tail)))
    if p.returncode:
        bad.append(os.path.basename(s))
        lines_ = (p.stdout + p.stderr).splitlines()
        for i_, l_ in enumerate(lines_):
            if "FAIL" in l_ and "FAILED:" not in l_:
                say("    " + l_.rstrip()[:200])
                if i_ + 1 < len(lines_) and lines_[i_ + 1].strip():
                    say("    " + lines_[i_ + 1].rstrip()[:200])
        for l_ in lines_[-12:]:
            say("    | " + l_.rstrip()[:200])
say("SUITES DONE %.0f s - failing: %s" % (time.time() - t0, bad or "none"))
if out_dir:
    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, "selftests_%s.log" % time.strftime("%Y-%m-%d_%H%M")), "w", encoding="utf-8").write("\n".join(lines) + "\n")
sys.exit(1 if bad else 0)

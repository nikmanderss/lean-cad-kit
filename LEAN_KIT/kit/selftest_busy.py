# needs none
import os, sys, time, tempfile, textwrap
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
if not os.environ.get("KIT_PROJECT"):
    _sp = os.path.join(tempfile.gettempdir(), "_kit_selftest_busy_proj"); os.makedirs(os.path.join(_sp, "claude_code"), exist_ok=True); os.makedirs(os.path.join(_sp, ".claude", "_leangates"), exist_ok=True)
    os.environ["KIT_PROJECT"] = _sp
os.environ.setdefault("KIT_NO_INBOX", "1")
import kit
RB = os.path.join(HERE, "rebuild")
child = os.path.join(tempfile.gettempdir(), "_kit_selftest_busy_child.py")
open(child, "w", encoding="utf-8").write(textwrap.dedent('''
    import sys, time; sys.path.insert(0, sys.argv[1]); from _busy import busy
    mode, allow, sleep = sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
    print("start", flush=True)
    if mode == "declared":
        with busy("a declared silent call", allow): time.sleep(sleep)
    else: time.sleep(sleep)
    print("done", flush=True)
'''))
fails = 0
def case(n, mode, allow, sleep, cap, expect_rc, expect_text):
    global fails
    log = os.path.join(tempfile.gettempdir(), "_kit_selftest_busy_%d.log" % n)
    for f in (log, log + ".busy"):
        try: os.remove(f)
        except OSError: pass
    rc, out = kit.sh([sys.executable, child, RB, mode, str(allow), str(sleep)], cap, log=log)
    ok = (rc == expect_rc) and (expect_text in out) and not os.path.exists(log + ".busy")
    print("[%d] %-10s allow %3g sleep %3g cap %2g -> rc %3d %s  %s" % (n, mode, allow, sleep, cap, rc, "ok  " if ok else "FAIL", expect_text if ok else out[-300:].replace("\n", " | ")), flush=True)
    if not ok: fails += 1
case(1, "declared", 40, 14, 6, 0, "heartbeat - the step declares itself busy")
case(2, "undeclared", 0, 14, 6, kit.KILLED_RC, "cause: silence")
case(3, "declared", 5, 20, 6, kit.KILLED_RC, "ran past its own allowance")
child2 = os.path.join(tempfile.gettempdir(), "_kit_selftest_busy_child2.py")
open(child2, "w", encoding="utf-8").write(textwrap.dedent('''
    import sys, time; sys.path.insert(0, sys.argv[1]); from _busy import busy
    print("start", flush=True)
    for op in sys.argv[2:]:
        k = op.split(":")
        if k[0] == "d":
            with busy("a declared silent call", float(k[1])): time.sleep(float(k[2]))
        elif k[0] == "s": time.sleep(float(k[1]))
        elif k[0] == "t":
            for i in range(int(k[1])): time.sleep(float(k[2])); print("tick %d" % i, flush=True)
    print("done", flush=True)
'''))
def case2(n, ops, cap, expect_rc, expect_text, gap=12.0):
    global fails
    time.sleep(gap)
    log = os.path.join(tempfile.gettempdir(), "_kit_selftest_busy_%d.log" % n)
    for f in (log, log + ".busy", log + ".busy.done"):
        try: os.remove(f)
        except OSError: pass
    rc, out = kit.sh([sys.executable, child2, RB] + ops, cap, log=log)
    ok = (rc == expect_rc) and (expect_text in out) and not os.path.exists(log + ".busy") and not os.path.exists(log + ".busy.done")
    print("[%d] %-24s cap %2g -> rc %3d %s  %s" % (n, " ".join(ops), cap, rc, "ok  " if ok else "FAIL", expect_text if ok else out[-300:].replace("\n", " | ")), flush=True)
    if not ok: fails += 1
case2(4, ["d:14:12", "t:8:1"], 6, 0, "done")
case2(5, ["d:14:12", "s:5"], 6, 0, "done")
case2(6, ["d:14:12", "s:20"], 6, kit.KILLED_RC, "after the step's last declared call ended")
case2(7, ["t:25:1"], 6, kit.KILLED_RC, "hard ceiling 18 s of undeclared time")
print("%d FAILED" % fails if fails else "selftest_busy: 7 passed, 0 failed - a declared silent call is waited for, an undeclared one is killed, a declaration is a bound, a declared call's time is out of the ceiling and the silence (31bq R6)")
sys.exit(1 if fails else 0)

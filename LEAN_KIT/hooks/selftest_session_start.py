#!/usr/bin/env python3
"""selftest_session_start.py - the SessionStart hook's post-compaction push (31bq COMPACT / batch XX), driven the way Claude Code drives it: JSON on stdin.

    & python "C:\\CAD\\LEAN_KIT\\hooks\\selftest_session_start.py"

PINNED: a compaction gives the block FIRST and a startup none; a strike owed and the unread inbox sit at the top, inside a 2 KB preview; the BUILD_LOG is five
rows; the live job is the one STATE_NOW's newest block names first by a WORD-BOUNDARY match (REBUILD_JOB never takes REBUILD_JOB2's place, however the logs'
times fall); an in-place edit of an inbox entry already read is not new, a new block is; the region's and the keep's verdicts are listed; the runner's refusals
(rc 2) never push the runs out - the newest five RUNS are listed and the refusals COUNTED in one line with the newest one's line (fix-route-end-seen)."""
import json, os, shutil, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); HOOK = os.path.join(HERE, "session_start.py")
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "kit")); import leangate as G
FAILED = []
def check(label, cond, detail=""):
    print("  %-4s %s" % ("ok" if cond else "FAIL", label))
    if not cond: print("       %s" % str(detail)[:300]); FAILED.append(label)
def run(root, source):
    env = dict(os.environ); env.pop("KIT_SCRATCH_ROOT", None)
    p = subprocess.run([sys.executable, HOOK], input=json.dumps({"cwd": root, "source": source, "session_id": "selftest", "hook_event_name": "SessionStart"}), capture_output=True, text=True, env=env)
    return p.stdout or ""
def row(tag, step, line, rc):
    return "| 2026-10-19 12:%02d:00 | %s | %s | LAM=0.5, KEEP_NET=1, EDGE_FIX=1, W_EDGE=400, CTRL_MM=1.0 | %s | %s | 9 |" % (tag, tag, step, line + " - 76 faces in the piece (the edit region's content had 142), a valid solid, the frame exact; check(True) FAILS on face(s) 1 (cap), 2 (orig)", rc)
def main():
    os.environ.pop("KIT_SCRATCH_ROOT", None)
    root = tempfile.mkdtemp(prefix="sstart_")
    try:
        os.makedirs(os.path.join(root, ".claude", "_leangates")); cc = os.path.join(root, "claude_code"); jobs = os.path.join(cc, "jobs")
        for jn in ("REBUILD_JOB2", "REBUILD_JOB"):
            os.makedirs(os.path.join(jobs, jn, "skin", "review")); os.makedirs(os.path.join(jobs, jn, "review"))
            open(os.path.join(jobs, jn, "BUILD_LOG.md"), "w", encoding="utf-8").write("# BUILD LOG\n\n" + "\n".join(row(i, "skin-build", "SKIN BUILD PASS %s %d" % (jn, i), 0) for i in range(1, 13)) + "\n")
            time.sleep(0.05)
        json.dump({"verdict": "ok", "when": "2026-10-19 12:00:00", "note": "the cuts land in air"}, open(os.path.join(jobs, "REBUILD_JOB2", "review", "REGION_CUTS_JUDGED.json"), "w"))
        os.utime(os.path.join(jobs, "REBUILD_JOB", "BUILD_LOG.md"), None)
        open(os.path.join(cc, "STATE_NOW.md"), "w", encoding="utf-8").write("# >>> UPDATE 2026-10-19 08:11\n* REBUILD_JOB2 HELD at the trial; REBUILD_JOB b27b accepted, not applied\n\n# >>> UPDATE 2026-10-18\n* old\n")
        ib = os.path.join(cc, "INBOX.md")
        open(ib, "w", encoding="utf-8").write("# INBOX\n\n---\n\n# FROM the kit maintainer  2026-10-19 10:00\n\nthe first note, read\n\n---\n\n# FROM the kit maintainer  2026-10-19 10:30\n\n" + "the second note, read too. " * 17 + "\n")
        G.inbox_mark(root, len(open(ib, encoding="utf-8").read()))
        txt = open(ib, encoding="utf-8").read().replace("the first note, read", "the first note, read - and corrected in place by its writer: " + "a longer sentence. " * 32)
        open(ib, "w", encoding="utf-8").write(txt)
        json.dump({"owed": {"n": 2, "since": time.time() - 60, "t": time.time() - 60}, "confessions": [], "strikes": [{"n": 1}, {"n": 2}]}, open(os.path.join(root, ".claude", "dumdum.json"), "w"))
        out_s = run(root, "startup"); out_c = run(root, "compact")
        check("a startup gives no post-compaction block", "AFTER THE COMPACTION" not in out_s, out_s[:200])
        i0 = out_c.find("AFTER THE COMPACTION")
        check("a compaction gives the block FIRST", 0 <= i0 < 200, out_c[:200])
        pre = out_c[:2048]
        check("the strike owed sits inside the 2 KB preview", "A STRIKE IS OWED" in pre, pre[-300:])
        check("the region's verdict is listed (and inside the preview)", "REGION_CUTS_JUDGED.json" in pre, pre[-300:])
        check("the live job is the one STATE_NOW names FIRST (REBUILD_JOB2), not the prefix job whose log is newer", "job REBUILD_JOB2:" in out_c and "job REBUILD_JOB:" not in out_c, [l for l in out_c.splitlines() if "BUILD_LOG.md, the newest" in l])
        blk = out_c[i0:out_c.find("=" * 78, i0 + 80)]
        check("the BUILD_LOG is FIVE rows, step and result (no levers column)", blk.count("skin-build: SKIN BUILD PASS") == 5 and "LAM=0.5" not in blk, blk[-400:])
        check("an in-place edit of an inbox entry already read is NOT new", "INBOX unread" not in out_c, [l for l in out_c.splitlines() if "INBOX" in l][:2])
        with open(ib, "a", encoding="utf-8") as fh: fh.write("\n---\n\n# FROM the client  2026-10-19 12:30\n\nstop at the trial\n")
        out_c2 = run(root, "compact")
        check("a NEW inbox block is listed by its head, inside the preview", "INBOX unread" in out_c2[:2048] and "FROM the client" in out_c2[:2048], [l for l in out_c2.splitlines() if "INBOX" in l][:2])
        bl2 = os.path.join(jobs, "REBUILD_JOB2", "BUILD_LOG.md")
        def runrow(i): return "| 2026-10-19 13:%02d:00 | r%d | skin-build | LAM=0.5, KEEP_NET=1 | RUN#%d SKIN BUILD PASS: 76 faces in the piece (the edit region's content had 142), a valid solid | 0 | 300 |" % (i, i, i)
        def refrow(i): return "| 2026-10-19 13:%02d:00 | d%d | reinsert STEP=3 | STEP=3, TRIAL=the selftest's trial | REFUSAL#%d kit rebuild REFUSED: TRIAL STEP 3 continues the trial STEP 2 that sewed THIS piece, and there is none | 2 | - |" % (i, i, i)
        open(bl2, "w", encoding="utf-8").write("# BUILD LOG\n\n" + "\n".join([refrow(1), runrow(2), refrow(3), refrow(4), runrow(5), refrow(6), refrow(7), runrow(8), refrow(9)]) + "\n")
        out_r = run(root, "compact"); pre_r = out_r[:2048]
        check("3 runs + 6 refusals: the 3 RUNS listed and the 6 refusals COUNTED with the newest one's line, all inside the 2 KB preview; the older refusals not listed",
              all("RUN#%d SKIN BUILD PASS" % i in pre_r for i in (2, 5, 8)) and "6 refusal(s) (rc 2, the runner's) since 2026-10-19 13:01 (the log's first row)" in pre_r and "REFUSAL#9 kit rebuild REFUSED" in pre_r
              and not any("REFUSAL#%d " % i in out_r for i in (1, 3, 4, 6, 7)), [l for l in out_r.splitlines() if "RUN#" in l or "REFUSAL#" in l or "refusal(s)" in l])
        open(bl2, "w", encoding="utf-8").write("# BUILD LOG\n\n" + "\n".join([runrow(1), runrow(2), refrow(3), runrow(4), runrow(5), refrow(6), runrow(7), refrow(8), runrow(9), runrow(10), refrow(11)]) + "\n")
        out_r2 = run(root, "compact")
        check("7 runs + 4 refusals: the five newest RUNS listed (never the two older), the 3 refusals since the oldest row shown counted, inside the 2 KB preview",
              all("RUN#%d SKIN BUILD PASS" % i in out_r2[:2048] for i in (4, 5, 7, 9, 10)) and not any("RUN#%d SKIN" % i in out_r2 for i in (1, 2))
              and "3 refusal(s) (rc 2, the runner's) since 2026-10-19 13:04 (the oldest row shown)" in out_r2[:2048] and "REFUSAL#11 kit rebuild REFUSED" in out_r2[:2048],
              [l for l in out_r2.splitlines() if "RUN#" in l or "REFUSAL#" in l or "refusal(s)" in l])
        open(os.path.join(cc, "STATE_NOW.md"), "w", encoding="utf-8").write("# >>> UPDATE 2026-11-03 09:00\n* the wall is \u2265 0.8 mm \u2192 ok \u2014 said\n\n# >>> UPDATE 2026-10-18\n* old\n")
        _env1 = dict(os.environ)
        for _k1 in ("PYTHONUTF8", "PYTHONIOENCODING", "PYTHONLEGACYWINDOWSSTDIO"): _env1.pop(_k1, None)
        _p1 = subprocess.run([sys.executable, HOOK], input=json.dumps({"cwd": root, "source": "startup", "session_id": "selftest", "hook_event_name": "SessionStart"}).encode("utf-8"), capture_output=True, env=_env1)
        check("31bs K1: with no UTF-8 env the hook still exits 0 and its output decodes as UTF-8 with the pushed >= / -> / em dash intact (rc %s)" % _p1.returncode,
              _p1.returncode == 0 and "\u2265 0.8 mm \u2192 ok \u2014 said" in _p1.stdout.decode("utf-8", "strict"), _p1.stderr[-300:])
        # names no cwd
        _r2 = tempfile.mkdtemp(prefix="sstart_bad_"); os.makedirs(os.path.join(_r2, ".claude", "_leangates"))
        _pb = subprocess.run([sys.executable, HOOK], input="{not json", capture_output=True, text=True, cwd=_r2)
        _pc = subprocess.run([sys.executable, HOOK], input=json.dumps({"source": "startup", "session_id": "selftest", "hook_event_name": "SessionStart"}), capture_output=True, text=True, cwd=_r2)
        check("31bv TB1 F10: a payload that is not JSON, or one without a cwd, exits 0 with nothing on stdout, says so on stderr and writes nothing under the hook's own cwd",
              _pb.returncode == 0 and not _pb.stdout.strip() and "names no cwd" in _pb.stderr and _pc.returncode == 0 and not _pc.stdout.strip() and "names no cwd" in _pc.stderr
              and os.listdir(os.path.join(_r2, ".claude", "_leangates")) == [], (_pb.stdout + _pb.stderr + _pc.stdout + _pc.stderr)[-400:])
        shutil.rmtree(_r2, ignore_errors=True)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print()
    if FAILED: print("%d FAILED: %s" % (len(FAILED), ", ".join(FAILED))); return 1
    print("all cases pass. The post-compaction push comes first, the strike and the inbox at its top, the live job by its own name.")
    return 0
if __name__ == "__main__":
    sys.exit(main())

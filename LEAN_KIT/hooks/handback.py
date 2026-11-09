#!/usr/bin/env python3
"""SubagentStop hook: a worker may not finish while its newest job folder has a script but no RESULT.md, or a RESULT.md
without BOOKKEEPING and picture lines. Exit 2 = keep working, with the reason."""
import sys, json, os, glob, time
for _s_ in (sys.stdout, sys.stderr):      # transcript
    try: _s_.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
cwd = data.get("cwd", os.getcwd()); root = cwd
while root and not os.path.exists(os.path.join(root, ".claude")) and os.path.dirname(root) != root:
    root = os.path.dirname(root)
# recorded
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import liveness as _L; _L.beat(root, "handback", "ok")
except Exception:
    pass
jobs = sorted(glob.glob(os.path.join(root, "claude_code", "jobs", "J*")), key=os.path.getmtime)
if not jobs: sys.exit(0)
j = jobs[-1]
if time.time() - os.path.getmtime(j) > 3 * 3600: sys.exit(0)
scripts = glob.glob(os.path.join(j, "w_*.py")); res = os.path.join(j, "RESULT.md")
if scripts and not os.path.exists(res):
    sys.stderr.write("HANDBACK REFUSED: %s has a script but no RESULT.md (PARAMS, BOOKKEEPING lines, one line per picture, questions).\n" % j); sys.exit(2)
if os.path.exists(res):
    txt = open(res, encoding="utf-8", errors="replace").read(); up = txt.upper()
    if "BOOKKEEPING" not in txt and "QUESTION" not in up:
        sys.stderr.write("HANDBACK REFUSED: RESULT.md has no BOOKKEEPING line and no question.\n"); sys.exit(2)
    if "HIT" not in up and "MISS" not in up and "QUESTION" not in up:
        sys.stderr.write("HANDBACK REFUSED: RESULT.md has no picture lines (HIT/MISS per rendered picture).\n"); sys.exit(2)
sys.exit(0)

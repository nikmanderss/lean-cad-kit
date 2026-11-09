#!/usr/bin/env python3
"""selftest_mesh.py - `kit mesh`, the mesh route's runner, driven the way an orchestrator drives it (kit.py in a subprocess
on a throw-away project). Pinned:
  * --help lists every step and the gate tools;
  * a step needs the session open; `gate`, `slots` and --plan do not;
  * --plan fills CC_EXTENT from `kit atlas extent`'s record, writes the env record, runs nothing;
  * a CARD lever the run leaves unset is REFUSED by name (the census); a --set no script reads is refused;
  * a body-sized STL input is REFUSED (the crop flow) unless --whole-body "<why>", which the env record keeps;
  * a crop with its sidecar passes the gate; a gate tool runs under plain python with its positional args;
  * `kit mesh slots` reports free slots and never breaks a live one.

    & python "C:\\CAD\\LEAN_KIT\\kit\\selftest_mesh.py"
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_crop as KC
import kitlib_render as R
from selftest_crop import hollow_box

FAILED = []
NOWIN = 0x08000000 if os.name == "nt" else 0


def check(label, cond, detail=""):
    print("  %-4s %s" % ("ok" if cond else "FAIL", label))
    if not cond:
        print("       %s" % str(detail)[:500])
        FAILED.append(label)


def kit(root, *args):
    env = dict(os.environ); env["KIT_PROJECT"] = root; env["KIT_NO_INBOX"] = "1"
    p = subprocess.run([sys.executable, "-W", "ignore", os.path.join(HERE, "kit.py")] + list(args), capture_output=True, text=True,
                       env=env, cwd=os.path.join(root, "claude_code"), creationflags=NOWIN, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    root = tempfile.mkdtemp(prefix="kitmesh_")
    print("\nKIT MESH - the route's runner\n")
    try:
        work = os.path.join(root, "claude_code", "jobs", "J1", "work"); os.makedirs(work)
        os.makedirs(os.path.join(root, ".claude"))
        V, T = hollow_box()
        body = os.path.join(work, "body.stl"); R.write_stl(body, V, T)
        json.dump({"model": "x", "regions": {"top": {"box": [0, 100, 0, 60, 30, 40], "what_it_is": "the top"}},
                   "body_extent": {"box": [0, 100, 0, 60, 0, 40], "md5": "x", "model": "bank/x.brep"}},
                  open(os.path.join(root, "claude_code", "ATLAS.json"), "w"), indent=1)
        rc, out = kit(root, "mesh", "--help")
        check("--help lists the steps", rc in (0, 2) and "extract" in out and "_ccrefine.py" in out and "gate " in out, out[-400:])
        rc, out = kit(root, "crop", body, "--box", "40 60 20 40 30 42", "--margin", "3", "--out", os.path.join(work, "c.stl"))
        check("kit crop cuts the test body", rc == 0 and os.path.isfile(os.path.join(work, "c.crop.json")), out[-400:])
        crop = os.path.join(work, "c.stl")
        rc, out = kit(root, "mesh", "refine", "--job", "J1", "--tag", "T1", "--set", "CC_BODY=" + crop, "--set", "CC_BLOBS=x.npz",
                      "--set", "CC_DEV=0.08", "--set", "CC_OUT=" + os.path.join(work, "o.stl"))
        check("a step without an open session is refused", rc != 0 and ("session" in out.lower()), out[-400:])
        rc, out = kit(root, "mesh", "refine", "--job", "J1", "--tag", "T2", "--plan", "--set", "CC_BODY=" + crop, "--set", "CC_BLOBS=x.npz",
                      "--set", "CC_DEV=0.08", "--set", "CC_OUT=" + os.path.join(work, "o.stl"))
        check("--plan runs without a session", rc == 0, out[-500:])
        check("...fills CC_EXTENT from the atlas record", "CC_EXTENT = 0 100 0 60 0 40" in out, out[-500:])
        check("...writes the env record in work\\", os.path.isfile(os.path.join(work, "envT2.json")), os.listdir(work))
        rec = json.load(open(os.path.join(work, "envT2.json")))
        check("...which names where each lever came from", rec.get("_sources", {}).get("CC_EXTENT", "").startswith("filled"), rec.get("_sources"))
        check("...and says nothing ran", "nothing was run" in out, out[-300:])
        rc, out = kit(root, "mesh", "weld", "--job", "J1", "--tag", "T3", "--plan", "--set", "CC_BODY=" + crop, "--set", "CC_OUT=" + os.path.join(work, "w.stl"))
        check("a CARD lever left unset is REFUSED by name", rc == 2 and "REFUSED" in out and "CC_PATCH" in out and "CC_CORE_BLOB" in out, out[-500:])
        rc, out = kit(root, "mesh", "refine", "--job", "J1", "--tag", "T4", "--plan", "--set", "CC_NOPE=1", "--set", "CC_BODY=" + crop,
                      "--set", "CC_BLOBS=x.npz", "--set", "CC_DEV=0.08", "--set", "CC_OUT=" + os.path.join(work, "o.stl"))
        check("a --set no script reads is refused", rc == 2 and "CC_NOPE" in out, out[-400:])
        rc, out = kit(root, "mesh", "refine", "--job", "J1", "--tag", "T5", "--plan", "--set", "CC_BODY=" + body, "--set", "CC_BLOBS=x.npz",
                      "--set", "CC_DEV=0.08", "--set", "CC_OUT=" + os.path.join(work, "o.stl"))
        check("the whole body as CC_BODY is REFUSED", rc == 2 and "WHOLE BODY" in out, out[-500:])
        rc, out = kit(root, "mesh", "refine", "--job", "J1", "--tag", "T6", "--plan", "--whole-body", "the test says so", "--set", "CC_BODY=" + body,
                      "--set", "CC_BLOBS=x.npz", "--set", "CC_DEV=0.08", "--set", "CC_OUT=" + os.path.join(work, "o.stl"))
        check("...--whole-body \"<why>\" lets it through", rc == 0 and "WHOLE BODY" in out, out[-500:])
        rec = json.load(open(os.path.join(work, "envT6.json")))
        check("...and the reason is in the env record", rec.get("_whole_body_because") == "the test says so", rec)
        rc, out = kit(root, "mesh", "gate", "shells", "--job", "J1", "--tag", "T7", "--", crop)
        check("a gate tool runs with its positional args", rc == 0 and "shells" in out, out[-500:])
        check("...under plain python, not freecadcmd", "pure python" in out, out[-500:])
        rc, out = kit(root, "mesh", "slots")
        check("kit mesh slots reports", rc == 0 and "free" in out, out[-300:])
        rc, out = kit(root, "mesh", "slots", "--free", "0")
        check("...and refuses to free a slot nobody holds", rc == 2, out[-300:])
        rc, out = kit(root, "mesh", "nope", "--job", "J1", "--tag", "T8", "--plan")
        check("an unknown step is refused with the list", rc == 2 and "not a step" in out, out[-300:])
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print()
    if FAILED:
        print("%d FAILED:" % len(FAILED))
        for f in FAILED:
            print("  - " + f)
        return 1
    print("all cases pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

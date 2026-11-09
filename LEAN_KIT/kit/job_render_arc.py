#!/usr/bin/env python3
r"""job_render_arc.py — renders ONE SHARD of an orbit review. NO KERNEL. Safe to run N-up.

    KIT_HOME=<kit>  LK_CACHE_A=<tess_before.npz>  LK_CACHE_B=<tess_after.npz>
    LK_FRAMES='[["orbhi_000",[1,0,0.34]], ...]'   LK_OUT=<dir>  LK_SHARD=3
    LK_BOX="x0,x1,y0,y1,z0,z1"                    (the card's region — optional but wanted)
    & "<python or freecadcmd>" "<kit>\job_render_arc.py"

**THIS FILE MUST NEVER IMPORT `Part` AND MUST NEVER OPEN A `.brep`.** That is the whole reason it is
safe to run six at once: the ban that froze the machine on 2026-09-10 is on two KERNEL jobs against
one body, and a process holding only numpy arrays is not one. `job_tess_cache.py` did the kernel
work, once, alone. If this file ever grows an `import Part`, the parallelism becomes the old hazard
and the frames must go back to serial.

It renders **only the frames it is handed**, which is what makes the fan-out coverage-neutral: the
orchestrator shards a full sweep across N of these and every frame is still rendered and still
opened. the client, 2026-09-13: *"you should be gated to never be allowed to bypass full orbit reviews. I
don't care if you think it's wasteful it's absolutely not."* Nothing here renders fewer frames.

Every shard writes **its own tagged status file and its own log** — `status_arc<SHARD>.json`. An
untagged one is a shared mutable global between runs: on 2026-09-14 a waiter read a previous run's
terminal state out of `job_compare_pics.py`'s untagged `status_compare.json` and reported TIMEOUT on
a job that was working perfectly.
"""

import json
import os
import sys
import time

KIT = os.environ.get("KIT_HOME") or os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, KIT)
import numpy as np
import kitlib_render as R
sys.path.insert(0, os.path.join(os.environ.get("KIT_HOME", os.path.dirname(os.path.abspath(__file__))), "rebuild"))
import sk_lib as K

SHARD = os.environ.get("LK_SHARD", "0")
OUT = os.environ.get("LK_OUT") or os.getcwd()
BOX = os.environ.get("LK_BOX", "").strip()
W = int(os.environ.get("LK_W", "1400"))

ST = os.path.join(OUT, "status_arc%s.json" % SHARD)
st = {"state": "running", "shard": SHARD, "pid": os.getpid(),
      "started": time.strftime("%H:%M:%S"), "frames": [], "written": []}


def dump():
    try:
        os.makedirs(OUT, exist_ok=True)
        with open(ST, "w", encoding="utf-8") as fh:
            json.dump(st, fh, indent=1)
    except Exception:
        pass


def say(*a):
    print("[arc %s]" % SHARD, *a, flush=True)


dump()
t0 = time.time()
try:
    frames = json.loads(os.environ.get("LK_FRAMES", "[]"))
    if not frames:
        raise SystemExit("LK_FRAMES is empty - this shard was given nothing to render.")
    st["frames"] = [f[0] for f in frames]
    dump()

    VA, TA, _FA, metaA = R.load_tess_cache(os.environ["LK_CACHE_A"])
    VB, TB, _FB, metaB = R.load_tess_cache(os.environ["LK_CACHE_B"])
    st["cache"] = {"a": metaA.get("source", ""), "b": metaB.get("source", ""),
                   "tris_a": int(len(TA)), "tris_b": int(len(TB))}
    dump()

    box = None
    if BOX:
        n = [float(x) for x in BOX.split(",")]
        box = ((n[0], n[1]), (n[2], n[3]), (n[4], n[5]))

    _s = (os.environ.get("LK_SECTION") or "auto").strip().lower()
    if _s in ("auto", "", "none"):
        SECTION = "auto" if _s == "auto" else None
    else:
        _keep = "above" if _s.endswith("+") else "below"
        _ax, _rest = _s[0], _s.lstrip("xyz").rstrip("+")
        if _ax not in "xyz":
            raise SystemExit("LK_SECTION must be auto, none, or like z64 / y-192 / z64+")
        SECTION = (_ax, float(_rest), _keep)
        say("section: %s = %s, keeping what is %s" % (_ax, _rest, _keep))

    MODE = (os.environ.get("LK_MODE") or "after").lower()
    GREY = (0.62, 0.62, 0.65)
    if MODE == "overlay":
        say("overlay mode was removed on 2026-09-24 (two frame sets on one camera instead); rendering AFTER")
        MODE = "after"
    QA = metaA.get("quality") or {"tris": int(len(TA)), "defective": True, "defective_mesh": True, "why": "no mesh record in the cache (made before 31bn) - re-run the cache step", "why_mesh": "no mesh record in the cache"}
    QB = metaB.get("quality") or {"tris": int(len(TB)), "defective": True, "defective_mesh": True, "why": "no mesh record in the cache (made before 31bn) - re-run the cache step", "why_mesh": "no mesh record in the cache"}
    if MODE == "before":
        meshes, label = [(VA, TA, _FA, QA, GREY)], "BEFORE only"
    else:
        MODE = "after"
        meshes, label = [(VB, TB, _FB, QB, GREY)], "AFTER only"
    st["mode"] = MODE

    if box is not None:
        (x0, x1), (y0, y1), (z0, z1) = box
        focus = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], float)
    else:
        focus = np.vstack([VB])

    for name, d in frames:
        t1 = time.time()
        png = os.path.join(OUT, "%s.png" % name)
        stats = {}
        d3 = tuple(float(x) for x in d)
        clip = None
        if SECTION == "auto":
            if box is not None and d3[2] > 0.25:
                clip = ((0.0, 0.0, float(z0)), (0.0, 0.0, -1.0))
        elif SECTION:
            _ax, _val, _keep = SECTION
            _n = [0.0, 0.0, 0.0]
            _n["xyz".index(_ax)] = 1.0 if _keep == "below" else -1.0
            _p = [0.0, 0.0, 0.0]
            _p["xyz".index(_ax)] = _val
            clip = (tuple(_p), tuple(_n))
        _cut = ""
        K.view_meshes(R, png, meshes, d3, K.fbox_of(focus), W, name, "%s   %s%s" % (name, label, "   [CUT - capped]" if clip else ""),
                      ["The %s body opaque, smooth-shaded within each face; the quality line says how fine; a red RENDER DEFECTIVE banner across the frame = NO EVIDENCE." % MODE], clip=clip, stats=stats, subject_box=box)
        mmpx = stats.get("mmpx")
        if os.environ.get("LK_OWNERMAP", "") not in ("", "0"):
            try:
                np.save(png[:-4] + "_own.npy", stats.get("own"))
            except Exception as _e:
                print("   ownermap NOT saved: %s" % _e, flush=True)
        _c = stats.get("cut") or {}
        if clip and _c:
            _cut = "  [CUT: %d loop(s) capped, %d OPEN]" % (_c.get("closed", 0), _c.get("open", 0))
        rec = {"frame": name, "png": png, "secs": round(time.time() - t1, 1),
               "mm_per_px": round(float(mmpx or 0), 4), "clipped": bool(clip),
               "cut_loops_closed": _c.get("closed"), "cut_loops_open": _c.get("open"),
               "drawn_px": stats.get("drawn_px"), "subject_px": stats.get("subject_px")}
        _res = float(os.environ.get("LK_RESOLVE", "0") or 0)
        if _res > 0 and mmpx:
            _px = _res / float(mmpx)
            rec["judged_px"] = round(_px, 1)
            if _px < float(os.environ.get("LK_RESOLVE_PX", "8")):
                rec["look"] = "CANNOT-JUDGE"
                rec["why"] = ("the %.2f mm quantity spans %.1f px at %.4f mm/px - this frame cannot "
                              "show its failure" % (_res, _px, mmpx))
        if box is not None and stats.get("subject_px") is not None:
            tot = max(1, int(stats.get("drawn_px") or 1))
            frac = float(stats["subject_px"]) / tot
            rec["subject_frac"] = round(frac, 4)
            if rec.get("look") != "CANNOT-JUDGE":
                rec["look"] = "POOR" if frac < 0.02 else ("thin" if frac < 0.08 else "ok")
                _den = stats.get("box_drawn_px") if stats.get("box_drawn_px") is not None else stats.get("box_px")
                if rec["look"] == "POOR" and _den and (stats.get("occluded_px") or 0) >= 0.5 * _den:
                    rec["look"] = "OCCLUDED"; rec["occluded_px"] = int(stats["occluded_px"]); rec["box_px"] = int(_den); rec["box_footprint_px"] = int(stats.get("box_px") or 0)
                    rec["why"] = "the box lies behind the body's surface in this view (%d of %d of its drawn footprint covered by nearer surface) - this view cannot judge it; the frames that see it do" % (stats["occluded_px"], _den)
        st["written"].append(rec)
        dump()
        say("%-16s %5.1f s  %-13s%s" % (name, rec["secs"], rec.get("look", ""), _cut))

    poor = [r["frame"] for r in st["written"] if r.get("look") == "POOR"]
    thin = [r["frame"] for r in st["written"] if r.get("look") == "thin"]
    occl = [r["frame"] for r in st["written"] if r.get("look") == "OCCLUDED"]
    st["gates"] = {"frames": len(st["written"]), "poor": poor, "thin": thin, "occluded": occl,
                   "all_on_target": not poor}
    if occl:
        say("    %d frame(s) OCCLUDED - the box lies behind the body's surface in that view (a feature inside a closed solid; the client 2026-11-05: report it and use the views that work): %s" % (len(occl), ", ".join(occl)))
    if occl and not poor and len(occl) == len(st["written"]):
        poor = list(occl); say("*** every frame of this arc is occluded - nothing here can judge the card: a section (SECTION=...) or another arc")
    if poor:
        st.update({"state": "failed", "secs": round(time.time() - t0, 1),
                   "error": "%d frame(s) do not show the card: %s" % (len(poor), ", ".join(poor))})
        say("*** SHARD FAILED: %d frame(s) show under 2%% of the card - %s"
            % (len(poor), ", ".join(poor)))
        say("    Do NOT delete them and do NOT accept the sweep. Give those views a clip plane or")
        say("    a camera that can see the target, and re-render. A sweep with a hole is not a review.")
        say("    A ONE-SIDED feature (a blind pocket, a boss on one face) is in view from the far side only when the box holds the feature THROUGH the body:")
        say("    widen --box to the feature that HOLDS it - the subject is the box's pixels (31bt K3; the client 2026-11-05: review the larger feature, not the item alone).")
    else:
        st.update({"state": "done", "secs": round(time.time() - t0, 1), "n": len(st["written"])})
        say("%d frame(s) in %.1f s%s" % (len(st["written"]), time.time() - t0,
                                         ("  (%d thin)" % len(thin)) if thin else ""))
except BaseException as e:
    import traceback
    st.update({"state": "failed", "error": "%s: %s" % (type(e).__name__, e),
               "trace": traceback.format_exc()[-1200:], "secs": round(time.time() - t0, 1)})
    say("FAILED: %s: %s" % (type(e).__name__, e))
dump()
if st.get("state") == "failed": sys.exit(3)

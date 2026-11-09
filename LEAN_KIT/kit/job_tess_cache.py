#!/usr/bin/env python3
r"""job_tess_cache.py — THE ONLY KERNEL WORK IN AN ORBIT REVIEW. Runs ONCE, ALONE.

    KIT_HOME=<kit>  LK_SHAPES="before=<a.brep>;after=<b.brep>"  LK_OUT=<dir>
    LK_DEV=0.1  LK_TAG=_B21
    & "<freecadcmd>" "<kit>\job_tess_cache.py"

Tessellates each named shape a single time and writes `<out>\tess_<name><TAG>.npz` with the arrays
AND their provenance. Everything downstream — projection, raster, overlay, patch census — then runs
on those arrays with no FreeCAD in the process, which is what lets the frames be rendered six-up.

WHY THIS FILE EXISTS. Measured by the R19 orchestrator on 2026-09-14: a 29-frame review took over
NINE MINUTES on a ~4,500-face body, and only about ONE of those was kernel work. The rest was numpy,
serial for no reason at all.

**THE CONCURRENCY BAN IS ON THE KERNEL AND IT STANDS.** Two kernel jobs on one body froze the
machine on 2026-09-10. So this step — and only this step — runs alone, out of process, via
`lk_spawn`. Nothing here is parallel and nothing here should be made parallel.

DO NOT CHASE THE FLOOR BY LOWERING `LK_DEV`. A coarser mesh is a less honest picture, and the
picture is the instrument. The tessellation is the floor of a review's wall time and it is a floor
worth paying.
"""

import json
import os
import sys
import time

KIT = os.environ.get("KIT_HOME") or os.path.dirname(os.path.abspath(__file__))      # KeyError
sys.path.insert(0, KIT)
import numpy as np
import kitlib_render as R
import Part

TAG = os.environ.get("LK_TAG", "")
OUT = os.environ.get("LK_OUT") or os.getcwd()
DEV = float(os.environ.get("LK_DEV", "0.1"))
SHAPES = [s for s in os.environ.get("LK_SHAPES", "").split(";") if s.strip()]

ST = os.path.join(OUT, "status_tess_cache%s.json" % TAG)
st = {"state": "running", "started": time.strftime("%H:%M:%S"), "pid": os.getpid(),
      "dev": DEV, "shapes": {}}


def dump():
    try:
        os.makedirs(OUT, exist_ok=True)
        with open(ST, "w", encoding="utf-8") as fh:
            json.dump(st, fh, indent=1)
    except Exception:
        pass


def say(*a):
    print(*a, flush=True)


# MeshPart
# MeshPart
def _read_stl(path):
    """delegates - the reader lives in kitlib_render, which has no kernel dependency."""
    import kitlib_render as _R
    return _R.read_stl(path)


def _load_mesh_parts(paths):
    import kitlib_render as _R
    return _R.load_mesh_parts(paths)


dump()
t0 = time.time()
try:
    if not SHAPES:
        raise SystemExit('LK_SHAPES is empty. Give it "before=<a.brep>;after=<b.brep>", or '
                         '"after=<tool.stl+body.stl>" for a mesh result.')
    for spec in SHAPES:
        name, _, path = spec.partition("=")
        name, path = name.strip(), path.strip()
        parts = [q.strip() for q in path.split("+") if q.strip()]
        missing = [q for q in parts if not os.path.exists(q)]
        if not parts or missing:
            raise SystemExit("LK_SHAPES: %r does not exist (from %r)" % (missing or path, spec))
        if all(q.lower().endswith((".stl", ".ast")) for q in parts):
            t1 = time.time()
            V, T = _load_mesh_parts(parts)
            if len(T) == 0:
                raise SystemExit("%s: the mesh has 0 triangles (%s). That is the finding." % (name, path))
            out = os.path.join(OUT, "tess_%s%s.npz" % (name, TAG))
            sys.path.insert(0, os.path.join(KIT, "rebuild")); import sk_lib as K
            Qm = K.mesh_quality(np.asarray(V, float), np.asarray(T, int), np.zeros(len(T), int), closed=False, judge_open=False); Qm.update({"dev_mm": DEV, "how": "a mesh file"})
            R.save_tess_cache(out, V, T, np.zeros(len(T), np.int32), parts[0], DEV, quality=Qm)
            info = {"npz": out, "verts": int(len(V)), "tris": int(len(T)), "mesh": True,
                    "secs": round(time.time() - t1, 1), "source": " + ".join(parts),
                    "bbox": [[float(V[:, i].min()), float(V[:, i].max())] for i in range(3)]}
            st["shapes"][name] = info
            dump()
            say("MESH %-8s %7d tris from %d file(s)  %4.1f s  -> %s"
                % (name, len(T), len(parts), info["secs"], os.path.basename(out)))
            continue
        if len(parts) > 1:
            raise SystemExit("LK_SHAPES: '+' concatenation is for meshes; %r mixes or repeats "
                             "B-reps. Union them first (B.union) and pass the union." % spec)
        t1 = time.time()
        sh = Part.Shape()
        sh.importBrep(path)
        try:
            _ns = len(sh.Solids)
        except Exception:
            _ns = 1
        if _ns > 1:
            say("WARNING %s: %d SOLIDS in %s. If these are pieces that OVERLAP by design, this review will "
                "draw their intersections as seams and notches that are not there - union them first "
                "(B.union) and review the union. If they are separate features, say so in the verdict."
                % (name, _ns, os.path.basename(path)))
            st.setdefault("warnings", []).append("%s: %d solids" % (name, _ns))
        # MeshPart
        sys.path.insert(0, os.path.join(KIT, "rebuild")); import sk_lib as K
        V, T, FID, Q = K.piece_mesh(path, sh, cache_dir=OUT, say=say); V = np.asarray(V, float); T = np.asarray(T, int); FID = np.asarray(FID, int)
        if len(T) == 0:
            raise SystemExit(
                "%s TESSELLATED TO NOTHING (0 triangles) from %s.\n"
                "  That is the finding. Do not render, do not fuse, and do not treat any file "
                "already on disk for this tag as a product." % (name, path))
        out = os.path.join(OUT, "tess_%s%s.npz" % (name, TAG))
        R.save_tess_cache(out, V, T, FID, path, K.PIC_DEV, quality=Q)
        info = {"npz": out, "verts": int(len(V)), "tris": int(len(T)), "quality": {k_: Q.get(k_) for k_ in ("dev_mm", "ang_rad", "open_edges", "seams", "cracks", "dev_p99_mm", "nang_p99_deg", "defective", "why")},
                "secs": round(time.time() - t1, 1), "source": path,
                "bbox": [[float(V[:, i].min()), float(V[:, i].max())] for i in range(3)]}
        st["shapes"][name] = info
        dump()
        say("TESS %-8s %7d tris  %5.1f s  -> %s" % (name, len(T), info["secs"], os.path.basename(out)))
    st.update({"state": "done", "secs": round(time.time() - t0, 1)})
    say("TESS CACHE done in %.1f s - this is the whole of the kernel cost of the review." % (time.time() - t0))
    say("Render the frames with job_render_arc.py, which imports no Part and is safe N-up.")
except BaseException as e:
    import traceback
    st.update({"state": "failed", "error": "%s: %s" % (type(e).__name__, e),
               "trace": traceback.format_exc()[-1200:], "secs": round(time.time() - t0, 1)})
    say("TESS CACHE FAILED: %s: %s" % (type(e).__name__, e))
dump()
if st.get("state") == "failed": sys.exit(2)

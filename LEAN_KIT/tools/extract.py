# KIT INSTRUMENT `extract` - A REGION OF AN ASSEMBLY COPIED OUT, EVERY SOLID KEPT (31bw B4: a box of a 1,750-solid board assembly, the part set to design around).
# Run: kit tool extract --job <JOB> --set "BOX=x0 x1 y0 y1 z0 z1" [--set SHAPE=<.brep>] [--set OUT=<.brep>] [--set TRIM=1|0] [--set WHAT="<what this region is>"]
# Inputs: BOX (required - the region to copy out) SHAPE (default: the job's region.brep - the model of record's read-only link) OUT (default: <job>\extract_<HHMMSS>.brep)
#   TRIM (1, the default: a solid the box CUTS is trimmed to the box; 0: only the solids wholly inside the box, whole) WHAT (a caption for the record) CC_OUTDIR (the job folder).
# Writes OUT - one solid, or a compound of the kept solids - and prints the census (the shape named by its full path, never the job's link name - 31bw (TB6 F6): the full path): the solids wholly inside the box (kept whole), the ones the box cuts (trimmed or left out,
#   each with its volume inside the box), the ones outside (left out). It reads the shape and writes a NEW file; the model of record is never written and nothing is fused.
# Why an instrument: every kit boolean on a ONE-solid base keeps the largest solid (an edit never makes a second body) and the skin route edits one solid; since 31bw a compound
#   base keeps every solid, and this copies a region of an assembly out for the next job (`kit newjob <J> --from <OUT>`) or straight into a delivery (`kit deliver --add-body`).
import os, sys, time, Part, FreeCAD
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
def _fail(m): print(m if str(m).startswith("FAIL") else "FAIL: " + str(m), flush=True); raise SystemExit(1)
T0 = time.time()
raw = os.environ.get("BOX", "").replace(",", " ").split()
try: x0, x1, y0, y1, z0, z1 = [float(v) for v in raw]
except ValueError: _fail("FAIL: BOX is six numbers \"x0 x1 y0 y1 z0 z1\" - the region to copy out; got %r" % os.environ.get("BOX", ""))
if not (x1 > x0 and y1 > y0 and z1 > z0): _fail("FAIL: BOX is x0 x1 y0 y1 z0 z1 with each max above its min; got %r" % (raw,))
_base = os.environ.get("CC_OUTDIR") or os.getcwd()
SHAPE = os.environ.get("SHAPE", "") or os.path.join(_base, "region.brep")
if not os.path.isfile(SHAPE): _fail("FAIL: no shape at %s (SHAPE=<brep>, or run in a job made by `kit newjob --from` the assembly)" % SHAPE)
OUT = os.environ.get("OUT", "") or os.path.join(_base, "extract_%s.brep" % time.strftime("%H%M%S"))
TRIM = os.environ.get("TRIM", "1").strip().lower() not in ("0", "false", "no")
WHAT = os.environ.get("WHAT", "").strip()
sh = Part.Shape(); sh.importBrep(SHAPE); sols = sh.Solids
print("extract: %s - %d solid(s), %d faces, %.0f mm3 (%.0fs); the box x %g..%g y %g..%g z %g..%g" % (SHAPE, len(sols), len(sh.Faces), sh.Volume, time.time() - T0, x0, x1, y0, y1, z0, z1), flush=True)
try:
    import json as _json
    _jr = _json.load(open(os.path.join(_base, "JOB.json"), encoding="utf-8")) if not os.environ.get("SHAPE", "") and os.path.isfile(os.path.join(_base, "JOB.json")) else {}
    if _jr.get("base"): print("   (the job's copy of %s - %s)" % (_jr["base"], _jr.get("how") or "copied"), flush=True)
except Exception: pass
if not sols: _fail("FAIL: %s holds no solid - nothing to copy out" % SHAPE)
bx = Part.makeBox(x1 - x0, y1 - y0, z1 - z0, FreeCAD.Vector(x0, y0, z0))
inside, cut, outside, kept = [], [], [], []
for i, s in enumerate(sols):
    bb = s.BoundBox
    if bb.XMin >= x0 - 1e-6 and bb.XMax <= x1 + 1e-6 and bb.YMin >= y0 - 1e-6 and bb.YMax <= y1 + 1e-6 and bb.ZMin >= z0 - 1e-6 and bb.ZMax <= z1 + 1e-6:
        inside.append(i); kept.append(s); continue
    if bb.XMax < x0 or bb.XMin > x1 or bb.YMax < y0 or bb.YMin > y1 or bb.ZMax < z0 or bb.ZMin > z1:
        outside.append(i); continue
    c = s.common(bx)
    if c.Volume > 1e-6:
        cut.append((i, s.Volume, c.Volume))
        if TRIM: kept.extend(c.Solids)
    else:
        outside.append(i)
print("extract: %d solid(s) wholly inside the box (kept whole), %d cut by the box (%s), %d outside (left out)"
      % (len(inside), len(cut), ("trimmed to the box - TRIM=1" if TRIM else "LEFT OUT - TRIM=0; TRIM=1 trims them to the box"), len(outside)), flush=True)
for i, v, cv in cut[:20]: print("   solid %d: %.1f mm3, %.1f of it inside the box" % (i, v, cv), flush=True)
if len(cut) > 20: print("   ... %d more cut solid(s)" % (len(cut) - 20), flush=True)
if not kept: _fail("FAIL: nothing of %s lies in the box %s - the box is wrong, or TRIM=0 left out every solid the box cuts" % (SHAPE, " ".join(raw)))
res = kept[0] if len(kept) == 1 else Part.makeCompound(kept)
res.exportBrep(OUT)
print("extract: %d solid(s), %d faces, %.0f mm3 -> %s%s (%.0fs)" % (len(res.Solids), len(res.Faces), res.Volume, OUT, (" - %s" % WHAT) if WHAT else "", time.time() - T0), flush=True)
print("  Next: `kit newjob <J> --from \"%s\"` for an edit on the part (every boolean keeps its solids - 31bw B4); `kit deliver --add-body` puts it in the document as it is." % OUT, flush=True)

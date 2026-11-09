# voxel step is now getting skipped
# kit rebuild  skin-source
# ORIGINAL  content.brep
# source.stl
# skin-labels  skin-features
# skin-wires
# source.stl  REBUILD_source.json
# skin-labels
import os, sys, json, time, hashlib, math
if not globals().get("_SK_INNER"):      # 31br D3 (2026-10-29): a crash's TRACEBACK reaches the log
    import runpy as _rp3, traceback as _tb3
    try: _rp3.run_path(os.path.abspath(__file__), init_globals={"_SK_INNER": True}, run_name="__main__")
    except SystemExit: raise
    except BaseException:
        print("TRACEBACK (31br D3) - the crash's place:\n" + _tb3.format_exc(), flush=True); raise
    raise SystemExit(0)
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8")
    except Exception: pass
import numpy as np
import Part
from FreeCAD import Vector as V3
sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sk_lib as K; RUN = K.RUN
T0 = time.time()
TESS = float(os.environ.get("TESS", "0.05") or 0.05); ANG = float(os.environ.get("ANG", "5") or 5); MIN_A = float(os.environ.get("MIN_A", "1e-6") or 1e-6)
TAG = os.environ.get("LK_TAG", "src")


def say(s): print("%5.0fs  %s" % (time.time() - T0, s), flush=True)


src = os.path.join(RUN, "content.brep")
if not os.path.isfile(src):
    print("FAIL: %s is missing - the region step writes it (kit rebuild region first)" % src, flush=True); sys.exit(1)
s = Part.Shape(); s.importBrep(src)
say("the edit region's original content: %d face(s), %d solid(s), volume %.1f mm3" % (len(s.Faces), len(s.Solids), s.Volume))
V = None; T = None; FID = None; how = ""
# ORIGINAL  MeshPart
# skin-labels
try:
    import MeshPart
    try:
        m = MeshPart.meshFromShape(Shape=s, LinearDeflection=TESS, AngularDeflection=math.radians(ANG), Relative=False, Segments=True)
        segs = [np.array(m.getSegment(i), int) for i in range(m.countSegments())]
    except TypeError:
        m = MeshPart.meshFromShape(Shape=s, LinearDeflection=TESS, AngularDeflection=math.radians(ANG), Relative=False); segs = []
    pts = np.array([[p.x, p.y, p.z] for p in m.Points], float); fac = np.array([list(f.PointIndices) for f in m.Facets], int)
    V, T = pts, fac; how = "MeshPart (linear %.3f mm, angular %.1f deg)" % (TESS, ANG)
    if len(segs) == len(s.Faces) and sum(len(x) for x in segs) == len(fac):
        FID = np.full(len(fac), -1, np.int64)
        for i, x in enumerate(segs):
            if len(x): FID[x] = i
        how += ", the face of every triangle from the mesher's segments"
    else:
        say("the mesher gave %d segments for %d faces (%d facets in them of %d) - the face of each triangle found by its nearest face sample instead"
            % (len(segs), len(s.Faces), sum(len(x) for x in segs), len(fac)))
except Exception as ex:
    say("MeshPart not usable (%s) - Part.tessellate at %.3f mm" % (str(ex)[:60], TESS))
    V_, T_, fid_ = R.tess_shape(s, TESS); V, T = np.asarray(V_, float), np.asarray(T_, int); FID = np.asarray(fid_, np.int64); how = "Part.tessellate (%.3f mm), the face of every triangle from it" % TESS
if FID is None or (FID < 0).any():
    from scipy.spatial import cKDTree
    VO, TO, FO = R.tess_shape(s, 0.01); VO = np.asarray(VO, float); TO = np.asarray(TO, int); FO = np.asarray(FO, int)
    Sp = np.vstack([VO[TO].mean(axis=1), VO[TO].reshape(-1, 3)]); Sf = np.concatenate([FO, np.repeat(FO, 3)])
    _, nn = cKDTree(Sp).query(V[T].mean(axis=1), workers=-1)
    near = Sf[nn]
    FID = near if FID is None else np.where(FID < 0, near, FID)
    how += ", triangles given to their nearest face"
Vu, F = K.weld(V, T)
P = Vu[F]; a2 = np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1) * 0.5
keep = (a2 > MIN_A) & (F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])
F = F[keep]; FID = FID[keep]
# skin-build
# skin-labels
body = Part.Shape(); body.importBrep(K.BODY); BFb = body.Faces
MAP_TOL = float(os.environ.get("MAP_TOL", "0.06") or 0.06)
bb_b = np.array([[g.BoundBox.XMin, g.BoundBox.XMax, g.BoundBox.YMin, g.BoundBox.YMax, g.BoundBox.ZMin, g.BoundBox.ZMax] for g in BFb], float)
from scipy.spatial import cKDTree
sel = [j for j, g in enumerate(BFb) if not (g.BoundBox.XMax < K.WIN[0] - 1 or g.BoundBox.XMin > K.WIN[1] + 1 or g.BoundBox.YMax < K.WIN[2] - 1
       or g.BoundBox.YMin > K.WIN[3] + 1 or g.BoundBox.ZMax < K.WIN[4] - 1 or g.BoundBox.ZMin > K.WIN[5] + 1)]
VO, TO, FO = R.tess_shape(body, 0.01, faces=sel); FO = np.asarray(sel)[np.asarray(FO)]
kd = cKDTree(np.asarray(VO, float)[np.asarray(TO)].mean(axis=1))
cen_t = Vu[F].mean(1); c2b = np.full(len(s.Faces), -1, np.int64); unmapped = []
for i, f in enumerate(s.Faces):
    tri = np.nonzero(FID == i)[0]
    if not len(tri): continue
    samp = cen_t[tri[np.unique(np.linspace(0, len(tri) - 1, min(6, len(tri))).astype(int))]]
    _, nn = kd.query(samp, k=min(48, len(FO)), workers=-1)
    cands = dict.fromkeys(int(x) for x in np.asarray(FO)[np.asarray(nn).ravel()].tolist())
    best = None
    for j in cands:
        g = BFb[j]; worst = 0.0; ok = True
        for q in samp:
            try:
                u_, w_ = g.Surface.parameter(V3(*q))
                if not g.isPartOfDomain(u_, w_): ok = False; break
                worst = max(worst, (g.Surface.value(u_, w_) - V3(*q)).Length)
            except Exception:
                ok = False; break
        if ok and worst < MAP_TOL and (best is None or worst < best[0]): best = (worst, j)
    if best is None:
        lo = samp.min(0) - 2.0; hi = samp.max(0) + 2.0
        near = np.nonzero((bb_b[:, 1] >= lo[0]) & (bb_b[:, 0] <= hi[0]) & (bb_b[:, 3] >= lo[1]) & (bb_b[:, 2] <= hi[1]) & (bb_b[:, 5] >= lo[2]) & (bb_b[:, 4] <= hi[2]))[0]
        for j in near:
            try: dj = max(BFb[int(j)].distToShape(Part.Vertex(V3(*q)))[0] for q in samp[:3])
            except Exception: continue
            if dj < MAP_TOL and (best is None or dj < best[0]): best = (dj, int(j))
    if best is not None: c2b[i] = best[1]
    else: unmapped.append(i)
# REBUILD_region.json
try:
    walls_ = list(K.WALLS)
except Exception:
    walls_ = []
is_wall = np.zeros(len(s.Faces), bool)
for i in unmapped:
    c_ = s.Faces[i].CenterOfMass; q_ = np.array([c_.x, c_.y, c_.z])
    is_wall[i] = any(abs(q_ @ np.asarray(n_, float) - float(c0_)) < 0.15 for n_, c0_ in walls_)
odd = [i for i in unmapped if not is_wall[i]]
FID_BODY = np.where(c2b[FID] >= 0, c2b[FID], -1000000 - FID)
out = os.path.join(RUN, "source.stl")
R.write_stl(out, Vu, F)
smd5 = hashlib.md5(open(out, "rb").read()).hexdigest(); cmd5 = hashlib.md5(open(src, "rb").read()).hexdigest()
np.savez_compressed(os.path.join(RUN, "source_fid.npz"), fid=FID_BODY, fid_content=FID, content_to_body=c2b, source_md5=np.array(smd5), content_md5=np.array(cmd5))
say("the content's %d faces -> the body's: %d mapped, %d walls (the caps), %d on NO body face%s" % (len(s.Faces), int((c2b >= 0).sum()), int(is_wall.sum()), len(odd),
    (" - faces %s: not pieces of the body? they will be absorbed by their neighbours unless a point lands on them" % odd[:10]) if odd else ""))
rec = {"tag": TAG, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "content_md5": cmd5, "source_md5": smd5, "triangles": int(len(F)), "vertices": int(len(Vu)),
       "faces": len(s.Faces), "faces_with_triangles": int(len(np.unique(FID))), "body_faces_mapped": int((c2b >= 0).sum()), "wall_faces": int(is_wall.sum()),
       "unmapped_faces": odd, "how": how, "TESS": TESS, "ANG": ANG, "dropped_degenerate": int((~keep).sum()), "seconds": round(time.time() - T0, 1)}
json.dump(rec, open(os.path.join(RUN, "REBUILD_source.json"), "w", encoding="utf-8"), indent=1)
say("SOURCE -> source.stl + source_fid.npz: %d triangles, %d vertices from the original's %d faces (%s; %d degenerate dropped) - the mesh every skin step"
    " lays its points, layout, frame and network on, MADE ONCE (remade only when content.brep changes). THE VOXEL FIELD IS SHELVED (the client 2026-10-08): the"
    " original's faces are the start - what is kept is the agent's pick (skin-points: a face with no point is absorbed), the geometry is corrected in"
    " the WIREFRAME (skin-wires)." % (len(F), len(Vu), len(s.Faces), how, int((~keep).sum())))
say("next: kit rebuild reinsert --set STEP=1 (the caps), then skin-regions -> skin-edges -> skin-points -> skin-labels -> skin-features -> skin-layout")
print("DONE", flush=True)

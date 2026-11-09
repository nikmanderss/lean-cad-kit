# kit rebuild
# content.brep  content_base.stl
# content_base.stl
import os, sys, json, time
if not globals().get("_SK_INNER"):      # 31br D3 (2026-10-29): a crash's TRACEBACK reaches the log
    import runpy as _rp3, traceback as _tb3
    try: _rp3.run_path(os.path.abspath(__file__), init_globals={"_SK_INNER": True}, run_name="__main__")
    except SystemExit: raise
    except BaseException:
        print("TRACEBACK (31br D3) - the crash's place:\n" + _tb3.format_exc(), flush=True); raise
    raise SystemExit(0)
import numpy as np
import Part
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sk_lib as K; RUN = K.RUN; K.need_window()
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from PIL import ImageDraw

T_HI = float(os.environ.get("T_HI", "0.15")); T_LO = float(os.environ.get("T_LO", "0.04"))
A_MIN = float(os.environ.get("A_MIN", "1.0")); WALL_MM = float(os.environ.get("WALL_MM", "0.6")); WALL_CLIP = float(os.environ.get("WALL_CLIP", "1.5"))
SK = K.SK; os.makedirs(SK, exist_ok=True)
OUT = K.OUT
T0 = time.time()
def say(*a): print("%5.0fs " % (time.time() - T0), *a, flush=True)

VP, TP = R.read_stl(K.STL); VP = VP.astype(float)
Vu, F = K.weld(VP, TP)
if K.brep_source():
    # no region
    # skin-source
    fid = K.source_fid(len(F))
    if fid is None: K._fail("FAIL: source_fid.npz is not this mesh's (%d triangles) - run `kit rebuild skin-source` again (content.brep changed?)" % len(F))
    d = np.zeros(len(Vu)); inside = np.zeros(len(Vu), bool); vreg = np.full(len(Vu), -1)
    np.savez_compressed(os.path.join(SK, "regions.npz"), Vu=Vu, F=F, d=d, inside=inside, vreg=vreg, fid=fid)
    json.dump({"brep_source": True, "T_HI": T_HI, "T_LO": T_LO, "A_MIN": A_MIN, "WALL_MM": WALL_MM, "WALL_CLIP": WALL_CLIP, "regions": []},
              open(os.path.join(SK, "regions.json"), "w"), indent=1)
    say("B-REP SOURCE (31bb): the mesh IS the original (%d triangles on %d original faces) - no changed region to find, no pictures; the mesh record written"
        " for the skin steps (skin\\regions.npz, with the original face of every triangle). What is kept is the pick: skin-points (a face with no point is"
        " absorbed by its neighbours) and the wireframe (a line left as it is keeps its faces; a line redrawn re-spans them)." % (len(F), len(np.unique(fid[fid >= 0]))))
    print("DONE", flush=True); sys.exit(0)
VC, TC, _orig_src = K.orig_mesh(R, Part)   # content_base.stl  content.brep
say("voxel piece: %d triangles, %d welded vertices; original content %d triangles" % (len(F), len(Vu), len(TC)))
d = np.zeros(len(Vu))
for i0 in range(0, len(Vu), 20000):
    d[i0:i0 + 20000] = R.point_tri_dist(Vu[i0:i0 + 20000], VC, TC)
say("vertex distances: p50 %.3f p90 %.3f p99 %.3f max %.2f mm; over T_LO %.2f: %d, over T_HI %.2f: %d"
    % (np.median(d), np.percentile(d, 90), np.percentile(d, 99), d.max(), T_LO, int((d > T_LO).sum()), T_HI, int((d > T_HI).sum())))
wdv = K.wall_dist(Vu)
cand = (d > T_LO) & (wdv > WALL_CLIP)
inside = np.zeros(len(Vu), bool); inside[cand] = R.points_inside(Vu[cand], VC, TC)
E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
E = E[cand[E[:, 0]] & cand[E[:, 1]]]
n = len(Vu)
G = coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(n, n))
ncomp, lab = connected_components(G, directed=False)
lab = np.where(cand, lab, -1)
seed_comps = np.unique(lab[(d > T_HI) & cand])
A_t = 0.5 * np.linalg.norm(np.cross(Vu[F[:, 1]] - Vu[F[:, 0]], Vu[F[:, 2]] - Vu[F[:, 0]]), axis=1)
lt = lab[F]
tri_lab = np.full(len(F), -1)
for k in range(3):
    same = (lt[:, k] >= 0) & (((lt[:, k] == lt[:, (k + 1) % 3])) | (lt[:, k] == lt[:, (k + 2) % 3]))
    tri_lab = np.where((tri_lab < 0) & same, lt[:, k], tri_lab)
sO = Part.Shape(); sO.importBrep(K.BODY); facesO = sO.Faces
sel = [i for i, f in enumerate(facesO) if not (f.BoundBox.XMax < K.WIN[0] - 1 or f.BoundBox.XMin > K.WIN[1] + 1 or f.BoundBox.YMax < K.WIN[2] - 1
       or f.BoundBox.YMin > K.WIN[3] + 1 or f.BoundBox.ZMax < K.WIN[4] - 1 or f.BoundBox.ZMin > K.WIN[5] + 1)]
VO, TO, FO = R.tess_shape(sO, 0.01, faces=sel); FO = np.asarray(sel)[FO]
Sp = np.vstack([VO[TO].mean(axis=1), VO[TO].reshape(-1, 3)]); Sf = np.concatenate([FO, np.repeat(FO, 3)])
kd = cKDTree(Sp)
say("original edit region faces: %d, %d triangles sampled" % (len(sel), len(TO)))
regions = []; vreg = np.full(n, -1)
for c in seed_comps:
    vm = lab == c; tm = tri_lab == c
    area = float(A_t[tm].sum())
    vidx = np.nonzero(vm)[0]
    wd = float(K.wall_dist(Vu[vidx]).min())
    added = int((~inside[vidx]).sum()); removed = int(inside[vidx].sum())
    _, nn = kd.query(Vu[vidx], workers=-1); fids = Sf[nn]
    fu, fc = np.unique(fids, return_counts=True)
    rec = {"comp": int(c), "verts": int(vm.sum()), "tris": int(tm.sum()), "area_mm2": round(area, 2), "d_max": round(float(d[vidx].max()), 3),
           "added_frac": round(added / max(len(vidx), 1), 3), "wall_mm": round(wd, 2), "centre": [round(float(v), 2) for v in Vu[vidx].mean(axis=0)],
           "bbox": [round(float(v), 2) for v in np.concatenate([Vu[vidx].min(axis=0), Vu[vidx].max(axis=0)])],
           "orig_faces": [int(x) for x in fu[np.argsort(-fc)]], "orig_face_counts": [int(x) for x in fc[np.argsort(-fc)]]}
    rec["status"] = "noise" if area < A_MIN else ("wall" if (wd < WALL_MM and WALL_CLIP <= 0) else "remake")
    near = vidx[wdv[vidx] < WALL_CLIP + 0.5]
    rec["clipped_at_wall"] = bool(len(near)); rec["d_at_clip_max"] = round(float(d[near].max()), 3) if len(near) else 0.0
    regions.append(rec)
regions.sort(key=lambda r: -r["area_mm2"])
rid = 0
for r in regions:
    if r["status"] == "remake":
        r["id"] = rid; vreg[lab == r["comp"]] = rid; rid += 1
    else: r["id"] = None
nre = sum(1 for r in regions if r["status"] == "remake")
say("regions: %d seeded; REMAKE %d (%.0f mm2), wall %d (%.0f mm2), noise %d (%.1f mm2)" % (len(regions), nre,
    sum(r["area_mm2"] for r in regions if r["status"] == "remake"), sum(1 for r in regions if r["status"] == "wall"),
    sum(r["area_mm2"] for r in regions if r["status"] == "wall"), sum(1 for r in regions if r["status"] == "noise"),
    sum(r["area_mm2"] for r in regions if r["status"] == "noise")))
for r in regions:
    if r["status"] != "noise":
        say("  %-6s id %-4s %7.1f mm2  d_max %.2f  added %3.0f %%  wall %.1f mm%s  centre %s  bbox %s  on %d original faces" % (r["status"], r["id"], r["area_mm2"], r["d_max"],
            100 * r["added_frac"], r["wall_mm"], ("  CLIPPED at a wall, voxel %.2f off there" % r["d_at_clip_max"]) if r.get("clipped_at_wall") else "", r["centre"], r["bbox"], len(r["orig_faces"])))
np.savez_compressed(os.path.join(SK, "regions.npz"), Vu=Vu, F=F, d=d, inside=inside, vreg=vreg)
json.dump({"T_HI": T_HI, "T_LO": T_LO, "A_MIN": A_MIN, "WALL_MM": WALL_MM, "WALL_CLIP": WALL_CLIP, "regions": regions}, open(os.path.join(SK, "regions.json"), "w"), indent=1)

treg = np.full(len(F), -1); lt2 = vreg[F]
for k in range(3):
    same = (lt2[:, k] >= 0) & ((lt2[:, k] == lt2[:, (k + 1) % 3]) | (lt2[:, k] == lt2[:, (k + 2) % 3]))
    treg = np.where((treg < 0) & same, lt2[:, k], treg)
wallt = np.zeros(len(F), bool)
for r in regions:
    if r["status"] == "wall": wallt |= tri_lab == r["comp"]
C = np.tile(np.array(K.VOX), (len(F), 1))
for i in range(nre): C[treg == i] = K.PALETTE[i % len(K.PALETTE)]
C[wallt] = (0.55, 0.55, 0.60)
try: EC = json.load(open(os.path.join(K.EDGEMAP, "edge_classes.json")))
except (OSError, ValueError): EC = []
runs = [np.array(rr, float) for r in EC for rr in r["runs"]]
cen = {r["id"]: np.array(r["centre"]) for r in regions if r["status"] == "remake"}
def draw(dr, proj):
    for rr in runs: dr.line(proj(rr), fill=(60, 200, 230), width=1)
    for i, c in cen.items():
        x, y = proj(c[None, :])[0]; t = "R%d" % i
        dr.rectangle([x - 2, y - 2, x + 9 * len(t), y + 18], fill=(0, 0, 0)); dr.text((x, y), t, fill=(255, 255, 255), font=K.F16)
leg = [(tuple(int(255 * v) for v in K.PALETTE[i % len(K.PALETTE)]), "R%d" % i) for i in range(min(nre, 12))]
leg += [((140, 140, 153), "at an edit region wall - not remade"), (tuple(int(255 * v) for v in K.VOX), "voxel = original"), ((60, 200, 230), "original B-rep edges")]
for i, (nm, dv, fb, W, ttl) in enumerate(K.views()):
    K.view(R, os.path.join(OUT, "SP1_%02d_regions_%s.png" % (i + 1, nm)), Vu, F, dv, fb, W, ttl,
           "SP1.%02d  THE CHANGED REGIONS (voxel vs original) - %s" % (i + 1, ttl),
           ["Each colour is one region where the voxel differs from the original (seeded where it is more than %.2f mm off, grown out to where it is" % T_HI,
            "within %.2f mm again, so the outline sits where the two surfaces meet). Each region becomes ONE new face; the rest stays the original's faces." % T_LO,
            "Regions are clipped %.1f mm inside the edit region walls (the body is the original's there). Regions under %.1f mm2 are noise and dropped." % (WALL_CLIP, A_MIN)],
           draw=draw, C=C, legend=leg)
    say("SP1_%02d written" % (i + 1))
print("DONE", flush=True)

# kit rebuild
# over the
import os, sys, json, time, math
if not globals().get("_SK_INNER"):      # 31br D3 (2026-10-29): a crash's TRACEBACK reaches the log
    import runpy as _rp3, traceback as _tb3
    try: _rp3.run_path(os.path.abspath(__file__), init_globals={"_SK_INNER": True}, run_name="__main__")
    except SystemExit: raise
    except BaseException:
        print("TRACEBACK (31br D3) - the crash's place:\n" + _tb3.format_exc(), flush=True); raise
    raise SystemExit(0)
import numpy as np
import Part, FreeCAD
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
from PIL import Image, ImageDraw, ImageFont

PHASE = os.environ.get("EDGE_PHASE", "both")
TANGENT_DEG = float(os.environ.get("TANGENT_DEG", "10"))
TINY_MM = float(os.environ.get("TINY_MM", "0.5"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sk_lib as K; RUN = K.RUN; K.need_window()
_BREP0 = K.brep_source()
OUT = os.path.join(K.OUT, "edgemap")
RAW = K.EDGEMAP
for d_ in (OUT, RAW): os.makedirs(d_, exist_ok=True)
T0 = time.time()
def say(*a): print("%5.0fs " % (time.time() - T0), *a, flush=True)
V3 = FreeCAD.Vector
WIN = K.WIN; inwin = K.inwin

VP, TP = R.read_stl(K.STL); VP = VP.astype(float)
sO = Part.Shape(); sO.importBrep(K.BODY)
sV = K.frozen_surfaces(Part)
say("loaded: the mesh %d triangles; the body %d faces; frozen surfaces (the atlas, keep_frozen.json) %d faces" % (len(TP), len(sO.Faces), len(sV.Faces) if sV is not None else 0))

if PHASE in ("classify", "both"):
    EDGES = []
    allE = sO.Edges
    # ancestorsOfType
    # content.brep
    _by_hash = {}
    for _fi, _f in enumerate(sO.Faces):
        for _e in _f.Edges: _by_hash.setdefault(_e.hashCode(), []).append(_fi)
    _faces_of = lambda e_: [sO.Faces[i_] for i_ in dict.fromkeys(_by_hash.get(e_.hashCode(), []))]
    _cp = os.path.join(RUN, "content.brep"); sIN = sO
    if os.path.isfile(_cp):
        try:
            sIN = Part.Shape(); sIN.importBrep(_cp)
        except Exception:
            sIN = sO
    for ei, e in enumerate(allE):
        bb = e.BoundBox
        if bb.XMax < WIN[0] or bb.XMin > WIN[1] or bb.YMax < WIN[2] or bb.YMin > WIN[3] or bb.ZMax < WIN[4] or bb.ZMin > WIN[5]:
            continue
        try: pts = np.array([[p.x, p.y, p.z] for p in e.discretize(Number=max(2, int(e.Length / 0.05) + 1))])
        except Exception: continue
        m = inwin(pts, 0.0)
        if not m.any(): continue
        runs = []; run = []
        for p, k in zip(pts, m):
            if k: run.append(p)
            elif len(run) > 1: runs.append(np.array(run)); run = []
            else: run = []
        if len(run) > 1: runs.append(np.array(run))
        if not runs: continue
        L_in = sum(float(np.linalg.norm(np.diff(r, axis=0), axis=1).sum()) for r in runs)
        longest = max(runs, key=lambda r: len(r)); pm = longest[len(longest) // 2]
        faces = _faces_of(e)
        rec = {"idx": ei, "runs": runs, "length_in": L_in, "nfaces": len(faces), "angle": None, "cls": None, "frozen": False, "pm": pm}
        if len(faces) == 2:
            ns = []
            for f in faces:
                try:
                    u, v = f.Surface.parameter(V3(*pm)); n = f.normalAt(u, v); ns.append(np.array([n.x, n.y, n.z]))
                except Exception: ns.append(None)
            if ns[0] is not None and ns[1] is not None:
                c = float(np.clip(ns[0] @ ns[1], -1, 1)); ang = math.degrees(math.acos(c)); rec["angle"] = ang
                if ang < TANGENT_DEG: rec["cls"] = "smooth"
                else:
                    d = ns[0] - ns[1]; nd = np.linalg.norm(d)
                    q = pm + 0.05 * d / nd if nd > 1e-9 else pm
                    try: inside = sIN.isInside(V3(*q), 1e-4, True)
                    except Exception: inside = None
                    rec["cls"] = "concave" if inside else ("convex" if inside is not None else "other")
        if rec["cls"] is None: rec["cls"] = "other"
        if L_in < TINY_MM: rec["cls"] = "tiny"
        EDGES.append(rec)
        if len(EDGES) % 50 == 0: say("classified %d edges" % len(EDGES))
    if sV is None:
        for r in EDGES: r["frozen"] = False; r["d_vane"] = None
        say("no frozen region meets the edit region (keep_frozen.json): no edge is frozen")
    else:
        vfaces = sV.Faces
        vsel = [i for i, f in enumerate(vfaces) if not (f.BoundBox.XMax < WIN[0] - 1 or f.BoundBox.XMin > WIN[1] + 1 or f.BoundBox.YMax < WIN[2] - 1
                or f.BoundBox.YMin > WIN[3] + 1 or f.BoundBox.ZMax < WIN[4] - 1 or f.BoundBox.ZMin > WIN[5] + 1)]
        VV, TV, _ = R.tess_shape(sV, 0.01, faces=vsel)
        dv = R.point_tri_dist(np.array([r["pm"] for r in EDGES]), VV, TV)
        for r, dd in zip(EDGES, dv):
            r["frozen"] = bool(dd < 0.02); r["d_vane"] = float(dd)
            if r["frozen"] and r["cls"] != "tiny": r["cls_geom"] = r["cls"]; r["cls"] = "frozen"
        say("frozen surfaces in the edit region: %d faces, %d triangles; frozen edges %d" % (len(vsel), len(TV), sum(1 for r in EDGES if r["frozen"])))
    SEL = lambda r: r["cls"] in ("convex", "smooth")
    counts = {}
    for r in EDGES: counts[r["cls"]] = counts.get(r["cls"], 0) + 1
    lens = {}
    for r in EDGES: lens[r["cls"]] = lens.get(r["cls"], 0.0) + r["length_in"]
    say("edges in the edit region: %d - %s" % (len(EDGES), ", ".join("%s %d (%.0f mm)" % (k, counts[k], lens[k]) for k in sorted(counts))))
    say("selected for measurement (convex + smooth, not tiny): %d edges, %.0f mm of edge" % (sum(1 for r in EDGES if SEL(r)), sum(r["length_in"] for r in EDGES if SEL(r))))
    json.dump([{k: (v if k not in ("runs", "pm") else ([[[round(float(x), 4) for x in p] for p in rr] for rr in v] if k == "runs" else [round(float(x), 4) for x in v])) for k, v in r.items()} for r in EDGES],
              open(os.path.join(RAW, "edge_classes.json"), "w"))

BG = (0.13, 0.14, 0.17); VOX = (0.80, 0.62, 0.42); ALPHA = 0.20
COL = {"frozen": (90, 140, 255), "convex": (60, 230, 255), "smooth": (170, 255, 140), "concave": (255, 150, 40),
       "tiny": (140, 140, 140), "other": (255, 80, 200)}
WID = {"frozen": 2, "convex": 3, "smooth": 3, "concave": 2, "tiny": 1, "other": 2}
LBL = {"convex": "crisp outside edge" + ("" if _BREP0 else " - MEASURED"), "smooth": "tangent join" + ("" if _BREP0 else " - MEASURED"), "concave": "inside corner (a blend is decided there)" + ("" if _BREP0 else " - not measured"),
       "frozen": "frozen edge (an atlas region) - kept by rule", "tiny": "sliver edge under %.1f mm" % TINY_MM + ("" if _BREP0 else " - not measured"), "other": "not two faces" + ("" if _BREP0 else " - not measured")}
def font(sz):
    for nm in ("arialbd.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try: return ImageFont.truetype(nm, sz)
        except Exception: pass
    return ImageFont.load_default()
F16, F22 = font(16), font(22)
def corners(b):
    return np.array([[x, y, z] for x in (b[0], b[1]) for y in (b[2], b[3]) for z in (b[4], b[5])], float)
def render_transparent(V, T, d, foc, W, pad, C=None):
    d3, r3, u3 = R.basis(d)
    fx = foc @ r3; fy = foc @ u3
    x0, x1 = fx.min() - pad, fx.max() + pad; y0, y1 = fy.min() - pad, fy.max() + pad
    mmpx = (x1 - x0) / W; H = int(np.ceil((y1 - y0) / mmpx))
    X = (V @ r3 - x0) / mmpx; Y = (y1 - V @ u3) / mmpx
    P = V[T]; n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]); ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1; n = n / ln[:, None]
    light = -d3 + 0.5 * u3 + 0.35 * r3; light = light / np.linalg.norm(light)
    sh = 0.30 + 0.70 * np.abs(n @ light); col = np.array(VOX)
    Ct = np.tile(col, (len(T), 1)) if C is None else np.asarray(C, float)
    acc = np.zeros((H, W, 3)); wsum = np.zeros((H, W)); trans = np.ones((H, W))
    XT = X[T]; YT = Y[T]
    xa_ = np.clip(np.floor(XT.min(axis=1)).astype(int), 0, W - 1); xb_ = np.clip(np.ceil(XT.max(axis=1)).astype(int), 0, W - 1)
    ya_ = np.clip(np.floor(YT.min(axis=1)).astype(int), 0, H - 1); yb_ = np.clip(np.ceil(YT.max(axis=1)).astype(int), 0, H - 1)
    for i in range(len(T)):
        xa, xb, ya, yb = xa_[i], xb_[i], ya_[i], yb_[i]
        (x1_, x2_, x3_), (y1_, y2_, y3_) = XT[i], YT[i]
        den = (y2_ - y3_) * (x1_ - x3_) + (x3_ - x2_) * (y1_ - y3_)
        if abs(den) < 1e-12: continue
        gx = np.arange(xa, xb + 1)[None, :] + 0.5; gy = np.arange(ya, yb + 1)[:, None] + 0.5
        w0 = ((y2_ - y3_) * (gx - x3_) + (x3_ - x2_) * (gy - y3_)) / den
        w1 = ((y3_ - y1_) * (gx - x3_) + (x1_ - x3_) * (gy - y3_)) / den
        ins = (w0 >= 0) & (w1 >= 0) & (1.0 - w0 - w1 >= 0)
        if not ins.any(): continue
        sa = acc[ya:yb + 1, xa:xb + 1]; sw = wsum[ya:yb + 1, xa:xb + 1]; st_ = trans[ya:yb + 1, xa:xb + 1]
        sa[ins] += Ct[i] * sh[i] * ALPHA; sw[ins] += ALPHA; st_[ins] *= (1.0 - ALPHA)
    hit = wsum > 0
    mean = np.zeros_like(acc); mean[hit] = acc[hit] / wsum[hit][:, None]
    cov = (1.0 - trans)[..., None]
    img = mean * cov + np.array(BG)[None, None, :] * (1.0 - cov)
    edge = np.zeros((H, W), bool); edge[:, 1:] |= hit[:, 1:] != hit[:, :-1]; edge[1:, :] |= hit[1:, :] != hit[:-1, :]
    img[edge] = np.array(VOX) * 0.9
    return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)), mmpx, x0, y1, r3, u3

def view(name, d, fbox, W, title, head, lines, draw, C=None, legend=None):
    foc = corners(fbox); pad = 1.0
    gb = (fbox[0] - 4, fbox[1] + 4, fbox[2] - 4, fbox[3] + 4, fbox[4] - 4, fbox[5] + 4)
    m = K._clip_mask(VP, TP, gb)
    im, mmpx, x0, y1, r3, u3 = render_transparent(VP, TP[m], d, foc, W, pad, None if C is None else C[m])
    dr = ImageDraw.Draw(im)
    proj = lambda P: [tuple(v) for v in np.stack([(P @ r3 - x0) / mmpx, (y1 - P @ u3) / mmpx], axis=1)]
    draw(dr, proj)
    dr.rectangle([0, 0, im.width, 18], fill=(0, 0, 0)); dr.text((4, 2), "%s   [%s]" % (title, R.axes_label(r3, u3)), fill=(255, 255, 80))
    bar = 10.0 / mmpx; dr.line([10, im.height - 12, 10 + bar, im.height - 12], fill=(255, 255, 255), width=3)
    dr.text((12, im.height - 30), "10 mm  (%.3f mm/px)" % mmpx, fill=(255, 255, 255))
    out = Image.new("RGB", (im.width, im.height + 40 + 26 * 3 + 24 * len(lines) + 10), (16, 16, 20))
    od = ImageDraw.Draw(out); od.text((10, 8), head, fill=(255, 235, 120), font=F22); out.paste(im, (0, 40))
    y = im.height + 46; x = 10
    for colr, t in (legend or [(COL[k], LBL[k]) for k in ("convex", "smooth", "frozen", "concave", "tiny", "other")]):
        tw = od.textbbox((0, 0), t, font=F16)[2]
        if x + 30 + tw > out.width - 10: y += 26; x = 10
        od.rectangle([x, y + 3, x + 22, y + 19], fill=colr); od.text((x + 30, y + 2), t, fill=(235, 235, 235), font=F16); x += 44 + tw
    y += 30
    for ln in lines:
        od.text((10, y), ln, fill=(235, 235, 235), font=F16); y += 24
    out.save(os.path.join(OUT, name + ".png"))
    say("%s written" % name)

def draw_classes(dr, proj):
    for k in ("tiny", "other", "concave", "frozen", "smooth", "convex"):
        for r in EDGES:
            if r["cls"] != k: continue
            for rr in r["runs"]: dr.line(proj(rr), fill=COL[k], width=WID[k])

VIEWS = K.views()
if PHASE in ("classify", "both"):
    for i, (nm, d, fb, W, ttl) in enumerate(VIEWS):
        view("1_%02d_classes_%s" % (i + 1, nm), d, fb, W, ttl, "1.%02d  THE ORIGINAL'S EDGES BY CLASS (from the B-rep) ON THE SOURCE MESH - %s" % (i + 1, ttl),
             ["Which original edges START as the layout's borders: crisp outside edges and tangent joins (cyan, green); inside corners (orange) are where a blend is decided",
              "in the wireframe (a fillet line). Frozen edges (blue, the atlas's regions) are kept by rule. On a B-rep source nothing is measured against a voxel (the field is shelved - 31ba)."],
             draw_classes)
    say("phase classify done: %s" % sorted(f for f in os.listdir(OUT) if f.startswith("1_")))
if PHASE in ("measure", "both"):
    ON_MM = float(os.environ.get("ON_MM", "0.10"))
    E = json.load(open(os.path.join(RAW, "edge_classes.json")))
    for r in E:
        r["runs"] = [np.array(rr, float) for rr in r["runs"]]
        if r["cls"] == "frozen" and r.get("cls_geom") == "concave": r["cls"] = "concave"
    MEAS = [r for r in E if r["cls"] in ("convex", "smooth") or (r["cls"] == "frozen" and r.get("cls_geom") in ("convex", "smooth"))]
    if K.brep_source(): say("edges by class on a B-REP SOURCE: nothing is measured against a voxel (the field is shelved) - %d crisp / tangent edges, %d frozen" % (len(MEAS), sum(1 for r in MEAS if r["cls"] == "frozen")))
    else: say("measured edges: %d (%d frozen, checked only); not measured: %d inside corners, %d slivers, %d other"
        % (len(MEAS), sum(1 for r in MEAS if r["cls"] == "frozen"), sum(1 for r in E if r["cls"] == "concave"), sum(1 for r in E if r["cls"] == "tiny"),
           sum(1 for r in E if r["cls"] == "other")))
    for r in MEAS:
        r["samp"] = []
        for rr in r["runs"]:
            L = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(rr, axis=0), axis=1))])
            sx = np.linspace(0.0, L[-1], max(2, int(L[-1] / 0.25) + 1))
            r["samp"].append(np.stack([np.interp(sx, L, rr[:, k]) for k in range(3)], axis=1))
    allp = np.vstack([q for r in MEAS for q in r["samp"]])
    BREP_SRC = K.brep_source()
    if BREP_SRC:
        dd = np.zeros(len(allp)); say("   B-rep source: every measured edge is ON the mesh by construction - no distance taken (the voxel-era measure skipped)")
    else:
        dd = R.point_tri_dist(allp, VP, TP)
    k0 = 0
    for r in MEAS:
        r["d"] = []
        for q in r["samp"]:
            r["d"].append(dd[k0:k0 + len(q)]); k0 += len(q)
    if not BREP_SRC:
        say("selected points measured: %d (0.25 mm apart) - on the voxel (<= %.2f mm) %d, off it %d; p50 %.3f p90 %.3f max %.2f mm"
            % (len(allp), ON_MM, int((dd <= ON_MM).sum()), int((dd > ON_MM).sum()), float(np.median(dd)), float(np.percentile(dd, 90)), float(dd.max())))
    for grp in (() if BREP_SRC else ("convex", "smooth", "frozen")):
        sel = [r for r in MEAS if r["cls"] == grp]
        if not sel: continue
        d_ = np.concatenate([x for r in sel for x in r["d"]])
        say("   %-7s %3d edges: on %.0f %% of their points, off %.0f %%" % (grp, len(sel), 100.0 * (d_ <= ON_MM).mean(), 100.0 * (d_ > ON_MM).mean()))
    # content_base.stl  content.brep
    # content_base.stl
    cP = VP[TP].mean(axis=1); d2 = np.zeros(len(cP))
    if BREP_SRC:
        say("   B-rep source (31bb): the mesh is the original - nothing added, nothing removed; every measured edge is on it")
        VC = TC = None
    else:
        VC, TC, _src_ = K.orig_mesh(R, Part); VC = VC.astype(float)
        for i0 in range(0, len(cP), 20000):
            d2[i0:i0 + 20000] = R.point_tri_dist(cP[i0:i0 + 20000], VC, TC)
            say("   mesh vs original: %d of %d triangles compared" % (min(i0 + 20000, len(cP)), len(cP)))
    chg = d2 > ON_MM
    ins = np.zeros(len(cP), bool)
    if chg.any(): ins[chg] = R.points_inside(cP[chg], VC, TC)
    added = chg & ~ins; removed = chg & ins
    A = 0.5 * np.linalg.norm(np.cross(VP[TP][:, 1] - VP[TP][:, 0], VP[TP][:, 2] - VP[TP][:, 0]), axis=1)
    if not BREP_SRC:
        say("voxel surface: %.0f mm2 in all; unchanged (within %.2f mm of the original) %.0f mm2; ADDED material over the original %.0f mm2; REMOVED %.0f mm2"
            % (A.sum(), ON_MM, A[~chg].sum(), A[added].sum(), A[removed].sum()))
    np.savez_compressed(os.path.join(RAW, "edge_measure.npz"), d2=d2, added=added, removed=removed)
    json.dump([{"idx": r["idx"], "cls": r["cls"], "cls_geom": r.get("cls_geom"), "on_frac": float(np.mean(np.concatenate(r["d"]) <= ON_MM)),
                "d_max": float(np.concatenate(r["d"]).max())} for r in MEAS], open(os.path.join(RAW, "edge_measure.json"), "w"), indent=0)
    CV = np.tile(np.array(VOX), (len(TP), 1)); CV[added] = (0.95, 0.30, 0.85); CV[removed] = (0.95, 0.25, 0.20)
    G_ON, Y_OFF, B_ON, W_OFF, DIM = (90, 255, 110), (255, 230, 40), (90, 140, 255), (255, 255, 255), (110, 110, 120)
    MEAS_IDS = set(id(r) for r in MEAS)
    def draw_map(dr, proj):
        for r in E:
            if id(r) in MEAS_IDS: continue
            for rr in r["runs"]: dr.line(proj(rr), fill=DIM, width=1)
        for r in MEAS:
            fz = r["cls"] == "frozen"
            for q, d_ in zip(r["samp"], r["d"]):
                pp = proj(q)
                for k in range(len(pp) - 1):
                    on = d_[k] <= ON_MM and d_[k + 1] <= ON_MM
                    dr.line([pp[k], pp[k + 1]], fill=((B_ON if on else W_OFF) if fz else (G_ON if on else Y_OFF)), width=3)
    LEG = [(G_ON, "original edge ON the voxel - a boundary that stays"), (Y_OFF, "measured edge the voxel has LEFT"),
           (B_ON, "frozen edge on the voxel"), (W_OFF, "frozen edge the voxel has left"), (DIM, "not measured (inside corner, sliver)"),
           ((242, 76, 217), "voxel ADDS material here"), ((242, 64, 51), "voxel REMOVES material here"), (tuple(int(255 * v) for v in VOX), "voxel = original (unchanged)")]
    for i, (nm, d, fb, W, ttl) in enumerate([] if BREP_SRC else VIEWS):
        view("2_%02d_map_%s" % (i + 1, nm), d, fb, W, ttl, "2.%02d  THE BOUNDARY EDGE MAP - measured original edges + where the voxel changed the shape - %s" % (i + 1, ttl),
             ["Original edges measured against the voxel at selected points only (every 0.25 mm on crisp outside edges, tangent joins and frozen edges): green = still",
              "on the voxel within %.2f mm (that boundary stays), yellow = the voxel left it. The voxel itself is coloured where it differs from the original: magenta =" % ON_MM,
              "material added (fills, fillets), red = material removed - their outlines are the new boundaries that fill in the rest of the map."],
             draw_map, C=CV, legend=LEG)
    say("phase measure done")
print("DONE", flush=True)

r"""kit_dossier - MEASURE ONCE, KEEP IT, MARK IT STALE WHEN AN APPLIED JOB TOUCHES IT.

the client, 2026-09-10, on the orchestrator's 27 measuring calls for zero edits: "MASSIVE waste ...
One overall measurement at the start of edits that is kept in a file and flagged as changed as
work is approved, only updated if measurements are available or retaken. Allow for measurements
per section to fill back in the file."

So: a DOSSIER is one named box on the model of record with everything a card needs, taken in ONE
kernel call — N zoomed sections along the box's long axis, each with its material profile (the
outer/inner numbers per station), the faces census in the box (count, faces under 0.30 mm²), and
the standard boxed frames. It lives under claude_code\dossier\<name>\ with an index
DOSSIER.json that carries the model-of-record hash it was measured on.

  kit dossier take <name> --box x0 x1 y0 y1 z0 z1 [--axis x|y|z] [--stations 3] [--step 1]
                          [--views std|all] [--no-frames] [--no-faces] [--from <brep>]
  kit dossier list                       every dossier: FRESH / STALE (by which job) / model changed /
                                         PARTIAL; UNCHECKED before `kit open` (nothing to compare against)
  kit dossier add <name> --what "..." --value "..." --source "<script, render or file>" [--png <file>]
                                         FILE A NUMBER YOU ALREADY HAVE - no kernel call, no re-measure
  kit dossier show <name> [--faces]      the numbers, without the kernel: profiles, faces, files
  kit dossier refresh <name> [--only sections|faces|frames]   re-take on the current model of record
  kit dossier unstale <name> --because "..."   clear a STALE mark when the model of record did NOT change (an
                                         apply that was never promoted); refused if the model hash moved
  kit measure ... --dossier <name>       any measurement FILLS BACK into the dossier (text + png)
  kit before <job> --dossier <name>      the dossier's frames are the job's BEFORE set (no re-render)

A card names the dossier it was written from (`Dossier:` slot); `kit job` refuses a card whose
dossier is missing or STALE. `kit apply` marks every dossier whose box intersects the applied
job's box STALE — the others stay valid even though the model of record changed (their box was
not touched). Nothing is deleted: a stale dossier is refreshed, and its old files stay beside it.
"""
import os, sys, json, time, hashlib, shutil, re

DIR = os.path.join("claude_code", "dossier")
INDEX = "DOSSIER.json"


def index_path(root):
    return os.path.join(root, DIR, INDEX)
def load(root):
    try:
        with open(index_path(root), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}
def save(root, idx):
    os.makedirs(os.path.join(root, DIR), exist_ok=True)
    tmp = index_path(root) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(idx, fh, indent=1)
    os.replace(tmp, index_path(root))
def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")
def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()
def boxes_intersect(a, b):
    a = [float(x) for x in a]; b = [float(x) for x in b]
    return not (a[1] < b[0] or b[1] < a[0] or a[3] < b[2] or b[3] < a[2] or a[5] < b[4] or b[5] < a[4])


def status(root, name, model=None):
    """('missing'|'fresh'|'stale'|'valid-model-changed', entry)."""
    e = (load(root) or {}).get(name)
    if not e:
        return "missing", None
    if e.get("partial"):
        return "partial", e
    if e.get("defined_only") and not e.get("added"):
        return "defined", e
    if e.get("stale"):
        return "stale", e
    if model and os.path.exists(model):
        try:
            if e.get("model_hash") and file_hash(model) != e["model_hash"]:
                return "valid-model-changed", e
        except OSError:
            pass
    return "fresh", e


def mark_stale(root, job, box):
    """Called by `kit apply`: every dossier whose box meets the applied job's box goes STALE."""
    idx = load(root); hit = []
    try:
        box = [float(t) for t in str(box).split()]
    except (ValueError, AttributeError):
        return hit
    if len(box) != 6:
        return hit
    for name, e in idx.items():
        if not e.get("stale") and boxes_intersect(e.get("box", [0] * 6), box):
            e["stale"] = {"by": job, "when": now()}; hit.append(name)
    if hit:
        save(root, idx)
        print("[dossier] STALE after %s applied: %s — `kit dossier refresh <name>` before the next "
              "card on that box." % (job, ", ".join(hit)))
    return hit


def add(root, name, cmd_text, out_text, png=None):
    """A measurement taken with --dossier <name> fills back into the dossier."""
    idx = load(root); e = idx.get(name)
    if not e:
        print("[dossier] no dossier %r — the measurement was not filed. `kit dossier list`." % name)
        return False
    d = os.path.join(root, e["dir"]); os.makedirs(d, exist_ok=True)
    kept = None
    if png and os.path.exists(png):
        kept = os.path.join(d, "added_%02d_%s" % (len(e.get("added", [])) + 1, os.path.basename(png)))
        try:
            shutil.copyfile(png, kept)
        except OSError:
            kept = None
    e.setdefault("added", []).append({"when": now(), "cmd": cmd_text, "png": kept,
                                      "text": (out_text or "")[-6000:]})
    save(root, idx)
    print("[dossier] filed into %s (added #%d%s)" % (name, len(e["added"]), ", picture kept" if kept else ""))
    return True


_TAKE = r'''
import sys, os, json, time, hashlib; sys.path.insert(0, __HERE__); import kitlib as K, numpy as np
t0 = time.time()
src = __SRC__; s = K.load(src); bx = __BOX__; ax = __AX__; au, av = [i for i in (0, 1, 2) if i != ax]
box3 = ((bx[0], bx[1]), (bx[2], bx[3]), (bx[4], bx[5]))
out = __OUT__; name = __NAME__; tol = __TOL__; max_st = __MAXST__
rep = {"sections": [], "profiles": {}, "faces": None, "frames": [], "reads": "tessellation, dev 0.05 mm (rays read the kernel)"}
# ONE tessellation per model of record: cached by file hash under the PROJECT's claude_code/jobs/_tess_cache,
# shared with kit check (it was <kit>/../jobs since the 09-14 unification - the master's folder; 2026-09-17)
def _tess_cached(path, shape):
    p = None
    try:
        h = hashlib.md5(open(path, "rb").read()).hexdigest()
        d = os.path.join(__ROOT__, "claude_code", "jobs", "_tess_cache"); os.makedirs(d, exist_ok=True)
        p = os.path.join(d, h + ".npz")
        if os.path.exists(p):
            z = np.load(p); print("DOSSIER tessellation from cache", flush=True); return z["V"], z["T"], z["FID"]
    except Exception as e:
        p = None; print("DOSSIER note: tessellation cache unavailable (%s)" % e, flush=True)
    Vx, Tx, Fx = K.tess(shape)
    if p:
        try: np.savez_compressed(p, V=Vx, T=Tx, FID=Fx)
        except Exception as e: print("DOSSIER note: tessellation not cached (%s)" % e, flush=True)
    return Vx, Tx, Fx
V, T, F = _tess_cached(src, s)
print("DOSSIER tessellated %d triangles, %.0f s" % (len(T), time.time() - t0), flush=True)
win = ((bx[2 * au], bx[2 * au + 1]), (bx[2 * av], bx[2 * av + 1]))
step = __STEP__
Pax = V[T][:, :, ax] if len(T) else np.zeros((0, 3))
def station(c):
    segs = K.R.section_segs(V, T, ax, float(c))
    if not len(segs):
        print("DOSSIER station %s=%.2f: no section in the box plane - skipped (31bx R1 F3)" % ("xyz"[ax], c), flush=True); return None
    onplane = int(np.sum(np.all(np.abs(Pax - c) < 1e-6, axis=1))) if len(T) else 0
    png = os.path.join(out, "%s_sec_%s%.2f.png" % (name, "xyz"[ax], c))
    mmpx = K.R.draw_section_filled(png, [(segs, (150, 150, 160))], [(segs, (240, 240, 240), 1)], ax,
                                   "%s section %s = %.2f" % (name, "xyz"[ax], c), W=1200, window=win, grid=1.0)
    A = segs[:, 0, :]; B = segs[:, 1, :]; prof = []; tops = []; bots = []
    u = win[0][0]
    while u <= win[0][1] + 1e-9:
        if len(segs):
            lo = np.minimum(A[:, au], B[:, au]); hi = np.maximum(A[:, au], B[:, au])
            m = (lo <= u) & (hi > u) & (hi - lo > 1e-9)
            t = (u - A[m, au]) / (B[m, au] - A[m, au])
            v = np.sort(A[m, av] + t * (B[m, av] - A[m, av]))[::-1]
        else:
            v = np.zeros(0)
        pairs = []
        for i in range(0, len(v) - 1, 2):
            h, l = float(v[i]), float(v[i + 1])
            if h < win[1][0] or l > win[1][1]:
                continue
            pairs.append([round(min(h, win[1][1]), 3), round(max(l, win[1][0]), 3), bool(h > win[1][1]), bool(l < win[1][0])])
        prof.append([round(float(u), 3), pairs])
        tops.append(pairs[0][0] if pairs else np.nan); bots.append(pairs[-1][1] if pairs else np.nan)
        u += step
    if onplane:
        print("DOSSIER WARNING: %d triangles lie IN the plane %s=%.2f - a face is coincident with it and the filled picture may show a false band; offset the station by 0.2" % (onplane, "xyz"[ax], c), flush=True)
    return {"c": float(c), "png": png, "mmpx": float(mmpx), "onplane": onplane}, prof, np.array(tops, float), np.array(bots, float)
done = {}
def take_station(c):
    _r = station(c)
    if _r is None: return      # 31bx (R1 F3): a station whose section is empty is no station (31bx R1 F3)
    sec, prof, tops, bots = _r
    rep["sections"].append(sec); rep["profiles"]["%s=%.2f" % ("xyz"[ax], c)] = prof; done[float(c)] = (tops, bots)
    print("DOSSIER section %s=%.2f -> %s (%.3f mm/px), %d stations profiled" % ("xyz"[ax], c, sec["png"], sec["mmpx"], len(prof)), flush=True)
# 31bx (R1 F3): a station in the AIR holds no material - skipped and said; every station empty = the wrong axis, refused by name (a box over a face with air above had crashed on the empty section)
# 31ca (R1 F1): THE MATERIAL TEST IS BY TRIANGLES - the 31bx form looked for the mesh's VERTICES inside the box's window, and a flat face's interior has none (a plain plate was
# refused on every axis): a triangle meets the box when its bounding box overlaps it and the separating-axis test finds no separating axis; a station is KEPT when its plane lies within the SPAN,
# along the axis, of the triangles that meet the box (31ca 2b: a plane through the INSIDE of a solid meets no surface triangle there - the per-station surface test had skipped every station
# of a plate along z), SKIPPED outside it (in the air) and said; an axis with no kept station is refused naming --axis.
# >>> 31ca R1 F1 THE MATERIAL TEST
def _tri_meets_box(P_, lo, hi, eps=1e-9):
    """which triangles of P_ (n, 3, 3) meet the axis-aligned box lo..hi - the separating-axis test on the box's three axes, the triangle's normal and the nine edge x axis cross products"""
    P_ = np.asarray(P_, float)
    if not len(P_): return np.zeros(0, bool)
    lo = np.asarray(lo, float); hi = np.asarray(hi, float); c_ = (lo + hi) / 2.0; h_ = (hi - lo) / 2.0 + eps; v_ = P_ - c_
    ok_ = np.all((v_.min(1) <= h_) & (v_.max(1) >= -h_), axis=1)
    E_ = [v_[:, 1] - v_[:, 0], v_[:, 2] - v_[:, 1], v_[:, 0] - v_[:, 2]]
    def _sep(a_):
        p_ = np.einsum("nij,nj->ni", v_, a_); r_ = (np.abs(a_) * h_).sum(1)
        return (p_.min(1) > r_) | (p_.max(1) < -r_)
    ok_ &= ~_sep(np.cross(E_[0], E_[1]))
    for e_ in E_:
        for k_ in range(3):
            u_ = np.zeros(3); u_[k_] = 1.0; ok_ &= ~_sep(np.cross(np.broadcast_to(u_, e_.shape), e_))
    return ok_
def _material_stations(V_, T_, bx_, ax_, stations_):
    """the stations whose plane lies within the span (along the axis) of the triangles that meet the box (kept), those outside it (skipped), the material's span along the axis inside the box
    (None: no triangle meets the box) and the number of triangles that meet it"""
    lo = np.array([bx_[0], bx_[2], bx_[4]], float); hi = np.array([bx_[1], bx_[3], bx_[5]], float)
    P3 = np.asarray(V_, float)[np.asarray(T_, int)] if len(T_) else np.zeros((0, 3, 3))
    m_ = np.all((P3.min(1) <= hi + 1e-6) & (P3.max(1) >= lo - 1e-6), axis=1) if len(P3) else np.zeros(0, bool)
    Pc = P3[m_]; Pc = Pc[_tri_meets_box(Pc, lo, hi)] if len(Pc) else Pc
    rng_ = (max(float(Pc[:, :, ax_].min()), float(lo[ax_])), min(float(Pc[:, :, ax_].max()), float(hi[ax_]))) if len(Pc) else None
    keep_, skip_ = [], []
    for c_ in stations_:      # 31ca 2b: the station's plane within the span of the triangles that meet the box - inside a solid too
        (keep_ if (rng_ is not None and rng_[0] - 1e-6 <= c_ <= rng_[1] + 1e-6) else skip_).append(c_)
    return keep_, skip_, rng_, int(len(Pc))
# <<< 31ca R1 F1 THE MATERIAL TEST
try:
    _st0, _skip, _rng, _ntri = _material_stations(V, T, bx, ax, list(__STATIONS__))
    print("DOSSIER material: %d triangle(s) of the model meet the box%s (31ca R1 F1: the test is by triangles)" % (_ntri, (" - along %s it spans %.2f..%.2f" % ("xyz"[ax], _rng[0], _rng[1])) if _rng else ""), flush=True)
except Exception as _emt:
    print("DOSSIER note: the material test did not run (%s) - every station is taken; a station whose section is empty is skipped by itself" % _emt, flush=True)
    _st0, _skip, _rng, _ntri = list(__STATIONS__), [], None, -1
if _skip and _rng is not None: print("DOSSIER: station(s) %s=%s hold no material (the body spans %s %.2f..%.2f inside the box; the station's plane lies outside the span of the triangles that meet the box) - skipped (31bx R1 F3)" % ("xyz"[ax], [round(c, 2) for c in _skip], "xyz"[ax], _rng[0], _rng[1]), flush=True)
if __STATIONS__ and not _st0:
    print("FAIL: DOSSIER REFUSED - no station along %s crosses material inside the box (the body spans %s %s inside it; %d triangle(s) of the model meet the box): name the axis the box's material runs along - kit dossier take ... --axis <x|y|z> (31bx R1 F3)" % ("xyz"[ax], "xyz"[ax], ("%.2f..%.2f" % _rng) if _rng else "nothing", max(_ntri, 0)), flush=True); raise SystemExit(1)
for c in _st0:
    take_station(c)
# ADAPTIVE: where two neighbouring sections differ by more than tol anywhere along u, a station goes
# between them, until every pair agrees or max_st is reached. Simple geometry costs three sections;
# a spine or a seam costs what it needs. (the client: "intelligently take less measurements on planes and
# places where geometry is not complicated".)
def _diff(a, b):
    ta, ba = done[a]; tb, bb = done[b]
    if len(ta) != len(tb):
        return 0.0
    with np.errstate(invalid="ignore"):
        d = np.nanmax(np.abs(np.concatenate([ta - tb, ba - bb]))) if len(ta) else 0.0
    return float(d) if np.isfinite(d) else 0.0
# A STEP IS NOT A SLOPE (2026-09-24). Two stations that still disagree once they are closer than `min_gap` sit either
# side of a real feature edge; bisecting further finds the edge to a millimetre and costs a section each time (the
# launch test: one aft step bisected five times, ten extra sections, 122 s). Such a pair is recorded as a STEP, not
# refined, and the loop moves to the next pair.
_span = max(abs(__STATIONS__[-1] - __STATIONS__[0]), 1e-6) if len(__STATIONS__) > 1 else 10.0
min_gap = max(0.5, _span / 40.0)
steps_found = []
while len(done) < max_st and tol > 0 and len(done) >= 2:
    cs_ = sorted(done); worst = (0.0, None)
    for a, b in zip(cs_[:-1], cs_[1:]):
        if (b - a) < min_gap:
            continue                                      # a step: recorded below, not bisected again
        d = _diff(a, b)
        if d > worst[0]:
            worst = (d, (a, b))
    if worst[1] is None or worst[0] <= tol:
        break
    a, b = worst[1]; mid = round((a + b) / 2.0, 3)
    print("DOSSIER refine: sections %s=%.2f and %.2f differ by %.2f > %.2f -> station at %.2f" % ("xyz"[ax], a, b, worst[0], tol, mid), flush=True)
    take_station(mid)
cs_ = sorted(done)
for a, b in zip(cs_[:-1], cs_[1:]):
    if (b - a) < min_gap and _diff(a, b) > tol:
        steps_found.append([a, b, round(_diff(a, b), 3)])
        print("DOSSIER STEP: the profile changes by %.2f between %s=%.2f and %.2f (%.2f apart) - a feature edge, not a slope; "
              "not bisected further" % (_diff(a, b), "xyz"[ax], a, b, b - a), flush=True)
rep["steps"] = steps_found
rep["sections"].sort(key=lambda d_: d_["c"]); rep["stations"] = sorted(done)
if __FACES__:
    n = 0; small = []
    for i, f in enumerate(s.Faces):
        b = f.BoundBox
        if b.XMax < bx[0] or b.XMin > bx[1] or b.YMax < bx[2] or b.YMin > bx[3] or b.ZMax < bx[4] or b.ZMin > bx[5]:
            continue
        n += 1
        if f.Area < 0.30:
            cm = f.CenterOfMass; small.append([i + 1, round(float(f.Area), 4), [round(cm.x, 2), round(cm.y, 2), round(cm.z, 2)]])
    rep["faces"] = {"in_box": n, "under_0.30": len(small), "small": small[:300]}
    print("DOSSIER faces in box: %d, under 0.30 mm2: %d" % (n, len(small)), flush=True)
if __FRAMES__:
    rep["frames"] = K.look(s, out, name, focus_box=box3, views=__VIEWS__)
with open(os.path.join(out, "dossier.json"), "w", encoding="utf-8") as fh:
    json.dump(rep, fh, indent=1)
print("DOSSIER done: %d sections, %d frames, %.0f s" % (len(rep["sections"]), len(rep["frames"] or []), time.time() - t0), flush=True)
'''


def _stations(box, ax, n):
    lo, hi = float(box[2 * ax]), float(box[2 * ax + 1])
    return [round(lo + (i + 0.5) * (hi - lo) / n, 3) for i in range(n)]


def take(kit, name, box, src, axis=None, stations=3, step=1.0, views="std", frames=True, faces=True,
         only=None, entry=None, tol=0.30, max_stations=15):
    ROOT, HERE = kit.ROOT, kit.HERE
    box = [float(t) for t in box]
    if axis is None:
        ext = [box[1] - box[0], box[3] - box[2], box[5] - box[4]]
        axis = int(max(range(3), key=lambda i: ext[i]))
    ax = {"x": 0, "y": 1, "z": 2}.get(axis, axis) if isinstance(axis, str) else int(axis)
    out = os.path.join(ROOT, DIR, name); os.makedirs(out, exist_ok=True)
    st = _stations(box, ax, int(stations))
    do_sec = only in (None, "sections"); do_faces = faces and only in (None, "faces"); do_frames = frames and only in (None, "frames")
    code = (_TAKE.replace("__HERE__", repr(HERE)).replace("__ROOT__", repr(ROOT)).replace("__SRC__", repr(src)).replace("__BOX__", repr(box))
            .replace("__AX__", repr(ax)).replace("__OUT__", repr(out)).replace("__NAME__", repr(name))
            .replace("__STEP__", repr(float(step))).replace("__STATIONS__", repr(st if do_sec else []))
            .replace("__FACES__", repr(bool(do_faces))).replace("__FRAMES__", repr(bool(do_frames)))
            .replace("__VIEWS__", repr(views)).replace("__TOL__", repr(float(tol)))
            .replace("__MAXST__", repr(int(max_stations))))
    _idx0 = load(ROOT); _e0 = _idx0.get(name) or {"name": name, "box": box, "items": {}, "added": [],
                                                  "dir": os.path.relpath(out, ROOT), "stale": None}
    _e0["partial"] = {"started": now(), "model": src}
    _idx0[name] = _e0; save(ROOT, _idx0)
    rc = kit._fc(code, out, "dossier")
    if rc != 0:
        print("kit dossier: the kernel call failed (rc %s) — %s is registered PARTIAL; `kit job` refuses it until a"
              " take completes. Read %s" % (rc, name, os.path.join(out, "kit_run.log")))
        return rc
    try:
        with open(os.path.join(out, "dossier.json"), encoding="utf-8") as fh:
            rep = json.load(fh)
    except (OSError, ValueError) as e:
        print("kit dossier: the run wrote no dossier.json (%s) — %s stays PARTIAL." % (e, name)); return 2
    idx = load(ROOT); e = entry or idx.get(name) or {}
    items = e.get("items", {})
    if do_sec:
        items["sections"] = rep.get("sections", []); items["profiles"] = rep.get("profiles", {})
        st = rep.get("stations", st)
    if do_faces: items["faces"] = rep.get("faces")
    if do_frames: items["frames"] = rep.get("frames", [])
    try:
        mh = file_hash(src)
    except OSError:
        mh = None
    e.update({"name": name, "box": box, "axis": "xyz"[ax], "stations": st, "step": float(step),
              "views": views, "model": src, "model_hash": mh, "when": now(),
              "dir": os.path.relpath(out, ROOT), "items": items, "stale": None})
    e.pop("defined_only", None)
    e.pop("partial", None)
    e.setdefault("added", [])
    idx[name] = e; save(ROOT, idx)
    print("[dossier] %s: box %s, axis %s, stations %s — %d sections, faces %s, %d frames. FRESH on %s"
          % (name, " ".join("%g" % v for v in box), "xyz"[ax], st, len(items.get("sections", [])),
             (items.get("faces") or {}).get("in_box", "-"), len(items.get("frames") or []), os.path.basename(src)))
    print("[dossier] read it without the kernel:   kit dossier show %s" % name)
    return 0


def session_prompt(root):
    """Printed by `kit open` and `kit status`: what the orchestrator must ASK the client about regions at
    the start of a session (the client, 2026-09-10). Defined regions: ask which to measure. None defined:
    propose them from the survey frames and the open criteria rows, and ask whether to measure."""
    idx = load(root) or {}
    defined = [n for n, e in idx.items() if e.get("defined_only")]
    stale = [n for n, e in idx.items() if e.get("stale")]
    fresh = [n for n, e in idx.items() if not e.get("defined_only") and not e.get("stale")]
    lines = []
    if not idx:
        _quiet = None
        try:
            import leangate as _G
            _dfr = _G.atlas_defer_active(root)
            if _dfr:
                _quiet = "the atlas is deferred until \"%s\"" % _dfr.get("until")
            elif not ((_G.session(root) or {}).get("model_of_record") or ""):
                _bk = [f_ for d_ in (os.path.join(root, "claude_code", "bank"), os.path.join(root, "model", "bank")) if os.path.isdir(d_) for f_ in os.listdir(d_) if f_.lower().endswith(".brep")]
                _quiet = ("no session is open - the bank holds %d brep(s) (kit open --model <one of them>)" % len(_bk)) if _bk else "the bank is empty - no model of record yet"
        except Exception:
            _quiet = None
        if _quiet:
            lines.append("[dossier] no regions yet - %s: the atlas and the dossier come AFTER the model has made worthwhile progress (PROJECT_START.md 4); nothing to propose now (31bv B1)." % _quiet)
        else:
            lines.append("[dossier] no regions defined yet: name one as you measure it - `kit dossier define <name> --box ... --row X` (one box per open criteria row, "
                         "from the survey frames), then `kit dossier take <name>`; on a client's part, propose the list to the client first and measure the ones agreed (31bx R1 D2).")
    else:
        if defined:
            lines.append("[dossier] defined, NOT measured: %s — ASK the client which of these to measure (`kit dossier take`)."
                         % ", ".join(sorted(defined)))
        if stale:
            lines.append("[dossier] STALE (a job changed their box): %s — ask before refreshing." % ", ".join(sorted(stale)))
        if fresh:
            lines.append("[dossier] measured and valid: %s (`kit dossier show <name>`)." % ", ".join(sorted(fresh)))
    try:
        d = os.path.join(root, DIR)
        on_disk = {n for n in os.listdir(d)
                   if os.path.isdir(os.path.join(d, n)) and not n.startswith(("_", "."))} \
            if os.path.isdir(d) else set()
        orphan = sorted(on_disk - set(idx))
        missing = sorted(n for n in idx if n not in on_disk and not idx[n].get("defined_only"))
        if orphan:
            lines.append("[dossier] ON DISK BUT NOT REGISTERED: %s. A region the register has not "
                         "heard of is never\n[dossier]   reported, never marked STALE when a job "
                         "changes its box, and cannot be refused on.\n[dossier]   Take it properly "
                         "(`kit dossier take`) or delete the folder." % ", ".join(orphan))
        if missing:
            lines.append("[dossier] REGISTERED BUT NOT ON DISK: %s. `kit dossier show` will find "
                         "nothing." % ", ".join(missing))
    except OSError:
        pass
    for l in lines:
        print(l)
    return lines


def cmd(args, kit):
    ROOT = kit.ROOT
    if not args or args[0] in ("-h", "--help"):
        print(__doc__); return 2
    BARE = ("--as-orchestrator", "--no-frames", "--no-faces", "--force", "--faces")
    sub = args[0]; rest = [t for t in args[1:] if t != "--as-orchestrator"]
    idx = load(ROOT)
    if sub == "list":
        if not idx:
            print("no dossiers yet — kit dossier take <name> --box x0 x1 y0 y1 z0 z1"); return 0
        # UNCHECKED
        try:
            model = (kit.G._require_session(ROOT, "dossier") or {}).get("model_of_record")
        except BaseException:
            model = None
        if not model:
            print("[dossier] NO SESSION OPEN - the model hash cannot be compared, so nothing below is checked.")
            print("[dossier]   `kit open` first; until then FRESH is printed as UNCHECKED.")
        for name in sorted(idx):
            stt, e = status(ROOT, name, model)
            if stt == "fresh" and not model:
                stt = "unchecked"
            it = e.get("items", {})
            print("%-20s %-22s box %s  row %s  axis %s  %d sec  faces %s  %d frames  +%d added  %s"
                  % (name, stt.upper() if stt != "stale" else "STALE by %s" % e["stale"].get("by"),
                     " ".join("%g" % v for v in e.get("box", [])), e.get("row") or "-", e.get("axis") or "-",
                     len(it.get("sections", [])), (it.get("faces") or {}).get("in_box", "-"),
                     len(it.get("frames") or []), len(e.get("added", [])), e.get("when") or ("defined " + str(e.get("defined")))))
        return 0
    if sub == "show":
        if len(rest) < 1:
            print("kit dossier show <name> [--faces]"); return 2
        name = rest[0]; e = idx.get(name)
        if not e:
            print("no dossier %r. kit dossier list" % name); return 2
        print("DOSSIER %s  box %s  axis %s  stations %s  step %g  taken %s  model %s%s%s"
              % (name, " ".join("%g" % v for v in e.get("box", [])), e.get("axis", "-"), e.get("stations", "-"),
                 e.get("step", 1.0), e.get("when") or "never (defined %s)" % e.get("defined", "?"),
                 os.path.basename(e.get("model", "") or "") or "-",
                 ("  *** STALE by %s at %s ***" % (e["stale"]["by"], e["stale"]["when"])) if e.get("stale") else "",
                 "  *** PARTIAL - a take did not finish ***" if e.get("partial") else ""))
        it = e.get("items", {})
        for sc in it.get("sections", []):
            print("  section %s=%.2f  %s  (%.3f mm/px)" % (e["axis"], sc["c"], sc["png"], sc["mmpx"]))
        for fr in it.get("frames") or []:
            print("  frame   %s" % fr)
        for key, prof in (it.get("profiles") or {}).items():
            print("PROFILE %s, u = the box's first remaining axis, v = the second: intervals top-down [outer inner], + = continues past the window" % key)
            for u, pairs in prof:
                print("PROFILE u %8.2f : %s" % (u, " ".join("[%.2f%s %.2f%s]" % (p[0], "+" if p[2] else "", p[1], "+" if p[3] else "") for p in pairs) if pairs else "MISS"))
        f = it.get("faces")
        if f:
            print("FACES in box %d, under 0.30 mm2: %d" % (f["in_box"], f["under_0.30"]))
            if "--faces" in rest:
                for i, area, cm in f.get("small", []):
                    print("  face %5d  %.4f mm2  at %s" % (i, area, cm))
        for k, ad in enumerate(e.get("added", []), 1):
            print("ADDED #%d %s  %s%s" % (k, ad["when"], ad["cmd"], ("  -> " + ad["png"]) if ad.get("png") else ""))
            for line in (ad.get("text") or "").splitlines():
                if line.strip():
                    print("    " + line)
        return 0
    if sub == "add":
        # kit measure
        if len(rest) < 1:
            print('kit dossier add <name> --what "..." --value "..." --source "<script, render or file>" [--png <file>]'); return 2
        name = rest[0]; a = kit._kv([t for t in rest[1:] if t not in BARE])
        miss = [k for k in ("--what", "--value", "--source") if not str(a.get(k, "")).strip()]
        if miss:
            print("kit dossier add REFUSED: %s required. A number with no statement of what it measures, or of"
                  " where it came from, is not reusable - the next agent cannot tell it from a guess." % ", ".join(miss))
            return 2
        if name not in idx:
            print("kit dossier add: no dossier %r. Define its box first: kit dossier define %s --box x0 x1 y0 y1 z0 z1"
                  % (name, name)); return 2
        txt = "%s = %s\n  source: %s" % (a["--what"], a["--value"], a["--source"])
        ok = add(ROOT, name, "added: %s" % a["--what"], txt, a.get("--png"))
        return 0 if ok else 2
    if sub == "define":
        if len(rest) < 1:
            print("kit dossier define <name> --box x0 x1 y0 y1 z0 z1 [--row A-L] [--note \"...\"]"); return 2
        name = rest[0]; a = kit._kv([t for t in rest[1:] if t not in BARE])
        box = str(a.get("--box", "")).split()
        if len(box) != 6:
            print("kit dossier define: --box needs SIX numbers x0 x1 y0 y1 z0 z1"); return 2
        e = idx.get(name) or {}
        if e and not e.get("defined_only"):
            print("dossier %r is already measured (%s); define is for regions not yet taken." % (name, e.get("when"))); return 2
        e.update({"name": name, "box": [float(t) for t in box], "row": a.get("--row"), "note": a.get("--note"),
                  "defined": now(), "defined_only": True, "items": e.get("items", {}), "stale": None,
                  "dir": os.path.relpath(os.path.join(ROOT, DIR, name), ROOT), "added": e.get("added", [])})
        idx[name] = e; save(ROOT, idx)
        print("[dossier] %s DEFINED (row %s): box %s — not measured. `kit dossier take %s` when a card needs it."
              % (name, e.get("row") or "-", " ".join("%g" % v for v in e["box"]), name))
        return 0
    if sub == "unstale":
        # recorded
        if len(rest) < 1:
            print("kit dossier unstale <name> --because \"<why the model of record did not change>\""); return 2
        name = rest[0]; a = kit._kv([t for t in rest[1:] if t not in BARE])
        e = idx.get(name)
        if not e or not e.get("stale"):
            print("kit dossier unstale: %r is not STALE (kit dossier list)" % name); return 2
        why = str(a.get("--because", "")).strip()
        if len(why) < 15:
            print("kit dossier unstale REFUSED: --because \"<why the model of record did not change>\" (15+ characters)"); return 2
        s = kit.G.session(ROOT) or {}
        model = s.get("model_of_record") or e.get("model")
        if e.get("model_hash") and model and os.path.exists(model) and file_hash(model) != e["model_hash"]:
            print("kit dossier unstale REFUSED: the model of record (%s) is NOT the model %s was measured on - the mark is\n"
                  "  right; `kit dossier refresh %s` re-takes it on the current model." % (os.path.basename(model), name, name))
            return 2
        e["unstaled"] = {"was": e["stale"], "because": why, "when": now()}
        e["stale"] = None
        idx[name] = e; save(ROOT, idx)
        print("[dossier] %s is FRESH again (was STALE by %s): %s" % (name, e["unstaled"]["was"].get("by"), why))
        return 0
    if sub in ("take", "refresh"):
        if len(rest) < 1:
            print("kit dossier %s <name> ..." % sub); return 2
        name = rest[0]; a = kit._kv([t for t in rest[1:] if t not in BARE])
        e = idx.get(name)
        if sub == "take" and e and e.get("partial") and "--force" not in rest:      # did not finish
            print("[dossier] %s is PARTIAL (a take started %s and did not finish) - taken again" % (name, (e.get("partial") or {}).get("started")))
        elif sub == "take" and e and not e.get("defined_only") and "--force" not in rest:
            print("dossier %r exists (%s%s). `kit dossier refresh %s` re-takes it; `--force` overwrites."
                  % (name, e.get("when"), " STALE" if e.get("stale") else "", name)); return 2
        if sub == "refresh" and not e:
            print("no dossier %r to refresh. kit dossier list" % name); return 2
        s = kit.G._require_session(ROOT, "dossier")
        src = a.get("--from") or s.get("model_of_record") or (e or {}).get("model")
        if not src or not os.path.exists(src):
            print("kit dossier: no model to measure (%r). --from <brep> or open the session on one." % src); return 2
        if sub == "take":
            box = str(a.get("--box", "")).split()
            if len(box) != 6 and e and e.get("defined_only"):
                box = [str(v) for v in e["box"]]
            if len(box) != 6:
                print("kit dossier take: --box needs SIX numbers x0 x1 y0 y1 z0 z1 (or a region defined first)"); return 2
            axis = a.get("--axis"); stations = int(a.get("--stations", 3)); step = float(a.get("--step", 1.0))
            views = a.get("--views", "std")
        else:
            box = e["box"]; axis = e.get("axis"); stations = 3; step = e.get("step", 1.0); views = e.get("views", "std")
        frames = "--no-frames" not in rest; faces = "--no-faces" not in rest
        only = a.get("--only")
        return take(kit, name, box, src, axis=axis, stations=stations, step=step, views=views,
                    frames=frames, faces=faces, only=only, entry=e if sub == "refresh" else None,
                    tol=float(a.get("--tol", 0.30)), max_stations=int(a.get("--max-stations", 15)))
    print(__doc__); return 2

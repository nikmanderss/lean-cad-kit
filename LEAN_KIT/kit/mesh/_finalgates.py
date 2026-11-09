# open edges
import os, sys, json, struct, subprocess, re, time
import numpy as np
from scipy.spatial import cKDTree

J = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("CC_WORK") or os.getcwd()
PY = sys.executable
KIT = os.path.join(os.environ.get("KIT_HOME") or os.path.dirname(J), "kit.py")
t0 = time.time()


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def topo(T):
    V, inv = np.unique(np.round(T.reshape(-1, 3), 6), axis=0, return_inverse=True)
    F = inv.reshape(-1, 3)
    E = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
    _, cnt = np.unique(E, axis=0, return_counts=True)
    par = np.arange(len(V))
    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for f in F:
        r0 = find(f[0])
        for k in (1, 2):
            rk = find(f[k])
            if rk != r0: par[rk] = r0
    roots = np.array([find(i) for i in range(len(V))])
    shells = len(np.unique(roots[F[:, 0]]))
    return {"triangles": len(T), "open": int((cnt == 1).sum()), "nonmanifold": int((cnt > 2).sum()), "shells": shells}


def volume(T):
    return float(np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum() / 6.0)


def keys(T):
    q = np.round(T / 1e-4).astype(np.int64)
    s = np.sort(q.view([("x", np.int64), ("y", np.int64), ("z", np.int64)]).reshape(-1, 3), axis=1)
    return s.view(np.int64).reshape(-1, 9)


R = read_stl(os.environ["CC_RESULT"]); B = read_stl(os.environ["CC_BASE"])
man = json.load(open(os.environ["CC_MANIFEST"]))
rep = {"result": os.environ["CC_RESULT"], "base": os.environ["CC_BASE"], "gates": {}, "edits": {}, "refused": []}
say = lambda *a: print(*a, flush=True)
tr, tb = topo(R), topo(B)
rep["gates"]["topology"] = {"result": tr, "base": tb}
say("1-2. topology  result %s | base %s" % (tr, tb))
dopen = (tr["open"] + tr["nonmanifold"]) - (tb["open"] + tb["nonmanifold"])
if dopen > int(os.environ.get("CC_MAXOPEN", "20")):
    rep["refused"].append("open+non-manifold rose by %d (limit %s)" % (dopen, os.environ.get("CC_MAXOPEN", "20")))
if tr["shells"] > tb["shells"]:
    rep["refused"].append("shells rose %d -> %d (a new inner skin or loose piece)" % (tb["shells"], tr["shells"]))
if not os.environ.get("CC_EXTENT", "").strip():
    say("FAIL: CC_EXTENT \"x0 x1 y0 y1 z0 z1\" (the body of record's extent) is not set - kit mesh fills it from the atlas"); sys.exit(2)
_ext = [float(t) for t in os.environ["CC_EXTENT"].split()]
lo, hi = np.array(_ext[0::2]) - 0.5, np.array(_ext[1::2]) + 0.5
Rv = R.reshape(-1, 3)
spikes = int((~np.isfinite(Rv).all(1) | np.any(Rv < lo, 1) | np.any(Rv > hi, 1)).sum())
rep["gates"]["spikes"] = spikes; say("3. spikes: %d vertices outside the body of record's extent + 0.5 mm" % spikes)
if spikes: rep["refused"].append("%d spike vertices" % spikes)
vr, vb = volume(R), volume(B)
rep["gates"]["volume"] = {"result": vr, "base": vb, "delta": vr - vb}
say("4. volume %.1f mm3 against %.1f (delta %+.1f)" % (vr, vb, vr - vb))
bk = set(map(bytes, keys(B)))
new = np.array([bytes(k) not in bk for k in keys(R)])
boxes = {}
for e in man["edits"]:
    z = np.load(e["blob"]); E = z["E"]; M = float(z["M"])
    Mi = z["Mi"] if "Mi" in z.files else None
    boxes[e["name"]] = (E.min(0) - M, E.max(0) + M, E, M, Mi)
_bt = cKDTree(B.mean(1))
_cand = np.where(new)[0]
_dd = _bt.query(R[_cand].mean(1))[0]
new[_cand[_dd < 2e-3]] = False
C = R[new].mean(1)
inside_any = np.zeros(len(C), bool)
for nm, (blo, bhi, *_r) in boxes.items():
    inside_any |= np.all((C >= blo - 2) & (C <= bhi + 2), 1)
out_n = int((~inside_any).sum())
rep["gates"]["changed_outside_edits"] = out_n
say("5. changed triangles outside every edit box + 2 mm: %d of %d changed" % (out_n, len(C)))
if out_n: rep["refused"].append("%d changed triangles outside every edit box" % out_n)

import tempfile
_TMP = tempfile.mkdtemp(prefix="fg_", dir=os.path.dirname(os.path.abspath(os.environ["CC_OUT"])))


def _write(pth, T):
    T = np.asarray(T, np.float32)
    n_ = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); l_ = np.linalg.norm(n_, axis=1); l_[l_ == 0] = 1
    rec = np.zeros(len(T), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    rec["n"] = n_ / l_[:, None]; rec["v"] = T.reshape(-1, 9)
    with open(pth, "wb") as f_:
        f_.write(b"the agent fg crop".ljust(80, b" ")); f_.write(struct.pack("<I", len(T))); f_.write(rec.tobytes())


def crops(lo, hi, tag, mg=6.0):
    """both meshes cut to [lo - mg, hi + mg]; returns (base crop path, result crop path)"""
    lo = np.asarray(lo, float) - mg; hi = np.asarray(hi, float) + mg
    out_ = []
    for lab, T in (("b", B), ("r", R)):
        m_ = np.any(np.all((T >= lo) & (T <= hi), 2), 1)
        pth = os.path.join(_TMP, "%s_%s.stl" % (tag, lab)).replace("\\", "/"); _write(pth, T[m_]); out_.append(pth)
    return out_

for e in man["edits"]:
    nm = e["name"]; blo, bhi, E, M, Mi = boxes[nm]
    er = {}
    def boxvol(T):
        c = T.mean(1); m = np.all((c >= blo - 1) & (c <= bhi + 1), 1)
        return volume(T[m])
    er["volume_delta_in_box"] = boxvol(R) - boxvol(B)
    bx = "%g %g %g %g %g %g" % (blo[0] - 3, bhi[0] + 3, blo[1] - 3, bhi[1] + 3, blo[2] - 3, bhi[2] + 3)
    _cb, _cr = crops(blo - 3, bhi + 3, "e_" + nm)
    p = subprocess.run([PY, "-W", "ignore", os.path.join(J, "_passage.py"), _cb, _cr, bx, "0.25", nm],
                       capture_output=True, text=True)
    er["passage"] = p.stdout.strip()
    for ax, a, b_ in re.findall(r"(\w): (\d+) -> (\d+) clear", p.stdout):
        a, b_ = int(a), int(b_)
        if a > 0 and b_ < 0.95 * a:
            rep["refused"].append("%s: lines of sight along %s fell %d -> %d (more than 5 pct)" % (nm, ax, a, b_))
    Rt = R[np.all((R.mean(1) >= blo - 1) & (R.mean(1) <= bhi + 1), 1)]
    rng = np.random.default_rng(3)
    u = rng.random((len(Rt), 6)); u1, u2 = u[:, :1], u[:, 1:2]; s = np.sqrt(u1)
    P = (1 - s) * Rt[:, 0] + s * (1 - u2) * Rt[:, 1] + s * u2 * Rt[:, 2]
    tE = cKDTree(E)
    if Mi is None:
        f = tE.query(P)[0] - M
    else:
        dk, ik = tE.query(P, k=16); f = (dk - Mi[ik]).min(1)
    band = P[np.abs(f) < 0.2]
    Bs = B[np.all((B.mean(1) >= blo - 2) & (B.mean(1) <= bhi + 2), 1)]
    ub = rng.random((len(Bs) * 8, 2)); sb = np.sqrt(ub[:, :1])
    Bt = np.repeat(Bs, 8, axis=0)
    BP = (1 - sb) * Bt[:, 0] + sb * (1 - ub[:, 1:2]) * Bt[:, 1] + sb * ub[:, 1:2] * Bt[:, 2]
    d = cKDTree(BP).query(band)[0] if len(band) else np.array([0.0])
    er["seam_band"] = {"points": int(len(band)), "p99": float(np.percentile(d, 99)), "max": float(d.max())}
    for tag, mesh in (("result", _cr), ("base", _cb)):
        q = subprocess.run([PY, "-W", "ignore", KIT, "mesh", "thin", "--job", os.environ.get("CC_JOB", os.path.basename(os.path.dirname(WORK))),
                            "--tag", "FG%s%s" % (nm[:6].upper(), tag[0].upper()), "--set", "CC_RESULT=%s" % os.path.abspath(mesh),
                            "--set", "CC_BOX=%g %g %g %g %g %g" % (blo[0], bhi[0], blo[1], bhi[1], blo[2], bhi[2]),
                            "--set", "CC_SAMPLE=%s" % ("100000000" if tag == "result" else "1")]
                           + (["--set", "CC_NEWREF=%s" % os.path.abspath(_cb)] if tag == "result" else []),
                           cwd=os.environ.get("KIT_CWD") or os.getcwd(), capture_output=True, text=True,
                           creationflags=(0x08000000 if os.name == "nt" else 0))
        mn = re.search(r"min ([\d.]+)\s+p01 ([\d.]+)\s+median ([\d.]+)", q.stdout)
        nd = re.search(r"aspect over\s+1000 :\s+(\d+) triangles,\s+([\d.]+) mm2", q.stdout)
        er["wall_" + tag] = {"min": float(mn.group(1)) if mn else None, "p01": float(mn.group(2)) if mn else None,
                             "needles_1000": int(nd.group(1)) if nd else None,
                             "needle_area_1000": float(nd.group(2)) if nd else None}
    rep["edits"][nm] = er
    say("   %-6s vol %+7.1f | %s | seam band %d pts p99 %.3f max %.3f | new-surface wall min %s p01 %s (min is ray-at-convex-edge; p01 is the wall), needles %s / %.3f mm2 (base %s / %.3f)"
        % (nm, er["volume_delta_in_box"], er["passage"].split(None, 1)[1] if " " in er["passage"] else er["passage"],
           er["seam_band"]["points"], er["seam_band"]["p99"], er["seam_band"]["max"],
           er["wall_result"]["min"], er["wall_result"]["p01"], er["wall_result"]["needles_1000"], er["wall_result"]["needle_area_1000"] or 0, er["wall_base"]["needles_1000"], er["wall_base"]["needle_area_1000"] or 0))
    if er["seam_band"]["p99"] > 0.15:
        rep["refused"].append("%s: seam band p99 %.3f mm over 0.15" % (nm, er["seam_band"]["p99"]))
    _na, _nb = er["wall_result"]["needle_area_1000"], er["wall_base"]["needle_area_1000"]
    if _na is not None and _nb is not None and _na - _nb > 1.0:
        rep["refused"].append("%s: needle-triangle area rose %.2f -> %.2f mm2" % (nm, _nb, _na))
if os.environ.get("CC_OPENINGS"):
    rep["openings"] = {}
    for o in json.load(open(os.environ["CC_OPENINGS"]))["openings"]:
        bx = " ".join("%g" % v for v in o["box"])
        _ob, _or = crops(np.array(o["box"][0::2]), np.array(o["box"][1::2]), "o_" + re.sub(r"\W", "_", o["name"]))
        p = subprocess.run([PY, "-W", "ignore", os.path.join(J, "_passage.py"), _ob, _or, bx, "0.2", o["name"]],
                           capture_output=True, text=True)
        rep["openings"][o["name"]] = p.stdout.strip()
        for ax, a, b_ in re.findall(r"(\w): (\d+) -> (\d+) clear", p.stdout):
            if ax in o.get("axes", "xyz"):
                a, b_ = int(a), int(b_)
                flag = (a > 0 and b_ < 0.95 * a)
                if flag:
                    rep["refused"].append("opening %s: clear lines of sight along %s fell %d -> %d" % (o["name"], ax, a, b_))
                say("9. opening %-26s %s: %d -> %d clear%s" % (o["name"], ax, a, b_, "   *** NARROWED" if flag else ""))
json.dump(rep, open(os.environ["CC_OUT"], "w"), indent=1)
say("REFUSED:" if rep["refused"] else "ALL GATES PASS", *["\n   - " + r for r in rep["refused"]])
say("%.0f s" % (time.time() - t0))
import shutil; shutil.rmtree(_TMP, ignore_errors=True)

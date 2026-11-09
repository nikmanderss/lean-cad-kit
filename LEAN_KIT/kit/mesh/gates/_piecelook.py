"""the agent 2026-09-24 - LK'S OWN LOOK AT A PIECE: the new surface found by itself (weld triangles not in the base), the (a gate tool: kit mesh gate _piecelook --job <J> --tag <T> -- <args>)"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _rlook import read_stl, boxclip
sys.path.insert(0, os.environ.get("KIT_HOME") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
import kitlib_render as R

out = sys.argv[1]; os.makedirs(out, exist_ok=True)


def keys(T):
    q = np.round(T / 1e-4).astype(np.int64)
    s = np.sort(q.view([("x", np.int64), ("y", np.int64), ("z", np.int64)]).reshape(-1, 3), axis=1)
    return s.view(np.int64).reshape(-1, 9)


for spec in sys.argv[2].split(";"):
    name, weld, base = spec.split("|")
    W = read_stl(weld); B = read_stl(base)
    bk = set(map(bytes, keys(B)))
    new = np.array([bytes(k) not in bk for k in keys(W)])
    Nw = W[new]
    if not len(Nw):
        print(name, "no new surface"); continue
    lo = Nw.reshape(-1, 3).min(0) - 2.0; hi = Nw.reshape(-1, 3).max(0) + 2.0
    N = np.cross(Nw[:, 1] - Nw[:, 0], Nw[:, 2] - Nw[:, 0])
    n = N.sum(0); n = n / max(np.linalg.norm(n), 1e-9)
    t1 = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0]); t1 /= np.linalg.norm(t1)
    t2 = np.cross(n, t1)
    T = boxclip(W, lo, hi)
    V = T.reshape(-1, 3); TT = np.arange(len(V)).reshape(-1, 3)
    focus = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    files = []
    for vn, d, lt in (("face", -n, None), ("graze1", -n + 1.2 * t1, "grazing"), ("graze2", -n + 1.2 * t2, "grazing")):
        f = os.path.join(out, "%s_%s.png" % (name, vn))
        R.render(f, [(name, V, TT, np.array([0.8, 0.8, 0.82]))], list(d / np.linalg.norm(d)), W=900, pad=0.1, focus=focus,
                 light=lt, title="%s after - %s (new surface %.0f x %.0f x %.0f mm)" % ((name, vn) + tuple(hi - lo - 4)),
                 scale_bar=True)
        files.append(f)
    ims = [Image.open(f) for f in files]
    h = max(i.height for i in ims); sheet = Image.new("RGB", (sum(i.width for i in ims), h), "white"); x = 0
    for i in ims:
        sheet.paste(i, (x, 0)); x += i.width
    sp = os.path.join(out, "SHEET_%s.png" % name); sheet.save(sp)
    print(sp, "new triangles %d, normal %s" % (int(new.sum()), np.round(n, 2).tolist()), flush=True)

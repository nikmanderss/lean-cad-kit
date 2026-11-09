"""the agent 2026-09-24 - close-ups of every cluster _ccneedle.py flags: base and weld, the same 3 views (looking at the surface along (a gate tool: kit mesh gate _needlelook --job <J> --tag <T> -- <args>)"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _rlook import read_stl, boxclip
sys.path.insert(0, os.environ.get("KIT_HOME") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
import kitlib_render as R
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
RR = float(os.environ.get("CC_R", "2.5"))
cache = {}
for spec in sys.argv[2].split(";"):
    tag, base, weld, c = spec.split("|")
    c = np.array([float(t) for t in c.split()])
    lo = c - RR; hi = c + RR
    for lab, p in (("after", weld), ("before", base)):
        if p not in cache:
            cache[p] = read_stl(p)
        T = boxclip(cache[p], lo, hi)
        if lab == "after":
            N = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); w = np.linalg.norm(N, axis=1)
            d0 = np.linalg.norm(T.mean(1) - c, axis=1); m = d0 < 1.5
            n = N[m].sum(0); n = n / max(np.linalg.norm(n), 1e-9)
            t1 = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0]); t1 /= np.linalg.norm(t1)
            t2 = np.cross(n, t1)
            views = {"face": -n, "graze1": -n + 1.4 * t1, "graze2": -n + 1.4 * t2}
        V = T.reshape(-1, 3); TT = np.arange(len(V)).reshape(-1, 3)
        focus = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        for nm, d in views.items():
            f = os.path.join(out, "%s_%s_%s.png" % (tag, nm, lab))
            R.render(f, [(tag, V, TT, np.array([0.8, 0.8, 0.82]))], list(d / np.linalg.norm(d)), W=700, pad=0.15, focus=focus,
                     light="grazing" if nm != "face" else None, title="%s %s %s (+-%.1f mm)" % (tag, nm, lab, RR), scale_bar=True)
            print(f)

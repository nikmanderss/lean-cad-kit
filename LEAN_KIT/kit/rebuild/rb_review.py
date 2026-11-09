# kit rebuild
# content.brep
import os, sys, numpy as np, Part
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
TAG = os.environ.get("LK_TAG", "")
sys.path.insert(0, os.environ["KIT_HOME"])
import kitlib_render as R
STL = os.environ["STL"]; TAG = os.environ.get("TAG", "piece"); OUT = os.environ.get("OUT_DIR") or os.path.join(os.path.dirname(STL), "review"); os.makedirs(OUT, exist_ok=True)
V, T = R.read_stl(STL)[:2] if isinstance(R.read_stl(STL), tuple) else R.read_stl(STL)
V = np.asarray(V, float); T = np.asarray(T, int)
cx = V[T].mean(axis=1); WIN = [float(t) for t in os.environ["WIN"].split()]
inw = (cx[:, 0] >= WIN[0] - 0.5) & (cx[:, 0] <= WIN[1] + 0.5) & (cx[:, 1] >= WIN[2] - 0.5) & (cx[:, 1] <= WIN[3] + 0.5) & (cx[:, 2] >= WIN[4] - 0.5) & (cx[:, 2] <= WIN[5] + 0.5)
Tw = T[inw]
C = np.full((len(Tw), 3), (0.95, 0.6, 0.2))
views = {"iso_aft_below": R.look(fwd=0.6, left=-0.5, up=0.6), "above": R.look(up=-1.0), "below": R.look(up=1.0), "fromP": R.look(left=-1.0),
         "v1": R.look(fwd=1.0, left=0.4, up=0.5), "v2": R.look(fwd=1.0, left=-0.4, up=-0.5), "v3": R.look(fwd=-1.0, left=0.4, up=0.5), "v4": R.look(fwd=1.0, up=0.9, left=0.2)}
for nm, d in views.items():
    R.render(os.path.join(OUT, "%s_%s.png" % (TAG, nm)), [("m", V, Tw, C)], d, W=1000, title="%s %s" % (TAG, nm))
S = Part.Shape(); S.importBrep(os.environ["ORIG"]); s = max(S.Solids, key=lambda x: x.Volume)
VA, TA, _ = R.tess_shape(s, dev=0.03); VA = np.asarray(VA, float); TA = np.asarray(TA, int); cxa = VA[TA].mean(axis=1)
TA = TA[(cxa[:, 0] >= WIN[0] - 0.5) & (cxa[:, 0] <= WIN[1] + 0.5) & (cxa[:, 1] >= WIN[2] - 0.5) & (cxa[:, 1] <= WIN[3] + 0.5) & (cxa[:, 2] >= WIN[4] - 0.5) & (cxa[:, 2] <= WIN[5] + 0.5)]
try:
    from scipy.spatial import cKDTree
    ref = np.vstack([VA, VA[TA].mean(axis=1)]); dd, _ = cKDTree(ref).query(V[Tw].mean(axis=1))
    sel = dd > 0.2; P_ = V[Tw].mean(axis=1)[sel]; D_ = dd[sel]
    groups = []
    if len(P_):
        kk = np.floor(P_ / 6.0).astype(int); uk, inv, cnt = np.unique(kk, axis=0, return_inverse=True, return_counts=True); inv = np.asarray(inv).reshape(-1)
        for j in np.argsort(-cnt)[:4]:
            Q = P_[inv == j]; groups.append((Q.min(0) - 4.0, Q.max(0) + 4.0, float(D_[inv == j].max()), int(cnt[j])))
    if not groups:
        xm = 0.5 * (WIN[0] + WIN[1]); ym = 0.5 * (WIN[2] + WIN[3])
        for xa, xb in ((WIN[0], xm), (xm, WIN[1])):
            for ya, yb in ((WIN[2], ym), (ym, WIN[3])): groups.append((np.array([xa, ya, WIN[4]]), np.array([xb, yb, WIN[5]]), 0.0, 0))
    for k, (blo, bhi, dmax, n_) in enumerate(groups):
        foc = np.array([[x, y, z] for x in (blo[0], bhi[0]) for y in (blo[1], bhi[1]) for z in (blo[2], bhi[2])], float)
        for dn, d in (("a", R.look(fwd=0.5, left=0.4, up=-0.7)), ("b", R.look(fwd=-0.5, left=-0.4, up=0.6))):
            R.render(os.path.join(OUT, "%s_close%d%s.png" % (TAG, k + 1, dn)), [("m", V, Tw, C)], d, W=1200, focus=foc,
                     title="%s CLOSE-UP %d%s: %s" % (TAG, k + 1, dn, ("a place the piece changed (up to %.2f mm from the original, %d samples)" % (dmax, n_)) if n_ else "a quarter of the window"))
    print("close-ups: %d place(s), two views each" % len(groups), flush=True)
except Exception as ex: print("close-ups not made: %r" % (ex,), flush=True)
def _st(env, lo, hi, n=6): return [float(t) for t in os.environ[env].split()] if os.environ.get(env) else [lo + (hi - lo) * (k + 0.5) / n for k in range(n)]
for ax, name, cs in ((0, "x", _st("STATIONS_X", WIN[0], WIN[1])), (1, "y", _st("STATIONS_Y", WIN[2], WIN[3]))):
    for c in cs:
        sa = R.section_segs(VA, TA, ax, c); sb = R.section_segs(V, Tw, ax, c)
        if len(sa) == 0 and len(sb) == 0: print("station %s = %.1f: nothing there, skipped" % (name, c), flush=True); continue
        R.draw_section(os.path.join(OUT, "%s_%s%+.0f.png" % (TAG, name, c)), [(sa, (255, 215, 60), 3), (sb, (80, 200, 255), 1)], ax, "%s = %.0f   yellow: original   blue: %s" % (name, c, TAG), W=700, pad=3.0)
print("DONE")

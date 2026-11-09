import os, sys, numpy as np
for _s in (sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
def _fail(m): print(m if str(m).startswith("FAIL") else "FAIL: " + str(m), flush=True); raise SystemExit(1)
TAG = os.environ.get("LK_TAG", "")
sys.path.insert(0, os.environ["KIT_HOME"]); import kitlib_render as R
def _arg(name, i):
    v = os.environ.get(name)
    if v not in (None, ""): return v
    if len(sys.argv) > i and not sys.argv[i].lower().endswith(".py"): return sys.argv[i]
    _fail("rb_fillholes: %s not set (env %s or argument %d)" % (name, name, i))
src, out = _arg("STL", 1), _arg("OUT", 2)
V, T = R.read_stl(src)[:2]; V = np.asarray(V, float); T = np.asarray(T, int)
key = np.round(V / 1e-5).astype(np.int64); _, ui, inv = np.unique(key, axis=0, return_index=True, return_inverse=True); inv = inv.reshape(-1); V = V[ui]; T = inv[T]
for rnd in range(5):
    dirs = {}
    for t in T:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])): dirs[(int(a), int(b))] = 1
    opens = [(a, b) for (a, b) in dirs if (b, a) not in dirs]
    if not opens: break
    # open edges
    nxt = {a: b for a, b in opens}; used = set(); new = []
    for a, b in opens:
        if (a, b) in used: continue
        loop = [a]; cur = b; used.add((a, b))
        while cur != a and cur in nxt and len(loop) < 200:
            loop.append(cur); nx = nxt[cur]; used.add((cur, nx)); cur = nx
        if cur != a: continue
        # open edges
        for i in range(1, len(loop) - 1): new.append([loop[0], loop[i + 1], loop[i]])
    print("round %d: %d open edges -> %d triangles added" % (rnd, len(opens), len(new)), flush=True)
    if not new: break
    T = np.vstack([T, np.array(new, int)])
R.write_stl(out, V, T); print("health", R.mesh_health(V, T))

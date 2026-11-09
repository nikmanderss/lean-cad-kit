# pure python
import os, sys, json
import numpy as np
sys.path.insert(0, os.environ["KIT_HOME"])
import kitlib_render as R

MESH = os.environ["PC_MESH"]; OUT = os.environ["PC_OUT"]; WJ = os.environ["PC_WALLS"]
MIN_MM2 = float(os.environ.get("PC_MIN_MM2", "5.0")); MAXC = int(os.environ.get("PC_MAX_CLUSTERS", "12"))
SEC = os.path.join(OUT, "sections"); os.makedirs(SEC, exist_ok=True)
W = json.load(open(WJ, encoding="utf-8"))
clusters = [c for c in W.get("clusters", []) if c["mm2"] >= MIN_MM2][:MAXC]
if not clusters:
    print("no cluster of %.1f mm2 or more - nothing to section" % MIN_MM2); print("DONE"); sys.exit(0)
V, T = R.read_stl(MESH)
V = np.asarray(V, float); T = np.asarray(T, int)
made = []
for n, c in enumerate(clusters, 1):
    x0, x1, y0, y1, z0, z1 = c["box"]
    span = np.array([x1 - x0, y1 - y0, z1 - z0])
    ctr = np.array(c.get("median_at") or c["centre"])
    axes = list(np.argsort(-span)[:2])
    for axis in axes:
        cval = float(ctr[axis])
        segs = R.section_segs(V, T, int(axis), cval)
        if len(segs) == 0:
            continue
        ax_u, ax_v = [a for a in (0, 1, 2) if a != axis]
        lo = np.array([x0, y0, z0]); hi = np.array([x1, y1, z1])
        cu = 0.5 * (lo[ax_u] + hi[ax_u]); cv = 0.5 * (lo[ax_v] + hi[ax_v])
        wu = max(hi[ax_u] - lo[ax_u] + 12.0, 24.0); wv = max(hi[ax_v] - lo[ax_v] + 12.0, 24.0)
        window = ((cu - 0.5 * wu, cu + 0.5 * wu), (cv - 0.5 * wv, cv + 0.5 * wv))
        bx = [(lo[ax_u], lo[ax_v]), (hi[ax_u], lo[ax_v]), (hi[ax_u], hi[ax_v]), (lo[ax_u], hi[ax_v])]
        path = os.path.join(SEC, "sec_%02d_%s%g.png" % (n, "xyz"[axis], round(cval, 1)))
        title = "thin cluster %d: %.0f mm2, median %.2f mm - section across %s; light = material, red = the census box" % (n, c["mm2"], c["median"], "xyz"[axis])
        R.draw_section_filled(path, [(segs, (185, 185, 180))], [(segs, (255, 220, 60), 1)], int(axis), title,
                              W=1400, window=window, grid=5.0, polys=[(bx, (230, 60, 60))])
        made.append({"cluster": n, "axis": "xyz"[axis], "file": path})
        print("  cluster %d (%.0f mm2): %s" % (n, c["mm2"], path), flush=True)
json.dump(made, open(os.path.join(OUT, "sections.json"), "w", encoding="utf-8"), indent=1)
print("DONE")

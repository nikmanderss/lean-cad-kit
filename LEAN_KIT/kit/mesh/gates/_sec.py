"""review2/R1 - true planar sections of before (blue) and after (red) in one plot, same scale, mm grid. (a gate tool: kit mesh gate _sec --job <J> --tag <T> -- <args>)"""
import sys, struct
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def slice_mesh(tri, ax, v):
    d = tri[:, :, ax] - v
    s = np.sign(d); s[s == 0] = 1e-9
    cross = ~(np.all(d > 0, 1) | np.all(d < 0, 1))
    t = tri[cross]; d = d[cross]
    segs = []
    for (a, b) in ((0, 1), (1, 2), (2, 0)):
        pass
    P = []
    for i in range(3):
        j = (i + 1) % 3
        di, dj = d[:, i], d[:, j]
        m = (di * dj) < 0
        w = np.where(m, di / np.where(m, di - dj, 1), np.nan)
        p = t[:, i] + (t[:, j] - t[:, i]) * w[:, None]
        P.append(p)
    P = np.stack(P, 1)
    out = []
    for k in range(len(P)):
        q = P[k][~np.isnan(P[k][:, 0])]
        if len(q) >= 2:
            out.append(q[:2])
    return np.array(out) if out else np.zeros((0, 2, 3))


if __name__ == "__main__":
    before, after, axn, vals, win, pref = sys.argv[1:7]
    title = sys.argv[7] if len(sys.argv) > 7 else ""
    ax = "xyz".index(axn)
    uv = [i for i in range(3) if i != ax]
    win = [float(t) for t in win.split()]
    B = read_stl(before); A = read_stl(after)
    lo = np.array([win[0], win[2]]); hi = np.array([win[1], win[3]])
    for v in [float(t) for t in vals.split()]:
        fig, g = plt.subplots(figsize=(9, 9 * (win[3] - win[2]) / (win[1] - win[0]) + 0.6), dpi=110)
        for lab, M, col, lw in (("before", B, "#2060d0", 2.4), ("after", A, "#e03020", 1.1)):
            m = (M[:, :, ax].min(1) <= v) & (M[:, :, ax].max(1) >= v)
            s = slice_mesh(M[m], ax, v)
            s2 = s[:, :, uv]
            keep = np.any(np.all((s2 >= lo - 1) & (s2 <= hi + 1), axis=2), axis=1)
            g.add_collection(LineCollection(s2[keep], colors=col, linewidths=lw, label=lab))
        g.set_xlim(win[0], win[1]); g.set_ylim(win[2], win[3]); g.set_aspect("equal")
        span = win[1] - win[0]
        maj = 1.0 if span <= 12 else (2.0 if span <= 30 else 5.0)
        g.set_xticks(np.arange(np.ceil(win[0] / maj) * maj, win[1] + 1e-9, maj))
        g.set_yticks(np.arange(np.ceil(win[2] / maj) * maj, win[3] + 1e-9, maj))
        if span <= 12:
            g.set_xticks(np.arange(np.ceil(win[0] * 10) / 10, win[1], 0.1 if span <= 4 else 0.25), minor=True)
            g.set_yticks(np.arange(np.ceil(win[2] * 10) / 10, win[3], 0.1 if span <= 4 else 0.25), minor=True)
            g.grid(which="minor", color="#dddddd", lw=0.4)
        g.grid(which="major", color="#aaaaaa", lw=0.6)
        g.set_xlabel("xyz"[uv[0]] + " mm"); g.set_ylabel("xyz"[uv[1]] + " mm")
        g.legend(loc="upper right", fontsize=8)
        g.set_title("%s  section %s = %.2f  (blue before, red after)" % (title, axn, v), fontsize=10)
        out = "%s_%s%s.png" % (pref, axn, ("%.2f" % v).replace("-", "m").replace(".", "p"))
        fig.tight_layout(); fig.savefig(out); plt.close(fig)
        print(out)

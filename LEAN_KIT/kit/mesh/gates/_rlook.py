"""review3 Z2_front r1 - true box-cut renders (triangles split on the box walls, no caps, no centroid crop). (a gate tool: kit mesh gate _rlook --job <J> --tag <T> -- <args>)"""
import os, sys, struct
import numpy as np
sys.path.insert(0, os.environ.get("KIT_HOME") or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
import kitlib_render as R


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def clip_poly(poly, ax, val, keep_le):
    out = []
    n = len(poly)
    for i in range(n):
        a = poly[i]; b = poly[(i + 1) % n]
        da = (a[ax] - val) * (1 if keep_le else -1); db = (b[ax] - val) * (1 if keep_le else -1)
        ina = da <= 0; inb = db <= 0
        if ina:
            out.append(a)
        if ina != inb:
            t = da / (da - db)
            out.append(a + t * (b - a))
    return out


def boxclip(T, lo, hi):
    m = np.all(T.max(1) >= lo, 1) & np.all(T.min(1) <= hi, 1)
    T = T[m]
    inside = np.all(T.min(1) >= lo, 1) & np.all(T.max(1) <= hi, 1)
    keep = [T[inside]]
    extra = []
    for t in T[~inside]:
        poly = [t[0], t[1], t[2]]
        for ax in range(3):
            poly = clip_poly(poly, ax, lo[ax], False)
            if len(poly) < 3:
                break
            poly = clip_poly(poly, ax, hi[ax], True)
            if len(poly) < 3:
                break
        if len(poly) >= 3:
            for k in range(1, len(poly) - 1):
                extra.append([poly[0], poly[k], poly[k + 1]])
    if extra:
        keep.append(np.array(extra))
    return np.concatenate(keep)


if __name__ == "__main__":
    stl, box, out, tag, views = sys.argv[1:6]
    W = int(sys.argv[6]) if len(sys.argv) > 6 else 1300
    title = sys.argv[7] if len(sys.argv) > 7 else tag
    b = [float(t) for t in box.split()]; lo = np.array(b[0::2]); hi = np.array(b[1::2])
    T = boxclip(read_stl(stl), lo, hi)
    V = T.reshape(-1, 3); TT = np.arange(len(V)).reshape(-1, 3)
    C = np.array([0.80, 0.80, 0.82])
    focus = np.array([[x, y, z] for x in b[0:2] for y in b[2:4] for z in b[4:6]], float)
    os.makedirs(out, exist_ok=True)
    for spec in views.split(";"):
        nm, d = spec.split("=")
        parts = d.split(",")
        light = None
        if parts[-1] == "g":
            light = "grazing"; parts = parts[:-1]
        d = [float(t) for t in parts]
        p = os.path.join(out, "%s_%s.png" % (tag, nm))
        mmpx = R.render(p, [(tag, V, TT, C)], d, W=W, pad=0.2, focus=focus, light=light,
                        title="%s - %s  box %s" % (title, nm, box), scale_bar=True)
        print(p, "mm/px %.4f" % mmpx, flush=True)

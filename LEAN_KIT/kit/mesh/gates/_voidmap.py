"""R5 survey probe (mine, read-only): map of x-ray crossing counts over a y-z grid inside an x range, before vs after. (a gate tool: kit mesh gate _voidmap --job <J> --tag <T> -- <args>)"""
import sys, struct
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
def rd(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)
def crossings(T, lo, hi, step):
    m = np.all(T.max(1) >= lo, 1) & np.all(T.min(1) <= hi, 1); T = T[m]
    gy = np.arange(lo[1] + step / 2, hi[1], step); gz = np.arange(lo[2] + step / 2, hi[2], step)
    Y, Z = np.meshgrid(gy, gz, indexing="ij"); Y = Y.ravel(); Z = Z.ravel()
    H = [[] for _ in range(len(Y))]
    for t in T:
        a, b, c = t[:, 1], t[:, 2], t[:, 0]
        bb = np.where((Y >= a.min()) & (Y <= a.max()) & (Z >= b.min()) & (Z <= b.max()))[0]
        if len(bb) == 0: continue
        e1 = np.array([a[1] - a[0], b[1] - b[0]]); e2 = np.array([a[2] - a[0], b[2] - b[0]])
        det = e1[0] * e2[1] - e1[1] * e2[0]
        if abs(det) < 1e-14: continue
        du = Y[bb] - a[0]; dv = Z[bb] - b[0]
        s = (du * e2[1] - dv * e2[0]) / det; r = (e1[0] * dv - e1[1] * du) / det
        ins = (s >= 0) & (r >= 0) & (s + r <= 1)
        w = c[0] + s * (c[1] - c[0]) + r * (c[2] - c[0])
        ok = ins & (w >= lo[0]) & (w <= hi[0])
        for i, ww in zip(bb[ok], w[ok]): H[i].append(ww)
    return gy, gz, [sorted(h) for h in H]
box = [float(t) for t in sys.argv[3].split()]; lo = np.array(box[0::2]); hi = np.array(box[1::2]); step = float(sys.argv[4])
res = {}
for lab, p in (("before", sys.argv[1]), ("after", sys.argv[2])):
    gy, gz, H = crossings(rd(p), lo, hi, step)
    cnt = np.array([len(h) for h in H]).reshape(len(gy), len(gz))
    res[lab] = (cnt, H)
cb, Hb = res["before"]; ca, Ha = res["after"]
extra = ca - cb
print("grid %d x %d at %.2f mm; rays where AFTER has MORE crossings than BEFORE: %d" % (len(gy), len(gz), step, int((extra > 0).sum())))
if (extra > 0).any():
    ii, jj = np.where(extra > 0)
    print("  their y %.2f..%.2f  z %.2f..%.2f" % (gy[ii].min(), gy[ii].max(), gz[jj].min(), gz[jj].max()))
    sk = []; vd = []
    for i, j in zip(ii, jj):
        h = Ha[i * len(gz) + j]
        if len(h) == 4:
            sk += [h[1] - h[0], h[3] - h[2]]; vd.append(h[2] - h[1])
    if sk:
        sk = np.array(sk); vd = np.array(vd)
        print("  4-crossing rays %d: skin min %.2f median %.2f max %.2f mm; void min %.2f median %.2f max %.2f mm" % (len(vd), sk.min(), np.median(sk), sk.max(), vd.min(), np.median(vd), vd.max()))
fig, axs = plt.subplots(1, 2, figsize=(12, 5.5))
for a_, (lab, c) in zip(axs, (("before", cb), ("after", ca))):
    im = a_.imshow(c.T, origin="lower", extent=(lo[1], hi[1], lo[2], hi[2]), vmin=0, vmax=6, cmap="viridis", interpolation="nearest")
    a_.set_title("%s: x-ray crossings in x %.0f..%.0f" % (lab, lo[0], hi[0])); a_.set_xlabel("y (mm)"); a_.set_ylabel("z (mm)")
plt.colorbar(im, ax=axs, shrink=0.8, label="crossings (2 = solid wall, 4 = hollow)")
plt.savefig(sys.argv[5], dpi=100); print(sys.argv[5])

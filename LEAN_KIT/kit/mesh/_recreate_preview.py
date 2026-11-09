import os, sys, numpy as np
sys.path.insert(0, os.environ["KIT_HOME"])
import kitlib_render as R
orig, res, tol = sys.argv[1], sys.argv[2], 0.15
box = [float(t) for t in sys.argv[3].split()] if len(sys.argv) > 3 else None
OV, OT = R.read_stl(orig); RV, RT = R.read_stl(res)
OV = np.asarray(OV, float); OT = np.asarray(OT, int); RV = np.asarray(RV, float); RT = np.asarray(RT, int)
P = np.vstack([OV, OV[OT].mean(1)])
if box:
    lo, hi = np.array(box[0::2]), np.array(box[1::2]); P = P[np.all((P >= lo) & (P <= hi), 1)]
P = P[np.linspace(0, len(P) - 1, min(len(P), 20000)).astype(int)]
c = RV[RT].mean(1); keep = np.all((c > P.min(0) - 3) & (c < P.max(0) + 3), 1)
d = R.point_tri_dist(P, RV, RT[keep])
off = d > tol
print("%s: %d samples, median %.3f p99 %.3f worst %.3f; off by > %.2f: %d" % (os.path.basename(orig), len(P), np.median(d), np.percentile(d, 99), d.max(), tol, off.sum()))
if off.any():
    ins = R.points_inside(P[off][:3000], RV, RT)
    print("   of those: BURIED (inside the result) %d, CUT (outside) %d" % (ins.sum(), (~ins).sum()))
    Q = P[off][~ins]
    if len(Q):
        print("   CUT samples extent:", np.round(Q.min(0), 1).tolist(), np.round(Q.max(0), 1).tolist())

import sys, numpy as np
src, dst, box = sys.argv[1], sys.argv[2], [float(t) for t in sys.argv[3].split()]
z = np.load(src); E = z["E"]; lo, hi = np.array(box[0::2]), np.array(box[1::2])
k = np.all((E >= lo) & (E <= hi), 1)
out = dict(E=E[k], M=float(z["M"]))
if "Mi" in z.files: out["Mi"] = z["Mi"][k]
np.savez_compressed(dst, **out)
print("kept %d of %d edit points inside %s" % (k.sum(), len(E), box))

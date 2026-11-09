import sys, numpy as np
from scipy.spatial import cKDTree
a, b, ao, bo = sys.argv[1:5]; Mn = float(sys.argv[5]) if len(sys.argv) > 5 else 0.6
A = np.load(a); B = np.load(b)
EA, EB = A["E"], B["E"]; MA, MB = float(A["M"]), float(B["M"])
reach = MA + MB + 0.6
dA = cKDTree(EB).query(EA)[0]; dB = cKDTree(EA).query(EB)[0]
MiA = np.where(dA < reach, Mn, MA); MiB = np.where(dB < reach, Mn, MB)
np.savez_compressed(ao, E=EA, M=MA, Mi=MiA); np.savez_compressed(bo, E=EB, M=MB, Mi=MiB)
print("A: %d of %d points narrowed to %.1f; B: %d of %d; zones' closest approach %.2f mm" % ((MiA < MA).sum(), len(EA), Mn, (MiB < MB).sum(), len(EB), dA.min()))

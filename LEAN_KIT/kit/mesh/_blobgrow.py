import os, json, numpy as np
z = np.load(os.environ["CC_BLOB"]); E = np.asarray(z["E"], float); M = float(z["M"])
add = np.array([[float(t) for t in p.split()] for p in os.environ["CC_POINTS"].split(";") if p.strip()])
E2 = np.vstack([E, add])
np.savez_compressed(os.environ["CC_OUT"], E=E2, M=M)
print("grew %s by %d point(s) -> %d; margin %.2f" % (os.path.basename(os.environ["CC_BLOB"]), len(add), len(E2), M))

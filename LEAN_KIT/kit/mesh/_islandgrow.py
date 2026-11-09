import os, sys, struct
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ccseam as S


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    t = a["v"].reshape(-1, 3, 3).astype(np.float64)
    q = np.round(t.reshape(-1, 3) / 1e-7).astype(np.int64)
    u, inv = np.unique(q, axis=0, return_inverse=True)
    return u * 1e-7, inv.reshape(-1, 3)


stem = os.environ["CC_WELD"]; lim = float(os.environ.get("CC_MAXLOOP", "15"))
VB, TB = read_stl(stem + "_patchcore.stl")
VB, TB = S._weld(VB, TB, 1e-7)
LB, _, _ = S._loops(TB)
LB = [l for l in LB if len(l) >= 3]
z = np.load(os.environ["CC_BLOB"]); E = z["E"]; M = float(z["M"])
add = []
for l in LB:
    P = VB[l]; diag = float(np.linalg.norm(P.max(0) - P.min(0)))
    tag = "ISLAND - grown over" if diag < lim else "kept (the core's own wall)"
    print("patch loop: %4d points, %.1f mm across, centre %s  %s" % (len(l), diag, np.round(P.mean(0), 1).tolist(), tag))
    if diag < lim:
        add.append(P[:: max(1, len(P) // 200)]); add.append(P.mean(0)[None])
if add:
    E2 = np.vstack([E] + add)
    out = {"E": E2, "M": M}
    if "Mi" in z.files:
        out["Mi"] = np.concatenate([z["Mi"], np.full(len(E2) - len(E), M)])
    np.savez_compressed(os.environ["CC_OUT"], **out)
    print("grew %s by %d point(s) -> %s" % (os.path.basename(os.environ["CC_BLOB"]), len(E2) - len(E), os.environ["CC_OUT"]))
else:
    print("no island")
    sys.exit(3)

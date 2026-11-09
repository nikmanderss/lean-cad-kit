import os, sys, struct, json
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def write_stl(p, T):
    T = T.astype(np.float32)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); ln = np.linalg.norm(n, axis=1); ln[ln == 0] = 1
    rec = np.zeros(len(T), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    rec["n"] = n / ln[:, None]; rec["v"] = T.reshape(-1, 9)
    with open(p, "wb") as f:
        f.write(b"the agent spikes and specks out".ljust(80, b" ")); f.write(struct.pack("<I", len(T))); f.write(rec.tobytes())


def topo(T):
    V, inv = np.unique(np.round(T.reshape(-1, 3), 6), axis=0, return_inverse=True); F = inv.reshape(-1, 3)
    E = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
    _, c = np.unique(E, axis=0, return_counts=True)
    return int((c == 1).sum()), int((c > 2).sum()), V, F


if not os.environ.get("CC_EXTENT", "").strip():
    print("FAIL: CC_EXTENT \"x0 x1 y0 y1 z0 z1\" (the body of record's extent) is not set - no default in the kit; kit mesh fills it from the atlas")
    raise SystemExit(2)
ext = [float(t) for t in os.environ["CC_EXTENT"].split()]
mg = float(os.environ.get("CC_MARGIN", "0.5")); SPECK = float(os.environ.get("CC_SPECK", "1.0"))
lo = np.array(ext[0::2]) - mg; hi = np.array(ext[1::2]) + mg
T = read_stl(os.environ["CC_IN"])
o0, n0, V, F = topo(T)
spike = np.any(np.any((T < lo) | (T > hi), 2), 1)
rows = np.concatenate([F[:, 0], F[:, 1], F[:, 0]]); cols = np.concatenate([F[:, 1], F[:, 2], F[:, 2]])
k, lab = connected_components(coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(len(V), len(V))), directed=False)
tl = lab[F[:, 0]]; cnt = np.bincount(tl, minlength=k); big = int(np.argmax(cnt))
speck = np.zeros(len(T), bool); specks = []
for c in range(k):
    if c == big or cnt[c] == 0:
        continue
    P = T[tl == c].reshape(-1, 3); size = float(np.linalg.norm(P.max(0) - P.min(0)))
    if size < SPECK:
        speck |= tl == c; specks.append({"triangles": int(cnt[c]), "size": size, "at": P.mean(0).round(2).tolist()})
drop = spike | speck
o1, n1, _, _ = topo(T[~drop])
rep = {"in": len(T), "spike_triangles": int(spike.sum()), "specks": specks, "open": [o0, o1], "nonmanifold": [n0, n1],
       "shells_in": int((cnt > 0).sum())}
if spike.any():
    P = T[spike].reshape(-1, 3); rep["spike_extent"] = [P.min(0).round(2).tolist(), P.max(0).round(2).tolist()]
print("spike triangles %d, specks %d (%s), open %d -> %d, non-manifold %d -> %d"
      % (spike.sum(), len(specks), ", ".join("%d tri %.2f mm" % (s["triangles"], s["size"]) for s in specks), o0, o1, n0, n1))
if o1 > o0 or n1 > n0:
    print("REFUSED: removing them would raise open or non-manifold edges"); sys.exit(2)
write_stl(os.environ["CC_OUT"], T[~drop])
json.dump(rep, open(os.environ["CC_OUT"] + ".json", "w"), indent=1)
print("wrote", os.environ["CC_OUT"])

"""review2/R1 - edge-connected shells of a mesh; report every shell other than the largest (extent, area, signed (a gate tool: kit mesh gate _shells --job <J> --tag <T> -- <args>)"""
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from _sec import read_stl

T = read_stl(sys.argv[1])
n = len(T)
V = T.reshape(-1, 3)
q = np.round(V / 1e-5).astype(np.int64)
_, vid = np.unique(q, axis=0, return_inverse=True)
vid = vid.reshape(-1, 3)
E = np.concatenate([vid[:, [0, 1]], vid[:, [1, 2]], vid[:, [2, 0]]])
E.sort(1)
tri = np.concatenate([np.arange(n)] * 3)
key = E[:, 0] * (vid.max() + 1) + E[:, 1]
order = np.argsort(key)
ks = key[order]; ts = tri[order]
same = ks[1:] == ks[:-1]
a = ts[:-1][same]; b = ts[1:][same]
G = coo_matrix((np.ones(len(a)), (a, b)), shape=(n, n))
nc, lab = connected_components(G, directed=False)
cnt = np.bincount(lab)
big = np.argmax(cnt)
print("triangles %d, edge-connected shells %d, largest %d tri" % (n, nc, cnt[big]))
area = 0.5 * np.linalg.norm(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]), axis=1)
sv = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])) / 6.0
others = [c for c in np.argsort(-cnt) if c != big]
for c in others[:25]:
    m = lab == c
    P = T[m].reshape(-1, 3)
    print("  shell %6d: %6d tri, area %8.3f mm2, signed vol %+9.4f mm3, x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (
        c, m.sum(), area[m].sum(), sv[m].sum(), P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max(), P[:, 2].min(), P[:, 2].max()))
if len(sys.argv) > 2:
    C = T.mean(1)
    for s in sys.argv[2].split(";"):
        p = np.array([float(t) for t in s.split(",")])
        d = np.linalg.norm(C - p, axis=1)
        i = np.argsort(d)[:5]
        print("  probe %s: nearest tri shells %s (dist %s)" % (s, list(lab[i]), np.round(d[i], 3)))
np.save(sys.argv[1].replace("\\", "/").split("/")[-1] + ".shells.npy", lab) if False else None

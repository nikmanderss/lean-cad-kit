"""non-manifold edges in AFTER that are not in BASE:  python _nmnew.py <base.stl> <after.stl> (a gate tool: kit mesh gate _nmnew --job <J> --tag <T> -- <args>)"""
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sec import read_stl
def nm(p):
    T = read_stl(p)
    V, inv = np.unique(np.round(T.reshape(-1, 3), 6), axis=0, return_inverse=True); F = inv.reshape(-1, 3)
    E = np.sort(np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
    u, c = np.unique(E, axis=0, return_counts=True)
    m = u[c > 2]
    return (V[m[:, 0]] + V[m[:, 1]]) / 2, c[c > 2]
Pb, _ = nm(sys.argv[1]); Pa, ca = nm(sys.argv[2])
from scipy.spatial import cKDTree
d, _ = cKDTree(Pb).query(Pa)
new = Pa[d > 1e-3]; cn = ca[d > 1e-3]
print("non-manifold edges in after not in base: %d" % len(new))
for p, c in zip(np.round(new, 3).tolist(), cn): print("  ", p, "uses", c)

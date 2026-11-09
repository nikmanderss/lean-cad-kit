"""review2/R1 - point-in-solid by ray parity along several directions (majority vote), before and after. (a gate tool: kit mesh gate _inside --job <J> --tag <T> -- <args>)"""
import sys, struct
import numpy as np


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def ray_count(tri, o, d):
    e1 = tri[:, 1] - tri[:, 0]; e2 = tri[:, 2] - tri[:, 0]
    p = np.cross(d, e2); det = np.einsum("ij,ij->i", e1, p)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    s = o - tri[:, 0]
    u = np.einsum("ij,ij->i", s, p) * inv
    q = np.cross(s, e1)
    v = (q @ d) * inv
    t = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-9)
    return int(hit.sum())


if __name__ == "__main__":
    T = read_stl(sys.argv[1])
    dirs = [np.array(v, float) / np.linalg.norm(v) for v in ([1, 0.013, 0.007], [-1, 0.011, -0.017], [0.009, 1, 0.013], [0.012, -1, 0.004], [0.006, 0.014, 1], [0.015, -0.008, -1])]
    for s in sys.argv[2].split(";"):
        o = np.array([float(t) for t in s.split(",")])
        c = [ray_count(T, o, d) % 2 for d in dirs]
        print("%-28s parity %s -> %s" % (s, c, "SOLID" if sum(c) >= 4 else ("air" if sum(c) <= 2 else "??")))

# MESH_JOB
# does not exist
# CC_PATCH
import os, struct, json
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


def say(*a):
    print(*a, flush=True)


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


def sample(tri, step, rng):
    a = 0.5 * np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    n = np.maximum(1, np.ceil(a / (step * step) * 2)).astype(int)
    idx = np.repeat(np.arange(len(tri)), n)
    r1 = np.sqrt(rng.random(len(idx))); r2 = rng.random(len(idx))
    t = tri[idx]
    return (1 - r1)[:, None] * t[:, 0] + (r1 * (1 - r2))[:, None] * t[:, 1] + (r1 * r2)[:, None] * t[:, 2]


def box(s):
    v = [float(t) for t in s.split()]
    return np.array(v[0::2]), np.array(v[1::2])


BOXLO, BOXHI = box(os.environ["CC_BOX"])
INSET = float(os.environ.get("CC_INSET", "1.6"))
lo, hi = BOXLO + INSET, BOXHI - INSET
SLO, SHI = box(os.environ["CC_SEL"])
ALO, AHI = box(os.environ["CC_ALLOW"]) if os.environ.get("CC_ALLOW") else (lo, hi)
M = float(os.environ.get("CC_M", "1.5"))
TOL = float(os.environ.get("CC_TOL", "0.12"))
rng = np.random.default_rng(1)
B = read_stl(os.environ["CC_BASE"]); P = read_stl(os.environ["CC_PATCH"])


def inbox(tri, m=0.0):
    c = tri.mean(1); return np.all((c >= lo - m) & (c <= hi + m), axis=1)


Bs = sample(B[inbox(B, 3)], 0.06, rng); Bs = Bs[np.all((Bs >= lo) & (Bs <= hi), axis=1)]
Ps = sample(P[inbox(P, 1)], 0.06, rng); Ps = Ps[np.all((Ps >= lo) & (Ps <= hi), axis=1)]
dB = cKDTree(Ps).query(Bs)[0]
dP = cKDTree(Bs).query(Ps)[0]
E = np.vstack([Bs[dB > TOL], Ps[dP > TOL]])
say("disagreement > %.2f mm: %d body samples (REMOVED, worst %.2f), %d patch samples (ADDED, worst %.2f)"
    % (TOL, (dB > TOL).sum(), dB.max(), (dP > TOL).sum(), dP.max()))
g = np.unique(np.round(E / 0.2).astype(np.int64), axis=0)
E = g * 0.2
tr = cKDTree(E)
pr = tr.query_pairs(0.5, output_type="ndarray")
A = coo_matrix((np.ones(len(pr)), (pr[:, 0], pr[:, 1])), shape=(len(E), len(E)))
nc, lab = connected_components(A, directed=False)
cnt = np.bincount(lab)
say("%d disagreement points (0.2 mm voxels) in %d clusters; largest %s" % (len(E), nc, sorted(cnt, reverse=True)[:6]))
insel = np.all((E >= SLO) & (E <= SHI), axis=1)
chosen = set(np.unique(lab[insel]).tolist())
if not chosen:
    say("REFUSED: no disagreement inside CC_SEL - nothing to weld here")
    raise SystemExit(2)
ABS = float(os.environ.get("CC_ABSORB", "0.5"))
while True:
    selpts = E[np.isin(lab, list(chosen))]
    st = cKDTree(selpts)
    d_other = st.query(E)[0]
    near = set(np.unique(lab[(d_other <= M + ABS) & ~np.isin(lab, list(chosen))]).tolist())
    if not near:
        break
    chosen |= near
selpts = E[np.isin(lab, list(chosen))]
trimmed = np.zeros((0, 3))
if os.environ.get("CC_TRIM"):
    TLO, THI = box(os.environ["CC_TRIM"])
    kin = np.all((selpts >= TLO) & (selpts <= THI), axis=1)
    trimmed = selpts[~kin]; selpts = selpts[kin]
    say("CC_TRIM %s: kept %d edit points, trimmed %d%s" % (os.environ["CC_TRIM"], len(selpts), len(trimmed),
        (", extent x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f"
         % tuple(v for k in range(3) for v in (trimmed[:, k].min(), trimmed[:, k].max()))) if len(trimmed) else ""))
say("the edit: %d cluster(s), %d points, extent x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f"
    % (len(chosen), len(selpts), *[v for k in range(3) for v in (selpts[:, k].min(), selpts[:, k].max())]))
refuse = []
out_allow = selpts[~np.all((selpts >= ALO) & (selpts <= AHI), axis=1)]
if len(out_allow):
    refuse.append("%d edit points lie outside CC_ALLOW (the box this edit may occupy), extent %s .. %s"
                  % (len(out_allow), np.round(out_allow.min(0), 1).tolist(), np.round(out_allow.max(0), 1).tolist()))
room_lo = selpts.min(0) - lo; room_hi = hi - selpts.max(0)
names = "xyz"
for k in range(3):
    if room_lo[k] < M + 0.3:
        refuse.append("the edit comes within %.1f mm of the extract box's %s-min cap (needs %.1f): widen the box there"
                      % (room_lo[k], names[k], M + 0.3))
    if room_hi[k] < M + 0.3:
        refuse.append("the edit comes within %.1f mm of the extract box's %s-max cap (needs %.1f): widen the box there"
                      % (room_hi[k], names[k], M + 0.3))
others = np.vstack([E[~np.isin(lab, list(chosen))], trimmed])
dmin = cKDTree(selpts).query(others)[0].min() if len(others) else 99
say("nearest disagreement NOT in the edit: %.1f mm from it (the wall sits at %.1f)" % (dmin, M))
rep = {"M": M, "tol": TOL, "box": os.environ["CC_BOX"], "sel": os.environ["CC_SEL"], "points": int(len(selpts)),
       "extent": [selpts.min(0).tolist(), selpts.max(0).tolist()], "room_lo": room_lo.tolist(),
       "room_hi": room_hi.tolist(), "nearest_other": float(dmin), "refused": refuse}
if os.environ.get("CC_PNG"):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(21, 7))
    for k, (i, j, nm) in enumerate(((0, 1, "PLAN: across = side to side, up the page = rear"),
                                   (1, 2, "SIDE: across = front (left) to rear (right), up = height"),
                                   (0, 2, "END (from the front): across = side to side, up = height"))):
        a = ax[k]
        sb = Bs[:: max(1, len(Bs) // 40000)]
        a.scatter(sb[:, i], sb[:, j], s=0.3, c="0.82")
        if len(others): a.scatter(others[:, i], others[:, j], s=1, c="red", label="disagreement NOT in this edit")
        a.scatter(selpts[:, i], selpts[:, j], s=1, c="darkorange", label="this edit (the core is it grown by %.1f mm)" % M)
        a.add_patch(plt.Rectangle((lo[i], lo[j]), hi[i] - lo[i], hi[j] - lo[j], fill=False, ec="blue", lw=1.2, label="usable extract box"))
        a.set_title(nm, fontsize=10); a.set_aspect("equal"); a.grid(alpha=.3)
    ax[0].legend(loc="upper right", fontsize=8, markerscale=6)
    fig.suptitle("Edit zone core. %s" % ("REFUSED: " + "; ".join(refuse) if refuse else "clean"), fontsize=10)
    fig.tight_layout(); fig.savefig(os.environ["CC_PNG"], dpi=85)
    say("wrote", os.environ["CC_PNG"])
if refuse:
    for r in refuse:
        say("REFUSED: " + r)
    json.dump(rep, open(os.environ["CC_OUT"].replace(".npz", ".json"), "w"), indent=1)
    raise SystemExit(2)
np.savez_compressed(os.environ["CC_OUT"], E=selpts, M=M)
json.dump(rep, open(os.environ["CC_OUT"].replace(".npz", ".json"), "w"), indent=1)
say("wrote %s - core = within %.1f mm of %d points" % (os.environ["CC_OUT"], M, len(selpts)))

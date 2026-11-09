import os, sys, json, glob
import numpy as np
from scipy.spatial import cKDTree

WORK = os.environ.get("CC_WORK") or os.getcwd()
out = sys.argv[1]
files = sorted(glob.glob(os.path.join(WORK, "Z*", "pieces.json"))) + sys.argv[2:]
pieces = []
for f in files:
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception as e:
        print("could not read %s: %s" % (f, e)); continue
    for p in d.get("pieces", []):
        # recorded
        v = str(p.get("verdict", "")).upper()
        rv = str(p.get("review", "APPROVE" if os.environ.get("CC_ALLOW_UNREVIEWED") == "1" else "NOT REVIEWED")).upper()
        ok = v.startswith("GOOD") and rv in ("APPROVE", "APPROVE_WITH_NOTES")
        print("%-8s %-28s verdict %-10s review %-20s %s" % (os.path.basename(os.path.dirname(f)), p.get("name"), v[:10], rv[:20],
                                                           "IN" if ok else "out"))
        if ok:
            for k in ("patch", "blob", "weld", "crop"):
                if not p.get(k) or not os.path.exists(p[k]):
                    print("   *** missing %s: %s%s" % (k, p.get(k), "   (the crop flow needs the welded CROP and its .crop.json)"
                                                       if k in ("weld", "crop") else "")); ok = False
        if ok:
            pieces.append({"name": p["name"], "patch": p["patch"], "blob": p["blob"], "weld": p["weld"], "crop": p["crop"],
                           "zone": os.path.basename(os.path.dirname(f)), "weld_sets": p.get("weld_sets", [])})
E = {}
for p in pieces:
    z = np.load(p["blob"])
    E[p["name"]] = (z["E"], z["Mi"].astype(float) if "Mi" in z.files else np.full(len(z["E"]), float(z["M"])))
clash = []
names = [p["name"] for p in pieces]
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, ma = E[names[i]]; b, mb = E[names[j]]
        lo = np.maximum(a.min(0), b.min(0)) - 5; hi = np.minimum(a.max(0), b.max(0)) + 5
        if np.any(lo > hi):
            continue
        dk, ik = cKDTree(a).query(b, k=8)
        gap = float((dk - mb[:, None] - ma[ik]).min())
        if gap < 0.2:
            clash.append((names[i], names[j], round(float(dk.min()), 2), round(gap, 2)))
for c in clash:
    print("CLASH: %s and %s: edit points %.2f mm apart, cores %.2f mm clear (need 0.2)" % c)
json.dump({"edits": pieces, "clashes": clash}, open(out, "w"), indent=1)
print("%d piece(s) in the manifest, %d clash(es) -> %s" % (len(pieces), len(clash), out))
sys.exit(2 if clash else 0)

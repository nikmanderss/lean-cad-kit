# KIT INSTRUMENT `atlas_features` - regroup an `atlas_split` into the FEATURES the client names, move pieces by
# rule, and write the feature compounds + facemap. No geometry is cut or changed: pieces are regrouped.
# Run: kit tool atlas_features --job <JOB> --set ATLAS_SPLIT=<split folder> --set ATLAS_FEATURES=<features.json> ...
# Inputs: ATLAS_SPLIT (the folder atlas_split wrote)  ATLAS_FEATURES (below)  ATLAS_MOVES (optional, below)
#         ATLAS_OUTDIR (default: <ATLAS_SPLIT>\features)
# the client, 2026-09-22: regions are FEATURES, not a breakdown - "If the whole skirt is named 'the skirt' - then when I
# say front corners or interior corners it's still obvious what that means." So the fine split is regrouped.
#
# ATLAS_FEATURES: [{"name": "skirt", "from": ["fine_a", "fine_b"], "rgb": [r,g,b], "note": "what it IS",
#                   "definition": "DRAFT", "edit": "OPEN"}, ...]   - every fine region must land in exactly one.
# ATLAS_MOVES (the client's corrections, applied in this order):
#   {"faces": {"<body face>": "<feature>"}          - every piece of that body face goes to that feature;
#    "rules": [{"from": ["feat", ...] | "*", "to": "feat", "box": [x0,x1,y0,y1,z0,z1],
#               "near_points": {"pts": [[x,y,z], ...], "tol": mm}, "except_faces": [...], "why": "..."}]}
#   A rule moves the pieces whose centre of mass satisfies every condition it gives.
# THE GATE: the features' total area and piece count must equal the split's - regrouping cannot lose surface.
import os, sys, json, time
sys.path.insert(0, os.environ["KIT_HOME"])
import Part


def say(*a):
    print(*a, flush=True)


T0 = time.time()
S = os.environ["ATLAS_SPLIT"]
fine = json.load(open(os.path.join(S, "manifest.json"), encoding="utf-8"))
feats = json.load(open(os.environ["ATLAS_FEATURES"], encoding="utf-8"))
moves = json.load(open(os.environ["ATLAS_MOVES"], encoding="utf-8")) if os.environ.get("ATLAS_MOVES") else {}
D = os.environ.get("ATLAS_OUTDIR") or os.path.join(S, "features")
os.makedirs(D, exist_ok=True)

names = [f["name"] for f in feats]
if len(set(names)) != len(names):
    say("REFUSED: a feature name appears twice"); raise SystemExit(2)
owner = {}
for f in feats:
    for n in f.get("from", []):
        if n in owner:
            say("REFUSED: fine region %s is claimed by both %s and %s" % (n, owner[n], f["name"])); raise SystemExit(2)
        owner[n] = f["name"]
orphans = [n for n in fine if n not in owner]
if orphans:
    say("REFUSED: %d fine region(s) belong to no feature: %s - every piece of the split must land somewhere"
        % (len(orphans), ", ".join(orphans))); raise SystemExit(2)

pieces = {nm: [] for nm in names}
area0 = n0 = 0
for n, spec in fine.items():
    s = Part.Shape(); s.importBrep(spec["brep"])
    if len(s.Faces) != len(spec["from_faces"]):
        say("REFUSED: %s has %d faces and %d origins - a manifest from another run" % (n, len(s.Faces), len(spec["from_faces"])))
        raise SystemExit(2)
    for g, fid in zip(s.Faces, spec["from_faces"]):
        pieces[owner[n]].append((g, int(fid), g.CenterOfMass))
        area0 += g.Area; n0 += 1
say("split: %d region(s), %d piece(s), %.1f mm2 -> %d feature(s)" % (len(fine), n0, area0, len(names)))

fo = {int(k): v for k, v in (moves.get("faces") or {}).items()}
for k, v in fo.items():
    if v not in pieces:
        say("REFUSED: face override Face%d -> %r, which is not a feature" % (k, v)); raise SystemExit(2)
if fo:
    n_ = 0
    for nm in names:
        keep = []
        for p in pieces[nm]:
            dst = fo.get(p[1])
            if dst and dst != nm:
                pieces[dst].append(p); n_ += 1
            else:
                keep.append(p)
        pieces[nm] = keep
    say("face overrides: %d piece(s) moved" % n_)


def _ok(c, rule):
    b = rule.get("box")
    if b and not (b[0] <= c.x <= b[1] and b[2] <= c.y <= b[3] and b[4] <= c.z <= b[5]):
        return False
    npn = rule.get("near_points")
    if npn and not any(((c.x - q[0]) ** 2 + (c.y - q[1]) ** 2 + (c.z - q[2]) ** 2) ** 0.5 <= npn["tol"] for q in npn["pts"]):
        return False
    return True


for rule in moves.get("rules", []) or []:
    dst = rule["to"]
    if dst not in pieces:
        say("REFUSED: rule to %r, which is not a feature" % dst); raise SystemExit(2)
    srcs = names if rule.get("from") == "*" else rule.get("from", [])
    exc = set(int(x) for x in rule.get("except_faces", []))
    moved = 0
    for src in srcs:
        if src == dst or src not in pieces:
            continue
        keep = []
        for p in pieces[src]:
            if p[1] not in exc and _ok(p[2], rule):
                pieces[dst].append(p); moved += 1
            else:
                keep.append(p)
        pieces[src] = keep
    say("  rule -> %-20s %5d piece(s)   %s" % (dst, moved, rule.get("why", "")))

man, fmap, regs = {}, {}, {}
area1 = n1 = 0
for f in feats:
    lst = pieces[f["name"]]
    if not lst:
        say("  %-26s EMPTY" % f["name"]); continue
    p = os.path.join(D, f["name"] + ".brep")
    Part.Compound([g for g, _, _ in lst]).exportBrep(p)
    a = float(sum(g.Area for g, _, _ in lst))
    man[f["name"]] = {"brep": p, "rgb": f.get("rgb", [205, 205, 210]), "pieces": len(lst), "area": a,
                      "from_faces": [fid for _, fid, _ in lst], "note": f.get("note", "")}
    fmap[f["name"]] = {str(i + 1): fid for i, (_, fid, _) in enumerate(lst)}
    regs[f["name"]] = {"rgb": f.get("rgb"), "definition": f.get("definition", "DRAFT"), "edit": f.get("edit", "OPEN"),
                       "note": f.get("note", "")}
    area1 += a; n1 += len(lst)
    say("  %-26s %5d piece(s) %10.0f mm2" % (f["name"], len(lst), a))
json.dump(man, open(os.path.join(D, "manifest.json"), "w", encoding="utf-8"), indent=1)
json.dump(fmap, open(os.path.join(D, "facemap.json"), "w", encoding="utf-8"), indent=1)
json.dump(regs, open(os.path.join(D, "regions.json"), "w", encoding="utf-8"), indent=1)
ok = (n1 == n0) and abs(area1 - area0) <= 1e-6 * max(area0, 1.0) + 1e-3
json.dump({"state": "done" if ok else "REFUSED", "pieces_in": n0, "pieces_out": n1, "area_in": round(area0, 1),
           "area_out": round(area1, 1), "seconds": round(time.time() - T0, 1)},
          open(os.path.join(D, "status_atlas_features.json"), "w", encoding="utf-8"), indent=1)
say("pieces %d -> %d, area %.1f -> %.1f mm2  (%.0f s)" % (n0, n1, area0, area1, time.time() - T0))
if not ok:
    say("REFUSED: regrouping changed the piece count or the area - a piece was lost or doubled"); raise SystemExit(2)
say("DONE")

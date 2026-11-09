# two pieces
import os, sys, json, subprocess, time, struct, shutil
import numpy as np

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get("KIT_HOME") or os.path.dirname(SRC))
import kit_crop as KC
import kitlib_render as R

WORK = os.environ.get("CC_WORK") or os.getcwd()
OUT = os.path.abspath(os.environ.get("CC_FINAL_OUT") or os.path.join(WORK, "final")).replace("\\", "/")
os.makedirs(OUT, exist_ok=True)
NAME = os.environ.get("CC_NAME", "reworked").strip() or "reworked"
BASE = os.environ.get("CC_BASE", "").strip()
if not BASE or not os.path.isfile(BASE):
    print("FAIL: CC_BASE (the one unchanged base mesh every crop was cut from) is not set or not a file"); sys.exit(2)
_ext = os.environ.get("CC_EXTENT", "").strip()
if not _ext:
    print("FAIL: CC_EXTENT \"x0 x1 y0 y1 z0 z1\" is not set (kit mesh fills it from the atlas; name it here otherwise)"); sys.exit(2)
EXT = [float(t) for t in _ext.split()]
NOWIN = 0x08000000 if os.name == "nt" else 0
man = json.load(open(sys.argv[1], encoding="utf-8"))
edits = man["edits"]


def run(script, env_extra, args=()):
    t = time.time()
    r = subprocess.run([sys.executable, "-W", "ignore", os.path.join(SRC, script)] + list(args),
                       env=dict(os.environ, **env_extra), capture_output=True, text=True, creationflags=NOWIN)
    return r, time.time() - t


pieces, missing = [], []
for e in edits:
    w, c = e.get("weld", ""), e.get("crop", "")
    if not (w and c and os.path.isfile(w) and os.path.isfile(c)):
        missing.append(e.get("name", "?")); continue
    meta, eV, eT = KC._load_piece(w, c)
    meta["_edited"] = os.path.abspath(w)
    pieces.append((meta, eV, eT))
if missing:
    print("REFUSED: %d edit(s) have no welded crop + crop.json pair: %s" % (len(missing), ", ".join(missing))); sys.exit(4)
bV, bT = R.read_stl(BASE)
raw = OUT + "/" + NAME + "_raw.stl"
t0 = time.time()
try:
    V, T, rep = KC.splice_many(bV, bT, pieces)
except RuntimeError as ex:
    print("1. splice %s" % ex); sys.exit(3)
R.write_stl(raw, V, T)
rep.update({"target": BASE, "out": raw, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "secs": round(time.time() - t0, 1)})
json.dump(rep, open(raw[:-4] + ".splice.json", "w"), indent=1)
print("1. splice: %d piece(s) into %s -> %d triangles, open edges %d -> %d, non-manifold %d -> %d, %.0f s"
      % (len(pieces), os.path.basename(BASE), rep["result_triangles"], rep["open_edges_target"], rep["open_edges_result"],
         rep["nonmanifold_target"], rep["nonmanifold_result"], rep["secs"]))
print("   " + rep["outside_identity"])

clean = OUT + "/" + NAME + "_clean.stl"
base_clean = OUT + "/" + "base_final_clean.stl"
for src_, dst_ in ((raw, clean), (BASE, base_clean)):
    r3, dt = run("_ccspikes.py", dict(CC_IN=src_, CC_OUT=dst_, CC_EXTENT=_ext))
    print("2. spikes/specks %-24s rc %s %.0f s %s%s" % (os.path.basename(src_), r3.returncode, dt, r3.stdout.strip()[-400:], r3.stderr[-300:]))
    if r3.returncode != 0:
        shutil.copyfile(src_, dst_)
ndl = OUT + "/" + NAME + "_clean_needle.stl"
box = "%g %g %g %g %g %g" % (EXT[0] - 2, EXT[1] + 2, EXT[2] - 2, EXT[3] + 2, EXT[4] - 2, EXT[5] + 2)
r4, dt = run("_ccneedle.py", dict(CC_REF=base_clean), [clean, ndl, box])
print("3. needles rc %s %.0f s\n%s%s" % (r4.returncode, dt, r4.stdout[-2500:], r4.stderr[-1000:]))
if r4.returncode == 0 and os.path.isfile(ndl):
    shutil.copyfile(ndl, clean)
merged = OUT + "/" + NAME + ".stl"
r2, dt = run("_ccnmfix.py", dict(CC_IN=clean, CC_OUT=merged, CC_REF=base_clean))
print("4. pinch fix rc %s %.0f s\n%s%s" % (r2.returncode, dt, r2.stdout[-1500:], r2.stderr[-1000:]))
if r2.returncode != 0 or not os.path.isfile(merged):
    shutil.copyfile(clean, merged)
tmp_ = merged[:-4] + "_specks.stl"
r5, dt = run("_ccspikes.py", dict(CC_IN=merged, CC_OUT=tmp_, CC_EXTENT=_ext))
print("5. specks after the pinch fix rc %s %.0f s %s%s" % (r5.returncode, dt, r5.stdout.strip()[-600:], r5.stderr[-300:]))
if r5.returncode == 0 and os.path.isfile(tmp_):
    shutil.copyfile(tmp_, merged)


def read_stl(p):
    b = open(p, "rb").read(); n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(np.float64)


B = read_stl(base_clean); M = read_stl(merged)
def keys(t):
    q = np.round(t / 1e-4).astype(np.int64)
    s = np.sort(q.view([("x", np.int64), ("y", np.int64), ("z", np.int64)]).reshape(-1, 3), axis=1)
    return set(map(bytes, s.view(np.int64).reshape(-1, 9)))
bk = keys(B)
q = np.round(M / 1e-4).astype(np.int64)
s = np.sort(q.view([("x", np.int64), ("y", np.int64), ("z", np.int64)]).reshape(-1, 3), axis=1).view(np.int64).reshape(-1, 9)
new = np.array([bytes(k) not in bk for k in s])
C = M[new].astype(np.float32)
nrm = np.cross(C[:, 1] - C[:, 0], C[:, 2] - C[:, 0]); ln = np.linalg.norm(nrm, axis=1); ln[ln == 0] = 1
rec = np.zeros(len(C), dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
rec["n"] = nrm / ln[:, None]; rec["v"] = C.reshape(-1, 9)
cp = OUT + "/" + NAME + "_changed_only.stl"
with open(cp, "wb") as f:
    f.write(b"the agent changed only".ljust(80, b" ")); f.write(struct.pack("<I", len(C))); f.write(rec.tobytes())
print("6. changed-only mesh: %d of %d triangles -> %s" % (len(C), len(M), cp))
json.dump({"edits": edits, "pieces": [p[0]["_edited"] for p in pieces], "merged": merged, "original": base_clean,
           "raw": raw, "splice": rep, "when": time.strftime("%Y-%m-%d %H:%M:%S")},
          open(OUT + "/" + "final_report.json", "w"), indent=1)
print("DONE")

"""selftest_cuts_gate.py - THE ORBIT OF THE CUTS IS JUDGED BEFORE THE WORK CONTINUES (kit_rebuild.judge / cuts_verdict, 31ai),
without a kernel. the client, 2026-10-05: "the cuts should be render reviewed by an orbit pass before continuing work."
Cases: no orbit on disk -> judge refuses; a short note -> refused; a real note -> recorded, the verdict reads ok; the artefact
changes (a re-run region / keep) -> the old verdict no longer counts; a 'move' verdict -> the gate refuses; the frames listed
must exist; the frames of an earlier artefact cannot be judged."""
import os, sys, json, shutil, tempfile, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kit_rebuild as KR
ok = 0; bad = 0
def check(cond, what):
    global ok, bad
    if cond: ok += 1; print("  ok   " + what)
    else: bad += 1; print("  FAIL " + what)

class Kit:
    def __init__(self, root): self.ROOT = root
    @staticmethod
    def _opt(args, name, default=None):
        return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default

root = tempfile.mkdtemp(prefix="cutsgate_"); job = "JOBX"; folder = os.path.join(root, "claude_code", "jobs", job)
os.makedirs(os.path.join(folder, "review")); os.makedirs(os.path.join(folder, "keep"))
out = []
say = lambda *a: out.append(" ".join(str(x) for x in a))
K = Kit(root)
try:
    for what, sub, cuts_fn, art_fn, mk in (("region", "review", "CUTS_REGION.json", "content.brep", "content_md5"), ("keep", "keep", "CUTS.json", "keep_region.brep", "region_md5")):
        art = os.path.join(folder, art_fn)
        open(art, "wb").write(b"first version of the artefact")
        out.clear(); rc = KR.judge(["--job", job, "--what", what, "--verdict", "ok", "--note", "the red cuts cross the skins everywhere I looked"], K, say)
        check(rc == 2 and "missing" in " ".join(out), "%s: judge REFUSES when the step wrote no orbit (%s)" % (what, out[-1][:70] if out else ""))
        frames = ["%s_cuts_above.png" % what, "%s_cuts_below.png" % what]
        for f in frames: open(os.path.join(folder, sub, f), "wb").write(b"png")
        md5 = hashlib.md5(open(art, "rb").read()).hexdigest()
        json.dump({"frames": frames, mk: md5}, open(os.path.join(folder, sub, cuts_fn), "w"))
        out.clear(); rc = KR.judge(["--job", job, "--what", what, "--verdict", "ok", "--note", "fine"], K, say)
        check(rc == 2 and "--note" in " ".join(out), "%s: a one-word note is REFUSED" % what)
        okv, why = KR.cuts_verdict(folder, what)
        check(not okv, "%s: no verdict yet -> the gate refuses (%s)" % (what, why[:60]))
        out.clear(); rc = KR.judge(["--job", job, "--what", what, "--verdict", "ok", "--note", "every red cut crosses the skins; none runs along a lip"], K, say)
        okv, why = KR.cuts_verdict(folder, what)
        check(rc == 0 and okv, "%s: a judged 'ok' opens the gate (%s)" % (what, why[:60]))
        open(art, "wb").write(b"second version - the step ran again")
        okv, why = KR.cuts_verdict(folder, what)
        check(not okv and "earlier" in why, "%s: a re-run step's new cuts need a new look (%s)" % (what, why[:70]))
        out.clear(); rc = KR.judge(["--job", job, "--what", what, "--verdict", "ok", "--note", "judging the old frames against the new artefact"], K, say)
        check(rc == 2 and "earlier" in " ".join(out), "%s: the frames of an earlier artefact cannot be judged" % what)
        md5 = hashlib.md5(open(art, "rb").read()).hexdigest(); json.dump({"frames": frames, mk: md5}, open(os.path.join(folder, sub, cuts_fn), "w"))
        out.clear(); rc = KR.judge(["--job", job, "--what", what, "--verdict", "move", "--note", "one cut runs flat inside the side lip - moving it"], K, say)
        okv, why = KR.cuts_verdict(folder, what)
        check(rc == 0 and not okv and "move" in why, "%s: a 'move' verdict keeps the gate shut (%s)" % (what, why[:60]))
        os.remove(os.path.join(folder, sub, frames[0])); os.remove(os.path.join(folder, sub, frames[1]))
        out.clear(); rc = KR.judge(["--job", job, "--what", what, "--verdict", "ok", "--note", "frames gone from the disk - cannot be judged"], K, say)
        check(rc == 2 and "not on disk" in " ".join(out), "%s: frames that are not on disk cannot be judged" % what)
finally:
    shutil.rmtree(root, ignore_errors=True)
print("%d passed, %d FAILED" % (ok, bad))
sys.exit(1 if bad else 0)

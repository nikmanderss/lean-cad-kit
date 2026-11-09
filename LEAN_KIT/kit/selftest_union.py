import os, sys, json, shutil, subprocess, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kitlib_render as R
import kit_union as KU

FAILED = []


def check(label, cond, detail=""):
    print("  %-4s %s" % ("ok" if cond else "FAIL", label))
    if not cond:
        print("       %s" % str(detail)[:500])
        FAILED.append(label)


def box_mesh(lo, hi, n=(4, 4, 4), inward=False):
    """an axis-aligned box as a welded, outward triangle mesh; each face an n x m grid"""
    lo = np.asarray(lo, float); hi = np.asarray(hi, float)
    tris = []
    for ax in range(3):
        b, c = (ax + 1) % 3, (ax + 2) % 3
        for side in (0, 1):
            fixed = hi[ax] if side else lo[ax]
            nb, nc = n[b], n[c]
            for i in range(nb):
                for j in range(nc):
                    def P(ii, jj):
                        p = np.zeros(3); p[ax] = fixed
                        p[b] = lo[b] + (hi[b] - lo[b]) * ii / nb
                        p[c] = lo[c] + (hi[c] - lo[c]) * jj / nc
                        return p
                    q = [P(i, j), P(i + 1, j), P(i + 1, j + 1), P(i, j + 1)]
                    for t in ([q[0], q[1], q[2]], [q[0], q[2], q[3]]):
                        nn = np.cross(t[1] - t[0], t[2] - t[0])
                        want = (1.0 if side else -1.0) * (-1.0 if inward else 1.0)
                        if nn[ax] * want < 0:
                            t = [t[0], t[2], t[1]]
                        tris.append(t)
    V = np.asarray(tris, float).reshape(-1, 3)
    T = np.arange(len(V)).reshape(-1, 3)
    V, T, _, _ = R._weld(V, T, [], 1e-6)
    return V, T


def volume(V, T):
    P = np.asarray(V, float)[np.asarray(T, int)]
    return float(np.einsum("ij,ij->i", P[:, 0], np.cross(P[:, 1], P[:, 2])).sum() / 6.0)


def main():
    root = tempfile.mkdtemp(prefix="kitunion_")
    print("\nKIT UNION - a drawn solid into a crop, exactly\n")
    try:
        crop = os.path.join(root, "crop.stl"); R.write_stl(crop, *box_mesh((0, 0, 0), (20, 20, 10), n=(8, 8, 4)))
        tool = os.path.join(root, "tool.stl"); R.write_stl(tool, *box_mesh((7, 7, 8), (13, 13, 14), n=(3, 3, 3)))
        say = lambda *a: None

        print("[1] UNION: the crop grows by exactly the solid's part outside it")
        out = os.path.join(root, "u1.stl")
        rep = KU.union(crop, [tool], out, say=say)
        check("closed, no edge beyond the crop's own", rep["bad_edges"] == 0 and rep["wound_against_edges"] == 0, rep)
        check("volume +144.0 mm3 (the 6 x 6 x 4 outside the crop)", abs(rep["added_mm3"] - 144.0) < 0.05, rep["added_mm3"])
        V, T = KU.load(out)
        check("...and the written file reads back with that volume", abs(volume(V, T) - (4000 + 144.0)) < 0.05, volume(V, T))

        print("\n[2] CUT: the crop loses exactly the tool's part inside it")
        out2 = os.path.join(root, "c1.stl")
        rep2 = KU.union(crop, [tool], out2, say=say, cut=True)
        check("closed", rep2["bad_edges"] == 0 and rep2["wound_against_edges"] == 0, rep2)
        check("volume -72.0 mm3 (the 6 x 6 x 2 inside the crop)", abs(rep2["added_mm3"] + 72.0) < 0.05, rep2["added_mm3"])

        print("\n[3] A MIS-WOUND SOLID IS RE-WOUND, and the log says so (the P3 loss)")
        bad = os.path.join(root, "tool_inward.stl"); R.write_stl(bad, *box_mesh((7, 7, 8), (13, 13, 14), n=(3, 3, 3), inward=True))
        lines = []
        rep3 = KU.union(crop, [bad], os.path.join(root, "u3.stl"), say=lambda *a: lines.append(" ".join(str(x) for x in a)))
        check("an inward-wound solid still unions to +144.0 mm3", abs(rep3["added_mm3"] - 144.0) < 0.05, rep3["added_mm3"])
        check("...and the log shouts NOT WOUND OUTWARD", any("NOT WOUND OUTWARD" in l for l in lines), lines[:6])
        Vm, Tm = box_mesh((7, 7, 8), (13, 13, 14), n=(3, 3, 3))
        nrm = np.cross(Vm[Tm[:, 1]] - Vm[Tm[:, 0]], Vm[Tm[:, 2]] - Vm[Tm[:, 0]])
        flip = np.abs(nrm[:, 2]) > 1e-9
        Tm2 = Tm.copy(); Tm2[flip] = Tm2[flip][:, ::-1]
        mixed = os.path.join(root, "tool_mixed.stl"); R.write_stl(mixed, Vm, Tm2)
        lines = []
        rep3b = KU.union(crop, [mixed], os.path.join(root, "u3b.stl"), say=lambda *a: lines.append(" ".join(str(x) for x in a)))
        check("a solid with its caps wound against its sides (closed, positive volume about the origin) is re-wound and unions to +144.0",
              abs(rep3b["added_mm3"] - 144.0) < 0.05 and rep3b["wound_against_edges"] == 0, (rep3b["added_mm3"], rep3b["wound_against_edges"]))

        print("\n[4] REFUSALS: an open solid; a solid that never reaches the surface")
        Vo, To = box_mesh((7, 7, 8), (13, 13, 14), n=(3, 3, 3))
        opn = os.path.join(root, "tool_open.stl"); R.write_stl(opn, Vo, To[:-1])
        try:
            KU.union(crop, [opn], os.path.join(root, "u4.stl"), say=say)
            check("an open solid is REFUSED", False, "it was not")
        except RuntimeError as e:
            check("an open solid is REFUSED", "not closed" in str(e), str(e))
        inside = os.path.join(root, "tool_inside.stl"); R.write_stl(inside, *box_mesh((7, 7, 2), (13, 13, 6), n=(2, 2, 2)))
        try:
            r4 = KU.union(crop, [inside], os.path.join(root, "u4b.stl"), say=say)
            check("a solid wholly inside the crop is refused, or adds nothing", abs(r4["added_mm3"]) < 0.05, r4["added_mm3"])
        except RuntimeError as e:
            check("a solid wholly inside the crop is refused, or adds nothing", True, str(e))

        print("\n[5] TWO SOLIDS IN ONE CALL")
        tool2 = os.path.join(root, "tool2.stl"); R.write_stl(tool2, *box_mesh((1, 1, 8), (4, 4, 13), n=(2, 2, 2)))
        rep5 = KU.union(crop, [tool, tool2], os.path.join(root, "u5.stl"), say=say)
        check("+144 + 27 mm3 (3 x 3 x 3 of the second stands proud)", abs(rep5["added_mm3"] - 171.0) < 0.05, rep5["added_mm3"])
        check("...and both passes are in the report", len(rep5["passes"]) == 2, len(rep5["passes"]))

        print("\n[6] THE CLI: float32 round trip, the .union.json with md5s, --cut --baseline and the ORIGINAL-material figure")
        proj = os.path.join(root, "proj"); os.makedirs(os.path.join(proj, "claude_code", "jobs", "U1"), exist_ok=True)
        env = dict(os.environ); env["KIT_PROJECT"] = proj; env["KIT_NO_INBOX"] = "1"; env["PYTHONUTF8"] = "1"
        kit = os.path.join(HERE, "kit.py")
        flags = {"creationflags": 0x08000000} if os.name == "nt" else {}
        o6 = os.path.join(proj, "claude_code", "jobs", "U1", "u6.stl")
        p = subprocess.run([sys.executable, kit, "union", crop, "--solid", tool, "--out", o6], capture_output=True, text=True,
                           env=env, cwd=os.path.join(proj, "claude_code"), **flags)
        outp = (p.stdout or "") + (p.stderr or "")
        check("kit union runs (rc 0)", p.returncode == 0, outp[-600:])
        j = json.load(open(o6[:-4] + ".union.json", encoding="utf-8")) if os.path.isfile(o6[:-4] + ".union.json") else {}
        check("...writes <out>.union.json with the md5 of the crop, the solid and the output",
              j.get("md5", {}).get("crop") and j["md5"].get("solids") and j["md5"].get("out"), str(j.get("md5"))[:200])
        check("...and its volume line", abs(j.get("added_mm3", 0) - 144.0) < 0.05, j.get("added_mm3"))
        # ORIGINAL
        o7 = os.path.join(proj, "claude_code", "jobs", "U1", "c7.stl")
        p = subprocess.run([sys.executable, kit, "union", crop, "--solid", tool, "--out", o7, "--cut", "--baseline", crop],
                           capture_output=True, text=True, env=env, cwd=os.path.join(proj, "claude_code"), **flags)
        outp = (p.stdout or "") + (p.stderr or "")
        check("--cut --baseline runs (rc 0)", p.returncode == 0, outp[-600:])
        check("...prints the change to the ORIGINAL surface (-72.00) and WARNS that the cut takes original material",
              "ORIGINAL" in outp and "-72.00" in outp and "OF THE ORIGINAL PART" in outp, outp[-700:])
        check("...and writes <out>.baseline.stl", os.path.isfile(o7[:-4] + ".baseline.stl"), o7)
        crop2 = os.path.join(root, "crop2.stl"); shutil.copyfile(out, crop2)
        trim = os.path.join(root, "trim.stl"); R.write_stl(trim, *box_mesh((6, 6, 13), (14, 14, 16), n=(2, 2, 2)))
        o8 = os.path.join(proj, "claude_code", "jobs", "U1", "c8.stl")
        p = subprocess.run([sys.executable, kit, "union", crop2, "--solid", trim, "--out", o8, "--cut", "--baseline", crop],
                           capture_output=True, text=True, env=env, cwd=os.path.join(proj, "claude_code"), **flags)
        outp = (p.stdout or "") + (p.stderr or "")
        j8 = json.load(open(o8[:-4] + ".union.json", encoding="utf-8")) if os.path.isfile(o8[:-4] + ".union.json") else {}
        check("a cut that trims only ADDED material reads -36 on the crop and ~0 on the baseline, with no warning",
              p.returncode == 0 and abs(j8.get("added_mm3", 0) + 36.0) < 0.05 and abs(j8.get("baseline_change_mm3") or 0) < 0.05
              and "OF THE ORIGINAL PART" not in outp, (p.returncode, j8.get("added_mm3"), j8.get("baseline_change_mm3"), outp[-400:]))
    finally:
        shutil.rmtree(root, ignore_errors=True)
    if FAILED:
        print("\n%d FAILED:" % len(FAILED))
        for f in FAILED:
            print("  - %s" % f)
        sys.exit(1)
    print("\nall cases pass. kit union's volume, winding, refusals, md5 record and --baseline hold on synthetic solids;\n"
          "NOT COVERED: a solid grazing a rough voxel surface (the rail cases in the kit's development record are the record of that).")


if __name__ == "__main__":
    main()

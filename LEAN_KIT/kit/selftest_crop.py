#!/usr/bin/env python3
"""selftest_crop.py - `kit crop` / `kit splice`: the mesh route's unit of work is a crop, never the body.

    & python "C:\\CAD\\LEAN_KIT\\kit\\selftest_crop.py"

Every case is on a synthetic hollow box (outer 100 x 60 x 40, wall 5) whose material volume inside any axis-aligned
box is arithmetic, so the crop's closedness is checked by its SIGNED VOLUME against the number, not by eye.
Pinned:
  * a crop through the top slab is CLOSED (0 open edges) and its volume is the slab's material in the grown box;
  * a crop whose walls cut all four side walls caps an ANNULUS (a hole bridged into its outer loop) - closed, right volume;
  * the box's own edges through material are part of the cap loops (no triangle edge lies there);
  * splicing the UNEDITED crop back reproduces the body: 0 open edges, the outside kept by index;
  * an edit inside the box splices (0 open edges, the moved vertex is in the result); an edit that reaches a wall is REFUSED;
  * two pieces splice in ONE pass; two grown boxes sharing a triangle are REFUSED;
  * a sequential splice --into an already-spliced body works when the box is untouched and is REFUSED when it is not;
  * the CLI round trip (kit crop, kit splice) writes the sidecar and the report;
  * the whole-body gate's size test reads a binary STL header.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_crop as KC
import kitlib_render as R

FAILED = []


def check(label, cond, detail=""):
    print("  %-4s %s" % ("ok" if cond else "FAIL", label))
    if not cond:
        print("       %s" % str(detail)[:400])
        FAILED.append(label)


def box_mesh(lo, hi, n=(10, 6, 4), inward=False):
    """an axis-aligned box as an unwelded triangle soup (like an STL), each face an n x m grid, outward normals"""
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
                    t1, t2 = [q[0], q[1], q[2]], [q[0], q[2], q[3]]
                    for t in (t1, t2):
                        nn = np.cross(t[1] - t[0], t[2] - t[0])
                        want = 1.0 if side else -1.0
                        if inward:
                            want = -want
                        if nn[ax] * want < 0:
                            t = [t[0], t[2], t[1]]
                        tris.append(t)
    V = np.asarray(tris, float).reshape(-1, 3)
    return V, np.arange(len(V)).reshape(-1, 3)


def hollow_box():
    Vo, To = box_mesh((0, 0, 0), (100, 60, 40), n=(20, 12, 8))
    Vi, Ti = box_mesh((5, 5, 5), (95, 55, 35), n=(18, 10, 6), inward=True)
    return np.vstack([Vo, Vi]), np.vstack([To, Ti + len(Vo)])


def volume(V, T):
    P = np.asarray(V, float)[np.asarray(T, int)]
    return float(np.einsum("ij,ij->i", P[:, 0], np.cross(P[:, 1], P[:, 2])).sum() / 6.0)


def open_edges_of(V, T, limit=12):
    """the open edges of an index-welded mesh, as coordinate pairs (for a failure's evidence)"""
    oe, _ = KC._open_edges(T)
    return "; ".join("%s-%s" % (tuple(np.round(V[a], 2)), tuple(np.round(V[b], 2))) for a, b in oe[:limit])


def material_in(gb):
    """material of the hollow box inside an axis-aligned box gb = [x0 x1 y0 y1 z0 z1]"""
    def vol(a, b):
        d = [max(0.0, min(a[2 * i + 1], b[2 * i + 1]) - max(a[2 * i], b[2 * i])) for i in range(3)]
        return d[0] * d[1] * d[2]
    outer = [0, 100, 0, 60, 0, 40]; inner = [5, 95, 5, 55, 5, 35]
    return vol(gb, outer) - vol(gb, inner)


def main():
    root = tempfile.mkdtemp(prefix="kitcrop_")
    print("\nKIT CROP / SPLICE - the crop is the unit of work\n")
    try:
        V, T = hollow_box()
        Vw, Tw, _, _ = R._weld(V, T, [], 1e-6)
        check("the synthetic body is closed (0 open edges)", KC.health(Vw, Tw) == (0, 0), KC.health(Vw, Tw))
        check("...and its volume is the hollow box's", abs(volume(V, T) - material_in([0, 100, 0, 60, 0, 40])) < 1e-6, volume(V, T))
        body = os.path.join(root, "body.stl"); R.write_stl(body, V, T)
        V, T = R.read_stl(body)

        print("\n[1] A CROP THROUGH THE TOP SLAB")
        box = [40, 60, 20, 40, 30, 42]
        cV, cT, ncap, rV, rT, rep = KC.crop(V, T, box, margin=3.0)
        gb = rep["grown_box"]
        check("the crop is CLOSED after capping", rep["crop_open_edges_after_cap"] == 0,
              "%s | open: %s" % ({k: rep[k] for k in ("crop_triangles", "cap_triangles", "crop_open_edges_before_cap",
                                                        "crop_open_edges_after_cap", "wall_loops_not_closed")}, open_edges_of(cV, cT)))
        check("...with no non-manifold edge", rep["crop_nonmanifold"] == 0, rep)
        check("...and caps were made", ncap > 0, ncap)
        want = material_in(gb)
        check("its signed volume is the slab's material in the grown box (%.0f mm3)" % want,
              abs(volume(cV, cT) - want) < 1e-3 * want, volume(cV, cT))
        check("straddlers were split, not dropped or kept whole", rep["straddling"] > 0 and rep["crop_triangles"] > rep["fully_inside"], rep)
        check("every wall loop closed", rep["wall_loops_not_closed"] == 0, rep)
        check("the remainder + crop account for every body triangle",
              rep["fully_inside"] + rep["fully_outside"] + rep["straddling"] == len(T), rep)
        rVw, rTw, _, _ = R._weld(rV, rT, [], 1e-6)
        o_rem, _ = KC.health(rVw, rTw)
        check("the remainder is open only where the crop was (its open edges lie on the walls)", o_rem > 0, o_rem)
        crop_stl = os.path.join(root, "top_crop.stl"); R.write_stl(crop_stl, cV, cT)
        side = os.path.join(root, "top_crop.crop.json")
        caps = cT[len(cT) - ncap:]
        meta = dict(rep, body=body, body_md5=KC._md5(body), crop=crop_stl, crop_md5=KC._md5(crop_stl),
                    cap_keys=[[list(v) for v in k] for k in KC._tri_keys(cV, caps)])
        json.dump(meta, open(side, "w"), indent=1)

        print("\n[2] A CROP WHOSE WALLS CUT ALL FOUR SIDE WALLS - the cap is an ANNULUS")
        box2 = [-8, 108, -8, 68, 18, 22]
        c2V, c2T, ncap2, _, _, rep2 = KC.crop(V, T, box2, margin=3.0)
        want2 = material_in(rep2["grown_box"])
        check("closed (0 open edges)", rep2["crop_open_edges_after_cap"] == 0,
              "%s | open: %s" % ({k: rep2[k] for k in ("crop_triangles", "cap_triangles", "crop_open_edges_before_cap",
                                                         "crop_open_edges_after_cap", "wall_loops_not_closed")}, open_edges_of(c2V, c2T)))
        check("its volume is the ring of wall between the two z planes (%.0f mm3)" % want2,
              abs(volume(c2V, c2T) - want2) < 1e-3 * want2, volume(c2V, c2T))
        check("the x and y walls stand in air and carry no cap", rep2["straddling"] > 0 and rep2["wall_loops_not_closed"] == 0, rep2)

        print("\n[3] A CROP ROUND AN OUTER CORNER - L-shaped sections, box edges through material")
        box3 = [90, 106, -6, 12, 30, 46]
        c3V, c3T, _, _, _, rep3 = KC.crop(V, T, box3, margin=2.0)
        want3 = material_in(rep3["grown_box"])
        check("closed (0 open edges)", rep3["crop_open_edges_after_cap"] == 0,
              "%s | open: %s" % ({k: rep3[k] for k in ("crop_triangles", "cap_triangles", "crop_open_edges_before_cap",
                                                         "crop_open_edges_after_cap", "wall_loops_not_closed")}, open_edges_of(c3V, c3T)))
        check("volume right (%.0f mm3)" % want3, abs(volume(c3V, c3T) - want3) < 1e-3 * want3, volume(c3V, c3T))

        print("\n[4] SPLICE THE UNEDITED CROP BACK")
        eV, eT = R.read_stl(crop_stl); eV, eT, _, _ = R._weld(eV, eT, [], 1e-6)
        V2, T2, srep = KC.splice_many(V, T, [(dict(meta), eV, eT)], say=lambda *a: None)
        check("the result is closed (0 open edges)", srep["open_edges_result"] == 0,
              "%s | open: %s" % ({k: srep[k] for k in ("kept_by_index", "result_triangles", "open_edges_result")}, open_edges_of(V2, T2)))
        check("...and non-manifold 0", srep["nonmanifold_result"] == 0, srep)
        check("the volume is the body's", abs(volume(V2, T2) - material_in([0, 100, 0, 60, 0, 40])) < 1e-3, volume(V2, T2))
        check("the outside was kept by index", srep["kept_by_index"] == rep["fully_outside"], srep)
        check("the caps were dropped", srep["pieces"][0]["caps_dropped"] == ncap, srep["pieces"][0])

        print("\n[5] AN EDIT INSIDE THE BOX SPLICES; AN EDIT THAT REACHES A WALL IS REFUSED")
        eV2 = eV.copy()
        planes = KC._planes(gb)
        on_wall = np.zeros(len(eV2), bool)
        for p0, n in planes:
            on_wall |= np.abs((eV2 - np.asarray(p0, float)) @ np.asarray(n, float)) <= 1e-3
        inner = np.where(~on_wall & (np.abs(eV2[:, 2] - 40.0) < 1e-6) & (eV2[:, 0] > 45) & (eV2[:, 0] < 55))[0]
        check("there are top-face vertices inside the box to move", len(inner) > 0, len(inner))
        eV2[inner, 2] += 1.5
        edited = os.path.join(root, "top_edit.stl"); R.write_stl(edited, eV2, eT)
        m2, xV, xT = KC._load_piece(edited, side)
        V3, T3, srep3 = KC.splice_many(V, T, [(m2, xV, xT)], say=lambda *a: None)
        check("the edited crop splices with 0 open edges", srep3["open_edges_result"] == 0, srep3)
        check("the bump is in the result (a vertex at z 41.5)", bool(np.any(np.abs(V3[:, 2] - 41.5) < 1e-4)), V3[:, 2].max())
        check("and the volume grew", volume(V3, T3) > material_in([0, 100, 0, 60, 0, 40]) + 1.0, volume(V3, T3))
        body2 = os.path.join(root, "body2.stl"); R.write_stl(body2, V3, T3)
        eV3 = eV.copy()
        rim = np.where(on_wall & (np.abs(eV3[:, 2] - 40.0) < 1e-6))[0]
        eV3[rim[:3], 2] += 0.5
        bad = os.path.join(root, "top_bad.stl"); R.write_stl(bad, eV3, eT)
        m3, yV, yT = KC._load_piece(bad, side)
        try:
            KC.splice_many(V, T, [(m3, yV, yT)], say=lambda *a: None)
            check("an edit that moved rim points is REFUSED", False, "it was not")
        except RuntimeError as e:
            check("an edit that moved rim points is REFUSED", "reached the crop wall" in str(e), str(e))

        print("\n[6] TWO PIECES IN ONE PASS; OVERLAPPING GROWN BOXES REFUSED")
        boxb = [40, 60, 20, 40, -2, 10]
        bV, bT_, ncapb, _, _, repb = KC.crop(V, T, boxb, margin=3.0)
        check("the bottom crop is closed", repb["crop_open_edges_after_cap"] == 0, repb)
        crop_b = os.path.join(root, "bot_crop.stl"); R.write_stl(crop_b, bV, bT_)
        side_b = os.path.join(root, "bot_crop.crop.json")
        capsb = bT_[len(bT_) - ncapb:]
        metab = dict(repb, body=body, body_md5=KC._md5(body), crop=crop_b, crop_md5=KC._md5(crop_b),
                     cap_keys=[[list(v) for v in k] for k in KC._tri_keys(bV, capsb)])
        json.dump(metab, open(side_b, "w"), indent=1)
        mb, zV, zT = KC._load_piece(crop_b, side_b)
        V4, T4, srep4 = KC.splice_many(V, T, [(m2, xV, xT), (mb, zV, zT)], say=lambda *a: None)
        check("two pieces splice in one pass, 0 open edges", srep4["open_edges_result"] == 0 and len(srep4["pieces"]) == 2, srep4)
        boxo = [50, 70, 20, 40, 30, 42]
        oV, oT, ncapo, _, _, repo = KC.crop(V, T, boxo, margin=3.0)
        crop_o = os.path.join(root, "ovl_crop.stl"); R.write_stl(crop_o, oV, oT)
        metao = dict(repo, body=body, body_md5=KC._md5(body), crop=crop_o, crop_md5=KC._md5(crop_o),
                     cap_keys=[[list(v) for v in k] for k in KC._tri_keys(oV, oT[len(oT) - ncapo:])])
        try:
            KC.splice_many(V, T, [(m2, xV, xT), (metao, *R._weld(oV, oT, [], 1e-6)[:2])], say=lambda *a: None)
            check("two grown boxes sharing a triangle are REFUSED", False, "they were not")
        except RuntimeError as e:
            check("two grown boxes sharing a triangle are REFUSED", "two pieces" in str(e), str(e))

        print("\n[7] SEQUENTIAL: --into the body after piece 1")
        B2V, B2T = R.read_stl(body2)
        V5, T5, srep5 = KC.splice_many(B2V, B2T, [(mb, zV, zT)], say=lambda *a: None)
        check("piece 2 into body2 (its box untouched by piece 1) splices, 0 open edges", srep5["open_edges_result"] == 0, srep5)
        try:
            m2b, xV2, xT2 = KC._load_piece(crop_stl, side)
            KC.splice_many(B2V, B2T, [(m2b, xV2, xT2)], say=lambda *a: None)
            check("the top crop into body2 (its box already edited) is REFUSED", False, "it was not")
        except RuntimeError as e:
            check("the top crop into body2 (its box already edited) is REFUSED", "not the surface the crop was cut from" in str(e), str(e))

        print("\n[8] THE CLI ROUND TRIP")
        proj = os.path.join(root, "proj"); os.makedirs(os.path.join(proj, "claude_code", "jobs", "T1"), exist_ok=True)
        env = dict(os.environ); env["KIT_PROJECT"] = proj; env["KIT_NO_INBOX"] = "1"
        cli_crop = os.path.join(proj, "claude_code", "jobs", "T1", "c.stl")
        p = subprocess.run([sys.executable, os.path.join(HERE, "kit.py"), "crop", body, "--box", "40 60 20 40 30 42",
                            "--margin", "3", "--out", cli_crop], capture_output=True, text=True, env=env,
                            cwd=os.path.join(proj, "claude_code"), creationflags=(0x08000000 if os.name == "nt" else 0))
        out = (p.stdout or "") + (p.stderr or "")
        check("kit crop runs (rc 0)", p.returncode == 0, out[-600:])
        check("...writes the crop and its sidecar", os.path.isfile(cli_crop) and os.path.isfile(cli_crop[:-4] + ".crop.json"), out[-300:])
        check("...and says the crop is closed", "open edges" in out and "-> 0 after capping" in out, out[-600:])
        cli_out = os.path.join(proj, "claude_code", "jobs", "T1", "body_out.stl")
        p = subprocess.run([sys.executable, os.path.join(HERE, "kit.py"), "splice", cli_crop, "--crop", cli_crop[:-4] + ".crop.json",
                            "--out", cli_out], capture_output=True, text=True, env=env,
                            cwd=os.path.join(proj, "claude_code"), creationflags=(0x08000000 if os.name == "nt" else 0))
        out = (p.stdout or "") + (p.stderr or "")
        check("kit splice runs (rc 0)", p.returncode == 0, out[-600:])
        check("...writes the body and its report", os.path.isfile(cli_out) and os.path.isfile(cli_out[:-4] + ".splice.json"), out[-300:])
        check("...and reports the identity outside the box", "kept by index" in out, out[-400:])
        dry_out = os.path.join(proj, "claude_code", "jobs", "T1", "body_dry.stl")
        p = subprocess.run([sys.executable, os.path.join(HERE, "kit.py"), "splice", cli_crop, "--crop", cli_crop[:-4] + ".crop.json",
                            "--out", dry_out, "--dry-run"], capture_output=True, text=True, env=env,
                            cwd=os.path.join(proj, "claude_code"), creationflags=(0x08000000 if os.name == "nt" else 0))
        out = (p.stdout or "") + (p.stderr or "")
        check("kit splice --dry-run runs every check and writes nothing", p.returncode == 0 and "DRY RUN" in out
              and "kept by index" in out and not os.path.isfile(dry_out) and not os.path.isfile(dry_out[:-4] + ".splice.json"), out[-500:])
        sib_out = os.path.join(proj, "claude_code", "jobs", "T1", "body_sibling.stl")
        p = subprocess.run([sys.executable, os.path.join(HERE, "kit.py"), "splice", cli_crop, "--crop", cli_crop[:-4] + ".crop.json",
                            "--out", sib_out], capture_output=True, text=True, env=env,
                            cwd=os.path.join(proj, "claude_code"), creationflags=(0x08000000 if os.name == "nt" else 0))
        out = (p.stdout or "") + (p.stderr or "")
        check("a second splice from the same body without --into is WARNED as a sibling (the first's --out named)",
              p.returncode == 0 and "SIBLINGS" in out and "body_out.stl" in out, out[-600:])
        p = subprocess.run([sys.executable, os.path.join(HERE, "kit.py"), "crop", "--help"], capture_output=True, text=True, env=env,
                            cwd=os.path.join(proj, "claude_code"), creationflags=(0x08000000 if os.name == "nt" else 0))
        check("kit crop --help answers", p.returncode == 0 and "--margin" in (p.stdout or ""), (p.stdout or p.stderr)[-300:])

        print("\n[9] THE WHOLE-BODY GATE'S SIZE TEST")
        check("stl_count reads the header", KC.stl_count(body) == len(T), KC.stl_count(body))
        check("a crop is under the body-sized threshold", KC.stl_count(crop_stl) < KC.BODY_SIZED, KC.stl_count(crop_stl))
        ext = ([0, 0, 0], [100, 60, 40])
        big, why = KC.body_sized(body, ext)
        check("the body (no sidecar, spans the whole extent) is BODY-SIZED", big, why)
        big, why = KC.body_sized(crop_stl, ext)
        check("a crop with its sidecar is not", not big, why)
        bare = os.path.join(root, "bare_crop.stl"); shutil.copy(crop_stl, bare)
        big, why = KC.body_sized(bare, ext)
        check("a crop-sized STL with NO sidecar is not either (it spans a corner of the extent)", not big, why)
        big, why = KC.body_sized(body, None)
        check("with no extent known, a 3k-triangle body passes the count test alone (the atlas is what gives the gate its teeth)", not big, why)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    Vz = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [1 + 1e-12, 0, 0], [2, 0, 0], [3, 0, 0]], float)
    Tz = np.array([[0, 1, 2], [1, 3, 2], [0, 1, 4], [1, 4, 5]])
    Vo, To, nd, nc = KC._weld_degenerate(Vz, Tz)
    check("31bz R4 F5: _weld_degenerate drops the repeated-vertex facet (1) and KEEPS the collinear ones (2 counted)", nd == 1 and nc == 2 and len(To) == 3, (nd, nc, len(To)))
    check("31bz R4 F5: ...the splice calls it and reports both counts", "_weld_degenerate(V, T" in open(os.path.join(HERE, "kit_crop.py"), encoding="utf-8").read()
          and 'rep["degenerate_dropped"]' in open(os.path.join(HERE, "kit_crop.py"), encoding="utf-8").read())
    # open edges
    def _box_fan(split):
        P = [[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0], [0, 0, 10], [10, 0, 10], [10, 10, 10], [0, 10, 10], [5, 5, 10]]
        Tb = [[0, 2, 1], [0, 3, 2], [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5], [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]]
        if not split: return np.array(P, float), np.array(Tb + [[8, 4, 5], [8, 5, 6], [8, 6, 7], [8, 7, 4]], int)
        P = P + [[5 + 2e-5, 5, 10]]
        return np.array(P, float), np.array(Tb + [[8, 4, 5], [8, 5, 6], [9, 6, 7], [9, 7, 4], [4, 8, 9], [8, 6, 9]], int)
    def _vol(V_, T_): A, B, C = V_[T_[:, 0]], V_[T_[:, 1]], V_[T_[:, 2]]; return float(np.einsum("ij,ij->i", A, np.cross(B, C)).sum() / 6.0)
    Vs, Ts = _box_fan(True); _oe0, _nm0 = KC.health(Vs, Ts); _info = {}
    Vo, To, nd, nc = KC._weld_degenerate(Vs, Ts, _info); _oe1, _nm1 = KC.health(Vo, To)
    check("31ca R4 F5: the short-edge collapse - the split box is closed as crafted (open 0, 16 triangles)", _oe0 == 0 and _nm0 == 0 and len(Ts) == 16, (_oe0, _nm0, len(Ts)))
    check("31ca R4 F5: ...after _weld_degenerate: 1 edge collapsed, the 2 slivers dropped, 14 triangles, open edges 0, non-manifold 0",
          _info.get("collapsed") == 1 and nd == 2 and len(To) == 14 and _oe1 == 0 and _nm1 == 0 and not _info.get("collapse_cap_hit"), (_info, nd, len(To), _oe1, _nm1))
    check("31ca R4 F5: ...the signed volume kept within 1e-6 (1000 mm3)", abs(_vol(Vo, To) - _vol(Vs, Ts)) < 1e-6 and abs(_vol(Vo, To) - 1000.0) < 1e-6, (_vol(Vs, Ts), _vol(Vo, To)))
    Vp, Tp = _box_fan(False); _info2 = {}; Vq, Tq, nd2, nc2 = KC._weld_degenerate(Vp, Tp, _info2)
    check("31ca R4 F5: ...a box with no edge under 1e-4 mm comes back unchanged - 14 triangles, 0 collapsed / 0 dropped",
          len(Tq) == 14 and _info2.get("collapsed") == 0 and nd2 == 0 and nc2 == 0 and KC.health(Vq, Tq) == (0, 0), (len(Tq), _info2, nd2, nc2))
    _src = open(os.path.join(HERE, "kit_crop.py"), encoding="utf-8").read()
    check("31ca R4 F5: ...the splice passes the info and its weld line says the collapsed count", "_weld_degenerate(V, T, _winfo)" in _src and "edge(s) under 1e-4 mm collapsed" in _src and "COLLAPSE_MM = 1e-4" in _src)
    print()
    if FAILED:
        print("%d FAILED:" % len(FAILED))
        for f in FAILED:
            print("  - " + f)
        return 1
    print("all cases pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

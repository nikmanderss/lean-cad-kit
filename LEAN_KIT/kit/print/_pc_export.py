import os, sys, json, time
import numpy as np
import Part, Mesh, MeshPart

IN = os.environ["PC_IN"]; OUT = os.environ["PC_OUT"]; DEV = float(os.environ.get("PC_DEV", "0.05"))
os.makedirs(OUT, exist_ok=True)
t0 = time.time()
out = {"input": IN, "kind": "brep" if IN.lower().endswith((".brep", ".brp")) else "mesh", "dev": DEV}


def say(*a):
    print(*a, flush=True)


def topo(mesh):
    """the mesh as it stands: points, facets, volume, extents, shells with the small ones listed, open and non-manifold
    edges counted on the index topology (exact, after duplicate points are merged)."""
    d = {"points": mesh.CountPoints, "facets": mesh.CountFacets, "volume": round(float(mesh.Volume), 1),
         "is_solid": bool(mesh.isSolid()), "has_nonmanifold": bool(mesh.hasNonManifolds())}
    b = mesh.BoundBox
    d["bbox"] = [round(v, 3) for v in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)]
    d["extent_mm"] = [round(b.XLength, 2), round(b.YLength, 2), round(b.ZLength, 2)]
    try:
        comps = mesh.getSeparateComponents()
        d["shells"] = len(comps)
        small = []
        for c in comps:
            if c.CountFacets < 2000:
                cb = c.BoundBox
                small.append({"facets": c.CountFacets, "volume": round(float(c.Volume), 4),
                              "bbox": [round(v, 2) for v in (cb.XMin, cb.XMax, cb.YMin, cb.YMax, cb.ZMin, cb.ZMax)]})
        d["small_shells"] = sorted(small, key=lambda s: -s["facets"])[:40]
        d["shell_facets"] = sorted([c.CountFacets for c in comps], reverse=True)[:8]
    except Exception as e:
        d["shells"] = None; d["shells_error"] = str(e)
    tp = mesh.Topology
    T = np.asarray(tp[1], np.int64)
    E = np.sort(np.concatenate([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], 0), 1)
    _, c = np.unique(E, axis=0, return_counts=True)
    d["open_edges"] = int((c == 1).sum()); d["nonmanifold_edges"] = int((c > 2).sum())
    P = np.asarray(tp[0], float)[T]
    ar = 0.5 * np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1)
    d["surface_mm2"] = round(float(ar.sum()), 1); d["degenerate_facets"] = int((ar < 1e-8).sum())
    return d


def bores(sh, spec):
    """every bore of the spec: the vertical cylinder faces at its (x, y), their radius and z extent, against dia/depth."""
    res = []
    cyl = [(f, f.Surface) for f in sh.Faces if type(f.Surface).__name__ == "Cylinder"]
    for b in spec.get("bores", []):
        got = []
        for f, s in cyl:
            if abs(abs(s.Axis.z) - 1) > 1e-3 or abs(s.Center.x - b["x"]) > 0.15 or abs(s.Center.y - b["y"]) > 0.15:
                continue
            bb = f.BoundBox
            got.append((s.Radius, bb.ZMin, bb.ZMax, f.Area))
        if not got:
            res.append(dict(b, found=False)); continue
        k = max(range(len(got)), key=lambda i: got[i][3])
        r, z0, z1, a = got[k]
        d = {"dia": round(2 * r, 3), "depth": round(z1 - z0, 3), "z0": round(z0, 3), "z1": round(z1, 3),
             "rings": [{"dia": round(2 * g[0], 3), "z": [round(g[1], 2), round(g[2], 2)]} for i, g in enumerate(got) if i != k and g[3] > 0.01]}
        ok = abs(2 * r - b["dia"]) <= spec.get("tol_dia", 0.05) and abs((z1 - z0) - b["depth"]) <= spec.get("tol_depth", 0.2)
        res.append(dict(b, found=True, has=d, ok=bool(ok)))
    return res


def _ray_hits(T3, o, d):
    """Moller-Trumbore over every triangle at once; the sorted positive distances along the ray."""
    e1 = T3[:, 1] - T3[:, 0]; e2 = T3[:, 2] - T3[:, 0]
    p = np.cross(d, e2); det = (e1 * p).sum(1)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    s = o - T3[:, 0]
    u = (s * p).sum(1) * inv
    q = np.cross(s, e1)
    v = (q * d).sum(1) * inv
    t = (e2 * q).sum(1) * inv
    m = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-9)
    return np.sort(t[m])


def bores_mesh(mesh, spec):
    """every bore of the spec measured ON THE MESH (2026-09-25; R33 notes 19 / lessons K12: `--bores` measured only a
    B-rep's cylinder faces and on the print STL printed nothing and warned of nothing - PRINT_READINESS step 4
    relied on it; ported from a project's own bore check, which found a bore plugged by a drawn slab). A bore is a blind hole on a vertical axis, open at the part's bottom (spec "from":
    "below", the default) or top ("above"). Bottom = the first material crossing along the axis from outside; the
    diameter = twice the mean distance of 12 radial rays to the wall at 1.0 / 3.5 / 6.0 mm inside; the mouth = the last
    level (0.05 mm steps) at which all rays still meet a wall within dia/2 + 0.6. Mesh tolerance: the spec's + 0.05 on
    the diameter and + 0.1 on the depth (a decimated print file)."""
    tp = mesh.Topology
    P = np.asarray(tp[0], float); T3 = P[np.asarray(tp[1], np.int64)]
    C = T3.mean(1)
    zlo, zhi = float(P[:, 2].min()), float(P[:, 2].max())
    angs = np.linspace(0, 2 * np.pi, 12, endpoint=False)
    res = []
    for b in spec.get("bores", []):
        x, y, dia, depth = b["x"], b["y"], b["dia"], b["depth"]
        frm = (b.get("from") or spec.get("from") or "below").lower()
        sgn = 1.0 if frm == "below" else -1.0
        near = T3[(np.abs(C[:, 0] - x) < max(6.0, dia)) & (np.abs(C[:, 1] - y) < max(6.0, dia))]
        if not len(near):
            res.append(dict(b, found=False, why="no surface within 6 mm of the axis")); continue
        o = np.array([x + 1e-4, y + 1.3e-4, (zlo - 5.0) if sgn > 0 else (zhi + 5.0)])
        up = _ray_hits(near, o, np.array([0.0, 0.0, sgn]))
        if not len(up):
            zs = np.arange(zlo + 0.05, zhi - 0.05 + 1e-9, 0.05) if sgn > 0 else np.arange(zhi - 0.05, zlo + 0.05 - 1e-9, -0.05)
            good = []
            for z in zs:
                ok_ = True
                for a in angs[::2]:
                    h = _ray_hits(near, np.array([x, y, z]), np.array([np.cos(a), np.sin(a), 0.0]))
                    if not len(h) or h[0] > dia / 2 + 0.6:
                        ok_ = False; break
                good.append(ok_)
            good = np.array(good, bool)
            if not good.any():
                res.append(dict(b, found=False, why="no surface on the axis and no bore wall round it")); continue
            runs = []; s_ = None
            for i_, g_ in enumerate(good):
                if g_ and s_ is None: s_ = i_
                if s_ is not None and (not g_ or i_ == len(good) - 1): runs.append((s_, i_ if g_ else i_ - 1)); s_ = None
            i0, i1 = max(runs, key=lambda r_: r_[1] - r_[0]); zm, zb = float(zs[i0]), float(zs[i1])
            rads = {}
            for dz in (1.0, 3.5, 6.0):
                z = zm + sgn * min(dz, max(abs(zb - zm) - 0.05, 0.05)); r = []
                for a in angs:
                    h = _ray_hits(near, np.array([x, y, z]), np.array([np.cos(a), np.sin(a), 0.0])); r.append(h[0] if len(h) else np.nan)
                rads[dz] = np.array(r)
            dmeas = {k: float(2 * np.nanmean(v)) if np.isfinite(v).any() else float("nan") for k, v in rads.items()}
            dep = abs(zb - zm) + 0.05; dmean = float(np.nanmean(list(dmeas.values())))
            ok = (np.isfinite(dmean) and abs(dmean - dia) <= spec.get("tol_dia", 0.05) + 0.05 and abs(dep - depth) <= spec.get("tol_depth", 0.2) + 0.1)
            res.append(dict(b, found=True, ok=bool(ok), has={"dia": round(dmean, 3), "dia_at_1_3.5_6": [round(dmeas[1.0], 3), round(dmeas[3.5], 3), round(dmeas[6.0], 3)],
                                                           "depth": round(dep, 3), "bottom_z": round(zb, 3), "mouth_z": round(zm, 3), "measured_on": "mesh", "through": True})); continue
        zb = o[2] + sgn * up[0]
        rads = {}
        for dz in (1.0, 3.5, 6.0):
            z = zb - sgn * dz
            r = []
            for a in angs:
                h = _ray_hits(near, np.array([x, y, z]), np.array([np.cos(a), np.sin(a), 0.0]))
                r.append(h[0] if len(h) else np.nan)
            rads[dz] = np.array(r)
        zm = zb; z = zb - sgn * 0.05
        while abs(z - zb) < depth + 3.0:
            good_ = True
            for a in angs[::2]:
                h = _ray_hits(near, np.array([x, y, z]), np.array([np.cos(a), np.sin(a), 0.0]))
                if not len(h) or h[0] > dia / 2 + 0.6:
                    good_ = False; break
            if not good_:
                break
            zm = z; z -= sgn * 0.05
        dmeas = {k: float(2 * np.nanmean(v)) if np.isfinite(v).any() else float("nan") for k, v in rads.items()}
        dep = abs(zb - zm)
        dmean = float(np.nanmean(list(dmeas.values())))
        ok = (np.isfinite(dmean) and abs(dmean - dia) <= spec.get("tol_dia", 0.05) + 0.05
              and abs(dep - depth) <= spec.get("tol_depth", 0.2) + 0.1)
        d = {"dia": round(dmean, 3), "dia_at_1_3.5_6": [round(dmeas[1.0], 3), round(dmeas[3.5], 3), round(dmeas[6.0], 3)],
             "depth": round(dep, 3), "bottom_z": round(float(zb), 3), "mouth_z": round(float(zm), 3), "measured_on": "mesh"}
        res.append(dict(b, found=True, has=d, ok=bool(ok)))
    return res


if out["kind"] == "brep":
    sh = Part.Shape(); sh.importBrep(IN)
    ob = sh.optimalBoundingBox()
    A = np.array([f.Area for f in sh.Faces])
    out["brep"] = {"faces": len(sh.Faces), "solids": len(sh.Solids), "shells": len(sh.Shells), "valid": bool(sh.isValid()),
                   "closed": bool(sh.isClosed()) if hasattr(sh, "isClosed") else None,
                   "volume": round(sh.Volume, 1), "surface_mm2": round(float(A.sum()), 1),
                   "extent_mm": [round(ob.XLength, 2), round(ob.YLength, 2), round(ob.ZLength, 2)],
                   "edge_tol_max": round(max(e.Tolerance for e in sh.Edges), 4),
                   "vertex_tol_max": round(max(v.Tolerance for v in sh.Vertexes), 4),
                   "faces_under_mm2": {"0.05": int((A < 0.05).sum()), "0.30": int((A < 0.30).sum()), "1.0": int((A < 1.0).sum()), "5.0": int((A < 5.0).sum())},
                   "area_under_0.30": round(float(A[A < 0.30].sum()), 1)}
    say("brep: %d faces, %d solid(s), valid %s, %.1f mm3, %s mm, edge tol %.3f vertex tol %.3f, %d faces under 0.30 mm2 (%.0f s)"
        % (len(sh.Faces), len(sh.Solids), sh.isValid(), sh.Volume, out["brep"]["extent_mm"], out["brep"]["edge_tol_max"],
           out["brep"]["vertex_tol_max"], out["brep"]["faces_under_mm2"]["0.30"], time.time() - t0))
    m = MeshPart.meshFromShape(Shape=sh, LinearDeflection=DEV, AngularDeflection=0.3, Relative=False)
    m.removeDuplicatedPoints()
    stl = os.path.join(OUT, "tess.stl"); m.write(stl)
    out["mesh"] = topo(m); out["mesh"]["file"] = stl; out["mesh"]["MB"] = round(os.path.getsize(stl) / 1e6, 1)
    say("tessellation at %g mm: %d facets, %.1f MB, open %d, non-manifold %d, shells %d, volume %.1f (%.0f s)"
        % (DEV, m.CountFacets, out["mesh"]["MB"], out["mesh"]["open_edges"], out["mesh"]["nonmanifold_edges"], out["mesh"]["shells"], m.Volume, time.time() - t0))
    if os.environ.get("PC_BORES"):
        spec = json.load(open(os.environ["PC_BORES"], encoding="utf-8"))
        out["bores"] = bores(sh, spec)
        for r in out["bores"]:
            if not r["found"]:
                say("  bore %-14s NOT FOUND at its axis" % r["name"])
            else:
                say("  bore %-14s spec %.2f x %.1f   has %.2f x %.2f   %s" % (r["name"], r["dia"], r["depth"], r["has"]["dia"], r["has"]["depth"],
                                                                            "ok" if r["ok"] else "OFF SPEC" + ("  (spec pending the client)" if r.get("pending_ad") else "")))
    if os.environ.get("PC_STEP") == "1":
        p = os.path.join(OUT, "_roundtrip.step")
        try:
            sh.exportStep(p)
            rd = Part.read(p)
            out["step"] = {"MB": round(os.path.getsize(p) / 1e6, 1), "reimport_solids": len(rd.Solids), "reimport_faces": len(rd.Faces),
                           "reimport_valid": bool(rd.isValid()), "reimport_volume": round(rd.Volume, 1)}
            say("STEP round trip: %.1f MB, re-imports as %d solid(s), %d faces (body has %d), volume %.1f vs %.1f (%.0f s)"
                % (out["step"]["MB"], len(rd.Solids), len(rd.Faces), len(sh.Faces), rd.Volume, sh.Volume, time.time() - t0))
        except Exception as e:
            out["step"] = {"error": str(e)}; say("STEP round trip failed: %s" % e)
        finally:
            try:
                os.remove(p)
            except OSError:
                pass
else:
    m = Mesh.Mesh(IN)
    m.removeDuplicatedPoints()
    out["mesh"] = topo(m); out["mesh"]["file"] = IN; out["mesh"]["MB"] = round(os.path.getsize(IN) / 1e6, 1)
    say("mesh: %d facets, %.1f MB, open %d, non-manifold %d, shells %d, volume %.1f, %s mm (%.0f s)"
        % (m.CountFacets, out["mesh"]["MB"], out["mesh"]["open_edges"], out["mesh"]["nonmanifold_edges"], out["mesh"]["shells"], m.Volume,
           out["mesh"]["extent_mm"], time.time() - t0))
    if os.environ.get("PC_BORES"):
        spec = json.load(open(os.environ["PC_BORES"], encoding="utf-8"))
        _tb = time.time()
        out["bores"] = bores_mesh(m, spec)
        for r in out["bores"]:
            if not r["found"]:
                say("  bore %-14s NOT FOUND (%s)" % (r["name"], r.get("why", "")))
            else:
                say("  bore %-14s spec %.2f x %.1f   has %.2f (%.2f / %.2f / %.2f at 1 / 3.5 / 6 mm) x %.2f   %s"
                    % (r["name"], r["dia"], r["depth"], r["has"]["dia"], *r["has"]["dia_at_1_3.5_6"], r["has"]["depth"],
                       "ok" if r["ok"] else "OFF SPEC" + ("  (spec pending the client)" if r.get("pending_ad") else "")))
        say("  bores on the mesh: %d of %d at spec (%.0f s; mesh tolerance = spec + 0.05 dia / + 0.1 depth)"
            % (sum(1 for r in out["bores"] if r.get("ok")), len(out["bores"]), time.time() - _tb))
json.dump(out, open(os.path.join(OUT, "export.json"), "w", encoding="utf-8"), indent=1)
say("%.0f s" % (time.time() - t0)); say("DONE")

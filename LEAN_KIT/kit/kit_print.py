# -*- coding: utf-8 -*-
"""kit printcheck / kit printfile — is this body ready for a print shop, and the file that is.

WHY THIS EXISTS (the client, 2026-09-24): *"Evaluate the current state of the latest model vs. what I had asked for and compare
that to 3D printing rules / best practice ... consider how a 3D print shop will process the file ... I want a full scope
review of how ready it is."* and, after the review: *"if you have generic checks or a process written for how to review a
part to be ready to print at the end of the review that would be helpful / wanted for future agents."* The review was
done by hand with eight scripts in a job folder; this is those scripts as ONE command any agent runs at the end of a
round, judged against a named shop's rules (`print_rules.json`), with the pictures the verdict rests on.

    kit printcheck <body.brep | mesh.stl> --rules jlc_mjf_pa12 [--out <dir>] [--bores <spec.json>] [--dev 0.05]
                   [--step] [--sample 400000] [--no-sections]

Runs, each as its own process under the kit's cap:
  1. export  (freecadcmd)  the B-rep as the kernel sees it (valid, solids, tolerances, shard census) AND as the STL the
                           shop will see (tessellated at --dev; open edges, non-manifold edges, shells, fragments, size);
                           --bores measures every bore of a spec file - on a B-rep from its cylinder faces, on a MESH by rays
                           (the print STL: bottom by an axis ray, diameter by 12 radial rays at three depths, mouth by
                           stepping down; 2026-09-25 - before that a mesh printed no bore row and no warning);
                           --step exports STEP and re-imports it.
                           THE BORE SPEC (--bores <spec.json>): {"bores": [{"name": "H1", "x": 20.0, "y": 20.0, "dia": 6.0, "depth": 10.0, "from": "below"}],
                           "tol_dia": 0.05, "tol_depth": 0.2} - x / y the axis, dia / depth the drawing's, "from" the open end (below | above); a THROUGH
                           bore's depth is the part's thickness there (on a mesh its wall is measured station by station - 31bz R4 F7).
  2. walls   (freecadcmd)  a ray-cast wall-thickness census of the mesh against the shop's floors, thin places clustered.
  3. sections (python)     filled 2-D sections through every thin cluster of 5 mm² or more: a wall reads as one band, a
                           lamina (an air film under a skin) as two - the census cannot tell them apart, the picture can.
  4. verdict               PRINTCHECK.md + printcheck.json in --out: each rule PASS / WARN / FAIL with the number that
                           decided it and the kit action that clears it. Thin clusters are named by atlas region.

The verdict is a LIST OF BLOCKERS, not a certificate: the shop's own manual review decides last. An agent reads every
section picture before repeating a number from the table (the client: the pictures are the acceptance).
"""
import os, sys, json, time, re

HERE = os.path.dirname(os.path.abspath(__file__))
RULES_FILE = os.path.join(HERE, "print_rules.json")
STEPS_DIR = os.path.join(HERE, "print")


def rules_load(name):
    d = json.load(open(RULES_FILE, encoding="utf-8"))
    if name not in d or name.startswith("_"):
        raise SystemExit("kit printfile / printcheck: no rules named %r in print_rules.json - have: %s" % (name, ", ".join(k for k in d if not k.startswith("_"))))
    return d[name]


def _fits(extent, build):
    """can a box of `extent` be turned to fit the build volume? sorted comparison, a rotation onto the axes."""
    e = sorted(extent, reverse=True); b = sorted(build, reverse=True)
    return all(x <= y for x, y in zip(e, b))


def _region_of(kit, centre):
    """the smallest atlas region whose box holds the point, or None."""
    try:
        regs = kit.G.atlas_regions(kit.ROOT) or {}
    except Exception:
        return None
    best = None
    for name, r in regs.items():
        b = r.get("box")
        if not b or len(b) != 6:
            continue
        if b[0] <= centre[0] <= b[1] and b[2] <= centre[1] <= b[3] and b[4] <= centre[2] <= b[5]:
            vol = (b[1] - b[0]) * (b[3] - b[2]) * (b[5] - b[4])
            if best is None or vol < best[1]:
                best = (name, vol)
    return best[0] if best else None


def _run(kit, script, env, cap, log, needs_fc):
    runner = kit.freecad() if needs_fc else sys.executable
    cmdline = [runner, os.path.join(STEPS_DIR, script)] if needs_fc else [runner, "-W", "ignore", os.path.join(STEPS_DIR, script)]
    rc, out = kit.sh(cmdline, cap, log, env, cwd=os.path.dirname(os.path.abspath(log)))
    rc = kit._judge_output(out, rc, log, "kit printcheck")
    if "DONE" not in out:
        rc = rc or 3
    return rc


def cmd_printcheck(args, kit):
    if not args or args[0].startswith("-"):
        print(__doc__); return 2
    body = os.path.abspath(args[0])
    if not os.path.isfile(body):
        print("kit printcheck: no such file %s" % body); return 2
    rules_name = kit._opt(args, "--rules")
    if not rules_name:
        print("kit printcheck: --rules <name> is required (print_rules.json: %s)"
              % ", ".join(k for k in json.load(open(RULES_FILE, encoding="utf-8")) if not k.startswith("_"))); return 2
    R = rules_load(rules_name)
    stem = os.path.splitext(os.path.basename(body))[0]
    out = os.path.abspath(kit._opt(args, "--out") or os.path.join(kit.ROOT, "claude_code", "jobs", "PRINTCHECK_%s_%s" % (stem, rules_name)))
    os.makedirs(out, exist_ok=True)
    dev = float(kit._opt(args, "--dev") or 0.05)
    env = dict(os.environ)
    env.update({"KIT_HOME": kit.HERE, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1",
                "PC_IN": body, "PC_OUT": out, "PC_DEV": str(dev), "PC_STEP": "1" if "--step" in args else "0",
                "PC_THIN": str(R["thinnest_min_mm"]), "PC_WALL": str(R["auto_check_wall_mm"]),
                "PC_SAMPLE": str(kit._opt(args, "--sample") or 400000)})
    bores = kit._opt(args, "--bores")
    if bores:
        env["PC_BORES"] = os.path.abspath(bores)
    t0 = time.time()
    print("kit printcheck: %s against %s (%s %s, rules read %s)\n  out: %s" % (body, rules_name, R["process"], R["material"], R["read"], out))
    rc = _run(kit, "_pc_export.py", env, 1800, os.path.join(out, "log_export.txt"), True)
    if rc:
        print("kit printcheck: the export step failed (rc %s) - log_export.txt" % rc); return rc
    E = json.load(open(os.path.join(out, "export.json"), encoding="utf-8"))
    mesh = E["mesh"]["file"]
    env["PC_MESH"] = mesh
    rc = _run(kit, "_pc_walls.py", env, 2400, os.path.join(out, "log_walls.txt"), True)
    if rc:
        print("kit printcheck: the wall census failed (rc %s) - log_walls.txt" % rc); return rc
    Wj = json.load(open(os.path.join(out, "walls.json"), encoding="utf-8"))
    sections = []
    if "--no-sections" not in args:
        env["PC_WALLS"] = os.path.join(out, "walls.json")
        rc = _run(kit, "_pc_sections.py", env, 900, os.path.join(out, "log_sections.txt"), False)
        if rc:
            print("kit printcheck: the sections step failed (rc %s) - log_sections.txt; the verdict below is without pictures" % rc)
        else:
            try:
                sections = json.load(open(os.path.join(out, "sections.json"), encoding="utf-8"))
            except (OSError, ValueError):
                sections = []
    rows = []
    M = E["mesh"]
    ext = M["extent_mm"]
    rows.append(("size vs build volume %s mm" % "x".join(str(v) for v in R["build_mm"]),
                 "PASS" if _fits(ext, R["build_mm"]) else "FAIL", "part %s mm" % " x ".join("%.1f" % v for v in ext),
                 "" if _fits(ext, R["build_mm"]) else "the part does not fit this process's build volume - another process, or split"))
    mb = M["MB"]
    rows.append(("file size <= %d MB (one model per file, %s)" % (R["file_max_mb"], "/".join(R["file_formats"])),
                 "PASS" if mb <= R["file_max_mb"] else "FAIL", "%.1f MB, %d triangles" % (mb, M["facets"]),
                 "" if mb <= R["file_max_mb"] else "kit printfile decimates to the limit"))
    wt = (M["open_edges"] == 0 and M["nonmanifold_edges"] == 0 and M.get("shells") == 1)
    rows.append(("watertight: 0 open edges, 0 non-manifold edges, 1 shell", "PASS" if wt else "FAIL",
                 "open %d, non-manifold %d, shells %s%s" % (M["open_edges"], M["nonmanifold_edges"], M.get("shells"),
                                                            (" (%d small: %s facets)" % (len(M.get("small_shells", [])), "/".join(str(s["facets"]) for s in M.get("small_shells", [])[:6]))) if M.get("small_shells") else ""),
                 "" if wt else "kit printfile: stitch, fill, drop fragments and inner shells, fix non-manifold; the shop's repair would do the same blind"))
    if M.get("degenerate_facets"):
        rows.append(("degenerate (zero-area) facets", "WARN", "%d" % M["degenerate_facets"], "kit printfile removes them"))
    if E.get("brep"):
        B = E["brep"]
        rows.append(("B-rep: one valid solid", "PASS" if (B["valid"] and B["solids"] == 1) else "FAIL",
                     "%d face(s), %d solid(s), valid %s, %.1f mm3" % (B["faces"], B["solids"], B["valid"], B["volume"]),
                     "" if (B["valid"] and B["solids"] == 1) else "the model of record is not a solid - fix before any print file"))
        dv = 100.0 * (M["volume"] - B["volume"]) / max(B["volume"], 1e-9)
        rows.append(("mesh volume vs B-rep volume (laminae and bubbles count twice)", "PASS" if abs(dv) < 0.5 else "WARN",
                     "%+.2f %% (mesh %.0f, B-rep %.0f mm3)" % (dv, M["volume"], B["volume"]), "" if abs(dv) < 0.5 else "expect laminae / inner shells - see the thin clusters"))
        rows.append(("B-rep tolerances (STEP survives under ~0.01 mm)", "PASS" if B["vertex_tol_max"] < 0.01 else "WARN",
                     "edge max %.3f, vertex max %.3f mm; %d faces under 0.30 mm2 (%.1f mm2)" % (B["edge_tol_max"], B["vertex_tol_max"], B["faces_under_mm2"]["0.30"], B["area_under_0.30"]),
                     "" if B["vertex_tol_max"] < 0.01 else "send STL, not STEP; slivers tessellate fine and print invisibly"))
        if E.get("step"):
            S = E["step"]
            ok = S.get("reimport_solids") == 1
            rows.append(("STEP round trip re-imports as 1 solid", "PASS" if ok else "FAIL",
                         ("%.1f MB, %d solid(s), %d faces back of %d" % (S["MB"], S["reimport_solids"], S["reimport_faces"], B["faces"])) if "MB" in S else S.get("error", "?"),
                         "" if ok else "never send this body as STEP"))
    thin = R["thinnest_min_mm"]; wall = R["auto_check_wall_mm"]
    cl = Wj.get("clusters", [])
    bad = [c for c in cl if c["median"] < thin and c["mm2"] >= 5.0]
    warn = [c for c in cl if c["median"] >= thin and c["mm2"] >= 5.0]
    for c in cl:
        c["region"] = _region_of(kit, c["centre"])
    rows.append(("walls: no place under the thinnest-part floor %.1f mm over 5 mm2 or more" % thin, "FAIL" if bad else "PASS",
                 "%.1f mm2 of surface under %.1f mm (%.2f %%); %d cluster(s) of 5 mm2+: %s"
                 % (Wj.get("mm2_under_thin", 0), thin, Wj.get("pct_under_thin", 0), len(bad),
                    "; ".join("%s %.0f mm2 median %.2f mm" % (c["region"] or "outside the atlas", c["mm2"], c["median"]) for c in bad[:8]) or "none"),
                 "" if not bad else "section pictures say wall or lamina: a wall needs a design change (thicken), a lamina a fill of the film (a drawn wedge fused over it); the shop's auto-check flags either"))
    rows.append(("walls: the auto-check floor %.1f mm (a question from the shop, not a refusal)" % wall, "WARN" if warn else "PASS",
                 "%.1f mm2 under %.1f mm (%.2f %%); %d further cluster(s) of 5 mm2+: %s"
                 % (Wj.get("mm2_under_wall", 0), wall, Wj.get("pct_under_wall", 0), len(warn),
                    "; ".join("%s %.0f mm2 median %.2f mm" % (c["region"] or "outside the atlas", c["mm2"], c["median"]) for c in warn[:8]) or "none"),
                 "" if not warn else "expect a question at the manual review; answer it or thicken"))
    if E.get("bores"):
        off = [b for b in E["bores"] if not b.get("ok")]
        pend = [b for b in off if b.get("pending_ad")]
        rows.append(("bores at spec (%s)" % os.path.basename(bores), "FAIL" if off else "PASS",
                     "%d of %d at spec; off: %s" % (len(E["bores"]) - len(off), len(E["bores"]),
                                                    "; ".join("%s spec %.2f x %.1f has %s" % (b["name"], b["dia"], b["depth"],
                                                                                              ("%.2f x %.2f" % (b["has"]["dia"], b["has"]["depth"])) if b.get("found") else "NOTHING at its axis")
                                                              for b in off[:6]) + (" ..." if len(off) > 6 else "") or "none"),
                     "" if not off else (("on a mesh: find what filled it (a drawn solid over the mouth - kit union's cavity/frozen report) and cut it clear; "
                                          "on the B-rep a `hole` worker job re-cuts them") + ("; %d spec(s) pending the client's word" % len(pend) if pend else ""))))
    elif bores:
        rows.append(("bores at spec (%s)" % os.path.basename(bores), "FAIL", "the export step measured NO bore (its log says why)",
                     "a --bores spec that measures nothing is a FAIL, never a silent pass (2026-09-25)"))
    fails = [r for r in rows if r[1] == "FAIL"]; warns = [r for r in rows if r[1] == "WARN"]
    verdict = "NOT ORDERABLE - %d blocker(s)" % len(fails) if fails else ("ORDERABLE with %d question(s) for the shop's review" % len(warns) if warns else "ORDERABLE")
    took = time.time() - t0
    lines = ["# PRINTCHECK - %s against %s (%s, %s)  %s" % (os.path.basename(body), rules_name, R["process"], R["material"], time.strftime("%Y-%m-%d %H:%M")),
             "", "**%s.** %.0f s. Rules read off the shop's pages %s - re-read them before ordering." % (verdict, took, R["read"]), "",
             "| rule | verdict | the number | what clears it |", "|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | **%s** | %s | %s |" % (r[0], r[1], r[2].replace("|", "/"), r[3]))
    lines += ["", "## How this shop processes the file", "", R.get("review", ""), "", R.get("notes", ""), ""]
    if cl:
        lines += ["## Thin clusters (under %.1f mm), by area - the census box, and the section that shows what it is" % wall, "",
                  "| # | region | mm2 | median mm | min mm | box (x y z extents, mm) | pictures |", "|---|---|---|---|---|---|---|"]
        for i, c in enumerate(cl[:25], 1):
            b = c["box"]
            pics = ", ".join(os.path.basename(s["file"]) for s in sections if s["cluster"] == i) or ("(under 5 mm2 - not sectioned)" if c["mm2"] < 5.0 else "-")
            lines.append("| %d | %s | %.1f | %.2f | %.2f | %.1f x %.1f x %.1f | %s |" % (i, c["region"] or "outside the atlas", c["mm2"], c["median"], c["min"], b[1] - b[0], b[3] - b[2], b[5] - b[4], pics))
        lines.append("")
    lines += ["## Files", "", "* `export.json`, `walls.json`, `walls.npz`, `sections\\` - the numbers and pictures above",
              "* `%s` - the mesh every number was taken on%s" % (os.path.basename(mesh), " (the B-rep tessellated at %g mm)" % dev if E["kind"] == "brep" else ""), ""]
    with open(os.path.join(out, "PRINTCHECK.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    json.dump({"body": body, "rules": rules_name, "verdict": verdict, "rows": rows, "export": E, "walls": {k: v for k, v in Wj.items() if k != "clusters"},
               "clusters": cl[:60], "sections": sections, "seconds": round(took)}, open(os.path.join(out, "printcheck.json"), "w", encoding="utf-8"), indent=1)
    print("\nkit printcheck: %s" % verdict)
    for r in rows:
        print("  %-5s %s - %s%s" % (r[1], r[0], r[2], ("  -> " + r[3]) if r[3] else ""))
    print("  report: %s\\PRINTCHECK.md%s" % (out, ("  (%d section pictures in sections\\ - open every one)" % len(sections)) if sections else ""))
    return 1 if fails else 0


def cmd_printfile(args, kit):
    """kit printfile <mesh.stl | body.brep> --out <file.stl> [--rules <name>] [--film 0.35] [--keep 1] [--max-mb 100]
                     [--dev 0.05] [--tag "<STL header>"] [--no-nmfix] [--work <dir>]

    THE FILE THAT GOES TO THE SHOP, from the mesh (or the B-rep, tessellated at --dev). Geometry is never moved
    except by the final decimation, and that only when the file is over the shop's size limit. Stages:
      A  (freecadcmd)  weld exact duplicates; drop degenerate and duplicate triangles; OPEN THE FILMS - every surface
                       that sees a facing surface within --film mm (a lamina, a slit, a crack) loses both walls, so the
                       body closes over the film; remove the dangling bridges; keep the --keep largest shells (a part
                       is one) and drop every fragment and bubble.
      B  (python)      the kit's nmfix (kit\\mesh\\_ccnmfix.py): pinches made manifold by vertex splitting, no face lost.
      C  (freecadcmd)  weld at FreeCAD's tolerance (1e-4); fill every boundary loop (minimum-area triangulation in 3-D,
                       flaps and junction vertices handled; FreeCAD's fillupHoles for the rest); decimate to --max-mb
                       (DecimatePro preserving topology; quadric on request), weld again, refill; write.
      B2 + C2          when pinches remain: nmfix on the written file, then stage C once more without decimation.
      verify           the kit's export census on the written file: facets, MB, open, non-manifold, shells, volume.
    Writes PRINTFILE.md beside the output and printfile.json in --work. Exit 1 when the file is still not closed.
    --rules names the shop (print_rules.json) and sets --max-mb from it. Then `kit printcheck <file> --rules <name>`.
    """
    if not args or args[0].startswith("-"):
        print(cmd_printfile.__doc__); return 2
    src = os.path.abspath(args[0])
    outp = kit._opt(args, "--out")
    if not os.path.isfile(src) or not outp:
        print("kit printfile: <mesh.stl | body.brep> and --out <file.stl> are required"); return 2
    outp = os.path.abspath(outp); os.makedirs(os.path.dirname(outp), exist_ok=True)
    R = rules_load(kit._opt(args, "--rules")) if kit._opt(args, "--rules") else None
    max_mb = float(kit._opt(args, "--max-mb") or (R["file_max_mb"] if R else 100))
    film = float(kit._opt(args, "--film") or 0.35); keep = int(kit._opt(args, "--keep") or 1); dev = float(kit._opt(args, "--dev") or 0.05)
    stem = os.path.splitext(os.path.basename(outp))[0]
    work = os.path.abspath(kit._opt(args, "--work") or os.path.join(kit.ROOT, "claude_code", "jobs", "PRINTFILE_%s" % stem))
    os.makedirs(work, exist_ok=True)
    tag = kit._opt(args, "--tag") or ("%s kit printfile %s" % (stem, time.strftime("%Y-%m-%d")))
    env = dict(os.environ)
    env.update({"KIT_HOME": kit.HERE, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"})
    t0 = time.time()
    print("kit printfile: %s -> %s\n  work: %s   film %.2f mm, keep %d shell(s), limit %.0f MB" % (src, outp, work, film, keep, max_mb))
    mesh_in = src
    if src.lower().endswith((".brep", ".brp")):
        env.update({"PC_IN": src, "PC_OUT": work, "PC_DEV": str(dev), "PC_STEP": "0"})
        rc = _run(kit, "_pc_export.py", env, 1800, os.path.join(work, "log_tess.txt"), True)
        if rc:
            print("kit printfile: tessellation failed (rc %s) - log_tess.txt" % rc); return rc
        mesh_in = os.path.join(work, "tess.stl")
    a_out = os.path.join(work, "A_clean.stl")
    env.update({"PF_IN": mesh_in, "PF_OUT": a_out, "PF_JSON": os.path.join(work, "A.json"), "PF_FILM": str(film), "PF_KEEP": str(keep)})
    rc = _run(kit, "_pf_a.py", env, 3600, os.path.join(work, "log_A.txt"), True)
    if rc:
        print("kit printfile: stage A failed (rc %s) - log_A.txt" % rc); return rc
    A = json.load(open(os.path.join(work, "A.json"), encoding="utf-8"))
    b_out = a_out
    if "--no-nmfix" not in args and A["out"]["nonmanifold_edges"]:
        b_out = os.path.join(work, "B_nmfix.stl")
        env2 = dict(env); env2.update({"CC_IN": a_out, "CC_OUT": b_out})
        script = os.path.join(kit.HERE, "mesh", "_ccnmfix.py")
        rc, out = kit.sh([sys.executable, "-W", "ignore", script], 3600, os.path.join(work, "log_B.txt"), env2, cwd=work)
        rc = kit._judge_output(out, rc, os.path.join(work, "log_B.txt"), "kit printfile")
        if rc or not os.path.isfile(b_out):
            print("kit printfile: nmfix failed (rc %s) - log_B.txt; continuing with stage A's mesh" % rc); b_out = a_out
    env.update({"PF_IN": b_out, "PF_OUT": outp, "PF_JSON": os.path.join(work, "C.json"), "PF_MAX_MB": str(max_mb), "PF_TAG": tag})
    rc = _run(kit, "_pf_c.py", env, 3600, os.path.join(work, "log_C.txt"), True)
    if rc:
        print("kit printfile: stage C failed (rc %s) - log_C.txt" % rc); return rc
    C = json.load(open(os.path.join(work, "C.json"), encoding="utf-8"))
    C2 = None
    if "--no-nmfix" not in args and (C["out"]["nonmanifold_edges"] or C["out"]["open_edges"]):
        b2 = os.path.join(work, "B2_nmfix.stl")
        env2 = dict(env); env2.update({"CC_IN": outp, "CC_OUT": b2})
        script = os.path.join(kit.HERE, "mesh", "_ccnmfix.py")
        rc, out = kit.sh([sys.executable, "-W", "ignore", script], 3600, os.path.join(work, "log_B2.txt"), env2, cwd=work)
        rc = kit._judge_output(out, rc, os.path.join(work, "log_B2.txt"), "kit printfile")
        if rc == 0 and os.path.isfile(b2):
            env.update({"PF_IN": b2, "PF_OUT": outp, "PF_JSON": os.path.join(work, "C2.json"), "PF_MAX_MB": "1e9"})
            rc = _run(kit, "_pf_c.py", env, 3600, os.path.join(work, "log_C2.txt"), True)
            if rc == 0:
                C2 = json.load(open(os.path.join(work, "C2.json"), encoding="utf-8"))
            else:
                print("kit printfile: the second stage C failed (rc %s) - log_C2.txt; the first pass's file stands" % rc)
        else:
            print("kit printfile: the second nmfix failed (rc %s) - log_B2.txt; the first pass's file stands" % rc)
    env.update({"PC_IN": outp, "PC_OUT": os.path.join(work, "verify"), "PC_DEV": str(dev), "PC_STEP": "0"})
    os.makedirs(env["PC_OUT"], exist_ok=True)
    rc = _run(kit, "_pc_export.py", env, 1800, os.path.join(work, "log_verify.txt"), True)
    Vf = json.load(open(os.path.join(work, "verify", "export.json"), encoding="utf-8"))["mesh"] if not rc else {}
    closed = bool(Vf) and Vf["open_edges"] == 0 and Vf["nonmanifold_edges"] == 0 and Vf.get("shells") == 1
    took = time.time() - t0
    film_cl = A.get("film", {}).get("clusters", [])
    lines = ["# PRINTFILE - %s  (%s)" % (os.path.basename(outp), time.strftime("%Y-%m-%d %H:%M")), "",
             "**%s.** %.0f s. From `%s`.%s" % ("CLOSED - one shell, 0 open, 0 non-manifold" if closed else "NOT CLOSED - see the counts", took, src,
                                               (" Size limit %.0f MB (%s)." % (max_mb, kit._opt(args, "--rules"))) if R else ""), "",
             "| stage | what happened |", "|---|---|",
             "| A weld | %d facets in, %d degenerate/duplicate removed; open %d, non-manifold %d |" % (A["weld"]["facets_in"], A["weld"]["degenerate_or_duplicate_removed"], A["after_weld"]["open_edges"], A["after_weld"]["nonmanifold_edges"]),
             "| A films (%.2f mm) | %d wall triangles removed, %.1f mm2 (%.3f %% of the surface) in %d place(s): %s |"
             % (film, A["film"].get("wall_triangles", 0), A["film"].get("wall_mm2", 0), A["film"].get("pct_of_surface", 0), len(film_cl),
                "; ".join("%.0f mm2 at %s" % (c["mm2"], _region_of(kit, [0.5 * (c["box"][0] + c["box"][1]), 0.5 * (c["box"][2] + c["box"][3]), 0.5 * (c["box"][4] + c["box"][5])]) or "outside the atlas") for c in film_cl[:8]) or "none"),
             "| A dangling | %d bridge triangles removed |" % A["dangling_removed"],
             "| A fragments | %d shell(s) in, %d kept, %d dropped (%d facets%s) |" % (A["fragments"]["shells_in"], A["fragments"]["kept"], len(A["fragments"]["dropped"]), A["fragments"]["dropped_facets"],
                                                                                    ("; largest dropped %d facets" % A["fragments"]["dropped"][0]["facets"]) if A["fragments"]["dropped"] else ""),
             "| B nmfix | %s |" % ("run: non-manifold %d -> %d" % (A["out"]["nonmanifold_edges"], C["in_counts"]["nonmanifold_edges"]) if b_out != a_out else "not needed / skipped"),
             "| C loose | %d shell(s) after nmfix, largest kept, %d dropped (%d facets) |" % (C["loose"]["shells"], len(C["loose"]["dropped"]), C["loose"]["dropped_facets"]),
             "| C fill | %d loop(s), %d closed with %d triangles, %d skipped; open after %d, non-manifold %d%s |"
             % (C["fill"]["loops"], C["fill"]["filled"], C["fill"]["triangles_added"], len(C["fill"]["skipped_loops"]), C["fill"]["open_after"], C["fill"]["nonmanifold_after"],
                ("; fillupHoles -> open %s" % C["fill"].get("fillupHoles", {}).get("open_after", "?")) if C["fill"].get("fillupHoles") else ""),
             "| C decimate | %s: %d -> %d facets%s%s |" % (C["decimate"]["method"], C["decimate"]["facets_before"], C["decimate"].get("facets_after", C["decimate"]["facets_before"]),
                                                       (" (open %d, non-manifold %d after)" % (C["decimate"]["open_after"], C["decimate"]["nonmanifold_after"])) if "open_after" in C["decimate"] else "",
                                                       ("; refill: %d loop(s), %d triangles, open %d, non-manifold %d" % (C["refill"]["filled"], C["refill"]["triangles_added"], C["refill"]["open_after"], C["refill"]["nonmanifold_after"])) if C.get("refill") else ""),
             "| C written | %d facets, %.1f MB, volume %.0f mm3, open %d, non-manifold %d |" % (C["out"]["facets"], C["out"]["MB"], C["out"]["volume"], C["out"]["open_edges"], C["out"]["nonmanifold_edges"]),
             "| B2 nmfix + C2 | %s |" % (("pinches split again; loose %d shell(s) dropped (%d facets); fill %d loop(s), open %d, non-manifold %d; written %d facets, %.1f MB, volume %.0f"
                                          % (len(C2["loose"]["dropped"]), C2["loose"]["dropped_facets"], C2["fill"]["filled"], C2["fill"]["open_after"], C2["fill"]["nonmanifold_after"], C2["out"]["facets"], C2["out"]["MB"], C2["out"]["volume"])) if C2 else "not needed"),
             "| verify (FreeCAD census) | %s |" % (("open %d, non-manifold %d, shells %s, volume %.0f, %s mm" % (Vf["open_edges"], Vf["nonmanifold_edges"], Vf.get("shells"), Vf["volume"], " x ".join("%.1f" % v for v in Vf["extent_mm"]))) if Vf else "verify step failed - log_verify.txt"),
             "", "Next: `kit printcheck %s --rules <shop>` for the wall census and the section pictures; open every picture." % outp, ""]
    with open(os.path.splitext(outp)[0] + "_PRINTFILE.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    json.dump({"src": src, "out": outp, "A": A, "C": C, "C2": C2, "verify": Vf, "closed": closed, "seconds": round(took)},
              open(os.path.join(work, "printfile.json"), "w", encoding="utf-8"), indent=1)
    print("\n".join(lines[2:3] + lines[5:]))
    print("  report: %s" % (os.path.splitext(outp)[0] + "_PRINTFILE.md"))
    return 0 if closed else 1


def cmd(args, kit):
    return cmd_printcheck(args, kit)

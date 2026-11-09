"""kit_mesh.py - `kit mesh <step>`: THE MESH ROUTE'S RUNNER (route A of voxel_smooth, and the whole-mesh gates).

the client, 2026-09-24: "mesh editing should not be in the burrito." The route's scripts - extract, core, refine, weld, seam,
the gates, the final assembly, the delivery zip - grew inside two project job folders
and ran through `kit burrito`, the BURRITO's runner, which injected the burrito's WINNING_ENV levers into every one of
them (the agent 2.10), let their status files race in the script folder (2.11), kept no census of their CC_ levers (2.9) and
keyed their wall clocks by script name only (2.6). They now live in the kit, in ONE copy (LEAN_KIT\\kit\\mesh\\), and this
runner is theirs:

    kit mesh <step|_script.py> --job <name> --tag <T> [--set K=V ...] [--env FILE] [--row <name>] [--plan] [--bg]
                               [--whole-body "<why>"] [-- <positional args for the script>]
    kit mesh gate <_tool.py|name> --job <J> --tag <T> [-- <args>]          the gate tools under mesh\\gates\\ (they take positional args; the --job / --tag form as every step)
    kit mesh --help                                    every step, its script and what it does

What every run gets: an environment that starts EMPTY of levers (nothing inherited from the shell), the --env file
then every --set, `KIT_HOME`, `CC_WORK` = `claude_code\\jobs\\<job>\\work\\` (every artefact, status file and log of a run
goes there, named by the tag - the scripts never write beside themselves), `CC_JOB`, `LK_TAG`; `CC_EXTENT` and
`CC_ATLAS` / `CC_ATLAS_MANIFEST` filled from the project's atlas when a step needs them and the run did not set them
(the extent is the union of the atlas boxes - no project number is hard-coded in the kit); the CC_ lever census of
`kit\\mesh\\LEVERS_CENSUS.md` (a CARD lever this step reads that the run does not set is REFUSED by name; a --set the
scripts never read is refused); the whole-body gate (`kit_crop.body_sized`); the run's env record `env<TAG>.json`; the
wall-clock budget from the project's WALL_CLOCKS.md row for the script (or `--row <name>` - the agent 2.6: the final's 27-core
refine needs its own row) run through the kit's `sh()` (extend while printing, kill on silence, `.KILLED` markers,
declared outputs renamed); and for the heavy steps a MACHINE SLOT (the agent 2.13: at most `mesh_slots` heavy kernels at
once, PID-owned, a dead owner's slot freed, a lock under 60 s never broken) - `kit mesh slots` shows and frees them.
"""
import os, sys, json, time, re, subprocess

STEPS = [
    ("extract",   "_ccextract.py",         "V2: the region's surface from the cleaned field (patch + gate)",  True),
    ("core",      "_blobcore.py",          "the weld core = the edit zone measured both ways, grown CC_M",     False),
    ("grow",      "_blobgrow.py",          "grow a core over far points / discarded regions",                 False),
    ("pair",      "_blobpair.py",          "narrow the margin where two cores meet (per-point Mi)",            False),
    ("trim",      "_blobtrim.py",          "keep edit points inside a box (reproduction-error tails)",         False),
    ("island",    "_islandgrow.py",        "patch rim loops under 15 mm become core",                          False),
    ("refine",    "_ccrefine.py",          "the base (a CROP) refined at the core wall, geometry unchanged",    False),
    ("weld",      "_ccweld.py",            "V3 route A: the patch welded onto the base, seammerge join",       True),
    ("seamdiag",  "_seamdiag.py",          "replay a refused seam: each far point ORDER or SHAPE",             False),
    ("thin",      "_ccthin.py",            "minimum wall from NEW surface + needle triangles (VTK)",           False),
    ("passage",   "_passage.py",           "lines of sight through a box, before against after",              False),
    ("regions",   "_ccexport_regions.py",  "frozen-region STLs for the gates and atlas recreated",             False),
    ("recreate",  "_recreate_preview.py",  "CUT preview of a frozen region against a result",                  False),
    ("collect",   "_collect.py",           "the GOOD + reviewed pieces of every zone -> the final's manifest", False),
    ("final",     "_final.py",             "ONE splice of every welded crop into the base + the agent's repairs",     False),
    ("gates",     "_finalgates.py",        "the whole-mesh gates on the assembled result",                     True),
    ("spikes",    "_ccspikes.py",          "spike flaps and specks out (CC_IN -> CC_OUT)",                     False),
    ("needle",    "_ccneedle.py",          "attached needles/fins on NEW surface cut and closed",              False),
    ("nmfix",     "_ccnmfix.py",           "pinches made manifold by vertex splitting (CC_REF)",              False),
    ("meshdoc",   "_ccmeshdoc.py",         "the throw-away mesh-only document for the delivery zip",          False),
    ("zip",       "_ccdeliver_zip.py",     "the delivery FCStd by zip surgery (payloads after their XML)",    False),
    ("guiload",   "_guiload.py",           "GUI load + view-property readback (runs under FreeCAD.exe)",       False),
]
HEAVY = {k for k, _, _, h in STEPS if h}
NEEDS_EXTENT = {"refine", "gates", "spikes", "final", "needle"}
NEEDS_ATLAS = {"zip"}
NEEDS_MANIFEST = {"extract"}
SLOT_MAX_DEFAULT = 2
SLOT_WAIT_DEFAULT_MIN = 180


def _mesh_dir(kit):
    return os.path.join(kit.HERE, "mesh")


def _pid_alive(pid):
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if os.name == "nt":
        try:
            r = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid, "/NH"], capture_output=True, text=True, timeout=15,
                               creationflags=0x08000000)
            return str(pid) in (r.stdout or "")
        except Exception:
            return True
    try:
        os.kill(pid, 0); return True
    except OSError:
        return False


def _slot_dir(root):
    import leangate as _G
    d = os.path.join(_G.records_root(root), ".claude", "_leangates", "slots")
    os.makedirs(d, exist_ok=True)
    return d


def slots_status(root, n_max):
    """[(slot index, holder dict or None, alive)]"""
    out = []
    d = _slot_dir(root)
    for i in range(n_max):
        p = os.path.join(d, "slot%d.json" % i)
        if os.path.isfile(p):
            try:
                h = json.load(open(p, encoding="utf-8"))
            except (OSError, ValueError):
                h = {"pid": None, "since": 0}
            out.append((i, h, _pid_alive(h.get("pid"))))
        else:
            out.append((i, None, False))
    return out


def slot_take(root, n_max, wait_min, what, say):
    """block until a slot is free (a dead owner's slot is freed - never one younger than 60 s); returns the lock path"""
    d = _slot_dir(root)
    t0 = time.time(); said = False
    while True:
        for i in range(n_max):
            p = os.path.join(d, "slot%d.json" % i)
            if os.path.isfile(p):
                try:
                    h = json.load(open(p, encoding="utf-8"))
                except (OSError, ValueError):
                    h = {"pid": None, "since": os.path.getmtime(p)}
                age = time.time() - float(h.get("since") or os.path.getmtime(p))
                if age > 60 and not _pid_alive(h.get("pid")):
                    say("  slot %d: its owner (pid %s, %s) is dead - freed" % (i, h.get("pid"), h.get("what", "?")))
                    try:
                        os.remove(p)
                    except OSError:
                        continue
                else:
                    continue
            try:
                fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                continue
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump({"pid": os.getpid(), "since": time.time(), "what": what, "when": time.strftime("%Y-%m-%d %H:%M:%S")}, fh)
            return p
        if time.time() - t0 > wait_min * 60:
            return None
        if not said:
            say("  slots: all %d busy - waiting (up to %d min): %s" % (n_max, wait_min, "; ".join(
                "slot %d %s pid %s" % (i, h.get("what", "?"), h.get("pid")) for i, h, _ in slots_status(root, n_max) if h)))
            said = True
        time.sleep(20)


def cmd_slots(args, kit, say=print):
    n_max = int(kit.ENV.get("mesh_slots", SLOT_MAX_DEFAULT))
    if "--free" in args:
        i = kit._opt(args, "--free")
        p = os.path.join(_slot_dir(kit.ROOT), "slot%s.json" % i)
        if not os.path.isfile(p):
            say("kit mesh slots: slot %s is not held" % i); return 2
        h = json.load(open(p, encoding="utf-8"))
        if _pid_alive(h.get("pid")) and "--anyway" not in args:
            say("kit mesh slots: slot %s is held by a LIVE process (pid %s, %s) - `--anyway` frees it regardless, which\n"
                "  kills nothing: the step keeps running outside the slot count. Kill it first with `kit collected <name> --kill`."
                % (i, h.get("pid"), h.get("what", "?")))
            return 2
        os.remove(p); say("kit mesh slots: slot %s freed (%s)" % (i, h.get("what", "?"))); return 0
    say("kit mesh slots: %d heavy-kernel slot(s) (env.json mesh_slots)" % n_max)
    for i, h, alive in slots_status(kit.ROOT, n_max):
        if h is None:
            say("  slot %d: free" % i)
        else:
            age_min = (time.time() - float(h.get("since", time.time()))) / 60
            if not alive and age_min * 60 > 60:
                try:
                    os.remove(os.path.join(_slot_dir(kit.ROOT), "slot%d.json" % i))
                    say("  slot %d: DEAD  pid %s  %s  since %s  (%.0f min) - its owner is gone: FREED"
                        % (i, h.get("pid"), h.get("what", "?"), h.get("when", "?"), age_min))
                    continue
                except OSError:
                    pass
            say("  slot %d: %s  pid %s  %s  since %s  (%.0f min)" % (i, "ALIVE" if alive else "DEAD ", h.get("pid"), h.get("what", "?"),
                                                                    h.get("when", "?"), age_min))
    say("  a dead owner's slot is freed when listed or taken; `--free <i> --anyway` is for a live one you have killed.")
    return 0


def _atlas_extent(kit):
    """the body of record's extent as `kit atlas extent` recorded it (a kernel measurement of the brep, with its md5).
    NOT the union of the atlas boxes: measured on R31 that union is 2.6 mm short in x, and the spike gate would have
    dropped real surface. None when it was never recorded - the step then says to run `kit atlas extent`."""
    try:
        ad = kit.G.atlas_load(kit.ROOT) or {}
        be = ad.get("body_extent") or {}
        box = be.get("box")
        if box and len(box) == 6:
            return [float(v) for v in box]
    except Exception:
        pass
    return None


def _atlas_box_union(kit):
    """the union of the atlas region boxes - good enough for 'is this STL the whole body' (the whole-body gate), never
    for a spike extent"""
    try:
        ad = kit.G.atlas_load(kit.ROOT) or {}
        bx = [[float(v) for v in r["box"]] for r in (ad.get("regions") or {}).values() if r.get("box") and len(r["box"]) == 6]
        if not bx:
            return None
        return [min(b[0] for b in bx), max(b[1] for b in bx), min(b[2] for b in bx), max(b[3] for b in bx),
                min(b[4] for b in bx), max(b[5] for b in bx)]
    except Exception:
        return None


def _atlas_manifest(kit):
    """the face manifest the extract's keepers read (region -> from_faces): named by the atlas as `manifest`, else the
    manifest.json beside the first region's surface_file, else nothing"""
    try:
        ad = kit.G.atlas_load(kit.ROOT) or {}
        m = ad.get("manifest") or (ad.get("recipe") or {}).get("manifest")
        if m and os.path.isfile(os.path.join(kit.ROOT, m) if not os.path.isabs(m) else m):
            return os.path.join(kit.ROOT, m) if not os.path.isabs(m) else m
        for r in (ad.get("regions") or {}).values():
            sf = r.get("surface_file")
            if sf:
                cand = os.path.join(os.path.dirname(os.path.join(kit.ROOT, sf) if not os.path.isabs(sf) else sf), "manifest.json")
                if os.path.isfile(cand):
                    return cand
    except Exception:
        pass
    return None


def cmd(args, kit):
    say = print
    G = kit.G
    MESH = _mesh_dir(kit)
    if not args or args[0] in ("-h", "--help"):
        say(__doc__)
        say("steps:")
        for k, scr, what, heavy in STEPS:
            say("  %-9s %-24s %s%s" % (k, scr, what, "   [heavy: takes a slot]" if heavy else ""))
        say("  gate      mesh\\gates\\<tool>.py    %s" % ", ".join(sorted(f[:-3] for f in os.listdir(os.path.join(MESH, "gates")) if f.endswith(".py"))))
        return 2
    if args[0] == "slots":
        return cmd_slots(args[1:], kit, say)
    if args[0] == "gate":
        if len(args) < 2:
            say("kit mesh gate <_tool.py|name> --job <J> --tag <T> [-- <args>]"); return 2
        nm = args[1] if args[1].endswith(".py") else "_%s.py" % args[1].lstrip("_")
        path = os.path.join(MESH, "gates", nm); step = "gate:" + nm[:-3]; what = "a gate tool"; heavy = False
        rest = args[2:]
    else:
        step = args[0]
        steps = {k: (scr, what, heavy) for k, scr, what, heavy in STEPS}
        if step in steps:
            script, what, heavy = steps[step]
        elif step.endswith(".py") and os.path.isfile(os.path.join(MESH, os.path.basename(step))):
            script, what, heavy = os.path.basename(step), "a script of the kit's mesh folder", False
        else:
            say("kit mesh: %r is not a step (%s) and not a script in %s" % (step, ", ".join(k for k, _, _, _ in STEPS), MESH)); return 2
        path = os.path.join(MESH, script)
        rest = args[1:]
    if not os.path.isfile(path):
        say("kit mesh: %s is missing from the kit (%s)" % (os.path.basename(path), MESH)); return 2
    script = os.path.basename(path)
    extra = []
    if "--" in rest:
        i = rest.index("--"); extra = rest[i + 1:]; rest = rest[:i]
    plan = "--plan" in rest
    job = kit._opt(rest, "--job")
    if not job:
        say("kit mesh: --job <name> names the job folder under claude_code\\jobs\\ whose work\\ holds this run's files"); return 2
    folder = os.path.join(kit.ROOT, "claude_code", "jobs", job)
    work = os.path.join(folder, "work")
    os.makedirs(work, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith(kit.LEVER_PREFIXES)}
    env["KIT_HOME"] = kit.HERE; env["PYTHONUTF8"] = "1"; env["PYTHONIOENCODING"] = "utf-8"
    envfile = kit._opt(rest, "--env")
    from_file = {}
    if envfile:
        try:
            from_file = {k: str(v) for k, v in json.load(open(envfile, encoding="utf-8")).items() if not k.startswith("_")}
        except (OSError, ValueError) as e:
            say("kit mesh: cannot read --env %s (%s)" % (envfile, e)); return 2
        env.update(from_file)
    sets = {}
    for kv in kit._all(rest, "--set"):
        if "=" not in kv:
            say("kit mesh: --set takes KEY=VALUE, not %r" % kv); return 2
        k, v = kv.split("=", 1); sets[k.strip()] = v
    tag = kit._opt(rest, "--tag") or sets.get("LK_TAG") or from_file.get("LK_TAG")
    if not tag:
        say("kit mesh: no tag. --tag <T> suffixes the status file, the env record and the log so two runs never overwrite each other."); return 2
    if not re.match(r"^[A-Za-z0-9_-]+$", tag):
        say("kit mesh: the tag is letters, digits, _ or - (it names files): %r" % tag); return 2
    sets["LK_TAG"] = tag
    env.update(sets)
    env["CC_WORK"] = work; env["CC_JOB"] = job; env["KIT_CWD"] = os.path.join(kit.ROOT, "claude_code")
    filled = {}
    if step in NEEDS_EXTENT and not env.get("CC_EXTENT", "").strip():
        ext = _atlas_extent(kit)
        if ext:
            env["CC_EXTENT"] = " ".join("%g" % v for v in ext); filled["CC_EXTENT"] = "kit atlas extent's record of the body"
        else:
            say("  CC_EXTENT: not set and the atlas carries no body extent - run `kit atlas extent` once (a kernel measurement of\n"
                "  the model of record); the step will refuse without it unless it is a crop base.")
    if step in NEEDS_ATLAS and not env.get("CC_ATLAS", "").strip():
        ap = G._atlas_path(kit.ROOT)
        if os.path.isfile(ap):
            env["CC_ATLAS"] = ap; filled["CC_ATLAS"] = "the project's atlas"
    if step in NEEDS_MANIFEST and not env.get("CC_ATLAS_MANIFEST", "").strip():
        mp = _atlas_manifest(kit)
        if mp:
            env["CC_ATLAS_MANIFEST"] = mp; filled["CC_ATLAS_MANIFEST"] = "from the atlas record"
    rows, _ = G.levers(MESH, "CC_", envfile)
    known = {r[0]: r for r in rows}
    unknown = [k for k in sets if k.startswith("CC_") and k not in known]
    if unknown:
        say("kit mesh: --set names a lever NO script in the mesh folder reads: %s. `kit levers \"%s\" --prefix CC_` lists the %d that exist."
            % (", ".join(unknown), MESH, len(known))); return 2
    mine = [r for r in rows if script in r[1]]
    say("kit mesh: %s -> %s   (%s)" % (step, script, what))
    say("  job     : %s   work: %s" % (folder, work))
    say("  settings: %s%s" % (envfile or "(none)", " + %d --set" % len(sets) if sets else ""))
    for k, why in filled.items():
        say("  filled  : %s = %s   (%s)" % (k, env[k] if len(env[k]) < 70 else env[k][:67] + "...", why))
    uncls, missing, has_census = G.census_check(MESH, set(from_file) | set(sets) | set(filled), script)
    if has_census:
        if missing:
            say("kit mesh REFUSED: %s reads %d CARD lever(s) this run does not set: %s\n"
                "  A CARD lever is a number the card decides - set each one (--set KEY=VALUE, or the run's env file; an empty\n"
                "  value is a decision too), or reclassify it in %s\\LEVERS_CENSUS.md with a note saying why the default is right."
                % (script, len(missing), ", ".join(missing), MESH))
            return 2
        if uncls:
            say("  census  : %d lever(s) this script reads are not yet classified: %s" % (len(uncls), ", ".join(uncls[:12]) + (" ..." if len(uncls) > 12 else "")))
    else:
        say("  census  : none (%s\\LEVERS_CENSUS.md) - every default is being taken as the answer" % MESH)
    say("  tag     : %s" % tag)
    named = sorted(set(from_file) | set(sets) | set(filled))
    rec = {"_step": step, "_script": script, "_when": time.strftime("%Y-%m-%d %H:%M:%S"), "_settings_file": envfile,
           "_sources": {k: ("--set" if k in sets else ("filled:" + filled[k] if k in filled else "file")) for k in named},
           "_args": extra}
    rec.update({k: env[k] for k in named if k in env})
    rec["_inherited"] = kit._lever_env(env, MESH, set(rec))
    try:
        with open(os.path.join(work, "env%s.json" % tag), "w", encoding="utf-8") as fh:
            json.dump(rec, fh, indent=1)
        say("  env file: work\\env%s.json (%d lever(s) set, %d filled)" % (tag, len(named) - len(filled), len(filled)))
    except OSError as e:
        say("  env file: NOT written (%s)" % e)
    say("  levers this script reads: %d - %d set, %d on a hardcoded default"
        % (len(mine), sum(1 for r in mine if r[0] in env), sum(1 for r in mine if r[0] not in env)))
    for r in mine:
        say("    %s%-22s %s" % ("set " if r[0] in env else "    ", r[0], ("= " + str(env.get(r[0]))[:60]) if r[0] in env else ("default " + (r[2] or "-"))))
    try:
        import kit_crop as KC
        ext = _atlas_extent(kit) or _atlas_box_union(kit)
        ext_lh = ([ext[0], ext[2], ext[4]], [ext[1], ext[3], ext[5]]) if ext else None
        whole = []
        for k, v in env.items():
            if not (k.startswith("CC_") and isinstance(v, str) and v.strip().lower().endswith(".stl")) or "OUT" in k:
                continue
            p = v.strip() if os.path.isabs(v.strip()) else os.path.join(work, v.strip())
            if os.path.isfile(p):
                big, why = KC.body_sized(p, ext_lh)
                if big:
                    whole.append((k, os.path.basename(p), why))
        why_wb = kit._opt(rest, "--whole-body")
        if whole and not why_wb:
            say("kit mesh REFUSED: %s is the WHOLE BODY (%s) and this step would process all of it.\n"
                "  The route's unit of work is a CROP: kit crop <body.stl> --box <extract box> --margin 6 --out work\\<name>_crop.stl,\n"
                "  then run this step on the crop and `kit splice` puts it back. If there is genuinely no other way,\n"
                "  --whole-body \"<why>\" runs it and the reason goes into the env record."
                % (", ".join(k for k, _, _ in whole), "; ".join("%s: %s" % (b, w) for _, b, w in whole)))
            return 2
        if whole and why_wb:
            say("  WHOLE BODY: %s - run on the recorded exception: %s" % (", ".join(k for k, _, _ in whole), why_wb))
            try:
                ef = os.path.join(work, "env%s.json" % tag)
                ej = json.load(open(ef, encoding="utf-8")); ej["_whole_body_because"] = why_wb
                json.dump(ej, open(ef, "w", encoding="utf-8"), indent=1)
            except (OSError, ValueError):
                pass
    except ImportError:
        pass
    W = kit._wallclock()
    row = kit._opt(rest, "--row") or script
    budget_min, why = (W.budget_for(row, "Bash", kit.ROOT) if W else (4.0, "no wall clock module"))
    cap = max(int(budget_min * 60 * 2), 60)
    say("  budget  : %.1f min (%s; row %s); cap %d s%s" % (budget_min, why, row, cap, "   [heavy: takes a slot]" if heavy else ""))
    if plan:
        say("  --plan: nothing was run."); return 0
    log = os.path.join(work, "log_%s_%s.txt" % (os.path.splitext(script)[0], tag))
    needs_fc = bool(re.search(r"^\s*(?:import|from)\s+(?:FreeCAD|FreeCADGui|Part|MeshPart|Mesh|vtk)\b",
                              open(path, encoding="utf-8", errors="replace").read(), re.M))
    runner = kit.freecad() if needs_fc else sys.executable
    if not needs_fc:
        env.setdefault("PYTHONUNBUFFERED", "1")
    cmdline = ([runner, path] if needs_fc else [runner, "-W", "ignore", path]) + extra
    say("  runs under: %s%s" % ("freecadcmd (imports the kernel/VTK)" if needs_fc else os.path.basename(runner) + " (pure python)",
                                 "   args: " + " ".join(extra) if extra else ""))
    _miss_out = []
    for _k, _v in list(env.items()):
        if not (_k.startswith("CC_") and "OUT" in _k and isinstance(_v, str) and re.search(r"\.(stl|brep|npz|json|fcstd|step|stp|obj|ply|png)$", _v.strip(), re.I)): continue
        _vv = _v.strip()
        if os.path.isabs(_vv):
            if not os.path.isdir(os.path.dirname(_vv)): _miss_out.append("%s=%s (no folder %s)" % (_k, _vv, os.path.dirname(_vv)))
            continue
        if not ("/" in _vv or "\\" in _vv):
            env[_k] = os.path.join(work, _vv); continue
        for _base in (os.getcwd(), os.path.join(kit.ROOT, "claude_code"), kit.ROOT, work):
            _c = os.path.normpath(os.path.join(_base, _vv))
            if os.path.isdir(os.path.dirname(_c)): env[_k] = _c; say("  %s: %s -> %s (resolved against %s)" % (_k, _vv, _c, _base)); break
        else: _miss_out.append("%s=%s" % (_k, _vv))
    if _miss_out:
        print("kit mesh %s REFUSED: these CC_*OUT* path(s) have no folder to land in (tried against the folder you ran from, claude_code\\, the project root and the job's work folder): %s\n"
              "  Make the folder first, or name the file alone - a bare name lands in the job's work folder." % (script, "; ".join(_miss_out))); return 2
    outs = [v.strip() for k, v in env.items() if k.startswith("CC_") and "OUT" in k and isinstance(v, str)
            and re.search(r"\.(stl|brep|npz|json|fcstd|step|stp|obj|ply|png)$", v.strip(), re.I)]
    _miss = []
    for _k, _v in list(env.items()):
        if not (_k.startswith("CC_") and "OUT" not in _k and isinstance(_v, str) and re.search(r"\.(stl|brep|npz|json|fcstd|step|stp|obj|ply)$", _v.strip(), re.I)): continue
        _vv = _v.strip()
        if os.path.isabs(_vv):
            if not os.path.exists(_vv): _miss.append("%s=%s" % (_k, _vv))
            continue
        for _base in (work, os.path.join(kit.ROOT, "claude_code"), kit.ROOT):
            _c = os.path.normpath(os.path.join(_base, _vv))
            if os.path.exists(_c): env[_k] = _c; say("  %s: %s -> %s (resolved against %s)" % (_k, _vv, _c, _base)); break
        else: _miss.append("%s=%s" % (_k, _vv))
    if _miss:
        print("kit mesh %s REFUSED: these CC_* input path(s) resolve to no file (tried as given, against the job's work folder, claude_code\\ and the project root): %s\n  Give absolute paths (kit crop prints its output's absolute path)." % (step, "; ".join(_miss))); return 2
    if "--bg" in rest:
        name = "mesh_%s_%s" % (step.replace(":", "_"), tag)
        env.setdefault("PYTHONUNBUFFERED", "1")
        with open(log, "w", encoding="utf-8") as fh:
            _p = subprocess.Popen(cmdline, cwd=work, env=env, stdout=fh, stderr=subprocess.STDOUT,
                                  creationflags=(0x08000000 if os.name == "nt" else 0))
            pid = _p.pid
            if hasattr(kit, "pin_process"):
                kit.pin_process(_p)
        if W:
            W.watch_add(kit.ROOT, name, budget_min, "kit mesh %s (%s)" % (step, script),
                        owner=G.current_conversation(kit.ROOT) or "", pid=pid)
        say("  started in the background, pid %d, log %s\n  ON THE CLOCK as %s - `kit collected %s` when it is read; `--kill` ends it by pid."
            % (pid, log, name, name))
        say("  (a --bg heavy step takes NO slot: run heavy steps blocking, or count them yourself)")
        return 0
    lock = None
    if heavy:
        n_max = int(kit.ENV.get("mesh_slots", SLOT_MAX_DEFAULT))
        wait_min = float(kit._opt(rest, "--wait") or kit.ENV.get("mesh_slot_wait_min", SLOT_WAIT_DEFAULT_MIN))
        lock = slot_take(kit.ROOT, n_max, wait_min, "kit mesh %s %s (%s)" % (step, tag, job), say)
        if not lock:
            say("kit mesh REFUSED: no slot came free in %d min - `kit mesh slots` shows the holders." % wait_min); return 2
        say("  slot    : %s" % os.path.basename(lock))
    before = time.time()
    try:
        rc, out = kit.sh(cmdline, cap, log, env, cwd=work, outputs=outs)
    finally:
        if lock:
            try:
                os.remove(lock)
            except OSError:
                pass
    took = time.time() - before
    rc = kit._judge_output(out, rc, log, "kit mesh")
    newest = None
    try:
        cands = [f for f in os.listdir(work) if f.startswith("status") and f.endswith(".json") and tag in f
                 and os.path.getmtime(os.path.join(work, f)) >= before]
        newest = max(cands, key=lambda f: os.path.getmtime(os.path.join(work, f))) if cands else None
        if rc == kit.KILLED_RC and newest:
            os.replace(os.path.join(work, newest), os.path.join(work, newest + ".KILLED"))
            say("  status  : %s was written by the killed step - renamed .KILLED, not a result" % newest); newest = None
    except OSError:
        pass
    typical = (W.table_budgets(kit.ROOT).get(row) if W else None)
    flag = "   RED FLAG - %.1fx the typical %.0f s (the client: 1.5x needs evaluating)" % (took / typical, typical) if typical and took > 1.5 * typical else ""
    say("kit mesh: rc %s, %.0f s%s, log %s" % (rc, took, flag, log))
    say("  status  : %s" % (os.path.join("work", newest) if newest else "no status file written by this step - wait on its artefact, never on a status name"))
    _nxt = {"extract": "kit mesh core --job %s --tag %s --set CC_BASE=<the crop.stl> --set CC_PATCH=<the patch.stl this step wrote> --set CC_OUT=<blob.npz> (+ the core's levers)",
            "core": "kit mesh refine --job %s --tag %s --set CC_BODY=<the crop.stl> --set CC_BLOBS=<the blob.npz this step wrote> --set CC_DEV=<the extract's CC_DEV - the recipe's 0.08> --set CC_OUT=<cbase.stl> [--set CC_EXTENT=\"x0 x1 y0 y1 z0 z1\" (the body of record's extent, for the flap pass)] (+ its levers from LEVERS_CENSUS.md: CC_REFINE_L ...)",
            "refine": "kit mesh weld --job %s --tag %sW --env <RECIPE_WELD.json> --set CC_BODY=<cbase.stl> --set CC_PATCH=<the patch.stl> --set CC_CORE_BLOB=<blob.npz> --set CC_OUT=<cweld.stl>",
            "weld": "kit mesh gate _nmnew --job %s --tag %s -- <crop.stl> <cweld.stl>  and  kit mesh gate _shells ... ; then kit splice <cweld.stl> --crop <the crop's .crop.json (beside the crop.stl)> --out <body2.stl>",
            "gates": "kit splice (route A) or kit printfile on the assembled result (VOXEL_SMOOTH_STEPS.md)"}
    if rc == 0 and step in _nxt: say("  Next    : %s" % (_nxt[step] % ((job, tag) if _nxt[step].count("%s") == 2 else ())))
    elif rc == 0: say("  Next    : the route's next step (VOXEL_SMOOTH_STEPS.md; `kit mesh --help` lists the steps)")
    try:
        if W and hasattr(W, "state_behind"):
            n_new, sfolder, has_state = W.state_behind(kit.ROOT)
            if n_new >= getattr(W, "STATE_EVERY", 25):
                say("  STATE   : %d new artefacts in %s since %s - write claude_code\\STATE_NOW.md now (kit state --note ...)"
                    % (n_new, os.path.basename(sfolder), "STATE_NOW.md was written" if has_state else "the session opened"))
    except Exception:
        pass
    return rc

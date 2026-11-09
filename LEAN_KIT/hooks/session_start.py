#!/usr/bin/env python3
"""session_start.py — SessionStart warden for the LEAN kit. The contract arrives; it is not found.

Pushes, before the first prompt:
  * CONTRACT.md in full — ONE PAGE, deliberately
  * the edit-type catalogue as a LIST OF NAMES, not the cards
  * whether a gate session is open, and what is unfinished if one is
  * whether the PreToolUse guard is actually running

WHY IT PUSHES SO LITTLE, and this is the whole design difference (the client, 2026-09-09):
*"The main difference for the lean kit is it's not trying to teach everything at each
agent/session launch. It's setting up only the workflows that can have a chance of success."*

An earlier kit's equivalent hook pushes its start file, the ledger format in full, the carried
settings and a police report, and then requires a 1,965-line master to be read and examined —
roughly 45-50k tokens before the first command. Measured against what that bought on the part:
8,021 gate-log rows, 2,039 stamped review images, 96 % of look challenges satisfied, and a round
that still edited the wrong faces because the brief joined a size census to a colour picture with
an assumption.

So this pushes a page, names the ten edit types WITHOUT their cards, and stops. The cards arrive
one at a time, when a card of that type is linted — a `hole` job never reads about mirror planes.
Traps arrive the same way. Nothing here is a summary of something longer; there is nothing longer.

Cannot block anything. What it removes is the excuse "I did not know the rules were there", and
the slower failure where the rules were there and nobody had reason to open them.
"""

import json
import os
import sys
for _s_ in (sys.stdout, sys.stderr):      # transcript
    try: _s_.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
import time

HERE = os.path.dirname(os.path.abspath(__file__))

PROCESS_RULES = ("PA12_MJF_Rules_EVALUATED.md",)


def _first_existing(*paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


def payload():
    try:
        return json.load(sys.stdin)
    except Exception:
        return None


def project_root(data):
    root = (data or {}).get("cwd") or ""
    if not root:
        return None
    while root and not os.path.exists(os.path.join(root, ".claude")) \
            and os.path.dirname(root) != root:
        root = os.path.dirname(root)
    return root if os.path.exists(os.path.join(root, ".claude")) else None


def find_kit(root):
    """The LEAN_KIT folder, wherever it was installed from. The project's copy of the docs may
    be alongside the kit or in claude_code\\ — both layouts exist on this machine."""
    for cand in (os.path.join(os.path.dirname(HERE)),
                 os.path.join(root, "claude_code"),
                 root):
        if os.path.exists(os.path.join(cand, "CONTRACT.md")) or \
           os.path.exists(os.path.join(cand, "EDIT_TYPES.md")):
            return cand
    return os.path.dirname(HERE)


def main():
    data = payload()
    if not isinstance(data, dict) or not data.get("cwd"):
        try: sys.stderr.write("session_start: the hook payload is not JSON or names no cwd - nothing pushed (the project is the payload's cwd, never this process's folder; 31bv)\n")
        except Exception: pass
        sys.exit(0)
    root = project_root(data)
    if not root:
        sys.exit(0)
    kit = find_kit(root)
    out = []

    # METHOD.md
    cwd = data.get("cwd") or ""
    _cwd_n = os.path.normcase(os.path.abspath(cwd)) if cwd else ""; _root_n = os.path.normcase(os.path.abspath(root))
    if cwd and _cwd_n != _root_n and not _cwd_n.startswith(_root_n.rstrip(os.sep) + os.sep):
        out.append("!" * 78)
        out.append("CLAUDE CODE WAS STARTED OUTSIDE THIS PROJECT (above it, or elsewhere), NOT IN IT.")
        out.append("   started in : %s" % cwd)
        out.append("   project    : %s" % root)
        out.append("")
        out.append("Claude Code reads .claude\\agents\\ and .claude\\settings.json from the folder")
        out.append("it was started in. From up there it finds neither, so:")
        out.append("  * cad-worker-haiku / sonnet / opus are NOT loaded — workers run as generic")
        out.append("    agents at whatever tier the launcher picks, not the tiers you tested;")
        out.append("  * the project's own hooks may not fire (this one is running from wherever Claude Code")
        out.append("    was started), so nothing is certainly enforcing METHOD.md 5.")
        out.append("")
        out.append("Neither announces itself. Close this session and start again IN the project:")
        out.append("    the project root must be:  %s" % root)
        out.append("      * desktop app: change the folder this project is open on")
        out.append("      * terminal:    restart Claude Code from inside that folder")
        out.append("!" * 78)
        out.append("")

    # still needs
    for name in ("CONTRACT.md", "ORCHESTRATOR.md"):
        p = os.path.join(kit, name)
        if os.path.exists(p):
            with open(p, encoding="utf-8", errors="replace") as fh:
                out.append(fh.read().rstrip())
            out.append("")

    for name in PROCESS_RULES:
        p = _first_existing(os.path.join(root, "references", name),
                            os.path.join(os.path.dirname(root), name),
                            os.path.join(os.path.dirname(root), "references", name),
                            os.path.join(root, "claude_code", name),
                            os.path.join(kit, name),
                            os.path.join(root, name))
        if p:
            with open(p, encoding="utf-8", errors="replace") as fh:
                txt = fh.read().rstrip()
            out.append("--- MANUFACTURING RULES — %s (%s) ---" % (name, os.path.dirname(p)))
            out.append("These are constraints on every edit, not background. A part that measures")
            out.append("perfectly and cannot be printed has failed, and no gate in this kit can")
            out.append("tell you so — they all measure geometry.")
            out.append("")
            out.append(txt)
            out.append("")
        else:
            out.append("!! %s WAS NOT FOUND — this session is running without the manufacturing"
                       % name)
            out.append("   rules. Looked in: %s, %s, %s"
                       % (os.path.join(root, "claude_code"), kit, root))
            out.append("   Put it in claude_code\\ (the evaluated, project-specific copy) or ask the client")
            out.append("   where it lives. Do not infer print limits from memory.")
            out.append("")

    # kit howto <type>
    et = os.path.join(kit, "EDIT_TYPES.md")
    if os.path.exists(et):
        import re as _re
        txt = open(et, encoding="utf-8", errors="replace").read()
        rows = []
        for m in _re.finditer(r"^## (\S+) — .*?$(.*?)(?=^## |\Z)", txt, _re.M | _re.S):
            name = m.group(1)
            if name in ("GENERAL", "SYMPTOMS"):
                continue
            body = m.group(2)
            r = _re.search(r"^Route:\s*(.+)$", body, _re.M); t = _re.search(r"^Tier:\s*(.+?)(?: - | \(|\.|$)", body, _re.M)
            rows.append((name, (t.group(1).strip() if t else "?")[:12], (r.group(1).strip() if r else "")[:70]))
        if rows:
            out.append("--- THE ROUTER: %d edit types. `kit route \"<the request in words>\"` names the one to use and prints its"
                       " sequence and what to read; nothing else is read until it does. ---" % len(rows))
            for name, tier, words in rows:
                out.append("    %-16s %-12s %s" % (name, tier, words))
            out.append("    A feature that fits none: split it into ones that do, or ask the client.")
            out.append("")

    for rel, label, keep in ((os.path.join("claude_code", "STATE_NOW.md"), "STATE_NOW (newest block)", 24),
                             ("SESSION_HANDOFF.md", "SESSION_HANDOFF (head)", 14)):
        p = os.path.join(root, rel)
        if os.path.isfile(p):
            try:
                lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                continue
            if rel.endswith("STATE_NOW.md"):
                blk, started = [], False
                for ln in lines:
                    if ln.startswith("# >>> UPDATE"):
                        if started:
                            break
                        started = True
                    if started:
                        blk.append(ln)
                lines = blk or lines
            out.append("--- %s: %s ---" % (label, rel))
            out += ["    " + l for l in lines[:keep]]
            if len(lines) > keep:
                out.append("    ... (%d more lines in the file)" % (len(lines) - keep))
            out.append("")

    if str(data.get("source") or "").lower() == "compact":
        _cb = []
        try:
            import glob as _glob, json as _json, re as _re
            _cb.append("=" * 78); _cb.append("AFTER THE COMPACTION - THE STATE ON DISK (read it before your next move; the summary is a digest, this is the state):")
            try:
                sys.path.insert(0, HERE); import lookgate as _LGc
                _ow = (_LGc._dd_load(root) or {}).get("owed")
                if _ow: _cb.append("    A STRIKE IS OWED: %s - the apology in your message first (CONTRACT 8a)" % _json.dumps(_ow)[:160])
            except Exception: pass
            try:
                sys.path.insert(0, os.path.join(kit, "kit")); import leangate as _Gc
                _new, _tot = _Gc.inbox_new(root)
                if _new.strip():
                    _hd = [l for l in _new.splitlines() if l.startswith("# ")][:6]
                    _cb.append("    INBOX unread since your last look (%d chars): %s - `kit inbox` reads them" % (len(_new), " | ".join(h[:80] for h in _hd) or _new.strip()[:120]))
            except Exception: pass
            jobs_dir = os.path.join(root, "claude_code", "jobs"); logs = sorted(_glob.glob(os.path.join(jobs_dir, "*", "BUILD_LOG.md")), key=os.path.getmtime)
            try:
                _sn = open(os.path.join(root, "claude_code", "STATE_NOW.md"), encoding="utf-8", errors="replace").read(); _blk = _sn.split("# >>> UPDATE")[1] if "# >>> UPDATE" in _sn else _sn[:2000]
                _pos = {}
                for l_ in logs:
                    _m = _re.search(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % _re.escape(os.path.basename(os.path.dirname(l_))), _blk)
                    if _m: _pos[l_] = _m.start()
                if _pos: logs = [l_ for l_ in logs if l_ not in _pos] + sorted(_pos, key=lambda l_: _pos[l_], reverse=True)
            except Exception: pass
            if not logs: _cb.append("    no job is open in this project (no BUILD_LOG) - the state is STATE_NOW's newest block and `kit status` (31bx R3 F8)")
            if logs:
                bl = logs[-1]; jname = os.path.basename(os.path.dirname(bl)); jdir = os.path.dirname(bl)
                _cb.append("    THE LIVE JOB'S OWN RECORD (%s):" % jname)
                for jf in sorted(_glob.glob(os.path.join(jdir, "skin", "review", "*_JUDGED.json"))) + sorted(_glob.glob(os.path.join(jdir, "review_body", "TRIAL_JUDGED.json"))) + sorted(_glob.glob(os.path.join(jdir, "review", "*_JUDGED.json"))) + sorted(_glob.glob(os.path.join(jdir, "keep", "*_JUDGED.json"))):
                    try:
                        j = _json.load(open(jf, encoding="utf-8"))
                        _cb.append("    judged (%s): %-22s %-8s %s %s" % (jname, os.path.basename(jf), str(j.get("verdict", j.get("ok", "?"))), str(j.get("when", ""))[:19], (str(j.get("note", ""))[:90]) if j.get("note") else ""))
                    except Exception:
                        pass
                for nm in ("RESTART.json", "TRIAL.json", "LAYOUT_LOCK.json"):
                    fp = os.path.join(jdir, "skin", nm) if nm != "TRIAL.json" else os.path.join(jdir, nm)
                    if os.path.isfile(fp):
                        try:
                            j = _json.load(open(fp, encoding="utf-8")); _cb.append("    %s: %s" % (nm, _json.dumps(j)[:220]))
                        except Exception:
                            pass
                rows = [l for l in open(bl, encoding="utf-8", errors="replace").read().splitlines() if l.startswith("| 20")]
                _cl = [[x_.strip() for x_ in r_.strip().strip("|").split("|")] for r_ in rows]
                _rf = [len(c_) >= 6 and c_[5] == "2" for c_ in _cl]
                _runs = [i_ for i_ in range(len(rows)) if not _rf[i_]]; _shown = _runs[-5:]
                _since = _shown[0] if len(_runs) > 5 else 0
                _refs = [i_ for i_ in range(_since, len(rows)) if _rf[i_]]
                _rt = lambda i_: (("%s %s %s: %s (rc %s)" % (_cl[i_][0][11:16], _cl[i_][1], _cl[i_][2], _cl[i_][4][:120], _cl[i_][5])) if len(_cl[i_]) >= 6 else rows[i_][:160])
                _cb.append("--- job %s: BUILD_LOG.md, the newest %d of %d runs (when / tag / step / the line / rc); %d runner refusal row(s) (rc 2) counted, not listed ---"
                           % (jname, len(_shown), len(_runs), sum(_rf)))
                for i_ in _shown:
                    _cb.append("    " + _rt(i_))
                if _refs:
                    _cb.append("    %d refusal(s) (rc 2, the runner's) since %s (%s) - the newest: %s"
                               % (len(_refs), _cl[_since][0][:16], "the oldest row shown" if _shown and _since == _shown[0] else "the log's first row", _rt(_refs[-1])))
            _cb.append("    Your standing orders ride every turn (CLAUDE.md); the decisions are on disk (LINES / FEATURES / the judge records) - nothing in flight was lost, only the detail in your memory.")
            _cb.append("=" * 78); _cb.append("")
            out[0:0] = _cb
        except Exception as _ex:
            out.append("NOTE: the post-compaction push failed (%s) - `kit status` and the job's BUILD_LOG.md are the state." % _ex)
    try:
        import hashlib as _hl, glob as _g2
        _ag_k = os.path.join(kit, "agents"); _ag_p = os.path.join(root, ".claude", "agents"); _stale = []
        for _f in _g2.glob(os.path.join(_ag_k, "*.md")):
            _q = os.path.join(_ag_p, os.path.basename(_f))
            if not os.path.isfile(_q) or _hl.md5(open(_q, "rb").read()).hexdigest() != _hl.md5(open(_f, "rb").read()).hexdigest(): _stale.append(os.path.basename(_f))
        if _stale: out.append("AGENTS STALE: %s in .claude\\agents\\ differ from the kit's agents\\ - copy the kit's over them before a review that uses them (31bq B15)" % ", ".join(_stale))
    except Exception:
        pass
    sys.path.insert(0, os.path.join(kit, "kit"))
    state = "none"
    try:
        import leangate as G
        G.stamp_conversation(root, data.get("session_id"))
        state, sess = G.session_state(root, data.get("session_id"))
        jobs = G._read(G._p(root, G.JOBS), {}) or {}
    except Exception as exc:
        out.append("NOTE: could not read the gate state (%s). `kit status` will say why."
                   % exc)
        sess, jobs = None, {}

    if state == "carried":
        out.append("=" * 78)
        out.append("THIS CONVERSATION COMPACTED. THE SESSION IS STILL YOURS AND STILL OPEN.")
        out.append("Nothing needs re-declaring and nothing in flight was lost — the gates are")
        out.append("code and a compaction does not touch them. What the compaction DID destroy")
        out.append("is your memory of the detail, so re-anchor on the registers below before")
        out.append("your next move. `kit status` is the full picture; it is read off disk.")
        out.append("=" * 78)
        out.append("")
    elif state == "foreign":
        out.append("!" * 78)
        out.append("A SESSION IS OPEN AND IT BELONGS TO A DIFFERENT CONVERSATION.")
        out.append("It was opened %s by another run, and jobs from it are still unapplied."
                   % (sess or {}).get("opened"))
        out.append("")
        out.append("You have NOT done the reading it certifies. Two honest choices:")
        out.append("  * pick up its work — read METHOD.md and EDIT_TYPES.md, then `kit open`")
        out.append("    again to put YOUR name on the session; or")
        out.append("  * leave it alone and ask the client which of you owns this project right now.")
        out.append("Do not simply carry on: the reading gate exists because the failures it")
        out.append("prevents are the ones nobody remembers reading about.")
        out.append("!" * 78)
        out.append("")
    elif state == "orphan":
        out.append("NOTE: a session from another conversation is open with nothing in flight.")
        out.append("      `kit open` to take it over once you have done the reading.")
        out.append("")

    out.append("=" * 78)
    try:
        _bk = os.path.join(root, "claude_code", "bank")
        _has = any(f.lower().endswith((".brep", ".stl", ".step", ".stp", ".fcstd")) for f in (os.listdir(_bk) if os.path.isdir(_bk) else []))
        if not _has and not (sess or {}).get("model_of_record"):
            out.append("THE BANK IS EMPTY - a project that designs from parts starts here: read LEAN_KIT\\PROJECT_START.md (one page - the first body, the FreeCAD document from the kit's")
            out.append("template, placing and turning parts, the atlas and the dossier AFTER the model has made worthwhile progress: `kit atlas defer`). `kit open` prints the steps.")
            out.append("")
    except Exception:
        pass
    if sess:
        out.append("A GATE SESSION IS OPEN — model of record: %s" % (sess.get("model_of_record") or "NONE YET (the bank is empty - the first body is the next step; PROJECT_START.md; 31bv B1)"))
        out.append("  opened %s   state: %s"
                   % (sess.get("opened"), str(sess.get("state_read"))[:90]))
        open_jobs = [n for n, j in jobs.items() if not j.get("applied")]
        if open_jobs:
            out.append("  %d job(s) not yet applied: %s" % (len(open_jobs),
                                                            ", ".join(sorted(open_jobs)[:8])))
            need_look = [n for n in open_jobs if jobs[n].get("checked")
                         and not jobs[n].get("looked")]
            if need_look:
                out.append("  %d checked but NOT LOOKED AT BY YOU: %s"
                           % (len(need_look), ", ".join(sorted(need_look))))
                out.append("    kit look <job> --says \"...\" --says \"...\" --says \"...\"")
    else:
        out.append("NO GATE SESSION IS OPEN.")
        out.append("  `kit check`, `kit apply` and `kit measure` will refuse until there is one.")
        out.append("  `kit run` and `kit render` work regardless — a WORKER never needs a "
                   "session.")
        out.append("")
        out.append("  First session on this project: read METHOD.md and EDIT_TYPES.md once. Then:")
        out.append("      kit exam        the three questions")
        # G.OPEN_EXAMPLE
        out.append("      " + (G.OPEN_EXAMPLE if "G" in dir() else
                               "kit open --method --edit-types ..."))

    try:
        sys.path.insert(0, HERE)
        import integrity
        out += integrity.banner(project=root)
    except Exception:
        pass

    try:
        sys.path.insert(0, HERE)
        import liveness as _L
        _L.beat(root, "session_start", "ok")
        out += _L.report(root, at_start=True)
    except Exception:
        pass

    hb = os.path.join(root, ".claude", ".guard_alive")
    if os.path.exists(hb):
        age = int((time.time() - os.path.getmtime(hb)) / 60)
        out.append("  guard: last heartbeat %d min ago." % age)
    else:
        out.append("")
        out.append("  the PreToolUse guard has not run yet in this project - it runs from your first tool call (31bx R3 F1: a new project's "
                   "first session). If `kit status` still says NOT RUNNING after one, the hooks are not installed - the line below.")
        _inst = None
        for _c in (os.path.join(os.path.dirname(HERE), "install_lean_hooks.py"),
                   os.path.join(kit, "install_lean_hooks.py"),
                   os.path.join(os.path.dirname(kit), "LEAN_KIT", "install_lean_hooks.py")):
            if os.path.exists(_c):
                _inst = _c
                break
        _inst = _inst or os.path.join(os.path.dirname(HERE), "install_lean_hooks.py")
        out.append("     & \"%s\" \"%s\" --project \"%s\" --status"
                   % (sys.executable, _inst, root))
    try:
        if kit and os.path.exists(os.path.join(kit, "leangate.py")):
            sys.path.insert(0, kit)
            import leangate as _G
            _cl = os.path.join(root, "CLAUDE.md")
            _master = os.path.dirname(kit)
            _dead = _G.dead_paths(_cl, [root, os.path.dirname(_master), _master, os.path.dirname(root)]) if os.path.isfile(_cl) else []
            if _dead:
                out.append("  !! CLAUDE.md names %d path(s) that do not exist - fix the document before obeying it:" % len(_dead))
                for _tok, _ in _dead[:8]:
                    out.append("       %s" % _tok)
                out.append("     (kit paths lists them; a read order goes stale the moment files move)")
    except Exception:
        pass
    out.append("=" * 78)

    print("\n".join(out))
    sys.exit(0)


if __name__ == "__main__":
    main()

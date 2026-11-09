#!/usr/bin/env python3
"""Claude Code PreToolUse guard for a lean-kit CAD project (settings.json wires it to Bash / Write / Edit / Read, and - 31bs K7 - Task / Agent for the wall clock's start stamp).
Reads the hook JSON on stdin; exit 2 with a message on stderr = the tool call is refused.
  Bash : FreeCAD run outside `kit.py run`; `kit.py check|apply|measure` without the orchestrator token `--as-orchestrator`.
  Write/Edit : protected files (model bank, deliverables, FACTS/DESIGN/STATE/METHOD/EDIT_TYPES, the kit) unless `.claude/unlock` exists
         (the orchestrator creates it for its own edits and deletes it after; job cards never mention it).
"""
import sys, json, os, re
for _s_ in (sys.stdout, sys.stderr):      # transcript
    try: _s_.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

def _find_root(start):
    r = start
    while r and not os.path.exists(os.path.join(r, ".claude")) and os.path.dirname(r) != r:
        r = os.path.dirname(r)
    return r


def _heartbeat(root, note=""):
    """Prove this file ran. Never the reason a tool call fails."""
    try:
        with open(os.path.join(root, ".claude", ".guard_alive"), "w", encoding="utf-8") as _fh:
            import time as _t
            _fh.write("%d\n%s\n%s\n" % (int(_t.time()), sys.executable, note))
    except Exception:
        pass


data = {}
if __name__ == "__main__":
    try:
        data = json.load(sys.stdin)
    except Exception as _exc:
        # sys.exit(0)
        _heartbeat(_find_root(os.getcwd()), "UNPARSED stdin: %s" % _exc.__class__.__name__)
        sys.exit(0)
tool = data.get("tool_name", ""); inp = data.get("tool_input", {}) or {}
cwd = data.get("cwd", os.getcwd()); root = _find_root(cwd)
unlock = os.path.exists(os.path.join(root, ".claude", "unlock"))

# METHOD.md
if __name__ == "__main__":
    _heartbeat(root)


def _wallclock_start(root, tool, inp):
    """Stamp the START of this tool call for the wall-clock warden. 2026-09-14.

    THE MEASUREMENT HAS TO BE TAKEN HERE OR IT IS NOT HONEST. `wallclock.py` runs on PostToolUse
    and wants the tool's OWN wall time. Without a start stamp the best it could do is the gap
    since the previous call, which also contains the model's thinking and any wait for the client - so it
    would report a coffee break as a stuck step. A warden that cries wolf gets filtered (P17), and
    a filtered warden is not a warden.

    It is in the guard, rather than a second PreToolUse hook, because the guard already fires on
    every Bash / Write / Edit / Read and already proves itself with the heartbeat two lines up.
    One hook, two facts recorded. It can never refuse anything and never raises.
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import wallclock
        wallclock.stamp_start(root, tool, (inp or {}).get("command")
                              or (inp or {}).get("description")
                              or (inp or {}).get("file_path") or "")
    except Exception:
        pass


def _beat(root, phase="ok", note=""):
    """Join the shared liveness register. 2026-09-14.

    `_heartbeat()` above is UNCHANGED and stays — `kit.py` reads `.guard_alive` and refuses FreeCAD
    on a stale one, and that is the kit's one load-bearing refusal. This is additive: the guard has
    always been the only warden that could prove it ran, and now it proves it in the same place the
    others do, so one report covers all of them.

    Never refuses, never raises. the client, 2026-09-14: "Dead guards report."
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import liveness
        liveness.beat(root, "guard", phase, note)
    except Exception:
        pass


if __name__ == "__main__":
    _wallclock_start(root, tool, inp)
    _beat(root, "ok")


FAILURE_LINE = ("\n  A process failure (this refusal if you think it is wrong, a step that failed, a kit gap) goes in ONE place: the project root's\n"
                "  FAILURES.md, written by   kit failure --what \"...\" --why \"...\" --fix \"...\" --signature \"...\" --caught gate|user|self\n"
                "  (never a new file, never a note in a job folder, never the kit's own files). A kit gap ALSO gets a note for the kit maintainer:\n"
                "  kit inbox --append <claude_code\\<ROUND>\\NOTE_*.md>.   (31az, the client 2026-10-08: \"the agent also does not know where to place failures\")\n")


def refuse(msg):
    sys.stderr.write("GUARD REFUSED: " + msg + FAILURE_LINE); sys.exit(2)
def gates():
    """leangate, or None. The guard must work even if the kit moves — it never blocks on its
    own inability to import something."""
    # does not exist
    for cand in (os.path.join(os.path.dirname(HERE), "kit"),
                 os.path.join(root, "claude_code", "kit"),
                 os.path.join(os.path.dirname(os.path.dirname(HERE)), "kit"),
                 os.path.join(root, "kit")):
        if os.path.exists(os.path.join(cand, "leangate.py")):
            sys.path.insert(0, cand)
            try:
                import leangate
                return leangate
            except Exception:
                return None
    return None


HERE = os.path.dirname(os.path.abspath(__file__))

PROTECTED = ["/model/bank/", "/claude_code/bank/", "/deliverables/", "/FACTS.md", "/DESIGN.md",
             "/STATE.md", "/claude_code/METHOD.md", "/claude_code/EDIT_TYPES.md",
             "/claude_code/CONTRACT.md", "/claude_code/ORCHESTRATOR.md",
             "/claude_code/PROJECT_LAYOUT.md", "/claude_code/kit/"]
PROTECTED_OPEN = ["/deliverables/"]
PROTECTED_OPEN_SUB = ["/review/", "/renders/"]


_REV_DIR = re.compile(r"[\\/]deliverables[\\/](R\d+)[\\/]", re.I)
_REV_NAME = re.compile(r"(?:^|[^A-Za-z0-9])(R\d+)[^A-Za-z0-9]", re.I)


def wrong_revision(path):
    """(rev_of_folder, rev_in_name) when a file is being written into ANOTHER round's folder.

    THE RULE, `PROJECT_LAYOUT.md`: *"A new round makes `Deliverables\\R19\\`; it does not add to the
    previous one."* It was prose, it was ignored by two consecutive rounds, and on 2026-09-14
    `Deliverables\\R18\\` held R19's delivered body, R19's whole before/after survey, R19's piece
    renders AND R20's delivered model. **The cost is not tidiness: "the R18 model" stopped
    identifying a file.**

    This is the cheapest possible enforcement and it needs no new state - no current-revision field,
    no session bookkeeping, nothing to keep in sync. It compares the revision in the FOLDER with the
    revision in the FILENAME, and those are both already there. `R19_MYPART.FCStd` landing in
    `Deliverables\\R18\\model\\` is the entire failure, and it is visible in the path alone.

    Deliberately narrow, because a guard that blocks harmless things gets uninstalled:
      * silent when the filename carries no `R<n>` at all (most renders);
      * silent when the two agree;
      * silent outside `Deliverables\\`.
    A file that genuinely belongs to an earlier round - a correction to R18's own deliverable - is
    the one false positive, and the refusal says how to proceed.
    """
    p = str(path).replace("\\", "/")
    m = _REV_DIR.search(p)
    if not m:
        return None
    folder_rev = m.group(1).upper()
    name = os.path.basename(p)
    got = {r.upper() for r in _REV_NAME.findall("_" + name + "_")}
    if not got or folder_rev in got:
        return None
    return folder_rev, sorted(got)[0]


def refuse_revision(path, folder_rev, name_rev):
    refuse(
        "THAT FILE BELONGS TO %s AND YOU ARE WRITING IT INTO %s.\n"
        "      target : %s\n"
        "\n"
        "  PROJECT_LAYOUT.md: \"A new round makes Deliverables\\<REV>\\; it does not add to the\n"
        "  previous one.\" Two rounds ignored that and Deliverables\\R18\\ ended up holding R19's\n"
        "  delivered body, R19's entire before/after survey and R20's model. After that, \"the R18\n"
        "  model\" no longer names a file - which is the whole point of filing by revision.\n"
        "\n"
        "  Write it to Deliverables\\%s\\ instead. The folder is yours to create.\n"
        "\n"
        "  If this really is a correction to %s's OWN deliverable, the filename is what is wrong:\n"
        "  rename it so the round in the name matches the round in the folder, and the refusal\n"
        "  goes away. Do not work around this by dropping the revision out of the filename."
        % (name_rev, folder_rev, path, name_rev, folder_rev))


def protected_path(path):
    """True when `path` is one the guard protects. CASE-INSENSITIVE: on Windows the folder is
    `Deliverables\\`, and the old `"/deliverables/" in n` never matched it — the protection was
    decorative on the one platform the round runs on (found 2026-09-11 while opening review\\)."""
    n = str(path).replace("\\", "/").lower()
    if not any(k.lower() in n for k in PROTECTED):
        return False
    if any(k in n for k in PROTECTED_OPEN) and any(s in n for s in PROTECTED_OPEN_SUB) \
            and "/bank/" not in n:
        return False
    return True


_GITBASH_DRIVE = re.compile(r"^/([A-Za-z])(/|$)")


def _drive(p):
    """A Git-Bash drive path spelled the Windows way: `/c/CAD/x` -> `C:/CAD/x` (2026-09-25, lessons K1 / R33
    notes 6: `/q/...` INSIDE the project was refused as WRITING OUTSIDE THE PROJECT, because `abspath` on Windows
    puts a rooted path on the current drive). Anything else comes back untouched."""
    s = str(p).strip().strip('"').strip("'")
    m = _GITBASH_DRIVE.match(s)
    if m and os.name == "nt":
        return m.group(1).upper() + ":" + s[2:] if len(s) > 2 else m.group(1).upper() + ":/"
    return s


def _norm(p):
    try:
        return os.path.normcase(os.path.abspath(os.path.expandvars(os.path.expanduser(_drive(p)))))
    except Exception:
        return ""


def _inside(path, folder):
    p, f = _norm(path), _norm(folder)
    return bool(p) and bool(f) and (p == f or p.startswith(f + os.sep))


def _temp_ok(path):
    import tempfile
    for t in (tempfile.gettempdir(), os.environ.get("TEMP"), os.environ.get("TMP"), "/tmp"):
        if t and _inside(path, t):
            return True
    return _memory_ok(path)


def _memory_ok(path):
    """The harness's own memory folder, and ONLY that folder.

    the client asked a project session to store an instruction to memory and the boundary refused it —
    the memory store lives under the user home. The client wants that to work. The allowance is exactly
    `...\\local-agent-mode-sessions\\<...>\\spaces\\<id>\\memory\\` — the `uploads`, `outputs`
    and `.claude` folders that live beside it stay outside the boundary, because they are where
    a session's working files go and nothing there should be reachable from a project.
    """
    p = _norm(path).replace("\\", "/")
    return ("/local-agent-mode-sessions/" in p and "/spaces/" in p and "/memory/" in p
            and "/uploads/" not in p and "/outputs/" not in p)


# none of the
ENFORCEMENT_NAMES = frozenset((
    "guard.py", "handback.py", "session_start.py", "leangate.py", "kit.py",
    "install_lean_hooks.py", "selftest_leangates.py", "settings.json",
    "wallclock.py", "selftest_wallclock.py",
    "stop_guard.py", "selftest_stop_guard.py", "selftest_guard.py", "selftest_cutguard.py",
    "kitlib.py", "kitlib_render.py", "kitlib_burrito.py", "kit_dossier.py", "env.json",
    "selftest_psline.py",
    "integrity.py", "leankit_manifest.json",
    "liveness.py", "selftest_liveness.py",
    "job_tess_cache.py", "job_render_arc.py", "waitlib.py", "cad-reviewer.md",
    "CONTRACT.md", "ORCHESTRATOR.md", "METHOD.md", "EDIT_TYPES.md", "PROJECT_LAYOUT.md",
    "BURRITO_STEPS.md", "PA12_MJF_Rules_EVALUATED.md",
    "cad-worker-haiku.md", "cad-worker-sonnet.md", "cad-worker-opus.md",
    "gates.py", "police.py", "cadroot.py", "install_gates.py", "install_hooks.py",
    "warden_common.py", "warden_shell.py", "warden_write.py", "warden_stop.py",
    "warden_mcp.py", "settings.hooks.json", "config.json",
))
ENFORCEMENT_PREFIX = ("MASTER_",)


def is_enforcement(path):
    """True for a file that ENFORCES, by name, regardless of which folder it sits in."""
    base = os.path.basename(str(path).strip().strip('"').strip("'"))
    if base in ENFORCEMENT_NAMES:
        return True
    return any(base.startswith(p) and base.endswith(".md") for p in ENFORCEMENT_PREFIX)


def refuse_enforcement(path, how):
    refuse(
        "THAT FILE ENFORCES THE RULES — refused, wherever it lives.\n"
        "      target : %s\n"
        "      via    : %s\n"
        "\n"
        "  %s is one of the files that gates this work: the wardens, the kit, the gate module,\n"
        "  the settings that wire them, or a MASTER_*.md. It is refused BY NAME, in any folder,\n"
        "  so a copy of the kit somewhere unexpected is protected too — a second checkout, a\n"
        "  backup, another project's copy.\n"
        "\n"
        "  A session that can edit its own gates has no gates. If one of these genuinely needs\n"
        "  changing, that is a finding and not an edit:\n"
        "      kit failure --what ... --why ... --fix ... --signature ...\n"
        "  and a note for the kit maintainer (kit inbox --append <claude_code\\<ROUND>\\NOTE_*.md>); the kit's maintainer\n"
        "  changes the kit, tests it on a copy and merges it (31bs T7 F8 - the outside-write refusal's route)."
        % (path, how, os.path.basename(str(path))))


# does not exist
# MESSAGE TEXT
SEPARATORS = "&|;\n\r"


def split_segments(cmd):
    """Split a command line into the pieces the shell will run separately.

    Quote-aware on purpose: a separator inside quotes is data, not a separator, so
    `echo "a && b"` stays ONE segment. An unterminated quote yields one segment for the rest of
    the string — the safe direction, because the shell cannot run an unterminated command either.
    """
    segs, buf, quote = [], [], None
    i, n = 0, len(cmd)
    while i < n:
        ch = cmd[i]
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            i += 1
        elif ch in "'\"":
            quote = ch
            buf.append(ch)
            i += 1
        elif ch in SEPARATORS:
            segs.append("".join(buf)); buf = []
            i += 2 if (i + 1 < n and cmd[i + 1] == ch) else 1
        else:
            buf.append(ch)
            i += 1
    segs.append("".join(buf))
    return [s for s in (x.strip() for x in segs) if s]


_QUOTED = re.compile(r"""(?:[rRbBuUfF]{0,2})(?P<q>['"])(?P<s>(?:\\.|(?!(?P=q))[^\\])*)(?P=q)""")


_SP, _OP = "\u2400", "\u2401"


def _squash_quotes(text):
    """Make every quoted span ONE token with no shell characters in it.

    R18 friction log 10:39: `kit failure --what "... /check/_kit_check.py ... A -> B"` was refused
    as WRITING OUTSIDE THE PROJECT — the arrow inside the quoted report read as a redirect and the
    quoted path as its target. Quoted text is data (L246). Spaces inside quotes become a private
    character so the span stays one token (a quoted redirect TARGET, `> "C:\\a b\\c"`, is still
    found whole), and `< > ; | &` inside quotes become another so they can never read as shell.
    `_unsquash()` restores a captured target."""
    out, last = [], 0
    for m in _QUOTED.finditer(text):
        out.append(text[last:m.start()])
        inner = m.group("s").replace(" ", _SP)
        out.append(re.sub(r"[<>;|&]", _OP, inner))
        last = m.end()
    out.append(text[last:])
    return "".join(out)


def _unsquash(t):
    return str(t).replace(_SP, " ").replace(_OP, "")


# does not exist
_SED_EXPR = re.compile(r"^(?:\d+|\$|/[^/]*/)?\s*,?\s*(?:\d+|\$|/[^/]*/)?\s*(?:s|y)([/|#@,~%])(?:\\.|(?!\1).)*\1(?:\\.|(?!\1).)*\1[gIpi0-9]*$"
                       r"|^(?:\d+|\$|/[^/]*/)(?:,(?:\d+|\$|/[^/]*/))?\s*[dp]$|^/[^/]*/[dp]$")


def _looks_path(s):
    s = (s or "").strip()
    if not s:
        return False
    if _SED_EXPR.match(s):
        return False
    if re.match(r"^[A-Za-z]:[\\/]", s) or s.startswith("/"):
        return True
    return bool(re.search(r"[^\\/\s][\\/]+[^\\/\s]", s))


def paths_in(text):
    """Every path-looking string in `text`, with quoted spans kept whole.

    A SPACE INSIDE QUOTES IS PART OF THE PATH. Getting this wrong does not merely mis-name the
    target in a refusal — it invents a DIFFERENT path, judges that, and refuses on the answer.
    """
    found, masked = [], list(text)
    for m in _QUOTED.finditer(text):
        if _looks_path(m.group("s")):
            found.append(m.group("s"))
        for i in range(m.start(), m.end()):
            masked[i] = " "
    for m in re.finditer(r"[A-Za-z]:[\\/][^\s\"\';,)]*|/[^\s\"\';,)]{6,}", "".join(masked)):
        found.append(m.group(0))
    return found


def _truncated(p, folder):
    """True when `p` is only a PREFIX of the project root — a fragment, not a target.

    An unquoted Windows path with a space still arrives here chopped. A fragment is not evidence
    of anything, and refusing on one is how the guard came to name a path that does not exist.
    """
    a, b = _norm(p), _norm(folder)
    return bool(a) and bool(b) and b.startswith(a) and a != b


WRITE_INTENT = re.compile(
    r"open\s*\([^)]*,\s*['\"][rbt+]*[wax][rwxabt+]*['\"]"
    r"|open\s*\([^)]*,\s*['\"][rbt]*\+[rwxabt+]*['\"]" 
    r"|\.write(_text|_bytes)?\s*\(|\bwritelines\b|\bdump\s*\("
    r"|shutil\.(copy\w*|move|rmtree)"
    r"|os\.(remove|unlink|rename|replace|rmdir|makedirs|mkdir)"
    r"|\.(unlink|rename|replace|mkdir|touch|write_text|write_bytes)\s*\("
    r"|fs\.(writeFile|appendFile|unlink|rename)"
    r"|\b(Set-Content|Out-File|Add-Content|New-Item|Remove-Item)\b", re.I)

INTERP = re.compile(r"^(?:.*[\\/])?(?:python\d?(?:\.exe)?|py(?:\.exe)?|node|perl|ruby|pwsh"
                    r"|powershell(?:\.exe)?)$", re.I)


def _tokens(seg):
    """Shell-ish tokens of one segment, quotes removed, quoted spans kept whole."""
    toks = []
    buf, quote = [], None
    for ch in seg:
        if quote:
            if ch == quote:
                quote = None
            else:
                buf.append(ch)
        elif ch in "'\"":
            quote = ch
        elif ch.isspace():
            if buf:
                toks.append("".join(buf)); buf = []
        else:
            buf.append(ch)
    if buf:
        toks.append("".join(buf))
    return toks


_PREFIX_WORDS = frozenset(("&", "sudo", "nohup", "time", "exec", "env", "call", "start", "cmd", "/c",
                           "timeout", "nice", "ionice", "stdbuf", "xargs", "command", "builtin", "setsid",
                           "chrt", "taskset"))


_SHELL_KEYWORDS = frozenset(("do", "then", "else", "elif", "if", "while", "until", "!", "{", "("))


def _strip_prefix(toks):
    """The tokens of a segment with every launcher prefix removed, so toks[0] is the thing run."""
    toks = list(toks)
    while toks:
        t = toks[0].lower()
        if t in _PREFIX_WORDS:
            toks = toks[1:]
            while toks and (toks[0].startswith("-") or re.fullmatch(r"\d+(?:\.\d+)?[smhd]?", toks[0])):
                toks = toks[1:]
            continue
        if t in _SHELL_KEYWORDS:
            toks = toks[1:]
            continue
        _lead = toks[0].lstrip("({!")
        if _lead != toks[0]:
            toks = ([_lead] if _lead else []) + toks[1:]
            continue
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", toks[0]):
            toks = toks[1:]
            continue
        break
    return toks


def _strip_heredocs(cmd):
    """Drop heredoc BODIES: `cat >> log.md << 'EOF' ... EOF`. A body is data, and its lines are
    not commands — split on newlines they would read as one, and a line beginning with the word
    FreeCAD would be judged as a launch."""
    out, lines, i = [], str(cmd).split("\n"), 0
    while i < len(lines):
        m = re.search(r"<<-?\s*['\"]?(\w+)['\"]?", lines[i])
        out.append(lines[i]); i += 1
        if m:
            term = m.group(1)
            while i < len(lines) and lines[i].strip() != term:
                i += 1
            i += 1
    return "\n".join(out)


def freecad_launch(cmd):
    """The token that would RUN FreeCAD in `cmd`, or None.

    JUDGED ON THE TOKEN BEING EXECUTED, NOT ON THE TEXT. R18 friction log, 2026-09-10 09:47: the
    orchestrator's heredoc appending to its own friction log was refused as "FreeCAD runs only
    through kit.py run", because the SENTENCE it was writing contained the word FreeCAD. The
    friction log could not record the friction it existed for. That is ledger L246 again — "a
    remedy call must never be classifiable as the thing it remedies" — and the fix is the one the
    inline-code check already uses: only a segment's first real token is the thing being run.
    `python -c "import FreeCAD"` is caught separately, on the code it runs.
    """
    for seg in split_segments(_strip_heredocs(cmd)):
        if "kit.py" in seg:
            continue
        toks = _strip_prefix(_tokens(seg))
        if not toks:
            continue
        base = os.path.basename(toks[0].strip())
        if re.match(r"^freecad(cmd)?(\.exe)?$", base, re.I):
            return toks[0]
        code = inline_code(seg)
        if code and re.search(r"\bimport\s+FreeCAD\b|\bfrom\s+FreeCAD\b|\bimport\s+Part\b", code):
            return "inline code importing FreeCAD"
    return None


def inline_code(seg):
    """The CODE argument of an interpreter one-liner in `seg`, or None.

    Only when the segment's FIRST token is the interpreter. That single condition is what stops
    the guard refusing a report that merely QUOTES such a command: text inside an argument is
    data, and the thing being run is the first token.
    """
    toks = _strip_prefix(_tokens(seg))
    if not toks or not INTERP.match(toks[0].strip()):
        return None
    for i, t in enumerate(toks[1:], 1):
        if t in ("-c", "-e", "-Command", "-command") and i + 1 < len(toks):
            return toks[i + 1]
    return None


_DEVICES = frozenset(("/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty", "nul", "nul:", "con", "con:"))


def outside_project(path, root, base=None):
    """True when this write target is outside the project and not a temp file.

    A RELATIVE PATH IS RESOLVED AGAINST THE PROJECT, NOT AGAINST THIS PROCESS'S CWD. Found
    2026-09-16 while fixing the `'\\n'` false positive beside it: `open('sub/dir/notes.txt','w')`
    - a write plainly inside the job folder - was refused as *"WRITING OUTSIDE THE PROJECT"*,
    because `_norm` calls `os.path.abspath`, which resolves against the GUARD's working directory.
    The guard is a hook; its cwd is whatever launched it, and the session's own directory arrives
    in the payload instead. So the answer depended on where the hook happened to be started.

    `..\\..\\elsewhere` is still caught: it is joined to the project first and then judged, which
    is what makes the escape visible rather than accidental.
    """
    if not str(path).strip():
        return False
    _p = _drive(str(path).strip().strip('"').strip("'"))
    if _p and not os.path.isabs(_p) and not re.match(r"^[A-Za-z]:", _p) \
            and not _p.startswith(("\\", "/")):
        # resolved against
        path = os.path.join(str(base or root), _p.replace("\\", "/"))
    # WRITING OUTSIDE THE PROJECT
    if str(path).strip().strip("\"'").lower() in _DEVICES:
        return False
    return not _inside(path, root) and not _temp_ok(path)


def refuse_outside(path, root, how):
    refuse(
        "WRITING OUTSIDE THE PROJECT — refused.\n"
        "      target  : %s\n"
        "      project : %s\n"
        "      via     : %s\n"
        "\n"
        "  This session may write inside its own project and nowhere else. Everything outside is\n"
        "  off limits — the master kit in LEAN_KIT, other projects, your\n"
        "  home directory. A session that can edit the kit can edit its own gates, which is the\n"
        "  opposite of the point (the client, 2026-09-09, after a session wrote into LEAN_KIT).\n"
        "\n"
        "  If the KIT needs changing, that is a real and welcome finding - but it is not yours to\n"
        "  apply: there is ONE kit (the client 2026-09-14: never a project copy). Record the defect with\n"
        "      kit failure --what ... --why ... --fix ... --signature ...\n"
        "  and a note for the kit maintainer (kit inbox --append <claude_code\\<ROUND>\\NOTE_*.md>); the setup\n"
        "  session changes the kit, tests it on a copy and merges it." % (path, root, how))

# RAW FUSE
# loose documents
CLAUDE_CODE_OWN = frozenset(n.lower() for n in (
    "STATE_NOW.md", "MEASUREMENTS.md", "KERNEL_LESSONS.md", "INBOX.md", "WALL_CLOCKS.md", "FINE_LOG.md",
    "BURRITO_LESSONS.md", "ATLAS.json", "FROZEN_REGIONS.json", "WHERE_THE_KIT_IS.md", "LEVERS_CENSUS.md",
    "PROCESS_IMPROVEMENTS.md", "FAILURES.md"))
CLAUDE_CODE_FOLDERS = frozenset(("jobs", "bank", "dossier", "_archive", "_to_delete", "scratch"))
ROOT_OWN = frozenset(n.lower() for n in (
    "CLAUDE.md", "PROJECT_FACTS.md", "FACTS.md", "PROCESS_IMPROVEMENTS.md", "SESSION_HANDOFF.md",
    "SESSION_DEFAULTS.md", "FAILURES.md", "STATE.md", "DESIGN.md", ".notcadproject"))
_ROUND_DIR = re.compile(r"^(R\d+|CC_[A-Z0-9_]+|ROUND_[A-Z0-9_]+|[A-Z0-9_]+_ROUND)$")


def overwrite_outside(path, root):
    """31bz (R3 F2): the refusal text for a write to an EXISTING file outside the two places the agent writes (PROJECT_LAYOUT.md: claude_code\\ and
    Deliverables\\<REV>\\review\\ / renders\\; .claude\\ is the kit's), or None. misplaced() judges a NEW file; this judges an overwrite, an edit or an
    append of a file that already stands at the root, in references\\, in a delivery's model folder or in any folder that is not the agent's."""
    try:
        p = os.path.normpath(os.path.abspath(path)); r = os.path.normpath(os.path.abspath(root))
    except Exception:
        return None
    if not p.lower().startswith(r.lower() + os.sep):
        return None
    parts = p[len(r) + 1:].split(os.sep); top = parts[0].lower(); low = parts[-1].lower()
    if top in ("claude_code", ".claude") or low.startswith("_kit_") or low.startswith("kit_run"):
        return None
    if top == "deliverables" and len(parts) >= 4 and parts[2].lower() in ("review", "renders"):
        return None
    return ("AN EXISTING FILE OUTSIDE THE TWO PLACES THE AGENT WRITES: %s\n"
            "  The agent writes in claude_code\\ and Deliverables\\<REV>\\review\\ / renders\\ (PROJECT_LAYOUT.md); the root files, references\\ and a\n"
            "  delivery's model folder are the client's and the kit's own commands':\n"
            "  a ruling the client gave  -> kit ruling --said \"...\"           (PROJECT_FACTS.md, dated)\n"
            "  a process failure         -> kit failure --what ... --why ... --fix ... --signature ...   (FAILURES.md)\n"
            "  friction and its fix      -> kit close --improvement \"...\"      (PROCESS_IMPROVEMENTS.md)\n"
            "  a note for the client     -> kit inbox --append <file in the job folder>\n"
            "  A deliberate edit of the project's own entry files is the orchestrator's unlock, in ONE command:\n"
            "      echo 1 > .claude/unlock && <the edit> && rm .claude/unlock" % p[len(r) + 1:])


def misplaced(path, root):
    """The refusal text for a NEW file that lands where PROJECT_LAYOUT.md says nothing goes, or None.

    Allowed, for a new file:
      claude_code\\jobs\\<JOB>\\...           anything a job produces (scripts, cards, results, pictures)
      claude_code\\<ROUND>\\...              a round's brief, reports, audits
      claude_code\\dossier\\..., bank\\ (the kit), _archive\\
      claude_code\\<one of the named registers>   (the one-of-each set; created once, then appended)
      Deliverables\\<REV>\\...                 pictures, models, reports for the client
      .claude\\_leangates\\...                 the kit's own registers and scratch
      <root>\\<one of the named root files>  (a new project's first CLAUDE.md, PROJECT_FACTS.md ...)
    Refused: any other new file in claude_code\\ root, in the project root, or in a folder of
    claude_code\\ that is not a job, a round, or one of the kit's own.
    """
    try:
        p = os.path.normpath(os.path.abspath(path))
        r = os.path.normpath(os.path.abspath(root))
    except Exception:
        return None
    if not p.lower().startswith(r.lower() + os.sep):
        return None
    rel = p[len(r) + 1:]
    parts = rel.split(os.sep)
    name = parts[-1]
    low = name.lower()
    if low.startswith("_kit_") or low.startswith("kit_run"):
        return None
    if len(parts) == 1:
        if low in ROOT_OWN:
            return None
        return ("A NEW FILE AT THE PROJECT ROOT: %s\n"
                "  Nothing new is written at the root (PROJECT_LAYOUT.md). The root holds the entry point, the\n"
                "  facts, the handoff and the registers - all of which exist and are appended to, never re-created.\n"
                "  A ruling the client gave     -> kit ruling --said \"...\"          (PROJECT_FACTS.md, dated)\n"
                "  a process failure    -> kit failure --what ... --why ... --fix ... --signature ...\n"
                "  friction and its fix -> kit close --improvement \"...\"  (PROCESS_IMPROVEMENTS.md)\n"
                "  a report or a brief  -> claude_code\\<ROUND>\\ ;  a job's file -> claude_code\\jobs\\<JOB>\\" % rel)
    top = parts[0]
    if low.endswith((".py", ".ps1", ".sh", ".bat", ".cmd")) and not (
            top.lower() == "claude_code" and len(parts) >= 4 and parts[1].lower() == "jobs") \
            and top.lower() != ".claude":
        return ("A NEW SCRIPT OUTSIDE A JOB FOLDER: %s\n"
                "  Scripts are not documents: a script belongs in the job it serves, claude_code\\jobs\\<JOB>\\ (any\n"
                "  depth). A script worth keeping is a kit command - say so (kit failure / the inbox), do not\n"
                "  write it beside the kit (ORCHESTRATOR.md section 3). `kit priorart <folder>` lists what a job already has." % rel)
    if top.lower() == "claude_code":
        if len(parts) == 2:
            if low in CLAUDE_CODE_OWN or low.endswith(".log"):
                return None                          # kit close
            return ("A NEW FILE LOOSE IN claude_code\\: %s\n"
                    "  claude_code\\ holds the named registers (STATE_NOW, MEASUREMENTS, KERNEL_LESSONS, INBOX,\n"
                    "  WALL_CLOCKS, FINE_LOG, ATLAS.json ...) and folders. It does not hold notes, handovers, reports,\n"
                    "  scripts or maps (28 loose files were counted there on 2026-09-24; nobody could tell which was current).\n"
                    "  the state that survives a compaction -> kit state --note \"...\"     (STATE_NOW.md, dated)\n"
                    "  a number you measured                -> MEASUREMENTS.md (append) or kit dossier add\n"
                    "  a timing                             -> kit clock add <script> <seconds>\n"
                    "  a note for the auditor / the client          -> kit inbox --append <file in the job folder>\n"
                    "  a script, a card, a probe, a picture -> claude_code\\jobs\\<JOB>\\\n"
                    "  a round's brief, report or audit     -> claude_code\\<ROUND>\\   (e.g. CC_FINISH\\, R32\\)" % rel)
        sub = parts[1]
        if sub.lower() in CLAUDE_CODE_FOLDERS or _ROUND_DIR.match(sub):
            return None
        return ("A NEW FILE IN AN UNNAMED FOLDER OF claude_code\\: %s\n"
                "  Folders under claude_code\\ are: jobs\\<JOB>\\ (a job's files), a round's folder (R<NN>\\, CC_<NAME>\\,\n"
                "  ROUND_<NAME>\\ or <NAME>_ROUND\\ - upper case, digits, underscores), dossier\\, bank\\ (the kit writes it), _archive\\, _to_delete\\ or scratch\\. `%s\\` is none of these.\n"
                "  Put a job's file in claude_code\\jobs\\<JOB>\\ and a round's file in its round folder." % (rel, sub))
    if top.lower() not in ("claude_code", "deliverables", ".claude"):
        return ("A NEW FILE OUTSIDE THE TWO PLACES THE AGENT WRITES: %s\n"
                "  The agent writes in claude_code\\ and in Deliverables\\<REV>\\review\\ or renders\\ (PROJECT_LAYOUT.md); `%s\\` is neither.\n"
                "  A job's file -> claude_code\\jobs\\<JOB>\\ ; a round's file -> claude_code\\<ROUND>\\ ; a picture or a note for the client -> Deliverables\\<REV>\\review\\" % (rel, top))
    return None


RAW_FUSE = re.compile(r"(?<![\w.])(?!K\.|B\.|kitlib\.|kitlib_burrito\.)\w+\.fuse\s*\(")

_PY_WRITE = re.compile(
    r">>?\s*[\"']?[^\s;|&\"']*\.py[\"']?(?:\s|;|\||&|$)"
    r"|>>?\s*\"[^\"]*\.py\"|>>?\s*'[^']*\.py'"
    r"|\btee\s+(?:-a\s+)?[\"']?[^\s;|&\"']*\.py\b"
    r"|\btee\s+(?:-a\s+)?(?:\"[^\"]*\.py\"|'[^']*\.py')"
    r"|\bsed\s+-i[^;|&]*\.py\b"
    r"|\b(?:cp|mv|copy|move|install)\s+[^;|&]*\.py\b"
    r"|\b(?:Set-Content|Out-File|Add-Content)\b[^;|&]*\.py\b"
    r"|open\s*\(\s*[^)]*\.py[^)]*,\s*[\"'](?:w|a|r\+|x)[bt]?[\"']"
    r"|\.write_text\s*\(|Path\s*\([^)]*\.py[^)]*\)\s*\.write",
    re.I)


_OPEN_FOR_WRITE = re.compile(r"open\s*\([^)]*,\s*[\"'](?:w|a|r\+|x)[bt]?[\"']|\.write_text\s*\(|\.write_bytes\s*\(")


def writes_a_py(cmd):
    return bool(_PY_WRITE.search(cmd)) or bool(_OPEN_FOR_WRITE.search(cmd) and re.search(r"\.py\b", cmd))


def shell_content_rules(cmd):
    """The Write-tool content rules, applied to a shell command that writes a .py. Returns None or
    the refusal text. The command text IS the content: a heredoc body or a one-liner's string."""
    m = RAW_FUSE.search(cmd)
    if m:
        return ("THAT COMMAND WRITES A RAW FUSE INTO A PROJECT SCRIPT, AND A SCRIPT THAT FUSES IS A\n"
                "  SCRIPT THAT ROUTES AROUND THE ORBIT GATE.\n"
                "      found  : %s\n"
                "      how    : a shell write (heredoc, redirect, tee, sed -i or an interpreter one-liner)\n"
                "  The Write tool refuses this and so does this door - the rule is on the CONTENT, not on\n"
                "  which tool carried it (the project FAILURES row 54, 2026-09-17).\n"
                "  `K.fuse(...)`, `B.fuse(...)` and `B.union(pieces)` - the kit's own, bookkept and checked\n"
                "  pairwise - are fine and are not what this refuses. Piece-to-piece union: B.union().\n"
                "  Piece-into-body: the chain's S7, which refuses without a recorded orbit verdict.\n"
                "  If you believe this refusal is wrong, that is a finding and not an edit:\n"
                "      kit failure --what ... --why ... --fix ... --signature ...\n"
                "  Do not reword the script to get past it." % m.group(0)[:60])
    return None


_KILL_BY_PATTERN = re.compile(
    r"(?:^|[\s;&|(])(?:pkill\b|killall\b|taskkill(?:\.exe)?\s+(?:[/-]{1,2}\w+\s+)*[/-]{1,2}IM\b"
    r"|Stop-Process\b[^;\n]*-Name\b|(?:Get-Process|Get-CimInstance|Get-WmiObject|gps)\b[^;\n]*\|[^;\n]*Stop-Process\b"
    r"|Where-Object\b[^;\n]*CommandLine\b[^;\n]*\|[^;\n]*(?:Stop-Process|kill)\b)", re.I)


def kill_by_pattern(cmd):
    """A process kill by NAME or COMMAND-LINE PATTERN, or None. On 2026-09-24 a `*_ccthin.py*` filter
    caught an orphaned kernel of the caller's own earlier run and could have killed another agent's
    gate (the agent's handoff, 2.14); on 2026-09-25 `taskkill /F /IM python.exe` killed five processes the
    caller did not own, the FreeCAD MCP servers among them (lessons K3). A kill names a pid -
    `kit collected <name> --kill` ends the recorded tree; `taskkill /T /F /PID <n>` / `kill <n>` end one you know."""
    m = _KILL_BY_PATTERN.search(_squash_quotes(_strip_heredocs(cmd)))
    return m.group(0).strip() if m else None


def bare_background(cmd):
    """A bare `&` ANYWHERE - a shell background outside the harness's own run_in_background - or None.
    Such a process outlives the tool call with no id, no clock and no way to stop it: a review chain started
    this way outlived its shell on 2026-09-24 (2.14), and on 2026-09-25 `( ... &) ;`, `& cd` and a `nohup ... &`
    inside a loop all walked past the old end-of-segment test and four survey processes ran untracked for 11 min
    (lessons K3). `&&`, `||`, `2>&1`, `>&`, `&>` and `|&` are not backgrounds; quoted text is data."""
    text = _squash_quotes(_strip_heredocs(cmd))
    for line in text.split("\n"):
        probe = re.sub(r"&&|\|\||\d?>&\d?|&>|\|&", " ", line)
        for m in re.finditer(r"&", probe):
            i = m.start()
            before = probe[:i].rstrip(); after = probe[i + 1:].lstrip()
            if not before:
                continue
            return (before[-70:] + " &" + (" " + after[:8] if after else "")).strip()
    return None


_LOOP_SLEEP = re.compile(r"\b(while|until|for)\b[^\n]*\bsleep\b|\bsleep\s+(\d+)", re.I)


def foreground_wait(cmd, inp):
    """A wait loop, or a sleep of 60 s or more, in the FOREGROUND, or None (2026-09-25, lessons T1/T2: 244 of 312
    main-session tool-minutes were `until ...; do sleep 15; done` waits sized to the 600 s cap; the client's messages sat
    unanswered for up to 10 min and the client killed tasks; the orchestrator promised to stop and did it again 7 min
    later - "a rule the client has to state twice needs a mechanism"). run_in_background is the harness's own way."""
    if inp.get("run_in_background"):
        return None
    text = _squash_quotes(_strip_heredocs(cmd))
    for m in _LOOP_SLEEP.finditer(text):
        if m.group(1):
            return m.group(0).strip()[:80]
        if m.group(2) and int(m.group(2)) >= 60:
            return m.group(0).strip()[:80]
    return None


def bare_python(cmd):
    """The bare word `python` / `python3` run as a command on Windows, or None (2026-09-25, lessons F3: it is the
    Microsoft Store stub on the client's machine - at least five agents hit it, the handover's own first command among
    them). The interpreter is spelled in full: env.json's `python`."""
    if os.name != "nt":
        return None
    for seg in split_segments(_strip_heredocs(cmd)):
        toks = _strip_prefix(_tokens(seg))
        if toks and toks[0].strip().lower() in ("python", "python3", "python.exe", "python3.exe"):
            return toks[0]
    return None


def _kit_python():
    try:
        with open(os.path.join(os.path.dirname(HERE), "kit", "env.json"), encoding="utf-8") as fh:
            return json.load(fh).get("python") or sys.executable
    except Exception:
        return sys.executable


_INFO_SUBCMDS = frozenset(("exam", "types", "howto", "templates", "paths", "levers", "lessons", "priorart",
                           "tool", "route", "facts", "help", "--help", "-h"))
_FILTER_VERB = re.compile(r"grep|egrep|fgrep|rg|sed|awk|gawk|head|tail|cut|tr|findstr|find|wc|uniq|"
                          r"sort|more|less|select-string|sls|select-object|select|out-string|"
                          r"out-null|where-object|where|\?|foreach-object|foreach|%|measure-object|"
                          r"measure")
_COMPOUND_END = frozenset(("done", "fi", "}", ")", "esac", "};", ");"))




def _kit_info_call(after):
    """True when the kit call whose arguments are `after` is a REFERENCE one whose output cannot hide a refusal
    (2026-09-25, lessons K4: `kit exam | head`, `kit atlas --help | sed` were refused and the whole compound line
    lost each time). `kit status` is deliberately NOT here: its output carries the guard's and the wardens' state
    ("NOT RUNNING", "DEAD"), which a filter for FAIL would hide - refused since 2026-09-16 in every shell's spelling."""
    toks = after.strip().split()
    if not toks:
        return False
    first = toks[0].strip("\"'").lower()
    if first in _INFO_SUBCMDS:
        return True
    return any(t.strip("\"'").lower() in ("--help", "-h") for t in toks[:6])


def _expand_vars(target, assigns):
    """`$D/x` with D assigned in the same command -> the literal; an unresolved `$X` -> None (2026-09-25, lessons
    K2: `> $D\\x`, `$J`, `$OUT`, `$T` were each refused as 'an unnamed folder named after the variable')."""
    def sub(m):
        name = m.group(1) or m.group(2)
        return assigns.get(name, m.group(0))
    t = re.sub(r"\$\{(\w+)\}|\$(\w+)", sub, target)
    return None if "$" in t else t


def _assignments(segs):
    """NAME=value assignments made in the command's own segments (plain, `export`, `set`), first to last."""
    out = {}
    for s in segs:
        for m in re.finditer(r"(?:^|[\s;])(?:export\s+|set\s+)?([A-Za-z_]\w*)=([^\s;|&]+)", s):
            out[m.group(1)] = _unsquash(m.group(2).strip("\"'"))
    return out


def _sed_operands(toks):
    """The FILE operands of `sed -i ... <expr> <files>`: everything after the expression that is not an option
    (2026-09-25, lessons K2 / R31 2.17: the expression itself was read as a new file in claude_code\\s\\)."""
    rest = toks[1:]
    files, expr_seen = [], False
    i = 0
    while i < len(rest):
        t = rest[i]
        if t.startswith("-"):
            if t in ("-e", "--expression", "-f", "--file") and i + 1 < len(rest):
                expr_seen = True; i += 2; continue
            i += 1; continue
        if not expr_seen:
            expr_seen = True; i += 1; continue
        files.append(t); i += 1
    return files


_OPT_WITH_VALUE = frozenset(("-X", "-W", "-m", "-c", "-Q"))


def _script_token(tk):
    """31bq R7b (3): the SCRIPT token of an interpreter call - the first token after the interpreter that is not an option, an option's value skipped
    (`python -X utf8 kit.py ...` had read `utf8` as the script and let the filter through, D2)."""
    i__ = 1
    while i__ < len(tk):
        t__ = tk[i__]
        if t__ in _OPT_WITH_VALUE:
            i__ += 2; continue
        if t__.startswith("-"):
            i__ += 1; continue
        return t__
    return ""


def _corrected_kit(stretch):
    """31bq R7b: THE CORRECTED COMMAND of the no-filter rule - the kit's own stretch (the interpreter and kit.py included), quoted again where a token held a
    space, `--brief` added (31bq B57 (3) / MM). R7b (3): the shell keywords and launcher prefixes before the interpreter dropped (`do python ...` ran as a
    loop body), a `$(... kit.py)` substitution replaced by the quoted literal path (the re-quoting had left `$(cygpath -w "...kit.py)"`), a token with a
    space or a backslash quoted, `--brief` placed before any redirection (`2>&1 --brief` ran, but reads wrong)."""
    _s = str(stretch)
    _s = re.sub(r"\$\(([^()]*?)\)|`([^`]*?)`", lambda m__: next(('"%s"' % x__.strip("\"'")) for x__ in reversed((m__.group(1) or m__.group(2) or "").split()) if x__.strip("\"'").lower().endswith("kit.py")) if any(x__.strip("\"'").lower().endswith("kit.py") for x__ in (m__.group(1) or m__.group(2) or "").split()) else m__.group(0), _s)
    _toks = _strip_prefix(_s.split())
    _toks = [(('"%s"' % _tk_.replace(_SP, " ").strip("\"")) if (_SP in _tk_ or ("\\" in _tk_ and not _tk_.startswith("\""))) else _tk_) for _tk_ in _toks]
    _red = [i__ for i__, _tk_ in enumerate(_toks) if re.match(r"^\d*[<>]", _tk_)]
    if "--brief" not in _toks:
        _toks = _toks[:_red[0]] + ["--brief"] + _toks[_red[0]:] if _red else _toks + ["--brief"]
    _fixed = _unsquash(" ".join(_toks))
    _fixed = re.sub(r'(?<!")((?:[A-Za-z]:[\\/]|\\\\|/[A-Za-z]/)[^"|;&<>]*?\.(?:exe|py|json|brep|md|stl|txt))(?!")', lambda m__: ('"%s"' % m__.group(1)) if " " in m__.group(1) else m__.group(1), _fixed)
    return _fixed.rstrip(")").strip()


def _refuse_filter(verb, segment, fixed, captured=None):
    """31bq R7b: the no-filter rule's refusal, one text for every form it catches (the direct pipe, the captured output, the closed compound)."""
    refuse(
        "do not filter the kit's output through `%s` (the segment: `| %s`).%s\n"
        "  THE CORRECTED COMMAND: %s\n"
        "  A filter cannot tell a banner from a refusal. An orchestrator that did this on\n"
        "  2026-09-09 lost an exit code through the pipe and recorded a REFUSAL AS A PASS.\n"
        "  The whole call is refused, so anything else this line would have done did not\n"
        "  happen - run that part again on its own.\n"
        "\n"
        "  Use the kit's own quiet mode, which suppresses advice and NEVER a refusal:\n"
        "      kit <command> --brief\n"
        "  (`--brief` followed by a filter is still a filter, and is refused the same.)\n"
        "  If --brief still says too much, that is a kit defect worth reporting - \n"
        "      kit failure --what \"...\" --why \"...\" --fix \"...\" --signature \"...\"\n"
        "  - and it is a better outcome than a filter that hides the one line that mattered."
        % (verb, segment, ("\n  The kit's output was CAPTURED into $%s and filtered from there - the same thing one step later (31bq R7b)." % captured) if captured else "", fixed))


# LOOK BEFORE YOU MEASURE
# recorded  kit measure
# MEASURES:
if __name__ == "__main__":
    _lg_note = None
    try:
        sys.path.insert(0, HERE)
        import lookgate as _lookgate
        _lg_msg = _lookgate.check(root, tool, inp, cwd, transcript=data.get("transcript_path"))
        _lg_note = getattr(_lookgate, "USER_NOTE", None)
    except Exception:
        _lg_msg = None
    # wall of shame
    if _lg_note:
        try:
            sys.stdout.write(json.dumps({"systemMessage": _lg_note}) + "\n"); sys.stdout.flush()
        except Exception:
            pass
        sys.stdout = sys.stderr
    if _lg_msg:
        refuse(_lg_msg)

if __name__ == "__main__" and tool == "Bash":
    cmd = inp.get("command", "")
    _fc = freecad_launch(cmd)
    if _fc:
        refuse("FreeCAD runs only through `kit.py run <script>` (METHOD.md 5).\n"
               "      judged on the token being run: %s\n"
               "  (Prose that merely mentions FreeCAD — a log, a report — is not refused.)" % _fc)
    _kp_ = kill_by_pattern(cmd)
    if _kp_:
        refuse("never stop a process by NAME or COMMAND-LINE PATTERN: `%s`.\n"
               "  A pattern reaches every agent's process on this machine - on 2026-09-24 one caught an orphaned\n"
               "  kernel of the caller's own earlier run and could have killed another agent's gate.\n"
               "  End a task you launched by its recorded pid tree:   kit collected <name> --kill\n"
               "  End a pid you know:                                 taskkill /T /F /PID <n>   (or kill <n>)" % _kp_)
    _bg_ = bare_background(cmd)
    if _bg_:
        refuse("never start a process with a bare `&`: `... %s`.\n"
               "  It outlives the tool call with no id, no clock and no way to stop it (`( ... &)`, `nohup ... &` and a\n"
               "  `&` inside a loop are the same thing). Use the tool's own run_in_background (the wall clock registers\n"
               "  it), or `kit burrito <step> --bg` (registered with its pid), or a bounded foreground wait." % _bg_)
    _fw_ = foreground_wait(cmd, inp)
    if _fw_:
        refuse("a WAIT in the foreground: `%s`.\n"
               "  A foreground loop or a long sleep blocks the session: the client's messages sit unanswered until it returns\n"
               "  (up to 10 min at a time on 2026-09-25, 244 of 312 tool-minutes) and the client ends up killing tasks. Waiting\n"
               "  is not a tool call. Launch the work with run_in_background (its completion wakes you), or arm a\n"
               "  Monitor on the verdict line of its log, then END THE TURN with a short status. A bounded wait under\n"
               "  60 s on a step you know is short is fine; a loop is not." % _fw_)
    _bp_ = bare_python(cmd)
    if _bp_:
        refuse("`%s` is not the kit's interpreter (on this machine the bare word may be the Microsoft Store stub, which prints an advert and exits).\n"
               "  Spell the interpreter in full:  %s" % (_bp_, _kit_python()))
    if re.search(r"kit\.py[\"']?\s+(check|apply|measure)\b", cmd) and "--as-orchestrator" not in cmd:
        refuse("`kit.py check/apply/measure` are orchestrator commands; a worker only renders (the client's rule). The orchestrator adds --as-orchestrator.")
    if re.search(r"\brm\s+-rf?\b.*(bank|deliverables)", _squash_quotes(_strip_heredocs(cmd)), re.I):
        refuse("never delete the bank or deliverables.")

    # recorded
    # none of the
    for _seg in split_segments(cmd):
        code = inline_code(_seg)
        if not code or not WRITE_INTENT.search(code):
            continue
        for t in paths_in(code):
            if is_enforcement(t):
                refuse_enforcement(t, "an inline interpreter command (python -c and similar)")
            if _temp_ok(t) or _truncated(t, root):
                continue
            if outside_project(t, root):
                refuse_outside(t, root,
                               "an inline interpreter command (python -c and similar). The path "
                               "is visible in the\n      command line, which is what made this "
                               "catchable — do not try to hide it instead")

    # kit inbox
    _cmdq = _squash_quotes(cmd)
    _kps = []      # --brief 2>&1
    # SHELL VARIABLE
    try:
        for _va in re.finditer(r"(?:^|[;&|\s])(?:export\s+|set\s+|\$)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?!\$\(|`)(\"[^\"]*(?:kit\.py|python[\w.]*|freecadcmd(?:\.exe)?)\"|'[^']*(?:kit\.py|python[\w.]*|freecadcmd(?:\.exe)?)'|\S*(?:kit\.py|python[\w.]*|freecadcmd(?:\.exe)?))(?=\s|;|&|\||$)", _cmdq, flags=re.I):
            _vn, _vv = _va.group(1), _va.group(2).strip("\"'")
            _cmdq = re.sub(r"\$\{%s\}|\$%s\b|%%%s%%|\$env:%s\b" % (_vn, _vn, _vn, _vn), lambda m__, v__=_vv: (m__.group(0) if re.match(r"\s*=(?!=)", m__.string[m__.end():]) else v__), _cmdq)
    except Exception:
        pass
    try:
        for _vm in set(re.findall(r"\$\{(\w+)\}|\$env:(\w+)|%(\w+)%|\$(\w+)", _cmdq)):
            _vn2 = next((x__ for x__ in _vm if x__), ""); _vv2 = os.environ.get(_vn2, "").strip().strip("\"'")
            if _vn2 and _vv2.lower().endswith("kit.py"):
                _cmdq = re.sub(r"\$\{%s\}|\$env:%s\b|%%%s%%|\$%s\b" % (_vn2, _vn2, _vn2, _vn2), lambda m__, v__=_vv2.replace(" ", _SP): v__, _cmdq)
    except Exception:
        pass
    for _m in re.finditer(r"kit\.py\b", _cmdq):
        _pre = re.search(r"=\s*([^;&|=]*)$", _cmdq[:_m.start()])
        if _pre and not any(INTERP.match(_tk_.strip("\"'")) for _tk_ in _pre.group(1).split()): continue
        _stretch = re.split(r";|&&|\|\||\r?\n", _cmdq[:_m.end()])[-1]
        _tk = _strip_prefix(_tokens(_stretch))
        _tk1 = _script_token(_tk)
        if _tk1.startswith(("$(", "`")) and _tk[-1].strip("\"'`)").lower().endswith("kit.py"): _tk1 = _tk[-1].strip("\"'`)")
        if _tk and (INTERP.match(_tk[0].strip("\"'")) and _tk1.strip("\"'").lower().endswith("kit.py")
                    or (_tk[0].strip("\"'").startswith(("$", "%")) and _tk1.strip("\"'").lower().endswith("kit.py"))
                    or _tk[0].strip("\"'").lower().endswith("kit.py")):
            _kps.append(_m)
    for _m in re.finditer(r"(?<![\w./\\-])kit(?=\s)", _cmdq):
        _stretch = re.split(r";|&&|\|\||\r?\n", _cmdq[:_m.end()])[-1]
        _tk = _strip_prefix(_tokens(_stretch))
        if _tk and _tk[0].strip("\"'").lower() == "kit":
            _kps.append(_m)
    for _kp in _kps:
        _after = re.split(r";|&&|\|\||\r?\n", _cmdq[_kp.end():])[0]
        _segs = re.split(r"(?<!\|)\|(?!\|)", _after)
        if _kit_info_call(_segs[0]):
            _segs = _segs[:1]
        for _sg in _segs[1:]:
            _tok = _strip_prefix(_tokens(_sg))
            if not _tok:
                continue
            _verb = os.path.basename(_tok[0].strip("\"'")).lower()
            if _FILTER_VERB.fullmatch(_verb):
                _fixed = _corrected_kit(re.split(r";|&&|\|\||\r?\n", _cmdq[:_kp.end()])[-1] + _segs[0])
                _refuse_filter(_tok[0].strip("\"'"), _unsquash(_sg.strip())[:80], _fixed)
        if not _kit_info_call(_segs[0]):
            for _st3 in re.split(r";|&&|\|\||\r?\n", _cmdq[_kp.end():])[1:]:
                _ps3 = re.split(r"(?<!\|)\|(?!\|)", _st3)
                if len(_ps3) < 2 or _ps3[0].strip().split()[:1] not in ([w__] for w__ in _COMPOUND_END): continue
                for _sg3 in _ps3[1:]:
                    _tok3 = _strip_prefix(_tokens(_sg3))
                    if _tok3 and _FILTER_VERB.fullmatch(os.path.basename(_tok3[0].strip("\"'")).lower()):
                        _refuse_filter(_tok3[0].strip("\"'"), _unsquash(_sg3.strip())[:80], _corrected_kit(re.split(r";|&&|\|\||\r?\n", _cmdq[:_kp.end()])[-1] + _segs[0]))
    try:
        _caps = {}
        for _cm in re.finditer(r"(?:^|[\s;&|({])([A-Za-z_]\w*)=\"?(\$\(|`)", _cmdq):
            _body = _cmdq[_cm.end():]; _close = _body.find(")") if _cm.group(2) == "$(" else _body.find("`")
            _body = _body[:_close] if _close >= 0 else _body
            _btk = _strip_prefix(_tokens(_body))
            if not _btk: continue
            _b1 = next((x__ for x__ in _btk[1:] if not x__.startswith("-")), "")
            _is_kit = ((INTERP.match(_btk[0].strip("\"'")) or _btk[0].strip("\"'").startswith(("$", "%"))) and _b1.strip("\"'").lower().endswith("kit.py")) \
                or _btk[0].strip("\"'").lower() == "kit" or _btk[0].strip("\"'").lower().endswith("kit.py")
            if not _is_kit: continue
            _args = _body.split("kit.py", 1)[-1].strip("\"' ") if "kit.py" in _body.lower() else " ".join(_btk[1:])
            if _kit_info_call(_args): continue
            _caps[_cm.group(1)] = _body.strip()
        for _vn3, _kcall in _caps.items():
            _ref = re.compile(r"\$\{?%s\}?(?!\w)" % re.escape(_vn3))
            for _st in re.split(r";|&&|\|\||\r?\n", _cmdq):
                _ps = re.split(r"(?<!\|)\|(?!\|)", _st)
                for _i3 in range(1, len(_ps)):
                    _tok3 = _strip_prefix(_tokens(_ps[_i3]))
                    if _tok3 and _FILTER_VERB.fullmatch(os.path.basename(_tok3[0].strip("\"'")).lower()) and _ref.search(" ".join(_ps[:_i3])):
                        _refuse_filter(_tok3[0].strip("\"'"), _unsquash(_ps[_i3].strip())[:80], _corrected_kit(_kcall), captured=_vn3)
                _t0 = _strip_prefix(_tokens(_st))
                if _t0 and _FILTER_VERB.fullmatch(os.path.basename(_t0[0].strip("\"'")).lower()) and "<<<" in _st and _ref.search(_st):
                    _refuse_filter(_t0[0].strip("\"'"), _unsquash(_st.strip())[:80], _corrected_kit(_kcall), captured=_vn3)
        for _pm in re.finditer(r"<\(", _cmdq):
            _body = _cmdq[_pm.end():]; _close = _body.find(")"); _body = _body[:_close] if _close >= 0 else _body
            _btk = _strip_prefix(_tokens(_body))
            if not _btk: continue
            _b1 = _script_token(_btk)
            _is_kit = ((INTERP.match(_btk[0].strip("\"'")) or _btk[0].strip("\"'").startswith(("$", "%"))) and _b1.strip("\"'").lower().endswith("kit.py")) \
                or _btk[0].strip("\"'").lower() == "kit" or _btk[0].strip("\"'").lower().endswith("kit.py")
            if not _is_kit: continue
            _args = _body.split("kit.py", 1)[-1].strip("\"' ") if "kit.py" in _body.lower() else " ".join(_btk[1:])
            if _kit_info_call(_args): continue
            _st = re.split(r";|&&|\|\||\r?\n|(?<!\|)\|(?!\|)", _cmdq[:_pm.start()])[-1]
            _t0 = _strip_prefix(_tokens(_st))
            if _t0 and _FILTER_VERB.fullmatch(os.path.basename(_t0[0].strip("\"'")).lower()):
                _refuse_filter(_t0[0].strip("\"'"), _unsquash((_st + "<(" + _body + ")").strip())[:80], _corrected_kit(_body))
    except Exception:
        pass

    _unlock_p = _norm(os.path.join(root, ".claude", "unlock"))
    if not unlock:
        # kit failure --what
        # WRITING OUTSIDE THE PROJECT
        _scan = _strip_heredocs(cmd)
        _segs_w = split_segments(_squash_quotes(_scan))
        _assign = _assignments(_segs_w)
        _cur = _drive(cwd or os.getcwd())
        writes = []
        _unlocked, _unlock_removed = False, False
        for _sg in _segs_w:
            _tk = _strip_prefix(_tokens(_sg))
            if not _tk:
                continue
            _verb = os.path.basename(_tk[0].strip("\"'")).lower()
            if _verb in ("cd", "pushd", "set-location", "sl", "chdir") and len(_tk) > 1:
                _to = _unsquash(_expand_vars(_tk[1], _assign) or _tk[1]).strip("\"'")
                _to = _drive(_to)
                _cur = _to if os.path.isabs(_to) or re.match(r"^[A-Za-z]:", _to) else os.path.join(_cur, _to)
                continue
            _t_here = []
            _t_here += [t for grp in re.findall(r">>?\s*([^\s;|&]+)"
                                                  r"|\b(?:cp|mv|install|copy|move)\s+[^;|&]*?\s([^\s;|&]+)\s*$"
                                                  r"|\btee\s+(?:-a\s+)?([^\s;|&]+)", _sg) for t in grp if t]
            if _verb == "sed" and any(t in ("-i", "--in-place") or t.startswith("-i") for t in _tk[1:]):
                _t_here += _sed_operands(_tk)
            if _verb in ("touch", "new-item", "ni") and len(_tk) > 1:
                _t_here += [t for t in _tk[1:] if not t.startswith("-")]
            for t in _t_here:
                t = _unsquash(t.strip("\"'"))
                _tx = _expand_vars(t, _assign)
                if _tx is None:
                    refuse("a SHELL VARIABLE in a write target: `%s`.\n"
                           "  The guard cannot judge where it lands, and a target it cannot judge is a target it cannot\n"
                           "  allow. Write the literal path, or assign the variable in the same command (`D=<path>; ... > $D/x`)."
                           % t)
                _tabs = _drive(_tx)
                if not (os.path.isabs(_tabs) or re.match(r"^[A-Za-z]:", _tabs)):
                    _tabs = os.path.join(_cur, _tabs)
                if _norm(_tabs) == _unlock_p:
                    if _verb in ("rm", "del", "remove-item", "ri", "erase"):
                        _unlock_removed = True
                    else:
                        _unlocked = True
                    continue
                writes.append((_tx, _cur, _unlocked))
            if _verb in ("rm", "del", "remove-item", "ri", "erase") and any(
                    _norm(_drive(_unsquash(_expand_vars(t, _assign) or t))) == _unlock_p
                    or _norm(os.path.join(_cur, _drive(_unsquash(_expand_vars(t, _assign) or t)))) == _unlock_p
                    for t in _tk[1:] if not t.startswith("-")):
                _unlock_removed = True
        if _unlocked and not _unlock_removed:
            refuse("this command CREATES .claude/unlock and never removes it - the project would be left unguarded.\n"
                   "  The protected write is one line: create the unlock, write, remove it:\n"
                   "      echo 1 > .claude/unlock && cp <draft> <protected path> && rm .claude/unlock")
        for seg in split_segments(_scan):
            _tk = _strip_prefix(_tokens(seg))
            if not _tk or not re.fullmatch(r"rm|rmdir|del|erase|unlink|Remove-Item|mv|move|Move-Item",
                                           os.path.basename(_tk[0]), re.I):
                continue
            for t in _tk[1:]:
                if not t or t.startswith("-"):
                    continue
                if is_enforcement(t):
                    refuse_enforcement(t, "a delete (rm / del / Remove-Item / mv)")
                if _temp_ok(t) or _truncated(t, root):
                    continue
                if outside_project(t, root):
                    refuse_outside(t, root, "a delete (rm / del / Remove-Item)")

        for t, _base, _ul in writes:
            if is_enforcement(t):
                refuse_enforcement(t, "a shell redirection, cp/mv, sed -i or tee")
            _wr = wrong_revision(t)
            if _wr:
                refuse_revision(t, _wr[0], _wr[1])
            if _temp_ok(t) or _truncated(t, root):
                continue
            if outside_project(t, root, base=_base):
                refuse_outside(_drive(t), root, "a shell redirection, cp/mv, sed -i or tee (a relative target is judged"
                               " against the segment's own cwd: %s)" % _base)
            # RESOLVED
            _td = _drive(t)
            _tp = _td if (os.path.isabs(_td) or re.match(r"^[A-Za-z]:", _td)) else os.path.join(_base, _td)
            _tpn = os.path.normpath(_tp)
            if (protected_path(t) or protected_path(_tpn)) and not _ul:
                refuse(
                    "%s is a protected path and this command WRITES to it.\n"
                    "  Workers write only inside their own job folder. The orchestrator creates "
                    "`.claude/unlock`,\n  makes the edit, and DELETES it again - in ONE command, so the third step is\n"
                    "  never forgotten:\n"
                    "      echo 1 > .claude/unlock && cp <draft> <protected path> && rm .claude/unlock\n"
                    "  (relative to the project root or absolute - both are recognised in the same command).\n"
                    "  Reading these files is never blocked." % t)
            _unl = _ul or os.path.exists(os.path.join(root, ".claude", "unlock"))
            if not os.path.exists(_tpn) and t.lower() not in _DEVICES and not _unl:
                _mp = misplaced(_tpn, root)
                if _mp:
                    refuse(_mp)
            elif os.path.exists(_tpn) and t.lower() not in _DEVICES and not _unl:
                _mo = overwrite_outside(_tpn, root)
                if _mo:
                    refuse(_mo)

    # ORIGINAL
    if writes_a_py(cmd):
        _why = shell_content_rules(cmd)
        if _why:
            refuse(_why)

    if re.search(r"kit\.py[\"']?\s+(check|apply|measure)\b", cmd):
        G = gates()
        if G and not G.session(root):
            refuse(
                "no gate session is open in this project.\n"
                "  The orchestrator opens one once per conversation, after reading METHOD.md and\n"
                "  EDIT_TYPES.md (about five minutes together):\n"
                "      kit exam      the three questions\n"
                "      kit open --method --edit-types --state \"<file>: <summary>\" \\\n"
                "          --model \"<model of record>\" --answer overlap=\"...\" \\\n"
                "          --answer measure=\"...\" --answer punch=\"...\"\n"
                "  `kit run` and `kit render` are NOT gated and work right now — if you are a "
                "worker,\n  you have run an orchestrator command by mistake. Stop and report it.")

    m = re.search(r"kit\.py[\"']?\s+apply\b", cmd)
    if m:
        G = gates()
        if G:
            jobs = G._read(G._p(root, G.JOBS), {}) or {}
            unlooked = [n for n, j in jobs.items()
                        if j.get("checked") and not j.get("looked") and not j.get("applied")
                        and not j.get("cancelled")]
            if unlooked:
                refuse(
                    "%d job(s) are checked but YOU have not looked at them: %s\n"
                    "  a recorded lesson: a worker will report HIT against its own render and "
                    "still be wrong\n  about the number — the orchestrator must re-measure every "
                    "hand-back. a recorded lesson,\n  the client: \"Orbit renders are the only reliable "
                    "check. If it were Claude Code it would be gated\n  and required.\" This is "
                    "that gate.\n"
                    "      kit look <job> --says \"...\" --says \"...\" --says \"...\"\n"
                    "  \"Looks right\" is refused: that is what the worker's HIT already said."
                    % (len(unlooked), ", ".join(sorted(unlooked))))

elif __name__ == "__main__" and tool in ("Write", "Edit", "MultiEdit"):
    raw = inp.get("file_path") or ""
    if is_enforcement(raw):
        refuse_enforcement(raw, "the %s tool" % tool)
    if outside_project(raw, root):
        refuse_outside(raw, root, "the %s tool" % tool)
    _wr = wrong_revision(raw)
    if _wr:
        refuse_revision(raw, _wr[0], _wr[1])
    if tool == "Write" and raw and not os.path.exists(raw) and not os.path.exists(os.path.join(root, ".claude", "unlock")):
        _mp = misplaced(raw, root)
        if _mp:
            refuse(_mp)
    if raw and os.path.exists(raw) and not os.path.exists(os.path.join(root, ".claude", "unlock")):
        _mo = overwrite_outside(raw, root)
        if _mo:
            refuse(_mo)

    # recorded
    _body = str(inp.get("content") or inp.get("new_string") or "")

    # PRIOR ART
    if tool == "Write" and re.match(r"job_[\w\-]+\.py$", os.path.basename(raw)) and not os.path.exists(raw):
        _jf = os.path.dirname(raw)
        _sib = [f for f in (os.listdir(_jf) if os.path.isdir(_jf) else []) if f.endswith(".py") and f != os.path.basename(raw)]
        if len(_sib) >= 20 and os.sep + "jobs" + os.sep in os.path.normpath(raw) + os.sep:
            _head = "\n".join(_body.splitlines()[:60]).lower()
            _names_one = any(s.lower() in _head for s in _sib)
            if not ("prior art" in _head or _names_one):
                refuse(
                    "A NEW JOB SCRIPT IN A FOLDER OF %d, AND IT NAMES NONE OF THEM.\n"
                    "      target : %s\n"
                    "  Name the script you are applying, or say why not, BEFORE you write a new one - in the\n"
                    "  header, in the first sixty lines: the file's name, or the words `PRIOR ART`, or `no prior\n"
                    "  art` with the reason. Rebuilding a pipeline that already existed cost a full day on\n"
                    "  2026-09-16 (four standing instructions and a lesson said not to; nothing made the\n"
                    "  session look). The list, ranked with the client's rulings first:\n"
                    "      kit priorart %s\n"
                    "  An Edit to an existing script is not gated by this; a new one is." % (len(_sib), raw, os.path.basename(_jf)))

    _raw_fuse = RAW_FUSE.search(_body)
    if raw.lower().endswith(".py") and _raw_fuse and not is_enforcement(raw):
        refuse(
            "THAT SCRIPT PERFORMS A RAW FUSE ON A SHAPE, AND A SCRIPT THAT FUSES IS A SCRIPT\n"
            "  THAT ROUTES AROUND THE ORBIT GATE.\n"
            "      found  : %s\n"
            "      target : %s\n"
            "  `K.fuse(...)` and `B.fuse(...)` - the kit's own, which are bookkept and gated - are\n"
            "  fine and are not what this refuses.\n"
            "\n"
            "  the client, 2026-09-13: \"you should be gated to never be allowed to bypass full orbit\n"
            "  reviews. I don't care if you think it's wasteful it's absolutely not.\"\n"
            "\n"
            "  On 2026-09-14 an agent wrote a driver that ran build-then-fuse with nothing in\n"
            "  between and called it efficiency. The gate was not bypassed by accident - it was\n"
            "  designed out. This is why the boolean is refused and not just the step.\n"
            "\n"
            "  Fuse through the kit's S7. It refuses without a recorded orbit verdict on the piece,\n"
            "  which is the whole point:\n"
            "      kit review <base> <piece> --mode after --box <card> --shards 6\n"
            "      kit verdict S5 --artefact <piece> --pass --by <you> --saw \"<one line per frame>\"\n"
            "      then run job_s7_replace.py\n"
            "  (the burrito fork still calls lk_review.gate('S5', ...); both write the same\n"
            "  record, and the kit's own is `kitlib.verdict_*`.)\n"
            "\n"
            "  If you believe this refusal is wrong, that is a finding and not an edit:\n"
            "      kit failure --what ... --why ... --fix ... --signature ...\n"
            "  Do not reword the script to get past it."
            % (_raw_fuse.group(0)[:60], raw))

    _cuts = re.search(r"\.cut\s*\(", _body)
    _saves = re.search(r"(?<![\w.])K\.save\s*\(|\.exportBrep\s*\(", _body)
    _is_cut_job = bool(_cuts and _saves)
    if raw.lower().endswith(".py") and _is_cut_job and not is_enforcement(raw):
        _cut_rules = (
            (r"\.BoundBox(?![\w])",
             "MEASURING WITH BoundBox",
             "On NURBS, `Shape.BoundBox` is computed from CONTROL POINTS and over-reports by up to\n"
             "  45 mm on this body (L36). A session once concluded the kernel was returning wrong\n"
             "  results and was one step from filing it; the true extents, taken by tessellating and\n"
             "  taking vertex min/max, were exactly right.\n"
             "  Use it to SELECT a region if you like. Never to MEASURE one.\n"
             "  Instead: `K.tess(shape)` then min/max, or `optimalBoundingBox(True, False)`."),
            (r"\.OuterWire(?![\w])|\.Surface\.value\s*\(|\.makeOffsetShape\s*\(",
             "BUILDING A CUTTER OUT OF THE PART'S OWN FACES",
             "This is the doctrine the client rejected on 2026-09-15. `job_facecut.py` extruded four picked\n"
             "  faces +25 mm and cut: 1 solid, 4,447 faces, valid, 4,739.4 mm3 removed, debris\n"
             "  17 mm3 - every number green. Then the client looked at it: \"does that look right to you?\"\n"
             "  It did not. A hard square step sat a third of the way outboard, exactly on the donor\n"
             "  face's own boundary.\n"
             "  A FACE EDGE IS MODELLING HISTORY, NOT SHAPE. Measured, same job, thin-wall columns\n"
             "  against 94 untouched: 141 with a face-built cutter, 81 with a drawn one.\n"
             "  Instead: DRAW THE CUTTER. `kit howto cutter` - measure the part, fair the table,\n"
             "  sweep, cut once."),
        )
        for _pat, _what, _why in _cut_rules:
            _m = re.search(_pat, _body)
            if not _m:
                continue
            refuse(
                "THAT SCRIPT IS %s.\n"
                "      found  : %s\n"
                "      target : %s\n"
                "\n"
                "  %s\n"
                "\n"
                "  If you believe this refusal is wrong, that is a finding and not an edit:\n"
                "      kit failure --what ... --why ... --fix ... --signature ...\n"
                "  Do not reword the script to get past it."
                % (_what, _m.group(0)[:60], raw, _why))

    p = raw.replace("\\", "/")
    if protected_path(raw) and not unlock:
        refuse("protected path %s - workers write only inside their job folder; the orchestrator creates .claude/unlock first." % p)
if __name__ == "__main__":
    sys.exit(0)

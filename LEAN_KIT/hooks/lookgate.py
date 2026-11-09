r"""lookgate.py - LOOK BEFORE YOU MEASURE (kit 31am, 2026-10-06). guard.py calls check() on every PreToolUse.

the client, 2026-10-06: "For any step, in any process, the agent must be pushed to render review if a measurement is about to be taken
in the next step. It can be as little as 1 image for the generic push but it must be gated to be properly targeted at the
measurement subject in question. If you can gate the overall idea that's great but I don't see a way to since this idea lives
outside a defined process and lives in experiments to find how to make method improvements (like it is doing now to the burrito
process)."

HOW IT IS GATED, inside a process and in an experiment alike - the hook sees every tool call, whoever wrote the script:
  1. Every picture the kit's renderer makes is INDEXED with the 3-D box it frames: kitlib_render.render() (and sk_lib.view) append
     {png, box, view, title} to <project>\\.claude\\frames.jsonl.
  2. Every picture the agent OPENS - the Read tool on a .png / .jpg - is recorded with that box in <project>\\.claude\\looks.jsonl.
  3. A MEASUREMENT is about to run when a Bash command is
       - `kit measure ...`, `kit atlas recreated ...`, or `kit tool <instrument>` whose name says it measures (diag_*, probe, measure,
         dist, dev, census, compare, stat, misfit, check);
       - `kit burrito <script>` / `kit run <script>` whose script declares `# MEASURES:` in its first 60 lines, or whose name says it
         measures (the same words);
       - ANY command that declares `# MEASURES: x0 x1 y0 y1 z0 z1 - <what>` at its end (a shell comment, ignored by the shell).
     It must name its SUBJECT - the box it measures: that `# MEASURES:` box, `--box`, `BOX=` / `MEASURE_BOX=`, or what the command
     itself says (`kit atlas recreated <region>`: the atlas region's box; `kit tool diag_section`: CC_WIN and CC_Y).
  4. It is REFUSED unless a picture whose frame covers the subject - its centre inside the frame, the frame at most LOOK_SCALE x the
     subject's size (or LOOK_MIN_MM across) - was opened in the last LOOK_MAX_MIN minutes. One picture is enough:
         kit tool look_at --job <JOB> --set "BOX=x0 x1 y0 y1 z0 z1" [--set SHAPE=<file>] [--set WHAT="<what will be measured>"]
     makes exactly that picture; open it, then measure - and measure only what the picture points at.
The gate never raises and never refuses on its own error (the guard's rule: a warden that cannot decide stays out of the way).

31aq (2026-10-07, the agent live). the client: "the agent is editing and ALWAYS jumps to measurements before renders. Find a way to punish it ... Make it
announce to me that it's a silly dum dum every time it does that and if you can think of anything else creative to do to help enforce
making decisions on renders over measurements, do that as well." and "It consistently gets to a good result off of renders + changes,
makes a measurement that it arbitrarily decides is a bad measurement with no reasoning as to why, and then undoes correct work. It has
to stop." So, on top of 1-4:
  5. A STRIKE - a measurement with no picture of its subject opened, or a build that changes levers right after a measurement with no
     picture opened since ("a decision on a number") - is written to <project>\claude_code\DUMDUM.md (the wall of shame, numbered) and
     LOCKS the session: every tool but Read / Glob / Grep is refused until the agent has said, to the client, "I'm a silly dum dum" - its next
     message to them opens with the sentence the refusal gives, and it runs that sentence as an `echo` (the guard sees the echo and
     unlocks).
  6. PENANCE: after a strike, a measurement needs MORE pictures of its subject - 1 + the strikes of the last 24 h, up to 4, distinct.
  7. REASONS BEFORE NUMBERS: every measurement carries `# SAW: <what the picture of the subject shows>` and `# WHY: <what this number
     will decide that the picture cannot>` (each a sentence) - no arbitrary measurement, and no measurement without its reason.
  8. WIDER NET: a `python` / `freecadcmd` run of a script whose name says it measures, and inline `python -c` code that measures
     (distToShape, .Volume, .Area, isValid, check(, percentile, np.linalg.norm, MeshDist ...), are measurements too.
  9. kit_rebuild adds the last piece: a layout or piece judged OK from its pictures is not undone on a number (see there).
 10. 31au (the client, 2026-10-07: "update the kit so the wall of shame shows as it is built. Not just at session wrap"): the confession had
     been an `echo` in a tool call, 3-7 s after each strike - the client saw the strikes only when the agent listed them at the end. Now the
     guard SHOWS the client each strike as it lands and each confession as it is said: check() leaves USER_NOTE, the guard prints it as the
     hook's `systemMessage` (Claude Code shows it to the user, on any platform, whether the call is blocked or let through). A strike
     made inside a kit process (an undo, kit_rebuild) is shown at the agent's next tool call.
 11. 31av (the client, 2026-10-07: "How renders get generated needs to be locked down, same idea as how the targeting is"; "only refuse unless it is
     announced in the chat session why it has to be different. A refusal should come with a nudge after the announcement 'Are you sure?'"): a job
     script outside the kit that draws pictures of its own is refused until the agent tells the client why (echo "RENDER EXCEPTION: <script>: <why>",
     shown to them), refused once more with "Are you sure?", then let through and recorded (.claude\\render_exc.json) until the script changes.
 12. 31bq R6 (B51): the announcement is the agent's MESSAGE (31bq), parsed strictly - a line that STARTS with `RENDER EXCEPTION: <script or its
     full path>: <its own reason>`; the refusal's template line is no reason; ONE message announces ONE version of the script (a message is
     taken once, the announcement and the allowance hold for the script's md5); a RENDER EXCEPTION line inside a command lets nothing through.
 13. 31bq R7W (M11): ONE RESOLVER for the render gate and the look gate (_runs): what a command runs, however it is spelled - a cd before it, "$PY",
     a subshell, `bash -c`, a loop body, a heredoc fed to the interpreter, `kit burrito x.py --job J`, a $(...); python CODE in a command (-c, a
     heredoc) that saves a picture is refused with its way out (a job script, then the announcement), code that measures is a measurement; on the
     fail-open route the echo + run sent again after its "Are you sure?" goes ahead.
"""
import os, re, json, time, shlex

LOOK_MAX_MIN = 20.0
LOOK_SCALE = 6.0
LOOK_MIN_MM = 30.0
IMG = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
MEASURE_WORD = re.compile(r"(?:probe|measure|census|misfit|deviation|compare|diag|check)|(?:^|[_\-.])(?:dist|distance|dev|stat|stats|cmp)(?:$|[_\-.\d])", re.I)
MEASURE_TOOL = re.compile(r"^(?:diag_|probe|measure|dist|dev|census|compare|cmp|stat|misfit|check)", re.I)
NUM = r"[-+]?\d+(?:\.\d+)?"
DECL = re.compile(r"#\s*MEASURES?\s*:\s*((?:%s[\s,;]+){5}%s)\s*(?:[-:]\s*(.*))?" % (NUM, NUM), re.I)
DUMDUM = re.compile(r"silly\s*dum\s*-?\s*dum", re.I)
FORGIVE = re.compile(r"please\s+forgive\s+mr\.?\s*silly\s*dum\s*-?\s*dum", re.I)
ADMIT = re.compile(r"i\s*[\'\u2019]?\s*m\s+a\s+silly\s*dum\s*-?\s*dum", re.I)


def pretties(n):
    """one 'pretty' per strike: 'Pretty', 'Pretty pretty', ..."""
    try: n = max(1, int(n or 1))
    except (TypeError, ValueError): n = 1
    return " ".join(["Pretty"] + ["pretty"] * (n - 1))


def apology(n, deed):
    """the sentence owed to the client for strike n"""
    return "I'm a silly dum dum - I'm so very sorry! %s please forgive Mr. Silly Dum Dum: %s." % (pretties(n), deed)


def said_ok(text, n=None):
    """the apology is in the text: the admission "I'm a silly dum dum" AND 'please forgive Mr. Silly Dum Dum' with exactly n 'pretty' (n None: the phrases alone)"""
    s = str(text or "")
    if not FORGIVE.search(s) or not ADMIT.search(s): return False
    return True if n is None else len(re.findall(r"\bpretty\b", s, flags=re.I)) == int(n)
USER_NOTE = None
NOTE_MAX = 420
SAW = re.compile(r"#\s*SAW\s*:\s*([^#\n]+)", re.I)
WHY = re.compile(r"#\s*WHY\s*:\s*([^#\n]+)", re.I)
REASON_MIN = 30
PENANCE_MAX = 4
STRIKE_HOURS = 24.0
PY_EXE = re.compile(r"^(?:.*[\\/])?(?:python(?:3(?:\.\d+)?)?|py|pythonw|freecadcmd)(?:\.exe)?$", re.I)
MEASURE_CODE = re.compile(r"distToShape|\.Volume\b|\.Area\b|\.isValid\(|\.check\(|getSelfIntersections|np\.linalg\.norm|linalg\.norm|percentile|MeshDist|deviation|\.query\(", re.I)
BUILD_SUBS = ("rebuild", "burrito", "run", "mesh", "union")
NOT_BUILD_STEPS = ("judge", "second", "record", "--help", "-h", "skin-look", "review", "review-body", "skin-mirror")
FREE_SETS = {"STL", "BODY", "RUN", "PIECE", "WHAT", "STEP", "SHAPE", "TAG", "LK_TAG", "OUT", "OUT_DIR", "SUFFIX", "LOOK_PREFIX", "BOP_OK", "SHELVED_OK", "NEW", "ORIG", "WINDOW", "REGION", "WALLS",
             "TRIAL", "LOOK_MODE", "SHOW_NUMBERS", "LOOK_HIDDEN",
             "WIRE_PICS", "WIRE_LABELS", "CORNER_PICS", "FEAT_LABELS",  # skin-wires  skin-features  FEATURES
             "PICS", "CARRY_MM",
             "PIC_W", "NET_PICS", "DESIGN", "FILLET_LINES", "FILLET_RERUN", "FIL_DBG", "LOOK_ANG", "LOOK_TOL_MAX", "LOOK_VIS", "SLOW_X", "SLOW_MIN_S", "FIL_TAPER", "PIC_DEV", "PIC_ANG"}


def _norm(p):
    try:
        return os.path.normcase(os.path.abspath(p)).replace("\\", "/")
    except Exception:
        return str(p)


def _records_root(root):
    """31bq B53: the shared records' root - the project, or KIT_SCRATCH_ROOT (a kit-maintenance scratch test's own folder)"""
    r = (os.environ.get("KIT_SCRATCH_ROOT") or "").strip()
    if r:
        try: os.makedirs(os.path.join(r, ".claude"), exist_ok=True)
        except OSError: pass
        return r
    return root


def _claude(root):
    d = os.path.join(_records_root(root), ".claude")
    return d if os.path.isdir(d) else None


def _tail(path, n=4000):
    """the newest n records of a jsonl (a byte window of 600 x n); n=0 reads the WHOLE file - 31bs K30 (2026-11-03): frames.jsonl is read whole - its 600 x 4000 = 2.4 MB window was
    shorter than the project's 4.3 MB / 8091-line file, so a picture rendered before the window's start had box None at open time and read 'no frame record' at the next
    measurement: a false refusal and a strike (kitlib_render trims the file itself, so whole is bounded)"""
    try:
        with open(path, "rb") as fh:
            if n:
                fh.seek(0, 2); size = fh.tell(); fh.seek(max(0, size - 600 * n))
            lines = fh.read().decode("utf-8", "replace").splitlines()
        out = []
        for ln in (lines[-n:] if n else lines):
            try: out.append(json.loads(ln))
            except ValueError: pass
        return out
    except OSError:
        return []


def _box6(vals):
    try:
        v = [float(x) for x in vals]
    except (TypeError, ValueError):
        return None
    if len(v) != 6: return None
    x0, x1, y0, y1, z0, z1 = v
    return [min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1)]


def frame_box(root, png):
    """the box a picture frames, from the renderer's index (newest entry for that file), or None"""
    c = _claude(root)
    if not c: return None
    key = _norm(png)
    for r in reversed(_tail(os.path.join(c, "frames.jsonl"), 0)):
        if r.get("png_n") == key or _norm(r.get("png", "")) == key:
            return r.get("box")
    return None


def frame_defective(root, png):
    """31bn: the renderer stamped this picture RENDER DEFECTIVE (cracks between faces, facets too coarse) - its newest record says so; such a
    picture is no evidence: not a look for a measurement, not a picture that overturns a verdict"""
    c = _claude(root)
    if not c: return False
    key = _norm(png)
    for r in reversed(_tail(os.path.join(c, "frames.jsonl"), 0)):
        if r.get("png_n") == key or _norm(r.get("png", "")) == key:
            return bool(r.get("defective"))
    return False


def record_open(root, png):
    """the agent opened a picture: remember when, and what it frames"""
    c = _claude(root)
    if not c: return
    rec = {"png": png, "png_n": _norm(png), "box": frame_box(root, png), "opened": time.time(), "when": time.strftime("%Y-%m-%d %H:%M:%S"), "defective": frame_defective(root, png)}
    try:
        p = os.path.join(c, "looks.jsonl")
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        if os.path.getsize(p) > 2_000_000:
            keep = _tail(p, 2000)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("".join(json.dumps(r) + "\n" for r in keep))
    except OSError:
        pass


def _diag(b):
    return ((b[1] - b[0]) ** 2 + (b[3] - b[2]) ** 2 + (b[5] - b[4]) ** 2) ** 0.5


def targeted(look_box, subject):
    """the picture is AT the subject: the subject's centre inside the frame (grown 1 mm), and the frame not far bigger than it"""
    if not look_box or not subject: return False
    c = [(subject[0] + subject[1]) / 2, (subject[2] + subject[3]) / 2, (subject[4] + subject[5]) / 2]
    inside = all(look_box[2 * k] - 1.0 <= c[k] <= look_box[2 * k + 1] + 1.0 for k in range(3))
    return inside and _diag(look_box) <= max(LOOK_SCALE * _diag(subject), LOOK_MIN_MM)


def _segments(cmd):
    """the command's pieces, split on && || ; | and newlines (quotes kept together)"""
    out, cur, q = [], "", None
    i = 0
    while i < len(cmd):
        ch = cmd[i]
        if q:
            cur += ch
            if ch == q: q = None
        elif ch in "\"'":
            q = ch; cur += ch
        elif cmd.startswith("&&", i) or cmd.startswith("||", i):
            out.append(cur); cur = ""; i += 1
        elif ch in ";|\n":
            out.append(cur); cur = ""
        else:
            cur += ch
        i += 1
    out.append(cur)
    return [s.strip() for s in out if s.strip()]


def _toks(seg):
    try:
        t = shlex.split(seg, posix=False)
    except ValueError:
        t = seg.split()
    return [x.strip("\"'") for x in t]


def _sets(toks):
    """the --set KEY=VALUE pairs of a kit command"""
    d = {}
    for i, t in enumerate(toks):
        if t == "--set" and i + 1 < len(toks) and "=" in toks[i + 1]:
            k, v = toks[i + 1].split("=", 1); d[k.strip()] = v.strip().strip("\"'")
    return d


def _declared(text):
    """a `# MEASURES: x0 x1 y0 y1 z0 z1 - <what>` declaration in a command or a script's header: (box, what) or (None, None)"""
    m = DECL.search(text or "")
    if not m: return None, None
    return _box6(re.split(r"[\s,;]+", m.group(1).strip())), (m.group(2) or "").strip()


def _atlas_box(root, region):
    try:
        a = json.load(open(os.path.join(root, "claude_code", "ATLAS.json"), encoding="utf-8"))
        r = (a.get("regions") or {}).get(region) or {}
        return _box6(r.get("box"))
    except (OSError, ValueError, AttributeError):
        return None


def _script_path(tok, cwd, root):
    for base in (cwd, os.path.join(root, "claude_code"), root):
        p = tok if os.path.isabs(tok) else os.path.join(base, tok)
        if os.path.isfile(p): return p
    return None


_LEAD_WORDS = frozenset(("do", "then", "else", "elif", "if", "while", "until", "!", "{", "(", "time", "exec", "command", "builtin", "nohup", "env", "&", "call", "start", "sudo"))
_ARG_WORDS = frozenset(("timeout", "nice", "ionice", "stdbuf", "xargs", "setsid", "taskset", "chrt"))
_PY_VALUE_OPTS = frozenset(("-X", "-W", "-Q"))
_SHELL_EXE = re.compile(r"^(?:.*[\\/])?(?:bash|sh|dash|zsh)(?:\.exe)?$", re.I)
_KIT_TOK = re.compile(r"(?:^|[\\/])kit\.py$|^kit(?:\.cmd|\.bat)?$", re.I)


def _winpath(p):
    """an MSYS path (/c/CAD/...) as Windows reads it (C:/CAD/...); anything else as it is"""
    m = re.match(r"^/([A-Za-z])(/.*)?$", str(p or ""))
    return (m.group(1).upper() + ":" + (m.group(2) or "/")) if (m and os.name == "nt") else p


def _heredocs(cmd):
    """(the command with every heredoc BODY taken out and its `<<TERM` replaced by the marker `<<@HD<n>`, {n: body}) - quote-aware: a `<<` inside a
    quoted string (a `1 << 3` in -c code) is no heredoc, and a here-string `<<<` is left alone"""
    s = str(cmd or ""); n = len(s); out = []; bodies = {}; i = 0; q = None
    while i < n:
        ch = s[i]
        if q:
            out.append(ch); q = None if ch == q else q; i += 1; continue
        if ch in "\"'":
            q = ch; out.append(ch); i += 1; continue
        if s.startswith("<<", i) and not s.startswith("<<<", i):
            m = re.match(r"<<(-?)\s*(['\"]?)([A-Za-z_]\w*)\2", s[i:])
            nl = s.find("\n", i + m.end()) if m else -1
            if m and nl >= 0:
                k = len(bodies); out.append("<<@HD%d" % k); out.append(s[i + m.end():nl]); out.append("\n")
                j = nl + 1; body = []
                while j < n:
                    e = s.find("\n", j); e = n if e < 0 else e; ln = s[j:e]; j = e + 1
                    if (ln.lstrip("\t") if m.group(1) else ln).strip() == m.group(3): break
                    body.append(ln)
                bodies[k] = "\n".join(body); i = j; continue
        out.append(ch); i += 1
    return "".join(out), bodies


def _strip_comments(text):
    """a shell comment - a `#` that starts a word, outside quotes - taken off its line (the old resolver cut at any `#`, inside quotes too)"""
    s = str(text or ""); out = []; q = None; i = 0; n = len(s)
    while i < n:
        ch = s[i]
        if q:
            out.append(ch); q = None if ch == q else q; i += 1; continue
        if ch in "\"'":
            q = ch; out.append(ch); i += 1; continue
        if ch == "#" and (i == 0 or s[i - 1] in " \t\n;&|("):
            e = s.find("\n", i); i = n if e < 0 else e; continue
        out.append(ch); i += 1
    return "".join(out)


def _subst(seg):
    """(the text with every $(...) / `...` / <(...) replaced by the marker @SUBST<k>, [their insides]) - a run inside a command substitution is a
    run too; done on the WHOLE command before it is split (a `&&` inside a $(...) is no separator of the outer command)"""
    s = str(seg or ""); n = len(s); out = []; inner = []; i = 0; sq = dq = False
    while i < n:
        ch = s[i]
        if ch == "'" and not dq: sq = not sq; out.append(ch); i += 1; continue
        if ch == '"' and not sq: dq = not dq; out.append(ch); i += 1; continue
        if not sq and (s.startswith("$(", i) or (not dq and (s.startswith("<(", i) or s.startswith(">(", i)))):
            d = 0; j = i + 1
            while j < n:
                if s[j] == "(": d += 1
                elif s[j] == ")":
                    d -= 1
                    if d == 0: break
                j += 1
            out.append("@SUBST%d" % len(inner)); inner.append(s[i + 2:j]); i = j + 1; continue
        if ch == "`" and not sq:
            j = s.find("`", i + 1); j = n if j < 0 else j
            out.append("@SUBST%d" % len(inner)); inner.append(s[i + 1:j]); i = j + 1; continue
        out.append(ch); i += 1
    return "".join(out), inner


def _assign(seg):
    """(NAME, value) when a piece of the command is a bare assignment (NAME=value, export NAME=value) - a $(...) / `...` value is the last path in
    it that ends in .py / .exe (K=$(cygpath -w ".../kit.py") names kit.py), else None; None when the piece is no assignment (VAR=x cmd is a prefix)"""
    m = re.match(r"^\s*(?:export\s+|declare\s+|local\s+|readonly\s+)?([A-Za-z_]\w*)=(.*)$", str(seg or ""), re.S)
    if not m: return None
    v = m.group(2).strip()
    if v.startswith("$(") or v.startswith("`"):
        c = re.findall(r"([^\s\"'()`]+\.(?:py|exe))", v)
        return (m.group(1), c[-1] if c else None)
    if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]: return (m.group(1), v[1:-1])
    if re.search(r"\s", v): return None
    return (m.group(1), v)


def _expand(seg, vars_):
    """$NAME / ${NAME} replaced by the value the command assigned (else the hook's own environment's); an unknown one is left as it is"""
    def sub(m):
        v = vars_.get(m.group(1) or m.group(2))
        if v is None: v = os.environ.get(m.group(1) or m.group(2))
        return v if v is not None else m.group(0)
    return re.sub(r"\$\{([A-Za-z_]\w*)\}|\$([A-Za-z_]\w*)", sub, str(seg or ""))


def _lead(t):
    """(the tokens with the shell's keywords, a grouping paren or brace, launcher words and prefix assignments off the front, a `(` opened here)"""
    t = list(t); opened = False
    while t:
        x = t[0]; xl = x.lower()
        if len(x) > 1 and x[0] in "({!" and x not in ("{}",):
            opened = opened or x[0] == "("; t[0] = x[1:]; continue
        if xl in _LEAD_WORDS:
            opened = opened or x == "("; t = t[1:]; continue
        if xl in _ARG_WORDS:
            t = t[1:]
            while t and (t[0].startswith("-") or re.fullmatch(r"\d+(?:\.\d+)?[smhd]?", t[0])): t = t[1:]
            continue
        if re.fullmatch(r"[A-Za-z_]\w*=.*", x):
            t = t[1:]; continue
        break
    return t, opened


def _resolve(tok, base, cwd, root):
    """the file a script token names - an MSYS or Windows absolute path, else beside the shell's folder (after any cd), the session's, claude_code, the root"""
    tok = _winpath(str(tok or "").strip("\"'"))
    if not tok: return None
    if os.path.isabs(tok): return tok if os.path.isfile(tok) else None
    for b in (base, cwd, os.path.join(root, "claude_code"), root):
        if b:
            p = os.path.join(b, tok)
            if os.path.isfile(p): return p
    return None


def _kit_run(rest, base, cwd, root):
    """a kit call: {kind kit, sub, rest, script} - `burrito <x.py> --job J` takes jobs\\J\\x.py as the kit does (no --job: the newest job holding
    WINNING_ENV.json, the kit's own rule), `run <x.py>` the file beside the shell's folder"""
    if not rest: return None
    sub = rest[0].lower(); args = list(rest[1:]); sp = None
    if sub in ("burrito", "run") and args and not args[0].startswith("-"):
        tok = args[0]
        if sub == "burrito" and tok.lower().endswith(".py"):
            jd = os.path.join(root, "claude_code", "jobs")
            job = args[args.index("--job") + 1] if "--job" in args and args.index("--job") + 1 < len(args) else None
            try:
                if job:
                    c = os.path.join(jd, job, os.path.basename(tok)); sp = c if os.path.isfile(c) else None
                else:
                    cands = [os.path.join(jd, d) for d in os.listdir(jd) if os.path.isfile(os.path.join(jd, d, "WINNING_ENV.json"))]
                    if cands:
                        c = os.path.join(max(cands, key=os.path.getmtime), os.path.basename(tok)); sp = c if os.path.isfile(c) else None
            except OSError:
                sp = None
        sp = sp or _resolve(tok, base, cwd, root)
    return {"kind": "kit", "sub": sub, "rest": args, "script": sp, "base": base}


def _piece(t, segx, base, cwd, root, bodies):
    """what one piece runs: a kit call, a python script, python code (-c / a heredoc), a module, or None"""
    t0 = t[0]
    if re.fullmatch(r"kit(?:\.cmd|\.bat)?", os.path.basename(t0), re.I): return _kit_run(t[1:], base, cwd, root)
    unres = t0.startswith("$") and len(t) > 1 and not PY_EXE.match(t0)
    interp = bool(PY_EXE.match(t0)) or unres
    if not interp:
        ki = next((i for i, x in enumerate(t) if _KIT_TOK.search(x)), None)
        return _kit_run(t[ki + 1:], base, cwd, root) if ki is not None else None
    i = 1
    while i < len(t):
        a = t[i]
        if a == "-c": return {"kind": "code", "code": " ".join(t[i + 1:]), "how": "python -c", "base": base}
        if a == "-m": return {"kind": "module", "module": t[i + 1] if i + 1 < len(t) else "", "base": base}
        if a in _PY_VALUE_OPTS: i += 2; continue
        if a == "-": break
        if a.startswith("-") or re.match(r"^\d*[<>]", a) or a.startswith("@SUBST"): i += 1; continue
        if _KIT_TOK.search(a): return _kit_run(t[i + 1:], base, cwd, root)
        if unres and not a.lower().endswith(".py"): return None
        return {"kind": "py", "tok": a, "script": _resolve(a, base, cwd, root), "args": t[i + 1:], "base": base}
    hd = [int(x) for x in re.findall(r"<<@HD(\d+)", segx)]
    if hd: return {"kind": "code", "code": "\n".join(bodies.get(k, "") for k in hd), "how": "a heredoc fed to the interpreter", "base": base}
    m = re.search(r"(?:^|\s)<\s*([^\s<>|&;]+)", segx)
    if m: return {"kind": "py", "tok": m.group(1), "script": _resolve(m.group(1), base, cwd, root), "args": [], "base": base}
    return None


def _runs(cmd, cwd, root, _depth=0, _vars=None, _bodies=None):
    """[{kind: 'kit' | 'py' | 'code' | 'module', ...}] - what the command runs, piece by piece (the block's head says how it reads one)"""
    vars_ = _vars if _vars is not None else {}
    if _bodies is None: text, bodies = _heredocs(cmd)
    else: text, bodies = str(cmd or ""), _bodies
    out = []; base = cwd or os.getcwd(); stack = []; scope = []
    text, substs = _subst(_strip_comments(text))
    for seg in _segments(text):
        try:
            for k in re.findall(r"@SUBST(\d+)", seg):
                if _depth < 3 and int(k) < len(substs): out.extend(_runs(substs[int(k)], base, root, _depth + 1, vars_, bodies))
            a = _assign(re.sub(r"@SUBST(\d+)", lambda m_: "$(" + (substs[int(m_.group(1))] if int(m_.group(1)) < len(substs) else "") + ")", seg))
            if a:
                if a[1] is not None: vars_[a[0]] = a[1]
                continue
            segx = _expand(seg, vars_)
            t, opened = _lead(_toks(segx))
            if opened: scope.append((base, list(stack)))
            closes = 0
            while t and t[-1].endswith(")") and t[-1].count(")") > t[-1].count("("):
                k_ = t[-1].count(")") - t[-1].count("(")
                while k_ > 0 and t[-1].endswith(")"): t[-1] = t[-1][:-1]; k_ -= 1; closes += 1
                if t[-1]: break
                t = t[:-1]
            if t:
                t0 = os.path.basename(t[0]).lower()
                if t0 in ("cd", "pushd"):
                    d = next((x for x in t[1:] if x and not x.startswith("-") and x.lower() != "/d"), None)
                    if d and d != "-":
                        if t0 == "pushd": stack.append(base)
                        d = os.path.expanduser(_winpath(d)); base = d if os.path.isabs(d) else os.path.join(base, d)
                elif t0 == "popd":
                    if stack: base = stack.pop()
                elif _SHELL_EXE.match(t[0]) and "-c" in t[1:]:
                    k = t.index("-c", 1)
                    if k + 1 < len(t) and _depth < 3: out.extend(_runs(t[k + 1], base, root, _depth + 1, vars_, bodies))
                elif _SHELL_EXE.match(t[0]) and re.search(r"<<@HD\d+", segx):
                    if _depth < 3:
                        for k in re.findall(r"<<@HD(\d+)", segx): out.extend(_runs(bodies.get(int(k), ""), base, root, _depth + 1, dict(vars_)))
                else:
                    r = _piece(t, segx, base, cwd, root, bodies)
                    if r: out.append(r)
            for _ in range(closes):
                if scope: base, stack = scope.pop()
        except Exception:
            continue
    return out


def _head_decl(sp):
    """(box, what) a script declares in its first 60 lines (`# MEASURES: ...`), or (None, None)"""
    if not sp: return None, None
    try:
        return _declared("".join(open(sp, encoding="utf-8", errors="replace").readlines()[:60]))
    except OSError:
        return None, None


def _code_only(code, keep_strings=False):
    """a python snippet with its comments (and, unless keep_strings, the text of its string literals) blanked - a test of what the code DOES: an
    editor that rewrites a script's source carries `.save(` / `.Volume` inside its strings and does neither (R7W: one of the corpus's 51 inline picture
    snippets, and most of its 'measuring' heredocs, were such editors)"""
    s = str(code or "")
    try:
        import io, tokenize
        starts = [0]
        for ln in s.splitlines(True): starts.append(starts[-1] + len(ln))
        out = list(s)
        kinds = {tokenize.COMMENT} if keep_strings else {tokenize.COMMENT, tokenize.STRING, getattr(tokenize, "FSTRING_MIDDLE", -1)}
        for tk in tokenize.generate_tokens(io.StringIO(s).readline):
            if tk.type in kinds:
                a_ = starts[tk.start[0] - 1] + tk.start[1]; b_ = starts[tk.end[0] - 1] + tk.end[1]
                for i in range(a_, min(b_, len(out))):
                    if out[i] != "\n": out[i] = " "
        return "".join(out)
    except Exception:
        t = "\n".join(l.split("#", 1)[0] for l in s.splitlines())
        if not keep_strings:
            t = re.sub(r"'{3}[\s\S]*?'{3}|\"{3}[\s\S]*?\"{3}|'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"", "''", t)
        return t


def _code_draws(code):
    """python code that saves a picture: a .png / .jpg named (in its strings) and a save / render CALL in its code (not in a string)"""
    return bool(PIC_EXT.search(_code_only(code, keep_strings=True)) and PIC_SAVE.search(re.sub(r"\b(?:np|numpy|torch|joblib)\.save\(", " ", _code_only(code))))


def _code_measures(code):
    """python code that measures (MEASURE_CODE) in its code, not in a string"""
    return bool(MEASURE_CODE.search(_code_only(code)))


def measurement(cmd, cwd, root):
    """None, or {what, box (None when the command does not say), how}. 31bq R7W (M11): through _runs() - a probe run after a cd, by `kit burrito
    <probe> --job J`, by "$PY", in a loop body or a heredoc is a measurement, and its header's box is read from the file the run really takes"""
    box, what = _declared(cmd)
    if box is not None:
        return {"what": what or "a declared measurement", "box": box, "how": "the command's # MEASURES: line"}
    for r in _runs(cmd, cwd, root):
        k = r.get("kind")
        if k == "code":
            if _code_measures(r.get("code")):
                return {"what": "inline python that measures" + (" (%s)" % r["how"] if r.get("how") and r["how"] != "python -c" else ""), "box": None, "how": "its code"}
            continue
        if k == "py":
            sp = r.get("script"); nm = os.path.basename(sp or r.get("tok") or "")
            hb, hw = _head_decl(sp)
            if hb is not None:
                return {"what": "%s (%s)" % (nm, hw or "declared"), "box": hb, "how": "the script's # MEASURES: header"}
            if nm.lower().endswith(".py") and MEASURE_WORD.search(os.path.splitext(nm)[0]):
                return {"what": nm, "box": None, "how": "its name"}
            continue
        if k != "kit": continue
        sub = r.get("sub") or ""; rest = r.get("rest") or []
        sets = _sets(rest)
        def from_args():
            b = None
            if "--box" in rest:
                i = rest.index("--box"); cand = rest[i + 1:i + 7]
                b = _box6(re.split(r"[\s,]+", cand[0])) if cand and "," in cand[0] else _box6(cand)
            for k_ in ("BOX", "MEASURE_BOX"):
                if b is None and sets.get(k_): b = _box6(re.split(r"[\s,;]+", sets[k_].strip()))
            return b
        if sub == "measure" and not ("--help" in rest or "-h" in rest):
            return {"what": "kit measure %s" % " ".join(rest[:3]), "box": from_args(), "how": "kit measure"}
        if sub == "atlas" and rest[:1] == ["recreated"]:
            reg = rest[1] if len(rest) > 1 and not rest[1].startswith("-") else None
            return {"what": "kit atlas recreated %s" % (reg or ""), "box": from_args() or (_atlas_box(root, reg) if reg else None), "how": "the atlas region's box"}
        if sub == "tool" and rest:
            nm = os.path.basename(rest[0]); nm = nm[:-3] if nm.endswith(".py") else nm; nm = nm.lstrip("_")
            if nm == "look_at" or rest[0].startswith("-") or not MEASURE_TOOL.match(nm) or "--help" in rest: continue
            b = from_args()
            if b is None and sets.get("CC_WIN") and sets.get("CC_Y"):
                try:
                    w = [float(x) for x in re.split(r"[\s,]+", sets["CC_WIN"].strip())]; ys = [float(x) for x in re.split(r"[\s,]+", sets["CC_Y"].strip())]
                    b = [w[0], w[1], min(ys) - 1.0, max(ys) + 1.0, w[2], w[3]]
                except (ValueError, IndexError):
                    b = None
            return {"what": "kit tool %s" % nm, "box": b, "how": "the instrument's levers"}
        if sub in ("burrito", "run") and rest:
            sp = r.get("script")
            if not sp: continue
            b, w = _head_decl(sp)
            if b is not None:
                return {"what": "%s (%s)" % (os.path.basename(sp), w or "declared"), "box": b, "how": "the script's # MEASURES: header"}
            if MEASURE_WORD.search(os.path.splitext(os.path.basename(sp))[0]):
                return {"what": os.path.basename(sp), "box": from_args(), "how": "its name"}
    return None


def _dd_path(root):
    c = _claude(root)
    return os.path.join(c, "dumdum.json") if c else None


def _dd_load(root):
    p = _dd_path(root)
    try:
        st = json.load(open(p, encoding="utf-8")) if p else {}
    except (OSError, ValueError):
        st = {}
    st.setdefault("strikes", []); st.setdefault("confessions", []); st.setdefault("owed", None)
    return st


def _dd_save(root, st):
    p = _dd_path(root)
    if not p: return False
    try:
        with open(p + ".tmp", "w", encoding="utf-8") as fh:
            json.dump(st, fh, indent=1)
        os.replace(p + ".tmp", p)
        return True
    except OSError:
        return False


def recent_strikes(st, now=None):
    now = now or time.time()
    return sum(1 for x in st.get("strikes", []) if now - float(x.get("t", 0)) <= STRIKE_HOURS * 3600)


def strike(root, kind, what, cmd):
    """a strike: recorded, written to the wall of shame, and the session locked until the agent says it to the client. Returns the sentence."""
    st = _dd_load(root)
    n = len(st["strikes"]) + 1
    what_ = re.split(r"\s+#\s*(?:SAW|WHY)\b", str(what or ""), 1)[0].strip() or what
    deed = {"measure": "I went for a measurement (%s) before looking at a render of it" % what_,
            "decide": "I changed a lever (%s) on a number, with no render looked at since the measurement" % what,
            "undo": "I tried to undo work the renders said was good (%s), on a number" % what}.get(kind, what)
    sentence = apology(n, deed)
    st["strikes"].append({"n": n, "t": time.time(), "when": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": kind, "what": what, "cmd": (cmd or "")[:400]})
    st["owed"] = {"n": n, "sentence": sentence, "since": time.time()}
    if not _dd_save(root, st):
        return None
    try:
        wp = os.path.join(_records_root(root), "claude_code", "DUMDUM.md"); os.makedirs(os.path.dirname(wp), exist_ok=True)
        new = not os.path.isfile(wp)
        with open(wp, "a", encoding="utf-8") as fh:
            if new:
                fh.write("# DUMDUM - THE WALL OF SHAME (the client, 2026-10-07: the agent \"ALWAYS jumps to measurements before renders\"; it says \"I'm a silly dum dum\" to them\n"
                         "# every time). Written by the guard (hooks\\lookgate.py); one row per strike; the report pastes it.\n\n| # | when | what | the command |\n|---|---|---|---|\n")
            fh.write("| %d | %s | %s | `%s` |\n" % (n, time.strftime("%Y-%m-%d %H:%M:%S"), deed.replace("|", "/"), (cmd or "").replace("|", "/").replace("\n", " ")[:160]))
    except OSError:
        pass
    return sentence


def _shown(st, n):
    return n in (st.get("shown") or [])


def announce(root, st, n, text):
    """31au: the line the client sees now (the guard prints USER_NOTE as the hook's systemMessage); a strike is announced once, a confession always"""
    global USER_NOTE
    t = " ".join(str(text).split())
    if len(t) > NOTE_MAX: t = t[:NOTE_MAX - 3] + "..."
    USER_NOTE = t
    if n is not None and not _shown(st, n):
        st.setdefault("shown", []).append(n); _dd_save(root, st)
    return t


def owed_message(st, how="transcript"):
    o = st.get("owed") or {}
    if how == "transcript":
        said = ("  2. The guard reads the session transcript and unlocks when that sentence is in YOUR MESSAGE TEXT (31az, the client 2026-10-08: \"The kit\n"
                "     is not live reporting that it's a dum dum\" - an echo in a tool call is NOT said to them and does not unlock). WHEN the desktop app\n"
                "     writes your message text to the transcript is not in your hands (31bc saw it only at the turn's end; R7W measured mid-turn text in the\n"
                "     file before the next tool call, not that the hook can read it then): write the sentence as the first line of your reply\n"
                "     and END THE TURN - the Stop hook reads it, lifts the lock and HANDS THE TURN BACK TO YOU (31bi): you continue the work at once,\n"
                "     without waiting for the client (the client reads the sentence in the chat).\n")
    else:
        said = ("  2. then run exactly:   echo \"%s\"\n"
                "     (no transcript is readable here, so the guard takes the echo; the strike stays on the wall of shame, claude_code\\DUMDUM.md)\n"
                % o.get("sentence", "").replace('"', "'"))
    return ("SILLY DUM DUM - STRIKE %s IS OWED TO the client. Nothing runs (Read / Glob / Grep only) until you have said it:\n"
            "  1. your NEXT message to the client opens with, word for word (one 'pretty' per strike - the count is the strike number):\n"
            "        %s\n"
            "%s"
            "  3. then RENDER the subject, open the picture, and decide from the picture. the client, 2026-10-06: \"render reviews are how you understand\n"
            "     the model\"; \"Measurements are BAD. NO MEASURE. only if it is absolutely required\"." % (o.get("n", "?"), o.get("sentence", ""), said))


# silly dum dum
# transcript
# transcript
TRANSCRIPT_MAX = 512 * 1024 * 1024     # transcript


def _iso_t(ts):
    """an ISO-8601 timestamp (Claude Code writes UTC with a Z) -> epoch seconds, or 0"""
    try:
        import datetime as _dt
        ts = str(ts).strip()
        if ts.endswith("Z"): ts = ts[:-1] + "+00:00"
        return _dt.datetime.fromisoformat(ts).timestamp()
    except Exception:
        return 0.0


def _lines_backwards(path, cap=TRANSCRIPT_MAX, chunk=1 << 20):
    """the file's lines from the last to the first, read in chunks from the end (a transcript holds 400 KB picture lines)"""
    with open(path, "rb") as fh:
        fh.seek(0, 2); pos = fh.tell(); read = 0; buf = b""
        while pos > 0 and read < cap:
            step = min(chunk, pos); pos -= step; fh.seek(pos); data = fh.read(step); read += step
            buf = data + buf
            parts = buf.split(b"\n"); buf = parts[0]
            for ln in reversed(parts[1:]):
                if ln.strip(): yield ln
        if buf.strip() and read < cap: yield buf


def said_in_transcript(transcript, since_t, phrase="silly dum dum", n=None):
    """True when an assistant TEXT block written after since_t holds the apology with (when given) exactly n 'pretty' (31bh);
    False when the transcript is readable and holds no such text; None when it is not readable. Walks the JSONL backwards from its end,
    line by line, until a line older than the strike (31bc; a fixed tail missed a confession behind two picture Reads)."""
    if not transcript: return None
    try:
        if not os.path.isfile(transcript): return None
        for raw in _lines_backwards(transcript):
            if not raw.lstrip().startswith(b"{"): continue
            if b"timestamp" not in raw.lower(): continue
            try:
                d = json.loads(raw.decode("utf-8", errors="replace"))
            except ValueError:
                continue
            t = _iso_t(d.get("timestamp"))
            if t and since_t and t < float(since_t): return False
            if d.get("type") != "assistant": continue
            m = d.get("message") or {}; c = m.get("content")
            texts = [c] if isinstance(c, str) else [b.get("text", "") for b in (c or []) if isinstance(b, dict) and b.get("type") == "text"]
            if any(said_ok(x, n) for x in texts): return True
        return False
    except OSError:
        return None


def announced_in_transcript(transcript, hours=4.0):
    """31bq B51: RENDER EXCEPTION lines the agent wrote in its MESSAGE to the client (an echo's systemMessage never reached them - 31az measured it). Returns
    [(script, why, key)] from the assistant text blocks of the last `hours`, newest first - 31bq R6 (B51 (3) / (e) / (c)): each line STARTS with the
    announcement and carries a reason of its own (exc_lines - the refusal's template line is no reason), a subagent's text (isSidechain) is not the
    agent's message, and `key` names the message (its uuid, else its timestamp and text) so that one message announces one version of a script;
    [] when none; None when no transcript is readable."""
    if not transcript: return None
    try:
        if not os.path.isfile(transcript): return None
        since = time.time() - hours * 3600.0; out = []
        for raw in _lines_backwards(transcript):
            if not raw.lstrip().startswith(b"{") or b"timestamp" not in raw.lower(): continue
            try: d = json.loads(raw.decode("utf-8", errors="replace"))
            except ValueError: continue
            t_ = _iso_t(d.get("timestamp"))
            if t_ and t_ < since: break
            if d.get("type") != "assistant" or d.get("isSidechain"): continue
            m = d.get("message") or {}; c = m.get("content")
            texts = [c] if isinstance(c, str) else [b.get("text", "") for b in (c or []) if isinstance(b, dict) and b.get("type") == "text"]
            for x in texts:
                for s_, w_ in exc_lines(x):
                    out.append((s_, w_, str(d.get("uuid") or "%s|%s" % (d.get("timestamp"), __import__("hashlib").md5(str(x).encode("utf-8", "replace")).hexdigest()[:12]))))
        return out
    except OSError:
        return None


def _record_measure(root, m):
    c = _claude(root)
    if not c: return
    try:
        with open(os.path.join(c, "measures.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"t": time.time(), "when": time.strftime("%Y-%m-%d %H:%M:%S"), "what": m.get("what"), "box": m.get("box")}) + "\n")
    except OSError:
        pass


def last_measure(root):
    c = _claude(root)
    r = _tail(os.path.join(c, "measures.jsonl"), 50) if c else []
    return r[-1] if r else None


def last_look_t(root):
    c = _claude(root)
    r = _tail(os.path.join(c, "looks.jsonl"), 50) if c else []
    return max([float(x.get("opened", 0)) for x in r] + [0.0])


# job script
# RENDER EXCEPTION
PIC_SAVE = re.compile(r"\.save\(|savefig\(|saveImage\(|\brender\(|\bview\(\s*R\s*,|render_transparent\(|imwrite\(", re.I)
PIC_EXT = re.compile(r"\.(?:png|jpe?g)\b", re.I)
# ANNOUNCE
# transcript  RENDER EXCEPTION
EXC_WHY_MIN = 12
_EXC_HEAD = r"RENDER\s+EXCEPTION\s*[*_]*\s*:\s*[*_]*\s*"
_EXC_PATH = r"(?P<q>[`\"']?)(?P<path>(?:[A-Za-z]:[\\/])?[^\n`\"<>|?*]*?[^\s`\"'<>|?*:\\/]\.py)(?P=q)[*_]*\s*:\s*"
EXC_SAY = re.compile(r"^[ \t>*_+\-]*(?:\d{1,3}[.)][ \t]+)?" + _EXC_HEAD + _EXC_PATH + r"(?P<why>[^\n]*)$", re.I | re.M)
EXC_CMD = re.compile(_EXC_HEAD + _EXC_PATH + r"(?P<why>(?:(?!&&|\|\|)[^;|\"\n])*)", re.I)
EXC_HOURS = 4.0
ANNOUNCE_MIN = 60.0
_KIT = os.path.normcase(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


_EXC_PLACEHOLDER = "why the kit's pictures cannot show it"


def _exc_norm(w):
    return re.sub(r"[\s<>*_`'\"‘’.,:;-]+", " ", str(w or "")).strip().lower()


def _exc_why(w):
    """31bq R6: the reason of an announcement, or None. 31bq R7W (P-controls 8): the refusal's PLACEHOLDER is no reason, with or without its brackets
    (R6 refused any `<...>` span - an own reason like 'lines <0.1 mm wide at >2000 px' - and took the placeholder text once its brackets were dropped);
    an own reason written inside the template's brackets is read without them; a reason under EXC_WHY_MIN characters is none"""
    w = re.sub(r"[*_`\s]+$", "", str(w or "")).strip().strip("\"'").strip()
    if len(w) >= 2 and w[0] == "<" and w[-1] == ">" and "<" not in w[1:-1] and ">" not in w[1:-1]: w = w[1:-1].strip()
    if len(w) < EXC_WHY_MIN or _exc_norm(w) == _exc_norm(_EXC_PLACEHOLDER): return None
    return w[:300]



def exc_lines(text):
    """31bq R6: [(script path or name, why)] of the announcements in a message - each at the start of its own line, with a reason of its own"""
    out = []
    for ma in EXC_SAY.finditer(str(text or "")):
        w = _exc_why(ma.group("why"))
        if w: out.append((ma.group("path").strip(), w))
    return out


def exc_in_cmd(cmd):
    """31bq R6: (script, why) of a RENDER EXCEPTION line inside a command (an echo, a comment), or None"""
    for ma in EXC_CMD.finditer(str(cmd or "")):
        w = _exc_why(ma.group("why"))
        if w: return (ma.group("path").strip(), w)
    return None


def _note(text):
    """what the client sees for this tool call (the guard prints USER_NOTE as the hook's systemMessage)"""
    global USER_NOTE
    t = " ".join(str(text).split())
    USER_NOTE = t if len(t) <= NOTE_MAX else t[:NOTE_MAX - 3] + "..."


def _in_kit(p):
    try:
        return os.path.normcase(os.path.abspath(p)).startswith(_KIT + os.sep)
    except Exception:
        return False


def _draws(path):
    """the script writes pictures of its own: a .png / .jpg named in its code and a call that saves or renders one (comments left out)"""
    try:
        txt = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return False
    code = "\n".join(l.split("#", 1)[0] for l in txt.splitlines())
    return bool(PIC_EXT.search(code) and PIC_SAVE.search(code))


def picture_script(cmd, cwd, root):
    """the job script (outside the kit) a command runs that draws pictures of its own, or None. 31bq R7W (M11): through _runs() - R6's `cd` was one
    form of nine; `"$PY" x.py` (the agent's real 13eb:189), a subshell, `bash -c`, a loop body, an MSYS path, `kit burrito x.py --job J` from another folder
    and a `$(...)` reach the gate too"""
    for r in _runs(cmd, cwd, root):
        sp = r.get("script") if (r.get("kind") == "py" or (r.get("kind") == "kit" and r.get("sub") in ("burrito", "run"))) else None
        if sp and not _in_kit(sp) and _draws(sp):
            return sp
    return None


def inline_picture(cmd, cwd, root):
    """31bq R7W (M11): python CODE the command runs (-c, a heredoc fed to the interpreter) that saves a picture of its own - the run record, or None"""
    for r in _runs(cmd, cwd, root):
        if r.get("kind") == "code" and _code_draws(r.get("code")):
            return r
    return None



def _rx_path(root):
    c = _claude(root)
    return os.path.join(c, "render_exc.json") if c else None


def _rx_load(root):
    p = _rx_path(root)
    try:
        st = json.load(open(p, encoding="utf-8")) if p else {}
    except (OSError, ValueError):
        st = {}
    for k in ("announced", "asked", "allowed"): st.setdefault(k, {})
    st.setdefault("log", [])
    return st


def _rx_save(root, st):
    p = _rx_path(root)
    if not p: return False
    try:
        with open(p + ".tmp", "w", encoding="utf-8") as fh:
            json.dump(st, fh, indent=1)
        os.replace(p + ".tmp", p)
        return True
    except OSError:
        return False


def _md5f(p):
    import hashlib
    try:
        with open(p, "rb") as fh:
            return hashlib.md5(fh.read()).hexdigest()
    except OSError:
        return None


def render_gate(root, ps):
    """None = let the script run; a string = the refusal (no announcement yet, or the "Are you sure?"). 31bq R6 (B51 (c)): an announcement and an
    allowance hold for ONE version of the script - the md5 it had when the announcement was taken (the echo route: when it was first asked about);
    a changed script is announced again (round 4's G: the same old message had re-allowed a changed script, nothing said)"""
    if not _claude(root):
        return None                       # recorded
    rx = _rx_load(root); nm = os.path.basename(ps).lower(); now = time.time(); md = _md5f(ps); base = os.path.basename(ps)
    al = rx["allowed"].get(nm)
    if al and al.get("md5") == md and now - float(al.get("t", 0)) <= EXC_HOURS * 3600:
        return None
    an = rx["announced"].get(nm); was_ = ""
    if an and an.get("md5") and an.get("md5") != md:
        was_ = an.get("when", ""); rx["announced"].pop(nm, None); rx["asked"].pop(nm, None); _rx_save(root, rx); an = None
    elif al and al.get("md5") != md:
        was_ = al.get("when", "")
    if not an or now - float(an.get("t", 0)) > ANNOUNCE_MIN * 60:
        return ("YOUR OWN PICTURES (31av; the client 2026-10-07: \"How renders get generated needs to be locked down, same idea as how the targeting is\"):\n"
                "  %s draws pictures of its own. A picture comes from the kit - a step's own frames, `kit tool look_at` (a targeted look at a box on any\n"
                "  shape: --set SHAPE / VIEW / VIEWS), `kit review` - so what you look at is the model, not a drawing artefact (the render study: the\n"
                "  shredded colours and ragged surfaces of job-script pictures were not the model). If this picture truly has to be different, tell the client\n"
                "  why first - IN YOUR MESSAGE TO the client (the client reads the message; an echo's note does not reach them - 31bq B51), a line of its own that STARTS:\n"
                "      RENDER EXCEPTION: %s: <why the kit's pictures cannot show it>\n"
                "  (your own reason in place of the <...> - the template line is no reason; ONE message announces ONE version of the script, so a\n"
                "  changed script is announced again; an `echo` of the line is NOT read when your message can be), then run it again - in the same\n"
                "  turn (31bq R7W measured the FILE's write order: in the agent's transcripts a mid-turn message's text precedes the next tool call, 420 of 420 lines;\n"
                "  the gate's live read of one was measured in a subagent's session only). If the gate still sees no announcement, write the line once more -\n"
                "  the desktop app now and then records a message only as a summary of it (two of six probes, 2026-10-22).%s"
                % (base, base, ("\n  %s HAS CHANGED since its announcement / allowance of %s - that one held for the script as it was then." % (base, was_)) if was_ else ""))
    ask = rx["asked"].get(nm)
    if not ask or float(ask.get("t", 0)) < float(an.get("t", 0)):
        rx["asked"][nm] = {"t": now, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "md5": md}
        if not an.get("md5"): an["md5"] = md
        if not _rx_save(root, rx): return None
        return ("ARE YOU SURE? (31av) You told the client: \"%s\".\n"
                "  The kit's pictures - look_at with BOX / SHAPE / VIEW / VIEWS, a step's frames with PICS=full - show the model as it is; a picture of your\n"
                "  own is the exception the client asked to be told about. Run it once more to go ahead: it is recorded, and it holds for %s until the script\n"
                "  changes (%g h at most)." % (an.get("why", ""), base, EXC_HOURS))
    rx["allowed"][nm] = {"md5": md, "t": now, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "why": an.get("why", "")}
    rx["announced"].pop(nm, None); rx["asked"].pop(nm, None)
    rx["log"].append({"script": nm, "why": an.get("why", ""), "when": time.strftime("%Y-%m-%d %H:%M:%S"), "md5": md, "how": an.get("how", "an echo")})
    _rx_save(root, rx)
    _note("RENDER EXCEPTION confirmed by the agent: %s - %s" % (base, an.get("why", "")))
    return None


def _lever_build(cmd):
    """the kit build a command runs with the levers it changes - (what, [levers]) or None"""
    for seg in _segments(re.sub(r"#[^\n]*", "", cmd)):
        t = _toks(seg)
        ki = next((i for i, x in enumerate(t) if x.lower().endswith("kit.py") or x.lower() in ("kit", "kit.cmd", "kit.bat")), None)
        if ki is None or ki + 1 >= len(t): continue
        sub = t[ki + 1].lower(); rest = t[ki + 2:]
        if sub not in BUILD_SUBS or not rest or rest[0].lower() in NOT_BUILD_STEPS or "--plan" in rest or "--help" in rest: continue
        lv = sorted(k for k in _sets(rest) if k not in FREE_SETS)
        if lv:
            return ("kit %s %s" % (sub, rest[0]), lv)
    return None


def check(root, tool, inp, cwd=None, transcript=None):
    """None = let the call through; a string = the refusal (the guard prints it and exits 2). USER_NOTE: what the client is shown (31au).
    transcript: the hook input's transcript_path (31az - the confession is read from the agent's own message)."""
    global USER_NOTE
    USER_NOTE = None
    try:
        if tool == "Read":
            fp = (inp or {}).get("file_path") or ""
            if fp.lower().endswith(IMG):
                record_open(root, fp)
            return None
        cmd = ((inp or {}).get("command") or "") if tool == "Bash" else ""
        st = _dd_load(root)
        if st.get("owed"):
            o_ = st["owed"]
            # transcript
            # transcript
            said = said_in_transcript(transcript, o_.get("since"), n=o_.get("n"))
            by_echo = said is None and tool == "Bash" and said_ok(cmd, o_.get("n"))
            if said or by_echo:
                st["confessions"].append({"n": o_.get("n"), "t": time.time(), "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                                          "said": ("in the message to the client (transcript)" if said else cmd[:300])})
                st["owed"] = None; _dd_save(root, st)
                announce(root, st, o_.get("n"), "%s   [the wall of shame, claude_code\\DUMDUM.md: %d strike(s) in %dh]" % (o_.get("sentence", ""), recent_strikes(st), STRIKE_HOURS))
                if by_echo: return None
            else:
                if not _shown(st, o_.get("n")):
                    announce(root, st, o_.get("n"), "WALL OF SHAME +1 - %s   [the agent is locked until it says it to you]" % o_.get("sentence", ""))
                if tool in ("Glob", "Grep", "LS"):
                    return None
                if tool == "Bash" and DUMDUM.search(cmd) and said is False:
                    return ("NOT SAID TO the client: an echo is a tool call - the client does not read it. " + owed_message(st, "transcript"))
                return owed_message(st, "transcript" if said is not None else "echo")
        elif tool == "Bash" and DUMDUM.search(cmd):
            return None
        if tool != "Bash":
            return None
        # RENDER EXCEPTION
        # RENDER EXCEPTION  transcript
        # RENDER EXCEPTION
        # kit measure  RENDER EXCEPTION
        ma = exc_in_cmd(cmd)
        if ma:
            try: _tr_ok = announced_in_transcript(transcript) is not None      # transcript
            except Exception: _tr_ok = False
            if _tr_ok:
                _note("RENDER EXCEPTION by `echo` IGNORED (%s): the client reads your MESSAGE - write the line there, at the start of a line (31bq B51)" % ma[0])
            else:
                rx = _rx_load(root); nm_ = os.path.basename(ma[0]).lower(); an0_ = rx["announced"].get(nm_)
                if an0_ and an0_.get("why") == ma[1] and time.time() - float(an0_.get("t", 0)) <= ANNOUNCE_MIN * 60:
                    pass
                else:
                    rx["announced"][nm_] = {"why": ma[1], "t": time.time(), "when": time.strftime("%Y-%m-%d %H:%M:%S"), "how": "an echo (no transcript readable)"}
                    rx["asked"].pop(nm_, None); _rx_save(root, rx)
                _note("RENDER EXCEPTION (the agent wants its own pictures): %s - %s" % (ma[0], ma[1]))
        ps = picture_script(cmd, cwd or os.getcwd(), root)
        if ps:
            try:
                _nm = os.path.basename(ps).lower()
                _mine = [a_ for a_ in (announced_in_transcript(transcript) or []) if os.path.basename(a_[0]).lower() == _nm]
                if _mine:
                    rx = _rx_load(root); _md = _md5f(ps); _now = time.time()
                    _used = rx.setdefault("used", {}).setdefault(_nm, [])
                    _new = [a_ for a_ in _mine if a_[2] not in _used]
                    if _new:
                        _al_ = rx["allowed"].get(_nm); _live_ = bool(_al_ and _al_.get("md5") == _md and _now - float(_al_.get("t", 0)) <= EXC_HOURS * 3600)
                        _an_ = rx["announced"].get(_nm); _fresh_ = bool(_an_ and _now - float(_an_.get("t", 0)) <= ANNOUNCE_MIN * 60 and _an_.get("md5") in (None, _md))
                        if not _live_ and not _fresh_:
                            _s, _w, _k = _new[0]      # transcript
                            rx["announced"][_nm] = {"why": _w, "t": _now, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "how": "the agent's message", "msg": _k, "md5": _md}
                            rx["asked"].pop(_nm, None)
                        _used.extend(a_[2] for a_ in _new); del _used[:-50]; _rx_save(root, rx)
            except Exception: pass
            ref = render_gate(root, ps)
            if ref: return ref
        elif _claude(root):
            ip_ = inline_picture(cmd, cwd or os.getcwd(), root)
            if ip_:
                return ("YOUR OWN PICTURES - PYTHON CODE IN THE COMMAND (31av; 31bq R7W): this command runs python code that saves a picture of its own\n"
                        "  (%s: `%s`). A picture comes from the kit - a step's own frames, `kit tool look_at`, `kit review` - so what you look at is the model,\n"
                        "  not a drawing artefact. If this picture truly has to be different, put the code in a job script (claude_code\\jobs\\<JOB>\\<name>.py)\n"
                        "  and run that: a script meets the RENDER EXCEPTION route - a line of its own in your MESSAGE to the client that STARTS\n"
                        "      RENDER EXCEPTION: <name>.py: <your reason>\n"
                        "  then \"Are you sure?\", then it holds for that version of the script. Code typed into a command has no version for an exception\n"
                        "  to hold for, so it is never let through as it is." % (ip_.get("how") or "python code", " ".join(str(ip_.get("code") or "").split())[:110]))
        m = measurement(cmd, cwd or os.getcwd(), root)
        if not m:
            return None
        if m["box"] is None:
            return ("LOOK BEFORE YOU MEASURE (the client 2026-10-06) - a measurement is next (%s) and it does not say WHAT it measures.\n"
                    "  Name its subject - the box it measures - at the end of the command:\n"
                    "      <the command>   # MEASURES: x0 x1 y0 y1 z0 z1 - <what you are measuring>   # SAW: <what the picture of it shows>   # WHY: <what this number will decide that the picture cannot>\n"
                    "  (or in the header of the script it runs; --box / --set BOX= count too). Then look at that box first:\n"
                    "      kit tool look_at --job <JOB> --set \"BOX=x0 x1 y0 y1 z0 z1\"   -> open the picture it prints\n"
                    "  the client: render reviews are how the model is understood; measure only what the picture points at." % m["what"])
        now = time.time(); c = _claude(root)
        looks = _tail(os.path.join(c, "looks.jsonl")) if c else []
        recent = [r for r in looks if now - float(r.get("opened", 0)) <= LOOK_MAX_MIN * 60]
        at = {r.get("png_n") or r.get("png") for r in recent if targeted(r.get("box"), m["box"]) and not r.get("defective")}
        need = min(PENANCE_MAX, 1 + recent_strikes(st, now))
        b = m["box"]; bs = " ".join("%g" % round(v, 2) for v in b)
        if not at:
            near = [r for r in recent if r.get("box")]
            bad_at = [r for r in recent if targeted(r.get("box"), m["box"]) and r.get("defective")]
            why = ("the %d picture(s) opened AT it are stamped RENDER DEFECTIVE - a torn or coarse mesh is no evidence: make the mesh right (PIC_DEV / PIC_ANG, an invalid face left out), draw it again, open that" % len(bad_at) if bad_at else
                   "no picture was opened in the last %d min" % LOOK_MAX_MIN if not recent else
                   ("the pictures opened in the last %d min have no frame record (not made by the kit's renderer)" % LOOK_MAX_MIN if not near else
                    "none of the %d picture(s) opened in the last %d min is AT it (its centre inside the frame, the frame at most %gx its size or %g mm)" % (len(near), LOOK_MAX_MIN, LOOK_SCALE, LOOK_MIN_MM)))
            sent = strike(root, "measure", m["what"], cmd)
            if sent:
                st_ = _dd_load(root); announce(root, st_, (st_.get("owed") or {}).get("n"), "WALL OF SHAME +1 - %s" % sent)
            body = ("LOOK BEFORE YOU MEASURE (the client 2026-10-06: \"the agent must be pushed to render review if a measurement is about to be taken\n"
                    "  in the next step ... it must be gated to be properly targeted at the measurement subject\").\n"
                    "  Next: %s of the box %s (%s) - and %s.\n"
                    "  The picture:\n"
                    "      kit tool look_at --job <JOB> --set \"BOX=%s\" [--set SHAPE=<the file you will measure>] [--set WHAT=\"<what>\"] [--set VIEWS=%d]\n"
                    "  open it (any kit render that frames this box counts once it is opened), say in a sentence what it shows - then run the\n"
                    "  measurement again, and measure only what the picture points at." % (m["what"], bs, m["how"], why, bs, need + (1 if sent else 0)))
            return (owed_message(_dd_load(root)) + "\n\n" + body) if sent else body
        if len(at) < need:
            return ("PENANCE (31aq): you have %d strike(s) in the last %d h, so a measurement now needs %d DIFFERENT pictures of its subject opened in\n"
                    "  the last %d min - %d so far. kit tool look_at --job <JOB> --set \"BOX=%s\" --set VIEWS=%d   (open every one), then measure."
                    % (recent_strikes(st, now), STRIKE_HOURS, need, LOOK_MAX_MIN, len(at), bs, need))
        saw = SAW.search(cmd); why_ = WHY.search(cmd)
        if not saw or len(saw.group(1).strip()) < REASON_MIN or not why_ or len(why_.group(1).strip()) < REASON_MIN:
            return ("REASONS BEFORE NUMBERS (31aq; the client 2026-10-07: it \"makes a measurement that it arbitrarily decides is a bad measurement with no\n"
                    "  reasoning as to why, and then undoes correct work\"). End the command with BOTH, each a sentence (%d+ characters):\n"
                    "      # SAW: <what the picture of this box shows>\n"
                    "      # WHY: <what this number will decide that the picture cannot - the client: measure only when it is absolutely required>\n"
                    "  A number never overturns a picture: if the picture says the work is right, the work stays." % REASON_MIN)
        _record_measure(root, m)
        return None
    except Exception:
        return None

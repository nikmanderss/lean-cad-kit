"""leangate.py — the LEAN kit's gates. Small on purpose, and aimed where the failures are.

    kit open   ...      declare the session (orchestrator, once per conversation)
    kit card   <path>   lint a job card BEFORE a worker is launched
    kit job    <name> --type <edit_type>   register a job and pin its edit type
    kit look   <job> --says "<one line per picture>"   the orchestrator's own look
    kit accept <job>    the gate on applying a piece to the model of record

DESIGN NOTE — WHY THIS IS NOT A SECOND gates.py.
the client, 2026-09-09: *"I want the lean kit to have similar session start requirements for method and
edit types. I want gates in the lean kit. I want wardens in the lean kit. The main difference for
the lean kit is it's not trying to teach everything at each agent/session launch. It's setting up
only the workflows that can have a chance of success. for both the orchestrator and the agents
that get launched by it."*

An earlier kit is 29,092 lines and it put its heaviest machinery on the WORKER. Measured on the
part project: 8,021 gate-log rows, 286 refusals, 332 look challenges, 2,039 stamped images,
96 % of challenges satisfied — and the round still edited the wrong faces, because
proof-of-looking proves LOOKING and cannot prove SEEING. Two of its own gates had quietly stopped
working: 220 of 220 registered attempts sit at outcome OPEN (nobody ever calls attempt_outcome, so
the attempt budget has never seen an attempt), and 284 of 415 ledger rows carry no `pitfall`, so
roughly 285 paid-for lessons cannot reach a begin() push at all.

Meanwhile in this kit the worker cannot make a method mistake, because a template has no branch
where a different method could be expressed. And the tier record says so plainly — nearly every
lean failure on record is the ORCHESTRATOR'S CARD:

    "worker flagged my wrong expected volume"          "CARD wrong: lead-in too short"
    "card forgot the bore openings"                    "orchestrator arithmetic error"

So the gates go where the failures are. Five of the six below judge the ORCHESTRATOR. The worker
keeps exactly two obligations it already had — run only through `kit run`, and write HIT/MISS for
every picture — because the tier record shows it already meets them.

WHAT IS DELIBERATELY ABSENT, and each absence is a lesson from an earlier kit:
  * No master to read in full. The contract is one page and it is pushed, not looked up.
  * No stamped-code look challenge. It bought 2,039 stamped images and did not stop the round
    editing the wrong feature. What is gated instead is the ONE look nobody was doing: the
    orchestrator's own, before it applies a piece.
  * No attempt budget. An earlier kit's has never once closed an attempt.
  * No trap wall. Traps are attached to the EDIT TYPE and print only for the type in play —
    "setting up only the workflows that can have a chance of success".
"""

import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)



def records_root(root):
    """31bq B53: the folder the SHARED RECORDS live under - the project, or KIT_SCRATCH_ROOT when a kit-maintenance scratch test sets it (its own .claude folder and
    claude_code/STATE_NOW.md), so a test never writes the agent's live session, inbox marker, frames, looks, strikes or state (a recorded process failure: a cleanup by hand put a
    day-old session record over the agent's live one)"""
    r = (os.environ.get("KIT_SCRATCH_ROOT") or "").strip()
    return r if r else root


def store(root):
    return os.path.join(records_root(root), ".claude", "_leangates")


def _p(root, name):
    return os.path.join(store(root), name)


def _read(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default


def _write(root, name, obj):
    os.makedirs(store(root), exist_ok=True)
    p = _p(root, name)
    tmp = p + ".%d.tmp" % os.getpid()
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2)
    os.replace(tmp, p)
    return p


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


class Refused(Exception):
    """A gate said no. The message is the whole remedy — print it and stop."""


def refuse(gate, findings, remedy=""):
    lines = ["", "=" * 78, "%s REFUSED — %d finding(s):" % (gate.upper(), len(findings)), "=" * 78]
    for f in findings:
        lines.append("  - %s" % f)
    if remedy:
        lines += ["", remedy]
    lines.append("=" * 78)
    raise Refused("\n".join(lines))



PS_PY = None


def ps_python():
    """The interpreter to spell in a line for the client. NEVER the word `python`."""
    global PS_PY
    if PS_PY:
        return PS_PY
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "env.json"),
                  encoding="utf-8") as fh:
            PS_PY = (json.load(fh) or {}).get("python") or sys.executable
    except Exception:
        PS_PY = sys.executable
    return PS_PY


def _psq(a):
    """Quote one argument the way PowerShell needs it."""
    a = str(a)
    if a.startswith('"') and a.endswith('"'):
        return a
    if re.match(r"^-{1,2}[A-Za-z0-9][\w-]*$", a):
        return a
    return '"%s"' % a.replace('"', '`"')


def psline(script, *args, **kw):
    r"""ONE pastable PowerShell line that runs `script` with `args`. Use this; never type one.

        psline(r"C:\...\selftest_wallclock.py")
        psline(r"C:\...\install_lean_hooks.py", "--project", project)
        psline(r"C:\...\kit.py", "status", "--as-orchestrator", cwd=kitdir)

    `cwd=` prepends `cd "<dir>";` — a semicolon, NOT `&&`: Windows PowerShell 5.1 has no `&&`
    operator at all and reports a parse error on it. `&` at the front is the call operator, and
    without it PowerShell treats a leading quoted path as a string literal and merely echoes it.

    A `.ps1` TAKES NO INTERPRETER. Found 2026-09-16: asked for a line to run a generated `.ps1`,
    this returned `& "...python.exe" "...\script.ps1"`, which hands the file to Python and dies on
    the first `$`. That is the failure this whole function exists to stop — *"nearly right is worse
    than nothing, because it looks runnable"* — so a PowerShell script is called directly, and a
    `.bat`/`.cmd` likewise.
    """
    _ext = str(script).strip().strip('"').strip("'").lower()
    if _ext.endswith((".ps1", ".bat", ".cmd")):
        parts = ["&", _psq(script)] + [_psq(a) for a in args]
        line = " ".join(parts)
        if kw.get("cwd"):
            line = 'cd %s; %s' % (_psq(kw["cwd"]), line)
        return line
    py = kw.get("py") or ps_python()
    parts = ["&", _psq(py), _psq(script)] + [_psq(a) for a in args]
    line = " ".join(parts)
    if kw.get("cwd"):
        line = 'cd %s; %s' % (_psq(kw["cwd"]), line)
    return line


PS_FAULTS = [
    (r"^\s*[\"']",
     "starts with a quoted path and no `&`",
     "PowerShell treats a leading quoted string as a VALUE and prints it. It does not run, it "
     "does not error, and it looks like it worked. Put the call operator first: `& \"...\\python.exe\" \"...\"`"),
    (r"^\s*(python|python3)\b",
     "starts with the bare word `python`",
     "On this machine that is the Microsoft Store stub — it prints an advert and exits non-zero "
     "(INSTALL.md, Windows: Python). Spell the interpreter's full path: `& \"%s\" ...`"),
    (r"\^\s*$",
     "ends with `^`",
     "that is a cmd.exe continuation and PowerShell does not understand it. One line, no "
     "continuations of any kind"),
    (r"\\\s*$",
     "ends with `\\`",
     "that is a bash continuation. One line"),
    (r"`\s*$",
     "ends with a backtick",
     "a PowerShell continuation is still MORE THAN ONE LINE, and a multi-line paste is what this "
     "rule exists to stop. One line"),
    (r"&&",
     "uses `&&`",
     "Windows PowerShell 5.1 has no `&&` operator and fails to parse it. Separate statements "
     "with `;`"),
    (r"(?<![\w-])[A-Z_][A-Z0-9_]*=\S+\s+(?=&|\"|py\b|python)",
     "sets an environment variable the bash way",
     "`FOO=bar cmd` is bash. PowerShell needs `$env:FOO=\"bar\"; & \"...\" ...` — and the LK_* "
     "burrito variables are set exactly this way"),
    (r"%[A-Za-z_][A-Za-z0-9_]*%",
     "uses %VAR% expansion",
     "that is cmd.exe. PowerShell reads `$env:VAR`"),
    (r"<[^>]{2,40}>",
     "contains a placeholder in angle brackets",
     "the client cannot fill in a path the client has not been told. Spell the real, complete path. (A "
     "placeholder for a VALUE the client must decide — a note, a verdict — is fine and is not this)"),
    (r"\n",
     "is more than one line",
     "one pastable line. Several commands means several separate one-line commands"),
    (r"[^\x00-\x7F]",
     "contains a non-ASCII character",
     "an em-dash, a curly quote or an arrow. Windows PowerShell 5.1 reads a .ps1 as cp1252 unless "
     "it has a BOM, and the console is cp1252 too, so a UTF-8 dash arrives as three bytes and "
     "breaks the quoting around it. A .ps1 written this way on 2026-09-14 would not parse at all - "
     "four syntax errors from four dashes. It is P36 from the other direction (`kit check` died on "
     "an em-dash because the generated script was written in cp1252). ASCII only in anything the client "
     "runs: '-' not '—', straight quotes, '->' not an arrow"),
]


def pslint(line):
    """[(what is wrong, what to do instead)] for a line meant for the client. Empty means it is fine."""
    out = []
    for pat, bad, fix in PS_FAULTS:
        if re.search(pat, str(line or ""), re.M):
            out.append((bad, fix % ps_python() if "%s" in fix else fix))
    if not re.search(r"[A-Za-z]:\\", str(line or "")) and "cd " not in str(line or ""):
        out.append(("names no absolute path",
                    "a line pasted from a document runs in whatever folder the window happens to "
                    "be in. Spell the full path, or `cd \"<full path>\";` first"))
    return out



SESSION = "SESSION.json"
STALE_H = 18

OPEN_EXAMPLE = (
    'kit open --method --edit-types --state "STATE_NOW.md: <what its newest block says>" '
    '--model "<project>\\claude_code\\bank\\<the model of record .brep>" '
    '--answer overlap="<the two numbers, and which is which>" '
    '--answer measure="<who measures>" '
    '--answer punch="<what a piece may never do, and what on the card prevents it>"')

# METHOD.md
EXAM = [
    {"id": "overlap",
     "q": "A piece joins existing material. How far does it go INTO that material, and how far "
          "must a face that must NOT touch stand clear? (two numbers, in mm)",
     "why": "METHOD.md 3.4. Never flush, never 0.1 mm off — that is where the kernel fails "
            "silently and reports success."},
    {"id": "measure",
     "q": "Who measures — the orchestrator or the worker?",
     "why": "the client's rule. Workers ONLY render; every number a worker needs is on its card, "
            "measured by you. A worker that measures is a worker choosing a number."},
    {"id": "punch",
     "q": "A piece may enter an existing feature. What may it never do, and what does the card "
          "state to prevent it?",
     "why": "METHOD.md 3. Punch-through is forbidden; the card states the far limit as a "
            "number the orchestrator has measured."},
]



def _dist(text, num, words):
    """Characters from `num` to the NEAREST of `words`, or None if none appear.

    A fixed window does not work here and the selftest proved it: "0.5 mm into material, 2 mm
    clear in air" is 38 characters, so a 40-character window around either number contains BOTH
    keyword sets and the inversion check fired on a correct answer. What actually distinguishes
    the right answer from the inverted one is not presence but WHICH KEYWORD IS CLOSER, so that
    is what is measured.
    """
    t = text.lower()
    best = None
    for m in re.finditer(re.escape(num), t):
        for w in words:
            for wm in re.finditer(re.escape(w), t):
                d = abs(wm.start() - m.start())
                if best is None or d < best:
                    best = d
    return best


def _closer_to(text, num, these, than_these):
    """True when `num` sits nearer to `these` than to `than_these`."""
    a, b = _dist(text, num, these), _dist(text, num, than_these)
    if a is None:
        return False
    return b is None or a < b


INTO = ("into", "inside", "in to", "overlap", "material", "embed", "bury")
AIR = ("clear", "air", "away", "gap", "stand off", "standoff", "apart", "not touch")


def _grade_overlap(a):
    if not re.search(r"0\.5", a):
        return "no 0.5 mm figure at all."
    if not re.search(r"(?<![\d.])2(?![\d])|2\.0", a):
        return "no 2 mm figure at all."
    half_into = _closer_to(a, "0.5", INTO, AIR)
    two_air = _closer_to(a, "2", AIR, INTO)
    if not half_into and not two_air:
        return ("the two numbers are the WRONG WAY ROUND. 0.5 mm is how far a piece goes INTO "
                "material;\n      2 mm is how far a face that must not touch stands CLEAR in air.")
    if not half_into:
        return "0.5 mm is not tied to going INTO material. Say which number is which."
    if not two_air:
        return "2 mm is not tied to standing CLEAR in air. Say which number is which."
    return None


def _grade_measure(a):
    t = a.lower()
    if re.search(r"\b(worker|agent)s?\b[^.]{0,40}\b(measures?|measuring)\b", t) and \
            not re.search(r"\b(worker|agent)s?\b[^.]{0,40}\bnever\b", t):
        return "this says the WORKER measures. Workers only render."
    if re.search(r"(never|not|no)\b[^.]{0,30}orchestrat", t):
        return ("this says the orchestrator does NOT measure. It is the only party that "
                "measures.")
    if "orchestrat" not in t:
        return "does not name the orchestrator."
    return None


def _grade_punch(a):
    t = a.lower()
    forbids = re.search(r"(never|not|no|forbid|must not|cannot|may not)\b[^.]{0,60}"
                        r"(punch|through|out the other|far side|exit)", t) or \
              re.search(r"(punch|through)[^.]{0,30}(forbidden|not allowed|never)", t)
    if not forbids:
        return ("does not say punch-through is FORBIDDEN. As written it reads as permission — "
                "the test\n      answer 'punch through as far as the limit stops you' passed the "
                "old keyword check.")
    if not re.search(r"far limit|limit|stops? \d|mm short", t):
        return "does not name the FAR LIMIT as the thing on the card that prevents it."
    return None


GRADERS = {"overlap": _grade_overlap, "measure": _grade_measure, "punch": _grade_punch}


def exam_questions():
    return [{"id": q["id"], "q": q["q"]} for q in EXAM]


CONVERSATION = ".conversation"


def stamp_conversation(root, sid):
    """Record the CURRENT Claude Code session_id. Called only from the SessionStart hook.

    Lives in `.claude/` rather than the gate store because it describes the CONVERSATION, not
    the work: purging gate state must never lose the one fact that tells a compaction from a
    new conversation.
    """
    if not sid:
        return None
    try:
        d = os.path.join(records_root(root), ".claude")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, CONVERSATION), "w", encoding="utf-8") as fh:
            fh.write(str(sid).strip())
    except OSError:
        return None
    return str(sid).strip()


def current_conversation(root):
    """The id stamped by the SessionStart hook, or None if the hook never ran.

    None is meaningful and is NOT guessed around: no id means the hooks are not firing, which is
    itself the thing worth knowing."""
    try:
        with open(os.path.join(records_root(root), ".claude", CONVERSATION), encoding="utf-8") as fh:
            return fh.read().strip() or None
    except OSError:
        return os.environ.get("CLAUDE_SESSION_ID") or os.environ.get("GATES_CONVERSATION") or None


def session_open(root, method_read, edit_types_read, state_read, answers, model_of_record,
                 notes=""):
    """Declare the session. Every gate below calls _require_session() first.

    WHY THERE IS A READING GATE AT ALL, when the whole point of this kit is not to teach
    everything at every launch: the two files are 20 KB together, not 140 KB, and the failures
    they prevent are the ones actually on this project's record. An earlier kit's read-in is ~50k
    tokens and an exam; this is a five-minute read and three questions.
    """
    findings = []
    for name, val in (("METHOD.md", method_read), ("EDIT_TYPES.md", edit_types_read)):
        if not val:
            findings.append("%s not declared read (--method / --edit-types). Read once per project - METHOD.md is "
                            "the approach, EDIT_TYPES.md the catalogue `kit route` picks from - then declare it." % name)
    if not str(state_read or "").strip():
        findings.append("no state file named. Say which STATE.md you read and what it says the "
                        "model of record is — a session that does not know the model of record "
                        "edits the wrong file, and that has happened here.")
    mor = str(model_of_record or "").strip().strip('"').strip("'")
    first_body = False
    if not mor:
        _bks = [os.path.join(root, "claude_code", "bank"), os.path.join(root, "model", "bank")]
        _have = sorted(f for d_ in _bks if os.path.isdir(d_) for f in os.listdir(d_) if f.lower().endswith((".brep", ".stl")))
        if _have:
            findings.append("no model_of_record. Name the FILE every piece will be applied to (in the bank: %s)." % ", ".join(_have[:8]))
        else:
            first_body = True
    else:
        cands = [mor] if os.path.isabs(mor) else [
            os.path.join(root, mor), os.path.join(root, "claude_code", "bank", mor),
            os.path.join(root, "model", "bank", mor), os.path.join(root, "model", mor), mor]
        hit = next((c for c in cands if os.path.isfile(c)), None)
        if hit:
            model_of_record = os.path.abspath(hit)
        else:
            looks_like_prose = (" " in mor and not os.path.splitext(mor)[1]) or len(mor) > 160
            bank = os.path.join(root, "claude_code", "bank")
            if not os.path.isdir(bank):
                bank = os.path.join(root, "model", "bank")
            try:
                have = sorted(f for f in os.listdir(bank) if f.lower().endswith(".brep"))
            except OSError:
                have = []
            findings.append(
                "--model is a FILE PATH and this one does not resolve to a file:\n"
                "      %s\n"
                "      %s\n"
                "      Give the path of the .brep every piece will be applied to — absolute, or "
                "relative to the\n      project root. Put any DESCRIPTION in --notes instead.%s"
                % (mor[:150],
                   ("That reads like a description, not a path."
                    if looks_like_prose else "No file of that name was found."),
                   ("\n      In %s: %s" % (bank, ", ".join(have[:8]))) if have else
                   "\n      Nothing in claude_code\\bank\\ yet — an EMPTY bank opens WITHOUT --model (`kit open --method --edit-types --state ...` with no --model: the first-body start, PROJECT_START.md); a bank that holds a brep names it here (31bx R7 D2)."))

    answers = {str(k).lower(): str(v or "") for k, v in (answers or {}).items()}
    for q in EXAM:
        a = answers.get(q["id"], "")
        if not a.strip():
            findings.append("exam %r unanswered: %s" % (q["id"], q["q"]))
            continue
        bad = GRADERS[q["id"]](a)
        if bad:
            findings.append("exam %r — %s\n      your answer: %s\n      %s"
                            % (q["id"], bad, a[:150], q["why"]))

    if findings:
        refuse("session_open", findings,
               "Answer from CONTRACT.md (pushed) and METHOD.md 3 (the far limit); METHOD.md and EDIT_TYPES.md once per project. Then:\n"
               "    " + OPEN_EXAMPLE + "\n\n"
               "  kit exam   prints the three questions.")

    purge_old_looks(root)
    rec = {"opened": _now(), "started": time.time(), "method_read": True,
           "edit_types_read": True, "state_read": str(state_read),
           "model_of_record": str(model_of_record), "notes": str(notes),
           "answers": answers, "pid": os.getpid(),
           "conversation": current_conversation(root)}
    _write(root, SESSION, rec)
    print("[leangate] SESSION OPEN — model of record: %s" % (model_of_record if not first_body else "NONE YET - the bank is empty: the first body is the next step (PROJECT_START.md; 31bv B1)"))
    print("[leangate]   state: %s" % str(state_read)[:110])
    print("[leangate]   Gates now active: card lint, job registration, the orchestrator's own")
    print("[leangate]   look, and the apply gate. `kit run/render` work for workers as before.")
    return rec


def session(root, conversation=None):
    """The open session, or None. Stale after STALE_H — a session is a working stretch.

    conversation: when given, the CURRENT Claude Code session_id. A session opened in a DIFFERENT
    conversation is reported (see session_state) but not silently treated as yours.

    A test orchestrator, 2026-09-09: it inherited a live session from the previous orchestrator
    and "could have done the whole job without reading METHOD.md. The reading gate is
    per-18-hours, not per-conversation." Correct — and the fix is not simply to shorten the
    window, because a COMPACTION must not close a session either. Those are different events and
    they need telling apart, which is what session_state() below does.
    """
    rec = _read(_p(root, SESSION), None)
    if not rec:
        return None
    # kit close
    if rec.get("closed"):
        return None
    try:
        if (time.time() - float(rec.get("started", 0))) > STALE_H * 3600:
            return None
    except (TypeError, ValueError):
        return None
    return rec


def session_record(root):
    """The session record REGARDLESS of whether it has been closed. `session()` is the gate question -
    is a session OPEN - and `close()` needs a different one: what session am I closing? Reading the gate
    answer there made a second `close()` lose the model of record (selftest [13], 2026-09-21)."""
    return _read(_p(root, SESSION), None)


def session_state(root, conversation=None):
    """(state, session) — how the open session relates to the conversation asking.

        "none"      no session, or it aged out
        "mine"      opened in THIS conversation
        "carried"   same conversation id, so this is a COMPACTION — the session survives
        "foreign"   opened in a DIFFERENT conversation and jobs are still in flight
        "orphan"    opened in a different conversation with nothing in flight

    WHY THIS EXISTS. Claude Code re-fires SessionStart on every compaction, and an earlier kit
    learned the expensive way (an earlier improvement (P11)) that treating that as a new session
    kills everything in flight — there, a compaction cost two workers their handbacks after they
    had finished their real work. The lesson generalises: **a compaction is the same working
    stretch and must not close anything; a genuinely new conversation is a different stretch and
    must not inherit the reading.** One test tells them apart, and it is the conversation id.

    Nothing here refuses. It reports, and the SessionStart warden says which it is — because the
    failure both kits keep paying for is a guard that changes state without announcing it.
    """
    rec = session(root)
    if not rec:
        return "none", None
    conversation = conversation or current_conversation(root)
    prev = rec.get("conversation")
    if conversation and prev and conversation == prev:
        return "carried", rec
    if conversation and prev and conversation != prev:
        jobs = _read(_p(root, JOBS), {}) or {}
        live = [n for n, j in jobs.items() if not j.get("applied")]
        return ("foreign" if live else "orphan"), rec
    return "mine", rec


def _require_session(root, gate):
    s = session(root)
    if not s:
        refuse(gate, ["no session is open in this project (or it is more than %d h old)."
                      % STALE_H],
               "The orchestrator opens it once:  kit open ...\n"
               "  kit exam  prints the three questions.\n"
               "  A WORKER never opens a session and never needs one — if you are a worker and "
               "you are\n  reading this, you ran an orchestrator command. Stop and report it.")
    return s



CARD_SLOTS = [
    ("EDIT TYPE",   [r"edit[ _]?type\s*[:=]", r"^\s*type\s*[:=]"],
     "name one type from EDIT_TYPES.md. A worker never combines two."),
    ("PURPOSE",     [r"purpose\s*[:=]", r"what it is for", r"this feature (is|exists)"],
     "ONE PLAIN SENTENCE saying what the feature is FOR — 'the face looks up and BACK at the "
     "viewer'. METHOD.md 10: R1's screen faced away from the viewer while every number was right "
     "and every check passed. A number can only be checked against itself."),
    ("BASE FILE",   [r"base\s*[:=]", r"region\.brep", r"base\.brep"],
     "the .brep the piece is fused into or cut from, already copied into the job folder."),
    ("PARAMS",      [r"PARAMS", r"params\s*[:=]"],
     "every value spelled out. A missing value costs a launch: the worker asks and stops "
     "(correctly), and you pay a round trip."),
    ("EXPECTED",    [r"expect(ed)?\s*[:=]", r"expect(ed)? vol", r"expect(ed)? faces"],
     "the volume change and face count YOU COMPUTED — not guessed. This is the tripwire that "
     "caught three bad cuts. Use 'about' for face counts: cylinder seams split unpredictably."),
    ("FAR LIMIT",   [r"far limit", r"stops? \d", r"mm short", r"no punch|punch-?through"],
     "the far limit in words and a number ('stops 3 mm short of the inner floor'). "
     "Punch-through is forbidden and the worker cannot measure to check."),
    ("ABS PATHS",   [r"[A-Za-z]:\\\\|[A-Za-z]:\\|/sessions/|\$\{?CLAUDE"],
     "absolute paths. A relative path resolved from the wrong cwd is a recorded failure in both "
     "kits (one lean job ran in the wrong folder and had to be redone)."),
    ("TOP FACE",    [r"top face\s*[:=]\s*[^<\s]"],
     "what the piece's TOP has to be, decided before the numbers: 'a plane' (extrude) or 'a piece "
     "of the existing skin' (sketch_connect off its section points). an early fill job chose the type "
     "from the shape of the hole, not the surface, and shipped a flat patch on a curved skin.",
     ("sketch_extrude", "sketch_connect", "burrito")),
    ("ROW",         [r"^\s*row\s*[:=]\s*(?:[A-L]\b|R\d+\b|none\s*[-—:]\s*the client\b)"],
     "which criteria row this job satisfies - a letter (A-L), an R<n> of the client's work list, or "
     "`none - the client <date>: '<the client's words>'` when the client asked for it outside the table. an early corner job "
     "(2026-09-10) satisfied none of the rows it was carded for; a job that names its row can be "
     "checked against that row's test."),
    ("CLASS",       [r"^\s*class\s*[:=]\s*(shape|seal)\b"],
     "shape or seal — does it change what the outside looks like, or only how it is built? the client's "
     "order: shape first, seal last. Decided at the card, like the top face."),
    ("DOSSIER",     [r"^\s*dossier\s*[:=]\s*\S+"],
     "the dossier the numbers came from (`kit dossier show <name>`), or 'none — <why>'. A card "
     "written from fresh single measurements is the 27-calls-for-no-edit waste the client refused."),
    # SECTIONS APPROVED  its approval is the REGION JUDGE
    # kit rebuild
    ("AFTER RENDER", [r"kit\.py[\"']?\s+render\b[^\n]*--box", r"\bAfter\s*[:=][^\n]*render[^\n]*--box"],
     "the exact `kit render ... --box <the job box> --job <name>` line the worker runs after its "
     "edit. Without it the worker renders the WHOLE BODY at ~0.35 mm/px (an early fill job, "
     "2026-09-10: a 4 mm fill in eleven pixels) and the before/after pair is not comparable."),
]

TYPE_TRAPS = {
    "sketch_extrude": [
        "extra_rects that only TOUCH along an edge are DROPPED by the fuse. Overlap them, or "
        "use one rectangle that swallows the old feature and re-cut the bore after.",
        "The z extent of a FACE is not the extent of MATERIAL. A 64 mm blade shipped three "
        "times from exactly this (a recorded lesson).",
        "Expected volume = plan area x (depth - the air lead-in). Counting the lead-in as "
        "removed is the commonest card arithmetic error on record.",
    ],
    "hole": [
        "MOVING a bore is TWO operations: plug the old, cut the new. R25 shipped with two "
        "3.4 holes 4 mm apart in each side wall (a recorded lesson).",
        "A tilted bore's lead-in = 2 + r*tan(tilt). Too short and the end discs clip the block.",
        "Face count after a bore is unpredictable — the cylinder seam may or may not split. "
        "Say 'about'.",
        "Wall thickness: a 4.0 bore down a 10x10 post leaves EXACTLY 3.0, not more than. "
        "List all five clearances.",
    ],
    "sketch_connect": [
        "The two outlines must have the SAME vertex count. A 4-vertex against a 3-vertex "
        "refuses — correctly (test T04).",
        "Rounded corners are drawn INTO both outlines, never filleted afterwards.",
    ],
    "burrito": [
        "THE WALLS ARE THE CARD. A wall lands in AIR or in thick clean material, never through the feature being fixed, "
        "never along a skin: `kit rebuild region` refuses a GRAZING wall and warns of a DESIGN FACE lying in a plane - and "
        "it renders THE ORBIT OF THE CUTS (review\\region_cuts_*.png, the walls in red on the body): open every frame and "
        "record the verdict (`kit rebuild judge --what region`) - a fresh split refuses without it (the client 2026-10-05: \"the cuts "
        "should be render reviewed by an orbit pass before continuing work\"). The same holds for the keep's cuts.",
        # kit rebuild
        "THE REINSERT FACES COME FIRST: `kit rebuild reinsert --set STEP=1` writes wall_caps.brep - the body's own section faces on the edit region's "
        "walls - before any skin step, and every skin face ends exactly on them (L114; the skin steps refuse without it). Enclosed pockets are junk "
        "and are filled by the rebuild (the client 2026-10-05: \"enclosed pockets are not wanted\"); a designed OPENING (one the project's facts rule open - PROJECT_FACTS section 6, its newest line) gets "
        "a PROTECT box round the opening's air ONLY, set on the REGION step (--set PROTECT=...) - STEP 4 refuses a changed box; a box round enclosed "
        "air keeps the junk (L111).",
        "A DETACHED COMPONENT OF THE PIECE IS NOT A RIB END until measured: STEP 2 keeps one only if IN_CONTENT (90 %) "
        "of it lies inside the original; a section's two (30 and 7 mm3, 64 % inside) stood 0.6 mm proud of the vane wing "
        "as a lump the sandbox review missed and the kit's before/after review caught (L89, L95).",
        "EVERY PICTURE, FULL SIZE, BEFORE AND AFTER ON THE SAME CAMERA. The chain's own reviews (review\\, review_body\\) "
        "are the piece and the seams; the kit's `kit review` before/after frames are what found the lump. Both, always; "
        "a defect in any frame stops the chain at that step.",
        "THE KIT'S GATES NEED THEIR OWN LINES: `kit check` refuses the window box by its 25x rule - pass `--wide-box "
        "\"the window is the change: <content mm3> re-expressed\"`; `kit look` needs the card's After render (`kit render "
        "... --box <window + 3> --job <name>`) first - the chain's pictures are not stamped.",
        "THE WIREFRAME IS WHERE THE GEOMETRY IS CORRECTED, AND EVERY LOOK IS JUDGED: the points pick what is kept (PTS_BOX / PTS_DROP, each with "
        "its reason), the feature map names the faces (FEATURES with _why), every LINE / RAIL / _add / _fillets entry is decided with its why from "
        "the WIRE_* pictures - a line is decided, never traced on a measurement (L127, L137); the layout, the wires, the piece's look and the trial's "
        "real model are each OPENED frame by frame and judged before the next step (L136); the trial is the acceptance - two reviewers, then judge "
        "--what trial ok - and is never rebuilt or re-sewn after (L134). The voxel field and `kit rebuild keep` are SHELVED (31al / 31ba).",
        "THE REINSERT MEETS THE BODY ON EXACT PLANES ONLY: STEP 2 cuts the body and the piece by the SAME region solid; "
        "no skin of the piece ever lies on a skin of the body (the band of 2026-09-28 did, and the fuse failed quietly on "
        "it - L99). A piece that fails check(True) is REFUSED before any boolean (L100); the volume is gated to 0.1 % of "
        "the exact expectation; STEP 4 refuses a seam face wider than SEAM_MAX (0.15, the client's seam ceiling), a PROTECT box whose material "
        "changed, or an enclosed void. A FAIL there is the piece's defect, not the join's: fix the piece.",
    ],
    "gapfill": [
        "The SLAB reaches INTO every wall the fill must touch (0.5 mm or more into material), and its "
        "free walls sit exactly where the fill should END - they become the fill's own faces. A slab "
        "wall left in air where contact was wanted is a fill that touches nothing there.",
        "The fill is the air piece that contains the PROBE point. Never pick it by bounding box: a "
        "B-spline body's boxes reach far outside the geometry (direct route, 2026-09-11).",
        "The fill's bottom and ends FOLLOW THE NEIGHBOUR'S surface (the cover ledge plane, the rim), "
        "not a chosen z (the client, 2026-09-11: 'all of those fixes do not follow a specific z').",
        "Judge the fuse by solids, validity and the fill's own volume, and read a 1-3 % volume "
        "discrepancy as the kernel's precision on this body, not as a lost piece.",
    ],
    "cutter": [
        "`find.tol_deg` is MEASURED, never assumed. The four faces the client picked for the vane plate sit "
        "7.6 and 8.9 deg off -z, so a 5 deg card finds NONE of them - and an empty selection proves "
        "nothing while reading as a clean part (T68). Run `kit measure faces --normal` first and put "
        "its angles on the card.",
        "`expect.volume_mm3` is required and the run refuses at C9 without it - after the cut. "
        "A card that omits it buys the whole job and then throws it away.",
    ],
    "mirror_pattern": [
        "Symmetry of NAME is not symmetry of GEOMETRY. Section the far side and look before "
        "repeating an edit on 'the other one' (a recorded lesson).",
    ],
    "split": [
        "A cut plane exactly on an existing face removes the feature on one side only. Offset "
        "by a micron (14.0005) or cut each side separately (a recorded lesson).",
    ],
    "edge_round": [
        "Rounds go on a PRIMITIVE piece BEFORE it is fused. Never on the assembled body.",
    ],
    "revolve": [
        "Tier is untested for this type. Launch it, then record the result in tests\\README.md.",
    ],
    "shell": [
        "Tier is untested for this type. Plain box-like solids only.",
    ],
    "move": [],
    "region_look": [],
    "voxel_smooth": [
        "TREATS ONE DEFECT CLASS: a CONCAVE JUNCTION that wants a fillet. Not a step, shelf, ridge,",
        "tab, crown or shard - those are REMOVALS or convex, and go to `cutter` or the B-rep. The tell",
        "when it is aimed wrong is a FRAGMENTARY ADD mask: slivers being added AROUND the feature.",
        "Name the V3 route at V1, from the ACCEPTANCE: blend -> A, rim tolerated -> B, both -> C.",
        "The drop-in cannot produce a tangent blend at any cell size - the rim is structural.",
        "`add_open` is the LAST resort: it erodes the mask and a fillet's feather is thinner than it.",
        "Check the box against `kit frozen list` before choosing lumps; a regular array of lumps at",
        "constant pitch is SUSPECT - nothing measurable tells a construction gap from a design.",
    ],
    "mesh_union": [
        "THE SOLID IS CLOSED AND WOUND OUTWARD, checked about ITS OWN CENTRE, not the origin: a sweep whose "
        "caps face out and sides face in reads 'closed' and a positive volume about the origin (rail piece P3 "
        "lost material). `kit union` re-winds and refuses a volume outside 0..+solid, but draw it right.",
        "NO FACE OF THE SOLID GRAZES A BODY FACE: keep every face >= 0.3 mm inside or outside the body (a "
        "coincident face is a zero field - the rail's inboard face at the plate edge sat 0.15 mm in). Two "
        "pieces of one solid must overlap, and a shared top plane between them is lifted 0.2 mm on the second.",
        "A DRAWN FACE THAT SPANS A POCKET ENCLOSES IT - `kit union` reports the cavity it makes (the rail "
        "floor bridged a 5.3 mm3 groove). Sink the face, fill the pocket, or cut it off afterwards with "
        "`kit union --cut` (the ramp cut). MJF fills an enclosed cavity with powder that never comes out.",
        "IT IS FOR DESIGNED MATERIAL, NOT BLENDING: a prism is 12 triangles here and a million on the voxel "
        "route (the client: 'why does a rectangular section that could be 4 pieces require over 1M triangles?'). A "
        "fillet is drawn INTO the solid's profile, never smoothed on afterwards.",
        "THE CROP BOX HOLDS THE WHOLE SOLID WITH 6 mm TO SPARE and `kit splice` closes it: read its seam line "
        "('seam adds +N') - a union that leaves rim points the remainder lacks beyond the splice's T-junction "
        "and near-duplicate allowances is a solid that crosses the crop wall.",
    ],
}

TYPES = sorted(TYPE_TRAPS)


# METHOD.md
# recorded

TOL_CLASSES = {"critical": 0.30, "seal": 0.10, "working": 1.5}

_NUM = re.compile(r"(?<![\w./\\-])(\d+\.\d{3,})(?![\d./\\-])")


def over_precise(text, tol=0.30):
    """Figures carrying more decimals than the tolerance class can mean. Returns a list."""
    out = []
    for m in _NUM.finditer(str(text)):
        s = m.group(1)
        dec = len(s.split(".")[1])
        if dec >= 3 and s not in out:
            out.append(s)
    return out


# kit inbox
INBOX_FILE = os.path.join("claude_code", "INBOX.md")
INBOX_SEEN = "INBOX_SEEN.json"


def _inbox_path(root):
    """31bq WW (B53 (5)): the inbox lives where its read mark lives - the project, or KIT_SCRATCH_ROOT in a kit-maintenance scratch test (the file was the
    project's and the mark the scratch root's: a scratch session appended into the agent's live INBOX.md and read it with its own mark)"""
    return os.path.join(records_root(root), INBOX_FILE)


def inbox_new(root):
    """(new_text, total_length) — what has been added to the inbox since it was last shown."""
    p = _inbox_path(root)
    if not os.path.exists(p):
        return "", 0
    try:
        with open(p, encoding="utf-8", errors="replace") as fh:
            txt = fh.read()
    except OSError:
        return "", 0
    st = _read(_p(root, INBOX_SEEN), {}) or {}
    seen = int(st.get("offset", 0))
    anchor = st.get("anchor") or ""
    if anchor:
        k = txt.find(anchor, max(0, seen - 4000))
        if k < 0:
            k = txt.rfind(anchor)
        if k >= 0:
            seen = k + len(anchor)
    if seen > len(txt):
        seen = 0
    return txt[seen:].strip(), len(txt)


READER = "THE ORCHESTRATOR"


def inbox_append(root, text, who=READER):
    """Append a block to the inbox VERBATIM under a stamped heading. This is the channel's own
    append - no shell quoting, no heredoc, no escape mangling `\\r` into a carriage return
    (orchestrator, 2026-09-11 08:45, Defect 2).

    THE READ MARK MOVES ONLY FOR THE READER'S OWN BLOCK. The orchestrator is the inbox's one reader;
    a block IT appends (`kit inbox --append`) is not new to it, so the mark skips that block - and
    only when nothing else was waiting. A block appended by ANYONE ELSE (the kit maintainer from LEAN_KIT,
    the Stop guard) leaves the mark exactly where it is, so the block is new at the reader's next
    look. Until 2026-09-17 every append skipped its own block whoever wrote it: two blocks from
    the kit maintainer - one of them the instruction that the lever census comes first - were classed as read
    the moment they were written, and `kit inbox` said "nothing new" (the project FAILURES row 48,
    filed by the orchestrator that found them by grepping the headings)."""
    p = _inbox_path(root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    text = text.rstrip("\n")
    head = "\n\n---\n\n# FROM %s  %s\n\n" % (who, _now())
    new, total = inbox_new(root)
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(head + text + "\n")
    if who == READER and not new.strip():
        with open(p, encoding="utf-8", errors="replace") as fh:
            txt = fh.read()
        _write(root, INBOX_SEEN, {"offset": len(txt), "anchor": txt[max(0, len(txt) - 400):], "when": _now()})
    return len(head) + len(text) + 1


def inbox_mark(root, total_length):
    p = _inbox_path(root); anchor = ""
    try:
        with open(p, encoding="utf-8", errors="replace") as fh:
            txt = fh.read()
        anchor = txt[max(0, int(total_length) - 400):int(total_length)]
    except OSError:
        pass
    _write(root, INBOX_SEEN, {"offset": int(total_length), "anchor": anchor, "when": _now()})


def inbox_banner(root):
    """Print anything new in the inbox, ONCE. `***` so --brief cannot hide it. True if shown."""
    new, total = inbox_new(root)
    if not new:
        return False
    print("*** INBOX *** new instructions in %s — read them before you continue:" % INBOX_FILE)
    for line in new.splitlines():
        print("***   " + line)
    print("*** INBOX *** end (shown once; the file keeps them).")
    inbox_mark(root, total)
    return True


def inbox_wait(root, seconds=600, every=5):
    """Block up to `seconds` for new inbox text; print it when it arrives. True if it did."""
    t0 = time.time()
    while True:
        if inbox_banner(root):
            return True
        if time.time() - t0 >= float(seconds):
            print("INBOX: nothing new after %d s in %s. Run `kit inbox --wait %d` again — waiting "
                  "costs nothing; guessing costs a round." % (int(seconds), INBOX_FILE, int(seconds)))
            return False
        time.sleep(float(every))


MEASURES = "MEASURES.json"
SPIRAL_AT = 10


def measure_tick(root, what=""):
    """Count one `kit measure`. Returns (n_since_last_card, message_or_None)."""
    st = _read(_p(root, MEASURES), {"since_card": 0, "total": 0, "marks": []})
    st["since_card"] = int(st.get("since_card", 0)) + 1
    st["total"] = int(st.get("total", 0)) + 1
    st.setdefault("marks", []).append({"what": str(what)[:100], "when": _now()})
    st["marks"] = st["marks"][-40:]
    _write(root, MEASURES, st)
    n = st["since_card"]
    _jobs = _read(_p(root, JOBS), {}) or {}
    if not any(not j.get("applied") and not j.get("cancelled") for j in _jobs.values()):
        if n < 2 * SPIRAL_AT or n % SPIRAL_AT:
            return n, None
        return n, ("[leangate] %d measurements and no job open. A survey is allowed to measure; "
                   "when it has found its target, `kit newjob` opens the card and this resets." % n)
    if n < SPIRAL_AT:
        return n, None
    return n, (
        "\n" + "-" * 78 + "\n"
        "%d MEASUREMENTS SINCE THE LAST CARD WAS WRITTEN.\n" % n +
        "\n"
        "Not a refusal — sometimes a feature genuinely needs this. But it is the shape of a\n"
        "round spending itself on instruments for numbers nobody will use, and on this project\n"
        "the measured bottleneck is CARD-WRITING, not worker time: worker median 152 s against\n"
        "an orchestrator gap whose p90 is 35 minutes.\n"
        "\n"
        "Two questions, and they are the same two an earlier kit learned to ask:\n"
        "  1. CAN A RENDER ANSWER THIS INSTEAD? A picture answers most of what an instrument\n"
        "     would be built for, and `kit render` is cheap. (An earlier kit fanned four agents\n"
        "     at a tip slot whose answer was visible in a render; done directly it took minutes.)\n"
        "  2. WHICH NUMBER ON THE CARD does this measurement produce? If you cannot name the\n"
        "     PARAMS field it fills, you are not measuring for a card.\n"
        "\n"
        "Write the card. The counter resets when you do.\n"
        + "-" * 78)


def measure_reset(root):
    st = _read(_p(root, MEASURES), {})
    st["since_card"] = 0
    _write(root, MEASURES, st)


CARDS_OK = "CARDS_OK.json"


def card_passed(root, card_path):
    """(passed?, why) - has the card's CURRENT text a lint pass on record?"""
    try:
        txt = open(card_path, encoding="utf-8", errors="replace").read()
    except OSError:
        return False, "the card cannot be read: %s" % card_path
    import hashlib as _h
    ok = _read(_p(root, CARDS_OK), {}) or {}
    h = _h.md5(txt.encode("utf-8", "replace")).hexdigest()
    if h in ok:
        return True, "linted %s" % ok[h].get("when", "")
    if any(v.get("card") == os.path.abspath(card_path) for v in ok.values()):
        return False, "the card was EDITED after its last `kit card` pass - lint it again"
    return False, "the card never passed `kit card`"


def card_lint(root, card_path, edit_type=None, strict=True):
    """Refuse a card that is missing a slot the record says costs a launch."""
    _require_session(root, "card")
    if not os.path.exists(card_path):
        refuse("card", ["no such card: %s" % card_path])
    txt = open(card_path, encoding="utf-8", errors="replace").read()

    et = edit_type
    if not et:
        m = re.search(r"edit[ _]?type\s*[:=]\s*`?([a-z_]+)", txt, re.I)
        et = m.group(1).lower() if m else None
    findings = []
    if et and et not in TYPE_TRAPS:
        findings.append("edit type %r is not in EDIT_TYPES.md. The types are: %s"
                        % (et, ", ".join(TYPES)))
    for slot in CARD_SLOTS:
        name, pats, why = slot[0], slot[1], slot[2]
        only = slot[3] if len(slot) > 3 else None
        if only and et and et not in only:
            continue
        if not any(re.search(p, txt, re.I | re.M) for p in pats):
            findings.append("no %s — %s" % (name, why))

    if findings and strict:
        refuse("card", findings,
               "A card missing one of these costs a worker launch to discover. The lint costs a "
               "second.\n  METHOD.md 7b: a COMPLETE card is the single thing that keeps a haiku "
               "worker on task.")
    if findings:
        for f in findings:
            print("[leangate] card WARN: %s" % f)

    loud = over_precise(txt)
    if loud:
        print("[leangate] MORE DECIMALS THAN THE TOLERANCE CAN MEAN: %s" % ", ".join(loud[:8]))
        print("[leangate]   Classes on this part: critical 0.30, seal 0.10, working band 1.5 "
              "(METHOD.md 6).")
        print("[leangate]   Report at class resolution. NOT a refusal — a deliberate micron "
              "offset is legitimate\n[leangate]   and on this project's record (a cut plane "
              "exactly on an existing face removes the\n[leangate]   feature on one side only; "
              "14.0005 is the fix). If that is what this is, ignore this line.")

    measure_reset(root)

    # recorded
    if not findings:
        import hashlib as _h
        ok = _read(_p(root, CARDS_OK), {}) or {}
        ok[_h.md5(txt.encode("utf-8", "replace")).hexdigest()] = {"card": os.path.abspath(card_path), "edit_type": et, "when": _now()}
        _write(root, CARDS_OK, ok)

    print("[leangate] CARD OK — %s" % os.path.basename(card_path))
    if et:
        traps = TYPE_TRAPS.get(et) or []
        print("[leangate] traps for %r — %d, and ONLY these. Other types' traps are not your "
              "problem:" % (et, len(traps)))
        for t in traps:
            print("[leangate]   * %s" % t)
        if not traps:
            print("[leangate]   (none recorded for this type yet)")
    return {"card": card_path, "edit_type": et, "findings": findings}


PRIOR_ART_MAX = 14


def prior_art(root, job):
    """NAME THE PRIOR ART. Print the scripts that already exist for this job, with their own first
    line of purpose. Never refuses.

    THE DAY THIS COST. The R21 orchestrator's error log, item A1 - the most expensive entry in it:
    it rebuilt a whole pipeline from scratch against **four standing instructions and a numbered
    lesson**, because the authoritative script for the subject was sitting in the job folder and
    nobody looked. the client: *"I hope you aren't reinventing the process."* The fix, once it stopped, was
    **two environment variables** added to the script that already existed. Its own ask to this kit
    was: *"a job in a folder that already holds an authoritative script for the same subject must
    name that script, or state why it is not being used, before anything is written."*

    IT PRINTS RATHER THAN REFUSES, on purpose. Which of several scripts is authoritative is a
    judgement the kit cannot make, and a gate that guessed wrong would block a correct new job -
    the failure the client named on the fuse block. What the kit CAN do is make it impossible to say
    nobody mentioned them: the names, the dates, and the first comment line of each, which is where
    this project writes its rulings (`job_rakedsec.py`'s header carries the client's 2026-09-15 ruling).
    """
    try:
        d = os.path.join(root, "claude_code", "jobs", str(job))
        if not os.path.isdir(d):
            return
        found = []
        for f in sorted(os.listdir(d)):
            if not f.endswith(".py") or f.startswith("_kit_"):
                continue
            p = os.path.join(d, f)
            try:
                head, ruling = "", False
                with open(p, encoding="utf-8", errors="replace") as fh:
                    for i, line in enumerate(fh):
                        if i > 24:
                            break
                        s = line.strip()
                        if s.startswith("#") and len(s) > 3:
                            t = s.lstrip("# ").strip()
                            if not head:
                                head = t
                            if re.search(r"\b(?:client|user)\b.*20\d\d-\d\d-\d\d|20\d\d-\d\d-\d\d.*\b(?:client|user)\b"
                                         r"|\bruling\b|AUTHORITATIVE", t, re.I):
                                ruling = True
                                if len(t) > len(head):
                                    head = t
                mt = os.path.getmtime(p)
                found.append((ruling, f.startswith("job_"), f.startswith("w_"), mt, f,
                              time.strftime("%m-%d %H:%M", time.localtime(mt)), head[:76]))
            except OSError:
                continue
        if not found:
            return
        found.sort(key=lambda r: (not r[0], not r[1], not r[2], -r[3]))
        fams, order = {}, []
        for r in found:
            stem = re.sub(r"(_v?\d+|\d+)?(\.py)$", "", r[4])
            stem = re.sub(r"\d+$", "", stem)
            if stem not in fams:
                fams[stem] = [r, 0]
                order.append(stem)
            else:
                fams[stem][1] += 1
        total = len(found)
        found = []
        for s in order:
            r, extra = fams[s]
            found.append(r + (extra,))
        ruled = sum(1 for r in found if r[0])
        print("\n[leangate] PRIOR ART - %d script(s) in jobs\\%s, %d distinct subjects. Name the "
              "one you are" % (total, job, len(found)))
        print("[leangate]   applying, or say in RESULT.md why it is not, BEFORE you write a new "
              "one.")
        for r in found[:PRIOR_ART_MAX]:
            sib = "  (+%d earlier)" % r[7] if r[7] else ""
            print("[leangate]   %-1s %-30s %s  %s%s"
                  % ("*" if r[0] else " ", r[4], r[5], r[6][:60], sib))
        if len(found) > PRIOR_ART_MAX:
            print("[leangate]   ... and %d more subjects (* = its header quotes a ruling)"
                  % (len(found) - PRIOR_ART_MAX))
        print("[leangate]   Rebuilding one of these from scratch cost a full day on 2026-09-16. "
              "Not a refusal.")
    except OSError:
        pass


LOOSE_DOC_LIMIT = 12
PERMANENT_DOCS = ("INBOX.md", "KERNEL_LESSONS.md", "MEASUREMENTS.md",
                  "PROCESS_IMPROVEMENTS.md", "WHERE_THE_KIT_IS.md", "WALL_CLOCKS.md",
                  "STATE_NOW.md")


def loose_docs(root):
    """SAY when the documents in `claude_code\\` are piling up. Never refuse.

    the client, 2026-09-16: *"make sure things are organized appropriately and future agents are instructed
    so this file runaway doesn't happen again."* One project's working folder had **six**
    `HANDOVER_*.md`, four reports and briefs from a closed round, two merge requests and two loose
    `.ps1` scripts - and its `CLAUDE.md` named one handover by filename that was no longer the
    newest. A reader cannot tell which of six is current.

    `PROJECT_LAYOUT.md` owns the rule (ONE of each document, a round's files in
    `claude_code\\<ROUND>\\`, the folder archived whole when the round closes). This only counts and
    names. **It does not refuse** - a refusal at close would strand a session holding work to hand
    back, and a check that breaks the process is worse than no check.
    """
    try:
        cc = os.path.join(root, "claude_code")
        if not os.path.isdir(cc):
            return
        docs = sorted(f for f in os.listdir(cc)
                      if f.lower().endswith((".md", ".ps1"))
                      and os.path.isfile(os.path.join(cc, f))
                      and f not in PERMANENT_DOCS)
        if len(docs) <= LOOSE_DOC_LIMIT:
            return
        dated = [f for f in docs if re.search(r"(20\d{6}|20\d\d-\d\d-\d\d|_[Rr]\d{2,})", f)]
        print("[leangate] %d loose documents in claude_code\\ (over %d). PROJECT_LAYOUT.md: ONE of "
              "each,\n[leangate]   and a round's files live in claude_code\\<ROUND>\\ and move to "
              "_archive\\ whole when it closes." % (len(docs), LOOSE_DOC_LIMIT))
        if dated:
            print("[leangate]   %d carry a date or a round in the NAME, which is how a reader loses "
                  "track of which\n[leangate]   one is current: %s"
                  % (len(dated), ", ".join(dated[:8]) + (" ..." if len(dated) > 8 else "")))
        print("[leangate]   Not a refusal. Archive what a closed round produced; keep appending to "
              "the one file.")
    except OSError:
        pass


MEASUREMENT_LEDGER = "MEASUREMENTS.md"
# LK_MEASUREMENTS.md  kit accept
OLD_LEDGER_NAMES = ("LK_MEASUREMENTS.md",)
MEASUREMENT_LEDGERS = (MEASUREMENT_LEDGER,)


def ledger_behind(root, job):
    """SAY when the job measured more than the ledger records. Never refuses.

    M18, from the R21 merge request, and the client's own instruction behind it (2026-09-15): *"have you
    been adding all of your measurements to the dossier? If not make sure that you record the
    instruction is missing for the lean_kit agent."*

    What happened: the ledger was created on the client's order on 2026-09-11 and its last row is dated
    2026-09-11. **Four days of work measured the same body over and over** into per-job
    `status*.json`, `.npz` and PNG files, and several of those numbers were then measured AGAIN by
    a later step that had no way to know they existed - the vane rake, the shelf thickness and the
    body volume were all re-taken. The orchestrator's own error log has the matching entry (F2):
    *"did you check the dossier for measurements? Were you instructed to by the lean_kit?"* -
    the answer to both was no.

    Why it lapsed: it was nobody's step. `kit check` / `kit look` / `kit accept` gate the PICTURES;
    nothing gates the NUMBERS. The card's DOSSIER slot asks where the numbers came from, which is
    the other half - this is the half that asks whether what you measured got written down.

    It compares mtimes and prints. A refusal here would strand a session at the last gate before
    the model of record, holding work it cannot hand back, and M18 itself is a warning's worth of
    evidence rather than a gate's.
    """
    try:
        cc = os.path.join(root, "claude_code")
        led = os.path.join(cc, MEASUREMENT_LEDGER)
        if not os.path.isfile(led):
            led = None
            for n in OLD_LEDGER_NAMES:
                if os.path.isfile(os.path.join(cc, n)):
                    print("[leangate] THE MEASUREMENTS LEDGER HAS THE OLD NAME: claude_code\\%s. One name, "
                          "the one PROJECT_LAYOUT.md\n[leangate]   gives - rename it to %s (one move; the rows "
                          "do not change). Until then the\n[leangate]   ledger check below runs on it. Not a "
                          "refusal." % (n, MEASUREMENT_LEDGER))
                    led = os.path.join(cc, n)
                    break
        d = os.path.join(cc, "jobs", str(job))
        if not os.path.isdir(d):
            return
        newest, when = None, 0
        for f in os.listdir(d):
            if f.startswith("status") and f.endswith(".json"):
                m = os.path.getmtime(os.path.join(d, f))
                if m > when:
                    newest, when = f, m
        if not newest:
            return
        if not led:
            print("[leangate] NO MEASUREMENTS LEDGER in claude_code\\ - %s measured and there is "
                  "nowhere\n[leangate]   this project records a number. One file, one row per "
                  "measurement, what it was\n[leangate]   measured on and what it is valid for "
                  "(PROJECT_LAYOUT.md). Not a refusal." % job)
            return
        if os.path.getmtime(led) < when:
            secs = when - os.path.getmtime(led)
            age = ("%.0f min" % (secs / 60.0) if secs < 5400 else
                   "%.1f h" % (secs / 3600.0) if secs < 172800 else
                   "%.1f days" % (secs / 86400.0))
            print("[leangate] THE MEASUREMENTS LEDGER IS BEHIND THIS JOB by %s: %s is "
                  "newer than\n[leangate]   %s. A number nobody wrote down gets measured again - "
                  "the vane rake, the shelf\n[leangate]   thickness and the body volume were each "
                  "taken twice for exactly this reason (M18).\n[leangate]   Add the rows before "
                  "you apply. Not a refusal."
                  % (age, newest, os.path.basename(led)))
    except OSError:
        pass



LESSON_HEAD = re.compile(r"^(?:##\s+|\*\*)L(\d+)(?:-OLD)?(?:\.\s+|\s+[—-]+\s+|\.\s*$)\s*(.+?)\s*(?:\*\*)?\s*$", re.M)
STOP_WORDS = set("""a an and are as at be been before but by can cannot do does for from has have if in into is
it its not of on one only or that the then there this to was were what when which will with you your
never ever every each than them they it's this. not. into. how why where use used using""".split())


def lessons(master_md):
    """[(number, title, first ~600 chars of body)] from BURRITO_STEPS.md - both heading styles
    (`## L26. TITLE` and `**L1. Title**`), L46-OLD skipped as a duplicate of L46."""
    try:
        txt = open(master_md, encoding="utf-8", errors="replace").read()
    except OSError:
        return []
    out = []
    heads = [(m.start(), m.end(), int(m.group(1)), m.group(2), m.group(0)) for m in LESSON_HEAD.finditer(txt)]
    for i, (a, b, n, title, raw) in enumerate(heads):
        if "-OLD" in raw:
            continue
        nxt = heads[i + 1][0] if i + 1 < len(heads) else len(txt)
        body = txt[b:nxt]
        out.append((n, title.strip("* ").rstrip("."), body[:600]))
    return out


def _words(text):
    return set(w for w in re.findall(r"[a-z][a-z_0-9]{3,}", text.lower()) if w not in STOP_WORDS)


def lessons_near(master_md, text, top=6):
    """The lessons whose title (weighted) and opening share the most distinctive words with `text`.
    A nudge: it prints what a new lesson would sit beside, so a contradiction is seen before it is
    written. Returns [(score, number, title)] with score > 0, best first."""
    q = _words(text)
    if not q:
        return []
    scored = []
    for n, title, body in lessons(master_md):
        tw = _words(title); bw = _words(body)
        score = 3 * len(q & tw) + len(q & bw)
        if score:
            scored.append((score, n, title))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return scored[:top]


LEVER_PAT = re.compile(
    r"""environ(?:\.get)?\s*[\(\[]\s*["']([A-Z][A-Z0-9_]*)["']\s*(?:,\s*([^\)\]\n]{1,60}))?""")


def levers(folder, prefix="LK_", env_file=None):
    """Every environment-variable LEVER the scripts in `folder` read, which scripts read it, and its
    hardcoded default - straight out of the code, so it cannot be stale. Returns (rows, set_keys).

    WHY. The burrito is not run through a template. It is a chain of project scripts driven by
    environment variables - measured 2026-09-17 on the live folder: **81 distinct `LK_*` levers
    across thirteen scripts, of which `WINNING_ENV.json` sets 17.** The other 64 run on defaults
    hardcoded inside the scripts, and no document lists them; an agent learns a lever by grepping, or
    by not knowing it exists. That is a recorded process failure (*"a script that hardcodes a lever
    stops being a tool and becomes the method"*) and L34, and it is the shape of the client's complaint:
    *"controls put in place that an agent does not yet know how to use."*

    The code is the owner of the vocabulary (README rule 0), so this reads the code rather than
    keeping a second list. `env_file` (a JSON of name -> value, like `WINNING_ENV.json`) marks which
    levers the run actually sets; everything else is running on its default, and that is worth
    seeing before a tuning sweep starts on the wrong knob.
    """
    rows = {}
    if not os.path.isdir(folder):
        return [], set()
    for f in sorted(os.listdir(folder)):
        if not f.endswith(".py") or f.startswith("_kit_"):
            continue
        try:
            src = open(os.path.join(folder, f), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for m in LEVER_PAT.finditer(src):
            name = m.group(1)
            if prefix and not name.startswith(prefix):
                continue
            d = (m.group(2) or "").strip().strip(",").strip()
            e = rows.setdefault(name, {"scripts": [], "default": ""})
            if f not in e["scripts"]:
                e["scripts"].append(f)
            if d and not e["default"]:
                e["default"] = d[:40]
    set_keys = set()
    if env_file and os.path.isfile(env_file):
        try:
            set_keys = set(json.load(open(env_file, encoding="utf-8")))
        except (OSError, ValueError):
            set_keys = set()
    out = [(k, rows[k]["scripts"], rows[k]["default"], k in set_keys) for k in sorted(rows)]
    return out, set_keys


def levers_report(folder, prefix="LK_", env_file=None, only_unset=False):
    rows, set_keys = levers(folder, prefix, env_file)
    if not rows:
        print("[levers] no `%s*` environment reads under %s" % (prefix, folder))
        return 0
    n_set = sum(1 for r in rows if r[3])
    print("[levers] %d lever(s) read by the scripts in %s%s" % (
        len(rows), os.path.basename(folder.rstrip("\\/")) or folder,
        (" - %d set by %s, %d running on a hardcoded default" % (n_set, os.path.basename(env_file), len(rows) - n_set))
        if env_file else ""))
    for name, scripts, default, is_set in rows:
        if only_unset and is_set:
            continue
        mark = "set " if is_set else ("    " if env_file else "")
        print("[levers]   %s%-24s default %-22s %s" % (mark, name, (default or "-")[:22],
                                                     ", ".join(s.replace("job_", "").replace(".py", "") for s in scripts)[:60]))
    if env_file:
        stale = sorted(set_keys - {r[0] for r in rows})
        if stale:
            print("[levers]   SET IN %s BUT READ BY NOTHING: %s" % (os.path.basename(env_file), ", ".join(stale)))
    print("[levers] A lever running on its default is the method deciding for you. Name the one you are turning.")
    return 0



PATH_TOKEN = re.compile(r"`([^`\n]{3,160})`")


def _path_like(tok):
    t = tok.strip()
    if any(c in t for c in "<>*|\"") or "..." in t or " " in t.strip("\\/") and not re.match(r"^[A-Za-z]:\\", t):
        return False
    if not ("\\" in t or "/" in t):
        return False
    if t.startswith(("--", "http", "kit ", "python ", "&")):
        return False
    return bool(re.search(r"[A-Za-z0-9_]", t))


def dead_paths(md_file, roots):
    """[(token, tried)] for every backticked path-shaped token in `md_file` that resolves to nothing
    under any of `roots` (absolute tokens are tried as written first). Placeholders (`<REV>`,
    `*`, `...`) and command lines are skipped - a document may name a shape, not only a file."""
    try:
        txt = open(md_file, encoding="utf-8", errors="replace").read()
    except OSError:
        return []
    seen = set(); out = []
    for m in PATH_TOKEN.finditer(txt):
        tok = m.group(1).strip()
        if tok in seen or not _path_like(tok):
            continue
        seen.add(tok)
        rel = tok.replace("\\", os.sep).replace("/", os.sep).rstrip(os.sep)
        cands = []
        if re.match(r"^[A-Za-z]:", rel) or rel.startswith(os.sep):
            if len([q for q in rel.split(os.sep) if q]) <= 3 and re.match(r"^[A-Za-z]:", rel):
                continue
            cands.append(rel)
            parts = rel.split(os.sep)
            for r in roots:
                for i in range(1, len(parts)):
                    cands.append(os.path.join(r, *parts[i:]))
        else:
            for r in roots:
                cands.append(os.path.join(r, rel))
                cands.append(os.path.join(r, "claude_code", rel))
        if any(os.path.exists(c) for c in cands):
            continue
        base = re.sub(r":\d+(-\d+)?$", "", rel)
        if base != rel and any(os.path.exists(os.path.join(r, base)) or os.path.exists(os.path.join(r, "claude_code", base)) for r in roots):
            continue
        out.append((tok, cands[0] if cands else rel))
    return out



LEVERS_CENSUS = "LEVERS_CENSUS.md"
LEVER_CLASSES = ("CARD", "CONSTANT", "DEAD")
CENSUS_HEAD = """# LEVER CENSUS - every environment-variable lever the scripts in this folder read (generated; the `class` and `note` columns are yours)

**Fill `class` for every row: `CARD`, `CONSTANT` or `DEAD`.** Nothing else in the process reads the code's default as
an answer once this is done: `kit burrito` refuses a step whose CARD levers are not set for the run, by name.

* **CARD** - a number a card decides (it differs per card, piece or region). It must be SET for every run - in the
  run's env file or `--set` - and the value in the example file is the example's decision, not yours.
* **CONSTANT** - an algorithm constant no card changes. The code default IS the value; write why in `note`.
* **DEAD** - read only by scripts that are not in the chain (`in chain` = no) and are not run. Say so in `note`;
  the script is a candidate for removal.
* `in chain` = no means only scripts outside the canonical chain read it; the note names them. Whether they
  are the round's live drivers or dead ends is the classifier's call - the census states the fact and proposes nothing.

`kit levers --check` lists what is still unclassified and which CARD levers the example file sets. Re-run
`kit levers --census` after the scripts change: it keeps every class already given and adds the new rows.

| lever | default in code | read by | in chain | set by example | class | note |
|---|---|---|---|---|---|---|
"""


def census_read(folder):
    """{lever: {"class": "CARD"/"CONSTANT"/"DEAD"/"" (a trailing ? means proposed), "note": str}}"""
    p = os.path.join(folder, LEVERS_CENSUS)
    out = {}
    if not os.path.isfile(p):
        return out
    for line in open(p, encoding="utf-8", errors="replace"):
        if not line.startswith("| ") or line.startswith("| lever") or line.startswith("|---"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 7 or not c[0].startswith("`"):
            continue
        out[c[0].strip("`")] = {"class": c[5].strip().upper(), "note": c[6].strip(),
                                "default": c[1].strip("`"), "scripts": [x.strip().strip("`") for x in c[2].split(",") if x.strip()],
                                "in_chain": c[3].strip().lower() == "yes", "example": c[4].strip().lower() == "yes"}
    return out


def census_write(folder, chain_scripts, env_file=None, prefix="LK_"):
    """Write or MERGE LEVERS_CENSUS.md. Returns (rows_written, unclassified, new_rows)."""
    rows, set_keys = levers(folder, prefix, env_file)
    old = census_read(folder)
    chain = set(os.path.basename(c) for c in (chain_scripts or ()))
    lines = [CENSUS_HEAD]
    unclassified = 0
    new = 0
    seen = set()
    for name, scripts, default, is_set in rows:
        seen.add(name)
        in_chain = any(s in chain for s in scripts)
        prev = old.get(name, {})
        cls = prev.get("class", "")
        note = prev.get("note", "")
        if name not in old:
            new += 1
            if not in_chain:
                note = note or "read only outside the chain (%s)" % ", ".join(scripts)[:60]
        if not cls or cls.endswith("?") or cls.rstrip("?") not in LEVER_CLASSES:
            unclassified += 1
        lines.append("| `%s` | `%s` | %s | %s | %s | %s | %s |\n" % (
            name, (default or "-").replace("|", "/"), ", ".join("`%s`" % s for s in scripts), "yes" if in_chain else "no",
            "yes" if is_set else "no", cls, note.replace("|", "/")))
    gone = sorted(set(old) - seen)
    for name in gone:
        prev = old[name]
        lines.append("| `%s` | `%s` | %s | no | no | %s | %s |\n" % (
            name, prev.get("default", "-"), "(no script reads it now)", prev.get("class", ""),
            ("NO LONGER READ BY ANY SCRIPT. " + prev.get("note", "")).strip()))
    stale = sorted(set_keys - {r[0] for r in rows})
    if stale:
        lines.append("\nSet in `%s` but read by nothing: %s\n" % (os.path.basename(env_file), ", ".join("`%s`" % k for k in stale)))
    _atomic_write(os.path.join(folder, LEVERS_CENSUS), "".join(lines))
    return len(rows), unclassified, new


def _atomic_write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def census_check(folder, env_keys=(), step_script=None):
    """(unclassified [names], card_missing [names], has_census). CARD levers read by `step_script`
    (or by anything, when None) that `env_keys` does not set are `card_missing`."""
    c = census_read(folder)
    if not c:
        return [], [], False
    step = os.path.basename(step_script) if step_script else None
    unclassified = sorted(n for n, v in c.items()
                          if (not v["class"]) or v["class"].endswith("?") or v["class"] not in LEVER_CLASSES)
    missing = sorted(n for n, v in c.items()
                     if v["class"] == "CARD" and n not in set(env_keys)
                     and (step is None or step in v["scripts"]))
    if step:
        unclassified = [n for n in unclassified if step in c[n]["scripts"]]
    return unclassified, missing, True



JOBS = "JOBS.json"


WALL_MIN_DEFAULT = 15


def wall_status(root):
    """[(job, minutes, budget, over?)] for every job that is claimed and not applied.

    THE WALL CLOCK, the client's criterion 2026-09-09: "Keep agents on a wall clock."
    An earlier kit has one and it earned its place — a worker there ran 45 minutes on a task it did
    not need while the parent 'just let it go', and nothing was timing it. This kit's workers are
    far shorter (152 s median across 129 measured jobs, p90 452 s), which is exactly why an
    overrun is worth noticing: a lean job past 15 minutes is not working hard, it is stuck, and
    the usual cause is a card it cannot satisfy.

    Reported, never refused. Stopping a worker is the orchestrator's judgment, and a gate that
    killed one mid-write would lose the RESULT.md that says why it was stuck.
    """
    out = []
    now = time.time()
    for n, j in sorted((_read(_p(root, JOBS), {}) or {}).items()):
        if j.get("applied") or j.get("cancelled") or not j.get("launched"):
            continue
        if j.get("parked") or j.get("handed_back"):
            continue
        jf = os.path.join(root, "claude_code", "jobs", str(n))
        if os.path.isfile(os.path.join(jf, "PARKED.md")) or os.path.isfile(os.path.join(jf, "RESULT.md")):
            continue
        try:
            mins = (now - float(j["launched"])) / 60.0
        except (TypeError, ValueError):
            continue
        budget = j.get("wall_min") or WALL_MIN_DEFAULT
        out.append((n, round(mins, 1), budget, mins > budget))
    return out


FACES_UNSIGNED_MIN = 40      # not taken
def job_open(root, name, edit_type, card=None, tier="haiku", expect_vol=None, expect_faces=None,
             wall_min=None):
    _require_session(root, "job")
    if edit_type not in TYPE_TRAPS:
        refuse("job", ["edit type %r is not one of: %s" % (edit_type, ", ".join(TYPES))])
    # METHOD.md
    purpose, card_vol = "", None
    if not card:
        refuse("job", ["no --card. `kit newcard %s --type %s --write <path>` scaffolds one; `kit card <path>` lints it; "
                       "then `kit job %s --type %s --card <path>`." % (name, edit_type, name, edit_type)])
    if not os.path.exists(card):
        refuse("job", ["the card does not exist: %s" % card])
    _ok, _why = card_passed(root, card)
    if not _ok:
        refuse("job", ["%s - kit card \"%s\" first. The lint is the gate that keeps a haiku worker on task and it is not "
                       "optional for the orchestrator's own run either." % (_why, card)])
    if card and os.path.exists(card):
        try:
            txt = open(card, encoding="utf-8", errors="replace").read()
            m = re.search(r"^\s*Purpose\s*[:=]\s*(.+?)(?:\n\s*\n|\n\s*[A-Z][A-Za-z ]{2,}\s*[:=])",
                          txt, re.S | re.M | re.I)
            if m:
                purpose = " ".join(m.group(1).split())[:400]
            mv = re.search(r"^\s*Expected\s*[:=][^\n]*?(-?\d[\d,]*\.?\d*)\s*mm3", txt,
                           re.M | re.I)
            if mv:
                card_vol = float(mv.group(1).replace(",", ""))
            mf = re.search(r"^\s*Expected\s*[:=][^\n]*?\bfaces?\s*[:=]?\s*(?:about|~|approx\.?|roughly)?\s*([+-]?\s*\d+)", txt, re.M | re.I)
            if mf and expect_faces is None:
                # NOT taken
                try:
                    _fs9 = mf.group(1).replace(" ", ""); _fn9 = int(_fs9)
                    if _fs9[0] in "+-" or abs(_fn9) < FACES_UNSIGNED_MIN:
                        expect_faces = _fn9; expect_faces_signed = _fs9[0] in "+-"
                    else:
                        expect_faces_unsigned = _fn9
                        print("[leangate] the card's face figure %d has NO SIGN and is %d or more - NOT taken as the growth allowance (a figure that size reads as a face COUNT); the Expected line's figure is the NEW faces the edit adds, with its sign: `faces about +N` (`kit card`, then `kit job %s` alone re-reads it) - until then kit check runs its growth check at 40 (31bw)" % (_fn9, FACES_UNSIGNED_MIN, name))
                except ValueError: pass
            ms = re.search(r"^\s*Expected\s*[:=][^\n]*?\bsolids?\s*[:=]?\s*(?:about|~)?\s*(\d+)", txt, re.M | re.I)
            if ms:
                try: expect_solids = int(ms.group(1))
                except ValueError: pass
        except (OSError, ValueError):
            pass

    if card_vol is not None and expect_vol is not None:
        if abs(float(expect_vol) - card_vol) > max(abs(card_vol) * 0.01, 0.5):
            refuse("job", [
                "the card says the expected volume change is %.1f mm3 and --expect-vol says "
                "%.1f.\n  They must agree — they are the same claim written twice, and the "
                "tripwire is only worth\n  something if the number came off the card rather "
                "than off the command line."
                % (card_vol, float(expect_vol))])
    if expect_vol is None:
        expect_vol = card_vol
    jobs = _read(_p(root, JOBS), {})
    prev = jobs.get(name) or {}
    if prev.get("applied"):
        refuse("job", ["%s was APPLIED (%s) — it is in the model of record and is not re-carded; "
                       "a new premise is a new job." % (name, prev.get("applied"))])
    jobs[name] = {"edit_type": edit_type, "card": card, "tier": tier,
                  "expect_vol": expect_vol, "expect_faces": expect_faces, "expect_solids": locals().get("expect_solids"),
                  "expect_faces_signed": locals().get("expect_faces_signed"), "expect_faces_unsigned": locals().get("expect_faces_unsigned"),
                  "card_vol": card_vol, "card_purpose": purpose,
                  "wall_min": int(wall_min) if wall_min else WALL_MIN_DEFAULT,
                  "opened": _now(), "launched": None, "checked": None, "check_json": None,
                  "looked": None, "applied": None,
                  "box": prev.get("box"), "before_dir": prev.get("before_dir"),
                  "before_looked": prev.get("before_looked"),
                  "region": prev.get("region")}
    if prev.get("before_looked"):
        print("[leangate] re-carded: the BEFORE frames and look from %s are kept (same region)."
              % prev.get("before_looked"))
    _write(root, JOBS, jobs)
    print("[leangate] JOB %s registered — type %s, tier %s, wall budget %d min"
          % (name, edit_type, tier, jobs[name]["wall_min"]))
    return jobs[name]


def _check_codes(root, key, codes, label="look"):
    """(verified_names, findings) for one stamped frame set. Shared by BOTH looks.

    Factored out of orchestrator_look when the before-look was added, rather than copied.
    PROTECTED in guard.py was duplicated into two branches once and the copies disagreed within
    a day; proof-of-opening is the last check that cannot be talked past, so it gets exactly one
    implementation.
    """
    rec = codes_for(root, key)
    findings = []
    given = {os.path.basename(str(k)).lower(): str(v).strip().upper()
             for k, v in (codes or {}).items()}
    if not rec:
        findings.append(
            "no stamped codes exist for this %s (%s) — the frames were never stamped, so there "
            "is\n      NO proof of opening to check. The usual cause is Pillow missing from the "
            "kit's Python:\n          & \"<python.exe>\" -m pip install pillow\n      then "
            "re-run the render that makes these frames (kit before / kit render --job) and look "
            "again." % (label, key))
        return [], findings
    salt = rec["salt"]
    by_name = {os.path.basename(it["image"]).lower(): it for it in rec["items"]}
    blank = [os.path.basename(it["image"]) for it in rec["items"] if it.get("blank")]
    good, wrong, unknown = [], [], []
    for k, v in given.items():
        it = by_name.get(k)
        if not it:
            near = [n for n in by_name if k in n or n in k]
            it = by_name[near[0]] if len(near) == 1 else None
        if not it:
            unknown.append(k)
        elif _kdf(v, salt) == it["hash"]:
            good.append(k)
        else:
            wrong.append(k)
    if wrong:
        findings.append(
            "%d code(s) are WRONG: %s.\n      The code is stamped in the header band of the "
            "image and it is ONLY there — it is\n      not in any file. A wrong code means the "
            "picture was not opened, or was misread:\n      enlarge the band before answering "
            "again. The alphabet excludes O/0, I/1, B/8, S/5,\n      Z/2 and G/6, so a confusion "
            "between those is not possible." % (len(wrong), ", ".join(sorted(wrong))))
    if unknown:
        findings.append("%d code(s) name a picture this job did not render: %s"
                        % (len(unknown), ", ".join(sorted(unknown))))
    if len(good) < min(MIN_CODES, len(by_name)):
        findings.append(
            "only %d verified code(s); %d are required.\n"
            "      THIS IS THE CHECK THAT CANNOT BE TALKED PAST. A specific-sounding observation\n"
            "      costs nothing to invent. Open the frames, read the code out of the header "
            "band,\n      and pass them. Frames rendered:\n        %s"
            % (len(good), min(MIN_CODES, len(by_name)),
               "\n        ".join(sorted(by_name)[:10])))
    if blank:
        findings.append(
            "%d frame(s) drew almost nothing and cannot show anything: %s.\n"
            "      That is measured off the pixels, not judged. Re-render with a box that "
            "contains\n      the subject before reading them." % (len(blank), ", ".join(blank)))
    return good, findings


def before_key(name):
    return "%s::before" % name


def before_look(root, name, says, codes=None):
    """The orchestrator's OWN look at the CURRENT state of the region, before any edit."""
    _require_session(root, "before-look")
    j = job(root, name)
    if not j:
        refuse("before-look", ["job %r was never registered" % name])
    if not j.get("before_dir"):
        refuse("before-look", ["no BEFORE frames exist for %r yet" % name],
               "Render them first — once, by the one who understands the change:\n"
               "    kit before %s --box x0 x1 y0 y1 z0 z1" % name)
    ok, findings = _check_codes(root, before_key(name), codes)
    lines = [t.strip() for t in (says or []) if str(t).strip()]
    if not lines:
        findings.append("say what you SAW — one line per frame, about the geometry.")
    elif any(_LAZY.match(t) for t in lines):
        findings.append("'%s' is agreement, not an observation. What is actually THERE?"
                        % next(t for t in lines if _LAZY.match(t)))
    if findings:
        refuse("before-look", findings,
               "This is the look that stops a round being spent on the wrong plan. The handoff's\n"
               "numbers are not evidence; the picture is.")
    looks = _read(_p(root, LOOKS), {})
    looks[before_key(name)] = {"when": _now(), "says": lines, "codes": sorted(ok)}
    _write(root, LOOKS, looks)
    job_mark(root, name, "before_looked", _now())
    print("[leangate] BEFORE-LOOK recorded for %s — %d frame(s) opened." % (name, len(ok)))
    return True


def require_before_look(root, name):
    """Refuse to launch a worker on a region nobody has looked at."""
    j = job(root, name) or {}
    if j.get("before_looked"):
        return True
    refuse("launch", [
        "RENDER FIRST — %r has never been looked at.\n"
        "  No BEFORE frames were opened, so this job is carded from numbers alone." % name],
        "Two commands, and they cost one render:\n"
        "    kit before %s --box x0 x1 y0 y1 z0 z1\n"
        "    kit beforelook %s --saw <frame>=<CODE> ... --says \"what is actually there\"\n"
        "\n"
        "  The frames go on the worker's card, so the render is generated once and by the one\n"
        "  who understands the change. On 2026-09-09 this is what caught a handoff that called\n"
        "  for two jobs when the geometry needed four — before the round was spent." % (name, name))


def job_cancel(root, name, why):
    """Retire a job whose PREMISE is disproved — the register learns what the orchestrator knew.

    the project P29, 2026-09-09/10: TIPNOSE_P was cancelled with a full RESULT.md saying the crease it
    was carded to remove does not exist. The register did not know: `kit status` listed it every
    call, the wall clock ran on it for a day, and `kit close` wrote it into the handoff under
    "NOT applied — pick these up first" — so the next session's first instruction was to resume a
    job with a disproved premise. The next brief had to name it by hand, which is the
    file-beside-the-kit failure in miniature.

    A cancelled job stays in the register (a decision is a record), leaves the clock, is refused
    by accept/apply/launched, and appears in the handoff under its own heading WITH the reason —
    the reason is the whole value: it is the premise the next orchestrator must not re-buy.
    An APPLIED job cannot be cancelled: it is in the model of record, and undoing it is a new job.
    """
    _require_session(root, "cancel")
    j = job(root, name)
    if not j:
        refuse("cancel", ["job %r was never registered — there is nothing to cancel" % name])
    if j.get("applied"):
        refuse("cancel", ["%s was APPLIED (%s) — it is in the model of record. An applied job is "
                          "not cancelled, it is reverted by a NEW job with its own card and check."
                          % (name, j.get("applied"))])
    if not str(why or "").strip():
        refuse("cancel", ["--why is required: the premise that failed, in one line, so the next "
                          "orchestrator does not re-buy it.\n      kit cancel %s --why \"the crease "
                          "the card removes does not exist: dihedral 0.00 on all three nose edges\""
                          % name])
    job_mark(root, name, "cancelled", _now())
    job_mark(root, name, "cancel_why", str(why).strip())
    print("[leangate] %s CANCELLED — %s\n[leangate]   off the wall clock; refused by launched / "
          "accept / apply; listed in the handoff under CANCELLED with that reason."
          % (name, str(why).strip()))
    return job(root, name)


def job_stub(root, name):
    """A job folder exists (`kit newjob`) but no card yet: a STUB record, so `kit before` and
    `kit beforelook` can run BEFORE the card is written — which is what render-first means.
    R18 friction log 12:28: the brief said newjob → before → beforelook → card → job, and the
    kit refused `before` on an unregistered job, so the picture came AFTER the card. `kit job`
    replaces the stub and keeps its box / before frames / look; `kit launched` refuses a stub."""
    jobs = _read(_p(root, JOBS), {}) or {}
    if name in jobs:
        return jobs[name]
    jobs[name] = {"edit_type": None, "card": None, "tier": None, "expect_vol": None,
                  "expect_faces": None, "card_vol": None, "card_purpose": "",
                  "wall_min": WALL_MIN_DEFAULT, "opened": None, "launched": None, "checked": None,
                  "check_json": None, "looked": None, "applied": None, "box": None,
                  "before_dir": None, "before_looked": None, "region": None,
                  "stub": True, "stubbed": _now()}
    _write(root, JOBS, jobs)
    print("[leangate] %s: no card yet — a stub record holds the BEFORE frames until `kit job` "
          "registers the card (render first, then write the card from the picture)." % name)
    return jobs[name]


def job_launched(root, name):
    """Start this job's wall clock. Called when the worker is actually spawned."""
    j0 = job(root, name) or {}
    if j0.get("stub"):
        refuse("launched", ["%s has BEFORE frames but no card — write the card from them, then "
                            "kit job %s --type <t> --card <path>" % (name, name)])
    if j0.get("cancelled"):
        refuse("launched", ["%s was CANCELLED %s — %s.\n      A cancelled job is not relaunched; "
                            "a new premise is a new job with its own card."
                            % (name, j0.get("cancelled"), j0.get("cancel_why", ""))])
    require_before_look(root, name)
    job_mark(root, name, "launched", time.time())
    j = job(root, name)
    print("[leangate] %s launched — wall budget %d min. `kit status` shows the clock."
          % (name, j.get("wall_min") or WALL_MIN_DEFAULT))
    return j


def job_elapsed(root, name):
    """Freeze this job's duration when it finishes. Returns minutes, or None.

    THE CLOCK WAS INVISIBLE AND KEPT NOTHING. A test orchestrator scored it 3/10 on
    2026-09-09: it reported only jobs "claimed and not applied", so a job applied seconds after
    launch never appeared, and **nothing recorded how long a finished job took** — `kit close`
    had five timestamps and computed no durations. A clock you can only read during a window you
    were not watching is not a clock; it is a coincidence.

    So the duration is frozen at the moment the job is applied, and it lands in the handoff.
    That is what makes the NEXT round's budgets real instead of guessed.
    """
    j = job(root, name) or {}
    if j.get("elapsed_min") is not None:
        return j["elapsed_min"]
    try:
        mins = round((time.time() - float(j["launched"])) / 60.0, 1)
    except (TypeError, ValueError, KeyError):
        return None
    job_mark(root, name, "elapsed_min", mins)
    budget = j.get("wall_min") or WALL_MIN_DEFAULT
    if mins > budget:
        print("[leangate] %s took %.1f min against a %d min budget — OVER. Worth a line in the "
              "handoff\n[leangate]   about why, so the next card of this type is budgeted "
              "honestly." % (name, mins, budget))
    else:
        print("[leangate] %s took %.1f min (budget %d)." % (name, mins, budget))
    return mins


def job(root, name):
    return (_read(_p(root, JOBS), {}) or {}).get(name)


def job_mark(root, name, key, value):
    jobs = _read(_p(root, JOBS), {})
    if name not in jobs:
        refuse("job", ["job %r was never registered — kit job %s --type <edit_type>"
                       % (name, name)])
    jobs[name][key] = value
    _write(root, JOBS, jobs)
    return jobs[name]


# recorded
# recorded

LOOK_ALPHABET = "ACEFHJKLMNPRTUWXY349"
LOOK_LEN = 5
CODES = "CODES.json"


def _kdf(code, salt):
    import hashlib
    return hashlib.sha256((salt + "|" + str(code).strip().upper()).encode()).hexdigest()


def new_code():
    return "".join(LOOK_ALPHABET[b % len(LOOK_ALPHABET)]
                   for b in os.urandom(LOOK_LEN * 4)[:LOOK_LEN])


def codes_record(root, job, items, salt):
    """items: [{"image":<path>, "hash":<kdf>, "blank":<bool>}]. Plaintext NEVER lands here."""
    st = _read(_p(root, CODES), {})
    st[job] = {"salt": salt, "when": _now(), "items": items}
    _write(root, CODES, st)
    return st[job]


def codes_for(root, job):
    return (_read(_p(root, CODES), {}) or {}).get(job)


def purge_old_looks(root, keep_applied=False):
    """A NEW SESSION CLEARS LAST SESSION'S STAMPED FRAMES AND THEIR CODES.

    the client, 2026-09-09: "have new sessions clean out old files of these. They create gate check
    errors, aren't relevant, and eat disk space." All three are true and the first is the one
    that bites: a stale code record makes `kit look` ask for frames that belong to a finished
    job, and a refusal about last week's pictures is indistinguishable from a real one.

    Deletes the stamped PNGs of jobs that were already APPLIED, and their code records. An
    unapplied job is left alone — its pictures are still the evidence for work someone has to
    pick up, and this project's whole handoff discipline rests on that surviving a restart.
    """
    st = _read(_p(root, CODES), {}) or {}
    jobs = _read(_p(root, JOBS), {}) or {}
    freed, gone = 0, []
    for job_name, rec in list(st.items()):
        j = jobs.get(job_name) or {}
        if (not j.get("applied") or (str(j.get("edit_type") or "") == "burrito" and not j.get("applied_to"))) and not keep_applied:
            continue                       # kit accept
        for it in rec.get("items") or []:
            p = it.get("image")
            try:
                if p and os.path.exists(p):
                    freed += os.path.getsize(p)
                    os.remove(p)
            except OSError:
                pass
        st.pop(job_name, None)
        gone.append(job_name)
    if gone:
        _write(root, CODES, st)
        print("[leangate] cleared stamped frames for %d finished job(s) — %s (%.1f MB freed).\n"
              "[leangate]   Unapplied jobs keep their pictures: they are the evidence for work "
              "somebody\n[leangate]   still has to pick up." % (len(gone), ", ".join(sorted(gone)),
                                                               freed / 1e6))
    return gone


LOOKS = "LOOKS.json"
_LAZY = re.compile(r"^\s*(ok|fine|good|looks? (ok|good|fine|right)|as expected|correct|pass|"
                   r"no issues?|nothing wrong|hit)\s*[.!]?\s*$", re.I)


MIN_CODES = 3


def orchestrator_look(root, name, says, pictures=None, codes=None):
    """Record the orchestrator's OWN reading of the job's pictures.

    Three checks that fail independently:
      1. CODES — at least MIN_CODES frames opened and their stamped codes typed back. This is
         the only one that cannot be satisfied without opening a file.
      2. SPECIFICITY — no bare agreement. "Looks right" is what the worker's HIT already said.
      3. THE PURPOSE SENTENCE — printed back, so the picture is checked against what the feature
         is FOR rather than against the numbers you wrote (METHOD.md 10).
    """
    _require_session(root, "look")
    j = job(root, name)
    if not j:
        refuse("look", ["job %r was never registered" % name])
    lines = [s.strip() for s in (says or []) if str(s).strip()]
    findings = []

    rec = codes_for(root, name)
    given = {os.path.basename(str(k)).lower(): str(v).strip().upper()
             for k, v in (codes or {}).items()}
    if rec:
        salt = rec["salt"]
        by_name = {os.path.basename(it["image"]).lower(): it for it in rec["items"]}
        blank = [os.path.basename(it["image"]) for it in rec["items"] if it.get("blank")]
        good, wrong, unknown = [], [], []
        for k, v in given.items():
            it = by_name.get(k)
            if not it:
                near = [n for n in by_name if k in n or n in k]
                it = by_name[near[0]] if len(near) == 1 else None
            if not it:
                unknown.append(k)
            elif _kdf(v, salt) == it["hash"]:
                good.append(k)
            else:
                wrong.append(k)
        if wrong:
            findings.append(
                "%d code(s) are WRONG: %s.\n      The code is stamped in the header band of the "
                "image and it is ONLY there — it is\n      not in any file. A wrong code means "
                "the picture was not opened, or was misread:\n      enlarge the band before "
                "answering again. The alphabet excludes O/0, I/1, B/8, S/5, Z/2\n      and G/6, "
                "so a confusion between those is not possible."
                % (len(wrong), ", ".join(sorted(wrong))))
        if unknown:
            findings.append("%d code(s) name a picture this job did not render: %s"
                            % (len(unknown), ", ".join(sorted(unknown))))
        if len(good) < min(MIN_CODES, len(by_name)):
            findings.append(
                "only %d verified code(s); %d are required.\n"
                "      THIS IS THE CHECK THAT CANNOT BE TALKED PAST. A specific-sounding "
                "observation costs\n      nothing to invent — a test orchestrator wrote one "
                "about a frame it had not opened and\n      this gate accepted it, which is the "
                "failure the gate exists to stop. Open the frames,\n      read the code out of "
                "the header band, and pass them:\n"
                "          %s\n"
                "      Frames rendered for this job:\n        %s"
                % (len(good), min(MIN_CODES, len(by_name)), (("kit beforelook %s --saw <picture>=<CODE> --saw ... --says \"...\"" % str(name)[:-8]) if str(name).endswith("::before") else ("kit look %s --code <picture>=<CODE> --code ... --says \"...\"" % name)),
                   "\n        ".join(sorted(by_name)[:10])))
        if blank:
            findings.append(
                "%d frame(s) drew almost nothing and cannot show anything: %s.\n"
                "      That is measured off the pixels, not judged. Re-render with a box that "
                "contains the\n      subject before reading them." % (len(blank), ", ".join(blank)))
        unboxed = [os.path.basename(it["image"]) for it in rec["items"]
                   if it.get("boxed") is False]
        if j.get("box") and unboxed:
            findings.append(
                "%d frame(s) were rendered WITHOUT the job's box (the whole body, ~0.35 mm/px): "
                "%s.\n      This job's box is `%s`; a feature a few mm across is a few pixels in "
                "those frames and\n      nothing honest can be read off them. Re-render:\n"
                "          kit render <result.brep> --out <job>/after --name look --job %s\n"
                "      (`--job` alone now uses the job's recorded box)."
                % (len(unboxed), ", ".join(sorted(unboxed)[:6]), j.get("box"), name))
    else:
        findings.append(
            "no stamped codes exist for %s — its pictures were never stamped (made before codes "
            "existed,\n      by something other than `kit render --job`, or with Pillow missing "
            "from the kit's Python:\n          & \"<python.exe>\" -m pip install pillow ).\n"
            "      Re-render with `kit render <result.brep> --out <job>/after --name look --job %s`"
            " and look again." % (name, name))

    if len(lines) < 3:
        findings.append("only %d observation(s). The standard sweep is six views; read at least "
                        "three of them, and say which." % len(lines))
    lazy = [l for l in lines if _LAZY.match(l)]
    if lazy:
        findings.append("these say agreement and nothing else: %s\n      An observation names "
                        "what is IN the picture — 'the pocket floor is flat and the aft wall is "
                        "full height'. 'Looks right' is not a reading, and it is exactly what a "
                        "worker's HIT already told you." % "; ".join(repr(l) for l in lazy[:3]))
    purpose = str((j.get("card_purpose") or "")).strip()
    if findings:
        refuse("look", findings,
               "a recorded lesson: a worker will report HIT against its own render and still be "
               "wrong about\n  the number. a recorded lesson, the client: \"Orbit renders are the only "
               "reliable check. If it were\n  Claude Code it would be gated and required.\" "
               "This is that gate.\n"
               "  kit look <job> --says \"...\" --says \"...\" --says \"...\"")
    rec = {"when": _now(), "says": lines, "pictures": list(pictures or []),
           "against_purpose": purpose}
    st = _read(_p(root, LOOKS), {})
    st[name] = rec
    _write(root, LOOKS, st)
    job_mark(root, name, "looked", rec["when"])
    print("[leangate] LOOK RECORDED for %s — %d observation(s)." % (name, len(lines)))
    if purpose:
        print("[leangate]   Card purpose: %s" % purpose[:150])
        print("[leangate]   Check the PICTURE against that sentence, not against the numbers you "
              "wrote (METHOD.md 10).")
    return rec



def gate_apply(root, name, check_json=None):
    """Refuse `kit apply` unless this job was checked, looked at, and matched its card."""
    s = _require_session(root, "accept")
    j = job(root, name)
    if not j:
        refuse("accept", ["job %r was never registered — so nothing recorded what it was for, "
                          "what it expected, or whether anyone looked at it." % name])
    if j.get("cancelled"):
        refuse("accept", ["%s was CANCELLED %s — %s.\n      Nothing from a cancelled job reaches "
                          "the model of record." % (name, j.get("cancelled"),
                                                     j.get("cancel_why", ""))])
    findings = []
    if not j.get("checked"):
        findings.append("`kit check` has not passed for this job. It is the instrument: valid, "
                        "one solid, kernel and tessellation agree, nothing changed outside the "
                        "box, no new opening where the card said no punch-through.")
    if not j.get("looked"):
        findings.append("the ORCHESTRATOR has not looked. The worker's HIT lines are its reading "
                        "of its own render; they are not yours.\n      "
                        "kit look %s --says \"...\" --says \"...\" --says \"...\""
                        % name)

    # recorded
    cj = _read(check_json, {}) if check_json else {}
    if not cj and j.get("check_json"):
        cj = _read(j["check_json"], {})          # recorded
    # recorded
    _local = cj.get("dvol_local")
    _skin = bool(cj.get("skin_piece")) or _local is not None
    got = _local if _local is not None else cj.get("dvol_tess", cj.get("dvol_kernel",
                                     cj.get("volume_change", cj.get("dvol"))))
    want = j.get("expect_vol")
    _matched = False      # matching its card
    _by = ("the local ruler (the piece against the region's content)" if _local is not None else
           ("the whole-body mesh delta - the local ruler was NOT taken%s" % ((": " + str(cj.get("dvol_local_failed"))[:80]) if cj.get("dvol_local_failed") else "") if _skin else "the whole-body mesh delta"))
    _parts = ", ".join("the %s %s" % (nm_, v_) for nm_, v_ in (("kernel", cj.get("dvol_local_kernel")), ("meshes", cj.get("dvol_local_mesh"))) if v_ is not None)
    if got is None and want is not None and not _skin:
        findings.append("VOLUME: the check holds NO volume change (no dvol_local / dvol_tess / dvol_kernel%s) against the card's Expected %s - the tripwire that caught three bad cuts has nothing to judge.\n"
                        "      Run `kit check` again and read its CHECK.json; a check that cannot measure the change is not a pass (31bq R7g)." % ("; the record is missing or unreadable" if not cj else "", want))
    elif got is None:
        print("[leangate] VOLUME: the check recorded NO volume change (no dvol_local / dvol_tess / dvol_kernel) - nothing judged against the card's Expected %s (31bq B21)" % want)
    elif want is None:
        print("[leangate] VOLUME CHANGE %s mm3 by %s%s - the card has no Expected volume: reported, not judged (31bq B21)" % (got, _by, (" (%s)" % _parts) if _parts else ""))
    else:
        try:
            w, g = float(want), float(got)
            _spread = float(cj.get("dvol_local_spread") or 0.0) if _local is not None else 0.0
            tol = max(abs(w) * 0.05, 1.0, _spread)
            if _skin:
                print("[leangate] VOLUME CHANGE %.1f mm3 by %s%s against the card's %.1f - reported, not judged; the pictures decide (31bq B21)."
                      % (g, _by, (" (%s; the ruler's own spread %.0f)" % (_parts, _spread)) if _parts else "", w))
            elif abs(g - w) > tol:
                findings.append(
                    "VOLUME CHANGE %.1f (the whole-body mesh delta) against the card's expected %.1f (%.0f%% out; the tolerance %.0f).\n"
                    "      This is the tripwire that caught three bad cuts. It fires either "
                    "because the piece is\n      wrong or because the CARD's arithmetic is — and "
                    "on this project's record it is usually\n      the card. Do not apply. "
                    "Re-derive the expectation, and if the card was wrong say so in\n"
                    "      the failure log so the next card does not repeat it."
                    % (g, w, 100 * abs(g - w) / max(abs(w), 1e-9), tol))
            else:
                _matched = True
        except (TypeError, ValueError):
            print("[leangate] VOLUME: the card's Expected (%r) or the check's numbers (%r / local %r) are not numbers - the change is reported, not judged (31bq B21)" % (want, got, _local))

    if findings:
        refuse("accept", findings,
               "This is the last gate before the model of record. Everything past it is applied "
               "geometry.")
    job_mark(root, name, "applied", _now())
    job_elapsed(root, name)
    print("[leangate] APPLY GATE PASSED for %s — checked, looked at%s."
          % (name, ", and matching its card" if _matched else "; the volume change as said above - reported, not judged against the card (31bq B21)"))
    print("[leangate]   model of record: %s" % s.get("model_of_record"))
    return True



FAILURES = "FAILURES.md"


def record_failure(root, what, why, fix, signature, job_name="", caught=""):
    _require_session(root, "failure")
    findings = [n for n, v in (("what", what), ("why", why), ("fix", fix),
                               ("signature", signature)) if not str(v or "").strip()]
    if findings:
        refuse("failure", ["missing: %s" % ", ".join(findings)],
               "All four, one call:\n"
               "    kit failure --what \"<what went wrong, observed>\" \\\n"
               "        --why \"<the mechanism>\" --fix \"<what was done>\" \\\n"
               "        --signature \"<what you would SEE that should make the next one suspect "
               "this>\"\n\n"
               "  `signature` is the one that makes a log searchable from inside a problem. On "
               "the part\n  ledger 88 % of 415 rows have none, and the commonest words in the "
               "operation column are\n  'part', 'mesh', 'face' — no index at all.")
    p = os.path.join(records_root(root), FAILURES)
    new = not os.path.exists(p)
    with open(p, "a", encoding="utf-8") as fh:
        if new:
            fh.write("# FAILURES — one row each. All four fields are required.\n\n"
                     "Append-only: rows are numbered in file order and never edited or deleted. A row whose "
                     "*what happened* begins `RESOLVED: row N` closes row N. The kit only writes here; "
                     "`LEAN_KIT\\failures_review.py <project>` is the review (numbered, open vs "
                     "resolved) and the way to close a row.\n\n"
                     "| when | job | caught by | what happened | why | fix | signature |\n"
                     "|---|---|---|---|---|---|---|\n")
        fh.write("| %s | %s | %s | %s | %s | %s | %s |\n"
                 % (_now(), job_name or "-", (caught or "unknown").strip().lower(),
                    str(what).replace("|", "/"), str(why).replace("|", "/"),
                    str(fix).replace("|", "/"), str(signature).replace("|", "/")))
    print("[leangate] failure recorded in %s" % FAILURES)
    measure_reset(root)          # recorded
    return p


def caught_tally(root):
    """WHO CAUGHT IT. Two opposite facts about a process are recorded identically today: a fault a GATE
    refused, and a fault the USER had to point out. The first is the process working. The second is the
    process not existing. the client, 2026-09-21, on a file of 343 such incidents: *"being fixed afterwards is
    not the same as having listened."* Counting them is the only honest measure of whether any of this
    machinery is doing anything, and it is one pass over the register.
    Returns {"gate": n, "ad": n, "self": n, "unknown": n}."""
    out = {"gate": 0, "user": 0, "self": 0, "unknown": 0}
    p = os.path.join(records_root(root), FAILURES)
    if not os.path.exists(p):
        return out
    for ln in open(p, encoding="utf-8", errors="replace"):
        if not ln.startswith("|") or ln.startswith("|---") or " when " in ln[:12]:
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if any(c.startswith("RESOLVED:") for c in cells[2:4]):
            continue
        if len(cells) < 7:
            out["unknown"] += 1
            continue
        k = cells[2].lower()
        out[k if k in out else "unknown"] += 1
    return out



def status(root):
    s = session(root)
    jobs = _read(_p(root, JOBS), {}) or {}
    out = {"session": s, "jobs": jobs}
    if not s:
        print("[leangate] NO SESSION OPEN in %s" % root)
        print("[leangate]   kit exam    then    kit open ...")
    else:
        print("[leangate] session opened %s — model of record: %s"
              % (s.get("opened"), s.get("model_of_record")))
    if jobs:
        print("[leangate] jobs:")
        for n, j in sorted(jobs.items()):
            if j.get("cancelled"):
                print("[leangate]   %-24s %-16s CANCELLED %s — %s"
                      % (n, j.get("edit_type"), j.get("cancelled"), j.get("cancel_why", "")))
                continue
            print("[leangate]   %-24s %-16s checked:%-5s looked:%-5s applied:%s"
                  % (n, j.get("edit_type"), bool(j.get("checked")), bool(j.get("looked")),
                     bool(j.get("applied"))))
        stuck = [n for n, j in jobs.items()
                 if j.get("checked") and not j.get("applied") and not j.get("cancelled")]
        if stuck:
            print("[leangate] %d job(s) checked but not applied: %s"
                  % (len(stuck), ", ".join(sorted(stuck))))
    for n, mins, budget, over in wall_status(root):
        if over:
            print("[leangate] *** %s is %.0f min PAST its %d min budget. A lean job past its "
                  "budget is\n[leangate]     not working hard, it is stuck — and the usual cause "
                  "is a card it cannot\n[leangate]     satisfy. Read its RESULT.md; if there is "
                  "none, ask it for one before killing it." % (n, mins - budget, budget))
        else:
            print("[leangate] %s in flight %.0f of %d min" % (n, mins, budget))
    return out


HANDOFF = "SESSION_HANDOFF.md"


PROCESS_IMPROVEMENTS = "PROCESS_IMPROVEMENTS.md"


def close(root, note="", next_up="", improvements=None, facts=None, remaining=None,
          no_improvements="", no_facts=""):
    """END OF SESSION: write down where this got to, for whoever opens the project next.

    the client's criterion, 2026-09-09: "Record state of where it is at the end of sessions."

    It is written from the REGISTERS, not from memory — what was applied, what is half-done, what
    the model of record is now. That distinction is the whole point: a handoff composed from
    recollection is exactly as reliable as the recollection, and a compaction destroys that while
    leaving every register on disk intact. An earlier kit's hardest-won rule is the same one —
    read the folders, not the messages.
    """
    s = session_record(root)
    jobs = _read(_p(root, JOBS), {}) or {}
    applied = [(n, j) for n, j in sorted(jobs.items()) if j.get("applied")]
    cancelled = [(n, j) for n, j in sorted(jobs.items())
                 if j.get("cancelled") and not j.get("applied")]
    open_j = [(n, j) for n, j in sorted(jobs.items())
              if not j.get("applied") and not j.get("cancelled")]

    findings = []
    if not improvements and not str(no_improvements).strip():
        findings.append(
            "no process improvements, and no reason given for having none.\n"
            "      Anything that made the MACHINERY harder to use this session — a refusal whose "
            "remedy did\n      not run, a command you wanted and could not find, a document that "
            "contradicted another.\n      Write it while you still remember what you were doing "
            "when it bit; that context is the\n      part that makes a fix land in the right "
            "place.\n"
            "          --improvement \"<what bit, and where>\"   (repeatable)\n"
            "          --no-improvements \"<why there is genuinely nothing>\"")
    if not facts and not str(no_facts).strip():
        findings.append(
            "no new project facts, and no reason given for having none.\n"
            "      Every number you MEASURED this session that the next session would otherwise "
            "measure again:\n      a wall thickness, a clearance, a face index, an insert depth. "
            "FACTS.md is the file that\n      stops a project re-deriving itself every round.\n"
            "          --fact \"<the number and what it is of>\"   (repeatable)\n"
            "          --no-facts \"<why nothing was learned that is worth keeping>\"")
    if not str(remaining or "").strip():
        findings.append(
            "no statement of WHAT REMAINS.\n"
            "      A handoff that lists what was done and not what is left hands the next "
            "session a page of\n      finished things. Say where the design actually stands and "
            "what the next piece of work is.\n          --remaining \"<where the design stands; "
            "what is still to do>\"")
    if findings:
        refuse("close", findings,
               "These are the client's three, and the session is not closed until they are answered. "
               "Two of them\n  accept 'nothing to add' WITH A REASON — what is refused is "
               "silence, because silence and\n  having forgotten look identical to whoever reads "
               "this next.")

    lines = ["# SESSION HANDOFF — %s" % _now(), ""]
    if s:
        lines += ["**Model of record: `%s`**" % s.get("model_of_record"),
                  "", "Session opened %s. State read at open: %s"
                  % (s.get("opened"), s.get("state_read")), ""]
        for p in (s.get("promotions") or []):
            lines.append("- promoted `%s` -> `%s` (%s)%s"
                         % (p.get("from"), p.get("to"), p.get("when"),
                            ("  — " + p["note"]) if p.get("note") else ""))
        if s.get("promotions"):
            lines.append("")
    if note:
        lines += ["## What happened", "", note, ""]
    lines += ["## Applied this session (%d)" % len(applied), ""]
    lines += ["- **%s** (%s) applied %s%s%s" %
              (n, j.get("edit_type"), j.get("applied"),
               ("  [%.1f min of %s budgeted]" % (j["elapsed_min"], j.get("wall_min")))
               if j.get("elapsed_min") is not None else "",
               ("  — " + j["card_purpose"]) if j.get("card_purpose") else "")
              for n, j in applied] or ["- nothing"]
    _durs = [j["elapsed_min"] for _, j in applied if j.get("elapsed_min") is not None]
    if _durs:
        lines += ["", "%d job(s) timed: median %.1f min, slowest %.1f. **These are the numbers "
                  "to budget the next round from** — a guessed budget is how a stuck worker goes "
                  "unnoticed." % (len(_durs), sorted(_durs)[len(_durs) // 2], max(_durs))]
    lines += ["", "## NOT applied — pick these up first (%d)" % len(open_j), ""]
    if open_j:
        for n, j in open_j:
            missing = [w for w, k in (("checked", "checked"), ("looked at by you", "looked"))
                       if not j.get(k)]
            lines.append("- **%s** (%s) — %s%s"
                         % (n, j.get("edit_type"),
                            ("still needs: " + ", ".join(missing)) if missing
                            else "checked and looked at; needs `kit accept` then `kit apply`",
                            ("  [card: %s]" % j["card"]) if j.get("card") else ""))
    else:
        lines.append("- nothing")
    if cancelled:
        lines += ["", "## CANCELLED — premise disproved, do NOT re-card (%d)" % len(cancelled), ""]
        lines += ["- **%s** (%s) cancelled %s — %s" % (n, j.get("edit_type"), j.get("cancelled"),
                                                       j.get("cancel_why", ""))
                  for n, j in cancelled]
    lines += ["", "## WHERE THE DESIGN STANDS / WHAT REMAINS", "",
              str(remaining).strip(), ""]
    if facts:
        _fname = "FACTS.md" if os.path.exists(os.path.join(root, "FACTS.md")) or not os.path.exists(os.path.join(root, "PROJECT_FACTS.md")) else "PROJECT_FACTS.md"
        lines += ["## New facts measured this session", "",
                  "*Appended to `%s`. A number measured and not written down is a number "
                  "the next session measures again.*" % _fname, ""]
        lines += ["- %s" % f for f in facts]
        lines.append("")
    elif no_facts:
        lines += ["## New facts", "", "None — %s" % no_facts, ""]
    if improvements:
        lines += ["## Process improvements", "",
                  "*Appended to `%s`.*" % PROCESS_IMPROVEMENTS, ""]
        lines += ["- %s" % i for i in improvements]
        lines.append("")
    elif no_improvements:
        lines += ["## Process improvements", "", "None — %s" % no_improvements, ""]
    if next_up:
        lines += ["## Next", "", next_up, ""]
    lines += ["", "---", "",
              "*Written by `kit close` from the gate registers, not from memory. If this "
              "disagrees with", "the conversation above it, THIS is right — it was read off "
              "disk.*", ""]
    p = os.path.join(root, HANDOFF)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("[leangate] handoff written: %s" % p)
    print("[leangate]   %d applied, %d still open." % (len(applied), len(open_j)))

    # recorded
    if improvements:
        pi = os.path.join(root, PROCESS_IMPROVEMENTS)
        new = not os.path.exists(pi)
        try:
            with open(pi, "a", encoding="utf-8") as fh:
                if new:
                    fh.write("# PROCESS IMPROVEMENTS\n\nFriction in the MACHINERY — the kit, the "
                             "gates, the docs, the way a session runs.\nA geometry failure goes "
                             "in FAILURES.md instead. Each entry says what was HAPPENING\nwhen it "
                             "bit, because a fix with no context gets misapplied.\n")
                fh.write("\n## %s\n\n" % _now())
                for i in improvements:
                    fh.write("- %s\n" % i)
            print("[leangate]   %d improvement(s) -> %s" % (len(improvements), PROCESS_IMPROVEMENTS))
        except OSError as exc:
            print("[leangate]   could NOT write %s (%s) — it may be guard-protected. The entries "
                  "are in the\n[leangate]   handoff; move them across under .claude/unlock."
                  % (PROCESS_IMPROVEMENTS, exc))
    if facts:
        fp = os.path.join(root, "FACTS.md")
        if not os.path.exists(fp) and os.path.exists(os.path.join(root, "PROJECT_FACTS.md")):
            fp = os.path.join(root, "PROJECT_FACTS.md")
        try:
            with open(fp, "a", encoding="utf-8") as fh:
                fh.write("\n## Measured %s\n\n" % _now())
                for f in facts:
                    fh.write("- %s\n" % f)
            print("[leangate]   %d fact(s) -> %s" % (len(facts), os.path.basename(fp)))
        except OSError as exc:
            print("[leangate]   could NOT write %s (%s) — it is guard-protected. The facts "
                  "are in the\n[leangate]   handoff; move them across under .claude/unlock: %s"
                  % (os.path.basename(fp), exc, "; ".join(facts)[:200]))
    try:
        _rec = _read(_p(root, SESSION), None)
        if _rec and not _rec.get("closed"):
            _rec["closed"] = _now()
            _write(root, SESSION, _rec)
            print("[leangate] session CLOSED (handoff written AND session ended - nothing else to run)")
        else:
            print("[leangate] handoff written; the session was already closed or absent")
    except Exception as _e:
        print("[leangate] handoff written, but the session record could NOT be stamped closed (%s).\n"
              "[leangate]   The Stop hook will still see an open session - `kit stop --why \"...\"` is "
              "the way out." % _e)
    try:
        _t = caught_tally(root)
        if sum(_t.values()):
            print("[leangate]   caught by GATE %d · by the client %d · by the agent itself %d · unrecorded %d"
                  % (_t["gate"], _t["user"], _t["self"], _t["unknown"]))
            if _t["user"] > _t["gate"]:
                print("[leangate]   the client is catching more than the gates are. That is the number to move, "
                      "and it moves by\n[leangate]   building a refusal where the client had to speak, not by "
                      "writing the rule down again.")
    except Exception:
        pass
    return p


FINE_STD_SPACING = 0.5
FINE_MAX_CELLS = 40000
FINE_HOUR_CELLS = 120000
FINE_LOG = "FINE_LOG.md"

def _card_plan(folder, card):
    """spacing and the footprint's plan area (mm2) and box, read off the card's PARAMS text; None when unreadable"""
    import re, ast
    try:
        txt = open(os.path.join(folder, card), encoding="utf-8", errors="replace").read()
    except Exception:
        return None
    m = re.search(r"\bspacing\s*=\s*([0-9.]+)", txt); sp = float(m.group(1)) if m else FINE_STD_SPACING
    m = re.search(r"\bfootprint\s*=\s*(\[.*?\])", txt, re.S)
    if not m: return {"spacing": sp, "area": None, "box": None}
    try:
        pts = ast.literal_eval(re.sub(r"#.*", "", m.group(1)))
        xs = [float(p[0]) for p in pts]; ys = [float(p[1]) for p in pts]
        area = 0.5 * abs(sum(xs[i] * ys[(i + 1) % len(pts)] - xs[(i + 1) % len(pts)] * ys[i] for i in range(len(pts))))
        return {"spacing": sp, "area": area, "box": (min(xs), max(xs), min(ys), max(ys))}
    except Exception:
        return {"spacing": sp, "area": None, "box": None}

def fine_gate(folder, env, fine_args, tag):
    """the S3 door: returns {} for a standard run, {'announce': line} for an allowed fine run (also logged),
    {'refused': why} for one that is too big, unannounced, or a piece of a bigger one"""
    import time, json
    card = env.get("LK_CARD") or ""
    plan = _card_plan(folder, card) if card else None
    if not plan or plan["spacing"] >= FINE_STD_SPACING - 1e-9:
        return {}
    sp = plan["spacing"]; area = plan["area"]
    if area is None:
        return {"refused": "%s samples at %.3f mm (fine) but its footprint could not be read, so its size cannot be gated. "
                           "Write the footprint as a plain list of (a, b) tuples." % (card, sp)}
    cells = int(area / (sp * sp)); secs = cells * 0.0005
    why = " ".join(a for a in fine_args if a).strip() or "(no reason given)"
    if cells > FINE_MAX_CELLS:
        return {"refused": "%s at %.3f mm over %.0f mm2 is %d cells (~%.0f s); one fine run is capped at %d (~20 s). "
                           "Shrink the footprint to the question, or coarsen." % (card, sp, area, cells, secs, FINE_MAX_CELLS)}
    logp = os.path.join(os.path.dirname(os.path.dirname(folder)), FINE_LOG)
    now = time.time(); recent = []
    try:
        for line in open(logp, encoding="utf-8", errors="replace"):
            if not line.startswith("| 20"): continue
            c = [t.strip() for t in line.strip("|\n").split("|")]
            try:
                t = time.mktime(time.strptime(c[0], "%Y-%m-%d %H:%M:%S"))
                if now - t <= 3600:
                    recent.append({"t": t, "cells": int(c[5]), "box": json.loads(c[6]) if c[6] not in ("", "null") else None, "tag": c[2]})
            except Exception:
                continue
    except OSError:
        pass
    total = sum(r["cells"] for r in recent) + cells
    if total > FINE_HOUR_CELLS:
        return {"refused": "fine runs in the last hour already total %d cells; with this one %d > %d. Fifteen small fine "
                           "runs are one huge one. Run it coarse, or wait for the hour to pass."
                           % (total - cells, total, FINE_HOUR_CELLS)}
    bx = plan["box"]
    for r in recent:
        b2 = r.get("box")
        if not b2: continue
        touch = not (bx[1] < b2[0] - 2.0 or b2[1] < bx[0] - 2.0 or bx[3] < b2[2] - 2.0 or b2[3] < bx[2] - 2.0)
        if touch and r["cells"] + cells > FINE_MAX_CELLS and r["tag"] != tag:
            return {"refused": "this footprint touches the fine run %s of the last hour and the two together are %d cells > %d: "
                               "that is one measurement in pieces. One footprint, one run, or coarser." % (r["tag"], r["cells"] + cells, FINE_MAX_CELLS)}
    line = ("FINE MEASUREMENT: %s / %s, %s at %.3f mm over %.0f mm2 = %d cells (~%.0f s): %s"
            % (os.path.basename(folder), tag, card, sp, area, cells, secs, why))
    try:
        new = not os.path.isfile(logp)
        with open(logp, "a", encoding="utf-8") as fh:
            if new:
                fh.write("# FINE MEASUREMENTS - every run sampled finer than 0.5 mm (leangate.fine_gate). The agent pastes the ANNOUNCE line in the chat.\n\n"
                         "| when | job | tag | card | spacing | cells | plan box | why |\n|---|---|---|---|---|---|---|---|\n")
            fh.write("| %s | %s | %s | %s | %.3f | %d | %s | %s |\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), os.path.basename(folder), tag, card, sp, cells, json.dumps([round(v, 2) for v in bx]), why.replace("|", "/")))
    except OSError:
        pass
    return {"announce": line}


FROZEN_FILE = "FROZEN_REGIONS.json"


def _frozen_path(root):
    return os.path.join(root, "claude_code", FROZEN_FILE)


def frozen_load(root):
    p = _frozen_path(root)
    if not os.path.exists(p):
        return []
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh).get("regions", [])
    except Exception:
        return []


def frozen_save(root, regions):
    p = _frozen_path(root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"regions": regions}, fh, indent=2)
    os.replace(tmp, p)


def frozen_hits(root, box):
    """Every frozen region the given box [x0 x1 y0 y1 z0 z1] INTERSECTS.

    THE REGISTRY EXISTS BECAUSE A GATE SUITE CANNOT SEE INTENT. the agent, 2026-09-22, on a fill it built
    over a flank slot array: *"closed tool, 0 exposed vertices, +0 open edges, body bit-identical"* -
    every gate passed and the tool would have put material into a DESIGNED vent array. The only thing
    that caught it was painting the tool and asking a human-equivalent reviewer whether the openings
    were construction gaps or apertures. **Nothing measurable distinguishes those two.** So the answer
    has to be recorded once, as boxes, by whoever knows the design - and then it is enforceable.
    """
    hits = []
    b = [float(v) for v in box]
    for r in frozen_load(root):
        q = [float(v) for v in r.get("box", [0] * 6)]
        if (b[0] <= q[1] and b[1] >= q[0] and b[2] <= q[3] and b[3] >= q[2]
                and b[4] <= q[5] and b[5] >= q[4]):
            hits.append(r)
    return hits


def frozen_refuse(root, box, what="this edit", allow=""):
    """(ok, message). Refuses when `box` touches a frozen region, unless `allow` names it."""
    hits = frozen_hits(root, box)
    if not hits:
        return True, ""
    named = {n.strip().lower() for n in str(allow or "").split(",") if n.strip()}
    blocking = [h for h in hits if h.get("name", "").lower() not in named]
    if not blocking:
        return True, ("frozen regions touched and NAMED as allowed: %s"
                      % ", ".join(h.get("name", "?") for h in hits))
    lines = ["%s intersects %d FROZEN region(s):" % (what, len(blocking))]
    for h in blocking:
        lines.append("  %-22s %s" % (h.get("name", "?"), h.get("why", "no reason recorded")))
        lines.append("      recorded %s by %s" % (h.get("when", "?"), h.get("who", "?")))
    lines.append("A LUMP inside a frozen region is not chosen: it fills a designed feature, and the region is")
    lines.append("recreated at the end of edits anyway (the client, 2026-09-22). A selection AREA may include the region;")
    lines.append("a lump may not. Nothing measurable tells a construction gap from a designed aperture, which is")
    lines.append("why the answer is a recorded box. --allow-frozen \"<name>\" overrides and is recorded.")
    return False, "\n".join(lines)


def frozen_suspect(lumps, pitch_tol=0.15, vol_tol=0.25, min_n=3):
    """Flag lumps that are one of N near-identical lumps at constant pitch. REGULARITY IS A SIGNAL.

    the agent's reviewer settled the vent array on exactly this: *"Construction gaps from a voxel process are
    irregular in width and position frame to frame; this row is metronomic."* A defect is irregular; a
    designed feature repeats. This cannot decide anything on its own - it marks SUSPECT so the
    question gets asked before the tool is placed, not after it ships.

    `lumps` is a list of dicts with 'vol' and 'centre' (x, y, z). Returns the indices flagged.
    """
    n = len(lumps)
    if n < min_n:
        return []
    import itertools
    out = set()
    for ax in range(3):
        idx = sorted(range(n), key=lambda i: float(lumps[i]["centre"][ax]))
        run = [idx[0]]
        for a, b in zip(idx, idx[1:]):
            ca = float(lumps[a]["centre"][ax]); cb = float(lumps[b]["centre"][ax])
            va = float(lumps[a]["vol"]); vb = float(lumps[b]["vol"])
            same_vol = abs(va - vb) <= vol_tol * max(va, vb, 1e-9)
            if not run or not same_vol:
                if len(run) >= min_n:
                    out.update(run)
                run = [b]
                continue
            run.append(b)
        if len(run) >= min_n:
            out.update(run)
    keep = set()
    for ax in range(3):
        cand = sorted((i for i in out), key=lambda i: float(lumps[i]["centre"][ax]))
        if len(cand) < min_n:
            continue
        gaps = [float(lumps[b]["centre"][ax]) - float(lumps[a]["centre"][ax])
                for a, b in zip(cand, cand[1:])]
        gaps = [g for g in gaps if g > 1e-9]
        if len(gaps) >= min_n - 1:
            m = sum(gaps) / len(gaps)
            if m > 0 and max(abs(g - m) for g in gaps) <= pitch_tol * m:
                keep.update(cand)
    return sorted(keep)


ATLAS_FILE = "ATLAS.json"
ATLAS_DEF = ("DRAFT", "RENDERED", "CLIENT", "STALE")
ATLAS_EDIT = ("FROZEN", "OPEN", "CARDED", "RUNNING", "BUILT", "REJECTED", "ACCEPTED")


def _atlas_path(root):
    return os.path.join(root, "claude_code", ATLAS_FILE)


def atlas_load(root):
    p = _atlas_path(root)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return None
    al_ = _atlas_token_aliases()
    if al_:      # atlas_token_aliases
        for r in (d.get("regions") or {}).values():
            if not isinstance(r, dict): continue
            for k in ("definition_status", "definition"):
                if r.get(k) in al_: r[k] = al_[r.get(k)]
            for ok_, nk_ in al_.items():
                if ok_ in r and nk_ not in r and ok_ not in ("definition_status", "definition"): r[nk_] = r[ok_]
    return d
def _atlas_token_aliases():
    """31by: the machine's env.json "atlas_token_aliases" - {old status token or key name: the current one}; {} when none (the shipped env.example.json lists none)"""
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "env.json"), encoding="utf-8") as fh:
            v = (json.load(fh) or {}).get("atlas_token_aliases") or {}
        return {str(k): str(x) for k, x in v.items()} if isinstance(v, dict) else {}
    except Exception:
        return {}


ATLAS_DEFER_FILE = "ATLAS_DEFER.json"


def atlas_defer_path(root):
    return os.path.join(root, "claude_code", ATLAS_DEFER_FILE)


def atlas_deferred(root):
    """31bv B1 (the second project project's friction F5; the client 10-30: the atlas and the dossier come AFTER the model has made worthwhile progress): the deferral record
    {until, when, by} written by `kit atlas defer --until "<the client's words>"`, or None."""
    p = atlas_defer_path(root)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) and d.get("until") else None
    except Exception:
        return None


def atlas_defer_active(root):
    """the deferral IN FORCE: recorded, no atlas yet, and no model of record PROMOTED since it was recorded (the question returns at the first promotion, as the client's rule says) -
    the record, or None"""
    d = atlas_deferred(root)
    if not d or atlas_load(root) is not None:
        return None
    if d.get("ended"):
        return None
    try:
        for p in ((session(root) or {}).get("promotions") or []):
            if str(p.get("when") or "") > str(d.get("when") or ""):
                return None
    except Exception:
        pass
    return d


def atlas_defer_end(root, how):
    """31bv B1 (the tester TB1's F3): THE DEFERRAL'S END IS WRITTEN INTO ITS OWN RECORD. The first form read the open session's promotions, and `kit close` takes the
    session with it: after a close the deferral read as in force again and the atlas question stayed silent for good after the first promotion. `kit promote` ends
    it here (the record stays, `ended` on it - kit atlas status says how); `kit atlas defer --until` after it starts a new one. True when a standing deferral was ended."""
    d = atlas_deferred(root)
    if not d or d.get("ended"):
        return False
    d["ended"] = {"when": _now(), "how": str(how)}
    p = atlas_defer_path(root); tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1)
    os.replace(tmp, p)
    return True


def atlas_save(root, doc):
    p = _atlas_path(root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    os.replace(tmp, p)


def atlas_regions(root):
    d = atlas_load(root) or {}
    return d.get("regions", {})


def atlas_citable(root, name):
    """(ok, message) — may a card cite this region? Only a definition the client has confirmed.

    THE ARTEFACT THIS GATES DID NOT EXIST, AND THAT IS THE WHOLE FAILURE. the agent, 2026-09-22, answering
    the client's *"do you decide that fact new every time?"*: **yes** - there had never been a stored
    definition of any region on a part eleven revisions in. Three consecutive scripts in ONE session
    each re-derived every boundary from nothing; the acceptance table named regions in prose with no
    coordinates for any of them. So every card was written against a box invented that afternoon and
    the edit landed wherever that afternoon's guess pointed. **It is not a geometry problem. It is a
    missing artefact.** The kit gates the model of record, the measurements, the wall clock and the
    orbit review, and it did not gate the one thing that says what the model's PARTS are.
    """
    regs = atlas_regions(root)
    if not regs:
        return False, ("this project has NO ATLAS. Nothing can be cited until the part has named "
                       "regions: `kit atlas init`, then `kit atlas add <name> ...`")
    r = regs.get(name)
    if not r:
        return False, ("no region named %r. `kit atlas status` lists them." % name)
    st = r.get("definition_status", "DRAFT")
    if st == "CLIENT":
        return True, "region %r is confirmed by the client" % name
    return False, ("region %r is at definition status %s, not the client. A card may not cite a boundary the "
                   "client has never confirmed - that is how a month was spent." % (name, st))


def atlas_mark_stale(root, box, why=""):
    """Every region whose space the given box touches goes STALE. The dossier's rule, applied here."""
    doc = atlas_load(root)
    if not doc:
        return []
    hit = []
    b = [float(v) for v in box]
    for name, r in doc.get("regions", {}).items():
        q = r.get("box")
        if not q or len(q) != 6:
            # confirmed
            if r.get("definition_status") not in ("STALE",):
                r["was"] = r.get("definition_status", "DRAFT")
                r["definition_status"] = "STALE"
                r["stale_why"] = (why or "an applied edit touched this space") + \
                    "  (no box recorded, so this region cannot be shown to be untouched)"
                r["stale_when"] = _now()
                hit.append(name)
            continue
        q = [float(v) for v in q]
        if (b[0] <= q[1] and b[1] >= q[0] and b[2] <= q[3] and b[3] >= q[2]
                and b[4] <= q[5] and b[5] >= q[4]):
            if r.get("definition_status") != "STALE":
                r["was"] = r.get("definition_status", "DRAFT")
                r["definition_status"] = "STALE"
                r["stale_why"] = why or "an applied edit touched this space"
                r["stale_when"] = _now()
                hit.append(name)
    if hit:
        atlas_save(root, doc)
    return hit


def atlas_mark_edited(root, names, job, out=""):
    """Record that an applied job edited these regions. Their DEFINITION stays as the client confirmed it; their
    MAP (face list, pieces) now predates the model. Returns the names recorded."""
    doc = atlas_load(root)
    if not doc:
        return []
    hit = []
    for n in names:
        r = doc.get("regions", {}).get(n)
        if r is None:
            continue
        r.setdefault("edited_by", []).append({"job": job, "when": _now(), "model": out})
        if r.get("edit_status") == "FROZEN":
            r.setdefault("recreate_owed", []).append({"job": job, "when": _now(), "model": out})
        hit.append(n)
    if hit:
        atlas_save(root, doc)
    return hit


def atlas_assignment(root, key):
    """The region a B-rep edit's new geometry was assigned to, or None. the client, 2026-09-22: a region map only
    goes stale on B-rep edits, so *"gate agent to have to assign all new geometry to an existing section or
    announce they are creating a new section."* Keyed by job name, or by a burrito tag."""
    return ((atlas_load(root) or {}).get("assignments", {}) or {}).get(str(key))


def atlas_needs_assignment(root):
    """True once the atlas holds a region the client confirmed - before that there is nothing to assign to."""
    return any(r.get("definition_status") == "CLIENT" for r in atlas_regions(root).values())


def atlas_assign(root, key, region=None, new=None, what="", box=None):
    """Record where a B-rep edit's new geometry belongs: an existing region, or a NEW one (created at DRAFT
    and announced). Returns (ok, message)."""
    doc = atlas_load(root)
    if not doc:
        return False, "this project has no atlas"
    regs = doc.setdefault("regions", {})
    if new:
        if new in regs:
            return False, "region %r already exists - assign to it with --to %s" % (new, new)
        if not str(what).strip():
            return False, "--new needs --what: the new section's physical definition in one sentence"
        regs[new] = {"what_it_is": what, "box": box, "surface": "", "connectivity": "", "area_limits": "",
                     "faces": [], "evidence": "", "definition_status": "DRAFT", "edit_status": "OPEN",
                     "model": doc.get("model", ""), "when": _now(), "announced_by": str(key)}
        region = new
    elif region not in regs:
        return False, "no region named %r in the atlas" % region
    doc.setdefault("assignments", {})[str(key)] = {"to": region, "new": bool(new), "when": _now()}
    regs[region].setdefault("added_geometry", []).append({"by": str(key), "when": _now()})
    atlas_save(root, doc)
    return True, region


def atlas_recreate_owed(root):
    """{region: [jobs]} - FROZEN regions an applied job edited that have not been measured back yet."""
    return {n: [e.get("job", "?") for e in r.get("recreate_owed", [])]
            for n, r in atlas_regions(root).items() if r.get("recreate_owed")}


def atlas_running(root):
    """Regions recorded as an edit in progress. `kit close` must not hand over with one live."""
    return [n for n, r in atlas_regions(root).items() if r.get("edit_status") == "RUNNING"]


def atlas_axis(root):
    """The project's recorded orientation: {'axis':'y','front':-33.1,'aft':-297.9,'said':'...'} or None."""
    return (atlas_load(root) or {}).get("axis")


def atlas_axis_conflict(name, box, axis):
    """Does a region's NAME claim an end its BOX contradicts? Returns a message, or "".

    FOUR REGIONS IN ONE DELIVERED MAP CARRIED THE WRONG END IN THEIR NAME, 2026-09-22 - three
    called "front" sitting at the aft end and one called "aft" sitting at the front - on a part
    whose orientation had been settled from the assembly and written into the project's standing
    rulings that same day. Nothing compared the two. A name is the only thing most readers ever see
    of a region, and a wrong one sends the next card, and the edit, to the other end of the part.

    The test is arithmetic, not judgement: the project records which coordinate is the front; a
    region whose box lies wholly past the midpoint gets the other word.
    """
    if not axis or not box or len(box) != 6:
        return ""
    ax = "xyz".find(str(axis.get("axis", "y")).lower()[:1])
    if ax < 0:
        return ""
    try:
        front = float(axis["front"]); aft = float(axis["aft"])
    except Exception:
        return ""
    lo, hi = float(box[2 * ax]), float(box[2 * ax + 1])
    mid = 0.5 * (front + aft)
    toward_front = (front > aft)
    at_front = (lo > mid) if toward_front else (hi < mid)
    at_aft = (hi < mid) if toward_front else (lo > mid)
    low = name.lower()
    says_front = any(w in low for w in ("front", "nose", "forward"))
    says_aft = any(w in low for w in ("aft", "rear", "tail"))
    if says_front and says_aft:
        return ""
    if says_front and at_aft:
        return ("%r is named for the FRONT and its box sits wholly at the AFT end (%s %.1f..%.1f; "
                "front is %s=%.1f, aft %.1f)." % (name, "xyz"[ax], lo, hi, "xyz"[ax], front, aft))
    if says_aft and at_front:
        return ("%r is named for the AFT end and its box sits wholly at the FRONT (%s %.1f..%.1f; "
                "front is %s=%.1f, aft %.1f)." % (name, "xyz"[ax], lo, hi, "xyz"[ax], front, aft))
    return ""

#!/usr/bin/env python3
r"""integrity.py — THE SECOND-LEVEL CONTROL: you cannot prevent every workaround, but you can
always DETECT one, because the evidence is on disk.

the client, 2026-09-14: *"What do you mean 'not a sandbox' ... Can it be gated to report if it goes out of
bounds using a workaround? That seems like an easy 2nd level control."*

The client is right, and it is easy. This is that.

WHY PREVENTION HAS A CEILING, IN ONE PARAGRAPH. `guard.py` is a PreToolUse hook: it reads the
COMMAND TEXT of a Bash call and the file path of a Write/Edit. It refuses a visible path outside
the project, an enforcement file by name, a FreeCAD launch outside `kit run`. What it cannot see is
INSIDE a program: `& "python.exe" "job.py"` is four harmless-looking tokens, and once `job.py` is
running it opens whatever the account can. Claude Code's own permission rules stop at the same
line — Claude Code's own documentation: *"Permission rules do not confine a subprocess... Once a
script is running, permission rules have no further say over what it touches."* And the sandboxed
Bash tool that WOULD confine it *"runs on macOS, Linux and WSL2. Native Windows is not supported."*

SO STOP TRYING TO WATCH THE ROUTE AND WATCH THE RESULT. Every route — a runtime-assembled path, an
encoded one, a script file, a subprocess of a subprocess — ends in the same place: a control file
on disk is different from what it was. That is one thing to check, it is cheap, and **it is
route-independent**, which is the property none of the preventive layers has.

WHERE THE MANIFEST LIVES, AND WHY IT IS NOT IN LEAN_KIT. `%USERPROFILE%\.claude\` — outside
every project. To forge it, a session would have to break TWO independent rules rather than one:
the guard's boundary (writes are allowed inside the project and nowhere else) and, once the client applies
them, the `Edit(~/.claude/...)` deny rules, which beat hooks. It is still not proof against a
determined subprocess and this file does not claim to be. **What it IS proof against is every
accident** — and every instance on this project's record has been an accident.

    integrity.py --write     record the controls as they are now (the installer calls this)
    integrity.py --check     compare, print what changed, exit 1 if anything did
    integrity.py             the same as --check, quietly

Never refuses anything, never raises, and is never the reason work stops.
"""

import hashlib
import json
import os
import sys
for _s_ in (sys.stdout, sys.stderr):      # transcript
    try: _s_.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass
import time

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
MANIFEST = os.path.join(os.path.expanduser("~"), ".claude", "leankit_manifest.json")

SUFFIXES = (".py", ".json")
DOCS = ("CONTRACT.md", "ORCHESTRATOR.md", "METHOD.md", "EDIT_TYPES.md", "PROJECT_LAYOUT.md",
        "BURRITO_STEPS.md", "BURRITO_BLANKET_METHOD.md")
SKIP_DIRS = ("__pycache__", "_burrito_working_copy_20260913", "templates_from_lean_snapshot")


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def scan(root=KIT):
    """{relative path: short sha256} for every control file under `root`."""
    out = {}
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not (f.endswith(SUFFIXES) or f in DOCS):
                continue
            p = os.path.join(dirpath, f)
            try:
                out[os.path.relpath(p, root).replace("\\", "/")] = _sha(p)
            except Exception:
                pass
    return out


def syntax(root=KIT):
    """[(relative path, one-line reason)] for every control .py that will not COMPILE.

    WHY THIS EXISTS, AND IT COST THE WHOLE GUARD. On 2026-09-16 `guard.py` was found carrying a
    SyntaxError: a refusal message applied `%` in the middle of an implicitly-concatenated literal
    and then continued with another string. Python cannot parse that, so the file never ran - and a
    PreToolUse hook that dies at PARSE time exits non-zero with a traceback on stderr, which is not
    exit code 2, so NOTHING WAS BLOCKED AND NOTHING WAS SAID. The guard was dead and the session
    looked exactly the same as one where the guard had nothing to refuse.

    That is this project's oldest shape of failure wearing new clothes - P08, and
    the process-failure record's closing line: a silent wait looks exactly like a silent success. The
    manifest above catches a control that CHANGED. It could not catch a control that changed into
    something that does not run, because a hash is a hash either way.

    Compiling is deterministic, costs a few milliseconds, and cannot itself fail silently: a
    watcher whose own check is one `compile()` call has nowhere left to hide. It reports; it never
    refuses.
    """
    bad = []
    for rel in sorted(scan(root)):
        if not rel.endswith(".py"):
            continue
        p = os.path.join(root, rel.replace("/", os.sep))
        try:
            with open(p, "rb") as fh:
                compile(fh.read(), p, "exec")
        except SyntaxError as e:
            bad.append((rel, "line %s: %s" % (getattr(e, "lineno", "?"), (e.msg or "")[:90])))
        except Exception as e:                       # unreadable
            bad.append((rel, "%s: %s" % (type(e).__name__, str(e)[:90])))
    return bad


def write(root=KIT):
    """Record the controls as they are now. This is what the INSTALLER calls.

    The installer is the sanctioned moment the controls change: the client runs it, deliberately, after a
    maintenance pass. Anything that changes them at any OTHER moment is what this file exists to
    find.
    """
    m = {"root": root, "when": time.strftime("%Y-%m-%d %H:%M:%S"), "files": scan(root)}
    try:
        os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
        with open(MANIFEST, "w", encoding="utf-8") as fh:
            json.dump(m, fh, indent=1)
        return len(m["files"])
    except Exception:
        return None


def verify(root=KIT):
    """(state, when, [(what, path)]) — state is "ok", "changed", "none" or "unreadable"."""
    try:
        with open(MANIFEST, encoding="utf-8") as fh:
            m = json.load(fh)
    except FileNotFoundError:
        return "none", None, []
    except Exception:
        return "unreadable", None, []
    was, now = (m.get("files") or {}), scan(root)
    findings = [("CHANGED", p) for p in sorted(was) if p in now and now[p] != was[p]]
    findings += [("REMOVED", p) for p in sorted(was) if p not in now]
    findings += [("ADDED", p) for p in sorted(now) if p not in was]
    return ("changed" if findings else "ok"), m.get("when"), findings


def banner(root=KIT, project=None):
    """The lines session_start.py prints, or [] when there is nothing to say.

    `root` is the KIT being hashed; `project` is where the liveness beat goes. They are different
    folders and conflating them is how the first attempt at this fix went wrong.

    IT BEATS HERE, AND THIS IS A DEFECT THE R20 ORCHESTRATOR FOUND. 2026-09-14, from its close:
    *"`kit status` reports the integrity watcher has never run in this project - nothing is
    checking whether the controls themselves have changed. The guard is alive; integrity is not."*

    It was right, and the cause was mine: `guarded()` only wraps a module run as `__main__`, and
    NOTHING runs integrity.py that way. `session_start.py` imports it and calls this function, so
    the wrapper never fired and `integrity` reported DEAD for ever - while the check itself was
    running perfectly every session.

    **A liveness register that reports a healthy watcher as dead is worse than none**: it is the
    cry-wolf failure aimed at the one signal that exists to be believed. The beat belongs where the
    WORK happens, not where the process starts.
    """
    if project:
        try:
            import sys as _sys
            _sys.path.insert(0, HERE)
            import liveness as _L
            _L.beat(project, "integrity", "ok")
        except Exception:
            pass
    _bad = syntax(root)
    head = []
    if _bad:
        head = ["!" * 78,
                "A CONTROL FILE DOES NOT COMPILE. IT IS NOT RUNNING, AND ITS SILENCE LOOKS EXACTLY",
                "LIKE HAVING NOTHING TO SAY.", ""]
        for rel, why in _bad[:12]:
            head.append("    %-44s %s" % (rel, why))
        if len(_bad) > 12:
            head.append("    ... and %d more" % (len(_bad) - 12))
        head += ["",
                 "Fix it before anything else. If `guard.py` or a hook is on that list, NOTHING has",
                 "been enforced since it was last edited - treat every write in that window as",
                 "ungated and re-check it.",
                 "!" * 78, ""]

    state, when, findings = verify(root)
    if state == "ok":
        return head
    if state == "none":
        return head + ["  controls: NOT RECORDED. Run the installer once and this line becomes a check.",
                       "            (integrity.py --write, or any install_lean_hooks.py run)"]
    if state == "unreadable":
        return head + ["  !! the control manifest exists and cannot be read. Treat the kit as unverified."]
    out = head + ["!" * 78,
                  "THE CONTROLS HAVE CHANGED SINCE THEY WERE LAST RECORDED (%s)." % when, ""]
    for what, p in findings[:25]:
        out.append("    %-8s %s" % (what, p))
    if len(findings) > 25:
        out.append("    ... and %d more" % (len(findings) - 25))
    out += ["",
            "If the client ran the installer or edited the kit themselves, this is expected and the next",
            "installer run re-records it. If NOBODY did, then something wrote to the kit without",
            "going through a tool call that `guard.py` could see — a script, a subprocess, a path",
            "assembled at runtime. That is the case this check exists for, and it is the case",
            "prevention cannot cover.",
            "",
            "DO NOT 'fix' it by re-recording the manifest. Say what you found, in the message body,",
            "and stop. A tripwire an agent is allowed to reset is a tripwire.",
            "!" * 78]
    return out


def main(argv):
    root = KIT
    if "--write" in argv:
        n = write(root)
        print("[integrity] recorded %s control file(s) -> %s" % (n, MANIFEST) if n
              else "[integrity] could not write %s" % MANIFEST)
        return 0
    lines = banner(root)
    if not lines:
        state, when, _ = verify(root)
        print("[integrity] controls unchanged since %s." % when)
        return 0
    print("\n".join(lines))
    return 1


if __name__ == "__main__":
    _root = os.getcwd()
    while _root and not os.path.isdir(os.path.join(_root, ".claude")) \
            and os.path.dirname(_root) != _root:
        _root = os.path.dirname(_root)
    try:
        sys.path.insert(0, HERE)
        import liveness as _L
        sys.exit(_L.guarded(_root, "integrity", main, sys.argv[1:]))
    except Exception as exc:
        sys.stderr.write("[integrity] skipped (%s)\n" % exc.__class__.__name__)
        sys.exit(0)

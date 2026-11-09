#!/usr/bin/env python3
"""failures_review.py - read a project's FAILURES.md the way a LEAN_KIT agent reviews it; mark rows resolved.

    python "C:\\CAD\\LEAN_KIT\\failures_review.py" "C:\\CAD\\Projects\\MYPART"
    python "...\\failures_review.py" "<project root>" --resolve 24 --by "kit.py _kv(): --help is a bare flag; pinned by selftest_leangates [25]"
    python "...\\failures_review.py" "<project root>" --open        (only the rows nobody has closed)

WHO RUNS THIS. A LEAN_KIT agent, when it reviews the register - never a project session. the client,
2026-09-17: *"I do want items resolved marked as such. I also do not want the lean kit reviewing this
information each time. It does not need to. It only needs to add to a file for LEAN_KIT agents to
review. It's wasted compute to have it review past items at all."* So the split is:

  * `kit failure` (in the kit, run by project agents)  -> APPENDS a row. Reads nothing back. Unchanged.
  * this script (in LEAN_KIT, run by LEAN_KIT agents) -> READS the register, numbers the rows,
    says which are open, and appends the RESOLVED row that closes one.

THE FORMAT DOES NOT CHANGE. A resolution is an ordinary row whose *what happened* column begins
`RESOLVED: row N` and quotes the first words of the row it closes; *why* carries what changed, where
it is pinned. The register stays append-only, which is what makes it evidence: nothing is edited or
deleted, and a row number is stable because nothing above it can move. A row is "resolved" when a
later row says `RESOLVED: row N` for its number.

A row number is what `--resolve` takes, and it is what this script prints - count nothing by hand.
"""
import os
import re
import sys
import time

FAILURES = "FAILURES.md"
RESOLVED_PAT = re.compile(r"^RESOLVED:\s*row\s+(\d+)\b", re.I)


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def rows(root):
    """[(n, when, job, what, why, fix, signature)] - data rows, numbered from 1, in file order."""
    p = os.path.join(root, FAILURES)
    if not os.path.exists(p):
        return []
    out = []
    n = 0
    for line in open(p, encoding="utf-8", errors="replace"):
        if not re.match(r"^\|\s*20\d\d-\d\d-\d\d", line):
            continue
        c = _cells(line)
        if len(c) >= 7 and c[2].lower() in ("gate", "user", "self", "unknown", "-", "resolved"):
            c = [c[0], c[1]] + c[3:7]
        while len(c) < 6:
            c.append("")
        n += 1
        out.append((n,) + tuple(c[:6]))
    return out


def resolved_map(root):
    """{closed row number: (closing row number, why)} from every RESOLVED: row in the file."""
    m = {}
    for n, _when, _job, what, why, _fix, _sig in rows(root):
        hit = RESOLVED_PAT.match(what)
        if hit:
            m[int(hit.group(1))] = (n, why)
    return m


def report(root, only_open=False, width=110):
    rs = rows(root)
    if not rs:
        return "%s: no %s" % (root, FAILURES)
    closed = resolved_map(root)
    lines = ["%s - %d rows, %d open, %d resolved" % (os.path.join(root, FAILURES), len(rs),
                                                     sum(1 for r in rs if r[0] not in closed and not RESOLVED_PAT.match(r[3])),
                                                     len(closed))]
    for n, when, job, what, why, fix, sig in rs:
        if RESOLVED_PAT.match(what):
            if only_open:
                continue
            lines.append("%3d  %s  %-14s  %s" % (n, when[:10], "(closes)", what[:width]))
            continue
        if n in closed:
            if only_open:
                continue
            lines.append("%3d  %s  %-14s  RESOLVED by row %d - %s" % (n, when[:10], job[:14] or "-", closed[n][0], what[:width - 30]))
        else:
            lines.append("%3d  %s  %-14s  OPEN  %s" % (n, when[:10], job[:14] or "-", what[:width]))
    return "\n".join(lines)


def resolve(root, n, by):
    """Append the RESOLVED row for row n. Refuses a row that does not exist, is itself a RESOLVED
    row, or is already closed; refuses a `by` under thirty characters (a closure with no
    evidence is the 68 %-empty ledger again)."""
    rs = rows(root)
    by = (by or "").strip()
    if not rs:
        return 2, "%s: no %s to resolve anything in" % (root, FAILURES)
    if n < 1 or n > len(rs):
        return 2, "row %d does not exist - the register has %d rows (run without --resolve to see them numbered)" % (n, len(rs))
    row = rs[n - 1]
    if RESOLVED_PAT.match(row[3]):
        return 2, "row %d is itself a RESOLVED row; name the row it closes instead" % n
    closed = resolved_map(root)
    if n in closed:
        return 2, "row %d is already resolved, by row %d: %s" % (n, closed[n][0], closed[n][1][:120])
    if len(by) < 30:
        return 2, ("--by needs the evidence in one sentence (30+ characters): what changed, where, and what "
                   "pins it - e.g. \"kit.py _kv(): --help is a bare flag; selftest_leangates [25] drives every "
                   "command's --help\"")
    quote = row[3][:70].rstrip()
    what = "RESOLVED: row %d (%s%s)" % (n, quote, "..." if len(row[3]) > 70 else "")
    _seven = "caught by" in open(os.path.join(root, FAILURES), encoding="utf-8", errors="replace").read(4000)
    line = ("| %s | %s | resolved | %s | %s | - | - |\n" if _seven else "| %s | %s | %s | %s | - | - |\n") % (
        time.strftime("%Y-%m-%d %H:%M:%S"), row[2] or "-", what.replace("|", "/"), by.replace("|", "/"))
    with open(os.path.join(root, FAILURES), "a", encoding="utf-8") as fh:
        fh.write(line)
    return 0, "row %d marked resolved (row %d appended): %s" % (n, len(rs) + 1, what)


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__); return 0
    root = argv[0]
    if not os.path.isdir(root):
        print("not a folder: %s" % root); return 2
    if "--resolve" in argv:
        i = argv.index("--resolve")
        try:
            n = int(argv[i + 1])
        except (IndexError, ValueError):
            print("--resolve takes the row NUMBER this script prints"); return 2
        by = ""
        if "--by" in argv:
            j = argv.index("--by")
            by = argv[j + 1] if j + 1 < len(argv) else ""
        rc, msg = resolve(root, n, by)
        print(msg)
        return rc
    print(report(root, only_open="--open" in argv))
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    sys.exit(main(sys.argv[1:]))

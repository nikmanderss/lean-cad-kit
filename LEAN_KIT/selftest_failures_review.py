#!/usr/bin/env python3
"""selftest_failures_review.py - the register review: numbering, open/resolved, and the RESOLVED row.

    & python "C:\\CAD\\LEAN_KIT\\selftest_failures_review.py"

PINNED: rows are numbered in file order from 1 and never renumbered; a RESOLVED row closes the row it
names and nothing else; --open hides closed rows and RESOLVED rows; resolving a missing row, a RESOLVED
row, an already-closed row, or with no evidence is refused; the register is only ever appended to;
and `kit failure` in the kit still reads nothing back (grep-level: leangate.record_failure opens the
file in append mode only).
"""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import failures_review as F

FAILED = []


def check(label, cond, detail=""):
    print("  %-4s %s" % ("ok" if cond else "FAIL", label))
    if not cond:
        print("       %s" % str(detail)[:300])
        FAILED.append(label)


def main():
    root = tempfile.mkdtemp(prefix="failrev_")
    print("\nFAILURES REVIEW - numbered, closable, append-only\n")
    try:
        p = os.path.join(root, "FAILURES.md")
        open(p, "w", encoding="utf-8").write(
            "# FAILURES\n\n| when | job | what happened | why | fix | signature |\n|---|---|---|---|---|---|\n"
            "| 2026-09-09 15:18:26 | - | kit facts crashes on the project | hardcodes FACTS.md | reported | FileNotFoundError FACTS.md |\n"
            "| 2026-09-09 15:18:26 | - | the guard does not load | launch root is the parent | reported | no .guard_alive |\n"
            "| 2026-09-11 09:41:39 | J1 | kit measure --help crashes: IndexError | parses positionals first | reported | IndexError |\n")
        rs = F.rows(root)
        check("three rows, numbered 1..3 in file order", [r[0] for r in rs] == [1, 2, 3] and rs[2][2] == "J1", rs)
        check("all open before any resolution", F.resolved_map(root) == {})
        out = F.report(root)
        check("the report says 3 rows, 3 open, 0 resolved", "3 rows, 3 open, 0 resolved" in out, out)

        rc, msg = F.resolve(root, 3, "short")
        check("no evidence -> refused", rc == 2 and "30+" in msg, msg)
        rc, msg = F.resolve(root, 9, "kit.py _kv(): --help is a bare flag; pinned by selftest_leangates [25]")
        check("a row that does not exist -> refused by number", rc == 2 and "row 9 does not exist" in msg, msg)
        rc, msg = F.resolve(root, 3, "kit.py _kv(): --help is a bare flag; pinned by selftest_leangates [25]")
        check("row 3 resolved, row 4 appended", rc == 0 and "row 4 appended" in msg, msg)
        rs = F.rows(root)
        check("...the register grew by one row and rows 1-3 are byte-identical",
              len(rs) == 4 and rs[2][3].startswith("kit measure --help crashes") and rs[3][3].startswith("RESOLVED: row 3 ("), rs)
        check("...the closing row keeps the job of the row it closes", rs[3][2] == "J1", rs[3])
        check("...and quotes the first words of what it closes", "kit measure --help crashes" in rs[3][3], rs[3][3])
        check("resolved_map pairs 3 -> 4", F.resolved_map(root) == {3: (4, "kit.py _kv(): --help is a bare flag; pinned by selftest_leangates [25]")}, F.resolved_map(root))
        out = F.report(root)
        check("the report shows row 3 RESOLVED by row 4 and rows 1-2 OPEN", "RESOLVED by row 4" in out and out.count("OPEN") == 2, out)
        check("...and the header count is 2 open, 1 resolved", "4 rows, 2 open, 1 resolved" in out, out)
        out = F.report(root, only_open=True)
        check("--open hides the closed row and the closing row", "OPEN" in out and "RESOLVED" not in out and out.count("\n") == 2, out)

        rc, msg = F.resolve(root, 3, "again, with a perfectly good thirty-plus character reason")
        check("resolving an already-closed row -> refused, naming the closing row", rc == 2 and "already resolved, by row 4" in msg, msg)
        rc, msg = F.resolve(root, 4, "a RESOLVED row is not a failure and cannot be closed")
        check("resolving a RESOLVED row -> refused", rc == 2 and "itself a RESOLVED row" in msg, msg)

        rc, msg = F.resolve(root, 1, "leangate._facts_path prefers whichever fact file exists | tested on both projects")
        rs = F.rows(root)
        check("a pipe in --by is neutralised, the table still parses to 5 rows", rc == 0 and len(rs) == 5 and "/" in rs[4][4], rs[4] if len(rs) > 4 else rs)

        lg = open(os.path.join(HERE, "kit", "leangate.py"), encoding="utf-8").read()
        i = lg.index("def record_failure")
        body = lg[i:lg.index("\ndef ", i + 10)]
        check("leangate.record_failure opens FAILURES.md in append mode only and never reads it",
              'open(p, "a"' in body and ".read(" not in body and "readlines" not in body)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print()
    if FAILED:
        print("%d FAILED: %s" % (len(FAILED), ", ".join(FAILED)))
        return 1
    print("all cases pass. The register is reviewed here, never by the kit; a closed row is named, not edited.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

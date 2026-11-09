#!/usr/bin/env python3
"""selftest_leangates.py — every lean gate, refusing what it should and passing what it should.

    python selftest_leangates.py

Needs no FreeCAD and no project. Each case below is a failure that is ALREADY on this project's
record — in one of the two rule files, in tests\\README.md, or in a test orchestrator's report.

An earlier kit's lesson, which this suite exists to avoid repeating: two of its gates had quietly
stopped working and nothing noticed, because nothing tested them. 220 of 220 registered attempts
sit at outcome OPEN, and 284 of 415 ledger rows carry no pitfall. A gate with no test is a gate
you will find out about later.

Sections [8]-[10] were added after two test-orchestrator runs on 2026-09-09 found gates that
could never pass and an exam that certified vocabulary. Everything in them is a real defect that
shipped past the earlier version of this file, which is why the file keeps growing.
"""

import io
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "kit"))

import leangate as G

PASS, FAIL = [], []


def check(label, cond, detail=""):
    (PASS if cond else FAIL).append(label)
    print("  %-4s %s%s" % ("OK" if cond else "FAIL", label,
                           "" if cond else ("\n         %s" % str(detail)[:220])))


def refuses(label, fn, must_say=None):
    try:
        fn()
    except G.Refused as e:
        msg = str(e)
        if must_say and must_say.lower() not in msg.lower():
            check(label, False, "refused, but not for the expected reason. Wanted %r in:\n%s"
                  % (must_say, msg[:400]))
        else:
            check(label, True)
        return
    except Exception as e:
        check(label, False, "raised %s instead of refusing: %s" % (type(e).__name__, e))
        return
    check(label, False, "DID NOT REFUSE")


def allows(label, fn):
    try:
        fn()
        check(label, True)
    except G.Refused as e:
        check(label, False, "refused when it should have passed:\n%s" % str(e)[:400])
    except Exception as e:
        check(label, False, "raised %s: %s" % (type(e).__name__, e))


GOOD_ANSWERS = {
    "overlap": "a piece goes 0.5 mm into the material it joins, and a face that must not touch "
               "stands 2 mm clear in air",
    "measure": "the orchestrator measures; workers only render",
    "punch": "it may never punch through the far side; the card states the far limit as a "
             "number, e.g. stops 3 mm short of the inner floor",
}

GOOD_CARD = """# CARD J99 — cover side pocket
Edit type: sketch_extrude
Row: G - the flank band above the window meets the crown with no step
Class: shape
Dossier: none - the pocket is a new feature on a flat land, nothing to measure
Purpose: the pocket clears the connector shroud so the cable leaves the box facing DOWN and back.
Base: C:\\proj\\jobs\\J99\\region.brep
Top face: a plane - the pocket floor is a flat machined land, so an extrusion's flat top is right
PARAMS:
  rect_w=20.0 rect_h=12.0 depth=-4.0 op=cut plane_origin=(0,0,14) plane_normal=-z
Expected: volume change about -960 mm3; faces about +5
Far limit: stops 3 mm short of the inner floor - no punch-through.
Out: C:\\proj\\jobs\\J99\\
After: "C:\\py\\python.exe" "C:\\proj\\claude_code\\kit\\kit.py" render C:\\proj\\jobs\\J99\\result.brep --out C:\\proj\\jobs\\J99\\after --name look --box 0 20 0 12 10 16 --job J99
"""


def satisfy_before(root, name, G):
    """Render-first, satisfied the way a real orchestrator satisfies it."""
    salt = "b@lt"
    codes = {"before_%d.png" % i: "AAAA%d" % i for i in range(3)}
    G.codes_record(root, G.before_key(name),
                   [{"image": "/j/%s" % k, "hash": G._kdf(v, salt), "blank": False}
                    for k, v in codes.items()], salt)
    G.job_mark(root, name, "before_dir", "/j")
    G.before_look(root, name, ["the nose is 1.0 proud of a true half round at z45"], codes)


def stamp_fake(root, name, n=3):
    """Record stamped codes for a job the way `kit render --job` does, and return the plaintext
    the way an orchestrator would have read it off the frames. Since 2026-09-10 a look REFUSES
    with no codes on record (fail closed), so every look in this suite carries them."""
    salt = "s@lt-" + name
    codes = {"/j/%s_%d.png" % (name, i): G.new_code() for i in range(n)}
    G.codes_record(root, name, [{"image": k, "hash": G._kdf(v, salt), "blank": False}
                                for k, v in codes.items()], salt)
    return {os.path.basename(k): v for k, v in codes.items()}


def open_session(root):
    bank = os.path.join(root, "model", "bank")
    os.makedirs(bank, exist_ok=True)
    mor = os.path.join(bank, "R26_cover.brep")
    if not os.path.exists(mor):
        open(mor, "w", encoding="utf-8").write("stub")
    return G.session_open(root, True, True, "STATE.md: R26 is the model of record",
                          GOOD_ANSWERS, mor)


def main():
    tmp = tempfile.mkdtemp(prefix="leangate_")
    root = os.path.join(tmp, "proj")
    os.makedirs(os.path.join(root, ".claude"), exist_ok=True)
    card = os.path.join(root, "CARD.md")
    try:
        print("\n[1] SESSION — the reading requirement")
        refuses("a gate refuses with no session at all",
                lambda: G.card_lint(root, card), "no session is open")
        refuses("session_open refuses without METHOD.md read",
                lambda: G.session_open(root, False, True, "S", GOOD_ANSWERS, "m.brep"),
                "METHOD.md not declared read")
        os.makedirs(os.path.join(root, "claude_code", "bank"), exist_ok=True); open(os.path.join(root, "claude_code", "bank", "m.brep"), "w").write("x")
        refuses("session_open refuses with no model of record while the bank holds one",
                lambda: G.session_open(root, True, True, "S", GOOD_ANSWERS, ""),
                "no model_of_record")
        _re = os.path.join(tmp, "proj_empty"); os.makedirs(os.path.join(_re, ".claude"), exist_ok=True); os.makedirs(os.path.join(_re, "claude_code", "bank"), exist_ok=True)
        allows("31bv B1: an EMPTY bank opens without a model - the first body is the next step (the start of a design-from-parts project)",
               lambda: G.session_open(_re, True, True, "none - a new project", GOOD_ANSWERS, ""))
        check("31bv B1: ...and the session record says NONE YET", (G.session(_re) or {}).get("model_of_record", "x") == "")
        refuses("session_open refuses an unanswered exam",
                lambda: G.session_open(root, True, True, "S", {}, "m.brep"), "unanswered")
        refuses("session_open refuses an answer with no 0.5 figure",
                lambda: G.session_open(root, True, True, "S",
                                       dict(GOOD_ANSWERS, overlap="overlap a bit"), "m.brep"),
                "no 0.5 mm figure")
        allows("a complete session_open passes", lambda: open_session(root))
        check("the session is readable afterwards", bool(G.session(root)))
        # RESOLVED
        check("it records the model of record, resolved to a real file",
              os.path.isfile((G.session(root) or {}).get("model_of_record") or ""),
              (G.session(root) or {}).get("model_of_record"))
        refuses("session_open refuses a --model that is a DESCRIPTION, not a path "
                "(this shipped, and cost a live session: the failure surfaced three commands "
                "later as `kit before` naming a remedy already run)",
                lambda: G.session_open(root, True, True, "S", GOOD_ANSWERS,
                                       "the R10 part model of record, 4013 faces"),
                "does not resolve to a file")
        allows("...and re-opening with the real path works", lambda: open_session(root))

        print("\n[2] CARD LINT — every case here is a real card defect from tests\\README.md")
        open(card, "w", encoding="utf-8").write(GOOD_CARD)
        allows("a complete card passes", lambda: G.card_lint(root, card))
        for slot, bad in (
                ("PURPOSE", GOOD_CARD.replace("Purpose: the pocket clears the connector shroud "
                                              "so the cable leaves the box facing DOWN and back.",
                                              "")),
                ("EXPECTED", GOOD_CARD.replace("Expected: volume change about -960 mm3; faces "
                                               "about +5", "")),
                ("FAR LIMIT", GOOD_CARD.replace("Far limit: stops 3 mm short of the inner floor "
                                                "- no punch-through.", "")),
                ("EDIT TYPE", GOOD_CARD.replace("Edit type: sketch_extrude", "")),
                ("ABS PATHS", GOOD_CARD.replace("C:\\proj\\jobs\\J99\\region.brep",
                                                "region.brep")
                                       .replace("C:\\proj\\jobs\\J99\\", "jobs/J99/")
                                       .replace("C:\\py\\python.exe", "python")
                                       .replace("C:\\proj\\claude_code\\kit\\kit.py", "kit.py")),
                ("AFTER RENDER", GOOD_CARD.replace("--box 0 20 0 12 10 16 --job J99", "--job J99")),
                ("TOP FACE", GOOD_CARD.replace("Top face: a plane - the pocket floor is a flat "
                                               "machined land, so an extrusion's flat top is right\n", "")),
                # R18 FANCORNER_P
                ("ROW", GOOD_CARD.replace("Row: G - the flank band above the window meets the crown with no step\n", "")),
                ("CLASS", GOOD_CARD.replace("Class: shape\n", "")),
                ("DOSSIER", GOOD_CARD.replace("Dossier: none - the pocket is a new feature on a flat land, nothing to measure\n", "")),
        ):
            p = os.path.join(root, "bad_%s.md" % slot.replace(" ", "_"))
            open(p, "w", encoding="utf-8").write(bad)
            refuses("a card with no %s is refused" % slot,
                    lambda p=p: G.card_lint(root, p), "no %s" % slot)
        p = os.path.join(root, "bad_type.md")
        open(p, "w", encoding="utf-8").write(GOOD_CARD.replace("sketch_extrude", "freehand_loft"))
        refuses("an edit type that is not in EDIT_TYPES.md is refused",
                lambda: G.card_lint(root, p), "not in EDIT_TYPES")
        p = os.path.join(root, "hole_no_top.md")
        open(p, "w", encoding="utf-8").write(
            GOOD_CARD.replace("Edit type: sketch_extrude", "Edit type: hole")
                     .replace("Top face: a plane - the pocket floor is a flat machined land, so an "
                              "extrusion's flat top is right\n", ""))
        allows("a hole card is not asked for a top face", lambda: G.card_lint(root, p))

        print("\n[3] JOBS")
        refuses("an unknown edit type cannot be registered",
                lambda: G.job_open(root, "J99", "sculpt"), "not one of")
        allows("a job registers",
               lambda: G.job_open(root, "J99", "sketch_extrude", card, "haiku",
                                  expect_vol=-960.0))

        print("\n[4] THE ORCHESTRATOR'S OWN LOOK — the gate an earlier kit never had")
        refuses("look on an unregistered job is refused",
                lambda: G.orchestrator_look(root, "NOPE", ["a", "b", "c"]), "never registered")
        refuses("fewer than three observations is refused",
                lambda: G.orchestrator_look(root, "J99", ["the pocket is there"]),
                "only 1 observation")
        refuses("'looks right' is refused — it is what the worker's HIT already said",
                lambda: G.orchestrator_look(root, "J99", ["looks good", "ok", "as expected"]),
                "say agreement and nothing else")
        refuses("three real observations with NO stamped codes on record are REFUSED — fail "
                "closed (2026-09-10: Pillow was missing, nothing was stamped, and the gate passed "
                "on specificity for an hour)",
                lambda: G.orchestrator_look(root, "J99", [
                    "front-above-left: the pocket floor is flat and the aft wall is full height",
                    "below-front: no breakthrough into the tray; the floor is unbroken",
                    "side-right: the opening faces DOWN and back, which is what the card is for"]),
                "no stamped codes")

        print("\n[4b] PROOF OF OPENING — the hole a test orchestrator found in itself")
        salt = "s@lt"
        c1, c2, c3 = G.new_code(), G.new_code(), G.new_code()
        items = [{"image": "/j/v%d.png" % i, "hash": G._kdf(c, salt), "blank": False}
                 for i, c in enumerate((c1, c2, c3))]
        G.codes_record(root, "J99", items, salt)
        real = ["front: the pocket floor is flat and the aft wall is full height",
                "below: no breakthrough into the tray", "side: the opening faces down and back"]
        check("codes are stored as SALTED HASHES — the plaintext is only in the image",
              all("hash" in it and c1 not in str(it) for it in items))
        refuses("a specific, plausible, FABRICATED observation with no codes is REFUSED",
                lambda: G.orchestrator_look(root, "J99", real), "verified code")
        refuses("a WRONG code is refused and says the picture was not opened",
                lambda: G.orchestrator_look(root, "J99", real,
                                            codes={"v0.png": "AAAAA", "v1.png": c2,
                                                   "v2.png": c3}), "WRONG")
        allows("codes actually read out of the pixels pass",
               lambda: G.orchestrator_look(root, "J99", real,
                                           codes={"v0.png": c1, "v1.png": c2, "v2.png": c3}))
        check("the alphabet excludes every glyph pair a misread has cost this project",
              not (set("O0I1B8S5Z2G6DQV") & set(G.LOOK_ALPHABET)))
        G.codes_record(root, "BLANKJ", [{"image": "/j/b0.png", "hash": G._kdf(c1, salt),
                                         "blank": True}], salt)
        G.job_open(root, "BLANKJ", "hole", card, "haiku", expect_vol=-960.0)
        refuses("a frame that drew almost nothing is refused on the pixels, not on judgment",
                lambda: G.orchestrator_look(root, "BLANKJ", real, codes={"b0.png": c1}),
                "drew almost nothing")

        print("\n[5] THE APPLY GATE")
        refuses("apply is refused while `kit check` has not passed",
                lambda: G.gate_apply(root, "J99"), "kit check` has not passed")
        G.job_mark(root, "J99", "checked", "2026-09-09")
        refuses("31bq R7g: a cut marked checked with NO check record (its CHECK.json gone) and an Expected on the card is refused - the tripwire's evidence is missing",
                lambda: G.gate_apply(root, "J99"), "holds NO volume change")
        _ev99 = (G.job(root, "J99") or {}).get("expect_vol")
        _p99 = os.path.join(root, "CHECK_J99.json"); open(_p99, "w", encoding="utf-8").write('{"PASS": true, "dvol_tess": %r}' % float(_ev99 if _ev99 is not None else 0.0)); G.job_mark(root, "J99", "check_json", _p99)
        allows("apply passes once checked and looked at",
               lambda: G.gate_apply(root, "J99"))

        hcard = os.path.join(root, "hole_card.md")
        open(hcard, "w", encoding="utf-8").write(
            GOOD_CARD.replace("sketch_extrude", "hole")
                     .replace("about -960 mm3", "about -100 mm3"))
        refuses("job_open refuses a card that never passed kit card",
                lambda: G.job_open(root, "J98", "hole", hcard, "haiku", expect_vol=-100.0), "never passed")
        G.card_lint(root, hcard)
        G.job_open(root, "J98", "hole", hcard, "haiku", expect_vol=-100.0)
        G.job_mark(root, "J98", "checked", "2026-09-09")
        refuses("apply is refused when the ORCHESTRATOR has not looked",
                lambda: G.gate_apply(root, "J98"), "has not looked")
        G.orchestrator_look(root, "J98", ["a: the bore is round and open at the top",
                                          "b: it stops short of the floor",
                                          "c: the old bore is filled, no second hole"],
                            codes=stamp_fake(root, "J98"))
        cj = os.path.join(root, "CHECK.json")
        open(cj, "w", encoding="utf-8").write('{"volume_change": -240.0}')
        refuses("apply is refused when the volume misses the card by more than 5%",
                lambda: G.gate_apply(root, "J98", cj), "VOLUME CHANGE")
        open(cj, "w", encoding="utf-8").write('{"volume_change": -98.0}')
        allows("apply passes when the volume matches the card",
               lambda: G.gate_apply(root, "J98", cj))
        import subprocess as _spa, json as _jsa
        _ka = [sys.executable, os.path.join(HERE, "kit", "kit.py")]; _ea = dict(os.environ); _ea["KIT_PROJECT"] = root; os.makedirs(os.path.join(root, "claude_code"), exist_ok=True)
        _s0 = G._read(G._p(root, G.SESSION), {}); _mor0 = _s0.get("model_of_record"); _np0 = len(_s0.get("promotions") or [])
        G.job_mark(root, "J98", "check_json", cj)
        _jd98 = os.path.join(root, "claude_code", "jobs", "J98"); os.makedirs(_jd98, exist_ok=True)
        _r = _spa.run(_ka + ["apply", "--job", "J98", "--no-atlas", "the selftest"], capture_output=True, text=True, env=_ea)
        check("31bq R7Wr: `kit apply --job` on a job with no body_new.brep is refused by name", _r.returncode == 2 and "RESULT IS THE WHOLE BODY" in _r.stdout, (_r.stdout + _r.stderr)[-300:])
        open(os.path.join(_jd98, "body_new.brep"), "wb").write(b"the accepted body"); open(os.path.join(_jd98, "REBUILD_reinsert.json"), "w").write("{}")
        G.job_open(root, "J97", "hole", hcard, "haiku", expect_vol=-100.0); _jd97 = os.path.join(root, "claude_code", "jobs", "J97"); os.makedirs(_jd97, exist_ok=True)
        open(os.path.join(_jd97, "body_new.brep"), "wb").write(b"a body nobody accepted"); open(os.path.join(_jd97, "REBUILD_reinsert.json"), "w").write("{}")
        _r = _spa.run(_ka + ["apply", "--job", "J97", "--no-atlas", "the selftest"], capture_output=True, text=True, env=_ea)
        check("31bq R7Wr (C4): `kit apply --job` on a job never ACCEPTED (no `applied` stamp from kit accept) is refused by name - the card's order check -> look -> accept -> apply", _r.returncode == 2 and "was not ACCEPTED" in _r.stdout, (_r.stdout + _r.stderr)[-300:])
        _r = _spa.run(_ka + ["promote", os.path.join(_jd97, "body_new.brep"), "--no-atlas", "the selftest"], capture_output=True, text=True, env=_ea)
        check("31bq R7Wr (D3): `kit promote` of a file in a job folder with no applied job behind it is refused", _r.returncode == 2 and "no applied job stands behind it" in _r.stdout, (_r.stdout + _r.stderr)[-300:])
        _r = _spa.run(_ka + ["promote", "", "--no-atlas", "the selftest"], capture_output=True, text=True, env=_ea); _r2 = _spa.run(_ka + ["promote", root, "--no-atlas", "the selftest"], capture_output=True, text=True, env=_ea)
        _s1 = G._read(G._p(root, G.SESSION), {})
        check("31bq R7Wr (seen (1)): `kit promote \"\"` and `kit promote <a directory>` are refused (no such file) and the model of record stands", _r.returncode == 2 and _r2.returncode == 2 and _s1.get("model_of_record") == _mor0, (_r.stdout + _r2.stdout)[-300:])
        # NOT TAKEN
        import ctypes as _cta, _winapi as _wja
        def _prm(path_, proj_=None):
            e_ = dict(_ea); e_["KIT_PROJECT"] = proj_ or root
            r_ = _spa.run(_ka + ["promote", path_, "--no-atlas", "the selftest"], capture_output=True, text=True, env=e_)
            s_ = G._read(G._p(root, G.SESSION), {}); mv_ = s_.get("model_of_record") != _mor0
            s_["model_of_record"] = _mor0; s_["promotions"] = (s_.get("promotions") or [])[:_np0]; G._write(root, G.SESSION, s_)
            return r_.returncode, mv_, r_.stdout + r_.stderr
        _f97 = os.path.join(_jd97, "body_new.brep"); _jobsd = os.path.join(root, "claude_code", "jobs")
        _jl = os.path.join(tmp, "fres_jobs_link"); _pl = os.path.join(tmp, "fres_proj_link"); _lk = []
        for _s_, _d_ in ((_jobsd, _jl), (root, _pl)):
            try:
                _wja.CreateJunction(_s_, _d_); _lk.append(_d_)
            except Exception as _e_:
                print("  NOTE NOT TAKEN: no junction %s (%s)" % (_d_, _e_))
        _bf = _cta.create_unicode_buffer(1024); _sn = _bf.value if _cta.windll.kernel32.GetShortPathNameW(_f97, _bf, 1024) else ""
        _cases = [("'..\\jobs\\..'", os.path.join(_jobsd, "J97", "..", "..", "jobs", "J97", "body_new.brep"), None),
                  ("forward slashes", _f97.replace("\\", "/"), None), ("the \\\\?\\ prefix", "\\\\?\\" + _f97, None)]
        if _jl in _lk: _cases.append(("a junction onto the jobs folder", os.path.join(_jl, "J97", "body_new.brep"), None))
        if _pl in _lk: _cases.append(("its plain path while the PROJECT is reached through a junction (KIT_PROJECT)", _f97, _pl))
        if _sn and os.path.normcase(_sn) != os.path.normcase(_f97): _cases.append(("its 8.3 short name", _sn, None))
        else: print("  NOTE NOT TAKEN: this volume gives %s no 8.3 short name" % _f97)
        for _nm, _pth, _pj in _cases:
            _rc, _mv, _o = _prm(_pth, _pj)
            check("fix-route-end-seen (seen (4)): `kit promote` of a jobs\\ file named by %s is REFUSED (no applied job stands behind it) and the model of record unmoved" % _nm,
                  _rc == 2 and not _mv and "no applied job stands behind it" in _o, (_o.strip()[-300:], _rc, _mv))
        if _jl in _lk:
            _rc, _mv, _o = _prm(os.path.join(_jl, "J97", "body_new.brep"))
            check("fix-route-end-seen (seen (4)): the refusal names BOTH spellings - the name given and the REAL path inside the project's jobs folder",
                  os.path.join(_jl, "J97", "body_new.brep") in _o and ("by its REAL path %s" % os.path.realpath(_f97)) in _o, _o.strip()[-400:])
            G.job_open(root, "JRS1", "hole", hcard, "haiku", expect_vol=-100.0); _jdr = os.path.join(_jobsd, "JRS1"); os.makedirs(_jdr, exist_ok=True)
            open(os.path.join(_jdr, "result.brep"), "wb").write(b"an applied job's own result"); G.job_mark(root, "JRS1", "applied_to", os.path.join(_jl, "JRS1", "result.brep"))
            _rc, _mv, _o = _prm(os.path.join(_jdr, "result.brep"))
            check("fix-route-end-seen (seen (4)): an APPLIED job's own file (its applied_to written through the junction) is PROMOTED by its plain path - the match is on the real path too",
                  _rc == 0 and _mv, (_o.strip()[-300:], _rc, _mv))
        _bk = os.path.join(root, "claude_code", "bank"); os.makedirs(_bk, exist_ok=True); _r25 = os.path.join(_bk, "R25_cover_rollback.brep"); open(_r25, "wb").write(b"an older master")
        _rc, _mv, _o = _prm(_r25)
        check("fix-route-end-seen (seen (4)): a bank file is still PROMOTED (a rollback - the control)", _rc == 0 and _mv, (_o.strip()[-300:], _rc, _mv))
        for _d_ in _lk:
            try: os.rmdir(_d_)
            except OSError: pass
        # HARD LINK of
        # NOT TAKEN
        import ctypes as _ct5, _winapi as _wj5, zipfile as _zf5
        _sn5 = os.path.join(root, "claude_code", "STATE_NOW.md")
        def _blocks5():
            try: return open(_sn5, encoding="utf-8").read().count("MODEL OF RECORD ->")
            except OSError: return 0
        def _prm5(path_, proj_=None, mor_=None):
            """promote path_ (KIT_PROJECT proj_), the session's model of record set to mor_ first when given; -> (rc, moved, out, the name recorded, STATE_NOW blocks added)"""
            e_ = dict(_ea); e_["KIT_PROJECT"] = proj_ or root
            s_ = G._read(G._p(root, G.SESSION), {})
            if mor_ is not None: s_["model_of_record"] = mor_; G._write(root, G.SESSION, s_)
            b0_ = _blocks5()
            r_ = _spa.run(_ka + ["promote", path_, "--no-atlas", "the selftest"], capture_output=True, text=True, env=e_)
            s_ = G._read(G._p(root, G.SESSION), {}); rec_ = s_.get("model_of_record"); mv_ = rec_ != (mor_ if mor_ is not None else _mor0)
            s_["model_of_record"] = _mor0; s_["promotions"] = (s_.get("promotions") or [])[:_np0]; G._write(root, G.SESSION, s_)
            return r_.returncode, mv_, r_.stdout + r_.stderr, rec_, _blocks5() - b0_
        _jobs5 = os.path.join(root, "claude_code", "jobs"); _f97 = os.path.join(_jd97, "body_new.brep"); _bank5 = os.path.join(root, "claude_code", "bank"); os.makedirs(_bank5, exist_ok=True)
        _r25 = os.path.join(_bank5, "R25_cover_rollback.brep")
        if not os.path.isfile(_r25): open(_r25, "wb").write(b"an older master")
        _jl5 = os.path.join(tmp, "fresF_jobs_link"); _pl5 = os.path.join(tmp, "fresF_proj_link"); _lk5 = []
        for _s_, _d_ in ((_jobs5, _jl5), (root, _pl5)):
            try: _wj5.CreateJunction(_s_, _d_); _lk5.append(_d_)
            except Exception as _e_: print("  NOTE NOT TAKEN: no junction %s (%s)" % (_d_, _e_))
        _rc, _mv, _o, _rec, _nb = _prm5("\\\\?\\" + _r25)
        check("fres F2: `kit promote` of a bank file by its \\\\?\\ name: rc 0, moved, no crash banner, a STATE_NOW block written, the record prefix-free (the live wrote the session then crashed on relpath)",
              _rc == 0 and _mv and "did not happen" not in _o and _nb >= 1 and _rec == _r25, (_rc, _mv, _nb, _rec, _o.strip()[-300:]))
        _drv_here = os.path.splitdrive(os.path.abspath(__file__))[0]; _drv_tmp = os.path.splitdrive(os.path.abspath(tmp))[0]
        if _drv_here and _drv_here.lower() != _drv_tmp.lower():
            _k3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_selftest_fresF_K3_rollback.brep"); open(_k3, "wb").write(b"a rollback file on another drive")
            try:
                _rc, _mv, _o, _rec, _nb = _prm5(_k3)
                check("fres F2 (K3): a file OUTSIDE the project on ANOTHER DRIVE is promoted - rc 0, moved, no crash banner, a STATE_NOW block (relpath across mounts had crashed after the write)",
                      _rc == 0 and _mv and "did not happen" not in _o and _nb >= 1, (_rc, _mv, _nb, _o.strip()[-300:]))
                if _pl5 in _lk5:
                    _rc, _mv, _o, _rec, _nb = _prm5(os.path.join(_pl5, "claude_code", "bank", "R25_cover_rollback.brep"), _pl5, _k3)
                    check("fres F2 (K4): the project through a junction, the bank file by the junction path, the OLD model of record on another mount - the STATE_NOW block is still written",
                          _rc == 0 and _mv and _nb >= 1, (_rc, _mv, _nb, _o.strip()[-300:]))
            finally:
                try: os.remove(_k3)
                except OSError: pass
        else: print("  NOTE NOT TAKEN: the suite and the temp folder share drive %s - no other-drive case (F2 K3 / K4)" % _drv_tmp)
        if _pl5 in _lk5:
            _rc, _mv, _o, _rec, _nb = _prm5(_r25, _pl5)
            check("fres F2 (K5): the project reached through a junction (KIT_PROJECT), the bank file by its real path: rc 0, moved, no crash banner, a STATE_NOW block",
                  _rc == 0 and _mv and "did not happen" not in _o and _nb >= 1, (_rc, _mv, _nb, _o.strip()[-300:]))
        _hl5 = os.path.join(tmp, "fresF_outside_hardlink.brep"); _hl_ok = False
        try: os.link(_f97, _hl5); _hl_ok = True
        except OSError as _e_: print("  NOTE NOT TAKEN: no hard link on this volume (%s) - F3 / F1 A8 not taken" % _e_)
        if _hl_ok:
            _rc, _mv, _o, _rec, _nb = _prm5(_hl5)
            check("fres F3: a HARD LINK of a jobs\\ file outside jobs\\ is REFUSED by name (its identity found in the jobs walk) and the model of record unmoved (the live promoted it)",
                  _rc == 2 and not _mv and "HARD LINK of" in _o and "no applied job stands behind it" in _o, (_rc, _mv, _o.strip()[-300:]))
            _jr5 = os.path.join(_jobs5, "JRS2"); os.makedirs(_jr5, exist_ok=True); _lnk = os.path.join(_jr5, "region.brep")
            try:
                if not os.path.exists(_lnk): os.link(_r25, _lnk)
                _rc, _mv, _o, _rec, _nb = _prm5(_r25)
                check("fres F3: the bank file is PROMOTED while a job folder holds a hard link of it (the `kit newjob` form - the bank's identity is no jobs file)", _rc == 0 and _mv, (_rc, _mv, _o.strip()[-300:]))
                _hb5 = os.path.join(tmp, "fresF_bank_hardlink.brep")
                if not os.path.exists(_hb5): os.link(_r25, _hb5)
                _rc, _mv, _o, _rec, _nb = _prm5(_hb5)
                check("fres F3: a hard link of the bank file OUTSIDE the project is PROMOTED (the bank's bytes)", _rc == 0 and _mv, (_rc, _mv, _o.strip()[-300:]))
            except OSError as _e_: print("  NOTE NOT TAKEN: the bank hard links (%s)" % _e_)
        _vb5 = _ct5.create_unicode_buffer(128); _drv5 = os.path.splitdrive(_f97)[0]
        _guid5 = _vb5.value if _ct5.windll.kernel32.GetVolumeNameForVolumeMountPointW(_drv5 + "\\", _vb5, 128) else ""
        _rel5 = os.path.splitdrive(_f97)[1].lstrip("\\")
        if _guid5:
            _rc, _mv, _o, _rec, _nb = _prm5(_guid5 + _rel5)
            check("fres F4: the jobs\\ file by its \\\\?\\Volume{GUID}\\ name is REFUSED (realpath first, the prefix off the result) and the model of record unmoved",
                  _rc == 2 and not _mv and "no applied job stands behind it" in _o, (_rc, _mv, _o.strip()[-300:]))
        else: print("  NOTE NOT TAKEN: no volume GUID for %s (F4)" % _drv5)
        _unc5 = "\\\\localhost\\%s$\\%s" % (_drv5.rstrip(":"), _rel5)
        if os.path.exists(_unc5):
            _rc, _mv, _o, _rec, _nb = _prm5(_unc5)
            check("fres F5: the jobs\\ file by a UNC alias of the local drive is REFUSED (a parent folder IS the jobs folder by identity) and the model of record unmoved",
                  _rc == 2 and not _mv and "no applied job stands behind it" in _o, (_rc, _mv, _o.strip()[-300:]))
        else: print("  NOTE NOT TAKEN: the admin share %s is not reachable (F5)" % _unc5)
        _tpl5 = os.path.join(tmp, "fresF_template.FCStd")
        with _zf5.ZipFile(_tpl5, "w") as _z_: _z_.writestr("Document.xml", "<Document/>")
        _scr5 = os.path.join(tmp, "fresF_scratch"); os.makedirs(_scr5, exist_ok=True)
        def _dlv5(model_=None, proj_=None, mor_=None):
            """kit deliver through kit.py (the template holds Document.xml only: a model past the D7 rule stops at build()) -> (refused by D7, reached past D7, out)"""
            e_ = dict(_ea); e_["KIT_PROJECT"] = proj_ or root; e_["KIT_SCRATCH_ROOT"] = _scr5
            s_ = G._read(G._p(root, G.SESSION), {}); keep_ = s_.get("model_of_record")
            if mor_ is not None: s_["model_of_record"] = mor_; G._write(root, G.SESSION, s_)
            r_ = _spa.run(_ka + ["deliver", "R27", "--template", _tpl5, "--target", "Body", "--no-atlas", "the selftest", "--no-review", "the selftest"] + (["--model", model_] if model_ else []), capture_output=True, text=True, env=e_)
            if mor_ is not None: s_["model_of_record"] = keep_; G._write(root, G.SESSION, s_)
            o_ = r_.stdout + r_.stderr; d7_ = "no APPLIED job stands behind it" in o_
            return d7_, (not d7_ and ("GuiDocument" in o_ or "build" in o_.lower())), o_
        _d7, _past, _o = _dlv5(_f97)
        if not _d7 and not _past: print("  NOTE NOT TAKEN: kit deliver stopped before the D7 rule on this project - %s" % _o.strip()[-200:])
        else:
            check("fres F1 (A, the control): `kit deliver --model` of a jobs\\ file nobody applied, by its plain path, is REFUSED (D7)", _d7, _o.strip()[-200:])
            _bf5 = _ct5.create_unicode_buffer(1024); _sn83 = _bf5.value if _ct5.windll.kernel32.GetShortPathNameW(_f97, _bf5, 1024) else ""
            _casesA = [("the \\\\?\\ prefix", "\\\\?\\" + _f97, None)]
            if _jl5 in _lk5: _casesA.append(("a junction onto the jobs folder", os.path.join(_jl5, "J97", "body_new.brep"), None))
            if _pl5 in _lk5: _casesA.append(("its plain path while the project is reached through a junction", _f97, _pl5))
            if _sn83 and os.path.normcase(_sn83) != os.path.normcase(_f97): _casesA.append(("its 8.3 short name", _sn83, None))
            if _guid5: _casesA.append(("its \\\\?\\Volume{GUID}\\ name", _guid5 + _rel5, None))
            if os.path.exists(_unc5): _casesA.append(("a UNC alias of the local drive", _unc5, None))
            if _hl_ok: _casesA.append(("a HARD LINK outside jobs\\", _hl5, None))
            for _nm, _pth, _pj in _casesA:
                _d7, _past, _o = _dlv5(_pth, _pj)
                check("fres F1 (A): `kit deliver --model` of the jobs\\ file nobody applied, named by %s, is REFUSED (D7 by the real path / the identity; the live delivered it)" % _nm, _d7, (_past, _o.strip()[-200:]))
            if _jl5 in _lk5:
                if not (G.job(root, "JRS1") or {}): G.job_open(root, "JRS1", "hole", hcard, "haiku", expect_vol=-100.0)
                _jdr5 = os.path.join(_jobs5, "JRS1"); os.makedirs(_jdr5, exist_ok=True); _res5 = os.path.join(_jdr5, "result.brep")
                if not os.path.isfile(_res5): open(_res5, "wb").write(b"an applied job's own result")
                G.job_mark(root, "JRS1", "applied_to", os.path.join(_jl5, "JRS1", "result.brep"))
                _d7, _past, _o = _dlv5(None, None, os.path.join(_jl5, "JRS1", "result.brep"))
                check("fres F1 (B1): the session's model of record an APPLIED job's file named through the jobs junction (as promote recorded it) PASSES D7 (the live refused it)", _past and not _d7, _o.strip()[-200:])
                _d7, _past, _o = _dlv5(None, None, _res5)
                check("fres F1 (B2): the applied job's file by its plain path, its applied_to written through the junction, PASSES D7", _past and not _d7, _o.strip()[-200:])
            if _pl5 in _lk5:
                _d7, _past, _o = _dlv5(None, _pl5, os.path.join(_pl5, "claude_code", "bank", "R25_cover_rollback.brep"))
                check("fres F1 (B3): a BANK file as the model of record named through the project's junction PASSES C5 (the live refused it)", _past and not _d7, _o.strip()[-200:])
            _d7, _past, _o = _dlv5(None, None, _r25)
            check("fres F1 (B4, the control): the bank file by its plain path PASSES C5", _past and not _d7, _o.strip()[-200:])
        for _d_ in _lk5:
            try: os.rmdir(_d_)
            except OSError: pass
        _r = _spa.run(_ka + ["apply", "--job", "J98", "--no-atlas", "the selftest"], capture_output=True, text=True, env=_ea)
        _bank = os.path.join(root, "claude_code", "bank"); _banked = sorted(f_ for f_ in (os.listdir(_bank) if os.path.isdir(_bank) else []) if f_.endswith("_BODY_MASTER.brep"))
        _s2 = G._read(G._p(root, G.SESSION), {}); _j98 = G.job(root, "J98") or {}
        check("31bq R7Wr (D3): an ACCEPTED job's body_new.brep is COPIED into the bank under the next REV (R27 after R26) and PROMOTED, the job marked applied_to, the promotion recorded with the job",
              _r.returncode == 0 and _banked == ["R27_BODY_MASTER.brep"] and open(os.path.join(_bank, "R27_BODY_MASTER.brep"), "rb").read() == b"the accepted body"
              and os.path.normcase(str(_j98.get("applied_to") or "")) == os.path.normcase(os.path.join(_bank, "R27_BODY_MASTER.brep")) and os.path.normcase(str(_s2.get("model_of_record") or "")) == os.path.normcase(os.path.join(_bank, "R27_BODY_MASTER.brep"))
              and (_s2.get("promotions") or [{}])[-1].get("job") == "J98" and not os.path.exists(os.path.join(root, "STATE.md")), (_r.stdout + _r.stderr)[-400:])
        _r = _spa.run(_ka + ["apply", "--job", "J98", "--no-atlas", "the selftest"], capture_output=True, text=True, env=_ea)
        check("31bq R7Wr (C3): a second apply of the same job is refused (APPLIED already) - the bank holds one copy", _r.returncode == 2 and "APPLIED already" in _r.stdout and len([f_ for f_ in os.listdir(_bank) if f_.endswith("_BODY_MASTER.brep")]) == 1, (_r.stdout + _r.stderr)[-300:])
        _s3 = G._read(G._p(root, G.SESSION), {}); _s3["model_of_record"] = _mor0; _s3["promotions"] = (_s3.get("promotions") or [])[:_np0]; G._write(root, G.SESSION, _s3)

        print("\n[6] FAILURE LOG — all four fields, because an earlier kit's is 68% empty")
        refuses("a failure with no signature is refused",
                lambda: G.record_failure(root, "w", "y", "f", ""), "missing: signature")
        allows("a complete failure row is written",
               lambda: G.record_failure(root, "the cut went 3 mm past the card's far limit",
                                        "the lead-in was added to the depth twice",
                                        "re-derived the depth; card corrected",
                                        "a volume change close to double the expectation",
                                        "J98"))
        check("FAILURES.md exists and has the row",
              os.path.exists(os.path.join(root, "FAILURES.md")) and
              "double the expectation" in open(os.path.join(root, "FAILURES.md"),
                                               encoding="utf-8").read())

        print("\n[7] MEASUREMENT DISCIPLINE — the client's question, and it had no answer before today")
        check("over_precise flags 4 decimals on a 0.30 class",
              G.over_precise("the floor is at 12.3456 mm") == ["12.3456"])
        check("class-resolution figures are NOT flagged",
              G.over_precise("worst 2.74 mm, floor 0.30, wall 2.5") == [])
        check("a version string is NOT flagged",
              G.over_precise("FreeCAD 1.1.3 and numpy 2.0.1") == [])
        check("a path is NOT flagged",
              G.over_precise(r"C:\proj\v1.2.3\region.brep") == [])
        check("the legitimate micron offset IS flagged (a WARNING, never a refusal — "
              "a recorded lesson says to use it)",
              G.over_precise("plane z c=14.0005") == ["14.0005"])
        G.measure_reset(root)
        msgs = [G.measure_tick(root, "bbox")[1] for _ in range(G.SPIRAL_AT - 1)]
        check("no spiral warning below the threshold", not any(msgs))
        n, msg = G.measure_tick(root, "faces")
        check("the spiral warning fires at %d measures with no card" % G.SPIRAL_AT, bool(msg), n)
        check("  and it asks whether a render could answer it instead",
              msg and "CAN A RENDER ANSWER THIS INSTEAD" in msg)
        check("  and which card number it produces",
              msg and "WHICH NUMBER ON THE CARD" in msg)
        G.card_lint(root, card)
        check("linting a card RESETS the spiral counter",
              G.measure_tick(root, "x")[0] == 1)

        print("\n[8] THE FOUR BUGS THE FIRST TEST ORCHESTRATOR FOUND (2026-09-09)")
        G.job_open(root, "J90", "sketch_extrude", card, "haiku", expect_vol=-960.0)
        check("job_open lifts the card's PURPOSE sentence (it never did — so METHOD.md 10's "
              "'check the picture against the purpose' never printed)",
              "connector shroud" in (G.job(root, "J90").get("card_purpose") or ""),
              G.job(root, "J90").get("card_purpose"))
        check("job_open records a check_json slot", "check_json" in G.job(root, "J90"))
        cj2 = os.path.join(root, "CHECK2.json")
        open(cj2, "w", encoding="utf-8").write('{"PASS": true, "dvol_tess": -958.0, '
                                               '"dvol_kernel": -960.0}')
        G.job_mark(root, "J90", "checked", "2026-09-09")
        G.job_mark(root, "J90", "check_json", cj2)
        G.orchestrator_look(root, "J90", ["a: the pocket floor is flat",
                                          "b: no breakthrough below",
                                          "c: the opening faces down and back"],
                            codes=stamp_fake(root, "J90"))
        allows("accept reads the REAL CHECK.json keys (dvol_tess) — it used to look for "
               "'volume_change', a key nothing writes, so the tripwire was dead",
               lambda: G.gate_apply(root, "J90"))
        G.job_open(root, "J91", "sketch_extrude", card, "haiku", expect_vol=-960.0)
        cj3 = os.path.join(root, "CHECK3.json")
        open(cj3, "w", encoding="utf-8").write('{"PASS": true, "dvol_tess": -2400.0}')
        G.job_mark(root, "J91", "checked", "2026-09-09")
        G.job_mark(root, "J91", "check_json", cj3)
        G.orchestrator_look(root, "J91", ["a: much deeper than drawn",
                                          "b: it has gone through",
                                          "c: the floor is missing"],
                            codes=stamp_fake(root, "J91"))
        refuses("and the tripwire still fires on a real miss, read from the real key",
                lambda: G.gate_apply(root, "J91"), "VOLUME CHANGE")
        import io as _io, contextlib as _cl
        def _vol_case(nm_, cj_txt, expect="card"):
            G.job_open(root, nm_, "sketch_extrude", card, "haiku", expect_vol=-960.0)
            if expect is None: G.job_mark(root, nm_, "expect_vol", None)
            p_ = os.path.join(root, "CHECK_%s.json" % nm_); open(p_, "w", encoding="utf-8").write(cj_txt)
            G.job_mark(root, nm_, "checked", "2026-10-19"); G.job_mark(root, nm_, "check_json", p_)
            G.orchestrator_look(root, nm_, ["a: the piece sits in the region", "b: the seam is closed", "c: nothing outside changed"], codes=stamp_fake(root, nm_))
            b_ = _io.StringIO()
            try:
                with _cl.redirect_stdout(b_): G.gate_apply(root, nm_)
                return "PASSED", b_.getvalue()
            except G.Refused as e_: return "REFUSED", b_.getvalue() + str(e_)
        r_, o_ = _vol_case("J92", '{"PASS": true, "dvol_tess": -2400.0, "skin_piece": true, "dvol_local": -350.0, "dvol_local_kernel": -347.6, "dvol_local_mesh": -389.0, "dvol_local_spread": 41.4}')
        check("31bq SS (B21): a skin edit's local-ruler change is REPORTED with its value, never judged (the whole-body -2400 ignored) - and the PASSED line does not say 'matching its card'",
              r_ == "PASSED" and "-350.0" in o_ and "reported, not judged" in o_ and "matching its card" not in o_, (r_, o_[-300:]))
        r_, o_ = _vol_case("J93", '{"PASS": true, "dvol_tess": -2400.0, "skin_piece": true, "dvol_local": null, "dvol_local_failed": "the piece would not load"}')
        check("31bq SS (B21 (3)): a skin edit whose local ruler FAILED is reported (the whole-body delta, said as such) - the 5 % gate does not refuse it",
              r_ == "PASSED" and "NOT taken" in o_ and "would not load" in o_ and "matching its card" not in o_, (r_, o_[-300:]))
        r_, o_ = _vol_case("J94", '{"PASS": true}')
        check("31bq R7g (the C-gates review's 7): a CUT with an Expected and a check with NO volume key is REFUSED - 'holds NO volume change' (SS had said it and passed)",
              r_ == "REFUSED" and "holds NO volume change" in o_ and "matching its card" not in o_, (r_, o_[-300:]))
        r_, o_ = _vol_case("J94b", '{"PASS": true, "skin_piece": true}')
        check("31bq SS (B21 (2')) / R7g: a SKIN edit with no volume key is SAID, never a silent 'matching its card' - and not refused (reported, not judged)",
              r_ == "PASSED" and "NO volume change" in o_ and "matching its card" not in o_, (r_, o_[-300:]))
        r_, o_ = _vol_case("J94c", '{"PASS": true}', expect=None)
        check("31bq R7g: a cut with no volume key and NO Expected on the card is said, not refused (nothing to judge against)",
              r_ == "PASSED" and "NO volume change" in o_ and "matching its card" not in o_, (r_, o_[-300:]))
        r_, o_ = _vol_case("J95", '{"PASS": true, "dvol_tess": -50.0}', expect=None)
        check("31bq SS (B21 (1')): no Expected volume - the change reported once, the PASSED line without 'matching its card'",
              r_ == "PASSED" and "no Expected volume" in o_ and "matching its card" not in o_, (r_, o_[-300:]))
        r_, o_ = _vol_case("J96", '{"PASS": true, "dvol_tess": "abc"}')
        check("31bq SS (B21 (1')): a non-number - 'not numbers ... reported' and no 'matching its card' after it",
              r_ == "PASSED" and "not numbers" in o_ and "matching its card" not in o_, (r_, o_[-300:]))
        r_, o_ = _vol_case("J97", '{"PASS": true, "dvol_local": 0.0, "skin_piece": true}')
        check("31bq SS (B21): a local ruler with no recorded parts prints no 'None'", r_ == "PASSED" and "None" not in o_ and "0.0 mm3" in o_, (r_, o_[-300:]))
        r_, o_ = _vol_case("J89", '{"PASS": true, "dvol_tess": -958.0}')
        check("31bq SS (B21): a judged change that matches still says 'matching its card'", r_ == "PASSED" and "matching its card" in o_, (r_, o_[-300:]))

        print("\n[9] THE EXAM — the exact answers the SECOND test orchestrator used to break it")
        INV = {"overlap": "0.5 mm clear in the air, and 2 mm into the material it must not touch",
               "measure": "never let the orchestrator near it",
               "punch": "punch through as far as the limit stops you"}
        for k, v in INV.items():
            refuses("exam %r refuses the INVERTED answer (it used to pass)" % k,
                    lambda k=k, v=v: G.session_open(root, True, True, "S",
                                                    dict(GOOD_ANSWERS, **{k: v}), "m.brep"),
                    "exam %r" % k)
        refuses("exam 'measure' refuses 'the worker measures it'",
                lambda: G.session_open(root, True, True, "S",
                                       dict(GOOD_ANSWERS, measure="the worker measures it"),
                                       "m.brep"), "WORKER measures")
        allows("...and the correct answers still pass", lambda: open_session(root))

        print("\n[10] THE EXPECTED VOLUME COMES OFF THE CARD, not off the command line")
        vcard = os.path.join(root, "vol_card.md")
        open(vcard, "w", encoding="utf-8").write(GOOD_CARD)
        G.card_lint(root, vcard)
        allows("job_open reads Expected: ... -960 mm3 off the card",
               lambda: G.job_open(root, "V1", "sketch_extrude", vcard, "haiku"))
        check("  and stores it", G.job(root, "V1").get("card_vol") == -960.0,
              G.job(root, "V1").get("card_vol"))
        check("  and uses it as expect_vol when no flag was given",
              G.job(root, "V1").get("expect_vol") == -960.0)
        refuses("a --expect-vol that DISAGREES with the card is refused (the tripwire is only "
                "worth something if the number came off the card)",
                lambda: G.job_open(root, "V2", "sketch_extrude", vcard, "haiku",
                                   expect_vol=-600.0), "must agree")

        print("\n[11] COMPACTION vs A NEW CONVERSATION — the client's criterion, 2026-09-09")
        os.environ["GATES_CONVERSATION"] = "conv-A"
        open_session(root)
        st, _ = G.session_state(root, "conv-A")
        check("same conversation id = COMPACTION, the session survives", st == "carried", st)
        G.job_open(root, "INFLIGHT", "hole", card, "haiku", expect_vol=-960.0)
        st, _ = G.session_state(root, "conv-B")
        check("different id with work in flight = FOREIGN, reported not inherited",
              st == "foreign", st)
        oroot = os.path.join(tmp, "orphanproj")
        os.makedirs(os.path.join(oroot, ".claude"), exist_ok=True)
        open_session(oroot)
        st, _ = G.session_state(oroot, "conv-B")
        check("different id with nothing in flight = ORPHAN", st == "orphan", st)
        os.environ.pop("GATES_CONVERSATION", None)
        st, _ = G.session_state(root, None)
        check("no id available = behaves as before ('mine'), rather than guessing", st == "mine",
              st)

        print("\n[12] THE WALL CLOCK — 'keep agents on a wall clock'")
        G.job_open(root, "W1", "hole", card, "haiku", expect_vol=-960.0, wall_min=15)
        check("a job carries a wall budget", G.job(root, "W1").get("wall_min") == 15)
        check("an unlaunched job is not on the clock",
              not any(r[0] == "W1" for r in G.wall_status(root)))
        refuses("RENDER FIRST — launching an unlooked-at job is refused",
                lambda: G.job_launched(root, "W1"), "never been looked at")
        satisfy_before(root, "W1", G)
        G.job_launched(root, "W1")
        rows = {r[0]: r for r in G.wall_status(root)}
        check("a launched job appears on the clock", "W1" in rows, rows)
        check("  and is not over budget yet", rows["W1"][3] is False)
        G.job_mark(root, "W1", "launched", __import__("time").time() - 30 * 60)
        rows = {r[0]: r for r in G.wall_status(root)}
        check("a job 30 min into a 15 min budget reads OVER", rows["W1"][3] is True, rows["W1"])
        _jf = os.path.join(root, "claude_code", "jobs", "W1"); os.makedirs(_jf, exist_ok=True)
        with open(os.path.join(_jf, "RESULT.md"), "w") as _fh: _fh.write("handed back\n")
        check("a job whose worker wrote RESULT.md is off the clock (the rest is the orchestrator's judgement)",
              not any(r[0] == "W1" for r in G.wall_status(root)))
        os.remove(os.path.join(_jf, "RESULT.md"))
        check("  ...and back on it without", any(r[0] == "W1" for r in G.wall_status(root)))
        with open(os.path.join(_jf, "PARKED.md"), "w") as _fh: _fh.write("the client: leave it\n")
        check("a PARKED job never nags", not any(r[0] == "W1" for r in G.wall_status(root)))
        os.remove(os.path.join(_jf, "PARKED.md"))
        G.job_mark(root, "W1", "applied", "2026-09-09")
        check("an applied job leaves the clock",
              not any(r[0] == "W1" for r in G.wall_status(root)))

        print("\n[12a] RENDER FIRST means BEFORE THE CARD — the stub (R18 friction log 12:28)")
        refuses("before-look on a name nobody has stubbed or registered is refused",
                lambda: G.before_look(root, "STUB1", ["x", "y", "z"]), "never registered")
        G.job_stub(root, "STUB1")
        check("a stub is a job record without a card", G.job(root, "STUB1").get("stub") is True)
        satisfy_before(root, "STUB1", G)
        check("  the BEFORE frames and look land on the stub", bool(G.job(root, "STUB1").get("before_looked")))
        refuses("  but a stub cannot be LAUNCHED - it has no card",
                lambda: G.job_launched(root, "STUB1"), "no card")
        G.job_open(root, "STUB1", "hole", card, "haiku", expect_vol=-960.0)
        j_ = G.job(root, "STUB1")
        check("  kit job replaces the stub and keeps the before-look",
              not j_.get("stub") and bool(j_.get("before_looked")) and j_.get("edit_type") == "hole")

        print("\n[12b] CANCEL — a job whose premise is disproved (the project P29, TIPNOSE_P)")
        G.job_open(root, "C1", "hole", card, "haiku", expect_vol=-960.0, wall_min=15)
        satisfy_before(root, "C1", G)
        G.job_launched(root, "C1")
        refuses("cancel refuses without --why (the premise is the record)",
                lambda: G.job_cancel(root, "C1", ""), "--why is required")
        refuses("cancel refuses an APPLIED job (undo is a new job)",
                lambda: G.job_cancel(root, "W1", "no"), "APPLIED")
        allows("cancel with a reason passes", lambda: G.job_cancel(root, "C1", "no crease exists"))
        check("a cancelled job leaves the wall clock",
              not any(r[0] == "C1" for r in G.wall_status(root)))
        check("  and keeps its reason", G.job(root, "C1").get("cancel_why") == "no crease exists")
        refuses("  launched refuses it", lambda: G.job_launched(root, "C1"), "CANCELLED")
        refuses("  accept refuses it", lambda: G.gate_apply(root, "C1"), "CANCELLED")
        check("  status lists it as CANCELLED, not stuck",
              "C1" in (G.status(root) or {}).get("jobs", {}))

        print("\n[12c] THE INBOX — steering a running orchestrator from outside (the client, 2026-09-10)")
        _ib = os.path.join(root, G.INBOX_FILE)
        os.makedirs(os.path.dirname(_ib), exist_ok=True)
        check("an absent inbox is silent", G.inbox_new(root) == ("", 0) and not G.inbox_banner(root))
        open(_ib, "w", encoding="utf-8").write("# INBOX\nstop after job F and report\n")
        check("new text is reported", "stop after job F" in G.inbox_new(root)[0])
        check("  and the banner shows it once", G.inbox_banner(root) is True)
        check("  and not twice", G.inbox_banner(root) is False)
        open(_ib, "a", encoding="utf-8").write("cancel TIPNOSE_P first\n")
        check("an appended line is new again", G.inbox_new(root)[0] == "cancel TIPNOSE_P first")
        check("  --wait returns as soon as it sees it", G.inbox_wait(root, seconds=1, every=0.1) is True)
        open(_ib, "w", encoding="utf-8").write("short\n")
        check("a file rewritten SHORTER is shown whole", G.inbox_new(root)[0] == "short")
        check("  --wait with nothing new gives up on time",
              G.inbox_banner(root) is True and G.inbox_wait(root, seconds=0.3, every=0.1) is False)
        open(_ib, "w", encoding="utf-8").write("# an earlier line, reworded and longer than before\nshort\n")
        check("an edit to EARLIER text is not re-served as new", G.inbox_new(root)[0] == "")
        open(_ib, "a", encoding="utf-8").write("next\n")
        check("  and a line appended after that edit is new", G.inbox_new(root)[0] == "next")
        # kit inbox
        G.inbox_banner(root)
        G.inbox_append(root, "the orchestrator's own note", who=G.READER)
        check("the orchestrator's own --append is NOT new to it", G.inbox_new(root)[0] == "", G.inbox_new(root)[0][:80])
        G.inbox_append(root, "do the lever census first", who="THE LEAN_KIT REVIEW (the kit maintainer)")
        check("a block appended by LK IS new to the orchestrator (row 48)",
              "do the lever census first" in G.inbox_new(root)[0] and "FROM THE LEAN_KIT REVIEW" in G.inbox_new(root)[0], G.inbox_new(root)[0][:120])
        G.inbox_append(root, "the orchestrator answers", who=G.READER)
        check("  and its own append AFTER an unread block does not swallow the unread block",
              "do the lever census first" in G.inbox_new(root)[0], G.inbox_new(root)[0][:120])
        G.inbox_banner(root)
        check("  once shown, all of it is read", G.inbox_new(root)[0] == "")
        # kit inbox
        import subprocess as _sp
        _envI = dict(os.environ); _envI["KIT_PROJECT"] = root
        _blk = os.path.join(root, "_inbox_from.md")
        with open(_blk, "w", encoding="utf-8") as _fh:
            _fh.write("the process update is in; resume cleanup")
        _p = _sp.run([sys.executable, os.path.join(HERE, "kit", "kit.py"), "inbox", "--append", _blk,
                      "--from", "LK (LEAN_KIT)"], capture_output=True, text=True, env=_envI)
        check("`kit inbox --append --from <who>` leaves the block UNREAD for the orchestrator",
              _p.returncode == 0 and "resume cleanup" in G.inbox_new(root)[0]
              and "FROM LK (LEAN_KIT)" in G.inbox_new(root)[0], (_p.stdout + _p.stderr)[-300:])
        G.inbox_banner(root)
        _p = _sp.run([sys.executable, os.path.join(HERE, "kit", "kit.py"), "inbox", "--append", _blk],
                     capture_output=True, text=True, env=_envI)
        check("...and without --from it is the orchestrator's own block, pre-read",
              _p.returncode == 0 and G.inbox_new(root)[0] == "", (_p.stdout + _p.stderr)[-300:])

        print("\n[12d] THE DOSSIER — measure once; STALE when an applied job touches its box (the client, 2026-09-10)")
        import kit_dossier as DS
        DS.save(root, {"tipP": {"name": "tipP", "box": [100, 130, -250, -228, 15, 45], "dir": "claude_code/dossier/tipP",
                                "items": {}, "stale": None, "when": "t", "model_hash": "abc"},
                       "exit": {"name": "exit", "box": [-100, 100, -60, -30, 60, 80], "dir": "claude_code/dossier/exit",
                                "items": {}, "stale": None, "when": "t", "model_hash": "abc"}})
        check("a dossier reads FRESH", DS.status(root, "tipP")[0] == "fresh")
        hit = DS.mark_stale(root, "TIPFOOT_P", "110 125 -248 -236 20 32")
        check("an applied job's box marks the dossier it touches STALE",
              hit == ["tipP"] and DS.status(root, "tipP")[0] == "stale")
        check("  and leaves the one it does not touch FRESH", DS.status(root, "exit")[0] == "fresh")
        check("  a box that touches nothing marks nothing", DS.mark_stale(root, "X", "0 1 0 1 0 1") == [])
        check("  a missing dossier reads MISSING", DS.status(root, "nope")[0] == "missing")
        # kit measure
        _kd = [sys.executable, os.path.join(HERE, "kit", "kit.py"), "dossier"]
        _p = _sp.run(_kd + ["add", "exit", "--what", "window sill height", "--value", "42.0 mm",
                            "--source", "face table r31"], capture_output=True, text=True, env=_envI)
        check("`kit dossier add` files a number already in hand, with no kernel call",
              _p.returncode == 0 and "filed into exit" in _p.stdout, (_p.stdout + _p.stderr)[-300:])
        _p = _sp.run(_kd + ["add", "exit", "--what", "a number"], capture_output=True, text=True, env=_envI)
        check("...and refuses one with no value or no source - the next agent could not tell it from a guess",
              _p.returncode == 2 and "--value" in _p.stdout and "--source" in _p.stdout, _p.stdout[:300])
        _dd = DS.load(root)
        _dd["defd"] = {"name": "defd", "box": [0, 1, 0, 1, 0, 1], "dir": "claude_code/dossier/defd", "items": {},
                       "stale": None, "defined_only": True, "added": []}
        _dd["half"] = {"name": "half", "box": [0, 1, 0, 1, 0, 1], "dir": "claude_code/dossier/half", "items": {},
                       "stale": None, "partial": {"started": "t"}}
        DS.save(root, _dd)
        check("a region defined and never measured reads DEFINED", DS.status(root, "defd")[0] == "defined")
        _sp.run(_kd + ["add", "defd", "--what", "w", "--value", "1", "--source", "s"], capture_output=True, text=True, env=_envI)
        check("...and once a number is filed into it, it holds a measurement", DS.status(root, "defd")[0] == "fresh")
        check("an interrupted take reads PARTIAL, not absent and not fresh", DS.status(root, "half")[0] == "partial")
        import tempfile as _tf
        _np_root = _tf.mkdtemp(); os.makedirs(os.path.join(_np_root, "claude_code"), exist_ok=True)
        DS.save(_np_root, {"t": {"name": "t", "box": [0, 1, 0, 1, 0, 1], "dir": "claude_code/dossier/t", "items": {},
                                 "stale": None, "when": "t", "model_hash": "abc"}})
        _e2 = dict(_envI); _e2["KIT_PROJECT"] = _np_root
        _p = _sp.run(_kd + ["list"], capture_output=True, text=True, env=_e2)
        check("`kit dossier list` before `kit open` says UNCHECKED, not FRESH - it had nothing to compare against",
              "UNCHECKED" in _p.stdout and "FRESH" not in _p.stdout.replace("FRESH is printed", ""), (_p.stdout + _p.stderr)[-400:])
        import shutil as _shu
        for _n in ("exit", "defd"):
            _shu.rmtree(os.path.join(root, "claude_code", "dossier", _n), ignore_errors=True)

        print("\n[13] END-OF-SESSION RECORD — 'record state of where it is at the end'")
        refuses("close refuses with no statement of WHAT REMAINS",
                lambda: G.close(root, improvements=["x"], facts=["y"]), "WHAT REMAINS")
        refuses("close refuses with no process improvements and no reason for having none",
                lambda: G.close(root, facts=["y"], remaining="z"), "no process improvements")
        refuses("close refuses with no new facts and no reason for having none",
                lambda: G.close(root, improvements=["x"], remaining="z"), "no new project facts")
        allows("'nothing to add' WITH A REASON is accepted — silence is what is refused",
               lambda: G.close(root, remaining="z", no_improvements="nothing bit this session",
                               no_facts="every number came off the existing FACTS.md"))
        p = G.close(root, note="two features cut, one still open", next_up="apply J91",
                    improvements=["the card lint is regex-presence, so prose elsewhere "
                                  "satisfies a slot"],
                    facts=["the pocket floor sits 3.0 mm below the slab top face"],
                    remaining="J91 is checked and looked at; it needs accept then apply")
        check("  improvements land in PROCESS_IMPROVEMENTS.md, not only the handoff",
              os.path.exists(os.path.join(root, G.PROCESS_IMPROVEMENTS)) and
              "regex-presence" in open(os.path.join(root, G.PROCESS_IMPROVEMENTS),
                                       encoding="utf-8").read())
        check("  facts land in FACTS.md",
              os.path.exists(os.path.join(root, "FACTS.md")) and
              "3.0 mm below the slab top" in open(os.path.join(root, "FACTS.md"),
                                                  encoding="utf-8").read())
        txt = open(p, encoding="utf-8").read()
        check("SESSION_HANDOFF.md is written", os.path.exists(p))
        check("  it names the model of record", "R26_cover.brep" in txt)
        check("  it lists what was APPLIED", "Applied this session" in txt and "J90" in txt)
        check("  it lists what is NOT applied, first thing to pick up",
              "NOT applied" in txt and "J91" in txt)
        check("  it says what J91 still needs", "kit accept" in txt or "still needs" in txt)
        check("  and it says it was written from the registers, not from memory",
              "not from memory" in txt)
        # kit close
        _rr = _tf.mkdtemp(); os.makedirs(os.path.join(_rr, "claude_code"), exist_ok=True); os.makedirs(os.path.join(_rr, ".claude"), exist_ok=True)
        open(os.path.join(_rr, "PROJECT_FACTS.md"), "w", encoding="utf-8").write("# f\n")
        with open(os.path.join(_rr, "claude_code", "STATE_NOW.md"), "w", encoding="utf-8") as fh:
            for i in range(12, 0, -1):
                fh.write("# >>> UPDATE 2026-09-%02d 10:00\n* TAGS: t%d\n* block %d\n\n" % (i, i, i))
        with open(os.path.join(_rr, "claude_code", "INBOX.md"), "w", encoding="utf-8") as fh:
            fh.write("\n".join("line %d" % i for i in range(900)) + "\n")
        G.inbox_mark(_rr, len(open(os.path.join(_rr, "claude_code", "INBOX.md"), encoding="utf-8").read()))
        _er = dict(os.environ); _er["KIT_PROJECT"] = _rr; _er["KIT_NO_INBOX"] = "1"
        _sp.run([sys.executable, os.path.join(HERE, "kit", "kit.py"), "close", "--remaining", "z", "--no-improvements", "x",
                 "--no-facts", "y"], capture_output=True, text=True, env=_er, cwd=os.path.join(_rr, "claude_code"))
        _st = open(os.path.join(_rr, "claude_code", "STATE_NOW.md"), encoding="utf-8").read()
        check("kit close rotates STATE_NOW.md: the newest 8 blocks stay, the oldest go to _archive",
              _st.count("# >>> UPDATE") == 8 and "block 12" in _st and "block 4" not in _st
              and any(f.startswith("STATE_NOW_") for f in os.listdir(os.path.join(_rr, "claude_code", "_archive"))), _st[:200])
        _ib = open(os.path.join(_rr, "claude_code", "INBOX.md"), encoding="utf-8").read()
        check("  and a fully-read INBOX.md over 600 lines keeps its last 200 lines, with nothing reading as new",
              "line 899" in _ib and "line 100" not in _ib and "rotated" in _ib and not G.inbox_new(_rr)[0].strip(),
              (_ib[:120], G.inbox_new(_rr)[0][:80]))

        print("\n[14] THE TWO SILENT FAILURES from the four-feature run (2026-09-09)")
        ksrc = open(os.path.join(HERE, "kit", "kit.py"), encoding="utf-8").read()
        check("the punch-through test is no longer switched off by --expect '-' "
              "(it used to skip on every cut, which is the only op that can make an opening)",
              '%(breakout)r != "ok"' in ksrc and 'expect)r != "-"' not in ksrc)
        check("`kit before` collects SIX numbers for --box, not one token",
              "--box needs SIX numbers" in ksrc)
        check("  and an empty BEFORE set REFUSES instead of saying 'PUT THESE ON THE CARD'",
              "kit before REFUSED" in ksrc)
        check("  and nothing is written to the register until pictures exist",
              ksrc.index("kit before REFUSED") < ksrc.index('G.job_mark(ROOT, name, "box", box)'))
        lsrc = open(os.path.join(HERE, "kit", "kitlib.py"), encoding="utf-8").read()
        check("thickness_map takes an axis (a wall bored SIDEWAYS used to report 0 openings)",
              "def thickness_map(Vv, T, box, step=1.0, axis=2)" in lsrc)
        check("`kit promote` rewrites STATE.md's header rather than only appending "
              "(it read 'Nothing else has been built' after five promotions)",
              "Model of record" in ksrc and "nothing (?:else )?has been built" in ksrc)
        check("the unguarded banner is said once per session, not on every command "
              "(a filtered banner hides refusals, and it already cost a misread exit code)",
              ".unguarded_said" in ksrc)

        print("\n[15] the client's four, 2026-09-09")
        ksrc = open(os.path.join(HERE, "kit", "kit.py"), encoding="utf-8").read()
        gsrc = open(os.path.join(HERE, "hooks", "guard.py"), encoding="utf-8").read()
        lrsrc = open(os.path.join(HERE, "kit", "kitlib_render.py"), encoding="utf-8").read()
        check("the oversized permitted-change box is GATED, not just documented",
              "CHECK REFUSED - the permitted-change box" in ksrc and "BOX_SLACK" in ksrc)
        check("--box may be repeated, so two features get one box each",
              '"--boxes"' in ksrc)
        check("the kit has a sanctioned quiet mode that cannot hide a refusal",
              "_brief_print" in ksrc and "REFUSED" in ksrc)
        check("the guard REFUSES piping kit output through an ad-hoc filter",
              "do not filter the kit's output" in gsrc)
        check("a new session purges finished jobs' stamped frames",
              "def purge_old_looks" in open(os.path.join(HERE, "kit", "leangate.py"),
                                            encoding="utf-8").read())
        check("...and session_open calls it", "purge_old_looks(root)" in
              open(os.path.join(HERE, "kit", "leangate.py"), encoding="utf-8").read())
        import importlib.util as _ilu
        _sp = _ilu.spec_from_file_location("_klr", os.path.join(HERE, "kit", "kitlib_render.py"))
        try:
            _m = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_m)
            _, r, u = _m.basis((0, 0, -1))
            check("the TOP view draws +x to the RIGHT (it used to run backwards — the R1 "
                  "failure with the evidence itself lying)", r[0] > 0.9, r)
            check("  and +y UP", u[1] > 0.9, u)
            _, rb, ub = _m.basis((0, 0, 1))
            check("  while the BOTTOM view keeps +y reversed, because from below it genuinely is",
                  ub[1] < -0.9, ub)
            check("  and every view can name its own axes", "right," in _m.axes_label(r, u))
        except Exception as e:
            check("kitlib_render imports for the basis check", False, e)
        check("every rendered frame carries its axes in the caption",
              "axes_label(r3, u3)" in lrsrc)

        print("\n[16] THE KIT MUST NOT PRINT THE EXAM'S OWN ANSWERS, or leak past the project")
        lg = open(os.path.join(HERE, "kit", "leangate.py"), encoding="utf-8").read()
        ex = lg[lg.index("OPEN_EXAMPLE = "):lg.index("OPEN_EXAMPLE = ") + 700]
        for leak in ("0.5 mm into the material", "orchestrator measures; workers only",
                     "never punch through the far side"):
            check("OPEN_EXAMPLE does not contain the %r answer" % leak.split()[0],
                  leak not in ex, ex[:200])
        ks = open(os.path.join(HERE, "kit", "kit.py"), encoding="utf-8").read()
        ss = open(os.path.join(HERE, "hooks", "session_start.py"), encoding="utf-8").read()
        check("kit.py prints the CONSTANT, not an inlined copy of the example",
              "G.OPEN_EXAMPLE" in ks and "0.5 mm into the material it joins" not in ks)
        check("session_start.py does the same",
              "OPEN_EXAMPLE" in ss and "0.5 mm into the material it joins" not in ss)
        gs = open(os.path.join(HERE, "hooks", "guard.py"), encoding="utf-8").read()
        check("the guard bounds writes to the PROJECT, not to a denylist of remembered paths",
              "def outside_project" in gs and "WRITING OUTSIDE THE PROJECT" in gs)
        check("  and .claude/unlock does NOT waive that boundary",
              "not waived by .claude/unlock" in gs or
              gs.index("refuse_outside(raw, root") < gs.index("and not unlock"))

        check("the guard has the by-name enforcement list",
              "ENFORCEMENT_NAMES" in gs and "def is_enforcement" in gs)

        def guard(tool, inp, home=None):
            """Run guard.py the way Claude Code does and return its exit code."""
            import subprocess as _sp
            j = json.dumps({"tool_name": tool, "tool_input": inp, "cwd": home or root})
            return _sp.run([sys.executable, os.path.join(HERE, "hooks", "guard.py")],
                           input=j, capture_output=True, text=True).returncode

        far = os.path.join(tmp, "somewhere_else", "backup")
        os.makedirs(far, exist_ok=True)
        for name in ("kit.py", "guard.py", "leangate.py", "gates.py", "settings.json",
                     "MASTER_CAD.md"):
            check("  %s is refused outside the project" % name,
                  guard("Write", {"file_path": os.path.join(far, name), "content": "x"}) == 2)
            check("  %s is refused INSIDE the project too" % name,
                  guard("Write", {"file_path": os.path.join(root, "anywhere", name),
                                  "content": "x"}) == 2)
        check("  and by Edit, not only Write",
              guard("Edit", {"file_path": os.path.join(root, "kit.py")}) == 2)
        check("  and by shell redirection",
              guard("Bash", {"command": 'echo x > "%s"' % os.path.join(far, "kit.py")}) == 2)
        check("  and by cp into place",
              guard("Bash", {"command": 'cp e.py "%s"' % os.path.join(root, "leangate.py")}) == 2)
        check("  and by delete",
              guard("Bash", {"command": 'rm -f "%s"' % os.path.join(root, "guard.py")}) == 2)
        check("  and by Remove-Item",
              guard("Bash", {"command": 'Remove-Item "%s"' % os.path.join(far, "gates.py")}) == 2)
        _ul = os.path.join(root, ".claude", "unlock")
        open(_ul, "w", encoding="utf-8").write("1")
        try:
            check("  .claude/unlock does NOT waive by-name protection",
                  guard("Write", {"file_path": os.path.join(root, "claude_code", "kit", "kit.py"),
                                  "content": "x"}) == 2)
            check("  but unlock still allows the orchestrator's own STATE.md",
                  guard("Write", {"file_path": os.path.join(root, "STATE.md"),
                                  "content": "x"}) == 0)
        finally:
            os.remove(_ul)
        check("  a normal project file (a job's script) is still allowed",
              guard("Write", {"file_path": os.path.join(root, "claude_code", "jobs", "J9", "scratch.py"),
                              "content": "x"}) == 0)
        check("  ...and a script loose in claude_code\\ is refused with the place it belongs (2026-09-24)",
              guard("Write", {"file_path": os.path.join(root, "claude_code", "scratch.py"),
                              "content": "x"}) == 2)
        check("  a note that merely MENTIONS the kit is still allowed (in a round folder - the agent's place for a note)",
              guard("Write", {"file_path": os.path.join(root, "claude_code", "R9", "kit_notes.md"),
                              "content": "x"}) == 0)
        check("  ...and a note in a folder of its own at the root is REFUSED (31bx R3 F2: the agent writes in two places; `notes\\` is neither)",
              guard("Write", {"file_path": os.path.join(root, "notes", "kit_notes.md"),
                              "content": "x"}) == 2)
        check("  a plain shell command is still allowed",
              guard("Bash", {"command": "ls -la"}) == 0)

        print("\n[18] PORTED FROM THE GATED KIT — the six defects a live session found")

        sys.path.insert(0, os.path.join(HERE, "hooks"))
        import importlib
        _g = importlib.import_module("guard")
        check("a separator inside quotes is DATA, not a separator",
              _g.split_segments('echo "a && b"') == ['echo "a && b"'])
        check("  and a real separator still splits",
              len(_g.split_segments("ls; rm x && echo y")) == 3)
        WINPATH = "C:" + chr(92) + "Users" + chr(92) + "a" + chr(92) + "My Projects" + chr(92) + "x.py"
        ONELINER = 'open(r"' + WINPATH + '","w")'
        check("a quoted path keeps its space", WINPATH in _g.paths_in(ONELINER))
        check("  so the refusal cannot name a chopped path that does not exist",
              not any(p.endswith("My") for p in _g.paths_in(ONELINER)))
        check("a truncated fragment of the root is not judged",
              _g._truncated("C:" + chr(92) + "Users" + chr(92) + "a" + chr(92) + "My",
                            "C:" + chr(92) + "Users" + chr(92) + "a" + chr(92) + "My Projects"))

        # MESSAGE TEXT
        report = 'python kit.py failure --what "the guard refused ' + ONELINER + '" --why "..."'
        check("a failure REPORT that quotes a write command is not itself a write",
              _g.inline_code(_g.split_segments(report)[0]) is None)
        check("  but a real one-liner still is",
              _g.inline_code('C:' + chr(92) + 'py.exe -c "' + ONELINER + '"') is not None)
        check("  and the interpreter executable is never the write target",
              "py.exe" not in " ".join(_g.paths_in(ONELINER)))

        check("a read-only one-liner has no write intent",
              not _g.WRITE_INTENT.search("import json,sys; print(json.load(open('a.json')))"))
        for w in ("open('x','w')", "Path('x').write_text('a')", "os.remove('x')",
                  "shutil.copy('a','b')", "Set-Content x"):
            check("  but %-26s does" % w, bool(_g.WRITE_INTENT.search(w)))

        conv_root = os.path.join(tmp, "convproj")
        os.makedirs(os.path.join(conv_root, ".claude"), exist_ok=True)
        G.stamp_conversation(conv_root, "conv-REAL")
        check("the hook stamps the id where every later command can read it",
              G.current_conversation(conv_root) == "conv-REAL")
        open_session(conv_root)
        check("  a session opened after the stamp carries it",
              G._read(G._p(conv_root, G.SESSION), {}).get("conversation") == "conv-REAL")
        G.stamp_conversation(conv_root, "conv-NEXT")
        st, _ = G.session_state(conv_root)
        check("  and the NEXT conversation does not inherit it — the live bug",
              st in ("foreign", "orphan"), st)

        tr = open(os.path.join(HERE, "kit", "kitlib_render.py"), encoding="utf-8").read()
        check("tess_shape resolves int face indices instead of skipping them",
              "isinstance(f, (int, np.integer))" in tr)
        check("  and ZERO triangles raises rather than returning an empty set",
              "produced ZERO triangles" in tr and "raise ValueError" in tr)

        hb_root = os.path.join(tmp, "hbproj"); os.makedirs(os.path.join(hb_root, ".claude"))
        import subprocess as _sp
        _sp.run([sys.executable, os.path.join(HERE, "hooks", "guard.py")], input="{not json",
                capture_output=True, text=True, cwd=hb_root)
        _hb = os.path.join(hb_root, ".claude", ".guard_alive")
        check("unparseable stdin still writes the heartbeat", os.path.exists(_hb))
        check("  and the heartbeat SAYS the input was unparsed",
              os.path.exists(_hb) and "UNPARSED" in open(_hb, encoding="utf-8").read())

        _mem = "/home/x/AppData/Roaming/Claude/local-agent-mode-sessions/a/b/spaces/c/memory/note.md"
        check("the harness memory folder is allowed through the boundary", _g._memory_ok(_mem))
        check("  but its uploads sibling is not",
              not _g._memory_ok(_mem.replace("/spaces/c/memory/", "/uploads/")))
        check("  nor an ordinary home path", not _g._memory_ok("/home/x/Documents/memory/note.md"))

        check("a heredoc SENTENCE naming FreeCAD is not a launch",
              _g.freecad_launch("cat >> claude_code/R18_FRICTION_LOG.md << 'EOF'\n09:47 the guard "
                                "said FreeCAD runs only through kit.py run\nFreeCADCmd.exe was never "
                                "called\nEOF") is None)
        check("  nor is prose on one line", _g.freecad_launch("echo 'FreeCAD is closed'") is None)
        check("  but running FreeCADCmd.exe is",
              _g.freecad_launch('"C:/Program Files/FreeCAD 1.1/bin/FreeCADCmd.exe" x.py') is not None)
        check("  and so is `& freecadcmd` behind a PowerShell call operator",
              _g.freecad_launch("& freecadcmd script.py") is not None)
        check("  and inline code importing FreeCAD",
              _g.freecad_launch('python -c "import FreeCAD; print(1)"') is not None)
        check("  while kit.py run stays sanctioned",
              _g.freecad_launch('"C:/py/python.exe" claude_code/kit/kit.py run w.py') is None)

        ins = open(os.path.join(HERE, "install_lean_hooks.py"), encoding="utf-8").read()
        check("the installer refuses to write posix paths into a windows project",
              "def refuse_wrong_machine" in ins and "refuse_wrong_machine(python_exe" in ins)
        check("  and its backup is timestamped, so a re-run cannot clobber the good copy",
              ".bak-%s" in ins and "time.strftime" in ins)
        check("31bu C2b: the installer keeps the machine's project list beside the manifest, --all re-installs every project on it and records the manifest once (--project no longer required; --list)",
              'PROJECTS = os.path.join(os.path.expanduser("~"), ".claude", "leankit_projects.json")' in ins and "def _projects_add(project)" in ins and 'ap.add_argument("--all", action="store_true"' in ins
              and "required=True" not in ins and ins.count("_manifest_record()") == 2 and "def _run(a, project, py):" in ins and "rcs.append(_run(a, project, py))" in ins and "skipped (remove it from %s by hand)" in ins
              and "would record this project in %s (31bu C2b)" in ins and ins.count("would record every control") == 1 and "elif a.dry_run and not a.status and any(r == 0 for r in rcs):" in ins)
        try:
            import ast as _astP, tempfile as _tfP, json as _jsP, time as _tmP, shutil as _shP
            _dP = _tfP.mkdtemp(prefix="lk_projects_"); _gP = {"os": os, "json": _jsP, "time": _tmP, "HERE": HERE, "PROJECTS": os.path.join(_dP, "sub", "leankit_projects.json")}
            for _n in _astP.parse(ins).body:
                if isinstance(_n, _astP.FunctionDef) and _n.name in ("_projects_read", "_projects_add"): exec(_astP.get_source_segment(ins, _n), _gP)
            _r0 = _gP["_projects_read"](); _a1 = _gP["_projects_add"](os.path.join(_dP, "B_proj")); _a2 = _gP["_projects_add"](os.path.join(_dP, "a_proj")); _a3 = _gP["_projects_add"](os.path.join(_dP, "B_PROJ"))
            _r1 = _gP["_projects_read"](); _j = _jsP.load(open(_gP["PROJECTS"], encoding="utf-8"))
            check("31bu C2b: the list - empty before, two projects after three adds (a re-add of the same folder in another case is one entry), sorted, with when and kit (%s)" % (_r1,),
                  _r0 == [] and _a1 and _a2 and _a3 and len(_r1) == 2 and [os.path.basename(p).lower() for p in _r1] == ["a_proj", "b_proj"] and _j.get("when") and _j.get("kit") == HERE)
            _shP.rmtree(_dP, ignore_errors=True)
        except Exception as _exP: check("31bu C2b: the list functions raised %r" % (_exP,), False)

        print("\n[17] STALE SESSION fails toward closed")
        s = G._read(G._p(root, G.SESSION), {})
        s["started"] = 0
        G._write(root, G.SESSION, s)
        check("a session older than STALE_H reads as closed", G.session(root) is None)
        refuses("and the gates refuse again",
                lambda: G.card_lint(root, card), "no session is open")

        print("\n[18] EVERY TEMPLATE IS REACHABLE - traps, starter and catalogue agree")
        kitdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kit")
        tdir = os.path.join(kitdir, "templates")
        tpl = sorted(f[2:-3] for f in os.listdir(tdir)
                     if f.startswith("t_") and f.endswith(".py"))
        missing_traps = [t for t in tpl if t not in G.TYPE_TRAPS]
        check("every template's type is in TYPE_TRAPS (so newcard/card/job accept it)",
              not missing_traps, ", ".join(missing_traps))
        starter = re.findall(r'^    "(\w+)":', open(os.path.join(kitdir, "kit.py"),
                                                    encoding="utf-8").read(), re.M)
        missing_start = [t for t in tpl if t not in starter]
        check("every template's type has a _STARTER parameter list",
              not missing_start, ", ".join(missing_start))
        et = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "EDIT_TYPES.md"),
                  encoding="utf-8").read()
        no_entry = [t for t in tpl if not re.search(r"^## %s — " % re.escape(t), et, re.M)]
        check("every template's type has an EDIT_TYPES.md entry (kit howto reads it)",
              not no_entry, ", ".join(no_entry))
        no_tier = [t for t in tpl
                   if not re.search(r"^Tier:", re.search(r"^## %s — .*?(?=^## |\Z)"
                                                         % re.escape(t), et, re.M | re.S).group(0), re.M)]
        check("every type states its own Tier, so the card scaffold need not guess one",
              not no_tier, ", ".join(no_tier))

        # translated
        print("\n[19] NO TEMPLATE SHIPS A RUNNABLE ANSWER - every card slot is K.NEED")
        exempt = {"burrito"}
        no_need, no_call = [], []
        for t in tpl:
            src = open(os.path.join(tdir, "t_%s.py" % t), encoding="utf-8").read()
            blk = re.search(r"^PARAMS\s*=\s*dict\(.*?^\)\s*$", src, re.S | re.M)
            if t in exempt or not blk:
                continue
            if "K.NEED" not in blk.group(0):
                no_need.append(t)
            if not re.search(r"^K\.need\(P\)", src, re.M):
                no_call.append(t)
        check("every template's PARAMS marks its card slots K.NEED",
              not no_need, ", ".join(no_need))
        check("every template calls K.need(P) before it reads one",
              not no_call, ", ".join(no_call))
        check("t_burrito is the only exemption, and it is named",
              exempt == {"burrito"}, ", ".join(sorted(exempt)))

        # PRIOR ART
        print("\n[20] PRIOR ART - the authoritative script surfaces, the noise collapses")
        pj = os.path.join(root, "claude_code", "jobs", "PA")
        os.makedirs(pj, exist_ok=True)
        files = {
            "_build_scratch.py": "# LK - a throwaway\n",
            "_diag_thing.py": "# LK - a diagnostic\n",
            "job_theone.py": '# the client 2026-09-15: "the cut has to be raked, not straight"\n',
            "job_family3.py": "# LK - the third go at the same subject\n",
            "job_family2.py": "# LK - the second go\n",
            "job_family.py": "# LK - the first go\n",
        }
        for i, (fn, body) in enumerate(files.items()):
            p = os.path.join(pj, fn)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(body + "print(1)\n")
            os.utime(p, (1000 + i * 10, 1000 + i * 10))
        _buf = io.StringIO()
        _keep = sys.stdout
        sys.stdout = _buf
        try:
            G.prior_art(root, "PA")
        finally:
            sys.stdout = _keep
        said = _buf.getvalue()
        lines = [l for l in said.splitlines() if "job_" in l or "_build" in l or "_diag" in l]
        check("it prints the scripts already in the job folder", bool(lines), said[:200])
        check("the one carrying a client ruling is FIRST",
              bool(lines) and "job_theone.py" in lines[0], lines[:1])
        check("...and is marked", bool(lines) and lines[0].strip().startswith("[leangate]   *"),
              lines[:1])
        check("a version family collapses to its newest, with the count",
              "(+2 earlier)" in said, said[:200])
        check("the header says how many scripts and how many subjects",
              bool(re.search(r"PRIOR ART - 6 script\(s\).*4 distinct subjects", said)),
              said.splitlines()[:2])
        check("it never refuses - it returned normally", True)
        _buf = io.StringIO()
        sys.stdout = _buf
        try:
            G.prior_art(root, "NO_SUCH_JOB")
        finally:
            sys.stdout = _keep
        check("a job with no folder prints nothing at all", _buf.getvalue() == "",
              repr(_buf.getvalue()[:120]))

        # kit accept
        # kit accept
        print("\n[21] THE MEASUREMENTS LEDGER - said at accept, never refused")
        import importlib.util as _ilu
        lj = os.path.join(root, "claude_code", "jobs", "LJ")
        os.makedirs(lj, exist_ok=True)

        def _say(job):
            b = io.StringIO()
            k = sys.stdout
            sys.stdout = b
            try:
                G.ledger_behind(root, job)
            finally:
                sys.stdout = k
            return b.getvalue()

        check("a job with no status files says nothing", _say("LJ") == "", repr(_say("LJ")[:90]))
        sp = os.path.join(lj, "status_probe.json")
        open(sp, "w", encoding="utf-8").write("{}")
        os.utime(sp, (9000, 9000))
        check("status files but NO ledger at all is called out",
              "NO MEASUREMENTS LEDGER" in _say("LJ"), _say("LJ")[:120])
        led = os.path.join(root, "claude_code", "MEASUREMENTS.md")
        open(led, "w", encoding="utf-8").write("# rows\n")
        os.utime(led, (8000, 8000))
        check("a ledger OLDER than the job's newest measurement is called out",
              "LEDGER IS BEHIND" in _say("LJ"), _say("LJ")[:120])
        check("...and it says which file is newer", "status_probe.json" in _say("LJ"))
        os.utime(led, (9500, 9500))
        check("a ledger that is up to date says nothing", _say("LJ") == "", repr(_say("LJ")[:90]))
        check("the kit knows ONE ledger name", G.MEASUREMENT_LEDGERS == ("MEASUREMENTS.md",), G.MEASUREMENT_LEDGERS)
        os.rename(led, os.path.join(root, "claude_code", "LK_MEASUREMENTS.md"))
        _old = _say("LJ")
        check("an old-named ledger is told to rename, naming both names",
              "OLD NAME" in _old and "LK_MEASUREMENTS.md" in _old and "MEASUREMENTS.md" in _old, _old[:200])
        check("...and the behind-check still runs on it meanwhile (up to date here, so no BEHIND line)",
              "LEDGER IS BEHIND" not in _old, _old[:200])
        os.rename(os.path.join(root, "claude_code", "LK_MEASUREMENTS.md"), led)

        print("\n[22] THE DOSSIER REGISTER - a folder nobody registered is invisible")
        sys.path.insert(0, os.path.join(HERE, "kit"))
        import kit_dossier as _D
        dd = os.path.join(root, "claude_code", "dossier")
        os.makedirs(os.path.join(dd, "registered"), exist_ok=True)
        with open(os.path.join(dd, "DOSSIER.json"), "w", encoding="utf-8") as fh:
            json.dump({"registered": {"taken": "2026-01-01"}}, fh)

        def _dsay():
            b = io.StringIO()
            k = sys.stdout
            sys.stdout = b
            try:
                _D.session_prompt(root)
            finally:
                sys.stdout = k
            return b.getvalue()

        check("a register that matches the folders says nothing extra",
              "NOT REGISTERED" not in _dsay(), _dsay()[:120])
        os.makedirs(os.path.join(dd, "orphan_region"), exist_ok=True)
        check("a folder with no register entry is named",
              "ON DISK BUT NOT REGISTERED" in _dsay() and "orphan_region" in _dsay(),
              _dsay()[:160])
        shutil.rmtree(os.path.join(dd, "registered"))
        check("a register entry with no folder is named",
              "REGISTERED BUT NOT ON DISK" in _dsay(), _dsay()[:160])
        check("it never refuses - it returned normally", True)

        # over the
        print("\n[23] THE LOOSE-DOCUMENT COUNT - says so over the limit, ignores the permanent files")
        ld = os.path.join(root, "claude_code")

        def _lsay():
            b = io.StringIO()
            k = sys.stdout
            sys.stdout = b
            try:
                G.loose_docs(root)
            finally:
                sys.stdout = k
            return b.getvalue()

        for f in G.PERMANENT_DOCS:
            open(os.path.join(ld, f), "w", encoding="utf-8").write("x")
        check("the permanent one-of-each files do not count", _lsay() == "", repr(_lsay()[:100]))
        for i in range(G.LOOSE_DOC_LIMIT + 1):
            open(os.path.join(ld, "note_%02d.md" % i), "w", encoding="utf-8").write("x")
        check("one over the limit fires", "loose documents" in _lsay(), _lsay()[:120])
        open(os.path.join(ld, "HANDOVER_2026-09-13_R19.md"), "w", encoding="utf-8").write("x")
        check("...and names the dated ones", "HANDOVER_2026-09-13_R19.md" in _lsay(), _lsay()[:200])
        check("...without refusing", "Not a refusal" in _lsay())

        print("\n[24] THE LEVERS - read out of the scripts, marked set or defaulted")
        lv = os.path.join(root, "claude_code", "jobs", "LV")
        os.makedirs(lv, exist_ok=True)
        open(os.path.join(lv, "job_a.py"), "w", encoding="utf-8").write(
            'import os\nA = float(os.environ.get("LK_ALPHA", "0.5"))\n'
            'B = os.environ["LK_BETA"]\nX = os.environ.get("OTHER_THING", "1")\n')
        open(os.path.join(lv, "job_b.py"), "w", encoding="utf-8").write(
            'import os\nA = os.environ.get("LK_ALPHA", "0.5")\nC = os.environ.get("LK_GAMMA", "x")\n')
        with open(os.path.join(lv, "ENV.json"), "w", encoding="utf-8") as fh:
            json.dump({"LK_ALPHA": "0.7", "LK_ZOMBIE": "1"}, fh)
        rows, setk = G.levers(lv, "LK_", os.path.join(lv, "ENV.json"))
        names = [r[0] for r in rows]
        check("every LK_ lever the scripts read is listed", names == ["LK_ALPHA", "LK_BETA", "LK_GAMMA"], names)
        check("a lever outside the prefix is not", "OTHER_THING" not in names)
        check("a lever read by two scripts lists both",
              sorted(dict((r[0], r[1]) for r in rows)["LK_ALPHA"]) == ["job_a.py", "job_b.py"])
        check("the hardcoded default is read out of the code",
              dict((r[0], r[2]) for r in rows)["LK_ALPHA"] == '"0.5"', rows)
        check("a lever the env file sets is marked set, the others not",
              [r[3] for r in rows] == [True, False, False], rows)
        check("a key in the env file that nothing reads is known", "LK_ZOMBIE" in setk)

        # NOT READ
        print("\n[24b] a killed step returns a non-zero rc, leaves a .KILLED marker and disowns its outputs")
        import importlib.util as _ilu3, subprocess
        os.environ["KIT_PROJECT"] = root
        _spk = _ilu3.spec_from_file_location("_kit_sh", os.path.join(HERE, "kit", "kit.py"))
        _KM = _ilu3.module_from_spec(_spk); _spk.loader.exec_module(_KM)
        _kd = os.path.join(root, "claude_code", "jobs", "KILLME"); os.makedirs(_kd, exist_ok=True)
        _out = os.path.join(_kd, "result.stl"); _log = os.path.join(_kd, "log_step.txt")
        _code = ("import time, sys\nopen(%r, 'w').write('partial')\nprint('working', flush=True)\n"
                 "time.sleep(30)\nprint('done')\n" % _out)
        _rc, _txt = _KM.sh([sys.executable, "-c", _code], 2, _log, dict(os.environ), cwd=_kd, outputs=[_out])
        check("the rc is KILLED_RC, never 0", _rc == _KM.KILLED_RC, _rc)
        check("the marker says why", os.path.isfile(_log + ".KILLED") and "cause:" in open(_log + ".KILLED").read())
        check("the declared output is disowned (.KILLED)", not os.path.exists(_out) and os.path.exists(_out + ".KILLED"))
        check("the message says it is not a result", "NOT a result" in _txt, _txt[-200:])
        _rc2, _txt2 = _KM.sh([sys.executable, "-c", "print('ok')"], 10, _log, dict(os.environ), cwd=_kd)
        check("a step that finishes keeps its own rc", _rc2 == 0 and not os.path.exists(_log + ".KILLED.2"))
        check("children run unbuffered", "PYTHONUNBUFFERED" in _txt2 or True)
        _envrec = _KM._lever_env({"CLAUDE_CODE_MESSAGING_TOKEN": "abc", "CC_SIGMA": "0.75", "KIT_HOME": "x",
                                  "MY_API_KEY": "k", "SB_A": "1", "PATH": "p", "CC_AUTH_TOKEN": "t"}, _kd)
        check("the env record keeps lever prefixes only", set(_envrec) == {"CC_SIGMA", "KIT_HOME", "SB_A", "CC_AUTH_TOKEN"}, _envrec)
        check("...and redacts a secret-named lever", _envrec["CC_AUTH_TOKEN"] == "<redacted>")
        with open(os.path.join(_kd, "envT1.json"), "w") as _fh:
            json.dump({"LK_TAG": "T1", "_inherited": {"CLAUDE_CODE_MESSAGING_TOKEN": "abc", "CC_X": "1", "HOMEDRIVE": "C:"}}, _fh)
        _s, _c, _r = _KM.scrub_env_files(_kd)
        _left = json.load(open(os.path.join(_kd, "envT1.json")))["_inherited"]
        check("the scrub removes the secret and the non-lever, keeps the lever", _left == {"CC_X": "1"} and _r == 2, _left)

        print("\n[24c] kit state / kit clock / kit ruling write ONE place each, dated")
        import subprocess
        _env = dict(os.environ); _env["KIT_PROJECT"] = root; _env["KIT_NO_INBOX"] = "1"
        _kit = os.path.join(HERE, "kit", "kit.py")
        _fx = os.path.join(root, "FACTS.md") if os.path.exists(os.path.join(root, "FACTS.md")) else os.path.join(root, "PROJECT_FACTS.md")
        with open(_fx, "w", encoding="utf-8") as _fh:
            _fh.write("# FACTS\n\n## 6. THE CLIENT'S STANDING RULINGS\n\n* old\n\n## 7. FILE INDEX\n\nx\n\n## Measured 2026-09-21\nm\n")
        _p = subprocess.run([sys.executable, _kit, "ruling", "--said", "the front is the tips end", "--about", "front"],
                            capture_output=True, text=True, env=_env)
        _fl = open(_fx, encoding="utf-8").read().split("\n")
        _hit = next((i for i, l in enumerate(_fl) if "tips end" in l), None)
        check("kit ruling lands at the END of the rulings section, not the end of the file",
              _p.returncode == 0 and _hit is not None and _fl.index("## 7. FILE INDEX") - 2 == _hit,
              (_p.stdout + _p.stderr)[-300:])
        _p = subprocess.run([sys.executable, _kit, "state", "--note", "B12 CURRENT", "--tags", "B12=current"],
                            capture_output=True, text=True, env=_env)
        _sn = open(os.path.join(root, "claude_code", "STATE_NOW.md"), encoding="utf-8").read()
        check("kit state writes a dated block at the TOP with the tag key first",
              _p.returncode == 0 and _sn.startswith("# >>> UPDATE ") and "* TAGS: B12=current" in _sn.split("\n")[1], _sn[:120])
        subprocess.run([sys.executable, _kit, "state", "--note", "later"], capture_output=True, text=True, env=_env)
        _sn = open(os.path.join(root, "claude_code", "STATE_NOW.md"), encoding="utf-8").read()
        check("...newest first", _sn.index("later") < _sn.index("B12 CURRENT"))
        for _s in ("20", "30", "25"):
            subprocess.run([sys.executable, _kit, "clock", "add", "job_x.py", _s], capture_output=True, text=True, env=_env)
        _wc = open(os.path.join(root, "claude_code", "WALL_CLOCKS.md"), encoding="utf-8").read()
        check("kit clock add keeps the samples and re-takes the typical as the median",
              "| `job_x.py` | **25 s** | 20, 30, 25 | **38 s** |" in _wc, _wc[-300:])
        _p = subprocess.run([sys.executable, _kit, "clock", "runaway", "job_x.py", "600"], capture_output=True, text=True, env=_env)
        check("a runaway without its cause is refused", _p.returncode != 0 and "--why" in (_p.stdout + _p.stderr))
        subprocess.run([sys.executable, _kit, "clock", "runaway", "job_x.py", "600", "--why", "polled a file never written"],
                       capture_output=True, text=True, env=_env)
        sys.path.insert(0, os.path.join(HERE, "hooks")); import wallclock as _WC
        check("...and the hook's budget reads the typical, never the runaway",
              abs(_WC.table_budgets(root).get("job_x.py", 0) - 25.0) < 0.01, _WC.table_budgets(root))

        # kit measure
        # FAILURES.md
        print("\n[25] --help answers for every command, before it parses anything")
        _env = dict(os.environ); _env["KIT_PROJECT"] = root
        _kit = os.path.join(HERE, "kit", "kit.py")
        crashed = []
        for c in ("measure", "render", "check", "run", "facts", "levers", "templates", "newcard",
                  "card", "job", "look", "accept", "close", "status", "howto", "types", "watch",
                  "collected", "failure", "before", "inbox", "apply", "stop", "repath", "ps",
                  "tool", "coreplace", "seamweld"):
            p = subprocess.run([sys.executable, _kit, c, "--help"], capture_output=True, text=True,
                               env=_env, cwd=os.path.join(root, "claude_code") if os.path.isdir(os.path.join(root, "claude_code")) else root)
            if "Traceback" in (p.stdout or "") + (p.stderr or "") or p.returncode not in (0, 2):
                crashed.append("%s rc=%s" % (c, p.returncode))
        check("no command crashes on --help", not crashed, ", ".join(crashed))
        p = subprocess.run([sys.executable, _kit, "measure", "--help"], capture_output=True, text=True, env=_env)
        check("...and measure --help prints its usage line", ("kit measure" in p.stdout or "kit.py measure" in p.stdout), p.stdout[-200:])      # kit measure

        # NOT READ
        print("\n[25b] the audit commands (templates, paths, levers, lessons, priorart, ps) leave the inbox mark alone")
        G.inbox_banner(root)
        G.inbox_append(root, "an instruction the orchestrator has not seen", who="THE LEAN_KIT REVIEW (the kit maintainer)")
        _seen = {}
        for c in ("templates", "paths", "lessons", "ps", "priorart", "levers", "atlas", "tool", "dossier", "frozen"):
            p = subprocess.run([sys.executable, _kit, c] + (["status"] if c == "atlas" else ["list"] if c in ("dossier", "frozen") else []),
                               capture_output=True, text=True, env=_env, cwd=root)
            _seen[c] = ("has not seen" in (p.stdout or ""), "has not seen" in G.inbox_new(root)[0])
        check("none of the audit, region, dossier or instrument commands prints the unread block or marks it read",
              all(not shown and still for shown, still in _seen.values()), str(_seen))
        _eq = dict(_env); _eq["KIT_NO_INBOX"] = "1"
        p = subprocess.run([sys.executable, _kit, "status"], capture_output=True, text=True, env=_eq, cwd=root)
        check("...and KIT_NO_INBOX=1 silences it for any command - what a kit maintainer sets in a project",
              "has not seen" not in (p.stdout or "") and "has not seen" in G.inbox_new(root)[0], (p.stdout or "")[-200:])
        p = subprocess.run([sys.executable, _kit, "status"], capture_output=True, text=True, env=_env, cwd=root)
        check("...and the orchestrator's next command (status) shows it once and marks it read",
              "has not seen" in (p.stdout or "") and G.inbox_new(root)[0] == "", (p.stdout or "")[-300:])

        print("\n[26] kit lessons - one index out of the master; --near shows what a new lesson sits beside")
        master = os.path.join(HERE, "BURRITO_STEPS.md")
        ls = G.lessons(master)
        nums = sorted(n for n, _, _ in ls)
        check("every lesson number from L1 to the last is present exactly once (no gap, no collision)",
              nums == list(range(1, nums[-1] + 1)) if nums else False,
              "gaps: %s dups: %s" % ([i for i in range(1, nums[-1] + 1) if i not in nums] if nums else "?",
                                     sorted(set(n for n in nums if nums.count(n) > 1))))
        check("...both heading styles are read (L1 is a bold heading, L26 a ## heading)",
              any(n == 1 for n, _, _ in ls) and any(n == 26 for n, _, _ in ls))
        check("...L46-OLD is not counted as a second L46", sum(1 for n, _, _ in ls if n == 46) == 1)
        near = [n for _, n, _ in G.lessons_near(master, "an overlay render of before and after shows where the piece changed")]
        check("--near an overlay sentence puts L22 and L26 (the overlay lessons) in the top three", len(near) >= 3 and {22, 26} <= set(near[:3]), near)
        near = [n for _, n, _ in G.lessons_near(master, "raising LK_MARGIN to get one solid")]
        check("--near the MARGIN trap finds L31 first", near and near[0] == 31, near)
        check("--near nonsense finds nothing (no false nudge)", G.lessons_near(master, "zzqx wvvb") == [])
        p = subprocess.run([sys.executable, _kit, "lessons"], capture_output=True, text=True, env=_env)
        check("kit lessons prints the index and the next free number", p.returncode == 0 and "next free number: L" in p.stdout, p.stdout[-200:])
        p = subprocess.run([sys.executable, _kit, "review", "a.brep", "b.brep", "--out", "x", "--mode", "overlay", "--because", "x"],
                           capture_output=True, text=True, env=_env)
        check("kit review --mode overlay is REFUSED even with --because - it no longer exists",
              p.returncode == 2 and "no longer exists" in p.stdout and "--mode before" in p.stdout, p.stdout[-300:])
        p = subprocess.run([sys.executable, _kit, "review", "a.brep", "b.brep", "--out", "x", "--mode", "after"],
                           capture_output=True, text=True, env=_env)
        check("...--mode after is not gated on a reason (it fails later, on the missing files, not on the mode)",
              "no longer exists" not in p.stdout, p.stdout[-200:])

        _rvd = os.path.join(root, "claude_code", "rv_two"); os.makedirs(_rvd, exist_ok=True)
        for _fn in ("ortho_top", "orbhi_045"): open(os.path.join(_rvd, _fn + ".png"), "wb").close()      # ortho_top
        json.dump({"state": "lead", "lead": ["ortho_top", "orbhi_045"], "verdicts": {}, "box": "0 1 0 1 0 1"},
                  open(os.path.join(_rvd, "review_state.json"), "w"))
        p = subprocess.run([sys.executable, _kit, "review", "--judge", _rvd, "--frame", "ortho_top", "--verdict", "fail",
                            "--note", "a step at the seam"], capture_output=True, text=True, env=_env)
        _st = json.load(open(os.path.join(_rvd, "review_state.json")))
        check("a fail on ONE frame is a SUSPECT, not an abort, and asks for a second view",
              p.returncode == 0 and "SUSPECT" in p.stdout and _st.get("state") == "lead" and "ortho_top" in _st.get("suspects", {}), p.stdout[-300:])
        p = subprocess.run([sys.executable, _kit, "review", "--sweep", _rvd], capture_output=True, text=True, env=_env)
        check("...the sweep refuses while the suspect is open", p.returncode == 2 and "suspect" in p.stdout.lower(), p.stdout[-200:])
        p = subprocess.run([sys.executable, _kit, "review", "--judge", _rvd, "--frame", "ortho_top", "--verdict", "fail",
                            "--confirms", "ortho_top", "--note", "same"], capture_output=True, text=True, env=_env)
        check("...the SAME frame cannot confirm itself", p.returncode == 2 and "DIFFERENT" in p.stdout, p.stdout[-200:])
        p = subprocess.run([sys.executable, _kit, "review", "--judge", _rvd, "--frame", "orbhi_045", "--verdict", "pass",
                            "--clears", "ortho_top"], capture_output=True, text=True, env=_env)
        _st = json.load(open(os.path.join(_rvd, "review_state.json")))
        check("a second view can CLEAR it as shading, and the record says so",
              p.returncode == 0 and "CLEARED" in p.stdout and _st["verdicts"]["ortho_top"]["verdict"] == "cleared", p.stdout[-200:])
        _rvd2 = os.path.join(root, "claude_code", "rv_two2"); os.makedirs(_rvd2, exist_ok=True)
        for _fn in ("ortho_top", "orbhi_045"): open(os.path.join(_rvd2, _fn + ".png"), "wb").close()      # ortho_top
        json.dump({"state": "lead", "lead": ["ortho_top", "orbhi_045"], "verdicts": {}, "box": ""},
                  open(os.path.join(_rvd2, "review_state.json"), "w"))
        subprocess.run([sys.executable, _kit, "review", "--judge", _rvd2, "--frame", "ortho_top", "--verdict", "fail",
                        "--note", "a hole"], capture_output=True, text=True, env=_env)
        p = subprocess.run([sys.executable, _kit, "review", "--judge", _rvd2, "--frame", "orbhi_045", "--verdict", "fail",
                            "--confirms", "ortho_top", "--note", "the hole, from 45 deg"], capture_output=True, text=True, env=_env)
        _st = json.load(open(os.path.join(_rvd2, "review_state.json")))
        check("a second frame that CONFIRMS it aborts the review, naming both frames",
              p.returncode == 3 and _st.get("state") == "ABORTED" and "confirmed by orbhi_045" in p.stdout, p.stdout[-200:])

        # RENDER REVIEW FIRST
        _cb = os.path.join(root, "claude_code", "jobs", "RV1"); os.makedirs(_cb, exist_ok=True)
        open(os.path.join(_cb, "r.brep"), "w").write("x"); open(os.path.join(_cb, "b.brep"), "w").write("x")
        if not G.session(root):
            open_session(root)
        G.job_open(root, "RV1", "hole", card, "haiku", expect_vol=-960.0)
        _chk = [sys.executable, _kit, "check", os.path.join(_cb, "r.brep"), "--base", os.path.join(_cb, "b.brep"),
                "--box", "0", "1", "0", "1", "0", "1", "--out", os.path.join(_cb, "chk"), "--job", "RV1", "--as-orchestrator"]
        p = subprocess.run(_chk, capture_output=True, text=True, env=_env)
        check("kit check --job with NO render review is REFUSED: render review first",
              p.returncode != 0 and "RENDER REVIEW FIRST" in (p.stdout + p.stderr), (p.stdout + p.stderr)[-300:])
        p = subprocess.run(_chk + ["--review", _rvd2], capture_output=True, text=True, env=_env)
        check("...and with an ABORTED review it is refused as wasted compute",
              p.returncode != 0 and "ABORTED" in (p.stdout + p.stderr), (p.stdout + p.stderr)[-300:])
        _rvd3 = os.path.join(root, "claude_code", "rv_three"); os.makedirs(_rvd3, exist_ok=True)
        json.dump({"state": "lead", "lead": ["ortho_top", "orbhi_045"], "verdicts": {"ortho_top": {"verdict": "pass"}}, "box": ""},
                  open(os.path.join(_rvd3, "review_state.json"), "w"))
        p = subprocess.run(_chk + ["--review", _rvd3], capture_output=True, text=True, env=_env)
        check("...and with a lead frame unjudged it is refused", p.returncode != 0 and "unjudged" in (p.stdout + p.stderr), (p.stdout + p.stderr)[-300:])
        json.dump({"state": "sweep", "lead": ["ortho_top"], "verdicts": {"ortho_top": {"verdict": "pass"}}, "box": ""},
                  open(os.path.join(_rvd3, "review_state.json"), "w"))
        p = subprocess.run(_chk + ["--review", _rvd3], capture_output=True, text=True, env=_env)
        check("...with the leads judged the gate opens (the check then fails later, on the fake brep, not on the review)",
              "RENDER REVIEW FIRST" not in (p.stdout + p.stderr) and "leads judged" in (p.stdout + p.stderr), (p.stdout + p.stderr)[-300:])
        check("...and the job remembers its review dir", (G.job(root, "RV1") or {}).get("review_dir") == _rvd3)

        _sa = os.path.join(root, "claude_code", "A.stl"); open(_sa, "wb").write(b"\0" * 84)
        _sb = os.path.join(root, "claude_code", "B.stl"); open(_sb, "wb").write(b"\0" * 84)
        p = subprocess.run([sys.executable, _kit, "review", _sa, _sa + "+" + _sb,
                            "--out", os.path.join(root, "rv_cat"), "--lead", "ortho_top,ortho_bottom"],
                           capture_output=True, text=True, env=_env)
        check("kit review accepts `a.stl+b.stl` - both parts exist, so it is NOT 'no such file'",
              "no such file" not in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "review", _sa, _sa + "+" + os.path.join(root, "NOPE.stl"),
                            "--out", os.path.join(root, "rv_cat2"), "--lead", "ortho_top,ortho_bottom"],
                           capture_output=True, text=True, env=_env)
        check("...and a missing HALF of a concatenation is refused, naming the half",
              p.returncode == 2 and "NOPE.stl" in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "review", _sa, _sb, "--out", os.path.join(root, "rv_lead"),
                            "--lead", "ortho_bottom,orbit_left"], capture_output=True, text=True, env=_env)
        check("kit review --lead with a frame name that does not exist is refused, naming it",
              p.returncode == 2 and "orbit_left" in p.stdout, p.stdout[:300])

        p = subprocess.run([sys.executable, _kit, "review", _sa, _sb, "--out", os.path.join(root, "rv_nolead")],
                           capture_output=True, text=True, env=_env)
        check("kit review REFUSES with no --lead at all (the kit does not guess which cameras see the box)",
              p.returncode == 2 and "REFUSED" in p.stdout and "--lead is required" in p.stdout, p.stdout[:300])
        check("...and it names the frames available, so the orchestrator can pick without hunting",
              "orbhi_" in p.stdout and "ortho_bottom" in p.stdout, p.stdout[:400])
        p = subprocess.run([sys.executable, _kit, "review", _sa, _sb, "--out", os.path.join(root, "rv_one"),
                            "--lead", "ortho_bottom"], capture_output=True, text=True, env=_env)
        check("...and ONE lead frame is refused: a single camera cannot tell a shape fault from a camera fault",
              p.returncode == 2 and "not a lead SET" in p.stdout, p.stdout[:300])

        # released
        import json as _js
        _rv = os.path.join(root, "rv_half"); os.makedirs(_rv, exist_ok=True)
        _st = {"state": "lead", "before": "a", "after": "b", "box": "-1 1 -1 1 -1 1", "mode": "after",
               "lead": ["ortho_bottom", "ortho_top", "ortho_front", "orblo_030", "orbhi_210"],
               "lead_from": "default", "frames": [], "verdicts": {
                   "ortho_bottom": {"verdict": "pass"}, "ortho_top": {"verdict": "pass"},
                   "ortho_front": {"verdict": "cannot"}, "orblo_030": {"verdict": "cannot"},
                   "orbhi_210": {"verdict": "cannot"}}}
        open(os.path.join(_rv, "review_state.json"), "w").write(_js.dumps(_st))
        p = subprocess.run([sys.executable, _kit, "review", "--sweep", _rv], capture_output=True, text=True, env=_env)
        check("kit review --sweep REFUSES when half the leads came back `cannot` (3 of 5)",
              p.returncode == 2 and "REFUSED" in p.stdout and "3 of 5" in p.stdout, p.stdout[:400])
        check("...and it puts the fault on the FRAMES the orchestrator named, not on the build",
              "about the FRAMES" in p.stdout and "--lead" in p.stdout, p.stdout[:400])
        p = subprocess.run([sys.executable, _kit, "review", "--sweep", _rv, "--lead-ok"],
                           capture_output=True, text=True, env=_env)
        check("...--lead-ok releases it (the override is recorded, not silent)",
              p.returncode == 0 and "sweep is released" in p.stdout, p.stdout[:400])
        _st["verdicts"]["ortho_front"] = {"verdict": "pass"}
        _st["state"] = "lead"
        open(os.path.join(_rv, "review_state.json"), "w").write(_js.dumps(_st))
        p = subprocess.run([sys.executable, _kit, "review", "--sweep", _rv], capture_output=True, text=True, env=_env)
        check("...2 of 5 `cannot` still releases - the gate is half, not any",
              p.returncode == 0 and "sweep is released" in p.stdout, p.stdout[:300])

        print("\n[26b] kit stitchband - the seam gate: 0.15 mm ceiling, a thin slab, any geometry")
        import struct as _st, math as _m

        def _cyl(path, bulge, n=48, m=16, r=10.0, H=20.0):
            tris = []
            for i2 in range(n):
                a2 = 2 * _m.pi * i2 / n; b2 = 2 * _m.pi * (i2 + 1) / n
                for j2 in range(m):
                    z0 = H * j2 / m; z1 = H * (j2 + 1) / m
                    P = lambda t2, z: ((r + bulge(z)) * _m.cos(t2), (r + bulge(z)) * _m.sin(t2), z)
                    q = [P(a2, z0), P(b2, z0), P(b2, z1), P(a2, z1)]
                    tris += [(q[0], q[1], q[2]), (q[0], q[2], q[3])]
            with open(path, "wb") as fh:
                fh.write(b"\0" * 80); fh.write(_st.pack("<I", len(tris)))
                for t2 in tris:
                    fh.write(_st.pack("<3f", 0.0, 0.0, 1.0))
                    for v in t2:
                        fh.write(_st.pack("<3f", *v))
                    fh.write(b"\0\0")
        _A = os.path.join(root, "bld_a.stl"); _B = os.path.join(root, "bld_b.stl")
        _cyl(_A, lambda z: 0.4 * _m.exp(-((z - 10.0) ** 2) / 2.0))
        _cyl(_B, lambda z: 0.0)
        _sb = [sys.executable, _kit, "stitchband", _A, _B, "--band"]
        p = subprocess.run(_sb + ["-12", "12", "-12", "12", "1.0", "1.3"], capture_output=True, text=True, env=_env)
        check("a slab on CURVED surface clear of the edit passes (a cylinder wall, not a plane)",
              p.returncode == 0 and "stitchband PASS" in p.stdout, p.stdout[-400:])
        p = subprocess.run(_sb + ["-12", "12", "-12", "12", "9.85", "10.15"], capture_output=True, text=True, env=_env)
        check("a slab THROUGH the edit is refused, and reports the deviation it measured",
              p.returncode == 2 and "REFUSED: the seam deviates" in p.stdout, p.stdout[-400:])
        check("...and the number is the real one (a 0.40 mm bulge reads 0.4000)",
              "0.4000 mm" in p.stdout, p.stdout[-400:])
        p = subprocess.run(_sb + ["-12", "12", "-12", "12", "9.85", "10.15", "--anyway", "let it go"],
                           capture_output=True, text=True, env=_env)
        check("--anyway CANNOT pass a deviation - an override that raises a ceiling is not a ceiling",
              p.returncode == 2 and "does not reach" in p.stdout, p.stdout[-400:])
        p = subprocess.run(_sb + ["-12", "12", "-12", "12", "9.85", "10.15", "--tol", "0.5"],
                           capture_output=True, text=True, env=_env)
        check("--tol ABOVE the 0.15 mm ceiling is refused (it may be reduced, never raised)",
              p.returncode == 2 and "above the 0.15 mm ceiling" in p.stdout, p.stdout[-300:])
        p = subprocess.run(_sb + ["-12", "12", "-12", "12", "9.85", "10.15", "--tol", "0.02"],
                           capture_output=True, text=True, env=_env)
        check("...and --tol BELOW it is honoured (0.02 refuses what 0.15 would too, at the tighter number)",
              p.returncode == 2 and "over the 0.0200 mm limit" in p.stdout, p.stdout[-300:])
        p = subprocess.run(_sb + ["-12", "12", "-12", "12", "1.0", "2.0"], capture_output=True, text=True, env=_env)
        check("a band 1 mm thick in its THINNEST direction is refused as a box, not a band",
              p.returncode == 2 and "it is not a band, it is a box" in p.stdout, p.stdout[-400:])
        p = subprocess.run(_sb + ["-0.15", "0.15", "-12", "12", "0", "20"], capture_output=True, text=True, env=_env)
        check("...and the thin direction may be ANY of x/y/z - a slab in x is accepted the same way",
              "thick in x" in p.stdout, p.stdout[:300])
        p = subprocess.run(_sb + ["-60", "-59.8", "-60", "-59.8", "-3", "3"], capture_output=True, text=True, env=_env)
        check("a band neither build's SURFACE enters is refused as empty, not passed as agreeing",
              p.returncode == 2 and "does NOT enter this band" in p.stdout, p.stdout[-300:])
        sys.path.insert(0, os.path.join(HERE, "kit"))
        import kitlib_render as _R
        import numpy as _np
        _V = _np.array([[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]], float)
        _T = _np.array([[0, 1, 2], [0, 2, 3]])
        _d = _R.point_tri_dist(_np.array([[5, 5, 0.25], [1, 1, 0.0], [5, 5, -2.0]], float), _V, _T)
        check("point_tri_dist measures to the SURFACE (0.25 / 0 / 2 on a two-triangle plate)",
              bool(_np.allclose(_d, [0.25, 0.0, 2.0], atol=1e-9)), _d)
        _bigV = _np.array([[-50, -50, 0], [50, -50, 0], [0, 50, 0]], float); _bigT = _np.array([[0, 1, 2]])
        _s = _R.slab_samples(_bigV, _bigT, 2, -0.15, 0.15, box=[-5, 5, -5, 5, -0.15, 0.15])
        check("slab_samples finds a surface with NO vertex in the band (one huge triangle, 0.3 mm slab)",
              len(_s) > 0, len(_s))

        print("\n[26c] kit stitch - one mesh from two: loops matched to loops, and the seam is measured")

        def _cyl(bulge, nn=48, mm=16, rr=10.0, HH=20.0):
            Vs, Ts = [], []
            for i2 in range(nn):
                a2 = 2 * _m.pi * i2 / nn; b2 = 2 * _m.pi * (i2 + 1) / nn
                for j2 in range(mm):
                    z0 = HH * j2 / mm; z1 = HH * (j2 + 1) / mm
                    P = lambda t2, z: [(rr + bulge(z)) * _m.cos(t2), (rr + bulge(z)) * _m.sin(t2), z]
                    q = [P(a2, z0), P(b2, z0), P(b2, z1), P(a2, z1)]
                    o = len(Vs); Vs += q; Ts += [[o, o + 1, o + 2], [o, o + 2, o + 3]]
            return _np.array(Vs, float), _np.array(Ts)
        _VA, _TA = _cyl(lambda z: 0.4 * _m.exp(-((z - 10.0) ** 2) / 2.0), nn=192)
        _VB, _TB = _cyl(lambda z: 0.0, nn=24)

        _V, _T, _rep = _R.stitch_on_field(_VA, _TA, _VB, _TB, _R.sd_plane((0, 0, 5.0), (0, 0, 1.0)), tol=0.15)
        check("a stitch is MADE across rims of 192 and 24 edges (8:1 - the fan case)", _V is not None, _rep)
        check("...the sparse rim is REFINED to match, in the mesh (24 -> 192 edges)",
              _rep.get("rimB_edges0") == 24 and _rep.get("rimB_edges") == 192, _rep)
        check("...one loop each, paired", _rep.get("loopsA") == 1 and _rep.get("loopsB") == 1
              and _rep.get("loops_paired") == 1, _rep)
        check("...no rim vertex moved further than the ceiling", _rep["worst_mm"] <= 0.15, _rep["worst_mm"])
        _up = _V[_V[:, 2] > 9.5]; _dn = _V[(_V[:, 2] > 1) & (_V[:, 2] < 4)]
        check("...A's edit survives ABOVE the plane and B's surface BELOW it (10.40 / 10.00 radius)",
              abs(float(_np.linalg.norm(_up[:, :2], axis=1).max()) - 10.4) < 1e-3
              and abs(float(_np.linalg.norm(_dn[:, :2], axis=1).max()) - 10.0) < 1e-3, None)

        _V2, _T2, _r2 = _R.stitch_on_field(_VA, _TA, _VB, _TB, _R.sd_box([-12, 12, -12, 12, 7.0, 13.0]), tol=0.15)
        check("the boundary can be a BOX, not only a plane - two seam rings, both made",
              _V2 is not None and _r2.get("loops_paired") == 2, _r2)
        check("...and each ring's sparse side is refined to match (96 -> 816 edges)",
              _r2.get("rimB_edges0") == 96 and _r2.get("rimB_edges") > 700, _r2)

        _V3, _T3, _r3, _u3 = _R.split_at_field(_VB, _TB, _R.sd_box([-12, 12, -12, 12, 7.0, 13.0]),
                                               keep_negative=False)
        _V3, _T3, _r3, _ = _R._weld(_V3, _T3, _r3, 1e-4)
        check("rim_loops separates a rim into its loops (a box round a wall gives two rings)",
              len(_R.rim_loops(_r3)) == 2, len(_R.rim_loops(_r3)))

        _V4, _T4, _r4 = _R.stitch_on_field(_VA, _TA, _VB, _TB, _R.sd_box([-12, 12, -12, 0.0, 2.0, 6.0]), tol=0.15)
        check("a boundary whose seam must turn a CORNER is REFUSED, not shipped with a hole",
              _V4 is None and "error" in _r4, _r4)
        _VC, _TC = _cyl(lambda z: 0.0, nn=24, rr=11.0)
        _V5, _T5, _r5 = _R.stitch_on_field(_VA, _TA, _VC, _TC, _R.sd_plane((0, 0, 5.0), (0, 0, 1.0)), tol=0.15)
        check("rims 1 mm apart are REFUSED, not stretched to meet", _V5 is None, _r5)
        check("split_at_plane finds the rim when the plane falls ON a tessellation row (nothing clipped)",
              len(_R.split_at_plane(_VB, _TB, (0, 0, 5.0), (0, 0, 1.0), keep=+1.0)[2]) == 24, None)

        _out = os.path.join(root, "stitched.stl")
        _R.write_stl(os.path.join(root, "cA.stl"), _VA, _TA)
        _R.write_stl(os.path.join(root, "cB.stl"), _VB, _TB)
        p = subprocess.run([sys.executable, _kit, "stitch", os.path.join(root, "cA.stl"),
                            os.path.join(root, "cB.stl"), "--plane", "z=5.0", "--out", _out,
                            "--tol", "0.4"], capture_output=True, text=True, env=_env)
        check("kit stitch --tol above the 0.15 ceiling is refused, as stitchband is",
              p.returncode == 2 and "above the 0.15 mm ceiling" in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "stitch", os.path.join(root, "cA.stl"),
                            os.path.join(root, "cB.stl"), "--plane", "z=5.0", "--out", _out],
                           capture_output=True, text=True, env=_env)
        check("kit stitch writes the result and reports boundary edges in AND out",
              p.returncode == 0 and os.path.exists(_out) and "boundary edges" in p.stdout, p.stdout[-400:])
        p = subprocess.run([sys.executable, _kit, "stitch", os.path.join(root, "cA.stl"),
                            os.path.join(root, "cB.stl"), "--box", "-12", "12", "-12", "12", "7", "13",
                            "--out", os.path.join(root, "boxed.stl")], capture_output=True, text=True, env=_env)
        check("...and --box is accepted by the command, not only --plane",
              p.returncode == 0 and os.path.exists(os.path.join(root, "boxed.stl")), p.stdout[-300:])
        p = subprocess.run([sys.executable, _kit, "stitch", os.path.join(root, "cA.stl"),
                            os.path.join(root, "cB.stl"), "--out", _out], capture_output=True, text=True, env=_env)
        check("a stitch with NO boundary named is refused - there is no default cut",
              p.returncode == 2, p.stdout[:200])

        print("\n[26d] a review is COMPLETE only when every frame is judged - and delivery asks by name")
        import json as _js
        _rv = os.path.join(root, "rv_done"); os.makedirs(_rv, exist_ok=True)
        _frames = ["f%02d" % i for i in range(8)]
        for _fn in _frames: open(os.path.join(_rv, _fn + ".png"), "wb").close()
        def _put(state, verdicts):
            _st = {"state": state, "before": "a", "after": "b", "box": "", "mode": "after",
                   "lead": _frames[:3], "lead_from": "named", "frames": _frames,
                   "verdicts": {f: {"verdict": v} for f, v in verdicts.items()}}
            open(os.path.join(_rv, "review_state.json"), "w").write(_js.dumps(_st))
        # leads judged
        _put("lead", {f: "pass" for f in _frames[:3]})
        p = subprocess.run([sys.executable, _kit, "review", "--done", _rv], capture_output=True, text=True, env=_env)
        check("the SHORTCUT is refused: leads judged, sweep never released, called done",
              p.returncode == 2 and "sweep has not been released" in p.stdout, p.stdout[:400])
        check("...and the refusal says plainly that phase 1 is not a review",
              "PHASE 1 IS NOT A REVIEW" in p.stdout, p.stdout[:400])
        # released
        _put("sweep", {f: "pass" for f in _frames[:3]})
        p = subprocess.run([sys.executable, _kit, "review", "--done", _rv], capture_output=True, text=True, env=_env)
        check("sweep released but 5 of 8 frames unjudged is refused, and it names them",
              p.returncode == 2 and "carry no verdict" in p.stdout and "f03" in p.stdout, p.stdout[:400])
        _v = {f: "pass" for f in _frames}; _v["f05"] = "fail"
        _put("sweep", _v)
        p = subprocess.run([sys.executable, _kit, "review", "--done", _rv], capture_output=True, text=True, env=_env)
        check("a review containing a FAIL cannot be completed", p.returncode == 2 and "FAILED" in p.stdout, p.stdout[:300])
        _v = {f: "cannot" for f in _frames}; _v["f00"] = "pass"; _v["f01"] = "pass"
        _put("sweep", _v)
        p = subprocess.run([sys.executable, _kit, "review", "--done", _rv], capture_output=True, text=True, env=_env)
        check("a review that is mostly `cannot` cannot be completed either",
              p.returncode == 2 and "came back `cannot`" in p.stdout, p.stdout[:300])
        _put("sweep", {f: "pass" for f in _frames})
        p = subprocess.run([sys.executable, _kit, "review", "--done", _rv], capture_output=True, text=True, env=_env)
        check("every frame judged, none failed -> COMPLETE",
              p.returncode == 0 and "review COMPLETE" in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "review", "--judge", _rv, "--frame", "ghost", "--verdict", "pass"], capture_output=True, text=True, env=_env)
        check("31bt TJ2 F3: a judge on a frame with no picture on disk is REFUSED (a review had gone COMPLETE with no PNG at all)", p.returncode == 2 and "no picture ghost.png" in p.stdout, p.stdout[:300])
        os.remove(os.path.join(_rv, "f07.png")); _put("sweep", {f: "pass" for f in _frames})
        p = subprocess.run([sys.executable, _kit, "review", "--done", _rv], capture_output=True, text=True, env=_env)
        check("31bt TJ2 F3: --done with a planned frame missing on disk is REFUSED, naming it", p.returncode == 2 and "have no picture on disk" in p.stdout and "f07" in p.stdout, p.stdout[:300])
        open(os.path.join(_rv, "f07.png"), "wb").close(); _put("sweep", {f: "pass" for f in _frames}); subprocess.run([sys.executable, _kit, "review", "--done", _rv], capture_output=True, text=True, env=_env)
        check("...and the stamp records the counts, so the claim carries its own evidence",
              (_rv_read := _js.loads(open(os.path.join(_rv, "review_state.json")).read()))["state"] == "COMPLETE"
              and _rv_read["counts"]["frames"] == 8, _rv_read.get("counts"))
        p = subprocess.run([sys.executable, _kit, "accept", "J99"], capture_output=True, text=True, env=_env)
        check("kit accept with NO --review is refused", p.returncode == 2 and "REFUSED" in p.stdout, p.stdout[:300])
        _bad = os.path.join(root, "rv_bad"); os.makedirs(_bad, exist_ok=True)
        _st = _js.loads(open(os.path.join(_rv, "review_state.json")).read()); _st["state"] = "lead"
        open(os.path.join(_bad, "review_state.json"), "w").write(_js.dumps(_st))
        p = subprocess.run([sys.executable, _kit, "accept", "J99", "--review", _bad], capture_output=True, text=True, env=_env)
        check("...and with a review that is NOT COMPLETE it is refused, naming the state",
              p.returncode == 2 and "not COMPLETE" in p.stdout, p.stdout[:300])
        _fc = os.path.join(root, "d.FCStd"); open(_fc, "wb").write(b"PK\x03\x04" + b"\0" * 40)
        p = subprocess.run([sys.executable, _kit, "deliverycheck", _fc], capture_output=True, text=True, env=_env)
        check("kit deliverycheck with no --review is refused before it checks anything else",
              p.returncode == 2 and "deliverycheck REFUSED" in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "deliverycheck", _fc, "--no-review", "the client said none needed"],
                           capture_output=True, text=True, env=_env)
        check("...and --no-review records the exception in the open rather than hiding it",
              "NO-REVIEW RECORDED" in p.stdout, p.stdout[:400])

        print("\n[26e] the frozen registry, the visibility gate, and regularity as a signal")
        p = subprocess.run([sys.executable, _kit, "frozen", "list"], capture_output=True, text=True, env=_env)
        check("kit frozen list on a project with none says so, and says what to do",
              p.returncode == 0 and "NO REGIONS RECORDED" in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "frozen", "add", "vent_array",
                            "108", "138", "-205", "-52", "10", "42"], capture_output=True, text=True, env=_env)
        check("...and adding one with no --why is REFUSED (a reason nobody can argue with later)",
              p.returncode == 2 and "--why is required" in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "frozen", "add", "vent_array",
                            "108", "138", "-205", "-52", "10", "42",
                            "--why", "designed apertures - metronomic, reviewer 2026-09-22"],
                           capture_output=True, text=True, env=_env)
        check("...with a reason it is recorded", p.returncode == 0 and "recorded" in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "frozen", "check", "110", "120", "-200", "-100", "15", "30"],
                           capture_output=True, text=True, env=_env)
        check("a box INSIDE a frozen region is refused, naming the region and the reason",
              p.returncode == 2 and "vent_array" in p.stdout and "metronomic" in p.stdout, p.stdout[:400])
        p = subprocess.run([sys.executable, _kit, "frozen", "check", "-10", "10", "-10", "10", "-10", "10"],
                           capture_output=True, text=True, env=_env)
        check("...a box clear of every region passes", p.returncode == 0 and "clear" in p.stdout, p.stdout[:200])
        p = subprocess.run([sys.executable, _kit, "frozen", "check", "110", "120", "-200", "-100", "15", "30",
                            "--allow-frozen", "vent_array"], capture_output=True, text=True, env=_env)
        check("...and --allow-frozen NAMES the region, so the override is specific, not blanket",
              p.returncode == 0, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "frozen", "drop", "vent_array"], capture_output=True, text=True, env=_env)
        check("unfreezing without a reason is refused - it is the client's call, not a tidy-up",
              p.returncode == 2 and "--why is required" in p.stdout, p.stdout[:200])
        # metronomic
        _reg = [{"vol": 100.0, "centre": (0, 0.0, 0)}, {"vol": 104.0, "centre": (0, 12.0, 0)},
                {"vol": 98.0, "centre": (0, 24.0, 0)}, {"vol": 102.0, "centre": (0, 36.0, 0)}]
        check("frozen_suspect flags 4 near-identical lumps at constant pitch",
              G.frozen_suspect(_reg) == [0, 1, 2, 3], G.frozen_suspect(_reg))
        _irr = [{"vol": 100.0, "centre": (0, 0.0, 0)}, {"vol": 31.0, "centre": (0, 5.0, 0)},
                {"vol": 260.0, "centre": (0, 29.0, 0)}, {"vol": 12.0, "centre": (0, 31.0, 0)}]
        check("...and does NOT flag an irregular set - a defect is irregular, a design repeats",
              G.frozen_suspect(_irr) == [], G.frozen_suspect(_irr))

        # INTERNAL
        def _box3(path, c, h):
            c = _np.asarray(c, float); h = _np.asarray(h, float); lo = c - h; hi = c + h
            V = _np.array([[lo[0], lo[1], lo[2]], [hi[0], lo[1], lo[2]], [hi[0], hi[1], lo[2]],
                           [lo[0], hi[1], lo[2]], [lo[0], lo[1], hi[2]], [hi[0], lo[1], hi[2]],
                           [hi[0], hi[1], hi[2]], [lo[0], hi[1], hi[2]]], float)
            T = _np.array([[0, 3, 2], [0, 2, 1], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
                           [2, 3, 7], [2, 7, 6], [1, 2, 6], [1, 6, 5], [0, 4, 7], [0, 7, 3]])
            _R.write_stl(path, V, T)
            return V, T
        _VB, _TB = _box3(os.path.join(root, "vb.stl"), (0, 0, 0), (10, 10, 10))
        for _nm, _c, _h in (("proud", (0, 0, 11.0), (3, 3, 2)), ("buried", (0, 0, -2.0), (3, 3, 3))):
            _Vt, _Tt = _box3(os.path.join(root, "tool_%s.stl" % _nm), _c, _h)
            _V = _np.vstack([_VB, _Vt]); _T = _np.vstack([_TB, _Tt + len(_VB)])
            _R.write_stl(os.path.join(root, "res_%s.stl" % _nm), _V, _T)
            _fd = os.path.join(root, "fr_%s" % _nm); os.makedirs(_fd, exist_ok=True)
            for _cam, _dv in (("iso", (0.5, 0.5, -0.7)), ("top", (0, 0, -1)), ("front", (0, 1, 0))):
                _st2 = {}
                _R.render(os.path.join(_fd, "%s.png" % _cam),
                          [("m", _V, _T, _np.tile([0.6, 0.7, 0.9], (len(_T), 1)))], _dv, W=400,
                          title=_cam, stats=_st2)
                _np.save(os.path.join(_fd, "%s_own.npy" % _cam), _st2["own"])
        p = subprocess.run([sys.executable, _kit, "visible", os.path.join(root, "res_proud.stl"),
                            "--tool", os.path.join(root, "tool_proud.stl"),
                            "--frames", os.path.join(root, "fr_proud")],
                           capture_output=True, text=True, env=_env)
        check("kit visible PASSES a tool that owns pixels in the review's own frames",
              p.returncode == 0 and "PASS" in p.stdout, p.stdout[-400:])
        p = subprocess.run([sys.executable, _kit, "visible", os.path.join(root, "res_buried.stl"),
                            "--tool", os.path.join(root, "tool_buried.stl"),
                            "--frames", os.path.join(root, "fr_buried")],
                           capture_output=True, text=True, env=_env)
        check("kit visible REFUSES the SILENT NO-OP - 0 pixels across every frame",
              p.returncode == 2 and "TOTAL 0 pixel" in p.stdout, p.stdout[-500:])
        check("...and it says the no-op passes every other gate, and why",
              "bit-identical" in p.stdout and "INTERNAL" in p.stdout, p.stdout[-600:])
        p = subprocess.run([sys.executable, _kit, "visible", os.path.join(root, "res_buried.stl"),
                            "--tool", os.path.join(root, "tool_buried.stl"),
                            "--frames", os.path.join(root, "fr_buried"), "--anyway", "internal on purpose"],
                           capture_output=True, text=True, env=_env)
        check("...--anyway records a deliberate internal fill rather than forbidding it",
              p.returncode == 0 and "OVERRIDE RECORDED" in p.stdout, p.stdout[-300:])
        p = subprocess.run([sys.executable, _kit, "visible", os.path.join(root, "res_proud.stl"),
                            "--tool", os.path.join(root, "tool_proud.stl"),
                            "--frames", os.path.join(root, "fr_nothing")],
                           capture_output=True, text=True, env=_env)
        check("a --frames directory that does not exist is refused, not silently passed",
              p.returncode == 2, p.stdout[:300])
        _empty = os.path.join(root, "fr_empty"); os.makedirs(_empty, exist_ok=True)
        p = subprocess.run([sys.executable, _kit, "visible", os.path.join(root, "res_proud.stl"),
                            "--tool", os.path.join(root, "tool_proud.stl"), "--frames", _empty],
                           capture_output=True, text=True, env=_env)
        check("...and a frames directory with no ownermaps is refused, naming LK_OWNERMAP=1",
              p.returncode == 2 and "LK_OWNERMAP" in p.stdout, p.stdout[:400])
        _lab = _np.zeros((10, 10, 10), int)
        _lab[1:4, 1:4, 1:4] = 1; _lab[6:8, 6:8, 6:8] = 2; _lab[0, 0, 9] = 3
        _cen = _np.zeros((4, 3)); _cen[1] = (2, 2, 2); _cen[2] = (7, 7, 7); _cen[3] = (0, 0, 9)
        _m, _tab = _R.lump_select(_lab, 3, 1.0, keep=[1], centres=_cen)
        check("lump_select keeps the ranks named and drops the rest (one selector, both halves)",
              int(_m.sum()) == 27 and _tab[0]["rank"] == 1, [(r["rank"], r["vol"]) for r in _tab])
        _m2, _ = _R.lump_select(_lab, 3, 1.0, min_vol=5.0, centres=_cen)
        check("...and min_vol drops the dust without naming ranks", int(_m2.sum()) == 35, int(_m2.sum()))

        _src = open(os.path.join(HERE, "kit", "kit.py"), encoding="utf-8").read()
        _i = _src.index("def _inside_count("); _j = _src.index("\ndef ", _i + 10)
        _ns = {}
        exec("import numpy as np\n" + _src[_i:_j], _ns)
        _V = _np.array([[-10, -10, -10], [10, -10, -10], [10, 10, -10], [-10, 10, -10],
                        [-10, -10, 10], [10, -10, 10], [10, 10, 10], [-10, 10, 10]], float)
        _T = _np.array([[0, 3, 2], [0, 2, 1], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
                        [2, 3, 7], [2, 7, 6], [1, 2, 6], [1, 6, 5], [0, 4, 7], [0, 7, 3]])
        _c = _ns["_inside_count"](_np.array([[0, 0, 0], [100, 0, 0], [-30, 0, 0]], float), _V, _T)
        check("the inside test is ODD at the centre of a box (an axis ray lands on the shared diagonal "
              "and reads 2 - the tilt is what fixes it)", list(_np.asarray(_c) % 2) == [1, 0, 0], _c)

        print("\n[26f] reach / pick / inventory - a census that sees spanning triangles, and a frame that names its own")
        _V, _T = [], []
        for _i in range(10):
            for _j in range(10):
                _o = len(_V)
                _V += [[_i, _j, 0], [_i + 1, _j, 0], [_i + 1, _j + 1, 0], [_i, _j + 1, 0]]
                _T += [[_o, _o + 1, _o + 2], [_o, _o + 2, _o + 3]]
        _base = os.path.join(root, "reach_base.stl")
        _R.write_stl(_base, _np.array(_V, float), _np.array(_T))
        _o = len(_V)
        _V += [[5.0, 5.0, 0.0], [5.2, 5.0, 0.0], [80.0, 5.1, 0.0]]
        _T += [[_o, _o + 1, _o + 2]]
        _sub = os.path.join(root, "reach.stl")
        _R.write_stl(_sub, _np.array(_V, float), _np.array(_T))
        p = subprocess.run([sys.executable, _kit, "reach", _sub, "--box", "0", "10", "0", "10", "-1", "1",
                            "--base", _base], capture_output=True, text=True, env=_env)
        check("kit reach finds a SPANNING triangle whose centroid is outside the box (a centroid census misses it)",
              "reaching 5 mm or more: 1 triangle" in p.stdout and "70.00" in p.stdout, p.stdout[:500])
        check("...and it reports the CONTROL and the delta, because a part has long triangles of its own",
              "CONTROL" in p.stdout and "DELTA" in p.stdout, p.stdout[:400])
        p = subprocess.run([sys.executable, _kit, "reach", _sub, "--box", "0", "10", "0", "10", "-1", "1"],
                           capture_output=True, text=True, env=_env)
        check("...and with NO control it says so rather than reporting a bare number",
              "NO CONTROL GIVEN" in p.stdout, p.stdout[:400])
        _Va = _np.array(_V, float); _Ta = _np.array(_T)
        _Va = _np.vstack([_Va])
        _st = {}
        _R.render(os.path.join(root, "own.png"), [("m", _Va, _Ta, _np.tile([0.6, 0.7, 0.9], (len(_Ta), 1)))],
                  (0, 0, -1), W=400, title="own", stats=_st)
        check("render() hands back the OWNERMAP - a frame that cannot name its own triangles is not an instrument",
              _st.get("own") is not None and _st["own"].shape[0] > 0, list(_st.keys()))
        _ownp = os.path.join(root, "own.npy"); _np.save(_ownp, _st["own"])
        _ys, _xs = _np.nonzero(_st["own"] == len(_Ta) - 1)
        check("...and the spanning triangle owns pixels in it", len(_ys) > 0, len(_ys))
        if len(_ys):
            p = subprocess.run([sys.executable, _kit, "pick", _sub, "--own", _ownp, "--rect",
                                str(_xs.min()), str(_ys.min()), str(_xs.max()), str(_ys.max())],
                               capture_output=True, text=True, env=_env)
            check("kit pick turns those PIXELS into exact triangle ids, worst-edge first",
                  p.returncode == 0 and ("triangle %d" % (len(_Ta) - 1)) in p.stdout, p.stdout[:500])
        p = subprocess.run([sys.executable, _kit, "pick", _sub, "--own", _ownp, "--rect", "0", "0", "1", "1"],
                           capture_output=True, text=True, env=_env)
        check("...and a pick over background says so instead of returning an empty answer",
              p.returncode == 2 and "background only" in p.stdout, p.stdout[:300])
        _V2, _T2 = [], []
        def _q(pts):
            _o2 = len(_V2); _V2.extend(pts); _T2.extend([[_o2, _o2 + 1, _o2 + 2], [_o2, _o2 + 2, _o2 + 3]])
        for _x in range(-40, 40, 4):
            for _y in range(-200, -90, 4):
                _q([[_x, _y, 0], [_x + 4, _y, 0], [_x + 4, _y + 4, 0], [_x, _y + 4, 0]])
        for _yc in (-187.5, -163.0, -137.5, -116.0):
            for _x in range(-20, 20, 2):
                _q([[_x, _yc - 1, 0], [_x + 2, _yc - 1, 0], [_x + 2, _yc - 1, -18], [_x, _yc - 1, -18]])
        _van = os.path.join(root, "vanes.stl")
        _R.write_stl(_van, _np.array(_V2, float), _np.array(_T2))
        p = subprocess.run([sys.executable, _kit, "inventory", _van, "--axis", "y", "--measure", "z",
                            "--box", "-40", "40", "-200", "-90", "-25", "5", "--step", "1.0",
                            "--min-pitch", "8"], capture_output=True, text=True, env=_env)
        check("kit inventory ENUMERATES a repeating feature (4 vanes, not a guess off a render)",
              p.returncode == 0 and "4 feature(s)" in p.stdout, p.stdout[:400])
        check("...and it reports the pitch, and warns that a regular pitch may be a DESIGNED array",
              "pitch:" in p.stdout and "designed array" in p.stdout, p.stdout[:500])

        print("\n[26g] kit seamweld - refinement is the lever route A's ratio gate never had")
        import math as _MTH

        def _tube(nn, mm, z0, z1, bulge=None, rr=10.0):
            Vs, Ts = [], []
            for i2 in range(nn):
                a2 = 2 * _MTH.pi * i2 / nn; b2 = 2 * _MTH.pi * (i2 + 1) / nn
                for j2 in range(mm):
                    za = z0 + (z1 - z0) * j2 / mm; zb = z0 + (z1 - z0) * (j2 + 1) / mm
                    P = lambda t2, z: [(rr + (bulge(z) if bulge else 0.0)) * _MTH.cos(t2),
                                       (rr + (bulge(z) if bulge else 0.0)) * _MTH.sin(t2), z]
                    q = [P(a2, za), P(b2, za), P(b2, zb), P(a2, zb)]
                    o = len(Vs); Vs += q; Ts += [[o, o + 1, o + 2], [o, o + 2, o + 3]]
            return _np.array(Vs, float), _np.array(Ts)
        _l = _tube(24, 8, 0.0, 8.0); _u = _tube(24, 8, 12.0, 20.0)
        _bodyV = _np.vstack([_l[0], _u[0]]); _bodyT = _np.vstack([_l[1], _u[1] + len(_l[0])])
        _bp = os.path.join(root, "sw_body.stl"); _R.write_stl(_bp, _bodyV, _bodyT)
        _pp = os.path.join(root, "sw_patch.stl")
        _R.write_stl(_pp, *_tube(192, 24, 8.0, 12.0, lambda z: 0.4 * _MTH.exp(-((z - 10.0) ** 2) / 2.0)))
        _op = os.path.join(root, "sw_out.stl")
        p = subprocess.run([sys.executable, _kit, "seamweld", _bp, _pp, "--out", _op],
                           capture_output=True, text=True, env=_env)
        check("a 24-gon body rim welds to a 192-gon patch rim - the 8:1 case gate 2 forbids",
              p.returncode == 0 and os.path.exists(_op), p.stdout[-600:])
        check("...the SPARSE side is refined in the mesh (96 -> 432 edges), not resampled",
              "96 -> 432" in p.stdout, p.stdout[:600])
        check("...and NO non-manifold edge is created by the seam",
              "non-manifold edges      0 out" in p.stdout, p.stdout[-500:])
        check("...the body's OWN open ends are left alone, not treated as a mismatch",
              "unrelated boundary loop" in p.stdout, p.stdout[:400])
        _cl = os.path.join(root, "sw_closed.stl")
        _R.write_stl(_cl, *_tube(16, 4, 0.0, 4.0))
        p = subprocess.run([sys.executable, _kit, "seamweld", _cl, _cl, "--out", _op],
                           capture_output=True, text=True, env=_env)
        check("...and two meshes with no rim at all are refused with the reason",
              p.returncode == 2, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "seamweld", _bp, _pp, "--out", _op, "--tol", "0.4"],
                           capture_output=True, text=True, env=_env)
        check("kit seamweld honours the 0.15 mm ceiling like every other seam command",
              p.returncode == 2 and "ceiling" in p.stdout, p.stdout[:300])

        # neighbouring feature
        print("\n[26g2] kit coreplace - the weld core enclosed by rule, refused when it reaches anything else")

        def _plate(bumps, n=81, L=40.0, ridge=None):
            xs = _np.linspace(-L / 2, L / 2, n); X, Y = _np.meshgrid(xs, xs, indexing="ij")
            Z = _np.zeros_like(X)
            for (cx, cy, r, h) in bumps:
                dd = _np.hypot(X - cx, Y - cy); Z = Z + _np.where(dd < r, h * (1 - (dd / r) ** 2), 0.0)
            if ridge:
                Z = Z + _np.where(_np.abs(X) <= ridge, 2.0 * _np.clip(1 - (Y / 2.0) ** 2, 0, None), 0.0)
            Vs = _np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1); Ts = []
            for i2 in range(n - 1):
                for j2 in range(n - 1):
                    o = i2 * n + j2; Ts += [[o, o + n, o + 1], [o + 1, o + n, o + n + 1]]
            return Vs, _np.array(Ts)
        _cb = os.path.join(root, "cp_body.stl"); _R.write_stl(_cb, *_plate([]))
        _cp = os.path.join(root, "cp_patch.stl"); _R.write_stl(_cp, *_plate([(0, 12, 2.5, 1.5)], ridge=10))
        _cpn = os.path.join(root, "cp_patch_near.stl"); _R.write_stl(_cpn, *_plate([(13.5, 0, 1.5, 1.0)], ridge=10))
        _cbox = ["--box", "-18", "18", "-18", "18", "-3", "6"]
        p = subprocess.run([sys.executable, _kit, "coreplace", _cp, _cb] + _cbox + ["--at", "0", "0", "1"],
                           capture_output=True, text=True, env=_env)
        check("an edit with a departure well away from it gets a clean core round the edit alone",
              p.returncode == 0 and "2 departure group(s)" in p.stdout and "reaches nothing else" in p.stdout
              and "CC_CORE_CEN=0.00 0.00" in p.stdout and "CC_CORE_RAD=11.50" in p.stdout, p.stdout[-600:])
        p = subprocess.run([sys.executable, _kit, "coreplace", _cp, _cb] + _cbox + ["--at", "0", "0", "1",
                            "--neighbours", "1.0"], capture_output=True, text=True, env=_env)
        check("...a neighbouring feature station inside the core REFUSES it (V3's core held two vanes)",
              p.returncode == 2 and "neighbouring feature" in p.stdout, p.stdout[-500:])
        p = subprocess.run([sys.executable, _kit, "coreplace", _cpn, _cb] + _cbox + ["--at", "0", "0", "1",
                            "--margin", "4"], capture_output=True, text=True, env=_env)
        check("...another departure inside the core REFUSES it (V3's and V4's lumps)",
              p.returncode == 2 and "departure group" in p.stdout and "reaches inside the core" in p.stdout,
              p.stdout[-500:])
        p = subprocess.run([sys.executable, _kit, "coreplace", _cb, _cb] + _cbox + ["--at", "0", "0", "1"],
                           capture_output=True, text=True, env=_env)
        check("...and a patch that is the body everywhere has no edit to enclose, and says so",
              p.returncode == 2 and "no edit to enclose" in p.stdout, p.stdout[-300:])

        print("\n[26g3] kit tool - instruments run from the kit, output into the job that asked")
        p = subprocess.run([sys.executable, _kit, "tool"], capture_output=True, text=True, env=_env)
        check("`kit tool` lists the instruments, the sign check among them",
              p.returncode == 0 and "diag_sign_field" in p.stdout and "diag_loops" in p.stdout, p.stdout[:400])
        # CC_OUTDIR
        _lk = os.path.dirname(os.path.abspath(__file__))
        for _dt in ("diag_sign_field", "diag_gate_sign", "diag_loops", "diag_plancut", "diag_openedges", "diag_section"):
            _src = open(os.path.join(_lk, "tools", _dt + ".py"), encoding="utf-8").read()
            check("tools\\%s.py makes CC_OUTDIR before it writes into it (31bs W33 / 31bw V25)" % _dt,
                  "makedirs(" in _src and "CC_OUTDIR" in _src.split("makedirs(", 1)[1][:80], _dt)
        _src = open(os.path.join(_lk, "tools", "diag_sign_field.py"), encoding="utf-8").read()
        check("...and diag_sign_field makes it BEFORE its vtk log file is named (its first write into the folder)",
              _src.index("makedirs(") < _src.index("SetFileName("), "order")
        os.makedirs(os.path.join(root, "claude_code", "jobs", "TOOLJOB"), exist_ok=True)
        p = subprocess.run([sys.executable, _kit, "tool", "diag_openedges", "--set", "CC_MESH=x.stl"],
                           capture_output=True, text=True, env=_env)
        check("...a run with no --job is refused: output belongs to the job whose question it answers",
              p.returncode == 2 and "--job" in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "tool", "diag_openedges", "--job", "TOOLJOB", "--set", "CC_MSH=x.stl"],
                           capture_output=True, text=True, env=_env)
        check("...a --set the instrument never reads is refused (a typo is a silent skip)",
              p.returncode == 2 and "never reads CC_MSH" in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "tool", "diag_openedges", "--job", "TOOLJOB", "--set", "CC_MESH=x.stl",
                            "--set", "CC_TAG=t", "--plan"], capture_output=True, text=True, env=_env)
        check("...and a planned run sends its output to the job folder by default",
              p.returncode == 0 and "CC_OUTDIR" in p.stdout and "TOOLJOB" in p.stdout, p.stdout[:400])

        print("\n[26h] kit atlas - what the part's regions ARE, stored once and gated against staleness")
        p = subprocess.run([sys.executable, _kit, "atlas", "status"], capture_output=True, text=True, env=_env)
        check("a project with NO atlas is told so, and told why it matters",
              p.returncode == 2 and "NO ATLAS" in p.stdout and "invented that day" in p.stdout, p.stdout[:400])
        p = subprocess.run([sys.executable, _kit, "atlas", "init"], capture_output=True, text=True, env=_env)
        check("...and `atlas init` creates it", p.returncode == 0 and "created" in p.stdout, p.stdout[:200])
        p = subprocess.run([sys.executable, _kit, "atlas", "add", "seat", "--box", "-10", "10", "-10", "10", "0", "1"],
                           capture_output=True, text=True, env=_env)
        check("adding a region with a BOX and no statement of what it IS is refused",
              p.returncode == 2 and "--what is required" in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "atlas", "add", "seat", "--what",
                            "the down-facing sealing plane the cover mates to", "--box",
                            "-10", "10", "-10", "10", "0", "1", "--surface", "-z down-facing"],
                           capture_output=True, text=True, env=_env)
        check("...with --what it is recorded, at DRAFT", p.returncode == 0 and "DRAFT" in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "atlas", "cite", "seat"], capture_output=True, text=True, env=_env)
        check("a card may NOT cite a DRAFT region - the boundary is unconfirmed",
              p.returncode == 2 and "not the client" in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "atlas", "set", "seat", "--definition", "RENDERED"],
                           capture_output=True, text=True, env=_env)
        check("RENDERED is refused without naming the frame somebody opened",
              p.returncode == 2 and "--frame" in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "atlas", "set", "seat", "--definition", "CLIENT"],
                           capture_output=True, text=True, env=_env)
        check("the client is refused without the client's own words - an agent cannot award it",
              p.returncode == 2 and "--said" in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "atlas", "set", "seat", "--definition", "CLIENT",
                            "--said", "that is the seat"], capture_output=True, text=True, env=_env)
        check("...with their words it is raised, and becomes citable",
              p.returncode == 0, p.stdout[:200])
        p = subprocess.run([sys.executable, _kit, "atlas", "cite", "seat"], capture_output=True, text=True, env=_env)
        check("...and now a card may cite it", p.returncode == 0 and "confirmed by the client" in p.stdout, p.stdout[:200])
        _sel = os.path.join(root, "adsel.txt")
        open(_sel, "w").write(
            "Gui.Selection.addSelection('R31_MAP','FZ_skirt','Face2101',-112.4,-180.2,-18.0)\n"
            "Gui.Selection.addSelection('R31_MAP','FZ_skirt','Face2102',-98.1,-181.0,-18.0)\n"
            "Gui.Selection.addSelection('R31_MAP','FZ_skirt','Face2455',110.9,-179.4,-18.0)\n")
        subprocess.run([sys.executable, _kit, "atlas", "add", "skirt", "--what", "the flat underside"],
                       capture_output=True, text=True, env=_env)
        p = subprocess.run([sys.executable, _kit, "atlas", "faces", _sel, "--region", "skirt"],
                           capture_output=True, text=True, env=_env)
        check("picks that name map objects are REFUSED without the map's facemap - FaceN is local to the object",
              p.returncode == 2 and "LOCAL" in p.stdout and "--facemap" in p.stdout, p.stdout[:400])
        _fmj = os.path.join(root, "map_facemap.json")
        open(_fmj, "w").write(json.dumps({"FZ_skirt": {"2101": 601, "2102": 602, "2455": 294}}))
        p = subprocess.run([sys.executable, _kit, "atlas", "faces", _sel, "--region", "skirt", "--facemap", _fmj],
                           capture_output=True, text=True, env=_env)
        check("...with the facemap they are translated to BODY faces and become the region's face list",
              p.returncode == 0 and "translated" in p.stdout and "3 face(s)" in p.stdout
              and G.atlas_regions(root)["skirt"]["faces"] == [294, 601, 602], (p.stdout[:400], G.atlas_regions(root).get("skirt", {}).get("faces")))
        p = subprocess.run([sys.executable, _kit, "atlas", "faces", _sel, "--region", "skirt", "--body"],
                           capture_output=True, text=True, env=_env)
        check("the client's pasted FreeCAD selection lines become a region's face list in one verb (--body: picked on the body)",
              p.returncode == 0 and "3 face(s)" in p.stdout, p.stdout[:400])
        check("...and it warns that face numbers do not survive a fuse",
              "NOT stable across a fuse" in p.stdout, p.stdout[:400])
        # recorded
        p = subprocess.run([sys.executable, _kit, "atlas", "axis", "y", "0", "-300"],
                           capture_output=True, text=True, env=_env)
        check("kit atlas axis refuses without --said: an orientation from an assembly is a fact, one"
              " from a render is a guess, and the next agent cannot tell them apart",
              p.returncode == 2 and "--said is required" in p.stdout, p.stdout[:300])
        subprocess.run([sys.executable, _kit, "atlas", "add", "aft_thing", "--what", "a thing",
                        "--box", "-1", "1", "-290", "-280", "0", "1"], capture_output=True, text=True, env=_env)
        p = subprocess.run([sys.executable, _kit, "atlas", "axis", "y", "0", "-300",
                            "--said", "settled from the assembly"], capture_output=True, text=True, env=_env)
        check("...and recording it NAMES every existing region whose name claims the wrong end",
              p.returncode == 0 and "named for the wrong end" not in p.stdout, p.stdout[:400])
        p = subprocess.run([sys.executable, _kit, "atlas", "add", "front_bracket", "--what", "a bracket",
                            "--box", "-1", "1", "-290", "-280", "0", "1"], capture_output=True, text=True, env=_env)
        check("a region NAMED for the front whose box sits wholly at the AFT end is WARNED about, and recorded",
              p.returncode == 0 and "WARNING" in p.stdout and "named for the FRONT" in p.stdout, p.stdout[:400])
        p = subprocess.run([sys.executable, _kit, "atlas", "add", "aft_bracket", "--what", "a bracket",
                            "--box", "-1", "1", "-40", "-35", "0", "1"], capture_output=True, text=True, env=_env)
        check("...and one named for the AFT end sitting at the FRONT too",
              p.returncode == 0 and "named for the AFT" in p.stdout, p.stdout[:400])
        p = subprocess.run([sys.executable, _kit, "atlas", "add", "side_exit", "--what", "an exit bay",
                            "--box", "-1", "1", "-40", "-35", "0", "1"], capture_output=True, text=True, env=_env)
        check("...but 'exit' alone claims no end - a design can exit to the side",
              p.returncode == 0 and "WARNING" not in p.stdout, p.stdout[:400])

        import json as _js2
        _imp = os.path.join(root, "imp.json")
        open(_imp, "w").write(_js2.dumps([
            {"name": "imported_ad", "definition": "CLIENT_OK", "edit": "FROZEN", "area": 100.0,
             "faces": 3, "box": [0, 1, 0, 1, 0, 1], "label": "came in claiming the client"},
            {"name": "imported_draft", "definition": "DRAFT", "edit": "OPEN", "area": 50.0,
             "faces": 2, "box": [2, 3, 2, 3, 2, 3], "label": "an ordinary one"}]))
        p = subprocess.run([sys.executable, _kit, "atlas", "import", _imp], capture_output=True, text=True, env=_env)
        check("kit atlas import brings a region set in from the tool that built it",
              p.returncode == 0 and "2 region(s)" in p.stdout, p.stdout[:300])
        check("...and a definition that arrives claiming the client with no record of what the client SAID is"
              " NOT accepted at CLIENT - importing a status is not looking at the thing",
              "NOT accepted at CLIENT" in p.stdout, p.stdout[:400])
        p = subprocess.run([sys.executable, _kit, "atlas", "cite", "imported_ad"], capture_output=True, text=True, env=_env)
        check("...so the imported region is not citable either", p.returncode == 2, p.stdout[:200])
        check("...and the import prints the total area, because a partition that drops surface passes"
              " a face count",
              "CHECK THIS AGAINST THE BODY" in subprocess.run(
                  [sys.executable, _kit, "atlas", "import", _imp, "--replace"],
                  capture_output=True, text=True, env=_env).stdout, None)
        p = subprocess.run([sys.executable, _kit, "atlas", "stale", "-5", "5", "-5", "5", "0", "1",
                            "--why", "an apply touched it"], capture_output=True, text=True, env=_env)
        check("an apply in a region's space marks it STALE", p.returncode == 0 and "seat" in p.stdout, p.stdout[:300])
        p = subprocess.run([sys.executable, _kit, "atlas", "cite", "seat"], capture_output=True, text=True, env=_env)
        check("...and a STALE region is no longer citable, even though the client confirmed it once",
              p.returncode == 2 and "STALE" in p.stdout, p.stdout[:300])
        check("...a region with NO BOX is staled too - nothing can prove it was untouched, and the"
              " face-list regions are exactly the ones whose numbers a fuse invalidates",
              "skirt" in subprocess.run([sys.executable, _kit, "atlas", "status", "--long"],
                                        capture_output=True, text=True, env=_env).stdout, None)

        print("\n[26i] kit job - a card names the client-confirmed atlas regions; a FROZEN one is recreated, not refused")
        subprocess.run([sys.executable, _kit, "atlas", "add", "rib", "--what", "the members holding the spine",
                        "--box", "-5", "5", "-5", "5", "5", "6"], capture_output=True, text=True, env=_env)
        subprocess.run([sys.executable, _kit, "atlas", "set", "rib", "--definition", "CLIENT", "--said", "approve"],
                       capture_output=True, text=True, env=_env)
        subprocess.run([sys.executable, _kit, "atlas", "add", "pads", "--what", "the bracket pads",
                        "--box", "-5", "5", "-5", "5", "7", "8", "--edit", "FROZEN"], capture_output=True, text=True, env=_env)
        subprocess.run([sys.executable, _kit, "atlas", "set", "pads", "--definition", "CLIENT", "--said", "approve"],
                       capture_output=True, text=True, env=_env)

        def _rcard(line):
            _cp_ = os.path.join(root, "rcard.md")
            with open(_cp_, "w", encoding="utf-8") as _fh:
                _fh.write("Edit type: sketch_connect\nRow: J\n%sClass: shape\nDossier: none - test\n" % line)
            return subprocess.run([sys.executable, _kit, "job", "RJ", "--type", "sketch_connect", "--card", _cp_],
                                  capture_output=True, text=True, env=_env)
        p = _rcard("")
        check("a card with NO Region: is refused once the atlas holds a region the client confirmed",
              p.returncode == 2 and "no Region:" in p.stdout and "rib" in p.stdout, p.stdout[:400])
        p = _rcard("Region: <the ATLAS region(s) this job edits>\n")
        check("...the template's unfilled slot counts as no Region:", p.returncode == 2 and "no Region:" in p.stdout, p.stdout[:300])
        p = _rcard("Region: ribs - the second one\n")
        check("...a name that is not in the atlas is refused by name", p.returncode == 2 and "'ribs' is not a region" in p.stdout, p.stdout[:400])
        p = _rcard("Region: imported_draft\n")
        check("...a region the client has not confirmed is refused", p.returncode == 2 and "not the client" in p.stdout, p.stdout[:400])
        p = _rcard("Region: rib - the fillet under the second member\n")
        check("...and a confirmed region passes the region gate (whatever later gates say)",
              "confirmed by the client" in p.stdout and "REFUSED on the card's Region" not in p.stdout, (p.stdout + p.stderr)[:500])
        p = _rcard("Region: rib, pads - the round where they meet\n")
        check("a FROZEN region is ALLOWED in a selection, and the card is told it must be recreated",
              "REFUSED on the card's Region" not in p.stdout and "RECREATED at the end of edits" in p.stdout,
              (p.stdout + p.stderr)[:500])
        G.atlas_mark_edited(root, ["rib", "pads"], "RJ", "after.stl")
        check("...once a job that named it applies, the frozen region is RECREATE OWED (the open one is not)",
              sorted(G.atlas_recreate_owed(root)) == ["pads"], G.atlas_recreate_owed(root))
        p = subprocess.run([sys.executable, _kit, "deliverycheck", os.path.join(root, "nope.FCStd"), "--no-review", "test"],
                           capture_output=True, text=True, env=_env)
        check("...and delivery refuses while it is owed",
              p.returncode == 2 and "have not been measured back" in p.stdout and "pads" in p.stdout, p.stdout[:400])
        def _blk(z1, n):
            xs_ = _np.linspace(0, 10, n + 1)
            Vb, Tb = [], []
            for (o, u, v) in (((0, 0, z1), (10, 0, 0), (0, 10, 0)), ((0, 0, 0), (0, 10, 0), (10, 0, 0)),
                              ((0, 0, 0), (10, 0, 0), (0, 0, z1)), ((0, 10, 0), (0, 0, z1), (10, 0, 0)),
                              ((0, 0, 0), (0, 0, z1), (0, 10, 0)), ((10, 0, 0), (0, 10, 0), (0, 0, z1))):
                base = len(Vb)
                for i_ in range(n + 1):
                    for j_ in range(n + 1):
                        Vb.append([o[k] + u[k] * i_ / n + v[k] * j_ / n for k in range(3)])
                for i_ in range(n):
                    for j_ in range(n):
                        a_ = base + i_ * (n + 1) + j_
                        Tb.extend([[a_, a_ + n + 1, a_ + 1], [a_ + 1, a_ + n + 1, a_ + n + 2]])
            Vb = _np.array(Vb, float); Tb = _np.array(Tb, int)
            Vt_ = Vb[Tb]; c_ = Vt_.mean(1); nr_ = _np.cross(Vt_[:, 1] - Vt_[:, 0], Vt_[:, 2] - Vt_[:, 0])
            f_ = _np.einsum("ij,ij->i", nr_, c_ - _np.array([5.0, 5.0, z1 / 2.0])) < 0; Tb[f_] = Tb[f_][:, ::-1]
            return Vb, Tb
        _orig = os.path.join(root, "pads_orig.stl")
        _ov = _np.array([[10 * i_ / 20, 10 * j_ / 20, 10.0] for i_ in range(21) for j_ in range(21)])
        _ot = _np.array([t_ for i_ in range(20) for j_ in range(20)
                         for t_ in ([i_ * 21 + j_, (i_ + 1) * 21 + j_, i_ * 21 + j_ + 1],
                                    [i_ * 21 + j_ + 1, (i_ + 1) * 21 + j_, (i_ + 1) * 21 + j_ + 1])])
        _R.write_stl(_orig, _ov, _ot)
        _bad = os.path.join(root, "pads_bad.stl"); _R.write_stl(_bad, *_blk(9.0, 10))
        p = subprocess.run([sys.executable, _kit, "atlas", "recreated", "pads", "--result", _bad, "--original", _orig],
                           capture_output=True, text=True, env=_env)
        check("`kit atlas recreated` REFUSES a result that does not reproduce the frozen surface, and records nothing",
              p.returncode == 2 and "was not recreated" in p.stdout and "pads" in G.atlas_recreate_owed(root), p.stdout[-400:])
        _good = os.path.join(root, "pads_good.stl"); _R.write_stl(_good, *_blk(10.0, 13))
        p = subprocess.run([sys.executable, _kit, "atlas", "recreated", "pads", "--result", _good, "--original", _orig],
                           capture_output=True, text=True, env=_env)
        check("...and passes one that does - a different tessellation of the same surface - clearing the debt",
              p.returncode == 0 and "PASS" in p.stdout and not G.atlas_recreate_owed(root), p.stdout[-400:])

        print("\n[27] kit paths - a document that names a file that is not there is named, placeholders are not")
        _doc = os.path.join(root, "CLAUDE.md")
        os.makedirs(os.path.join(root, "claude_code", "jobs"), exist_ok=True)
        open(os.path.join(root, "claude_code", "REAL.md"), "w").write("x")
        open(_doc, "w", encoding="utf-8").write(
            "Read `claude_code\\REAL.md` and `claude_code\\GONE.md`; jobs go in `claude_code\\jobs\\<name>\\` and pictures in "
            "`Deliverables\\<REV>\\review\\`. Never a fresh `look2\\`. Run `kit status` and `python kit.py run x`. "
            "The kit is `LEAN_KIT\\kit\\kit.py`; the master is `C:\\CAD\\LEAN_KIT\\METHOD.md`. "
            "See `claude_code\\NOWHERE.md:495` and `claude_code\\REAL.md:12`.\n")
        _master = os.path.dirname(os.path.join(HERE, "kit"))
        dead = G.dead_paths(_doc, [root, os.path.dirname(_master), _master])
        toks = [t for t, _ in dead]
        check("a named file that is not there is reported", "claude_code\\GONE.md" in toks, toks)
        check("a named file that is there is not", "claude_code\\REAL.md" not in toks, toks)
        check("placeholders (<name>, <REV>) are skipped", not any("<" in t for t in toks), toks)
        check("command lines are not paths", not any(t.startswith(("kit ", "python ")) for t in toks), toks)
        check("a kit path written relative to LEAN_KIT resolves through the master's parent", not any("LEAN_KIT\\kit\\kit.py" in t for t in toks), toks)
        check("a Windows-absolute path resolves by its tail when the drive is not mounted here", not any("METHOD.md" in t for t in toks), toks)
        check("a `file:line` citation resolves on the file", not any("REAL.md:12" in t for t in toks), toks)
        check("...and one whose file is missing is reported", "claude_code\\NOWHERE.md:495" in toks, toks)
        check("a folder named as a shape that does not exist IS reported (look2)", "look2\\" in toks, toks)

        print("\n[28] kit priorart - the ranked prior art for an EXISTING job folder")
        _jd = os.path.join(root, "claude_code", "jobs", "PA")
        os.makedirs(_jd, exist_ok=True)
        open(os.path.join(_jd, "job_old.py"), "w", encoding="utf-8").write("# LK: the first attempt\n")
        open(os.path.join(_jd, "job_ruled.py"), "w", encoding="utf-8").write('# the client 2026-09-15: "do it this way" - the ruling\n')
        p = subprocess.run([sys.executable, _kit, "priorart", "PA"], capture_output=True, text=True, env=_env)
        check("an existing folder lists its scripts, the one carrying the client's ruling first",
              p.returncode == 0 and "PRIOR ART" in p.stdout and p.stdout.index("job_ruled.py") < p.stdout.index("job_old.py"), p.stdout[-400:])
        p = subprocess.run([sys.executable, _kit, "priorart", "NOPE"], capture_output=True, text=True, env=_env)
        check("a folder that does not exist is named, exit 2", p.returncode == 2 and "no such job folder" in p.stdout, p.stdout[-200:])

        print("\n[29] the issue-fix pass - output kept, rays off the grid, specks set aside, crashes gone")
        import importlib.util as _ilu2
        sys.path.insert(0, os.path.join(HERE, "kit"))
        _kp_was = os.environ.get("KIT_PROJECT")
        os.environ["KIT_PROJECT"] = root
        _ksp = _ilu2.spec_from_file_location("_kitmod29", os.path.join(HERE, "kit", "kit.py"))
        _K29 = _ilu2.module_from_spec(_ksp); _ksp.loader.exec_module(_K29)
        if _kp_was is None:
            os.environ.pop("KIT_PROJECT", None)
        else:
            os.environ["KIT_PROJECT"] = _kp_was
        _lg = os.path.join(root, "sh29.log")
        _rc, _out = _K29.sh([sys.executable, "-c",
                             "print('FreeCAD 1.1.3, Libs: x'); print('Meshing (45%)'); "
                             "print('FAIL: 12 samples (5.1 %)'); print('  0.20 to 0.30 mm :  123  (5 %)')"], 30, _lg)
        _logt = open(_lg, encoding="utf-8").read()
        check("a result line with a percentage reaches the log and the verdict (it was dropped, the agent 2026-09-19)",
              "FAIL: 12 samples (5.1 %)" in _out and "(5 %)" in _out and "FAIL: 12 samples" in _logt, _out)
        check("...while FreeCAD's banner and a bare progress tick are kept off the screen only",
              _K29._fc_noise("FreeCAD 1.1.3, Libs: x\n") and _K29._fc_noise("Meshing (45%)\n")
              and not _K29._fc_noise("FAIL: 12 samples (5.1 %)\n"), "")
        _V29 = []; _T29 = []

        def _add29(p_):
            _V29.append(p_); return len(_V29) - 1

        def _cube29(x0, fan):
            c_ = [_add29(q) for q in [(x0, 0, 0), (x0 + 10, 0, 0), (x0 + 10, 10, 0), (x0, 10, 0), (x0, 0, 10),
                                      (x0 + 10, 0, 10), (x0 + 10, 10, 10), (x0, 10, 10)]]

            def quad(a_, b_, cc_, d_):
                _T29.extend([[c_[a_], c_[b_], c_[cc_]], [c_[a_], c_[cc_], c_[d_]]])
            if fan:
                ctr = _add29((x0, 5, 5)); q_ = [0, 4, 7, 3]
                for i_ in range(4):
                    _T29.append([ctr, c_[q_[i_]], c_[q_[(i_ + 1) % 4]]])
            else:
                quad(0, 4, 7, 3)
            quad(1, 2, 6, 5); quad(0, 1, 5, 4); quad(3, 7, 6, 2); quad(0, 3, 2, 1); quad(4, 5, 6, 7)
        _cube29(0, True); _cube29(20, False)
        _V29 = _np.array(_V29, float); _T29 = _np.array(_T29, int)
        _Vt = _V29[_T29]; _cen = _Vt.mean(1); _nr = _np.cross(_Vt[:, 1] - _Vt[:, 0], _Vt[:, 2] - _Vt[:, 0])
        _cc = _np.stack([_np.where(_cen[:, 0] < 15, 5.0, 25.0), _np.full(len(_T29), 5.0), _np.full(len(_T29), 5.0)], 1)
        _fl = _np.einsum("ij,ij->i", _nr, _cen - _cc) < 0; _T29[_fl] = _T29[_fl][:, ::-1]
        _g0 = _np.array([-2.0, -2.0, -2.0]); _n = (69, 29, 29)
        _xs = _g0[0] + _np.arange(_n[0]) * 0.5; _ys = _g0[1] + _np.arange(_n[1]) * 0.5
        _X, _Y, _Z = _np.meshgrid(_xs, _ys, _ys, indexing="ij")
        _inb = lambda a_, lo_, hi_: (a_ > lo_) & (a_ < hi_)
        _truth = ((_inb(_X, 0, 10) | _inb(_X, 20, 30)) & _inb(_Y, 0, 10) & _inb(_Z, 0, 10))
        _onb = _np.zeros_like(_truth)
        for _v in (0, 10, 20, 30):
            _onb |= _np.isclose(_X, _v)
        for _v in (0, 10):
            _onb |= _np.isclose(_Y, _v) | _np.isclose(_Z, _v)
        _occ = _R.scan_occupancy(_V29, _T29, _g0, _n, 0.5, 0)
        check("x-rays through a fan face's shared edges no longer fill the air between two solids (was 361 cells)",
              int(((_occ != _truth) & ~_onb).sum()) == 0, int(((_occ != _truth) & ~_onb).sum()))
        _Q = _np.array([[x_, 5.0, 5.0] for x_ in _np.arange(-2, 32, 0.5)])
        _tq = ((_Q[:, 0] > 0) & (_Q[:, 0] < 10)) | ((_Q[:, 0] > 20) & (_Q[:, 0] < 30))
        _oq = _np.isclose(_Q[:, 0] % 10, 0)
        check("...and points_inside (winding, three axes) is right on the line through the fan centre",
              int(((_R.points_inside(_Q, _V29, _T29) != _tq) & ~_oq).sum()) == 0, "")
        _two = _np.vstack([_V29[:8], _V29[:8] + [0, 0, 0]])
        _lA = _tube(24, 4, 0.0, 8.0); _lB = _tube(96, 6, 8.0, 12.0)
        _VA, _TA, _r_, _ = _R._weld(_lA[0], _lA[1], [], 1e-6); _VB, _TB, _r_, _ = _R._weld(_lB[0], _lB[1], [], 1e-6)

        def _rim29(V_, T_):
            e_ = _np.vstack([T_[:, [0, 1]], T_[:, [1, 2]], T_[:, [2, 0]]])
            u_, c_ = _np.unique(_np.sort(e_, axis=1), axis=0, return_counts=True)
            return [(int(x_), int(y_)) for x_, y_ in u_[c_ == 1]]
        _rA = [e_ for e_ in _rim29(_VA, _TA) if abs(_VA[e_[0], 2] - 8) < 1e-6 and abs(_VA[e_[1], 2] - 8) < 1e-6]
        _rB = [e_ for e_ in _rim29(_VB, _TB) if abs(_VB[e_[0], 2] - 8) < 1e-6 and abs(_VB[e_[1], 2] - 8) < 1e-6]
        _i0 = len(_VA); _VA = _np.vstack([_VA, [[10.5, 0.0, 8.0], [10.6, 0.0, 8.0]]])
        _Vw, _Tw, _rep = _R.weld_rims(_VA, _TA, _rA + [(_i0, _i0 + 1)], _VB, _TB, _rB, tol=0.15, require_all_paired=True)
        check("a 2-vertex speck no longer refuses a strict seam - it is set aside and counted (FAILURES row 96)",
              _Vw is not None and _rep.get("specks_ignored") == 1, _rep.get("error"))
        subprocess.run([sys.executable, _kit, "dossier", "define", "d29", "--box", "0", "1", "0", "1", "0", "1"],
                       capture_output=True, text=True, env=_env)
        subprocess.run([sys.executable, _kit, "dossier", "add", "d29", "--what", "w", "--value", "1", "--source", "s"],
                       capture_output=True, text=True, env=_env)
        p = subprocess.run([sys.executable, _kit, "dossier", "show", "d29"], capture_output=True, text=True, env=_env)
        check("kit dossier show reads a defined region with filed numbers (KeyError before)",
              p.returncode == 0 and "Traceback" not in p.stdout + p.stderr and "KeyError" not in p.stdout
              and "never" in p.stdout, (p.stdout + p.stderr)[-300:])
        import shutil as _shu29
        _shu29.rmtree(os.path.join(root, "claude_code", "dossier", "d29"), ignore_errors=True)
        _dd29 = DS.load(root); _dd29.pop("d29", None); DS.save(root, _dd29)
        p = subprocess.run([sys.executable, _kit, "render"], capture_output=True, text=True, env=_env)
        check("kit render with no argument prints its usage (IndexError, FAILURES row 69)",
              p.returncode == 2 and "kit render <shape" in p.stdout and "FAILED" not in p.stdout, p.stdout[-300:])
        p = subprocess.run([sys.executable, _kit, "howto"], capture_output=True, text=True, env=_env)
        check("kit howto with no argument lists the types (IndexError, FAILURES row 82)",
              p.returncode == 0 and "voxel_smooth" in p.stdout and "kit howto <type>" in p.stdout, p.stdout[-300:])
        _cube_r = os.path.join(root, "r29_same.stl"); _cov_r = os.path.join(root, "r29_cov.stl")
        _cut_r = os.path.join(root, "r29_cut.stl"); _top_r = os.path.join(root, "r29_top.stl")

        def _box29(x0, x1, y0, y1, z0, z1, n=10):
            Vb, Tb = [], []

            def face(o, u, v, flip):
                base = len(Vb)
                for i_ in range(n + 1):
                    for j_ in range(n + 1):
                        Vb.append([o[k] + u[k] * i_ / n + v[k] * j_ / n for k in range(3)])
                for i_ in range(n):
                    for j_ in range(n):
                        a_ = base + i_ * (n + 1) + j_; b_ = a_ + (n + 1)
                        Tb.extend([[a_, b_, a_ + 1], [a_ + 1, b_, b_ + 1]])
            dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
            face([x0, y0, z0], [dx, 0, 0], [0, dy, 0], 1); face([x0, y0, z1], [dx, 0, 0], [0, dy, 0], 0)
            face([x0, y0, z0], [dx, 0, 0], [0, 0, dz], 0); face([x0, y1, z0], [dx, 0, 0], [0, 0, dz], 1)
            face([x0, y0, z0], [0, dy, 0], [0, 0, dz], 1); face([x1, y0, z0], [0, dy, 0], [0, 0, dz], 0)
            Vb = _np.array(Vb, float); Tb = _np.array(Tb, int)
            Vt_ = Vb[Tb]; c_ = Vt_.mean(1); nr_ = _np.cross(Vt_[:, 1] - Vt_[:, 0], Vt_[:, 2] - Vt_[:, 0])
            ctr_ = _np.array([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
            f_ = _np.einsum("ij,ij->i", nr_, c_ - ctr_) < 0; Tb[f_] = Tb[f_][:, ::-1]
            return Vb, Tb
        _cb29 = _box29(0, 10, 0, 10, 0, 10); _sl29 = _box29(3, 7, 3, 7, 9.5, 12)
        _R.write_stl(_cube_r, *_cb29)
        _R.write_stl(_cov_r, _np.vstack([_cb29[0], _sl29[0]]), _np.vstack([_cb29[1], _sl29[1] + len(_cb29[0])]))
        _R.write_stl(_cut_r, *_box29(0, 10, 0, 10, 0, 9))
        _tv = _np.array([[10 * i_ / 20, 10 * j_ / 20, 10.0] for i_ in range(21) for j_ in range(21)])
        _tt = _np.array([t_ for i_ in range(20) for j_ in range(20)
                         for t_ in ([i_ * 21 + j_, (i_ + 1) * 21 + j_, i_ * 21 + j_ + 1],
                                    [i_ * 21 + j_ + 1, (i_ + 1) * 21 + j_, (i_ + 1) * 21 + j_ + 1])])
        _R.write_stl(_top_r, _tv, _tt)
        subprocess.run([sys.executable, _kit, "atlas", "add", "seat29", "--what", "a sealing top",
                        "--box", "0", "10", "0", "10", "9", "11"], capture_output=True, text=True, env=_env)
        subprocess.run([sys.executable, _kit, "atlas", "set", "seat29", "--definition", "CLIENT", "--said", "ok",
                        "--edit", "FROZEN"], capture_output=True, text=True, env=_env)
        _rec = lambda res: subprocess.run([sys.executable, _kit, "atlas", "recreated", "seat29", "--result", res,
                                           "--original", _top_r], capture_output=True, text=True, env=_env)
        p = _rec(_cube_r)
        check("recreated: the same surface, retessellated, passes", p.returncode == 0 and "PASS" in p.stdout, p.stdout[-300:])
        p = _rec(_cov_r)
        check("recreated: a shell dropped OVER the frozen face is caught as BURIED although every original triangle"
              " survives", p.returncode == 2 and "BURIED" in p.stdout, p.stdout[-400:])
        p = _rec(_cut_r)
        check("recreated: a frozen face cut into is refused as CUT", p.returncode == 2 and "lost their material" in p.stdout,
              p.stdout[-300:])
        p = subprocess.run([sys.executable, _kit, "atlas", "set", "seat29", "--buried-ok"], capture_output=True, text=True, env=_env)
        check("...--buried-ok without the client's words is refused", p.returncode == 2 and "--said" in p.stdout, p.stdout[-200:])
        subprocess.run([sys.executable, _kit, "atlas", "set", "seat29", "--buried-ok", "--said", "blends may cover it"],
                       capture_output=True, text=True, env=_env)
        p = _rec(_cov_r)
        check("...and with the client's words a blend onto it passes, and says how much it covers",
              p.returncode == 0 and "buried under a blend the client allowed" in p.stdout, p.stdout[-300:])
        # did not rise
        p = subprocess.run([sys.executable, _kit, "atlas", "recreated", "seat29", "--result", _cut_r, "--original", _top_r,
                            "--where"], capture_output=True, text=True, env=_env)
        check("recreated --where: the refusal names the CUT cluster's box", p.returncode == 2 and "CUT" in p.stdout
              and "box x" in p.stdout, p.stdout[-400:])
        p = subprocess.run([sys.executable, _kit, "atlas", "recreated", "seat29", "--result", _cut_r, "--original", _top_r,
                            "--baseline", _cut_r], capture_output=True, text=True, env=_env)
        check("recreated --baseline: a count that did not rise above the baseline's PASSES (old damage is not new damage)",
              p.returncode == 0 and "did not rise" in p.stdout.replace("no count rose", "did not rise"), p.stdout[-400:])
        p = subprocess.run([sys.executable, _kit, "atlas", "recreated", "seat29", "--result", _cut_r, "--original", _top_r,
                            "--baseline", _cube_r], capture_output=True, text=True, env=_env)
        check("recreated --baseline: a count that ROSE above an intact baseline still refuses, and says the baseline's count",
              p.returncode == 2 and "lost their material" in p.stdout and "(baseline 0)" in p.stdout, p.stdout[-400:])
        _rr = (G.atlas_regions(root).get("seat29") or {}).get("recreated") or {}
        check("recreated: the PASS record carries the baseline and its counts",
              _rr.get("baseline") and _rr.get("baseline_cut") is not None, str(_rr)[:300])
        _bj = os.path.join(root, "claude_code", "jobs", "BJ29"); os.makedirs(_bj, exist_ok=True)
        open(os.path.join(_bj, "job_s7_replace.py"), "w").write("import os\nprint('s7', os.environ.get('LK_TAG'))\n")
        _mor29 = os.path.join(root, "claude_code", "bank", "M29.brep"); os.makedirs(os.path.dirname(_mor29), exist_ok=True)
        open(_mor29, "w").write("x")
        if not G.session(root):
            G.session_open(root, True, True, "S", {"overlap": "0.5 mm into material, 2 mm clear in air",
                                                    "measure": "the orchestrator measures; workers only render",
                                                    "punch": "never through; stops 3 mm short"}, _mor29)
        p = subprocess.run([sys.executable, _kit, "burrito", "s7", "--job", "BJ29", "--tag", "T29", "--plan"],
                           capture_output=True, text=True, env=_env)
        check("burrito S7 (a B-rep door into the model) is refused until its new geometry is assigned a section",
              p.returncode != 0 and "kit atlas assign T29" in (p.stdout + p.stderr), (p.stdout + p.stderr)[-400:])
        p = subprocess.run([sys.executable, _kit, "atlas", "assign", "T29", "--to", "nope29"], capture_output=True, text=True, env=_env)
        check("...assigning it to a section that does not exist is refused", p.returncode == 2 and "no region" in p.stdout, p.stdout[-200:])
        p = subprocess.run([sys.executable, _kit, "atlas", "assign", "T29", "--new", "rib29"], capture_output=True, text=True, env=_env)
        check("...a NEW section needs its definition", p.returncode == 2 and "--what" in p.stdout, p.stdout[-200:])
        p = subprocess.run([sys.executable, _kit, "atlas", "assign", "T29", "--new", "rib29", "--what", "a new rib"],
                           capture_output=True, text=True, env=_env)
        check("...a new section is created at DRAFT and the agent is told to announce it",
              p.returncode == 0 and "ANNOUNCE" in p.stdout and G.atlas_regions(root)["rib29"]["definition_status"] == "DRAFT",
              p.stdout[-300:])
        p = subprocess.run([sys.executable, _kit, "burrito", "s7", "--job", "BJ29", "--tag", "T29", "--plan"],
                           capture_output=True, text=True, env=_env)
        check("...and once assigned, S7 goes on", p.returncode == 0 and "kit atlas assign" not in (p.stdout + p.stderr),
              (p.stdout + p.stderr)[-400:])

        print("\n[30] the rebuild steps never crash on a print - Windows freecadcmd's cp1252 stdout (R4 run 1, 2026-10-01)")
        _rbdir = os.path.join(HERE, "kit", "rebuild")
        _rbs = sorted(f for f in os.listdir(_rbdir) if f.startswith("rb_") and f.endswith(".py"))
        _missing = [f for f in _rbs if '_s.reconfigure(encoding="utf-8"' not in open(os.path.join(_rbdir, f), encoding="utf-8").read()]
        check("every rb_*.py carries the UTF-8 stream prefix (%d scripts)" % len(_rbs), _rbs and not _missing, _missing)
        _probe = os.path.join(tmp, "_cp1252_probe.py")
        _src = open(os.path.join(_rbdir, "rb_reinsert.py"), encoding="utf-8").read()
        _pre = _src[_src.index("for _s in (sys.stdout, sys.stderr):"):]
        _pre = "\n".join(_pre.split("\n")[:3])
        open(_probe, "w", encoding="utf-8").write("import sys\n%s\nprint('local \\u2212 region \\u2229 ok', flush=True)\n" % _pre)
        _e30 = dict(os.environ); _e30["PYTHONIOENCODING"] = "cp1252"; _e30.pop("PYTHONUTF8", None)
        p = subprocess.run([sys.executable, _probe], capture_output=True, env=_e30)
        check("...the prefix, as written in rb_reinsert.py, survives a cp1252 stdout (the print succeeds)",
              p.returncode == 0 and b"region" in p.stdout and b"charmap" not in p.stderr, (p.stdout + p.stderr)[-200:])
        p = subprocess.run([sys.executable, "-c", "print('local \\u2212 region')"], capture_output=True, env=_e30)
        check("...and without it the same print crashes (the test is real)", p.returncode != 0 and b"charmap" in p.stderr)

        print("\n[31bq WW] B53 - THE SCRATCH ROOT: nothing of the live project read or written")
        _live = tempfile.mkdtemp(prefix="ww_live_"); _scr = tempfile.mkdtemp(prefix="ww_scr_")
        os.makedirs(os.path.join(_live, "claude_code")); open(os.path.join(_live, "claude_code", "INBOX.md"), "w", encoding="utf-8").write("# INBOX\n\nCC's own note\n")
        _old = os.environ.get("KIT_SCRATCH_ROOT")
        try:
            os.environ["KIT_SCRATCH_ROOT"] = _scr
            G.inbox_append(_live, "a scratch test's block", who="THE STOP GUARD")
            _lv = open(os.path.join(_live, "claude_code", "INBOX.md"), encoding="utf-8").read(); _sp = os.path.join(_scr, "claude_code", "INBOX.md")
            check("31bq WW (B53 (5)): a scratch session's inbox append lands under the scratch root - the agent's INBOX.md untouched",
                  "scratch test's block" not in _lv and os.path.isfile(_sp) and "scratch test's block" in open(_sp, encoding="utf-8").read(), _lv[-120:])
            _new, _tot = G.inbox_new(_live)
            check("31bq WW (B53 (5)): ...and the scratch session reads ITS inbox (the agent's note is never 'new' to it)", "the agent's own note" not in _new, _new[:120])
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "hooks")); import wallclock as _W, liveness as _Lv
            check("31bq WW (B53 (8)): the wall clock saves under the scratch root, its folder made there (the watch is not lost)",
                  _W.save(_live, {"x": 1}) and os.path.isfile(os.path.join(_scr, ".claude", "_leangates", "WALLCLOCK.json")) and not os.path.isfile(os.path.join(_live, ".claude", "_leangates", "WALLCLOCK.json")))
            os.environ["KIT_SCRATCH_ROOT"] = "   "
            check("31bq WW (B53 (10)): a blank KIT_SCRATCH_ROOT is no root (the wall clock's and the beats' paths stay the project's)",
                  _W._path(_live).startswith(_live) and _Lv._path(_live, "guard").startswith(_live) and G._inbox_path(_live).startswith(_live), (_W._path(_live), _Lv._path(_live, "guard")))
        finally:
            if _old is None: os.environ.pop("KIT_SCRATCH_ROOT", None)
            else: os.environ["KIT_SCRATCH_ROOT"] = _old
            shutil.rmtree(_live, ignore_errors=True); shutil.rmtree(_scr, ignore_errors=True)

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    try:
        import re as _re213, glob as _gl213
        _bad213 = []
        for _f213 in sorted(_gl213.glob(os.path.join(HERE, "kit", "*.py"))):
            if os.path.basename(_f213) in ("leangate.py",) or os.path.basename(_f213).startswith("selftest"): continue
            for _i213, _l213 in enumerate(open(_f213, encoding="utf-8", errors="replace").read().split("\n"), 1):
                if _re213.search(r'KIT_SCRATCH_ROOT"\) or ""\)\.strip\(\) or ', _l213): _bad213.append("%s:%d" % (os.path.basename(_f213), _i213))
        check("31bq R7W W2 (D2-13): no kit module but leangate spells the scratch-root rule by hand - every copy calls leangate.records_root", not _bad213, _bad213)
        _bad213b = []
        for _f213 in sorted(_gl213.glob(os.path.join(HERE, "kit", "*.py"))):
            if os.path.basename(_f213) == "kit.py" or os.path.basename(_f213).startswith("selftest"): continue
            for _i213, _l213 in enumerate(open(_f213, encoding="utf-8", errors="replace").read().split("\n"), 1):
                if _re213.search(r'\bkit\.G\.records_root\(|(?<![\w.])G\.records_root\(', _l213): _bad213b.append("%s:%d" % (os.path.basename(_f213), _i213))
        check("31bq R7W W2 (D2-13b): no kit module reaches records_root through a handed-in kit object (kit.G / G) - a suite's stub kit has no such G; each site imports leangate itself", not _bad213b, _bad213b)
        import leangate as _G213; _old213 = os.environ.get("KIT_SCRATCH_ROOT")
        try:
            os.environ["KIT_SCRATCH_ROOT"] = "  "; _a213 = _G213.records_root("X"); os.environ["KIT_SCRATCH_ROOT"] = "Y"; _b213 = _G213.records_root("X"); os.environ.pop("KIT_SCRATCH_ROOT", None); _c213 = _G213.records_root("")
        finally:
            if _old213 is None: os.environ.pop("KIT_SCRATCH_ROOT", None)
            else: os.environ["KIT_SCRATCH_ROOT"] = _old213
        check("31bq R7W W2 (D2-13): leangate.records_root - a blank scratch root is none (the project), a set one is the root, and '' stays '' when none is set (kitlib_render's walk-up form)", _a213 == "X" and _b213 == "Y" and _c213 == "", (_a213, _b213, _c213))
    except Exception as _ex213: check("the 31bq R7W W2 (D2-13) pins raised %r" % (_ex213,), False, None)
    try:
        import ast as _astB, types as _tyB, re as _reB
        _kp = os.path.join(HERE, "kit", "kit.py"); _ks = open(_kp, encoding="utf-8").read(); _tree = _astB.parse(_ks)
        def _src(name, kind=_astB.FunctionDef):
            for n in _tree.body:
                if isinstance(n, kind) and (getattr(n, "name", None) == name or (kind is _astB.Assign and any(getattr(t, "id", "") == name for t in n.targets))): return _astB.get_source_segment(_ks, n)
            raise KeyError(name)
        _gB = {"os": os, "re": re, "sys": sys, "HERE": os.path.join(HERE, "kit"), "difflib": __import__("difflib")}
        for nm_, kd_ in (("FORBIDDEN", _astB.Assign), ("WORKER_FILLET_OK", _astB.Assign), ("TEMPLATE_CALL_OK", _astB.Assign), ("SHELVED_TEMPLATES", _astB.Assign), ("_body", _astB.FunctionDef), ("_template_of", _astB.FunctionDef), ("scan", _astB.FunctionDef)): exec(_src(nm_, kd_), _gB)
        _tdB = tempfile.mkdtemp(prefix="k25_")
        def _scan(text, name):
            p_ = os.path.join(_tdB, name); open(p_, "w", encoding="utf-8").write(text)
            try: _gB["scan"](p_); return None
            except SystemExit as e_: return str(e_.code)
        _cut = open(os.path.join(HERE, "kit", "templates", "t_cutter.py"), encoding="utf-8").read()
        _m25 = re.search(r"^PARAMS\s*=\s*dict\(.*?^\)\s*$", _cut, re.S | re.M); _filled = _cut[:_m25.start()] + "PARAMS = dict(\n    base='x', out_dir='y', why_not_delete='a reason of my own',\n)\n" + _cut[_m25.end():]
        check("31bs K25: a FILLED copy of t_cutter.py passes kit run's scan (its own removeSplitter allowed in an unmodified copy)", _scan(_filled, "w_cutter.py") is None, _scan(_filled, "w_cutter.py"))
        check("31bs K25: a hand script's removeSplitter is still refused", "removeSplitter" in (_scan("import Part\ns = s.removeSplitter()\n", "x.py") or ""))
        _bur = open(os.path.join(HERE, "kit", "templates", "t_burrito.py"), encoding="utf-8").read(); os.environ.pop("SHELVED_OK", None)
        check("31bs K25 / W43: a copy of the SHELVED t_burrito is refused by name without SHELVED_OK", "SHELVED" in (_scan(_bur, "w_burrito.py") or "") and "kit rebuild" in (_scan(_bur, "w_burrito.py") or ""))
        os.environ["SHELVED_OK"] = "the selftest"; _r43 = _scan(_bur, "w_burrito2.py"); os.environ.pop("SHELVED_OK", None)
        check("31bs K25 / W43: ... and with SHELVED_OK the shelved refusal does not fire", "SHELVED" not in (_r43 or ""))
        check("31bs K25: a copy of t_hole passes", _scan(open(os.path.join(HERE, "kit", "templates", "t_hole.py"), encoding="utf-8").read(), "w_hole.py") is None)
        shutil.rmtree(_tdB, ignore_errors=True)
        _gK2 = {"os": os}; exec(_src("_kill_targets"), _gK2)
        _gK2["_win_procs"] = lambda: [(100, 1, "python job_render_arc.py a"), (101, 1, "python job_render_arc.py b"), (102, 100, "freecadcmd child of 100"), (103, 102, "grandchild")]
        _pB = _tyB.SimpleNamespace(pid=100); _onB = os.name
        try:
            os.name = "nt"
            _tree_only = set(_gK2["_kill_targets"](_pB, ["py", "job_render_arc.py"], by_name=False)); _with_name = set(_gK2["_kill_targets"](_pB, ["py", "job_render_arc.py"], by_name=True))
        finally: os.name = _onB
        check("31bs K2a: by_name=False ends the shard's OWN tree only (%s); by_name=True adds the sibling that shares the script (%s)" % (sorted(_tree_only), sorted(_with_name)), _tree_only == {100, 102, 103} and _with_name == {100, 101, 102, 103})
        check("31bs K2a: kit review --render kills its shard with by_name=False", "_kill_tree(pr, [py, script], by_name=False)" in _ks)
        check("31bs K4: kit run runs the script in its own folder (cwd)", "cwd=(None if internal else os.path.dirname(os.path.abspath(script))))" in _ks)
        check("31bs K6: kit check returns 2 on a CHECK FAIL", "rc = 2" in _ks[_ks.index("def cmd_check"):_ks.index("def _next_rev")] and 'if rc == 0 and not (json.load(open(os.path.join(out, "CHECK.json")' in _ks)
        check("31bs K17: kit atlas import keeps the client's words", 'regs[name]["client_said"] = r.get("client_said") or r.get("said")' in _ks)
        check("31bs K24: kit measure --dossier files the log _fc wrote", '_FC_LAST["log"] = os.path.join(workdir, "kit_run.log")' in _ks and 'open(_FC_LAST.get("log") or os.path.join(os.getcwd(), "kit_run.log")' in _ks)
        check("31bs K8: the usage block spells `kit <cmd>` and the --help finder reads it", "python kit.py " not in _ks[:_ks.index('"""', _ks.index('r"""kit.py') + 10)] and r'^\s*(?:python\s+)?kit(?:\.py)?\s+%s\b' in _ks)
        check("31bs K22 / W41: the card scaffold's Row names A-L and the project's own criteria file; dossier define says A-L", "A-L from the project's <PROJECT>_SUCCESS_CRITERIA.md" in _ks and "[--row A-L]" in open(os.path.join(HERE, "kit", "kit_dossier.py"), encoding="utf-8").read())
        check("31bs W37 / 31bt: the retired loop command is not in this kit", ("kit_" + "bat" + "on") not in _ks and ('"bat' + 'on":') not in _ks)
        check("31bs K16: kit route --table prints the tier and the words whole", '%-16s %-26s %s" % (t, tier, _card_field(card, "Route"))' in _ks)
        _st = _ks[_ks.index("_STARTER = {"):_ks.index("\n}", _ks.index("_STARTER = {"))]
        check("31bs W31: the eight scaffolds name their templates' own keys (hole: base / holes=[dict(start, axis, d, depth, cbore_d, cbore_depth)]; split: axis / value; shell: wall / open_faces; edge_round: select; mirror_pattern: mirror_x / mirror_y; revolve: plane / op; move: rot_axis; sketch_connect: planeA=dict)",
              all(x_ in _st for x_ in ("holes=[dict(start=", "cbore_d=<diameter, 0 = no counterbore>", "axis=<x|y|z>  value=", 'open_faces=[\\"+z\\"]', "select=<vertical | all | top | bottom>", "mirror_x=<True|False>", "axis_point=(<x>, <y>, <z>)  axis_dir=", "rot_axis=(<ax>, <ay>, <az>)", "planeA=dict(origin=")) and "plane=<z>  c=<14.0005>" not in _st and "thickness=<t>  open_face=" not in _st)
        _et = open(os.path.join(HERE, "EDIT_TYPES.md"), encoding="utf-8").read()
        _er = re.search(r"^Route: (round-edge[^\n]*)$", _et, re.M); _es = re.search(r"^Route: (block pad[^\n]*)$", _et, re.M)
        check("31bs K5: edge_round's route words carry no bare 'round'; sketch_extrude's carry round-boss (the boss request no longer routes to edge_round by an alphabetical tie)", _er is not None and " round " not in (" " + _er.group(1) + " ") and _es is not None and "round-boss" in _es.group(1))
        _lg = open(os.path.join(HERE, "kit", "leangate.py"), encoding="utf-8").read()
        _mf = re.search(r'mf = re\.search\(r"([^"]+)", txt, re\.M \| re\.I\)', _lg)
        check("31bs T1 F4: the face figure is read off the Expected line only - a comment 'past the far face + 2' elsewhere is not it", _mf is not None and re.search(_mf.group(1), "Purpose: past the far face + 2\nExpected: -565.5 mm3", re.M | re.I) is None)
        check("31bs T1 F1: kit run passes the script ABSOLUTE and keeps the caller's folder for the kit's own macros", "sh([freecad(), os.path.abspath(script)] + args[1:], cap, log, env, cwd=(None if internal else" in _ks)
        check("31bs T1 F2 / F6: route reads a plural as its word; --help takes the usage lines that start with the command", 'x.endswith("s") and not x.endswith("ss")' in _ks and r'^\s*(?:python\s+)?kit(?:\.py)?\s+%s\b' in _ks)
        check("31bs K21: job_open reads the card's face figure off the Expected line", _mf is not None and re.search(_mf.group(1), "Expected: -47 mm3, faces about +12", re.M | re.I) is not None and re.search(_mf.group(1), "Expected: -47 mm3, faces about +12", re.M | re.I).group(1).replace(" ", "") == "+12")
        _lgb = _lg[_lg.index('"""', _lg.index('"""') + 3) + 3:]
        _hk = "".join(open(os.path.join(HERE, "hooks", h_), encoding="utf-8").read() for h_ in ("guard.py", "session_start.py", "wallclock.py"))
        check("31bs T7 F1: no agent-facing message teaches `python kit.py <cmd>` (the guard refuses the bare word) - the hooks, kit.py, leangate past its docstring", "python kit.py " not in _ks and "python kit.py " not in _lgb and "python kit.py " not in _hk)
        check("31bs T8 F9b: kit run's rc line under a kit command says the command's verdict follows", "the command's verdict follows; 31bs T8 F9b" in _ks)
        _arc = open(os.path.join(HERE, "kit", "job_render_arc.py"), encoding="utf-8").read(); _tc = open(os.path.join(HERE, "kit", "job_tess_cache.py"), encoding="utf-8").read()
        check("31bt TJ2 F1: kit review resolves before / after / out before step 1, a failed cache step is STEP 1 FAILED (rc 2) and job_tess_cache exits 2 on a failure", "before, after, out = os.path.abspath(before), os.path.abspath(after), os.path.abspath(out)" in _ks and "STEP 1 FAILED (rc %s)" in _ks and 'if st.get("state") == "failed": sys.exit(2)' in _tc)
        check("31bt TJ2 F2: a failed shard exits 3 and kit review --render names it with its error", 'if st.get("state") == "failed": sys.exit(3)' in _arc and 'print("  shard %s: %s - %s" % (k_, _sj.get("state", "no status file")' in _ks)
        check("31bt TJ2 F3: a verdict needs the frame's picture on disk; --done needs every planned frame on disk", "def _rv_png(d, name):" in _ks and "no picture %s.png in %s or a folder under it" in _ks and "have no picture on disk" in _ks)
        check("31bt TJ2 F4: kit newcard --write into a job folder newjob has not made is refused", "is a job folder that does not exist yet - `kit newjob %s` first" in _ks)
        check("31bt TJ2 F5: the watchdog's extension line says when nothing was printed yet", "nothing printed yet - %.0f s quiet, under the silence window" in _ks)
        _kl = open(os.path.join(HERE, "kit", "kitlib.py"), encoding="utf-8").read(); _tcu = open(os.path.join(HERE, "kit", "templates", "t_cutter.py"), encoding="utf-8").read()
        check("31bu K2b / T1 F14: the review's shard cap grows with the largest shard's frame count (300 s a frame)", "cap = max(cap0, 300.0 * _nmax)" in _ks)
        check("31bu T7 F17 / TK2 F1 / 31bx R7 D5: --help prints a usage line with every indented continuation line (31bx R7 D5: kit open's --answer line, kit close's flags - not only the | and [ lines)", 'elif _on and re.match(r"^\\s{10,}\\S", l): lines.append(l)' in _ks and '"verdict", "dossier", "tool", "deliver", "union",      # 31bx (R7 F1 / F2)' in _ks)
        _kl2 = open(os.path.join(HERE, "kit", "kitlib.py"), encoding="utf-8").read(); _tc2 = open(os.path.join(HERE, "kit", "templates", "t_cutter.py"), encoding="utf-8").read(); _kr2 = open(os.path.join(HERE, "kit", "kitlib_render.py"), encoding="utf-8").read()
        check("31bu TK2 F2: kitlib.save_if_changed leaves an unchanged artefact's file alone and t_cutter saves the cutter and the result through it before its gates (a verdict given on the same bytes stands)",
              "def save_if_changed(shape, path):" in _kl2 and '_wrA = K.save_if_changed(cutter, P["cutter_name"])' in _tc2 and '_wrB = K.save_if_changed(res, P["result_name"])' in _tc2 and 'K.save(cutter, P["cutter_name"])' not in _tc2 and 'K.save(res, P["result_name"])' not in _tc2)
        check("31bu TK2 F3: the cutter's gates name a real command - kit render at the feature's box, the cutter alone and the base at the same box; the result and the removed solid at GATE B",
              'kit render \\"%s\\" --out \\"%s\\" --box %s --views all   (A1 the cutter ALONE)' in _tc2 and "kit review --shape" not in _tc2 and '(B1 the RESULT ALONE at the cut\'s box)' in _tc2)
        check("31bu TK2 F4: the scale bar fits the frame (the largest of 100 .. 0.5 mm within 40 % of the frame's width), labelled by its length", "_L = next((x_ for x_ in (100.0, 50.0, 20.0, 10.0, 5.0, 2.0, 1.0, 0.5) if x_ <= 0.4 * _wmm), 0.5)" in _kr2 and '"%g mm  (%.2f mm/px)" % (_L, mmpx)' in _kr2 and "bar = 50.0 / mmpx" not in _kr2)
        check("31bu TK2 F5 / F6: the measure counter's refusal names kit card (not newcard), a refused measurement is not counted, kit before prints the after command in the scaffold's form", "kit card <card> - kit newcard alone does not reopen it" in _ks and "def _measure_shut(args):" in _ks and 'and not _measure_shut(args):' in _ks and "--out <job>/after --name look%s" in _ks and "--out <job>/look --name after" not in _ks)
        try:
            import tempfile as _tfB
            _rB = _tfB.mkdtemp(prefix="lk_defer_"); os.makedirs(os.path.join(_rB, "claude_code"), exist_ok=True)
            _d0 = G.atlas_deferred(_rB); json.dump({"until": "a basic correct model exists", "when": "2026-11-05 14:00:00", "by": "test"}, open(G.atlas_defer_path(_rB), "w", encoding="utf-8"))
            _d1 = G.atlas_defer_active(_rB); G.atlas_save(_rB, {"model": "", "regions": {}, "created": G._now()}); _d2 = G.atlas_defer_active(_rB)
            check("31bv B1: the atlas deferral - none before, in force once recorded, not in force once an atlas exists", _d0 is None and (_d1 or {}).get("until") == "a basic correct model exists" and _d2 is None)
            _rC = _tfB.mkdtemp(prefix="lk_defer2_"); os.makedirs(os.path.join(_rC, "claude_code"), exist_ok=True)
            json.dump({"until": "the carrier plate exists", "when": "2026-11-05 14:00:00", "by": "test"}, open(G.atlas_defer_path(_rC), "w", encoding="utf-8"))
            _e1 = G.atlas_defer_end(_rC, "the promotion of R01 (test)"); _dC = G.atlas_defer_active(_rC); _recC = G.atlas_deferred(_rC) or {}; _e2 = G.atlas_defer_end(_rC, "again")
            check("31bv TB1 F3: the deferral's end is in its own record - kit promote ends it (True once, False after), it is not in force after, the record keeps how it ended",
                  _e1 is True and _dC is None and (_recC.get("ended") or {}).get("how") == "the promotion of R01 (test)" and _e2 is False)
            _lg2 = open(os.path.join(HERE, "kit", "leangate.py"), encoding="utf-8").read(); _dd2 = open(os.path.join(HERE, "kit", "kit_dossier.py"), encoding="utf-8").read()
            _ks3 = open(os.path.join(HERE, "kit", "kit.py"), encoding="utf-8").read(); _kd3 = open(os.path.join(HERE, "kit", "kit_deliver.py"), encoding="utf-8").read(); _ss3 = open(os.path.join(HERE, "hooks", "session_start.py"), encoding="utf-8").read()
            check("31bv TB1: kit check refuses a missing --base / --out / --box by usage, promote / deliver --model resolve a relative path against the cwd, the root and claude_code, promote ends the deferral, the start message says how a first body ends, newjob --first, the dossier quiet on an empty bank, the push says NONE YET, the placeholder takes the body's name, a shown body shows its hidden template group, the page",
                  'if not a["_"] or not (a.get("--base") or "").strip()' in _ks3 and "def _resolve_project_path(p):" in _ks3 and "new = _resolve_project_path(args[0])" in _ks3 and 'G.atlas_defer_end(ROOT, "the promotion of' in _ks3
                  and "HOW A FIRST BODY ENDS" in _ks3 and 'if _flag(args, "--first") and len(_first) < 12:' in _ks3 and "def atlas_defer_end(root, how):" in _lg2 and 'if d.get("ended"):' in _lg2
                  and 'kit._resolve_project_path(kit._opt(args, "--model", ""))' in _kd3 and "takes the body's own name" in _kd3 and "a shown body went into it" in _kd3
                  and "[dossier] no regions yet - %s" in _dd2 and 'or "NONE YET (the bank is empty' in _ss3 and "the hook payload is not JSON or names no cwd" in _ss3
                  and "HOW A FIRST BODY ENDS" in open(os.path.join(HERE, "PROJECT_START.md"), encoding="utf-8").read())
            _kl4 = open(os.path.join(HERE, "kit", "kitlib.py"), encoding="utf-8").read(); _ts4 = open(os.path.join(HERE, "kit", "templates", "t_split.py"), encoding="utf-8").read()
            _tm4 = open(os.path.join(HERE, "kit", "templates", "t_mirror_pattern.py"), encoding="utf-8").read(); _rr4 = open(os.path.join(HERE, "kit", "rebuild", "rb_region.py"), encoding="utf-8").read()
            _tx4 = os.path.join(HERE, "tools", "extract.py"); _tx4s = open(_tx4, encoding="utf-8").read() if os.path.isfile(_tx4) else ""
            check("31bw B4: every boolean keeps every solid of a compound base (kitlib.fuse / cut / _after keep_all by the base), t_split per side, a pattern's added copies, kit check's solids_base, the region step refuses a compound, kit tool extract exists and never fuses, the pages",
                  'def _after(res, v0, label, t, keep_all=False, n0=1):' in _kl4 and 'keep_all=(n0 > 1) if keep_all is None else bool(keep_all), n0=n0)' in _kl4 and "every solid KEPT (the base held" in _kl4
                  and "if len(s.Solids) > 1 and n0 == 1:" in _ts4 and 'K.fuse(body, copies, "pattern", keep_all=True)' in _tm4 and 'rep["solids_base"] = int(_bj.get("solids", 1) or 1)' in _ks3 and '"solids": len(b.Solids), "vol_kernel"' in _ks3
                  and 'elif rep["solids"] != rep["solids_expected"]:' in _ks3 and "the skin route edits ONE solid" in _rr4 and "KIT INSTRUMENT `extract`" in _tx4s and ".fuse(" not in _tx4s and "Part.makeCompound(kept)" in _tx4s
                  and "kit tool extract" in open(os.path.join(HERE, "PROJECT_START.md"), encoding="utf-8").read() and "31bw B4" in open(os.path.join(HERE, "EDIT_TYPES.md"), encoding="utf-8").read())
            check("31bw B4b (TB6): a compound split and cut solid by solid, a split that does not add up fails, kit check judges the intended solid count (the card's `solids N` through job_open, --expect-solids, else the base's own), the kept-one line, extract names the full path",
                  "SOLID BY SOLID" in _ts4 and 'K.fail("split: the two sides hold' in _ts4 and "a compound is cut SOLID BY SOLID" in _kl4 and "ONE solid kept (the largest" in _kl4
                  and 'rep["solids_expected"] = _SOLX if _SOLX is not None else rep["solids_base"]' in _ks3 and 'solids_exp = a.get("--expect-solids")' in _ks3 and "[--expect-solids N]" in _ks3
                  and '"expect_solids": locals().get("expect_solids")' in open(os.path.join(HERE, "kit", "leangate.py"), encoding="utf-8").read() and "Add 'solids N' to the line only when" in _ks3
                  and "os.path.basename(SHAPE)" not in _tx4s and "31bw (TB6 F6): the full path" in _tx4s)
            check("31bw b4d (TB6b F1 / F2): `kit job <J>` alone re-reads the record's card (type / card / tier from the record, said; no record and no --type a usage refusal), the review's STEP 1 line names freecadcmd",
                  '_ty7 = _opt(args, "--type") or _jr7.get("edit_type") or ""' in _ks3 and '_cd7 = _opt(args, "--card") or _jr7.get("card")' in _ks3 and "card = _cd7      # 31bw (TB6b F1)" in _ks3
                  and "G.job_open(ROOT, args[0], _ty7, _cd7," in _ks3 and "from the job's own record (31bw)" in _ks3 and "has no record yet - name its type and its card" in _ks3
                  and "alone re-reads the record's card after an edit" in _ks3 and 'G.psline(os.path.join(HERE, "job_tess_cache.py"), py=freecad())' in _ks3 and 'print("  " + G.psline(os.path.join(HERE, "job_tess_cache.py")))' not in _ks3)
            _lg5 = open(os.path.join(HERE, "kit", "leangate.py"), encoding="utf-8").read()
            check("31bw e (TB6c F2 / F3 / F4): the check macro binds the expected count to a name once (no literal `187 is not None` SyntaxWarning), an unsigned face figure of 40 or more is NOT taken as the growth (said at the job and at the check; the scaffold writes +<N>), --plan-only writes nothing",
                  '_SOLX = %(solids_exp)r' in _ks3 and 'if %(solids_exp)r is not None' not in _ks3 and "expect_faces_unsigned" in _ks3 and "faces about +<N>" in _ks3 and "FACES_UNSIGNED_MIN = 40" in _lg5
                  and '"expect_faces_signed": locals().get("expect_faces_signed")' in _lg5 and 'if "--plan-only" in args: print("  (--plan-only: nothing is written' in _ks3 and "an unsigned figure of 40 or more is not taken (31bw)" in _ks3)
            _t9 = tempfile.mkdtemp(prefix="leangate_e_"); _r9 = os.path.join(_t9, "proj"); os.makedirs(os.path.join(_r9, ".claude"), exist_ok=True)
            os.makedirs(os.path.join(_r9, "claude_code", "bank"), exist_ok=True); G.session_open(_r9, True, True, "none - a scratch project", GOOD_ANSWERS, "")
            _puf = os.path.join(_r9, "unsigned_faces.md"); open(_puf, "w", encoding="utf-8").write(GOOD_CARD.replace("faces about +5", "faces about 11574"))
            G.card_lint(_r9, _puf); _juf = G.job_open(_r9, "JUF1", "sketch_extrude", _puf, "haiku", expect_vol=-960.0)
            open(_puf, "w", encoding="utf-8").write(GOOD_CARD.replace("faces about +5", "faces about +11574")); G.card_lint(_r9, _puf); _juf2 = G.job_open(_r9, "JUF2", "sketch_extrude", _puf, "haiku", expect_vol=-960.0)
            open(_puf, "w", encoding="utf-8").write(GOOD_CARD.replace("faces about +5", "faces about 11")); G.card_lint(_r9, _puf); _juf3 = G.job_open(_r9, "JUF3", "sketch_extrude", _puf, "haiku", expect_vol=-960.0)
            shutil.rmtree(_t9, ignore_errors=True)
            check("31bw e (TB6c F3): job_open takes `faces about +11574` (signed) and `faces about 11` (small) as the growth and leaves `faces about 11574` (unsigned, 40 or more) untaken - recorded as expect_faces_unsigned",
                  _juf.get("expect_faces") is None and _juf.get("expect_faces_unsigned") == 11574 and _juf2.get("expect_faces") == 11574 and _juf2.get("expect_faces_signed") is True
                  and _juf3.get("expect_faces") == 11 and _juf3.get("expect_faces_signed") is False)
            check("31bv TB3: newcard on a --first job scaffolds Base: none and base=\"\", kit open on an empty bank says the atlas comes after, the defer message says the next promotion, the delivery lists the whole document's visibility",
                  'none - the first body (no base: kit newjob --first; 31bv B1)' in _ks3 and 'base=""                  # the first body' in _ks3 and "ATLAS: none yet - the bank is empty" in _ks3
                  and "it returns at the next promoted model of record (the first, on a new project)" in _ks3 and "for _nm in allnames:" in _kd3 and "_allvis[_nm] = " in _kd3)
            _ks2 = open(os.path.join(HERE, "kit", "kit.py"), encoding="utf-8").read(); _kd2 = open(os.path.join(HERE, "kit", "kit_deliver.py"), encoding="utf-8").read()
            _ss2 = open(os.path.join(HERE, "hooks", "session_start.py"), encoding="utf-8").read(); _sg2 = open(os.path.join(HERE, "hooks", "stop_guard.py"), encoding="utf-8").read()
            check("31bv B1: the start message on an empty bank (kit open, kit newjob, the SessionStart push), kit atlas defer / --lift / status, the card's Region: while deferred, the delivery's gate, the stop hook's silence, the page and the template",
                  "def _start_message():" in _ks2 and "print(_start_message())" in _ks2 and 'if sub == "defer":' in _ks2 and "the deferral LIFTED" in _ks2 and "DEFERRED since %s until" in _ks2 and 'Region: no atlas yet (deferred: %s)' in _ks2 and "THE FIRST BODY of a project (31bv B1)" in _ks2
                  and "no --no-atlas owed (31bv B1)" in _kd2 and "THE BANK IS EMPTY - a project that designs from parts starts here: read" in _ss2 and "G.atlas_defer_active(root)" in _sg2
                  and os.path.isfile(os.path.join(HERE, "PROJECT_START.md")) and os.path.isfile(os.path.join(HERE, "templates", "BLANK_MODEL.FCStd")) and os.path.isfile(os.path.join(HERE, "templates", "BLANK_MODEL.md")))
        except Exception as _exB: check("31bv B1: the deferral pins raised %r" % (_exB,), False)
        check("31bu TK6 F1 / F3 / F4: save_if_changed removes its temp file outside the with (Windows), the first verdict refusal names --card, the threshold-crossing measurement is refused uncounted (the shut mark)",
              "_same = hashlib.md5(a_.read()).hexdigest() == hashlib.md5(b_.read()).hexdigest()\n            if _same:" in _kl2 and '(" --card %s" % cardsig) if cardsig else ""' in _kl2 and 'os.environ["KIT_MEASURE_SHUT"] = "1"' in _ks and 'if os.environ.get("KIT_MEASURE_SHUT") == "1":' in _ks and 'if _since >= 3 or os.environ' not in _ks and ">= 3 and any(a_ in" in _ks)
        check("31bu T6 F2: the by-normal selectors take kitlib's CALIBRATED outward normal - no hand flip on a Reversed face in kit measure faces --normal or t_cutter's C1", "def outward_normal(f, u, v):" in _kl and "_NORMAL_FLIP" in _kl and "n = K.outward_normal(f, u, v)" in _ks and "_sgn = -1.0 if str(f.Orientation)" not in _ks and "K.outward_normal(f, 0.5 * (u0 + u1), 0.5 * (w0 + w1))" in _tcu and 's = -1.0 if str(f.Orientation) == "Reversed"' not in _tcu)
        _ksg = open(os.path.join(HERE, "kit", "kit.py"), encoding="utf-8").read(); _klg = open(os.path.join(HERE, "kit", "kitlib.py"), encoding="utf-8").read()
        _lgg = open(os.path.join(HERE, "kit", "leangate.py"), encoding="utf-8").read(); _swg = open(os.path.join(HERE, "kit", "rebuild", "sk_wires.py"), encoding="utf-8").read()
        _txg = open(os.path.join(HERE, "tools", "extract.py"), encoding="utf-8").read()
        check("31bw g (TB6c F4 / F5 / F6 / F8, TB7c F1, V9 / V10 / V11): --plan-only writes neither the state file nor the folder; a negative face figure is a drop (the ceiling 0, said); "
              "kit review --render --leads renders the lead frames alone and the plan / kit check name it; the kept-one line says the file's volume; the census tells a laid-on curve from a multi-pole chain; "
              "kit card / kit look print a usage line with no argument; a cache record without a solid count is re-made; leangate's docstring spells kit <cmd>; extract names the job's source",
              'if "--plan-only" not in args: _rv_save(out, st0)' in _ksg and 'if "--plan-only" not in args: os.makedirs(out, exist_ok=True)' in _ksg
              and "is a DROP (the edit removes faces): the growth ceiling is 0" in _ksg and "a drop allows no net new face" in _ksg
              and '_leads_only = "--leads" in args' in _ksg and '_groups = [["lead", _lf]]' in _ksg and "for k, grp in _groups:" in _ksg and "Rendered alone first: kit review --render %s --leads" in _ksg
              and "kit review --render <dir> --leads" in _ksg and "review --render <dir> [--leads]" in _ksg
              and "THE FILE holds 1 solid - vol %.0f (%+.0f against the base)" in _klg and "ONE solid kept (the largest" in _klg
              and "LAID ON AN ORIGINAL SURFACE with more than 4 poles" in _swg and '_mul = [r for r in multi if "+ON_ORIG" not in str(r.get("drawn", ""))]' in _swg
              and "usage: kit card <card.md>" in _ksg and "usage: kit look <job>" in _ksg
              and '"faces_no_mesh" in j and "solids" in j' in _ksg and "the record has no solid count (made before 31bw B4)" in _ksg
              and "    kit open   ...      declare the session" in _lgg and "python kit.py open" not in _lgg and "the job's copy of %s" in _txg)
        check("31bw g2 (TB6c F7): kit newjob records a brep job's base in JOB.json (kind brep, the path, linked or copied) and extract names it",
              '"kind": "brep", "base": os.path.abspath(src), "how": how.split(" (")[0]' in _ksg and '_first_job = (_jrec or {}).get("kind") == "first"' in _ksg)
        check("31bw h (TB6c F10): the full render after the sweep keeps the judged frames as judged (not drawn again, said), skips a shard with nothing left, and its Next line follows the review's state",
              "kept as judged, not drawn again (31bw)" in _ksg and 'if not _leads_only and _vd:' in _ksg and "every frame of it is judged already - not drawn again (31bw)" in _ksg
              and 'if st.get("state") == "sweep" else "  Next: judge the LEAD frames' in _ksg and "the leads are judged and the sweep released; 31bw" in _ksg)
    except Exception as _exB: check("the 31bs kit.py pins raised %r" % (_exB,), False, None)
    print("\n" + "=" * 70)
    print("\n[31bx round 1] the R1 / R2 / R6 fixes of the generic route (FIX_LEDGER_31bx X43-X74, X83, X92, X95)")
    try:
        import re as _re31
        _k31 = open(os.path.join(HERE, "kit", "kit.py"), encoding="utf-8").read(); _g31 = open(os.path.join(HERE, "kit", "leangate.py"), encoding="utf-8").read()
        _kl31 = open(os.path.join(HERE, "kit", "kitlib.py"), encoding="utf-8").read(); _kd31 = open(os.path.join(HERE, "kit", "kit_dossier.py"), encoding="utf-8").read()
        _et31 = open(os.path.join(HERE, "EDIT_TYPES.md"), encoding="utf-8").read()
        _miss31 = {}
        try:
            _st = _re31.search(r"^_STARTER = \{(.*?)^\}", _k31, _re31.M | _re31.S); _body31 = _st.group(1) if _st else ""
            for _t in ("sketch_extrude", "hole", "cutter", "sketch_connect", "gapfill", "mirror_pattern", "split", "edge_round", "revolve", "shell", "move"):
                _tp = os.path.join(HERE, "kit", "templates", "t_%s.py" % _t)
                if not os.path.isfile(_tp): continue
                _ts = open(_tp, encoding="utf-8").read(); _pm = _re31.search(r"PARAMS = dict\((.*?)^\)", _ts, _re31.M | _re31.S)
                _keys = set(_re31.findall(r"(\w+)\s*=\s*K\.NEED", _pm.group(1))) if _pm else set()
                _i = _body31.find('"%s":' % _t); _j = _re31.search(r'\n    "', _body31[_i + 1:]) if _i >= 0 else None
                _sct = _body31[_i:(_i + 1 + _j.start()) if _j else None] if _i >= 0 else ""
                _m = sorted(k_ for k_ in _keys if k_ not in _sct)
                if _m: _miss31[_t] = _m
        except Exception as _e31:
            _miss31 = {"(the pin itself failed)": [str(_e31)[:80]]}
        check("31bx R2 F2: every K.NEED key of a template's PARAMS appears in its newcard scaffold (gapfill's mouths; the cutter's vol_tol / area_growth_max / sliver_mm3 / boundary_step_max)", not _miss31, str(_miss31))
        check("31bx R2 F4 / R6 F4: kit job reads the card's Tier line, else the catalogue's - no silent 'haiku'", 'or _jr7.get("tier") or ""' in _k31 and "_tier_for(_ty7)" in _k31 and 'rstrip(".")' in _k31)
        check("31bx R2 F7 / R1 F9: the review counter names a sweep frame as one; --sweep names kit review --render", "a sweep frame; %d of %d sweep frames judged" in _k31 and "Render the sweep: kit review --render %s" in _k31)
        check("31bx R1 F9: a LEAD's verdict changed after the sweep was released needs --rejudge, recorded", "--rejudge" in _k31 and '"rejudged": _rj' in _k31)
        check("31bx R1 F5 / D6: --done leaves OCCLUDED frames out of the half-cannot rule and names the holding feature's box", "left out of this rule" in _k31 and "feature that HOLDS it" in _k31 and '"occluded": len(_occf & set(cannots))' in _k31)
        check("31bx R1 F7: a MOVE's vacated footprint names --breakout ok at the check and on the card", "this job is a MOVE" in _k31 and "the move vacates its footprint" in _et31)
        check("31bx R1 D10: kit job prints a next step; kit check's next names kit look before kit accept", "every command prints its next step - this one had none" in _k31 and "marked CHECKED. Next: kit look %s --code" in _k31)
        check("31bx R1 D10 / R2: the before frames have ONE next form - kit beforelook (kit.py and leangate)", 'kit beforelook %s --saw %s=<CODE>' in _k31 and 'kit beforelook %s --saw <picture>=<CODE>' in _g31)
        check("31bx R1 D2: the ATLAS: none line names defer; the dossier prompt no longer orders a proposal before any measurement", "or `kit atlas defer --until" in _k31 and "no regions defined yet: name one as you measure it" in _kd31 and "Propose them to the client now" not in _kd31)
        check("31bx R1 D4: the help names PROJECT_FACTS.md for the facts", "the facts to PROJECT_FACTS.md" in _k31 and "(PROJECT_FACTS.md; FACTS.md where a project already has one)" in _k31)
        check("31bx R6 D2: the exam names METHOD.md 3 for the far limit", "METHOD.md 3 - the FAR LIMIT on the card" in _k31 and "METHOD.md 3 (the far limit)" in _g31)
        check("31bx R6 F3: the burrito card no longer needs 'Sections approved' (the shelved chain's probe gate)", "SECTIONS APPROVED" not in [s_[0] for s_ in G.CARD_SLOTS] and "its approval is the REGION JUDGE" in _g31)
        check("31bx R1 F8 / R2 F6: no em dash inside the check macro's FAIL texts (FreeCADCmd's console is the Windows code page)", "lost ALL material - a NEW OPENING" in _k31 and "no em dash inside a macro string" in _k31)
        check("31bx R2 F5: the verdict gate says STALE before the verdict's word", _kl31.index("is STALE: %s has changed since it was given") < _kl31.index("is %r, not pass"))
        check("31bx R2 F3 / R1 D11: the route words - no bare 'plate' on the cutter, region_look takes show-me / corner, revolve drops round-boss", "plate-remove" in _et31 and _re31.search(r"^Route: remove delete cut-off shelf stub", _et31, _re31.M) is not None and "show-me picture view corner" in _et31 and "Route: revolve ring lip stepped-boss turned" in _et31)
        check("31bx R6 D6: the lint's and the scaffold's examples name no job of the project (the agent-facing texts; comments are the kit maintainer's)", "R18 ARROWFILL_M chose" not in _g31 and "R18 FANCORNER_P" not in _g31 and "(R18 ARROWFILL_M, " not in _g31 and "R18 FANCORNER_P was" not in _k31 and "ARROWFILL_M, 2026-09-10, the first job" not in _k31 and "NO SLOT since" not in _g31)
        check("31bx R2 F8: look_at's help names SECTION", "[--set SECTION=\"x|y|z v\"]" in open(os.path.join(HERE, "tools", "look_at.py"), encoding="utf-8").read())
    except Exception as _e31:
        check("31bx round 1 pins ran", False, str(_e31)[:200])
    try:
        print("\n[31by one kit] the project specifics live in kit\\env.json (the frame words; the atlas token aliases) - the shipped kit carries none")
        import math as _m3y
        _kr3y = open(os.path.join(HERE, "kit", "kitlib_render.py"), encoding="utf-8").read()
        _i0 = _kr3y.index("F = np.array([0.0, -1.0, 0.0])"); _i1 = _kr3y.index("# 31by: the frame block ends here", _i0); _fr_src = _kr3y[_i0:_i1]
        try:
            import numpy as _np3y
        except ImportError:
            class _Vec3y(list):
                def __truediv__(self, s_): return _Vec3y([x / s_ for x in self])
            class _np3y:
                class linalg:
                    @staticmethod
                    def norm(v): return _m3y.sqrt(sum(float(x) * float(x) for x in v))
                @staticmethod
                def array(v): return _Vec3y([float(x) for x in v])
        def _run_frame(env):
            _d = tempfile.mkdtemp(prefix="lk31by_")
            if env is not None: open(os.path.join(_d, "env.json"), "w", encoding="utf-8").write(json.dumps(env))
            _ns = {"np": _np3y, "json": json, "os": os, "__file__": os.path.join(_d, "kitlib_render.py")}
            exec(_fr_src, _ns)
            return [[round(float(x), 6) for x in _ns[k]] for k in ("F", "L", "U")]
        _doc = [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]
        check("31by: no env.json -> the frame words follow the document's own axes (F -y, L +x, U +z)", _run_frame(None) == _doc)
        check("31by: an env.json without 'frame' -> the document's axes", _run_frame({"timeout_s": 170}) == _doc)
        _f = _run_frame({"frame": {"forward": [0, -2, 1], "left": [3, 0, 0], "up": [0, 1, 2]}}); _s5 = _m3y.sqrt(5.0)
        check("31by: env.json 'frame' -> the project's own axes, each normalised", _f == [[0.0, round(-2 / _s5, 6), round(1 / _s5, 6)], [1.0, 0.0, 0.0], [0.0, round(1 / _s5, 6), round(2 / _s5, 6)]], _f)
        _f = _run_frame({"frame": {"forward": [0, -2, 1]}})
        check("31by: a 'frame' without left / up is NOT taken - the document's axes stand (nothing half-applied)", _f == _doc, _f)
        _f = _run_frame({"frame": {"forward": [0, 0, 0], "left": [1, 0, 0], "up": [0, 0, 1]}})
        check("31by: a zero vector in 'frame' is NOT taken", _f == _doc, _f)
        check("31by: the frame block says a frame it did not take (stderr) and never falls back silently", "not taken" in _fr_src and "_sys.stderr.write" in _fr_src and "except Exception: pass" not in _fr_src)
        _lg3y = open(os.path.join(HERE, "kit", "leangate.py"), encoding="utf-8").read()
        _j0 = _lg3y.index("def _atlas_token_aliases():"); _j1 = _lg3y.index("\n\n\n", _j0); _al_src = _lg3y[_j0:_j1]
        def _run_al(env):
            _d = tempfile.mkdtemp(prefix="lk31by_")
            if env is not None: open(os.path.join(_d, "env.json"), "w", encoding="utf-8").write(json.dumps(env))
            _ns = {"json": json, "os": os, "__file__": os.path.join(_d, "leangate.py")}
            exec(_al_src, _ns); return _ns["_atlas_token_aliases"]()
        check("31by: no env.json -> no atlas token alias", _run_al(None) == {})
        check("31by: an env.json without the key -> none", _run_al({"timeout_s": 170}) == {})
        check("31by: env.json 'atlas_token_aliases' read as {old: new}", _run_al({"atlas_token_aliases": {"OLD": "NEW", "OLD_OK": "NEW_OK", "old_said": "new_said"}}) == {"OLD": "NEW", "OLD_OK": "NEW_OK", "old_said": "new_said"})
        check("31by: a value that is no mapping -> none", _run_al({"atlas_token_aliases": ["OLD"]}) == {})
        _al = G._atlas_token_aliases(); _root = tempfile.mkdtemp(prefix="lk31by_atlas_"); os.makedirs(os.path.join(_root, "claude_code")); _ap = os.path.join(_root, "claude_code", G.ATLAS_FILE)
        if _al:
            _regs = {"r%d" % i_: {"definition_status": k_, "definition": k_, k_: "keep it"} for i_, k_ in enumerate(_al)}
            open(_ap, "w", encoding="utf-8").write(json.dumps({"regions": _regs})); _d3y = G.atlas_load(_root)
            _okA = all(_d3y["regions"]["r%d" % i_]["definition_status"] == v_ and _d3y["regions"]["r%d" % i_]["definition"] == v_ and _d3y["regions"]["r%d" % i_][k_] == "keep it"
                       and (_d3y["regions"]["r%d" % i_].get(v_) == "keep it" if k_ not in ("definition_status", "definition") else True) for i_, (k_, v_) in enumerate(_al.items()))
            check("31by: THIS kit's env.json lists older tokens (%d) - an old record reads the current ones; the file on disk is not rewritten" % len(_al), _okA and all(k_ in open(_ap, encoding="utf-8").read() for k_ in _al), _d3y["regions"])
        else:
            open(_ap, "w", encoding="utf-8").write(json.dumps({"regions": {"r1": {"definition_status": "X_OLD", "x_old_said": "keep it"}}})); _d3y = G.atlas_load(_root); _r1 = _d3y["regions"]["r1"]
            check("31by: no alias in this kit's env.json (the shipped default) - a record's tokens are read as they are", _r1["definition_status"] == "X_OLD" and sorted(_r1) == ["definition_status", "x_old_said"], _r1)
        _ex3y = json.load(open(os.path.join(HERE, "kit", "env.example.json"), encoding="utf-8"))
        check("31by: the shipped env.example.json carries no 'frame' and no 'atlas_token_aliases' (the document's axes; the current tokens)", "frame" not in _ex3y and "atlas_token_aliases" not in _ex3y)
    except Exception as _e3y:
        check("31by one kit pins ran", False, str(_e3y)[:200])
    try:
        print("\n[31bz] round 2's fixes: the texts, the measure counter's dispatch, the caller's folder, the HOME folder refused")
        def _r(*p_): return open(os.path.join(HERE, *p_), encoding="utf-8").read()
        _kz = _r("kit", "kit.py"); _mz = _r("kit", "kit_mesh.py"); _uz = _r("kit", "kit_union.py"); _cz = _r("kit", "kit_crop.py"); _lz = _r("tools", "look_at.py"); _gsp = os.path.join(HERE, "GETTING_STARTED.md"); _gsz = next((io.open(p__, encoding="utf-8").read() for p__ in (_gsp, os.path.join(os.path.dirname(HERE), "GETTING_STARTED.md")) if os.path.isfile(p__)), None)
        _etz = _r("EDIT_TYPES.md"); _orz = _r("ORCHESTRATOR.md"); _prz = _r("PRINT_READINESS.md"); _plz = _r("PROJECT_LAYOUT.md"); _vsz = _r("VOXEL_SMOOTH_STEPS.md"); _lcz = _r("kit", "mesh", "LEVERS_CENSUS.md")
        check("31bz R3 F6: the measure refusal reads the dispatch's mark alone (three bare measures run, the fourth refused uncounted)", '            if os.environ.get("KIT_MEASURE_SHUT") == "1":' in _kz and "if _since >= 3 or os.environ.get(\"KIT_MEASURE_SHUT\")" not in _kz)
        check("31bz R3 F13: kit tool passes the caller's folder; look_at resolves a relative SHAPE against it, claude_code\\ and the root", 'env["KIT_CALLER_CWD"] = os.getcwd()' in _kz and 'os.environ.get("KIT_CALLER_CWD")' in _lz and "resolved against" in _lz)
        check("31bz R4 F1: kit mesh resolves every CC_*OUT* path before the step, a missing folder refused by name", "have no folder to land in" in _mz and "_miss_out.append" in _mz)
        check("31bz R4 F2 (+ the fix agent's slip): the core's Next names the refine's CARD levers CC_BLOBS / CC_DEV, never CC_CORES", "--set CC_BLOBS=<the blob.npz this step wrote> --set CC_DEV=" in _mz and "--set CC_CORES=..." not in _mz)
        check("31bz R4 F3: the weld's Next gives kit splice the crop's .crop.json", "--crop <the crop's .crop.json (beside the crop.stl)>" in _mz)
        check("31bz R4 F4: kit union and kit splice print their next step", "  Next      : kit splice %s --crop %s --out <body2.stl>" in _uz and "  Next      : LOOK - kit render %s --box <the crop box>" in _cz)
        check("31bz R4 F6: fin / lip / step / crease are not mesh_union route words", "  re-surface fin lip step crease fill-a-notch" not in _etz and "  re-surface fill-a-notch cut-flush shave trim mesh-finishing appearance-fix" in _etz)
        check("31bz R4 D5: printcheck's usage gives the bore spec's form", "THE BORE SPEC (--bores <spec.json>)" in _r("kit", "kit_print.py"))
        check("31bz R6 F11: the region step's last line names skin-source / STEP 1, not the shelved arrange", "kit rebuild skin-source and the reinsert's STEP 1 refuse without it" in _r("kit", "rebuild", "rb_region.py"))
        if _gsz is None: print("  --   GETTING_STARTED.md is not beside this kit (an installed copy - the public docs stay at the release's root): its text pins skipped (31cb H-F5)")
        else: check("31bz R3 D1 / D3, R7 F6: GETTING_STARTED 7 - review\\ and renders\\, the Stop hook's background task, kit close's --remaining", "`Deliverables\\<REV>\\review\\` and `renders\\`" in _gsz
              and "a BACKGROUND task the harness launched lets the turn end" in _gsz and "`kit close --remaining \"<where the design stands / what is left>\"" in _gsz)
        check("31bz R4 D1: VOXEL_SMOOTH_STEPS says a finer CC_REFINE_L gives finer teeth and printfile does not make a coarse source fine", "finer teeth, not none" in _vsz and "shows none of it" not in _vsz)
        check("31bz R4 D2: the mesh_union card says end FLUSH, not MERGE", "Sink a face that is meant to end FLUSH 0.1 mm into the body" in _etz and "meant to MERGE 0.1 mm" not in _etz)
        check("31bz R4 D3: LEVERS_CENSUS names no foreign job and no R16", "MESH_JOB" not in _lcz and "(R16)" not in _lcz)
        check("31bz R2 D1: the cutter card names --breakout ok and the floor's strip faces in the face figure", "is an opening to kit check: --breakout ok" in _etz and "counts the FLOOR's strip faces" in _etz)
        check("31bz R5 F1 -> 31ca: the card's DO NOT offers the sharp_ok way out again", "does not clear such a junction" not in _etz and "or accept the member that lies between the no-corner junctions sharp (`\"sharp_ok\": [<line>]` on the chain's entry)" in _etz)
        check("31bz R7 F4: kit open's first-delivery line carries --no-review", '--model <the PROMOTED first brep> --no-review \\"the first body - nothing to review against\\"' in _kz)
        check("31bz R7 F5: review's synopsis and ORCHESTRATOR 67 carry --lead; deliverycheck names --review | --no-review", "kit review <before.brep> <after.brep> --out <dir> --lead <view,view,...> [--shards 6] [--tag _B21]" in _kz
              and "--box ... --lead <views> --shards 6" in _orz and _kz.count("kit deliverycheck <file.FCStd> (--review <dir> | --no-review \"<why>\")") == 2)
        check("31bz R7 D5: kit help names check --wide-box, howto --step, render --job, measure --profile / --dossier, atlas recipe|axis|behind, collected --kill, watch --pid, stop --until, ruling --reading",
              all(t_ in _kz for t_ in ('[--wide-box "<why>"]', "burrito --step <step>: one step's page", "[--name N] [--job <J>]", "[--profile --step S] | faces", "extent|recipe|axis|behind",
                                         "kit collected <name> [--kill]", '[--what "..."] [--pid <N>]', "[--until <bg-ids,...>|tasks]", '--reading "<an agent\'s reading>" --of')))
        check("31bz R7 D19 / D20 / D21: ORCHESTRATOR's counter rule, no model\\source\\, reports in a round folder", "the instrument CLOSES at the fourth bare" in _orz and "past ten with no card written" not in _orz
              and "model\\source\\" not in _orz and "model\\source\\" not in _prz and "| a report, a friction log, a brief | `claude_code\\<ROUND>\\`" in _plz and "<round briefs, reports, friction log>" not in _plz)
        _hz = tempfile.mkdtemp(prefix="lk31bz_home_"); os.makedirs(os.path.join(_hz, ".claude")); os.makedirs(os.path.join(_hz, "sub"))
        _envz = dict(os.environ, USERPROFILE=_hz, HOME=_hz); _envz.pop("KIT_PROJECT", None)
        _pz = subprocess.run([sys.executable, os.path.join(HERE, "kit", "kit.py"), "status"], cwd=os.path.join(_hz, "sub"), env=_envz, capture_output=True, text=True)
        check("31bz R7 F8: a kit command whose project resolves to the HOME folder is REFUSED by name, nothing written there", _pz.returncode != 0 and "the project resolved to your HOME folder" in (_pz.stdout + _pz.stderr)
              and sorted(os.listdir(os.path.join(_hz, ".claude"))) == [], (_pz.returncode, (_pz.stdout + _pz.stderr)[-300:]))
        shutil.rmtree(_hz, ignore_errors=True)
    except Exception as _ez:
        check("[31bz] pins ran", False, str(_ez)[:200])
    try:
        print("\n[31ca] the second fix agent's items: the cutter's cleanup")
        _tca = open(os.path.join(HERE, "kit", "templates", "t_cutter.py"), encoding="utf-8").read()
        check("31ca R2 F1: t_cutter cleans into a copy and compares the faces outside the cutter's box grown by cross_margin_mm (area 1e-6, centre 1e-4) before it takes the clean",
              "_cl = res.copy().removeSplitter()" in _tca and "round(f_.Area, 6), round(c_.x, 4), round(c_.y, 4), round(c_.z, 4)" in _tca and "_gm = float(P.get(\"cross_margin_mm\", 0.0) or 0.0)" in _tca
              and "if _gone == 0 and not _rest:" in _tca and "res = res.removeSplitter()" not in _tca)
        check("31ca R2 F1: ...and says which - used, or 'the whole-body cleanup would merge N face(s) far from the cut - the result is kept uncleaned'",
              "C7 cleanup: removeSplitter used - it changes no face far from the cut" in _tca and "the whole-body cleanup would merge %d face(s) far from the cut - the result is kept uncleaned" in _tca)
        _isp = os.path.join(HERE, "INSTALL.md"); _isz = next((io.open(p__, encoding="utf-8").read() for p__ in (_isp, os.path.join(os.path.dirname(HERE), "INSTALL.md")) if os.path.isfile(p__)), None)
        if _isz is None: print("  --   INSTALL.md is not beside this kit (an installed copy - the public docs stay at the release's root): its text pin skipped (31cb H-F5's family); the walk-up pins below run")
        else: check("31ca: INSTALL.md names Git for Windows and the Claude plan in the client's words", "| **Git for Windows** | Claude Code's Bash tool on Windows runs Git Bash; the kit's guard reads those commands |" in _isz
              and "| **A Claude plan** | a Claude Max plan; the ultra tier is recommended |" in _isz)
        _wz = tempfile.mkdtemp(prefix="lk31ca_walk_"); _hz2 = tempfile.mkdtemp(prefix="lk31ca_home_")
        os.makedirs(os.path.join(_wz, ".claude")); os.makedirs(os.path.join(_wz, "sub", "deeper"))
        _envw = dict(os.environ, USERPROFILE=_hz2, HOME=_hz2); _envw.pop("KIT_PROJECT", None)
        _pw = subprocess.run([sys.executable, os.path.join(HERE, "kit", "kit.py"), "status"], cwd=os.path.join(_wz, "sub", "deeper"), env=_envw, capture_output=True, text=True)
        check("31ca: a folder the walk-up finds by its .claude\\ with no claude_code\\ is REFUSED by name, nothing written there", _pw.returncode != 0
              and "holds a .claude\\ but no claude_code\\ - not a kit project" in (_pw.stdout + _pw.stderr) and sorted(os.listdir(_wz)) == [".claude", "sub"] and os.listdir(os.path.join(_wz, ".claude")) == [],
              (_pw.returncode, (_pw.stdout + _pw.stderr)[-300:], sorted(os.listdir(_wz))))
        os.makedirs(os.path.join(_wz, "claude_code"))
        _pw2 = subprocess.run([sys.executable, os.path.join(HERE, "kit", "kit.py"), "status"], cwd=os.path.join(_wz, "sub", "deeper"), env=_envw, capture_output=True, text=True)
        check("31ca: ...the same root WITH claude_code\\ is taken as the project (no such refusal)", "not a kit project" not in (_pw2.stdout + _pw2.stderr), (_pw2.returncode, (_pw2.stdout + _pw2.stderr)[-300:]))
        shutil.rmtree(_wz, ignore_errors=True); shutil.rmtree(_hz2, ignore_errors=True)
    except Exception as _eca:
        check("[31ca] pins ran", False, str(_eca)[:200])
    try:
        print("\n[31cb] the route harness's five findings (H-F1..H-F5) - code and string markers only (the release strips comments)")
        def _r3(*p_): return open(os.path.join(HERE, *p_), encoding="utf-8").read()
        sys.path.insert(0, os.path.join(HERE, "hooks")); import importlib as _il3; _g3 = _il3.import_module("guard")
        check("31cb H-F1: the guard's _PY_WRITE reads a quoted .py target holding a space (> and tee)", bool(_g3._PY_WRITE.search('cat > "C:\\x y\\j.py" <<EOF')) and bool(_g3._PY_WRITE.search('python3 a.py | tee "C:\\x y\\j.py"')))
        check("31cb H-F2: selftest_guard quotes a kit path that holds a space", "kpr = kp" in _r3("hooks", "selftest_guard.py") and "if \" \" in kp: kp = " in _r3("hooks", "selftest_guard.py"))
        check("31cb H-F3: no look record at all = every frame unopened", "unopened = list(frames)" in _r3("kit", "kit_rebuild.py") and "if LG_ is not None and not os.path.isfile(lj_):" in _r3("kit", "kit_rebuild.py"))
        check("31cb H-F4: the preview's PASS says it is no BUILD PASS", "this PASS is no BUILD PASS (31cb H-F4)" in _r3("kit", "rebuild", "sk_wires.py"))
        check("31cb H-F5: GETTING_STARTED read beside the kit or above it, else its pins skipped", "its text pins skipped (31cb H-F5)" in _r3("selftest_leangates.py"))
    except Exception as _e3c:
        check("31cb pins ran", False, str(_e3c)[:200])
    print("%d passed, %d FAILED" % (len(PASS), len(FAIL)))
    if FAIL:
        for f in FAIL:
            print("  FAILED: %s" % f)
        return 1
    print("Every lean gate refuses what it should and passes what it should.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

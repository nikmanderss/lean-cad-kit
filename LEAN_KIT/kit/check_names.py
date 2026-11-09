# kit rebuild
import ast, builtins, os, re, sys, symtable

KIT = os.path.dirname(os.path.abspath(__file__))
_PLATFORM = {"signal", "socket", "select", "subprocess", "errno", "msvcrt", "winreg", "ctypes", "posix", "nt", "resource", "fcntl", "termios", "pwd", "grp"}
_PLATFORM_ONLY = {"os": {"getpgid", "killpg", "setsid", "setpgrp", "setpgid", "getpgrp", "fork", "forkpty", "getuid", "geteuid", "getgid", "getegid", "getppid", "setuid", "setgid", "uname",
                         "getloadavg", "sysconf", "statvfs", "fstatvfs", "chown", "lchown", "fchown", "wait3", "wait4", "WNOHANG", "WIFEXITED", "WEXITSTATUS", "nice", "sync", "mkfifo", "pipe2",
                         "sched_getaffinity", "posix_spawn", "startfile", "O_BINARY", "add_dll_directory", "get_handle_inheritable", "set_handle_inheritable", "getlogin"},
                  "time": {"tzset", "clock_gettime", "clock_settime", "pthread_getcpuclockid", "clock_gettime_ns"},
                  "sys": {"getwindowsversion", "winver", "dllhandle", "setdlopenflags", "getdlopenflags", "abiflags", "getandroidapilevel"}}
_FUTURE_ANN = [False]
BUILTINS = set(dir(builtins)) | {"__file__", "__name__", "__builtins__", "__doc__", "__spec__", "__loader__", "__package__", "__path__", "__cached__", "__annotations__"}


def _module_bound(top):
    return {s.get_name() for s in top.get_symbols() if s.is_assigned() or s.is_imported() or s.is_parameter() or s.is_namespace()}


def _walk(tb, out, mod_bound, path):
    for s in tb.get_symbols():
        n = s.get_name()
        if not s.is_referenced(): continue
        if tb.get_type() == "module":
            if not (s.is_assigned() or s.is_imported() or s.is_namespace()) and n not in BUILTINS and n not in mod_bound: out.append((tb.get_lineno(), n, "used at module level, bound nowhere"))
        elif s.is_global() and not s.is_declared_global() and not (s.is_assigned() or s.is_imported() or s.is_parameter() or s.is_namespace()):
            if n not in mod_bound and n not in BUILTINS: out.append((tb.get_lineno(), n, "used in %s '%s', bound in no enclosing scope, the module or builtins" % (tb.get_type(), tb.get_name())))
        elif s.is_declared_global() and n not in mod_bound and n not in BUILTINS and not s.is_assigned():
            out.append((tb.get_lineno(), n, "declared global in '%s' and read, never bound at module level" % tb.get_name()))
    for ch in tb.get_children(): _walk(ch, out, mod_bound, path)


_COMPS = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


def _comp_locals(c):
    """31bq R7e; R7W tester-findings (T5's N2, y01): the names comprehension NODE `c` binds for itself - its generators' targets, local to that node (its element,
    its conditions, its later generators and the comprehensions nested in them), never to the rest of the statement and never a module bind"""
    return {t_.id for g_ in c.generators for t_ in ast.walk(g_.target) if isinstance(t_, ast.Name)}


def _comp_walrus(c):
    """R7W fix-small (F.7 b): the targets an assignment expression inside comprehension `c` binds - PEP 572: in the scope that CONTAINS the comprehension, through
    every comprehension nested in it, never through a def / lambda / class it holds (cases_f7 b2 nested, b7 a lambda's own)"""
    out = set(); stack = list(ast.iter_child_nodes(c))
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)): continue
        if isinstance(n, ast.NamedExpr) and isinstance(n.target, ast.Name): out.add(n.target.id)
        stack.extend(ast.iter_child_nodes(n))
    return out


def _iter_comps(st):
    """R7W fix-small (F.7 b): the comprehensions of statement `st` at its own level - not inside a def / lambda / class, not nested in another comprehension (its
    walrus targets are the outer one's - _comp_walrus reaches them)"""
    stack = [st]
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)): continue
        if isinstance(n, _COMPS): yield n; continue
        stack.extend(ast.iter_child_nodes(n))


def _stored_gens(st):
    """R7W fix-small (F.7 a): the generator expressions of statement `st` stored WHOLE in plain names (`g = (... for ...)`, `g = h = ...`, `g: T = ...`) -
    {id(genexp): its names}; never one inside a def / lambda / class / comprehension (_iter_binds' walk: those run elsewhere or are consumed where they stand)"""
    out = {}
    for n in ([st] if isinstance(st, (ast.Assign, ast.AnnAssign)) else []):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.GeneratorExp) and n.targets and all(isinstance(t_, ast.Name) for t_ in n.targets):
            out[id(n.value)] = [t_.id for t_ in n.targets]
        elif isinstance(n, ast.AnnAssign) and isinstance(n.value, ast.GeneratorExp) and isinstance(n.target, ast.Name):
            out[id(n.value)] = [n.target.id]
    return out


class _Order(ast.NodeVisitor):
    """module-level statements in order: a name LOADED by a module-level statement (outside any def / lambda / class body) before any module-level binding of it"""
    def __init__(self, later, fglob=None, uncond=None):
        self.bound = set(); self.later = later; self.hits = []
        self.fglob = fglob or {}; self.uncond = uncond or {}; self.uncertain = []; self.gen_hits = []; self.stored = {}; self.gens = {}; self._defer = None; self._st = None
    def run(self, tree):
        for st in tree.body:
            self._st = st
            self._consume(st)
            self.stored = _stored_gens(st)
            self._loads(st)
            b_ = _binds(st)
            for n in b_: self.bound.add(n)
            if isinstance(st, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete, ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for g_ in [g_ for g_, e_ in self.gens.items() if g_ in b_ and e_["st"] is not st]: del self.gens[g_]
    def _consume(self, st):
        """R7W fix-small (F.7 a): a stored generator expression runs its element, conditions and later generators when it is CONSUMED - at the first module-level
        statement that reads its name, or calls (on the statement's own straight line) a module-level function reading it; its deferred loads are judged against the
        names bound by then - a NAME, or UNCERTAIN when that function reads it only under an if / try branch (R7e's rule; the generator then stays live for a later
        consumer). Its walrus targets bind when it runs. A read that does not consume it (an alias, a print of the object) is taken as consumption - the alarm side."""
        if not self.gens: return
        reads = {}; calls = []
        for node in _iter_toplevel(st):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load): reads.setdefault(node.id, node.lineno)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in self.fglob and self.later.get(node.func.id, 10 ** 9) <= node.lineno: calls.append(node)
        calls.sort(key=lambda c_: (c_.lineno, c_.col_offset))
        for e_ in list({id(v_): v_ for v_ in self.gens.values()}.values()):
            how = None
            for g_ in e_["names"]:
                if self.gens.get(g_) is not e_: continue
                if g_ in reads: how = (reads[g_], g_, None, True); break
                for c_ in calls:
                    if g_ in self.fglob.get(c_.func.id, ()): how = (c_.lineno, g_, c_.func.id, g_ in self.uncond.get(c_.func.id, set())); break
                if how: break
            if not how: continue
            ln_, g_, via_, sure_ = how
            for lno_, nm_ in e_["loads"]:
                if nm_ in self.bound or nm_ in BUILTINS: continue
                w_ = "read by the generator expression stored in %s on line %d, which runs when it is consumed%s on line %d - before %s's module-level binding (line %d)" % (
                    g_, e_["line"], (" by %s()" % via_) if via_ else "", ln_, nm_, self.later.get(nm_, 0))
                if sure_: self.hits.append((ln_, nm_, w_)); self.gen_hits.append((ln_, nm_, w_))
                else: self.uncertain.append((ln_, nm_, w_ + " - %s() reads %s under an if / try branch (UNCERTAIN: that branch may not run on this call; waive it on the call's line with `# check_names: %s later on purpose`)" % (via_, g_, nm_)))
            if sure_:
                self.bound |= e_["walrus"]
                for g2_ in [k_ for k_, v_ in self.gens.items() if v_ is e_]: del self.gens[g2_]
    def _loads(self, st):
        self._visit(st, frozenset(), frozenset())
    def _visit(self, n, cls_bound, _cl):
        """31bq R7e (3): the loads a statement makes at module level NOW, in source order - a def's / lambda's body runs later (its decorators and defaults now); a CLASS
        BODY runs now and its own EARLIER binds resolve its loads (T5's y10: `class C: X = 1; Y = X + 1` with a module X bound later had read as a false NAME since R7e
        made class binds non-module); a class body reading a name it binds later in the body, or never, stays a NAME (it runs to NameError)"""
        if isinstance(n, (ast.Assign, ast.AnnAssign)) and self._defer is None and n.value is not None and id(n.value) in self.stored:
            for t_ in (list(n.targets) if isinstance(n, ast.Assign) else [n.target] + ([] if _FUTURE_ANN[0] else [n.annotation])): self._visit(t_, cls_bound, _cl)
            ge_ = n.value; g0 = ge_.generators[0]
            self._visit(g0.iter, cls_bound, _cl)
            self._defer = []; inner = frozenset(_cl) | _comp_locals(ge_)
            try:
                for t_ in [g0.target] + list(g0.ifs): self._visit(t_, frozenset(), inner)
                for g_ in ge_.generators[1:]:
                    for t_ in [g_.target, g_.iter] + list(g_.ifs): self._visit(t_, frozenset(), inner)
                self._visit(ge_.elt, frozenset(), inner)
                e_ = {"names": list(self.stored[id(ge_)]), "line": n.lineno, "loads": list(self._defer), "walrus": _comp_walrus(ge_), "st": self._st}
            finally:
                self._defer = None
            for g_ in e_["names"]: self.gens[g_] = e_
            return
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in list(n.decorator_list) + list(n.args.defaults) + [d for d in n.args.kw_defaults if d is not None]: self._visit(d, cls_bound, _cl)
            return
        if isinstance(n, ast.Lambda):
            for d in n.args.defaults: self._visit(d, cls_bound, _cl)
            return
        if isinstance(n, ast.ClassDef):
            for d in list(n.decorator_list) + list(n.bases) + [k.value for k in n.keywords]: self._visit(d, cls_bound, _cl)
            local = set(cls_bound)
            for s_ in n.body:
                self._visit(s_, frozenset(local), _cl); local |= _binds(s_)
            return
        if isinstance(n, ast.AnnAssign) and _FUTURE_ANN[0]:
            self._visit(n.target, cls_bound, _cl)
            if n.value is not None: self._visit(n.value, cls_bound, _cl)
            return
        if isinstance(n, _COMPS):
            g0 = n.generators[0]
            self._visit(g0.iter, cls_bound, _cl)
            inner = frozenset(_cl) | _comp_locals(n)
            for t_ in [g0.target] + list(g0.ifs): self._visit(t_, frozenset(), inner)
            for g_ in n.generators[1:]:
                for t_ in [g_.target, g_.iter] + list(g_.ifs): self._visit(t_, frozenset(), inner)
            for e_ in ([n.key, n.value] if isinstance(n, ast.DictComp) else [n.elt]): self._visit(e_, frozenset(), inner)
            return
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            if n.id in self.later and n.id not in self.bound and n.id not in BUILTINS and n.id not in _cl and n.id not in cls_bound:
                if self._defer is not None: self._defer.append((n.lineno, n.id))
                else: self.hits.append((n.lineno, n.id, "used at module level before its module-level binding (line %d)" % self.later[n.id]))
            return
        for c_ in ast.iter_child_nodes(n): self._visit(c_, cls_bound, _cl)


def _iter_toplevel(st):
    """the nodes of a statement executed at module level now - not the bodies of defs / lambdas / classes / comprehensions' own scopes (their loads run later)"""
    stack = [st]
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stack.extend(n.decorator_list); stack.extend(d for d in n.args.defaults); stack.extend(d for d in n.args.kw_defaults if d is not None); continue
        if isinstance(n, ast.Lambda):
            stack.extend(d for d in n.args.defaults); continue
        if isinstance(n, ast.ClassDef):
            stack.extend(n.decorator_list); stack.extend(n.bases); stack.extend(n.body); continue
        if isinstance(n, ast.AnnAssign) and _FUTURE_ANN[0]:
            yield n; stack.append(n.target); stack.extend([n.value] if n.value is not None else []); continue
        yield n
        stack.extend(ast.iter_child_nodes(n))


def _iter_binds(st):
    """31bq R7e: the nodes whose Store targets BIND at module level - like _iter_toplevel, but a class body (its own namespace) and a comprehension (its own scope) are
    not descended: `class C: X = 1` binds no module X (b13), `[n for n in ...]` binds no module n (b14)"""
    stack = [st]
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)): continue
        yield n
        stack.extend(ast.iter_child_nodes(n))


def _binds(st):
    out = set()
    for n in _iter_binds(st):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)): out.add(n.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names: out.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, ast.ExceptHandler) and n.name: out.add(n.name)
    for n in ast.walk(st):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and _is_module_level(st, n): out.add(n.name)
    _sg = _stored_gens(st)
    for c_ in _iter_comps(st):
        if id(c_) not in _sg: out |= _comp_walrus(c_)
    return out


def _is_module_level(st, target):
    """target is a def/class reachable from st without passing through another def/class/lambda"""
    stack = [st]
    while stack:
        n = stack.pop()
        if n is target: return True
        if n is not st and isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)): continue
        stack.extend(ast.iter_child_nodes(n))
    return False


def _callee_reads(top, tree):
    """31bq PP / R5h / R7e - moved out of check() by R7W fix-small (F.7 a), its code unchanged: per module-level function, the globals it reads (the symbol table's)
    and those it reads on its STRAIGHT line (a for / while / with body runs; an if / try branch may not). ({}, {}) when they cannot be read - the call rule and a stored
    generator's call consumer then find nothing (as the try round the whole call rule did)"""
    try:
        _fglob = {}
        for ch in top.get_children():
            if ch.get_type() == "function":
                _fglob.setdefault(ch.get_name(), set()).update(s.get_name() for s in ch.get_symbols() if s.is_global() and s.is_referenced() and not s.is_assigned())
        _uncond = {}
        def _loads_of(x_, acc_):
            if isinstance(x_, ast.Lambda): return
            if isinstance(x_, ast.Name) and isinstance(x_.ctx, ast.Load): acc_.add(x_.id)
            for c_ in ast.iter_child_nodes(x_): _loads_of(c_, acc_)
        def _straight(body_, acc_):
            for s_ in body_:
                if isinstance(s_, ast.If): _loads_of(s_.test, acc_); continue
                if isinstance(s_, ast.While): _loads_of(s_.test, acc_); _straight(s_.body, acc_); continue
                if isinstance(s_, (ast.For, ast.AsyncFor)): _loads_of(s_.iter, acc_); _straight(s_.body, acc_); continue
                if isinstance(s_, (ast.With, ast.AsyncWith)):
                    for it_ in s_.items: _loads_of(it_.context_expr, acc_)
                    _straight(s_.body, acc_); continue
                if isinstance(s_, (ast.Try, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) or type(s_).__name__ in ("Match", "TryStar"): continue
                _loads_of(s_, acc_)
        for st in tree.body:
            for fn_ in ast.walk(st):
                if isinstance(fn_, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_module_level(st, fn_): _straight(fn_.body, _uncond.setdefault(fn_.name, set()))
        return _fglob, _uncond
    except Exception:
        return {}, {}


def check(path):
    src = open(path, encoding="utf-8", errors="replace").read()
    try:
        top = symtable.symtable(src, path, "exec"); tree = ast.parse(src, path)
    except SyntaxError as ex:
        return [(ex.lineno or 0, "-", "SyntaxError: %s" % ex.msg)], []
    mod_bound = _module_bound(top); out = []; _FUTURE_ANN[0] = any(isinstance(st, ast.ImportFrom) and st.module == "__future__" and any(a.name == "annotations" for a in st.names) for st in tree.body)
    import re as _re
    for _sib in _re.findall(r'"(\w+\.py)"\)\)\.read\(\)', src):
        _sp = os.path.join(os.path.dirname(os.path.abspath(path)), _sib)
        if "exec(" in src and os.path.isfile(_sp):
            try: mod_bound |= _module_bound(symtable.symtable(open(_sp, encoding="utf-8", errors="replace").read(), _sp, "exec"))
            except SyntaxError: pass
    for st_ in tree.body:
        for c_ in _iter_comps(st_): mod_bound |= _comp_walrus(c_)
    _dyn = []
    for n_ in ast.walk(tree):
        if isinstance(n_, ast.ImportFrom) and any(a_.name == "*" for a_ in n_.names): _dyn.append("import *")
        elif isinstance(n_, ast.Call) and isinstance(n_.func, ast.Name) and n_.func.id == "exec" and not _re.findall(r'"(\w+\.py)"\)\)\.read\(\)', src): _dyn.append("exec()")
        elif isinstance(n_, ast.Subscript) and isinstance(n_.value, ast.Call) and isinstance(n_.value.func, ast.Name) and n_.value.func.id == "globals":
            if isinstance(n_.slice, ast.Constant) and isinstance(n_.slice.value, str):
                if isinstance(n_.ctx, ast.Store): mod_bound.add(n_.slice.value)      # KeyError
            elif isinstance(n_.ctx, ast.Store): _dyn.append("globals()[<computed>] = ...")
    _walk(top, out, mod_bound, path)
    uncertain = []
    if _dyn and out:
        uncertain = [(l, n, w + " (UNCERTAIN: the module uses %s)" % ", ".join(sorted(set(_dyn)))) for l, n, w in out]; out = []
    first = {}
    for st in tree.body:
        for n in _binds(st): first.setdefault(n, st.lineno)
    _fglob, _uncond = _callee_reads(top, tree)
    od = _Order(first, _fglob, _uncond); od.run(tree); uncertain_calls = [u_ for u_ in od.uncertain if first.get(u_[1], 0) > u_[0]]
    out += [h for h in od.hits if first.get(h[1], 0) > h[0] or (h in od.gen_hits and first.get(h[1], 0) >= h[0])]
    try:
        for st in tree.body:
            for node in _iter_toplevel(st):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _fglob and first.get(node.func.id, 10**9) <= node.lineno:
                    for g_ in sorted(_fglob[node.func.id]):
                        if first.get(g_, 0) > node.lineno and g_ not in BUILTINS:
                            _w = "read by %s(), which is called at module level on line %d before %s's module-level binding (line %d)" % (node.func.id, node.lineno, g_, first[g_])
                            if g_ in _uncond.get(node.func.id, set()): out.append((node.lineno, g_, _w))
                            else: uncertain_calls.append((node.lineno, g_, _w + " - the read sits under an if / try branch in %s() (UNCERTAIN: that branch may not run on this call; waive it on the call's line with `# check_names: %s later on purpose`)" % (node.func.id, g_)))
    except Exception: pass
    try:
        import importlib as _il
        _mods = {}
        for st in tree.body:
            for n in ast.walk(st):
                if isinstance(n, ast.Import):
                    for a in n.names:
                        root = a.name.split(".")[0]
                        if root in getattr(sys, "stdlib_module_names", ()) and "." not in a.name and root not in _PLATFORM: _mods[a.asname or a.name] = a.name
        _rebound = {x.id for x in ast.walk(tree) if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del))} | {x.arg for x in ast.walk(tree) if isinstance(x, ast.arg)}
        _mods = {k: v for k, v in _mods.items() if k not in _rebound}
        _cache = {}
        for n in ast.walk(tree):
            if isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Load) and isinstance(n.value, ast.Name) and n.value.id in _mods:
                mn = _mods[n.value.id]
                if mn not in _cache:
                    try: _cache[mn] = _il.import_module(mn)
                    except Exception: _cache[mn] = None
                if _cache[mn] is not None and not hasattr(_cache[mn], n.attr) and n.attr not in _PLATFORM_ONLY.get(mn, ()):
                    try: _il.import_module("%s.%s" % (mn, n.attr)); continue
                    except Exception: pass
                    out.append((n.lineno, "%s.%s" % (n.value.id, n.attr), "the stdlib module %s has no attribute %s" % (mn, n.attr)))
    except Exception: pass
    loads = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load): loads.setdefault(n.id, n.lineno)
    out = sorted({(loads.get(nm, ln) if "before its module-level binding" not in why else ln, nm, why) for ln, nm, why in out})
    return out, uncertain + sorted(set(uncertain_calls))


def _rel(f):
    try: return os.path.relpath(f, os.path.dirname(KIT))
    except ValueError: return f


_WAIVE_RE = re.compile(r"#\s*check_names:\s*(?P<names>[A-Za-z_][\w, ]*?)\s+later on purpose\b")


def _waived(line, nm):
    """31bq R7e (3): the call's line waives the global by its WHOLE name in the sentence `# check_names: <name>[, <name>] later on purpose` - T5's w5 (a waiver of HANDLER
    had waived H by a substring test) and w9 (a bare `# check_names: HANDLER` had waived)"""
    m = _WAIVE_RE.search(line)
    if not m: return False
    return nm in {x.strip() for x in m.group("names").replace(",", " ").split() if x.strip()}


def main(argv):
    targets = argv[1:] or [os.path.dirname(KIT)]
    files = []
    for t in targets:
        if os.path.isdir(t):
            for _root, _dirs, _fns in os.walk(t):
                _dirs[:] = sorted(d_ for d_ in _dirs if d_ not in ("__pycache__", "proto"))
                files += sorted(os.path.join(_root, f) for f in _fns if f.endswith(".py"))
        elif t.endswith(".py") and os.path.isfile(t): files.append(t)
    bad = 0; unc = 0; waived = 0
    missing = [t for t in targets if not (os.path.isdir(t) or (t.endswith(".py") and os.path.isfile(t)))]
    for m in missing: print("NAME %s - %s (nothing checked there)" % (m, "not a .py file" if os.path.isfile(m) else "no such .py file or folder")); bad += 1
    if not files and not missing: print("NAME - no .py file found in %s" % targets); bad += 1
    for f in files:
        hits, uncertain = check(f)
        for ln, nm, why in hits: print("NAME %s:%d  %s - %s" % (_rel(f), ln, nm, why)); bad += 1
        try: _lines = open(f, encoding="utf-8", errors="replace").read().splitlines()
        except OSError: _lines = []
        for ln, nm, why in uncertain:
            _ln_txt = _lines[ln - 1] if 0 < ln <= len(_lines) else ""
            if _waived(_ln_txt, nm): print("WAIVED %s:%d  %s - %s" % (_rel(f), ln, nm, why)); waived += 1
            else: print("UNCERTAIN %s:%d  %s - %s" % (_rel(f), ln, nm, why)); unc += 1
    print("check_names: %d file(s), %d name(s) bound nowhere or used before their binding, %d uncertain%s" % (len(files), bad, unc, (", %d waived" % waived) if waived else ""))
    return 1 if (bad or unc) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

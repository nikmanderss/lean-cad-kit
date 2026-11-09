# -*- coding: utf-8 -*-
r"""selftest_print.py - kit printcheck / kit printfile, the parts that need no kernel (numpy only).

The pipeline scripts under kit\print\ run under freecadcmd (VTK, Mesh); their pure functions - the loop walk, the
minimum-area fill, the flap rule, the size and rules logic - are lifted out of the scripts by their `def` blocks and
tested here on shapes whose answer is arithmetic. Run: python selftest_print.py
"""
import os, sys, ast, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("KIT_HOME", HERE)
import kit_print as KP
import kitlib_render as R

fails = []


def check(name, ok, detail=""):
    print(("  ok    " if ok else "  FAIL  ") + name + ((" - " + detail) if detail and not ok else ""))
    if not ok:
        fails.append(name)


def lift(script, names):
    """the named top-level functions of a pipeline script, executed into a namespace with numpy and the renderer."""
    src = open(os.path.join(HERE, "print", script), encoding="utf-8").read()
    tree = ast.parse(src)
    ns = {"np": np, "R": R, "os": os, "sys": sys, "math": __import__("math"), "struct": __import__("struct")}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            exec(compile(ast.Module(body=[node], type_ignores=[]), script, "exec"), ns)
    return ns


print("1. rules and verdict helpers")
d = json.load(open(KP.RULES_FILE, encoding="utf-8"))
for name in ("jlc_mjf_pa12", "jlc_9000he"):
    r = KP.rules_load(name)
    need = ("build_mm", "wall_min_mm", "auto_check_wall_mm", "thinnest_min_mm", "file_max_mb", "read", "process", "material", "supports")
    check("rules %s carry every field the check reads" % name, all(k in r for k in need), str([k for k in need if k not in r]))
try:
    KP.rules_load("no_such_shop"); check("unknown rules refused", False)
except SystemExit:
    check("unknown rules refused", True)
check("a 341 x 265 x 169 part fits 370 x 276 x 360 by rotation", KP._fits([341, 265, 169], [370, 276, 360]))
check("a 341 x 265 x 169 part fits 580 x 580 x 380", KP._fits([341, 265, 169], [580, 580, 380]))
check("a 400 x 100 x 100 part does not fit 370 x 276 x 360", not KP._fits([400, 100, 100], [370, 276, 360]))
check("a 300 x 300 x 100 part is turned to fit 370 x 276 x 360", KP._fits([300, 300, 100], [370, 276, 360]))


class _FakeG:
    def atlas_regions(self, root):
        return {"big": {"box": [-100, 100, -100, 100, -100, 100]}, "small": {"box": [0, 10, 0, 10, 0, 10]}}


class _FakeKit:
    G = _FakeG(); ROOT = "."
check("the smallest region holding the point is named", KP._region_of(_FakeKit(), [5, 5, 5]) == "small")
check("a point in the big region only", KP._region_of(_FakeKit(), [50, 50, 50]) == "big")
check("a point outside every region is None", KP._region_of(_FakeKit(), [500, 0, 0]) is None)

print("2. the loop walk and the fill (lifted from _pf_c.py)")
C = lift("_pf_c.py", ("boundary_loops", "min_area_triangulation", "fill_loop", "edge_counts"))
V = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]], float)
T = np.array([[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5], [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]])
ue, inv, c = C["edge_counts"](T)
check("the cube is closed", int((c == 1).sum()) == 0 and int((c > 2).sum()) == 0)
loops, nj, nje = C["boundary_loops"](T)
check("a closed mesh has no loops", loops == [] and nj == 0)
T1 = T[1:]
loops, nj, nje = C["boundary_loops"](T1)
check("one missing triangle: one loop of three", len(loops) == 1 and len(loops[0]) == 3, str(loops))
cap = C["fill_loop"](V, loops[0])
check("its cap is one triangle", len(cap) == 1)
T2 = np.vstack([T1, cap]); ue, inv, c = C["edge_counts"](T2)
check("the cap closes it, manifold", int((c == 1).sum()) == 0 and int((c > 2).sum()) == 0)
vol = float(np.einsum("ij,ij->i", V[T2][:, 0], np.cross(V[T2][:, 1], V[T2][:, 2])).sum() / 6.0)
check("and winds the right way (volume +1)", abs(vol - 1.0) < 1e-9, "%.3f" % vol)
T3 = T[2:]
loops, nj, nje = C["boundary_loops"](T3)
check("a missing face: one loop of four", len(loops) == 1 and len(loops[0]) == 4, str(loops))
cap = C["fill_loop"](V, loops[0])
T4 = np.vstack([T3, cap]); ue, inv, c = C["edge_counts"](T4)
vol = float(np.einsum("ij,ij->i", V[T4][:, 0], np.cross(V[T4][:, 1], V[T4][:, 2])).sum() / 6.0)
check("two cap triangles close it with volume +1", len(cap) == 2 and int((c == 1).sum()) == 0 and abs(vol - 1.0) < 1e-9)
th = np.linspace(0, np.pi / 2, 20)
side_a = np.column_stack([np.cos(th) * 30, np.sin(th) * 30, np.zeros(20)])
side_b = np.column_stack([np.cos(th) * 30, np.sin(th) * 30, np.full(20, 0.2)])[::-1]
P = np.vstack([side_a, side_b])
tris = C["min_area_triangulation"](P)
check("a bent 40-point ribbon: 38 triangles", len(tris) == 38, str(len(tris)))
tot = sum(0.5 * np.linalg.norm(np.cross(P[b] - P[a], P[c] - P[a])) for a, b, c in tris)
check("their area is the ribbon's (0.2 x the arc length, within 2 %)", abs(tot - 0.2 * 30 * np.pi / 2) < 0.02 * 0.2 * 30 * np.pi / 2, "%.3f" % tot)
Vl = P
Tstrip = np.array([t for i in range(0, 19) for t in ([i, i + 1, 39 - i], [i + 1, 38 - i, 39 - i])])   # over the
loops_strip, _, _ = C["boundary_loops"](Tstrip)
check("the strip's boundary is one loop of 40", len(loops_strip) == 1 and len(loops_strip[0]) == 40, str([len(l) for l in loops_strip]))
cap = C["fill_loop"](Vl, loops_strip[0]) if loops_strip else []
check("fill_loop returns m - 2 triangles for the ribbon", len(cap) == 38, str(len(cap)))
if len(cap):
    Tboth = np.vstack([Tstrip, cap]); ue, inv, c = C["edge_counts"](Tboth)
    check("strip + cap is a closed (two-sided) sheet: 0 open edges", int((c == 1).sum()) == 0)
    vol = float(np.einsum("ij,ij->i", Vl[Tboth][:, 0], np.cross(Vl[Tboth][:, 1], Vl[Tboth][:, 2])).sum() / 6.0)
    check("and encloses no volume (the cap winds against the strip)", abs(vol) < 1e-6, "%.4f" % vol)
Tj = np.array([[0, 1, 2], [0, 3, 4]])                                # open edges
Vj = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [-1, 0, 0], [-1, -1, 0]], float)
loops, nj, nje = C["boundary_loops"](Tj)
check("a bow-tie vertex is a junction, its loops are not walked", nj == 1 and loops == [], "loops %s nj %d" % (loops, nj))

print("3. the film rule (lifted from _pf_a.py): a thin fin is not a film, a slit is")
def facing(n_i, n_j, d, film=0.35):
    """the one test _pf_a.py applies at the first face a ray meets: it faces back (parallel) and lies within film"""
    return float(n_j @ n_i) < -0.9 and 0.005 < d < film
check("a slit's walls: film", facing(np.array([0, 0, 1.0]), np.array([0, 0, -1.0]), 0.2))
check("a fin's faces look away from each other: the ray meets nothing at 0.2", not facing(np.array([0, 0, 1.0]), np.array([0, 0, 1.0]), 0.2))
check("a V-groove wall at 60 deg is not parallel: not a film", not facing(np.array([0, 0, 1.0]), np.array([0, np.sin(np.radians(60)), -np.cos(np.radians(60))]), 0.2))
check("a coincident double sheet (0 mm) is not reached", not facing(np.array([0, 0, 1.0]), np.array([0, 0, -1.0]), 0.0))

print()
if fails:
    print("FAILED: %d - %s" % (len(fails), ", ".join(fails))); sys.exit(1)
print("selftest_print: all green")

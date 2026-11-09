import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kitlib_render
import numpy as np

FAILED = []


def check(label, cond, detail=""):
    print("  %-4s %s" % ("ok" if cond else "FAIL", label))
    if not cond:
        print("       %s" % str(detail)[:400]); FAILED.append(label)


print("\nBLAS - one thread, and the product at 3 M rows is right\n")
check("OPENBLAS_NUM_THREADS is pinned to 1 by the kit's modules", os.environ.get("OPENBLAS_NUM_THREADS") == "1", os.environ.get("OPENBLAS_NUM_THREADS"))
rng = np.random.default_rng(7)
N = 3_000_000
A = rng.uniform(-300, 300, (N, 3))
B = rng.uniform(-1, 1, (3, 2))
P1 = A @ B
P2 = A @ B
E = np.einsum("ij,jk->ik", A, B)
G = np.stack([A @ B[:, 0], A @ B[:, 1]], axis=1)
scale = float(np.abs(E).max())
check("(N,3)@(3,2) equals the einsum (max abs diff under 1e-9 x scale)", float(np.abs(P1 - E).max()) < 1e-9 * scale, float(np.abs(P1 - E).max()))
check("...and the per-column matrix-vector products", float(np.abs(P1 - G).max()) < 1e-9 * scale, float(np.abs(P1 - G).max()))
check("two identical runs agree bit for bit", np.array_equal(P1, P2), float(np.abs(P1 - P2).max()))
print("  numpy %s" % np.__version__)
if FAILED:
    print("\n%d FAILED - numpy's threaded BLAS is WRONG on this machine: set OPENBLAS_NUM_THREADS=1 in the session's environment"
          " before any numpy work, and say so in FAILURES.md" % len(FAILED))
    sys.exit(1)
print("\nall cases pass.")

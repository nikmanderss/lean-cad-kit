# t_cutter - THE DRAWN CUTTER: remove a feature whole by drawing an independent tool from a measured,
# faired table. Fill PARAMS only.
#
#   DRAW THE CUTTER. MEASURE THE PART; DO NOT CUT WITH IT.
#
# WHY, AND WHY THIS IS A GATE RATHER THAN ADVICE. The opposite doctrine - take the cutter's outline
# from the feature's own faces - was the an earlier kit's `shaped-cut-from-feature` step 4, it was run here
# as `job_facecut.py` on 2026-09-15, and the client rejected the result on sight. Every number passed: 1
# solid, 4,447 faces, valid, 4,739.4 mm3 removed, debris 17 mm3. Then: *"does that look right to
# you?"* It did not. Vane 1's trailing edge had been one smooth continuous sweep; the cut left a hard
# square step a third of the way outboard, exactly where the donor face's own boundary ends.
#
# A FACE EDGE IS MODELLING HISTORY, NOT SHAPE. It carries trim boundaries the modeller happened to
# create, it splits asymmetrically left and right, and one physical feature is routinely spread over
# several faces with slivers between them. Build a cutter from those and you stamp every artefact
# into the part. Measured, on the same job - thin-wall columns against 94 on the untouched part:
# 141 with a face-built cutter (WORSE THAN NOT CUTTING), 81 with a drawn one.
#
# THE ORDER IS C0..C10 AND IT IS NOT OPTIONAL. Each step prints what it used, because a lever that
# is a literal inside a script stops being a tool and becomes the method (a recorded process failure).
#
#   C0  why is this a cut and not a deletion?      (an earlier kit's test T44 - the client's own question, asked first)
#   C1  find every face of the feature BY NORMAL   (numbering is not stable across revisions)
#   C2  classify by orientation                    (pointing away bounds material; into = air behind)
#   C3  measure a table from the tessellated faces (NEVER BoundBox - it lies on NURBS by tens of mm)
#   C4  symmetrise -> smooth -> OFFSET             (NEVER clamp: clamping puts the trim kinks back)
#   C5  declare where the cut ENDS                 (from the part, never from a face's edge)
#   C6  draw sections, sweep, ONE cutter solid
#   ==  GATE A: the proposal, BEFORE the cut       (T94 - the cheap check that catches a bad zone)
#   C7  cut once
#   C8  clean leftovers with boxes                 (a box is the cleanest cutter there is)
#   C9  verify - all seven
#   ==  GATE B: the result alone + what was removed (T61 - an overlay is BANNED as acceptance)
#   C10 RESULT
#
# TIER: WORKER (cad-worker-opus) from a filled card. C2, C4 and C5 are judgement calls - they are
# exactly the three the face-cut got wrong, and a gate cannot make them for you. A gate can refuse
# `boundary: "face_edge"`; it cannot tell you where the vane actually tapers out.
import os, sys, json, time
sys.path.insert(0, os.environ.get("KIT_HOME", os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import kitlib as K, Part
from FreeCAD import Vector as Vec

PARAMS = dict(
    base=K.NEED,                 # ABSOLUTE path. ONE unchanged base - never a previous result (L12)
    out_dir=".",                 # ABSOLUTE job folder

    # C0 - an earlier kit's test T44. the client: "Can you just delete things? You are always cutting, is that the only
    # way to remove material?" One line, in your own words. Boilerplate is refused.
    why_not_delete="",

    # C1 - the feature, found by the direction its faces point. `kit measure faces --normal` prints
    # the same selection with the per-face angles and the spread warning; use it first.
    # `tol_deg` IS MEASURED AND HAS NO DEFAULT. The four faces the client picked for the vane-plate removal
    # have normals (-0.131,-0.020,-0.991) and (-0.125,0.092,-0.988) - **7.6 and 8.9 deg** off -z.
    # Any card written at 5 finds NONE of them and reports an empty selection, which is the T68
    # trap: an empty set proves nothing and reads as a clean part. Those are that part's numbers,
    # not this type's - measure yours with `kit measure faces --normal` and put them on the card.
    find=dict(normal=K.NEED, tol_deg=K.NEED,
              within=K.NEED),                      # x0 x1 y0 y1 z0 z1 - the search box

    # C3 - the table. `along` is the axis stations run along; `cross` is sampled across; the sweep
    # axis is whatever is left. `step` is the station pitch in mm.
    along=K.NEED, cross=K.NEED, step=K.NEED, cross_samples=K.NEED,

    # C4 - fairing. `symmetrise` mirrors and averages about a plane on the CROSS axis (None = off).
    # `offset_mm` MUST exceed the smoothing's own worst deviation - the run refuses otherwise, and
    # clamping is refused outright. Offsetting past the deviation is the whole rule: pinning the
    # faired line back to the measured one so it can "only err safely" puts the trim kinks straight
    # back, and they appear in the part as steps.
    symmetrise=None,             # e.g. 0.0 to mirror about cross = 0
    smooth_mm=K.NEED,
    offset_mm=K.NEED,
    cross_margin_mm=0.30,   # 31bx (R2 F1): each station's cross extent widened both ways by this - a round feature's extreme points lie ON the sampled faces, so a tool bounded
                            # exactly by them passes through those points and leaves zero-volume needles no volume check sees (GATE B's picture did); the print tolerance by default, 0 = the bare extent

    # C5 - WHERE THE CUT ENDS. Declared, never inherited. This is the slot the rejected face-cut
    # had no answer for. "stations" = end at these `along` values (the feature's own taper, read
    # from sections); "full" = the selection's own span, only honest when the feature ends in air.
    boundary=dict(type=K.NEED, value=K.NEED),

    # C6 - the sweep. dir +1 cuts from the floor UPWARD along the remaining axis; -1 downward.
    sweep=dict(dir=K.NEED, dist_mm=K.NEED),

    # C8 - leftovers. Each entry is x0 x1 y0 y1 z0 z1. Keep them on the card, never inline.
    cleanup_boxes=(),

    # C9 - what the result must satisfy. `volume_mm3` is REQUIRED: a cut with no expectation cannot
    # be verified, and T61 is the trap of accepting a boolean on numbers alone.
    # `thinwall_mm` is the PROCESS MINIMUM for the part, not the face-area tolerance: a column of
    # material thinner than this will not print. Set it from the print rules (MJF PA12: the vane
    # work used 3.5 mm as "thin"). `thinwall_max` None means "no worse than the untouched part",
    # which is the comparison that settled the doctrine.
    expect=dict(volume_mm3=None, vol_tol=K.NEED, area_growth_max=K.NEED,
                thinwall_mm=K.NEED, thinwall_max=None, sliver_mm3=K.NEED,
                boundary_step_max=K.NEED),

    cutter_name="cutter.brep",   # ABSOLUTE path: the tool alone - GATE A looks at this
    result_name="result.brep",   # ABSOLUTE path: the cut body - GATE B looks at this
    removed_name="removed.brep", # ABSOLUTE path: original - result, as its own solid
    attempt=1,                   # bump it on a retry and say in RESULT.md what you changed
)
P = PARAMS
K.need(P)          # every slot the CARD owns, named in one refusal
OUT = str(P["out_dir"])
AX = {"x": 0, "y": 1, "z": 2}
t_start = time.time()


def say(*a):
    print("CUTTER " + " ".join(str(x) for x in a), flush=True)


def retry_block(check, seen, want, levers):
    """Instructed, not forced. the client: 'If the first attempt fails the agent should be instructed to try
    again with different settings but not be forced to.' So this STOPS - it never retries itself and
    it never blocks a retry."""
    lines = ["", "RETRY BLOCK - attempt %d failed %s" % (int(P.get("attempt", 1)), check),
             "  saw %s, wanted %s" % (seen, want), "",
             "  ONE VARIABLE PER RETRY - a recorded process failure. More than once on this project,",
             "  four settings moved at once produced a worse result nobody could attribute.",
             "  Suggested, in order:"]
    for i, (lev, why) in enumerate(levers, 1):
        lines.append("    %d. %-22s %s" % (i, lev, why))
    lines += ["",
              "  A retry is a CHANGED PROBLEM: re-derive from the new input, do not carry numbers",
              "  across (#1). You may also STOP AND REPORT - that is always a valid outcome.",
              "  Dropping scope to escape the defect is not (#9: 'you are giving up and taking the",
              "  easy way out'). Say which lever you changed and why in RESULT.md, and bump `attempt`.", ""]
    K.fail("\n".join(lines))


# ---------------------------------------------------------------------------- C0
_why = str(P.get("why_not_delete", "") or "").strip()
if len(_why) < 20 or _why.lower() in ("n/a", "na", "none", "not applicable", "tbd", "because"):
    K.fail("C0 REFUSED - `why_not_delete` is empty or boilerplate.\n"
           "  an earlier kit's test T44, the client's own words: \"Can you just delete things? You are always cutting, is\n"
           "  that the only way to remove material?\" On a mesh, removal is deleting triangles and\n"
           "  splitting straddlers - no solid-against-solid boolean anywhere. On a B-rep it usually\n"
           "  is a cut, but the question costs one line and it is the cheapest step in this card.\n"
           "  Answer it in your own words, then run again.")
say("C0 why not a deletion:", _why)

# ---------------------------------------------------------------------------- C1
body = K.load(P["base"])
v0 = float(body.Volume)
a0 = float(body.Area)
say("C0 base %s: %d solid(s), %d faces, %.1f mm3, area %.1f mm2, valid %s"
    % (os.path.basename(str(P["base"])), len(body.Solids), len(body.Faces), v0, a0, body.isValid()))

_n = np.array(P["find"]["normal"], float)
_n = _n / max(np.linalg.norm(_n), 1e-12)
_tol = float(P["find"]["tol_deg"])
bx = [float(t) for t in P["find"]["within"]]
if len(bx) != 6:
    K.fail("C1: find.within needs SIX numbers x0 x1 y0 y1 z0 z1")


def face_angle(f):
    """Angle between the face's OUTWARD normal and the target, at the parameter midpoint, degrees.

    ORIENTATION IS APPLIED. `normalAt` gives the SURFACE normal; a face whose Orientation is
    'Reversed' points the other way and half a B-rep's faces typically are. Getting this wrong
    selects the far side of the part and every measurement after it is of the wrong material -
    silently, because the count still looks plausible."""
    try:
        u0, u1, w0, w1 = f.ParameterRange
    except Exception:
        return None
    nv = K.outward_normal(f, 0.5 * (u0 + u1), 0.5 * (w0 + w1))      # 31bu (T6 F2): the OUTWARD normal, calibrated once in kitlib - the hand flip on a Reversed face had inverted it (R02: the cutter drew at the bottom)
    if nv is None:
        return None
    d = nv.x * _n[0] + nv.y * _n[1] + nv.z * _n[2]
    return float(np.degrees(np.arccos(max(-1.0, min(1.0, d)))))


sel = []
for i, f in enumerate(body.Faces):
    b = f.BoundBox
    if not (b.XMax >= bx[0] and b.XMin <= bx[1] and b.YMax >= bx[2] and b.YMin <= bx[3]
            and b.ZMax >= bx[4] and b.ZMin <= bx[5]):
        continue                                   # the box SELECTS a region; it never MEASURES
    ang = face_angle(f)
    if ang is not None and ang <= _tol:
        sel.append((i, f, ang, float(f.Area)))
if not sel:
    K.fail("C1: no face in the box points within %.1f deg of %s.\n"
           "  An empty selection proves nothing (T68). Widen --tol-deg, check the normal's SIGN\n"
           "  (an underside points -z, not +z), or widen the box. `kit measure faces --normal %s\n"
           "  --tol-deg %g --box \"%s\"` prints every candidate with its angle."
           % (_tol, tuple(_n), ",".join("%g" % c for c in _n), _tol, " ".join("%g" % c for c in bx)))
say("C1 found %d face(s) by normal %s within %.1f deg, total area %.1f mm2; face #s %s"
    % (len(sel), tuple(round(c, 3) for c in _n), _tol, sum(s[3] for s in sel),
       [s[0] + 1 for s in sel][:24]))

# ---------------------------------------------------------------------------- C2
# CLASSIFY BY ORIENTATION. A face pointing AWAY from the material bounds it; one pointing INTO it
# has air behind. Only the first kind can carry the floor of a cut - a face with air behind it is
# the far side of a void and measuring the floor from it puts the cutter through the part.
away = [s for s in sel if s[2] <= _tol]
say("C2 %d face(s) bound material (normal points away from it); total area %.1f mm2"
    % (len(away), sum(s[3] for s in away)))
if not away:
    K.fail("C2: every selected face has air behind it - none of them bounds the material you mean\n"
           "  to remove. Re-read the sections; the feature is probably on the other side.")

# ---------------------------------------------------------------------------- C3
# MEASURE FROM THE TESSELLATED FACES, NEVER FROM BoundBox. `Shape.BoundBox` on NURBS is computed
# from CONTROL POINTS and over-reports by up to 45 mm on this body (L36). That reading once led to
# a near-filed bug against the kernel; the true extents, taken this way, were exactly right.
ia, ic = AX[str(P["along"])], AX[str(P["cross"])]
if ia == ic:
    K.fail("C3: `along` and `cross` are the same axis (%s). They name two different directions: "
           "stations run ALONG one and are sampled ACROSS the other." % P["along"])
iw = ({0, 1, 2} - {ia, ic}).pop()
step = float(P["step"])
sgn = 1.0 if int(P["sweep"]["dir"]) > 0 else -1.0

pts = []
for _, f, _, _ in away:
    try:
        vv, _tr = f.tessellate(0.05)
        pts.extend([[p.x, p.y, p.z] for p in vv])
    except Exception:
        pass
Pt = np.asarray(pts, float)
if len(Pt) < 16:
    K.fail("C3: the selected faces tessellate to %d point(s) - too few to measure a table." % len(Pt))
U, C, W = Pt[:, ia], Pt[:, ic], Pt[:, iw]

u_edges = np.arange(U.min(), U.max() + step, step)
if len(u_edges) < 4:
    K.fail("C3: the feature spans %.2f mm along %s, under 4 stations at step %g. Lower `step`."
           % (U.max() - U.min(), P["along"], step))
ui = np.clip(np.digitize(U, u_edges) - 1, 0, len(u_edges) - 2)
NS, NV = len(u_edges) - 1, int(P["cross_samples"])
c_lo = np.full(NS, np.nan); c_hi = np.full(NS, np.nan)
Wt = np.full((NS, NV), np.nan)
for i in range(NS):
    m = ui == i
    if m.sum() < 3:
        continue
    c_lo[i], c_hi[i] = C[m].min(), C[m].max()
    if c_hi[i] - c_lo[i] < 1e-6:
        continue
    # the floor at NV fixed fractions across the station, so every outline has the SAME vertex
    # count - a narrowing feature is handled by the fractions, not by dropping points
    frac = (C[m] - c_lo[i]) / (c_hi[i] - c_lo[i])
    jj = np.clip((frac * (NV - 1)).round().astype(int), 0, NV - 1)
    for j in range(NV):
        mj = jj == j
        if mj.any():
            Wt[i, j] = (W[m][mj].min() if sgn > 0 else W[m][mj].max())
live = ~np.isnan(c_lo)
if live.sum() < 4:
    K.fail("C3: only %d station(s) carry data. The selection is too sparse to draw from." % live.sum())
# fill gaps across the cross direction, then along the stations - a hole in the table is a hole in
# the cutter, and a hole in the cutter is material left behind
filled = int(np.isnan(Wt[live]).sum())
for i in np.where(live)[0]:
    row = Wt[i]
    ok = ~np.isnan(row)
    if ok.sum() >= 2:
        Wt[i] = np.interp(np.arange(NV), np.where(ok)[0], row[ok])
for arr in (c_lo, c_hi):
    ok = ~np.isnan(arr)
    arr[~ok] = np.interp(np.where(~ok)[0], np.where(ok)[0], arr[ok]) if ok.sum() >= 2 else 0.0
for j in range(NV):
    col = Wt[:, j]
    ok = ~np.isnan(col)
    if ok.sum() >= 2:
        Wt[:, j] = np.interp(np.arange(NS), np.where(ok)[0], col[ok])
u_mid = 0.5 * (u_edges[:-1] + u_edges[1:])
say("C3 table: %d stations at %g mm along %s, %d cross samples; %s span %.2f..%.2f, floor %.2f..%.2f"
    % (NS, step, P["along"], NV, P["cross"], np.nanmin(c_lo), np.nanmax(c_hi),
       np.nanmin(Wt), np.nanmax(Wt)))
if filled:
    say("C3 NOTE: %d of %d cells had no data and were interpolated (%.1f pct). A large number here\n"
        "       means the selection has holes in it - check C1 caught every face of the feature."
        % (filled, NS * NV, 100.0 * filled / max(1, NS * NV)))

# ---------------------------------------------------------------------------- C4
W_raw = Wt.copy()
sym = P.get("symmetrise")
if sym is not None:
    # SYMMETRISE. A physical feature that is symmetric was modelled asymmetrically: the trims fall
    # in different places left and right. Averaging the two sides removes the modelling difference
    # and keeps the shape.
    s0 = float(sym)
    cmid = 0.5 * (c_lo + c_hi)
    say("C4 symmetrise about %s = %g: the cross mid-line sits at %.3f +- %.3f before"
        % (P["cross"], s0, cmid.mean(), cmid.std()))
    Wt = 0.5 * (Wt + Wt[:, ::-1])
    half = 0.5 * (np.abs(c_hi - s0) + np.abs(c_lo - s0))
    c_lo, c_hi = s0 - half, s0 + half


def smooth2(A, r_cells):
    if r_cells < 1:
        return A
    k = 2 * int(r_cells) + 1
    ker = np.ones(k) / k
    B = np.apply_along_axis(lambda v: np.convolve(np.pad(v, (k // 2, k // 2), mode="edge"), ker, "valid"), 0, A)
    return np.apply_along_axis(lambda v: np.convolve(np.pad(v, (k // 2, k // 2), mode="edge"), ker, "valid"), 1, B)


r = max(0, int(round(float(P["smooth_mm"]) / max(step, 1e-6))))
W_sm = smooth2(Wt, r)
dev = float(np.nanmax(np.abs(W_sm - Wt)))
off = float(P["offset_mm"])
say("C4 smooth radius %g mm (%d cells): worst deviation from the measured floor %.3f mm; offset %.3f mm"
    % (P["smooth_mm"], r, dev, off))
# THE RULE, AND THE REFUSAL THAT ENFORCES IT.
if off <= dev:
    K.fail("C4 REFUSED - offset_mm %.3f does not exceed the smoothing's own worst deviation %.3f.\n"
           "  Then the faired floor sits ABOVE the measured surface somewhere, and the cut leaves a\n"
           "  skin of the old feature exactly where the smoothing worked hardest.\n"
           "  RAISE offset_mm past %.3f, or LOWER smooth_mm until the deviation drops.\n"
           "  DO NOT clamp the faired table back to the measured one - that is the failure this rule\n"
           "  exists to stop: clamping reinstates the trim kinks and they appear in the part as steps."
           % (off, dev, dev))
W_fin = W_sm - sgn * off
say("C4 faired floor %.3f..%.3f (measured %.3f..%.3f); the faired floor is clear of the measured\n"
    "       surface everywhere by at least %.3f mm"
    % (W_fin.min(), W_fin.max(), W_raw.min(), W_raw.max(), off - dev))

# ---------------------------------------------------------------------------- C5
bt = str(P["boundary"]["type"])
if bt == "face_edge":
    K.fail("C5 REFUSED - boundary.type 'face_edge'.\n"
           "  A face's edge is not where the feature ends; it is an internal boundary of the B-rep.\n"
           "  Cutting to it is what put the square step in vane 1 on 2026-09-15 and it is the whole\n"
           "  reason this template exists. Declare the boundary from the PART - where the feature\n"
           "  tapers out, a plane you can name, a curve you measured - and put it on the card.")
if bt == "stations":
    b_lo, b_hi = P["boundary"]["value"]
    keep = np.ones(NS, bool)
    if b_lo is not None:
        keep &= u_mid >= float(b_lo)
    if b_hi is not None:
        keep &= u_mid <= float(b_hi)
elif bt == "full":
    keep = np.ones(NS, bool)
    say("C5 boundary 'full' - the cut ends at the selection's own span. This is only honest when the\n"
        "       feature ENDS IN AIR there. If it runs into material, you are about to make a stub.")
else:
    K.fail("C5: boundary.type %r is not one of 'stations' / 'full'." % bt)
if keep.sum() < 3:
    K.fail("C5: the boundary leaves %d station(s). Check the values against the table's span %.2f..%.2f."
           % (keep.sum(), u_mid.min(), u_mid.max()))
ks = np.where(keep)[0]
say("C5 boundary %s: %d of %d stations kept, %s %.2f..%.2f"
    % (bt, len(ks), NS, P["along"], u_mid[ks[0]], u_mid[ks[-1]]))

# ---------------------------------------------------------------------------- C6
# DRAW SECTIONS, SWEEP, ONE SOLID. Ruled segments between consecutive stations - no loft, no fitted
# surface (METHOD.md 4 forbids both). Each outline is the faired floor sampled across the station,
# then up to a flat top that stands in air.
w_top = (W_fin.max() + float(P["sweep"]["dist_mm"])) if sgn > 0 else (W_fin.min() - float(P["sweep"]["dist_mm"]))
nrm = {0: "+x", 1: "+y", 2: "+z"}[ia]
udir = {0: "+x", 1: "+y", 2: "+z"}[ic]


_cm = float(P.get("cross_margin_mm", 0.0) or 0.0)
def outline(i):
    cs = np.linspace(c_lo[i], c_hi[i], NV)
    pts2 = [(float(cs[j]), float(W_fin[i, j])) for j in range(NV)]
    if _cm > 0: pts2 = [(float(cs[0]) - _cm, float(W_fin[i, 0]))] + pts2 + [(float(cs[-1]) + _cm, float(W_fin[i, -1]))]      # 31bx (R2 F1): the cross margin: a flat lip of cm on each side of the measured floor
    return pts2 + [(pts2[-1][0], w_top), (pts2[0][0], w_top)]


def origin(u):
    o = [0.0, 0.0, 0.0]
    o[ia] = float(u)
    return tuple(o)


segs = []
for a, b in zip(ks[:-1], ks[1:]):
    plA = K.plane(origin(u_mid[a]), nrm, udir)
    plB = K.plane(origin(u_mid[b]), nrm, udir)
    try:
        segs.append(K.connect(plA, outline(a), plB, outline(b)))
    except Exception as e:
        K.fail("C6: the ruled segment between stations %.3f and %.3f failed (%s).\n"
               "  Usually the outlines cross - the floor jumps between neighbouring stations. Raise\n"
               "  smooth_mm, or narrow the boundary past the jump." % (u_mid[a], u_mid[b], str(e)[:160]))
cutter = segs[0] if len(segs) == 1 else segs[0].fuse(segs[1:])
cutter = cutter.removeSplitter()
say("C6 cutter: %d segment(s) -> %d solid(s), %d faces, %.1f mm3, valid %s; cross margin %.2f mm each side (31bx R2 F1: a tool bounded exactly by the sampled faces' extreme points leaves zero-volume needles on a round feature)"
    % (len(segs), len(cutter.Solids), len(cutter.Faces), cutter.Volume, cutter.isValid(), _cm))
if not cutter.Solids or cutter.Volume <= 0:
    K.fail("C6: the swept cutter is empty. Check sweep.dir against the normal's sign.")
_wrA = K.save_if_changed(cutter, P["cutter_name"])      # 31bu (TK2 F2): the same bytes leave the file alone, so GATE A's verdict on it stands on a re-run
say("C6 cutter %s: %s" % ("written" if _wrA else "UNCHANGED since the last run (the same bytes) - a verdict already given on it stands", P["cutter_name"]))

# ---------------------------------------------------------------------------- GATE A
# T94: PROPOSE EVERY REPLACEMENT ZONE AS A PICTURE BEFORE CUTTING. One cheap render is the only
# check that catches a mis-placed zone, and it catches it before the expensive step.
CARD = K.card_sig({k: P[k] for k in ("base", "find", "along", "cross", "step", "cross_samples",
                                     "symmetrise", "smooth_mm", "offset_mm", "cross_margin_mm", "boundary", "sweep")})      # 31bx (R2 F1): the margin changes the shape - signed
# Only the entries that CHANGE THE SHAPE are signed. Over-signing makes every verdict stale on a
# cosmetic edit, which trains agents to re-issue verdicts without looking - the opposite of a gate.
say("card signature %s  - pass it to `kit verdict ... --card %s` so the verdict is bound to THESE\n"
    "       numbers and not merely to this file." % (CARD, CARD))
_bbA = cutter.BoundBox; _boxA = "%.1f %.1f %.1f %.1f %.1f %.1f" % (_bbA.XMin - 3, _bbA.XMax + 3, _bbA.YMin - 3, _bbA.YMax + 3, _bbA.ZMin - 3, _bbA.ZMax + 3)      # 31bu (TK2 F3): a real command at the feature's box
K.verdict_require(
    OUT, "cutterA", P["cutter_name"], CARD, "THE CUT",
    "kit render \"%s\" --out \"%s\" --box %s --views all   (A1 the cutter ALONE)  and  kit render \"%s\" --out \"%s\" --box %s --views all   "
    "(A2 the base at the cutter's place - the two sets share one camera - judge them side by side, never overlaid); OPEN EVERY FRAME"
    % (P["cutter_name"], os.path.join(OUT, "gateA"), _boxA, P["base"], os.path.join(OUT, "gateA_base"), _boxA))
say("GATE A passed. Judged: does the cutter cover the WHOLE feature, and does it end where the card\n"
    "       says - not on a face edge?")

# ---------------------------------------------------------------------------- C7
res = K.cut(body, [cutter], "cutter")
# 31bx (R2 F1): the result cleaned as the tool is (kit run allows this template its own removeSplitter - 31bs K25); the floor's faces are the ruled segments' - one per station interval by construction (`step` sets the pitch)
# 31ca (round 2's R2 F1): THE CLEANUP IS KEPT ONLY WHERE IT CHANGES NOTHING FAR FROM THE CUT - removeSplitter runs over the WHOLE body and merged coplanar faces of earlier fused
# features far from the cut (a plate with two fused cubes: 12 faces; `kit check`: changed far from every edit region box). The faces whose centre of mass lies OUTSIDE the cutter's
# box grown by the card's cross_margin_mm are compared before and after as multisets of (area to 1e-6, centre to 1e-4): equal - the cleaned body is used; not - the result stays as cut.
try:
    _cl = res.copy().removeSplitter()      # 31ca: on a COPY - removeSplitter changes the shape it is called on (measured 2026-11-06, FreeCAD 1.1.3: the cut 27854.03 mm3 valid True read 27948.27 valid False after it)
    _bbC = cutter.BoundBox; _gm = float(P.get("cross_margin_mm", 0.0) or 0.0)
    _clo = (_bbC.XMin - _gm, _bbC.YMin - _gm, _bbC.ZMin - _gm); _chi = (_bbC.XMax + _gm, _bbC.YMax + _gm, _bbC.ZMax + _gm)
    def _far_faces(sh):
        _o = []
        for f_ in sh.Faces:
            c_ = f_.CenterOfMass
            if _clo[0] <= c_.x <= _chi[0] and _clo[1] <= c_.y <= _chi[1] and _clo[2] <= c_.z <= _chi[2]: continue
            _o.append((round(f_.Area, 6), round(c_.x, 4), round(c_.y, 4), round(c_.z, 4)))
        return _o
    _fr = _far_faces(res); _rest = _far_faces(_cl); _gone = 0
    for t_ in _fr:
        if t_ in _rest: _rest.remove(t_)
        else: _gone += 1
    if _gone == 0 and not _rest:
        res = _cl; say("C7 cleanup: removeSplitter used - it changes no face far from the cut (%d face(s) outside the cutter's box grown by %.2f mm, the same before and after)" % (len(_fr), _gm))
    else:
        say("C7 cleanup: the whole-body cleanup would merge %d face(s) far from the cut - the result is kept uncleaned (the cut's own faces carry their splits; the card's face figure counts them)" % max(_gone, len(_rest)))
except Exception as _exrs: say("C7 note: removeSplitter on the result failed (%s) - the result stands as cut" % str(_exrs)[:80])
say("C7 cut: %d solid(s), %d faces, %.1f mm3 (%+.1f), valid %s (the floor's faces: one ruled face per station interval - `step` sets the pitch)"
    % (len(res.Solids), len(res.Faces), res.Volume, res.Volume - v0, res.isValid()))

# ---------------------------------------------------------------------------- C8
for k, bxx in enumerate(P.get("cleanup_boxes") or ()):
    b = [float(t) for t in bxx]
    if len(b) != 6:
        K.fail("C8: cleanup box %d needs SIX numbers" % k)
    res = K.cut(res, [K.box(*b)], "cleanup %d" % k)
    say("C8 cleanup box %d %s -> %.1f mm3" % (k, b, res.Volume))

# ---------------------------------------------------------------------------- C9
E = P["expect"]
fails = []
# A CHECK THAT DID NOT RUN IS NOT A CHECK THAT PASSED - the process-failure record.md 11.
# Checks 2 and 3 keep their try/except (a report that kills the edit is worse than an absent check),
# but a check that threw is now neither PASS nor FAIL: it is carried by name to GATE B, where a human
# already has to look, and into cutter_report.json. It refuses nothing.
not_taken = []
res_full = res
solids = sorted(res.Solids, key=lambda s: -s.Volume)
slivers = [s for s in solids[1:] if s.Volume <= float(E["sliver_mm3"])]
big = [s for s in solids[1:] if s.Volume > float(E["sliver_mm3"])]
if len(solids) > 1:
    say("C9 solids: %d. Kept %.1f mm3; %d sliver(s) totalling %.2f mm3 dropped; %d over the sliver limit"
        % (len(solids), solids[0].Volume, len(slivers), sum(s.Volume for s in slivers), len(big)))
    if big:
        fails.append("%d solid(s) over the %g mm3 sliver limit: %s"
                     % (len(big), E["sliver_mm3"], [round(s.Volume, 1) for s in big]))
    res = solids[0]

removed = body.cut(res)
K.save(removed, P["removed_name"])
rv = float(removed.Volume)

# 1. removed volume
if E.get("volume_mm3") is None:
    K.fail("C9 REFUSED - expect.volume_mm3 is not set.\n"
           "  A result with no expectation cannot be verified, and T61 is exactly the trap of\n"
           "  accepting a boolean on numbers alone. Measure what the feature should weigh (a probe,\n"
           "  a section, the topspan map) and put it on the card. The cut removed %.1f mm3." % rv)
ev = float(E["volume_mm3"]); tol = float(E["vol_tol"])
ok1 = abs(rv - ev) <= tol * ev
say("C9 1 removed volume %.1f mm3 against an expected %.1f (%+.1f pct, limit %g pct)  %s"
    % (rv, ev, 100.0 * (rv - ev) / max(ev, 1e-9), 100 * tol, "PASS" if ok1 else "FAIL"))
if not ok1:
    fails.append("removed volume %.1f vs expected %.1f" % (rv, ev))

# 5. SURFACE AREA - T42. A cut that ends with MORE surface area than it started is wrong: 401,800
# -> 444,916 mm2, +10.7 pct, was rejected outright. The lean doc had no area check at all.
a1 = float(res.Area); growth = a1 / max(a0, 1e-9) - 1.0
ok5 = growth <= float(E["area_growth_max"])
say("C9 5 surface area %.1f -> %.1f mm2 (%+.2f pct, limit %+.2f pct)  %s"
    % (a0, a1, 100 * growth, 100 * float(E["area_growth_max"]), "PASS" if ok5 else "FAIL"))
if not ok5:
    fails.append("surface area grew %+.2f pct" % (100 * growth))

# 6. CONSERVATION - T95. kept + removed - source, to machine precision. Strictly stronger than a
# volume comparison: it caught a pass that LOST 9 faces and another that DUPLICATED 33, both of
# which passed the weaker gate.
# `removed` is taken against the KEPT solid, so the slivers are on the removed side of the identity
# and `res` is the right operand here, not `res_full`. Using the pre-drop shape would post a
# residual exactly equal to the slivers and call a clean cut a failure.
resid = float(res.Volume) + rv - v0
ok6 = abs(resid) <= max(1e-3, 1e-6 * v0)
say("C9 6 conservation kept %.4f + removed %.4f - source %.4f = %+.6f mm3  %s"
    % (res.Volume, rv, v0, resid, "PASS" if ok6 else "FAIL"))
if not ok6:
    fails.append("conservation residual %+.6f mm3" % resid)

# 7. RE-VALIDATE - T89. Validity, not a ratio: 92.4 pct of full bore passed a 92 pct gate and left a
# tangential sliver. And `isValid()` is True on an EMPTY shape (L32), so count solids and volume first.
ok7 = bool(res.Solids) and res.Volume > 0 and res.isValid()
say("C9 7 re-validate: %d solid(s), %.1f mm3, valid %s  %s"
    % (len(res.Solids), res.Volume, res.isValid(), "PASS" if ok7 else "FAIL"))
if not ok7:
    fails.append("the result is not one valid non-empty solid")

# 2. THIN-WALL COUNT - the check that settled the doctrine. 94 untouched, 141 with a face-built
# cutter (worse than not cutting), 81 with a drawn one.
#
# The tessellations and the box are built OUTSIDE the try, because check 3 uses all three. Building
# them inside meant a failure in check 2 took check 3 down with a NameError that its own except
# reported as "boundary check NOT TAKEN" - one fault presenting as two, with the second one lying
# about its cause.
tw_lim = E.get("thinwall_max")
tb = ((bx[0], bx[1]), (bx[2], bx[3]), (bx[4], bx[5]))
Vb, Tb = K.tess(body)[0:2]
Vr, Tr = K.tess(res)[0:2]
try:
    _, _, Hb = K.thickness_map(Vb, Tb, tb, step=1.0, axis=iw)
    _, _, Hr = K.thickness_map(Vr, Tr, tb, step=1.0, axis=iw)
    thin = float(E["thinwall_mm"])
    nb = int(((Hb > 1e-6) & (Hb < thin)).sum()); nr = int(((Hr > 1e-6) & (Hr < thin)).sum())
    lim = int(tw_lim) if tw_lim is not None else nb
    ok2 = nr <= lim
    say("C9 2 thin-wall columns under %g mm: %d before -> %d after (limit %d)  %s"
        % (thin, nb, nr, lim, "PASS" if ok2 else "FAIL"))
    if not ok2:
        fails.append("thin-wall columns %d -> %d, over the limit %d" % (nb, nr, lim))
except Exception as e:
    not_taken.append("2 thin-wall column count (%s)" % str(e)[:90])
    say("C9 2 thin-wall count NOT TAKEN (%s). This is the check that settled the doctrine - take it\n"
        "       by hand before accepting the result." % str(e)[:140])

# 3. THE BOUNDARY, STATION BY STATION - stub / knife edge / island. Compare the material depth just
# inside the cut's ends with just outside: a real boundary steps by nothing.
try:
    def depth_at(u):
        """Mean material depth in a 1 mm slab at station u, on the RESULT."""
        sl = [list(t) for t in tb]
        sl[ia] = [float(u) - 0.5, float(u) + 0.5]
        _, _, Hs = K.thickness_map(Vr, Tr, tuple(tuple(t) for t in sl), step=1.0, axis=iw)
        return float(Hs[Hs > 1e-6].mean()) if (Hs > 1e-6).any() else 0.0

    # 1.5 mm each side of each end. A cut that finishes on a REAL boundary steps by nothing here;
    # a stub, a knife edge or an island all show as a jump.
    step_lo = abs(depth_at(u_mid[ks[0]] + 1.5) - depth_at(u_mid[ks[0]] - 1.5))
    step_hi = abs(depth_at(u_mid[ks[-1]] - 1.5) - depth_at(u_mid[ks[-1]] + 1.5))
    ok3 = max(step_lo, step_hi) <= float(E["boundary_step_max"])
    say("C9 3 boundary step: %.3f mm at the low end, %.3f at the high (limit %g)  %s"
        % (step_lo, step_hi, E["boundary_step_max"], "PASS" if ok3 else "FAIL"))
    if not ok3:
        fails.append("boundary step %.3f mm - a stub or a knife edge" % max(step_lo, step_hi))
except Exception as e:
    not_taken.append("3 boundary step at the cut's ends (%s)" % str(e)[:90])
    say("C9 3 boundary check NOT TAKEN (%s). Read the ends in sections before accepting." % str(e)[:140])

# 4. solids - reported above
say("C9 4 solids kept 1, slivers dropped %d (%.2f mm3)" % (len(slivers), sum(s.Volume for s in slivers)))

if fails:
    retry_block(
        "; ".join(fails), "the numbers above", "every check PASS",
        [("fair.offset_mm  %.2f -> %.2f" % (off, off + 0.3),
          "the faired floor is cutting shy and leaving a skin"),
         ("boundary.value", "the cut is ending inside material - extend it to where the feature tapers"),
         ("cleanup_boxes", "a leftover the sweep cannot reach; add a box"),
         ("find.tol_deg  %.1f -> %.1f" % (_tol, _tol + 3),
          "C1 may have missed part of the feature - check the C3 interpolated-cell count")])

_wrB = K.save_if_changed(res, P["result_name"])      # 31bu (TK2 F2): as at GATE A
say("C8 result %s: %s" % ("written" if _wrB else "UNCHANGED since the last run (the same bytes) - a verdict already given on it stands", P["result_name"]))

# ---------------------------------------------------------------------------- GATE B
# T61: a boolean's PRIMARY acceptance is a look at the BUILT SOLID ALONE; an overlay is BANNED as
# acceptance. the client, in this project, in stronger terms: "YOU CAN'T OVERLAY THE ORBIT OR YOU DON'T SEE
# THE EDIT." Render from the angle the client works in - isometric from above.
_bbB = removed.BoundBox; _boxB = "%.1f %.1f %.1f %.1f %.1f %.1f" % (_bbB.XMin - 3, _bbB.XMax + 3, _bbB.YMin - 3, _bbB.YMax + 3, _bbB.ZMin - 3, _bbB.ZMax + 3)      # 31bu (TK2 F3)
_how = ("kit render \"%s\" --out \"%s\" --box %s --views all   (B1 the RESULT ALONE at the cut's box)  and  kit render \"%s\" --out \"%s\" --box %s --views all   "
        "(B2 what was REMOVED, as its own solid - never overlaid); OPEN EVERY FRAME"
        % (P["result_name"], os.path.join(OUT, "gateB"), _boxB, P["removed_name"], os.path.join(OUT, "gateB_removed"), _boxB))
if not_taken:
    # Not a refusal. The one place a check that could not run is guaranteed to be read is the gate a
    # human already has to pass, so it is named there and in nothing quieter.
    say("C9 ** %d CHECK(S) DID NOT RUN - they are NOT passes **" % len(not_taken))
    for _n in not_taken:
        say("      not taken: C9 %s" % _n)
    say("      Every other check may read PASS above. These were not among them; judge them by eye\n"
        "      at GATE B and say in RESULT.md what you saw.")
    _how += ("\n       AND JUDGE BY EYE, because the run could not: C9 "
             + "; C9 ".join(not_taken))
K.verdict_require(
    OUT, "cutterB", P["result_name"], CARD, "BANKING THE RESULT", _how)
say("GATE B passed. Judged: is the removed material the feature and ONLY the feature, and does the\n"
    "       result carry no stub, knife edge or island at the boundary?%s"
    % ("\n       ...and the %d check(s) that did not run, by eye." % len(not_taken) if not_taken else ""))

# ---------------------------------------------------------------------------- C10
rep = dict(attempt=int(P.get("attempt", 1)), base=str(P["base"]), why_not_delete=_why,
           faces_found=len(sel), faces_bounding=len(away), stations=int(len(ks)),
           smooth_mm=float(P["smooth_mm"]), smooth_deviation=round(dev, 4), offset_mm=off,
           boundary=str(bt), removed_mm3=round(rv, 2), expected_mm3=ev,
           area_before=round(a0, 1), area_after=round(a1, 1), area_growth_pct=round(100 * growth, 3),
           conservation_residual=round(resid, 6), solids=len(solids), slivers=len(slivers),
           valid=bool(res.isValid()), checks_not_taken=list(not_taken),
           secs=round(time.time() - t_start))
with open(os.path.join(OUT, "cutter_report.json"), "w", encoding="utf-8") as fh:
    json.dump(rep, fh, indent=1)
say("C10 done in %d s. %s" % (rep["secs"], json.dumps(rep)))
say("C10 saved %s" % P["result_name"])

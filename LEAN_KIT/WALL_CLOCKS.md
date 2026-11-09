# TYPICAL WALL CLOCKS PER JOB — a living table. UPDATE IT AS YOU GO.

**the client, 2026-09-14:** *"log for future agents in this session what typical wall clocks are per job.
Update the average as you go and do not include jobs that have runaway issues in regards to time."*
And: *"any clock that runs 1.5x what a typical job runs is a red flag and needs to be evaluated."*

> **Master copy.** Promoted from `the project\claude_code\` on 2026-09-16 (merge request M21). **This table
> is now load-bearing: `hooks\wallclock.py`'s `STEP_BUDGETS` is generated from it, at 1.5x each typical.**
> An expectation that lives only in a document is an expectation nothing can enforce — that was the
> original defect. Change a number here and change it there, or the two instruments disagree.

## How to use this file

1. **Before launching a step, read its typical here** and know what you are expecting.
2. **After it returns, add its time** to the samples and re-take the typical.
3. **A run at 1.5x the typical is a RED FLAG — evaluate it.** Evaluate means find the cause, not
   note it and carry on. At 2x, treat it as stuck (L11) unless you can say in one line why it is
   legitimately long.
4. **Do NOT fold a runaway into the average.** A hang, a wait on a file that is never written, or a
   run that was killed is a defect sample, not a timing sample. Record it in the RUNAWAYS section
   with its cause so the next agent recognises the shape of it.

*Machine: one FreeCAD 1.1.3 kernel at a time on the 119 MB R19 body. Times are wall-clock from spawn
to status file.*

## The table

| job | typical | samples (s) | red flag at 1.5x | notes |
|---|---|---|---|---|
| `job_fields_dump.py` (S3) | **13 s** | 12, 13, 13, 13, 13, 13, 15, 15 | **20 s** | very tight; numpy only after the tessellation |
| `job_features_burrito.py` (S5) | **85 s** | 65, 77, 78, 81, 81, 84, 87, 90, 94, 97, 100 | **128 s** | scales with region count and panel count, not card area |
| `job_s7_replace.py` (S7) — full fuse | **64 s** | 64 | **96 s** | cut 4 s + fuse 10 s + the rest is tessellation/bookkeeping |
| `job_s7_replace.py` (S7) — refused at a gate | **20 s** | 19, 19, 19, 20, 22, 23 | **30 s** | exits at the review-binding check; NOT a failure of the fuse |
| `job_s7_crop.py` | **15 s** | 15 | **23 s** | |
| `job_compare_pics.py` (30 kept frames + step1 + overlay) | **~15 s PER FRAME** | 79, 120 (early); 450 (2026-09-15) | — | **the typical is now useless — see M12.** Budget 15 s/frame and count PNGs; do NOT budget 100 s |
| `job_repair.py` `CHAIN=census` (4530 faces) | **27 s** | 27 | **41 s** | iterates `isValid()` per face; names WHERE the fuse is bad |
| `job_fuzzladder.py` — load + cut, then one rung | **20 s / rung** | 20 | **30 s** | a rung that returns a NULL shape is FAST, not slow (L32) |
| `job_brepstat.py` | **13 s** | 12, 12, 13, 15 | **20 s** | one body, load + tessellate |
| `job_sect_compare.py` (3–4 stations) | **23 s** | 23 | **35 s** | **writes no status file** — wait on its PNGs |
| `kit measure section` (1 station) | **8 s** | 8, 8, 8 | **12 s** | |
| `kit measure section --profile` | **9 s** | 8, 10 | **14 s** | |
| `kit measure faces --only` | **3 s** | 3 | **5 s** | |
| `kit render --views all` (whole body) | **83 s** | 75, 92 | **125 s** | |
| `kit render --views all` (boxed / piece) | **50 s** | 42, 58, 60 | **75 s** | |
| `kit dossier take` (15 sections + 10 frames) | **127 s** | 127 | **190 s** | 7 of those 15 sections were wasted — see M4 |
| `kit review` step 1 (tess cache, 2 bodies) | **90 s** | 90 | **135 s** | the ONLY kernel step of a review |
| `cad-reviewer` agent, 5 frames | **105 s** | 89, 95, 110, 110, 115, 120 | **160 s** | |
| `cad-reviewer` agent, 10 frames | **125 s** | 105, 110, 157 | **190 s** | |
| `t_cutter.py` C0–C6 (find, measure, fair, sweep) | **PROVISIONAL ~40 s** | — | — | **no samples yet.** Estimated from S3 plus two `kit measure section` calls. Take three real samples and replace this row |
| `t_cutter.py` C7–C9 (cut, cleanup, seven checks) | **PROVISIONAL ~60 s** | — | — | **no samples yet.** The thin-wall count is two `thickness_map` passes and dominates |

## RUNAWAYS — excluded from the averages, kept so the shape is recognisable

| job | ran | typical | why |
|---|---|---|---|
| `kit run t_burrito.py` build | **14 min, killed** | ~2 min | piece-assembly fuse on a 5,200-face piece. Cause: `bridge`/`majority` raised, which made the piece far heavier. **The fuse cost scales with face count.** |
| `job_s7_replace.py` | **10 min, killed** | 64 s | running `check(True)` on the BODY. Gate 6 documents that this **does not return** (>15 min). `LK_BODYBOP=0 LK_PREBOP=0 LK_RESBOP=0` and it finished in 64 s. |
| `job_compare_pics.py` | **272 s** | 100 s | 3.4x. Wrote a **ZERO-BYTE log** while running 4 minutes, so it could not be told from a hang. Merge request M9. |
| `job_features_burrito.py` | **159 s, 219 s** | 84 s | both runs carried `LK_EDITS`; the 219 s one also produced a worse piece. Edits cost time AND quality here. |
| `job_s7_replace.py` FUZZY 0.02 | **8 min, killed** | 163–283 s (L17) | the client: *"fuse stopped. It was at 8min which means it likely failed."* CORRECTION: the client killed it on the clock; it was never observed to fail. L17 says poll a fuzzy fuse to ~9 min before calling it stuck. |
| `job_compare_pics.py` (4th sample) | **420 s** | 100 s | 79 → 120 → 272 → 420 s. **Monotonically worse on the same machine, one kernel at a time.** Something accumulates — merge request M12. |
| `job_features_burrito.py` POLE=2.0 | **488 s** | 84 s | **5.8x for ZERO improvement** in the defect it was aimed at. Finer poles are not free and did not help. |
| `job_features_burrito.py` STEP=1 | **302 s** | 84 s | 3.6x; quadric fallbacks 15 → 12, defect unchanged. |

## Steps that write NO status file — wait on the artefact, never on a status name

L11's documented trap. These will burn your whole timeout if you poll for a status JSON:

* **`job_sect_compare.py`** — writes its PNGs, no status file. Wait on the PNG count.
* **`job_compare_pics.py`** — same. Wait on the `_kept.png` count.
* **`job_fields_dump.py`** — *used to* write none; it DOES now (fixed 2026-09-14) and records the
  layers it found. Wait on `status_fields_dump<TAG>.json`.

**And check the PID, not just the file.** A dead worker and a slow one look identical to a poll loop.
Ten minutes went into polling a dead process on 2026-09-14.
